"""Exercise P41 score interventions, held-out backgrounds and direction comparisons."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.climate_yield import CountyTrends, LEARNERS, make_model
from src.county_yield_data import FEATURES
from src.scoring_response_check import (compare, fold_curves, partial_dependence, scoring_curves,
                                        summarize_state, verify_windows)


def test_scoring_uses_exact_hot_day_screen_and_post_bucket_deficit():
    crop = {"season_length_days": 260, "water_need_mm": 500, "heat_tolerance_c": 30,
            "min_rain_mm": 100, "max_rain_mm": 600, "min_temp_c": 8, "max_temp_c": 24,
            "cover_score": .8, "relative_income_index": .5}
    model = SimpleNamespace(crops={"winter_wheat": crop}, ids=["winter_wheat"], days={(0, 0): ("cool", 10, 260)},
                            season_labels=[["cool"]], farm={"irrigation": {"supply_fraction": 0}},
                            storage=40, slope=2, policy={"max_hot_day_fraction": .1, "same_family_risk_share": .5,
                                                         "bare_slot_risk_share": .5},
                            additions=np.zeros((1, 1, 5)), planting_windows=np.ones((1, 1), dtype=bool),
                            suitable=np.ones((1, 1), dtype=bool), credits=np.array([0]), demand=np.array([60]),
                            bare=np.array([False]), family=np.array([0]), nitrogen_bounds=(-60, 30), erosion_max=20)
    medians = {"water_deficit_mm": 200, "heat_days": 26, "rainfall_mm": 300, "mean_temp_c": 15}
    grid = {"water_deficit_mm": (0, 250, 500), "heat_days": (25, 26, 27, 30)}
    results = scoring_curves(model, medians, grid)
    assert results["water_deficit_mm"] == {"water": [1., .5, 0.], "climate_fit": [1., 1., 1.]}
    assert results["heat_days"] == {"water": [.6] * 4, "climate_fit": [1., 1., 0., 0.]}
    assert not model.additions.any()


def test_uses_held_out_background_and_centers_at_first_grid_point():
    class JointPredictor:
        def predict(self, values):
            return values[:, 0] * values[:, 1]

    background = np.array([[1., 2.], [9., 4.]])
    np.testing.assert_allclose(partial_dependence(JointPredictor(), background, 0, [10, 20, 30]),
                               [0, 30, 60])
    np.testing.assert_array_equal(background, [[1., 2.], [9., 4.]])


def test_frozen_fold_matches_saved_predictions_and_rejects_leakage():
    rng = np.random.default_rng(42)
    rows = pd.DataFrame(rng.normal(size=(25, len(FEATURES))), columns=FEATURES)
    rows["fips"] = np.repeat(["20001", "20002", "20003", "20004", "20005"], 5)
    rows["district"] = np.repeat(["10", "20"], [20, 5])
    rows["year"] = np.tile(np.arange(2000, 2005), 5)
    rows["yield_bu_ac"] = rng.normal(55, 10, len(rows))
    train, held = rows.iloc[:20], rows.iloc[20:]
    setting = {"ridge": {"alpha": 1.}, "random_forest": {"min_samples_leaf": 2}}
    config = {"seed": 42, "forest_trees": 4}
    trend = CountyTrends(train)
    residual = train.yield_bu_ac.to_numpy() - trend.predict(train)[1]
    saved = {key: make_model(key, setting[key], config).fit(train[list(FEATURES)].to_numpy(), residual)
             .predict(held[list(FEATURES)].to_numpy()) + trend.predict(held)[1] for key in LEARNERS}
    outputs, errors = fold_curves(train, held, saved, setting, config)
    changed = fold_curves(train, held.assign(yield_bu_ac=-1000), saved, setting, config)[0]
    for learner in LEARNERS:
        assert errors[learner] == 0
        for feature in outputs[learner]:
            np.testing.assert_array_equal(outputs[learner][feature], changed[learner][feature])
    with pytest.raises(ValueError, match="held-out district or county"):
        fold_curves(rows, held, saved, setting, config)
    with pytest.raises(ValueError, match="does not match"):
        fold_curves(train, held, {**saved, "ridge": saved["ridge"] + 1}, setting, config)


def test_ranges_separate_sign_pairs_and_marginal_support():
    grid = [0, 5, 10, 15, 20, 25]
    point = np.array([0, -1, 0, 0, -1, -2])
    result = compare(grid, [1., .9, .8, .7, .7, .7], point, np.tile(point, (4, 1)),
                     [False, True, True, True, True, True], [.025, .975])
    assert result["score_shape"] == "non-increasing"
    assert result["data_shape"] == "non-monotone"
    assert result["supported_opposite_direction"] == 1
    assert result["supported_same_direction"] == 0
    assert result["spans"] == [
        {"start": 0, "end": 5, "signs": [-1, -1], "supported": False},
        {"start": 5, "end": 10, "signs": [-1, 1], "supported": True},
        {"start": 10, "end": 15, "signs": [-1, 0], "supported": True},
        {"start": 15, "end": 25, "signs": [0, -1], "supported": True},
    ]
    flat = compare(grid, np.ones(len(grid)), point, np.tile(point, (4, 1)),
                   np.ones(len(grid), dtype=bool), [.025, .975])
    assert flat["rho"] == {"value": None, "bootstrap_95": None, "bootstrap_n": 0}


def test_state_summary_weights_folds_by_rows_and_is_seeded():
    feature = "heat_days"
    grid = {feature: [0, 5, 10]}
    scoring = {feature: {"climate_fit": [1., 1., 0.]}}
    folds = [{key: {feature: x} for key in LEARNERS} for x in [[0, 5, 1], [0, -9, -3]]]
    audit = [{"n": 1}, {"n": 3}]
    rows = pd.DataFrame({"heat_days": [0, 4, 7, 10], "year": [2000, 2001, 2000, 2001],
                         "fips": ["20001", "20002", "20002", "20002"], "practice": ["non_irrigated"] * 4})
    config = {"seed": 42, "bootstrap_draws": 10, "bootstrap_quantiles": [.025, .975]}
    result = summarize_state(rows, folds, audit, scoring, config, grid)
    assert result == summarize_state(rows, folds, audit, scoring, config, grid)
    assert result["weather"][feature]["learners"]["ridge"]["partial_dependence_bu_ac"] == [0., -5.5, -2.]


def test_cached_dates_must_match_scoring_window():
    rows = pd.DataFrame({"year": [1992], "window_start": ["1991-10-01"], "window_end": ["1992-06-16"]})
    verify_windows(rows, 10, 260)
    with pytest.raises(ValueError, match="do not match"):
        verify_windows(rows, 10, 261)
