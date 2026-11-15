"""P43 transition-specific overlays for the immutable CropSwarm scoring engine."""

from dataclasses import asdict, dataclass
from functools import lru_cache
from itertools import product
import json

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from threadpoolctl import threadpool_limits

from src.crops import load_crops
from src.literature_check import REFERENCES, converted_n_bounds
from src.optimizer import allowed_layers, canonical_cycle, enumerate_canonical_rotations
from src.precompute_cache import write_json
from src.scoring import METRICS, ROOT, baseline_indices, crop_windows, daily_water_deficit, preload, score_rotations
from src.sensitivity import apply_values, inventory, joint_samples

KANSAS = "us_high_plains_b"
PLAN = "docs/p43_plan.md"
OUTPUT = "literature_variant_p43.json"
NUMERICAL_TOLERANCE = 1e-12  # config/tie_diagnosis.json, checked at build time
WHEAT = "winter_wheat"


@dataclass(frozen=True)
class Variant:
    nitrogen: bool
    water_mm: int
    disease: bool

    @property
    def key(self):
        return "_".join(part for part in ("N" if self.nitrogen else "",
                                          f"W{self.water_mm}" if self.water_mm else "",
                                          "D" if self.disease else "") if part) or "original"


def design(refs):
    refs_effect = refs["effects"]
    cold, _ = converted_n_bounds(refs_effect["ks_soy_wheat"]["lb_ac"], refs)
    warm, _ = converted_n_bounds(refs_effect["ks_soy_warm_cereal"]["lb_ac"], refs)
    water = refs_effect["legume_pa_water"]
    wet, dry = max(water["legume_mm"]), min(water["legume_mm"])
    reductions = [water["fallow_mm"] - wet, water["fallow_mm"] - dry]
    reductions.insert(1, sum(reductions) // 2)
    tan = refs_effect["tan_spot"]
    observed = 1 - np.array(tan["rotation_no_till_pct"]) / np.array(tan["continuous_no_till_pct"])
    variants = [Variant(nitrogen, mm, disease)
                for mm, nitrogen, disease in product([0, *reductions], (False, True), (False, True))]
    evidence = [
        {"input": "Soybean N credit by successor", "value": f"{cold} before wheat, {warm} kg N/ha before maize, sorghum or sunflower",
         "grade": "literature", "application_grade": "assumption, validate locally",
         "source": refs["sources"]["kstate"], "limitation": "Kansas extension fertilizer-equivalent credit."},
        {"input": "Loss of starting water after legumes", "value": f"{', '.join(map(str, reductions))} mm after legumes",
         "grade": "literature", "application_grade": "assumption, validate locally",
         "source": refs["sources"][water["source"]], "limitation": "Deep profile observations, translated by a reserve calculation."},
        {"input": "Sorghum break for wheat tan spot", "value": f"{np.median(observed):.1%} proportional penalty reduction",
         "grade": "literature", "application_grade": "assumption, validate locally",
         "source": refs["sources"][tan["source"]], "limitation": "Date-median relative severity reduction mapped onto a score index."},
    ]
    return variants, dict(cold=cold, warm=warm, reserve=water["fallow_mm"],
                          disease_reduction=float(np.median(observed)),
                          disease_observed_range=[float(observed.min()), float(observed.max())]), evidence


def corrected_water(deficit, demand, supply, reserve, reduction):
    """Paired one-time reserve loss added to the original shallow-bucket deficit."""
    extra = np.maximum(0, deficit - (reserve - reduction)) - np.maximum(0, deficit - reserve)
    fraction_unserved = 1 - supply
    return np.minimum(deficit + extra, demand) * fraction_unserved


@dataclass
class Overlay:
    water_delta: np.ndarray
    water_fraction_delta: np.ndarray
    water_blocked: np.ndarray
    nitrogen_delta: np.ndarray
    disease_delta: np.ndarray


def transitions(model, settings, reductions):
    """Cache all draw-specific slot-by-crop water corrections for a legume preceding wheat."""
    wheat = model.ids.index(WHEAT)
    soy = model.ids.index("soybean")
    warm = [model.ids.index(crop) for crop in ("maize", "sorghum", "sunflower")]
    sorghum = model.ids.index("sorghum")
    legumes = np.array([row["is_legume"] for row in model.crops.values()])
    nitrogen = np.zeros((len(model.ids), len(model.ids)))
    nitrogen[soy, wheat] = settings["cold"] - model.credits[soy]
    nitrogen[soy, warm] = settings["warm"] - model.credits[soy]
    disease = np.zeros_like(nitrogen)
    disease[sorghum, wheat] = -model.policy["same_family_risk_share"] * settings["disease_reduction"]

    water_rows = []
    crop = model.crops[WHEAT]
    demand = crop["water_need_mm"]
    supply = model.farm["irrigation"]["supply_fraction"]
    for slot in range(len(model.season_labels)):
        windows = model.histories[slot, wheat]
        rain = np.array([row[:, 0] for row in windows.values()]) if windows else np.empty((0, 0))
        water_rows.append(daily_water_deficit(rain, demand, model.storage))
    water = {}
    for reduction in reductions:
        delta, delta_fraction = np.zeros(model.suitable.shape), np.zeros(model.suitable.shape)
        blocked = np.zeros(model.suitable.shape, dtype=bool)
        for slot, deficits in enumerate(water_rows):
            if len(deficits) and demand and reduction:
                corrected = corrected_water(deficits, demand, supply, settings["reserve"], reduction)
                delta[slot, wheat] = (corrected - deficits * (1 - supply)).mean()
                delta_fraction[slot, wheat] = delta[slot, wheat] / demand
                blocked[slot, wheat] = np.median(corrected / demand) > model.policy["max_median_unmet_water_fraction"]
        water[reduction] = delta, delta_fraction, blocked
    return legumes, nitrogen, disease, water


class Batch:
    """Score one fixed rotation batch and keep reusable transition deltas."""

    def __init__(self, model, rows, pairs=None):
        self.model = model
        self.rows = rows
        self.raw, self.scores, self.warnings = score_rotations(model, rows)
        self.previous = np.roll(rows, 1, axis=1)
        self.slots = np.arange(rows.shape[1]) % len(model.season_labels)
        self.overlays = {}
        if pairs is not None:
            legumes, nitrogen, disease, water = pairs
            self.nitrogen = nitrogen[self.previous, rows].mean(axis=1)
            self.disease = disease[self.previous, rows].mean(axis=1)
            previous_legume = legumes[self.previous]
            for mm, (delta, fraction, blocked) in water.items():
                self.overlays[mm] = Overlay(
                    (delta[self.slots, rows] * previous_legume).mean(axis=1),
                    (fraction[self.slots, rows] * previous_legume).mean(axis=1),
                    blocked[self.slots, rows] & previous_legume, self.nitrogen, self.disease)

    def evaluate(self, variant):
        if not self.overlays or variant.key == "original":
            return self.raw, self.scores, self.warnings
        correction = self.overlays[variant.water_mm]
        raw, scores = self.raw.copy(), self.scores.copy()
        flags = self.warnings.copy()
        if variant.nitrogen:
            i = METRICS.index("nitrogen")
            raw[:, i] += correction.nitrogen_delta
            low, high = self.model.nitrogen_bounds
            scores[:, i] = np.clip((raw[:, i] - low) / (high - low), 0, 1)
        if variant.water_mm:
            i = METRICS.index("water")
            raw[:, i] += correction.water_delta
            scores[:, i] = np.clip(scores[:, i] - correction.water_fraction_delta, 0, 1)
            flags["irrigation_shortfall"] = (flags["irrigation_shortfall"]
                                            | (correction.water_blocked & self.model.planting_windows[self.slots, self.rows]))
        if variant.disease:
            i = METRICS.index("risk")
            raw[:, i] += correction.disease_delta
            scores[:, i] = np.clip(1 - raw[:, i], 0, 1)
        return raw, scores, flags


def eligible(flags):
    return ~np.logical_or.reduce(list(flags.values())).any(axis=1)


def crop_sequence(model, row):
    slots = len(model.season_labels)
    ids = [model.ids[i] for i in row]
    return [ids[start:start + slots] for start in range(0, len(ids), slots)]


def ranking(values, mask, tolerance):
    if not mask.any():
        raise ValueError("No feasible canonical alternative in a P43 nominal comparison")
    objective = values[mask]
    best = objective.max()
    first = int(np.flatnonzero(mask)[objective.argmax()])
    near = mask & (values >= best - tolerance)
    tied = mask & (values >= best - NUMERICAL_TOLERANCE)
    gap = float(best - np.partition(objective, -2)[-2]) if len(objective) > 1 else None
    return first, float(best), near, int(tied.sum()), gap


def compare_rankings(model, rows, original, revised, common_mask, tolerance):
    old, new = original, revised
    old_mask = np.ones(len(rows), dtype=bool)
    old_pick, old_max, old_near, old_ties, old_gap = ranking(old, old_mask, tolerance)
    new_pick, new_max, new_near, new_ties, new_gap = ranking(new, common_mask, tolerance)
    a, b = old[common_mask], new[common_mask]
    rank = None if len(a) < 2 or np.ptp(a) == 0 or np.ptp(b) == 0 else float(spearmanr(a, b).statistic)
    return {"original_rotation": crop_sequence(model, rows[old_pick]),
            "variant_rotation": crop_sequence(model, rows[new_pick]),
            "original_score": old_max, "variant_score": new_max, "label_changed": old_pick != new_pick,
            "original_still_optimal": bool(common_mask[old_pick] and new[old_pick] >= new_max - NUMERICAL_TOLERANCE),
            "rank_spearman": rank, "common_count": int(common_mask.sum()), "excluded_count": int((~common_mask).sum()),
            "added_count": 0, "original_exact_ties": old_ties, "variant_exact_ties": new_ties,
            "original_top_two_gap": old_gap, "variant_top_two_gap": new_gap,
            "original_near_top": int(old_near.sum()), "variant_near_top": int(new_near.sum()),
            "entered_near_top": int((new_near & ~old_near).sum()), "left_near_top": int((old_near & ~new_near).sum()),
            "near_tie_appeared": bool(old_gap is not None and old_gap > tolerance and new_gap is not None and new_gap <= tolerance),
            "near_tie_disappeared": bool(old_gap is not None and old_gap <= tolerance and
                                         (new_gap is None or new_gap > tolerance))}


def shortlist_deltas(original, revised, identifiers):
    raw, scores, flags = revised
    return [{
        "strategy": label,
        "raw": dict(zip(METRICS, (raw[i] - original.raw[i]).tolist(), strict=True)),
        "normalized": dict(zip(METRICS, (scores[i] - original.scores[i]).tolist(), strict=True)),
        "flags": {key: np.flatnonzero(mask[i]).tolist() for key, mask in flags.items()},
    } for i, label in enumerate(identifiers)]


def rotation_pool(model, years, enumerate_rows):
    layers = tuple(tuple(layer) for layer in allowed_layers(model, years))
    return enumerate_rows(layers)


def nominal(model, saved, variants, pairs, weights, tolerance, enumerate_rows):
    rotations = rotation_pool(model, saved["horizon_years"], enumerate_rows)
    strategies = saved["strategies"]
    short_rows = np.array([[model.ids.index(crop) for year in row["crop_ids"] for crop in year]
                           for row in strategies])
    short = Batch(model, short_rows, pairs)
    exact = Batch(model, rotations, pairs)
    if len(rotations) != saved["feasible_count"] or not eligible(exact.warnings).all():
        raise ValueError("Original P43 feasibility differs from saved exact search")
    for i, row in enumerate(strategies):
        for key, actual in (("score", short.scores), ("value", short.raw)):
            from_saved = [row["metrics"][metric][key] for metric in METRICS]
            np.testing.assert_allclose(actual[i], from_saved, atol=1e-10, rtol=0)
    old = {key: exact.scores @ weight for key, weight in weights.items()}
    for key, values in old.items():
        np.testing.assert_allclose(values.max(), saved["verification"][key]["exact_score"], atol=1e-10, rtol=0)
    result = {}
    for variant in variants:
        _, scores, flags = exact.evaluate(variant)
        mask = eligible(flags)
        result[variant.key] = {
            "presets": {key: compare_rankings(model, rotations, old[key], scores @ weight, mask, tolerance)
                        for key, weight in weights.items()},
            "shortlist": shortlist_deltas(short, short.evaluate(variant), [row["strategy_id"] for row in strategies]),
        }
    return result


def draw_outcomes(model, years, variants, pairs, weights, enumerate_rows, tolerance, incumbent=None):
    """Use P22's baseline-first convention and feasibility for the nominal incumbent."""
    rotations = rotation_pool(model, years, enumerate_rows)
    baseline = canonical_cycle(baseline_indices(model, years), len(model.season_labels))
    rows = np.vstack([baseline, rotations])
    batch = Batch(model, rows, pairs)
    output = {}
    for variant in variants:
        _, scores, flags = batch.evaluate(variant)
        mask = eligible(flags)
        mask[0] = True
        winner_scores = scores[mask]
        selected = {}
        ref_batch = None
        if incumbent is not None:
            reference = np.array([incumbent[variant.key][key]["rotation"] for key in weights])
            ref_batch = Batch(model, reference, pairs)
            _, ref_scores, ref_flags = ref_batch.evaluate(variant)
            ref_eligible = eligible(ref_flags) | np.all(reference == baseline, axis=1)
        for i, (name, weight) in enumerate(weights.items()):
            objective = winner_scores @ weight
            first = int(objective.argmax())
            chosen = rows[mask][first]
            result = {"rotation": chosen, "top": float(objective[first])}
            if ref_batch is not None:
                changed = not np.array_equal(chosen, reference[i])
                result.update(label_changed=changed, material_change=bool(changed and
                              (not ref_eligible[i] or objective[first] - ref_scores[i] @ weight > tolerance)))
            selected[name] = result
        output[variant.key] = selected
    return output


def p22_rates(model, builder, samples, variants, settings, reductions, weights, years, nearest, saved, enumerate_rows):
    pairs = transitions(model, settings, reductions)
    reference = draw_outcomes(model, years, variants, pairs, weights, enumerate_rows, nearest)
    counts = {v.key: {name: np.zeros(3, dtype=int) for name in weights} for v in variants}
    for sample in samples:
        drawn = builder(sample)
        result = draw_outcomes(drawn, years, variants, transitions(drawn, settings, reductions),
                               weights, enumerate_rows, nearest, reference)
        for key, presets in result.items():
            for name, item in presets.items():
                counts[key][name] += [item["label_changed"], item["material_change"],
                                      not np.array_equal(item["rotation"], result["original"][name]["rotation"])]
    records = {}
    for key, row in counts.items():
        presets = {}
        for name, (changed, material, disagreement) in row.items():
            n = len(samples)
            base = saved["presets"][name]
            change_rate, material_rate = changed / n, material / n
            winner = crop_sequence(model, reference[key][name]["rotation"])
            if key == "original":
                if (winner != base["reference_winner"]
                        or not np.allclose([change_rate, material_rate],
                                           [base["joint"]["winner_change_fraction"], base["joint"]["material_change_fraction"]],
                                           atol=NUMERICAL_TOLERANCE, rtol=0)):
                    raise ValueError(f"Original P22 draw result differs for {name}")
            presets[name] = {"draws": n, "reference_rotation": winner,
                             "winner_change_fraction": float(change_rate), "material_change_fraction": float(material_rate),
                             "paired_disagreement_fraction": float(disagreement / n),
                             "winner_change_delta": float(change_rate - base["joint"]["winner_change_fraction"]),
                             "material_change_delta": float(material_rate - base["joint"]["material_change_fraction"])}
        records[key] = presets
    return records


def unchanged_p22(variants, saved):
    return {variant.key: {name: {"draws": row["joint"]["evaluations"],
                                "reference_rotation": row["reference_winner"],
                                "winner_change_fraction": row["joint"]["winner_change_fraction"],
                                "material_change_fraction": row["joint"]["material_change_fraction"],
                                "paired_disagreement_fraction": 0.0, "winner_change_delta": 0.0,
                                "material_change_delta": 0.0}
                          for name, row in saved["presets"].items()} for variant in variants}


def build_farm(root, farm, read, crops, variants, settings, weights, config):
    farm_id = farm["farm_id"]
    path = root / "data/processed"
    seasons = read(f"data/processed/seasons_{farm_id}.json")
    climate = pd.read_parquet(path / f"climate_{farm_id}.parquet").set_index("date")

    @lru_cache(maxsize=256)
    def lookup(start, length):
        return crop_windows(climate, start, length)

    model = preload(farm, root=root, crops=crops, season_calendar=seasons, climate=climate, window_lookup=lookup)
    saved = read(f"data/processed/strategies_{farm_id}.json")
    saved_p22 = read(f"data/processed/sensitivity_{farm_id}.json")
    if config != saved_p22["design"] or saved["horizon_years"] != saved_p22["horizon_years"]:
        raise ValueError(f"P43 settings differ from saved P22 for {farm_id}")
    slots = len(model.season_labels)

    @lru_cache(maxsize=8)
    def enumerate_rows(layers):
        return enumerate_canonical_rotations([np.asarray(layer, dtype=int) for layer in layers], slots)

    reductions = sorted({variant.water_mm for variant in variants})
    if farm_id != KANSAS:
        results = nominal(model, saved, variants[:1], None, weights, config["near_tie_gap"], enumerate_rows)
        results = dict.fromkeys((v.key for v in variants), results["original"])
        rates = unchanged_p22(variants, saved_p22)
    else:
        results = nominal(model, saved, variants, transitions(model, settings, reductions),
                          weights, config["near_tie_gap"], enumerate_rows)
        inputs = inventory(model, seasons, read("config/evidence_grades.json"), config)
        if json.loads(json.dumps([asdict(item) for item in inputs])) != saved_p22["inputs"]:
            raise ValueError("P43 Kansas P22 input identities differ from the saved stream")
        draws = joint_samples(inputs, config)

        def draw_model(draw):
            test_farm, test_crops, policy, calendar = apply_values(model, seasons, inputs, draw)
            return preload(test_farm, root=root, crops=test_crops, policy=policy, season_calendar=calendar,
                           climate=climate, window_lookup=lookup)

        rates = p22_rates(model, draw_model, draws, variants, settings, reductions, weights,
                          saved["horizon_years"], config["near_tie_gap"], saved_p22, enumerate_rows)
    return {"name": farm["name"], "benchmark": farm_id == KANSAS,
            "benchmark_label": "Kansas literature benchmarks" if farm_id == KANSAS else "no benchmark",
            "nominal": results, "p22": rates}


def build(root=ROOT, output=None):
    def read(path):
        return json.loads((root / path).read_text())

    variants, settings, evidence = design(read(REFERENCES))
    config = read("config/sensitivity.json")
    if read("config/tie_diagnosis.json")["exact_metric_tolerance"] != NUMERICAL_TOLERANCE:
        raise ValueError("P43 expects the preregistered numerical tolerance")
    weights = {key: np.array([row[metric] for metric in METRICS])
               for key, row in read("config/weights_presets.json")["presets"].items()}
    crops = load_crops(root / "data/crops.csv")
    with threadpool_limits(limits=1):
        farms = {farm["farm_id"]: build_farm(root, farm, read, crops, variants, settings, weights, config)
                 for farm in read("config/farms.json")}
    result = {"label": "illustrative, validate locally", "plan": PLAN,
              "design": {"near_tie": config["near_tie_gap"], "seed": config["seed"], "draws": config["joint_draws"],
                         **settings},
              "variants": [{"id": v.key, "nitrogen": v.nitrogen, "water_mm": v.water_mm, "disease": v.disease}
                           for v in variants], "evidence": evidence, "farms": farms}
    write_json(output if output is not None else root / "data/processed" / OUTPUT, result)
    return result


if __name__ == "__main__":
    build()
