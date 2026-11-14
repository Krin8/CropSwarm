"""Build P32 yield and POWER features for the two preregistered target states."""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd

from src.county_yield_data import (FEATURES, SELECTORS, archive_responses, county_jobs, extract_centroids,
                                   read_weather, restore_archive, season_features, select_yields)
from src.crops import load_crops
from src.data_pipeline import ROOT, atomic_write, fetch_chunk, manifest_row
from src.precompute_cache import write_json

TARGETS = {"31": "Nebraska", "40": "Oklahoma"}
SOURCE_FIELDS = ("STATE_ANSI", "COUNTY_ANSI", "COUNTY_CODE", "COUNTY_NAME", "ASD_CODE", "ASD_DESC",
                 "YEAR", "VALUE", "SHORT_DESC")
ARCHIVE = ROOT / "data/raw/p32"


def extract_targets(source, destination, config):
    """Stream the same verified NASS snapshot used in P25, retaining district columns."""
    state_codes = {code.encode() for code in TARGETS}
    descriptions = {text.encode() for text in SELECTORS}
    with gzip.open(source, "rb") as handle, destination.open("w", encoding="utf-8", newline="") as out:
        headers = {name.decode("ascii"): i for i, name in enumerate(handle.readline().rstrip().split(b"\t"))}
        indices = {key: headers[key] for key in (*SOURCE_FIELDS, "SOURCE_DESC", "DOMAIN_DESC", "AGG_LEVEL_DESC",
                                                "FREQ_DESC", "REFERENCE_PERIOD_DESC")}
        filters = {"SOURCE_DESC": b"SURVEY", "DOMAIN_DESC": b"TOTAL", "AGG_LEVEL_DESC": b"COUNTY",
                   "FREQ_DESC": b"ANNUAL", "REFERENCE_PERIOD_DESC": b"YEAR"}
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(SOURCE_FIELDS)
        for line in handle:
            fields = line.split(b"\t")
            if (fields[indices["STATE_ANSI"]] in state_codes and fields[indices["SHORT_DESC"]] in descriptions
                    and all(fields[indices[key]] == value for key, value in filters.items())):
                year = fields[indices["YEAR"]]
                if year.isdigit() and config["first_harvest_year"] <= int(year) <= config["last_harvest_year"]:
                    writer.writerow(fields[indices[key]].replace(b"\0", b"").decode("latin-1") for key in SOURCE_FIELDS)


def target_districts(source, yields):
    """Keep one sourced reporting district per real county."""
    mapping = source.assign(fips=source.STATE_ANSI + source.COUNTY_ANSI)
    columns = ["fips", "ASD_CODE", "ASD_DESC"]
    mapping = mapping.loc[mapping.fips.isin(yields.fips), columns].drop_duplicates()
    if (mapping.ASD_CODE.eq("").any() or mapping.ASD_DESC.eq("").any()
            or mapping.fips.duplicated().any() or len(mapping) != yields.fips.nunique()):
        raise ValueError("Unresolved county reporting district in the NASS archive")
    return mapping.rename(columns={"ASD_CODE": "district", "ASD_DESC": "district_name"})


def yield_inventory(source, config):
    """Screen source county identifiers and histories before a geographic join."""
    inventory = {}
    for state, name in TARGETS.items():
        raw = source.loc[source.STATE_ANSI.eq(state)]
        fips = raw.STATE_ANSI + raw.COUNTY_ANSI
        county_ids = pd.DataFrame({"fips": fips.loc[fips.str.fullmatch(r"[0-9]{5}")].unique()})
        yields, selection = select_yields(raw, county_ids, config)
        districts = target_districts(raw, yields)
        years = yields.groupby("fips").size()
        eligible = yields.loc[yields.fips.isin(years[years.ge(config["minimum_yield_years"])].index)]
        eligible_counties = districts.loc[districts.fips.isin(eligible.fips)]
        names = raw.assign(fips=fips).drop_duplicates("fips").set_index("fips").COUNTY_NAME
        excluded = [{"fips": f, "county": names[f], "valid_yield_years": int(n)}
                    for f, n in years[years.lt(config["minimum_yield_years"])].items()]
        inventory[state] = {"name": name, "selection": selection, "counties_with_yield": len(years),
                            "eligible_counties": len(eligible_counties),
                            "eligible_reporting_districts": int(eligible_counties.district.nunique()),
                            "eligible_rows": len(eligible), "first_year": int(eligible.year.min()),
                            "last_year": int(eligible.year.max()),
                            "practice_counts": eligible.practice.value_counts().to_dict(),
                            "excluded_low_coverage": excluded}
    return inventory


def load_centroids(path, state):
    centroids = (extract_centroids(path) if path.suffix == ".html"
                 else pd.read_csv(path, dtype={"fips": str}))
    if (centroids.empty or centroids.fips.duplicated().any()
            or not centroids.fips.str.fullmatch(rf"{state}[0-9]{{3}}").all()
            or not centroids.lat.between(-90, 90).all() or not centroids.lon.between(-180, 180).all()):
        raise ValueError(f"Invalid county centroid table for state {state}")
    return centroids


def prepare_state(source, centroids, config, window, crop, cache, archive, *, fetch=False, save_archive=False):
    identifiers = (source.STATE_ANSI + source.COUNTY_ANSI).loc[source.COUNTY_ANSI.str.fullmatch(r"[0-9]{3}")]
    uncovered = sorted(set(identifiers) - set(centroids.fips))
    if uncovered:
        raise ValueError(f"NASS county IDs missing from the verified centroid file: {uncovered}")
    yields, selection = select_yields(source, centroids, config)
    districts = target_districts(source, yields)
    eligible = yields.groupby("fips").size().loc[lambda years: years.ge(config["minimum_yield_years"])].index
    jobs = {row.fips: list(county_jobs(row, config)) for row in centroids.itertuples(index=False)
            if row.fips in eligible}
    for county_jobs_ in jobs.values():
        for job in county_jobs_:
            restore_archive(job, cache, archive)
    pending = [job for chunks in jobs.values() for job in chunks]
    if fetch:
        with ThreadPoolExecutor(max_workers=config["fetch_workers"]) as pool:
            counts = Counter()
            for result in pool.map(lambda job: fetch_chunk(job, cache), pending):
                counts[result] += 1
                if counts.total() % 20 == 0:
                    print(dict(counts), flush=True)
        print(dict(counts), flush=True)
    if save_archive:
        archive_responses(pending, cache, archive)

    coverage, complete_rows = [], []
    county_yields = {fips: group for fips, group in yields.groupby("fips")}
    for county in centroids.itertuples(index=False):
        records = county_yields.get(county.fips, yields.iloc[:0])
        complete, unavailable = [], []
        status = "fewer than minimum yield years"
        if county.fips in jobs:
            weather = read_weather(jobs[county.fips], cache)
            for row in records.itertuples(index=False):
                f = season_features(weather, row.year, crop, window["onset_month"],
                                    window["year_offset"], config["storage_proxy_mm"])
                if f[FEATURES[0]] is None:
                    unavailable.append({"year": row.year, **f["missing_days"]})
                else:
                    complete.append({**row._asdict(), **{name: f[name] for name in FEATURES},
                                     "window_start": f["window_start"], "window_end": f["window_end"]})
            status = "insufficient complete POWER windows"
            if len(complete) >= config["minimum_climate_years"]:
                status = "retained"
                complete_rows.extend(complete)
        coverage.append({"fips": county.fips, "county": county.county, "lat": county.lat, "lon": county.lon,
                         "yield_years": len(records), "non_irrigated_years": int(records.practice.eq("non_irrigated").sum()),
                         "climate_years": len(complete), "unavailable_windows": unavailable, "status": status})
    manifest = []
    for job in pending:
        row = manifest_row(job, cache)
        compressed = job.path(archive).with_suffix(".json.gz")
        if compressed.is_file():
            row["archive_file"] = str(compressed.relative_to(archive))
            row["archive_sha256"] = hashlib.sha256(compressed.read_bytes()).hexdigest()
        manifest.append(row)
    cols = [*yields.columns, *FEATURES, "window_start", "window_end"]
    data = pd.DataFrame(complete_rows, columns=cols).merge(districts, on="fips", validate="many_to_one")
    return data, {"selection": selection, "selected_yield_rows": len(yields), "yield_counties": len(eligible),
                  "retained_counties": int(data.fips.nunique()), "retained_rows": len(data),
                  "counties": coverage, "complete_chunks": sum(row["coverage"] == "complete" for row in manifest),
                  "requested_chunks": len(manifest)}, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract-bulk", type=Path, help="The original P20 USDA NASS bulk gzip")
    parser.add_argument("--state", choices=tuple(TARGETS))
    parser.add_argument("--centroid-file", type=Path, help="Verified local Census table or centroid CSV for --state")
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--archive", action="store_true")
    parser.add_argument("--yield-inventory", action="store_true", help="Report NASS coverage before the geographic join")
    args = parser.parse_args()
    if args.centroid_file and not args.state:
        parser.error("--centroid-file requires --state")
    config = json.loads((ROOT / "config/climate_yield.json").read_text())
    source = ARCHIVE / "quickstats_targets.csv"
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    if args.extract_bulk:
        provenance = json.loads((ROOT / "data/raw/p27/provenance.json").read_text())
        with args.extract_bulk.open("rb") as handle:
            if hashlib.file_digest(handle, "sha256").hexdigest() != provenance["bulk_sha256"]:
                parser.error("The NASS snapshot does not match the registered P20/P25 file")
        atomic_write(source, lambda path: extract_targets(args.extract_bulk, path, config))
        if not (args.state or args.fetch or args.archive or args.yield_inventory):
            return
    rows = pd.read_csv(source, dtype=str, keep_default_na=False)
    if args.yield_inventory:
        write_json(ROOT / "data/processed/climate_yield_transfer_yield_inventory.json", yield_inventory(rows, config))
        return
    p20 = json.loads((ROOT / "config/yield_backtest.json").read_text())
    spec = p20["farms"]["us_high_plains_b"]["series"][0]
    calendar = json.loads((ROOT / "data/processed/seasons_us_high_plains_b.json").read_text())
    window = {**calendar["season_windows"][spec["season"]], "year_offset": spec["start_year_offset"]}
    crop = load_crops(ROOT / "data/crops.csv")[spec["crop"]]
    for state in (args.state,) if args.state else TARGETS:
        print(f"Preparing {TARGETS[state]}", flush=True)
        path = args.centroid_file or ARCHIVE / f"census_{state}_counties.html"
        if not path.is_file():
            parser.error(f"Missing verified county centroid table for {TARGETS[state]}: {path.name}")
        centroids = load_centroids(path, state)
        out, coverage, manifest = prepare_state(rows[rows.STATE_ANSI.eq(state)], centroids, config, window, crop,
                                               ARCHIVE / "power", ARCHIVE / "power_archive",
                                               fetch=args.fetch, save_archive=args.archive)
        atomic_write(ROOT / "data/processed" / f"climate_yield_transfer_{state}_features.csv",
                     lambda path: out.to_csv(path, index=False))
        write_json(ROOT / "data/processed" / f"climate_yield_transfer_{state}_coverage.json", coverage)
        write_json(ARCHIVE / f"power_{state}_manifest.json", manifest)
        print({k: v for k, v in coverage.items() if type(v) is int}, flush=True)


if __name__ == "__main__":
    main()
