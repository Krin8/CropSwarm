"""Run P27 district and practice checks without writing to the P25 artifacts."""
import argparse
import json

import pandas as pd
from threadpoolctl import threadpool_limits

from src.climate_yield import SCHEMES, analyse
from src.data_pipeline import ROOT, atomic_write
from src.precompute_cache import write_json

DISTRICT_SCHEME = {"leave_one_district_out": "district"}
COHORTS = ("pooled", "non_irrigated", "all_practices")


def attach_districts(frame, mapping):
    """Join a single fixed USDA district to each county, rejecting ambiguous or missing assignments."""
    district_columns = ["fips", "district", "district_name"]
    data = frame.merge(mapping[district_columns], on="fips", how="left", validate="many_to_one")
    if data[district_columns].isna().any().any():
        raise ValueError("Missing USDA district for a P25 county")
    if data[["district", "district_name"]].drop_duplicates()["district"].duplicated().any():
        raise ValueError("Conflicting USDA district names")
    return data


def evaluate_cohort(frame, cohort, config):
    subset = frame if cohort == "pooled" else frame.loc[frame.practice.eq(cohort)]
    schemes = DISTRICT_SCHEME if cohort == "pooled" else {**SCHEMES, **DISTRICT_SCHEME}
    if any(subset[column].nunique() <= config["inner_folds"] for column in schemes.values()):
        raise ValueError(f"Too few training groups for inner CV in {cohort}")
    with threadpool_limits(limits=1):
        results, predictions = analyse(subset, config, schemes=schemes)
    predictions["district"] = predictions.fips.map(subset.drop_duplicates("fips").set_index("fips").district)
    report = {"n": len(subset), "counties": int(subset.fips.nunique()),
              "first_year": int(subset.year.min()), "last_year": int(subset.year.max()),
              "years": int(subset.year.nunique()), "districts": int(subset.district.nunique()),
              "schemes": results}
    return report, predictions.assign(cohort=cohort)


def build(root=ROOT, *, cohort=None):
    processed = root / "data/processed"
    config = json.loads((root / "config/climate_yield.json").read_text())
    frame = pd.read_csv(processed / "climate_yield_features.csv", dtype={"fips": str})
    mapping = pd.read_csv(root / "data/raw/p27/kansas_reporting_districts.csv", dtype=str)
    data = attach_districts(frame, mapping)
    for name in COHORTS if cohort is None else (cohort,):
        report, predictions = evaluate_cohort(data, name, config)
        write_json(processed / f"climate_yield_validity_{name}.json", report)
        atomic_write(processed / f"climate_yield_validity_{name}_predictions.csv",
                     lambda path: predictions.to_csv(path, index=False))
        print(f"{name}: {report['n']} rows, {report['counties']} counties", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", choices=COHORTS, help="Rebuild one cohort")
    build(cohort=parser.parse_args().cohort)
