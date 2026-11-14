# Opportunity windows

This offline screen looks for periods of recurring low greenness and asks whether a short cover or legume could fit the same dates under cached weather. It identifies possible checks for a local conversation. Field history, soil moisture, seed, timing and costs still need local evidence. All numbers are illustrative and need local validation.

## Detecting windows from MODIS

- Use the 2001–2024 Terra MODIS MOD13Q1 record from P19 at each point. QA uses good summary reliability, good or absent detailed QA, and a valid NDVI value. A missing or QA-rejected composite breaks the run. No NDVI is filled or smoothed. [P19 coverage and QA](backtest.md#p19-long-record-nasa-consistency-check)
- Start from the P5 low-cover rule, NDVI strictly below **0.25**, labeled `assumption, validate locally`. Repeat the analysis at **0.20** and **0.30** using the requested ±0.05 design changes. Use at least two adjacent accepted low composites, each representing its nominal 16-day coverage, shortened at calendar year-end. A December run can continue in January only where both composites are valid and adjacent. A single low composite does not establish an interval. [P5 settings](decisions.md) · [P17 settings](../config/opportunity_windows.json)
- For each pair of nominal MODIS dates, count a year as assessable if both are QA-valid. A pair recurs if at least three years show low NDVI in both and those years make up at least half of its assessable years. Group adjacent recurrent pair starts, including across January 1. Label each group by the pair with the most supporting years, then the highest share, then earlier nominal day. Report the starts and lengths of the containing observed runs, taking medians relative to that anchor. The typical dates are illustrated on the non-leap 2001 calendar. Runs that cross January are assigned the anchor pair's year. The result keeps all individual runs, even where they fall outside the recurring group.
- If no pair recurs, summarize the strongest observed pair when there is one. Fewer than three supporting years are **tentative**. Three or more years below the recurrence share are **sporadic**. These criteria are design choices. If no qualifying pair exists, the panel shows the NDVI trace and the absence of a recurring window.
- Report the number of QA-valid composites in supporting runs and the number of assessable years for the anchor pair. Descriptive 95% bootstrap intervals for the median offset and length resample supporting years, using 1,000 draws and seed 42. These settings are design choices. The intervals describe sampling variation under that rule. They leave out uncertainties from management, threshold choice and serial dependence.

## Crops and fit criteria

Cereal rye is the cover entry in the current catalog. Test it alongside catalog legumes with a duration at or below 105 days, a short-season screening choice. This admits green gram (75 days), cowpea (85), field pea (95), common bean (100) and chickpea (105). Rye uses its 100-day cover duration. Duration, rainfall bounds, temperature bounds, daily heat thresholds and water demand come from each existing crop row with its original source or assumption label. The dates are sampled from each detected run, so the fit screen stays separate from the baseline optimizer's season list. The app shows only candidates with a matching season in the farm's crop catalog. The original climate-only calculations remain in the archive. [Crop catalog](../data/crops.csv) · [Catalog methods and source limits](crops.md)

For each supporting run, test the crop's complete duration starting on the first nominal low-NDVI day. This fixed timing avoids searching for the warmest or wettest placement within the run. Each of the following reports passes over assessable years.

1. **Length.** The run must have at least the catalog's full duration.
2. **Temperature.** NASA POWER mean daily air temperature over those dates must be within the catalog bounds. The share of days with daily maxima above the crop's daily heat threshold must be at or below the existing scoring policy of 10%. Apply the P5 frost-free requirement of daily minimum temperature above 0 °C to the legume candidates. The cereal rye winter-cover exception is an assumption. The screen does not model winter injury or dormancy. [Scoring policy](../config/scoring.json) · [Rye catalog source](crops.md)
3. **Water.** Require raw rain at or below the catalog upper rainfall bound. Require rain plus initial soil-water proxy and available irrigation at or above the catalog lower rainfall bound. Initial soil water equals the planting-day POWER `GWETROOT` value times mapped available water in the top 30 cm. Root-zone wetness is a POWER **model product**. Its multiplication by mapped storage is a simple assumption, validate locally. Estimate available irrigation as the configured supply fraction times any positive gap between catalog water need and rain plus the soil-water proxy. Water sufficiency here means passing the catalog screen. It may leave substantial unmet crop demand.
4. **Overall.** Every check must pass. A failed length counts as an overall failure and leaves temperature and water untested. A known failure counts even if another check is unknown. An otherwise passing case with a missing required observation is unavailable for the overall count. POWER fill values of −999 are missing. Report each denominator so years excluded for missing climate or short runs stay visible.

## Modeled change when the fit screen passes

Reuse the rotation engine for a paired comparison with one added gap in the configured baseline. Place it just before the first planted crop in the baseline cycle, once as uncovered and once planted with the candidate. This is an illustrative placement for the carryover calculation. It does not establish that the dates match an actual baseline planting. The same-length pair keeps other slot contributions fixed. Convert per-slot deltas into changes per gap insertion and summarize passing years with a median and observed range.

- **Net nitrogen carryover** is the crop's modeled credit to its successor minus its demand. This is a crop-catalog proxy and does not establish fertilizer rates.
- **Erosion proxy** is the change in the existing slope × daily peak rainfall × uncovered-share calculation over the candidate's dates. Negative values mean less modeled erosion exposure.
- **Crop water use** is the catalog demand met by the existing daily rainfall bucket and assumed irrigation. The same engine also reports additional unmet water. Its bucket starts empty as it does in the scoring engine. The separate wetness proxy is used for the fit screen only. Cover-crop water use is a cost to the following crop. The model does not track the resulting loss of soil water into the next crop. The study estimates no yield effect.

## Evidence and safeguards

The panel uses P18's equal-input provenance shares and high/medium/low thresholds. The JSON stores each metric's source ledger. QA-screened NDVI and POWER weather are in the NASA measured grade. POWER root-zone wetness and SRTM-derived slope are NASA modeled, mapped soil water is external measured in the P18 taxonomy, and crop terms keep their literature or assumption grade. The threshold, recurrence and fit rules are assumptions. Fit evidence includes the window and crop duration dependencies. The modeled changes include the passing-year selection and the appropriate score inputs.

The unexplained Kansas spring peak over CDL fallow, Telangana's tentative second crop season, and unverified Makueni cropland cap window, fit and contextual model estimates at low. The directly sourced NDVI trace and counts retain their data provenance label. A 250 m pixel can mix crops, weeds and other land cover. Clouds remove valid composites, and the apparent end of a run can reflect a gap. Low greenness cannot establish bare soil, harvest dates or management. [P18 evidence grades](evidence_grades.md) · [Reference-site flags](decisions.md)

## Results

Figure entries give typical start day-of-year, median length, supporting / assessable years, and QA-valid composites across supporting runs. Each is an illustrative **low-evidence** P18 window estimate. A dash means no qualifying pair was detected at that cutoff.

| Farm | QA-valid composites in record | NDVI < 0.20 | NDVI < 0.25 · P5 reference | NDVI < 0.30 |
|---|---:|---|---|---|
| Kansas | 516 | Day 129 · 80 days · 1/24 · 5 composites · tentative | Day 1 · 96 days · 11/17 · 92 composites · recurrent | Day 1 · 160 days · 15/17 · 155 composites · recurrent |
| Telangana | 295 | — | Day 129 · 32 days · 2/17 · 4 composites · tentative | Day 129 · 48 days · 11/17 · 33 composites · recurrent |
| Makueni | 345 | — | — | Day 273 · 32 days · 3/13 · 7 composites · sporadic |

The Kansas P5 reference low-greenness window centers on winter, with a median-length bootstrap interval of 80–221 days. It may be winter-wheat dormancy, not bare soil. The cached CDL and MODIS evidence leaves planting availability unknown. [Kansas evidence check](#kansas-dormancy-check) It does not survive the stricter cutoff. At 0.25, no crop passes all checks at either farm with a recorded window. Cereal rye passes temperature in two of five long-enough Kansas years and passes none of their water checks. Telangana's two tentative runs are too short for all tested crops. Makueni has no supported reference window.

Only the looser 0.30 Kansas sensitivity run shows a complete fit for a catalog-matched crop. Cereal rye passes in one of 15 anchor years (2012). Its Kansas cool catalog season and rare modeled fit leave field availability unresolved. The original archive also records a climate-screen pass for green gram. The app excludes it because it has no Kansas catalog season.

| Kansas crop at 0.30 | Length | Temperature | Water | Overall | Modeled net N change | Erosion-proxy change | Water used / unmet |
|---|---:|---:|---:|---:|---:|---:|---:|
| Cereal rye cover | 10/15 | 4/10 | 4/10 | 1/15 | 0 kg N/ha | −132.69 | 75.04 / 144.96 mm |

There is one passing year for the displayed rye benefit estimates, so each saved range collapses to that single value. Remaining records, denominators and source ledgers are in the [Kansas](../data/processed/opportunity_windows_us_high_plains_b.json), [Telangana](../data/processed/opportunity_windows_telangana_a.json), and [Makueni](../data/processed/opportunity_windows_kenya_makueni_north.json) outputs.

## Kansas dormancy check

The cached CDL 3×3 neighborhood classified all nine samples as winter wheat in 2020 and 2023, fallow/idle cropland in 2019 and 2022, and sorghum in 2021. The P5 Kansas cool-season calendar spans October–June, and P15 assigns it to the harvest year. This calendar is illustrative and includes winter dormancy.

- **2020, mapped winter wheat.** Five QA-valid composites were below 0.25 in the January 1–March 21 span (end exclusive). NDVI was 0.207 on February 2 and rose to 0.522 on May 8. This rise is compatible with spring green-up after dormancy.
- **2022, mapped fallow/idle cropland.** A longer below-cutoff run overlapped the same winter period. The April 7 and May 9 composites stayed near 0.20. Low winter NDVI occurs with different mapped classes.
- **2019 and 2023.** Neither has a low run supporting the reference window, even though CDL mapped fallow in 2019 and wheat in 2023. The unexplained April 2019 greenness over mapped fallow and the mismatch between the CDL neighborhood and MODIS footprint limit field interpretation.

The comparison supports the cautious low-greenness label. CDL provides annual map classes, NDVI covers a mixed pixel, and the crop window is assumed. Field-level management or ground cover remains unverified. [Saved CDL comparison](../data/processed/validity_us_high_plains_b.json) · [QA-screened NDVI and runs](../data/processed/opportunity_windows_us_high_plains_b.json) · [P15 crop calendar](backtest.md#what-was-compared)

## Rebuild offline

Run `python -m src.opportunity_windows` from the repository. It uses the processed daily POWER weather and long MODIS series, the cached soil, terrain and season inputs, and the committed farm, crop and evidence settings. It writes the three new opportunity files. The app reads the results from those files. Existing rotation, uncertainty, P16 weather-shift, P22 assumption-sensitivity and back-test results retain their published values.
