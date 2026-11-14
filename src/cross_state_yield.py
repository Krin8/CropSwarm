"""Evaluate the frozen P25/P27 recipe across state borders."""

import json

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from src.climate_yield import (BASELINES, LEARNERS, MODELS, analyse, bootstrap_metrics, check_fold,
                               model_configurations)
from src.climate_yield_validity import DISTRICT_SCHEME, attach_districts
from src.county_yield_data import FEATURES
from src.data_pipeline import ROOT, atomic_write
from src.precompute_cache import write_json

STATE_NAMES = {"20": "Kansas", "31": "Nebraska", "40": "Oklahoma"}
KEY = ["fips", "year"]
DISTRICT_BLOCK = "district_block"


def indexed(frame):
    return frame.sort_values(KEY).reset_index(drop=True)


def outer_state_splits(frames):
    """The pooled check withholds one whole state at a time."""
    for held, target in frames.items():
        source = tuple(state for state in frames if state != held)
        yield source, held, pd.concat([frames[state] for state in source]), target


def predictions_for_transfer(train, target, config):
    if set(train.state) & set(target.state) or set(train.fips) & set(target.fips):
        raise ValueError("Transfer training and test geographies overlap")
    if train[DISTRICT_BLOCK].nunique() < config["inner_folds"]:
        raise ValueError("Too few training reporting districts for frozen inner CV")
    train, target = indexed(train), indexed(target)
    scores, selected, _ = check_fold(train, target, DISTRICT_BLOCK, config,
                                      np.random.default_rng(config["seed"]))
    columns = [*KEY, "state", DISTRICT_BLOCK, "practice", "yield_bu_ac"]
    return target[columns].assign(**scores), selected


def attach_reference(predictions, own_reference):
    """Compare against P27-style held-out target references on exactly the same rows."""
    expected = predictions.set_index(KEY).yield_bu_ac
    lookup = own_reference.set_index(KEY)
    if not lookup.index.is_unique or len(lookup) != len(expected) or set(lookup.index) != set(expected.index):
        raise ValueError("Own-state reference and transfer predictions cover different county-years")
    reference = lookup.reindex(expected.index)
    if not np.array_equal(reference.yield_bu_ac, expected.to_numpy()):
        raise ValueError("Own-state reference and transfer yields differ")
    return predictions.assign(**{f"own_{name}": reference[name].to_numpy() for name in BASELINES})


def evaluate_predictions(predictions, block, config):
    performance, source_deltas = bootstrap_metrics(predictions, block, config)
    # The same P27 paired bootstrap uses the alternate reference in its trend slot.
    own = {}
    for baseline in BASELINES:
        _, own[baseline] = bootstrap_metrics(
            predictions.assign(linear_trend=predictions[f"own_{baseline}"]), block, config)
    return {"n": len(predictions), "counties": int(predictions.fips.nunique()),
            "bootstrap_block": block, "bootstrap_blocks": int(predictions[block].nunique()),
            "performance": performance, "rmse_delta_vs_source_trend": source_deltas,
            "rmse_delta_vs_own_baselines": own,
            "own_baseline_rmse": {name: float(np.sqrt(np.mean(
                (predictions.yield_bu_ac - predictions[f"own_{name}"]) ** 2))) for name in BASELINES}}


def validate(frame, state):
    if (frame.empty or not frame.fips.str.fullmatch(rf"{state}[0-9]{{3}}").all()
            or frame.duplicated(KEY).any() or not np.isfinite(frame[["yield_bu_ac", *FEATURES]]).all().all()
            or frame.district.isna().any() or frame.district.eq("").any()
            or frame[["fips", "district"]].drop_duplicates().fips.duplicated().any()):
        raise ValueError(f"Expected one finite feature row per county-year with a fixed district for state {state}")
    return indexed(frame.assign(state=state, district_block=state + ":" + frame.district))


def evaluate(frames, kansas_reference, config):
    complete = {state: validate(frame, state) for state, frame in frames.items()}
    references, cases, predictions = {"20": kansas_reference}, {}, []
    counts = {"in_state": 0, "direct": 0, "pooled": 0}
    for target in ("31", "40"):
        frame = complete[target]
        if frame.district.nunique() <= config["inner_folds"]:
            raise ValueError(f"Too few reporting districts in {STATE_NAMES[target]} for in-state P27 split")
        results, held = analyse(frame, config, schemes=DISTRICT_SCHEME)
        state_result = next(iter(results.values()))
        references[target] = held
        tag = f"in_state_{target}"
        counts["in_state"] += state_result["outer_folds"]
        cases[tag] = {**state_result, "kind": "in_state", "train_states": [target], "test_state": target,
                      "counties": int(frame.fips.nunique())}
        predictions.append(held.assign(case=tag, state=target))

    pooled = []
    for source, target in (("20", "31"), ("20", "40"), ("31", "20"), ("40", "20")):
        tag = f"{source}_to_{target}"
        held, selected = predictions_for_transfer(complete[source], complete[target], config)
        held = attach_reference(held, references[target])
        cases[tag] = {**evaluate_predictions(held, DISTRICT_BLOCK, config), "kind": "direct",
                      "train_states": [source], "test_state": target, "selected": selected}
        counts["direct"] += 1
        predictions.append(held.assign(case=tag))

    for sources, target, train, test in outer_state_splits(complete):
        tag = f"pooled_holdout_{target}"
        held, selected = predictions_for_transfer(train, test, config)
        held = attach_reference(held, references[target])
        cases[tag] = {**evaluate_predictions(held, DISTRICT_BLOCK, config), "kind": "pooled_fold",
                      "train_states": list(sources), "test_state": target, "selected": selected}
        counts["pooled"] += 1
        pooled.append(held.assign(case=tag))
    predictions.extend(pooled)
    cases["pooled"] = {**evaluate_predictions(pd.concat(pooled, ignore_index=True), "state", config),
                       "kind": "pooled", "train_states": list(complete), "test_state": None}
    grid = model_configurations(config)
    outer = sum(counts.values())
    return {"label": "illustrative, validate locally",
            "status": "complete", "states": STATE_NAMES, "model_count": len(MODELS),
            "configurations": grid, "learned_configuration_count": sum(map(len, grid.values())),
            "outer_fits_by_experiment": counts, "inner_learned_fits": outer * config["inner_folds"] * sum(map(len, grid.values())),
            "outer_learned_refits": outer * len(LEARNERS), "cases": cases}, pd.concat(predictions, ignore_index=True)


def build(root=ROOT):
    processed = root / "data/processed"
    config = json.loads((root / "config/climate_yield.json").read_text())
    kansas = pd.read_csv(processed / "climate_yield_features.csv", dtype={"fips": str})
    mapping = pd.read_csv(root / "data/raw/p27/kansas_reporting_districts.csv", dtype=str)
    kansas = attach_districts(kansas, mapping)
    reference = pd.read_csv(processed / "climate_yield_validity_pooled_predictions.csv", dtype={"fips": str})
    reference = reference.loc[reference.scheme.isin(DISTRICT_SCHEME)]
    target_files = {state: processed / f"climate_yield_transfer_{state}_features.csv" for state in ("31", "40")}
    missing = [STATE_NAMES[state] for state, path in target_files.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Build verified target weather features first: {', '.join(missing)}")
    targets = {state: pd.read_csv(path, dtype={"fips": str, "district": str})
               for state, path in target_files.items()}
    frames = {"20": kansas, **targets}
    with threadpool_limits(limits=1):
        results, predictions = evaluate(frames, reference, config)
    results["cohorts"] = {
        key: {"county_years": len(frame), "counties": int(frame.fips.nunique()),
              "districts": int(frame.district.nunique()), "first_year": int(frame.year.min()),
              "last_year": int(frame.year.max()), "practice_counts": frame.practice.value_counts().to_dict()}
        for key, frame in frames.items()
    }
    atomic_write(processed / "climate_yield_transfer_predictions.csv", lambda path: predictions.to_csv(path, index=False))
    write_json(processed / "climate_yield_transfer.json", results)


if __name__ == "__main__":
    build()
