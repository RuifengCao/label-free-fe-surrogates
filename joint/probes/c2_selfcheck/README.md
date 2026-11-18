# Exploratory readings of gate G-C2.2's records: plastic depth and self-check quantities

17 and 18 November 2026, after the verdict of G-C2.2. **Nothing here is a gate, nothing was pre-specified, and no criterion of G-C2.2 changes.** The readings use G-C2.2's public records and train nothing. They are kept because gate G-C2.3 (`docs/PRESPEC_G-C2.3.md`) was designed after them and must say what had been seen.

All errors are the judged distance $\lvert F/F^*(e) - 1\rvert$ of gate G-C2.2, in the condensed reading unless stated; some scripts call that reading "refined". The two samples are the 64 fresh held-out members of G-C2.2 ("eval") and the 64 held-out members of G-C2.1 ("former"), 448 (member, level) pairs each, predicted by the three networks of G-C2.2 (seeds 5, 6, 7).

## Run

    python3 conditions.py JOINT
    python3 plastic_index.py JOINT RETURN
    python3 plastic_index2.py JOINT RETURN
    python3 other_metrics.py JOINT RETURN
    python3 conditions_numbers.py JOINT conditions_index.csv
    python3 selfcheck_indicators.py JOINT RETURN [OUT.csv]
    python3 spread_details.py JOINT RETURN
    python3 -I gate_code_on_seen_samples.py RETURN INST

`JOINT` is this `joint` folder (the scripts read `records/c22/return/verdict.json` and `manifest.json`). `RETURN` is a folder with `labels/<member>.npz`, the reference solutions of G-C2.2's deposit (its address is in the main README of `joint/`); they are used for the secant stiffness of the reference curve and to rebuild the predicted points from the recorded relative errors. `conditions_index.csv` holds the secant ratio and the number of plastic Gauss points of each pair of the fresh sample, so that `conditions_numbers.py` runs without the deposit. The outputs are in `records/`. The scripts are working scripts, kept as they were run; only a file name, the usage lines and the paths they take changed. The two `.csv` files are kept with LF line ends; the scripts write them with CRLF.

## 17 November: where the error is large

The secant ratio of a pair is the secant stiffness $F/e$ of the reference solution at that level divided by its value at the first level. Ranges are over the three runs.

| Pairs of the fresh sample | Number | Median | 90th percentile | Largest | Above 10% |
|---|---|---|---|---|---|
| no plastic Gauss point in the reference solution | 126 | 0.43 to 0.47% | 1.0 to 1.1% | 2.3 to 3.4% | 0 |
| secant ratio at least 1/8 | 331 | 0.58 to 0.62% | 2.2 to 2.4% | 7.1 to 7.7% | 0 |
| secant ratio below 1/8 | 117 | 2.0% | 6.5 to 7.1% | 50 to 69% | 6, 5, 6 |

- The pairs above 10% are in five members, all with a yield stress below 300 MPa; in each of them the predicted force is above the reference force.
- Without the condensation, the 90th percentile of the pairs below 1/8 is 35% to 41%.
- The same split on the first sample gives the same picture (`records/plastic_index2.txt`).
- The bins are halvings of the secant ratio, chosen before the split was looked at; the reading itself was made after the verdict.

## 18 November: quantities that need no reference solution

| | Quantity | Needs |
|---|---|---|
| A | secant ratio of the predicted curve | one run |
| B | mismatch of the two force readings of one field (spring and stresses) | one run |
| C | change of the force made by the condensation | one run |
| D | spread of the spring force over the three runs, (max - min) / median | three runs |
| O | secant ratio of the reference curve, for comparison | the reference solution |

Compared without tuning: by the area under the curve as a score for "error above 5%" (and 10%), and by the largest error left outside the quarter of the pairs with the highest score (`records/selfcheck_indicators.txt`).

- D ranks best on both samples: area 0.956 to 0.972 (first sample) and 0.944 to 0.956 (second) for errors above 5%.
- With the upper quartile of D on the first sample as a threshold (0.004504), carried unchanged to the second: 118 of 448 pairs are flagged there; of the pairs not flagged none exceeds 5% in any run (largest 4.8 to 4.9%); every pair above 10% is flagged. On the first sample itself one reading not flagged exceeds 5% (5.09%).
- **No margin on the first sample**: one pair above 10% has a spread of 0.00476, the next 0.0230. At a threshold of 0.0050 three readings above 10% would not be flagged. On the second sample the smallest spread among pairs above 10% is 0.0242.
- D is not plastic depth: of the 118 pairs flagged on the second sample, 56 are among the 117 with a secant ratio below 1/8.
- With two runs the spread is weaker (largest error not flagged 7.0 to 9.0%). C, which needs one run, leaves 7.1 to 7.7% on the second sample and misses one pair of 13.4% on the first. A equals O in effect. B is the weakest.

## The gate's code on the two samples

`gate_code_on_seen_samples.py` was written with the code of G-C2.3, after the readings above. It gives the predictions of G-C2.2's three runs on the two samples to the gate's own function, `c23.evaluate.self_check`, with the force read from each predicted field as the gate reads it, and with the judged errors of G-C2.2's verdict record. It needs the label and prediction files of G-C2.2's deposit for `RETURN`, and it exports the 128 members again into `INST`. Its output (`records/gate_code_on_seen_samples.txt`) agrees with the readings above:

| Sample | Pairs flagged | Readings not flagged | of them above 5% | Pairs not flagged above 10% | S1 to S3 | R |
|---|---|---|---|---|---|---|
| first (G-C2.1's held-out members) | 113 of 448 | 1,005 | 1 (5.09%) | 0 | hold | holds (0.956, 0.972, 0.967) |
| second (G-C2.2's fresh members) | 118 of 448 | 990 | 0 (largest 4.92%) | 0 | hold | holds (0.956, 0.944, 0.952) |

The threshold was set on the first sample and chosen after both had been seen, so these two rows test the code, not the hypothesis.

## What these readings are not

- D was chosen among four quantities after both samples had been seen, and both samples were predicted by the same three networks. The threshold is therefore a hypothesis; G-C2.3 tests it on a third sample.
- One row of the second sample (its worst pair, one run) had been looked at before the script of 18 November was written.
- Everything is inside the family's ranges and against the reference model, not against tests.
