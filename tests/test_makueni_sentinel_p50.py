"""Offline fixtures for the P50 Sentinel-2 NDVI witness analysis."""

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from scripts.cache_p50_sentinel2 import select_preregistered_points
from src.makueni_sentinel_p50 import (ACCEPTED_SCL, MIN_COMPOSITES_PER_YEAR,
                                     MIN_SCENES_PER_YEAR, composite_frame,
                                     point_observations, summarize)
from src.scoring import ROOT


def point(point_id, group="cropland_ref", subgroup="cropland"):
    return {"point_id": point_id, "lat": -1.95, "lon": 37.64,
            "group": group, "subgroup": subgroup}


def scene(day, scl=4, red=2000, nir=6000, status="ok"):
    return {"id": day, "date": day, "status": status,
            "scl": [scl], "red_dn": [red], "nir_dn": [nir],
            "red_scale": 0.0001, "red_offset": 0.0,
            "nir_scale": 0.0001, "nir_offset": 0.0}


def test_preregistered_points_reproduce_map_agreement_and_selection():
    points = select_preregistered_points(ROOT)
    assert len(points) == 12
    assert [row["point_id"] for row in points[:2]] == ["original", "makueni_alt"]
    assert all(row["worldcover_code"] == 40 and row["glad_code"] == 1
               for row in points[2:7])
    assert all(row["worldcover_code"] in (10, 30) and row["glad_code"] == 0
               for row in points[7:])


def test_scl_mask_and_dn_scaling_exclude_clouds_and_bad_reflectance():
    payload = {"points": [point("a")], "scenes": [
        scene("2019-01-04", scl=4, red=2000, nir=6000),
        scene("2019-01-09", scl=9, red=2000, nir=6000),
        scene("2019-01-14", scl=5, red=0, nir=4000),
        scene("2019-01-19", scl=4, red=2000, nir=6000, status="failed"),
    ]}
    rows, counts = point_observations(payload)
    assert len(rows["a"]) == 1
    assert rows["a"][0]["date"] == "2019-01-04"
    assert rows["a"][0]["ndvi"] == pytest.approx(0.5)
    assert rows["a"][0]["scl"] == 4
    assert counts["a"]["2019"]["valid_scene_count"] == 1
    assert counts["a"]["2019"]["scl_counts"] == {"4": 1, "5": 1, "9": 1}
    assert counts["a"]["2019"]["masked_scl_counts"] == {"9": 1}
    assert counts["a"]["2019"]["rejected_band_or_ndvi_counts"]["zero_DN"] == 1
    assert counts["a"]["2019"]["failed_scene_count"] == 1
    assert ACCEPTED_SCL == {4, 5}


def test_missing_scenes_do_not_become_zero_vegetation_composites():
    frame = composite_frame([{"date": "2019-01-02", "year": 2019, "ndvi": 0.7}])
    assert len(frame) == 115
    assert frame.iloc[0]["ndvi"] == pytest.approx(0.7)
    assert frame.iloc[0]["pixel_reliability"] == 0
    assert frame.iloc[1]["ndvi"] == 0
    assert frame.iloc[1]["pixel_reliability"] == 3
    assert frame.iloc[1]["vi_quality"] == 2062
    assert frame.iloc[23]["pixel_reliability"] == 3


def test_gate_requires_minimum_scene_and_composite_counts_at_every_point():
    points = [point("a")]
    scenes = [scene((date(year, 1, 1) + timedelta(days=16 * window)).isoformat())
              for year in range(2019, 2024) for window in range(10)]
    result = summarize({"points": points, "scenes": scenes}, min_scenes=10, min_composites=8)
    assert result["gate"]["passed"]
    broken = {"points": points, "scenes": scenes[:-3]}
    failed = summarize(broken, min_scenes=10, min_composites=8)
    assert not failed["gate"]["passed"]
    assert failed["status"] == "observation gate failed; do not interpret seasonality"
    assert failed["points"] == {}


def test_actual_cached_p50_witness_is_processed_offline_when_present():
    raw = ROOT / "data/raw/p50/sentinel2_observations.json"
    if not raw.is_file():
        pytest.skip("P50 scene witness has not been fetched")
    payload = json.loads(raw.read_text())
    report = summarize(payload)
    assert report["chosen_catalog"]
    assert len(report["gate"]["counts"]) == 12 * 5
    if report["gate"]["passed"]:
        assert set(report["points"]) == {row["point_id"] for row in payload["points"]}
        assert report["interpretation_limit"] == "NDVI seasonality does not identify crop type, management or irrigation."
