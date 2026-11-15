# P52b size and trim analysis

This is analysis only. No further files were removed. The fresh clone at `/private/tmp/cropswarm-p52b-clone` used the existing repository `.venv` interpreter without installing packages. Its pip freeze matched every pinned requirement exactly, all 306 tests passed, and Streamlit AppTest loaded all three farms, the Evidence ledger, and each farm's applicable Validation panels without exceptions. The local Markdown link check found 60 documents, 472 resolving local links, and 30 PNGs. This does not establish that a new venv can install dependencies without a package source.

## Tracked size by top-level group

| Group | MiB |
| --- | ---: |
| `data/` | 96.38 |
| `docs/` | 8.20 |
| `src/` | 0.66 |
| `tests/` | 0.23 |
| `app/` | 0.13 |
| `scripts/` | 0.05 |
| `config/` | 0.01 |
| Root files and settings | less than 0.03 |

The per-file list below uses exact tracked-file sizes from the fresh clone and searches code, tests, scripts and Markdown for readers and links. A generated result may be intentionally retained as audit evidence even when no runtime reader appears.

| Tracked file | MiB | Reader / link | Category |
| --- | ---: | --- | --- |
| `data/processed/climate_yield_interval_predictions.csv` | 7.56 | `src/yield_intervals.py`, `src/interval_diagnosis.py` | app/test/rebuild reader |
| `data/raw/p31/Shapefile.rar` | 3.18 | `src/india_yield_screen.py`, `docs/cleanup_manifest.md` | app/test/rebuild reader |
| `data/processed/climate_yield_transfer_predictions.csv` | 3.10 | `src/cross_state_yield.py`, `src/yield_intervals.py` | app/test/rebuild reader |
| `data/processed/consensus_shortlist_p44b_telangana_a.csv.gz` | 1.70 | `docs/cleanup_manifest.md`, `docs/consensus_shortlist_p44b.md` | doc link only |
| `data/processed/consensus_shortlist_p44_telangana_a.csv.gz` | 1.70 | `docs/cleanup_manifest.md`, `docs/consensus_shortlist.md` | doc link only |
| `data/raw/p31/Data.csv` | 1.30 | `src/india_yield_screen.py`, `docs/cleanup_manifest.md` | app/test/rebuild reader |
| `data/raw/p2_evidence/p2_evidence.json` | 1.28 | `src/data_pipeline.py`, `src/farm_validity.py` | app/test/rebuild reader |
| `data/processed/sensitivity_telangana_a.json` | 1.02 | `docs/cleanup_manifest.md`, `docs/sensitivity.md` | doc link only |
| `data/processed/climate_yield_interval_diagnosis_rows.csv.gz` | 0.81 | `src/interval_diagnosis.py`, `tests/test_interval_diagnosis.py` | app/test/rebuild reader |
| `data/processed/sensitivity_us_high_plains_b.json` | 0.80 | `tests/test_app.py`, `docs/cleanup_manifest.md` | app/test/rebuild reader |
| `data/processed/climate_yield_predictions.csv` | 0.75 | `src/climate_yield.py`, `docs/cleanup_manifest.md` | app/test/rebuild reader |
| `data/processed/sensitivity_kenya_makueni_north.json` | 0.75 | `docs/cleanup_manifest.md`, `docs/sensitivity.md` | doc link only |
| `data/processed/opportunity_windows_us_high_plains_b.json` | 0.69 | `docs/cleanup_manifest.md`, `docs/opportunity_windows.md` | doc link only |
| `data/raw/p25/quickstats_kansas.csv` | 0.68 | `src/county_yield_data.py`, `docs/cleanup_manifest.md` | app/test/rebuild reader |
| `data/processed/climate_yield_intervals.json` | 0.63 | `app/main.py`, `src/yield_intervals.py` | app/test/rebuild reader |
| `data/raw/p32/quickstats_targets.csv` | 0.57 | `src/cross_state_yield_data.py`, `tests/test_cross_state_yield.py` | app/test/rebuild reader |
| `data/processed/literature_variant_p43.json` | 0.54 | `app/main.py`, `src/consensus_shortlist.py` | app/test/rebuild reader |
| `data/processed/climate_yield_interval_diagnosis.json` | 0.52 | `app/main.py`, `src/evidence_ledger.py` | app/test/rebuild reader |
| `data/processed/rank_concentration_p47.json` | 0.51 | `app/main.py`, `src/evidence_ledger.py` | app/test/rebuild reader |
| `data/processed/climate_yield_validity_all_practices_predictions.csv` | 0.48 | `docs/cleanup_manifest.md` | doc link only |
| `data/raw/p2_evidence/kenya_power.json` | 0.48 | `src/farm_validity.py`, `docs/public_readiness.md` | app/test/rebuild reader |
| `data/processed/opportunity_windows_telangana_a.json` | 0.45 | `docs/opportunity_windows.md` | doc link only |
| `data/processed/climate_yield_validity_pooled_predictions.csv` | 0.42 | `src/cross_state_yield.py`, `src/scoring_response_check.py` | app/test/rebuild reader |
| `data/processed/climate_yield_features.csv` | 0.37 | `src/cross_state_yield.py`, `src/yield_intervals.py` | app/test/rebuild reader |
| `data/raw/p50/sentinel2_observations.json` | 0.37 | `src/makueni_sentinel_report.py`, `src/makueni_sentinel_p50.py` | app/test/rebuild reader |

## Optional future trims

These are estimates, not cleanup actions. Each would need its own quarantine run, test review and documentation changes.

| Group | Tracked size that could leave Git | Effect | Fixture and documentation work | Risk |
| --- | ---: | --- | --- | --- |
| P25 archived POWER county chunks (`data/raw/p25/power_archive/`) | about 23 MiB | Offline Kansas climate feature rebuild and P33b diagnostics lose their full weather witness; saved app results still load. | Retain a small county-year fixture for parser tests; reword `docs/ml_model.md` and README offline rebuild claims and preserve manifest hashes. | High |
| P32 archived POWER county chunks (`data/raw/p32/power_archive/`) | about 26 MiB | Offline Nebraska/Oklahoma feature rebuild and P33b diagnostics lose their full weather witness. | Keep a small two-state fixture, reword `docs/ml_model.md` and README offline rebuild claims, and preserve request manifests. | High |
| P31 ICRISAT archive (`Data.csv` and `Shapefile.rar`) | about 4.5 MiB | The India archive screening rebuild cannot check the original deposited rows or district map. | Small schema fixture could test code, but would not reproduce the published screening counts; revise `docs/ml_model.md`. | High |
| P33 held-out interval predictions CSV | 7.56 MiB | `src.interval_diagnosis` and two tests lose their row-level witness. | A small interval fixture supports unit tests but not the full diagnostic; revise `docs/ml_model.md` links and rebuild statements. | High |
| P44/P44b Telangana consensus CSVs | about 3.4 MiB together | Linked ranking-frequency detail would disappear, though summary JSON remains. | Could replace with compressed summary or top rows; revise the two consensus documents and their links. | Medium |
| Historical processing outputs with no reader or link | file-specific, under 1 MiB each among the top 25 | May remove audit detail. | Prove no reader or link and run quarantine tests individually. | Medium |

## Claim check

All linked documents and images in the fresh clone resolve. The README's cached rebuild commands have not all been executed in this audit, so they are listed as entry points rather than a byte-for-byte reproduction claim. The P25/P32 archives, P31 archive, P33 interval rows, P48/P50 compact witnesses, and linked study outputs remain tracked. The P48/P50 full download caches remain ignored and are only re-fetchable with network authorization. Fresh-clone app startup and tests were exercised with the matching existing interpreter; a new venv dependency installation was not attempted in P52b.
