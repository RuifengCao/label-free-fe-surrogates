# Independent pre-stamp review of gate G-C2.2: reports as delivered

Verbatim reports of the independent reviewer (a separate agent that did not write the code) to the author, 12 November 2026, in three rounds. The reviewer worked read-only on the working tree, in a scratch folder of its own, and was barred from drawing, solving or training anything of the gate's configuration.

Only this header and the three notes "What the author did" are the author's. In the reports, the paths of the development sandbox are shortened: `<sandbox>` stands for its working folder, in which `wt` was the working tree. Nothing else in them was changed.

The file names and hashes the reports cite are those of the day of the review. `docs/G-C2.2_code.sha256` has the stamped ones.

---

# Round 1 (12 November 2026, about 18:00 GMT)

REVIEW OF GATE G-C2.2 CODE BEFORE THE STAMP (cold review; nothing inside wt was modified)

Reviewed state (sha256 prefixes): c22/__init__.py e3b0c442, __main__.py 8239e885, condense.py c722f56d, config.py 9541e1c6, data.py dd648cbd, evaluate.py 672ea6a1, train.py 6b360c66, tests/test_c22.py ee28a41e. These did not change during the review. Three things did change under me: the draft pre-specification was edited at 17:11 GMT (one sentence in "Changed 2"), joint/probes/c2_dev/ appeared at 17:11 and joint/RUNBOOK_C22.md at 17:27. I read the runbook because the pre-specification's Procedure rests on it; it was not in the listed scope.

Result in one line: no defect found in the seven c22 modules that would crash or invalidate the deciding run or break a clause of the pre-specification; one blocker for stamping the tree as it stands (the runbook calls a file that does not exist), one major procedural risk, and a set of minor defects and ambiguities.

Line numbers refer to the files under <sandbox>/wt/joint/.

1. FINDINGS, MOST SEVERE FIRST

F1. BLOCKER for the stamp as the tree stands (procedure, outside the seven modules). RUNBOOK_C22.md line 53.
- Step 0d runs `gate/joint/c22/smoke.py --repo gate --device cuda --workers 4 --out ...`. There is no c22/smoke.py in the tree (checked 17:35 GMT). The only smoke script is <sandbox>/smoke_c22.py, outside the tree; it has no --repo option, finds the code through BASE/code/joint, and does not record the machine data the runbook says the report holds.
- Consequences: step 0d cannot be carried out, so the run stops at a precondition. Adding the file to c22/ makes test_code_list_holds_the_package_and_c21s_stamped_files fail until CODE in c22/__main__.py (lines 22-28) lists it, so __main__.py and the hash table change, and the new file becomes stamped code that nobody has reviewed.
- Smallest fix: add the script, list it in CODE (or keep it outside c22/, for example joint/smoke_c22.py, and list it only in docs/G-C2.2_code.sha256), rerun the code-list test, and have that one file reviewed.

F2. MAJOR (procedure; the failure itself is suspected, not verified). RUNBOOK_C22.md lines 13 and 51-57; c22/train.py lines 67-68; c2/train.py lines 40-43; c22/data.py lines 74-79.
- Verified by reading: three paths of c22 have never run on the laptop according to the development scripts in probes/c2_dev (grep: no _note, no %Z, no process pool, resume always with map_location=dev): (a) `_note` and the start line print `time.strftime('%Z')`, the first to attempts.log opened without an encoding, the second to a redirected stdout; (b) the spawn pool for labels and evaluation; (c) resume through c2.train._load_state with map_location "cpu".
- The runbook runs the host smoke test after the stamp, so anything it finds forces a second stamp.
- Suspected, not verified (no Windows here): on Windows `%Z` gives the localised zone name. Under -I, PYTHONUTF8 and PYTHONIOENCODING are ignored, so both writes use the ANSI code page. If the display language is Chinese and the code page cannot encode the name (for example 1252), train() raises UnicodeEncodeError at its first line. With an English display language, or code page 936, nothing happens. <sandbox>/laptop_files_sha.txt shows these exact c22 files and dev/smoke_c22.py staged on the laptop at 13:48; I found no report of a run there.
- Checked for (b) and (c): a toy package of the same layout started as `python -I pkg/__main__.py` with a spawn pool works on Linux (children re-run the script as __mp_main__, inherit -I and the parent's sys.path); torch 2.12.1's Optimizer.load_state_dict moves CPU-loaded state to the parameters' device.
- Smallest fix: run the smoke test on the laptop through the queue (same `python -I -u`, same log redirection) before stamping and list it under "What was seen before the stamp". Independently, start Python with `-X utf8` in the runbook's PY, which removes the encoding dependence without touching stamped code.

F3. MINOR. c22/evaluate.py lines 24-29 and 64-70. evaluate() takes any run folder that holds the three prediction files; it never compares history.json's config_sha256, or condense.json's "reading" and "levels_mm", with the configuration.
- Reproduced in scratch: a folder whose history.json carries config_sha256 "000…" is evaluated as "finished" and enters the verdict.
- Scenario: after a second stamp that changes code but not c22/config.py, run folders of the earlier code are accepted by evaluate and by train (which returns "finished"). The runbook requires only that gate/ is new (line 37); G-C2.1's runbook checked that the data and runs folder was fresh.
- Fix: in evaluate, for every seed that is not missing, raise unless history.json's hash equals sha256(cfg) and condense.json's reading and levels equal the configuration's; add to runbook 0a that gate_data, gate_runs and gate_records must not exist.

F4. MINOR. c22/train.py lines 166-172. The checkpoint is written to state.tmp and renamed, with no flush to disk, one generation and no retry.
- Verified by reading: after a forced power-off or system crash within seconds of an epoch end, state.pt may be unreadable; _load_state then raises at every restart. The INCOMPLETE rule taken from G-C2.1 covers "no checkpoint", not "an unreadable one", and a rerun from the start is another realisation on the GPU.
- Suspected, not verified: on Windows the rename raises PermissionError while another process (sync client, indexer, antivirus) holds state.pt. The run then ends with an error and the guard stops the queue. The run resumes, but each occurrence costs an epoch and a report. The development trainer did the same rename every epoch on this laptop without a recorded failure.
- Fix: fsync the temporary file before the rename, keep the previous checkpoint as state.prev.pt and fall back to it, retry the rename a few times on PermissionError; or say in the pre-specification what happens to an unreadable checkpoint.

F5. MINOR. c22/train.py lines 119-126; RUNBOOK_C22.md line 100; pre-specification, "Chosen here". history.json does not record every resume.
- Reproduced in scratch: killed in epoch 3, resumed, killed again before the next checkpoint, resumed: history.json has resumes [2], attempts.log has both. A resume that only writes predictions (history.json already there) is not added either: the returned history had [4], the file [].
- The runbook says "each resume is recorded in the run's history.json". Fix: point both documents at attempts.log (complete), or write the resume to disk when it happens.

F6. MINOR. c22/evaluate.py lines 93-99. The amplitude counts in verdict.json (n, min, max, median, at_bound, not_converged) run over all members of the three sets, 924 pairs a seed, not the 448 judged pairs.
- Reproduced: bound flags set only on a former member and non-convergence only on the tested member give at_bound 2, not_converged 2, n 8 with 4 judged pairs.
- The pre-specification says such amplitudes are "counted" without naming the set. Fix: one entry per set, and name the set in the pre-specification.

F7. MINOR. c22/evaluate.py line 84. The number of members a set must have comes from the manifest, where c2/evaluate.py line 180 took n_eval from the configuration. Nothing asserts 448 pairs.
- Scenario: a manifest with fewer held-out members (generate --limit, or another data folder of the same hash) is summarised and judged without complaint. Through the runbook's commands this does not arise.
- Fix: assert that the split sizes equal n_eval, n_former and the tested count, and that the judged summary has n = n_eval × levels.

F8. MINOR. c22/train.py lines 44-49. A window whose median is zero.
- Checked numerically: gradient 0 gives ratio inf, so every such step is recorded as a burst (written as Infinity in history.json); a non-zero gradient is scaled by 0 and logged as a cap event with ratio inf.
- Scenario: a collapsed encoder, where G-C2.1's seed 0 had no gradient reaching it. The bursts list fills with false entries and the cap erases whatever gradient returns. The second follows the letter of "at most 5 times the median".
- Fix: ratio = 0.0 when both are zero; state in the pre-specification what the cap does at a zero median.

F9. MINOR. c22/train.py lines 221-240; RUNBOOK_C22.md section 6. The base field z0 is not saved. The return package holds z, z_c and a, so the judged fields cannot be recomputed from it; the audit needs state.pt from the laptop. Fix: also write the field at the base level for every member (about 2.6 MB) and return it.

F10. MINOR. Pre-specification, "Changed 2" (the sentence edited at 17:11); c22/condense.py line 27; c22/train.py line 218. The text now says the raw field is one of the evaluated points. The code evaluates z0 + 1·(z − z0), which is not z bit for bit.
- Measured on five coarse members: 170 to 680 of about 1,300 to 1,450 unknowns differ in the last bit; the float32 energy was equal in 400 of 400 trials.
- Pi_raw in condense.json comes from a separate evaluation of z, so Pi_condensed ≤ Pi_raw is observed, not guaranteed. The test and the smoke check allow 1e-6.
- Fix: word it as "the first evaluated point is the raw field up to float32 rounding", or use z itself where a equals 1 in vg and in predict.

F11. MINOR. tests/test_c22.py, behaviour not tested or tested vacuously.
- Bursts are never recorded in any test. My rerun of the training test's configuration gives cap events at steps 5 to 8 with ratios 0.593 to 0.963 and no burst, so line 269's `all(r > 1.0 …)` and line 277's comparison of the burst lists are vacuous.
- Line 268 asserts the first capped step is at least 4; it is 5. The boundary "window + 1" is pinned only by my scratch check.
- For c22.train there is no test of a non-finite loss, non-finite predictions, a kill between the last checkpoint and history.json, a kill during the predictions, or a folder of another configuration. All behaved correctly in scratch runs; test_c2.py covers c2.train only.
- Nothing tests that the cap precedes the global clipping or touches only the encoder inside train().
- evaluate: no test of a judged member whose metrics fail (correct in scratch: that seed infinite, verdict from the other two), of infinite pairs, or of the pair count.
- condense: no test of the lower bound, the evaluation budget or the not-converged flag.
- test_spawned_workers… does not assert that spawn was used; the entry point is never started as a process (the command-line test calls main() in-process with a patched configuration).
- test_the_clamped_unknowns… rebuilds the mask itself; a wrong mask in predict() would pass, since outputs are checked only for contact unknowns ≥ 0 and fixed unknowns = 0.

F12. NOTES on the code.
- c22/train.py line 143 against lines 149 and 151: the non-finite message counts steps from 0, cap events and bursts from 1.
- c22/train.py lines 164 to 172: the epoch line is printed before the checkpoint is written. Saving first would close the roughly one-second window in which a kill discards an epoch whose loss has already been shown. The steps lost at a pause leave no record.
- The seed refusals (c22/data.py lines 26-27, c22/train.py lines 61-62), the manifest check in evaluate (line 49) and the base-hash check (c22/config.py line 36) are assert statements and vanish under python -O. The runbook's start has no -O, and -I ignores PYTHONOPTIMIZE.
- c22/__main__.py line 60: on Windows the written configuration file has CRLF line ends, so the file must not be hashed or compared byte for byte. The printed hash does not depend on it.
- multiprocessing.Pool waits forever if a worker process is killed by the system (known behaviour, not reproduced here); a stalled evaluation would look like a slow one.

F13. NOTES on the pre-specification.
- "A FAIL decided by a seed that stopped or collapsed": "collapsed" has no definition, and c22.train has no collapse record (the development trainer had one).
- The tolerance of the amplitude iteration, |dΠ/da| ≤ 1e-4 Π, is in the configuration and not in the text. Because it is relative to Π, a mock energy with a large constant part stops at a = 1 with the minimiser at 1.3. On the real energy of coarse members the result matched a 501-point scan.
- "Seeds 0 to 4 were used before the stamp": the test suite and the smoke script train small models with seeds 5, 6 and 7 on a reduced configuration (other members, another model). Worth one line under "What was seen".
- "Why the condensed reading" cites 44% and 5.0% at 8 mm "(below)"; the figures are not below, they are in probes/c2_dev/README.md section 10.
- Where labels and evaluation may run is not said; "The machine" speaks of the three runs only.

F14. NOTES on the runbook and the commit (outside the listed scope).
- The label and evaluation commands start 16 workers with no limit on BLAS threads; G-C2.1's runbook set OMP_NUM_THREADS, MKL_NUM_THREADS and OPENBLAS_NUM_THREADS to 1. Results are not affected, the time may be.
- Line 37: git archive applies line-ending conversion if the operator's clone has core.autocrlf set; step 0b catches it.
- .gitignore line 8 (`runs/`) ignores joint/probes/c2_dev/records/runs/, which the development README cites (for example records/runs/L3_recipe_s0_e200). A plain git add leaves these out; earlier returns under records/…/runs/ are tracked, so they were added with -f.

2. CHECKED AND FOUND CORRECT

Recipe and training loop
- AdamW gets betas (0.9, 0.99) from the configuration; everything else in the loop equals c2.train.train (diffed line by line): loss, sampling, order, clipping at 1.0, schedule, 200 × 512 steps, the non-finite stop.
- The cap runs after backward and before clip_grad_norm_, on nets[0] (the encoder of c2.model.build), over all its parameters; the window receives the unscaled norm after the test.
- At the configured window, run numerically: a spike at step 256 is untouched, a spike at step 257 is scaled to exactly 5 times the median of the previous 256 unscaled norms.
- The development trainer (probes/c2_dev/dev/train_dev.py) has the same cap, order and window logic.
- Recorded: epoch losses, cap events with ratios, bursts with ratio strictly above 10.

Checkpoint and resume
- Saved and restored: the three networks, optimiser, schedule, numpy generator, torch CPU generator, window, epoch, step, history. Checkpoints fall only on epoch ends, so no place within an epoch needs saving.
- No CUDA generator is needed: the encoder has no dropout (src/fejepa/models/fejepa.py lines 146-195), and the sampling uses the numpy generator only.
- Scratch runs on the tests' small configuration, CPU: a kill in mid-epoch followed by a rerun ends with the same weights bit for bit, the same cap events, losses, window and predictions.
- A kill after the last checkpoint and before history.json: the rerun writes history and predictions.
- A kill during the predictions: the rerun writes all three files, identical to an uninterrupted run.
- A non-finite loss and non-finite predictions are final; a rerun returns without loading members, and nothing is written for non-finite predictions.
- A history.json or state.pt of another configuration is refused (by reading).

Condensed reading
- Base level 0.1 mm (the training D_min), bounds 0.5 and 3, 12 evaluations, float32 training energy with the configured bubble steps, all from the configuration.
- The clamp mask is the contact unknowns; fixed unknowns stay zero; the amplitude never leaves the bounds; the evaluated point of lowest energy is returned; a field's result does not depend on the others in the batch.
- Mock energies: interior minima found, both bounds flagged, mixed batches right, the evaluation budget respected.
- Real energy of coarse members: the result agrees with a 501-point scan within 2e-7 relative in energy.
- c22/condense.py equals the development file but for its docstring; predict() mirrors dev/evalcond.py, which the full-length development reading used with 12 evaluations.

Leakage
- train, predict and condense read exports only (`_prepare(..., labels=False)`); no label file is opened outside the evaluation and the label check.
- Training members are the manifest's split "train" and must number n_train; held-out and tested members cannot enter.
- No file in the sandbox outside c22/config.py, the pre-specification, the runbook and the design notes mentions 20261113; the development records show training seeds 0, 1, 3 and 4 only.

Data
- members(): 512 from 20261106, 64 from 20261113 as "eval", 64 from 20261107 as "former", four tested; the held-out seed is refused if it is in the seen list or equals the training or former seed.
- generate, label and check_labels are c2's with the stated differences (diffed); a labelled training member fails the check; the label command refuses the training split.

Evaluation and criteria
- Judged: the condensed reading on split "eval"; per-seed median and 90th percentile by c2's _summary and _quantile (np.quantile, linear, infinities kept); median over the three seeds; thresholds as "at most".
- A stopped seed counts as infinite; a missing seed gives INCOMPLETE with readings and amplitudes withheld; the raw reading is reported with its own C1 and C2; a failure in a former member leaves the verdict untouched (scratch run).
- One worker and spawned workers give equal verdicts (test).

Configuration, hashes, entry point
- The configuration's values equal the pre-specification (printed from write-config).
- write-config through `python -I -B` from another folder prints 27 code hashes and 6 repository checks; the draft configuration hash is ef5376a4d6c3cc98….
- CODE covers every c2, c22 and fejoint module that c22 imports (import trace); `sha256sum -c docs/G-C2.1_code.sha256` passes.
- train and evaluate refuse a wrong --config-sha before touching data (by reading and unit tests).
- All c22 files and the test file are ASCII with LF and parse under the 3.10 and 3.12 grammars.

Tests
- All 14 tests of tests/test_c22.py pass, each run singly (Linux, CPU, Python 3.13.18, torch 2.12.1+cu130, numpy 2.5.3).

3. NOT CHECKED

- Anything on Windows or CUDA: no execution was possible here. That covers the `%Z` behaviour, file replacement under Windows, the spawn pool on Windows, GPU memory and CUDA resume.
- The real configuration's generate, label and train were not run, by rule. One command of mine that would have called the real train and label with a wrong hash and split, to see the refusals, was refused by the permission system; I did not retry it.
- c22/smoke.py (absent), docs/G-C2.2_code.sha256, docs/G-C2.2_stamped_code and the final docs/PRESPEC_G-C2.2.md (not in the tree).
- The laptop's queue and guard scripts; I read only the pause, resume and hold copies in <sandbox>/pausetool.
- The content of probes/c2_dev beyond comparing its trainer and condense code with c22, and the figures the pre-specification quotes from it, except the seed list, the collapse steps and the full-length reading.
- The internals of the stamped c2 and fejoint code beyond the interfaces c22 uses.
- Behaviour at full scale (5 mm mesh, the 256-wide model, 102,400 steps) and evaluation time on the laptop.
- The suite in one run; the laptop's Python 3.12 and numpy 2.4.6 at run time.
- Whether seed 20261113 was drawn anywhere outside this sandbox.

Scratch scripts and outputs are in <sandbox>/review_scratch. Nothing in this report comes from memory, and there is nothing new for memory beyond these findings.

---

# What the author did after round 1

- F1: `c22/smoke.py` added to the package and to its code list; it refuses a folder that is not empty and deletes nothing; a test runs it on a CPU.
- F2: `c22/train.py` writes no zone name: its own note writer and its start line use an ISO time with a numeric offset, in ASCII. The host check is run on the laptop through the queue before the stamp. `-X utf8` was not added.
- F3: the evaluation refuses a run folder whose history does not carry the configuration's hash, and a finished run with another reading or other levels; the runbook requires fresh folders.
- F4: the checkpoint is flushed to the disk before it is moved; moves are retried on PermissionError; no second generation is kept; the pre-specification says what happens to an unreadable checkpoint.
- F5: the documents point at `attempts.log`.
- F6: amplitude counts for each set. F7: the set sizes and the pair counts are checked against the configuration.
- F8: a ratio of 0 when gradient and median are both zero; the pre-specification states what the cap does at a zero median.
- F9: `preds_base.npz` is written, required and returned; a test computes the stored condensed fields again from the stored files.
- F10, F13: the pre-specification's wording. F11: tests added or made to bite. F12: the points taken, except the base-hash assertion of `c22/config.py`, which stays an assertion.
- F14: spawned workers get one linear-algebra thread through the environment; `git archive` with `core.autocrlf=false`; the folder `records/runs` of `probes/c2_dev` renamed `records/gpu`.

---

# Round 2 (12 November 2026, about 18:50 GMT)

ROUND 2 REVIEW OF GATE G-C2.2 (cold review of the changes; nothing inside wt was modified)

Result in one line: every round-1 finding is resolved except F4 and F11, which are partly resolved; the changes introduce no defect that would crash or invalidate the deciding run; three minor findings and some notes remain, none a blocker.

Reviewed state (sha256 prefixes), unchanged while I worked (file times 18:05 to 18:09 GMT): c22/__main__.py 2c692935, config.py 9541e1c6 and condense.py c722f56d (both as in round 1), data.py 0aabd4e8, evaluate.py 9e9388f9, smoke.py 715e42c9, train.py 8575047a, tests/test_c22.py 492845cf, RUNBOOK_C22.md 25891d50, pre-specification draft 0.3 aa447310. Line numbers refer to these files.

A. STATUS OF F1 TO F14

- F1 resolved. c22/smoke.py exists, is in CODE (28 entries), and the code-list test passes. I ran it as the main script in isolated mode with the pool forced to spawn (scratch launcher, CPU, 2 workers): workers re-ran smoke.py as __mp_main__, labels, training with resume and both evaluations completed, last line "smoke test of c22 passed". A second start on the same folder exits 1 and leaves it untouched. No deletion call exists in c22.
- F2 resolved in the code (by reading and running). c22 writes no zone name any more: _now() gives an ISO time with numeric offset and attempts.log is opened as ASCII. Every other text c22 writes is JSON with ASCII escapes or a relative path from the command line, so -X utf8 is not needed. The same time expression ran on the laptop in the development trainer. The host check before the stamp is a placeholder in the pre-specification (line 91); I cannot verify it.
- F3 resolved. evaluate refuses a run folder of another configuration hash, another reading or other levels (tests, and a scratch run for the levels). The runbook's "none of the four folders exists" (line 12) is a sentence with no command behind it.
- F4 partly resolved. The checkpoint is flushed and fsynced before the move; checkpoint and prediction moves are retried; the pre-specification and runbook now cover an unreadable checkpoint consistently. Other moves are not retried: see R2.
- F5 resolved. Pre-specification line 61 and runbook line 103 point at attempts.log.
- F6 resolved. Amplitude counts are per set (scratch run: flags on a former and on a tested member appear only in their sets).
- F7 resolved. Set sizes are checked against the configuration before any work, the pair count after each summary.
- F8 resolved. Ratio 0.0 when gradient and median are both zero; a non-zero gradient against a zero median is scaled to zero and recorded with an infinite ratio; pre-specification line 28 says so; the unit test covers both.
- F9 resolved. preds_base.npz is written, required by predictions_written and run_status, and copied by the runbook. On CPU the stored condensed fields equal the recomputation from the stored base and raw fields and amplitudes bit for bit (13,690 of 13,690 values in the smoke run, 10,910 of 10,910 in the training test's run).
- F10 resolved. Line 32 of the pre-specification matches the code.
- F11 partly resolved. Now tested and not vacuous: bursts (2 of 4 capped steps), the cap before the global clipping and on the encoder object, the first capped step at window + 1, a non-finite loss as final, the retry, evaluate's refusals, that spawn is used and the thread variables set, the entry point as a process, condense's bounds, budget and not-converged flag, the host check on CPU, and that the base file is required. Still untested: see R1, R3 and the list under R3.
- F12 resolved. The non-finite message counts from 1; the checkpoint is written before the epoch line; seed refusals and evaluate's manifest check raise RuntimeError; write-config writes ASCII with LF.
- F13 resolved on all five points (lines 32, 45, 90, 187, 206; README section 10 is the full-length run).
- F14 resolved. A spawned worker sees the three thread variables at 1 and its two BLAS pools have one thread (scratch probe); the parent's loaded pools are unchanged. git archive runs with core.autocrlf=false. records/gpu is not ignored by git and the README no longer cites records/runs.

1. NEW FINDINGS, MOST SEVERE FIRST

R1. MINOR. tests/test_c22.py lines 341-343. The new "another configuration" assertion of test_train_resume_and_predict never reaches the run folder.
- train() checks the manifest first (c22/train.py line 99), so the call with the other configuration and the first configuration's data raises "the data were generated under another configuration", which also matches the pattern. Reproduced in scratch: that message, and no run folder created.
- The two refusals it was meant to pin (train.py lines 108-109 and 148-149) do work: with data of the other configuration, a finished folder gives "holds a run of another configuration" and a folder with only state.pt gives "belongs to another configuration".
- Fix: generate data under the other configuration in the test and call train with it on the first run's folder; for the second case use a copy without history.json and prediction files.

R2. MINOR (the Windows behaviour is suspected, not verified). The rest of F4: moves that are not retried.
- c22/evaluate.py lines 142-144 (verdict.json), c22/data.py line 67 (instance files), and through c2's writers the ledger (data.py line 109), the manifest (line 72) and history.json (train.py lines 162, 165, 218, 221).
- Scenario: a scanner holds verdict.tmp or an existing verdict.json for a moment at the end of an evaluation of 1.5 to 6 h that does not resume. The command ends with an error and no summary line; the complete verdict is left in verdict.tmp. The other cases cost only a rerun that resumes.
- Fix: use _replace for verdict.json in evaluate. Optionally give c22.data.label its own ledger writer with _replace.

R3. MINOR. The clamp in predict() (c22/train.py line 259) is exercised by no test and not by the smoke.
- In the training test's run all eight amplitudes are 0.5 and no contact value is below zero before the clamp (0 of 10,910; smoke 0 of 13,690). Lines 329 and 332-335 of the test would pass without the clamp, though the comment at 330-331 says it is checked. The recomputation does pin the other direction: non-contact unknowns are not clamped.
- A missing clamp would not be silent in the real run (the evaluation's metrics assert contact unknowns ≥ 0, so the seed would count as infinite). By reading, the line is right and equals the development code.
- Fix: one check on fields built so that a contact unknown goes negative on the ray with a > 1.
- Also still untested from F11: non-finite predictions in c22.train, kills after the last checkpoint and during the predictions, a judged member whose metrics fail, infinite pairs, check_labels' "extra", and the pair-count and levels refusals. I ran all but the pair-count refusal, infinite pairs and "extra" in scratch against the new code; each behaved correctly.

R4. NOTES on smoke.py and the runbook.
- RUNBOOK line 118: "no new output for an hour" is always true for the evaluation, which prints nothing before its last line. Only the processors' load shows progress.
- RUNBOOK line 58 against smoke.py lines 70-77: the "in use" figure is total minus free after this process has started CUDA, so it includes the smoke's own context (suspected a few hundred MiB; not verifiable here). The runbook reads it as "in use by other programs".
- RUNBOOK line 12: add a command that shows the four folders are absent.
- smoke.py "passed" rests on three asserts (lines 85, 91, 122) and on no exception. energy_never_higher, same_cap_steps and the differences are reported only.
- The report holds "verdict": "FAIL" for the untrained small model (C1 value 115 in my run). Worth one line in 0d that this means nothing.
- Line 122 compares dictionaries, so any not-a-number metric would make it false. None occurred.
- The smoke report does not record the three thread variables or the label solver (pardiso or scipy). A thread variable already set in the queue's environment is kept (c22/data.py line 89), so runbook line 91 holds only if none is set.
- Pre-specification line 91: name the commit or hashes the host check ran with. The files staged on the laptop at 13:48 were round 1's.

R5. NOTES on the code and tests.
- check_run raises FileNotFoundError, not the refusal message, for a folder with the four prediction files and no history.json (scratch). train() cannot produce such a folder.
- train()'s docstring (lines 89-90) lists the files without preds_base.npz and attempts.log. The module text on `resumes` (lines 16-17) does not cover a resume that only writes predictions, which is recorded only if history.json did not exist yet.
- Asserts that remain: train.py line 122, config.py line 36, evaluate.py line 53, data.py line 38. Harmless without -O.
- test_spawned_workers… leaves thread variables set to 1 in the pytest process when they were absent before (delenv with raising=False records nothing to restore). No effect on later tests that I can see.
- The second half of test_a_non_finite_loss_… tests _replace alone; that the checkpoint goes through it is by reading (line 209).

2. CHECKED AND FOUND CORRECT

c22/train.py
- Checkpoint: written through an open file, flushed, fsynced, closed, then moved; the epoch line follows.
- Scratch runs on CPU: a kill in mid-epoch then a rerun gives the same weights bit for bit, the same cap events, bursts, losses, window and three prediction files. A kill after the last checkpoint and before history.json is completed by the rerun.
- Prediction files: condense.json is written last. Killed before each of the four moves in turn, predictions_written is False and run_status "missing" every time, and the rerun completes with identical files.
- A base field that alone is not finite gives "non-finite predictions" with nothing written.
- _replace retries PermissionError only, which is what Windows raises for access denied and sharing violations, and raises after the last try (test).
- attempts.log lines are ISO times with offset, ASCII.

c22/evaluate.py
- check_run runs for finished and stopped runs before any metric work; the reading and levels survive the JSON round trip.
- A judged member whose condensed field fails the metrics still gives that seed infinite and the verdict from the other two; the pair check does not interfere.
- Importing c22.evaluate (which now imports c22.train) does not import torch or fejepa.

c22/data.py pool and threads
- The variables are set in the parent before the pool is made and only under spawn; a set variable is kept (test).
- Reference solves of two coarse members are bit-identical under 1, 2, 8, 24 and unset OpenBLAS threads, and the evaluation of the smoke's predictions gives the same verdict under 24 threads and 1 (Linux, OpenBLAS 0.3.34). So the smoke's comparison of workers against the single process, and the spawn test's bitwise comparison, did not depend on threads here.

c22/smoke.py
- reduced() differs from the gate's configuration only in seeds 7, 8, 101, sizes, mesh, levels, tested members, model, cap settings, epochs and seeds [5]; its hash is 819a8445…, not the gate's.
- No torch import at module level, so spawned workers stay light; the repository files are verified inside train(); the CLI options match the runbook's command.

Documents against code, where they changed
- Pre-specification lines 28, 32, 61, 110, 144, 152, 172, 187, 206 and runbook lines 35, 54-57, 68, 91, 103, 106, 117, 127 agree with the code and with each other, apart from the notes in R4.
- The configuration is unchanged and its texts still describe the code.

Tests and hashes
- All 19 tests of tests/test_c22.py pass, each run singly (Linux, CPU, Python 3.13.18, torch 2.12.1+cu130, numpy 2.5.3).
- `sha256sum -c docs/G-C2.1_code.sha256` passes.

What I executed, for the pre-specification's sentence about this review
- Round 1: the tests' small configuration (family seeds 7, 8, 101, coarse mesh; training seed 5), read-only use of an earlier smoke run's data, mock energies, a toy package, and write-config of the gate's configuration.
- Round 2: the same small configuration, again with training seed 5, and a variant of it with beta2 0.999 that was generated and labelled but never trained (both calls were refused before a step); c22/smoke.py's reduced configuration once (training seed 5, spawned workers); two coarse members solved again under different thread counts; two evaluations of that smoke run's predictions.
- Nothing of seed 20261113 and no run of the gate's configuration.

3. NOT CHECKED

- Anything on Windows or CUDA: os.fsync and the retried move on NTFS, torch.cuda.mem_get_info, the size of the CUDA context, spawn on Windows, the laptop's BLAS under 24 threads, CUDA resume.
- The host check on the laptop, before the stamp or in step 0d, and the queue and guard scripts.
- docs/G-C2.2_code.sha256, the stamped copy, the final docs/PRESPEC_G-C2.2.md and the review file it cites (not in the tree).
- The gate's entry point with a spawn pool as a real process: write-config and the refusal run as processes, and the pool runs through smoke.py, but label and evaluate through c22/__main__.py first run with workers in section 3.
- probes/c2_dev beyond the rename and the section number.
- The suite in one run, full-scale behaviour, and Python 3.12 with numpy 2.4.6 at run time.

Scratch for this round is in <sandbox>/review_scratch/r2. Nothing in this report comes from memory, and there is nothing new for memory beyond these findings.

---

# What the author did after round 2

- R1: the test reaches each of the three refusals.
- R2: one retried move and one JSON writer in `c22/data.py`, used for every file the package writes itself, `verdict.json` included.
- R3: a test of the clamp in the prediction step, on fields built so that the ray goes negative.
- R4: the runbook says what the host check's report must show, how the in-use figure is counted, and that the evaluation is silent; `c22/smoke.py` records the label solver and the thread variables.
- R5: a refusal in place of a missing-file error; docstrings; the spawn test restores the environment. The remaining assertions were left.
- Not done: tests of non-finite predictions inside the training module, of kills after the last checkpoint and during the predictions, of a judged member whose metrics fail, of infinite pairs, of the label check's "extra" and of the pair-count refusal.

---

# Round 3 (12 November 2026, about 19:00 GMT)

ROUND 3 REVIEW OF GATE G-C2.2 (the small diff after round 2; nothing inside wt was modified)

Result in one line: R1 to R5 are resolved, I found no defect in the changed lines, and the runbook's changed lines agree with the code; two notes follow.

Reviewed state (sha256 prefixes): c22/data.py 5f145685, train.py 37446aa4, evaluate.py 329e39a2, smoke.py 604ff851, tests/test_c22.py d5c8ebc6 (20 tests), RUNBOOK_C22.md 5b7b94d1. __main__.py, config.py, condense.py and the pre-specification draft are as in round 2.

1. FINDINGS

None of severity minor or above. Two notes:

N1. NOTE. c22/smoke.py line 75 against fejoint/linsolve.py lines 19-20 and 45-53.
- `label_solver` records which backend is loaded, not which one the host check used. The reduced configuration's systems are below PARDISO_MIN = 3000 unknowns (1,306 to 1,453 in my round-2 smoke run), so they go to SuperLU either way.
- A report that says "pardiso" therefore does not show that PARDISO ran on the host; its first use would be the gate's labels in section 3.
- linsolve is already imported by every c22 process through c2.data, so the new call loads nothing new.
- Smallest fix: one sentence in runbook 0d saying what the field means.

N2. NOTE. The label files are still moved without retry.
- c2.data._label_one (stamped) writes them in the worker with a plain move. A failure there ends the label command, and the rerun resumes.
- So "c2's writers are no longer used by c22" is true of the two JSON writers, not of this one.
- Also cosmetic: three blank lines are left in c22/train.py (lines 47-49) where _replace was.

2. CHECKED

R1 to R5, by reading
- R1 resolved. The test now raises in turn on the data's configuration (fresh folder), on a finished run's history with data generated under the other configuration, and on a checkpoint alone; the three patterns match the three messages in train().
- R2 resolved for everything c22 writes itself. _replace and _write_json live in c22/data.py and serve the instance files, manifest, ledger, checkpoint, history.json, the four prediction files and verdict.json. The only bare os.replace left in c22 is inside _replace.
- R2, the test of the order: train's names _replace and _write_json are patched, and the real _write_json calls c22.data's own _replace, so each move is recorded once. The expected list is four checkpoints, the history, then preds, preds_condensed, preds_base and condense.json last.
- R3 resolved. The new test patches c22.train.field and c22.condense.condense (predict imports condense at call time, so the patch takes effect), builds a ray that gives -0.1 on every unknown, and asserts exactly 0 on the contact unknowns and -0.1 elsewhere. It would fail without the clamp and with a wider mask. I ran this one test: passed in 6 s.
- R4 resolved. See the runbook below.
- R5 resolved. check_run raises the refusal when history.json is absent, with a test. The docstrings of train.py are accurate. The spawn test's setenv-then-delenv records the original value, so pytest restores each variable; this still works after pool() sets it and after the later setenv to "3".

Changed lines
- Import order: c22.data imports no other c22 module at module level; c22.train imports c22.data; c22.evaluate imports both. No cycle. Each of the three, imported first in a fresh interpreter, loads without torch or fejepa.
- _write_json is c2's two writers with the move replaced: same json.dumps(obj, indent=1), same write_text, same temporary names (manifest.tmp, ledger.tmp, history.tmp, verdict.tmp). The bytes are the same.
- No reference to _write_history or _write_json_atomic remains in c22 or its tests.
- Temporary names in a run folder do not collide (state.tmp, history.tmp, condense.tmp, three *.npz.tmp).
- train.py still needs os (fsync) and time (perf_counter). The retry test still works, since it patches the os module that c22.data's _replace uses.
- smoke.py: thread_variables_at_start is read before any pool. thread_variables_of_the_workers is the parent's environment after the label pool, which is what spawned workers were started with; under fork it shows the unchanged environment, and the CPU test checks only the keys.
- All c22 files and the test file parse under the 3.12 grammar, are ASCII with LF; `sha256sum -c docs/G-C2.1_code.sha256` passes.

Runbook against code
- The `ls -d … | wc -l` line prints 0 when none of the four folders exists.
- The report keys it names exist with those names: check_labels.ok, evaluate.same_with_workers, condense.energy_never_higher, machine.thread_variables_of_the_workers, machine.gpu_memory_in_use_MiB, evaluate.verdict, resume.
- "1 three times" matches the strings pool() sets when none is preset. "16 steps" is 4 members × 4 epochs.
- The label line now states the preset-variable exception. The evaluation does print nothing before its last line.

3. NOT CHECKED

- By your request I ran almost nothing: one new test and three one-second imports. The other 19 tests were not rerun against this state; that the changed tests pass is by reading.
- Anything on Windows or CUDA, the host check on the laptop, the queue scripts, and the documents not yet in the tree, as before.
- The items you list as not done remain untested in the suite. My round-2 scratch runs of them were against the round-2 code; the lines they exercise changed only in which writer is called.

Nothing in this report comes from memory, and there is nothing new for memory.

---

# What the author did after round 3

- N1: one sentence in the runbook's step 0d on what `machine.label_solver` means.
- N2: nothing for the label files, which the stamped `c2/data.py` writes and whose command resumes; the three blank lines in `c22/train.py` were made two.
- At the stamp, 13 November 2026:
  - The host check (`c22/smoke.py`) ran on the laptop with the code as stamped, from 04:24 to 04:27 GMT, and passed; its report and log are in `records/c22/host_check/`. It covers what the review could not: the pool of spawned worker processes, the resume on the GPU, and the writing and moving of files on Windows.
  - No file of `c22/` and no test changed after this review, apart from the blank line of N2.
  - `docs/PRESPEC_G-C2.2.md` received the values of the stamp, the full-length development run of seed 1, the result of the host check, and the second full-length model in its expected outcome and in its reason for the condensed reading; its sentence on a resumed run now names the host check.
  - `RUNBOOK_C22.md` received the configuration hash, the tag of the stamp (`prereg-c22`) from which the tree is taken, the laptop's number of logical processors as the host check recorded it (32, where the draft said 24), and the loss level of the two full-length development runs.
  - `probes/c2_dev/README.md` received the full-length run of seed 1, and `README.md` the lines of this gate. Neither was under review.
