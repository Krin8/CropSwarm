"""P43 variant math, scope, deterministic replay and read-only invariants."""

import hashlib
import json

import numpy as np

from src.literature_variant import (Batch, KANSAS, METRICS, OUTPUT, Variant, build, corrected_water,
                                    design, transitions)
from src.scoring import ROOT, preload


def test_deep_reserve_loss_has_physical_bounds_and_preserves_shallow_bucket():
    deficit = np.array([0., 90., 145., 190., 300., 548.])
    corrected = corrected_water(deficit, 550, 0, 201, 70)
    np.testing.assert_array_equal(corrected, [0, 90, 159, 249, 370, 550])
    np.testing.assert_allclose(corrected_water(deficit, 550, .6, 201, 70), corrected * .4)
    np.testing.assert_array_equal(corrected_water(deficit, 550, 0, 201, 0), deficit)


def test_overlay_targets_only_documented_transitions_and_combines_on_a_copy():
    farms = json.loads((ROOT / "config/farms.json").read_text())
    farm, = (farm for farm in farms if farm["farm_id"] == KANSAS)
    model = preload(farm)
    variants, settings, _ = design(json.loads((ROOT / "data/p35_literature.json").read_text()))
    assert len({v.key for v in variants}) == 16
    wheat, soy, sorghum, fallow = [model.ids.index(i) for i in ("winter_wheat", "soybean", "sorghum", "fallow")]
    rotations = np.array([[soy, wheat, fallow], [wheat, sorghum, fallow],
                          [sorghum, wheat, fallow], [soy, sorghum, fallow]])
    batch = Batch(model, rotations, transitions(model, settings, [0, 43, 70, 97]))
    original = batch.evaluate(Variant(False, 0, False))[0].copy()
    revised = batch.evaluate(Variant(True, 70, True))[0]
    differences = revised - original
    assert differences[0, METRICS.index("water")] > 0
    assert not differences[1].any()
    assert differences[2, METRICS.index("risk")] < 0
    np.testing.assert_allclose(differences[:, METRICS.index("nitrogen")], [-34 / 3, 0, 0, (45 - 34) / 3])
    np.testing.assert_array_equal(batch.raw, original)


def test_frozen_input_and_output_hashes_and_reproducible_full_run(tmp_path):
    paths = [*ROOT.glob("data/processed/**/*"), *ROOT.glob("config/**/*"),
             *(ROOT / name for name in ("data/crops.csv", "data/p35_literature.json", "src/scoring.py",
                                        "src/sensitivity.py", "src/optimizer.py"))]
    paths = [path for path in paths if path.is_file() and path.name != OUTPUT]

    def hashes():
        return {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}

    before = hashes()
    generated = tmp_path / OUTPUT
    report = build(output=generated)
    assert before and hashes() == before
    saved = ROOT / "data/processed" / OUTPUT
    if saved.exists():
        assert generated.read_bytes() == saved.read_bytes()
    farms = report["farms"]
    assert set(farms) == {KANSAS, "telangana_a", "kenya_makueni_north"}
    for key, farm in farms.items():
        assert len(farm["nominal"]) == len(farm["p22"]) == 16
        assert all(len(case["presets"]) == 4 for case in farm["nominal"].values())
        if key != KANSAS:
            assert farm["benchmark_label"] == "no benchmark"
            assert all(case == farm["nominal"]["original"] for case in farm["nominal"].values())
            assert all(case == farm["p22"]["original"] for case in farm["p22"].values())
