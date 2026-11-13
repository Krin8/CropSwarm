import json
from pathlib import Path

import pytest

from src.context import build_context, terrain_fields
from src.precompute_cache import RequestCache

ROOT = Path(__file__).resolve().parents[1]
FARMS = json.loads((ROOT / "config/farms.json").read_text())


def assert_fields(section):
    for item in section.values():
        if "value" not in item:
            assert_fields(item)
            continue
        assert {"value", "unit", "source", "resolution", "uncertainty_note", "evidence_refs"} <= item.keys()
        assert item["source"].startswith("https://") or item["source"] == "assumption, validate locally"
        assert all(item[key] for key in ("unit", "resolution", "uncertainty_note"))
        for ref in item["evidence_refs"]:
            if ref.startswith("data/"):
                path, key = ref.split("#")
                assert key in json.loads((ROOT / path).read_text())


@pytest.mark.parametrize("farm", FARMS, ids=[farm["farm_id"] for farm in FARMS])
def test_context_matches_offline_rebuild_with_sourced_fields(farm, monkeypatch):
    def network_forbidden(*args, **kwargs):
        pytest.fail("Context rebuild attempted a network request")

    cache = RequestCache(ROOT / "data/raw/p3", offline=True)
    monkeypatch.setattr(cache.session, "request", network_forbidden)
    path = ROOT / "data/processed" / f"context_{farm['farm_id']}.json"
    result = json.loads(path.read_text())
    assert build_context(cache, farm) == result
    assert_fields({name: result[name] for name in ("soil", "terrain", "groundwater")})
    assert result["soil"]["available_water_mm_0_30"]["value"] > 0
    assert set(farm["validation_flags"]) <= set(result["validation_flags"])
    assert "Groundwater trend and availability" in result["groundwater"]["regional_context"]["uncertainty_note"]


def test_missing_cross_is_not_flat_terrain():
    result = terrain_fields([{"elevation": 100}, {"elevation": None}])
    assert result["elevation_m"]["value"] == 100
    assert result["mean_slope_pct"]["value"] is None
    assert result["slope_class"]["value"] is None
