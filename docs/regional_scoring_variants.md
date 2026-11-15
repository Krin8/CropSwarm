# Regional literature-informed variants (P46)

[Preregistration](p46_plan.md) was committed as `24b48fb` before evaluation. [Full-precision results](../data/processed/regional_scoring_variants_p46.json).

Illustrative what-if, validate locally. Each substitution applies to one farm. Makueni cropland is unverified and Telangana's second season remains tentative. Regional results cannot establish crop responses at the demo points or the quality of a rotation.

## Inputs and exact comparisons

- **Makueni common-bean nitrogen credit** (kg N/ha). Catalog 22. Low 44, mid 62, high 80. Figure 2, Tables II–VI and pp. 130, 135–136. [Nadar and Faught (1984), East African Agricultural and Forestry Journal](https://pdf.usaid.gov/pdf_docs/PNAAX822.pdf)
- **Telangana paddy water demand** (mm ET). Catalog 575. Low 473.9, mid 565.85, high 657.8. Table 2, p. 119 (seasonal ET); p. 118 (variety duration and irrigation regimes). [Mote et al. (2018), Journal of Agrometeorology](https://pdfs.semanticscholar.org/e027/a990fd565193f4a02e017cf66d4086fcdd89.pdf)

Endpoints are literature values and midpoints are design choices. The Makueni trial estimated fertilizer equivalence before sole maize. The model applies the credit to every slot after bean and recalculates the nitrogen normalization denominator. A normalized nitrogen score can change even when raw nitrogen stays the same. Telangana's trial spans 100 days after transplanting. The model applies its totals to 120-day crop windows and reapplies the same water screen. Its water score uses cached NASA POWER with soil storage and the assumed irrigation fraction.

Near-ties use 0.01 weighted points, a design choice. Spearman uses only rotations feasible in both settings. Each winner and near-top set is computed in its own pool. Near-top counts include the winner. Equal objectives use the first canonical row. An exact top-tie count of one means the leader is alone within the numerical tolerance.

The [P22 replay](sensitivity.md) uses 512 matched draws per farm with seed 42. It fixes the changed coordinate while preserving the other sampled inputs. Rates compare each draw with its own nominal reference, and the paired count compares the two winners on the same draw. A material change requires a changed winner and either reference ineligibility or a gap above the near-tie tolerance. Original P22 winner histograms, nominal references and change rates reproduced.

**6 of 24** active level–preset comparisons changed the nominal leader. Top-two near-ties created **0**, resolved **0**.

## All configurations

Each pairing points to the exact same farm-level results as its constituent single changes. The farms have independent pools and scores. Kansas uses the original inputs for every pairing.

| Makueni setting | Telangana setting | Kansas setting |
| --- | --- | --- |
| original | original | original |
| original | low | original |
| original | mid | original |
| original | high | original |
| low | original | original |
| low | low | original |
| low | mid | original |
| low | high | original |
| mid | original | original |
| mid | low | original |
| mid | mid | original |
| mid | high | original |
| high | original | original |
| high | low | original |
| high | mid | original |
| high | high | original |

## US High Plains B

### Original input

Feasible canonical rotations **168 → 168**. Common 168, added 0, removed 0.

| Preset | Original leader (score) | Variant leader (score) | Changed | Original leader feasible / optimal | Rank ρ |
| --- | --- | --- | --- | --- | --- |
| water saver | fallow → sorghum → soybean (0.683723) | fallow → sorghum → soybean (0.683723) | no | yes / yes | 1.000000 |
| soil builder | fallow → soybean → cereal rye cover (0.715755) | fallow → soybean → cereal rye cover (0.715755) | no | yes / yes | 1.000000 |
| income | sorghum → soybean → sunflower (0.641364) | sorghum → soybean → sunflower (0.641364) | no | yes / yes | 1.000000 |
| balanced | fallow → sorghum → soybean (0.678125) | fallow → sorghum → soybean (0.678125) | no | yes / yes | 1.000000 |

| Preset | Top-two gap original → variant | Exact top ties original → variant | Near-top count original → variant | Entered / left | Top-two near-tie |
| --- | --- | --- | --- | --- | --- |
| water saver | 0.000000 → 0.000000 | 2 → 2 | 4 → 4 | 0 / 0 | no change |
| soil builder | 0.000000 → 0.000000 | 2 → 2 | 4 → 4 | 0 / 0 | no change |
| income | 0.000000 → 0.000000 | 2 → 2 | 2 → 2 | 0 / 0 | no change |
| balanced | 0.000000 → 0.000000 | 2 → 2 | 2 → 2 | 0 / 0 | no change |

| Preset | P22 change original → variant | Change (pp) | Material original → variant | Material change (pp) | Paired winners differ |
| --- | --- | --- | --- | --- | --- |
| water saver | 85.94% → 85.94% | +0.00 | 77.73% → 77.73% | +0.00 | 0/512 (0.00%) |
| soil builder | 76.37% → 76.37% | +0.00 | 58.98% → 58.98% | +0.00 | 0/512 (0.00%) |
| income | 92.58% → 92.58% | +0.00 | 86.52% → 86.52% | +0.00 | 0/512 (0.00%) |
| balanced | 87.11% → 87.11% | +0.00 | 79.10% → 79.10% | +0.00 | 0/512 (0.00%) |

Published baseline and shortlist deltas are variant minus original, shown as raw / normalized. Flags locate slots in the displayed rotation.

| Published option | Water (mm unmet per slot) | Nitrogen (kg N/ha per slot) | Erosion (slope × rainfall proxy) | Climate Fit (historical share) | Income (relative index) | Risk (relative penalty) | Flag changes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| water saver | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| soil builder | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| income | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| balanced | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |

## Telangana A

### Original input

Feasible canonical rotations **211,394 → 211,394**. Common 211,394, added 0, removed 0.

| Preset | Original leader (score) | Variant leader (score) | Changed | Original leader feasible / optimal | Rank ρ |
| --- | --- | --- | --- | --- | --- |
| water saver | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.801544) | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.801544) | no | yes / yes | 1.000000 |
| soil builder | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.770346) | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.770346) | no | yes / yes | 1.000000 |
| income | pigeonpea / maize → pigeonpea / maize → pigeonpea / maize (0.672979) | pigeonpea / maize → pigeonpea / maize → pigeonpea / maize (0.672979) | no | yes / yes | 1.000000 |
| balanced | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.741856) | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.741856) | no | yes / yes | 1.000000 |

| Preset | Top-two gap original → variant | Exact top ties original → variant | Near-top count original → variant | Entered / left | Top-two near-tie |
| --- | --- | --- | --- | --- | --- |
| water saver | 0.008222 → 0.008222 | 1 → 1 | 3 → 3 | 0 / 0 | no change |
| soil builder | 0.004286 → 0.004286 | 1 → 1 | 3 → 3 | 0 / 0 | no change |
| income | 0.000573 → 0.000573 | 1 → 1 | 56 → 56 | 0 / 0 | no change |
| balanced | 0.008115 → 0.008115 | 1 → 1 | 2 → 2 | 0 / 0 | no change |

| Preset | P22 change original → variant | Change (pp) | Material original → variant | Material change (pp) | Paired winners differ |
| --- | --- | --- | --- | --- | --- |
| water saver | 78.91% → 78.91% | +0.00 | 71.09% → 71.09% | +0.00 | 0/512 (0.00%) |
| soil builder | 77.73% → 77.73% | +0.00 | 66.41% → 66.41% | +0.00 | 0/512 (0.00%) |
| income | 96.48% → 96.48% | +0.00 | 92.77% → 92.77% | +0.00 | 0/512 (0.00%) |
| balanced | 81.64% → 81.64% | +0.00 | 75.39% → 75.39% | +0.00 | 0/512 (0.00%) |

Published baseline and shortlist deltas are variant minus original, shown as raw / normalized. Flags locate slots in the displayed rotation.

| Published option | Water (mm unmet per slot) | Nitrogen (kg N/ha per slot) | Erosion (slope × rainfall proxy) | Climate Fit (historical share) | Income (relative index) | Risk (relative penalty) | Flag changes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| water saver | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| soil builder | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| income | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| balanced | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |

### Low input

Feasible canonical rotations **211,394 → 211,394**. Common 211,394, added 0, removed 0.

| Preset | Original leader (score) | Variant leader (score) | Changed | Original leader feasible / optimal | Rank ρ |
| --- | --- | --- | --- | --- | --- |
| water saver | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.801544) | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.801544) | no | yes / yes | 0.999627 |
| soil builder | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.770346) | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.770346) | no | yes / yes | 0.999980 |
| income | pigeonpea / maize → pigeonpea / maize → pigeonpea / maize (0.672979) | pigeonpea / maize → pigeonpea / maize → pigeonpea / maize (0.672979) | no | yes / yes | 0.999968 |
| balanced | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.741856) | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.741856) | no | yes / yes | 0.999880 |

| Preset | Top-two gap original → variant | Exact top ties original → variant | Near-top count original → variant | Entered / left | Top-two near-tie |
| --- | --- | --- | --- | --- | --- |
| water saver | 0.008222 → 0.008222 | 1 → 1 | 3 → 3 | 0 / 0 | no change |
| soil builder | 0.004286 → 0.004286 | 1 → 1 | 3 → 3 | 0 / 0 | no change |
| income | 0.000573 → 0.000483 | 1 → 1 | 56 → 57 | 1 / 0 | no change |
| balanced | 0.008115 → 0.008115 | 1 → 1 | 2 → 2 | 0 / 0 | no change |

| Preset | P22 change original → variant | Change (pp) | Material original → variant | Material change (pp) | Paired winners differ |
| --- | --- | --- | --- | --- | --- |
| water saver | 78.91% → 78.91% | +0.00 | 71.09% → 71.09% | +0.00 | 2/512 (0.39%) |
| soil builder | 77.73% → 77.73% | +0.00 | 66.41% → 66.41% | +0.00 | 0/512 (0.00%) |
| income | 96.48% → 96.48% | +0.00 | 92.77% → 92.77% | +0.00 | 7/512 (1.37%) |
| balanced | 81.64% → 81.84% | +0.20 | 75.39% → 75.39% | +0.00 | 3/512 (0.59%) |

Published baseline and shortlist deltas are variant minus original, shown as raw / normalized. Flags locate slots in the displayed rotation.

| Published option | Water (mm unmet per slot) | Nitrogen (kg N/ha per slot) | Erosion (slope × rainfall proxy) | Climate Fit (historical share) | Income (relative index) | Risk (relative penalty) | Flag changes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | -29.40472 / +0.01396 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| water saver | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| soil builder | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| income | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| balanced | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |

### Mid input

Feasible canonical rotations **211,394 → 211,394**. Common 211,394, added 0, removed 0.

| Preset | Original leader (score) | Variant leader (score) | Changed | Original leader feasible / optimal | Rank ρ |
| --- | --- | --- | --- | --- | --- |
| water saver | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.801544) | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.801544) | no | yes / yes | 0.999997 |
| soil builder | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.770346) | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.770346) | no | yes / yes | 1.000000 |
| income | pigeonpea / maize → pigeonpea / maize → pigeonpea / maize (0.672979) | pigeonpea / maize → pigeonpea / maize → pigeonpea / maize (0.672979) | no | yes / yes | 1.000000 |
| balanced | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.741856) | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.741856) | no | yes / yes | 0.999999 |

| Preset | Top-two gap original → variant | Exact top ties original → variant | Near-top count original → variant | Entered / left | Top-two near-tie |
| --- | --- | --- | --- | --- | --- |
| water saver | 0.008222 → 0.008222 | 1 → 1 | 3 → 3 | 0 / 0 | no change |
| soil builder | 0.004286 → 0.004286 | 1 → 1 | 3 → 3 | 0 / 0 | no change |
| income | 0.000573 → 0.000566 | 1 → 1 | 56 → 56 | 0 / 0 | no change |
| balanced | 0.008115 → 0.008115 | 1 → 1 | 2 → 2 | 0 / 0 | no change |

| Preset | P22 change original → variant | Change (pp) | Material original → variant | Material change (pp) | Paired winners differ |
| --- | --- | --- | --- | --- | --- |
| water saver | 78.91% → 78.91% | +0.00 | 71.09% → 70.90% | -0.20 | 3/512 (0.59%) |
| soil builder | 77.73% → 77.73% | +0.00 | 66.41% → 66.41% | +0.00 | 0/512 (0.00%) |
| income | 96.48% → 96.48% | +0.00 | 92.77% → 92.77% | +0.00 | 5/512 (0.98%) |
| balanced | 81.64% → 81.64% | +0.00 | 75.39% → 75.20% | -0.20 | 3/512 (0.59%) |

Published baseline and shortlist deltas are variant minus original, shown as raw / normalized. Flags locate slots in the displayed rotation.

| Published option | Water (mm unmet per slot) | Nitrogen (kg N/ha per slot) | Erosion (slope × rainfall proxy) | Climate Fit (historical share) | Income (relative index) | Risk (relative penalty) | Flag changes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | -2.78331 / +0.00127 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| water saver | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| soil builder | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| income | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| balanced | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |

### High input

Feasible canonical rotations **211,394 → 211,394**. Common 211,394, added 0, removed 0.

| Preset | Original leader (score) | Variant leader (score) | Changed | Original leader feasible / optimal | Rank ρ |
| --- | --- | --- | --- | --- | --- |
| water saver | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.801544) | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.801544) | no | yes / yes | 0.999738 |
| soil builder | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.770346) | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.770346) | no | yes / yes | 0.999986 |
| income | pigeonpea / maize → pigeonpea / maize → pigeonpea / maize (0.672979) | pigeonpea / maize → pigeonpea / maize → pigeonpea / maize (0.672979) | no | yes / yes | 0.999977 |
| balanced | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.741856) | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.741856) | no | yes / yes | 0.999915 |

| Preset | Top-two gap original → variant | Exact top ties original → variant | Near-top count original → variant | Entered / left | Top-two near-tie |
| --- | --- | --- | --- | --- | --- |
| water saver | 0.008222 → 0.008222 | 1 → 1 | 3 → 3 | 0 / 0 | no change |
| soil builder | 0.004286 → 0.004286 | 1 → 1 | 3 → 3 | 0 / 0 | no change |
| income | 0.000573 → 0.000626 | 1 → 1 | 56 → 56 | 0 / 0 | no change |
| balanced | 0.008115 → 0.008115 | 1 → 1 | 2 → 2 | 0 / 0 | no change |

| Preset | P22 change original → variant | Change (pp) | Material original → variant | Material change (pp) | Paired winners differ |
| --- | --- | --- | --- | --- | --- |
| water saver | 78.91% → 78.91% | +0.00 | 71.09% → 70.70% | -0.39 | 5/512 (0.98%) |
| soil builder | 77.73% → 77.73% | +0.00 | 66.41% → 66.41% | +0.00 | 0/512 (0.00%) |
| income | 96.48% → 96.48% | +0.00 | 92.77% → 92.77% | +0.00 | 2/512 (0.39%) |
| balanced | 81.64% → 81.64% | +0.00 | 75.39% → 75.20% | -0.20 | 2/512 (0.39%) |

Published baseline and shortlist deltas are variant minus original, shown as raw / normalized. Flags locate slots in the displayed rotation.

| Published option | Water (mm unmet per slot) | Nitrogen (kg N/ha per slot) | Erosion (slope × rainfall proxy) | Climate Fit (historical share) | Income (relative index) | Risk (relative penalty) | Flag changes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | +25.96162 / -0.01110 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| water saver | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| soil builder | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| income | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| balanced | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |

## Makueni North Candidate

### Original input

Feasible canonical rotations **16,914 → 16,914**. Common 16,914, added 0, removed 0.

| Preset | Original leader (score) | Variant leader (score) | Changed | Original leader feasible / optimal | Rank ρ |
| --- | --- | --- | --- | --- | --- |
| water saver | green gram / fallow → green gram / fallow → green gram / fallow (0.746728) | green gram / fallow → green gram / fallow → green gram / fallow (0.746728) | no | yes / yes | 1.000000 |
| soil builder | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.755802) | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.755802) | no | yes / yes | 1.000000 |
| income | maize / green gram → maize / green gram → maize / green gram (0.707399) | maize / green gram → maize / green gram → maize / green gram (0.707399) | no | yes / yes | 1.000000 |
| balanced | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.739487) | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.739487) | no | yes / yes | 1.000000 |

| Preset | Top-two gap original → variant | Exact top ties original → variant | Near-top count original → variant | Entered / left | Top-two near-tie |
| --- | --- | --- | --- | --- | --- |
| water saver | 0.005711 → 0.005711 | 1 → 1 | 3 → 3 | 0 / 0 | no change |
| soil builder | 0.000785 → 0.000785 | 1 → 1 | 29 → 29 | 0 / 0 | no change |
| income | 0.001022 → 0.001022 | 1 → 1 | 42 → 42 | 0 / 0 | no change |
| balanced | 0.003566 → 0.003566 | 1 → 1 | 12 → 12 | 0 / 0 | no change |

| Preset | P22 change original → variant | Change (pp) | Material original → variant | Material change (pp) | Paired winners differ |
| --- | --- | --- | --- | --- | --- |
| water saver | 74.41% → 74.41% | +0.00 | 65.04% → 65.04% | +0.00 | 0/512 (0.00%) |
| soil builder | 94.14% → 94.14% | +0.00 | 76.95% → 76.95% | +0.00 | 0/512 (0.00%) |
| income | 88.28% → 88.28% | +0.00 | 83.79% → 83.79% | +0.00 | 0/512 (0.00%) |
| balanced | 92.77% → 92.77% | +0.00 | 82.23% → 82.23% | +0.00 | 0/512 (0.00%) |

Published baseline and shortlist deltas are variant minus original, shown as raw / normalized. Flags locate slots in the displayed rotation.

| Published option | Water (mm unmet per slot) | Nitrogen (kg N/ha per slot) | Erosion (slope × rainfall proxy) | Climate Fit (historical share) | Income (relative index) | Risk (relative penalty) | Flag changes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| water saver | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| soil builder | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| income | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| balanced | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |

### Low input

Feasible canonical rotations **16,914 → 16,914**. Common 16,914, added 0, removed 0.

| Preset | Original leader (score) | Variant leader (score) | Changed | Original leader feasible / optimal | Rank ρ |
| --- | --- | --- | --- | --- | --- |
| water saver | green gram / fallow → green gram / fallow → green gram / fallow (0.746728) | green gram / fallow → green gram / fallow → green gram / fallow (0.739453) | no | yes / yes | 0.995592 |
| soil builder | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.755802) | pearl millet / common bean → pearl millet / common bean → pearl millet / common bean (0.748682) | yes | yes / no | 0.977163 |
| income | maize / green gram → maize / green gram → maize / green gram (0.707399) | maize / green gram → maize / green gram → maize / green gram (0.704924) | no | yes / yes | 0.998671 |
| balanced | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.739487) | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.732756) | no | yes / yes | 0.988882 |

| Preset | Top-two gap original → variant | Exact top ties original → variant | Near-top count original → variant | Entered / left | Top-two near-tie |
| --- | --- | --- | --- | --- | --- |
| water saver | 0.005711 → 0.004447 | 1 → 1 | 3 → 6 | 3 / 0 | no change |
| soil builder | 0.000785 → 0.002401 | 1 → 1 | 29 → 60 | 39 / 8 | no change |
| income | 0.001022 → 0.001385 | 1 → 1 | 42 → 69 | 28 / 1 | no change |
| balanced | 0.003566 → 0.003229 | 1 → 1 | 12 → 21 | 9 / 0 | no change |

| Preset | P22 change original → variant | Change (pp) | Material original → variant | Material change (pp) | Paired winners differ |
| --- | --- | --- | --- | --- | --- |
| water saver | 74.41% → 78.12% | +3.71 | 65.04% → 70.70% | +5.66 | 50/512 (9.77%) |
| soil builder | 94.14% → 89.45% | -4.69 | 76.95% → 78.32% | +1.37 | 178/512 (34.77%) |
| income | 88.28% → 89.45% | +1.17 | 83.79% → 84.38% | +0.59 | 39/512 (7.62%) |
| balanced | 92.77% → 93.95% | +1.17 | 82.23% → 84.77% | +2.54 | 83/512 (16.21%) |

Published baseline and shortlist deltas are variant minus original, shown as raw / normalized. Flags locate slots in the displayed rotation.

| Published option | Water (mm unmet per slot) | Nitrogen (kg N/ha per slot) | Erosion (slope × rainfall proxy) | Climate Fit (historical share) | Income (relative index) | Risk (relative penalty) | Flag changes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | +0.00000 / +0.00000 | +11.00000 / +0.04292 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| water saver | +0.00000 / +0.00000 | +0.00000 / -0.04850 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| soil builder | +0.00000 / +0.00000 | +0.00000 / -0.03959 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| income | +0.00000 / +0.00000 | +0.00000 / -0.02475 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| balanced | +0.00000 / +0.00000 | +0.00000 / -0.04256 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |

### Mid input

Feasible canonical rotations **16,914 → 16,914**. Common 16,914, added 0, removed 0.

| Preset | Original leader (score) | Variant leader (score) | Changed | Original leader feasible / optimal | Rank ρ |
| --- | --- | --- | --- | --- | --- |
| water saver | green gram / fallow → green gram / fallow → green gram / fallow (0.746728) | green gram / fallow → green gram / fallow → green gram / fallow (0.728371) | no | yes / yes | 0.987651 |
| soil builder | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.755802) | pearl millet / common bean → pearl millet / common bean → pearl millet / common bean (0.743706) | yes | yes / no | 0.935116 |
| income | maize / green gram → maize / green gram → maize / green gram (0.707399) | maize / green gram → maize / green gram → maize / green gram (0.701155) | no | yes / yes | 0.996449 |
| balanced | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.739487) | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.722504) | no | yes / yes | 0.968195 |

| Preset | Top-two gap original → variant | Exact top ties original → variant | Near-top count original → variant | Entered / left | Top-two near-tie |
| --- | --- | --- | --- | --- | --- |
| water saver | 0.005711 → 0.002260 | 1 → 1 | 3 → 8 | 5 / 0 | no change |
| soil builder | 0.000785 → 0.002638 | 1 → 1 | 29 → 13 | 13 / 29 | no change |
| income | 0.001022 → 0.000563 | 1 → 1 | 42 → 81 | 45 / 6 | no change |
| balanced | 0.003566 → 0.002717 | 1 → 1 | 12 → 51 | 40 / 1 | no change |

| Preset | P22 change original → variant | Change (pp) | Material original → variant | Material change (pp) | Paired winners differ |
| --- | --- | --- | --- | --- | --- |
| water saver | 74.41% → 79.69% | +5.27 | 65.04% → 74.22% | +9.18 | 83/512 (16.21%) |
| soil builder | 94.14% → 84.57% | -9.57 | 76.95% → 70.12% | -6.84 | 285/512 (55.66%) |
| income | 88.28% → 90.23% | +1.95 | 83.79% → 84.38% | +0.59 | 60/512 (11.72%) |
| balanced | 92.77% → 95.12% | +2.34 | 82.23% → 86.91% | +4.69 | 135/512 (26.37%) |

Published baseline and shortlist deltas are variant minus original, shown as raw / normalized. Flags locate slots in the displayed rotation.

| Published option | Water (mm unmet per slot) | Nitrogen (kg N/ha per slot) | Erosion (slope × rainfall proxy) | Climate Fit (historical share) | Income (relative index) | Risk (relative penalty) | Flag changes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | +0.00000 / +0.00000 | +20.00000 / +0.04895 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| water saver | +0.00000 / +0.00000 | +0.00000 / -0.12238 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| soil builder | +0.00000 / +0.00000 | +0.00000 / -0.09990 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| income | +0.00000 / +0.00000 | +0.00000 / -0.06244 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| balanced | +0.00000 / +0.00000 | +0.00000 / -0.10739 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |

### High input

Feasible canonical rotations **16,914 → 16,914**. Common 16,914, added 0, removed 0.

| Preset | Original leader (score) | Variant leader (score) | Changed | Original leader feasible / optimal | Rank ρ |
| --- | --- | --- | --- | --- | --- |
| water saver | green gram / fallow → green gram / fallow → green gram / fallow (0.746728) | fallow / common bean → fallow / common bean → fallow / common bean (0.720105) | yes | yes / no | 0.977466 |
| soil builder | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.755802) | pearl millet / common bean → pearl millet / common bean → pearl millet / common bean (0.739627) | yes | yes / no | 0.885643 |
| income | maize / green gram → maize / green gram → maize / green gram (0.707399) | maize / common bean → maize / common bean → maize / common bean (0.699961) | yes | yes / no | 0.993722 |
| balanced | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.739487) | pearl millet / common bean → pearl millet / common bean → pearl millet / common bean (0.715097) | yes | yes / no | 0.943148 |

| Preset | Top-two gap original → variant | Exact top ties original → variant | Near-top count original → variant | Entered / left | Top-two near-tie |
| --- | --- | --- | --- | --- | --- |
| water saver | 0.005711 → 0.000820 | 1 → 1 | 3 → 9 | 6 / 0 | no change |
| soil builder | 0.000785 → 0.002638 | 1 → 1 | 29 → 8 | 8 / 29 | no change |
| income | 0.001022 → 0.000632 | 1 → 1 | 42 → 59 | 27 / 10 | no change |
| balanced | 0.003566 → 0.001000 | 1 → 1 | 12 → 104 | 94 / 2 | no change |

| Preset | P22 change original → variant | Change (pp) | Material original → variant | Material change (pp) | Paired winners differ |
| --- | --- | --- | --- | --- | --- |
| water saver | 74.41% → 79.30% | +4.88 | 65.04% → 66.21% | +1.17 | 116/512 (22.66%) |
| soil builder | 94.14% → 79.69% | -14.45 | 76.95% → 64.65% | -12.30 | 356/512 (69.53%) |
| income | 88.28% → 61.72% | -26.56 | 83.79% → 51.76% | -32.03 | 72/512 (14.06%) |
| balanced | 92.77% → 91.41% | -1.37 | 82.23% → 82.42% | +0.20 | 175/512 (34.18%) |

Published baseline and shortlist deltas are variant minus original, shown as raw / normalized. Flags locate slots in the displayed rotation.

| Published option | Water (mm unmet per slot) | Nitrogen (kg N/ha per slot) | Erosion (slope × rainfall proxy) | Climate Fit (historical share) | Income (relative index) | Risk (relative penalty) | Flag changes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | +0.00000 / +0.00000 | +29.00000 / +0.05390 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| water saver | +0.00000 / +0.00000 | +0.00000 / -0.18295 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| soil builder | +0.00000 / +0.00000 | +0.00000 / -0.14935 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| income | +0.00000 / +0.00000 | +0.00000 / -0.09334 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |
| balanced | +0.00000 / +0.00000 | +0.00000 / -0.16055 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | +0.00000 / +0.00000 | No change |

The [P43 Kansas variants](literature_variant.md), [P44 consensus runs](consensus_shortlist.md), [P42 smoother](smooth_climate_fit.md), and published rotation shortlists use their original settings and results.

Rebuild the results with `python -m src.regional_scoring_variants` and this report with `python -m src.regional_scoring_report`. Both commands run offline.
