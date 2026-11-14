"""Compare saved P37 predictions against the local county mean without fitting models."""

import json

import pandas as pd

from src.data_pipeline import ROOT
from src.local_recalibration import METHODS, YEARS, curve_summary
from src.precompute_cache import write_json

BASELINE = "county_mean"
DELTA = f"rmse_delta_vs_{BASELINE}"


def compare(predictions, config):
    states = {}
    for state, rows in predictions.groupby("state", sort=True):
        curves = curve_summary(rows, config, baseline_method=BASELINE)
        comparisons = {}
        for k, methods in curves.items():
            comparisons[k] = {}
            for method, result in methods.items():
                delta = result.get(DELTA)
                if delta is None:
                    status = "Unavailable"
                elif method == BASELINE:
                    status = "Reference"
                elif delta["bootstrap_95"][1] < 0:
                    status = "Beats county mean"
                elif delta["bootstrap_95"][0] > 0:
                    status = "Higher RMSE"
                else:
                    status = "Interval includes zero"
                comparisons[k][method] = {"difference": delta, "status": status}
        states[state] = comparisons
    return {"label": "illustrative, validate locally", "baseline": BASELINE,
            "local_years": list(YEARS), "methods": list(METHODS),
            "bootstrap_draws": config["bootstrap_draws"], "seed": config["seed"], "states": states}


def build(root=ROOT):
    output = root / "data/processed"
    source = "climate_yield_recalibration_predictions.csv"
    predictions = pd.read_csv(output / source, dtype={"state": str, "district": str, "fips": str})
    config = json.loads((root / "config/climate_yield.json").read_text())
    report = compare(predictions, config)
    write_json(output / "climate_yield_recalibration_county_mean.json", {**report, "source": source})


if __name__ == "__main__":
    build()
