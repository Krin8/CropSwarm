# P13 portability and screenshots

The tracked Python, Markdown, configuration and build files use repository-relative locations or resolve the repository root from the file location. The application runtime uses only the following data, all under `data/processed/`.

| When used | Files |
|---|---|
| Initial layout and farm picker | `app_settings.json` and `world_land.json` |
| Selected farm | `context_<farm_id>.json`, `assessment_<farm_id>.json`, `validity_<farm_id>.json`, `backtest_<farm_id>.json`, `chart_backtest_<farm_id>.json`, `stress_test_<farm_id>.json`, `stress_margins_<farm_id>.json`, `tie_diagnosis_<farm_id>.json` and the four climate `chart_<farm_id>_*.json` files |
| Long-record NASA validation | `nasa_consistency_<farm_id>.json` |
| Opportunity windows | `opportunity_windows_<farm_id>.json` |
| Robust pick under assumption changes | `robust_stability_<farm_id>.json` |
| What to check first | `sensitivity_<farm_id>.json` |
| Learned climate-yield check | `climate_yield_model.json` and `climate_yield_validity_<cohort>.json` |
| Consensus shortlist | `consensus_shortlist_p44.json` |
| Scoring literature cross-check and Kansas what-if | `literature_check_p35.json` and `literature_variant_p43.json` |
| Yield validation | `yield_backtest_<farm_id>.json` |
| Strategy and scenario comparisons | `strategies_<farm_id>.json` and `uncertainty_<farm_id>.json` |
| Applying edited inputs | `seasons_<farm_id>.json` and `climate_<farm_id>.parquet` |

The farm decision brief uses the same saved JSON, plus the bundled PDFs and release manifest in `docs/briefs/`.

The app has no runtime dependency on `data/raw/`, `data/cache/`, `ndvi_*.csv`, `coverage_p4.json`, the source crop CSV or the precompute configuration files. The offline back-test rebuild (`python -m src.backtest`) does read the committed Kansas CDL raw sample, crop CSV, climate and NDVI processed files. Keep the committed archives and fixtures when running the full test suite or rebuilding processed data. Install the pinned requirements in a fresh Python 3.12 virtual environment, then run `python -m pytest -q` and `python -m streamlit run app/main.py` from the checkout.

P52 retained the checked-in processed outputs, raw test and rebuild witnesses, all 12 PDF and 12 linked HTML briefs, and every ledger-linked document. The unreferenced `data/processed/climate_yield_validity_non_irrigated_predictions.csv` was quarantined outside the repository after the full 306-test suite and three farm app checks passed without it. It is not needed to run the app or tests. The active `.venv` and ignored caches remain in the local working tree and are not part of a clone.

`data/cache/p48/` contains ignored WorldCover, GLAD, WorldCereal and related raster/access downloads used by `scripts/cache_p48_rasters.py` for online retrieval. `data/cache/p50/` contains ignored Sentinel-2 STAC and COG range caches used by `scripts/cache_p50_sentinel2.py`. These scripts require public network access to re-fetch missing cache entries. Neither the app nor the offline test suite reads these cache directories; the checked-in P48/P50 raw witnesses and processed reports are the offline inputs. Run the scripts from the repository root only when network retrieval is authorized. `data/raw/p11/` remains for `python -m src.app_assets` offline rebuilding, and `data/raw/p13/` remains because `docs/citation_audit.md` links its manifest.

The screenshot script starts its own loopback-only Streamlit server, blocks external HTTP resources in the browser, and opens a separate session per farm. The uncertainty panels use the existing rotation under historical-weather draws. With Google Chrome installed:

```sh
python -m pip install -r requirements-screenshots.txt
python scripts/capture_screenshots.py --channel chrome
```

Alternatively install Playwright Chromium with `python -m playwright install chromium` and omit `--channel`. The [screenshot index](screenshots/README.md) links all 30 outputs. Use `--sensitivity-only` or `--opportunity-only` to refresh just the corresponding three views. Pass `--panels` followed by panel names to refresh a custom subset.
