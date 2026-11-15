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


if __name__ == "__main__":
    build()
