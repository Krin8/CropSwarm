"""P28b exact feasible-tail scores, draw-count stability, and held-out ACO checks."""
import argparse
from functools import lru_cache
import json
import math
from pathlib import Path
import resource
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from src.crops import load_crops
from src.optimizer import allowed_layers, ant_colony, enumerate_canonical_rotations
from src.precompute_cache import write_json
from src.robust_optimization import (ColonyFitness, draw_oracles, exact_pick, lower_cvar, pick_record,
                                     prepare_metrics, sample_models, weighted_scores)
from src.scoring import METRICS, ROOT, crop_windows, preload, score_rotations

OBJECTIVES = ("expected", "conditional_cvar", "minimax_regret")


def conditional_cvar(scores, feasible, fraction):
    """Average exactly the lower tail of the feasible draws; undefined without one."""
    if scores.shape != feasible.shape or not 0 < fraction <= 1:
        raise ValueError("CVaR needs aligned scores and feasibility and a fraction in (0, 1]")
    counts = feasible.sum(axis=-1)
    order = np.sort(np.where(feasible, scores, np.inf), axis=-1)
    mass = fraction * counts
    # Zero weight suppresses the masked infinities and handles an integer tail boundary.
    weights = np.clip(mass[..., None] - np.arange(scores.shape[-1]), 0, 1)
    total = np.sum(np.where(weights > 0, order, 0) * weights, axis=-1)
    return np.divide(total, mass, out=np.full_like(total, np.nan, dtype=float), where=mass > 0)


def evaluations(cache, feasible, weight, oracle, fraction, counts, chunk):
    """Score any nested prefixes, reading the memory map in bounded rotation chunks."""
    results = {n: np.empty((len(cache), 4)) for n in counts}
    for start in range(0, len(cache), chunk):
        stop = min(start + chunk, len(cache))
        scores = weighted_scores(np.ascontiguousarray(cache[start:stop]), weight)
        mask = np.ascontiguousarray(feasible[start:stop])
        shortfalls = np.maximum(oracle - scores, 0)
        for n, out in results.items():
            sample = scores[:, :n]
            out[start:stop, 0] = sample.mean(axis=1)
            out[start:stop, 1] = conditional_cvar(sample, mask[:, :n], fraction)
            out[start:stop, 2] = 1 - shortfalls[:, :n].max(axis=1)
            out[start:stop, 3] = lower_cvar(sample, fraction)
    return results


def rank_top(values, tolerance, nominal, k):
    """Keep the nominal rotation if tied. Rank the remaining rows by utility then canonical index."""
    eligible = np.flatnonzero(np.isfinite(values))
    if not len(eligible):
        return [], None, 0
    usable = np.where(np.isfinite(values), values, -np.inf)
    winner, maximum, ties = exact_pick(usable, tolerance, preferred=nominal)
    ordered = eligible[np.argsort(-values[eligible], kind="stable")]
    return [winner, *(int(i) for i in ordered[ordered != winner][:k-1])], maximum, ties


def bootstrap_choices(scores, feasible, oracle, fraction, tolerance, *, objective, count, repeats, seed):
    """Reselect within a documented finalist set for paired draw-index bootstrap samples."""
    if count > scores.shape[1]:
        raise ValueError("Cannot bootstrap more source draws than are available")
    rng = np.random.default_rng(seed)
    credit = np.zeros(len(scores))
    included = 0
    for ix in rng.integers(count, size=(repeats, count)):
        sample = scores[:, ix]
        if objective == "expected":
            utility = sample.mean(axis=1)
        elif objective == "conditional_cvar":
            utility = conditional_cvar(sample, feasible[:, ix], fraction)
        elif objective == "minimax_regret":
            utility = 1 - np.maximum(oracle[ix] - sample, 0).max(axis=1)
        else:
            raise ValueError(f"Unknown bootstrap objective {objective}")
        valid = np.isfinite(utility)
        if valid.any():
            tied = valid & (np.max(utility[valid]) - utility <= tolerance)
            credit[tied] += 1 / tied.sum()
            included += 1
    return {"valid_replicates": included,
            "win_share": (credit / included).tolist() if included else [None] * len(scores)}


def preset_results(model, rotations, cache, feasible, oracle, weight, nominal_values, p28, setup, root, grades):
    tolerance = p28["tie_tolerance"]
    counts = setup["draw_counts"]
    nominal, _, nominal_ties = exact_pick(nominal_values, tolerance)
    tables = evaluations(cache, feasible, weight, oracle, p28["tail_fraction"], counts, p28["rotation_chunk"])
    ranks = {}
    serialized = {}
    for n, table in tables.items():
        ranks[n] = [rank_top(table[:, i], tolerance, nominal, setup["shortlist_per_count"])
                    for i in range(len(OBJECTIVES))]
        subcache, submask, suboracle = cache[:, :n], feasible[:, :n], oracle[:n]

        @lru_cache(maxsize=None)
        def record(index):
            row = pick_record(index, rotations, subcache, submask, suboracle, weight, nominal_values,
                              p28, model, root, grades)
            tail = float(table[index, 1])
            return {**row, "conditional_cvar": tail if math.isfinite(tail) else None,
                    "feasible_share": row["feasible_draws"] / n,
                    "nominal_cost": float(nominal_values[nominal] - nominal_values[index])}

        old_first, old_max, old_ties = rank_top(table[:, 3], tolerance, nominal, 1)
        objectives = {}
        for goal, (rows, maximum, ties) in zip(OBJECTIVES, ranks[n], strict=True):
            i = OBJECTIVES.index(goal)
            gap = abs(float(table[rows[0], i] - table[rows[1], i])) if len(rows) > 1 else None
            objectives[goal] = {
                "maximum_utility": maximum, "ties": ties,
                "runner_up_gap": gap, "near_tie": gap is not None and gap <= tolerance,
                "top": [{**record(index), "gap_to_best": float(maximum - table[index, i])} for index in rows],
            }
        serialized[str(n)] = {"nominal": record(nominal), "nominal_ties": nominal_ties,
                              "objectives": objectives, "unconditional_cvar": {
                                  "best": record(old_first[0]), "maximum": old_max, "ties": old_ties},
                              "zero_feasible_candidates": int(np.isnan(table[:, 1]).sum())}
    stability = {}
    for i, goal in enumerate(OBJECTIVES):
        pool = sorted({row for n in counts for row in ranks[n][i][0]})
        scores = weighted_scores(cache[pool], weight)
        mask = feasible[pool]
        chosen = [ranks[n][i][0][0] if ranks[n][i][0] else None for n in counts]
        bootstraps = {}
        for count, winner in zip(counts, chosen, strict=True):
            result = bootstrap_choices(scores, mask, oracle, p28["tail_fraction"], tolerance, objective=goal,
                                       count=count, repeats=setup["bootstrap_replicates"], seed=setup["bootstrap_seed"])
            result["pick_win_share"] = result["win_share"][pool.index(winner)] if winner is not None else None
            bootstraps[str(count)] = result
        stability[goal] = {"same_pick": all(choice == chosen[0] for choice in chosen) and chosen[0] is not None,
                           "finalist_indices": pool, "bootstrap": bootstraps}
    return serialized, stability, tables


class TailFitness(ColonyFitness):
    """Use fixed draws and track actual search coverage rather than exact ranks."""

    def __init__(self, rotations, cache, feasible, weight, fraction, slots, crop_count, *, conditional):
        super().__init__(rotations, cache, weight, None, fraction, slots, crop_count)
        self.feasible = feasible
        self.conditional = conditional
        self.values = np.full(len(rotations), np.nan)
        self.visited = set()

    def __call__(self, batch):
        indices = self.indices(batch)
        self.visited.update(map(int, indices))
        new = np.unique(indices[np.isnan(self.values[indices])])
        if len(new):
            scores = weighted_scores(self.metric_cache[new], self.weight)
            if self.conditional:
                self.values[new] = np.nan_to_num(conditional_cvar(scores, self.feasible[new], self.fraction), nan=0)
            else:
                self.values[new] = lower_cvar(scores, self.fraction)
        return self.values[indices]


def swarm_trials(model, layers, weight, optimizer, fitness, reference, tolerance, trial_count, restarts,
                seed_start, *, exploration=0.):
    target = set(np.flatnonzero(np.isfinite(reference) & (np.nanmax(reference) - reference <= tolerance)))
    maximum = float(np.nanmax(reference))
    rows = []
    for trial in range(trial_count):
        seeds = [seed_start + trial + step * trial_count for step in range(restarts)]
        scores = []
        visited = set()
        for seed in seeds:
            fitness.visited.clear()
            score, _ = ant_colony(model, layers, weight, optimizer, seed, fitness=fitness, exploration=exploration)
            if score is None or score > maximum + tolerance:
                raise ValueError("Unusable swarm outcome")
            scores.append(score)
            visited.update(fitness.visited)
        gaps = [max(0., maximum - score) for score in scores]
        rows.append({"seeds": seeds, "single_gap": gaps[0], "best_gap": min(gaps),
                     "distinct_visited": len(visited), "visited_exact_objective_tie": not target.isdisjoint(visited),
                     "share_visited_zero_fitness": float(np.mean(fitness.values[list(visited)] == 0))})
    return {"trials": rows, "single_hits": sum(row["single_gap"] <= tolerance for row in rows),
            "best_of_five_hits": sum(row["best_gap"] <= tolerance for row in rows),
            "best_mean_gap": float(np.mean([row["best_gap"] for row in rows])),
            "best_worst_gap": max(row["best_gap"] for row in rows),
            "mean_distinct_visited": float(np.mean([row["distinct_visited"] for row in rows])),
            "mean_zero_fitness_share": float(np.mean([row["share_visited_zero_fitness"] for row in rows])),
            "trials_visiting_a_winner": sum(row["visited_exact_objective_tie"] for row in rows)}


def swarm_check(model, rotations, cache, feasible, weight, tables, p28, setup, optimizer, layers, slots):
    crop_count = len(model.ids)
    frac, tolerance = p28["tail_fraction"], p28["tie_tolerance"]
    restarts = p28["aco_restarts"]
    smallest, largest = setup["draw_counts"][0], setup["draw_counts"][-1]
    original = TailFitness(rotations, cache[:, :smallest], feasible[:, :smallest], weight, frac, slots, crop_count,
                           conditional=False)
    diagnostic = swarm_trials(model, layers, weight, optimizer, original, tables[smallest][:, 3], tolerance,
                              setup["diagnostic_trials"], restarts, 0)
    conditional = TailFitness(rotations, cache, feasible, weight, frac, slots, crop_count, conditional=True)
    reference = tables[largest][:, 1]
    args = (conditional, reference, tolerance, setup["held_out_trials"], restarts, setup["held_out_seed_start"])
    control = swarm_trials(model, layers, weight, optimizer, *args)
    fix = {**optimizer, "iterations": setup["exploration_iterations"]}
    explored = swarm_trials(model, layers, weight, fix, *args, exploration=setup["exploration_fraction"])
    unconditional = tables[smallest][:, 3]
    return {"original_128": diagnostic, "original_zero_count": int(np.count_nonzero(unconditional == 0)),
            "conditional_control_512": control, "conditional_exploration_512": explored}


def build_farm(root, farm, crops, presets, p22, grades, optimizer, p28, setup):
    started = perf_counter()
    name = farm["farm_id"]
    out = root / "data/processed"
    seasons = json.loads((out / f"seasons_{name}.json").read_text())
    old = json.loads((out / f"robust_optimization_{name}.json").read_text())
    climate = pd.read_parquet(out / f"climate_{name}.parquet").set_index("date")

    @lru_cache(maxsize=256)
    def lookup(start, length):
        return crop_windows(climate, start, length)

    model = preload(farm, root=root, crops=crops, season_calendar=seasons, climate=climate, window_lookup=lookup)
    slots = len(model.season_labels)
    years = old["horizon_years"]
    layers = allowed_layers(model, years)
    rotations = enumerate_canonical_rotations(layers, slots)
    if len(rotations) != old["candidate_count"]:
        raise ValueError("P28 canonical candidate space changed")
    counts = setup["draw_counts"]
    if counts != sorted(set(counts)) or not counts or counts[0] <= 0 or counts[-1] > p22["joint_draws"]:
        raise ValueError("Draw counts must be increasing positive P22 prefixes")
    n = counts[-1]
    draws, hashes = sample_models(model, seasons, climate, p22, n, grades, root, lookup, primary_count=counts[0])
    if hashes[str(counts[0])] != old["sample_prefix_sha256"][str(counts[0])]:
        raise ValueError("P28 draw prefix changed")
    weights = np.array([[values[m] for m in METRICS] for values in presets.values()], dtype=float)
    nominal = score_rotations(model, rotations)[1]
    chunk = p28["rotation_chunk"]
    runtime = {"draw_preparation_seconds": perf_counter() - started}
    with TemporaryDirectory(prefix="cropswarm-stability-") as directory:
        # Build by draw with sequential writes; copy bounded rotation slabs for scoring.
        cache = np.memmap(Path(directory) / "metrics", mode="w+", dtype=np.float32,
                          shape=(n, len(rotations), len(METRICS))).transpose(1, 0, 2)
        feasible = np.memmap(Path(directory) / "feasible", mode="w+", dtype=bool, shape=(n, len(rotations))).T
        tick = perf_counter()
        prepare_metrics(draws, rotations, cache, feasible, chunk)
        runtime["cache_seconds"] = perf_counter() - tick
        print(f"{name}: draw metrics cached in {runtime['cache_seconds']:.1f}s", flush=True)
        tick = perf_counter()
        oracle = draw_oracles(draws, rotations, cache, feasible, weights, years, chunk)
        runtime["oracle_seconds"] = perf_counter() - tick
        print(f"{name}: regret references ready", flush=True)
        results = {}
        for i, (preset, weight) in enumerate(zip(presets, weights, strict=True)):
            tick = perf_counter()
            cases, stability, tables = preset_results(model, rotations, cache, feasible, oracle[:, i], weight,
                                                      nominal @ weight, p28, setup, root, grades)
            exact_seconds = perf_counter() - tick
            results[preset] = {"draw_counts": cases, "stability": stability, "exact_and_bootstrap_seconds": exact_seconds}
            if name == setup["swarm_farm"]:
                tick = perf_counter()
                results[preset]["aco"] = swarm_check(model, rotations, cache, feasible, weight, tables,
                                                     p28, setup, optimizer, layers, slots)
                results[preset]["aco_seconds"] = perf_counter() - tick
            print(f"{name}: {preset} complete", flush=True)
        runtime["cache_bytes"] = cache.nbytes + feasible.nbytes
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    runtime["peak_rss_bytes"] = int(rss if sys.platform == "darwin" else rss * 1024)
    runtime["total_seconds"] = perf_counter() - started
    return {"farm_id": name, "design": setup, "precision_tolerance": p28["tie_tolerance"],
            "tail_fraction": p28["tail_fraction"], "candidate_count": len(rotations),
            "sample_prefix_sha256": hashes, "presets": results, "compute": runtime}


def main(root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--farm", help="Rebuild only this farm")
    args = parser.parse_args()
    conf = root / "config"

    def read(name):
        return json.loads((conf / f"{name}.json").read_text())

    farms = read("farms")
    if args.farm and args.farm not in {farm["farm_id"] for farm in farms}:
        parser.error("Unknown farm")
    crops = load_crops(root / "data/crops.csv")
    settings = (read("weights_presets")["presets"], read("sensitivity"), read("evidence_grades"),
                read("optimizer"), read("robust_optimization"), read("robust_stability"))
    with threadpool_limits(limits=1):
        for farm in farms:
            name = farm["farm_id"]
            if args.farm and args.farm != name:
                continue
            data = build_farm(root, farm, crops, *settings)
            write_json(root / "data/processed" / f"robust_stability_{name}.json", data)


if __name__ == "__main__":
    main()
