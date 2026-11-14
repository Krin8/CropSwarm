# What to check first

The sensitivity study ranks which inputs move CropSwarm's scores and winners for the three reference farms. Every trial uses the existing score formulas, constraints, cached historical NASA POWER weather and three-year horizon. **This ranks sensitivity inside the model. Real-world importance needs local evidence.** Results are illustrative and need local validation.

## Inputs and ranges

Every range or category below is a **design choice** for the experiment, except where the endpoints come from an existing crop citation. The shape of each draw distribution remains a design choice. The linked inventory files list the exact reference, bounds, test levels, evidence grade and source for every input on each farm.

| Input | Range or alternative |
|---|---|
| Irrigation supply fraction | Telangana 0.48–0.72 around 0.60. Kansas and Makueni 0–0.20 so a zero reference can be checked. The upper end at rainfed points is hypothetical water supply. |
| Baseline rotation identity | Telangana and Makueni only. Replace one season slot with each other crop that passes the reference planting-calendar screen. Keep the original baseline, including any flags, as the reference. Kansas uses the CDL-informed configured baseline. |
| Seasonal crop water need | Use the already-cited catalog ranges. For assumed cereal rye, 176–264 mm around 220 mm. See the crop-by-crop ranges below. |
| Crop duration | Vary the assumed durations by ±20%. Winter wheat 208–312 days, cereal rye 80–120, cowpea 68–102. Use the established P24 source labels. |
| Nitrogen carryover credit and demand | ±20% per crop and quantity. Zero bounds stay zero. Catalog-wide normalization uses the perturbed values and can respond to a crop even where it is excluded from planting. |
| Cover and relative income | ±20% per crop and index, bounded to 0–1. Indices of zero stay zero, including the no-sale assumption for cereal rye. |
| Climate limits | ±20% independently for each crop's minimum and maximum seasonal rainfall, minimum and maximum mean temperature, and daily maximum heat trigger. Temperature percentages use the numeric °C thresholds. |
| Crop eligibility by season | Withdraw one of each crop's listed local seasons at a time. Bare fallow stays available. No unsupported new growing window is assigned to a crop. |
| Season boundaries | Shift each onset and cessation independently by ±20% of its window length, rounded to whole months with a minimum step of one month. Kansas cool shifts up to two months and its warm window up to one. All Telangana and Makueni boundaries shift up to one month. In joint draws keep the window within 1–12 months, clipping at the end if necessary. |
| Scoring and feasibility thresholds | ±20% of the configured values. Calendar extension 36–54 days, maximum median unmet-water fraction 0.64–0.96, maximum hot-day fraction 0.08–0.12, and both risk shares 0.40–0.60. Risk shares vary independently in the joint draws and the existing score clipping still applies. |

Water needs in mm from citations already cataloged include winter wheat 450–650, sorghum and pearl millet 450–650, paddy and soybean 450–700, maize 500–800, common bean and chickpea 300–500, pigeonpea 500–800, green gram 350–400, sunflower 600–1,000, cowpea 281.6–288.0, and field pea 350–500. Each farm uses the relevant crops. For cowpea, the range comes from two field ET observations in Bangalore and carries the original transfer limitation. [Crop catalog](../data/crops.csv) · [Source context](crops.md)

This study holds the number and order of annual season slots, scoring formulas, preset weights, weather, and mapped soil and terrain values fixed. Root-depth class and the legume flag are descriptive fields. Botanical family is literature-sourced for planted crops. Fallow's zero and blank crop fields define the absence of a planted crop. These are outside the sweep. An assumption for a crop outside a farm's available season labels is included only when it can enter catalog-wide nitrogen normalization.

**Full inventories and rankings** are in the [Kansas](../data/processed/sensitivity_us_high_plains_b.json), [Telangana](../data/processed/sensitivity_telangana_a.json), and [Makueni](../data/processed/sensitivity_kenya_makueni_north.json) outputs. Each preset includes all varied inputs, equal ranks, weak-effect marks, changes in the score of the reference winner, ranges of new winning scores, and exact canonical winner counts. Assumptions with no nonzero test level are listed separately from the ranks in the same inventories.

## How the study measures influence

- **One input at a time.** Test up to five evenly spaced numeric levels within each range, rounding discrete values and deduplicating. Season offsets use all admissible integer offsets. Skip the reference value in the fraction of settings that change the winner. Include it in the reported one-at-a-time score ranges so a one-sided or one-level choice can show movement from the reference. Test each listed categorical alternative once.
- **Joint draws.** Use 512 independent input draws per farm and evaluate each draw under all four presets. The fixed NumPy seed is 42. Sample numeric intervals uniformly, rounding integer inputs. Categorical inputs keep their reference with 80% probability and otherwise choose uniformly from their listed alternatives. Report the fraction of draws with a changed canonical winner, the score bounds, and the 10th, 50th and 90th percentiles of the new top score. These fractions depend on the chosen ranges and sampling design.
- **Exact search.** Rebuild score components and feasibility from the perturbed inputs and enumerate all feasible canonical rotations. Whole-year cyclic shifts count once and slots within a year keep their season. Use the lexicographic first exact maximizer, with ties favoring the baseline as in the robustness grid. Always score the drawn baseline with the engine's existing handling of violations. A baseline identical to a feasible canonical cycle shares its identity for counting changes.
- **Ranking.** First sort by the fraction of all one-at-a-time settings that materially change the winner. A change is material when the original winner becomes ineligible or the new leader scores more than 0.01 points above it in that trial. Then sort by top-score span rounded to six decimals. Equal keys share a rank. A weak result has no material change and spans at most 0.01 points. The 0.01 threshold follows the robustness tolerance and is a design choice. If all compared inputs are weak, their order gives little reason to prioritize field checks based on this model.
- **Joint rank sensitivity.** Report signed Spearman ρ for numeric inputs and a rank correlation ratio (η) for unordered categorical inputs, against both the top score and the indicator of a changed winner. An undefined coefficient is shown as unavailable. η is nonnegative and does not indicate direction. These are marginal associations across joint draws. They do not apportion variance or resolve input interactions. The app's main priorities use the one-at-a-time ranks above, with joint associations available in the full results.

A categorical season test may have just one alternative. A 100% sweep change can therefore mean one deterministic exclusion. It should be read with its denominator, score span and joint results. Thresholds, perturbation sizes, categorical probability and sweep levels affect the ordering. A nearly equal score can transfer the winner label, which is why the reports include both all changes and material changes. See the [study settings](../config/sensitivity.json), [scoring](scoring.md) and [evidence grades](evidence_grades.md).

## Results by farm and preset

Kansas varied **121 inputs** in 451 one-at-a-time settings, Telangana **150** in 573, and Makueni **104** in 398. Another 9, 8 and 8 numeric inputs, respectively, stayed at zero throughout their test bounds. Each farm used 512 joint draws, for 1,536 farm draws across all three sites. All four presets use the same draws within a farm.

| Farm | Preset | First three checks in rank order | Weak inputs | Joint winner changes | Material changes | Joint top score | Change from reference score |
|---|---|---|---:|---:|---:|---:|---:|
| Kansas | Water saver | 1. When the warm season starts<br>2. Which seasons are suitable for planting grain sorghum<br>3. Which seasons are suitable for planting soybean | 109 | 85.9% | 77.7% | 0.596–0.764 | -0.088 to +0.080 |
| Kansas | Soil builder | 1. Which seasons are suitable for planting soybean<br>2. Which seasons are suitable for planting cereal rye cover<br>3. The daily heat threshold for common bean | 114 | 76.4% | 59.0% | 0.625–0.773 | -0.090 to +0.058 |
| Kansas | Income | 1. Which seasons are suitable for planting soybean<br>2. Which seasons are suitable for planting grain sorghum<br>3. Which seasons are suitable for planting sunflower | 106 | 92.6% | 86.5% | 0.522–0.797 | -0.119 to +0.155 |
| Kansas | Balanced | 1. When the warm season starts<br>2. Which seasons are suitable for planting grain sorghum<br>3. Which seasons are suitable for planting soybean | 105 | 87.1% | 79.1% | 0.601–0.773 | -0.077 to +0.095 |
| Telangana | Water saver | 1. Which seasons are suitable for planting pigeonpea<br>2. When the monsoon season starts<br>3. When the monsoon season ends | 139 | 78.9% | 71.1% | 0.743–0.854 | -0.059 to +0.052 |
| Telangana | Soil builder | 1. Which seasons are suitable for planting pigeonpea<br>2. When the monsoon season starts<br>3. The daily heat threshold for soybean | 137 | 77.7% | 66.4% | 0.716–0.814 | -0.054 to +0.044 |
| Telangana | Income | 1. When the monsoon season starts<br>2. Which seasons are suitable for planting pigeonpea<br>3. The daily heat threshold for paddy rice | 130 | 96.5% | 92.8% | 0.643–0.799 | -0.030 to +0.126 |
| Telangana | Balanced | 1. Which seasons are suitable for planting pigeonpea<br>2. When the monsoon season starts<br>3. The daily heat threshold for soybean | 139 | 81.6% | 75.4% | 0.687–0.802 | -0.055 to +0.060 |
| Makueni | Water saver | 1. When the long rains season starts<br>2. The daily heat threshold for green gram (mung bean)<br>3. Which seasons are suitable for planting green gram | 97 | 74.4% | 65.0% | 0.554–0.785 | -0.192 to +0.038 |
| Makueni | Soil builder | 1. When the long rains season starts<br>2. The daily heat threshold for green gram (mung bean)<br>3. When the long rains season ends | 89 | 94.1% | 77.0% | 0.629–0.802 | -0.127 to +0.046 |
| Makueni | Income | 1. When the short rains season starts<br>2. When the long rains season starts<br>3. The relative income estimate for grain maize | 86 | 88.3% | 83.8% | 0.569–0.803 | -0.138 to +0.095 |
| Makueni | Balanced | 1. When the long rains season starts<br>2. The daily heat threshold for green gram (mung bean)<br>3. Which seasons are suitable for planting green gram | 90 | 92.8% | 82.2% | 0.598–0.781 | -0.141 to +0.041 |

Season boundaries and crop eligibility lead different farm–preset rankings. No individual input leads everywhere. Kansas switches between the start of the warm season and soybean eligibility. Telangana's pigeonpea eligibility leads three presets. Monsoon onset leads its income preset. In Makueni, long-rains onset leads three presets and short-rains onset leads income. The weakest effects often tie, and most inputs meet the weak-effect rule.

Varying irrigation supply alone never changed the top rotation across the 12 farm–preset combinations. The tested baseline substitutions in Telangana and Makueni also left the top rotation and its score unchanged. These findings apply to the tested ranges and alternatives.

In Telangana, the one-at-a-time exclusion of pigeonpea always changes the reference winner where it leads the rank, with a top-score span of about 0.013–0.025 points across those three presets. Joint winner changes can be more common than material changes. For example, Kansas soil builder changes winner in 76.4% of joint draws, with 59.0% qualifying as material.

### Largest joint rank associations

These rows summarize the largest coefficient magnitudes. The complete coefficients, weak effects and tied groups remain in the farm files. The underlying associations can be weak even when an imposed feasibility change produces a high one-at-a-time rank. A categorical η has no sign. The Makueni soil-builder association with soybean's nitrogen credit comes from the score's catalog-wide normalization, even though soybean is outside the Makueni planting windows.

| Farm | Preset | With top score | With winner change |
|---|---|---|---|
| Kansas | Water saver | `warm.onset_month` · Spearman ρ +0.56 | `sorghum.heat_tolerance_c` · Spearman ρ -0.27 |
| Kansas | Soil builder | `soybean.seasons_allowed` · rank η 0.41 | `soybean.seasons_allowed` · rank η 0.29 |
| Kansas | Income | `sunflower.heat_tolerance_c` · Spearman ρ +0.34 | `sorghum.heat_tolerance_c` · Spearman ρ -0.20 |
| Kansas | Balanced | `warm.onset_month` · Spearman ρ +0.46 | `sorghum.heat_tolerance_c` · Spearman ρ -0.25 |
| Telangana | Water saver | `monsoon.onset_month` · Spearman ρ +0.54 | `pigeonpea.heat_tolerance_c` · Spearman ρ -0.30 |
| Telangana | Soil builder | `post_monsoon.onset_month` · Spearman ρ +0.29 | `pigeonpea.heat_tolerance_c` · Spearman ρ -0.28 |
| Telangana | Income | `monsoon.onset_month` · Spearman ρ +0.36 | `pigeonpea.relative_income_index` · Spearman ρ -0.15 |
| Telangana | Balanced | `monsoon.onset_month` · Spearman ρ +0.45 | `pigeonpea.heat_tolerance_c` · Spearman ρ -0.33 |
| Makueni | Water saver | `green_gram.min_rain_mm` · Spearman ρ -0.29 | `green_gram.heat_tolerance_c` · Spearman ρ -0.28 |
| Makueni | Soil builder | `soybean.n_credit_kg_ha` · Spearman ρ -0.34 | `short_rains.onset_month` · Spearman ρ +0.19 |
| Makueni | Income | `short_rains.onset_month` · Spearman ρ -0.37 | `maize.relative_income_index` · Spearman ρ -0.23 |
| Makueni | Balanced | `long_rains.onset_month` · Spearman ρ -0.33 | `green_gram.heat_tolerance_c` · Spearman ρ -0.20 |

## Offline rebuild

Run `python -m src.sensitivity` from the repository. It reads the committed crop and farm inputs, historical daily POWER records, cached season windows and scoring settings. It writes only the three new sensitivity files. Archived strategy, optimizer, back-test, uncertainty and robustness results retain their published values. The app reads the sensitivity files directly and does not run the sweep during a demo.
