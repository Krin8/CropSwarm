"""P47 exploratory rank concentration using the original P44 replay."""

from collections import Counter
import json

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from src.consensus_shortlist import FarmReplay, OUTPUT as P44_OUTPUT
from src.crops import load_crops
from src.literature_check import REFERENCES
from src.literature_variant import design as variant_design
from src.precompute_cache import write_json
from src.scoring import METRICS, ROOT

OUTPUT = "rank_concentration_p47.json"
PLAN = "docs/p47_plan.md"
CUTOFFS = (5, 10, 20)  # Tenths of a percent, to apply the cutoffs with integers.
NULL_SEED = 4747
REPLICATES = 1000
BATCH_SIZE = 16
NULL_SAMPLE_LIMIT = 262144
LIMIT = ("This exploratory comparison measures repeated high ranks across the tested scoring "
         "settings and draws. The shuffled null keeps eligibility and removes dependence among "
         "cells. These results leave real-world rotation quality unresolved.")


def top_slots(size):
    return tuple((size * cutoff + 999) // 1000 for cutoff in CUTOFFS)


def cutoff_key(cutoff):
    return f"{cutoff / 10:g}"


def ranked_prefix(values, length):
    """Return the exact leading ranks. The input order is the P44 tie order."""
    if length < len(values):
        threshold = np.partition(values, len(values) - length)[len(values) - length]
        higher = np.flatnonzero(values > threshold)
        tied = np.flatnonzero(values == threshold)
        rows = np.r_[higher, tied[:length - len(higher)]]
    else:
        rows = np.arange(len(values))
    return rows[np.lexsort((rows, -values[rows]))]


def rank_counts(replay, weights, keys, saved_counts, prior):
    """Accumulate percentile hits and independently reconcile P44's top one and three."""
    counts = np.zeros((len(weights), len(CUTOFFS), len(keys)), dtype=np.uint16)
    legacy = np.zeros((len(weights), 2, len(keys)), dtype=np.uint16)
    masks, sizes, variant_counts = Counter(), Counter(), Counter()
    for model in replay.draws():
        for variant, codes, scores, admitted, _ in replay.cells(model):
            # The first admitted row is the draw baseline. P44 orders the rest canonically.
            rows = np.flatnonzero(admitted)
            rotations = codes[rows]
            indices = np.searchsorted(keys, rotations)
            if (indices >= len(keys)).any() or not np.array_equal(keys[indices], rotations):
                raise ValueError("P44 replay contains an unexpected canonical label")
            mask = np.zeros(len(keys), dtype=bool)
            mask[indices] = True
            if mask.sum() != len(indices):
                raise ValueError("Multiple admitted rows map to the same canonical rotation")
            size = len(indices)
            sizes[size] += 1
            masks[np.packbits(mask).tobytes()] += 1
            variant_counts[variant] += 1
            slots = top_slots(size)
            prefix = min(size, max(3, slots[-1]))
            for preset, weight in enumerate(weights.values()):
                order = ranked_prefix((scores @ weight)[rows], prefix)
                leaders = indices[order]
                legacy[preset, 0, leaders[0]] += 1
                legacy[preset, 1, leaders[:3]] += 1
                for q_index, length in enumerate(slots):
                    counts[preset, q_index, leaders[:length]] += 1
    if variant_counts != Counter(dict.fromkeys(prior["variants"], prior["draws"])):
        raise ValueError("Replay does not have the saved P44 variants and draw counts")
    for preset, name in enumerate(weights):
        for i, rank in enumerate(("top1", "top3")):
            if not np.array_equal(legacy[preset, i], saved_counts[f"{name}_{rank}_count"]):
                raise ValueError(f"Replay disagrees with the saved P44 {name} {rank} counts")
    return counts, masks, sizes


def ordered_samples(rng, population, slots, size):
    """Draw independent uniform rank prefixes without replacement."""
    if slots <= 16:
        # Vectorized rejection avoids a Python sampling call for every small Kansas cell.
        result = np.empty((size, slots), dtype=np.int32)
        for col in range(slots):
            values = rng.integers(population, size=size, dtype=np.int32)
            duplicated = np.any(result[:, :col] == values[:, None], axis=1)
            while duplicated.any():
                values[duplicated] = rng.integers(population, size=int(duplicated.sum()), dtype=np.int32)
                duplicated = np.any(result[:, :col] == values[:, None], axis=1)
            result[:, col] = values
        return result
    result = np.empty((size, slots), dtype=np.int32)
    for row in result:
        row[:] = rng.choice(population, slots, replace=False, shuffle=False)
        rng.shuffle(row)
    return result


def shuffled_null(masks, universe_size, cells, rng, replications=REPLICATES):
    if sum(masks.values()) != cells:
        raise ValueError("Null eligibility masks do not match the observed cell count")
    maxima = np.zeros((replications, len(CUTOFFS)), dtype=np.uint16)
    sizes = np.zeros(maxima.shape, dtype=np.int32)
    for start in range(0, replications, BATCH_SIZE):
        batch = min(BATCH_SIZE, replications - start)
        tally = np.zeros((len(CUTOFFS), batch, universe_size), dtype=np.uint16)
        for packed, multiplicity in masks.items():
            candidates = np.flatnonzero(np.unpackbits(np.frombuffer(packed, dtype=np.uint8),
                                                      count=universe_size)).astype(np.int32)
            slots = top_slots(len(candidates))
            block_limit = max(1, NULL_SAMPLE_LIMIT // (batch * slots[-1]))
            for cell in range(0, multiplicity, block_limit):
                block = min(block_limit, multiplicity - cell)
                samples = ordered_samples(rng, len(candidates), slots[-1], batch * block)
                labels = candidates[samples]
                replicate = np.repeat(np.arange(batch), block)[:, None]
                for q_index, length in enumerate(slots):
                    np.add.at(tally[q_index], (replicate, labels[:, :length]), 1)
        maxima[start:start+batch] = tally.max(axis=2).T
        sizes[start:start+batch] = (tally >= (cells + 1) // 2).sum(axis=2).T
    return maxima, sizes


def null_reference(maxima, sizes, cells):
    low, high = np.quantile(maxima, [0.025, 0.975], method="inverted_cdf") / cells
    return {"mean_set_size": float(np.mean(sizes)), "mean_max_share": float(np.mean(maxima)) / cells,
            "max_share_95_range": [float(low), float(high)]}


def tails(maximum, size, null_maxima, null_sizes):
    max_event, size_event = null_maxima >= maximum, null_sizes >= size
    denominator = len(null_maxima) + 1
    return {"max_share_p": (1 + int(max_event.sum())) / denominator,
            "set_size_p": (1 + int(size_event.sum())) / denominator,
            "joint_p": (1 + int((max_event & size_event).sum())) / denominator}


def summarize(replay, keys, counts, masks, admitted_sizes, weights, prior, saved, rng):
    cells = int(prior["cells_per_preset"])
    maxima, sizes = shuffled_null(masks, len(keys), cells, rng)
    published = {replay.encode(strategy["crop_ids"]): strategy for strategy in saved["strategies"]}
    minimum = (cells + 1) // 2
    presets = {}
    for preset, name in enumerate(weights):
        outcomes = {}
        for q_index, q in enumerate(CUTOFFS):
            hits = counts[preset, q_index]
            selected = sorted(np.flatnonzero(hits >= minimum), key=lambda i: (-int(hits[i]), int(keys[i])))

            def record(index):
                key, count = int(keys[index]), int(hits[index])
                entry = {"rotation_key": key, "cycle": replay.decode(key), "count": count,
                         "share": count / cells, "member": count >= minimum}
                if key in published:
                    strategy = published[key]
                    entry.update(strategy=strategy["strategy_id"], evidence_label=strategy["evidence_label"])
                return entry

            max_hits = int(hits.max())
            outcomes[cutoff_key(q)] = {
                "size": len(selected), "members": [record(index) for index in selected],
                "largest_share": max_hits / cells,
                "published": [record(int(np.searchsorted(keys, key))) for key in published],
                **tails(max_hits, len(selected), maxima[:, q_index], sizes[:, q_index]),
            }
        presets[name] = outcomes
    return {"name": prior["name"], "variants": prior["variants"], "draws": prior["draws"],
            "cells_per_preset": cells, "rotation_count": len(keys), "p44_counts_reproduced": True,
            "admitted_rotations_per_cell": [min(admitted_sizes), max(admitted_sizes)],
            "top_slots_per_cell": {cutoff_key(q): [top_slots(min(admitted_sizes))[i],
                                                   top_slots(max(admitted_sizes))[i]]
                                   for i, q in enumerate(CUTOFFS)},
            "null": {cutoff_key(q): null_reference(maxima[:, i], sizes[:, i], cells)
                     for i, q in enumerate(CUTOFFS)},
            "presets": presets}


def build(root=ROOT, output_dir=None):
    def read(path):
        return json.loads((root / path).read_text())

    data = root / "data/processed"
    earlier = read(data / P44_OUTPUT)
    plans, parameters, _ = variant_design(read(REFERENCES))
    config = read("config/sensitivity.json")
    grades = read("config/evidence_grades.json")
    weights = {name: np.array([row[metric] for metric in METRICS])
               for name, row in read("config/weights_presets.json")["presets"].items()}
    farms = read("config/farms.json")
    crops = load_crops(root / "data/crops.csv", farms=farms)
    if config["seed"] != earlier["design"]["seed"]:
        raise ValueError("P22 seed differs from the published P44 seed")
    results = {}
    with threadpool_limits(limits=1):
        for farm, seed in zip(farms, np.random.SeedSequence(NULL_SEED).spawn(len(farms)), strict=True):
            farm_id = farm["farm_id"]
            prior = earlier["farms"][farm_id]
            saved = read(data / f"strategies_{farm_id}.json")
            p22 = read(data / f"sensitivity_{farm_id}.json")
            replay = FarmReplay(root, farm, crops, config, plans, parameters, p22, grades)
            if ([variant.key for variant in replay.variants] != prior["variants"] or
                    len(replay.samples) != prior["draws"] or saved["horizon_years"] != replay.horizon):
                raise ValueError(f"P44 variant, draw or shortlist scope differs for {farm_id}")
            previous = pd.read_csv(data / prior["counts_file"])
            keys = previous["rotation_key"].to_numpy()
            if (len(keys) != prior["rotation_count"] or (keys[1:] <= keys[:-1]).any() or
                    not (previous["cells_per_preset"] == prior["cells_per_preset"]).all()):
                raise ValueError(f"The saved P44 canonical universe is inconsistent for {farm_id}")
            if not all(replay.encode(row["crop_ids"]) in keys for row in saved["strategies"]):
                raise ValueError(f"A published strategy is absent from the P44 canonical universe for {farm_id}")
            counts, masks, sizes = rank_counts(replay, weights, keys, previous, prior)
            results[farm_id] = summarize(replay, keys, counts, masks, sizes, weights, prior, saved,
                                         np.random.default_rng(seed))
            print(f"{farm_id}: reconciled P44 rankings and completed {REPLICATES} null replicates", flush=True)
    study = {"label": "EXPLORATORY · illustrative, validate locally", "plan": PLAN,
             "design": {"q_pct": [q / 10 for q in CUTOFFS], "min_share": 0.5,
                        "draw_seed": config["seed"], "null_seed": NULL_SEED,
                        "null_replicates": REPLICATES, "source": PLAN},
             "limit": LIMIT, "farms": results}
    write_json((output_dir if output_dir is not None else data) / OUTPUT, study)
    return study


if __name__ == "__main__":
    build()
