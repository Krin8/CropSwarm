"""P41 one-driver-at-a-time diagnostic of the frozen scoring and county-yield models."""

import json

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from threadpoolctl import threadpool_limits

from src.climate_yield import CountyTrends, LEARNERS, grouped_splits, make_model
from src.climate_yield_validity import attach_districts
from src.county_yield_data import FEATURES, FEATURE_LABELS
from src.cross_state_yield import STATE_NAMES, validate
from src.precompute_cache import write_json
from src.scoring import METRICS, ROOT, historical_metrics, preload, score_rotations

OUTPUT = "scoring_response_check.json"
FARM_ID = "us_high_plains_b"
CROP = "winter_wheat"
GRIDS = {"water_deficit_mm": tuple(range(0, 501, 25)),
         "heat_days": tuple(sorted({*range(0, 61, 5), 26, 27}))}
LINKED = {"water_deficit_mm": "water", "heat_days": "climate_fit"}
SCORES = ("water", "climate_fit")
KEY = ["fips", "year"]
EPSILON = 1e-9


def verify_windows(rows, onset, length):
    starts = pd.to_datetime({"year": rows.year - 1, "month": onset, "day": 1})
    ends = starts + pd.Timedelta(days=length - 1)
    if (not rows.window_start.eq(starts.dt.strftime("%Y-%m-%d")).all()
            or not rows.window_end.eq(ends.dt.strftime("%Y-%m-%d")).all()):
        raise ValueError("County feature windows do not match the scoring window")


def scoring_curves(model, medians, grids=GRIDS):
    """Expose the crop's own scoring transforms through a one-slot synthetic season."""
    crop = model.crops[CROP]
    index = model.ids.index(CROP)
    label, _, length = model.days[0, index]
    supply = model.farm["irrigation"]["supply_fraction"]
    if len(model.season_labels) != 1 or label != "cool" or supply != 0:
        raise ValueError("P41 requires the Kansas cool-season rainfed scoring reference")

    curves = {}
    for driver, grid in grids.items():
        histories, deficits = {}, []
        for i, value in enumerate(grid):
            deficit = value if driver == "water_deficit_mm" else medians["water_deficit_mm"]
            heat_days = value if driver == "heat_days" else medians["heat_days"]
            if not 0 <= heat_days <= length or heat_days != int(heat_days):
                raise ValueError("The synthetic season requires an integer hot-day count")
            window = np.full((length, 3), [medians["rainfall_mm"] / length, medians["mean_temp_c"],
                                          crop["heat_tolerance_c"]], dtype=float)
            window[:int(heat_days), 2] = np.nextafter(crop["heat_tolerance_c"], np.inf)
            histories[i] = window
            deficits.append(deficit)
        values = historical_metrics(histories, crop, model.storage, model.slope, supply, model.policy)
        curves[driver] = {name: [] for name in SCORES}
        for metrics, deficit in zip(values, deficits, strict=True):
            additions = model.additions.copy()
            additions[0, index] = metrics
            # The swept deficit is an intervention downstream of the daily bucket.
            additions[0, index, :2] = (deficit, deficit / crop["water_need_mm"])
            _, scores, _ = score_rotations(model, [[index]], additions=additions)
            for name in SCORES:
                curves[driver][name].append(float(scores[0, METRICS.index(name)]))
    return curves


def partial_dependence(model, held_features, column, grid):
    values = np.tile(held_features, (len(grid), 1))
    values[:, column] = np.repeat(grid, len(held_features))
    means = model.predict(values).reshape(len(grid), len(held_features)).mean(axis=1)
    return means - means[0]


def fold_curves(train, test, saved, selected, config, grids=GRIDS):
    if set(train.district) & set(test.district) or set(train.fips) & set(test.fips):
        raise ValueError("P41 training data include a held-out district or county")
    trends = CountyTrends(train)
    trend = trends.predict(test)[1]
    residual = train.yield_bu_ac.to_numpy() - trends.predict(train)[1]
    x_train, x_test = (frame[list(FEATURES)].to_numpy() for frame in (train, test))
    curves, errors = {}, {}
    for learner in LEARNERS:
        model = make_model(learner, selected[learner], config).fit(x_train, residual)
        error = float(np.max(np.abs(trend + model.predict(x_test) - saved[learner])))
        if not np.isfinite(error) or error > EPSILON:
            raise ValueError(f"Reconstructed {learner} does not match the saved district predictions ({error})")
        errors[learner] = error
        curves[learner] = {feature: partial_dependence(model, x_test, FEATURES.index(feature), grid)
                           for feature, grid in grids.items()}
    return curves, errors


def state_folds(rows, saved, reference, config, grids=GRIDS):
    saved = saved.set_index(KEY)
    keys = pd.MultiIndex.from_frame(rows[KEY])
    if not saved.index.is_unique or set(saved.index) != set(keys):
        raise ValueError("P41 county-years differ from saved held-out predictions")
    saved = saved.reindex(keys)
    for field in ("district", "yield_bu_ac", "practice"):
        if not np.array_equal(rows[field], saved[field]):
            raise ValueError(f"P41 {field} differs from saved held-out data")

    selected = {str(fold["held_out"]): fold for fold in reference["folds"]}
    if set(selected) != set(rows.district):
        raise ValueError("P41 districts differ from the earlier runs")
    curves, audit = [], []
    for fit, held in grouped_splits(rows, "district"):
        train, test = rows.iloc[fit], rows.iloc[held]
        district = test.district.iloc[0]
        record = selected[district]
        if len(test) != record["n"]:
            raise ValueError(f"Unexpected count for held-out district {district}")
        points, errors = fold_curves(train, test, saved.iloc[held], record["selected"], config, grids)
        curves.append(points)
        audit.append({"district": district, "n": len(held), "n_train": len(fit),
                      "settings": record["selected"], "max_prediction_difference_bu_ac": errors})
    return curves, audit


def curve_sign(values):
    changes = np.diff(values)
    return np.where(np.abs(changes) <= EPSILON, 0, np.sign(changes)).astype(int)


def shape(signs):
    up, down = np.any(signs > 0), np.any(signs < 0)
    if up and down:
        return "non-monotone"
    if up:
        return "non-decreasing"
    if down:
        return "non-increasing"
    return "flat"


def rank_curve(values):
    # Stable numerical ties are grouped by adjacent sorted differences.
    order = np.argsort(values, kind="stable")
    groups = np.cumsum(np.r_[False, np.diff(values[order]) > EPSILON])
    return rankdata(groups)[np.argsort(order)]


def rank_agreement(score, data):
    if len(score) < 2 or shape(curve_sign(score)) == "flat" or shape(curve_sign(data)) == "flat":
        return None
    ranks = [rank_curve(values) for values in (score, data)]
    return float(np.corrcoef(*ranks)[0, 1])


def estimate_rho(score, point, draws, quantiles):
    rho = rank_agreement(score, point)
    samples = [value for draw in draws if (value := rank_agreement(score, draw)) is not None]
    return {"value": rho, "bootstrap_95": np.quantile(samples, quantiles).tolist()
            if rho is not None and samples else None, "bootstrap_n": len(samples)}


def compare(grid, scores, point, draws, support, quantiles):
    grid, scores, support = np.asarray(grid), np.asarray(scores), np.asarray(support, dtype=bool)
    left, right = curve_sign(scores), curve_sign(point)
    spans = []
    for lo, hi, score_sign, data_sign, inside in zip(
            grid[:-1], grid[1:], left, right, support[:-1] & support[1:], strict=True):
        sign_pair = (int(score_sign), int(data_sign))
        if spans and tuple(spans[-1]["signs"]) == sign_pair and spans[-1]["supported"] == inside:
            spans[-1]["end"] = int(hi)
        else:
            spans.append({"start": int(lo), "end": int(hi), "signs": list(sign_pair), "supported": bool(inside)})
    return {
        "score_shape": shape(left), "data_shape": shape(right), "spans": spans,
        "rho": estimate_rho(scores, point, draws, quantiles),
        "rho_supported": estimate_rho(scores[support], point[support], draws[:, support], quantiles),
        "supported_same_direction": sum(bool(a * b > 0 and s) for a, b, s in
                                        zip(left, right, support[:-1] & support[1:], strict=True)),
        "supported_opposite_direction": sum(bool(a * b < 0 and s) for a, b, s in
                                            zip(left, right, support[:-1] & support[1:], strict=True)),
    }


def summarize_state(rows, folds, audit, scoring, config, grids=GRIDS):
    weights = np.array([fold["n"] for fold in audit])
    rng = np.random.default_rng(config["seed"])
    draws = rng.integers(len(folds), size=(config["bootstrap_draws"], len(folds)))
    quantiles = config["bootstrap_quantiles"]
    drawn_weights = weights[draws]
    weather = {}
    for feature, grid in grids.items():
        lo, hi = float(rows[feature].min()), float(rows[feature].max())
        support = (lo <= np.asarray(grid)) & (np.asarray(grid) <= hi)
        learners = {}
        for learner in LEARNERS:
            values = np.array([fold[learner][feature] for fold in folds])
            point = np.average(values, axis=0, weights=weights)
            resampled = (values[draws] * drawn_weights[:, :, None]).sum(axis=1) / drawn_weights.sum(axis=1)[:, None]
            learners[learner] = {
                "partial_dependence_bu_ac": point.tolist(),
                "bootstrap_95": np.quantile(resampled, quantiles, axis=0).T.tolist(),
                "comparisons": {name: compare(grid, score, point, resampled, support, quantiles)
                                for name, score in scoring[feature].items()},
            }
        weather[feature] = {"observed_range": [lo, hi], "grid_supported": support.tolist(),
                            "learners": learners}
    return {"county_years": len(rows), "counties": int(rows.fips.nunique()), "districts": len(folds),
            "first_year": int(rows.year.min()), "last_year": int(rows.year.max()),
            "practice_counts": rows.practice.value_counts().to_dict(), "fold_audit": audit, "weather": weather}


def ledger_summary(states):
    linked = [learner["comparisons"][LINKED[feature]] for state in states.values()
              for feature, weather in state["weather"].items() for learner in weather["learners"].values()]
    any_same = sum(result["supported_same_direction"] > 0 for result in linked)
    any_opposite = sum(result["supported_opposite_direction"] > 0 for result in linked)
    direction = "mixed"
    if any_same == len(linked) and not any_opposite:
        direction = "supports"
    elif any_opposite and not any_same:
        direction = "does not support"
    return {"linked_comparisons": len(linked), "with_same_direction": any_same,
            "with_opposite_direction": any_opposite, "direction": direction}


def build(root=ROOT):
    def read(path):
        return json.loads((root / path).read_text())

    def csv(path):
        return pd.read_csv(root / path, dtype={"fips": str, "district": str})

    processed = "data/processed"
    config = read("config/climate_yield.json")
    farm, = (item for item in read("config/farms.json") if item["farm_id"] == FARM_ID)
    model = preload(farm, root=root)
    _, onset, length = model.days[0, model.ids.index(CROP)]
    kansas = attach_districts(csv(f"{processed}/climate_yield_features.csv"),
                              csv("data/raw/p27/kansas_reporting_districts.csv"))
    medians = kansas[list(FEATURES)].median().to_dict()
    scoring = scoring_curves(model, medians)
    frames = {"20": kansas, **{state: csv(f"{processed}/climate_yield_transfer_{state}_features.csv")
                              for state in STATE_NAMES if state != "20"}}
    p27 = read(f"{processed}/climate_yield_validity_pooled.json")["schemes"]["leave_one_district_out"]
    p32 = read(f"{processed}/climate_yield_transfer.json")["cases"]
    target_saved = csv(f"{processed}/climate_yield_transfer_predictions.csv")
    saved = {"20": csv(f"{processed}/climate_yield_validity_pooled_predictions.csv"),
             **{state: target_saved.loc[target_saved.case.eq(f"in_state_{state}")] for state in ("31", "40")}}
    states = {}
    with threadpool_limits(limits=1):
        for state, raw in frames.items():
            frame = validate(raw, state)
            verify_windows(frame, onset, length)
            reference = p27 if state == "20" else p32[f"in_state_{state}"]
            folds, audit = state_folds(frame, saved[state], reference, config)
            states[state] = summarize_state(frame, folds, audit, scoring, config)
    report = {
        "label": "illustrative, validate locally",
        "design": {"source": "docs/p41_plan.md", "grid": GRIDS, "seed": config["seed"],
                   "bootstrap_draws": config["bootstrap_draws"], "bootstrap_quantiles": config["bootstrap_quantiles"],
                   "numeric_tolerance": EPSILON, "linked_scores": LINKED},
        "window": {"onset_month": onset, "duration_days": length,
                   "heat_tolerance_c": model.crops[CROP]["heat_tolerance_c"],
                   "max_hot_day_fraction": model.policy["max_hot_day_fraction"],
                   "sources": {"onset": f"{processed}/seasons_{FARM_ID}.json", "duration_and_heat": "data/crops.csv",
                               "hot_fraction": "config/scoring.json"}},
        "scoring_reference": {"kansas_medians": medians, "source": f"{processed}/climate_yield_features.csv",
                              "crop_water_demand_mm": model.crops[CROP]["water_need_mm"],
                              "storage_mm": model.storage, "irrigation_supply_fraction": farm["irrigation"]["supply_fraction"],
                              "sources": {"water_demand": "data/crops.csv",
                                          "storage": f"{processed}/context_{FARM_ID}.json",
                                          "irrigation": "config/farms.json"}},
        "feature_labels": {key: FEATURE_LABELS[key] for key in GRIDS},
        "state_names": STATE_NAMES, "states": states, "scoring": scoring, "summary": ledger_summary(states),
    }
    write_json(root / processed / OUTPUT, report)
    return report


if __name__ == "__main__":
    build()
