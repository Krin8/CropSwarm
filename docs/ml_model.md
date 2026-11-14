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
