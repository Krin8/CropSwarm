import json

import numpy as np
import pandas as pd
import pytest

from src import yield_intervals as study
from src.county_yield_data import FEATURES

CONFIG = {**json.loads((study.ROOT / "config/climate_yield.json").read_text()),
          "forest_trees": 3, "bootstrap_draws": 30}


@pytest.fixture
def county_years():
    rng = np.random.default_rng(CONFIG["seed"])
    rows = []
    for district in range(7):
        for year in range(1990, 1997):
            x = rng.uniform(size=len(FEATURES))
            rows.append({"district": str(district), "fips": f"200{district:02}", "year": year,
                         "yield_bu_ac": 25 + 2 * district + year - 1990 + x[0] * 6,
                         **dict(zip(FEATURES, x, strict=True))})
    return pd.DataFrame(rows)


def test_finite_sample_rank_nested_and_unbounded():
    assert study.conformal_radius(np.arange(1, 10), 80) == 8
    assert study.conformal_radius(np.arange(1, 10)[::-1], 90) == 9
    assert study.conformal_radius([3, 2, 2, 1], 80) == 3
    assert np.isinf(study.conformal_radius([3, 2, 2, 1], 90))
    with pytest.raises(ValueError, match="finite nonnegative"):
        study.conformal_radius([2, np.nan], 90)


@pytest.mark.parametrize("group", ["district", "year"])
def test_fitting_and_calibration_exclude_outer_holdout_and_each_other(county_years, monkeypatch, group):
    train, test = county_years.iloc[:-1], county_years.iloc[-1:]
    train = train[~train[group].isin(test[group])]
    tune, trend_init, make_model = study.tune, study.CountyTrends.__init__, study.make_model
    seen = []

    def record_tuning(rows, name, config):
        seen.append(("tuning", set(rows[group])))
        return tune(rows, name, config)

    def record_trends(self, rows):
        seen.append(("trends", set(rows[group])))
        trend_init(self, rows)

    def record_fit(name, setting, config):
        model = make_model(name, setting, config)
        fit = model.fit

        def with_audit(features, y):
            groups = train.set_index(FEATURES[0]).loc[features[:, 0], group]
            seen.append(("fit", set(groups)))
            return fit(features, y)

        model.fit = with_audit
        return model

    monkeypatch.setattr(study, "tune", record_tuning)
    monkeypatch.setattr(study.CountyTrends, "__init__", record_trends)
    monkeypatch.setattr(study, "make_model", record_fit)
    trends, fits, errors, audit = study.fit_split(train, group, CONFIG, held=test)
    assert {kind for kind, _ in seen} == {"tuning", "trends", "fit"}
    assert all(groups <= set(audit["proper_groups"]) for _, groups in seen)
    assert set(audit["proper_groups"]).isdisjoint(audit["calibration_groups"])
    assert set(test[group]).isdisjoint(audit["calibration_groups"])
    shifted = test.assign(yield_bu_ac=test.yield_bu_ac + 1000)
    second_trend, second_fits, other_errors, _ = study.fit_split(train, group, CONFIG, held=shifted)
    for name, a in study.predict(test, trends, fits).items():
        np.testing.assert_array_equal(a, study.predict(shifted, second_trend, second_fits)[name])
    for name in errors:
        np.testing.assert_array_equal(errors[name], other_errors[name])
    with pytest.raises(ValueError, match="overlaps"):
        study.fit_split(county_years, group, CONFIG, held=test)


def test_frozen_calibration_scores_and_bootstrap_reproduce(county_years):
    trends, models, errors, audit = study.fit_split(county_years, "district", CONFIG)
    other_trend, other_models, other_errors, other_audit = study.fit_split(
        county_years.sample(frac=1, random_state=42), "district", CONFIG)
    assert audit == other_audit
    test = county_years.iloc[:24].copy()
    first = study.interval_rows(test, study.predict(test, trends, models), errors)
    second = study.interval_rows(test, study.predict(test, other_trend, other_models), other_errors)
    pd.testing.assert_frame_equal(first, second)
    assert study.summarize(first, "district", CONFIG) == study.summarize(second, "district", CONFIG)
    for _, rows in first.groupby("model"):
        assert (rows.loc[rows.level.eq(80), "radius"].to_numpy()
                <= rows.loc[rows.level.eq(90), "radius"].to_numpy()).all()
    single = first[first.district.eq("0")]
    assert study.coverage_interval(single, "district", CONFIG) is None


def test_saved_report_preserves_p37_test_rows_and_centers():
    data = study.ROOT / "data/processed"
    report = json.loads((data / "climate_yield_intervals.json").read_text())
    csv = pd.read_csv(data / "climate_yield_interval_predictions.csv",
                      dtype={"fips": str, "state": str, "district": str})
    local = csv.loc[csv.protocol.eq("p37_recalibration")]
    source = pd.read_csv(data / "climate_yield_recalibration_predictions.csv",
                         dtype={"fips": str, "state": str, "district": str})
    keys = ["state", "district", "fips", "year", "k"]
    row_keys = local[keys].drop_duplicates().sort_values(keys).reset_index(drop=True)
    pd.testing.assert_frame_equal(row_keys, source[keys].sort_values(keys).reset_index(drop=True))
    comparison = ["state", "district", "fips", "year", "model", "level"]
    reference = local.loc[local.k.eq(0)].set_index(comparison).center.sort_index()
    for _, rows in local.groupby("k"):
        pd.testing.assert_series_equal(reference, rows.set_index(comparison).center.sort_index())
    assert len(csv) == report["interval_evaluations"]
    assert not csv.duplicated(["protocol", *keys, "model", "level"]).any()
