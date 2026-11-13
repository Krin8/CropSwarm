import json
from pathlib import Path

import pandas as pd
import plotly.io as pio
import pytest

from src.diagnostics import contiguous_rain_windows, longest_run, trend, vegetation

ROOT = Path(__file__).resolve().parents[1]
FARMS = json.loads((ROOT / "config/farms.json").read_text())


def test_trend_known_slope_and_two_sided_rank_significance():
    result = trend(pd.Series([1., 2., 3., 4., 5., 6.], index=range(2000, 2006)))
    assert result["linear_per_decade"] == pytest.approx(10)
    assert result["theil_sen_per_decade"] == pytest.approx(10)
    assert result["mann_kendall_significant_0_05"]
    assert longest_run([True, True, False, True]) == 2


def test_rain_windows_wrap_and_cloudy_composite_is_excluded():
    monthly = pd.Series([80, 10, 10, 100, 90, 10, 10, 10, 10, 10, 10, 60], index=range(1, 13))
    assert contiguous_rain_windows(monthly) == [(4, 5), (12, 1)]
    frame = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=7, freq="16D"),
                          "ndvi": [.2, .2, .21, .9, .23, .2, .2],
                          "pixel_reliability": [0, 0, 0, 3, 0, 0, 0], "vi_quality": [0] * 7})
    results, _ = vegetation(frame)
    assert results["2020"]["good_composites"] == 6
    assert results["2020"]["peak_count"] == 0
    assert results["2020"]["status"] == "incomplete"


@pytest.mark.parametrize("farm", FARMS, ids=[farm["farm_id"] for farm in FARMS])
def test_written_assessment_seasons_and_charts(farm):
    out = ROOT / "data/processed"
    farm_id = farm["farm_id"]
    assessment = json.loads((out / f"assessment_{farm_id}.json").read_text())
    seasons = json.loads((out / f"seasons_{farm_id}.json").read_text())
    assert assessment["assessment"]
    assert all(row["source"] for row in assessment["metrics"].values())
    assert seasons["assumed_seasons_per_year"] == farm["seasons_per_year"]
    assert all(seasons["season_windows"][label]["historical"]
               for slot in seasons["slots"] for label in slot["eligible_labels"])
    assert 0 < assessment["metrics"]["precipitation_data_agreement"]["value"]["days"]
    figures = list(out.glob(f"chart_{farm_id}_*.json"))
    assert len(figures) == 4
    for chart in figures:
        assert "NASA" in pio.from_json(chart.read_text()).layout.title.text
