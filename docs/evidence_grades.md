# Evidence grades for modeled scores

These grades describe **provenance and unresolved validation gaps**, not the probability that a rotation will work. All numbers and strategies remain illustrative and need local validation. The per-strategy, per-metric input ledger and shares are in `data/processed/strategies_<farm_id>.json`; the rule and thresholds are in [evidence_grades.json](../config/evidence_grades.json). The labels do not change scoring, optimizer ranks, or scenario draws.

## Grades and direct inputs

| Grade | What it means in this application |
|---|---|
| `nasa_measured` | Cached NASA POWER gridded precipitation and temperatures. These are gridded products, not on-farm gauges. MODIS NDVI is an observed input to season diagnostics and the back-test, but not a direct numeric input to a score. |
| `nasa_modeled` | The slope calculated from NASA SRTM elevations. POWER root-zone wetness is modeled and appears in climate diagnostics, but does not enter any of the six scores. |
| `external_measured` | USDA SSURGO mapped soil capacity in Kansas and ISRIC SoilGrids soil capacity in Telangana and Makueni. **SoilGrids is a model prediction**, despite this requested external-data bucket. USDA CDL maps the Kansas baseline class history, but does not enter alternative scores. |
| `literature` | A crop parameter linked to a source marked *opened-and-supports* in the [P13 citation audit](citation_audit.md) or [P23 source audit](p23_changes.md), without an explicit `assumption, validate locally` qualifier. A selected midpoint or representative value is still illustrative, not locally observed. |
| `assumption` | A crop field marked `assumption, validate locally`, an uncited crop field, farm irrigation or season choice, scoring rule, or parameter from [scoring.json](../config/scoring.json). A citation with an explicit assumption qualifier stays in this grade. |

Every active dependency is recorded with its field name, source, grade and weight. The direct-input lists are also defined in [`src/evidence.py`](../src/evidence.py): water uses POWER rainfall, soil capacity, crop water need and duration, irrigation, the season calendar and the daily bucket rule; nitrogen uses crop N credits and demand and their normalization; erosion uses POWER rainfall, SRTM slope, cover and the simplified proxy; climate fit uses POWER rainfall and two temperatures, crop limits and duration, the season calendar, heat policy and screening rule; income uses the relative income index; risk uses crop family, bare-slot duration, two policy weights and the proxy rule. **Root depth, POWER wetness and MODIS NDVI do not directly enter these six scores**. NDVI is used to derive or check seasons and in the back-test; its observational grade does not inflate score shares.

## Share and label rule

Each listed direct input field or scoring rule receives equal weight within its metric. For a crop-specific field, that weight is split evenly over the rotation's crop slots; each slot takes the grade of its own source. Summing these weights by grade gives shares that total 1. This is a transparent **dependency-count proxy**, not a causal allocation of the nonlinear, sometimes clipped score. Equal weighting and the cutoffs below are **design choices, not empirical estimates**.

- **High:** assumption share at most 0.10 and combined other-grade share at least 0.75.
- **Medium:** assumption share at most 0.34 and combined other-grade share at least 0.50.
- **Low:** otherwise.

The thresholds are applied before site validation caps. The overall strategy label is the **lowest of its six metric labels**, so one weak component cannot be masked by another. These rules deliberately make high difficult to reach; none of the current reference strategies is high or medium overall.

## Validation caps

The 2019–2023 [back-test](backtest.md) compares modeled water and heat stress with QA-filtered MODIS NDVI. It is a farm-level check of the baseline, **not** evidence that an alternative crop sequence will perform. It caps only water and climate-fit labels: zero assessable directional comparisons or fewer than half directionally consistent caps at **low**; otherwise a largest seasonal sample below eight caps at **medium**. Eight and one-half are design choices. Kansas has **0 assessable** comparisons, Telangana has **1 of 1** but its largest seasonal sample is **3**, and Makueni has **4 of 6** with largest seasonal sample **5**. All are small samples; correlations and intervals are in the back-test file.

The unexplained Kansas spring NDVI peak over CDL fallow and Telangana's tentative second season cap water and climate fit at **low**. Makueni's MCD12Q1 grassland classification conflicts with the intended cropland use, so all six metric labels are capped at **low** until the point is field-verified. SoilGrids water capacity caps water at **medium** because it is a modeled prediction. These caps never increase a label.

## Current result

All five displayed strategies per farm, including the baseline, have **low** overall evidence. All six metrics are **low** for every displayed strategy: even erosion depends on an assumed cover score and simplified proxy, while the NASA rainfall and SRTM slope account for only half of its dependency ledger. Makueni also has the unverified cropland cap. These labels are conservative descriptions of the current evidence, not a comparison of farm performance. Full individual shares and reasons are next to each metric in the app and in the checked-in strategy JSON.
