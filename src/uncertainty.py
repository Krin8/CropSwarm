"""Reproducible scenario comparisons for the cached candidate strategies."""

import json

import numpy as np

from src.precompute_cache import write_json
from src.scoring import METRICS, ROOT, UNITS, historical_metrics, preload, score_rotations

UNKNOWN = [
    "Satellites do not directly measure soil nitrogen or organic carbon. Verify these with soil samples.",
    "NASA POWER soil wetness is a model product.",
    "Irrigation share, baseline management, prices and pest pressure need local evidence.",
    "Crop income is a relative index. Market prices and yield can change.",
]


def summarise(raw, scores, weights):
    objectives = np.stack([scores @ w for w in weights.values()], axis=-1)
    maximum = objectives.max(axis=1, keepdims=True)
    tied = np.isclose(objectives, maximum, atol=1e-10, rtol=0)
    win_share = (tied / tied.sum(axis=1, keepdims=True)).mean(axis=0)
    regrets = maximum - objectives
    quantiles = np.quantile(raw, [.1, .5, .9], axis=0)
    return [
        {"metrics": {key: {"p10": round(float(v[0]), 4), "p50": round(float(v[1]), 4),
                           "p90": round(float(v[2]), 4), "unit": unit}
                     for key, v, unit in zip(METRICS, quantiles[:, i, :].T, UNITS, strict=True)},
         "wins_pct": {key: round(100 * float(win_share[i, j]), 2) for j, key in enumerate(weights)},
         "mean_regret": {key: round(float(regrets[:, i, j].mean()), 5) for j, key in enumerate(weights)}}
        for i in range(raw.shape[1])
    ]


def simulate(model, result, assessment, presets, config):
    rng = np.random.default_rng(config["seed"])
    draws = config["draws"]
    spread = config["parameter_range_fraction"]
    strategies = result["strategies"]
    rotations = np.array([[model.ids.index(crop) for row in strategy["crop_ids"] for crop in row]
                          for strategy in strategies])
    slots = np.arange(rotations.shape[1]) % len(model.season_labels)
    weights = {name: np.array([value[key] for key in METRICS]) for name, value in presets.items()}
    regimes = assessment["metrics"]["annual_climate_regimes"]["value"]
    years = sorted(set.intersection(*(set(model.histories[slot, crop]) for slot, crop in
                   set(zip(np.tile(slots, len(rotations)), rotations.ravel())))))
    if not years:
        raise ValueError("No common climate years for uncertainty comparison")
    groups = {}
    for year in years:
        groups.setdefault(regimes.get(str(year), "unclassified"), []).append(year)
    # Sample regimes in empirical proportions and years uniformly conditional on regime.
    group_years = list(groups.values())
    chosen_groups = rng.choice(len(groups), size=(draws, rotations.shape[1]),
                               p=[len(group) / len(years) for group in group_years])
    year_choices = np.empty_like(chosen_groups)
    for i, group in enumerate(group_years):
        mask = chosen_groups == i
        year_choices[mask] = rng.choice(group, mask.sum())
    crop_scales = rng.uniform(1-spread, 1+spread, (draws, 5, len(model.ids)))
    supply = model.farm["irrigation"]["supply_fraction"]
    scenarios = {"historical": (supply, 0, 1),
                 "warmer_drier": (supply, config["scenario_temperature_change_c"], config["scenario_rainfall_factor"]),
                 "less_irrigation": (max(0, supply-config["supply_fraction_offset"]), 0, 1),
                 "more_irrigation": (min(1, supply+config["supply_fraction_offset"]), 0, 1)}
    outputs = {}
    for scenario, (share, heat, rain) in scenarios.items():
        values = np.empty((draws, len(rotations), len(METRICS)))
        scores = np.empty_like(values)
        for draw, scales in enumerate(crop_scales):
            # Average crop-window outcomes over all occurrences in each candidate sequence.
            for i, rotation in enumerate(rotations):
                additions = model.additions.copy()
                for slot, index in set(zip(slots, rotation)):
                    chosen = year_choices[draw, (slots == slot) & (rotation == index)]
                    row = historical_metrics(model.histories[slot, index], model.crops[model.ids[index]],
                                             model.storage, model.slope, share, model.policy,
                                             water_factor=scales[0, index], heat_shift=heat, rain_factor=rain,
                                             years=chosen).mean(axis=0)
                    row[2] *= scales[3, index]
                    row[4] = np.clip(row[4] * scales[4, index], 0, 1)
                    additions[slot, index] = row
                raw, score, _ = score_rotations(model, rotation, additions=additions,
                                                credits=model.credits * scales[1], demand=model.demand * scales[2])
                values[draw, i] = raw[0]
                scores[draw, i] = score[0]
        outputs[scenario] = {"supply_fraction": share, "temperature_change_c": heat,
                             "rainfall_factor": rain, "strategies": {
             row["strategy_id"]: stats for row, stats in zip(strategies, summarise(values, scores, weights), strict=True)}}
    return {"farm_id": model.farm["farm_id"], "label": "illustrative; validate locally",
            "draws": draws, "seed": config["seed"], "parameter_source": "config/uncertainty.json",
            "climate_source": "NASA POWER historical years and seeded climate regimes",
            "limitations": ["Wins and regret compare the displayed strategies. Tied wins divide credit.",
                            "Scenario ranges are conditional on illustrative parameter spreads and chosen strategies."],
            "unknowns": UNKNOWN + model.farm["validation_flags"], "scenarios": outputs}


def main():
    farms = json.loads((ROOT / "config/farms.json").read_text())
    weights = json.loads((ROOT / "config/weights_presets.json").read_text())["presets"]
    config = json.loads((ROOT / "config/uncertainty.json").read_text())
    directory = ROOT / "data/processed"
    for farm in farms:
        identifier = farm["farm_id"]
        result = json.loads((directory / f"strategies_{identifier}.json").read_text())
        assessment = json.loads((directory / f"assessment_{identifier}.json").read_text())
        write_json(directory / f"uncertainty_{identifier}.json",
                   simulate(preload(farm), result, assessment, weights, config))
        print(identifier, flush=True)


if __name__ == "__main__":
    main()
