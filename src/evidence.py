"""Conservative provenance shares for scoring dependencies, never score changes."""

import json
from pathlib import Path

from src.scoring import METRICS, ROOT

GRADES = ("nasa_measured", "nasa_modeled", "external_measured", "literature", "assumption")
ORDER = {"low": 0, "medium": 1, "high": 2}
FIELD_SOURCES = {
    "season_length_days": "season_length_source", "water_need_mm": "water_need_source",
    "min_rain_mm": "rain_source", "max_rain_mm": "rain_source",
    "min_temp_c": "thermal_source", "max_temp_c": "thermal_source",
    "heat_tolerance_c": "thermal_source", "n_credit_kg_ha": "n_credit_source",
    "n_demand_kg_ha": "n_demand_source", "cover_score": "cover_source",
    "relative_income_index": "income_source", "disease_family": "disease_family_source",
}
DIRECT_FIELDS = {
    "water": ("POWER.PRECTOTCORR", "soil.available_water_mm_0_30", "crop.water_need_mm",
              "crop.season_length_days", "farm.irrigation.supply_fraction", "season.calendar",
              "model.daily_water_bucket"),
    "nitrogen": ("crop.n_credit_kg_ha", "crop.n_demand_kg_ha", "model.nitrogen_normalization"),
    "erosion": ("POWER.PRECTOTCORR", "SRTM.mean_slope_pct", "crop.cover_score", "model.erosion_proxy"),
    "climate_fit": ("POWER.PRECTOTCORR", "POWER.T2M", "POWER.T2M_MAX", "crop.min_rain_mm",
                    "crop.max_rain_mm", "crop.min_temp_c", "crop.max_temp_c",
                    "crop.heat_tolerance_c", "crop.season_length_days", "season.calendar",
                    "policy.max_hot_day_fraction", "model.climate_screen"),
    "income": ("crop.relative_income_index",),
    "risk": ("crop.disease_family", "crop.season_length_days", "policy.same_family_risk_share",
             "policy.bare_slot_risk_share", "model.risk_rule"),
}


def crop_source_grade(source, config):
    """A citation with an explicit local-assumption qualifier stays an assumption."""
    if "assumption, validate locally" in source.lower():
        return "assumption"
    if any(url in source for url in config["verified_crop_source_urls"]):
        return "literature"
    return "assumption"


def label_for_shares(shares, config):
    assumption = shares["assumption"]
    supported = sum(shares[grade] for grade in GRADES if grade != "assumption")
    if assumption <= config["high_max_assumption_share"] and supported >= config["high_min_supported_share"]:
        return "high"
    if assumption <= config["medium_max_assumption_share"] and supported >= config["medium_min_supported_share"]:
        return "medium"
    return "low"


def cap_label(label, maximum):
    return min((label, maximum), key=ORDER.get)


def backtest_cap(backtest, config):
    """Farm-level baseline check is a limit on water and climate-fit labels only."""
    seasons = backtest["seasons"].values()
    assessable = sum(row["directional"]["assessable"] for row in seasons)
    consistent = sum(row["directional"]["consistent"] for row in seasons)
    largest_n = max((row["comparisons"]["deficit_fraction_vs_ndvi_peak"]["n"] for row in seasons), default=0)
    if assessable == 0:
        return "low", f"Back-test: 0 assessable directional comparisons (largest season n={largest_n})."
    if consistent / assessable < 0.5:
        return "low", f"Back-test: directionally consistent in {consistent}/{assessable} comparisons."
    if largest_n < config["backtest_small_n_below"]:
        return "medium", f"Back-test: {consistent}/{assessable} directionally consistent; largest season n={largest_n} is small."
    return "high", f"Back-test: {consistent}/{assessable} directionally consistent; this does not verify a field outcome."


def evidence_for_strategy(model, sequence, *, root=ROOT, config=None):
    """Return a per-metric input ledger and conservative label for one rotation."""
    if config is None:
        config = json.loads((root / "config/evidence_grades.json").read_text())
    processed = root / "data/processed"
    farm_id = model.farm["farm_id"]
    context = json.loads((processed / f"context_{farm_id}.json").read_text())
    backtest = json.loads((processed / f"backtest_{farm_id}.json").read_text())
    soil = context["soil"]["available_water_mm_0_30"]
    soil_source = model.soil_source
    if "assumption, validate locally" in soil_source.lower():
        soil_grade = "assumption"
    elif soil_source == soil["source"] and ("isric.org" in soil_source or "nrcs.usda.gov" in soil_source):
        soil_grade = "external_measured"
    else:
        soil_grade = "assumption"
    crop_ids = [model.ids[int(index)] for index in sequence]
    cap, backtest_reason = backtest_cap(backtest, config)
    flags = " ".join(model.farm.get("validation_flags", [])).lower()
    cropland_unverified = "cropland at exact point unverified" in flags
    secondary_tentative = "second crop season remains tentative" in flags
    spring_unexplained = "spring peak remains unexplained" in flags
    result = {}
    for metric, fields in DIRECT_FIELDS.items():
        inputs = []
        weight = 1 / len(fields)
        for field in fields:
            if field.startswith("crop."):
                crop_field = field.split(".", 1)[1]
                for crop_id in crop_ids:
                    source = model.crops[crop_id][FIELD_SOURCES[crop_field]]
                    inputs.append({"input": field, "crop_id": crop_id, "grade": crop_source_grade(source, config),
                                   "source": source, "weight": weight / len(crop_ids)})
            else:
                grade, source = {
                    "POWER.PRECTOTCORR": ("nasa_measured", "NASA POWER PRECTOTCORR; cached daily climate"),
                    "POWER.T2M": ("nasa_measured", "NASA POWER T2M; cached daily climate"),
                    "POWER.T2M_MAX": ("nasa_measured", "NASA POWER T2M_MAX; cached daily climate"),
                    "soil.available_water_mm_0_30": (soil_grade, soil_source),
                    "SRTM.mean_slope_pct": ("nasa_modeled", context["terrain"]["mean_slope_pct"]["source"]),
                    "farm.irrigation.supply_fraction": ("assumption", model.farm["irrigation"]["basis"]),
                    "season.calendar": ("assumption", model.farm["seasons_basis"]),
                    "policy.max_hot_day_fraction": ("assumption", "config/scoring.json; assumption, validate locally"),
                    "policy.same_family_risk_share": ("assumption", "config/scoring.json; assumption, validate locally"),
                    "policy.bare_slot_risk_share": ("assumption", "config/scoring.json; assumption, validate locally"),
                    "model.daily_water_bucket": ("assumption", "src/scoring.py daily_water_deficit; assumption, validate locally"),
                    "model.nitrogen_normalization": ("assumption", "src/scoring.py score_rotations; catalog-wide bounds; assumption, validate locally"),
                    "model.erosion_proxy": ("assumption", "src/scoring.py historical_metrics; simplified erosion proxy; assumption, validate locally"),
                    "model.climate_screen": ("assumption", "src/scoring.py historical_metrics; threshold screening rule; assumption, validate locally"),
                    "model.risk_rule": ("assumption", "src/scoring.py score_rotations; family and bare-slot proxy; assumption, validate locally"),
                }[field]
                inputs.append({"input": field, "grade": grade, "source": source, "weight": weight})
        shares = {grade: sum(item["weight"] for item in inputs if item["grade"] == grade) for grade in GRADES}
        label = label_for_shares(shares, config)
        reasons = []
        if metric in ("water", "climate_fit"):
            label = cap_label(label, cap)
            reasons.append(backtest_reason)
            if secondary_tentative:
                label = cap_label(label, "low")
                reasons.append("Second crop season remains tentative after NDVI screening.")
            if spring_unexplained:
                label = cap_label(label, "low")
                reasons.append("Kansas spring NDVI peak over CDL fallow remains unexplained.")
        if cropland_unverified:
            label = cap_label(label, "low")
            reasons.append("Cropland at this point is unverified; MCD12Q1 class 10 indicates grassland.")
        if "isric.org" in soil_source and metric == "water":
            label = cap_label(label, "medium")
            reasons.append("SoilGrids is a model prediction, not a field soil measurement.")
        result[metric] = {"shares": shares, "label": label, "inputs": inputs, "reasons": reasons,
                          "method": config["method"], "threshold_source": config["threshold_source"]}
    return {"metrics": result, "label": min((row["label"] for row in result.values()), key=ORDER.get),
            "method": config["method"], "threshold_source": config["threshold_source"]}


def main():
    """Refresh evidence annotations without rerunning or changing optimization scores."""
    from src.precompute_cache import write_json
    from src.scoring import preload

    config = json.loads((ROOT / "config/evidence_grades.json").read_text())
    for farm in json.loads((ROOT / "config/farms.json").read_text()):
        model = preload(farm)
        path = ROOT / "data/processed" / f"strategies_{farm['farm_id']}.json"
        result = json.loads(path.read_text())
        for strategy in result["strategies"]:
            sequence = [model.ids.index(crop_id) for year in strategy["crop_ids"] for crop_id in year]
            evidence = evidence_for_strategy(model, sequence, config=config)
            strategy["evidence_label"] = evidence["label"]
            for metric in METRICS:
                strategy["metrics"][metric]["evidence"] = evidence["metrics"][metric]
        write_json(path, result)
        print(farm["farm_id"], len(result["strategies"]), flush=True)


if __name__ == "__main__":
    main()
