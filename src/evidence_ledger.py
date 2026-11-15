"""Summarize saved validation outputs without rerunning or changing any study."""

from dataclasses import dataclass
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FARMS = ("us_high_plains_b", "telangana_a", "kenya_makueni_north")
FARM_REGIONS = "Kansas, Telangana and Makueni"
DISTRICT = "leave_one_district_out"
COLUMNS = ("What was tested", "Farm or region and sample size", "Headline result and interval",
           "Direction", "What it does not show")
FORBIDDEN = re.compile(r"\b(?:validated|predicts|proven)\b", re.IGNORECASE)
DIRECTIONS = ("supports", "mixed", "does not support")
NOTE = ("Direction applies only to the question in each row. Mixed includes inconclusive findings. "
        "Brackets show saved descriptive 95% bootstrap intervals. "
        "Each sample size uses the unit shown. Several studies reuse observations. "
        "Rotation decisions still need field evidence.")


@dataclass(frozen=True)
class EvidenceRow:
    study: str
    question: str
    sample: str
    result: str
    direction: str
    limit: str
    detail: str

    def cells(self):
        return (f"{self.study} · {self.question}", self.sample, self.result, self.direction, self.limit)


def interval(value, bounds, spec):
    """Preserve signs when printing rounded saved estimates, without changing inference."""
    return f"{value:{spec}} [{bounds[0]:{spec}}, {bounds[1]:{spec}}]"


def rho(record):
    return f"ρ {interval(record['rho'], record['bootstrap_95'], '+.2f')}"


def delta(record, spec="+.2f"):
    return interval(record["value"], record["bootstrap_95"], spec)


def coverage(record):
    return interval(record["coverage"], record["coverage_95"], ".1%")


def excludes_zero(bounds):
    return bounds is not None and (bounds[0] > 0 or bounds[1] < 0)


def direction(supports, conflicts):
    if supports and not conflicts:
        return "supports"
    if conflicts and not supports:
        return "does not support"
    return "mixed"


def span(items):
    low, high = min(items), max(items)
    return str(low) if low == high else f"{low}–{high}"


def unique(rows, **fields):
    match, = (row for row in rows if all(row[key] == value for key, value in fields.items()))
    return match


def farm_checks(load):
    stress, nasa, yield_reports = ([load(f"{stem}_{farm}.json") for farm in FARMS]
                                  for stem in ("backtest", "nasa_consistency", "yield_backtest"))
    stress_stats = [stat for farm in stress for season in farm["seasons"].values()
                    for stat in season["comparisons"].values()]
    stress_clear = [stat for stat in stress_stats if excludes_zero(stat["bootstrap_95"])]
    stress_bad = sum(stat["rho"] > 0 for stat in stress_clear)
    stress_n = sum(stat["rho"] is not None for stat in stress_stats)
    short_rains = stress[2]["seasons"]["short_rains"]["comparisons"]["heat_days_vs_ndvi_amplitude"]
    long_rains = stress[2]["seasons"]["long_rains"]["comparisons"]["heat_days_vs_ndvi_peak"]
    kansas_missing = all(stat["rho"] is None for season in stress[0]["seasons"].values()
                         for stat in season["comparisons"].values())

    nasa_stats = [stat for farm in nasa for season in farm["seasons"].values()
                  for stat in season["comparisons"]]
    strong = sum(stat["finding"] == "strong expected association" for stat in nasa_stats)
    opposite = sum(stat["finding"] == "opposite sign" for stat in nasa_stats)
    rain = unique(nasa[2]["seasons"]["short_rains"]["comparisons"],
                  driver="rainfall anomaly", response="integrated NDVI")

    yield_stats = [stat for farm in yield_reports for series in farm["series"] for stat in series["comparisons"]]
    yield_clear = [stat for stat in yield_stats if excludes_zero(stat["bootstrap_95"])]
    yield_expected = sum(stat["rho"] < 0 for stat in yield_clear)
    wheat_series = unique(yield_reports[0]["series"], crop="winter_wheat", practice="Non-irrigated")
    wheat = unique(wheat_series["comparisons"], field="water_deficit_mm")
    kenya_skipped = not yield_reports[2]["series"]

    return [
        EvidenceRow("P15", "Does crop-window stress track lower MODIS greenness?",
                    f"{FARM_REGIONS} · {span([s['n'] for s in stress_stats])} paired years per comparison",
                    f"{stress_n}/{len(stress_stats)} estimates available; {len(stress_clear)} intervals exclude zero, "
                    f"{stress_bad} in the opposite direction. "
                    f"Makueni heat: long-rains peak {rho(long_rains)}; short-rains amplitude {rho(short_rains)}."
                    + (" No Kansas correlation estimable." if kansas_missing else ""),
                    direction(len(stress_clear) > stress_bad, stress_bad or len(stress_clear) < len(stress_stats)),
                    "Mixed MODIS pixels and assumed crop identities leave field yield and management unresolved.",
                    "backtest.md#results"),
        EvidenceRow("P19", "Do NASA weather and MODIS greenness move together in expected directions?",
                    f"{FARM_REGIONS} · {span([s['n'] for s in nasa_stats])} paired seasons per comparison",
                    f"{strong}/{len(nasa_stats)} strong expected associations; {opposite} opposite-sign estimates. "
                    f"Makueni short-rains rainfall anomaly vs integrated NDVI {rho(rain)} (n={rain['n']}).",
                    direction(strong, opposite or strong < len(nasa_stats)),
                    "NASA input consistency leaves crop-specific stress, yield and rotation performance unresolved.",
                    "backtest.md#p19-long-record-nasa-consistency-check"),
        EvidenceRow("P20", "Does modeled water or heat stress track lower regional yield anomalies?",
                    f"Finney County and historical Warangal · {span([s['n'] for s in yield_stats])} paired years per series"
                    + ("; Makueni skipped" if kenya_skipped else ""),
                    f"{len(yield_clear)}/{len(yield_stats)} intervals exclude zero. Finney non-irrigated wheat deficit "
                    f"{rho(wheat)} (n={wheat['n']})."
                    + (" Makueni lacked a comparable seasonal series." if kenya_skipped else ""),
                    direction(yield_expected, yield_expected < len(yield_stats)),
                    "Regional yield and point weather leave individual field yield and irrigation effects unresolved.",
                    "backtest.md#p20-yield-back-test"),
    ]


def kansas_checks(load):
    p25 = load("climate_yield_model.json")
    p27 = {key: load(f"climate_yield_validity_{key}.json")
           for key in ("pooled", "non_irrigated", "all_practices")}
    year = p25["schemes"]["leave_one_year_out"]["rmse_delta_vs_trend"]
    county = p25["schemes"]["leave_one_county_out"]["rmse_delta_vs_trend"]
    p25_deltas = [*year.values(), *county.values()]
    p25_wins = sum(row["bootstrap_95"][1] < 0 for row in p25_deltas)
    district_results = [cohort["schemes"][DISTRICT] for cohort in p27.values()]
    overall = district_results[0]
    p27_deltas = [entry for result in district_results for entry in result["rmse_delta_vs_trend"].values()]
    p27_wins = sum(row["bootstrap_95"][1] < 0 for row in p27_deltas)
    return [
        EvidenceRow("P25", "Do weather models beat the trend on held-out years and counties?",
                    f"Kansas · {p25['dataset']['retained_rows']:,} county-years, "
                    f"{p25['dataset']['retained_counties']} counties",
                    f"{p25_wins}/{len(p25_deltas)} paired differences favor the learned model. "
                    f"ΔRMSE (bu/acre): year ridge {delta(year['ridge'])}; county forest {delta(county['random_forest'])}.",
                    direction(p25_wins, p25_wins < len(p25_deltas)),
                    "County and year holdouts leave wider spatial transfer and field outcomes untested.",
                    "ml_model.md#p25-learned-climate-yield-check"),
        EvidenceRow("P27", "Does the Kansas result hold when whole USDA districts are withheld?",
                    f"Kansas · {overall['n']:,} county-years, {overall['outer_folds']} districts; "
                    f"{p27['non_irrigated']['n']:,} reported non-irrigated and {p27['all_practices']['n']:,} fallback",
                    f"{p27_wins}/{len(p27_deltas)} district differences vs trend favor the learned model across cohorts. "
                    f"Pooled ΔRMSE (bu/acre): ridge {delta(overall['rmse_delta_vs_trend']['ridge'])}; "
                    f"forest {delta(overall['rmse_delta_vs_trend']['random_forest'])}.",
                    direction(p27_wins, p27_wins < len(p27_deltas)),
                    "Reporting subsets differ in years and management. Their differences leave irrigation effects unresolved.",
                    "ml_model.md#p27-validity-checks"),
    ]


def transfer_check(load):
    report = load("climate_yield_transfer.json")
    cases = report["cases"]
    ok_ridge = cases["20_to_40"]["rmse_delta_vs_own_baselines"]["linear_trend"]["ridge"]
    ne_forest = cases["20_to_31"]["rmse_delta_vs_own_baselines"]["county_mean"]["random_forest"]
    pooled_forest = cases["pooled"]["rmse_delta_vs_own_baselines"]["linear_trend"]["random_forest"]
    deltas = [entry for case in cases.values() if case["kind"] in {"direct", "pooled"}
              for results in case["rmse_delta_vs_own_baselines"].values() for entry in results.values()]

    return EvidenceRow("P32", "Do cross-state winter-wheat models beat target-state baselines?",
                       f"KS, NE, OK · {cases['pooled']['n']:,} pooled county-years; "
                       f"KS→NE {cases['20_to_31']['n']:,}, KS→OK {cases['20_to_40']['n']:,}",
                       f"ΔRMSE (bu/acre): KS→NE forest vs mean {delta(ne_forest)}; KS→OK ridge vs trend "
                       f"{delta(ok_ridge)}; pooled state holdout forest vs trend {delta(pooled_forest)}.",
                       direction(any(d["bootstrap_95"][1] < 0 for d in deltas),
                                 any(d["bootstrap_95"][1] >= 0 for d in deltas)),
                       "The transfer comparisons leave the cause of geographic differences unresolved.",
                       "ml_model.md#p32-cross-state-winter-wheat-transfer")


def interval_checks(load):
    p33 = load("climate_yield_intervals.json")
    p33b = load("climate_yield_interval_diagnosis.json")
    ks_district = unique(p33["kansas"]["district"]["pooled"], model="random_forest", level=90)
    ks_year = unique(p33["kansas"]["year"]["pooled"], model="random_forest", level=90)
    k = str(max(p33["k"]))
    ok_local = unique(p33["transfer"]["40"]["local"][k]["pooled"], model="ridge", level=90)
    inflated = unique(p33b["kansas"]["year"]["pooled"], model="ridge", method="inflated", level=90)
    year_2007 = [row for row in p33b["kansas"]["year"]["folds"]["2007"] if row["level"] == 90]
    best_2007 = max(year_2007, key=lambda row: row["coverage"])
    unbounded = sum(row["unbounded"] for row in p33b["interval_status_by_method"].values())
    frost = p33b["frost_2007"]
    local = [row for state in p33b["transfer"].values()
             for fit in state["p37"].values() for row in fit["results"]]
    finite_local_success = any(not row["unbounded"] and not row["below_nominal"]
                               for row in local)
    return [
        EvidenceRow("P33", "Do calibrated county-yield intervals meet nominal coverage on holdout and transfer?",
                    f"KS, NE, OK · {p33['interval_evaluations']:,} interval evaluations; "
                    f"KS {ks_district['n']:,} county-years per split",
                    f"Nominal {ks_district['level']}%: KS forest district {coverage(ks_district)}, "
                    f"year {coverage(ks_year)}; OK ridge with {k} local years {coverage(ok_local)}.",
                    direction(not ks_district["undercoverage"], ks_year["undercoverage"] or ok_local["undercoverage"]),
                    "Historical coverage leaves future coverage and coverage under geographic shift uncertain.",
                    "ml_model.md#p33-calibrated-yield-intervals"),
        EvidenceRow("P33b", "Do alternative interval methods remove undercoverage across settings?",
                    f"KS, NE, OK · {p33b['interval_count']:,} evaluations; "
                    f"2007 KS {best_2007['n']} county-years",
                    f"Nominal {inflated['level']}%: inflated ridge, KS year holdout {coverage(inflated)}; "
                    f"highest 2007 coverage {coverage(best_2007)}. {unbounded:,} unbounded intervals."
                    + (" No finite-width local setting reached nominal." if not finite_local_success else "")
                    + (" Freeze check unavailable." if frost["status"] == "unavailable" else ""),
                    ("does not support" if best_2007["coverage"] < best_2007["level"] / 100
                     and not finite_local_success else "mixed"),
                    "Residual and coverage differences leave the 2007 freeze hypothesis and shifted coverage unresolved.",
                    "ml_model.md#p33b-interval-undercoverage-diagnosis"),
    ]


def recalibration_checks(load):
    study = load("climate_yield_recalibration.json")
    comparison = load("climate_yield_recalibration_county_mean.json")
    states = study["states"]
    sample = " · ".join(f"{v['name']} {v['test_rows']:,} county-years" for v in states.values())
    adjust = "source_adjusted"
    first = {key: state["smallest_k_beating_trend"][adjust] for key, state in states.items()}
    trend_results = []
    for key, state in states.items():
        k = first[key]
        entry = state["curves"][str(k)][adjust]["rmse_delta_vs_local_trend"] if k is not None else None
        trend_results.append(f"{state['name']} {k} years {delta(entry)}" if entry else
                             f"{state['name']} had no qualifying improvement")
    wins = {key: [(int(k), method, row["difference"]) for k, curve in curves.items()
                  for method, row in curve.items() if row["status"] == "Beats county mean"]
            for key, curves in comparison["states"].items()}
    ridge_first = {key: min((row for row in entries if row[1] == "local_ridge"), default=None)
                   for key, entries in wins.items()}
    ridge_results = [f"{states[key]['name']} {row[0]} years {delta(row[2], '+.3f')}" if row else
                     f"{states[key]['name']} had no qualifying ridge improvement"
                     for key, row in ridge_first.items()]
    no_three_year_wins = all(k != 3 for entries in wins.values() for k, _, _ in entries)
    source_feature_wins = [(key, k) for key, entries in wins.items()
                           for k, method, _ in entries if method == "source_feature"]
    source_feature_text = ", ".join(f"{states[key]['name']} at {k} years" for key, k in source_feature_wins)
    local_wins = sum(map(len, wins.values()))
    return [
        EvidenceRow("P37", "Can local intercept and trend adjustment beat the local trend alone?",
                    sample,
                    "First clear ΔRMSE (bu/acre), source adjustment vs trend: " + "; ".join(trend_results) + ".",
                    direction(any(k is not None for k in first.values()), any(k is None for k in first.values())),
                    "The short trend is a weak baseline. Gains over a county mean and on farms require separate evidence.",
                    "ml_model.md#p37-local-yield-recalibration"),
        EvidenceRow("P37b", "Do local methods also beat the county mean?",
                    sample,
                    "First clear local ridge ΔRMSE (bu/acre): " + "; ".join(ridge_results) + "."
                    + (f" Source-feature ridge: {source_feature_text}." if source_feature_text else "")
                    + (f" {local_wins} qualifying improvements. None at 3 years." if no_three_year_wins
                       else f" {local_wins} qualifying improvements."),
                    direction(any(wins.values()), no_three_year_wins),
                    "District yield history is required. These results leave gains for individual farms unresolved.",
                    "ml_model.md#p37b-county-mean-comparison"),
    ]


def overlap_check(load):
    report = load("climate_yield_transfer_diagnosis.json")
    full, inside = (report["performance"][key] for key in ("full", "inside"))
    ridge = inside["paired_rmse_delta"]["ridge"]["own_linear_trend"]
    forest = inside["paired_rmse_delta"]["random_forest"]["own_linear_trend"]
    differences = [row for model in inside["paired_rmse_delta"].values() for row in model.values()]
    return EvidenceRow("P38", "Does restricting to overlapping weather remove the Oklahoma transfer gap?",
                       f"KS→OK · {inside['n']:,}/{full['n']:,} Oklahoma county-years inside all bands",
                       f"Inside overlap, ΔRMSE vs OK trend (bu/acre): ridge {delta(ridge)}; forest {delta(forest)}. "
                       + ("Both also trailed the OK mean." if all(d["bootstrap_95"][0] > 0 for d in differences)
                          else "See the full report for both baseline comparisons."),
                       direction(any(d["bootstrap_95"][1] < 0 for d in differences),
                                 all(d["bootstrap_95"][0] > 0 for d in differences)),
                       "Marginal overlap leaves the cause of the remaining gap unresolved.",
                       "ml_model.md#p38-kansas-to-oklahoma-transfer-diagnosis")


def state_check(report):
    pooled = report["held_out"]["pooled"]
    ok = report["held_out"]["by_state"]["40"]
    pairs = [pair for row in report["coefficients"].values() for pair in row["pairs"]]
    contrasts = sum(pair["difference_excludes_zero"] for pair in pairs)
    return EvidenceRow("P39", "Do state slopes differ, and do those interactions improve district holdout?",
                       f"KS, NE, OK · {pooled['n']:,} county-years, {pooled['districts']} districts",
                       f"{contrasts}/{len(pairs)} slope contrasts exclude zero (unadjusted). "
                       f"Interaction ΔRMSE (bu/acre): pooled {delta(pooled['rmse_difference_bu_ac'], '+.4f')}, "
                       f"OK {delta(ok['rmse_difference_bu_ac'], '+.3f')}.",
                       direction(contrasts or ok["clear_improvement"], not pooled["clear_improvement"]),
                       "County-average associations leave crop physiology, management and irrigation effects unresolved.",
                       "ml_model.md#p39-weatheryield-associations-by-state")


def scoring_response_check(report):
    summary = report["summary"]
    states = report["states"]
    total = sum(row["county_years"] for row in states.values())
    districts = sum(row["districts"] for row in states.values())
    heat = states["40"]["weather"]["heat_days"]["learners"]["random_forest"]["comparisons"]["climate_fit"]
    return EvidenceRow("P41", "Do wheat score responses agree with county-yield associations?",
                       f"KS, NE, OK · {total:,} county-years, {districts} held-out districts",
                       f"{summary['with_same_direction']}/{summary['linked_comparisons']} linked pairs move together "
                       f"somewhere in range; {summary['with_opposite_direction']} reverse somewhere. "
                       f"OK heat, forest vs climate-fit ρ {delta(heat['rho_supported'], '+.3f')}.",
                       summary["direction"],
                       "County associations leave field response and rotation quality unresolved.",
                       "ml_model.md#p41-scoring-versus-county-yield-response")


def smooth_climate_check(report):
    farms = list(report["farms"].values())
    comparisons = [row for farm in farms for row in farm["nominal"].values()]
    changed = sum(row["label_changed"] for row in comparisons)
    shortlist_changed = sum(farm["published_shortlist"]["above_cutoff"] for farm in farms)
    shortlist_total = sum(farm["published_shortlist"]["total"] for farm in farms)
    correlations = [row["rank_spearman"] for row in comparisons if row["rank_spearman"] is not None]
    rank = (f"Rank ρ {min(correlations):.4f}–{max(correlations):.4f}."
            if correlations else "Rank correlations unavailable.")
    tolerates_smoothing = changed == 0 and shortlist_changed == 0
    changes_throughout = changed == len(comparisons) and shortlist_changed == shortlist_total
    design = report["design"]
    return EvidenceRow("P42", "Do rotation ranks agree after smoothing the heat screen?",
                       f"{len(comparisons)} farm–preset cases · {design['draws']} matched draws per farm",
                       f"{changed}/{len(comparisons)} nominal leaders changed. "
                       f"{shortlist_changed}/{shortlist_total} published options moved more than "
                       f"{design['shortlist_cutoff']:g} climate-fit points. {rank}",
                       direction(tolerates_smoothing, changes_throughout),
                       "Changing the heat screen measures model sensitivity. Field response remains untested.",
                       "smooth_climate_fit.md")


def literature_variant_check(report):
    farm, = (data for data in report["farms"].values() if data["benchmark"])
    comparisons = [row for key, result in farm["nominal"].items() if key != "original"
                   for row in result["presets"].values()]
    changed = sum(not row["original_still_optimal"] for row in comparisons)
    near = sum(row["near_tie_disappeared"] for row in comparisons)
    ranks = [row["rank_spearman"] for row in comparisons]
    return EvidenceRow("P43", "Do Kansas winners survive literature-based scoring changes?",
                       f"Kansas · {len(comparisons)} variant–preset comparisons, {report['design']['draws']} paired draws",
                       f"The original winner lost optimality in {changed}/{len(comparisons)} comparisons. "
                       f"Ranking ρ {min(ranks):.5f}–{max(ranks):.5f}. {near} top-two near-ties disappeared.",
                       direction(changed < len(comparisons), changed > 0),
                       "The Kansas what-if leaves field effects and applicability to other farms unresolved.",
                       "literature_variant.md")


def consensus_shortlist_check(report):
    cutoff = report["design"]["primary_threshold"]
    farms = report["farms"].values()
    results = [preset["thresholds"][str(cutoff)] for farm in farms for preset in farm["presets"].values()]
    nonempty = sum(row["size"] > 0 for row in results)
    overlap = sum(row["shortlist_overlap"] > 0 for row in results)
    decisions = f"{nonempty}/{len(results)} farm–preset sets are nonempty at {cutoff}%; {overlap} overlap the published shortlist."
    cells = sorted({farm["cells_per_preset"] for farm in farms})
    return EvidenceRow("P44", "Do rotations repeatedly place in the top three across assumption draws?",
                       f"Kansas, Telangana, Makueni · {cells[0]:,}–{cells[-1]:,} cells per preset",
                       decisions, direction(nonempty, nonempty < len(results)),
                       "Agreement within the tested configurations leaves field quality unresolved.",
                       "consensus_shortlist.md")


def regional_literature_check(report):
    from src.literature_check_p45 import metric_counts

    regions = report["regions"]
    regional_counts = {region["name"]: metric_counts(region) for region in regions.values()}
    totals = {name: sum(row["Usable"] for row in counts) for name, counts in regional_counts.items()}
    inside = sum(row["Inside range"] for counts in regional_counts.values() for row in counts)
    outside = sum(totals.values()) - inside
    sample = ", ".join(f"{name} {count}" for name, count in totals.items())
    bean, = (row for row in regions["kenya_makueni_north"]["rows"]
             if row["check"] == "Common bean before sole maize · N credit")
    return EvidenceRow("P45", "How do crop inputs compare with regional literature?",
                       f"{sample} usable comparisons · {len(report['sources'])} sources read",
                       f"{inside} inside the published bounds, {outside} outside. "
                       f"Katumani bean-to-maize N: {bean['model']} versus {bean['reference']}.",
                       direction(inside, outside),
                       "Published treatment spans do not establish local crop response or rotation quality.",
                       "literature_check_p45.md")


def regional_scoring_check(report):
    farms = report["farms"]
    cases = [row for farm in farms.values() for level, result in farm["levels"].items()
             if level != "original" for row in result["nominal"].values()]
    changed = sum(row["label_changed"] for row in cases)
    created = sum(row["near_tie_appeared"] for row in cases)
    resolved = sum(row["near_tie_disappeared"] for row in cases)
    return EvidenceRow("P46", "Do nominal leaders hold under regional water and nitrogen inputs?",
                       f"Telangana and Makueni · {len(cases)} active level–preset comparisons · "
                       f"{report['design']['joint_draws']} paired draws per farm",
                       f"{changed}/{len(cases)} leaders changed. Top-two near-ties created {created}, resolved {resolved}.",
                       direction(changed < len(cases), changed > 0),
                       "Trial estimates leave field response and rotation suitability unresolved. Makueni cropland is unverified.",
                       "regional_scoring_variants.md")


def expanded_consensus_check(report):
    farms = list(report["farms"].values())
    cutoff = report["design"]["primary_threshold"]
    presets = [preset for farm in farms for preset in farm["presets"].values()]
    counts = {str(level): sum(row["thresholds"][str(level)]["size"] > 0 for row in presets)
              for level in report["design"]["thresholds"]}
    counts_text = ", ".join(f"{count}/{len(presets)} at {level}%" for level, count in counts.items())
    sizes = ", ".join(str(len(farm["variants"])) for farm in farms)
    return EvidenceRow("P44b", "Do rotations repeatedly place in the top three across the expanded variants?",
                       f"Kansas, Telangana, Makueni · {sizes} variants respectively · {farms[0]['draws']} draws each",
                       f"Nonempty farm–preset sets {counts_text}.",
                       direction(counts[str(cutoff)] > 0, counts[str(cutoff)] < len(presets)),
                       "Agreement within the evaluated settings leaves field performance and rotation quality unresolved.",
                       "consensus_shortlist_p44b.md")


def rank_concentration_check(report):
    farms = list(report["farms"].values())
    cutoffs = [f"{q:g}" for q in report["design"]["q_pct"]]
    cases = [outcomes for farm in farms for outcomes in farm["presets"].values()]
    sizes = {q: sum(case[q]["size"] > 0 for case in cases) for q in cutoffs}
    nonempty = ", ".join(f"{sizes[q]}/{len(cases)} at {q}%" for q in cutoffs)
    largest, reference = max(
        ((case[q], farm["null"][q]) for farm in farms for case in farm["presets"].values() for q in cutoffs),
        key=lambda pair: pair[0]["largest_share"],
    )
    low, high = reference["max_share_95_range"]
    return EvidenceRow(
        "P47", "EXPLORATORY · Do rotations repeatedly place in wider rank bands across P44 settings?",
        f"{FARM_REGIONS} · " +
        ", ".join(f"{farm['cells_per_preset']:,}" for farm in farms) + " cells per preset, respectively",
        f"Nonempty sets {nonempty}. Highest share {largest['largest_share']:.2%}, with shuffled 95% range "
        f"{low:.2%} to {high:.2%} and p {largest['max_share_p']:.4f}.",
        direction(any(sizes.values()), any(n < len(cases) for n in sizes.values())),
        "Repeated ranks within the model leave field performance and rotation quality unresolved.",
        "rank_concentration.md",
    )


def makueni_cropland_check(report):
    products = sum("class_code" in row for row in report["products"].values())
    original, alternate = report["original"], report["alternate"]
    result = f"Original point: {original['crop_votes']}/{products} products mapped cropland."
    if alternate:
        result += (f" Parallel point {alternate['distance_m']:.1f} m away: "
                   f"{len(alternate['supporting_products'])}/{products}.")
    else:
        result += " No same-cell candidate met the map agreement rule."
    return EvidenceRow("P48", "Do independent maps classify the Makueni points as cropland?",
                       f"Makueni · {products} classifying maps · {report['design']['radius_m'] / 1000:g} km disk",
                       result, direction(original["meets_rule"] or bool(alternate), not original["meets_rule"]),
                       "Map labels leave current field use, crop identity and the rotation unresolved.",
                       "makueni_cropland.md")


def check_rows(rows):
    ids = [row.study for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate evidence study")
    for row in rows:
        if row.direction not in DIRECTIONS:
            raise ValueError(f"{row.study} has an unknown direction")
        for cell in (*row.cells(), row.detail):
            if not cell.strip() or FORBIDDEN.search(cell):
                raise ValueError(f"{row.study} contains an empty cell or forbidden wording")


def build_ledger(load):
    rows = [*farm_checks(load), *kansas_checks(load), transfer_check(load), *interval_checks(load),
            *recalibration_checks(load), overlap_check(load)]
    for filename, describe in (("climate_yield_state_associations.json", state_check),
                               ("scoring_response_check.json", scoring_response_check),
                               ("smooth_climate_fit_p42.json", smooth_climate_check),
                               ("literature_variant_p43.json", literature_variant_check),
                               ("consensus_shortlist_p44.json", consensus_shortlist_check),
                               ("literature_check_p45.json", regional_literature_check),
                               ("regional_scoring_variants_p46.json", regional_scoring_check),
                               ("consensus_shortlist_p44b.json", expanded_consensus_check),
                               ("makueni_cropland_p48.json", makueni_cropland_check),
                               ("rank_concentration_p47.json", rank_concentration_check)):
        try:
            report = load(filename)
        except FileNotFoundError:
            continue
        rows.append(describe(report))
    check_rows(rows)
    return rows


def render_markdown(rows):
    check_rows(rows)

    def line(cells):
        return "| " + " | ".join(cell.replace("|", r"\|") for cell in cells) + " |"

    return "\n".join([
        "# Evidence ledger", "", NOTE, "",
        line(COLUMNS), line(["---"] * len(COLUMNS)),
        *(line((f"[{row.cells()[0]}]({row.detail})", *row.cells()[1:])) for row in rows),
        "", "Regenerate offline with `python -m src.evidence_ledger`.", "",
    ])


def build_document(root=ROOT):
    def load(name):
        return json.loads((root / "data/processed" / name).read_text())

    return render_markdown(build_ledger(load))


if __name__ == "__main__":
    (ROOT / "docs/evidence_ledger.md").write_text(build_document())
