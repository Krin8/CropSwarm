"""P37 common-tail learning curves using only cached non-irrigated wheat records."""

from collections import Counter
import hashlib
import json

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from src.climate_yield import CountyTrends, METRICS, grouped_splits, make_model, rmse, statistics
from src.climate_yield_validity import attach_districts
from src.county_yield_data import FEATURES
from src.cross_state_yield import STATE_NAMES, validate
from src.data_pipeline import ROOT, atomic_write
from src.precompute_cache import write_json

YEARS = (0, 3, 5, 8, 12)
METHODS = {
    "source": "Kansas source only",
    "source_adjusted": "Source + local intercept/trend",
    "local_ridge": "Local ridge",
    "source_feature": "Local ridge + source feature",
    "local_trend": "Local trend",
    "county_mean": "Local county mean",
}
RIDGES = {"local_ridge": list(FEATURES), "source_feature": [*FEATURES, "source"]}


def district_windows(frame):
    """Keep the later test tail fixed on the maximum calibration length."""
    years = sorted(frame.year.unique().tolist())
    if len(years) <= YEARS[-1]:
        raise ValueError("Fewer than 13 observed years")
    tail = frame.loc[frame.year.ge(years[YEARS[-1]])].copy()
    history = {k: frame.loc[frame.year.isin(years[:k])].copy() for k in YEARS}
    return history, tail, years


def fit_source(train, config):
    """Train only the preregistered P25 forest with its existing nested district recipe."""
    grid = [{"min_samples_leaf": leaf} for leaf in config["forest_min_leaf"]]
    loss = np.zeros(len(grid))
    for fit, valid in grouped_splits(train, "district", config["inner_folds"]):
        fit_rows, held = train.iloc[fit], train.iloc[valid]
        trends = CountyTrends(fit_rows)
        values = fit_rows.yield_bu_ac.to_numpy() - trends.predict(fit_rows)[1]
        target = held.yield_bu_ac.to_numpy() - trends.predict(held)[1]
        for i, setting in enumerate(grid):
            model = make_model("random_forest", setting, config).fit(fit_rows[list(FEATURES)].to_numpy(), values)
            loss[i] += np.square(target - model.predict(held[list(FEATURES)].to_numpy())).sum()
    selected = grid[int(np.argmin(loss))]
    trends = CountyTrends(train)
    residual = train.yield_bu_ac.to_numpy() - trends.predict(train)[1]
    model = make_model("random_forest", selected, config).fit(train[list(FEATURES)].to_numpy(), residual)
    return trends, model, selected


def source_prediction(rows, source):
    trends, model, _ = source
    return trends.predict(rows)[1] + model.predict(rows[list(FEATURES)].to_numpy())


def forward_alpha(train, columns, config):
    """Choose alpha using only earlier years in each local inner fold."""
    years = sorted(train.year.unique())
    grid = config["ridge_alphas"]
    loss = np.zeros(len(grid))
    for year in years[1:]:
        fit, held = train.loc[train.year.lt(year)], train.loc[train.year.eq(year)]
        x = fit[columns].to_numpy()
        y = fit.yield_bu_ac.to_numpy()
        for i, alpha in enumerate(grid):
            ridge = make_model("ridge", {"alpha": alpha}, config).fit(x, y)
            loss[i] += np.square(held.yield_bu_ac.to_numpy() - ridge.predict(held[columns].to_numpy())).sum()
    return grid[int(np.argmin(loss))]


def predict_local(history, tail, config):
    if history.empty or history.year.max() >= tail.year.min():
        raise ValueError("Local calibration must precede the common test tail")
    county_mean, local_trend = CountyTrends(history).predict(tail)
    origin = history.year.min()
    x = history.year.to_numpy() - origin
    y = history.yield_bu_ac.to_numpy() - history.source.to_numpy()
    intercept, slope = np.linalg.lstsq(np.column_stack([np.ones(len(x)), x]), y, rcond=None)[0]
    predictions = {"source_adjusted": tail.source.to_numpy() + intercept + slope * (tail.year.to_numpy() - origin),
                   "local_trend": local_trend, "county_mean": county_mean}
    selections = {}
    for name, columns in RIDGES.items():
        alpha = forward_alpha(history, columns, config)
        selections[name] = alpha
        model = make_model("ridge", {"alpha": alpha}, config).fit(history[columns].to_numpy(),
                                                               history.yield_bu_ac.to_numpy())
        predictions[name] = model.predict(tail[columns].to_numpy())
    return predictions, selections


def curve_summary(rows, config):
    """Pair all curves to the same test rows and district bootstrap resamples."""
    groups = list(rows[rows.k.eq(YEARS[0])].groupby("district", sort=True).indices.values())
    rng = np.random.default_rng(config["seed"])
    samples = [np.concatenate([groups[i] for i in rng.integers(len(groups), size=len(groups))])
               for _ in range(config["bootstrap_draws"])]

    def summarize(point, values):
        valid = [x for x in values if x is not None]
        bounds = np.quantile(valid, config["bootstrap_quantiles"]).tolist() if valid else None
        return {"value": point, "bootstrap_95": bounds, "bootstrap_n": len(valid)}

    reference = rows.loc[rows.k.eq(0), ["fips", "year", "yield_bu_ac"]].reset_index(drop=True)
    output = {}
    for k in YEARS:
        frame = rows.loc[rows.k.eq(k)].reset_index(drop=True)
        if not frame[list(reference)].equals(reference):
            raise ValueError("The common test rows differ across calibration sizes")
        actual = frame.yield_bu_ac.to_numpy()
        baseline = frame.local_trend.to_numpy()
        have_baseline = np.isfinite(baseline).all()
        baseline_draws = [rmse(actual[ix], baseline[ix]) for ix in samples] if have_baseline else []
        output[str(k)] = {}
        for method in METHODS:
            pred = frame[method].to_numpy()
            if np.isnan(pred).all():
                output[str(k)][method] = {"status": "unavailable at zero local years"}
                continue
            if not np.isfinite(pred).all():
                raise ValueError(f"Invalid predictions for {method} at k={k}")
            point = statistics(actual, pred)
            draws = [statistics(actual[ix], pred[ix]) for ix in samples]
            entry = {key: summarize(value, draw) for key, value, draw in zip(METRICS, point, zip(*draws), strict=True)}
            entry["status"] = "complete"
            entry["rmse_delta_vs_local_trend"] = (
                summarize(point[1] - rmse(actual, baseline),
                          [value[1] - base for value, base in zip(draws, baseline_draws, strict=True)])
                if have_baseline else None)
            output[str(k)][method] = entry
    return output


def evaluate(kansas, targets, config):
    kansas = validate(kansas, "20")
    sources, origins, states, all_predictions = {}, {}, {}, []
    for state, frame in targets.items():
        frame = validate(frame, state)
        metadata, district_predictions = [], []
        local_fit_counts = Counter()
        for code, district in frame.groupby("district", sort=True):
            years = sorted(district.year.unique().tolist())
            info = {"district": code, "district_name": district.district_name.iloc[0], "observed_years": years}
            if len(years) <= YEARS[-1]:
                metadata.append({**info, "status": "fewer than 13 observed years"})
                continue
            history, tail, years = district_windows(district)
            origin = years[YEARS[-1]]
            training = kansas.loc[kansas.year.lt(origin)]
            if training.district.nunique() < config["inner_folds"]:
                metadata.append({**info, "status": "too few Kansas inner groups"})
                continue
            if origin not in sources:
                sources[origin] = fit_source(training, config)
                origins[str(origin)] = {
                    "training_rows": len(training), "training_counties": int(training.fips.nunique()),
                    "first_year": int(training.year.min()), "last_year": int(training.year.max()),
                    "selected": sources[origin][2],
                }
            fixed = sources[origin]
            tail["source"] = source_prediction(tail, fixed)
            first = tail[["fips", "year", "district", "yield_bu_ac", "source"]]
            folds = {}
            for k, subset in history.items():
                if k:
                    subset["source"] = source_prediction(subset, fixed)
                    scores, alphas = predict_local(subset, tail, config)
                    local_fit_counts["ridge_inner"] += len(RIDGES) * len(config["ridge_alphas"]) * (k - 1)
                    local_fit_counts["ridge_outer"] += len(RIDGES)
                    local_fit_counts["ordinary_least_squares_and_mean"] += 3
                    folds[str(k)] = {"n": len(subset), "years": years[:k], "selected_alpha": alphas,
                                     "test_counties_without_local_yield": len(set(tail.fips) - set(subset.fips))}
                else:
                    scores = dict.fromkeys((key for key in METHODS if key != "source"), np.nan)
                    folds[str(k)] = {"n": 0, "years": [], "selected_alpha": {}}
                district_predictions.append(first.assign(k=k, **scores))
            metadata.append({**info, "status": "retained", "common_test_years": years[YEARS[-1]:],
                             "test_rows": len(tail), "test_counties": int(tail.fips.nunique()), "calibration": folds})
        if not district_predictions:
            raise ValueError(f"No district supports the preregistered common test in {STATE_NAMES[state]}")
        rows = pd.concat(district_predictions, ignore_index=True)
        curve = curve_summary(rows, config)
        first_k = {}
        for method in METHODS:
            deltas = ((k, curve[str(k)][method].get("rmse_delta_vs_local_trend")) for k in YEARS)
            first_k[method] = next((k for k, item in deltas if item and item["bootstrap_95"][1] < 0), None)
        test = rows.loc[rows.k.eq(0)]
        states[state] = {"name": STATE_NAMES[state], "test_rows": len(test),
                         "test_counties": int(test.fips.nunique()), "district_blocks": int(test.district.nunique()),
                         "first_test_year": int(test.year.min()), "last_test_year": int(test.year.max()),
                         "districts": metadata, "curves": curve, "smallest_k_beating_trend": first_k,
                         "local_fit_counts": dict(local_fit_counts)}
        all_predictions.append(rows.assign(state=state))
    source_fit_counts = {"grid_configs": len(config["forest_min_leaf"]),
                         "inner_learned": len(sources) * config["inner_folds"] * len(config["forest_min_leaf"]),
                         "outer_learned": len(sources)}
    return {"label": "illustrative, validate locally", "local_years": YEARS, "methods": METHODS, "states": states,
            "source_origins": origins, "source_fit_counts": source_fit_counts, "ridge_grid": config["ridge_alphas"],
            "source_leaf_grid": config["forest_min_leaf"], "bootstrap_draws": config["bootstrap_draws"],
            "seed": config["seed"]}, pd.concat(all_predictions, ignore_index=True)


def build(root=ROOT):
    processed = root / "data/processed"
    config_path = root / "config/climate_yield.json"
    config = json.loads(config_path.read_text())
    feature_files = {"20": processed / "climate_yield_features.csv",
                     **{key: processed / f"climate_yield_transfer_{key}_features.csv" for key in ("31", "40")}}
    district_map = root / "data/raw/p27/kansas_reporting_districts.csv"
    frames = {key: pd.read_csv(path, dtype={"fips": str, "district": str}).loc[lambda x: x.practice.eq("non_irrigated")]
              for key, path in feature_files.items()}
    kansas = attach_districts(frames.pop("20"), pd.read_csv(district_map, dtype=str))
    with threadpool_limits(limits=1):
        report, predictions = evaluate(kansas, frames, config)
    report["source_files_sha256"] = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                                     for path in (*feature_files.values(), district_map, config_path)}
    atomic_write(processed / "climate_yield_recalibration_predictions.csv",
                 lambda path: predictions.to_csv(path, index=False))
    write_json(processed / "climate_yield_recalibration.json", report)


if __name__ == "__main__":
    build()
