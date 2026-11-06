# RUNBOOK: gate G-C2.1, commands in execution order

**What it runs.** The deciding run of `docs/PRESPEC_G-C2.1.md`: label-free training of the project's transformer on a family of bolted T-stubs with plastic flanges, webs and bolts, bolt preload and contact, loaded through a spring, against a supervised arm, judged on held-out T-stubs.

**Roles.** The **box** is the GPU machine. The **repo** holds the code, the pre-specification and the records.

**When.** Before R2b, by the owner's decision of 6 November 2026, when R2b had not started. R2b starts only after this run's return package has been sent; if R2b has already started, stop and report before section 0. Nothing else may use the GPU during the bench and the training.
- The run uses its own worktree, `~/autodl-tmp/FE-JEPA-c2`. No other checkout is touched.

**Time and space** (estimates; the bench of section 3 measures the step time).
- Generation: about 5 min on the CPU.
- Bench: a few minutes.
- Labels: 132 members, 860 solves (68 members at 7 levels, 64 training members at 6 levels). Seven members on this mesh took 1.6 to 5.4 min each on one core of the development machine with the scipy solver: about half an hour with 16 worker processes, less with PARDISO.
- Training: six runs, 345,600 steps in all (three label-free runs of 102,400 steps, three supervised runs of 12,800). The bench prints the predicted time. Above 0.30 s a label-free step the run stops before training (section 3).
- Evaluation: for each of the 2,856 predicted fields (six runs, 68 members, seven levels), its energy and an exact solve at its predicted end displacement, about 15 to 60 s on one core: about 1 to 3 h with 16 worker processes.
- Disk: about 2 GB on the data disk. Device memory: about 3 to 4 GB for the training set's energies, plus the model.

Everything runs in ONE tmux session, named `c2`. Every block below starts with its own `cd` and variables, so it can be run again after a reconnection.

**Any error or traceback, or any output that differs from what a comment states: stop and report.**

## 0. Preconditions (box, once)

0a. The tmux session. On its own line, outside tmux; after a dropped connection, `tmux attach -t c2`:
```bash
tmux new -A -s c2
```

0b. The tag and the worktree (once). First fetch the tag; the first line must print `fresh`, otherwise stop and report:
```bash
test ! -e ~/autodl-tmp/c2 && echo fresh     # must print: fresh
cd ~/autodl-tmp/FE-JEPA
git fetch origin wp10-joint --tags
```
- If the fetch fails, or has not ended after 20 minutes, fetch the tag from the git bundle sent with the operator's instruction instead:
```bash
cd ~/autodl-tmp/FE-JEPA
sha256sum ~/wp10-joint-c2.bundle             # must equal the SHA-256 sent with the bundle
git fetch ~/wp10-joint-c2.bundle +refs/tags/prereg-c2:refs/tags/prereg-c2 && echo FETCH-OK || echo FETCH-FAILED
```
- Then, either way, the worktree:
```bash
cd ~/autodl-tmp/FE-JEPA
git rev-parse --short 'prereg-c2^{commit}'   # must print the commit named in the operator's instruction
if [ -e ~/autodl-tmp/FE-JEPA-c2 ]; then cd ~/autodl-tmp/FE-JEPA-c2 && git checkout --detach prereg-c2; else git worktree add ~/autodl-tmp/FE-JEPA-c2 prereg-c2; fi
mkdir -p ~/autodl-tmp/c2/records
```

0c. The checks and the suite (a few minutes):
```bash
cd ~/autodl-tmp/FE-JEPA-c2
R=~/autodl-tmp/c2/records
git describe --tags --match prereg-c2 2>&1 | tee -a $R/preconditions.log       # must print exactly: prereg-c2
git status --porcelain --untracked-files=no 2>&1 | tee -a $R/preconditions.log  # must print nothing
git rev-parse HEAD | tee $R/commit.txt
hostname | tee -a $R/preconditions.log; nproc | tee -a $R/preconditions.log      # nproc: the CPUs this shell may run on
df -h ~/autodl-tmp | tail -n 1 | tee -a $R/preconditions.log                    # at least 10 GB free
pgrep -af "python.*(fejepa|c13/__main__|c2/__main__)|spawn_main" | tee -a $R/preconditions.log   # must print nothing
nvidia-smi --query-gpu=name,driver_version,utilization.gpu,memory.used,memory.total --format=csv,noheader | tee -a $R/preconditions.log   # about 0 %, under 1,000 MiB used
python -c "import numpy, scipy, torch; print('numpy', numpy.__version__, 'scipy', scipy.__version__, 'torch', torch.__version__, torch.cuda.is_available())" | tee -a $R/preconditions.log   # torch ... True
cd joint
python -I -c "import sys; sys.path.insert(0, '.'); from fejoint import linsolve; print('label solver:', 'pardiso' if linsolve._PARDISO is not None else 'scipy')" | tee -a $R/preconditions.log
sha256sum -c docs/G-C2.1_code.sha256 2>&1 | tee $R/sha256_check.log | grep -vc ': OK$'   # must print 0
FEJEPA_REPO=.. python -m pytest -q -p no:cacheprovider tests/test_hex8i.py tests/test_contact.py tests/test_c2.py 2>&1 | tee $R/pytest.log | tail -n 1   # "31 passed" and nothing failed
```
- The hash file lists the gate's code and the six repository files it imports.

0d. The provenance line. Run it now, before sections 3 and 5, and whenever the instance has been restarted; report a restart, or a change of host (another host name or driver):
```bash
{ date; hostname; nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader; lscpu | grep -m1 "Model name"; nproc; for f in /sys/fs/cgroup/memory.max /sys/fs/cgroup/cpu.max /sys/fs/cgroup/memory/memory.limit_in_bytes; do [ -r $f ] && echo "$f $(cat $f)"; done; } 2>&1 | tee -a ~/autodl-tmp/c2/records/provenance.log
```
- The worker count W of sections 4 and 6 is one less than the CPUs the run may use, at least 1: the CPUs it may run on (`nproc` above), or fewer if the container's quota (`cpu.max` above) is lower.
- The three test files are the ones this run depends on. The other test files belong to earlier gates.
- Warnings in the summary line, if any, are notices from torch; anything failed or skipped: stop and report.

## 1. Configuration (box; seconds)

```bash
cd ~/autodl-tmp/FE-JEPA-c2/joint
R=~/autodl-tmp/c2/records
python -I c2/__main__.py write-config --out $R/c2_config.json --repo .. 2>&1 | tee $R/config.log
```
- The first line must be `config sha256 795515630ff6f37a819c7503931c7d7cf6e70a9f272e25ac96730394dd361fb4` (the value in `docs/PRESPEC_G-C2.1.md`).
- Twenty file hashes follow; they must equal the table in `docs/PRESPEC_G-C2.1.md`.
- Six lines `repository ... checked` follow.

## 2. Generation (box; about 5 min; no solve)

```bash
cd ~/autodl-tmp/FE-JEPA-c2/joint
R=~/autodl-tmp/c2/records; D=~/autodl-tmp/c2/data
python -I c2/__main__.py generate --data $D 2>&1 | tee $R/generate.log
python -c "import json; m = json.load(open('$D/manifest.json')); print(m['n'], m['config_sha256'])"   # 580 795515630ff6f37a819c7503931c7d7cf6e70a9f272e25ac96730394dd361fb4
```
If interrupted, run the block again: files already written for the same member and configuration are kept, and any other file is refused.

## 3. Bench and its stop rule (box; a few minutes; nothing else on the GPU)

```bash
cd ~/autodl-tmp/FE-JEPA-c2/joint
R=~/autodl-tmp/c2/records; D=~/autodl-tmp/c2/data
pgrep -af "python.*(fejepa|c13/__main__|c2/__main__)|spawn_main" | tee -a $R/gpu_checks.log   # must print nothing
nvidia-smi --query-gpu=name,driver_version,utilization.gpu,memory.used,memory.total --format=csv,noheader | tee -a $R/gpu_checks.log   # about 0 %, under 1,000 MiB used
python -I c2/__main__.py bench --data $D --repo .. --out $R/bench.json 2>&1 | tee $R/bench.log
python -c "import json; b = json.load(open('$R/bench.json')); print('mean_s_per_step', round(b['seconds_per_step_mean'], 4), 'losses_finite', b['losses_finite'], 'peak_GiB', round(b['peak_memory_GiB'], 2), 'energies_GiB', round(b['energy_GiB_training_set'], 2), 'predicted_h_at_most', round(345600 * b['seconds_per_step_mean'] / 3600, 1), 'gpu', b['gpu'])"
```
- If `mean_s_per_step` exceeds 0.30, or `losses_finite` is False, stop and report: no training before the owner decides.
- If `peak_GiB + energies_GiB` exceeds the GPU's memory minus 2 GB, stop and report.
- `predicted_h_at_most` bounds the training time (a supervised step costs less than a label-free one). If the training has not finished within that time plus half of it, report to the owner; the runs go on unless the owner stops them.

## 4. Labels (box; about half an hour with 16 worker processes)

```bash
cd ~/autodl-tmp/FE-JEPA-c2/joint
R=~/autodl-tmp/c2/records; D=~/autodl-tmp/c2/data; W=$(python -c "import os; n = len(os.sched_getaffinity(0)); q = open('/sys/fs/cgroup/cpu.max').read().split() if os.path.exists('/sys/fs/cgroup/cpu.max') else ['max']; c = n if q[0] == 'max' else max(1, int(q[0]) // int(q[1])); print(max(1, min(n, c) - 1))")
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
echo "workers $W" | tee -a $R/label.log
for s in eval tested train:64; do python -I c2/__main__.py label --data $D --split $s --workers $W 2>&1 | tee -a $R/label.log; done
python -I c2/__main__.py check-labels --data $D 2>&1 | tee $R/check_labels.log
unset OMP_NUM_THREADS MKL_NUM_THREADS OPENBLAS_NUM_THREADS
```
- Every labelled member prints one line ending in `converged`. A line ending in `NOT CONVERGED`: let the loop finish, then stop and report.
- The check prints one line with `"labels": 132, "needed": 132, "missing": []` and ending in `"ok": true`.
- If it ends otherwise, or stops with "labels fail the checks", stop and report: no training.
- If the label loop is interrupted, run the block again: labels already written are kept.

## 5. Training (box; the bulk of the time)

```bash
cd ~/autodl-tmp/FE-JEPA-c2/joint
R=~/autodl-tmp/c2/records; D=~/autodl-tmp/c2/data; U=~/autodl-tmp/c2/runs; SHA=795515630ff6f37a819c7503931c7d7cf6e70a9f272e25ac96730394dd361fb4
pgrep -af "python.*(fejepa|c13/__main__|c2/__main__)|spawn_main" | tee -a $R/gpu_checks.log   # must print nothing
nvidia-smi --query-gpu=name,driver_version,utilization.gpu,memory.used,memory.total --format=csv,noheader | tee -a $R/gpu_checks.log   # about 0 %, under 1,000 MiB used
hostname | tee -a $R/train_times.log; date | tee -a $R/train_times.log
set -o pipefail
for arm in label_free supervised_64; do
  for seed in 0 1 2; do
    python -I c2/__main__.py train --data $D --runs $U --arm $arm --seed $seed --repo .. --config-sha $SHA 2>&1 | tee -a $R/train_${arm}_s${seed}.log || break 2
  done
done
set +o pipefail
date | tee -a $R/train_times.log
```
- Each run prints a start line, one line per epoch (loss and seconds), and ends by printing its status and steps: `{"status": "finished", "steps": 102400}` for a label-free run, `12800` for a supervised one.
- The label-free loss is the mean of log Pi, Pi in N mm. It starts at about 10.5 to 11 and should end near the exact solutions' average over the sampled levels, about 10.3 to 10.6 (numbers, not criteria; the loading spring holds much of the energy, so the loss moves little).
- Each run checkpoints every 5 epochs. Running the block again resumes interrupted runs from their checkpoints; finished runs return at once.
- A run that stops on a non-finite loss, or whose predictions are not finite, records it in its `history.json`. That stop is final: running the block again leaves the run as it is, and the loop goes on to the next run.
- A run that ends with any other error stops the loop (`break 2`). Stop and report. Once the cause is known, running the block again resumes.

## 6. Evaluation (box; about 1 to 3 h on the CPU)

```bash
cd ~/autodl-tmp/FE-JEPA-c2/joint
R=~/autodl-tmp/c2/records; D=~/autodl-tmp/c2/data; U=~/autodl-tmp/c2/runs; SHA=795515630ff6f37a819c7503931c7d7cf6e70a9f272e25ac96730394dd361fb4; W=$(python -c "import os; n = len(os.sched_getaffinity(0)); q = open('/sys/fs/cgroup/cpu.max').read().split() if os.path.exists('/sys/fs/cgroup/cpu.max') else ['max']; c = n if q[0] == 'max' else max(1, int(q[0]) // int(q[1])); print(max(1, min(n, c) - 1))")
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -I c2/__main__.py evaluate --data $D --runs $U --config-sha $SHA --workers $W 2>&1 | tee $R/evaluate.log
```
The last line prints the verdict, the two criterion values, and any missing or non-finite runs.
- A run whose predicted end displacements lie far from the reference takes longer to evaluate: each exact solve then starts far from its solution, and the evaluation has no time limit. If it has not ended after 6 h, report; it goes on unless the owner stops it.

## 7. Return package (box)

```bash
cd ~/autodl-tmp/c2
cp data/manifest.json data/labels/ledger.json runs/verdict.json records/
mkdir -p records/labels records/runs
cp data/labels/eval_*.npz data/labels/tested_*.npz records/labels/
for d in runs/*_s*/; do n=$(basename $d); mkdir -p records/runs/$n; cp $d/history.json $d/attempts.log $d/preds.npz records/runs/$n/ 2>/dev/null; done
tar czf c2_return.tar.gz records
sha256sum c2_return.tar.gz | tee c2_return.sha256
ls -l c2_return.tar.gz      # about 60 MB
```
- Send `c2_return.tar.gz` and its SHA-256.
- It holds the logs, the configuration, the bench, the manifest, the label ledger, the verdict with the metrics of every member, every run's history, attempts and predictions, and the labels of the held-out and tested members.
- The instance files can be regenerated from the stamped code.
- Keep the data and the model states on the box until the verdict has been audited.
