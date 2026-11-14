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

### Evaluation disposition

The verified Nebraska and Oklahoma county centroid tables are absent from the available offline data. The current network scope covers NASS bulk data and resumable POWER requests. The feature build stops before sending a POWER request for either target. Final climate-paired sample sizes, RMSE, R², Spearman and bootstrap intervals are unavailable. There were zero real P32 fits or model configurations tried.

| Preregistered case | Status |
|---|---|
| Nebraska USDA district holdout | Pending Nebraska centroid and weather inputs |
| Oklahoma USDA district holdout | Pending Oklahoma centroid and weather inputs |
| Kansas → Nebraska and Kansas → Oklahoma | Target features and own-state references unavailable |
| Nebraska → Kansas and Oklahoma → Kansas | Source-state climate features unavailable |
| Three-state blocked holdout, including all three state-specific comparisons | Final three-state cohort unavailable |

The prepared evaluator reuses the P25/P27 training-fold trends, ridge scaling, model construction and inner selection. The fixed grid has ridge alpha 0.1, 1 and 10, and forest minimum leaf size 5 and 20 with 48 trees. The same paired bootstrap estimates RMSE, R² and Spearman with 95% intervals. Direct transfer estimates use the source state's averages of training-county means and trends. Each comparison also pairs the same evaluated county-years with the target-state held-out mean and trend baselines, fitted on other reporting districts. The pooled fold excludes an entire state and tunes on the remaining states' state-qualified reporting districts. Its pooled bootstrap would have three state blocks. Seeded fixtures exercise every planned case, disjoint folds and reproducibility.

Centroid weather is a coarse proxy. The yield records mix management and reporting practices. The comparison describes historical weather–yield associations in county averages and does not validate rotation recommendations.

### Resume from verified county coordinates

With locally available verified centroid tables, save the Census HTML as `data/raw/p32/census_31_counties.html` and `data/raw/p32/census_40_counties.html`. A sourced CSV with `fips,county,lat,lon` also works with `--state`, `--centroid-file` and `--centroid-source`. Preserve the source and vintage of either input. Then run:

```sh
python -m src.cross_state_yield_data --fetch --archive
python -m src.cross_state_yield
```

The first command resumes county POWER chunks and writes only P32 weather, feature and coverage files. The second consumes the final cohort and writes separate P32 results. Run `python -m src.cross_state_yield_data --yield-inventory` to reproduce the yield-only counts offline.
