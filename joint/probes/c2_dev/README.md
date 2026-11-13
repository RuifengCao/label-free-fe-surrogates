# After G-C2.1: the tail, a stability recipe and a condensed reading

Exploratory, after the verdict (`docs/G-C2.1_verdict.md`) and not pre-registered, like the notes in `../c2_diag`. Nothing here changes the verdict. 10 to 13 November 2026.

G-C2.1 failed twice over: one label-free seed collapsed, and the two that trained had a tail of errors at the largest loading levels (90th percentiles of 31.2% and 18.6%, against 10%). `../c2_diag` traced the collapse. This note reads the tail, and records the development runs in which two changes of method were tried: a stability recipe for the training, and a reading of the predicted point after one amplitude of the field has been set by minimising the energy.

**The 64 held-out members of G-C2.1 were read throughout**, for every figure below that is not marked otherwise. They are unseen by every training here, but not by the choices of method made on these figures. A gate that judges those choices needs a fresh held-out sample.

Words used throughout:
- **the judged error** of a predicted point (e, F) is G-C2.1's: F/F\*(e) - 1, with e the end displacement, F = 4 k_s (D - e) the spring's force and F\*(e) the reference curve;
- **a reading** is given as median, 90th percentile (linear interpolation) and number of pairs above 10%, over the 448 pairs of the 64 members and seven levels. G-C2.1's criteria are a median of at most 5% (C1) and a 90th percentile of at most 10% (C2); C2 holds when at most 44 pairs are above 10%;
- **the host's models** are the final states of G-C2.1's label-free runs (`../c2_diag/HOST_STATES.md`); only that of seed 2 is used here, the better of the two that trained.

## Findings

1. **The tail is the error of the end displacement, magnified by the spring reading.** A relative error x of the end displacement puts the spring's force off by -x e/(D - e). At 4, 6 and 8 mm the judged error follows that product (correlations of 0.997 to 1.000 in seeds 1 and 2). The factor e/(D - e) is set by the member's strength against the fixed spring: at 8 mm it runs from 0.97 to 5.61 over the 64 members, with a median of 1.80. The end displacement is too small in every one of the 40 pairs with a yield stress below 300 MPa at 6 and 8 mm; in seed 2 those pairs have a median judged error of 24.0%, and the other 408 pairs have 44 above 10%, which is the number C2 allows (section 2).
2. **The model fits the training members no better.** On 24 training members solved for this note, the host's seed 2 model has the errors it has on the held-out members: over all levels, a median energy gap of 0.37% against 0.42% and a median end-displacement error of 2.9% against 2.6% (section 3). The tail is a failure to fit, not to generalise.
3. **The errors sort by mechanism.** A closed-form estimate with four mechanisms (the three T-stub modes of EN 1993-1-8 and yielding of the web in tension) gives the reference force at an end displacement of 4 mm within 0.92 to 1.09. By it, the web governs 32 of the 64 members, mode 1 governs 17 and mode 2 governs 15. Seed 2 has 2 of 105 pairs above 10% in the mode 2 members, 31 of 119 in the mode 1 members and 41 of 224 in the web members (section 4).
4. **With the recipe, four seeds ran 30 epochs without a collapse, and two of them 200.** The recipe is AdamW's β2 at 0.99 and a cap on the encoder's gradient at five times its running median, the first two changes of `../c2_diag/BRANCHES.md` together. Without it, on the same GPU, seed 0 collapsed in its fourth epoch and seed 1 ran 15 epochs without a collapse. With it the bursts still occur (11 to 20 in 30 epochs, up to 220 times the running median) and are capped, and the losses over epochs 21 to 30 equal those of the host's seed that never collapsed (sections 5 and 10).
5. **Setting one amplitude by the energy removes much of the tail, without retraining.** The condensed reading takes the field z_c = z_0 + a (z - z_0), with z the network's field at the level, z_0 its field at 0.1 mm, and the scalar a minimising the energy the network was trained on; no reference solution enters. For the host's seed 2 model it brings the reading from 2.41%, 18.56% and 74 pairs to 1.64%, 11.35% and 56 pairs (section 6).
6. **Under the condensed reading the judged error is the stiffness of the network's ray against the true structure's, and the spring only selects the point at which it is read.** Derived in section 6 and checked on 90 pairs: a spring scaled to each member lowers e/(D - e) to between 0.35 and 0.96 of its value and moves the condensed judged error by 0.15 percentage points in the median. A softer spring therefore cannot repair the tail; it can only read each member at a shallower point.
7. **Putting the condensed field into the loss adds little to the condensed reading.** For a single mode 1 member, the gate's own loss with the condensed reading ends at 5.8% at 8 mm after 600 steps, and a loss on the condensed field is at 5.3% after 500, from 65.5% in the raw reading of the start (section 7). On the whole family a loss on the condensed field cost 5.7 times the training time and made the raw reading worse (section 8).
8. **Ten more epochs at a low learning rate bring the host's seed 2 model to the threshold and no further.** Three variants end at 9.91% to 10.08% with 44 to 47 pairs above 10% under the condensed reading. The same 43 pairs, in 18 members and all too stiff, stay above 10% in all three (section 8).
9. **A reading with seven amplitudes lowers that to 8.59% and 34 pairs**, on one of the three models. It halves the pairs above 10% in the mode 1 members (18 to 9) and hardly moves those in the web members (28 to 24) (section 9).
10. **The recipe at full length gives a far better model than the host's seed 2, in both seeds run.** Seed 0, 200 epochs, no collapse: 1.42%, 7.27% and 35 pairs in the raw reading; 0.84%, 3.00% and 2 pairs in the condensed reading. Seed 1, the same: 1.55%, 8.03% and 38 pairs; 0.95%, 3.22% and 5 pairs. The host's own run of seed 1, on the same draws without the recipe, read 6.61% and 31.16%. The web members, which finding 8 could not move, have no pair above 10% under the condensed reading in seed 0 and two in seed 1 (section 10). Finding 8's hard core belonged to that model, not to the method. The raw tail that is left belongs to the members: 32 pairs are above 10% in both seeds.
11. **What this does not show** is in section 11: above all, that two seeds are two seeds, and that none of this is a gate.

## 1. What was run

**Inputs.** The stamped tree of G-C2.1 (`git archive prereg-c2`), its return package (`records/c2/return`), the 580 instances exported again with the stamped code, and the host's three final states.

**Machines.**
- A CPU sandbox with two cores (Python 3.13.18, numpy 2.5.3, scipy 1.18.1, torch 2.12.1) for every reading made with the stamped numpy reference code, the exact solutions of sections 3 and 6, the readings of the host's models in sections 6 and 9, and the summaries.
- A laptop with an NVIDIA GeForce RTX 4070 Laptop GPU (8 GB; Windows 11, Python 3.12.16, torch 2.12.1 with CUDA 13.2, numpy 2.4.6, scipy 1.18.1) for all training and for the readings of sections 8 and 10. A step of G-C2.1's training took 0.38 s there when the machine was otherwise idle and 0.6 to 0.8 s when it was in use; the host of G-C2.1 took 0.17 s.

**The training scripts** (`dev/`) follow `c2.train.train` step by step, with the stamped configuration (its hash is in each run's `summary.json`) and the stamped code imported unchanged. They add the recipe as an option, the per-step records and probes of `../c2_diag`, a count of inactive units, and a stop after a collapse.
- A run draws the same members and displacements as the host's run of the same seed, so their epoch losses compare models, not draws. The GPU run of seed 0 without the recipe drew the member and displacements of the CPU replay of `../c2_diag` at each of its 2,432 steps, and its losses equal the replay's within 10⁻⁵ over the first 64 steps (`records/logs/draws_check.log`); after that the two part, as the replay and the host did.
- Over the first three epochs the two GPU runs of seed 0 lie within 0.003 of the host's epoch losses (0.0025 without the recipe, 0.0016 with it).

**Bursts and collapses** are counted as in `../c2_diag`: a burst is a step whose encoder gradient norm exceeds ten times its median over the previous 256 steps; a collapse is a probe (every 64 steps, on the first training member) at which the relative variance of the latents has fallen below a third of its value at the probe before.

**Judging.** The development readings judge a point against a monotone interpolant of the member's exact points: its seven labels, the origin, and the exact solves at prescribed end displacement that G-C2.1's evaluation made for six runs, 46 to 50 points a member (`refcurve.py`, `make_eval_ref.py`, `records/eval_ref.json`). Leaving one point out, the interpolant is off by at most 0.33% for end displacements of 1 mm and more, and by 0.03% at the 90th percentile (`records/logs/refcurve.log`). The raw reading of the host's seed 2 model comes out as in the verdict: 2.41%, 18.56%, 74 pairs. The reference data enter the judging only, never a training or a reading.

## 2. The tail of G-C2.1, read again

From the returned rows and predictions alone (`a1_readings.py`, `magnification.py`). Label-free seed 2, the 64 held-out members at each level:

| D (mm) | Judged error: median; 90th percentile | Pairs above 10% | End-displacement error, median | Energy gap, median | e/(D - e) of the reference, median |
|---|---|---|---|---|---|
| 0.5 | 1.7%; 4.5% | 0 | 1.7% | 0.15% | 0.14 |
| 1 | 1.4%; 3.3% | 0 | 1.4% | 0.14% | 0.16 |
| 2 | 1.7%; 4.6% | 3 | 1.9% | 0.15% | 0.18 |
| 3 | 1.6%; 15.2% | 11 | 3.3% | 0.29% | 0.26 |
| 4 | 2.6%; 21.1% | 11 | 3.6% | 0.68% | 0.57 |
| 6 | 3.4%; 33.3% | 18 | 3.0% | 1.91% | 1.23 |
| 8 | 9.5%; 46.6% | 31 | 5.2% | 3.25% | 1.80 |

- The error of the end displacement grows by a factor of three from the smallest level to the largest; the judged error grows by more, because the factor e/(D - e) grows from 0.14 to 1.80.
- At 4, 6 and 8 mm the judged error and the product of that factor with the end-displacement error have correlations of 0.997 to 1.000 in seeds 1 and 2; the judged error is 1.06 to 1.12 times the product in the median, the reference curve not being quite flat.
- At 8 mm the reference forces run from 97 to 324 kN and the factor from 0.97 to 5.61; it is above 1.5 in 47 members and above 2.5 in 16.
- **The weak corner**, the 40 pairs with a yield stress below 300 MPa at 6 and 8 mm:

| | Seed 2 | Seed 1 |
|---|---|---|
| Pairs above 10% | 30 | 34 |
| Judged error, median | 24.0% | 34.0% |
| End-displacement error, median (too small in all 40) | -10.4% | -13.6% |
| Energy gap, median | 8.3% | 11.0% |
| The other 408 pairs: median; 90th percentile; above 10% | 2.2%; 10.4%; 44 | 6.0%; 21.0%; 119 |

**Other readings of the same predictions, without retraining** (`a1_readings.py`, `a2_secant.py`, `a3_linesearch.py`, `a3_final.py`). A line search minimises the energy of the predicted field along one direction and reads the point again; it uses no reference solution.

| Reading | Seed 1 | Seed 2 |
|---|---|---|
| The gate's: e of the field, force from the spring | 6.61%, 31.16%, 153 pairs | 2.41%, 18.56%, 74 pairs |
| Force from the stresses, same e | 6.66%, 23.92% | 3.36%, 15.94% |
| Line search along the network's own path (the difference of its fields at the neighbouring levels) | 4.22%, 14.90%, 74 pairs | 1.94%, 12.90%, 59 pairs |
| Line search in the amplitude of the part of the field the load induces | 5.16%, 19.10%, 115 pairs | 2.18%, 12.65%, 62 pairs |

- In the last row the unloaded field was extrapolated from the network's fields at 0.5 and 1 mm. The condensed reading of section 6 is this reading with the network's own field at 0.1 mm in its place, and a solve that keeps the amplitude within bounds.
- The force read from the difference of the energies of neighbouring levels, a mean force over the interval and so another quantity than the judged one, is off by 0.86% in the median over all intervals in seed 2 (1.71% in seed 1), and by 29% (33%) at the 90th percentile of the interval from 6 to 8 mm.

## 3. Training members against held-out members

Sixteen training members with a yield stress below 300 MPa and sixteen others were drawn at random (`select_members.py`, seed 20261111) and solved at the seven judged levels with the stamped code and the gate's solver settings, one process for each kind (`label_members.py`). The solves were stopped at 24 members, 11 of the first kind and 13 of the second, when the answer was clear. All levels converged; the force from the stresses and the force from the spring differ by at most 8 × 10⁻¹³.

The host's seed 2 model on these members and on the held-out members (`predict_states.py`, `compare.py`; the held-out figures are the verdict's):

| Pairs | | Number (members) | Energy gap: median; 90th percentile | End-displacement error: median; 90th percentile | Too small |
|---|---|---|---|---|---|
| Below 300 MPa, 6 and 8 mm | training | 22 (11) | 6.95%; 22.9% | 8.9%; 24.0% | 22 |
| | held-out | 40 (20) | 8.26%; 20.4% | 10.4%; 18.1% | 40 |
| Below 300 MPa, 3 and 4 mm | training | 22 (11) | 2.68%; 8.1% | 9.1%; 39.8% | 19 |
| | held-out | 40 (20) | 2.92%; 8.4% | 9.1%; 29.0% | 37 |
| Others, 6 and 8 mm | training | 26 (13) | 0.86%; 2.3% | 3.7%; 7.3% | 22 |
| | held-out | 88 (44) | 1.70%; 5.6% | 3.2%; 8.7% | 75 |
| All | training | 168 (24) | 0.37%; 5.8% | 2.9%; 12.2% | 127 |
| | held-out | 448 (64) | 0.42%; 5.5% | 2.6%; 11.0% | 336 |

After 200 epochs the model had not fitted the weak training members either. More training members would not have helped.

## 4. Four mechanisms

**The estimate** (`rule_explore3.py`, `records/fit4.json`). With m and n the lever arms of EN 1993-1-8, M_pl the plastic moment of the flange over the length of 80 mm, and B the yield force of the bolts, the four forces are 4 M_pl/m (mode 1), (2 M_pl + n B)/(m + n) (mode 2), B (mode 3) and the yield force of the web's section. Each is multiplied by a fitted factor and the four are combined by a smooth minimum with a fitted exponent. The five constants were fitted to the reference force of the 64 held-out members at a given end displacement:

| End displacement | Members | Factors on modes 1, 2, 3 and the web | Reference over estimate | Leaving one member out |
|---|---|---|---|---|
| 2 mm | 64 | 1.67, 1.16, 1.30, 1.03 | 0.93 to 1.09 | 0.92 to 1.10 |
| 3 mm | 64 | 1.74, 1.25, 1.27, 1.04 | 0.92 to 1.09 | 0.92 to 1.11 |
| 4 mm | 64 | 1.83, 1.34, 1.33, 1.07 | 0.92 to 1.09 | 0.91 to 1.10 |
| 5 mm | 46 | 1.91, 1.38, 1.37, 1.10 | 0.92 to 1.08 | 0.91 to 1.09 |

The governing mechanism of a member is the smallest of its four factored forces at 4 mm: mode 1 in 17 members, mode 2 in 15, the web in 32, mode 3 in none. The three T-stub modes alone miss the web. For `eval_0043` they give 201, 210 and 297 kN, the web's section yields at 130 kN, and the reference force at 4 mm is 137 kN.

**The host's seed 2 model by mechanism** (the raw columns of `records/logs/condense_summary.log`):

| Governing mechanism | Members | All levels: median; 90th percentile; above 10% | 6 and 8 mm: median; 90th percentile; above 10% |
|---|---|---|---|
| Mode 2 (flange and bolts) | 15 | 1.48%; 4.8%; 2 of 105 | 3.1%; 8.6%; 2 of 30 |
| Mode 1 (flange) | 17 | 3.25%; 30.4%; 31 of 119 | 15.4%; 66.2%; 18 of 34 |
| Web yielding | 32 | 2.43%; 18.3%; 41 of 224 | 8.6%; 36.0%; 29 of 64 |

- The yield stress below 300 MPa of finding 1 is a coarse stand-in for this: the mode 2 members are fine, and the tail lies in the mode 1 and the web members at the large levels.
- The two kinds fail differently under the condensed reading of section 6. It repairs most of the mode 1 tail, so those fields have the right shape and too small an amplitude. It leaves the web tail: in the worst member, `eval_0043` at 8 mm, the predicted bolt force is 68% above the reference before the reading and 69% after it, with the end displacement 23% and 16% short.

## 5. Short runs with and without the recipe

Six runs of the first epochs of G-C2.1's schedule on the GPU (`dev/train_dev.py`; `runs_compare.py`, `probes_summary.py`, `analyse_run.py`). The recipe:
- AdamW's β2 is 0.99 instead of 0.999;
- before the global clipping at 1, the encoder's gradient is scaled down to at most five times the median of its norm over the previous 256 steps, from step 257 on.

| Run | Recipe | Seed | Epochs | Bursts (largest) | Steps capped | Collapse | Largest fall of the latents' relative variance between two probes, from step 512 |
|---|---|---|---|---|---|---|---|
| `L1_control_s0` | no | 0 | 4, stopped 512 steps after the collapse | 6 (150 times) | | between steps 1,856 and 1,920 | 0.838 to 0.077 |
| `L1_control_s1` | no | 1 | 15 | 14 (187 times) | | none | 0.824 to 0.704 |
| `L2_recipe_s0` | yes | 0 | 30 | 13 (163 times) | 45 | none | 0.306 to 0.277, at step 512 |
| `L2_recipe_s1` | yes | 1 | 30 | 11 (220 times) | 40 | none | 0.479 to 0.429, at step 576 |
| `L2_recipe_s3` | yes | 3 | 30 | 11 (32 times) | 43 | none | 0.651 to 0.629, at step 896 |
| `L2_recipe_s4` | yes | 4 | 30 | 20 (148 times) | 49 | none | 0.395 to 0.349, at step 640 |

- **Without the recipe.** Seed 0 collapsed in its fourth epoch, after a burst of 150 times at step 1,871, at a learning rate of 3.7 × 10⁻⁴ inside the warm-up; the host's run of the same seed rose in its eighth epoch and the CPU replay collapsed in its sixth. Seed 1 had its largest bursts at steps 1,447 (90 times), 2,374 (187) and 2,381 (98) and did not collapse in its 15 epochs; the host's run of that seed did in its fourteenth, where it lies 0.198 above this run. On the same draws the host, the CPU replay and this GPU collapsed in different epochs or not at all: whether and when a run collapses depends on rounding.
- **With the recipe.** In the four runs the latents' relative variance has a median of 0.95 to 0.97 from step 512 on, and the largest bursts leave it where it was: 0.957 and 0.954 at the probes around the burst of 220 times in seed 1, 0.958 and 0.958 around that of 163 times in seed 0. The falls in the table belong to the first two epochs, while the variance is still rising from its start. Seeds 0 and 4 still have bursts in the last five of the 30 epochs.
- **The loss is not slowed.** Mean loss over epochs 21 to 30: 10.494, 10.504, 10.501 and 10.519 for the four recipe runs; 10.495 for the host's seed 2, which never collapsed; 10.580 and 10.618 for the host's seeds 1 and 0. Against the host's run of the same seed, the recipe run of seed 0 differs by at most 0.006 through epoch 7 and is 0.07 to 0.14 lower from epoch 8 on.
- **The rule stated before these runs** was: adopt the recipe if at least one run without it collapses and none of the four with it does, with steady probes. It was met.
- Thirty epochs are the start of the schedule: the learning rate is still 97% of its peak. Section 10 has the full length.

## 6. The condensed reading

**The reading.** For a member and a level D, with z the network's field at D and z_0 its field at 0.1 mm, the smallest level sampled in training:

z_c = keep (z_0 + a (z - z_0)), with a minimising the training energy of z_c at D,

where keep sets the contact unknowns to at least zero. The point (e, F) is then read from z_c as the gate reads it from z. No reference solution enters; the reading uses the network's two fields and the energy it was trained on, and costs a few energy evaluations for a field.
- The first version (`condense_eval.py`, on a CPU, for this section) made secant steps on the slope in a and kept the lowest energy. The version used from section 7's second round on (`dev/condense.py`) walks to a change of sign of the slope, then makes secant steps inside the bracket, with a between 0.5 and 3 and at most 12 energy evaluations in float32, and returns the evaluated point of lowest energy. The two agree on the host's seed 2 model: the same summary figures, and judged errors within 0.16 percentage points pair by pair.
- The raw field is among the evaluated points, so in the float32 energy of the solve the condensed field is never above it. Evaluated again in float64 for the judging, the condensed energy is above the raw one in at most two pairs of a reading, by at most 10⁻⁷ of its value.

**Why it should help, and what it cannot do.** Derived; exact where the minimisation in a is exact and the clamp does not change along the ray. Per quarter model, write W(z) for the strain energy of the parts and the bolt, so that the energy is W(z) + ½ k_s (D - e(z))², and f\*(e) for the reference reaction at end displacement e, so that the judged error is J = k_s (D - e)/f\*(e) - 1.
1. Along the ray z(a) = z_0 + a (z - z_0), the energy is stationary in a where dW/da = k_s (D - e) de/da.
2. Define the ray's own reaction f_ray(e) = (dW/da)/(de/da), the force that pushes the structure to the end displacement e along the ray. At the condensed point e_c the spring balances it: k_s (D - e_c) = f_ray(e_c).
3. Hence J = f_ray(e_c)/f\*(e_c) - 1 =: s, how much stiffer the ray is than the true structure at e_c. The spring's stiffness does not appear in s; it selects the point e_c, where its line meets the ray's curve.
4. For the raw field the spring's force is off the ray's reaction by a relative imbalance ρ, and 1 + J = (1 + s)(1 + ρ). The energy is of second order in ρ, so the training leaves what it leaves; the condensed reading removes it.
5. Linearised, the error of the end displacement is -s / [m (1 + f\*'/k_s)] with m = e/(D - e): at a given s, a softer spring, which lowers m, raises the error of the end displacement.

**The host's seed 2 model, not retrained** (`condense_eval.py`, `condense_summary.py`):

| Pairs | Number | Raw: median; 90th percentile; above 10% | Condensed: median; 90th percentile; above 10% |
|---|---|---|---|
| All | 448 | 2.41%; 18.56%; 74 | 1.64%; 11.35%; 56 |
| D = 3 mm | 64 | 1.64%; 15.2%; 11 | 1.88%; 11.3%; 8 |
| D = 4 mm | 64 | 2.57%; 21.1%; 11 | 2.69%; 11.1%; 9 |
| D = 6 mm | 64 | 3.41%; 33.3%; 18 | 4.25%; 17.9%; 13 |
| D = 8 mm | 64 | 9.48%; 46.6%; 31 | 7.63%; 22.4%; 24 |
| Mode 2 members | 105 | 1.48%; 4.8%; 2 | 1.00%; 3.1%; 1 |
| Mode 1 members | 119 | 3.25%; 30.4%; 31 | 4.28%; 11.9%; 20 |
| Web members | 224 | 2.43%; 18.3%; 41 | 1.42%; 13.5%; 35 |

- The amplitudes lie between 0.93 and 1.32, none at a bound.
- The reading does not improve every pair: 163 pairs are worse after it, and the median rises at 3, 4 and 6 mm.

**The check of point 3 under another spring** (`rule_v0.py`, `respring_eval.py`, `respring_summary.py`). A spring scaled to each member, k_s = F_est/(4 Δ) with F_est the estimate of section 4 and Δ = 4 mm, loaded to D = 9 mm, lets every member yield at the same share of the largest level. For 16 held-out members and five or six levels each (90 pairs inside the range the network was trained on), the exact end displacement under the new spring was taken, then the level of the old problem with the same exact end displacement, then the network's ray at that level, read under both springs.

| | Old spring to new |
|---|---|
| e/(D - e) | to 0.35 to 0.96 of its value, median 0.69 |
| Condensed judged error, new minus old | median 0.15 percentage points, 90th percentile 0.96, largest 9.4 |
| Condensed reading, 90 pairs: median; 90th percentile; above 10% | 4.64%; 19.8%; 17 to 4.41%; 17.8%; 17 |

- The largest difference is in `eval_0043` near its knee, where s changes fast with e.
- The same on all 64 members at seven levels of the new loading (`respring_eval64.py`): of 448 pairs, 428 lie inside the trained range, and their condensed reading is 1.79%, 8.97% and 35 pairs under the new spring and 1.81%, 9.43% and 42 pairs under the old one at the same end displacements. The other 20 pairs, the largest level of the strong members, lie beyond 8 mm of the old problem and could not be read. Against the 56 pairs of the old levels, the gain comes from the levels, which read the weak members less deeply (to end displacements of 4.6 to 5.2 mm, against up to 6.8 mm), not from the spring.
- A first-order projection made before this check (`project_rule.py`) had assumed that a softer spring leaves the error of the end displacement as it is, and promised a 90th percentile of 7.3% for the raw reading. Point 5 and the check show that assumption to be wrong.

## 7. Fits to single training members

From the host's seed 2 model, one training member alone was trained for 600 or 1,200 steps with a new AdamW at 10⁻⁴ (`dev/overfit_dev.py`, `dev/overfit2_dev.py`). The judged error is taken against an interpolant through the origin and the member's seven exact points only, so it is rough near the knee (`overfit_curve.py`, `overfit2_summary.py`). The loss on the condensed field is the mean of ln Π of the condensed fields plus a quarter of the gate's loss on the raw fields and on the field at 0.1 mm.

Judged error at 4, 6 and 8 mm. Where a range of steps is given, the value is the median of the last five readings.

| Member | Loss | Reading | Start | End |
|---|---|---|---|---|
| `train_0081`, mode 1 | the gate's, 600 steps | raw | 20.9%; 43.4%; 65.5% | 1.9%; 17.3%; 35.9% |
| | | condensed | 8.0%; 8.0%; 12.2% | 2.0%; 3.2%; 5.8% |
| | on the condensed field, 600 steps (first round) | condensed | 8.0%; 8.0%; 12.2% | 2.3%; 3.3%; 5.3% at step 500 |
| `train_0391`, mode 1 | on the condensed field, 600 steps | raw | 3.8%; 5.3%; 16.8% | -0.2%; 6.0%; 19.5% |
| | | condensed | 5.3%; 5.7%; 10.9% | 2.5%; 3.1%; 6.4% |
| `train_0033`, web | the gate's, 600 steps (first round) | raw | 40.5%; 59.6%; 71.4% | 20.6%; 40.3%; 56.9% at step 600 |
| | on the condensed field, 1,200 steps | raw | 40.5%; 59.6%; 71.4% | 47.7%; 112.7%; 164.9% |
| | | condensed | 23.9%; 39.8%; 64.2% | 4.1%; 4.9%; 9.3%, with readings up to 8.2%; 18.4%; 24.2% among the last five |

- **The gate's loss converges slowly in the amplitude.** In 600 steps on `train_0081` alone the energy gap at 8 mm fell from 11.5% to 3.9% and the raw judged error only to 36%: an error of the amplitude is of second order in the energy and is magnified in the judged error.
- **For the mode 1 members the condensed reading does the work**; a loss on the condensed field adds nothing beyond the scatter of the readings (4.4% to 7.1% among the last five of the first row's condensed reading). It also lets the raw field drift: the raw reading of `train_0391` did not improve.
- **The web member is fitted only with a large amplitude and not steadily.** Its condensed reading at 8 mm came below 10% after 650 steps, with amplitudes of 1.7 to 2.3 at 4 to 8 mm and the network's own field shrunk to about half (raw end-displacement error -54%), and 4 of the 10 readings after step 700 were above 10% again, at 19% to 25%. In the first round, with the amplitude kept below 1.6, the same member stopped at 28%.
- In the first round the three secant steps of that version did not always converge: the condensed reading of `train_0081` at 8 mm is 5.3% at step 500 and 13.2% at step 600. The second round's solve left 3 of 441 readings short of its tolerance, none at a bound.
- Training only on levels of 3 mm and more (first round) lowered the tail faster (40% at 8 mm for `train_0033`) and spoiled the small levels (-56% at 0.5 mm).

## 8. Ten more epochs for the host's seed 2 model

The host's seed 2 model was trained on the 512 training members for 10 more epochs with the recipe: 100 steps of warm-up to 10⁻⁴, held to the end of epoch 8, then half a cosine to zero (`dev/finetune_dev.py`, `l5_summary.py`). Three variants: (a) the gate's loss and sampling; (b) the gate's loss with D drawn uniformly; (c) the loss on the condensed field of section 7 with D drawn uniformly.

| After epoch | (a): raw; condensed | (b): raw; condensed | (c): raw; condensed |
|---|---|---|---|
| 0 | 2.41%, 18.56%, 74; 1.64%, 11.35%, 56 | the same | the same |
| 2 | 3.69%, 22.25%, 101; 2.08%, 13.97%, 80 | 2.84%, 19.69%, 81; 2.46%, 13.27%, 78 | 3.12%, 23.36%, 103; 2.71%, 12.44%, 78 |
| 8 | 2.38%, 18.33%, 75; 3.24%, 15.23%, 77 | 2.91%, 18.89%, 79; 2.51%, 13.11%, 68 | 3.56%, 24.32%, 104; 1.99%, 14.23%, 80 |
| 10 | 2.41%, 18.02%, 68; 1.60%, 10.08%, 47 | 2.54%, 17.54%, 66; 1.70%, 9.99%, 45 | 3.03%, 25.27%, 101; 1.67%, 9.91%, 44 |

- The host's model had been annealed to a learning rate of zero; 10⁻⁴ warms it up again and the readings get worse until the rate comes down. Only epoch 10 counts.
- **At epoch 10 the three variants are at the threshold of C2**, between 9.91% and 10.08%, with C1 at 1.6% to 1.7%. In the raw reading the gain is small (74 pairs to 66 and 68), and variant (c) is worse than the start.
- **The pairs above 10% under the condensed reading are the same in all three**: 43 pairs, all above 10% at the start as well, in 18 members: 26 pairs in 10 web members, 16 in 7 mode 1 members and 1 in a mode 2 member. Every one is too stiff. The worst are `eval_0043` (52.7%), `eval_0010` (37.4%), `eval_0014` (35.8%) and `eval_0038` (32.7%).
- The variants differ by one to three pairs, with one run each: no effect of the uniform sampling or of the loss on the condensed field can be read from them. Variant (c) took 5 h 50 min of training against 1 h 1 min for (b).
- No collapse; 3 to 6 bursts of at most 16 times, 73 to 80 steps capped. The amplitudes of the readings lie between 0.90 and 1.42, none at a bound.

## 9. A reading with seven amplitudes

The condensed reading moves the field along one ray. Here the member's own fields at the seven judged levels, each less z_0, span a subspace, and the energy at each level is minimised over the seven coefficients by L-BFGS with 60 evaluations, starting from the raw field (`subspace_eval.py`, `subspace_summary.py`). The ray lies in the subspace, so an exact minimum cannot lie above the condensed one. No reference solution enters.

| Model | Pairs | Raw | Condensed | Seven amplitudes |
|---|---|---|---|---|
| Variant (a) of section 8 after epoch 10 | all 448 | 2.41%, 18.02%, 68 | 1.60%, 10.08%, 47 | 1.47%, 8.59%, 34 |
| The host's seed 2 model | the 126 of the 18 members of section 8 | 58 above 10% | 49 | 39 |

- By mechanism, pairs above 10%, condensed to seven amplitudes: mode 1 members 18 to 9, web members 28 to 24, in the first row; 19 to 9 and 29 to 29 in the second. The subspace of the network's own fields holds a better field for the mode 1 members and not for the web members.
- No pair of the first row crossed 10% upwards; one of the second did (`eval_0001` at 6 mm).
- On the pairs above 10% the median energy gap fell from 8.26% to 6.00% (first row).

## 10. The recipe at full length

Seeds 0 and 1 with the recipe were run on from their 30 epochs to the 200 of G-C2.1's schedule, 102,400 steps each, at 0.38 s a step when the machine was idle (`dev/train_dev2.py`; `l3_summary.py`). The runs are `L2_recipe_s0` and `L2_recipe_s1` continued; their records at 200 epochs are under `records/gpu/L3_recipe_s0_e200` and `records/gpu/L6_recipe_s1_e200`. The run of seed 1 was stopped twice so that the machine could be used, after epochs 37 and 143, and resumed from its last checkpoint, which holds the random states and the cap's window; the epoch under way at each stop was run again.

**Training.** No collapse in either run. From step 512 on the latents' relative variance has a median of 0.94 in both and ends at 0.93 and 0.92.

| Epochs | Seed 0: bursts (largest) | Seed 0: steps capped | Seed 1: bursts (largest) | Seed 1: steps capped |
|---|---|---|---|---|
| 1 to 30 | 13 (163 times) | 45 | 11 (220 times) | 40 |
| 31 to 60 | 1 (15 times) | 105 | 4 (19 times) | 74 |
| 61 to 100 | 3 (11 times) | 290 | 4 (27 times) | 281 |
| 101 to 150 | 48 (19 times) | 694 | 18 (17 times) | 525 |
| 151 to 200 | 112 (23 times) | 953 | 76 (32 times) | 776 |

Mean loss over blocks of epochs, against the host's runs of G-C2.1:

| Epochs | Seed 0, recipe | Seed 1, recipe | Host seed 0 | Host seed 1 | Host seed 2 |
|---|---|---|---|---|---|
| 1 to 10 | 10.5768 | 10.5550 | 10.5988 | 10.5638 | 10.5718 |
| 21 to 30 | 10.4944 | 10.5038 | 10.6181 | 10.5795 | 10.4954 |
| 61 to 100 | 10.4302 | 10.4150 | 10.6314 | 10.4437 | 10.4286 |
| 151 to 180 | 10.3679 | 10.3683 | 10.6365 | 10.3864 | 10.3746 |
| 191 to 200 | 10.3714 | 10.3440 | 10.6456 | 10.3591 | 10.3762 |

- Each run draws what the host's run of its seed drew. The run of seed 0 has the lower loss in 197 of the 200 epochs, by 0.27 over the last ten; the host's seed 0 stayed at the starting field's loss.
- The run of seed 1 has the lower loss in 196 of the 200 epochs, by 0.08 over epochs 11 to 30 and by 0.015 over the last ten. The host's seed 1 collapsed in its fourteenth epoch and had recovered by about epoch 40 (`../c2_diag/RESULTS.md`).
- The bursts late in the runs are many and small: 160 of the 177 of seed 0 and 94 of the 113 of seed 1 fall in epochs 101 to 200, none above 32 times.

**Reading** (`dev/eval_state.py`), as median; 90th percentile; pairs above 10%:

| Pairs | Number | Seed 0, raw | Seed 0, condensed | Seed 1, raw | Seed 1, condensed |
|---|---|---|---|---|---|
| All | 448 | 1.42%; 7.27%; 35 | 0.84%; 3.00%; 2 | 1.55%; 8.03%; 38 | 0.95%; 3.22%; 5 |
| D = 4 mm | 64 | 1.41%; 5.8%; 3 | 1.31%; 2.8%; 0 | 1.59%; 7.8%; 3 | 1.47%; 3.0%; 0 |
| D = 6 mm | 64 | 1.82%; 20.2%; 12 | 1.25%; 3.5%; 0 | 1.55%; 24.8%; 12 | 1.44%; 4.4%; 1 |
| D = 8 mm | 64 | 5.76%; 44.3%; 20 | 1.52%; 5.0%; 2 | 5.98%; 48.1%; 23 | 2.02%; 6.5%; 4 |
| Mode 2 members | 105 | 1.09%; 4.7%; 2 | 0.61%; 2.2%; 1 | 1.11%; 3.7%; 1 | 0.53%; 2.2%; 1 |
| Mode 1 members | 119 | 2.02%; 25.1%; 21 | 1.61%; 4.4%; 1 | 2.10%; 23.3%; 19 | 1.62%; 4.1%; 2 |
| Web members | 224 | 1.33%; 5.1%; 12 | 0.68%; 2.3%; 0 | 1.54%; 7.8%; 18 | 0.76%; 3.4%; 2 |

- **Both readings of both models meet both criteria of G-C2.1** on these members: two seeds, development runs, no gate.
- **The raw tail is still there, and it belongs to the members.** It lies in 20 members in seed 0 and 23 in seed 1, 19 of them the same, at 4, 6 and 8 mm. All 35 and 38 pairs are too stiff, 32 pairs are above 10% in both seeds, and the worst is `eval_0026` at 8 mm in both (109% and 102%). Over the 448 pairs the raw judged errors of the two seeds have a correlation of 0.98.
- **The condensed reading removes it** but for two pairs in seed 0, `eval_0017` (12.2%) and `eval_0038` (10.8%) at 8 mm, and five in seed 1: the same two (11.4% and 11.2%), `eval_0038` at 6 mm (11.7%), and `eval_0014` (10.5%) and `eval_0043` (15.3%) at 8 mm.
- The amplitudes lie between 0.91 and 1.21 in seed 0 and between 0.89 and 1.19 in seed 1, none at a bound; 11 and 7 of the 448 solves ended short of their tolerance, with relative slopes below 6 × 10⁻⁴.
- The energy gap of seed 0 is below that of the host's seed 2 model at every level: in the median 0.066% against 0.150% at 0.5 mm, 0.20% against 0.29% at 3 mm, 0.57% against 1.91% at 6 mm and 1.04% against 3.25% at 8 mm. That of seed 1 is 0.072%, 0.21%, 0.70% and 1.12% at those levels.
- **The loss says little about the tail.** On the same draws the recipe run of seed 1 ends 0.015 below the host's run in loss, and reads 1.55% and 8.03% where the host's run read 6.61% and 31.16%.

**Checks made on seed 0 because the result was better than expected.**
- The predictions that the training script itself wrote at its end, read by another route than the reading script, give the same raw figures, pair by pair within 4 × 10⁻⁷.
- The energy gaps of four members, computed again with the float64 reference code and the gate's labels, equal the stored ones.
- The training draws from the 512 members marked for training in the manifest and from no others.

For seed 1 the first of these checks was made again (`second_route.py`): the predictions written at the end of the run, read with the float64 reference code, give 1.55%, 8.03% and 38 pairs, pair by pair within 5 × 10⁻⁷ of the reading script's rows.

## 11. Reading

**Shown.**
- The tail of G-C2.1 is an error of the end displacement, magnified where the member is weak against the spring, and present on the training members as on the held-out ones.
- A reading that sets one amplitude by the energy removes the part of it that the energy barely sees. What is left is how much too stiff the network's field is, which no choice of spring changes.
- On this GPU the recipe took two seeds through the whole schedule without a collapse, and four seeds through its first 30 epochs.
- The two models that came out of the full runs meet G-C2.1's two criteria on G-C2.1's held-out members under either reading.

**Not shown.**
- **Whether seeds 0 and 1 are typical.** Two full-length runs with the recipe had ended when this was written. On the same draws without the recipe, the host's seed 0 collapsed for good and its seed 1 collapsed and recovered to a reading of 6.61% and 31.16%; with it both are within the criteria. That models trained with the recipe are in general better than the host's seed 2 has these two examples.
- **Whether the recipe is needed for the quality, or only against collapses.** There is no full-length run without the recipe on this GPU.
- **How any of this does on unseen members.** Every reading above is on members that were read while the method was chosen.
- **What the recipe does late in training.** The bursts and capped steps grow in number as the learning rate falls; that they are harmless is read from the loss and the variance only.
- **Why the web members of the host's seed 2 model resist** the condensed reading, further training and the seven amplitudes, while those of the two full-length recipe models have none and two pairs above 10%.
- Sections 7 to 9 rest on single runs, single members or one model, with settings (10⁻⁴, 600 steps, 10 epochs) that were not tuned.

**Kept in reserve, not adopted.** The further training of section 8, the seven amplitudes of section 9, the spring scaled to each member, and a loss on the condensed field.

## 12. Files

**Folders the scripts need** are named in `paths.py`, by environment variables: the stamped tree (`C2DEV_JOINT`, `C2DEV_SRC`), the instances (`C2DEV_DATA`), the host's states (`C2DEV_STATES`). The return package, the records and the runs default to this repository's folders. The scripts are the ones that ran, with their hard-coded folders replaced by `paths.py`; `magnification.py`, `draws_check.py` and `second_route.py` were written for this note. The scripts in `dev/` are byte for byte the ones that ran on the GPU.

**GPU scripts** (`dev/`), run in a working folder that holds `dev/`, the stamped tree as `code/joint` and `code/repo`, the instances as `data/`, the host's seed 2 state as `states/label_free_s2/state.pt`, and `eval_ref.json`:
- `train_dev.py`: section 5. `train_dev2.py`: the same with a continuation of a finished run and snapshots, section 10.
- `overfit_dev.py`, `overfit2_dev.py`: section 7, first and second round.
- `finetune_dev.py`: section 8.
- `condense.py`: the amplitude's solve. `evalcond.py`, `eval_state.py`: the two readings of a model and their judging against `eval_ref.json`.

```
python -I dev/train_dev.py --name L1_control_s0 --seed 0 --recipe none --epochs 15 --stop-on-collapse
python -I dev/train_dev.py --name L2_recipe_s0 --seed 0 --recipe cap+beta2 --epochs 30 --stop-on-collapse
python -I dev/train_dev2.py --name L2_recipe_s0 --seed 0 --recipe cap+beta2 --epochs 200 --stop-on-collapse --after-collapse 2560 --extend --snapshots 60,100,150
python -I dev/eval_state.py --name L3_recipe_s0_e200 --state runs/L2_recipe_s0/final_state.pt --fields
python -I dev/train_dev2.py --name L2_recipe_s1 --seed 1 --recipe cap+beta2 --epochs 200 --stop-on-collapse --after-collapse 2560 --extend --snapshots 60,100,150
python -I dev/eval_state.py --name L6_recipe_s1_e200 --state runs/L2_recipe_s1/final_state.pt --fields
```

**CPU scripts** (this folder):
- Section 2: `gen_eval.py` (the held-out and tested instances again, no solve), `common.py`, `refcurve.py`, `a1_readings.py`, `a2_secant.py`, `a3_linesearch.py`, `a3_final.py`, `a3_summary.py`, `timing.py` (one field and one exact solve against the host's records), `magnification.py`.
- Section 3: `select_members.py`, `label_members.py`, `predict_states.py`, `compare.py`.
- Section 4: `rule_explore3.py`. Section 6: `condense_eval.py`, `condense_summary.py`, `rule_v0.py`, `respring_eval.py`, `respring_eval64.py`, `respring_summary.py`, `project_rule.py`.
- Summaries of the GPU runs: `analyse_run.py`, `runs_compare.py`, `probes_summary.py`, `draws_check.py` (section 5); `overfit_summary.py`, `overfit_curve.py`, `overfit2_summary.py` (section 7); `l5_summary.py` (section 8); `l3_summary.py`, for either seed, and `second_route.py` (section 10).
- Section 9: `subspace_eval.py` (with `--base` the GPU working folder), `subspace_summary.py`. `make_eval_ref.py` writes `records/eval_ref.json`.

**Records** (`records/`):
- `logs/`: the printouts of the summary scripts, from which the figures of this note are taken.
- `eval_ref.json`, `fit4.json`, `selection.json`; `labels/`: the exact end displacements, forces, energies and bolt forces of the 24 training members of section 3, without their fields; `out/`: the rows of section 3 and the solve log.
- `cond/`, `proj/`, `proj64/`: the rows of section 6, pair by pair. `tail/`: the line searches of section 2. `sub/`: the rows of section 9.
- `gpu/`: from the GPU working folder's `runs/`: each run's `summary.json`; the step record of `L1_control_s0`; the records of the single-member fits; the readings of section 8 at epochs 0, 2, 5, 8 and 10; `eval/L3_recipe_s0_e200.json` and `eval/L6_recipe_s1_e200.json`, the readings of section 10. `L2_recipe_s0` and `L2_recipe_s1` hold the summaries at 30 epochs, `L3_recipe_s0_e200` and `L6_recipe_s1_e200` those of the same two runs at 200.
- In four records the path of the model state, which named a folder of the machine, was shortened to a relative one. Twenty text records under `gpu/` were written on Windows with its line endings and are stored with Unix line endings. Nothing else in a record was changed.
- Not kept: the model states (27 MB and 82 MB each), the fields, the step records of the other runs (2 to 27 MB), the predictions of section 3, and `tail/a1_rows.json` (1.4 MB), which `a1_readings.py` writes in seconds. `probes_summary.py`, `analyse_run.py` and the probe line of `l3_summary.py` need step records that are not kept, and `second_route.py` needs the predictions of a run; their printouts are in `logs/` (`l3_summary.log` and `l6_summary.log` for the two seeds of section 10, `l6_second_route.log`).

The summaries, run in this folder:

```
python -I magnification.py
python -I draws_check.py
python -I runs_compare.py
python -I condense_summary.py
python -I respring_summary.py records/proj
python -I respring_summary.py records/proj64
python -I overfit_summary.py
python -I overfit_curve.py
python -I overfit2_summary.py records/gpu/overfit2/train_0081_plain_rc.jsonl records/gpu/overfit2/train_0391_cond.jsonl records/gpu/overfit2/train_0033_cond.jsonl
python -I l5_summary.py records/gpu records/eval_ref.json
python -I subspace_summary.py records/sub/L5a_e10_gate.json records/gpu/L5a_plain_sqrt/eval_e10.json
python -I subspace_summary.py records/sub/hosts2_gate.json records/gpu/L5a_plain_sqrt/eval_e0.json
```

`condense_summary.py`, `respring_summary.py`, `rule_v0.py`, `rule_explore3.py`, `refcurve.py`, `a1_readings.py` and `a3_final.py` also read the members' parameters from the instances' manifest (`C2DEV_DATA`) and import the stamped tree (`C2DEV_JOINT`).
