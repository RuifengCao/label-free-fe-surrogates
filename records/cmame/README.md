# records/cmame -- cmame-paper records

## Default path against wp8-lejepa (Stage 2, run again at Stages 9, 11, 12 and 14)

Stage 2 changed `src` (opt-in additions only: the stiffness-norm loss of the
supervised trainer, its E8 row, an E8 run that trains a supervised grid beside
reused label-free states, and their step count), and
`scripts/regress_against_branch.py` ran in the sandbox on 6 October 2026 (CPU,
one thread, each side in its own process importing its own source tree; a
fresh pass and a restart pass) with this side's `src` = tree
`2da09d0593669f50149f4fb546c01861ac0d5149`, the code CM2D ran.

Stage 9 changed `src` again: `fe/tet3d.py`'s structured tetrahedral mesh, which
split each hexahedral cell into five tetrahedra covering 5/6 of it, now uses
the conforming six-tetrahedron Kuhn split (no run reported in the manuscript
and no record here used this mesh; only the three WP7-S1 smoke configurations,
`scripts/bench3d_scale.py` and `scripts/amp_compile_check.py` did). The
regression ran again in the sandbox on 10 October 2026, with the same library
versions, on the same two miniatures as `records/wp9/`;
`regression_wp8_e1_2d_base.json` and `regression_wp8_phase2b.json` are now its
summaries, identical to Stage 2's apart from this side's tree. Stage 11 added
two modules that no run imports (`fejepa.analysis.holdout` and
`fejepa.analysis.adjudicate_holdout`, PREREG_HOLDOUT's evaluation and
adjudication); the regression ran again on 14 October 2026 in the same way,
with the same result (Stage 9's tree was `7cc8ac1b6b16673f14609a422f7e95479d968df0`;
the runs took 60 s and 147 s). Stage 12 (PREREG_K3D) changed `src` in two
places, both taken from wp9-pool Stage 2 (PREREG_FINE3D r5): the supervised
trainer keeps the loss of the last step of every epoch (`history`, carried
across a resume, returned with its result), and `load_epoch_checkpoint` moves
aside an epoch checkpoint it cannot read and stops on one it can read but not
restore (it had deleted both); the regression ran again on 20 October 2026 in
the same way, with the same result (Stage 11's tree was
`b719ea99d4063cf01fd183395745e0e87eba9591`). Stage 14 added a module that
nothing else in `src` imports (`fejepa.analysis.ritz`, the construction of
the Ritz baseline and of the enriched c* reading, which Stage 14's three
scripts import); the regression ran again on 27 October 2026 in the same
way, with the same result (Stage 12's tree was
`165e8bf6b591614ee6a7edb850a83058e4f420ad`; the runs took 50 s and 119 s):

| | source tree (`git rev-parse <commit>:src`) |
|---|---|
| this side | the Stage 14 code: `src` = tree `8c3fefb087423e65bef8e064d2cd2873aef2f5ab` |
| the other side | `wp8-lejepa` at `5f8e2df`: `src` = tree `5be6357b912cad058121092f274e6a322169b9f6` |

- `regression_wp8_e1_2d_base.json`: a miniature of `configs/e1_2d_base.json`
  (E1's stamped base) -- 162 numbers and 2 state files, identical (0
  differences; every state file byte-identical).
- `regression_wp8_phase2b.json`: a miniature of `configs/phase2b_v1.json` (E8
  with labels, labels_anchor, AR and MGN; P3; WP6; E6; gate G2) -- 2,590
  numbers and 6 state files, identical.

The two summaries equal `records/wp9/`'s except for this side's tree (wp9's
ran the Stage 0c code, tree `710ccb32...`). Each run took a few minutes (Stage
9: 43 s and 100 s). `tests/test_w9_records.py` checks
that a committed `src` without local changes is the tree named by the newest
regression record (this file on this branch): a change to `src` needs the
regression run again and this table updated. The miniatures exercise the
default paths only; the new opt-in paths are covered by
`tests/test_cm2d_training.py`. Bitwise identity is a same-machine,
same-library statement (sandbox: Python 3.11.15, torch 2.14.0+cu130 on CPU,
numpy 2.4.4, scipy 1.17.1).

## The decision rule's operating characteristics and the run's wall time (PREREG_CM2D Sec. 4, 7)

`cm2d_sims.json`: `scripts/cm2d_sims.py` (fixed seed; seconds), the source of
every simulated number PREREG_CM2D quotes. The E-series noise guard on three
seeds per arm with log-normal per-seed values: false and true "lower" and
"worse" readings at equal and unequal seed spreads (`cells`), with the
reference at July's labels-only spread in the relative energy gap, 9%
(`july_reference`), and with per-instance blow-ups (one validation instance
at 20-40 times an arm's level, about one per seed) in one arm or both
(`blowups`); and, from cmame-paper Stage 5 (PREREG_CM2D r3), with the
reference at that row's spread in the von Mises error, 7.1%
(`july_reference_vm`), drawn after all the others so that every earlier value
is unchanged. `schedule`: the 30 units of `configs/cm2d_v1.json` in the order
the run submits them on three workers, at the measured 52 ms per supervised
step plus a minute per unit, for the graph network's (unmeasured) step at
0.5-3 times the transformer's (2.5 and 3 added in Stage 5). The script
regenerates the file byte for byte (`--check`; tested).

## A functional check of the stiffness-norm loss (PREREG_CM2D Sec. 4)

`cm2d_funccheck.json`: `scripts/cm2d_funccheck.py`, run in the sandbox on 7
October 2026 (CPU, one thread; about 15 minutes) with the Stage 2 code (`src`
tree `2da09d05...`), before PREREG_CM2D's stamp. 72 instances of the 2D
training family drawn by the gmsh generator with its own seed (777; not E1's
corpus), 48 for training and 24 for validation; a transformer of width 32 and
depth 2 trained for 25 epochs with L_D, with L_K and with the label-free
objective, seeds 0 and 1. Recorded per loss and seed: the metric suite, the
gradient norms before clipping and the share of clipped steps; and the L_K
value the trainer computes against Lemma 1 over 200 steps. PREREG_CM2D Sec. 4
quotes its energy gaps and von Mises errors (tested); it is not evidence for
any of PREREG_CM2D's hypotheses. The record carries the script's SHA-256 and
the tree of the `src` it ran (named only when `src` had no local changes);
rerunning the script on the same machine and library versions gives the same
numbers apart from the wall-clock seconds.

## Sec. A return: inference timing and field export (8 October 2026)

`timing/` holds RUNBOOK_CMAME Sec. A as it ran on the box (RTX 5090, driver
595.71.05, torch 2.12.1+cu130, Python 3.12.3; a 16-CPU allotment of a
two-socket Xeon Gold 6459C host) on commit `61f018f` (tree
`ec2ecbf2057f28a97a94b1fe867ad2c9eb89a4ca`, clean), copied byte for byte
from `cmame_timing_return_20261008.tgz`
(SHA-256 `81d6f079bd271691c3b2474e3434d8a59f06aeae7072b840e15fe06836f79523`,
as the operator sent it and as recomputed on receipt). The suite there: 505
passed, 2 deselected (the two LaTeX compile tests).

| file | SHA-256 |
|---|---|
| `fields/energies_val.npz` | `504498e4030ef2645166baf2cf7cc12633272245bd638ed97dcd4d8a954c5297` |
| `fields/fields.json` | `c25bc4507639ced8158cf327b248a29a82c4078cfe2dd51a639b3e0ec65f1583` |
| `fields/fig5.npz` | `594556cc327987e17083a1fb967a53dbe3b6736679f7746d032385d852c5a4a5` |
| `fields/fig6.npz` | `b4ffede43f0029882da911d3da102e225e468679f20c9700fbdd4255a646771e` |
| `fields/fig7.npz` | `241fd0d22dc2b2040661d84227d952bfdad027ccd2cc3a785c641504107c484c` |
| `fields_3d.log` | `d7add2c407fa9adf47576387b97e89f032ced142efc34213604dc60b8f0bf2dc` |
| `machine.txt` | `2789deea33efcbedacbd75c449969f5ab6bf6386a5f76f5131f809256297fda0` |
| `precheck.txt` | `0bd95b80755017f80a0495437677a22e28a2847a6314d2339da393f2bfa91359` |
| `pytest.log` | `127543191e7db8581ba7a07fffd0cb6de79455d8074823fdd227a25f3d4c53f8` |
| `status.txt` | `f4f1843700b60f100953be2ced1b05e59966a7cd1be169674d1a4ad845e3b8ae` |
| `timing_2d.json` | `573543b13c54e85e1eaa275abef878f38c42c6590dc1e17035004aac62914997` |
| `timing_2d.log` | `2d33b63c7bf2ae6162afc6c368ae0160627d058ea0bf04446f53614e6abba13b` |
| `timing_3d.json` | `8eb5e4f506ca9c9864b297e02a372cbd1dccea795b1155fcf14066f7d1b1e871` |
| `timing_3d.log` | `02fdd2bcb822b72bbb94d18c6d28df0d0e33ee0a7de39c117021683c343bfe23` |

- `timing_2d.json`, `timing_3d.json` and their logs:
  `scripts/time_inference_vs_solve.py` on 32 validation instances of E1's 2D
  corpus with E1's label-free state of seed 0, and on 32 validation and 8
  fine-mesh instances of Phase-2b's 3D corpus with Phase-2b's label-free
  state of seed 0. Per instance: the surrogate's inference on the GPU (first
  and warm call) against, on the CPU, a direct solve and conjugate gradients
  from zero, from the prediction, and from zero until they are as accurate in
  the energy norm as the prediction or as the prediction rescaled by c* (a
  stop decided by the labels, so a lower bound), assembly and archive
  reading excluded.
- `fields/`: `scripts/export_fields.py` on Phase-2b's nine states of the
  1,024-instance budget (label-free, trained without labels; labels only;
  graph network; seeds 0-2): the per-load energies and error measures of the
  256 validation instances (`energies_val.npz`), the counts, checks and
  diagnostics (`fields.json`), and the three figure files (`fig5.npz`,
  `fig6.npz`, `fig7.npz`: validation instances 107 and 154, fine-set
  instance 77, chosen by the rules `fields.json` records).
- `status.txt` (the three steps, exit 0), `machine.txt`, `precheck.txt`
  (the GPU idle and no other run before the timing) and `pytest.log`.

`tests/test_cmame_timing_records.py` checks that:
- the files are these; the reports the steps read, which carry their
  configurations, are the committed records; and the states they evaluated
  are the runs' own: the label-free ones those the reports record
  (`d9_restart`), the supervised ones those of
  `records/wp9/phase2_supervised_states.json`;
- every solver solved every instance, and no conjugate-gradient solve fell
  back to the direct one; the direct solutions agree with the stored labels
  to round-off and the full conjugate-gradient ones to within 1e-8 (observed
  below 1e-11); every matching solve met its target; and the timed model
  reproduces its report's five per-instance arrays on every timed instance
  (the fine ones against the report's transfer arrays);
- the field export used all nine states and left none out, and its
  diagnostics lie in the runbook's ranges;
- its counts agree with the manuscript's numbers, which come from other
  records: instance-seed pairs whose mean relative energy gap exceeds 1
  (label-free 0, labels only 18, graph network 28 of 768) and label-free
  load cases with a relative energy gap above 1 (1 of 3,072);
- on every load case of every network and seed in `energies_val.npz`, the
  relative energy gap, computed from the energies, equals the squared
  relative energy-norm error, computed from the error (Lemma "Exactness");
  the energy is positive exactly when that error exceeds the zero field's,
  and the energies of two networks for the same load case rank them as
  their errors do (Corollary "Zero-field test and ranking"); the rescaling
  by c* never increases the gap and leaves no prediction worse than the zero
  field (Proposition "Energy-optimal amplitude"); and the volume-weighted
  von Mises error obeys the bound of Proposition "Energy gap and stress
  error";
- the per-instance means of these arrays reproduce the report's relative
  energy gaps, displacement errors and von Mises errors (the transformers'
  to round-off; the graph network's within the export's tolerance of 1e-3,
  observed median deviations below 1e-4 and largest 6.5e-4: its CUDA
  scatter reductions are not bitwise reproducible); the
  counts of `fields.json` follow from them; the figure rules, applied to the
  report's arrays, select the instances exported; and the two validation
  figures carry their instance's per-load arrays.

## The threads of the solvers: RUNBOOK_W9 Sec. 4 (11 October 2026)

`threads/` holds RUNBOOK_W9 Sec. 4 as it ran on the box on 11 October 2026,
copied byte for byte from `wp9_threads_return_20261011.tgz` (SHA-256
`cef9d17f23069ed5baa508559cd4dcaba54ab0609f07fe0dde9d0778d565ea81`, as the
operator sent it and as recomputed on receipt); branch wp9-pool commits the
same files as `records/wp9/threads/`. The cost table's timing above recorded
the threads of its environment (`OMP_NUM_THREADS` and `MKL_NUM_THREADS` 16)
but not the threads the solvers used. This return times the same direct solve
and conjugate gradients on the first 8 validation and 2 fine-mesh instances
of Phase-2b's corpus with the label-free state of seed 0, in the box's
environment, with one thread, and in the environment again, and reads the
BLAS pools that numpy and SciPy load (`scripts/blas_threads.py`). It ran on
another host than the cost table: a Xeon Platinum 8470Q with 25 CPUs
allotted and NVIDIA driver 580.95.05, where the environment sets the threads
to 25 (wp9-pool's `DEVIATIONS_W9.md`, W1 and W3).

| file | SHA-256 |
|---|---|
| `blas.txt` | `75e6e1c6c29958ba8de261e03bfcbd6734ebbb57e499031d3e4f3ed8b6ffa3d2` |
| `blas_env.log` | `36c5f0f861e8ec84fe9fc5f6a1c3d6e84fe7a4092cec46567ba64dc48b2af94e` |
| `blas_one.log` | `2857509aeb14a114e0183c5210417dfa6742a60fbac1927efa59b16268e0db5d` |
| `machine.txt` | `4436f8d70e59373d3b0790f18329fe26ea316d5933f516376971037d620fe128` |
| `precheck.txt` | `cc74ce67bac1b3053b4649d766e6e127f07255aca07ddc9632a9bdc35a528cf6` |
| `status.txt` | `7effaf50153a333b35fdc992387e8d6ede92695a9b34fd685f9a21d6d5225f57` |
| `timing_2d_env.json` | `5f77cac2c5bfc638c25f278b5beeac6aa1ff9591f39aa37094ef83e0b635eb08` |
| `timing_2d_env.log` | `8009fdbf4bc5e8b69912aac1ce3d4862b52a35f4434e7da71ab8ea325f0fa7d8` |
| `timing_2d_one.json` | `0e87c30cac6d58c2997124209de0b22459a55e5b22429b62fc87c07d9f5c5a49` |
| `timing_2d_one.log` | `93b171606edce5d0ed4856f6fc034f6856896385dd1c9d21d184b619b028b8a8` |
| `timing_3d_env.json` | `eaf238953e2cf7eb7ac127d24a6112f1b388979198ae52bccb107582e7d19c6f` |
| `timing_3d_env.log` | `44f67f1e7d44e26f9d861c326f9fc78f601b1d46a8e752797ed07db705feef0e` |
| `timing_3d_env2.json` | `38b4e98fd17c1cb864d228d9d8bb2c2cc27cf83e47eef3e2dd0870cd58bf43ef` |
| `timing_3d_env2.log` | `0370ff3fe199a27d5f7b25da74b2007d8ace6898338efe1a343df026143a3563` |
| `timing_3d_one.json` | `6d17ce7a1963303302d23423abb3d43e1660f478fe220a5f4a43b100207baa37` |
| `timing_3d_one.log` | `64a443e75405ba348121dbd33559a512eb100dfed6bf4a0db506a2d43d35d82f` |

The readings, which `scripts/make_cmame_material.py` turns into the cost
table's note on threads and `tests/test_cmame_material.py` recomputes: both
BLAS pools (two OpenBLAS builds) ran the environment's 25 threads, and 1 with
one thread; the direct solve took the same time with one thread as with 25;
conjugate gradients took less with one thread; the repeat in the environment
agreed with the first run. Every solution agreed with the stored labels, and
the timed model reproduced its report's arrays.

## B0 readiness (8 October 2026)

`cm2d_ready.log` (SHA-256 `d1ca946eee99f272e8924275329cff2634a454bf134fbdc265c304c57546a28e`):
RUNBOOK_CMAME B0 on the same commit, run after Sec. A by the operator's
account, as the operator sent it beside the tarball. Every check `ok` or
`info`, last line `GO`: E1's three states reproduced E1's report on CUDA
with largest relative deviation 0, one epoch of stiffness-norm training on
two pool instances gave a finite relative energy gap (0.995), and
PREREG_CM2D was unstamped, as it must be before the stamp. Checked by the
same test file.

## CM2D: the run of 8-9 October 2026 and its verdict (PREREG_CM2D)

`cm2d/return/` holds RUNBOOK_CMAME Sec. B as it ran on the box on the stamped
commit `094c804` (tag `prereg-cm2d`, tree
`cd3ec0c5baada05cf86eb6d12d64153d28930e10`), copied byte for byte from
`cm2d_return_20261009-1433.tgz` (SHA-256
`6cd07ef487cfab7c5d12f7d63a8f0d4887f535c495d2c04e444e29aa46ada2b6`, as the
operator sent it and as recomputed on receipt). The run started at
2026-10-08T15:24:06Z and exited 0 after one attempt; its supervised grid of
30 units took 12.8 h on three workers (16 CPUs allotted; RTX 5090, driver
595.71.05, torch 2.12.1+cu130). The suite there: 514 passed, 2 deselected.

| file | SHA-256 |
|---|---|
| `return/RESULTS.md` | `0afd779dd48c422def1cac3059ab588205b5f6deef34e8f0520e0a2419da320e` |
| `return/figure1_energy_gap.png` | `42274c7a2cc4e5a284ead107fda38a4c1ff2affe0124993bd3dccb659db24a0e` |
| `return/precheck.json.used` | `f69a8a177c8d6ffdf76679e72a3dab90fd2b8589e9f025e6071380b74b5da377` |
| `return/precheck.log.20261009-142644` | `7ed83d52a513f85d193c69926e77e1d058b26f9fdff44f4054f08a3480910e30` |
| `return/provenance.txt` | `cfc46f91c0828f21533a340ee7719462549a6e86e1e57b9640b49e203b6001ff` |
| `return/pytest.log` | `3c89394354f70ca22b45234465f944446a1d320368580095a414217622ae4a28` |
| `return/report.json` | `a72c007e1a612986af463084572f1794b574e9861cce233006534c51e1a6e5ec` |
| `return/run.log` | `75c403a76a8d6d1cdfb2ad26f6d691b85a1d80147af974cec5d86be161f06b16` |
| `return/status.txt` | `4687ec091e1ad57d59367ee8d7044d4c9742fc46630e1a396c9989cb997e5c11` |

- `report.json`, `RESULTS.md`, `figure1_energy_gap.png`: the run's outputs.
  `status.txt`: one start, exit 0. `run.log`: the run's console.
  `provenance.txt`: the commit, the tree, `git describe` (both forms
  `prereg-cm2d`), torch, the SHA-256 of the report and of the kept states
  (the states stay on the box), the GPU and the memory events (`oom_kill 0`);
  its `git status` lists one untracked file at the repository's root, the
  operator's manual of 3 September (already on the box at E1's run), which
  `git describe --dirty`, B1c and the precheck ignore by design. The
  container's hostname differs from E1's (`records/wp8/e1/provenance.txt`):
  the instance's host changed, as PREREG_CM2D Sec. 7 discloses; the GPU,
  driver and torch are E1's.
  `pytest.log`: the suite before the run. `precheck.json.used`: the GO the run
  used. `precheck.log.20261009-142644`: the log of that precheck (GO), renamed
  after the run (below).
- `cm2d/verdict.json` (SHA-256
  `008b26550dcde4880f5d1baf0e949c4d3909c7e8079807becf7a2f7d648b4db9`):
  `scripts/adjudicate_cm2d.py`, run on 9 October 2026 at the stamped commit
  in a clone of its own, with the tag fetched by a forced refspec and only
  `prereg-cm2d` pointing at that commit (RUNBOOK_CMAME Sec. C), as
  `python scripts/adjudicate_cm2d.py --return records/cmame/cm2d/return
  --e1-report records/wp8/e1/e1_2d_base/report.json --prereg PREREG_CM2D.md
  --july-report records/phase1/report_rec8_v2.json --out
  records/cmame/cm2d/verdict.json`. Run again on the same inputs, it writes
  the same file byte for byte. H1, H2a and H2b: SUPPORTED; H3: no difference
  shown (within the guard). The label-free row passed its reuse checks
  (largest relative deviation from E1's values 0); the adjudicator recorded
  no deviation and found its code identical to the stamped version.

Departures from the runbook's operations, recorded under PREREG_CM2D Sec. 8;
none touches a file the adjudicator reads or a criterion:
- B1b's direct fetch from GitHub timed out on the box. The branch and the tag
  were fetched from a git bundle of the stamped commit and its annotated tag,
  one of the two routes of the supplement to the operator's instruction of 8
  October (the other: AutoDL's network route); the operator's report,
  relayed on 9 October, recorded at Stage 7. The precheck
  (`precheck.json.used`) and the provenance file show the tag, the commit,
  the tree and a clean checkout.
- At 14:26:44 China Standard Time (06:26:44 UTC) on 9 October, after the run
  had ended (its report is dated 04:10:26 UTC), B2's line that sets an
  earlier precheck log aside ran again at the box's terminal and renamed
  `precheck.log`. No other line of B2 that writes a file ran: the return
  holds no new precheck log and no new GO file, and `precheck.json.used` is
  the GO the run used. Arrow keys had been pressed in the run's window during
  the run (a screenshot the operator sent shows them), so the line may have
  been recalled from the shell history; how it came to run is not recorded.

`tests/test_cm2d_records.py` checks that:
- the files are these, and the verdict's recorded inputs are these files,
  E1's committed report, the stamped PREREG_CM2D.md and July's report;
- the run was one attempt on the stamped commit and tree, exited 0, with
  the GPU idle and the suite green before it, no out-of-memory event, and
  the GO it used was the precheck of the stamped checkout;
- the report is the stamped configuration's (its canonical SHA-256 is
  PREREG_CM2D's CONFIG_SHA256[cm2d_v1]), on E1's corpus and seeds, with a
  solve ledger of 0 and no restart;
- the verdicts follow from the report's per-instance arrays by PREREG_CM2D
  Sec. 4's rule, recomputed in the test, and the label-free row reproduces
  E1's per-instance values; the secondary readings the manuscript may quote
  (the 80 comparisons, the label efficiency, the instance-seed pairs, the
  values worse than the zero field, the graph network's reading) follow from
  the same arrays, recomputed in the test;
- everything in `verdict.json` that does not depend on git (the hypotheses
  with their medians, Welch and resampling intervals, the reuse checks, all
  secondary readings, the deviations and the run block) is what
  `scripts/adjudicate_cm2d.py` computes in process from the committed
  files.

## CM2D's error spectra: the export of 9 October 2026 (RUNBOOK_CMAME Sec. D)

`spectra/` holds RUNBOOK_CMAME Sec. D as it ran on the box on Stage 7's
commit `8b5d443` (tree `e288619b0338a6fa497dfabba6c953e8b3a4e553`, clean),
copied byte for byte from `cm2d_spectra_return_20261010-0023.tgz` (SHA-256
`8c9a4c1f3830607579d3fd6d6f08aa62e2c76f223db8885074f0973dfe263b63`, as the
operator sent it and as recomputed on receipt; the name carries the box's
China Standard Time, 16:23 UTC on 9 October). The suite there: 535 passed, 2
deselected. The export exited 0; its timed part (the 256 instances, the
summaries and the figure file) took 70 s, of which 31 s went to the
eigendecompositions and 14 s to the second pass with TF32 off (RTX 5090,
driver 595.71.05, torch 2.12.1+cu130; 16 CPUs allotted). Post hoc: specified
after CM2D's verdict and reported only; no verdict reads it.

| file | SHA-256 |
|---|---|
| `export/fig2d.npz` | `1444977bceba4466b37a3b0f96b2eed78869826b499618e63ee24b349a7b4084` |
| `export/spectra.json` | `a494aa49c299a83f614d3b8e8bd3aaf81d6e3cf76181e66f6abbb7fff863dc85` |
| `export/spectra_val.npz` | `fed09ab55afbf2866427e54920ee7655df565a9704e6c5f098615e4f935116ac` |
| `machine.txt` | `adb55605b33d8c5569390244d1cf9c67c1204d94c256cf21b7126bc32ae03f9c` |
| `pytest.log` | `ad78a837322b7120785b0c73b829010fb8ba5a5efe47786a24ac00f03cfb5a37` |
| `spectra.log` | `26c1e419d8e806e16860686a828dc2722e35458cc63090b56cc108bc04f6a780` |
| `status.txt` | `fe4aefe67ea7930edbd135c51a60065bd5d4cbf7258a14bc67925de5a7da1b6b` |

- `export/`: `scripts/cm2d_spectra.py` on CM2D's kept states at 1,024 labels
  (L_D, row `labels`; L_K, row `labels_knorm`; the graph network, row `mgn`;
  seeds 0-2) and E1's three label-free states (row `ar`), on the run's 256
  validation instances: the per-load arrays (`spectra_val.npz`), the inputs
  and their hashes, the content checks, the counts and the summaries
  (`spectra.json`), and the figure instance chosen by the script's rule
  (`fig2d.npz`: validation index 221, `instance_27356.npz`, 547 nodes).
  Every state matched CM2D's provenance file, the label-free ones also the
  report's d9_restart record. Every transformer reproduced the report's five
  per-instance arrays exactly, the graph network with median relative
  deviations up to 1.7e-5 in the displacement error and 1.4e-4 in the energy
  gap, the two the export gates (up to 5.2e-4 in the peak von Mises error):
  its CUDA scatter reductions are not bitwise reproducible. The TF32 policy
  was in force after the second pass as before it.
- `status.txt` (exit 0), `machine.txt` (the commit, the tree, a clean
  checkout, the GPU and the CPU allotment), `spectra.log` (the export's
  console, ending with its summary line) and `pytest.log` (the suite before
  the export).

`tests/test_cm2d_spectra_records.py` checks that:
- the files are these; the export ran once on Stage 7's commit and tree,
  exited 0 after a green suite, kept the TF32 policy, and printed the summary
  of the JSON it wrote; the machine, the texts and the timings are those
  quoted here;
- its inputs were CM2D's committed report and provenance file, the stamped
  configuration, the twelve states the provenance file lists (the label-free
  ones also those of the report's d9_restart record) and the run's own
  validation split;
- every model reproduced the report's per-instance arrays (the export's
  content check, and the same comparison recomputed from the per-load
  arrays: the transformers' to 1e-12, and the graph network's recorded
  median and largest deviations);
- on every load case of every row and seed, Lemma "Exactness", Corollary
  "Zero-field test and ranking", Proposition "Energy-optimal amplitude"
  (with the gap of c* u from the stored energies) and the plane-stress
  identity and bound of Proposition "Energy gap and stress error" (with
  gamma* from the stored integrals) hold; the spectra sum to the norms (the
  errors' and the solution's in both binnings, the IEEE predictions' errors'
  and the rounding's in the log binning); in every occupied bin the
  stiffness-weighted mass over the Euclidean mass lies within the bin's
  eigenvalue range, and the outermost log bins are empty; every Rayleigh
  quotient (the errors', the IEEE predictions' errors', the rounding's and
  the solution's) lies between the extreme eigenvalues; and the rounding is
  of TF32's size on every prediction (the second pass was not the first
  again);
- the summaries, the counts and the eigenvalue ranges are what the script's
  functions compute from the committed arrays, and the readings the
  manuscript may quote follow from their definitions, written out again (per
  row the quotients, the shares above 10^k RQ*, the IEEE quotients and the
  rounding's shares; the solution's shares and quotient; per pair of rows
  the shares, the ratios of means and the geometric-mean ratios, overall,
  per seed and with TF32 off);
- end to end, the export's seed means of the relative energy gap and of the
  von Mises error are the verdict's, seed by seed, for H1, H2a, H2b and H3,
  and L_D's over L_K's ratios of means are H2a's and H2b's 4.596 and 2.215;
- the figure file is the instance the rule selects from the report and
  carries that instance's per-load arrays; with its stiffness matrix
  reassembled from its mesh and material by the generator's assembly, it has
  the stored eigenvalues, a U* that solves the stored loads, and every row's
  stored seed-0 coefficients, norms, energies, gaps, c*, spectra and von
  Mises stresses.

## The holdout sets: pool depths, exclusions and resampling (PREREG_HOLDOUT, 14 October 2026)

- `holdout/pool_depths.json`: `scripts/holdout_pool_depths.py` on the six
  branches of the repository as they stood on 14 October 2026 (the commits
  are listed under `scanned`), reading every JSON file of each from git
  objects. Fifteen reports: for each its corpus, split, the pool depth it
  records (`data_economy.unlabeled_pool_depth_used`; every one of the fifteen
  records it) and the depth its configuration implies
  (`fejepa.experiments.runner._pool_need`, from which the runner sets the
  recorded one, so that the two agree by construction). `history`: the scan
  of every JSON file reachable from the remote branches and tags it lists
  (`refs`), older commits included, finds the same fifteen reports.
  `other_reads`: the depths that
  the recorded tools outside the runs reached, from their records (E1's
  lambda pilot, the two-dimensional step timing, wp9's C0.6 memory audit and
  C0.4 reading, CM2D's precheck). The deepest prefix of `runs/data3d_phase2`
  is 1,024 and of `runs/data2d` 25,600.
- `holdout/overlap.json`: `scripts/holdout_overlap.py`. The replay of the
  draws of every three-dimensional set the repository records a generation
  of, without meshing (the cross-branch regression's miniature of
  `configs/phase2b_v1.json` and its fine set, run in the sandbox, and the
  geometries of the mesh-size calibration included), checked against the
  Poisson ratio, box and load scales of the field export's three figure
  instances; the sandbox's other sets of the two generators and seed 0,
  prefixes of the same streams (`sandbox`: `scripts/holdout_scan_sets.py`
  over /home/claude, /tmp and /mnt/user-data on 14 October 2026 at 05:37
  UTC; the script lists every set of the generators and seed per kind,
  copies of the corpus manifests, and stray instance files).
  Of `runs/data3d_phase2`, the regression's miniature drew instances 0 to
  79 again, and the fine-mesh set, drawn from the same seed, drew 28, 106
  and 294 of the tail and 198, 210 and 218 of the training pool (the fine
  evaluation instances 212, 224 and 232); the 34 tail instances among them
  (32 of 0 to 79, and 106 and 294) are excluded from h3d. Nine pairs share
  the box and the Poisson ratio only, with other cavities and load scales
  (`same_box_and_nu_only_3d`), and are not excluded. In two dimensions: the
  33 instances of the tail that wp9's load-scale measurement rebuilt (32 of
  the 256 it rebuilt; the regression's miniature of
  `configs/e1_2d_base.json`, instances 0 to 79, among them) or whose own
  file the authors' July 2026 archive holds (6, 9 and 10, rebuilt too, and
  29992), excluded from h2d (`records/wp9/scale_factor.json`); the backup
  archives of the whole corpus (`backups_2d`), from which no file is
  recorded as extracted outside the box, leave nothing out. `bounds`: a set
  of the generators and seed of at most 80 instances with a band of mesh
  sizes, 320 at one size or 256 in two dimensions shares with the tails only
  excluded instances (checked by the script), so that the regression's
  miniatures, drawn again whenever it runs, leave the sets as they are; the
  sandbox is scanned again before the stamp, which is not made unless every
  such set is within the bounds.
  PREREG_HOLDOUT's sets: 686 and 4,111 instances.
- `holdout/resample.json`: `scripts/holdout_resample.py`. The rules of
  PREREG_HOLDOUT Sec. 5 on 1,000 resamples of the validation instances of
  each holdout set's size, drawn directly and with the validation set's own
  sampling added, with the count of each claim's failures by the comparison
  that failed (`failing`); and the calibration of V on the validation
  instances alone (`V`: random halves of 128 and draws of the holdout sets'
  sizes, without a change and with the label-free transformer's four error
  metrics multiplied by 1.05 to 1.20 in both sets; and at the holdout sets'
  sizes each quantity alone made worse by 1.02 to 1.20). PREREG_HOLDOUT
  Sec. 5 quotes both.
- `tests/test_holdout_config.py` checks the listings against
  `configs/holdout_v1.json`, re-derives the pool depths and the other
  tools' depths from the listed commits when they are in the checkout
  (a checkout without them checks the record's consistency), re-derives
  the overlap record and its bounds, checks that the regression's
  miniatures are the sets it replays, and tests the scan script on sets of
  its own; `tests/test_holdout_rules.py` re-derives the resampling record.

## K3D: the code that trained Phase-2's L_D states, and the decision rule (PREREG_K3D, 20 October 2026)

`k3d/regression_phase2_e672110.json` and `k3d/regression_phase2_99d3674.json`:
`scripts/regress_supervised_rows.py`, in the sandbox on 20 October 2026, ran
the miniature of `scripts/regress_against_branch.py` for Phase-2's stamped
configuration (`configs/phase2_v1.json`) on this code (the Stage 12 tree
`165e8bf6b591614ee6a7edb850a83058e4f420ad`, which PREREG_K3D ran at
`prereg-k3d`) and on the code of the Phase-2 attempts that trained the L_D
states at 1,024 labels: wp7-3d `e672110` (third attempt, 3-13 September
2026: seeds 1 and 2; `src` = tree `61b7471ac4808505405700b90afcbe118318f335`)
and `99d3674` (second attempt, 1-2 September: seed 0; tree
`2aa920efcd0fa5676f8f409ff4ff0c07bf096ff5`; the two differ only in
`anchor/energy.py`, D10, which the labels-only unit does not use). Each side
in its own process importing its own source tree, CPU, one thread, a fresh
pass and a restart pass. E8's cells of the supervised rows (labels-only,
labels+energy, graph network: 300 numbers per pass) and of the naive rows
(210) are identical, and the labels-only and graph-network states
byte-identical (4 files). The label-free row differs, as it must
(DEVIATIONS_PHASE2 D14 corrected its objective after Phase-2), and so does
everything computed from it (P3's fine-tuning, E8's comparisons, gate G2),
with three keys the later code adds to the report; the record counts these
differences by path and lists none elsewhere. This is PREREG_K3D Sec. 7's
evidence that the code it ran builds the L_D unit's initial weights and
draws its order as the attempts' code did. `wp8-lejepa` merged these
attempts' changes by cherry-pick: `e672110` is on `wp7-3d` only (fetch it
to compare the tree), `99d3674` is an ancestor of this branch. The records
stay as committed when `src` changes after that run (Stage 14 added a
module); the table at the top of this file names the current code.

`k3d_sims.json`: `scripts/k3d_sims.py` (fixed seed; seconds), the source of
every simulated number PREREG_K3D quotes. The E-series noise guard on three
per-seed values per arm, log-normal, at the references' spreads of the
per-seed medians over the validation instances (Phase-2b's arrays: the L_D
transformer's 10.2% in the relative energy gap and 5.9% in the von Mises
error, the label-free transformer's 23.3% in the relative energy gap,
simulated at 10%, 6% and 23%), against new-arm spreads of 5% to 50%
(`medians`) and at L_K's two-dimensional spreads (CM2D's return: 37% and
19%; `medians_at_lk_2d_spread`); and the seed-mean form with the reference
at L_D's recorded seed means (`seed_means_at_the_recorded_reference`: one
validation instance carries seed 1's, so that the reference's own SE_rel is
0.989 in the relative energy gap and no reduction can be shown).
`tests/test_k3d_prereg.py` checks the constants against the reports and
every quoted number against the record.

## The holdout sets: the run of 21 October 2026 and its verdict (PREREG_HOLDOUT)

`holdout/return/` holds RUNBOOK_CMAME Sec. E as it ran on the box, copied
byte for byte from `holdout_return_20261021-2011.tgz` (SHA-256
`d185ee5990f3865584579979c10ec3f823db8fd32ce2ac0c8ca180c0c556069e`, as the
operator sent it and as recomputed on receipt). The four stages ran on the
stamped commit `69fb698` (tag `prereg-holdout`, tree
`c480c756ada4d933056e7b6918d48462df054da9`) from 2026-10-21T10:16:04Z, one
after another in E1's order (each set's labelling, then its evaluation),
each in its second attempt and each exiting 0 (the first attempts are
below): the labellings of h3d (686 instances, 2,744 load-case solves,
2,321.9 s) and h2d (4,111 instances, 16,444 solves, 39.3 s), with largest
relative residuals 5.3e-11 and 3.7e-11 (the bound 1e-8), no label reused
and no holdout instance recorded as labelled by its corpus, and the
evaluations of h3d (3,829.1 s) and h2d (357.8 s). Host
`autodl-container-45e441a24a-99d5b40d`, RTX 5090 (driver 595.71.05), torch
2.12.1+cu130. The suite there, on the tag: 684 passed, 3 deselected. The
box's clock reads China Standard Time (UTC+8): below, its times are marked
"box time" and UTC times end in Z.

| file | SHA-256 |
|---|---|
| `return/eval_h2d.log` | `eda6ded38b8683f11ea72abcb7c977bc8faeca44900538d5ac414e2e46afea33` |
| `return/eval_h2d.log.20261021-195917` | `636a610f1a9c2e000b3d45f44cb109e5de696ec8b4f392b1803267695b5530d5` |
| `return/eval_h3d.log` | `896aa07532c6242fc635cfe8ca6d01d14afa33fc685cb6206da079898ad640b3` |
| `return/eval_h3d.log.20261021-185447` | `636a610f1a9c2e000b3d45f44cb109e5de696ec8b4f392b1803267695b5530d5` |
| `return/h2d/eval.json` | `b81f80b740a0e593890952b7791c4b6aab7570587ba62b6d1513a2cc7e08d9ea` |
| `return/h2d/eval_arrays.npz` | `9ce675c746a8657d2596b803735fa40f79bb0d30c697152ec30a3c9c6bdff614` |
| `return/h2d/manifest.json` | `4b79ed0673726585e2f6c292b99866f035d4b4968bd859f5df860fe9be62c9a8` |
| `return/h3d/eval.json` | `855572411c44edebb6a2e2b8821138192552335603f05f6fe70d5c386f88cba9` |
| `return/h3d/eval_arrays.npz` | `ed205f29315b0df2fb6e2244b6cdb2045d4f15af96d66004132ca2ae61d64b96` |
| `return/h3d/manifest.json` | `d88b4a745842c679a07dfc6afba07ed4c72e314d13776612f0e0876b909b749d` |
| `return/label_h2d.log` | `ffda19605209874d4b6093db56281d32e8885453641643c6c4e047ff7829e6bc` |
| `return/label_h2d.log.20261021-195838` | `636a610f1a9c2e000b3d45f44cb109e5de696ec8b4f392b1803267695b5530d5` |
| `return/label_h3d.log` | `ab48145cfe4257c457257351ca5a4c7a11c407f3e6880848ad77b985d4244646` |
| `return/label_h3d.log.20261021-181604` | `636a610f1a9c2e000b3d45f44cb109e5de696ec8b4f392b1803267695b5530d5` |
| `return/machine.txt` | `858cb7ea32af984e26e7838c76fc09f8535f917eb4fb9c9611d388f4975091a8` |
| `return/precheck.txt` | `6a086e45767a433b32f0760a52493e2162f3fe5cf3657504abb45ba62293387d` |
| `return/provenance.txt` | `7070fbf6d1927f51a4133734d48fb309f08e320e0e3b39e507c09db48e2cc999` |
| `return/pytest.log` | `c7183434a75589ed17068904bd4e0c16ed1c43c33fd61b3bf00aaf05afcf43ee` |
| `return/pytest.log.20261021-180704` | `4850f7525b1c1cdd26ec971e7d6b7958779adfad06f3ef29d4017f19eea7fec3` |
| `return/status.txt` | `dca9b66d1bdcdcbee21e61faabcb9caa08a6a7db7f3837f1507174a5c2d1ad8b` |

- `h3d/` and `h2d/`: per set, the labels manifest (`manifest.json`: per
  instance the SHA-256 of the corpus file it was solved from and of its
  labels file, and the solve's residual; the labels stay on the box), the
  evaluation (`eval.json`: the states and their SHA-256, their content
  checks on the 256 validation instances, the per-seed means and the load
  cases worse than the zero field) and its per-instance arrays
  (`eval_arrays.npz`). `status.txt`: the start and exit lines of every
  attempt. `label_h3d.log`, `eval_h3d.log`, `label_h2d.log` and
  `eval_h2d.log`: the consoles of the second attempts; each
  `*.log.20261021-HHMMSS` is the first attempt's, set aside when the second
  started (the suffix is the box's time). `precheck.txt` and `machine.txt`:
  E1's checks before each attempt (the time, the host, the GPU idle) and
  its record after each (the commit and tree, the GPU, the CPUs, the memory
  limit and the memory). `pytest.log`: E0c's suite on the tag;
  `pytest.log.20261021-180704`: an earlier run of it, set aside when E0c ran
  again (below). `provenance.txt`: E2's record of the checkout when the
  return was packed (`git describe`, both forms, `prereg-holdout`), the
  host, and every other file's SHA-256.
- `holdout/verdict.json` (SHA-256
  `b76f869f72f2b55de9216815a6707ca5860ae9628da2150fe461da1f2138ba68`):
  `scripts/adjudicate_holdout.py`, run on 25 October 2026 at the stamped
  commit (RUNBOOK_CMAME Sec. E3, with the tag checked out, since the branch
  had moved past it on 21 October: tracked files clean, in a clone of its
  own with the tag fetched by a forced refspec), with the return in place,
  as `python scripts/adjudicate_holdout.py --return
  records/cmame/holdout/return --config configs/holdout_v1.json --prereg
  PREREG_HOLDOUT.md --out records/cmame/holdout/verdict.json` (the two
  options name the files the script reads by default, given so that the
  paths it records are the repository's). Run again on the same inputs, it
  writes the same file byte for byte; the adjudication of 21 October 2026,
  of the return as received and unpacked elsewhere, wrote the same file but
  for the paths. The adjudicator found its code identical to the tag's.
  Every state passed its content check: the transformers' values were
  reproduced exactly, and the graph networks' largest median relative
  deviations of the displacement error and of the relative energy gap were
  1.7e-5 and 7.9e-5 in h3d and 1.8e-5 and 1.5e-4 in h2d (PREREG_HOLDOUT
  Sec. 3's bound: 1e-3).

The claims (PREREG_HOLDOUT Sec. 5), read on the holdout sets; per-seed
values are seeds 0, 1 and 2:

| claim | on the holdout set | verdict |
|---|---|---|
| T1 (h3d) | the label-free transformer better than the supervised transformer on all five metrics, in each seed and in the seed mean (20 comparisons); in all nine pairs of seeds as well, the least favourable 23.3% apart (critical-region recall) | REPLICATED |
| T2 (h3d) | the graph network's displacement error lower than the label-free transformer's on 95.8%, 92.0% and 86.3% of the instances (the rule: above 50% in each seed), its von Mises error higher on 2,058 of the 2,058 instance-seed pairs (at least 95%) | REPLICATED |
| T3 (h3d) | load cases worse than the zero field: 340 of the supervised transformer's 8,232 (96, 107 and 137 per seed) and 237 of the graph network's (67, 79 and 91), each with a positive energy and no other | REPLICATED |
| H1 (h2d) | relative energy gap, the label-free transformer 0.0393, 0.0400 and 0.0385 against L_D's 0.1423, 0.1467 and 0.1212: rel -71.3%, SE_rel 5.8%, tau 11.5% | REPLICATED |
| H2a (h2d) | relative energy gap, L_K 0.1298, 0.0213 and 0.0834 against L_D's: rel -42.9%, SE_rel 23.7%, tau 47.4% | NOT REPLICATED |
| H2b (h2d) | von Mises error, L_K 0.1280, 0.0855 and 0.1205 against L_D's 0.2343, 0.2501 and 0.2237: rel -52.8%, SE_rel 6.4%, tau 12.9% | REPLICATED |
| H2c (h2d) | the same comparison against halving: rel -52.8%, below -50% | REPLICATED |
| D2 (h2d) | the label-free transformer's displacement error higher than L_D's (0.0640, 0.0674 and 0.0625 against 0.0513, 0.0503 and 0.0541) and its other four metrics better, in each seed and in the seed mean (20 comparisons); in all nine pairs of seeds as well, the least favourable 7.5% apart (peak von Mises error) | REPLICATED |

- Tally: 7 REPLICATED, 1 NOT REPLICATED (H2a, the claim itself:
  `failing`), none NOT EVALUATED. Applied to the validation instances as
  this run recomputed them, every claim's rule reads REPLICATED
  (`validation_reference`), and none of PREREG_HOLDOUT Sec. 5's 2,000
  resamples of the validation instances (`holdout/resample.json`, 1,000 per
  scheme) read H2a NOT REPLICATED. Sec. 5: any revision of the manuscript
  qualifies its statement of H2a with these numbers beside the original
  ones.
- Beside H2a (PREREG_HOLDOUT Sec. 6, no verdict): L_K's mean relative
  energy gap is 2.69 times as large on the holdout set as on the validation
  instances (95% interval, the holdout set resampled: 1.12 to 4.64; L_D's
  ratio 1.02, 0.99 to 1.07), while its median is alike on the two (0.0223
  and 0.0210; V does not reject the quantity, p 0.52). On per-seed medians
  L_K reads rel -81.4% against L_D, tau 13.4%: lower beyond the guard. Its
  seed means rest on a few instances: the largest relative energy gaps of
  its seeds 0, 1 and 2 on the holdout set are 254.3, 21.6 and 190.4.
- H3 (a reading): relative energy gap, L_K against the label-free
  transformer, rel +99.1%, SE_rel 80.1%, tau 160.2%: no difference shown
  (within the guard); with the roles exchanged rel -49.8%, tau 80.4%, the
  same.
- V: REPRESENTATIVE. Of the 35 quantities (every row and metric of both
  sets, none left out), none is rejected at the family-wise level of 5%.
- `deviations`: each of the four stages started twice, with exits 2 and 0
  (the first attempts, below). `secondary`: PREREG_HOLDOUT Sec. 6's
  readings, on the holdout sets beside the validation instances.

Two departures, recorded under PREREG_HOLDOUT Sec. 7: the first from the
runbook, the second one that the last sentence of Sec. 7 has the authors
record. Neither changes a criterion, a label or an evaluation; the first
attempts' start and exit lines are in `status.txt`, which the adjudication
reads (`deviations`, above):
- The first attempts ran on another commit. E0c's suite ran on commit
  `8b5d443` (RUNBOOK_CMAME Sec. D's, two commits after `prereg-cm2d`; tree
  `e288619b0338a6fa497dfabba6c953e8b3a4e553`):
  `pytest.log.20261021-180704` reads 535 passed, 2 deselected, that
  commit's count (the log is undated; it was set aside at 18:07:04 box
  time, 10:07:04Z, when E0c ran again). E1's checks ran at 18:02:11 box
  time (10:02:11Z; `precheck.txt`, first block), and its four stages
  started at 10:02:23Z and each exited 2 at once: the script is not on that
  commit (each first attempt's log is the one line `python: can't open
  file '/root/autodl-tmp/FE-JEPA/scripts/holdout_run.py': [Errno 2] No such
  file or directory`). E1's record after its stages names that commit
  (`machine.txt`, first block). E0b fetches the branch and the tag, and E0c
  checks the branch out, requires `git describe --tags --match
  prereg-holdout` to print exactly `prereg-holdout` before the suite, and
  stops at any other output or count. E0c then ran again, on the tag, and
  E1 again (its checks at 18:15:45 box time, 10:15:45Z; its first stage at
  10:16:04Z). The adjudication reads the status file, which records every
  attempt but not its commit. On the same visit the box had run
  PREREG_FINE3D's session (branch `wp9-pool`) before this run;
  `DEVIATIONS_FINE3D.md` F1 and F2 on that branch record the order and the
  checkout's switch to this branch.
- A set beyond the bounds of Sec. 2, in the sandbox, between the scan of
  Sec. 2 (14 October 2026, 05:37 UTC; repeated at the stamp, 18 October
  2026, 07:45 UTC) and the return (packed at 20:11 box time on 21 October
  2026, 12:11Z). On 20 October 2026, from 12:13 to 12:41 UTC, an
  independent review of PREREG_K3D's box-scale paths (Stage 12) worked on
  `runs/data3d_phase2` with its generator: it replayed the generator's
  draws for the corpus's 2,000 instances (seed 0, the corpus's band of mesh
  sizes) without meshing, as `scripts/holdout_overlap.py` replays the
  corpus, and the split (n_val 256, seed 1), and kept the drawn mesh sizes,
  geometries and Poisson ratios of all 2,000, the tail's among them;
  meshed three validation instances (`instance_01661`, `instance_01130` and
  `instance_00608`) to compare their node counts with
  `records/cmame/timing/timing_3d.json`; meshed the 1,024 instances of
  pool[:1024], each at its own mesh size, keeping only their node, element
  and edge counts; and rebuilt two of those in full (`instance_01656` and
  `instance_00479`, pool positions 75 and 34), labelled them by the direct
  solve and ran one training step of the full-size transformer on each, on
  the CPU, with either loss. The two instances' files were deleted at 12:41
  UTC. The 1,024 are a set of the corpus's generator and seed beyond the
  bound of 80 with a band of mesh sizes. None of these instances is in the
  tail pool[1024:] from which h3d is drawn: they are validation instances
  and pool[:1024], the prefix on which the arms at 1,024 labels and the
  label-free arm trained; of a tail instance nothing but its drawn
  parameters was made. No other set of the corpora's generators and seed
  beyond the bounds, and no file of a holdout instance copied off the box,
  is known in that window: the two returns that left the box in it,
  PREREG_FINE3D's (packed at 18:03 box time on 21 October) and this one,
  hold no instance or label file. The review's scripts and records are kept
  in the sandbox; Stage 12's notes report the meshing. The sandbox, scanned
  again on 25 October 2026 at 12:22 UTC (`scripts/holdout_scan_sets.py`,
  the same directories, exit 0), holds no set of the generators and seed
  beyond the bounds.

`tests/test_holdout_records.py` checks that:
- the files are these, with these SHA-256, and the verdict's recorded
  inputs are these files, the stamped PREREG_HOLDOUT.md and
  `configs/holdout_v1.json`;
- the attempts are those described above: the four stages started at
  10:02:23Z exited 2, each logging only the missing script, on the commit
  the first block of `machine.txt` names; the four that count ran in E1's
  order on one host, on the stamped commit and tree, and exited 0; and the
  two suites' logs read the counts quoted;
- the labels manifests are the configuration's sets (686 and 4,111
  instances in pool order, the excluded instances left out), every
  residual within the bound and no label reused, and the evaluations read
  them;
- the claims, H3 and the tally follow from the evaluations' per-instance
  arrays by PREREG_HOLDOUT Sec. 5's rules, recomputed in the test, and
  everything in `verdict.json` but the paths of its inputs, the
  configuration's record (checked against the stamp, above) and the
  adjudicator's own record (its code's SHA-256, its comparison with the
  tag, the library versions) is what `scripts/adjudicate_holdout.py`
  computes in process from the committed files;
- the numbers this section quotes from the verdict and the return are
  theirs, those beside H2a recomputed from the arrays; the sandbox's times
  and its scan, which no file in the repository records, are checked only
  as quoted.

## K3D: the run of 22-25 October 2026 and its verdict (PREREG_K3D)

`k3d/return/` holds RUNBOOK_CMAME Sec. F as it ran on the box on the
stamped commit `7614ae2` (tag `prereg-k3d`, tree
`30398e29d00df1ebe7c8e9027f0b76c0cbb12b3c`), copied byte for byte from
`k3d_return_20261025-1929.tgz` (SHA-256
`d6dc142e05c3bc21ba3d718118faeb287bdaf081bcde3f59e94e90f602b33f52`, as the
operator sent it and as recomputed on receipt). One attempt: it started at
2026-10-22T14:00:41Z and exited 0. By the times of `runs/k3d/` in
`provenance.txt` (China Standard Time): the six stored states evaluated by
22:12:32 on 22 October (`reused.json`); the three L_K seeds, 200 epochs
each, finished at 20:38:55 on 23 October, 19:06:24 on 24 October and
17:35:20 on 25 October, each 22 h 26 min to 22 h 29 min after the one
before (seed 0 after the stored states' evaluations); the holdout set's
686 instances evaluated in 2,692 s; the report written at 18:20:13 on 25
October, 68 h 20 min after the start. The host of PREREG_HOLDOUT's run, RTX
5090 (driver 595.71.05), torch 2.12.1+cu130, a memory limit of
96,636,764,160 bytes (90 GiB) and no memory event (`oom_kill 0`). The suite
there: 760 passed, 3 deselected.

| file | SHA-256 |
|---|---|
| `return/holdout_arrays.npz` | `d166006b0bcfaaeec16b0b085e9c00b84eb7e1078bf6962bca28dee265f6df9e` |
| `return/k3d.log` | `89b005b5d79ff4bfd2ecc7f680731ebed5cd2dacbaf3de4f59afc3f6fa4ec193` |
| `return/machine.txt` | `419e8c4033eba038224908af236a5e4990b57ab9878cd4323834d52e747d3712` |
| `return/precheck.txt` | `48a61454ac386faad177c7b6ed9bb85451312d2322dab7900cfee9bb58ee48ef` |
| `return/provenance.txt` | `ebadd9340477e0d664da253dfc42b18a84ef84e10b9380237c34159be9fa08ee` |
| `return/pytest.log` | `ede86fe12d6ea1bbed2a4f303b9c5b5107ba9c219e2697b2e08861081327de6f` |
| `return/report.json` | `f57b5cbf66659d0dd0986f7b07ee2fbed744c6a49f85329a942624cc75d90a95` |
| `return/reused.json` | `0a9a6d8e29d1d15562eab8b4314f56a9325ffd89637e35c6951c9cb5b4026a4b` |
| `return/seed_0.json` | `6eb25009ca0c6b95ce3c6116b84c57304facf633ada696904799b4e44f804581` |
| `return/seed_1.json` | `8c5178c2c5bfc5b6aaace7665ba997d9eca9f60b4be83559f6277ca187133d92` |
| `return/seed_2.json` | `691602dbc08ea282bb1da3710db7b15d15605899356eff914de82376fb6a9e3d` |
| `return/status.txt` | `4f3f7896850b3b49ad1d025adc37b07e964c9ce2ec13e040e8ae344bf2a994aa` |

- `report.json`: the run's report: the configuration and its canonical
  SHA-256 (PREREG_K3D's CONFIG_SHA256[k3d_v1]), `git describe` and the
  commit; the six stored states' evaluations with their content checks;
  each L_K seed's training and its evaluation on the 256 validation
  instances; the holdout set's evaluation. `reused.json`: the stored
  states' evaluations, written before any training. `seed_0.json` to
  `seed_2.json`: each seed's result, written as it finished.
  `holdout_arrays.npz`: the per-instance values on the 686 holdout
  instances. `k3d.log`: the console. `status.txt`: one start, exit 0.
  `precheck.txt` and `machine.txt`: F1's check before the run (the time,
  the host, the GPU idle) and its record after it (the commit and tree, the
  GPU, the CPUs, the memory limit, the memory events and the memory).
  `pytest.log`: F0c's suite on the tag. `provenance.txt`: F2's record: the
  commit, the tree, `git describe` (`prereg-k3d`), the host, the listing of
  `runs/k3d/` with its times, the SHA-256 of the three L_K states (they
  stay on the box) and of every other file.
- `k3d/verdict.json` (SHA-256
  `87f944d7f4320e0c32fd48c4c268c1cf90c8f302277405756058d45ea85f335b`):
  `scripts/adjudicate_k3d.py`, run on 25 October 2026 in a clone of its
  own at `/work/label-free-fe-surrogates`, the branch at the stamped commit
  with the tag fetched by a forced refspec, PREREG_HOLDOUT's return and
  verdict committed there under `records/cmame/holdout/` as above
  (RUNBOOK_CMAME Sec. F3) and tracked files clean, as `python
  scripts/adjudicate_k3d.py --return records/cmame/k3d/return --prereg
  PREREG_K3D.md --config configs/k3d_v1.json --source-report
  records/wp8/e2/baseline/report_phase2b.json --out
  records/cmame/k3d/verdict.json` (the three options name the files the
  script reads by default). The script writes the paths of three further
  inputs from its own location, so that they name that clone:
  `inputs.holdout_manifest`, `inputs.holdout_spec` and
  `inputs.cm2d_verdict` are its
  `records/cmame/holdout/return/h3d/manifest.json`,
  `configs/holdout_v1.json` and `records/cmame/cm2d/verdict.json`, with
  their SHA-256. Run again, it writes the same file byte for byte; the
  adjudication of the same day, of the return as received and unpacked
  elsewhere, wrote the same file but for those three paths. The adjudicator
  found its code identical to the tag's and recorded no deviation. The six
  stored states reproduced Phase-2b's per-instance values exactly (largest
  relative deviation 0 in every metric, as the run recorded it and as
  recomputed from the report's arrays).

The verdicts read per-seed medians over the 256 validation instances
(PREREG_K3D Sec. 4); per-seed values are seeds 0, 1 and 2:
- H2a-3D, SUPPORTED: relative energy gap, L_K 0.00432, 0.00448 and 0.00452
  against L_D's 0.2241, 0.2555 and 0.2748: rel -98.2%, SE_rel 5.9%, tau
  11.7%.
- H2b-3D, SUPPORTED: von Mises error, L_K 0.0412, 0.0425 and 0.0437 against
  L_D's 0.2469, 0.2539 and 0.2760: rel -83.6%, SE_rel 3.4%, tau 10.0%.
- H3-3D (a reading): relative energy gap, L_K against the label-free
  transformer's 0.00932, 0.00744 and 0.00581: rel -41.0%, SE_rel 13.5%, tau
  27.0%: the stiffness-norm transformer lower beyond the guard. With the
  roles exchanged, rel +69.5%, tau 45.8%: the label-free transformer worse
  beyond the guard.
- Beside them, with no criterion: the seed means (H2a-3D rel -99.98%, tau
  197.9%, within the guard, L_D's seed 1 at 92.99 carried by one validation
  instance, `instance_00485`; H2b-3D -88.1%, tau 43.7%, and H3-3D -44.7%,
  tau 29.0%, lower beyond it); and the 686 holdout instances, per-seed
  medians: H2a-3D -98.0% (tau 12.6%), H2b-3D -83.0% (tau 10.0%), H3-3D
  -38.0% (tau 25.6%), each in its validation reading's direction.
- Beside them as well (PREREG_K3D Sec. 4), rel's Welch 95% intervals on the
  per-seed medians, with about 2 degrees of freedom: H2a-3D -123.5% to
  -73.0%, H2b-3D -98.0% to -69.2%, H3-3D -98.7% to +16.7% (H3-3D's includes
  no difference); from resampling the instances, the seeds kept: -98.4% to
  -98.1%, -84.5% to -82.7% and -43.9% to -38.4%. On the seed means, Welch:
  -525.7% to +325.7%, -182.0% to +5.8% and -105.9% to +16.5%; their rel
  has each verdict's and the reading's sign (`seed_means_show_the_direction`),
  which for H2a-3D, whose seed-mean guard cannot show a reduction (tau
  197.9%), is the seed-mean reading.

Secondary readings (PREREG_K3D Sec. 5; per-seed medians unless stated):
- L_K against the label-free transformer, the five metrics: relative
  energy gap -41.0%, displacement error -25.0%, von Mises error -19.4% and
  peak von Mises error -51.7%, each lower beyond the guard; critical-region
  recall +8.7%, within it (tau 10.0%). L_K is the lower of the two on 738,
  528 and 676 of the 768 instance-seed pairs in the relative energy gap,
  the displacement error and the von Mises error.
- Instance-seed pairs worse than the zero field (a mean relative energy
  gap above 1), of 768: the label-free transformer 0, L_D 18, L_K 0.
- L_K against the labels+energy row (Phase-2b's record): relative energy
  gap -95.7% (tau 52.8%), von Mises error -65.5% (tau 10.0%), both lower
  beyond the guard.
- The share of the gap between L_D and the label-free transformer that L_K
  closes: 105% in the von Mises error and 101% in the relative energy gap.

The container's memory limit, 96,636,764,160 bytes (90 GiB) as in
PREREG_HOLDOUT's run, is not the one the text gives: PREREG_K3D Sec. 7
says 92 GiB and F0c's comment expects 98,784,247,808 or `max`, the limit
that `records/cmame/timing/`, `spectra/` and `threads/` record (8-11
October 2026). It is above the 64 GB of PREREG_K3D Sec. 6 and F0c's stop
threshold, 64,000,000,000, and the operator instruction of 21 October 2026
had the run go on at any limit of at least that. No other departure from
PREREG_K3D or RUNBOOK_CMAME Sec. F is known beyond what the adjudication
reads, and it records none (PREREG_K3D Sec. 8).

`tests/test_k3d_records.py` checks that:
- the files are these, with these SHA-256, and the verdict's recorded
  inputs are these files, the stamped PREREG_K3D.md, `configs/k3d_v1.json`,
  Phase-2b's report, PREREG_HOLDOUT's labels manifest of h3d, the holdout
  configuration and CM2D's verdict;
- the run was one attempt on the stamped commit and tree, exited 0, with
  the GPU idle at its check, the suite green and no memory event, and the
  times quoted above are the return's;
- the verdicts, the reading H3-3D and the secondary readings quoted above
  follow by PREREG_K3D Sec. 4's rule from the per-instance values of the
  report, of the holdout arrays and of Phase-2b's report, recomputed in the
  test;
- everything in `verdict.json` but its inputs (above) and the
  adjudicator's own record (its code's SHA-256 and its comparison with the
  tag) is what `scripts/adjudicate_k3d.py` computes in process from the
  committed files;
- the numbers this section quotes from the verdict, the return and the
  records named are theirs; the operator instruction is quoted from outside
  the repository.

## Ritz baseline and enriched c*: the run of 28 October 2026 (RUNBOOK_CMAME Sec. G)

`ritz/ritz_return_20261029-1150.tgz` is the return of RUNBOOK_CMAME Sec. G
as the operator sent it on 29 October 2026 (23,818,923 bytes, SHA-256
`c0f5621fac38e8a946c34c7870a6c284305e2c2f0ccec29b24946a0f984c96af`, as sent
and as recomputed on receipt). `ritz/return/` holds its files other than the
19 per-instance `rows.jsonl`, byte for byte (50 files, 1.35 MB); the rows (81
MB unpacked, the largest file 19.6 MB) stay in the tarball, whose
`provenance.txt` lists the SHA-256 of all 68 files. The run: the branch at
`0c1d59a` (tree `d36f70537aadbf7a98e1a265aebea6daaa111b0b`, `git describe`
`prereg-k3d-2-g0c1d59a`, tracked files clean), on the host of
PREREG_HOLDOUT's and PREREG_K3D's runs (an Intel Xeon Platinum 8470Q, 25
CPUs; an RTX 5090, driver 595.71.05; a memory limit of 96,636,764,160 bytes,
90 GiB; `oom_kill 0`). G0c's suite: 806 passed, 3 deselected. G0d printed
Sec. G's eleven lines. G1 ran the fifteen steps in order, each with one start
line and `exit=0`, the first from 2026-10-28T17:26:48Z and the last from
19:55:47Z for 1,968 s, so to about 20:29.

Checked on receipt (29 October 2026; `tests/test_ritz_return.py` repeats each
check that the committed files allow):
- every file against `provenance.txt`;
- each set's summary rebuilt from its rows and the records (G3's
  `--resummarise`) and each arm's reading from its summaries (`--reread`):
  all 25 files identical byte for byte, wp9's two arms with wp9-pool's
  records copies of their reports (`--report`, at the SHA-256 that
  `configs/ritz_v1.json` pins), which this branch does not carry, so that the
  test rebuilds those two arms' readings but not their six summaries;
- every set's rows numbered 0 to n-1, no file twice, their SHA-256 the
  summaries' `rows_sha256`;
- the enriched reading's Ritz rows (p = 8) against the baseline's p = 8 on
  val3d and fine3d: relative difference at most 1.3e-10.

The baseline (Appendix 1; post hoc). The 5,565 instances of the five sets
passed the identity check (largest relative difference 2.5e-12, on h2d), no
direction was dropped at any p, and no load case of a Ritz solution was worse
than the zero field. Each set's medians, over its instances, of the
per-instance means over the load battery:

| set | p | unknowns | relative energy gap | displacement error | von Mises error | peak von Mises error | critical-region recall |
|---|---|---|---|---|---|---|---|
| val3d (256) | 6 | 168 | 0.0177 | 0.0203 | 0.0837 | 0.32 | 0.817 |
| val3d (256) | 7 | 252 | 0.0112 | 0.0132 | 0.0617 | 0.281 | 0.862 |
| val3d (256) | 8 | 360 | 0.0083 | 0.00963 | 0.0518 | 0.253 | 0.882 |
| val3d (256) | 9 | 495 | 0.00634 | 0.00756 | 0.044 | 0.226 | 0.894 |
| fine3d (256) | 6 | 168 | 0.0193 | 0.0221 | 0.0897 | 0.462 | 0.81 |
| fine3d (256) | 7 | 252 | 0.0126 | 0.0149 | 0.0668 | 0.424 | 0.859 |
| fine3d (256) | 8 | 360 | 0.00932 | 0.0111 | 0.0573 | 0.39 | 0.881 |
| fine3d (256) | 9 | 495 | 0.00703 | 0.00853 | 0.0488 | 0.354 | 0.893 |
| h3d (686) | 6 | 168 | 0.0172 | 0.0196 | 0.0835 | 0.325 | 0.821 |
| h3d (686) | 7 | 252 | 0.0108 | 0.0127 | 0.0615 | 0.287 | 0.862 |
| h3d (686) | 8 | 360 | 0.00798 | 0.00947 | 0.0513 | 0.253 | 0.88 |
| h3d (686) | 9 | 495 | 0.00614 | 0.00745 | 0.0437 | 0.221 | 0.894 |
| val2d (256) | 6 | 42 | 0.0305 | 0.0379 | 0.12 | 0.27 | 0.832 |
| val2d (256) | 8 | 72 | 0.0248 | 0.0325 | 0.111 | 0.21 | 0.846 |
| h2d (4111) | 6 | 42 | 0.0322 | 0.0406 | 0.122 | 0.273 | 0.833 |
| h2d (4111) | 8 | 72 | 0.0265 | 0.0348 | 0.111 | 0.21 | 0.85 |

The pairing (`baseline/<set>/summary.json`, `ladder.<p>.paired`): per model,
seed and metric, the share of instances on which the Ritz solution is
strictly better (lower, except the critical-region recall; ties apart),
rounded to the percent, except that a share strictly between 0 and 1 is never
shown as 0% or 100%. For the label-free transformers and L_K on every set,
the range over the three seeds, with the models' medians of the relative
energy gap and of the peak von Mises error in brackets:

| set | model (median energy gap; peak von Mises error) | p | relative energy gap | displacement error | von Mises error | peak von Mises error | critical-region recall |
|---|---|---|---|---|---|---|---|
| val3d | `phase2b:ar@1024` (0.00581 to 0.00932; 0.0659 to 0.095) | 6 | 0.4% to 6% | 67% to 79% | 1% to 8% | 0% to 1% | 48% to 71% |
|  |  | 7 | 3% to 25% | 91% to 98% | 14% to 31% | 0% to 1% | 81% to 96% |
|  |  | 8 | 11% to 73% | 98% to 99% | 37% to 67% | 0% to 1% | 95% to 99.6% |
|  |  | 9 | 38% to 100% | 99.6% to 100% | 69% to 98% | 0% to 2% | 99.6% to 100% |
| val3d | `k3d:labels_knorm@1024` (0.00432 to 0.00452; 0.0373 to 0.0388) | 6 | 0% to 1% | 43% to 57% | 0% to 2% | 0% | 23% to 25% |
|  |  | 7 | 0% to 1% | 78% to 85% | 4% to 7% | 0% | 51% to 54% |
|  |  | 8 | 1% to 4% | 94% to 96% | 13% to 19% | 0% | 61% to 65% |
|  |  | 9 | 6% to 10% | 98% to 99% | 28% to 43% | 0% | 74% to 80% |
| fine3d | `phase2b:ar (zero-shot)` (0.0791 to 0.111; 0.203 to 0.254) | 6 | 99.6% to 100% | 100% | 100% | 8% to 19% | 92% to 96% |
|  |  | 7 | 100% | 100% | 100% | 9% to 20% | 99% to 100% |
|  |  | 8 | 100% | 100% | 100% | 12% to 20% | 100% |
|  |  | 9 | 100% | 100% | 100% | 14% to 21% | 100% |
| h3d | `r1:ar` (0.00578 to 0.00901; 0.0659 to 0.0917) | 6 | 1% to 3% | 67% to 81% | 1% to 4% | 0% to 0.1% | 56% to 79% |
|  |  | 7 | 2% to 21% | 91% to 97% | 12% to 28% | 0% to 0.1% | 84% to 95% |
|  |  | 8 | 12% to 71% | 98% to 99.9% | 32% to 69% | 0% to 0.3% | 96% to 99% |
|  |  | 9 | 34% to 99.9% | 99.6% to 100% | 67% to 96% | 0% to 1% | 99.7% to 100% |
| h3d | `k3d:labels_knorm` (0.00437 to 0.00465; 0.0355 to 0.0388) | 6 | 0.1% to 1% | 45% to 58% | 1% to 2% | 0% to 0.1% | 27% to 28% |
|  |  | 7 | 1% to 2% | 82% to 88% | 3% to 7% | 0% to 0.3% | 52% to 55% |
|  |  | 8 | 2% to 4% | 94% to 97% | 11% to 17% | 0% to 0.3% | 63% to 67% |
|  |  | 9 | 6% to 12% | 98% to 99% | 31% to 44% | 0% to 0.3% | 77% to 84% |
| val2d | `cm2d:ar@1024` (0.0247 to 0.0254; 0.136 to 0.139) | 6 | 16% to 20% | 80% to 84% | 47% to 53% | 0% to 0.4% | 95% to 96% |
|  |  | 8 | 61% to 66% | 96% to 97% | 82% to 86% | 2% to 3% | 98% to 99% |
| val2d | `cm2d:labels_knorm@1024` (0.0113 to 0.0247; 0.0424 to 0.132) | 6 | 0.4% to 15% | 44% to 73% | 2% to 45% | 0% | 24% to 89% |
|  |  | 8 | 2% to 55% | 64% to 96% | 7% to 74% | 0% to 2% | 33% to 98% |
| h2d | `r1:ar` (0.028 to 0.0285; 0.139 to 0.14) | 6 | 17% to 19% | 79% to 84% | 49% to 53% | 0.1% to 0.2% | 94% to 96% |
|  |  | 8 | 62% to 66% | 94% to 95% | 81% to 85% | 4% | 99% |

Against the supervised transformers trained on the displacement error, with
or without the energy term (every budget, zero-shot on the fine set
included), the graph networks and the deterministic baselines, the Ritz
solution's relative energy gap is the lower on every instance at every p, on
every set. Every other recorded model's shares are in the summaries.

The timing (`return/timing/`): the cost table's measurements of Sec. A run
again on this host beside the Ritz timing, on the same instances (the first 32
validation instances and 8 of the fine set), with 8 October 2026's
measurements on the earlier host (`timing/`, an Intel Xeon Gold 6459C) in
brackets. The direct solve on the fine set stopped starting new solves at its
900 s budget after 7 of the 8 instances (8 on 8 October); every accuracy value
of the cost table's measurements equals 8 October's. The Ritz timing used the
host's 25 BLAS threads, as each file's `machine` records.

| seconds, median (8 October 2026 in brackets) | 3D validation | 3D fine set | 2D validation |
|---|---|---|---|
| instances, median free dofs | 32, 14,304 | 8, 112,095 | 32, 1,088 |
| network inference, cold (GPU) | 0.0492 (0.0495) | 2.15 (2.17) | 0.00319 (0.00259) |
| Ritz after assembly, by p (3D 6 to 9; 2D 6, 8) | 0.0336, 0.0529, 0.109, 0.144 | 0.541, 0.75, 1.04, 1.39 | 0.00143, 0.00206 |
| assembly of K (the repository's assembler) | 0.9 | 8.07 | 0.00947 |
| direct solve | 1.22 (0.907) | 133 (105), 7 of 8 solved | 0.00377 (0.00312) |
| conjugate gradients | 1.72 (1.24) | 26.1 (26.2) | 0.0285 (0.0237) |
| conjugate gradients to the network's accuracy | 0.292 (0.217) | 4.5 (4.26) | 0.00876 (0.00721) |

The enriched c* (Appendix 2; exploratory, not in the manuscript). Each arm's
reading (`enriched/<arm>/reading.json`) and Appendix 2's ratio per seed: in
band (IB, val3d), the median enriched relative energy gap over the smaller of
c* u's and Ritz's medians; out of distribution (F2, F5, fine3d), the median
enriched peak von Mises error over Ritz's. "Per load case" is the sensitivity
reading fixed on 27 October 2026, before the run: the same rule on the medians
over every instance and load case. For every arm it reads as the reading does.

| arm | set | ratio per seed | per load case | reading of the arm |
|---|---|---|---|---|
| `b_n1024` | IB (in band, at most 0.8) | 0.933, 0.930, 0.933 | 0.916, 0.919, 0.918 | not complementary |
|  | F2 (peak, at most 0.5) | 0.911, 0.947, 0.914 | 0.902, 0.941, 0.913 |  |
|  | F5 (peak, at most 0.5) | 0.607, 0.589, 0.622 | 0.461, 0.464, 0.567 |  |
| `s_n1024` | IB (in band, at most 0.8) | 0.932, 0.935, 0.936 | 0.922, 0.923, 0.923 | not complementary |
|  | F2 (peak, at most 0.5) | 0.937, 0.947, 0.940 | 0.911, 0.941, 0.918 |  |
|  | F5 (peak, at most 0.5) | 0.514, 0.485, 0.524 | 0.391, 0.338, 0.380 |  |
| `phase2b` | val3d (in band, at most 0.8) | 0.637, 0.727, 0.812 | 0.641, 0.744, 0.819 | not complementary |
|  | fine3d (peak, at most 0.5) | 0.698, 0.657, 0.601 | 0.699, 0.661, 0.617 |  |
| `phase2b_labels` (beyond Appendix 2) | val3d (in band, at most 0.8) | 0.989, 0.990, 0.992 | 0.989, 0.990, 0.989 | not complementary |
|  | fine3d (peak, at most 0.5) | 0.989, 0.989, 0.980 | 0.987, 0.987, 0.973 |  |
| `phase2b_mgn` (beyond Appendix 2) | val3d (in band, at most 0.8) | 0.966, 0.968, 0.969 | 0.968, 0.968, 0.969 | not complementary |
|  | fine3d (peak, at most 0.5) | 0.995, 0.999, 0.999 | 0.996, 0.999, 0.999 |  |
| `k3d_labels_knorm` (beyond Appendix 2) | val3d (in band, at most 0.8) | 0.933, 0.921, 0.928 | 0.932, 0.914, 0.922 | complementary |
|  | fine3d (peak, at most 0.5) | 0.418, 0.250, 0.408 | 0.384, 0.239, 0.322 |  |

No instance failed the identity check; every network reproduced its report at
the precheck (the transformers exactly, the graph network within 1.2e-4) and
on the whole set; the enriched solution was never worse than c* u or Ritz by
more than round-off (`bound_ok`, the largest excess 1.6e-12); no direction was
dropped in the enriched solve.
