import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.climate_yield import CountyTrends, MODELS, analyse, check_fold, grouped_splits
from src.county_yield_data import (EXPECTED_UNITS, FEATURES, POWER_FIELDS, SELECTORS, archive_responses,
                                   county_jobs, read_weather, restore_archive, season_features, select_yields)
from src.data_pipeline import daily_dates, fetch_chunk, write_json
from src.scoring import ROOT

CONFIG = json.loads((ROOT / "config/climate_yield.json").read_text())


@pytest.fixture
def county_years():
    rng = np.random.default_rng(8)
    rows = []
    for i in range(4):
        for year in range(2001, 2007):
            features = rng.normal(size=len(FEATURES))
            rows.append({"fips": f"2000{i+1}", "year": year, "practice": "non_irrigated",
                         "yield_bu_ac": 20.0 + i * 3 + (year - 2000) * 2 + 4 * features[0],
                         **dict(zip(FEATURES, features, strict=True))})
    return pd.DataFrame(rows)


def small_config():
    return {**CONFIG, "bootstrap_draws": 20, "forest_trees": 4, "permutation_repeats": 2}


def test_county_yield_precedence_and_invalid_values():
    def row(county, year, value, index):
        return {"STATE_ANSI": "20", "COUNTY_ANSI": county, "COUNTY_CODE": county,
                "YEAR": str(year), "VALUE": value, "SHORT_DESC": list(SELECTORS)[index]}

    raw = pd.DataFrame([row("001", 2000, "42", 1), row("001", 2000, "38", 0),
                        row("001", 2001, "(D)", 0), row("001", 2001, "40", 1),
                        row("998", 2000, "30", 1), row("001", 2002, "(NA)", 1)])
    centroids = pd.DataFrame({"fips": ["20001"]})
    chosen, report = select_yields(raw, centroids, CONFIG)
    assert chosen[["yield_bu_ac", "practice"]].values.tolist() == [[38., "non_irrigated"], [40., "all_practices"]]
    assert report == {"source_rows": 6, "unmatched_county_rows": 1, "unmatched_county_codes": ["998"],
                      "missing_or_invalid_county_values": 2, "duplicate_source_rows": 0,
                      "all_practice_rows_superseded": 1}


def test_cached_weather_archives_units_and_missing_values(tmp_path):
    county = SimpleNamespace(fips="20001", lat=38., lon=-99.)
    config = {**CONFIG, "first_harvest_year": 2001, "last_harvest_year": 2001}
    job, = county_jobs(county, config)
    dates = daily_dates(job)
    parameters = {p: dict.fromkeys(dates.strftime("%Y%m%d"), v)
                  for p, v in zip(POWER_FIELDS, (2., 31., 12., 18.), strict=True)}
    body = {"properties": {"parameter": parameters},
            "parameters": {p: {"units": unit} for p, unit in zip(POWER_FIELDS, EXPECTED_UNITS, strict=True)}}
    cache, archive = tmp_path / "cache", tmp_path / "archive"
    raw_path = job.path(cache)
    write_json(raw_path, {"url": job.url, "params": job.params, "status": 200, "body": body})
    archive_responses([job], cache, archive)
    raw_path.unlink()
    restore_archive(job, cache, archive)
    params = {**parameters, "T2M": {}}
    incomplete_reply = {**body, "properties": {"parameter": params}}
    write_json(raw_path, {"url": job.url, "params": job.params, "status": 200, "body": incomplete_reply})
    restore_archive(job, cache, archive)

    def no_network(*args, **kwargs):
        pytest.fail("Complete raw reply should be reused")
    assert fetch_chunk(job, cache, get=no_network) == "cached"

    crop = {"season_length_days": 3, "heat_tolerance_c": 30, "water_need_mm": 9.}
    sample = read_weather([job], cache)
    row = season_features(sample, 2001, crop, 10, -1, 10.)
    assert row["window_start"] == "2000-10-01" and row["window_end"] == "2000-10-03"
    assert [row[k] for k in FEATURES] == [6., 3., 3, 12., 18.]
    parameters["PRECTOTCORR"]["20001002"] = -999
    write_json(raw_path, {"url": job.url, "params": job.params, "status": 200, "body": body})
    incomplete = season_features(read_weather([job], cache), 2001, crop, 10, -1, 10.)
    assert incomplete["missing_days"]["PRECTOTCORR"] == 1
    assert all(incomplete[k] is None for k in FEATURES)


@pytest.mark.parametrize("column", ["year", "fips"])
def test_outer_and_inner_folds_are_disjoint(county_years, column):
    frame = county_years
    for fit, held in grouped_splits(frame, column):
        train, test = frame.iloc[fit], frame.iloc[held]
        assert test[column].nunique() == 1
        assert set(train[column]).isdisjoint(test[column])
        for inner_fit, inner_held in grouped_splits(train, column, 3):
            assert set(train.iloc[inner_fit][column]).isdisjoint(train.iloc[inner_held][column])
            assert set(train.iloc[inner_fit][column]).isdisjoint(test[column])


def test_holdout_yield_cannot_influence_trends_tuning_or_predictions(county_years):
    config = small_config()
    for column in ("year", "fips"):
        fit, held = next(grouped_splits(county_years, column))
        train, test = county_years.iloc[fit], county_years.iloc[held]
        shifted = test.assign(yield_bu_ac=test.yield_bu_ac + 1000)
        pred, selected, _ = check_fold(train, test, column, config, np.random.default_rng(2))
        other, other_selected, _ = check_fold(train, shifted, column, config, np.random.default_rng(2))
        assert selected == other_selected
        for model in MODELS:
            np.testing.assert_allclose(pred[model], other[model])
        if column == "fips":
            expected = train.groupby("fips").yield_bu_ac.mean().mean()
            np.testing.assert_allclose(CountyTrends(train).predict(test)[0], expected)


def test_model_results_reproduce_and_cover_each_row_once(county_years):
    config = small_config()
    first, predictions = analyse(county_years, config)
    second, repeated = analyse(county_years.sample(frac=1, random_state=9), config)
    assert first == second
    pd.testing.assert_frame_equal(predictions, repeated)
    assert len(predictions) == 2 * len(county_years)
    assert not predictions.duplicated(["scheme", "fips", "year"]).any()
    assert first["leave_one_year_out"]["outer_folds"] == 6
    assert first["leave_one_county_out"]["outer_folds"] == 4
    for result in first.values():
        assert set(result["performance"]) == set(MODELS)
        assert len(result["interpretation"]["ridge"]) == len(FEATURES)
        assert len(result["interpretation"]["ridge"][0]["partial_dependence"]) == len(config["partial_quantiles"])
        assert result["performance"]["ridge"]["rmse_bu_ac"]["bootstrap_n"] == config["bootstrap_draws"]
