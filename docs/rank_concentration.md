# P47 chance-adjusted rank concentration

**EXPLORATORY.** A rotation enters a stable-top set if it ranks in the listed top fraction in at least 50% of the variant-by-draw cells. This describes the tested settings. The thresholds and rounding are design choices. Results are illustrative and need local validation. [Preregistration](p47_plan.md) · [P44](consensus_shortlist.md) · [Every stable-top member and share](#stable-top-member-shares)

Nonempty sets appeared in 5 of 12 at 0.5%, 5 of 12 at 1%, 7 of 12 at 2%. The largest observed share was 90.62%.

P44’s top-three sets were empty for every farm and preset, and P47 found nonempty sets in broader top-percent bands using the same scoring settings and draws.

The largest observed share in every comparison exceeds an independent-shuffle null (floor 1/1001); the null ignores dependence between cells, so this is not a significance test.

## Search spaces and cells

| Farm | P44 variants | P22 draws | Cells per preset | Canonical union | Admitted rotations per cell | Rotations per cell in top 0.5% | Rotations per cell in top 1% | Rotations per cell in top 2% |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| US High Plains B | 16 | 512 | 8,192 | 330 | 3–330 | 1–2 | 1–4 | 1–7 |
| Telangana A | 1 | 512 | 512 | 303,132 | 1,137–303,132 | 6–1,516 | 12–3,032 | 23–6,063 |
| Makueni North Candidate | 1 | 512 | 512 | 41,707 | 1–41,706 | 1–209 | 1–418 | 1–835 |

Percentile is 100 times (rank minus 1) divided by the number of admitted rotations. Ineligible rotations get zero hits and keep all cells in the denominator. The code selects only the ranks needed to reproduce P44's top-one and top-three counts and the three P47 cutoffs. Each band column gives the minimum and maximum absolute number of rotations admitted to that top band in a single cell. Counts vary with eligibility. The slot count rounds up, so different thresholds can occupy the same number of slots in small cells.

## Set size, largest share and shuffled reference

1,000 independent null replicates preserve the admitted rotation labels in each cell and shuffle their ordering. The maximum is taken over the full canonical union. The 95% range is a descriptive spread of shuffled maxima.

| Farm | Preset | Top fraction | Members | Largest share | Null mean members | Null mean largest share | Null largest share 95% range |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| US High Plains B | Water Saver | 0.5% | 0 | 16.70% | 0.00 | 1.40% | 1.16% to 1.65% |
| US High Plains B | Water Saver | 1% | 0 | 18.73% | 0.00 | 1.81% | 1.53% to 2.09% |
| US High Plains B | Water Saver | 2% | 0 | 23.93% | 0.00 | 2.72% | 2.34% to 3.08% |
| US High Plains B | Soil Builder | 0.5% | 0 | 22.14% | 0.00 | 1.40% | 1.16% to 1.65% |
| US High Plains B | Soil Builder | 1% | 0 | 24.90% | 0.00 | 1.81% | 1.53% to 2.09% |
| US High Plains B | Soil Builder | 2% | 0 | 31.91% | 0.00 | 2.72% | 2.34% to 3.08% |
| US High Plains B | Income | 0.5% | 0 | 15.01% | 0.00 | 1.40% | 1.16% to 1.65% |
| US High Plains B | Income | 1% | 0 | 18.38% | 0.00 | 1.81% | 1.53% to 2.09% |
| US High Plains B | Income | 2% | 0 | 25.16% | 0.00 | 2.72% | 2.34% to 3.08% |
| US High Plains B | Balanced | 0.5% | 0 | 15.82% | 0.00 | 1.40% | 1.16% to 1.65% |
| US High Plains B | Balanced | 1% | 0 | 17.55% | 0.00 | 1.81% | 1.53% to 2.09% |
| US High Plains B | Balanced | 2% | 0 | 22.55% | 0.00 | 2.72% | 2.34% to 3.08% |
| Telangana A | Water Saver | 0.5% | 96 | 85.35% | 0.00 | 1.76% | 1.56% to 2.15% |
| Telangana A | Water Saver | 1% | 126 | 89.84% | 0.00 | 2.49% | 2.34% to 2.93% |
| Telangana A | Water Saver | 2% | 283 | 90.62% | 0.00 | 3.73% | 3.32% to 4.30% |
| Telangana A | Soil Builder | 0.5% | 30 | 72.46% | 0.00 | 1.76% | 1.56% to 2.15% |
| Telangana A | Soil Builder | 1% | 47 | 80.27% | 0.00 | 2.49% | 2.34% to 2.93% |
| Telangana A | Soil Builder | 2% | 105 | 84.77% | 0.00 | 3.73% | 3.32% to 4.30% |
| Telangana A | Income | 0.5% | 0 | 41.80% | 0.00 | 1.76% | 1.56% to 2.15% |
| Telangana A | Income | 1% | 0 | 47.07% | 0.00 | 2.49% | 2.34% to 2.93% |
| Telangana A | Income | 2% | 2 | 51.17% | 0.00 | 3.73% | 3.32% to 4.30% |
| Telangana A | Balanced | 0.5% | 8 | 62.50% | 0.00 | 1.76% | 1.56% to 2.15% |
| Telangana A | Balanced | 1% | 20 | 67.77% | 0.00 | 2.49% | 2.34% to 2.93% |
| Telangana A | Balanced | 2% | 45 | 74.61% | 0.00 | 3.73% | 3.32% to 4.30% |
| Makueni North Candidate | Water Saver | 0.5% | 1 | 51.17% | 0.00 | 2.18% | 1.56% to 3.12% |
| Makueni North Candidate | Water Saver | 1% | 2 | 55.47% | 0.00 | 2.61% | 1.95% to 3.71% |
| Makueni North Candidate | Water Saver | 2% | 12 | 62.11% | 0.00 | 3.53% | 2.73% to 4.69% |
| Makueni North Candidate | Soil Builder | 0.5% | 0 | 40.62% | 0.00 | 2.18% | 1.56% to 3.12% |
| Makueni North Candidate | Soil Builder | 1% | 0 | 46.29% | 0.00 | 2.61% | 1.95% to 3.71% |
| Makueni North Candidate | Soil Builder | 2% | 1 | 52.93% | 0.00 | 3.53% | 2.73% to 4.69% |
| Makueni North Candidate | Income | 0.5% | 1 | 50.39% | 0.00 | 2.18% | 1.56% to 3.12% |
| Makueni North Candidate | Income | 1% | 1 | 56.05% | 0.00 | 2.61% | 1.95% to 3.71% |
| Makueni North Candidate | Income | 2% | 1 | 61.13% | 0.00 | 3.53% | 2.73% to 4.69% |
| Makueni North Candidate | Balanced | 0.5% | 0 | 31.84% | 0.00 | 2.18% | 1.56% to 3.12% |
| Makueni North Candidate | Balanced | 1% | 0 | 34.57% | 0.00 | 2.61% | 1.95% to 3.71% |
| Makueni North Candidate | Balanced | 2% | 0 | 41.21% | 0.00 | 3.53% | 2.73% to 4.69% |

## Published baseline and alternatives

Bold shares mark set membership. These are shares of all cells for the fixed published cycles.

| Farm | Preset | Published strategy | 0.5% | 1% | 2% |
| --- | --- | --- | ---: | ---: | ---: |
| US High Plains B | Water Saver | Baseline · fallow → winter wheat → sorghum | 0.00% | 0.00% | 0.00% |
| US High Plains B | Water Saver | Water Saver · fallow → sorghum → soybean | 8.64% | 13.01% | 19.75% |
| US High Plains B | Water Saver | Soil Builder · fallow → soybean → cereal rye cover | 6.79% | 8.57% | 13.21% |
| US High Plains B | Water Saver | Income · sorghum → soybean → sunflower | 0.00% | 0.00% | 0.00% |
| US High Plains B | Water Saver | Balanced · fallow → winter wheat → soybean | 6.15% | 7.23% | 10.96% |
| US High Plains B | Soil Builder | Baseline · fallow → winter wheat → sorghum | 0.00% | 0.00% | 0.00% |
| US High Plains B | Soil Builder | Water Saver · fallow → sorghum → soybean | 2.64% | 4.00% | 6.69% |
| US High Plains B | Soil Builder | Soil Builder · fallow → soybean → cereal rye cover | 22.14% | 24.90% | 31.91% |
| US High Plains B | Soil Builder | Income · sorghum → soybean → sunflower | 0.49% | 0.78% | 1.27% |
| US High Plains B | Soil Builder | Balanced · fallow → winter wheat → soybean | 0.39% | 0.59% | 0.76% |
| US High Plains B | Income | Baseline · fallow → winter wheat → sorghum | 0.00% | 0.00% | 0.00% |
| US High Plains B | Income | Water Saver · fallow → sorghum → soybean | 0.10% | 0.10% | 0.10% |
| US High Plains B | Income | Soil Builder · fallow → soybean → cereal rye cover | 0.00% | 0.00% | 0.00% |
| US High Plains B | Income | Income · sorghum → soybean → sunflower | 7.13% | 8.74% | 14.14% |
| US High Plains B | Income | Balanced · fallow → winter wheat → soybean | 0.00% | 0.00% | 0.00% |
| US High Plains B | Balanced | Baseline · fallow → winter wheat → sorghum | 0.00% | 0.00% | 0.00% |
| US High Plains B | Balanced | Water Saver · fallow → sorghum → soybean | 7.96% | 11.62% | 16.09% |
| US High Plains B | Balanced | Soil Builder · fallow → soybean → cereal rye cover | 1.86% | 2.66% | 4.35% |
| US High Plains B | Balanced | Income · sorghum → soybean → sunflower | 3.20% | 3.91% | 6.49% |
| US High Plains B | Balanced | Balanced · fallow → winter wheat → soybean | 4.88% | 5.54% | 8.20% |
| Telangana A | Water Saver | Baseline · paddy / paddy → paddy / paddy → paddy / paddy | 0.00% | 0.00% | 0.00% |
| Telangana A | Water Saver | Water Saver · pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow | **54.88%** | **54.88%** | **55.08%** |
| Telangana A | Water Saver | Soil Builder · soybean / fallow → pigeonpea / fallow → pigeonpea / fallow | 46.09% | 46.29% | 46.29% |
| Telangana A | Water Saver | Income · pigeonpea / maize → pigeonpea / maize → pigeonpea / maize | 0.00% | 0.00% | 0.00% |
| Telangana A | Water Saver | Balanced · pigeonpea / fallow → pigeonpea / fallow → pearl millet / fallow | 41.99% | 42.77% | 43.16% |
| Telangana A | Soil Builder | Baseline · paddy / paddy → paddy / paddy → paddy / paddy | 0.00% | 0.00% | 0.00% |
| Telangana A | Soil Builder | Water Saver · pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow | **53.32%** | **54.30%** | **55.08%** |
| Telangana A | Soil Builder | Soil Builder · soybean / fallow → pigeonpea / fallow → pigeonpea / fallow | 46.09% | 46.09% | 46.29% |
| Telangana A | Soil Builder | Income · pigeonpea / maize → pigeonpea / maize → pigeonpea / maize | 0.00% | 0.00% | 0.00% |
| Telangana A | Soil Builder | Balanced · pigeonpea / fallow → pigeonpea / fallow → pearl millet / fallow | 32.23% | 38.09% | 40.62% |
| Telangana A | Income | Baseline · paddy / paddy → paddy / paddy → paddy / paddy | 1.37% | 3.12% | 4.49% |
| Telangana A | Income | Water Saver · pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow | 0.00% | 0.00% | 0.00% |
| Telangana A | Income | Soil Builder · soybean / fallow → pigeonpea / fallow → pigeonpea / fallow | 0.00% | 0.00% | 0.00% |
| Telangana A | Income | Income · pigeonpea / maize → pigeonpea / maize → pigeonpea / maize | 21.09% | 25.00% | 29.10% |
| Telangana A | Income | Balanced · pigeonpea / fallow → pigeonpea / fallow → pearl millet / fallow | 0.00% | 0.00% | 0.00% |
| Telangana A | Balanced | Baseline · paddy / paddy → paddy / paddy → paddy / paddy | 0.00% | 0.00% | 0.00% |
| Telangana A | Balanced | Water Saver · pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow | 46.48% | 49.61% | **52.15%** |
| Telangana A | Balanced | Soil Builder · soybean / fallow → pigeonpea / fallow → pigeonpea / fallow | 43.36% | 44.14% | 44.92% |
| Telangana A | Balanced | Income · pigeonpea / maize → pigeonpea / maize → pigeonpea / maize | 1.17% | 3.12% | 4.88% |
| Telangana A | Balanced | Balanced · pigeonpea / fallow → pigeonpea / fallow → pearl millet / fallow | 33.79% | 37.70% | 40.04% |
| Makueni North Candidate | Water Saver | Baseline · maize / common bean → maize / common bean → maize / common bean | 0.98% | 0.98% | 0.98% |
| Makueni North Candidate | Water Saver | Water Saver · green gram / fallow → green gram / fallow → green gram / fallow | 48.24% | **53.52%** | **62.11%** |
| Makueni North Candidate | Water Saver | Soil Builder · green gram / pearl millet → green gram / pearl millet → green gram / pearl millet | 0.00% | 0.20% | 0.78% |
| Makueni North Candidate | Water Saver | Income · maize / green gram → maize / green gram → maize / green gram | 0.00% | 0.00% | 0.00% |
| Makueni North Candidate | Water Saver | Balanced · green gram / fallow → green gram / pearl millet → green gram / pearl millet | 1.56% | 4.49% | 10.55% |
| Makueni North Candidate | Soil Builder | Baseline · maize / common bean → maize / common bean → maize / common bean | 0.98% | 0.98% | 0.98% |
| Makueni North Candidate | Soil Builder | Water Saver · green gram / fallow → green gram / fallow → green gram / fallow | 40.62% | 46.29% | **52.93%** |
| Makueni North Candidate | Soil Builder | Soil Builder · green gram / pearl millet → green gram / pearl millet → green gram / pearl millet | 23.83% | 28.32% | 33.79% |
| Makueni North Candidate | Soil Builder | Income · maize / green gram → maize / green gram → maize / green gram | 0.00% | 0.00% | 0.00% |
| Makueni North Candidate | Soil Builder | Balanced · green gram / fallow → green gram / pearl millet → green gram / pearl millet | 24.80% | 29.10% | 34.38% |
| Makueni North Candidate | Income | Baseline · maize / common bean → maize / common bean → maize / common bean | **50.39%** | **56.05%** | **61.13%** |
| Makueni North Candidate | Income | Water Saver · green gram / fallow → green gram / fallow → green gram / fallow | 0.98% | 2.15% | 2.73% |
| Makueni North Candidate | Income | Soil Builder · green gram / pearl millet → green gram / pearl millet → green gram / pearl millet | 19.53% | 24.41% | 30.08% |
| Makueni North Candidate | Income | Income · maize / green gram → maize / green gram → maize / green gram | 27.15% | 30.86% | 34.57% |
| Makueni North Candidate | Income | Balanced · green gram / fallow → green gram / pearl millet → green gram / pearl millet | 0.78% | 2.73% | 5.86% |
| Makueni North Candidate | Balanced | Baseline · maize / common bean → maize / common bean → maize / common bean | 2.73% | 3.52% | 4.10% |
| Makueni North Candidate | Balanced | Water Saver · green gram / fallow → green gram / fallow → green gram / fallow | 31.84% | 34.57% | 41.21% |
| Makueni North Candidate | Balanced | Soil Builder · green gram / pearl millet → green gram / pearl millet → green gram / pearl millet | 24.22% | 27.54% | 30.47% |
| Makueni North Candidate | Balanced | Income · maize / green gram → maize / green gram → maize / green gram | 2.34% | 4.30% | 5.86% |
| Makueni North Candidate | Balanced | Balanced · green gram / fallow → green gram / pearl millet → green gram / pearl millet | 21.29% | 26.76% | 30.27% |

## Stable-top member shares

Each entry shows the number and share of all variant-by-draw cells in the band. A dash means the rotation did not enter the stable-top set at that cutoff. [Saved member data](../data/processed/rank_concentration_p47.json)

### US High Plains B

**Water Saver.** All three sets were empty.

**Soil Builder.** All three sets were empty.

**Income.** All three sets were empty.

**Balanced.** All three sets were empty.

### Telangana A

#### Water Saver

| Canonical rotation | Top 0.5% | Top 1% | Top 2% |
| --- | ---: | ---: | ---: |
| green gram / fallow → green gram / fallow → green gram / fallow | 437/512 (85.35%) | 460/512 (89.84%) | 464/512 (90.62%) |
| cowpea / fallow → cowpea / fallow → cowpea / fallow | 424/512 (82.81%) | 445/512 (86.91%) | 458/512 (89.45%) |
| common bean / fallow → common bean / fallow → common bean / fallow | 414/512 (80.86%) | 439/512 (85.74%) | 455/512 (88.87%) |
| green gram / fallow → cowpea / fallow → cowpea / fallow | 407/512 (79.49%) | 418/512 (81.64%) | 423/512 (82.62%) |
| green gram / fallow → green gram / fallow → cowpea / fallow | 407/512 (79.49%) | 418/512 (81.64%) | 422/512 (82.42%) |
| common bean / fallow → common bean / fallow → green gram / fallow | 403/512 (78.71%) | 414/512 (80.86%) | 417/512 (81.45%) |
| common bean / fallow → green gram / fallow → green gram / fallow | 402/512 (78.52%) | 414/512 (80.86%) | 417/512 (81.45%) |
| common bean / fallow → common bean / fallow → cowpea / fallow | 380/512 (74.22%) | 401/512 (78.32%) | 413/512 (80.66%) |
| common bean / fallow → cowpea / fallow → cowpea / fallow | 381/512 (74.41%) | 400/512 (78.12%) | 413/512 (80.66%) |
| green gram / fallow → green gram / fallow → sunflower / fallow | 323/512 (63.09%) | 361/512 (70.51%) | 385/512 (75.20%) |
| maize / fallow → green gram / fallow → green gram / fallow | 310/512 (60.55%) | 361/512 (70.51%) | 382/512 (74.61%) |
| common bean / fallow → green gram / fallow → cowpea / fallow | 369/512 (72.07%) | 376/512 (73.44%) | 379/512 (74.02%) |
| common bean / fallow → cowpea / fallow → green gram / fallow | 369/512 (72.07%) | 376/512 (73.44%) | 379/512 (74.02%) |
| paddy / fallow → green gram / fallow → green gram / fallow | 323/512 (63.09%) | 352/512 (68.75%) | 371/512 (72.46%) |
| sunflower / fallow → cowpea / fallow → cowpea / fallow | 288/512 (56.25%) | 343/512 (66.99%) | 369/512 (72.07%) |
| maize / fallow → cowpea / fallow → cowpea / fallow | 284/512 (55.47%) | 332/512 (64.84%) | 366/512 (71.48%) |
| common bean / fallow → common bean / fallow → sunflower / fallow | 280/512 (54.69%) | 340/512 (66.41%) | 366/512 (71.48%) |
| paddy / fallow → common bean / fallow → common bean / fallow | 295/512 (57.62%) | 343/512 (66.99%) | 364/512 (71.09%) |
| maize / fallow → common bean / fallow → common bean / fallow | 280/512 (54.69%) | 334/512 (65.23%) | 364/512 (71.09%) |
| paddy / fallow → cowpea / fallow → cowpea / fallow | 300/512 (58.59%) | 342/512 (66.80%) | 362/512 (70.70%) |
| green gram / fallow → green gram / fallow → pearl millet / fallow | 336/512 (65.62%) | 353/512 (68.95%) | 360/512 (70.31%) |
| pearl millet / fallow → cowpea / fallow → cowpea / fallow | 328/512 (64.06%) | 350/512 (68.36%) | 359/512 (70.12%) |
| soybean / fallow → soybean / fallow → soybean / fallow | 354/512 (69.14%) | 356/512 (69.53%) | 357/512 (69.73%) |
| common bean / fallow → common bean / fallow → pearl millet / fallow | 313/512 (61.13%) | 346/512 (67.58%) | 352/512 (68.75%) |
| green gram / fallow → pearl millet / fallow → pearl millet / fallow | 303/512 (59.18%) | 332/512 (64.84%) | 351/512 (68.55%) |
| green gram / fallow → sunflower / fallow → cowpea / fallow | 302/512 (58.98%) | 333/512 (65.04%) | 350/512 (68.36%) |
| green gram / fallow → cowpea / fallow → sunflower / fallow | 302/512 (58.98%) | 333/512 (65.04%) | 350/512 (68.36%) |
| pearl millet / fallow → pearl millet / fallow → cowpea / fallow | 287/512 (56.05%) | 324/512 (63.28%) | 349/512 (68.16%) |
| common bean / fallow → green gram / fallow → sunflower / fallow | 294/512 (57.42%) | 335/512 (65.43%) | 346/512 (67.58%) |
| common bean / fallow → sunflower / fallow → green gram / fallow | 292/512 (57.03%) | 334/512 (65.23%) | 346/512 (67.58%) |
| maize / fallow → green gram / fallow → cowpea / fallow | 288/512 (56.25%) | 328/512 (64.06%) | 345/512 (67.38%) |
| maize / fallow → cowpea / fallow → green gram / fallow | 288/512 (56.25%) | 328/512 (64.06%) | 345/512 (67.38%) |
| sorghum / fallow → green gram / fallow → green gram / fallow | 302/512 (58.98%) | 332/512 (64.84%) | 343/512 (66.99%) |
| maize / fallow → common bean / fallow → green gram / fallow | 278/512 (54.30%) | 328/512 (64.06%) | 343/512 (66.99%) |
| maize / fallow → green gram / fallow → common bean / fallow | 278/512 (54.30%) | 328/512 (64.06%) | 343/512 (66.99%) |
| common bean / fallow → pearl millet / fallow → pearl millet / fallow | 288/512 (56.25%) | 321/512 (62.70%) | 343/512 (66.99%) |
| sorghum / fallow → common bean / fallow → common bean / fallow | 279/512 (54.49%) | 319/512 (62.30%) | 342/512 (66.80%) |
| pearl millet / fallow → pearl millet / fallow → pearl millet / fallow | 273/512 (53.32%) | 313/512 (61.13%) | 342/512 (66.80%) |
| sorghum / fallow → cowpea / fallow → cowpea / fallow | 293/512 (57.23%) | 320/512 (62.50%) | 340/512 (66.41%) |
| paddy / fallow → green gram / fallow → cowpea / fallow | 292/512 (57.03%) | 326/512 (63.67%) | 340/512 (66.41%) |
| paddy / fallow → cowpea / fallow → green gram / fallow | 292/512 (57.03%) | 326/512 (63.67%) | 340/512 (66.41%) |
| paddy / fallow → common bean / fallow → green gram / fallow | 295/512 (57.62%) | 318/512 (62.11%) | 336/512 (65.62%) |
| paddy / fallow → green gram / fallow → common bean / fallow | 295/512 (57.62%) | 318/512 (62.11%) | 336/512 (65.62%) |
| green gram / fallow → sunflower / fallow → sunflower / fallow | — | 276/512 (53.91%) | 335/512 (65.43%) |
| common bean / fallow → sunflower / fallow → cowpea / fallow | — | 305/512 (59.57%) | 332/512 (64.84%) |
| common bean / fallow → cowpea / fallow → sunflower / fallow | — | 305/512 (59.57%) | 332/512 (64.84%) |
| paddy / fallow → common bean / fallow → cowpea / fallow | 262/512 (51.17%) | 307/512 (59.96%) | 330/512 (64.45%) |
| paddy / fallow → cowpea / fallow → common bean / fallow | 262/512 (51.17%) | 307/512 (59.96%) | 330/512 (64.45%) |
| green gram / fallow → pearl millet / fallow → cowpea / fallow | 316/512 (61.72%) | 325/512 (63.48%) | 330/512 (64.45%) |
| green gram / fallow → cowpea / fallow → pearl millet / fallow | 316/512 (61.72%) | 325/512 (63.48%) | 330/512 (64.45%) |
| maize / fallow → common bean / fallow → cowpea / fallow | 257/512 (50.20%) | 305/512 (59.57%) | 329/512 (64.26%) |
| maize / fallow → cowpea / fallow → common bean / fallow | 257/512 (50.20%) | 305/512 (59.57%) | 329/512 (64.26%) |
| common bean / fallow → pearl millet / fallow → cowpea / fallow | 298/512 (58.20%) | 320/512 (62.50%) | 326/512 (63.67%) |
| common bean / fallow → cowpea / fallow → pearl millet / fallow | 297/512 (58.01%) | 320/512 (62.50%) | 326/512 (63.67%) |
| common bean / fallow → common bean / fallow → soybean / fallow | 321/512 (62.70%) | 323/512 (63.09%) | 324/512 (63.28%) |
| common bean / fallow → soybean / fallow → soybean / fallow | 322/512 (62.89%) | 323/512 (63.09%) | 324/512 (63.28%) |
| soybean / fallow → soybean / fallow → green gram / fallow | 324/512 (63.28%) | 324/512 (63.28%) | 324/512 (63.28%) |
| soybean / fallow → green gram / fallow → green gram / fallow | 324/512 (63.28%) | 324/512 (63.28%) | 324/512 (63.28%) |
| paddy / fallow → paddy / fallow → green gram / fallow | — | 276/512 (53.91%) | 322/512 (62.89%) |
| common bean / fallow → green gram / fallow → pearl millet / fallow | 308/512 (60.16%) | 318/512 (62.11%) | 322/512 (62.89%) |
| common bean / fallow → pearl millet / fallow → green gram / fallow | 308/512 (60.16%) | 318/512 (62.11%) | 322/512 (62.89%) |
| soybean / fallow → soybean / fallow → cowpea / fallow | 321/512 (62.70%) | 321/512 (62.70%) | 321/512 (62.70%) |
| soybean / fallow → cowpea / fallow → cowpea / fallow | 318/512 (62.11%) | 321/512 (62.70%) | 321/512 (62.70%) |
| green gram / fallow → cowpea / fallow → cowpea / sunflower | — | — | 319/512 (62.30%) |
| green gram / fallow → cowpea / sunflower → cowpea / fallow | — | — | 319/512 (62.30%) |
| green gram / sunflower → cowpea / fallow → cowpea / fallow | — | — | 319/512 (62.30%) |
| sorghum / fallow → green gram / fallow → cowpea / fallow | 287/512 (56.05%) | 308/512 (60.16%) | 318/512 (62.11%) |
| sorghum / fallow → cowpea / fallow → green gram / fallow | 287/512 (56.05%) | 308/512 (60.16%) | 318/512 (62.11%) |
| soybean / fallow → soybean / fallow → sunflower / fallow | 308/512 (60.16%) | 314/512 (61.33%) | 318/512 (62.11%) |
| sorghum / fallow → sorghum / fallow → green gram / fallow | — | 285/512 (55.66%) | 317/512 (61.91%) |
| green gram / fallow → green gram / fallow → cowpea / sunflower | — | — | 317/512 (61.91%) |
| green gram / fallow → green gram / sunflower → cowpea / fallow | — | — | 317/512 (61.91%) |
| green gram / fallow → cowpea / fallow → green gram / sunflower | — | — | 317/512 (61.91%) |
| sorghum / fallow → common bean / fallow → cowpea / fallow | 262/512 (51.17%) | 292/512 (57.03%) | 316/512 (61.72%) |
| sorghum / fallow → cowpea / fallow → common bean / fallow | 262/512 (51.17%) | 292/512 (57.03%) | 316/512 (61.72%) |
| green gram / fallow → green gram / fallow → green gram / sunflower | — | — | 316/512 (61.72%) |
| maize / fallow → maize / fallow → green gram / fallow | — | — | 314/512 (61.33%) |
| paddy / fallow → soybean / fallow → soybean / fallow | 302/512 (58.98%) | 312/512 (60.94%) | 313/512 (61.13%) |
| soybean / fallow → soybean / fallow → soybean / sunflower | — | 296/512 (57.81%) | 313/512 (61.13%) |
| sorghum / fallow → common bean / fallow → green gram / fallow | 279/512 (54.49%) | 304/512 (59.38%) | 312/512 (60.94%) |
| sorghum / fallow → green gram / fallow → common bean / fallow | 279/512 (54.49%) | 304/512 (59.38%) | 312/512 (60.94%) |
| maize / fallow → soybean / fallow → soybean / fallow | 302/512 (58.98%) | 305/512 (59.57%) | 312/512 (60.94%) |
| paddy / fallow → paddy / fallow → cowpea / fallow | — | 260/512 (50.78%) | 311/512 (60.74%) |
| soybean / fallow → soybean / fallow → soybean / paddy | — | 276/512 (53.91%) | 311/512 (60.74%) |
| sorghum / fallow → sorghum / fallow → cowpea / fallow | — | 268/512 (52.34%) | 309/512 (60.35%) |
| paddy / fallow → green gram / fallow → sunflower / fallow | — | 271/512 (52.93%) | 308/512 (60.16%) |
| paddy / fallow → sunflower / fallow → green gram / fallow | — | 271/512 (52.93%) | 308/512 (60.16%) |
| maize / fallow → green gram / fallow → sunflower / fallow | — | 256/512 (50.00%) | 308/512 (60.16%) |
| maize / fallow → sunflower / fallow → green gram / fallow | — | 256/512 (50.00%) | 308/512 (60.16%) |
| common bean / fallow → green gram / fallow → green gram / sunflower | — | — | 307/512 (59.96%) |
| common bean / fallow → green gram / sunflower → green gram / fallow | — | — | 307/512 (59.96%) |
| common bean / fallow → sunflower / fallow → sunflower / fallow | — | — | 307/512 (59.96%) |
| common bean / sunflower → green gram / fallow → green gram / fallow | — | — | 307/512 (59.96%) |
| sunflower / fallow → sunflower / fallow → cowpea / fallow | — | — | 307/512 (59.96%) |
| paddy / fallow → paddy / fallow → common bean / fallow | — | 257/512 (50.20%) | 305/512 (59.57%) |
| common bean / fallow → common bean / fallow → green gram / sunflower | — | — | 305/512 (59.57%) |
| common bean / fallow → common bean / sunflower → green gram / fallow | — | — | 305/512 (59.57%) |
| common bean / fallow → green gram / fallow → common bean / sunflower | — | — | 305/512 (59.57%) |
| soybean / fallow → soybean / fallow → soybean / maize | — | 266/512 (51.95%) | 305/512 (59.57%) |
| sorghum / fallow → sorghum / fallow → common bean / fallow | — | 267/512 (52.15%) | 302/512 (58.98%) |
| paddy / fallow → maize / fallow → green gram / fallow | — | 262/512 (51.17%) | 299/512 (58.40%) |
| paddy / fallow → green gram / fallow → maize / fallow | — | 262/512 (51.17%) | 299/512 (58.40%) |
| soybean / fallow → sunflower / fallow → sunflower / fallow | — | — | 298/512 (58.20%) |
| common bean / fallow → soybean / fallow → green gram / fallow | 294/512 (57.42%) | 294/512 (57.42%) | 294/512 (57.42%) |
| common bean / fallow → green gram / fallow → soybean / fallow | 294/512 (57.42%) | 294/512 (57.42%) | 294/512 (57.42%) |
| paddy / fallow → common bean / fallow → sunflower / fallow | — | — | 293/512 (57.23%) |
| paddy / fallow → sunflower / fallow → common bean / fallow | — | — | 293/512 (57.23%) |
| maize / fallow → maize / fallow → common bean / fallow | — | — | 293/512 (57.23%) |
| soybean / fallow → green gram / fallow → sunflower / fallow | 280/512 (54.69%) | 291/512 (56.84%) | 293/512 (57.23%) |
| soybean / fallow → sunflower / fallow → green gram / fallow | 280/512 (54.69%) | 291/512 (56.84%) | 293/512 (57.23%) |
| common bean / fallow → soybean / fallow → cowpea / fallow | 290/512 (56.64%) | 292/512 (57.03%) | 292/512 (57.03%) |
| common bean / fallow → cowpea / fallow → soybean / fallow | 290/512 (56.64%) | 292/512 (57.03%) | 292/512 (57.03%) |
| soybean / fallow → green gram / fallow → cowpea / fallow | 292/512 (57.03%) | 292/512 (57.03%) | 292/512 (57.03%) |
| soybean / fallow → cowpea / fallow → green gram / fallow | 292/512 (57.03%) | 292/512 (57.03%) | 292/512 (57.03%) |
| maize / fallow → green gram / fallow → pearl millet / fallow | — | 257/512 (50.20%) | 291/512 (56.84%) |
| maize / fallow → pearl millet / fallow → green gram / fallow | — | 257/512 (50.20%) | 291/512 (56.84%) |
| maize / fallow → maize / fallow → cowpea / fallow | — | — | 290/512 (56.64%) |
| soybean / fallow → soybean / fallow → green gram / sunflower | — | 272/512 (53.12%) | 289/512 (56.45%) |
| soybean / fallow → soybean / sunflower → green gram / fallow | — | 272/512 (53.12%) | 289/512 (56.45%) |
| soybean / fallow → green gram / fallow → soybean / sunflower | — | 271/512 (52.93%) | 289/512 (56.45%) |
| green gram / fallow → pearl millet / fallow → sunflower / fallow | — | 265/512 (51.76%) | 289/512 (56.45%) |
| green gram / fallow → sunflower / fallow → pearl millet / fallow | — | 265/512 (51.76%) | 289/512 (56.45%) |
| paddy / fallow → sunflower / fallow → cowpea / fallow | — | — | 288/512 (56.25%) |
| paddy / fallow → cowpea / fallow → sunflower / fallow | — | — | 288/512 (56.25%) |
| common bean / fallow → green gram / fallow → cowpea / sunflower | — | — | 287/512 (56.05%) |
| common bean / fallow → green gram / sunflower → cowpea / fallow | — | — | 287/512 (56.05%) |
| common bean / fallow → cowpea / fallow → green gram / sunflower | — | — | 287/512 (56.05%) |
| common bean / fallow → cowpea / sunflower → green gram / fallow | — | — | 287/512 (56.05%) |
| common bean / sunflower → green gram / fallow → cowpea / fallow | — | — | 287/512 (56.05%) |
| common bean / sunflower → cowpea / fallow → green gram / fallow | — | — | 287/512 (56.05%) |
| paddy / fallow → paddy / fallow → soybean / fallow | — | — | 286/512 (55.86%) |
| maize / fallow → soybean / fallow → green gram / fallow | 271/512 (52.93%) | 285/512 (55.66%) | 286/512 (55.86%) |
| maize / fallow → green gram / fallow → soybean / fallow | 271/512 (52.93%) | 285/512 (55.66%) | 286/512 (55.86%) |
| soybean / fallow → sunflower / fallow → cowpea / fallow | 261/512 (50.98%) | 278/512 (54.30%) | 286/512 (55.86%) |
| soybean / fallow → cowpea / fallow → sunflower / fallow | 261/512 (50.98%) | 278/512 (54.30%) | 286/512 (55.86%) |
| common bean / fallow → soybean / fallow → sunflower / fallow | 264/512 (51.56%) | 279/512 (54.49%) | 285/512 (55.66%) |
| common bean / fallow → sunflower / fallow → soybean / fallow | 264/512 (51.56%) | 279/512 (54.49%) | 285/512 (55.66%) |
| soybean / fallow → soybean / fallow → green gram / paddy | — | — | 285/512 (55.66%) |
| soybean / fallow → soybean / paddy → green gram / fallow | — | — | 285/512 (55.66%) |
| soybean / fallow → green gram / fallow → soybean / paddy | — | — | 285/512 (55.66%) |
| maize / fallow → common bean / fallow → sunflower / fallow | — | — | 284/512 (55.47%) |
| maize / fallow → sunflower / fallow → common bean / fallow | — | — | 284/512 (55.47%) |
| pearl millet / fallow → sunflower / fallow → cowpea / fallow | — | — | 284/512 (55.47%) |
| pearl millet / fallow → cowpea / fallow → sunflower / fallow | — | — | 284/512 (55.47%) |
| paddy / fallow → maize / fallow → cowpea / fallow | — | — | 283/512 (55.27%) |
| paddy / fallow → cowpea / fallow → maize / fallow | — | — | 283/512 (55.27%) |
| maize / fallow → sunflower / fallow → cowpea / fallow | — | — | 283/512 (55.27%) |
| maize / fallow → cowpea / fallow → sunflower / fallow | — | — | 283/512 (55.27%) |
| cowpea / fallow → cowpea / fallow → cowpea / sunflower | — | — | 283/512 (55.27%) |
| paddy / fallow → soybean / fallow → green gram / fallow | 271/512 (52.93%) | 279/512 (54.49%) | 282/512 (55.08%) |
| paddy / fallow → green gram / fallow → soybean / fallow | 271/512 (52.93%) | 279/512 (54.49%) | 282/512 (55.08%) |
| maize / fallow → pearl millet / fallow → cowpea / fallow | — | — | 282/512 (55.08%) |
| maize / fallow → cowpea / fallow → pearl millet / fallow | — | — | 282/512 (55.08%) |
| common bean / fallow → pearl millet / fallow → sunflower / fallow | — | — | 282/512 (55.08%) |
| soybean / fallow → green gram / fallow → green gram / sunflower | — | — | 282/512 (55.08%) |
| soybean / fallow → green gram / sunflower → green gram / fallow | — | — | 282/512 (55.08%) |
| soybean / sunflower → green gram / fallow → green gram / fallow | — | — | 282/512 (55.08%) |
| pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow | 281/512 (54.88%) | 281/512 (54.88%) | 282/512 (55.08%) |
| green gram / fallow → green gram / fallow → green gram / paddy | — | — | 282/512 (55.08%) |
| pearl millet / fallow → pearl millet / fallow → sunflower / fallow | — | — | 282/512 (55.08%) |
| paddy / fallow → maize / fallow → common bean / fallow | — | — | 281/512 (54.88%) |
| paddy / fallow → common bean / fallow → maize / fallow | — | — | 281/512 (54.88%) |
| paddy / fallow → soybean / fallow → cowpea / fallow | 261/512 (50.98%) | 276/512 (53.91%) | 281/512 (54.88%) |
| paddy / fallow → cowpea / fallow → soybean / fallow | 261/512 (50.98%) | 276/512 (53.91%) | 281/512 (54.88%) |
| maize / fallow → maize / fallow → soybean / fallow | — | — | 281/512 (54.88%) |
| common bean / fallow → sunflower / fallow → pearl millet / fallow | — | — | 281/512 (54.88%) |
| soybean / fallow → soybean / fallow → green gram / maize | — | — | 281/512 (54.88%) |
| soybean / fallow → soybean / maize → green gram / fallow | — | — | 281/512 (54.88%) |
| soybean / fallow → green gram / fallow → soybean / maize | — | — | 281/512 (54.88%) |
| paddy / fallow → common bean / fallow → soybean / fallow | 259/512 (50.59%) | 279/512 (54.49%) | 280/512 (54.69%) |
| paddy / fallow → soybean / fallow → common bean / fallow | 259/512 (50.59%) | 279/512 (54.49%) | 280/512 (54.69%) |
| soybean / fallow → soybean / fallow → cowpea / sunflower | — | — | 280/512 (54.69%) |
| soybean / fallow → soybean / sunflower → cowpea / fallow | — | — | 280/512 (54.69%) |
| soybean / fallow → cowpea / fallow → soybean / sunflower | — | — | 280/512 (54.69%) |
| maize / fallow → common bean / fallow → soybean / fallow | 259/512 (50.59%) | 273/512 (53.32%) | 279/512 (54.49%) |
| maize / fallow → soybean / fallow → common bean / fallow | 259/512 (50.59%) | 273/512 (53.32%) | 279/512 (54.49%) |
| maize / fallow → soybean / fallow → cowpea / fallow | 256/512 (50.00%) | 271/512 (52.93%) | 279/512 (54.49%) |
| maize / fallow → cowpea / fallow → soybean / fallow | 256/512 (50.00%) | 271/512 (52.93%) | 279/512 (54.49%) |
| common bean / fallow → soybean / fallow → soybean / sunflower | — | — | 279/512 (54.49%) |
| common bean / fallow → soybean / sunflower → soybean / fallow | — | — | 279/512 (54.49%) |
| common bean / sunflower → soybean / fallow → soybean / fallow | — | — | 279/512 (54.49%) |
| paddy / fallow → pearl millet / fallow → cowpea / fallow | — | — | 278/512 (54.30%) |
| paddy / fallow → cowpea / fallow → pearl millet / fallow | — | — | 278/512 (54.30%) |
| paddy / fallow → pearl millet / fallow → pearl millet / fallow | — | — | 277/512 (54.10%) |
| soybean / fallow → soybean / fallow → pearl millet / fallow | 275/512 (53.71%) | 277/512 (54.10%) | 277/512 (54.10%) |
| sorghum / fallow → soybean / fallow → soybean / fallow | 267/512 (52.15%) | 272/512 (53.12%) | 276/512 (53.91%) |
| paddy / fallow → green gram / fallow → pearl millet / fallow | — | 258/512 (50.39%) | 276/512 (53.91%) |
| paddy / fallow → pearl millet / fallow → green gram / fallow | — | 258/512 (50.39%) | 276/512 (53.91%) |
| sorghum / fallow → pearl millet / fallow → cowpea / fallow | — | — | 275/512 (53.71%) |
| sorghum / fallow → cowpea / fallow → pearl millet / fallow | — | — | 275/512 (53.71%) |
| maize / fallow → pearl millet / fallow → pearl millet / fallow | — | — | 275/512 (53.71%) |
| soybean / fallow → pearl millet / fallow → pearl millet / fallow | — | 263/512 (51.37%) | 274/512 (53.52%) |
| sorghum / fallow → green gram / fallow → sunflower / fallow | — | — | 273/512 (53.32%) |
| sorghum / fallow → sunflower / fallow → green gram / fallow | — | — | 273/512 (53.32%) |
| common bean / fallow → common bean / fallow → common bean / sunflower | — | — | 273/512 (53.32%) |
| soybean / fallow → soybean / fallow → cowpea / paddy | — | — | 273/512 (53.32%) |
| soybean / fallow → soybean / paddy → cowpea / fallow | — | — | 273/512 (53.32%) |
| soybean / fallow → cowpea / fallow → soybean / paddy | — | — | 273/512 (53.32%) |
| paddy / fallow → common bean / fallow → pearl millet / fallow | — | — | 272/512 (53.12%) |
| paddy / fallow → pearl millet / fallow → common bean / fallow | — | — | 272/512 (53.12%) |
| soybean / fallow → soybean / fallow → soybean / common bean | — | — | 272/512 (53.12%) |
| sorghum / fallow → pearl millet / fallow → pearl millet / fallow | — | — | 271/512 (52.93%) |
| paddy / fallow → soybean / fallow → sunflower / fallow | — | — | 271/512 (52.93%) |
| paddy / fallow → sunflower / fallow → soybean / fallow | — | — | 271/512 (52.93%) |
| common bean / fallow → soybean / fallow → soybean / paddy | — | — | 271/512 (52.93%) |
| common bean / fallow → soybean / paddy → soybean / fallow | — | — | 271/512 (52.93%) |
| common bean / paddy → soybean / fallow → soybean / fallow | — | — | 271/512 (52.93%) |
| sorghum / fallow → maize / fallow → green gram / fallow | — | — | 270/512 (52.73%) |
| sorghum / fallow → green gram / fallow → maize / fallow | — | — | 270/512 (52.73%) |
| maize / fallow → common bean / fallow → pearl millet / fallow | — | — | 270/512 (52.73%) |
| maize / fallow → pearl millet / fallow → common bean / fallow | — | — | 270/512 (52.73%) |
| green gram / fallow → cowpea / fallow → cowpea / paddy | — | — | 270/512 (52.73%) |
| green gram / fallow → cowpea / paddy → cowpea / fallow | — | — | 270/512 (52.73%) |
| green gram / paddy → cowpea / fallow → cowpea / fallow | — | — | 270/512 (52.73%) |
| sorghum / fallow → common bean / fallow → pearl millet / fallow | — | — | 269/512 (52.54%) |
| sorghum / fallow → pearl millet / fallow → common bean / fallow | — | — | 269/512 (52.54%) |
| soybean / fallow → soybean / fallow → soybean / green gram | — | — | 269/512 (52.54%) |
| sorghum / fallow → common bean / fallow → sunflower / fallow | — | — | 268/512 (52.34%) |
| sorghum / fallow → sunflower / fallow → common bean / fallow | — | — | 268/512 (52.34%) |
| sorghum / fallow → paddy / fallow → common bean / fallow | — | — | 267/512 (52.15%) |
| sorghum / fallow → paddy / fallow → green gram / fallow | — | — | 267/512 (52.15%) |
| sorghum / fallow → common bean / fallow → paddy / fallow | — | — | 267/512 (52.15%) |
| sorghum / fallow → green gram / fallow → paddy / fallow | — | — | 267/512 (52.15%) |
| sorghum / fallow → paddy / fallow → cowpea / fallow | — | — | 266/512 (51.95%) |
| sorghum / fallow → green gram / fallow → pearl millet / fallow | — | — | 266/512 (51.95%) |
| sorghum / fallow → pearl millet / fallow → green gram / fallow | — | — | 266/512 (51.95%) |
| sorghum / fallow → sunflower / fallow → cowpea / fallow | — | — | 266/512 (51.95%) |
| sorghum / fallow → cowpea / fallow → paddy / fallow | — | — | 266/512 (51.95%) |
| sorghum / fallow → cowpea / fallow → sunflower / fallow | — | — | 266/512 (51.95%) |
| paddy / fallow → maize / fallow → soybean / fallow | — | — | 266/512 (51.95%) |
| paddy / fallow → soybean / fallow → maize / fallow | — | — | 266/512 (51.95%) |
| common bean / fallow → soybean / fallow → soybean / maize | — | — | 266/512 (51.95%) |
| common bean / fallow → soybean / maize → soybean / fallow | — | — | 266/512 (51.95%) |
| common bean / fallow → cowpea / fallow → cowpea / sunflower | — | — | 266/512 (51.95%) |
| common bean / maize → soybean / fallow → soybean / fallow | — | — | 266/512 (51.95%) |
| soybean / fallow → soybean / fallow → cowpea / maize | — | — | 266/512 (51.95%) |
| soybean / fallow → soybean / maize → cowpea / fallow | — | — | 266/512 (51.95%) |
| soybean / fallow → cowpea / fallow → soybean / maize | — | — | 266/512 (51.95%) |
| green gram / fallow → green gram / fallow → cowpea / paddy | — | — | 266/512 (51.95%) |
| green gram / fallow → green gram / paddy → cowpea / fallow | — | — | 266/512 (51.95%) |
| green gram / fallow → cowpea / fallow → green gram / paddy | — | — | 266/512 (51.95%) |
| sorghum / fallow → sorghum / fallow → sorghum / fallow | — | — | 265/512 (51.76%) |
| common bean / fallow → cowpea / sunflower → cowpea / fallow | — | — | 265/512 (51.76%) |
| common bean / sunflower → cowpea / fallow → cowpea / fallow | — | — | 265/512 (51.76%) |
| soybean / fallow → cowpea / fallow → cowpea / sunflower | — | — | 265/512 (51.76%) |
| soybean / fallow → cowpea / sunflower → cowpea / fallow | — | — | 265/512 (51.76%) |
| soybean / sunflower → cowpea / fallow → cowpea / fallow | — | — | 265/512 (51.76%) |
| maize / fallow → soybean / fallow → sunflower / fallow | — | — | 264/512 (51.56%) |
| maize / fallow → sunflower / fallow → soybean / fallow | — | — | 264/512 (51.56%) |
| common bean / fallow → common bean / fallow → soybean / sunflower | — | — | 264/512 (51.56%) |
| common bean / fallow → common bean / sunflower → soybean / fallow | — | — | 264/512 (51.56%) |
| common bean / fallow → soybean / fallow → common bean / sunflower | — | — | 264/512 (51.56%) |
| sorghum / fallow → sorghum / fallow → soybean / fallow | — | — | 261/512 (50.98%) |
| sorghum / fallow → maize / fallow → common bean / fallow | — | — | 261/512 (50.98%) |
| sorghum / fallow → common bean / fallow → maize / fallow | — | — | 261/512 (50.98%) |
| soybean / fallow → green gram / fallow → cowpea / sunflower | — | — | 261/512 (50.98%) |
| soybean / fallow → green gram / sunflower → cowpea / fallow | — | — | 261/512 (50.98%) |
| soybean / fallow → cowpea / fallow → green gram / sunflower | — | — | 261/512 (50.98%) |
| soybean / fallow → cowpea / sunflower → green gram / fallow | — | — | 261/512 (50.98%) |
| soybean / sunflower → green gram / fallow → cowpea / fallow | — | — | 261/512 (50.98%) |
| soybean / sunflower → cowpea / fallow → green gram / fallow | — | — | 261/512 (50.98%) |
| sorghum / fallow → maize / fallow → cowpea / fallow | — | — | 260/512 (50.78%) |
| sorghum / fallow → cowpea / fallow → maize / fallow | — | — | 260/512 (50.78%) |
| common bean / fallow → common bean / fallow → cowpea / sunflower | — | — | 259/512 (50.59%) |
| common bean / fallow → common bean / sunflower → cowpea / fallow | — | — | 259/512 (50.59%) |
| common bean / fallow → green gram / fallow → green gram / paddy | — | — | 259/512 (50.59%) |
| common bean / fallow → green gram / paddy → green gram / fallow | — | — | 259/512 (50.59%) |
| common bean / fallow → cowpea / fallow → common bean / sunflower | — | — | 259/512 (50.59%) |
| common bean / paddy → green gram / fallow → green gram / fallow | — | — | 259/512 (50.59%) |
| soybean / fallow → green gram / fallow → green gram / paddy | — | — | 259/512 (50.59%) |
| soybean / fallow → green gram / paddy → green gram / fallow | — | — | 259/512 (50.59%) |
| soybean / paddy → green gram / fallow → green gram / fallow | — | — | 259/512 (50.59%) |
| green gram / fallow → pearl millet / common bean → pearl millet / fallow | — | — | 259/512 (50.59%) |
| common bean / fallow → soybean / fallow → green gram / sunflower | — | — | 258/512 (50.39%) |
| common bean / fallow → soybean / sunflower → green gram / fallow | — | — | 258/512 (50.39%) |
| common bean / fallow → green gram / fallow → soybean / sunflower | — | — | 258/512 (50.39%) |
| common bean / fallow → green gram / sunflower → soybean / fallow | — | — | 258/512 (50.39%) |
| common bean / sunflower → soybean / fallow → green gram / fallow | — | — | 258/512 (50.39%) |
| common bean / sunflower → green gram / fallow → soybean / fallow | — | — | 258/512 (50.39%) |
| pigeonpea / fallow → pigeonpea / fallow → green gram / fallow | 256/512 (50.00%) | 256/512 (50.00%) | 257/512 (50.20%) |
| pigeonpea / fallow → pigeonpea / fallow → cowpea / fallow | — | — | 257/512 (50.20%) |
| pigeonpea / fallow → green gram / fallow → green gram / fallow | — | 257/512 (50.20%) | 257/512 (50.20%) |
| pigeonpea / fallow → cowpea / fallow → cowpea / fallow | — | 257/512 (50.20%) | 257/512 (50.20%) |

#### Soil Builder

| Canonical rotation | Top 0.5% | Top 1% | Top 2% |
| --- | ---: | ---: | ---: |
| green gram / fallow → green gram / fallow → green gram / fallow | 371/512 (72.46%) | 411/512 (80.27%) | 434/512 (84.77%) |
| cowpea / fallow → cowpea / fallow → cowpea / fallow | 356/512 (69.53%) | 392/512 (76.56%) | 425/512 (83.01%) |
| green gram / fallow → green gram / fallow → cowpea / fallow | 352/512 (68.75%) | 385/512 (75.20%) | 406/512 (79.30%) |
| green gram / fallow → cowpea / fallow → cowpea / fallow | 350/512 (68.36%) | 386/512 (75.39%) | 405/512 (79.10%) |
| common bean / fallow → green gram / fallow → green gram / fallow | 320/512 (62.50%) | 369/512 (72.07%) | 391/512 (76.37%) |
| common bean / fallow → cowpea / fallow → cowpea / fallow | 307/512 (59.96%) | 343/512 (66.99%) | 376/512 (73.44%) |
| common bean / fallow → common bean / fallow → green gram / fallow | 290/512 (56.64%) | 337/512 (65.82%) | 375/512 (73.24%) |
| common bean / fallow → common bean / fallow → common bean / fallow | 256/512 (50.00%) | 309/512 (60.35%) | 370/512 (72.27%) |
| common bean / fallow → common bean / fallow → cowpea / fallow | 267/512 (52.15%) | 324/512 (63.28%) | 360/512 (70.31%) |
| common bean / fallow → green gram / fallow → cowpea / fallow | 299/512 (58.40%) | 335/512 (65.43%) | 360/512 (70.31%) |
| common bean / fallow → cowpea / fallow → green gram / fallow | 299/512 (58.40%) | 335/512 (65.43%) | 360/512 (70.31%) |
| soybean / fallow → soybean / fallow → soybean / fallow | 354/512 (69.14%) | 355/512 (69.34%) | 357/512 (69.73%) |
| soybean / fallow → soybean / fallow → green gram / fallow | 321/512 (62.70%) | 324/512 (63.28%) | 324/512 (63.28%) |
| soybean / fallow → green gram / fallow → green gram / fallow | 306/512 (59.77%) | 315/512 (61.52%) | 323/512 (63.09%) |
| common bean / fallow → soybean / fallow → soybean / fallow | 313/512 (61.13%) | 321/512 (62.70%) | 322/512 (62.89%) |
| soybean / fallow → soybean / fallow → cowpea / fallow | 318/512 (62.11%) | 320/512 (62.50%) | 321/512 (62.70%) |
| soybean / fallow → cowpea / fallow → cowpea / fallow | 296/512 (57.81%) | 312/512 (60.94%) | 319/512 (62.30%) |
| common bean / fallow → common bean / fallow → soybean / fallow | 267/512 (52.15%) | 292/512 (57.03%) | 317/512 (61.91%) |
| soybean / fallow → soybean / fallow → soybean / sunflower | 289/512 (56.45%) | 307/512 (59.96%) | 317/512 (61.91%) |
| soybean / fallow → soybean / fallow → soybean / common bean | 280/512 (54.69%) | 302/512 (58.98%) | 314/512 (61.33%) |
| soybean / fallow → soybean / fallow → soybean / green gram | 281/512 (54.88%) | 299/512 (58.40%) | 308/512 (60.16%) |
| soybean / fallow → soybean / fallow → soybean / cowpea | 275/512 (53.71%) | 289/512 (56.45%) | 300/512 (58.59%) |
| green gram / fallow → green gram / fallow → green gram / sunflower | — | — | 299/512 (58.40%) |
| common bean / fallow → soybean / fallow → green gram / fallow | 270/512 (52.73%) | 287/512 (56.05%) | 292/512 (57.03%) |
| common bean / fallow → green gram / fallow → soybean / fallow | 270/512 (52.73%) | 287/512 (56.05%) | 292/512 (57.03%) |
| soybean / fallow → green gram / fallow → cowpea / fallow | 279/512 (54.49%) | 288/512 (56.25%) | 292/512 (57.03%) |
| soybean / fallow → cowpea / fallow → green gram / fallow | 279/512 (54.49%) | 288/512 (56.25%) | 292/512 (57.03%) |
| common bean / fallow → soybean / fallow → cowpea / fallow | 261/512 (50.98%) | 280/512 (54.69%) | 288/512 (56.25%) |
| common bean / fallow → cowpea / fallow → soybean / fallow | 261/512 (50.98%) | 280/512 (54.69%) | 288/512 (56.25%) |
| green gram / fallow → green gram / fallow → cowpea / sunflower | — | — | 288/512 (56.25%) |
| green gram / fallow → green gram / sunflower → cowpea / fallow | — | — | 288/512 (56.25%) |
| green gram / fallow → cowpea / fallow → green gram / sunflower | — | — | 288/512 (56.25%) |
| soybean / fallow → soybean / fallow → green gram / common bean | — | 263/512 (51.37%) | 287/512 (56.05%) |
| soybean / fallow → soybean / fallow → green gram / sunflower | — | 276/512 (53.91%) | 287/512 (56.05%) |
| soybean / fallow → soybean / common bean → green gram / fallow | — | 263/512 (51.37%) | 287/512 (56.05%) |
| soybean / fallow → soybean / sunflower → green gram / fallow | — | 276/512 (53.91%) | 287/512 (56.05%) |
| soybean / fallow → green gram / fallow → soybean / common bean | — | 263/512 (51.37%) | 287/512 (56.05%) |
| soybean / fallow → green gram / fallow → soybean / sunflower | — | 276/512 (53.91%) | 287/512 (56.05%) |
| soybean / fallow → soybean / fallow → cowpea / sunflower | — | 270/512 (52.73%) | 285/512 (55.66%) |
| soybean / fallow → soybean / sunflower → cowpea / fallow | — | 270/512 (52.73%) | 285/512 (55.66%) |
| soybean / fallow → cowpea / fallow → soybean / sunflower | — | 270/512 (52.73%) | 285/512 (55.66%) |
| green gram / fallow → cowpea / fallow → cowpea / sunflower | — | — | 284/512 (55.47%) |
| soybean / fallow → soybean / fallow → soybean / chickpea | 264/512 (51.56%) | 275/512 (53.71%) | 283/512 (55.27%) |
| green gram / fallow → green gram / fallow → pearl millet / fallow | — | — | 283/512 (55.27%) |
| green gram / fallow → cowpea / sunflower → cowpea / fallow | — | — | 283/512 (55.27%) |
| green gram / sunflower → cowpea / fallow → cowpea / fallow | — | — | 283/512 (55.27%) |
| pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow | 273/512 (53.32%) | 278/512 (54.30%) | 282/512 (55.08%) |
| cowpea / fallow → cowpea / fallow → cowpea / sunflower | — | — | 279/512 (54.49%) |
| soybean / fallow → green gram / fallow → soybean / green gram | — | 262/512 (51.17%) | 277/512 (54.10%) |
| common bean / fallow → soybean / fallow → soybean / sunflower | — | — | 276/512 (53.91%) |
| common bean / fallow → soybean / sunflower → soybean / fallow | — | — | 276/512 (53.91%) |
| common bean / sunflower → soybean / fallow → soybean / fallow | — | — | 276/512 (53.91%) |
| soybean / fallow → soybean / fallow → green gram / cowpea | — | 257/512 (50.20%) | 276/512 (53.91%) |
| soybean / fallow → soybean / cowpea → green gram / fallow | — | 257/512 (50.20%) | 276/512 (53.91%) |
| soybean / fallow → green gram / fallow → soybean / cowpea | — | 257/512 (50.20%) | 276/512 (53.91%) |
| soybean / fallow → soybean / fallow → cowpea / common bean | — | — | 275/512 (53.71%) |
| soybean / fallow → soybean / fallow → cowpea / green gram | — | 258/512 (50.39%) | 275/512 (53.71%) |
| soybean / fallow → soybean / common bean → cowpea / fallow | — | — | 275/512 (53.71%) |
| soybean / fallow → soybean / green gram → cowpea / fallow | — | 258/512 (50.39%) | 275/512 (53.71%) |
| soybean / fallow → cowpea / fallow → soybean / common bean | — | — | 275/512 (53.71%) |
| soybean / fallow → cowpea / fallow → soybean / green gram | — | 258/512 (50.39%) | 275/512 (53.71%) |
| soybean / fallow → soybean / fallow → soybean / paddy | — | — | 274/512 (53.52%) |
| common bean / fallow → soybean / fallow → soybean / green gram | — | — | 272/512 (53.12%) |
| common bean / fallow → soybean / green gram → soybean / fallow | — | — | 272/512 (53.12%) |
| common bean / green gram → soybean / fallow → soybean / fallow | — | — | 272/512 (53.12%) |
| soybean / fallow → soybean / fallow → soybean / field pea | — | 263/512 (51.37%) | 271/512 (52.93%) |
| green gram / fallow → green gram / fallow → green gram / chickpea | — | — | 271/512 (52.93%) |
| common bean / fallow → soybean / common bean → soybean / fallow | — | — | 269/512 (52.54%) |
| green gram / fallow → green gram / fallow → green gram / common bean | — | — | 269/512 (52.54%) |
| green gram / fallow → pearl millet / fallow → cowpea / fallow | — | — | 269/512 (52.54%) |
| green gram / fallow → cowpea / fallow → pearl millet / fallow | — | — | 269/512 (52.54%) |
| soybean / fallow → green gram / fallow → green gram / sunflower | — | — | 268/512 (52.34%) |
| soybean / fallow → green gram / sunflower → green gram / fallow | — | — | 268/512 (52.34%) |
| soybean / sunflower → green gram / fallow → green gram / fallow | — | — | 268/512 (52.34%) |
| green gram / fallow → green gram / fallow → green gram / cowpea | — | — | 268/512 (52.34%) |
| soybean / fallow → soybean / fallow → soybean / maize | — | — | 266/512 (51.95%) |
| soybean / fallow → soybean / fallow → pearl millet / fallow | — | — | 266/512 (51.95%) |
| pearl millet / fallow → cowpea / fallow → cowpea / fallow | — | — | 265/512 (51.76%) |
| green gram / fallow → green gram / fallow → cowpea / chickpea | — | — | 264/512 (51.56%) |
| green gram / fallow → green gram / chickpea → cowpea / fallow | — | — | 264/512 (51.56%) |
| green gram / fallow → cowpea / fallow → green gram / chickpea | — | — | 264/512 (51.56%) |
| green gram / fallow → cowpea / fallow → cowpea / chickpea | — | — | 263/512 (51.37%) |
| green gram / fallow → cowpea / chickpea → cowpea / fallow | — | — | 263/512 (51.37%) |
| green gram / chickpea → cowpea / fallow → cowpea / fallow | — | — | 263/512 (51.37%) |
| common bean / fallow → soybean / fallow → soybean / cowpea | — | — | 262/512 (51.17%) |
| common bean / fallow → soybean / cowpea → soybean / fallow | — | — | 262/512 (51.17%) |
| common bean / cowpea → soybean / fallow → soybean / fallow | — | — | 262/512 (51.17%) |
| green gram / fallow → cowpea / green gram → cowpea / fallow | — | — | 260/512 (50.78%) |
| soybean / fallow → soybean / fallow → green gram / chickpea | — | — | 259/512 (50.59%) |
| soybean / fallow → soybean / chickpea → green gram / fallow | — | — | 259/512 (50.59%) |
| soybean / fallow → green gram / fallow → soybean / chickpea | — | — | 259/512 (50.59%) |
| soybean / fallow → cowpea / fallow → soybean / cowpea | — | — | 258/512 (50.39%) |
| soybean / fallow → cowpea / fallow → cowpea / sunflower | — | — | 258/512 (50.39%) |
| soybean / fallow → cowpea / sunflower → cowpea / fallow | — | — | 258/512 (50.39%) |
| soybean / sunflower → cowpea / fallow → cowpea / fallow | — | — | 258/512 (50.39%) |
| green gram / fallow → cowpea / fallow → green gram / cowpea | — | — | 258/512 (50.39%) |
| common bean / fallow → green gram / fallow → green gram / sunflower | — | — | 257/512 (50.20%) |
| common bean / fallow → green gram / sunflower → green gram / fallow | — | — | 257/512 (50.20%) |
| common bean / sunflower → green gram / fallow → green gram / fallow | — | — | 257/512 (50.20%) |
| soybean / fallow → soybean / fallow → sunflower / fallow | — | — | 257/512 (50.20%) |
| soybean / fallow → soybean / fallow → cowpea / chickpea | — | — | 257/512 (50.20%) |
| soybean / fallow → soybean / chickpea → cowpea / fallow | — | — | 257/512 (50.20%) |
| soybean / fallow → cowpea / fallow → soybean / chickpea | — | — | 257/512 (50.20%) |
| pigeonpea / fallow → pigeonpea / fallow → green gram / fallow | — | — | 256/512 (50.00%) |
| pigeonpea / fallow → pigeonpea / fallow → cowpea / fallow | — | — | 256/512 (50.00%) |

#### Income

| Canonical rotation | Top 0.5% | Top 1% | Top 2% |
| --- | ---: | ---: | ---: |
| soybean / paddy → soybean / paddy → soybean / paddy | — | — | 262/512 (51.17%) |
| soybean / maize → soybean / maize → soybean / maize | — | — | 258/512 (50.39%) |

#### Balanced

| Canonical rotation | Top 0.5% | Top 1% | Top 2% |
| --- | ---: | ---: | ---: |
| green gram / fallow → green gram / fallow → green gram / fallow | 304/512 (59.38%) | 347/512 (67.77%) | 382/512 (74.61%) |
| common bean / fallow → green gram / fallow → green gram / fallow | 270/512 (52.73%) | 312/512 (60.94%) | 356/512 (69.53%) |
| green gram / fallow → green gram / fallow → cowpea / fallow | 270/512 (52.73%) | 313/512 (61.13%) | 356/512 (69.53%) |
| soybean / fallow → soybean / fallow → soybean / fallow | 320/512 (62.50%) | 336/512 (65.62%) | 344/512 (67.19%) |
| common bean / fallow → common bean / fallow → green gram / fallow | — | 287/512 (56.05%) | 338/512 (66.02%) |
| green gram / fallow → cowpea / fallow → cowpea / fallow | — | 282/512 (55.08%) | 337/512 (65.82%) |
| soybean / fallow → soybean / fallow → green gram / fallow | 291/512 (56.84%) | 309/512 (60.35%) | 319/512 (62.30%) |
| common bean / fallow → green gram / fallow → cowpea / fallow | — | 264/512 (51.56%) | 314/512 (61.33%) |
| common bean / fallow → cowpea / fallow → green gram / fallow | — | 264/512 (51.56%) | 314/512 (61.33%) |
| soybean / fallow → green gram / fallow → green gram / fallow | 267/512 (52.15%) | 291/512 (56.84%) | 308/512 (60.16%) |
| common bean / fallow → soybean / fallow → soybean / fallow | 278/512 (54.30%) | 301/512 (58.79%) | 307/512 (59.96%) |
| common bean / fallow → common bean / fallow → common bean / fallow | — | — | 305/512 (59.57%) |
| soybean / fallow → soybean / fallow → cowpea / fallow | 271/512 (52.93%) | 291/512 (56.84%) | 304/512 (59.38%) |
| cowpea / fallow → cowpea / fallow → cowpea / fallow | — | — | 304/512 (59.38%) |
| green gram / fallow → green gram / fallow → pearl millet / fallow | — | 257/512 (50.20%) | 295/512 (57.62%) |
| common bean / fallow → common bean / fallow → soybean / fallow | — | 261/512 (50.98%) | 286/512 (55.86%) |
| common bean / fallow → common bean / fallow → cowpea / fallow | — | — | 284/512 (55.47%) |
| common bean / fallow → cowpea / fallow → cowpea / fallow | — | — | 284/512 (55.47%) |
| soybean / fallow → soybean / fallow → soybean / sunflower | — | 258/512 (50.39%) | 283/512 (55.27%) |
| common bean / fallow → soybean / fallow → green gram / fallow | — | 265/512 (51.76%) | 280/512 (54.69%) |
| common bean / fallow → green gram / fallow → soybean / fallow | — | 265/512 (51.76%) | 280/512 (54.69%) |
| soybean / fallow → cowpea / fallow → cowpea / fallow | — | — | 280/512 (54.69%) |
| soybean / fallow → green gram / fallow → cowpea / fallow | — | 258/512 (50.39%) | 278/512 (54.30%) |
| soybean / fallow → cowpea / fallow → green gram / fallow | — | 258/512 (50.39%) | 278/512 (54.30%) |
| maize / fallow → soybean / fallow → soybean / fallow | — | — | 275/512 (53.71%) |
| soybean / fallow → soybean / fallow → sunflower / fallow | — | — | 273/512 (53.32%) |
| paddy / fallow → soybean / fallow → soybean / fallow | — | — | 269/512 (52.54%) |
| soybean / fallow → soybean / fallow → soybean / paddy | — | — | 269/512 (52.54%) |
| green gram / fallow → pearl millet / fallow → pearl millet / fallow | — | — | 268/512 (52.34%) |
| pigeonpea / fallow → pigeonpea / fallow → pigeonpea / fallow | — | — | 267/512 (52.15%) |
| green gram / fallow → pearl millet / fallow → cowpea / fallow | — | — | 266/512 (51.95%) |
| maize / fallow → green gram / fallow → green gram / fallow | — | — | 265/512 (51.76%) |
| soybean / fallow → soybean / fallow → soybean / maize | — | — | 265/512 (51.76%) |
| green gram / fallow → cowpea / fallow → pearl millet / fallow | — | — | 265/512 (51.76%) |
| paddy / fallow → green gram / fallow → green gram / fallow | — | — | 264/512 (51.56%) |
| green gram / fallow → green gram / fallow → green gram / sunflower | — | — | 264/512 (51.56%) |
| soybean / fallow → soybean / fallow → pearl millet / fallow | — | 256/512 (50.00%) | 262/512 (51.17%) |
| common bean / fallow → soybean / fallow → cowpea / fallow | — | — | 260/512 (50.78%) |
| common bean / fallow → cowpea / fallow → soybean / fallow | — | — | 260/512 (50.78%) |
| soybean / fallow → soybean / fallow → green gram / sunflower | — | — | 260/512 (50.78%) |
| soybean / fallow → soybean / sunflower → green gram / fallow | — | — | 260/512 (50.78%) |
| soybean / fallow → green gram / fallow → soybean / sunflower | — | — | 260/512 (50.78%) |
| common bean / fallow → green gram / fallow → pearl millet / fallow | — | — | 258/512 (50.39%) |
| common bean / fallow → pearl millet / fallow → green gram / fallow | — | — | 258/512 (50.39%) |
| green gram / fallow → green gram / fallow → sunflower / fallow | — | — | 258/512 (50.39%) |

### Makueni North Candidate

#### Water Saver

| Canonical rotation | Top 0.5% | Top 1% | Top 2% |
| --- | ---: | ---: | ---: |
| green gram / fallow → green gram / fallow → green gram / fallow | — | 274/512 (53.52%) | 318/512 (62.11%) |
| fallow / green gram → fallow / green gram → fallow / green gram | 262/512 (51.17%) | 284/512 (55.47%) | 307/512 (59.96%) |
| common bean / fallow → green gram / fallow → green gram / fallow | — | — | 277/512 (54.10%) |
| green gram / fallow → green gram / fallow → cowpea / fallow | — | — | 277/512 (54.10%) |
| common bean / fallow → common bean / fallow → green gram / fallow | — | — | 270/512 (52.73%) |
| fallow / green gram → fallow / green gram → fallow / cowpea | — | — | 267/512 (52.15%) |
| cowpea / fallow → cowpea / fallow → cowpea / fallow | — | — | 267/512 (52.15%) |
| common bean / fallow → common bean / fallow → common bean / fallow | — | — | 264/512 (51.56%) |
| fallow / cowpea → fallow / cowpea → fallow / cowpea | — | — | 263/512 (51.37%) |
| common bean / fallow → green gram / fallow → cowpea / fallow | — | — | 258/512 (50.39%) |
| green gram / fallow → cowpea / fallow → cowpea / fallow | — | — | 258/512 (50.39%) |
| fallow / green gram → fallow / cowpea → fallow / cowpea | — | — | 256/512 (50.00%) |

#### Soil Builder

| Canonical rotation | Top 0.5% | Top 1% | Top 2% |
| --- | ---: | ---: | ---: |
| green gram / fallow → green gram / fallow → green gram / fallow | — | — | 271/512 (52.93%) |

#### Income

| Canonical rotation | Top 0.5% | Top 1% | Top 2% |
| --- | ---: | ---: | ---: |
| maize / common bean → maize / common bean → maize / common bean | 258/512 (50.39%) | 287/512 (56.05%) | 313/512 (61.13%) |

**Balanced.** All three sets were empty.

## Interpretation and reproduction

Repeated use of the same model and assumptions can raise observed concentration. Ranking consistency within the model leaves field performance unresolved.

Regenerate this page from the saved P47 results with `python -m src.rank_concentration_report`.
