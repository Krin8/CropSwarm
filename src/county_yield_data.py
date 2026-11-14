"""Prepare P25 Kansas county winter-wheat yields and resumable POWER weather."""
import argparse
import gzip
import hashlib
from concurrent.futures import ThreadPoolExecutor
import csv
from pathlib import Path
import json
from xml.etree import ElementTree

import numpy as np
import pandas as pd

from src.crops import load_crops
from src.data_pipeline import (Chunk, POWER, ROOT, atomic_write, cache_hit, daily_dates, fetch_chunk,
                               get_cached, manifest_row, read_json)
from src.precompute_cache import write_json
from src.scoring import daily_water_deficit
from src.validation import POWER_FILL_VALUE

SELECTORS = {
    "WHEAT, WINTER, NON-IRRIGATED - YIELD, MEASURED IN BU / ACRE": "non_irrigated",
    "WHEAT, WINTER - YIELD, MEASURED IN BU / ACRE": "all_practices",
}
POWER_FIELDS = ("PRECTOTCORR", "T2M_MAX", "ALLSKY_SFC_SW_DWN", "T2M")
FEATURES = ("rainfall_mm", "water_deficit_mm", "heat_days", "radiation_mj_m2_day", "mean_temp_c")
FEATURE_LABELS = dict(zip(FEATURES, ("Season rainfall (mm)", "Modeled water deficit (mm)",
                                    "Heat days", "Mean daily solar radiation (MJ/m²/day)",
                                    "Mean air temperature (°C)"), strict=True))
EXPECTED_UNITS = ("mm/day", "C", "MJ/m^2/day", "C")


def extract_centroids(html):
    rows = ElementTree.parse(html).findall(".//{*}tr")
    headers = [cell.text.strip() for cell in rows[0]]
    items = [dict(zip(headers, (cell.text.strip() for cell in row), strict=True)) for row in rows[1:]]
    return pd.DataFrame([{"fips": row["GEOID"], "county": row["BASENAME"], "lat": float(row["CENTLAT"]),
                          "lon": float(row["CENTLON"])} for row in items])


def extract_bulk(source, out, config):
    """Keep matching source rows and columns. Stream the full bulk file or a tab-separated slice."""
    fields = ("STATE_ANSI", "COUNTY_ANSI", "COUNTY_CODE", "COUNTY_NAME", "YEAR", "VALUE", "SHORT_DESC",
              "SOURCE_DESC", "DOMAIN_DESC", "AGG_LEVEL_DESC", "FREQ_DESC", "REFERENCE_PERIOD_DESC", "LOAD_TIME")
    opener = gzip.open if source.suffix == ".gz" else open
    with opener(source, "rt", encoding="latin-1", newline="") as handle, out.open("w", newline="") as saved:
        reader = csv.DictReader(handle, delimiter="\t")
        writer = csv.DictWriter(saved, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in reader:
            if (row["SHORT_DESC"] in SELECTORS and row["STATE_ANSI"] == config["state_fips"]
                    and row["SOURCE_DESC"] == "SURVEY" and row["DOMAIN_DESC"] == "TOTAL"
                    and row["AGG_LEVEL_DESC"] == "COUNTY" and row["FREQ_DESC"] == "ANNUAL"
                    and row["REFERENCE_PERIOD_DESC"] == "YEAR" and row["YEAR"].isdigit()
                    and config["first_harvest_year"] <= int(row["YEAR"]) <= config["last_harvest_year"]):
                writer.writerow({key: row[key].replace("\x00", "") for key in fields})


def select_yields(raw, centroids, config):
    """Prefer non-irrigated by county-year. Keep all-practice fallback explicitly tagged."""
    rows = raw.assign(
        fips=raw.STATE_ANSI + raw.COUNTY_ANSI,
        year=raw.YEAR.astype(int),
        yield_bu_ac=pd.to_numeric(raw.VALUE.str.replace(",", ""), errors="coerce"),
        practice=raw.SHORT_DESC.map(SELECTORS),
    )
    is_county = rows.fips.isin(centroids.fips)
    valid = rows.yield_bu_ac.ge(0) & np.isfinite(rows.yield_bu_ac)
    rows_valid = rows[is_county & valid].copy()
    duplicated = rows_valid.groupby(["fips", "year", "practice"]).yield_bu_ac.nunique()
    if (duplicated > 1).any():
        raise ValueError(f"Conflicting USDA values: {duplicated[duplicated > 1].index.tolist()}")
    ordered = rows_valid.assign(preferred=rows_valid.practice.eq("non_irrigated")).sort_values(
        ["fips", "year", "preferred"], ascending=[True, True, False])
    preferred = ordered.drop_duplicates(["fips", "year"])
    result = preferred[["fips", "year", "yield_bu_ac", "practice"]].reset_index(drop=True)
    return result, {"source_rows": len(rows), "unmatched_county_rows": int((~is_county).sum()),
                    "missing_or_invalid_county_values": int((is_county & ~valid).sum()),
                    "unmatched_county_codes": sorted(set(rows.loc[~is_county, "COUNTY_CODE"].dropna())),
                    "duplicate_source_rows": len(rows_valid) - len(duplicated),
                    "all_practice_rows_superseded": len(duplicated) - len(result)}


def county_jobs(county, config):
    first = config["first_harvest_year"] - 1
    last = config["last_harvest_year"]
    for start in range(first, last + 1, config["power_chunk_years"]):
        end = min(start + config["power_chunk_years"] - 1, last)
        yield Chunk(county.fips, f"power_{start}_{end}", POWER, {
            "latitude": county.lat, "longitude": county.lon, "start": f"{start}0101", "end": f"{end}1231",
            "community": "AG", "format": "JSON", "time-standard": "LST", "parameters": ",".join(POWER_FIELDS),
        })


def restore_archive(job, cache, archives):
    """Materialize an unmodified raw response if its tracked compressed copy exists."""
    path = job.path(cache)
    archive = job.path(archives).with_suffix(".json.gz")
    if not archive.exists() or cache_hit(job, read_json(path)):
        return
    raw = gzip.decompress(archive.read_bytes())
    if not path.exists() or cache_hit(job, json.loads(raw)):
        atomic_write(path, lambda tmp: tmp.write_bytes(raw))


def archive_responses(jobs, cache, archives):
    for job in jobs:
        source = job.path(cache)
        target = job.path(archives).with_suffix(".json.gz")
        if source.exists():
            data = gzip.compress(source.read_bytes(), mtime=0)
            atomic_write(target, lambda tmp: tmp.write_bytes(data))


def read_weather(jobs, raw):
    pieces = []
    for job in jobs:
        payload = get_cached(job, raw)
        dates = daily_dates(job)
        data = pd.DataFrame(index=dates, columns=list(POWER_FIELDS), dtype=float)
        if payload is not None:
            fill = payload.get("header", {}).get("fill_value", POWER_FILL_VALUE)
            parameters = payload["properties"]["parameter"]
            for field, unit in zip(POWER_FIELDS, EXPECTED_UNITS, strict=True):
                metadata = payload.get("parameters", {}).get(field, {})
                if field in parameters and metadata.get("units") != unit:
                    raise ValueError(f"Unverified POWER units for {job.farm_id}, {field}: {metadata}")
                row = pd.Series(parameters.get(field, {}), dtype=object).reindex(dates.strftime("%Y%m%d"))
                values = pd.to_numeric(row, errors="coerce").replace([fill, POWER_FILL_VALUE, np.inf, -np.inf], np.nan)
                data[field] = values.to_numpy()
        pieces.append(data)
    return pd.concat(pieces, verify_integrity=True)


def season_features(weather, harvest_year, crop, onset, offset, storage):
    start = pd.Timestamp(harvest_year + offset, onset, 1)
    dates = pd.date_range(start, periods=crop["season_length_days"])
    sample = weather.reindex(dates)
    valid = sample.notna().sum()
    result = {"window_start": start.date().isoformat(), "window_end": dates[-1].date().isoformat(),
              "missing_days": {field: int(len(dates) - valid[field]) for field in POWER_FIELDS}}
    if (valid != len(dates)).any():
        return {**result, **dict.fromkeys(FEATURES)}
    rain = sample.PRECTOTCORR
    deficit = daily_water_deficit(rain.to_numpy()[None, :], crop["water_need_mm"], storage)[0]
    return {**result, **dict(zip(FEATURES, (float(rain.sum()), float(deficit),
                    int(sample.T2M_MAX.gt(crop["heat_tolerance_c"]).sum()), float(sample.ALLSKY_SFC_SW_DWN.mean()),
                    float(sample.T2M.mean())), strict=True))}


def prepare(root=ROOT, *, fetch=False, archive=False):
    config = json.loads((root / "config/climate_yield.json").read_text())
    raw = root / "data/raw/p25"
    centroids = pd.read_csv(raw / "kansas_centroids.csv", dtype={"fips": str})
    source = pd.read_csv(raw / "quickstats_kansas.csv", dtype=str)
    yields, selection = select_yields(source, centroids, config)
    counts = yields.groupby("fips").size().to_dict()
    climate_raw = raw / "power"
    archives = raw / "power_archive"
    output = root / "data/processed"
    eligible = centroids[centroids.fips.map(counts).fillna(0).ge(config["minimum_yield_years"])]
    jobs = {row.fips: list(county_jobs(row, config)) for row in eligible.itertuples(index=False)}
    flat_jobs = [job for county in jobs.values() for job in county]
    for job in flat_jobs:
        restore_archive(job, climate_raw, archives)
    if fetch:
        with ThreadPoolExecutor(max_workers=config["fetch_workers"]) as pool:
            states = list(pool.map(lambda job: fetch_chunk(job, climate_raw), flat_jobs))
        print({state: states.count(state) for state in sorted(set(states))}, flush=True)
    if archive:
        archive_responses(flat_jobs, climate_raw, archives)

    p20 = json.loads((root / "config/yield_backtest.json").read_text())
    spec = p20["farms"]["us_high_plains_b"]["series"][0]
    calendar = json.loads((output / "seasons_us_high_plains_b.json").read_text())
    window = calendar["season_windows"][spec["season"]]
    crop = load_crops(root / "data/crops.csv")[spec["crop"]]
    coverage, features = [], []
    for county in centroids.itertuples(index=False):
        records = yields[yields.fips.eq(county.fips)]
        complete = 0
        missing = []
        status = "fewer than minimum yield years"
        if county.fips in jobs:
            weather = read_weather(jobs[county.fips], climate_raw)
            for row in records.itertuples(index=False):
                feature = season_features(weather, row.year, crop, window["onset_month"], spec["start_year_offset"],
                                          config["storage_proxy_mm"])
                if feature[FEATURES[0]] is None:
                    missing.append({"year": row.year, **feature["missing_days"]})
                else:
                    complete += 1
                    features.append({**row._asdict(), **{key: feature[key] for key in FEATURES},
                                     "window_start": feature["window_start"], "window_end": feature["window_end"]})
            status = "retained" if complete >= config["minimum_climate_years"] else "insufficient complete POWER windows"
        coverage.append({"fips": county.fips, "county": county.county, "lat": county.lat, "lon": county.lon,
                         "yield_years": len(records), "non_irrigated_years": int(records.practice.eq("non_irrigated").sum()),
                         "climate_years": complete, "unavailable_windows": missing, "status": status})
    manifest = []
    for job in flat_jobs:
        row = manifest_row(job, climate_raw)
        path = job.path(archives).with_suffix(".json.gz")
        if path.exists():
            row["archive_file"] = str(path.relative_to(raw))
            row["archive_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest.append(row)
    write_json(raw / "power_manifest.json", manifest)
    retained = {row["fips"] for row in coverage if row["status"] == "retained"}
    data = pd.DataFrame((row for row in features if row["fips"] in retained),
                        columns=["fips", "year", "yield_bu_ac", "practice", *FEATURES, "window_start", "window_end"])
    atomic_write(output / "climate_yield_features.csv", lambda path: data.to_csv(path, index=False))
    provenance = {"selection": selection, "coverage": coverage, "selected_yield_rows": len(yields),
                  "eligible_yield_counties": len(eligible), "eligible_yield_rows": int(yields.fips.isin(jobs).sum()),
                  "complete_chunk_count": sum(row["coverage"] == "complete" for row in manifest),
                  "requested_chunk_count": len(manifest), "retained_counties": len(retained), "retained_rows": len(data),
                  "crop": spec["crop"], "onset_month": window["onset_month"], "window_source": window["source"],
                  "start_year_offset": spec["start_year_offset"], "duration_days": crop["season_length_days"],
                  "duration_source": crop["season_length_source"], "water_need_mm": crop["water_need_mm"],
                  "water_need_source": crop["water_need_source"], "heat_threshold_c": crop["heat_tolerance_c"],
                  "heat_source": crop["thermal_source"], "power_fields": dict(zip(POWER_FIELDS, EXPECTED_UNITS, strict=True))}
    write_json(output / "climate_yield_coverage.json", provenance)
    return provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract-bulk", type=Path, help="Exact P20 bulk .gz or its already-filtered TSV")
    parser.add_argument("--centroid-html", type=Path, help="Saved Census TIGERweb Kansas table")
    parser.add_argument("--fetch", action="store_true", help="Resume missing county POWER chunks")
    parser.add_argument("--archive", action="store_true", help="Compress cached responses for versioned evidence")
    args = parser.parse_args()
    conf = json.loads((ROOT / "config/climate_yield.json").read_text())
    raw = ROOT / "data/raw/p25"
    raw.mkdir(parents=True, exist_ok=True)
    if args.extract_bulk:
        extract_bulk(args.extract_bulk, raw / "quickstats_kansas.csv", conf)
    if args.centroid_html:
        centroids = extract_centroids(args.centroid_html)
        if centroids.fips.duplicated().any() or not centroids.fips.str.startswith(conf["state_fips"]).all():
            raise ValueError("Unexpected county geography in Census table")
        centroids.to_csv(raw / "kansas_centroids.csv", index=False)
    report = prepare(fetch=args.fetch, archive=args.archive)
    print({k: v for k, v in report.items() if type(v) is int}, flush=True)


if __name__ == "__main__":
    main()
