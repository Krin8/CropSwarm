"""P33 split-conformal intervals for cached county winter-wheat features."""

import hashlib
import json
from math import ceil

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from src.climate_yield import CountyTrends, LEARNERS, grouped_splits, make_model, rmse, tune
from src.climate_yield_validity import attach_districts
from src.county_yield_data import FEATURES
from src.data_pipeline import ROOT, atomic_write
from src.local_recalibration import YEARS, district_windows
from src.precompute_cache import write_json

LEVELS = (80, 90)
KEYS = ["fips", "year"]
COLUMNS = [*KEYS, "district", "yield_bu_ac"]


def conformal_radius(scores, level):
    """Finite-sample conformal order statistic, without interpolating the tail."""
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 1 or not len(scores) or not np.isfinite(scores).all() or (scores < 0).any():
        raise ValueError("Calibration needs finite nonnegative errors")
    if level not in LEVELS:
        raise ValueError("Unsupported interval level")
    # Integer arithmetic implements ceil((n + 1) * level / 100).
    rank = ((len(scores) + 1) * level + 99) // 100
    return float(np.partition(scores, rank - 1)[rank - 1]) if rank <= len(scores) else np.inf


def fit_split(train, group, config, *, held=None):
    """Reserve the calibration block before tuning or fitting either learner."""
    train = train.sort_values(KEYS).reset_index(drop=True)
    if held is not None and (set(train[group]) & set(held[group])):
        raise ValueError(f"Outer holdout overlaps the {group} training groups")
    fit, reserved = next(grouped_splits(train, group, config["inner_folds"]))
    proper, calibration = train.iloc[fit], train.iloc[reserved]
    selected = tune(proper, group, config)
    trends = CountyTrends(proper)
    residual = proper.yield_bu_ac.to_numpy() - trends.predict(proper)[1]
    matrix = proper[list(FEATURES)].to_numpy()
    fits = {name: make_model(name, selected[name], config).fit(matrix, residual) for name in LEARNERS}
    centers = predict(calibration, trends, fits)
    errors = {name: abs(calibration.yield_bu_ac.to_numpy() - centers[name]) for name in LEARNERS}
    audit = {"group": group, "proper_groups": sorted(proper[group].unique().tolist()),
             "calibration_groups": sorted(calibration[group].unique().tolist()),
             "proper_rows": len(proper), "calibration_rows": len(calibration), "selected": selected}
    return trends, fits, errors, audit


def predict(frame, trends, fits):
    mean, trend = trends.predict(frame)
    matrix = frame[list(FEATURES)].to_numpy()
    return {"county_mean": mean, **{name: trend + estimator.predict(matrix) for name, estimator in fits.items()}}


def interval_rows(frame, predictions, errors, **labels):
    base = frame[COLUMNS].copy()
    actual = base.yield_bu_ac.to_numpy()
    results = []
    for model in LEARNERS:
        center = predictions[model]
        for level in LEVELS:
            radius = conformal_radius(errors[model], level)
            results.append(base.assign(**labels, model=model, level=level, center=center,
                                       radius=radius, lower=center - radius, upper=center + radius,
                                       covered=(actual >= center - radius) & (actual <= center + radius),
                                       county_mean=predictions["county_mean"], calibration_rows=len(errors[model])))
    return pd.concat(results, ignore_index=True)


def coverage_interval(frame, block, config):
    grouped = frame.groupby(block, sort=True).covered.agg(["sum", "size"])
    if len(grouped) <= 1:
        return None
    rng = np.random.default_rng(config["seed"])
    indices = rng.integers(len(grouped), size=(config["bootstrap_draws"], len(grouped)))
    draws = grouped["sum"].to_numpy()[indices].sum(axis=1) / grouped["size"].to_numpy()[indices].sum(axis=1)
    return np.quantile(draws, config["bootstrap_quantiles"]).tolist()


def summarize(frame, block, config):
    rows = []
    for (model, level), group in frame.groupby(["model", "level"], sort=False):
        coverage = float(group.covered.mean())
        bounded = np.isfinite(group.radius).all()
        width = float(2 * group.radius.mean()) if bounded else None
        baseline = (rmse(group.yield_bu_ac.to_numpy(), group.county_mean.to_numpy())
                    if group.county_mean.notna().all() else None)
        rows.append({"model": model, "level": int(level), "n": len(group), "covered": int(group.covered.sum()),
                     "coverage": coverage, "undercoverage": coverage < level / 100,
                     "coverage_95": coverage_interval(group, block, config),
                     "bootstrap_block": block, "blocks": int(group[block].nunique()),
                     "mean_width": width, "unbounded": int((~np.isfinite(group.radius)).sum()),
                     "county_mean_rmse": baseline,
                     "width_to_county_mean_rmse": width / baseline if width is not None and baseline else None,
                     "calibration_rows_min": int(group.calibration_rows.min()),
                     "calibration_rows_max": int(group.calibration_rows.max())})
    return rows


def kansas_evaluation(frame, config):
    annual_means = frame.groupby("year").yield_bu_ac.mean().sort_values(kind="stable")
    count = ceil(len(annual_means) / 10)
    extremes = {"low": annual_means.index[:count].tolist(), "high": annual_means.index[-count:].tolist()}
    reports, predictions = {}, []
    for outer, inner in (("district", "year"), ("year", "district")):
        folds, all_rows = [], []
        for fit, held in grouped_splits(frame, outer):
            test = frame.iloc[held]
            label = str(test[outer].iloc[0])
            trend, models, errors, audit = fit_split(frame.iloc[fit], outer, config, held=test)
            rows = interval_rows(test, predict(test, trend, models), errors, protocol=f"kansas_{outer}",
                                 state="20", fold=label, k=-1)
            folds.append({"fold": label, "audit": audit, "results": summarize(rows, inner, config)})
            all_rows.append(rows)
        scores = pd.concat(all_rows, ignore_index=True)
        diagnostics = {block: [
            {"group": str(key), "results": summarize(group, "year" if block == "district" else "district", config)}
            for key, group in scores.groupby(block, sort=True)] for block in ("district", "year")}
        reports[outer] = {"pooled": summarize(scores, outer, config), "folds": folds, "diagnostics": diagnostics,
                          "extremes": {label: summarize(scores.loc[scores.year.isin(years)], outer, config)
                                       for label, years in extremes.items()}}
        predictions.append(scores)
    return reports, extremes, predictions


def match_baseline(frame, reference, col):
    """Join frozen baseline predictions and verify exact evaluated observations."""
    wanted = frame.set_index(KEYS)
    baseline = reference.set_index(KEYS)
    if (not wanted.index.is_unique or not baseline.index.is_unique or set(wanted.index) != set(baseline.index)):
        raise ValueError("The baseline and interval county-years differ")
    aligned = baseline.reindex(wanted.index)
    if not np.array_equal(aligned.yield_bu_ac, wanted.yield_bu_ac):
        raise ValueError("The baseline and interval yields differ")
    return aligned[col].to_numpy()


def transfer_evaluation(kansas, targets, p32, p37, p37_predictions, config):
    trends, models, errors, audit = fit_split(kansas, "district", config)
    source_fits, reports, outputs = {}, {}, []
    for state, target in targets.items():
        direct = predict(target, trends, models)
        direct["county_mean"] = match_baseline(target, p32.loc[p32.case.eq(f"in_state_{state}")], "county_mean")
        direct_rows = interval_rows(target, direct, errors, protocol="p32_transfer", state=state, fold="all", k=-1)
        outputs.append(direct_rows)
        by_district = []
        local = target.loc[target.practice.eq("non_irrigated")]
        for item in p37["states"][state]["districts"]:
            if item["status"] != "retained":
                continue
            district = item["district"]
            history, tail, years = district_windows(local.loc[local.district.eq(district)])
            if years[YEARS[-1]:] != item["common_test_years"]:
                raise ValueError("The local test years differ from P37")
            origin = min(item["common_test_years"])
            if origin not in source_fits:
                source_fits[origin] = fit_split(
                    kansas.loc[kansas.practice.eq("non_irrigated") & kansas.year.lt(origin)], "district", config)
            source_trends, source_models, source_errors, _ = source_fits[origin]
            centers = predict(tail, source_trends, source_models)
            for k, calibration in history.items():
                if k:
                    if (calibration.year.max() >= origin or calibration.year.unique().size != k
                            or sorted(calibration.year.unique()) != item["calibration"][str(k)]["years"]):
                        raise ValueError("Local calibration must match P37 and strictly precede the test")
                    estimates = predict(calibration, source_trends, source_models)
                    scores = {model: abs(calibration.yield_bu_ac.to_numpy() - estimates[model])
                              for model in LEARNERS}
                else:
                    scores = source_errors
                refs = p37_predictions.loc[p37_predictions.state.eq(state) & p37_predictions.k.eq(k)
                                           & p37_predictions.district.eq(district)]
                baseline = match_baseline(tail, refs, "county_mean")
                by_district.append(interval_rows(tail, {**centers, "county_mean": baseline}, scores,
                                                 protocol="p37_recalibration", state=state, fold=district, k=k))
        local_rows = pd.concat(by_district, ignore_index=True)
        outputs.append(local_rows)
        reports[state] = {"transfer": summarize(direct_rows, "district", config), "local": {}}
        for k, rows in local_rows.groupby("k", sort=True):
            reports[state]["local"][str(k)] = {"pooled": summarize(rows, "district", config),
                                               "districts": {key: summarize(group, "year", config)
                                                             for key, group in rows.groupby("district", sort=True)}}
    source_audits = {str(origin): {**fit[3], "last_eligible_year": origin - 1} for origin, fit in source_fits.items()}
    return reports, {"all_years": audit, "chronological": source_audits}, outputs


def build(root=ROOT):
    data = root / "data/processed"
    config_path = root / "config/climate_yield.json"
    config = json.loads(config_path.read_text())

    def read(name):
        return pd.read_csv(data / name, dtype={"fips": str, "district": str, "state": str}).sort_values(KEYS)

    mapping = root / "data/raw/p27/kansas_reporting_districts.csv"
    ks = attach_districts(read("climate_yield_features.csv"), pd.read_csv(mapping, dtype=str)).reset_index(drop=True)
    targets = {state: read(f"climate_yield_transfer_{state}_features.csv") for state in ("31", "40")}
    p37 = json.loads((data / "climate_yield_recalibration.json").read_text())
    with threadpool_limits(limits=1):
        kansas, extremes, ks_rows = kansas_evaluation(ks, config)
        transfer, audit, tr_rows = transfer_evaluation(
            ks, targets, read("climate_yield_transfer_predictions.csv"), p37,
            read("climate_yield_recalibration_predictions.csv"), config)
    intervals = pd.concat([*ks_rows, *tr_rows], ignore_index=True)
    if intervals.duplicated(["protocol", "state", *KEYS, "model", "level", "k"]).any():
        raise ValueError("Duplicate interval evaluation")
    counts = intervals.groupby("protocol").size().to_dict()
    inputs = [config_path, mapping, *(data / name for name in (
        "climate_yield_features.csv", "climate_yield_transfer_31_features.csv", "climate_yield_transfer_40_features.csv",
        "climate_yield_transfer_predictions.csv", "climate_yield_recalibration.json",
        "climate_yield_recalibration_predictions.csv"))]
    report = {"label": "illustrative, validate locally", "levels": LEVELS, "k": YEARS,
              "interval_evaluations": len(intervals), "counts": counts, "kansas": kansas, "extreme_years": extremes,
              "transfer": transfer, "source_audit": audit, "bootstrap_draws": config["bootstrap_draws"],
              "seed": config["seed"], "input_sha256": {
                  str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}}
    atomic_write(data / "climate_yield_interval_predictions.csv", lambda path: intervals.to_csv(path, index=False))
    write_json(data / "climate_yield_intervals.json", report)


if __name__ == "__main__":
    build()
