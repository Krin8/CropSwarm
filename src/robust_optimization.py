"""P28 offline risk objectives for fixed, nominally feasible rotations."""
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import resource
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from src.crops import load_crops
from src.evidence import evidence_for_strategy
from src.optimizer import allowed_layers, ant_colony, canonical_cycle, enumerate_canonical_rotations
from src.precompute_cache import write_json
from src.scoring import METRICS, ROOT, baseline_indices, crop_windows, preload, score_rotations
from src.sensitivity import apply_values, inventory, joint_samples
from src.stress_test import rotation_record

OBJECTIVES = ("expected", "cvar", "minimax_regret")


def lower_cvar(scores, fraction):
    """Average exactly the specified lower-tail mass, including a fractional boundary."""
    count = scores.shape[-1]
    if not count or not 0 < fraction <= 1:
        raise ValueError("CVaR needs draws and a tail fraction in (0, 1]")
    mass = fraction * count
    full = int(mass)
    if full == count:
        return scores.mean(axis=-1, dtype=np.float64)
    tail = np.partition(scores, full, axis=-1)
    return (tail[..., :full].sum(axis=-1, dtype=np.float64) + (mass - full) * tail[..., full]) / mass


def utilities(scores, oracle, fraction):
    """Each objective is maximized. Regret uses 1 minus the maximum shortfall."""
    regret = np.maximum(oracle - scores, 0).max(axis=-1)
    return np.column_stack((scores.mean(axis=-1, dtype=np.float64), lower_cvar(scores, fraction), 1 - regret))


def metric_rows(model, rotations):
    """Score with the unchanged engine, assigning zero realized score on hard-rule failure."""
    _, scores, flags = score_rotations(model, rotations)
    feasible = ~np.logical_or.reduce(tuple(flags.values())).any(axis=1)
    return np.where(feasible[:, None], scores, 0).astype(np.float32), feasible


def prepare_metrics(models, rotations, cache, feasibility, chunk):
    for draw, model in enumerate(models):
        for start in range(0, len(rotations), chunk):
            stop = min(start + chunk, len(rotations))
            cache[start:stop, draw], feasibility[start:stop, draw] = metric_rows(model, rotations[start:stop])


def rotation_keys(rotations, crop_count):
    places = crop_count ** np.arange(rotations.shape[1] - 1, -1, -1, dtype=np.int64)
    return rotations @ places


def draw_oracles(models, rotations, cache, feasibility, weights, years, chunk):
    """Reuse feasible cached rows and score only additional feasible rotations and the drawn baseline."""
    oracles = []
    nominal_keys = rotation_keys(rotations, len(models[0].ids))
    for i, model in enumerate(models):
        baseline = np.array(canonical_cycle(baseline_indices(model, years), len(model.season_labels)))
        # P22 always lets the draw's baseline be scored, even when flagged.
        best = score_rotations(model, baseline)[1][0].astype(np.float32) @ weights.T
        for start in range(0, len(rotations), chunk):
            stop = start + chunk
            values = cache[start:stop, i][feasibility[start:stop, i]]
            if len(values):
                best = np.maximum(best, (values @ weights.T).max(axis=0))
        layers = allowed_layers(model, years)
        if all(map(len, layers)):
            feasible_in_draw = enumerate_canonical_rotations(layers, len(model.season_labels))
            extra = ~np.isin(rotation_keys(feasible_in_draw, len(model.ids)), nominal_keys)
            candidates = feasible_in_draw[extra]
            for start in range(0, len(candidates), chunk):
                scores, _ = metric_rows(model, candidates[start:start + chunk])
                best = np.maximum(best, (scores @ weights.T).max(axis=0))
        oracles.append(best)
    return np.array(oracles)


def weighted_scores(metrics, weight):
    return metrics @ weight


def chunk_objectives(cache, weight, oracle, fraction, chunk):
    out = np.empty((len(cache), len(OBJECTIVES)), dtype=np.float64)
    for start in range(0, len(cache), chunk):
        stop = min(start + chunk, len(cache))
        out[start:stop] = utilities(weighted_scores(cache[start:stop], weight), oracle, fraction)
    return out


def exact_pick(values, tolerance, *, preferred=None):
    maximum = values.max()
    tied = np.flatnonzero(maximum - values <= tolerance)
    index = preferred if preferred is not None and maximum - values[preferred] <= tolerance else tied[0]
    return int(index), float(maximum), len(tied)


class ColonyFitness:
    """Evaluate ant batches from the draw metrics, independently of exact objectives."""

    def __init__(self, rotations, metric_cache, weight, oracle, fraction, slots, crop_count):
        self.metric_cache = metric_cache
        self.weight = weight
        self.oracle = oracle
        self.fraction = fraction
        self.slots = slots
        self.place_values = crop_count ** np.arange(rotations.shape[1] - 1, -1, -1, dtype=np.int64)
        self.rotation_keys = rotations @ self.place_values
        self.memo = np.full((len(rotations), len(OBJECTIVES)), np.nan)

    def indices(self, batch):
        keys = batch @ self.place_values
        for shift in range(self.slots, batch.shape[1], self.slots):
            keys = np.minimum(keys, np.roll(batch, -shift, axis=1) @ self.place_values)
        ix = np.searchsorted(self.rotation_keys, keys)
        if np.any(ix >= len(self.rotation_keys)) or not np.array_equal(self.rotation_keys[ix], keys):
            raise ValueError("Colony generated a rotation outside the reference space")
        return ix

    def __call__(self, batch, objective):
        indices = self.indices(batch)
        new = np.unique(indices[np.isnan(self.memo[indices, objective])])
        if len(new):
            scores = weighted_scores(self.metric_cache[new], self.weight)
            self.memo[new] = utilities(scores, self.oracle, self.fraction)
        return self.memo[indices, objective]


def colony_trials(model, layers, weights, optimizer, config, colony, objective, best_value):
    results = []
    for trial in range(config["aco_trials"]):
        seeds = [trial + restart * config["aco_trials"] for restart in range(config["aco_restarts"])]
        values = [ant_colony(model, layers, weights, optimizer, seed,
                             fitness=lambda batch: colony(batch, objective))[0] for seed in seeds]
        if any(value is None for value in values):
            raise ValueError("ACO failed to produce a complete rotation")
        gaps = [max(0.0, best_value - value) for value in values]
        if any(value - best_value > config["tie_tolerance"] for value in values):
            raise ValueError("ACO exceeded the exact reference")
        results.append({"seeds": seeds, "single_gap": gaps[0], "best_gap": min(gaps)})
    return {
        "trials": len(results),
        "single_hits": sum(row["single_gap"] <= config["tie_tolerance"] for row in results),
        "best_of_five_hits": sum(row["best_gap"] <= config["tie_tolerance"] for row in results),
        "single_mean_gap": float(np.mean([row["single_gap"] for row in results])),
        "single_worst_gap": max(row["single_gap"] for row in results),
        "best_of_five_mean_gap": float(np.mean([row["best_gap"] for row in results])),
        "best_of_five_worst_gap": max(row["best_gap"] for row in results),
        "runs": results,
    }


def pick_record(index, rotations, cache, feasible, oracle, weight, nominal, config, model, root, grades):
    scores = weighted_scores(cache[index], weight)
    expected, cvar, regret_utility = utilities(scores[None], oracle, config["tail_fraction"])[0]
    rotation = rotations[index]
    evidence = evidence_for_strategy(model, rotation, config=grades, root=root)
    return {
        **rotation_record(model, rotation, canonical=False),
        "index": index,
        "nominal_score": float(nominal[index]),
        "expected": float(expected),
        "cvar": float(cvar),
        "worst_score": float(scores.min()),
        "minimax_regret": float(1 - regret_utility),
        "feasible_draws": int(np.count_nonzero(feasible[index])),
        "evidence_label": evidence["label"],
        "metric_evidence": {key: value["label"] for key, value in evidence["metrics"].items()},
    }


def comparison(pick, nominal, tolerance):
    return {
        "rotation_changed": pick["index"] != nominal["index"],
        "nominal_score_cost": nominal["nominal_score"] - pick["nominal_score"],
        "worst_score_gain": pick["worst_score"] - nominal["worst_score"],
        "max_regret_reduction": nominal["minimax_regret"] - pick["minimax_regret"],
        "expected_score_gain": pick["expected"] - nominal["expected"],
        "cvar_gain": pick["cvar"] - nominal["cvar"],
        "nominal_score_tie": abs(pick["nominal_score"] - nominal["nominal_score"]) <= tolerance,
    }


def exact_results(model, rotations, cache, feasible, oracle, presets, config, root, grades):
    nominal_scores = score_rotations(model, rotations)[1]
    results = {}
    for i, (preset, values) in enumerate(presets.items()):
        started = perf_counter()
        weight = np.array([values[key] for key in METRICS], dtype=np.float64)
        nominal_values = nominal_scores @ weight
        nominal_index, _, nominal_ties = exact_pick(nominal_values, config["tie_tolerance"])
        values = chunk_objectives(cache, weight, oracle[:, i], config["tail_fraction"], config["rotation_chunk"])
        sum_elapsed = perf_counter() - started
        if sum_elapsed > config["exact_seconds_per_preset"]:
            raise TimeoutError(f"Exact evaluation exceeded the limit for {preset}")

        def record(index):
            return pick_record(index, rotations, cache, feasible, oracle[:, i], weight, nominal_values,
                               config, model, root, grades)

        nominal = record(nominal_index)
        picks = {}
        for j, objective in enumerate(OBJECTIVES):
            index, maximum, ties = exact_pick(values[:, j], config["tie_tolerance"], preferred=nominal_index)
            pick = record(index)
            picks[objective] = {"rotation": pick, "comparison": comparison(pick, nominal, config["tie_tolerance"]),
                                "objective_maximum_utility": maximum, "ties": ties}
        results[preset] = {"nominal": nominal, "nominal_ties": nominal_ties,
                           "picks": picks, "exact_seconds": sum_elapsed}
    return results


def sample_models(model, seasons, climate, p22, count, grades, root, lookup, *, primary_count):
    inputs = inventory(model, seasons, grades, p22)
    samples = joint_samples(inputs, p22, count)
    active = [i for i, item in enumerate(inputs) if item.levels]
    varied = [inputs[i] for i in active]
    models = []
    for draw in samples:
        farm, crops, policy, calendar = apply_values(model, seasons, varied, [draw[i] for i in active])
        drawn = preload(farm, root=root, crops=crops, policy=policy, season_calendar=calendar,
                        climate=climate, window_lookup=lookup)
        models.append(drawn)
    signatures = {str(size): hashlib.sha256(json.dumps(samples[:size], separators=(",", ":")).encode()).hexdigest()
                  for size in sorted({count, primary_count})}
    return models, signatures


def convergence_summary(main, check, tolerance):
    totals = {}
    for preset, expanded in check.items():
        rows = {}
        for goal, result in expanded["picks"].items():
            original = main[preset]["picks"][goal]
            before, after = original["comparison"], result["comparison"]
            close = lambda key: abs(before[key] - after[key]) <= tolerance
            rows[goal] = {
                "same_rotation": original["rotation"]["index"] == result["rotation"]["index"],
                "same_nominal_difference": before["rotation_changed"] == after["rotation_changed"],
                "nominal_cost_close": close("nominal_score_cost"),
                "worst_score_gain_close": close("worst_score_gain"),
                "regret_reduction_close": close("max_regret_reduction"),
            }
        totals[preset] = rows
    return totals


def build_farm(root, farm, crops, presets, p22, grades, optimizer, config, *, check):
    started = perf_counter()
    out = root / "data/processed"
    name = farm["farm_id"]
    seasons = json.loads((out / f"seasons_{name}.json").read_text())
    existing = json.loads((out / f"strategies_{name}.json").read_text())
    climate = pd.read_parquet(out / f"climate_{name}.parquet").set_index("date")
    years = existing["horizon_years"]

    @lru_cache(maxsize=256)
    def lookup(start, length):
        return crop_windows(climate, start, length)

    model = preload(farm, root=root, crops=crops, season_calendar=seasons, climate=climate, window_lookup=lookup)
    slots = len(model.season_labels)
    layers = allowed_layers(model, years)
    rotations = enumerate_canonical_rotations(layers, slots)
    if len(rotations) != existing["feasible_count"]:
        raise ValueError("Nominal canonical count differs from saved results")
    n = config["check_draws"] if check else config["draws"]
    models, signatures = sample_models(model, seasons, climate, p22, n, grades, root, lookup,
                                       primary_count=config["draws"])
    print(f"{name}: {len(rotations):,} nominal rotations, {n} draws generated", flush=True)
    draw_seconds = perf_counter() - started
    preset_weights = np.array([[preset[key] for key in METRICS] for preset in presets.values()])

    with TemporaryDirectory(prefix="cropswarm-risk-") as directory:
        cache = np.memmap(Path(directory) / "metrics", mode="w+", dtype=np.float32,
                          shape=(len(rotations), n, len(METRICS)))
        feasible = np.memmap(Path(directory) / "feasible", mode="w+", dtype=bool, shape=(len(rotations), n))
        mark = perf_counter()
        prepare_metrics(models, rotations, cache, feasible, config["rotation_chunk"])
        metric_seconds = perf_counter() - mark
        print(f"{name}: metric cache in {metric_seconds:.1f}s", flush=True)
        mark = perf_counter()
        oracle = draw_oracles(models, rotations, cache, feasible, preset_weights, years, config["rotation_chunk"])
        oracle_seconds = perf_counter() - mark
        draws = config["draws"]
        results = exact_results(model, rotations, cache[:, :draws], feasible[:, :draws], oracle[:draws],
                                presets, config, root, grades)
        for preset, row in results.items():
            if abs(existing["verification"][preset]["exact_score"] - row["nominal"]["nominal_score"]) > config["tie_tolerance"]:
                raise ValueError("Nominal weighted score differs from archive")
        check_result = None
        if check:
            expanded = exact_results(model, rotations, cache, feasible, oracle, presets, config, root, grades)
            check_result = {"draws": n, "presets": expanded, "comparison": convergence_summary(
                results, expanded, config["practical_difference"])}
        print(f"{name}: exact references ready", flush=True)
        swarm_started = perf_counter()
        for index, (preset, values) in enumerate(presets.items()):
            weights = np.array([values[key] for key in METRICS], dtype=np.float64)
            colony = ColonyFitness(rotations, cache[:, :draws], weights, oracle[:draws, index],
                                   config["tail_fraction"], slots, len(model.ids))
            for j, goal in enumerate(OBJECTIVES):
                pick = results[preset]["picks"][goal]
                pick["aco"] = colony_trials(model, layers, weights, optimizer, config, colony, j,
                                            pick["objective_maximum_utility"])
            print(f"{name}: {preset} ACO runs complete", flush=True)
        bytes_cached = cache.nbytes + feasible.nbytes
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "farm_id": name, "label": "illustrative, validate locally", "draws": draws, "draw_seed": p22["seed"],
        "sample_prefix_sha256": signatures, "config": config, "horizon_years": years,
        "reference_space": "full nominal-feasible canonical rotation space",
        "candidate_count": len(rotations), "presets": results, "check_256": check_result,
        "compute": {"cache_bytes": bytes_cached, "peak_process_rss_bytes": int(rss if sys.platform == "darwin" else rss*1024),
                    "draw_preparation_seconds": draw_seconds, "oracle_seconds": oracle_seconds,
                    "metric_cache_seconds": metric_seconds,
                    "aco_seconds": perf_counter() - swarm_started, "total_seconds": perf_counter() - started},
    }


def main(root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--farm", help="Rebuild one farm")
    args = parser.parse_args()
    conf = root / "config"
    read = lambda name: json.loads((conf / f"{name}.json").read_text())
    farms = read("farms")
    crops = load_crops(root / "data/crops.csv")
    computed = root / "data/processed"
    smallest = min(farms, key=lambda farm: json.loads(
        (computed / f"strategies_{farm['farm_id']}.json").read_text())["feasible_count"])["farm_id"]
    if args.farm and args.farm not in {farm["farm_id"] for farm in farms}:
        parser.error(f"Unknown farm {args.farm}")
    settings = (read("weights_presets")["presets"], read("sensitivity"), read("evidence_grades"),
                read("optimizer"), read("robust_optimization"))
    with threadpool_limits(limits=1):
        for farm in farms:
            name = farm["farm_id"]
            if args.farm and name != args.farm:
                continue
            data = build_farm(root, farm, crops, *settings, check=name == smallest)
            write_json(computed / f"robust_optimization_{name}.json", data)


if __name__ == "__main__":
    main()
