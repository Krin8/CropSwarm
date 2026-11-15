"""P46 farm-scoped counterfactuals using the unchanged scoring engine."""

from dataclasses import asdict, replace
from functools import lru_cache
from itertools import product
import json

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from threadpoolctl import threadpool_limits

from src.crops import load_crops
from src.literature_variant import NUMERICAL_TOLERANCE, crop_sequence, eligible, ranking
from src.optimizer import allowed_layers
from src.precompute_cache import write_json
from src.scoring import METRICS, ROOT, crop_windows, historical_metrics, preload, score_rotations
from src.sensitivity import ExactSearch, apply_values, inventory, joint_samples, measures

OUTPUT = "regional_scoring_variants_p46.json"
LEVELS = ("original", "low", "mid", "high")
TELANGANA = "telangana_a"
MAKUENI = "kenya_makueni_north"
TARGETS = {
    MAKUENI: ("common_bean", "n_credit_kg_ha", "nadar", 22, (44, 62, 80), "kg N/ha"),
    TELANGANA: ("paddy", "water_need_mm", "mote", 575, (473.9, 565.85, 657.8), "mm ET"),
}


def design(crops, evidence):
    corrections = {}
    for farm_id, (crop, field, source, original, levels, unit) in TARGETS.items():
        reference, = (row for row in evidence["comparisons"] if row["region"] == farm_id
                      and row["source"] == source and "bounds" in row
                      and row.get("crop") == crop and row.get("field") == field)
        if reference["bounds"] != [levels[0], levels[-1]] or crops[crop][field] != original:
            raise ValueError(f"Cached sources or catalog differ from the P46 plan for {farm_id}")
        corrections[farm_id] = {"crop": crop, "field": field, "unit": unit,
                                "values": dict(zip(LEVELS, (original, *levels), strict=True)),
                                "source": evidence["sources"][source], "endpoint_grade": "literature",
                                "midpoint_grade": "design choice", "transfer_grade": "assumption, validate locally"}
    cases = [{"makueni": n, "telangana": w, "local_levels": {MAKUENI: n, TELANGANA: w}}
             for n, w in product(LEVELS, repeat=2)]
    return corrections, cases


def regional_model(model, correction, level):
    if level == "original":
        return model
    crop_id, field = correction["crop"], correction["field"]
    index = model.ids.index(crop_id)
    value = correction["values"][level]
    crop = {**model.crops[crop_id], field: value}
    crops = {**model.crops, crop_id: crop}
    if field == "n_credit_kg_ha":
        credits = model.credits.copy()
        credits[index] = value
        return replace(model, crops=crops, credits=credits,
                       nitrogen_bounds=(model.nitrogen_bounds[0], float(credits.max())))

    additions = model.additions.copy()
    suitable = model.suitable.copy()
    for slot in range(len(model.season_labels)):
        windows = model.histories[slot, index]
        hist = historical_metrics(windows, crop, model.storage, model.slope,
                                  model.farm["irrigation"]["supply_fraction"], model.policy)
        if len(hist):
            additions[slot, index, :2] = hist[:, :2].mean(axis=0)
            suitable[slot, index] = (model.planting_windows[slot, index] and
                                     np.median(hist[:, 1]) <= model.policy["max_median_unmet_water_fraction"])
    return replace(model, crops=crops, additions=additions, suitable=suitable)


def nominal_comparison(model, rows, old_scores, new_scores, old_ok, new_ok, tolerance):
    old_index, old_max, old_near, old_ties, old_gap = ranking(old_scores, old_ok, tolerance)
    new_index, new_max, new_near, new_ties, new_gap = ranking(new_scores, new_ok, tolerance)
    common = old_ok & new_ok
    a, b = old_scores[common], new_scores[common]
    rho = None if len(a) < 2 or np.ptp(a) == 0 or np.ptp(b) == 0 else float(spearmanr(a, b).statistic)
    old_close = old_gap is not None and old_gap <= tolerance
    new_close = new_gap is not None and new_gap <= tolerance
    return {
        "original_rotation": crop_sequence(model, rows[old_index]),
        "variant_rotation": crop_sequence(model, rows[new_index]),
        "original_score": old_max, "variant_score": new_max,
        "label_changed": old_index != new_index,
        "original_still_feasible": bool(new_ok[old_index]),
        "original_still_optimal": bool(new_ok[old_index] and new_scores[old_index] >= new_max - NUMERICAL_TOLERANCE),
        "rank_spearman": rho, "original_count": int(old_ok.sum()), "variant_count": int(new_ok.sum()),
        "common_count": int(common.sum()), "added_count": int((new_ok & ~old_ok).sum()),
        "excluded_count": int((old_ok & ~new_ok).sum()),
        "original_top_two_gap": old_gap, "variant_top_two_gap": new_gap,
        "original_exact_ties": old_ties, "variant_exact_ties": new_ties,
        "original_near_top": int(old_near.sum()), "variant_near_top": int(new_near.sum()),
        "entered_near_top": int((new_near & ~old_near).sum()), "left_near_top": int((old_near & ~new_near).sum()),
        "near_tie_appeared": new_close and not old_close, "near_tie_disappeared": old_close and not new_close,
    }


def exact_and_shortlist(original, models, search, names, saved):
    def rotations(model):
        return search.rotations(tuple(tuple(layer) for layer in allowed_layers(model, search.years)))

    original_rows = rotations(original)
    if len(original_rows) != saved["feasible_count"]:
        raise ValueError("Original feasible rotation count differs from the saved artifact")
    entries = saved["strategies"]
    fixed = [[original.ids.index(crop) for year in row["crop_ids"] for crop in year] for row in entries]
    original_raw, original_scores, original_flags = score_rotations(original, fixed)
    for index, entry in enumerate(entries):
        for key, actual in (("value", original_raw[index]), ("score", original_scores[index])):
            np.testing.assert_allclose(actual, [entry["metrics"][m][key] for m in METRICS], atol=1e-10, rtol=0)

    results = {}
    for level, model in models.items():
        new_rows = rotations(model)
        same_pool = original_rows is new_rows
        # Unique sorts rows lexicographically, the same order used by exact enumeration.
        rows = original_rows if same_pool else np.unique(np.vstack([original_rows, new_rows]), axis=0)
        _, before, flags = score_rotations(original, rows)
        old_ok = eligible(flags)
        if level == "original":
            after, new_ok = before, old_ok
        else:
            _, after, flags = score_rotations(model, rows)
            new_ok = eligible(flags)
        if old_ok.sum() != len(original_rows) or new_ok.sum() != len(new_rows):
            raise ValueError("Canonical enumeration and scorer disagree on feasibility")

        ranking_results = {}
        for name, weight in zip(names, search.weights, strict=True):
            old, new = before @ weight, after @ weight
            np.testing.assert_allclose(old[old_ok].max(), saved["verification"][name]["exact_score"],
                                       atol=1e-10, rtol=0)
            ranking_results[name] = nominal_comparison(original, rows, old, new, old_ok, new_ok, search.tolerance)

        raw, scores, flags = score_rotations(model, fixed)
        shortlist = []
        for i, entry in enumerate(entries):
            shortlist.append({
                "strategy": entry["strategy_id"], "rotation": entry["crop_ids"],
                "raw_delta": dict(zip(METRICS, (raw[i] - original_raw[i]).tolist(), strict=True)),
                "score_delta": dict(zip(METRICS, (scores[i] - original_scores[i]).tolist(), strict=True)),
                "original_flags": {flag: np.flatnonzero(mask[i]).tolist() for flag, mask in original_flags.items()},
                "variant_flags": {flag: np.flatnonzero(mask[i]).tolist() for flag, mask in flags.items()},
                "sources": {metric: entry["metrics"][metric]["source"] for metric in METRICS},
            })
        results[level] = {"nominal": ranking_results, "shortlist": shortlist}
    return results


def replay(original, models, correction, search, names, draws, saved):
    references = {level: search.evaluate(model) for level, model in models.items()}
    outcomes = {level: [] for level in models}
    for drawn in draws:
        for level, reference in references.items():
            model = regional_model(drawn, correction, level)
            outcomes[level].append(search.evaluate(model, reference.winners))

    def decode(cycle):
        return crop_sequence(original, cycle)

    records = {level: {} for level in models}
    for i, name in enumerate(names):
        original_draws = outcomes["original"]
        base = measures(original_draws, references["original"], i, decode)
        published = saved["presets"][name]
        reference = references["original"]
        number = base["evaluations"]
        if (decode(reference.winners[i]) != published["reference_winner"]
                or base["winners"] != published["joint"]["winners"]
                or number != published["joint"]["evaluations"]):
            raise ValueError(f"P46 original P22 winners differ for {name}")
        keys = ("winner_change_fraction", "material_change_fraction")
        np.testing.assert_allclose([reference.top_scores[i], *(base[key] for key in keys)],
                                   [published["reference_top_score"], *(published["joint"][key] for key in keys)],
                                   atol=NUMERICAL_TOLERANCE, rtol=0)
        for level, changes in outcomes.items():
            summary = base if level == "original" else measures(changes, references[level], i, decode)
            disagreements = sum(not np.array_equal(a.winners[i], b.winners[i])
                                for a, b in zip(original_draws, changes, strict=True))
            records[level][name] = {
                "draws": number, "reference_winner": decode(references[level].winners[i]),
                **{key: summary[key] for key in keys},
                "winner_change_delta": summary[keys[0]] - base[keys[0]],
                "material_change_delta": summary[keys[1]] - base[keys[1]],
                "paired_disagreement_count": disagreements, "paired_disagreement_fraction": disagreements / number,
            }
    return records


def build_farm(root, farm, read, crops, presets, config, grades, correction):
    farm_id = farm["farm_id"]
    data = root / "data/processed"
    seasons = read(data / f"seasons_{farm_id}.json")
    climate = pd.read_parquet(data / f"climate_{farm_id}.parquet").set_index("date")

    @lru_cache(maxsize=256)
    def lookup(start, length):
        return crop_windows(climate, start, length)

    def load(farm_config, catalog, policy, calendar):
        return preload(farm_config, root=root, crops=catalog, policy=policy, season_calendar=calendar,
                       climate=climate, window_lookup=lookup)

    original = load(farm, crops, None, seasons)
    saved = read(data / f"strategies_{farm_id}.json")
    p22 = read(data / f"sensitivity_{farm_id}.json")
    inputs = inventory(original, seasons, grades, config)
    if (config != p22["design"] or saved["horizon_years"] != p22["horizon_years"]
            or json.loads(json.dumps([asdict(item) for item in inputs])) != p22["inputs"]):
        raise ValueError(f"P46 input definitions differ from saved P22 for {farm_id}")
    if correction is not None and ("crop", correction["crop"], correction["field"]) not in [
        item.target for item in inputs
    ]:
        raise ValueError(f"P46 correction is missing from the original P22 inventory for {farm_id}")

    search = ExactSearch(presets, saved["horizon_years"], len(original.season_labels), config["near_tie_gap"])
    models = {level: regional_model(original, correction, level)
              for level in (LEVELS if correction is not None else LEVELS[:1])}
    results = exact_and_shortlist(original, models, search, presets, saved)
    active = [i for i, item in enumerate(inputs) if item.levels]
    varying = [inputs[i] for i in active]
    draws = (load(*apply_values(original, seasons, varying, [sample[i] for i in active]))
             for sample in joint_samples(inputs, config))
    rates = replay(original, models, correction, search, presets, draws, p22)
    for level, record in results.items():
        record["p22"] = rates[level]
    return {"name": farm["name"], "levels": results}


def build(root=ROOT, output=None):
    def read(path):
        return json.loads((root / path).read_text())

    config = read("config/sensitivity.json")
    if read("config/tie_diagnosis.json")["exact_metric_tolerance"] != NUMERICAL_TOLERANCE:
        raise ValueError("P46 expects the preregistered numerical tolerance")
    presets = read("config/weights_presets.json")["presets"]
    grades = read("config/evidence_grades.json")
    farms = read("config/farms.json")
    crops = load_crops(root / "data/crops.csv", farms=farms)
    corrections, cases = design(crops, read("data/p45_literature.json"))
    with threadpool_limits(limits=1):
        results = {farm["farm_id"]: build_farm(root, farm, read, crops, presets, config, grades,
                                               corrections.get(farm["farm_id"])) for farm in farms}
    for case in cases:
        case["local_levels"] = {farm_id: case["local_levels"].get(farm_id, "original") for farm_id in results}
    report = {"label": "illustrative, validate locally", "plan": "docs/p46_plan.md",
              "design": {key: config[key] for key in ("seed", "joint_draws", "near_tie_gap", "source")},
              "corrections": corrections, "configurations": cases, "farms": results}
    write_json(output if output is not None else root / "data/processed" / OUTPUT, report)
    return report


if __name__ == "__main__":
    build()
