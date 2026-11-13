"""Load and validate the offline CropSwarm crop knowledge base."""

from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from typing import Any

HEADER_NOTE = "# illustrative; validate locally"
SEASON_LABELS = frozenset({"cool", "warm", "monsoon", "post_monsoon", "long_rains", "short_rains"})
ROOT_DEPTH_CLASSES = frozenset({"none", "shallow", "medium", "deep"})
REQUIRED_CROPS = frozenset({"fallow", "winter_wheat", "sorghum", "paddy", "maize", "common_bean"})
CROP_ID = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*")
CLIMATE_FIELDS = ("heat_tolerance_c", "min_temp_c", "max_temp_c", "min_rain_mm", "max_rain_mm")
SCORE_FIELDS = ("cover_score", "relative_income_index")
DEMAND_FIELDS = ("water_need_mm", "n_credit_kg_ha", "n_demand_kg_ha")
SOURCE_FIELDS = (
    "seasons_source", "season_length_source", "water_need_source", "thermal_source",
    "rain_source", "is_legume_source", "n_credit_source", "n_demand_source", "cover_source",
    "root_depth_source", "income_source", "disease_family_source",
)
REQUIRED_COLUMNS = frozenset({
    "crop_id", "display_name", "seasons_allowed", "season_length_days", "is_legume",
    "root_depth_class", "disease_family", "notes", *CLIMATE_FIELDS, *SCORE_FIELDS,
    *DEMAND_FIELDS, *SOURCE_FIELDS,
})


def _finite_number(raw: str, field: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{field} must be a finite number") from exc
    if not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    return value


def _parse_row(row: dict[str, str], crop_id: str) -> dict[str, Any]:
    if not CROP_ID.fullmatch(crop_id):
        raise ValueError("crop_id must be snake_case")
    for field in (*SOURCE_FIELDS, "display_name", "notes"):
        if not row[field]:
            raise ValueError(f"{field} is required")
    seasons = json.loads(row["seasons_allowed"])
    if (not isinstance(seasons, list) or not seasons
            or any(not isinstance(season, str) or season not in SEASON_LABELS for season in seasons)
            or len(set(seasons)) != len(seasons)):
        raise ValueError("seasons_allowed must be a nonempty JSON array of unique season labels")
    if row["root_depth_class"] not in ROOT_DEPTH_CLASSES:
        raise ValueError("invalid root_depth_class")
    if not CROP_ID.fullmatch(row["disease_family"]):
        raise ValueError("disease_family must be snake_case")
    if row["is_legume"] not in {"true", "false"}:
        raise ValueError("is_legume must be true or false")
    length = int(row["season_length_days"])
    numbers = {field: _finite_number(row[field], field) for field in (*SCORE_FIELDS, *DEMAND_FIELDS)}
    for field in SCORE_FIELDS:
        if not 0 <= numbers[field] <= 1:
            raise ValueError(f"{field} must be between 0 and 1")
    for field in DEMAND_FIELDS:
        if numbers[field] < 0:
            raise ValueError(f"{field} must be nonnegative")
    if crop_id == "fallow":
        if set(seasons) != SEASON_LABELS or length != 0 or any(numbers.values()):
            raise ValueError("bare fallow must allow every season and use zero crop inputs and scores")
        if any(row[field] for field in CLIMATE_FIELDS) or row["root_depth_class"] != "none":
            raise ValueError("bare fallow has no crop climate thresholds or root depth")
        climate = dict.fromkeys(CLIMATE_FIELDS)
    else:
        if length <= 0 or row["root_depth_class"] == "none":
            raise ValueError("a planted crop needs positive duration and a root depth class")
        climate = {field: _finite_number(row[field], field) for field in CLIMATE_FIELDS}
        if climate["min_temp_c"] > climate["max_temp_c"]:
            raise ValueError("temperature bounds are reversed")
        if not 0 <= climate["min_rain_mm"] <= climate["max_rain_mm"]:
            raise ValueError("rainfall bounds must be nonnegative and ordered")
    return {
        **row, **numbers, **climate, "seasons_allowed": seasons,
        "season_length_days": length, "is_legume": row["is_legume"] == "true",
    }


def load_crops(path: str | Path, *, farms: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    """Validate the CSV and return typed records indexed by crop ID.

    Pass validated farm configurations to check baseline crop membership.
    """
    crops = {}
    with Path(path).open(encoding="utf-8", newline="") as source:
        if source.readline().strip() != HEADER_NOTE:
            raise ValueError(f"crop table must start with {HEADER_NOTE!r}")
        reader = csv.DictReader(source)
        columns = reader.fieldnames or []
        missing_columns = REQUIRED_COLUMNS.difference(columns)
        if missing_columns or len(columns) != len(set(columns)):
            raise ValueError(f"invalid crop table columns, missing {sorted(missing_columns)}")
        for line, raw_row in enumerate(reader, start=3):
            if None in raw_row or any(value is None for value in raw_row.values()):
                raise ValueError(f"malformed crop row on line {line}")
            row = {field: value.strip() for field, value in raw_row.items()}
            crop_id = row["crop_id"]
            if crop_id in crops:
                raise ValueError(f"duplicate crop_id: {crop_id}")
            try:
                crops[crop_id] = _parse_row(row, crop_id)
            except ValueError as exc:
                raise ValueError(f"crop {crop_id!r} on line {line}: {exc}") from exc
    if not 14 <= len(crops) <= 16:
        raise ValueError("crop table must contain 14 to 16 rows")
    if missing_crops := REQUIRED_CROPS.difference(crops):
        raise ValueError(f"required crop IDs missing: {sorted(missing_crops)}")
    for farm in farms or []:
        missing = {crop for year in farm["baseline_rotation_cycle"] for crop in year}.difference(crops)
        if missing:
            raise ValueError(f"farm {farm['farm_id']} has unknown baseline crop IDs: {sorted(missing)}")
    return crops
