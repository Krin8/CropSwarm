"""Offline P50 Sentinel-2 point-seasonality analysis from the cached scene witness."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
import json

import numpy as np
import pandas as pd

from src.precompute_cache import write_json
from src.scoring import ROOT
from src.diagnostics import BARE_NDVI, PROMINENCES, vegetation
from src.farm_validity import rainfall_consistent_peaks

OBSERVATIONS = "sentinel2_observations.json"
OUTPUT = "makueni_sentinel_p50.json"
YEARS = tuple(range(2019, 2024))
MIN_SCENES_PER_YEAR = 10
MIN_COMPOSITES_PER_YEAR = 8
ACCEPTED_SCL = {4, 5}
SOURCE = "Copernicus Sentinel-2 MSI Level-2A surface reflectance · Earth Search AWS Open Data STAC · 10 m NDVI"
SCL_SOURCE = "Copernicus Sentinel-2 L2A Scene Classification Layer · 20 m · codes 4 vegetation and 5 not-vegetated accepted"
THRESHOLD_SOURCE = "P5 low-greenness threshold NDVI < 0.25; design choice, validate locally"


def point_observations(payload: dict) -> tuple[dict[str, list[dict]], dict[str, dict]]:
    """Decode quality-screened NDVI and retain failed/masked request counts."""
    points = payload["points"]
    rows = {point["point_id"]: [] for point in points}
    annual = {point["point_id"]: {str(year): {
        "valid_scene_count": 0, "scenes_seen": 0, "failed_scene_count": 0,
        "scl_counts": Counter(), "masked_scl_counts": Counter(),
        "rejected_band_or_ndvi_counts": Counter(),
    } for year in YEARS} for point in points}
    for scene in payload["scenes"]:
        day = scene.get("date")
        if not day:
            continue
        year = int(day[:4])
        if year not in YEARS:
            continue
        year_text = str(year)
        for index, point in enumerate(points):
            counts = annual[point["point_id"]][year_text]
            counts["scenes_seen"] += 1
            if scene.get("status") != "ok":
                counts["failed_scene_count"] += 1
                continue
            scl = scene["scl"][index]
            if scl is None:
                counts["failed_scene_count"] += 1
                continue
            counts["scl_counts"][str(scl)] += 1
            if scl not in ACCEPTED_SCL:
                counts["masked_scl_counts"][str(scl)] += 1
                continue
            red_dn, nir_dn = scene["red_dn"][index], scene["nir_dn"][index]
            if red_dn is None or nir_dn is None:
                counts["rejected_band_or_ndvi_counts"]["missing_band"] += 1
                continue
            if red_dn == 0 or nir_dn == 0:
                counts["rejected_band_or_ndvi_counts"]["zero_DN"] += 1
                continue
            red = red_dn * scene["red_scale"] + scene["red_offset"]
            nir = nir_dn * scene["nir_scale"] + scene["nir_offset"]
            if red <= 0 or nir <= 0 or nir + red <= 0:
                counts["rejected_band_or_ndvi_counts"]["nonpositive_reflectance"] += 1
                continue
            ndvi = (nir - red) / (nir + red)
            if not -0.2 <= ndvi <= 1.0:
                counts["rejected_band_or_ndvi_counts"]["outside_valid_NDVI"] += 1
                continue
            counts["valid_scene_count"] += 1
            rows[point["point_id"]].append({"date": day, "year": year, "ndvi": float(ndvi),
                                             "scl": int(scl), "source": SOURCE})
    for point_id, years in annual.items():
        for year, counts in years.items():
            for key in ("scl_counts", "masked_scl_counts", "rejected_band_or_ndvi_counts"):
                counts[key] = dict(sorted(counts[key].items(), key=lambda row: int(row[0]) if row[0].isdigit() else row[0]))
    return rows, annual


def composite_frame(scene_rows: list[dict], years=YEARS) -> pd.DataFrame:
    """Aggregate valid scene NDVI into the preregistered 23 16-day P5 windows."""
    by_year_window: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for row in scene_rows:
        year = int(row["year"])
        day = date.fromisoformat(row["date"])
        window = min((day.timetuple().tm_yday - 1) // 16, 22)
        by_year_window[(year, window)].append(row)

    composites = []
    for year in years:
        for window in range(23):
            start = date(year, 1, 1) + timedelta(days=16 * window)
            selected = by_year_window[(year, window)]
            if selected:
                values = np.array([row["ndvi"] for row in selected])
                median = float(np.median(values))
                observation = min(selected, key=lambda row: (abs(row["ndvi"] - median), row["date"]))
                composites.append({"date": pd.Timestamp(start), "composite_date": observation["date"],
                                   "ndvi": median, "pixel_reliability": 0, "vi_quality": 0,
                                   "valid_scene_count": len(selected), "source": SOURCE})
            else:
                composites.append({"date": pd.Timestamp(start), "composite_date": start.isoformat(),
                                   "ndvi": 0.0, "pixel_reliability": 3, "vi_quality": 2062,
                                   "valid_scene_count": 0, "source": SOURCE})
    return pd.DataFrame(composites)


def point_summary(point: dict, rows: list[dict], annual_counts: dict, failed_scenes: list[dict]) -> dict:
    frame = composite_frame(rows)
    vegetation_rows, _ = vegetation(frame)
    p7 = rainfall_consistent_peaks(frame)
    annual = {}
    for year in YEARS:
        key = str(year)
        scenes = [row for row in rows if row["year"] == year]
        values = np.array([row["ndvi"] for row in scenes], dtype=float)
        valid_comp = frame[(frame.date.dt.year == year) & frame.pixel_reliability.eq(0)]
        p5 = vegetation_rows.get(key, {"peaks": {str(p): [] for p in PROMINENCES}, "good_composites": 0})
        peaks = {
            prominence: {"dates": p5["peaks"][str(prominence)],
                         "months": [int(value[5:7]) for value in p5["peaks"][str(prominence)]],
                         "count": len(p5["peaks"][str(prominence)])}
            for prominence in PROMINENCES
        }
        low_comp = valid_comp[valid_comp.ndvi < BARE_NDVI]
        low_scene = [row["date"] for row in scenes if row["ndvi"] < BARE_NDVI]
        annual[key] = {
            **annual_counts[key],
            "good_composites": int(p5["good_composites"]), "possible_composites": 23,
            "peaks": peaks,
            "unconstrained_two_or_more_peaks": peaks[0.12]["count"] >= 2,
            "p7": {"long_rain_peak_dates": p7[key]["long_rain_peaks"],
                   "short_rain_peak_dates": p7[key]["short_rain_peaks"],
                   "qualifies": p7[key]["two_rain_aligned_peaks"]},
            "scene_ndvi": {
                "minimum": None if not len(values) else float(values.min()),
                "maximum": None if not len(values) else float(values.max()),
                "amplitude_max_minus_min": None if not len(values) else float(values.max() - values.min()),
                "p90_minus_p10": None if not len(values) else float(np.percentile(values, 90) - np.percentile(values, 10)),
                "median": None if not len(values) else float(np.median(values)),
                "low_greenness_scene_count": sum(value < BARE_NDVI for value in values),
                "low_greenness_scene_share": None if not len(values) else float(np.mean(values < BARE_NDVI)),
                "low_greenness_dates": low_scene,
                "source": SOURCE,
            },
            "composite_ndvi": {
                "minimum": None if valid_comp.empty else float(valid_comp.ndvi.min()),
                "maximum": None if valid_comp.empty else float(valid_comp.ndvi.max()),
                "amplitude_max_minus_min": None if valid_comp.empty else float(valid_comp.ndvi.max() - valid_comp.ndvi.min()),
                "low_greenness_dates": [value.date().isoformat() for value in low_comp.date],
                "low_greenness_threshold": BARE_NDVI, "threshold_source": THRESHOLD_SOURCE,
                "source": SOURCE,
            },
            "sources": {"ndvi": SOURCE, "cloud_mask": SCL_SOURCE},
        }
    all_scene_values = np.array([row["ndvi"] for row in rows], dtype=float)
    annual_amplitudes = [row["scene_ndvi"]["amplitude_max_minus_min"] for row in annual.values()
                         if row["scene_ndvi"]["amplitude_max_minus_min"] is not None]
    annual_peaks = [row["peaks"][0.12]["count"] for row in annual.values()]
    return {
        **point, "annual": annual,
        "summary": {
            "mean_annual_peaks_0_12": float(np.mean(annual_peaks)),
            "median_annual_scene_amplitude": None if not annual_amplitudes else float(np.median(annual_amplitudes)),
            "median_annual_min_scene_ndvi": None if not rows else float(np.median([
                row["scene_ndvi"]["minimum"] for row in annual.values() if row["scene_ndvi"]["minimum"] is not None])),
            "valid_scene_low_greenness_share": None if not len(all_scene_values) else float(np.mean(all_scene_values < BARE_NDVI)),
            "p7_qualifying_years": sum(row["p7"]["qualifies"] for row in annual.values()),
            "p5_two_or_more_peak_years": sum(row["unconstrained_two_or_more_peaks"] for row in annual.values()),
            "valid_sentinel_observations": len(rows),
            "failed_scenes": failed_scenes,
            "source": SOURCE,
        },
    }


def observation_gate(annual_counts: dict, points: list[dict]) -> dict:
    cells = []
    for point in points:
        for year in YEARS:
            counts = annual_counts[point["point_id"]][str(year)]
            cells.append({"point_id": point["point_id"], "year": year,
                          "valid_scenes": counts["valid_scene_count"],
                          "minimum_scenes": 10,
                          "valid_composites": None,
                          "minimum_composites": 8})
    return {"minimum_valid_scenes_per_year": MIN_SCENES_PER_YEAR,
            "minimum_valid_composites_per_year": MIN_COMPOSITES_PER_YEAR,
            "counts": cells}


def group_summary(points: list[dict], group: str) -> dict:
    chosen = [row for row in points if row["group"] == group]
    metrics = ("mean_annual_peaks_0_12", "median_annual_scene_amplitude",
               "median_annual_min_scene_ndvi", "valid_scene_low_greenness_share", "p7_qualifying_years")

    def summarize_rows(rows):
        summary = {}
        for metric in metrics:
            values = [row["summary"][metric] for row in rows if row["summary"][metric] is not None]
            summary[metric] = {"median": float(np.median(values)) if values else None,
                               "range": [float(min(values)), float(max(values))] if values else None,
                               "mean": float(np.mean(values)) if values else None,
                               "unit": ("years" if metric == "p7_qualifying_years" else
                                        "share" if metric == "valid_scene_low_greenness_share" else
                                        "NDVI" if metric in ("median_annual_scene_amplitude",
                                                              "median_annual_min_scene_ndvi") else "peaks/year"),
                               "source": SOURCE}
        return summary

    subgroups = {}
    for subgroup in sorted({row["subgroup"] for row in chosen}):
        subgroups[subgroup] = {"point_count": sum(row["subgroup"] == subgroup for row in chosen),
                               "metrics": summarize_rows([row for row in chosen if row["subgroup"] == subgroup])}
    return {"point_count": len(chosen), "metrics": summarize_rows(chosen), "subgroups": subgroups}


def compare_study_points(points: list[dict], groups: dict[str, dict]) -> dict:
    """Compare five preregistered descriptors by reference min–max range count."""
    result = {}
    for point in points:
        if point["group"] != "study":
            continue
        group_hits = {}
        for group_name, group in groups.items():
            hits = []
            for metric, record in group["metrics"].items():
                value = point["summary"][metric]
                bounds = record["range"]
                if value is not None and bounds is not None and bounds[0] <= value <= bounds[1]:
                    hits.append(metric)
            group_hits[group_name] = {"in_range_count": len(hits), "metrics_in_range": hits}
        crop = group_hits["cropland_ref"]["in_range_count"]
        noncrop = group_hits["noncropland_ref"]["in_range_count"]
        result[point["point_id"]] = {
            "cropland_reference": group_hits["cropland_ref"], "noncropland_reference": group_hits["noncropland_ref"],
            "appearance": ("more like the cropland-agreed group" if crop > noncrop else
                           "more like the non-cropland group" if noncrop > crop else "overlaps both groups"),
            "comparison_rule": "Count of five point descriptors falling within each group's observed min–max range.",
            "source": SOURCE,
        }
    return result


def summarize(payload: dict, min_scenes=MIN_SCENES_PER_YEAR,
              min_composites=MIN_COMPOSITES_PER_YEAR) -> dict:
    rows, annual_counts = point_observations(payload)
    summaries = {}
    gate_rows = []
    for point in payload["points"]:
        point_id = point["point_id"]
        frame = composite_frame(rows[point_id])
        point_year = {}
        for year in YEARS:
            key = str(year)
            valid_composites = int(frame[(frame.date.dt.year == year) & frame.pixel_reliability.eq(0)].shape[0])
            point_year[key] = {**annual_counts[point_id][key], "valid_composites": valid_composites}
            counts = annual_counts[point_id][key]
            passes = counts["valid_scene_count"] >= min_scenes and valid_composites >= min_composites
            gate_rows.append({"point_id": point_id, "point_label": point.get("label", point_id),
                              "map_group": point.get("group", "unknown"),
                              "map_class": point.get("worldcover_class", "unknown"),
                              "year": year, "valid_scenes": counts["valid_scene_count"], "minimum_scenes": min_scenes,
                              "valid_composites": valid_composites, "minimum_composites": min_composites,
                              "scenes_seen": counts["scenes_seen"], "failed_scenes": counts["failed_scene_count"],
                              "scl_counts": counts["scl_counts"], "masked_scl_counts": counts["masked_scl_counts"],
                              "rejected_band_or_ndvi_counts": counts["rejected_band_or_ndvi_counts"],
                              "ndvi_source": SOURCE, "mask_source": SCL_SOURCE,
                              "passes": passes})
        annual_counts[point_id] = point_year
        failures = [scene for scene in payload["scenes"] if scene.get("status") != "ok"
                    and scene.get("date", "")[:4] in {str(year) for year in YEARS}]
        summaries[point_id] = {"point": point, "rows": rows[point_id], "counts": point_year,
                               "failed_scenes": failures}

    gate_pass = all(row["passes"] for row in gate_rows)
    report = {
        "farm_id": "kenya_makueni_north", "label": "illustrative, validate locally",
        "source": SOURCE, "cloud_mask_source": SCL_SOURCE,
        "catalog_attempts": payload.get("catalog_attempts", []),
        "chosen_catalog": payload.get("chosen_catalog"),
        "years": list(YEARS), "raw_item_count": payload.get("raw_item_count"),
        "unique_scene_dates": payload.get("unique_scene_dates"),
        "duplicate_items_removed": payload.get("duplicate_items_removed"),
        "minimum_observations": {"valid_scenes_per_year": min_scenes, "valid_16_day_composites_per_year": min_composites,
                                 "source": "design choice, docs/p50_plan.md"},
        "gate": {"passed": gate_pass, "counts": gate_rows},
        "scene_failures": [scene for scene in payload["scenes"] if scene.get("status") != "ok"],
        "failed_scene_count": sum(scene.get("status") != "ok" for scene in payload["scenes"]),
        "point_year_gate_failures": sum(not row["passes"] for row in gate_rows),
        "points": {},
        "interpretation_limit": "NDVI seasonality does not identify crop type, management or irrigation.",
    }
    if not gate_pass:
        report["status"] = "observation gate failed; do not interpret seasonality"
        return report

    point_results = []
    for point_id, entry in summaries.items():
        point_results.append(point_summary(entry["point"], entry["rows"], entry["counts"], entry["failed_scenes"]))
    groups = {group: group_summary(point_results, group)
              for group in ("cropland_ref", "noncropland_ref")}
    report["points"] = {row["point_id"]: row for row in point_results}
    report["groups"] = groups
    report["study_point_comparison"] = compare_study_points(point_results, groups)
    report["status"] = "observation gate passed; descriptive seasonality comparison"
    report["limits"] = [
        "The reference groups were selected using WorldCover and GLAD map labels, not verified field use.",
        "The 12 study and reference pixels are nearby and share Sentinel scenes and spatial climate; they are not independent samples.",
        "Ten-metre NDVI seasonality does not identify crop type, management or irrigation.",
        "Low greenness is not proof of bare soil. Cloud masking and valid-observation selection can affect seasonal summaries.",
        "Results describe 2019–2023 and do not change the farm status or any existing model output.",
    ]
    return report


def build(root=ROOT, output=None):
    payload_path = root / "data/raw/p50" / OBSERVATIONS
    payload = json.loads(payload_path.read_text())
    report = summarize(payload)
    access_path = root / "data/raw/p50/stac_access_check.json"
    if access_path.is_file():
        report["stac_access_check"] = json.loads(access_path.read_text())
    retry_path = root / "data/raw/p50/retrieval_attempt_summary.json"
    if retry_path.is_file():
        report["retrieval_attempt_summary"] = json.loads(retry_path.read_text())
    fallback_path = root / "data/raw/p50/fallback_access_summary.json"
    if fallback_path.is_file():
        report["fallback_access_summary"] = json.loads(fallback_path.read_text())
    report_path = output if output is not None else root / "data/processed" / OUTPUT
    write_json(report_path, report)
    return report


if __name__ == "__main__":
    result = build()
    print(f"P50 observation gate {'passed' if result['gate']['passed'] else 'failed'}.")
