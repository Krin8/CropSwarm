"""Apply the preregistered P31 archive screen before any weather retrieval or fitting."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

import numpy as np
import pandas as pd

from src.precompute_cache import write_json

ROOT = Path(__file__).resolve().parents[1]
MAP_MEMBER = "India_DI_sh_1993_F.dbf"
MAP_KEYS = ["map_code", "feature_id"]
IDENTITY = [*MAP_KEYS, "source_code", "state", "district"]
ARCHIVE_COLUMNS = {
    "Crops": "crop", "Sh_Dist_code": "map_code", "FID_1": "feature_id", "Dist.Code": "source_code",
    "State": "state", "District": "district", "Year": "year", "RICE.YIELD..Kg.per.ha.": "yield_kg_ha",
}
# This describes the one series documented in the cached deposit. Its listed files
# do not document a comparable crop irrigation share or a rainfed-dominant series.
CROPS = {"Rice": {"season": "kharif", "irrigation_share": None, "rainfed_dominance_documented": False}}


def historic_mapping(dbf):
    """Read the archived dBASE polygon attributes using its fixed record layout."""
    count, start, stride = struct.unpack_from("<IHH", dbf, 4)
    fields = {}
    offset = 1  # the first byte is the deletion flag
    for index in range(32, start - 1, 32):
        name = dbf[index:index + 11].rstrip(b"\0").decode("ascii")
        width = dbf[index + 16]
        fields[name] = slice(offset, offset + width)
        offset += width
    if offset != stride or len(dbf) < start + count * stride:
        raise ValueError("Invalid archive map attribute layout")
    columns = {"map_code": "IPUM1993", "feature_id": "FID_1", "state": "State", "district": "District"}
    rows = []
    for start_row in range(start, start + count * stride, stride):
        row = dbf[start_row:start_row + stride]
        if row[0:1] == b"*":
            continue
        entry = {key: row[fields[col]].decode("utf-8").strip() for key, col in columns.items()}
        entry["map_code"] = int(entry["map_code"])
        entry["feature_id"] = int(entry["feature_id"])
        rows.append(entry)
    return pd.DataFrame(rows, columns=list(columns))


def district_coverage(raw, mapping, first_year, last_year, minimum_years):
    """Screen historical district IDs and exclude conflicting district-year yields."""
    raw = raw.loc[raw["year"].between(first_year, last_year)].copy()
    if raw.empty:
        raise ValueError("No district-year rows in the archive period")
    mapping = mapping.rename(columns={"state": "map_state", "district": "map_district"})
    merged = raw.merge(mapping, how="left", on=MAP_KEYS, validate="many_to_one", indicator=True)
    output = []
    for identity, district in merged.groupby(["crop", *IDENTITY], sort=True):
        crop, *key = identity
        valid = district[np.isfinite(district["yield_kg_ha"]) & district["yield_kg_ha"].gt(0)]
        distinct = valid.groupby("year")["yield_kg_ha"].nunique()
        conflicts = [int(year) for year in distinct[distinct.gt(1)].index]
        usable = distinct.eq(1).sum()
        joined = district["_merge"].eq("both").all()
        consistent = (joined and district["state"].eq(district["map_state"]).all()
                      and district["district"].eq(district["map_district"]).all())
        if not joined:
            status = "excluded_missing_polygon"
        elif not consistent:
            status = "excluded_inconsistent_polygon_metadata"
        elif usable < minimum_years:
            status = "excluded_fewer_than_minimum_yield_years"
        else:
            status = "meets_yield_and_geography_gate"
        output.append({"crop": crop, **dict(zip(IDENTITY, key, strict=True)), "raw_years": int(district["year"].nunique()),
                       "valid_yield_years": int(usable), "conflicting_years": conflicts, "status": status})
    return output


def archive_screen(raw, mapping, *, first_year, last_year, minimum_years, minimum_districts, crops=CROPS):
    """Return candidate evidence and the preregistered disposition, without fetching weather."""
    if set(raw["crop"]) != set(crops):
        raise ValueError("Candidate metadata must account for every archived crop")
    coverage = district_coverage(raw, mapping, first_year, last_year, minimum_years)
    candidates = []
    for crop, metadata in crops.items():
        rows = [row for row in coverage if row["crop"] == crop]
        passed = [row for row in rows if row["status"] == "meets_yield_and_geography_gate"]
        years = raw.loc[raw["crop"].eq(crop) & raw["year"].between(first_year, last_year), "year"]
        candidates.append({"crop": crop, **metadata, "districts_in_archive": len(rows),
                           "districts_meeting_yield_and_geography": len(passed),
                           "district_years_meeting_yield_and_geography": sum(r["valid_yield_years"] for r in passed),
                           "states_meeting_yield_and_geography": len({r["state"] for r in passed}),
                           "first_yield_year": int(years.min()), "last_yield_year": int(years.max()),
                           "passes_yield_and_geography_gate": len(passed) >= minimum_districts,
                           "passes_irrigation_gate": metadata["irrigation_share"] is not None
                           or metadata["rainfed_dominance_documented"]})
    eligible = [row for row in candidates if row["passes_yield_and_geography_gate"] and row["season"] == "kharif"]
    with_shares = [row for row in eligible if row["irrigation_share"] is not None]
    supported = with_shares or [row for row in eligible if row["rainfed_dominance_documented"]]
    chosen = min(supported, key=lambda row: (row["irrigation_share"] or 0, row["crop"]), default=None)
    return {"selected_crop": chosen["crop"] if chosen else None, "candidates": candidates,
            "district_coverage": coverage}


def build(root=ROOT):
    archive = root / "data/raw/p31"
    record = json.loads((archive / "record.json").read_text())
    provenance = json.loads((root / "data/raw/p20/provenance.json").read_text())["icrisat_warangal.csv"]
    config = json.loads((root / "config/climate_yield.json").read_text())
    hashes = {}
    for name, key in (("Data.csv", "data_sha256"), ("Shapefile.rar", "district_map_sha256")):
        digest = hashlib.sha256((archive / name).read_bytes()).hexdigest()
        if digest != provenance[key]:
            raise ValueError(f"P20 archive hash mismatch for {name}")
        hashes[name] = digest
    members = [item["key"] for item in record["files"]]
    if set(members) != set(hashes):
        raise ValueError("The archive inventory changed")
    attrs = subprocess.run(["bsdtar", "-xOf", str(archive / "Shapefile.rar"), MAP_MEMBER], check=True,
                           capture_output=True, timeout=30).stdout
    archived_rows = pd.read_csv(archive / "Data.csv", encoding="cp1252")
    raw = archived_rows[list(ARCHIVE_COLUMNS)].rename(columns=ARCHIVE_COLUMNS)
    report = archive_screen(raw, historic_mapping(attrs), first_year=config["first_harvest_year"],
                            last_year=config["last_harvest_year"], minimum_years=config["minimum_yield_years"],
                            minimum_districts=50)
    if report["selected_crop"] is not None:
        raise RuntimeError("P31's archived screening disposition changed")
    return {**report, "status": "stopped_at_crop_selection_gate",
            "reason": "The archived kharif rice series has no comparable irrigated-area share or documented "
                      "rainfed dominance.",
            "power_requests": 0, "india_model_fits": 0,
            "transfer": "Skipped. The sole archived candidate is monsoon rice. The Kansas study uses winter wheat "
                        "and a different season window.",
            "source": provenance["archive"], "license": record["metadata"]["license"]["id"],
            "archive_members": members, "sha256": hashes, "map_member": MAP_MEMBER,
            "source_columns": list(archived_rows.columns)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/climate_yield_india_screen.json")
    args = parser.parse_args()
    write_json(args.output, build())
