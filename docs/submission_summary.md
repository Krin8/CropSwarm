# CropSwarm submission summary

## Summary (150 words)

CropSwarm is an offline decision-support prototype that helps farmers compare crop rotations at three illustrative locations: Kansas, Telangana, and Makueni. For each location it preserves a baseline and offers four alternative strategies, explaining evidence, benefits, risks, and information gaps. NASA POWER weather, Terra MODIS vegetation, and SRTM terrain inform seasonal diagnostics and mechanistic scores alongside soil estimates, crop parameters, and farmer priorities. Rule-based constraints screen proposed rotations; exact enumeration checks ant-colony search results. Seeded scenario draws display ranges, win percentages, regret, and sensitivity rather than a single promised outcome. The app tags data sources on metrics and keeps conflicting evidence and baseline violations in view. Kansas is modeled as rainfed; its spring vegetation peak over mapped fallow remains unexplained. Telangana's second season is tentative, and Makueni cropland is unverified. All points, management assumptions, crop values, and indices are illustrative and need local validation. Farmers and local experts retain the decision.

## Data actually used

| Provider | Dataset | Role in results |
|---|---|---|
| NASA | [POWER](data_pipeline.md) corrected precipitation, temperature, radiation, humidity and modeled root-zone wetness | Daily weather was cached. Corrected precipitation and temperature feed seasonal diagnostics, stress indicators and scenario scoring. Modeled root-zone wetness informs the climate assessment. |
| NASA | [GPM IMERG via POWER](data_pipeline.md) | Used in the climate assessment’s rainfall agreement check against POWER corrected precipitation on matching UTC dates. That diagnostic is its only role in the results. |
| NASA | [Terra MODIS MOD13Q1 NDVI](data_pipeline.md) | Vegetation seasonality, low-greenness window screening, and the P15 and P19 historical comparisons. |
| NASA | [MODIS MCD12Q1 land cover](decisions.md) | Land-cover screening, including the grassland flag at the illustrative Makueni point. |
| NASA / NGA | [SRTM](data_pipeline.md) through OpenTopoData | Terrain slope proxy in the erosion score. |
| Non-NASA | [ISRIC SoilGrids](api_status.md) | Gridded soil texture and organic-carbon estimates. |
| Non-NASA | [USDA SSURGO](api_status.md) | Kansas soil map units and estimated soil water capacity. |
| Non-NASA | [USDA NASS Cropland Data Layer](decisions.md) | Mapped Kansas crop history and the P15 crop identity input. |
| Non-NASA | [USDA NASS Quick Stats](backtest.md#p20-yield-back-test) | Finney County winter wheat and sorghum yields for P20. |
| Non-NASA | [ICRISAT district yields](backtest.md#p20-yield-back-test) | Historical Warangal kharif rice yields from the public study archive for P20. |
| Non-NASA | [Crop catalog and assumptions](crops.md) | Indicative crop water need, sourced botanical families and locally unverified values for crop climate screening, nitrogen, cover and relative income. See the [P23 source audit](p23_changes.md). |

## Limitations

SMAP, ECOSTRESS, GRACE, Landsat and ERA5 were unused. The historical comparisons check NASA input consistency and associations with county or district yields. Rotation recommendations still need field validation.

The [What to check first panel](sensitivity.md) ranks which assumptions move the modeled score and ranking under specified ranges. Its priorities depend on the reference farm and preset. The [Opportunity windows panel](opportunity_windows.md) screens low-greenness spans against crop length and historical weather. None of the screened crops passed at the reference cutoff. Kansas low greenness may reflect winter-wheat dormancy. Field availability remains unknown.

These are illustrative point estimates, not field boundaries or management records. Kansas irrigation supply is set to 0, the 2019 spring NDVI peak over mapped fallow is unresolved, Telangana's second season is tentative, and Makueni cropland remains unverified. POWER root-zone wetness and SoilGrids properties are modeled estimates. The app does not directly measure soil nitrogen or soil organic carbon. Relative income, rainfall uncertainty, simplified erosion, season windows and crop choices need local validation. Scenario intervals and win percentages describe the modeled draws under the specified assumptions. See [decisions](decisions.md), [methods](scoring.md), and [citation audit](citation_audit.md).

## AI-assistance statement

**Placeholder for the team's wording:** “We used AI assistance for [describe coding, analysis, writing and testing tasks]. Team members reviewed [describe specific outputs and source checks] and take responsibility for the submitted work.” Replace this text before submission.
