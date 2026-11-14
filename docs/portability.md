# P13 portability and screenshots

The tracked Python, Markdown, configuration and build files use repository-relative locations or resolve the repository root from the file location. The application runtime uses only the following data, all under `data/processed/`.

| When used | Files |
|---|---|
| Initial layout and farm picker | `app_settings.json` and `world_land.json` |
| Selected farm | `context_<farm_id>.json`, `assessment_<farm_id>.json`, `validity_<farm_id>.json`, `backtest_<farm_id>.json`, `chart_backtest_<farm_id>.json`, `stress_test_<farm_id>.json`, `stress_margins_<farm_id>.json`, `tie_diagnosis_<farm_id>.json` and the four climate `chart_<farm_id>_*.json` files |
| Strategy and scenario comparisons | `strategies_<farm_id>.json` and `uncertainty_<farm_id>.json` |
| Applying edited inputs | `seasons_<farm_id>.json` and `climate_<farm_id>.parquet` |

The app has no runtime dependency on `data/raw/`, `data/cache/`, `ndvi_*.csv`, `coverage_p4.json`, the source crop CSV or the precompute configuration files. The offline back-test rebuild (`python -m src.backtest`) does read the committed Kansas CDL raw sample, crop CSV, climate and NDVI processed files. Keep the committed archives and fixtures when running the full test suite or rebuilding processed data. Install the pinned requirements in a fresh Python 3.12 virtual environment, then run `python -m pytest -q` and `python -m streamlit run app/main.py` from the checkout.

The screenshot script starts its own loopback-only Streamlit server, blocks external HTTP resources in the browser, and opens a separate session per farm. The uncertainty panels use the existing rotation under the warmer and drier scenario. With Google Chrome installed:

```sh
python -m pip install -r requirements-screenshots.txt
python scripts/capture_screenshots.py --channel chrome
```

Alternatively install Playwright Chromium with `python -m playwright install chromium` and omit `--channel`. The [screenshot index](screenshots/README.md) links all nine outputs.
