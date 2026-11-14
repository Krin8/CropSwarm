# CropSwarm submission summary

## Summary (150 words)

CropSwarm is an offline decision-support prototype that helps farmers compare crop rotations at three illustrative locations: Kansas, Telangana, and Makueni. For each location it preserves a baseline and offers four alternative strategies, explaining evidence, benefits, risks, and information gaps. NASA POWER weather, Terra MODIS vegetation, and SRTM terrain inform seasonal diagnostics and mechanistic scores alongside soil estimates, crop parameters, and farmer priorities. Rule-based constraints screen proposed rotations; exact enumeration checks ant-colony search results. Seeded scenario draws display ranges, win percentages, regret, and sensitivity rather than a single promised outcome. The app tags data sources on metrics and keeps conflicting evidence and baseline violations in view. Kansas is modeled as rainfed; its spring vegetation peak over mapped fallow remains unexplained. Telangana's second season is tentative, and Makueni cropland is unverified. All points, management assumptions, crop values, and indices are illustrative and need local validation. Farmers and local experts retain the decision.

## Data actually used

| Provider | Dataset | Role in results |
|---|---|---|
| NASA | [POWER](data_pipeline.md) corrected precipitation, temperature, radiation, humidity and modeled root-zone wetness | Weather diagnostics, crop water balance and scenarios. POWER `PRECTOTCORR` drives seasonal windows and strategy scores. |
| NASA | [GPM IMERG via POWER](data_pipeline.md) | **Used in the rainfall agreement diagnostic** shown in the climate assessment. It was **not used** to score or rank rotations. |
| NASA | [Terra MODIS MOD13Q1 and MCD12Q1](data_pipeline.md) | Vegetation seasonality and land-cover validity checks. They do not establish crop identity at a point. |
| NASA / NGA | [SRTM](data_pipeline.md) through OpenTopoData | Terrain slope proxy in the erosion score. |
| Non-NASA | [ISRIC SoilGrids](api_status.md) | Gridded soil texture and organic-carbon estimates. |
| Non-NASA | [USDA SSURGO and CDL](api_status.md) | Kansas soil context and mapped crop history; CDL is not a farm management record. |
| Non-NASA | [Crop catalog and assumptions](crops.md) | Indicative crop water need, sourced botanical families and locally unverified values for crop climate screening, nitrogen, cover and relative income. See the [P23 source audit](p23_changes.md). |

## Limitations

These are illustrative point estimates, not field boundaries or management records. Kansas irrigation supply is set to 0, the 2019 spring NDVI peak over mapped fallow is unresolved, Telangana's second season is tentative, and Makueni cropland remains unverified. POWER root-zone wetness and SoilGrids properties are modeled estimates. The app does not directly measure soil nitrogen or soil organic carbon. Relative income, rainfall uncertainty, simplified erosion, season windows and crop choices need local validation. Scenario intervals and win percentages reflect the specified model and assumptions, not calibrated forecast probabilities. See [decisions](decisions.md), [methods](scoring.md), and [citation audit](citation_audit.md).

## AI-assistance statement

**Placeholder for the team's wording:** “We used AI assistance for [describe coding, analysis, writing and testing tasks]. Team members reviewed [describe specific outputs and source checks] and take responsibility for the submitted work.” Replace this text before submission.
