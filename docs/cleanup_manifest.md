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

## Ask items and stop point

The ASK groups above total hundreds of MiB. They are ambiguous because the network prohibition prevents re-fetching caches during P52 and because briefs may be intended deliverables. Recommendation: keep all ASK groups for the submission and delete only confirmed generated junk. No deletion or quarantine trial has been run. The task's Step 2 requires stopping here until these items are resolved.
