from dataclasses import replace
import json

import numpy as np
import pandas as pd
import pytest

from src.opportunity_windows import (bare_runs, compute, fit_year, modeled_addition, normalize_weather,
                                     prepare_ndvi, summarize_checks)
from src.scoring import ROOT, preload

CONFIG = json.loads((ROOT / "config/opportunity_windows.json").read_text())
GRADES = json.loads((ROOT / "config/evidence_grades.json").read_text())


@pytest.fixture
def observations():
    dates = pd.date_range("2001-01-01", periods=6, freq="16D")
    spans = {day: day + pd.Timedelta(days=16) for day in dates}
    ndvi = pd.DataFrame({"date": dates[[0, 1, 3, 4, 5]],
                         "ndvi": [.24, .23, .10, .10, .25],
                         "pixel_reliability": [0, 0, 1, 0, 0],
                         "vi_quality": [0, 0, 0, 0, 0]})
    return spans, ndvi


def test_detection_does_not_bridge_missing_or_bad_qa(observations):
    spans, ndvi = observations
    series = prepare_ndvi(ndvi, spans)
    days = list(spans)
    assert pd.isna(series[days[2]]) and pd.isna(series[days[3]])
    assert bare_runs(series, spans, .25) == [tuple(days[:2])]
    assert bare_runs(series, spans, .20) == []
    assert bare_runs(series, spans, .30) == [tuple(days[:2]), tuple(days[4:])]


def test_run_can_continue_across_calendar_year():
    dates = pd.DatetimeIndex(["2003-12-19", "2004-01-01"])
    spans = {dates[0]: dates[1], dates[1]: pd.Timestamp("2004-01-17")}
    assert bare_runs(pd.Series([.1, .1], index=dates), spans, .25) == [tuple(dates)]
    assert (spans[dates[-1]] - dates[0]).days == 29


@pytest.fixture
def cover_crop():
    return {"season_length_days": 4, "heat_tolerance_c": 35, "min_temp_c": 10, "max_temp_c": 30,
            "water_need_mm": 40, "min_rain_mm": 24, "max_rain_mm": 60}


@pytest.fixture
def weather():
    return pd.DataFrame({"date": pd.date_range("2001-01-01", periods=4), "PRECTOTCORR": 3.,
                         "T2M": 20., "T2M_MAX": 30., "T2M_MIN": 4., "GWETROOT": .25})


def test_fit_length_heat_frost_rain_irrigation_and_missing(cover_crop, weather):
    policy = {"max_hot_day_fraction": .1}
    window = {"anchor_year": 2001, "start": "2001-01-01", "days": 4}

    def fit(frame, *, irrigation=.5, frost_free=True, run=window):
        return fit_year(run, cover_crop, normalize_weather(frame), 20, irrigation, policy, frost_free)

    good = fit(weather)
    assert all(good[k] for k in ("length", "temperature", "water", "overall"))
    assert good["initial_soil_water_proxy_mm"] == 5
    assert good["irrigation_mm"] == 11.5
    assert fit(weather, irrigation=0)["water"] is False
    assert fit(weather.assign(PRECTOTCORR=16))["water"] is False
    assert fit(weather.assign(T2M=31))["temperature"] is False
    assert fit(weather.assign(T2M_MAX=[36, 30, 30, 30]))["heat_days"] == 1
    assert fit(weather.assign(T2M_MAX=[36, 30, 30, 30]))["temperature"] is False
    assert fit(weather.assign(T2M_MIN=0))["temperature"] is False
    assert fit(weather.assign(T2M_MIN=0), frost_free=False)["temperature"] is True
    missing = fit(weather.assign(GWETROOT=[-999, .25, .25, .25]))
    assert missing["water"] is missing["overall"] is None
    short = fit(weather, run={**window, "days": 3})
    assert short["length"] is short["overall"] is False and short["temperature"] is None
    assert summarize_checks([good, short, missing]) == {
        "length": {"passes": 2, "n": 3}, "temperature": {"passes": 2, "n": 2},
        "water": {"passes": 1, "n": 1}, "overall": {"passes": 1, "n": 2}}


def test_fixture_recurrence_sensitivity_and_seeded_bootstrap(weather):
    farm = json.loads((ROOT / "config/farms.json").read_text())[0]
    model = preload(farm)
    spans, rows = {}, []
    for index, year in enumerate(range(2001, 2006)):
        dates = pd.date_range(f"{year}-01-01", periods=5, freq="16D")
        for slot, day in enumerate(dates):
            spans[day] = day + pd.Timedelta(days=16)
            ndvi = .22 if slot < 2 + index % 3 else .6
            rows.append({"date": day, "ndvi": ndvi, "pixel_reliability": 0, "vi_quality": 0})
    ndvi = pd.DataFrame(rows)
    first = compute(model, ndvi, weather, spans, CONFIG, GRADES)
    assert first == compute(model, ndvi, weather, spans, CONFIG, GRADES)
    assert [row["threshold"] for row in first["sensitivity"]] == [.2, .25, .3]
    assert not first["sensitivity"][0]["windows"]
    window = first["sensitivity"][1]["windows"][0]
    assert window["supporting_years"] == 5
    assert window["status"] == "recurrent" and not window["threshold_stable"]
    assert window["qa_composites"] == 14 and window["typical_days"] == 48
    assert window["bootstrap_interval"]["length_days"] == [32, 64]
    assert first["evidence"]["window"]["label"] == "low"
    assert first["evidence"]["ndvi"]["shares"]["nasa_measured"] == 1


def test_modeled_addition_reuses_engine_without_mutating_baseline():
    farm = json.loads((ROOT / "config/farms.json").read_text())[0]
    model = preload(farm)
    index = model.ids.index("green_gram")
    crop = model.crops[model.ids[index]]
    sample = np.tile([2., 22., 28.], (crop["season_length_days"], 1))
    original = model.additions.copy()
    result = modeled_addition(model, index, sample)
    assert result["nitrogen"] == pytest.approx(crop["n_credit_kg_ha"] - crop["n_demand_kg_ha"])
    assert result["erosion_proxy"] == pytest.approx(-model.slope * 2 * crop["cover_score"])
    assert result["water_used"] == pytest.approx(2 * len(sample))
    assert result["water_used"] + result["unmet_water"] == pytest.approx(crop["water_need_mm"])
    assert np.array_equal(model.additions, original)
    assert result == modeled_addition(replace(model, additions=original), index, sample)
