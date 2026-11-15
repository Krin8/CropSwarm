import json

import pytest

from src.crops import load_crops
from src.literature_check_p49 import (DOCUMENT, OUTPUT, REFERENCES, ROOT, build_report, finding,
                                      matched_n, overlap, render)


def test_quadratic_equivalence_uses_the_rising_branch():
    curve = {"intercept": 2159, "linear": 60.95, "quadratic": -0.4}
    assert matched_n(curve, 3053) == 16.4
    assert matched_n(curve, 2907) == 13.5
    assert matched_n(curve, 2159) == 0
    with pytest.raises(ValueError, match="does not cross"):
        matched_n(curve, 5000)


def test_only_bean_grain_equivalents_are_compared_as_credits():
    record = {"id": "sample", "measure": "bean_equivalence", "estimates": [
        {"label": "site A", "value": 12}, {"label": "site B", "value": 50}
    ]}
    assert finding(record, 22, [44, 80])["p45_overlap"] == [44, 50]
    assert finding(record, 22, [44, 80])["catalog_finding"] == "inside range"
    assert finding(record, 51, [44, 80])["catalog_finding"] == "outside range"
    assert overlap([0.7, 16.4], [44, 80]) is None
    for measure in ("residue", "uptake", "other_equivalence", "biomass_equivalence"):
        row = finding(record | {"measure": measure}, 22, [44, 80])
        assert "catalog_finding" not in row and "p45_overlap" not in row


def test_saved_results_and_document_rebuild_from_the_opened_source_records():
    references = json.loads((ROOT / REFERENCES).read_text())
    p45 = json.loads((ROOT / "data/p45_literature.json").read_text())
    report = build_report(references, load_crops(ROOT / "data/crops.csv"), p45)
    assert report == json.loads((ROOT / "data" / "processed" / OUTPUT).read_text())
    assert render(report) == (ROOT / "docs" / DOCUMENT).read_text()
    assert report["catalog"]["value"] == 22
    assert report["p45"]["bounds"] == [44, 80]
    assert report["machakos"]["bounds"] == [0.7, 56]
    assert report["machakos"]["p45_overlap"] == [44, 56]
    assert report["machakos"]["recomputed"] == [
        {"label": "Bean residue removed (RotNR)", "value": 16.4},
        {"label": "Bean residue returned (RotRR)", "value": 13.5},
    ]
    assert len(report["access_limits"]) == 3
    assert {row["source"] for row in report["rows"]} == set(report["sources"])
    for row in report["rows"]:
        assert all(row[field] for field in ("soil", "season", "residues", "unit", "method", "locator"))
