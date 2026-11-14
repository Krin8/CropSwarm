"""Offline input sensitivity using the existing scoring and canonical exact search."""
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from functools import lru_cache
import json
import re

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from src.crops import load_crops
from src.evidence import FIELD_SOURCES, crop_source_grade
from src.optimizer import allowed_layers, canonical_cycle, enumerate_canonical_rotations
from src.precompute_cache import write_json
from src.scoring import METRICS, ROOT, baseline_indices, crop_windows, preload, score_rotations

WATER = "water_need_mm"
N_INPUTS = ("n_credit_kg_ha", "n_demand_kg_ha")
DURATION = "season_length_days"
ELIGIBILITY = "seasons_allowed"
SOURCE_RANGE = re.compile(r"(\d+(?:\.\d+)?)\s*[–-]\s*(\d+(?:\.\d+)?)\s*(mm|days)\b")
CHECKS = {
    WATER: "Confirm seasonal water needs for {crop}.",
    DURATION: "Confirm how long {crop} grows before harvest or termination.",
    "n_credit_kg_ha": "Check how much nitrogen {crop} leaves for the next crop.",
    "n_demand_kg_ha": "Check how much nitrogen {crop} needs.",
    "cover_score": "Check how well {crop} protects the soil.",
    "relative_income_index": "Check the relative income estimate for {crop}.",
    "min_rain_mm": "Check the minimum seasonal rainfall assumed for {crop}.",
    "max_rain_mm": "Check the maximum seasonal rainfall assumed for {crop}.",
    "min_temp_c": "Check the lower growing-season temperature limit for {crop}.",
    "max_temp_c": "Check the upper growing-season temperature limit for {crop}.",
    "heat_tolerance_c": "Check the daily heat threshold for {crop}.",
    ELIGIBILITY: "Confirm which seasons are suitable for planting {crop}.",
}
POLICY_CHECKS = {
    "calendar_extension_days": "Check how much later than the season end a crop can finish.",
    "max_median_unmet_water_fraction": "Check how much unmet water demand makes a crop unsuitable.",
    "max_hot_day_fraction": "Check how many hot days a crop can tolerate.",
    "same_family_risk_share": "Check the risk assigned to repeating crops from the same family.",
    "bare_slot_risk_share": "Check the risk assigned to leaving soil bare.",
}


@dataclass(frozen=True)
class Input:
    key: str
    question: str
    source: str
    grade: str
    target: tuple
    reference: object
    levels: tuple
    bounds: tuple | None = None
    integer: bool = False
    range_basis: str = "±20% of the reference; design choice"

    def draw(self, rng, change_probability):
        if self.bounds is None:
            if rng.random() >= change_probability:
                return self.reference
            return self.levels[int(rng.integers(len(self.levels)))]
        value = float(rng.uniform(*self.bounds))
        return int(round(value)) if self.integer else value


def numeric(key, question, source, grade, target, value, config, *, bounds=None, maximum=None):
    source_range = bounds is not None
    if bounds is None:
        spread = config["relative_spread"]
        bounds = (value - abs(value) * spread, value + abs(value) * spread)
    if maximum is not None:
        bounds = (max(0, bounds[0]), min(maximum, bounds[1]))
    integer = type(value) is int
    levels = np.linspace(*bounds, config["sweep_levels"])
    levels = tuple(sorted(set(map(int, np.rint(levels))) if integer else set(map(float, levels))))
    range_basis = "cited range" if source_range else f"±{config['relative_spread']:.0%}; design choice"
    return Input(key, question, source, grade, target, value,
                 tuple(x for x in levels if not np.isclose(x, value, atol=1e-12, rtol=0)),
                 tuple(bounds), integer, range_basis)


def inventory(model, seasons, evidence, config):
    """Build a factor for each applicable crop field, farm input and score policy."""
    farm = model.farm
    supply = farm["irrigation"]["supply_fraction"]
    water = numeric("irrigation", "Confirm how much irrigation water is available.",
                    farm["irrigation"]["basis"], "assumption", ("irrigation",), supply, config, maximum=1)
    if supply == 0:
        water = numeric(water.key, water.question, water.source, water.grade, water.target,
                        float(supply), config, bounds=(0, config["zero_irrigation_upper_fraction"]))
        water = replace(water, range_basis="one-sided check from zero; design choice")
    inputs = [water]
    if "assumption, validate locally" in farm["baseline_source"].lower():
        baseline = tuple(map(tuple, farm["baseline_rotation_cycle"]))
        choices = []
        for y, year in enumerate(baseline):
            for slot, original in enumerate(year):
                for i in np.flatnonzero(model.planting_windows[slot]):
                    replacement = model.ids[i]
                    if replacement != original:
                        updated = [list(row) for row in baseline]
                        updated[y][slot] = replacement
                        choices.append(tuple(map(tuple, updated)))
        inputs.append(Input("baseline", "Confirm which crops are already in the rotation.",
                            farm["baseline_source"], "assumption", ("baseline",), baseline,
                            tuple(choices), range_basis="one slot replaced using the reference season screen; design choice"))

    labels = set().union(*model.season_labels)
    for crop_id, crop in model.crops.items():
        applicable = tuple(label for label in crop[ELIGIBILITY] if label in labels)
        if crop[DURATION] == 0:
            continue
        name = crop["display_name"].lower()
        for field, source_key in FIELD_SOURCES.items():
            # Ineligible crops can still set the catalog-wide nitrogen normalization bounds.
            if field not in CHECKS or (not applicable and field not in N_INPUTS):
                continue
            source = crop[source_key]
            grade = crop_source_grade(source, evidence)
            if grade != "assumption" and field != WATER:
                continue
            value = crop[field]
            match = SOURCE_RANGE.search(source) if field in (WATER, DURATION) else None
            expected_unit = "mm" if field == WATER else "days"
            bounds = (tuple(map(float, match.groups()[:2])) if match and match[3] == expected_unit else None)
            maximum = 1 if field in ("cover_score", "relative_income_index") else None
            inputs.append(numeric(f"{crop_id}.{field}", CHECKS[field].format(crop=name), source, grade,
                                  ("crop", crop_id, field), value, config, bounds=bounds, maximum=maximum))
        if not applicable:
            continue
        # Screen uncertainty by withdrawing one current label at a time. Preserve labels for other sites.
        eligible = tuple(crop[ELIGIBILITY])
        inputs.append(Input(f"{crop_id}.{ELIGIBILITY}", CHECKS[ELIGIBILITY].format(crop=name),
                            crop["seasons_source"], "assumption", ("crop", crop_id, ELIGIBILITY), eligible,
                            tuple(tuple(x for x in eligible if x != label) for label in applicable),
                            range_basis="withdraw one listed local season; design choice"))
    for label, window in seasons["season_windows"].items():
        start, end = window["onset_month"], window["cessation_month"]
        length = (end - start) % 12 + 1
        span = max(1, int(round(length * config["relative_spread"])))
        source = f"{farm['seasons_basis']} | reference calendar: {window['source']}"
        for edge, name in (("onset_month", "starts"), ("cessation_month", "ends")):
            other = length - 1
            low, high = (-span, min(span, other)) if edge == "onset_month" else (-min(span, other), span)
            inputs.append(Input(f"{label}.{edge}", f"Confirm when the {label.replace('_', ' ')} season {name}.",
                                source, "assumption", ("season", label, edge), 0,
                                tuple(i for i in range(low, high + 1) if i),
                                bounds=(low, high), integer=True,
                                range_basis="±20% of window length, rounded to whole months, at least one; design choice"))
    for field, question in POLICY_CHECKS.items():
        value = model.policy[field]
        maximum = None if field == "calendar_extension_days" else 1
        inputs.append(numeric(field, question, "config/scoring.json; " + model.policy["source"], "assumption",
                              ("policy", field), value, config, maximum=maximum))
    # Bare fallow has no planted crop, so the catalog's zero and null values define it.
    return inputs


def apply_values(model, seasons, inputs, values):
    farm = deepcopy(model.farm)
    crops = {key: dict(row) for key, row in model.crops.items()}
    policy = dict(model.policy)
    calendar = deepcopy(seasons)
    offsets = {}
    for item, value in zip(inputs, values, strict=True):
        target = item.target
        match target[0]:
            case "irrigation":
                farm["irrigation"]["supply_fraction"] = value
            case "baseline":
                farm["baseline_rotation_cycle"] = value
            case "crop":
                crops[target[1]][target[2]] = value
            case "policy":
                policy[target[1]] = value
            case "season":
                offsets.setdefault(target[1], {})[target[2]] = value
    for label, shifts in offsets.items():
        window = calendar["season_windows"][label]
        start, end = window["onset_month"], window["cessation_month"]
        span = (end - start) % 12
        move_start = shifts.get("onset_month", 0)
        moved_span = int(np.clip(span + shifts.get("cessation_month", 0) - move_start, 0, 11))
        start = (start + move_start - 1) % 12
        window.update(onset_month=start + 1, cessation_month=(start + moved_span) % 12 + 1)
    return farm, crops, policy, calendar


@dataclass
class Outcome:
    winners: np.ndarray
    top_scores: np.ndarray
    reference_scores: np.ndarray
    material_changes: np.ndarray
    reference_eligible: np.ndarray


class ExactSearch:
    def __init__(self, presets, years, slots_per_year, tolerance):
        # Use the same single-preset dot products and tie rules as the climate robustness sweep.
        self.weights = np.array([[row[m] for m in METRICS] for row in presets.values()])
        self.years = years
        self.slots_per_year = slots_per_year
        self.tolerance = tolerance
        self.rotations = lru_cache(maxsize=8)(self.enumerate)

    def enumerate(self, layers):
        return enumerate_canonical_rotations([np.asarray(layer, dtype=int) for layer in layers],
                                             self.slots_per_year)

    def evaluate(self, model, reference=None):
        layers = tuple(tuple(layer) for layer in allowed_layers(model, self.years))
        canonical = self.rotations(layers)
        baseline = canonical_cycle(baseline_indices(model, self.years), self.slots_per_year)
        rows = np.vstack([baseline, canonical])
        scores = score_rotations(model, rows)[1]
        winners, top_scores = [], []
        for weight in self.weights:
            objective = scores @ weight
            winner = int(np.argmax(objective))
            winners.append(rows[winner])
            top_scores.append(objective[winner])
        winners = np.array(winners)
        if reference is None:
            reference = winners
        reference_is_baseline = (reference == baseline).all(axis=1)
        period = np.arange(rows.shape[1]) % self.slots_per_year
        reference_feasible = (model.suitable[period, reference].all(axis=1)
                              & (reference != np.roll(reference, 1, axis=1)).all(axis=1))
        reference_scores = score_rotations(model, reference)[1]
        reference_scores = np.array([row @ w for row, w in zip(reference_scores, self.weights, strict=True)])
        changed = (winners != reference).any(axis=1)
        eligible = reference_is_baseline | reference_feasible
        material = changed & (~eligible | (top_scores - reference_scores > self.tolerance))
        return Outcome(winners, np.array(top_scores), reference_scores, material, eligible)


def joint_associations(inputs, samples, outcomes):
    """Spearman for numeric inputs, rank correlation ratio for categorical inputs."""
    result = []
    outcome_ranks = rankdata(outcomes)
    centered = outcome_ranks - outcome_ranks.mean()
    for item, values in zip(inputs, zip(*samples, strict=True), strict=True):
        if item.bounds is not None:
            ranks = rankdata(values)
            ranks -= ranks.mean()
            denominator = np.linalg.norm(ranks) * np.linalg.norm(centered)
            result.append(float(ranks @ centered / denominator) if denominator else None)
        else:
            levels = {value: i for i, value in enumerate((item.reference, *item.levels))}
            codes = np.array([levels[value] for value in values])
            counts = np.bincount(codes)
            totals = np.bincount(codes, weights=centered)
            variance = centered @ centered
            populated = counts > 0
            numerator = np.sum(totals[populated] ** 2 / counts[populated])
            result.append(float(np.sqrt(numerator / variance)) if variance and sum(populated) > 1 else None)
    return result


def measures(outcomes, reference, preset, decode, *, include_reference=False):
    reference_cycle = reference.winners[preset]
    score = reference.top_scores[preset]
    winners = Counter(tuple(o.winners[preset]) for o in outcomes)
    new_scores = [o.top_scores[preset] for o in outcomes]
    original_scores = [o.reference_scores[preset] for o in outcomes]
    if include_reference:
        new_scores.append(score)
        original_scores.append(score)
    deltas = [value - score for value in new_scores]
    count = len(outcomes)
    return {
        "evaluations": count,
        "top_score_range": [float(min(new_scores)), float(max(new_scores))],
        "top_score_delta_range": [float(min(deltas)), float(max(deltas))],
        "reference_winner_score_range": [float(min(original_scores)), float(max(original_scores))],
        "top_score_span": float(max(new_scores) - min(new_scores)),
        "winner_change_fraction": 1 - winners[tuple(reference_cycle)] / count,
        "material_change_fraction": sum(bool(row.material_changes[preset]) for row in outcomes) / count,
        "reference_excluded_fraction": sum(not row.reference_eligible[preset] for row in outcomes) / count,
        "winners": [{"cycle": decode(cycle), "count": number}
                    for cycle, number in sorted(winners.items(), key=lambda row: (-row[1], row[0]))],
    }


def rank_inputs(rows, config):
    """Group equal priorities. Use input key only to order members of a tie."""
    def key(row):
        effect = row["one_at_a_time"]
        return (-effect["material_change_fraction"], -round(effect["top_score_span"], config["rank_score_decimals"]))

    ordered = sorted(rows, key=lambda row: (key(row), row["key"]))
    previous = None
    for position, row in enumerate(ordered, 1):
        priority = key(row)
        if priority != previous:
            rank = position
        previous = priority
        row["rank"] = rank
        row["weak"] = (-priority[0] == 0 and -priority[1] <= config["weak_score_span"])
    counts = Counter(row["rank"] for row in ordered)
    for row in ordered:
        row["tied"] = counts[row["rank"]] > 1
    return ordered


def check_first(rows, limit=3):
    """Render messages only from the saved per-preset ranking and effects."""
    output = []
    for row in rows[:limit]:
        effect = row["one_at_a_time"]
        if effect["material_change_fraction"]:
            reason = f"The top choice changed materially in {effect['material_change_fraction']:.0%} of the settings tested ({effect['evaluations']} total)."
            if effect["reference_excluded_fraction"]:
                reason += f" The original top choice became ineligible in {effect['reference_excluded_fraction']:.0%}."
        elif row["weak"]:
            reason = "This check showed a small effect within the tested range."
        else:
            reason = f"It moved the top score by {effect['top_score_span']:.3f} points across its tested range."
        if row["tied"]:
            reason += " It shares this priority with other inputs."
        output.append({"question": row["question"], "reason": reason, "grade": row["grade"],
                       "source": row["source"], "rank": row["rank"]})
    return output


def joint_samples(inputs, config, count=None):
    """Generate the P22 sample stream, optionally taking only its first draws."""
    rng = np.random.default_rng(config["seed"])
    return [
        tuple(item.draw(rng, config["categorical_change_probability"]) if item.levels else item.reference
              for item in inputs)
        for _ in range(config["joint_draws"] if count is None else count)
    ]


def analyse(model, presets, config, inputs, years, score_model):
    search = ExactSearch(presets, years, len(model.season_labels), config["near_tie_gap"])
    reference = search.evaluate(model)
    slots = len(model.season_labels)

    def decode(cycle):
        ids = [model.ids[i] for i in cycle]
        return [ids[start:start + slots] for start in range(0, len(ids), slots)]

    def evaluate(inputs, values):
        return search.evaluate(score_model(inputs, values), reference.winners)

    sweeps = [[evaluate([item], [level]) for level in item.levels] for item in inputs]
    samples = joint_samples(inputs, config)
    active = [i for i, item in enumerate(inputs) if item.levels]
    varying = [inputs[i] for i in active]
    joint = [evaluate(varying, [draw[i] for i in active]) for draw in samples]
    results = {}
    for index, name in enumerate(presets):
        scores = [o.top_scores[index] for o in joint]
        changes = [bool((o.winners[index] != reference.winners[index]).any()) for o in joint]
        score_links = joint_associations(inputs, samples, scores)
        change_links = joint_associations(inputs, samples, changes)
        rankings = [
            {"key": item.key, "question": item.question, "grade": item.grade, "source": item.source,
             "one_at_a_time": measures(test, reference, index, decode, include_reference=True),
             "joint_association": {"method": "Spearman ρ" if item.bounds is not None else "rank η",
                                   "top_score": score_links[i], "winner_changed": change_links[i]}}
            for i, (item, test) in enumerate(zip(inputs, sweeps, strict=True)) if test
        ]
        results[name] = {
            "reference_winner": decode(reference.winners[index]),
            "reference_top_score": float(reference.top_scores[index]),
            "joint": {**measures(joint, reference, index, decode),
                      "top_score_percentiles_10_50_90": np.quantile(scores, [0.1, 0.5, 0.9]).tolist()},
            "ranking": rank_inputs(rankings, config),
        }
    return {
        "farm_id": model.farm["farm_id"], "label": "illustrative; validate locally",
        "design": config, "horizon_years": years, "inputs": [asdict(item) for item in inputs],
        "input_count": len(active), "fixed_input_count": len(inputs) - len(active),
        "sweep_evaluations": sum(map(len, sweeps)), "presets": results,
    }


def main():
    conf = ROOT / "config"
    out = ROOT / "data/processed"
    config = json.loads((conf / "sensitivity.json").read_text())
    if config["joint_draws"] < 500:
        raise ValueError("The reference-farm sensitivity run needs at least 500 draws")
    presets = json.loads((conf / "weights_presets.json").read_text())["presets"]
    evidence = json.loads((conf / "evidence_grades.json").read_text())
    crops = load_crops(ROOT / "data/crops.csv")
    for farm in json.loads((conf / "farms.json").read_text()):
        farm_id = farm["farm_id"]
        seasons = json.loads((out / f"seasons_{farm_id}.json").read_text())
        current = json.loads((out / f"strategies_{farm_id}.json").read_text())
        climate = pd.read_parquet(out / f"climate_{farm_id}.parquet").set_index("date")

        @lru_cache(maxsize=256)
        def lookup(start, length):
            return crop_windows(climate, start, length)

        model = preload(farm, crops=crops, season_calendar=seasons, climate=climate, window_lookup=lookup)
        inputs = inventory(model, seasons, evidence, config)

        def rebuild(inputs, values):
            test_farm, test_crops, policy, calendar = apply_values(model, seasons, inputs, values)
            return preload(test_farm, crops=test_crops, policy=policy, season_calendar=calendar,
                           climate=climate, window_lookup=lookup)

        result = analyse(model, presets, config, inputs, current["horizon_years"], rebuild)
        write_json(out / f"sensitivity_{farm_id}.json", result)
        print(farm_id, result["input_count"], result["sweep_evaluations"], flush=True)


if __name__ == "__main__":
    main()
