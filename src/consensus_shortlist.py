"""P44 exact top-k frequencies across fixed scoring variants and P22 draws."""

from collections import Counter
from dataclasses import asdict
from functools import lru_cache
import csv
import gzip
import io
import json

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from src.crops import load_crops
from src.data_pipeline import atomic_write
from src.evidence import evidence_for_strategy
from src.literature_check import REFERENCES
from src.literature_variant import KANSAS, NUMERICAL_TOLERANCE, Batch, design, eligible, transitions
from src.optimizer import allowed_layers, canonical_cycle, enumerate_canonical_rotations
from src.precompute_cache import write_json
from src.robust_optimization import rotation_keys
from src.scoring import METRICS, ROOT, baseline_indices, crop_windows, preload, score_rotations
from src.sensitivity import apply_values, inventory, joint_samples

OUTPUT = "consensus_shortlist_p44.json"
THRESHOLDS = (40, 50, 60)
TOP_K = 3


def ranks(scores, weights, admitted, k=TOP_K):
    """Return up to k ranks. Row order breaks exact ties."""
    values = scores @ weights
    values[~admitted] = -np.inf
    order = []
    for _ in range(min(k, int(admitted.sum()))):
        first = int(values.argmax())
        order.append(first)
        values[first] = -np.inf
    return order


def strict_dominator(scores, feasible, target):
    return bool(np.any(np.all(scores[feasible] - target > NUMERICAL_TOLERANCE, axis=1)))


def threshold_keys(tally, cells, threshold):
    """Integer arithmetic makes inclusion at the exact threshold deterministic."""
    return {key for key, count in tally.items() if count * 100 >= cells * threshold}


class FarmReplay:
    def __init__(self, root, farm, crops, config, chosen, parameters, saved_p22, grades):
        self.root = root
        self.farm = farm
        self.config = config
        self.variants = chosen if farm["farm_id"] == KANSAS else chosen[:1]
        self.parameters = parameters
        self.reductions = sorted({variant.water_mm for variant in self.variants})
        self.horizon = saved_p22["horizon_years"]
        self.slots = farm["seasons_per_year"]
        self.saved_p22 = saved_p22
        data = root / "data/processed"
        self.seasons = json.loads((data / f"seasons_{farm['farm_id']}.json").read_text())
        self.climate = pd.read_parquet(data / f"climate_{farm['farm_id']}.parquet").set_index("date")
        self.windows = lru_cache(maxsize=256)(self._crop_windows)
        self.enumerate = lru_cache(maxsize=8)(self._enumerate)
        self.model = self._preload(farm, crops, None, self.seasons)
        self.inputs = inventory(self.model, self.seasons, grades, config)
        if config != saved_p22["design"] or json.loads(json.dumps([asdict(i) for i in self.inputs])) != saved_p22["inputs"]:
            raise ValueError(f"P44 inputs differ from the saved P22 study for {farm['farm_id']}")
        self.samples = joint_samples(self.inputs, config)
        self.ids = self.model.ids
        self.width = self.slots * self.horizon
        self.places = len(self.ids) ** np.arange(self.width - 1, -1, -1, dtype=np.int64)

    def _preload(self, farm, crops, policy, seasons):
        return preload(farm, root=self.root, crops=crops, policy=policy, season_calendar=seasons,
                       climate=self.climate, window_lookup=self.windows)

    def _crop_windows(self, start, length):
        return crop_windows(self.climate, start, length)

    def _enumerate(self, layers):
        rotations = enumerate_canonical_rotations([np.asarray(layer, dtype=int) for layer in layers], self.slots)
        return rotations, rotation_keys(rotations, len(self.ids))

    def encode(self, cycle):
        row = [self.ids.index(crop) for year in cycle for crop in year]
        row = canonical_cycle(row, self.slots)
        return int(np.asarray(row) @ self.places)

    def decode(self, key):
        indices = (key // self.places) % len(self.ids)
        return [[self.ids[i] for i in indices[start:start + self.slots]]
                for start in range(0, self.width, self.slots)]

    def cells(self, model):
        layers = tuple(tuple(layer) for layer in allowed_layers(model, self.horizon))
        rotations, codes = self.enumerate(layers)
        baseline = canonical_cycle(baseline_indices(model, self.horizon), self.slots)
        baseline_code = int(np.asarray(baseline) @ self.places)
        rows = np.vstack([baseline, rotations])
        codes = np.r_[baseline_code, codes]
        if len(self.variants) == 1:
            _, scores, flags = score_rotations(model, rows)
            states = [("original", scores, eligible(flags))]
        else:
            batch = Batch(model, rows, transitions(model, self.parameters, self.reductions))
            states = ((variant.key, scores, eligible(flags)) for variant in self.variants
                      for _, scores, flags in (batch.evaluate(variant),))
        for name, scores, feasible in states:
            # If the baseline is feasible, its duplicate still serves as a feasible witness.
            admitted = feasible & (codes != baseline_code)
            admitted[0] = True
            yield name, codes, scores, admitted, feasible

    def draws(self):
        for sample in self.samples:
            yield self._preload(*apply_values(self.model, self.seasons, self.inputs, sample))


def verify_winners(replay, original_histograms, per_variant, references, p43):
    for preset, histogram in original_histograms.items():
        saved = replay.saved_p22["presets"][preset]
        expected = {replay.encode(row["cycle"]): row["count"] for row in saved["joint"]["winners"]}
        if histogram != expected or references["original"][preset] != replay.encode(saved["reference_winner"]):
            raise ValueError(f"P44 did not reproduce original P22 winners for {replay.farm['farm_id']}/{preset}")
        for variant in replay.variants:
            source = p43["p22"][variant.key][preset]
            changes = per_variant[variant.key][preset]
            reference = references[variant.key][preset]
            expected_change_fraction = source["winner_change_fraction"]
            if (reference != replay.encode(source["reference_rotation"])
                    or not np.isclose(changes / len(replay.samples), expected_change_fraction, rtol=0, atol=1e-12)):
                raise ValueError(f"P44 did not reproduce P43 changes for {variant.key}/{preset}")


def count_ranks(replay, weights, saved, p43):
    # A dense boolean direct index avoids hashing millions of inactive rotation labels on each draw.
    seen = np.zeros(len(replay.ids) ** replay.width, dtype=bool)
    fixed_codes = [replay.encode(row["crop_ids"]) for row in saved["strategies"]]
    seen[fixed_codes] = True
    references = {}
    for name, codes, scores, admitted, _ in replay.cells(replay.model):
        seen[codes[admitted]] = True
        references[name] = {key: int(codes[ranks(scores, weight, admitted, k=1)[0]])
                            for key, weight in weights.items()}
    top1, top3, original = ({name: Counter() for name in weights} for _ in range(3))
    draw_baseline = {name: [0, 0] for name in weights}
    changes = {variant.key: dict.fromkeys(weights, 0) for variant in replay.variants}
    short_cells = flagged_baselines = 0
    for drawn in replay.draws():
        for variant, codes, scores, admitted, feasible in replay.cells(drawn):
            baseline = int(codes[0])
            if variant == "original":
                seen[codes[admitted]] = True
            short_cells += int(admitted.sum() < TOP_K)
            flagged_baselines += int(not feasible[0])
            for name, weight in weights.items():
                top = [int(codes[i]) for i in ranks(scores, weight, admitted)]
                top1[name][top[0]] += 1
                top3[name].update(top)
                draw_baseline[name][0] += top[0] == baseline
                draw_baseline[name][1] += baseline in top
                changes[variant][name] += top[0] != references[variant][name]
                if variant == "original":
                    original[name][top[0]] += 1
    verify_winners(replay, original, changes, references, p43)
    return (np.flatnonzero(seen), top1, top3, original, draw_baseline, references["original"],
            short_cells, flagged_baselines)


def dominance_counts(replay, candidates):
    result = {key: {"admitted_cells": 0, "strictly_dominated_cells": 0} for key in candidates}
    if not candidates:
        return result
    for drawn in replay.draws():
        for _, codes, scores, admitted, feasible in replay.cells(drawn):
            # The alternatives remain in canonical order, and the baseline is the first row.
            for candidate in candidates:
                index = 0 if candidate == codes[0] else 1 + np.searchsorted(codes[1:], candidate)
                if index >= len(codes) or codes[index] != candidate or not admitted[index]:
                    continue
                result[candidate]["admitted_cells"] += 1
                result[candidate]["strictly_dominated_cells"] += strict_dominator(scores, feasible, scores[index])
    return result


def write_rotations(path, replay, keys, top1, top3, cells):
    def output(temp):
        with temp.open("wb") as raw, gzip.GzipFile(fileobj=raw, filename="", mtime=0) as archive:
            with io.TextIOWrapper(archive, encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream, lineterminator="\n")
                slot_cols = [f"year_{year + 1}_slot_{slot + 1}" for year in range(replay.horizon)
                             for slot in range(replay.slots)]
                rank_cols = [f"{preset}_{metric}" for preset in top1
                             for metric in ("top1_count", "top3_count", "top1_share", "top3_share")]
                writer.writerow(["rotation_key", *slot_cols, "cells_per_preset", *rank_cols])
                for key in keys:
                    row = [int(key), *(crop for year in replay.decode(key) for crop in year), cells]
                    for name in top1:
                        a, b = top1[name][key], top3[name][key]
                        row.extend((a, b, a / cells, b / cells))
                    writer.writerow(row)
    atomic_write(path, output)


def summarize_farm(replay, weights, saved, p43, grades, out):
    keys, top1, top3, original, draw_baseline, references, short, flags = count_ranks(replay, weights, saved, p43)
    cells = len(replay.samples) * len(replay.variants)
    pooled_sets = {name: {value: threshold_keys(tally, cells, value) for value in THRESHOLDS}
                   for name, tally in top3.items()}
    combined = set().union(*(ids for sets in pooled_sets.values() for ids in sets.values()))
    dominance = dominance_counts(replay, combined)
    fixed = {replay.encode(row["crop_ids"]): row for row in saved["strategies"]}
    baseline_row, *shortlist_rows = saved["strategies"]
    baseline = replay.encode(baseline_row["crop_ids"])
    shortlist = {replay.encode(row["crop_ids"]) for row in shortlist_rows}
    counts_filename = f"consensus_shortlist_p44_{replay.farm['farm_id']}.csv.gz"
    write_rotations(out / counts_filename, replay, keys, top1, top3, cells)

    @lru_cache(maxsize=None)
    def evidence(key):
        if key in fixed:
            return {"overall": fixed[key]["evidence_label"],
                    "metrics": {metric: row["evidence"]["label"] for metric, row in fixed[key]["metrics"].items()}}
        sequence = [(key // power) % len(replay.ids) for power in replay.places]
        report = evidence_for_strategy(replay.model, sequence, root=replay.root, config=grades)
        return {"overall": report["label"], "metrics": {field: row["label"] for field, row in report["metrics"].items()}}

    def record(key, preset):
        item = {"rotation_key": key, "cycle": replay.decode(key),
                "top1_count": top1[preset][key], "top3_count": top3[preset][key],
                "top1_share": top1[preset][key] / cells, "top3_share": top3[preset][key] / cells,
                "evidence": evidence(key)}
        if key in fixed:
            item["published_strategy"] = fixed[key]["strategy_id"]
        if key in dominance:
            item.update(dominance[key])
        return item

    presets = {}
    for name, cases in pooled_sets.items():
        thresholds = {}
        for value, ids in cases.items():
            overlap = ids & shortlist
            admitted = sum(dominance[key]["admitted_cells"] for key in ids)
            dominated = sum(dominance[key]["strictly_dominated_cells"] for key in ids)
            ordered = sorted(ids, key=lambda key: (-top3[name][key], -top1[name][key], key))
            winners = sum(original[name][key] for key in ids)
            thresholds[str(value)] = {
                "size": len(ids), "members": [record(key, name) for key in ordered],
                "original_nominal_member": references[name] in ids,
                "original_draw_winners_in_consensus": winners,
                "original_draw_winners_share": winners / len(replay.samples),
                "baseline_member": baseline in ids,
                "shortlist_overlap": len(overlap),
                "both": [record(key, name) for key in ordered if key in overlap],
                "consensus_only": [record(key, name) for key in ordered if key not in shortlist and key != baseline],
                "shortlist_only": [record(key, name) for key in sorted(shortlist - ids)],
                "members_ever_dominated": sum(dominance[key]["strictly_dominated_cells"] > 0 for key in ids),
                "admitted_member_cells": admitted, "strictly_dominated_member_cells": dominated,
                "strictly_dominated_share": dominated / admitted if admitted else None,
            }
        leaders = sorted(top3[name], key=lambda key: (-top3[name][key], -top1[name][key], key))[:TOP_K]
        presets[name] = {
            "thresholds": thresholds, "original_nominal": record(references[name], name),
            "fixed_baseline": record(baseline, name), "leaders": [record(key, name) for key in leaders],
            "draw_baseline": {"top1_share": draw_baseline[name][0] / cells, "top3_share": draw_baseline[name][1] / cells},
        }
    return {"name": replay.farm["name"], "variants": [v.key for v in replay.variants],
            "draws": len(replay.samples), "cells_per_preset": cells, "rotation_count": len(keys),
            "cells_with_fewer_than_three": short, "flagged_baseline_cells": flags,
            "counts_file": counts_filename, "presets": presets}


def build(root=ROOT, output_dir=None):
    def read(path):
        return json.loads((root / path).read_text())

    variants, settings, evidence = design(read(REFERENCES))
    p43 = read("data/processed/literature_variant_p43.json")
    if [variant.key for variant in variants] != [item["id"] for item in p43["variants"]]:
        raise ValueError("P44 configurations differ from the published P43 variants")
    config = read("config/sensitivity.json")
    grades = read("config/evidence_grades.json")
    weights = {name: np.array([values[metric] for metric in METRICS])
               for name, values in read("config/weights_presets.json")["presets"].items()}
    crops = load_crops(root / "data/crops.csv")
    out = output_dir if output_dir is not None else root / "data/processed"
    farms = {}
    with threadpool_limits(limits=1):
        for farm in read("config/farms.json"):
            farm_id = farm["farm_id"]
            saved_p22 = read(f"data/processed/sensitivity_{farm_id}.json")
            saved = read(f"data/processed/strategies_{farm_id}.json")
            if saved["horizon_years"] != saved_p22["horizon_years"]:
                raise ValueError(f"Published shortlist and P22 horizon differ for {farm_id}")
            replay = FarmReplay(root, farm, crops, config, variants, settings, saved_p22, grades)
            farms[farm_id] = summarize_farm(replay, weights, saved, p43["farms"][farm_id], grades, out)
    result = {"label": "illustrative, validate locally", "source": "docs/p44_plan.md",
              "design": {"primary_threshold": THRESHOLDS[1], "thresholds": THRESHOLDS, "top_k": TOP_K,
                         "seed": config["seed"], "p42": "Absent from merged history at preregistration"},
              "literature_evidence": evidence, "farms": farms}
    write_json(out / OUTPUT, result)
    return result


if __name__ == "__main__":
    build()
