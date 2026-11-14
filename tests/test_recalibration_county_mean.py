import json

import numpy as np
import pandas as pd
import pytest

from src.data_pipeline import ROOT
from src.local_recalibration import METHODS, YEARS, curve_summary
from src.recalibration_county_mean import compare


def test_county_mean_comparison_pairs_same_bootstrap_draws_and_keeps_unavailable():
    rows = []
    for k in YEARS:
        for district, errors in enumerate(([1, 2], [4, 8])):
            for i, error in enumerate(errors):
                row = {"state": "31", "district": str(district), "k": k,
                       "fips": str(district * 2 + i), "year": 2005, "yield_bu_ac": float(20 + i)}
                for method in METHODS:
                    row[method] = np.nan if k == 0 and method != "source" else row["yield_bu_ac"] + error
                row["source"] = row["yield_bu_ac"] + error / 2
                if k:
                    row["source_adjusted"] = row["yield_bu_ac"] + error * 2
                rows.append(row)
    frame = pd.DataFrame(rows)
    config = {"seed": 42, "bootstrap_draws": 100, "bootstrap_quantiles": [0.025, 0.975]}
    result = compare(frame, config)["states"]["31"]
    assert result["0"]["source"] == {"difference": None, "status": "Unavailable"}
    assert result["3"]["source"]["status"] == "Beats county mean"
    assert result["3"]["source_adjusted"]["status"] == "Higher RMSE"
    assert result["3"]["local_ridge"]["status"] == "Interval includes zero"
    assert result["3"]["county_mean"]["status"] == "Reference"
    assert result["3"]["county_mean"]["difference"]["bootstrap_95"] == [0.0, 0.0]
    mismatched = frame.copy()
    mismatched.loc[mismatched.k.eq(3), "district"] = "different block"
    with pytest.raises(ValueError, match="common test rows differ"):
        compare(mismatched, config)
    draw = curve_summary(frame, config)["3"]["county_mean"]["rmse_bu_ac"]
    np.testing.assert_allclose(result["3"]["source"]["difference"]["bootstrap_95"],
                               [-v / 2 for v in reversed(draw["bootstrap_95"])])


def test_saved_county_mean_results_reproduce_and_keep_prior_trend_metrics():
    data = ROOT / "data/processed"
    predictions = pd.read_csv(data / "climate_yield_recalibration_predictions.csv",
                              dtype={"state": str, "district": str, "fips": str})
    config = json.loads((ROOT / "config/climate_yield.json").read_text())
    expected = json.loads((data / "climate_yield_recalibration_county_mean.json").read_text())
    actual = compare(predictions, config)
    assert actual == {key: value for key, value in expected.items() if key != "source"}

    prior = json.loads((data / "climate_yield_recalibration.json").read_text())
    for state, rows in predictions.groupby("state", sort=True):
        for k, methods in curve_summary(rows, config).items():
            for method, entry in methods.items():
                latest = entry.get("rmse_delta_vs_local_trend")
                original = prior["states"][state]["curves"][k][method].get("rmse_delta_vs_local_trend")
                assert (latest is None) == (original is None)
                if latest is not None:
                    np.testing.assert_allclose(latest["value"], original["value"], atol=1e-12)
                    np.testing.assert_allclose(latest["bootstrap_95"], original["bootstrap_95"], atol=1e-12)
