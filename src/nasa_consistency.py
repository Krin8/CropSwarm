"""Crop-agnostic comparison of cached POWER weather and MODIS vegetation."""

import json

import numpy as np
import pandas as pd

from src.backtest import BOOTSTRAP_DRAWS, SEED, quality_ndvi, rank_interval
from src.data_pipeline import (LONG_MODIS_YEARS, MODIS_SOURCE, POWER_SOURCE, ROOT, atomic_write,
                               modis_chunks, modis_codes, modis_day)
from src.validation import POWER_FILL_VALUE

REFERENCE_YEARS = range(1991, 2021)
HEAT_QUANTILE = 0.90
MIN_GOOD_COMPOSITES = 3  # Existing P15 QA screen.
MIN_GOOD_DAY_SHARE = 0.50
STRONG_RHO = 0.60
DESIGN_SOURCE = "design choice, not empirical; illustrative, validate locally"
DRIVERS = {"rainfall anomaly": ("rainfall_anomaly_mm", 1),
           "rainfall deficit": ("rainfall_deficit_mm", -1), "heat days": ("heat_days", -1)}
RESPONSES = {"integrated NDVI": "integrated_ndvi_days", "peak NDVI": "peak_ndvi"}


def season_days(year, window):
    start, last = window["onset_month"], window["cessation_month"]
    first_day = pd.Timestamp(year, start, 1)
    end_year = year + int(last < start)
    return pd.date_range(first_day, pd.Timestamp(end_year, last, 1) + pd.offsets.MonthEnd())


def weather_window(climate, days):
    sample = climate.reindex(days)
    rain = sample["PRECTOTCORR"]
    heat = sample["T2M_MAX"]
    return (float(rain.sum()) if rain.notna().all() else None,
            heat if heat.notna().all() else None)


def reference_weather(climate, window, years):
    samples = [weather_window(climate, season_days(year, window)) for year in years]
    rain = [value for value, _ in samples if value is not None]
    heat = [values for _, values in samples if values is not None]
    return {"rainfall_mean_mm": float(np.mean(rain)) if rain else None,
            "heat_threshold_c": float(pd.concat(heat).quantile(HEAT_QUANTILE)) if heat else None,
            "rainfall_reference_seasons": len(rain), "heat_reference_seasons": len(heat),
            "source": POWER_SOURCE}


def composite_spans(farm, years):
    starts = sorted({pd.Timestamp(modis_day(code)) for job in modis_chunks(farm, years)
                     for code in modis_codes(job)})
    return {start: min(start + pd.Timedelta(days=16), pd.Timestamp(start.year + 1, 1, 1))
            for start in starts}


def vegetation_window(days, spans, raw, good):
    start, stop = days[0], days[-1] + pd.Timedelta(days=1)
    weights = {date: (min(stop, end) - max(start, date)).days
               for date, end in spans.items() if date < stop and end > start}
    raw_count = sum(date in raw for date in weights)
    good_weights = {date: weight for date, weight in weights.items() if date in good}
    good_days = sum(good_weights.values())
    complete = bool(weights) and sum(weights.values()) == len(days) and raw_count == len(weights)
    enough = complete and len(good_weights) >= MIN_GOOD_COMPOSITES and good_days >= MIN_GOOD_DAY_SHARE * len(days)
    # Scale the observed day-weighted mean to the season length. Unobserved days supply no values.
    integral = (sum(good[date] * weight for date, weight in good_weights.items()) / good_days * len(days)
                if enough else None)
    return {"expected_composites": len(weights), "valid_ndvi_composites": raw_count,
            "qa_composites": len(good_weights), "qa_days": good_days, "record_complete": complete,
            "integrated_ndvi_days": integral,
            "peak_ndvi": max(good[date] for date in good_weights) if enough else None}


def compare(rows, driver, response, expected_sign, seed):
    pairs = [(row[driver], row[response]) for row in rows
             if row[driver] is not None and row[response] is not None]
    xs, ys = zip(*pairs) if pairs else ([], [])
    stat = rank_interval(xs, ys, seed=seed)
    assessable = consistent = 0
    if stat["n"] >= 3:
        x, y = np.asarray(xs), np.asarray(ys)
        direction = np.sign(x - np.median(x)) * np.sign(y - np.median(y))
        assessable = int(np.count_nonzero(direction))
        consistent = int(np.count_nonzero(direction == expected_sign))
    rho, interval = stat["rho"], stat["bootstrap_95"]
    if rho is None:
        finding = "unavailable"
    elif rho * expected_sign < 0:
        finding = "opposite sign"
    elif (rho * expected_sign >= STRONG_RHO and interval is not None and
          all(endpoint * expected_sign > 0 for endpoint in interval)):
        finding = "strong expected association"
    else:
        finding = "weak or uncertain expected association"
    return {**stat, "expected_sign": expected_sign, "finding": finding,
            "consistent": consistent, "assessable": assessable}


def compute(farm, windows, climate, ndvi, *, years=LONG_MODIS_YEARS, reference_years=REFERENCE_YEARS):
    years, reference_years = tuple(years), tuple(reference_years)
    climate = climate.assign(date=pd.to_datetime(climate.date)).set_index("date")
    climate = climate[["PRECTOTCORR", "T2M_MAX"]].replace([POWER_FILL_VALUE, np.inf, -np.inf], np.nan)
    ndvi = ndvi.assign(date=pd.to_datetime(ndvi.date))
    raw = set(ndvi.loc[ndvi.ndvi.between(-0.2, 1), "date"])
    good = quality_ndvi(ndvi).set_index("date").ndvi.to_dict()
    spans = composite_spans(farm, years)
    coverage = []
    for year in years:
        dates = [day for day in spans if day.year == year]
        missing = [str(day.date()) for day in dates if day not in raw]
        coverage.append({"year": year, "expected": len(dates), "valid_ndvi": len(dates) - len(missing),
                         "qa_accepted": sum(day in good for day in dates), "missing_dates": missing,
                         "status": "incomplete" if missing else "complete", "source": MODIS_SOURCE})
    seasons = {}
    for index, (name, window) in enumerate(windows.items()):
        reference = reference_weather(climate, window, reference_years)
        rows = []
        for year in years:
            days = season_days(year, window)
            rainfall, heat = weather_window(climate, days)
            mean_rain, heat_threshold = reference["rainfall_mean_mm"], reference["heat_threshold_c"]
            anomaly = rainfall - mean_rain if rainfall is not None and mean_rain is not None else None
            rows.append({"start_year": year, "start": str(days[0].date()), "end": str(days[-1].date()),
                         "season_days": len(days), "rainfall_mm": rainfall, "rainfall_anomaly_mm": anomaly,
                         "rainfall_deficit_mm": max(0.0, -anomaly) if anomaly is not None else None,
                         "heat_days": int(heat.gt(heat_threshold).sum()) if heat is not None and heat_threshold is not None else None,
                         **vegetation_window(days, spans, raw, good)})
        comparisons = []
        for driver_name, (driver, sign) in DRIVERS.items():
            for response_name, response in RESPONSES.items():
                result = compare(rows, driver, response, sign, SEED + index * 6 + len(comparisons))
                comparisons.append({"driver": driver_name, "response": response_name, **result})
        seasons[name] = {"window_source": window["source"], "reference": reference,
                         "notes": window.get("p19_notes", []), "rows": rows, "comparisons": comparisons,
                         "sources": {"weather": POWER_SOURCE, "vegetation": MODIS_SOURCE}}
    return {"farm_id": farm["farm_id"], "years": list(years), "coverage": coverage, "seasons": seasons,
            "label": "illustrative; validate locally",
            "design": {"reference_years": list(reference_years), "heat_quantile": HEAT_QUANTILE,
                       "min_qa_composites": MIN_GOOD_COMPOSITES, "min_qa_day_share": MIN_GOOD_DAY_SHARE,
                       "strong_abs_rho": STRONG_RHO, "bootstrap_seed": SEED, "bootstrap_draws": BOOTSTRAP_DRAWS,
                       "source": DESIGN_SOURCE}}


def build(root=ROOT):
    processed = root / "data/processed"
    farms = json.loads((root / "config/farms.json").read_text())
    for farm in farms:
        farm_id = farm["farm_id"]
        windows = json.loads((processed / f"seasons_{farm_id}.json").read_text())["season_windows"]
        if farm_id == "telangana_a":
            windows["post_monsoon"]["p19_notes"] = ["Tentative second season inferred from MODIS NDVI."]
        if farm_id == "us_high_plains_b":
            windows["cool"]["p19_notes"] = ["Cool-season calendar is an assumption, validate locally."]
        if farm_id == "kenya_makueni_north":
            for window in windows.values():
                window["p19_notes"] = ["Cropland at this point is unverified."]
        result = compute(farm, windows, pd.read_parquet(processed / f"climate_{farm_id}.parquet"),
                         pd.read_csv(processed / f"ndvi_long_{farm_id}.csv"))
        atomic_write(processed / f"nasa_consistency_{farm_id}.json",
                     lambda temp: temp.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n"))


if __name__ == "__main__":
    build()
