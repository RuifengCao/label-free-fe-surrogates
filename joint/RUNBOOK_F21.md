# RUNBOOK: gate G-F2.1, commands in execution order

**What it runs.** The run of `docs/PRESPEC_G-F2.1.md`: the label-free surrogate of the CHS flange-plate splices is trained three times, with the seeds 5, 6 and 7, each through the two cycles of the recipe, and read on 64 members of the family that are drawn after the stamp.

**Roles.** The **host** is a hosted notebook runtime with one GPU, the compute of the development: in the development's sessions an NVIDIA RTX PRO 6000 with 95 GiB, 48 processors, Python 3.13.16, torch 2.14.1 (CUDA 13.0), numpy 2.4.6 and scipy 1.16.3. The **queue** is a notebook outside the stamp that runs the steps of a task file on the host, one after another. The **operator** writes the task file, reads the records and reports. A **helper** starts each session of the host; the helper decides nothing and changes nothing, except that after a stop the helper moves a folder aside in the store when the operator asks for it in writing (section 11). The **repository** holds the code, the pre-specification and, after the run, the records.

**When.** After the commit of the stamp is in the repository and the operator has checked it (section 0).

**Where.** One working folder on the host's local disk, called W below. Every path in this runbook is relative to W, and no command reads or writes outside W:
- `code/`: the stamped tree, with `code/joint` and `code/src`, unpacked from the code archive;
- `data/`: the development's members, 128 for training and 31 with labels;
- `data_thin/`: the 32 further training members;
- `data_gate/`: the sample, with `sample.json`, the members and their labels;
- `runs/<preset>/label_free_s<seed>/`: the two cycles of each seed;
- `runs_gate/label_free_s<seed>/`: the predictions of each seed on the sample;
- `records/`, `host_check/`, `logs/`, `marks/`, `bundles/`: what the commands and the queue write beside them.

W does not outlive a session. The queue copies what must outlive it to the task's folder in a shared store while the steps run and at their end, and copies it back at the start of the next session ("What a session starts from"). Nothing of that store is named in the commands.

**How the commands are run.** The queue starts each step as `python -I -u code/joint/f21/__main__.py <arguments>` from W and writes its output to `logs/<step>.log`. Below, `PY` stands for that start, `SHA` for the configuration hash of the pre-specification, `N` for the number of worker processes that the queue gives (24 on the development's runtime, two fewer than the processors on a smaller one) and `H` for the hours that the session has left, less a quarter of an hour.
- **A step that ends with an exit code other than 0 stops the session, and no later step is run.** This is the "stop" of the rules below. Every stop of this runbook is such an exit code: a refusal, an error, a preload that is not on target, a failed check of labels, a training that stopped on a non-finite value, predictions that are not finite, a final verdict that is not complete.
- A step is complete when its completion files are there (the table below). A complete step is skipped. A step that ends with the exit code 0 without its completion files has used up the session's time: the session ends there and the next one goes on with the same command, which resumes.
- At the start of every session the queue compares the code archive with the SHA-256 in the task file, releases a runtime whose GPU the task does not list, and stops if the versions of Python, torch, numpy or scipy differ from those of the task's first session. The first command of the task prints the versions of numpy, scipy, pypardiso, mkl and torch into its log.
- The commands write no bytecode, and they refuse to run while a `__pycache__` folder lies in one of the stamped packages: Python would run a cached file in the place of a stamped source. The code folder of W comes from the archive and holds none.
- The commands that open pools of worker processes (`generate`, `label`, `check-labels`, `evaluate`) give each process one thread for linear algebra, unless the queue has set the thread variables itself. The commands `train` and `predict` run without the sparse solver's libraries, as every training of the development did.
- The commands that solve (`generate`, `label`, `evaluate`) refuse a host whose reference solves would not use PARDISO, the configured solver.

**The steps and what completes each.** The queue writes a mark for a step that ended with the exit code 0; a step without a mark below is complete by its files alone.

| Step | Section | Complete when these exist |
|---|---|---|
| `check_stamp` | 1 | its mark and `records/config.json` |
| `host_check` | 1 | its mark and `host_check/smoke.json` |
| `data_train` | 2 | its mark and `data/manifest.json` |
| `data_thin` | 2 | its mark and `data_thin/manifest.json` |
| `data_sample` | 3 | its mark, `data_gate/manifest.json` and `data_gate/sample.json` |
| a cycle of a seed | 4 | `condense.json` in the cycle's folder, which the training writes last |
| the predictions of a seed | 5 | `runs_gate/label_free_s<seed>/history.json` |
| `evaluate_dev`, `evaluate_sample` | 6 | its mark and the evaluation file |
| `verdict` | 7 | its mark, `records/verdict.json` and `records/verdict.txt` |

**What a session starts from.** The queue restores to W the marks, the records, the logs and every file of the runs' folders (the state files and the prediction files among them). A data folder comes back whole from its archive, which the queue writes when the folder's step is complete. If a data step was cut off, only the folder's small records come back (the manifest, the generation log, the ledger, the label summary and `sample.json`), and the step's commands make the missing exports and labels again: `generate` and `label` keep a file that is there and make one that is not, and `check-labels` compares every file with the manifest and the ledger.

**After a stop** nothing of this runbook is run again before the operator has reported the stop and the owner has answered. The operator and the helper keep this rule; the queue does not. If a session is started all the same, the queue skips the complete steps and goes on with the others under the code's own refusals: a training that stopped for good ends its step with the same error at once, a data step or a check that failed for good fails again, and after predictions that were not finite the session runs the steps that are left, which are the closing steps of section 10 for that case. No number changes by such a session; it is reported as a difference from this runbook.
- *Stops for good* are not continued: a preload that did not converge or is not on target; a check of labels whose line shows a level that did not converge, a limit that is not kept or a member that the evaluation could not use; an export or a label that ends with the same error when it is run again; a training that stopped on a non-finite value; predictions that are not finite. The pre-specification says what each means for the verdict ("Stop conditions"). After a training or predictions stopped for good, sections 10 and 11 say what is still run.
- *A stop that came from the host* is continued in the next session once its cause is removed: a session that ended inside a command that does not resume (the host check, an evaluation), a full disk, a busy GPU, a check of labels that fails only because labels are missing after a label command was cut off (its line then names them under `"missing"`, or says that no label is written).
- *A step that waits.* The data steps and the evaluations print a line for each member they finish, and a training a line about every half minute. **If the log of a running step shows no new line for half an hour, report**: the session is then ended by hand, and the step starts again in the next one. The host check ends a stage of its own that has not ended after 45 minutes and fails.

**Time** (estimates from the development's records on its runtime; no criterion): the data steps about half an hour in all; a first cycle about 9.5 hours and a second about 4.8 hours for one seed trained alone; the predictions a few minutes a seed; the evaluation of the 31 members about half an hour for three seeds; the evaluation of the sample two to three hours; the verdict seconds. On a runtime with fewer processors or another GPU the times differ: on the 12 processors and the A100 of the timing of 25 November 2026, about two and a half times as long for the processor steps and 2.2 times for the trainings. A session lasts at most 20 hours. The queue starts a step only in a session that has the step's minimum time left, which the task file lists: eight hours for the evaluation of the sample and two for that of the development's members, neither of which resumes.

**Any error or traceback, or any output that differs from what a comment states: stop and report.**

## 0. Before the first session (the operator, once)

0a. The stamp. Read the commit of the stamp back from the repository. In `joint/` of that commit, `sha256sum -c docs/G-F2.1_code.sha256` must pass for all 48 files (the 45 files of the code and the three coupon curves), and `python -I f21/__main__.py write-config --out <any file>` must print the configuration hash that `docs/PRESPEC_G-F2.1.md` holds. (It also prints `stamped code: no` if the tree holds bytecode folders from tests; on the host it must print `yes`.)

0b. The seed and the day. The seed of the sample is the one in `f21/stamp_day.py`, which is part of the hashed configuration and which the pre-specification names ("The sample"). The commit of the stamp is the last commit on the branch that changes `docs/G-F2.1_code.sha256`. Its day in UTC is printed by

    TZ=UTC git log -1 --date=format-local:%Y%m%d --format=%cd -- joint/docs/G-F2.1_code.sha256

By the owner's decision of 25 November 2026 the seed stands whatever that day is; a rule that tied the two was dropped before the stamp (pre-specification, "The sample"). The operator writes the commit, its day and the seed into the report before the first session.

0c. The code archive: `git archive` of the commit of the stamp, restricted to what the commands need: `joint/f21`, `joint/f2`, `joint/f1`, `joint/c2`, `joint/c22`, `joint/fejoint`, `joint/docs/G-F2.1_code.sha256`, `joint/docs/PRESPEC_G-F2.1.md`, `joint/RUNBOOK_F21.md`, `src` and the licence files. Its SHA-256 goes into the task file, and the queue refuses an archive with another hash.

0d. The task file: the steps of sections 1 to 7 in their order, with SHA filled in, the completion files of the table above, the GPUs that the task accepts and the trainings at the same time or one after another, both by the rule of the pre-specification ("Host and budget"). Every training comes before the first prediction on the sample. The task file is returned with the records (section 8). The queue's notebook is not part of the repository, because it names the shared store and the people who use it; it is kept with the task's folder in the store.

## 1. Stamp and host (minutes)

    PY write-config --out records/config.json --config-sha SHA
    PY smoke --out host_check --device cuda --workers N

- `write-config` prints the configuration hash, the four pinned hashes of the recipe, the hash of each of the 48 stamped files, `stamped code: yes`, the library versions and `linear solver: pardiso`. With `--config-sha` it ends with an error unless the hash is SHA, the code is the stamped code and the host's reference solves use PARDISO, the solver of the development: the solutions do not depend on the solver beyond rounding, but the pre-specification names it, and without it the labels and the evaluations take several times as long.
- `smoke` is the host check: every step of the gate on a reduced configuration, with stand-in networks and a sample of two drawn with a day of the past (20260102), in three stages that are processes of their own (the data and the sample; the trainings and the predictions; the evaluations and the verdict). It needs no stamp and draws nothing of the gate. Its last line must hold `"ok": true` and name each stage as `ended with exit code 0`, and `host_check/smoke.json` then lists each of its nineteen checks as true. Its verdict is that of stand-in networks and means nothing. It should take a few minutes on the host.
- The host check refuses a folder that is not empty. If a session ends inside it, the next session starts it again in an empty folder. A host check that failed is not run again under the same task: its record comes back with the next session, and the check refuses the folder. By the pre-specification a failure there means a new stamp, and with it a new task with a folder of its own.

## 2. The development's members (about 15 minutes)

    PY chain --do "generate --what train --data data --config-sha SHA --workers N"
             --do "label --what train --data data --config-sha SHA --workers N"
             --do "check-labels --what train --data data --config-sha SHA --workers N"
    PY generate --what thin --data data_thin --config-sha SHA --workers N

- `generate` prints one line for each member that it exports, ending `preload ok`, and the path of the manifest as its last line; a run that resumes prints lines for the members that were still missing only. 159 members go to `data/` and 32 to `data_thin/`. **It ends with an error if the preload of any member of the folder did not converge or is not on target**, or if the generation log holds no preload record for a member: a stop for good.
- `label` prints one line for each of the 31 labelled members that it solves, each ending `converged`, and then `labelled 31`.
- `check-labels` prints one line of JSON with `"ok": true`. Besides the development's checks of the labels it tests that every label was solved with the configured solver and, for each labelled member, what the evaluation will need of it: that the rotation of the measuring ring rises along the labelled path and that the reference code evaluates every labelled state. Anything else than `"ok": true` is a stop.
- `chain` runs its commands in one process, one after another, and ends at the first error. It takes the data commands and `evaluate` only, never a command that trains or predicts.

## 3. The sample (about 15 minutes)

    PY chain --do "generate --what sample --data data_gate --config-sha SHA --workers N"
             --do "label --what sample --data data_gate --config-sha SHA --workers N"
             --do "check-labels --what sample --data data_gate --config-sha SHA --workers N"

- The seed of the sample is in the configuration; no command takes it as an argument. `generate` writes `data_gate/sample.json`, with the seed, the configuration hash and the hash of the drawn parameters, before it exports the first member, and from then on refuses that folder under any other configuration and any draw that differs from the recorded one. It exports 64 members named `gate_0000` to `gate_0063`, and ends with an error for a preload that is not on target, as in section 2.
- `label` ends with `labelled 64`; `check-labels` prints `"ok": true` and `"members": 64`.
- **From here on the sample exists.** No command of section 4 is given `data_gate`.

## 4. Training (the GPU)

For each seed S of 5, 6 and 7:

    PY train --cycle first --seed S --data data --runs runs --config-sha SHA --max-hours H
    PY train --cycle second --seed S --data data --runs runs --extra-data data_thin --config-sha SHA --max-hours H

- The pre-specification says whether the three seeds are trained one after another or at the same time ("Host and budget"). At the same time, the three commands of a cycle are started by one step,

      PY together --do "train --cycle first --seed 5 ..." --do "train --cycle first --seed 6 ..." --do "train --cycle first --seed 7 ..." --logs logs/together_first

  and likewise for the second cycle. `together` ends when all three have ended, with an error if one of them did. A training that it started ends itself before its next step once the process of `together` is gone, so that a session which stops that step stops all three; it tests this by the process number. If the system has given that number to another process, or still lists the ended one, the training goes on until the session ends and resumes from its last checkpoint like any other.
- A training prints a line every half minute or so with the epoch, the loss, the seconds of the epoch and the actions of the cap. It writes a checkpoint at the end of an epoch once ten minutes have passed since the last one, and `progress.json` every minute. It tests its time at the end of each epoch: when `H` hours have passed it writes a checkpoint, ends with the exit code 0 and goes on when it is started again.
- After its last step a cycle writes `history.json` with `"status": "finished"`, then predicts the 31 members of the development and writes `condense.json` last. **A cycle is finished only when `condense.json` is there.** If a session ends inside those predictions, the record already says finished and the step is not complete: the same command, run again, makes the predictions and leaves the state as it is. The gate's commands hold to this themselves: the second cycle, the predictions on the sample and the verdict count a cycle as finished only with its `condense.json`.
- The second cycle refuses to start unless the same seed's first cycle is finished. Both refuse a seed that is not 5, 6 or 7.
- **A non-finite loss**, or predictions at the end of a cycle that are not finite, end the command with an error: a stop for good. The command then refuses to start any cycle that has not been started; a cycle that is under way goes on when its command is run again (section 10).
- While a training runs, the operator may read `progress.json` and `snapshots.json`. They hold what the networks give on the members of the development. No decision is taken on them.

## 5. Predictions on the sample (the GPU, a few minutes a seed)

**After every training of all three seeds**, for each seed S:

    PY predict --seed S --runs runs --data-gate data_gate --runs-gate runs_gate --config-sha SHA

- It prints `{"status": "finished", ...}` and writes `runs_gate/label_free_sS/` with the fields in both readings and a `history.json` that names the two states of the seed and the four prediction files by their SHA-256.
- **It refuses while any cycle of any seed is still to run**: no seed predicts the sample before every training of the gate has ended. It also refuses unless both cycles are this seed's finished runs of the two pinned configurations, the second started from the first's final state, and the state file is the end of this seed's second cycle. (After a stop for good a seed without two finished cycles gets a record in the place of predictions, section 10.)
- **Predictions that are not finite** end the command with an error: a stop for good. The record is kept and the seed is not predicted again.
- The readings of the predictions are compared with the sample's labels by the evaluation of section 6 and by nothing else.

## 6. Evaluations (processors only)

    PY evaluate --what dev --runs runs --data data --config-sha SHA --workers N
    PY evaluate --what sample --runs runs_gate --data data_gate --config-sha SHA --workers N

- Each prints a line for each member it finishes, then the status of the three seeds, `{"5": "finished", "6": "finished", "7": "finished"}`, and writes `evaluation_seeds_5_6_7.json` beside the runs it read. The file holds, under `"inputs"`, the SHA-256 of every prediction file, of the manifest and of the ledger as the evaluation read them, and the linear solver.
- Each first runs the checks of `check-labels` on its data folder and refuses if they fail. Each ends with an error, and writes nothing, if a file it read changed while it ran or if a seed with a finished record has no readable predictions.
- The evaluation of the development's members refuses while any cycle of any seed is still to run.
- The evaluation of the sample refuses unless every seed has predictions on the sample or a record that it has none (section 10), and refuses prediction files whose SHA-256 are not those of the predictions' record.
- Each evaluation is a process of its own that does not load torch; its pool of worker processes is forked from it. No command of this runbook trains and evaluates in one process.
- The evaluations do not resume. If a session ends inside one, the next session starts it again.

## 7. Verdict (seconds)

    PY verdict --runs runs --data data --data-gate data_gate --runs-gate runs_gate --out records --config-sha SHA --final

- It prints the verdict's text and writes `records/verdict.json` and `records/verdict.txt`. It refuses, with an error, an evaluation whose inputs are not those on record: prediction files other than the ones the predictions' records name, another manifest or ledger, members that are not the manifest's, an evaluation of the sample without the exact value. With `--final` it ends with an error if the verdict is INCOMPLETE, which it is while a training, a prediction, the evaluation of the sample or the evaluation of the development's members is missing.
- Without `--final` the command may be run at any time: it reads the files as they are and changes nothing but its two output files. Before the evaluation of the sample exists it shows the state of the runs and no number of the sample.

## 8. What is returned

The queue copies these files to the task's folder in the shared store, during the steps and at their end. The operator fetches the small ones and puts them into `records/G-F2.1/` of the repository with the verdict document:
- `records/config.json`, `records/verdict.json`, `records/verdict.txt`, `host_check/smoke.json`;
- the logs of every step, the marks, the queue's own record of each session (the machine, the library versions, the times, the state of every step) and the task file;
- of each run and of each seed's predictions on the sample: `history.json`, `progress.json`, `snapshots.json`, `condense.json`, `attempts.log`;
- the two evaluation files;
- of each data folder: `manifest.json`, `generate_log.json`, `labels/ledger.json`, `labels/summary.json`, and `data_gate/sample.json`.

The state files, the prediction files and the archives of the three data folders stay in the shared store: they are too large for the repository. Their SHA-256 are in the records: of the two state files of a seed and of its prediction files on the sample in the predictions' `history.json`; of the prediction files of the development's members in the evaluation that read them (no other record holds these); of every export and label in the manifests and ledgers.

The verdict and the evaluation files hold `Infinity` and `NaN` where a value is infinite or not a number. Python reads them; a strict JSON reader does not.

A run's record lists a resume only if a checkpoint was written after it, and `attempts.log` is complete only as far as it was copied out before a session ended. The queue's own record of the sessions is the complete account of starts and stops.

No file of the returned records names the shared store, an account or a person.

## 9. After the run

- The operator computes the verdict's statistics again from the rows of the sample's evaluation file with `probes/f21_recompute/recompute.py`, which shares no code with `f21/gate.py`, and compares them with `records/verdict.json`.
- The verdict document `docs/G-F2.1_verdict.md` gives the verdict, the reported values, the commit of the stamp with its day and the seed, the sessions with their GPUs, every stop and resume, and every difference from this runbook.

## 10. After a training or predictions stopped for good

The verdict is then FAIL (pre-specification, "Stop conditions"). After the operator's report and the owner's answer, a closing task is written, with the task's name and store, and run. Its steps, in this order:

1. The same `train` command for every cycle that was under way when the stop came (trainings at the same time), each as a step of its own, until it is finished. No cycle that had not been started is started: the command refuses it. If one of these cycles stops for good in its turn, its step ends with an error each time it is run: the stop is reported like the first, and a new closing task is written without that cycle.
2. `PY predict ...` for each of the three seeds. A seed with two finished cycles is predicted as in section 5. A seed without them gets a `history.json` in `runs_gate/label_free_sS/` whose status begins with `no predictions:` and names the reason, and the command ends with the exit code 0.
3. The two `evaluate` commands of section 6. They evaluate the seeds that have predictions.
4. `PY verdict ... --final`. It prints FAIL with the list of the seeds that failed and, as reported values, what the finished seeds gave. With `--final` it ends with an error as long as one of these steps is missing.

If no seed has finished both cycles, nothing is predicted on the sample, its evaluation has nothing to read and may be left out, and the verdict's text holds no number of the sample.

## 11. A checkpoint or a state file that cannot be read

A `train` or `predict` command that ends with an error while it reads a checkpoint or a state file is a stop. After the operator's report and the owner's answer, the helper renames that cycle's folder in the store, `runs/<preset>/label_free_s<seed>`, to `runs/<preset>/unreadable_s<seed>` (and, if it is a first cycle whose second cycle exists, that folder likewise), on the operator's written request. The cycle then counts as not started, and its `train` command starts it from its beginning with the same seed. The renamed folder is returned with the records, and the restart is reported.

After a training or predictions stopped for good (section 10) no cycle is started again in this way: a cycle whose folder was moved aside then counts as not started, its `train` command refuses it, it is left out of the closing task, and its seed gets the record that it has no predictions on the sample. That record gives as its reason that the cycle was not started; the verdict document says that it stands for a state that could not be read.
