# Ant colony search and exact verification

All three farms use a three-year horizon. Exact enumeration prunes identical consecutive crops, including the repeating-cycle boundary. Ant colony searches use the same feasible layers. A distinct best-of-five winner is used when available. Exact enumeration provides a distinct fallback if the swarm winners would duplicate an existing strategy.

For each farm and preset, 30 trials paired a first run with the best of five independent ACO runs. Trial `i` uses seeds `i + 30 × j` for `j = 0–4`. Each run starts with fresh pheromone state. This retains single-run seeds 0–29 and uses 150 unique seeds per farm and preset. The hit tolerance is 1e-10 on the normalized weighted score. Seed schedule, tolerance and ACO parameters are assumptions, validate locally. See `config/optimizer.json`.

The gap is the exact weighted score minus the ACO score. All trials completed. Best gap was zero to the displayed precision in every row for both modes. Mean and worst gaps are shown below. Raw trial seeds and scores are in the processed strategy files.

| Farm | Feasible rotations | Preset | Single exact hits | Single mean / worst gap | Best of 5 exact hits | Best of 5 mean / worst gap |
|---|---:|---|---:|---:|---:|---:|
| kenya_makueni_north | 50,658 | water_saver | 21/30 (70.0%) | 0.001713 / 0.005711 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| kenya_makueni_north | 50,658 | soil_builder | 26/30 (86.7%) | 0.000160 / 0.002444 | 29/30 (96.7%) | 0.000026 / 0.000785 |
| kenya_makueni_north | 50,658 | income | 29/30 (96.7%) | 0.000034 / 0.001022 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| kenya_makueni_north | 50,658 | balanced | 21/30 (70.0%) | 0.001441 / 0.010833 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| telangana_a | 633,998 | water_saver | 28/30 (93.3%) | 0.000548 / 0.008222 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| telangana_a | 633,998 | soil_builder | 28/30 (93.3%) | 0.000286 / 0.004286 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| telangana_a | 633,998 | income | 23/30 (76.7%) | 0.000711 / 0.015530 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| telangana_a | 633,998 | balanced | 29/30 (96.7%) | 0.000270 / 0.008115 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| us_high_plains_b | 504 | water_saver | 30/30 (100.0%) | 0.000000 / 0.000000 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| us_high_plains_b | 504 | soil_builder | 30/30 (100.0%) | 0.000000 / 0.000000 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| us_high_plains_b | 504 | income | 30/30 (100.0%) | 0.000000 / 0.000000 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| us_high_plains_b | 504 | balanced | 30/30 (100.0%) | 0.000000 / 0.000000 | 30/30 (100.0%) | 0.000000 / 0.000000 |
