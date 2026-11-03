# RUNBOOK -- R2b (PREREG_R2B: S on the Phase-2b transformer), commands in execution order

Written 3 November 2026 (wp9-pool Stage 4, with the draft pre-registration).
PREREG_R2B.md is stamped and tagged (`prereg-r2b`, an annotated tag) BEFORE the
box session; the session then runs the transformer with S, the post-hoc
amplitude pass on it, the fresh baseline and the post-hoc pass on it, in one
visit and one tmux session, through `scripts/r2b_session.sh` (the mechanics of
`scripts/fine3d_session.sh`, which the box ran for fine3d). In the sandbox, a
miniature laid out like the box (sizes scaled down, CPU) ran the session
script, interrupted twice (Ctrl-C in S's arm, a kill in the baseline's) and
restarted, then Sec. 2's block and Sec. 3's command (BRANCH_NOTES Stage 4).
The suite on the GPU, the GPU checks and the real corpora were not run
there.

Roles: **box** = the GPU machine; **repo** = code, records, pre-registration,
adjudication.

Governance: the session writes only under `runs/r2b/`. It reads the two
corpora (`runs/data3d_phase2`, `runs/data3d_phase2_fine`), whose manifests and
labels it does not change (the runs buy no labels: their solve ledgers read 0).
It touches no other run's directory and reads no earlier run's states. The
branch is frozen from the stamp until the session has returned: Sec. 0c checks
that HEAD is exactly the tagged commit, and the session script checks it again
before every step, and the GPU before every step it runs.

Time: about 170 h, seven days -- each arm about 83 h (the Phase-2b AR units
took 27.3 h per seed; then P3's zero-shot pass, about 1.5 h; S's arm somewhat
longer), the two post-hoc passes about 45 min each (the first also meshes the
64 remesh instances). The instance's balance must cover about 210 h (one
re-run of a seed, Sec. 1c, included). Nothing else may use the GPU meanwhile.

## 0. Preconditions (box, once)

0a. The tmux session -- on its own line, outside tmux; after a dropped
connection, `tmux attach -t r2b`:
```bash
tmux new -A -s r2b
```

0b. Fetch the branch and the tag, directly:
```bash
cd ~/autodl-tmp/FE-JEPA
git fetch origin +refs/heads/wp9-pool:refs/remotes/origin/wp9-pool +refs/tags/prereg-r2b:refs/tags/prereg-r2b && echo FETCH-OK || echo FETCH-FAILED
git rev-parse --short origin/wp9-pool              # the commit the operator instruction names
git rev-parse --short 'prereg-r2b^{commit}'        # the same commit
```
Continue only if `FETCH-OK` is printed and both lines are the named commit. If
`FETCH-FAILED` is printed, nothing at all is printed for 10 min, or the fetch
has not ended after 20 min (then press Ctrl-C), take the bundle route: upload
the bundle the operator instruction sends to `~/wp9-pool.bundle` and run, in
place of the first block:
```bash
cd ~/autodl-tmp/FE-JEPA
sha256sum ~/wp9-pool.bundle                        # the SHA-256 the operator instruction names
git fetch ~/wp9-pool.bundle +refs/heads/wp9-pool:refs/remotes/origin/wp9-pool +refs/tags/prereg-r2b:refs/tags/prereg-r2b && echo FETCH-OK || echo FETCH-FAILED
git rev-parse --short origin/wp9-pool              # the commit the operator instruction names
git rev-parse --short 'prereg-r2b^{commit}'        # the same commit
```
Continue only if the SHA-256 is the named one, `FETCH-OK` is printed and both
lines are the named commit; otherwise stop here and report. The explicit
refspecs matter: the box's clone is single-branch. (Repo side, before the
operator instruction is sent: `git ls-remote origin refs/heads/wp9-pool
'refs/tags/prereg-r2b^{}'` shows the branch and the annotated tag at the named
commit; the bundle is made from the pushed branch and tag with `git bundle
create wp9-pool.bundle 5a31223..wp9-pool prereg-r2b`, the box holding
`5a31223` (`prereg-fine3d`) since the fine3d session, and `git bundle
list-heads wp9-pool.bundle` shows the branch at the named commit and the tag's
own object.)

0c. Checkout, checks and the suite (about 7 min):
```bash
cd ~/autodl-tmp/FE-JEPA
git checkout -B wp9-pool origin/wp9-pool           # "Switched to ..." or "Reset branch ...", maybe "set up to track" or "up to date"
git describe --always --dirty --tags               # must print exactly: prereg-r2b
git tag --points-at HEAD                           # must print exactly: prereg-r2b
git rev-parse 'HEAD^{tree}'                        # the tree the operator instruction names
git status --porcelain --untracked-files=no        # must print nothing
df -h ~/autodl-tmp / | tail -n 2                   # >= 15 GB free on the data disk, >= 5 GB on /
pgrep -af "fejepa|spawn_main|holdout"              # must print nothing (no other run)
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader   # about 0 %, under 1,000 MiB
grep oom_kill /sys/fs/cgroup/memory.events         # note the number: 1' compares with it
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"   # 2.12.1+cu130 True
ls -A runs/r2b 2>/dev/null | grep -vx session || echo "no r2b run yet"   # must print exactly: no r2b run yet
mkdir -p runs/r2b/session
python -m pytest -q 2>&1 | tee runs/r2b/session/pytest.log | tail -n 3   # "821 passed, 1 skipped"
```
Any output other than the comments describe: stop and report. The suite's last
line reads `821 passed, 1 skipped`, then the warnings and the time, where
`pdflatex` is missing (the box: the paper tables' LaTeX build is not
compiled); `822 passed` where it is present. Anything failed, an error,
or another count: stop and report. (`no r2b run yet`: `runs/r2b` holds no
output of an R2b step, so no step can be skipped as finished by an output of
other code; 0c itself makes only `runs/r2b/session`, which the check ignores,
and the dry runs of 0d write nothing there, so a repeated 0c prints the same.)

0d. The inputs and the dry runs (~2 min):
```bash
cd ~/autodl-tmp/FE-JEPA
python -m fejepa.cli info runs/data3d_phase2 | grep -E 'manifest_sha256|n_instances'
python -m fejepa.cli info runs/data3d_phase2_fine | grep -E 'manifest_sha256|n_instances|n_labelled'
for c in r2b_s r2b_b; do
  python -m fejepa.cli run-config configs/$c.json --dry-run 2>&1 | grep -o '"prereg_status": "[^"]*"'
done
```
Expected: `runs/data3d_phase2` with manifest `dc75628290bb...` and 2000
instances; `runs/data3d_phase2_fine` with manifest `0f859ad98a01...`, 320
instances, 320 labelled; both dry runs `"prereg_status": "verified"`. Anything
else (a traceback, `would refuse`, `null`, another hash or count): stop and
report.

## 1. The session (box; about 170 h; the same tmux window)
```bash
cd ~/autodl-tmp/FE-JEPA
bash scripts/r2b_session.sh
```
Steps, in order: `r2b_s` (about 83 h), `amp_r2b_s` (about 45 min), `r2b_b`
(about 83 h; it starts only once `r2b_s` has a complete report), `amp_r2b_b`
(about 45 min). Normal signs:
- the script first prints the torch version and its CUDA build
  (`torch 2.12.1+cu130 | CUDA build 13.0`), then checks the GPU (an allocation;
  it must be free) before the session and before every step;
- each arm's log (`runs/r2b/session/r2b_*.log`) starts with `[prereg] verified
  against PREREG_R2B.md`, prints the validation set's labelling lines (it is
  already labelled: no solve), a training line at every tenth of a seed's
  steps (about every 2 h 45 min) and one line per finished seed (about every
  27 h); then P3: the fine set's labelling lines (no solve either) and its
  zero-shot pass, a line every 32 instances (`[p3] zero-shot ...`, a few
  minutes apart; about 1.5 h in all); it ends with a `gate G2` line that may
  read `passed=False` (ignore it: it is not an R2b verdict) and the solve
  ledger reading `'total': 0`;
- each amplitude log prints one JSON line per seed and set, a line of seed
  means, then one line per seed for the remesh pass;
- at the end `status.txt` lists the four steps with `exit=0`.

### 1'. Health check (any time; a second tmux window: Ctrl-b c; back: Ctrl-b 0)
```bash
cd ~/autodl-tmp/FE-JEPA; date; tail -n 3 runs/r2b/session/status.txt
pgrep -af "run-config|posthoc_amplitude" | cut -c1-120
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
find runs/r2b -type f -mmin -45 -printf '%TH:%TM %p\n' | sort | tail -n 4
grep -h oom_kill /sys/fs/cgroup/memory.events 2>/dev/null; df -h ~/autodl-tmp / | tail -n 2
```
Healthy: one step process; the GPU in use (memory well above 1,000 MiB); a
file under `runs/r2b/` written within the last 45 min (a log, a checkpoint, a
state or a record: during training an epoch checkpoint about every 8 min);
`oom_kill` unchanged since 0c. Otherwise: Ctrl-C in window 0, wait for the
prompt (the script stops once the command it interrupted has ended and writes
`session interrupted` to `status.txt`; if a step starts instead, press Ctrl-C
again), and send this output plus `tail -n 60` of the running step's log; do
not restart.

### 1c. Interruptions and crashes
- A dropped connection: `tmux attach -t r2b`; the session goes on.
- The box restarted or the script was stopped: open tmux again (0a), then
  `pgrep -af "run-config|posthoc_amplitude"` must print nothing; then
  `cd ~/autodl-tmp/FE-JEPA && bash scripts/r2b_session.sh`. A finished step is
  skipped; an arm with states but no report restarts with `--reuse-states`
  (finished seeds reused, an interrupted one resumed from its epoch
  checkpoint; recorded in its report); every attempt keeps its log and
  `status.txt` time-stamps each attempt, with the host and GPU driver it
  starts on. The script refuses to start while another copy runs.
- A step ends with `exit` other than 0 (the script goes on to the next step,
  except that the baseline runs only once S's report is complete: then
  `status.txt` reads `r2b_b: r2b_s has a complete report`, followed by the
  baseline's start line or by its GPU check's `STOP`; otherwise it reads
  `r2b_b: not run, r2b_s has no complete report (R2b needs both arms)`):
  when the script has finished, read `tail -n 30 runs/r2b/session/<step>.log`.
  If it mentions `out of memory`, the exit is 137, or `oom_kill` rose: do not
  re-run; go to Sec. 2 and report. Otherwise re-run the script once as above;
  if the step fails again, go to Sec. 2 and report.
- `STOP before <step>: the code is ...` in `status.txt`: the checkout changed
  during the session; go to Sec. 2 and report.
- `STOP: ...` at the start, or `STOP before <step>: ...` in `status.txt`, with
  `no GPU`, `the GPU does not work (...)` or `the GPU is in use (...)`: the
  GPU is missing, failing or used by another process, and that step did not
  start (it would have run on the CPU, or failed restoring what an earlier
  attempt left); go to Sec. 2 and report.
- `STOP before <step>: the check of its report failed (exit ...)` (or of its
  record) in `status.txt`: a check of a step's output could not run (out of
  memory, a killed process, a disk error); nothing was moved or run; go to
  Sec. 2 and report.
- Never delete anything under `runs/r2b/`.

## 2. Return (box; minutes)
```bash
cd ~/autodl-tmp/FE-JEPA
OUT=~/r2b_return && rm -rf $OUT && mkdir -p $OUT/session $OUT/posthoc
cp runs/r2b/session/status.txt runs/r2b/session/*.log* $OUT/session/
for a in r2b_s r2b_b; do
  [ -d runs/r2b/$a ] || continue
  mkdir -p $OUT/$a; cp runs/r2b/$a/report.json* runs/r2b/$a/RESULTS*.md $OUT/$a/ 2>/dev/null
done
cp runs/r2b/posthoc/amp_*.json $OUT/posthoc/ 2>/dev/null
( echo "HEAD $(git rev-parse HEAD)"; echo "tree $(git rev-parse 'HEAD^{tree}')"
  echo "describe $(git describe --always --dirty --tags)"
  echo "tags $(git tag --points-at HEAD | tr '\n' ' ')"
  echo "--- git status --porcelain ---"; git status --porcelain | grep -v '^?? runs/' | head -40
  python -c "import torch, gmsh; print('torch', torch.__version__, torch.cuda.is_available(), 'gmsh', gmsh.__version__)"
  echo "--- reports ---"; sha256sum runs/r2b/*/report.json runs/r2b/posthoc/amp_*.json
  echo "--- states ---"; ls -l --full-time runs/r2b/*/e8_states/
  sha256sum runs/r2b/*/e8_states/ar_*.pt
  nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv,noheader
  echo "hostname $(hostname)"; echo "nproc $(nproc)"; lscpu | grep 'Model name'
  cat /sys/fs/cgroup/memory.max 2>/dev/null; cat /sys/fs/cgroup/memory.events 2>/dev/null
  df -h ~/autodl-tmp / | tail -n 2
) > $OUT/provenance.txt 2>&1
cd ~ && tar czf r2b_return_$(date +%Y%m%d).tgz r2b_return \
    && sha256sum r2b_return_*.tgz && du -h r2b_return_*.tgz
```
Send the tarball. The states stay on the box (their SHA-256 are in the
provenance file and in the reports). Then shut the instance down without
releasing it.

## 3. Adjudication (repo)
```bash
python scripts/adjudicate_r2b.py \
    --r2b-b <return>/r2b_b/report.json --r2b-s <return>/r2b_s/report.json \
    --amp-b <return>/posthoc/amp_r2b_b.json --amp-s <return>/posthoc/amp_r2b_s.json \
    --status <return>/session/status.txt \
    --out records/wp9/r2b/r2b_verdict.json
```
It reads the Phase-2b report and fine3d's verdict file from `records/` (each
checked by SHA-256) and the stamped lines from PREREG_R2B.md, and requires
both reports to have run on `prereg-r2b`. R2b per PREREG_R2B Sec. 5, the
secondary readings of Sec. 6, refusals and deviations; the inputs' SHA-256,
the session's attempts and their last exits, and the adjudicating code (its
files against the tag's) are recorded in the verdict file. A report refused
or not in the return leaves R2b NOT EVALUATED.
