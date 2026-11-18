# RUNBOOK: gate G-C2.3, commands in execution order

**What it runs.** The run of `docs/PRESPEC_G-C2.3.md`, in two parts. Part 1: the three label-free networks of G-C2.2 predict a third sample of T-stubs, and the spread of their forces is compared with a fixed threshold. Part 2: the same network is trained on reference solutions of the 512 training members, three seeds, and compared with the label-free networks on the same sample.

**Roles.** The **laptop** is the GPU machine of this gate, the one of G-C2.2 (`RUNBOOK_C22.md`): Windows 11, an NVIDIA GeForce RTX 4070 Laptop GPU with 8 GB, 32 logical processors, Python 3.12 with torch 2.12.1 (CUDA 13.2), numpy 2.4.6 and scipy 1.18.1. The **repo** holds the code, the pre-specification and the records. The **operator** queues the commands, reads their logs and reports.

**When.** After the stamp is in the repository under the tag `prereg-c23` and the operator has checked the pushed commit against the stamped files. Nothing else trains on the GPU during the runs.

**Where.** One working folder on the laptop, called W below, the one of G-C2.2. Every path in this runbook is relative to W, and nothing outside W is read or written:
- `gate3/`: the stamped tree, with `gate3/joint` and `gate3/src`;
- `gate3_data/`, `gate3_runs/`, `gate3_records/`: the instances and labels, the runs, and the logs and records to return;
- `gate_runs/label_free_s5/state.pt`, `gate_runs/label_free_s6/state.pt`, `gate_runs/label_free_s7/state.pt`: the state files that G-C2.2's runs left in W. They are read and not changed.
- None of the four `gate3` folders exists before section 0. No other file of G-C2.2 in W is read. No command of this runbook is given `gate_data` or `gate_runs` as its data or runs folder; `verdict` refuses a runs folder that holds the verdict of another configuration, or that holds no run and no rows of this gate.

**How the commands are run on the laptop.** As in G-C2.2: the laptop's job queue, a script outside the stamp, starts each command as `python -I -u <script> <arguments>` from W with the Python of W's environment, one after another, and writes its output to `logs/<job>.log`. Below, `PY` stands for that start.
- After each stage a guard job reads the stage's exit code. If it is not 0 the guard cancels every later job of this runbook, which is the "stop" of the rules below. The guard reads nothing but the exit code, so every stop of this runbook is an exit code other than 0: a refusal, an error, a failed check of labels, predictions that are not finite, an evaluation of an arm with a run that has no predictions, and a verdict whose identity check is not `OK` or whose part 1 is not the one first written.
- The owner may pause a training run to use the GPU. The run is then stopped at once and queued again; it resumes from its last finished epoch. Generation and the labels can be paused in the same way. The host check of 0e, the predictions of section 4, the two evaluations and the verdicts do not resume and are not paused.
- If the laptop restarts, the queue is started again and the interrupted command runs again from where its files left it. The host check is the exception: it refuses a folder that is not empty, so it is queued again with a new folder for `--out`.
- **After a stop.** A guard that has stopped the queue leaves a done file for every cancelled job. Nothing of this runbook is queued again before the operator has reported the stop and the owner has answered.
  - *Final stops* are not continued: predictions of a label-free state that are not finite; a check of labels whose line shows a level that did not converge (`"converged": false`), levels that are not the configured ones (`"levels_ok": false`) or a limit that is not kept (a `false` under `"within_limits"`); a verdict whose identity check is not `OK` or whose part 1 is not the one first written. After predictions that are not finite, section 4 says what is still run so that the verdict is on record.
  - *A stop that came from the host* is continued once its cause is removed: a restart during a command that does not resume, a full disk, a busy GPU, or a check of labels that fails only because labels are `"missing"` after a label command was cut off. The operator moves into `gate3_records/stopped_<n>/`, which goes into the return package: the job files and the done files of the failed stage, of the guard that stopped and of the cancelled jobs; the files of the stage's continuations, if it had been paused; and the log of the failed attempt. The jobs are then written again with the generator (`--from`; it refuses the jobs of part 2 unless the guard after part 1's verdict ended with 0). The move and its reason are reported.
  - Once `gate3_runs/verdict_part1.json` exists, the evaluation of the label-free arm is not queued again: every later verdict compares the SHA-256 of its rows file with the kept one. If that file is lost, report.
- The gate's commands and the host check write no bytecode. `gate3/` therefore never holds a `__pycache__` folder; 0b and section 9 check it, because Python would run a cached file in place of a stamped source.
- The job files and the queue's scripts that go into the return package are named in section 9.

**Before the stamp** (not part of the gate; `docs/PRESPEC_G-C2.3.md`, "Procedure", step 1). The draft tree is unpacked into `pre3/`, and six jobs run from it and write into `pre3_records/` only: the host check; `probes/c23_precheck/repredict.py`, which predicts G-C2.2's members again from the three state files and compares the fields with G-C2.2's prediction files; `probes/c23_precheck/pilot_labels.py`, which solves 32 members of a family seed used before G-C2.1's stamp at the eight levels of the training labels; and the three timing probes. They read `gate_data` and `gate_runs` and change nothing there, and they draw nothing of this gate. The second job ends with 0 also when the fields differ: the operator reads `all_identical` and the largest differences in `pre3_records/repredict/repredict.json`. Their outputs are quoted in the pre-specification at the stamp and go into the return package (section 9).

**Time and space** (estimates).
- Generation: 644 members (512 for training, 64 of the third sample, 64 of G-C2.2's fresh sample, 4 tested), about 5 min; G-C2.2 exported as many in 265 s.
- Labels of the held-out members: 132 members at 7 levels, about half an hour with 16 worker processes, as in G-C2.2.
- Predictions of the label-free states: both readings of 132 members at 7 levels, about ten minutes each; the check made before the stamp predicted G-C2.2's 132 members from each state in ten and a half minutes.
- Evaluation of an arm: 5,544 exact solves, as many as G-C2.2's evaluation, which took two hours with 16 worker processes.
- Part 1 is final about three and a quarter hours after section 2 starts.
- Labels of the training members: 512 members at 8 levels. A member took 117 s at seven levels in the median of G-C2.2's ledger; the eighth level is the smallest. One to one and a half hours with 16 worker processes.
- Supervised training: three runs of 102,400 steps. The step time is the one `probes/c2_timing/step_cost.py` gave on this laptop before the stamp (`docs/PRESPEC_G-C2.3.md`, "Budget"); it is not a criterion.
- Disk: less than 1 GB in W; G-C2.2's data and runs take 0.4 GB there. GPU memory: expected below the 3.5 GiB of G-C2.2's runs, because the supervised training holds no energy on the device; nothing before the first supervised run measures it at full size.

**Any error or traceback, or any output that differs from what a comment states: stop and report.**

## 0. Preconditions (once)

0a. **The tree.** The operator makes the archive from the stamp's tag, `prereg-c23`, in a clone of the repository and unpacks it into `gate3/`:
```bash
ls -d gate3 gate3_data gate3_runs gate3_records 2>/dev/null | wc -l      # in W; must print 0
git rev-parse --short 'prereg-c23^{commit}'        # must print the commit named in the operator's report of the push check
git -c core.autocrlf=false archive --format=tar -o gate3.tar prereg-c23 joint/c23 joint/c22 joint/c2 joint/fejoint joint/docs/G-C2.3_code.sha256 joint/docs/PRESPEC_G-C2.3.md joint/RUNBOOK_C23.md src
sha256sum gate3.tar                # recorded in gate3_records/preconditions.log
```
- The tree is unpacked from this archive and not checked out by a git on Windows, so that no line ending is converted. Step 0b would show a conversion.
- `joint/docs/G-C2.3_code.sha256` must be in the tree: without it every command but `write-config` refuses to run.

0b. **The files.** In `gate3/joint`, from a shell that has `sha256sum` (on the laptop, the Linux shell that mounts W):
```bash
sha256sum -c docs/G-C2.3_code.sha256 | grep -vc ': OK$'      # must print 0
```
- The hash file lists the gate's code and the six repository files it imports.
- `find gate3 -name __pycache__ | wc -l` must print 0, here and whenever the operator looks again.

0c. **The suite**, on the same tree in a Linux shell with pytest (the laptop's environment has none):
```bash
cd joint && FEJEPA_REPO=.. python -m pytest -q -p no:cacheprovider tests/test_hex8i.py tests/test_contact.py tests/test_c2.py tests/test_c22.py tests/test_c23.py | tail -n 1    # "69 passed" and nothing failed
```
- For this step the operator uses a full checkout of the same commit, which holds `tests/`. On two processor cores the suite took 22 to 29 minutes; two tests of `tests/test_c23.py`, which train small networks and solve reference solutions, take most of it.

0d. **The state files**, in W, from the shell of 0b:
```bash
sha256sum gate_runs/label_free_s5/state.pt gate_runs/label_free_s6/state.pt gate_runs/label_free_s7/state.pt
```
- The three lines must begin with `5859ca7737e94b502660dddd082891a18f981b6df4228ff2a7c59d865ca7dcf5`, `adb9992ae19846afd56e9f75d9dfe533edcf5a47fbca9c6a210f18581032c0b1` and `80c56c73af04b4321f52a9acfd037a476837bfa6ec0cc8e55524dbf63988bc53`, the values pinned in `c23/config.py`.
- If a file is missing it is taken from the owner's archive of the three states, into a new folder, and section 4 is given that path. A file with another hash is not used: stop and report.

0e. **The host**, on the laptop (about 10 min; nothing else on the GPU):
```
PY gate3/joint/c23/smoke.py --repo gate3 --device cuda --workers 4 --out gate3_records/smoke
```
- It runs every stage of this runbook, in this runbook's order, on a reduced configuration with family seeds used before G-C2.1's stamp: a coarse mesh, a small model, three label-free runs of two epochs that stand for G-C2.2's, a supervised run of four epochs interrupted and resumed. It draws, exports, solves and trains nothing of this gate, and it needs no stamp. The folder given to `--out` must be new or empty.
- The last line must be `smoke test of c23 passed`. Its report, `gate3_records/smoke/smoke_report.json`, records the machine.
- In the report, `check_labels_held_out.ok`, `check_labels.ok`, `evaluate.same_with_workers`, `evaluate.identity.ok` and `evaluate.part1_same_as_first` must be true. `resume` holds the differences between the interrupted and the uninterrupted run; on a GPU they need not be zero. The verdicts in the report are those of small models trained for a few steps and mean nothing.
- `machine.thread_variables_of_the_workers` must show one thread for each of the three variables: the processor time of the labels, which part 2 reports, depends on it.
- The stand-in networks are far from the reference, so the host check scales the tolerance of its identity check to their values. If that check fails on the GPU, predictions made from a state file differ from those made in the run that wrote it: stop and report. `evaluate.identity.largest_difference` is reported in any case; the pre-specification quotes the value of the run made before the stamp.
- The versions must be those named under Roles. A different GPU, or `machine.gpu_memory_in_use_MiB` above 3,000: stop and report.

## 1. Configuration (seconds)

```
PY gate3/joint/c23/__main__.py write-config --out gate3_records/c23_config.json --repo gate3 --config-sha 3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e
```
- The first line must be `config sha256 3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e` (the value in `docs/PRESPEC_G-C2.3.md`).
- The second line must be `state files pinned: True` and the third `code as stamped: True`.
- Thirty-five file hashes follow; they must equal the lines of `docs/G-C2.3_code.sha256` for the same files.
- Six lines `repository ... checked` follow.
- Given `--config-sha`, the command ends with a code other than 0 unless the first three lines are as stated, and the queue stops before anything is drawn.

## 2. Generation (about 5 min; no solve)

```
PY gate3/joint/c23/__main__.py generate --data gate3_data --config-sha 3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e
```
- It prints the path of the manifest. The manifest must hold `"n": 644` and the configuration hash of section 1.
- From this command on, members of seed 20261118 exist. It is not run before sections 0 and 1 have passed, and it refuses another configuration hash than the stamped one before it draws.
- If interrupted, the command is run again: files already written for the same member and configuration are kept, and any other file is refused.

## 3. Labels of the held-out members (about half an hour)

```
PY gate3/joint/c23/__main__.py label --data gate3_data --split third --workers 16
PY gate3/joint/c23/__main__.py label --data gate3_data --split eval --workers 16
PY gate3/joint/c23/__main__.py label --data gate3_data --split tested --workers 16
PY gate3/joint/c23/__main__.py check-labels --data gate3_data --splits third eval tested
```
- Every labelled member prints one line ending in `converged`. A line ending in `NOT CONVERGED`: the commands run on to the check, which then fails.
- The check prints one line with `"labels": 132, "needed": 132, "missing": []` and ending in `"ok": true}`.
- If it ends otherwise, or stops with "labels fail the checks", the queue stops: no prediction. Report. A level that did not converge or a limit that is not kept is final. A check that fails only because labels are `"missing"` after a label command was cut off is not: see "After a stop".
- If a label command is interrupted, it is run again: labels already written are kept. The label commands use the same pool of worker processes as the evaluation, so the warning of section 5 holds for them: idle processors and no new line are the sign of a worker that the system has killed. Report.

## 4. Predictions of the label-free states (about ten minutes each)

```
PY gate3/joint/c23/__main__.py predict-label-free --data gate3_data --runs gate3_runs --seed 5 --state gate_runs/label_free_s5/state.pt --repo gate3 --config-sha 3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e
PY gate3/joint/c23/__main__.py predict-label-free --data gate3_data --runs gate3_runs --seed 6 --state gate_runs/label_free_s6/state.pt --repo gate3 --config-sha 3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e
PY gate3/joint/c23/__main__.py predict-label-free --data gate3_data --runs gate3_runs --seed 7 --state gate_runs/label_free_s7/state.pt --repo gate3 --config-sha 3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e
```
- Each prints a start line, unless its predictions exist already, and ends with `{"status": "finished", "predict_seconds": ...}`.
- The command refuses a state file whose SHA-256 is not the pinned one, or that is not the end of G-C2.2's run of that seed. Nothing is trained and the state file is not changed.
- Predictions that are not finite end the command with a code other than 0, and the queue stops. That end is final: the command, run again, returns the same end and predicts nothing. By the pre-specification the verdict is INVALID. So that it is written, the operator queues without guards (the generator's set R): the three prediction commands again, of which those that have ended return at once and those that the guard cancelled now run; then the two commands of section 5. Both of these end with a code other than 0, and the verdict's line shows `"identity": "INVALID"`. Report.
- If interrupted, the command is run again from its start.

## 5. Evaluation of the label-free arm, and part 1 (about 2 h on the CPU)

```
PY gate3/joint/c23/__main__.py evaluate --data gate3_data --runs gate3_runs --config-sha 3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e --arm label_free --workers 16
PY gate3/joint/c23/__main__.py verdict --data gate3_data --runs gate3_runs --config-sha 3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e
```
- The first command writes `gate3_runs/rows_label_free.json` and prints the status of the three runs, each `finished`. It does not resume: if it is interrupted it is run again from its start. If it has not ended after 8 h, report; it goes on unless the owner stops it. If the owner stops it and does not let it run again, both parts stay INCOMPLETE.
- It prints nothing before its last line; only the processors' load shows that it works. If the system kills a worker process it can wait without end: idle processors and no line are the sign. Report.
- The second command takes seconds. Its line must show `"identity": "OK"`, `"comparison": "INCOMPLETE"`, `"not_evaluated": ["supervised_512"]` and `"part1_same_as_first": true`; `"self_check"` is `PASS` or `FAIL` and `"ranking"` is `HOLDS`, `DOES NOT HOLD` or `NOT EVALUABLE`; `"missing"` lists the three supervised runs, which do not exist yet.
- **Part 1 is final here.** The command has written the whole verdict to `gate3_runs/verdict_part1.json` as well. No later command overwrites that file, and it is written only while no training member has a label. Part 1 as kept includes the SHA-256 of `gate3_runs/rows_label_free.json`: a later verdict that reads other label-free rows says that its part 1 is not the kept one. The operator reports part 1 to the owner when this line is read, with the SHA-256 of `gate3_runs/verdict_part1.json` and of `gate3_runs/rows_label_free.json`; the queue does not wait for that.
- `"identity": "INVALID"`: the label-free runs are not G-C2.2's. The command ends with a code other than 0 and the queue stops; nothing further is run. Report.

## 6. Labels of the training members (one to one and a half hours)

```
PY gate3/joint/c23/__main__.py label --data gate3_data --split train --workers 16
PY gate3/joint/c23/__main__.py check-labels --data gate3_data
```
- The check prints one line with `"labels": 644, "needed": 644, "missing": []` and ending in `"ok": true}`.
- Otherwise the queue stops. By the pre-specification the supervised arm is then not trained and part 2 stays INCOMPLETE; part 1 stands; no other solver settings are tried. Report. That holds for a level that did not converge or a limit that is not kept; a check that fails only because labels are `"missing"` after the label command was cut off is continued as "After a stop" says. The warning of section 3 about a killed worker holds here too.

## 7. Supervised training

```
PY gate3/joint/c23/__main__.py train --data gate3_data --runs gate3_runs --seed 5 --repo gate3 --config-sha 3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e
PY gate3/joint/c23/__main__.py train --data gate3_data --runs gate3_runs --seed 6 --repo gate3 --config-sha 3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e
PY gate3/joint/c23/__main__.py train --data gate3_data --runs gate3_runs --seed 7 --repo gate3 --config-sha 3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e
```
- Each run prints a start line and one line per epoch (loss and seconds), then writes its predictions in both readings, and ends by printing `{"status": "finished", "steps": 102400}`.
- The loss is the mean squared error of the displacement relative to the loading displacement. No run of this length exists to compare with; the loss should fall over the first epochs.
- Before it starts or resumes, a run compares the training members' instance and label files with the manifest and the ledger. A difference is an error: the queue stops. Report.
- Each run checkpoints at the end of every epoch. A run that is interrupted, by a pause or otherwise, is run again and resumes from its checkpoint; every start, resume and end is written to the run's `attempts.log`. A finished run returns at once.
- A run that stops on a non-finite loss, or whose predictions are not finite, records it in its `history.json` and ends with code 0. That stop is final: running the command again leaves the run as it is, the next run starts, and the seed enters the comparison with infinite errors.
- A run that ends with any other error stops the queue. Report. Once the cause is known, running the command again resumes.
- A checkpoint that cannot be read is such an error. As in G-C2.2, the run is then started again from its beginning: its `state.pt` is moved aside, not deleted, and the restart is reported.
- If the three runs have not ended 60 hours after the first started, report to the owner; the runs go on unless the owner stops them. A run that the owner stops and does not let run again leaves part 2 INCOMPLETE.

## 8. Evaluation of the supervised arm, and part 2 (about 2 h on the CPU)

```
PY gate3/joint/c23/__main__.py evaluate --data gate3_data --runs gate3_runs --config-sha 3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e --arm supervised_512 --workers 16
PY gate3/joint/c23/__main__.py verdict --data gate3_data --runs gate3_runs --config-sha 3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e --final
```
- The first command writes `gate3_runs/rows_supervised_512.json`; the rules of section 5 hold. A run that stopped on a non-finite loss is listed as `non-finite` and does not stop the queue; a run without predictions and without such a stop does. While no supervised run has ended the command refuses to run and writes nothing. It also refuses a run that was trained on other labels than those now in the ledger.
- The second command reads both rows files. It refuses rows that were computed from other files than those now present: the manifest, the ledger entries of the held-out and tested members, and the prediction files of the runs. The labels of the training members, added in section 6, are not among them.
- Its line holds the four words of the verdict. `"self_check"`, `"ranking"` and `"identity"` must be those of section 5, `"part1_same_as_first"` must be true and `"not_evaluated"` and `"missing"` must be empty; otherwise the command ends with a code other than 0. The verdict of part 1 is the one in `gate3_runs/verdict_part1.json`, whatever a later verdict says.
- The operator checks that `gate3_runs/verdict_part1.json` and `gate3_runs/rows_label_free.json` have the SHA-256 reported in section 5, and that the kept file shows `"not_evaluated": ["supervised_512"]` and `"training_members_labelled": 0`.

## 9. Return package

In W, from a shell with `tar` and `sha256sum`:
```bash
cp gate3_data/manifest.json gate3_data/labels/ledger.json gate3_runs/verdict.json gate3_runs/verdict_part1.json gate3_runs/rows_label_free.json gate3_runs/rows_supervised_512.json gate3_records/
mkdir -p gate3_records/labels gate3_records/run_files gate3_records/queue gate3_records/before_stamp
cp gate3_data/labels/third_*.npz gate3_data/labels/eval_*.npz gate3_data/labels/tested_*.npz gate3_records/labels/
for d in gate3_runs/label_free_s*/ gate3_runs/supervised_512_s*/; do n=$(basename $d); mkdir -p gate3_records/run_files/$n; cp $d/history.json $d/attempts.log $d/preds.npz $d/preds_condensed.npz $d/preds_base.npz $d/condense.json gate3_records/run_files/$n/ 2>/dev/null; done
cp logs/*c23*.log queue/*c23*.json gate3_records/queue/
cp tools/guard.py tools/hold.py gate3_records/queue/
cp pre3_records/step_cost.json pre3_records/time_curve.json pre3_records/f2_energy_cost.json pre3_records/smoke/smoke_report.json pre3_records/repredict/repredict.json pre3_records/pilot_labels/pilot_labels.json gate3_records/before_stamp/
find gate3 -name __pycache__ | wc -l      # must print 0
tar czf c23_return.tar.gz gate3_records
sha256sum c23_return.tar.gz | tee c23_return.sha256
```
- The operator adds the generator of the job files to `gate3_records/queue/`. The queue's scripts in the package are the guard, the waiting job and that generator. The scripts with which the owner pauses and continues a run, the runner and the machine's set-up log are not in it.
- The package holds the precondition records and the host check's report, the outputs of the jobs run before the stamp, the configuration, the manifest, the label ledger, the labels of the third sample, of G-C2.2's fresh sample and of the tested members, both rows files, the verdict of part 1 and the final verdict, every run's history, attempts, predictions in both readings, base fields and amplitudes, and the logs and job files of every command.
- The labels of the training members and the instance files can be computed again from the stamped code; they and the supervised model states stay on the laptop until the verdict has been audited.
