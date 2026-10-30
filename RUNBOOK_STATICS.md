# RUNBOOK -- statics-paper, commands in execution order

The box sessions that the manuscript (`paper/statics/`) needs. Roles:
**box** = the GPU machine; **repo** = code, records, pre-registration and
the manuscript.

- Sec. A: timing and field export (read only; ~1.5 h; no pre-registration).
- Sec. B: CM2D, the two-dimensional supervised networks retrained with the
  current code beside E1's label-free states, with a stiffness-norm control
  (PREREG_CM2D; ~11 h, up to ~22 h; only after PREREG_CM2D is stamped and
  tagged `prereg-cm2d`, except its readiness check B0).
- Sec. C: CM2D's adjudication (repo).
- Sec. D: the error spectra of CM2D's models (read only; ~30 min; post hoc,
  no pre-registration; after Sec. C).
- Sec. E: PREREG_HOLDOUT, the manuscript's stored states on the instances of
  its two corpora on which no recorded run or tool trained a network,
  computed a label or evaluated a network (evaluation only; ~1-1.5 h; only
  after PREREG_HOLDOUT is stamped and tagged `prereg-holdout`), and its
  adjudication in the repo.
- Sec. F: PREREG_K3D, the three-dimensional supervised transformer of
  Phase-2 retrained with the stiffness-norm loss beside Phase-2's L_D and
  Phase-2b's label-free states (~70-85 h; after Sec. E, whose h3d labels it
  reads, and only after PREREG_K3D is stamped and tagged `prereg-k3d`), and
  its adjudication in the repo.
- Sec. G: the polynomial Ritz-Galerkin baseline of the JCP revision and the
  enriched c* reading, post hoc (read only; ~4 h; after Sec. F's return),
  with the cost table's measurements run again on the same host beside the
  baseline's timing; no pre-registration (the specification of 20 October
  2026 is in BRANCH_NOTES_statics-paper.md, Stage 14).

The branch was called `cmame-paper` until 29 October 2026, when it was renamed
`statics-paper` on GitHub, its commits and tags unchanged. On the same day this runbook,
until then `RUNBOOK_CMAME.md`, the manuscript's directory `paper/cmame/`, its generator
`scripts/make_cmame_material.py` and its tests `tests/test_cmame_*.py` were renamed after
the branch, with `statics` in place of `cmame` (BRANCH_NOTES_statics-paper.md, Stage 18).
Sections A to G keep their commands as they ran, with the old names; to run Sec. A, D or
G again on a later commit, read the new names for the old. Any later section uses the new
ones.

No section writes another's files: each reads E1's or Phase-2b's states and
corpora (Sec. D also CM2D's kept states and its committed return; Sec. E all
three runs' states; Sec. F Phase-2b's and Phase-2's states and Sec. E's h3d
labels; Sec. G the states of Phase-2b, Phase-2, Sec. F, wp9's session 2 and
E1, Sec. E's labels and wp9's sets); Sec. A and B0 write only under
`runs/cmame/`, Sec. B otherwise only under `runs/cm2d/`, Sec. D only under
`runs/cmame/spectra/`, Sec. E only under `runs/holdout/`, Sec. F only under
`runs/k3d/`, Sec. G only under `runs/ritz/`; none writes to a stamped
configuration of another pre-registration, another run's `e8_states/`,
`runs/data2d` or `runs/data3d_phase2`.

## A. Timing and field export, standalone (box; ~1.5 h)

The same measurements as Sec. 4 of `RUNBOOK_W9.md` (Stages 0d-0e of
`wp9-pool`), run on their own and before PREREG_W9's stamp, with the
diagnostics of cmame-paper Stage 1 in the field export. Nothing in PREREG_W9
reads them, and they read no output of wp9's sessions; the 2D timing therefore
runs on E1's validation instances only (the OOD family F5 is made by wp9's
session 1, which has not run). When this section has returned complete, wp9's
Sec. 4 need not be repeated, except its 2D timing on F5 if wp9 wants it. It
ran on 8 October 2026 on commit `61f018f` and returned complete; the return
is in `records/cmame/timing/` (`records/cmame/README.md`).

What it measures. The manuscript's cost table: per instance, on the same
instances and this machine, the surrogate's inference (GPU, batch of one, every
load case in one pass; its accuracy on those instances recorded too) against
exact solves of the same system: the direct solve that bought every label
(SuperLU on the free block, one process), unpreconditioned conjugate gradients
to a relative residual of 1e-10 from zero, the same CG started from the
surrogate's prediction, and the same CG from zero stopped as soon as it is as
accurate as the surrogate in energy, for the raw prediction and for the
prediction rescaled by the label-free amplitude c*. 2D: E1's states on 32
validation instances (a few minutes). 3D: Phase-2b's states on 32 in-band
validation instances (about 10 min) and 8 of the fine set, whose direct solves
take several minutes and an estimated 7-10 GB of host memory each; each solver
stops starting new solves after 15 min per set (the one in progress
completes), and the surrogate is timed on every instance. Then the
manuscript's field figures, per-load energies and diagnostics: Phase-2b's
label-free, labels-only and graph-network states (seeds 0-2; the label-free
ones checked against the report, the supervised ones against
`records/wp9/phase2_supervised_states.json`, all of them also by content) on
all 256 validation instances, and three instances chosen by rules fixed in the
script (about 15-25 min, estimated). Read only: no state, corpus or report is
written; everything goes under `runs/cmame/timing/`. A failure here costs
nothing else; report it.

### A0. Preconditions (box)

A0a. The tmux session -- on its own line, outside tmux (skip it if a tmux
status bar is already showing); after a dropped connection, `tmux attach -t cm`:
```bash
tmux new -A -s cm
```

A0b. Fetch the branch (directly: on 8 October 2026, by the operator's
report, AutoDL's network route answered HTTP 503 and the direct fetch
worked; the box's clone is single-branch, hence the explicit refspec):
```bash
cd ~/autodl-tmp/FE-JEPA
( for i in 1 2 3; do git fetch origin +refs/heads/cmame-paper:refs/remotes/origin/cmame-paper && exit 0; sleep 10; done
  exit 1 ) && echo FETCH-OK || echo FETCH-FAILED
git rev-parse --short origin/cmame-paper     # the commit the operator instruction names
```
Continue only if `FETCH-OK` is printed and the commit is the named one
(an error printed by a failed first attempt before `FETCH-OK` is harmless);
otherwise stop here and report.

A0c. Checkout, checks and the suite (~7 min):
```bash
cd ~/autodl-tmp/FE-JEPA
git checkout -B cmame-paper origin/cmame-paper   # "Switched to ..." or "Reset branch ...", maybe "set up to track"
git rev-parse 'HEAD^{tree}'                  # the tree the operator instruction names
git status --porcelain --untracked-files=no  # must print nothing
df -h ~/autodl-tmp / | tail -n 2             # >= 3 GB free on the data disk and on /
pgrep -af "fejepa|spawn_main"                # must print nothing
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader   # about 0 %, under 1,000 MiB
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"   # 2.12.1+cu130 True
mkdir -p runs/cmame/timing
python -m pytest -q --deselect tests/test_cmame_material.py::test_manuscript_compiles \
    --deselect tests/test_w9_session2.py::test_paper_material_compiles \
    --deselect tests/test_cmame_references.py::test_the_bibliography_renders_the_data_reference_and_the_chapter \
    2>&1 | tee runs/cmame/timing/pytest.log | tail -n 3
```
The suite's last line reads `825 passed, 3 deselected`, then warnings and the
time (the two LaTeX builds and the bibliography test are left out: they
need a TeX installation that the box does not have). Anything failed, an
error, or another count: stop and report. Any other output than the
comments describe: stop and report.

### A1. The measurements (box; ~1.5 h; nothing else on the GPU)

First the checks, on their own:
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/cmame/timing; mkdir -p $P
( date; pgrep -af "fejepa|spawn_main"
  nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader ) 2>&1 | tee $P/precheck.txt
```
`pgrep` must print nothing and the GPU line must read about 0 % and under
1,000 MiB; otherwise stop here and report (the timings would be wrong). Then:
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/cmame/timing
[ -s $P/status.txt ] && mv $P/status.txt $P/status.txt.$(date +%Y%m%d-%H%M%S); : > $P/status.txt
run() { local log=$1; shift; [ -e $P/$log ] && mv $P/$log $P/$log.$(date +%Y%m%d-%H%M%S)
        "$@" 2>&1 | tee $P/$log; echo "$log exit=${PIPESTATUS[0]}" | tee -a $P/status.txt; }
run timing_2d.log python scripts/time_inference_vs_solve.py \
    --report records/wp8/e1/e1_2d_base/report.json --states-dir runs/e1_2d_base/e8_states \
    --out $P/timing_2d.json
run timing_3d.log python scripts/time_inference_vs_solve.py \
    --report records/wp8/e2/baseline/report_phase2b.json --states-dir runs/phase2/e8_states \
    --out $P/timing_3d.json
[ -d $P/fields ] && mv $P/fields $P/fields.$(date +%Y%m%d-%H%M%S)
run fields_3d.log python scripts/export_fields.py \
    --report records/wp8/e2/baseline/report_phase2b.json --states-dir runs/phase2/e8_states \
    --out $P/fields
( echo "HEAD $(git rev-parse HEAD)"; echo "tree $(git rev-parse 'HEAD^{tree}')"
  git status --porcelain --untracked-files=no
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
  lscpu | grep -E "^Model name|^CPU\(s\)|^Thread|^Socket"; echo "nproc $(nproc)"
  cat /sys/fs/cgroup/cpu.max /sys/fs/cgroup/memory.max 2>/dev/null; free -g | head -n 2
) > $P/machine.txt 2>&1
cat $P/status.txt
```
What to expect. Each timing step prints one line per instance (on the 3D fine
set one every few minutes: long silences there are normal), then one line per
set with the medians and the largest deviation of each solver's solution from
the stored labels (`direct_label_max_rel_dev`: round-off, below 1e-12; `cg`
and `cg_warm` below about 1e-8; the two matching kinds print `null`, they stop
short of a full solution), and last the check of the timed model against the
report's own arrays (`disp_rel_l2_max_rel_dev` and
`energy_gap_rel_max_rel_dev`, 0 or round-off). In the JSON,
`cg_match_unreached`, `cg_match_cstar_unreached` and both `*_iters_mismatch`
are 0. The field export prints a line every 16 validation instances, one line
per figure and last a summary line:
- `content_median_rel_dev` about 0 for the `ar_*` and `labels_*` states and
  about 1e-4 for the `mgn_*` ones (the graph network's CUDA reductions are not
  bitwise reproducible); `left_out` and `content_mismatch` empty;
- the figures' files `instance_00485.npz` (fig5, validation index 107),
  `instance_00130.npz` (fig6, validation index 154) and `instance_00077.npz`
  (fig7, fine-set index 77);
- under `diagnostics`, for each of `ar`, `labels` and `mgn`:
  `prop1_bound_ratio_max` at most 1 (Proposition 1's bound),
  `stress_identity_max_rel_dev` and `gap_identity_max_rel_dev` round-off
  (below about 1e-6), and `u_dirichlet_max` exactly 0.

`status.txt` must show the three steps with `exit=0`. `exit=4` from the field
export: a supervised state failed both its hash and its content check and was
left out, the rest exported; `exit=5`: a state used on its hash did not
reproduce the report's arrays. Report any of these, and any diagnostic outside
the ranges above.

### A2. Return (box; minutes)
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/cmame/timing
OUT=~/cmame_timing_return && rm -rf $OUT && mkdir -p $OUT && cp -r $P/* $OUT/
cd ~ && tar czf cmame_timing_return_$(date +%Y%m%d).tgz cmame_timing_return \
    && sha256sum cmame_timing_return_*.tgz && du -h cmame_timing_return_*.tgz
```
The tarball is a few tens of MB with the fields. Send it with the SHA-256
line; then shut the instance down without releasing it. Do not run wp9's
sessions from this branch: PREREG_W9 is not stamped.

### A3. In the repo
The return is checked (HEAD and tree against the pushed commit, the states'
and report's hashes recorded in the JSON files, the exit codes) and committed
under `records/cmame/timing/`; the manuscript's cost table, field figures and
per-load counts are then generated from it.

## B. CM2D: the 2D supervised networks retrained, with a stiffness-norm control (box; ~11-22 h)

PREREG_CM2D.md governs. One run of the stamped configuration
`configs/cm2d_v1.json` on E1's corpus, split and seeds: E1's three label-free
states evaluated (not trained; each checked by SHA-256), and the supervised
grid trained with the current code -- the labels-only transformer and the same
transformer trained on the relative stiffness-norm error at 16, 64, 256 and
1,024 labels, the graph network at 64 and 1,024, and the naive rows.
2,284,800 supervised steps in 30 units on three workers: about 11 h if the
graph network's step is as long as the transformer's, 18-22 h at two to three
times as long, which may well be the case (not measured; PREREG_CM2D Sec. 7).
The instance's balance must cover at least 30 h (more is safer: no training
step has been timed on the instance's current host). Everything is written
under `runs/cm2d/`. The branch is frozen from the stamp until the return: the
checkout must be exactly the tagged commit. Before the operator instruction
is sent, the repo side checks the remote:
`git ls-remote origin refs/heads/cmame-paper 'refs/tags/*'` shows the branch
at the stamped commit and, of all tags, only `refs/tags/prereg-cm2d^{}` at
that commit (PREREG_CM2D Sec. 6: no other tag on it). It ran on 8-9
October 2026 on the stamped commit `094c804`, one attempt, exit 0, and
returned complete; the return and the verdict are in `records/cmame/cm2d/`
(`records/cmame/README.md`).

### B0. Readiness (box; optional, after A2 or on any visit before the stamp; read only; ~10 min)
The checks of B2 without the tag and the stamp, on the commit the operator
instruction names for B0, which must contain `scripts/cm2d_precheck.py`
(Stage 1's commit `58f079f`, on which Sec. A was first planned, does not;
Sec. A and B0 both ran on Stage 3's, `61f018f`).
They also evaluate E1's three states on the validation split and train two
steps that are not kept, so a FAIL here changes the plan before the stamp
instead of after it. Nothing else may run meanwhile (not during A1).
```bash
cd ~/autodl-tmp/FE-JEPA
( for i in 1 2 3; do git fetch origin +refs/heads/cmame-paper:refs/remotes/origin/cmame-paper && exit 0; sleep 10; done
  exit 1 ) && echo FETCH-OK || echo FETCH-FAILED
git checkout -B cmame-paper origin/cmame-paper   # "Switched to ..." or "Reset branch ...", maybe "set up to track"
git rev-parse --short HEAD                   # the commit the operator instruction names for B0
git status --porcelain --untracked-files=no  # must print nothing
P=runs/cmame; mkdir -p $P
python scripts/cm2d_precheck.py --pre-stamp --out $P/cm2d_ready.json 2>&1 \
    | tee $P/cm2d_ready.log | grep -v '^\[dry-run\] {'
```
What you see: a `[dry-run] prereg guard would refuse: ... unstamped ...`
line, a banner (`=== fejepa v2 run: configs/cm2d_v1.json | ...`), a
`[plan] steps by experiment: {'e8': 2284800, 'total': 2284800}` line, a
`[sup:none] step 2/2 (100%) knorm=...` line (the two training steps),
possibly torch `UserWarning` blocks (harmless), then one `[precheck]` line
per check: `info` for `tag` (it may read `fatal: No names found ...`),
`report_git`, `head` and `stamp`, `ok` for every other check, and last
`GO`. Send `runs/cmame/cm2d_ready.log` beside the Sec. A tarball (or on its
own). A traceback, or a last line other than `GO` / `STOP: ...`, counts as
STOP.

### B1. Preconditions (box)

B1a. The tmux session -- on its own line, outside tmux (skip it if a tmux
status bar is already showing); after a dropped connection, `tmux attach -t cm`:
```bash
tmux new -A -s cm
```

B1b. Fetch the branch and the tag (directly, as in A0b; the tag's refspec is
forced, so that a stale local tag of that name is replaced):
```bash
cd ~/autodl-tmp/FE-JEPA
( for i in 1 2 3; do git fetch origin +refs/heads/cmame-paper:refs/remotes/origin/cmame-paper +refs/tags/prereg-cm2d:refs/tags/prereg-cm2d && exit 0; sleep 10; done
  exit 1 ) && echo FETCH-OK || echo FETCH-FAILED
git rev-parse --short origin/cmame-paper     # the commit the operator instruction names
git rev-parse --short 'prereg-cm2d^{commit}' # the same commit
```
Continue only if `FETCH-OK` is printed and both lines are the named commit
(an error printed by a failed first attempt before `FETCH-OK` is harmless);
otherwise stop here and report.

B1c. Checkout, checks and the suite (~5 min):
```bash
cd ~/autodl-tmp/FE-JEPA
git checkout -B cmame-paper origin/cmame-paper   # "Switched to ..." or "Reset branch ...", maybe "set up to track"
git describe --tags --match prereg-cm2d      # must print exactly: prereg-cm2d
git rev-parse 'HEAD^{tree}'                  # the tree the operator instruction names
git status --porcelain --untracked-files=no  # must print nothing
df -h ~/autodl-tmp / | tail -n 2             # >= 7 GB free on the data disk, >= 3 GB on /
pgrep -af "fejepa|spawn_main|scripts/[A-Za-z0-9_]+\.py"   # must print nothing
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader   # about 0 %, under 1,000 MiB
grep oom_kill /sys/fs/cgroup/memory.events 2>/dev/null   # note the number: B2' compares with it
mkdir -p runs/cm2d
python -m pytest -q --deselect tests/test_cmame_material.py::test_manuscript_compiles \
    --deselect tests/test_w9_session2.py::test_paper_material_compiles \
    --deselect tests/test_cmame_references.py::test_the_bibliography_renders_the_data_reference_and_the_chapter \
    2>&1 | tee runs/cm2d/pytest.log | tail -n 3
```
The suite's last line reads `514 passed, 2 deselected`, then warnings and the time
(the suite of the tagged commit, as `records/cmame/cm2d/return/pytest.log`
records it; the third `--deselect` names a later test and deselects nothing).
Anything failed, an error, another count, or any other output than the
comments describe: stop and report.

### B2. Checks and the run (box; ~11-22 h; nothing else on the GPU)
The checks (~10 min; they evaluate E1's states and train two steps that are
not kept):
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/cm2d
for f in precheck.json precheck.log; do [ -e $P/$f ] && mv $P/$f $P/$f.$(date +%Y%m%d-%H%M%S); done
python scripts/cm2d_precheck.py --out $P/precheck.json 2>&1 \
    | tee $P/precheck.log | grep -v '^\[dry-run\] {'
```
What you see: `[prereg] verified against PREREG_CM2D.md: <12 hex>...`, the
banner and the `[plan]` line, the `[sup:none] step 2/2 (100%) knorm=...`
line, possibly torch `UserWarning` blocks (harmless), then one `[precheck]`
line per check: `info` for `head`, `ok` for every other check, and last `GO`.
On `STOP: ...` (or a traceback, or another last line): stop here, send
`runs/cm2d/precheck.log`, and shut the instance down without releasing it. On
`GO`, in the same window (the run uses up the GO: pasting this block again
prints the STOP line and starts nothing):
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/cm2d
run() { local log=$1; shift; [ -e $P/$log ] && mv $P/$log $P/$log.$(date +%Y%m%d-%H%M%S)
        echo "$log start $(date -u +%FT%TZ)" >> $P/status.txt
        "$@" 2>&1 | tee $P/$log; echo "$log exit=${PIPESTATUS[0]}" | tee -a $P/status.txt; }
grep -q '"go": true' $P/precheck.json 2>/dev/null || echo "STOP: no unused GO in $P/precheck.json -- nothing started"
grep -q '"go": true' $P/precheck.json 2>/dev/null && mv $P/precheck.json $P/precheck.json.used && run run.log python -m fejepa.cli run-config configs/cm2d_v1.json
```
Normal signs:
- the log starts with `[prereg] verified against PREREG_CM2D.md` and
  `[plan] steps by experiment: {'e8': 2284800, 'total': 2284800}`; torch
  `UserWarning` blocks (sparse tensors, a tensor converted to a scalar) are
  harmless, as in E1's log;
- the labelling stage only checks the labels (no solves);
  `[E8 (AR pretrain)] starting: 3 units` evaluates E1's states in minutes;
- `[E8 (supervised grid)] starting: 30 units`, then for each finished unit a
  line from its worker (`[sup:none E8 labels b16 s0] step 3200/3200 (100%)
  disp=...`, `... knorm=...` for the stiffness-norm row) and one from the
  run (`[E8 (supervised grid)] k/30 ... | labels b16 s0`); the 1,024-label
  transformer units take about 3 h each and the graph network's possibly
  6-9 h, so hours without a new line are normal;
- at the end, in this order: `runs/cm2d/report.json`, `RESULTS.md`, a figure,
  a `gate G1'` line that reads `passed=False` (it always does here: it is not
  a CM2D verdict), and the solve ledger with `'total': 0`;
- `status.txt` shows `run.log start ...` and `run.log exit=0`.

### B2'. Health check (any time; a second tmux window: Ctrl-b c; back: Ctrl-b 0)
```bash
cd ~/autodl-tmp/FE-JEPA; date; tail -n 2 runs/cm2d/run.log; tail -n 2 runs/cm2d/status.txt
pgrep -af "fejepa.cli run-config" | cut -c1-120; echo "workers: $(pgrep -fc spawn_main)"
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
find runs/cm2d/e8_states -type f -mmin -30 -printf '%TH:%TM %f\n' | sort | tail -n 6
grep -h oom_kill /sys/fs/cgroup/memory.events 2>/dev/null; df -h ~/autodl-tmp / | tail -n 2
```
Healthy: one `run-config` process; `workers: 3`; the GPU in use (memory well
above 1,000 MiB); `oom_kill` unchanged since B1c (or since B3 after a box
restart); a file under `e8_states/` written within the last 30 min (the
units' epoch checkpoints, every 5-6 min). Also normal -- check again 15 min
later: before `[E8 (supervised grid)] starting: 30 units` and for a few
minutes after it, `find` prints `No such file or directory` or nothing (E1's
states are only evaluated); after `[E8 (supervised grid)] done in`,
`workers: 0` and the GPU nearly idle for a few minutes (naive rows, report).
Once `status.txt` shows `run.log exit=`, the run has ended: go to B3 or B4,
not here. Otherwise: Ctrl-C in window 0, wait for the prompt, send this
output plus `tail -n 60 runs/cm2d/run.log`; then B4 (return) and shut the
instance down without releasing it; do not restart.

### B3. Interruptions and crashes
- A dropped connection: `tmux attach -t cm`; the run goes on.
- If `runs/cm2d/report.json` exists, the run has finished: do not restart,
  whatever happened afterwards; go to B4.
- The box restarted, or the run ended with an exit other than 0, and there
  is no report (after a Ctrl-C of yours under B2': B4, no restart): read
  `tail -n 30 runs/cm2d/run.log; tail -n 3 runs/cm2d/status.txt; grep oom_kill /sys/fs/cgroup/memory.events`.
  If the log mentions `out of memory` or `a worker process died`, or the
  status file shows `exit=137`, or `oom_kill` rose (it starts again from 0
  after a box restart): do not restart; go to B4 and report. Otherwise
  restart once as below. (After a worker's death the run's own message ends
  "restart the run with --reuse-states": this rule takes precedence.)
- Never delete `runs/cm2d/e8_states/`, the report, a log or `status.txt`.

The restart keeps the finished units (from the unit cache) and the
interrupted ones (up to three, from their epoch checkpoints); E1's states are
checked and evaluated again; all of it is recorded in the report. Open tmux
again (B1a) and run `pgrep -af fejepa.cli`: if it prints a line, the run is
still going -- back to B2', no restart. Note the `oom_kill` number again (B2'
compares with it from now on). Then the checks for a restart (the checkout,
the GPU, and that no report exists):
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/cm2d
for f in precheck_restart.json precheck_restart.log; do [ -e $P/$f ] && mv $P/$f $P/$f.$(date +%Y%m%d-%H%M%S); done
python scripts/cm2d_precheck.py --restart --out $P/precheck_restart.json 2>&1 \
    | tee $P/precheck_restart.log | grep -v '^\[dry-run\] {'
```
On `GO` (read as in B2), the restart (it uses up the GO as in B2):
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/cm2d
run() { local log=$1; shift; [ -e $P/$log ] && mv $P/$log $P/$log.$(date +%Y%m%d-%H%M%S)
        echo "$log start $(date -u +%FT%TZ)" >> $P/status.txt
        "$@" 2>&1 | tee $P/$log; echo "$log exit=${PIPESTATUS[0]}" | tee -a $P/status.txt; }
grep -q '"go": true' $P/precheck_restart.json 2>/dev/null || echo "STOP: no unused GO in $P/precheck_restart.json -- not restarted"
grep -q '"go": true' $P/precheck_restart.json 2>/dev/null && mv $P/precheck_restart.json $P/precheck_restart.json.used && run run.log python -m fejepa.cli run-config configs/cm2d_v1.json --reuse-states
```
If the checks print STOP, or the restarted run fails again: go to B4 and
report.

### B4. Return (box; minutes)
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/cm2d
T=$(date +%Y%m%d-%H%M)
OUT=~/cm2d_return && rm -rf $OUT && mkdir -p $OUT
cp $P/report.json $P/RESULTS*.md $P/figure1_energy_gap*.png $P/status.txt $P/precheck* \
    $P/pytest.log $P/run.log* $OUT/ 2>/dev/null
( echo "HEAD $(git rev-parse HEAD)"; echo "tree $(git rev-parse 'HEAD^{tree}')"
  echo "describe $(git describe --tags --match prereg-cm2d)"
  echo "describe-all $(git describe --always --dirty --tags)"
  echo "--- git status --porcelain ---"; git status --porcelain | grep -v '^?? runs/' | head -40
  python -c "import torch; print('torch', torch.__version__, torch.cuda.is_available())"
  echo "--- report ---"; sha256sum $P/report.json
  echo "--- states ---"; ls -l --full-time $P/e8_states/*.pt
  sha256sum $P/e8_states/*.pt runs/e1_2d_base/e8_states/ar_*.pt
  nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv,noheader
  echo "hostname $(hostname)"; echo "nproc $(nproc)"
  cat /sys/fs/cgroup/memory.events 2>/dev/null; df -h ~/autodl-tmp / | tail -n 2
) > $OUT/provenance.txt 2>&1
cd ~ && tar czf cm2d_return_$T.tgz cm2d_return \
    && sha256sum cm2d_return_$T.tgz && du -h cm2d_return_$T.tgz
```
Send the tarball with the SHA-256 line (a few MB). The states stay on the box
(their SHA-256 are in the provenance file); then shut the instance down
without releasing it.

## C. CM2D's adjudication (repo)
In a checkout of the branch (a clone of its own, not a copy of a worktree),
with the tag fetched by a forced refspec, so that a stale local tag of that
name cannot remain:
```bash
git fetch origin +refs/heads/cmame-paper:refs/remotes/origin/cmame-paper +refs/tags/prereg-cm2d:refs/tags/prereg-cm2d
git rev-parse 'prereg-cm2d^{commit}'         # the stamped commit
git tag --points-at 'prereg-cm2d^{commit}'   # exactly one line: prereg-cm2d
git checkout -B cmame-paper origin/cmame-paper   # frozen at the stamped commit until the return
git describe --tags --match prereg-cm2d      # exactly: prereg-cm2d
git status --porcelain --untracked-files=no  # must print nothing
python scripts/adjudicate_cm2d.py --return <the unpacked cm2d_return> \
    --out records/cmame/cm2d/verdict.json
```
It reads the report, `status.txt`, `provenance.txt` and the run logs from the
return, E1's report from `records/wp8/e1/`, July's from `records/phase1/`
(descriptive only) and PREREG_CM2D.md, checks the recorded commit and tree
against the tag `prereg-cm2d`, and writes H1, H2a and H2b per PREREG_CM2D
Sec. 4, the reading H3, the secondary readings of Sec. 5, the label-free row's
reuse checks and the deviations, with every input's SHA-256 and the
adjudicating code's. The return is committed under `records/cmame/cm2d/` with
the verdict. It ran on 9 October 2026 (`records/cmame/README.md`).

## D. The error spectra of CM2D's models, post hoc (box; ~30 min)

What it measures. CM2D's H2b changed only the norm of the supervised loss,
from the relative Euclidean displacement error (L_D, row `labels`) to the
relative stiffness-norm error (L_K, row `labels_knorm`), and the von Mises
error halved. By the manuscript's Corollary "Modewise contraction", the
energy norm weights the error in each eigenmode of the stiffness matrix by
its eigenvalue and the Euclidean norm weights all modes equally. This section
measures how each model's error is spread over those modes: the free
stiffness block of each of the 256 validation instances is diagonalised once
(at most about 3,600 free dofs), and every model's error on every load case
is projected on its eigenvectors, for CM2D's kept states at 1,024 labels
(L_D, L_K and the graph network, seeds 0-2) and E1's three label-free states;
the spectra are binned by each mode's stiffness relative to the solution's
own Rayleigh quotient (and, for completeness, by mode rank). Every model
predicts each instance twice: as in the run, with TF32 products, and once
more with TF32 off, so that the rounding of TF32, which falls in the stiff
modes, is measured beside the errors.
Also recorded per load case: the error's Euclidean and stiffness norms, the
von Mises errors, the energies and checks of the manuscript's identities.
Specified after CM2D's verdict: post hoc, reported only; no verdict reads it
and nothing in PREREG_CM2D does. Read only: every state's SHA-256 is checked
against CM2D's return (`records/cmame/cm2d/return/provenance.txt`) before
any model runs, every model is also checked against the report's
per-instance arrays, and everything goes under `runs/cmame/spectra/`. A
failure here costs nothing else; report it. It ran on 9 October 2026 on
commit `8b5d443`, exit 0 (the export's timed part 70 s, the tarball 22.7 MB),
and returned complete; the return is in `records/cmame/spectra/`
(`records/cmame/README.md`).

### D0. Preconditions (box)

D0a. The tmux session -- on its own line, outside tmux (skip it if a tmux
status bar is already showing); after a dropped connection, `tmux attach -t cm`:
```bash
tmux new -A -s cm
```

D0b. Fetch the branch (directly, as in A0b):
```bash
cd ~/autodl-tmp/FE-JEPA
( for i in 1 2 3; do git fetch origin +refs/heads/cmame-paper:refs/remotes/origin/cmame-paper && exit 0; sleep 10; done
  exit 1 ) && echo FETCH-OK || echo FETCH-FAILED
git rev-parse --short origin/cmame-paper     # the commit the operator instruction names
```
Continue only if `FETCH-OK` is printed and the commit is the named one (an
error printed by a failed first attempt before `FETCH-OK` is harmless). If
nothing at all is printed for 10 min, press Ctrl-C (then neither line
appears) and take the bundle route. On
`FETCH-FAILED` (later on 8 October 2026, at B1b, the direct fetch timed out
and CM2D's operator fetched from a git bundle): upload the bundle that the
operator instruction sends to `~/cmame-paper.bundle` and run, in place of
the first block:
```bash
cd ~/autodl-tmp/FE-JEPA
sha256sum ~/cmame-paper.bundle               # the SHA-256 the operator instruction names
git fetch ~/cmame-paper.bundle +refs/heads/cmame-paper:refs/remotes/origin/cmame-paper && echo FETCH-OK || echo FETCH-FAILED
git rev-parse --short origin/cmame-paper     # the commit the operator instruction names
```
Continue only if the SHA-256 is the named one, `FETCH-OK` is printed and the
commit is the named one; otherwise stop here and report. (Repo side: the
bundle is made from the pushed branch with
`git bundle create cmame-paper.bundle 094c804..cmame-paper`, the stamped
commit being on the box since Sec. B; `git bundle list-heads` shows
`refs/heads/cmame-paper` at the named commit.)

D0c. Checkout, checks and the suite (~7 min):
```bash
cd ~/autodl-tmp/FE-JEPA
git checkout -B cmame-paper origin/cmame-paper   # "Switched to ..." or "Reset branch ...", maybe "set up to track" or "up to date"
git rev-parse 'HEAD^{tree}'                  # the tree the operator instruction names
git status --porcelain --untracked-files=no  # must print nothing
ls runs/cm2d/e8_states/*_b1024_s*.pt runs/e1_2d_base/e8_states/ar_p1024_s*.pt | wc -l   # 12
df -h ~/autodl-tmp / | tail -n 2             # >= 5 GB free on the data disk and on / (the suite needs 5)
pgrep -af "fejepa|spawn_main|scripts/[A-Za-z0-9_]+\.py"   # must print nothing
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader   # about 0 %, under 1,000 MiB
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"   # 2.12.1+cu130 True
mkdir -p runs/cmame/spectra
python -m pytest -q --deselect tests/test_cmame_material.py::test_manuscript_compiles \
    --deselect tests/test_w9_session2.py::test_paper_material_compiles \
    --deselect tests/test_cmame_references.py::test_the_bibliography_renders_the_data_reference_and_the_chapter \
    2>&1 | tee runs/cmame/spectra/pytest.log | tail -n 3
```
The suite's last line reads `825 passed, 3 deselected`, then warnings and the
time. Anything failed, an error, another count, or any other output than the
comments describe: stop and report.

### D1. The export (box; ~10 min; nothing else on the GPU)
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/cmame/spectra
[ -s $P/status.txt ] && mv $P/status.txt $P/status.txt.$(date +%Y%m%d-%H%M%S); : > $P/status.txt
run() { local log=$1; shift; [ -e $P/$log ] && mv $P/$log $P/$log.$(date +%Y%m%d-%H%M%S)
        "$@" 2>&1 | tee $P/$log; echo "$log exit=${PIPESTATUS[0]}" | tee -a $P/status.txt; }
[ -d $P/export ] && mv $P/export $P/export.$(date +%Y%m%d-%H%M%S)
run spectra.log python scripts/cm2d_spectra.py --report records/cmame/cm2d/return/report.json \
    --provenance records/cmame/cm2d/return/provenance.txt --states-dir runs/cm2d/e8_states \
    --out $P/export --device cuda
( echo "HEAD $(git rev-parse HEAD)"; echo "tree $(git rev-parse 'HEAD^{tree}')"
  git status --porcelain --untracked-files=no
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
  lscpu | grep -E "^Model name|^CPU\(s\)|^Thread|^Socket"; echo "nproc $(nproc)"
  cat /sys/fs/cgroup/cpu.max /sys/fs/cgroup/memory.max 2>/dev/null; free -g | head -n 2
) > $P/machine.txt 2>&1
cat $P/status.txt
```
What to expect: possibly torch `UserWarning` blocks (harmless), a line every
16 validation instances (`[spectra] val 16/256 | ... s`), one line for the
figure instance, `[spectra] fig2d: val #221 instance_27356.npz (... nodes)`,
and last a summary line with six keys:
- `content_median_rel_dev` (two numbers per state) about 0 for the `ar_*`,
  `labels_*` and `labels_knorm_*` states; for the `mgn_*` ones small but not
  necessarily 0 (the graph network's CUDA reductions are not bitwise
  reproducible: about 1e-4 in 3D in Sec. A; a median above 1e-3 ends with
  exit 5); `content_mismatch` empty;
- `prop1_bound_ratio_max` at most 1 for every row (Proposition "Energy gap
  and stress error");
- `rayleigh_ratio_median` and `pairs`: the readings themselves; no range is
  expected of them;
- `figures`: `{"fig2d": ["instance_27356.npz", 221]}`.

`status.txt` must show `spectra.log exit=0`. `exit=5`: a model did not
reproduce the report's arrays (everything else is written). `exit=1` with a
message naming a file and its SHA-256: a refusal, before anything is
measured or written under `export/`. Any other exit, or `exit=1` with a
traceback or another message: send `spectra.log`. Report any of these, and
any reading outside the ranges above (a `prop1_bound_ratio_max` above 1, a
transformer's deviation that is not about 0); in every case go on to D2:
the return carries the logs and whatever was written.

### D2. Return (box; minutes)
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/cmame/spectra
T=$(date +%Y%m%d-%H%M)
OUT=~/cm2d_spectra_return && rm -rf $OUT && mkdir -p $OUT && cp -r $P/* $OUT/
cd ~ && tar czf cm2d_spectra_return_$T.tgz cm2d_spectra_return \
    && sha256sum cm2d_spectra_return_$T.tgz && du -h cm2d_spectra_return_$T.tgz
```
The tarball is about 35 MB. Send it with the SHA-256 line; then shut the
instance down without releasing it.

### D3. In the repo
The return is checked (HEAD and tree against the pushed commit, the states'
and the report's hashes recorded in `spectra.json`, the exit code, the
identities on every array, and, end to end, the verdict: the pair
`labels_vs_labels_knorm`'s ratios of means of the relative gap and of the
von Mises error agree with `base_mean / new_mean` of H2a and H2b in
`records/cmame/cm2d/verdict.json`, 4.596 and 2.215, to round-off when both
rows' content deviations are 0) and committed under
`records/cmame/spectra/`; the manuscript's reading of the errors' spectral
content is then generated from it.

## E. PREREG_HOLDOUT: the stored states on the never-used instances (box; ~1.5 h)
The manuscript's networks, unchanged, on the instances of its two corpora on
which no recorded run or tool trained a network, computed a label or
evaluated a network (PREREG_HOLDOUT Sec. 2): 686 of `runs/data3d_phase2`
after the first 1,024 of its pool, and 4,111 of `runs/data2d` after the
first 25,600 of its pool (the configuration lists the few instances of
those tails that are left out). Each set is first labelled (one exact solve
per instance, into `runs/holdout/<set>/labels/`; the corpus files are only
read), then every state is checked by SHA-256 and by content on its run's
validation split and evaluated on the set. Nothing trains. Only after
PREREG_HOLDOUT is stamped and tagged `prereg-holdout`: the script refuses to
run otherwise. It reads Phase-2b's, E1's and CM2D's states and the two
corpora, and writes only under `runs/holdout/`. Before the operator
instruction is sent, the repo side checks the remote:
`git ls-remote origin refs/heads/cmame-paper 'refs/tags/*'` shows the branch
at the stamped commit and, of all tags, only `refs/tags/prereg-holdout^{}`
at that commit (PREREG_HOLDOUT Sec. 7: no other tag on it). It ran on 21
October 2026 on the stamped commit `69fb698`, each stage in its second attempt
(the first attempts, on commit `8b5d443`, exited 2), and returned complete;
the return and the verdict are in `records/cmame/holdout/`
(`records/cmame/README.md`).

### E0. Preconditions (box)

E0a. The tmux session -- on its own line, outside tmux (skip it if a tmux
status bar is already showing); after a dropped connection, `tmux attach -t cm`:
```bash
tmux new -A -s cm
```

E0b. The repository's address, then the branch and the tag. Since 11 October
2026 the repository is `RuifengCao/label-free-fe-surrogates` (the old
address forwards; the box's remote is set to the new one, once), and the
tag's refspec is forced, so that a stale local tag of that name is replaced:
```bash
cd ~/autodl-tmp/FE-JEPA
git remote set-url origin https://github.com/RuifengCao/label-free-fe-surrogates.git
git remote get-url origin                    # https://github.com/RuifengCao/label-free-fe-surrogates.git
( for i in 1 2 3; do git fetch origin +refs/heads/cmame-paper:refs/remotes/origin/cmame-paper +refs/tags/prereg-holdout:refs/tags/prereg-holdout && exit 0; sleep 10; done
  exit 1 ) && echo FETCH-OK || echo FETCH-FAILED
git rev-parse --short origin/cmame-paper     # the commit the operator instruction names
git rev-parse --short 'prereg-holdout^{commit}'   # the same commit
```
Continue only if `FETCH-OK` is printed and both lines are the named commit
(an error printed by a failed first attempt before `FETCH-OK` is harmless).
If nothing at all is printed for 10 min, or the fetch has not ended after
20 min, press Ctrl-C (then `FETCH-OK` does not appear; ignore any lines
printed after it) and take the bundle route. On `FETCH-FAILED`: upload the bundle
that the operator instruction sends to `~/cmame-paper.bundle` and run, in
place of the fetch block:
```bash
cd ~/autodl-tmp/FE-JEPA
sha256sum ~/cmame-paper.bundle               # the SHA-256 the operator instruction names
git fetch ~/cmame-paper.bundle +refs/heads/cmame-paper:refs/remotes/origin/cmame-paper +refs/tags/prereg-holdout:refs/tags/prereg-holdout && echo FETCH-OK || echo FETCH-FAILED
git rev-parse --short origin/cmame-paper     # the commit the operator instruction names
git rev-parse --short 'prereg-holdout^{commit}'   # the same commit
```
Continue only if the SHA-256 is the named one, `FETCH-OK` is printed and
both lines are the named commit; otherwise stop here and report. (Repo side:
the bundle is made from the pushed branch and tag with
`git bundle create cmame-paper.bundle 8b5d443..cmame-paper prereg-holdout`,
Sec. D's commit `8b5d443` being on the box; `git bundle list-heads` shows
`refs/heads/cmame-paper` at the named commit and `refs/tags/prereg-holdout`
at the annotated tag's own object, which peels to that commit.)

E0c. Checkout, checks and the suite (~7 min):
```bash
cd ~/autodl-tmp/FE-JEPA
git checkout -B cmame-paper origin/cmame-paper   # "Switched to ..." or "Reset branch ...", maybe "set up to track" or "up to date"
git describe --tags --match prereg-holdout   # must print exactly: prereg-holdout
git rev-parse 'HEAD^{tree}'                  # the tree the operator instruction names
git status --porcelain --untracked-files=no  # must print nothing
ls runs/phase2/e8_states/{ar_p1024,labels_b1024,mgn_b1024}_s*.pt runs/e1_2d_base/e8_states/ar_p1024_s*.pt \
    runs/cm2d/e8_states/*_b1024_s*.pt | wc -l   # 21
python -c "from fejepa.analysis.holdout import load_spec, check_states; s = load_spec('configs/holdout_v1.json'); [check_states(v, s['seeds']) for v in s['sets'].values()]; print('21 states verified')"   # 21 states verified
python -c "from pathlib import Path; from fejepa.analysis.holdout import load_spec, holdout_names; s = load_spec('configs/holdout_v1.json'); [print(k, sum((Path(v['corpus']) / f).is_file() for f in holdout_names(v)), v['n_holdout']) for k, v in s['sets'].items()]"   # h3d 686 686, then h2d 4111 4111
ls runs/holdout/status.txt 2>/dev/null || echo "no E1 yet"   # on the first visit: no E1 yet
df -h ~/autodl-tmp / | tail -n 2             # >= 5 GB free on the data disk and on / (the suite needs 5)
pgrep -af "fejepa|spawn_main|scripts/[A-Za-z0-9_]+\.py"   # must print nothing
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader   # about 0 %, under 1,000 MiB
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"   # 2.12.1+cu130 True
mkdir -p runs/holdout
[ -e runs/holdout/pytest.log ] && mv runs/holdout/pytest.log runs/holdout/pytest.log.$(date +%Y%m%d-%H%M%S)
python -m pytest -q --deselect tests/test_cmame_material.py::test_manuscript_compiles \
    --deselect tests/test_w9_session2.py::test_paper_material_compiles \
    --deselect tests/test_cmame_references.py::test_the_bibliography_renders_the_data_reference_and_the_chapter \
    2>&1 | tee runs/holdout/pytest.log | tail -n 3
```
The suite's last line reads `684 passed, 3 deselected`, then warnings and the
time. Anything failed, an error, another count, or any other output than the
comments describe: stop and report. (`runs/holdout/status.txt` printed on a
later visit, after an interrupted E1: go to E1' instead of E1.) The line
`21 states verified` means that every state has the SHA-256 that the
configuration records. Otherwise that command prints a traceback whose last
line begins `ValueError: states refused:` and names the refused states of
the first set that has one, and the rest of the block still runs to its
end: then stop and report, before anything is labelled.

### E1. The run (box; ~1.5 h; nothing else on the GPU)
First the checks, on their own:
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/holdout
( date; hostname; pgrep -af "fejepa|spawn_main|scripts/[A-Za-z0-9_]+\.py"
  nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader ) 2>&1 | tee -a $P/precheck.txt
```
`pgrep` must print nothing and the GPU line must read about 0 % and under
1,000 MiB; otherwise stop here and report. Then, in the same window:
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/holdout
touch $P/status.txt
run() { local log=$1; shift; [ -e $P/$log ] && mv $P/$log $P/$log.$(date +%Y%m%d-%H%M%S)
        echo "$log start $(date -u +%FT%TZ) $(hostname)" >> $P/status.txt
        "$@" 2>&1 | tee $P/$log; echo "$log exit=${PIPESTATUS[0]}" | tee -a $P/status.txt; }
run label_h3d.log python scripts/holdout_run.py --config configs/holdout_v1.json --set h3d --stage label --device cuda
run eval_h3d.log python scripts/holdout_run.py --config configs/holdout_v1.json --set h3d --stage eval --device cuda
run label_h2d.log python scripts/holdout_run.py --config configs/holdout_v1.json --set h2d --stage label --device cuda
run eval_h2d.log python scripts/holdout_run.py --config configs/holdout_v1.json --set h2d --stage eval --device cuda
( echo "HEAD $(git rev-parse HEAD)"; echo "tree $(git rev-parse 'HEAD^{tree}')"
  git status --porcelain --untracked-files=no
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
  lscpu | grep -E "^Model name|^CPU\(s\)|^Thread|^Socket"; echo "nproc $(nproc)"
  echo "hostname $(hostname)"
  cat /sys/fs/cgroup/cpu.max /sys/fs/cgroup/memory.max 2>/dev/null; free -g | head -n 2
) >> $P/machine.txt 2>&1
cat $P/status.txt
```
`status.txt` is never deleted or rotated: it keeps a start line and an exit
line per attempt. Do not press Ctrl-C in this window while the block runs: it
stops only the stage in progress, which is then left without an exit line,
and the block goes on with the next stage.

What to expect, per set:
- `label`: a line every 64 instances (`[holdout] h3d labels 64/686 | ... s`),
  then one summary line: `"n": 686` (h3d) or `4111` (h2d), `"reused": 0`,
  `"solves": 2744` or `16444`, `"kept": false`, `"residual_max"` of order 1e-11
  (up to about 1e-10; the script refuses a label above 1e-8),
  `"source_labelled": 0`. About 35-40 min for h3d (an instance can take half a
  minute), 5-10 min for h2d. A labelling run again after an
  interruption counts the labels it kept under `"reused"` and solves only the
  others; one that finds every label prints `[holdout] h3d labels unchanged:
  ... kept as it was` and `"reused"` equal to `"n"`, `"solves": 0`,
  `"kept": true`.
- `eval`: possibly torch `UserWarning` blocks (harmless), a line every 32
  validation instances (`[holdout] h3d val 32/256 | ... s`) and every 32
  holdout instances, then one summary line: `content_median_rel_dev` (two
  numbers per state) about 0 for the transformer states (`ar_*`, `labels_*`,
  `labels_knorm_*`), small but not necessarily 0 for the graph-network ones
  (`mgn_*`: about 1e-4, as in Sec. A); `content_mismatch` empty; the
  per-state means (`summary`) and the load cases worse than the zero field
  (`worse_than_zero`, each with `"sign_mismatch": 0`). About 25 min for h3d
  and 10-20 min for h2d.

`status.txt` must show, for each of `label_h3d.log`, `eval_h3d.log`,
`label_h2d.log` and `eval_h2d.log` in this order, one start line and one
`exit=0` line. `exit=3`: a report or a state whose SHA-256 is not the
configuration's, refused before any model was built and before anything was
written (the message names it). `exit=5`: a state did not reproduce its
report's validation arrays (everything else is written). `exit=1` with a
message about the pre-registration: the checkout is not the stamped tag. Any
other exit below 128, or a traceback: send the log. Report any of these. A
stage without an exit line, or with an exit of 128 or more (the stage was
killed): E1'. Otherwise, in every case, go on to E2: the return carries the
logs and whatever was written. Never delete anything under `runs/holdout/`.

### E1'. Interruptions
Type nothing into window 0 while the block runs: as long as it shows no
prompt, the run is going (look in a second window: Ctrl-b c; back: Ctrl-b 0).
- A dropped connection: `tmux attach -t cm`; the run goes on. Do not paste
  anything again.
- Window 0 shows no new line for 30 min while `pgrep -af
  "scripts/holdout_run.py"` in a second window still shows the stage: report,
  and do not stop it.
- The box restarted, or a stage was cut off: at a prompt in window 0 (after
  a restart, open tmux again, E0a), run
  ```bash
  cd ~/autodl-tmp/FE-JEPA
  cat runs/holdout/status.txt
  pgrep -af "scripts/holdout_run.py"      # must print nothing
  ```
  If `pgrep` prints a line, the run is still going: no restart. Otherwise
  look, for each stage, at the last line of `status.txt` that names it: the
  stage was cut off when that line is a start line, or an exit line with a
  code of 128 or more (the stage was killed); it never started when no line
  names it. Paste E1's second block again with only the `run` lines of the
  stages that were cut off or never started, in E1's order, and after a
  `label` line always the `eval` line of its set, whatever that line's exit
  (everything else in the block stays as it is). No other stage is run
  again. The labelling keeps every label it has already written; each
  attempt adds its own start and exit lines, and the adjudication records
  them.
- A stage cut off twice is not run again, nor its set's `eval`; the other
  set's stages still run as above; then E2.

### E2. Return (box; minutes)
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/holdout
T=$(date +%Y%m%d-%H%M)
OUT=~/holdout_return && rm -rf $OUT && mkdir -p $OUT/h3d $OUT/h2d
for s in h3d h2d; do cp $P/$s/eval.json $P/$s/eval_arrays.npz $P/$s/manifest.json $OUT/$s/ 2>/dev/null; done
cp $P/*.log* $P/status.txt $P/precheck.txt $P/machine.txt $OUT/ 2>/dev/null
( echo "HEAD $(git rev-parse HEAD)"; echo "tree $(git rev-parse 'HEAD^{tree}')"
  echo "describe $(git describe --tags --match prereg-holdout)"
  echo "describe-all $(git describe --always --dirty --tags)"
  echo "hostname $(hostname)"
  echo "--- files ---"; cd $OUT && find . -type f ! -name provenance.txt | sort | xargs sha256sum
) > $OUT/provenance.txt 2>&1
cd ~ && tar czf holdout_return_$T.tgz holdout_return \
    && sha256sum holdout_return_$T.tgz && du -h holdout_return_$T.tgz
```
The tarball is a few MB. Send it with the SHA-256 line. The labels stay on
the box (their SHA-256 are in the manifests); then shut the instance down
without releasing it.

### E3. In the repo
In a checkout of the branch (a clone of its own, not a copy of a worktree),
with the tag fetched by a forced refspec:
```bash
git fetch origin +refs/heads/cmame-paper:refs/remotes/origin/cmame-paper +refs/tags/prereg-holdout:refs/tags/prereg-holdout
git tag --points-at 'prereg-holdout^{commit}'   # exactly one line: prereg-holdout
git checkout -B cmame-paper origin/cmame-paper   # frozen at the stamped commit until the return
git describe --tags --match prereg-holdout   # exactly: prereg-holdout
git status --porcelain --untracked-files=no  # must print nothing
python scripts/adjudicate_holdout.py --return <the unpacked holdout_return> \
    --out records/cmame/holdout/verdict.json
```
The tarball is unpacked with `tar xzf` into an empty directory and
adjudicated as it is: a file added to it (a `.DS_Store`, say) is not in the
provenance file and refuses the return. It reads the two sets' evaluations, arrays and labels manifests, `status.txt`
and `provenance.txt` from the return, the reports of `configs/holdout_v1.json`
from `records/`, and PREREG_HOLDOUT.md, checks every returned file against
the provenance file and the recorded commit and tree against the tag
`prereg-holdout`, and writes the claims T1-T3, H1, H2a, H2b, H2c and D2 per
PREREG_HOLDOUT Sec. 5, each that does not replicate with the comparisons that
failed, the reading H3, V (whether the per-instance values are distributed
alike on the holdout set and on the validation instances), the secondary
readings of Sec. 6 beside their validation values, and the deviations, with
every input's SHA-256, the adjudicating code's and the library versions. The return is committed under
`records/cmame/holdout/return/` with the verdict. It ran on 25 October 2026
with the tag checked out, the branch having moved past it on 21 October
(`records/cmame/README.md`).

## F. PREREG_K3D: the 3D supervised transformer retrained with the stiffness-norm loss (box; ~70-85 h)
The three-dimensional supervised transformer of Phase-2, trained again on
its 1,024 labelled instances with the stiffness-norm loss L_K in place of
the displacement loss, with Phase-2's settings and seeds, beside Phase-2's
L_D states and Phase-2b's label-free states, which are evaluated again and
not trained (PREREG_K3D Sec. 2). One script, `scripts/k3d_train.py`: it
checks every input (the dry run does the same and stops there); evaluates
the six stored states on the validation split and stops before any training
if one does not reproduce Phase-2b's values; trains the three seeds in order
(about 22-27 h each); evaluates the nine states on PREREG_HOLDOUT's h3d set
with the labels Sec. E computed; writes the report. Only after Sec. E has
run (it reads `runs/holdout/h3d/`) and PREREG_K3D is stamped and tagged
`prereg-k3d`: the script refuses to run otherwise. It reads Phase-2's corpus
and states and Sec. E's h3d labels, and writes only under `runs/k3d/`, where
it holds a lock while it runs (one run at a time). Before the operator
instruction is sent, the repo side checks the remote:
`git ls-remote origin refs/heads/cmame-paper 'refs/tags/*'` shows the branch
at the stamped commit and, of all tags, only `refs/tags/prereg-k3d^{}` at
that commit (PREREG_K3D Sec. 6: no other tag on it). Before F0: the
instance's balance covers at least 100 h of it, and no scheduled shutdown is
set (AutoDL stops an instance whose balance runs out). It ran on 22-25 October
2026 on the stamped commit `7614ae2`, one attempt, exit 0, and returned
complete; the return and the verdict are in `records/cmame/k3d/`
(`records/cmame/README.md`).

### F0. Preconditions (box)

F0a. The tmux session -- on its own line, outside tmux. If a tmux status bar
is already showing (a session Sec. E left open, say), skip the line and work
in that session (`tmux ls` names it). After a dropped connection,
`tmux attach -t k3`, or `tmux attach -t` with that session's name:
```bash
tmux new -A -s k3
```

F0b. The branch and the tag (the remote's address as Sec. E set it; setting
it again changes nothing), the tag's refspec forced:
```bash
cd ~/autodl-tmp/FE-JEPA
git remote set-url origin https://github.com/RuifengCao/label-free-fe-surrogates.git
git remote get-url origin                    # https://github.com/RuifengCao/label-free-fe-surrogates.git
( for i in 1 2 3; do git fetch origin +refs/heads/cmame-paper:refs/remotes/origin/cmame-paper +refs/tags/prereg-k3d:refs/tags/prereg-k3d && exit 0; sleep 10; done
  exit 1 ) && echo FETCH-OK || echo FETCH-FAILED
git rev-parse --short origin/cmame-paper     # the commit the operator instruction names
git rev-parse --short 'prereg-k3d^{commit}'  # the same commit
```
Continue only if `FETCH-OK` is printed and both lines begin with the named
commit (an error printed by a failed first attempt before `FETCH-OK` is
harmless). If nothing at all is printed for 10 min, or the fetch has not
ended after 20 min, press Ctrl-C (then `FETCH-OK` does not appear; ignore
any lines printed after it) and take the bundle route. On `FETCH-FAILED`:
upload the bundle that the operator instruction sends to
`~/cmame-paper.bundle` and run, in place of the fetch block:
```bash
cd ~/autodl-tmp/FE-JEPA
sha256sum ~/cmame-paper.bundle               # the SHA-256 the operator instruction names
git fetch ~/cmame-paper.bundle +refs/heads/cmame-paper:refs/remotes/origin/cmame-paper +refs/tags/prereg-k3d:refs/tags/prereg-k3d && echo FETCH-OK || echo FETCH-FAILED
git rev-parse --short origin/cmame-paper     # the commit the operator instruction names
git rev-parse --short 'prereg-k3d^{commit}'  # the same commit
```
Continue only if the SHA-256 is the named one, `FETCH-OK` is printed and
both lines begin with the named commit; otherwise stop here and report.
(Repo side: the bundle is made from the pushed branch and tag with
`git bundle create cmame-paper.bundle 69fb698..cmame-paper prereg-k3d`,
Sec. E's stamped commit `69fb698` being on the box; `git bundle list-heads`
shows `refs/heads/cmame-paper` at the named commit and `refs/tags/prereg-k3d`
at the annotated tag's own object, which peels to that commit.)

F0c. First, on its own:
```bash
ls ~/autodl-tmp/FE-JEPA/runs/k3d/status.txt 2>/dev/null || echo "no F1 yet"
```
On the first visit it prints `no F1 yet`: go on. If it prints the file's
path, F1 has run before: go to F1' instead, and run nothing else of F0.
Then the checkout, the checks and the suite (~10 min):
```bash
cd ~/autodl-tmp/FE-JEPA
git checkout -B cmame-paper origin/cmame-paper   # "Switched to ..." or "Reset branch ...", maybe "set up to track" or "up to date"
git describe --always --dirty --tags         # must print exactly: prereg-k3d
git tag --points-at HEAD                     # must print exactly: prereg-k3d
git rev-parse 'HEAD^{tree}'                  # the tree the operator instruction names
git status --porcelain --untracked-files=no  # must print nothing
ls runs/k3d/status.txt 2>/dev/null || echo "no F1 yet"   # on the first visit: no F1 yet
sha256sum runs/holdout/h3d/manifest.json     # the SHA-256 the operator instruction names (Sec. E's labels manifest, as returned)
df -h ~/autodl-tmp / | tail -n 2             # >= 5 GB free on the data disk and on /
cat /sys/fs/cgroup/memory.max                # 98784247808 (92 GiB) or max; a number under 64000000000: stop
pgrep -af "fejepa|spawn_main|scripts/[A-Za-z0-9_]+\.py"   # must print nothing
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader   # about 0 %, under 1,000 MiB
grep oom_kill /sys/fs/cgroup/memory.events   # note the number: F1' compares with it
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"   # 2.12.1+cu130 True
mkdir -p runs/k3d
[ -e runs/k3d/pytest.log ] && mv runs/k3d/pytest.log runs/k3d/pytest.log.$(date +%Y%m%d-%H%M%S)
python -m pytest -q --deselect tests/test_cmame_material.py::test_manuscript_compiles \
    --deselect tests/test_w9_session2.py::test_paper_material_compiles \
    --deselect tests/test_cmame_references.py::test_the_bibliography_renders_the_data_reference_and_the_chapter \
    2>&1 | tee runs/k3d/pytest.log | tail -n 3
```
The suite's last line reads `760 passed, 3 deselected`, then warnings and the
time. Anything failed, an error, another count, or any other output than the
comments describe: stop and report.

F0d. The dry run (~2 min; nothing trains, nothing runs on the GPU):
```bash
cd ~/autodl-tmp/FE-JEPA
python scripts/k3d_train.py configs/k3d_v1.json --dry-run
```
It prints two lines. The first: `[k3d] holdout h3d: 686 instances, their
corpus and labels files verified (... s)`. The second, the plan: `"row": "labels_knorm"`,
`"device": "cuda"`, `"seeds": [0, 1, 2]`, `"budget": 1024`, `"epochs": 200`,
`"lr": 0.0015`, `"n_train": 1024`, `"n_val": 256`, `"states_verified": 6`,
`"holdout": 686`, `"git": "prereg-k3d"`, `"commit": "..."` with the commit the
operator instruction names, and `"prereg": {"file": "PREREG_K3D.md",
"config_sha256": "..."}` with the hash the operator instruction names.
Anything but those two lines (a line beginning `STOP:`, a traceback, a
one-line message, another number or `null`): stop and report.

### F1. The run (box; ~70-85 h; nothing else on the GPU)
First the checks, on their own:
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/k3d
( date; hostname; pgrep -af "fejepa|spawn_main|scripts/[A-Za-z0-9_]+\.py"
  nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader ) 2>&1 | tee -a $P/precheck.txt
```
`pgrep` must print nothing and the GPU line must read about 0 % and under
1,000 MiB; otherwise stop here and report. Then, in the same window:
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/k3d
touch $P/status.txt
run() { [ -e $P/report.json ] && { echo "DONE: report.json exists, nothing started (F2)"; return 1; }
        pgrep -af '^python[0-9.]* scripts/k3d_train\.py' && { echo "ALREADY RUNNING: nothing started (F1')"; return 1; }
        local log=$1; shift; [ -e $P/$log ] && mv $P/$log $P/$log.$(date +%Y%m%d-%H%M%S)
        echo "$log start $(date -u +%FT%TZ) $(hostname)" >> $P/status.txt
        "$@" 2>&1 | tee $P/$log; echo "$log exit=${PIPESTATUS[0]}" | tee -a $P/status.txt; }
run k3d.log python scripts/k3d_train.py configs/k3d_v1.json
( echo "HEAD $(git rev-parse HEAD)"; echo "tree $(git rev-parse 'HEAD^{tree}')"
  git status --porcelain --untracked-files=no
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
  lscpu | grep -E "^Model name|^CPU\(s\)|^Thread|^Socket"; echo "nproc $(nproc)"
  echo "hostname $(hostname)"
  cat /sys/fs/cgroup/cpu.max /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.events 2>/dev/null
  free -g | head -n 2
) >> $P/machine.txt 2>&1
cat $P/status.txt
```
If the block does not start after it is pasted, press Enter once. If it
prints `ALREADY RUNNING`, a run is going already: nothing was started or
written; report. If it prints `DONE`, the run has finished (its report is
there): nothing was started or written; go to F2. `status.txt` is never deleted or rotated: it keeps a start line per attempt,
and an exit line whenever the script ended or was killed on its own. Do not
press Ctrl-C in this window and do not type into it while the block runs;
to look, open a second window (Ctrl-b c; back: Ctrl-b 0).

What to expect, in order:
- the two lines of F0d;
- the six stored states evaluated on the validation split (possibly torch
  `UserWarning` blocks, harmless): a line every 32 instances
  (`[k3d] evaluating ar s0: 32/256`), then per state one line with
  `"content_check"` that includes `"finite": true, "ok": true`; about 5 min in
  all;
- the three seeds in order, each about 22-27 h. At a seed's start and before
  its first progress line, possibly torch `UserWarning` blocks (harmless, also
  where they mention memory errors or a SEGFAULT); then a progress line every
  10% of its
  204,800 steps, the first after about 2.5 h
  (`[sup:none K3D labels_knorm b1024 s0] step 20480/204800 (10%) knorm=...`;
  the number after `knorm=` is one instance's loss at that step, so it moves
  up and down from line to line); the trainer's evaluation on the validation
  split (no lines); then one line per seed
  (`{"seed": 0, "val": {...}, "seconds": {...}}`): about 22-27, 44-54 and
  66-82 h after the start;
- the holdout set: a line every 32 instances (`[k3d] holdout h3d: 32/686 |
  ... s`), about half an hour;
- `[k3d] report -> .../runs/k3d/report.json` and `k3d.log exit=0`.

Exit status: 0 done (F2). 2: no GPU, or a GPU that does not work or is in
use; nothing ran on it (the message says which). 3: an input refused, or
another run holding the lock (a line beginning `STOP:` names it). 5: a
stored state does not reproduce Phase-2b's values; nothing trained. 137:
killed (SIGKILL, for example by the out-of-memory killer). Anything else: an
error (a traceback, or a one-line message). A Ctrl-C, a closed session or a
restart of the box leaves the start line without an exit line (F1').

Health check (any time, in a second window; once or twice a day is enough):
```bash
cd ~/autodl-tmp/FE-JEPA; date; tail -n 2 runs/k3d/status.txt; tail -n 2 runs/k3d/k3d.log | cut -c1-160
pgrep -af '^python[0-9.]* scripts/k3d_train\.py' | cut -c1-120
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
find runs/k3d -type f -mmin -45 -printf '%TH:%TM %p\n' | sort | tail -n 3
grep -h oom_kill /sys/fs/cgroup/memory.events 2>/dev/null; df -h ~/autodl-tmp / | tail -n 2
```
Healthy: `pgrep` prints exactly one line, the script's own (it ends with
`k3d_train.py configs/k3d_v1.json`; two such lines: two copies, report at once); the GPU in
use (memory well above 1,000 MiB); a file under `runs/k3d/` written within
45 min (while a seed trains, its epoch checkpoint
`labels_knorm_b1024_s<seed>.ckpt` about every 7 min; while states are
evaluated, the log); `oom_kill` as noted in F0c; at least 5 GB free on the
data disk and on /. Not healthy: report, and do not stop the run.

### F1'. Interruptions
What decides is the last line of `runs/k3d/status.txt` (the check below
prints it): an exit line is the script's own end (the third bullet); a start
line is a run that is going (`pgrep` shows it) or one that ended without an
exit line (a restart of the box, the session or its shell killed).
- A dropped connection: `tmux attach -t k3` (or the session F0a left you
  in); the run goes on. Do not paste anything again. If `tmux ls` lists no
  session (it answers with an error, such as `no server running`), the box
  restarted: next bullet.
- The box restarted, or the last line of `status.txt` is a start line: at a
  prompt in window 0 (after a restart, open tmux again, F0a), run
  ```bash
  cd ~/autodl-tmp/FE-JEPA
  cat runs/k3d/status.txt
  pgrep -af '^python[0-9.]* scripts/k3d_train\.py'   # must print nothing
  grep oom_kill /sys/fs/cgroup/memory.events
  tail -n 3 runs/k3d/k3d.log | cut -c1-160
  ```
  If `pgrep` prints a line, the run is still going: no restart. If the last
  line of `status.txt` is an exit line: the third bullet, not this one.
  Otherwise note the seed and the last progress line that `tail` shows, and
  paste F1's second block again, unchanged (a restart of the box resets the
  `oom_kill` count: note the new number). The stored states' evaluations
  (once all six are done) and every finished seed are kept (`[k3d] stored
  states: evaluations on disk` and `[k3d] seed 0: result on disk`), and the
  interrupted seed resumes from its last epoch checkpoint (`[ckpt] resumed
  K3D labels_knorm b1024 s1 at epoch .../200`; a checkpoint that cannot be
  read is moved aside, `[ckpt] ... unusable ...`, and that seed trains from
  the start); each attempt adds its own start line, and the adjudication
  records them. Interrupted again with the same seed and the same last
  progress line as noted: report instead.
- An exit line other than `exit=0`:
  - `exit=3` or `exit=5`: first `pgrep -af '^python[0-9.]* scripts/k3d_train\.py'`:
    if it prints a line, a run is still going: touch nothing and report.
    Otherwise do not run again; make the F2 return (it carries the logs),
    shut the instance down without releasing it, and report.
  - `exit=2`: look at `nvidia-smi`; if the GPU is idle and nothing else
    runs, paste F1's second block again once; otherwise report.
  - `exit=137`, `oom_kill` above the number noted, or `out of memory` in the
    log's last 60 lines (`tail -n 60 runs/k3d/k3d.log`): do not run again;
    report.
  - `No space left on device` on the screen or in the log's last 60 lines,
    or under 1 GB free in `df -h ~/autodl-tmp /`: do not run again; report.
  - anything else: paste F1's second block again. If that attempt also ends
    with an exit line other than `exit=0` that none of the rules above
    covers, paste the block below once: it writes the report without the
    holdout set (PREREG_K3D Sec. 6) only if all three seed result files
    exist and the last two run logs both end in a traceback through
    `holdout_evaluation` or `holdout_instances` (the holdout evaluation
    failed in both attempts); otherwise it prints `NOT ALLOWED` and runs
    nothing:
    ```bash
    cd ~/autodl-tmp/FE-JEPA
    P=runs/k3d
    n=$(ls $P/seed_*.json 2>/dev/null | wc -l)
    h=$(for f in $(ls -t $P/k3d.log* | head -n 2); do tail -n 60 $f | grep -cE 'in holdout_(evaluation|instances)$'; done | grep -c '^[1-9]')
    echo "seed result files: $n; of the last two logs, ending in a holdout traceback: $h"   # 3 and 2
    run() { [ -e $P/report.json ] && { echo "DONE: report.json exists, nothing started (F2)"; return 1; }
            pgrep -af '^python[0-9.]* scripts/k3d_train\.py' && { echo "ALREADY RUNNING: nothing started (F1')"; return 1; }
            local log=$1; shift; [ -e $P/$log ] && mv $P/$log $P/$log.$(date +%Y%m%d-%H%M%S)
            echo "$log start $(date -u +%FT%TZ) $(hostname)" >> $P/status.txt
            "$@" 2>&1 | tee $P/$log; echo "$log exit=${PIPESTATUS[0]}" | tee -a $P/status.txt; }
    if [ "$n" = 3 ] && [ "$h" = 2 ]; then
    run k3d.log python scripts/k3d_train.py configs/k3d_v1.json --skip-holdout
    else echo "NOT ALLOWED: nothing run; report (F1')"; fi
    ```
    `NOT ALLOWED`, any other case, or that run not ending with `exit=0`:
    report.
- When reporting, send `cat runs/k3d/status.txt`, `tail -n 60
  runs/k3d/k3d.log`, the `nvidia-smi` line, `df -h ~/autodl-tmp /` and the
  `oom_kill` line.
- Never delete anything under `runs/k3d/`, never release the instance, and
  do not restart it without its GPU or move it to another host without
  asking.

### F2. Return (box; minutes)
After `k3d.log exit=0` (or as F1' says):
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/k3d
T=$(date +%Y%m%d-%H%M)
OUT=~/k3d_return && rm -rf $OUT && mkdir -p $OUT
cp $P/report.json $P/reused.json $P/seed_?.json $P/holdout_arrays.npz $OUT/ 2>/dev/null
cp $P/k3d.log* $P/status.txt $P/precheck.txt $P/machine.txt $P/pytest.log $OUT/ 2>/dev/null
( echo "HEAD $(git rev-parse HEAD)"; echo "tree $(git rev-parse 'HEAD^{tree}')"
  echo "describe $(git describe --always --dirty --tags)"
  echo "hostname $(hostname)"
  echo "--- runs/k3d ---"; ls -l --full-time $P
  echo "--- states ---"; sha256sum $P/labels_knorm_b1024_s?.pt
  echo "--- files ---"; cd $OUT && find . -type f ! -name provenance.txt | sort | xargs sha256sum
) > $OUT/provenance.txt 2>&1
cd ~ && tar czf k3d_return_$T.tgz k3d_return \
    && sha256sum k3d_return_$T.tgz && du -h k3d_return_$T.tgz
```
The tarball is a few MB. Send it with the SHA-256 line. The three L_K states
stay on the box (their SHA-256 are in the provenance file and the report);
then shut the instance down without releasing it.

### F3. In the repo
In a checkout of the branch (a clone of its own, not a copy of a worktree),
with the tag fetched by a forced refspec, and PREREG_HOLDOUT's return
committed under `records/cmame/holdout/return/` (the holdout readings
compare the labels the run used with its `h3d/manifest.json`):
```bash
git fetch origin +refs/heads/cmame-paper:refs/remotes/origin/cmame-paper +refs/tags/prereg-k3d:refs/tags/prereg-k3d
git tag --points-at 'prereg-k3d^{commit}'    # exactly one line: prereg-k3d
git checkout -B cmame-paper origin/cmame-paper
git status --porcelain --untracked-files=no  # must print nothing
python scripts/adjudicate_k3d.py --return <the unpacked k3d_return> \
    --out records/cmame/k3d/verdict.json
```
The tarball is unpacked with `tar xzf` into an empty directory and
adjudicated as it is: a file added to it (a `.DS_Store`, say) is not in the
provenance file and refuses the return. It reads the report, the status
file, the run logs, the seed files, `reused.json` and the holdout arrays
from the return, the source report and `configs/k3d_v1.json` from the
checkout, and PREREG_K3D.md; checks every returned file against the
provenance file, the recorded commit and tree against the tag `prereg-k3d`,
and the report's states, seeds and commits against the return's; and writes
H2a-3D and H2b-3D, the reading H3-3D, the secondary readings of PREREG_K3D
Sec. 5 and the deviations, with every input's SHA-256, the adjudicating
code's and its comparison with the tag. The return is committed under
`records/cmame/k3d/return/` with the verdict. It ran on 25 October 2026
(`records/cmame/README.md`).

## G. The polynomial Ritz baseline and the enriched c*, post hoc (box; ~4 h)
Post hoc, no pre-registration; no verdict reads either reading. Their
specification was fixed on 20 October 2026, before any paired computation
on the manuscript's instances (BRANCH_NOTES_cmame-paper.md, Stage 14; the
values in `configs/ritz_v1.json`):
- the baseline (Appendix 1): per instance, the Ritz-Galerkin projection on a
  vector polynomial subspace with the instance's own K and F, the whole
  ladder (3D p = 6, 7, 8, 9: 168 to 495 unknowns; 2D p = 6, 8: 42 and 72),
  on the manuscript's own instances: 3D val3d (256), fine3d (the first 256 of
  the fine set) and PREREG_HOLDOUT's h3d (686), 2D val2d (256) and h2d
  (4,111), each instance checked against the records (its size and
  ||U*||_K) and paired with every recorded model's per-instance values,
  R1's and R4's included; then its row of the cost table, timed on this
  machine with the cost table's own measurements (Sec. A's
  `scripts/time_inference_vs_solve.py`) run again beside it;
- the enriched c* (Appendix 2; exploratory, not in the manuscript): the
  label-free networks' predictions combined with the same polynomial space
  (wp9 session 2's 2D baseline and S on wp9's sets IB, F2 and F5; Phase-2b's
  3D network on val3d and fine3d), then, beyond Appendix 2, Phase-2's
  labels-only transformer and graph network and PREREG_K3D's L_K on val3d
  and fine3d.
It reads the corpora (`runs/data3d_phase2`, `runs/data3d_phase2_fine`,
`runs/data2d`), Sec. E's holdout labels (`runs/holdout/`), wp9's sets and
reports (`runs/w9/`) and the states of Phase-2b, Phase-2, PREREG_K3D,
wp9's session 2 and E1 (E1's for the 2D timing only), every one checked by
SHA-256 before use (G0d checks all but E1's, which the 2D timing checks when
it starts, as in Sec. A), and writes only under `runs/ritz/`. Nothing
trains. Not on a tag: the branch at the commit the operator instruction
names. A failure here costs nothing else; report it.

### G0. Preconditions (box)

G0a. The tmux session -- on its own line, outside tmux. If a tmux status bar
is already showing, skip the line and work in that session (`tmux ls` names
it). After a dropped connection, `tmux attach -t rz`, or `tmux attach -t`
with that session's name:
```bash
tmux new -A -s rz
```

G0b. The branch (the remote's address as Sec. E set it; setting it again
changes nothing):
```bash
cd ~/autodl-tmp/FE-JEPA
git remote set-url origin https://github.com/RuifengCao/label-free-fe-surrogates.git
git remote get-url origin                    # https://github.com/RuifengCao/label-free-fe-surrogates.git
( for i in 1 2 3; do git fetch origin +refs/heads/cmame-paper:refs/remotes/origin/cmame-paper && exit 0; sleep 10; done
  exit 1 ) && echo FETCH-OK || echo FETCH-FAILED
git rev-parse --short origin/cmame-paper     # the commit the operator instruction names
```
Continue only if `FETCH-OK` is printed and the last line begins with the
named commit (an error printed by a failed first attempt before `FETCH-OK`
is harmless). If nothing at all is printed for 10 min, or the fetch has not
ended after 20 min, press Ctrl-C (then `FETCH-OK` does not appear; ignore
any lines printed after it) and take the bundle route. On `FETCH-FAILED`:
upload the bundle that the operator instruction sends to
`~/cmame-paper.bundle` and run, in place of the fetch block:
```bash
cd ~/autodl-tmp/FE-JEPA
sha256sum ~/cmame-paper.bundle               # the SHA-256 the operator instruction names
git fetch ~/cmame-paper.bundle +refs/heads/cmame-paper:refs/remotes/origin/cmame-paper && echo FETCH-OK || echo FETCH-FAILED
git rev-parse --short origin/cmame-paper     # the commit the operator instruction names
```
Continue only if the SHA-256 is the named one, `FETCH-OK` is printed and the
last line begins with the named commit; otherwise stop here and report.
(Repo side: the bundle is made from the pushed branch with
`git bundle create cmame-paper.bundle 7614ae2..cmame-paper`, Sec. F's commit
`7614ae2` being on the box; `git bundle list-heads` shows
`refs/heads/cmame-paper` at the named commit.)

G0c. First, on its own:
```bash
ls ~/autodl-tmp/FE-JEPA/runs/ritz/status.txt 2>/dev/null || echo "no G1 yet"
```
On the first visit it prints `no G1 yet`: go on. If it prints the file's
path, G1 has run before: go to G1' instead, and run nothing else of G0.
Then the checkout, the checks and the suite (~10 min):
```bash
cd ~/autodl-tmp/FE-JEPA
git checkout -B cmame-paper origin/cmame-paper   # "Switched to ..." or "Reset branch ...", maybe "set up to track" or "up to date"
git rev-parse 'HEAD^{tree}'                  # the tree the operator instruction names
git status --porcelain --untracked-files=no  # must print nothing
ls runs/ritz/status.txt 2>/dev/null || echo "no G1 yet"   # on the first visit: no G1 yet
ls runs/phase2/e8_states/{ar_p1024,labels_b1024,mgn_b1024}_s*.pt runs/k3d/labels_knorm_b1024_s*.pt \
    runs/w9/{b,s}_n1024/e8_states/ar_p1024_s*.pt runs/w9/{b,s}_n1024/report.json \
    runs/e1_2d_base/e8_states/ar_p1024_s*.pt | wc -l   # 23
df -h ~/autodl-tmp / | tail -n 2             # >= 5 GB free on the data disk and on /
cat /sys/fs/cgroup/memory.max                # 96636764160 (90 GiB) or max; a number under 64000000000: stop
pgrep -af "fejepa|spawn_main|scripts/[A-Za-z0-9_]+\.py"   # must print nothing
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader   # about 0 %, under 1,000 MiB
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"   # 2.12.1+cu130 True
mkdir -p runs/ritz
[ -e runs/ritz/pytest.log ] && mv runs/ritz/pytest.log runs/ritz/pytest.log.$(date +%Y%m%d-%H%M%S)
python -m pytest -q --deselect tests/test_cmame_material.py::test_manuscript_compiles \
    --deselect tests/test_w9_session2.py::test_paper_material_compiles \
    --deselect tests/test_cmame_references.py::test_the_bibliography_renders_the_data_reference_and_the_chapter \
    2>&1 | tee runs/ritz/pytest.log | tail -n 3
```
The suite's last line reads `825 passed, 3 deselected`, then warnings and the
time. Anything failed, an error, another count, or any other output than the
comments describe: stop and report.

G0d. Every input checked (~2 min; nothing is computed or written but the log):
```bash
cd ~/autodl-tmp/FE-JEPA
python scripts/ritz_baseline.py --config configs/ritz_v1.json --set all --check 2>&1 | tee runs/ritz/check.log
python scripts/enriched_cstar.py --config configs/ritz_v1.json --arm all --check 2>&1 | tee -a runs/ritz/check.log
```
It prints eleven lines and nothing else. Five from the baseline, one per set:
`{"set": "val3d", "n": 256, "files": "present", "inputs": "verified"}`, then
the same for `fine3d` (256), `h3d` (686), `val2d` (256) and `h2d` (4111).
Six from the enriched reading, one per arm: `{"arm": "b_n1024", "seeds": [3,
4, 5], "states_verified": 3, "sets": {"IB": 2048, "F2": 256, "F5": 256}}`,
the same for `s_n1024`, then `phase2b`, `phase2b_labels`, `phase2b_mgn` and
`k3d_labels_knorm`, each with `"seeds": [0, 1, 2]`, `"states_verified": 3`
and `"sets": {"val3d": 256, "fine3d": 256}`. A line beginning `REFUSED:`
names a file whose bytes are not the ones the records give (a report, a
manifest, a labels file, a state) or a file that is missing: stop and
report, before G1. Any other output (a traceback, another number): stop and
report.

### G1. The run (box; ~3.5-4.5 h; nothing else on the GPU)
First the checks, on their own:
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/ritz
( date; hostname; pgrep -af "fejepa|spawn_main|scripts/[A-Za-z0-9_]+\.py"
  nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader ) 2>&1 | tee -a $P/precheck.txt
```
`pgrep` must print nothing and the GPU line must read about 0 % and under
1,000 MiB; otherwise stop here and report. Then, in the same window:
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/ritz
touch $P/status.txt
run() { local log=$1; shift; [ -e $P/$log ] && mv $P/$log $P/$log.$(date +%Y%m%d-%H%M%S)
        echo "$log start $(date -u +%FT%TZ) $(hostname)" >> $P/status.txt
        "$@" 2>&1 | tee $P/$log; echo "$log exit=${PIPESTATUS[0]}" | tee -a $P/status.txt; }
run ritz_val3d.log python scripts/ritz_baseline.py --config configs/ritz_v1.json --set val3d
run ritz_fine3d.log python scripts/ritz_baseline.py --config configs/ritz_v1.json --set fine3d
run ritz_h3d.log python scripts/ritz_baseline.py --config configs/ritz_v1.json --set h3d
run ritz_val2d.log python scripts/ritz_baseline.py --config configs/ritz_v1.json --set val2d
run ritz_h2d.log python scripts/ritz_baseline.py --config configs/ritz_v1.json --set h2d
run enriched_b_n1024.log python scripts/enriched_cstar.py --config configs/ritz_v1.json --arm b_n1024 --device cuda
run enriched_s_n1024.log python scripts/enriched_cstar.py --config configs/ritz_v1.json --arm s_n1024 --device cuda
run enriched_phase2b.log python scripts/enriched_cstar.py --config configs/ritz_v1.json --arm phase2b --device cuda
run ritz_timing_3d.log python scripts/ritz_timing.py --config configs/ritz_v1.json --dim 3 --out $P/timing/ritz_timing_3d.json
run ritz_timing_2d.log python scripts/ritz_timing.py --config configs/ritz_v1.json --dim 2 --out $P/timing/ritz_timing_2d.json
run timing_3d.log python scripts/time_inference_vs_solve.py --report records/wp8/e2/baseline/report_phase2b.json --states-dir runs/phase2/e8_states --out $P/timing/timing_3d.json
run timing_2d.log python scripts/time_inference_vs_solve.py --report records/wp8/e1/e1_2d_base/report.json --states-dir runs/e1_2d_base/e8_states --out $P/timing/timing_2d.json
run enriched_phase2b_labels.log python scripts/enriched_cstar.py --config configs/ritz_v1.json --arm phase2b_labels --device cuda
run enriched_phase2b_mgn.log python scripts/enriched_cstar.py --config configs/ritz_v1.json --arm phase2b_mgn --device cuda
run enriched_k3d_labels_knorm.log python scripts/enriched_cstar.py --config configs/ritz_v1.json --arm k3d_labels_knorm --device cuda
( echo "HEAD $(git rev-parse HEAD)"; echo "tree $(git rev-parse 'HEAD^{tree}')"
  git status --porcelain --untracked-files=no
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
  lscpu | grep -E "^Model name|^CPU\(s\)|^Thread|^Socket"; echo "nproc $(nproc)"
  echo "hostname $(hostname)"
  cat /sys/fs/cgroup/cpu.max /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.events 2>/dev/null
  free -g | head -n 2
) >> $P/machine.txt 2>&1
cat $P/status.txt
```
If the block does not start after it is pasted, press Enter once.
`status.txt` is never deleted or rotated: it keeps a start line and an exit
line per attempt of each step. Do not press Ctrl-C in this window and do
not type into it while the block runs; to look, open a second window
(Ctrl-b c; back: Ctrl-b 0). Each step runs whatever the steps before it
ended with. The four timing steps run on a machine with nothing else on it,
like the other steps; long silences there are normal.

What to expect, in order:
- the baseline, five steps (~25 min in all; about 10 min for fine3d): a line
  every 16 instances (`[ritz val3d] 16/256 instance_... dofs ... gap p6:...
  p7:... p8:... p9:... id ... | ... s`), then one summary line:
  `"set"`, `"n"` and `"n_used"` both the set's size (256, 256, 686, 256,
  4111), `"identity_failed": 0`, `"identity_max_rel_diff"` below 1e-9,
  `"median_gap"` per p, `"dropped_max"` per p (0 expected), `"worse_than_zero"`
  per p (0 expected: the zero field lies in every subspace),
  `"sign_mismatch": 0`. A line `... NOT THE RECORDED INSTANCE ...` names an
  instance whose size or ||U*||_K differs from the records;
- the enriched reading, three steps (~1 h in all; Phase-2b's fine3d about 35
  min, its 2.2 s inference per seed and instance setting the pace): per set,
  first a precheck line (`{"arm": ..., "set": ..., "precheck": {"set": ...,
  "n": 8, "median_rel_dev": {"s3": [..., ...], ...}}}`: each seed's
  displacement error and energy gap recomputed on 8 instances against the
  report, about 0 for the transformers), a line every 16 instances
  (`[enriched b_n1024 IB] 16/2048 | ... s`), and a summary line with
  `"identity_failed": 0`, `"content_passed": true`, `"bound_ok": true` (the
  enriched projection is never worse than c* or Ritz: its largest excess,
  `"bound_excess_max"`, is round-off, at most 1e-8) and the two ratios per
  seed; last, one line per arm
  (`{"arm": ..., "sets_complete": [...], "complementary": ...}`, the
  reading itself: `true`, `false` or `null`, no value expected);
- the timing, four steps (~50 min): `[ritz-timing] val 1/32 dof ... |
  assembly ... s, ritz p9 ... s, gap ... | ... s` per instance (32
  validation, then 8 fine instances in 3D; 32 in 2D), then a summary line;
  then the cost table's measurements as in Sec. A1 (one line per instance;
  the 3D fine set's direct solves take minutes each and an estimated 7-10
  GB of host memory; each solver stops starting new solves after 15 min
  per set), each ending with its summary line;
- the enriched reading beyond Appendix 2, three steps (~1.5-2 h): as above,
  the graph network's precheck deviations small but not necessarily 0
  (about 1e-4, as in Sec. A), and for `k3d_labels_knorm` the fine set's
  precheck reading the validation split (`"precheck": {"set": "val3d", ...}`:
  its run recorded no fine-set values), so that its fine3d summary line
  reads `"content_passed": null`.

`status.txt` must show, for each of the fifteen steps in this order, one
start line and one `exit=0` line. Exit statuses of the three scripts of this
section: `exit=3`: an input refused before anything was computed for that
step (the line beginning `REFUSED:` names it); `exit=4`: an instance that is
not the recorded one (everything written; the summary lists it); `exit=5`
(enriched): a model that does not reproduce its report (at the precheck,
`NOT REPRODUCED`, nothing written for that set; after a set, everything
written); `exit=2` (enriched): no usable GPU (from any script, `exit=2`
after a line beginning `usage:` is a command that does not parse: a line
pasted in part). Any other exit below 128, or a traceback: send the log.
Report any of these. A step without an exit line, or with an exit of 128 or
more (the step was killed): G1'. Otherwise, in every case, go on to G2: the
return carries the logs and whatever was written. Never delete anything
under `runs/ritz/`.

### G1'. Interruptions
- A dropped connection: `tmux attach -t rz` (or the session G0a left you
  in); the run goes on. Do not paste anything again. If `tmux ls` lists no
  session (it answers with an error, such as `no server running`), the box
  restarted: next bullet.
- The box restarted, or a step was cut off: at a prompt in window 0 (after a
  restart, open tmux again, G0a), run
  ```bash
  cd ~/autodl-tmp/FE-JEPA
  cat runs/ritz/status.txt
  pgrep -af "scripts/(ritz_baseline|enriched_cstar|ritz_timing|time_inference_vs_solve)\.py"   # must print nothing
  ```
  If `pgrep` prints a line, the run is still going: no restart. Otherwise
  look, for each step, at the last line of `status.txt` that names it: the
  step was cut off when that line is a start line, or an exit line with a
  code of 128 or more (the step was killed); it never started when no line
  names it. Paste G1's second block again with only the `run` lines of the
  steps that were cut off or never started, in G1's order (each step is one
  whole line beginning `run`; everything else in the block stays as it is).
  No other step is run again. The baseline and the enriched reading resume
  after the last instance they wrote (`resuming after ... instances on
  disk`); a timing step starts again. Each attempt adds its own start and
  exit lines.
- A step cut off twice is not run again; the other steps still run as
  above; then G2.
- When reporting, send `cat runs/ritz/status.txt`, the last 60 lines of the
  step's log, the `nvidia-smi` line, `df -h ~/autodl-tmp /` and
  `grep oom_kill /sys/fs/cgroup/memory.events`.

### G2. Return (box; minutes)
```bash
cd ~/autodl-tmp/FE-JEPA
P=runs/ritz
T=$(date +%Y%m%d-%H%M)
OUT=~/ritz_return && rm -rf $OUT && mkdir -p $OUT && cp -r $P/. $OUT/
( echo "HEAD $(git rev-parse HEAD)"; echo "tree $(git rev-parse 'HEAD^{tree}')"
  echo "describe-all $(git describe --always --dirty --tags)"
  echo "hostname $(hostname)"
  echo "--- files ---"; cd $OUT && find . -type f ! -name provenance.txt | sort | xargs sha256sum
) > $OUT/provenance.txt 2>&1
cd ~ && tar czf ritz_return_$T.tgz ritz_return \
    && sha256sum ritz_return_$T.tgz && du -h ritz_return_$T.tgz
```
The tarball is a few tens of MB. Send it with the SHA-256 line; then shut
the instance down without releasing it.

### G3. In the repo
The return is checked: HEAD and tree against the pushed commit, every file
against the provenance file, the exit codes; each set's summary is rebuilt
from its rows and the records (`python scripts/ritz_baseline.py --config
configs/ritz_v1.json --set <set> --resummarise <dir>`; for the enriched
reading `python scripts/enriched_cstar.py --config configs/ritz_v1.json --arm
<arm> --resummarise <dir>`, with `--report` naming wp9-pool's records copy of
a wp9 arm's report, and `--reread <arm dir>` for its reading) and compared
with the returned one; the enriched reading's Ritz rows against the
baseline's p = 8 on val3d and fine3d. It is committed under
`records/cmame/ritz/`; the manuscript's baseline rows, its cost-table row and
its discussion are then generated from it. It ran on 28 October 2026
(`records/cmame/README.md`).
