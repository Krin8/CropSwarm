"""Cache P50 Sentinel-2 L2A STAC metadata andCOG pixel observations at Makueni.

Run from the repository root with python -m scripts.cache_p50_sentinel2.
Only verified unauthenticated public STAC and Cloud-Optimized GeoTIFF endpoints
are contacted, with on-disk range caching, ETag verification, and bounded backoff.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import io
import json
import math
from pathlib import Path
import time

import numpy as np
from PIL import Image, TiffImagePlugin
import requests
from scipy.ndimage import convolve

from src.makueni_cropland import FARM_ID, RADIUS_M, Raster, distance_m, read_json
from src.precompute_cache import write_json

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data/cache/p50"
RAW = ROOT / "data/raw/p50"

PRIMARY_CATALOG = {
    "id": "earth_search_v1",
    "name": "Element 84 Earth Search v1 (AWS Open Data Sentinel-2 COGs)",
    "search_url": "https://earth-search.aws.element84.com/v1/search",
    "collection": "sentinel-2-l2a",
    "doc_url": "https://registry.opendata.aws/sentinel-2-l2a-cogs/",
}
FALLBACK_CATALOG = {
    "id": "deafrica_stac",
    "name": "Digital Earth Africa STAC (Sentinel-2 L2A COGs)",
    "search_url": "https://explorer.digitalearth.africa/stac/search",
    "collection": "s2_l2a",
    "doc_url": "https://docs.digitalearthafrica.org/en/latest/data_specs/Sentinel-2_Level-2A_specs.html",
}

BBOX = [37.59, -2.0, 37.69, -1.9]
DATETIME_RANGE = "2019-01-01T00:00:00Z/2023-12-31T23:59:59Z"
YEARS = (2019, 2020, 2021, 2022, 2023)
MGRS_TILE = "37MCT"
MIN_SEPARATION_M = 250.0
HEADER_BYTES = 65536
VALID_SCL = (4, 5)


def wgs84_to_utm37s(lat: float, lon: float) -> tuple[float, float]:
    """Project WGS84 latitude/longitude (degrees) to EPSG:32737 (UTM Zone 37S, meters)."""
    a = 6378137.0
    f = 1.0 / 298.257223563
    k0 = 0.9996
    lon0 = math.radians(39.0)
    e2 = f * (2.0 - f)
    ep2 = e2 / (1.0 - e2)
    phi = math.radians(lat)
    lam = math.radians(lon)
    n = a / math.sqrt(1.0 - e2 * math.sin(phi) ** 2)
    t = math.tan(phi) ** 2
    c = ep2 * math.cos(phi) ** 2
    dlon = (lam - lon0) * math.cos(phi)
    m = a * (
        (1.0 - e2 / 4.0 - 3.0 * e2**2 / 64.0 - 5.0 * e2**3 / 256.0) * phi
        - (3.0 * e2 / 8.0 + 3.0 * e2**2 / 32.0 + 45.0 * e2**3 / 1024.0) * math.sin(2.0 * phi)
        + (15.0 * e2**2 / 256.0 + 45.0 * e2**3 / 1024.0) * math.sin(4.0 * phi)
        - (35.0 * e2**3 / 3072.0) * math.sin(6.0 * phi)
    )
    easting = 500000.0 + k0 * n * (
        dlon
        + (1.0 - t + c) * dlon**3 / 6.0
        + (5.0 - 18.0 * t + t**2 + 72.0 * c - 58.0 * ep2) * dlon**5 / 120.0
    )
    northing = 10000000.0 + k0 * (
        m
        + n
        * math.tan(phi)
        * (
            dlon**2 / 2.0
            + (5.0 - t + 9.0 * c + 4.0 * c**2) * dlon**4 / 24.0
            + (61.0 - 58.0 * t + t**2 + 600.0 * c - 330.0 * ep2) * dlon**6 / 720.0
        )
    )
    return round(easting, 3), round(northing, 3)


def select_preregistered_points(root: Path = ROOT) -> list[dict]:
    """Deterministically build the 12 preregistered Makueni points from P48 rasters."""
    farms = read_json(root / "config/farms.json")
    farm = next(row for row in farms if row["farm_id"] == FARM_ID)
    alt_cfg = read_json(root / "config/makueni_alt.json")
    orig = (float(farm["lat"]), float(farm["lon"]))
    alt = (float(alt_cfg["lat"]), float(alt_cfg["lon"]))

    with np.load(root / "data/raw/p48/worldcover.npz", allow_pickle=False) as wc_npz:
        wc = Raster(wc_npz["values"], *wc_npz["grid"])
    with np.load(root / "data/raw/p48/glad.npz", allow_pickle=False) as glad_npz:
        glad = Raster(glad_npz["values"], *glad_npz["grid"])

    lat, lon = glad.centers()
    dist = distance_m(lat, lon, orig)
    in_disk = (dist <= RADIUS_M) & (dist > 0)

    glad_crop_3x3 = convolve((glad.values == 1).astype(int), np.ones((3, 3), dtype=int), mode="constant") == 9
    glad_noncrop_3x3 = convolve((glad.values == 0).astype(int), np.ones((3, 3), dtype=int), mode="constant") == 9

    wc_crop_3x3 = np.ones_like(glad.values, dtype=bool)
    wc_tree_3x3 = np.ones_like(glad.values, dtype=bool)
    wc_grass_3x3 = np.ones_like(glad.values, dtype=bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            sampled = wc.sample(lat + dy * wc.dy, lon + dx * wc.dx)
            wc_crop_3x3 &= sampled == 40
            wc_tree_3x3 &= sampled == 10
            wc_grass_3x3 &= sampled == 30

    def greedy_pick(mask: np.ndarray, count: int, anchors: list[tuple[float, float]]) -> list[tuple[float, float, float]]:
        rows, cols = np.where(mask)
        order = np.lexsort((lon[0, cols], lat[rows, 0], dist[rows, cols]))
        chosen: list[tuple[float, float, float]] = []
        for idx in order:
            r, c = rows[idx], cols[idx]
            pt = (round(float(lat[r, 0]), 9), round(float(lon[0, c]), 9))
            if all(distance_m(pt[0], pt[1], prev) >= MIN_SEPARATION_M for prev in (*anchors, *[p[:2] for p in chosen])):
                chosen.append((pt[0], pt[1], round(float(dist[r, c]), 2)))
                if len(chosen) == count:
                    break
        if len(chosen) != count:
            raise ValueError(f"Expected {count} reference points, found {len(chosen)}")
        return chosen

    anchors = [orig, alt]
    crop_pts = greedy_pick(in_disk & glad_crop_3x3 & wc_crop_3x3, 5, anchors)
    anchors.extend(pt[:2] for pt in crop_pts)
    grass_pts = greedy_pick(in_disk & glad_noncrop_3x3 & wc_grass_3x3, 3, anchors)
    anchors.extend(pt[:2] for pt in grass_pts)
    tree_pts = greedy_pick(in_disk & glad_noncrop_3x3 & wc_tree_3x3, 2, anchors)

    wc_labels = {10: "Tree cover", 30: "Grassland", 40: "Cropland"}
    glad_labels = {0: "No cropland or no data", 1: "Cropland"}

    def make_entry(point_id: str, label: str, group: str, subgroup: str, pt_lat: float, pt_lon: float, dist_m: float) -> dict:
        wc_code = int(wc.sample(pt_lat, pt_lon))
        glad_code = int(glad.sample(pt_lat, pt_lon))
        utm_x, utm_y = wgs84_to_utm37s(pt_lat, pt_lon)
        return {
            "point_id": point_id,
            "label": label,
            "group": group,
            "subgroup": subgroup,
            "lat": pt_lat,
            "lon": pt_lon,
            "distance_from_original_m": dist_m,
            "utm37s_x": utm_x,
            "utm37s_y": utm_y,
            "worldcover_code": wc_code,
            "worldcover_class": wc_labels.get(wc_code, f"Class {wc_code}"),
            "glad_code": glad_code,
            "glad_class": glad_labels.get(glad_code, f"Class {glad_code}"),
        }

    entries = [
        make_entry("original", "Original Makueni point", "study", "original", orig[0], orig[1], 0.0),
        make_entry(
            "makueni_alt",
            "Parallel cropland-map point (makueni_alt)",
            "study",
            "makueni_alt",
            alt[0],
            alt[1],
            round(float(distance_m(alt[0], alt[1], orig)), 2),
        ),
    ]
    for idx, (pt_lat, pt_lon, dist_m) in enumerate(crop_pts, 1):
        entries.append(
            make_entry(
                f"crop_ref_{idx}",
                f"Cropland reference {idx}",
                "cropland_ref",
                "cropland",
                pt_lat,
                pt_lon,
                dist_m,
            )
        )
    for idx, (pt_lat, pt_lon, dist_m) in enumerate(grass_pts, 1):
        entries.append(
            make_entry(
                f"noncrop_ref_{idx}",
                f"Non-cropland reference {idx} (grassland)",
                "noncropland_ref",
                "grassland",
                pt_lat,
                pt_lon,
                dist_m,
            )
        )
    for idx, (pt_lat, pt_lon, dist_m) in enumerate(tree_pts, 4):
        entries.append(
            make_entry(
                f"noncrop_ref_{idx}",
                f"Non-cropland reference {idx} (tree cover)",
                "noncropland_ref",
                "tree_cover",
                pt_lat,
                pt_lon,
                dist_m,
            )
        )
    return entries


def s3_to_https(href: str) -> str:
    if href.startswith("s3://sentinel-cogs/"):
        return "https://sentinel-cogs.s3.us-west-2.amazonaws.com/" + href.removeprefix("s3://sentinel-cogs/")
    if href.startswith("s3://deafrica-sentinel-2/"):
        return "https://deafrica-sentinel-2.s3.af-south-1.amazonaws.com/" + href.removeprefix("s3://deafrica-sentinel-2/")
    return href


def fetch_range(session: requests.Session, url: str, start: int, end: int, cache_dir: Path, expected_etag: str | None = None) -> tuple[bytes, dict]:
    """Fetch an inclusive byte range [start, end] with on-disk caching, ETag validation, and bounded backoff."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
    block_path = cache_dir / f"{key}_{start}_{end}.bin"
    meta_path = cache_dir / f"{key}_{start}_{end}.json"
    expected_len = end - start + 1
    if block_path.is_file() and meta_path.is_file():
        meta = json.loads(meta_path.read_text())
        if meta.get("url") == url and (expected_etag is None or meta.get("etag") == expected_etag):
            data = block_path.read_bytes()
            if len(data) == meta.get("length"):
                return data, meta

    headers = {"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"}
    if expected_etag:
        headers["If-Match"] = expected_etag

    last_err = None
    for attempt in range(3):
        try:
            with session.get(url, headers=headers, timeout=30, allow_redirects=False) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    raise PermissionError(f"Unauthenticated request redirected ({response.status_code}) to {response.headers.get('Location')}")
                if response.status_code in (401, 403):
                    raise PermissionError(f"Authentication required ({response.status_code}) for {url}")
                response.raise_for_status()
                content_range = response.headers.get("Content-Range", "")
                etag = response.headers.get("ETag")
                if response.status_code != 206 or not content_range.startswith(f"bytes {start}-"):
                    raise ValueError(f"Expected 206 Partial Content for {url} ({start}-{end}), got {response.status_code} {content_range}")
                if expected_etag and etag != expected_etag:
                    raise ValueError(f"ETag mismatch for {url}: expected {expected_etag}, got {etag}")
                data = response.content
                total_bytes = int(content_range.split("/")[-1])
                expected_actual = min(expected_len, total_bytes - start)
                if len(data) != expected_actual:
                    raise ValueError(f"Truncated range response: got {len(data)} bytes, expected {expected_actual}")
                meta = {"url": url, "start": start, "end": end, "length": len(data), "total_bytes": total_bytes,
                        "etag": etag, "http_status": response.status_code,
                        "content_range": content_range}
                tmp_bin = block_path.with_suffix(".part")
                tmp_bin.write_bytes(data)
                tmp_bin.replace(block_path)
                write_json(meta_path, meta)
                return data, meta
        except (requests.RequestException, ValueError) as exc:
            last_err = exc
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    raise RuntimeError(str(last_err))


def parse_cog_header(header_bytes: bytes) -> dict:
    """Parse IFD0 georeferencing and tile table from the initial COG header bytes."""
    with Image.open(io.BytesIO(header_bytes)) as img:
        tags = img.tag_v2
        dx, dy, *_ = tags[33550]
        col, row, _, east, north, *_ = tags[33922]
        west = east - col * dx
        top = north + row * dy
        tile_w, tile_h = int(tags[322]), int(tags[323])
        offsets = [int(x) for x in tags[324]]
        counts = [int(x) for x in tags[325]]
        raw_tags = {k: tags[k] for k in (258, 259, 266, 317, 339) if k in tags}
        return {
            "width": int(img.width),
            "height": int(img.height),
            "west": float(west),
            "north": float(top),
            "dx": float(dx),
            "dy": float(dy),
            "tile_w": tile_w,
            "tile_h": tile_h,
            "tiles_across": math.ceil(img.width / tile_w),
            "offsets": offsets,
            "counts": counts,
            "raw_tags": raw_tags,
        }


def decode_cog_tile(payload: bytes, info: dict) -> np.ndarray:
    """Decode a single compressed COG tile using Pillow without downloading the full image."""
    tile_w, tile_h = info["tile_w"], info["tile_h"]
    raw_tags = info["raw_tags"]
    header = b"II*\x00\x08\x00\x00\x00"
    directory = TiffImagePlugin.ImageFileDirectory_v2(header)
    for key, value in {
        256: tile_w,
        257: tile_h,
        258: raw_tags.get(258, (8,)),
        262: 1,
        273: (0,),
        277: 1,
        278: tile_h,
        279: (len(payload),),
        284: 1,
        339: raw_tags.get(339, (1,)),
    }.items():
        directory[key] = value
    for key in (259, 266, 317):
        if key in raw_tags:
            directory[key] = raw_tags[key]
    with Image.open(io.BytesIO(header + directory.tobytes(8) + payload)) as pixels:
        return np.array(pixels)


def sample_cog_points(session: requests.Session, url: str, points: list[dict], cache_dir: Path, active_indices: list[int] | None = None) -> tuple[dict[int, int], str | None]:
    """Sample a remote COG at the specified point indices using range requests for the header and needed tile(s)."""
    indices = list(range(len(points))) if active_indices is None else active_indices
    if not indices:
        return {}, None
    header_bytes, header_meta = fetch_range(session, url, 0, HEADER_BYTES - 1, cache_dir)
    etag = header_meta.get("etag")
    info = parse_cog_header(header_bytes)
    by_tile: dict[tuple[int, int], list[tuple[int, int, int]]] = {}
    for idx in indices:
        pt = points[idx]
        col = math.floor((pt["utm37s_x"] - info["west"]) / info["dx"])
        row = math.floor((info["north"] - pt["utm37s_y"]) / info["dy"])
        if not (0 <= col < info["width"] and 0 <= row < info["height"]):
            raise ValueError(f"Point {pt['point_id']} falls outside raster {url}")
        tx, ty = col // info["tile_w"], row // info["tile_h"]
        by_tile.setdefault((tx, ty), []).append((idx, row % info["tile_h"], col % info["tile_w"]))

    results: dict[int, int] = {}
    for (tx, ty), members in by_tile.items():
        tile_index = ty * info["tiles_across"] + tx
        offset = info["offsets"][tile_index]
        byte_count = info["counts"][tile_index]
        if byte_count == 0:
            for idx, _, _ in members:
                results[idx] = 0
            continue
        payload, _ = fetch_range(session, url, offset, offset + byte_count - 1, cache_dir, expected_etag=etag)
        tile_arr = decode_cog_tile(payload, info)
        for idx, local_r, local_c in members:
            results[idx] = int(tile_arr[local_r, local_c])
    return results, etag


def query_stac_catalog(session: requests.Session, catalog: dict, cache_dir: Path) -> list[dict]:
    """Query all STAC items for 2019-2023 covering Makueni with pagination and on-disk caching."""
    cache_file = cache_dir / f"stac_{catalog['id']}_items.json"
    if cache_file.is_file():
        return json.loads(cache_file.read_text())

    items: list[dict] = []
    body: dict = {
        "collections": [catalog["collection"]],
        "bbox": BBOX,
        "datetime": DATETIME_RANGE,
        "limit": 100,
    }
    url = catalog["search_url"]
    page = 0
    while url:
        page += 1
        last_err = None
        for attempt in range(3):
            try:
                with session.post(url, json=body, timeout=30, allow_redirects=False) as response:
                    if response.status_code in (301, 302, 303, 307, 308, 401, 403):
                        raise PermissionError(f"STAC search returned HTTP {response.status_code} for {url}")
                    response.raise_for_status()
                    payload = response.json()
                    break
            except (requests.RequestException, ValueError) as exc:
                last_err = exc
                if attempt == 2:
                    raise
                time.sleep(2**attempt)
        else:
            raise RuntimeError(str(last_err))

        features = payload.get("features", [])
        for feat in features:
            props = feat.get("properties", {})
            tile = (
                props.get("s2:mgrs_tile")
                or props.get("mgrs:latitude_band", "")
                + props.get("mgrs:grid_square", "")
            )
            grid_code = props.get("grid:code", "")
            if tile != MGRS_TILE and grid_code != f"MGRS-{MGRS_TILE}" and MGRS_TILE not in feat.get("id", ""):
                continue
            assets = feat.get("assets", {})
            red_asset = assets.get("red") or assets.get("B04")
            nir_asset = assets.get("nir") or assets.get("B08")
            scl_asset = assets.get("scl") or assets.get("SCL")
            if not (red_asset and nir_asset and scl_asset):
                continue

            def band_scale_offset(asset_obj: dict, baseline: str) -> tuple[float, float]:
                rb = asset_obj.get("raster:bands")
                if isinstance(rb, list) and rb:
                    scale = float(rb[0].get("scale", 0.0001))
                    offset = float(rb[0].get("offset", 0.0))
                    return scale, offset
                return (0.0001, -0.1 if baseline >= "04.00" else 0.0)

            baseline = str(props.get("s2:processing_baseline") or "00.00")
            red_scale, red_offset = band_scale_offset(red_asset, baseline)
            nir_scale, nir_offset = band_scale_offset(nir_asset, baseline)
            dt = str(props.get("datetime", ""))
            items.append(
                {
                    "id": feat["id"],
                    "date": dt[:10],
                    "datetime": dt,
                    "processing_baseline": baseline,
                    "generation_time": str(props.get("s2:generation_time") or props.get("created") or dt),
                    "eo_cloud_cover": props.get("eo:cloud_cover"),
                    "red_href": s3_to_https(red_asset["href"]),
                    "nir_href": s3_to_https(nir_asset["href"]),
                    "scl_href": s3_to_https(scl_asset["href"]),
                    "red_scale": red_scale,
                    "red_offset": red_offset,
                    "nir_scale": nir_scale,
                    "nir_offset": nir_offset,
                }
            )

        next_link = next(
            (link for link in payload.get("links", []) if link.get("rel") == "next"),
            None,
        )
        if next_link and features:
            url = next_link.get("href", url)
            if "body" in next_link:
                body = next_link["body"]
            else:
                break
        else:
            break

    cache_dir.mkdir(parents=True, exist_ok=True)
    write_json(cache_file, items)
    return items


def deduplicate_items(items: list[dict]) -> tuple[list[dict], int]:
    """Retain one item per sensing date (YYYY-MM-DD), choosing highest processing baseline then generation time."""
    by_date: dict[str, dict] = {}
    duplicates = 0
    for item in items:
        day = item["date"]
        if not day or int(day[:4]) not in YEARS:
            continue
        key = (item["processing_baseline"], item["generation_time"], item["id"])
        if day in by_date:
            duplicates += 1
            prev = by_date[day]
            prev_key = (prev["processing_baseline"], prev["generation_time"], prev["id"])
            if key > prev_key:
                by_date[day] = item
        else:
            by_date[day] = item
    deduped = [by_date[day] for day in sorted(by_date)]
    return deduped, duplicates


def process_scene(item: dict, points: list[dict], cache_dir: Path) -> dict:
    """Extract SCL and (for clear pixels) B04 and B08 values for all 12 points in a single scene."""
    scene_cache = cache_dir / "scenes" / f"{item['date']}_{item['id']}.json"
    if scene_cache.is_file():
        cached = json.loads(scene_cache.read_text())
        if cached.get("status") == "ok":
            return cached
        scene_cache.unlink()

    with requests.Session() as session:
        try:
            scl_map, scl_etag = sample_cog_points(session, item["scl_href"], points, cache_dir / "blocks")
            clear_indices = [idx for idx, code in scl_map.items() if code in VALID_SCL]
            if clear_indices:
                red_map, red_etag = sample_cog_points(
                    session, item["red_href"], points, cache_dir / "blocks", active_indices=clear_indices
                )
                nir_map, nir_etag = sample_cog_points(
                    session, item["nir_href"], points, cache_dir / "blocks", active_indices=clear_indices
                )
            else:
                red_map, nir_map = {}, {}
                red_etag = nir_etag = None
            record = {
                "id": item["id"],
                "date": item["date"],
                "datetime": item["datetime"],
                "processing_baseline": item["processing_baseline"],
                "eo_cloud_cover": item["eo_cloud_cover"],
                "red_scale": item["red_scale"],
                "red_offset": item["red_offset"],
                "nir_scale": item["nir_scale"],
                "nir_offset": item["nir_offset"],
                "status": "ok",
                "error": None,
                "etags": {"scl": scl_etag, "red": red_etag, "nir": nir_etag},
                "scl": [int(scl_map[i]) for i in range(len(points))],
                "red_dn": [int(red_map[i]) if i in red_map else None for i in range(len(points))],
                "nir_dn": [int(nir_map[i]) if i in nir_map else None for i in range(len(points))],
            }
        except Exception as exc:
            record = {
                "id": item["id"],
                "date": item["date"],
                "datetime": item["datetime"],
                "processing_baseline": item["processing_baseline"],
                "eo_cloud_cover": item["eo_cloud_cover"],
                "red_scale": item["red_scale"],
                "red_offset": item["red_offset"],
                "nir_scale": item["nir_scale"],
                "nir_offset": item["nir_offset"],
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "etags": {},
                "scl": [None] * len(points),
                "red_dn": [None] * len(points),
                "nir_dn": [None] * len(points),
            }
    scene_cache.parent.mkdir(parents=True, exist_ok=True)
    write_json(scene_cache, record)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=8, help="Concurrent scene workers")
    parser.add_argument("--limit", type=int, default=0, help="Optional scene limit for smoke testing")
    args = parser.parse_args()

    points = select_preregistered_points(ROOT)
    catalog_attempts = []
    chosen_catalog = None
    raw_items: list[dict] = []

    with requests.Session() as session:
        for catalog in (PRIMARY_CATALOG, FALLBACK_CATALOG):
            try:
                raw_items = query_stac_catalog(session, catalog, CACHE)
                catalog_attempts.append(
                    {
                        "id": catalog["id"],
                        "name": catalog["name"],
                        "search_url": catalog["search_url"],
                        "collection": catalog["collection"],
                        "doc_url": catalog["doc_url"],
                        "status": "ok",
                        "items_returned": len(raw_items),
                        "error": None,
                    }
                )
                if raw_items:
                    chosen_catalog = catalog
                    break
            except Exception as exc:
                catalog_attempts.append(
                    {
                        "id": catalog["id"],
                        "name": catalog["name"],
                        "search_url": catalog["search_url"],
                        "collection": catalog["collection"],
                        "doc_url": catalog["doc_url"],
                        "status": "failed",
                        "items_returned": 0,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

    if chosen_catalog is None:
        RAW.mkdir(parents=True, exist_ok=True)
        write_json(
            RAW / "sentinel2_observations.json",
            {
                "catalog_attempts": catalog_attempts,
                "chosen_catalog": None,
                "mgrs_tile": MGRS_TILE,
                "bbox": BBOX,
                "years": list(YEARS),
                "raw_item_count": 0,
                "duplicate_items_removed": 0,
                "unique_scene_dates": 0,
                "points": points,
                "scenes": [],
            },
        )
        print("All public STAC catalogs failed.")
        return

    deduped, duplicates = deduplicate_items(raw_items)
    if args.limit > 0:
        deduped = deduped[: args.limit]

    print(f"Catalog {chosen_catalog['id']}: {len(raw_items)} raw items, {len(deduped)} unique dates ({duplicates} duplicates removed).")
    scenes_by_date: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        future_map = {pool.submit(process_scene, item, points, CACHE): item["date"] for item in deduped}
        done_count = 0
        for future in as_completed(future_map):
            day = future_map[future]
            scenes_by_date[day] = future.result()
            done_count += 1
            if done_count % 50 == 0 or done_count == len(deduped):
                print(f"Processed {done_count}/{len(deduped)} scenes...")

    ordered_scenes = [scenes_by_date[item["date"]] for item in deduped]
    if args.limit == 0:
        RAW.mkdir(parents=True, exist_ok=True)
        write_json(
            RAW / "sentinel2_observations.json",
            {
                "catalog_attempts": catalog_attempts,
                "chosen_catalog": chosen_catalog,
                "mgrs_tile": MGRS_TILE,
                "bbox": BBOX,
                "years": list(YEARS),
                "raw_item_count": len(raw_items),
                "duplicate_items_removed": duplicates,
                "unique_scene_dates": len(ordered_scenes),
                "points": points,
                "scenes": ordered_scenes,
            },
        )
        ok_scenes = sum(s["status"] == "ok" for s in ordered_scenes)
        failed_scenes = sum(s["status"] != "ok" for s in ordered_scenes)
        print(f"Saved {len(ordered_scenes)} scenes to data/raw/p50/sentinel2_observations.json (ok={ok_scenes}, failed={failed_scenes}).")


if __name__ == "__main__":
    main()
