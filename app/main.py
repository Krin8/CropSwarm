"""Offline CropSwarm decision support."""

import copy
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.decision_brief import BRIEFS, brief_filename, brief_release, reference_inputs, render_brief, repository_version
from src.optimizer import allowed_layers, count_rotations, enumerate_canonical_rotations, strategy
from src.scoring import METRICS, baseline_indices, preload, score_rotations
from src.sensitivity import check_first
from src.tie_diagnosis import alternative_groups
from src.uncertainty import simulate

DATA = ROOT / "data/processed"
COLORS = ["#697473", "#32774F", "#956027", "#316F8A", "#765A91"]


@st.cache_data
def cached(name):
    return json.loads((DATA / name).read_text())


def load(farm_id, prefix):
    return cached(f"{prefix}_{farm_id}.json")


def title(name):
    return name.replace("_", " ").capitalize()


def brief_controls(farm, preset):
    stem = brief_filename(farm["farm_id"], preset)
    html = render_brief(farm, preset, *reference_inputs(load, farm["farm_id"]),
                        generated_on=date.today(), commit=repository_version())
    release = brief_release()
    pdf = BRIEFS / f"{stem}.pdf"
    with st.container(key="decision_brief"):
        st.caption(f"Farm decision brief · {farm['name']} · {title(preset)} preset. "
                   "Uses the saved farm inputs and named preset weights.")
        columns = st.columns(2)
        columns[0].download_button("Download brief (HTML)", html, f"{stem}.html", mime="text/html", on_click="ignore")
        if release.get("pdf_paper") and pdf.is_file():
            columns[1].download_button("Download brief (PDF)", pdf.read_bytes(), pdf.name,
                                       mime="application/pdf", on_click="ignore",
                                       help=f"Bundled {release['pdf_paper']} copy generated {release['generated_on']} "
                                            f"from {release['source_commit'][:12]}.")


def correlation_counts(farm_ids):
    studies = {"P15 crop stress and NDVI": [], "P19 NASA weather and NDVI": [],
               "P20 regional yield": []}
    for farm_id in farm_ids:
        for season in load(farm_id, "backtest")["seasons"].values():
            studies["P15 crop stress and NDVI"].extend(season["comparisons"].values())
        for season in load(farm_id, "nasa_consistency")["seasons"].values():
            studies["P19 NASA weather and NDVI"].extend(season["comparisons"])
        for series in load(farm_id, "yield_backtest")["series"]:
            studies["P20 regional yield"].extend(series["comparisons"])
    counts = []
    for study, comparisons in studies.items():
        intervals = [row["bootstrap_95"] for row in comparisons if row["bootstrap_95"] is not None]
        counts.append({"Study": study, "Comparisons": len(comparisons),
                       "Correlations computed": sum(row["rho"] is not None for row in comparisons),
                       "Intervals available": len(intervals),
                       "Intervals excluding zero": sum(low > 0 or high < 0 for low, high in intervals)})
    return counts


def learned_yield_panel():
    district_key = "leave_one_district_out"
    pooled = cached("climate_yield_validity_pooled.json")
    district = pooled["schemes"][district_key]
    names = {"county_mean": "County mean", "linear_trend": "Linear trend",
             "ridge": "Ridge", "random_forest": "Random forest"}
    rmse = " · ".join(f"{label} {district['performance'][model]['rmse_bu_ac']['value']:.3f}"
                      for model, label in names.items())
    st.write(f"**Kansas winter wheat · USDA district holdout · RMSE (bu/acre)**  \n{rmse}")
    st.caption(f"Pooled evaluation of {district['n']:,} county-years in {district['outer_folds']} USDA districts. "
               "The models describe weather–yield associations in Kansas county averages. "
               "Rotation quality still needs field evidence.")
    with st.expander("Learned climate-yield check"):
        study = cached("climate_yield_model.json")
        data = study["dataset"]
        practices = data["practice_counts"]
        st.write(f"Kansas winter wheat · {data['retained_counties']} counties · "
                 f"{data['retained_rows']:,} county-years · {data['first_year']}–{data['last_year']}")
        st.caption(f"{practices.get('non_irrigated', 0):,} reported non-irrigated yields and "
                   f"{practices.get('all_practices', 0):,} all-practice fallbacks. USDA NASS yield and NASA POWER "
                   "centroid weather are regional proxies. All-practice yields can include irrigated wheat.")
        cohorts = {"pooled": "All P25 rows", "non_irrigated": "Reported non-irrigated only",
                   "all_practices": "All-practice fallback only"}
        cohort = st.selectbox("Yield rows to evaluate", tuple(cohorts), format_func=cohorts.get,
                              key="climate_yield_cohort")
        validity = pooled if cohort == "pooled" else cached(f"climate_yield_validity_{cohort}.json")
        st.caption(f"{cohorts[cohort]} · {validity['n']:,} county-years · {validity['counties']} counties · "
                   f"{validity['first_year']}–{validity['last_year']}. The practice subsets cover different years "
                   "and are evaluated separately.")
        labels = {"leave_one_year_out": "Hold out one year", "leave_one_county_out": "Hold out one county",
                  "leave_one_district_out": "Hold out one USDA reporting district"}
        scheme = st.selectbox("Cross-validation split", tuple(labels), index=tuple(labels).index(district_key),
                              format_func=labels.get, key="climate_yield_split")
        results = (study["schemes"][scheme] if cohort == "pooled" and scheme in study["schemes"]
                   else validity["schemes"][scheme])
        st.caption(f"{results['outer_folds']} held-out folds · {results['n']:,} predictions per model · "
                   f"{study['model_count']} models and baselines · "
                   f"{study['learned_configuration_count']} learned configurations tested inside training folds.")
        metric_names = {"r2": "R²", "rmse_bu_ac": "RMSE (bu/acre)", "spearman": "Spearman ρ"}
        rows = []
        for model, scores in results["performance"].items():
            row = {"Model": names[model]}
            for key, name in metric_names.items():
                stat = scores[key]
                if stat["value"] is None:
                    row[name] = "Unavailable"
                else:
                    bound = stat["bootstrap_95"]
                    suffix = f" [{bound[0]:.3f}, {bound[1]:.3f}]" if bound is not None else ""
                    row[name] = f"{stat['value']:.3f}{suffix}"
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), hide_index=True)
        st.caption("Pooled held-out yield scores with descriptive 95% intervals. Bootstrap resamples complete held-out "
                   "groups. Detrending, feature scaling and model selection use training rows only. Held-out "
                   "counties and districts use reference yields from the training counties.")
        changes = []
        for model, stat in results["rmse_delta_vs_trend"].items():
            low, high = stat["bootstrap_95"]
            changes.append(f"{names[model]} {stat['value']:+.2f} [{low:+.2f}, {high:+.2f}]")
        st.caption("Paired RMSE change versus the linear trend (bu/acre) · " + " · ".join(changes))
        if scheme == district_key:
            st.caption(f"Each fold holds out one entire USDA reporting district. With {results['outer_folds']} "
                       "spatial blocks, the intervals are descriptive. Nearby counties can straddle district borders.")
        model = st.selectbox("Inspect a learned model", tuple(results["interpretation"]), format_func=names.get,
                             key="climate_yield_model")
        features = results["interpretation"][model]
        st.dataframe(pd.DataFrame([{"Feature": row["label"],
                                    "RMSE change when shuffled (bu/acre)": row["permutation_rmse_increase"]}
                                   for row in features]), hide_index=True)
        st.caption("Permutation importance shuffles each feature within held-out folds. A negative change means "
                   "the shuffle lowered error. Related weather features can share information.")
        feature = st.selectbox("Inspect partial dependence", [row["label"] for row in features],
                               key="climate_yield_feature")
        selected = next(row for row in features if row["label"] == feature)
        partial = selected["partial_dependence"]
        curve = go.Figure(go.Scatter(x=[row["value"] for row in partial],
                                     y=[row["predicted_yield_anomaly_bu_ac"] for row in partial],
                                     mode="lines+markers", marker_color="#32774F"))
        curve.update_layout(height=260, xaxis_title=selected["label"], yaxis_title="Modeled yield anomaly (bu/acre)",
                            margin=dict(t=12, b=55))
        st.plotly_chart(curve, key="climate_yield_partial_dependence", config={"displayModeBar": False})
        st.caption("Partial dependence averages predictions on held-out rows at training-fold quantiles of the "
                   "selected feature. County and district holdouts still use other locations in the same years. "
                   "County-average associations cannot establish causation "
                   "or validate rotation recommendations.")


def india_yield_screen_panel():
    report = cached("climate_yield_india_screen.json")
    candidate, = report["candidates"]
    with st.expander("India climate-yield replication (P31)"):
        st.write("The India check stopped at the preregistered crop-selection step.")
        st.write(f"Kharif rice was the only archived crop. "
                 f"{candidate['districts_meeting_yield_and_geography']} of "
                 f"{candidate['districts_in_archive']} districts met the yield-history and map requirements "
                 f"({candidate['first_yield_year']}–{candidate['last_yield_year']}).")
        st.caption("The archive lacks a comparable irrigated-area share and does not document the series as "
                   "rainfed-dominant. Historical district polygons can differ from current boundaries, and "
                   "district yields mix management practices. Centroid weather would be a coarse proxy for "
                   "conditions on farms across each district.")
        st.caption("No India models were fitted. The Kansas transfer check was skipped because winter wheat "
                   "and kharif rice use different crop seasons.")
        st.markdown(f"[Cached ICRISAT study archive]({report['source']})")


def cross_state_yield_panel():
    with st.expander("Cross-state winter-wheat check (P32)"):
        st.caption("Weather–yield associations in county averages do not validate rotation recommendations.")
        results_file = DATA / "climate_yield_transfer.json"
        if not results_file.is_file():
            inventory = cached("climate_yield_transfer_yield_inventory.json")
            st.write("The yield screen is complete. Cross-state model results are pending verified county weather locations.")
            for row in inventory.values():
                st.caption(f"{row['name']} · {row['eligible_counties']} counties, "
                           f"{row['eligible_rows']:,} county-years meet the yield-history requirement.")
            return
        report = cached(results_file.name)
        states = report["states"]
        cases = report["cases"]

        def case_name(key):
            row = cases[key]
            if row["kind"] == "pooled":
                return "All three states · state-blocked holdout"
            target = states[row["test_state"]]
            if row["kind"] == "in_state":
                return f"{target} · reporting-district holdout"
            sources = " + ".join(states[state] for state in row["train_states"])
            return f"{sources} → {target}"

        default = tuple(cases).index("pooled")
        key = st.selectbox("Evaluation", tuple(cases), format_func=case_name, index=default,
                           key="cross_state_yield_case")
        result = cases[key]
        st.caption(f"{result['n']:,} held-out county-years · {result['counties']} counties · "
                   f"{report['model_count']} models and baselines · "
                   f"{report['learned_configuration_count']} learned configurations across the two learners.")
        model_labels = {"county_mean": "County mean", "linear_trend": "Linear trend",
                        "ridge": "Ridge", "random_forest": "Random forest"}
        metric_labels = {"rmse_bu_ac": "RMSE (bu/acre)", "r2": "R²", "spearman": "Spearman ρ"}

        def estimate(value, signed=False):
            point = value["value"]
            if point is None:
                return "Unavailable"
            fmt = "+.3f" if signed else ".3f"
            interval = value["bootstrap_95"]
            suffix = f" [{interval[0]:{fmt}}, {interval[1]:{fmt}}]" if interval else ""
            return f"{point:{fmt}}{suffix}"

        st.dataframe(pd.DataFrame([{"Model": model_labels[model],
                                    **{label: estimate(scores[name]) for name, label in metric_labels.items()}}
                                   for model, scores in result["performance"].items()]), hide_index=True)
        if "own_baseline_rmse" in result:
            own = result["own_baseline_rmse"]
            st.caption(f"Own-state held-out references on the same rows · mean {own['county_mean']:.3f} "
                       f"and trend {own['linear_trend']:.3f} bu/acre RMSE.")
            deltas = result["rmse_delta_vs_own_baselines"]
            st.dataframe(pd.DataFrame([{"Model": model_labels[model],
                                        **{f"Δ RMSE vs own {model_labels[name].lower()}": estimate(values[model], True)
                                           for name, values in deltas.items()}}
                                       for model in ("ridge", "random_forest")]), hide_index=True)
        st.caption("Paired 95% bootstrap intervals are descriptive. The pooled check resamples three states. "
                   "NASA POWER county-centroid weather and USDA NASS county yields are area-level proxies. "
                   "Yield series mix management and can include irrigated wheat where all-practice records are used.")


def opportunity_panel(farm_id, farm_name):
    data = load(farm_id, "opportunity_windows")
    with st.container(key="opportunity_windows"):
        st.subheader("Opportunity windows")
        st.caption(farm_name)
        st.write("Look for recurring low greenness before checking an opening locally. A mixed MODIS pixel can "
                 "contain crops, weeds or other cover. Clouds and unknown management limit what low NDVI can tell us.")
        for flag in data["flags"]:
            st.warning(flag)
        if farm_id == "us_high_plains_b":
            st.warning("Kansas low-greenness window: may be winter-wheat dormancy, not bare soil. "
                       "The cached CDL and MODIS records cannot establish planting availability.")
        runs = data["sensitivity"]
        default = next(i for i, row in enumerate(runs) if row["offset"] == 0)
        levels = [row["threshold"] for row in runs]
        selected = st.selectbox("Low-NDVI threshold", levels, index=default, format_func=lambda v: f"{v:.2f}",
                                key=f"opportunity_threshold_{farm_id}")
        current = next(row for row in runs if row["threshold"] == selected)
        st.caption("Threshold evidence · assumption, validate locally · P5 cutoff and sensitivity settings. "
                   "Site flags lower the evidence grade for the window and climate-fit estimates.")
        view = st.selectbox("NDVI timeline", ["Typical year", *data["years"]],
                            key=f"opportunity_year_{farm_id}")
        series = (data["timeline"] if view == "Typical year" else
                  [row for row in data["annual_ndvi"] if row["year"] == view])
        figure = go.Figure(go.Scatter(x=[row["doy"] for row in series], y=[row["ndvi"] for row in series],
                                      mode="lines+markers", connectgaps=False, name="QA-screened MODIS NDVI",
                                      marker_color="#32774F"))
        figure.update_traces(hovertemplate="Day %{x} · NDVI %{y:.3f} · NASA Terra MODIS<extra></extra>")
        if view == "Typical year":
            for window in current["windows"]:
                start = window["start_doy"]
                stop = start + window["typical_days"]
                figure.add_vrect(x0=start, x1=min(stop, 366), fillcolor="#C58C40", opacity=.23, line_width=0)
                if stop > 366:
                    figure.add_vrect(x0=1, x1=stop - 365, fillcolor="#C58C40", opacity=.23, line_width=0)
        else:
            year = pd.Timestamp(view, 1, 1)
            next_year = pd.Timestamp(view + 1, 1, 1)
            for run in current["runs"]:
                start = max(year, pd.Timestamp(run["start"]))
                stop = min(next_year, pd.Timestamp(run["end_exclusive"]))
                if start < stop:
                    figure.add_vrect(x0=(start - year).days + 1, x1=(stop - year).days + 1,
                                     fillcolor="#C58C40", opacity=.23, line_width=0)
        figure.add_hline(y=selected, line_dash="dot", line_color="#956027")
        figure.update_layout(height=300, xaxis_title="Day of year", yaxis_title="NDVI",
                             margin=dict(t=12, r=18, b=50, l=56))
        st.plotly_chart(figure, key=f"opportunity_ndvi_{farm_id}", config={"displayModeBar": False})
        ndvi_grade = data["evidence"]["ndvi"]["label"].upper()
        window_grade = data["evidence"]["window"]["label"].upper()
        st.caption(f"NASA Terra MODIS NDVI · {data['years'][0]}–{data['years'][-1]} · "
                   f"{data['qa_composites']} QA-valid composites · NDVI evidence {ndvi_grade}. "
                   f"Shading estimates low greenness · window evidence {window_grade}.")
        st.dataframe(pd.DataFrame([{
            "NDVI cutoff": f"{row['threshold']:.2f}", "Detected runs": row["run_count"],
            "Recurrent windows": sum(w["status"] == "recurrent" for w in row["windows"]),
            "Evidence": window_grade,
        } for row in runs]), hide_index=True)
        if not any(w["status"] == "recurrent" for w in current["windows"]):
            st.info("No reliable recurring low-greenness window was found at this cutoff.")
        elif farm_id == "us_high_plains_b" or not any(
            item["local_catalog_seasons"] and item["checks"]["overall"]["passes"]
            for window in current["windows"] for item in window["fit"]
        ):
            st.info("No reliable planting window was established at this cutoff.")
        for window in current["windows"]:
            st.markdown(f"**{window['status'].capitalize()} low-NDVI window · evidence {window_grade}**")
            st.write(f"The low-greenness spans typically start around day {window['start_doy']} and last about "
                     f"{window['typical_days']} days. {window['supporting_years']} of {window['assessable_years']} "
                     f"QA-assessable years support this window, with {window['qa_composites']} valid composites "
                     "in the supporting spans.")
            if current["offset"] == 0 and not window["threshold_stable"]:
                st.caption("The same recurring window did not carry through both alternative cutoffs.")
            interval = window["bootstrap_interval"]
            if interval:
                low, high = interval["length_days"]
                st.caption(f"Median-length bootstrap interval {low:.0f}–{high:.0f} days · evidence {window_grade}.")
            labels = {"length": "Length", "temperature": "Temperature", "water": "Water", "overall": "Overall fit"}
            candidates = [item for item in window["fit"] if item["local_catalog_seasons"]]
            fit_rows = []
            for item in candidates:
                row = {"Crop": item["crop"], "Catalog season":
                       ", ".join(label.replace("_", " ") for label in item["local_catalog_seasons"])}
                for check, name in labels.items():
                    counts = item["checks"][check]
                    grade = item["evidence"][check]["label"].upper()
                    ratio = f"{counts['passes']}/{counts['n']}" if counts["n"] else "Unavailable (n=0)"
                    row[name] = f"{ratio} · {grade}"
                fit_rows.append(row)
            if fit_rows:
                st.dataframe(pd.DataFrame(fit_rows), hide_index=True)
                st.caption("Fit cells show years passing / years assessable and the P18 evidence label. "
                           "NASA POWER temperature and rainfall inform fit. POWER root-zone wetness is modeled. "
                           "Temperature and water are tested in long-enough windows. Crops are shown only "
                           "when their catalog includes a season at this farm. Fit uses the run's actual dates.")
            passing = [item for item in candidates if item["checks"]["overall"]["passes"]]
            if passing:
                if current["offset"] != 0:
                    st.info("These passes are from an alternative cutoff. Use the P5 cutoff as the reference.")
                for item in passing:
                    overall = item["checks"]["overall"]
                    grade = item["evidence"]["overall"]["label"].upper()
                    st.write(f"{item['crop']} fits the screen in {overall['passes']} of {overall['n']} years "
                             f"with this low-NDVI window · evidence {grade}.")
                names = {"nitrogen": "Net nitrogen carryover", "erosion_proxy": "Erosion proxy",
                         "water_used": "Crop water use", "unmet_water": "Unmet crop water"}
                st.markdown("**Modeled change from adding the crop to a gap in the baseline**")
                st.dataframe(pd.DataFrame([{
                    "Crop": item["crop"], "Metric": names[key], "Median change": f"{metric['median']:+.2f}",
                    "Range": " to ".join(f"{value:+.2f}" for value in metric["range"]),
                    "Unit": metric["unit"], "Evidence": item["evidence"][key]["label"].upper(),
                    "Source": {"nitrogen": "Crop catalog", "erosion_proxy": "NASA SRTM, NASA POWER, crop cover",
                               "water_used": "NASA POWER, mapped soil, crop catalog",
                               "unmet_water": "NASA POWER, mapped soil, crop catalog"}[key],
                } for item in passing for key, metric in item["modeled_addition"].items()]), hide_index=True)
                st.caption("Cover-crop water use is a cost to the following crop. The estimates give crop demand "
                           "met and unmet during the added gap crop. They do not quantify the next crop's water loss.")
            elif candidates:
                st.write("No crop with a matching catalog season passed all checks for this window.")
            else:
                st.write("No screened crop has a matching catalog season at this farm.")
        st.caption("Illustrative window screening · validate locally. Check soil moisture, seed availability "
                   "and costs locally. Farm calendars and yield effects require other evidence.")


def stress_map(data, preset):
    selected = data["presets"][preset]
    rain = data["rainfall_changes_pct"]
    temperatures = data["temperature_changes_c"]
    ids = list(dict.fromkeys(cell["winner_id"] for cell in selected["cells"]))
    palette = px.colors.qualitative.Safe
    colors = [palette[index % len(palette)] for index in range(len(ids))]
    n = len(ids)
    scale = [point for i, color in enumerate(colors)
             for point in ((i / n, color), ((i + 1) / n, color))]
    by_cell = {(cell["temperature_change_c"], cell["rainfall_change_pct"]): cell
               for cell in selected["cells"]}
    z, labels, hover = [], [], []
    for temp in temperatures:
        zrow, labelrow, hoverrow = [], [], []
        for change in rain:
            cell = by_cell[temp, change]
            identifier = cell["winner_id"]
            sequence = data["rotation_catalog"][identifier]["crop_ids"]
            zrow.append(ids.index(identifier))
            labelrow.append(f"S{ids.index(identifier) + 1}")
            hoverrow.append(" / ".join(" → ".join(year) for year in sequence))
        z.append(zrow)
        labels.append(labelrow)
        hover.append(hoverrow)
    figure = go.Figure(go.Heatmap(z=z, x=rain, y=temperatures, zmin=-.5, zmax=n-.5,
                                  colorscale=scale, showscale=False, xgap=2, ygap=2,
                                  text=labels, texttemplate="%{text}", customdata=hover,
                                  hovertemplate="Rainfall change %{x:+}%<br>Temperature +%{y:g} °C<br>"
                                                "Top rotation: %{customdata}<extra></extra>"))
    figure.update_layout(height=350, margin=dict(t=15, r=15, b=50, l=65),
                         xaxis_title="Uniform rainfall change (%)",
                         yaxis_title="Uniform temperature change (°C)")
    legend = [{"Map label": f"S{index + 1}", "Top rotation":
               " / ".join(" → ".join(year) for year in data["rotation_catalog"][identifier]["crop_ids"])}
              for index, identifier in enumerate(ids)]
    return figure, legend


def farm_map(farms, selected):
    geography = cached("world_land.json")
    lon, lat = [], []
    for ring in geography["rings"]:
        lon.extend([point[0] for point in ring] + [None])
        lat.extend([point[1] for point in ring] + [None])
    figure = go.Figure(go.Scatter(x=lon, y=lat, mode="lines", fill="toself", hoverinfo="skip",
                                  fillcolor="#E2EADF", line=dict(color="#B6CCB9", width=1), showlegend=False))
    figure.add_scatter(x=[farm["lon"] for farm in farms], y=[farm["lat"] for farm in farms],
                       mode="markers", text=[farm["name"] for farm in farms], hovertemplate="%{text}<extra></extra>",
                       marker=dict(size=13, color=["#286448" if farm["farm_id"] == selected else "#92713B"
                                                  for farm in farms]), showlegend=False)
    figure.update_layout(height=240, margin=dict(l=0, r=0, b=0, t=0), dragmode=False,
                         xaxis=dict(visible=False, range=[-140, 120], fixedrange=True),
                         yaxis=dict(visible=False, range=[-42, 70], fixedrange=True),
                         plot_bgcolor="#F0F5F2", paper_bgcolor="#F0F5F2")
    return figure


def edit_farm(farm, context, settings):
    key = farm["farm_id"]
    with st.expander("Edit farm assumptions"):
        baseline = farm["baseline_rotation_cycle"]
        crops = settings["crops"]
        lookup = list(crops)
        with st.form(f"edit_{key}"):
            size = st.number_input("Farm size (ha)", min_value=0.0, value=0.0, step=0.1,
                                   help="Context for the farmer. Comparisons use per-hectare or relative values.")
            irrigation = st.slider("Share of irrigation demand you can supply", 0., 1.,
                                   key=f"supply_{key}", value=float(farm["irrigation"]["supply_fraction"]), step=.05)
            available = st.number_input("Available soil water in top 30 cm (mm)", min_value=0.,
                                        value=float(context["soil"]["available_water_mm_0_30"]["value"]), step=1.)
            rotation = [[st.selectbox(f"Baseline crop · year {year + 1}, season {slot + 1}", lookup,
                       index=lookup.index(crop), format_func=lambda crop: crops[crop]["display_name"])
                         for slot, crop in enumerate(row)] for year, row in enumerate(baseline)]
            apply = st.form_submit_button("Apply farm inputs")
        if apply:
            st.session_state[f"edits_{key}"] = (irrigation, available, rotation, size)
        st.caption("Edited values are farmer inputs to validate locally.")
    return st.session_state.get(f"edits_{key}")


@st.cache_data(show_spinner="Recomputing edited farm comparison…")
def edited_results(farm, settings, edits, result, assessment, difference_threshold):
    supply, water, rotation, _ = edits
    farm = copy.deepcopy(farm)
    farm["irrigation"]["supply_fraction"] = supply
    farm["baseline_rotation_cycle"] = rotation
    model = preload(farm, processed=DATA, crops=settings["crops"], policy=settings["scoring"],
                    storage_override=water)
    years = result["horizon_years"]
    layers = allowed_layers(model, years)
    if count_rotations(layers, len(model.ids)) < 3:
        return None
    rotations = enumerate_canonical_rotations(layers, len(model.season_labels))
    _, scores, _ = score_rotations(model, rotations)
    presets = settings["weights_presets"]["presets"]
    weights = {name: np.array([preset[k] for k in METRICS]) for name, preset in presets.items()}
    baseline = baseline_indices(model, years)
    selected = [strategy(model, baseline, "baseline", None, weights)]
    selected[0]["why"] = "Your edited existing rotation."
    selected_vectors = [score_rotations(model, baseline)[1][0]]
    for name, vector in weights.items():
        for index in np.argsort(-(scores @ vector), kind="stable"):
            sequence = rotations[index]
            if all(np.max(np.abs(scores[index] - other)) > difference_threshold for other in selected_vectors):
                selected.append(strategy(model, sequence, name, name, weights))
                selected_vectors.append(scores[index])
                break
    if len(selected) < 3:
        return None
    updated = {**result, "strategies": selected, "verification": {},
               "selection": {"requested_alternatives": len(weights),
                             "displayed_alternatives": len(selected) - 1,
                             "difference_threshold": difference_threshold,
                             "source": "config/tie_diagnosis.json; design choice, not empirical"}}
    return updated, simulate(model, updated, assessment, presets, settings["uncertainty"])


def robust_pick_panel(farm, preset, farm_ids):
    data = load(farm["farm_id"], "robust_stability")
    by_preset = data["presets"][preset]
    labels = {"expected": "Expected score",
              "conditional_cvar": f"Feasible-only worst {data['tail_fraction']:.0%} mean",
              "minimax_regret": "Minimax regret"}

    def cycle(pick):
        size = len(pick["crop_ids"][0])
        crops = pick["crop_names"]
        years = [" → ".join(crops[i:i+size]) for i in range(0, len(crops), size)]
        return f"{years[0]} ×{len(years)}" if len(set(years)) == 1 else " / ".join(years)

    def fmt(value):
        return f"{value:.4f}" if value is not None else "—"

    rare_warning = "rarely feasible; not a practical recommendation"

    def feasibility(pick):
        return f"{pick['feasible_draws']}/{n} ({pick['feasible_share']:.1%})"

    def feasibility_flag(pick):
        return rare_warning if pick["feasible_share"] < .5 else ""

    all_presets = [entry for farm_id in farm_ids
                   for entry in load(farm_id, "robust_stability")["presets"].values()]
    same_counts = {objective: sum(entry["stability"][objective]["same_pick"] for entry in all_presets)
                   for objective in labels}
    summary_labels = ("expected score", "conditional CVaR", "minimax regret")
    count_summary = ", ".join(f"{label} {same_counts[key]} of {len(all_presets)}"
                              for key, label in zip(labels, summary_labels, strict=True))
    with st.container(key="robust_pick"):
        st.subheader("Robust pick under assumption changes (P28b)")
        st.caption(f"{farm['name']} · {title(preset)} · exact search of {data['candidate_count']:,} nominally feasible rotations")
        counts = data["design"]["draw_counts"]
        n = st.selectbox("Assumption draws", counts, index=len(counts) - 1, key="robust_draw_count")
        current = by_preset["draw_counts"][str(n)]
        nominal = current["nominal"]
        st.write("These risk-aware picks are preliminary and depend on the sampled assumption ranges. "
                 "Picks changed across draw counts.")
        st.caption(f"Across {', '.join(map(str, counts))} draws, farm–preset combinations that kept the "
                   f"same rotation · {count_summary}.")

        def table_row(name, pick, status, repeat=None, near_tie=False, objective_value=None):
            return {"Pick": name, "Rotation by year": cycle(pick), "Evidence": pick["evidence_label"].upper(),
                    "Feasible draws": feasibility(pick), "Across draw counts": status,
                    "Near-tie": "Yes" if near_tie else "—", "Objective value": fmt(objective_value),
                    "Nominal score cost": fmt(pick["nominal_cost"]),
                    "Finalist bootstrap wins": f"{repeat:.0%}" if repeat is not None else "—",
                    "Feasibility flag": feasibility_flag(pick)}

        rows = [table_row("Nominal score leader", nominal, "Reference", objective_value=nominal["nominal_score"])]
        for key, result in current["objectives"].items():
            if result["top"]:
                stability = by_preset["stability"][key]
                status = "Same pick" if stability["same_pick"] else "Pick changes"
                wins = stability["bootstrap"][str(n)]["pick_win_share"]
                pick = result["top"][0]
                rows.append(table_row(labels[key], pick, status, wins, result["near_tie"], pick[key]))
        flagged = [row["Pick"] for row in rows if row["Feasibility flag"]]
        if flagged:
            st.warning(f"{', '.join(flagged)} · {rare_warning}.")
        st.dataframe(pd.DataFrame(rows), hide_index=True)
        st.caption("Feasibility describes the share of modeled draws that passed the hard rules. "
                   "The under-half warning is a display cutoff.")
        st.caption(f"Lower maximum regret is better. CVaR averages the worst {data['tail_fraction']:.0%} of feasible "
                   "scores. Expected score and regret use zero when a hard rule fails. Bootstrap win shares compare "
                   "the union of the three finalists at each draw count.")
        with st.expander("Top three by objective and metric evidence"):
            finalists = []
            for key, result in current["objectives"].items():
                for rank, pick in enumerate(result["top"], 1):
                    finalists.append({"Objective": labels[key], "Place": ("Pick", "Runner-up", "Third")[rank - 1],
                                      "Rotation by year": cycle(pick), "Feasible draws": feasibility(pick),
                                      "Gap to optimum": f"{pick['gap_to_best']:.8f}",
                                      "Objective value": fmt(pick[key]), "Evidence": pick["evidence_label"].upper(),
                                      "Feasibility flag": feasibility_flag(pick)})
                if result["near_tie"]:
                    st.info(f"{labels[key]} has a near-tie with its runner-up "
                            f"({result['runner_up_gap']:.8f} weighted points apart).")
            st.dataframe(pd.DataFrame(finalists), hide_index=True)
            flagged_finalists = [f"{row['Objective']} ({row['Place'].lower()})" for row in finalists
                                 if row["Feasibility flag"] and row["Place"] != "Pick"]
            if flagged_finalists:
                st.caption(f"{', '.join(flagged_finalists)} · {rare_warning}.")
            for key, result in current["objectives"].items():
                if result["top"]:
                    evidence = result["top"][0]["metric_evidence"]
                    st.caption(f"{labels[key]} · " + " · ".join(f"{title(metric)} {level.upper()}"
                                                                for metric, level in evidence.items()))
            st.caption(f"Near-tie tolerance {data['precision_tolerance']:g} weighted points (P28 design choice).")
        old = current["unconditional_cvar"]
        st.caption(f"Original zero-score CVaR rule at {n} draws · maximum {old['maximum']:.4f} · "
                   f"candidates within tolerance of the maximum: {old['ties']:,}. Climate input · cached NASA POWER.")
        minimax = current["objectives"]["minimax_regret"]["top"][0]
        reduction = nominal["minimax_regret"] - minimax["minimax_regret"]
        st.write(f"The minimax pick lowers maximum regret by {reduction:.4f} points at "
                 f"a nominal cost of {minimax['nominal_cost']:.4f}." if reduction > data["precision_tolerance"]
                 else "The minimax pick does not lower maximum regret at the reported precision.")
        if "aco" in by_preset:
            aco = by_preset["aco"]
            original = aco["original_128"]
            control = aco["conditional_control_512"]
            explored = aco["conditional_exploration_512"]
            total = len(explored["trials"])
            st.info(f"Telangana CVaR swarm check · Original rule: {original['best_of_five_hits']}/"
                    f"{len(original['trials'])} exact hits. On the held-out 512-draw conditional objective, "
                    f"the original search reached {control['best_of_five_hits']}/{total} and the longer exploration "
                    f"search reached {explored['best_of_five_hits']}/{total} in best-of-five trials. "
                    "The table shows exact-search picks.")



def app():
    st.set_page_config(page_title="CropSwarm", page_icon="🌱", layout="wide")
    st.title("CropSwarm")
    st.write("Compare crop rotations using NASA Earth data, soil maps and your priorities.")
    settings = cached("app_settings.json")
    farms = settings["farms"]
    by_id = {farm["farm_id"]: farm for farm in farms}
    st.session_state.setdefault("farm_picker", farms[0]["farm_id"])
    if selected_map := st.session_state.get("farm_map"):
        points = selected_map.get("selection", {}).get("points", [])
        if points and points[0].get("curve_number", points[0].get("curveNumber")) == 1:
            index = points[0].get("point_index", points[0].get("pointIndex"))
            if index is not None and index != st.session_state.get("map_handled"):
                st.session_state["farm_picker"] = farms[index]["farm_id"]
                st.session_state["map_handled"] = index
    farm_id = st.selectbox("Choose an illustrative farm", list(by_id), format_func=lambda key: by_id[key]["name"],
                           key="farm_picker")
    farm = by_id[farm_id]
    st.caption(f"{farm['region']} · {farm['label']}")
    st.plotly_chart(farm_map(farms, farm_id), key="farm_map", on_select="rerun", selection_mode="points",
                    config={"displayModeBar": False})
    validity = load(farm_id, "validity")
    context = load(farm_id, "context")
    assessment = load(farm_id, "assessment")
    with st.container(key="climate_assessment"):
        st.subheader("Farm Climate Assessment")
        st.caption(farm["name"])
        if farm["farm_id"] == "us_high_plains_b" and farm["irrigation"]["supply_fraction"] == 0:
            st.caption("Rainfed reference · 0% of irrigation demand supplied · assumption, validate locally")
        st.write(assessment["assessment"].replace("longest observed dry spell", "longest dry spell in the POWER record"))
        for flag in validity["flags"]:
            st.warning(flag)
        if farm_id == "us_high_plains_b":
            st.caption("The 2019 spring MODIS peak over the CDL fallow neighborhood remains unexplained.")
        elif farm_id == "telangana_a":
            st.caption("Telangana's second crop season is tentative.")
        charts = st.tabs(["Monthly rainfall", "Temperature", "Vegetation", "Annual rainfall"])
        for tab, key in zip(charts, ("monthly_rain", "annual_temperature", "vegetation", "annual_rain"), strict=True):
            with tab:
                chart = pio.from_json((DATA / f"chart_{farm_id}_{key}.json").read_text())
                st.plotly_chart(chart, key=f"chart_{key}", config={"displayModeBar": False})
        st.caption("Processed NASA inputs include POWER weather, Terra MODIS NDVI, MODIS land cover and SRTM terrain. "
                   "GPM IMERG via POWER is used only for the rainfall agreement check on matching UTC days. "
                   "SMAP, ECOSTRESS, GRACE, Landsat and ERA5 were unused.")
    opportunity_panel(farm_id, farm["name"])
    with st.container(key="historical_validation"):
        st.subheader("Validation · historical back-test")
        counts = correlation_counts(by_id)
        computed = sum(row["Correlations computed"] for row in counts)
        comparisons = sum(row["Comparisons"] for row in counts)
        excluding_zero = sum(row["Intervals excluding zero"] for row in counts)
        st.write(f"Across all three farms, {computed} of {comparisons} comparisons produced a correlation. "
                 f"{excluding_zero} bootstrap intervals excluded zero.")
        st.caption("These checks compare NASA weather and vegetation data and examine consistency with county or "
                   "district yields. "
                   "Rotation recommendations still need field validation.")
        with st.expander("Correlation counts across all farms"):
            st.dataframe(pd.DataFrame(counts), hide_index=True)
            st.caption("Counts use full-precision endpoints. Intervals that touch zero include zero. "
                       "Intervals are descriptive and unadjusted for multiple comparisons.")
        backtest = load(farm_id, "backtest")
        st.caption(f"{backtest['years'][0]}–{backtest['years'][-1]} · CDL mapped classes in Kansas. "
                   "Crop identities in Telangana and Makueni are assumed. "
                   "This uses the reference farm inputs, even when you edit the comparison below.")
        figure = pio.from_json((DATA / f"chart_backtest_{farm_id}.json").read_text())
        st.plotly_chart(figure, key=f"backtest_{farm_id}", config={"displayModeBar": False})
        results = []
        for season, entry in backtest["seasons"].items():
            for name, statistic in entry["comparisons"].items():
                interval = statistic["bootstrap_95"]
                results.append({"Season": season, "Comparison": name.replace("_", " "),
                                "Spearman ρ": None if statistic["rho"] is None else round(statistic["rho"], 2),
                                "n": statistic["n"],
                                "Bootstrap 95%": "unavailable" if interval is None else
                                f"{interval[0]:.2f} to {interval[1]:.2f}",
                                "Small sample": "yes" if statistic["small_n"] else "no",
                                "Source": entry["source"]})
            direction = entry["directional"]
            st.caption(f"{season.replace('_', ' ').title()}: directionally consistent in "
                       f"{direction['consistent']} of {direction['assessable']} assessable year comparisons "
                       "(water stress versus NDVI peak).")
        st.dataframe(pd.DataFrame(results), hide_index=True)
        st.caption("Sources · NASA POWER daily climate; NASA Terra MOD13Q1 QA-filtered NDVI; "
                   "USDA NASS CDL Kansas classes; illustrative crop catalog and irrigation assumptions.")
        for caveat in backtest["caveats"]:
            st.caption(caveat)
        consistency = load(farm_id, "nasa_consistency")
        with st.expander(f"{consistency['years'][0]}–{consistency['years'][-1]} NASA climate and vegetation check"):
            st.write("Do NASA POWER rainfall and heat move with Terra MODIS greenness in the same season? "
                     "This crop-agnostic comparison describes agreement between the NASA data products. "
                     "Crop performance and rotation recommendations are outside its scope.")
            st.caption("Illustrative, validate locally. The 250 m MODIS pixel can mix fields, weeds and other cover. "
                       "The P5 season windows are approximate. Missing composites are excluded.")
            design = consistency["design"]
            years = design["reference_years"]
            st.caption(f"Rainfall anomaly compares seasonal totals with the {years[0]}–{years[-1]} mean. "
                       "Deficit is the shortfall below that mean. Heat days exceed the local seasonal "
                       f"{design['heat_quantile'] * 100:g}th percentile of daily maxima in that period. "
                       "These thresholds are design choices.")
            long_results = []
            for season, entry in consistency["seasons"].items():
                for note in entry["notes"]:
                    st.caption(f"{title(season)} · {note}")
                for statistic in entry["comparisons"]:
                    interval = statistic["bootstrap_95"]
                    long_results.append({
                        "Season": title(season), "POWER indicator": statistic["driver"],
                        "MODIS response": statistic["response"], "n": statistic["n"],
                        "Spearman ρ": None if statistic["rho"] is None else round(statistic["rho"], 2),
                        "Bootstrap 95%": "Unavailable" if interval is None else
                        f"{interval[0]:.2f} to {interval[1]:.2f}",
                        "Direction": f"Consistent in {statistic['consistent']} of {statistic['assessable']}",
                        "Finding": statistic["finding"],
                    })
            st.dataframe(pd.DataFrame(long_results), hide_index=True)
            st.caption("Sources · NASA POWER daily precipitation and maximum temperature · "
                       "NASA Terra MOD13Q1 QA-screened NDVI. Counts exclude median ties. "
                       "Bootstrap intervals are descriptive and samples below eight are small.")
            season = st.selectbox("Inspect seasonal values", tuple(consistency["seasons"]),
                                  format_func=title, key="nasa_consistency_season")
            st.dataframe(pd.DataFrame([{
                "Season start year": row["start_year"], "Rain anomaly (mm)": row["rainfall_anomaly_mm"],
                "Rain deficit (mm)": row["rainfall_deficit_mm"], "Heat days": row["heat_days"],
                "Integrated NDVI (NDVI × days)": row["integrated_ndvi_days"], "Peak NDVI": row["peak_ndvi"],
                "Composites passing QA": row["qa_composites"],
            } for row in consistency["seasons"][season]["rows"]]), hide_index=True)
            st.markdown("**MODIS coverage by calendar year**")
            st.dataframe(pd.DataFrame([{
                "Year": row["year"], "Expected": row["expected"], "Valid NDVI": row["valid_ndvi"],
                "Passes QA": row["qa_accepted"], "Record": row["status"],
            } for row in consistency["coverage"]]), hide_index=True)
        with st.expander("Yield back-test"):
            yields = load(farm_id, "yield_backtest")
            st.write(yields["geography"])
            st.caption(yields["note"])
            st.markdown(f"Yield source · [{yields['source']}]({yields['source_url']})")
            if yields["series"]:
                st.caption("Yield anomalies are departures from a separate linear trend for each crop and practice. "
                           "The county or district and the NASA POWER reference point cover different areas. "
                           "Model inputs are illustrative and need local validation.")
                st.caption(f"Modeled irrigation supply: {yields['irrigation_supply_fraction']:.0%} of unmet water demand "
                           "at the reference point. Actual county or district supply varies.")
                yield_results = []
                for series in yields["series"]:
                    years = [row["year"] for row in series["rows"]]
                    for statistic in series["comparisons"]:
                        interval = statistic["bootstrap_95"]
                        yield_results.append({
                            "Crop": series["crop_name"], "Yield series": series["practice"],
                            "Reported years": f"{min(years)}–{max(years)} ({len(years)} records)" if years else "None",
                            "POWER indicator": statistic["indicator"], "Paired n": statistic["n"],
                            "Spearman ρ": statistic["rho"],
                            "Bootstrap 95%": "Unavailable" if interval is None else
                            f"{interval[0]:.2f} to {interval[1]:.2f}",
                            "Finding": statistic["finding"],
                        })
                st.dataframe(pd.DataFrame(yield_results), hide_index=True,
                             column_config={"Spearman ρ": st.column_config.NumberColumn(format="%.2f")})
                st.caption("Sources · NASA POWER daily rainfall and maximum temperature · CropSwarm crop catalog, "
                           "season windows and soil water estimate. Bootstrap intervals are descriptive.")
        learned_yield_panel()
        india_yield_screen_panel()
        cross_state_yield_panel()
    edits = edit_farm(farm, context, settings)

    st.subheader("Farm priorities")
    presets = settings["weights_presets"]["presets"]
    preset = st.selectbox("Start from a priority preset", list(presets), format_func=title)
    priorities = st.columns(3)
    values = [priorities[i % 3].slider(title(metric), 0, 100, int(presets[preset][metric]*100 + .5),
                                      key=f"{farm_id}_{preset}_{metric}") for i, metric in enumerate(METRICS)]
    if not sum(values):
        st.info("All priorities are zero. The selected preset supplies the weights.")
        values = list(presets[preset].values())
    weight = np.array(values) / sum(values)
    st.caption("Adjusted priorities update scores for the displayed strategies. Scenario win percentages follow the selected named preset.")
    brief_controls(farm, preset)

    with st.container(key="climate_stress_test"):
        st.subheader("Robustness check under weather shifts (P16)")
        stress = load(farm_id, "stress_test")
        diagnosis = load(farm_id, "tie_diagnosis")
        figure, legend = stress_map(stress, preset)
        st.plotly_chart(figure, key=f"stress_{farm_id}_{preset}", config={"displayModeBar": False})
        st.caption(f"Winner map for {title(preset).lower()} · exact search over feasible rotations at every cell · "
                   "NASA POWER cached historical weather and illustrative crop inputs.")
        st.dataframe(pd.DataFrame(legend), hide_index=True)
        finding = diagnosis["presets"][preset]
        margins = load(farm_id, "stress_margins")
        margin = margins["presets"][preset]
        st.write(f"The weather-shift map labels a different top rotation in {finding['changed_cells']} of "
                 f"{finding['grid_cells']} tested climate cells compared with unchanged weather.")
        if margin["near_tie"]:
            st.info("top choices are close here · the nearest reported change is between options "
                    "within the illustrative near-tie tolerance. Equal-score labels may change "
                    "without a score gain.")
        elif finding["changed_cells"] == 0:
            st.caption("The map keeps the same top-rotation label throughout the tested grid.")
        st.caption(f"Near-tie tolerance · {margins['tolerance']['value']:g} normalized points between the top two "
                   "distinct rotations at either adjacent cell (design choice). "
                   "Cyclic starting-year labels count as one rotation.")
        st.caption(stress["caveat"])
        temperatures, rainfall = stress["temperature_changes_c"], stress["rainfall_changes_pct"]
        st.caption(f"Grid · {temperatures[0]:+g} to {temperatures[-1]:+g} °C by "
                   f"{temperatures[1] - temperatures[0]:g} °C, rainfall {rainfall[0]:+g}% to {rainfall[-1]:+g}% "
                   f"by {rainfall[1] - rainfall[0]:g}% (design choice). The map uses reference farm inputs.")

    with st.container(key="what_to_check_first"):
        st.subheader("What to check first")
        sensitivity = load(farm_id, "sensitivity")
        priorities_to_check = sensitivity["presets"][preset]
        joint = priorities_to_check["joint"]
        low, high = joint["top_score_range"]
        st.caption(f"{farm['name']} · {title(preset)} · {sensitivity['input_count']} inputs varied")
        st.caption("P22 sweeps broader assumptions jointly and reruns the exact search. "
                   "P10 resamples weather and varies parameters for the displayed rotations.")
        st.write(f"The top rotation changed in {joint['winner_change_fraction']:.0%} of {joint['evaluations']} "
                 f"joint draws. In {joint['material_change_fraction']:.0%}, the earlier leader became "
                 f"ineligible or the winner led by more than {sensitivity['design']['near_tie_gap']:g} points. "
                 f"The top score ranged from {low:.3f} to {high:.3f} on the model's 0–1 scale.")
        for item in check_first(priorities_to_check["ranking"]):
            st.markdown(f"**Priority {item['rank']} · {item['question']}**")
            st.write(item["reason"])
            grade = item["grade"].replace("_", " ").capitalize()
            st.caption(f"Input evidence · {grade} · {item['source']}")
        st.caption("This ranks sensitivity inside the model. Real-world importance needs local evidence. "
                   "The check uses the reference farm, the named preset and illustrative ranges.")
        with st.expander("All input effects"):
            st.dataframe(pd.DataFrame([{
                "Rank": row["rank"], "Input": row["question"],
                "Evidence": row["grade"], "Tied rank": row["tied"], "Weak effect": row["weak"],
                "Sweep settings": row["one_at_a_time"]["evaluations"],
                "Ranking changes in sweep": f"{row['one_at_a_time']['winner_change_fraction']:.0%}",
                "Material changes in sweep": f"{row['one_at_a_time']['material_change_fraction']:.0%}",
                "Top score span": row["one_at_a_time"]["top_score_span"],
                "Joint association method": row["joint_association"]["method"],
                "Joint association with top score": row["joint_association"]["top_score"],
                "Joint association with winner change": row["joint_association"]["winner_changed"],
            } for row in priorities_to_check["ranking"]]), hide_index=True)

    robust_pick_panel(farm, preset, by_id)

    result = load(farm_id, "strategies")
    uncertainty = load(farm_id, "uncertainty")
    if edits is not None:
        updated = edited_results(farm, settings, edits, result, assessment,
                                 diagnosis["alternative_difference"]["threshold"])
        if updated is None:
            st.warning("Fewer than three metric-distinct rotations meet those inputs. This table uses the reference farm assumptions.")
        else:
            result, uncertainty = updated
            st.caption("Showing a new exact comparison and new scenario draws for your edited inputs.")
            if edits[3] > 0:
                st.caption(f"Entered farm area {edits[3]:g} ha · farmer input")
    difference_threshold = diagnosis["alternative_difference"]["threshold"]
    alternatives = alternative_groups(result["strategies"][1:], difference_threshold)
    with st.container(key="strategy_comparison"):
        st.subheader("Compare rotations")
        st.caption(farm["name"])
        st.caption("Evidence labels: high = few assumed score inputs; medium = mixed provenance; "
                   "low = substantial assumptions or unresolved site validation. "
                   "Shares count input fields, scoring rules and crop slots equally; they are not causal fractions of the score.")
        scenario_names = {"historical": "Historical weather", "warmer_drier": "Warmer and drier",
                          "less_irrigation": "Less irrigation", "more_irrigation": "More irrigation"}
        scenario = st.selectbox("Scenario", list(scenario_names), format_func=scenario_names.get)
        sims = uncertainty["scenarios"][scenario]
        st.caption(f"{uncertainty['draws']} simulated draws · NASA POWER climate years · crop assumptions")
        if scenario != "historical":
            st.caption(f"Scenario irrigation supply share {sims['supply_fraction']:.0%} · temperature change "
                       f"{sims['temperature_change_c']:+g} °C · rainfall factor {sims['rainfall_factor']:.0%} · illustrative scenario assumptions")
        rows = []
        baseline = result["strategies"][0]
        for entry in result["strategies"]:
            key = entry["strategy_id"]
            stats = sims["strategies"][key]
            rating = np.array([entry["metrics"][m]["score"] for m in METRICS]) @ weight
            rows.append({"Strategy": "Existing rotation" if key == "baseline" else title(key),
                         "Rotation": " → ".join(entry["crop_names"]), "Historical priority score": round(float(rating), 3),
                         "Wins in draws": f"{stats['wins_pct'][preset]:.1f}%",
                         "Unmet water · median (mm)": round(stats["metrics"]["water"]["p50"], 1)})
        st.dataframe(pd.DataFrame(rows), hide_index=True)
        st.caption(f"{alternatives['displayed_alternatives']} displayed alternatives form "
                   f"{alternatives['meaningfully_different_groups']} "
                   f"distinct metric profiles. Each selected alternative differs from the baseline and every "
                   f"other selected alternative by more than {difference_threshold:g} on at least one normalized "
                   "metric. The threshold is a design choice.")
        st.caption("Wins use the selected preset and split credit among tied strategies. Water source · NASA POWER rainfall, soil available water and crop demand. Priority scores combine all six sourced metrics.")
        chart = go.Figure(go.Bar(x=[row["Strategy"] for row in rows], y=[row["Historical priority score"] for row in rows],
                                 marker_color=COLORS[:len(rows)]))
        chart.update_layout(yaxis=dict(range=[0, 1], title="Weighted score"), height=290,
                            margin=dict(t=10, r=16, l=46, b=25))
        st.plotly_chart(chart, key="comparison", config={"displayModeBar": False})

    for entry, row in zip(result["strategies"], rows, strict=True):
        key = entry["strategy_id"]
        stats = sims["strategies"][key]
        with st.expander(row["Strategy"], expanded=key == "baseline"):
            st.write(entry["why"])
            st.write(row["Rotation"])
            st.caption(f"Overall evidence: {entry['evidence_label'].upper()} · weakest of the six metric labels")
            for pair in alternatives["pairs"]:
                if pair["near_duplicate"] and key in (pair["first"], pair["second"]):
                    other = pair["second"] if key == pair["first"] else pair["first"]
                    st.info(f"Near-duplicate metric profile with {title(other)} "
                            f"(largest metric-score difference {pair['max_difference']:.3f}).")
            for flag, slots in entry["flags"].items():
                st.warning(f"{title(flag)} in slots {', '.join(str(slot + 1) for slot in slots)}.")
            if key != "baseline":
                better = [title(m) for m in METRICS if entry["metrics"][m]["score"] > baseline["metrics"][m]["score"]]
                worse = [title(m) for m in METRICS if entry["metrics"][m]["score"] < baseline["metrics"][m]["score"]]
                st.write("Benefits compared with the existing rotation · " + (", ".join(better) or "No higher model component"))
                st.write("Trade-offs · " + (", ".join(worse) or "No lower model component"))
            else:
                st.write("Benefit · Keeping the existing rotation avoids a change in planting plans.")
            st.write(f"Water risk · Median unmet demand is {stats['metrics']['water']['p50']:.0f} mm per slot "
                     f"in this scenario. NASA POWER rainfall, soil water and crop demand inform this estimate.")
            with st.container(key=f"uncertainty_{key}"):
                st.markdown("**Scenario uncertainty (P10)**")
                spread = settings["uncertainty"]["parameter_range_fraction"]
                st.caption(f"P10 resamples weather and varies modeled parameters within ±{spread:.0%} for the "
                           "displayed rotations. P22 sweeps broader assumptions jointly and reruns exact search.")
                st.caption(f"{farm['name']} · {row['Strategy']} · {scenario_names[scenario]}")
                st.write(f"Wins in {stats['wins_pct'][preset]:.1f}% of draws under the {title(preset).lower()} preset. "
                         f"Mean regret {stats['mean_regret'][preset]:.3f} weighted score units.")
                details = []
                for metric, info in entry["metrics"].items():
                    interval = stats["metrics"][metric]
                    evidence = info["evidence"]
                    details.append({"Metric": title(metric), "Evidence": evidence["label"].upper(),
                                    "Why lower": " ".join(evidence["reasons"]),
                                    "10th / 50th / 90th percentile":
                                    f"{interval['p10']:.2f} / {interval['p50']:.2f} / {interval['p90']:.2f}",
                                    "Unit": info["unit"], "Model score": round(info["score"], 3),
                                    "Source": info["source"], "How it works": info["explanation"]})
                st.dataframe(pd.DataFrame(details), hide_index=True)
                with st.expander("Evidence grade shares and input sources"):
                    grade_rows = []
                    for metric, info in entry["metrics"].items():
                        evidence = info["evidence"]
                        grade_rows.append({"Metric": title(metric), "Label": evidence["label"].upper(),
                                           **{grade.replace("_", " ").title(): f"{share:.0%}"
                                              for grade, share in evidence["shares"].items()}})
                    st.dataframe(pd.DataFrame(grade_rows), hide_index=True)
                    selected_metric = st.selectbox("Inspect input sources", METRICS, format_func=title,
                                                   key=f"evidence_metric_{farm_id}_{key}")
                    source_rows = {}
                    for item in entry["metrics"][selected_metric]["evidence"]["inputs"]:
                        lookup = (item["input"], item["grade"], item["source"])
                        source_rows[lookup] = source_rows.get(lookup, 0) + item["weight"]
                    st.dataframe(pd.DataFrame([{"Input": field, "Grade": grade, "Dependency share": f"{share:.0%}",
                                                "Source": source}
                                               for (field, grade, source), share in source_rows.items()]),
                                 hide_index=True)
            st.caption("Information gap · The soil, crop and farm assumptions below apply to this strategy.")

    if result["verification"]:
        with st.expander("How the optimizer was checked"):
            st.write(f"Exact enumeration checked {result['feasible_count']:,} feasible rotations across "
                     f"{result['horizon_years']} years.")
            for name, record in result["verification"].items():
                single, restarts = record["single_run"], record["best_of_restarts"]
                st.write(f"{title(name)} · exact hits {single['optimum_hits']}/{single['runs']} with one run, "
                         f"{restarts['optimum_hits']}/{restarts['runs']} with the best of {record['restart_count']}.")
    st.subheader("What we cannot know from these data")
    for item in dict.fromkeys(uncertainty["unknowns"] + [context["groundwater"]["regional_context"]["uncertainty_note"]]):
        st.write(f"• {item}")
    st.success("The farmer decides. Validate these illustrative comparisons locally before changing a rotation.")


app()
