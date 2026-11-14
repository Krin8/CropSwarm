# Metric-by-metric tie diagnosis

This report uses the P16d **canonical whole-year rotation** grid and refreshed P16b adjacent cells. Each pair is the highest and second-highest distinct rotation among exact feasible rotations plus the retained baseline. The six signed differences are **top minus second** in normalized metric-score units. `0` means equal to within `1e-12` (a floating-point comparison convention, design choice). Multiply each difference by that preset’s weight in [weights_presets.json](../config/weights_presets.json) and sum to recover the weighted gap. Full-precision top and second scores, weighted contributions, crop sequences and a source tag for every metric are in the [Kansas](../data/processed/tie_diagnosis_us_high_plains_b.json), [Telangana](../data/processed/tie_diagnosis_telangana_a.json), and [Makueni](../data/processed/tie_diagnosis_kenya_makueni_north.json) records. All scores are illustrative; validate locally.

**Water, erosion and climate fit** respond to the uniform weather shifts. **Nitrogen, relative income and family/cover risk** do not change with weather for a fixed rotation in this model, though their values may differ between rotations. Thus a small total gap can reflect opposing weighted metric changes. No model values were tuned.

| Farm / preset | Cell | Top vs second distinct rotation | Weighted gap | Water Δ | N Δ | Erosion Δ | Climate fit Δ | Income Δ | Risk Δ |
|---|---|---|---|---|---|---|---|---|---|
| Kansas / water saver | +1.5 °C, +0% rain (before) | fallow → soybean → sorghum **vs** fallow → sorghum → soybean | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Kansas / water saver | +2 °C, +0% rain (after) | fallow → soybean → pearl_millet **vs** fallow → pearl_millet → soybean | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Kansas / soil builder | +3 °C, +0% rain (before) | fallow → cereal_rye_cover → soybean **vs** fallow → soybean → cereal_rye_cover | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Kansas / soil builder | +3 °C, +10% rain (after) | fallow → soybean → pearl_millet **vs** fallow → pearl_millet → soybean | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Kansas / income | +1 °C, +0% rain (before) | sorghum → sunflower → soybean **vs** sorghum → soybean → sunflower | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Kansas / income | +1.5 °C, +0% rain (after) | maize → soybean → sunflower **vs** maize → sunflower → soybean | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Kansas / balanced | +1 °C, +0% rain (before) | fallow → soybean → sorghum **vs** fallow → sorghum → soybean | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Kansas / balanced | +1 °C, +10% rain (after) | fallow → soybean → pearl_millet **vs** fallow → pearl_millet → soybean | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Telangana / soil builder | +2.5 °C, +0% rain (before) | pigeonpea then fallow ×3 **vs** soybean then fallow → pigeonpea then fallow → pigeonpea then fallow | +0.001428 | +0.002671 | -0.004329 | +0.003173 | +0.03333 | -0.01667 | 0 |
| Telangana / soil builder | +3 °C, +0% rain (after) | soybean then fallow ×3 **vs** soybean then fallow → soybean then fallow → pigeonpea then fallow | +1.744e-07 | -0.002671 | +0.004329 | -0.003173 | -0.01905 | +0.01667 | 0 |
| Telangana / income | +1 °C, +0% rain (before) | pigeonpea then maize ×3 **vs** pigeonpea then paddy → pigeonpea then maize → pigeonpea then maize | +0.0005728 | +0.0006341 | -0.01082 | +0.001833 | 0 | +0.003333 | 0 |
| Telangana / income | +1 °C, +10% rain (after) | soybean then maize ×3 **vs** soybean then maize → soybean then maize → pigeonpea then maize | +0.0003873 | -0.002283 | +0.004329 | -0.00349 | -0.04762 | +0.01667 | 0 |
| Telangana / balanced | +3 °C, +0% rain (before) | pigeonpea then fallow ×3 **vs** soybean then fallow → pigeonpea then fallow → pigeonpea then fallow | +0.0008291 | +0.002671 | -0.004329 | +0.003173 | +0.01905 | -0.01667 | 0 |
| Telangana / balanced | +3 °C, +10% rain (after) | soybean then fallow ×3 **vs** soybean then fallow → soybean then fallow → pigeonpea then fallow | +0.0008021 | -0.002283 | +0.004329 | -0.00349 | -0.009524 | +0.01667 | 0 |
| Makueni / water saver | +0 °C, -20% rain (before) | green_gram then fallow ×3 **vs** green_gram then fallow → green_gram then fallow → cowpea then fallow | +0.004926 | -0.024247 | -0.0054113 | -0.003468 | +0.090476 | +0.01 | 0 |
| Makueni / water saver | +0 °C, -30% rain (after) | fallow then cowpea ×3 **vs** green_gram then fallow ×3 | +0.001169 | +0.06399 | +0.016234 | +0.0038837 | -0.14034 | -0.03 | 0 |
| Makueni / soil builder | +0 °C, +0% rain (before) | green_gram then pearl_millet ×3 **vs** green_gram then fallow → green_gram then pearl_millet → green_gram then pearl_millet | +0.0007852 | -0.09171 | -0.0487 | +0.02144 | -0.01961 | +0.08667 | +0.08333 |
| Makueni / soil builder | +0 °C, -10% rain (after) | green_gram then fallow ×3 **vs** green_gram then fallow → green_gram then fallow → green_gram then pearl_millet | +0.001396 | +0.09835 | +0.0487 | -0.0193 | +0.02941 | -0.08667 | -0.08333 |
| Makueni / income | +0 °C, -10% rain (before) | maize then green_gram ×3 **vs** maize then common_bean → maize then green_gram → maize then green_gram | +0.001272 | -0.004557 | +0.003247 | -0.0004639 | +0.02451 | -0.005 | 0 |
| Makueni / income | +0 °C, -20% rain (after) | maize then common_bean ×3 **vs** maize then common_bean → maize then common_bean → maize then green_gram | +0.0002217 | +0.004816 | -0.003247 | +0.0004124 | -0.01471 | +0.005 | 0 |
| Makueni / balanced | +0 °C, +0% rain (before) | green_gram then pearl_millet ×3 **vs** green_gram then sorghum → green_gram then pearl_millet → green_gram then pearl_millet | +0.003566 | -0.00783 | +0.03247 | -0.004055 | +0.009804 | -0.01 | 0 |
| Makueni / balanced | +0 °C, +10% rain (after) | pearl_millet then green_gram ×3 **vs** green_gram then pearl_millet ×3 | +0.0006898 | +0.003275 | 0 | +0.001623 | -0.0008403 | 0 | 0 |

## Diagnosis

- **Kansas:** Every compared zero-gap pair has the same six metric scores and the same crop multiset in a different order. With one annual slot, the model averages water, erosion, climate fit and income over slots; nitrogen credit/demand and the counted risk also remain equal for these orderings. After canonicalization and deterministic tie-breaking under the P16 weather shifts, the soil-builder and income nearest changed cells involve new crop sets. The earlier nearest map-label flips for those two presets were tie-selection artifacts. The refreshed grid still has order ties within each cell, because changing the order of three crops is not necessarily a whole-year cyclic shift.
- **Telangana and Makueni:** The paired rotations use different crop mixes or season assignments. The table shows which scores are equal and which differ; the signed weighted contributions nearly cancel. Climate-insensitive metrics can supply common terms (for example, risk is equal in most pairs), but they do not by themselves cause a flip. Makueni balanced after the change is especially clear: nitrogen, income and risk are equal, while water, erosion and climate fit differ.
- **Bug or rounding:** Recomputed full-precision top-two gaps match the refreshed P16b records, and the six weighted metric differences sum to each gap. No scoring bug or numerical rounding error was found. An earlier four-decimal app sentence could display the tiny Telangana soil-builder after-gap as `0.0000`; the P16 weather-shift robustness panel avoids that misleading precision. P16d now chooses the lexicographically first canonical rotation in an exact tie, so a changed feasible pool does not reorder surviving tied rotations. The P16 climate grid was rerun with that tie rule; metric definitions remain unchanged.

## Displayed alternatives

The four alternatives in the reference app are grouped by complete-link comparison: every pair in a group must have maximum absolute difference at most `0.05` across the six normalized metric scores. The threshold and display-order grouping are **design choices, not empirical values**. Selection now requires every alternative also to clear that threshold against the baseline. A group is one meaningfully different metric profile, not proof of equivalent field outcomes.

| Farm | Near-duplicate alternatives | Largest metric-score difference | Meaningfully different groups |
|---|---|---:|---:|
| Kansas | None in the four displayed alternatives | — | 4 of 4 |
| Telangana | None in the four displayed alternatives | — | 4 of 4 |
| Makueni | None in the four displayed alternatives | — | 4 of 4 |

The exact-score tie rule is documented in [the P16 robustness check under weather shifts](stress_test.md): the lexicographically first canonical maximizer wins; the baseline wins an exact tie with the best feasible candidate. Whole-year cyclic shifts share a strategy label. This rule is deterministic and independent of the number of other feasible rotations.
