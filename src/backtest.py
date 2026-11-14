"""Offline comparison of fixed crop stress indicators with QA-screened MODIS greenness."""

import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import spearmanr

from src.crops import load_crops
from src.precompute_cache import write_json
from src.scoring import ROOT, crop_windows, daily_water_deficit, preload

YEARS = range(2019, 2024)
BOOTSTRAP_DRAWS = 1000  # design choice, not empirical; fixed seed below
SEED = 42  # design choice, not empirical
POWER = "NASA POWER PRECTOTCORR and T2M_MAX; cached daily climate"
MODIS = "NASA Terra MOD13Q1 NDVI via ORNL DAAC; QA-screened point pixel"
CATALOG = "data/crops.csv; illustrative crop demand and heat thresholds"
ASSUMPTION = "assumption, validate locally"
CDL = "USDA NASS CDL point classes 2019–2023; data/raw/p2_evidence/p2_wheat_cdl.json"
CDL_CROPS = {61: "fallow", 24: "winter_wheat", 4: "sorghum"}


def quality_ndvi(frame):
    """Use the same summary and detailed QA gate as diagnostics.vegetation."""
    frame = frame.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    quality = frame["vi_quality"].fillna(-1).astype(int)
    good = frame["pixel_reliability"].eq(0) & (quality.eq(-1) | (quality & 3).eq(0))
    return frame.loc[good & frame["ndvi"].between(-0.2, 1)].sort_values("date")


def cdl_history(payload):
    result = {}
    for year in YEARS:
        record = payload[str(year)]
        if record["status"] != 200:
            raise ValueError(f"CDL {year} was not successful")
        match = re.search(r"\bvalue:\s*(\d+)\b", record["body"])
        if not match or int(match.group(1)) not in CDL_CROPS:
            raise ValueError(f"CDL {year} crop class unrecognized")
        result[year] = CDL_CROPS[int(match.group(1))]
    return result


def rank_interval(x, y, *, seed=SEED, draws=BOOTSTRAP_DRAWS):
    paired = np.asarray([(a, b) for a, b in zip(x, y, strict=True)
                         if a is not None and b is not None and np.isfinite(a) and np.isfinite(b)], dtype=float)
    n = len(paired)
    if n < 3 or len(set(paired[:, 0])) < 2 or len(set(paired[:, 1])) < 2:
        return {"rho": None, "n": n, "bootstrap_95": None, "small_n": n < 8,
                "note": "insufficient variation or fewer than three pairs"}
    rho = float(spearmanr(paired[:, 0], paired[:, 1]).statistic)
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(draws):
        row = paired[rng.integers(0, n, n)]
        if len(set(row[:, 0])) >= 2 and len(set(row[:, 1])) >= 2:
            samples.append(float(spearmanr(row[:, 0], row[:, 1]).statistic))
    interval = [float(v) for v in np.percentile(samples, [2.5, 97.5])] if samples else None
    return {"rho": rho, "n": n, "bootstrap_95": interval, "small_n": n < 8,
            "note": "descriptive bootstrap; not a calibrated confidence interval"}


def directional_count(rows, stress="deficit_fraction", response="ndvi_peak"):
    """Count opposing within-season departures from medians, excluding median ties."""
    pairs = [(r[stress]["value"], r[response]["value"]) for r in rows
             if r[stress]["value"] is not None and r[response]["value"] is not None]
    if len(pairs) < 3:
        return {"consistent": 0, "assessable": 0}
    a, b = np.asarray(pairs).T
    a_delta, b_delta = a - np.median(a), b - np.median(b)
    assessable = (a_delta != 0) & (b_delta != 0)
    return {"consistent": int(((a_delta * b_delta < 0) & assessable).sum()),
            "assessable": int(assessable.sum())}


def compute(farm, model, climate, ndvi, *, cdl=None, years=YEARS):
    clean = quality_ndvi(ndvi)
    climate = climate.sort_values("date").set_index("date")
    observed = cdl_history(cdl) if cdl is not None else None
    rows = []
    for year in years:
        crop_ids = ([observed[year]] if observed is not None else
                    farm["baseline_rotation_cycle"][(year - 2019) % len(farm["baseline_rotation_cycle"])])
        for slot, crop_id in enumerate(crop_ids):
            crop = model.crops[crop_id]
            label, onset, length = model.days[slot, model.ids.index(crop_id)]
            # A CDL winter-wheat class is labelled by harvest year; the modeled window starts in prior October.
            start_year = year - 1 if observed is not None and label == "cool" else year
            if length == 0:
                window = json.loads((ROOT / "data/processed" / f"seasons_{farm['farm_id']}.json").read_text())["season_windows"][label]
                first, last = window["onset_month"], window["cessation_month"]
                length = (pd.Timestamp(2001 + (last < first or last == 12), last % 12 + 1, 1) -
                          pd.Timestamp(2001, first, 1)).days
            sample = crop_windows(climate, onset, length).get(start_year)
            start = pd.Timestamp(start_year, onset, 1)
            end = start + pd.Timedelta(days=length - 1)
            vegetation = clean.loc[clean.date.between(start, end), "ndvi"]
            enough_ndvi = len(vegetation) >= 3  # screening rule; design choice, validate locally
            if sample is None:
                rain = deficit = fraction = hot_days = None
            else:
                rain = float(sample[:, 0].sum())
                if crop["season_length_days"] == 0:
                    deficit = fraction = hot_days = None
                else:
                    demand = crop["water_need_mm"]
                    deficit = float(daily_water_deficit(sample[None, :, 0], demand, model.storage)[0] *
                                    (1 - farm["irrigation"]["supply_fraction"]))
                    fraction = deficit / demand if demand else None
                    hot_days = int((sample[:, 2] > crop["heat_tolerance_c"]).sum())
            def item(value, unit, source):
                return {"value": value, "unit": unit, "source": source}
            rows.append({"year": year, "season": label, "slot": slot + 1, "crop_id": crop_id,
                         "crop_basis": CDL if observed is not None else farm["baseline_source"],
                         "window_start": str(start.date()), "window_end": str(end.date()),
                         "rainfall_mm": item(rain, "mm", POWER),
                         "crop_water_need_mm": item(crop["water_need_mm"] if crop["season_length_days"] else None,
                                                    "mm", CATALOG),
                         "deficit_mm": item(deficit, "mm", POWER + "; " + CATALOG + "; soil water and irrigation assumptions"),
                         "deficit_fraction": item(fraction, "share of crop water need", POWER + "; " + CATALOG),
                         "heat_days": item(hot_days, "days", POWER + "; " + CATALOG),
                         "ndvi_peak": item(float(vegetation.max()) if enough_ndvi else None, "NDVI ratio", MODIS),
                         "ndvi_amplitude": item(float(vegetation.max() - vegetation.min()) if enough_ndvi else None,
                                                "NDVI ratio", MODIS),
                         "good_composites": item(len(vegetation), "composites", MODIS),
                         "status": "complete" if sample is not None and enough_ndvi else "incomplete"})
    analyses = {}
    for slot, name in enumerate(dict.fromkeys(r["season"] for r in rows)):
        season_rows = [r for r in rows if r["season"] == name]
        comparisons = {}
        for stress in ("deficit_fraction", "heat_days"):
            for response in ("ndvi_peak", "ndvi_amplitude"):
                pairs = [r for r in season_rows if r["status"] == "complete"]
                comparisons[f"{stress}_vs_{response}"] = rank_interval(
                    [r[stress]["value"] for r in pairs], [r[response]["value"] for r in pairs],
                    seed=SEED + slot * 4 + len(comparisons))
        analyses[name] = {"comparisons": comparisons, "directional": directional_count(
            [r for r in season_rows if r["status"] == "complete"]),
            "source": POWER + "; " + MODIS + "; " + CATALOG}
    return {"farm_id": farm["farm_id"], "years": list(years), "label": "illustrative; validate locally",
            "crop_identity": "CDL mapped point class, not verified farm management" if observed is not None else ASSUMPTION,
            "method": "Crop-window rainfall and heat from scoring inputs; daily bucket deficit; QA-filtered MOD13Q1 peak and max-minus-min amplitude. Spearman and seeded paired bootstrap within season; no parameter tuning.",
            "bootstrap": {"draws": BOOTSTRAP_DRAWS, "seed": SEED, "source": "design choice, not empirical"},
            "screening": {"minimum_good_composites": 3, "small_n_below": 8,
                          "source": "design choice, not empirical; validate locally"},
            "rows": rows, "seasons": analyses,
            "caveats": ["MODIS point pixels can mix fields, weeds and other cover; NDVI is not a crop-yield measure.",
                        "CDL is a mapped class at a different resolution, not a management record.",
                        "Small sample sizes and repeated assumptions make correlations descriptive only.",
                        "Kansas 2019 spring NDVI over mapped fallow remains unexplained.",
                        "Telangana's second season is tentative; Makueni cropland is unverified."]}


def chart(result):
    figure = go.Figure()
    for season, group in result["seasons"].items():
        rows = [r for r in result["rows"] if r["season"] == season and r["status"] == "complete"
                and r["deficit_fraction"]["value"] is not None]
        figure.add_trace(go.Scatter(x=[r["deficit_fraction"]["value"] for r in rows],
                                    y=[r["ndvi_peak"]["value"] for r in rows],
                                    text=[str(r["year"]) for r in rows], mode="markers+text", name=season,
                                    textposition="top center"))
    figure.update_layout(title=f"{result['farm_id']}: modeled water deficit vs QA-filtered NDVI peak",
                         xaxis_title="Modeled unmet crop water demand / need (share)",
                         yaxis_title="Observed MODIS NDVI seasonal peak (ratio)", height=420)
    return figure


def chart_svg(result):
    """Standalone offline preview of the same points as the interactive Plotly chart."""
    left, top, width, height = 85, 70, 580, 350
    colors = ("#28724e", "#a6612b", "#336e9c")
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="760" height="510" viewBox="0 0 760 510">',
             '<rect width="760" height="510" fill="#fff"/>',
             f'<text x="30" y="35" font-size="18" font-family="sans-serif">{escape(result["farm_id"])}: modeled water stress and MODIS NDVI</text>',
             f'<path d="M{left} {top}V{top+height}H{left+width}" fill="none" stroke="#333"/>']
    for step in range(5):
        value = step / 4
        x = left + value * width
        y = top + height - value * height
        parts.extend([f'<text x="{x-9:.0f}" y="{top+height+23}" font-size="12" font-family="sans-serif">{value:.2f}</text>',
                      f'<text x="{left-42}" y="{y+4:.0f}" font-size="12" font-family="sans-serif">{value:.2f}</text>'])
    for index, season in enumerate(result["seasons"]):
        color = colors[index % len(colors)]
        for row in result["rows"]:
            if row["season"] != season or row["status"] != "complete":
                continue
            x_value = row["deficit_fraction"]["value"]
            y_value = row["ndvi_peak"]["value"]
            if x_value is None or y_value is None:
                continue
            x = left + min(1, max(0, x_value)) * width
            y = top + height - min(1, max(0, y_value)) * height
            parts.extend([f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{color}"/>',
                          f'<text x="{x+8:.1f}" y="{y-8:.1f}" font-size="12" font-family="sans-serif">{row["year"]}</text>'])
        parts.append(f'<text x="{left+width+20}" y="{top+24*index+12}" fill="{color}" font-size="13" font-family="sans-serif">{escape(season)}</text>')
    parts.extend([f'<text x="{left+120}" y="480" font-size="13" font-family="sans-serif">Modeled unmet water / crop demand (share) · NASA POWER + assumptions</text>',
                  f'<text transform="translate(20 {top+height-5}) rotate(-90)" font-size="13" font-family="sans-serif">QA-filtered MODIS NDVI peak</text>',
                  '</svg>'])
    return "\n".join(parts) + "\n"


def build(root=ROOT):
    root = Path(root)
    farms = json.loads((root / "config/farms.json").read_text())
    crops = load_crops(root / "data/crops.csv", farms=farms)
    cdl = json.loads((root / "data/raw/p2_evidence/p2_wheat_cdl.json").read_text())
    for farm in farms:
        farm_id = farm["farm_id"]
        model = preload(farm, root=root, crops=crops)
        climate = pd.read_parquet(root / "data/processed" / f"climate_{farm_id}.parquet")
        ndvi = pd.read_csv(root / "data/processed" / f"ndvi_{farm_id}.csv")
        result = compute(farm, model, climate, ndvi, cdl=cdl if farm_id == "us_high_plains_b" else None)
        write_json(root / "data/processed" / f"backtest_{farm_id}.json", result)
        figure = chart(result)
        (root / "data/processed" / f"chart_backtest_{farm_id}.json").write_text(figure.to_json())
        chart_dir = root / "docs/charts"
        chart_dir.mkdir(parents=True, exist_ok=True)
        (chart_dir / f"backtest_{farm_id}.svg").write_text(chart_svg(result))


if __name__ == "__main__":
    build()
