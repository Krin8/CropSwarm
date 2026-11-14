import json

import numpy as np
import pandas as pd
import pytest
from threadpoolctl import threadpool_limits

from src import interval_diagnosis as study
from src.yield_intervals import interval_rows, conformal_radius


@pytest.fixture
def history():
    rng = np.random.default_rng(42)
    rows = []
    for district in range(8):
        for year in range(1995, 2002):
            weather = rng.uniform(size=len(study.FEATURES))
            rows.append({"fips": f"200{district:02}", "year": year, "district": str(district),
                         "yield_bu_ac": 20 + district + weather[1] * 5,
                         **dict(zip(study.FEATURES, weather, strict=True)),
                         **dict(zip(study.ANNUAL, rng.uniform(size=3), strict=True))})
    return pd.DataFrame(rows)


@pytest.fixture
def config():
    return {**json.loads((study.ROOT / "config/climate_yield.json").read_text()),
            "forest_trees": 3, "bootstrap_draws": 20}


def test_weighted_order_statistic_accounts_for_unseen_score():
    scores = np.arange(1., 10.)
    assert study.weighted_radius(scores, np.ones(9), 80) == conformal_radius(scores, 80)
    assert study.weighted_radius(scores, np.ones(9), 90) == conformal_radius(scores, 90)
    assert np.isinf(study.weighted_radius(scores, np.full(9, .1), 90))
    assert study.weighted_radius(scores, np.array([50.] + [1.] * 8), 90) == 5


def test_inflation_and_residual_spread_use_signed_errors():
    calibration = pd.DataFrame({"district": ["a"] * 4 + ["b"] * 4,
                                "year": [2000, 2000, 2001, 2001] * 2})
    factor, districts = study.inflation_factor(calibration, np.array([-1, 1, -3, 3, -1, 1, -2, 2]))
    assert (factor, districts) == (2.5, 2)
    assert study.spread_ratio([0, 0], [3, 3]) is None


def test_methods_are_reproducible_and_test_labels_cannot_change_radii(history, config, monkeypatch):
    proper_n = []
    fit_regimes = study.fit_regimes

    def audit_regimes(rows):
        proper_n.append(set(rows.district))
        return fit_regimes(rows)

    monkeypatch.setattr(study, "fit_regimes", audit_regimes)
    train, test = history.loc[history.district.ne("7")], history.loc[history.district.eq("7")]
    with threadpool_limits(limits=1):
        learned = study.source_fit(train, "district", config, held=test)
        assert proper_n == [set(learned["audit"]["proper_groups"])]
        assert "7" not in proper_n[0] | set(learned["audit"]["calibration_groups"])
        cal = learned["calibration"]
        projected = study.predict(test, learned["trends"], learned["models"])
        estimates = study.predict(cal, learned["trends"], learned["models"])
        scores = {name: abs(cal.yield_bu_ac.to_numpy() - estimates[name]) for name in study.LEARNERS}
        original = interval_rows(test, projected, scores)
        first, _ = study.make_rows(original, test, cal, learned)
        another, _ = study.make_rows(original, test, cal, learned)
        pd.testing.assert_frame_equal(first, another)
        assert study.summarize(first, "year", config) == study.summarize(another, "year", config)
        shifted, _ = study.make_rows(original.assign(yield_bu_ac=10000), test.assign(yield_bu_ac=10000), cal, learned)
        pd.testing.assert_series_equal(first.radius, shifted.radius)
        assert first.groupby("method").size().eq(len(original)).all()
        np.testing.assert_array_equal(first.loc[first.method.eq("reference"), "radius"],
                                      first.loc[first.method.eq("leave_year_out"), "radius"])
        with pytest.raises(ValueError, match="overlaps"):
            study.source_fit(history, "district", config, held=test)


def test_missing_weather_and_empty_regime_are_distinct():
    frame = pd.DataFrame({"fips": ["20001"]})
    result = study.frost_check(frame, pd.DataFrame({"fips": [], "spring_min_c": []}))
    assert result == {"status": "unavailable", "counties": 1, "complete_spring_minimum": 0}
    rows = pd.DataFrame({"method": ["mondrian"] * 3, "model": ["ridge"] * 3, "level": [80] * 3,
                         "available": [False, True, True], "radius": [np.nan, 1., np.inf],
                         "covered": [False, False, True], "district": ["01", "02", "02"]})
    row, = study.summarize(rows, "district", {"seed": 42})
    assert (row["coverage"], row["unavailable"], row["unbounded"], row["mean_width"]) == (.5, 1, 1, None)
