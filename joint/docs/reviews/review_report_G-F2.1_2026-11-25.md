# Independent pre-stamp reading of gate G-F2.1: reports as delivered

Reports of two independent readers to the author, 25 November 2026, one for each round. Each reader was a separate agent that wrote none of the files it read and had no part in the development. The second reader had no part in the first round either and ran on another model than the author and the first reader. Each worked on a copy of the working tree in a folder of its own, with scripts of its own, and was barred from drawing any member with the gate's configuration or with a day from 25 November 2026 on as a seed.

Read: the gate's new code (`f21/`), `tests/test_f21.py`, the draft of `docs/PRESPEC_G-F2.1.md`, `RUNBOOK_F21.md`, `probes/f21_recompute/recompute.py`, the development's code where the gate calls it, the development note and the records that the pre-specification cites, and, in round 2, the working tools outside the repository that write and run the host's task (the task generator, the queue's notebook and the session simulation) with the measurements made before the stamp.

Notes of the author for this file:
- Only this header, the two sections "What the author did after round ..." and the section "The states that were read" are the author's. Each reader returned its report as one message, which is given here as the author saved it on arrival, with one change: where the second report quotes a name that must not appear in the repository's prose, in order to say that it does not occur, the name is replaced by `<a name that the brief lists as not to appear>`.
- The first reader could not be asked for a second round, because the author had kept no means to address it. With the owner's agreement the second round was given to a new reader, which received the first report, the author's notes on it and six questions on the repaired state.
- In the reports, `tree` is the state that round 1 read and `tree2` the state that round 2 read. Neither state was pushed. Line numbers, file hashes and configuration hashes in the reports are those of the states read; `docs/G-F2.1_code.sha256` and the pre-specification have the stamped ones. Folders named `scratch`, `round2` or `measurements` held the readers' working files and the material given to them; what the pre-specification cites of it is in `records/G-F2.1/before_stamp/`.
- "The owner" is the owner of the repository, who decides what is run; "the author" wrote the files that were read; "the helper" starts the sessions of the host.

---

# Round 1 (25 November 2026, delivered at about 13:15 GMT)

# Independent reading of gate G-F2.1 before its stamp: round 1

25 November 2026. Reader: an agent that wrote none of the code or text under review and had no earlier context.

**What was read.** `joint/docs/PRESPEC_G-F2.1.md`, `joint/RUNBOOK_F21.md`, the gate's code in `joint/f21/`, `joint/tests/test_f21.py`, `joint/probes/f21_recompute/recompute.py`, the development code that the gate calls in `joint/f2/` and, where the gate reaches it, `joint/c2/`, `joint/c22/`, `joint/f1/`, `joint/fejoint/` and `src/fejepa/`; `joint/docs/F2_development_note.md`, `joint/probes/f2_stage2/PRESPEC.md`, `joint/probes/f2_under/PRESPEC.md`, `joint/records/f2_dev/`; for comparison `joint/docs/PRESPEC_G-C2.2.md`, `joint/docs/PRESPEC_G-C2.3.md`, `joint/RUNBOOK_C23.md`, `joint/c23/` and `joint/README.md`.

**The state read** (first 16 digits of each SHA-256; line numbers in this report are those of this state):

| File | SHA-256 |
|---|---|
| `joint/docs/PRESPEC_G-F2.1.md` | `947578a2e90f744a` |
| `joint/RUNBOOK_F21.md` | `5b4caf1a8f212b3e` |
| `joint/f21/__main__.py` | `0a0217f8680850cb` |
| `joint/f21/config.py` | `363f6684eea93dfd` |
| `joint/f21/gate.py` | `77e3843d3870c5b0` |
| `joint/f21/smoke.py` | `ad15233e2bba616b` |
| `joint/tests/test_f21.py` | `0af08d248100ecb7` |
| `joint/probes/f21_recompute/recompute.py` | `a1b83edac91e37f2` |
| `joint/f2/train.py` | `00659fec79f82491` |
| `joint/f2/evaluate.py` | `c0daf2fa645d3b73` |
| `joint/f2/data.py` | `608de8ddd1c02658` |
| `joint/f2/devconfig.py` | `8e8b338994dda9c9` |
| `joint/docs/F2_development_note.md` | `b3724d0087f527f4` |
| `joint/records/f2_dev/README.md` | `4d901c19e689244a` |

The gate configuration of this state has the canonical SHA-256 `02244683db02ad8f8190958353f99165823ec644e26974403a9b1c588d7e2836`.

**How to read this report**
- "Executed" means that I ran something and give what it printed. "Read" means that I only read the code or the text.
- My scripts and their outputs are not part of the repository. Where an output held a path of the review machine it is shortened to `<folder>`.
- **Seeds.** No function or command that draws members was given a date from 25 November 2026 on. Every draw that my experiments made is one that the host check's reduced configuration makes: a sample of two with the seed 20260102, and the reduced configuration's own members, which come from the development's seeds 20261120, 20261121 and 20261124. The rule function `f21.config.check_sample_seed`, which draws nothing, was called with later dates to see what it accepts (finding 5). With the gate's own configuration I only built dictionaries and ran `write-config`.
- **Stamp file.** None was written in the tree under review. Two scratch copies of the tree were given a temporary `docs/G-F2.1_code.sha256`, deleted again at the end; in one of them `f21/config.py` was made to return the host check's reduced configuration, so that the command line itself could be run on the smaller mesh with a date of the past.
- **Machine.** Two processors, shared with another job, no GPU; Python 3.13.18, numpy 2.5.3, scipy 1.18.1, torch 2.12.1 (the host of the gate: 3.13.16, 2.4.6, 1.16.3, 2.14.1). One epoch of the host check's stand-in training did not end within two minutes here, so no stand-in training was run to its end through the command line; the paths of `f2/train.py` that this report describes were walked with a still smaller stand-in (finding 3).
- The copy of the tree that I was given already held 31 bytecode files in seven `__pycache__` folders, written before my first command (finding 11d).

**Result in short.** One finding blocks the stamp in my reading (1): three data files that define the reference model and the training energy are outside everything the stamp checks. Eleven findings should be repaired before the stamp (2 to 12); most of them are places where the pre-specification holds only as long as the queue and the operator do the right thing, where the earlier gates had the code refuse. Six findings are minor (13 to 18). I found no error in the verdict's arithmetic, none in the chain of hashes from the trainings to the predictions, and no command of `f21/` that draws, trains, predicts or evaluates without the stamp. The numbers that the texts quote agree with the records, with one rounding slip and two version numbers that have no record. Of the placeholders, the one on the timing hides a decision (finding 12a), and the records of the host check and of the simulation must state the seeds they drew with (finding 5f).

---

## 1. Findings

### 1. BLOCKS THE STAMP. The material curves of the reference model are read from three data files that no hash of the gate covers

**Where.** `joint/f2/family.py`, lines 33 and 85 (`np.loadtxt(DATA / BOLT["curve"], ...)`), and lines 66 to 74 through `joint/f1/materials.py`, line 22 (`np.loadtxt(DATA / spec["curve"], ...)`). The files are `joint/f1/data/material_plate13_eng.csv`, `joint/f1/data/material_chs_eng.csv` and `joint/f1/data/material_bolt_eng.csv`. The list of stamped files is `CODE` in `joint/f21/__main__.py`, lines 54 to 63. Text: `joint/docs/PRESPEC_G-F2.1.md`, lines 110 and 114.

**What is wrong.** Every export of a member (training members, the 31 members of the development, the sample) takes the plate's and the tube's hardening curve and the bolt's law from these three files at the moment of the export. They then sit in the export and decide the training energy, the labels and the evaluation. `CODE` lists the 44 Python files that the gate imports, and its comment says so: "every file of the packages that the gate imports". The three data files are not in it, they are not pinned in `f21/config.py` as the six repository files are, and the "data" hashes of the pre-specification are hashes of configuration text: "the hash of the family and data sections" names the plate law in words ("gate G-F1's 12.7 mm plate law (f1/materials.py), stresses scaled by fy / 397") and not by content. The sentence of line 110, "The data they train on are pinned too", is therefore true of the seeds and ranges and not of the material laws. `tests/test_f21.py`, lines 54 to 87, compares `CODE` with import statements only, so it cannot see a file that is read.

G-F1 had these files in its stamp: `joint/docs/G-F1_code.sha256` lists all three, and their hashes there are those of the files today (`436579d9...`, `bd2e5912...`, `5b7f1267...`).

**Executed.** In a scratch copy with a temporary stamp file I multiplied the stresses of the bolt curve by 0.9 and of the plate curve by 1.1 and asked the gate whether the code is the stamped code:

```
== before the edit
gate config sha 02244683db02ad8f | first pin ok True | data pin ok True | extra pin ok True
bolt points (first, last): (0.0037632..., 817.0) (0.05609, 940.1) n 14
plate hardening sigma[:3]: [400.0, 412.676, 424.279]
== after the edit
gate config sha 02244683db02ad8f | first pin ok True | data pin ok True | extra pin ok True
bolt points (first, last): (0.0037632..., 817.0) (0.05609, 846.09) n 12
plate hardening sigma[:3]: [400.0, 421.583, 442.044]
$ python -I joint/f21/__main__.py write-config --out /dev/null --config-sha <the hash>
stamped code: yes                                   (exit code 0)
```

The configuration hash, the four pins and the stamp check are unchanged, and every member exported from that tree would have another bolt and another plate.

**Why it matters.** The stamp exists so that nothing that decides the outcome can differ from the committed state without a command refusing. Here the reference model itself can. On the host the only guard is the queue's comparison of the code archive with a hash in the task file, and both are outside the stamp. The question the brief put ("could an edit change what is trained without changing a hash that is checked") has the answer yes, by these three files.

**What I would change.** Add the three files to the stamped list (it then holds 47 files and is a list of files, not of imports), or pin their SHA-256 in `f21/config.py` and check them where `verify_repository` checks the repository files. Add a test that names them, since the import walk cannot find them. Correct line 110 and line 114 of the pre-specification and step 0a of the runbook to the new count.

---

### 2. SHOULD BE FIXED. The sample can be evaluated, and the verdict read, while seeds are still to be trained

**Where.** `joint/f21/gate.py`, lines 222 to 242; `joint/f2/evaluate.py`, lines 230 to 234; `joint/f21/__main__.py`, lines 263 to 265. `joint/RUNBOOK_F21.md`, lines 94 and 116. `joint/docs/PRESPEC_G-F2.1.md`, lines 195, 197 and 236.

**What is wrong.** `evaluate --what sample` evaluates the seeds that have predictions, lists the others as `missing`, writes the evaluation file and ends with the exit code 0. `verdict` without `--final` then prints the median, the 90th percentile and the largest error of every seed that was evaluated; the runbook says of it: "The command may be run at any earlier time". The runbook's section 5 reads "For each seed S, after its second cycle", which allows the predictions of seed 5 on the sample to exist before the trainings of seeds 6 and 7 have started, about 14 hours apart each if the runs are made one after another. The pre-specification forbids decisions on the snapshots of the development's members (line 236); it has no sentence about the sample before all three runs have ended. It does let the owner end the gate while it is INCOMPLETE (line 195).

No command is needed either: the predictions' `condense.json` holds the end rotation, the moment and the rotation of the measuring ring of every pair, the sample's `labels/summary.json` holds the reference curves, both are among the small files that the queue copies out during the steps (runbook, section 8), and the development's `quicklook` (`joint/f2/evaluate.py`, lines 288 to 314) shows how to compare them without a solve.

**Executed** (reduced configuration, no seed predicted yet):

```
$ python -I joint/f21/__main__.py evaluate --what sample --runs runs_gate --data data_gate --config-sha <hash> --workers 2
gate_0000 evaluated, 1 of 2, 14 s
gate_0001 evaluated, 2 of 2, 14 s
{"5": "missing", "6": "missing", "7": "missing"}          (exit code 0; evaluation_seeds_5_6_7.json written)
```

**Why it matters.** The one thing a gate has to exclude is a decision taken with results on the sample in view. As it stands, the errors of the first seed on the sample can be on the operator's screen two days before the last training starts, and ending the gate then gives "not completed" in the place of a FAIL. I do not say that anyone intends this; the pre-specification should not leave it open. G-C2.3 did not: there "an evaluation of an arm with a run that has no predictions" was a stop of the queue (`joint/RUNBOOK_C23.md`, lines 16 and 171).

**What I would change.** (a) `evaluate --what sample` refuses, with an error and without writing, unless every seed has predictions or a recorded final stop. (b) The runbook says that no seed predicts the sample before every training has ended or stopped for good, and drops the invitation to run `verdict` early, or `verdict` prints no statistic of the sample while a seed is missing. (c) The pre-specification says so in one sentence under "Procedure", and says that the readings of the predictions on the sample are not compared with its labels by any other means before that point. (d) If the owner ends the gate while it is INCOMPLETE, the report states whether predictions on the sample existed at that time.

---

### 3. SHOULD BE FIXED. A cycle is recorded as finished before its end-of-cycle predictions exist, and the gate takes the record at its word

**Where.** `joint/f2/train.py`, lines 763 to 771. `joint/f21/gate.py`, lines 143 to 149 (start of the second cycle), 178 to 191 (predictions on the sample) and 317 to 321 (verdict). `joint/RUNBOOK_F21.md`, line 87. `joint/docs/PRESPEC_G-F2.1.md`, line 173.

**What is wrong.** `f2.train.train` writes `history.json` with `"status": "finished"` and `progress.json` with the state `finished` first, and only then predicts the 31 members of the development. A process that is ended during those predictions leaves a run that every record calls finished and that has no prediction file. The runbook says the opposite order: "A finished cycle ends with the predictions of the 31 members of the development and writes `condense.json` last; its `history.json` then has `"status": "finished"`."

The gate's code asks the record only. The second cycle starts if the first cycle's `history.json` says finished with all steps; `predict` on the sample asks the same of both cycles; `verdict` counts a cycle as finished by its status. None of them asks whether the cycle's predictions were made. The pre-specification makes them part of a finished cycle: a cycle that "has ended on a non-finite value (a non-finite loss, or predictions of the development's members at the end of the cycle that are not finite)" is a FAIL. For a cycle that was cut off in its predictions and not run again, that condition is never looked at, and the verdict can be PASS.

**Executed** (a stand-in smaller than the host check's, through `f2.train.train`: one training member, two epochs; the predictions interrupted, then the command run again):

```
history.json after the kill: status 'finished' steps 2 / 2 | prediction files written: False
progress.json state: finished
f2.evaluate.run_status: missing
run again: finished resumes [1, 2] | predictions written: True | state.pt unchanged
```

The resume itself is sound: run again, the command goes on at the predictions and leaves the state file as it was. The hole is in what counts as finished.

**Why it matters.** The queue skips "a step whose files are complete" (runbook, line 21). Whether a training step that died in its last minutes is run again depends on which file the queue looks at, and the runbook points it to the wrong one. If it is skipped, the evaluation of the development's members lists that seed as `missing`, the verdict leaves it out of `development_members` without a word, and the verdict can still be PASS.

**What I would change.** In `f21/gate.py`: the second cycle, the predictions on the sample and the verdict count a cycle as finished only if `history.json` says so and `condense.json`, which is written last and is small enough to be restored in every session, is there. Correct line 87 of the runbook, and name the file that marks each step as complete (finding 11f).

---

### 4. SHOULD BE FIXED. A preload that is not on target does not stop anything for the training members

**Where.** `joint/f21/gate.py`, lines 76 to 80 and 71 to 75; `joint/f2/data.py`, lines 185 to 189, 211 and 339; `joint/f2/__main__.py`, lines 166 to 170; `joint/RUNBOOK_F21.md`, lines 58 and 60.

**What is wrong.** Every export sets the bolts' preload by a fixed point of solves. If it does not converge or does not reach the target, `f2.data.generate` prints `PRELOAD NOT ON TARGET` for the member, writes `"preload_ok": false` to the manifest and ends normally.
- For the 32 further training members (`generate --what thin`) nothing reads that flag afterwards: the command ends with 0, there is no check command for that folder, and `f2.train` does not look at the flag. The development's own command had the check, with the reason beside it: "training members only: nothing else checks them" (`joint/f2/__main__.py`, line 166). The gate's command dropped it.
- For the development's folder `check-labels` does fail on the flag, but the flag is `on_target` alone (`f2/data.py`, line 211); the development's check asked for `converged and on_target`. A member whose log entry is missing counts as on target (`.get("on_target", True)`).
- The runbook leaves it to the operator's eye ("each ending `preload ok`", 191 lines), and the queue goes on to the trainings unattended.
- The pre-specification has no stop condition for it: line 210 speaks of labels.

**Executed.** With the export replaced by a stand-in that reports a failed preload (no solve), `gate.generate(G, "thin", ...)` as the command calls it:

```
trainx_0000 0.0 s PRELOAD NOT ON TARGET
trainx_0001 0.0 s PRELOAD NOT ON TARGET
gate.generate returned manifest.json without an error
manifest preload_ok: [('trainx_0000', False), ('trainx_0001', False)]
f2.train.check_manifest accepts the folder: True | members 2
```

**Why it matters.** A training member with a wrong preload is trained on with a preload that its features do not state. The gate would run to its verdict on a training set that is not the one the pre-specification names, and only a reader of the generation log would know.

**What I would change.** `f21 generate` ends with an error, for all three folders, if the generation log holds a member whose preload did not converge or is not on target (the test of `f2/__main__.py`, lines 167 to 170). One stop condition in the pre-specification: a preload of any member that does not converge or is not on target stops the gate before any training.

---

### 5. SHOULD BE FIXED. The sample's seed: found by hand, open towards the future, fixed only within a folder, and undefined when it goes wrong

**Where.** `joint/docs/PRESPEC_G-F2.1.md`, lines 3, 135, 137 and 216; `joint/RUNBOOK_F21.md`, line 38; `joint/f21/config.py`, lines 118 to 131; `joint/f21/gate.py`, lines 83 to 99; `joint/f21/smoke.py`, lines 62 to 64.

**What is wrong.** The pre-specification says plainly that the code does not check that the seed is the date of the stamp. I take that as given and list what is left open around it.

(a) *By hand.* The runbook's command, `git log -1 --format=%cI <commit>`, prints the committer's local time with its offset. The seed is the date in UTC. A commit at 00:30 with the offset +01:00 on the 26th carries the 25th; the operator has to see that. A command that prints the seed leaves nothing to convert: `TZ=UTC git log -1 --date=format-local:%Y%m%d --format=%cd <commit>`.

(b) *Open towards the future.* The rule function accepts every calendar date from 25 November 2026 on that is not in the used list. Executed (the rule only, nothing drawn):

```
gate configuration, check_sample_seed( 20261126 ) -> 20261126 (accepted)
gate configuration, check_sample_seed( 20270615 ) -> 20270615 (accepted)
gate configuration, check_sample_seed( 99991231 ) -> 99991231 (accepted)
```

A date later than the day on which the command runs can never be the date of a commit that already exists. The command could refuse it at no cost.

(c) *Fixed within a folder only.* "From then on that command refuses any other seed" holds for the folder that holds `sample.json` (`gate.py`, lines 88 to 98). Given another folder, the command draws another sample with another date, and every later command accepts that folder. Nothing in the code knows that a sample exists. The protection is the repository's history and the verdict document; the text should say that it is the only one.

(d) *Which commit.* "The commit that adds this document and `docs/G-F2.1_code.sha256`" (line 3) is one commit only if both files are new in it and if it reaches the repository unchanged. Line 216 foresees a second stamp after a failed host check; a merge that squashes makes a new commit with a new committer date. The text does not say which date then counts.

(e) *A wrong seed.* If the seed given turns out not to be the date of the stamp, by (a) or (d), the text says only that the verdict document "states both". Whether the gate then stands, is void, or is reported as changed after the stamp is not said, and by then the sample is drawn.

(f) *The reduced configuration accepts the dates that the stamp can fall on.* `smoke.reduced()` sets `not_before` to 20260101 and keeps the rest of the used list, so `check_sample_seed(reduced, 20261126)` returns 20261126 (executed, the rule only). `f2.family.sample` draws its members one after another, so a sample of two drawn with a date is the first two members of the gate's sample for that date; `tests/test_f21.py`, lines 116 to 118, asserts exactly that property. The host check itself is safe, its seed is the constant 20260102. A call of the functions with the reduced configuration is not, and the paragraph on 20261127 shows that such calls are made. The simulation of the host's task "with the reduced configuration in the place of the gate's" (line 87) goes through the command line with a seed that someone typed; its record is a placeholder, and I could not see which seed it used. If it was a date from 25 November 2026 on, that date is used.

**Why it matters.** The sample is the gate. Every other determinant is hashed; this one is typed, once, after a conversion by hand, and the mistake of 25 November shows that the mechanism is easy to trip.

**What I would change.** (1) Give the operator the command of (a). (2) Refuse a date later than the current UTC date. (3) Give the reduced configuration an upper limit as well as a lower one, for instance dates of January 2026 only, so that neither a test nor a simulation can draw a date that the stamp could fall on; state the seed in the simulation's record. (4) Define the commit: the last commit that changes `docs/G-F2.1_code.sha256` before the first member of the sample is exported, read on the branch from which the code archive is made; and say what a wrong seed means for the verdict. (5) Say in "How the code holds to it" that the seed is fixed within a folder and that a second folder is refused by nothing but the record. An option to put to the owner, who agreed to "the date of the stamp as its seed": write that date into the hashed configuration when the stamp is made, as G-C2.2 and G-C2.3 carried their seeds, and stamp again if the commit lands on another UTC day. The code would then refuse every other seed and (a) to (e) would not arise.

---

### 6. SHOULD BE FIXED. The evaluation does not record what it was computed from, and the verdict cannot tell a stale evaluation

**Where.** `joint/f21/gate.py`, lines 235 to 242 and 324 to 340; `joint/f2/evaluate.py`, lines 223 to 226. Text: `joint/docs/PRESPEC_G-F2.1.md`, line 153.

**What is wrong.** `evaluate --what sample` compares the prediction files with the hashes in the predictions' records before it starts. That is the only moment at which the chain is closed. The evaluation file itself does not hold the hashes of the prediction files it read, nor those of the manifest and the ledger. The verdict reads the evaluation file, writes down the hashes that the predictions' records, the manifest and the ledger have at that later time, and compares nothing. G-C2.3 did: its rows file held its inputs, its evaluation checked at its end that nothing had changed meanwhile, and its verdict "reads the label-free rows as they are, after checking that what they were computed from has not changed: the manifest, the ledger entries of the evaluated members, and the prediction files of the runs" (`joint/docs/PRESPEC_G-C2.3.md`, line 216; `joint/c23/evaluate.py`, lines 171 to 185, 267 and 315).

**Executed** (made-up files as in `tests/test_f21.py`; after the evaluation file was written, the predictions' record of seed 5 was given another hash, then the manifest another plate thickness):

```
[prediction_record_changed_after_evaluation] -> PASS | recorded prediction hash now {'preds.npz': 'ffff...ffff'}
[manifest_changed_after_evaluation] -> PASS | thin members 2
```

**Why it matters.** The gate runs over several sessions in folders that are rebuilt from a store each time. A prediction step that is run again after the evaluation (its large files not restored, for instance) writes new files and a new record; the verdict then names hashes of files that the evaluation never read, and nothing shows it. On a GPU a second prediction need not be equal to the first to the last bit. The numbers would hardly move; the record would be wrong.

**What I would change.** `gate.evaluate` writes, with the evaluation, the SHA-256 of each seed's four prediction files as it read them, of `manifest.json` and of `labels/ledger.json`; `verdict` refuses an evaluation whose inputs are not those now recorded. In the same place, `predict_sample` should compare the seed in the state file with the seed asked for (finding 14d).

---

### 7. SHOULD BE FIXED. The judged quantity's first-order step has never been compared with the exact value on the family's mesh, and the text does not define it fully

**Where.** `joint/docs/PRESPEC_G-F2.1.md`, lines 36, 38, 161 and 163; `joint/f2/evaluate.py`, lines 80 to 88 and 108 to 133; `joint/records/f2_dev/README.md`, line 43.

**What is wrong.**
(a) The judged error is exact "to first order" in the difference between the predicted rotation of the measuring ring and the reference's at the predicted end rotation. The exact value is computed in the gate and reported. No record of the development holds it: all thirteen evaluation files of `joint/records/f2_dev` carry `"exact_ThetaD": false`, and the README says of the earlier ones that "none of them has it". So when the stamp is made nobody has measured how far the judged value is from the quantity that the hypothesis names, and `ExportedProblem.solve_at_ThetaD` (a secant search with up to 12 exact solves a pair) has never run on predictions of a trained network on the family's mesh. Its first real use would be inside the sample's evaluation, a step of two to three hours that does not resume.

(b) "The monotone cubic through the member's labelled path" does not say which. The code uses `scipy.interpolate.PchipInterpolator` with `extrapolate=True`. Several monotone cubics exist and they differ in their slopes. Beyond the last labelled point the slope is that of the last piece continued; the text does not mention that case, and it occurs with the gate's recipe (below).

**Executed, from the records alone.** I computed `curveD_err` again for every pair of the gate's recipe and of the first cycle, in both readings, from the row's own readings (`M`, `ThetaD`, `M_curve`, `ThetaD_curve`) and the labelled path in `data/family_mesh/labels_summary.json`, with scipy's interpolator:

```
arm 2 (the gate's recipe), condensed: 217 pairs; largest |recomputed - recorded curveD_err| = 0.00e+00
    |ThetaD - ThetaD'| / ThetaD: median 0.72%  p90 1.97%  max 6.6%
    next (second-order) term of M*, from the cubic, relative: median 0.0009%  p90 0.0132%  max 0.108%
arm 2, raw: 217 pairs; largest difference 0.00e+00 ... max 0.096%
first cycle, condensed: 217 pairs; largest difference 0.00e+00 ... max 0.173%
pairs whose slope is read beyond the last labelled point: arm 2 condensed 1 of 217, arm 2 raw 7 of 217 (furthest 1.87% beyond)
```

Two things follow. A third party can compute the judged quantity again from the returned records, once the interpolator is named: the definition is sufficient. And for a run like the development's, the term that the first-order step leaves out is of the order of 0.1 percentage points at most. That is my estimate from an eight-point cubic, not a measurement; for a run that has not trained it says nothing.

**What I would change.** Before the stamp, run the development's evaluation with the exact value on the 31 members for the gate's recipe (seed 0; its prediction files exist), and put under "What was seen before the stamp" how far the two values lie apart and how many solves the search took; or say in that section that the difference has never been measured. Name the interpolator and its continuation beyond the last level in "The judged quantity". It would also help a reader to be told that the judged error of a pair depends on the predicted field through two numbers only, its end rotation and its rotation of the measuring ring, both of which are in the evaluation's rows.

---

### 8. SHOULD BE FIXED. Outcomes that the stop conditions leave undefined

**Where.** `joint/docs/PRESPEC_G-F2.1.md`, lines 191 to 197 and 208 to 216; the code as cited.

Each of these can happen after the stamp, and the text then has no answer.

(a) *A member of the sample that cannot be exported or labelled at all.* Line 210 covers a label "that does not converge or fails its checks". An exception in the export, in the preload solve or in a level's solve is neither: the command ends with a traceback every time it is run again, and the ledger never gets the member.

(b) *An evaluation of the sample that cannot end.* In `joint/f2/evaluate.py` two steps of a member lie outside the handlers of lines 171 to 175: the assertion that the rotation of the measuring ring rises along the labelled path (line 87) and the evaluation of the labelled states (lines 164 to 167). If either fails for one of the 64 members, the whole evaluation ends with an error, after the trainings and the predictions. `check-labels` tests neither. The gate would hold predictions on the sample and no evaluation. Both can be tested when the labels are checked, before any training, and would then fall under line 210.

(c) *A preload of a training member that is not on target* (finding 4).

(d) *The linear solver.* Line 220 says that the solver of the labels and of the evaluation is PARDISO. `joint/fejoint/linsolve.py`, lines 30 to 37, falls back to SuperLU without a word if the library does not load; that happened in two earlier gates (`joint/docs/G-C1.3_verdict.md`, line 30; `joint/docs/G-C2.1_verdict.md`, line 35). The ledger records the solver of each label; `check-labels` does not look at it, and the evaluation does not record its solver. The queue compares four library versions between sessions, and the solver library is not among them. Is a label solved by SuperLU a label of this gate?

(e) *A seed that is not the date of the stamp* (finding 5e).

(f) *A gate that ends before any prediction on the sample is evaluated*: a label that stops it, a first training that stops on a non-finite value, the owner ending it. By line 197 the sample is spent "once a prediction on it has been evaluated". Its members have then been drawn, solved and their reference curves returned, and it is not spent. May a later gate judge the same 64 members? I would say the sample is spent once it has been exported.

(g) *Trainings at the same time, one stops for good.* Line 211: "runs that are under way at the same time may finish". If the session's limit pauses them first, they are not finished, and the runbook says that final stops "are not continued" (line 27). Are the paused runs resumed? And since "no training that has not been started is started afterwards", a non-finite stop in a first cycle leaves the other seeds without a second cycle, so no number on the sample will exist; the interpretation of line 193 ("the values of the seeds that finished are given") should say that this is the case it describes.

(h) *After a final stop.* The queue stops and runs no later step. Nothing says which commands are then run, once the owner has answered, so that the predictions of the finished seeds, their evaluation and the FAIL are on record. `joint/RUNBOOK_C23.md`, line 125, spelled this out for its case.

(i) *The state file of a finished first cycle is lost or cannot be read.* The second cycle starts from it and the chain of hashes reads it again at the prediction. Line 213 speaks of a checkpoint; a finished run returns at once when its command is run again and does not train.

(j) *A PASS with pairs whose error is infinite.* Up to 44 of the 448 pairs can be infinite without the 90th percentile becoming infinite. The fixed wording should say that such pairs are named with their number and their members.

**What I would change.** One line each in "Stop conditions" or "Interpretation". For (b), the two tests in `check-labels`.

---

### 9. SHOULD BE FIXED. The stop on a failed label check is the queue's, not the code's

**Where.** `joint/docs/PRESPEC_G-F2.1.md`, line 210; `joint/f21/gate.py`, lines 222 to 242 and 293 to 386; `joint/f2/evaluate.py`, line 217.

**What is wrong.** "A label that does not converge or fails its checks ...: the gate stops before any prediction is evaluated and stays INCOMPLETE." In the code only `check-labels` knows whether the labels pass, and what stops is the queue that reads its exit code. `evaluate` compares the label files with the ledger's hashes and does not ask whether the levels converged or the limits hold; `verdict` does not look at labels. A queue that goes on after a failed check, by a fault of the task file or by a step run by hand, gets an evaluation and a verdict of PASS or FAIL where the text says INCOMPLETE.

**What I would change.** `evaluate` (both kinds) runs the label check first and refuses if it fails; it is a matter of seconds. Then the stop condition holds whatever the queue does.

---

### 10. SHOULD BE FIXED. The host check and the tests do not exercise some of what they name, and the host check has not run where the gate will

**Where.** `joint/f21/smoke.py`, lines 10 to 11, 72 to 77, 95 and 103 to 138; `joint/tests/test_f21.py`; `joint/f21/__main__.py`, lines 207 to 216 and 219 to 278; `joint/docs/PRESPEC_G-F2.1.md`, lines 85 and 228.

**What is wrong.**
(a) *The refusal of a second seed is not tested.* The check `second_seed_refused` calls the export with the seed 20260103 once the sample is written. In the reduced configuration that seed is still in the used list, so it is refused by the rule on used seeds before the code reaches the test "the sample in this folder was drawn with another seed". `_refused` counts every `RuntimeError` and `ValueError` alike. Executed through the command line of the reduced copy:

```
$ ... generate --what sample --data data_gate --sample-seed 20260103 --config-sha <hash>
ValueError: 20260103 drew members of the family before the stamp
```

The branch itself is correct. Reached with a seed that passes the rule (the used list shortened by hand, a hand-made `sample.json`):

```
RuntimeError | the sample in <folder> was drawn with seed 20260102; its seed is fixed
files but no sample.json: RuntimeError | <folder> holds files but no sample.json; give a new folder
```

No test of `tests/test_f21.py` reaches it either. The check that the pre-specification leans on most ("from then on that command refuses any other seed") is the one that is not exercised.

(b) *The command line's branches are not tested.* `tests/test_f21.py` calls `main` for the two refusals, for `write-config` and for `smoke`. The branches of `_run` for `generate`, `label`, `check-labels`, `train`, `predict`, `evaluate` and `verdict`, their exit codes, and `chain` and `together` are run by no test, because every one of them needs a stamp file. I ran most of them in the reduced copy and found them as the runbook says (section 2 below). The simulation of the host's task may cover them; its record is a placeholder.

(c) *The host check's training stage is not the command's process.* The `train` command sets `FEJOINT_SOLVER=legacy` so that the sparse solver's libraries stay out of the process that holds torch (`joint/f2/__main__.py`, lines 96 to 99, gives the reason: two OpenMP runtimes in one process). The host check calls `gate.train` directly and does not set it, so its training stage loads both. It tests a combination of libraries that the gate's trainings never have, and not the one they have.

(d) *Not on the gate's host before the stamp.* Line 85: the host check "has not been run on the gate's host before the stamp; it is the first step there after the stamp". On that host nothing of `f21/` has run: not the GPU path, not three trainings at once through `f21`'s `together`, not the pools with 24 workers under that Python and torch. The host check has already found one hang on a processor. If it fails on the host after the stamp, the gate must be stamped again (line 216), with the questions of finding 5d. The timing is to be made on that host before the stamp anyway, and the host check needs no stamp: it can run in the same session.

**What I would change.** (a) Remove both past dates from the reduced used list, call the second export with a date that passes the rule, and let `_refused` name the error it expects. (b) Tests that give `main` a temporary stamp file (as `test_stamp_check` does) and the reduced configuration, for each branch and exit code, with `chain` and `together` on cheap commands. (c) Run the host check's stages through the commands, or set the variable as the command does. (d) Run the host check on the gate's host before the stamp and quote its record.

---

### 11. SHOULD BE FIXED. The runbook: two false sentences, a first command that fails in an empty folder, and steps that only the queue's author can fill in

**Where.** `joint/RUNBOOK_F21.md`, by line.

(a) Line 72: "No command of sections 4 and 5 is given `data_gate`." The command of section 5 is `PY predict --seed S --runs runs --data-gate data_gate ...` (line 96). The sentence holds for section 4.

(b) Line 87: the order of `history.json` and the predictions (finding 3).

(c) Line 46: `PY write-config --out records/config.json ...` is the first command in a working folder that "does not outlive a session". The command does not make the folder. Executed in an empty folder:

```
FileNotFoundError: [Errno 2] No such file or directory: 'records/config.json'          (exit code 1)
```

Unless the queue makes `records/` first, the run stops at its first step.

(d) *Bytecode.* "The commands write no bytecode" is true, and they would still read it. `joint/RUNBOOK_C23.md` (lines 57 and 187) had the operator check that the code tree holds no `__pycache__` folder, "because Python would run a cached file in place of a stamped source". That check is gone. The copy I was given held 31 bytecode files.

(e) *Threads.* `joint/f21/smoke.py` says that "the host's queue tells the gate's processor steps" to use one thread for linear algebra. The runbook does not say it. With 24 worker processes and no such setting the labels and the evaluations oversubscribe the processors, and the times of line 30 do not hold.

(f) *What makes a step complete, and what is restored.* "A step whose files are complete is skipped" (line 21) and the store "copies it back at the start of the next session" (line 18) decide which commands run twice and on which files. Neither is defined. For a training the mark matters (finding 3); for the data folders a mixture of restored and new files ends in a traceback of `check-labels` ("label ... differs from the ledger") that the list of host stops (line 28) does not name. An operator who did not write the queue cannot write the task file of step 0d from this text: its format, the mark of each step, the accepted GPUs, the margin by which `H` must be shorter than the session (the limit is tested at the end of an epoch only, and the predictions of 31 members follow the last epoch without a test).

(g) *After a stop.* What is run after a final stop so that the verdict is on record (finding 8h). How a cycle is "started again from its beginning" when its checkpoint cannot be read: which files are moved aside. `joint/RUNBOOK_C23.md`, line 162, said it.

(h) Step 0b: the seed by hand (finding 5a).

(i) Line 60: "each ending `preload ok`". The command's last line is the manifest's path, and a run that resumes prints no member line at all. Under "any output that differs from what a comment states: stop and report" a careful operator stops here. A line `PRELOAD NOT ON TARGET` does not stop the queue (finding 4).

(j) Line 107: an evaluation ends with 0 whatever the status of the seeds. For the sample the final verdict catches it; for the development's members nothing does.

(k) *A step that waits.* The rule "no new line for half an hour: report" is given for the host check only, which has its own limit of 45 minutes a stage that the runbook does not mention. The labels and the evaluations use pools of worker processes that wait for ever if the system kills a worker; `joint/RUNBOOK_C23.md`, lines 114 and 135, warned of it. Both now print a line a member, so the rule can be the same for them.

(l) Step 0a uses `PY`, which is defined from the working folder of the host; the step is the operator's own, before any session.

(m) Line 127: "of the prediction files in the same record". That holds for the predictions on the sample. The prediction files that each cycle makes of the development's members are hashed in no record.

**What I would change.** Correct (a) and (b); let `write-config` make the folder; restore the bytecode check; state (e), (f), (g) and (k); and add one line to section 2: the ledger's `"solver"` must read `pardiso` for every label, or the pre-specification says what holds if it does not (finding 8d).

---

### 12. SHOULD BE FIXED. Four statements of the pre-specification that are not established, or say less than the records

**Where.** `joint/docs/PRESPEC_G-F2.1.md`, by line.

(a) *The timing.* Line 22 states as a fact: "a timing before the stamp used seeds 90 to 93 for two epochs each", and `joint/f21/config.py`, line 64, lists 90 to 93 under `training_seeds_used_before_stamp`. Lines 76 and 222 are placeholders that allow the timing not to have been made when the document is stamped, and line 222 lets it be made up to the first session. This placeholder hides a decision. If the timing is made after the stamp, line 22 and the name of the key are false, and the timing is then a run of the gate's first-cycle configuration on the gate's host, after the stamp, by the development's command line, which no line of the runbook holds. Make the timing before the stamp, or word line 22 and the key as seeds set aside for a timing and say in the runbook when and by which command it is made.

(b) *Two version numbers without a record.* Line 220 gives "pypardiso 0.4.7, mkl 2026.2.1" for the development's runs. `joint/records/f2_dev/host/sessions.jsonl` records Python, torch, CUDA, numpy and scipy for each session and neither of these two; the label ledger records only that the 31 labels were solved with PARDISO. I found no record in the tree behind the two numbers. Record them, or do not quote them. See also finding 8d.

(c) *A second departure from the plan of 24 November.* The section "Where the recipe comes from" says plainly that arm 2 was adopted against the trial's rule. The same plan ends its rule with "Whatever the outcome, no further change is tried before the gate" (`joint/probes/f2_stage2/PRESPEC.md`, line 72). The trial of 25 November tried one. It was not adopted, so the recipe is untouched; the sentence was still broken, and the section that "says so plainly" should say this too.

(d) *The price of the deviation.* Line 50 puts against the gains "0.2 percentage points more at the two lowest levels". From the two evaluation files of `joint/records/f2_dev/family_mesh/` (my computation; `trial_24_november/outside_the_rule.txt` has the same numbers): in plates thinner than 12.5 mm the median error at the two lowest levels rose from 1.97% to 2.63%; the median over the eleven hand-picked members rose from 1.54% to 1.82%; the median over all pairs rose from 0.99% to 1.07%; 27 of 31 members got worse at the two lowest levels. The table of line 62 shows the third of these and the development note the fourth. Thin plates are where the pre-specification expects the largest errors, so the first belongs in the sentence that weighs the choice.

---

### 13. MINOR. Text against code: smaller differences

(a) Line 161 of the pre-specification: if "the reference code cannot evaluate the predicted field, the error of the pair is infinite". In `joint/f2/evaluate.py` a field that breaks the two assertions of lines 97 and 98 makes all seven pairs of that member infinite for that seed and reading (lines 171 to 175; `joint/f21/gate.py`, lines 259 to 267). A field whose energy the reference code cannot evaluate (lines 135 to 141) keeps its judged value: only the gap and the other reported quantities become not-a-number, which the verdict's statistics then show as infinite. A third case is in the code and not in the text: the first-order reference moment itself not positive (line 116).

(b) Line 173 against `gate.py`, lines 317 to 321: "finished both cycles" (finding 3). Line 173 against lines 363 to 368: the verdict is PASS or FAIL without the evaluation of the development's members, and `--final` does not object.

(c) Line 214: "the record of each run lists its resumes". The list in `history.json` holds a resume only if a checkpoint or the history was written after it, and it comes from the checkpoint each time: three restarts at the last epoch gave `resumes [1, 2]` in my run. `attempts.log` is complete only as far as the queue copied it out before the session ended. The queue's own record of the sessions is the complete one; say so. (`joint/c22/train.py` carries this caveat in its first lines.)

(d) Line 181: "The raw reading, with the same statistics". The verdict gives the median, the 90th percentile, the largest value and the count for the raw reading (`gate.py`, lines 353 to 354), not the levels, the thin plates or the worst members.

(e) Line 185: "seconds an epoch ... the peak memory". The verdict holds the sum of the epochs' seconds, and the peak memory of the last process of a run only (`gate.py`, lines 308 to 312).

(f) The two pinned run configurations hold `"checkpoint_every_epochs": 1` (`joint/f2/devconfig.py`, line 282). `f2/train.py` does not read it: it writes a checkpoint when ten minutes have passed, as the runbook says. A hashed setting that the code ignores; it cannot be changed without changing the pins, so one sentence in the pre-specification.

(g) The statistics of `ThetaD_err` and `gap` in `verdict.json` are those of absolute values under the names of the signed quantities (`gate.py`, lines 249 to 268).

(h) Line 11 and `joint/README.md`, line 30: "three seeds that no run has used". The seeds 5, 6 and 7 trained G-C2.2 and G-C2.3 and the stand-in networks of the tests. Line 3 has the exact wording: no run of the gate's two training configurations.

(i) Line 137: the command "refuses ... a date before 25 November 2026"; it has no upper limit (finding 5b).

### 14. MINOR. What `verdict` and `predict` take on trust

(a) `joint/f21/gate.py`, lines 330 to 335: the members of the evaluation are counted, not compared with the manifest. Executed with a made-up file whose list names one member twice: `[duplicate_members] -> PASS`, the other member never read. A name that is not in the manifest gives `KeyError: 'x_0000'`. The gate's own evaluation cannot write such a file; `recompute.py` does test for a repeated name.

(b) Lines 363 to 368: the evaluation of the development's members is taken as found. Executed: a file of another configuration with one member and one seed is reported under "development's 31 members" (the number is a constant in `joint/f21/__main__.py`, line 126).

(c) If the evaluation holds no exact value, the verdict and its text say nothing about it (executed: `exact per_seed: {}`).

(d) Lines 193 to 195: the state file is tested for its configuration and its step, not for its seed. Executed with made-up records: of thirteen broken chains twelve were refused with the right message; a state file of another seed in this seed's folder, with the same configuration and step, went on to the building of the networks.

(e) `verdict` requires `--data` and does not use it (`gate.py`, line 293).

### 15. MINOR. The stamp's mechanics

(a) `joint/f21/__main__.py`, lines 135 and 204 to 206: `src` of the repository is put in front of the stamped tree on the module path. A package in `<repo>/src` with the name of a stamped one would be imported in its place while `not_stamped` hashes the files of the stamped tree. This needs a `--repo` that holds such a package; the runbook gives none. Putting `src` behind the stamped tree closes it.

(b) Bytecode: finding 11d.

(c) `joint/probes/f21_recompute/recompute.py` is not stamped, and need not be; say in the pre-specification that a change of it after the stamp is reported as one, or give its hash.

(d) `joint/README.md`, lines 98 and 159, names a folder `docs/G-F2.1_stamped_code/` with a copy of the new code and of the development's. The pre-specification does not mention a copy. Decide which is right.

### 16. MINOR. The fork: the repair is sound, two places remain open by the command line

The note in `joint/f21/smoke.py` and the function `pool` in `joint/f2/evaluate.py` (lines 51 to 63) are sound as far as I can judge by reading: the evaluation spawns its workers when torch is loaded; the host check runs its three stages in three fresh processes and ends a stage that waits, with its workers; and the commands of the runbook that open pools are processes that never load torch. Executed: after importing everything that `generate`, `label`, `check-labels`, `evaluate` and `verdict` import, torch is not among the loaded modules.

Two places remain, neither on the runbook's path:
(a) `joint/f2/data.py`, lines 195 and 285, open their pools through `c22.data.pool`, which forks whatever is loaded. The command `chain` runs its commands in one process, so a chain that held a `train` or a `predict` before a `generate` or a `label` would fork from a process that has trained. The runbook's chains hold data commands only. `chain` could refuse the two GPU commands.
(b) The comment of `joint/f21/__main__.py`, line 212, "a later command of a chain chooses its solver itself", is not so: `joint/fejoint/linsolve.py`, line 37, fixes the solver when the module is first imported. A `label` chained after a `train` would solve with SuperLU.

### 17. MINOR. Small points of robustness

(a) `check-labels` on a ledger without entries ends with `ValueError: min() iterable argument is empty` (executed), and without a ledger with `FileNotFoundError`. The runbook's case "fails only because labels are missing after a label command was cut off" shows as a traceback when no label was written.

(b) `joint/f21/gate.py`, lines 91 to 92: when the seed is the same and the gate configuration differs, the message still says "was drawn with seed ...; its seed is fixed" (executed).

(c) `predict` makes the seed's folder before its refusals and leaves it empty (executed).

(d) `joint/f2/train.py`, lines 85 to 107: `os.kill(pid, 0)` also succeeds for a process that has ended and has not been collected, and for a number that the system has given to another process. Comparing `os.getppid()` with the number is exact.

(e) That a non-finite stop is final rests on `history.json` being restored: with the checkpoint alone the command resumes. The queue must copy that file out before anything else after such a stop.

(f) In a new folder `generate` does not compare the members it draws with a manifest that was restored. If the random generator of numpy changed between two sessions, the sample would change and nothing would say so; the queue's comparison of versions is the only guard.

(g) `verdict.json` and the evaluation files hold `Infinity` and `NaN`, which Python reads and strict JSON readers do not. Worth a line in the records' description.

### 18. MINOR. Numbers and wording

(a) `joint/docs/F2_development_note.md`, line 26: "B-13's moment is 1.0% to 5.1% higher". The records give 0.91% at the fourth level (1.23, 1.34, 1.00, 0.91, 1.06, 3.32, 5.11): 0.9% to 5.1%. `joint/probes/f2_under/PRESPEC.md`, line 87, has it right.

(b) Line 224 of the pre-specification: "an epoch of the first cycle took 85.5 s". The record's median is 85.55 s and its mean 85.66 s; `joint/probes/f2_under/PRESPEC.md`, line 70, says 85.6 s for the same run. Immaterial; one of the two.

(c) `joint/records/f2_dev/README.md`, line 3: "Every number that the development note and `docs/PRESPEC_G-F2.1.md` quote can be computed again from the evaluation files below". Not every one: the readings during training in section 3 of the note and the single-member runs have no file in the folder, the times come from the run records, the sizes from the manifest, and the two version numbers from nowhere (finding 12b). "Every number of the tables and of sections 5 to 8" would be true as far as I checked.

(d) Line 60 of the pre-specification, "The runs of the development on the family's mesh, all with seed 0", heads a table of the five runs of full length. The note has others on that mesh: the single-member runs and the runs carried over from the smaller mesh that were ended by their stop rule. "The runs of full length".

---

## 2. What I checked and found correct

**The code list and the pins**
- `CODE` against the imports, with a walk of my own over every import statement, those inside functions included: 44 files reached, 44 listed, no difference. No dynamic import in any of them (`find_spec` is used to locate the repository package only). The limit of that statement is finding 1.
- The six repository files of `REPOSITORY_CODE` are all that `fejepa.models.fejepa` and `fejepa.train.schedule` import; their hashes are the pinned ones.
- The two run configurations hash to the pins of the pre-specification, and their settings are those of the text: 400 and 160 epochs, 128 and 160 members, 51,200 and 25,600 steps, peak rates 1e-3 and 3e-4, weight decay 1e-4, second-moment coefficient 0.99, the cap at 5 times the median of 256 steps, clipping at 1.0, four rotations a step, the square-root draw up to the device range and the uniform draw up to 1.15 times it, width 256 with 8 layers and 8 heads, the condensed reading with base level 0.0125, amplitudes 0.5 to 3 and 12 evaluations. The encoder has no dropout, so a resumed run needs no random state of the GPU.
- The stamp files of the five earlier gates (`G-C1.3`, `G-C2.1`, `G-C2.2`, `G-C2.3`, `G-F1`) still verify in this tree: no file that an earlier gate stamped has changed.
- `joint/records/f2_dev/FILES.sha256` verifies for its 43 files and lists every file of the folder but itself and the README.

**The refusals** (executed, the first through `tests/test_f21.py`, the others through the command line of the reduced copy or the functions)
- Without a stamp file and with another configuration hash: refused before anything is written. `write-config --config-sha` ends with 0 only on the stamped code.
- The sample: without a seed, with a date before the configured day, with a used seed, with another seed once it is written (finding 10a for how), into a folder that holds files and no `sample.json`. `sample.json` is written before the first member is exported.
- The training: a seed that is not the gate's; a second cycle without its first; and the sample's folder given as training data, which `f2.train` refuses by the data hash ("the data were generated under another family or data configuration"). The training code reads exports of the two development folders only; it reads no label and no file of the sample.
- The predictions: twelve broken chains refused, each with its own message (finding 14d for the thirteenth).
- The sample's evaluation refuses prediction files that are not the recorded ones (`tests/test_f21.py`).

**The verdict's arithmetic** (executed on made-up files, reduced configuration)
- PASS, FAIL and INCOMPLETE as line 173 of the pre-specification defines them: a cycle with a non-finite status of either kind, in either cycle, gives FAIL; predictions on the sample that are not finite give FAIL; a missing record of a cycle, of the predictions or of a seed in the evaluation gives INCOMPLETE; `--final` ends with 1 on INCOMPLETE and with 0 otherwise.
- The quantile is numpy's with infinite values kept: one infinite pair of 14 leaves the 90th percentile finite, two make it infinite; values that are missing or not a number count as infinite; values exactly on the lines pass.
- One seed with every pair infinite passes by the median over the seeds, as the text says it does.
- Fewer or more members, another number of levels, or rows missing for a finished seed end with an error that names the cause.
- `recompute.py` agreed with `gate.verdict` in six cases (plain, levels that differ, infinite and not-a-number pairs, a member without rows, a failed cycle, a missing seed) and disagreed, as it should, when I changed the verdict's word, a value across the seeds, or the list of failed seeds in the verdict file.

**The judged quantity**
- A check with a known answer on a member of the reduced sample: the field of a level set to the reference's own state of another level, in single precision. Expected -34.427167%; the code's first-order value -34.427166%, its exact value -34.427165% (two solves). With the level's own state: 3e-8, which is the size of what single precision costs.
- The recomputation of 868 recorded values from the records (finding 7): no difference.

**The numbers of the texts against `joint/records/f2_dev`** (median, 90th percentile by linear interpolation, largest value of `abs_curveD_err`, as the README says)
- The table of line 62 of the pre-specification, all five rows: 1.53, 5.39, 67.9; 0.99, 3.69, 56.9; 1.06, 3.46, 17.6; 1.07, 2.99, 12.2; 4.69, 11.64, 34.3.
- For the gate's recipe: the 16 random members 1.02, 2.53, 4.4; the four tested members 0.51, 1.60, 2.1; the raw reading 1.29, 3.94, 20.8; thin plates 2.63, 1.12 and 2.78; the signed median positive at every level.
- The smaller mesh: medians 0.93, 1.28, 1.17 and 90th percentiles 3.10, 4.11, 3.52 for the seeds 0, 1 and 2.
- The trial of 24 November: all six measures of the control and of both arms as in section 6 of the note; all 31 members better at the last level, 29 and 27 worse at the two lowest.
- The note's section 3 (0.6 and 5.8, 1.6 and 11, 2.2 and 11 at the same device rotation; 4.4 and 13.4, 12.7 and 30.9, 15.5 and 38.5 at the same rotation of the measuring ring), section 5 (every row, and the two averages 1.00 and 3.69, 1.21 and 4.11) and section 7 (3.8, 9.2 and 11.8).
- 8,632 nodes and 25,916 unknowns for B-13; 85.5 s and 107.0 s an epoch, 9.5 and 4.8 hours; the versions of Python, torch, numpy and scipy and the 48 processors; all five runs of the table finished without a resume; the export and label times are consistent with the generation log and the ledger; the shares of steps below one eighth of the device range (27% and 10%) follow from the two draws.
- The cross-references: the frictionless model 3% to 8% below the tests (`joint/docs/F2_preparation_note.md`, line 91), G-F1 failing one criterion of three, G-C2.1 losing seed 0.
- Exceptions: findings 12b and 18a.

**The four things the brief named as seen before the stamp.** The recipe adopted against the trial's rule, the single draw with 20261127, the one seed on the family's mesh and the 31 watched members are each stated, in the places where a reader looks for them, without softening. What I found missing or understated is in findings 7a, 12c and 12d.

**Robustness** (executed where said)
- An export step ended by force after 12 seconds and run again: completes, manifest of all members.
- A folder that holds the small files only (`sample.json`, manifest, logs, ledger, summary): `label` and `check-labels` end with an error on the first missing file; nothing wrong is written.
- With the numpy of the review machine the array files are byte for byte the same when the same arrays are saved again (the archive entries carry no time), so an export made again from the same solve has the same hash.
- A training paused by its limit, resumed, ended in its predictions and run again (finding 3): the resume goes on at the predictions and does not touch the state.
- `together` with one command that fails and one that succeeds: waits for both, names the failed one, ends with 1. `chain`: ends at the first error.
- By reading: the checkpoint is written to a temporary file, flushed and moved; the history of a run is inside its checkpoint, so `init_from` survives a resume; a second cycle that is ended before its first checkpoint starts again from the first cycle's state; the evaluation writes its file at its end only.

**The runbook's quoted outputs** that I saw: `write-config` (the configuration hash, the four pins, 44 file hashes, `stamped code: yes`); `generate` (`<member> <seconds> s preload ok`); `label` (`... converged`, then `labelled N`); `check-labels` (one line of JSON with `"ok": true` and, for the sample, `"members": N`); `evaluate` (the status of the three seeds); `verdict` (the text, and the two files). Every flag of every command of the runbook exists in the parser.

**The rules for the repository's text**, in the new files (the pre-specification, the development note, the runbook, the records' README, the sources of `f21/` and `f2/`, `tests/test_f21.py`, `recompute.py`): no em dash and no en dash; the only characters outside ASCII are Greek letters in two documents; no American spelling in the prose (what my search found are identifiers: a method of torch, a constant of another system, a configuration key, a module of the standard library); no path of a home or temporary folder, no user name, no e-mail address, no path of a store; the project's nickname does not occur, and its second half occurs only inside the package's path, the package's name in two error messages, and the name of the environment variable that `tests/test_f21.py` reads. The fast tests pass: 12 passed, 1 deselected.

---

## 3. What I did not check, and why

- **The host check, `tests/test_f2_dev.py` and the test that runs the host check**: not run, as instructed; each takes twenty minutes or more on the review machine.
- **A stand-in training to its end through the command line, and what follows it**: one epoch did not end within two minutes here. So the success paths of `train` and `predict`, the evaluation of the development's members, a verdict of PASS or FAIL from real files, and the positive path of the chain of hashes were read and not run. The host check covers them by its design; I did not see it run.
- **Anything on a GPU**, three trainings at the same time, the timing, and the behaviour under the host's versions of Python, torch, numpy and scipy.
- **The queue and the task file.** They are outside the tree. Which file marks a step as complete, what is restored at the start of a session, how the versions and the GPU are compared, which thread settings the steps get: none of it could be read. Findings 3, 6 and 11f say where the gate depends on it.
- **The family's mesh.** No member was exported, solved or evaluated on it; every experiment used the smaller mesh. Times of the labels and of the evaluations are therefore unchecked beyond the development's records.
- **The numbers printed from the draw with 20261127** (7 of 64; 10.47 and 24.78 mm): checking them needs the draw that the rules forbid me.
- **Declarations**: that no member was drawn with a date from 25 November 2026 on other than 20261127, that the seeds 5, 6 and 7 never trained the two configurations, and the owner's messages, which are not in the tree.
- **The records behind the placeholders**: the host check on a processor, the simulation of the host's task (and the seed it used, finding 5f), the timing, the test counts.
- **The reference code of the earlier gates** (`fejoint/`, `c2/`, `c22/`, `f1/`) beyond the lines the gate reaches, and the mathematics of `f2/model.py` and `f2/torch_energy.py`. `f2/precond.py` and `f2/prolong.py` are imported and not used by the gate's two configurations; I did not read them closely.
- **The scripts of the two trials** (`probes/f2_stage2/`, `probes/f2_under/`): not run; I computed their numbers with code of my own.

---

# What the author did after round 1

25 November 2026. What was done about each finding, in the reader's numbering. "Changed" means changed in the files that are stamped or that go into the repository with the stamp; the tests named are in `tests/test_f21.py`.

**1. The material curves (blocks the stamp): changed.** The three files of `f1/data/` are stamped with the code: `DATA` in `f21/__main__.py`, 48 stamped files with the new `f21/stamp_day.py`. A test names them and ties their hashes to gate G-F1's stamp. The pre-specification and the runbook give the new count and say what the data hashes cover and what they do not.

**2. The sample evaluated while seeds are still to be trained: changed, further than asked.** `f21/gate.py` now holds to three rules by itself: no seed predicts the sample before every training of the gate has ended (`settled`); the sample is evaluated only when every seed has predictions on it or a record that it has none; the development's members are evaluated only when every training has ended. The task's steps were reordered to fit: every training comes before the first prediction. Before the sample's evaluation exists, `verdict` shows the state of the runs and no number of the sample. The pre-specification says in "Procedure" that the predictions' readings are compared with the labels by the evaluation and by nothing else, and that a gate ended while INCOMPLETE is reported with whether predictions on the sample existed.

**3. A cycle recorded as finished before its predictions: changed.** `cycle_state` counts a cycle as finished only with its record and its `condense.json`; the second cycle, the predictions on the sample, the evaluations and the verdict all use it. `f2/train.py` is not changed. The runbook's sentence is corrected and a table names what completes each step. The host check takes a finished cycle's `condense.json` away and puts it back, and a test does the same on made-up files.

**4. A preload that is not on target: changed.** `f21 generate` ends with an error, for all three folders, if a member's preload did not converge or is not on target, or if the generation log holds no preload record for a member of the manifest (`check_preloads`). A stop condition was added.

**5. The sample's seed: changed by the option the reader put to the owner.** The seed is written into `f21/stamp_day.py` when the stamp is prepared and is part of the hashed configuration. No command takes a seed. The points (a) to (e) fall away with it: the code refuses every other seed in every folder, and what is left for a person to check is one comparison, the day of the stamp's commit against the seed, for which the runbook gives the command of (a); a stamp whose commit carries another day is void and is made again. (b): the rule refuses a day that has not come. (f): a reduced configuration takes days of January 2026 only (`not_after`), which a test asserts against the days the stamp could fall on; the host check draws with 20260102 and the session simulation with 20260103, and both records say so. The owner agreed to "the date of the stamp as its seed"; the change of mechanism is listed in "Authority" among the author's choices, and the owner decides on it by making the commit.

**6. An evaluation that does not record its inputs: changed.** Both evaluations write the SHA-256 of every prediction file, of the manifest and of the ledger as read, with the linear solver, and end with an error if one changed while they ran. The verdict refuses a sample's evaluation whose inputs are not those on record (the predictions' records, the manifest and the ledger as they are), whose members are not the manifest's, or which lacks the exact value. `predict` compares the seed in the state file (14d).

**7. The first-order step never compared with the exact value: measured, and the text completed.** (a) The exact value was computed for the gate's recipe on eight of the 31 members of the development, on the family's mesh, from the recorded readings (`probes/f21_first_order/first_order.py`; the judged error depends on the predicted field through three recorded numbers, as the reader showed). The result is in "What was seen before the stamp" and in `records/G-F2.1/before_stamp/`. The reader's estimate from the records was computed again with the same script and agrees. (b) The interpolator and its continuation are named in "The judged quantity".

**8. Outcomes left undefined: defined.** (a) An export or a label that ends with the same error each time counts as a label that fails. (b) `check-labels` now tests, for every labelled member, that the rotation of the measuring ring rises and that the reference code evaluates each labelled state, in worker processes, before any training. (c) Finding 4. (d) The configuration names the linear solver; `generate`, `label` and `evaluate` refuse a host with another, `write-config --config-sha` ends with an error on such a host, `check-labels` requires the solver in every ledger entry, and the evaluations record theirs. (e) Finding 5. (f) The sample is spent once its first member is exported. (g) Cycles under way at a stop for good are trained to their end, also in a later session; no cycle is started afterwards, which the command now refuses by itself; the interpretation says that a stop before any seed has finished leaves no number on the sample. (h) The runbook's new section 10 gives the closing steps; `predict` writes a record without predictions for a seed that has no finished run, and the final verdict is complete only when what the finished seeds gave is on record. The session simulation runs these steps on a copy of a finished task in which one cycle's record is rewritten as a non-finite stop. (i) Runbook, section 11. (j) The pairs with an infinite error are listed by member and level in the verdict, and the wording fixed for a PASS names them.

**9. The label check as the queue's stop only: changed.** Both evaluations run the label checks first and refuse if they fail.

**10. The host check and the tests.** (a) Changed: no command takes a seed any more; the host check's refusals name the text they expect, and the refusal of another configuration in the sample's folder is reached with a seed that passes the rule. (b) Changed in part: tests now run `write-config`, `verdict` with its exit codes, `chain` and `together` through `main` with a temporary stamp file; the other commands are run through the command line by the session simulation, whose record is in `records/G-F2.1/before_stamp/`, and not by the tests. (c) Changed: the training stage of the host check sets `FEJOINT_SOLVER=legacy`, and so does the command `predict`, which before loaded the sparse solver's libraries beside torch; a check asserts that the stage ends without them. (d) **Not done.** The host check has not run on the gate's host before the stamp. It needs the final code, another session of the helper and about a day; if it fails after the stamp, nothing has been drawn and the stamp is made again, which the pre-specification says. The owner was given the choice.

**11. The runbook: rewritten.** (a), (b) corrected. (c) `write-config` makes its folder. (d) The commands refuse to run while a bytecode folder lies in a stamped package; it is part of the stamp check that every command makes. (e) The pool commands set one thread for linear algebra themselves. (f) The table of completion files and the paragraph on what a session starts from. (g) Sections 10 and 11. (h) Step 0b. (i), (j), (k), (l), (m) corrected as proposed; `evaluate` now ends with an error if a seed with a finished record has no readable predictions.

**12. Statements of the pre-specification.** (a) The timing was made before the stamp, on the GPU the helper could get, and is reported; the configuration's key is now `training_seeds_kept_from_the_gate`, and the text says by which command a later timing would be made. (b) The text says where the two version numbers come from and that the development's session records do not hold them; the gate's first command prints them. (c) Said, with the owner's message that asked for the trial. (d) The cost of arm 2 is given in full.

**13.** (a) to (e), (g) to (i): the text follows the code. (f): one sentence. (b): the verdict needs the evaluation of the development's members for every seed with a finished second cycle.

**14.** (a), (b), (c), (d): changed (tests on made-up files). (e): `--data` is used: the verdict compares the development's manifest with the one its evaluation read.

**15.** (a) `src` goes behind the stamped tree on the module path. (b) Finding 11d. (c) Said; the script's hash at the stamp is recorded. (d) The pre-specification names the copy.

**16.** (a) `chain` takes `write-config` and the pool commands only. (b) The comment is gone with the case.

**17.** (a), (b), (c): changed. (d) **Not changed**: `f2/train.py` stays the file that the last run of the development executed on the gate's host; the case needs a recycled process number within a session, and its cost is a training that runs on until the session ends. (e) Runbook, section 10. (f) `sample.json` holds a hash of the drawn parameters, and a later call refuses a draw that differs. (g) Runbook, section 8.

**18.** (a), (c), (d) corrected. (b) 85.55 s, the record's median.

**Found by the author while repairing**
- With the seed in the configuration, a call of a function with the gate's own configuration could have drawn the gate's sample before the stamp (the commands refuse without the stamp; the functions did not). `f21/config.py` now refuses to configure the gate's sample until a command has found the code to be the stamped code; a test asserts that nothing is drawn.
- The session simulation found that the host check's refusal of a used seed relied on the base configuration listing that seed; under the simulation's reduced configuration it drew a sample of two with the day 20260103 instead of refusing. The check now puts the seed on the list of the copy it tests.
- The development's code is not byte for byte the code that made the recipe's runs (the records of the runs hold the hashes). The pre-specification now says so, and a stand-in training was run with the development's files of 21 and of 24 November 2026 and with the stamped files ("What was seen before the stamp").
- In the task as first written the predictions of a seed followed its own second cycle. That order is the one finding 2 describes; the task generator now puts every training first, and the code refuses the old order.

---

# Round 2 (25 November 2026, delivered at about 15:07 GMT)

# Independent reading of gate G-F2.1 before its stamp: round 2

25 November 2026. Reader: an agent that wrote none of the code or text and did not take part in round 1. Line numbers are those of the tree read (tree2). "Executed" means I ran something; "Read" means I read only.

Seeds: no function or command that draws members was called with the gate's configuration or with a day from 25 November 2026 on. check_sample_seed was not called with any such day either. The only gate-configuration command I ran was write-config, in a scratch copy, with a temporary stamp file that I then deleted. No training, host check or test_f2_dev was run.

## (1) Findings

### 1. BLOCKS THE STAMP. records/G-F2.1/before_stamp/ is cited and is not in the tree
Where: docs/PRESPEC_G-F2.1.md line 128 (hash of probes/f21_recompute/recompute.py "is in records/G-F2.1/before_stamp/"), README.md line 75, and the fills exact_measure and timing_seen (".../first_order/", ".../timing/").
Evidence (Executed): `ls -R records/G-F2.1` gives "No such file or directory". The measurement files exist only in the review material (round2/measurements/).
Why it matters: the stamped text points to records that the stamp commit does not hold. In particular, the only fixed reference for "a change of recompute.py after the stamp" is missing.
Change: add the folder, with the first-order, timing and code-equivalence files, the host-check record, the simulation summary and the SHA-256 of recompute.py, to the stamp commit. Or drop the references.

### 2. SHOULD BE FIXED. The stamp check certifies itself; the text claims more than the code can give
Where: f21/__main__.py lines 89-105; PRESPEC line 124 ("Before the stamp there is no such file, so that no command of the gate can draw the sample or train from a draft"); __main__ docstring lines 29-30.
Evidence (Executed): I copied joint/{f21,f2,f1,c2,c22,fejoint,docs} and src into scratch. There I wrote docs/G-F2.1_code.sha256 from the sha256 of CODE+DATA and ran `python3 -I f21/__main__.py write-config --out <folder>/cfg.json`. It printed "stamped code: yes" and "linear solver: pardiso". (I did not run generate, and I deleted the file.)
Why it matters: anyone can turn any uncommitted draft into a "stamped" tree with one sha256sum, and the commands, sample draw included, then run. The real protection is procedural: runbook 0a to 0c, the archive from the commit, and the repository history.
Change: say so in the pre-specification, at line 124 and in "How the code holds to it": the stamp file proves only that the files match it; that the files are those of the commit is checked by 0a to 0c.

### 3. SHOULD BE FIXED. The guard against drawing outside the commands leaks within a process
Where: f21/__main__.py line 302 (`stamped_config._STAMP_VERIFIED = True`, never reset); tests/test_f21.py lines 233-260 and 625ff (main() run with a temporary stamp file and the gate's hash); the test at line 140 asserts the flag is False.
Evidence (Executed): `pytest tests/test_f21.py::test_command_line_refuses_without_stamp_and_with_another_hash tests/test_f21.py::test_the_gates_sample_is_not_configured_outside_its_commands` gave "assert True is False ... FAILED ... 1 failed, 1 passed". In file order the suite passes only because that check runs first. Every later test, and any test file pytest collects after test_f21.py in the same process, runs with the guard off. Today no later call uses the gate's own configuration, so nothing was drawn.
Why it matters: PRESPEC line 151 states the guard as a property ("a test, a check or a look at the code cannot draw it by a call"). It holds only in a process that has not run a stamped command.
Change: in the tests, monkeypatch.setattr(C, "_STAMP_VERIFIED", False) wherever main() can pass the stamp check (an autouse fixture). Optionally reset the flag in a finally of _run unless the command is chain.

### 4. SHOULD BE FIXED. Deadlock: a cycle that stops for good inside the closing task
Where: RUNBOOK section 10 step 1 ("... each as a step of its own, until it is finished"); queue/make_task_g_f21.py one() (done = condense.json); f2/train.py lines 523-525 (a non-finite record returns at once); f21/__main__.py lines 316-317 (exit 1).
Read: if a cycle that was under way at the first stop then stops itself (non-finite loss or end predictions), its step can never complete. Each later session runs it again, it ends with exit 1, and the session stops before the predictions, evaluations and verdict. No text says what to do.
Change: one sentence in section 10, for instance "a cycle that stops for good during the closing task is left out of the next closing task; the closing steps go on". Or make a training step complete on a history.json whose status is non-finite.

### 5. SHOULD BE FIXED. A stop is not kept across sessions by the queue
Where: RUNBOOK line 44 ("After a stop nothing of this runbook is run again before the operator has reported"); make_queue_notebook.py CELL_RUN (FAILED and OUTCOME live in memory only; status.json is written but never read back at the start of a session).
Read: if the helper runs the notebook again after a stop, completed steps are skipped and the task goes on. After predictions on the sample that are not finite, for example: predict_sS has its history.json and counts as done, so the next session runs the other seeds' predictions, both evaluations and the final verdict without the owner's answer. After a non-finite loss the re-run fails again, which is harmless, and a stop that came from the host is meant to go on. The gate's code keeps the order rules either way, so the integrity of the numbers is not at stake; the runbook rule is.
Change: have cell 2 halt when status.json of the task says "failed", unless the task file carries a field such as "resume_after_failure" that the operator sets. Or state in the runbook and in the helper's sheet that after a failure the notebook is not run again until told.

### 6. SHOULD BE FIXED. The queue that is "kept with the records" names an account, a person and the nickname
Where: RUNBOOK 0d ("The task file and the queue are kept with the records (section 8)") and line 161 ("No file of the returned records names the shared store, an account or a person"); queue/make_queue_notebook.py (an account address in INTRO, a person's name throughout, and the store's folder name containing the project nickname).
Read. Change: keep the notebook outside the repository and say so, or keep a redacted copy. The task file itself is clean.

### 7. SHOULD BE FIXED. An unlisted placeholder, and what its text must say
Where: PRESPEC line 82, [[FILL:code_equivalence]]. It is in neither fills_partial.json nor the list of placeholders still to write.
Evidence (Read): measurements/code_equivalence shows stand-in runs ("dry", "dry_more_ux": 6 and 12 steps, and 60 and 120 in the long runs) equal to the last bit between the files of 21 and 24 November and the stamped files.
Why it matters: the stamp step could leave the marker in. And the text must not overclaim: the comparison covers the stand-in presets on the small mesh on a processor, not the code paths only the pinned presets reach (resident_members 128 and 160, the family's mesh, the GPU).
Change: add it to the fill list, and word it with that scope.

### 8. MINOR. The verdict's "complete" and the development evaluation take some things on trust
Where: f21/gate.py lines 560-562 (done), 612-626, 630-632.
Read:
(a) In the FAIL branch, complete = settled and done and dev_done. When the sample evaluation exists, done does not require every seed's sample record to exist now. If the queue fails to restore a "no predictions" history.json, the verdict is complete and --final ends with 0. The record's absence shows only as "sample None" in the text.
(b) The development evaluation is compared with the manifest only, and only if data/manifest.json exists (`if mp.exists()`). Its recorded prediction hashes and ledger are not compared with the files as they are.
Change: in (a), require a non-None sample status for every seed; in (b), compare the dev inputs like the sample's and refuse if the manifest is absent.

### 9. MINOR. Section 11 against the stop rule
Where: RUNBOOK section 11 ("The cycle then counts as not started, and its train command starts it from its beginning"); gate.train lines 309-313.
Read: after a stop for good elsewhere, a renamed folder counts as "not started" and train refuses it. Section 11 does not say what happens then, for example a state file that cannot be read during the closing task.
Change: one sentence: after a stop for good, a cycle whose folder was moved aside is not restarted and its seed gets the no-predictions record.

### 10. MINOR. The exact_measure fill leaves out that the re-solved exports and labels are not the records' bytes
Where: fills_partial.json exact_measure ("Their exports and labels were solved again ... agrees with the record to 1e-13"); measurements/first_order/data.json ("export equal to the record's, by SHA-256": false for all eight; "label equal ...": false for all eight).
Read: the 1e-13 agreement (exact.json: 8.1e-14 in moment, 4.0e-14 in rotation) shows that the difference is rounding, but the text should say the files differ.
Change: "re-made exports and labels differ from the recorded files in their bytes; the solves at the end rotation agree with the record to 1e-13".

### 11. MINOR. A100 timing: an extrapolation, and a minimum time below the estimate
Where: fill timing_budget ("about 21 and 10 hours a seed"); make_task_g_f21.py MIN_HOURS evaluate_sample 4.0.
Read: 21 h is 187.4 s x 400 = 20.8 h, measured. 10 h for the second cycle is 107.0 s x 2.19 x 160 = 10.4 h, an extrapolation (no second-cycle epoch was timed on the A100); say so. By the same fill the sample evaluation takes 2.5 times as long on such a runtime, 5 to 7.5 h, above the 4.0 h minimum. A session with 4 to 7 h left starts it and loses it; nothing is wrong, but compute is wasted. Raise the minimum for a runtime with fewer processors, or state it.

### 12. MINOR. Runbook wording
- Line 49, "the data steps about 25 minutes in all", against sections 2 and 3, "about 15 minutes" each.
- Section 5: "It also refuses unless both cycles are this seed's finished runs". After a stop for good it writes a no-predictions record and ends with 0 (section 10). Add "(after a stop for good, see section 10)".
- Line 74: "If a session ends inside it, the next session starts it again in an empty W." After a failed host check, host_check/smoke.json is carried to the store and restored, so smoke refuses the non-empty folder. The pre-specification makes a failure a restamp (a new task); say that the old task's folder is not reused.

### 13. MINOR. 17d not stated
Round 1 17d (os.kill(pid, 0) in f2.train.launcher_gone: a reused or uncollected pid keeps a training running after `together` ended) is "not changed". Neither the pre-specification nor the runbook names the consequence (a training that goes on until the session ends). One sentence would do.

## (2) The repairs of round 1
1 confirmed: DATA (3 coupon curves) stamped; 45+3=48 (Executed: len(CODE)=45, len(DATA)=3).
2 confirmed: settled() gates predict and evaluate dev; the sample evaluation needs every record; the queue orders every training first.
3 confirmed: cycle_state needs condense.json; the table in the runbook; the host check renames condense.json aside.
4 confirmed: check_preloads for every folder.
5 confirmed (a to f): seed in stamp_day.py and hashed; the future-day refusal; reduced not_after 20260131; the 0b command in UTC. The residual is finding 2.
6 confirmed for the sample (inputs recorded, checked at the end and in the verdict); partly for the development evaluation (finding 8b).
7 confirmed: measured on 8 members (finding 10 on wording); PchipInterpolator and its continuation named (PRESPEC line 183).
8 confirmed: a (line 238), b (_reference_member), c, d (solver: configuration, refusals, ledger, record), e, f (line 157), g (line 239), i (section 11), j (not_finite_pairs; the PASS wording). h is partly done: section 10 is there, but see finding 4.
9 confirmed: both evaluations run check_labels first.
10 partly. a confirmed (refusals match their texts; the other-configuration check uses 20260103 with used=False). b partly (tests reach write-config, verdict, chain and together through main; the other branches rest on the simulation, whose record is a placeholder and is not in the tree). c confirmed. d not done, and stated in PRESPEC line 95 with its consequence.
11 confirmed (a to m). The runbook's table matches the generator's done lists (Read).
12 confirmed (a to d); d re-verified against outside_the_rule.txt.
13 confirmed (a to i).
14 partly: a, c and d confirmed; b and e partly (finding 8b).
15 partly: a, b and d confirmed; c partly (the hash is said to be in a folder that does not exist, finding 1).
16 confirmed (a, b).
17 a, b, c, f, g confirmed. d not changed and not stated (finding 13). e partly (the notebook carries files right after a failed step; a hard kill between the history write and the carry remains, which is small).
18 confirmed (a to d).

## (3) Answers
C1. No. predict_sample refuses unless settled() (gate.py lines 348-350). settled is False while any cycle is "under way", and while any is "not started" unless some cycle has stopped for good. evaluate --what sample needs every seed's record, and those exist only after settled. evaluate --what dev needs settled. verdict computes nothing from predictions; it reads only the evaluation file. chain refuses train and predict. The paths that bypass this are outside the gate's commands: a self-written stamp file (finding 2) or a process with a leaked guard (finding 3), and both still go through the same settled check. If condense.json is lost after the predictions, the cycle reverts to "under way". Re-running train then changes no state (the epoch loop is empty) and only repredicts the 31 development members.
C2. Deadlocks found: a cycle that stops for good inside the closing task (finding 4); a failed host check re-run in the same task folder (finding 12, third point); a folder moved aside after a stop for good (finding 9). Covered states:
- a session ending inside the end-of-cycle predictions (history says finished, no condense.json, under way, resumes and predicts);
- a session ending inside predict (history.json is written last, so it recomputes);
- a session ending inside an evaluation (no mark, so it reruns from the start; nothing written before the end);
- files not restored (the carry covers runs/*/label_free_s*/*, runs_gate, marks, records, logs, data bundles; a cut-off data step re-exports and relabels missing files, and label re-solves when the label file is missing).
C3. Not with another seed through the stamped commands: the seed is in the hashed configuration, no command takes a seed, the development CLI (f2/__main__.py) has no seed option for the sample, and smoke's reduced() accepts January 2026 only. Outside the stamped commands, yes, without editing code: write a stamp file into an unstamped tree (finding 2, executed up to write-config), or call the functions in a process in which a stamped command has already run (finding 3, executed).
C4. Ends with 0 while something is missing: the FAIL branch with a sample record lost after the evaluation (finding 8a); a development evaluation that is stale in its prediction files or ledger, or checked against no manifest (finding 8b). Ends with an error while everything is there: I found no case in the PASS or FAIL logic. The no-finished-seed case gives complete True with or without the sample evaluation, and the FAIL-by-criteria case gives complete True.
C5. Checked against measurements and records, all agree:
- arm 2's cost (0.79 to 1.01, 1.97 to 2.63 in 8 thin members (Executed: 8 of 31 with tp<12.5), 27 of 31, 0.99 to 1.07, 1.54 to 1.82); the table under "What was seen";
- 45 and 224 (Executed: numpy linear interpolation, and c2.evaluate._quantile keeps inf where np.quantile gives nan from 46 on); 45 and 48 files; nineteen checks (6+9+4 in smoke.py);
- timing_seen and timing_rule (187.43, 495.52/495.40/496.14, ratio 2.644, 187.43/85.55 = 2.19, A100 with 12 processors and the same library versions as the development sessions);
- timing_budget (100 h / 5 to 6 sessions and 47 h / 3 by my arithmetic);
- exact_measure (0.03/0.17/0.52 pp; 2.32/4.69/12.22 and 2.33/4.96/12.38; dev_S1 (tp 25) level 4, 4.91 against 5.42; 3 to 5 solves; 25 s and 54 s; the estimate 0.0009% and 0.107%; the eight members are the top eight by step; exact.json's recorded values equal arm_2/evaluation.json to 0).
The messages the runbook quotes match the code ("preload ok", "converged", "labelled N", "stamped code: yes", "linear solver: pardiso", `"ok": true` with the stages, `{"status": "finished", ...}`). Caveats in findings 10 and 11. Not checkable: the 7 of 64 and the 10.47/24.78 mm of seed 20261127.
C6. The generator matches the runbook table and section 10: steps, order (all trainings before any predict; one after another first_s, second_s per seed; together first_all, second_all), done files, marks and bundles. The {H} and {W} substitution reaches the --do strings of together. In closing mode, predict needs only marks/data_sample, which is safe because the code refuses and a paused closing training ends the session first. A session ending at any point resumes correctly by C2, with the exceptions of findings 4 and 12. Findings 5 and 6 concern the notebook.

## (4) Checked and found correct
- The fast tests: 24 passed.
- cycle_state, settled, train, predict_sample, evaluate, verdict and their refusals, against f2.train and f2.evaluate: the run_status and predictions_written semantics agree with cycle_state; f2.evaluate's write flag changes only writing.
- The pinned presets have no EMA (no unrestored average folders).
- Exit codes against the __main__ docstring.
- Thread and solver settings: the pool commands set one thread; train and predict run with FEJOINT_SOLVER=legacy; the queue gives one thread to its processor steps.
- The f2.data generate, label and check_labels resume behaviour.
- The text rules in the new files: no em or en dash, no <a name that the brief lists as not to appear>, no nickname, no home paths; the only non-ASCII characters are the Greek symbols of the pre-specification.

## (5) Not checked, and why
- The host check, test_f2_dev, any training or evaluation: forbidden or too slow here.
- The simulation record: a placeholder, not in the tree.
- That the pinned presets switch on no later setting (PRESPEC line 82) beyond reading the presets.
- recompute.py in depth: read its imports and quantile rule only.
- The figures of seed 20261127: they would need a draw.
- docs/F2_development_note.md beyond the 18a line, and records/f2_dev/FILES.sha256.

Process note: my first command (python3 -I with importlib exec of f21/__main__.py; -I ignores PYTHONDONTWRITEBYTECODE) wrote f21/__pycache__/__main__.cpython-313.pyc into the review tree at 14:57. I removed it, and `find tree2 -name __pycache__` is now empty. The scratch copy with a stamp file has had the stamp file deleted.

---

# What the author did after round 2

25 November 2026. What was done about each finding of the second reader, in that reader's numbering. "Changed" means changed in the files that are stamped or that go into the repository with the stamp; the tests named are in `tests/test_f21.py`. Nothing of the development's code (`f2/`) was changed after this round, so the comparison of the code as run with the stamped code stands as it was made.

**1. `records/G-F2.1/before_stamp/` cited and not in the tree: assembled.** The folder was put together last, from the runs on the final files, and is part of the stamp's commit: the host check on a processor, the outcome of the session simulation, the timing of the host, the first-order value against the exact one, the comparison of the code as run with the stamped code, the list of the tests, and `not_stamped.sha256` with the SHA-256 of `probes/f21_recompute/recompute.py` and of the two test files.

**2. The stamp check certifies itself: the text now says what the check proves.** The pre-specification ("Configuration") and the head of `f21/__main__.py` say that the check compares the files with the stamp file and no more, that a stamp file written beside a draft would pass it, and that the tie to the stamp's commit is the reading back of the commit and the archive whose SHA-256 the task file holds (`RUNBOOK_F21.md`, 0a to 0c). The code is not changed: a file in the tree cannot prove where the tree came from.

**3. The guard leaked within a process: changed.** `main` clears the flag when its command ends, with or without an error, so that it is set only while a stamped command runs; a command of `chain` sets and clears it for itself. The tests start each test with the flag cleared, and one test asserts that it is set while a stamped command runs and cleared after it, also after a command that ended with an error. The pre-specification states the guard as it is: a flag that guards against a slip and not against intent.

**4. A cycle that stops for good inside the closing task: defined, not coded.** The runbook (section 10) and the stop conditions say that such a stop is reported like the first and that a new closing task is written without that cycle. The case needs trainings at the same time; one after another, no cycle is under way when another stops.

**5. The queue does not keep a stop across sessions: stated, not changed.** The pre-specification ("Stop conditions") and the runbook ("After a stop") now say that the people who run the sessions keep the rule and the queue does not, and what a session started all the same would do: a step that stopped for good ends with the same error again, and after predictions on the sample that were not finite the steps that are left are the closing steps for that case. The queue was left as it is on purpose: a session that failed on the host's account (a full disk, a busy GPU) is continued by running the notebook again, and a queue that halted on every failure would need a new task file for each of them. The sheet for the helper says not to start a session after a failure until told.

**6. The queue's notebook "kept with the records": corrected.** The runbook (0d) says that the task file is returned with the records and that the notebook is not part of the repository, because it names the shared store and the people who use it. The pre-specification's list of what is not stamped says the same.

**7. The placeholder without a text: written, with its scope.** The paragraph now gives the comparison (the two stand-in presets, 6 and 60 steps and 12 and 120 steps, equal to the last bit) and says what was not compared: what only the pinned presets reach, that is 128 and 160 training members, the family's mesh, the network at its full size and a GPU.

**8. What the verdict took on trust: changed.** (a) A FAIL counts as complete only when every seed has its record on the sample. (b) The verdict compares the evaluation of the development's members with the manifest and the ledger of its data, refuses if either file is absent, and compares the prediction files as they are with those the evaluation read. Tests cover a lost record, a changed ledger, an absent manifest, and prediction files that the evaluation did not read.

**9. Section 11 against the stop rule: one paragraph.** After a stop for good a cycle whose folder was moved aside is not started again, is left out of the closing task, and its seed gets the record that it has no predictions; the record's reason says "not started", and the verdict document is to say what it stands for. The same is in the stop conditions.

**10. The exports and labels made again: said.** The paragraph says that none of the sixteen files has the SHA-256 of the host's records and that the solves agree with the records to 1e-13.

**11. The A100 hours and the minimum time: said and raised.** The budget says that no epoch of the second cycle was timed on the A100 and that its hours are scaled, and that the factor for the processor steps is by the number of processes, without a timing. The task file's minimum time for the evaluation of the sample is eight hours and for that of the development's members two (it was four and one); the runbook names both.

**12. Runbook wording: corrected** in the three places (the data steps' half hour; the reference to section 10 in section 5; a failed host check is not run again under the same task).

**13. 17d: one sentence** in the runbook's section 4 on what happens if the test by the process number fails: the training goes on until the session ends and resumes like any other. `f2/train.py` is not changed, for the reason given after round 1. By the timing rule the gate's task trains one after another on every accepted GPU, unless a timing of another model is made before the first session, so that `together` is not expected to run in it.

**Changed after both readings, by the owner's decision.** The first reader's point 5 was met by writing the seed into the hashed configuration, with a rule that a stamp whose commit carried another day than the seed was void. On 25 November 2026 at 16:29, before the stamp, the owner dropped that rule: the seed stands whatever day the commit carries. The pre-specification ("Authority", "The sample") and the runbook (0b) say so and say what the dropped rule would have given. The docstring of `f21/stamp_day.py` and the `seed_rule` text of the configuration still state the first rule; no stamped file was changed for this, so that the tests, the host check and the simulation stand as run. Neither reader saw this change.

**Not done, and why**
- Round 1's 10 (d), the host check on the gate's host before the stamp: the timing session was the last one before the stamp, and the owner agreed to run the check as the first step after it. The pre-specification says so and says what a failure there means.
- The second reader did not run the host check, the development's tests or the session simulation, and could not check the two figures of the draw with the seed 20261127. The author ran the first three on the final files (`records/G-F2.1/before_stamp/`); nobody but the author has checked those runs.
- No third reading was made: the changes after round 2 were read by nobody but the author.

---

# The states that were read

Of the 48 stamped files, these differ between a state that was read and the stamp's commit:
- round 1: `f21/__main__.py`, `f21/config.py`, `f21/gate.py`, `f21/smoke.py`, `f21/stamp_day.py`, `f2/evaluate.py`;
- round 2: `f21/__main__.py`, `f21/config.py`, `f21/gate.py`.

The other files that the readers were given (first 16 digits of each SHA-256):

| File | Read in round 1 | Read in round 2 | In the stamp's commit |
|---|---|---|---|
| `docs/PRESPEC_G-F2.1.md` | `947578a2e90f744a` | `b07a173615ac48ec` | filled in at the stamp |
| `RUNBOOK_F21.md` | `5b4caf1a8f212b3e` | `f0d2b8455e61d85b` | `b1e6752ca61f01a4` |
| `tests/test_f21.py` | `0af08d248100ecb7` | `b76071fec1b853ea` | `2b8e6be5e2f01925` |
| `tests/test_f2_dev.py` | `5aa82282efad3263` | `5aa82282efad3263` | `5aa82282efad3263` |
| `probes/f21_recompute/recompute.py` | `a1b83edac91e37f2` | `a1b83edac91e37f2` | `a1b83edac91e37f2` |
| `docs/F2_development_note.md` | `b3724d0087f527f4` | `420dffb257892f6b` | `420dffb257892f6b` |

The changes after round 2 are those of the author's notes on round 2. They were read by nobody but the author, and the tests, the host check and the session simulation were run again on the final files (`records/G-F2.1/before_stamp/`). No value of the gate's configuration was changed after round 2: its hash in the pre-specification is the one the second reader computed.
