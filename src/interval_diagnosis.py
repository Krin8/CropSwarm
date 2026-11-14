"""P33b diagnostics and alternative radii for the existing P33 point centers."""

import gzip
import hashlib
import json

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from src.climate_yield import LEARNERS, grouped_splits
from src.climate_yield_validity import attach_districts
from src.county_yield_data import FEATURES
from src.data_pipeline import ROOT, atomic_write
from src.diagnostics import SEED
from src.local_recalibration import YEARS, district_windows
from src.precompute_cache import write_json
from src.validation import POWER_FILL_VALUE
from src.yield_intervals import LEVELS, KEYS, fit_split, predict, conformal_radius, coverage_interval

ANNUAL = {"rain": "PRECTOTCORR", "temp": "T2M", "high": "T2M_MAX"}
BANDWIDTH = 1.0
METHODS = {
    "reference": "P33 reference",
    "leave_year_out": "Leave-one-year-out scores",
    "inflated": "Training-only inflation",
    "mondrian": "Weather-regime Mondrian",
    "weighted": "Climate-similarity weighting",
}


def cached_weather(root, held_2007):
    """Recover complete calendar-year series and assess county-level frost availability."""
    rows, frost, archives = [], [], []
    for archive in ("p25", "p32"):
        for path in sorted((root / f"data/raw/{archive}/power_archive").glob("*/*.json.gz")):
            archives.append(path)
            body = json.loads(gzip.decompress(path.read_bytes()))["body"]
            fields = body["properties"]["parameter"]
            fill = body["header"].get("fill_value", POWER_FILL_VALUE)
            mapping = {name: pd.Series(fields[field], dtype=float) for name, field in ANNUAL.items()}
            if "T2M_MIN" in fields:
                mapping["minimum"] = pd.Series(fields["T2M_MIN"], dtype=float)
            weather = pd.DataFrame(mapping).replace([fill, POWER_FILL_VALUE, np.inf, -np.inf], np.nan)
            weather.index = pd.to_datetime(weather.index, format="%Y%m%d")
            fips = path.parent.name
            for year, data in weather.groupby(weather.index.year):
                dates = pd.date_range(f"{year}-01-01", f"{year}-12-31")
                annual = data.reindex(dates)[list(ANNUAL)]
                if annual.notna().all().all():
                    rows.append({"fips": fips, "year": int(year), "rain": annual.rain.sum(),
                                 "temp": annual.temp.mean(), "high": annual.high.mean()})
                if year == 2007 and fips in held_2007 and "minimum" in data:
                    spring = data.minimum.reindex(pd.date_range("2007-03-01", "2007-05-31"))
                    if spring.notna().all():
                        frost.append({"fips": fips, "spring_min_c": float(spring.min())})
    if not rows:
        raise ValueError("No annual county weather was recovered from POWER")
    return pd.DataFrame(rows), pd.DataFrame(frost, columns=["fips", "spring_min_c"]), archives


def fit_regimes(proper):
    matrix = proper[list(ANNUAL)].dropna().to_numpy()
    if len(np.unique(matrix, axis=0)) < 3:
        return None
    scaler = StandardScaler().fit(matrix)
    fitted = KMeans(n_clusters=3, random_state=SEED, n_init=10).fit(scaler.transform(matrix))
    centers = fitted.cluster_centers_
    wet = int(np.argmax(centers[:, 0]))
    dry = max((idx for idx in range(3) if idx != wet), key=lambda idx: centers[idx, 2] - centers[idx, 0])
    return scaler, fitted, {wet: "wet", dry: "dry_hot"}


def classify(frame, regime):
    labels = np.full(len(frame), "", dtype=object)
    if regime is not None:
        scale, model, names = regime
        valid = frame[list(ANNUAL)].notna().all(axis=1).to_numpy()
        if valid.any():
            groups = model.predict(scale.transform(frame[list(ANNUAL)].to_numpy()[valid]))
            labels[valid] = [names.get(key, "normal") for key in groups]
    return labels


def spread_ratio(calibration, test):
    if len(calibration) < 2 or len(test) < 2:
        return None
    denominator = np.std(test, ddof=1)
    return float(np.std(calibration, ddof=1) / denominator) if denominator > 0 else None


def inflation_factor(calibration, residual):
    frame = calibration.assign(error=residual)
    ratios = []
    for _, group in frame.groupby("district", sort=True):
        years = sorted(group.year.unique())
        early = group.year.isin(years[:len(years) // 2])
        ratio = spread_ratio(group.error[~early], group.error[early])
        if ratio is not None:
            ratios.append(ratio)
    return (max(1.0, float(np.median(ratios))) if ratios else None), len(ratios)


def weighted_radius(scores, weights, level):
    order = np.argsort(scores, kind="stable")
    cumulative = np.cumsum(weights[order])
    # An atom with weight one at infinity represents the unseen test score.
    rank = np.searchsorted(cumulative, (cumulative[-1] + 1) * (level / 100))
    return float(scores[order[rank]]) if rank < len(scores) else np.inf


def year_profiles(frame, scaler):
    return (pd.DataFrame(scaler.transform(frame[list(FEATURES)].to_numpy()), index=frame.index)
            .groupby(frame.year).transform("mean").to_numpy())


def score_yearwise(calibration, centers):
    signed = calibration.yield_bu_ac.to_numpy() - centers
    loo = np.empty(len(signed))
    for positions in calibration.groupby("year").indices.values():
        # The model was frozen before any of these calibration rows were used.
        loo[positions] = np.abs(signed[positions])
    return signed, loo


def source_fit(train, group, config, held=None):
    trends, models, errors, audit = fit_split(train, group, config, held=held)
    proper = train.loc[train[group].isin(audit["proper_groups"])]
    calibration = train.loc[train[group].isin(audit["calibration_groups"])].sort_values(KEYS)
    estimates = predict(calibration, trends, models)
    factors = {}
    for name in LEARNERS:
        residual, loo = score_yearwise(calibration, estimates[name])
        np.testing.assert_allclose(loo, errors[name], rtol=1e-12, atol=1e-12)
        factor, n = inflation_factor(calibration, residual)
        factors[name] = {"factor": factor, "districts": n}
    return {"trends": trends, "models": models, "calibration": calibration,
            "factors": factors, "regimes": fit_regimes(proper), "audit": audit,
            "scaler": StandardScaler().fit(proper[list(FEATURES)].to_numpy())}


def make_rows(saved, test, calibration, fit):
    cal = calibration.sort_values(KEYS)
    test = test.sort_values(KEYS)
    estimated = predict(cal, fit["trends"], fit["models"])
    expected = predict(test, fit["trends"], fit["models"])
    cal_regime = classify(cal, fit["regimes"])
    test_regime = classify(test, fit["regimes"])
    c_profile = year_profiles(cal, fit["scaler"])
    t_profile = year_profiles(test, fit["scaler"])
    _, first, inverse = np.unique(test.year, return_index=True, return_inverse=True)
    test_centroids = t_profile[first]
    dist_sq = np.square(test_centroids[:, None, :] - c_profile).sum(axis=2)
    kernel = np.exp(-dist_sq / (2 * BANDWIDTH**2))
    rows, diagnostics = [], {}
    for model in LEARNERS:
        signed, loo = score_yearwise(cal, estimated[model])
        scores = np.abs(signed)
        diagnostics[model] = signed
        for level in LEVELS:
            base = saved.loc[saved.model.eq(model) & saved.level.eq(level)].sort_values(KEYS).copy()
            if not base[KEYS].reset_index(drop=True).equals(test[KEYS].reset_index(drop=True)):
                raise ValueError("P33 held-out county-years differ")
            np.testing.assert_allclose(base.center, expected[model], rtol=1e-10, atol=1e-10)
            radius = conformal_radius(scores, level)
            np.testing.assert_allclose(base.radius, radius, rtol=1e-10, atol=1e-10)
            if not np.array_equal(scores, loo):
                raise ValueError("Frozen calibration scores differ year by year")
            stratum = np.full(len(test), np.nan)
            for regime in ("wet", "dry_hot", "normal"):
                mask = cal_regime == regime
                stratum[test_regime == regime] = conformal_radius(scores[mask], level) if mask.any() else np.inf
            factor = fit["factors"][model]["factor"]
            radii = {"reference": base.radius.to_numpy(), "leave_year_out": radius,
                     "inflated": radius * factor if factor is not None else np.nan,
                     "mondrian": stratum,
                     "weighted": np.array([weighted_radius(scores, weights, level) for weights in kernel])[inverse]}
            for method, value in radii.items():
                lo, hi = base.center - value, base.center + value
                rows.append(base.assign(method=method, radius=value, lower=lo, upper=hi,
                                        covered=(base.yield_bu_ac.ge(lo) & base.yield_bu_ac.le(hi)),
                                        available=~np.isnan(np.broadcast_to(value, len(base)))))
    return pd.concat(rows, ignore_index=True), diagnostics


def summarize(rows, block, config):
    summaries = []
    for (method, model, level), all_rows in rows.groupby(["method", "model", "level"], sort=False):
        sub = all_rows.loc[all_rows.available]
        n = len(sub)
        unbounded = int(np.isinf(sub.radius).sum())
        coverage = float(sub.covered.mean()) if n else None
        summaries.append({"method": method, "model": model, "level": int(level), "n": n,
                          "unavailable": len(all_rows) - n, "unbounded": unbounded,
                          "coverage": coverage, "coverage_95": coverage_interval(sub, block, config) if n else None,
                          "mean_width": float(2 * sub.radius.mean()) if n and not unbounded else None,
                          "below_nominal": coverage < level / 100 if coverage is not None else None})
    return summaries


def kansas_results(kansas, saved, config):
    parts, reports = [], {}
    for group, within in (("district", "year"), ("year", "district")):
        folds, audit = [], {}
        protocol = f"kansas_{group}"
        for train, held in grouped_splits(kansas, group):
            test = kansas.iloc[held]
            label = str(test[group].iloc[0])
            fit = source_fit(kansas.iloc[train], group, config, held=test)
            fixed = saved.loc[saved.protocol.eq(protocol) & saved.fold.eq(label)]
            rows, _ = make_rows(fixed, test, fit["calibration"], fit)
            folds.append(rows)
            audit[label] = {**fit["audit"], "inflation": fit["factors"]}
        complete = pd.concat(folds, ignore_index=True)
        reports[group] = {"pooled": summarize(complete, group, config), "folds": {
            key: summarize(rows, within, config) for key, rows in complete.groupby("fold", sort=True)},
            "audit": audit}
        parts.append(complete)
    return reports, parts


def transfer_results(kansas, targets, prior_p37, saved, config):
    all_years = source_fit(kansas, "district", config)
    origins, parts, reports = {}, [], {}
    for state, target in targets.items():
        fixed = saved.loc[saved.state.eq(state)]
        spatial, _ = make_rows(fixed.loc[fixed.protocol.eq("p32_transfer")], target,
                               all_years["calibration"], all_years)
        parts.append(spatial)
        history_rows = {k: [] for k in YEARS}
        errors = {(k, name): ([], []) for k in YEARS for name in LEARNERS}
        local = target.loc[target.practice.eq("non_irrigated")]
        for item in prior_p37["states"][state]["districts"]:
            if item["status"] != "retained":
                continue
            district = item["district"]
            history, tail, years = district_windows(local.loc[local.district.eq(district)])
            if years[YEARS[-1]:] != item["common_test_years"]:
                raise ValueError("Common tail differs from P37")
            origin = min(item["common_test_years"])
            if origin not in origins:
                smaller = kansas.loc[kansas.practice.eq("non_irrigated") & kansas.year.lt(origin)]
                origins[origin] = source_fit(smaller, "district", config)
            fit = origins[origin]
            for k, cal in history.items():
                if k and (sorted(cal.year.unique()) != item["calibration"][str(k)]["years"]
                          or cal.year.max() >= origin):
                    raise ValueError("Local calibration differs from P37")
                rows, residuals = make_rows(fixed.loc[fixed.protocol.eq("p37_recalibration")
                                                       & fixed.k.eq(k) & fixed.district.eq(district)],
                                            tail, cal if k else fit["calibration"], fit)
                history_rows[k].append(rows)
                for model, residual in residuals.items():
                    test = rows.loc[rows.method.eq("reference") & rows.level.eq(LEVELS[0]) & rows.model.eq(model)]
                    errors[k, model][0].extend(residual)
                    errors[k, model][1].extend(test.yield_bu_ac - test.center)
        local_results = {}
        for k, rows in history_rows.items():
            joined = pd.concat(rows, ignore_index=True)
            parts.append(joined)
            diagnosis = {}
            for model in LEARNERS:
                cal, test = errors[k, model]
                diagnosis[model] = {"calibration_n": len(cal), "test_n": len(test),
                                    "calibration_sd": float(np.std(cal, ddof=1)),
                                    "test_sd": float(np.std(test, ddof=1)), "ratio": spread_ratio(cal, test)}
            local_results[str(k)] = {"results": summarize(joined, "district", config), "diagnosis": diagnosis}
        reports[state] = {"p32": summarize(spatial, "district", config), "p37": local_results}
    source_audit = {"all_years": all_years["factors"],
                    "chronological": {str(year): fit["factors"] for year, fit in origins.items()}}
    return reports, parts, source_audit


def frost_check(held, frost):
    counties = held.fips.unique()
    available = frost.loc[frost.fips.isin(counties)]
    if len(available) / len(counties) < 0.8:
        return {"status": "unavailable", "counties": len(counties), "complete_spring_minimum": len(available)}
    from scipy.stats import spearmanr

    join = held.loc[held.level.eq(80)].merge(available, on="fips", validate="many_to_one")
    return {"status": "exploratory", "counties": len(counties), "complete_spring_minimum": len(available),
            "correlations": {name: stat if np.isfinite(stat) else None for name, group in join.groupby("model")
                             for stat in [float(spearmanr(group.spring_min_c, group.yield_bu_ac - group.center).statistic)]}}


def build(root=ROOT):
    data = root / "data/processed"
    config = json.loads((root / "config/climate_yield.json").read_text())

    def read(name):
        return pd.read_csv(data / name, dtype={"fips": str, "district": str, "state": str, "fold": str})

    saved = read("climate_yield_interval_predictions.csv")
    held = saved.loc[saved.protocol.eq("kansas_year") & saved.year.eq(2007)]
    annual, frost, paths = cached_weather(root, set(held.fips))
    mapping = pd.read_csv(root / "data/raw/p27/kansas_reporting_districts.csv", dtype=str)
    kansas = attach_districts(read("climate_yield_features.csv"), mapping).merge(
        annual, on=KEYS, how="left", validate="one_to_one").sort_values(KEYS).reset_index(drop=True)
    targets = {state: read(f"climate_yield_transfer_{state}_features.csv").merge(
        annual, on=KEYS, how="left", validate="one_to_one") for state in ("31", "40")}
    prior = json.loads((data / "climate_yield_recalibration.json").read_text())
    with threadpool_limits(limits=1):
        ks, ks_parts = kansas_results(kansas, saved, config)
        transfer, tr_parts, source_audit = transfer_results(kansas, targets, prior, saved, config)
    rows = pd.concat([*ks_parts, *tr_parts], ignore_index=True)
    if len(rows) != len(saved) * len(METHODS):
        raise ValueError("Some planned method evaluations are missing")
    keys = ["protocol", "state", "fold", "k", "model", "level", *KEYS]
    if rows.duplicated([*keys, "method"]).any():
        raise ValueError("Duplicate method interval")
    reference = rows.loc[rows.method.eq("reference")].set_index(keys).sort_index()
    original = saved.set_index(keys).sort_index()
    pd.testing.assert_series_equal(reference.covered, original.covered)
    status = rows.assign(unbounded=np.isinf(rows.radius), unavailable=~rows.available).groupby("method")
    report = {"label": "illustrative, validate locally", "methods": METHODS, "levels": LEVELS, "k": YEARS,
              "interval_count": len(rows), "counts": rows.groupby("protocol").size().to_dict(),
              "interval_status_by_method": status[["unbounded", "unavailable"]].sum().to_dict("index"),
              "kansas": ks, "transfer": transfer, "source_audit": source_audit,
              "frost_2007": frost_check(held, frost), "power_chunks": len(paths),
              "p33_predictions_sha256": hashlib.sha256((data / "climate_yield_interval_predictions.csv").read_bytes()).hexdigest()}
    # County-year rows retain alternate radii without duplicating P33 outcomes or centers.
    compact = rows[[*keys, "method", "radius", "available", "covered"]]

    def write_rows(path):
        with path.open("wb") as output, gzip.GzipFile(filename="", fileobj=output, mode="wb", mtime=0) as zipped:
            compact.to_csv(zipped, index=False)

    atomic_write(data / "climate_yield_interval_diagnosis_rows.csv.gz", write_rows)
    write_json(data / "climate_yield_interval_diagnosis.json", report)


if __name__ == "__main__":
    build()
