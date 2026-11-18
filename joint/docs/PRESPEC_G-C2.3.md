# Pre-specification of gate G-C2.3

Stamped 18 November 2026, 12:02 GMT. At that time no member drawn with seed 20261118 had been exported or solved, and no training of this gate had started.

## Questions

G-C2.2 passed: on 64 fresh T-stubs the label-free surrogate, read after the amplitude condensation, lay within 0.80% of the reference curve in the median and within 3.66% at the 90th percentile (`docs/G-C2.2_verdict.md`). G-C2.3 trains nothing new in the label-free arm. It asks two further questions on a third sample that nobody has seen: one of the same three networks, and one of the same network trained with reference solutions.

**Part 1, the self-check.** Can the surrogate tell, without any reference solution, where it is far from the reference model? After G-C2.2's verdict an exploratory reading of its records suggested one such quantity: the spread of the predicted force over the three training runs.

*Hypothesis.* With the threshold fixed below, the pairs that the spread does not flag hold no error above 10% and almost none above 5%, while at most 35% of the pairs are flagged.

**Part 2, the comparison at equal budget.** How close to the reference model is the same network when it is trained on reference solutions of the same 512 training members, with the same number of steps and the same training settings? G-C2.1 had a supervised arm, but with 64 labelled members and one eighth of the steps; no comparison at equal budget exists.

*No hypothesis is tested in part 2.* The gate fixes what is compared, and the words that the outcome allows.

**Unchanged from G-C2.2** (`docs/PRESPEC_G-C2.2.md` and `docs/PRESPEC_G-C2.1.md`, which this document does not repeat):
- the reference model, its theory, mesh and solver;
- the family of T-stubs and the 512 training members (seed 20261106);
- the loading through a spring, and the seven judged levels of the loading-device displacement, 0.5 to 8 mm;
- the judged quantity, the distance $\lvert F/F^*(e) - 1\rvert$ of a predicted point $(e, F)$ from the reference curve;
- the network, the label-free loss, the sampling, the learning rate, the schedule, the budget of 200 epochs, the stability recipe;
- the raw and the condensed reading; the condensed reading is the judged one;
- the three label-free networks themselves: the state files of G-C2.2's runs with seeds 5, 6 and 7.

**Changed**
- *Held-out members.* 64 fresh members, seed 20261118, are judged. G-C2.2's fresh members (seed 20261113) and the four tested members are reported. G-C2.1's held-out members are not evaluated again: every evaluated prediction costs an exact solve, and their readings with these networks are in G-C2.2's records.
- *Label-free arm.* Not trained. Each state file is read after its SHA-256 has been found equal to the pinned one, and the network predicts this gate's members.
- *Supervised arm.* New: see "Model and training".
- *Labels for training.* Every training member is labelled, at eight levels: 0.1, 0.75, 1.5, 2.5, 3.5, 5, 7 and 8 mm. These are the base level of the condensed reading, the six training levels of G-C2.1's supervised arm, and the largest judged level. A network is read at the base level and at the seven judged levels; all of these then lie within the labelled range, and every judged level but the largest lies between two labelled levels; in G-C2.1 that held for the judged levels from 1 to 6 mm. That is 4,096 reference solutions. The owner's message of 03:56 had agreed to seven levels, without 0.1 mm, on the author's recommendation, which was wrong: draft 0.1 said that no judged level lay beyond the labelled range, while the level 0.5 mm and the base level 0.1 mm of the judged reading lay below the lowest labelled level, 0.75 mm. The author found this after the owner's message, and the review found it independently. The owner agreed to the eight levels at 10:31 ("Authority").

## Authority

**The owner** wrote the following (messages translated from Chinese; the originals are kept in the correspondence record):
- 18 November 2026, 02:28: "Carry on with the research. What should be done next?"
- 18 November 2026, 03:03, after a list of four runs with a recommended order (a comparison with supervised training at equal budget; a timing; a registered check of the self-check on a third sample; the cost of a training step for the CHS surrogate): "As recommended. Start."
- 18 November 2026, 03:56: "All as recommended." This answered a note of 03:52 in which the author had put to the owner, with draft 0.1:
  - the recommendation to make one gate of the two registered runs, with one third sample for both parts and the seeds 5, 6 and 7 for the supervised runs;
  - six points with a recommendation for each but the last: the training labels at seven levels, with 8 mm; the stability recipe kept in the supervised arm; the threshold of 0.0045; the criteria S1 to S3 and R, the band and the words of part 2 as drafted; an independent review of the new code before the stamp; the nights on which the host is free;
  - two things to be done unless the owner objected: the seed 20261118 for the third sample; the timing and the CHS cost as probes outside the gate.
- 18 November 2026, 10:31: "As recommended. The laptop can be used for the checks before the stamp right now; the full run can start tonight before I go to bed." This answered two messages of the author, of 06:15 and of 10:09, which put to the owner: the eighth level of the training labels, 0.1 mm, with the error of the author's earlier recommendation and the recommendation to add it; and the question of when the host is free. A note of 09:57, which the message of 10:09 announced, also told the owner that the later drafts add 18 points to draft 0.1, summed them up in one sentence and offered them one by one; the owner did not ask for them.

**Chosen by the author, and not put to the owner point by point**: everything that drafts 0.2 to 0.5 add to draft 0.1 apart from the level 0.1 mm. The points are listed at the end of the review's record (`docs/reviews/review_report_G-C2.3_2026-11-18.md`). None of them changes the threshold, the criteria S1 to S3, the limit of R, the band, the seeds or the samples of draft 0.1.

**Changes.** Any change after the stamp is reported as a change after the stamp. No threshold, criterion, reading, level or seed changes once the first member of seed 20261118 has been exported.

## What was seen before the stamp

**G-C2.2**: its verdict and every metric of every pair of its fresh members, of G-C2.1's held-out members and of the tested members, for the three seeds and both readings.

**The reading of plastic depth, 17 November 2026** (exploratory; `probes/c2_selfcheck/README.md`). On G-C2.2's fresh members the error grew with plastic deformation; every error above 10% lay where the secant stiffness of the reference curve had fallen below one eighth of its initial value, in five members with a yield stress below 300 MPa.

**The reading of self-check quantities, 18 November 2026** (exploratory; same folder). Four quantities that need no reference solution were compared on G-C2.1's held-out members and on G-C2.2's fresh members, 448 pairs each, with the three networks of G-C2.2 in the condensed reading: the secant stiffness of the predicted curve; the mismatch of the two force readings of one field; the change of the force made by the condensation; the spread of the force over the three runs. None of them had been computed before the script was written, apart from one row.
- By the area under the curve as a score for "error above 5%", the spread ranked the errors best on both samples: 0.956 to 0.972 on the first and 0.944 to 0.956 on the second, over the three runs. Not every reading favours it: for errors above 10% on the first sample the change made by the condensation has the larger area in one run, and its rank correlation with the error is slightly higher on the second sample.
- The threshold is the upper quartile of the spread on the first sample, 0.004504, rounded to 0.0045. On the first sample it flags 113 of 448 pairs; of the 1,005 readings that are not flagged, one exceeds 5% (5.09%) and none 10%. On the second sample it flags 118 pairs; none of the 990 readings that are not flagged exceeds 5% (largest 4.92%).
- **The threshold has no margin on the first sample.** One pair there exceeds 10% with a spread of 0.00476; the next smallest spread among pairs above 10% is 0.0230. At a threshold of 0.0050 three readings above 10% would not be flagged. On the second sample the smallest spread among pairs above 10% is 0.0242.
- With two runs instead of three the spread is weaker: at its own upper quartile, the largest error not flagged on the second sample is 7.0% to 9.0%.
- The spread was chosen among the four after both samples had been seen. Both samples were predicted by the same three networks.

**G-C2.1's supervised arm**: 64 labelled members at six levels, 12,800 steps, three seeds, read raw; its metrics on G-C2.1's held-out members and on the tested members (`docs/G-C2.1_verdict.md`). On the tested member T1 with preload (`BJ_T1_preloaded`) its error against the reference curve was 1.4% to 18% over the seven levels (median of three seeds), against 0.2% to 1.7% for the label-free networks of G-C2.2 (0.2% to 2.8% read raw). Its errors were largest at the smallest judged level, 0.5 mm, which lay below its labelled range.

**Not seen**
- No member drawn with seed 20261118 has been exported or solved.
- No training member has been solved at the eight label levels. In G-C2.2's development 24 training members were solved at the seven judged levels (`probes/c2_dev/README.md`).
- No supervised run at this gate's size has been made. The supervised runs so far are G-C2.1's, with 64 labelled members and without the stability recipe, and the runs of the tests and of the host check on reduced configurations: a few members, a small network, a few epochs. On the host before the stamp, `probes/c2_timing/step_cost.py` made 45 supervised steps on eight training members to time them, against zero fields in place of reference solutions; nothing of them is kept.
- The other checks made on the host before the stamp read G-C2.2's own data: the state files' predictions of G-C2.2's members ("Identity of the label-free networks"), and a timing of the surrogate and of the reference solve on eight members of G-C2.2's fresh sample (`probes/c2_timing/time_curve.py`). The cost of the CHS energy was timed on one member of the CHS family (`probes/f2_cost/energy_cost.py`), which is outside this gate.
- Members drawn with seeds that were used before G-C2.1's stamp were solved at the eight label levels on the gate's mesh, to see that the reference model converges and the label checks hold from 0.1 mm. On a processor, with another linear solver than the host's: two members of seed 7 by the author (`probes/c23_precheck/records/pilot_labels_processor_seed7.json`) and twelve of seed 101 by the reviewer (the review's record, round 2); all converged. On the host, with its solver, on 18 November 2026: 32 members of seed 101 (`probes/c23_precheck/pilot_labels.py`); every level converged, with two iterations at 0.1 mm in each member and at most 25 at any level, and the label checks hold, the largest residual being 5.1e-11 against a limit of 1e-6. A member took 123 s in the median and 213 s at most (`records/c23/before_stamp/pilot_labels.json`).

**The code of this gate** was checked on its own, with nothing of this gate drawn:
- The gate's function for part 1 was given the predictions of G-C2.2's three runs on the two samples above, with the force read from the fields as the gate reads it (`probes/c2_selfcheck/gate_code_on_seen_samples.py`). It returned the numbers of the exploratory reading: 113 and 118 pairs flagged, one and no reading above 5% among those not flagged, S1 to S3 and R holding on both. This tests the code, not the hypothesis.
- The tests: `tests/test_c23.py` has 18 tests, and the whole suite of the package, 156 tests, passed on the stamped state.
- The host check (`c23/smoke.py`) passed on the host on 18 November 2026, from a copy of the code that is file for file the stamped code, on its reduced configuration with family seeds used before G-C2.1's stamp (`records/c23/before_stamp/smoke_report.json`). On the GPU, the interrupted and resumed supervised run equalled the uninterrupted one, and the evaluation with worker processes equalled the one without.
- The check of the state files' predictions on the host and the pilot of the training labels: see "Identity of the label-free networks" and "Not seen".
- The independent review, in three rounds (`docs/reviews/review_report_G-C2.3_2026-11-18.md`). Nothing that the reviewer found blocked the stamp. The changes that the author made after the third round were not seen by the reviewer; they are listed there, and none of them touches a line of the code that computes, judges or refuses.

## Expected outcome, stated before the run

**Part 1.** S3 is expected to hold (25% and 26% were flagged before). S2 is expected to hold (0.1% and 0% before, against a limit of 1%). S1 is uncertain: it held on both samples, on the first by a margin of one pair, and a fresh sample will hold about seven pairs above 10%; the author's estimate is about two chances in three that S1 holds. R is expected to hold.

**Part 2.** The author expects the supervised arm to be closer to the reference model in the median, because it is given 4,096 exact solutions of the family it is judged on. The 90th percentile is uncertain: the label-free arm's large errors lie far into the plastic range, where the supervised arm has labels.

## Configuration

**The configuration** is `c23/config.py`: G-C2.2's stamped configuration with the changes listed above and nothing else. Its canonical SHA-256 is `3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e`; G-C2.2's is `ef5376a4d6c3cc98d7888121439c8d959ee817d332958dd6b1141b25e78734bb`.

**The repository code** the runs import is pinned file by file, as in G-C2.1 and G-C2.2; the files and their hashes are the same.

**The gate's own code.** The files of `c22/`, `c2/` and `fejoint/` stamped for G-C2.2 are used unchanged. New: `c23/__init__.py`, which is empty, `c23/config.py`, `c23/data.py`, `c23/train.py`, `c23/evaluate.py`, `c23/__main__.py` and `c23/smoke.py`. Hashes: `docs/G-C2.3_code.sha256`, which lists all 35 files of the gate's code and the six repository files; the new files are in the table below. Every command of the gate but `write-config` refuses to run unless that file lies beside the code and holds the hash of every file as it is; before the stamp there is no such file, so that no command of the gate can draw the held-out sample from a draft. `generate`, `predict-label-free`, `train`, `evaluate` and `verdict` also refuse to run unless the configuration hash given to them is that of the code; the job files take it from this document. `label` and `check-labels` take none: the stamp file and the manifest of the generated data cover them. The commands write no bytecode, so that the tree they run from holds the sources only.

| File | SHA-256 |
|---|---|
| `c23/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `c23/__main__.py` | `f6636b5b4153fade230443af8ae0b24f9f372b946f81833f45bf847aa1943ced` |
| `c23/config.py` | `8b926322e1a495ec71e7d4706cfd4e28073fa914dc998dfa081f495808586a1c` |
| `c23/data.py` | `10ddd019b80dc19d7801f424f94940d7bbf8bcfc5dde7dd268011275af5942c1` |
| `c23/train.py` | `2e8095b20e5e770b13ab5ee60343ed1cf7abe63fe06b0e9a9f2149f33dae6f83` |
| `c23/evaluate.py` | `d526fb2754cd15b53c228b1707d533c1aa4a22fb79f6c4a5796684b36e36ce61` |
| `c23/smoke.py` | `dc8e5e657b11f8c30292d62bd00a50b953cc9f8b5e337aef24a4e3d0069aa65c` |

**The label-free state files** of G-C2.2's runs, with their SHA-256:

| File | SHA-256 |
|---|---|
| `label_free_s5/state.pt` | `5859ca7737e94b502660dddd082891a18f981b6df4228ff2a7c59d865ca7dcf5` |
| `label_free_s6/state.pt` | `adb9992ae19846afd56e9f75d9dfe533edcf5a47fbca9c6a210f18581032c0b1` |
| `label_free_s7/state.pt` | `80c56c73af04b4321f52a9acfd037a476837bfa6ec0cc8e55524dbf63988bc53` |

The values are those of the record that the owner's archive of the three files carries, written when the archive was made on 15 November 2026. The files are not in the repository. On 18 November 2026 the three files on the host had these hashes (`records/c23/before_stamp/repredict.json`). They are hashed again on the host before the first prediction, and the prediction command refuses a file with another hash.

**Host.** The laptop of G-C2.2, as its host check of 18 November 2026 recorded it: Windows 11, an NVIDIA GeForce RTX 4070 Laptop GPU with 8 GB, 32 logical processors, Python 3.12.16, torch 2.12.1 with CUDA 13.2, numpy 2.4.6 and scipy 1.18.1. The owner gave it to the checks before the stamp on the morning of 18 November 2026 and to the run from that night (message of 10:31).

## Data

**Family, levels, export and solver**: as in G-C2.2.

**Samples**

| Split | Members | Seed | Levels solved | Role |
|---|---|---|---|---|
| train | 512 | 20261106 | the eight levels of the training labels | labels of the supervised arm |
| third | 64 | 20261118 | the seven judged levels | judged |
| eval | 64 | 20261113 | the same | reported; identity check |
| tested | 4 | fixed | the same | reported |

**Labels**: exact solutions with G-C2.1's solver settings and label checks; 644 members. Every file is exported and solved again under this gate's configuration; nothing is copied from G-C2.2.

## Model and training

**Network**: as in G-C2.2.

**Label-free arm**: the three state files; no training.

**Supervised arm** (`supervised_512`): G-C2.2's run with one change. The loss of a step is G-C2.1's supervised loss, the mean squared error of the physical displacement over $(D + \delta)^2$, on 4 of the 8 labelled levels of the step's member, drawn without replacement. Everything else is G-C2.2's: the 512 training members in a fresh random order every epoch, one member a step, 200 epochs, 102,400 steps, AdamW with the recipe's $\beta_2$ of 0.99, the cap on the encoder's gradient, the clipping, the schedule, the precision, a checkpoint every epoch. Seeds 5, 6 and 7, as the label-free runs. The seed is set in the same way before the network is built, so that a supervised run starts from the initial weights of the label-free run of its seed; on a processor, in the reduced configuration, the two sets of weights were identical (`tests/test_c23.py`). The order of the members is the label-free run's in the first epoch only: the two losses draw differently from the random stream. Before a run starts or resumes, the training members' files are compared with the manifest and the ledger, and the run's history keeps the SHA-256 of their ledger entries.

**Predictions**: for every held-out and tested member at the seven levels, in both readings, for all six runs, by G-C2.2's code. The condensation needs no reference solution and is applied to both arms.

**Budget**: 307,200 supervised steps. The step time on the host, measured before the stamp over 40 steps on eight training members (`probes/c2_timing/step_cost.py`, `records/c23/before_stamp/step_cost.json`): 0.167 s for a supervised step and 0.671 s for a label-free step, in the median. At that rate a supervised run takes 4.7 hours. In G-C2.2's runs a label-free step took 0.44 to 0.50 s on the host; the measured times are estimates and no criterion. Labels: about 22 hours of processor time in all, of which about 18 for the training members: an hour to an hour and a half with 16 worker processes. Evaluation: 5,544 exact solves for each arm, as many as in G-C2.2, whose evaluation took two hours with 16 worker processes.

## Identity of the label-free networks

The judged values of each label-free run on G-C2.2's fresh members (the per-seed median and 90th percentile, both readings) are computed again and must equal those of G-C2.2's verdict within 0.0001. If they do not, the verdict is INVALID and neither part is evaluated. The same holds when one of these values cannot be computed: a label-free run without finite predictions, or a member of G-C2.2's fresh sample whose metrics the reference code cannot compute in a label-free run. A run that ends without finite predictions is not predicted again: that end is final, as a supervised run's non-finite stop is.

This check can be made only after the third sample has been drawn, labelled and evaluated. Before the stamp, and so before the draw, the same question is asked on G-C2.2's own data: on the host, each state file predicts G-C2.2's held-out and tested members again, and the fields are compared with the prediction files that G-C2.2's runs left (`probes/c23_precheck/repredict.py`). Result, 18 November 2026: for each of the three state files the fields of all 132 members were equal to G-C2.2's files to the last bit, in the raw reading, in the condensed reading and at the base level, and the amplitudes were equal (`records/c23/before_stamp/repredict.json`). The comparison of the fields does not cover the exports and the reference solutions of these members, which this gate makes again. The host check covers that part on its reduced configuration: it exports and solves the members of its stand-in for G-C2.2's fresh sample twice, in two data folders, and reports the largest difference between the judged values of the two evaluations. Result on the host, 18 November 2026: the largest difference was 0.0 (`records/c23/before_stamp/smoke_report.json`, `evaluate.identity`).

## Part 1: criteria (label-free arm, the 448 pairs of the third sample, condensed reading)

For each pair, $F_s = 4 k_s (D - e_s)$ is the spring force of run $s$, read from its field alone. The spread is $(\max_s F_s - \min_s F_s)/\lvert\operatorname{median}_s F_s\rvert$. A pair is flagged when its spread is at least 0.0045, and when the median force is zero.

**S1.** No pair that is not flagged has an error above 0.10 in any run.

**S2.** Of the readings (pair, run) of the pairs that are not flagged, at most 0.01 have an error above 0.05.

**S3.** At most 0.35 of the pairs are flagged.

**Verdict of part 1.** PASS if and only if S1, S2 and S3 hold.

**R, the ranking.** In each run that has a pair above 0.05 and a pair at or below 0.05, the probability that a pair above 0.05 has a larger spread than a pair at or below 0.05, ties counting half, is at least 0.90. R is reported beside the verdict, as HOLDS or DOES NOT HOLD, or as NOT EVALUABLE if no run has pairs on both sides of 0.05.

**A member without metrics.** If the reference code cannot compute the metrics of a member of the third sample in a label-free run, part 1 is FAIL and R is NOT EVALUABLE.

## Part 2: comparison (both arms, the same pairs, condensed reading)

For each arm: the median over its three seeds of the per-seed median error, and of the per-seed 90th percentile. The two ratios are those of the supervised arm over the label-free arm.

**Wording.** "Comparable" if and only if both ratios lie between 2/3 and 3/2, the ends included. "Supervised closer" if both ratios are below 1 and at least one is below 2/3. "Label-free closer" if both are above 1 and at least one is above 3/2. "Mixed" otherwise. If a ratio is not a number, because a statistic is infinite in both arms, the wording is NOT COMPARABLE.

**Seeds without numbers.** A supervised seed whose run stopped on a non-finite loss or on non-finite predictions enters both medians over seeds with infinite errors. So does a seed of either arm in which a member of the third sample has no metrics.

**What each arm needed** is reported with the wording: the reference solutions and their processor time, and the training time of each run. For the label-free runs the training times and the cap's actions are those of G-C2.2's records (`records/c22/`); nothing of them is measured again here.

## Reported, not judged

- Both readings of both arms on every set, with the values that C1 and C2 of G-C2.2 would take.
- The median error of both arms at each of the seven levels, in both readings.
- The two ratios of the supervised arm read raw over the label-free arm in the condensed reading.
- In each run, the pairs above 5% and above 10%, and how many of them are flagged.
- The spread, the flags and S1 to S3 on the other sets, in the raw reading, and for the three supervised runs.
- Every metric of G-C2.1 for every pair.
- The cap's actions in the supervised runs.

## Interpretation, fixed in advance

**Part 1, PASS.** On a third sample, three training runs that agreed within 0.45% in force held no error above 10%, and at most one reading in a hundred above 5%. Any wording says that the check needs three training runs, that the threshold was set on T-stubs of this family, and gives the share of pairs flagged and, for each run, the number of pairs above 5% and above 10% and how many of them were flagged. If no pair exceeds 10% in any run, the wording says that S1 was not put to the test. If R does not hold, the wording says that the threshold separated the large errors on this sample and that the spread did not rank the errors. If R is NOT EVALUABLE, the wording says that no run had pairs on both sides of 5% and that the ranking was not put to the test.

**Part 1, FAIL.** The fixed threshold did not separate the large errors on a third sample. The failing criterion and the pairs concerned are listed. If R holds, the wording is that the spread ranks the errors and that no fixed threshold is claimed. If part 1 is FAIL because a member of the third sample has no metrics in a label-free run, the wording says so: the reference code could not evaluate a prediction of a label-free network, the criteria were not computed, and the member and the error are given.

**Part 2.** The wording is the one the ratios allow, with both statistics of both arms, the medians at each level for every arm whose three runs all have numbers, and what each arm needed. The condensed reading was developed on the label-free networks, so the supervised arm's raw reading is given beside its condensed reading: the two ratios of the supervised arm's raw reading over the label-free arm's condensed reading are stated with the wording in every case, and if they do not give the same wording, the text says that the wording depends on how the supervised networks are read. The training settings were developed on label-free runs too: any wording says that the supervised arm was trained with the label-free arm's settings and was not tuned. Whatever the wording, it does not carry to another family, mesh or budget, or to a supervised arm whose settings were chosen for the supervised loss.

**INVALID, INCOMPLETE.** A part that is INVALID or INCOMPLETE is not read; when part 2 is INCOMPLETE, part 1 stands. A verdict that is INVALID holds no statistic of the third sample. An INVALID is reported with its cause. If the cause is a label-free run without finite predictions, it is reported as a failure of a label-free network on this gate's members: the same state files gave finite predictions on G-C2.2's members on the host in the check before the stamp. An outcome that is INVALID, and a part that is INCOMPLETE by a stop condition, are final: the gate is not run again on the third sample, which is spent, and anything computed on it afterwards is exploratory and is reported as such.

## What the gate does not show

- Nothing about laboratory tests: every error is against the reference model.
- Nothing outside the family, its ranges, its mesh, and monotonic loading to 8 mm.
- Part 1: nothing for other networks than these three, for fewer runs, or for another family; the threshold is not a rule.
- Part 1: the spread sees only what differs between the runs. An error that the three runs share is not flagged. The host check shows the extreme case: in its runs before the stamp, on a processor and on the host, its three networks, trained for two epochs, were all far from the reference and agreed with one another, and none of their four pairs was flagged (`records/c23/before_stamp/smoke_report.json`; the review's record, round 2).
- Part 2: nothing at other budgets, with fewer labels, with labels at other levels, or where a reference solution is much more expensive than here. Between its eight labelled levels the supervised arm interpolates; the label-free arm is trained at displacements drawn anew at every step.
- Part 2: nothing about a supervised arm whose learning rate, schedule or stabilisation were chosen for the supervised loss. Both arms train with the settings of the earlier gates and with the stability recipe, which was developed on label-free runs; no supervised run of this size was made before this gate, and none is tuned in it.
- Part 2: the two arms do not run the same risk. The three label-free runs are known to have finished and to have passed G-C2.2, so the label-free arm cannot lose a seed to its training here; a supervised seed can, and then counts with infinite errors.

## Stop conditions

- A label of a held-out or tested member that does not converge or fails its checks stops the gate before any prediction, as in G-C2.2.
- A label of a training member that does not converge or fails its checks: the supervised arm is not trained and part 2 stays INCOMPLETE. Part 1, which is final by then, stands. No other solver settings are tried.
- A non-finite loss stops a supervised run for good; the runs are not repeated with other seeds.
- A checkpoint of a supervised run that cannot be read: as in G-C2.2, the run is started again from its beginning, and the restart is reported.
- A label-free run without finite predictions: the run is not predicted again, and the verdict is INVALID (see "Identity"). The operator has the predictions that the stop cancelled made, and the evaluation and the verdict written once, so that the INVALID verdict is on record.
- A command that the owner stops and does not let run again leaves INCOMPLETE what needs it: both parts for the evaluation of the label-free arm, part 2 for a supervised run or the evaluation of the supervised arm.
- An interruption that is none of these (the host restarts, a disk is full) is no stop of the gate: the interrupted command is run again as the runbook says, and the interruption is reported.

## Procedure

1. Before the stamp: an independent review of the new code, of this text and of the runbook, by a reviewer who wrote none of them and draws nothing of this gate (`docs/reviews/review_report_G-C2.3_2026-11-18.md`). On the host, from the draft: the host check (`c23/smoke.py`), the check of the state files' predictions, the pilot of the training labels, and the step timing; their records are in `records/c23/before_stamp/`. Then the stamp: fill in this document; hash the configuration and the code; tag `prereg-c23`.
2. On the host, from the tag: the host check again; then generate; label the third sample, G-C2.2's fresh members and the tested members; check the labels.
3. Predict with the three label-free states; evaluate the label-free arm (`rows_label_free.json`); write the verdict. Part 1 and the identity check are final at this point, before any training member has a label. The whole verdict is also written to `verdict_part1.json`, which no later command overwrites and which is written only while no training member is labelled; every later verdict states whether its part 1 is the one kept, and its command ends with an error if it is not. The SHA-256 of the label-free rows file is part of what is compared, because the same rows give the label-free side of part 2.
4. Label the training members; check; train the three supervised runs; evaluate the supervised arm; write the verdict again. It reads the label-free rows as they are, after checking that what they were computed from has not changed: the manifest, the ledger entries of the evaluated members, and the prediction files of the runs. Part 2 is final.
5. Return the records; verdict document; independent recomputation as for G-C2.2.

## References

As in `docs/PRESPEC_G-C2.1.md`.
