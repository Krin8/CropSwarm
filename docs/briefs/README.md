# Farm decision briefs

Each brief is a one-page shortlist of options to discuss with an extension officer. Choose a farm and priority preset below, or use **Download brief** under **Farm priorities** in the app.

| Illustrative farm | Water saver | Soil builder | Income | Balanced |
|---|---|---|---|---|
| US High Plains B | [HTML](us_high_plains_b_water_saver.html) · [PDF](us_high_plains_b_water_saver.pdf) | [HTML](us_high_plains_b_soil_builder.html) · [PDF](us_high_plains_b_soil_builder.pdf) | [HTML](us_high_plains_b_income.html) · [PDF](us_high_plains_b_income.pdf) | [HTML](us_high_plains_b_balanced.html) · [PDF](us_high_plains_b_balanced.pdf) |
| Telangana A | [HTML](telangana_a_water_saver.html) · [PDF](telangana_a_water_saver.pdf) | [HTML](telangana_a_soil_builder.html) · [PDF](telangana_a_soil_builder.pdf) | [HTML](telangana_a_income.html) · [PDF](telangana_a_income.pdf) | [HTML](telangana_a_balanced.html) · [PDF](telangana_a_balanced.pdf) |
| Makueni North Candidate | [HTML](kenya_makueni_north_water_saver.html) · [PDF](kenya_makueni_north_water_saver.pdf) | [HTML](kenya_makueni_north_soil_builder.html) · [PDF](kenya_makueni_north_soil_builder.pdf) | [HTML](kenya_makueni_north_income.html) · [PDF](kenya_makueni_north_income.pdf) | [HTML](kenya_makueni_north_balanced.html) · [PDF](kenya_makueni_north_balanced.pdf) |

The bundled PDFs use US Letter. The HTML also fits A4 when printed at 100% with browser headers and footers disabled. All briefs use the saved reference inputs and named presets. The shortlist retains its saved order. The score-gap note compares the two highest preset scores among the shown options, including the baseline, using the existing P22 tolerance. The preliminary P28b section uses the largest saved draw count and reports whether each objective’s pick stayed the same across all three counts.

Live HTML downloads carry the local checkout’s commit and current date. Bundled PDFs carry the source commit and date recorded in [the release manifest](release.json). When the app runs from the Docker image without Git metadata, it uses that source commit for the HTML.

## Regenerate offline

From the repository root, run `python scripts/generate_decision_briefs.py` for HTML. For both formats, use an installed Chrome with the existing Playwright screenshot requirements and run

```sh
python scripts/generate_decision_briefs.py --pdf --channel chrome
```

Add `--paper A4` and use a separate `--output` directory for A4 copies. The script uses cached JSON and blocks browser requests when printing.
