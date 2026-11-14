"""Diagnose the saved P32 Kansas-to-Oklahoma predictions without refitting."""

import hashlib
import json

import numpy as np
import pandas as pd

from src.climate_yield import LEARNERS
from src.county_yield_data import FEATURES, FEATURE_LABELS
from src.data_pipeline import ROOT
from src.precompute_cache import write_json

KEYS = ["fips", "year"]
MODELS = (*LEARNERS, "own_linear_trend", "own_county_mean")
BASELINES = MODELS[-2:]
RANGES = {"full": ("min", "max"), "central": ("p05", "p95")}
BINS = ("Below", "Inside", "Above")
PRACTICES = ("non_irrigated", "all_practices")


def match_rows(features, predictions):
    target = features.set_index(KEYS)
    frozen = predictions.set_index(KEYS)
    if (not target.index.is_unique or not frozen.index.is_unique
            or set(target.index) != set(frozen.index)):
        raise ValueError("Oklahoma features and transfer predictions must share unique county-years")
    frozen = frozen.reindex(target.index)
    for column in ("yield_bu_ac", "practice", "district"):
        if not target[column].equals(frozen[column]):
            raise ValueError(f"Oklahoma {column} differs from saved P32 predictions")
    return target.join(frozen[list(MODELS)]).reset_index().sort_values(KEYS).reset_index(drop=True)


def distribution(rows):
    values = rows[list(FEATURES)].quantile([0, .05, .5, .95, 1], interpolation="linear")
    return values.set_axis(["min", "p05", "median", "p95", "max"]).to_dict()


def range_bins(rows, reference, band):
    low, high = RANGES[band]
    table = {}
    for name in FEATURES:
        x = rows[name]
        a, b = reference[name][low], reference[name][high]
        table[name] = np.select([x.lt(a), x.gt(b)], ["Below", "Above"], default="Inside")
    return pd.DataFrame(table, index=rows.index)


def range_report(bins):
    n = len(bins)
    outside = bins.ne("Inside")
    return {"n": n, "outside_any_n": int(outside.any(axis=1).sum()),
            "outside_any_share": float(outside.any(axis=1).mean()),
            "features": {name: {"below_n": int(bins[name].eq("Below").sum()),
                                "above_n": int(bins[name].eq("Above").sum()),
                                "outside_n": int(outside[name].sum()),
                                "outside_share": float(outside[name].mean())}
                         for name in FEATURES}}


def performance(rows, config):
    n = len(rows)
    groups = rows.groupby("district", sort=True)
    blocks = groups.ngroups
    error = rows[list(MODELS)].subtract(rows.yield_bu_ac, axis=0)
    squared = error.pow(2)
    metrics = {name: float(np.sqrt(squared[name].mean())) if n else None for name in MODELS}
    draws = None
    if blocks >= 2:
        # Resample the paired district totals, preserving each district's actual row count.
        totals = squared.groupby(rows.district, sort=True).sum().to_numpy()
        counts = groups.size().to_numpy()
        rng = np.random.default_rng(config["seed"])
        ix = rng.integers(blocks, size=(config["bootstrap_draws"], blocks))
        draws = np.sqrt(totals[ix].sum(axis=1) / counts[ix].sum(axis=1, keepdims=True))

    def difference(model, baseline):
        point = metrics[model] - metrics[baseline] if n else None
        ci = (np.quantile(draws[:, MODELS.index(model)] - draws[:, MODELS.index(baseline)],
                          config["bootstrap_quantiles"]).tolist() if draws is not None else None)
        return {"value": point, "bootstrap_95": ci}

    return {"n": n, "counties": int(rows.fips.nunique()), "districts": blocks, "rmse": metrics,
            "paired_rmse_delta": {name: {base: difference(name, base) for base in BASELINES}
                                  for name in LEARNERS}}


def error_groups(error, group, order=None):
    squared = error.pow(2)
    total = squared.sum()
    labels = sorted(group.unique()) if order is None else order
    results = []
    for key in labels:
        test = group.eq(key)
        n = int(test.sum())
        sse = float(squared[test].sum())
        results.append({"group": str(key), "n": n, "row_share": n / len(error),
                        "bias": float(error[test].mean()) if n else None,
                        "rmse": float(np.sqrt(sse / n)) if n else None,
                        "sse": sse, "sse_share": float(sse / total) if total else None})
    return results


def concentration(groups, count):
    # The groups are already ordered by year or district code. Stable sorting breaks SSE ties.
    ranked = sorted(groups, key=lambda row: -row["sse"])[:count]
    error_share = sum(row["sse_share"] for row in ranked) if ranked and ranked[0]["sse_share"] is not None else None
    return {"groups": [row["group"] for row in ranked],
            "row_share": sum(row["row_share"] for row in ranked), "sse_share": error_share,
            "above_half": error_share > .5 if error_share is not None else None}


def practice_report(rows):
    counts = rows.practice.value_counts().to_dict()
    return {key: {"n": counts.get(key, 0), "share": counts.get(key, 0) / len(rows)} for key in PRACTICES}


def assess(kansas, target, config):
    for frame, columns in ((kansas, FEATURES), (target, (*FEATURES, *MODELS, "yield_bu_ac"))):
        if frame.empty or not np.isfinite(frame[list(columns)]).all().all():
            raise ValueError("Expected nonempty finite cached inputs")
        if not set(frame.practice).issubset(PRACTICES):
            raise ValueError("Unexpected NASS practice label")
    bounds = distribution(kansas)
    bins = {band: range_bins(target, bounds, band) for band in RANGES}
    central = bins["central"]
    inside = central.eq("Inside").all(axis=1)
    analyses = {"full": target, "inside": target.loc[inside], "outside": target.loc[~inside]}
    errors = {}
    for model in LEARNERS:
        residual = target[model] - target.yield_bu_ac
        by_year = error_groups(residual, target.year)
        by_district = error_groups(residual, target.district)
        errors[model] = {"year": by_year, "district": by_district,
                         "feature": {name: error_groups(residual, central[name], BINS) for name in FEATURES},
                         "top_years": concentration(by_year, 3), "top_districts": concentration(by_district, 2)}
    return {"label": "illustrative, validate locally", "features": FEATURE_LABELS,
            "distributions": {"kansas": bounds, "oklahoma": distribution(target)},
            "outside_ranges": {band: range_report(values) for band, values in bins.items()},
            "kansas_central": range_report(range_bins(kansas, bounds, "central")),
            "practice": {"kansas": practice_report(kansas), "oklahoma": practice_report(target)},
            "performance": {key: performance(frame, config) for key, frame in analyses.items()},
            "district_names": dict(target[["district", "district_name"]].drop_duplicates().itertuples(index=False, name=None)),
            "errors": errors, "bootstrap_seed": config["seed"], "bootstrap_draws": config["bootstrap_draws"]}


def build(root=ROOT):
    data = root / "data/processed"
    config_path = root / "config/climate_yield.json"
    fields = {"fips": str, "district": str}
    files = {"kansas": data / "climate_yield_features.csv",
             "oklahoma": data / "climate_yield_transfer_40_features.csv",
             "predictions": data / "climate_yield_transfer_predictions.csv"}
    kansas, oklahoma, predictions = (pd.read_csv(path, dtype=fields) for path in files.values())
    matched = match_rows(oklahoma, predictions.loc[predictions.case.eq("20_to_40")])
    report = assess(kansas, matched, json.loads(config_path.read_text()))
    report["input_sha256"] = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                              for path in (*files.values(), config_path)}
    write_json(data / "climate_yield_transfer_diagnosis.json", report)


if __name__ == "__main__":
    build()
