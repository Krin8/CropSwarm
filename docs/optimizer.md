# Ant colony search and exact verification

All three farms use a three-year horizon. Exact enumeration prunes identical consecutive crops, including the repeating-cycle boundary. **Whole-year cyclic shifts are one rotation**: the lexicographically smallest year shift is retained. This reduces the raw feasible counts from 504 to **168** in Kansas, 633,998 to **211,394** in Telangana, and 50,658 to **16,914** in Makueni. A one-season-slot shift is *not* equivalent at two-season farms because it changes the climate window. The scoring engine's six metric definitions are unchanged. Ant colony searches use the same feasible layers, canonicalize winning sequences, and choose the lexicographically first canonical sequence when weighted scores are exactly equal.

Displayed alternatives use the best-of-five swarm result when its six-score vector differs from every already selected strategy, including the baseline, by more than **0.05 on at least one normalized metric**. Otherwise exact enumeration supplies the highest-scoring canonical alternative that clears that threshold. The `0.05` threshold is a design choice, not empirical. All three farms retain four distinct alternatives; none is padded with a near-duplicate. If fewer than four clear the threshold under edited inputs, the app displays fewer and says why. See [distinctness settings](../config/tie_diagnosis.json).

For each farm and preset, 30 trials paired a first run with the best of five independent ACO runs. Trial `i` uses seeds `i + 30 × j` for `j = 0–4`. Each run starts with fresh pheromone state. This retains single-run seeds 0–29 and uses 150 unique seeds per farm and preset. The hit tolerance is 1e-10 on the normalized weighted score. Seed schedule, tolerance and ACO parameters are assumptions, validate locally. See `config/optimizer.json`.

The gap is the exact weighted score minus the ACO score. All trials completed. Best gap was zero to the displayed precision in every row for both modes. Mean and worst gaps are shown below. Raw trial seeds and scores are in the processed strategy files.

The [P16d change log](p16d_changes.md) compares these canonical results with the former raw-rotation results and records the effect on the P16 maps under weather shifts and displayed uncertainty.

| Farm | Feasible rotations | Preset | Single exact hits | Single mean / worst gap | Best of 5 exact hits | Best of 5 mean / worst gap |
|---|---:|---|---:|---:|---:|---:|
| kenya_makueni_north | 16,914 | water_saver | 22/30 (73.3%) | 0.001696 / 0.010896 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| kenya_makueni_north | 16,914 | soil_builder | 26/30 (86.7%) | 0.000268 / 0.002444 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| kenya_makueni_north | 16,914 | income | 30/30 (100.0%) | 0.000000 / 0.000000 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| kenya_makueni_north | 16,914 | balanced | 21/30 (70.0%) | 0.001441 / 0.010833 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| telangana_a | 211,394 | water_saver | 28/30 (93.3%) | 0.000548 / 0.008222 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| telangana_a | 211,394 | soil_builder | 28/30 (93.3%) | 0.000286 / 0.004286 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| telangana_a | 211,394 | income | 23/30 (76.7%) | 0.000711 / 0.015530 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| telangana_a | 211,394 | balanced | 29/30 (96.7%) | 0.000270 / 0.008115 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| us_high_plains_b | 168 | water_saver | 30/30 (100.0%) | 0.000000 / 0.000000 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| us_high_plains_b | 168 | soil_builder | 30/30 (100.0%) | 0.000000 / 0.000000 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| us_high_plains_b | 168 | income | 30/30 (100.0%) | 0.000000 / 0.000000 | 30/30 (100.0%) | 0.000000 / 0.000000 |
| us_high_plains_b | 168 | balanced | 30/30 (100.0%) | 0.000000 / 0.000000 | 30/30 (100.0%) | 0.000000 / 0.000000 |
