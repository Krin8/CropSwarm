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
