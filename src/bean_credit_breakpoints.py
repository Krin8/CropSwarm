"""Offline P51 bean-credit counterfactuals on the original Makueni scorer."""

import json
from dataclasses import asdict
from functools import lru_cache

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from src.crops import load_crops
from src.literature_variant import crop_sequence, eligible
from src.optimizer import allowed_layers
from src.precompute_cache import write_json
from src.regional_scoring_variants import MAKUENI, OUTPUT as P46_OUTPUT, regional_model
from src.scoring import METRICS, ROOT, crop_windows, preload, score_rotations
from src.sensitivity import ExactSearch, apply_values, inventory, joint_samples, measures

OUTPUT = "bean_credit_breakpoints_p51.json"
PLAN = "p51_plan.md"
CATALOG = 22
GRID_SOURCES = {
    0.7: "P49 Machakos field-yield fit, Chui p. 156",
    5: "design choice",
    10: "design choice",
    16.4: "P49 recalculation of Kimutwa yield fit, Chui Table 37b and Appendix Table 21",
    22: "Crop catalog, assumption, validate locally",
    30: "design choice",
    44: "P45 Katumani field-yield fit, Nadar and Faught Figure 2 and Tables II–VI",
    56: "P49 Machakos field-yield fit, Chui p. 156",
    68: "design choice",
    80: "P45 Katumani field-yield fit, Nadar and Faught Figure 2 and Tables II–VI",
}
DRAW_CREDITS = (CATALOG, 44, 80)
CORRECTION = {"crop": "common_bean", "field": "n_credit_kg_ha", "values": {credit: credit for credit in GRID_SOURCES}}
UNCERTAINTY = (
    "Regional trials suggest an uncertain range of roughly 1–80 kg N/ha for bean credit. "
    "They estimate fertilizer equivalence for following maize in specific trial conditions. "
    "Transfer to this farm and to other successor crops is an assumption, validate locally."
)
FARM_CAVEAT = "Makueni cropland is unverified. Results are illustrative and conditional on the assumed baseline."


def top_two(objective, rows, decode, tolerance):
    """Use canonical row order to resolve equal full-precision weighted scores."""
    order = np.argsort(-objective, kind="stable")[:2]
    leader, runner = [{"rotation": decode(rows[i]), "score": float(objective[i])} for i in order]
    gap = leader["score"] - runner["score"]
    return {"leader": leader, "runner_up": runner, "gap": gap, "near_tie": gap <= tolerance}


def leader_runs(points, catalog_credit=CATALOG):
    """Group unchanged leaders and retain both ends of each observed flip."""
    catalog = next(point["leader"]["rotation"] for point in points if point["credit"] == catalog_credit)
    intervals, breakpoints = [], []
    for point in points:
        leader = point["leader"]["rotation"]
        if not intervals or leader != intervals[-1]["rotation"]:
            if intervals:
                breakpoints.append({"before": previous, "after": point,
                                    "near_tie": previous["near_tie"] or point["near_tie"]})
            intervals.append({"first_credit": point["credit"], "last_credit": point["credit"],
                              "rotation": leader, "catalog_leader": leader == catalog})
        else:
            intervals[-1]["last_credit"] = point["credit"]
        previous = point
    return {"catalog_leader": catalog, "retains_catalog_leader": len(intervals) == 1,
            "leader_intervals": intervals, "breakpoints": breakpoints, "grid": points}


def fixed_rows(entries, raw, scores, flags, reference, weights):
    reference_raw, reference_scores = reference
    terms = {}
    for preset, weight in weights.items():
        objective = scores @ weight
        ranks = np.empty(len(entries), dtype=int)
        ranks[np.argsort(-objective, kind="stable")] = np.arange(1, len(entries) + 1)
        terms[preset] = (objective, reference_scores @ weight, ranks)
    return [{
        "strategy": entry["strategy_id"], "rotation": entry["crop_ids"],
        "metrics": {metric: {
            "value": float(raw[i, j]), "delta": float(raw[i, j] - reference_raw[i, j]),
            "score": float(scores[i, j]), "score_delta": float(scores[i, j] - reference_scores[i, j]),
            "unit": entry["metrics"][metric]["unit"], "source": entry["metrics"][metric]["source"],
            "evidence_label": entry["metrics"][metric]["evidence"]["label"],
        } for j, metric in enumerate(METRICS)},
        "flags": {name: np.flatnonzero(mask[i]).tolist() for name, mask in flags.items()},
        "presets": {preset: {"score": float(objective[i]), "score_delta": float(objective[i] - before[i]),
                             "rank_among_published": int(ranks[i])}
                    for preset, (objective, before, ranks) in terms.items()},
    } for i, entry in enumerate(entries)]


def nominal(model, search, names, saved, p46):
    rows = search.rotations(tuple(tuple(layer) for layer in allowed_layers(model, search.years)))
    if len(rows) != saved["feasible_count"]:
        raise ValueError("P51 canonical pool differs from the published optimizer count")
    entries = saved["strategies"]
    fixed = [[model.ids.index(crop) for year in entry["crop_ids"] for crop in year] for entry in entries]
    original_raw, original_scores, original_flags = score_rotations(model, fixed)
    for key, actual in (("value", original_raw), ("score", original_scores)):
        np.testing.assert_allclose(actual, [[entry["metrics"][m][key] for m in METRICS] for entry in entries],
                                   atol=1e-10, rtol=0)

    def decode(row):
        return crop_sequence(model, row)

    weights = dict(zip(names, search.weights, strict=True))
    points = {name: [] for name in names}
    shortlist = []
    p46_levels = {44: "low", 80: "high"}
    for credit in GRID_SOURCES:
        variant = regional_model(model, CORRECTION, credit)
        _, scores, flags = score_rotations(variant, rows)
        if not eligible(flags).all():
            raise ValueError(f"P51 overlay changed canonical feasibility at {credit}")
        for name, weight in weights.items():
            top = top_two(scores @ weight, rows, decode, search.tolerance)
            if credit == CATALOG:
                np.testing.assert_allclose(top["leader"]["score"], saved["verification"][name]["exact_score"],
                                           atol=1e-10, rtol=0)
            if credit in p46_levels:
                check = p46[p46_levels[credit]]["nominal"][name]
                if top["leader"]["rotation"] != check["variant_rotation"] or len(rows) != check["variant_count"]:
                    raise ValueError(f"P51 nominal leader differs from P46 for {name} at {credit}")
                np.testing.assert_allclose([top["leader"]["score"], top["gap"]],
                                           [check["variant_score"], check["variant_top_two_gap"]], atol=1e-10, rtol=0)
            points[name].append({"credit": credit, **top})

        raw, scores, flags = score_rotations(variant, fixed)
        invariant = np.array([metric != "nitrogen" or credit == CATALOG for metric in METRICS])
        np.testing.assert_array_equal(raw[:, invariant], original_raw[:, invariant])
        np.testing.assert_array_equal(scores[:, invariant], original_scores[:, invariant])
        for flag in original_flags:
            np.testing.assert_array_equal(flags[flag], original_flags[flag])
        shortlist.append({"credit": credit, "nitrogen_bounds": list(variant.nitrogen_bounds),
                          "strategies": fixed_rows(entries, raw, scores, flags,
                                                   (original_raw, original_scores), weights)})
    return len(rows), {name: leader_runs(grid) for name, grid in points.items()}, shortlist


def replay(model, search, names, draws, p46=None):
    references = {credit: search.evaluate(regional_model(model, CORRECTION, credit)) for credit in DRAW_CREDITS}
    outcomes = {credit: [] for credit in DRAW_CREDITS}
    for draw in draws:
        for credit, reference in references.items():
            outcome = search.evaluate(regional_model(draw, CORRECTION, credit), reference.winners)
            outcomes[credit].append(outcome)

    def decode(row):
        return crop_sequence(model, row)

    records = {name: [] for name in names}
    for i, name in enumerate(names):
        for credit, changes in outcomes.items():
            reference = references[credit]
            metrics = measures(changes, reference, i, decode)
            disagreements = sum(not np.array_equal(a.winners[i], b.winners[i])
                                for a, b in zip(outcomes[CATALOG], changes, strict=True))
            reference_winner = decode(reference.winners[i])
            if p46 is not None and credit != CATALOG:
                check = p46["low" if credit == 44 else "high"]["p22"][name]
                if reference_winner != check["reference_winner"] or metrics["evaluations"] != check["draws"]:
                    raise ValueError(f"P51 draw reference differs from P46 for {name} at {credit}")
                for key in ("winner_change_fraction", "material_change_fraction"):
                    np.testing.assert_allclose(metrics[key], check[key], atol=1e-12, rtol=0)
            records[name].append({"credit": credit, "reference_winner": reference_winner,
                                  **metrics, "paired_disagreement_count": disagreements,
                                  "paired_disagreement_fraction": disagreements / len(changes)})
    return records


def build(root=ROOT, output=None):
    def read(path):
        return json.loads((root / path).read_text())

    data = root / "data/processed"
    farms = read("config/farms.json")
    farm, = (farm for farm in farms if farm["farm_id"] == MAKUENI)
    crops = load_crops(root / "data/crops.csv", farms=farms)
    presets = read("config/weights_presets.json")["presets"]
    config = read("config/sensitivity.json")
    if (config["seed"], config["joint_draws"], config["near_tie_gap"]) != (42, 512, 0.01):
        raise ValueError("P51 requires the preregistered P22 settings")
    seasons = read(data / f"seasons_{MAKUENI}.json")
    climate = pd.read_parquet(data / f"climate_{MAKUENI}.parquet").set_index("date")

    @lru_cache(maxsize=256)
    def lookup(start, length):
        return crop_windows(climate, start, length)

    def load(farm_config, catalog, policy, calendar):
        return preload(farm_config, root=root, crops=catalog, policy=policy, season_calendar=calendar,
                       climate=climate, window_lookup=lookup)

    original = load(farm, crops, None, seasons)
    saved = read(data / f"strategies_{MAKUENI}.json")
    p22 = read(data / f"sensitivity_{MAKUENI}.json")
    p46 = read(data / P46_OUTPUT)["farms"][MAKUENI]["levels"]
    inputs = inventory(original, seasons, read("config/evidence_grades.json"), config)
    if (config != p22["design"] or saved["horizon_years"] != p22["horizon_years"]
            or json.loads(json.dumps([asdict(item) for item in inputs])) != p22["inputs"]
            or crops["common_bean"]["n_credit_kg_ha"] != CATALOG):
        raise ValueError("P51 catalog or replay inventory differs from the saved inputs")

    search = ExactSearch(presets, saved["horizon_years"], len(original.season_labels), config["near_tie_gap"])
    active = [i for i, item in enumerate(inputs) if item.levels]
    varying = [inputs[i] for i in active]
    draws = (load(*apply_values(original, seasons, varying, [sample[i] for i in active]))
             for sample in joint_samples(inputs, config))
    with threadpool_limits(limits=1):
        count, rankings, shortlist = nominal(original, search, presets, saved, p46)
        replays = replay(original, search, presets, draws, p46)
    for name, result in rankings.items():
        historical = p22["presets"][name]["joint"]
        result["matched_draws"] = replays[name]
        result["p22_sampled_credit_context"] = {
            "evaluations": historical["evaluations"], "winner_change_fraction": historical["winner_change_fraction"],
            "material_change_fraction": historical["material_change_fraction"],
        }
    report = {
        "farm_id": MAKUENI, "name": farm["name"], "label": "illustrative, validate locally",
        "caveat": FARM_CAVEAT, "credit_evidence": UNCERTAINTY,
        "baseline_source": farm["baseline_source"], "horizon_years": saved["horizon_years"],
        "canonical_count": count, "catalog_credit": CATALOG, "credit_unit": "kg N/ha",
        "credit_grid": [{"credit": credit, "source": source} for credit, source in GRID_SOURCES.items()],
        "draw_design": {key: config[key] for key in ("seed", "joint_draws", "near_tie_gap", "source")},
        "presets": rankings, "published_strategies": shortlist,
    }
    write_json(output if output is not None else data / OUTPUT, report)
    return report


if __name__ == "__main__":
    build()
