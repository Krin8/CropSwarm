"""Offline screening of potential cover-crop windows from QA-filtered vegetation."""
from collections import Counter, defaultdict
from dataclasses import replace
import json

import numpy as np
import pandas as pd

from src.backtest import quality_ndvi
from src.data_pipeline import LONG_MODIS_YEARS, MODIS_SOURCE, POWER_SOURCE
from src.diagnostics import BARE_NDVI, FROST_C
from src.evidence import FIELD_SOURCES, GRADES, cap_label, crop_source_grade, label_for_shares
from src.nasa_consistency import composite_spans
from src.precompute_cache import write_json
from src.scoring import ROOT, baseline_indices, historical_metrics, preload, score_rotations
from src.validation import POWER_FILL_VALUE


DESIGN = "assumption, validate locally"
WEATHER_FIELDS = ["PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "GWETROOT"]
FIT_CHECKS = ("length", "temperature", "water", "overall")
SITE_FLAGS = ("spring peak remains unexplained", "second crop season remains tentative",
              "cropland at exact point unverified")
BENEFITS = {
    "nitrogen": "kg N/ha per insertion",
    "erosion_proxy": "slope × peak daily rainfall proxy",
    "water_used": "mm of modeled crop-water demand met",
    "unmet_water": "mm of additional modeled unmet crop water",
}


def evidence(inputs, config, flags=()):
    """Apply the P18 equal-field provenance rule and a conservative site cap."""
    counts = Counter(item["grade"] for item in inputs)
    shares = {grade: counts[grade] / len(inputs) for grade in GRADES}
    label = label_for_shares(shares, config)
    return {"label": cap_label(label, "low") if flags else label, "shares": shares,
            "inputs": inputs, "reasons": list(flags)}


def source(field, grade, reference):
    return {"field": field, "grade": grade, "source": reference}


def crop_sources(crop, fields, evidence_config):
    return [source(field, crop_source_grade(crop[FIELD_SOURCES[field]], evidence_config),
                   crop[FIELD_SOURCES[field]]) for field in fields]


def prepare_ndvi(ndvi, spans):
    ndvi = ndvi.assign(date=pd.to_datetime(ndvi.date))
    clean = quality_ndvi(ndvi).set_index("date").ndvi
    return clean.reindex(sorted(spans))


def bare_runs(series, spans, threshold):
    """Detect runs of at least two adjacent valid low composites through year-end."""
    runs, current = [], []
    for day, value in series.items():
        if current and (not pd.notna(value) or value >= threshold or spans[current[-1]] != day):
            if len(current) >= 2:
                runs.append(tuple(current))
            current = []
        if pd.notna(value) and value < threshold:
            current.append(day)
    if len(current) >= 2:
        runs.append(tuple(current))
    return runs


def window_clusters(series, spans, runs, config):
    """Find recurrent adjacent-composite pairs by their nominal MODIS day of year."""
    run_by_date = {day: run for run in runs for day in run[:-1]}
    pairs = defaultdict(list)
    support = defaultdict(list)
    all_slots = sorted({day.day_of_year for day in series.index})
    for day, next_day in zip(series.index[:-1], series.index[1:], strict=True):
        if spans[day] != next_day or pd.isna(series[day]) or pd.isna(series[next_day]):
            continue
        slot = day.day_of_year
        pairs[slot].append(day)
        if day in run_by_date:
            support[slot].append(day)

    def recurrent(slot):
        return (len(support[slot]) >= config["minimum_support_years"]
                and len(support[slot]) / len(pairs[slot]) >= config["minimum_recurrence_fraction"])

    groups = []
    for index, slot in enumerate(all_slots):
        if recurrent(slot):
            if groups and index and groups[-1][-1] == all_slots[index - 1]:
                groups[-1].append(slot)
            else:
                groups.append([slot])
    if len(groups) > 1 and groups[0][0] == all_slots[0] and groups[-1][-1] == all_slots[-1]:
        groups = [groups[-1] + groups[0], *groups[1:-1]]

    # Show the strongest thinly supported signal when there is no recurrent pair.
    exploratory = not groups
    if exploratory:
        present = [slot for slot in all_slots if support[slot]]
        groups = [present] if present else []
    return [(max(group, key=lambda slot: (len(support[slot]), len(support[slot]) / len(pairs[slot]), -slot)),
             group if not exploratory else [], pairs, support, run_by_date)
            for group in groups]


def summarize_windows(series, spans, runs, config):
    result = []
    for slot, group, pairs, support, run_by_date in window_clusters(series, spans, runs, config):
        annual = []
        for anchor in support[slot]:
            run = run_by_date[anchor]
            start, stop = run[0], spans[run[-1]]
            annual.append({"anchor_year": anchor.year, "start": start.date().isoformat(),
                           "end_exclusive": stop.date().isoformat(), "start_doy": start.day_of_year,
                           "days": (stop - start).days, "qa_composites": len(run),
                           "offset_days": (start - anchor).days})
        start_offsets = np.array([row["offset_days"] for row in annual])
        lengths = np.array([row["days"] for row in annual])
        anchor_date = pd.Timestamp(config["timeline_year"], 1, 1) + pd.Timedelta(days=slot - 1)
        typical_start = anchor_date + pd.Timedelta(days=round(float(np.median(start_offsets))))
        typical_days = int(round(float(np.median(lengths))))
        enough = len(annual) >= config["minimum_support_years"]
        interval = {}
        if enough:
            rng = np.random.default_rng(config["bootstrap_seed"])
            draws = rng.integers(len(annual), size=(config["bootstrap_draws"], len(annual)))
            quantiles = config["bootstrap_quantiles"]
            interval = {"start_offset_days": np.quantile(np.median(start_offsets[draws], axis=1), quantiles).tolist(),
                        "length_days": np.quantile(np.median(lengths[draws], axis=1), quantiles).tolist()}
        result.append({
            "anchor_doy": slot, "start_doy": typical_start.day_of_year,
            "typical_start": typical_start.date().isoformat(), "typical_days": typical_days,
            "supporting_years": len(annual), "assessable_years": len(pairs[slot]),
            "qa_composites": sum(row["qa_composites"] for row in annual),
            "anchor_pair_qa_composites": 2 * len(pairs[slot]),
            "status": "recurrent" if group else ("tentative" if not enough else "sporadic"),
            "recurrent_anchor_doys": group, "bootstrap_interval": interval,
            "years": annual,
        })
    return result


def normalize_weather(climate):
    return climate.assign(date=pd.to_datetime(climate.date)).set_index("date")[WEATHER_FIELDS].replace(
        [POWER_FILL_VALUE, np.inf, -np.inf], np.nan).sort_index()


def fit_year(window, crop, weather, capacity, irrigation, policy, needs_frost_free):
    """Screen the fixed crop-duration interval beginning at the observed run start."""
    duration = crop["season_length_days"]
    result = {"anchor_year": window["anchor_year"], "length": window["days"] >= duration,
              "temperature": None, "water": None, "overall": None}
    if not result["length"]:
        return {**result, "overall": False}

    sample = weather.reindex(pd.date_range(window["start"], periods=duration))
    fields = ["T2M", "T2M_MAX"] + (["T2M_MIN"] if needs_frost_free else [])
    if sample[fields].notna().all().all():
        mean = float(sample.T2M.mean())
        heat_days = int(sample.T2M_MAX.gt(crop["heat_tolerance_c"]).sum())
        frost_days = int(sample.T2M_MIN.le(FROST_C).sum()) if needs_frost_free else None
        result.update(mean_temperature_c=mean, heat_days=heat_days, frost_days=frost_days,
                      temperature=(crop["min_temp_c"] <= mean <= crop["max_temp_c"]
                                   and heat_days / duration <= policy["max_hot_day_fraction"]
                                   and (frost_days is None or frost_days == 0)))
    wetness = sample.GWETROOT.iloc[0]
    if sample.PRECTOTCORR.notna().all() and pd.notna(wetness) and 0 <= wetness <= 1:
        rain = float(sample.PRECTOTCORR.sum())
        proxy = float(wetness * capacity)
        extra = irrigation * max(crop["water_need_mm"] - rain - proxy, 0)
        result.update(rainfall_mm=rain, initial_soil_water_proxy_mm=proxy, irrigation_mm=extra,
                      water=(rain <= crop["max_rain_mm"] and rain + proxy + extra >= crop["min_rain_mm"]))
    checks = (result["temperature"], result["water"])
    if any(value is False for value in checks):
        result["overall"] = False
    elif all(value is True for value in checks):
        result["overall"] = True
    return result


def summarize_checks(rows):
    return {check: {"passes": sum(row[check] is True for row in rows),
                    "n": sum(row[check] is not None for row in rows)}
            for check in FIT_CHECKS}


def modeled_addition(model, crop_index, sample):
    """Use the engine to compare an uncovered gap and a planted gap in one baseline cycle."""
    baseline = baseline_indices(model)
    fallow = model.ids.index("fallow")
    # Rotate the cycle to compare the gap just before the first planted crop.
    # The existing engine applies each crop's credit to its successor.
    following = next((index for index, crop in enumerate(baseline) if crop != fallow), 0)
    original_slots = (np.arange(len(baseline)) + following) % len(baseline) % len(model.season_labels)
    baseline = np.roll(baseline, -following)
    gap = np.zeros_like(model.additions[0])
    supply = model.farm["irrigation"]["supply_fraction"]
    for index in (fallow, crop_index):
        gap[index] = historical_metrics({0: sample}, model.crops[model.ids[index]], model.storage,
                                        model.slope, supply, model.policy)[0]
    slots = len(baseline) + 1
    # The two cycles have the same length. Other crop contributions cancel out.
    comparison = replace(model, season_labels=[[]] * slots,
                         additions=np.concatenate([model.additions[original_slots], gap[None]]),
                         planting_windows=np.ones((slots, len(model.ids)), dtype=bool),
                         suitable=np.ones((slots, len(model.ids)), dtype=bool))
    raw, _, _ = score_rotations(comparison, [np.append(baseline, fallow), np.append(baseline, crop_index)])
    unmet, nitrogen, erosion = (raw[1, :3] - raw[0, :3]) * slots
    water_need = model.crops[model.ids[crop_index]]["water_need_mm"]
    return {"nitrogen": float(nitrogen), "erosion_proxy": float(erosion),
            "water_used": float(water_need - unmet), "unmet_water": float(unmet)}


def benefit_summary(model, crop_index, rows, weather, window):
    values = []
    starts = {row["anchor_year"]: row["start"] for row in window["years"]}
    duration = model.crops[model.ids[crop_index]]["season_length_days"]
    for row in rows:
        if row["overall"] is True:
            days = pd.date_range(starts[row["anchor_year"]], periods=duration)
            sample = weather.loc[days, WEATHER_FIELDS[:3]].to_numpy()
            values.append(modeled_addition(model, crop_index, sample))
    return {key: {"median": float(np.median([value[key] for value in values])),
                  "range": [float(min(value[key] for value in values)), float(max(value[key] for value in values))],
                  "unit": unit}
            for key, unit in BENEFITS.items()} if values else {}


def evidence_ledger(model, crop, config, flags):
    length = [
        source("Low NDVI span", "nasa_measured", MODIS_SOURCE),
        source("P5 threshold and window rule", "assumption", DESIGN),
        *crop_sources(crop, ("season_length_days",), config),
    ]
    temperature = [
        source("Temperature, daily minimum and maximum", "nasa_measured", POWER_SOURCE),
        source("Heat-day fraction and frost screen", "assumption", DESIGN),
        *crop_sources(crop, ("min_temp_c", "max_temp_c", "heat_tolerance_c"), config),
    ]
    soil_grade = ("assumption" if DESIGN in model.soil_source.lower() else "external_measured")
    water = [
        source("Rainfall", "nasa_measured", POWER_SOURCE),
        source("Root-zone wetness, modeled", "nasa_modeled", POWER_SOURCE),
        source("Mapped soil water capacity", soil_grade, model.soil_source),
        source("Available irrigation share", "assumption", model.farm["irrigation"]["basis"]),
        source("Wetness-to-storage proxy", "assumption", DESIGN),
        *crop_sources(crop, ("water_need_mm", "min_rain_mm", "max_rain_mm"), config),
    ]
    modeled = source("Uncovered versus planted gap in baseline cycle", "assumption", DESIGN)
    baseline_source = model.farm["baseline_source"]
    baseline_grade = "assumption" if DESIGN in baseline_source.lower() else "external_measured"
    passing_years = length + temperature + water
    bucket = [*passing_years, modeled, source("Daily soil-water bucket", "assumption", DESIGN)]
    baseline = source("Configured baseline rotation", baseline_grade, baseline_source)
    return {key: evidence(inputs, config, flags) for key, inputs in {
        "length": length, "temperature": length + temperature, "water": length + water,
        "overall": passing_years,
        "nitrogen": [*passing_years, modeled, baseline, source("Carryover calculation", "assumption", DESIGN),
                     *crop_sources(crop, ("n_credit_kg_ha", "n_demand_kg_ha"), config)],
        "erosion_proxy": [*passing_years, modeled, source("Terrain slope", "nasa_modeled", "NASA SRTM-derived slope"),
                          *crop_sources(crop, ("cover_score",), config)],
        "water_used": bucket, "unmet_water": bucket,
    }.items()}


def compute(model, ndvi, climate, spans, config, grades):
    series = prepare_ndvi(ndvi, spans)
    weather = normalize_weather(climate)
    flags = [flag for flag in model.farm["validation_flags"] if any(term in flag.lower() for term in SITE_FLAGS)]
    candidates = []
    local_seasons = {label for slot in model.season_labels for label in slot}
    for index, (crop_id, crop) in enumerate(model.crops.items()):
        if (crop_id in config["cover_crop_ids"] or
                (crop["is_legume"] and crop["season_length_days"] <= config["max_short_legume_days"])):
            local_labels = set(crop["seasons_allowed"]) & local_seasons
            candidates.append((index, crop_id, crop, evidence_ledger(model, crop, grades, flags), sorted(local_labels)))
    sensitivity = []
    for offset in config["threshold_offsets"]:
        threshold = round(BARE_NDVI + offset, 8)
        runs = bare_runs(series, spans, threshold)
        windows = summarize_windows(series, spans, runs, config)
        for window in windows:
            fit = []
            for index, crop_id, crop, ledger, local_labels in candidates:
                frost_free = crop_id not in config["frost_screen_exceptions"]
                rows = [fit_year(year, crop, weather, model.storage, model.farm["irrigation"]["supply_fraction"],
                                 model.policy, frost_free) for year in window["years"]]
                benefits = benefit_summary(model, index, rows, weather, window)
                fit.append({"crop_id": crop_id, "crop": crop["display_name"], "local_catalog_seasons": local_labels,
                            "parameters": {field: crop[field] for field in (
                                "season_length_days", "water_need_mm", "min_rain_mm", "max_rain_mm",
                                "min_temp_c", "max_temp_c", "heat_tolerance_c")},
                            "frost_free_required": frost_free,
                            "checks": summarize_checks(rows), "years": rows, "evidence": ledger,
                            "modeled_addition": benefits})
            window["fit"] = fit
        sensitivity.append({"offset": offset, "threshold": threshold, "windows": windows,
                            "run_count": len(runs), "runs": [
                                {"start": run[0].date().isoformat(), "end_exclusive": spans[run[-1]].date().isoformat(),
                                 "qa_composites": len(run)} for run in runs]})
    for window in next(row for row in sensitivity if row["offset"] == 0)["windows"]:
        slots = set(window["recurrent_anchor_doys"])
        window["threshold_stable"] = bool(slots) and all(
            any(slots.intersection(other["recurrent_anchor_doys"]) for other in row["windows"])
            for row in sensitivity if row["offset"] != 0)
    timeline = []
    for doy, values in series.groupby(series.index.day_of_year):
        valid = values.dropna()
        timeline.append({"doy": int(doy), "qa_composites": len(valid),
                         "ndvi": float(valid.median()) if len(valid) else None})
    ndvi_evidence = evidence([source("QA-valid MODIS NDVI", "nasa_measured", MODIS_SOURCE)], grades)
    window_evidence = evidence([
        *ndvi_evidence["inputs"],
        source("P5 low NDVI threshold", "assumption", "docs/decisions.md, P5; " + DESIGN),
        source("Window timing, support and recurrence rules", "assumption", config["source"]),
    ], grades, flags)
    return {"farm_id": model.farm["farm_id"], "label": "illustrative; validate locally",
            "years": sorted({day.year for day in spans}), "config": config, "flags": flags,
            "qa_composites": int(series.count()), "timeline": timeline, "sensitivity": sensitivity,
            "annual_ndvi": [{"year": int(day.year), "doy": int(day.day_of_year),
                             "date": day.date().isoformat(), "ndvi": float(value) if pd.notna(value) else None}
                            for day, value in series.items()],
            "evidence": {"ndvi": ndvi_evidence, "window": window_evidence},
            "threshold_source": "docs/decisions.md P5; " + DESIGN}


def build(root=ROOT):
    config = json.loads((root / "config/opportunity_windows.json").read_text())
    grades = json.loads((root / "config/evidence_grades.json").read_text())
    processed = root / "data/processed"
    for farm in json.loads((root / "config/farms.json").read_text()):
        farm_id = farm["farm_id"]
        climate = pd.read_parquet(processed / f"climate_{farm_id}.parquet")
        model = preload(farm, root=root, climate=climate.set_index("date"))
        results = compute(model, pd.read_csv(processed / f"ndvi_long_{farm_id}.csv"), climate,
                          composite_spans(farm, LONG_MODIS_YEARS), config, grades)
        write_json(processed / f"opportunity_windows_{farm_id}.json", results)
        print(farm_id, [(row["threshold"], row["run_count"], len(row["windows"]))
                        for row in results["sensitivity"]], flush=True)


if __name__ == "__main__":
    build()
