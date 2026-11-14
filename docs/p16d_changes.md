# P16d results compared with P16c

All numbers here are **illustrative and need local validation**. The comparison uses only committed cached climate and model inputs. No scoring parameter, crop parameter, or metric definition changed. [Exact verification](optimizer.md), [robustness maps](stress_test.md), and [metric-level diagnosis](tie_diagnosis.md) contain the current results.

## Equivalence decision

For **every previously enumerated feasible rotation** at all three farms, shifting by one or two whole years preserved all six normalized scores to within `1e-12` numerical precision (floating-point test convention). A one-slot shift **did not** preserve scores in the two-season Telangana and Makueni farms, because crops move to different seasonal weather windows. Therefore only whole-year cyclic shifts are collapsed. The canonical representative is the lexicographically smallest whole-year shift. The baseline keeps its farmer-supplied order when displayed.

| Farm | Former raw feasible rotations | Canonical rotations | ACO exact-hit rates or gaps changed? | Displayed alternatives clearing the 0.05 metric threshold |
|---|---:|---:|---|---:|
| Kansas | 504 | 168 | No: all single and best-of-five runs still 30/30 hits, zero gap | 4 of 4 |
| Telangana | 633,998 | 211,394 | No: single 23–29/30 and best-of-five 30/30 across presets; same gaps | 4 of 4 |
| Makueni | 50,658 | 16,914 | No: single 21–29/30; best-of-five 29–30/30; same gaps | 4 of 4 |

The threshold is a **design choice, not empirical**. Every displayed alternative also differs from the baseline by more than 0.05 on at least one of the six normalized metric scores. Previously each farm displayed four named alternatives but only three distinct metric profiles. New candidates were chosen by the existing seeded ACO runs when they cleared the threshold, with exact canonical fallback otherwise. ACO settings were not tuned.

## Robustness map changes

These counts are grid cells whose top *label* differs from the unchanged-weather label, out of 35; they are not climate probabilities or field outcomes. The grid ranges are design choices. The new exact tie rule is lexicographically first canonical rotation, with baseline precedence on an exact tie.

| Farm | Preset | Changed-label cells before → after | Nearest changed cell before → after |
|---|---|---:|---|
| Kansas | Water saver | 15 → 15 | +2 °C, 0% rain → same |
| Kansas | Soil builder | 7 → 1 | 0 °C, +10% rain → +3 °C, +10% rain |
| Kansas | Income | 23 → 20 | 0 °C, +10% rain → +1.5 °C, 0% rain |
| Kansas | Balanced | 19 → 19 | +1 °C, +10% rain → same |
| Telangana | Water saver | 0 → 0 | No label change → same |
| Telangana | Soil builder | 2 → 2 | +3 °C, 0% rain → same |
| Telangana | Income | 12 → 12 | +1 °C, +10% rain → same |
| Telangana | Balanced | 1 → 1 | +3 °C, +10% rain → same |
| Makueni | Water saver | 12 → 12 | 0 °C, −30% rain → same |
| Makueni | Soil builder | 30 → 30 | 0 °C, −10% rain → same |
| Makueni | Income | 8 → 8 | 0 °C, −20% rain → same |
| Makueni | Balanced | 25 → 25 | 0 °C, +10% rain → same |

The **near-tie count remains 11 of 11 reported flips**; Telangana water saver still has no flip. Four Kansas before/after comparisons still have zero gap between two *noncyclic* orderings of the same crop set. Canonicalization removes redundant starting-year labels, but the simplified model can remain indifferent to the order of distinct annual crops. The earlier Kansas soil-builder and income nearest flips were label artifacts under seeded tie selection; the refreshed nearest changed cells involve different crop sets.

## Effects on displayed uncertainty

Because the four displayed alternatives changed, the seeded 500-draw uncertainty comparisons were regenerated with the **same** seed and assumptions. They describe the new candidate set; the baseline inputs and scoring method are unchanged. For example, under historical weather the Kansas baseline's water-saver win share changed from **0.8% to 1.8%**, its income win share from **1.2% to 0.6%**, and the Makueni baseline's income win share from **23% to 24%**. Telangana's baseline historical win shares stayed the same. All strategy/scenario values are in the three committed `data/processed/uncertainty_*.json` files. These differences reflect the comparison set, not new weather evidence.
