import pandas as pd
import pytest

from src.nasa_consistency import compare, compute, season_days


@pytest.fixture
def seasonal_inputs():
    farm = {"farm_id": "fixture", "lat": 0, "lon": 0}
    windows = {"rainy": {"onset_month": 1, "cessation_month": 2, "source": "fixture calendar"}}
    dates = pd.date_range("2001-01-01", "2005-12-31")
    climate = pd.DataFrame({"date": dates, "PRECTOTCORR": dates.year - 2000,
                            "T2M_MAX": 30 - (dates.year - 2000)})
    rows = []
    for year in range(2001, 2006):
        for day, increment in [(0, 0), (16, .1), (32, .2), (48, .8)]:
            rows.append({"date": pd.Timestamp(year, 1, 1) + pd.Timedelta(days=day),
                         "ndvi": (year - 2000) / 10 + increment if day != 48 else .99,
                         "pixel_reliability": int(day == 48), "vi_quality": 0})
    return farm, windows, climate, pd.DataFrame(rows)


def test_complete_windows_use_qa_day_weights_and_climate_reference(seasonal_inputs):
    farm, windows, climate, ndvi = seasonal_inputs
    args = {"years": range(2001, 2006), "reference_years": [2001, 2002]}
    output = compute(farm, windows, climate, ndvi, **args)
    season = output["seasons"]["rainy"]
    assert season["reference"]["rainfall_mean_mm"] == 88.5
    assert season["reference"]["heat_threshold_c"] == 29
    first = season["rows"][0]
    assert first["rainfall_anomaly_mm"] == -29.5
    assert first["rainfall_deficit_mm"] == 29.5
    assert first["peak_ndvi"] == pytest.approx(.3)
    assert first["qa_days"] == 48
    assert first["integrated_ndvi_days"] == pytest.approx(.2 * 59)
    anomaly = season["comparisons"][0]
    assert anomaly["rho"] == pytest.approx(1)
    assert anomaly["n"] == 5
    assert (anomaly["consistent"], anomaly["assessable"]) == (4, 4)
    assert anomaly["finding"] == "strong expected association"
    assert anomaly == compare(season["rows"], "rainfall_anomaly_mm", "integrated_ndvi_days", 1, 42) | {
        "driver": "rainfall anomaly", "response": "integrated NDVI"}


def test_missing_composite_and_power_fill_are_excluded_not_zeroed(seasonal_inputs):
    farm, windows, climate, ndvi = seasonal_inputs
    climate.loc[climate.date.eq("2001-01-01"), "PRECTOTCORR"] = -999
    ndvi = ndvi.loc[~ndvi.date.eq("2002-01-17")]
    output = compute(farm, windows, climate, ndvi, years=[2001, 2002, 2003], reference_years=[2003])
    first, second, _ = output["seasons"]["rainy"]["rows"]
    assert first["rainfall_mm"] is None and first["peak_ndvi"] is not None
    assert second["integrated_ndvi_days"] is None and second["peak_ndvi"] is None
    assert output["coverage"][1]["status"] == "incomplete"
    assert "2002-01-17" in output["coverage"][1]["missing_dates"]
    assert output["seasons"]["rainy"]["comparisons"][0]["n"] == 1


def test_cross_year_season_is_indexed_by_start_year_and_requires_next_year_ndvi(seasonal_inputs):
    farm, _, climate, ndvi = seasonal_inputs
    window = {"onset_month": 11, "cessation_month": 2, "source": "fixture calendar"}
    days = season_days(2003, window)
    assert str(days[-1].date()) == "2004-02-29"
    result = compute(farm, {"winter": window}, climate, ndvi, years=[2003], reference_years=[2003])
    row = result["seasons"]["winter"]["rows"][0]
    assert row["start_year"] == 2003
    assert row["rainfall_mm"] is not None
    assert not row["record_complete"] and row["peak_ndvi"] is None


def test_wrong_sign_is_reported_even_when_interval_excludes_zero():
    rows = [{"heat": n, "peak": n} for n in range(5)]
    result = compare(rows, "heat", "peak", -1, 42)
    assert result["finding"] == "opposite sign"
    assert (result["consistent"], result["assessable"], result["n"]) == (0, 4, 5)
