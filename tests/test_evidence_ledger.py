from dataclasses import replace
import json
from pathlib import Path

import pytest

from src.evidence_ledger import COLUMNS, build_document, build_ledger, check_rows, render_markdown

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed"


def load(name):
    return json.loads((DATA / name).read_text())


def test_committed_ledger_rebuilds_exactly_from_processed_results():
    assert build_document(ROOT) == (ROOT / "docs/evidence_ledger.md").read_text()
    rows = build_ledger(load)
    studies = ["P15", "P19", "P20", "P25", "P27", "P32", "P33", "P33b", "P37", "P37b", "P38"]
    if (DATA / "climate_yield_state_associations.json").exists():
        studies.append("P39")
    if (DATA / "scoring_response_check.json").exists():
        studies.append("P41")
    if (DATA / "smooth_climate_fit_p42.json").exists():
        studies.append("P42")
    if (DATA / "literature_variant_p43.json").exists():
        studies.append("P43")
    if (DATA / "consensus_shortlist_p44.json").exists():
        studies.append("P44")
    if (DATA / "literature_check_p45.json").exists():
        studies.append("P45")
    if (DATA / "regional_scoring_variants_p46.json").exists():
        studies.append("P46")
    if (DATA / "consensus_shortlist_p44b.json").exists():
        studies.append("P44b")
    if (DATA / "makueni_cropland_p48.json").exists():
        studies.append("P48")
    if (DATA / "rank_concentration_p47.json").exists():
        studies.append("P47")
    assert [row.study for row in rows] == studies
    assert all(len(row.cells()) == len(COLUMNS) for row in rows)
    assert {row.direction for row in rows} == {"supports", "mixed", "does not support"}


def test_rows_disclose_negative_results_and_limits():
    rows = {row.study: row for row in build_ledger(load)}
    assert "No Kansas correlation estimable" in rows["P15"].result
    assert "opposite-sign estimates" in rows["P19"].result
    assert "Makueni skipped" in rows["P20"].sample
    assert "No finite-width local setting reached nominal" in rows["P33b"].result
    assert "Freeze check unavailable" in rows["P33b"].result
    assert "None at 3 years" in rows["P37b"].result
    assert rows["P38"].direction == "does not support"
    if "P39" in rows:
        assert rows["P39"].direction == "mixed"
    if "P41" in rows:
        assert rows["P41"].direction == "mixed" and "11/12 linked pairs" in rows["P41"].result
    if "P43" in rows:
        assert rows["P43"].direction == "mixed" and "24/60" in rows["P43"].result
    if "P44" in rows:
        assert rows["P44"].direction == "does not support" and "0/12" in rows["P44"].result
    if "P47" in rows:
        assert "EXPLORATORY" in rows["P47"].question
        assert "shuffled 95% range" in rows["P47"].result
    if "P48" in rows:
        assert rows["P48"].direction == "mixed"
        assert "1/4" in rows["P48"].result and "2/4" in rows["P48"].result
    if "P45" in rows:
        assert rows["P45"].direction == "mixed"
        assert "Telangana 6, Makueni 6" in rows["P45"].sample
        assert "22 kg N/ha versus 44 to 80 kg N/ha" in rows["P45"].result


def test_source_change_changes_generated_sample_headline_and_direction():
    def fixture_load(name):
        report = load(name)
        if name == "climate_yield_model.json":
            report["dataset"]["retained_rows"] = 11
            report["schemes"]["leave_one_year_out"]["rmse_delta_vs_trend"]["ridge"] = {
                "value": 0.5, "bootstrap_95": [0.1, 0.8]}
        return report

    row = next(row for row in build_ledger(fixture_load) if row.study == "P25")
    assert "11 county-years" in row.sample
    assert "3/4" in row.result
    assert "+0.50 [+0.10, +0.80]" in row.result
    assert row.direction == "mixed"


def test_p39_is_optional_but_bad_inputs_still_fail():
    def before_p39(name):
        if name in {"climate_yield_state_associations.json", "scoring_response_check.json",
                    "literature_variant_p43.json", "consensus_shortlist_p44.json",
                    "literature_check_p45.json", "smooth_climate_fit_p42.json", "regional_scoring_variants_p46.json",
                    "consensus_shortlist_p44b.json", "makueni_cropland_p48.json", "rank_concentration_p47.json"}:
            raise FileNotFoundError(name)
        return load(name)

    assert build_ledger(before_p39)[-1].study == "P38"

    def bad_p39(name):
        return {} if name == "climate_yield_state_associations.json" else load(name)

    with pytest.raises(KeyError, match="held_out"):
        build_ledger(bad_p39)


@pytest.mark.parametrize("word", ["VALIDATED", "predicts", "Proven"])
@pytest.mark.parametrize("field", ["question", "sample", "result", "direction", "limit", "detail"])
def test_forbidden_wording_is_rejected_in_each_field(word, field):
    row = build_ledger(load)[0]
    row = replace(row, **{field: f"A result {word}."})
    with pytest.raises(ValueError):
        check_rows([row])
    with pytest.raises(ValueError):
        render_markdown([row])
