"""P42 heat-response overlay. All evaluation uses the cached reference farms."""

from dataclasses import asdict, replace
from functools import lru_cache
import json

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from src.crops import load_crops
from src.literature_variant import NUMERICAL_TOLERANCE, compare_rankings, crop_sequence, eligible
from src.optimizer import allowed_layers
from src.precompute_cache import write_json
from src.scoring import METRICS, ROOT, crop_windows, preload, score_rotations
from src.sensitivity import ExactSearch, apply_values, inventory, joint_samples, measures

OUTPUT = "smooth_climate_fit_p42.json"
PLAN = "docs/p42_plan.md"
HEAT_BAND_DAYS = 5  # Each side of the original cutoff. Design choice fixed in P42.
SHORTLIST_CHANGE_CUTOFF = 0.1  # Normalized climate-fit points. Design choice.
CLIMATE_ADDITION = 3
CLIMATE_METRIC = METRICS.index("climate_fit")


def smooth_heat(hot_days, cutoff):
    """Return a smooth heat-fit value between one and zero across the fixed band."""
    fraction = np.clip((hot_days - cutoff + HEAT_BAND_DAYS) / (2 * HEAT_BAND_DAYS), 0, 1)
    return 1 - fraction**2 * (3 - 2 * fraction)


def smooth_window_scores(windows, crop, hot_day_fraction):
    samples = np.stack(list(windows.values()))
    rainfall, mean_temperature, daily_high = np.moveaxis(samples, -1, 0)
    rainfall_total = rainfall.sum(axis=1)
    temperature_average = mean_temperature.mean(axis=1)
    rain_pass = (rainfall_total >= crop["min_rain_mm"]) & (rainfall_total <= crop["max_rain_mm"])
    temperature_pass = (temperature_average >= crop["min_temp_c"]) & (temperature_average <= crop["max_temp_c"])
    hot_days = (daily_high > crop["heat_tolerance_c"]).sum(axis=1)
    cutoff = hot_day_fraction * daily_high.shape[1]
    return smooth_heat(hot_days, cutoff) * (rain_pass & temperature_pass)


def smooth_model(model):
    additions = model.additions.copy()
    for (slot, crop_index), windows in model.histories.items():
        crop = model.crops[model.ids[crop_index]]
        if windows and crop["season_length_days"]:
            score = smooth_window_scores(windows, crop, model.policy["max_hot_day_fraction"])
            additions[slot, crop_index, CLIMATE_ADDITION] = score.mean()
    return replace(model, additions=additions)


def compare_scores(model, smoothed, rows):
    old_raw, old_scores, old_flags = score_rotations(model, rows)
    new_raw, new_scores, new_flags = score_rotations(smoothed, rows)
    other = [i for i, metric in enumerate(METRICS) if metric != "climate_fit"]
    np.testing.assert_array_equal(old_raw[:, other], new_raw[:, other])
    np.testing.assert_array_equal(old_scores[:, other], new_scores[:, other])
    for flag, mask in old_flags.items():
        np.testing.assert_array_equal(mask, new_flags[flag])
    return old_raw, old_scores, new_scores, old_flags


def nominal_results(model, smoothed, search, names, saved):
    layers = tuple(tuple(layer) for layer in allowed_layers(model, search.years))
    rotations = search.rotations(layers)
    _, original, smooth, flags = compare_scores(model, smoothed, rotations)
    mask = eligible(flags)
    if len(rotations) != saved["feasible_count"] or not mask.all():
        raise ValueError("P42 did not reproduce the published nominal canonical feasible count")
    comparisons = {}
    for name, weights in zip(names, search.weights, strict=True):
        old = original @ weights
        np.testing.assert_allclose(old.max(), saved["verification"][name]["exact_score"], atol=1e-10, rtol=0)
        comparisons[name] = compare_rankings(model, rotations, old, smooth @ weights, mask, search.tolerance)
    return comparisons


def shortlist_results(model, smoothed, strategies):
    rows = [[model.ids.index(crop) for year in item["crop_ids"] for crop in year] for item in strategies]
    raw, original, smooth, flags = compare_scores(model, smoothed, rows)
    result = []
    for index, item in enumerate(strategies):
        for key, vector in (("score", original[index]), ("value", raw[index])):
            saved = [item["metrics"][metric][key] for metric in METRICS]
            np.testing.assert_allclose(vector, saved, atol=1e-10, rtol=0)
        before = float(original[index, CLIMATE_METRIC])
        after = float(smooth[index, CLIMATE_METRIC])
        delta = after - before
        result.append({"strategy_id": item["strategy_id"], "rotation": item["crop_ids"],
                       "original": before, "smooth": after, "delta": delta,
                       "over_cutoff": abs(delta) > SHORTLIST_CHANGE_CUTOFF + NUMERICAL_TOLERANCE,
                       "flags": {key: np.flatnonzero(values[index]).tolist() for key, values in flags.items()}})
    return {"strategies": result, "above_cutoff": sum(row["over_cutoff"] for row in result), "total": len(result)}


def matched_draw_results(model, smoothed, search, names, draws, saved):
    reference = search.evaluate(model)
    smooth_reference = search.evaluate(smoothed)
    original_draws, smooth_draws = [], []
    for drawn_model in draws:
        original_draws.append(search.evaluate(drawn_model, reference.winners))
        smooth_draws.append(search.evaluate(smooth_model(drawn_model), smooth_reference.winners))

    def decode(sequence):
        return crop_sequence(model, sequence)

    result = {}
    for i, name in enumerate(names):
        original = measures(original_draws, reference, i, decode)
        smooth = measures(smooth_draws, smooth_reference, i, decode)
        published = saved["presets"][name]
        old_reference = decode(reference.winners[i])
        n = original["evaluations"]
        if (old_reference != published["reference_winner"] or original["winners"] != published["joint"]["winners"]
                or n != published["joint"]["evaluations"]):
            raise ValueError(f"P42 could not reproduce the saved P22 winner identities for {name}")
        np.testing.assert_allclose(
            [reference.top_scores[i], original["winner_change_fraction"], original["material_change_fraction"]],
            [published["reference_top_score"], published["joint"]["winner_change_fraction"],
             published["joint"]["material_change_fraction"]],
            atol=NUMERICAL_TOLERANCE, rtol=0,
        )
        differences = sum(not np.array_equal(a.winners[i], b.winners[i])
                          for a, b in zip(original_draws, smooth_draws, strict=True))
        result[name] = {
            "draws": n,
            "original_reference": old_reference,
            "smooth_reference": decode(smooth_reference.winners[i]),
            "original_change_fraction": original["winner_change_fraction"],
            "smooth_change_fraction": smooth["winner_change_fraction"],
            "change_delta": smooth["winner_change_fraction"] - original["winner_change_fraction"],
            "original_material_fraction": original["material_change_fraction"],
            "smooth_material_fraction": smooth["material_change_fraction"],
            "material_delta": smooth["material_change_fraction"] - original["material_change_fraction"],
            "paired_disagreement_count": differences,
            "paired_disagreement_fraction": differences / n,
        }
    return result


def build_farm(root, farm, read, crops, presets, config, grades):
    farm_id = farm["farm_id"]
    seasons = read(f"data/processed/seasons_{farm_id}.json")
    climate = pd.read_parquet(root / f"data/processed/climate_{farm_id}.parquet").set_index("date")

    @lru_cache(maxsize=256)
    def lookup(start, length):
        return crop_windows(climate, start, length)

    def load_model(farm_config, catalog, policy, calendar):
        return preload(farm_config, root=root, crops=catalog, policy=policy, season_calendar=calendar,
                       climate=climate, window_lookup=lookup)

    model = load_model(farm, crops, None, seasons)
    saved = read(f"data/processed/strategies_{farm_id}.json")
    p22 = read(f"data/processed/sensitivity_{farm_id}.json")
    inputs = inventory(model, seasons, grades, config)
    if (config != p22["design"] or saved["horizon_years"] != p22["horizon_years"]
            or json.loads(json.dumps([asdict(item) for item in inputs])) != p22["inputs"]):
        raise ValueError(f"P42 inputs differ from the saved P22 study for {farm_id}")

    search = ExactSearch(presets, saved["horizon_years"], len(model.season_labels), config["near_tie_gap"])
    smoothed = smooth_model(model)
    nominal = nominal_results(model, smoothed, search, presets, saved)
    shortlist = shortlist_results(model, smoothed, saved["strategies"])
    active = tuple(i for i, item in enumerate(inputs) if item.levels)
    varied_inputs = [inputs[i] for i in active]
    draws = (load_model(*apply_values(model, seasons, varied_inputs, [sample[i] for i in active]))
             for sample in joint_samples(inputs, config))
    rates = matched_draw_results(model, smoothed, search, presets, draws, p22)
    return {"name": farm["name"], "horizon_years": search.years, "nominal": nominal,
            "published_shortlist": shortlist, "p22": rates}


def build(root=ROOT, output=None):
    def read(path):
        return json.loads((root / path).read_text())

    config = read("config/sensitivity.json")
    if read("config/tie_diagnosis.json")["exact_metric_tolerance"] != NUMERICAL_TOLERANCE:
        raise ValueError("P42 expects the preregistered floating-point tolerance")
    presets = read("config/weights_presets.json")["presets"]
    grades = read("config/evidence_grades.json")
    farms = read("config/farms.json")
    crops = load_crops(root / "data/crops.csv", farms=farms)
    with threadpool_limits(limits=1):
        results = {farm["farm_id"]: build_farm(root, farm, read, crops, presets, config, grades) for farm in farms}
    report = {"label": "illustrative; validate locally", "plan": PLAN,
              "source": "NASA POWER · crop catalog · smooth heat rule is a design choice",
              "design": {"half_band_hot_days": HEAT_BAND_DAYS, "shortlist_cutoff": SHORTLIST_CHANGE_CUTOFF,
                         "near_tie_gap": config["near_tie_gap"], "draws": config["joint_draws"],
                         "seed": config["seed"], "source": config["source"]},
              "farms": results}
    write_json(output if output is not None else root / "data/processed" / OUTPUT, report)
    return report


def render_markdown(report):
    design = report["design"]
    farms = list(report["farms"].values())
    comparisons = [row for farm in farms for row in farm["nominal"].values()]
    correlations = [r["rank_spearman"] for r in comparisons if r["rank_spearman"] is not None]
    correlation_summary = (f"Rank Spearman ρ ranged from **{min(correlations):.4f} to "
                           f"{max(correlations):.4f}** across estimable cases."
                           if correlations else "Rank correlations were unavailable.")
    shortlist_changed = sum(farm["published_shortlist"]["above_cutoff"] for farm in farms)
    shortlist_total = sum(farm["published_shortlist"]["total"] for farm in farms)
    threshold = design["shortlist_cutoff"]
    changed = sum(r["label_changed"] for r in comparisons)
    tie_appeared = sum(r["near_tie_appeared"] for r in comparisons)
    tie_disappeared = sum(r["near_tie_disappeared"] for r in comparisons)
    entered = sum(r["entered_near_top"] for r in comparisons)
    left = sum(r["left_near_top"] for r in comparisons)
    lines = [
        "# Smooth climate-fit what-if (P42)", "",
        "[Preregistration](p42_plan.md) was finalized in `be32ce5` before evaluation. "
        "[Saved comparison](../data/processed/smooth_climate_fit_p42.json).", "",
        f"The heat score declines smoothly within **±{design['half_band_hot_days']} hot days** of "
        "the original cutoff. The band and its shape are design choices inspired by gradual heat responses "
        "in P41's ridge curves, with no fitting to those curves. Rainfall and mean-temperature gates still "
        "apply. Inputs come from NASA POWER and the crop catalog. [P41 response curves]"
        "(ml_model.md#p41-scoring-versus-county-yield-response)", "",
        f"**{changed} of {len(comparisons)}** nominal leaders changed. "
        f"{correlation_summary} "
        f"The top-two near-tie was created in **{tie_appeared}** cases and resolved in **{tie_disappeared}**. "
        f"There were **{entered} entries and {left} exits** from near-top sets across farm–preset cases. "
        f"**{shortlist_changed} of {shortlist_total}** published options moved by more than {threshold:g} "
        f"climate-fit points (**{shortlist_changed / shortlist_total:.1%}**).", "",
        f"Near-top sets count all feasible canonical rotations within {design['near_tie_gap']:g} "
        "weighted points of first, including the winner. The original and smooth rankings use "
        "identical canonical pools. Exact top ties use the existing numerical tolerance. All results "
        "are illustrative and need local validation.", "",
        f"P22 replay uses {design['draws']} paired draws per farm and seed {design['seed']}. "
        "Each change rate compares a draw's winner with its own specification's nominal P22 winner. "
        "The paired-difference column compares the two winners directly on identical draws. A winner change "
        "counts as material if the reference is ineligible or its weighted gap exceeds the near-tie tolerance. "
        "A flagged baseline remains visible and eligible for comparison under P22's original convention. "
        "The replay reproduced the saved original winner histograms, change rates and material-change rates. "
        "These frequencies describe the chosen assumption ranges. [P22 assumptions](sensitivity.md)", "",
    ]

    def table(headers, rows):
        def line(cells):
            return "| " + " | ".join(map(str, cells)) + " |"
        lines.extend([line(headers), line(["---"] * len(headers)), *(line(row) for row in rows), ""])

    def cycle(rows):
        return " → ".join(" / ".join(crop.replace("_", " ") for crop in year) for year in rows)

    def number(value, spec):
        return "Unavailable" if value is None else format(value, spec)

    for farm in farms:
        exact = farm["nominal"]
        count = next(iter(exact.values()))["common_count"]
        lines.extend([f"## {farm['name']}", "", f"{count:,} feasible canonical rotations over "
                      f"{farm['horizon_years']} years for each preset.", ""])
        table(["Preset", "Original leader (score)", "Smooth leader (score)", "Leader changed",
               "Old leader still optimal", "Rank Spearman ρ"], [
            (name.replace("_", " "), f"{cycle(r['original_rotation'])} ({r['original_score']:.6f})",
             f"{cycle(r['variant_rotation'])} ({r['variant_score']:.6f})",
             "yes" if r["label_changed"] else "no", "yes" if r["original_still_optimal"] else "no",
             number(r["rank_spearman"], ".6f")) for name, r in exact.items()
        ])
        table(["Preset", "Top-two gap original → smooth", "Exact top ties original → smooth",
               "Near-top count original → smooth", "Entered", "Left", "Top-two near-tie change"], [
            (name.replace("_", " "),
             f"{number(r['original_top_two_gap'], '.6f')} → {number(r['variant_top_two_gap'], '.6f')}",
             f"{r['original_exact_ties']} → {r['variant_exact_ties']}",
             f"{r['original_near_top']} → {r['variant_near_top']}", r["entered_near_top"], r["left_near_top"],
             "created" if r["near_tie_appeared"] else "resolved" if r["near_tie_disappeared"] else "none")
            for name, r in exact.items()
        ])
        table(["Preset", "P22 change original → smooth", "Change (pp)", "P22 material original → smooth",
               "Material change (pp)", "Different winners on matched draws"], [
            (name.replace("_", " "), f"{r['original_change_fraction']:.2%} → {r['smooth_change_fraction']:.2%}",
             f"{100 * r['change_delta']:+.2f}", f"{r['original_material_fraction']:.2%} → {r['smooth_material_fraction']:.2%}",
             f"{100 * r['material_delta']:+.2f}", f"{r['paired_disagreement_count']}/{r['draws']} ({r['paired_disagreement_fraction']:.2%})")
            for name, r in farm["p22"].items()
        ])
        shortlist = farm["published_shortlist"]
        lines.extend([f"Published baseline and shortlist · **{shortlist['above_cutoff']} of "
                      f"{shortlist['total']} ({shortlist['above_cutoff'] / shortlist['total']:.1%})** "
                      f"changed by more than {threshold:g} climate-fit points.", ""])
        table(["Published strategy", "Original climate fit", "Smooth climate fit", "Change"], [
            (r["strategy_id"].replace("_", " "), f"{r['original']:.6f}", f"{r['smooth']:.6f}", f"{r['delta']:+.6f}")
            for r in shortlist["strategies"]
        ])
    lines.extend([
        "The swap measures how the score responds to one modeling choice. Field heat responses and "
        "rotation suitability remain untested. The [published P44 consensus](consensus_shortlist.md) "
        "describes the configurations tested at the time.", "",
        "Rebuild the separate audit offline with `python -m src.smooth_climate_fit`.", "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    (ROOT / "docs/smooth_climate_fit.md").write_text(render_markdown(build()), encoding="utf-8")
