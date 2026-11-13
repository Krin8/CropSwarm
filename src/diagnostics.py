"""Offline climate and vegetation diagnostics for the configured farms."""

import calendar
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.signal import find_peaks, savgol_filter
from scipy.stats import kendalltau, linregress, theilslopes
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from src.crops import load_crops
from src.precompute_cache import write_json

ROOT = Path(__file__).resolve().parents[1]
POWER = "NASA POWER | https://power.larc.nasa.gov/docs/services/api/temporal/daily/"
MODIS = "NASA Terra MOD13Q1 | https://ladsweb.modaps.eosdis.nasa.gov/filespec/MODIS/61/MOD13Q1"
ASSUMPTION = "assumption, validate locally"
PROMINENCES = (0.08, 0.12, 0.16)
BARE_NDVI = 0.25
DRY_MM = 1.0
FROST_C = 0.0
RAIN_WINDOW_FRACTION = 0.50
SEED = 42


def metric(value, unit, source=POWER):
    return {"value": value, "unit": unit, "source": source}


def trend(data):
    data = data.dropna()
    if len(data) < 3:
        return {"status": "incomplete", "years": len(data)}
    years = data.index.to_numpy(dtype=float)
    linear = linregress(years, data)
    robust = theilslopes(data, years)
    # Kendall's test against increasing time is the rank-based Mann-Kendall trend test.
    rank = kendalltau(years, data, method="asymptotic")
    return {"status": "complete", "years": len(data), "linear_per_decade": linear.slope * 10,
            "theil_sen_per_decade": robust.slope * 10, "theil_sen_95_interval": [
                robust.low_slope * 10, robust.high_slope * 10],
            "mann_kendall_p": float(rank.pvalue) if np.isfinite(rank.pvalue) else None,
            "mann_kendall_significant_0_05": bool(rank.pvalue < .05) if np.isfinite(rank.pvalue) else None}


def longest_run(mask):
    longest = current = 0
    for active in mask:
        current = current + 1 if active else 0
        longest = max(longest, current)
    return longest


def vegetation(frame):
    if frame.empty:
        return {}, pd.Series(dtype=float, name="smoothed_ndvi")
    frame = frame.copy().sort_values("date").set_index("date")
    quality = frame["vi_quality"].fillna(-1).astype(int)
    # Good summary QA plus good or absent detailed QA. Unreported summary QA is excluded.
    good = frame.pixel_reliability.eq(0) & (quality.eq(-1) | (quality & 3).eq(0))
    good &= frame.ndvi.between(-0.2, 1)
    clean = frame.ndvi.where(good)
    # Fill single internal gaps for smoothing only. Prohibit bridging larger gaps.
    interpolated = clean.where(~(clean.isna() & clean.shift().notna() & clean.shift(-1).notna()),
                               (clean.shift() + clean.shift(-1)) / 2)
    smooth = pd.Series(np.nan, index=frame.index)
    gap = frame.index.to_series().diff().dt.days.gt(17)
    groups = (interpolated.isna() | interpolated.shift().isna() | gap).cumsum()
    for _, segment in interpolated.groupby(groups):
        segment = segment.dropna()
        if len(segment) >= 5:
            smooth.loc[segment.index] = savgol_filter(segment, 5, 2)
    peaks = {}
    for prominence in PROMINENCES:
        dates = []
        for _, segment in smooth.groupby(groups):
            segment = segment.dropna()
            positions, _ = find_peaks(segment, prominence=prominence, distance=3)
            dates.extend(segment.index[position] for position in positions
                         if pd.notna(clean.loc[segment.index[position]]))
        peaks[str(prominence)] = dates
    result = {}
    for year, group in clean.groupby(clean.index.year):
        selected = {key: [date.date().isoformat() for date in dates if date.year == year]
                    for key, dates in peaks.items()}
        result[str(year)] = {
            "good_composites": int(group.count()),
            "received_composites": int(frame.ndvi.reindex(group.index).count()),
            "status": "complete" if frame.ndvi.reindex(group.index).count() == 23 else "incomplete",
            "peaks": selected, "peak_count": len(selected["0.12"]),
            "bare_composites": [date.date().isoformat() for date in group[group.lt(BARE_NDVI)].index],
        }
    return result, smooth.rename("smoothed_ndvi")


def contiguous_rain_windows(monthly):
    active = monthly.ge(monthly.max() * RAIN_WINDOW_FRACTION)
    starts = [month for month in range(1, 13) if active[month] and not active[(month - 2) % 12 + 1]]
    if active.all():
        return [(1, 12)]
    windows = []
    for start in starts:
        end = start
        while active[end % 12 + 1]:
            end = end % 12 + 1
        windows.append((start, end))
    return windows


def window_records(climate, start, end):
    records = []
    wetness_mean = []
    for year in range(climate.index.year.min(), climate.index.year.max() + 1):
        end_year = year + (end < start)
        last_day = calendar.monthrange(end_year, end)[1]
        dates = pd.date_range(f"{year}-{start:02d}-01", f"{end_year}-{end:02d}-{last_day}")
        sample = climate.reindex(dates)
        if sample[["PRECTOTCORR", "T2M", "T2M_MAX"]].isna().any().any():
            continue
        wetness_mean.append(float(sample.GWETROOT.mean()) if sample.GWETROOT.notna().all() else None)
        records.append({"year": year, "days": len(dates), "precip_mm": float(sample.PRECTOTCORR.sum()),
                        "temperature_c": float(sample.T2M.mean()), "peak_daily_rain_mm": float(sample.PRECTOTCORR.max()),
                        "max_temperature_c": float(sample.T2M_MAX.max()), "soil_wetness": wetness_mean[-1]})
    reference = [value for value in wetness_mean if value is not None]
    center = float(np.mean(reference)) if reference else None
    for record in records:
        value = record["soil_wetness"]
        record["soil_wetness_anomaly"] = None if value is None else value - center
    return records


def derive_seasons(farm, climate, monthly, ndvi):
    windows = contiguous_rain_windows(monthly)
    source = f"{POWER}; {MODIS}"
    peak_months = [pd.Timestamp(date).month for year, row in ndvi.items()
                   if year.isdigit() and row["status"] == "complete" for date in row["peaks"]["0.12"]]
    east_africa = farm["farm_id"].startswith("kenya_")
    if len(windows) == 2 and east_africa:
        candidates = [("long_rains", windows[0]), ("short_rains", windows[1])]
        slot_labels = [[label] for label, _ in candidates]
    elif farm["farm_id"] == "telangana_a":
        wet = max(windows, key=lambda pair: sum(monthly[month] for month in range(pair[0], pair[1] + 1)))
        candidates = [("monsoon", wet)]
        climatology = ndvi.get("monthly_climatology", {})
        if all(str(month) in climatology for month in (1, 2, 3, 4)):
            peak = max(range(1, 5), key=lambda month: climatology[str(month)])
            neighbors = [str((peak - 2) % 12 + 1), str(peak % 12 + 1)]
            if all(key in climatology and climatology[str(peak)] - climatology[key] >= 0.08
                   for key in neighbors):
                candidates.append(("post_monsoon", ((peak - 4) % 12 + 1, peak % 12 + 1)))
        slot_labels = [[label] for label, _ in candidates]
    else:
        wet = windows[0]
        candidates = [("warm", wet), ("cool", (10, 6))]
        slot_labels = [["cool", "warm"]]
    slots = [{"slot": i, "eligible_labels": labels} for i, labels in enumerate(slot_labels)]
    season_windows = {}
    for label, (start, end) in candidates:
        season_windows[label] = {
            "onset_month": start, "cessation_month": end,
            "source": ASSUMPTION if label == "cool" else source,
            "historical": window_records(climate, start, end),
        }
    return {"farm_id": farm["farm_id"], "label": "illustrative; validate locally",
            "source": source, "season_windows": season_windows, "slots": slots,
            "rainfall_windows": [{"onset_month": start, "cessation_month": end} for start, end in windows],
            "derived_seasons_per_year": len(slots), "assumed_seasons_per_year": farm["seasons_per_year"],
            "agreement": len(slots) == farm["seasons_per_year"], "ndvi_peak_months": peak_months,
            "uncertainty_note": "Monthly windows are approximate. Vegetation peaks can reflect crops or other cover. Kansas cool-season timing is an assumption. Telangana's secondary window uses a monthly NDVI climatology peak and remains tentative."}


def analyse(farm, climate, ndvi, crops):
    climate = climate.sort_values("date").set_index("date").asfreq("D")
    by_year = climate.groupby(climate.index.year)
    annual = pd.DataFrame({
        "rain": by_year.PRECTOTCORR.sum().where(by_year.PRECTOTCORR.count().eq(by_year.size())),
        "temp": by_year.T2M.mean().where(by_year.T2M.count().eq(by_year.size())),
        "high": by_year.T2M_MAX.mean().where(by_year.T2M_MAX.count().eq(by_year.size())),
    })
    dates = climate.index
    rain_monthly = climate.PRECTOTCORR.resample("MS").sum(min_count=1)
    rain_monthly = rain_monthly.where(climate.PRECTOTCORR.resample("MS").count().eq(rain_monthly.index.days_in_month))
    monthly = rain_monthly.groupby(rain_monthly.index.month).mean()
    veg, smooth = vegetation(ndvi)
    quality_ndvi = ndvi[ndvi.pixel_reliability.eq(0)]
    median_ndvi = quality_ndvi.groupby(quality_ndvi.date.dt.month).ndvi.median().dropna()
    seasons = derive_seasons(farm, climate, monthly, {
        **veg, "monthly_climatology": {str(month): float(value) for month, value in median_ndvi.items()}
    })
    rainfall_cv = float(annual.rain.std() / annual.rain.mean()) if annual.rain.mean() > 0 else None
    paired = climate[["IMERG_PRECTOT", "PRECTOTCORR_UTC"]].loc["2000":"2025"].dropna()
    difference = paired.IMERG_PRECTOT - paired.PRECTOTCORR_UTC
    agreement = {"days": len(paired), "bias": float(difference.mean()), "mae": float(difference.abs().mean()),
                 "correlation": float(paired.corr().iloc[0, 1])} if not paired.empty else None
    if agreement:
        agreement = {k: v if np.isfinite(v) else None for k, v in agreement.items()}
    regimes = annual.dropna().copy()
    regime_rows = {}
    if len(regimes) >= 3 and len(regimes.drop_duplicates()) >= 3:
        scaled = StandardScaler().fit_transform(regimes)
        with threadpool_limits(limits=1):
            clusters = KMeans(n_clusters=3, random_state=SEED, n_init=10).fit_predict(scaled)
        # Name clusters by relative wetness with joint heat and dryness for the dry-hot cluster.
        centers = pd.DataFrame(scaled, columns=["rain", "temp", "high"]).groupby(clusters).mean()
        wet = centers.rain.idxmax()
        other = centers.drop(wet)
        dry = (other.high - other.rain).idxmax()
        names = {int(wet): "wet", int(dry): "dry_hot"}
        regime_rows = {str(year): names.get(int(cluster), "normal") for year, cluster in zip(regimes.index, clusters, strict=True)}
    heat = {crop_id: {"threshold_c": crop["heat_tolerance_c"],
                     "threshold_source": "data/crops.csv", "observed_days": int(climate.T2M_MAX.count()),
                     "days_above": int(climate.T2M_MAX.gt(crop["heat_tolerance_c"]).sum())}
            for crop_id, crop in crops.items()
            if crop["heat_tolerance_c"] is not None and climate.T2M_MAX.notna().any()}
    frost_windows = {}
    if climate.T2M_MIN.le(FROST_C).any():
        for year, sample in by_year:
            if sample.T2M_MIN.isna().any():
                continue
            above = sample.T2M_MIN.gt(FROST_C)
            length = longest_run(above)
            runs = above.ne(above.shift()).cumsum()
            intervals = [series for _, series in above.groupby(runs) if series.iloc[0]]
            longest = max(intervals, key=len, default=None)
            frost_windows[str(year)] = {"days": length, "start": str(longest.index[0].date()) if length else None,
                                        "end": str(longest.index[-1].date()) if length else None}
    dry = longest_run(climate.PRECTOTCORR.lt(DRY_MM)) if climate.PRECTOTCORR.notna().any() else None
    observations = {
        "temperature_trend": metric(trend(annual.temp), "°C/decade"),
        "precipitation_trend": metric(trend(annual.rain), "mm/decade of annual total"),
        "rainfall_cv": metric(rainfall_cv, "ratio"),
        "longest_observed_dry_spell": metric(dry, "days"),
        "days_above_crop_heat_threshold": metric(heat, "days"),
        "frost_free_windows": metric(frost_windows, "days and calendar dates"),
        "seasonal_soil_wetness_anomaly": metric({key: [
            {"year": row["year"], "anomaly": row["soil_wetness_anomaly"]} for row in window["historical"]]
            for key, window in seasons["season_windows"].items()}, "relative soil wetness"),
        "precipitation_data_agreement": metric(agreement, "daily mm, Pearson r and matched days",
                                                "NASA POWER PRECTOTCORR and IMERG_PRECTOT (UTC)"),
        "annual_climate_regimes": metric(regime_rows, "class"),
        "ndvi_peaks": metric(veg, "counts and composite dates", MODIS),
        "monthly_precipitation": metric({int(month): round(float(value), 2) for month, value in monthly.items()},
                                         "mm/month"),
    }
    sentence = f"NASA POWER supplies {len(dates):,} calendar days for this site."
    if dry is not None:
        sentence += f" The longest observed dry spell was {dry} days using the local-validation rainfall threshold."
    if rainfall_cv is not None:
        sentence += f" The annual rainfall coefficient of variation was {rainfall_cv:.2f}."
    if veg:
        usable = sum(row["good_composites"] for row in veg.values())
        sentence += f" MODIS supplied {usable} quality-screened vegetation composites for this assessment."
    if agreement:
        sentence += f" The mean absolute difference between the two daily rainfall products was {agreement['mae']:.1f} mm."
    return {"farm_id": farm["farm_id"], "label": "illustrative; validate locally", "assessment": sentence,
            "metrics": observations, "validation_flags": farm["validation_flags"],
            "limitations": ["POWER soil wetness is modelled. Rainfall and vegetation are gridded products.",
                            "Satellites do not directly measure soil nitrogen or organic carbon.",
                            "Rank trend significance assumes independent annual values. It is illustrative."]}, seasons, annual, smooth


def save_charts(output, farm_id, assessment, annual, smooth):
    rain = assessment["metrics"]["monthly_precipitation"]["value"]
    charts = {
        "monthly_rain": go.Figure(go.Bar(x=[calendar.month_abbr[month] for month in rain], y=list(rain.values()))),
        "annual_rain": go.Figure(go.Scatter(x=annual.index.tolist(), y=annual.rain.tolist())),
        "annual_temperature": go.Figure(go.Scatter(x=annual.index.tolist(), y=annual.temp.tolist())),
        "vegetation": go.Figure(go.Scatter(x=smooth.index.tolist(), y=smooth.tolist(), connectgaps=False)),
    }
    titles = {"monthly_rain": ("Monthly rainfall", "mm/month", "NASA POWER"),
              "annual_rain": ("Annual rainfall", "mm/year", "NASA POWER"),
              "annual_temperature": ("Average annual temperature", "°C", "NASA POWER"),
              "vegetation": ("Quality-screened vegetation index", "NDVI", "NASA Terra MODIS")}
    for key, figure in charts.items():
        title, unit, source = titles[key]
        figure.update_layout(title=f"{title} · {source}", yaxis_title=unit,
                             margin=dict(t=45, l=48, r=12, b=30))
        (output / f"chart_{farm_id}_{key}.json").write_text(figure.to_json() + "\n")


def main():
    output = ROOT / "data/processed"
    farms = json.loads((ROOT / "config/farms.json").read_text())
    crops = load_crops(ROOT / "data/crops.csv", farms=farms)
    for farm in farms:
        farm_id = farm["farm_id"]
        climate = pd.read_parquet(output / f"climate_{farm_id}.parquet")
        ndvi = pd.read_csv(output / f"ndvi_{farm_id}.csv", parse_dates=["date"])
        assessment, seasons, annual, smooth = analyse(farm, climate, ndvi, crops)
        write_json(output / f"assessment_{farm_id}.json", assessment)
        write_json(output / f"seasons_{farm_id}.json", seasons)
        save_charts(output, farm_id, assessment, annual, smooth)


if __name__ == "__main__":
    main()
