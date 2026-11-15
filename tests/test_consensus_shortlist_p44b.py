"""P44b ranking, denominator, and replay regressions."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.consensus_shortlist_p44b import SMOOTH, count_frequencies, verify_legacy
from src.consensus_shortlist import threshold_keys


def test_all_variant_cells_count_with_baseline_first_and_unique_top_three(tmp_path):
    def cells(draw):
        codes = np.array([1, 1, 2, 3, 4])
        old_rank = np.array([[.6], [.6], [.6], [.8], [.2]])
        for name in ("original", SMOOTH):
            scores = old_rank.copy()
            if name == SMOOTH:
                scores[2] = .9
            if draw != "nominal" and name == SMOOTH:
                scores[2] = .6
            yield name, codes, scores, np.array([True, False, True, True, False]), np.array(
                [False, True, True, True, False])

    replay = SimpleNamespace(
        ids=range(5), width=1, cells=cells, model="nominal", draws=lambda: iter((0, 1)),
        samples=(0, 1), legacy=("original",), names=("original", SMOOTH), encode=int,
        saved_p22={"presets": {"balanced": {"joint": {"winners": [{"cycle": 3, "count": 2}]}}}},
    )
    old = {"rotation_count": 3, "cells_per_preset": 2}
    path = tmp_path / "legacy.csv"
    pd.DataFrame({"rotation_key": [1, 2, 3], "cells_per_preset": [2, 2, 2],
                  "balanced_top1_count": [0, 0, 2], "balanced_top3_count": [2, 2, 2]}).to_csv(path, index=False)
    expected = {"original": {"balanced": (3, 0)}, SMOOTH: {"balanced": (2, 1)}}
    weights = {"balanced": np.array([1])}
    replayed = count_frequencies(replay, weights, [1], expected, old, path)
    first, third = replayed["counts"]["balanced"]
    assert first == {3: 4}
    assert third == {1: 4, 2: 4, 3: 4}
    assert replayed["baseline_hits"]["balanced"] == [0, 4]
    assert replayed["flagged_baselines"] == 4
    assert threshold_keys(third, 4, 60) == {1, 2, 3}


def test_p44_reproduction_rejects_a_missing_count(tmp_path):
    path = tmp_path / "old.csv"
    pd.DataFrame({"rotation_key": [0], "cells_per_preset": [1],
                  "x_top1_count": [1], "x_top3_count": [1]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="top3 counts"):
        verify_legacy(path, {"rotation_count": 1, "cells_per_preset": 1}, np.array([True]),
                      {"x": {0: 1}}, {"x": {0: 0}})


def test_saved_expanded_counts_reconcile_with_denominators_and_earlier_results():
    import json

    from src.consensus_report_p44b import DOCUMENT, render
    from src.consensus_shortlist_p44b import OUTPUT, ROOT

    data = ROOT / "data/processed"
    report = json.loads((data / OUTPUT).read_text())
    assert (ROOT / "docs" / DOCUMENT).read_text() == render(report)
    assert [len(farm["variants"]) for farm in report["farms"].values()] == [17, 5, 5]
    assert len(report["p46_global_to_local"]) == 16
    prior = json.loads((data / "consensus_shortlist_p44.json").read_text())
    for farm_id, farm in report["farms"].items():
        assert farm["legacy_counts_reproduced"] and farm["saved_variant_winner_rates_reproduced"]
        assert {row[farm_id] for row in report["p46_global_to_local"]}.issubset(farm["variants"])
        assert farm["cells_per_preset"] == farm["draws"] * len(farm["variants"])
        cells = farm["cells_per_preset"]
        counts = pd.read_csv(data / farm["counts_file"])
        assert len(counts) == farm["rotation_count"] and counts["rotation_key"].is_unique
        assert (counts["cells_per_preset"] == cells).all()
        indexed = counts.set_index("rotation_key")
        for preset, item in farm["presets"].items():
            first, third = counts[f"{preset}_top1_count"], counts[f"{preset}_top3_count"]
            assert first.sum() == cells and (first <= third).all() and (third <= cells).all()
            assert 0 <= 3 * cells - third.sum() <= 2 * farm["cells_with_fewer_than_three"]
            for level, outcome in item["thresholds"].items():
                actual = set(counts.loc[third * 100 >= int(level) * cells, "rotation_key"])
                assert actual == {member["rotation_key"] for member in outcome["members"]}
                assert outcome["size"] == 0
                assert outcome["p44_size"] == prior["farms"][farm_id]["presets"][preset]["thresholds"][level]["size"]
            for row in (item["original_nominal"], item["fixed_baseline"], item["leaders"][0]):
                assert indexed.loc[row["rotation_key"], f"{preset}_top1_count"] == row["top1_count"]
                assert indexed.loc[row["rotation_key"], f"{preset}_top3_count"] == row["top3_count"]
                assert row["evidence"]["overall"] == "low"
    makueni = report["farms"]["kenya_makueni_north"]["presets"]["income"]["leaders"][0]
    assert makueni["top3_count"] == 1021


def test_full_seeded_replay_rebuilds_outputs_without_changing_prior_artifacts(tmp_path):
    import hashlib

    from src.consensus_shortlist_p44b import OUTPUT, ROOT, build

    data = ROOT / "data/processed"
    frozen = [path for path in [*data.glob("**/*"), *ROOT.glob("config/**/*"), ROOT / "data/crops.csv",
                               ROOT / "src/scoring.py", ROOT / "src/consensus_shortlist.py"]
              if path.is_file() and not path.name.startswith("consensus_shortlist_p44b")]

    def hashes():
        return {path: hashlib.sha256(path.read_bytes()).digest() for path in frozen}

    before = hashes()
    report = build(output_dir=tmp_path)
    assert hashes() == before
    for name in (OUTPUT, *(farm["counts_file"] for farm in report["farms"].values())):
        assert (tmp_path / name).read_bytes() == (data / name).read_bytes()
