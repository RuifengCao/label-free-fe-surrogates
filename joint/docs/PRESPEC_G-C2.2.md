# Pre-specification of gate G-C2.2

Stamped 13 November 2026, 08:59 GMT. At that time no member drawn with seed 20261113 had been exported or solved, and no training of this gate had started.

## Question

G-C2.1 asked whether the project's transformer, trained on the total potential energy alone, predicts the force-deformation response of plastic bolted T-stubs it has not seen. It failed on both criteria: the median over three seeds was 6.6% and the 90th percentile 31%, and one seed did not train (`docs/G-C2.1_verdict.md`).

G-C2.2 asks the same question of the same problem after two changes of method that were found after that verdict:
- a stability recipe in the label-free training (two settings, below);
- the point of a prediction read from its field after one amplitude has been set by minimising the energy (the condensed reading, below).

**Hypothesis.** With these two changes the transformer meets C1 and C2 of G-C2.1 on held-out members that neither the training nor the choice of the method has seen.

**Unchanged from G-C2.1** (`docs/PRESPEC_G-C2.1.md`, which this document does not repeat):
- the reference model, its theory, mesh and solver;
- the family of T-stubs, its ranges and fixed values, and the 512 training members (seed 20261106);
- the loading through a spring of 20 kN/mm per quarter model, and the seven judged levels of the loading-device displacement, 0.5 to 8 mm;
- the judged quantity, the distance $F/F^*(e) - 1$ of a predicted point $(e, F)$ from the reference curve, and both thresholds;
- the network, the loss, the sampling of the loading levels, the learning rate, the schedule and the budget of 200 epochs.

**Changed**

1. **The stability recipe.** In the label-free training:
   - AdamW's second-moment coefficient $\beta_2$ is 0.99 instead of 0.999;
   - before the global clipping at 1.0, the gradient of the encoder is scaled down to at most 5 times the median of its norm over the previous 256 steps, from step 257 on. The norms in that window are those before any scaling. If the median is zero, a gradient that is not zero is scaled to zero.
2. **The condensed reading.** For a member and a level $D$, with $z$ the network's field at $D$ and $z_0$ its field at 0.1 mm, the smallest level sampled in training, the judged point is read from
   $z_c = \mathrm{keep}\,(z_0 + a\,(z - z_0))$,
   where keep sets the contact unknowns to at least zero, and $a$ minimises the training energy of $z_c$ at $D$ over $0.5 \le a \le 3$.
   - The minimisation is a safeguarded secant iteration on the slope in $a$, started at $a = 1$, with at most 12 energy evaluations in float32, stopped where $\lvert d\Pi/da\rvert \le 10^{-4}\,\Pi$ or on a bound. It returns the evaluated point of lowest energy. The first evaluated point is the raw field up to float32 rounding, so $z_c$ is not above the raw field in energy beyond that rounding.
   - No reference solution enters the reading. It uses the network's own two fields and the energy the network was trained on.
   - The error of the point is judged exactly as in G-C2.1.
   - The raw reading of G-C2.1, the point of $z$ itself, is reported and not judged.
3. **The held-out members are drawn afresh**: 64 members with seed 20261113. The 64 held-out members of G-C2.1 (seed 20261107) were read many times while the method was developed (below), so they are reported and not judged.
4. **The training seeds** are 5, 6 and 7. Seeds 0 to 4 were used before the stamp.
5. **No supervised arm.** G-C2.1's supervised arm stands as reported there.
6. **The host.** The three runs are made on the owner's laptop, the machine of the development runs: an NVIDIA GeForce RTX 4070 Laptop GPU with 8 GB under Windows, where G-C2.1 ran on a rented RTX 5090 under Linux.
   - G-C2.1's limit on the time of a step was a bound on the cost of a rented machine; it is not kept. In development a step took 0.38 s on this machine when it was otherwise idle and up to 0.8 s when it was in use, against 0.17 s on G-C2.1's host.
   - The owner uses the machine during the runs. A run may be interrupted and is then resumed from its last checkpoint.

**Why the recipe.** In G-C2.1 the loss of seed 0 rose in its eighth epoch to the level of the starting field and stayed there for the rest of the run. Its final state has latents that do not vary between the nodes, and the first hidden layers of its decoder and head are dead for every input checked, so no gradient reaches its encoder (`probes/c2_diag/RESULTS.md`, `HOST_STATES.md`). The host kept no record within an epoch. CPU replays of seeds 0 and 1 collapsed in the same way within six epochs, each after a run of bursts in the encoder's gradient. Branched from the states just before those two collapses, a cap on the encoder's gradient at five times its running median, $\beta_2 = 0.99$ and half the learning rate each prevented the collapse over the 256 steps that were run (`probes/c2_diag/BRANCHES.md`). The recipe takes the first two and leaves the learning rate as it was. Over whole runs it was tried in development only (below).

**Why the condensed reading.** The judged error grows with the error of the end displacement, magnified on a plastic plateau (G-C2.1's pre-specification). In development the raw field's amplitude was the weak part at the large levels: for the two full-length models trained with the recipe before this stamp, the 90th percentile of the error at 8 mm was 44% and 48% in the raw reading and 5.0% and 6.5% in the condensed one (`probes/c2_dev/README.md`, section 10). At the minimiser the spring's force balances the field's own resistance along the direction $z - z_0$; the derivation and its numerical check are in `probes/c2_dev/README.md`.

## Authority

**The owner** wrote the following (messages translated from Chinese; the originals are kept in the correspondence record):
- 10 November 2026, 21:18: bolted connections and plasticity are now the first priority; a full assessment of how to go on is wanted.
- 10 November 2026, 23:27: permission to use the GPU of the owner's laptop for development runs. "Start."
- 11 November 2026, 10:26: "Start", for a second batch of development runs.
- 11 November 2026, 11:17: "Route agreed": the next gate keeps G-C2.1's problem, that is the family, the spring, the levels and the criteria, and changes the method only. A spring scaled to each member was assessed and is kept as a fallback, not used here.
- 11 November 2026, 21:36: runs go on the owner's laptop where it can carry them; a server is rented only if there is no other way.
- 12 November 2026, 13:05: "Start", on the recommendations sent that morning: the recipe and nothing else in training; the condensed reading judged and the raw reading reported; three new training seeds; no new supervised runs.
- 12 November 2026, 16:53: "As recommended", on the four points put to the owner that day: the held-out members are drawn afresh and the former ones reported; the runs are made on the owner's laptop; the new code is reviewed once, independently, before the stamp; the stamp waits for the full-length development run of seed 1.

**Chosen here**
- The seed of the fresh held-out sample, 20261113.
- The bounds of the amplitude, 0.5 to 3, and the 12 energy evaluations: the values used in development since 11 November 2026.
- A checkpoint at the end of every epoch, so that an interrupted run loses little. A resumed run is the same run; every start, resume and end of a run is written to its `attempts.log`. It draws the same members and levels as an uninterrupted run. That it ends in the same state to the last bit was checked on a CPU (`tests/test_c22.py`) and, in the reduced configuration of the host check, on the laptop's GPU; it is not claimed for the runs of this gate.

**Changes.** Any change after this stamp is reported as a change after the stamp. No threshold, metric, reading or seed changes once the first training run has started.

## What was seen before the stamp

**G-C2.1**: its verdict and every metric of every pair of its 64 held-out and four tested members, for its three label-free and three supervised seeds. Per seed, the median and the 90th percentile of the judged error were: seed 0, which did not train, 170 and 5,075 times the reference force; seed 1, 6.61% and 31.16%; seed 2, 2.41% and 18.56%.

**The diagnostics after that verdict** (`probes/c2_diag/`, commits 7ed4338, 412634e and 8eb6e68).

**The development runs of 10 to 13 November 2026** (`probes/c2_dev/README.md` gives every run; none was pre-specified, and none changes G-C2.1's verdict). All used G-C2.1's stamped code and data, on the owner's laptop (an RTX 4070 Laptop GPU) or on a CPU. Every reading below is on the 64 held-out members of G-C2.1, as median, 90th percentile and number of the 448 pairs above 10%.

- **Short runs**, the first 30 epochs of the gate's schedule:
  - without the recipe, seed 0 collapsed in its fourth epoch, between steps 1,856 and 1,920; seed 1 ran 15 epochs without a collapse;
  - with the recipe, seeds 0, 1, 3 and 4 ran 30 epochs without a collapse.
  - A run draws the same members and levels as the host's run of the same seed. Over the first three epochs the epoch losses of the laptop's two runs of seed 0 lay within 0.003 of the host's (0.0025 without the recipe, 0.0016 with it).
- **The model of G-C2.1's seed 2, not trained further**: raw reading 2.41%, 18.56%, 74 pairs; condensed reading 1.64%, 11.35%, 56 pairs.
- **That model on training members.** Twenty-four training members were solved at the judged levels and compared with the held-out members; the model was then fitted to single ones of them, with the gate's loss and with a loss on the condensed field.
- **That model trained 10 more epochs on the training family at a low learning rate**, three variants: condensed reading 1.60% to 1.70%, 9.91% to 10.08%, 44 to 47 pairs. The same 43 pairs stayed above 10% in all three.
- **A reading with seven amplitudes**, one for each of the member's fields at the judged levels, on one of those three models: 1.47%, 8.59%, 34 pairs. It is not used in this gate.
- **The recipe at full length, seed 0** (200 epochs, 102,400 steps): no collapse; raw reading 1.42%, 7.27%, 35 pairs; condensed reading 0.84%, 3.00%, 2 pairs.
- **The recipe at full length, seed 1** (the same length; it ended on 13 November 2026 at 04:22 GMT): no collapse; raw reading 1.55%, 8.03%, 38 pairs; condensed reading 0.95%, 3.22%, 5 pairs. G-C2.1's run of this seed, on the same draws without the recipe, had read 6.61% and 31.16%.
- **The two full-length models compared.** Of the pairs above 10% in the raw reading, 32 are the same in both; they lie in 20 and 23 members, 19 of them the same.
- The condensed reading under a spring scaled to each member, which showed that the judged error of the condensed reading does not depend on the spring's stiffness.

**What these runs mean for this gate**
- The 64 held-out members of G-C2.1 took part in every choice above. They are therefore not judged here.
- The training members and the training seeds 0, 1, 3 and 4 were used; the training members are kept, the seeds are not.

**The code of this gate** was checked on its own, with nothing of this gate drawn.
- Its 20 tests (`tests/test_c22.py`) and its check of a host (`c22/smoke.py`) train and evaluate small models on a reduced configuration: other members (family seeds 7, 8 and 101, on a coarse mesh), another network, a few epochs. They use the seed numbers 5, 6 and 7 there; no run of this gate's configuration was started.
- The host check was run on the laptop before the stamp, through the queue that runs the gate, on 13 November 2026 from 04:24 to 04:27 GMT, with the code as stamped here. It passed (`records/c22/host_check/`):
  - the labels were solved in a pool of spawned worker processes and met the label check;
  - a run stopped after two of its four epochs and resumed ended with the weights, the losses, the capped steps and the three prediction files of the uninterrupted run, with no difference, on the GPU;
  - no condensed field lay above its raw field in energy by more than one part in a million;
  - the evaluation wrote the same verdict record with four worker processes as with none.
- A separate agent that wrote none of the code reviewed the new code, this text and the runbook before the stamp, in three rounds. Its checks ran the same reduced configuration, with the seed number 5, and `write-config`. The code, the tests, this text and the runbook were changed as it asked; its reports and what was done about each finding are in `docs/reviews/review_report_G-C2.2_2026-11-12.md`.
- After the last round no file of `c22/` and no test changed, apart from a blank line in `c22/train.py` that the round had noted. This text received the values of the stamp, the full-length run of seed 1, the result of the host check and, in the expected outcome and the reason for the condensed reading, the second full-length model; the sentence on a resumed run now names the host check. The runbook received a sentence on the host check's report that the round had asked for, the configuration hash, the tag of this stamp from which the tree is taken, the laptop's number of logical processors as the host check recorded it, and the loss level of the second full-length run.

**This gate's sample.** No member drawn with seed 20261113 has been exported or solved.

## Expected outcome, stated before the run

- **C1 is expected to hold.** The condensed reading's median was 0.84% and 0.95% for the two full-length models with the recipe, and 1.6% for a model without it.
- **C2 is expected to hold, with less certainty.** It was 3.00% and 3.22% for those two models, with 2 and 5 of the 448 pairs above 10%. The uncertainty has three sources:
  - two full-length runs with the recipe had ended at the stamp, so the spread between seeds rests on two;
  - the tail comes from few members: under the raw reading the 35 and 38 pairs above 10% lay in 20 and 23 of the 64 members, 19 of them the same, at 4 mm and above; a fresh sample may hold more of them;
  - a seed may still collapse. Two seeds within the thresholds decide the medians.
- **The raw reading** is expected to meet C1 and to lie near the threshold of C2, where it was 7.27% and 8.03% for those two models.
- **The gate is therefore expected to pass.**

## Configuration

**The configuration** is `c22/config.py`: G-C2.1's configuration with the changes listed above and nothing else.
- Its canonical JSON has SHA-256 `ef5376a4d6c3cc98d7888121439c8d959ee817d332958dd6b1141b25e78734bb`.
- The training and evaluation commands refuse to run unless they are given this hash. The evaluation also refuses a run folder whose history does not carry it, and data whose sets do not have the configured sizes.

**The repository code** the run imports is pinned file by file, as in G-C2.1; the files and their hashes are the same.

**The gate's own code.** The files of `c2/` and `fejoint/` stamped for G-C2.1 are used unchanged (`sha256sum -c docs/G-C2.1_code.sha256` still passes). The new files are in `c22/`:

| File | SHA-256 |
|---|---|
| `c22/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `c22/__main__.py` | `2c692935ecb5d24284738e8f0529a2c2f2fb25807ebf2385061fee0c5abae15f` |
| `c22/config.py` | `9541e1c6e22cd6739d4cf589defb050d9983c2a537eef1bf44bd73966b339c8c` |
| `c22/condense.py` | `c722f56dcd0d929eca4306b50ed34630dbd5b9e0c71464144c8479a71705b1a5` |
| `c22/data.py` | `5f1456856c87d6305952ac9efc0efa76f4975fca7fd68ef134017acd882e4baf` |
| `c22/train.py` | `7082ac6a174cb47a0d4e55e48284783106ed9c74b889a669e34a007fc4fd988e` |
| `c22/evaluate.py` | `329e39a23b744ba1860c2c357dc77ed99317ff2c8cf7b38a5be37aeb0c35cf22` |
| `c22/smoke.py` | `604ff851da4d86971ecc33e5a4dbbc97d5c6cee00121d25fe16d05f696834697` |

A copy is kept in `docs/G-C2.2_stamped_code`. The file `docs/G-C2.2_code.sha256` lists every hash for `sha256sum -c`.

## Data

**Family, levels, export and labels**: as in G-C2.1.

**Samples**
- 512 training members, seed 20261106: the members of G-C2.1.
- 64 held-out members, seed 20261113: judged.
- The 64 held-out members of G-C2.1, seed 20261107: reported and not judged.
- The four tested members: reported and not judged.
- The code refuses a held-out seed used before the stamp (7, 8, 101, 102, 20261106 and 20261107) and a training seed used before the stamp (0 to 4).

**Labels**: exact solutions at the seven levels for the two held-out samples and the tested members, with G-C2.1's solver settings and label check. No training member is labelled.

## Model and training

**Network, loss and sampling**: as in G-C2.1.

**Training**: as in G-C2.1's label-free arm, with the stability recipe.
- The window of the cap holds the encoder's gradient norms of the previous 256 steps, before any scaling; it is saved in the checkpoints.
- Each run records its epoch losses, the steps at which the cap acted with their ratios, and the steps whose ratio exceeded 10.
- A non-finite loss stops the run, and a run whose raw or condensed predictions are not finite records that instead of predictions. Either stop is final and is not retried.
- No run is stopped, repeated or replaced because it trains badly.
- A run whose checkpoint cannot be read, after a crash of the machine for instance, is started again from its beginning with the same seed, which draws the same members and levels. The restart is reported.

**Arm**

| Arm | Loss | Training members | Seeds | Steps per seed |
|---|---|---|---|---|
| label_free | mean of $\log \Pi$ | 512 | 5, 6, 7 | 102,400 (200 epochs) |

**Predictions.** After training, for every held-out and tested member at the seven levels: the raw field, the condensed field, the amplitude, and how the amplitude's iteration ended; and the member's field at the base level, so that the condensed fields can be computed again from the returned files.

**Budget**: 307,200 steps. At the step times seen in development, 0.38 to 0.8 s, a run takes 11 to 23 hours and the three runs 32 to 68 hours.

## Criteria (on the fresh held-out members, condensed reading)

The point of a field is $(e, F)$, $e$ its end displacement and $F = 4 k_s (D - e)$. Its error is $F/F^*(e) - 1$, with $F^*(e)$ from an exact solve with $e$ prescribed, as in G-C2.1. The fields judged are the condensed fields $z_c$.

**C1.** The median over the three seeds of the per-seed median of $\lvert F/F^*(e) - 1\rvert$ over the 448 pairs of the fresh held-out members is at most 0.05.

**C2.** The median over the three seeds of the per-seed 90th percentile of $\lvert F/F^*(e) - 1\rvert$ over the same pairs is at most 0.10.

**Verdict.** G-C2.2 passes if and only if C1 and C2 hold.
- Infinite errors of pairs, final stops of seeds and the INCOMPLETE verdict are treated as in G-C2.1.
- An amplitude that ends on a bound, or whose iteration has not met its tolerance after 12 evaluations, is used as it is and counted.

**Reported, not judged**
- The raw reading on the fresh held-out members, with what C1 and C2 would be for it.
- Both readings on the 64 held-out members of G-C2.1 and on the tested members.
- Every metric G-C2.1 reported, for both readings.
- The amplitudes, and the counts of amplitudes on a bound or not converged, for each of the three sets.
- The cap's actions and the bursts of each run.
- The metrics of every pair, in `verdict.json`.

## Interpretation, fixed in advance

**PASS.** With the two stability settings, label-free training of the project's transformer reproduced the reference model's force-deformation curve on 64 T-stubs that neither the training nor the choice of the method had seen: within 5% in force in the median and within 10% at the 90th percentile, in the median over three training seeds.
- The point is read after one amplitude of the field has been set by minimising the energy. Any wording says so, and gives the raw reading beside it.
- The limits stated for a PASS of G-C2.1 hold: the 5 mm mesh, small strains, frictionless contact, the deformation theory under monotonic loading, and the gap of the reference model to the T-stub tests.
- G-C2.1's verdict stands. G-C2.2 is a new gate with a changed method; it does not show which of the two changes is needed.

**FAIL on C2 only, FAIL on C1 only, FAIL on both**: as in G-C2.1. The pairs above 10% are listed by member and level.

**In every FAIL**
- The thresholds stay.
- A FAIL decided by a seed that stopped on a non-finite loss or prediction is reported as a failure of the recipe at these settings, with the seed named. The runs record no probe of a collapse; whether a seed that trained badly had collapsed is read afterwards from its loss history and its fields, and does not enter the verdict.
- The raw reading, the members of G-C2.1 and the other reported readings are described, not substituted for the criteria.
- Any next stage is pre-specified anew.

**INCOMPLETE**: as in G-C2.1.

## What the gate does not show

- Everything G-C2.1's pre-specification lists.
- Whether the recipe is needed: this gate has no arm without it. G-C2.1 is that comparison only loosely, with other seeds, another host and other held-out members.
- The share of each change: the raw reading is reported, the old training is not rerun.
- Anything about the seven-amplitude reading or the further training at a low learning rate tried in development.

## Stop conditions

- **Checks.** A precondition, test, hash or count in the runbook differs from what the runbook states: stop and report before going on.
- **The labels.** The label check fails: stop before any training, and report. The check is G-C2.1's, on the two held-out samples and the tested members.
- **Errors.** A training run that ends with an error other than a final stop: stop the training loop and report.
- **Time.** If the three runs have not ended 96 hours after the first started, the owner is told. The runs go on unless the owner stops them; a stop before the three seeds have ended leaves the verdict INCOMPLETE until they are resumed.
- **The machine.** All three runs are made on the laptop, and so are the labels and the evaluation, which are CPU computations in float64. Moving a run to another machine is a change after the stamp and is reported as one.
- No other training uses the GPU during the runs. The times of the steps are recorded and are not a criterion.

## Procedure

`RUNBOOK_C22.md`, in its sections:
0. preconditions, the hash checks and the tests;
1. the configuration hash and the repository check;
2. generation, without solves;
3. labels for the two held-out samples and the tested members, and their check;
4. the three training runs, which resume if interrupted, each followed by its predictions;
5. evaluation;
6. the return package.

## References

- `docs/PRESPEC_G-C2.1.md`, `docs/G-C2.1_verdict.md` and the references given there.
- `probes/c2_diag/RESULTS.md`, `BRANCHES.md`, `HOST_STATES.md`.
- `probes/c2_dev/README.md`.
