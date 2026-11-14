"""Compare archived public yield anomalies with cached farm-point weather."""

import json

import numpy as np
import pandas as pd

from src.backtest import BOOTSTRAP_DRAWS, SEED, rank_interval
from src.crops import load_crops
from src.data_pipeline import POWER_SOURCE, ROOT, atomic_write
from src.nasa_consistency import STRONG_RHO
from src.scoring import daily_water_deficit
from src.validation import POWER_FILL_VALUE

INDICATORS = {"water_deficit_mm": "Modeled water deficit", "heat_days": "Heat days"}


def load_yields(frame, source_format, selector, year_bounds):
    """Extract one series. USDA disclosure codes and missing records stay missing."""
    if source_format == "quickstats":
        selected = frame.loc[frame.SHORT_DESC.eq(selector), ["YEAR", "VALUE"]]
        years = selected.YEAR
        values = selected.VALUE.astype(str).str.replace(",", "", regex=False)
        unit = "bu/acre"
    elif source_format == "icrisat":
        years, values = frame.Year, frame[selector]
        unit = "kg/ha"
    else:
        raise ValueError(f"Unknown yield format {source_format}")
    yields = pd.DataFrame({"year": pd.to_numeric(years, errors="raise"),
                           "yield": pd.to_numeric(values, errors="coerce")})
    yields = yields.loc[yields.year.between(*year_bounds) & np.isfinite(yields["yield"]) & yields["yield"].ge(0)]
    if yields.year.duplicated().any():
        raise ValueError("Duplicate yields within one crop, year and practice")
    return yields.sort_values("year").reset_index(drop=True), unit


def detrend(yields):
    """Fit a separate linear time trend to all available yields in each series."""
    if len(yields) < 3:
        return yields.assign(trend=np.nan, anomaly=np.nan)
    years = yields.year.to_numpy(dtype=float)
    values = yields["yield"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(years - years.mean(), values, 1)
    trend = slope * (years - years.mean()) + intercept
    anomaly = values - trend
    # Avoid spurious ranks from numerical noise in an exactly fitted trend.
    if np.allclose(values, trend, atol=1e-10, rtol=0):
        anomaly = np.zeros_like(values)
    return yields.assign(trend=trend, anomaly=anomaly)


def crop_stress(climate, start, crop, storage, supply):
    dates = pd.date_range(start, periods=crop["season_length_days"])
    sample = climate.reindex(dates).replace([POWER_FILL_VALUE, np.inf, -np.inf], np.nan)
    rain = sample.PRECTOTCORR
    maximum = sample.T2M_MAX
    deficit = None
    if rain.notna().all():
        unmet = daily_water_deficit(rain.to_numpy()[None, :], crop["water_need_mm"], storage)[0]
        deficit = float(unmet * (1 - supply))
    return {"window_start": str(dates[0].date()), "window_end": str(dates[-1].date()),
            "water_deficit_mm": deficit,
            "heat_days": int(maximum.gt(crop["heat_tolerance_c"]).sum()) if maximum.notna().all() else None}


def evaluate(yields, climate, crop, onset, offset, storage, supply):
    rows = []
    for year, value, trend, anomaly in detrend(yields).itertuples(index=False, name=None):
        start = pd.Timestamp(int(year) + offset, onset, 1)
        rows.append({"year": int(year), "yield": float(value),
                     "trend": float(trend) if np.isfinite(trend) else None,
                     "yield_anomaly": float(anomaly) if np.isfinite(anomaly) else None,
                     **crop_stress(climate, start, crop, storage, supply)})
    comparisons = []
    for offset, (indicator, label) in enumerate(INDICATORS.items()):
        stat = rank_interval([row[indicator] for row in rows], [row["yield_anomaly"] for row in rows],
                             seed=SEED + offset)
        rho, interval = stat["rho"], stat["bootstrap_95"]
        finding = "Unavailable"
        if rho is not None:
            if rho > 0:
                finding = "Opposite sign"
            elif rho <= -STRONG_RHO and interval is not None and interval[1] < 0:
                finding = "Strong expected association"
            else:
                finding = "Weak or uncertain expected association"
        comparisons.append({"indicator": label, "field": indicator, "finding": finding, **stat})
    return rows, comparisons


def build(root=ROOT):
    raw = root / "data/raw/p20"
    processed = root / "data/processed"
    config = json.loads((root / "config/yield_backtest.json").read_text())
    farms = json.loads((root / "config/farms.json").read_text())
    crops = load_crops(root / "data/crops.csv", farms=farms)
    year_bounds = (config["start_year"], config["end_year"])
    for farm in farms:
        farm_id = farm["farm_id"]
        site = config["farms"][farm_id]
        result = {key: site[key] for key in ("geography", "note", "source", "source_url")}
        result.update(farm_id=farm_id, year_bounds=year_bounds, series=[], label="illustrative, validate locally",
                      climate_source=POWER_SOURCE, method_source=config["method_source"],
                      bootstrap={"seed": SEED, "draws": BOOTSTRAP_DRAWS, "source": config["method_source"]})
        if site["series"]:
            frame = pd.read_csv(raw / site["file"])
            climate = pd.read_parquet(processed / f"climate_{farm_id}.parquet").set_index("date")
            windows = json.loads((processed / f"seasons_{farm_id}.json").read_text())["season_windows"]
            context = json.loads((processed / f"context_{farm_id}.json").read_text())
            soil = context["soil"]["available_water_mm_0_30"]
            irrigation = farm["irrigation"]
            result.update(soil_storage_mm=soil["value"], soil_source=soil["source"],
                          irrigation_supply_fraction=irrigation["supply_fraction"], irrigation_source=irrigation["basis"],
                          yield_input="data/raw/p20/" + site["file"])
            for spec in site["series"]:
                crop = crops[spec["crop"]]
                window = windows[spec["season"]]
                yields, unit = load_yields(frame, site["format"], spec["selector"], year_bounds)
                rows, comparisons = evaluate(yields, climate, crop, window["onset_month"], spec["start_year_offset"],
                                             soil["value"], irrigation["supply_fraction"])
                result["series"].append({**spec, "crop_name": crop["display_name"], "yield_unit": unit,
                                         "yearly_yield_count": len(rows), "onset_month": window["onset_month"],
                                         "window_source": window["source"], "crop_source": "data/crops.csv",
                                         "season_length_days": crop["season_length_days"],
                                         "season_length_source": crop["season_length_source"],
                                         "water_need_mm": crop["water_need_mm"], "water_need_source": crop["water_need_source"],
                                         "heat_threshold_c": crop["heat_tolerance_c"], "heat_source": crop["thermal_source"],
                                         "rows": rows, "comparisons": comparisons})
        atomic_write(processed / f"yield_backtest_{farm_id}.json",
                     lambda path: path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n"))


if __name__ == "__main__":
    build()
