"""Compare seeded ant colony searches with exact feasible enumeration."""

import json
import time

import numpy as np

from src.precompute_cache import write_json
from src.scoring import METRICS, ROOT, baseline_indices, metric_rows, preload, score_rotations
from src.evidence import evidence_for_strategy


def allowed_layers(model, years):
    return [
        np.flatnonzero(model.suitable[slot % len(model.season_labels)])
        for slot in range(years * len(model.season_labels))
    ]


def count_rotations(layers, size):
    counter = np.zeros((size, size), dtype=np.int64)
    counter[layers[0], layers[0]] = 1
    for allowed in layers[1:]:
        current = np.zeros_like(counter)
        current[:, allowed] = (counter.sum(axis=1, keepdims=True) - counter)[:, allowed]
        counter = current
    return int(counter.sum() - np.trace(counter)) if len(layers) > 1 else int(counter.sum())


def enumerate_rotations(layers):
    rotations = layers[0][:, None]
    for allowed in layers[1:]:
        indices, branches = np.where(rotations[:, -1, None] != allowed)
        rotations = np.column_stack((rotations[indices], allowed[branches]))
    if len(layers) > 1:
        rotations = rotations[rotations[:, 0] != rotations[:, -1]]
    return rotations


def canonical_cycle(sequence, slots_per_year):
    """Lexicographically smallest whole-year shift; never swap within-year seasons."""
    rows = np.asarray(sequence, dtype=int).reshape(-1, slots_per_year)
    return min(tuple(np.roll(rows, -offset, axis=0).ravel()) for offset in range(len(rows)))


def canonical_rotations(rotations, slots_per_year):
    """Keep one representative per whole-year cycle without changing score rules."""
    if len(rotations) == 0:
        return rotations
    years = rotations.shape[1] // slots_per_year
    rows = rotations.reshape(len(rotations), years, slots_per_year)
    keep = np.ones(len(rotations), dtype=bool)
    indices = np.arange(len(rotations))
    for offset in range(1, years):
        shifted = np.roll(rows, -offset, axis=1).reshape(rotations.shape)
        different = shifted != rotations
        first = different.argmax(axis=1)
        smaller = different.any(axis=1) & (shifted[indices, first] < rotations[indices, first])
        keep &= ~smaller
    return rotations[keep]


def enumerate_canonical_rotations(layers, slots_per_year):
    return canonical_rotations(enumerate_rotations(layers), slots_per_year)


def ant_colony(model, layers, weights, config, seed, *, fitness=None):
    rng = np.random.default_rng(seed)
    n = len(model.ids)
    slots = len(layers)
    ants = config["ants"]
    # The start node is n. Subsequent nodes encode the previous crop ID.
    pheromone = np.ones((slots, n + 1, n))
    allowed = np.zeros((slots, n), dtype=bool)
    for slot, nodes in enumerate(layers):
        allowed[slot, nodes] = True
    additions = model.additions[np.arange(slots) % len(model.season_labels)]
    # Local heuristic uses the score components that are available without a predecessor.
    heuristic = (1-additions[..., 1]) * weights[0]
    if model.erosion_max:
        heuristic += (1-additions[..., 2]/model.erosion_max) * weights[2]
    heuristic += additions[..., 3] * weights[3] + additions[..., 4] * weights[4]
    heuristic = np.maximum(heuristic, np.finfo(float).eps) ** config["beta"]
    best = -np.inf
    best_sequence = None
    for _ in range(config["iterations"]):
        batch = np.empty((ants, slots), dtype=int)
        previous = np.full(ants, n)
        live = np.ones(ants, dtype=bool)
        for slot in range(slots):
            choices = np.broadcast_to(allowed[slot], (ants, n)).copy()
            choices &= np.arange(n) != previous[:, None]
            if slot == slots - 1 and slot:
                choices &= np.arange(n) != batch[:, :1]
            probabilities = pheromone[slot, previous] ** config["alpha"] * heuristic[slot] * choices
            sums = probabilities.sum(axis=1)
            live &= sums > 0
            targets = rng.random(ants) * sums
            next_nodes = (probabilities.cumsum(axis=1) <= targets[:, None]).sum(axis=1)
            batch[:, slot] = np.minimum(next_nodes, n - 1)
            previous = batch[:, slot]
        batch = batch[live]
        if not len(batch):
            continue
        if fitness is None:
            _, scores, _ = score_rotations(model, batch)
            objective = scores @ weights
        else:
            objective = fitness(batch)
        maximum = objective.max()
        leader_sequence = min(canonical_cycle(batch[index], len(model.season_labels))
                              for index in np.flatnonzero(objective == maximum))
        if maximum > best or (maximum == best and (best_sequence is None or leader_sequence < tuple(best_sequence))):
            best = float(maximum)
            best_sequence = np.array(leader_sequence)
        pheromone *= 1 - config["evaporation"]
        top = np.argsort(objective)[-config["elites"]:]
        previous = np.column_stack((np.full(len(top), n), batch[top, :-1]))
        np.add.at(pheromone, (np.arange(slots)[None, :], previous, batch[top]), objective[top, None])
    return (best, np.array(canonical_cycle(best_sequence, len(model.season_labels)))) if best_sequence is not None else (None, None)


def strategy(model, sequence, strategy_id, priority, weights):
    if priority is not None:
        sequence = np.array(canonical_cycle(sequence, len(model.season_labels)))
    raw, scores, violations = score_rotations(model, sequence)
    flags = {name: np.flatnonzero(mask[0]).tolist() for name, mask in violations.items() if mask.any()}
    source_tags = {"water": f"NASA POWER · {model.soil_source} · crop catalog and irrigation assumption"}
    metrics = metric_rows(raw[0], scores[0])
    evidence = evidence_for_strategy(model, sequence)
    for name, source in source_tags.items():
        metrics[name]["source"] = source
    for name in METRICS:
        metrics[name]["evidence"] = evidence["metrics"][name]
    crop_names = [model.crops[model.ids[index]]["display_name"] for index in sequence]
    cycle = np.asarray([model.ids[index] for index in sequence]).reshape(-1, len(model.season_labels)).tolist()
    return {
        "strategy_id": strategy_id, "priority": priority, "crop_ids": cycle, "crop_names": crop_names,
        "metrics": metrics, "evidence_label": evidence["label"], "flags": flags,
        "objectives": {name: float(scores[0] @ values) for name, values in weights.items()},
        "why": "Existing rotation supplied for comparison." if priority is None else
        f"High exact-search score under the {priority.replace('_',' ')} priorities, among distinct strategies.",
    }


def aco_restarts(model, layers, weights, config, trial):
    """Start each colony with independent seed and pheromone state."""
    seeds = [trial + restart * config["seed_count"] for restart in range(config["restarts"])]
    outcomes = [ant_colony(model, layers, weights, config, seed) for seed in seeds]
    best = min(outcomes, key=lambda outcome: (-(outcome[0] if outcome[0] is not None else -np.inf),
                                            tuple(outcome[1]) if outcome[1] is not None else ()))
    return seeds, outcomes, best


def verification_summary(exact, scores):
    gaps = [max(0., exact - value) for value in scores if value is not None]
    hits = sum(gap <= 1e-10 for gap in gaps)
    return {"runs": len(scores), "completed_runs": len(gaps), "optimum_hits": hits,
            "exact_hit_rate": hits / len(scores), "best_gap": min(gaps, default=None),
            "mean_gap": float(np.mean(gaps)) if gaps else None, "worst_gap": max(gaps, default=None),
            "scores": scores}


def optimise(model, presets, config, difference_threshold=None):
    if difference_threshold is None:
        difference_threshold = json.loads((ROOT / "config/tie_diagnosis.json").read_text())["alternative_max_metric_difference"]
    years = config["default_years"]
    layers = allowed_layers(model, years)
    count = count_rotations(layers, len(model.ids))
    original_count = count
    if count > config["max_exact_rotations"]:
        years = config["fallback_years"]
        layers = allowed_layers(model, years)
        count = count_rotations(layers, len(model.ids))
    if count > config["max_exact_rotations"] or count < 3:
        raise ValueError(f"Unsupported feasible search space of {count} rotations")
    exact_start = time.perf_counter()
    rotations = enumerate_canonical_rotations(layers, len(model.season_labels))
    canonical_count = len(rotations)
    _, scores, _ = score_rotations(model, rotations)
    weights = {name: np.array([values[key] for key in METRICS]) for name, values in presets.items()}
    reference = baseline_indices(model, years)
    selected = [strategy(model, reference, "baseline", None, weights)]
    selected_vectors = [score_rotations(model, reference)[1][0]]
    seen = {canonical_cycle(reference, len(model.season_labels))}
    verification = {}
    exact_seconds = time.perf_counter() - exact_start
    for name, weight in weights.items():
        objective = scores @ weight
        order = np.argsort(-objective, kind="stable")
        best = float(objective[order[0]])
        start = time.perf_counter()
        trials = [aco_restarts(model, layers, weight, config, i) for i in range(config["seed_count"])]
        runtime = time.perf_counter() - start
        swarm = [best_outcome for _, _, best_outcome in trials]
        chosen = None
        method = None
        for value, sequence in sorted((row for row in swarm if row[1] is not None),
                                      key=lambda row: (-row[0], canonical_cycle(row[1], len(model.season_labels)))):
            key = canonical_cycle(sequence, len(model.season_labels))
            if key in seen:
                continue
            vector = score_rotations(model, sequence)[1][0]
            if all(np.max(np.abs(vector - other)) > difference_threshold for other in selected_vectors):
                chosen, method = sequence, f"best-of-{config['restarts']} ant colony"
                break
        if chosen is None:
            for index in order:
                sequence = rotations[index]
                key = tuple(sequence)
                if key in seen:
                    continue
                vector = scores[index]
                if all(np.max(np.abs(vector - other)) > difference_threshold for other in selected_vectors):
                    chosen, method = sequence, "exact metric-distinct fallback"
                    break
        if chosen is not None:
            seen.add(canonical_cycle(chosen, len(model.season_labels)))
            entry = strategy(model, chosen, name, name, weights)
            entry["why"] = f"Selected by {method} for the {name.replace('_', ' ')} priorities."
            entry["selection_method"] = method
            selected.append(entry)
            selected_vectors.append(score_rotations(model, chosen)[1][0])
        verification[name] = {
            "exact_score": best,
            "single_run": verification_summary(best, [outcomes[0][0] for _, outcomes, _ in trials]),
            "best_of_restarts": verification_summary(best, [value for value, _ in swarm]),
            "runtime_seconds": runtime,
            "restart_count": config["restarts"],
            "trials": [{"seeds": seeds, "scores": [value for value, _ in outcomes]}
                       for seeds, outcomes, _ in trials],
        }
    return {"farm_id": model.farm["farm_id"], "label": "illustrative; validate locally",
            "horizon_years": years, "three_year_raw_count": original_count,
            "three_year_feasible_count": canonical_count if years == config["default_years"] else None,
            "raw_feasible_count": count, "feasible_count": canonical_count,
            "exact_runtime_seconds": exact_seconds, "verification": verification,
            "selection": {"requested_alternatives": len(presets), "displayed_alternatives": len(selected) - 1,
                          "difference_threshold": difference_threshold,
                          "source": "config/tie_diagnosis.json; design choice, not empirical",
                          "note": "Fewer alternatives mean no additional canonical rotation cleared the metric-difference threshold."},
            "strategies": selected, "parameter_source": "config/optimizer.json"}


def main():
    farms = json.loads((ROOT / "config/farms.json").read_text())
    presets = json.loads((ROOT / "config/weights_presets.json").read_text())["presets"]
    config = json.loads((ROOT / "config/optimizer.json").read_text())
    for farm in farms:
        result = optimise(preload(farm), presets, config)
        write_json(ROOT / "data/processed" / f"strategies_{farm['farm_id']}.json", result)
        print(farm["farm_id"], result["feasible_count"],
              {name: [row["single_run"]["optimum_hits"], row["best_of_restarts"]["optimum_hits"]]
               for name, row in result["verification"].items()}, flush=True)


if __name__ == "__main__":
    main()
