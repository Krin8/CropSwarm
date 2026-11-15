# P47 chance-adjusted rank concentration

**EXPLORATORY.** The empty P44 top-three sets motivated this wider rank check. A rotation enters a stable-top set if it ranks in the listed top fraction in at least 50% of the variant-by-draw cells. This describes the tested settings. The thresholds and rounding are design choices. Results are illustrative and need local validation. [Preregistration](p47_plan.md) · [P44](consensus_shortlist.md) · [Every member and its exact hit count](../data/processed/rank_concentration_p47.json)

Nonempty sets appeared in 5 of 12 at 0.5%, 5 of 12 at 1%, 7 of 12 at 2%. The largest observed share was 90.62%. In each of the 36 comparisons, every shuffled maximum was below the observed maximum (empirical p = 1/1,001).

## Search spaces and cells

| Farm | P44 variants | P22 draws | Cells per preset | Canonical union | Admitted rotations per cell | Top slot ranges at 0.5%, 1%, 2% |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| US High Plains B | 16 | 512 | 8,192 | 330 | 3–330 | 1–2, 1–4, 1–7 |
| Telangana A | 1 | 512 | 512 | 303,132 | 1,137–303,132 | 6–1,516, 12–3,032, 23–6,063 |
| Makueni North Candidate | 1 | 512 | 512 | 41,707 | 1–41,706 | 1–209, 1–418, 1–835 |

Percentile is 100 times (rank minus 1) divided by the number of admitted rotations. Ineligible rotations get zero hits and keep all cells in the denominator. The code selects only the ranks needed to reproduce P44's top-one and top-three counts and the three P47 cutoffs. The exact fraction uses the ceiling of the slot count, so different thresholds can occupy the same number of slots in small cells.

## Set size, largest share and shuffled reference

1,000 independent null replicates preserve the admitted rotation labels in each cell and shuffle their ordering. The maximum is taken over the full canonical union. The 95% range describes shuffled maxima. Plus-one upper-tail p-values include ties and are unadjusted. The joint p-value counts replicates meeting or exceeding both the observed set size and maximum share.

| Farm | Preset | Top fraction | Members | Largest share | Null mean members | Null mean largest share | Null largest share 95% range | p for largest | p for size | p for both |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| US High Plains B | Water Saver | 0.5% | 0 | 16.70% | 0.00 | 1.40% | 1.16% to 1.65% | 0.0010 | 1.0000 | 0.0010 |
| US High Plains B | Water Saver | 1% | 0 | 18.73% | 0.00 | 1.81% | 1.53% to 2.09% | 0.0010 | 1.0000 | 0.0010 |
| US High Plains B | Water Saver | 2% | 0 | 23.93% | 0.00 | 2.72% | 2.34% to 3.08% | 0.0010 | 1.0000 | 0.0010 |
| US High Plains B | Soil Builder | 0.5% | 0 | 22.14% | 0.00 | 1.40% | 1.16% to 1.65% | 0.0010 | 1.0000 | 0.0010 |
| US High Plains B | Soil Builder | 1% | 0 | 24.90% | 0.00 | 1.81% | 1.53% to 2.09% | 0.0010 | 1.0000 | 0.0010 |
| US High Plains B | Soil Builder | 2% | 0 | 31.91% | 0.00 | 2.72% | 2.34% to 3.08% | 0.0010 | 1.0000 | 0.0010 |
| US High Plains B | Income | 0.5% | 0 | 15.01% | 0.00 | 1.40% | 1.16% to 1.65% | 0.0010 | 1.0000 | 0.0010 |
| US High Plains B | Income | 1% | 0 | 18.38% | 0.00 | 1.81% | 1.53% to 2.09% | 0.0010 | 1.0000 | 0.0010 |
| US High Plains B | Income | 2% | 0 | 25.16% | 0.00 | 2.72% | 2.34% to 3.08% | 0.0010 | 1.0000 | 0.0010 |
| US High Plains B | Balanced | 0.5% | 0 | 15.82% | 0.00 | 1.40% | 1.16% to 1.65% | 0.0010 | 1.0000 | 0.0010 |
| US High Plains B | Balanced | 1% | 0 | 17.55% | 0.00 | 1.81% | 1.53% to 2.09% | 0.0010 | 1.0000 | 0.0010 |
| US High Plains B | Balanced | 2% | 0 | 22.55% | 0.00 | 2.72% | 2.34% to 3.08% | 0.0010 | 1.0000 | 0.0010 |
| Telangana A | Water Saver | 0.5% | 96 | 85.35% | 0.00 | 1.76% | 1.56% to 2.15% | 0.0010 | 0.0010 | 0.0010 |
| Telangana A | Water Saver | 1% | 126 | 89.84% | 0.00 | 2.49% | 2.34% to 2.93% | 0.0010 | 0.0010 | 0.0010 |
| Telangana A | Water Saver | 2% | 283 | 90.62% | 0.00 | 3.73% | 3.32% to 4.30% | 0.0010 | 0.0010 | 0.0010 |
| Telangana A | Soil Builder | 0.5% | 30 | 72.46% | 0.00 | 1.76% | 1.56% to 2.15% | 0.0010 | 0.0010 | 0.0010 |
| Telangana A | Soil Builder | 1% | 47 | 80.27% | 0.00 | 2.49% | 2.34% to 2.93% | 0.0010 | 0.0010 | 0.0010 |
| Telangana A | Soil Builder | 2% | 105 | 84.77% | 0.00 | 3.73% | 3.32% to 4.30% | 0.0010 | 0.0010 | 0.0010 |
| Telangana A | Income | 0.5% | 0 | 41.80% | 0.00 | 1.76% | 1.56% to 2.15% | 0.0010 | 1.0000 | 0.0010 |
| Telangana A | Income | 1% | 0 | 47.07% | 0.00 | 2.49% | 2.34% to 2.93% | 0.0010 | 1.0000 | 0.0010 |
| Telangana A | Income | 2% | 2 | 51.17% | 0.00 | 3.73% | 3.32% to 4.30% | 0.0010 | 0.0010 | 0.0010 |
| Telangana A | Balanced | 0.5% | 8 | 62.50% | 0.00 | 1.76% | 1.56% to 2.15% | 0.0010 | 0.0010 | 0.0010 |
| Telangana A | Balanced | 1% | 20 | 67.77% | 0.00 | 2.49% | 2.34% to 2.93% | 0.0010 | 0.0010 | 0.0010 |
| Telangana A | Balanced | 2% | 45 | 74.61% | 0.00 | 3.73% | 3.32% to 4.30% | 0.0010 | 0.0010 | 0.0010 |
| Makueni North Candidate | Water Saver | 0.5% | 1 | 51.17% | 0.00 | 2.18% | 1.56% to 3.12% | 0.0010 | 0.0010 | 0.0010 |
| Makueni North Candidate | Water Saver | 1% | 2 | 55.47% | 0.00 | 2.61% | 1.95% to 3.71% | 0.0010 | 0.0010 | 0.0010 |
| Makueni North Candidate | Water Saver | 2% | 12 | 62.11% | 0.00 | 3.53% | 2.73% to 4.69% | 0.0010 | 0.0010 | 0.0010 |
| Makueni North Candidate | Soil Builder | 0.5% | 0 | 40.62% | 0.00 | 2.18% | 1.56% to 3.12% | 0.0010 | 1.0000 | 0.0010 |
| Makueni North Candidate | Soil Builder | 1% | 0 | 46.29% | 0.00 | 2.61% | 1.95% to 3.71% | 0.0010 | 1.0000 | 0.0010 |
| Makueni North Candidate | Soil Builder | 2% | 1 | 52.93% | 0.00 | 3.53% | 2.73% to 4.69% | 0.0010 | 0.0010 | 0.0010 |
| Makueni North Candidate | Income | 0.5% | 1 | 50.39% | 0.00 | 2.18% | 1.56% to 3.12% | 0.0010 | 0.0010 | 0.0010 |
| Makueni North Candidate | Income | 1% | 1 | 56.05% | 0.00 | 2.61% | 1.95% to 3.71% | 0.0010 | 0.0010 | 0.0010 |
| Makueni North Candidate | Income | 2% | 1 | 61.13% | 0.00 | 3.53% | 2.73% to 4.69% | 0.0010 | 0.0010 | 0.0010 |
| Makueni North Candidate | Balanced | 0.5% | 0 | 31.84% | 0.00 | 2.18% | 1.56% to 3.12% | 0.0010 | 1.0000 | 0.0010 |
| Makueni North Candidate | Balanced | 1% | 0 | 34.57% | 0.00 | 2.61% | 1.95% to 3.71% | 0.0010 | 1.0000 | 0.0010 |
| Makueni North Candidate | Balanced | 2% | 0 | 41.21% | 0.00 | 3.53% | 2.73% to 4.69% | 0.0010 | 1.0000 | 0.0010 |

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

The saved output lists every canonical member with its cycle, hit count and share. The Validation panel displays the complete member list for the selected farm, preset and threshold.

## Interpretation and reproduction

This exploratory comparison measures repeated high ranks across the tested scoring settings and draws. The shuffled null keeps eligibility and removes dependence among cells. These results leave real-world rotation quality unresolved. The comparison treats variant-by-draw cells as independent only in the null. Repeated use of the same model and assumptions can raise observed concentration. Field performance requires local evidence.

Rebuild offline with `python -m src.rank_concentration`, then regenerate this page with `python -m src.rank_concentration_report`. The replay writes its own processed output.
