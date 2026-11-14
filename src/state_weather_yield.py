"""P39 cached state coefficients and spatially held-out pooled ridge comparisons."""

from collections import Counter
from itertools import combinations
import json

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from src.climate_yield import CountyTrends, grouped_splits, make_model
from src.climate_yield_validity import attach_districts
from src.county_yield_data import FEATURES, FEATURE_LABELS
from src.cross_state_yield import DISTRICT_BLOCK, STATE_NAMES, validate
from src.data_pipeline import ROOT
from src.precompute_cache import write_json

VARIANTS = ("common_slopes", "interactions")
OUTPUT = "climate_yield_state_associations.json"


def trend_predictions(train, rows):
    """Use the P27 trend and unseen-county fallback within each state."""
    values = np.empty(len(rows), dtype=float)
    for state, positions in rows.groupby("state").indices.items():
        local = train.loc[train.state.eq(state)]
        if local.empty:
            raise ValueError(f"Missing trend training rows for state {state}")
        values[positions] = CountyTrends(local).predict(rows.iloc[positions])[1]
    return values


def design_matrices(train, held):
    """Standardize only the weather features, then construct binary indicators and interactions."""
    scaler = StandardScaler().fit(train[list(FEATURES)])
    matrices = []
    for rows in (train, held):
        weather = scaler.transform(rows[list(FEATURES)])
        indicators = rows.state.to_numpy()[:, None] == np.asarray(tuple(STATE_NAMES))
        common = np.column_stack((weather, indicators))
        products = (indicators[:, :, None] * weather[:, None, :]).reshape(len(rows), -1)
        matrices.append(dict(zip(VARIANTS, (common, np.column_stack((common, products))), strict=True)))
    return matrices


def detrended_state_fit(rows, alpha, config):
    """Match P25's ridge pipeline, returning its scaler and residual-yield slopes."""
    y = rows.yield_bu_ac.to_numpy() - CountyTrends(rows).predict(rows)[1]
    return make_model("ridge", {"alpha": alpha}, config).fit(rows[list(FEATURES)].to_numpy(), y)


def choose_alphas(train, config, *, pooled):
    """Rebuild every transform on the inner fitting districts, then minimize held-out SSE."""
    variants = VARIANTS if pooled else ("state",)
    alphas = config["ridge_alphas"]
    losses = {name: np.zeros(len(alphas)) for name in variants}
    for fit, held in grouped_splits(train, DISTRICT_BLOCK, config["inner_folds"]):
        inner_train, inner_held = train.iloc[fit], train.iloc[held]
        if pooled:
            x, x_held = design_matrices(inner_train, inner_held)
            y_train = inner_train.yield_bu_ac.to_numpy() - trend_predictions(inner_train, inner_train)
            y_held = inner_held.yield_bu_ac.to_numpy() - trend_predictions(inner_train, inner_held)
        else:
            trends = CountyTrends(inner_train)
            y_train = inner_train.yield_bu_ac.to_numpy() - trends.predict(inner_train)[1]
            y_held = inner_held.yield_bu_ac.to_numpy() - trends.predict(inner_held)[1]
            scaler = StandardScaler().fit(inner_train[list(FEATURES)])
            x = {"state": scaler.transform(inner_train[list(FEATURES)])}
            x_held = {"state": scaler.transform(inner_held[list(FEATURES)])}
        for name in variants:
            for index, alpha in enumerate(alphas):
                model = Ridge(alpha=alpha).fit(x[name], y_train)
                losses[name][index] += np.square(y_held - model.predict(x_held[name])).sum()
    return {name: alphas[int(scores.argmin())] for name, scores in losses.items()}


def state_coefficients(rows, config, rng):
    alpha = choose_alphas(rows, config, pooled=False)["state"]
    estimate = detrended_state_fit(rows, alpha, config)["ridge"].coef_
    groups = list(rows.groupby(DISTRICT_BLOCK, sort=True).indices.values())
    indices = rng.integers(len(groups), size=(config["bootstrap_draws"], len(groups)))
    samples = np.empty((len(indices), len(FEATURES)))
    for i, draw in enumerate(indices):
        sample = rows.iloc[np.concatenate([groups[j] for j in draw])]
        samples[i] = detrended_state_fit(sample, alpha, config)["ridge"].coef_
    return alpha, estimate, samples


def interval(samples, config):
    return np.quantile(samples, config["bootstrap_quantiles"]).tolist()


def excludes_zero(bounds):
    return bounds[0] > 0 or bounds[1] < 0


def coefficient_comparison(fitted, config):
    comparisons = {}
    for i, name in enumerate(FEATURES):
        states = {state: {"value": float(estimate[i]), "bootstrap_95": interval(samples[:, i], config)}
                  for state, (_, estimate, samples) in fitted.items()}
        pairs = []
        for left, right in combinations(states, 2):
            a, b = states[left], states[right]
            bounds = interval(fitted[right][2][:, i] - fitted[left][2][:, i], config)
            pairs.append({"left": left, "right": right, "right_minus_left": b["value"] - a["value"],
                          "bootstrap_95": bounds, "difference_excludes_zero": excludes_zero(bounds),
                          "marginal_intervals_overlap": max(a["bootstrap_95"][0], b["bootstrap_95"][0])
                          <= min(a["bootstrap_95"][1], b["bootstrap_95"][1])})
        intervals = [item["bootstrap_95"] for item in states.values()]
        signs = [item["value"] for item in states.values()]
        comparisons[name] = {"states": states, "pairs": pairs, "all_intervals_overlap":
                             max(lo for lo, _ in intervals) <= min(hi for _, hi in intervals),
                             "opposite_point_signs": min(signs) < 0 < max(signs)}
    return comparisons


def pooled_fold(train, test, config):
    if (not set(train[DISTRICT_BLOCK]).isdisjoint(test[DISTRICT_BLOCK])
            or not set(train.fips).isdisjoint(test.fips)):
        raise ValueError("Held-out district or county appears in the fitting rows")
    selected = choose_alphas(train, config, pooled=True)
    x, x_test = design_matrices(train, test)
    y = train.yield_bu_ac.to_numpy() - trend_predictions(train, train)
    baseline = trend_predictions(train, test)
    predictions = {name: baseline + Ridge(alpha=alpha).fit(x[name], y).predict(x_test[name])
                   for name, alpha in selected.items()}
    return predictions, selected


def pooled_holdout(rows, config):
    held_rows, folds = [], []
    for fit, held in grouped_splits(rows, DISTRICT_BLOCK):
        train, test = rows.iloc[fit], rows.iloc[held]
        predictions, selected = pooled_fold(train, test, config)
        errors = np.column_stack([(test.yield_bu_ac.to_numpy() - predictions[m]) ** 2 for m in VARIANTS])
        state = test.state.iloc[0]
        district = test[DISTRICT_BLOCK].iloc[0]
        scores = np.sqrt(errors.mean(axis=0))
        folds.append({"state": state, "district_block": district, "district_name": test.district_name.iloc[0],
                      "n": len(held), "counties": int(test.fips.nunique()), "selected_alphas": selected,
                      "rmse_bu_ac": dict(zip(VARIANTS, scores.tolist(), strict=True)),
                      "rmse_difference_bu_ac": float(scores[1] - scores[0])})
        held_rows.append(test[["state", DISTRICT_BLOCK, "fips", "year"]].assign(
            **dict(zip(VARIANTS, errors.T, strict=True))))
    return pd.concat(held_rows, ignore_index=True), folds


def rmse_summary(rows, config):
    """Pair the models within every draw, resampling districts within state."""
    totals = rows.groupby(["state", DISTRICT_BLOCK])[list(VARIANTS)].sum()
    counts = rows.groupby(["state", DISTRICT_BLOCK]).size()
    estimates = np.sqrt(totals.sum().to_numpy() / len(rows))
    draws = config["bootstrap_draws"]
    rng = np.random.default_rng(config["seed"])
    sum_squared = np.zeros((draws, len(VARIANTS)))
    n = np.zeros(draws, dtype=int)
    for state, state_totals in totals.groupby(level="state", sort=True):
        size = len(state_totals)
        index = rng.integers(size, size=(draws, size))
        sum_squared += state_totals.to_numpy()[index].sum(axis=1)
        n += counts.loc[state].to_numpy()[index].sum(axis=1)
    pooled = np.sqrt(sum_squared / n[:, None])
    difference = pooled[:, 1] - pooled[:, 0]
    bounds = interval(difference, config)
    return {"n": len(rows), "districts": len(totals),
            "rmse_bu_ac": {name: {"value": float(estimates[i]), "bootstrap_95": interval(pooled[:, i], config)}
                          for i, name in enumerate(VARIANTS)},
            "rmse_difference_bu_ac": {"value": float(estimates[1] - estimates[0]), "bootstrap_95": bounds},
            "clear_improvement": bounds[1] < 0}


def assess(frames, config):
    data = {state: validate(frames[state], state) for state in STATE_NAMES}
    rngs = np.random.SeedSequence(config["seed"]).spawn(len(data))
    fitted = {state: state_coefficients(frame, config, np.random.default_rng(seed))
              for (state, frame), seed in zip(data.items(), rngs, strict=True)}
    errors, folds = pooled_holdout(pd.concat(data.values(), ignore_index=True), config)
    outer_fits = len(data) + len(VARIANTS) * len(folds)
    return {
        "label": "illustrative, validate locally",
        "feature_labels": FEATURE_LABELS, "states": STATE_NAMES,
        "design": {"ridge_alphas": config["ridge_alphas"], "inner_folds": config["inner_folds"],
                   "bootstrap_draws": config["bootstrap_draws"], "bootstrap_quantiles": config["bootstrap_quantiles"],
                   "seed": config["seed"]},
        "counts": {"coefficients": len(FEATURES) * len(data),
                   "coefficient_differences": len(FEATURES) * len(list(combinations(data, 2))),
                   "model_specifications": len(data) + len(VARIANTS),
                   "specification_alpha_configurations": (len(data) + len(VARIANTS)) * len(config["ridge_alphas"]),
                   "inner_ridge_fits": outer_fits * len(config["ridge_alphas"]) * config["inner_folds"],
                   "final_ridge_fits": outer_fits,
                   "coefficient_bootstrap_refits": len(data) * config["bootstrap_draws"]},
        "cohorts": {state: {"n": len(frame), "counties": int(frame.fips.nunique()),
                            "districts": int(frame[DISTRICT_BLOCK].nunique()),
                            "first_year": int(frame.year.min()), "last_year": int(frame.year.max()),
                            "practice_counts": frame.practice.value_counts().to_dict(),
                            "alpha": fitted[state][0]}
                    for state, frame in data.items()},
        "coefficients": coefficient_comparison(fitted, config),
        "held_out": {"pooled": rmse_summary(errors, config),
                     "by_state": {state: rmse_summary(group, config) for state, group in errors.groupby("state")},
                     "alpha_counts": {name: dict(Counter(str(fold["selected_alphas"][name]) for fold in folds))
                                      for name in VARIANTS},
                     "folds": folds},
    }


def build(root=ROOT):
    processed = root / "data/processed"
    config = json.loads((root / "config/climate_yield.json").read_text())
    kansas = pd.read_csv(processed / "climate_yield_features.csv", dtype={"fips": str})
    mapping = pd.read_csv(root / "data/raw/p27/kansas_reporting_districts.csv", dtype=str)
    frames = {"20": attach_districts(kansas, mapping)}
    for state in ("31", "40"):
        frames[state] = pd.read_csv(processed / f"climate_yield_transfer_{state}_features.csv",
                                    dtype={"fips": str, "district": str})
    with threadpool_limits(limits=1):
        report = assess(frames, config)
    write_json(processed / OUTPUT, report)


if __name__ == "__main__":
    build()
