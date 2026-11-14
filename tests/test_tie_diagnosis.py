import json

import numpy as np

from src.scoring import METRICS, ROOT, preload
from src.tie_diagnosis import alternative_groups, analyse, detailed_top_two, explain_pair


def test_difference_threshold_uses_all_six_metrics_and_complete_link_groups():
    def strategy(name, values):
        return {"strategy_id": name, "metrics": {
            metric: {"score": value} for metric, value in zip(METRICS, values, strict=True)}}
    alternatives = [strategy("a", [0] * 6), strategy("b", [.04] + [0] * 5),
                    strategy("c", [.08] + [0] * 5), strategy("d", [0] * 5 + [.3])]
    result = alternative_groups(alternatives, .05)
    assert result["meaningfully_different_groups"] == 3
    assert result["groups"] == [["a", "b"], ["c"], ["d"]]
    assert next(p for p in result["pairs"] if p["first"] == "a" and p["second"] == "b")["near_duplicate"]


def test_exact_tie_metric_contributions_reconstruct_weighted_gap():
    farm = json.loads((ROOT / "config/farms.json").read_text())[0]
    preset = json.loads((ROOT / "config/weights_presets.json").read_text())["presets"]["water_saver"]
    weights = np.array([preset[metric] for metric in METRICS])
    pair = detailed_top_two(preload(farm), weights, 3)
    result = explain_pair(pair, weights, 1e-12)
    assert len(result["metric_differences"]) == 6
    assert np.isclose(sum(row["weighted_contribution"] for row in result["metric_differences"].values()),
                      result["gap"], atol=1e-12)
    assert result["top"]["id"] != result["second"]["id"]


def test_cached_analysis_reproduces_and_preserves_grid_and_margins():
    farm = json.loads((ROOT / "config/farms.json").read_text())[0]
    processed = ROOT / "data/processed"
    grid = json.loads((processed / "stress_test_us_high_plains_b.json").read_text())
    margins = json.loads((processed / "stress_margins_us_high_plains_b.json").read_text())
    strategies = json.loads((processed / "strategies_us_high_plains_b.json").read_text())
    presets = json.loads((ROOT / "config/weights_presets.json").read_text())["presets"]
    config = json.loads((ROOT / "config/tie_diagnosis.json").read_text())
    before = json.dumps((grid, margins), sort_keys=True)
    first = analyse(preload(farm), grid, margins, strategies, presets, config)
    second = analyse(preload(farm), grid, margins, strategies, presets, config)
    assert first == second
    assert json.dumps((grid, margins), sort_keys=True) == before
    assert first["alternatives"]["meaningfully_different_groups"] == 3


def test_saved_diagnoses_cover_each_near_tie_and_reconstruct_every_gap():
    for farm_id in ("us_high_plains_b", "telangana_a", "kenya_makueni_north"):
        processed = ROOT / "data/processed"
        grid = json.loads((processed / f"stress_test_{farm_id}.json").read_text())
        margins = json.loads((processed / f"stress_margins_{farm_id}.json").read_text())
        report = json.loads((processed / f"tie_diagnosis_{farm_id}.json").read_text())
        assert report["alternatives"]["meaningfully_different_groups"] == 3
        for preset, finding in report["presets"].items():
            entry = grid["presets"][preset]
            assert finding["changed_cells"] == sum(
                cell["winner_id"] != entry["reference_winner_id"] for cell in entry["cells"])
            if margins["presets"][preset]["near_tie"]:
                for side in ("before", "after"):
                    pair = finding[side]
                    assert pair["top"]["id"] != pair["second"]["id"]
                    assert np.isclose(sum(v["weighted_contribution"]
                                          for v in pair["metric_differences"].values()), pair["gap"], atol=1e-12)
                    assert np.isclose(pair["gap"], margins["presets"][preset][side]["gap"], atol=1e-12)
