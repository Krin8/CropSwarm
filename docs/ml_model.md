# P25 learned climate-yield check

This study asks whether cached historical weather helps explain Kansas county winter-wheat yields beyond a county mean or time trend. It is separate from CropSwarm's rotation scores and the P15, P19 and P20 correlation tally. All feature assumptions and results are illustrative and need local validation.

## Data and exclusions

- **Yield.** Used the exact USDA NASS Quick Stats bulk crops file archived for P20. Its SHA-256 matches the P20 manifest. The extraction selects Kansas county survey records for annual winter-wheat yield in bushels per acre, total domain, 1990–2024. A valid published non-irrigated value takes precedence within each county-year. When that value is absent, the published all-practice value is used and flagged. This makes the combined target sensitive to differences in irrigation mix and reporting. A non-irrigated-only 20-year eligibility screen would retain 31 counties and 696 rows. That count describes source coverage. All model results below use the preferred-with-fallback dataset. [P20 extract provenance](../data/raw/p20/provenance.json) · [P25 provenance](../data/raw/p25/provenance.json)
- **Selection.** Of 5,415 extracted rows, exclude 123 aggregate “other county” entries without a matching Census county FIPS, and discard 2,041 all-practice rows superseded by non-irrigated values. This leaves 3,251 county-year rows across 105 counties. Doniphan and Wyandotte each have 18 valid years, below the 20-year minimum. All 103 eligible counties pass the same 20-year complete-climate minimum. The final dataset has **3,215 county-years**, including **2,005 non-irrigated** and **1,210 all-practice** records. The requested period ends in 2024. The recovered file has no qualifying 2024 observations. Actual coverage is 1990–2023. [County-by-county coverage](../data/processed/climate_yield_coverage.json)
- **Climate locations.** Matched NASS records to the Census TIGERweb Kansas county table by five-digit FIPS. Used the published `CENTLAT` and `CENTLON` for the January 1, 2026 geography. These fixed centroids are coarse proxies for county weather and can sit away from wheat-growing areas. POWER values are gridded. Neighboring points and shared weather years can still carry related information. [Census county table](https://tigerweb.geo.census.gov/tigerwebmain/Files/acs26/tigerweb_acs26_county_ks.html) · [Archived centroids](../data/raw/p25/kansas_centroids.csv)
- **POWER cache.** All 206 county chunks completed with HTTP 200. The AG daily point requests cover 1989–2024 in two 18-year chunks per county, on local solar days. The manifest records exact parameters, response status, timestamps and compressed raw-response hashes. Complete chunks are reused and failed chunks can be resumed with the existing bounded retries. The feature builder treats fill values such as −999 as missing and excludes incomplete seasonal inputs. The input manifest preserves request provenance even if the uncompressed cache is discarded. [NASA POWER daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) · [Request manifest](../data/raw/p25/power_manifest.json)
- **MODIS.** Skipped. The committed QA-screened P19 NDVI series are for three reference farm pixels, with no adequate county-centroid series or county wheat mask. No MODIS data were downloaded for P25.

## Features and training

Use the same Kansas winter-wheat dates and crop values as P20. Start on October 1 of the year before harvest and take the 260 days specified in the crop catalog. Those dates and crop parameters remain illustrative. This analysis does not fit dates to yield. Calculate seasonal corrected rainfall, modeled water deficit, days above the catalog daily maximum threshold of 30 °C, mean daily surface shortwave radiation and mean air temperature. Use the existing daily bucket with catalog water need of 550 mm, initially empty, with no irrigation. Its fixed 60.2 mm storage proxy transfers the Kansas illustrative site's SSURGO-mapped top 30 cm storage to all counties as an explicit design assumption. The modeled deficit is a standardized indicator. It does not recover actual field water use or county irrigation. [Crop catalog](crops.md) · [P20 fixed analysis](backtest.md#fixed-analysis) · [P25 settings](../config/climate_yield.json)

Compare four methods on the same held-out rows. County mean and linear trend use only training yields for that county. For a held-out county with no training history, use the equal-county average of the other counties' means or fitted trends. The two climate models fit deviations from the training-fold trends, then add the applicable trend back to predict actual yield in bu/acre. Held-out yields never fit a trend, scaler or model. The climate model sees only the five weather features. The linear trend is a descriptive adjustment for slow changes. Management, crop genetics, practices and disclosure patterns can still explain residuals.

Leave-one-year-out removes all rows from the same harvest year and uses the earlier and later years available in the archive. This is historical cross-validation and does not simulate forecasting a future year. Leave-one-county-out removes all rows from the county. The remaining counties still provide information about the same years. Spatially and temporally independent transfer may be harder than either test.

For each of the 34 held-out years and 103 held-out counties, the inner three-fold group split matches the outer split's group type. It refits the trends and learns any scaling on inner training rows. Choose by pooled inner validation RMSE. The ridge grid uses three `alpha` values (0.1, 1 and 10). The random forest grid uses minimum leaf sizes 5 and 20 with 48 trees. Random seeds, candidate grids and tie rules are recorded design choices. In total there are **two baselines, two learned models and five learned configurations**, with 2,055 inner learned fits and 274 outer learned refits. The reporting compares both models without selecting a winner for deployment. Preprocessing, fold assignment and model fits are deterministic under the pinned dependencies.

## Results

R², RMSE and Spearman are pooled over **3,215 held-out county-years per model and scheme**. Intervals are descriptive 95% paired block-bootstrap intervals from 1,000 samples of the held-out groups, resampling years for the first scheme and counties for the second. The procedure reuses out-of-fold predictions and does not refit the models for each draw. It leaves residual dependence across the other grouping dimension, training overlap and full refit variability unaccounted for.

| Split | Model | R² [95% interval] | RMSE, bu/acre [95% interval] | Spearman ρ [95% interval] |
|---|---|---:|---:|---:|
| Hold out year | County mean | 0.051 [-0.047, 0.113] | 10.819 [9.702, 12.034] | 0.228 [0.126, 0.330] |
| Hold out year | Linear trend | 0.122 [0.005, 0.201] | 10.407 [9.291, 11.565] | 0.354 [0.232, 0.454] |
| Hold out year | Ridge | 0.308 [0.190, 0.389] | 9.243 [8.237, 10.401] | 0.556 [0.452, 0.634] |
| Hold out year | Random forest | 0.285 [0.137, 0.386] | 9.393 [8.341, 10.526] | 0.554 [0.450, 0.636] |
| Hold out county | County mean | -0.002 [-0.007, -0.002] | 11.120 [10.758, 11.484] | -0.317 [-0.354, -0.278] |
| Hold out county | Linear trend | 0.081 [0.058, 0.100] | 10.647 [10.267, 11.021] | 0.290 [0.253, 0.328] |
| Hold out county | Ridge | 0.285 [0.261, 0.309] | 9.391 [9.030, 9.776] | 0.545 [0.519, 0.571] |
| Hold out county | Random forest | 0.539 [0.502, 0.573] | 7.541 [7.154, 7.976] | 0.735 [0.709, 0.760] |

Both climate models lowered pooled RMSE compared with the trend baseline in both schemes. Ridge had the lowest point RMSE when holding out a year. Random forest had the lowest point RMSE when holding out a county. The paired differences below summarize the trend comparisons, with negative values favoring the climate model. In the county-held-out mean baseline, each county receives a slightly different average of the other counties. Its negative pooled rank correlation partly reflects the exclusion of that county's mean from its own reference.

| Split | Model | RMSE change from linear trend, bu/acre [95% interval] |
|---|---|---:|
| Hold out year | Ridge | -1.164 [-1.691, -0.654] |
| Hold out year | Random forest | -1.015 [-1.519, -0.509] |
| Hold out county | Ridge | -1.256 [-1.425, -1.092] |
| Hold out county | Random forest | -3.106 [-3.384, -2.819] |

## Interpretation

Permutation importance measures the increase in RMSE after shuffling a feature within each held-out fold, with 10 fixed-seed permutations. The learned predictions and baseline trend stay fixed. A negative value would indicate that the shuffle lowered error. Related rainfall and moisture features are dependent, so shuffling one of them may create combinations absent from the data.

| Split | Model | Highest-importance feature | RMSE increase, bu/acre | Second feature | RMSE increase, bu/acre |
|---|---|---|---:|---|---:|
| Hold out year | Ridge | Modeled water deficit (mm) | 5.877 | Season rainfall (mm) | 4.939 |
| Hold out year | Random forest | Modeled water deficit (mm) | 1.658 | Mean daily solar radiation (MJ/m²/day) | 0.838 |
| Hold out county | Ridge | Modeled water deficit (mm) | 4.144 | Season rainfall (mm) | 2.951 |
| Hold out county | Random forest | Modeled water deficit (mm) | 3.448 | Mean daily solar radiation (MJ/m²/day) | 1.580 |

The models' fitted yield anomaly generally declines over higher modeled water deficit. For example, the held-out-county random forest's partial dependence moves from about +5.8 to −7.0 bu/acre between the lowest and highest plotted training-fold quantiles. A curve replaces the selected feature with the 10th, 30th, 50th, 70th and 90th training-fold percentiles, averages the model's predicted anomalies across held-out rows, then pools those estimates by fold row count. The horizontal positions are the corresponding average training-fold feature values. Correlated weather inputs can make some combinations unrealistic. The panel provides all five feature curves per learned model and split.

The county models describe **associations in reported county averages**. The outcomes combine farms, varieties, practices and the noted irrigation reporting fallback. The study cannot establish causation, field outcomes or the value of a crop rotation. The app retains both validation schemes, both baselines and both learned models.

## Reproduce

From a checkout with the pinned requirements, run:

```sh
python -m src.county_yield_data
python -m src.climate_yield
```

The first command restores raw chunks from the committed compressed archive when needed, then writes the feature and coverage files. Add `--fetch` to resume missing POWER responses and `--archive` to archive newly fetched replies. `--extract-bulk` can regenerate the small source extract from the original P20 gzip. `--centroid-html data/raw/p25/census_kansas_counties.html` can regenerate the centroid CSV. Model predictions, intervals, selected inner settings and interpretations are saved in [model results](../data/processed/climate_yield_model.json) and [pooled predictions](../data/processed/climate_yield_predictions.csv). The app reads the results JSON offline. No models train during app use.

The fixture tests cover source-practice selection, POWER fill values and cache restoration, feature windows, disjoint inner and outer folds, and fixed-seed predictions and intervals. Changing only held-out yields cannot change training trends, the chosen settings or predictions. The app integration test covers both baseline rows, learned-model rows and interpretation controls.

## P27 validity checks

P27 adds blocked spatial validation and repeats the analysis on the two source practices separately. The original P25 pooled year and county rows above remain the reference. In the pooled held-out-year test, the county-mean baseline had RMSE **10.819 bu/acre**, R² **0.051** and Spearman **0.228**. The original table gives its intervals alongside the trend, ridge and random forest.

### Spatial blocks and practice subsets

Use the USDA NASS Quick Stats agricultural statistics districts from the same cached source file as P25. The original `ASD_CODE` and `ASD_DESC` fields give one district per county. A FIPS join assigns all 103 analyzed counties to nine USDA districts. The assignments were reconciled with the 5,415 source rows in the P25 extract before the join. [District lookup](../data/raw/p27/kansas_reporting_districts.csv) · [Cached source provenance](../data/raw/p27/provenance.json)

Hold out every county-year from one district at a time. Tune within the training districts using the original three-fold grouped inner cross-validation and model grid. A held-out district uses the equal-county average of the training-county trend or mean as its baseline. Use 1,000 paired bootstrap draws over the same whole groups used as outer holdouts. District intervals depend on nine blocks. Neighboring counties can still straddle a district boundary, and spatial folds still allow training on other locations in the same harvest years.

Use all **2,005 reported non-irrigated rows** across 103 counties and 30 years (1990–2019), and all **1,210 all-practice fallback rows** across 103 counties and 16 years (2008–2023). These are fixed subsets of the P25 analytic sample. The fallback label means that the selected county-year had no valid non-irrigated record. All-practice averages can include irrigated wheat. The subsets differ in years, reporting, and management mix. Differences between their metrics cannot be attributed to irrigation. Each subset is fitted independently for all three split types using the original P25 settings.

### Results by subset and split

**Headline · pooled USDA district holdout.** Across 3,215 county-years and nine USDA reporting districts, RMSE was 11.202 bu/acre for county mean, 10.758 for linear trend, 9.562 for ridge and 9.034 for random forest. The models describe weather–yield associations in Kansas county averages. Crop rotation quality is outside this evaluation. The app opens on the district split and keeps the year and county splits available.

Figures use pooled held-out rows and descriptive 95% block-bootstrap intervals. All models and baselines are shown, including negative values. R² and Spearman are unitless. RMSE is in bu/acre.

| Yield rows | Split | Model | RMSE [95% interval] | R² [95% interval] | Spearman ρ [95% interval] |
|---|---|---|---:|---:|---:|
| All P25 rows | USDA district | County mean | 11.202 [10.502, 12.014] | -0.017 [-0.059, -0.007] | -0.238 [-0.295, -0.126] |
| All P25 rows | USDA district | Linear trend | 10.758 [10.044, 11.679] | 0.062 [-0.013, 0.113] | 0.267 [0.162, 0.373] |
| All P25 rows | USDA district | Ridge | 9.562 [8.972, 10.249] | 0.259 [0.188, 0.301] | 0.516 [0.464, 0.573] |
| All P25 rows | USDA district | Random forest | 9.034 [8.384, 9.631] | 0.339 [0.260, 0.395] | 0.594 [0.530, 0.656] |
| Reported non-irrigated | Year | County mean | 10.660 [9.120, 12.066] | 0.023 [-0.148, 0.111] | 0.181 [0.044, 0.327] |
| Reported non-irrigated | Year | Linear trend | 11.008 [9.044, 12.989] | -0.042 [-0.378, 0.142] | 0.180 [-0.022, 0.356] |
| Reported non-irrigated | Year | Ridge | 9.296 [7.616, 11.267] | 0.257 [-0.052, 0.443] | 0.537 [0.349, 0.679] |
| Reported non-irrigated | Year | Random forest | 9.923 [8.013, 11.837] | 0.153 [-0.158, 0.360] | 0.481 [0.312, 0.615] |
| Reported non-irrigated | County | County mean | 10.800 [10.466, 11.175] | -0.003 [-0.010, -0.002] | -0.323 [-0.363, -0.278] |
| Reported non-irrigated | County | Linear trend | 10.843 [10.468, 11.248] | -0.011 [-0.034, 0.005] | 0.066 [0.017, 0.115] |
| Reported non-irrigated | County | Ridge | 9.019 [8.634, 9.439] | 0.301 [0.269, 0.331] | 0.567 [0.540, 0.596] |
| Reported non-irrigated | County | Random forest | 6.932 [6.522, 7.364] | 0.587 [0.552, 0.620] | 0.763 [0.739, 0.785] |
| Reported non-irrigated | USDA district | County mean | 10.889 [10.244, 11.657] | -0.019 [-0.063, -0.009] | -0.240 [-0.296, -0.119] |
| Reported non-irrigated | USDA district | Linear trend | 10.980 [10.252, 11.894] | -0.036 [-0.119, 0.000] | 0.016 [-0.096, 0.164] |
| Reported non-irrigated | USDA district | Ridge | 9.213 [8.392, 10.092] | 0.270 [0.206, 0.331] | 0.540 [0.484, 0.599] |
| Reported non-irrigated | USDA district | Random forest | 8.303 [7.542, 8.983] | 0.407 [0.323, 0.489] | 0.643 [0.579, 0.707] |
| All-practice fallback | Year | County mean | 10.411 [9.276, 11.481] | -0.009 [-0.172, 0.067] | 0.165 [0.082, 0.263] |
| All-practice fallback | Year | Linear trend | 10.609 [9.529, 11.623] | -0.048 [-0.331, 0.091] | 0.277 [0.169, 0.378] |
| All-practice fallback | Year | Ridge | 9.846 [8.808, 10.823] | 0.097 [-0.157, 0.257] | 0.459 [0.342, 0.552] |
| All-practice fallback | Year | Random forest | 9.607 [8.704, 10.442] | 0.140 [-0.074, 0.273] | 0.499 [0.405, 0.576] |
| All-practice fallback | County | County mean | 10.382 [9.875, 10.911] | -0.004 [-0.015, -0.003] | -0.370 [-0.415, -0.315] |
| All-practice fallback | County | Linear trend | 10.126 [9.589, 10.673] | 0.045 [0.013, 0.074] | 0.203 [0.142, 0.267] |
| All-practice fallback | County | Ridge | 9.154 [8.635, 9.661] | 0.220 [0.177, 0.258] | 0.488 [0.444, 0.530] |
| All-practice fallback | County | Random forest | 8.147 [7.572, 8.712] | 0.382 [0.326, 0.435] | 0.639 [0.594, 0.685] |
| All-practice fallback | USDA district | County mean | 10.430 [9.541, 11.437] | -0.013 [-0.041, -0.007] | -0.191 [-0.238, -0.088] |
| All-practice fallback | USDA district | Linear trend | 10.316 [9.355, 11.491] | 0.009 [-0.087, 0.078] | 0.173 [0.021, 0.340] |
| All-practice fallback | USDA district | Ridge | 9.423 [8.636, 10.309] | 0.173 [0.092, 0.242] | 0.435 [0.350, 0.522] |
| All-practice fallback | USDA district | Random forest | 9.308 [8.323, 10.429] | 0.193 [0.021, 0.333] | 0.484 [0.362, 0.631] |

In the pooled district split, ridge and random forest both improve on the trend baseline, by about 1.20 and 1.72 bu/acre respectively. The paired 95% RMSE intervals exclude zero for both improvements and for both learned models in each practice-only district split. The same district restriction raises RMSE relative to the corresponding county split. These conclusions are conditional on this sample and model.

### Leakage audit

The P25 and P27 outer splits exclude the named group before fitting. Yield detrending is estimated from the remaining rows. Inner selection receives only the outer training rows, groups by the same holdout key, and refits detrending and feature scaling on each inner training split. Ridge uses a scaler inside its fit pipeline. The forest uses the original unscaled features. Interpretation uses held-out values after fitting. Neither held-out labels nor features enter fitting or selection. No leakage was found under these split definitions.

Tests record exactly which fixture rows reach detrending, scaler fitting and each learned model fit, and verify that those rows come from the appropriate outer or inner training fold. Changing held-out yields leaves predictions and selected configurations unchanged. The group-overlap check rejects an invalid fold. Year holdouts and spatial holdouts are separate evaluations. A year split can include the same county in other years, and a county or district split can include the same year in other locations.

### Reproduce offline

Run `python -m src.climate_yield_validity` using the committed P25 feature file and P27 district lookup. The command writes only the new P27 reports and their held-out predictions. Use `--cohort` to rebuild a single subset. The app's **Learned climate-yield check** keeps the original P25 results under **All P25 rows**, and offers the district split and both practice subsets in the same panel.

[All P25 rows, district results](../data/processed/climate_yield_validity_pooled.json) · [Non-irrigated results](../data/processed/climate_yield_validity_non_irrigated.json) · [All-practice fallback results](../data/processed/climate_yield_validity_all_practices.json)

## P31 India replication archive screen

P31 stopped at the crop-selection gate fixed in the [preregistered plan](p31_plan.md), commit `ad97274`. The cached [Maiti et al. archive](https://doi.org/10.5281/zenodo.10958118) identifies its only crop series as kharif monsoon rice. Its inventory contains `Data.csv` and `Shapefile.rar`. Both files match the SHA-256 values recorded independently in [P20 provenance](../data/raw/p20/provenance.json). The deposited CSV contains rice area, production, yield, a column named `RICE.SHARE.IN.TOTAL..Percent.` and weather fields. The deposit does not define that share as crop irrigation. It supplies no identified crop-specific irrigated-area numerator or rainfed designation. Rainfed dominance remains unverified.

| Candidate | Yield years available | Districts in the CSV | Districts with at least 20 positive, unique yield years and a historical map match | District-years in those districts | Archived state labels in those districts | Irrigation evidence | Crop selection |
|---|---|---:|---:|---:|---:|---|---|
| Kharif rice | 1990–2017 | 384 | 365 | 10,105 | 20 | Irrigated share unavailable. Rainfed dominance unverified. | Ineligible under the preregistration |

The crop file contains 10,279 rows with finite positive rice yields and no duplicate archival district-years. The screen joins `Sh_Dist_code` to `IPUM1993` and checks `FID_1`, state and district attributes. All 384 district identities with yields match the archived polygon attributes. The polygon geography is the archive's historical 1993 mapping. Archived state labels are the labels in its crosswalk. Each can differ from present-day geography. How underlying yields were aggregated through splits remains unverified. The series represents reported district averages with unknown irrigation mix, varieties and management.

### Districts excluded by yield coverage

All 19 had fewer than the required 20 years. The remaining 365 met the yield and geography screen only. No districts advanced to centroid-weather processing.

| Archived state | Archived district | IPUM1993 | Valid yield years |
|---|---|---|---:|
| Bihar | Saharsa | `005021` | 2 |
| Gujarat | Amreli | `007005` | 9 |
| Gujarat | Bans Kantha | `007008` | 9 |
| Gujarat | Bhavnagar | `007004` | 14 |
| Gujarat | Junagadh | `007006` | 13 |
| Haryana | Rewari | `008011` | 19 |
| Madhya Pradesh | Indore | `013023` | 9 |
| Madhya Pradesh | Mandsaur | `013016` | 11 |
| Madhya Pradesh | Ujjain | `013018` | 7 |
| Maharashtra | Buldana | `014022` | 15 |
| Maharashtra | Jalna | `014016` | 17 |
| Rajasthan | Jaipur | `021009` | 14 |
| Rajasthan | Jalor | `021018` | 1 |
| Rajasthan | Jhunjhuna | `021004` | 1 |
| Rajasthan | Jodhpur | `021014` | 1 |
| Rajasthan | Pali | `021016` | 12 |
| Rajasthan | Sikar | `021010` | 1 |
| Rajasthan | Tonk | `021012` | 15 |
| Telangana | Hyderabad | `002016` | 4 |

### Evaluation and transfer disposition

No district centroids were calculated, no new POWER requests were made and no P31 models or configurations were fitted. The planned P25/P27 mean and trend baselines, ridge and random forest, five learned configurations, and year/state holdouts remain unevaluated for India. RMSE, R², Spearman, bootstrap intervals and relative performance are unavailable for this replication. Fixed centroids would have been coarse climate proxies even if a crop qualified.

**Kansas-to-India transfer was skipped.** Kansas winter wheat starts in the previous October and uses its catalog winter-wheat duration. The only India archive series is kharif monsoon rice and uses a different season and crop. The existing historical Warangal rice correlations remain a separate analysis. [P20 protocol](backtest.md#p20-yield-back-test)

The [saved screen](../data/processed/climate_yield_india_screen.json) lists candidate metadata, archived hashes and the status of every district. To reproduce offline from the committed [archive files](../data/raw/p31/), run `python -m src.india_yield_screen` with the pinned requirements. The screen verifies the original archive hashes and uses a compressed, hash-checked copy of its original dBASE attributes. It writes only the P31 screen. The app displays this disposition under Validation. P25/P27 results and the seasonal scoring engine retain their original files.

## P32 cross-state winter-wheat transfer

The [preregistration](p32_plan.md) was committed as `7400972` before opening the target-state data. All tests use the fixed P25/P27 winter-wheat recipe and the same model and hyperparameter grids. Kansas keeps its existing retained cohort of 103 counties and 3,215 county-years.

### Target yield screen

The [P32 extract](../data/raw/p32/quickstats_targets.csv) uses the cached P20 public USDA NASS bulk snapshot. The [provenance](../data/raw/p32/provenance.json) records the snapshot and extract hashes. The preferred records are the reported non-irrigated yields. Selected all-practice records fill gaps and may include irrigated wheat.

| State | Source rows | Aggregate “Other counties” rows removed | All-practice rows superseded | Counties with valid yields | Counties with at least 20 yield years | Eligible USDA districts | County-years before climate screen | Non-irrigated / fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Nebraska | 3,680 | 199 | 1,420 | 91 | 59 | 8 | 1,744 | 1,165 / 579 |
| Oklahoma | 2,741 | 181 | 473 | 75 | 58 | 8 | 1,800 | 421 / 1,379 |

Both yield-only cohorts span 1990–2023. The [saved inventory](../data/processed/climate_yield_transfer_yield_inventory.json) lists all 32 Nebraska and 17 Oklahoma counties excluded for fewer than 20 valid years. Yield coverage precedes the independent county geography join and the complete-weather screen.

### Weather coverage and final cohorts

After the yield-only screen, the authorized [Nebraska](https://tigerweb.geo.census.gov/tigerwebmain/Files/acs26/tigerweb_acs26_county_ne.html) and [Oklahoma](https://tigerweb.geo.census.gov/tigerwebmain/Files/acs26/tigerweb_acs26_county_ok.html) Census TIGERweb ACS26 tables supplied the published January 1, 2026 `CENTLAT` and `CENTLON` values. All USDA county identifiers reconciled by FIPS. The [archive provenance](../data/raw/p32/provenance.json) records both table hashes. 234 of 234 requested NASA POWER chunks were complete. All 117 yield-eligible counties cleared the climate screen. Nebraska lost 11 county-years because a required daily radiation value was missing. Oklahoma retained all 1,800 eligible county-years. The feature builder reused the Kansas winter-wheat window and crop inputs.

| State | Retained counties | USDA districts | Paired county-years | Harvest years | Non-irrigated / fallback |
| --- | --- | --- | --- | --- | --- |
| Kansas | 103 | 9 | 3,215 | 1990–2023 | 2,005 / 1,210 |
| Nebraska | 59 | 8 | 1,733 | 1990–2023 | 1,154 / 579 |
| Oklahoma | 58 | 8 | 1,800 | 1990–2023 | 421 / 1,379 |

The Nebraska and Oklahoma feature coverage and request manifests list every county and date range. Centroid weather is gridded and can miss field exposures. County yields combine management and varieties. The all-practice fallback is more frequent in Oklahoma and can include irrigated wheat. The tests describe weather–yield associations in county averages. Rotation quality still needs field evidence. [Nebraska coverage](../data/processed/climate_yield_transfer_31_coverage.json) · [Oklahoma coverage](../data/processed/climate_yield_transfer_40_coverage.json) · [Nebraska POWER manifest](../data/raw/p32/power_31_manifest.json) · [Oklahoma POWER manifest](../data/raw/p32/power_40_manifest.json)

### Results

The reporting unit is bushels per acre. Every result uses the same held-out rows for all four methods. The brackets show paired descriptive 95% bootstrap intervals. Target-state estimates resample USDA reporting districts. The pooled estimate resamples its three held-out states. The source-only baselines use the mean or trend of training counties, with the unchanged P27 equal-county fallback for unseen counties. The comparison against own-state baselines uses one USDA district held out at a time within the target state. Those reference fits may use years shared with the held-out district from other districts. No yields from the evaluated state enter the transfer model, scaling, trend fitting or tuning. Shared years can occur across states.

| Evaluation | County-years | Model | RMSE, bu/acre | R² | Spearman ρ |
| --- | --- | --- | --- | --- | --- |
| Nebraska district holdout | 1,733 | County mean | 11.274 [10.892, 11.612] | -0.047 [-0.206, -0.019] | -0.277 [-0.396, -0.043] |
| Nebraska district holdout | 1,733 | Linear trend | 10.161 [9.133, 11.407] | 0.150 [-0.178, 0.300] | 0.405 [0.249, 0.589] |
| Nebraska district holdout | 1,733 | Ridge | 9.861 [8.994, 10.879] | 0.199 [-0.078, 0.333] | 0.457 [0.344, 0.599] |
| Nebraska district holdout | 1,733 | Random forest | 9.090 [8.083, 10.164] | 0.320 [0.071, 0.437] | 0.576 [0.453, 0.678] |
| Oklahoma district holdout | 1,800 | County mean | 9.200 [8.515, 10.180] | -0.025 [-0.102, -0.014] | -0.253 [-0.305, -0.103] |
| Oklahoma district holdout | 1,800 | Linear trend | 8.985 [8.351, 9.831] | 0.022 [-0.131, 0.076] | 0.168 [0.051, 0.299] |
| Oklahoma district holdout | 1,800 | Ridge | 7.863 [7.041, 8.954] | 0.251 [0.104, 0.349] | 0.524 [0.436, 0.618] |
| Oklahoma district holdout | 1,800 | Random forest | 7.716 [6.726, 8.873] | 0.279 [0.145, 0.386] | 0.545 [0.447, 0.648] |
| Kansas → Nebraska | 1,733 | County mean | 11.331 [10.435, 11.929] | -0.057 [-0.189, -0.001] | Unavailable |
| Kansas → Nebraska | 1,733 | Linear trend | 10.383 [9.826, 10.859] | 0.112 [0.009, 0.152] | 0.453 [0.315, 0.594] |
| Kansas → Nebraska | 1,733 | Ridge | 11.017 [10.250, 11.519] | 0.001 [-0.149, 0.069] | 0.381 [0.251, 0.507] |
| Kansas → Nebraska | 1,733 | Random forest | 9.915 [9.495, 10.444] | 0.190 [0.100, 0.225] | 0.503 [0.373, 0.599] |
| Kansas → Oklahoma | 1,800 | County mean | 12.158 [11.305, 13.293] | -0.790 [-1.433, -0.453] | Unavailable |
| Kansas → Oklahoma | 1,800 | Linear trend | 12.027 [10.909, 13.412] | -0.752 [-1.473, -0.332] | 0.220 [0.093, 0.326] |
| Kansas → Oklahoma | 1,800 | Ridge | 12.096 [10.535, 13.930] | -0.772 [-1.689, -0.303] | 0.434 [0.339, 0.530] |
| Kansas → Oklahoma | 1,800 | Random forest | 13.225 [11.738, 15.077] | -1.118 [-2.222, -0.473] | 0.492 [0.405, 0.580] |
| Nebraska → Kansas | 3,215 | County mean | 11.379 [10.469, 12.429] | -0.049 [-0.139, -0.003] | Unavailable |
| Nebraska → Kansas | 3,215 | Linear trend | 11.304 [10.195, 12.595] | -0.036 [-0.209, 0.093] | 0.300 [0.195, 0.390] |
| Nebraska → Kansas | 3,215 | Ridge | 10.894 [10.116, 11.611] | 0.038 [-0.084, 0.138] | 0.467 [0.408, 0.512] |
| Nebraska → Kansas | 3,215 | Random forest | 10.180 [9.315, 10.950] | 0.160 [0.014, 0.297] | 0.529 [0.479, 0.578] |
| Oklahoma → Kansas | 3,215 | County mean | 13.737 [12.940, 14.694] | -0.529 [-0.871, -0.290] | Unavailable |
| Oklahoma → Kansas | 3,215 | Linear trend | 13.353 [12.650, 14.229] | -0.445 [-0.763, -0.229] | 0.300 [0.195, 0.390] |
| Oklahoma → Kansas | 3,215 | Ridge | 13.762 [12.618, 15.017] | -0.535 [-0.984, -0.231] | 0.512 [0.417, 0.595] |
| Oklahoma → Kansas | 3,215 | Random forest | 12.964 [11.933, 14.107] | -0.362 [-0.691, -0.125] | 0.571 [0.516, 0.624] |
| Nebraska + Oklahoma → Kansas | 3,215 | County mean | 11.446 [10.932, 12.053] | -0.062 [-0.182, -0.007] | Unavailable |
| Nebraska + Oklahoma → Kansas | 3,215 | Linear trend | 10.920 [10.391, 11.558] | 0.034 [-0.069, 0.100] | 0.300 [0.195, 0.390] |
| Nebraska + Oklahoma → Kansas | 3,215 | Ridge | 9.728 [9.275, 10.252] | 0.233 [0.113, 0.299] | 0.536 [0.464, 0.582] |
| Nebraska + Oklahoma → Kansas | 3,215 | Random forest | 9.152 [8.748, 9.605] | 0.321 [0.256, 0.349] | 0.624 [0.593, 0.652] |
| Kansas + Oklahoma → Nebraska | 1,733 | County mean | 12.331 [10.686, 13.234] | -0.252 [-0.497, -0.045] | Unavailable |
| Kansas + Oklahoma → Nebraska | 1,733 | Linear trend | 11.553 [10.143, 12.357] | -0.099 [-0.313, 0.061] | 0.453 [0.315, 0.594] |
| Kansas + Oklahoma → Nebraska | 1,733 | Ridge | 12.220 [10.474, 13.195] | -0.230 [-0.507, -0.010] | 0.433 [0.331, 0.534] |
| Kansas + Oklahoma → Nebraska | 1,733 | Random forest | 11.254 [9.992, 12.144] | -0.043 [-0.233, 0.090] | 0.489 [0.368, 0.586] |
| Kansas + Nebraska → Oklahoma | 1,800 | County mean | 12.782 [11.867, 14.002] | -0.979 [-1.708, -0.585] | Unavailable |
| Kansas + Nebraska → Oklahoma | 1,800 | Linear trend | 12.937 [11.666, 14.481] | -1.027 [-1.896, -0.508] | 0.220 [0.093, 0.326] |
| Kansas + Nebraska → Oklahoma | 1,800 | Ridge | 12.372 [10.953, 14.093] | -0.853 [-1.730, -0.406] | 0.451 [0.359, 0.539] |
| Kansas + Nebraska → Oklahoma | 1,800 | Random forest | 14.244 [12.661, 16.197] | -1.457 [-2.736, -0.690] | 0.484 [0.393, 0.571] |
| Three-state holdout, pooled | 6,748 | County mean | 12.044 [11.446, 12.782] | -0.124 [-0.979, -0.062] | -0.345 [-0.449, -0.076] |
| Three-state holdout, pooled | 6,748 | Linear trend | 11.651 [10.920, 12.937] | -0.052 [-1.027, 0.034] | 0.117 [0.009, 0.453] |
| Three-state holdout, pooled | 6,748 | Ridge | 11.147 [9.728, 12.372] | 0.037 [-0.853, 0.233] | 0.290 [0.136, 0.536] |
| Three-state holdout, pooled | 6,748 | Random forest | 11.250 [9.152, 14.244] | 0.019 [-1.457, 0.321] | 0.332 [0.182, 0.624] |

### Differences against own-state references

Negative RMSE differences favor the transfer model. For in-state references, the performance table directly compares models with that state's mean and trend. Kansas own-state references come from the saved P27 district evaluation. Nebraska and Oklahoma references come from the P32 in-state rows above.

| Evaluation | Own mean RMSE | Own trend RMSE | Model | Δ vs own mean | Δ vs own trend |
| --- | --- | --- | --- | --- | --- |
| Kansas → Nebraska | 11.274 | 10.161 | Ridge | -0.257 [-1.208, +0.466] | +0.856 [-1.131, +2.311] |
| Kansas → Nebraska | 11.274 | 10.161 | Random forest | -1.358 [-1.897, -0.821] | -0.245 [-1.860, +0.984] |
| Kansas → Oklahoma | 9.200 | 8.985 | Ridge | +2.896 [+1.141, +5.014] | +3.111 [+1.535, +4.930] |
| Kansas → Oklahoma | 9.200 | 8.985 | Random forest | +4.025 [+1.774, +6.285] | +4.240 [+2.227, +6.132] |
| Nebraska → Kansas | 11.202 | 10.758 | Ridge | -0.309 [-0.992, +0.380] | +0.135 [-0.721, +1.008] |
| Nebraska → Kansas | 11.202 | 10.758 | Random forest | -1.022 [-1.954, -0.217] | -0.578 [-1.430, +0.173] |
| Oklahoma → Kansas | 11.202 | 10.758 | Ridge | +2.560 [+1.044, +4.057] | +3.004 [+1.373, +4.503] |
| Oklahoma → Kansas | 11.202 | 10.758 | Random forest | +1.761 [+0.411, +3.020] | +2.205 [+0.731, +3.574] |
| Nebraska + Oklahoma → Kansas | 11.202 | 10.758 | Ridge | -1.474 [-2.141, -0.829] | -1.030 [-1.865, -0.302] |
| Nebraska + Oklahoma → Kansas | 11.202 | 10.758 | Random forest | -2.050 [-2.533, -1.645] | -1.606 [-2.265, -1.083] |
| Kansas + Oklahoma → Nebraska | 11.274 | 10.161 | Ridge | +0.946 [-0.987, +2.137] | +2.059 [-0.815, +3.787] |
| Kansas + Oklahoma → Nebraska | 11.274 | 10.161 | Random forest | -0.020 [-1.483, +0.955] | +1.093 [-1.350, +2.743] |
| Kansas + Nebraska → Oklahoma | 9.200 | 8.985 | Ridge | +3.172 [+1.486, +5.176] | +3.387 [+1.895, +5.101] |
| Kansas + Nebraska → Oklahoma | 9.200 | 8.985 | Random forest | +5.044 [+2.653, +7.457] | +5.259 [+3.116, +7.265] |
| Three-state holdout, pooled | 10.724 | 10.158 | Ridge | +0.423 [-1.474, +3.172] | +0.989 [-1.030, +3.387] |
| Three-state holdout, pooled | 10.724 | 10.158 | Random forest | +0.526 [-2.050, +5.044] | +1.091 [-1.606, +5.259] |

### What transferred

- **Within each target state.** Both learners lowered point RMSE relative to the district-held-out mean and trend. Against the trend, the forest's paired improvement was 1.071 bu/acre in Nebraska (95% interval 0.826–1.296) and 1.269 in Oklahoma (0.824–1.824). Oklahoma ridge also had an interval excluding zero. Nebraska ridge's interval included zero.
- **Kansas → Nebraska and Nebraska → Kansas.** The forest beat both own-state baselines on point RMSE in both directions. Against the own-state trend, its improvements were 0.245 and 0.578 bu/acre, respectively. Both paired intervals included zero. Ridge exceeded the own-state trend RMSE in both directions.
- **Kansas → Oklahoma and Oklahoma → Kansas.** Both transferred learners had higher RMSE than both own-state baselines in both directions. The paired intervals exclude zero. For example, Kansas → Oklahoma random forest had RMSE 13.225 bu/acre against Oklahoma's trend RMSE of 8.985.
- **Pooled state holdout.** Training on Nebraska and Oklahoma lowered RMSE for both learners versus both Kansas own-state references, with paired intervals excluding zero. The Nebraska and Oklahoma pooled folds both trailed their own-state trends. Overall, pooled ridge and forest had RMSEs of 11.147 and 11.250 bu/acre versus 11.651 for the source-only trend and 10.158 for the own-state trend. All paired differences against either trend included zero at the pooled level. The pooled bootstrap uses only three state blocks.

A direct-transfer county-mean baseline assigns every target row the same training-state mean, so its Spearman coefficient is undefined. Similar rank associations can coexist with substantial absolute yield error. The tests use these historical counties and overlapping years. Differences in irrigation reporting, management, cultivars or weather distributions could contribute to the transfer gaps. The evaluation does not separate these influences.

### Models, selection and reproduction

Compared 4 methods with 5 learned configurations. Tried ridge alpha 0.1, 1.0, 10.0 and forest minimum leaf sizes 5, 20, with the unchanged 48 trees. There were 16 target-state district folds, 4 directed fits and 3 pooled state folds. That used 345 inner learned fits and 46 outer learned refits. Inner selection groups were USDA districts, qualified by state for the pooled fit. The saved report includes chosen configurations per fold, sample sizes, source-trend comparisons and all intervals.

The [results JSON](../data/processed/climate_yield_transfer.json) and [held-out predictions](../data/processed/climate_yield_transfer_predictions.csv) are separate from P25/P27. Use the following commands from the repository root to rebuild them offline from the committed NASA archives. Add `--fetch --archive` to the first command to resume missing weather chunks. Run `python -m src.cross_state_yield_data --yield-inventory` to reproduce the yield-only screen.

```sh
python -m src.cross_state_yield_data
python -m src.cross_state_yield
```

## P37 local yield recalibration

This learning curve uses only reported non-irrigated winter-wheat records in the cached P25 and P32 feature files. The [preregistration](p37_plan.md) was committed as `5cd5183` before evaluation. The P25/P27/P32 results stay distinct. All P37 results are illustrative and need local validation.

### Common test and source cutoff

For each USDA reporting district, the first 0, 3, 5, 8 or 12 distinct observed years supply local calibration records. Observed years can have calendar gaps. The test set for every method and calibration size starts at that district's thirteenth observed year. Unused earlier years are left out for smaller calibration sizes. All test years follow every calibration year. Districts may use different test origins.

| Target | Districts | Test counties | Test county-years | Across-district test period | Calibration rows at k = 3 / 5 / 8 / 12 |
| --- | --- | --- | --- | --- | --- |
| Nebraska | 8 | 59 | 462 | 2002–2019 | 173 / 285 / 461 / 692 |
| Oklahoma | 5 | 24 | 88 | 2002–2008 | 95 / 148 / 196 / 270 |

Oklahoma excluded South Central, Northeast and East Central, which had 3, 3 and 5 observed years. Nebraska's Northeast district is retained with only one later county-year. The block bootstrap uses eight Nebraska districts and five Oklahoma districts and shares the exact same resamples across curves within each state. The sample is sparse, especially in Oklahoma. The intervals are pointwise and descriptive without multiplicity adjustment.

The Kansas forest uses 48 trees and the unchanged P25/P27 weather features, scaling and county detrending rules where applicable. Like P25/P27, the forest receives the raw weather features. It refits only on the Kansas records preceding each test origin and uses the same prediction throughout each district's curve. The local intercept/trend calibrates the source residual as a district-wide function of year. The two local ridges use earlier-only inner validation, and the mean and trend are county-level fits using the existing unseen-county fallback. The source feature and source adjustment use the outer-origin Kansas fit as frozen input during local selection.

| First held-out year | Last Kansas training year | Kansas training rows | Kansas counties | Selected forest minimum leaf |
| --- | --- | --- | --- | --- |
| 2002 | 2001 | 1,236 | 103 | 5 |
| 2007 | 2006 | 1,751 | 103 | 5 |
| 2008 | 2007 | 1,854 | 103 | 5 |

### First tested amount that beat the local trend

A method qualifies when the upper endpoint of the paired 95% bootstrap interval for its RMSE minus local-trend RMSE is below zero. The baseline needs local observations, so there is no comparison at k = 0.

| Method | Nebraska | Oklahoma |
| --- | --- | --- |
| Kansas source only | 3 years | 3 years |
| Source + local intercept/trend | 5 years | 8 years |
| Local ridge | 3 years | 3 years |
| Local ridge + source feature | 3 years | 3 years |
| Local trend | Reference | Reference |
| Local county mean | 3 years | 3 years |

### Full curves

Each bracket is a descriptive 95% district-block bootstrap interval. Units are bushels per acre for RMSE and its paired difference. A negative paired difference favors the listed method. A dash marks an unavailable estimate or comparison. The local methods require yield history and are unavailable at k = 0.

#### Nebraska

| Local years | Method | RMSE | R² | Spearman ρ | Δ RMSE vs local trend |
| --- | --- | --- | --- | --- | --- |
| 0 | Kansas source only | 12.381 [10.148, 14.728] | -0.373 [-1.375, -0.039] | 0.234 [-0.103, 0.482] | — |
| 0 | Source + local intercept/trend | — | — | — | — |
| 0 | Local ridge | — | — | — | — |
| 0 | Local ridge + source feature | — | — | — | — |
| 0 | Local trend | — | — | — | — |
| 0 | Local county mean | — | — | — | — |
| 3 | Kansas source only | 12.381 [10.148, 14.728] | -0.373 [-1.375, -0.039] | 0.234 [-0.103, 0.482] | -79.231 [-102.946, -35.134] |
| 3 | Source + local intercept/trend | 87.932 [45.724, 112.187] | -68.234 [-124.940, -23.435] | -0.331 [-0.508, 0.001] | -3.680 [-10.307, +1.314] |
| 3 | Local ridge | 12.670 [9.430, 15.255] | -0.437 [-1.514, 0.069] | 0.281 [-0.177, 0.617] | -78.942 [-99.584, -42.074] |
| 3 | Local ridge + source feature | 15.173 [12.228, 18.017] | -1.061 [-2.766, -0.547] | 0.300 [-0.179, 0.576] | -76.439 [-97.484, -39.155] |
| 3 | Local trend | 91.612 [50.328, 113.992] | -74.150 [-128.000, -34.160] | -0.246 [-0.407, 0.019] | +0.000 [+0.000, +0.000] |
| 3 | Local county mean | 12.171 [9.665, 14.209] | -0.326 [-1.357, -0.038] | 0.366 [0.007, 0.527] | -79.442 [-100.575, -41.500] |
| 5 | Kansas source only | 12.381 [10.148, 14.728] | -0.373 [-1.375, -0.039] | 0.234 [-0.103, 0.482] | -18.764 [-31.844, -5.699] |
| 5 | Source + local intercept/trend | 23.678 [13.981, 32.785] | -4.020 [-10.853, -1.032] | -0.296 [-0.493, 0.117] | -7.468 [-12.488, -1.605] |
| 5 | Local ridge | 13.261 [9.888, 16.274] | -0.575 [-2.078, -0.051] | 0.257 [-0.194, 0.581] | -17.884 [-26.036, -9.075] |
| 5 | Local ridge + source feature | 14.931 [11.355, 18.008] | -0.996 [-2.473, -0.301] | 0.320 [-0.153, 0.612] | -16.214 [-25.657, -5.750] |
| 5 | Local trend | 31.146 [19.847, 42.365] | -7.686 [-20.865, -2.930] | -0.312 [-0.454, 0.062] | +0.000 [+0.000, +0.000] |
| 5 | Local county mean | 12.589 [9.608, 15.242] | -0.419 [-1.811, 0.002] | 0.241 [-0.084, 0.426] | -18.556 [-27.614, -9.661] |
| 8 | Kansas source only | 12.381 [10.148, 14.728] | -0.373 [-1.375, -0.039] | 0.234 [-0.103, 0.482] | -3.104 [-8.240, +1.085] |
| 8 | Source + local intercept/trend | 14.303 [10.978, 16.729] | -0.832 [-1.946, -0.210] | -0.058 [-0.366, 0.407] | -1.183 [-5.722, +2.673] |
| 8 | Local ridge | 12.938 [9.028, 16.180] | -0.499 [-2.126, 0.088] | 0.219 [-0.166, 0.556] | -2.548 [-4.815, -0.528] |
| 8 | Local ridge + source feature | 12.484 [8.930, 16.343] | -0.396 [-2.070, 0.212] | 0.214 [-0.093, 0.516] | -3.001 [-4.952, -1.039] |
| 8 | Local trend | 15.485 [12.940, 18.895] | -1.147 [-3.059, -0.564] | -0.067 [-0.244, 0.242] | +0.000 [+0.000, +0.000] |
| 8 | Local county mean | 12.201 [9.050, 14.922] | -0.333 [-1.721, 0.112] | 0.172 [-0.121, 0.416] | -3.285 [-5.764, -0.804] |
| 12 | Kansas source only | 12.381 [10.148, 14.728] | -0.373 [-1.375, -0.039] | 0.234 [-0.103, 0.482] | +1.630 [-0.460, +4.127] |
| 12 | Source + local intercept/trend | 10.074 [8.543, 11.770] | 0.091 [-0.644, 0.300] | 0.499 [-0.084, 0.647] | -0.677 [-1.972, +0.947] |
| 12 | Local ridge | 10.253 [8.194, 12.040] | 0.059 [-0.817, 0.289] | 0.386 [-0.234, 0.594] | -0.498 [-2.746, +1.882] |
| 12 | Local ridge + source feature | 9.690 [8.008, 11.244] | 0.159 [-0.486, 0.362] | 0.448 [-0.106, 0.628] | -1.061 [-2.711, +0.510] |
| 12 | Local trend | 10.751 [9.994, 11.618] | -0.035 [-0.482, 0.084] | 0.265 [0.032, 0.476] | +0.000 [+0.000, +0.000] |
| 12 | Local county mean | 11.004 [8.474, 13.111] | -0.084 [-1.061, 0.201] | 0.218 [-0.120, 0.440] | +0.253 [-2.490, +2.866] |

#### Oklahoma

| Local years | Method | RMSE | R² | Spearman ρ | Δ RMSE vs local trend |
| --- | --- | --- | --- | --- | --- |
| 0 | Kansas source only | 20.259 [17.082, 21.230] | -6.011 [-10.243, -2.942] | 0.458 [0.164, 0.645] | — |
| 0 | Source + local intercept/trend | — | — | — | — |
| 0 | Local ridge | — | — | — | — |
| 0 | Local ridge + source feature | — | — | — | — |
| 0 | Local trend | — | — | — | — |
| 0 | Local county mean | — | — | — | — |
| 3 | Kansas source only | 20.259 [17.082, 21.230] | -6.011 [-10.243, -2.942] | 0.458 [0.164, 0.645] | -29.601 [-46.483, -10.127] |
| 3 | Source + local intercept/trend | 60.023 [39.683, 75.027] | -60.537 [-138.257, -18.760] | -0.043 [-0.250, 0.472] | +10.163 [-24.809, +43.110] |
| 3 | Local ridge | 7.005 [6.194, 7.767] | 0.162 [-0.063, 0.390] | 0.421 [0.188, 0.779] | -42.856 [-58.170, -24.608] |
| 3 | Local ridge + source feature | 7.863 [6.659, 8.561] | -0.056 [-0.456, 0.317] | 0.295 [0.026, 0.836] | -41.997 [-57.500, -23.635] |
| 3 | Local trend | 49.861 [31.045, 65.906] | -41.463 [-68.662, -22.707] | 0.249 [-0.091, 0.300] | +0.000 [+0.000, +0.000] |
| 3 | Local county mean | 7.463 [6.864, 8.979] | 0.049 [-0.342, 0.222] | 0.302 [0.003, 0.492] | -42.397 [-58.164, -23.968] |
| 5 | Kansas source only | 20.259 [17.082, 21.230] | -6.011 [-10.243, -2.942] | 0.458 [0.164, 0.645] | -8.182 [-27.199, +1.238] |
| 5 | Source + local intercept/trend | 27.535 [11.364, 34.648] | -11.950 [-20.588, -1.054] | 0.421 [0.131, 0.729] | -0.906 [-30.252, +8.206] |
| 5 | Local ridge | 6.675 [6.144, 8.179] | 0.239 [-0.104, 0.376] | 0.695 [0.456, 0.833] | -21.766 [-36.534, -13.592] |
| 5 | Local ridge + source feature | 7.933 [6.911, 10.266] | -0.075 [-0.782, 0.318] | 0.661 [0.461, 0.815] | -20.508 [-36.917, -12.162] |
| 5 | Local trend | 28.441 [20.074, 44.324] | -12.816 [-26.787, -8.622] | 0.107 [-0.363, 0.299] | +0.000 [+0.000, +0.000] |
| 5 | Local county mean | 7.530 [6.762, 9.433] | 0.032 [-0.347, 0.143] | 0.325 [0.048, 0.475] | -20.911 [-35.249, -13.063] |
| 8 | Kansas source only | 20.259 [17.082, 21.230] | -6.011 [-10.243, -2.942] | 0.458 [0.164, 0.645] | -3.378 [-23.606, +4.345] |
| 8 | Source + local intercept/trend | 14.654 [10.335, 17.062] | -2.668 [-6.119, -0.258] | 0.329 [0.120, 0.717] | -8.984 [-28.880, -0.241] |
| 8 | Local ridge | 6.862 [6.309, 7.537] | 0.196 [-0.282, 0.443] | 0.742 [0.488, 0.862] | -16.775 [-32.964, -9.548] |
| 8 | Local ridge + source feature | 7.965 [5.853, 9.356] | -0.084 [-1.144, 0.556] | 0.660 [0.515, 0.868] | -15.672 [-33.039, -7.420] |
| 8 | Local trend | 23.638 [16.515, 40.500] | -8.543 [-23.014, -4.305] | 0.024 [-0.201, 0.191] | +0.000 [+0.000, +0.000] |
| 8 | Local county mean | 7.783 [7.118, 9.625] | -0.035 [-0.376, 0.101] | 0.346 [0.029, 0.527] | -15.855 [-31.098, -9.045] |
| 12 | Kansas source only | 20.259 [17.082, 21.230] | -6.011 [-10.243, -2.942] | 0.458 [0.164, 0.645] | +8.893 [+1.263, +12.248] |
| 12 | Source + local intercept/trend | 7.201 [6.826, 8.014] | 0.114 [-0.301, 0.352] | 0.407 [0.120, 0.640] | -4.166 [-8.324, -1.742] |
| 12 | Local ridge | 6.029 [5.632, 6.827] | 0.379 [0.106, 0.493] | 0.680 [0.484, 0.833] | -5.338 [-9.652, -2.907] |
| 12 | Local ridge + source feature | 6.319 [5.877, 6.987] | 0.318 [0.119, 0.438] | 0.573 [0.387, 0.799] | -5.048 [-9.398, -2.868] |
| 12 | Local trend | 11.367 [8.979, 16.248] | -1.207 [-2.837, -0.739] | 0.011 [-0.194, 0.172] | +0.000 [+0.000, +0.000] |
| 12 | Local county mean | 7.501 [6.535, 9.641] | 0.039 [-0.391, 0.103] | 0.271 [0.011, 0.349] | -3.866 [-6.664, -2.214] |

### Reading the learning curves

- The three-year county trend extrapolated sharply, with RMSE of 91.612 bu/acre in Nebraska and 49.861 in Oklahoma. At 12 years those errors fell to 10.751 and 11.367. A trend fitted to only a few years is a weak baseline. The source-only prediction is identical at every k. Its early wins compare against a short trend with large extrapolation errors. In Oklahoma the source-only model was worse than the trend at 12 years, with a paired difference of +8.893 [+1.263, +12.248] bu/acre.

- In Nebraska at 12 years the source-feature ridge had the lowest point RMSE (9.690 bu/acre). Its paired difference from the trend was −1.061 [−2.711, +0.510]. Every Nebraska 12-year comparison with the trend included zero.

- In Oklahoma at 12 years the local ridge had the lowest point RMSE (6.029 bu/acre), ahead of the source-feature ridge (6.319) and the local county mean (7.501). The local ridge's paired difference from the trend was −5.338 [−9.652, −2.907]. Source adjustment, source-feature ridge and county mean also beat the trend at that size. The P37 and P37b comparisons use the local trend and county mean as references. Whether adding the Kansas prediction improves on local ridge remains undetermined.

- This exercise uses recorded district yield history, which many farmers do not have. Weather uses NASA POWER historic county centroids and the Kansas crop window. County yields represent many farms, varieties and management choices. These associations do not validate rotation recommendations.

### Fit counts and reproduction

Six methods were specified. The source forest tried two minimum leaf sizes (5 and 20). Each local ridge tried the same three alphas (0.1, 1 and 10). This yields eight search entries across the three fitted model roles, with no tuned settings for the residual line, trend or mean.

The source search ran 18 inner fits and 3 outer fits over three origins. Local ridge selection ran 1,872 inner fits and 104 outer fits across both ridge variants. There were 156 method-level fixed fit instances for the residual line, county trend and mean. Counts are for fitted district and history-size combinations, not individual county regressions.

Run `python -m src.local_recalibration` from the repository root to rebuild the two P37 files offline. The saved report records the exact district test and calibration years, available sample sizes, selected source and ridge configurations and the source file hashes. [Report JSON](../data/processed/climate_yield_recalibration.json) · [Held-out predictions](../data/processed/climate_yield_recalibration_predictions.csv)

## P37b county-mean comparison

This follow-up uses the saved P37 predictions and common test rows. No models were refitted. Differences are method RMSE minus the local county-mean RMSE in bushels per acre. The same 1,000 paired district-block bootstrap draws use seed 42 and the same 95% percentile interval. Intervals entirely below zero favor the method. An interval entirely above zero indicates higher RMSE. Intervals that cover zero leave the direction uncertain. At k = 0 the local mean is unavailable, so every comparison is unavailable.

### Nebraska

| Local years | Method | Δ RMSE vs county mean [95% interval] | Result |
|---|---|---:|---|
| 0 | Kansas source only | — | Unavailable |
| 0 | Source + local intercept/trend | — | Unavailable |
| 0 | Local ridge | — | Unavailable |
| 0 | Local ridge + source feature | — | Unavailable |
| 0 | Local trend | — | Unavailable |
| 0 | Local county mean | — | Unavailable |
| 3 | Kansas source only | +0.211 [-3.932, +4.922] | Interval includes zero |
| 3 | Source + local intercept/trend | +75.762 [+36.103, +98.553] | Higher RMSE |
| 3 | Local ridge | +0.500 [-1.252, +2.163] | Interval includes zero |
| 3 | Local ridge + source feature | +3.002 [+1.714, +3.966] | Higher RMSE |
| 3 | Local trend | +79.442 [+41.500, +100.575] | Higher RMSE |
| 3 | Local county mean | +0.000 [+0.000, +0.000] | Reference |
| 5 | Kansas source only | -0.208 [-4.962, +5.027] | Interval includes zero |
| 5 | Source + local intercept/trend | +11.088 [+3.631, +18.845] | Higher RMSE |
| 5 | Local ridge | +0.672 [-0.423, +1.850] | Interval includes zero |
| 5 | Local ridge + source feature | +2.342 [-0.470, +4.585] | Interval includes zero |
| 5 | Local trend | +18.556 [+9.661, +27.614] | Higher RMSE |
| 5 | Local county mean | +0.000 [+0.000, +0.000] | Reference |
| 8 | Kansas source only | +0.180 [-4.739, +5.578] | Interval includes zero |
| 8 | Source + local intercept/trend | +2.102 [-3.203, +7.278] | Interval includes zero |
| 8 | Local ridge | +0.737 [-0.138, +1.695] | Interval includes zero |
| 8 | Local ridge + source feature | +0.283 [-1.314, +2.385] | Interval includes zero |
| 8 | Local trend | +3.285 [+0.804, +5.764] | Higher RMSE |
| 8 | Local county mean | +0.000 [+0.000, +0.000] | Reference |
| 12 | Kansas source only | +1.377 [-2.812, +6.055] | Interval includes zero |
| 12 | Source + local intercept/trend | -0.929 [-2.994, +1.736] | Interval includes zero |
| 12 | Local ridge | -0.751 [-1.282, -0.019] | Beats county mean |
| 12 | Local ridge + source feature | -1.313 [-3.158, +0.952] | Interval includes zero |
| 12 | Local trend | -0.253 [-2.866, +2.490] | Interval includes zero |
| 12 | Local county mean | +0.000 [+0.000, +0.000] | Reference |

### Oklahoma

| Local years | Method | Δ RMSE vs county mean [95% interval] | Result |
|---|---|---:|---|
| 0 | Kansas source only | — | Unavailable |
| 0 | Source + local intercept/trend | — | Unavailable |
| 0 | Local ridge | — | Unavailable |
| 0 | Local ridge + source feature | — | Unavailable |
| 0 | Local trend | — | Unavailable |
| 0 | Local county mean | — | Unavailable |
| 3 | Kansas source only | +12.796 [+8.520, +14.333] | Higher RMSE |
| 3 | Source + local intercept/trend | +52.560 [+31.852, +68.066] | Higher RMSE |
| 3 | Local ridge | -0.459 [-2.241, +0.415] | Interval includes zero |
| 3 | Local ridge + source feature | +0.400 [-2.042, +1.298] | Interval includes zero |
| 3 | Local trend | +42.397 [+23.968, +58.164] | Higher RMSE |
| 3 | Local county mean | +0.000 [+0.000, +0.000] | Reference |
| 5 | Kansas source only | +12.730 [+7.648, +14.464] | Higher RMSE |
| 5 | Source + local intercept/trend | +20.005 [+2.798, +27.199] | Higher RMSE |
| 5 | Local ridge | -0.855 [-1.390, -0.322] | Beats county mean |
| 5 | Local ridge + source feature | +0.403 [-1.329, +2.058] | Interval includes zero |
| 5 | Local trend | +20.911 [+13.063, +35.249] | Higher RMSE |
| 5 | Local county mean | +0.000 [+0.000, +0.000] | Reference |
| 8 | Kansas source only | +12.477 [+7.627, +14.124] | Higher RMSE |
| 8 | Source + local intercept/trend | +6.871 [+1.016, +9.930] | Higher RMSE |
| 8 | Local ridge | -0.921 [-2.177, -0.057] | Beats county mean |
| 8 | Local ridge + source feature | +0.183 [-2.524, +2.029] | Interval includes zero |
| 8 | Local trend | +15.855 [+9.045, +31.098] | Higher RMSE |
| 8 | Local county mean | +0.000 [+0.000, +0.000] | Reference |
| 12 | Kansas source only | +12.759 [+7.254, +14.697] | Higher RMSE |
| 12 | Source + local intercept/trend | -0.299 [-1.981, +0.670] | Interval includes zero |
| 12 | Local ridge | -1.472 [-2.989, -0.594] | Beats county mean |
| 12 | Local ridge + source feature | -1.182 [-2.800, -0.512] | Beats county mean |
| 12 | Local trend | +3.866 [+2.214, +6.664] | Higher RMSE |
| 12 | Local county mean | +0.000 [+0.000, +0.000] | Reference |

### What changed with the county-mean benchmark

- **Nebraska.** Local ridge was the only method to beat the county mean with an interval excluding zero. It did so at 12 years (−0.751 [−1.282, −0.019] bu/acre). No method cleared that threshold at 3, 5 or 8 years.

- **Oklahoma.** Local ridge beat the mean at 5, 8 and 12 years. Its first qualifying difference was −0.855 [−1.390, −0.322] bu/acre at 5 years. Source-feature ridge also beat the mean at 12 years (−1.182 [−2.800, −0.512]). The Kansas source-only model, source adjustment and local trend had no qualifying improvement at any tested k. The county mean is the reference.

- **Three-year comparisons.** Several methods beat the three-year trend in P37, while no method beat the three-year county mean with an interval excluding zero in either state. A trend fitted to only a few years is a weak baseline. The intervals are descriptive, with eight district blocks in Nebraska and five in Oklahoma.

Run `python -m src.recalibration_county_mean` to rebuild only the P37b comparison offline. [Saved P37b comparison](../data/processed/climate_yield_recalibration_county_mean.json) · [Original trend comparisons](#full-curves)

## P33 calibrated yield intervals

The [preregistration](p33_plan.md) was committed as `8ba46bf` before evaluation. The analysis uses separate split-conformal copies of the P25/P27 ridge and random forest with the existing configuration and cached features. Each outer fold reserves a group split from outer training for calibration before any tuning or fitting. The P33 fit therefore uses fewer rows than the published point model. Both learners use the same held-apart groups for fitting, calibration and testing. Centers are held fixed after fitting. Neither calibration nor test observations participate in fitting or hyperparameter choice. The conformal radius uses the finite-sample ceiling rank of the absolute held-apart errors. All findings are illustrative and need local validation.

### Evaluation counts and reading the tables

| Protocol | Unique interval evaluations |
| --- | --- |
| Kansas district holdout | 12,860 |
| Kansas harvest-year holdout | 12,860 |
| P32 Kansas-to-target spatial transfer | 14,132 |
| P37 chronological recalibration | 11,000 |
| Total | 50,852 |

A county-year contributes one interval per learner, level and applicable calibration setting. Fold and subgroup tables are views of the same intervals. Width is the mean full span in bushels per acre, and the ratio divides that width by the county-mean point model's RMSE on those rows. In Kansas the mean model uses proper training only. Transfer rows use the saved target-state P32 district reference. P37 uses its saved local county mean at each positive k. Coverage intervals are pointwise descriptive paired district or year block bootstraps. The exact block, counts and fold membership are in the saved report. A dash for a coverage interval indicates that only one block was available.

### Kansas coverage

| Evaluation | Model | Nominal | County-years | Covered | Coverage | 95% interval | Mean width | County-mean RMSE | Width / RMSE | Below nominal | Calibration rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| District holdout | Ridge | 80% | 3,215 | 2,586 | 80.4% | 76.6%–83.7% | 24.921 | 11.269 | 2.212 | — | 993–1068 |
| District holdout | Ridge | 90% | 3,215 | 2,892 | 90.0% | 87.4%–92.0% | 31.984 | 11.269 | 2.838 | Yes | 993–1068 |
| District holdout | Random forest | 80% | 3,215 | 2,598 | 80.8% | 75.8%–85.0% | 23.931 | 11.269 | 2.124 | — | 993–1068 |
| District holdout | Random forest | 90% | 3,215 | 2,900 | 90.2% | 86.3%–93.2% | 32.130 | 11.269 | 2.851 | — | 993–1068 |
| Harvest-year holdout | Ridge | 80% | 3,215 | 2,535 | 78.8% | 72.9%–84.2% | 23.462 | 10.827 | 2.167 | Yes | 1038–1055 |
| Harvest-year holdout | Ridge | 90% | 3,215 | 2,840 | 88.3% | 83.4%–92.1% | 29.899 | 10.827 | 2.762 | Yes | 1038–1055 |
| Harvest-year holdout | Random forest | 80% | 3,215 | 2,426 | 75.5% | 69.4%–80.4% | 22.209 | 10.827 | 2.051 | Yes | 1038–1055 |
| Harvest-year holdout | Random forest | 90% | 3,215 | 2,760 | 85.8% | 80.7%–89.8% | 28.371 | 10.827 | 2.620 | Yes | 1038–1055 |

#### District holdout

<details>
<summary>All outer folds</summary>

| Evaluation | Model | Nominal | County-years | Covered | Coverage | 95% interval | Mean width | County-mean RMSE | Width / RMSE | Below nominal | Calibration rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | Ridge | 80% | 237 | 191 | 80.6% | 72.1%–88.1% | 26.924 | 11.617 | 2.318 | — | 1068 |
| 10 | Ridge | 90% | 237 | 214 | 90.3% | 84.2%–95.2% | 33.608 | 11.617 | 2.893 | — | 1068 |
| 10 | Random forest | 80% | 237 | 194 | 81.9% | 73.7%–88.9% | 25.200 | 11.617 | 2.169 | — | 1068 |
| 10 | Random forest | 90% | 237 | 220 | 92.8% | 87.2%–97.5% | 33.237 | 11.617 | 2.861 | — | 1068 |
| 20 | Ridge | 80% | 275 | 239 | 86.9% | 81.0%–92.1% | 26.369 | 11.025 | 2.392 | — | 1068 |
| 20 | Ridge | 90% | 275 | 258 | 93.8% | 89.8%–97.1% | 32.918 | 11.025 | 2.986 | — | 1068 |
| 20 | Random forest | 80% | 275 | 243 | 88.4% | 83.8%–92.6% | 24.378 | 11.025 | 2.211 | — | 1068 |
| 20 | Random forest | 90% | 275 | 265 | 96.4% | 93.3%–99.0% | 33.328 | 11.025 | 3.023 | — | 1068 |
| 30 | Ridge | 80% | 424 | 309 | 72.9% | 63.8%–81.3% | 23.812 | 13.079 | 1.821 | Yes | 994 |
| 30 | Ridge | 90% | 424 | 358 | 84.4% | 77.5%–91.0% | 30.832 | 13.079 | 2.357 | Yes | 994 |
| 30 | Random forest | 80% | 424 | 337 | 79.5% | 72.4%–84.9% | 23.269 | 13.079 | 1.779 | Yes | 994 |
| 30 | Random forest | 90% | 424 | 383 | 90.3% | 85.4%–94.2% | 30.147 | 13.079 | 2.305 | — | 994 |
| 40 | Ridge | 80% | 349 | 279 | 79.9% | 70.3%–88.2% | 25.580 | 10.153 | 2.520 | Yes | 994 |
| 40 | Ridge | 90% | 349 | 317 | 90.8% | 84.6%–95.9% | 32.137 | 10.153 | 3.165 | — | 994 |
| 40 | Random forest | 80% | 349 | 301 | 86.2% | 79.2%–92.5% | 24.321 | 10.153 | 2.396 | — | 994 |
| 40 | Random forest | 90% | 349 | 326 | 93.4% | 88.4%–97.7% | 32.851 | 10.153 | 3.236 | — | 994 |
| 50 | Ridge | 80% | 352 | 301 | 85.5% | 76.9%–93.1% | 24.958 | 10.406 | 2.399 | — | 994 |
| 50 | Ridge | 90% | 352 | 329 | 93.5% | 87.4%–98.0% | 31.885 | 10.406 | 3.064 | — | 994 |
| 50 | Random forest | 80% | 352 | 311 | 88.4% | 81.1%–94.4% | 23.921 | 10.406 | 2.299 | — | 994 |
| 50 | Random forest | 90% | 352 | 334 | 94.9% | 89.8%–98.3% | 30.677 | 10.406 | 2.948 | — | 994 |
| 60 | Ridge | 80% | 418 | 356 | 85.2% | 77.8%–91.3% | 24.302 | 10.353 | 2.347 | — | 994 |
| 60 | Ridge | 90% | 418 | 382 | 91.4% | 85.9%–95.8% | 31.718 | 10.353 | 3.064 | — | 994 |
| 60 | Random forest | 80% | 418 | 329 | 78.7% | 69.3%–87.4% | 23.634 | 10.353 | 2.283 | Yes | 994 |
| 60 | Random forest | 90% | 418 | 369 | 88.3% | 80.0%–94.8% | 30.834 | 10.353 | 2.978 | Yes | 994 |
| 70 | Ridge | 80% | 277 | 189 | 68.2% | 57.6%–78.1% | 24.477 | 12.765 | 1.918 | Yes | 1066 |
| 70 | Ridge | 90% | 277 | 229 | 82.7% | 73.1%–90.6% | 30.962 | 12.765 | 2.426 | Yes | 1066 |
| 70 | Random forest | 80% | 277 | 165 | 59.6% | 48.4%–70.2% | 21.100 | 12.765 | 1.653 | Yes | 1066 |
| 70 | Random forest | 90% | 277 | 201 | 72.6% | 61.5%–82.8% | 28.551 | 12.765 | 2.237 | Yes | 1066 |
| 80 | Ridge | 80% | 442 | 363 | 82.1% | 72.4%–90.4% | 24.700 | 10.526 | 2.347 | — | 993 |
| 80 | Ridge | 90% | 442 | 406 | 91.9% | 84.6%–97.4% | 32.390 | 10.526 | 3.077 | — | 993 |
| 80 | Random forest | 80% | 442 | 372 | 84.2% | 76.3%–91.3% | 25.223 | 10.526 | 2.396 | — | 993 |
| 80 | Random forest | 90% | 442 | 401 | 90.7% | 84.4%–96.3% | 34.415 | 10.526 | 3.270 | — | 993 |
| 90 | Ridge | 80% | 441 | 359 | 81.4% | 72.5%–87.8% | 24.547 | 11.402 | 2.153 | — | 994 |
| 90 | Ridge | 90% | 441 | 399 | 90.5% | 81.7%–95.6% | 32.084 | 11.402 | 2.814 | — | 994 |
| 90 | Random forest | 80% | 441 | 346 | 78.5% | 70.4%–85.4% | 24.070 | 11.402 | 2.111 | Yes | 994 |
| 90 | Random forest | 90% | 441 | 401 | 90.9% | 85.3%–95.5% | 34.469 | 11.402 | 3.023 | — | 994 |

</details>

<details>
<summary>All cross-cutting year diagnostics</summary>

| Evaluation | Model | Nominal | County-years | Covered | Coverage | 95% interval | Mean width | County-mean RMSE | Width / RMSE | Below nominal | Calibration rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1990 | Ridge | 80% | 103 | 82 | 79.6% | 61.9%–92.1% | 24.929 | 6.856 | 3.636 | Yes | 993–1068 |
| 1990 | Ridge | 90% | 103 | 96 | 93.2% | 80.6%–100.0% | 31.987 | 6.856 | 4.666 | — | 993–1068 |
| 1990 | Random forest | 80% | 103 | 82 | 79.6% | 63.7%–92.6% | 23.929 | 6.856 | 3.490 | Yes | 993–1068 |
| 1990 | Random forest | 90% | 103 | 96 | 93.2% | 83.3%–100.0% | 32.125 | 6.856 | 4.686 | — | 993–1068 |
| 1991 | Ridge | 80% | 103 | 99 | 96.1% | 90.3%–100.0% | 24.929 | 7.447 | 3.347 | — | 993–1068 |
| 1991 | Ridge | 90% | 103 | 102 | 99.0% | 97.1%–100.0% | 31.987 | 7.447 | 4.295 | — | 993–1068 |
| 1991 | Random forest | 80% | 103 | 95 | 92.2% | 86.7%–97.8% | 23.929 | 7.447 | 3.213 | — | 993–1068 |
| 1991 | Random forest | 90% | 103 | 102 | 99.0% | 97.1%–100.0% | 32.125 | 7.447 | 4.314 | — | 993–1068 |
| 1992 | Ridge | 80% | 103 | 96 | 93.2% | 87.2%–98.0% | 24.929 | 8.267 | 3.016 | — | 993–1068 |
| 1992 | Ridge | 90% | 103 | 99 | 96.1% | 90.1%–100.0% | 31.987 | 8.267 | 3.869 | — | 993–1068 |
| 1992 | Random forest | 80% | 103 | 84 | 81.6% | 73.2%–91.3% | 23.929 | 8.267 | 2.895 | — | 993–1068 |
| 1992 | Random forest | 90% | 103 | 96 | 93.2% | 87.5%–98.2% | 32.125 | 8.267 | 3.886 | — | 993–1068 |
| 1993 | Ridge | 80% | 103 | 95 | 92.2% | 87.4%–97.1% | 24.929 | 10.130 | 2.461 | — | 993–1068 |
| 1993 | Ridge | 90% | 103 | 102 | 99.0% | 96.7%–100.0% | 31.987 | 10.130 | 3.158 | — | 993–1068 |
| 1993 | Random forest | 80% | 103 | 101 | 98.1% | 95.3%–100.0% | 23.929 | 10.130 | 2.362 | — | 993–1068 |
| 1993 | Random forest | 90% | 103 | 102 | 99.0% | 96.7%–100.0% | 32.125 | 10.130 | 3.171 | — | 993–1068 |
| 1994 | Ridge | 80% | 103 | 101 | 98.1% | 94.8%–100.0% | 24.929 | 5.313 | 4.692 | — | 993–1068 |
| 1994 | Ridge | 90% | 103 | 103 | 100.0% | 100.0%–100.0% | 31.987 | 5.313 | 6.021 | — | 993–1068 |
| 1994 | Random forest | 80% | 103 | 93 | 90.3% | 79.8%–98.2% | 23.929 | 5.313 | 4.504 | — | 993–1068 |
| 1994 | Random forest | 90% | 103 | 99 | 96.1% | 90.0%–100.0% | 32.125 | 5.313 | 6.047 | — | 993–1068 |
| 1995 | Ridge | 80% | 103 | 81 | 78.6% | 54.6%–96.6% | 24.929 | 15.620 | 1.596 | Yes | 993–1068 |
| 1995 | Ridge | 90% | 103 | 89 | 86.4% | 68.2%–99.1% | 31.987 | 15.620 | 2.048 | Yes | 993–1068 |
| 1995 | Random forest | 80% | 103 | 79 | 76.7% | 60.4%–91.8% | 23.929 | 15.620 | 1.532 | Yes | 993–1068 |
| 1995 | Random forest | 90% | 103 | 94 | 91.3% | 80.9%–99.1% | 32.125 | 15.620 | 2.057 | — | 993–1068 |
| 1996 | Ridge | 80% | 103 | 89 | 86.4% | 75.5%–96.2% | 24.929 | 12.260 | 2.033 | — | 993–1068 |
| 1996 | Ridge | 90% | 103 | 97 | 94.2% | 89.1%–98.8% | 31.987 | 12.260 | 2.609 | — | 993–1068 |
| 1996 | Random forest | 80% | 103 | 98 | 95.1% | 91.0%–99.0% | 23.929 | 12.260 | 1.952 | — | 993–1068 |
| 1996 | Random forest | 90% | 103 | 103 | 100.0% | 100.0%–100.0% | 32.125 | 12.260 | 2.620 | — | 993–1068 |
| 1997 | Ridge | 80% | 103 | 87 | 84.5% | 78.3%–90.8% | 24.929 | 11.663 | 2.137 | — | 993–1068 |
| 1997 | Ridge | 90% | 103 | 97 | 94.2% | 88.3%–98.4% | 31.987 | 11.663 | 2.743 | — | 993–1068 |
| 1997 | Random forest | 80% | 103 | 81 | 78.6% | 71.7%–85.2% | 23.929 | 11.663 | 2.052 | Yes | 993–1068 |
| 1997 | Random forest | 90% | 103 | 96 | 93.2% | 89.4%–97.0% | 32.125 | 11.663 | 2.754 | — | 993–1068 |
| 1998 | Ridge | 80% | 103 | 88 | 85.4% | 74.5%–94.4% | 24.929 | 11.171 | 2.232 | — | 993–1068 |
| 1998 | Ridge | 90% | 103 | 99 | 96.1% | 88.2%–100.0% | 31.987 | 11.171 | 2.863 | — | 993–1068 |
| 1998 | Random forest | 80% | 103 | 80 | 77.7% | 55.3%–96.2% | 23.929 | 11.171 | 2.142 | Yes | 993–1068 |
| 1998 | Random forest | 90% | 103 | 89 | 86.4% | 69.8%–99.0% | 32.125 | 11.171 | 2.876 | Yes | 993–1068 |
| 1999 | Ridge | 80% | 103 | 82 | 79.6% | 61.2%–94.4% | 24.929 | 9.675 | 2.577 | Yes | 993–1068 |
| 1999 | Ridge | 90% | 103 | 96 | 93.2% | 83.7%–100.0% | 31.987 | 9.675 | 3.306 | — | 993–1068 |
| 1999 | Random forest | 80% | 103 | 83 | 80.6% | 61.8%–95.0% | 23.929 | 9.675 | 2.473 | — | 993–1068 |
| 1999 | Random forest | 90% | 103 | 88 | 85.4% | 66.3%–100.0% | 32.125 | 9.675 | 3.321 | Yes | 993–1068 |
| 2000 | Ridge | 80% | 103 | 96 | 93.2% | 84.5%–99.1% | 24.929 | 4.963 | 5.023 | — | 993–1068 |
| 2000 | Ridge | 90% | 103 | 102 | 99.0% | 96.8%–100.0% | 31.987 | 4.963 | 6.445 | — | 993–1068 |
| 2000 | Random forest | 80% | 103 | 96 | 93.2% | 79.8%–100.0% | 23.929 | 4.963 | 4.821 | — | 993–1068 |
| 2000 | Random forest | 90% | 103 | 98 | 95.1% | 84.0%–100.0% | 32.125 | 4.963 | 6.473 | — | 993–1068 |
| 2001 | Ridge | 80% | 103 | 99 | 96.1% | 92.0%–100.0% | 24.929 | 7.182 | 3.471 | — | 993–1068 |
| 2001 | Ridge | 90% | 103 | 102 | 99.0% | 96.8%–100.0% | 31.987 | 7.182 | 4.453 | — | 993–1068 |
| 2001 | Random forest | 80% | 103 | 84 | 81.6% | 69.1%–93.6% | 23.929 | 7.182 | 3.332 | — | 993–1068 |
| 2001 | Random forest | 90% | 103 | 97 | 94.2% | 86.6%–100.0% | 32.125 | 7.182 | 4.473 | — | 993–1068 |
| 2002 | Ridge | 80% | 103 | 79 | 76.7% | 58.1%–91.0% | 24.929 | 11.185 | 2.229 | Yes | 993–1068 |
| 2002 | Ridge | 90% | 103 | 89 | 86.4% | 73.7%–96.5% | 31.987 | 11.185 | 2.860 | Yes | 993–1068 |
| 2002 | Random forest | 80% | 103 | 91 | 88.3% | 77.2%–97.1% | 23.929 | 11.185 | 2.139 | — | 993–1068 |
| 2002 | Random forest | 90% | 103 | 98 | 95.1% | 86.4%–100.0% | 32.125 | 11.185 | 2.872 | — | 993–1068 |
| 2003 | Ridge | 80% | 103 | 60 | 58.3% | 35.1%–80.8% | 24.929 | 16.488 | 1.512 | Yes | 993–1068 |
| 2003 | Ridge | 90% | 103 | 73 | 70.9% | 48.4%–89.3% | 31.987 | 16.488 | 1.940 | Yes | 993–1068 |
| 2003 | Random forest | 80% | 103 | 57 | 55.3% | 32.7%–79.8% | 23.929 | 16.488 | 1.451 | Yes | 993–1068 |
| 2003 | Random forest | 90% | 103 | 73 | 70.9% | 48.6%–91.9% | 32.125 | 16.488 | 1.948 | Yes | 993–1068 |
| 2004 | Ridge | 80% | 103 | 86 | 83.5% | 70.0%–93.5% | 24.929 | 12.389 | 2.012 | — | 993–1068 |
| 2004 | Ridge | 90% | 103 | 98 | 95.1% | 89.8%–99.1% | 31.987 | 12.389 | 2.582 | — | 993–1068 |
| 2004 | Random forest | 80% | 103 | 85 | 82.5% | 65.9%–92.9% | 23.929 | 12.389 | 1.931 | — | 993–1068 |
| 2004 | Random forest | 90% | 103 | 97 | 94.2% | 83.1%–100.0% | 32.125 | 12.389 | 2.593 | — | 993–1068 |
| 2005 | Ridge | 80% | 103 | 94 | 91.3% | 83.8%–99.0% | 24.929 | 6.050 | 4.121 | — | 993–1068 |
| 2005 | Ridge | 90% | 103 | 100 | 97.1% | 91.3%–100.0% | 31.987 | 6.050 | 5.287 | — | 993–1068 |
| 2005 | Random forest | 80% | 103 | 97 | 94.2% | 87.1%–99.1% | 23.929 | 6.050 | 3.955 | — | 993–1068 |
| 2005 | Random forest | 90% | 103 | 100 | 97.1% | 92.4%–100.0% | 32.125 | 6.050 | 5.310 | — | 993–1068 |
| 2006 | Ridge | 80% | 103 | 78 | 75.7% | 58.1%–90.8% | 24.929 | 12.149 | 2.052 | Yes | 993–1068 |
| 2006 | Ridge | 90% | 103 | 90 | 87.4% | 79.8%–94.6% | 31.987 | 12.149 | 2.633 | Yes | 993–1068 |
| 2006 | Random forest | 80% | 103 | 82 | 79.6% | 59.5%–93.0% | 23.929 | 12.149 | 1.970 | Yes | 993–1068 |
| 2006 | Random forest | 90% | 103 | 92 | 89.3% | 78.2%–96.6% | 32.125 | 12.149 | 2.644 | Yes | 993–1068 |
| 2007 | Ridge | 80% | 103 | 50 | 48.5% | 23.2%–75.8% | 24.929 | 15.327 | 1.626 | Yes | 993–1068 |
| 2007 | Ridge | 90% | 103 | 64 | 62.1% | 36.2%–86.8% | 31.987 | 15.327 | 2.087 | Yes | 993–1068 |
| 2007 | Random forest | 80% | 103 | 61 | 59.2% | 35.5%–83.3% | 23.929 | 15.327 | 1.561 | Yes | 993–1068 |
| 2007 | Random forest | 90% | 103 | 72 | 69.9% | 48.2%–91.7% | 32.125 | 15.327 | 2.096 | Yes | 993–1068 |
| 2008 | Ridge | 80% | 93 | 77 | 82.8% | 65.2%–97.6% | 24.942 | 7.845 | 3.179 | — | 993–1068 |
| 2008 | Ridge | 90% | 93 | 86 | 92.5% | 83.9%–98.8% | 31.975 | 7.845 | 4.076 | — | 993–1068 |
| 2008 | Random forest | 80% | 93 | 86 | 92.5% | 83.9%–98.8% | 23.887 | 7.845 | 3.045 | — | 993–1068 |
| 2008 | Random forest | 90% | 93 | 91 | 97.8% | 94.9%–100.0% | 31.992 | 7.845 | 4.078 | — | 993–1068 |
| 2009 | Ridge | 80% | 103 | 87 | 84.5% | 70.7%–96.1% | 24.929 | 9.184 | 2.714 | — | 993–1068 |
| 2009 | Ridge | 90% | 103 | 92 | 89.3% | 77.4%–100.0% | 31.987 | 9.184 | 3.483 | Yes | 993–1068 |
| 2009 | Random forest | 80% | 103 | 85 | 82.5% | 67.2%–96.2% | 23.929 | 9.184 | 2.605 | — | 993–1068 |
| 2009 | Random forest | 90% | 103 | 95 | 92.2% | 84.4%–99.0% | 32.125 | 9.184 | 3.498 | — | 993–1068 |
| 2010 | Ridge | 80% | 97 | 85 | 87.6% | 75.7%–97.9% | 24.948 | 9.043 | 2.759 | — | 993–1068 |
| 2010 | Ridge | 90% | 97 | 93 | 95.9% | 87.1%–100.0% | 31.971 | 9.043 | 3.535 | — | 993–1068 |
| 2010 | Random forest | 80% | 97 | 90 | 92.8% | 86.0%–98.1% | 23.884 | 9.043 | 2.641 | — | 993–1068 |
| 2010 | Random forest | 90% | 97 | 96 | 99.0% | 96.7%–100.0% | 31.982 | 9.043 | 3.536 | — | 993–1068 |
| 2011 | Ridge | 80% | 102 | 87 | 85.3% | 72.8%–94.4% | 24.933 | 9.601 | 2.597 | — | 993–1068 |
| 2011 | Ridge | 90% | 102 | 94 | 92.2% | 82.5%–99.0% | 31.997 | 9.601 | 3.333 | — | 993–1068 |
| 2011 | Random forest | 80% | 102 | 92 | 90.2% | 81.2%–97.2% | 23.957 | 9.601 | 2.495 | — | 993–1068 |
| 2011 | Random forest | 90% | 102 | 99 | 97.1% | 94.0%–99.1% | 32.160 | 9.601 | 3.350 | — | 993–1068 |
| 2012 | Ridge | 80% | 96 | 84 | 87.5% | 71.7%–98.0% | 24.925 | 11.093 | 2.247 | — | 993–1068 |
| 2012 | Ridge | 90% | 96 | 88 | 91.7% | 79.6%–100.0% | 31.982 | 11.093 | 2.883 | — | 993–1068 |
| 2012 | Random forest | 80% | 96 | 84 | 87.5% | 78.9%–94.0% | 23.952 | 11.093 | 2.159 | — | 993–1068 |
| 2012 | Random forest | 90% | 96 | 92 | 95.8% | 91.6%–100.0% | 32.115 | 11.093 | 2.895 | — | 993–1068 |
| 2013 | Ridge | 80% | 86 | 37 | 43.0% | 24.4%–58.9% | 24.884 | 15.805 | 1.574 | Yes | 993–1068 |
| 2013 | Ridge | 90% | 86 | 58 | 67.4% | 52.0%–80.2% | 31.957 | 15.805 | 2.022 | Yes | 993–1068 |
| 2013 | Random forest | 80% | 86 | 45 | 52.3% | 34.8%–69.1% | 23.940 | 15.805 | 1.515 | Yes | 993–1068 |
| 2013 | Random forest | 90% | 86 | 64 | 74.4% | 58.3%–89.4% | 32.128 | 15.805 | 2.033 | Yes | 993–1068 |
| 2014 | Ridge | 80% | 84 | 67 | 79.8% | 62.6%–93.3% | 24.944 | 12.516 | 1.993 | Yes | 993–1068 |
| 2014 | Ridge | 90% | 84 | 72 | 85.7% | 70.6%–97.6% | 32.001 | 12.516 | 2.557 | Yes | 993–1068 |
| 2014 | Random forest | 80% | 84 | 65 | 77.4% | 58.4%–93.6% | 23.958 | 12.516 | 1.914 | Yes | 993–1068 |
| 2014 | Random forest | 90% | 84 | 73 | 86.9% | 71.4%–100.0% | 32.176 | 12.516 | 2.571 | Yes | 993–1068 |
| 2015 | Ridge | 80% | 81 | 73 | 90.1% | 80.5%–97.1% | 24.922 | 7.218 | 3.453 | — | 993–1068 |
| 2015 | Ridge | 90% | 81 | 77 | 95.1% | 84.4%–100.0% | 32.010 | 7.218 | 4.435 | — | 993–1068 |
| 2015 | Random forest | 80% | 81 | 65 | 80.2% | 70.7%–89.7% | 23.981 | 7.218 | 3.323 | — | 993–1068 |
| 2015 | Random forest | 90% | 81 | 75 | 92.6% | 82.0%–100.0% | 32.224 | 7.218 | 4.465 | — | 993–1068 |
| 2016 | Ridge | 80% | 80 | 42 | 52.5% | 34.7%–67.9% | 24.884 | 17.812 | 1.397 | Yes | 993–1068 |
| 2016 | Ridge | 90% | 80 | 60 | 75.0% | 59.7%–86.5% | 31.953 | 17.812 | 1.794 | Yes | 993–1068 |
| 2016 | Random forest | 80% | 80 | 46 | 57.5% | 41.5%–72.1% | 23.892 | 17.812 | 1.341 | Yes | 993–1068 |
| 2016 | Random forest | 90% | 80 | 61 | 76.2% | 58.4%–91.2% | 32.150 | 17.812 | 1.805 | Yes | 993–1068 |
| 2017 | Ridge | 80% | 75 | 33 | 44.0% | 30.1%–57.0% | 24.854 | 14.121 | 1.760 | Yes | 993–1068 |
| 2017 | Ridge | 90% | 75 | 57 | 76.0% | 59.5%–90.8% | 31.939 | 14.121 | 2.262 | Yes | 993–1068 |
| 2017 | Random forest | 80% | 75 | 49 | 65.3% | 47.1%–81.9% | 23.912 | 14.121 | 1.693 | Yes | 993–1068 |
| 2017 | Random forest | 90% | 75 | 59 | 78.7% | 62.8%–93.6% | 32.057 | 14.121 | 2.270 | Yes | 993–1068 |
| 2018 | Ridge | 80% | 65 | 55 | 84.6% | 73.5%–96.8% | 24.874 | 7.969 | 3.121 | — | 993–1068 |
| 2018 | Ridge | 90% | 65 | 64 | 98.5% | 95.7%–100.0% | 31.980 | 7.969 | 4.013 | — | 993–1068 |
| 2018 | Random forest | 80% | 65 | 58 | 89.2% | 81.9%–95.7% | 23.958 | 7.969 | 3.006 | — | 993–1068 |
| 2018 | Random forest | 90% | 65 | 63 | 96.9% | 91.4%–100.0% | 32.242 | 7.969 | 4.046 | — | 993–1068 |
| 2019 | Ridge | 80% | 64 | 53 | 82.8% | 60.9%–96.4% | 24.863 | 13.310 | 1.868 | — | 993–1068 |
| 2019 | Ridge | 90% | 64 | 54 | 84.4% | 65.5%–96.6% | 32.005 | 13.310 | 2.405 | Yes | 993–1068 |
| 2019 | Random forest | 80% | 64 | 47 | 73.4% | 54.2%–87.7% | 23.996 | 13.310 | 1.803 | Yes | 993–1068 |
| 2019 | Random forest | 90% | 64 | 54 | 84.4% | 71.2%–94.3% | 32.293 | 13.310 | 2.426 | Yes | 993–1068 |
| 2020 | Ridge | 80% | 94 | 91 | 96.8% | 92.9%–100.0% | 24.970 | 8.055 | 3.100 | — | 993–1068 |
| 2020 | Ridge | 90% | 94 | 94 | 100.0% | 100.0%–100.0% | 32.005 | 8.055 | 3.973 | — | 993–1068 |
| 2020 | Random forest | 80% | 94 | 89 | 94.7% | 88.2%–99.0% | 23.950 | 8.055 | 2.973 | — | 993–1068 |
| 2020 | Random forest | 90% | 94 | 93 | 98.9% | 96.8%–100.0% | 32.074 | 8.055 | 3.982 | — | 993–1068 |
| 2021 | Ridge | 80% | 85 | 64 | 75.3% | 62.3%–86.2% | 24.908 | 14.899 | 1.672 | Yes | 993–1068 |
| 2021 | Ridge | 90% | 85 | 72 | 84.7% | 73.3%–93.8% | 31.994 | 14.899 | 2.147 | Yes | 993–1068 |
| 2021 | Random forest | 80% | 85 | 61 | 71.8% | 53.1%–89.3% | 23.974 | 14.899 | 1.609 | Yes | 993–1068 |
| 2021 | Random forest | 90% | 85 | 72 | 84.7% | 72.6%–93.9% | 32.287 | 14.899 | 2.167 | Yes | 993–1068 |
| 2022 | Ridge | 80% | 87 | 62 | 71.3% | 54.4%–87.3% | 24.895 | 11.885 | 2.095 | Yes | 993–1068 |
| 2022 | Ridge | 90% | 87 | 76 | 87.4% | 70.0%–98.7% | 31.964 | 11.885 | 2.689 | Yes | 993–1068 |
| 2022 | Random forest | 80% | 87 | 62 | 71.3% | 48.2%–94.9% | 23.874 | 11.885 | 2.009 | Yes | 993–1068 |
| 2022 | Random forest | 90% | 87 | 70 | 80.5% | 63.4%–97.5% | 32.100 | 11.885 | 2.701 | Yes | 993–1068 |
| 2023 | Ridge | 80% | 69 | 47 | 68.1% | 50.0%–84.6% | 24.839 | 15.646 | 1.588 | Yes | 993–1068 |
| 2023 | Ridge | 90% | 69 | 57 | 82.6% | 65.7%–95.8% | 31.968 | 15.646 | 2.043 | Yes | 993–1068 |
| 2023 | Random forest | 80% | 69 | 45 | 65.2% | 46.5%–81.7% | 23.912 | 15.646 | 1.528 | Yes | 993–1068 |
| 2023 | Random forest | 90% | 69 | 51 | 73.9% | 57.9%–87.5% | 32.186 | 15.646 | 2.057 | Yes | 993–1068 |

</details>

| Evaluation | Model | Nominal | County-years | Covered | Coverage | 95% interval | Mean width | County-mean RMSE | Width / RMSE | Below nominal | Calibration rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| low annual yield slice | Ridge | 80% | 412 | 315 | 76.5% | 71.4%–82.8% | 24.929 | 13.526 | 1.843 | Yes | 993–1068 |
| low annual yield slice | Ridge | 90% | 412 | 352 | 85.4% | 80.1%–91.4% | 31.987 | 13.526 | 2.365 | Yes | 993–1068 |
| low annual yield slice | Random forest | 80% | 412 | 339 | 82.3% | 73.5%–90.0% | 23.929 | 13.526 | 1.769 | — | 993–1068 |
| low annual yield slice | Random forest | 90% | 412 | 371 | 90.0% | 84.5%–95.3% | 32.125 | 13.526 | 2.375 | — | 993–1068 |
| high annual yield slice | Ridge | 80% | 343 | 199 | 58.0% | 45.4%–68.2% | 24.897 | 15.945 | 1.561 | Yes | 993–1068 |
| high annual yield slice | Ridge | 90% | 343 | 262 | 76.4% | 66.2%–85.3% | 31.970 | 15.945 | 2.005 | Yes | 993–1068 |
| high annual yield slice | Random forest | 80% | 343 | 213 | 62.1% | 50.9%–72.8% | 23.928 | 15.945 | 1.501 | Yes | 993–1068 |
| high annual yield slice | Random forest | 90% | 343 | 265 | 77.3% | 65.4%–87.7% | 32.156 | 15.945 | 2.017 | Yes | 993–1068 |

Below-nominal outer folds out of 9 · Ridge 80% 3, Ridge 90% 2, Random forest 80% 4, Random forest 90% 2.

#### Harvest-year holdout

<details>
<summary>All outer folds</summary>

| Evaluation | Model | Nominal | County-years | Covered | Coverage | 95% interval | Mean width | County-mean RMSE | Width / RMSE | Below nominal | Calibration rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1990 | Ridge | 80% | 103 | 83 | 80.6% | 62.4%–93.4% | 22.797 | 7.738 | 2.946 | — | 1038 |
| 1990 | Ridge | 90% | 103 | 91 | 88.3% | 70.6%–99.0% | 29.698 | 7.738 | 3.838 | Yes | 1038 |
| 1990 | Random forest | 80% | 103 | 80 | 77.7% | 55.3%–93.8% | 20.708 | 7.738 | 2.676 | Yes | 1038 |
| 1990 | Random forest | 90% | 103 | 90 | 87.4% | 67.6%–100.0% | 26.514 | 7.738 | 3.426 | Yes | 1038 |
| 1991 | Ridge | 80% | 103 | 97 | 94.2% | 89.7%–97.4% | 22.945 | 9.198 | 2.495 | — | 1038 |
| 1991 | Ridge | 90% | 103 | 103 | 100.0% | 100.0%–100.0% | 29.785 | 9.198 | 3.238 | — | 1038 |
| 1991 | Random forest | 80% | 103 | 85 | 82.5% | 68.5%–93.8% | 20.410 | 9.198 | 2.219 | — | 1038 |
| 1991 | Random forest | 90% | 103 | 95 | 92.2% | 81.8%–100.0% | 26.190 | 9.198 | 2.847 | — | 1038 |
| 1992 | Ridge | 80% | 103 | 87 | 84.5% | 71.9%–94.1% | 22.999 | 8.779 | 2.620 | — | 1038 |
| 1992 | Ridge | 90% | 103 | 98 | 95.1% | 92.4%–98.1% | 29.429 | 8.779 | 3.352 | — | 1038 |
| 1992 | Random forest | 80% | 103 | 73 | 70.9% | 57.6%–84.9% | 20.937 | 8.779 | 2.385 | Yes | 1038 |
| 1992 | Random forest | 90% | 103 | 80 | 77.7% | 63.5%–91.8% | 26.844 | 8.779 | 3.058 | Yes | 1038 |
| 1993 | Ridge | 80% | 103 | 67 | 65.0% | 42.3%–84.1% | 22.135 | 12.582 | 1.759 | Yes | 1038 |
| 1993 | Ridge | 90% | 103 | 81 | 78.6% | 56.4%–95.5% | 28.486 | 12.582 | 2.264 | Yes | 1038 |
| 1993 | Random forest | 80% | 103 | 79 | 76.7% | 58.6%–91.0% | 21.075 | 12.582 | 1.675 | Yes | 1038 |
| 1993 | Random forest | 90% | 103 | 93 | 90.3% | 79.4%–100.0% | 27.757 | 12.582 | 2.206 | — | 1038 |
| 1994 | Ridge | 80% | 103 | 103 | 100.0% | 100.0%–100.0% | 21.695 | 3.969 | 5.467 | — | 1038 |
| 1994 | Ridge | 90% | 103 | 103 | 100.0% | 100.0%–100.0% | 28.072 | 3.969 | 7.073 | — | 1038 |
| 1994 | Random forest | 80% | 103 | 94 | 91.3% | 75.7%–100.0% | 21.670 | 3.969 | 5.460 | — | 1038 |
| 1994 | Random forest | 90% | 103 | 97 | 94.2% | 82.5%–100.0% | 27.600 | 3.969 | 6.954 | — | 1038 |
| 1995 | Ridge | 80% | 103 | 75 | 72.8% | 52.9%–89.6% | 22.371 | 17.030 | 1.314 | Yes | 1038 |
| 1995 | Ridge | 90% | 103 | 88 | 85.4% | 68.5%–98.0% | 28.214 | 17.030 | 1.657 | Yes | 1038 |
| 1995 | Random forest | 80% | 103 | 58 | 56.3% | 36.1%–74.7% | 20.569 | 17.030 | 1.208 | Yes | 1038 |
| 1995 | Random forest | 90% | 103 | 80 | 77.7% | 61.9%–92.3% | 26.741 | 17.030 | 1.570 | Yes | 1038 |
| 1996 | Ridge | 80% | 103 | 93 | 90.3% | 82.3%–97.8% | 23.075 | 12.639 | 1.826 | — | 1038 |
| 1996 | Ridge | 90% | 103 | 101 | 98.1% | 94.3%–100.0% | 28.957 | 12.639 | 2.291 | — | 1038 |
| 1996 | Random forest | 80% | 103 | 96 | 93.2% | 86.4%–98.1% | 22.230 | 12.639 | 1.759 | — | 1038 |
| 1996 | Random forest | 90% | 103 | 101 | 98.1% | 95.5%–100.0% | 28.836 | 12.639 | 2.282 | — | 1038 |
| 1997 | Ridge | 80% | 103 | 87 | 84.5% | 69.2%–95.4% | 22.718 | 9.959 | 2.281 | — | 1038 |
| 1997 | Ridge | 90% | 103 | 94 | 91.3% | 80.2%–100.0% | 28.051 | 9.959 | 2.816 | — | 1038 |
| 1997 | Random forest | 80% | 103 | 64 | 62.1% | 45.0%–79.8% | 22.070 | 9.959 | 2.216 | Yes | 1038 |
| 1997 | Random forest | 90% | 103 | 83 | 80.6% | 61.4%–94.1% | 28.853 | 9.959 | 2.897 | Yes | 1038 |
| 1998 | Ridge | 80% | 103 | 82 | 79.6% | 62.6%–93.5% | 22.435 | 10.323 | 2.173 | Yes | 1038 |
| 1998 | Ridge | 90% | 103 | 92 | 89.3% | 78.7%–97.4% | 28.235 | 10.323 | 2.735 | Yes | 1038 |
| 1998 | Random forest | 80% | 103 | 78 | 75.7% | 62.5%–87.0% | 21.582 | 10.323 | 2.091 | Yes | 1038 |
| 1998 | Random forest | 90% | 103 | 94 | 91.3% | 81.1%–98.2% | 28.044 | 10.323 | 2.717 | — | 1038 |
| 1999 | Ridge | 80% | 103 | 88 | 85.4% | 74.3%–95.4% | 22.609 | 10.057 | 2.248 | — | 1038 |
| 1999 | Ridge | 90% | 103 | 97 | 94.2% | 84.0%–100.0% | 28.665 | 10.057 | 2.850 | — | 1038 |
| 1999 | Random forest | 80% | 103 | 79 | 76.7% | 62.6%–88.9% | 21.641 | 10.057 | 2.152 | Yes | 1038 |
| 1999 | Random forest | 90% | 103 | 94 | 91.3% | 83.8%–97.2% | 28.044 | 10.057 | 2.789 | — | 1038 |
| 2000 | Ridge | 80% | 103 | 98 | 95.1% | 89.5%–100.0% | 23.258 | 4.433 | 5.247 | — | 1038 |
| 2000 | Ridge | 90% | 103 | 102 | 99.0% | 96.7%–100.0% | 29.191 | 4.433 | 6.585 | — | 1038 |
| 2000 | Random forest | 80% | 103 | 101 | 98.1% | 95.3%–100.0% | 22.423 | 4.433 | 5.059 | — | 1038 |
| 2000 | Random forest | 90% | 103 | 103 | 100.0% | 100.0%–100.0% | 29.356 | 4.433 | 6.623 | — | 1038 |
| 2001 | Ridge | 80% | 103 | 95 | 92.2% | 85.7%–98.0% | 23.062 | 6.365 | 3.623 | — | 1038 |
| 2001 | Ridge | 90% | 103 | 100 | 97.1% | 93.0%–100.0% | 29.181 | 6.365 | 4.585 | — | 1038 |
| 2001 | Random forest | 80% | 103 | 84 | 81.6% | 67.6%–95.5% | 22.390 | 6.365 | 3.518 | — | 1038 |
| 2001 | Random forest | 90% | 103 | 89 | 86.4% | 73.6%–100.0% | 28.258 | 6.365 | 4.440 | Yes | 1038 |
| 2002 | Ridge | 80% | 103 | 85 | 82.5% | 69.5%–93.5% | 22.710 | 9.677 | 2.347 | — | 1038 |
| 2002 | Ridge | 90% | 103 | 93 | 90.3% | 82.6%–96.7% | 28.692 | 9.677 | 2.965 | — | 1038 |
| 2002 | Random forest | 80% | 103 | 95 | 92.2% | 85.9%–97.1% | 22.789 | 9.677 | 2.355 | — | 1038 |
| 2002 | Random forest | 90% | 103 | 102 | 99.0% | 96.8%–100.0% | 29.393 | 9.677 | 3.037 | — | 1038 |
| 2003 | Ridge | 80% | 103 | 55 | 53.4% | 31.9%–76.3% | 22.200 | 14.862 | 1.494 | Yes | 1038 |
| 2003 | Ridge | 90% | 103 | 66 | 64.1% | 43.8%–83.1% | 28.264 | 14.862 | 1.902 | Yes | 1038 |
| 2003 | Random forest | 80% | 103 | 53 | 51.5% | 29.9%–75.7% | 23.060 | 14.862 | 1.552 | Yes | 1038 |
| 2003 | Random forest | 90% | 103 | 61 | 59.2% | 38.3%–81.3% | 28.943 | 14.862 | 1.947 | Yes | 1038 |
| 2004 | Ridge | 80% | 103 | 92 | 89.3% | 76.1%–97.5% | 22.585 | 10.996 | 2.054 | — | 1038 |
| 2004 | Ridge | 90% | 103 | 96 | 93.2% | 79.6%–100.0% | 28.655 | 10.996 | 2.606 | — | 1038 |
| 2004 | Random forest | 80% | 103 | 89 | 86.4% | 69.1%–98.2% | 23.323 | 10.996 | 2.121 | — | 1038 |
| 2004 | Random forest | 90% | 103 | 98 | 95.1% | 84.9%–100.0% | 29.485 | 10.996 | 2.681 | — | 1038 |
| 2005 | Ridge | 80% | 103 | 94 | 91.3% | 83.2%–100.0% | 22.654 | 6.375 | 3.554 | — | 1038 |
| 2005 | Ridge | 90% | 103 | 100 | 97.1% | 94.2%–100.0% | 28.817 | 6.375 | 4.521 | — | 1038 |
| 2005 | Random forest | 80% | 103 | 95 | 92.2% | 86.0%–97.3% | 23.666 | 6.375 | 3.712 | — | 1038 |
| 2005 | Random forest | 90% | 103 | 100 | 97.1% | 93.6%–100.0% | 29.862 | 6.375 | 4.684 | — | 1038 |
| 2006 | Ridge | 80% | 103 | 84 | 81.6% | 62.9%–95.2% | 23.172 | 11.300 | 2.051 | — | 1038 |
| 2006 | Ridge | 90% | 103 | 90 | 87.4% | 73.2%–96.6% | 29.021 | 11.300 | 2.568 | Yes | 1038 |
| 2006 | Random forest | 80% | 103 | 86 | 83.5% | 65.6%–94.8% | 23.622 | 11.300 | 2.090 | — | 1038 |
| 2006 | Random forest | 90% | 103 | 95 | 92.2% | 80.9%–100.0% | 29.984 | 11.300 | 2.653 | — | 1038 |
| 2007 | Ridge | 80% | 103 | 40 | 38.8% | 15.1%–68.5% | 22.613 | 17.253 | 1.311 | Yes | 1038 |
| 2007 | Ridge | 90% | 103 | 48 | 46.6% | 21.9%–76.0% | 28.319 | 17.253 | 1.641 | Yes | 1038 |
| 2007 | Random forest | 80% | 103 | 32 | 31.1% | 7.8%–60.0% | 23.247 | 17.253 | 1.347 | Yes | 1038 |
| 2007 | Random forest | 90% | 103 | 39 | 37.9% | 15.3%–66.4% | 28.754 | 17.253 | 1.667 | Yes | 1038 |
| 2008 | Ridge | 80% | 93 | 71 | 76.3% | 52.2%–94.2% | 22.406 | 8.006 | 2.798 | Yes | 1040 |
| 2008 | Ridge | 90% | 93 | 78 | 83.9% | 62.4%–100.0% | 29.075 | 8.006 | 3.632 | Yes | 1040 |
| 2008 | Random forest | 80% | 93 | 77 | 82.8% | 69.7%–94.8% | 20.237 | 8.006 | 2.528 | — | 1040 |
| 2008 | Random forest | 90% | 93 | 88 | 94.6% | 89.5%–100.0% | 26.148 | 8.006 | 3.266 | — | 1040 |
| 2009 | Ridge | 80% | 103 | 91 | 88.3% | 73.0%–99.0% | 24.696 | 7.673 | 3.219 | — | 1038 |
| 2009 | Ridge | 90% | 103 | 98 | 95.1% | 85.4%–100.0% | 34.007 | 7.673 | 4.432 | — | 1038 |
| 2009 | Random forest | 80% | 103 | 87 | 84.5% | 67.9%–98.0% | 25.776 | 7.673 | 3.359 | — | 1038 |
| 2009 | Random forest | 90% | 103 | 98 | 95.1% | 87.7%–100.0% | 33.700 | 7.673 | 4.392 | — | 1038 |
| 2010 | Ridge | 80% | 97 | 79 | 81.4% | 63.2%–96.6% | 23.237 | 10.207 | 2.277 | — | 1039 |
| 2010 | Ridge | 90% | 97 | 88 | 90.7% | 77.8%–100.0% | 29.982 | 10.207 | 2.937 | — | 1039 |
| 2010 | Random forest | 80% | 97 | 84 | 86.6% | 74.5%–97.8% | 21.383 | 10.207 | 2.095 | — | 1039 |
| 2010 | Random forest | 90% | 97 | 89 | 91.8% | 82.9%–100.0% | 27.207 | 10.207 | 2.665 | — | 1039 |
| 2011 | Ridge | 80% | 102 | 95 | 93.1% | 85.0%–99.1% | 25.989 | 7.995 | 3.251 | — | 1038 |
| 2011 | Ridge | 90% | 102 | 100 | 98.0% | 95.3%–100.0% | 31.721 | 7.995 | 3.968 | — | 1038 |
| 2011 | Random forest | 80% | 102 | 93 | 91.2% | 85.7%–96.8% | 23.066 | 7.995 | 2.885 | — | 1038 |
| 2011 | Random forest | 90% | 102 | 98 | 96.1% | 93.0%–99.0% | 28.917 | 7.995 | 3.617 | — | 1038 |
| 2012 | Ridge | 80% | 96 | 83 | 86.5% | 75.2%–94.7% | 23.345 | 8.659 | 2.696 | — | 1039 |
| 2012 | Ridge | 90% | 96 | 89 | 92.7% | 84.7%–98.9% | 29.459 | 8.659 | 3.402 | — | 1039 |
| 2012 | Random forest | 80% | 96 | 75 | 78.1% | 66.3%–88.5% | 21.062 | 8.659 | 2.432 | Yes | 1039 |
| 2012 | Random forest | 90% | 96 | 85 | 88.5% | 80.4%–96.2% | 26.080 | 8.659 | 3.012 | Yes | 1039 |
| 2013 | Ridge | 80% | 86 | 38 | 44.2% | 25.7%–58.1% | 23.505 | 13.129 | 1.790 | Yes | 1043 |
| 2013 | Ridge | 90% | 86 | 67 | 77.9% | 64.9%–87.9% | 30.841 | 13.129 | 2.349 | Yes | 1043 |
| 2013 | Random forest | 80% | 86 | 52 | 60.5% | 36.3%–81.7% | 22.097 | 13.129 | 1.683 | Yes | 1043 |
| 2013 | Random forest | 90% | 86 | 61 | 70.9% | 50.0%–88.5% | 27.422 | 13.129 | 2.089 | Yes | 1043 |
| 2014 | Ridge | 80% | 84 | 56 | 66.7% | 47.4%–83.8% | 24.872 | 11.576 | 2.149 | Yes | 1044 |
| 2014 | Ridge | 90% | 84 | 70 | 83.3% | 67.0%–96.2% | 32.695 | 11.576 | 2.824 | Yes | 1044 |
| 2014 | Random forest | 80% | 84 | 43 | 51.2% | 26.5%–74.1% | 22.554 | 11.576 | 1.948 | Yes | 1044 |
| 2014 | Random forest | 90% | 84 | 62 | 73.8% | 56.4%–87.7% | 28.461 | 11.576 | 2.459 | Yes | 1044 |
| 2015 | Ridge | 80% | 81 | 68 | 84.0% | 71.4%–94.7% | 24.910 | 7.128 | 3.495 | — | 1044 |
| 2015 | Ridge | 90% | 81 | 78 | 96.3% | 93.3%–98.9% | 31.577 | 7.128 | 4.430 | — | 1044 |
| 2015 | Random forest | 80% | 81 | 66 | 81.5% | 73.1%–89.4% | 21.607 | 7.128 | 3.031 | — | 1044 |
| 2015 | Random forest | 90% | 81 | 79 | 97.5% | 93.9%–100.0% | 28.304 | 7.128 | 3.971 | — | 1044 |
| 2016 | Ridge | 80% | 80 | 40 | 50.0% | 31.9%–66.3% | 25.013 | 16.999 | 1.471 | Yes | 1044 |
| 2016 | Ridge | 90% | 80 | 57 | 71.2% | 53.3%–85.1% | 32.533 | 16.999 | 1.914 | Yes | 1044 |
| 2016 | Random forest | 80% | 80 | 43 | 53.8% | 27.3%–72.8% | 22.814 | 16.999 | 1.342 | Yes | 1044 |
| 2016 | Random forest | 90% | 80 | 55 | 68.8% | 43.7%–85.7% | 28.756 | 16.999 | 1.692 | Yes | 1044 |
| 2017 | Ridge | 80% | 75 | 32 | 42.7% | 28.2%–59.0% | 24.816 | 12.239 | 2.028 | Yes | 1049 |
| 2017 | Ridge | 90% | 75 | 47 | 62.7% | 48.1%–77.3% | 32.273 | 12.239 | 2.637 | Yes | 1049 |
| 2017 | Random forest | 80% | 75 | 36 | 48.0% | 37.5%–60.3% | 22.718 | 12.239 | 1.856 | Yes | 1049 |
| 2017 | Random forest | 90% | 75 | 56 | 74.7% | 61.5%–88.5% | 28.982 | 12.239 | 2.368 | Yes | 1049 |
| 2018 | Ridge | 80% | 65 | 65 | 100.0% | 100.0%–100.0% | 26.804 | 6.357 | 4.216 | — | 1055 |
| 2018 | Ridge | 90% | 65 | 65 | 100.0% | 100.0%–100.0% | 33.310 | 6.357 | 5.240 | — | 1055 |
| 2018 | Random forest | 80% | 65 | 57 | 87.7% | 82.1%–93.9% | 23.462 | 6.357 | 3.691 | — | 1055 |
| 2018 | Random forest | 90% | 65 | 63 | 96.9% | 93.0%–100.0% | 28.941 | 6.357 | 4.553 | — | 1055 |
| 2019 | Ridge | 80% | 64 | 45 | 70.3% | 44.4%–90.0% | 27.020 | 14.030 | 1.926 | Yes | 1055 |
| 2019 | Ridge | 90% | 64 | 54 | 84.4% | 62.2%–97.6% | 33.429 | 14.030 | 2.383 | Yes | 1055 |
| 2019 | Random forest | 80% | 64 | 32 | 50.0% | 38.1%–63.2% | 23.060 | 14.030 | 1.644 | Yes | 1055 |
| 2019 | Random forest | 90% | 64 | 46 | 71.9% | 55.2%–84.6% | 29.529 | 14.030 | 2.105 | Yes | 1055 |
| 2020 | Ridge | 80% | 94 | 84 | 89.4% | 79.3%–97.1% | 22.785 | 7.750 | 2.940 | — | 1040 |
| 2020 | Ridge | 90% | 94 | 93 | 98.9% | 96.8%–100.0% | 28.605 | 7.750 | 3.691 | — | 1040 |
| 2020 | Random forest | 80% | 94 | 82 | 87.2% | 76.9%–95.7% | 20.962 | 7.750 | 2.705 | — | 1040 |
| 2020 | Random forest | 90% | 94 | 87 | 92.6% | 84.8%–98.1% | 27.286 | 7.750 | 3.521 | — | 1040 |
| 2021 | Ridge | 80% | 85 | 65 | 76.5% | 60.6%–89.7% | 24.778 | 14.337 | 1.728 | Yes | 1044 |
| 2021 | Ridge | 90% | 85 | 73 | 85.9% | 73.7%–95.0% | 31.295 | 14.337 | 2.183 | Yes | 1044 |
| 2021 | Random forest | 80% | 85 | 61 | 71.8% | 46.0%–90.8% | 22.383 | 14.337 | 1.561 | Yes | 1044 |
| 2021 | Random forest | 90% | 85 | 67 | 78.8% | 57.8%–95.0% | 27.656 | 14.337 | 1.929 | Yes | 1044 |
| 2022 | Ridge | 80% | 87 | 62 | 71.3% | 52.1%–88.9% | 24.054 | 9.312 | 2.583 | Yes | 1043 |
| 2022 | Ridge | 90% | 87 | 78 | 89.7% | 77.4%–100.0% | 30.811 | 9.312 | 3.309 | Yes | 1043 |
| 2022 | Random forest | 80% | 87 | 70 | 80.5% | 69.0%–90.1% | 22.114 | 9.312 | 2.375 | — | 1043 |
| 2022 | Random forest | 90% | 87 | 78 | 89.7% | 80.0%–96.5% | 29.114 | 9.312 | 3.127 | Yes | 1043 |
| 2023 | Ridge | 80% | 69 | 56 | 81.2% | 70.6%–89.6% | 26.484 | 13.657 | 1.939 | — | 1055 |
| 2023 | Ridge | 90% | 69 | 62 | 89.9% | 83.9%–95.1% | 33.446 | 13.657 | 2.449 | Yes | 1055 |
| 2023 | Random forest | 80% | 69 | 47 | 68.1% | 53.7%–83.1% | 23.329 | 13.657 | 1.708 | Yes | 1055 |
| 2023 | Random forest | 90% | 69 | 54 | 78.3% | 66.7%–90.4% | 29.099 | 13.657 | 2.131 | Yes | 1055 |

</details>

<details>
<summary>All cross-cutting district diagnostics</summary>

| Evaluation | Model | Nominal | County-years | Covered | Coverage | 95% interval | Mean width | County-mean RMSE | Width / RMSE | Below nominal | Calibration rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | Ridge | 80% | 237 | 177 | 74.7% | 66.2%–82.3% | 23.332 | 11.674 | 1.999 | Yes | 1038–1055 |
| 10 | Ridge | 90% | 237 | 204 | 86.1% | 78.2%–92.7% | 29.735 | 11.674 | 2.547 | Yes | 1038–1055 |
| 10 | Random forest | 80% | 237 | 173 | 73.0% | 63.5%–81.3% | 22.157 | 11.674 | 1.898 | Yes | 1038–1055 |
| 10 | Random forest | 90% | 237 | 198 | 83.5% | 76.3%–89.4% | 28.334 | 11.674 | 2.427 | Yes | 1038–1055 |
| 20 | Ridge | 80% | 275 | 220 | 80.0% | 72.7%–86.5% | 23.427 | 11.329 | 2.068 | — | 1038–1055 |
| 20 | Ridge | 90% | 275 | 250 | 90.9% | 85.7%–95.4% | 29.849 | 11.329 | 2.635 | — | 1038–1055 |
| 20 | Random forest | 80% | 275 | 203 | 73.8% | 65.0%–81.3% | 22.204 | 11.329 | 1.960 | Yes | 1038–1055 |
| 20 | Random forest | 90% | 275 | 242 | 88.0% | 81.7%–93.4% | 28.376 | 11.329 | 2.505 | Yes | 1038–1055 |
| 30 | Ridge | 80% | 424 | 304 | 71.7% | 62.5%–80.6% | 23.379 | 12.386 | 1.887 | Yes | 1038–1055 |
| 30 | Ridge | 90% | 424 | 357 | 84.2% | 76.3%–91.2% | 29.802 | 12.386 | 2.406 | Yes | 1038–1055 |
| 30 | Random forest | 80% | 424 | 307 | 72.4% | 62.0%–81.3% | 22.182 | 12.386 | 1.791 | Yes | 1038–1055 |
| 30 | Random forest | 90% | 424 | 355 | 83.7% | 75.1%–90.8% | 28.347 | 12.386 | 2.289 | Yes | 1038–1055 |
| 40 | Ridge | 80% | 349 | 278 | 79.7% | 69.9%–88.4% | 23.442 | 9.036 | 2.594 | Yes | 1038–1055 |
| 40 | Ridge | 90% | 349 | 308 | 88.3% | 80.5%–94.6% | 29.892 | 9.036 | 3.308 | Yes | 1038–1055 |
| 40 | Random forest | 80% | 349 | 268 | 76.8% | 66.7%–86.4% | 22.194 | 9.036 | 2.456 | Yes | 1038–1055 |
| 40 | Random forest | 90% | 349 | 303 | 86.8% | 78.7%–93.6% | 28.339 | 9.036 | 3.136 | Yes | 1038–1055 |
| 50 | Ridge | 80% | 352 | 288 | 81.8% | 72.4%–90.1% | 23.501 | 10.148 | 2.316 | — | 1038–1055 |
| 50 | Ridge | 90% | 352 | 317 | 90.1% | 82.5%–95.8% | 29.944 | 10.148 | 2.951 | — | 1038–1055 |
| 50 | Random forest | 80% | 352 | 273 | 77.6% | 67.1%–86.4% | 22.211 | 10.148 | 2.189 | Yes | 1038–1055 |
| 50 | Random forest | 90% | 352 | 302 | 85.8% | 77.4%–92.8% | 28.369 | 10.148 | 2.795 | Yes | 1038–1055 |
| 60 | Ridge | 80% | 418 | 343 | 82.1% | 73.2%–89.2% | 23.498 | 10.201 | 2.303 | — | 1038–1055 |
| 60 | Ridge | 90% | 418 | 383 | 91.6% | 85.9%–96.0% | 29.946 | 10.201 | 2.936 | — | 1038–1055 |
| 60 | Random forest | 80% | 418 | 334 | 79.9% | 70.8%–87.5% | 22.211 | 10.201 | 2.177 | Yes | 1038–1055 |
| 60 | Random forest | 90% | 418 | 375 | 89.7% | 81.3%–95.4% | 28.371 | 10.201 | 2.781 | Yes | 1038–1055 |
| 70 | Ridge | 80% | 277 | 205 | 74.0% | 62.4%–85.1% | 23.444 | 11.127 | 2.107 | Yes | 1038–1055 |
| 70 | Ridge | 90% | 277 | 235 | 84.8% | 73.8%–94.1% | 29.886 | 11.127 | 2.686 | Yes | 1038–1055 |
| 70 | Random forest | 80% | 277 | 199 | 71.8% | 61.2%–81.0% | 22.208 | 11.127 | 1.996 | Yes | 1038–1055 |
| 70 | Random forest | 90% | 277 | 237 | 85.6% | 76.4%–93.4% | 28.381 | 11.127 | 2.551 | Yes | 1038–1055 |
| 80 | Ridge | 80% | 442 | 364 | 82.4% | 72.3%–91.2% | 23.540 | 10.238 | 2.299 | — | 1038–1055 |
| 80 | Ridge | 90% | 442 | 392 | 88.7% | 79.5%–95.9% | 29.983 | 10.238 | 2.929 | Yes | 1038–1055 |
| 80 | Random forest | 80% | 442 | 344 | 77.8% | 68.8%–86.7% | 22.241 | 10.238 | 2.172 | Yes | 1038–1055 |
| 80 | Random forest | 90% | 442 | 387 | 87.6% | 78.8%–95.0% | 28.402 | 10.238 | 2.774 | Yes | 1038–1055 |
| 90 | Ridge | 80% | 441 | 356 | 80.7% | 72.0%–88.3% | 23.520 | 11.205 | 2.099 | — | 1038–1055 |
| 90 | Ridge | 90% | 441 | 394 | 89.3% | 81.0%–95.1% | 29.964 | 11.205 | 2.674 | Yes | 1038–1055 |
| 90 | Random forest | 80% | 441 | 325 | 73.7% | 64.1%–82.9% | 22.240 | 11.205 | 1.985 | Yes | 1038–1055 |
| 90 | Random forest | 90% | 441 | 361 | 81.9% | 72.8%–90.2% | 28.401 | 11.205 | 2.535 | Yes | 1038–1055 |

</details>

| Evaluation | Model | Nominal | County-years | Covered | Coverage | 95% interval | Mean width | County-mean RMSE | Width / RMSE | Below nominal | Calibration rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| low annual yield slice | Ridge | 80% | 412 | 275 | 66.7% | 45.4%–84.0% | 22.549 | 15.048 | 1.498 | Yes | 1038 |
| low annual yield slice | Ridge | 90% | 412 | 318 | 77.2% | 54.6%–93.2% | 28.494 | 15.048 | 1.894 | Yes | 1038 |
| low annual yield slice | Random forest | 80% | 412 | 265 | 64.3% | 42.5%–85.0% | 21.780 | 15.048 | 1.447 | Yes | 1038 |
| low annual yield slice | Random forest | 90% | 412 | 313 | 76.0% | 51.0%–94.2% | 28.022 | 15.048 | 1.862 | Yes | 1038 |
| high annual yield slice | Ridge | 80% | 343 | 192 | 56.0% | 46.0%–69.8% | 24.067 | 14.745 | 1.632 | Yes | 1038–1049 |
| high annual yield slice | Ridge | 90% | 343 | 243 | 70.8% | 63.5%–80.6% | 30.887 | 14.745 | 2.095 | Yes | 1038–1049 |
| high annual yield slice | Random forest | 80% | 343 | 193 | 56.3% | 49.5%–66.4% | 22.760 | 14.745 | 1.544 | Yes | 1038–1049 |
| high annual yield slice | Random forest | 90% | 343 | 239 | 69.7% | 62.2%–76.9% | 28.589 | 14.745 | 1.939 | Yes | 1038–1049 |

Below-nominal outer folds out of 34 · Ridge 80% 13, Ridge 90% 16, Random forest 80% 17, Random forest 90% 16.

The annual-mean yield extremes are low years 1995, 2007, 1996, 1993, and high years 2017, 2003, 2021, 2016. These are descriptive yield slices. They do not identify a cause of interval misses.

### Spatial transfer and P37 recalibration

The P32 transfer cohorts include all-practice fallback yields where preferred records are unavailable. These evaluate Kansas-only calibration across spatially held-out states, with overlapping harvest years. P37 separately uses the non-irrigated common test tail and Kansas data strictly before each district's test origin. At positive k the first k observed local years provide absolute residuals. Only the interval radius changes across k. The corresponding P37 county mean is unavailable at k = 0. The P32 and P37 cohorts differ.

#### Nebraska

| Evaluation | Model | Nominal | County-years | Covered | Coverage | 95% interval | Mean width | County-mean RMSE | Width / RMSE | Below nominal | Calibration rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kansas-calibrated P32 | Ridge | 80% | 1,733 | 1,310 | 75.6% | 70.7%–82.5% | 26.708 | 11.274 | 2.369 | Yes | 1068 |
| Kansas-calibrated P32 | Ridge | 90% | 1,733 | 1,478 | 85.3% | 82.3%–90.2% | 32.716 | 11.274 | 2.902 | Yes | 1068 |
| Kansas-calibrated P32 | Random forest | 80% | 1,733 | 1,290 | 74.4% | 69.5%–79.9% | 24.839 | 11.274 | 2.203 | Yes | 1068 |
| Kansas-calibrated P32 | Random forest | 90% | 1,733 | 1,512 | 87.2% | 83.8%–91.3% | 33.279 | 11.274 | 2.952 | Yes | 1068 |
| P37 · 0 local years | Ridge | 80% | 462 | 254 | 55.0% | 37.9%–70.7% | 18.344 | — | — | Yes | 420–595 |
| P37 · 0 local years | Ridge | 90% | 462 | 298 | 64.5% | 45.2%–81.9% | 22.950 | — | — | Yes | 420–595 |
| P37 · 0 local years | Random forest | 80% | 462 | 249 | 53.9% | 39.2%–65.9% | 18.847 | — | — | Yes | 420–595 |
| P37 · 0 local years | Random forest | 90% | 462 | 318 | 68.8% | 54.8%–81.2% | 25.172 | — | — | Yes | 420–595 |
| P37 · 3 local years | Ridge | 80% | 462 | 308 | 66.7% | 43.1%–87.4% | Unbounded (1) | 12.171 | — | Yes | 3–36 |
| P37 · 3 local years | Ridge | 90% | 462 | 338 | 73.2% | 48.6%–94.3% | Unbounded (1) | 12.171 | — | Yes | 3–36 |
| P37 · 3 local years | Random forest | 80% | 462 | 257 | 55.6% | 33.8%–72.8% | Unbounded (1) | 12.171 | — | Yes | 3–36 |
| P37 · 3 local years | Random forest | 90% | 462 | 299 | 64.7% | 41.0%–83.7% | Unbounded (1) | 12.171 | — | Yes | 3–36 |
| P37 · 5 local years | Ridge | 80% | 462 | 291 | 63.0% | 42.6%–81.2% | 21.920 | 12.589 | 1.741 | Yes | 5–60 |
| P37 · 5 local years | Ridge | 90% | 462 | 326 | 70.6% | 48.4%–90.0% | Unbounded (1) | 12.589 | — | Yes | 5–60 |
| P37 · 5 local years | Random forest | 80% | 462 | 239 | 51.7% | 33.6%–66.0% | 17.404 | 12.589 | 1.382 | Yes | 5–60 |
| P37 · 5 local years | Random forest | 90% | 462 | 285 | 61.7% | 40.6%–78.8% | Unbounded (1) | 12.589 | — | Yes | 5–60 |
| P37 · 8 local years | Ridge | 80% | 462 | 276 | 59.7% | 40.6%–75.7% | 20.523 | 12.201 | 1.682 | Yes | 8–96 |
| P37 · 8 local years | Ridge | 90% | 462 | 320 | 69.3% | 48.5%–88.5% | Unbounded (1) | 12.201 | — | Yes | 8–96 |
| P37 · 8 local years | Random forest | 80% | 462 | 239 | 51.7% | 35.4%–65.1% | 17.105 | 12.201 | 1.402 | Yes | 8–96 |
| P37 · 8 local years | Random forest | 90% | 462 | 278 | 60.2% | 40.5%–75.0% | Unbounded (1) | 12.201 | — | Yes | 8–96 |
| P37 · 12 local years | Ridge | 80% | 462 | 289 | 62.6% | 44.9%–78.5% | 22.161 | 11.004 | 2.014 | Yes | 12–144 |
| P37 · 12 local years | Ridge | 90% | 462 | 347 | 75.1% | 62.2%–89.1% | 28.445 | 11.004 | 2.585 | Yes | 12–144 |
| P37 · 12 local years | Random forest | 80% | 462 | 256 | 55.4% | 41.2%–68.3% | 19.329 | 11.004 | 1.757 | Yes | 12–144 |
| P37 · 12 local years | Random forest | 90% | 462 | 308 | 66.7% | 55.5%–76.8% | 24.772 | 11.004 | 2.251 | Yes | 12–144 |

<details>
<summary>All P37 district results</summary>

| Evaluation | Model | Nominal | County-years | Covered | Coverage | 95% interval | Mean width | County-mean RMSE | Width / RMSE | Below nominal | Calibration rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 years · district 10 | Ridge | 80% | 117 | 28 | 23.9% | 11.0%–36.2% | 18.344 | — | — | Yes | 420 |
| 0 years · district 10 | Ridge | 90% | 117 | 34 | 29.1% | 14.4%–42.9% | 22.944 | — | — | Yes | 420 |
| 0 years · district 10 | Random forest | 80% | 117 | 33 | 28.2% | 16.5%–40.0% | 18.843 | — | — | Yes | 420 |
| 0 years · district 10 | Random forest | 90% | 117 | 51 | 43.6% | 29.0%–57.6% | 25.166 | — | — | Yes | 420 |
| 0 years · district 20 | Ridge | 80% | 18 | 9 | 50.0% | 23.5%–78.9% | 18.344 | — | — | Yes | 420 |
| 0 years · district 20 | Ridge | 90% | 18 | 11 | 61.1% | 29.4%–90.0% | 22.944 | — | — | Yes | 420 |
| 0 years · district 20 | Random forest | 80% | 18 | 8 | 44.4% | 16.6%–75.0% | 18.843 | — | — | Yes | 420 |
| 0 years · district 20 | Random forest | 90% | 18 | 11 | 61.1% | 31.2%–89.5% | 25.166 | — | — | Yes | 420 |
| 0 years · district 30 | Ridge | 80% | 1 | 1 | 100.0% | — | 18.284 | — | — | — | 595 |
| 0 years · district 30 | Ridge | 90% | 1 | 1 | 100.0% | — | 25.611 | — | — | — | 595 |
| 0 years · district 30 | Random forest | 80% | 1 | 0 | 0.0% | — | 20.709 | — | — | Yes | 595 |
| 0 years · district 30 | Random forest | 90% | 1 | 1 | 100.0% | — | 28.304 | — | — | — | 595 |
| 0 years · district 50 | Ridge | 80% | 31 | 19 | 61.3% | 43.5%–78.3% | 18.344 | — | — | Yes | 420 |
| 0 years · district 50 | Ridge | 90% | 31 | 24 | 77.4% | 60.0%–93.5% | 22.944 | — | — | Yes | 420 |
| 0 years · district 50 | Random forest | 80% | 31 | 17 | 54.8% | 32.3%–80.7% | 18.843 | — | — | Yes | 420 |
| 0 years · district 50 | Random forest | 90% | 31 | 23 | 74.2% | 58.0%–91.5% | 25.166 | — | — | Yes | 420 |
| 0 years · district 60 | Ridge | 80% | 66 | 48 | 72.7% | 59.1%–86.2% | 18.344 | — | — | Yes | 420 |
| 0 years · district 60 | Ridge | 90% | 66 | 53 | 80.3% | 69.8%–91.3% | 22.944 | — | — | Yes | 420 |
| 0 years · district 60 | Random forest | 80% | 66 | 47 | 71.2% | 63.4%–79.2% | 18.843 | — | — | Yes | 420 |
| 0 years · district 60 | Random forest | 90% | 66 | 54 | 81.8% | 71.8%–91.7% | 25.166 | — | — | Yes | 420 |
| 0 years · district 70 | Ridge | 80% | 96 | 53 | 55.2% | 38.7%–72.8% | 18.344 | — | — | Yes | 420 |
| 0 years · district 70 | Ridge | 90% | 96 | 63 | 65.6% | 49.0%–81.9% | 22.944 | — | — | Yes | 420 |
| 0 years · district 70 | Random forest | 80% | 96 | 56 | 58.3% | 41.2%–74.2% | 18.843 | — | — | Yes | 420 |
| 0 years · district 70 | Random forest | 90% | 96 | 68 | 70.8% | 53.4%–87.0% | 25.166 | — | — | Yes | 420 |
| 0 years · district 80 | Ridge | 80% | 54 | 42 | 77.8% | 62.3%–92.5% | 18.344 | — | — | Yes | 420 |
| 0 years · district 80 | Ridge | 90% | 54 | 48 | 88.9% | 80.3%–96.7% | 22.944 | — | — | Yes | 420 |
| 0 years · district 80 | Random forest | 80% | 54 | 36 | 66.7% | 36.7%–94.4% | 18.843 | — | — | Yes | 420 |
| 0 years · district 80 | Random forest | 90% | 54 | 43 | 79.6% | 58.5%–100.0% | 25.166 | — | — | Yes | 420 |
| 0 years · district 90 | Ridge | 80% | 79 | 54 | 68.4% | 47.9%–84.3% | 18.344 | — | — | Yes | 420 |
| 0 years · district 90 | Ridge | 90% | 79 | 64 | 81.0% | 65.8%–92.3% | 22.944 | — | — | Yes | 420 |
| 0 years · district 90 | Random forest | 80% | 79 | 52 | 65.8% | 45.8%–82.2% | 18.843 | — | — | Yes | 420 |
| 0 years · district 90 | Random forest | 90% | 79 | 67 | 84.8% | 68.8%–95.2% | 25.166 | — | — | Yes | 420 |
| 3 years · district 10 | Ridge | 80% | 117 | 31 | 26.5% | 12.0%–39.3% | 20.715 | 8.494 | 2.439 | Yes | 29 |
| 3 years · district 10 | Ridge | 90% | 117 | 35 | 29.9% | 15.4%–43.2% | 24.196 | 8.494 | 2.849 | Yes | 29 |
| 3 years · district 10 | Random forest | 80% | 117 | 21 | 17.9% | 6.1%–28.5% | 13.547 | 8.494 | 1.595 | Yes | 29 |
| 3 years · district 10 | Random forest | 90% | 117 | 26 | 22.2% | 11.0%–32.8% | 15.091 | 8.494 | 1.777 | Yes | 29 |
| 3 years · district 20 | Ridge | 80% | 18 | 4 | 22.2% | 0.0%–57.2% | 10.367 | 8.233 | 1.259 | Yes | 9 |
| 3 years · district 20 | Ridge | 90% | 18 | 9 | 50.0% | 23.5%–78.9% | 19.402 | 8.233 | 2.357 | Yes | 9 |
| 3 years · district 20 | Random forest | 80% | 18 | 3 | 16.7% | 4.8%–31.6% | 13.605 | 8.233 | 1.653 | Yes | 9 |
| 3 years · district 20 | Random forest | 90% | 18 | 10 | 55.6% | 28.6%–82.4% | 24.850 | 8.233 | 3.019 | Yes | 9 |
| 3 years · district 30 | Ridge | 80% | 1 | 1 | 100.0% | — | Unbounded (1) | 17.433 | — | — | 3 |
| 3 years · district 30 | Ridge | 90% | 1 | 1 | 100.0% | — | Unbounded (1) | 17.433 | — | — | 3 |
| 3 years · district 30 | Random forest | 80% | 1 | 1 | 100.0% | — | Unbounded (1) | 17.433 | — | — | 3 |
| 3 years · district 30 | Random forest | 90% | 1 | 1 | 100.0% | — | Unbounded (1) | 17.433 | — | — | 3 |
| 3 years · district 50 | Ridge | 80% | 31 | 23 | 74.2% | 51.6%–93.5% | 20.978 | 9.788 | 2.143 | Yes | 15 |
| 3 years · district 50 | Ridge | 90% | 31 | 24 | 77.4% | 60.0%–93.5% | 22.022 | 9.788 | 2.250 | Yes | 15 |
| 3 years · district 50 | Random forest | 80% | 31 | 19 | 61.3% | 42.9%–81.5% | 22.196 | 9.788 | 2.268 | Yes | 15 |
| 3 years · district 50 | Random forest | 90% | 31 | 25 | 80.6% | 62.9%–100.0% | 29.575 | 9.788 | 3.022 | Yes | 15 |
| 3 years · district 60 | Ridge | 80% | 66 | 56 | 84.8% | 74.4%–95.9% | 27.866 | 13.970 | 1.995 | — | 30 |
| 3 years · district 60 | Ridge | 90% | 66 | 65 | 98.5% | 95.5%–100.0% | 33.892 | 13.970 | 2.426 | — | 30 |
| 3 years · district 60 | Random forest | 80% | 66 | 49 | 74.2% | 63.9%–84.9% | 19.786 | 13.970 | 1.416 | Yes | 30 |
| 3 years · district 60 | Random forest | 90% | 66 | 53 | 80.3% | 69.6%–91.1% | 24.190 | 13.970 | 1.732 | Yes | 30 |
| 3 years · district 70 | Ridge | 80% | 96 | 68 | 70.8% | 55.9%–85.9% | 24.808 | 13.516 | 1.835 | Yes | 27 |
| 3 years · district 70 | Ridge | 90% | 96 | 75 | 78.1% | 65.6%–88.7% | 31.927 | 13.516 | 2.362 | Yes | 27 |
| 3 years · district 70 | Random forest | 80% | 96 | 66 | 68.8% | 51.6%–84.8% | 24.249 | 13.516 | 1.794 | Yes | 27 |
| 3 years · district 70 | Random forest | 90% | 96 | 71 | 74.0% | 57.6%–89.2% | 27.500 | 13.516 | 2.035 | Yes | 27 |
| 3 years · district 80 | Ridge | 80% | 54 | 51 | 94.4% | 85.0%–100.0% | 28.084 | 10.398 | 2.701 | — | 24 |
| 3 years · district 80 | Ridge | 90% | 54 | 52 | 96.3% | 88.6%–100.0% | 32.319 | 10.398 | 3.108 | — | 24 |
| 3 years · district 80 | Random forest | 80% | 54 | 36 | 66.7% | 36.7%–94.4% | 20.080 | 10.398 | 1.931 | Yes | 24 |
| 3 years · district 80 | Random forest | 90% | 54 | 41 | 75.9% | 50.9%–100.0% | 23.465 | 10.398 | 2.257 | Yes | 24 |
| 3 years · district 90 | Ridge | 80% | 79 | 74 | 93.7% | 88.2%–98.7% | 30.513 | 15.607 | 1.955 | — | 36 |
| 3 years · district 90 | Ridge | 90% | 79 | 77 | 97.5% | 92.4%–100.0% | 36.926 | 15.607 | 2.366 | — | 36 |
| 3 years · district 90 | Random forest | 80% | 79 | 62 | 78.5% | 61.4%–91.0% | 22.549 | 15.607 | 1.445 | Yes | 36 |
| 3 years · district 90 | Random forest | 90% | 79 | 72 | 91.1% | 82.1%–97.0% | 29.371 | 15.607 | 1.882 | — | 36 |
| 5 years · district 10 | Ridge | 80% | 117 | 31 | 26.5% | 12.0%–39.3% | 20.715 | 7.870 | 2.632 | Yes | 51 |
| 5 years · district 10 | Ridge | 90% | 117 | 35 | 29.9% | 15.4%–43.2% | 24.514 | 7.870 | 3.115 | Yes | 51 |
| 5 years · district 10 | Random forest | 80% | 117 | 21 | 17.9% | 6.1%–28.5% | 13.547 | 7.870 | 1.721 | Yes | 51 |
| 5 years · district 10 | Random forest | 90% | 117 | 26 | 22.2% | 11.0%–32.8% | 15.091 | 7.870 | 1.918 | Yes | 51 |
| 5 years · district 20 | Ridge | 80% | 18 | 9 | 50.0% | 23.5%–78.9% | 19.402 | 8.229 | 2.358 | Yes | 15 |
| 5 years · district 20 | Ridge | 90% | 18 | 12 | 66.7% | 41.2%–90.0% | 24.663 | 8.229 | 2.997 | Yes | 15 |
| 5 years · district 20 | Random forest | 80% | 18 | 10 | 55.6% | 28.6%–82.4% | 24.850 | 8.229 | 3.020 | Yes | 15 |
| 5 years · district 20 | Random forest | 90% | 18 | 11 | 61.1% | 31.2%–89.5% | 28.326 | 8.229 | 3.442 | Yes | 15 |
| 5 years · district 30 | Ridge | 80% | 1 | 1 | 100.0% | — | 18.972 | 19.860 | 0.955 | — | 5 |
| 5 years · district 30 | Ridge | 90% | 1 | 1 | 100.0% | — | Unbounded (1) | 19.860 | — | — | 5 |
| 5 years · district 30 | Random forest | 80% | 1 | 0 | 0.0% | — | 20.196 | 19.860 | 1.017 | Yes | 5 |
| 5 years · district 30 | Random forest | 90% | 1 | 1 | 100.0% | — | Unbounded (1) | 19.860 | — | — | 5 |
| 5 years · district 50 | Ridge | 80% | 31 | 22 | 71.0% | 48.6%–88.9% | 19.860 | 10.014 | 1.983 | Yes | 23 |
| 5 years · district 50 | Ridge | 90% | 31 | 24 | 77.4% | 60.0%–93.5% | 21.934 | 10.014 | 2.190 | Yes | 23 |
| 5 years · district 50 | Random forest | 80% | 31 | 19 | 61.3% | 42.9%–81.5% | 22.196 | 10.014 | 2.216 | Yes | 23 |
| 5 years · district 50 | Random forest | 90% | 31 | 24 | 77.4% | 60.0%–93.5% | 28.065 | 10.014 | 2.803 | Yes | 23 |
| 5 years · district 60 | Ridge | 80% | 66 | 52 | 78.8% | 69.3%–89.7% | 21.965 | 16.146 | 1.360 | Yes | 50 |
| 5 years · district 60 | Ridge | 90% | 66 | 56 | 84.8% | 74.4%–95.9% | 27.908 | 16.146 | 1.728 | Yes | 50 |
| 5 years · district 60 | Random forest | 80% | 66 | 47 | 71.2% | 63.4%–79.2% | 18.790 | 16.146 | 1.164 | Yes | 50 |
| 5 years · district 60 | Random forest | 90% | 66 | 51 | 77.3% | 66.1%–89.6% | 22.635 | 16.146 | 1.402 | Yes | 50 |
| 5 years · district 70 | Ridge | 80% | 96 | 62 | 64.6% | 48.0%–80.8% | 21.985 | 12.808 | 1.716 | Yes | 45 |
| 5 years · district 70 | Ridge | 90% | 96 | 72 | 75.0% | 61.4%–87.0% | 29.074 | 12.808 | 2.270 | Yes | 45 |
| 5 years · district 70 | Random forest | 80% | 96 | 59 | 61.5% | 44.4%–77.3% | 20.247 | 12.808 | 1.581 | Yes | 45 |
| 5 years · district 70 | Random forest | 90% | 96 | 66 | 68.8% | 51.6%–84.8% | 24.308 | 12.808 | 1.898 | Yes | 45 |
| 5 years · district 80 | Ridge | 80% | 54 | 46 | 85.2% | 71.2%–96.7% | 21.527 | 10.623 | 2.027 | — | 36 |
| 5 years · district 80 | Ridge | 90% | 54 | 52 | 96.3% | 88.6%–100.0% | 30.519 | 10.623 | 2.873 | — | 36 |
| 5 years · district 80 | Random forest | 80% | 54 | 36 | 66.7% | 36.7%–94.4% | 16.968 | 10.623 | 1.597 | Yes | 36 |
| 5 years · district 80 | Random forest | 90% | 54 | 40 | 74.1% | 45.9%–100.0% | 21.880 | 10.623 | 2.060 | Yes | 36 |
| 5 years · district 90 | Ridge | 80% | 79 | 68 | 86.1% | 71.9%–96.8% | 25.276 | 16.766 | 1.508 | — | 60 |
| 5 years · district 90 | Ridge | 90% | 79 | 74 | 93.7% | 88.2%–98.7% | 30.647 | 16.766 | 1.828 | — | 60 |
| 5 years · district 90 | Random forest | 80% | 79 | 47 | 59.5% | 34.9%–79.8% | 15.188 | 16.766 | 0.906 | Yes | 60 |
| 5 years · district 90 | Random forest | 90% | 79 | 66 | 83.5% | 68.2%–93.0% | 24.998 | 16.766 | 1.491 | Yes | 60 |
| 8 years · district 10 | Ridge | 80% | 117 | 29 | 24.8% | 11.0%–37.4% | 19.147 | 7.113 | 2.692 | Yes | 84 |
| 8 years · district 10 | Ridge | 90% | 117 | 35 | 29.9% | 15.4%–43.2% | 24.514 | 7.113 | 3.446 | Yes | 84 |
| 8 years · district 10 | Random forest | 80% | 117 | 25 | 21.4% | 10.4%–32.3% | 14.609 | 7.113 | 2.054 | Yes | 84 |
| 8 years · district 10 | Random forest | 90% | 117 | 28 | 23.9% | 12.7%–35.0% | 17.022 | 7.113 | 2.393 | Yes | 84 |
| 8 years · district 20 | Ridge | 80% | 18 | 9 | 50.0% | 23.5%–78.9% | 19.402 | 8.090 | 2.398 | Yes | 24 |
| 8 years · district 20 | Ridge | 90% | 18 | 15 | 83.3% | 66.7%–95.2% | 31.269 | 8.090 | 3.865 | Yes | 24 |
| 8 years · district 20 | Random forest | 80% | 18 | 10 | 55.6% | 28.6%–82.4% | 24.850 | 8.090 | 3.072 | Yes | 24 |
| 8 years · district 20 | Random forest | 90% | 18 | 11 | 61.1% | 31.2%–89.5% | 28.326 | 8.090 | 3.501 | Yes | 24 |
| 8 years · district 30 | Ridge | 80% | 1 | 1 | 100.0% | — | 33.643 | 16.700 | 2.015 | — | 8 |
| 8 years · district 30 | Ridge | 90% | 1 | 1 | 100.0% | — | Unbounded (1) | 16.700 | — | — | 8 |
| 8 years · district 30 | Random forest | 80% | 1 | 1 | 100.0% | — | 26.881 | 16.700 | 1.610 | — | 8 |
| 8 years · district 30 | Random forest | 90% | 1 | 1 | 100.0% | — | Unbounded (1) | 16.700 | — | — | 8 |
| 8 years · district 50 | Ridge | 80% | 31 | 21 | 67.7% | 48.4%–81.5% | 19.341 | 9.826 | 1.968 | Yes | 38 |
| 8 years · district 50 | Ridge | 90% | 31 | 24 | 77.4% | 60.0%–93.5% | 22.022 | 9.826 | 2.241 | Yes | 38 |
| 8 years · district 50 | Random forest | 80% | 31 | 21 | 67.7% | 48.4%–87.0% | 23.098 | 9.826 | 2.351 | Yes | 38 |
| 8 years · district 50 | Random forest | 90% | 31 | 25 | 80.6% | 62.9%–100.0% | 29.575 | 9.826 | 3.010 | Yes | 38 |
| 8 years · district 60 | Ridge | 80% | 66 | 50 | 75.8% | 66.7%–86.7% | 20.371 | 16.124 | 1.263 | Yes | 79 |
| 8 years · district 60 | Ridge | 90% | 66 | 56 | 84.8% | 74.4%–95.9% | 27.701 | 16.124 | 1.718 | Yes | 79 |
| 8 years · district 60 | Random forest | 80% | 66 | 44 | 66.7% | 57.9%–75.0% | 17.801 | 16.124 | 1.104 | Yes | 79 |
| 8 years · district 60 | Random forest | 90% | 66 | 51 | 77.3% | 66.1%–89.6% | 22.756 | 16.124 | 1.411 | Yes | 79 |
| 8 years · district 70 | Ridge | 80% | 96 | 62 | 64.6% | 48.0%–80.8% | 21.985 | 12.161 | 1.808 | Yes | 72 |
| 8 years · district 70 | Ridge | 90% | 96 | 68 | 70.8% | 55.9%–85.9% | 24.891 | 12.161 | 2.047 | Yes | 72 |
| 8 years · district 70 | Random forest | 80% | 96 | 59 | 61.5% | 44.4%–77.3% | 20.264 | 12.161 | 1.666 | Yes | 72 |
| 8 years · district 70 | Random forest | 90% | 96 | 69 | 71.9% | 55.4%–87.6% | 26.009 | 12.161 | 2.139 | Yes | 72 |
| 8 years · district 80 | Ridge | 80% | 54 | 44 | 81.5% | 69.4%–93.2% | 20.832 | 10.558 | 1.973 | — | 60 |
| 8 years · district 80 | Ridge | 90% | 54 | 52 | 96.3% | 88.6%–100.0% | 29.912 | 10.558 | 2.833 | — | 60 |
| 8 years · district 80 | Random forest | 80% | 54 | 36 | 66.7% | 36.7%–94.4% | 16.569 | 10.558 | 1.569 | Yes | 60 |
| 8 years · district 80 | Random forest | 90% | 54 | 40 | 74.1% | 45.9%–100.0% | 21.880 | 10.558 | 2.072 | Yes | 60 |
| 8 years · district 90 | Ridge | 80% | 79 | 60 | 75.9% | 58.4%–91.0% | 21.252 | 16.314 | 1.303 | Yes | 96 |
| 8 years · district 90 | Ridge | 90% | 79 | 69 | 87.3% | 75.4%–96.8% | 25.964 | 16.314 | 1.592 | Yes | 96 |
| 8 years · district 90 | Random forest | 80% | 79 | 43 | 54.4% | 30.4%–75.3% | 12.505 | 16.314 | 0.767 | Yes | 96 |
| 8 years · district 90 | Random forest | 90% | 79 | 53 | 67.1% | 48.8%–82.7% | 19.175 | 16.314 | 1.175 | Yes | 96 |
| 12 years · district 10 | Ridge | 80% | 117 | 35 | 29.9% | 15.4%–43.2% | 24.514 | 7.044 | 3.480 | Yes | 128 |
| 12 years · district 10 | Ridge | 90% | 117 | 60 | 51.3% | 37.7%–63.2% | 33.221 | 7.044 | 4.717 | Yes | 128 |
| 12 years · district 10 | Random forest | 80% | 117 | 34 | 29.1% | 16.5%–41.4% | 19.122 | 7.044 | 2.715 | Yes | 128 |
| 12 years · district 10 | Random forest | 90% | 117 | 55 | 47.0% | 32.5%–60.3% | 26.513 | 7.044 | 3.764 | Yes | 128 |
| 12 years · district 20 | Ridge | 80% | 18 | 11 | 61.1% | 29.4%–90.0% | 22.515 | 7.731 | 2.912 | Yes | 36 |
| 12 years · district 20 | Ridge | 90% | 18 | 15 | 83.3% | 66.7%–95.2% | 31.269 | 7.731 | 4.044 | Yes | 36 |
| 12 years · district 20 | Random forest | 80% | 18 | 10 | 55.6% | 28.6%–82.4% | 24.850 | 7.731 | 3.214 | Yes | 36 |
| 12 years · district 20 | Random forest | 90% | 18 | 11 | 61.1% | 31.2%–89.5% | 28.326 | 7.731 | 3.664 | Yes | 36 |
| 12 years · district 30 | Ridge | 80% | 1 | 1 | 100.0% | — | 24.481 | 12.258 | 1.997 | — | 12 |
| 12 years · district 30 | Ridge | 90% | 1 | 1 | 100.0% | — | 33.643 | 12.258 | 2.745 | — | 12 |
| 12 years · district 30 | Random forest | 80% | 1 | 1 | 100.0% | — | 26.881 | 12.258 | 2.193 | — | 12 |
| 12 years · district 30 | Random forest | 90% | 1 | 1 | 100.0% | — | 31.672 | 12.258 | 2.584 | — | 12 |
| 12 years · district 50 | Ridge | 80% | 31 | 23 | 74.2% | 51.6%–93.5% | 20.978 | 9.202 | 2.280 | Yes | 57 |
| 12 years · district 50 | Ridge | 90% | 31 | 29 | 93.5% | 87.0%–100.0% | 33.444 | 9.202 | 3.634 | — | 57 |
| 12 years · district 50 | Random forest | 80% | 31 | 23 | 74.2% | 58.0%–91.5% | 26.808 | 9.202 | 2.913 | Yes | 57 |
| 12 years · district 50 | Random forest | 90% | 31 | 25 | 80.6% | 62.9%–100.0% | 30.586 | 9.202 | 3.324 | Yes | 57 |
| 12 years · district 60 | Ridge | 80% | 66 | 50 | 75.8% | 66.7%–86.7% | 20.227 | 13.898 | 1.455 | Yes | 115 |
| 12 years · district 60 | Ridge | 90% | 66 | 53 | 80.3% | 69.8%–91.3% | 23.074 | 13.898 | 1.660 | Yes | 115 |
| 12 years · district 60 | Random forest | 80% | 66 | 48 | 72.7% | 63.8%–81.9% | 19.612 | 13.898 | 1.411 | Yes | 115 |
| 12 years · district 60 | Random forest | 90% | 66 | 53 | 80.3% | 69.6%–91.1% | 24.306 | 13.898 | 1.749 | Yes | 115 |
| 12 years · district 70 | Ridge | 80% | 96 | 62 | 64.6% | 48.0%–80.8% | 22.353 | 11.754 | 1.902 | Yes | 108 |
| 12 years · district 70 | Ridge | 90% | 96 | 69 | 71.9% | 56.5%–86.5% | 25.558 | 11.754 | 2.174 | Yes | 108 |
| 12 years · district 70 | Random forest | 80% | 96 | 59 | 61.5% | 44.4%–77.3% | 20.264 | 11.754 | 1.724 | Yes | 108 |
| 12 years · district 70 | Random forest | 90% | 96 | 69 | 71.9% | 55.4%–87.6% | 26.009 | 11.754 | 2.213 | Yes | 108 |
| 12 years · district 80 | Ridge | 80% | 54 | 47 | 87.0% | 76.5%–96.7% | 22.021 | 9.129 | 2.412 | — | 92 |
| 12 years · district 80 | Ridge | 90% | 54 | 52 | 96.3% | 88.6%–100.0% | 30.519 | 9.129 | 3.343 | — | 92 |
| 12 years · district 80 | Random forest | 80% | 54 | 36 | 66.7% | 36.7%–94.4% | 19.834 | 9.129 | 2.173 | Yes | 92 |
| 12 years · district 80 | Random forest | 90% | 54 | 42 | 77.8% | 53.0%–100.0% | 23.617 | 9.129 | 2.587 | Yes | 92 |
| 12 years · district 90 | Ridge | 80% | 79 | 60 | 75.9% | 58.4%–91.0% | 20.508 | 14.130 | 1.451 | Yes | 144 |
| 12 years · district 90 | Ridge | 90% | 79 | 68 | 86.1% | 71.9%–96.8% | 25.276 | 14.130 | 1.789 | Yes | 144 |
| 12 years · district 90 | Random forest | 80% | 79 | 45 | 57.0% | 31.1%–78.7% | 13.628 | 14.130 | 0.964 | Yes | 144 |
| 12 years · district 90 | Random forest | 90% | 79 | 52 | 65.8% | 45.8%–82.2% | 18.693 | 14.130 | 1.323 | Yes | 144 |

</details>

#### Oklahoma

| Evaluation | Model | Nominal | County-years | Covered | Coverage | 95% interval | Mean width | County-mean RMSE | Width / RMSE | Below nominal | Calibration rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kansas-calibrated P32 | Ridge | 80% | 1,800 | 1,373 | 76.3% | 66.2%–83.6% | 26.708 | 9.200 | 2.903 | Yes | 1068 |
| Kansas-calibrated P32 | Ridge | 90% | 1,800 | 1,549 | 86.1% | 78.8%–91.5% | 32.716 | 9.200 | 3.556 | Yes | 1068 |
| Kansas-calibrated P32 | Random forest | 80% | 1,800 | 1,177 | 65.4% | 53.9%–74.0% | 24.839 | 9.200 | 2.700 | Yes | 1068 |
| Kansas-calibrated P32 | Random forest | 90% | 1,800 | 1,510 | 83.9% | 75.0%–90.0% | 33.279 | 9.200 | 3.617 | Yes | 1068 |
| P37 · 0 local years | Ridge | 80% | 88 | 13 | 14.8% | 3.7%–45.5% | 18.486 | — | — | Yes | 420–630 |
| P37 · 0 local years | Ridge | 90% | 88 | 18 | 20.5% | 7.8%–46.3% | 23.361 | — | — | Yes | 420–630 |
| P37 · 0 local years | Random forest | 80% | 88 | 6 | 6.8% | 0.8%–26.1% | 19.029 | — | — | Yes | 420–630 |
| P37 · 0 local years | Random forest | 90% | 88 | 8 | 9.1% | 3.7%–30.4% | 25.496 | — | — | Yes | 420–630 |
| P37 · 3 local years | Ridge | 80% | 88 | 20 | 22.7% | 12.6%–50.0% | 24.599 | 7.463 | 3.296 | Yes | 15–24 |
| P37 · 3 local years | Ridge | 90% | 88 | 29 | 33.0% | 22.2%–55.7% | 29.630 | 7.463 | 3.970 | Yes | 15–24 |
| P37 · 3 local years | Random forest | 80% | 88 | 10 | 11.4% | 4.8%–30.4% | 25.608 | 7.463 | 3.431 | Yes | 15–24 |
| P37 · 3 local years | Random forest | 90% | 88 | 21 | 23.9% | 11.1%–46.2% | 31.901 | 7.463 | 4.274 | Yes | 15–24 |
| P37 · 5 local years | Ridge | 80% | 88 | 25 | 28.4% | 20.0%–54.6% | 26.894 | 7.530 | 3.572 | Yes | 22–36 |
| P37 · 5 local years | Ridge | 90% | 88 | 32 | 36.4% | 28.3%–60.1% | 30.749 | 7.530 | 4.084 | Yes | 22–36 |
| P37 · 5 local years | Random forest | 80% | 88 | 18 | 20.5% | 9.1%–35.9% | 28.835 | 7.530 | 3.829 | Yes | 22–36 |
| P37 · 5 local years | Random forest | 90% | 88 | 29 | 33.0% | 17.8%–50.0% | 35.451 | 7.530 | 4.708 | Yes | 22–36 |
| P37 · 8 local years | Ridge | 80% | 88 | 39 | 44.3% | 34.7%–62.5% | 32.867 | 7.783 | 4.223 | Yes | 29–44 |
| P37 · 8 local years | Ridge | 90% | 88 | 50 | 56.8% | 46.3%–69.2% | 37.193 | 7.783 | 4.779 | Yes | 29–44 |
| P37 · 8 local years | Random forest | 80% | 88 | 24 | 27.3% | 17.8%–38.7% | 33.739 | 7.783 | 4.335 | Yes | 29–44 |
| P37 · 8 local years | Random forest | 90% | 88 | 43 | 48.9% | 41.5%–53.2% | 38.726 | 7.783 | 4.976 | Yes | 29–44 |
| P37 · 12 local years | Ridge | 80% | 88 | 38 | 43.2% | 30.8%–62.5% | 31.529 | 7.501 | 4.204 | Yes | 37–63 |
| P37 · 12 local years | Ridge | 90% | 88 | 50 | 56.8% | 43.9%–67.9% | 37.037 | 7.501 | 4.938 | Yes | 37–63 |
| P37 · 12 local years | Random forest | 80% | 88 | 25 | 28.4% | 17.8%–46.2% | 33.498 | 7.501 | 4.466 | Yes | 37–63 |
| P37 · 12 local years | Random forest | 90% | 88 | 38 | 43.2% | 33.3%–62.5% | 37.996 | 7.501 | 5.066 | Yes | 37–63 |

<details>
<summary>All P37 district results</summary>

| Evaluation | Model | Nominal | County-years | Covered | Coverage | 95% interval | Mean width | County-mean RMSE | Width / RMSE | Below nominal | Calibration rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 years · district 10 | Ridge | 80% | 30 | 0 | 0.0% | 0.0%–0.0% | 18.344 | — | — | Yes | 420 |
| 0 years · district 10 | Ridge | 90% | 30 | 1 | 3.3% | 0.0%–10.0% | 22.944 | — | — | Yes | 420 |
| 0 years · district 10 | Random forest | 80% | 30 | 0 | 0.0% | 0.0%–0.0% | 18.843 | — | — | Yes | 420 |
| 0 years · district 10 | Random forest | 90% | 30 | 1 | 3.3% | 0.0%–10.0% | 25.166 | — | — | Yes | 420 |
| 0 years · district 20 | Ridge | 80% | 14 | 3 | 21.4% | 0.0%–53.0% | 18.344 | — | — | Yes | 420 |
| 0 years · district 20 | Ridge | 90% | 14 | 4 | 28.6% | 4.9%–57.2% | 22.944 | — | — | Yes | 420 |
| 0 years · district 20 | Random forest | 80% | 14 | 0 | 0.0% | 0.0%–0.0% | 18.843 | — | — | Yes | 420 |
| 0 years · district 20 | Random forest | 90% | 14 | 1 | 7.1% | 0.0%–27.3% | 25.166 | — | — | Yes | 420 |
| 0 years · district 30 | Ridge | 80% | 31 | 3 | 9.7% | 0.0%–25.0% | 18.344 | — | — | Yes | 420 |
| 0 years · district 30 | Ridge | 90% | 31 | 6 | 19.4% | 2.6%–41.9% | 22.944 | — | — | Yes | 420 |
| 0 years · district 30 | Random forest | 80% | 31 | 1 | 3.2% | 0.0%–10.4% | 18.843 | — | — | Yes | 420 |
| 0 years · district 30 | Random forest | 90% | 31 | 1 | 3.2% | 0.0%–10.4% | 25.166 | — | — | Yes | 420 |
| 0 years · district 40 | Ridge | 80% | 7 | 1 | 14.3% | 0.0%–50.0% | 18.344 | — | — | Yes | 420 |
| 0 years · district 40 | Ridge | 90% | 7 | 1 | 14.3% | 0.0%–50.0% | 22.944 | — | — | Yes | 420 |
| 0 years · district 40 | Random forest | 80% | 7 | 1 | 14.3% | 0.0%–50.0% | 18.843 | — | — | Yes | 420 |
| 0 years · district 40 | Random forest | 90% | 7 | 1 | 14.3% | 0.0%–50.0% | 25.166 | — | — | Yes | 420 |
| 0 years · district 50 | Ridge | 80% | 6 | 6 | 100.0% | — | 20.434 | — | — | — | 630 |
| 0 years · district 50 | Ridge | 90% | 6 | 6 | 100.0% | — | 29.050 | — | — | — | 630 |
| 0 years · district 50 | Random forest | 80% | 6 | 4 | 66.7% | — | 21.578 | — | — | Yes | 630 |
| 0 years · district 50 | Random forest | 90% | 6 | 4 | 66.7% | — | 30.018 | — | — | Yes | 630 |
| 3 years · district 10 | Ridge | 80% | 30 | 3 | 10.0% | 0.0%–23.3% | 31.923 | 7.033 | 4.539 | Yes | 15 |
| 3 years · district 10 | Ridge | 90% | 30 | 10 | 33.3% | 10.0%–56.7% | 39.374 | 7.033 | 5.598 | Yes | 15 |
| 3 years · district 10 | Random forest | 80% | 30 | 3 | 10.0% | 3.3%–16.7% | 28.179 | 7.033 | 4.006 | Yes | 15 |
| 3 years · district 10 | Random forest | 90% | 30 | 10 | 33.3% | 23.3%–46.7% | 35.884 | 7.033 | 5.102 | Yes | 15 |
| 3 years · district 20 | Ridge | 80% | 14 | 4 | 28.6% | 4.9%–57.2% | 23.723 | 7.988 | 2.970 | Yes | 15 |
| 3 years · district 20 | Ridge | 90% | 14 | 6 | 42.9% | 6.5%–85.7% | 27.569 | 7.988 | 3.451 | Yes | 15 |
| 3 years · district 20 | Random forest | 80% | 14 | 1 | 7.1% | 0.0%–27.3% | 25.439 | 7.988 | 3.185 | Yes | 15 |
| 3 years · district 20 | Random forest | 90% | 14 | 2 | 14.3% | 0.0%–36.4% | 29.056 | 7.988 | 3.638 | Yes | 15 |
| 3 years · district 30 | Ridge | 80% | 31 | 6 | 19.4% | 2.6%–41.9% | 21.577 | 6.620 | 3.259 | Yes | 22 |
| 3 years · district 30 | Ridge | 90% | 31 | 6 | 19.4% | 2.6%–41.9% | 24.744 | 6.620 | 3.738 | Yes | 22 |
| 3 years · district 30 | Random forest | 80% | 31 | 1 | 3.2% | 0.0%–10.4% | 23.774 | 6.620 | 3.591 | Yes | 22 |
| 3 years · district 30 | Random forest | 90% | 31 | 3 | 9.7% | 0.0%–20.7% | 30.097 | 6.620 | 4.546 | Yes | 22 |
| 3 years · district 40 | Ridge | 80% | 7 | 1 | 14.3% | 0.0%–50.0% | 18.240 | 8.978 | 2.032 | Yes | 19 |
| 3 years · district 40 | Ridge | 90% | 7 | 1 | 14.3% | 0.0%–50.0% | 23.763 | 8.978 | 2.647 | Yes | 19 |
| 3 years · district 40 | Random forest | 80% | 7 | 1 | 14.3% | 0.0%–50.0% | 19.423 | 8.978 | 2.163 | Yes | 19 |
| 3 years · district 40 | Random forest | 90% | 7 | 1 | 14.3% | 0.0%–50.0% | 26.684 | 8.978 | 2.972 | Yes | 19 |
| 3 years · district 50 | Ridge | 80% | 6 | 6 | 100.0% | — | 13.064 | 10.014 | 1.305 | — | 24 |
| 3 years · district 50 | Ridge | 90% | 6 | 6 | 100.0% | — | 17.809 | 10.014 | 1.778 | — | 24 |
| 3 years · district 50 | Random forest | 80% | 6 | 4 | 66.7% | — | 29.839 | 10.014 | 2.980 | Yes | 24 |
| 3 years · district 50 | Random forest | 90% | 6 | 5 | 83.3% | — | 34.027 | 10.014 | 3.398 | Yes | 24 |
| 5 years · district 10 | Ridge | 80% | 30 | 8 | 26.7% | 6.7%–50.0% | 37.937 | 7.088 | 5.352 | Yes | 25 |
| 5 years · district 10 | Ridge | 90% | 30 | 10 | 33.3% | 10.0%–56.7% | 40.285 | 7.088 | 5.684 | Yes | 25 |
| 5 years · district 10 | Random forest | 80% | 30 | 9 | 30.0% | 16.7%–46.7% | 34.380 | 7.088 | 4.851 | Yes | 25 |
| 5 years · district 10 | Random forest | 90% | 30 | 14 | 46.7% | 33.3%–56.7% | 38.283 | 7.088 | 5.401 | Yes | 25 |
| 5 years · district 20 | Ridge | 80% | 14 | 4 | 28.6% | 4.9%–57.2% | 23.723 | 7.621 | 3.113 | Yes | 22 |
| 5 years · district 20 | Ridge | 90% | 14 | 6 | 42.9% | 6.5%–85.7% | 27.569 | 7.621 | 3.618 | Yes | 22 |
| 5 years · district 20 | Random forest | 80% | 14 | 1 | 7.1% | 0.0%–27.3% | 25.439 | 7.621 | 3.338 | Yes | 22 |
| 5 years · district 20 | Random forest | 90% | 14 | 2 | 14.3% | 0.0%–36.4% | 29.056 | 7.621 | 3.813 | Yes | 22 |
| 5 years · district 30 | Ridge | 80% | 31 | 6 | 19.4% | 2.6%–41.9% | 22.270 | 6.467 | 3.444 | Yes | 33 |
| 5 years · district 30 | Ridge | 90% | 31 | 9 | 29.0% | 8.6%–53.3% | 27.033 | 6.467 | 4.180 | Yes | 33 |
| 5 years · district 30 | Random forest | 80% | 31 | 3 | 9.7% | 0.0%–20.7% | 26.901 | 6.467 | 4.160 | Yes | 33 |
| 5 years · district 30 | Random forest | 90% | 31 | 7 | 22.6% | 9.1%–37.9% | 37.854 | 6.467 | 5.854 | Yes | 33 |
| 5 years · district 40 | Ridge | 80% | 7 | 1 | 14.3% | 0.0%–50.0% | 18.240 | 8.852 | 2.060 | Yes | 32 |
| 5 years · district 40 | Ridge | 90% | 7 | 1 | 14.3% | 0.0%–50.0% | 23.763 | 8.852 | 2.684 | Yes | 32 |
| 5 years · district 40 | Random forest | 80% | 7 | 1 | 14.3% | 0.0%–50.0% | 19.623 | 8.852 | 2.217 | Yes | 32 |
| 5 years · district 40 | Random forest | 90% | 7 | 1 | 14.3% | 0.0%–50.0% | 26.684 | 8.852 | 3.014 | Yes | 32 |
| 5 years · district 50 | Ridge | 80% | 6 | 6 | 100.0% | — | 13.064 | 11.723 | 1.114 | — | 36 |
| 5 years · district 50 | Ridge | 90% | 6 | 6 | 100.0% | — | 17.845 | 11.723 | 1.522 | — | 36 |
| 5 years · district 50 | Random forest | 80% | 6 | 4 | 66.7% | — | 29.778 | 11.723 | 2.540 | Yes | 36 |
| 5 years · district 50 | Random forest | 90% | 6 | 5 | 83.3% | — | 34.027 | 11.723 | 2.903 | Yes | 36 |
| 8 years · district 10 | Ridge | 80% | 30 | 12 | 40.0% | 16.7%–63.3% | 43.149 | 7.345 | 5.875 | Yes | 40 |
| 8 years · district 10 | Ridge | 90% | 30 | 18 | 60.0% | 43.3%–73.3% | 48.004 | 7.345 | 6.536 | Yes | 40 |
| 8 years · district 10 | Random forest | 80% | 30 | 10 | 33.3% | 23.3%–46.7% | 35.086 | 7.345 | 4.777 | Yes | 40 |
| 8 years · district 10 | Random forest | 90% | 30 | 15 | 50.0% | 36.7%–60.0% | 40.143 | 7.345 | 5.466 | Yes | 40 |
| 8 years · district 20 | Ridge | 80% | 14 | 7 | 50.0% | 15.4%–87.5% | 31.669 | 7.700 | 4.113 | Yes | 29 |
| 8 years · district 20 | Ridge | 90% | 14 | 7 | 50.0% | 15.4%–87.5% | 32.959 | 7.700 | 4.281 | Yes | 29 |
| 8 years · district 20 | Random forest | 80% | 14 | 2 | 14.3% | 0.0%–36.4% | 29.056 | 7.700 | 3.774 | Yes | 29 |
| 8 years · district 20 | Random forest | 90% | 14 | 6 | 42.9% | 9.1%–78.6% | 32.813 | 7.700 | 4.262 | Yes | 29 |
| 8 years · district 30 | Ridge | 80% | 31 | 13 | 41.9% | 19.4%–67.7% | 28.427 | 6.826 | 4.165 | Yes | 44 |
| 8 years · district 30 | Ridge | 90% | 31 | 17 | 54.8% | 27.3%–86.7% | 33.046 | 6.826 | 4.842 | Yes | 44 |
| 8 years · district 30 | Random forest | 80% | 31 | 7 | 22.6% | 9.1%–37.9% | 37.512 | 6.826 | 5.496 | Yes | 44 |
| 8 years · district 30 | Random forest | 90% | 31 | 16 | 51.6% | 31.4%–75.9% | 42.227 | 6.826 | 6.187 | Yes | 44 |
| 8 years · district 40 | Ridge | 80% | 7 | 1 | 14.3% | 0.0%–50.0% | 23.763 | 9.530 | 2.494 | Yes | 42 |
| 8 years · district 40 | Ridge | 90% | 7 | 2 | 28.6% | 0.0%–66.7% | 32.181 | 9.530 | 3.377 | Yes | 42 |
| 8 years · district 40 | Random forest | 80% | 7 | 1 | 14.3% | 0.0%–50.0% | 25.851 | 9.530 | 2.713 | Yes | 42 |
| 8 years · district 40 | Random forest | 90% | 7 | 2 | 28.6% | 0.0%–66.7% | 34.815 | 9.530 | 3.653 | Yes | 42 |
| 8 years · district 50 | Ridge | 80% | 6 | 6 | 100.0% | — | 17.809 | 11.563 | 1.540 | — | 41 |
| 8 years · district 50 | Ridge | 90% | 6 | 6 | 100.0% | — | 20.291 | 11.563 | 1.755 | — | 41 |
| 8 years · district 50 | Random forest | 80% | 6 | 4 | 66.7% | — | 27.642 | 11.563 | 2.390 | Yes | 41 |
| 8 years · district 50 | Random forest | 90% | 6 | 4 | 66.7% | — | 31.913 | 11.563 | 2.760 | Yes | 41 |
| 12 years · district 10 | Ridge | 80% | 30 | 10 | 33.3% | 10.0%–56.7% | 40.285 | 7.226 | 5.575 | Yes | 60 |
| 12 years · district 10 | Ridge | 90% | 30 | 17 | 56.7% | 40.0%–73.3% | 47.053 | 7.226 | 6.512 | Yes | 60 |
| 12 years · district 10 | Random forest | 80% | 30 | 10 | 33.3% | 23.3%–46.7% | 35.056 | 7.226 | 4.851 | Yes | 60 |
| 12 years · district 10 | Random forest | 90% | 30 | 14 | 46.7% | 33.3%–56.7% | 38.283 | 7.226 | 5.298 | Yes | 60 |
| 12 years · district 20 | Ridge | 80% | 14 | 6 | 42.9% | 6.5%–85.7% | 27.569 | 7.402 | 3.725 | Yes | 37 |
| 12 years · district 20 | Ridge | 90% | 14 | 7 | 50.0% | 15.4%–87.5% | 32.959 | 7.402 | 4.453 | Yes | 37 |
| 12 years · district 20 | Random forest | 80% | 14 | 2 | 14.3% | 0.0%–36.4% | 29.056 | 7.402 | 3.926 | Yes | 37 |
| 12 years · district 20 | Random forest | 90% | 14 | 6 | 42.9% | 9.1%–78.6% | 32.813 | 7.402 | 4.433 | Yes | 37 |
| 12 years · district 30 | Ridge | 80% | 31 | 15 | 48.4% | 23.5%–76.7% | 29.512 | 6.127 | 4.817 | Yes | 63 |
| 12 years · district 30 | Ridge | 90% | 31 | 19 | 61.3% | 34.2%–90.0% | 33.606 | 6.127 | 5.485 | Yes | 63 |
| 12 years · district 30 | Random forest | 80% | 31 | 7 | 22.6% | 9.1%–37.9% | 36.082 | 6.127 | 5.889 | Yes | 63 |
| 12 years · district 30 | Random forest | 90% | 31 | 11 | 35.5% | 16.7%–59.3% | 40.604 | 6.127 | 6.627 | Yes | 63 |
| 12 years · district 40 | Ridge | 80% | 7 | 1 | 14.3% | 0.0%–50.0% | 22.588 | 8.780 | 2.573 | Yes | 59 |
| 12 years · district 40 | Ridge | 90% | 7 | 1 | 14.3% | 0.0%–50.0% | 30.533 | 8.780 | 3.478 | Yes | 59 |
| 12 years · district 40 | Random forest | 80% | 7 | 1 | 14.3% | 0.0%–50.0% | 24.525 | 8.780 | 2.793 | Yes | 59 |
| 12 years · district 40 | Random forest | 90% | 7 | 1 | 14.3% | 0.0%–50.0% | 32.829 | 8.780 | 3.739 | Yes | 59 |
| 12 years · district 50 | Ridge | 80% | 6 | 6 | 100.0% | — | 17.845 | 12.342 | 1.446 | — | 51 |
| 12 years · district 50 | Ridge | 90% | 6 | 6 | 100.0% | — | 21.783 | 12.342 | 1.765 | — | 51 |
| 12 years · district 50 | Random forest | 80% | 6 | 5 | 83.3% | — | 33.184 | 12.342 | 2.689 | — | 51 |
| 12 years · district 50 | Random forest | 90% | 6 | 6 | 100.0% | — | 41.215 | 12.342 | 3.339 | — | 51 |

</details>

### Interpretation and reproduction

- **Kansas spatial holdout.** Pooled coverage was 80.4% and 90.0% for ridge and 80.8% and 90.2% for random forest, at the nominal 80% and 90% levels. Use the below-nominal column for full-precision comparisons. In the Northeast reporting district (USDA code 70), the forest covered 59.6% and 72.6% of 277 county-years. For the highest annual-yield slice, 90% coverage fell to 76.4% for ridge and 77.3% for forest.
- **Kansas harvest-year holdout.** Both learners fell below both nominal levels when pooled. At the 90% level, ridge covered 88.3% and forest 85.8%. In 2007, they covered 46.6% and 37.9% of 103 county-years at that level. The high annual-yield slice reached 70.8% and 69.7% at 90%. The low annual-yield slice also fell short for both learners at both levels. Across the two pooled Kansas evaluations and both levels, interval width was 2.05–2.85 times the county-mean error, expressed as RMSE.
- **Spatial transfer on the P32 cohorts.** All eight state–model–level combinations fell short. At 90%, coverage was 85.3% for ridge and 87.2% for forest in Nebraska, and 86.1% and 83.9% in Oklahoma. Full widths at this level were 32.72 and 33.28 bu/acre, or 2.90–2.95 times Nebraska's county-mean RMSE and 3.56–3.62 times Oklahoma's.
- **Chronological recalibration on P37 rows.** Every pooled state–learner–level result fell short at every tested k. At 12 years, nominal 90% coverage reached 75.1% for ridge and 66.7% for forest in Nebraska and 56.8% and 43.2% in Oklahoma. Their widths ranged from 24.77 to 38.00 bu/acre. On these fixed P37 rows, local history changes interval width while keeping the Kansas center fixed. Several early Nebraska results contain an unbounded interval from the Northeast district. It has one test county-year, and the finite-sample rank exceeded the available local calibration residuals for those settings. The pooled mean width is unbounded whenever any contributing interval is unbounded.

Conformal nominal levels rely on exchangeability. District-level dependence, differences between training and test years, and shifts across states can violate that condition. Block bootstrap ranges summarize these archived test groups and do not restore a coverage guarantee. The local calibration uses district yield history that many farmers do not have. Weather–yield associations in county averages do not validate rotation recommendations.

Rebuild offline with `python -m src.yield_intervals`. The [report JSON](../data/processed/climate_yield_intervals.json) contains all sample counts, fold assignments, selected settings and data hashes. The [held-out intervals CSV](../data/processed/climate_yield_interval_predictions.csv) includes each outcome, center, lower and upper bound, and coverage indicator.

## P33b interval undercoverage diagnosis

The [preregistration](p33b_plan.md) was committed as `376aecc` before evaluation. P33b reconstructs the fixed P33 fits only to recover calibration predictions. The reconstruction reproduces the saved P33 centers and radii. The five methods adjust interval width around the same center. All prior data, settings and outputs remain as published.

### Calibration versus test residual spread

On the P37 design, each calibration residual is observed yield minus the frozen Kansas center. The calibration observations are out of sample for that center. At positive k, they come from the first k years in the district and go directly into the local radius. There is no local point fit. At k = 0, a Kansas reserved-district split supplies calibration residuals before the test origin. The leave-one-year-out scores coincide exactly with the reference because each year's observations already lie outside the center fit. A different leave-year-out result would require a different point-fitting design.

The ratio divides the sample SD of calibration errors by the sample SD of test errors. Errors are signed. Pooling repeats shared Kansas residuals for the districts that used them at k = 0. Test errors enter only this diagnostic. All positive-k ratios are below one. That is consistent with narrower calibration errors, while differences in error location and shape can also affect coverage.

| State | k | Learner | Calibration n | Test n | Calibration SD | Test SD | Calibration / test SD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nebraska | 0 | Ridge | 3535 | 462 | 6.845 | 10.861 | 0.630 |
| Nebraska | 0 | Forest | 3535 | 462 | 7.387 | 9.768 | 0.756 |
| Nebraska | 3 | Ridge | 173 | 462 | 8.565 | 10.861 | 0.789 |
| Nebraska | 3 | Forest | 173 | 462 | 7.283 | 9.768 | 0.746 |
| Nebraska | 5 | Ridge | 285 | 462 | 8.114 | 10.861 | 0.747 |
| Nebraska | 5 | Forest | 285 | 462 | 6.561 | 9.768 | 0.672 |
| Nebraska | 8 | Ridge | 461 | 462 | 7.710 | 10.861 | 0.710 |
| Nebraska | 8 | Forest | 461 | 462 | 6.700 | 9.768 | 0.686 |
| Nebraska | 12 | Ridge | 692 | 462 | 8.357 | 10.861 | 0.769 |
| Nebraska | 12 | Forest | 692 | 462 | 7.364 | 9.768 | 0.754 |
| Oklahoma | 0 | Ridge | 2310 | 88 | 7.130 | 7.990 | 0.892 |
| Oklahoma | 0 | Forest | 2310 | 88 | 7.501 | 6.576 | 1.141 |
| Oklahoma | 3 | Ridge | 95 | 88 | 5.279 | 7.990 | 0.661 |
| Oklahoma | 3 | Forest | 95 | 88 | 5.039 | 6.576 | 0.766 |
| Oklahoma | 5 | Ridge | 148 | 88 | 5.780 | 7.990 | 0.723 |
| Oklahoma | 5 | Forest | 148 | 88 | 5.377 | 6.576 | 0.818 |
| Oklahoma | 8 | Ridge | 196 | 88 | 6.958 | 7.990 | 0.871 |
| Oklahoma | 8 | Forest | 196 | 88 | 5.939 | 6.576 | 0.903 |
| Oklahoma | 12 | Ridge | 270 | 88 | 6.578 | 7.990 | 0.823 |
| Oklahoma | 12 | Forest | 270 | 88 | 6.101 | 6.576 | 0.928 |

### Method results

The analysis reports 254,260 intervals, counting each learner, level and method. The 2007 view repeats its existing year-holdout rows. The full widths are in bu/acre. The 95% intervals shown are block bootstrap intervals for empirical coverage, not for width. Unbounded intervals count as covered. The mean width is unbounded if any contributing interval is unbounded. Unavailable intervals are counted and omitted from coverage. Any coverage below nominal is marked.

| Protocol | Interval evaluations |
| --- | --- |
| Kansas district holdout | 64,300 |
| Kansas harvest-year holdout | 64,300 |
| P32 Kansas-to-target direct transfer | 70,660 |
| P37 chronological calibration | 55,000 |

#### Kansas

| Evaluation | Method | Learner | Nominal | n | Coverage [95% interval] | Mean width | Unbounded | Unavailable | Below nominal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| District holdout | P33 reference | Ridge | 80% | 3,215 | 80.4% [76.6%, 83.7%] | 24.92 | 0 | 0 | — |
| District holdout | Leave-one-year-out | Ridge | 80% | 3,215 | 80.4% [76.6%, 83.7%] | 24.92 | 0 | 0 | — |
| District holdout | Training-only inflation | Ridge | 80% | 3,215 | 87.6% [84.7%, 89.9%] | 29.75 | 0 | 0 | — |
| District holdout | Weather-regime Mondrian | Ridge | 80% | 3,215 | 79.5% [74.3%, 83.4%] | 24.58 | 0 | 0 | Yes |
| District holdout | Climate-similarity weighting | Ridge | 80% | 3,215 | 84.5% [80.0%, 87.8%] | Unbounded | 187 | 0 | — |
| District holdout | P33 reference | Ridge | 90% | 3,215 | 90.0% [87.4%, 92.0%] | 31.98 | 0 | 0 | Yes |
| District holdout | Leave-one-year-out | Ridge | 90% | 3,215 | 90.0% [87.4%, 92.0%] | 31.98 | 0 | 0 | Yes |
| District holdout | Training-only inflation | Ridge | 90% | 3,215 | 94.7% [93.0%, 96.1%] | 38.20 | 0 | 0 | — |
| District holdout | Weather-regime Mondrian | Ridge | 90% | 3,215 | 89.3% [85.3%, 92.4%] | 31.52 | 0 | 0 | Yes |
| District holdout | Climate-similarity weighting | Ridge | 90% | 3,215 | 92.7% [90.7%, 94.3%] | Unbounded | 340 | 0 | — |
| District holdout | P33 reference | Forest | 80% | 3,215 | 80.8% [75.8%, 85.0%] | 23.93 | 0 | 0 | — |
| District holdout | Leave-one-year-out | Forest | 80% | 3,215 | 80.8% [75.8%, 85.0%] | 23.93 | 0 | 0 | — |
| District holdout | Training-only inflation | Forest | 80% | 3,215 | 86.2% [81.8%, 89.9%] | 27.58 | 0 | 0 | — |
| District holdout | Weather-regime Mondrian | Forest | 80% | 3,215 | 80.2% [75.4%, 84.4%] | 23.80 | 0 | 0 | — |
| District holdout | Climate-similarity weighting | Forest | 80% | 3,215 | 82.7% [77.5%, 86.4%] | Unbounded | 187 | 0 | — |
| District holdout | P33 reference | Forest | 90% | 3,215 | 90.2% [86.3%, 93.2%] | 32.13 | 0 | 0 | — |
| District holdout | Leave-one-year-out | Forest | 90% | 3,215 | 90.2% [86.3%, 93.2%] | 32.13 | 0 | 0 | — |
| District holdout | Training-only inflation | Forest | 90% | 3,215 | 94.0% [91.1%, 96.5%] | 37.00 | 0 | 0 | — |
| District holdout | Weather-regime Mondrian | Forest | 90% | 3,215 | 89.3% [85.6%, 92.7%] | 31.63 | 0 | 0 | Yes |
| District holdout | Climate-similarity weighting | Forest | 90% | 3,215 | 91.6% [88.0%, 94.5%] | Unbounded | 340 | 0 | — |
| Harvest-year holdout | P33 reference | Ridge | 80% | 3,215 | 78.8% [72.9%, 84.2%] | 23.46 | 0 | 0 | Yes |
| Harvest-year holdout | Leave-one-year-out | Ridge | 80% | 3,215 | 78.8% [72.9%, 84.2%] | 23.46 | 0 | 0 | Yes |
| Harvest-year holdout | Training-only inflation | Ridge | 80% | 3,215 | 84.1% [78.3%, 88.8%] | 26.89 | 0 | 0 | — |
| Harvest-year holdout | Weather-regime Mondrian | Ridge | 80% | 3,215 | 79.1% [73.4%, 84.3%] | 23.87 | 0 | 0 | Yes |
| Harvest-year holdout | Climate-similarity weighting | Ridge | 80% | 3,215 | 79.2% [73.3%, 84.4%] | 24.08 | 0 | 0 | Yes |
| Harvest-year holdout | P33 reference | Ridge | 90% | 3,215 | 88.3% [83.4%, 92.1%] | 29.90 | 0 | 0 | Yes |
| Harvest-year holdout | Leave-one-year-out | Ridge | 90% | 3,215 | 88.3% [83.4%, 92.1%] | 29.90 | 0 | 0 | Yes |
| Harvest-year holdout | Training-only inflation | Ridge | 90% | 3,215 | 92.3% [87.8%, 95.5%] | 34.27 | 0 | 0 | — |
| Harvest-year holdout | Weather-regime Mondrian | Ridge | 90% | 3,215 | 88.8% [83.7%, 92.5%] | 30.35 | 0 | 0 | Yes |
| Harvest-year holdout | Climate-similarity weighting | Ridge | 90% | 3,215 | 88.9% [84.3%, 92.6%] | 30.52 | 0 | 0 | Yes |
| Harvest-year holdout | P33 reference | Forest | 80% | 3,215 | 75.5% [69.4%, 80.4%] | 22.21 | 0 | 0 | Yes |
| Harvest-year holdout | Leave-one-year-out | Forest | 80% | 3,215 | 75.5% [69.4%, 80.4%] | 22.21 | 0 | 0 | Yes |
| Harvest-year holdout | Training-only inflation | Forest | 80% | 3,215 | 81.9% [76.5%, 86.1%] | 25.47 | 0 | 0 | — |
| Harvest-year holdout | Weather-regime Mondrian | Forest | 80% | 3,215 | 75.6% [70.1%, 80.5%] | 22.59 | 0 | 0 | Yes |
| Harvest-year holdout | Climate-similarity weighting | Forest | 80% | 3,215 | 76.8% [70.9%, 81.3%] | 22.88 | 0 | 0 | Yes |
| Harvest-year holdout | P33 reference | Forest | 90% | 3,215 | 85.8% [80.7%, 89.8%] | 28.37 | 0 | 0 | Yes |
| Harvest-year holdout | Leave-one-year-out | Forest | 90% | 3,215 | 85.8% [80.7%, 89.8%] | 28.37 | 0 | 0 | Yes |
| Harvest-year holdout | Training-only inflation | Forest | 90% | 3,215 | 90.9% [86.3%, 94.2%] | 32.53 | 0 | 0 | — |
| Harvest-year holdout | Weather-regime Mondrian | Forest | 90% | 3,215 | 86.5% [81.7%, 90.4%] | 29.03 | 0 | 0 | Yes |
| Harvest-year holdout | Climate-similarity weighting | Forest | 90% | 3,215 | 87.0% [82.3%, 90.6%] | 29.43 | 0 | 0 | Yes |
| 2007 held-out year | P33 reference | Ridge | 80% | 103 | 38.8% [15.1%, 68.5%] | 22.61 | 0 | 0 | Yes |
| 2007 held-out year | Leave-one-year-out | Ridge | 80% | 103 | 38.8% [15.1%, 68.5%] | 22.61 | 0 | 0 | Yes |
| 2007 held-out year | Training-only inflation | Ridge | 80% | 103 | 38.8% [15.1%, 68.5%] | 23.77 | 0 | 0 | Yes |
| 2007 held-out year | Weather-regime Mondrian | Ridge | 80% | 103 | 38.8% [14.7%, 68.3%] | 22.55 | 0 | 0 | Yes |
| 2007 held-out year | Climate-similarity weighting | Ridge | 80% | 103 | 38.8% [15.1%, 68.5%] | 23.77 | 0 | 0 | Yes |
| 2007 held-out year | P33 reference | Ridge | 90% | 103 | 46.6% [21.9%, 76.0%] | 28.32 | 0 | 0 | Yes |
| 2007 held-out year | Leave-one-year-out | Ridge | 90% | 103 | 46.6% [21.9%, 76.0%] | 28.32 | 0 | 0 | Yes |
| 2007 held-out year | Training-only inflation | Ridge | 90% | 103 | 49.5% [25.7%, 77.5%] | 29.76 | 0 | 0 | Yes |
| 2007 held-out year | Weather-regime Mondrian | Ridge | 90% | 103 | 43.7% [19.5%, 74.0%] | 27.86 | 0 | 0 | Yes |
| 2007 held-out year | Climate-similarity weighting | Ridge | 90% | 103 | 49.5% [25.7%, 77.5%] | 29.64 | 0 | 0 | Yes |
| 2007 held-out year | P33 reference | Forest | 80% | 103 | 31.1% [7.8%, 60.0%] | 23.25 | 0 | 0 | Yes |
| 2007 held-out year | Leave-one-year-out | Forest | 80% | 103 | 31.1% [7.8%, 60.0%] | 23.25 | 0 | 0 | Yes |
| 2007 held-out year | Training-only inflation | Forest | 80% | 103 | 34.0% [10.9%, 63.6%] | 25.50 | 0 | 0 | Yes |
| 2007 held-out year | Weather-regime Mondrian | Forest | 80% | 103 | 33.0% [9.2%, 62.8%] | 24.41 | 0 | 0 | Yes |
| 2007 held-out year | Climate-similarity weighting | Forest | 80% | 103 | 33.0% [9.2%, 62.8%] | 25.27 | 0 | 0 | Yes |
| 2007 held-out year | P33 reference | Forest | 90% | 103 | 37.9% [15.3%, 66.4%] | 28.75 | 0 | 0 | Yes |
| 2007 held-out year | Leave-one-year-out | Forest | 90% | 103 | 37.9% [15.3%, 66.4%] | 28.75 | 0 | 0 | Yes |
| 2007 held-out year | Training-only inflation | Forest | 90% | 103 | 44.7% [23.2%, 71.8%] | 31.54 | 0 | 0 | Yes |
| 2007 held-out year | Weather-regime Mondrian | Forest | 90% | 103 | 41.7% [18.3%, 70.7%] | 30.12 | 0 | 0 | Yes |
| 2007 held-out year | Climate-similarity weighting | Forest | 90% | 103 | 42.7% [20.0%, 70.8%] | 30.72 | 0 | 0 | Yes |

<details>
<summary>All Kansas district outer folds</summary>

| Evaluation | Method | Learner | Nominal | n | Coverage [95% interval] | Mean width | Unbounded | Unavailable | Below nominal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | P33 reference | Ridge | 80% | 237 | 80.6% [72.1%, 88.1%] | 26.92 | 0 | 0 | — |
| 10 | Leave-one-year-out | Ridge | 80% | 237 | 80.6% [72.1%, 88.1%] | 26.92 | 0 | 0 | — |
| 10 | Training-only inflation | Ridge | 80% | 237 | 85.7% [78.7%, 91.6%] | 29.70 | 0 | 0 | — |
| 10 | Weather-regime Mondrian | Ridge | 80% | 237 | 81.9% [73.4%, 89.2%] | 28.16 | 0 | 0 | — |
| 10 | Climate-similarity weighting | Ridge | 80% | 237 | 82.7% [74.8%, 89.8%] | 28.55 | 0 | 0 | — |
| 10 | P33 reference | Ridge | 90% | 237 | 90.3% [84.2%, 95.2%] | 33.61 | 0 | 0 | — |
| 10 | Leave-one-year-out | Ridge | 90% | 237 | 90.3% [84.2%, 95.2%] | 33.61 | 0 | 0 | — |
| 10 | Training-only inflation | Ridge | 90% | 237 | 94.1% [88.8%, 98.0%] | 37.07 | 0 | 0 | — |
| 10 | Weather-regime Mondrian | Ridge | 90% | 237 | 90.3% [83.7%, 95.4%] | 34.01 | 0 | 0 | — |
| 10 | Climate-similarity weighting | Ridge | 90% | 237 | 92.4% [86.8%, 96.9%] | Unbounded | 13 | 0 | — |
| 10 | P33 reference | Forest | 80% | 237 | 81.9% [73.7%, 88.9%] | 25.20 | 0 | 0 | — |
| 10 | Leave-one-year-out | Forest | 80% | 237 | 81.9% [73.7%, 88.9%] | 25.20 | 0 | 0 | — |
| 10 | Training-only inflation | Forest | 80% | 237 | 89.9% [83.2%, 95.4%] | 30.45 | 0 | 0 | — |
| 10 | Weather-regime Mondrian | Forest | 80% | 237 | 81.0% [72.8%, 88.3%] | 24.73 | 0 | 0 | — |
| 10 | Climate-similarity weighting | Forest | 80% | 237 | 81.9% [73.7%, 88.9%] | 25.30 | 0 | 0 | — |
| 10 | P33 reference | Forest | 90% | 237 | 92.8% [87.2%, 97.5%] | 33.24 | 0 | 0 | — |
| 10 | Leave-one-year-out | Forest | 90% | 237 | 92.8% [87.2%, 97.5%] | 33.24 | 0 | 0 | — |
| 10 | Training-only inflation | Forest | 90% | 237 | 98.7% [96.5%, 100.0%] | 40.16 | 0 | 0 | — |
| 10 | Weather-regime Mondrian | Forest | 90% | 237 | 91.1% [85.3%, 96.3%] | 31.66 | 0 | 0 | — |
| 10 | Climate-similarity weighting | Forest | 90% | 237 | 95.4% [90.5%, 98.7%] | Unbounded | 13 | 0 | — |
| 20 | P33 reference | Ridge | 80% | 275 | 86.9% [81.0%, 92.1%] | 26.37 | 0 | 0 | — |
| 20 | Leave-one-year-out | Ridge | 80% | 275 | 86.9% [81.0%, 92.1%] | 26.37 | 0 | 0 | — |
| 20 | Training-only inflation | Ridge | 80% | 275 | 90.2% [85.0%, 95.1%] | 29.09 | 0 | 0 | — |
| 20 | Weather-regime Mondrian | Ridge | 80% | 275 | 86.9% [79.9%, 93.1%] | 27.13 | 0 | 0 | — |
| 20 | Climate-similarity weighting | Ridge | 80% | 275 | 92.0% [86.8%, 96.4%] | Unbounded | 31 | 0 | — |
| 20 | P33 reference | Ridge | 90% | 275 | 93.8% [89.8%, 97.1%] | 32.92 | 0 | 0 | — |
| 20 | Leave-one-year-out | Ridge | 90% | 275 | 93.8% [89.8%, 97.1%] | 32.92 | 0 | 0 | — |
| 20 | Training-only inflation | Ridge | 90% | 275 | 96.4% [93.5%, 98.9%] | 36.31 | 0 | 0 | — |
| 20 | Weather-regime Mondrian | Ridge | 90% | 275 | 94.2% [90.2%, 97.5%] | 33.90 | 0 | 0 | — |
| 20 | Climate-similarity weighting | Ridge | 90% | 275 | 96.7% [93.0%, 99.6%] | Unbounded | 70 | 0 | — |
| 20 | P33 reference | Forest | 80% | 275 | 88.4% [83.8%, 92.6%] | 24.38 | 0 | 0 | — |
| 20 | Leave-one-year-out | Forest | 80% | 275 | 88.4% [83.8%, 92.6%] | 24.38 | 0 | 0 | — |
| 20 | Training-only inflation | Forest | 80% | 275 | 94.2% [90.6%, 97.2%] | 28.83 | 0 | 0 | — |
| 20 | Weather-regime Mondrian | Forest | 80% | 275 | 88.7% [83.8%, 93.7%] | 25.65 | 0 | 0 | — |
| 20 | Climate-similarity weighting | Forest | 80% | 275 | 91.3% [86.2%, 95.6%] | Unbounded | 31 | 0 | — |
| 20 | P33 reference | Forest | 90% | 275 | 96.4% [93.3%, 99.0%] | 33.33 | 0 | 0 | — |
| 20 | Leave-one-year-out | Forest | 90% | 275 | 96.4% [93.3%, 99.0%] | 33.33 | 0 | 0 | — |
| 20 | Training-only inflation | Forest | 90% | 275 | 98.5% [96.6%, 100.0%] | 39.42 | 0 | 0 | — |
| 20 | Weather-regime Mondrian | Forest | 90% | 275 | 94.9% [91.2%, 98.2%] | 33.85 | 0 | 0 | — |
| 20 | Climate-similarity weighting | Forest | 90% | 275 | 97.1% [94.2%, 99.3%] | Unbounded | 70 | 0 | — |
| 30 | P33 reference | Ridge | 80% | 424 | 72.9% [63.8%, 81.3%] | 23.81 | 0 | 0 | Yes |
| 30 | Leave-one-year-out | Ridge | 80% | 424 | 72.9% [63.8%, 81.3%] | 23.81 | 0 | 0 | Yes |
| 30 | Training-only inflation | Ridge | 80% | 424 | 81.4% [73.2%, 88.6%] | 28.96 | 0 | 0 | — |
| 30 | Weather-regime Mondrian | Ridge | 80% | 424 | 66.5% [57.5%, 75.0%] | 21.30 | 0 | 0 | Yes |
| 30 | Climate-similarity weighting | Ridge | 80% | 424 | 89.6% [82.7%, 94.8%] | Unbounded | 133 | 0 | — |
| 30 | P33 reference | Ridge | 90% | 424 | 84.4% [77.5%, 91.0%] | 30.83 | 0 | 0 | Yes |
| 30 | Leave-one-year-out | Ridge | 90% | 424 | 84.4% [77.5%, 91.0%] | 30.83 | 0 | 0 | Yes |
| 30 | Training-only inflation | Ridge | 90% | 424 | 90.8% [85.2%, 95.5%] | 37.50 | 0 | 0 | — |
| 30 | Weather-regime Mondrian | Ridge | 90% | 424 | 78.3% [69.6%, 86.5%] | 27.63 | 0 | 0 | Yes |
| 30 | Climate-similarity weighting | Ridge | 90% | 424 | 94.8% [89.5%, 98.6%] | Unbounded | 184 | 0 | — |
| 30 | P33 reference | Forest | 80% | 424 | 79.5% [72.4%, 84.9%] | 23.27 | 0 | 0 | Yes |
| 30 | Leave-one-year-out | Forest | 80% | 424 | 79.5% [72.4%, 84.9%] | 23.27 | 0 | 0 | Yes |
| 30 | Training-only inflation | Forest | 80% | 424 | 87.7% [82.0%, 92.3%] | 27.29 | 0 | 0 | — |
| 30 | Weather-regime Mondrian | Forest | 80% | 424 | 76.2% [69.0%, 82.4%] | 21.72 | 0 | 0 | Yes |
| 30 | Climate-similarity weighting | Forest | 80% | 424 | 84.4% [77.4%, 90.2%] | Unbounded | 133 | 0 | — |
| 30 | P33 reference | Forest | 90% | 424 | 90.3% [85.4%, 94.2%] | 30.15 | 0 | 0 | — |
| 30 | Leave-one-year-out | Forest | 90% | 424 | 90.3% [85.4%, 94.2%] | 30.15 | 0 | 0 | — |
| 30 | Training-only inflation | Forest | 90% | 424 | 94.8% [91.6%, 97.3%] | 35.36 | 0 | 0 | — |
| 30 | Weather-regime Mondrian | Forest | 90% | 424 | 88.4% [82.9%, 92.9%] | 28.93 | 0 | 0 | Yes |
| 30 | Climate-similarity weighting | Forest | 90% | 424 | 93.4% [88.7%, 97.1%] | Unbounded | 184 | 0 | — |
| 40 | P33 reference | Ridge | 80% | 349 | 79.9% [70.3%, 88.2%] | 25.58 | 0 | 0 | Yes |
| 40 | Leave-one-year-out | Ridge | 80% | 349 | 79.9% [70.3%, 88.2%] | 25.58 | 0 | 0 | Yes |
| 40 | Training-only inflation | Ridge | 80% | 349 | 88.3% [81.6%, 94.2%] | 30.85 | 0 | 0 | — |
| 40 | Weather-regime Mondrian | Ridge | 80% | 349 | 80.8% [71.3%, 89.1%] | 26.53 | 0 | 0 | — |
| 40 | Climate-similarity weighting | Ridge | 80% | 349 | 80.5% [71.1%, 88.8%] | 25.90 | 0 | 0 | — |
| 40 | P33 reference | Ridge | 90% | 349 | 90.8% [84.6%, 95.9%] | 32.14 | 0 | 0 | — |
| 40 | Leave-one-year-out | Ridge | 90% | 349 | 90.8% [84.6%, 95.9%] | 32.14 | 0 | 0 | — |
| 40 | Training-only inflation | Ridge | 90% | 349 | 96.6% [92.7%, 99.4%] | 38.76 | 0 | 0 | — |
| 40 | Weather-regime Mondrian | Ridge | 90% | 349 | 94.3% [88.9%, 98.3%] | 34.59 | 0 | 0 | — |
| 40 | Climate-similarity weighting | Ridge | 90% | 349 | 91.1% [84.7%, 96.1%] | 32.69 | 0 | 0 | — |
| 40 | P33 reference | Forest | 80% | 349 | 86.2% [79.2%, 92.5%] | 24.32 | 0 | 0 | — |
| 40 | Leave-one-year-out | Forest | 80% | 349 | 86.2% [79.2%, 92.5%] | 24.32 | 0 | 0 | — |
| 40 | Training-only inflation | Forest | 80% | 349 | 87.7% [81.2%, 93.3%] | 26.28 | 0 | 0 | — |
| 40 | Weather-regime Mondrian | Forest | 80% | 349 | 86.8% [79.5%, 92.8%] | 25.51 | 0 | 0 | — |
| 40 | Climate-similarity weighting | Forest | 80% | 349 | 86.2% [79.2%, 92.5%] | 24.04 | 0 | 0 | — |
| 40 | P33 reference | Forest | 90% | 349 | 93.4% [88.4%, 97.7%] | 32.85 | 0 | 0 | — |
| 40 | Leave-one-year-out | Forest | 90% | 349 | 93.4% [88.4%, 97.7%] | 32.85 | 0 | 0 | — |
| 40 | Training-only inflation | Forest | 90% | 349 | 96.8% [93.3%, 99.2%] | 35.50 | 0 | 0 | — |
| 40 | Weather-regime Mondrian | Forest | 90% | 349 | 96.3% [92.5%, 99.1%] | 36.06 | 0 | 0 | — |
| 40 | Climate-similarity weighting | Forest | 90% | 349 | 94.3% [89.1%, 98.1%] | 33.26 | 0 | 0 | — |
| 50 | P33 reference | Ridge | 80% | 352 | 85.5% [76.9%, 93.1%] | 24.96 | 0 | 0 | — |
| 50 | Leave-one-year-out | Ridge | 80% | 352 | 85.5% [76.9%, 93.1%] | 24.96 | 0 | 0 | — |
| 50 | Training-only inflation | Ridge | 80% | 352 | 91.8% [84.9%, 97.1%] | 30.06 | 0 | 0 | — |
| 50 | Weather-regime Mondrian | Ridge | 80% | 352 | 85.2% [76.4%, 92.8%] | 24.53 | 0 | 0 | — |
| 50 | Climate-similarity weighting | Ridge | 80% | 352 | 87.8% [79.4%, 94.5%] | 25.63 | 0 | 0 | — |
| 50 | P33 reference | Ridge | 90% | 352 | 93.5% [87.4%, 98.0%] | 31.89 | 0 | 0 | — |
| 50 | Leave-one-year-out | Ridge | 90% | 352 | 93.5% [87.4%, 98.0%] | 31.89 | 0 | 0 | — |
| 50 | Training-only inflation | Ridge | 90% | 352 | 96.9% [93.1%, 99.2%] | 38.40 | 0 | 0 | — |
| 50 | Weather-regime Mondrian | Ridge | 90% | 352 | 93.5% [87.2%, 98.1%] | 31.24 | 0 | 0 | — |
| 50 | Climate-similarity weighting | Ridge | 90% | 352 | 94.0% [88.3%, 98.3%] | 33.07 | 0 | 0 | — |
| 50 | P33 reference | Forest | 80% | 352 | 88.4% [81.1%, 94.4%] | 23.92 | 0 | 0 | — |
| 50 | Leave-one-year-out | Forest | 80% | 352 | 88.4% [81.1%, 94.4%] | 23.92 | 0 | 0 | — |
| 50 | Training-only inflation | Forest | 80% | 352 | 92.6% [87.1%, 97.1%] | 28.26 | 0 | 0 | — |
| 50 | Weather-regime Mondrian | Forest | 80% | 352 | 86.4% [78.5%, 93.2%] | 23.54 | 0 | 0 | — |
| 50 | Climate-similarity weighting | Forest | 80% | 352 | 88.4% [81.7%, 94.2%] | 23.87 | 0 | 0 | — |
| 50 | P33 reference | Forest | 90% | 352 | 94.9% [89.8%, 98.3%] | 30.68 | 0 | 0 | — |
| 50 | Leave-one-year-out | Forest | 90% | 352 | 94.9% [89.8%, 98.3%] | 30.68 | 0 | 0 | — |
| 50 | Training-only inflation | Forest | 90% | 352 | 97.4% [93.6%, 99.7%] | 36.24 | 0 | 0 | — |
| 50 | Weather-regime Mondrian | Forest | 90% | 352 | 94.3% [89.7%, 97.7%] | 29.68 | 0 | 0 | — |
| 50 | Climate-similarity weighting | Forest | 90% | 352 | 95.7% [91.9%, 98.6%] | 31.11 | 0 | 0 | — |
| 60 | P33 reference | Ridge | 80% | 418 | 85.2% [77.8%, 91.3%] | 24.30 | 0 | 0 | — |
| 60 | Leave-one-year-out | Ridge | 80% | 418 | 85.2% [77.8%, 91.3%] | 24.30 | 0 | 0 | — |
| 60 | Training-only inflation | Ridge | 80% | 418 | 89.7% [83.9%, 94.4%] | 29.27 | 0 | 0 | — |
| 60 | Weather-regime Mondrian | Ridge | 80% | 418 | 81.1% [73.0%, 88.0%] | 22.46 | 0 | 0 | — |
| 60 | Climate-similarity weighting | Ridge | 80% | 418 | 87.6% [81.1%, 92.9%] | 25.92 | 0 | 0 | — |
| 60 | P33 reference | Ridge | 90% | 418 | 91.4% [85.9%, 95.8%] | 31.72 | 0 | 0 | — |
| 60 | Leave-one-year-out | Ridge | 90% | 418 | 91.4% [85.9%, 95.8%] | 31.72 | 0 | 0 | — |
| 60 | Training-only inflation | Ridge | 90% | 418 | 95.9% [92.0%, 98.8%] | 38.20 | 0 | 0 | — |
| 60 | Weather-regime Mondrian | Ridge | 90% | 418 | 90.2% [84.2%, 95.0%] | 29.51 | 0 | 0 | — |
| 60 | Climate-similarity weighting | Ridge | 90% | 418 | 93.5% [88.6%, 97.6%] | Unbounded | 13 | 0 | — |
| 60 | P33 reference | Forest | 80% | 418 | 78.7% [69.3%, 87.4%] | 23.63 | 0 | 0 | Yes |
| 60 | Leave-one-year-out | Forest | 80% | 418 | 78.7% [69.3%, 87.4%] | 23.63 | 0 | 0 | Yes |
| 60 | Training-only inflation | Forest | 80% | 418 | 84.2% [75.7%, 91.7%] | 27.95 | 0 | 0 | — |
| 60 | Weather-regime Mondrian | Forest | 80% | 418 | 78.0% [69.0%, 86.1%] | 21.86 | 0 | 0 | Yes |
| 60 | Climate-similarity weighting | Forest | 80% | 418 | 80.1% [71.1%, 88.3%] | 24.21 | 0 | 0 | — |
| 60 | P33 reference | Forest | 90% | 418 | 88.3% [80.0%, 94.8%] | 30.83 | 0 | 0 | Yes |
| 60 | Leave-one-year-out | Forest | 90% | 418 | 88.3% [80.0%, 94.8%] | 30.83 | 0 | 0 | Yes |
| 60 | Training-only inflation | Forest | 90% | 418 | 91.9% [84.5%, 97.1%] | 36.47 | 0 | 0 | — |
| 60 | Weather-regime Mondrian | Forest | 90% | 418 | 83.5% [74.5%, 90.7%] | 26.92 | 0 | 0 | Yes |
| 60 | Climate-similarity weighting | Forest | 90% | 418 | 89.0% [80.9%, 95.3%] | Unbounded | 13 | 0 | Yes |
| 70 | P33 reference | Ridge | 80% | 277 | 68.2% [57.6%, 78.1%] | 24.48 | 0 | 0 | Yes |
| 70 | Leave-one-year-out | Ridge | 80% | 277 | 68.2% [57.6%, 78.1%] | 24.48 | 0 | 0 | Yes |
| 70 | Training-only inflation | Ridge | 80% | 277 | 79.8% [70.7%, 87.8%] | 29.52 | 0 | 0 | Yes |
| 70 | Weather-regime Mondrian | Ridge | 80% | 277 | 69.3% [58.7%, 79.1%] | 24.46 | 0 | 0 | Yes |
| 70 | Climate-similarity weighting | Ridge | 80% | 277 | 66.1% [55.6%, 75.4%] | 23.71 | 0 | 0 | Yes |
| 70 | P33 reference | Ridge | 90% | 277 | 82.7% [73.1%, 90.6%] | 30.96 | 0 | 0 | Yes |
| 70 | Leave-one-year-out | Ridge | 90% | 277 | 82.7% [73.1%, 90.6%] | 30.96 | 0 | 0 | Yes |
| 70 | Training-only inflation | Ridge | 90% | 277 | 89.9% [81.4%, 96.7%] | 37.34 | 0 | 0 | Yes |
| 70 | Weather-regime Mondrian | Ridge | 90% | 277 | 83.4% [74.3%, 91.3%] | 31.25 | 0 | 0 | Yes |
| 70 | Climate-similarity weighting | Ridge | 90% | 277 | 83.8% [74.5%, 91.3%] | 31.06 | 0 | 0 | Yes |
| 70 | P33 reference | Forest | 80% | 277 | 59.6% [48.4%, 70.2%] | 21.10 | 0 | 0 | Yes |
| 70 | Leave-one-year-out | Forest | 80% | 277 | 59.6% [48.4%, 70.2%] | 21.10 | 0 | 0 | Yes |
| 70 | Training-only inflation | Forest | 80% | 277 | 66.8% [55.5%, 77.8%] | 24.96 | 0 | 0 | Yes |
| 70 | Weather-regime Mondrian | Forest | 80% | 277 | 61.4% [50.2%, 71.8%] | 21.75 | 0 | 0 | Yes |
| 70 | Climate-similarity weighting | Forest | 80% | 277 | 60.3% [49.1%, 70.8%] | 21.73 | 0 | 0 | Yes |
| 70 | P33 reference | Forest | 90% | 277 | 72.6% [61.5%, 82.8%] | 28.55 | 0 | 0 | Yes |
| 70 | Leave-one-year-out | Forest | 90% | 277 | 72.6% [61.5%, 82.8%] | 28.55 | 0 | 0 | Yes |
| 70 | Training-only inflation | Forest | 90% | 277 | 80.5% [70.3%, 89.1%] | 33.77 | 0 | 0 | Yes |
| 70 | Weather-regime Mondrian | Forest | 90% | 277 | 74.0% [62.5%, 83.9%] | 28.95 | 0 | 0 | Yes |
| 70 | Climate-similarity weighting | Forest | 90% | 277 | 75.5% [64.5%, 85.1%] | 29.31 | 0 | 0 | Yes |
| 80 | P33 reference | Ridge | 80% | 442 | 82.1% [72.4%, 90.4%] | 24.70 | 0 | 0 | — |
| 80 | Leave-one-year-out | Ridge | 80% | 442 | 82.1% [72.4%, 90.4%] | 24.70 | 0 | 0 | — |
| 80 | Training-only inflation | Ridge | 80% | 442 | 90.3% [82.6%, 96.5%] | 30.17 | 0 | 0 | — |
| 80 | Weather-regime Mondrian | Ridge | 80% | 442 | 84.8% [75.3%, 92.9%] | 25.75 | 0 | 0 | — |
| 80 | Climate-similarity weighting | Ridge | 80% | 442 | 84.4% [75.3%, 92.2%] | 25.47 | 0 | 0 | — |
| 80 | P33 reference | Ridge | 90% | 442 | 91.9% [84.6%, 97.4%] | 32.39 | 0 | 0 | — |
| 80 | Leave-one-year-out | Ridge | 90% | 442 | 91.9% [84.6%, 97.4%] | 32.39 | 0 | 0 | — |
| 80 | Training-only inflation | Ridge | 90% | 442 | 95.7% [91.8%, 98.9%] | 39.57 | 0 | 0 | — |
| 80 | Weather-regime Mondrian | Ridge | 90% | 442 | 92.3% [85.0%, 97.9%] | 33.12 | 0 | 0 | — |
| 80 | Climate-similarity weighting | Ridge | 90% | 442 | 92.8% [86.3%, 97.6%] | 34.19 | 0 | 0 | — |
| 80 | P33 reference | Forest | 80% | 442 | 84.2% [76.3%, 91.3%] | 25.22 | 0 | 0 | — |
| 80 | Leave-one-year-out | Forest | 80% | 442 | 84.2% [76.3%, 91.3%] | 25.22 | 0 | 0 | — |
| 80 | Training-only inflation | Forest | 80% | 442 | 87.6% [80.0%, 94.2%] | 28.10 | 0 | 0 | — |
| 80 | Weather-regime Mondrian | Forest | 80% | 442 | 85.5% [77.8%, 92.3%] | 26.18 | 0 | 0 | — |
| 80 | Climate-similarity weighting | Forest | 80% | 442 | 85.1% [77.8%, 92.1%] | 26.65 | 0 | 0 | — |
| 80 | P33 reference | Forest | 90% | 442 | 90.7% [84.4%, 96.3%] | 34.42 | 0 | 0 | — |
| 80 | Leave-one-year-out | Forest | 90% | 442 | 90.7% [84.4%, 96.3%] | 34.42 | 0 | 0 | — |
| 80 | Training-only inflation | Forest | 90% | 442 | 93.7% [87.7%, 98.6%] | 38.33 | 0 | 0 | — |
| 80 | Weather-regime Mondrian | Forest | 90% | 442 | 90.7% [84.5%, 95.9%] | 35.27 | 0 | 0 | — |
| 80 | Climate-similarity weighting | Forest | 90% | 442 | 91.4% [85.0%, 96.8%] | 36.13 | 0 | 0 | — |
| 90 | P33 reference | Ridge | 80% | 441 | 81.4% [72.5%, 87.8%] | 24.55 | 0 | 0 | — |
| 90 | Leave-one-year-out | Ridge | 80% | 441 | 81.4% [72.5%, 87.8%] | 24.55 | 0 | 0 | — |
| 90 | Training-only inflation | Ridge | 80% | 441 | 89.1% [80.6%, 94.6%] | 29.99 | 0 | 0 | — |
| 90 | Weather-regime Mondrian | Ridge | 80% | 441 | 80.0% [70.9%, 86.6%] | 23.64 | 0 | 0 | — |
| 90 | Climate-similarity weighting | Ridge | 80% | 441 | 85.3% [76.8%, 91.2%] | Unbounded | 23 | 0 | — |
| 90 | P33 reference | Ridge | 90% | 441 | 90.5% [81.7%, 95.6%] | 32.08 | 0 | 0 | — |
| 90 | Leave-one-year-out | Ridge | 90% | 441 | 90.5% [81.7%, 95.6%] | 32.08 | 0 | 0 | — |
| 90 | Training-only inflation | Ridge | 90% | 441 | 95.2% [87.7%, 99.3%] | 39.19 | 0 | 0 | — |
| 90 | Weather-regime Mondrian | Ridge | 90% | 441 | 88.9% [80.0%, 94.4%] | 30.72 | 0 | 0 | Yes |
| 90 | Climate-similarity weighting | Ridge | 90% | 441 | 93.4% [85.8%, 97.7%] | Unbounded | 60 | 0 | — |
| 90 | P33 reference | Forest | 80% | 441 | 78.5% [70.4%, 85.4%] | 24.07 | 0 | 0 | Yes |
| 90 | Leave-one-year-out | Forest | 80% | 441 | 78.5% [70.4%, 85.4%] | 24.07 | 0 | 0 | Yes |
| 90 | Training-only inflation | Forest | 80% | 441 | 84.4% [77.5%, 90.1%] | 26.81 | 0 | 0 | — |
| 90 | Weather-regime Mondrian | Forest | 80% | 441 | 77.1% [69.6%, 83.8%] | 23.75 | 0 | 0 | Yes |
| 90 | Climate-similarity weighting | Forest | 80% | 441 | 83.0% [75.1%, 89.7%] | Unbounded | 23 | 0 | — |
| 90 | P33 reference | Forest | 90% | 441 | 90.9% [85.3%, 95.5%] | 34.47 | 0 | 0 | — |
| 90 | Leave-one-year-out | Forest | 90% | 441 | 90.9% [85.3%, 95.5%] | 34.47 | 0 | 0 | — |
| 90 | Training-only inflation | Forest | 90% | 441 | 93.7% [87.9%, 97.4%] | 38.39 | 0 | 0 | — |
| 90 | Weather-regime Mondrian | Forest | 90% | 441 | 89.8% [84.3%, 94.4%] | 33.34 | 0 | 0 | Yes |
| 90 | Climate-similarity weighting | Forest | 90% | 441 | 91.6% [85.5%, 96.3%] | Unbounded | 60 | 0 | — |

</details>

<details>
<summary>All Kansas harvest-year outer folds</summary>

| Evaluation | Method | Learner | Nominal | n | Coverage [95% interval] | Mean width | Unbounded | Unavailable | Below nominal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1990 | P33 reference | Ridge | 80% | 103 | 80.6% [62.4%, 93.4%] | 22.80 | 0 | 0 | — |
| 1990 | Leave-one-year-out | Ridge | 80% | 103 | 80.6% [62.4%, 93.4%] | 22.80 | 0 | 0 | — |
| 1990 | Training-only inflation | Ridge | 80% | 103 | 84.5% [65.4%, 97.0%] | 27.03 | 0 | 0 | — |
| 1990 | Weather-regime Mondrian | Ridge | 80% | 103 | 78.6% [60.6%, 92.5%] | 23.10 | 0 | 0 | Yes |
| 1990 | Climate-similarity weighting | Ridge | 80% | 103 | 80.6% [62.4%, 93.4%] | 23.77 | 0 | 0 | — |
| 1990 | P33 reference | Ridge | 90% | 103 | 88.3% [70.6%, 99.0%] | 29.70 | 0 | 0 | Yes |
| 1990 | Leave-one-year-out | Ridge | 90% | 103 | 88.3% [70.6%, 99.0%] | 29.70 | 0 | 0 | Yes |
| 1990 | Training-only inflation | Ridge | 90% | 103 | 94.2% [82.5%, 100.0%] | 35.21 | 0 | 0 | — |
| 1990 | Weather-regime Mondrian | Ridge | 90% | 103 | 89.3% [73.5%, 99.0%] | 30.19 | 0 | 0 | Yes |
| 1990 | Climate-similarity weighting | Ridge | 90% | 103 | 89.3% [71.7%, 99.1%] | 30.42 | 0 | 0 | Yes |
| 1990 | P33 reference | Forest | 80% | 103 | 77.7% [55.3%, 93.8%] | 20.71 | 0 | 0 | Yes |
| 1990 | Leave-one-year-out | Forest | 80% | 103 | 77.7% [55.3%, 93.8%] | 20.71 | 0 | 0 | Yes |
| 1990 | Training-only inflation | Forest | 80% | 103 | 86.4% [67.0%, 98.2%] | 25.52 | 0 | 0 | — |
| 1990 | Weather-regime Mondrian | Forest | 80% | 103 | 75.7% [53.8%, 91.7%] | 20.86 | 0 | 0 | Yes |
| 1990 | Climate-similarity weighting | Forest | 80% | 103 | 78.6% [56.5%, 94.5%] | 21.65 | 0 | 0 | Yes |
| 1990 | P33 reference | Forest | 90% | 103 | 87.4% [67.6%, 100.0%] | 26.51 | 0 | 0 | Yes |
| 1990 | Leave-one-year-out | Forest | 90% | 103 | 87.4% [67.6%, 100.0%] | 26.51 | 0 | 0 | Yes |
| 1990 | Training-only inflation | Forest | 90% | 103 | 91.3% [75.7%, 100.0%] | 32.67 | 0 | 0 | — |
| 1990 | Weather-regime Mondrian | Forest | 90% | 103 | 88.3% [68.6%, 100.0%] | 26.52 | 0 | 0 | Yes |
| 1990 | Climate-similarity weighting | Forest | 90% | 103 | 87.4% [67.6%, 100.0%] | 27.18 | 0 | 0 | Yes |
| 1991 | P33 reference | Ridge | 80% | 103 | 94.2% [89.7%, 97.4%] | 22.95 | 0 | 0 | — |
| 1991 | Leave-one-year-out | Ridge | 80% | 103 | 94.2% [89.7%, 97.4%] | 22.95 | 0 | 0 | — |
| 1991 | Training-only inflation | Ridge | 80% | 103 | 100.0% [100.0%, 100.0%] | 27.54 | 0 | 0 | — |
| 1991 | Weather-regime Mondrian | Ridge | 80% | 103 | 96.1% [91.2%, 100.0%] | 22.97 | 0 | 0 | — |
| 1991 | Climate-similarity weighting | Ridge | 80% | 103 | 96.1% [91.2%, 100.0%] | 24.49 | 0 | 0 | — |
| 1991 | P33 reference | Ridge | 90% | 103 | 100.0% [100.0%, 100.0%] | 29.78 | 0 | 0 | — |
| 1991 | Leave-one-year-out | Ridge | 90% | 103 | 100.0% [100.0%, 100.0%] | 29.78 | 0 | 0 | — |
| 1991 | Training-only inflation | Ridge | 90% | 103 | 100.0% [100.0%, 100.0%] | 35.75 | 0 | 0 | — |
| 1991 | Weather-regime Mondrian | Ridge | 90% | 103 | 100.0% [100.0%, 100.0%] | 29.99 | 0 | 0 | — |
| 1991 | Climate-similarity weighting | Ridge | 90% | 103 | 100.0% [100.0%, 100.0%] | 30.95 | 0 | 0 | — |
| 1991 | P33 reference | Forest | 80% | 103 | 82.5% [68.5%, 93.8%] | 20.41 | 0 | 0 | — |
| 1991 | Leave-one-year-out | Forest | 80% | 103 | 82.5% [68.5%, 93.8%] | 20.41 | 0 | 0 | — |
| 1991 | Training-only inflation | Forest | 80% | 103 | 94.2% [86.4%, 100.0%] | 27.15 | 0 | 0 | — |
| 1991 | Weather-regime Mondrian | Forest | 80% | 103 | 81.6% [68.2%, 92.8%] | 20.07 | 0 | 0 | — |
| 1991 | Climate-similarity weighting | Forest | 80% | 103 | 83.5% [68.5%, 95.1%] | 21.55 | 0 | 0 | — |
| 1991 | P33 reference | Forest | 90% | 103 | 92.2% [81.8%, 100.0%] | 26.19 | 0 | 0 | — |
| 1991 | Leave-one-year-out | Forest | 90% | 103 | 92.2% [81.8%, 100.0%] | 26.19 | 0 | 0 | — |
| 1991 | Training-only inflation | Forest | 90% | 103 | 97.1% [90.4%, 100.0%] | 34.84 | 0 | 0 | — |
| 1991 | Weather-regime Mondrian | Forest | 90% | 103 | 91.3% [81.4%, 100.0%] | 26.36 | 0 | 0 | — |
| 1991 | Climate-similarity weighting | Forest | 90% | 103 | 94.2% [86.4%, 100.0%] | 27.40 | 0 | 0 | — |
| 1992 | P33 reference | Ridge | 80% | 103 | 84.5% [71.9%, 94.1%] | 23.00 | 0 | 0 | — |
| 1992 | Leave-one-year-out | Ridge | 80% | 103 | 84.5% [71.9%, 94.1%] | 23.00 | 0 | 0 | — |
| 1992 | Training-only inflation | Ridge | 80% | 103 | 90.3% [80.6%, 97.4%] | 26.35 | 0 | 0 | — |
| 1992 | Weather-regime Mondrian | Ridge | 80% | 103 | 82.5% [71.3%, 91.3%] | 22.48 | 0 | 0 | — |
| 1992 | Climate-similarity weighting | Ridge | 80% | 103 | 83.5% [71.1%, 93.3%] | 22.35 | 0 | 0 | — |
| 1992 | P33 reference | Ridge | 90% | 103 | 95.1% [92.4%, 98.1%] | 29.43 | 0 | 0 | — |
| 1992 | Leave-one-year-out | Ridge | 90% | 103 | 95.1% [92.4%, 98.1%] | 29.43 | 0 | 0 | — |
| 1992 | Training-only inflation | Ridge | 90% | 103 | 97.1% [93.6%, 100.0%] | 33.72 | 0 | 0 | — |
| 1992 | Weather-regime Mondrian | Ridge | 90% | 103 | 95.1% [92.4%, 98.1%] | 29.51 | 0 | 0 | — |
| 1992 | Climate-similarity weighting | Ridge | 90% | 103 | 95.1% [92.4%, 98.1%] | 29.07 | 0 | 0 | — |
| 1992 | P33 reference | Forest | 80% | 103 | 70.9% [57.6%, 84.9%] | 20.94 | 0 | 0 | Yes |
| 1992 | Leave-one-year-out | Forest | 80% | 103 | 70.9% [57.6%, 84.9%] | 20.94 | 0 | 0 | Yes |
| 1992 | Training-only inflation | Forest | 80% | 103 | 77.7% [63.5%, 91.8%] | 27.30 | 0 | 0 | Yes |
| 1992 | Weather-regime Mondrian | Forest | 80% | 103 | 70.9% [57.6%, 84.9%] | 21.28 | 0 | 0 | Yes |
| 1992 | Climate-similarity weighting | Forest | 80% | 103 | 71.8% [58.3%, 86.0%] | 21.84 | 0 | 0 | Yes |
| 1992 | P33 reference | Forest | 90% | 103 | 77.7% [63.5%, 91.8%] | 26.84 | 0 | 0 | Yes |
| 1992 | Leave-one-year-out | Forest | 90% | 103 | 77.7% [63.5%, 91.8%] | 26.84 | 0 | 0 | Yes |
| 1992 | Training-only inflation | Forest | 90% | 103 | 85.4% [71.7%, 97.4%] | 35.00 | 0 | 0 | Yes |
| 1992 | Weather-regime Mondrian | Forest | 90% | 103 | 78.6% [64.1%, 92.2%] | 27.23 | 0 | 0 | Yes |
| 1992 | Climate-similarity weighting | Forest | 90% | 103 | 78.6% [64.1%, 92.2%] | 28.03 | 0 | 0 | Yes |
| 1993 | P33 reference | Ridge | 80% | 103 | 65.0% [42.3%, 84.1%] | 22.14 | 0 | 0 | Yes |
| 1993 | Leave-one-year-out | Ridge | 80% | 103 | 65.0% [42.3%, 84.1%] | 22.14 | 0 | 0 | Yes |
| 1993 | Training-only inflation | Ridge | 80% | 103 | 74.8% [52.9%, 92.0%] | 26.81 | 0 | 0 | Yes |
| 1993 | Weather-regime Mondrian | Ridge | 80% | 103 | 65.0% [42.3%, 84.1%] | 21.48 | 0 | 0 | Yes |
| 1993 | Climate-similarity weighting | Ridge | 80% | 103 | 64.1% [41.3%, 82.5%] | 20.46 | 0 | 0 | Yes |
| 1993 | P33 reference | Ridge | 90% | 103 | 78.6% [56.4%, 95.5%] | 28.49 | 0 | 0 | Yes |
| 1993 | Leave-one-year-out | Ridge | 90% | 103 | 78.6% [56.4%, 95.5%] | 28.49 | 0 | 0 | Yes |
| 1993 | Training-only inflation | Ridge | 90% | 103 | 92.2% [83.0%, 100.0%] | 34.50 | 0 | 0 | — |
| 1993 | Weather-regime Mondrian | Ridge | 90% | 103 | 77.7% [56.2%, 94.6%] | 28.37 | 0 | 0 | Yes |
| 1993 | Climate-similarity weighting | Ridge | 90% | 103 | 74.8% [52.9%, 92.0%] | 27.19 | 0 | 0 | Yes |
| 1993 | P33 reference | Forest | 80% | 103 | 76.7% [58.6%, 91.0%] | 21.07 | 0 | 0 | Yes |
| 1993 | Leave-one-year-out | Forest | 80% | 103 | 76.7% [58.6%, 91.0%] | 21.07 | 0 | 0 | Yes |
| 1993 | Training-only inflation | Forest | 80% | 103 | 80.6% [63.6%, 93.8%] | 23.05 | 0 | 0 | — |
| 1993 | Weather-regime Mondrian | Forest | 80% | 103 | 79.6% [63.3%, 92.7%] | 22.70 | 0 | 0 | Yes |
| 1993 | Climate-similarity weighting | Forest | 80% | 103 | 81.6% [66.3%, 93.8%] | 24.71 | 0 | 0 | — |
| 1993 | P33 reference | Forest | 90% | 103 | 90.3% [79.4%, 100.0%] | 27.76 | 0 | 0 | — |
| 1993 | Leave-one-year-out | Forest | 90% | 103 | 90.3% [79.4%, 100.0%] | 27.76 | 0 | 0 | — |
| 1993 | Training-only inflation | Forest | 90% | 103 | 93.2% [82.7%, 100.0%] | 30.36 | 0 | 0 | — |
| 1993 | Weather-regime Mondrian | Forest | 90% | 103 | 93.2% [82.4%, 100.0%] | 29.45 | 0 | 0 | — |
| 1993 | Climate-similarity weighting | Forest | 90% | 103 | 94.2% [83.7%, 100.0%] | 33.33 | 0 | 0 | — |
| 1994 | P33 reference | Ridge | 80% | 103 | 100.0% [100.0%, 100.0%] | 21.70 | 0 | 0 | — |
| 1994 | Leave-one-year-out | Ridge | 80% | 103 | 100.0% [100.0%, 100.0%] | 21.70 | 0 | 0 | — |
| 1994 | Training-only inflation | Ridge | 80% | 103 | 100.0% [100.0%, 100.0%] | 26.13 | 0 | 0 | — |
| 1994 | Weather-regime Mondrian | Ridge | 80% | 103 | 100.0% [100.0%, 100.0%] | 21.89 | 0 | 0 | — |
| 1994 | Climate-similarity weighting | Ridge | 80% | 103 | 100.0% [100.0%, 100.0%] | 23.32 | 0 | 0 | — |
| 1994 | P33 reference | Ridge | 90% | 103 | 100.0% [100.0%, 100.0%] | 28.07 | 0 | 0 | — |
| 1994 | Leave-one-year-out | Ridge | 90% | 103 | 100.0% [100.0%, 100.0%] | 28.07 | 0 | 0 | — |
| 1994 | Training-only inflation | Ridge | 90% | 103 | 100.0% [100.0%, 100.0%] | 33.81 | 0 | 0 | — |
| 1994 | Weather-regime Mondrian | Ridge | 90% | 103 | 100.0% [100.0%, 100.0%] | 28.62 | 0 | 0 | — |
| 1994 | Climate-similarity weighting | Ridge | 90% | 103 | 100.0% [100.0%, 100.0%] | 29.53 | 0 | 0 | — |
| 1994 | P33 reference | Forest | 80% | 103 | 91.3% [75.7%, 100.0%] | 21.67 | 0 | 0 | — |
| 1994 | Leave-one-year-out | Forest | 80% | 103 | 91.3% [75.7%, 100.0%] | 21.67 | 0 | 0 | — |
| 1994 | Training-only inflation | Forest | 80% | 103 | 92.2% [78.5%, 100.0%] | 24.55 | 0 | 0 | — |
| 1994 | Weather-regime Mondrian | Forest | 80% | 103 | 90.3% [74.8%, 100.0%] | 22.02 | 0 | 0 | — |
| 1994 | Climate-similarity weighting | Forest | 80% | 103 | 91.3% [75.7%, 100.0%] | 21.64 | 0 | 0 | — |
| 1994 | P33 reference | Forest | 90% | 103 | 94.2% [82.5%, 100.0%] | 27.60 | 0 | 0 | — |
| 1994 | Leave-one-year-out | Forest | 90% | 103 | 94.2% [82.5%, 100.0%] | 27.60 | 0 | 0 | — |
| 1994 | Training-only inflation | Forest | 90% | 103 | 95.1% [85.4%, 100.0%] | 31.27 | 0 | 0 | — |
| 1994 | Weather-regime Mondrian | Forest | 90% | 103 | 94.2% [82.5%, 100.0%] | 28.00 | 0 | 0 | — |
| 1994 | Climate-similarity weighting | Forest | 90% | 103 | 94.2% [82.5%, 100.0%] | 27.13 | 0 | 0 | — |
| 1995 | P33 reference | Ridge | 80% | 103 | 72.8% [52.9%, 89.6%] | 22.37 | 0 | 0 | Yes |
| 1995 | Leave-one-year-out | Ridge | 80% | 103 | 72.8% [52.9%, 89.6%] | 22.37 | 0 | 0 | Yes |
| 1995 | Training-only inflation | Ridge | 80% | 103 | 83.5% [64.0%, 98.0%] | 26.95 | 0 | 0 | — |
| 1995 | Weather-regime Mondrian | Ridge | 80% | 103 | 69.9% [50.5%, 87.3%] | 22.07 | 0 | 0 | Yes |
| 1995 | Climate-similarity weighting | Ridge | 80% | 103 | 56.3% [35.2%, 74.5%] | 19.98 | 0 | 0 | Yes |
| 1995 | P33 reference | Ridge | 90% | 103 | 85.4% [68.5%, 98.0%] | 28.21 | 0 | 0 | Yes |
| 1995 | Leave-one-year-out | Ridge | 90% | 103 | 85.4% [68.5%, 98.0%] | 28.21 | 0 | 0 | Yes |
| 1995 | Training-only inflation | Ridge | 90% | 103 | 92.2% [82.0%, 100.0%] | 33.99 | 0 | 0 | — |
| 1995 | Weather-regime Mondrian | Ridge | 90% | 103 | 85.4% [68.5%, 98.0%] | 27.92 | 0 | 0 | Yes |
| 1995 | Climate-similarity weighting | Ridge | 90% | 103 | 81.6% [62.4%, 96.9%] | 26.06 | 0 | 0 | Yes |
| 1995 | P33 reference | Forest | 80% | 103 | 56.3% [36.1%, 74.7%] | 20.57 | 0 | 0 | Yes |
| 1995 | Leave-one-year-out | Forest | 80% | 103 | 56.3% [36.1%, 74.7%] | 20.57 | 0 | 0 | Yes |
| 1995 | Training-only inflation | Forest | 80% | 103 | 68.9% [47.2%, 88.4%] | 24.28 | 0 | 0 | Yes |
| 1995 | Weather-regime Mondrian | Forest | 80% | 103 | 56.3% [36.1%, 74.7%] | 20.81 | 0 | 0 | Yes |
| 1995 | Climate-similarity weighting | Forest | 80% | 103 | 56.3% [36.1%, 74.7%] | 21.30 | 0 | 0 | Yes |
| 1995 | P33 reference | Forest | 90% | 103 | 77.7% [61.9%, 92.3%] | 26.74 | 0 | 0 | Yes |
| 1995 | Leave-one-year-out | Forest | 90% | 103 | 77.7% [61.9%, 92.3%] | 26.74 | 0 | 0 | Yes |
| 1995 | Training-only inflation | Forest | 90% | 103 | 87.4% [76.2%, 96.3%] | 31.57 | 0 | 0 | Yes |
| 1995 | Weather-regime Mondrian | Forest | 90% | 103 | 78.6% [62.0%, 93.7%] | 28.62 | 0 | 0 | Yes |
| 1995 | Climate-similarity weighting | Forest | 90% | 103 | 78.6% [63.8%, 92.3%] | 27.59 | 0 | 0 | Yes |
| 1996 | P33 reference | Ridge | 80% | 103 | 90.3% [82.3%, 97.8%] | 23.08 | 0 | 0 | — |
| 1996 | Leave-one-year-out | Ridge | 80% | 103 | 90.3% [82.3%, 97.8%] | 23.08 | 0 | 0 | — |
| 1996 | Training-only inflation | Ridge | 80% | 103 | 95.1% [90.5%, 99.1%] | 26.83 | 0 | 0 | — |
| 1996 | Weather-regime Mondrian | Ridge | 80% | 103 | 89.3% [81.4%, 96.8%] | 22.77 | 0 | 0 | — |
| 1996 | Climate-similarity weighting | Ridge | 80% | 103 | 91.3% [83.3%, 98.0%] | 25.07 | 0 | 0 | — |
| 1996 | P33 reference | Ridge | 90% | 103 | 98.1% [94.3%, 100.0%] | 28.96 | 0 | 0 | — |
| 1996 | Leave-one-year-out | Ridge | 90% | 103 | 98.1% [94.3%, 100.0%] | 28.96 | 0 | 0 | — |
| 1996 | Training-only inflation | Ridge | 90% | 103 | 99.0% [97.1%, 100.0%] | 33.67 | 0 | 0 | — |
| 1996 | Weather-regime Mondrian | Ridge | 90% | 103 | 98.1% [94.3%, 100.0%] | 28.71 | 0 | 0 | — |
| 1996 | Climate-similarity weighting | Ridge | 90% | 103 | 99.0% [97.1%, 100.0%] | 31.41 | 0 | 0 | — |
| 1996 | P33 reference | Forest | 80% | 103 | 93.2% [86.4%, 98.1%] | 22.23 | 0 | 0 | — |
| 1996 | Leave-one-year-out | Forest | 80% | 103 | 93.2% [86.4%, 98.1%] | 22.23 | 0 | 0 | — |
| 1996 | Training-only inflation | Forest | 80% | 103 | 95.1% [89.6%, 100.0%] | 24.37 | 0 | 0 | — |
| 1996 | Weather-regime Mondrian | Forest | 80% | 103 | 93.2% [86.4%, 98.1%] | 22.31 | 0 | 0 | — |
| 1996 | Climate-similarity weighting | Forest | 80% | 103 | 92.2% [83.5%, 98.1%] | 21.81 | 0 | 0 | — |
| 1996 | P33 reference | Forest | 90% | 103 | 98.1% [95.5%, 100.0%] | 28.84 | 0 | 0 | — |
| 1996 | Leave-one-year-out | Forest | 90% | 103 | 98.1% [95.5%, 100.0%] | 28.84 | 0 | 0 | — |
| 1996 | Training-only inflation | Forest | 90% | 103 | 99.0% [97.1%, 100.0%] | 31.61 | 0 | 0 | — |
| 1996 | Weather-regime Mondrian | Forest | 90% | 103 | 98.1% [95.5%, 100.0%] | 29.98 | 0 | 0 | — |
| 1996 | Climate-similarity weighting | Forest | 90% | 103 | 96.1% [91.5%, 100.0%] | 27.26 | 0 | 0 | — |
| 1997 | P33 reference | Ridge | 80% | 103 | 84.5% [69.2%, 95.4%] | 22.72 | 0 | 0 | — |
| 1997 | Leave-one-year-out | Ridge | 80% | 103 | 84.5% [69.2%, 95.4%] | 22.72 | 0 | 0 | — |
| 1997 | Training-only inflation | Ridge | 80% | 103 | 90.3% [79.5%, 98.0%] | 26.71 | 0 | 0 | — |
| 1997 | Weather-regime Mondrian | Ridge | 80% | 103 | 84.5% [68.6%, 96.0%] | 21.81 | 0 | 0 | — |
| 1997 | Climate-similarity weighting | Ridge | 80% | 103 | 84.5% [69.2%, 95.4%] | 22.80 | 0 | 0 | — |
| 1997 | P33 reference | Ridge | 90% | 103 | 91.3% [80.2%, 100.0%] | 28.05 | 0 | 0 | — |
| 1997 | Leave-one-year-out | Ridge | 90% | 103 | 91.3% [80.2%, 100.0%] | 28.05 | 0 | 0 | — |
| 1997 | Training-only inflation | Ridge | 90% | 103 | 95.1% [85.4%, 100.0%] | 32.97 | 0 | 0 | — |
| 1997 | Weather-regime Mondrian | Ridge | 90% | 103 | 90.3% [79.5%, 98.0%] | 27.39 | 0 | 0 | — |
| 1997 | Climate-similarity weighting | Ridge | 90% | 103 | 92.2% [81.1%, 100.0%] | 28.75 | 0 | 0 | — |
| 1997 | P33 reference | Forest | 80% | 103 | 62.1% [45.0%, 79.8%] | 22.07 | 0 | 0 | Yes |
| 1997 | Leave-one-year-out | Forest | 80% | 103 | 62.1% [45.0%, 79.8%] | 22.07 | 0 | 0 | Yes |
| 1997 | Training-only inflation | Forest | 80% | 103 | 63.1% [46.1%, 79.8%] | 22.92 | 0 | 0 | Yes |
| 1997 | Weather-regime Mondrian | Forest | 80% | 103 | 63.1% [46.1%, 79.8%] | 22.56 | 0 | 0 | Yes |
| 1997 | Climate-similarity weighting | Forest | 80% | 103 | 63.1% [46.1%, 79.8%] | 22.39 | 0 | 0 | Yes |
| 1997 | P33 reference | Forest | 90% | 103 | 80.6% [61.4%, 94.1%] | 28.85 | 0 | 0 | Yes |
| 1997 | Leave-one-year-out | Forest | 90% | 103 | 80.6% [61.4%, 94.1%] | 28.85 | 0 | 0 | Yes |
| 1997 | Training-only inflation | Forest | 90% | 103 | 81.6% [62.0%, 94.5%] | 29.96 | 0 | 0 | Yes |
| 1997 | Weather-regime Mondrian | Forest | 90% | 103 | 80.6% [60.8%, 94.0%] | 28.84 | 0 | 0 | Yes |
| 1997 | Climate-similarity weighting | Forest | 90% | 103 | 81.6% [62.0%, 94.5%] | 29.11 | 0 | 0 | Yes |
| 1998 | P33 reference | Ridge | 80% | 103 | 79.6% [62.6%, 93.5%] | 22.43 | 0 | 0 | Yes |
| 1998 | Leave-one-year-out | Ridge | 80% | 103 | 79.6% [62.6%, 93.5%] | 22.43 | 0 | 0 | Yes |
| 1998 | Training-only inflation | Ridge | 80% | 103 | 87.4% [76.1%, 97.2%] | 26.12 | 0 | 0 | — |
| 1998 | Weather-regime Mondrian | Ridge | 80% | 103 | 81.6% [65.5%, 94.3%] | 22.57 | 0 | 0 | — |
| 1998 | Climate-similarity weighting | Ridge | 80% | 103 | 79.6% [62.6%, 93.5%] | 22.45 | 0 | 0 | Yes |
| 1998 | P33 reference | Ridge | 90% | 103 | 89.3% [78.7%, 97.4%] | 28.23 | 0 | 0 | Yes |
| 1998 | Leave-one-year-out | Ridge | 90% | 103 | 89.3% [78.7%, 97.4%] | 28.23 | 0 | 0 | Yes |
| 1998 | Training-only inflation | Ridge | 90% | 103 | 94.2% [86.5%, 99.1%] | 32.88 | 0 | 0 | — |
| 1998 | Weather-regime Mondrian | Ridge | 90% | 103 | 91.3% [81.2%, 99.0%] | 28.62 | 0 | 0 | — |
| 1998 | Climate-similarity weighting | Ridge | 90% | 103 | 89.3% [78.7%, 97.4%] | 28.32 | 0 | 0 | Yes |
| 1998 | P33 reference | Forest | 80% | 103 | 75.7% [62.5%, 87.0%] | 21.58 | 0 | 0 | Yes |
| 1998 | Leave-one-year-out | Forest | 80% | 103 | 75.7% [62.5%, 87.0%] | 21.58 | 0 | 0 | Yes |
| 1998 | Training-only inflation | Forest | 80% | 103 | 78.6% [67.5%, 88.5%] | 22.77 | 0 | 0 | Yes |
| 1998 | Weather-regime Mondrian | Forest | 80% | 103 | 73.8% [59.8%, 85.5%] | 21.67 | 0 | 0 | Yes |
| 1998 | Climate-similarity weighting | Forest | 80% | 103 | 75.7% [62.5%, 87.0%] | 21.76 | 0 | 0 | Yes |
| 1998 | P33 reference | Forest | 90% | 103 | 91.3% [81.1%, 98.2%] | 28.04 | 0 | 0 | — |
| 1998 | Leave-one-year-out | Forest | 90% | 103 | 91.3% [81.1%, 98.2%] | 28.04 | 0 | 0 | — |
| 1998 | Training-only inflation | Forest | 90% | 103 | 94.2% [88.3%, 99.0%] | 29.59 | 0 | 0 | — |
| 1998 | Weather-regime Mondrian | Forest | 90% | 103 | 90.3% [80.2%, 97.4%] | 28.23 | 0 | 0 | — |
| 1998 | Climate-similarity weighting | Forest | 90% | 103 | 93.2% [85.2%, 99.0%] | 28.84 | 0 | 0 | — |
| 1999 | P33 reference | Ridge | 80% | 103 | 85.4% [74.3%, 95.4%] | 22.61 | 0 | 0 | — |
| 1999 | Leave-one-year-out | Ridge | 80% | 103 | 85.4% [74.3%, 95.4%] | 22.61 | 0 | 0 | — |
| 1999 | Training-only inflation | Ridge | 80% | 103 | 89.3% [78.7%, 98.0%] | 25.04 | 0 | 0 | — |
| 1999 | Weather-regime Mondrian | Ridge | 80% | 103 | 84.5% [72.6%, 95.1%] | 22.57 | 0 | 0 | — |
| 1999 | Climate-similarity weighting | Ridge | 80% | 103 | 82.5% [69.5%, 94.0%] | 21.68 | 0 | 0 | — |
| 1999 | P33 reference | Ridge | 90% | 103 | 94.2% [84.0%, 100.0%] | 28.67 | 0 | 0 | — |
| 1999 | Leave-one-year-out | Ridge | 90% | 103 | 94.2% [84.0%, 100.0%] | 28.67 | 0 | 0 | — |
| 1999 | Training-only inflation | Ridge | 90% | 103 | 97.1% [92.7%, 100.0%] | 31.74 | 0 | 0 | — |
| 1999 | Weather-regime Mondrian | Ridge | 90% | 103 | 93.2% [82.9%, 100.0%] | 28.66 | 0 | 0 | — |
| 1999 | Climate-similarity weighting | Ridge | 90% | 103 | 93.2% [83.3%, 99.1%] | 27.34 | 0 | 0 | — |
| 1999 | P33 reference | Forest | 80% | 103 | 76.7% [62.6%, 88.9%] | 21.64 | 0 | 0 | Yes |
| 1999 | Leave-one-year-out | Forest | 80% | 103 | 76.7% [62.6%, 88.9%] | 21.64 | 0 | 0 | Yes |
| 1999 | Training-only inflation | Forest | 80% | 103 | 79.6% [67.4%, 90.4%] | 22.96 | 0 | 0 | Yes |
| 1999 | Weather-regime Mondrian | Forest | 80% | 103 | 76.7% [61.7%, 88.9%] | 21.81 | 0 | 0 | Yes |
| 1999 | Climate-similarity weighting | Forest | 80% | 103 | 78.6% [67.0%, 88.9%] | 21.99 | 0 | 0 | Yes |
| 1999 | P33 reference | Forest | 90% | 103 | 91.3% [83.8%, 97.2%] | 28.04 | 0 | 0 | — |
| 1999 | Leave-one-year-out | Forest | 90% | 103 | 91.3% [83.8%, 97.2%] | 28.04 | 0 | 0 | — |
| 1999 | Training-only inflation | Forest | 90% | 103 | 94.2% [86.3%, 100.0%] | 29.75 | 0 | 0 | — |
| 1999 | Weather-regime Mondrian | Forest | 90% | 103 | 91.3% [81.4%, 98.2%] | 28.51 | 0 | 0 | — |
| 1999 | Climate-similarity weighting | Forest | 90% | 103 | 94.2% [86.3%, 100.0%] | 29.55 | 0 | 0 | — |
| 2000 | P33 reference | Ridge | 80% | 103 | 95.1% [89.5%, 100.0%] | 23.26 | 0 | 0 | — |
| 2000 | Leave-one-year-out | Ridge | 80% | 103 | 95.1% [89.5%, 100.0%] | 23.26 | 0 | 0 | — |
| 2000 | Training-only inflation | Ridge | 80% | 103 | 97.1% [93.6%, 100.0%] | 24.72 | 0 | 0 | — |
| 2000 | Weather-regime Mondrian | Ridge | 80% | 103 | 96.1% [91.1%, 100.0%] | 23.75 | 0 | 0 | — |
| 2000 | Climate-similarity weighting | Ridge | 80% | 103 | 96.1% [91.1%, 100.0%] | 23.90 | 0 | 0 | — |
| 2000 | P33 reference | Ridge | 90% | 103 | 99.0% [96.7%, 100.0%] | 29.19 | 0 | 0 | — |
| 2000 | Leave-one-year-out | Ridge | 90% | 103 | 99.0% [96.7%, 100.0%] | 29.19 | 0 | 0 | — |
| 2000 | Training-only inflation | Ridge | 90% | 103 | 100.0% [100.0%, 100.0%] | 31.03 | 0 | 0 | — |
| 2000 | Weather-regime Mondrian | Ridge | 90% | 103 | 100.0% [100.0%, 100.0%] | 30.33 | 0 | 0 | — |
| 2000 | Climate-similarity weighting | Ridge | 90% | 103 | 100.0% [100.0%, 100.0%] | 29.75 | 0 | 0 | — |
| 2000 | P33 reference | Forest | 80% | 103 | 98.1% [95.3%, 100.0%] | 22.42 | 0 | 0 | — |
| 2000 | Leave-one-year-out | Forest | 80% | 103 | 98.1% [95.3%, 100.0%] | 22.42 | 0 | 0 | — |
| 2000 | Training-only inflation | Forest | 80% | 103 | 98.1% [95.3%, 100.0%] | 22.42 | 0 | 0 | — |
| 2000 | Weather-regime Mondrian | Forest | 80% | 103 | 98.1% [95.3%, 100.0%] | 21.66 | 0 | 0 | — |
| 2000 | Climate-similarity weighting | Forest | 80% | 103 | 98.1% [95.3%, 100.0%] | 21.16 | 0 | 0 | — |
| 2000 | P33 reference | Forest | 90% | 103 | 100.0% [100.0%, 100.0%] | 29.36 | 0 | 0 | — |
| 2000 | Leave-one-year-out | Forest | 90% | 103 | 100.0% [100.0%, 100.0%] | 29.36 | 0 | 0 | — |
| 2000 | Training-only inflation | Forest | 90% | 103 | 100.0% [100.0%, 100.0%] | 29.36 | 0 | 0 | — |
| 2000 | Weather-regime Mondrian | Forest | 90% | 103 | 100.0% [100.0%, 100.0%] | 28.03 | 0 | 0 | — |
| 2000 | Climate-similarity weighting | Forest | 90% | 103 | 100.0% [100.0%, 100.0%] | 27.67 | 0 | 0 | — |
| 2001 | P33 reference | Ridge | 80% | 103 | 92.2% [85.7%, 98.0%] | 23.06 | 0 | 0 | — |
| 2001 | Leave-one-year-out | Ridge | 80% | 103 | 92.2% [85.7%, 98.0%] | 23.06 | 0 | 0 | — |
| 2001 | Training-only inflation | Ridge | 80% | 103 | 92.2% [85.7%, 98.0%] | 24.57 | 0 | 0 | — |
| 2001 | Weather-regime Mondrian | Ridge | 80% | 103 | 91.3% [84.2%, 98.0%] | 23.45 | 0 | 0 | — |
| 2001 | Climate-similarity weighting | Ridge | 80% | 103 | 92.2% [85.7%, 98.0%] | 22.50 | 0 | 0 | — |
| 2001 | P33 reference | Ridge | 90% | 103 | 97.1% [93.0%, 100.0%] | 29.18 | 0 | 0 | — |
| 2001 | Leave-one-year-out | Ridge | 90% | 103 | 97.1% [93.0%, 100.0%] | 29.18 | 0 | 0 | — |
| 2001 | Training-only inflation | Ridge | 90% | 103 | 98.1% [95.4%, 100.0%] | 31.09 | 0 | 0 | — |
| 2001 | Weather-regime Mondrian | Ridge | 90% | 103 | 96.1% [90.2%, 100.0%] | 29.19 | 0 | 0 | — |
| 2001 | Climate-similarity weighting | Ridge | 90% | 103 | 97.1% [93.0%, 100.0%] | 29.11 | 0 | 0 | — |
| 2001 | P33 reference | Forest | 80% | 103 | 81.6% [67.6%, 95.5%] | 22.39 | 0 | 0 | — |
| 2001 | Leave-one-year-out | Forest | 80% | 103 | 81.6% [67.6%, 95.5%] | 22.39 | 0 | 0 | — |
| 2001 | Training-only inflation | Forest | 80% | 103 | 81.6% [67.6%, 95.5%] | 22.39 | 0 | 0 | — |
| 2001 | Weather-regime Mondrian | Forest | 80% | 103 | 75.7% [60.0%, 91.8%] | 21.74 | 0 | 0 | Yes |
| 2001 | Climate-similarity weighting | Forest | 80% | 103 | 82.5% [68.4%, 97.7%] | 23.19 | 0 | 0 | — |
| 2001 | P33 reference | Forest | 90% | 103 | 86.4% [73.6%, 100.0%] | 28.26 | 0 | 0 | Yes |
| 2001 | Leave-one-year-out | Forest | 90% | 103 | 86.4% [73.6%, 100.0%] | 28.26 | 0 | 0 | Yes |
| 2001 | Training-only inflation | Forest | 90% | 103 | 86.4% [73.6%, 100.0%] | 28.26 | 0 | 0 | Yes |
| 2001 | Weather-regime Mondrian | Forest | 90% | 103 | 87.4% [75.9%, 100.0%] | 27.78 | 0 | 0 | Yes |
| 2001 | Climate-similarity weighting | Forest | 90% | 103 | 87.4% [75.2%, 100.0%] | 29.06 | 0 | 0 | Yes |
| 2002 | P33 reference | Ridge | 80% | 103 | 82.5% [69.5%, 93.5%] | 22.71 | 0 | 0 | — |
| 2002 | Leave-one-year-out | Ridge | 80% | 103 | 82.5% [69.5%, 93.5%] | 22.71 | 0 | 0 | — |
| 2002 | Training-only inflation | Ridge | 80% | 103 | 82.5% [69.5%, 93.5%] | 22.71 | 0 | 0 | — |
| 2002 | Weather-regime Mondrian | Ridge | 80% | 103 | 81.6% [66.7%, 93.5%] | 23.69 | 0 | 0 | — |
| 2002 | Climate-similarity weighting | Ridge | 80% | 103 | 84.5% [72.6%, 94.6%] | 23.93 | 0 | 0 | — |
| 2002 | P33 reference | Ridge | 90% | 103 | 90.3% [82.6%, 96.7%] | 28.69 | 0 | 0 | — |
| 2002 | Leave-one-year-out | Ridge | 90% | 103 | 90.3% [82.6%, 96.7%] | 28.69 | 0 | 0 | — |
| 2002 | Training-only inflation | Ridge | 90% | 103 | 90.3% [82.6%, 96.7%] | 28.69 | 0 | 0 | — |
| 2002 | Weather-regime Mondrian | Ridge | 90% | 103 | 91.3% [83.3%, 98.1%] | 29.95 | 0 | 0 | — |
| 2002 | Climate-similarity weighting | Ridge | 90% | 103 | 92.2% [84.8%, 98.2%] | 30.14 | 0 | 0 | — |
| 2002 | P33 reference | Forest | 80% | 103 | 92.2% [85.9%, 97.1%] | 22.79 | 0 | 0 | — |
| 2002 | Leave-one-year-out | Forest | 80% | 103 | 92.2% [85.9%, 97.1%] | 22.79 | 0 | 0 | — |
| 2002 | Training-only inflation | Forest | 80% | 103 | 92.2% [85.9%, 97.1%] | 22.79 | 0 | 0 | — |
| 2002 | Weather-regime Mondrian | Forest | 80% | 103 | 92.2% [85.9%, 97.1%] | 22.25 | 0 | 0 | — |
| 2002 | Climate-similarity weighting | Forest | 80% | 103 | 91.3% [85.1%, 95.8%] | 22.16 | 0 | 0 | — |
| 2002 | P33 reference | Forest | 90% | 103 | 99.0% [96.8%, 100.0%] | 29.39 | 0 | 0 | — |
| 2002 | Leave-one-year-out | Forest | 90% | 103 | 99.0% [96.8%, 100.0%] | 29.39 | 0 | 0 | — |
| 2002 | Training-only inflation | Forest | 90% | 103 | 99.0% [96.8%, 100.0%] | 29.39 | 0 | 0 | — |
| 2002 | Weather-regime Mondrian | Forest | 90% | 103 | 99.0% [97.1%, 100.0%] | 29.15 | 0 | 0 | — |
| 2002 | Climate-similarity weighting | Forest | 90% | 103 | 98.1% [95.5%, 100.0%] | 28.24 | 0 | 0 | — |
| 2003 | P33 reference | Ridge | 80% | 103 | 53.4% [31.9%, 76.3%] | 22.20 | 0 | 0 | Yes |
| 2003 | Leave-one-year-out | Ridge | 80% | 103 | 53.4% [31.9%, 76.3%] | 22.20 | 0 | 0 | Yes |
| 2003 | Training-only inflation | Ridge | 80% | 103 | 53.4% [31.9%, 76.3%] | 22.22 | 0 | 0 | Yes |
| 2003 | Weather-regime Mondrian | Ridge | 80% | 103 | 55.3% [35.2%, 76.6%] | 23.49 | 0 | 0 | Yes |
| 2003 | Climate-similarity weighting | Ridge | 80% | 103 | 51.5% [27.7%, 75.8%] | 21.49 | 0 | 0 | Yes |
| 2003 | P33 reference | Ridge | 90% | 103 | 64.1% [43.8%, 83.1%] | 28.26 | 0 | 0 | Yes |
| 2003 | Leave-one-year-out | Ridge | 90% | 103 | 64.1% [43.8%, 83.1%] | 28.26 | 0 | 0 | Yes |
| 2003 | Training-only inflation | Ridge | 90% | 103 | 64.1% [43.8%, 83.1%] | 28.29 | 0 | 0 | Yes |
| 2003 | Weather-regime Mondrian | Ridge | 90% | 103 | 74.8% [56.8%, 90.4%] | 30.10 | 0 | 0 | Yes |
| 2003 | Climate-similarity weighting | Ridge | 90% | 103 | 63.1% [42.6%, 82.7%] | 27.92 | 0 | 0 | Yes |
| 2003 | P33 reference | Forest | 80% | 103 | 51.5% [29.9%, 75.7%] | 23.06 | 0 | 0 | Yes |
| 2003 | Leave-one-year-out | Forest | 80% | 103 | 51.5% [29.9%, 75.7%] | 23.06 | 0 | 0 | Yes |
| 2003 | Training-only inflation | Forest | 80% | 103 | 53.4% [32.3%, 76.8%] | 24.78 | 0 | 0 | Yes |
| 2003 | Weather-regime Mondrian | Forest | 80% | 103 | 49.5% [27.5%, 74.5%] | 21.44 | 0 | 0 | Yes |
| 2003 | Climate-similarity weighting | Forest | 80% | 103 | 53.4% [32.3%, 76.8%] | 23.66 | 0 | 0 | Yes |
| 2003 | P33 reference | Forest | 90% | 103 | 59.2% [38.3%, 81.3%] | 28.94 | 0 | 0 | Yes |
| 2003 | Leave-one-year-out | Forest | 90% | 103 | 59.2% [38.3%, 81.3%] | 28.94 | 0 | 0 | Yes |
| 2003 | Training-only inflation | Forest | 90% | 103 | 64.1% [43.3%, 84.8%] | 31.10 | 0 | 0 | Yes |
| 2003 | Weather-regime Mondrian | Forest | 90% | 103 | 55.3% [35.0%, 78.1%] | 27.09 | 0 | 0 | Yes |
| 2003 | Climate-similarity weighting | Forest | 90% | 103 | 61.2% [40.4%, 83.0%] | 30.00 | 0 | 0 | Yes |
| 2004 | P33 reference | Ridge | 80% | 103 | 89.3% [76.1%, 97.5%] | 22.59 | 0 | 0 | — |
| 2004 | Leave-one-year-out | Ridge | 80% | 103 | 89.3% [76.1%, 97.5%] | 22.59 | 0 | 0 | — |
| 2004 | Training-only inflation | Ridge | 80% | 103 | 89.3% [76.1%, 97.5%] | 22.59 | 0 | 0 | — |
| 2004 | Weather-regime Mondrian | Ridge | 80% | 103 | 90.3% [77.0%, 98.4%] | 23.00 | 0 | 0 | — |
| 2004 | Climate-similarity weighting | Ridge | 80% | 103 | 90.3% [77.0%, 98.4%] | 23.09 | 0 | 0 | — |
| 2004 | P33 reference | Ridge | 90% | 103 | 93.2% [79.6%, 100.0%] | 28.66 | 0 | 0 | — |
| 2004 | Leave-one-year-out | Ridge | 90% | 103 | 93.2% [79.6%, 100.0%] | 28.66 | 0 | 0 | — |
| 2004 | Training-only inflation | Ridge | 90% | 103 | 93.2% [79.6%, 100.0%] | 28.66 | 0 | 0 | — |
| 2004 | Weather-regime Mondrian | Ridge | 90% | 103 | 94.2% [83.0%, 100.0%] | 28.41 | 0 | 0 | — |
| 2004 | Climate-similarity weighting | Ridge | 90% | 103 | 93.2% [79.6%, 100.0%] | 28.96 | 0 | 0 | — |
| 2004 | P33 reference | Forest | 80% | 103 | 86.4% [69.1%, 98.2%] | 23.32 | 0 | 0 | — |
| 2004 | Leave-one-year-out | Forest | 80% | 103 | 86.4% [69.1%, 98.2%] | 23.32 | 0 | 0 | — |
| 2004 | Training-only inflation | Forest | 80% | 103 | 86.4% [69.1%, 98.2%] | 23.32 | 0 | 0 | — |
| 2004 | Weather-regime Mondrian | Forest | 80% | 103 | 87.4% [69.4%, 98.4%] | 23.76 | 0 | 0 | — |
| 2004 | Climate-similarity weighting | Forest | 80% | 103 | 85.4% [65.9%, 98.2%] | 22.22 | 0 | 0 | — |
| 2004 | P33 reference | Forest | 90% | 103 | 95.1% [84.9%, 100.0%] | 29.48 | 0 | 0 | — |
| 2004 | Leave-one-year-out | Forest | 90% | 103 | 95.1% [84.9%, 100.0%] | 29.48 | 0 | 0 | — |
| 2004 | Training-only inflation | Forest | 90% | 103 | 95.1% [84.9%, 100.0%] | 29.48 | 0 | 0 | — |
| 2004 | Weather-regime Mondrian | Forest | 90% | 103 | 94.2% [84.2%, 100.0%] | 30.19 | 0 | 0 | — |
| 2004 | Climate-similarity weighting | Forest | 90% | 103 | 93.2% [82.6%, 100.0%] | 28.03 | 0 | 0 | — |
| 2005 | P33 reference | Ridge | 80% | 103 | 91.3% [83.2%, 100.0%] | 22.65 | 0 | 0 | — |
| 2005 | Leave-one-year-out | Ridge | 80% | 103 | 91.3% [83.2%, 100.0%] | 22.65 | 0 | 0 | — |
| 2005 | Training-only inflation | Ridge | 80% | 103 | 93.2% [86.4%, 100.0%] | 24.47 | 0 | 0 | — |
| 2005 | Weather-regime Mondrian | Ridge | 80% | 103 | 90.3% [82.1%, 98.9%] | 22.70 | 0 | 0 | — |
| 2005 | Climate-similarity weighting | Ridge | 80% | 103 | 91.3% [83.2%, 100.0%] | 23.07 | 0 | 0 | — |
| 2005 | P33 reference | Ridge | 90% | 103 | 97.1% [94.2%, 100.0%] | 28.82 | 0 | 0 | — |
| 2005 | Leave-one-year-out | Ridge | 90% | 103 | 97.1% [94.2%, 100.0%] | 28.82 | 0 | 0 | — |
| 2005 | Training-only inflation | Ridge | 90% | 103 | 97.1% [94.2%, 100.0%] | 31.12 | 0 | 0 | — |
| 2005 | Weather-regime Mondrian | Ridge | 90% | 103 | 95.1% [90.5%, 100.0%] | 28.16 | 0 | 0 | — |
| 2005 | Climate-similarity weighting | Ridge | 90% | 103 | 97.1% [94.2%, 100.0%] | 29.01 | 0 | 0 | — |
| 2005 | P33 reference | Forest | 80% | 103 | 92.2% [86.0%, 97.3%] | 23.67 | 0 | 0 | — |
| 2005 | Leave-one-year-out | Forest | 80% | 103 | 92.2% [86.0%, 97.3%] | 23.67 | 0 | 0 | — |
| 2005 | Training-only inflation | Forest | 80% | 103 | 92.2% [86.0%, 97.3%] | 23.67 | 0 | 0 | — |
| 2005 | Weather-regime Mondrian | Forest | 80% | 103 | 89.3% [83.0%, 95.3%] | 23.62 | 0 | 0 | — |
| 2005 | Climate-similarity weighting | Forest | 80% | 103 | 92.2% [86.0%, 97.3%] | 25.51 | 0 | 0 | — |
| 2005 | P33 reference | Forest | 90% | 103 | 97.1% [93.6%, 100.0%] | 29.86 | 0 | 0 | — |
| 2005 | Leave-one-year-out | Forest | 90% | 103 | 97.1% [93.6%, 100.0%] | 29.86 | 0 | 0 | — |
| 2005 | Training-only inflation | Forest | 90% | 103 | 97.1% [93.6%, 100.0%] | 29.86 | 0 | 0 | — |
| 2005 | Weather-regime Mondrian | Forest | 90% | 103 | 97.1% [93.7%, 100.0%] | 29.61 | 0 | 0 | — |
| 2005 | Climate-similarity weighting | Forest | 90% | 103 | 98.1% [94.7%, 100.0%] | 32.00 | 0 | 0 | — |
| 2006 | P33 reference | Ridge | 80% | 103 | 81.6% [62.9%, 95.2%] | 23.17 | 0 | 0 | — |
| 2006 | Leave-one-year-out | Ridge | 80% | 103 | 81.6% [62.9%, 95.2%] | 23.17 | 0 | 0 | — |
| 2006 | Training-only inflation | Ridge | 80% | 103 | 84.5% [68.6%, 95.9%] | 25.34 | 0 | 0 | — |
| 2006 | Weather-regime Mondrian | Ridge | 80% | 103 | 78.6% [61.3%, 92.2%] | 23.43 | 0 | 0 | Yes |
| 2006 | Climate-similarity weighting | Ridge | 80% | 103 | 76.7% [57.7%, 91.8%] | 20.66 | 0 | 0 | Yes |
| 2006 | P33 reference | Ridge | 90% | 103 | 87.4% [73.2%, 96.6%] | 29.02 | 0 | 0 | Yes |
| 2006 | Leave-one-year-out | Ridge | 90% | 103 | 87.4% [73.2%, 96.6%] | 29.02 | 0 | 0 | Yes |
| 2006 | Training-only inflation | Ridge | 90% | 103 | 93.2% [82.6%, 100.0%] | 31.74 | 0 | 0 | — |
| 2006 | Weather-regime Mondrian | Ridge | 90% | 103 | 88.3% [77.4%, 96.4%] | 29.52 | 0 | 0 | Yes |
| 2006 | Climate-similarity weighting | Ridge | 90% | 103 | 85.4% [69.9%, 96.3%] | 27.28 | 0 | 0 | Yes |
| 2006 | P33 reference | Forest | 80% | 103 | 83.5% [65.6%, 94.8%] | 23.62 | 0 | 0 | — |
| 2006 | Leave-one-year-out | Forest | 80% | 103 | 83.5% [65.6%, 94.8%] | 23.62 | 0 | 0 | — |
| 2006 | Training-only inflation | Forest | 80% | 103 | 83.5% [65.6%, 94.8%] | 23.62 | 0 | 0 | — |
| 2006 | Weather-regime Mondrian | Forest | 80% | 103 | 82.5% [64.9%, 93.8%] | 22.43 | 0 | 0 | — |
| 2006 | Climate-similarity weighting | Forest | 80% | 103 | 78.6% [60.8%, 90.8%] | 20.37 | 0 | 0 | Yes |
| 2006 | P33 reference | Forest | 90% | 103 | 92.2% [80.9%, 100.0%] | 29.98 | 0 | 0 | — |
| 2006 | Leave-one-year-out | Forest | 90% | 103 | 92.2% [80.9%, 100.0%] | 29.98 | 0 | 0 | — |
| 2006 | Training-only inflation | Forest | 90% | 103 | 92.2% [80.9%, 100.0%] | 29.98 | 0 | 0 | — |
| 2006 | Weather-regime Mondrian | Forest | 90% | 103 | 88.3% [77.6%, 96.3%] | 27.49 | 0 | 0 | Yes |
| 2006 | Climate-similarity weighting | Forest | 90% | 103 | 84.5% [66.0%, 96.1%] | 24.90 | 0 | 0 | Yes |
| 2007 | P33 reference | Ridge | 80% | 103 | 38.8% [15.1%, 68.5%] | 22.61 | 0 | 0 | Yes |
| 2007 | Leave-one-year-out | Ridge | 80% | 103 | 38.8% [15.1%, 68.5%] | 22.61 | 0 | 0 | Yes |
| 2007 | Training-only inflation | Ridge | 80% | 103 | 38.8% [15.1%, 68.5%] | 23.77 | 0 | 0 | Yes |
| 2007 | Weather-regime Mondrian | Ridge | 80% | 103 | 38.8% [14.7%, 68.3%] | 22.55 | 0 | 0 | Yes |
| 2007 | Climate-similarity weighting | Ridge | 80% | 103 | 38.8% [15.1%, 68.5%] | 23.77 | 0 | 0 | Yes |
| 2007 | P33 reference | Ridge | 90% | 103 | 46.6% [21.9%, 76.0%] | 28.32 | 0 | 0 | Yes |
| 2007 | Leave-one-year-out | Ridge | 90% | 103 | 46.6% [21.9%, 76.0%] | 28.32 | 0 | 0 | Yes |
| 2007 | Training-only inflation | Ridge | 90% | 103 | 49.5% [25.7%, 77.5%] | 29.76 | 0 | 0 | Yes |
| 2007 | Weather-regime Mondrian | Ridge | 90% | 103 | 43.7% [19.5%, 74.0%] | 27.86 | 0 | 0 | Yes |
| 2007 | Climate-similarity weighting | Ridge | 90% | 103 | 49.5% [25.7%, 77.5%] | 29.64 | 0 | 0 | Yes |
| 2007 | P33 reference | Forest | 80% | 103 | 31.1% [7.8%, 60.0%] | 23.25 | 0 | 0 | Yes |
| 2007 | Leave-one-year-out | Forest | 80% | 103 | 31.1% [7.8%, 60.0%] | 23.25 | 0 | 0 | Yes |
| 2007 | Training-only inflation | Forest | 80% | 103 | 34.0% [10.9%, 63.6%] | 25.50 | 0 | 0 | Yes |
| 2007 | Weather-regime Mondrian | Forest | 80% | 103 | 33.0% [9.2%, 62.8%] | 24.41 | 0 | 0 | Yes |
| 2007 | Climate-similarity weighting | Forest | 80% | 103 | 33.0% [9.2%, 62.8%] | 25.27 | 0 | 0 | Yes |
| 2007 | P33 reference | Forest | 90% | 103 | 37.9% [15.3%, 66.4%] | 28.75 | 0 | 0 | Yes |
| 2007 | Leave-one-year-out | Forest | 90% | 103 | 37.9% [15.3%, 66.4%] | 28.75 | 0 | 0 | Yes |
| 2007 | Training-only inflation | Forest | 90% | 103 | 44.7% [23.2%, 71.8%] | 31.54 | 0 | 0 | Yes |
| 2007 | Weather-regime Mondrian | Forest | 90% | 103 | 41.7% [18.3%, 70.7%] | 30.12 | 0 | 0 | Yes |
| 2007 | Climate-similarity weighting | Forest | 90% | 103 | 42.7% [20.0%, 70.8%] | 30.72 | 0 | 0 | Yes |
| 2008 | P33 reference | Ridge | 80% | 93 | 76.3% [52.2%, 94.2%] | 22.41 | 0 | 0 | Yes |
| 2008 | Leave-one-year-out | Ridge | 80% | 93 | 76.3% [52.2%, 94.2%] | 22.41 | 0 | 0 | Yes |
| 2008 | Training-only inflation | Ridge | 80% | 93 | 76.3% [52.2%, 94.2%] | 22.41 | 0 | 0 | Yes |
| 2008 | Weather-regime Mondrian | Ridge | 80% | 93 | 76.3% [52.4%, 94.8%] | 22.34 | 0 | 0 | Yes |
| 2008 | Climate-similarity weighting | Ridge | 80% | 93 | 77.4% [52.2%, 95.6%] | 23.11 | 0 | 0 | Yes |
| 2008 | P33 reference | Ridge | 90% | 93 | 83.9% [62.4%, 100.0%] | 29.08 | 0 | 0 | Yes |
| 2008 | Leave-one-year-out | Ridge | 90% | 93 | 83.9% [62.4%, 100.0%] | 29.08 | 0 | 0 | Yes |
| 2008 | Training-only inflation | Ridge | 90% | 93 | 83.9% [62.4%, 100.0%] | 29.08 | 0 | 0 | Yes |
| 2008 | Weather-regime Mondrian | Ridge | 90% | 93 | 80.6% [56.2%, 98.8%] | 27.82 | 0 | 0 | Yes |
| 2008 | Climate-similarity weighting | Ridge | 90% | 93 | 84.9% [65.6%, 100.0%] | 30.01 | 0 | 0 | Yes |
| 2008 | P33 reference | Forest | 80% | 93 | 82.8% [69.7%, 94.8%] | 20.24 | 0 | 0 | — |
| 2008 | Leave-one-year-out | Forest | 80% | 93 | 82.8% [69.7%, 94.8%] | 20.24 | 0 | 0 | — |
| 2008 | Training-only inflation | Forest | 80% | 93 | 87.1% [74.4%, 97.9%] | 22.06 | 0 | 0 | — |
| 2008 | Weather-regime Mondrian | Forest | 80% | 93 | 82.8% [69.7%, 94.8%] | 20.25 | 0 | 0 | — |
| 2008 | Climate-similarity weighting | Forest | 80% | 93 | 87.1% [74.4%, 97.9%] | 21.96 | 0 | 0 | — |
| 2008 | P33 reference | Forest | 90% | 93 | 94.6% [89.5%, 100.0%] | 26.15 | 0 | 0 | — |
| 2008 | Leave-one-year-out | Forest | 90% | 93 | 94.6% [89.5%, 100.0%] | 26.15 | 0 | 0 | — |
| 2008 | Training-only inflation | Forest | 90% | 93 | 95.7% [91.2%, 100.0%] | 28.50 | 0 | 0 | — |
| 2008 | Weather-regime Mondrian | Forest | 90% | 93 | 94.6% [89.5%, 100.0%] | 26.07 | 0 | 0 | — |
| 2008 | Climate-similarity weighting | Forest | 90% | 93 | 94.6% [89.5%, 100.0%] | 28.10 | 0 | 0 | — |
| 2009 | P33 reference | Ridge | 80% | 103 | 88.3% [73.0%, 99.0%] | 24.70 | 0 | 0 | — |
| 2009 | Leave-one-year-out | Ridge | 80% | 103 | 88.3% [73.0%, 99.0%] | 24.70 | 0 | 0 | — |
| 2009 | Training-only inflation | Ridge | 80% | 103 | 92.2% [80.9%, 100.0%] | 28.53 | 0 | 0 | — |
| 2009 | Weather-regime Mondrian | Ridge | 80% | 103 | 91.3% [79.4%, 99.0%] | 26.85 | 0 | 0 | — |
| 2009 | Climate-similarity weighting | Ridge | 80% | 103 | 92.2% [80.9%, 100.0%] | 27.89 | 0 | 0 | — |
| 2009 | P33 reference | Ridge | 90% | 103 | 95.1% [85.4%, 100.0%] | 34.01 | 0 | 0 | — |
| 2009 | Leave-one-year-out | Ridge | 90% | 103 | 95.1% [85.4%, 100.0%] | 34.01 | 0 | 0 | — |
| 2009 | Training-only inflation | Ridge | 90% | 103 | 98.1% [94.2%, 100.0%] | 39.28 | 0 | 0 | — |
| 2009 | Weather-regime Mondrian | Ridge | 90% | 103 | 99.0% [97.1%, 100.0%] | 38.13 | 0 | 0 | — |
| 2009 | Climate-similarity weighting | Ridge | 90% | 103 | 98.1% [94.2%, 100.0%] | 38.34 | 0 | 0 | — |
| 2009 | P33 reference | Forest | 80% | 103 | 84.5% [67.9%, 98.0%] | 25.78 | 0 | 0 | — |
| 2009 | Leave-one-year-out | Forest | 80% | 103 | 84.5% [67.9%, 98.0%] | 25.78 | 0 | 0 | — |
| 2009 | Training-only inflation | Forest | 80% | 103 | 95.1% [87.7%, 100.0%] | 33.01 | 0 | 0 | — |
| 2009 | Weather-regime Mondrian | Forest | 80% | 103 | 89.3% [77.9%, 100.0%] | 28.86 | 0 | 0 | — |
| 2009 | Climate-similarity weighting | Forest | 80% | 103 | 88.3% [72.0%, 99.0%] | 29.21 | 0 | 0 | — |
| 2009 | P33 reference | Forest | 90% | 103 | 95.1% [87.7%, 100.0%] | 33.70 | 0 | 0 | — |
| 2009 | Leave-one-year-out | Forest | 90% | 103 | 95.1% [87.7%, 100.0%] | 33.70 | 0 | 0 | — |
| 2009 | Training-only inflation | Forest | 90% | 103 | 98.1% [94.2%, 100.0%] | 43.16 | 0 | 0 | — |
| 2009 | Weather-regime Mondrian | Forest | 90% | 103 | 97.1% [93.1%, 100.0%] | 37.87 | 0 | 0 | — |
| 2009 | Climate-similarity weighting | Forest | 90% | 103 | 98.1% [94.2%, 100.0%] | 39.28 | 0 | 0 | — |
| 2010 | P33 reference | Ridge | 80% | 97 | 81.4% [63.2%, 96.6%] | 23.24 | 0 | 0 | — |
| 2010 | Leave-one-year-out | Ridge | 80% | 97 | 81.4% [63.2%, 96.6%] | 23.24 | 0 | 0 | — |
| 2010 | Training-only inflation | Ridge | 80% | 97 | 82.5% [64.1%, 97.9%] | 24.93 | 0 | 0 | — |
| 2010 | Weather-regime Mondrian | Ridge | 80% | 97 | 77.3% [59.6%, 92.7%] | 23.34 | 0 | 0 | Yes |
| 2010 | Climate-similarity weighting | Ridge | 80% | 97 | 79.4% [62.0%, 93.3%] | 22.82 | 0 | 0 | Yes |
| 2010 | P33 reference | Ridge | 90% | 97 | 90.7% [77.8%, 100.0%] | 29.98 | 0 | 0 | — |
| 2010 | Leave-one-year-out | Ridge | 90% | 97 | 90.7% [77.8%, 100.0%] | 29.98 | 0 | 0 | — |
| 2010 | Training-only inflation | Ridge | 90% | 97 | 91.8% [81.1%, 100.0%] | 32.16 | 0 | 0 | — |
| 2010 | Weather-regime Mondrian | Ridge | 90% | 97 | 92.8% [85.2%, 99.0%] | 30.43 | 0 | 0 | — |
| 2010 | Climate-similarity weighting | Ridge | 90% | 97 | 90.7% [77.8%, 100.0%] | 29.77 | 0 | 0 | — |
| 2010 | P33 reference | Forest | 80% | 97 | 86.6% [74.5%, 97.8%] | 21.38 | 0 | 0 | — |
| 2010 | Leave-one-year-out | Forest | 80% | 97 | 86.6% [74.5%, 97.8%] | 21.38 | 0 | 0 | — |
| 2010 | Training-only inflation | Forest | 80% | 97 | 89.7% [80.4%, 97.9%] | 24.89 | 0 | 0 | — |
| 2010 | Weather-regime Mondrian | Forest | 80% | 97 | 84.5% [70.5%, 96.8%] | 21.45 | 0 | 0 | — |
| 2010 | Climate-similarity weighting | Forest | 80% | 97 | 86.6% [74.5%, 97.8%] | 21.54 | 0 | 0 | — |
| 2010 | P33 reference | Forest | 90% | 97 | 91.8% [82.9%, 100.0%] | 27.21 | 0 | 0 | — |
| 2010 | Leave-one-year-out | Forest | 90% | 97 | 91.8% [82.9%, 100.0%] | 27.21 | 0 | 0 | — |
| 2010 | Training-only inflation | Forest | 90% | 97 | 96.9% [92.5%, 100.0%] | 31.66 | 0 | 0 | — |
| 2010 | Weather-regime Mondrian | Forest | 90% | 97 | 93.8% [86.7%, 100.0%] | 27.54 | 0 | 0 | — |
| 2010 | Climate-similarity weighting | Forest | 90% | 97 | 91.8% [82.9%, 100.0%] | 27.69 | 0 | 0 | — |
| 2011 | P33 reference | Ridge | 80% | 102 | 93.1% [85.0%, 99.1%] | 25.99 | 0 | 0 | — |
| 2011 | Leave-one-year-out | Ridge | 80% | 102 | 93.1% [85.0%, 99.1%] | 25.99 | 0 | 0 | — |
| 2011 | Training-only inflation | Ridge | 80% | 102 | 99.0% [97.1%, 100.0%] | 33.29 | 0 | 0 | — |
| 2011 | Weather-regime Mondrian | Ridge | 80% | 102 | 95.1% [90.7%, 98.9%] | 26.52 | 0 | 0 | — |
| 2011 | Climate-similarity weighting | Ridge | 80% | 102 | 95.1% [89.8%, 99.1%] | 27.73 | 0 | 0 | — |
| 2011 | P33 reference | Ridge | 90% | 102 | 98.0% [95.3%, 100.0%] | 31.72 | 0 | 0 | — |
| 2011 | Leave-one-year-out | Ridge | 90% | 102 | 98.0% [95.3%, 100.0%] | 31.72 | 0 | 0 | — |
| 2011 | Training-only inflation | Ridge | 90% | 102 | 99.0% [97.1%, 100.0%] | 40.63 | 0 | 0 | — |
| 2011 | Weather-regime Mondrian | Ridge | 90% | 102 | 97.1% [94.2%, 99.1%] | 33.03 | 0 | 0 | — |
| 2011 | Climate-similarity weighting | Ridge | 90% | 102 | 99.0% [97.1%, 100.0%] | 33.96 | 0 | 0 | — |
| 2011 | P33 reference | Forest | 80% | 102 | 91.2% [85.7%, 96.8%] | 23.07 | 0 | 0 | — |
| 2011 | Leave-one-year-out | Forest | 80% | 102 | 91.2% [85.7%, 96.8%] | 23.07 | 0 | 0 | — |
| 2011 | Training-only inflation | Forest | 80% | 102 | 96.1% [93.0%, 99.0%] | 28.00 | 0 | 0 | — |
| 2011 | Weather-regime Mondrian | Forest | 80% | 102 | 92.2% [86.6%, 97.0%] | 24.06 | 0 | 0 | — |
| 2011 | Climate-similarity weighting | Forest | 80% | 102 | 93.1% [89.1%, 97.1%] | 24.10 | 0 | 0 | — |
| 2011 | P33 reference | Forest | 90% | 102 | 96.1% [93.0%, 99.0%] | 28.92 | 0 | 0 | — |
| 2011 | Leave-one-year-out | Forest | 90% | 102 | 96.1% [93.0%, 99.0%] | 28.92 | 0 | 0 | — |
| 2011 | Training-only inflation | Forest | 90% | 102 | 100.0% [100.0%, 100.0%] | 35.10 | 0 | 0 | — |
| 2011 | Weather-regime Mondrian | Forest | 90% | 102 | 98.0% [95.1%, 100.0%] | 31.19 | 0 | 0 | — |
| 2011 | Climate-similarity weighting | Forest | 90% | 102 | 97.1% [94.0%, 100.0%] | 31.32 | 0 | 0 | — |
| 2012 | P33 reference | Ridge | 80% | 96 | 86.5% [75.2%, 94.7%] | 23.35 | 0 | 0 | — |
| 2012 | Leave-one-year-out | Ridge | 80% | 96 | 86.5% [75.2%, 94.7%] | 23.35 | 0 | 0 | — |
| 2012 | Training-only inflation | Ridge | 80% | 96 | 92.7% [84.7%, 98.9%] | 29.46 | 0 | 0 | — |
| 2012 | Weather-regime Mondrian | Ridge | 80% | 96 | 90.6% [80.4%, 98.8%] | 26.73 | 0 | 0 | — |
| 2012 | Climate-similarity weighting | Ridge | 80% | 96 | 88.5% [76.2%, 96.9%] | 25.93 | 0 | 0 | — |
| 2012 | P33 reference | Ridge | 90% | 96 | 92.7% [84.7%, 98.9%] | 29.46 | 0 | 0 | — |
| 2012 | Leave-one-year-out | Ridge | 90% | 96 | 92.7% [84.7%, 98.9%] | 29.46 | 0 | 0 | — |
| 2012 | Training-only inflation | Ridge | 90% | 96 | 97.9% [95.3%, 100.0%] | 37.17 | 0 | 0 | — |
| 2012 | Weather-regime Mondrian | Ridge | 90% | 96 | 93.8% [85.3%, 99.0%] | 32.07 | 0 | 0 | — |
| 2012 | Climate-similarity weighting | Ridge | 90% | 96 | 93.8% [85.3%, 99.0%] | 30.47 | 0 | 0 | — |
| 2012 | P33 reference | Forest | 80% | 96 | 78.1% [66.3%, 88.5%] | 21.06 | 0 | 0 | Yes |
| 2012 | Leave-one-year-out | Forest | 80% | 96 | 78.1% [66.3%, 88.5%] | 21.06 | 0 | 0 | Yes |
| 2012 | Training-only inflation | Forest | 80% | 96 | 84.4% [75.5%, 92.5%] | 24.08 | 0 | 0 | — |
| 2012 | Weather-regime Mondrian | Forest | 80% | 96 | 80.2% [68.0%, 89.6%] | 22.01 | 0 | 0 | — |
| 2012 | Climate-similarity weighting | Forest | 80% | 96 | 76.0% [62.7%, 86.9%] | 20.50 | 0 | 0 | Yes |
| 2012 | P33 reference | Forest | 90% | 96 | 88.5% [80.4%, 96.2%] | 26.08 | 0 | 0 | Yes |
| 2012 | Leave-one-year-out | Forest | 90% | 96 | 88.5% [80.4%, 96.2%] | 26.08 | 0 | 0 | Yes |
| 2012 | Training-only inflation | Forest | 90% | 96 | 92.7% [87.4%, 97.9%] | 29.82 | 0 | 0 | — |
| 2012 | Weather-regime Mondrian | Forest | 90% | 96 | 91.7% [85.3%, 97.7%] | 28.52 | 0 | 0 | — |
| 2012 | Climate-similarity weighting | Forest | 90% | 96 | 88.5% [80.4%, 96.2%] | 26.95 | 0 | 0 | Yes |
| 2013 | P33 reference | Ridge | 80% | 86 | 44.2% [25.7%, 58.1%] | 23.51 | 0 | 0 | Yes |
| 2013 | Leave-one-year-out | Ridge | 80% | 86 | 44.2% [25.7%, 58.1%] | 23.51 | 0 | 0 | Yes |
| 2013 | Training-only inflation | Ridge | 80% | 86 | 59.3% [40.3%, 73.6%] | 27.41 | 0 | 0 | Yes |
| 2013 | Weather-regime Mondrian | Ridge | 80% | 86 | 43.0% [26.2%, 54.4%] | 22.81 | 0 | 0 | Yes |
| 2013 | Climate-similarity weighting | Ridge | 80% | 86 | 43.0% [25.7%, 55.2%] | 23.13 | 0 | 0 | Yes |
| 2013 | P33 reference | Ridge | 90% | 86 | 77.9% [64.9%, 87.9%] | 30.84 | 0 | 0 | Yes |
| 2013 | Leave-one-year-out | Ridge | 90% | 86 | 77.9% [64.9%, 87.9%] | 30.84 | 0 | 0 | Yes |
| 2013 | Training-only inflation | Ridge | 90% | 86 | 87.2% [80.0%, 92.5%] | 35.97 | 0 | 0 | Yes |
| 2013 | Weather-regime Mondrian | Ridge | 90% | 86 | 76.7% [60.6%, 87.4%] | 30.15 | 0 | 0 | Yes |
| 2013 | Climate-similarity weighting | Ridge | 90% | 86 | 79.1% [67.1%, 88.2%] | 31.06 | 0 | 0 | Yes |
| 2013 | P33 reference | Forest | 80% | 86 | 60.5% [36.3%, 81.7%] | 22.10 | 0 | 0 | Yes |
| 2013 | Leave-one-year-out | Forest | 80% | 86 | 60.5% [36.3%, 81.7%] | 22.10 | 0 | 0 | Yes |
| 2013 | Training-only inflation | Forest | 80% | 86 | 69.8% [47.7%, 88.2%] | 25.11 | 0 | 0 | Yes |
| 2013 | Weather-regime Mondrian | Forest | 80% | 86 | 58.1% [34.1%, 79.8%] | 21.78 | 0 | 0 | Yes |
| 2013 | Climate-similarity weighting | Forest | 80% | 86 | 61.6% [39.1%, 81.7%] | 22.37 | 0 | 0 | Yes |
| 2013 | P33 reference | Forest | 90% | 86 | 70.9% [50.0%, 88.5%] | 27.42 | 0 | 0 | Yes |
| 2013 | Leave-one-year-out | Forest | 90% | 86 | 70.9% [50.0%, 88.5%] | 27.42 | 0 | 0 | Yes |
| 2013 | Training-only inflation | Forest | 90% | 86 | 79.1% [63.9%, 90.8%] | 31.16 | 0 | 0 | Yes |
| 2013 | Weather-regime Mondrian | Forest | 90% | 86 | 69.8% [47.7%, 88.2%] | 27.18 | 0 | 0 | Yes |
| 2013 | Climate-similarity weighting | Forest | 90% | 86 | 75.6% [58.2%, 90.2%] | 29.61 | 0 | 0 | Yes |
| 2014 | P33 reference | Ridge | 80% | 84 | 66.7% [47.4%, 83.8%] | 24.87 | 0 | 0 | Yes |
| 2014 | Leave-one-year-out | Ridge | 80% | 84 | 66.7% [47.4%, 83.8%] | 24.87 | 0 | 0 | Yes |
| 2014 | Training-only inflation | Ridge | 80% | 84 | 78.6% [62.6%, 91.3%] | 31.10 | 0 | 0 | Yes |
| 2014 | Weather-regime Mondrian | Ridge | 80% | 84 | 63.1% [41.3%, 82.0%] | 23.46 | 0 | 0 | Yes |
| 2014 | Climate-similarity weighting | Ridge | 80% | 84 | 67.9% [48.7%, 84.6%] | 25.98 | 0 | 0 | Yes |
| 2014 | P33 reference | Ridge | 90% | 84 | 83.3% [67.0%, 96.2%] | 32.69 | 0 | 0 | Yes |
| 2014 | Leave-one-year-out | Ridge | 90% | 84 | 83.3% [67.0%, 96.2%] | 32.69 | 0 | 0 | Yes |
| 2014 | Training-only inflation | Ridge | 90% | 84 | 96.4% [88.8%, 100.0%] | 40.88 | 0 | 0 | — |
| 2014 | Weather-regime Mondrian | Ridge | 90% | 84 | 79.8% [62.2%, 93.8%] | 30.72 | 0 | 0 | Yes |
| 2014 | Climate-similarity weighting | Ridge | 90% | 84 | 83.3% [67.0%, 96.2%] | 33.67 | 0 | 0 | Yes |
| 2014 | P33 reference | Forest | 80% | 84 | 51.2% [26.5%, 74.1%] | 22.55 | 0 | 0 | Yes |
| 2014 | Leave-one-year-out | Forest | 80% | 84 | 51.2% [26.5%, 74.1%] | 22.55 | 0 | 0 | Yes |
| 2014 | Training-only inflation | Forest | 80% | 84 | 72.6% [54.1%, 87.4%] | 28.05 | 0 | 0 | Yes |
| 2014 | Weather-regime Mondrian | Forest | 80% | 84 | 53.6% [26.7%, 76.6%] | 22.18 | 0 | 0 | Yes |
| 2014 | Climate-similarity weighting | Forest | 80% | 84 | 54.8% [30.8%, 76.2%] | 23.53 | 0 | 0 | Yes |
| 2014 | P33 reference | Forest | 90% | 84 | 73.8% [56.4%, 87.7%] | 28.46 | 0 | 0 | Yes |
| 2014 | Leave-one-year-out | Forest | 90% | 84 | 73.8% [56.4%, 87.7%] | 28.46 | 0 | 0 | Yes |
| 2014 | Training-only inflation | Forest | 90% | 84 | 88.1% [78.8%, 96.3%] | 35.40 | 0 | 0 | Yes |
| 2014 | Weather-regime Mondrian | Forest | 90% | 84 | 70.2% [51.5%, 86.3%] | 28.26 | 0 | 0 | Yes |
| 2014 | Climate-similarity weighting | Forest | 90% | 84 | 77.4% [63.3%, 89.3%] | 30.87 | 0 | 0 | Yes |
| 2015 | P33 reference | Ridge | 80% | 81 | 84.0% [71.4%, 94.7%] | 24.91 | 0 | 0 | — |
| 2015 | Leave-one-year-out | Ridge | 80% | 81 | 84.0% [71.4%, 94.7%] | 24.91 | 0 | 0 | — |
| 2015 | Training-only inflation | Ridge | 80% | 81 | 96.3% [93.3%, 98.9%] | 31.09 | 0 | 0 | — |
| 2015 | Weather-regime Mondrian | Ridge | 80% | 81 | 86.4% [76.0%, 95.2%] | 26.48 | 0 | 0 | — |
| 2015 | Climate-similarity weighting | Ridge | 80% | 81 | 84.0% [71.4%, 94.7%] | 24.91 | 0 | 0 | — |
| 2015 | P33 reference | Ridge | 90% | 81 | 96.3% [93.3%, 98.9%] | 31.58 | 0 | 0 | — |
| 2015 | Leave-one-year-out | Ridge | 90% | 81 | 96.3% [93.3%, 98.9%] | 31.58 | 0 | 0 | — |
| 2015 | Training-only inflation | Ridge | 90% | 81 | 98.8% [96.4%, 100.0%] | 39.41 | 0 | 0 | — |
| 2015 | Weather-regime Mondrian | Ridge | 90% | 81 | 97.5% [94.1%, 100.0%] | 32.91 | 0 | 0 | — |
| 2015 | Climate-similarity weighting | Ridge | 90% | 81 | 96.3% [93.3%, 98.9%] | 31.98 | 0 | 0 | — |
| 2015 | P33 reference | Forest | 80% | 81 | 81.5% [73.1%, 89.4%] | 21.61 | 0 | 0 | — |
| 2015 | Leave-one-year-out | Forest | 80% | 81 | 81.5% [73.1%, 89.4%] | 21.61 | 0 | 0 | — |
| 2015 | Training-only inflation | Forest | 80% | 81 | 93.8% [85.9%, 100.0%] | 25.24 | 0 | 0 | — |
| 2015 | Weather-regime Mondrian | Forest | 80% | 81 | 81.5% [73.7%, 88.4%] | 22.91 | 0 | 0 | — |
| 2015 | Climate-similarity weighting | Forest | 80% | 81 | 87.7% [78.4%, 95.0%] | 22.61 | 0 | 0 | — |
| 2015 | P33 reference | Forest | 90% | 81 | 97.5% [93.9%, 100.0%] | 28.30 | 0 | 0 | — |
| 2015 | Leave-one-year-out | Forest | 90% | 81 | 97.5% [93.9%, 100.0%] | 28.30 | 0 | 0 | — |
| 2015 | Training-only inflation | Forest | 90% | 81 | 100.0% [100.0%, 100.0%] | 33.07 | 0 | 0 | — |
| 2015 | Weather-regime Mondrian | Forest | 90% | 81 | 97.5% [94.5%, 100.0%] | 30.09 | 0 | 0 | — |
| 2015 | Climate-similarity weighting | Forest | 90% | 81 | 97.5% [93.9%, 100.0%] | 29.50 | 0 | 0 | — |
| 2016 | P33 reference | Ridge | 80% | 80 | 50.0% [31.9%, 66.3%] | 25.01 | 0 | 0 | Yes |
| 2016 | Leave-one-year-out | Ridge | 80% | 80 | 50.0% [31.9%, 66.3%] | 25.01 | 0 | 0 | Yes |
| 2016 | Training-only inflation | Ridge | 80% | 80 | 62.5% [42.1%, 78.2%] | 29.68 | 0 | 0 | Yes |
| 2016 | Weather-regime Mondrian | Ridge | 80% | 80 | 60.0% [39.4%, 76.4%] | 27.06 | 0 | 0 | Yes |
| 2016 | Climate-similarity weighting | Ridge | 80% | 80 | 60.0% [37.9%, 76.4%] | 28.05 | 0 | 0 | Yes |
| 2016 | P33 reference | Ridge | 90% | 80 | 71.2% [53.3%, 85.1%] | 32.53 | 0 | 0 | Yes |
| 2016 | Leave-one-year-out | Ridge | 90% | 80 | 71.2% [53.3%, 85.1%] | 32.53 | 0 | 0 | Yes |
| 2016 | Training-only inflation | Ridge | 90% | 80 | 83.8% [67.9%, 94.8%] | 38.60 | 0 | 0 | Yes |
| 2016 | Weather-regime Mondrian | Ridge | 90% | 80 | 73.8% [53.5%, 89.2%] | 33.50 | 0 | 0 | Yes |
| 2016 | Climate-similarity weighting | Ridge | 90% | 80 | 77.5% [60.0%, 90.5%] | 34.53 | 0 | 0 | Yes |
| 2016 | P33 reference | Forest | 80% | 80 | 53.8% [27.3%, 72.8%] | 22.81 | 0 | 0 | Yes |
| 2016 | Leave-one-year-out | Forest | 80% | 80 | 53.8% [27.3%, 72.8%] | 22.81 | 0 | 0 | Yes |
| 2016 | Training-only inflation | Forest | 80% | 80 | 71.2% [46.4%, 88.6%] | 29.10 | 0 | 0 | Yes |
| 2016 | Weather-regime Mondrian | Forest | 80% | 80 | 60.0% [34.9%, 78.4%] | 24.77 | 0 | 0 | Yes |
| 2016 | Climate-similarity weighting | Forest | 80% | 80 | 63.7% [38.0%, 81.0%] | 25.46 | 0 | 0 | Yes |
| 2016 | P33 reference | Forest | 90% | 80 | 68.8% [43.7%, 85.7%] | 28.76 | 0 | 0 | Yes |
| 2016 | Leave-one-year-out | Forest | 90% | 80 | 68.8% [43.7%, 85.7%] | 28.76 | 0 | 0 | Yes |
| 2016 | Training-only inflation | Forest | 90% | 80 | 85.0% [68.1%, 95.7%] | 36.67 | 0 | 0 | Yes |
| 2016 | Weather-regime Mondrian | Forest | 90% | 80 | 75.0% [54.7%, 90.0%] | 31.19 | 0 | 0 | Yes |
| 2016 | Climate-similarity weighting | Forest | 90% | 80 | 80.0% [59.2%, 94.3%] | 31.72 | 0 | 0 | Yes |
| 2017 | P33 reference | Ridge | 80% | 75 | 42.7% [28.2%, 59.0%] | 24.82 | 0 | 0 | Yes |
| 2017 | Leave-one-year-out | Ridge | 80% | 75 | 42.7% [28.2%, 59.0%] | 24.82 | 0 | 0 | Yes |
| 2017 | Training-only inflation | Ridge | 80% | 75 | 53.3% [39.5%, 69.6%] | 28.74 | 0 | 0 | Yes |
| 2017 | Weather-regime Mondrian | Ridge | 80% | 75 | 44.0% [31.3%, 60.3%] | 25.58 | 0 | 0 | Yes |
| 2017 | Climate-similarity weighting | Ridge | 80% | 75 | 52.0% [36.4%, 68.8%] | 27.79 | 0 | 0 | Yes |
| 2017 | P33 reference | Ridge | 90% | 75 | 62.7% [48.1%, 77.3%] | 32.27 | 0 | 0 | Yes |
| 2017 | Leave-one-year-out | Ridge | 90% | 75 | 62.7% [48.1%, 77.3%] | 32.27 | 0 | 0 | Yes |
| 2017 | Training-only inflation | Ridge | 90% | 75 | 82.7% [70.9%, 94.8%] | 37.37 | 0 | 0 | Yes |
| 2017 | Weather-regime Mondrian | Ridge | 90% | 75 | 68.0% [54.2%, 82.0%] | 32.73 | 0 | 0 | Yes |
| 2017 | Climate-similarity weighting | Ridge | 90% | 75 | 72.0% [57.0%, 88.1%] | 34.40 | 0 | 0 | Yes |
| 2017 | P33 reference | Forest | 80% | 75 | 48.0% [37.5%, 60.3%] | 22.72 | 0 | 0 | Yes |
| 2017 | Leave-one-year-out | Forest | 80% | 75 | 48.0% [37.5%, 60.3%] | 22.72 | 0 | 0 | Yes |
| 2017 | Training-only inflation | Forest | 80% | 75 | 76.0% [64.4%, 88.6%] | 30.75 | 0 | 0 | Yes |
| 2017 | Weather-regime Mondrian | Forest | 80% | 75 | 62.7% [47.5%, 76.0%] | 24.76 | 0 | 0 | Yes |
| 2017 | Climate-similarity weighting | Forest | 80% | 75 | 60.0% [46.4%, 75.0%] | 25.44 | 0 | 0 | Yes |
| 2017 | P33 reference | Forest | 90% | 75 | 74.7% [61.5%, 88.5%] | 28.98 | 0 | 0 | Yes |
| 2017 | Leave-one-year-out | Forest | 90% | 75 | 74.7% [61.5%, 88.5%] | 28.98 | 0 | 0 | Yes |
| 2017 | Training-only inflation | Forest | 90% | 75 | 93.3% [84.2%, 100.0%] | 39.23 | 0 | 0 | — |
| 2017 | Weather-regime Mondrian | Forest | 90% | 75 | 74.7% [56.1%, 89.5%] | 30.83 | 0 | 0 | Yes |
| 2017 | Climate-similarity weighting | Forest | 90% | 75 | 78.7% [69.0%, 89.2%] | 31.77 | 0 | 0 | Yes |
| 2018 | P33 reference | Ridge | 80% | 65 | 100.0% [100.0%, 100.0%] | 26.80 | 0 | 0 | — |
| 2018 | Leave-one-year-out | Ridge | 80% | 65 | 100.0% [100.0%, 100.0%] | 26.80 | 0 | 0 | — |
| 2018 | Training-only inflation | Ridge | 80% | 65 | 100.0% [100.0%, 100.0%] | 33.75 | 0 | 0 | — |
| 2018 | Weather-regime Mondrian | Ridge | 80% | 65 | 100.0% [100.0%, 100.0%] | 27.12 | 0 | 0 | — |
| 2018 | Climate-similarity weighting | Ridge | 80% | 65 | 100.0% [100.0%, 100.0%] | 28.30 | 0 | 0 | — |
| 2018 | P33 reference | Ridge | 90% | 65 | 100.0% [100.0%, 100.0%] | 33.31 | 0 | 0 | — |
| 2018 | Leave-one-year-out | Ridge | 90% | 65 | 100.0% [100.0%, 100.0%] | 33.31 | 0 | 0 | — |
| 2018 | Training-only inflation | Ridge | 90% | 65 | 100.0% [100.0%, 100.0%] | 41.95 | 0 | 0 | — |
| 2018 | Weather-regime Mondrian | Ridge | 90% | 65 | 100.0% [100.0%, 100.0%] | 33.71 | 0 | 0 | — |
| 2018 | Climate-similarity weighting | Ridge | 90% | 65 | 100.0% [100.0%, 100.0%] | 33.72 | 0 | 0 | — |
| 2018 | P33 reference | Forest | 80% | 65 | 87.7% [82.1%, 93.9%] | 23.46 | 0 | 0 | — |
| 2018 | Leave-one-year-out | Forest | 80% | 65 | 87.7% [82.1%, 93.9%] | 23.46 | 0 | 0 | — |
| 2018 | Training-only inflation | Forest | 80% | 65 | 96.9% [93.0%, 100.0%] | 31.63 | 0 | 0 | — |
| 2018 | Weather-regime Mondrian | Forest | 80% | 65 | 84.6% [78.1%, 90.9%] | 22.40 | 0 | 0 | — |
| 2018 | Climate-similarity weighting | Forest | 80% | 65 | 87.7% [82.1%, 93.9%] | 23.46 | 0 | 0 | — |
| 2018 | P33 reference | Forest | 90% | 65 | 96.9% [93.0%, 100.0%] | 28.94 | 0 | 0 | — |
| 2018 | Leave-one-year-out | Forest | 90% | 65 | 96.9% [93.0%, 100.0%] | 28.94 | 0 | 0 | — |
| 2018 | Training-only inflation | Forest | 90% | 65 | 100.0% [100.0%, 100.0%] | 39.02 | 0 | 0 | — |
| 2018 | Weather-regime Mondrian | Forest | 90% | 65 | 93.8% [89.2%, 98.2%] | 28.10 | 0 | 0 | — |
| 2018 | Climate-similarity weighting | Forest | 90% | 65 | 96.9% [93.0%, 100.0%] | 29.41 | 0 | 0 | — |
| 2019 | P33 reference | Ridge | 80% | 64 | 70.3% [44.4%, 90.0%] | 27.02 | 0 | 0 | Yes |
| 2019 | Leave-one-year-out | Ridge | 80% | 64 | 70.3% [44.4%, 90.0%] | 27.02 | 0 | 0 | Yes |
| 2019 | Training-only inflation | Ridge | 80% | 64 | 82.8% [60.8%, 96.7%] | 32.04 | 0 | 0 | — |
| 2019 | Weather-regime Mondrian | Ridge | 80% | 64 | 67.2% [38.6%, 88.7%] | 26.44 | 0 | 0 | Yes |
| 2019 | Climate-similarity weighting | Ridge | 80% | 64 | 65.6% [37.5%, 87.9%] | 24.45 | 0 | 0 | Yes |
| 2019 | P33 reference | Ridge | 90% | 64 | 84.4% [62.2%, 97.6%] | 33.43 | 0 | 0 | Yes |
| 2019 | Leave-one-year-out | Ridge | 90% | 64 | 84.4% [62.2%, 97.6%] | 33.43 | 0 | 0 | Yes |
| 2019 | Training-only inflation | Ridge | 90% | 64 | 87.5% [68.5%, 98.8%] | 39.63 | 0 | 0 | Yes |
| 2019 | Weather-regime Mondrian | Ridge | 90% | 64 | 81.2% [61.1%, 95.3%] | 32.75 | 0 | 0 | Yes |
| 2019 | Climate-similarity weighting | Ridge | 90% | 64 | 78.1% [56.1%, 93.4%] | 30.24 | 0 | 0 | Yes |
| 2019 | P33 reference | Forest | 80% | 64 | 50.0% [38.1%, 63.2%] | 23.06 | 0 | 0 | Yes |
| 2019 | Leave-one-year-out | Forest | 80% | 64 | 50.0% [38.1%, 63.2%] | 23.06 | 0 | 0 | Yes |
| 2019 | Training-only inflation | Forest | 80% | 64 | 73.4% [58.5%, 84.8%] | 30.45 | 0 | 0 | Yes |
| 2019 | Weather-regime Mondrian | Forest | 80% | 64 | 43.8% [32.8%, 55.1%] | 21.84 | 0 | 0 | Yes |
| 2019 | Climate-similarity weighting | Forest | 80% | 64 | 48.4% [33.9%, 62.3%] | 21.86 | 0 | 0 | Yes |
| 2019 | P33 reference | Forest | 90% | 64 | 71.9% [55.2%, 84.6%] | 29.53 | 0 | 0 | Yes |
| 2019 | Leave-one-year-out | Forest | 90% | 64 | 71.9% [55.2%, 84.6%] | 29.53 | 0 | 0 | Yes |
| 2019 | Training-only inflation | Forest | 90% | 64 | 93.8% [86.0%, 98.6%] | 38.99 | 0 | 0 | — |
| 2019 | Weather-regime Mondrian | Forest | 90% | 64 | 73.4% [60.8%, 83.3%] | 27.66 | 0 | 0 | Yes |
| 2019 | Climate-similarity weighting | Forest | 90% | 64 | 68.8% [54.5%, 79.1%] | 27.91 | 0 | 0 | Yes |
| 2020 | P33 reference | Ridge | 80% | 94 | 89.4% [79.3%, 97.1%] | 22.79 | 0 | 0 | — |
| 2020 | Leave-one-year-out | Ridge | 80% | 94 | 89.4% [79.3%, 97.1%] | 22.79 | 0 | 0 | — |
| 2020 | Training-only inflation | Ridge | 80% | 94 | 89.4% [79.3%, 97.1%] | 22.79 | 0 | 0 | — |
| 2020 | Weather-regime Mondrian | Ridge | 80% | 94 | 89.4% [79.3%, 97.1%] | 23.34 | 0 | 0 | — |
| 2020 | Climate-similarity weighting | Ridge | 80% | 94 | 93.6% [85.7%, 100.0%] | 24.91 | 0 | 0 | — |
| 2020 | P33 reference | Ridge | 90% | 94 | 98.9% [96.8%, 100.0%] | 28.61 | 0 | 0 | — |
| 2020 | Leave-one-year-out | Ridge | 90% | 94 | 98.9% [96.8%, 100.0%] | 28.61 | 0 | 0 | — |
| 2020 | Training-only inflation | Ridge | 90% | 94 | 98.9% [96.8%, 100.0%] | 28.61 | 0 | 0 | — |
| 2020 | Weather-regime Mondrian | Ridge | 90% | 94 | 98.9% [96.8%, 100.0%] | 29.47 | 0 | 0 | — |
| 2020 | Climate-similarity weighting | Ridge | 90% | 94 | 100.0% [100.0%, 100.0%] | 31.58 | 0 | 0 | — |
| 2020 | P33 reference | Forest | 80% | 94 | 87.2% [76.9%, 95.7%] | 20.96 | 0 | 0 | — |
| 2020 | Leave-one-year-out | Forest | 80% | 94 | 87.2% [76.9%, 95.7%] | 20.96 | 0 | 0 | — |
| 2020 | Training-only inflation | Forest | 80% | 94 | 90.4% [82.2%, 97.8%] | 23.28 | 0 | 0 | — |
| 2020 | Weather-regime Mondrian | Forest | 80% | 94 | 83.0% [73.3%, 90.7%] | 20.84 | 0 | 0 | — |
| 2020 | Climate-similarity weighting | Forest | 80% | 94 | 88.3% [78.5%, 95.9%] | 21.97 | 0 | 0 | — |
| 2020 | P33 reference | Forest | 90% | 94 | 92.6% [84.8%, 98.1%] | 27.29 | 0 | 0 | — |
| 2020 | Leave-one-year-out | Forest | 90% | 94 | 92.6% [84.8%, 98.1%] | 27.29 | 0 | 0 | — |
| 2020 | Training-only inflation | Forest | 90% | 94 | 97.9% [94.9%, 100.0%] | 30.31 | 0 | 0 | — |
| 2020 | Weather-regime Mondrian | Forest | 90% | 94 | 93.6% [86.4%, 98.9%] | 27.20 | 0 | 0 | — |
| 2020 | Climate-similarity weighting | Forest | 90% | 94 | 94.7% [87.2%, 100.0%] | 28.91 | 0 | 0 | — |
| 2021 | P33 reference | Ridge | 80% | 85 | 76.5% [60.6%, 89.7%] | 24.78 | 0 | 0 | Yes |
| 2021 | Leave-one-year-out | Ridge | 80% | 85 | 76.5% [60.6%, 89.7%] | 24.78 | 0 | 0 | Yes |
| 2021 | Training-only inflation | Ridge | 80% | 85 | 85.9% [73.7%, 95.0%] | 31.33 | 0 | 0 | — |
| 2021 | Weather-regime Mondrian | Ridge | 80% | 85 | 78.8% [63.7%, 91.3%] | 25.42 | 0 | 0 | Yes |
| 2021 | Climate-similarity weighting | Ridge | 80% | 85 | 76.5% [60.6%, 89.7%] | 25.13 | 0 | 0 | Yes |
| 2021 | P33 reference | Ridge | 90% | 85 | 85.9% [73.7%, 95.0%] | 31.29 | 0 | 0 | Yes |
| 2021 | Leave-one-year-out | Ridge | 90% | 85 | 85.9% [73.7%, 95.0%] | 31.29 | 0 | 0 | Yes |
| 2021 | Training-only inflation | Ridge | 90% | 85 | 92.9% [82.6%, 100.0%] | 39.56 | 0 | 0 | — |
| 2021 | Weather-regime Mondrian | Ridge | 90% | 85 | 85.9% [72.7%, 96.0%] | 31.55 | 0 | 0 | Yes |
| 2021 | Climate-similarity weighting | Ridge | 90% | 85 | 88.2% [77.0%, 97.4%] | 31.62 | 0 | 0 | Yes |
| 2021 | P33 reference | Forest | 80% | 85 | 71.8% [46.0%, 90.8%] | 22.38 | 0 | 0 | Yes |
| 2021 | Leave-one-year-out | Forest | 80% | 85 | 71.8% [46.0%, 90.8%] | 22.38 | 0 | 0 | Yes |
| 2021 | Training-only inflation | Forest | 80% | 85 | 80.0% [59.2%, 95.0%] | 28.29 | 0 | 0 | — |
| 2021 | Weather-regime Mondrian | Forest | 80% | 85 | 71.8% [47.5%, 89.9%] | 23.26 | 0 | 0 | Yes |
| 2021 | Climate-similarity weighting | Forest | 80% | 85 | 71.8% [46.0%, 90.8%] | 23.12 | 0 | 0 | Yes |
| 2021 | P33 reference | Forest | 90% | 85 | 78.8% [57.8%, 95.0%] | 27.66 | 0 | 0 | Yes |
| 2021 | Leave-one-year-out | Forest | 90% | 85 | 78.8% [57.8%, 95.0%] | 27.66 | 0 | 0 | Yes |
| 2021 | Training-only inflation | Forest | 90% | 85 | 88.2% [70.5%, 100.0%] | 34.96 | 0 | 0 | Yes |
| 2021 | Weather-regime Mondrian | Forest | 90% | 85 | 80.0% [60.5%, 94.3%] | 29.73 | 0 | 0 | Yes |
| 2021 | Climate-similarity weighting | Forest | 90% | 85 | 81.2% [59.7%, 96.2%] | 29.78 | 0 | 0 | Yes |
| 2022 | P33 reference | Ridge | 80% | 87 | 71.3% [52.1%, 88.9%] | 24.05 | 0 | 0 | Yes |
| 2022 | Leave-one-year-out | Ridge | 80% | 87 | 71.3% [52.1%, 88.9%] | 24.05 | 0 | 0 | Yes |
| 2022 | Training-only inflation | Ridge | 80% | 87 | 86.2% [71.1%, 98.7%] | 29.21 | 0 | 0 | — |
| 2022 | Weather-regime Mondrian | Ridge | 80% | 87 | 77.0% [58.2%, 92.5%] | 25.02 | 0 | 0 | Yes |
| 2022 | Climate-similarity weighting | Ridge | 80% | 87 | 81.6% [65.9%, 94.5%] | 27.30 | 0 | 0 | — |
| 2022 | P33 reference | Ridge | 90% | 87 | 89.7% [77.4%, 100.0%] | 30.81 | 0 | 0 | Yes |
| 2022 | Leave-one-year-out | Ridge | 90% | 87 | 89.7% [77.4%, 100.0%] | 30.81 | 0 | 0 | Yes |
| 2022 | Training-only inflation | Ridge | 90% | 87 | 94.3% [84.0%, 100.0%] | 37.41 | 0 | 0 | — |
| 2022 | Weather-regime Mondrian | Ridge | 90% | 87 | 87.4% [71.3%, 97.8%] | 31.62 | 0 | 0 | Yes |
| 2022 | Climate-similarity weighting | Ridge | 90% | 87 | 90.8% [77.8%, 100.0%] | 32.99 | 0 | 0 | — |
| 2022 | P33 reference | Forest | 80% | 87 | 80.5% [69.0%, 90.1%] | 22.11 | 0 | 0 | — |
| 2022 | Leave-one-year-out | Forest | 80% | 87 | 80.5% [69.0%, 90.1%] | 22.11 | 0 | 0 | — |
| 2022 | Training-only inflation | Forest | 80% | 87 | 88.5% [76.2%, 96.5%] | 26.86 | 0 | 0 | — |
| 2022 | Weather-regime Mondrian | Forest | 80% | 87 | 83.9% [68.3%, 94.3%] | 24.34 | 0 | 0 | — |
| 2022 | Climate-similarity weighting | Forest | 80% | 87 | 80.5% [69.0%, 90.1%] | 23.26 | 0 | 0 | — |
| 2022 | P33 reference | Forest | 90% | 87 | 89.7% [80.0%, 96.5%] | 29.11 | 0 | 0 | Yes |
| 2022 | Leave-one-year-out | Forest | 90% | 87 | 89.7% [80.0%, 96.5%] | 29.11 | 0 | 0 | Yes |
| 2022 | Training-only inflation | Forest | 90% | 87 | 97.7% [92.4%, 100.0%] | 35.36 | 0 | 0 | — |
| 2022 | Weather-regime Mondrian | Forest | 90% | 87 | 94.3% [81.0%, 100.0%] | 31.88 | 0 | 0 | — |
| 2022 | Climate-similarity weighting | Forest | 90% | 87 | 89.7% [80.0%, 96.5%] | 32.28 | 0 | 0 | Yes |
| 2023 | P33 reference | Ridge | 80% | 69 | 81.2% [70.6%, 89.6%] | 26.48 | 0 | 0 | — |
| 2023 | Leave-one-year-out | Ridge | 80% | 69 | 81.2% [70.6%, 89.6%] | 26.48 | 0 | 0 | — |
| 2023 | Training-only inflation | Ridge | 80% | 69 | 87.0% [77.5%, 94.2%] | 32.44 | 0 | 0 | — |
| 2023 | Weather-regime Mondrian | Ridge | 80% | 69 | 79.7% [66.7%, 90.0%] | 29.14 | 0 | 0 | Yes |
| 2023 | Climate-similarity weighting | Ridge | 80% | 69 | 82.6% [71.0%, 91.9%] | 28.81 | 0 | 0 | — |
| 2023 | P33 reference | Ridge | 90% | 69 | 89.9% [83.9%, 95.1%] | 33.45 | 0 | 0 | Yes |
| 2023 | Leave-one-year-out | Ridge | 90% | 69 | 89.9% [83.9%, 95.1%] | 33.45 | 0 | 0 | Yes |
| 2023 | Training-only inflation | Ridge | 90% | 69 | 97.1% [93.0%, 100.0%] | 40.96 | 0 | 0 | — |
| 2023 | Weather-regime Mondrian | Ridge | 90% | 69 | 94.2% [87.8%, 98.6%] | 35.92 | 0 | 0 | — |
| 2023 | Climate-similarity weighting | Ridge | 90% | 69 | 91.3% [86.0%, 95.5%] | 34.54 | 0 | 0 | — |
| 2023 | P33 reference | Forest | 80% | 69 | 68.1% [53.7%, 83.1%] | 23.33 | 0 | 0 | Yes |
| 2023 | Leave-one-year-out | Forest | 80% | 69 | 68.1% [53.7%, 83.1%] | 23.33 | 0 | 0 | Yes |
| 2023 | Training-only inflation | Forest | 80% | 69 | 79.7% [70.4%, 90.5%] | 30.15 | 0 | 0 | Yes |
| 2023 | Weather-regime Mondrian | Forest | 80% | 69 | 71.0% [56.7%, 84.7%] | 27.08 | 0 | 0 | Yes |
| 2023 | Climate-similarity weighting | Forest | 80% | 69 | 68.1% [53.7%, 83.1%] | 24.55 | 0 | 0 | Yes |
| 2023 | P33 reference | Forest | 90% | 69 | 78.3% [66.7%, 90.4%] | 29.10 | 0 | 0 | Yes |
| 2023 | Leave-one-year-out | Forest | 90% | 69 | 78.3% [66.7%, 90.4%] | 29.10 | 0 | 0 | Yes |
| 2023 | Training-only inflation | Forest | 90% | 69 | 92.8% [86.2%, 98.4%] | 37.61 | 0 | 0 | — |
| 2023 | Weather-regime Mondrian | Forest | 90% | 69 | 87.0% [79.3%, 92.8%] | 33.86 | 0 | 0 | Yes |
| 2023 | Climate-similarity weighting | Forest | 90% | 69 | 81.2% [73.1%, 91.2%] | 30.99 | 0 | 0 | Yes |

</details>

#### Kansas-to-state transfer

P32 contains the full preferred-with-fallback cohort and overlapping historical years. P37 uses its non-irrigated common test tail with Kansas training restricted to earlier years. P37 k = 0 uses Kansas radii. Positive k replaces the radius using the named district's earlier local years.

##### Nebraska

| Evaluation | Method | Learner | Nominal | n | Coverage [95% interval] | Mean width | Unbounded | Unavailable | Below nominal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P32 spatial transfer | P33 reference | Ridge | 80% | 1,733 | 75.6% [70.7%, 82.5%] | 26.71 | 0 | 0 | Yes |
| P32 spatial transfer | Leave-one-year-out | Ridge | 80% | 1,733 | 75.6% [70.7%, 82.5%] | 26.71 | 0 | 0 | Yes |
| P32 spatial transfer | Training-only inflation | Ridge | 80% | 1,733 | 80.6% [76.4%, 86.7%] | 29.45 | 0 | 0 | — |
| P32 spatial transfer | Weather-regime Mondrian | Ridge | 80% | 1,733 | 80.0% [75.8%, 86.8%] | 29.10 | 0 | 0 | Yes |
| P32 spatial transfer | Climate-similarity weighting | Ridge | 80% | 1,733 | 77.0% [72.6%, 83.6%] | 27.56 | 0 | 0 | Yes |
| P32 spatial transfer | P33 reference | Ridge | 90% | 1,733 | 85.3% [82.3%, 90.2%] | 32.72 | 0 | 0 | Yes |
| P32 spatial transfer | Leave-one-year-out | Ridge | 90% | 1,733 | 85.3% [82.3%, 90.2%] | 32.72 | 0 | 0 | Yes |
| P32 spatial transfer | Training-only inflation | Ridge | 90% | 1,733 | 88.5% [85.8%, 92.8%] | 36.07 | 0 | 0 | Yes |
| P32 spatial transfer | Weather-regime Mondrian | Ridge | 90% | 1,733 | 88.9% [86.3%, 93.1%] | 36.37 | 0 | 0 | Yes |
| P32 spatial transfer | Climate-similarity weighting | Ridge | 90% | 1,733 | 87.1% [84.4%, 91.5%] | 34.70 | 0 | 0 | Yes |
| P32 spatial transfer | P33 reference | Forest | 80% | 1,733 | 74.4% [69.5%, 79.9%] | 24.84 | 0 | 0 | Yes |
| P32 spatial transfer | Leave-one-year-out | Forest | 80% | 1,733 | 74.4% [69.5%, 79.9%] | 24.84 | 0 | 0 | Yes |
| P32 spatial transfer | Training-only inflation | Forest | 80% | 1,733 | 83.8% [80.4%, 88.0%] | 29.96 | 0 | 0 | — |
| P32 spatial transfer | Weather-regime Mondrian | Forest | 80% | 1,733 | 81.1% [77.6%, 86.2%] | 28.42 | 0 | 0 | — |
| P32 spatial transfer | Climate-similarity weighting | Forest | 80% | 1,733 | 73.7% [69.1%, 78.8%] | 24.11 | 0 | 0 | Yes |
| P32 spatial transfer | P33 reference | Forest | 90% | 1,733 | 87.2% [83.8%, 91.3%] | 33.28 | 0 | 0 | Yes |
| P32 spatial transfer | Leave-one-year-out | Forest | 90% | 1,733 | 87.2% [83.8%, 91.3%] | 33.28 | 0 | 0 | Yes |
| P32 spatial transfer | Training-only inflation | Forest | 90% | 1,733 | 92.8% [90.7%, 95.2%] | 40.14 | 0 | 0 | — |
| P32 spatial transfer | Weather-regime Mondrian | Forest | 90% | 1,733 | 90.7% [88.0%, 94.0%] | 37.07 | 0 | 0 | — |
| P32 spatial transfer | Climate-similarity weighting | Forest | 90% | 1,733 | 87.9% [84.7%, 91.8%] | 33.58 | 0 | 0 | Yes |
| P37 · 0 local years | P33 reference | Ridge | 80% | 462 | 55.0% [37.9%, 70.7%] | 18.34 | 0 | 0 | Yes |
| P37 · 0 local years | Leave-one-year-out | Ridge | 80% | 462 | 55.0% [37.9%, 70.7%] | 18.34 | 0 | 0 | Yes |
| P37 · 0 local years | Training-only inflation | Ridge | 80% | 462 | 58.9% [41.0%, 75.7%] | 19.89 | 0 | 0 | Yes |
| P37 · 0 local years | Weather-regime Mondrian | Ridge | 80% | 462 | 54.5% [38.0%, 69.7%] | 18.28 | 0 | 0 | Yes |
| P37 · 0 local years | Climate-similarity weighting | Ridge | 80% | 462 | 69.5% [65.9%, 74.2%] | Unbounded | 67 | 0 | Yes |
| P37 · 0 local years | P33 reference | Ridge | 90% | 462 | 64.5% [45.2%, 81.9%] | 22.95 | 0 | 0 | Yes |
| P37 · 0 local years | Leave-one-year-out | Ridge | 90% | 462 | 64.5% [45.2%, 81.9%] | 22.95 | 0 | 0 | Yes |
| P37 · 0 local years | Training-only inflation | Ridge | 90% | 462 | 68.0% [47.4%, 86.0%] | 24.89 | 0 | 0 | Yes |
| P37 · 0 local years | Weather-regime Mondrian | Ridge | 90% | 462 | 66.2% [46.4%, 83.8%] | 23.90 | 0 | 0 | Yes |
| P37 · 0 local years | Climate-similarity weighting | Ridge | 90% | 462 | 85.3% [80.5%, 90.8%] | Unbounded | 142 | 0 | Yes |
| P37 · 0 local years | P33 reference | Forest | 80% | 462 | 53.9% [39.2%, 65.9%] | 18.85 | 0 | 0 | Yes |
| P37 · 0 local years | Leave-one-year-out | Forest | 80% | 462 | 53.9% [39.2%, 65.9%] | 18.85 | 0 | 0 | Yes |
| P37 · 0 local years | Training-only inflation | Forest | 80% | 462 | 54.1% [39.7%, 66.1%] | 18.85 | 0 | 0 | Yes |
| P37 · 0 local years | Weather-regime Mondrian | Forest | 80% | 462 | 53.7% [38.5%, 66.1%] | 19.19 | 0 | 0 | Yes |
| P37 · 0 local years | Climate-similarity weighting | Forest | 80% | 462 | 69.9% [65.0%, 74.1%] | Unbounded | 67 | 0 | Yes |
| P37 · 0 local years | P33 reference | Forest | 90% | 462 | 68.8% [54.8%, 81.2%] | 25.17 | 0 | 0 | Yes |
| P37 · 0 local years | Leave-one-year-out | Forest | 90% | 462 | 68.8% [54.8%, 81.2%] | 25.17 | 0 | 0 | Yes |
| P37 · 0 local years | Training-only inflation | Forest | 90% | 462 | 68.8% [54.8%, 81.2%] | 25.18 | 0 | 0 | Yes |
| P37 · 0 local years | Weather-regime Mondrian | Forest | 90% | 462 | 72.5% [58.3%, 86.3%] | 27.17 | 0 | 0 | Yes |
| P37 · 0 local years | Climate-similarity weighting | Forest | 90% | 462 | 82.3% [77.3%, 86.2%] | Unbounded | 142 | 0 | Yes |
| P37 · 3 local years | P33 reference | Ridge | 80% | 462 | 66.7% [43.1%, 87.4%] | Unbounded | 1 | 0 | Yes |
| P37 · 3 local years | Leave-one-year-out | Ridge | 80% | 462 | 66.7% [43.1%, 87.4%] | Unbounded | 1 | 0 | Yes |
| P37 · 3 local years | Training-only inflation | Ridge | 80% | 462 | 68.4% [44.6%, 89.3%] | Unbounded | 1 | 0 | Yes |
| P37 · 3 local years | Weather-regime Mondrian | Ridge | 80% | 462 | 72.1% [50.6%, 89.3%] | Unbounded | 65 | 0 | Yes |
| P37 · 3 local years | Climate-similarity weighting | Ridge | 80% | 462 | 76.6% [56.9%, 91.9%] | Unbounded | 91 | 0 | Yes |
| P37 · 3 local years | P33 reference | Ridge | 90% | 462 | 73.2% [48.6%, 94.3%] | Unbounded | 1 | 0 | Yes |
| P37 · 3 local years | Leave-one-year-out | Ridge | 90% | 462 | 73.2% [48.6%, 94.3%] | Unbounded | 1 | 0 | Yes |
| P37 · 3 local years | Training-only inflation | Ridge | 90% | 462 | 76.0% [51.6%, 96.3%] | Unbounded | 1 | 0 | Yes |
| P37 · 3 local years | Weather-regime Mondrian | Ridge | 90% | 462 | 79.2% [57.9%, 96.2%] | Unbounded | 90 | 0 | Yes |
| P37 · 3 local years | Climate-similarity weighting | Ridge | 90% | 462 | 85.9% [69.0%, 99.0%] | Unbounded | 183 | 0 | Yes |
| P37 · 3 local years | P33 reference | Forest | 80% | 462 | 55.6% [33.8%, 72.8%] | Unbounded | 1 | 0 | Yes |
| P37 · 3 local years | Leave-one-year-out | Forest | 80% | 462 | 55.6% [33.8%, 72.8%] | Unbounded | 1 | 0 | Yes |
| P37 · 3 local years | Training-only inflation | Forest | 80% | 462 | 55.6% [33.8%, 72.8%] | Unbounded | 1 | 0 | Yes |
| P37 · 3 local years | Weather-regime Mondrian | Forest | 80% | 462 | 59.5% [39.5%, 75.0%] | Unbounded | 65 | 0 | Yes |
| P37 · 3 local years | Climate-similarity weighting | Forest | 80% | 462 | 70.3% [50.3%, 85.8%] | Unbounded | 91 | 0 | Yes |
| P37 · 3 local years | P33 reference | Forest | 90% | 462 | 64.7% [41.0%, 83.7%] | Unbounded | 1 | 0 | Yes |
| P37 · 3 local years | Leave-one-year-out | Forest | 90% | 462 | 64.7% [41.0%, 83.7%] | Unbounded | 1 | 0 | Yes |
| P37 · 3 local years | Training-only inflation | Forest | 90% | 462 | 64.7% [41.0%, 83.7%] | Unbounded | 1 | 0 | Yes |
| P37 · 3 local years | Weather-regime Mondrian | Forest | 90% | 462 | 74.0% [56.6%, 88.3%] | Unbounded | 90 | 0 | Yes |
| P37 · 3 local years | Climate-similarity weighting | Forest | 90% | 462 | 84.4% [68.4%, 96.9%] | Unbounded | 183 | 0 | Yes |
| P37 · 5 local years | P33 reference | Ridge | 80% | 462 | 63.0% [42.6%, 81.2%] | 21.92 | 0 | 0 | Yes |
| P37 · 5 local years | Leave-one-year-out | Ridge | 80% | 462 | 63.0% [42.6%, 81.2%] | 21.92 | 0 | 0 | Yes |
| P37 · 5 local years | Training-only inflation | Ridge | 80% | 462 | 66.0% [45.2%, 84.9%] | 23.77 | 0 | 0 | Yes |
| P37 · 5 local years | Weather-regime Mondrian | Ridge | 80% | 462 | 70.6% [50.7%, 88.2%] | Unbounded | 8 | 0 | Yes |
| P37 · 5 local years | Climate-similarity weighting | Ridge | 80% | 462 | 74.9% [56.1%, 91.6%] | Unbounded | 80 | 0 | Yes |
| P37 · 5 local years | P33 reference | Ridge | 90% | 462 | 70.6% [48.4%, 90.0%] | Unbounded | 1 | 0 | Yes |
| P37 · 5 local years | Leave-one-year-out | Ridge | 90% | 462 | 70.6% [48.4%, 90.0%] | Unbounded | 1 | 0 | Yes |
| P37 · 5 local years | Training-only inflation | Ridge | 90% | 462 | 73.4% [52.2%, 91.9%] | Unbounded | 1 | 0 | Yes |
| P37 · 5 local years | Weather-regime Mondrian | Ridge | 90% | 462 | 77.7% [55.9%, 94.7%] | Unbounded | 78 | 0 | Yes |
| P37 · 5 local years | Climate-similarity weighting | Ridge | 90% | 462 | 81.6% [60.5%, 98.8%] | Unbounded | 138 | 0 | Yes |
| P37 · 5 local years | P33 reference | Forest | 80% | 462 | 51.7% [33.6%, 66.0%] | 17.40 | 0 | 0 | Yes |
| P37 · 5 local years | Leave-one-year-out | Forest | 80% | 462 | 51.7% [33.6%, 66.0%] | 17.40 | 0 | 0 | Yes |
| P37 · 5 local years | Training-only inflation | Forest | 80% | 462 | 51.9% [33.7%, 66.3%] | 17.41 | 0 | 0 | Yes |
| P37 · 5 local years | Weather-regime Mondrian | Forest | 80% | 462 | 54.3% [37.0%, 67.2%] | Unbounded | 8 | 0 | Yes |
| P37 · 5 local years | Climate-similarity weighting | Forest | 80% | 462 | 66.7% [47.8%, 82.3%] | Unbounded | 80 | 0 | Yes |
| P37 · 5 local years | P33 reference | Forest | 90% | 462 | 61.7% [40.6%, 78.8%] | Unbounded | 1 | 0 | Yes |
| P37 · 5 local years | Leave-one-year-out | Forest | 90% | 462 | 61.7% [40.6%, 78.8%] | Unbounded | 1 | 0 | Yes |
| P37 · 5 local years | Training-only inflation | Forest | 90% | 462 | 61.7% [40.6%, 78.8%] | Unbounded | 1 | 0 | Yes |
| P37 · 5 local years | Weather-regime Mondrian | Forest | 90% | 462 | 69.7% [49.3%, 85.7%] | Unbounded | 78 | 0 | Yes |
| P37 · 5 local years | Climate-similarity weighting | Forest | 90% | 462 | 77.7% [56.2%, 95.7%] | Unbounded | 138 | 0 | Yes |
| P37 · 8 local years | P33 reference | Ridge | 80% | 462 | 59.7% [40.6%, 75.7%] | 20.52 | 0 | 0 | Yes |
| P37 · 8 local years | Leave-one-year-out | Ridge | 80% | 462 | 59.7% [40.6%, 75.7%] | 20.52 | 0 | 0 | Yes |
| P37 · 8 local years | Training-only inflation | Ridge | 80% | 462 | 63.6% [43.3%, 81.2%] | 22.25 | 0 | 0 | Yes |
| P37 · 8 local years | Weather-regime Mondrian | Ridge | 80% | 462 | 68.4% [50.4%, 83.0%] | Unbounded | 8 | 0 | Yes |
| P37 · 8 local years | Climate-similarity weighting | Ridge | 80% | 462 | 72.1% [54.8%, 86.9%] | Unbounded | 71 | 0 | Yes |
| P37 · 8 local years | P33 reference | Ridge | 90% | 462 | 69.3% [48.5%, 88.5%] | Unbounded | 1 | 0 | Yes |
| P37 · 8 local years | Leave-one-year-out | Ridge | 90% | 462 | 69.3% [48.5%, 88.5%] | Unbounded | 1 | 0 | Yes |
| P37 · 8 local years | Training-only inflation | Ridge | 90% | 462 | 71.6% [51.9%, 90.2%] | Unbounded | 1 | 0 | Yes |
| P37 · 8 local years | Weather-regime Mondrian | Ridge | 90% | 462 | 77.1% [55.5%, 93.6%] | Unbounded | 63 | 0 | Yes |
| P37 · 8 local years | Climate-similarity weighting | Ridge | 90% | 462 | 79.2% [59.5%, 96.1%] | Unbounded | 101 | 0 | Yes |
| P37 · 8 local years | P33 reference | Forest | 80% | 462 | 51.7% [35.4%, 65.1%] | 17.10 | 0 | 0 | Yes |
| P37 · 8 local years | Leave-one-year-out | Forest | 80% | 462 | 51.7% [35.4%, 65.1%] | 17.10 | 0 | 0 | Yes |
| P37 · 8 local years | Training-only inflation | Forest | 80% | 462 | 51.7% [35.4%, 65.1%] | 17.11 | 0 | 0 | Yes |
| P37 · 8 local years | Weather-regime Mondrian | Forest | 80% | 462 | 54.8% [39.0%, 67.9%] | Unbounded | 8 | 0 | Yes |
| P37 · 8 local years | Climate-similarity weighting | Forest | 80% | 462 | 66.0% [49.0%, 81.7%] | Unbounded | 71 | 0 | Yes |
| P37 · 8 local years | P33 reference | Forest | 90% | 462 | 60.2% [40.5%, 75.0%] | Unbounded | 1 | 0 | Yes |
| P37 · 8 local years | Leave-one-year-out | Forest | 90% | 462 | 60.2% [40.5%, 75.0%] | Unbounded | 1 | 0 | Yes |
| P37 · 8 local years | Training-only inflation | Forest | 90% | 462 | 60.2% [40.5%, 75.0%] | Unbounded | 1 | 0 | Yes |
| P37 · 8 local years | Weather-regime Mondrian | Forest | 90% | 462 | 69.7% [48.1%, 86.0%] | Unbounded | 63 | 0 | Yes |
| P37 · 8 local years | Climate-similarity weighting | Forest | 90% | 462 | 77.1% [57.4%, 94.1%] | Unbounded | 101 | 0 | Yes |
| P37 · 12 local years | P33 reference | Ridge | 80% | 462 | 62.6% [44.9%, 78.5%] | 22.16 | 0 | 0 | Yes |
| P37 · 12 local years | Leave-one-year-out | Ridge | 80% | 462 | 62.6% [44.9%, 78.5%] | 22.16 | 0 | 0 | Yes |
| P37 · 12 local years | Training-only inflation | Ridge | 80% | 462 | 66.7% [49.4%, 82.2%] | 24.03 | 0 | 0 | Yes |
| P37 · 12 local years | Weather-regime Mondrian | Ridge | 80% | 462 | 68.0% [55.5%, 81.0%] | Unbounded | 8 | 0 | Yes |
| P37 · 12 local years | Climate-similarity weighting | Ridge | 80% | 462 | 68.4% [50.2%, 87.1%] | Unbounded | 8 | 0 | Yes |
| P37 · 12 local years | P33 reference | Ridge | 90% | 462 | 75.1% [62.2%, 89.1%] | 28.44 | 0 | 0 | Yes |
| P37 · 12 local years | Leave-one-year-out | Ridge | 90% | 462 | 75.1% [62.2%, 89.1%] | 28.44 | 0 | 0 | Yes |
| P37 · 12 local years | Training-only inflation | Ridge | 90% | 462 | 79.4% [70.1%, 91.6%] | 30.84 | 0 | 0 | Yes |
| P37 · 12 local years | Weather-regime Mondrian | Ridge | 90% | 462 | 77.3% [65.7%, 89.3%] | Unbounded | 8 | 0 | Yes |
| P37 · 12 local years | Climate-similarity weighting | Ridge | 90% | 462 | 80.1% [66.6%, 92.9%] | Unbounded | 63 | 0 | Yes |
| P37 · 12 local years | P33 reference | Forest | 80% | 462 | 55.4% [41.2%, 68.3%] | 19.33 | 0 | 0 | Yes |
| P37 · 12 local years | Leave-one-year-out | Forest | 80% | 462 | 55.4% [41.2%, 68.3%] | 19.33 | 0 | 0 | Yes |
| P37 · 12 local years | Training-only inflation | Forest | 80% | 462 | 55.4% [41.2%, 68.3%] | 19.34 | 0 | 0 | Yes |
| P37 · 12 local years | Weather-regime Mondrian | Forest | 80% | 462 | 58.7% [48.8%, 68.2%] | Unbounded | 8 | 0 | Yes |
| P37 · 12 local years | Climate-similarity weighting | Forest | 80% | 462 | 59.7% [43.7%, 76.5%] | Unbounded | 8 | 0 | Yes |
| P37 · 12 local years | P33 reference | Forest | 90% | 462 | 66.7% [55.5%, 76.8%] | 24.77 | 0 | 0 | Yes |
| P37 · 12 local years | Leave-one-year-out | Forest | 90% | 462 | 66.7% [55.5%, 76.8%] | 24.77 | 0 | 0 | Yes |
| P37 · 12 local years | Training-only inflation | Forest | 90% | 462 | 66.7% [55.5%, 76.8%] | 24.78 | 0 | 0 | Yes |
| P37 · 12 local years | Weather-regime Mondrian | Forest | 90% | 462 | 69.9% [62.9%, 77.8%] | Unbounded | 8 | 0 | Yes |
| P37 · 12 local years | Climate-similarity weighting | Forest | 90% | 462 | 80.1% [67.2%, 93.0%] | Unbounded | 63 | 0 | Yes |

##### Oklahoma

| Evaluation | Method | Learner | Nominal | n | Coverage [95% interval] | Mean width | Unbounded | Unavailable | Below nominal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P32 spatial transfer | P33 reference | Ridge | 80% | 1,800 | 76.3% [66.2%, 83.6%] | 26.71 | 0 | 0 | Yes |
| P32 spatial transfer | Leave-one-year-out | Ridge | 80% | 1,800 | 76.3% [66.2%, 83.6%] | 26.71 | 0 | 0 | Yes |
| P32 spatial transfer | Training-only inflation | Ridge | 80% | 1,800 | 82.0% [73.0%, 88.8%] | 29.45 | 0 | 0 | — |
| P32 spatial transfer | Weather-regime Mondrian | Ridge | 80% | 1,800 | 58.9% [46.3%, 67.9%] | 19.55 | 0 | 0 | Yes |
| P32 spatial transfer | Climate-similarity weighting | Ridge | 80% | 1,800 | 83.6% [77.5%, 88.6%] | Unbounded | 523 | 0 | — |
| P32 spatial transfer | P33 reference | Ridge | 90% | 1,800 | 86.1% [78.8%, 91.5%] | 32.72 | 0 | 0 | Yes |
| P32 spatial transfer | Leave-one-year-out | Ridge | 90% | 1,800 | 86.1% [78.8%, 91.5%] | 32.72 | 0 | 0 | Yes |
| P32 spatial transfer | Training-only inflation | Ridge | 90% | 1,800 | 90.4% [85.2%, 94.3%] | 36.07 | 0 | 0 | — |
| P32 spatial transfer | Weather-regime Mondrian | Ridge | 90% | 1,800 | 79.1% [68.7%, 86.7%] | 28.10 | 0 | 0 | Yes |
| P32 spatial transfer | Climate-similarity weighting | Ridge | 90% | 1,800 | 92.7% [89.1%, 95.6%] | Unbounded | 523 | 0 | — |
| P32 spatial transfer | P33 reference | Forest | 80% | 1,800 | 65.4% [53.9%, 74.0%] | 24.84 | 0 | 0 | Yes |
| P32 spatial transfer | Leave-one-year-out | Forest | 80% | 1,800 | 65.4% [53.9%, 74.0%] | 24.84 | 0 | 0 | Yes |
| P32 spatial transfer | Training-only inflation | Forest | 80% | 1,800 | 77.5% [67.3%, 85.0%] | 29.96 | 0 | 0 | Yes |
| P32 spatial transfer | Weather-regime Mondrian | Forest | 80% | 1,800 | 50.7% [37.5%, 60.7%] | 19.11 | 0 | 0 | Yes |
| P32 spatial transfer | Climate-similarity weighting | Forest | 80% | 1,800 | 77.3% [68.1%, 84.0%] | Unbounded | 523 | 0 | Yes |
| P32 spatial transfer | P33 reference | Forest | 90% | 1,800 | 83.9% [75.0%, 90.0%] | 33.28 | 0 | 0 | Yes |
| P32 spatial transfer | Leave-one-year-out | Forest | 90% | 1,800 | 83.9% [75.0%, 90.0%] | 33.28 | 0 | 0 | Yes |
| P32 spatial transfer | Training-only inflation | Forest | 90% | 1,800 | 92.1% [86.4%, 95.7%] | 40.14 | 0 | 0 | — |
| P32 spatial transfer | Weather-regime Mondrian | Forest | 90% | 1,800 | 60.8% [47.1%, 71.2%] | 23.77 | 0 | 0 | Yes |
| P32 spatial transfer | Climate-similarity weighting | Forest | 90% | 1,800 | 90.2% [84.7%, 94.1%] | Unbounded | 523 | 0 | — |
| P37 · 0 local years | P33 reference | Ridge | 80% | 88 | 14.8% [3.7%, 45.5%] | 18.49 | 0 | 0 | Yes |
| P37 · 0 local years | Leave-one-year-out | Ridge | 80% | 88 | 14.8% [3.7%, 45.5%] | 18.49 | 0 | 0 | Yes |
| P37 · 0 local years | Training-only inflation | Ridge | 80% | 88 | 15.9% [3.9%, 45.5%] | 20.27 | 0 | 0 | Yes |
| P37 · 0 local years | Weather-regime Mondrian | Ridge | 80% | 88 | 14.8% [3.7%, 45.5%] | 18.55 | 0 | 0 | Yes |
| P37 · 0 local years | Climate-similarity weighting | Ridge | 80% | 88 | 71.6% [55.6%, 87.2%] | Unbounded | 55 | 0 | Yes |
| P37 · 0 local years | P33 reference | Ridge | 90% | 88 | 20.5% [7.8%, 46.3%] | 23.36 | 0 | 0 | Yes |
| P37 · 0 local years | Leave-one-year-out | Ridge | 90% | 88 | 20.5% [7.8%, 46.3%] | 23.36 | 0 | 0 | Yes |
| P37 · 0 local years | Training-only inflation | Ridge | 90% | 88 | 20.5% [7.8%, 46.3%] | 25.65 | 0 | 0 | Yes |
| P37 · 0 local years | Weather-regime Mondrian | Ridge | 90% | 88 | 20.5% [7.8%, 46.3%] | 23.38 | 0 | 0 | Yes |
| P37 · 0 local years | Climate-similarity weighting | Ridge | 90% | 88 | 79.5% [58.6%, 97.7%] | Unbounded | 60 | 0 | Yes |
| P37 · 0 local years | P33 reference | Forest | 80% | 88 | 6.8% [0.8%, 26.1%] | 19.03 | 0 | 0 | Yes |
| P37 · 0 local years | Leave-one-year-out | Forest | 80% | 88 | 6.8% [0.8%, 26.1%] | 19.03 | 0 | 0 | Yes |
| P37 · 0 local years | Training-only inflation | Forest | 80% | 88 | 6.8% [0.8%, 26.1%] | 19.11 | 0 | 0 | Yes |
| P37 · 0 local years | Weather-regime Mondrian | Forest | 80% | 88 | 6.8% [0.8%, 26.1%] | 18.95 | 0 | 0 | Yes |
| P37 · 0 local years | Climate-similarity weighting | Forest | 80% | 88 | 68.2% [53.8%, 81.6%] | Unbounded | 55 | 0 | Yes |
| P37 · 0 local years | P33 reference | Forest | 90% | 88 | 9.1% [3.7%, 30.4%] | 25.50 | 0 | 0 | Yes |
| P37 · 0 local years | Leave-one-year-out | Forest | 90% | 88 | 9.1% [3.7%, 30.4%] | 25.50 | 0 | 0 | Yes |
| P37 · 0 local years | Training-only inflation | Forest | 90% | 88 | 9.1% [3.7%, 30.4%] | 25.61 | 0 | 0 | Yes |
| P37 · 0 local years | Weather-regime Mondrian | Forest | 90% | 88 | 9.1% [3.7%, 30.4%] | 23.65 | 0 | 0 | Yes |
| P37 · 0 local years | Climate-similarity weighting | Forest | 90% | 88 | 77.3% [55.6%, 97.3%] | Unbounded | 60 | 0 | Yes |
| P37 · 3 local years | P33 reference | Ridge | 80% | 88 | 22.7% [12.6%, 50.0%] | 24.60 | 0 | 0 | Yes |
| P37 · 3 local years | Leave-one-year-out | Ridge | 80% | 88 | 22.7% [12.6%, 50.0%] | 24.60 | 0 | 0 | Yes |
| P37 · 3 local years | Training-only inflation | Ridge | 80% | 88 | 23.9% [13.3%, 50.0%] | 26.82 | 0 | 0 | Yes |
| P37 · 3 local years | Weather-regime Mondrian | Ridge | 80% | 88 | 22.7% [12.6%, 50.0%] | 25.05 | 0 | 0 | Yes |
| P37 · 3 local years | Climate-similarity weighting | Ridge | 80% | 88 | 68.2% [56.1%, 83.4%] | Unbounded | 40 | 0 | Yes |
| P37 · 3 local years | P33 reference | Ridge | 90% | 88 | 33.0% [22.2%, 55.7%] | 29.63 | 0 | 0 | Yes |
| P37 · 3 local years | Leave-one-year-out | Ridge | 90% | 88 | 33.0% [22.2%, 55.7%] | 29.63 | 0 | 0 | Yes |
| P37 · 3 local years | Training-only inflation | Ridge | 90% | 88 | 38.6% [28.9%, 60.1%] | 32.33 | 0 | 0 | Yes |
| P37 · 3 local years | Weather-regime Mondrian | Ridge | 90% | 88 | 33.0% [22.2%, 55.7%] | 30.09 | 0 | 0 | Yes |
| P37 · 3 local years | Climate-similarity weighting | Ridge | 90% | 88 | 100.0% [100.0%, 100.0%] | Unbounded | 88 | 0 | — |
| P37 · 3 local years | P33 reference | Forest | 80% | 88 | 11.4% [4.8%, 30.4%] | 25.61 | 0 | 0 | Yes |
| P37 · 3 local years | Leave-one-year-out | Forest | 80% | 88 | 11.4% [4.8%, 30.4%] | 25.61 | 0 | 0 | Yes |
| P37 · 3 local years | Training-only inflation | Forest | 80% | 88 | 11.4% [4.8%, 30.4%] | 25.72 | 0 | 0 | Yes |
| P37 · 3 local years | Weather-regime Mondrian | Forest | 80% | 88 | 11.4% [4.8%, 30.4%] | 26.23 | 0 | 0 | Yes |
| P37 · 3 local years | Climate-similarity weighting | Forest | 80% | 88 | 59.1% [51.9%, 72.5%] | Unbounded | 40 | 0 | Yes |
| P37 · 3 local years | P33 reference | Forest | 90% | 88 | 23.9% [11.1%, 46.2%] | 31.90 | 0 | 0 | Yes |
| P37 · 3 local years | Leave-one-year-out | Forest | 90% | 88 | 23.9% [11.1%, 46.2%] | 31.90 | 0 | 0 | Yes |
| P37 · 3 local years | Training-only inflation | Forest | 90% | 88 | 23.9% [11.1%, 46.2%] | 32.03 | 0 | 0 | Yes |
| P37 · 3 local years | Weather-regime Mondrian | Forest | 90% | 88 | 25.0% [12.4%, 48.7%] | 32.55 | 0 | 0 | Yes |
| P37 · 3 local years | Climate-similarity weighting | Forest | 90% | 88 | 100.0% [100.0%, 100.0%] | Unbounded | 88 | 0 | — |
| P37 · 5 local years | P33 reference | Ridge | 80% | 88 | 28.4% [20.0%, 54.6%] | 26.89 | 0 | 0 | Yes |
| P37 · 5 local years | Leave-one-year-out | Ridge | 80% | 88 | 28.4% [20.0%, 54.6%] | 26.89 | 0 | 0 | Yes |
| P37 · 5 local years | Training-only inflation | Ridge | 80% | 88 | 31.8% [21.1%, 54.7%] | 29.31 | 0 | 0 | Yes |
| P37 · 5 local years | Weather-regime Mondrian | Ridge | 80% | 88 | 28.4% [20.0%, 54.6%] | 26.89 | 0 | 0 | Yes |
| P37 · 5 local years | Climate-similarity weighting | Ridge | 80% | 88 | 65.9% [55.7%, 87.2%] | Unbounded | 35 | 0 | Yes |
| P37 · 5 local years | P33 reference | Ridge | 90% | 88 | 36.4% [28.3%, 60.1%] | 30.75 | 0 | 0 | Yes |
| P37 · 5 local years | Leave-one-year-out | Ridge | 90% | 88 | 36.4% [28.3%, 60.1%] | 30.75 | 0 | 0 | Yes |
| P37 · 5 local years | Training-only inflation | Ridge | 90% | 88 | 45.5% [35.7%, 62.5%] | 33.54 | 0 | 0 | Yes |
| P37 · 5 local years | Weather-regime Mondrian | Ridge | 90% | 88 | 36.4% [28.3%, 60.1%] | 31.20 | 0 | 0 | Yes |
| P37 · 5 local years | Climate-similarity weighting | Ridge | 90% | 88 | 93.2% [89.1%, 100.0%] | Unbounded | 65 | 0 | — |
| P37 · 5 local years | P33 reference | Forest | 80% | 88 | 20.5% [9.1%, 35.9%] | 28.84 | 0 | 0 | Yes |
| P37 · 5 local years | Leave-one-year-out | Forest | 80% | 88 | 20.5% [9.1%, 35.9%] | 28.84 | 0 | 0 | Yes |
| P37 · 5 local years | Training-only inflation | Forest | 80% | 88 | 20.5% [9.1%, 35.9%] | 28.94 | 0 | 0 | Yes |
| P37 · 5 local years | Weather-regime Mondrian | Forest | 80% | 88 | 20.5% [9.1%, 35.9%] | 28.82 | 0 | 0 | Yes |
| P37 · 5 local years | Climate-similarity weighting | Forest | 80% | 88 | 59.1% [49.1%, 72.5%] | Unbounded | 35 | 0 | Yes |
| P37 · 5 local years | P33 reference | Forest | 90% | 88 | 33.0% [17.8%, 50.0%] | 35.45 | 0 | 0 | Yes |
| P37 · 5 local years | Leave-one-year-out | Forest | 90% | 88 | 33.0% [17.8%, 50.0%] | 35.45 | 0 | 0 | Yes |
| P37 · 5 local years | Training-only inflation | Forest | 90% | 88 | 33.0% [17.8%, 50.0%] | 35.58 | 0 | 0 | Yes |
| P37 · 5 local years | Weather-regime Mondrian | Forest | 90% | 88 | 34.1% [20.4%, 50.6%] | 36.10 | 0 | 0 | Yes |
| P37 · 5 local years | Climate-similarity weighting | Forest | 90% | 88 | 85.2% [70.8%, 100.0%] | Unbounded | 65 | 0 | Yes |
| P37 · 8 local years | P33 reference | Ridge | 80% | 88 | 44.3% [34.7%, 62.5%] | 32.87 | 0 | 0 | Yes |
| P37 · 8 local years | Leave-one-year-out | Ridge | 80% | 88 | 44.3% [34.7%, 62.5%] | 32.87 | 0 | 0 | Yes |
| P37 · 8 local years | Training-only inflation | Ridge | 80% | 88 | 52.3% [39.7%, 66.7%] | 35.83 | 0 | 0 | Yes |
| P37 · 8 local years | Weather-regime Mondrian | Ridge | 80% | 88 | 44.3% [34.7%, 62.5%] | 33.16 | 0 | 0 | Yes |
| P37 · 8 local years | Climate-similarity weighting | Ridge | 80% | 88 | 72.7% [62.3%, 87.2%] | Unbounded | 34 | 0 | Yes |
| P37 · 8 local years | P33 reference | Ridge | 90% | 88 | 56.8% [46.3%, 69.2%] | 37.19 | 0 | 0 | Yes |
| P37 · 8 local years | Leave-one-year-out | Ridge | 90% | 88 | 56.8% [46.3%, 69.2%] | 37.19 | 0 | 0 | Yes |
| P37 · 8 local years | Training-only inflation | Ridge | 90% | 88 | 65.9% [53.0%, 77.8%] | 40.55 | 0 | 0 | Yes |
| P37 · 8 local years | Weather-regime Mondrian | Ridge | 90% | 88 | 59.1% [53.1%, 72.7%] | 37.56 | 0 | 0 | Yes |
| P37 · 8 local years | Climate-similarity weighting | Ridge | 90% | 88 | 90.9% [88.4%, 97.5%] | Unbounded | 47 | 0 | — |
| P37 · 8 local years | P33 reference | Forest | 80% | 88 | 27.3% [17.8%, 38.7%] | 33.74 | 0 | 0 | Yes |
| P37 · 8 local years | Leave-one-year-out | Forest | 80% | 88 | 27.3% [17.8%, 38.7%] | 33.74 | 0 | 0 | Yes |
| P37 · 8 local years | Training-only inflation | Forest | 80% | 88 | 27.3% [17.8%, 38.7%] | 33.84 | 0 | 0 | Yes |
| P37 · 8 local years | Weather-regime Mondrian | Forest | 80% | 88 | 27.3% [17.8%, 38.7%] | 33.95 | 0 | 0 | Yes |
| P37 · 8 local years | Climate-similarity weighting | Forest | 80% | 88 | 65.9% [56.6%, 75.9%] | Unbounded | 34 | 0 | Yes |
| P37 · 8 local years | P33 reference | Forest | 90% | 88 | 48.9% [41.5%, 53.2%] | 38.73 | 0 | 0 | Yes |
| P37 · 8 local years | Leave-one-year-out | Forest | 90% | 88 | 48.9% [41.5%, 53.2%] | 38.73 | 0 | 0 | Yes |
| P37 · 8 local years | Training-only inflation | Forest | 90% | 88 | 50.0% [41.5%, 58.7%] | 38.84 | 0 | 0 | Yes |
| P37 · 8 local years | Weather-regime Mondrian | Forest | 90% | 88 | 48.9% [41.5%, 53.2%] | 38.80 | 0 | 0 | Yes |
| P37 · 8 local years | Climate-similarity weighting | Forest | 90% | 88 | 79.5% [69.8%, 97.5%] | Unbounded | 47 | 0 | Yes |
| P37 · 12 local years | P33 reference | Ridge | 80% | 88 | 43.2% [30.8%, 62.5%] | 31.53 | 0 | 0 | Yes |
| P37 · 12 local years | Leave-one-year-out | Ridge | 80% | 88 | 43.2% [30.8%, 62.5%] | 31.53 | 0 | 0 | Yes |
| P37 · 12 local years | Training-only inflation | Ridge | 80% | 88 | 47.7% [35.7%, 64.3%] | 34.39 | 0 | 0 | Yes |
| P37 · 12 local years | Weather-regime Mondrian | Ridge | 80% | 88 | 43.2% [30.8%, 62.5%] | 31.58 | 0 | 0 | Yes |
| P37 · 12 local years | Climate-similarity weighting | Ridge | 80% | 88 | 70.5% [64.0%, 83.3%] | Unbounded | 26 | 0 | Yes |
| P37 · 12 local years | P33 reference | Ridge | 90% | 88 | 56.8% [43.9%, 67.9%] | 37.04 | 0 | 0 | Yes |
| P37 · 12 local years | Leave-one-year-out | Ridge | 90% | 88 | 56.8% [43.9%, 67.9%] | 37.04 | 0 | 0 | Yes |
| P37 · 12 local years | Training-only inflation | Ridge | 90% | 88 | 67.0% [54.2%, 77.8%] | 40.40 | 0 | 0 | Yes |
| P37 · 12 local years | Weather-regime Mondrian | Ridge | 90% | 88 | 58.0% [47.6%, 69.6%] | 37.17 | 0 | 0 | Yes |
| P37 · 12 local years | Climate-similarity weighting | Ridge | 90% | 88 | 85.2% [81.6%, 93.6%] | Unbounded | 45 | 0 | Yes |
| P37 · 12 local years | P33 reference | Forest | 80% | 88 | 28.4% [17.8%, 46.2%] | 33.50 | 0 | 0 | Yes |
| P37 · 12 local years | Leave-one-year-out | Forest | 80% | 88 | 28.4% [17.8%, 46.2%] | 33.50 | 0 | 0 | Yes |
| P37 · 12 local years | Training-only inflation | Forest | 80% | 88 | 28.4% [17.8%, 46.2%] | 33.62 | 0 | 0 | Yes |
| P37 · 12 local years | Weather-regime Mondrian | Forest | 80% | 88 | 28.4% [17.8%, 46.2%] | 33.65 | 0 | 0 | Yes |
| P37 · 12 local years | Climate-similarity weighting | Forest | 80% | 88 | 56.8% [50.9%, 68.5%] | Unbounded | 26 | 0 | Yes |
| P37 · 12 local years | P33 reference | Forest | 90% | 88 | 43.2% [33.3%, 62.5%] | 38.00 | 0 | 0 | Yes |
| P37 · 12 local years | Leave-one-year-out | Forest | 90% | 88 | 43.2% [33.3%, 62.5%] | 38.00 | 0 | 0 | Yes |
| P37 · 12 local years | Training-only inflation | Forest | 90% | 88 | 43.2% [33.3%, 62.5%] | 38.15 | 0 | 0 | Yes |
| P37 · 12 local years | Weather-regime Mondrian | Forest | 90% | 88 | 44.3% [35.6%, 63.7%] | 38.33 | 0 | 0 | Yes |
| P37 · 12 local years | Climate-similarity weighting | Forest | 90% | 88 | 78.4% [69.2%, 93.6%] | Unbounded | 45 | 0 | Yes |

### Failures and interpretation

Across all evaluations, 6,704 intervals were unbounded and none were unavailable. The reference, leave-one-year-out scores and inflation each had 8 unbounded intervals. Mondrian had 656, and climate-similarity weighting had 6,024.

- **Kansas.** Training-only inflation lifted pooled harvest-year coverage at both levels for both learners. At nominal 90%, ridge rose from 88.3% to 92.3% and forest from 85.8% to 90.9%, with widths of 34.27 and 32.53 bu/acre. At 90%, no method exceeded 49.5% coverage in 2007. The 2007 80% results were 31.1–38.8%. Under district holdout, weighting reached both nominal levels but returned 340 unbounded intervals per learner at 90%. Mondrian conditioning undercovered both learners at 90% on both Kansas splits.

- **Direct P32 transfer.** Inflation reached 90% empirical coverage for both Oklahoma learners (90.4% ridge, 92.1% forest) and for Nebraska forest (92.8%). Nebraska ridge reached 88.5%. The weighted Oklahoma 90% intervals included 523 unbounded intervals per learner. The Oklahoma forest Mondrian 90% interval covered 60.8%.

- **P37 common test.** No finite-width pooled result reached nominal coverage. The weighted Oklahoma results that reached nominal 90% did so with unbounded intervals. At three years both learners reached 100% with all 88 intervals unbounded per learner. At five and eight years, ridge reached 93.2% and 90.9%, with 65 and 47 of 88 intervals unbounded. At 12 years, Oklahoma's largest finite-width 90% coverage was 67.0% for inflated ridge and 44.3% for Mondrian forest. Nebraska's corresponding values were 79.4% for inflated ridge and 66.7% for the reference and inflation forest. Nebraska Mondrian and weighted intervals could cover more rows with an unbounded mean width.

### Exploratory 2007 freeze check

The county POWER archives contain precipitation, daily maximum temperature, mean temperature and radiation. Zero of the 103 held-out Kansas counties had a complete cached March–May daily minimum series. The exploratory single-case test could not be run. Whether a spring freeze explains the residuals remains unknown.

### Limits and reproduction

Nominal interval guarantees apply only in-region and under exchangeability. A shared region alone does not establish exchangeability. Training-domain inflation, regime stratification and weather similarity are fixed sensitivity analyses. Weather-similarity weights are not known sampling likelihood ratios. County-average associations do not validate rotation recommendations. The local workflow also requires district yield history.

Run `python -m src.interval_diagnosis` offline. The [summary and fold audit](../data/processed/climate_yield_interval_diagnosis.json) and [county-year method results](../data/processed/climate_yield_interval_diagnosis_rows.csv.gz) are separate from P33. A row can be joined to P33 on protocol, state, fold, k, model, level, FIPS and year. The original center plus or minus the P33b radius gives its endpoints. The county-year file distinguishes unavailable radii from infinite ones.

## P38 Kansas-to-Oklahoma transfer diagnosis

The [plan](p38_plan.md) was preregistered in commit `f8d9a99`. The diagnosis uses 3,215 Kansas training rows, 1,800 Oklahoma test rows and the frozen P32 Kansas ridge and random forest predictions. The Oklahoma district-held-out trend and county mean are the original saved P32 baselines. All comparisons use matching county-years. No models or thresholds were fitted to these test outcomes. Interpret explanations as hypotheses.

### Weather distributions and marginal overlap

The five P25 features come from the same fixed winter-wheat feature recipe and cached county-centroid NASA POWER series. Each entry gives minimum, 5th percentile, median, 95th percentile and maximum in feature units.

| Feature | Kansas distribution | Oklahoma distribution |
| --- | --- | --- |
| Season rainfall (mm) | 95.860 / 201.064 / 449.140 / 823.800 / 1146.230 | 73.170 / 267.991 / 583.790 / 974.492 / 1292.860 |
| Modeled water deficit (mm) | 3.341 / 60.261 / 218.221 / 381.411 / 454.140 | 0.523 / 22.767 / 138.174 / 324.003 / 476.830 |
| Heat days | 0.000 / 1.000 / 14.000 / 35.000 / 48.000 | 0.000 / 3.000 / 21.000 / 44.000 / 63.000 |
| Mean daily solar radiation (MJ/m²/day) | 11.378 / 12.739 / 14.268 / 15.949 / 16.885 | 11.727 / 13.350 / 14.878 / 16.735 / 18.006 |
| Mean air temperature (°C) | 4.597 / 6.174 / 8.328 / 10.516 / 12.005 | 8.013 / 9.216 / 11.137 / 13.495 / 15.559 |

| Feature | Below / above full Kansas range | Outside full range | Below / above Kansas 5th–95th | Outside central band |
| --- | --- | --- | --- | --- |
| Season rainfall (mm) | 1 / 5 | 6 (0.3%) | 31 / 257 | 288 (16.0%) |
| Modeled water deficit (mm) | 2 / 1 | 3 (0.2%) | 302 / 37 | 339 (18.8%) |
| Heat days | 0 / 39 | 39 (2.2%) | 32 / 309 | 341 (18.9%) |
| Mean daily solar radiation (MJ/m²/day) | 0 / 74 | 74 (4.1%) | 30 / 318 | 348 (19.3%) |
| Mean air temperature (°C) | 0 / 469 | 469 (26.1%) | 0 / 1,219 | 1,219 (67.7%) |
| Any feature, unique rows | — | 510 (28.3%) | — | 1,439 (79.9%) |

Mean temperature was outside the full Kansas range for 469 Oklahoma rows (26.1%), all above its maximum. It was above the Kansas 95th percentile for 67.7%. Across all five marginal bands, 361 Oklahoma rows (20.1%) passed. The same bands retain 2,307 of 3,215 Kansas training rows (71.8%). This is an axis-aligned screen, so passing does not establish that a feature combination was common in Kansas.

### Restricting to the overlap subset

| Oklahoma subset | County-years | Counties / districts | Kansas ridge | Kansas forest | Oklahoma trend | Oklahoma county mean |
| --- | --- | --- | --- | --- | --- | --- |
| All Oklahoma | 1,800 | 58 / 8 | 12.096 | 13.225 | 8.985 | 9.200 |
| Inside every central band | 361 | 42 / 7 | 10.981 | 12.840 | 8.572 | 8.585 |
| Outside at least one central band | 1,439 | 58 / 8 | 12.360 | 13.320 | 9.085 | 9.348 |

RMSE and paired differences are in bu/acre. Positive differences favor the Oklahoma baseline. Brackets show descriptive 95% percentile intervals from 1,000 paired bootstrap draws of whole USDA reporting districts.

| Oklahoma subset | Learner | Δ vs Oklahoma trend | Δ vs Oklahoma county mean |
| --- | --- | --- | --- |
| All Oklahoma | Kansas ridge | +3.111 [+1.535, +4.930] | +2.896 [+1.141, +5.014] |
| All Oklahoma | Kansas forest | +4.240 [+2.227, +6.132] | +4.025 [+1.774, +6.285] |
| Inside every central band | Kansas ridge | +2.408 [+0.779, +5.514] | +2.396 [+0.893, +5.169] |
| Inside every central band | Kansas forest | +4.268 [+1.946, +8.475] | +4.255 [+2.033, +8.060] |
| Outside at least one central band | Kansas ridge | +3.275 [+1.701, +5.035] | +3.013 [+1.038, +5.240] |
| Outside at least one central band | Kansas forest | +4.234 [+1.918, +6.224] | +3.972 [+1.432, +6.383] |

Ridge's gap to the Oklahoma trend shrank from +3.111 to +2.408 bu/acre on the overlap subset. The forest's gap changed from +4.240 to +4.268 bu/acre. Both learners still had higher RMSE than both local baselines, with intervals entirely above zero. The screen changes the rows and the baselines' RMSE too. Marginal weather differences are a plausible contributor. Removing the marginal extremes leaves a substantial transfer gap.

### Where squared error falls

The top groups below are ranked by total squared error. Neither learner meets the preregistered concentration rule of more than half the error in the top three years or top two districts.

| Learner | Grouping | Top groups | Share of rows | Share of squared error |
| --- | --- | --- | --- | --- |
| Kansas ridge | Three years | 2009, 2014, 2007 | 8.1% | 20.0% |
| Kansas ridge | Two districts | Southwest, West Central | 25.3% | 38.1% |
| Kansas forest | Three years | 2009, 2007, 2014 | 8.1% | 19.5% |
| Kansas forest | Two districts | Southwest, Central | 34.1% | 40.6% |

The highest-RMSE year for both learners was 2009, with 38 rows and RMSE of 23.173 for ridge and 26.326 for forest. The highest-RMSE districts were Panhandle for ridge (15.294) and Southwest for forest (17.057). Both learners had higher RMSE above the Kansas radiation band than inside. Ridge also had higher RMSE above the heat-days band, while the forest had lower RMSE there. The above-temperature bin accounted for 70.5% of ridge and 73.5% of forest squared error, alongside 67.7% of rows. The feature-bin patterns vary by learner and may reflect differences in county and year composition.

Positive mean error indicates overprediction. Feature bins partition all Oklahoma rows separately for each feature, so their squared-error shares should be read within that feature. Empty bins have no error estimate.

<details>
<summary>All yearly error results</summary>

| Learner | Group | County-years | Share of rows | Mean error | RMSE | Share of squared error |
| --- | --- | --- | --- | --- | --- | --- |
| Kansas ridge | 1990 | 58 | 3.2% | 1.212 | 7.324 | 1.2% |
| Kansas ridge | 1991 | 58 | 3.2% | 8.047 | 9.641 | 2.0% |
| Kansas ridge | 1992 | 58 | 3.2% | 10.328 | 12.643 | 3.5% |
| Kansas ridge | 1993 | 58 | 3.2% | 5.636 | 7.678 | 1.3% |
| Kansas ridge | 1994 | 58 | 3.2% | 9.631 | 11.506 | 2.9% |
| Kansas ridge | 1995 | 58 | 3.2% | 8.368 | 10.825 | 2.6% |
| Kansas ridge | 1996 | 58 | 3.2% | 11.729 | 12.845 | 3.6% |
| Kansas ridge | 1997 | 58 | 3.2% | 9.570 | 12.590 | 3.5% |
| Kansas ridge | 1998 | 58 | 3.2% | 4.888 | 7.261 | 1.2% |
| Kansas ridge | 1999 | 58 | 3.2% | 7.489 | 9.332 | 1.9% |
| Kansas ridge | 2000 | 58 | 3.2% | 5.834 | 7.086 | 1.1% |
| Kansas ridge | 2001 | 58 | 3.2% | 4.667 | 7.299 | 1.2% |
| Kansas ridge | 2002 | 58 | 3.2% | 10.815 | 11.765 | 3.0% |
| Kansas ridge | 2003 | 58 | 3.2% | 2.533 | 8.115 | 1.5% |
| Kansas ridge | 2004 | 57 | 3.2% | 4.642 | 8.085 | 1.4% |
| Kansas ridge | 2005 | 58 | 3.2% | 7.973 | 10.046 | 2.2% |
| Kansas ridge | 2006 | 58 | 3.2% | 9.511 | 11.441 | 2.9% |
| Kansas ridge | 2007 | 58 | 3.2% | 15.482 | 16.505 | 6.0% |
| Kansas ridge | 2008 | 40 | 2.2% | 3.874 | 7.684 | 0.9% |
| Kansas ridge | 2009 | 38 | 2.1% | 22.246 | 23.173 | 7.7% |
| Kansas ridge | 2010 | 49 | 2.7% | 10.171 | 11.909 | 2.6% |
| Kansas ridge | 2011 | 50 | 2.8% | 12.183 | 15.244 | 4.4% |
| Kansas ridge | 2012 | 53 | 2.9% | 8.949 | 11.379 | 2.6% |
| Kansas ridge | 2013 | 47 | 2.6% | 7.488 | 14.005 | 3.5% |
| Kansas ridge | 2014 | 49 | 2.7% | 16.454 | 18.401 | 6.3% |
| Kansas ridge | 2015 | 54 | 3.0% | 1.343 | 8.092 | 1.3% |
| Kansas ridge | 2016 | 52 | 2.9% | 6.931 | 13.154 | 3.4% |
| Kansas ridge | 2017 | 47 | 2.6% | 6.126 | 13.820 | 3.4% |
| Kansas ridge | 2018 | 39 | 2.2% | 6.743 | 12.845 | 2.4% |
| Kansas ridge | 2019 | 50 | 2.8% | 2.383 | 9.543 | 1.7% |
| Kansas ridge | 2020 | 43 | 2.4% | 14.335 | 16.546 | 4.5% |
| Kansas ridge | 2021 | 53 | 2.9% | 11.901 | 13.495 | 3.7% |
| Kansas ridge | 2022 | 50 | 2.8% | 8.555 | 15.899 | 4.8% |
| Kansas ridge | 2023 | 43 | 2.4% | 10.165 | 14.818 | 3.6% |
| Kansas forest | 1990 | 58 | 3.2% | 9.396 | 10.675 | 2.1% |
| Kansas forest | 1991 | 58 | 3.2% | 8.065 | 9.158 | 1.5% |
| Kansas forest | 1992 | 58 | 3.2% | 9.438 | 13.147 | 3.2% |
| Kansas forest | 1993 | 58 | 3.2% | 7.137 | 8.781 | 1.4% |
| Kansas forest | 1994 | 58 | 3.2% | 10.661 | 12.475 | 2.9% |
| Kansas forest | 1995 | 58 | 3.2% | 14.046 | 15.295 | 4.3% |
| Kansas forest | 1996 | 58 | 3.2% | 10.057 | 11.322 | 2.4% |
| Kansas forest | 1997 | 58 | 3.2% | 12.691 | 14.962 | 4.1% |
| Kansas forest | 1998 | 58 | 3.2% | 3.984 | 5.704 | 0.6% |
| Kansas forest | 1999 | 58 | 3.2% | 10.057 | 11.688 | 2.5% |
| Kansas forest | 2000 | 58 | 3.2% | 9.682 | 10.712 | 2.1% |
| Kansas forest | 2001 | 58 | 3.2% | 8.109 | 10.817 | 2.2% |
| Kansas forest | 2002 | 58 | 3.2% | 10.056 | 11.300 | 2.4% |
| Kansas forest | 2003 | 58 | 3.2% | 4.634 | 9.436 | 1.6% |
| Kansas forest | 2004 | 57 | 3.2% | 4.420 | 5.675 | 0.6% |
| Kansas forest | 2005 | 58 | 3.2% | 10.685 | 12.320 | 2.8% |
| Kansas forest | 2006 | 58 | 3.2% | 10.262 | 11.173 | 2.3% |
| Kansas forest | 2007 | 58 | 3.2% | 18.090 | 18.859 | 6.6% |
| Kansas forest | 2008 | 40 | 2.2% | 7.044 | 9.189 | 1.1% |
| Kansas forest | 2009 | 38 | 2.1% | 25.098 | 26.326 | 8.4% |
| Kansas forest | 2010 | 49 | 2.7% | 12.666 | 13.886 | 3.0% |
| Kansas forest | 2011 | 50 | 2.8% | 10.805 | 12.661 | 2.5% |
| Kansas forest | 2012 | 53 | 2.9% | 9.232 | 10.826 | 2.0% |
| Kansas forest | 2013 | 47 | 2.6% | 8.672 | 14.090 | 3.0% |
| Kansas forest | 2014 | 49 | 2.7% | 15.615 | 17.213 | 4.6% |
| Kansas forest | 2015 | 54 | 3.0% | 13.869 | 16.351 | 4.6% |
| Kansas forest | 2016 | 52 | 2.9% | 13.525 | 15.880 | 4.2% |
| Kansas forest | 2017 | 47 | 2.6% | 11.625 | 15.902 | 3.8% |
| Kansas forest | 2018 | 39 | 2.2% | 6.681 | 9.850 | 1.2% |
| Kansas forest | 2019 | 50 | 2.8% | 5.052 | 11.477 | 2.1% |
| Kansas forest | 2020 | 43 | 2.4% | 10.432 | 13.831 | 2.6% |
| Kansas forest | 2021 | 53 | 2.9% | 11.415 | 13.245 | 3.0% |
| Kansas forest | 2022 | 50 | 2.8% | 11.949 | 16.077 | 4.1% |
| Kansas forest | 2023 | 43 | 2.4% | 12.857 | 18.052 | 4.5% |

</details>

<details>
<summary>All district error results</summary>

| Learner | Group | County-years | Share of rows | Mean error | RMSE | Share of squared error |
| --- | --- | --- | --- | --- | --- | --- |
| Kansas ridge | Panhandle (10) | 154 | 8.6% | 13.651 | 15.294 | 13.7% |
| Kansas ridge | West Central (20) | 201 | 11.2% | 13.158 | 14.751 | 16.6% |
| Kansas ridge | Southwest (30) | 255 | 14.2% | 12.700 | 14.891 | 21.5% |
| Kansas ridge | North Central (40) | 264 | 14.7% | 8.054 | 10.605 | 11.3% |
| Kansas ridge | Central (50) | 358 | 19.9% | 6.897 | 9.900 | 13.3% |
| Kansas ridge | South Central (60) | 185 | 10.3% | 5.308 | 10.290 | 7.4% |
| Kansas ridge | Northeast (70) | 309 | 17.2% | 5.047 | 10.101 | 12.0% |
| Kansas ridge | East Central (80) | 74 | 4.1% | -1.983 | 12.293 | 4.2% |
| Kansas forest | Panhandle (10) | 154 | 8.6% | 12.448 | 14.226 | 9.9% |
| Kansas forest | West Central (20) | 201 | 11.2% | 13.879 | 15.390 | 15.1% |
| Kansas forest | Southwest (30) | 255 | 14.2% | 15.219 | 17.057 | 23.6% |
| Kansas forest | North Central (40) | 264 | 14.7% | 9.465 | 11.769 | 11.6% |
| Kansas forest | Central (50) | 358 | 19.9% | 9.918 | 12.253 | 17.1% |
| Kansas forest | South Central (60) | 185 | 10.3% | 10.423 | 12.837 | 9.7% |
| Kansas forest | Northeast (70) | 309 | 17.2% | 6.640 | 10.474 | 10.8% |
| Kansas forest | East Central (80) | 74 | 4.1% | 1.318 | 9.837 | 2.3% |

</details>

<details>
<summary>All per-feature error bins</summary>

| Learner | Group | County-years | Share of rows | Mean error | RMSE | Share of squared error |
| --- | --- | --- | --- | --- | --- | --- |
| Kansas ridge | Season rainfall (mm) · below | 31 | 1.7% | 15.490 | 17.211 | 3.5% |
| Kansas ridge | Season rainfall (mm) · inside | 1512 | 84.0% | 9.296 | 12.314 | 87.1% |
| Kansas ridge | Season rainfall (mm) · above | 257 | 14.3% | 1.712 | 9.846 | 9.5% |
| Kansas ridge | Modeled water deficit (mm) · below | 302 | 16.8% | 5.990 | 10.606 | 12.9% |
| Kansas ridge | Modeled water deficit (mm) · inside | 1461 | 81.2% | 8.623 | 12.233 | 83.0% |
| Kansas ridge | Modeled water deficit (mm) · above | 37 | 2.1% | 15.347 | 17.071 | 4.1% |
| Kansas ridge | Heat days · below | 32 | 1.8% | 1.894 | 5.840 | 0.4% |
| Kansas ridge | Heat days · inside | 1459 | 81.1% | 7.914 | 11.855 | 77.9% |
| Kansas ridge | Heat days · above | 309 | 17.2% | 10.900 | 13.608 | 21.7% |
| Kansas ridge | Mean daily solar radiation (MJ/m²/day) · below | 30 | 1.7% | 1.751 | 6.147 | 0.4% |
| Kansas ridge | Mean daily solar radiation (MJ/m²/day) · inside | 1452 | 80.7% | 6.985 | 10.949 | 66.1% |
| Kansas ridge | Mean daily solar radiation (MJ/m²/day) · above | 318 | 17.7% | 15.033 | 16.652 | 33.5% |
| Kansas ridge | Mean air temperature (°C) · below | 0 | 0.0% | — | — | 0.0% |
| Kansas ridge | Mean air temperature (°C) · inside | 581 | 32.3% | 8.140 | 11.563 | 29.5% |
| Kansas ridge | Mean air temperature (°C) · above | 1219 | 67.7% | 8.405 | 12.342 | 70.5% |
| Kansas forest | Season rainfall (mm) · below | 31 | 1.7% | 9.934 | 12.325 | 1.5% |
| Kansas forest | Season rainfall (mm) · inside | 1512 | 84.0% | 10.963 | 13.544 | 88.1% |
| Kansas forest | Season rainfall (mm) · above | 257 | 14.3% | 7.124 | 11.290 | 10.4% |
| Kansas forest | Modeled water deficit (mm) · below | 302 | 16.8% | 6.128 | 9.956 | 9.5% |
| Kansas forest | Modeled water deficit (mm) · inside | 1461 | 81.2% | 11.251 | 13.805 | 88.4% |
| Kansas forest | Modeled water deficit (mm) · above | 37 | 2.1% | 11.521 | 13.211 | 2.1% |
| Kansas forest | Heat days · below | 32 | 1.8% | 5.622 | 8.688 | 0.8% |
| Kansas forest | Heat days · inside | 1459 | 81.1% | 10.671 | 13.623 | 86.0% |
| Kansas forest | Heat days · above | 309 | 17.2% | 9.596 | 11.607 | 13.2% |
| Kansas forest | Mean daily solar radiation (MJ/m²/day) · below | 30 | 1.7% | 6.456 | 8.134 | 0.6% |
| Kansas forest | Mean daily solar radiation (MJ/m²/day) · inside | 1452 | 80.7% | 10.027 | 13.015 | 78.1% |
| Kansas forest | Mean daily solar radiation (MJ/m²/day) · above | 318 | 17.7% | 12.459 | 14.503 | 21.2% |
| Kansas forest | Mean air temperature (°C) · below | 0 | 0.0% | — | — | 0.0% |
| Kansas forest | Mean air temperature (°C) · inside | 581 | 32.3% | 9.047 | 11.983 | 26.5% |
| Kansas forest | Mean air temperature (°C) · above | 1219 | 67.7% | 11.041 | 13.777 | 73.5% |

</details>

### USDA NASS reporting context

| State and cohort | Reported non-irrigated | All-practice fallback |
| --- | --- | --- |
| Kansas | 2,005 (62.4%) | 1,210 (37.6%) |
| Oklahoma | 421 (23.4%) | 1,379 (76.6%) |

A different reporting mix could contribute to the transfer gap. The all-practice label does not tell us what fraction was irrigated. Cultivars, soils, management, and county-centroid weather error are other untested hypotheses. This diagnosis cannot separate them. County-average associations do not validate rotation recommendations.

Run `python -m src.transfer_diagnosis` to rebuild only the P38 [saved diagnostic](../data/processed/climate_yield_transfer_diagnosis.json).

## P39 Weather–yield associations by state

The [preregistration](p39_plan.md) was committed as `38ee005` before fitting. This analysis uses the unchanged P25/P27/P32 winter-wheat county-years and five season features from cached NASA POWER. It retains the USDA NASS all-practice fallback for county-years without reported non-irrigated yields. The [saved results](../data/processed/climate_yield_state_associations.json) include every coefficient, difference and district result. Results are illustrative and need local validation.

| State | County-years | Counties | USDA districts | Years | Reported non-irrigated rows | All-practice fallback rows | Selected alpha |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Kansas | 3,215 | 103 | 9 | 1990–2023 | 2,005 | 1,210 | 0.1 |
| Nebraska | 1,733 | 59 | 8 | 1990–2023 | 1,154 | 579 | 10 |
| Oklahoma | 1,800 | 58 | 8 | 1990–2023 | 421 | 1,379 | 10 |

### State-specific slopes

Each ridge uses yield residuals from county trends and the same five weather features. Slopes are in bu/acre per one standard deviation of that predictor **within the given state**, conditional on the other four features. Brackets show 95% percentile intervals from 1,000 whole-district resamples per state, with trends and scaling refitted and the selected alpha held fixed.

| Weather feature | Kansas | Nebraska | Oklahoma | Pairs with overlapping intervals | Common overlap across all three |
| --- | --- | --- | --- | --- | --- |
| Season rainfall (mm) | -8.985 [-10.558, -5.578] | -1.378 [-2.478, +0.448] | -3.479 [-4.205, -2.430] | Nebraska–Oklahoma | No |
| Modeled water deficit (mm) | -10.353 [-12.698, -7.174] | -3.286 [-4.338, -1.762] | -7.315 [-8.448, -5.491] | Kansas–Oklahoma | No |
| Heat days | -4.588 [-5.011, -3.618] | -2.093 [-3.035, -1.281] | -1.014 [-1.970, -0.014] | Nebraska–Oklahoma | No |
| Mean daily solar radiation (MJ/m²/day) | +4.639 [+3.187, +5.788] | +1.412 [+0.898, +1.798] | +3.444 [+2.099, +4.592] | Kansas–Oklahoma | No |
| Mean air temperature (°C) | -0.196 [-1.237, +0.569] | +0.215 [-0.400, +1.261] | -1.150 [-1.965, -0.255] | Kansas–Nebraska, Kansas–Oklahoma, Nebraska–Oklahoma | Yes |

Mean temperature was the only feature with opposite point signs across states. Nebraska's point slope was positive and Kansas's and Oklahoma's were negative. All three marginal intervals overlapped, and the Kansas and Nebraska intervals included zero. Rainfall, modeled water deficit and heat days had negative point slopes in all three states, while radiation had positive slopes. Kansas had the largest absolute slope for each of those four variables. The predictors, especially rainfall and modeled deficit, can covary. These conditional coefficients should be read with that dependence and the state-specific standard deviations in mind.

<details>
<summary>All 15 pairwise slope differences</summary>

Positive differences indicate a higher coefficient in the first-named state. The 95% intervals come from subtracting independently resampled state slopes. Ten of 15 intervals exclude zero at the unadjusted level. The other five include zero. Individual interval overlap and a paired-state contrast answer different questions.

| Weather feature | Contrast | Slope difference [95%] | Excludes zero |
| --- | --- | --- | --- |
| Season rainfall (mm) | Nebraska − Kansas | +7.607 [+4.125, +10.061] | Yes |
| Season rainfall (mm) | Oklahoma − Kansas | +5.506 [+2.161, +7.435] | Yes |
| Season rainfall (mm) | Oklahoma − Nebraska | -2.101 [-3.936, -0.554] | Yes |
| Modeled water deficit (mm) | Nebraska − Kansas | +7.068 [+3.814, +9.805] | Yes |
| Modeled water deficit (mm) | Oklahoma − Kansas | +3.039 [-0.179, +6.203] | No |
| Modeled water deficit (mm) | Oklahoma − Nebraska | -4.029 [-5.923, -1.966] | Yes |
| Heat days | Nebraska − Kansas | +2.495 [+1.094, +3.424] | Yes |
| Heat days | Oklahoma − Kansas | +3.575 [+2.261, +4.599] | Yes |
| Heat days | Oklahoma − Nebraska | +1.080 [-0.197, +2.580] | No |
| Mean daily solar radiation (MJ/m²/day) | Nebraska − Kansas | -3.227 [-4.479, -1.741] | Yes |
| Mean daily solar radiation (MJ/m²/day) | Oklahoma − Kansas | -1.195 [-2.789, +0.684] | No |
| Mean daily solar radiation (MJ/m²/day) | Oklahoma − Nebraska | +2.032 [+0.639, +3.266] | Yes |
| Mean air temperature (°C) | Nebraska − Kansas | +0.411 [-0.476, +1.884] | No |
| Mean air temperature (°C) | Oklahoma − Kansas | -0.954 [-2.087, +0.384] | No |
| Mean air temperature (°C) | Oklahoma − Nebraska | -1.365 [-2.638, -0.368] | Yes |

</details>

### Pooled blocked-district results

Both models include state indicators and fold-local county trend references. The second allows each standardized weather slope to vary by state. Both use the same alpha grid (0.1, 1 and 10) with separate three-fold district tuning inside each outer training set. Every test district has the same held-out county-years as in P27 or P32, with training expanded to the other states. The county trends, weather scaler and ridge use fitting rows only. RMSE is in bu/acre. A negative difference favors the interaction model. Intervals are 95% paired district bootstraps, resampling within each state.

| Geography | County-years | Districts | Common slopes RMSE [95%] | State interactions RMSE [95%] | Interactions − common [95%] |
| --- | --- | --- | --- | --- | --- |
| All states | 6,748 | 25 | 9.354 [8.863, 9.925] | 9.227 [8.744, 9.757] | -0.1265 [-0.2528, +0.0006] |
| Kansas | 3,215 | 9 | 9.577 [9.086, 10.165] | 9.562 [8.974, 10.250] | -0.0145 [-0.1516, +0.1269] |
| Nebraska | 1,733 | 8 | 10.011 [9.050, 11.335] | 9.880 [9.005, 10.916] | -0.1309 [-0.4806, +0.2091] |
| Oklahoma | 1,800 | 8 | 8.229 [7.359, 9.368] | 7.868 [7.030, 8.968] | -0.3609 [-0.6232, -0.1835] |

The pooled point RMSE fell by 0.126 bu/acre, with a 95% difference interval of [−0.2528, +0.0006]. This falls short of the preregistered criterion for a clear pooled improvement. Oklahoma's interval favored interactions, and the Kansas and Nebraska intervals included zero. Interactions lowered RMSE in 18 of 25 districts. The other seven had higher RMSE. Folds share training data, and the bootstrap describes the observed held-out errors without refitting the models.

<details>
<summary>All 25 district folds</summary>

| State | USDA district | County-years | Common RMSE | Interactions RMSE | Δ RMSE | Common alpha | Interactions alpha |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Kansas | NORTHWEST | 237 | 9.863 | 9.672 | -0.191 | 10 | 0.1 |
| Kansas | WEST CENTRAL | 275 | 9.160 | 9.364 | +0.204 | 10 | 0.1 |
| Kansas | SOUTHWEST | 424 | 10.807 | 11.116 | +0.309 | 10 | 0.1 |
| Kansas | NORTH CENTRAL | 349 | 9.144 | 9.106 | -0.038 | 10 | 10 |
| Kansas | CENTRAL | 352 | 8.571 | 8.366 | -0.205 | 10 | 10 |
| Kansas | SOUTH CENTRAL | 418 | 8.934 | 8.850 | -0.085 | 10 | 0.1 |
| Kansas | NORTHEAST | 277 | 11.101 | 11.222 | +0.121 | 10 | 0.1 |
| Kansas | EAST CENTRAL | 442 | 9.163 | 9.168 | +0.005 | 10 | 0.1 |
| Kansas | SOUTHEAST | 441 | 9.470 | 9.151 | -0.319 | 10 | 0.1 |
| Nebraska | NORTHWEST | 335 | 12.714 | 12.041 | -0.673 | 10 | 10 |
| Nebraska | NORTH | 67 | 8.897 | 8.418 | -0.480 | 10 | 0.1 |
| Nebraska | NORTHEAST | 20 | 9.035 | 8.226 | -0.809 | 10 | 0.1 |
| Nebraska | CENTRAL | 134 | 9.436 | 9.282 | -0.154 | 10 | 0.1 |
| Nebraska | EAST | 261 | 9.027 | 8.763 | -0.264 | 10 | 0.1 |
| Nebraska | SOUTHWEST | 290 | 9.840 | 9.800 | -0.040 | 10 | 1 |
| Nebraska | SOUTH | 245 | 9.053 | 9.069 | +0.015 | 0.1 | 0.1 |
| Nebraska | SOUTHEAST | 381 | 9.053 | 9.570 | +0.518 | 10 | 0.1 |
| Oklahoma | PANHANDLE | 154 | 8.029 | 6.893 | -1.136 | 10 | 0.1 |
| Oklahoma | WEST CENTRAL | 201 | 7.470 | 6.912 | -0.558 | 10 | 10 |
| Oklahoma | SOUTHWEST | 255 | 8.545 | 8.476 | -0.070 | 0.1 | 0.1 |
| Oklahoma | NORTH CENTRAL | 264 | 6.606 | 6.610 | +0.004 | 1 | 0.1 |
| Oklahoma | CENTRAL | 358 | 6.953 | 6.713 | -0.241 | 10 | 10 |
| Oklahoma | SOUTH CENTRAL | 185 | 8.217 | 7.608 | -0.609 | 10 | 0.1 |
| Oklahoma | NORTHEAST | 309 | 8.934 | 8.741 | -0.193 | 10 | 0.1 |
| Oklahoma | EAST CENTRAL | 74 | 14.767 | 13.856 | -0.911 | 10 | 0.1 |

</details>

The study compared 15 fitted slopes and 15 pairwise differences. It used 5 model specifications (three standalone state ridges and two pooled ridges), 15 specification–alpha configurations, 477 inner fits, 53 final fits and 3,000 coefficient bootstrap refits. The intervals are descriptive, use few district blocks and have no multiple-comparison adjustment. The coefficient differences describe county-average associations and may reflect management, varieties, irrigation, reporting mix or differences in feature distributions. The study does not establish weather physiology or the quality of rotation recommendations.
