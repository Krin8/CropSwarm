import json

import pytest

from src.scoring import ROOT, preload
from src.uncertainty import simulate


def read(path):
    return json.loads((ROOT / path).read_text())


def test_seeded_draws_reproducible_and_supply_changes_shortfall():
    farm = read("config/farms.json")[1]
    identifier = farm["farm_id"]
    result = read(f"data/processed/strategies_{identifier}.json")
    assessment = read(f"data/processed/assessment_{identifier}.json")
    config = {**read("config/uncertainty.json"), "draws": 8}
    weights = read("config/weights_presets.json")["presets"]
    model = preload(farm)
    first = simulate(model, result, assessment, weights, config)
    assert first == simulate(model, result, assessment, weights, config)
    low = first["scenarios"]["less_irrigation"]["strategies"]["baseline"]["metrics"]["water"]
    high = first["scenarios"]["more_irrigation"]["strategies"]["baseline"]["metrics"]["water"]
    assert high["p50"] < low["p50"]


@pytest.mark.parametrize("farm", read("config/farms.json"))
def test_cached_ranges_and_win_accounting(farm):
    result = read(f"data/processed/uncertainty_{farm['farm_id']}.json")
    assert result["draws"] == 500
    for scenario in result["scenarios"].values():
        for name in read("config/weights_presets.json")["presets"]:
            assert sum(row["wins_pct"][name] for row in scenario["strategies"].values()) == pytest.approx(100, abs=.05)
        for row in scenario["strategies"].values():
            assert all(v["p10"] <= v["p50"] <= v["p90"] for v in row["metrics"].values())
