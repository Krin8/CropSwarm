# P9 exact verification

All farm search spaces stayed below the configured threshold of 5 million feasible rotations. Each uses three years. Exact enumeration prunes consecutive identical crops and enforces the repeating-cycle boundary. Ant colony search uses the same allowed crop layers. For each preset the best distinct swarm result is used when available. Exact selection supplies another distinct candidate when all swarm winners duplicate an existing strategy.

The parameters in `config/optimizer.json` and the absolute optimum comparison tolerance of 1e-10 are assumptions, validate locally. Each row compares 30 seeded searches (0–29) with exact enumeration. The gap is in normalized weighted score units.

| Farm | Feasible rotations | Preset | Exact hits | Best gap | Worst gap | Exact seconds | Swarm seconds total |
|---|---:|---|---:|---:|---:|---:|---:|
| kenya_makueni_north | 50,658 | water_saver | 21/30 | 0.00000 | 0.00571 | 0.014 | 0.178 |
| kenya_makueni_north | 50,658 | soil_builder | 26/30 | 0.00000 | 0.00244 | 0.014 | 0.179 |
| kenya_makueni_north | 50,658 | income | 29/30 | 0.00000 | 0.00102 | 0.014 | 0.179 |
| kenya_makueni_north | 50,658 | balanced | 21/30 | 0.00000 | 0.01083 | 0.014 | 0.179 |
| telangana_a | 633,998 | water_saver | 28/30 | 0.00000 | 0.00822 | 0.176 | 0.184 |
| telangana_a | 633,998 | soil_builder | 28/30 | 0.00000 | 0.00429 | 0.176 | 0.182 |
| telangana_a | 633,998 | income | 23/30 | 0.00000 | 0.01553 | 0.176 | 0.182 |
| telangana_a | 633,998 | balanced | 29/30 | 0.00000 | 0.00811 | 0.176 | 0.180 |
| us_high_plains_b | 504 | water_saver | 30/30 | 0.00000 | 0.00000 | 0.000 | 0.115 |
| us_high_plains_b | 504 | soil_builder | 30/30 | 0.00000 | 0.00000 | 0.000 | 0.116 |
| us_high_plains_b | 504 | income | 30/30 | 0.00000 | 0.00000 | 0.000 | 0.115 |
| us_high_plains_b | 504 | balanced | 30/30 | 0.00000 | 0.00000 | 0.000 | 0.115 |

Timings are local observations from the cached verification run. Swarm search reached the optimum at least once for every preset and farm. The largest worst-run gap was below 0.016, so the project kept ACO.
