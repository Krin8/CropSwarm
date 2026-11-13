"""Validation for sourced, illustrative CropSwarm configuration."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

POWER_FILL_VALUE = -999
ESTIMATE_SOURCE = "expert estimate, validate locally"
FARM_FIELDS = {"farm_id", "name", "lat", "lon", "region", "tier", "label",
               "irrigation", "baseline_rotation_cycle", "baseline_source",
               "seasons_per_year", "seasons_basis", "coordinate_source",
               "validation_flags", "evidence_refs"}
WEIGHT_KEYS = {"water", "nitrogen", "erosion", "climate_fit", "income", "risk"}


def clean_power_value(value: float | int | None) -> float | None:
    if value is None or value == POWER_FILL_VALUE:
        return None
    return float(value)


def validate_metric(metric: dict[str, Any]) -> None:
    required = {"value", "unit", "source", "illustrative"}
    if not isinstance(metric, dict) or required - metric.keys():
        raise ValueError("metric missing value, unit, source, or illustrative label")
    if not isinstance(metric["value"], (int, float)) or isinstance(metric["value"], bool):
        raise ValueError("metric value must be numeric")
    if not isinstance(metric["source"], str) or not metric["source"].strip():
        raise ValueError("metric source must be nonempty")
    if metric["illustrative"] is not True:
        raise ValueError("metric must be labelled illustrative")


def _source(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} needs a source or assumption label")


def validate_farm(farm: dict[str, Any]) -> None:
    if not isinstance(farm, dict) or FARM_FIELDS - farm.keys():
        raise ValueError(f"farm missing required fields: {sorted(FARM_FIELDS - farm.keys()) if isinstance(farm, dict) else 'object'}")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", farm["farm_id"]):
        raise ValueError("farm_id must be snake_case")
    for field in ("name", "region"):
        if not isinstance(farm[field], str) or not farm[field].strip():
            raise ValueError(f"{field} must be nonempty")
    if farm["label"] != "illustrative representative farm":
        raise ValueError("farm must be labelled illustrative representative farm")
    if not isinstance(farm["lat"], (int, float)) or not -90 <= farm["lat"] <= 90:
        raise ValueError("lat out of range")
    if not isinstance(farm["lon"], (int, float)) or not -180 <= farm["lon"] <= 180:
        raise ValueError("lon out of range")
    if farm["tier"] not in (1, 2):
        raise ValueError("tier must be 1 or 2")
    for field in ("baseline_source", "seasons_basis", "coordinate_source"):
        _source(farm[field], field)
    irrigation = farm["irrigation"]
    if not isinstance(irrigation, dict) or {"supply_fraction", "basis"} - irrigation.keys():
        raise ValueError("irrigation needs supply_fraction and basis")
    fraction = irrigation["supply_fraction"]
    if not isinstance(fraction, (int, float)) or isinstance(fraction, bool) or not math.isfinite(fraction) or not 0 <= fraction <= 1:
        raise ValueError("supply_fraction must be between 0 and 1")
    _source(irrigation["basis"], "irrigation.basis")
    cycle = farm["baseline_rotation_cycle"]
    if not isinstance(cycle, list) or not cycle:
        raise ValueError("baseline_rotation_cycle needs years")
    if not isinstance(farm["seasons_per_year"], int) or farm["seasons_per_year"] < 1:
        raise ValueError("seasons_per_year must be positive integer")
    for year in cycle:
        if not isinstance(year, list) or len(year) != farm["seasons_per_year"]:
            raise ValueError("each year must have seasons_per_year crop IDs")
        if any(not isinstance(crop, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", crop) for crop in year):
            raise ValueError("crop IDs must be snake_case")
    if not isinstance(farm["validation_flags"], list):
        raise ValueError("validation_flags must be a list")
    if not isinstance(farm["evidence_refs"], list) or not farm["evidence_refs"]:
        raise ValueError("evidence_refs must be a nonempty list")


def validate_farms(farms: list[dict[str, Any]]) -> None:
    if not isinstance(farms, list) or len(farms) != 3:
        raise ValueError("exactly three farms required")
    for farm in farms:
        validate_farm(farm)
    if len({farm["farm_id"] for farm in farms}) != len(farms):
        raise ValueError("farm_id must be unique")


def validate_weight_presets(data: dict[str, Any]) -> None:
    if not isinstance(data, dict) or data.get("label") != "design choice, not empirical":
        raise ValueError("weights need design choice, not empirical label")
    presets = data.get("presets")
    if not isinstance(presets, dict) or set(presets) != {"water_saver", "soil_builder", "income", "balanced"}:
        raise ValueError("four named presets required")
    for name, weights in presets.items():
        if not isinstance(weights, dict) or set(weights) != WEIGHT_KEYS:
            raise ValueError(f"{name} needs all six weights")
        if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v < 0 for v in weights.values()):
            raise ValueError(f"{name} has invalid weight")
        if not math.isclose(sum(weights.values()), 1.0, rel_tol=0, abs_tol=1e-6):
            raise ValueError(f"{name} weights must sum to 1")


def load_and_validate(path: str | Path, kind: str) -> Any:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if kind == "farms":
        validate_farms(data)
    elif kind == "weights":
        validate_weight_presets(data)
    else:
        raise ValueError("kind must be farms or weights")
    return data
