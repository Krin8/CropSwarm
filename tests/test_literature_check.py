"""Regression checks for P35 table generation and isolated what-if changes."""

import json

import numpy as np
import pytest

from src.crops import load_crops
from src.literature_check import (FIELDS, INSIDE, OUTSIDE, UNAVAILABLE, ROOT, build_rows,
                                  compare_value, table_markdown)
from src.literature_what_if import revised_model, scores_for
from src.scoring import METRICS, preload, score_rotations


def test_inclusive_boundaries_and_missing_benchmark():
    assert compare_value(20, (20, 25)) == INSIDE
    assert compare_value(25, (20, 25)) == INSIDE
    assert compare_value(26, (20, 25)) == OUTSIDE
    assert compare_value(26, None) == UNAVAILABLE
    with pytest.raises(ValueError, match="ordered"):
        compare_value(15, (25, 20))


def test_every_crop_field_is_reported_and_references_resolve():
    rows, sources = build_rows()
    crops = load_crops(ROOT / "data/crops.csv")
    pairs = {(r["Check"], r["Crop or contrast"]) for r in rows}
    assert {(title, crop["display_name"]) for title, _ in FIELDS.values() for crop in crops.values()} <= pairs
    assert all(row["source"] in sources for row in rows if row["Finding"] != UNAVAILABLE)
    assert {INSIDE, OUTSIDE, UNAVAILABLE} == {row["Finding"] for row in rows}
    for check, crop, status in [
        ("Nitrogen credit", "Pigeonpea", OUTSIDE),
        ("Nitrogen credit", "Soybean", INSIDE),
        ("Nitrogen demand proxy", "Grain maize", UNAVAILABLE),
        ("Seasonal crop water demand", "Grain sorghum", INSIDE),
        ("Water demand, early grain sorghum", "Texas, 90–105 day group", OUTSIDE),
        ("Erosion protection index", "Cereal rye cover", UNAVAILABLE),
    ]:
        record, = [row for row in rows if (row["Check"], row["Crop or contrast"]) == (check, crop)]
        assert record["Finding"] == status
    document = table_markdown(rows, sources)
    assert "Chapter 3, Table 14" in document
    assert "254 to 381 mm" in document


def test_in_memory_credit_edits_leave_source_and_other_score_columns_untouched():
    farm = json.loads((ROOT / "config/farms.json").read_text())[0]
    model = preload(farm)
    wheat, soy = (model.ids.index(key) for key in ("winter_wheat", "soybean"))
    sequences = np.array([[wheat, soy, wheat], [wheat, wheat, wheat]])
    old_raw, old_scores, _ = score_rotations(model, sequences)
    alternative = revised_model(model, {"kind": "catalog", "crop": "soybean",
                                        "field": "n_credit_kg_ha", "value": 44})
    assert model.credits[soy] == 34 and alternative.credits[soy] == 44
    assert model.nitrogen_bounds[1] == 34 and alternative.nitrogen_bounds[1] == 44
    new_raw, new_scores = scores_for(model, sequences, {"kind": "transition_credit",
                                                        "crop": "soybean", "successors": ["winter_wheat"],
                                                        "value": 0})
    nitrogen = METRICS.index("nitrogen")
    np.testing.assert_allclose(new_raw[:, nitrogen] - old_raw[:, nitrogen], [-34/3, 0])
    np.testing.assert_array_equal(np.delete(new_scores, nitrogen, axis=1), np.delete(old_scores, nitrogen, axis=1))
