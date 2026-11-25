# Trial of a field underneath on the CHS splice family: plan fixed before the run

25 November 2026. Exploratory, one seed, not a gate. Nothing here is stamped. The plan is written before the run is
started; the run's files and this text are kept together.

## Question

On the family's mesh, the plain recipe (preset `fam128_bending_e400`, 400 epochs) followed by a second cycle of 200
epochs reaches a median error of 0.99 % and a 90th percentile of 3.69 % on the 31 members of the development. Most
of that budget goes into what a much cheaper run on the tiny mesh already holds. Does a network on the family's
mesh that only corrects the carried field of a finished tiny-mesh network reach the same two numbers within 150
epochs?

## What is run

One training run, preset `fam128_bending_under_e150`, seed 0, on the family's mesh, with the 128 training members
of the earlier runs, and its evaluation.

- The field underneath. For each member and each device rotation of a step, the finished tiny-mesh network (run
  `fam128_bending_e400` with the tiny mesh, seed 0, 400 epochs, 51,200 steps, of 21 November 2026; its configuration
  hash is a56eabfb...3812) gives its field on the member's tiny mesh. The change of that field from the tiny mesh's
  preload state is carried to the family's mesh and added to the family mesh's own preload state
  (`f2/prolong.py`, `f2.train.carried`, `f2.train.under_field`): displacements are evaluated at the family mesh's
  nodes with the tiny mesh's shape functions, part by part; the heads' unknowns, w0 and theta are copied; unknowns
  that the model combines with others (a head's separation, a root's opening) are set so that the physical
  displacements are the interpolated ones; contact unknowns are kept non-negative. The tiny-mesh network is not
  trained further. No exact solution of any training member is used; the two preload states are part of every
  member's export.
- The network. Sizes, optimiser, rate (1e-3, linear warm-up over the first 5 % of steps, cosine decay), four device
  rotations a step drawn as before, loss (mean of log Pi) and inner Newton steps are those of
  `fam128_bending_e400`. Its outputs are a correction to the field underneath (`f2.model.field`): with zero outputs,
  as the last layers start, the field is the one underneath, except that a contact closed underneath starts
  open by s T softplus(-2), about one micrometre at the largest rotations. 150 epochs, 19,200 steps.
- Snapshots (raw reading, 31 members, seven levels) before the first step and after epochs 5, 10, 20, 30, 40, 60,
  80, 100, 125 and 150.
- Evaluation as for the earlier runs: the 31 members (4 tested, 16 random, 11 chosen), seven levels, the condensed
  reading, the moment at the same joint rotation (`abs_curveD_err`).

The configuration hash of the preset is in the run's history; the hash of the tiny-mesh state file is written there
by the run (`under`), together with the report of the first member's transfer.

## Values the trial is compared with (from the records, fixed)

All 31 members, seven levels (217 points), condensed reading, per cent:

| run | epochs on the family's mesh | median | 90th percentile | largest |
|---|---|---|---|---|
| first cycle (`fam128_bending_e400`, seed 0) | 400 | 1.5312 | 5.3943 | 67.9 |
| control: second cycle of 22 November 2026 (`fam128_bending_more`, seed 0) | 600 | 0.9878 | 3.6862 | 56.9 |

## Outcome classes (fixed before the run)

- A: the trial's median is at most 0.9878 and its 90th percentile at most 3.6862 (the values as the verdict script
  computes them from the control's evaluation, unrounded). The carried field saves three quarters of the steps on
  the family's mesh at this accuracy.
- B: not A, and the median is at most 1.5312 and the 90th percentile at most 5.3943: 150 epochs give what 400
  epochs of the plain recipe gave.
- C: otherwise.

The class is read from the final evaluation only. It holds for this seed, these 31 members and this tiny-mesh
network; it is not a statement about fresh members or about a gate. The script is `under_verdict.py` (kept with the
trial's records, sha256 334f34f1...7e53); its three branches were tried with made-up files.

## Reported outside the rule

- The snapshots' trajectory beside those of the two earlier runs on the same mesh and of the tiny mesh, with the
  epoch at which the trial first has the control's raw values; the snapshot before the first step is the carried
  field itself (with the contacts' small opening).
- Seconds an epoch (the tiny network's forward pass and the transfer are extra work in every step; the plain recipe
  took 85.6 s on the same GPU model), peak memory, cap events.
- Largest member error, thin plates at the last level, medians by level, the two lowest levels, the random 16, the
  raw reading, as in the trial of 24 November 2026.
- The time ledger: tiny run (2.6 h) plus this run against the 14.3 h of the control, on the same GPU model only.

## What was checked beforehand (a sandbox processor, 25 November 2026)

- Member B-13 (nominal), tiny mesh 2,543 nodes, family's mesh 8,632 nodes: 1,466 nodes of the family's mesh lie on
  tiny-mesh nodes; 750 take a tiny element's functions continued beyond it, by at most 1.009 in local coordinates
  (the two meshes shape the bolt holes differently, and curved faces are cut differently); 6 nodes beyond the
  fillet's sloping face take the nearest point of an element, at most 0.25 mm away. A mesh onto itself is the
  identity; a linear displacement is reproduced at all but the 6 nodes.
- Energy of carried fields of B-13 over the family mesh's exact energy at the seven levels, per cent:
  the tiny mesh's exact solution, whole field carried, 33.4 22.9 12.7 9.6 9.1 12.1 25.2; the same with the change
  from the preload state carried, 1.7 3.2 4.8 5.6 6.4 10.4 23.8; a tiny-mesh network of another preset trained for
  200 epochs on a laptop, change carried, 3.39 4.15 5.29 5.87 6.74 9.93 15.45, with moment errors of 1.6 1.4
  1.1 1.1 1.2 4.9 13.3 (that network's own error at the last level is 7.8 on its mesh). The two meshes' exact solutions
  differ by 1.2 1.3 1.0 0.9 1.1 3.3 5.1 in the moment. At the last level two thirds of the excess is in the
  plate, which has one element through its thickness on the tiny mesh.
- Without a field underneath the field function gives the earlier values bit for bit; the 89 earlier presets keep
  their configuration hashes; the code's tests pass, with six new ones for the transfer and the new option.

## Cost

150 epochs of about 88 s, 3.7 h; snapshots and predictions about 0.3 h; evaluation about 0.2 h: about 4.2 h on the
RTX PRO 6000, about 42 compute units. One session.

## Not part of this trial

No variant is run before this run is read: no other starting weights of the correcting network, no other rate or
map, no change of the draws of the rotations, no extra members. What follows the trial is decided after it is read.
