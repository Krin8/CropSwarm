# Regional literature cross-check (P45)

Illustrative comparisons. Validate locally before using any value. This audit follows the [P35 scoring cross-check](literature_check.md) and applies no corrections.

## What counts as a benchmark

We searched for Telangana and peninsular Indian irrigated rice systems and for maize–bean systems in semi-arid eastern Kenya. The tables compare each eligible source and crop or crop contrast with the corresponding catalog quantity. A comparable observation uses the same crop and endpoint in the region. Where a study uses a different cultivar, water regime or window, the row specifies the difference. Crop water estimates and treatment spans describe the named study conditions. A point estimate has equal bounds, so any difference is classed as outside. Spans and points are descriptive references. Formal uncertainty intervals for transfers to the demo fields are unavailable.

Each usable comparison counts once, including the explicitly linked paddy–green gram contrast. The counts are comparisons, and some share a study or the same measurements. Climate-fit counts cover crop duration only. Seasonal rainfall and yield contrasts give context without defining the model's climate cut-offs. Nitrogen credits describe an immediately following crop's fertilizer-equivalent N, so residue N, mineral N and uptake remain contextual evidence. Crop ET is consumptive use. Gross withdrawals and paddy percolation require separate measurements. The model starts each seasonal bucket empty, represents one crop per slot and has no grain-yield output.

## Telangana

Irrigated rice-based systems in Telangana and peninsular India. The reference farm's second season is tentative.

| Metric | Usable | Inside range | Outside range | Context only |
| --- | ---: | ---: | ---: | ---: |
| Water | 5 | 1 | 4 | 1 |
| Nitrogen | 0 | 0 | 0 | 5 |
| Erosion | 0 | 0 | 0 | 0 |
| Climate fit | 1 | 1 | 0 | 0 |
| Income | 0 | 0 | 0 | 0 |
| Risk | 0 | 0 | 0 | 0 |

| Metric and comparison | Model | Published reference | Finding | Interpretation | Source |
| --- | --- | --- | --- | --- | --- |
| Water · Paddy rice seasonal ET · Hyderabad trial | 575 mm | 473.9 to 657.8 mm | inside range | Span of eight irrigation treatments, from alternate wetting and drying to continuous flooding. Published ET covers 100 days after transplanting, a different basis from the catalog's full crop window. Inclusion describes the trial span. | [Mote et al. (2018), Journal of Agrometeorology](#mote) |
| Water · Paddy rice seasonal ET · Sangareddy estimate | 575 mm | 595.5 mm | outside range | District-scale CROPWAT crop demand. A point comparison gives the difference from this estimate without a dispersion measure. | [Kumar et al. (2022), International Journal of Environment and Climate Change](#kumar) |
| Water · Green gram seasonal ET · Sangareddy estimate | 375 mm | 342.7 mm | outside range | Regional potential crop demand. The paper does not measure a green gram crop after paddy on the demo farm. | [Kumar et al. (2022), International Journal of Environment and Climate Change](#kumar) |
| Water · Chickpea (Bengal gram) seasonal ET · Sangareddy estimate | 400 mm | 344.9 mm | outside range | Regional potential crop demand for the study's Bengal gram season. Crop durations, rainfall and irrigation can vary. | [Kumar et al. (2022), International Journal of Environment and Climate Change](#kumar) |
| Water · Difference in seasonal ET · paddy minus green gram | 200 mm | 252.8 mm (595.5 − 342.7) | outside range | Both put crop ET higher for paddy. This contrast reuses the two Sangareddy crop estimates and says nothing about farm irrigation savings. | [Kumar et al. (2022), International Journal of Environment and Climate Change](#kumar) |
| Water · Field water applied and percolation · Jagtial | 575 mm | 1,276.5 mm applied, 402.86 mm crop ET, 452.13 mm percolation | no usable benchmark | The technology note provides component observations but gives no cultivar or crop-window details. These show how gross water applied can diverge from crop ET. They cannot constrain the rotation's water withdrawal or supply fraction. | [PJTSAU, Agro Technologies 2020–21](#pjtau) |
| Climate fit · Paddy rice variety duration · Hyderabad | 120 days | 120 to 125 days | inside range | Reported duration of MTU-1010. The field ET calculation covers only the post-transplant part. This comparison informs the crop window input. | [Mote et al. (2018), Journal of Agrometeorology](#mote) |
| Nitrogen · Green gram before paddy · N credit | 20 kg N/ha | 29–36 kg N/ha in material used as green manure. Rice mean 6.39 t/ha versus 4.70 after fallow. | no usable benchmark | Rice yield moved in the direction expected from a benefit. Incorporated biomass N is a different quantity from N fertilizer replaced. The trial does not isolate a successor fertilizer-equivalent response for the model's harvested grain legume. | [Surekha et al. (2013), The Andhra Agricultural Journal](#surekha) |
| Nitrogen · Cowpea before paddy · N credit | 22 kg N/ha | 38–50 kg N/ha in material used as green manure. Rice mean 6.34 t/ha versus 4.70 after fallow. | no usable benchmark | Positive rice yield response under incorporation. The mass of N returned includes N taken up from soil and gives no estimate of crop-available or fertilizer-equivalent N. | [Surekha et al. (2013), The Andhra Agricultural Journal](#surekha) |
| Nitrogen · Paddy before green gram · residual nutrient effect | 0 kg N/ha | Green gram seed yield 8.56% lower following normal transplanting than after dry direct-seeded rice. Uptake varied with rice establishment and manure form. | no usable benchmark | The study contrasts paddy management and manure treatments. The scorer has one paddy credit and no management-specific nutrient carryover. | [Vineela et al. (2026), Legume Research](#vineela) |
| Nitrogen · Harvested cowpea with haulms incorporated before rice · Coimbatore | 22 kg N/ha | 49–52 kg N/ha in the haulms. First rice yielded 4.80 and 4.45 t/ha versus 4.35 and 4.28 in the control sequence. | no usable benchmark | The table reports sequence means pooled across N rates separately from fertilizer means. The trial shows first-crop response with incorporation, but the table lacks the paired rate-specific yields required to infer a fertilizer-equivalent credit. | [Palaniappan and Siddeswaran (1994), SARP Research Proceedings](#palaniappan) |
| Nitrogen · Summer green gram before rice · Pilicode | 20 kg N/ha | Following-rice yields 4.48–4.67 t/ha across green gram treatments versus 4.46 t/ha after summer fallow. Treatment yield differences were not statistically significant. | no usable benchmark | The N rates varied for the preceding pulse. The following rice yields do not provide a fertilizer response curve for the successor. A nonsignificant yield result does not establish a zero credit. | [Adarsh (2019), Kerala Agricultural University MSc thesis](#adarsh) |

## Makueni

Maize–bean systems in semi-arid eastern Kenya, including Machakos and Makueni. Cropland at the demo coordinate is unverified.

| Metric | Usable | Inside range | Outside range | Context only |
| --- | ---: | ---: | ---: | ---: |
| Water | 2 | 0 | 2 | 2 |
| Nitrogen | 2 | 1 | 1 | 1 |
| Erosion | 0 | 0 | 0 | 0 |
| Climate fit | 2 | 1 | 1 | 2 |
| Income | 0 | 0 | 0 | 1 |
| Risk | 0 | 0 | 0 | 0 |

| Metric and comparison | Model | Published reference | Finding | Interpretation | Source |
| --- | --- | --- | --- | --- | --- |
| Nitrogen · Common bean before sole maize · N credit | 22 kg N/ha | 44 to 80 kg N/ha | outside range | Fertilizer equivalents of 80 in the 1982 long rains and 44 in 1982/83 short rains. The 80 comparison follows the season order assumed at the demo farm. Both agree with a positive credit. Yield response can include effects besides N and two seasons do not establish a modern field credit. | [Nadar and Faught (1984), East African Agricultural and Forestry Journal](#nadar) |
| Nitrogen · Cowpea before sole maize · N credit | 22 kg N/ha | 12.5 to 24 kg N/ha | inside range | Fertilizer equivalents of 12.5 in long rains and 24 in short rains. The catalog lies within this two-season span, above the long-rains estimate. This is a crop-specific comparison. | [Nadar and Faught (1984), East African Agricultural and Forestry Journal](#nadar) |
| Nitrogen · Maize–bean rotation and bean residues · residual mineral N | 22 kg N/ha | Rotation plots had higher residual mineral N than continuous maize at Masii and lower at Kimutwa. | no usable benchmark | The reprinted abstract shows site-dependent residual effects. It does not expose the treatment tables needed to attribute a fertilizer-equivalent range to one residue regime and crop sequence. | [Kenya Soil Health Consortium, Soil Fertility Management Book of Abstracts](#kenya_abstract) |
| Water · Maize seasonal ET · Katumani and Makindu budgets | 500 mm | 335 to 355 mm | outside range | Table 1 uses cultivar medians of 335 mm for Makindu and 355 mm for Katumani in both rainy seasons. The comparison uses published water-budget inputs. Maximum crop demand was not measured in this study. | [Recha et al. (2016), Arid Land Research and Management](#recha) |
| Water · Common bean seasonal ET · Katumani short rains | 400 mm | 281.3 mm | outside range | Coefficient-based seasonal requirement for an approximately 80-day dry bean crop. This endpoint is distinct from measured water use under rainfall stress. | [J. B. Kioko Musingi (1990), University of Nairobi MSc thesis](#musingi) |
| Water · Common bean actual water use · rainfed and irrigated | 400 mm | 187–245 mm rainfed and 481–503 mm fully irrigated | no usable benchmark | Treatment water use reflects soil storage, rainfall, supplemental water and a short-season cultivar. Pooling irrigation regimes would give a misleading reference range for one nominal ET input. | [Sennhenn et al. (2017), Frontiers in Plant Science](#sennhenn) |
| Water · Soil-water carryover and simultaneous crop competition | Seasonal bucket starts empty. One crop per slot. | Sole crops had higher near-surface moisture than the intercrop at 4 and 8 weeks after planting in 2019 short rains. | no usable benchmark | Observations are within a season in the top 20 cm. The trial does not estimate planting-time water carryover between the model's two crop slots. | [Wafula et al. (2022), Tropical and Subtropical Agroecosystems](#wafula) |
| Climate fit · Common bean maturity · Katumani short rains | 100 days | 69 to 78 days | outside range | Short-season KAT X56 physiological maturity. The catalog window is longer and may include time from maturity to harvest. | [Sennhenn et al. (2017), Frontiers in Plant Science](#sennhenn) |
| Climate fit · Early maize maturity · Machakos | 120 days | 100 to 125 days | inside range | Study's locally grown early-maturity group. The extra-early group is reported at 90–110 days and is distinct from the main comparison. | [Ndegwa et al. (2022), Weather, Climate, and Society](#ndegwa) |
| Climate fit · Seasonal grain yields and intercropping · Katumani | Binary thermal and rainfall suitability per crop window. One crop per slot. | Maize sole vs intercrop 2.88 vs 3.21 t/ha in 2019 short rains and 0.97 vs 1.08 in 2020 long rains. Beans 0.44–1.64 t/ha in contrasting 2019 treatments, with crop failure in 2020 long rains. | no usable benchmark | Cropping system effect on maize grain yield was significant in the short-rains trial and not significant in the long-rains trial. Bean treatment extremes also differ in tillage and fertilizer. These trials provide neither a climate cut-off nor a yield comparison for the demo rotation. | [Wafula et al. (2022), Tropical and Subtropical Agroecosystems](#wafula) |
| Climate fit · Rainfed bean grain yield across short rains | 170 mm of in-window rainfall | 1,107 and 978 kg/ha in 2012/13 and 2013/14 at 156 and 259 mm in-crop rainfall, respectively. | no usable benchmark | Both trials produced grain. Grain was observed under a relatively dry crop window, which cautions against reading the model threshold as a crop failure boundary. The study supplies no comparable minimum-rainfall curve. | [Sennhenn et al. (2017), Frontiers in Plant Science](#sennhenn) |
| Income · Sequential versus simultaneous maize–bean systems · Katumani | Unitless per-crop income index. No within-slot mixed crops. | Three-season production value 10,500 KSh/ha for sole-crop rotation, 6,585 for continuous intercrop and 5,198 for continuous sole maize. | no usable benchmark | Table VI values output at historical prices. The model's income index has no calibrated conversion to trial gross or net returns. | [Nadar and Faught (1984), East African Agricultural and Forestry Journal](#nadar) |

## Gaps that matter for interpretation

- Telangana has regional benchmarks for crop ET and rice duration. The local green-manure trial supports a benefit under incorporation. A matched fertilizer response after harvested grain legumes in irrigated rice remains unverified.
- In eastern Kenya, the common-bean N credit is below both Katumani season estimates. The comparison relies on an older yield-equivalence trial with substantial seasonal differences. The separate site-specific mineral N study and the observed maize–bean intercrop responses help explain why a single credit or one crop per slot simplifies the system.
- No comparable regional benchmark was identified for the model's N demand proxy, erosion cover index, same-family disease risk penalty, relative income index or heat and rainfall cut-offs. No evidence here constrains the demo farms' irrigation supply fractions or between-season water carryover. A regional comparison cannot establish local performance or rotation suitability.

## Sources opened and read

<a id="mote"></a>

- **Mote et al. (2018), Journal of Agrometeorology**. Table 2, p. 119 (seasonal ET); p. 118 (variety duration and irrigation regimes). Replicated lowland rice irrigation trial, Rajendranagar, 2013–2014. [Publication](https://pdfs.semanticscholar.org/e027/a990fd565193f4a02e017cf66d4086fcdd89.pdf)

<a id="kumar"></a>

- **Kumar et al. (2022), International Journal of Environment and Climate Change**. Section 3.3, Table 3 in the manuscript; totals agree with the journal abstract, pp. 1047–1052. CROPWAT crop ET estimates for Sangareddy. Published modeled point values give no trial spread. [Publication](https://journalijecc.com/index.php/IJECC/article/view/1124) · [Author manuscript](https://sdiopr.s3.ap-south-1.amazonaws.com/doc/Revised-ms_IJECC_90274_v1.pdf)

<a id="surekha"></a>

- **Surekha et al. (2013), The Andhra Agricultural Journal**. Tables 1–3, pp. 343–345. Five crop years on a Hyderabad Vertisol. Pre-kharif legumes and incorporation were compared with fallow. [Publication](https://aaj.net.in/wp-content/uploads/2024/05/2013_artilcle_602-19.pdf)

<a id="pjtau"></a>

- **PJTSAU, Agro Technologies 2020–21**. Entries 17–18, Performance sections. University extension water budgeting in Northern Telangana, with crop ET and deep percolation recorded separately. [Publication](https://pjtau.edu.in/files/publications/2024/Agro-Technilogies-2020-21.pdf)

<a id="vineela"></a>

- **Vineela et al. (2026), Legume Research**. Figure 1 and Table 5, pp. 1236–1242. Tirupati field trial on how rice establishment and organic nutrient management affect the following green gram. [Publication](https://arccjournals.com/journal/legume-research-an-international-journal/LR-5457)

<a id="nadar"></a>

- **Nadar and Faught (1984), East African Agricultural and Forestry Journal**. Figure 2, Tables II–VI and pp. 130, 135–136. Katumani trials with sole-crop rotations and intercrops. Fertilizer equivalence was inferred from a continuous-maize fertilizer response curve. [Publication](https://pdf.usaid.gov/pdf_docs/PNAAX822.pdf)

<a id="musingi"></a>

- **J. B. Kioko Musingi (1990), University of Nairobi MSc thesis**. §4.2 and Table 4.1, pp. 46–47; §5.2, p. 89. Katumani 1988/89 short rains. Pan evaporation and crop coefficients from one field-season calculation for two dry bean varieties. [Publication](https://erepository.uonbi.ac.ke/server/api/core/bitstreams/15355520-df23-42dd-85ed-17aafcb452c7/content)

<a id="recha"></a>

- **Recha et al. (2016), Arid Land Research and Management**. Table 1, p. 235. Seasonal rainfed maize water budgets for Katumani and Makindu using assumed cultivar median ET and station rainfall. [Publication](https://www.tandfonline.com/doi/pdf/10.1080/15324982.2015.1091398)

<a id="sennhenn"></a>

- **Sennhenn et al. (2017), Frontiers in Plant Science**. Tables 2 and 6 and Agronomic trials. Katumani short-rains field trials in 2012/13 and 2013/14 with rainfed and irrigation treatments. [Publication](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2017.00699/full)

<a id="wafula"></a>

- **Wafula et al. (2022), Tropical and Subtropical Agroecosystems**. Tables 4–5 and Figure 4, pp. 8–11. Katumani plots in the 2019 short and 2020 long rains, with tillage, fertilizer and crop arrangement treatments. [Publication](https://pdfs.semanticscholar.org/16e4/274e23f73c6ffe140d431e425b25df57385f.pdf)

<a id="ndegwa"></a>

- **Ndegwa et al. (2022), Weather, Climate, and Society**. §2b and Table 1 (variety and growth-stage lengths). Machakos county weather-index study with a description of early and extra-early maize varieties. Duration only here. [Publication](https://gala.gre.ac.uk/id/eprint/33893/13/33893_SHEE_Sequenced_crop_evapotranspiration_and_water.pdf)

<a id="kenya_abstract"></a>

- **Kenya Soil Health Consortium, Soil Fertility Management Book of Abstracts**. Abstract of the Kimutwa and Masii maize–bean field study, pp. 172–173. Accessible reprint of the study abstract. Underlying treatment tables could not be read. [Publication](https://www.apni.net/wp-content/uploads/2020/04/Compiled-Book-of-abstracts-Kenya-1.pdf)

<a id="palaniappan"></a>

- **Palaniappan and Siddeswaran (1994), SARP Research Proceedings**. Tables 1–2 and Conclusions, pp. 141–148. Two Coimbatore cycles with grain harvest followed by haulm incorporation. The lowland rice trial crossed crop sequences with fertilizer rates. [Publication](https://edepot.wur.nl/342845)

<a id="adarsh"></a>

- **Adarsh (2019), Kerala Agricultural University MSc thesis**. Materials and Methods §3 and Table 18, pp. 13–15, 54–55. Pilicode trial with four summer pulses and a fallow control in double-cropped lowland rice. The design varies N for the summer pulse. [Publication](https://krishikosh.egranth.ac.in/server/api/core/bitstreams/65189b92-b687-405c-b48f-6dff911d7819/content)

## Unreachable or partially accessible sources

- Publisher full and abstract views returned HTTP 403. The Stockholm University thesis overview was accessible, but it did not provide the paper's complete treatment reference. Excluded from counts. [Barron and Okwach (2005), Mwala runoff water harvesting experiment](https://www.sciencedirect.com/science/article/pii/S0378377404003178)
- Repository timed out. The reprinted abstract was read for context. The original results tables and an isolated seasonal N equivalence range remain unverified. [University of Nairobi thesis on nitrogen fertilizer, bean residue and maize–bean systems at Kimutwa and Masii](https://erepository.uonbi.ac.ke/items/974ed894-5cc2-43e5-81f8-681be03dbce4)
- Publisher viewer returned an empty document and the download could not be read. The author manuscript was opened and checked against the published abstract. [Kumar et al. (2022), journal PDF](https://journalijecc.com/index.php/IJECC/article/view/1124/2249)
- Publisher returned HTTP 502. Tables and figures were read in the full article copy. [Wafula et al. (2022), university journal page](https://www.filey.uady.mx/ojs/index.php/TSA/article/view/4247)
- HTML returned HTTP 403. The publisher PDF opened and Table 1 was read there. [Recha et al. (2016), journal HTML](https://www.tandfonline.com/doi/full/10.1080/15324982.2015.1091398)
- Publisher returned HTTP 403. The University of Greenwich copy opened. [Ndegwa et al. (2022), journal HTML](https://journals.ametsoc.org/view/journals/wcas/14/1/WCAS-D-21-0071.1.xml)
- Direct opening failed. Search snippets suggested bundled variety and management treatments, so they were not used as N-credit evidence. [Telangana frontline demonstrations on green gram preceding rice](https://www.researchgate.net/publication/378334062_Impact_of_technological_interventions_on_green_gram_preceding_rice_for_sustainable_soil_health_management)
- Repository timed out. The separate full-text 2022 journal paper was used. [Wafula, University of Nairobi thesis landing page](https://erepository.uonbi.ac.ke/items/f240d3c0-b14b-45c7-b254-6bfc8a160a52)
- Bot challenge blocked the full text. The candidate reports black gram, a species absent from the catalog. [Rice-fallow black gram lifesaving irrigation, Aduthurai](https://pmc.ncbi.nlm.nih.gov/articles/PMC10988059/)
- Publisher opening failed. No values were taken from the search listing. [Pratibha et al. (1997), ICAR rice–pulse crop sequence study](https://epubs.icar.org.in/index.php/IJAgS/article/view/29850)

Regenerate the report and app data offline with `python -m src.literature_check_p45`.
