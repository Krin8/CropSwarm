"""CropSwarm's deterministic, vectorised comparison model."""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.crops import load_crops

ROOT = Path(__file__).resolve().parents[1]
METRICS = ("water", "nitrogen", "erosion", "climate_fit", "income", "risk")
UNITS = ("mm unmet per slot", "kg N/ha per slot", "slope × rainfall proxy", "historical share",
         "relative index", "relative penalty")
SOURCES = ("NASA POWER · soil available water · crop catalog", "Crop catalog · local assumptions",
           "NASA SRTM · NASA POWER · crop cover assumptions", "NASA POWER · crop catalog",
           "Crop catalog · illustrative economic assumptions", "Crop catalog · disease family and cover assumptions")
EXPLANATIONS = (
    "Lower unmet crop water demand after a daily soil-water bucket and assumed irrigation.",
    "The previous crop's carryover credit offsets the current crop's assumed nitrogen demand.",
    "Lower slope, lower daily rainfall intensity or more cover reduces a simplified RUSLE-style index.",
    "Share of complete historical crop windows meeting the crop's temperature, rainfall and heat screens.",
    "The catalog's relative income index is a scenario input. It gives no price or yield forecast.",
    "Consecutive crops in the same family and uncovered fallow raise the risk proxy.",
)


@dataclass
class Model:
    farm: dict
    crops: dict
    season_labels: list
    policy: dict
    days: dict
    storage: float
    slope: float
    soil_source: str
    ids: list
    planting_windows: np.ndarray
    suitable: np.ndarray
    histories: dict
    additions: np.ndarray
    credits: np.ndarray
    demand: np.ndarray
    family: np.ndarray
    bare: np.ndarray
    nitrogen_bounds: tuple
    erosion_max: float


def crop_windows(climate, onset, length):
    starts = pd.to_datetime({"year": sorted(set(climate.index.year)), "month": onset, "day": 1})
    offsets = starts.to_numpy(dtype="datetime64[D]")[:, None] + np.arange(length).astype("timedelta64[D]")
    columns = ["PRECTOTCORR", "T2M", "T2M_MAX"]
    values = climate.reindex(pd.DatetimeIndex(offsets.ravel()))[columns].to_numpy().reshape(len(starts), length, 3)
    complete = np.isfinite(values).all(axis=(1, 2))
    return {int(year): sample for year, sample in zip(starts.dt.year[complete], values[complete], strict=True)}


def daily_water_deficit(rain, demand, storage):
    """Apply retained daily rainfall to daily crop demand, carrying remaining water forward."""
    if rain.shape[1] == 0 or demand == 0:
        return np.zeros(len(rain))
    daily_demand = demand / rain.shape[1]
    remaining = np.zeros(len(rain))
    unmet = np.zeros(len(rain))
    for day in rain.T:
        incoming = remaining + day
        unmet += np.maximum(daily_demand - incoming, 0)
        remaining = np.minimum(storage, np.maximum(incoming - daily_demand, 0))
    return unmet


def historical_metrics(windows, crop, storage, slope, supply, policy, *, water_factor=1,
                       heat_shift=0, rain_factor=1, years=None, need_factor=1):
    if not windows:
        return np.empty((0, 5))
    samples = np.array(list(windows.values()) if years is None else [windows[int(y)] for y in years])
    if crop["season_length_days"] == 0:
        result = np.tile([0., 0., 0., 1., 0.], (len(samples), 1))
        result[:, 2] = slope * rain_factor * samples[:, :, 0].max(axis=1)
        return result
    rain, mean_temp, daily_high = np.moveaxis(samples, -1, 0)
    rain = rain * rain_factor
    water = crop["water_need_mm"] * water_factor * need_factor
    deficit = daily_water_deficit(rain, water, storage) * (1 - supply)
    annual_rain = rain.sum(axis=1)
    mean_temp = mean_temp.mean(axis=1) + heat_shift
    hot_fraction = (daily_high + heat_shift > crop["heat_tolerance_c"]).mean(axis=1)
    climate_fit = ((annual_rain >= crop["min_rain_mm"]) & (annual_rain <= crop["max_rain_mm"]) &
                   (mean_temp >= crop["min_temp_c"]) & (mean_temp <= crop["max_temp_c"]) &
                   (hot_fraction <= policy["max_hot_day_fraction"]))
    peak_rain = rain.max(axis=1)
    erosion = slope * peak_rain * (1 - crop["cover_score"])
    return np.column_stack([deficit, deficit / water, erosion, climate_fit,
                            np.full(len(deficit), crop["relative_income_index"])])


def preload(farm, *, root=ROOT, processed=None, crops=None, policy=None, storage_override=None):
    out = Path(processed) if processed else root / "data/processed"
    context = json.loads((out / f"context_{farm['farm_id']}.json").read_text())
    seasons = json.loads((out / f"seasons_{farm['farm_id']}.json").read_text())
    if len(seasons["slots"]) != farm["seasons_per_year"]:
        raise ValueError(f"Season-slot disagreement for {farm['farm_id']}")
    climate = pd.read_parquet(out / f"climate_{farm['farm_id']}.parquet").set_index("date")
    if crops is None:
        crops = load_crops(root / "data/crops.csv", farms=[farm])
    if policy is None:
        policy = json.loads((root / "config/scoring.json").read_text())
    water_capacity = context["soil"]["available_water_mm_0_30"]
    storage = water_capacity["value"] if storage_override is None else storage_override
    slope = context["terrain"]["mean_slope_pct"]["value"]
    if storage is None or slope is None:
        raise ValueError(f"Missing soil-water capacity or slope for {farm['farm_id']}")
    labels = [slot["eligible_labels"] for slot in seasons["slots"]]
    ids = list(crops)
    planting_windows = np.zeros((len(labels), len(ids)), dtype=bool)
    suitability = planting_windows.copy()
    additions = np.zeros((*planting_windows.shape, 5))
    histories = {}
    days = {}
    # Fallow erosion uses peak rainfall in the reference season so uncovered soil still has erosion risk.
    for slot, options in enumerate(labels):
        for index, crop in enumerate(crops.values()):
            label = next((label for label in options if label in crop["seasons_allowed"]), options[0])
            window = seasons["season_windows"][label]
            start, end = window["onset_month"], window["cessation_month"]
            length = (pd.Timestamp(2001 + (end < start or end == 12), end % 12 + 1, 1) -
                      pd.Timestamp(2001, start, 1)).days
            allowed = label in crop["seasons_allowed"] and crop["season_length_days"] <= (
                length + policy["calendar_extension_days"])
            days[slot, index] = (label, start, crop["season_length_days"])
            search_length = crop["season_length_days"] or length
            windows = crop_windows(climate, start, search_length)
            histories[slot, index] = windows
            hist = historical_metrics(windows, crop, storage, slope, farm["irrigation"]["supply_fraction"], policy)
            if len(hist) == 0:
                continue
            planting_windows[slot, index] = allowed
            additions[slot, index] = hist.mean(axis=0)
            suitability[slot, index] = allowed and np.median(hist[:, 1]) <= policy["max_median_unmet_water_fraction"]
    credits = np.array([crop["n_credit_kg_ha"] for crop in crops.values()])
    demand = np.array([crop["n_demand_kg_ha"] for crop in crops.values()])
    families = sorted({crop["disease_family"] for crop in crops.values()})
    family = np.array([families.index(crop["disease_family"]) for crop in crops.values()])
    bare = np.array([crop["season_length_days"] == 0 for crop in crops.values()])
    bounds = (-float(demand.max()), float(credits.max()))
    soil_source = water_capacity["source"] if storage_override is None else "Farmer input · assumption, validate locally"
    return Model(farm, crops, labels, policy, days, storage, slope, soil_source, ids, planting_windows,
                 suitability, histories, additions, credits, demand, family, bare, bounds,
                 slope * float(climate.PRECTOTCORR.max()))


def score_rotations(model, rotations, *, additions=None, credits=None, demand=None):
    rotations = np.atleast_2d(np.asarray(rotations, dtype=int))
    if rotations.shape[1] % len(model.season_labels):
        raise ValueError("Rotations must have a whole number of years")
    slots = np.arange(rotations.shape[1]) % len(model.season_labels)
    previous = np.roll(rotations, 1, axis=1)
    allowed = model.planting_windows[slots, rotations]
    warnings = {"season_feasibility": ~allowed,
                "irrigation_shortfall": allowed & ~model.suitable[slots, rotations],
                "identical_consecutive_crop": (rotations == previous) if rotations.shape[1] > 1
                else np.zeros_like(rotations, dtype=bool)}
    values = (model.additions if additions is None else additions)[slots, rotations].mean(axis=1)
    nitrogen = ((model.credits if credits is None else credits)[previous] -
                (model.demand if demand is None else demand)[rotations]).mean(axis=1)
    bare = model.bare[rotations]
    shared_family = (model.family[rotations] == model.family[previous]) & ~bare & ~model.bare[previous]
    risk = (model.policy["same_family_risk_share"] * shared_family.mean(axis=1) +
            model.policy["bare_slot_risk_share"] * bare.mean(axis=1))
    raw = np.column_stack([values[:, 0], nitrogen, values[:, 2], values[:, 3], values[:, 4], risk])
    lower, upper = model.nitrogen_bounds
    scores = np.column_stack([1-values[:, 1], (nitrogen-lower)/(upper-lower),
                              1-values[:, 2]/model.erosion_max if model.erosion_max else np.ones(len(rotations)),
                              values[:, 3], values[:, 4], 1-risk])
    return raw, np.clip(scores, 0, 1), warnings


def metric_rows(raw, scores):
    return {metric: {"value": float(value), "unit": unit, "score": float(score), "source": source,
                     "explanation": explanation}
            for metric, value, score, unit, source, explanation in
            zip(METRICS, raw, scores, UNITS, SOURCES, EXPLANATIONS, strict=True)}


def baseline_indices(model, years=None):
    baseline = model.farm["baseline_rotation_cycle"]
    years = len(baseline) if years is None else years
    return np.array([model.ids.index(crop) for year in range(years)
                     for crop in baseline[year % len(baseline)]], dtype=int)
