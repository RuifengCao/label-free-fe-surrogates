# RUNBOOK: gate G-C2.2, commands in execution order

**What it runs.** The deciding run of `docs/PRESPEC_G-C2.2.md`: label-free training of the project's transformer on G-C2.1's family of plastic bolted T-stubs, with the stability recipe, judged on a fresh held-out sample in the condensed reading.

**Roles.** The **laptop** is the GPU machine of this gate, the one of the development runs (`probes/c2_dev/README.md`): Windows 11, an NVIDIA GeForce RTX 4070 Laptop GPU with 8 GB, 32 logical processors, Python 3.12 with torch 2.12.1 (CUDA 13.2), numpy 2.4.6 and scipy 1.18.1. The **repo** holds the code, the pre-specification and the records. The **operator** queues the commands, reads their logs and reports.

**When.** After the stamp is in the repository under the tag `prereg-c22` and the operator has checked the pushed commit against the stamped files. The development queue of the laptop is empty, and nothing else trains on the GPU during the runs.

**Where.** One working folder on the laptop, called W below. Every path in this runbook is relative to W, and nothing outside W is read or written:
- `gate/`: the stamped tree, with `gate/joint` and `gate/src`;
- `gate_data/`, `gate_runs/`, `gate_records/`: the instances and labels, the runs, and the logs and records to return.
- None of the four folders exists before section 0.

**How the commands are run on the laptop.** The laptop's job queue, a script outside the stamp that ran the development runs, starts each command as `python -I -u <script> <arguments>` from W with the Python of W's environment, one after another, and writes its output to `logs/<job>.log`. Below, `PY` stands for that start.
- After each stage a guard job reads the stage's exit code. If it is not 0 the guard cancels every later job of this runbook, which is the "stop" of the rules below.
- The owner may pause a training run to use the GPU. The run is then stopped at once and queued again; it resumes from its last finished epoch. Generation and the labels can be paused in the same way. The evaluation cannot resume and is not paused.
- If the laptop restarts, the queue is started again and the interrupted command runs again from where its files left it.
- The queue's scripts and its job files go into the return package (section 6).

**Time and space** (estimates from the development runs).
- Generation: 644 members (512 for training, 64 fresh held-out, 64 former held-out, 4 tested), about 5 min. The 580 members of G-C2.1 took 219 s on this laptop.
- Labels: 132 members at 7 levels, 924 solves. On one core of the development machine 24 members of this mesh took 38 to 248 s each, 131 s in the median: about half an hour with 16 worker processes.
- Training: three runs of 102,400 steps. A step took 0.38 s when the laptop was otherwise idle and up to 0.8 s when it was in use: 11 to 23 h a run, 32 to 68 h in all. The step time is recorded and is not a criterion.
- Predictions: at the end of each run, both readings of 132 members at 7 levels, a few minutes.
- Evaluation: for each of the 5,544 predicted fields (three runs, two readings, 132 members, seven levels), its energy and an exact solve at its end displacement, 15 to 60 s on one core: about 1.5 to 6 h with 16 worker processes.
- Disk: about 3 GB in W. GPU memory: 3.5 GiB at the peak in development.

**Any error or traceback, or any output that differs from what a comment states: stop and report.**

## 0. Preconditions (once)

0a. **The tree.** The operator makes the archive from the stamp's tag, `prereg-c22`, in a clone of the repository and unpacks it into `gate/`:
```bash
ls -d gate gate_data gate_runs gate_records 2>/dev/null | wc -l      # in W; must print 0
git rev-parse --short 'prereg-c22^{commit}'        # must print the commit named in the operator's report of the push check
git -c core.autocrlf=false archive --format=tar -o gate.tar prereg-c22 joint/c22 joint/c2 joint/fejoint joint/docs/G-C2.2_code.sha256 joint/docs/PRESPEC_G-C2.2.md joint/RUNBOOK_C22.md src
sha256sum gate.tar                # recorded in gate_records/preconditions.log
```
- The tree is unpacked from this archive and not checked out by a git on Windows, so that no line ending is converted. Step 0b would show a conversion.

0b. **The files.** In `gate/joint`, from a shell that has `sha256sum` (on the laptop, the Linux shell that mounts W):
```bash
sha256sum -c docs/G-C2.2_code.sha256 | grep -vc ': OK$'      # must print 0
```
- The hash file lists the gate's code and the six repository files it imports.

0c. **The suite**, on the same tree in a Linux shell with pytest (the laptop's environment has none):
```bash
cd joint && FEJEPA_REPO=.. python -m pytest -q -p no:cacheprovider tests/test_hex8i.py tests/test_contact.py tests/test_c2.py tests/test_c22.py | tail -n 1    # "51 passed" and nothing failed
```
- For this step the operator uses a full checkout of the same commit, which holds `tests/`.

0d. **The host**, on the laptop (about 5 min; nothing else on the GPU):
```
PY gate/joint/c22/smoke.py --repo gate --device cuda --workers 4 --out gate_records/smoke
```
- It runs every stage of this runbook on a reduced configuration with family seeds used before G-C2.1's stamp: a coarse mesh, a small model, four epochs, one run interrupted and resumed. It draws, exports, solves and trains nothing of this gate. The folder given to `--out` must be new.
- The last line must be `smoke test of c22 passed`. Its report, `gate_records/smoke/smoke_report.json`, records the machine: the operating system, the Python, numpy, scipy and torch versions, the GPU and its memory, the processors, how worker processes are started (`spawn` on Windows), the solver of the labels and the thread variables. `machine.label_solver` names the sparse solver that is loaded, not one that the check used: the check's systems are small and go to SuperLU either way.
- In the report, `check_labels.ok`, `evaluate.same_with_workers` and `condense.energy_never_higher` must be true, and `machine.thread_variables_of_the_workers` must show 1 three times. `resume` holds the differences between the interrupted and the uninterrupted run; on a GPU they need not be zero. `evaluate.verdict` is that of a small model trained for 16 steps and means nothing.
- The versions must be those named under Roles. A different GPU, or `machine.gpu_memory_in_use_MiB` above 3,000 (the figure counts every program, the check itself included): stop and report.

## 1. Configuration (seconds)

```
PY gate/joint/c22/__main__.py write-config --out gate_records/c22_config.json --repo gate
```
- The first line must be `config sha256 ef5376a4d6c3cc98d7888121439c8d959ee817d332958dd6b1141b25e78734bb` (the value in `docs/PRESPEC_G-C2.2.md`).
- Twenty-eight file hashes follow; they must equal the lines of `docs/G-C2.2_code.sha256` for the same files.
- Six lines `repository ... checked` follow.
- The file written has the same bytes on every system.

## 2. Generation (about 5 min; no solve)

```
PY gate/joint/c22/__main__.py generate --data gate_data
```
- It prints the path of the manifest. The manifest must hold `"n": 644` and the configuration hash of section 1.
- From this command on, members of seed 20261113 exist. It is not run before sections 0 and 1 have passed.
- If interrupted, the command is run again: files already written for the same member and configuration are kept, and any other file is refused.

## 3. Labels (about half an hour)

```
PY gate/joint/c22/__main__.py label --data gate_data --split eval --workers 16
PY gate/joint/c22/__main__.py label --data gate_data --split former --workers 16
PY gate/joint/c22/__main__.py label --data gate_data --split tested --workers 16
PY gate/joint/c22/__main__.py check-labels --data gate_data
```
- Every labelled member prints one line ending in `converged`. A line ending in `NOT CONVERGED`: the commands run on to the check, which then fails.
- The check prints one line with `"labels": 132, "needed": 132, "missing": []` and ending in `"ok": true`.
- If it ends otherwise, or stops with "labels fail the checks", stop and report: no training.
- If a label command is interrupted, it is run again: labels already written are kept.
- The worker processes use one thread each for linear algebra (`c22/data.py`), as G-C2.1's did, unless a thread variable is already set in the queue's environment; the host check's report shows them.
- No training member is labelled.

## 4. Training (the bulk of the time)

```
PY gate/joint/c22/__main__.py train --data gate_data --runs gate_runs --seed 5 --repo gate --config-sha ef5376a4d6c3cc98d7888121439c8d959ee817d332958dd6b1141b25e78734bb
PY gate/joint/c22/__main__.py train --data gate_data --runs gate_runs --seed 6 --repo gate --config-sha ef5376a4d6c3cc98d7888121439c8d959ee817d332958dd6b1141b25e78734bb
PY gate/joint/c22/__main__.py train --data gate_data --runs gate_runs --seed 7 --repo gate --config-sha ef5376a4d6c3cc98d7888121439c8d959ee817d332958dd6b1141b25e78734bb
```
- Each run prints a start line and one line per epoch (loss and seconds), then writes its predictions in both readings, and ends by printing `{"status": "finished", "steps": 102400}`.
- The loss is the mean of ln Π, Π in N mm. It starts near 10.6, and over its last ten epochs it should lie near 10.34 to 10.37, where the two full-length development runs lay (numbers, not criteria).
- Each run checkpoints at the end of every epoch. A run that is interrupted, by a pause or otherwise, is run again and resumes from its checkpoint; every start, resume and end is written to the run's `attempts.log`. A finished run returns at once.
- A run that stops on a non-finite loss, or whose predictions are not finite, records it in its `history.json`. That stop is final: running the command again leaves the run as it is, and the next run starts.
- A run that ends with any other error stops the queue (the guard). Stop and report. Once the cause is known, running the command again resumes.
- A checkpoint that cannot be read is such an error. By the pre-specification the run is then started again from its beginning: its `state.pt` is moved aside, not deleted, and the restart is reported.
- If the three runs have not ended 96 hours after the first started, report to the owner; the runs go on unless the owner stops them.

## 5. Evaluation (about 1.5 to 6 h on the CPU)

```
PY gate/joint/c22/__main__.py evaluate --data gate_data --runs gate_runs --config-sha ef5376a4d6c3cc98d7888121439c8d959ee817d332958dd6b1141b25e78734bb --workers 16
```
- The last line prints the verdict, the two criterion values, and any missing or non-finite runs. The criteria are those of the condensed reading on the fresh held-out members; `gate_runs/verdict.json` holds both readings on all three sets.
- A run whose predicted end displacements lie far from the reference takes longer to evaluate, and the evaluation has no time limit. If it has not ended after 12 h, report; it goes on unless the owner stops it.
- The evaluation does not resume. If it is interrupted it is run again from its start.
- It refuses a run folder that was not made under this configuration, and data whose sets do not have the configured sizes.
- The evaluation prints nothing before its last line; only the processors' load shows that it works. If the system kills a worker process it can wait without end: idle processors and no verdict are the sign. Report.

## 6. Return package

In W, from a shell with `tar` and `sha256sum`:
```bash
cp gate_data/manifest.json gate_data/labels/ledger.json gate_runs/verdict.json gate_records/
mkdir -p gate_records/labels gate_records/run_files gate_records/queue
cp gate_data/labels/eval_*.npz gate_data/labels/former_*.npz gate_data/labels/tested_*.npz gate_records/labels/
for d in gate_runs/label_free_s*/; do n=$(basename $d); mkdir -p gate_records/run_files/$n; cp $d/history.json $d/attempts.log $d/preds.npz $d/preds_condensed.npz $d/preds_base.npz $d/condense.json gate_records/run_files/$n/ 2>/dev/null; done
cp logs/*c22*.log queue/*c22*.json gate_records/queue/
tar czf c22_return.tar.gz gate_records
sha256sum c22_return.tar.gz | tee c22_return.sha256
```
- The operator adds the queue's scripts to `gate_records/queue/` before the archive is made.
- The package holds the precondition records and the smoke report, the configuration, the manifest, the label ledger, the labels of the two held-out samples and the tested members, the verdict with the metrics of every pair in both readings, every run's history, attempts, predictions in both readings, base fields and amplitudes, and the logs and job files of every command. The condensed fields can be computed again from the base fields, the raw fields and the amplitudes.
- The instance files can be regenerated from the stamped code.
- The data and the model states stay on the laptop until the verdict has been audited.
