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
from src.localize import Locale
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


def correlation_counts(farm_ids):
    studies = {"Crop stress and NDVI, 2019–2023": [], "NASA weather and NDVI, 2001–2024": [],
               "Regional yield": []}
    for farm_id in farm_ids:
        for season in load(farm_id, "backtest")["seasons"].values():
            studies["Crop stress and NDVI, 2019–2023"].extend(season["comparisons"].values())
        for season in load(farm_id, "nasa_consistency")["seasons"].values():
            studies["NASA weather and NDVI, 2001–2024"].extend(season["comparisons"])
        for series in load(farm_id, "yield_backtest")["series"]:
            studies["Regional yield"].extend(series["comparisons"])
    counts = []
    for study, comparisons in studies.items():
        intervals = [row["bootstrap_95"] for row in comparisons if row["bootstrap_95"] is not None]
        counts.append({"Study": study, "Comparisons": len(comparisons),
                       "Correlations computed": sum(row["rho"] is not None for row in comparisons),
                       "Intervals available": len(intervals),
                       "Intervals excluding zero": sum(low > 0 or high < 0 for low, high in intervals)})
    return counts


def learned_yield_panel():
    with st.expander("Learned climate-yield check"):
        study = cached("climate_yield_model.json")
        data = study["dataset"]
        practices = data["practice_counts"]
        st.write(f"Kansas winter wheat · {data['retained_counties']} counties · "
                 f"{data['retained_rows']:,} county-years · {data['first_year']}–{data['last_year']}")
        st.caption(f"{practices.get('non_irrigated', 0):,} reported non-irrigated yields and "
                   f"{practices.get('all_practices', 0):,} all-practice fallbacks. USDA NASS yield and NASA POWER "
                   "centroid weather are regional proxies. All-practice yields can include irrigated wheat.")
        labels = {"leave_one_year_out": "Hold out one year", "leave_one_county_out": "Hold out one county"}
        names = {"county_mean": "County mean", "linear_trend": "Linear trend",
                 "ridge": "Ridge", "random_forest": "Random forest"}
        scheme = st.selectbox("Cross-validation split", tuple(labels), format_func=labels.get,
                              key="climate_yield_split")
        results = study["schemes"][scheme]
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
                   "groups. Yield trends and model settings use training rows only. For a held-out county, "
                   "both baselines use references from other counties.")
        changes = []
        for model, stat in results["rmse_delta_vs_trend"].items():
            low, high = stat["bootstrap_95"]
            changes.append(f"{names[model]} {stat['value']:+.2f} [{low:+.2f}, {high:+.2f}]")
        st.caption("Paired RMSE change versus the linear trend (bu/acre) · " + " · ".join(changes))
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
                   "selected feature. Holding out a county still lets the model see other counties in those years. "
                   "County-average associations cannot establish causation "
                   "or validate rotation recommendations.")


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
        st.caption("Threshold evidence · assumption, validate locally · reference cutoff and sensitivity settings. "
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
                st.caption("Fit cells show years passing / years assessable and the evidence label. "
                           "NASA POWER temperature and rainfall inform fit. POWER root-zone wetness is modeled. "
                           "Temperature and water are tested in long-enough windows. Crops are shown only "
                           "when their catalog includes a season at this farm. Fit uses the run's actual dates.")
            passing = [item for item in candidates if item["checks"]["overall"]["passes"]]
            if passing:
                if current["offset"] != 0:
                    st.info("These passes are from an alternative cutoff. Use the default cutoff as the reference.")
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


def current_locale(settings, farm_id):
    """Read the language and unit choices before their widgets are drawn."""
    language = st.session_state.get(f"language_{farm_id}", "en")
    local_units = st.session_state.get(f"units_{farm_id}", "local") == "local"
    return Locale(settings["locales"], farm_id, language, local_units)


def display_controls(settings, locale, farm_id):
    languages = settings["locales"]["languages"]
    left, middle, right = st.columns(3)
    if len(locale.languages) > 1:
        left.radio(locale.text("language"), locale.languages, format_func=languages.get,
                   key=f"language_{farm_id}", horizontal=True)
    middle.radio(locale.text("units"), ["local", "metric"], key=f"units_{farm_id}", horizontal=True,
                 format_func=lambda choice: locale.units_summary(choice == "local"))
    technical = right.toggle("Show technical checks (for reviewers)", key="show_technical",
                             help="Shows how the data and the model were checked: satellite greenness windows, "
                                  "historical back-tests, weather-shift maps and the search verification.")
    if len(locale.languages) > 1:
        st.caption(locale.text("draft_notice"))
    return technical


def season_names(seasons, locale):
    """One local season name per planting slot, with the months the model uses."""
    windows = seasons["season_windows"]
    return [" / ".join(locale.season(label, windows.get(label)) for label in slot["eligible_labels"])
            for slot in seasons["slots"]]


def crop_rows(entry, locale, crops):
    return [[locale.crop(crop, crops[crop]["display_name"]) for crop in year] for year in entry["crop_ids"]]


def rotation_text(entry, locale, crops):
    years = crop_rows(entry, locale, crops)
    if len(years[0]) == 1:
        return " → ".join(year[0] for year in years)
    if all(year == years[0] for year in years):
        return f"{locale.text('every_year')}: " + " → ".join(years[0])
    return " · ".join(f"{locale.text('year')} {number}: " + " → ".join(year)
                      for number, year in enumerate(years, 1))


def depth_text(locale, millimetres):
    inches = locale.unit("depth") == "in"
    return f"{locale.to_local('depth', millimetres):.{1 if inches else 0}f} {'inches' if inches else 'mm'}"


def climate_summary(assessment, locale):
    """Restate the cached climate numbers in everyday words and the farm's units."""
    metrics = assessment["metrics"]
    monthly = {int(month): value for month, value in metrics["monthly_precipitation"]["value"].items()}
    annual = sum(monthly.values())
    wettest = sorted(sorted(monthly, key=monthly.get, reverse=True)[:3])
    share = sum(monthly[month] for month in wettest) / annual if annual else 0
    names = [pd.Timestamp(2001, month, 1).strftime("%B") for month in wettest]
    regimes = {}
    for regime in metrics["annual_climate_regimes"]["value"].values():
        regimes[regime] = regimes.get(regime, 0) + 1
    counts = ", ".join(f"{count} {name.replace('_', ' and ')}" for name, count in
                       sorted(regimes.items(), key=lambda item: -item[1]))
    return (f"In plain words · Rain averages about {depth_text(locale, annual)} a year, and about {share:.0%} of it "
            f"falls in {', '.join(names[:-1])} and {names[-1]}. From one year to the next the total typically "
            f"differs from that average by about {metrics['rainfall_cv']['value']:.0%}. Of the {sum(regimes.values())} "
            f"years on record, the model counts {counts}. The longest stretch without meaningful rain was "
            f"{metrics['longest_observed_dry_spell']['value']} days.")


def climate_panel(farm, locale, validity, assessment):
    farm_id = farm["farm_id"]
    with st.container(key="climate_assessment"):
        st.subheader(locale.text("climate_heading"))
        st.caption(farm["name"])
        if farm_id == "us_high_plains_b" and farm["irrigation"]["supply_fraction"] == 0:
            st.caption("Rainfed reference · 0% of irrigation demand supplied · assumption, validate locally")
        st.write(climate_summary(assessment, locale))
        st.caption("Record details · " +
                   assessment["assessment"].replace("longest observed dry spell", "longest dry spell in the POWER record")
                   + " The coefficient of variation is the year-to-year spread divided by the average.")
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
        if locale.unit("depth") != "mm":
            st.caption("These charts and the record details use metric units: 25.4 mm of rain is 1 inch, "
                       "and a change of 1 °C is a change of 1.8 °F.")
        st.caption("Processed NASA inputs include POWER weather, Terra MODIS NDVI, MODIS land cover and SRTM terrain. "
                   "GPM IMERG via POWER is used only for the rainfall agreement check on matching UTC days. "
                   "SMAP, ECOSTRESS, GRACE, Landsat and ERA5 were unused.")


def edit_farm(farm, context, settings, locale, names):
    key = farm["farm_id"]
    with st.expander(locale.text("edit_heading")):
        baseline = farm["baseline_rotation_cycle"]
        crops = settings["crops"]
        lookup = list(crops)
        area, depth = locale.unit("area"), locale.unit("depth")
        reference = float(context["soil"]["available_water_mm_0_30"]["value"])
        inches = depth == "in"
        shown = round(locale.to_local("depth", reference), 2 if inches else 1)
        with st.form(f"edit_{key}"):
            size = st.number_input(f"Farm size ({area})", min_value=0.0, value=0.0, step=0.1,
                                   help="For your reference only. Every comparison is per unit of land.")
            irrigation = st.slider("Share of the crop's missing water you can supply by irrigation (%)", 0, 100,
                                   key=f"supply_{key}", value=int(round(100 * farm["irrigation"]["supply_fraction"])),
                                   step=5, help="0% means the crop depends on rain alone. 100% means you can "
                                                "irrigate whenever rain falls short.")
            available = st.number_input(
                f"Water the top {'12 in' if inches else '30 cm'} of your soil can hold ({depth})", min_value=0.,
                value=shown, step=.05 if inches else 1.,
                help="Sandy soils hold less and clay or loam soils hold more. A soil test or your extension "
                     "office can give a local value.")
            rotation = [[st.selectbox(
                f"Existing crop · {locale.text('year').lower()} {year + 1}" +
                (f" · {names[slot]}" if len(row) > 1 else ""), lookup, index=lookup.index(crop),
                format_func=lambda crop: locale.crop(crop, crops[crop]["display_name"]))
                         for slot, crop in enumerate(row)] for year, row in enumerate(baseline)]
            apply = st.form_submit_button("Apply farm inputs")
        if apply:
            # An untouched soil value keeps the exact reference figure despite display rounding.
            water = reference if available == shown else locale.to_metric("depth", available)
            st.session_state[f"edits_{key}"] = (irrigation / 100, water, rotation, locale.to_metric("area", size))
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


def validation_panel(farm_id, farm_ids):
    with st.container(key="historical_validation"):
        st.subheader("Validation · historical back-test")
        counts = correlation_counts(farm_ids)
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
                   "This uses the reference farm inputs, even when you edit the comparison above.")
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
                       "The derived season windows are approximate. Missing composites are excluded.")
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
        learned_yield_panel()


def robustness_panel(farm_id, preset, diagnosis):
    with st.container(key="climate_stress_test"):
        st.subheader("Robustness check under weather shifts")
        stress = load(farm_id, "stress_test")
        figure, legend = stress_map(stress, preset)
        st.plotly_chart(figure, key=f"stress_{farm_id}_{preset}", config={"displayModeBar": False})
        st.caption(f"Winner map for {title(preset).lower()} · exact search over feasible rotations at every cell · "
                   "NASA POWER cached historical weather and illustrative crop inputs.")
        st.dataframe(pd.DataFrame(legend), hide_index=True)
        finding = diagnosis["presets"][preset]
        margin = load(farm_id, "stress_margins")["presets"][preset]
        st.write(f"The weather-shift map labels a different top rotation in {finding['changed_cells']} of "
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
                   "The map uses reference farm inputs even when you edit the comparison above.")


def check_first_panel(farm, preset, locale, technical):
    with st.container(key="what_to_check_first"):
        st.subheader(locale.text("check_first_heading"))
        sensitivity = load(farm["farm_id"], "sensitivity")
        priorities_to_check = sensitivity["presets"][preset]
        joint = priorities_to_check["joint"]
        low, high = joint["top_score_range"]
        st.caption(f"{farm['name']} · {locale.preset(preset)} · {sensitivity['input_count']} inputs varied")
        st.write(f"The model rests on assumptions about crops, seasons and scoring rules. We changed many of them "
                 f"together and repeated the full search {joint['evaluations']} times. The top rotation changed in "
                 f"{joint['winner_change_fraction']:.0%} of those runs. In {joint['material_change_fraction']:.0%} "
                 f"the change was clear-cut: the earlier leader dropped out, or the new leader was ahead by more than "
                 f"{sensitivity['design']['near_tie_gap']:g} points. The top score ranged from {low:.3f} to {high:.3f} "
                 "on the 0–1 scale. These are the inputs that move the result most, so check them locally first.")
        for item in check_first(priorities_to_check["ranking"]):
            st.markdown(f"**Priority {item['rank']} · {item['question']}**")
            st.write(item["reason"])
            grade = item["grade"].replace("_", " ").capitalize()
            st.caption(f"Input evidence · {grade} · {item['source']}")
        st.caption("This ranks sensitivity inside the model. Real-world importance needs local evidence. "
                   "The check uses the reference farm, the named preset and illustrative ranges.")
        st.caption("This check varies many assumptions together and repeats the full search. The test runs under "
                   "Compare rotations re-use past weather years and vary crop values for the displayed rotations only.")
        if not technical:
            return
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


def optimizer_panel(result):
    if result["verification"]:
        with st.expander("How the optimizer was checked"):
            st.write(f"Exact enumeration checked {result['feasible_count']:,} feasible rotations across "
                     f"{result['horizon_years']} years.")
            for name, record in result["verification"].items():
                single, restarts = record["single_run"], record["best_of_restarts"]
                st.write(f"{title(name)} · exact hits {single['optimum_hits']}/{single['runs']} with one run, "
                         f"{restarts['optimum_hits']}/{restarts['runs']} with the best of {record['restart_count']}.")


def app():
    st.set_page_config(page_title="CropSwarm", page_icon="🌱", layout="wide")
    settings = cached("app_settings.json")
    farms = settings["farms"]
    crops = settings["crops"]
    by_id = {farm["farm_id"]: farm for farm in farms}
    st.session_state.setdefault("farm_picker", farms[0]["farm_id"])
    if selected_map := st.session_state.get("farm_map"):
        points = selected_map.get("selection", {}).get("points", [])
        if points and points[0].get("curve_number", points[0].get("curveNumber")) == 1:
            index = points[0].get("point_index", points[0].get("pointIndex"))
            if index is not None and index != st.session_state.get("map_handled"):
                st.session_state["farm_picker"] = farms[index]["farm_id"]
                st.session_state["map_handled"] = index
    locale = current_locale(settings, st.session_state["farm_picker"])
    st.title("CropSwarm")
    st.write(locale.text("tagline"))
    farm_id = st.selectbox("Choose an illustrative farm", list(by_id), format_func=lambda key: by_id[key]["name"],
                           key="farm_picker")
    farm = by_id[farm_id]
    st.caption(f"{farm['region']} · {farm['label']}")
    st.plotly_chart(farm_map(farms, farm_id), key="farm_map", on_select="rerun", selection_mode="points",
                    config={"displayModeBar": False})
    technical = display_controls(settings, locale, farm_id)
    validity = load(farm_id, "validity")
    context = load(farm_id, "context")
    assessment = load(farm_id, "assessment")
    diagnosis = load(farm_id, "tie_diagnosis")
    result = load(farm_id, "strategies")
    uncertainty = load(farm_id, "uncertainty")
    names = season_names(load(farm_id, "seasons"), locale)
    with st.expander(locale.text("glossary_title")):
        for term, meaning in locale.glossary(draws=uncertainty["draws"]):
            st.markdown(f"**{term}** · {meaning}")
        for metric in METRICS:
            st.markdown(f"**{locale.metric(metric)}** · {locale.metric_meaning(metric)}")
    climate_panel(farm, locale, validity, assessment)
    edits = edit_farm(farm, context, settings, locale, names)

    st.subheader(locale.text("priorities_heading"))
    presets = settings["weights_presets"]["presets"]
    preset = st.selectbox("Start from a priority preset", list(presets), format_func=locale.preset)
    priorities = st.columns(3)
    values = [priorities[i % 3].slider(locale.metric(metric), 0, 100, int(presets[preset][metric]*100 + .5),
                                      key=f"{farm_id}_{preset}_{metric}", help=locale.metric_meaning(metric))
              for i, metric in enumerate(METRICS)]
    if not sum(values):
        st.info("All priorities are zero. The selected preset supplies the weights.")
        values = list(presets[preset].values())
    weight = np.array(values) / sum(values)
    st.caption("Move a slider to the right to make that goal count for more. Adjusted priorities update the scores "
               "of the displayed rotations. The share of test runs each one comes out best in follows the selected "
               "named preset.")

    if edits is not None:
        updated = edited_results(farm, settings, edits, result, assessment,
                                 diagnosis["alternative_difference"]["threshold"])
        if updated is None:
            st.warning("Fewer than three metric-distinct rotations meet those inputs. This table uses the reference farm assumptions.")
        else:
            result, uncertainty = updated
            st.caption("Showing a new exact comparison and new test runs for your edited inputs.")
            if edits[3] > 0:
                st.caption(f"Entered farm area {locale.to_local('area', edits[3]):g} {locale.unit('area')} · farmer input")
    difference_threshold = diagnosis["alternative_difference"]["threshold"]
    alternatives = alternative_groups(result["strategies"][1:], difference_threshold)
    with st.container(key="strategy_comparison"):
        st.subheader(locale.text("compare_heading"))
        st.caption(farm["name"])
        st.caption("Evidence labels: high = few assumed score inputs; medium = mixed provenance; "
                   "low = substantial assumptions or unresolved site validation. "
                   "Shares count input fields, scoring rules and crop slots equally; they are not causal fractions of the score.")
        scenario_names = {"historical": "Historical weather", "warmer_drier": "Warmer and drier",
                          "less_irrigation": "Less irrigation", "more_irrigation": "More irrigation"}
        scenario = st.selectbox("Scenario", list(scenario_names), format_func=scenario_names.get)
        sims = uncertainty["scenarios"][scenario]
        st.caption(f"{uncertainty['draws']} test runs · each one re-uses past NASA POWER weather years and slightly "
                   "different crop values")
        if scenario != "historical":
            st.caption(f"Scenario irrigation supply share {sims['supply_fraction']:.0%} · temperature change "
                       f"{sims['temperature_change_c']:+g} °C · rainfall factor {sims['rainfall_factor']:.0%} · illustrative scenario assumptions")
        rows = []
        baseline = result["strategies"][0]
        for entry in result["strategies"]:
            key = entry["strategy_id"]
            stats = sims["strategies"][key]
            rating = np.array([entry["metrics"][m]["score"] for m in METRICS]) @ weight
            rows.append({"Strategy": locale.text("existing_rotation") if key == "baseline" else locale.preset(key),
                         "Rotation": rotation_text(entry, locale, crops), "Score": round(float(rating), 3),
                         "Wins": f"{stats['wins_pct'][preset]:.1f}%",
                         "Shortage": round(locale.to_local("depth", stats["metrics"]["water"]["p50"]),
                                           2 if locale.unit("depth") == "in" else 1)})
        headings = {"Strategy": locale.text("strategy"), "Rotation": locale.text("rotation"),
                    "Score": locale.text("score"), "Wins": locale.text("best_in_runs"),
                    "Shortage": locale.text("water_shortage", unit=locale.unit("depth"))}
        st.dataframe(pd.DataFrame(rows).rename(columns=headings), hide_index=True)
        st.caption(f"{alternatives['displayed_alternatives']} displayed alternatives form "
                   f"{alternatives['meaningfully_different_groups']} "
                   f"distinct metric profiles. Each selected alternative differs from the baseline and every "
                   f"other selected alternative by more than {difference_threshold:g} on at least one normalized "
                   "metric. The threshold is a design choice.")
        st.caption(f"The score runs from 0 (worst) to 1 (best) and combines all six measures using your priorities. "
                   f"'{locale.text('best_in_runs')}' uses the selected preset and splits credit among tied options. "
                   "Water shortage source · NASA POWER rainfall, soil available water and crop demand.")
        chart = go.Figure(go.Bar(x=[row["Strategy"] for row in rows], y=[row["Score"] for row in rows],
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
            if len(names) > 1:
                st.dataframe(pd.DataFrame([{locale.text("year"): number, **dict(zip(names, year, strict=True))}
                                           for number, year in enumerate(crop_rows(entry, locale, crops), 1)]),
                             hide_index=True)
            st.caption(f"Overall evidence: {entry['evidence_label'].upper()} · weakest of the six metric labels")
            for pair in alternatives["pairs"]:
                if pair["near_duplicate"] and key in (pair["first"], pair["second"]):
                    other = pair["second"] if key == pair["first"] else pair["first"]
                    st.info(f"Near-duplicate metric profile with {title(other)} "
                            f"(largest metric-score difference {pair['max_difference']:.3f}).")
            for flag, slots in entry["flags"].items():
                st.warning(f"{locale.flag(flag)} "
                           f"{locale.text('slots_affected', slots=', '.join(str(slot + 1) for slot in slots))}")
            if key != "baseline":
                better = [locale.metric(m) for m in METRICS
                          if entry["metrics"][m]["score"] > baseline["metrics"][m]["score"]]
                worse = [locale.metric(m) for m in METRICS
                         if entry["metrics"][m]["score"] < baseline["metrics"][m]["score"]]
                st.write(f"{locale.text('better_on')} · " + (", ".join(better) or locale.text("nothing")))
                st.write(f"{locale.text('worse_on')} · " + (", ".join(worse) or locale.text("nothing")))
            else:
                st.write(locale.text("keep_existing_benefit"))
            st.write(f"{locale.metric('water')} · In a typical test run this rotation is about "
                     f"{depth_text(locale, stats['metrics']['water']['p50'])} of water short per season in this "
                     "scenario. NASA POWER rainfall, soil water and crop water needs inform this estimate.")
            with st.container(key=f"uncertainty_{key}"):
                st.markdown(f"**{locale.text('how_much_vary')}**")
                spread = settings["uncertainty"]["parameter_range_fraction"]
                st.caption(f"Each test run re-uses randomly chosen past weather years and shifts the crop values by "
                           f"up to ±{spread:.0%}, for the displayed rotations only. 'What to check first' varies "
                           "wider assumptions and repeats the full search.")
                st.caption(f"{farm['name']} · {row['Strategy']} · {scenario_names[scenario]}")
                st.write(f"Comes out best in {stats['wins_pct'][preset]:.1f}% of the {uncertainty['draws']} test runs "
                         f"under the {locale.preset(preset).lower()} priorities. On average it scores "
                         f"{stats['mean_regret'][preset]:.3f} below the best option in the same run, on the 0–1 scale.")
                details = []
                for metric, info in entry["metrics"].items():
                    interval = stats["metrics"][metric]
                    evidence = info["evidence"]
                    low, typical, high = (locale.metric_value(metric, interval[point])[0]
                                          for point in ("p10", "p50", "p90"))
                    details.append({"Measure": locale.metric(metric),
                                    locale.text("what_it_means"): locale.metric_meaning(metric),
                                    "Low / typical / high": f"{low:.2f} / {typical:.2f} / {high:.2f}",
                                    "Unit": locale.metric_value(metric, 0)[1], "Score (0–1)": round(info["score"], 3),
                                    "Evidence": evidence["label"].upper(),
                                    "Why the evidence is limited": " ".join(evidence["reasons"]),
                                    "Source": info["source"], "How it is calculated": info["explanation"]})
                st.dataframe(pd.DataFrame(details), hide_index=True)
                st.caption("Low and high leave out the lowest and highest tenth of the test runs. "
                           "Typical is the middle run.")
                with st.expander("Evidence grade shares and input sources"):
                    grade_rows = []
                    for metric, info in entry["metrics"].items():
                        evidence = info["evidence"]
                        grade_rows.append({"Metric": locale.metric(metric), "Label": evidence["label"].upper(),
                                           **{grade.replace("_", " ").title(): f"{share:.0%}"
                                              for grade, share in evidence["shares"].items()}})
                    st.dataframe(pd.DataFrame(grade_rows), hide_index=True)
                    selected_metric = st.selectbox("Inspect input sources", METRICS, format_func=locale.metric,
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

    check_first_panel(farm, preset, locale, technical)
    st.subheader(locale.text("unknown_heading"))
    for item in dict.fromkeys(uncertainty["unknowns"] + [context["groundwater"]["regional_context"]["uncertainty_note"]]):
        st.write(f"• {item}")
    st.success(locale.text("farmer_decides"))

    if technical:
        st.divider()
        st.header("Technical checks")
        st.caption("For reviewers · how the data and the model were checked. These panels use the reference farm "
                   "inputs, English wording and metric units.")
        with st.expander("Technical terms used below"):
            for row in settings["locales"]["technical_glossary"]:
                st.markdown(f"**{row['term']}** · {row['meaning']}")
        opportunity_panel(farm_id, farm["name"])
        validation_panel(farm_id, by_id)
        robustness_panel(farm_id, preset, diagnosis)
        optimizer_panel(result)


app()
