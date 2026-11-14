# P23 crop parameter sourcing

Baseline commit `3d32a61`. Catalog inputs and modeled outputs are illustrative and require local validation.

## Original assumption inventory

The inventory expands the shared thermal and rainfall source columns into the individual parameters they cover. “N/A” denotes a blank catalog field for bare fallow. The ranges and numerical inputs below come from the pre-P23 catalog.

- **fallow** (15) — `seasons_allowed` = `["cool","warm","monsoon","post_monsoon","long_rains","short_rains"]`, `season_length_days` = `0`, `water_need_mm` = `0`, `heat_tolerance_c` = `N/A`, `min_temp_c` = `N/A`, `max_temp_c` = `N/A`, `min_rain_mm` = `N/A`, `max_rain_mm` = `N/A`, `is_legume` = `false`, `n_credit_kg_ha` = `0`, `n_demand_kg_ha` = `0`, `cover_score` = `0`, `root_depth_class` = `none`, `relative_income_index` = `0`, `disease_family` = `none`.
- **winter_wheat** (13) — `seasons_allowed` = `["cool","post_monsoon"]`, `season_length_days` = `260`, `heat_tolerance_c` = `30`, `min_temp_c` = `8`, `max_temp_c` = `24`, `min_rain_mm` = `180`, `max_rain_mm` = `650`, `is_legume` = `false`, `n_credit_kg_ha` = `0`, `n_demand_kg_ha` = `90`, `cover_score` = `0.65`, `relative_income_index` = `0.65`, `disease_family` = `poaceae`.
- **sorghum** (12) — `seasons_allowed` = `["warm","monsoon","long_rains","short_rains"]`, `heat_tolerance_c` = `38`, `min_temp_c` = `17`, `max_temp_c` = `34`, `min_rain_mm` = `150`, `max_rain_mm` = `600`, `is_legume` = `false`, `n_credit_kg_ha` = `0`, `n_demand_kg_ha` = `75`, `cover_score` = `0.65`, `relative_income_index` = `0.58`, `disease_family` = `poaceae`.
- **paddy** (12) — `seasons_allowed` = `["monsoon","post_monsoon"]`, `heat_tolerance_c` = `35`, `min_temp_c` = `20`, `max_temp_c` = `33`, `min_rain_mm` = `200`, `max_rain_mm` = `1200`, `is_legume` = `false`, `n_credit_kg_ha` = `0`, `n_demand_kg_ha` = `110`, `cover_score` = `0.55`, `relative_income_index` = `0.78`, `disease_family` = `poaceae`.
- **maize** (12) — `seasons_allowed` = `["warm","monsoon","post_monsoon","long_rains","short_rains"]`, `heat_tolerance_c` = `35`, `min_temp_c` = `16`, `max_temp_c` = `32`, `min_rain_mm` = `200`, `max_rain_mm` = `850`, `is_legume` = `false`, `n_credit_kg_ha` = `0`, `n_demand_kg_ha` = `120`, `cover_score` = `0.65`, `relative_income_index` = `0.8`, `disease_family` = `poaceae`.
- **common_bean** (12) — `seasons_allowed` = `["warm","monsoon","post_monsoon","long_rains","short_rains"]`, `heat_tolerance_c` = `32`, `min_temp_c` = `15`, `max_temp_c` = `28`, `min_rain_mm` = `170`, `max_rain_mm` = `650`, `is_legume` = `true`, `n_credit_kg_ha` = `22`, `n_demand_kg_ha` = `20`, `cover_score` = `0.5`, `relative_income_index` = `0.67`, `disease_family` = `fabaceae`.
- **soybean** (12) — `seasons_allowed` = `["warm","monsoon"]`, `heat_tolerance_c` = `35`, `min_temp_c` = `17`, `max_temp_c` = `32`, `min_rain_mm` = `220`, `max_rain_mm` = `850`, `is_legume` = `true`, `n_credit_kg_ha` = `34`, `n_demand_kg_ha` = `15`, `cover_score` = `0.58`, `relative_income_index` = `0.73`, `disease_family` = `fabaceae`.
- **chickpea** (12) — `seasons_allowed` = `["cool","post_monsoon"]`, `heat_tolerance_c` = `32`, `min_temp_c` = `12`, `max_temp_c` = `27`, `min_rain_mm` = `90`, `max_rain_mm` = `500`, `is_legume` = `true`, `n_credit_kg_ha` = `25`, `n_demand_kg_ha` = `15`, `cover_score` = `0.45`, `relative_income_index` = `0.66`, `disease_family` = `fabaceae`.
- **pigeonpea** (13) — `seasons_allowed` = `["monsoon","long_rains"]`, `heat_tolerance_c` = `38`, `min_temp_c` = `18`, `max_temp_c` = `34`, `min_rain_mm` = `170`, `max_rain_mm` = `800`, `is_legume` = `true`, `n_credit_kg_ha` = `30`, `n_demand_kg_ha` = `15`, `cover_score` = `0.62`, `root_depth_class` = `deep`, `relative_income_index` = `0.63`, `disease_family` = `fabaceae`.
- **green_gram** (12) — `seasons_allowed` = `["monsoon","post_monsoon","long_rains","short_rains"]`, `heat_tolerance_c` = `36`, `min_temp_c` = `18`, `max_temp_c` = `33`, `min_rain_mm` = `140`, `max_rain_mm` = `600`, `is_legume` = `true`, `n_credit_kg_ha` = `20`, `n_demand_kg_ha` = `15`, `cover_score` = `0.48`, `relative_income_index` = `0.64`, `disease_family` = `fabaceae`.
- **pearl_millet** (12) — `seasons_allowed` = `["warm","monsoon","long_rains","short_rains"]`, `heat_tolerance_c` = `40`, `min_temp_c` = `18`, `max_temp_c` = `36`, `min_rain_mm` = `120`, `max_rain_mm` = `600`, `is_legume` = `false`, `n_credit_kg_ha` = `0`, `n_demand_kg_ha` = `45`, `cover_score` = `0.55`, `relative_income_index` = `0.52`, `disease_family` = `poaceae`.
- **sunflower** (12) — `seasons_allowed` = `["warm","monsoon","post_monsoon","long_rains"]`, `heat_tolerance_c` = `36`, `min_temp_c` = `14`, `max_temp_c` = `32`, `min_rain_mm` = `180`, `max_rain_mm` = `750`, `is_legume` = `false`, `n_credit_kg_ha` = `0`, `n_demand_kg_ha` = `65`, `cover_score` = `0.48`, `relative_income_index` = `0.65`, `disease_family` = `asteraceae`.
- **cowpea** (13) — `seasons_allowed` = `["monsoon","post_monsoon","long_rains","short_rains"]`, `water_need_mm` = `275`, `heat_tolerance_c` = `30`, `min_temp_c` = `20`, `max_temp_c` = `35`, `min_rain_mm` = `200`, `max_rain_mm` = `500`, `is_legume` = `true`, `n_credit_kg_ha` = `22`, `n_demand_kg_ha` = `12`, `cover_score` = `0.58`, `relative_income_index` = `0.58`, `disease_family` = `fabaceae`.
- **cereal_rye_cover** (15) — `seasons_allowed` = `["cool"]`, `season_length_days` = `100`, `water_need_mm` = `220`, `heat_tolerance_c` = `30`, `min_temp_c` = `4`, `max_temp_c` = `25`, `min_rain_mm` = `100`, `max_rain_mm` = `550`, `is_legume` = `false`, `n_credit_kg_ha` = `0`, `n_demand_kg_ha` = `0`, `cover_score` = `0.85`, `root_depth_class` = `medium`, `relative_income_index` = `0`, `disease_family` = `poaceae`.
- **field_pea** (12) — `seasons_allowed` = `["cool","post_monsoon"]`, `heat_tolerance_c` = `30`, `min_temp_c` = `8`, `max_temp_c` = `25`, `min_rain_mm` = `130`, `max_rain_mm` = `600`, `is_legume` = `true`, `n_credit_kg_ha` = `22`, `n_demand_kg_ha` = `15`, `cover_score` = `0.53`, `relative_income_index` = `0.52`, `disease_family` = `fabaceae`.

**Total: 189 individual parameters.**

## Changes to values and source labels

The botanical sources establish the plant family and legume status. The score penalty for successive crops in one family is still an assumed model rule.

| Crop | Parameter(s) | Old → new | Opened source and locator |
|---|---|---|---|
| winter_wheat | `disease_family`, `is_legume` | `poaceae`, `false` unchanged. Assumption → literature | [UMN Extension, Rotate crops, Plant families (Poaceae)](https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/living-soil-healthy-garden) |
| sorghum | `disease_family`, `is_legume` | `poaceae`, `false` unchanged. Assumption → literature | [UMN Extension, Rotate crops, Plant families (Poaceae)](https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/living-soil-healthy-garden) |
| paddy | `disease_family`, `is_legume` | `poaceae`, `false` unchanged. Assumption → literature | [USDA ARS GRIN Taxonomy, Oryza sativa subsp. sativa, Family (Poaceae)](https://npgsweb.ars-grin.gov/gringlobal/taxon/taxonomydetail?id=484525) |
| maize | `disease_family`, `is_legume` | `poaceae`, `false` unchanged. Assumption → literature | [UMN Extension, Rotate crops, Plant families (Poaceae)](https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/living-soil-healthy-garden) |
| common_bean | `disease_family`, `is_legume` | `fabaceae`, `true` unchanged. Assumption → literature | [UMN Extension, Rotate crops, Plant families (Fabaceae)](https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/living-soil-healthy-garden) |
| soybean | `disease_family`, `is_legume` | `fabaceae`, `true` unchanged. Assumption → literature | [USDA ARS GRIN Taxonomy, Glycine max subsp. max, Family (Fabaceae)](https://npgsweb.ars-grin.gov/gringlobal/taxon/taxonomydetail?id=487024) |
| chickpea | `disease_family`, `is_legume` | `fabaceae`, `true` unchanged. Assumption → literature | [Kew Plants of the World Online, Cicer arietinum, family heading (Fabaceae)](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:486336-1/general-information) |
| pigeonpea | `disease_family`, `is_legume` | `fabaceae`, `true` unchanged. Assumption → literature | [Kew Plants of the World Online, Cajanus cajan, family heading (Fabaceae)](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:1152177-2/general-information) |
| green_gram | `disease_family`, `is_legume` | `fabaceae`, `true` unchanged. Assumption → literature | [Kew Plants of the World Online, Vigna radiata, family heading (Fabaceae)](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:525492-1/general-information) |
| pearl_millet | `disease_family`, `is_legume` | `poaceae`, `false` unchanged. Assumption → literature | [Kew Plants of the World Online, Cenchrus americanus, family heading (Poaceae)](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:77105978-1/general-information) |
| sunflower | `disease_family`, `is_legume` | `asteraceae`, `false` unchanged. Assumption → literature | [UMN Extension, Rotate crops, Plant families (Asteraceae)](https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/living-soil-healthy-garden) |
| cowpea | `disease_family`, `is_legume` | `fabaceae`, `true` unchanged. Assumption → literature | [UMN Extension, Rotate crops, Plant families (Fabaceae)](https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/living-soil-healthy-garden) |
| cereal_rye_cover | `disease_family`, `is_legume` | `poaceae`, `false` unchanged. Assumption → literature | [USDA ARS GRIN Taxonomy, Secale cereale, Family (Poaceae)](https://npgsweb.ars-grin.gov/gringlobal/taxon/taxonomydetail?id=317600) |
| field_pea | `disease_family`, `is_legume` | `fabaceae`, `true` unchanged. Assumption → literature | [UMN Extension, Rotate crops, Plant families (Fabaceae)](https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/living-soil-healthy-garden) |
| cowpea | `water_need_mm` | 275 → 284.8. Assumption → literature | [Patil (2010), MAUSAM p. 567 Table 1, Bangalore kharif actual ET (281.6–288.0 mm, midpoint 284.8); illustrative regional transfer, validate locally](https://mausamjournal.imd.gov.in/index.php/MAUSAM/article/download/914/760/3269) |
| pigeonpea | `root_depth_class` | deep → deep. Assumption → literature | [FAO/IIASA GAEZ v5 Soil suitability assessment Table A3.1 p. 39 (1.0–2.0 m, midpoint 1.5 m; deep by catalog rule)](https://pure.iiasa.ac.at/id/eprint/21525/1/cd8206en.pdf) |

Cowpea uses the midpoint of two observed Bangalore kharif ET totals as an illustrative crop water-use reference. The trial used gravimetric lysimeters under the local recommended practices. The range is interannual observation, not a field-specific demand bound for Telangana or Kenya. The Sennar and Abu Naama CROPWAT estimates were higher and varied between years and sites. That comparison illustrates why the transferred value still needs validation. [Patil, pp. 565 and 567, Table 1](https://mausamjournal.imd.gov.in/index.php/MAUSAM/article/download/914/760/3269) · [Mohamoud et al., pp. 25–27, Tables 3–4](https://onlinejournals.uofk.edu/sjdr/en/article/download/1453/1281)

## Source checks for retained assumptions


Each group below applies to every row carrying that original assumption source, except for the replacements listed above.

- **Calendar slots and duration.** FAO-56 Table 11 gives location-specific growing periods and footnote 2 explains how winter-wheat dormancy changes them. K-State C529 Figure 1 gives planting dates by Kansas zone but does not establish a 260-day duration. FAO Kenya Table 4.11 reports crop cycle ranges. SARE’s Cereal Rye Management section describes flexible seeding and termination, with no fixed 100-day cover period. The Kenya extension handbook Table 5.14 confirms Machakos 66’s existing maturity reference, but these sources do not establish the model’s farm-specific slot lists or the two assumed durations. Fallow is a model slot with no planted crop, not a botanical classification. [FAO-56 Table 11](https://www.fao.org/4/x0490e/x0490e0b.htm) · [K-State C529, Figure 1](https://bookstore.ksre.ksu.edu/pubs/wheat-production-handbook_C529.pdf) · [FAO Kenya Table 4.11](https://www.fao.org/4/t0733e/T0733E05.htm) · [SARE Cereal Rye](https://www.sare.org/publications/managing-cover-crops-profitably/nonlegume-cover-crops/cereal-rye/) · [Kenya handbook, Tables 5.13–5.14](https://statistics.kilimo.go.ke/files/bookpage/KENYA_Farmers-Extension-Handbook.pdf)
- **Seasonal mean temperature and daily heat thresholds.** GAEZ v4 uses accumulated temperature and counts by daily mean temperature class (p. 33, Table 3-2). The older FAO irrigation land evaluation guide uses crop-group photosynthesis optima (Tables 32–33). The Kenyan handbook’s cowpea ecology table does not specify the model’s full-window mean and daily maximum conventions. ICRISAT’s pigeonpea climate section gives ranges for climates where pigeonpea is grown, with separate rainy- and post-rainy-season values. None of these sources verifies the catalog’s combined full-window limits and daily peak triggers. [GAEZ v4, p. 33 and Table 3-2](https://gaez-v4-data.fao.org/data/documentation/GAEZ%20v4%20Model%20Documentation.pdf) · [FAO agronomic factors, Tables 32–33](https://www.fao.org/4/x5648e/x5648e0e.htm) · [Kenya handbook, Table 5.13](https://statistics.kilimo.go.ke/files/bookpage/KENYA_Farmers-Extension-Handbook.pdf) · [ICRISAT pigeonpea, Climate, p. 13](https://oar.icrisat.org/2422/1/Pigeonpea-Botany-Production-Practices.pdf)
- **Seasonal rain and remaining water need.** FAO Tables 6 and 14 describe crop durations and evapotranspiration. FAO’s irrigation chapter §4.2 distinguishes total rainfall from effective rainfall. The Kenya cowpea handbook gives ecological rainfall, with no definition that matches this model’s crop-window rainfall bounds. SARE reports management-dependent moisture depletion under rye but does not establish the 220 mm total for the modeled cover period. The zero water requirement for bare fallow represents zero crop demand in the model, while real soil can still evaporate water. [FAO crop water needs, Tables 6 and 14](https://www.fao.org/4/s2022e/s2022e07.htm) · [FAO irrigation water needs, §4.2](https://www.fao.org/4/s2022e/s2022e08.htm) · [SARE Cereal Rye, Management](https://www.sare.org/publications/managing-cover-crops-profitably/nonlegume-cover-crops/cereal-rye/)
- **Nitrogen credit and demand.** Minnesota Extension Table 1 confirms the original soybean, edible bean and field pea reference credits for first-year corn. The engine transfers each tabulated credit to any following crop and farm. The Minnesota corn fertilizer guidance varies rates with soil and previous crop and cannot establish the unconditional crop-demand inputs. The model’s generic no-credit entries also do not establish measured residual nitrogen. [Minnesota soil biology, Table 1](https://extension.umn.edu/natural-resources/conservation/agricultural-soil-and-water/soil-biology) · [Minnesota corn fertilizer guidance, Table 1 and soil nitrate section](https://extension.umn.edu/agriculture/crop-production/nutrient-management-for-minnesota-crops/fertilizing-corn-in-minnesota)
- **Erosion cover proxy.** FAO Kenya Tables 4.11–4.15 describe crop stage, canopy and cover effects. USDA RUSLE Chapter 4 p. 17 reports different subfactors for canopy, surface cover, land use, roughness and moisture. Neither gives this app’s single seasonal cover score for each crop and practice. SARE documents rye’s protective cover qualitatively. [FAO Kenya Tables 4.11–4.15](https://www.fao.org/4/t0733e/T0733E05.htm) · [USDA RUSLE Chapter 4, p. 17](https://efotg.sc.egov.usda.gov/references/Agency/OK/RUSLE_Chap4_C_Factors.pdf)
- **Root depth.** FAO-56 Table 22 covers maximum effective depths for mature crops. GAEZ v5 Table A3.1 gives hibernating and other mature rye ranges. Neither describes root depth at the selected cover-crop termination date. Fallow has no crop root depth. The published pigeonpea range is recorded with its midpoint and the catalog’s design rule for assigning a class. Root-depth class is descriptive metadata in the current engine. [FAO-56 Table 22](https://www.fao.org/4/x0490e/x0490e0e.htm) · [FAO/IIASA GAEZ v5 Table A3.1, pp. 37–39](https://pure.iiasa.ac.at/id/eprint/21525/1/cd8206en.pdf)
- **Income index.** K-State’s non-irrigated crop budgets offer crop- and rotation-specific enterprise estimates. They do not establish the global unitless income scale used in CropSwarm. The fallow and rye-cover zero-sale values remain scenario decisions. [K-State non-irrigated crop budget overview and regional tables](https://agmanager.info/farm-budgets/2025-farm-management-guides-non-irrigated-crops)
- **Fallow family and legume flag.** The plant-family references describe species. For the unplanted fallow slot, `none` and `false` remain model conventions.

The legacy KALRO manual and ICRISAT Table 10.7 direct links did not re-open through the browser during P23. Their previous verified references remain in the catalog, with the access history in the [P13 citation audit](citation_audit.md). The Kenyan ministry handbook independently confirmed the cowpea maturity range. No new P23 source label relies on the two inaccessible links.

## Rebuild results

Rebuilt the historical scoring inputs, exact search and seeded ACO, Monte Carlo uncertainty, robustness grid and margins, tie diagnostics, vegetation and yield back-tests, app settings and evidence ledgers. All model outputs are illustrative and need local validation. The figures below compare checked-in artifacts with the pre-P23 commit. Wall-clock timings are excluded from numerical comparisons.

### Displayed strategies, scores and uncertainty

All 15 displayed sequences, metric values and scores, preset rankings, scenario ranges, win shares, regret and sensitivity values matched the previous run. The three canonical feasible counts remain 168, 211,394 and 16,914. All 12 exact reference optimum scores matched. The P15 vegetation and P20 yield back-tests also reproduced their previous outputs.

Cowpea’s modeled mean unmet water demand changed in all three farms’ precomputed weather windows. The Kansas cool window is a counterfactual precompute since cowpea is ineligible for that slot. None of the displayed strategies contains cowpea.

| Farm and window | Old → new mean unmet demand for cowpea (mm) |
|---|---:|
| Kansas cool, ineligible | 206.89 → 216.51 |
| Telangana monsoon | 11.90 → 12.93 |
| Telangana post-monsoon | 99.01 → 102.89 |
| Makueni long rains | 88.70 → 96.03 |
| Makueni short rains | 88.83 → 96.82 |

### Robustness rankings and near-ties

- At Makueni, water saver, +0 °C / −30% rain, the winning rotation is still fallow then cowpea, repeated across all three years. Its exact weighted score fell from 0.70509145 to 0.70239631.
- At Makueni, water saver, +0.5 °C / −30% rain, green gram then fallow, repeated across all three years, replaced fallow then cowpea. The exact weighted score at that cell changed from 0.70288557 to 0.70122692. This was the only winner label change among the 420 grid cells across farms and presets. Makueni water saver now changes winner relative to historical weather in 11 of 35 cells, previously 12 of 35.
- The nearest Makueni water-saver change is still +0 °C / −30% rain. The preceding +0 °C / −20% rain margin changed from 0.00298428 to 0.00492650, and the first changed cell’s margin from 0.00221868 to 0.00116940. Both runner-up rotations changed. See the updated metric-level [tie diagnosis](tie_diagnosis.md). All 11 reported flips still meet the existing near-tie tolerance.

### ACO verification

Each rate is out of 30 trials. The list includes all changes in hits or summary gaps. Best gaps remained zero in all groups.

| Farm and preset | Run | Exact hits old → new | Mean gap old → new | Worst gap old → new |
|---|---|---:|---:|---:|
| kenya_makueni_north / water_saver | Single | 21 → 22 | 0.001713326 → 0.001695792 | 0.005711087 → 0.010896153 |
| kenya_makueni_north / soil_builder | Single | 26 → 26 | 0.000159995 → 0.000267642 | 0.002444211 → 0.002444211 |
| kenya_makueni_north / soil_builder | Best of five | 29 → 30 | 0.000026174 → 0.000000000 | 0.000785210 → 0.000000000 |
| kenya_makueni_north / income | Single | 29 → 30 | 0.000034081 → 0.000000000 | 0.001022430 → 0.000000000 |

86 individual seeded scores changed by more than 1e-12. The [seed-level comparison](p23_aco_trials.csv) lists every such result. This tolerance excludes machine-precision differences. Current full results are recorded in the [optimizer report](optimizer.md) and processed strategy files.

### Evidence grades

The family input in risk changed from assumption to literature for each planted crop. The literature share rises by the corresponding decrease in assumption share. The cowpea water reference is graded as literature whenever used, but cowpea is absent from the 15 displayed rotations. Legume flags and root-depth classes have no direct score dependency. All 90 metric labels and 15 overall strategy labels are still low.

| Farm | Displayed strategy | Risk literature share old → new |
|---|---|---:|
| kenya_makueni_north | baseline | 20.0% → 40.0% |
| kenya_makueni_north | water_saver | 10.0% → 20.0% |
| kenya_makueni_north | soil_builder | 20.0% → 40.0% |
| kenya_makueni_north | income | 20.0% → 40.0% |
| kenya_makueni_north | balanced | 16.7% → 33.3% |
| telangana_a | baseline | 20.0% → 40.0% |
| telangana_a | water_saver | 10.0% → 20.0% |
| telangana_a | soil_builder | 10.0% → 20.0% |
| telangana_a | income | 20.0% → 40.0% |
| telangana_a | balanced | 10.0% → 20.0% |
| us_high_plains_b | baseline | 6.7% → 20.0% |
| us_high_plains_b | water_saver | 13.3% → 26.7% |
| us_high_plains_b | soil_builder | 6.7% → 20.0% |
| us_high_plains_b | income | 20.0% → 40.0% |
| us_high_plains_b | balanced | 6.7% → 20.0% |

### Submission materials and screenshots

- The README and demo talk track now give 30 of 30 exact hits for best of five in every farm and preset. Single-run results still span 21–30 of 30. Update any external optimizer slide that gives the old 29–30 range.
- The submission summary’s crop catalog row now distinguishes sourced taxonomy and water use from values that need local calibration. Slides that show the Makueni water-saver map or its winner count should use 11 of 35. Slides that show the evidence ledger should use the new risk shares. The report found no slide deck in the repository. The tracked slide outline is in [the demo guide](demo.md).
- Regenerated all 18 [app screenshots](screenshots/README.md). Nine files differ: comparison, evidence, robustness and validation for Makueni, comparison, evidence and validation for Telangana, and evidence and validation for Kansas. The remaining nine matched the earlier PNGs byte-for-byte.
