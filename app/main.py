"""Offline CropSwarm decision support."""

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.optimizer import allowed_layers, count_rotations, enumerate_rotations, strategy
from src.scoring import METRICS, baseline_indices, preload, score_rotations
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
def edited_results(farm, settings, edits, result, assessment):
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
    rotations = enumerate_rotations(layers)
    _, scores, _ = score_rotations(model, rotations)
    presets = settings["weights_presets"]["presets"]
    weights = {name: np.array([preset[k] for k in METRICS]) for name, preset in presets.items()}
    baseline = baseline_indices(model, years)
    selected = [strategy(model, baseline, "baseline", None, weights)]
    selected[0]["why"] = "Your edited existing rotation."
    seen = {tuple(baseline)}
    for name, vector in weights.items():
        for index in np.argsort(-(scores @ vector), kind="stable"):
            sequence = rotations[index]
            if tuple(sequence) not in seen:
                seen.add(tuple(sequence))
                selected.append(strategy(model, sequence, name, name, weights))
                break
    if len(selected) < 3:
        return None
    updated = {**result, "strategies": selected, "verification": {}}
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
    st.caption(farm["region"])
    st.plotly_chart(farm_map(farms, farm_id), key="farm_map", on_select="rerun", selection_mode="points",
                    config={"displayModeBar": False})
    validity = load(farm_id, "validity")
    context = load(farm_id, "context")
    assessment = load(farm_id, "assessment")
    st.subheader("Farm Climate Assessment")
    st.write(assessment["assessment"])
    for flag in validity["flags"]:
        st.warning(flag)
    charts = st.tabs(["Monthly rainfall", "Temperature", "Vegetation", "Annual rainfall"])
    for tab, key in zip(charts, ("monthly_rain", "annual_temperature", "vegetation", "annual_rain"), strict=True):
        with tab:
            chart = pio.from_json((DATA / f"chart_{farm_id}_{key}.json").read_text())
            st.plotly_chart(chart, key=f"chart_{key}", config={"displayModeBar": False})
    st.caption("NASA POWER rainfall and temperature · NASA Terra MODIS vegetation")
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
    st.caption("Adjusted priorities rank the displayed strategies. Scenario win percentages follow the selected named preset.")

    result = load(farm_id, "strategies")
    uncertainty = load(farm_id, "uncertainty")
    if edits is not None:
        updated = edited_results(farm, settings, edits, result, assessment)
        if updated is None:
            st.warning("Fewer than three distinct rotations meet those inputs. This table uses the reference farm assumptions.")
        else:
            result, uncertainty = updated
            st.caption("Showing a new exact comparison and new scenario draws for your edited inputs.")
            if edits[3] > 0:
                st.caption(f"Entered farm area {edits[3]:g} ha · farmer input")
    st.subheader("Compare rotations")
    scenario_names = {"historical": "Historical weather", "warmer_drier": "Warmer and drier",
                      "less_irrigation": "Less irrigation", "more_irrigation": "More irrigation"}
    scenario = st.selectbox("Scenario", list(scenario_names), format_func=scenario_names.get)
    sims = uncertainty["scenarios"][scenario]
    st.caption(f"{uncertainty['draws']} simulated draws · NASA POWER climate years · crop assumptions")
    if scenario != "historical":
        st.caption(f"Irrigation share {sims['supply_fraction']:.0%} · temperature change "
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
    st.caption("Water source · NASA POWER rainfall, soil available water and crop demand. Priority scores combine all six sourced metrics.")
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
            st.write(f"Wins in {stats['wins_pct'][preset]:.1f}% of draws under the {title(preset).lower()} preset. "
                     f"Mean regret {stats['mean_regret'][preset]:.3f} weighted score units.")
            details = []
            for metric, info in entry["metrics"].items():
                interval = stats["metrics"][metric]
                details.append({"Metric": title(metric), "10th / 50th / 90th percentile":
                                f"{interval['p10']:.2f} / {interval['p50']:.2f} / {interval['p90']:.2f}",
                                "Unit": info["unit"], "Model score": round(info["score"], 3),
                                "Source": info["source"], "How it works": info["explanation"]})
            st.dataframe(pd.DataFrame(details), hide_index=True)
            st.caption("Information gap · The soil, crop and farm assumptions below apply to this strategy.")

    if result["verification"]:
        with st.expander("How the optimizer was checked"):
            st.write(f"Exact enumeration checked {result['feasible_count']:,} feasible rotations across "
                     f"{result['horizon_years']} years.")
            for name, record in result["verification"].items():
                st.write(f"{title(name)} · ant colony search hit the exact optimum in "
                         f"{record['optimum_hits']} of {record['runs']} runs.")
    st.subheader("What we cannot know from these data")
    for item in dict.fromkeys(uncertainty["unknowns"] + [context["groundwater"]["regional_context"]["uncertainty_note"]]):
        st.write(f"• {item}")
    st.success("The farmer decides. Validate these illustrative comparisons locally before changing a rotation.")


app()
