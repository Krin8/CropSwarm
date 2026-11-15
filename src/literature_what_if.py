"""Run P35 sensitivity cases in memory and write only a separate audit artifact."""

import json
from dataclasses import replace

import numpy as np
from threadpoolctl import threadpool_limits

from src.crops import load_crops
from src.literature_check import KS_TRANSITIONS, REFERENCES, converted_n_bounds
from src.optimizer import allowed_layers, enumerate_canonical_rotations
from src.precompute_cache import write_json
from src.scoring import METRICS, ROOT, preload, score_rotations

OUTPUT = "literature_what_if_p35.json"
EPSILON = 1e-10
KANSAS = "us_high_plains_b"


def scenarios(refs):
    cases = []
    for crop in ("chickpea", "pigeonpea"):
        low, high, source = refs["parameter_ranges"]["n_credit_kg_ha"][crop]
        for value in (low, high):
            cases.append({"id": f"{crop}_credit_{value}", "kind": "catalog", "crop": crop,
                          "field": "n_credit_kg_ha", "value": value, "source": source})
    evidence = refs["effects"]["sorghum_early_water"]
    for value in evidence["inch"]:
        millimetres = value * refs["conversion"]["inch_to_mm"]
        cases.append({"id": f"sorghum_water_{millimetres:g}", "kind": "catalog", "crop": "sorghum",
                      "field": "water_need_mm", "value": millimetres, "source": evidence["source"]})
    for key, (crop, successors, _) in KS_TRANSITIONS.items():
        evidence = refs["effects"][key]
        value, _ = converted_n_bounds(evidence["lb_ac"], refs)
        cases.append({"id": key, "kind": "transition_credit", "crop": crop, "successors": successors,
                      "value": value, "source": evidence["source"], "farm": KANSAS})
    cases.append({"id": "ks_sorghum_wheat_tan_spot_direction", "kind": "transition_risk",
                  "crop": "sorghum", "successors": ("winter_wheat",), "value": 0,
                  "source": "bockus", "farm": KANSAS})
    return cases


def revised_model(model, scenario, root=ROOT):
    if scenario["kind"] != "catalog":
        return model
    crop_id, field, value = (scenario[key] for key in ("crop", "field", "value"))
    if field == "n_credit_kg_ha":
        credits = model.credits.copy()
        credits[model.ids.index(crop_id)] = value
        return replace(model, credits=credits, nitrogen_bounds=(model.nitrogen_bounds[0], float(credits.max())))
    crops = {**model.crops, crop_id: {**model.crops[crop_id], field: value}}
    return preload(model.farm, root=root, crops=crops)


def scores_for(model, rotations, scenario=None):
    raw, scores, _ = score_rotations(model, rotations)
    if not len(rotations) or scenario is None or scenario["kind"] == "catalog":
        return raw, scores

    previous = np.roll(rotations, 1, axis=1)
    crop = model.ids.index(scenario["crop"])
    successors = [model.ids.index(key) for key in scenario["successors"]]
    transition_share = ((previous == crop) & np.isin(rotations, successors)).mean(axis=1)
    if scenario["kind"] == "transition_credit":
        nitrogen = METRICS.index("nitrogen")
        raw[:, nitrogen] += transition_share * (scenario["value"] - model.credits[crop])
        low, high = model.nitrogen_bounds
        scores[:, nitrogen] = np.clip((raw[:, nitrogen] - low) / (high - low), 0, 1)
    elif scenario["kind"] == "transition_risk":
        risk = METRICS.index("risk")
        raw[:, risk] += transition_share * (scenario["value"] - model.policy["same_family_risk_share"])
        scores[:, risk] = np.clip(1 - raw[:, risk], 0, 1)
    else:
        raise ValueError(f"Unknown P35 scenario {scenario['kind']}")
    return raw, scores


def rotation_matrix(model, entries):
    return np.array([[model.ids.index(crop) for year in entry["crop_ids"] for crop in year]
                     for entry in entries])


def exact_scores(model, saved, scenario=None):
    layers = allowed_layers(model, saved["horizon_years"])
    rotations = enumerate_canonical_rotations(layers, len(model.season_labels))
    _, scores = scores_for(model, rotations, scenario)
    return rotations, scores


def objective_summary(model, before, after, weights):
    before_rotations, before_scores = before
    after_rotations, after_scores = after
    old, new = before_scores @ weights, after_scores @ weights
    old_best, new_best = float(old.max()), float(new.max())
    old_sequence = before_rotations[np.flatnonzero(old >= old_best - EPSILON)[0]]
    new_sequence = after_rotations[np.flatnonzero(new >= new_best - EPSILON)[0]]
    match = np.all(after_rotations == old_sequence, axis=1)
    still_optimal = bool(np.any(match & (new >= new_best - EPSILON)))
    return {"old_score": old_best, "scenario_score": new_best, "old_winner_still_optimal": still_optimal,
            "old_sequence": [model.ids[i] for i in old_sequence],
            "scenario_sequence": [model.ids[i] for i in new_sequence],
            "old_ties": int(np.sum(old >= old_best - EPSILON)), "scenario_ties": int(np.sum(new >= new_best - EPSILON))}


def assess(model, saved, variants, presets, root=ROOT):
    weights = {name: np.array([item[key] for key in METRICS]) for name, item in presets.items()}
    published = saved["strategies"]
    sequences = rotation_matrix(model, published)
    before = exact_scores(model, saved)
    old_raw, old_scores = scores_for(model, sequences)
    if len(before[0]) != saved["feasible_count"]:
        raise ValueError("Nominal search space differs from saved verification")
    for name, weight in weights.items():
        if not np.isclose((before[1] @ weight).max(), saved["verification"][name]["exact_score"], atol=EPSILON, rtol=0):
            raise ValueError("Nominal optimum differs from saved verification")
    for i, entry in enumerate(published):
        expected = np.array([entry["metrics"][name]["score"] for name in METRICS])
        if not np.allclose(old_scores[i], expected, atol=EPSILON, rtol=0):
            raise ValueError("Nominal displayed scores differ from the saved shortlist")

    outcomes = {}
    for scenario in variants:
        farm = model.farm["farm_id"]
        if scenario.get("farm", farm) != farm:
            continue
        revised = revised_model(model, scenario, root)
        after = exact_scores(revised, saved, scenario)
        new_raw, new_scores = scores_for(revised, sequences, scenario)

        shortlist = {}
        for name, weight in weights.items():
            old_objective, new_objective = old_scores @ weight, new_scores @ weight
            shortlist[name] = {"old": old_objective.tolist(), "scenario": new_objective.tolist(),
                               "old_order": np.argsort(-np.round(old_objective, 10), kind="stable").tolist(),
                               "scenario_order": np.argsort(-np.round(new_objective, 10), kind="stable").tolist()}
        deltas = []
        for i, entry in enumerate(published):
            raw_delta, score_delta = new_raw[i] - old_raw[i], new_scores[i] - old_scores[i]
            deltas.append({"strategy_id": entry["strategy_id"],
                           "raw": dict(zip(METRICS, raw_delta.tolist(), strict=True)),
                           "score": dict(zip(METRICS, score_delta.tolist(), strict=True))})
        outcomes[scenario["id"]] = {"nominal_count": len(before[0]), "scenario_count": len(after[0]),
                                    "shortlist_metric_deltas": deltas, "fixed_shortlist_order": shortlist,
                                    "exact": {name: objective_summary(model, before, after, weight)
                                              for name, weight in weights.items()}}
    return outcomes


def build(root=ROOT):
    def read(path):
        return json.loads((root / path).read_text())

    refs = read(REFERENCES)
    variants = scenarios(refs)
    presets = read("config/weights_presets.json")["presets"]
    crops = load_crops(root / "data/crops.csv")
    with threadpool_limits(limits=1):
        reports = {farm["farm_id"]: assess(preload(farm, root=root, crops=crops),
                                          read(f"data/processed/strategies_{farm['farm_id']}.json"),
                                          variants, presets, root)
                   for farm in read("config/farms.json")}
    report = {"label": "Illustrative sensitivity only, validate locally",
              "design": {"reference": REFERENCES, "tolerance": EPSILON, "tie_break": "first canonical rotation within tolerance",
                         "method": "One change at a time, exact search and frozen displayed shortlist. See docs/literature_check.md.",
                         "note": "Regional catalog endpoints are transfer sensitivity cases. Kansas predecessor cases apply only in Kansas."},
              "scenarios": variants, "farms": reports}
    write_json(root / "data/processed" / OUTPUT, report)
    return report


if __name__ == "__main__":
    build()
