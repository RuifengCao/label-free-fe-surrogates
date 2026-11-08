# G-F1 exploratory runs: results

Exploratory, after the verdict and not pre-registered (`EXPLORE_PLAN.md`). Written by `python probes/f1_explore/explore.py tables`.

## Cases

| Case | Levels | All converged, KKT ok | Last control | Last Theta_D (rad) | Last M (kNm) | s |
|---|---|---|---|---|---|---|
| E1_B-13_frictionless_hencky_nominal_medium | 7 | True | 0.006 | 0.00358 | 111.7 | 3292.2 |
| E1a_B-13_frictionless_hencky_nominal_coarse | 7 | True | 0.006 | 0.00358 | 111.7 | 655.8 |
| E2_B-13_frictionless_hencky_uniform-100_coarse | 12 | True | 0.006 | 0.00360 | 110.7 | 546.6 |
| E2_B-13_frictionless_hencky_uniform-mean_coarse | 12 | True | 0.006 | 0.00359 | 111.2 | 529.5 |
| E2_B-13_no-slip_hencky_uniform-100_coarse | 8 | True | 0.004 | 0.00159 | 118.6 | 280.0 |
| E2_B-13_no-slip_hencky_uniform-mean_coarse | 7 | True | 0.0035 | 0.00136 | 105.4 | 244.6 |
| E3_B-13_frictionless_hencky_nominal_coarse_ep-bolts | 15 | True | 0.015 | 0.01115 | 163.0 | 1267.5 |
| E3_B-13_no-slip_hencky_nominal_coarse_ep-bolts | 17 | True | 0.017 | 0.01063 | 278.7 | 1130.8 |
| E3_B-19_frictionless_hencky_nominal_coarse_ep-bolts | 17 | True | 0.017 | 0.01071 | 273.8 | 1158.2 |
| E3_B-19_no-slip_hencky_nominal_coarse_ep-bolts | 21 | True | 0.021 | 0.01093 | 385.2 | 1195.4 |

## E1. The mesh and C3

E1a check: 6 common levels, largest relative difference 2.03e-12; passed.

| | Coarse (gate) | Medium | Medium / coarse |
|---|---|---|---|
| C3 (kN) | 49.59 | 50.97 (ok) | 1.0278 |
| C1 (kNm) | 41.68 | 41.55 (ok) | 0.9969 |
| Bolt 1 at 25 kNm (kN) | 126.62 | 126.96 | |
| Bolt 1 at 100 kNm (kN) | 176.21 | 177.93 | |

Plastic points (plate, tube, weld, bolts) at each medium level: 0.001: [4, 0, 0, 0]; 0.0015: [17, 0, 0, 0]; 0.002: [54, 0, 0, 0]; 0.0025: [116, 0, 0, 0]; 0.005: [1860, 320, 259, 0]; 0.0055: [2562, 476, 312, 0]; 0.006: [3342, 616, 398, 0].

Elastic mesh flag of the gate for this quantity: 1.0177.

**Reading by the plan's rule** (test less tolerance 52.09 kN): the medium C3 lies within 1.5 kN of the coarse value: the mesh is not the main cause.

## E2. One preload value in every bolt

| Bound | Preload | C1 (kNm) | C3 (kN) | M at 0.0005 rad (kNm) |
|---|---|---|---|---|
| frictionless | nominal 125 kN (gate) | 41.68 | 49.59 | 22.55 |
| frictionless | measured (gate) | 41.01 | 57.61 | 22.18 |
| frictionless | uniform-mean (111.46 kN) | 41.11 | 56.42 | 22.25 |
| frictionless | uniform-100 (100.00 kN) | 40.56 | 62.20 | 21.99 |
| no-slip | nominal 125 kN (gate) | 82.47 | 34.79 | 45.31 |
| no-slip | measured (gate) | 80.90 | 40.68 | 44.48 |
| no-slip | uniform-mean (111.46 kN) | 81.16 | 39.66 | 44.60 |
| no-slip | uniform-100 (100.00 kN) | 79.92 | 44.37 | 43.96 |

**Reading (i)**: not both within 1 kN and 1 kNm: the unevenness matters (see the table for which quantity and bound).

**Reading (ii)**: P* = 120.0 kN (edge 52.09 kN); the no-slip C3 stays the lower value.

## E3. Towards the resistance

Check against the gate's records (dry run for B-19): B-13 frictionless: 5 common levels below bolt yield, largest relative difference 3.15e-12; B-13 no-slip: 3 common levels below bolt yield, largest relative difference 6.59e-12; B-19 frictionless: 4 common levels below bolt yield, largest relative difference 1.35e-12; B-19 no-slip: 4 common levels below bolt yield, largest relative difference 2.66e-12.

### B-13

| Theta_D (rad) | Test (kNm) | Author FE (3) | Frictionless | r | No-slip | r |
|---|---|---|---|---|---|---|
| 0.002 | 96.2 | 90.5 (0.94) | 74.5 | 0.77 | 143.7 | 1.49 |
| 0.003 | 113.8 | 111.7 (0.98) | 100.3 | 0.88 | 184.5 | 1.62 |
| 0.005 | 137.7 | 133.0 (0.97) | 129.3 | 0.94 | 229.0 | 1.66 |
| 0.0075 | 155.3 | 148.8 (0.96) | 147.5 | 0.95 | 257.8 | 1.66 |
| 0.01 | 166.8 | 164.0 (0.98) | 158.9 | 0.95 | 275.2 | 1.65 |

| M (kNm) | Test bolt 1 (upper dotted, kN) | Frictionless | No-slip |
|---|---|---|---|
| 100 | 162.3 | 174.7 | 160.8 |
| 125 | 180.5 | 175.4 | 174.9 |
| 150 | not reached | 176.4 | 175.5 |
| 175 | not reached | not reached | 176.4 |

frictionless: first level with a bolt above 174.7 kN: control 0.006, M 111.4 kNm, Theta_D 0.00358 rad; plastic points at the last level [4686, 1541, 889, 3]; no yielded bolt's force fell along the path.

no-slip: first level with a bolt above 174.7 kN: control 0.004, M 119.9 kNm, Theta_D 0.00156 rad; plastic points at the last level [5040, 3658, 1027, 4]; no yielded bolt's force fell along the path.

### B-19

| Theta_D (rad) | Test (kNm) | Author FE (3) | Frictionless | r | No-slip | r |
|---|---|---|---|---|---|---|
| 0.002 | 173.6 | 177.7 (1.02) | 136.4 | 0.79 | 217.7 | 1.25 |
| 0.003 | 203.2 | 210.2 (1.03) | 176.4 | 0.87 | 264.6 | 1.30 |
| 0.005 | 239.2 | 264.6 (1.11) | 220.9 | 0.92 | 326.8 | 1.37 |
| 0.0075 | 264.1 | 287.3 (1.09) | 251.8 | 0.95 | 362.5 | 1.37 |
| 0.01 | 277.9 | 295.1 (1.06) | 269.9 | 0.97 | 380.8 | 1.37 |

| M (kNm) | Test bolt 1 (upper dotted, kN) | Frictionless | No-slip |
|---|---|---|---|
| 100 | 139.4 | 160.2 | 143.9 |
| 125 | 148.2 | 173.5 | 156.6 |
| 150 | 162.3 | 175.4 | 171.4 |
| 175 | 177.3 | 176.3 | 174.6 |

frictionless: first level with a bolt above 174.7 kN: control 0.005, M 141.1 kNm, Theta_D 0.00209 rad; plastic points at the last level [4296, 3301, 970, 4]; no yielded bolt's force fell along the path.

no-slip: first level with a bolt above 174.7 kN: control 0.005, M 181.8 kNm, Theta_D 0.00137 rad; plastic points at the last level [3697, 5876, 1031, 4]; no yielded bolt's force fell along the path.

**Rule for the reference energy** (ratios at (0.005, 0.01) rad, both specimens; holds = all four within [0.90, 1.10]): frictionless holds, no-slip does not hold. Outcome: frictionless holds and no-slip does not: train both bounds (envelope). The rule informs the owner's choice; it does not make it.
