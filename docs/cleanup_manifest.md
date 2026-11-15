# P52 cleanup manifest (inventory stage)

This is a conservative classification before deletion. `pre-cleanup` tags the starting master commit. The readable full backup, including ignored and untracked files but excluding `.venv`, is `/private/tmp/cropswarm-pre-cleanup-2026-11-15.zip` (950 MiB). Starting sizes: working tree 1.7 GiB, `.git` 79 MiB, tracked files 109 MiB (`du` totals). No file has been removed.

## Top-level inventory

| Group | Class | Basis |
| --- | --- | --- |
| `app/`, `src/`, `config/`, `scripts/`, `.streamlit/`, root Python files, `requirements*.txt`, `Dockerfile`, `.dockerignore`, `.gitattributes`, `.gitignore`, `README.md` | KEEP-REQUIRED | Application, offline generators, and packaging. |
| `tests/` | KEEP-TEST | Offline test suite and fixtures. |
| `data/` | Mixed; see below | App inputs, saved results, test witnesses, and ignored caches. |
| `docs/` | Mixed; see below | Public explanation, ledger links, images, and generated briefs. |
| `.git/` | KEEP-REQUIRED | Repository and history; no history rewrite. |
| `.venv/` (629 MiB) | ASK | Disposable environment, but deleting the active environment before the required fresh-clone check may prevent verification if offline dependency installation fails. Recommend retaining until fresh-clone checks pass, then deleting from this checkout. |
| `__pycache__/`, `.pytest_cache/`, `*.pyc`, `.DS_Store` | REMOVE-SAFE candidate | Generated artifacts; require quarantine test and link scan before deletion. |

## Data file groups

| Group | Class | Basis |
| --- | --- | --- |
| `data/crops.csv`, `data/p35_literature.json`, `data/p45_literature.json`, `data/p49_literature.json` | KEEP-REQUIRED | Crop catalog and published evidence inputs to checked-in scripts and reports. |
| `data/processed/` (31 MiB) | KEEP-REQUIRED | Saved results used by the app and ledger. Individual files require dependency tracing before trimming. |
| `data/raw/smoke/`, `p2_evidence/`, `p3/`, `p4/`, `p7/`, `p20/`, `p25/`, `p27/`, `p31/`, `p32/`, `p48/`, `p50/` (250 MiB total raw) | KEEP-TEST | Tests and offline rebuilds read these witnesses; P50 report links to its raw witness. Per-file removal requires a quarantine test. |
| `data/raw/p11/`, `p13/` | ASK | Earlier map and screenshot assets may be rebuild inputs or historical provenance. Recommend keeping until mechanically traced and tested. |
| `data/cache/p48/` (large raster and access caches) | ASK | Ignored caches include a WorldCover tile over 50 MiB. P48/P50 scripts may need them to reproduce source checks, while the app may not. Recommend retaining outside Git until a quarantine test and offline rebuild establish whether each is dispensable. |
| `data/cache/p50/` (scene and STAC caches) | ASK | Ignored resumable Sentinel downloads; likely regenerable only with network, which P52 forbids. Recommend retain locally or archive outside repo, then remove only after the offline witness is confirmed sufficient. |
| `data/cache/.gitkeep` | KEEP-REQUIRED | Tracked directory placeholder; harmless. |

## Docs file groups

| Group | Class | Basis |
| --- | --- | --- |
| `docs/evidence_ledger.md`, every linked study document, preregistration and methods documents, `docs/portability.md`, `docs/submission_summary.md`, `docs/demo.md` | KEEP-REQUIRED | Ledger, README, and audit provenance. |
| `docs/screenshots/` (4.0 MiB), `docs/charts/` (112 KiB) | KEEP-REQUIRED pending per-file link check | Referenced images must remain; unlinked images are REMOVE-SAFE candidates only after mechanical link and app checks. |
| `docs/briefs/` (3.2 MiB) | ASK | Generated printable briefs may be expected submission artifacts even if no Markdown link names each file. Recommend keep unless the app and test suite prove them disposable and the user accepts removal. |
| Any orphan draft, duplicate, or temporary document | REMOVE-SAFE candidate | Only after no code or document links to it and quarantine tests pass. |

## Resolved ASK items and cleanup outcome

The user directed us to retain `.venv` locally, keep ignored P48/P50 caches, retain raw groups read by rebuilds or linked as provenance, and retain all 12 PDFs plus the 12 HTML briefs linked by the brief index. Thus the earlier ASK labels above are historical inventory labels, now resolved to KEEP-REQUIRED or KEEP-TEST as applicable. The cache directories and `.venv` match `.gitignore`; no app or test code reads `data/cache/`. The cache retrieval scripts themselves use those directories when explicitly run. `data/raw/p11/` is read by `src/app_assets.py`; `data/raw/p13/manifest.json` is linked by `docs/citation_audit.md`.

One unreferenced tracked CSV (0.81 MiB) was moved to `/private/tmp/cropswarm-p52-quarantine/data/processed/` and removed from Git. Its absence passed 306 tests and app checks for all three farms. No briefs or raw witnesses were removed. The largest retained tracked file is 7.56 MiB; no tracked file is over 50 MiB. The external ZIP backup was integrity checked before the removal.

The fresh clone passed a static link check: 60 documents, 472 local links and 30 PNGs. A newly created Python 3.14 venv could not install the pinned requirements in offline mode because no local Jinja2 3.1.6 wheel was available. Therefore fresh-clone tests and app startup are unverified; the branch must remain unmerged under the user’s all-tests gate.

## Twenty largest tracked files before removal

| File | MiB | Reader or link examples | Classification |
| --- | ---: | --- | --- |
| data/processed/climate_yield_interval_predictions.csv | 7.56 | src/yield_intervals.py, src/interval_diagnosis.py, tests/test_interval_diagnosis.py | KEEP-REQUIRED |
| data/raw/p31/Shapefile.rar | 3.18 | src/india_yield_screen.py, docs/ml_model.md | KEEP-TEST |
| data/processed/climate_yield_transfer_predictions.csv | 3.10 | src/cross_state_yield.py, src/yield_intervals.py, src/scoring_response_check.py | KEEP-REQUIRED |
| data/processed/consensus_shortlist_p44b_telangana_a.csv.gz | 1.70 | docs/consensus_shortlist_p44b.md | KEEP-REQUIRED |
| data/processed/consensus_shortlist_p44_telangana_a.csv.gz | 1.70 | docs/consensus_shortlist.md | KEEP-REQUIRED |
| data/raw/p31/Data.csv | 1.30 | src/india_yield_screen.py, docs/ml_model.md | KEEP-TEST |
| data/raw/p2_evidence/p2_evidence.json | 1.28 | src/data_pipeline.py, src/farm_validity.py, docs/public_readiness.md | KEEP-TEST |
| data/processed/sensitivity_telangana_a.json | 1.02 | docs/sensitivity.md | KEEP-REQUIRED |
| data/processed/climate_yield_interval_diagnosis_rows.csv.gz | 0.81 | src/interval_diagnosis.py, tests/test_interval_diagnosis.py, docs/ml_model.md | KEEP-REQUIRED |
| data/processed/sensitivity_us_high_plains_b.json | 0.80 | tests/test_app.py, docs/sensitivity.md | KEEP-REQUIRED |
| data/processed/climate_yield_predictions.csv | 0.75 | src/climate_yield.py, docs/ml_model.md | KEEP-REQUIRED |
| data/processed/sensitivity_kenya_makueni_north.json | 0.75 | docs/sensitivity.md | KEEP-REQUIRED |
| data/processed/opportunity_windows_us_high_plains_b.json | 0.69 | docs/opportunity_windows.md | KEEP-REQUIRED |
| data/raw/p25/quickstats_kansas.csv | 0.68 | src/county_yield_data.py | KEEP-TEST |
| data/processed/climate_yield_intervals.json | 0.63 | app/main.py, src/yield_intervals.py, src/evidence_ledger.py | KEEP-REQUIRED |
| data/raw/p32/quickstats_targets.csv | 0.57 | src/cross_state_yield_data.py, tests/test_cross_state_yield.py, docs/ml_model.md | KEEP-TEST |
| data/processed/literature_variant_p43.json | 0.54 | app/main.py, src/consensus_shortlist.py, src/evidence_ledger.py | KEEP-REQUIRED |
| data/processed/climate_yield_interval_diagnosis.json | 0.52 | app/main.py, src/evidence_ledger.py, src/interval_diagnosis.py | KEEP-REQUIRED |
| data/processed/rank_concentration_p47.json | 0.51 | app/main.py, src/evidence_ledger.py, src/rank_concentration.py | KEEP-REQUIRED |
| data/processed/climate_yield_validity_all_practices_predictions.csv | 0.48 | No textual reader found | KEEP-REQUIRED |

`data/processed/climate_yield_validity_non_irrigated_predictions.csv` was 0.81 MiB before quarantine. It had no textual reader or link, and the full 306-test suite and three farm app smoke checks passed with it absent. Its copy is at `/private/tmp/cropswarm-p52-quarantine/data/processed/`. All other listed large files are retained because they are read or linked, or because the processed result is part of the saved audit record.
