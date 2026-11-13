"""P4 NASA climate and vegetation precompute. Run with python -m src.data_pipeline."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from tempfile import NamedTemporaryFile
import time
from urllib.parse import parse_qsl, urlsplit, urlunsplit

import pandas as pd
import requests

from .validation import POWER_FILL_VALUE, load_and_validate

ROOT = Path(__file__).resolve().parents[1]
POWER = "https://power.larc.nasa.gov/api/temporal/daily/point"
MODIS = "https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset"
POWER_PARAMETERS = (
    "T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "GWETROOT",
    "ALLSKY_SFC_SW_DWN", "RH2M",
)
IMERG = "IMERG_PRECTOT"
UTC_RAIN = "PRECTOTCORR_UTC"
POWER_SOURCE = "NASA POWER daily (AG, LST)"
POWER_UTC_SOURCE = "NASA POWER daily (AG, UTC)"
MODIS_SOURCE = "NASA Terra MODIS MOD13Q1 via ORNL DAAC"
BAND_NAMES = {
    "ndvi": "250m_16_days_NDVI",
    "evi": "250m_16_days_EVI",
    "pixel_reliability": "250m_16_days_pixel_reliability",
    "vi_quality": "250m_16_days_VI_Quality",
    "composite_date": "250m_16_days_composite_day_of_the_year",
}
MODIS_COLUMNS = ("ndvi", "evi", "pixel_reliability", "vi_quality", "composite_date")
# ORNL TESViS allows at most ten dates per subset.
MODIS_WINDOWS = ((1, 145), (161, 305), (321, 353))
# Operational choices (not empirical). Timeout is per connect/read, not a job deadline.
TIMEOUT = (10, 65)
BACKOFF_SECONDS = (2, 8)
POWER_FIRST_YEAR = 1991
POWER_LAST_YEAR = 2025
IMERG_FIRST_YEAR = 2000
CORE_MODIS_YEARS = range(2019, 2024)
EXTENDED_MODIS_YEARS = range(2015, 2025)


@dataclass(frozen=True)
class Chunk:
    farm_id: str
    name: str
    url: str
    params: dict

    @property
    def id(self):
        payload = json.dumps([self.url, self.params], sort_keys=True).encode()
        return f"{self.name}_{hashlib.sha256(payload).hexdigest()[:12]}"

    @property
    def source(self):
        if self.url != POWER:
            return MODIS_SOURCE
        return POWER_UTC_SOURCE if self.params["time-standard"] == "UTC" else POWER_SOURCE

    def path(self, raw):
        return raw / self.farm_id / f"{self.id}.json"


def power_chunks(farm):
    point = {"longitude": farm["lon"], "latitude": farm["lat"]}
    for kind, first, parameters, standard in (
        ("power", POWER_FIRST_YEAR, POWER_PARAMETERS, "LST"),
        ("imerg", IMERG_FIRST_YEAR, (IMERG, "PRECTOTCORR"), "UTC"),
    ):
        for start in range(first, POWER_LAST_YEAR + 1, 5):
            end = min(start + 4, POWER_LAST_YEAR)
            params = {
                **point, "start": f"{start}0101", "end": f"{end}1231",
                "community": "AG", "format": "JSON", "time-standard": standard,
                "parameters": ",".join(parameters),
            }
            yield Chunk(farm["farm_id"], f"{kind}_{start}_{end}", POWER, params)


def modis_chunks(farm, years):
    point = {"latitude": farm["lat"], "longitude": farm["lon"]}
    for year in years:
        for first, last in MODIS_WINDOWS:
            start, end = f"A{year}{first:03}", f"A{year}{last:03}"
            params = {
                **point, "startDate": start, "endDate": end,
                "kmAboveBelow": 0, "kmLeftRight": 0,
            }
            yield Chunk(farm["farm_id"], f"modis_{start}_{end}", MODIS, params)


def modis_day(code):
    return datetime.strptime(code, "A%Y%j").date()


def modis_codes(chunk):
    start, end = chunk.params["startDate"], chunk.params["endDate"]
    return {f"{start[:5]}{day:03}" for day in range(int(start[5:]), int(end[5:]) + 1, 16)}


def daily_dates(chunk):
    return pd.date_range(chunk.params["start"], chunk.params["end"], name="date")


def present_body(chunk, body):
    """An HTTP success with unusable data is not a complete cache entry."""
    if not isinstance(body, dict):
        return False
    if chunk.url == POWER:
        properties = body.get("properties")
        if not isinstance(properties, dict):
            return False
        layer = properties.get("parameter")
        if not isinstance(layer, dict):
            return False
        required = chunk.params["parameters"].split(",")
        return any(isinstance(layer.get(key), dict) and layer[key] for key in required)
    rows = body.get("subset")
    return (
        body.get("nrows") == body.get("ncols") == 1
        and isinstance(rows, list)
        and any(isinstance(row, dict) and row.get("band") == BAND_NAMES["ndvi"] for row in rows)
    )


def payload_complete(chunk, body):
    if not present_body(chunk, body):
        return False
    if chunk.url == POWER:
        parameters = body["properties"]["parameter"]
        days = set(daily_dates(chunk).strftime("%Y%m%d"))
        return all(
            isinstance(parameters.get(key), dict) and days <= parameters[key].keys()
            for key in chunk.params["parameters"].split(",")
        )
    ndvi_dates = {
        row.get("modis_date") for row in body["subset"]
        if isinstance(row, dict) and row.get("band") == BAND_NAMES["ndvi"]
        and isinstance(row.get("data"), list) and len(row["data"]) == 1
    }
    return modis_codes(chunk) <= ndvi_dates


def atomic_write(path, writer):
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(prefix=f".{path.name}.", dir=path.parent, delete=False) as handle:
        temp = Path(handle.name)
    try:
        writer(temp)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def write_json(path, payload):
    atomic_write(path, lambda temp: temp.write_text(json.dumps(payload, separators=(",", ":")) + "\n"))


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def cache_hit(chunk, record):
    return (
        isinstance(record, dict)
        and record.get("url") == chunk.url
        and record.get("params") == chunk.params
        and record.get("status") == 200
        and payload_complete(chunk, record.get("body"))
    )


def import_p2_modis(chunks, raw, evidence_path):
    """Reuse checked-in point subsets with exactly matching coordinates and date ranges."""
    evidence = read_json(evidence_path) or {}
    candidates = {}
    for response in evidence.get("modis", {}).values():
        url = urlsplit(response.get("url", ""))
        if response.get("status") == 200 and urlunsplit(url._replace(query="")) == MODIS:
            candidates[tuple(sorted(parse_qsl(url.query)))] = response
    for chunk in chunks:
        if chunk.path(raw).exists():
            continue
        key = tuple(sorted((key, str(value)) for key, value in chunk.params.items()))
        response = candidates.get(key)
        if response and payload_complete(chunk, response.get("body")):
            write_json(chunk.path(raw), {
                "url": chunk.url, "params": chunk.params, "status": 200,
                "timestamp": evidence["checked_at"], "timestamp_kind": "P2 evidence batch",
                "imported_from": "data/raw/p2_evidence/p2_evidence.json",
                "body": response["body"],
            })


def fetch_chunk(chunk, raw, *, get=requests.get, sleep=time.sleep):
    path = chunk.path(raw)
    previous = read_json(path)
    if cache_hit(chunk, previous):
        return "cached"
    attempts = list(previous.get("attempts", [])) if isinstance(previous, dict) else []
    best = previous if isinstance(previous, dict) and present_body(chunk, previous.get("body")) else None
    for delay in (0, *BACKOFF_SECONDS):
        if delay:
            sleep(delay)
        attempt = {"timestamp": datetime.now(timezone.utc).isoformat(), "status": None}
        body = None
        try:
            response = get(chunk.url, params=chunk.params, timeout=TIMEOUT)
            attempt["status"] = response.status_code
            try:
                body = response.json()
            except ValueError:
                body = {"non_json_excerpt": response.text[:1000]}
            if response.status_code == 200 and not payload_complete(chunk, body):
                attempt["error"] = "Expected dates or primary data missing from response"
        except requests.RequestException as exc:
            attempt["error"] = str(exc)
        attempts.append(attempt)
        record = {"url": chunk.url, "params": chunk.params, **attempt, "body": body, "attempts": attempts}
        if present_body(chunk, body) and record["status"] == 200:
            best = record
        # Keep the last usable response if the current attempt failed.
        if best is not None:
            record = {**best, "attempts": attempts}
        write_json(path, record)
        if cache_hit(chunk, record):
            return "fetched"
        if attempt["status"] is not None and 400 <= attempt["status"] < 500 and attempt["status"] not in (408, 429):
            break
    return "incomplete"


def get_cached(chunk, raw):
    record = read_json(chunk.path(raw)) or {}
    if record.get("url") == chunk.url and record.get("params") == chunk.params and record.get("status") == 200:
        body = record.get("body")
        if present_body(chunk, body):
            return body
    return None


def power_data(chunks, raw):
    frame = pd.DataFrame(index=pd.date_range(f"{POWER_FIRST_YEAR}-01-01", f"{POWER_LAST_YEAR}-12-31", name="date"))
    for key in (*POWER_PARAMETERS, IMERG, UTC_RAIN):
        frame[key] = float("nan")
    units = {}
    for chunk in chunks:
        body = get_cached(chunk, raw)
        if body is None:
            continue
        params = body["properties"]["parameter"]
        fill = body.get("header", {}).get("fill_value", POWER_FILL_VALUE)
        expected = daily_dates(chunk).strftime("%Y%m%d")
        for key in chunk.params["parameters"].split(","):
            values = params.get(key, {})
            if not isinstance(values, dict):
                continue
            values = pd.to_numeric(pd.Series(values, dtype="object"), errors="coerce").reindex(expected)
            values = values.mask(values.isin((fill, POWER_FILL_VALUE)))
            column = UTC_RAIN if key == "PRECTOTCORR" and chunk.params["time-standard"] == "UTC" else key
            frame.loc[daily_dates(chunk), column] = values.to_numpy()
            unit = body.get("parameters", {}).get(key, {}).get("units")
            if unit:
                if column in units and unit != units[column]:
                    raise ValueError(f"Units changed across POWER chunks for {chunk.farm_id}, {column}")
                units[column] = unit
    frame["source"] = "NASA POWER daily (AG)"
    return frame.reset_index(), units


def band_metadata(root):
    path = root / "data/raw/smoke/modis_bands.json"
    item = (read_json(path) or {})["attempts"][-1]
    return {entry["band"]: entry for entry in item["body"]["bands"]}


def band_value(value, spec):
    lower, upper = (float(limit) for limit in spec["valid_range"].split(" to "))
    if not isinstance(value, (float, int)) or not math.isfinite(value):
        return None
    if value == float(spec["fill_value"]) or not lower <= value <= upper:
        return None
    if "scale_factor" in spec:
        return float(value) * float(spec["scale_factor"]) + float(spec.get("add_offset", 0))
    return int(value)


def modis_data(chunks, raw, metadata):
    names = {band: field for field, band in BAND_NAMES.items()}
    rows = {}
    for chunk in chunks:
        expected = modis_codes(chunk)
        body = get_cached(chunk, raw)
        if body is None:
            continue
        for item in body["subset"]:
            if not isinstance(item, dict):
                continue
            code, band = item.get("modis_date"), item.get("band")
            pixels = item.get("data")
            if code not in expected or band not in names or not isinstance(pixels, list) or len(pixels) != 1:
                continue
            day = modis_day(code)
            row = rows.setdefault(day, {"date": day, "source": MODIS_SOURCE})
            value = band_value(pixels[0], metadata[band])
            if names[band] == "composite_date" and value is not None:
                pixel_day = date(day.year, 1, 1) + timedelta(days=value - 1)
                value = pixel_day if pixel_day.year == day.year and day <= pixel_day < day + timedelta(days=16) else None
            row[names[band]] = value
    return pd.DataFrame((rows[day] for day in sorted(rows)), columns=("date", *MODIS_COLUMNS, "source"))


def missing_dates(frame, column):
    return frame.loc[frame[column].isna(), "date"].dt.strftime("%Y-%m-%d").tolist()


def coverage_summary(climate, units, ndvi, modis_jobs):
    climate_report = {}
    for parameter in (*POWER_PARAMETERS, IMERG, UTC_RAIN):
        utc = parameter in (IMERG, UTC_RAIN)
        eligible = climate.loc[climate.date.dt.year >= IMERG_FIRST_YEAR] if utc else climate
        missing = missing_dates(eligible, parameter)
        climate_report[parameter] = {
            "unit": units.get(parameter), "source": POWER_UTC_SOURCE if utc else POWER_SOURCE,
            "expected_count": len(eligible),
            "missing_dates": missing, "status": "incomplete" if missing else "complete",
        }
    expected = sorted({modis_day(code) for job in modis_jobs for code in modis_codes(job)})
    by_date = ndvi.set_index("date").reindex(expected)
    vegetation = {}
    for year in sorted({day.year for day in expected}):
        year_rows = by_date.loc[[day for day in expected if day.year == year]]
        missing = {
            field: [str(day) for day in year_rows.index[year_rows[field].isna()]]
            for field in MODIS_COLUMNS
        }
        vegetation[str(year)] = {
            "expected_count": len(year_rows), "missing_dates_by_field": missing,
            "status": "incomplete" if missing["ndvi"] else "complete",
        }
    return {"power": climate_report, "modis": vegetation}


def manifest_row(job, raw):
    path = job.path(raw)
    entry = read_json(path) or {}
    return {
        "farm_id": job.farm_id, "source": job.source, "url": job.url,
        "params": job.params, "timestamp": entry.get("timestamp"), "status": entry.get("status"),
        "coverage": "complete" if cache_hit(job, entry) else "incomplete",
        "raw_file": str(path.relative_to(raw)) if path.exists() else None,
    }


def diagnostic_manifest(raw, current_jobs):
    """Keep earlier requests visible when an API requires corrected parameters."""
    paths = {job.path(raw) for job in current_jobs}
    records = []
    for path in sorted(raw.glob("*/*.json")):
        if path in paths:
            continue
        entry = read_json(path) or {}
        if entry.get("url") == POWER and entry.get("params", {}).get("parameters") == IMERG:
            records.append({
                "farm_id": path.parent.name, "source": POWER_SOURCE,
                "url": entry.get("url"), "params": entry.get("params"),
                "timestamp": entry.get("timestamp"), "status": entry.get("status"),
                "coverage": "superseded", "raw_file": str(path.relative_to(raw)),
            })
    return records


def run(root=ROOT, *, fetch=False, extended=True, workers=4):
    farms = load_and_validate(root / "config/farms.json", "farms")
    raw = root / "data/raw/p4"
    processed = root / "data/processed"
    # Preserve and prefer the 2019–2023 core windows before fetching optional years.
    years = list(CORE_MODIS_YEARS)
    if extended:
        years.extend(year for year in EXTENDED_MODIS_YEARS if year not in CORE_MODIS_YEARS)
    power = {farm["farm_id"]: list(power_chunks(farm)) for farm in farms}
    modis = {farm["farm_id"]: list(modis_chunks(farm, years)) for farm in farms}
    all_jobs = [job for collection in (power, modis) for jobs in collection.values() for job in jobs]
    import_p2_modis([job for jobs in modis.values() for job in jobs], raw, root / "data/raw/p2_evidence/p2_evidence.json")
    if fetch:
        # Alternate farms so a slow location cannot delay all work at the other farms.
        power_order = [job for group in zip(*power.values(), strict=True) for job in group]
        modis_order = [job for group in zip(*modis.values(), strict=True) for job in group]
        pending = [job for job in (*power_order, *modis_order) if not cache_hit(job, read_json(job.path(raw)))]
        print(f"{len(pending)} NASA chunks need network fetch", flush=True)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for job, outcome in zip(pending, pool.map(lambda chunk: fetch_chunk(chunk, raw), pending), strict=True):
                print(f"{job.farm_id}/{job.name}: {outcome}", flush=True)
    metadata = band_metadata(root)
    report = {}
    for farm in farms:
        key = farm["farm_id"]
        climate, units = power_data(power[key], raw)
        ndvi = modis_data(modis[key], raw, metadata)
        atomic_write(processed / f"climate_{key}.parquet", lambda temp: climate.to_parquet(temp, index=False))
        atomic_write(processed / f"ndvi_{key}.csv", lambda temp: ndvi.to_csv(temp, index=False))
        report[key] = coverage_summary(climate, units, ndvi, modis[key])
    write_json(processed / "coverage_p4.json", report)
    write_json(raw / "manifest.json", [manifest_row(job, raw) for job in all_jobs] + diagnostic_manifest(raw, all_jobs))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="explicitly enable network requests for cache misses")
    years = parser.add_mutually_exclusive_group()
    years.add_argument("--core-only", action="store_true", help="limit MODIS to 2019–2023")
    years.add_argument("--extended", action="store_true", help="include 2015–2024 MODIS windows (default)")
    parser.add_argument("--workers", type=int, default=4, choices=range(1, 9))
    args = parser.parse_args()
    run(fetch=args.fetch, extended=not args.core_only, workers=args.workers)


if __name__ == "__main__":
    main()
