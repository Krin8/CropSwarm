# Smooth climate-fit what-if (P42)

[Preregistration](p42_plan.md) was finalized in `be32ce5` before evaluation. [Saved comparison](../data/processed/smooth_climate_fit_p42.json).

The heat score declines smoothly within **±5 hot days** of the original cutoff. The band and its shape are design choices inspired by gradual heat responses in P41's ridge curves, with no fitting to those curves. Rainfall and mean-temperature gates still apply. Inputs come from NASA POWER and the crop catalog. [P41 response curves](ml_model.md#p41-scoring-versus-county-yield-response)

**1 of 12** nominal leaders changed. Rank Spearman ρ ranged from **0.9972 to 0.9998** across estimable cases. The top-two near-tie was created in **0** cases and resolved in **0**. There were **36 entries and 2 exits** from near-top sets across farm–preset cases. **0 of 15** published options moved by more than 0.1 climate-fit points (**0.0%**).

Near-top sets count all feasible canonical rotations within 0.01 weighted points of first, including the winner. The original and smooth rankings use identical canonical pools. Exact top ties use the existing numerical tolerance. All results are illustrative and need local validation.

P22 replay uses 512 paired draws per farm and seed 42. Each change rate compares a draw's winner with its own specification's nominal P22 winner. The paired-difference column compares the two winners directly on identical draws. A winner change counts as material if the reference is ineligible or its weighted gap exceeds the near-tie tolerance. A flagged baseline remains visible and eligible for comparison under P22's original convention. The replay reproduced the saved original winner histograms, change rates and material-change rates. These frequencies describe the chosen assumption ranges. [P22 assumptions](sensitivity.md)

## US High Plains B

168 feasible canonical rotations over 3 years for each preset.

| Preset | Original leader (score) | Smooth leader (score) | Leader changed | Old leader still optimal | Rank Spearman ρ |
| --- | --- | --- | --- | --- | --- |
| water saver | fallow → sorghum → soybean (0.683723) | fallow → sorghum → soybean (0.682612) | no | yes | 0.999670 |
| soil builder | fallow → soybean → cereal rye cover (0.715755) | fallow → soybean → cereal rye cover (0.715533) | no | yes | 0.999469 |
| income | sorghum → soybean → sunflower (0.641364) | sorghum → soybean → sunflower (0.640102) | no | yes | 0.999773 |
| balanced | fallow → sorghum → soybean (0.678125) | fallow → sorghum → soybean (0.676865) | no | yes | 0.999289 |

| Preset | Top-two gap original → smooth | Exact top ties original → smooth | Near-top count original → smooth | Entered | Left | Top-two near-tie change |
| --- | --- | --- | --- | --- | --- | --- |
| water saver | 0.000000 → 0.000000 | 2 → 2 | 4 → 4 | 0 | 0 | none |
| soil builder | 0.000000 → 0.000000 | 2 → 2 | 4 → 4 | 0 | 0 | none |
| income | 0.000000 → 0.000000 | 2 → 2 | 2 → 2 | 0 | 0 | none |
| balanced | 0.000000 → 0.000000 | 2 → 2 | 2 → 2 | 0 | 0 | none |

| Preset | P22 change original → smooth | Change (pp) | P22 material original → smooth | Material change (pp) | Different winners on matched draws |
| --- | --- | --- | --- | --- | --- |
| water saver | 85.94% → 86.33% | +0.39 | 77.73% → 76.95% | -0.78 | 14/512 (2.73%) |
| soil builder | 76.37% → 75.98% | -0.39 | 58.98% → 59.38% | +0.39 | 19/512 (3.71%) |
| income | 92.58% → 92.58% | +0.00 | 86.52% → 86.52% | +0.00 | 36/512 (7.03%) |
| balanced | 87.11% → 86.91% | -0.20 | 79.10% → 78.91% | -0.20 | 19/512 (3.71%) |

Published baseline and shortlist · **0 of 5 (0.0%)** changed by more than 0.1 climate-fit points.

| Published strategy | Original climate fit | Smooth climate fit | Change |
| --- | --- | --- | --- |
| baseline | 0.766387 | 0.742500 | -0.023887 |
| water saver | 0.619048 | 0.611640 | -0.007407 |
| soil builder | 0.450700 | 0.448474 | -0.002226 |
| income | 0.333333 | 0.324921 | -0.008412 |
| balanced | 0.499720 | 0.486788 | -0.012932 |

## Telangana A

211,394 feasible canonical rotations over 3 years for each preset.

| Preset | Original leader (score) | Smooth leader (score) | Leader changed | Old leader still optimal | Rank Spearman ρ |
| --- | --- | --- | --- | --- | --- |
| water saver | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.801544) | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.800088) | no | yes | 0.998371 |
| soil builder | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.770346) | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.769376) | no | yes | 0.999461 |
| income | pigeonpea / maize → pigeonpea / maize → pigeonpea / maize (0.672979) | soybean / maize → soybean / maize → soybean / maize (0.672976) | yes | no | 0.998150 |
| balanced | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.741856) | pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow (0.740206) | no | yes | 0.997157 |

| Preset | Top-two gap original → smooth | Exact top ties original → smooth | Near-top count original → smooth | Entered | Left | Top-two near-tie change |
| --- | --- | --- | --- | --- | --- | --- |
| water saver | 0.008222 → 0.005959 | 1 → 1 | 3 → 2 | 0 | 1 | none |
| soil builder | 0.004286 → 0.002777 | 1 → 1 | 3 → 5 | 2 | 0 | none |
| income | 0.000573 → 0.000484 | 1 → 1 | 56 → 87 | 31 | 0 | none |
| balanced | 0.008115 → 0.005550 | 1 → 1 | 2 → 2 | 0 | 0 | none |

| Preset | P22 change original → smooth | Change (pp) | P22 material original → smooth | Material change (pp) | Different winners on matched draws |
| --- | --- | --- | --- | --- | --- |
| water saver | 78.91% → 79.30% | +0.39 | 71.09% → 70.90% | -0.20 | 14/512 (2.73%) |
| soil builder | 77.73% → 77.54% | -0.20 | 66.41% → 66.41% | +0.00 | 3/512 (0.59%) |
| income | 96.48% → 87.89% | -8.59 | 92.77% → 79.49% | -13.28 | 16/512 (3.12%) |
| balanced | 81.64% → 81.45% | -0.20 | 75.39% → 75.39% | +0.00 | 9/512 (1.76%) |

Published baseline and shortlist · **0 of 5 (0.0%)** changed by more than 0.1 climate-fit points.

| Published strategy | Original climate fit | Smooth climate fit | Change |
| --- | --- | --- | --- |
| baseline | 0.085714 | 0.096800 | +0.011086 |
| water saver | 0.728571 | 0.718864 | -0.009707 |
| soil builder | 0.666667 | 0.672046 | +0.005380 |
| income | 0.228571 | 0.218864 | -0.009707 |
| balanced | 0.761905 | 0.747490 | -0.014414 |

## Makueni North Candidate

16,914 feasible canonical rotations over 3 years for each preset.

| Preset | Original leader (score) | Smooth leader (score) | Leader changed | Old leader still optimal | Rank Spearman ρ |
| --- | --- | --- | --- | --- | --- |
| water saver | green gram / fallow → green gram / fallow → green gram / fallow (0.746728) | green gram / fallow → green gram / fallow → green gram / fallow (0.746728) | no | yes | 0.999441 |
| soil builder | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.755802) | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.755802) | no | yes | 0.999643 |
| income | maize / green gram → maize / green gram → maize / green gram (0.707399) | maize / green gram → maize / green gram → maize / green gram (0.707399) | no | yes | 0.999562 |
| balanced | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.739487) | green gram / pearl millet → green gram / pearl millet → green gram / pearl millet (0.739487) | no | yes | 0.998590 |

| Preset | Top-two gap original → smooth | Exact top ties original → smooth | Near-top count original → smooth | Entered | Left | Top-two near-tie change |
| --- | --- | --- | --- | --- | --- | --- |
| water saver | 0.005711 → 0.005711 | 1 → 1 | 3 → 3 | 0 | 0 | none |
| soil builder | 0.000785 → 0.000785 | 1 → 1 | 29 → 29 | 0 | 0 | none |
| income | 0.001022 → 0.001022 | 1 → 1 | 42 → 45 | 3 | 0 | none |
| balanced | 0.003566 → 0.003566 | 1 → 1 | 12 → 11 | 0 | 1 | none |

| Preset | P22 change original → smooth | Change (pp) | P22 material original → smooth | Material change (pp) | Different winners on matched draws |
| --- | --- | --- | --- | --- | --- |
| water saver | 74.41% → 74.61% | +0.20 | 65.04% → 65.82% | +0.78 | 7/512 (1.37%) |
| soil builder | 94.14% → 93.75% | -0.39 | 76.95% → 77.15% | +0.20 | 10/512 (1.95%) |
| income | 88.28% → 88.28% | +0.00 | 83.79% → 83.98% | +0.20 | 7/512 (1.37%) |
| balanced | 92.77% → 92.77% | +0.00 | 82.23% → 81.84% | -0.39 | 5/512 (0.98%) |

Published baseline and shortlist · **0 of 5 (0.0%)** changed by more than 0.1 climate-fit points.

| Published strategy | Original climate fit | Smooth climate fit | Change |
| --- | --- | --- | --- |
| baseline | 0.535714 | 0.540479 | +0.004765 |
| water saver | 0.914286 | 0.914286 | +0.000000 |
| soil builder | 0.855462 | 0.855462 | +0.000000 |
| income | 0.668067 | 0.668067 | +0.000000 |
| balanced | 0.875070 | 0.875070 | +0.000000 |

The swap measures how the score responds to one modeling choice. Field heat responses and rotation suitability remain untested. The [published P44 consensus](consensus_shortlist.md) describes the configurations tested at the time.

Rebuild the separate audit offline with `python -m src.smooth_climate_fit`.
