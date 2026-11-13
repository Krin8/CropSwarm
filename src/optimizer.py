"""Compare seeded ant colony searches with exact feasible enumeration."""

import json
import time

import numpy as np

from src.precompute_cache import write_json
from src.scoring import METRICS, ROOT, baseline_indices, metric_rows, preload, score_rotations


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


def ant_colony(model, layers, weights, config, seed):
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
        _, scores, _ = score_rotations(model, batch)
        objective = scores @ weights
        leader = objective.argmax()
        if objective[leader] > best:
            best = float(objective[leader])
            best_sequence = batch[leader].copy()
        pheromone *= 1 - config["evaporation"]
        top = np.argsort(objective)[-config["elites"]:]
        previous = np.column_stack((np.full(len(top), n), batch[top, :-1]))
        np.add.at(pheromone, (np.arange(slots)[None, :], previous, batch[top]), objective[top, None])
    return (best, best_sequence) if best_sequence is not None else (None, None)


def strategy(model, sequence, strategy_id, priority, weights):
    raw, scores, violations = score_rotations(model, sequence)
    flags = {name: np.flatnonzero(mask[0]).tolist() for name, mask in violations.items() if mask.any()}
    source_tags = {"water": f"NASA POWER · {model.soil_source} · crop catalog and irrigation assumption"}
    metrics = metric_rows(raw[0], scores[0])
    for name, source in source_tags.items():
        metrics[name]["source"] = source
    crop_names = [model.crops[model.ids[index]]["display_name"] for index in sequence]
    cycle = np.asarray([model.ids[index] for index in sequence]).reshape(-1, len(model.season_labels)).tolist()
    return {
        "strategy_id": strategy_id, "priority": priority, "crop_ids": cycle, "crop_names": crop_names,
        "metrics": metrics, "flags": flags,
        "objectives": {name: float(scores[0] @ values) for name, values in weights.items()},
        "why": "Existing rotation supplied for comparison." if priority is None else
        f"High exact-search score under the {priority.replace('_',' ')} priorities, among distinct strategies.",
    }


def optimise(model, presets, config):
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
    rotations = enumerate_rotations(layers)
    assert len(rotations) == count
    _, scores, _ = score_rotations(model, rotations)
    weights = {name: np.array([values[key] for key in METRICS]) for name, values in presets.items()}
    reference = baseline_indices(model, years)
    selected = [strategy(model, reference, "baseline", None, weights)]
    seen = {tuple(reference)}
    verification = {}
    exact_seconds = time.perf_counter() - exact_start
    for name, weight in weights.items():
        objective = scores @ weight
        order = np.argsort(-objective, kind="stable")
        best = float(objective[order[0]])
        start = time.perf_counter()
        swarm = [ant_colony(model, layers, weight, config, seed) for seed in range(config["seed_count"])]
        runtime = time.perf_counter() - start
        distinct = [(value, sequence) for value, sequence in swarm if sequence is not None and tuple(sequence) not in seen]
        if distinct:
            _, chosen = max(distinct, key=lambda row: row[0])
            method = "ant colony"
        else:
            index = next(i for i in order if tuple(rotations[i]) not in seen)
            chosen = rotations[index]
            method = "exact distinct fallback"
        seen.add(tuple(chosen))
        entry = strategy(model, chosen, name, name, weights)
        entry["why"] = f"Selected by {method} for the {name.replace('_', ' ')} priorities."
        entry["selection_method"] = method
        selected.append(entry)
        finite = [value for value, _ in swarm if value is not None]
        gap = [max(0, best-value) for value in finite]
        verification[name] = {"exact_score": best, "runs": len(swarm),
                              "optimum_hits": sum(bool(np.isclose(value, best, rtol=0, atol=1e-10)) for value in finite),
                              "best_gap": min(gap, default=None), "worst_gap": max(gap, default=None),
                              "runtime_seconds": runtime, "per_seed_scores": [value for value, _ in swarm]}
    return {"farm_id": model.farm["farm_id"], "label": "illustrative; validate locally",
            "horizon_years": years, "three_year_feasible_count": original_count,
            "feasible_count": count, "exact_runtime_seconds": exact_seconds, "verification": verification,
            "strategies": selected, "parameter_source": "config/optimizer.json"}


def main():
    farms = json.loads((ROOT / "config/farms.json").read_text())
    presets = json.loads((ROOT / "config/weights_presets.json").read_text())["presets"]
    config = json.loads((ROOT / "config/optimizer.json").read_text())
    for farm in farms:
        result = optimise(preload(farm), presets, config)
        write_json(ROOT / "data/processed" / f"strategies_{farm['farm_id']}.json", result)
        print(farm["farm_id"], result["feasible_count"],
              {name: row["optimum_hits"] for name, row in result["verification"].items()}, flush=True)


if __name__ == "__main__":
    main()
