# Metric-by-metric tie diagnosis

This report uses the unchanged P16 grid and P16b adjacent cells. Each pair is the highest and second-highest **distinct whole-year rotation** among exact feasible rotations plus the retained baseline. The six signed differences are **top minus second** in normalized metric-score units. `0` means equal to within `1e-12` (a floating-point comparison convention, design choice). Multiply each difference by that preset’s weight in [weights_presets.json](../config/weights_presets.json) and sum to recover the weighted gap. Full-precision top and second scores, weighted contributions, crop sequences and a source tag for every metric are in the [Kansas](../data/processed/tie_diagnosis_us_high_plains_b.json), [Telangana](../data/processed/tie_diagnosis_telangana_a.json), and [Makueni](../data/processed/tie_diagnosis_kenya_makueni_north.json) records. All scores are illustrative; validate locally.

**Water, erosion and climate fit** respond to the uniform weather shifts. **Nitrogen, relative income and family/cover risk** do not change with weather for a fixed rotation in this model, though their values may differ between rotations. Thus a small total gap can reflect opposing weighted metric changes. No model values were tuned.

| Farm / preset | Cell | Top vs second distinct rotation | Weighted gap | Water Δ | N Δ | Erosion Δ | Climate fit Δ | Income Δ | Risk Δ |
|---|---|---|---|---|---|---|---|---|---|
| Kansas / water saver | +1.5 °C, +0% rain (before) | fallow → soybean → sorghum **vs** fallow → sorghum → soybean | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Kansas / water saver | +2 °C, +0% rain (after) | fallow → soybean → pearl_millet **vs** fallow → pearl_millet → soybean | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Kansas / soil builder | +0 °C, +0% rain (before) | fallow → cereal_rye_cover → soybean **vs** fallow → soybean → cereal_rye_cover | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Kansas / soil builder | +0 °C, +10% rain (after) | fallow → cereal_rye_cover → soybean **vs** fallow → soybean → cereal_rye_cover | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Kansas / income | +0 °C, +0% rain (before) | sorghum → sunflower → soybean **vs** sorghum → soybean → sunflower | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Kansas / income | +0 °C, +10% rain (after) | sorghum → sunflower → soybean **vs** sorghum → soybean → sunflower | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Kansas / balanced | +1 °C, +0% rain (before) | fallow → soybean → sorghum **vs** fallow → sorghum → soybean | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Kansas / balanced | +1 °C, +10% rain (after) | fallow → soybean → pearl_millet **vs** fallow → pearl_millet → soybean | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Telangana / soil builder | +2.5 °C, +0% rain (before) | pigeonpea then fallow ×3 **vs** soybean then fallow → pigeonpea then fallow → pigeonpea then fallow | +0.001428 | +0.002671 | -0.004329 | +0.003173 | +0.03333 | -0.01667 | 0 |
| Telangana / soil builder | +3 °C, +0% rain (after) | soybean then fallow ×3 **vs** soybean then fallow → soybean then fallow → pigeonpea then fallow | +1.744e-07 | -0.002671 | +0.004329 | -0.003173 | -0.01905 | +0.01667 | 0 |
| Telangana / income | +1 °C, +0% rain (before) | pigeonpea then maize ×3 **vs** pigeonpea then paddy → pigeonpea then maize → pigeonpea then maize | +0.0005728 | +0.0006341 | -0.01082 | +0.001833 | 0 | +0.003333 | 0 |
| Telangana / income | +1 °C, +10% rain (after) | soybean then maize ×3 **vs** soybean then maize → soybean then maize → pigeonpea then maize | +0.0003873 | -0.002283 | +0.004329 | -0.00349 | -0.04762 | +0.01667 | 0 |
| Telangana / balanced | +3 °C, +0% rain (before) | pigeonpea then fallow ×3 **vs** soybean then fallow → pigeonpea then fallow → pigeonpea then fallow | +0.0008291 | +0.002671 | -0.004329 | +0.003173 | +0.01905 | -0.01667 | 0 |
| Telangana / balanced | +3 °C, +10% rain (after) | soybean then fallow ×3 **vs** soybean then fallow → soybean then fallow → pigeonpea then fallow | +0.0008021 | -0.002283 | +0.004329 | -0.00349 | -0.009524 | +0.01667 | 0 |
| Makueni / water saver | +0 °C, -20% rain (before) | green_gram then fallow ×3 **vs** fallow then cowpea ×3 | +0.002984 | -0.07645 | -0.01623 | -0.004438 | +0.1975 | +0.03 | 0 |
| Makueni / water saver | +0 °C, -30% rain (after) | fallow then cowpea ×3 **vs** fallow then green_gram → fallow then cowpea → fallow then cowpea | +0.002219 | +0.02503 | +0.005411 | +0.002631 | -0.04412 | -0.01 | 0 |
| Makueni / soil builder | +0 °C, +0% rain (before) | green_gram then pearl_millet ×3 **vs** green_gram then fallow → green_gram then pearl_millet → green_gram then pearl_millet | +0.0007852 | -0.09171 | -0.0487 | +0.02144 | -0.01961 | +0.08667 | +0.08333 |
| Makueni / soil builder | +0 °C, -10% rain (after) | green_gram then fallow ×3 **vs** green_gram then fallow → green_gram then fallow → green_gram then pearl_millet | +0.001396 | +0.09835 | +0.0487 | -0.0193 | +0.02941 | -0.08667 | -0.08333 |
| Makueni / income | +0 °C, -10% rain (before) | maize then green_gram ×3 **vs** maize then common_bean → maize then green_gram → maize then green_gram | +0.001272 | -0.004557 | +0.003247 | -0.0004639 | +0.02451 | -0.005 | 0 |
| Makueni / income | +0 °C, -20% rain (after) | maize then common_bean ×3 **vs** maize then common_bean → maize then common_bean → maize then green_gram | +0.0002217 | +0.004816 | -0.003247 | +0.0004124 | -0.01471 | +0.005 | 0 |
| Makueni / balanced | +0 °C, +0% rain (before) | green_gram then pearl_millet ×3 **vs** green_gram then sorghum → green_gram then pearl_millet → green_gram then pearl_millet | +0.003566 | -0.00783 | +0.03247 | -0.004055 | +0.009804 | -0.01 | 0 |
| Makueni / balanced | +0 °C, +10% rain (after) | pearl_millet then green_gram ×3 **vs** green_gram then pearl_millet ×3 | +0.0006898 | +0.003275 | 0 | +0.001623 | -0.0008403 | 0 | 0 |

## Diagnosis

- **Kansas:** Every compared zero-gap pair has the same six metric scores and the same crop multiset in a different order. With one annual slot, the model averages water, erosion, climate fit and income over slots; nitrogen credit/demand and the counted risk also remain equal for these orderings. The soil-builder and income pairs are unchanged across the reported adjacent cells, so those two P16 map-label flips are solely tie-selection artifacts. Water-saver and balanced change the tied crop set at their adjacent cells, but ordering within each set remains exactly tied.
- **Telangana and Makueni:** The paired rotations use different crop mixes or season assignments. The table shows which scores are equal and which differ; the signed weighted contributions nearly cancel. Climate-insensitive metrics can supply common terms (for example, risk is equal in most pairs), but they do not by themselves cause a flip. Makueni balanced after the change is especially clear: nitrogen, income and risk are equal, while water, erosion and climate fit differ.
- **Bug or rounding:** Recomputed full-precision top-two gaps match P16b, and the six weighted metric differences sum to each gap. No scoring bug or numerical rounding error was found. An earlier four-decimal app sentence could display the tiny Telangana soil-builder after-gap as `0.0000`; the robustness panel now avoids that misleading precision. P16’s seeded permutation is reproducible, but its selected label among exactly equal scores can change when the feasible pool size changes. This is a **presentation/tie-selection artifact**, not a score change. The P16 grid and scores are retained as requested.

## Displayed alternatives

The four alternatives in the reference app are grouped by complete-link comparison: every pair in a group must have maximum absolute difference at most `0.05` across the six normalized metric scores. The threshold and display-order grouping are **design choices, not empirical values**. A group is one meaningfully different metric profile, not proof of equivalent field outcomes.

| Farm | Near-duplicate alternatives | Largest metric-score difference | Meaningfully different groups |
|---|---|---:|---:|
| Kansas | water saver / balanced | 0.000000 | 3 of 4 |
| Telangana | soil builder / balanced | 0.000000 | 3 of 4 |
| Makueni | soil builder / balanced | 0.032468 | 3 of 4 |

The exact-score tie rule is documented in [the robustness check](stress_test.md): the first maximizer in a fixed-seed permutation of the enumerated feasible rotations wins; the baseline wins an exact tie with the best feasible candidate. Whole-year cyclic shifts share a strategy label. This rule is deterministic for fixed cached inputs and software, but a changed feasible pool can select another equal-scoring label.
