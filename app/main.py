"""Offline CropSwarm decision support."""

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.optimizer import allowed_layers, count_rotations, enumerate_canonical_rotations, strategy
from src.scoring import METRICS, baseline_indices, preload, score_rotations
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


def app():
    st.set_page_config(page_title="CropSwarm", page_icon="🌱", layout="wide")
    st.title("CropSwarm")
    st.write("Compare crop rotations using NASA observations, soil maps and your priorities.")
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
        st.caption("NASA POWER rainfall and temperature · GPM IMERG for the rainfall agreement check · NASA Terra MODIS vegetation")
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
        st.caption("2019–2023 · CDL mapped classes in Kansas; assumed crop identities in Telangana and Makueni. "
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
        with st.expander("2001–2024 NASA climate and vegetation check"):
            consistency = load(farm_id, "nasa_consistency")
            st.write("Do NASA POWER rainfall and heat move with Terra MODIS greenness in the same season? "
                     "This crop-agnostic comparison describes agreement between the NASA data products. "
                     "Crop performance and rotation recommendations are outside its scope.")
            st.caption("Illustrative, validate locally. The 250 m MODIS pixel can mix fields, weeds and other cover. "
                       "The P5 season windows are approximate. Missing composites are excluded.")
            st.caption("Rainfall anomaly compares seasonal totals with the 1991–2020 mean. "
                       "Deficit is the shortfall below that mean. Heat days exceed the local seasonal "
                       "90th percentile of daily maxima in that period. These thresholds are design choices.")
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

    with st.container(key="climate_stress_test"):
        st.subheader("Robustness check")
        stress = load(farm_id, "stress_test")
        diagnosis = load(farm_id, "tie_diagnosis")
        figure, legend = stress_map(stress, preset)
        st.plotly_chart(figure, key=f"stress_{farm_id}_{preset}", config={"displayModeBar": False})
        st.caption(f"Winner map for {title(preset).lower()} · exact search over feasible rotations at every cell · "
                   "NASA POWER cached historical weather and illustrative crop inputs.")
        st.dataframe(pd.DataFrame(legend), hide_index=True)
        finding = diagnosis["presets"][preset]
        margin = load(farm_id, "stress_margins")["presets"][preset]
        st.write(f"The robustness map labels a different top rotation in {finding['changed_cells']} of "
                 f"{finding['grid_cells']} tested climate cells compared with unchanged weather.")
        if margin["near_tie"]:
            st.info("top choices are close here · the nearest reported change is between options "
                    "within the illustrative near-tie tolerance. Equal-score labels may change "
                    "without a score gain.")
        elif finding["changed_cells"] == 0:
            st.caption("The map keeps the same top-rotation label throughout the tested grid.")
        st.caption("Near tie: top-two distinct-rotation score gap ≤0.01 normalized points at either adjacent "
                   "cell · design choice, not empirical. Cyclic starting-year labels count as one rotation.")
        st.caption(stress["caveat"])
        st.caption("Grid: +0 to +3 °C by 0.5 °C; rainfall −30% to +10% by 10% · design choice, not empirical. "
                   "The map uses reference farm inputs even when you edit the comparison below.")

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
                st.markdown("**Scenario uncertainty**")
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
