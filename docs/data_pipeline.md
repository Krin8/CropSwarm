# NASA climate and vegetation data pipeline

From the CropSwarm repository, run `python -m src.data_pipeline` to rebuild the processed files from disk. `python -m src.data_pipeline --fetch` enables requests for missing chunks. The default vegetation period is 2015–2024, with 2019–2023 fetched first. Use `--core-only` to build only the core years and `--workers 1` to request serially when troubleshooting a slow service. Tests and the app can use the checked-in data offline.

## Requests and provenance

The request manifest at [data/raw/p4/manifest.json](../data/raw/p4/manifest.json) records each farm, source, URL, parameters, timestamp, HTTP status, cached response file and coverage. Each chunk has a request-specific file name derived from the full URL and parameters. The raw file keeps the provider payload with request metadata and attempt history. Exact matching point subsets from P2 are imported with their original evidence reference and the P2 batch timestamp.

| Source | Exact date windows | Coverage rules |
| --- | --- | --- |
| NASA POWER, Agroclimatology community, Local Solar Time (LST) | January 1 through December 31 inclusive for 1991–1995, 1996–2000, 2001–2005, 2006–2010, 2011–2015, 2016–2020 and 2021–2025 | Seven requested parameters per call. NASA documents up to 20 for point requests. POWER and the product units are in the raw replies. [Daily API documentation](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) |
| NASA POWER IMERG and corrected rainfall, UTC | January 1 through December 31 inclusive for 2000–2004, 2005–2009, 2010–2014, 2015–2019, 2020–2024 and 2025 | IMERG is supplied only in UTC. Fetch corrected rainfall on the same UTC day boundaries for the later comparison. The first LST IMERG requests returned only fill values. Those raw replies remain in the manifest as superseded. [NASA POWER IMERG methodology](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/#imerg-integrated-multi-satellite-retrievals-for-gpm) |
| Terra MODIS MOD13Q1 point subset through ORNL DAAC | For every year 2015–2024, three inclusive windows: `Ayyyy001–Ayyyy145`, `Ayyyy161–Ayyyy305`, and `Ayyyy321–Ayyyy353` | These windows hold 10, 10 and 3 sixteen-day composites. ORNL permits a maximum of 10 dates per subset. `kmAboveBelow=0` and `kmLeftRight=0` request the point pixel. [ORNL REST documentation](https://modis.ornl.gov/data/modis_webservice.html) |

Five calendar years per POWER chunk, four default workers, 10-second connection and 65-second read timeouts, and up to two retries with delays of 2 and 8 seconds are operational choices. Client errors other than 408 and 429 end the attempt sequence. Slot dates are checked against the request before declaring a chunk complete. Each response and output is written via atomic replacement. A partial response remains usable for dates it actually includes and remains eligible for a later fetch. Where a complete provider response includes fill values, it is reused and the affected dates are still marked missing in the coverage report. Complete chunks carry forward across interrupted runs.

## Processed files

- `data/processed/climate_<farm_id>.parquet` has one `date` per day from 1991 through 2025. Measure columns retain their NASA field names: `T2M`, `T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`, `GWETROOT`, `ALLSKY_SFC_SW_DWN`, and `RH2M`. `IMERG_PRECTOT` and `PRECTOTCORR_UTC` contain the UTC comparison series from 2000. Keep the two precipitation time standards separate. Provider fill value `-999`, nulls and absent days become missing. Genuine zero rainfall remains zero.
- `data/processed/ndvi_<farm_id>.csv` includes composite start `date`, scaled `ndvi` and `evi`, `pixel_reliability`, `vi_quality` bit field, the pixel's selected `composite_date` when it is within the composite window, and the product source. Valid ranges and scaling come from the archived [ORNL API band metadata](../data/raw/smoke/modis_bands.json). Both vegetation indices use a scale factor of 0.0001. P5 will apply the quality filter to these recorded fields.
- [Coverage report](../data/processed/coverage_p4.json) lists expected dates and missing dates per daily field and per composite year/field. A MODIS year's status refers to valid-range NDVI coverage, before quality filtering. Other band gaps remain explicit.

These are gridded observations and model outputs for illustrative points. The provider's MOD13Q1 subset responses report nominal 250 m resolution and a projected cell size of about 231.7 m. Separate fields and vegetation can share the same pixel. POWER `GWETROOT` expresses modeled root-zone soil wetness. Use local observations to validate soil or crop claims. Satellite data here supply no soil nitrogen or organic carbon measurements. [NASA POWER hydrology documentation](https://power.larc.nasa.gov/docs/methodology/data/sources_hydrology/)

## P19 MODIS long record

Use `python -m src.data_pipeline --long-record --fetch` to resume the 2001–2024 point subsets for the three configured farms. This mode requests only MOD13Q1, using the existing P4 cache keys, three date chunks per year, bounded retries and atomic writes. Omit `--fetch` to process whatever is in the committed cache offline. This mode writes `data/processed/ndvi_long_<farm_id>.csv` and `data/raw/p4/manifest_p19.json`. The existing climate and vegetation outputs used by P5 and P15 keep their original date ranges.

Then run `python -m src.nasa_consistency` against the saved P5 calendars and cached POWER climate. The resulting `nasa_consistency_<farm_id>.json` files contain annual coverage, season rows and paired statistics. See [methods and results](backtest.md#p19-long-record-nasa-consistency-check).
