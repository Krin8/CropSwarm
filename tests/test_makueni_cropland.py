import io
import json

import numpy as np
from PIL import Image
import pytest

from scripts.cache_p48_rasters import extract
from src.makueni_cropland import (FARM_ID, REPORT, ROOT, Raster, make_study, map_summary,
                                 nearest_candidate, parallel_entry, power_grid_detail, terrain_proxy)


def test_tiff_extract_preserves_native_classes_and_center_coordinates():
    values = np.array([[40, 20, 10], [10, 0, 30], [20, 60, 10]], dtype=np.uint8)
    tags = {33550: (0.01, 0.01, 0.0),
            33922: (0.0, 0.0, 0.0, 37.6, -1.9, 0.0),
            34735: (1, 1, 0, 3, 1024, 0, 1, 2, 1025, 0, 1, 1, 2048, 0, 1, 4326),
            42113: "0"}
    source = io.BytesIO()
    Image.fromarray(values).save(source, format="TIFF", tiffinfo=tags, compression="tiff_lzw")
    source.seek(0)
    clip, grid, nodata = extract(source, (37.601, -1.919, 37.619, -1.901))
    np.testing.assert_array_equal(clip, values[:2, :2])
    np.testing.assert_allclose(grid, [37.6, -1.9, 0.01, 0.01])
    assert nodata == 0


def test_grid_boundary_and_unresolved_area_are_explicit():
    raster = Raster(np.array([[40, 40], [0, 30]], dtype=np.uint8), 37.63, -1.94, 0.01, 0.01)
    point = (-1.95, 37.64)
    report = map_summary(raster, 40, 0, point)
    assert report["class_code"] == 30
    assert report["touching_class_codes"] == [0, 30, 40]
    assert report["crop_pixels"] == 2
    assert report["unresolved_pixels"] == 1
    assert report["cropland_share"] == pytest.approx(0.5, abs=1e-5)
    assert report["classified_share"] == pytest.approx(0.75, abs=1e-5)
    assert int(raster.sample(-3, 42)) == -1


def test_single_agreeing_cell_and_one_product_cannot_qualify():
    values = np.zeros((3, 3), dtype=np.uint8)
    values[1, 1] = 1
    first = Raster(values, 37.64, -1.95, .001, .001)
    original = (-1.95, 37.64)
    assert nearest_candidate({"a": first}, {"a": 1}, original) is None
    assert nearest_candidate({"a": first, "b": first}, {"a": 1, "b": 1}, original) is None
    values[1, 2] = 1
    result = nearest_candidate({"a": first, "b": first}, {"a": 1, "b": 1}, original)
    assert (result["lat"], result["lon"]) == (-1.9515, 37.6415)
    assert result["supporting_products"] == ["a", "b"]


def test_imerg_edge_prevents_weather_reuse_but_other_grids_still_match():
    result = power_grid_detail((-1.95, 37.64), (-1.95, 37.598))
    assert result["MERRA-2"]["alternate_same_cell"]
    assert result["Solar (SRB/CERES)"]["alternate_same_cell"]
    assert not result["GPM IMERG"]["alternate_same_cell"]
    assert not result["GPM IMERG"]["full_disk_shares_cell"]
    assert result["MERRA-2"]["full_disk_shares_cell"]


def test_terrain_interpolates_inside_cross_without_extrapolation():
    rows = [{"elevation": value, "location": {"lat": lat, "lng": lon}} for value, lat, lon in
            [(100, 0, 0), (120, .001, 0), (80, -.001, 0), (100, 0, .001), (100, 0, -.001)]]
    proxy = terrain_proxy(rows, (-.0002, -.0002))
    assert proxy["interpolated_elevation_m"] == pytest.approx(96)
    assert proxy["slope_pct"] == pytest.approx(17.986, abs=0.01)
    assert terrain_proxy(rows, (-.001, -.001)) is None


def test_checked_in_study_rebuilds_offline(monkeypatch):
    def offline(*args, **kwargs):
        pytest.fail("P48 analysis attempted a network request")
    monkeypatch.setattr("requests.sessions.Session.request", offline)
    study = make_study()
    normalized = json.loads(json.dumps(study))
    assert normalized == json.loads((ROOT / "data/processed" / REPORT).read_text())
    assert study["original"]["crop_votes"] == 1 and not study["original"]["meets_rule"]
    assert study["alternate"]["supporting_products"] == ["worldcover", "glad"]
    assert study["products"]["worldcover"]["touching_class_codes"] == [30, 40]
    assert study["products"]["mcd12q1"]["cropland_share"] is None
    assert study["vegetation"]["shared_native_pixel"]
    assert all(grid["alternate_same_cell"] for grid in study["weather"]["native_grids"].values())
    assert study["soil"]["original"]["depths"]["0-5cm"]["clay"]["pixel_col_row"] != (
        study["soil"]["alternate"]["depths"]["0-5cm"]["clay"]["pixel_col_row"])
    entry = parallel_entry(study)
    assert entry == json.loads((ROOT / "config/makueni_alt.json").read_text())
    assert entry["parent_farm_id"] == FARM_ID and entry["weather_ref"].endswith(f"{FARM_ID}.parquet")
    assert "makueni_alt" not in {row["farm_id"] for row in json.loads((ROOT / "config/farms.json").read_text())}


def test_range_cache_resumes_and_refuses_full_download(tmp_path):
    from scripts.cache_p48_rasters import RangeFile

    class Response:
        def __init__(self, status, headers, content=b""):
            self.status_code, self.headers, self.content = status, headers, content
            self.url = "https://example.test/land_cover.tif"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def raise_for_status(self):
            pass

    class Session:
        calls = 0
        full_response = False

        def head(self, url, **options):
            return Response(200, {"Content-Length": "5", "ETag": '"pinned"'})

        def get(self, url, headers, **options):
            self.calls += 1
            assert headers["Range"] == "bytes=0-4"
            assert headers["If-Match"] == '"pinned"'
            if self.full_response:
                return Response(200, {}, b"abcde")
            return Response(206, {"Content-Range": "bytes 0-4/5", "ETag": '"pinned"'}, b"abcde")

    session = Session()
    url = "https://example.test/land_cover.tif"
    first = RangeFile(session, url, tmp_path / "ranged")
    first.seek(1)
    assert first.read(2) == b"bc"
    second = RangeFile(session, url, tmp_path / "ranged")
    assert second.read(5) == b"abcde"
    assert session.calls == 1
    session.full_response = True
    full = RangeFile(session, url, tmp_path / "unranged")
    with pytest.raises(ValueError, match="does not match pinned asset"):
        full.read(5)
    assert not (tmp_path / "unranged" / "0").exists()
