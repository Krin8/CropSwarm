"""Offline checks over real responses saved by src.smoke_test."""

import json
from pathlib import Path

import pytest


RAW = Path(__file__).resolve().parents[1] / "data/raw/smoke"


def response(name):
    record = json.loads((RAW / f"{name}.json").read_text(encoding="utf-8"))
    assert record["status"] == "PASS", name
    return record["attempts"][-1]["body"]


@pytest.mark.parametrize("point", ["us", "india"])
def test_power_2023_daily(point):
    body = response(f"power_{point}")
    assert body["header"]["fill_value"] == -999
    expected = {"T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "GWETROOT",
                "ALLSKY_SFC_SW_DWN", "RH2M"}
    assert set(body["properties"]["parameter"]) == expected
    assert all(len(values) == 365 for values in body["properties"]["parameter"].values())
    assert all(body["parameters"][key]["units"] for key in expected)


@pytest.mark.parametrize("point", ["us", "india"])
def test_modis_2023_ndvi_and_quality(point):
    dates = set()
    for part in (1, 2, 3):
        body = response(f"modis_{point}_{part}")
        bands = {row["band"] for row in body["subset"]}
        assert {"250m_16_days_NDVI", "250m_16_days_VI_Quality",
                "250m_16_days_pixel_reliability"} <= bands
        dates.update(row["modis_date"] for row in body["subset"] if row["band"] == "250m_16_days_NDVI")
    assert len(dates) == 23
    metadata = response("modis_bands")["bands"]
    ndvi = next(b for b in metadata if b["band"] == "250m_16_days_NDVI")
    assert ndvi["scale_factor"] == "0.0001"


@pytest.mark.parametrize("point", ["us", "india"])
def test_srtm_point_and_grid(point):
    single = response(f"srtm_{point}_point")
    grid = response(f"srtm_{point}_grid")
    assert single["status"] == grid["status"] == "OK"
    assert len(single["results"]) == 1
    assert len(grid["results"]) == 9
    assert all(isinstance(row["elevation"], (int, float)) for row in grid["results"])


def test_soilgrids_documented_wcs_fallback():
    # REST is currently paused by ISRIC; this checks access to their documented
    # WCS alternative, not the availability of clay/sand/SOC pixel values.
    body = response("soilgrids_wcs_clay")
    assert "wcs:Capabilities" in body
    assert "clay_0-5cm_Q0.5" in body


def test_manifest_records_observations():
    entries = json.loads((RAW / "manifest.json").read_text(encoding="utf-8"))
    by_name = {row["source"]: row for row in entries}
    for source in ("power_us", "modis_us_1", "srtm_us_grid", "soilgrids_wcs_clay"):
        row = by_name[source]
        assert row["http_status"] == 200
        assert row["latency_s"] >= 0
        assert row["url"]
        assert "units" in row and "fill_missing" in row and "sample_row" in row
    assert by_name["soilgrids_us"]["status"] == "FAIL"
