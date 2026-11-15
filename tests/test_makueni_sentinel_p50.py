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
    assert len(report["gate"]["counts"]) == 12 * 5
    if payload.get("chosen_catalog") is None:
        assert not report["gate"]["passed"]
        assert not report["points"]
        return
    if report["gate"]["passed"]:
        assert set(report["points"]) == {row["point_id"] for row in payload["points"]}
        assert report["interpretation_limit"] == "NDVI seasonality does not identify crop type, management or irrigation."


def test_digital_earth_africa_stac_fallback_extracts_grid_baseline_and_public_assets(tmp_path):
    from scripts.cache_p50_sentinel2 import FALLBACK_CATALOG, query_stac_catalog

    properties = {"datetime": "2019-01-04T08:00:34Z",
                  "sentinel:utm_zone": 37, "sentinel:latitude_band": "M", "sentinel:grid_square": "CT",
                  "sentinel:product_id": "S2B_MSIL2A_20190104T074319_N0211_R092_T37MCT_20190104T105348",
                  "created": "2019-01-04T10:53:48Z"}
    assets = {name: {"href": f"s3://deafrica-sentinel-2/sentinel-s2-l2a-cogs/37/M/CT/x/{name}.tif",
                     "raster:bands": [{"nodata": 0, "data_type": "uint16"}]}
              for name in ("B04", "B08", "SCL")}

    class Response:
        status_code = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def raise_for_status(self):
            return None

        def json(self):
            return {"features": [{"id": "public-stac-id", "properties": properties, "assets": assets}],
                    "links": []}

    class Session:
        def post(self, url, **kwargs):
            assert url == FALLBACK_CATALOG["search_url"]
            assert kwargs["json"]["collections"] == ["s2_l2a"]
            return Response()

    items = query_stac_catalog(Session(), FALLBACK_CATALOG, tmp_path)
    assert len(items) == 1
    item = items[0]
    assert item["processing_baseline"] == "02.11"
    assert item["red_offset"] == 0
    assert item["nir_offset"] == 0
    assert item["date"] == "2019-01-04"
    assert item["red_href"].startswith("https://deafrica-sentinel-2.s3.af-south-1.amazonaws.com/")
    page = json.loads(next(tmp_path.glob("stac_deafrica_stac_page_*.json")).read_text())
    assert page["_p50_http_status"] == 200


def test_stac_next_page_merge_retains_collection_and_time_filters(tmp_path):
    from scripts.cache_p50_sentinel2 import FALLBACK_CATALOG, query_stac_catalog

    first = {"features": [], "links": [
        {"rel": "next", "method": "POST", "merge": True, "href": FALLBACK_CATALOG["search_url"],
         "body": {"_o": 100}}
    ]}
    feature = {"id": "second-page", "properties": {
        "datetime": "2019-01-09T08:00:34Z", "sentinel:utm_zone": 37,
        "sentinel:latitude_band": "M", "sentinel:grid_square": "CT",
        "sentinel:product_id": "S2B_MSIL2A_20190109T074319_N0211_R092_T37MCT_20190109T105348"},
        "assets": {name: {"href": f"s3://deafrica-sentinel-2/sentinel-s2-l2a-cogs/37/M/CT/{name}.tif"}
                  for name in ("B04", "B08", "SCL")}}
    second = {"features": [feature], "links": []}

    class Response:
        status_code = 200

        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    class Session:
        def __init__(self):
            self.bodies = []

        def post(self, _url, **kwargs):
            self.bodies.append(kwargs["json"])
            return Response(first if len(self.bodies) == 1 else second)

    session = Session()
    items = query_stac_catalog(session, FALLBACK_CATALOG, tmp_path)
    assert len(items) == 1 and items[0]["id"] == "second-page"
    assert session.bodies[1]["collections"] == ["s2_l2a"]
    assert session.bodies[1]["bbox"] == [37.59, -2.0, 37.69, -1.9]
    assert session.bodies[1]["_o"] == 100


def test_gate_failure_is_saved_without_running_peak_or_group_comparison():
    raw = ROOT / "data/raw/p50/sentinel2_observations.json"
    if not raw.is_file():
        pytest.skip("P50 scene witness has not been fetched")
    report = summarize(json.loads(raw.read_text()))
    assert not report["gate"]["passed"]
    assert report["point_year_gate_failures"] == 6
    assert report["failed_scene_count"] == 0
    assert len(report["gate"]["counts"]) == 60
    assert {row["point_id"] for row in report["gate"]["counts"] if not row["passes"]} == {
        "original", "crop_ref_4", "noncrop_ref_4"}
    assert not report["points"]
    assert not report.get("groups")
    assert all(row["ndvi_source"] and row["mask_source"] for row in report["gate"]["counts"])


def test_saved_report_and_markdown_render_from_cached_witness():
    from src.makueni_sentinel_p50 import OUTPUT, build
    from src.makueni_sentinel_report import DOCUMENT, render

    output = ROOT / "data/processed" / OUTPUT
    report = build(output=output)
    doc = ROOT / "docs" / DOCUMENT
    assert render(report) == doc.read_text()
    assert "6 of 60 point-years" in doc.read_text()
    assert "seasonality does not identify crop type, management or irrigation" in doc.read_text()
    assert "ReadTimeout after 30 seconds on the second STAC page" in doc.read_text()
    assert "No fallback scenes were used in the analysis" in doc.read_text()
