# Plain wording, local names and local units

The app has two layers. The farmer view comes first and uses everyday words. The technical checks sit behind the **Show technical checks (for reviewers)** switch. Wording and unit choices change the display only. Scores, rankings and cached results are the same in every language and unit.

All local wording is a **draft, validate locally**. Have a local speaker and an extension officer review the Telugu and Kiswahili text, the local crop names and the season names before farmers rely on them.

## What each farm shows

| Farm | Languages | Local units | Season names |
|---|---|---|---|
| US High Plains B | English | acre, inch, lb/acre | Fall-planted (winter) season, summer season |
| Telangana A | English, Telugu | acre, mm, kg/acre | Kharif (Vanakalam), Rabi (Yasangi) |
| Makueni North | English, Kiswahili | acre, mm, kg/acre | Long rains (Masika), short rains (Vuli) |

English is the default language. Local units are the default, with a switch to metric (ha, mm, kg/ha). Season names show the months the model uses for that season, taken from `data/processed/seasons_<farm_id>.json`. Local crop names appear beside the catalog name, for example “Paddy rice (వరి)”.

## What is translated

- The tagline, section headings, comparison table headings, preset names and the closing message.
- The six measures and a one-sentence meaning for each. The same sentence is the help text on each priority slider.
- Rotation warnings, such as the same crop grown twice in a row.
- The “What do these words mean?” glossary: rotation, fallow, score, best in test runs, low / typical / high, shortfall from the best option, evidence label, irrigation share, soil water, scenario, NASA POWER and satellite greenness.

Captions, source notes, site warnings, the climate charts and every technical panel stay in English. Untranslated text falls back to English.

## What is converted

- Water shortage: mm to inches where the farm uses inches.
- Nitrogen balance: kg/ha to kg/acre or lb/acre.
- Farm size and the soil-water input in the edit form. Edited values are converted back to metric before the model runs. An untouched soil value keeps the exact reference figure.

The climate charts and the record details stay in mm and °C. Income remains a 0–1 comparison index. It is not converted to rupees, shillings or dollars because the catalog holds no prices.

## Where the wording lives

`config/locales.json` holds the farm settings, the translated text, the glossary and the reviewer glossary. `src/localize.py` validates it and serves it to the app. `python -m src.app_assets` copies it into `data/processed/app_settings.json`, so the offline app needs no configuration directory at runtime.

Validation fails the build when a farm has no entry, a unit is unknown, a local crop name is missing or points at an unknown crop, or a measure, preset, warning or glossary entry lacks wording in a language that a farm offers.

## Add or change a language

1. Add the language to `languages` and set it as the farm's `language` in `config/locales.json`.
2. Add that language to every entry under `metrics`, `presets`, `flags` and `glossary`, and add local names for every crop in the catalog and for the farm's seasons.
3. Translate entries under `text` as far as you can. Missing ones fall back to English.
4. Run `python -m src.app_assets` and `python -m pytest -q`.
