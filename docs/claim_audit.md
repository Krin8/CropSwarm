# P13 claim audit

| Topic | Change | Basis |
|---|---|---|
| US B water supply | README, talk track, climate panel and farm flags now identify the rainfed reference and zero irrigation supplied. The app labels non-reference irrigation values as scenario assumptions. The Kansas groundwater note now describes regional aquifer mapping without attributing irrigation or a decline to US B. | `config/farms.json`, Kansas Geological Survey regional map |
| Kansas fallow and spring greenness | README, talk track and the visible Kansas warning say the cause of the 2019 spring peak remains unexplained. The accompanying config warning now reflects the completed CDL neighborhood check. | `data/processed/validity_us_high_plains_b.json` |
| Makueni | README and talk track retain “cropland unverified.” The existing climate warning stays visible for the illustrative point. | `data/processed/validity_kenya_makueni_north.json` |
| Telangana | Talk track and app explicitly call the second season tentative. The config and decision log distinguish recovered 2022 downloads from limited quality-screened evidence. The repeated-paddy baseline warning stays visible. | `data/processed/coverage_p4.json`, `data/processed/validity_telangana_a.json` |
| Priority controls | Talk track and app describe updating scores for the displayed rotations. Preset win percentages use scenario draws and the selected named preset. | `app/main.py`, uncertainty files |
| Optimizer check | README, talk track and the app show the measured comparison between single-run and best-of-five ACO. | [Trial results](optimizer.md) |

Crop comparisons remain illustrative. Neither CDL nor the MODIS vegetation series supplies verified field management. Soil nitrogen and organic carbon require local soil evidence, and POWER soil wetness is modeled.
