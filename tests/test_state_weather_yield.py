"""Check the P39 fold boundary, paired intervals and reproducible ridge fits."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.climate_yield import tune
from src.county_yield_data import FEATURES
from src.cross_state_yield import DISTRICT_BLOCK, STATE_NAMES, validate
from src.state_weather_yield import (VARIANTS, assess, choose_alphas, design_matrices,
                                     pooled_fold, rmse_summary)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def study():
    rng = np.random.default_rng(10)
    frames = {}
    for i, state in enumerate(STATE_NAMES):
        rows = []
        for district in range(4):
            for county in range(2):
                for year in range(2000, 2007):
                    weather = rng.normal(size=len(FEATURES)) + i
                    rows.append({"fips": f"{state}{2 * district + county + 1:03d}", "year": year,
                                 "yield_bu_ac": 30 + district + .4 * (year - 2000) + (i - 1) * weather[0],
                                 "district": f"{district}0", "district_name": f"District {district}",
                                 "practice": "non_irrigated", **dict(zip(FEATURES, weather, strict=True))})
        frames[state] = pd.DataFrame(rows)
    config = {"seed": 42, "ridge_alphas": [.1, 1., 10.], "inner_folds": 3,
              "bootstrap_draws": 20, "bootstrap_quantiles": [.025, .975],
              "forest_trees": 2, "forest_min_leaf": [5]}
    return frames, config


def test_uses_unchanged_state_ridge_selection(study):
    frames, config = study
    for state, frame in frames.items():
        rows = validate(frame, state)
        expected = tune(rows, "district", config)["ridge"]["alpha"]
        assert choose_alphas(rows, config, pooled=False)["state"] == expected


def test_held_out_yields_cannot_change_fit_or_alpha_and_scaling_uses_training(study):
    frames, config = study
    rows = pd.concat([validate(frame, state) for state, frame in frames.items()], ignore_index=True)
    group = rows[DISTRICT_BLOCK].eq("20:00")
    train, test = rows.loc[~group], rows.loc[group]
    predicted, selected = pooled_fold(train, test, config)
    altered = test.assign(yield_bu_ac=test.yield_bu_ac + 100_000)
    other_predictions, other_selected = pooled_fold(train, altered, config)
    assert selected == other_selected
    for name in VARIANTS:
        np.testing.assert_array_equal(predicted[name], other_predictions[name])

    future = test.assign(**{name: 1_000 for name in FEATURES})
    x, x_future = design_matrices(train, future)
    np.testing.assert_allclose(x["common_slopes"][:, :len(FEATURES)].mean(axis=0), 0, atol=1e-12)
    np.testing.assert_allclose(x["common_slopes"][:, :len(FEATURES)].std(axis=0), 1)
    expected = (future[list(FEATURES)] - train[list(FEATURES)].mean()) / train[list(FEATURES)].std(ddof=0)
    np.testing.assert_allclose(x_future["common_slopes"][:, :len(FEATURES)], expected)
    products = x_future["interactions"][:, -len(STATE_NAMES) * len(FEATURES):]
    np.testing.assert_allclose(products[:, :len(FEATURES)], expected)
    assert not products[:, len(FEATURES):].any()
    with pytest.raises(ValueError, match="Held-out district or county"):
        pooled_fold(rows, test, config)


def test_complete_study_is_reproducible_and_spatial(study):
    frames, config = study
    result = assess(frames, config)
    shuffled = {state: frame.sample(frac=1, random_state=7) for state, frame in frames.items()}
    assert assess(shuffled, config) == result
    assert len(result["coefficients"]) == 5
    assert result["counts"]["coefficients"] == result["counts"]["coefficient_differences"] == 15
    folds = result["held_out"]["folds"]
    assert len(folds) == 12 == len({f["district_block"] for f in folds})
    assert sum(f["n"] for f in folds) == result["held_out"]["pooled"]["n"] == 168
    assert all(f["counties"] == 2 for f in folds)
    first = result["coefficients"][FEATURES[0]]
    assert first["opposite_point_signs"]
    assert not first["all_intervals_overlap"]


def test_paired_rmse_difference(study):
    _, config = study
    rows = pd.DataFrame({"state": ["20", "20", "20", "31", "31", "31"],
                         DISTRICT_BLOCK: ["20:00", "20:10", "20:10", "31:00", "31:10", "31:10"],
                         "common_slopes": [4., 4., 4., 4., 4., 4.],
                         "interactions": [1., 1., 1., 1., 1., 1.]})
    summary = rmse_summary(rows, config)
    assert summary["rmse_difference_bu_ac"] == {"value": -1.0, "bootstrap_95": [-1.0, -1.0]}
    assert summary["clear_improvement"]
