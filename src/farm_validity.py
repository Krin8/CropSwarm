"""Verify representative farm evidence from cached CDL and NASA observations."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from functools import partial
from pathlib import Path
import re

import pandas as pd

from .data_pipeline import band_metadata, fetch_chunk, manifest_row, modis_chunks, modis_data, read_json
from .diagnostics import vegetation
from .precompute_cache import RequestCache, write_json
from .validation import load_and_validate

ROOT = Path(__file__).resolve().parents[1]
YEARS = range(2019, 2024)
CDL_ENDPOINT = "https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLValue"
CDL_SOURCE = "USDA NASS Cropland Data Layer | https://www.nass.usda.gov/Research_and_Science/Cropland/metadata/meta.php"
CDL_RESOLUTION = 30
MCD_ENDPOINT = "https://modis.ornl.gov/rst/api/v1/MCD12Q1/subset"
MCD_SOURCE = "NASA MODIS MCD12Q1 IGBP | https://modis-land.gsfc.nasa.gov/pdf/MCD12Q1_C6_Userguide04042018.pdf"
LAND_COVER_YEAR = 2023
QUALIFYING_LAND_COVER = {12, 14}
MODIS_SOURCE = "NASA Terra MOD13Q1 | https://lpdaac.usgs.gov/documents/621/MOD13_User_Guide_V61.pdf"
KALRO = "https://kalroerepository.kalro.org/server/api/core/bitstreams/d25bba84-bf16-4d64-99dc-60aa7283e3ec/content"
VISIBLE_CROPLAND_FLAG = "cropland unverified"


def candidate_points():
    """Convert KALRO trial station coordinates in Table 3 from degrees/minutes/seconds."""
    return [
        {"farm_id": "kenya_katumani", "name": "Katumani, Machakos",
         "lat": -(1 + 35 / 60 + 17 / 3600), "lon": 37 + 14 / 60 + 17 / 3600,
         "source": KALRO},
        {"farm_id": "kenya_kampi_ya_mawe", "name": "Kampi ya Mawe, Makueni",
         "lat": -(1 + 50 / 60 + 54 / 3600), "lon": 37 + 39 / 60 + 29 / 3600,
         "source": KALRO},
    ]


def parse_cdl(body):
    text = body.decode() if isinstance(body, bytes) else body
    match = re.search(r'value:\s*(\d+),\s*category:\s*"([^"]+)"', text)
    if not match:
        raise ValueError("CropScape did not return a class value")
    return {"code": int(match[1]), "category": match[2]}


def cdl_neighborhood(cache, center_evidence):
    """Sample offsets of one native pixel in each direction in the archived Albers CRS."""
    from urllib.parse import parse_qs, urlsplit

    point = parse_qs(urlsplit(center_evidence["2019"]["url"]).query)
    x, y = float(point["x"][0]), float(point["y"][0])
    rows = {}
    for year in YEARS:
        center = parse_cdl(center_evidence[str(year)]["body"])
        samples = []
        for dy in (1, 0, -1):
            for dx in (-1, 0, 1):
                keys = {"year": year, "x": round(x + dx * CDL_RESOLUTION, 3),
                        "y": round(y + dy * CDL_RESOLUTION, 3)}
                if dx == dy == 0:
                    observation = center
                else:
                    observation = cache.fetch(f"cdl_{year}_{dx}_{dy}", CDL_ENDPOINT,
                                              params=keys, parse=parse_cdl, suffix="xml", timeout=8,
                                              attempts=2)
                samples.append({"dx_pixels": dx, "dy_pixels": dy, "request_params": keys,
                                "observation": observation})
        counts = Counter(sample["observation"]["category"] for sample in samples if sample["observation"])
        rows[str(year)] = {"center": center, "category_counts": dict(counts), "samples": samples,
                           "status": "complete" if sum(counts.values()) == len(samples) else "incomplete"}
    return rows


def igbp_neighborhood(body):
    """Return the IGBP class grid for a single annual MCD12Q1 request."""
    grid = next((band["data"] for band in body.get("subset", []) if band["band"] == "LC_Type1"), None)
    rows, columns = body.get("nrows"), body.get("ncols")
    if not grid or not isinstance(rows, int) or not isinstance(columns, int) or len(grid) != rows * columns:
        return None
    center = grid[(rows // 2) * columns + columns // 2]
    counts = Counter(str(code) for code in grid)
    # Require central agreement and a neighborhood majority to avoid a single edge pixel.
    qualifying = sum(code in QUALIFYING_LAND_COVER for code in grid)
    return {"center_class": center, "class_counts": dict(counts), "pixel_count": len(grid),
            "grid_rows": rows, "grid_columns": columns,
            "qualifies": center in QUALIFYING_LAND_COVER and qualifying > len(grid) / 2}


def rainfall_consistent_peaks(frame):
    """Same quality-screened peak method as P5, with explicit lag after each rain peak."""
    annual, _ = vegetation(frame)
    result = {}
    dates = frame.set_index("date")["composite_date"]
    for year in YEARS:
        observation = annual.get(str(year), {"status": "incomplete", "peaks": {"0.12": []}})
        peaks = []
        for composite in observation["peaks"]["0.12"]:
            selected_day = dates.get(pd.Timestamp(composite))
            observed = date.fromisoformat(selected_day) if isinstance(selected_day, str) else date.fromisoformat(composite)
            peaks.append(observed)
        # Screen windows accommodate vegetation lag after typical April and November rains.
        # Use the same calendar-year windows at every point, without January spillover.
        long_rain = [day.isoformat() for day in peaks if day.month in (4, 5, 6, 7)]
        short_rain = [day.isoformat() for day in peaks if day.month in (11, 12)]
        result[str(year)] = {**observation, "long_rain_peaks": long_rain, "short_rain_peaks": short_rain,
                             "two_rain_aligned_peaks": observation["status"] == "complete" and bool(long_rain and short_rain)}
    return result


def kenya_evidence(frame, land_cover):
    annual = rainfall_consistent_peaks(frame)
    qualifying_years = sum(observation["two_rain_aligned_peaks"] for observation in annual.values())
    return {"annual": annual, "land_cover": land_cover, "qualifying_years": qualifying_years,
            "passes": qualifying_years >= 3 and land_cover is not None and land_cover["qualifies"]}


def land_cover(cache, point):
    day = f"A{LAND_COVER_YEAR}001"
    body = cache.fetch(f"mcd12q1_{point['farm_id']}_{LAND_COVER_YEAR}_1km", MCD_ENDPOINT,
                       params={"latitude": point["lat"], "longitude": point["lon"], "startDate": day,
                               "endDate": day, "kmAboveBelow": 1, "kmLeftRight": 1},
                       attempts=2, timeout=12)
    return igbp_neighborhood(body) if body else None


def run_kenya(root, cache, farm, *, fetch=False):
    frame = read_ndvi(root, farm)
    cover = land_cover(cache, farm)
    if cover is None:
        p2 = read_json(root / "data/raw/p2_evidence/kenya_power.json") or {}
        archive = p2.get("points", {}).get("makueni_north", {}).get("landcover", {})
        if archive.get("status") == 200:
            cover = igbp_neighborhood(archive["body"])
    current = kenya_evidence(frame, cover)
    alternatives = {}
    manifests = []
    chosen = farm["farm_id"]
    if not current["passes"]:
        raw = root / "data/raw/p7/ndvi"
        for point in candidate_points():
            cover = land_cover(cache, point)
            jobs = list(modis_chunks(point, YEARS))
            if cover and not cover["qualifies"]:
                manifests.extend(manifest_row(job, raw) for job in jobs if job.path(raw).is_file())
                alternatives[point["farm_id"]] = {**point, "land_cover": cover, "passes": False,
                                                  "status": "rejected by land-cover gate",
                                                  "ndvi_check": "not completed after land-cover rejection"}
                continue
            if fetch:
                with ThreadPoolExecutor(max_workers=4) as pool:
                    list(pool.map(partial(fetch_chunk, raw=raw), jobs))
            manifests.extend(manifest_row(job, raw) for job in jobs)
            ndvi = modis_data(jobs, raw, band_metadata(root))
            ndvi["date"] = pd.to_datetime(ndvi["date"])
            ndvi["composite_date"] = ndvi["composite_date"].map(lambda item: str(item) if item else None)
            alternatives[point["farm_id"]] = {**point, **kenya_evidence(ndvi, cover),
                                              "status": "checked" if cover else "incomplete"}
        eligible = [row for row in alternatives.values() if row["passes"]]
        if eligible:
            chosen = max(eligible, key=lambda row: row["qualifying_years"])["farm_id"]
    write_json(root / "data/raw/p7/ndvi_manifest.json", manifests)
    return {
        "farm_id": farm["farm_id"], "verdict": "pass" if current["passes"] else "pass with flags",
        "flags": [] if current["passes"] else [VISIBLE_CROPLAND_FLAG],
        "coordinate_decision": chosen, "retained": chosen == farm["farm_id"],
        "current": current, "alternatives": alternatives,
        "sources": [MODIS_SOURCE, MCD_SOURCE, "NASA POWER April and November rainfall peaks | data/raw/p2_evidence/kenya_power.json"],
        "rule": "Two clear rain-aligned peaks in at least three of five years and cropland or mosaic at the center and a majority of nearby pixels.",
        "method_assumptions": {"source": "assumption, validate locally", "long_rain_peak_months": [4, 5, 6, 7],
                               "short_rain_peak_months": [11, 12], "ndvi_prominence": 0.12},
    }


def read_ndvi(root, farm):
    return pd.read_csv(root / "data/processed" / f"ndvi_{farm['farm_id']}.csv", parse_dates=["date"])


def telangana_evidence(frame):
    annual, _ = vegetation(frame)
    # Retain marginal observations as a sensitivity check rather than upgrading them in the primary result.
    marginal = frame.copy()
    acceptable = marginal.pixel_reliability.isin((0, 1)) & marginal.vi_quality.notna()
    quality = marginal.vi_quality.fillna(-1).astype(int)
    acceptable &= (quality & 3).le(1) & (quality & ((1 << 8) | (1 << 10) | (1 << 14) | (1 << 15))).eq(0)
    marginal.loc[acceptable, "pixel_reliability"] = 0
    marginal.loc[acceptable, "vi_quality"] = quality & ~3
    sensitivity, _ = vegetation(marginal)
    return {"annual": {str(year): annual.get(str(year)) for year in YEARS},
            "marginal_qa_sensitivity": {str(year): sensitivity.get(str(year)) for year in YEARS},
            "ndvi_2022_gap_filled": annual.get("2022", {}).get("status") == "complete",
            "two_peak_years": sum(annual.get(str(year), {}).get("peak_count", 0) >= 2 for year in YEARS)}


def run_us(root, cache, farm):
    center = read_json(root / "data/raw/p2_evidence/p2_wheat_cdl.json")
    neighborhood = cdl_neighborhood(cache, center)
    annual, _ = vegetation(read_ndvi(root, farm))
    counts = neighborhood["2019"]["category_counts"]
    category = neighborhood["2019"]["center"]["category"]
    agreement = counts.get(category, 0)
    complete = neighborhood["2019"]["status"] == "complete"
    if complete and agreement == 9:
        interpretation = "All nine CDL pixels are fallow/idle in 2019. The MODIS spring peak is greenness evidence and cannot identify planting or rule out weeds, volunteers or neighboring cover."
    elif complete:
        interpretation = "The 2019 CDL neighborhood contains mixed classes. MODIS samples a coarser footprint, so the spring peak cannot be assigned to the center CDL pixel."
    else:
        interpretation = "The CDL neighborhood is incomplete. MODIS spring greenness does not identify planting at the point."
    return {
        "farm_id": farm["farm_id"], "verdict": "pass with flags",
        "flags": ["CDL and MODIS describe different footprints. A verified field management history is unavailable."],
        "neighborhood": neighborhood, "resolution_m": CDL_RESOLUTION,
        "center_matches_entire_sample_every_year": all(
            sample["status"] == "complete" and sample["category_counts"].get(sample["center"]["category"]) == 9
            for sample in neighborhood.values()
        ),
        "spring_ndvi_2019_peaks": [day for day in annual.get("2019", {}).get("peaks", {}).get("0.12", [])
                                  if date.fromisoformat(day).month in (3, 4, 5)],
        "interpretation_2019": interpretation, "sources": [CDL_SOURCE, MODIS_SOURCE],
    }


def run(root=ROOT, *, fetch=False, target="all"):
    farms = {farm["farm_id"]: farm for farm in load_and_validate(root / "config/farms.json", "farms")}
    data = root / "data/processed"
    if target in ("all", "kenya"):
        cache = RequestCache(root / "data/raw/p7/land_cover", offline=not fetch)
        kenya = run_kenya(root, cache, farms["kenya_makueni_north"], fetch=fetch)
        write_json(data / f"validity_{kenya['farm_id']}.json", kenya)
    if target in ("all", "us"):
        cache = RequestCache(root / "data/raw/p7/cdl", offline=not fetch)
        us = run_us(root, cache, farms["us_high_plains_b"])
        write_json(data / f"validity_{us['farm_id']}.json", us)
    if target in ("all", "telangana"):
        farm = farms["telangana_a"]
        evidence = telangana_evidence(read_ndvi(root, farm))
        p2 = read_json(root / "data/raw/p2_evidence/p2_evidence.json") or {}
        archive = p2.get("landcover", {}).get("india_a", {})
        evidence["prior_land_cover"] = igbp_neighborhood(archive["body"]) if archive.get("status") == 200 else None
        verdict = {"farm_id": farm["farm_id"], "verdict": "pass with flags", "evidence": evidence,
                   "flags": ["Quality-screened NDVI does not consistently verify two crop seasons."],
                   "sources": [MODIS_SOURCE, MCD_SOURCE]}
        write_json(data / f"validity_{farm['farm_id']}.json", verdict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Download only missing evidence chunks")
    parser.add_argument("--target", default="all", choices=("all", "kenya", "us", "telangana"))
    arguments = parser.parse_args()
    run(fetch=arguments.fetch, target=arguments.target)
