import json

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler

import src.climate_yield as model
from src.climate_yield_validity import attach_districts, evaluate_cohort
from src.county_yield_data import FEATURES
from src.data_pipeline import ROOT

CONFIG = {**json.loads((ROOT / "config/climate_yield.json").read_text()),
          "bootstrap_draws": 20, "forest_trees": 4, "permutation_repeats": 2}


@pytest.fixture
def district_years():
    rng = np.random.default_rng(42)
    rows, mapping = [], []
    for i in range(8):
        county, district = f"20{i:03}", str(i // 2)
        mapping.append({"fips": county, "district": district, "district_name": f"District {district}"})
        for year in range(2000, 2008):
            data = rng.uniform(size=len(FEATURES))
            data[0] = len(rows)  # unique row identifier for scaler audit
            rows.append({"fips": county, "year": year,
                         "practice": "non_irrigated" if year < 2004 else "all_practices",
                         "yield_bu_ac": 20 + i + (year - 2000) + 5 * data[1],
                         **dict(zip(FEATURES, data, strict=True))})
    return pd.DataFrame(rows), pd.DataFrame(mapping)


def test_district_assignment_unique_and_complete(district_years):
    rows, mapping = district_years
    assert len(attach_districts(rows, mapping)) == len(rows)
    with pytest.raises(pd.errors.MergeError):
        attach_districts(rows, pd.concat([mapping, mapping.iloc[:1]]))
    with pytest.raises(ValueError, match="Missing USDA"):
        attach_districts(rows, mapping.iloc[:-1])


@pytest.mark.parametrize("column", ["year", "fips", "district"])
def test_no_outer_holdout_reaches_any_training_fit(district_years, column, monkeypatch):
    rows, mapping = district_years
    frame = attach_districts(rows, mapping)
    fit, held = next(model.grouped_splits(frame, column))
    train, test = frame.iloc[fit], frame.iloc[held]
    assert set(train[column]).isdisjoint(test[column])
    if column in ("fips", "district"):
        assert set(train.fips).isdisjoint(test.fips)
    permitted = {frozenset(train[FEATURES[0]])}
    for fit_inner, held_inner in model.grouped_splits(train, column, CONFIG["inner_folds"]):
        inner_train, inner_test = train.iloc[fit_inner], train.iloc[held_inner]
        assert set(inner_train[column]).isdisjoint(inner_test[column])
        permitted.add(frozenset(inner_train[FEATURES[0]]))
    trend_rows, scaler_rows, fit_rows = [], [], []
    trend_init = model.CountyTrends.__init__
    scaler_fit = StandardScaler.fit
    make = model.make_model

    def check_trend(self, values):
        ids = frozenset(values[FEATURES[0]])
        trend_rows.append(ids)
        trend_init(self, values)

    def check_scaler(self, values, *args, **kwargs):
        scaler_rows.append(frozenset(values[:, 0]))
        return scaler_fit(self, values, *args, **kwargs)

    def check_model(name, params, config):
        fitted = make(name, params, config)
        original_fit = fitted.fit

        def fit(values, residuals):
            fit_rows.append(frozenset(values[:, 0]))
            return original_fit(values, residuals)

        fitted.fit = fit
        return fitted

    monkeypatch.setattr(model.CountyTrends, "__init__", check_trend)
    monkeypatch.setattr(StandardScaler, "fit", check_scaler)
    monkeypatch.setattr(model, "make_model", check_model)
    predictions, selected, _ = model.check_fold(train, test, column, CONFIG, np.random.default_rng(42))
    assert set(trend_rows) == set(scaler_rows) == set(fit_rows) == permitted
    changed = test.copy()
    changed["yield_bu_ac"] += 1000
    shifted, other_settings, _ = model.check_fold(train, changed, column, CONFIG, np.random.default_rng(42))
    assert selected == other_settings
    for name in model.MODELS:
        np.testing.assert_array_equal(predictions[name], shifted[name])
    with pytest.raises(ValueError, match="Outer"):
        model.check_fold(frame, test, column, CONFIG, np.random.default_rng(42))


@pytest.mark.parametrize("cohort", ["pooled", "non_irrigated", "all_practices"])
def test_cohort_outputs_are_held_out_and_reproducible(district_years, cohort):
    frame = attach_districts(*district_years)
    config = CONFIG
    first, predictions = evaluate_cohort(frame, cohort, config)
    second, repeated = evaluate_cohort(frame.sample(frac=1, random_state=42), cohort, config)
    assert first == second
    pd.testing.assert_frame_equal(predictions, repeated)
    assert first["districts"] == 4
    assert first["n"] == (64 if cohort == "pooled" else 32)
    if cohort != "pooled":
        assert set(predictions.practice) == {cohort}
        assert set(first["schemes"]) == {"leave_one_year_out", "leave_one_county_out", "leave_one_district_out"}
    assert not predictions.duplicated(["scheme", "fips", "year"]).any()
    for scheme, result in first["schemes"].items():
        assert len(predictions.loc[predictions.scheme.eq(scheme)]) == first["n"]
        assert set(result["performance"]) == set(model.MODELS)
    blocked = first["schemes"]["leave_one_district_out"]
    assert blocked["bootstrap_block"] == "district"
    assert all(v["rmse_bu_ac"]["bootstrap_n"] == config["bootstrap_draws"] for v in blocked["performance"].values())
