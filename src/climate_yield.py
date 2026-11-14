"""Nested, held-out county and year checks of Kansas climate–yield associations."""
from collections import Counter
import json

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from src.county_yield_data import FEATURES, FEATURE_LABELS
from src.data_pipeline import ROOT, atomic_write
from src.precompute_cache import write_json

SCHEMES = {"leave_one_year_out": "year", "leave_one_county_out": "fips"}
BASELINES = ("county_mean", "linear_trend")
LEARNERS = ("ridge", "random_forest")
MODELS = (*BASELINES, *LEARNERS)
METRICS = ("r2", "rmse_bu_ac", "spearman")


class CountyTrends:
    """Fold-local yield reference. A new county uses the average fitted training-county reference."""

    def __init__(self, train):
        self.year_origin = float(train.year.mean())
        self.by_county = {}
        for county, group in train.groupby("fips"):
            values = group.yield_bu_ac.to_numpy()
            years = group.year.to_numpy(dtype=float) - self.year_origin
            xc = years - years.mean()
            yc = values - values.mean()
            denominator = xc @ xc
            slope = float(xc @ yc / denominator) if denominator else 0.0
            intercept = float(values.mean() - slope * years.mean())
            self.by_county[county] = (float(values.mean()), intercept, slope)
        self.fallback = np.mean(list(self.by_county.values()), axis=0)

    def predict(self, rows):
        values = np.array([self.by_county.get(county, self.fallback) for county in rows.fips])
        mean, intercept, slope = values.T
        return mean, intercept + (rows.year.to_numpy() - self.year_origin) * slope


def grouped_splits(frame, column, n_splits=None):
    groups = frame[column].to_numpy()
    splitter = LeaveOneGroupOut() if n_splits is None else GroupKFold(n_splits=n_splits)
    return splitter.split(frame, groups=groups)


def model_configurations(config):
    return {
        "ridge": [{"alpha": alpha} for alpha in config["ridge_alphas"]],
        "random_forest": [{"min_samples_leaf": leaf} for leaf in config["forest_min_leaf"]],
    }


def make_model(name, params, config):
    if name == "ridge":
        return make_pipeline(StandardScaler(), Ridge(**params))
    if name == "random_forest":
        return RandomForestRegressor(n_estimators=config["forest_trees"], n_jobs=1,
                                     random_state=config["seed"], **params)
    raise ValueError(f"Unknown climate model {name}")


def rmse(actual, predicted):
    return float(np.sqrt(np.mean(np.square(actual - predicted))))


def statistics(actual, predicted):
    rmse_value = rmse(actual, predicted)
    variance = np.var(actual)
    a, b = rankdata(actual), rankdata(predicted)
    a -= a.mean()
    b -= b.mean()
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return (float(1 - rmse_value**2 / variance) if variance else None,
            rmse_value, float(a @ b / norm) if norm else None)


def tune(train, group_column, config):
    """Select by pooled inner held-out RMSE. Refit the trend and transform inside each split."""
    candidates = model_configurations(config)
    loss = {name: np.zeros(len(params)) for name, params in candidates.items()}
    for fit, held in grouped_splits(train, group_column, config["inner_folds"]):
        inner_train, inner_held = train.iloc[fit], train.iloc[held]
        trend = CountyTrends(inner_train)
        y_train = inner_train.yield_bu_ac.to_numpy() - trend.predict(inner_train)[1]
        base = trend.predict(inner_held)[1]
        y_held = inner_held.yield_bu_ac.to_numpy()
        x, x_held = inner_train[list(FEATURES)].to_numpy(), inner_held[list(FEATURES)].to_numpy()
        for name, configs in candidates.items():
            for index, params in enumerate(configs):
                fitted = make_model(name, params, config).fit(x, y_train)
                loss[name][index] += np.square(y_held - base - fitted.predict(x_held)).sum()
    # The candidate grid's declared order breaks an exact tie.
    return {name: candidates[name][int(np.argmin(scores))] for name, scores in loss.items()}


def check_fold(train, test, group_column, config, rng):
    trends = CountyTrends(train)
    mean, trend = trends.predict(test)
    predictions = {"county_mean": mean, "linear_trend": trend}
    y = test.yield_bu_ac.to_numpy()
    residual = train.yield_bu_ac.to_numpy() - trends.predict(train)[1]
    x, x_test = train[list(FEATURES)].to_numpy(), test[list(FEATURES)].to_numpy()
    selected = tune(train, group_column, config)
    attribution = {}
    for name in LEARNERS:
        model = make_model(name, selected[name], config).fit(x, residual)
        predictions[name] = trend + model.predict(x_test)
        features = {}
        for j, field in enumerate(FEATURES):
            permutations = np.tile(x_test, (config["permutation_repeats"], 1))
            permutations[:, j] = np.concatenate([rng.permutation(x_test[:, j]) for _ in range(config["permutation_repeats"])])
            perturb = model.predict(permutations).reshape(config["permutation_repeats"], len(test))
            permuted_sse = np.square(y - trend - perturb).sum(axis=1)
            levels = np.quantile(x[:, j], config["partial_quantiles"])
            replacement = np.tile(x_test, (len(levels), 1))
            replacement[:, j] = np.repeat(levels, len(test))
            partial = model.predict(replacement).reshape(len(levels), len(test)).mean(axis=1)
            features[field] = {"permuted_sse": permuted_sse, "levels": levels, "partial": partial}
        attribution[name] = features
    return predictions, selected, attribution


def bootstrap_metrics(rows, block_column, config):
    """Paired block bootstrap of already held-out predictions, with no model refits."""
    actual = rows.yield_bu_ac.to_numpy()
    prediction = rows[list(MODELS)].to_numpy()
    indices_by_group = list(rows.groupby(block_column, sort=True).indices.values())
    rng = np.random.default_rng(config["seed"])
    values = {model: [[] for _ in METRICS] for model in MODELS}
    contrast = {model: [] for model in LEARNERS}
    trend = MODELS.index("linear_trend")
    for _ in range(config["bootstrap_draws"]):
        ix = np.concatenate([indices_by_group[i] for i in rng.integers(len(indices_by_group), size=len(indices_by_group))])
        metrics = [statistics(actual[ix], prediction[ix, column]) for column in range(len(MODELS))]
        for name, estimates in zip(MODELS, metrics, strict=True):
            for samples, score in zip(values[name], estimates, strict=True):
                if score is not None:
                    samples.append(score)
        for name in LEARNERS:
            contrast[name].append(metrics[MODELS.index(name)][1] - metrics[trend][1])
    quantiles = config["bootstrap_quantiles"]
    performance = {name: {
        key: {"value": point, "bootstrap_95": np.quantile(samples, quantiles).tolist() if samples else None,
              "bootstrap_n": len(samples)}
        for key, point, samples in zip(METRICS, statistics(actual, prediction[:, i]), values[name], strict=True)}
        for i, name in enumerate(MODELS)}
    deltas = {name: {"value": performance[name]["rmse_bu_ac"]["value"] -
                             performance["linear_trend"]["rmse_bu_ac"]["value"],
                     "bootstrap_95": np.quantile(values, quantiles).tolist()}
              for name, values in contrast.items()}
    return performance, deltas


def summarize_attribution(pieces, predictions, config):
    actual = predictions.yield_bu_ac.to_numpy()
    result = {}
    for name in LEARNERS:
        base = rmse(actual, predictions[name].to_numpy())
        features = []
        for field in FEATURES:
            rows = [data[name][field] for _, data in pieces]
            weights = [count for count, _ in pieces]
            permuted = np.sqrt(np.sum([row["permuted_sse"] for row in rows], axis=0) / len(predictions))
            levels = np.average([row["levels"] for row in rows], axis=0, weights=weights)
            partial = np.average([row["partial"] for row in rows], axis=0, weights=weights)
            features.append({"feature": field, "label": FEATURE_LABELS[field],
                             "permutation_rmse_increase": float(permuted.mean() - base),
                             "partial_dependence": [{"training_quantile": q, "value": float(x),
                                                     "predicted_yield_anomaly_bu_ac": float(y)}
                                                    for q, x, y in zip(config["partial_quantiles"], levels, partial,
                                                                       strict=True)]})
        result[name] = sorted(features, key=lambda row: (-row["permutation_rmse_increase"], row["feature"]))
    return result


def analyse(frame, config):
    frame = frame.sort_values(["fips", "year"]).reset_index(drop=True)
    if frame.duplicated(["fips", "year"]).any() or not np.isfinite(frame[["yield_bu_ac", *FEATURES]]).all().all():
        raise ValueError("Expected one finite yield and complete POWER feature row per county-year")
    result, held_out_rows = {}, []
    for scheme, group_column in SCHEMES.items():
        splits = list(grouped_splits(frame, group_column))
        rng = np.random.default_rng(config["seed"])
        predictions = frame[["fips", "year", "practice", "yield_bu_ac"]].copy()
        pieces, choices = [], []
        for fit, held in splits:
            test, train = frame.iloc[held], frame.iloc[fit]
            estimates, selected, interpretation = check_fold(train, test, group_column, config, rng)
            for model, estimate in estimates.items():
                predictions.loc[held, model] = estimate
            choices.append({"held_out": str(test[group_column].iloc[0]), "selected": selected, "n": len(held)})
            pieces.append((len(held), interpretation))
        configs = {name: dict(Counter(json.dumps(row["selected"][name], sort_keys=True) for row in choices))
                   for name in LEARNERS}
        performance, deltas = bootstrap_metrics(predictions, group_column, config)
        result[scheme] = {"n": len(predictions), "outer_folds": len(splits), "bootstrap_block": group_column,
                          "performance": performance, "rmse_delta_vs_trend": deltas,
                          "selected_config_counts": configs, "folds": choices,
                          "interpretation": summarize_attribution(pieces, predictions, config)}
        held_out_rows.append(predictions.assign(scheme=scheme))
    return result, pd.concat(held_out_rows, ignore_index=True)


def build(root=ROOT):
    config = json.loads((root / "config/climate_yield.json").read_text())
    processed = root / "data/processed"
    coverage = json.loads((processed / "climate_yield_coverage.json").read_text())
    frame = pd.read_csv(processed / "climate_yield_features.csv", dtype={"fips": str})
    if any(frame[column].nunique() <= config["inner_folds"] for column in SCHEMES.values()):
        raise ValueError("Too few complete POWER and yield groups. Resume county_yield_data --fetch.")
    with threadpool_limits(limits=1):
        results, predictions = analyse(frame, config)
    atomic_write(processed / "climate_yield_predictions.csv", lambda path: predictions.to_csv(path, index=False))
    dataset = {key: coverage[key] for key in (
        "eligible_yield_counties", "eligible_yield_rows", "retained_counties", "retained_rows",
        "complete_chunk_count", "requested_chunk_count",
    )}
    dataset.update(first_year=int(frame.year.min()), last_year=int(frame.year.max()),
                   practice_counts={key: int(value) for key, value in frame.practice.value_counts().items()})
    payload = {"label": "illustrative, validate locally", "dataset": dataset, "design": config,
               "model_count": len(MODELS), "learned_configuration_count": sum(map(len, model_configurations(config).values())),
               "configurations": model_configurations(config), "schemes": results}
    write_json(processed / "climate_yield_model.json", payload)
    return payload


if __name__ == "__main__":
    build()
