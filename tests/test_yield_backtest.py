import pandas as pd
import pytest

from src.yield_backtest import crop_stress, detrend, evaluate, load_yields


@pytest.fixture
def growing_window():
    return {"season_length_days": 3, "water_need_mm": 30, "heat_tolerance_c": 30}


def test_nass_series_does_not_mix_practices_or_fill_disclosure_codes():
    frame = pd.DataFrame({"YEAR": [1990, 1991, 1991, 1992, 2025],
                          "SHORT_DESC": ["dry", "dry", "all", "dry", "dry"],
                          "VALUE": ["10", "(D)", "100", "0", "50"]})
    result, unit = load_yields(frame, "quickstats", "dry", (1990, 2024))
    assert result.to_dict("records") == [{"year": 1990, "yield": 10}, {"year": 1992, "yield": 0}]
    assert unit == "bu/acre"
    with pytest.raises(ValueError, match="Duplicate"):
        load_yields(pd.concat([frame, frame]), "quickstats", "dry", (1990, 2024))


def test_linear_detrend_uses_elapsed_years_even_with_gaps():
    yields = pd.DataFrame({"year": [1991, 1994, 1999], "yield": [12, 18, 28]})
    assert detrend(yields).anomaly.tolist() == [0, 0, 0]
    perturbed = yields.assign(yield_=[12, 24, 28]).drop(columns="yield").rename(columns={"yield_": "yield"})
    output = detrend(perturbed)
    assert output.anomaly.sum() == pytest.approx(0)
    assert output.anomaly.iloc[1] > 0


def test_crop_stress_handles_fill_independently_and_counts_strict_heat(growing_window):
    dates = pd.date_range("2000-01-01", periods=3)
    climate = pd.DataFrame({"PRECTOTCORR": [20, 0, 0], "T2M_MAX": [30, 31, 29]}, index=dates)
    assert crop_stress(climate, dates[0], growing_window, storage=5, supply=.5) == {
        "window_start": "2000-01-01", "window_end": "2000-01-03", "water_deficit_mm": 7.5, "heat_days": 1}
    climate.loc[dates[1], "PRECTOTCORR"] = -999
    stress = crop_stress(climate, dates[0], growing_window, storage=5, supply=.5)
    assert stress["water_deficit_mm"] is None
    assert stress["heat_days"] == 1


def test_harvest_year_alignment_and_seeded_rank_result(growing_window):
    years = [2000, 2001, 2002, 2003, 2004]
    yields = pd.DataFrame({"year": years, "yield": [10, 18, 13, 6, 14]})
    days = pd.date_range("2000-10-01", "2003-10-03")
    climate = pd.DataFrame({"PRECTOTCORR": 4., "T2M_MAX": 30.}, index=days)
    climate.loc["2001-10-01", "T2M_MAX"] = 32.
    climate.loc["2002-10-01":"2002-10-02", "T2M_MAX"] = 32.
    rows, comparisons = evaluate(yields, climate, growing_window, 10, -1, 0, 0)
    assert rows[0]["window_start"] == "1999-10-01"
    assert rows[0]["heat_days"] is None and rows[1]["heat_days"] == 0
    assert comparisons[0]["n"] == comparisons[1]["n"] == 4
    assert comparisons[0]["rho"] is None
    assert comparisons[1]["bootstrap_95"] is not None
    assert (rows, comparisons) == evaluate(yields, climate, growing_window, 10, -1, 0, 0)
