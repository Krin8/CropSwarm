"""Expanded exact consensus replay over the published P42, P43 and P46 settings."""

from collections import Counter
from functools import lru_cache
import json

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from src import literature_variant as p43
from src import regional_scoring_variants as p46
from src import smooth_climate_fit as p42
from src.consensus_shortlist import (TOP_K, THRESHOLDS, FarmReplay, dominance_counts, ranks, threshold_keys,
                                     write_rotations)
from src.crops import load_crops
from src.evidence import evidence_for_strategy
from src.literature_check import REFERENCES
from src.optimizer import allowed_layers, canonical_cycle
from src.precompute_cache import write_json
from src.scoring import METRICS, ROOT, baseline_indices, score_rotations

OUTPUT = "consensus_shortlist_p44b.json"
SMOOTH = "p42_smooth"


class ExpandedReplay(FarmReplay):
    """Keep P44 replay and tie ordering, with each distinct local overlay once."""

    def __init__(self, *args, correction=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.legacy = tuple(variant.key for variant in self.variants)
        self.correction = correction
        self.regional = ({f"p46_{level}": level for level in p46.LEVELS[1:]} if correction is not None else {})
        self.names = (*self.legacy, SMOOTH, *self.regional)

    def cells(self, model):
        yield from super().cells(model)
        yield self.scored_cell(SMOOTH, p42.smooth_model(model))
        for name, level in self.regional.items():
            yield self.scored_cell(name, p46.regional_model(model, self.correction, level))

    def scored_cell(self, name, model):
        layers = tuple(tuple(layer) for layer in allowed_layers(model, self.horizon))
        rotations, codes = self.enumerate(layers)
        baseline = canonical_cycle(baseline_indices(model, self.horizon), self.slots)
        baseline_code = int(np.asarray(baseline) @ self.places)
        rows = np.vstack([baseline, rotations])
        codes = np.r_[baseline_code, codes]
        _, scores, flags = score_rotations(model, rows)
        feasible = p43.eligible(flags)
        admitted = feasible & (codes != baseline_code)
        admitted[0] = True
        return name, codes, scores, admitted, feasible


def saved_references(replay, p43_results, p42_results, p46_results):
    result = {
        name: {preset: (row["reference_rotation"], row["winner_change_fraction"])
               for preset, row in p43_results["p22"][name].items()}
        for name in replay.legacy
    }
    result[SMOOTH] = {preset: (row["smooth_reference"], row["smooth_change_fraction"])
                      for preset, row in p42_results["p22"].items()}
    for name, level in replay.regional.items():
        result[name] = {
            preset: (row["reference_winner"], row["winner_change_fraction"])
            for preset, row in p46_results["levels"][level]["p22"].items()
        }
    return result


def verify_legacy(path, old, seen, first, third):
    previous = pd.read_csv(path)
    keys = previous["rotation_key"].to_numpy()
    if len(keys) != old["rotation_count"] or not np.array_equal(keys, np.flatnonzero(seen)):
        raise ValueError("P44 canonical rotation coverage did not reproduce")
    if not (previous["cells_per_preset"] == old["cells_per_preset"]).all():
        raise ValueError("P44 prior CSV has an inconsistent denominator")
    key_set = set(keys)
    for name in first:
        for pos, counts in (("top1", first[name]), ("top3", third[name])):
            matched = np.fromiter((counts[key] for key in keys), dtype=np.int64, count=len(keys))
            if not set(counts).issubset(key_set) or not np.array_equal(matched, previous[f"{name}_{pos}_count"]):
                raise ValueError(f"P44 {pos} counts did not reproduce for {name}")


def count_frequencies(replay, weights, fixed_codes, expected, legacy_report, legacy_path):
    size = len(replay.ids) ** replay.width
    seen = np.zeros(size, dtype=bool)
    old_seen = np.zeros_like(seen)
    seen[fixed_codes] = old_seen[fixed_codes] = True
    frequencies = {
        scope: {preset: (Counter(), Counter()) for preset in weights}
        for scope in ("expanded", "legacy")
    }
    references = {}
    for name, codes, scores, admitted, _ in replay.cells(replay.model):
        seen[codes[admitted]] = True
        if name in replay.legacy:
            old_seen[codes[admitted]] = True
        references[name] = {preset: int(codes[ranks(scores, weight, admitted, k=1)[0]])
                            for preset, weight in weights.items()}
    first_by_variant = {name: {preset: Counter() for preset in weights} for name in replay.names}
    baseline_hits = {preset: [0, 0] for preset in weights}
    short_cells = flagged_baselines = 0
    cell_counts = Counter()
    for drawn in replay.draws():
        for name, codes, scores, admitted, feasible in replay.cells(drawn):
            seen[codes[admitted]] = True
            cell_counts[name] += 1
            legacy = name in replay.legacy
            if legacy:
                old_seen[codes[admitted]] = True
            short_cells += int(admitted.sum() < TOP_K)
            flagged_baselines += int(not feasible[0])
            for preset, weight in weights.items():
                top = [int(codes[i]) for i in ranks(scores, weight, admitted)]
                first_by_variant[name][preset][top[0]] += 1
                baseline_hits[preset][0] += top[0] == codes[0]
                baseline_hits[preset][1] += codes[0] in top
                for scope in ("expanded", "legacy") if legacy else ("expanded",):
                    first, third = frequencies[scope][preset]
                    first[top[0]] += 1
                    third.update(top)
    n = len(replay.samples)
    if cell_counts != dict.fromkeys(replay.names, n):
        raise ValueError("Each P44b variant must contribute exactly one cell per P22 draw")
    for name, presets in first_by_variant.items():
        for preset, counts in presets.items():
            if name == "original":
                saved = replay.saved_p22["presets"][preset]["joint"]["winners"]
                if counts != {replay.encode(row["cycle"]): row["count"] for row in saved}:
                    raise ValueError(f"P22 original winner histogram changed for {preset}")
            previous_cycle, previous_rate = expected[name][preset]
            reference = references[name][preset]
            rate = 1 - counts[reference] / n
            if reference != replay.encode(previous_cycle) or not np.isclose(rate, previous_rate, atol=1e-12, rtol=0):
                raise ValueError(f"Saved winner change did not reproduce for {name}/{preset}")

    old_first, old_third = ({preset: v[i] for preset, v in frequencies["legacy"].items()} for i in range(2))
    verify_legacy(legacy_path, legacy_report, old_seen, old_first, old_third)
    return {"keys": np.flatnonzero(seen), "counts": frequencies["expanded"], "baseline_hits": baseline_hits,
            "original_references": references["original"], "short_cells": short_cells,
            "flagged_baselines": flagged_baselines}


def summarize(replay, counts, saved, legacy, grades, output_dir):
    cell_count = len(replay.samples) * len(replay.names)
    fixed = {replay.encode(row["crop_ids"]): row for row in saved["strategies"]}
    baseline, *shortlist = fixed
    frequencies = counts["counts"]
    top1, top3 = ({name: pair[i] for name, pair in frequencies.items()} for i in range(2))
    candidates = {name: {level: threshold_keys(values, cell_count, level) for level in THRESHOLDS}
                  for name, values in top3.items()}
    checked = set().union(*(members for levels in candidates.values() for members in levels.values()))
    dominance = dominance_counts(replay, checked)
    filename = f"consensus_shortlist_p44b_{replay.farm['farm_id']}.csv.gz"
    write_rotations(output_dir / filename, replay, counts["keys"], top1, top3, cell_count)

    @lru_cache(maxsize=None)
    def evidence(key):
        if key in fixed:
            row = fixed[key]
            return {"overall": row["evidence_label"], "metrics": {
                name: field["evidence"]["label"] for name, field in row["metrics"].items()}}
        sequence = [(key // int(place)) % len(replay.ids) for place in replay.places]
        row = evidence_for_strategy(replay.model, sequence, root=replay.root, config=grades)
        return {"overall": row["label"], "metrics": {name: field["label"] for name, field in row["metrics"].items()}}

    def record(key, preset):
        first, third = top1[preset][key], top3[preset][key]
        return {"rotation_key": key, "cycle": replay.decode(key), "top1_count": first, "top3_count": third,
                "top1_share": first / cell_count, "top3_share": third / cell_count,
                "published_strategy": fixed[key]["strategy_id"] if key in fixed else None,
                "evidence": evidence(key), **dominance.get(key, {})}

    presets = {}
    for preset, sets in candidates.items():
        original = counts["original_references"][preset]
        previous = legacy["presets"][preset]
        thresholds = {}
        for level, members in sets.items():
            prior = previous["thresholds"][str(level)]
            ordered = sorted(members, key=lambda key: (-top3[preset][key], -top1[preset][key], key))
            eligible_cells = sum(dominance[key]["admitted_cells"] for key in ordered)
            dominated_cells = sum(dominance[key]["strictly_dominated_cells"] for key in ordered)
            thresholds[str(level)] = {
                "size": len(members), "p44_size": prior["size"], "members": [record(key, preset) for key in ordered],
                "baseline_member": baseline in members, "original_nominal_member": original in members,
                "shortlist_overlap": len(members.intersection(shortlist)),
                "admitted_member_cells": eligible_cells, "dominated_member_cells": dominated_cells,
                "strictly_dominated_share": dominated_cells / eligible_cells if eligible_cells else None,
                "members_ever_dominated": sum(bool(dominance[key]["strictly_dominated_cells"]) for key in ordered),
            }
        leaders = sorted(top3[preset], key=lambda key: (-top3[preset][key], -top1[preset][key], key))[:TOP_K]
        baseline_hits = counts["baseline_hits"][preset]
        presets[preset] = {
            "thresholds": thresholds,
            "fixed_baseline": record(baseline, preset), "original_nominal": record(original, preset),
            "leaders": [record(key, preset) for key in leaders],
            "displayed_alternatives": [record(key, preset) for key in shortlist],
            "draw_baseline": {"top1_share": baseline_hits[0] / cell_count, "top3_share": baseline_hits[1] / cell_count},
            "p44": {name: previous[name] for name in ("fixed_baseline", "original_nominal", "leaders", "draw_baseline")},
        }
    return {"name": replay.farm["name"], "variants": replay.names, "draws": len(replay.samples),
            "cells_per_preset": cell_count, "counts_file": filename, "rotation_count": len(counts["keys"]),
            "p44_cells_per_preset": legacy["cells_per_preset"], "p44_rotation_count": legacy["rotation_count"],
            "cells_with_fewer_than_three": counts["short_cells"], "flagged_baseline_cells": counts["flagged_baselines"],
            "legacy_counts_reproduced": True, "saved_variant_winner_rates_reproduced": True, "presets": presets}


def build(root=ROOT, output_dir=None):
    def read(path):
        return json.loads((root / path).read_text())

    data = root / "data/processed"
    out = output_dir if output_dir is not None else data
    out.mkdir(parents=True, exist_ok=True)
    earlier = read(data / "consensus_shortlist_p44.json")
    smooth = read(data / p42.OUTPUT)
    kansas = read(data / p43.OUTPUT)
    regional = read(data / p46.OUTPUT)
    variants, parameters, sources = p43.design(read(REFERENCES))
    if [variant.key for variant in variants] != [variant["id"] for variant in kansas["variants"]]:
        raise ValueError("P43 saved variant list does not match the current literature definitions")
    farms = read("config/farms.json")
    crops = load_crops(root / "data/crops.csv", farms=farms)
    corrections, combinations = p46.design(crops, read("data/p45_literature.json"))
    if any(case["local_levels"].get(farm["farm_id"], "original") != reference["local_levels"][farm["farm_id"]]
           for case, reference in zip(combinations, regional["configurations"], strict=True) for farm in farms):
        raise ValueError("Saved P46 combination mapping does not match the registered design")
    if corrections != regional["corrections"] or smooth["design"]["half_band_hot_days"] != p42.HEAT_BAND_DAYS:
        raise ValueError("P42 or P46 saved inputs do not match their registered design")
    config = read("config/sensitivity.json")
    grades = read("config/evidence_grades.json")
    weights = {name: np.array([row[metric] for metric in METRICS])
               for name, row in read("config/weights_presets.json")["presets"].items()}
    summaries = {}
    with threadpool_limits(limits=1):
        for farm in farms:
            farm_id = farm["farm_id"]
            saved = read(data / f"strategies_{farm_id}.json")
            p22 = read(data / f"sensitivity_{farm_id}.json")
            prior = earlier["farms"][farm_id]
            replay = ExpandedReplay(root, farm, crops, config, variants, parameters, p22, grades,
                                    correction=corrections.get(farm_id))
            if tuple(prior["variants"]) != replay.legacy or saved["horizon_years"] != replay.horizon:
                raise ValueError("P44 variant scope or shortlist horizon changed")
            expected = saved_references(replay, kansas["farms"][farm_id], smooth["farms"][farm_id],
                                        regional["farms"][farm_id])
            fixed = [replay.encode(row["crop_ids"]) for row in saved["strategies"]]
            counts = count_frequencies(replay, weights, fixed, expected, prior, data / prior["counts_file"])
            summaries[farm_id] = summarize(replay, counts, saved, prior, grades, out)
    report = {"label": "illustrative, validate locally", "plan": "docs/p44b_plan.md",
              "design": {"thresholds": THRESHOLDS, "primary_threshold": THRESHOLDS[1], "top_k": TOP_K,
                         "seed": config["seed"]},
              "p43_evidence": sources, "p46_evidence": corrections, "p42_design": smooth["design"],
              "p46_global_to_local": [{farm: "original" if level == "original" else f"p46_{level}"
                                      for farm, level in case["local_levels"].items()}
                                     for case in regional["configurations"]],
              "farms": summaries}
    write_json(out / OUTPUT, report)
    return report


if __name__ == "__main__":
    build()
