"""Rank, threshold, dominance and isolated reproducibility tests for P44."""

from collections import Counter

import numpy as np

from src.consensus_shortlist import ranks, strict_dominator, threshold_keys


def test_top_three_uses_distinct_admitted_rows_and_baseline_first_ties():
    matrix = np.array([[.9, .5], [.9, .5], [.9, .5], [.7, .4], [1., 1.]])
    weights = np.array([.5, .5])
    np.testing.assert_array_equal(ranks(matrix, weights, np.array([True, False, True, True, False])),
                                  [0, 2, 3])
    assert ranks(matrix, weights, np.array([False, False, True, False, False])) == [2]


def test_threshold_counts_include_exact_bound_and_keep_ineligible_in_denominator():
    top = Counter({4: 5, 7: 4, 3: 6, 5: 0})
    assert threshold_keys(top, 10, 40) == {3, 4, 7}
    assert threshold_keys(top, 10, 50) == {3, 4}
    assert threshold_keys(top, 10, 60) == {3}
    assert threshold_keys(top, 10, 70) == set()


def test_strict_dominance_requires_six_better_metrics_and_a_feasible_witness():
    target = np.full(6, .2)
    scores = np.array([[.3] * 6, [.2, .4, .4, .4, .4, .4], [.2 + 1e-13] * 6])
    assert strict_dominator(scores, np.array([True, True, True]), target)
    assert not strict_dominator(scores, np.array([False, True, True]), target)
    assert not strict_dominator(scores, np.array([False, False, False]), target)


def test_admitted_flagged_baseline_is_a_dominance_target_and_others_are_not():
    from src.consensus_shortlist import dominance_counts

    class Replay:
        def draws(self):
            return (object(),)

        def cells(self, _):
            yield ("original", np.array([10, 10, 20, 30]),
                   np.array([[.2] * 6, [.2] * 6, [.4] * 6, [.5] * 6]),
                   np.array([True, False, True, False]), np.array([False, False, True, False]))

    assert dominance_counts(Replay(), [10, 20, 30]) == {
        10: {"admitted_cells": 1, "strictly_dominated_cells": 1},
        20: {"admitted_cells": 1, "strictly_dominated_cells": 0},
        30: {"admitted_cells": 0, "strictly_dominated_cells": 0},
    }


def test_file_totals_and_saved_empty_sets():
    import json

    import pandas as pd

    from src.consensus_shortlist import OUTPUT, ROOT

    processed = ROOT / "data/processed"
    report = json.loads((processed / OUTPUT).read_text())
    for farm in report["farms"].values():
        rows = pd.read_csv(processed / farm["counts_file"])
        assert rows.rotation_key.is_unique and len(rows) == farm["rotation_count"]
        cells = farm["cells_per_preset"]
        for preset, data in farm["presets"].items():
            first, top = rows[f"{preset}_top1_count"], rows[f"{preset}_top3_count"]
            assert first.sum() == cells and (first <= top).all()
            assert 3 * cells - 2 * farm["cells_with_fewer_than_three"] <= top.sum() <= 3 * cells
            assert data["leaders"][0]["top3_count"] == top.max()
            assert data["fixed_baseline"]["top1_count"] == first[rows.rotation_key.eq(
                data["fixed_baseline"]["rotation_key"])].item()
            for value, entry in data["thresholds"].items():
                assert entry["size"] == int((top * 100 >= cells * int(value)).sum()) == 0
                assert entry["strictly_dominated_share"] is None


def test_offline_replay_is_byte_identical_and_preserves_all_prior_results(tmp_path):
    import hashlib

    from src.consensus_shortlist import OUTPUT, ROOT, build

    dirs = (ROOT / "data/processed", ROOT / "config")
    protected = [path for directory in dirs for path in directory.rglob("*")
                 if path.is_file() and not path.name.startswith("consensus_shortlist_p44")]
    protected.extend(ROOT / path for path in ("data/crops.csv", "data/p35_literature.json", "src/scoring.py",
                                              "src/optimizer.py", "src/sensitivity.py", "src/literature_variant.py"))

    def hashes():
        return {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}

    before = hashes()
    report = build(output_dir=tmp_path)
    assert before and hashes() == before
    outputs = [OUTPUT, *(farm["counts_file"] for farm in report["farms"].values())]
    for name in outputs:
        assert (tmp_path / name).read_bytes() == (dirs[0] / name).read_bytes()
