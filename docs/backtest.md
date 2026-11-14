# Historical back-test: does modeled stress move with vegetation?

This is a **descriptive check**, not a crop-yield validation. We fixed the existing scoring inputs and compared modeled crop-window water deficit and heat days with observed, QA-filtered MODIS NDVI peak and amplitude for 2019–2023. No parameters were tuned to improve these results. The farm points and crop parameters are illustrative; validate locally.

The [Kansas chart](charts/backtest_us_high_plains_b.svg), [Telangana chart](charts/backtest_telangana_a.svg), and [Makueni chart](charts/backtest_kenya_makueni_north.svg) show deficit share against NDVI peak. The app's **Validation** panel shows the same interactive plots and all four correlation pairs per season. The [Kansas](../data/processed/backtest_us_high_plains_b.json), [Telangana](../data/processed/backtest_telangana_a.json), and [Makueni](../data/processed/backtest_kenya_makueni_north.json) JSON files include every year, crop, season, source tag and statistic.

## All correlations across P15, P19 and P20

The back-tests check consistency between NASA weather and vegetation inputs and between modeled stress and county or district yields. Rotation recommendations still need field validation. All comparisons are shown below, including those with unavailable estimates, weak or opposite signs, and intervals that include zero.

| Study | Comparisons | Correlations computed | Bootstrap intervals available | Intervals excluding zero |
|---|---:|---:|---:|---:|
| P15 crop stress and MODIS NDVI | 24 | 12 | 12 | 4 |
| P19 NASA weather and MODIS NDVI | 36 | 36 | 36 | 11 |
| P20 county or district yield | 10 | 10 | 10 | 3 |
| **Total** | **70** | **58** | **58** | **18** |

The totals pool the saved comparisons across all three farms. A correlation counts when Spearman ρ is available. An interval excludes zero only if both full-precision endpoints are strictly positive or strictly negative. The intervals are descriptive and unadjusted for multiple comparisons. Comparisons reuse observations, so the 18 intervals are not independent confirmations. Makueni has no seasonal yield comparison in P20.

## What was compared

- Kansas uses saved USDA CDL point classes: 2019 fallow, 2020 winter wheat, 2021 sorghum, 2022 fallow, 2023 winter wheat. Winter wheat is assigned to the **harvest year** and its climate and NDVI window starts in the previous October. Fallow has no crop water or heat stress indicator. CDL is a mapped class, not verified management.
- Telangana uses the assumed paddy–paddy baseline; Makueni uses the assumed long-rains maize and short-rains bean baseline for each year. Telangana's second season is tentative, and Makueni's exact point is not verified cropland.
- NASA POWER `PRECTOTCORR` and `T2M_MAX` feed the scoring engine's daily water bucket and crop heat threshold. Crop demand, threshold, soil storage and irrigation share retain their existing sources and assumptions. A MODIS composite passes only with good pixel reliability, good or absent detailed QA, and valid NDVI. Each NDVI peak and amplitude requires at least three good composites in the crop window. These screening thresholds and 2019–2023 comparison range are design choices, not empirical calibrations.
- Spearman rank correlation is computed **within each season**, so different crops and windows are not pooled. A fixed-seed, 1,000-draw paired bootstrap provides a descriptive 95% interval. All samples are small (`n < 8`), and intervals are not calibrated confidence statements. Tied heat counts can produce deceptively narrow bootstrap intervals. Directional agreement counts assessable years whose stress and NDVI peak lie on opposite sides of their season medians; ties and fallow are excluded.

## Results

Each cell gives Spearman ρ, the bootstrap interval and paired n. An estimate is unavailable with fewer than three pairs or a constant series. A negative sign is the expected direction if more stress coincides with lower greenness. The numeric model indicators are illustrative and require local validation.

| Farm and season | Water deficit vs NDVI peak | Water deficit vs amplitude | Heat days vs NDVI peak | Heat days vs amplitude | Directionally consistent years |
|---|---|---|---|---|---|
| Kansas cool (wheat) | Unavailable; n=2 | Unavailable; n=2 | Unavailable; n=2 | Unavailable; n=2 | 0 of 0 assessable |
| Kansas warm (sorghum) | Unavailable; n=1 | Unavailable; n=1 | Unavailable; n=1 | Unavailable; n=1 | 0 of 0 assessable |
| Telangana monsoon | Unavailable; n=1 | Unavailable; n=1 | Unavailable; n=1 | Unavailable; n=1 | 0 of 0 assessable |
| Telangana post-monsoon | −0.50 [−1.00, 1.00]; n=3 | −0.50 [−1.00, 1.00]; n=3 | −0.50 [−1.00, 1.00]; n=3 | −0.50 [−1.00, 1.00]; n=3 | 1 of 1 assessable |
| Makueni long rains | −0.40 [−1.00, 1.00]; n=5 | −0.20 [−1.00, 1.00]; n=5 | −0.71 [−1.00, −0.71]; n=5 | −0.71 [−1.00, −0.71]; n=5 | 2 of 3 assessable |
| Makueni short rains | −0.20 [−1.00, 1.00]; n=5 | **+0.90 [+0.11, 1.00]; n=5, wrong sign** | 0.00 [−1.00, 1.00]; n=5 | **+0.95 [+0.75, 1.00]; n=5, wrong sign** | 2 of 3 assessable |

Water deficit and NDVI peak are weakly negatively associated where estimable, with intervals spanning both signs. The positive short-rains amplitude results run against the expected direction. Neither Kansas season nor Telangana monsoon had enough pairs to estimate a correlation. Telangana post-monsoon had three pairs, and all four intervals spanned both signs. The 2019 Kansas spring NDVI peak over CDL-mapped fallow remains unexplained.

## What this does not prove

MODIS NDVI measures vegetation greenness in a mixed point pixel; it does not identify the planted crop, yield, irrigation or management. MODIS and CDL have different footprints and sensor resolutions. The simplified bucket omits local irrigation timing, soil depth and management; the assumed crop identities in India and Kenya may be wrong. Small and QA-sparse samples, multiple comparisons, bootstrap ties and weather confounding prevent a causal or predictive claim. No soil nitrogen or soil organic carbon was directly measured by these data. Consult local records and field experts before using any strategy.

## P19 long-record NASA consistency check

This check asks whether NASA POWER seasonal weather and Terra MODIS vegetation move together from 2001 through 2024. The comparison uses the saved P5 month windows for each point and leaves the crop catalog, irrigation, CDL and scoring engine out of the calculation. It gives a descriptive check of the two NASA products at these locations. Crop model validity, field management, yield and the merits of individual recommendations are outside its scope. All results are illustrative and need local validation.

### Definitions and screening

- **Season dates.** Use the full P5 calendar months and label cross-year windows by their start year. Kansas warm (April–August) and cool (October–June) windows overlap across years and are assessed separately. The Kansas cool window is assumed. Telangana's November–March window is tentative and was inferred in part from MODIS NDVI, which makes this check less independent. Makueni's point is unverified cropland. A season extending into 2025 needs 2025 NDVI and is excluded from these comparisons.
- **NASA POWER daily climate.** Seasonal rainfall is the sum of `PRECTOTCORR`. The rainfall anomaly is seasonal rainfall minus the 1991–2020 mean for the same month window. Deficit is the positive shortfall below that mean, with genuinely above-reference seasons having zero deficit. Anomaly and deficit are related views of the same rainfall, so agreement in both is not independent corroboration. A heat day has `T2M_MAX` strictly above the local 90th percentile of daily maxima pooled across the same reference window. A missing value, including POWER fill `-999`, excludes the affected climate indicator for that season. Each reference uses complete seasons for that variable.
- **NASA Terra MOD13Q1 NDVI.** Reuse the P4 request grid and P15 quality filter. Coverage counts valid numeric NDVI and separately counts QA passes. An incomplete year has one or more missing or invalid NDVI values. For the seasonal calculation, each composite represents its nominal 16-day span, shortened at December 31 and clipped to the P5 window. A season needs all nominal spans to have valid NDVI, at least three QA-passing composites, and QA-passing spans covering at least half its days. Integrated NDVI equals the day-weighted mean of the passing spans times season length, in NDVI × days. This estimates a season total under the assumption that passing spans represent the full window. Peak is the maximum QA-passing NDVI among overlapping spans. A composite straddling a boundary can reflect days outside the window. Missing or rejected values never enter either calculation as zeros.
- **Association.** Spearman ρ uses complete pairs for each comparison, with the existing fixed seed of 42 and 1,000 paired bootstrap draws (offset deterministically by season and comparison). The descriptive 95% intervals resample years individually and do not adjust for temporal dependence or for testing multiple pairs. Samples below eight are small. An association is called strong in the expected direction when signed ρ is at least 0.60 and both interval endpoints are on that side of zero. Opposite sign means the point estimate goes against the expected direction, even if its interval includes zero. Expected signs are positive for rainfall anomaly and negative for deficit and heat days. The reference period, percentile, QA coverage cutoff and reporting cutoffs are design choices fixed before examining P19 results.
- **“Consistent in X of Y.”** Within a season and comparison, count years whose climate and vegetation values fall on the expected sides of their paired medians. Exclude ties at either median. The denominator can therefore be smaller than the Spearman sample size, especially for rainfall deficits with repeated zeros.

MODIS MOD13Q1 observes greenness at 250 m. One pixel can mix crops, weeds and other cover, including vegetation outside the intended farm. Timing, management, irrigation, mixed land cover, and trends can all affect the observed relationships. See the original [P4 pipeline documentation](data_pipeline.md) for source URLs, composite metadata and QA details.

### Annual MODIS coverage

All 24 years have 23 valid NDVI composites at each point. QA accepted 516 of 552 in Kansas, 295 of 552 in Telangana and 345 of 552 in Makueni. The 126 newly retrieved chunks and 90 reused chunks are in the request manifest.

Each cell shows valid NDVI / expected composites, followed by the number passing QA in parentheses. A dagger (†) marks an incomplete record. The full missing-date lists are in the processed files.

| Year | Kansas | Telangana | Makueni |
|---:|---:|---:|---:|
| 2001 | 23/23 (21) | 23/23 (18) | 23/23 (12) |
| 2002 | 23/23 (23) | 23/23 (17) | 23/23 (11) |
| 2003 | 23/23 (23) | 23/23 (18) | 23/23 (16) |
| 2004 | 23/23 (22) | 23/23 (18) | 23/23 (18) |
| 2005 | 23/23 (22) | 23/23 (13) | 23/23 (17) |
| 2006 | 23/23 (22) | 23/23 (14) | 23/23 (15) |
| 2007 | 23/23 (17) | 23/23 (16) | 23/23 (13) |
| 2008 | 23/23 (22) | 23/23 (13) | 23/23 (18) |
| 2009 | 23/23 (19) | 23/23 (13) | 23/23 (14) |
| 2010 | 23/23 (22) | 23/23 (13) | 23/23 (11) |
| 2011 | 23/23 (20) | 23/23 (12) | 23/23 (14) |
| 2012 | 23/23 (22) | 23/23 (14) | 23/23 (17) |
| 2013 | 23/23 (21) | 23/23 (13) | 23/23 (9) |
| 2014 | 23/23 (22) | 23/23 (10) | 23/23 (16) |
| 2015 | 23/23 (23) | 23/23 (9) | 23/23 (14) |
| 2016 | 23/23 (23) | 23/23 (18) | 23/23 (13) |
| 2017 | 23/23 (21) | 23/23 (11) | 23/23 (17) |
| 2018 | 23/23 (23) | 23/23 (10) | 23/23 (11) |
| 2019 | 23/23 (21) | 23/23 (9) | 23/23 (14) |
| 2020 | 23/23 (22) | 23/23 (8) | 23/23 (13) |
| 2021 | 23/23 (23) | 23/23 (6) | 23/23 (16) |
| 2022 | 23/23 (21) | 23/23 (6) | 23/23 (14) |
| 2023 | 23/23 (20) | 23/23 (10) | 23/23 (17) |
| 2024 | 23/23 (21) | 23/23 (6) | 23/23 (15) |

### Seasonal comparison results

- Kansas warm-season heat days and integrated NDVI met the strong-association cutoff (ρ = −0.60, 95% bootstrap interval −0.77 to −0.24, n = 24). They moved in the expected direction in 18 of 24 assessable seasons. The Kansas cool-season relationships were weaker.
- Makueni short-rains integrated NDVI had a strong association with both rainfall anomaly and deficit (ρ = +0.83 and −0.81, n = 8). Both were directionally consistent in 6 of 8 seasons. They represent the same rainfall signal. The long-rains comparisons were weaker and uncertain.
- Four Telangana monsoon estimates had the opposite sign, with only three usable seasons. A degenerate bootstrap interval such as [−1, −1] with three ranks offers little information about stability. All tentative post-monsoon intervals included zero (n = 17).

Each cell shows ρ [95% bootstrap interval], paired n, then the number of directionally consistent years out of assessable years. Bold indicates a strong association in the expected direction. A dagger (†) flags an opposite-sign point estimate. “Unavailable” means there were fewer than three pairs or one series was constant.

| Farm and season | Rain anomaly vs integrated NDVI | Rain anomaly vs peak NDVI | Rain deficit vs integrated NDVI | Rain deficit vs peak NDVI | Heat days vs integrated NDVI | Heat days vs peak NDVI |
|---|---|---|---|---|---|---|
| Kansas warm | +0.46 [+0.04, +0.71]<br>n=24, consistent in 14 of 24 | +0.42 [-0.07, +0.72]<br>n=24, consistent in 14 of 22 | -0.46 [-0.71, -0.04]<br>n=24, consistent in 14 of 24 | -0.36 [-0.70, +0.13]<br>n=24, consistent in 14 of 22 | **-0.60 [-0.77, -0.24]**<br>n=24, consistent in 18 of 24 | -0.58 [-0.82, -0.19]<br>n=24, consistent in 17 of 22 |
| Kansas cool | +0.24 [-0.17, +0.60]<br>n=23, consistent in 12 of 21 | +0.45 [+0.02, +0.73]<br>n=23, consistent in 14 of 22 | -0.14 [-0.51, +0.29]<br>n=23, consistent in 12 of 21 | -0.37 [-0.68, +0.03]<br>n=23, consistent in 14 of 22 | -0.38 [-0.74, +0.12]<br>n=23, consistent in 12 of 21 | -0.47 [-0.77, -0.02]<br>n=23, consistent in 14 of 22 |
| Telangana monsoon | -1.00 [-1.00, -1.00]†<br>n=3, consistent in 0 of 2 | -0.50 [-1.00, +1.00]†<br>n=3, consistent in 0 of 1 | +0.87 [+0.87, +1.00]†<br>n=3, consistent in 0 of 1 | +0.00 [-1.00, +1.00]<br>n=3, consistent in 0 of 0 | +0.87 [+0.87, +1.00]†<br>n=3, consistent in 0 of 1 | +0.00 [-1.00, +1.00]<br>n=3, consistent in 0 of 0 |
| Telangana post monsoon (tentative) | +0.29 [-0.27, +0.72]<br>n=17, consistent in 8 of 15 | +0.23 [-0.27, +0.64]<br>n=17, consistent in 9 of 15 | -0.27 [-0.70, +0.29]<br>n=17, consistent in 8 of 15 | -0.21 [-0.65, +0.26]<br>n=17, consistent in 9 of 15 | -0.13 [-0.66, +0.43]<br>n=17, consistent in 8 of 14 | -0.52 [-0.87, +0.03]<br>n=17, consistent in 11 of 14 |
| Makueni long rains | +0.48 [-0.37, +0.86]<br>n=9, consistent in 4 of 7 | +0.47 [-0.46, +0.89]<br>n=9, consistent in 5 of 7 | -0.44 [-0.85, +0.42]<br>n=9, consistent in 4 of 7 | -0.44 [-0.88, +0.53]<br>n=9, consistent in 5 of 7 | -0.46 [-1.00, +0.47]<br>n=9, consistent in 4 of 7 | -0.47 [-0.95, +0.42]<br>n=9, consistent in 4 of 7 |
| Makueni short rains | **+0.83 [+0.26, +1.00]**<br>n=8, consistent in 6 of 8 | +0.62 [-0.19, +1.00]<br>n=8, consistent in 6 of 8 | **-0.81 [-0.99, -0.22]**<br>n=8, consistent in 6 of 8 | -0.61 [-0.99, +0.21]<br>n=8, consistent in 6 of 8 | -0.40 [-1.00, +0.44]<br>n=8, consistent in 4 of 8 | -0.36 [-1.00, +0.67]<br>n=8, consistent in 4 of 8 |

Per-season observations, all intervals and missing dates are in the [Kansas](../data/processed/nasa_consistency_us_high_plains_b.json), [Telangana](../data/processed/nasa_consistency_telangana_a.json), and [Makueni](../data/processed/nasa_consistency_kenya_makueni_north.json) records. The [request manifest](../data/raw/p4/manifest_p19.json) links each archived MODIS response by path relative to the P4 raw cache.

## P20 yield back-test

This comparison pairs public county or district yield anomalies with modeled water deficit and heat days at the selected NASA POWER point. The yields represent regional averages across farms, varieties and management. The modeled weather and soil represent one illustrative point. Use the results as a check on the direction of the modeled stress indicators and validate the crop and management assumptions locally.

### Access, coverage and boundaries

- **Finney County, Kansas (FIPS 20055).** The point (37.940, −100.670) falls in Finney County. The Quick Stats API requires a key, so this analysis used the public USDA NASS bulk crop file dated November 13, 2026. The extract selects annual county survey yield in bushels per acre, in the Total domain, for winter wheat and grain sorghum in 1990–2024. Non-irrigated records are the primary comparison. All-practice records are shown separately across their own available years and include irrigated farms. Some years have no matching value. These two series overlap and cannot corroborate each other independently. [Census county map](https://www2.census.gov/geo/maps/DC2020/GARM20/GARM2020_ST20_KS.pdf) · [USDA Quick Stats bulk data](https://www.nass.usda.gov/datasets)
- **Historical Warangal district, Telangana.** The direct ICRISAT data portal timed out. The public Maiti et al. study archive supplies 1990–2017 ICRISAT kharif rice yield in kg/ha. The configured point is inside the Warangal polygon in the archive's 1993 district map (IPUMS code 002021). The published Warangal rows join to that polygon. This is the historical district geography, before the 2016 splits and the 2021 Warangal/Hanumakonda reorganization. The study documents the 1993 weather geography and the yield-to-polygon join is reproducible. How the underlying yield observations were apportioned across boundary changes remains unverified. The result covers one historical district, with mixed irrigation and management. [Study methods](https://doi.org/10.1038/s43247-024-01414-7) · [Public data and boundary archive](https://doi.org/10.5281/zenodo.10958118) · [District reorganization](https://cdnbbsr.s3waas.gov.in/s3ec04ddcbe25988981920c872c1787382/uploads/2024/06/2024062539.pdf)
- **Makueni County, Kenya.** The KNBS report verifies maize and bean area and production by county for 2020–2024. These annual totals combine growing seasons. The NDMA long-rains report verifies an individual seasonal assessment, but a comparable year-by-year yield series for the modeled season was not verified. Makueni was skipped and cropland at the point remains unverified. [KNBS report, Annexes 1 and 4](https://www.knbs.or.ke/wp-content/uploads/2025/10/National-Agriculture-Production-Report-2025.pdf) · [NDMA Makueni long-rains assessment](https://knowledgeweb.ndma.go.ke/Content/LibraryDocuments/Makueni_Long_Rains_Assessments20230922085657.pdf)

The [provenance manifest](../data/raw/p20/provenance.json) records the public source URLs, hashes and exact extracts. The repo contains the two small regional extracts. Run `python -m src.yield_backtest` offline to reproduce the processed results and per-year values.

### Fixed analysis

1. Fit a separate ordinary least-squares line against calendar year for each yield series, using all reported observations in 1990–2024. The yield anomaly is observed yield minus the fitted line, in the source units. Each fit uses calendar years, including gaps, and removes a linear trend. Changes in management, pest pressure, varieties and irrigation can still affect those residuals.
2. Use first-of-month P5 onset and the unchanged crop duration, water demand and heat threshold from [crops.csv](../data/crops.csv). Winter wheat starts October 1 of the year before harvest (260 days, 550 mm, above 30 °C). Grain sorghum starts April 1 (105 days, 450 mm, above 38 °C). Kharif paddy starts June 1 (120 days, 575 mm, above 35 °C). The month windows are illustrative. The April sorghum start in particular is the existing P5 warm window and may differ from local planting dates. The dates and thresholds were fixed before inspecting the correlations.
3. The existing daily bucket starts empty, retains rainfall up to the saved soil water capacity and uses the crop's water demand spread evenly across the window. Multiply unmet demand by one minus the farm's assumed irrigation supply fraction (Kansas 0%, Telangana 60%). The Telangana fraction describes the point model and does not measure district irrigation. Heat days count daily maxima strictly above the crop's threshold. A missing daily POWER value, including `-999`, excludes its corresponding indicator. POWER starts in 1991, so 1990 yield and the 1991 winter-wheat harvest are used in their respective trend fits but have no paired weather.
4. Compute Spearman ρ for each stress indicator against yield anomalies, with 1,000 paired bootstrap draws using fixed seeds 42 for water deficit and 43 for heat. The bootstrap resamples observed pairs after fitting the trend. It is descriptive and does not account for serial dependence, trend-fit uncertainty or multiple testing. The analysis uses P19's reporting threshold as a design choice. A strong expected association requires ρ ≤ −0.60 and both interval endpoints below zero. A positive estimate is in the opposite direction. The remaining estimates are weak or uncertain.

### Results

Each cell gives Spearman ρ [95% descriptive bootstrap interval], followed by the paired sample size.

| Yield series | Published years (records) | Modeled water deficit vs yield anomaly | Heat days vs yield anomaly |
|---|---|---|---|
| Finney winter wheat, non-irrigated | 1990–2013 (22) | **−0.61 [−0.87, −0.21], n=20** | −0.38 [−0.78, +0.10], n=20 |
| Finney grain sorghum, non-irrigated | 1990–2007 (18) | −0.20 [−0.67, +0.40], n=17 | −0.32 [−0.70, +0.22], n=17 |
| Finney winter wheat, all practices | 1990–2022 (29) | **−0.62 [−0.81, −0.32], n=27** | −0.42 [−0.73, +0.01], n=27 |
| Finney grain sorghum, all practices | 1990–2020 (26) | −0.41 [−0.76, +0.06], n=25 | −0.51 [−0.75, −0.15], n=25 |
| Historical Warangal kharif rice, district aggregate | 1990–2017 (28) | −0.32 [−0.59, +0.05], n=27 | −0.35 [−0.66, +0.03], n=27 |

Only winter wheat water deficit reached the strong-association cutoff, in both overlapping practice series. The all-practice sorghum heat estimate stayed below zero across its interval but fell short of that cutoff. The primary non-irrigated sorghum and district rice intervals included zero for both indicators. All point estimates were in the expected negative direction. These associations cannot establish the yield of an individual farm, explain why a particular year was poor, or establish the benefit of rotating crops. The app's **Yield back-test** section uses the same results. [Kansas data](../data/processed/yield_backtest_us_high_plains_b.json) · [Telangana data](../data/processed/yield_backtest_telangana_a.json) · [Makueni disposition](../data/processed/yield_backtest_kenya_makueni_north.json)
