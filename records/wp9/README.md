# records/wp9 -- wp9-pool records

## Default path against wp8-lejepa (PREREG_W9 Sec. 9)

`regression_wp8_e1_2d_base.json`, `regression_wp8_phase2b.json` and
`regression_wp8_e2_m1024.json` are the summaries
`scripts/regress_against_branch.py` wrote in the sandbox (CPU, one thread,
each side in its own process importing its own source tree; a fresh pass and
a restart pass), last on 16 October 2026 on the Stage 2 r5 code. The first two
were first run on 2 October 2026 on the Stage 0b and 0c code (`src` trees
`f300ac0c27ecaec63bca9fb0b32b2e1d4f124226` and
`710ccb32a703bb99355d0e797895698fa2155300`), with the same result; the third
is new with Stage 2 (PREREG_FINE3D Sec. 9):

| | source tree (`git rev-parse <commit>:src`) |
|---|---|
| this side | the Stage 2 r5 code: `src` = tree `e120b37da30be875147ed22b1bf05edc3557e0f7` |
| the other side | `wp8-lejepa` at `5f8e2df`: `src` = tree `5be6357b912cad058121092f274e6a322169b9f6` |

`tests/test_w9_records.py` checks that a committed `src` without local
changes is the tree named here: a change to `src` needs the regression run
again and this table updated.

- `regression_wp8_e1_2d_base.json`: a miniature of `configs/e1_2d_base.json`
  (E1's stamped base) -- 162 numbers and 2 state files, identical
  (0 differences; every state file byte-identical).
- `regression_wp8_phase2b.json`: a miniature of `configs/phase2b_v1.json`
  (E8 with labels, labels_anchor, AR and MGN; P3; WP6; E6; gate G2) -- 2,590
  numbers and 6 state files, identical.
- `regression_wp8_e2_m1024.json`: a miniature of `configs/e2_m1024.json` (E2's
  token bottleneck: E8 AR only; P3 zero-shot and, in the miniature, few-shot;
  WP6 and E6 disabled as stamped, since they probe the FE-JEPA interface; gate
  G2) -- 1,042 numbers and 2 state files, identical. Stage 2 changed the
  bottleneck (S), P3 (E8's seed offset; progress lines in its zero-shot pass)
  and the runner's checks, its r2 the supervised trainer (a per-epoch loss
  history, kept in its checkpoint), its r3 only the adjudication and its r4
  the adjudication and the retries of `git describe`; with the defaults every
  number and state is wp8-lejepa's.

Each summary names the two sides by these trees (`this_src_tree`,
`other_src_tree`: git tree ids computed from the files by
`regress_against_branch.src_tree`; Stage 0b's copies named the sandbox's paths
instead). The miniatures run their units inline (workers = 1); the
process-pool path is covered by the parallel-equals-inline tests
(`tests/test_experiments_smoke.py::test_e1_parallel_matches_serial`,
`tests/test_w9_parallel_kill.py::test_e8_ar_units_in_parallel_match_serial`).
Bitwise identity is a same-machine, same-library statement (sandbox: Python
3.11.15, torch 2.14.0+cu130 on CPU, numpy 2.4.4, scipy 1.17.1). This is what
supports evaluating E1's base states as C1's 1,024-instance arm instead of
retraining them.

## S's factor 1/64 (PREREG_W9 Sec. 2)

`scale_factor.json`: `scripts/w9_scale_factor.py` on the first 256 instances
of E1's training corpus (the generator's draws for seed 0, rebuilt with gmsh;
assembly only, no labels, no training), 2 October 2026. Per instance, the
battery's largest nodal force component max|F| (E1's decode scale) over the
sum of the absolute values of all its components sum|F| (S's): median 0.0151
(10th-90th percentile 0.0096-0.0219, i.e. 0.61-1.40 times 1/64), rank
correlation 0.67 with the instance's mesh size. 16 of these geometries meshed
again at R's mesh sizes (geometry, material and loads unchanged): from h =
0.12 to 0.025, max|F| scales by 0.213 (median over the geometries; range
0.204-0.225; h itself by 0.208), sum|F| by 1.000 (largest deviation 0.29%).

## fine3d: S's three-dimensional factor (PREREG_FINE3D Sec. 2)

`fine3d/scale_factor_3d.json`: `scripts/fine3d_scale_factor.py`, 15 October
2026, sandbox (gmsh 4.15.2; 15 min). 256 instances drawn afresh from the
three-dimensional training family's sampler (E2's corpus settings, lc uniform
in 0.0579-0.0906, one generator from seed 93000, which no corpus or set has
used; assembly only, no labels, no network): max|F| / sum|F| has median
0.00113 (10th-90th percentile 0.00068-0.00190), rank correlation 0.62 with
lc; the power of two nearest the median is 2^-10, S's factor (median 1.16
times it). 16 geometries (the wp8 post-hoc remesh geometries, generator 90000
+ g) meshed at lc 0.0906, 0.0742, 0.0579 and 0.0374: at 0.0374, max|F| is
0.186 times its 0.0906 value (median; range 0.168-0.210), sum|F| unchanged to
within 0.07%. These max|F| medians equal, to the last digit, the box's in
wp8's post-hoc records for the same geometries (`records/wp8/posthoc/amp_*.json`):
57 of the 64 meshes have the box's node counts and the other 7 differ by 1 to 21
nodes. `tests/test_fine3d_records.py`
recomputes the summary from the record's own rows and checks these facts.

## fine3d: operating characteristics (PREREG_FINE3D Sec. 6)

`fine3d/simulations.json`: `scripts/fine3d_sims.py` (fixed seed; seconds), the
source of every simulated number PREREG_FINE3D quotes: R2a's three conditions
and the R2b rule on E2's seed spreads; R2b's own rule on the Phase-2b
transformer's spreads, with what an R2a result predicts for it (`r2b`, its
sensitivity in `r2b_sensitivity`), and the R2b line as a decision, with the
transformer's spreads drawn from their three-seed uncertainty and the expected
value of each line (`r2b_line`; three seeds per arm unless a case says five);
and R3-E and R3-V on the labelled fine-tuning's spreads (and
larger ones), both arms drawn afresh, independent or correlated within a seed
(`r3`, `r3_paired`; r1's record-held reference in `r3_fixed_reference`). The
test re-runs the script and compares the bytes.

## Operating characteristics (PREREG_W9 Sec. 6-7)

`simulations.json`: `scripts/w9_sims.py` (fixed seeds; seconds on a laptop),
the source of every simulated number PREREG_W9 r3 quotes: H1 under r2's
log-normal model; H1 on E1's measured per-instance structure (E1's own
validation arrays, instance 233's blow-up included, as the reference's
validation part; per instance-seed jitter, seed noise and blow-ups elsewhere)
for the validation split alone and with IB; H2's three conditions; the
residual selection of rule 1 on F5's instances; and how often an exploratory
comparison without a true difference crosses the guard.

## The evaluation sets at full size (PREREG_W9 Sec. 3)

`ood2d_sandbox.json`: RUNBOOK_W9 step 1a (`scripts/w9_make_ood2d.py` with its
default sizes and seeds) run in the sandbox on 2 October 2026 on the Stage 0c
code: all seven sets generated and verified, no failed draw -- F1-F5 256
instances each, R 80 (16 geometries x 5 mesh sizes), IB 2,048; 3,408
instances, 5.5 min on one CPU, 0.83 GB (gmsh 4.15.2). The record session 1
writes, without the machine paths and the sandbox's git string. The instance
files are byte-reproducible on one machine (a draw regenerated hours later
was identical); session 1's manifests on the box can be compared with these
SHA-256 (equal with the same gmsh and numeric stack, else they show that the
meshes differ; either way the sets are the committed generator's draws for
these seeds, pinned by the box's own manifests).

## CPU pilot of S (Stage 0c, before the stamp)

`pilot_s_cpu/`: `scripts/w9_pilot_s.py` at toy scale on its own draws; its
README holds the pre-declared questions and red flags, what ran, and the
readings. Exploratory: nothing in PREREG_W9 depends on it.

## Phase-2's supervised states (Stage 0e)

`phase2_supervised_states.json`: the SHA-256 of the labels-only and
graph-network states at the largest budget (`labels_b1024_s{0,1,2}.pt`,
`mgn_b1024_s{0,1,2}.pt` in `runs/phase2/e8_states`), copied from
`e8_states_sha256.txt` in the Phase-2 return package of 22 September 2026
(the package's SHA-256 as received is recorded with them). Phase-2b reused
these units (`d9_restart.sup_units_from_cache`) and read these files as its
P3 shared checkpoints, but no report records their hashes. The field export
(`scripts/export_fields.py`) checks the states against this list and,
independently, by content against Phase-2b's per-instance arrays.

## The box returns (Stage 1, 11 October 2026)

The three returns are committed as received, unpacked byte for byte:

| Directory | Return (RUNBOOK_W9) | Tarball SHA-256 as received |
|---|---|---|
| `session1/` | Sec. 1f, session 1, returned on 10 October 2026 | `58148fb7ac3a2055a5529202804dd93115101e5e940aa64b149f66f032991d0e` |
| `session2/` | Sec. 2d, session 2, 10-11 October 2026 | `a47cb50ad9c2e21080e978fecc4249b2986ad61c52adfb6b5503c56d629f47dd` |
| `threads/` | Sec. 4, the threads of the CMAME paper's solvers, 11 October 2026 | `cef9d17f23069ed5baa508559cd4dcaba54ab0609f07fe0dde9d0778d565ea81` |

The trained states and the evaluation sets stay on the box; the states'
SHA-256 are in `session2/provenance.txt` and in each report, and the sets'
manifests in `session1/ood2d/`. Session 2 ran every planned arm once, in the
plan's order, each with exit 0, no restart and a solve ledger of 0. It ran
on another host than session 1, with another GPU driver, after the instance
had been shut down between the sessions; `DEVIATIONS_W9.md` (W1-W3) records
this, what the records show about its effect, and Sec. 4's threads.

## The verdict (RUNBOOK_W9 Sec. 3)

`w9_verdict.json` was written on 11 October 2026 on the stamped code (no
adjudicating file differs from `prereg-w9`; the file records
`adjudicator.git` = `prereg-w9`), with the returns in place:

    python scripts/adjudicate_w9.py --session1 records/wp9/session1 \
        --session2 records/wp9/session2 \
        --e1-report records/wp8/e1/e1_2d_base/report.json --prereg PREREG_W9.md \
        --out records/wp9/w9_verdict.json

(The two optional paths are given so that the file names its inputs relative
to the repository.) The decisions recomputed from session 1's readings were
identical; no report was refused, and the adjudication recorded no
deviation. H1 is NOT SUPPORTED and H2 SUPPORTED; the numbers are in
`paper/wp9/tables.md`, which `scripts/make_w9_paper_material.py` generates
from this file with the LaTeX tables beside it (every file in `paper/wp9/`
but `scale_lemma.tex`). `tests/test_w9_returns.py` checks the returns against
each other, re-runs the adjudication and compares it with this file,
recomputes H1 and H2 from the reports without the adjudicator's code, checks
that E1's states gave the same values on both hosts, and regenerates the
paper material byte for byte. To re-check the verdict by hand, write to a
temporary file (`--out /tmp/w9_verdict.json`), as the test does: run in a
checkout that has commits after the stamp or local changes, the adjudicator
records its own `git` string differently (`prereg-w9-...`), and only that
field may then differ.

## The evaluation sets on the box against the sandbox

The box drew all seven sets from the committed generator and seeds without a
failure, with PREREG_W9 Sec. 3's sizes and seeds and gmsh 4.15.2, as the
sandbox did (`ood2d_sandbox.json`). The sandbox's F2 manifest is the box's
byte for byte; the other six differ, while every set's smallest, median and
largest node counts are the same. So the sets regenerated on another
machine are not all byte-identical to the box's; the box's manifests, which
every run verified and recorded, are the record.

## The threads of the paper's solvers (`threads/`)

Sec. 4 ran with session 2's CPU count, driver and GPU, in an environment
that sets `OMP_NUM_THREADS` and `MKL_NUM_THREADS` to 25, not in that of the
paper's cost table (16; `DEVIATIONS_W9.md` W3). numpy and SciPy load two OpenBLAS
builds; both pools ran the environment's 25 threads, and 1 with one thread.
On the paper's first 8 three-dimensional validation instances and first 2
fine-mesh instances, the direct solve (SuperLU) took the same time with one
thread as with 25: medians 1.24 s on the validation instances and 97-98 s on
the fine ones. Conjugate gradients was faster with one thread: 1.22 s against
1.71 s, and 28.1 s against 33.6 s; the repeat in the environment, after the
one-thread run, gave 1.69 s and 32.9 s. In two dimensions every solve took
milliseconds either way. Every solution agreed with the stored labels (the
direct solve to within 1e-12 relative, conjugate gradients to within 1e-8),
and the timed model reproduced its report's arrays.

## fine3d: the box's return (Stage 3, 21 October 2026)

The return of RUNBOOK_FINE3D Sec. 2 is committed as received, unpacked byte
for byte:

| Directory | Return (RUNBOOK_FINE3D) | Tarball SHA-256 as received |
|---|---|---|
| `fine3d/return/` | Sec. 2, the session of 20-21 October 2026 (box time), returned on 21 October 2026 | `8c85f9cd71c401cabaad5ba94b244534b3c888c247038a5232fe478a3ed26bef` |

The trained and fine-tuned states stay on the box; their SHA-256 are in
`fine3d/return/provenance.txt` and in the reports. The session ran its six
steps once each, in the runbook's order, each with exit 0, from 01:29 on 20
October to 16:35 on 21 October (box time, +0800; `session/status.txt`), with
no restart, no resumed seed and no seed taken from disk; R2a's solve ledgers
read 0, and the memory events show no out-of-memory kill. R3's seeds record
one host and one GPU driver throughout (`autodl-container-45e441a24a-99d5b40d`,
595.71.05), the host the provenance file names, with an RTX 5090 and 25
CPUs. The session's suite read `704 passed, 1 skipped`
(`session/pytest.log`; RUNBOOK_FINE3D Sec. 0c, before the session; the log
itself is undated), the stamped commit's count.
`DEVIATIONS_FINE3D.md` records what the adjudication cannot see: the session
ran before R1, not after it (F1), and the return's provenance file was
written after the checkout had been switched to branch cmame-paper, so that
its git lines are not the session's (F2).

## fine3d: the verdict (RUNBOOK_FINE3D Sec. 3)

`fine3d/fine3d_verdict.json` was written on 21 October 2026 on the stamped
code, in a clean checkout of `prereg-fine3d` with the return in place
(`adjudicator.git` = `prereg-fine3d`; no adjudicating file differs from the
tag):

    python scripts/adjudicate_fine3d.py \
        --r2a-b records/wp9/fine3d/return/r2a_b_m1024/report.json \
        --r2a-s records/wp9/fine3d/return/r2a_s_m1024/report.json \
        --amp-b records/wp9/fine3d/return/posthoc/amp_r2a_b_m1024.json \
        --amp-s records/wp9/fine3d/return/posthoc/amp_r2a_s_m1024.json \
        --r3 records/wp9/fine3d/return/r3_eft_b16/report.json \
        --r3-labelled records/wp9/fine3d/return/r3_lft_b16/report.json \
        --status records/wp9/fine3d/return/session/status.txt \
        --phase2b records/wp8/e2/baseline/report_phase2b.json \
        --e2 records/wp8/e2/e2_m1024/report.json --prereg PREREG_FINE3D.md \
        --out records/wp9/fine3d/fine3d_verdict.json

(The three optional paths are given so that the file names its inputs
relative to the repository; a first run the same day, with the return
outside the repository, gave the same file but for the paths.) No report was
refused, and the adjudication recorded no deviation and no note. The
verdicts of PREREG_FINE3D Sec. 6, with rel (the relative change of the seed
means), tau (the guard, max(10%, 2 SE_rel); every tau here is 2 SE_rel) and
the per-seed values, the reference first:

- **R2a: SUPPORTED.** S against the fresh baseline, E2's M = 1,024 arm
  trained again on seeds 3-5: (i) the fine displacement error, 0.454 /
  0.511 / 0.576 and 0.037 / 0.027 / 0.029, rel -94.0%, tau 13.7%; (ii) the
  fine / in-band displacement-error ratio, 4.88 / 3.75 / 6.25 and 1.40 /
  1.10 / 1.09, rel -75.9%, tau 29.4% (the ratio of the seed means 4.79 and
  1.20); (iii) K1 on E8's in-band cell, neither worse: the energy gap,
  0.0251 / 0.0464 / 0.0236 and 0.0090 / 0.0087 / 0.0087, rel -72.3%, tau
  46.5%, and the displacement error, 0.093 / 0.136 / 0.092 and 0.027 /
  0.025 / 0.026, rel -75.8%, tau 27.1%.
- **R2b: recommended**, by Sec. 6's rule: R2a is SUPPORTED and S's fine
  displacement error is lower by 94.0%, beyond the line of 45%.
- **R3-E: NOT SUPPORTED.** The fine relative energy gap, the labelled arm
  0.078 / 4.477 / 0.088 and the energy arm 0.019 / 0.023 / 0.014, rel
  -98.8%, tau 189.3%.
- **R3-V: NOT SUPPORTED.** The fine von Mises error, 0.167 / 0.959 / 0.168
  and 0.084 / 0.093 / 0.076, rel -80.4%, tau 122.3%.
- With tau above 100%, neither R3 verdict could have been SUPPORTED: rel
  cannot fall below -100% for these non-negative metrics.
- Beside R3-E and R3-V (Sec. 6-7): the fine displacement error, the
  labelled arm's own objective, 0.052 / 0.090 / 0.055 and 0.053 / 0.059 /
  0.049, rel -18.5%, tau 38.2%, within the guard; and the labelled arm
  against the Phase-2b record of the same fine-tuning, within the guard on
  every metric, so with no flag on the training path (Sec. 7; the fine set,
  in the table below).

| Labelled arm against the record | Record, seeds 0 / 1 / 2 | Labelled arm | rel | tau |
|---|---|---|---|---|
| relative energy gap | 0.078 / 0.076 / 0.057 | 0.078 / 4.477 / 0.088 | +2103.5% | 4170.5% |
| displacement error | 0.056 / 0.050 / 0.053 | 0.052 / 0.090 / 0.055 | +24.0% | 46.5% |
| von Mises error | 0.173 / 0.177 / 0.147 | 0.167 / 0.959 / 0.168 | +160.6% | 318.8% |
| peak von Mises error | 0.386 / 0.451 / 0.330 | 0.365 / 2.209 / 0.325 | +148.4% | 319.9% |
| critical-region recall | 0.718 / 0.711 / 0.718 | 0.725 / 0.341 / 0.709 | -17.3% | 35.0% |

`tests/test_fine3d_returns.py` checks the return whole and against its own
hashes, re-runs this adjudication and compares it with the committed file,
recomputes R2a, R3-E and R3-V from the reports without the adjudicator's
code, and checks the facts quoted here, in `DEVIATIONS_FINE3D.md` and in the
Stage 3 notes. To re-check the verdict by hand, write to a temporary file
(`--out /tmp/fine3d_verdict.json`), as the test does: run in a checkout that
has commits after the stamp or local changes, the adjudicator records its
own `git` string differently (`prereg-fine3d-...`), and only that field may
then differ; where the tag `prereg-fine3d` is absent, so do its record of
the comparison with the tag and a deviation saying that it could not be
made.
