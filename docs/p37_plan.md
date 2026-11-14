# P37 local recalibration preregistration

Freeze this plan before examining P37 cohort counts or evaluating any models. P37 tests the amount of historical local yield information needed to recalibrate a Kansas winter-wheat weather model for Nebraska and Oklahoma. The analysis is illustrative.

## Cohort, origin and common test

- Use committed P25 Kansas features and P32 Nebraska and Oklahoma features and USDA reporting-district labels. Keep only records explicitly reported as non-irrigated winter wheat in all three states. Exclude P25/P32 all-practice fallbacks. The previous county-level coverage screen has already been applied to the feature files. Apply no second county-level minimum after filtering to non-irrigated rows.
- For each target district, order its distinct harvest years with any eligible record. The first k observed years are the calibration set for k = 0, 3, 5, 8 and 12. Use all eligible county records in those years. Freeze the test set across all k and all methods as every district row from the 13th observed year onward. The intervening years for smaller k are unused local data. This common tail is necessary to compare the same observations across the curve. An observed-year sequence can contain calendar gaps. Exclude a district if it has fewer than 13 observed years, and list all such districts. Counties may differ in coverage within a district. For a test county with no calibration record, use the existing P25 equal-training-county fallback for county trend and mean.
- Use one Kansas source model per distinct common-test origin, shared across methods and k within a district. Use only Kansas non-irrigated yields strictly before that district's first test year, including for k = 0. This keeps Kansas outcomes from test years out of the source fit as well. Use random forest, chosen now because it had the lower saved Kansas pooled district-holdout point RMSE in P27. Preserve the P25/P27 model recipe and settings, including the five cached weather features, training-only county detrending with the unseen-county trend fallback, 48 trees, seed 42, minimum leaf grid 5 and 20, and three-fold inner selection grouped by Kansas reporting district. Select by pooled inner RMSE, with existing declared-order tie handling. Do not fit any alternative source learner. If a test origin has fewer than three Kansas reporting districts in training, report the district unavailable under the fixed settings.
- Test years are district-specific and strictly later than all their calibration years. Labels from other target districts never train the local methods. No test labels, including those from an overlapping Kansas harvest year, are used to select hyperparameters or estimate model coefficients.

## Six fixed methods

1. **Source only.** Use the frozen Kansas prediction for the district and origin.
2. **Source + local intercept/trend.** Add an ordinary least-squares line fitted to local yield minus the frozen source prediction, with intercept and calendar-year slope pooled across calibration county-years within the district.
3. **Local ridge.** Fit raw local yield on the same five standardized weather features, with an intercept.
4. **Local ridge + source feature.** Fit raw local yield on those five weather features and the frozen Kansas prediction, with an intercept. Standardize all features inside each fit.
5. **Local trend.** Fit the P25 ordinary least-squares year trend separately by county within the district's k observed years. Use the P25 fallback for unseen counties and its zero slope for a county with just one calibration year.
6. **Local county mean.** Use the mean within each county from the same k observed years and the P25 equal-county fallback for unseen counties.

For both local ridges use the P25 alpha grid (0.1, 1, 10). For selection, hold out each successive calibration year after the first and fit on earlier calibration years only. Select by pooled inner RMSE with declared-order ties. Refit on all k calibration years. No local method is estimable at k = 0. Report that explicitly and give no baseline comparison at k = 0. Report the six methods, the two source grid points and three local alpha values per ridge method, selections, available sample sizes and actual fit counts. Do not tune on test years or add methods.

## Evaluation and reporting

Report RMSE (bu/acre), R² and Spearman for each state, method and k, with the P25/P27 descriptive 95% percentile intervals from 1,000 paired district-block bootstrap draws and seed 42. Use the same within-state blocks for every k and method. Reuse the same resamples for paired RMSE difference from method 5. Declare improvement only when the upper endpoint of the paired difference is strictly below zero. Report the smallest tested k meeting this rule per method and state. Method 5 compares with itself and cannot improve under that rule. Preserve failures, undefined correlations and unavailable methods. These are descriptive pointwise intervals without multiplicity adjustment. State that the exercise uses recorded district yield histories, which many farmers do not have. The analysis concerns aggregate weather–yield associations. Crop rotation quality is outside the evaluation.

No network, existing pipeline edits, or changes to any earlier saved results.
