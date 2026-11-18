# Independent pre-stamp review of gate G-C2.3: reports as delivered

Reports of the independent reviewer (a separate agent that wrote none of the reviewed files) to the author, 18 November 2026, in three rounds. The reviewer worked on copies of the working tree in a folder of its own, with scripts of its own, and was barred from drawing, exporting or solving any member of the gate's held-out sample: every check of the reviewer that needed members used the family seeds 7, 8, 101 and 102, which were used before G-C2.1's stamp.

Reviewed: the gate's new code (`c23/`), `tests/test_c23.py`, the draft of `docs/PRESPEC_G-C2.3.md`, `RUNBOOK_C23.md`, the exploratory readings that the pre-specification cites (`probes/c2_selfcheck/`), the probes run on the host before the stamp, and the working tools outside the repository that write the queue's jobs and the stamp. The code stamped for G-C2.1 and G-C2.2 was out of scope, except where the new code uses it.

Notes of the author for this file:
- Only this header, the sections "What the author did after round ...", the section "What changed between draft 0.5 and the stamped text", the list "What drafts 0.2 to 0.5 of the pre-specification add to draft 0.1" and the section "The reviewed states" are the author's. The reviewer returned each report as a message; its text is given here without a change, with two exceptions. Paths of the development sandbox are shortened: `<review>` stands for the reviewer's folder. And where a report quotes a name that must not appear in the repository's prose, in order to say that it does not occur, the name is replaced by `<a name that the brief lists under H>`; H is the brief's list of what must not be public.
- In the reports, `tree/` is the state that round 1 reviewed (the pre-specification's draft 0.2), `tree2/` the state that round 2 reviewed (draft 0.3) and `tree3/` the state that round 3 reviewed (draft 0.4). None of these states was pushed. The line numbers, file hashes and configuration hashes in the reports are those of the reviewed states; `docs/G-C2.3_code.sha256` and the pre-specification have the stamped ones.
- `scratch/` is the reviewer's working folder on the development machine and is not kept in the repository. `gate_prep/`, `gate_prep2/` and `gate_prep3/` held the working tools; the job generator goes into the return package of the run (`RUNBOOK_C23.md`, section 9). `draft01/` held draft 0.1 of the pre-specification and the points of the author's note of 03:52 in English.
- "The owner" is the owner of the repository, who decides what is run; "the author" wrote the reviewed files.

---

# Round 1 (18 November 2026, delivered at about 05:50 GMT)

# Independent review of gate G-C2.3 before its stamp: round 1

18 November 2026. Reviewer: an agent that wrote none of the reviewed files and had no earlier context.

**How to read this report**
- All paths are relative to the review folder of the brief. Files of the package are named from `tree/joint/`: `c23/evaluate.py` is `tree/joint/c23/evaluate.py`. My scripts and outputs are in `scratch/`; they hold absolute paths of this sandbox and are not meant for the repository.
- "Executed" means I ran something here and give the command or script and its output. "Read" means I only read the code or the text.
- Every check that needed members used family seeds 7, 8, 101 and 102. My scripts wrap `c2.family.sample` so that any other family seed raises before a draw (`scratch/guard_common.py`). With the real configuration I only built dictionaries (`config()`, `write-config`). The pytest runs call `c23.data.members` on a configuration that holds the real seed (finding 13d); I had read `c23/data.py` first: the refusal (lines 29 to 32) comes before the first call of `sample` (line 33).
- The reduced run that most checks use was made by `scratch/stage_base.py` (three label-free base runs of two epochs) and `scratch/stage_cli.py`, which replaces `c23.config.config` by the host check's reduced configuration and calls `main(argv)` of `c23/__main__.py`.
- Two of my scripts stopped half-way on errors of my own (`scen1.py`, `scen3.py`); the scenarios after the error were run from `scen2.py` and `scen4.py`.

**Result in short.** No BLOCKING finding: on the reduced configuration every command of the runbook ran through the real command line, in the runbook's order, on a processor, and the tests pass. Six findings should be repaired before the stamp (1 to 6). Findings 1 and 3 are about the text and need the owner; 2 and 4 are small changes of code; 5 is a check missing before the sample is drawn; 6 is a string that must not be published. Then seven MINOR findings (7 to 13) and six NOTES (14 to 19).

## 1. Findings

### 1. SHOULD FIX. The text says no judged level lies beyond the labelled range; the judged level 0.5 mm does, and it is the level where the supervised arm was weakest before

**Where.** `docs/PRESPEC_G-C2.3.md` line 30 ("so that no judged level lies beyond the labelled range"); `c23/config.py` line 44; the judged levels are in `c2/config.py` line 62.

**What is wrong.** The labels are at 0.75, 1.5, 2.5, 3.5, 5, 7 and 8 mm. The judged levels are 0.5, 1, 2, 3, 4, 6 and 8 mm. 0.5 mm is below the smallest labelled level, so 64 of the 448 judged pairs of part 2 are an extrapolation for the supervised arm. The label-free arm is trained on levels from 0.1 mm (`c2/config.py` lines 84 to 86). The condensed reading, the judged one for both arms, also uses each network's field at 0.1 mm as its base (`c22/config.py` line 70), again outside the supervised arm's labelled range. The sentence of line 30 is false at the lower end, and neither "What the gate does not show" nor the wording of part 2 mentions the asymmetry.

**Why it matters.** G-C2.1's supervised arm had the same lower end, and its record is listed under "What was seen". There 0.5 mm was that arm's worst level, and it weighed more on the tail than 8 mm, the level for which G-C2.3 adds labels:

```
$ python3 -I scratch/g21_supervised_levels.py      (reads records/c2/return/verdict.json)
supervised_64 seed 0: median by level (%) [19.4, 13.1, 8.4, 5.9, 3.1, 5.3, 8.3] | pairs at or above the run's 90th percentile, by level {0.5: 17, 1: 12, 2: 2, 3: 0, 4: 0, 6: 4, 8: 10} | p90 with and without the 0.5 mm level: 0.2900, 0.2371
supervised_64 seed 1: median by level (%) [10.8, 9.3, 6.8, 6.2, 3.7, 4.2, 6.4] | ... {0.5: 16, 1: 7, 2: 2, 3: 1, 4: 1, 6: 5, 8: 13} | p90 with and without the 0.5 mm level: 0.2061, 0.1736
supervised_64 seed 2: median by level (%) [8.4, 7.5, 6.5, 3.9, 2.7, 4.3, 7.7] | ... {0.5: 17, 1: 7, 2: 3, 3: 2, 4: 0, 6: 5, 8: 11} | p90 with and without the 0.5 mm level: 0.1606, 0.1461
```

One of the two ratios that fix the wording of part 2 is a ratio of 90th percentiles. The design repairs the upper end of the labelled range and leaves the lower end, where the earlier supervised arm lost most. A reader who checks the levels will call the comparison unfair to the supervised arm, and the text hands him the sentence to quote. I cannot say how large the effect will be with 512 labelled members; 1 mm, inside the range, was also poor in G-C2.1.

**Repair.** The owner confirmed "seven levels, with 8 mm", so this goes back to the owner. Either (a) label 0.5 mm as well (512 more solves, or 0.5 in place of 0.75), or (b) keep the levels and say so: correct line 30; add to "What the gate does not show" and to the fixed wording of part 2 that one of the seven judged levels, and the base level of the condensed reading, lie below the labelled range; and name the per-level medians of both arms under "Reported, not judged", so that reading them is not a choice made after the results.

### 2. SHOULD FIX. When the identity values cannot be computed, the verdict says NOT EVALUATED and goes on to judge part 1 and part 2

**Where.** `c23/evaluate.py` lines 331 to 335 (identity), 338 to 346 (part 1), 352 to 362 (part 2). Text: `docs/PRESPEC_G-C2.3.md` line 118.

**What is wrong.** The text: the judged values on G-C2.2's fresh members "must equal those of G-C2.2's verdict within 0.0001. If they do not, the verdict is INVALID and neither part is evaluated." The code computes the identity only if every label-free run is finished and every member of the set `eval` has metrics in both readings. If one member of that set fails its metrics for one run (for instance a raw field with a negative contact unknown, which `c2.evaluate.metrics` refuses), the set has no summary, the identity becomes "NOT EVALUATED", and the code goes on: part 1 is judged PASS or FAIL and written to `verdict_part1.json` as final, and part 2 gets a wording. A prediction that the reference code cannot evaluate, where G-C2.2 could, is exactly a network that does not reproduce G-C2.2.

**How found.** Executed on a copy of the reduced run (`scratch/scen3.py`, scenario e): one raw field of `eval_0001` in run 6 given a negative contact unknown, the arm evaluated again, then the verdict.

```
errors of run 6, raw: {'eval_0001': 'AssertionError: a contact unknown is negative'} | sets summarised: ['third', 'tested']
--- e1: an eval member fails in the raw reading of one label-free run; supervised arm evaluated
    {"verdict": {"identity": "NOT EVALUATED", "self_check": "FAIL", "ranking": "NOT EVALUABLE", "comparison": "supervised closer"}, "not_evaluated": [], "missing": [], "non_finite": [], "part1_same_as_first": true}
    identity: None | self_check judged: True | comparison: supervised closer
    verdict_part1.json written: True
```

(FAIL and "supervised closer" are the words of my small models; the point is that both parts were judged.) The runbook asks for `"identity": "OK"`, so an operator would stop; the files would still hold a "final" part 1.

**Repair.** In `verdict()`: when no label-free run is missing and the identity cannot be computed, set it to INVALID, and both parts with it, or give the case its own word that blocks both parts, and say so in the text. Decide in the same place what a label-free run without finite predictions means for the identity (today: identity NOT EVALUATED, part 1 FAIL by the configuration's `non_finite_seed`, part 2 compared; executed, `scratch/scen2.py` scenario d). Add a test.

### 3. SHOULD FIX. Outcomes that the code can produce and that the text does not fix in advance

Each is a choice that would otherwise be made after results are known.

a. **A training label that fails after part 1 is final.** `docs/PRESPEC_G-C2.3.md` line 166 says a label that does not converge or fails its checks "stops the gate before any prediction". That is true of the held-out labels only. The 3,584 training solves come after part 1 (runbook section 6). If one fails, `check-labels` stops the queue before the training, and the text does not say what becomes of part 2: left INCOMPLETE for good, or solved again in some other way. State the rule (my suggestion: part 2 is not run and is reported as INCOMPLETE; no other solver settings).

b. **A member whose metrics fail altogether.** Code: in the judged set of a label-free run, part 1 is FAIL and R is NOT EVALUABLE (`c23/evaluate.py` lines 342 and 343); in a supervised run the seed enters with infinite errors (lines 310 to 312, with `_stats`). Neither the text nor the configuration's `criteria` says so (`c23/config.py` lines 106 to 108 name non-finite losses and predictions only; G-C2.2's configuration named this case).

c. **R when no run has a pair above 0.05.** Text (line 132): R is reported "as HOLDS or DOES NOT HOLD". Code (`c23/evaluate.py` line 122): a third word, NOT EVALUABLE, which the runbook lists (line 122). By the text's own sentence R would hold vacuously. Say which.

d. **A PASS with R not holding, and a PASS with nothing to catch.** "Interpretation" covers PASS, and FAIL with R holding. It is silent on a PASS where R DOES NOT HOLD (possible: with all large errors flagged and 35% of the pairs flagged, the area can be near 0.7), and on a PASS in which few or no pairs exceed 10% (S1 is then true whatever the spread does). The code reports how many pairs above 5% and 10% there were and how many were flagged (`pairs_above`); the fixed wording of a PASS should be required to give these counts.

e. **Identity NOT EVALUATED**: finding 2.

### 4. SHOULD FIX. The runbook's stops on the words of a verdict are not enforced: the guards read exit codes, and `verdict` ends with 0 whatever it says

**Where.** `RUNBOOK_C23.md` lines 16, 123, 124 and 154; `c23/__main__.py` lines 116 to 134; `queue_tools_copy/guard.py` line 44; `gate_prep/make_jobs_c23.py` lines 96 to 107.

**What is wrong.** Section 5 says of `"identity": "INVALID"`: "Stop and report; nothing further is run", and of part 1: "the queue does not wait" for the operator. A guard cancels later jobs only if its stage ended with a non-zero exit code. `verdict` prints its line and ends with 0 for INVALID, for NOT EVALUATED, and for `"part1_same_as_first": false` or `null`. The same holds for `predict-label-free` ending with "non-finite predictions" and for `evaluate --arm` when a run is not `finished`. With set C queued, which "the queue does not wait" implies, an INVALID verdict would be followed by the training labels and three training runs.

**How found.** Read (`__main__.py`, `guard.py`), and executed for one case: the command line on a runs folder whose label-free rows file is absent.

```
$ python3 -I scratch/stage_cli.py scratch/run1 verdict --data scratch/run1/data --runs scratch/scen/a/runs --config-sha SHA
{"verdict": {"identity": "NOT EVALUATED", "self_check": "INCOMPLETE", "ranking": "INCOMPLETE", "comparison": "INCOMPLETE"}, "not_evaluated": ["label_free"], "missing": ["label_free_s5", "label_free_s6", "label_free_s7"], "non_finite": [], "part1_same_as_first": null}
[exit 0]
```

This does not touch the validity of a verdict; it costs laptop time and contradicts the runbook.

**Repair.** After writing its files, let `verdict` end with a non-zero code when the identity is not OK, or when `part1_same_as_first` is not true once `verdict_part1.json` exists; let `predict-label-free` do so when its status is not `finished`. Or change the runbook: set C is queued only after the operator has read the line of section 5. `make_jobs_c23.py C` could refuse unless the done file of `93z_c23_guard` shows exit code 0; it already reads the queue folder.

### 5. SHOULD FIX. The identity check can fail only after the third sample has been drawn, labelled, predicted and evaluated; nothing run before the draw tells whether it will pass on the host

**Where.** `RUNBOOK_C23.md` sections 2 to 5; `docs/PRESPEC_G-C2.3.md` lines 116 to 118; `probes/c2_timing/time_curve.py`.

**What is at stake.** The state files are pinned by SHA-256 and checked in section 0d, before the draw. With the right files, the identity check can fail only for numerical reasons: the GPU giving other float32 results today than on 14 and 15 November. It would then fail in section 5, when the errors of the fresh sample are already in `rows_label_free.json`, and its S1 to S3 under `self_check_reported` (finding 16). The sample would be spent and the gate INVALID.

**What I can and cannot say.** For a pass: G-C2.2's host check found no difference at all between two runs' prediction files on that GPU in the reduced configuration (`records/c22/host_check/smoke_report.json`: `resume.max_prediction_difference` 0.0 three times), and on a processor my predictions from a state file reproduced the base runs' values exactly (`identity.largest_difference` 0.0 in `scratch/run1/runs/verdict.json`). Against: the host's software changes (`records/c22/return/incidents.log`: a restart for Windows updates during the run of seed 5); G-C2.2's return package held no state file, so, as far as its records show, nobody has predicted again from a state on another day; and the condensed reading is not continuous in rounding, because the amplitude's iteration stops on a threshold and can end on another evaluation. Whether such a change stays below 0.0001 in a per-seed median or 90th percentile I cannot tell here. The host check of section 0e does not settle it either: it compares predictions made from a state file with predictions made minutes earlier in the same process.

**Repair.** Before the stamp, on the host: predict G-C2.2's fresh members from each of the three state files under G-C2.2's own data folder and compare the fields with the prediction files that G-C2.2 left (`gate_runs/label_free_s<seed>/preds.npz` and `preds_condensed.npz`). `time_curve.py` already loads a state and computes the fields and amplitudes of members of that folder; forming the condensed field and printing the largest difference from the stored one is a few lines, and it only reads. If the fields are equal to the last bit, the identity check will pass. If not, the tolerance can be set with the difference known, before anything is drawn.

### 6. SHOULD FIX. A string that must not be published

**Where.** `gate_prep/make_jobs_c23.py` line 17: the queue's folder is a path of the working machine under the user's home, and one of its folder names is the word that the brief lists under H, capitalised (`"mnt/C.../c2dev/queue"`).

**Why it matters.** The file is outside the repository today, but the runbook sends the queue's scripts into the return package (line 168), and G-C2.2's package is in the repository with its `make_jobs.py`, where the same line reads `pathlib.Path.home() / "W/queue"` (`records/c22/return/queue/make_jobs.py` line 14).

**How found.** Executed: a case-insensitive `grep` for the word over the new files gave this one line. The reference copy `queue_tools_copy/pause.py` line 41 holds the word too, in a message to the owner in Chinese; G-C2.2 returned `guard.py`, `hold.py`, `check_gpu.py` and `make_jobs.py`, not `pause.py`.

**Repair.** Take the folder from an argument or an environment variable, or write the neutral path as in G-C2.2, before the file is returned. Decide whether `pause.py` and `resume.py` belong to "the queue's scripts" of line 168; if so they need the same care.

Nothing else was found under H (section 2, H).

### 7. MINOR. "Every later verdict says whether its part 1 is the same" is not true when the later part 1 is INCOMPLETE

**Where.** `c23/evaluate.py` lines 375 to 379 and the module's docstring, lines 8 to 10; `docs/PRESPEC_G-C2.3.md` line 172; `RUNBOOK_C23.md` line 123.

**What is wrong.** The comparison with `verdict_part1.json` is made only if the present verdict's part 1 is decided. If the label-free rows file is absent at a later verdict (moved, not copied, or the arm evaluated again while a run folder is away), part 1 is INCOMPLETE, the key `part1_same_as_first` is absent and the command prints `null`, although a first part 1 exists and differs.

**How found.** Executed (`scratch/scen1.py`, scenario a):

```
--- a1: rows_label_free.json absent, verdict_part1.json present
    {"verdict": {"identity": "NOT EVALUATED", "self_check": "INCOMPLETE", "ranking": "INCOMPLETE", "comparison": "INCOMPLETE"}, "not_evaluated": ["label_free"], ..., "part1_same_as_first": "KEY ABSENT"}
```

**Repair.** Make the comparison whenever `verdict_part1.json` exists; an INCOMPLETE part 1 is then reported as `false`.

### 8. MINOR. `verdict_part1.json` is written again without a word if it is removed, and the unused function `evaluate()` writes a first part 1 that already holds part 2

**Where.** `c23/evaluate.py` lines 376 to 378 and 384 to 390.

**What is wrong.** "Written once" holds as long as the file stays. If it is deleted, the next verdict writes a new one from the present state and reports `part1_same_as_first: true`; nothing in `verdict.json` shows it. The only evidence of the order is inside the kept file (`not_evaluated`, `cost.training_members_labelled`) and in the queue's logs. The function `evaluate()` is called by nothing (not by `__main__.py`, `smoke.py` or the tests); called on a folder with both arms' runs it evaluates both and writes a first `verdict_part1.json` with a comparison in it.

**How found.** Executed (`scratch/scen1.py` scenario b, `scratch/scen4.py` scenario g):

```
--- b1: verdict_part1.json removed, then verdict
    {... "comparison": "supervised closer"}, "not_evaluated": [], ..., "part1_same_as_first": true}
    the new verdict_part1.json holds comparison: supervised closer | training members labelled: 4
--- g1: evaluate() on a folder with both arms' runs and no rows
    {... "comparison": "supervised closer"}, ..., "part1_same_as_first": true}
    verdict_part1.json holds comparison: supervised closer
```

**Repair.** Remove `evaluate()`. In section 5 of the runbook, have the operator record the SHA-256 of `verdict_part1.json` and of `rows_label_free.json` in the report of part 1; in section 8, check both, and check that the kept file shows `"not_evaluated": ["supervised_512"]` and `"training_members_labelled": 0`.

### 9. MINOR. Statements of the pre-specification that say more than the records show, or are imprecise

a. Line 51, "The spread ranked the errors best." True for the area under the curve for errors above 5% on both samples. Not true of every reading in `probes/c2_selfcheck/records/selfcheck_indicators.txt`: for errors above 10% on the first sample, C beats D in run 7 (0.963 against 0.950), and the Spearman correlation on the second sample is higher for C in all three runs (0.64, 0.62, 0.61 against 0.63, 0.60, 0.58). The README says it with care; add "by the area under the curve for errors above 5%".

b. Line 57, "the tested member T1". There are two, preloaded and snug. The numbers are those of `BJ_T1_preloaded` (executed: 1.39% to 18.12%; 0.20% to 1.67%; 0.19% to 2.77%). For the snug one the supervised arm of G-C2.1 read 1.8% to 49%. Name the member.

c. Line 59, "no training member has been solved at 8 mm for a label; no supervised run with more than 64 labelled members, or with the stability recipe, has been made." Twenty-four training members were solved at the seven judged levels, 8 mm among them, in G-C2.2's development (`probes/c2_dev/README.md` line 85); "for a label" saves the sentence only narrowly. And the host check itself trains a supervised run with the recipe (four members, reduced configuration), and `step_cost.py` makes supervised steps with the recipe's beta2. Qualify both halves.

d. Line 30: finding 1. Line 166: finding 3a. Line 132: finding 3c.

e. Line 122 and `c23/config.py` line 81 give the spread as (max - min) / median. The code divides by the absolute value of the median and treats a median of zero as an infinite spread, which is flagged (`c23/evaluate.py` lines 98 to 101). With three negative forces the text's formula gives a negative spread, not flagged; the code flags it (executed, `scratch/numerics.py`: -100, -100.2, -100.6 gives 0.00599 and a flag). The forces were positive in every pair of both earlier samples (executed), so this is wording; write the absolute value.

f. Line 40 attributes to the owner's message of 03:56 the confirmation of "one gate for the two registered runs; the third sample serves both parts; ... the seeds; the band of part 2". The list quoted for that message in line 38 names six other points. I cannot see draft 0.1; if these points were in it, say so, otherwise they are the author's choices.

g. Line 7, "two further questions of the same three networks": part 2 is a question about new networks.

h. Line 75 lists six new files; the hash list has seven (`c23/__init__.py`).

i. Lines 140 and 144: "the training time of each run" and "the cap's actions" exist in this gate's records for the supervised runs only; for the label-free runs the verdict holds a note that points to G-C2.2's records (`c23/evaluate.py` lines 370 and 371). Say that the verdict document takes them from there.

j. Line 138, "between 2/3 and 3/2": the code includes both ends (`c23/evaluate.py` line 135). Say "inclusive".

### 10. MINOR. Places where the runbook disagrees with the code or with the other texts

a. Line 28: "The step time is the one the host check of section 0e gave." Section 0e runs the reduced configuration and measures nothing of the gate's model. The step time comes from `probes/c2_timing/step_cost.py`, run before the stamp (`docs/PRESPEC_G-C2.3.md` line 114; `make_jobs_c23.py`, set P).

b. Section 0e does not say what to do after an interrupted host check. `smoke.py` refuses a folder that is not empty (line 89), so the rule of line 18 ("the interrupted command runs again from where its files left it") does not hold for it: the second start fails and the guard cancels the rest. `queue_tools_copy/pause.py` line 14 counts `smoke.py` among the scripts that can be paused and continued.

c. Section 5 drops a warning that `RUNBOOK_C22.md` gave for the same kind of command (its line 120): if the system kills a worker process, the evaluation can wait without end.

d. Line 111, "Each prints a start line": a prediction that already exists returns before the start line (`c23/train.py` lines 206 to 214).

e. Lines 100 and 132: the check's line ends in `"ok": true}`, with the brace.

f. Section 7 refers to section 4 of `RUNBOOK_C22.md`, which is not in the archive of step 0a. The operator needs the repository beside the archive, as for the tests of 0c.

g. The host check's report no longer records the thread variables of the worker processes, which `c22/smoke.py` recorded (its lines 76 and 86) and `RUNBOOK_C22.md` asked the operator to read. The processor time of the training labels is one of the things part 2 reports for the supervised arm, and it depends on them.

h. The outputs of set P (`pre3_records/`: the step time that the pre-specification will quote, and the host check before the stamp) are in no return package; say where they are kept.

i. To do at the stamp, not defects: the placeholder `@@CONFIG_SHA@@` stands in lines 77, 107 to 109, 118, 119, 137 to 139, 149 and 150; `docs/G-C2.3_code.sha256` does not exist yet; the pre-specification holds eight bracketed placeholders (lines 3, 61, 71, 75, 87, 110, 114, 170).

### 11. MINOR. The supervised runs neither check nor record the labels they train on

**Where.** `c23/train.py` lines 69 to 76.

**What is wrong.** `train()` reads `labels/train_*.npz` as they are. It does not compare them with the ledger (`check_files`), and `history.json` keeps only their number (`reference_solutions`). Between the check of section 6 and the end of the third run lie many hours; a label solved again or damaged in between would be noticed by no command, and the return package does not hold the training labels. An auditor can still hash the files on the laptop against the ledger, as long as they are kept.

**Repair.** In `train()`, call `check_files(data_dir, ids)` before `_prepare`, and store in the history the SHA-256 of the training members' ledger entries (the construction of `_inputs`), refusing a resume under another value.

### 12. MINOR. On the GPU the host check passes only if predictions agree to the last bits

**Where.** `c23/smoke.py` lines 113 and 139.

The reduced gate takes the base runs' values as its identity values and asserts `identity == "OK"` with the gate's absolute tolerance of 0.0001. The small models' identity values lie between 26 and 101 times the reference force in my run, so the tolerance asks for agreement to a few parts in a million. On a processor the difference was exactly 0.0. On the GPU it will pass if predictions from a loaded state repeat to the last bits, which G-C2.2's host check suggests; if it fails there, the cause may be this amplification and not a defect. Worth a sentence in section 0e, or a relative tolerance in the reduced configuration.

### 13. MINOR. The tests: two pass for another reason than their text says, and several behaviours have no test

a. `tests/test_c23.py` lines 57 to 60: the case "third seed equal to the eval seed" is refused by the first check of `members` ("used before the stamp"), because the eval seed is in the seen list. The second refusal ("not fresh", `c23/data.py` lines 31 and 32) is reached by no test, and with the real configuration it cannot be reached at all: all three seeds it names are in the seen list. Test it on the reduced configuration (third seed set to 8).

b. Lines 283 to 286: "another configuration: refused" is refused by the manifest's check (`c23/evaluate.py` lines 280 and 281). The rows file's own check (lines 292 and 293) has no test; the pattern `another configuration` matches both messages.

c. Lines 116 to 118, "a spread on the threshold is flagged": true of the triple chosen (100, 100.45, 100 gives 0.004500000000000028). The triple 1, 1.0045, 1 gives 0.0044999999999999485 and is not flagged (executed, `scratch/numerics.py`). Exact ties do not occur with real forces; the comment promises more than floating point gives.

d. Lines 57 to 64 call `data.members` on copies of the real configuration, one of them with the real held-out seed as its third seed. They are safe only because the refusal precedes the draw. `tests/test_c22.py` builds its refusal cases from its small configuration (lines 104 to 107); do the same here, so that a later edit of `members` cannot make the suite draw the sample.

e. Without any test (the host check covers the first three as library calls, on one seed): the whole of `c23/__main__.py`; `check_labels` with a list of splits; `train` and `predict_label_free` with their refusals of a state of another seed, arm, configuration or epoch; in the verdict step: a non-finite seed of either arm, a member whose metrics fail, the identity NOT EVALUATED, NOT COMPARABLE at the level of the verdict, the band's ends. I ran all of these on the reduced configuration (section 2); they behave as read, apart from findings 2 and 7.

### 14. NOTE. The interlock "not stamped" no longer blocks anything

`c23/__main__.py` lines 46 to 48 and 98 to 99 refuse every command but `write-config` while a state hash is not filled in, with the message "the gate is not stamped". Since draft 0.2 the hashes are filled in, so the check always passes. `generate` asks for no `--config-sha`. Nothing in the code keeps `generate` from drawing and exporting the held-out sample from the draft tree that set P puts on the laptop before the stamp; the protection is the runbook's sentence (line 88) alone. If a technical bar is wanted: let `generate` refuse unless `docs/G-C2.3_code.sha256` exists beside the code and matches it; that file is made at the stamp.

On the refusal in `members` itself (`c23/data.py` lines 29 to 32): it is sound for what it checks, and it runs before any draw. It rests on the list `seeds_seen_before_stamp` being complete; the tree shows no other draw of this family than 7, 8, 101, 102 and the three gate seeds (`grep` for `sample(`).

### 15. NOTE. `--runs` given G-C2.2's folder by mistake: `verdict` would overwrite G-C2.2's `verdict.json` on the laptop

Read: with `--runs gate_runs` no rows file exists there, every part is INCOMPLETE, and `c23/evaluate.py` line 380 writes `gate_runs/verdict.json`. The other commands refuse that folder (`check_run`, the history's configuration) or write only into new sub-folders. The job files give `gate3_runs`, so this needs a hand-typed command, and a copy of G-C2.2's verdict is in the repository. A line in `verdict` that refuses a folder whose `verdict.json` names another gate would close it.

### 16. NOTE. An INVALID verdict still holds the judged numbers

With the identity INVALID, the keys `self_check` and `comparison` are absent, but `self_check_reported["label_free"]["condensed"]["third"]` holds S1 to S3 and their verdict, and `statistics` holds both arms (executed, `scratch/scen4.py` scenario f). "No part is read" is then a rule for the reader, not a property of the file.

### 17. NOTE. The three probes

They do what their docstrings say, and they cannot change G-C2.2's data or state file (section 2, probes). Small points:
- `step_cost.py` line 104 and `time_curve.py` line 139 write their output only at the end; if the folder of `--out` does not exist, the timings are lost from the file (they are in the log). In set P the folder exists only because the host check made it.
- `time_curve.py`: the surrogate's time ends before the condensed field is formed and before anything leaves the device; the reference's time leaves out reading the export, the surrogate's time "with preparation" includes it. Both effects are small.
- `f2_cost/energy_cost.py` lines 69 to 84: the timed call also draws the random fields on the processor, moves them to the device and reduces two finiteness checks. For a figure called a lower bound, time only the energy and its gradient. Its fields are not made admissible (fixed unknowns zero, contact unknowns not negative), as `probes/f2_dev/energy_cost.py` made them; that does not change the time. The docstring sets "the coarse mesh" of the earlier probe against "the family's mesh"; the family's mesh is the coarse one (`f2/family.py` line 43). The export includes the preload solve and takes minutes on a processor before any timing starts.

### 18. NOTE. The job generator

- Set C can be queued after a failed set B: the training labels, their check and, if the labels are sound, three training runs are then made although part 1 has no verdict. See the repair of finding 4.
- The guard of set P's host check cancels the three probes if the host check fails; they do not depend on it.
- `generate --limit N`, kept from G-C2.2, on the gate's data folder writes a manifest with fewer members; every later command then refuses, and a plain `generate` restores the same bytes (executed, `scratch/scen6.py` scenario l).

### 19. NOTE. Smaller things

- `c23/config.py` line 74 keeps `training_seeds_seen_before_stamp` at 0 to 4 although seeds 5, 6 and 7 were used in G-C2.2; the comment says so, and `c23/train.py` does not check the key.
- The JSON files hold the tokens `Infinity` and `NaN` when values are infinite or not numbers, as G-C2.2's did; strict readers of JSON refuse them. My reduced rows file holds an infinite error (a tested member, "the reference force at the predicted end displacement is not positive"), and every step handled it.
- The configuration's key `self_check.arm` is not read by the code; the arm is fixed in `c23/evaluate.py`.
- `python -I` ignores `PYTHONDONTWRITEBYTECODE`; the queue's start writes `__pycache__` folders into the stamped tree, as in G-C2.2. They are not in the hash list.

## 2. Checked and found correct

**A. Code against the pre-specification**
- The configuration hash is the one of the text: `python3 -I tree/joint/c23/__main__.py write-config --out scratch/c23_config.json --repo tree` prints `config sha256 b21c7913b1e312e48e8259a935fcbb683c85d78616707731fffece5b7a26dce5` (executed). Its differences from G-C2.2's configuration are the listed ones and nothing else (executed, `scratch/cfg_check.py`, a recursive comparison of the two dictionaries); G-C2.2's hash is `ef5376a4...8734bb` (executed).
- The files of `c22/`, `c2/`, `fejoint/` and the six repository files are those stamped for G-C2.2: `sha256sum -c docs/G-C2.2_code.sha256` in `tree/joint` gave no line other than OK (executed).
- Samples and seeds, the levels of each split, the ids and their order (read; the differences of `c23/data.py` from `c22/data.py` listed by a diff, executed).
- The supervised run is G-C2.2's run with the changes the text names: a diff of `c23.train.train` against `c22.train.train` shows the arm's name, the dropped check of the training seeds, the labels in `_prepare`, the count of labelled levels, `reference_solutions`, `step_loss(..., True, ...)` and `del items`, and nothing else (executed). The loss on 4 of the 7 levels without replacement is `c2.train.step_loss`, unchanged (read). 200 epochs of 512 steps, AdamW with the configuration's beta2, the cap, the clipping, the schedule, a checkpoint every epoch (read).
- The same seed gives the same initial weights in both arms: for seeds 5, 6 and 7 the parameters built after `_prepare(energy=True)` and after `_prepare(labels=True)` are identical, and the first epoch's order is the same (executed on a processor, reduced configuration, `scratch/init_weights.py`: `energy_vs_labels_identical: true`, 22,055 parameters).
- Label-free arm: the file's SHA-256 is compared before the file is unpickled and before the run folder is made; then the history's configuration, arm and seed and the end of the run are checked; nothing is trained (read, and executed, `scratch/scen5.py`: a state of another seed, another arm, another configuration and an earlier epoch are each refused; the pinned file is accepted).
- The flag at "at least the threshold", S1, S2, S3, the verdict of part 1, and R with ties counting half: `self_check` agreed with a direct computation in 200 random cases with zero and negative medians and infinite errors, and `auc` with a count over all pairs in 300 random cases with ties and infinite scores, largest difference 0.0 (executed, `scratch/numerics.py`). The comparisons `<= 0.01` and `<= 0.35` cannot go wrong by rounding: each share is one correctly rounded division, and 0.35 of 448 is not a whole number (reasoning).
- Part 2: the two statistics are the middle of three per-seed values, the ratios are supervised over label-free, and the five words follow the text (read; the edges executed in `scratch/numerics.py`).
- The identity check compares twelve per-seed values in the order of seeds 5, 6, 7; the values in `c23/config.py` equal those of `records/c22/return/verdict.json` exactly (executed: `G22_PER_SEED equals the record: True`).
- INCOMPLETE and non-finite runs as the configuration's `criteria` say: two of three label-free runs give INCOMPLETE and no kept file; a non-finite supervised seed enters with infinite values; a label-free run without finite predictions gives part 1 FAIL (executed, `scratch/scen2.py`, `scratch/scen6.py`).

**B. Leakage and freshness**
- No reference solution enters a prediction: `predict-label-free` in a data folder with no label at all wrote the same bytes as with labels (executed, `scratch/scen8.py` scenario p).
- No held-out label enters the training or the supervised predictions: training with only the four training labels present gave the same prediction arrays as the run that had every label (executed, scenario q). `load_label` is reached only through `_prepare(labels=True)` for the ids of the split `train`, and in the evaluation (read, `grep`).
- The flag uses the predicted end displacement and the level only (read: `c23/evaluate.py` lines 54 and 55).
- Both arms are judged against the same label files: the hash of the evaluated members' ledger entries is among the inputs of both rows files, and each entry pins its instance file and its label file (read).
- No path of the tests, the host check or the probes draws the seed 20261118: the reduced configurations of the tests and of the host check set the third seed to 102; the two timing probes read G-C2.2's data and draw nothing; the cost probe uses a tested member of another family (read; `grep` finds the number in the tree only in `c23/config.py`, the pre-specification and the runbook).
- The stamped tests of G-C2.1 and G-C2.2 draw only their test seeds (read).

**C. The two-step evaluation**
- The repair is in place: `_inputs` hashes the ledger entries of the evaluated members only, sorted by id. In the reduced run the kept file and the label-free rows file had the same SHA-256 after the first verdict, after the training labels, and after the training and the final verdict (executed). The verdict after the training labels equals the first apart from `cost`, where the labelled training members go from 0 to 4 (executed, `scratch/scen9.py`).
- Stale rows are refused: a changed prediction file and a held-out label solved again (the tests, executed), a run that appeared after the evaluation (scenario j), a supervised run turned non-finite (scenario c), a manifest with other set sizes (scenario l).
- Valid rows are not refused in the runbook's order, nor after a second `generate` (same manifest bytes), a second `evaluate --arm label_free` with another number of workers (same bytes of the rows file), or a label-free prediction made again after a missing `condense.json` (same bytes on a processor) (executed, scenarios i, l, o). The supervised arm evaluated with two workers and with one gave the same bytes too (scenario s).
- Interrupted and repeated commands: the supervised run stopped after two epochs and resumed ends with the weights, losses, capped steps and predictions of the uninterrupted run; a run stopped between its history and its predictions predicts again and gives the same arrays; a finished run returns at once (executed on a processor, `scratch/scen7.py`). A kill within an epoch was not tried.
- The first verdict is written whole and through a temporary file; a verdict interrupted between the kept file and `verdict.json` is repaired by running it again (read).
- The comparison of part 1 through JSON is reliable: nothing in the compared part can be not-a-number, infinite values survive the round trip, and all keys are strings (reasoning; round trips executed in `scratch/numerics.py`).

**D. The runbook against the code**
- Every `PY` command of the runbook equals a job of sets A, B and C, token by token and in the same order: 19 of 19 (executed: a script that parses the runbook and the output of `make_jobs_c23.py --dry`). All four sets pass the generator's own assertions on names (executed).
- The whole order of sections 2 to 8 through `c23/__main__.py` on the reduced configuration: generate; label third, eval, tested; `check-labels --splits third eval tested`; three predictions; `evaluate --arm label_free`; verdict; label train; check; verdict; train; `evaluate --arm supervised_512`; verdict; every exit code 0 (executed). The quoted outputs match: `{"status": "finished", "predict_seconds": ...}`; `{"label_free_s5": "finished", ...}`; the verdict's line with its four words in the order identity, self_check, ranking, comparison, with `"not_evaluated": ["supervised_512"]` and `"part1_same_as_first": true`; `{"status": "finished", "steps": 16}`; the check's line with `"labels": 5, "needed": 5, "missing": []`, later 9 and 9.
- Refusals end with a non-zero code: a wrong `--config-sha`, a missing ledger, a split name that does not exist, `--arm` with another value, a missing training label (executed).
- Counts: 644 members (read); 132 and 644 labels (read; 5 and 9 in the reduced run, executed); 35 code hashes and six repository lines (executed: `write-config` prints 43 lines, the second `state files pinned: True`); 62 tests: `cd tree/joint && FEJEPA_REPO=.. python3 -m pytest -q -p no:cacheprovider tests/test_hex8i.py tests/test_contact.py tests/test_c2.py tests/test_c22.py tests/test_c23.py` ended with `62 passed, 5 warnings in 798.99s (0:13:18)` (executed).
- The three state hashes are the same in `c23/config.py`, the pre-specification and the runbook (executed).
- Folders: no command of the runbook or of the job files writes into `gate_data/` or `gate_runs/`; the state files are opened for reading only (read; for a mistyped option see finding 15).
- Guards: every stage but the label commands has its own guard; the label commands are covered by the guard of the check that follows them, which fails on a missing or unconverged label (read `guard.py`; the check's exit code executed). The names sort as the generator's docstring requires, continuations of a paused stage included (reasoning on `guard.py` lines 34 to 41).
- After an interruption: `generate` keeps finished files (read; a repeated `generate` executed); `label` keeps finished labels (read, stamped code); `predict-label-free` starts again and, once finished, returns at once (executed); `evaluate` writes its rows file only at its end (read); `train` resumes (executed, see C); the host check: finding 10b.
- The return package: every file name of section 9 is one the code writes; the reduced run produced each of them (executed, listing).
- The numbers of "Time and space" that rest on G-C2.2: 265 s for the export (264.6), 117 s a member in the median of the ledger (117.17), two hours of evaluation (7,223.5 s), 3.5 GiB (3.52) (executed, from `records/c22/return/`).

**E. Edge cases and numerics**: the items under A and C, and `scratch/numerics.py`; for ties see finding 13c, for negative and zero medians finding 9e.

**F. The tests**
- `cd tree/joint && FEJEPA_REPO=.. timeout 600 python3 -m pytest -q -p no:cacheprovider tests/test_c23.py`: `11 passed in 0.81s` (executed). Each test checks what its name says, apart from finding 13 (read; the expected numbers of the self-check, area and wording tests worked out by hand).

**G. The text of the pre-specification**
- "What was seen", recomputed from `records/c22/return/verdict.json` with the gate's own `auc` (executed, `scratch/seen_numbers.py`; the spread needs no reference force, which cancels): areas 0.956, 0.972, 0.967 and 0.956, 0.944, 0.952; upper quartile 0.004504; 113 of 448 flagged at "at least 0.0045" on the first sample, 1,005 readings not flagged, one above 5% (5.09%), none above 10%; 118 flagged on the second, 990 readings, none above 5%, largest 4.92%; smallest spreads among pairs above 10%: 0.00476 then 0.0230 on the first sample, 0.0242 on the second; three readings above 10% not flagged at 0.0050; 7 and 8 pairs above 10% in any run; shares flagged 25.2% and 26.3%.
- The reading of plastic depth, the two-run spread (7.0% to 9.0%) and the README's table and bullets agree with `probes/c2_selfcheck/records/` (read, line by line).
- G-C2.2's 0.80% and 3.66%; G-C2.1's supervised arm of 12,800 steps; 3,584 solutions; 307,200 steps; 5,544 solves an arm; a step of 0.44 to 0.50 s (the means of the three runs: 0.441, 0.446, 0.495); about 21 hours of labels (644 members at 117 s) (executed or computed).
- "The smoke test shows the extreme case ... none of their pairs is flagged": in my reduced run on a processor 0 of 4 pairs were flagged, with spreads of 0.0008 to 0.0011 and per-seed median errors of 37 to 56 times the reference force (executed).

**H. What must not be public** (executed: `grep` over the new files, with the README, scripts and records of `probes/c2_selfcheck`)
- The word of the brief: one line, finding 6. Personal names: none (I searched for the names of the owner and of the people known to me from the session's context, and listed every capitalised word of the prose). User names, e-mail addresses and paths of a working machine: none other than finding 6. <a name that the brief lists under H>: only the package name in an import and `FEJEPA_REPO` in a command.
- No en dash or em dash, and no character outside ASCII at all, in any new file. No American spelling found by a search for the usual endings and a word list; `synchronize` occurs only as the name of a library function.
- The eleven new Python files compile under Python 3.12 (executed with the 3.12 interpreter of this sandbox, in memory).

**The probes** (the two questions of the brief)
- `step_cost.py` and `time_curve.py` ran end to end on a processor against the data and a state file of the reduced base configuration; a hash over every file's name, bytes and modification time in the data folder and the runs folder was the same before and after (executed, `scratch/probe_dry.py`: `unchanged ...: True` twice). They open the data, the state and the repository files for reading and write the file of `--out` only (read).
- `f2_cost/energy_cost.py` ran on a processor with `--mesh tiny` and wrote its report (executed). It takes no folder of G-C2.2 and draws no member.

## 3. Not checked

- Anything that needs the host: CUDA, the GPU's memory and step times, worker processes started by spawn on Windows, the queue's runner (not among the copies), a pause or a kill of a real job, and whether today's GPU predictions equal those of G-C2.2 (finding 5).
- **`c23/smoke.py` as one command gave no result.** I started it once on a processor and stopped it after ten minutes, in its third base run: another test process held a full core, epochs of four steps took 20 to 57 s against 0.7 to 0.9 s earlier, and it could not have ended within the limit of 20 minutes. Its stages and its own comparisons were all run separately on the reduced configuration (section 2, C and D): the base runs, the refusal of another seed's state, the first verdict, the verdict after the training labels, the full and the resumed supervised run, the evaluations with and without workers, stale rows, a changed part 1.
- Python 3.12 at run time: this sandbox runs 3.13.18 with numpy 2.5.3 and torch 2.12.1 for the processor; under 3.12 I could only compile the files.
- The scripts of `probes/c2_selfcheck` were not run again: the labels of G-C2.2's deposit are not in the tree. I recomputed everything that follows from the spread out of the verdict record; the secant-ratio and plastic-point numbers of 17 November were compared with the stored records only.
- Draft 0.1, the owner's messages and the correspondence record: I cannot see them (finding 9f).
- That nothing of the gate has been drawn by anyone: I can only say that the tree holds no trace of it.
- The three state hashes against the owner's archive: no record in the tree carries them.
- The supervised run at full size: its memory, its time, and how the cap behaves under the supervised loss. `step_cost.py` on the host will show the first two.
- The content of the stamped tests and code of G-C2.1 and G-C2.2 beyond their use by the new code; `fejoint`, the solver and the reference model.

**What my work left behind.** Everything I wrote is in `scratch/`, the partial output of the stopped host check included (`scratch/smoke_out`). The pytest runs, started with the commands of the brief and of the runbook, put their temporary folders under the system's temporary folder, as those commands do. My runs created `__pycache__` folders in `tree/joint`; I removed them. `sha256sum -c SNAPSHOT_round1.sha256` gave 13 times OK at the start and at the end.

---

# What the author did after round 1

Written by the author of the reviewed files, not by the reviewer, on 18 November 2026, and handed to the reviewer with round 2. Paths are relative to `joint/`. "Tree 2" is the state that round 2 reviewed.

**Changes of the tree between the snapshot of round 1 and the report, made by the author before the report arrived**
- `tests/test_c23.py`: tests of the code list, of the entry point as a process, of the supervised training (initial weights, the recipe, resume) and of the runbook's commands through the command line in the runbook's order.
- The ranking's third word, NOT EVALUABLE, written into the configuration, the pre-specification and the runbook.
- The labels of the supervised arm at eight levels, from 0.1 mm (finding 1), with a pilot on two members of seed 7.
- `probes/c2_selfcheck/gate_code_on_seen_samples.py`: the gate's own function for part 1 on G-C2.2's predictions of the two seen samples, with its record.
- "Interpretation", part 2: the supervised arm's raw reading beside the wording.
- `README.md` of the package; the runbook's estimate of disk space, from the sizes on the laptop.

**Findings**

1. *The lower end of the labelled range.* Done, and it awaits the owner. The author had found the same defect while the review ran, and one more part of it: the base level of the condensed reading, 0.1 mm, lay below the labelled range too. The training labels now have eight levels, 0.1, 0.75, 1.5, 2.5, 3.5, 5, 7 and 8 mm (`c23/config.py`, with an assertion that every level at which a network is read lies within the labelled range; `tests/test_c23.py`). 0.5 mm is not labelled: it lies between 0.1 and 0.75 mm, as the other judged levels lie between labelled ones. The pre-specification is corrected and marks the point as open, because the owner had agreed to seven levels. The medians of both arms at each level are computed by the verdict (`by_level`) and named under "Reported, not judged".
2. *Identity NOT EVALUATED and both parts judged.* Done. When no label-free run is missing and the identity values cannot be computed, the identity is INVALID and both parts with it (`c23/evaluate.py`, `verdict`). This covers a label-free run without finite predictions and a member of G-C2.2's fresh sample without metrics. The configuration's `criteria` and the pre-specification ("Identity", "Stop conditions") say so. Test: `test_verdict_when_a_run_or_a_member_gives_no_numbers`.
3. *Outcomes not fixed in advance.*
   a. A training label that fails: the supervised arm is not trained, part 2 stays INCOMPLETE, part 1 stands, no other solver settings ("Stop conditions"; `criteria.training_label_failure`; runbook, section 6).
   b. A member without metrics: written into `criteria.member_without_metrics` and into the text of parts 1 and 2.
   c. R: NOT EVALUABLE if no run has pairs on both sides of 0.05 (text, configuration, runbook).
   d. "Interpretation", PASS: the wording gives, for each run, the pairs above 5% and above 10% and how many were flagged; it says when S1 was not put to the test and when R does not hold.
   e. See 2.
4. *Stops not enforced by exit codes.* Done. `predict-label-free` ends with a code other than 0 unless its predictions are finite; `evaluate` if a label-free run is not finished or a supervised run is missing; `verdict` unless the identity is OK and part 1 is the one first written, and with `--final` also unless both arms are evaluated and no run is missing. The files are written and the line is printed first. The job generator refuses set C alone unless the guard after part 1's verdict ended with 0, and has a set BC for a run that nobody watches. Runbook: "How the commands are run", sections 4, 5 and 8. Tests: `test_the_command_line_runs_the_runbooks_commands`.
5. *The identity check before the draw.* Done as proposed, as a script of its own: `probes/c23_precheck/repredict.py` predicts G-C2.2's held-out and tested members again from each state file, under G-C2.2's own data folder, into a new folder, and compares every array with G-C2.2's prediction files. It is job 81 of the set run before the stamp. On a processor, on the reduced runs that the host check leaves, the three seeds gave identical files. The pre-specification ("Identity") names the check and will state its result on the host at the stamp.
6. *The path in the job generator.* Done: the queue's folder is an argument. The runbook, section 9, names the queue's scripts that go into the return package (the guard, the waiting job, the generator) and those that do not.
7. *`part1_same_as_first` when a later part 1 is not decided.* Done: the comparison is made whenever the kept file exists.
8. *The kept file written again after a removal; `evaluate()`.* Done. `evaluate()` is removed. The first record is written only while no training member has a label and the supervised arm has not been evaluated; otherwise the verdict says that it is absent (`part1_first`) and its command ends with a code other than 0. The runbook has the operator report the SHA-256 of the kept file and of the label-free rows at part 1 and check them, and the kept file's `not_evaluated` and `training_members_labelled`, in section 8.
9. *Statements of the pre-specification.* a, b, c, e, g, h, i, j: done as proposed. f: "Authority" now says what the author's note of 03:52 put to the owner: the recommendation of one gate with one third sample and the seeds 5, 6 and 7; six points; two things to be done unless the owner objected. What was chosen afterwards is listed apart.
10. *The runbook.* a to h: done. For f the rules of the training are written out in section 7. For g the host check records the thread variables at its start and after the first labels. For h the outputs of the jobs run before the stamp go into the return package. i stays for the stamp.
11. *The labels the supervised runs train on.* Done as proposed: `check_files` before the labels are loaded, the SHA-256 of the training members' ledger entries in the history, and no resume on other labels. Tests in `test_supervised_training_keeps_the_recipe_and_the_initial_weights`.
12. *The host check's identity tolerance.* Done: the reduced configuration scales the tolerance to the stand-in networks' values; the runbook, section 0e, says what a failure there would mean.
13. *The tests.* a and d: the refusals of `members` are tested on the small configuration only, both of them; no test calls `members` with the gate's seed. b: the three places that refuse another configuration are tested one by one. c: the comment says what floating point gives, with a case just below the threshold, negative forces and a median of zero. e: the tests named under 2, 4, 8, 11 and 14, and the band's ends.
14. *The interlock.* Done as proposed: every command but `write-config` refuses unless `docs/G-C2.3_code.sha256` lies beside the code and holds the hash of every file of the code list as it is. The file is written at the stamp, so the draft tree on the laptop cannot draw the sample through the command line. `write-config` prints a third line, `code as stamped: True` or `False`. Test: `test_commands_refuse_code_that_is_not_the_stamped_code`.
15. *`verdict` on G-C2.2's runs folder.* Done: `verdict` refuses a folder whose `verdict.json` is of another configuration.
16. *An INVALID verdict with judged numbers.* Done: when the identity is INVALID the verdict holds the label-free statistics on G-C2.2's fresh sample only; the other statistics, the medians by level and the reported self-checks are empty.
17. *The probes.* Done: each makes the folder of `--out` before any timing; `f2_cost/energy_cost.py` times only the energy and its gradient, and its docstring is corrected. The two remarks on `time_curve.py` are noted and not acted on.
18. *The job generator.* Done: no guard in the set run before the stamp; `generate --limit` is removed from the gate's command line and from `c23/data.py`.
19. *Smaller things.* The list of training seeds seen before the stamp now holds 0 to 7. `verdict` asserts that the configuration's `self_check.arm` is the label-free arm. The two remarks on JSON tokens and on `__pycache__` are as in G-C2.2 and are left.

---

# Round 2 (18 November 2026, delivered at about 08:24 GMT)

# Review of gate G-C2.3, round 2

**Nothing that I found blocks the stamp.** Findings 20 and 21 should be settled before it, because they concern code and text that cannot change afterwards. [OPEN 3], [OPEN 6] and the places marked "at the stamp" remain as the draft says.

How to read this report. Paths are relative to the review folder of the brief. "Executed" means run by me in this round, on a processor, with reduced configurations and the family seeds 7, 8, 101 and 102 only. "Read" means read and not run. No member of seed 20261118 was drawn, exported or solved, and no stamp file was written into `tree2/`. My scripts and outputs are in `scratch/round2/`. Sandbox: Python 3.13.18, numpy 2.5.3, scipy 1.18.1, torch 2.12.1, two cores. The label solver here is Pardiso; on the host it is scipy's (`tree2/joint/records/c22/return/smoke/smoke_report.json`).

## 1. The 19 findings of round 1

1. **CLOSED** in code and text; the owner's word on 0.1 mm ([OPEN 6]) is still needed. Executed: the configuration reads at 0.1, 0.5, 1, 2, 3, 4, 6, 8 mm and labels at 0.1, 0.75, 1.5, 2.5, 3.5, 5, 7, 8 mm (`cfg_check2.py`; assertion at `c23/config.py` line 65); `by_level` of a reduced final verdict equals a direct computation from both rows files; 12 members of seed 101 solved at the eight levels on the gate's mesh, all converged, `"ok": true` (`pilot8.py`).
2. **CLOSED.** Executed (`sc2.py` F and G, `exit3.py` K1): a member of the identity set without metrics, or a label-free run without finite predictions, gives identity INVALID and both parts INVALID.
3. **CLOSED** for the five cases raised. Read: `docs/PRESPEC_G-C2.3.md` lines 142, 144, 152, 168, 187; `c23/config.py` lines 113 to 127; runbook line 140. Further cases found now are in finding 22.
4. **CLOSED.** Executed through `c23/__main__.py` (`cli2.py`, `exit3.py`): `predict-label-free` ends with 1 on "the predictions are not finite"; `evaluate` with 1 on a label-free run that is not finished or a supervised run that is missing; `verdict` with 0 only when the identity is OK and part 1 is the kept one; `--final` also needs both arms and no missing run. The real guard script on the generator's job files stops what follows (`qsim.py`).
5. **CLOSED** as a tool; its result on the host is one of the stamp's places. Executed: `repredict.py --host-check-configuration` on the base folders of round 1 and of my own host check, also from the unpacked draft archive: `{"all_identical": true}`; the base folders unchanged.
6. **CLOSED.** Executed: a search without regard to case over the 21 changed files and over `guard.py` and `hold.py` gives 0 lines; the queue's folder is an argument (`gate_prep2/make_jobs_c23.py` line 123); runbook line 183 says what is returned.
7. **CLOSED.** Executed (`sc1.py` E1): with the label-free rows removed, a later verdict says INCOMPLETE and `"part1_same_as_first": false`, exit 1.
8. **CLOSED.** Executed (`sc1.py` C1 to C3): the kept file removed after the training labels or after the supervised arm is not written again; the verdict says `part1_first: "absent, ..."` and ends with 1. `evaluate()` is gone (search).
9. **CLOSED.** Read a, b, c, e, g, h, i, j against lines 53, 59, 63 to 65, 132, 7, 83, 154, 150. f: the text now separates what was put to the owner from what the author chose; I cannot see the note or draft 0.1 (see 31).
10. **CLOSED** a to h. Read: runbook lines 30, 17, 18, 128, 116, 105, 139, 149 to 156, 73, 21, 179; executed: the report keys of line 72 exist in my host check's report. i is deferred to the stamp: accepted.
11. **CLOSED.** Read `c23/train.py` lines 73, 98, 107, 108; executed: the history of my reduced supervised run holds `training_labels_sha256`, and the test with both refusals passes.
12. **CLOSED.** Executed: the reduced configuration's tolerance is 1.0119 for identity values of 26 to 101; runbook line 74 read.
13. **CLOSED.** Executed: `tests/test_c23.py`, `17 passed, 1 warning in 778.85s`. Read: the tests at lines 67, 109, 326, 397, 470, 504, 574, 663.
14. **CLOSED.** Executed: without the stamp file `generate` ends with "G-C2.3_code.sha256 is not beside the code: the gate is not stamped; refusing to run" and makes no folder; with a wrong hash, a missing line or an empty file the command names the files and refuses; with the right file the commands run. Limits: finding 27.
15. **CLOSED.** Executed (`sc3.py` I1, I2): a runs folder whose `verdict.json` is of another configuration, or names none, is refused and left unchanged.
16. **CLOSED.** Executed (`sc2.py` F, `sc3.py` H): an INVALID verdict holds statistics for the label-free arm on G-C2.2's fresh sample only; `by_level` and `self_check_reported` are empty; every value under a key `third` is null.
17. **CLOSED.** Read: the three probes make the folder of `--out` first; `energy_cost.py` times the energy and its gradient only. The two remarks on `time_curve.py` were declined: accepted; the probe is outside the gate and the pre-specification quotes none of its numbers.
18. **CLOSED.** Executed (`qsim.py`): set C is refused without a done file of guard 93z, with its code 1, or when it was cancelled; it is queued with code 0. Read: set P has no guard; `--limit` is gone.
19. **CLOSED** for the two items acted on (executed: `training_seeds_seen_before_stamp` is 0 to 7; read: the assertion at `c23/evaluate.py` line 360). The two left as in G-C2.2 (the JSON tokens, the bytecode folders): accepted, with a remark on the second in finding 27.

## 2. New findings

### 20. SHOULD FIX. A label-free run without finite predictions: the stop is not final in the code, and the text does not say what this outcome means

**Where.** `tree2/joint/c23/train.py` lines 213 to 220 (only a finished run is returned; compare lines 60 to 62 of `train`). `docs/PRESPEC_G-C2.3.md` lines 126, 174, 190. `RUNBOOK_C23.md` lines 118, 119.

**What is wrong.** a. By the text such a run "makes the verdict INVALID". The command ends with 1 and the guard cancels the evaluation and the verdict, so nothing writes INVALID. If the same command is then run again it predicts again; if that attempt is finite the gate goes on to a valid verdict, and the first attempt is on record only in `attempts.log` and the queue's log. A supervised run's non-finite stop is final in the code; this one is not. b. These networks gave finite fields on G-C2.2's members, so values that are not finite now would come from a member of the third sample or from the host. The text files this under INVALID, "no part is read", and says nothing of what follows an INVALID. A referee will read that as a failure of the label-free networks on a fresh member that leaves the judged outcomes.

**How found.** Executed (`exit3.py` K1), with `predict` made to return no finite predictions for seed 6: `predict-label-free` printed `{"status": "non-finite predictions", ...}` and ended with "the predictions are not finite; stop and report"; `evaluate` and `verdict` ended with 1, the verdict INVALID. The same `predict-label-free` command again printed `{"status": "finished", ...}` and ended with 0.

**Repair.** In `predict_label_free`, return the recorded history when its status begins with "non-finite", as `train` does. In "Interpretation", say that an INVALID from predictions that are not finite is reported with its cause, as a failure of a label-free network on this gate's members, and that after an INVALID or INCOMPLETE outcome the third sample is spent.

### 21. SHOULD FIX. Part 2: the supervised arm trains with settings chosen for the label-free loss, and the text does not name this as a limit

**Where.** `docs/PRESPEC_G-C2.3.md` lines 13, 22, 118, 172, 182.

**What is wrong.** The learning rate, the schedule and the clipping are those of the earlier gates; the stability recipe (beta2 of 0.99 and the cap on the encoder's gradient) was developed on label-free runs (`probes/c2_dev`); line 64 says that no supervised run of this size exists. Part 2 therefore compares a developed method with a baseline that was not tuned. Line 172 states the matching point for the reading (the condensed reading was developed on the label-free networks); nothing states it for the training settings. Related, and also unstated as an asymmetry: the label-free arm consists of three runs known to have finished and passed G-C2.2, and cannot lose a seed here; a supervised seed can, and then counts with infinite errors.

**How found.** Read; configuration printed (`lr 0.001`, `beta2 0.99`, cap factor 5.0 over 256 steps).

**Repair.** One sentence under "What the gate does not show" (nothing about a supervised arm whose learning rate, schedule or stabilisation were chosen for the supervised loss), and the same clause in the last sentence of "Part 2" of the interpretation.

### 22. MINOR. Outcomes of the code that the text still does not cover

a. A label-free seed in which a member of the third sample has no metrics. The text fixes part 1 only (line 144; `c23/config.py` line 119). In part 2 the code lets that seed enter the label-free medians with infinite errors (`c23/evaluate.py` lines 313 to 315), which line 152 says of a supervised seed only. Executed (`sc4.py`): one such seed moves the label-free statistics to the larger of the two other seeds; two such seeds give both ratios 0 and "supervised closer".
b. Part 1 FAIL by that rule: the sentences of line 170 do not fit ("did not separate the large errors"; "the failing criterion and the pairs concerned are listed"). The verdict then holds no `self_check` block at all (executed, `sc4.py` L1).
c. PASS with R NOT EVALUABLE: line 168 fixes the wording when "R does not hold" only.
d. Line 174, "INVALID, INCOMPLETE: reported as such; no part is read", against line 187: when part 2 is INCOMPLETE, part 1 stands and is read. Write "a part that is INVALID or INCOMPLETE is not read".
e. An arm with a seed without numbers has no `by_level` and no reported self-check (`tests/test_c23.py` line 426 asserts it); line 172 promises "the medians at each level" with the wording.
f. Runbook lines 127 and 156: the evaluation and the supervised runs "go on unless the owner stops" them. The text does not say that part 2 then stays INCOMPLETE.
g. `c23/config.py` line 127, "part 1 is INCOMPLETE while a label-free run has no predictions", beside line 113 (without finite predictions: INVALID). The code's rule is: INCOMPLETE while a label-free run has neither predictions nor a non-finite end.

### 23. MINOR. "Interpretation", part 2: the supervised arm's raw reading is stated with the wording only if the wording is "label-free closer"

`docs/PRESPEC_G-C2.3.md` line 172. The code computes the two ratios in every case (`c23/evaluate.py` lines 385 to 388) and line 160 reports them. If the judged wording is "comparable" or "mixed" while the raw reading of the supervised arm gives "supervised closer", the stated wording is the one more favourable to the label-free arm and the text need not say so. Read. Repair: state the two ratios with the wording in every case, and say when they give another wording.

### 24. MINOR. Statements of the pre-specification without a record in the tree, or slightly wider than what is so

a. Line 65, two members of seed 7 solved at the eight label levels: no script and no record in the tree (search). My own run: 12 members of seed 101 on the gate's mesh, every level converged, every label check within its limit (largest residual 5.1e-11 against 1e-6), 2 iterations at 0.1 mm in each. A failed training label ends part 2 (line 187), and nobody has solved 0.1 mm on the gate's mesh with the host's solver. A pilot of some tens of members of a seen seed takes minutes on the host; it could be a sixth job before the stamp, with its record in the tree.
b. Line 122, "on a processor a supervised step took about a third of a label-free step": no record in the tree. Remove it when the host's time is filled in, or keep the record.
c. Line 128: the comparison of the fields "does not cover the reference solutions". It does not cover the exports either, which the gate also makes again (line 110) and from which the fields are predicted. The host check covers both. Write "the exports and the reference solutions".
d. Line 30, "every judged level but the largest lies between two labelled levels, as in G-C2.1": in G-C2.1 that held for 1 to 6 mm only.
e. Line 42, what drafts 0.2 and 0.3 add to draft 0.1 "is listed in the review's record": the author's notes list what changed after round 1. I have seen no list of what draft 0.2 added to draft 0.1, and my reports hold none. If the owner is to approve the additions, the list should exist in one place.
f. Line 181, "none of their pairs is flagged": true of the two runs on a processor (the author's and mine: 0 of 4 pairs flagged). The host's run does not exist yet; tie the sentence to a record.

### 25. MINOR. `identity()` skips a whole array of values when a reference value in it is infinite (host check and tests only)

**Where.** `tree2/joint/c23/evaluate.py` lines 148 to 155; `c23/smoke.py` lines 60, 61 expect infinite stand-in values.

**What is wrong.** The gate itself is not affected: its twelve reference values are finite, and an infinite recomputed value gives an infinite difference (executed). In a reduced configuration one infinite pair of four makes a seed's 90th percentile infinite. Then infinity minus infinity is not a number, `np.max` returns it, and `max(worst, nan)` keeps `worst`: the other seeds' differences in that array are ignored. Executed: reference [inf, 10, 20] against [inf, 50, 90] gives `largest_difference 0.0, ok True`. The host check's `evaluate.identity.ok` can be true without the comparison having been made.

**Repair** (tried on a copy): count equal infinities as 0 and any other difference that is not a number as infinite.

### 26. NOTE. The first record of part 1: what the code does not catch

- A label-free rows file changed by hand with its `inputs` left alone is accepted, and `part1_same_as_first` stays true unless the change moves something that part 1 holds. Executed (`sc1.py` E2): one error of the judged set halved gives true and exit 0, also with `--final`, while the label-free medians by level changed. Changes of the kept file outside part 1 give true as well (D5). The operator's SHA-256 comparison of section 8 and the audit cover both. The label-free statistics enter part 2, so the SHA-256 of `rows_label_free.json` could be added to what `_part1` compares.
- `evaluate --arm supervised_512` before the first verdict writes a rows file with every run missing; the first record is then refused until that file is deleted by hand (executed, A1, A2). The runbook is silent. Not reachable in the queue's order.
- The rule reads the ledger of this data folder, not the label files (executed, B2). Passing it wrongly needs a deliberate act.

### 27. NOTE. The interlock: what it does not cover

- A caller who imports `c23.data.generate` or `members`; `c23/smoke.py`, the tests and the probes, which need no stamp by design.
- Cached bytecode. The interlock hashes sources; Python runs a cached file when its recorded time and size match the source. Executed in a scratch copy with a valid stamp file: with a cache made from a `c23/config.py` whose threshold was 0.0054 and whose size and time equalled the stamped source, `sha256sum -c` gave 41 OK, `write-config` printed `code as stamped: True`, and the process ran with 0.0054. This cannot arise by accident in a fresh `gate3/`. Suggestion: `-B` in the queue's start line and a check that `gate3/` holds no `__pycache__` before section 1.
- Files that are not in the list: seven other files of `fejoint/` (none is loaded: executed), extra lines of the stamp file (ignored: executed), and the six repository lines (the configuration pins those files, and `predict-label-free` and `train` verify them).
- `write-config` ends with 0 whatever its three lines say, so the guard after job 86 passes; `generate` takes no `--config-sha`. With a tree whose code and stamp file agree with each other and are not the tag's, `generate` would draw before any command compares the configuration hash. The protection is the tag and the operator's reading of section 1. Suggestion: an optional `--config-sha` for `write-config` and `generate`.
- A malformed line of the stamp file ends in a traceback (ValueError), still with code 1 (executed).

### 28. NOTE. Runbook and queue

- After a guard has stopped the queue the runbook does not say how it is continued. The cancelled jobs have done files, the generator refuses names that exist ("refused: 87_c23_generate.job.json exists already", executed), and set C alone stays refused while `93z_c23_guard.done.json` holds the code 1 of a first attempt.
- Sections 3 and 6: the label jobs use the same pool of worker processes as the evaluation, so the warning of line 128 holds for them too.
- `verdict` on a runs folder that does not exist ends in a traceback; on a folder without a `verdict.json` it writes an INCOMPLETE one there (executed, I3).
- Line 74 asks for `evaluate.identity.largest_difference` only if the host check fails. The tolerance there is about 1% of the stand-in values, so the number should be reported in any case, as line 128 of the pre-specification plans.

### 29. NOTE. `probes/c23_precheck/repredict.py`

- Lines 96 to 102: a state file whose SHA-256 is not the pinned one is still unpickled, and only `state_is_the_pinned_one: false` is recorded. The gate's own command refuses such a file before reading it.
- It ends with 0 when the fields differ, and set P has no guard: the operator must read `all_identical`.
- `--out` is refused only if it exists; a new folder inside G-C2.2's data or runs folder would be accepted. The job file gives `pre3_records/repredict`.
- Predictions that are not finite end in a traceback and no report (read).

### 30. NOTE. Tests

- `test_the_entry_point_runs_as_a_process` (line 504, and its like in `tests/test_c22.py`) starts Python with `-I` and so writes `__pycache__` folders into the tree under test. Add `-B`.
- No test for the two new stops of the label-free arm at the command line (`c23/__main__.py` lines 146 and 158 for a run that is not finite), and none for 22a. I executed them.
- The command-line test says "in the runbook's order" but runs `evaluate --arm supervised_512` before the first verdict and deletes its rows file at line 728 without a comment.

### 31. NOTE. Smaller things

- `training_labels_sha256` is in each supervised history, which is returned, but not in the rows file or the verdict (`c23/evaluate.py` lines 217 to 219 copy a fixed list of keys); nothing compares the three runs' values.
- "Authority": the six points put to the owner end with "the nights on which the host is free" in draft 0.3 and with "the three state hashes read from the owner's record of the archive" in draft 0.2. I cannot see the note; check the list against it once more.
- `gate_prep2/make_stamp_c23.py` line 45 writes the stamp file with the platform's line ends, and the tool writes bytecode into the tree it stamps. Give `newline="\n"` and run it with `-B`.

## 3. Answers to questions a to i

**a. The interlock.** No command of `c23/__main__.py` but `write-config` ran with code other than the stamped code. Executed: refusal with no file, a wrong hash, a missing line, an empty file, a changed file of G-C2.2 (`fejoint/hex8i.py` named), and from the unpacked draft archive; `predict-label-free` and `train` without a stamp were read only (the same check at lines 123 to 125 precedes them). An import trace over all commands loaded 38 files of `tree2`, none outside the 35 and the six repository files (`trace2.py`). The order of the stamp is sound: the tool asserts that the 34 files of G-C2.2's stamp are unchanged and that the repository pins agree, and writes a file that `sha256sum -c` accepts (41 OK on a copy). The stamp file proves only that code and file agree; the outside anchors are the tag, the archive's hash and the configuration hash in the pre-specification. Outside the 41 files, a result depends on the Python environment (read by the operator in 0e), the pinned state files, the arguments of the job files, and bytecode caches. Tests, probes and queue tools decide no result. Not covered: finding 27.

**b. Exit codes and guards.** Executed codes: job 85 host check 0 only after its last line; 86 `write-config` 0 unless a repository file differs; 87 `generate` 0, 1 on any refusal; 88a to c and 94a `label` 0 also when a member did not converge; 88d and 94b `check-labels` 1 unless `"ok": true`; 89 to 91 0 only for `finished`; 92 0 only if the three runs are finished; 93 0 only with identity OK and part 1 equal to the kept record; 95 to 97 0 for `finished` and for a non-finite stop, 1 for an error; 98 0 unless a run is missing; 99 0 only with identity OK, the kept part 1, both arms evaluated and no run missing. With the real guard on the job files of set BC (`qsim.py`, 13 outcomes), each non-zero code cancelled every later job; a label job that ends with 1 is caught by the check that follows it. In set BC I found no outcome after which the training members are labelled or the supervised arm is trained without a valid first record: code 0 of job 93 implies that the kept file exists and equals this verdict's part 1 with the identity OK.

**c. The first record.** Executed (`sc1.py`, `cli2.py`): the runbook's order; `verdict` before any evaluation (INCOMPLETE, no record, code 1); `verdict` twice (same bytes, code 0); `evaluate --arm label_free` twice (same bytes); a training member in the ledger before the first verdict (record refused, code 1); the kept file deleted before the training labels (written again with the same bytes) and after them (not written again, code 1); the kept file edited inside part 1 (reported, code 1). I found no order in which a record is written after anything of the supervised arm could have been seen: training needs all training labels in the ledger, and one such entry blocks the record. Changes that leave part 1 as it was are not reported by the code (finding 26). A verdict while a label job writes the ledger was read only: the ledger is replaced in one move after each member. The JSON round trip is safe: executed with infinities (my kept files hold four), an integer against a float, another key order, and a not-a-number, which compares equal in this Python and cannot occur in part 1 by the code as read.

**d. Identity.** I found no state of the runs folder in which a part gets a word although the identity is not shown. Executed: a missing label-free run (NOT EVALUATED, INCOMPLETE), a run without finite predictions, a member of the identity set without metrics, values off by more than the tolerance (all INVALID), rows from other files (refused). The identity values of `c23/config.py` equal G-C2.2's returned verdict in both readings (executed). The prediction command refuses a state of another hash or seed (the test passes).

**e. Label levels.** Yes in the code and in both reduced configurations: the host check labels at 0.1, 0.75, 2.5, 8 mm and reads at 0.1, 0.5, 4 mm; the tests' own configuration keeps the eight levels. Line 118 says exactly what a step uses: `rng.choice(8, size=4, replace=False)` and the mean of the squared difference of the physical displacement over (D + delta) (`c2/train.py` lines 104 to 114, read). Still unfair and unstated: finding 21.

**f. The check before the draw.** With the job's arguments it cannot write into G-C2.2's folders: an existing `--out` is refused before anything is loaded; a missing state half way leaves only the new folder's partial files; a hash over names, sizes and times of the base folders was the same before and after (executed). Equality of the fields supports the sentence of line 128 with one addition, the exports (24c). What it says of the host check is so: read in `c23/smoke.py`, and executed, with a largest difference of 0.0.

**g. The pre-specification as a referee.** Contradictions: line 174 against 187 (22d); `c23/config.py` line 127 against 113 (22g). Numbers: all that I could check agree: 0.80% and 3.66% (0.00797, 0.03664), the twelve identity values, 113 and 118 pairs with 1,005 and 990 readings, the areas, 644, 132, 4,096, 307,200, 5,544, 265 s, 117 s, two hours, and "about 22 hours, of which about 18" (4.35 h in G-C2.2's ledger; my pilot's iterations at the eight levels are 1.06 times those of the seven judged levels, which gives 17.6 h). Freedoms left open: what follows an INVALID (20); the owner's stop of a run (22f); the identity tolerance, which line 128 allows to change before the stamp. Outcomes not covered: 22. Statements wider than what was done: 24. Apart from these, [OPEN 3], [OPEN 6] and the eleven bracketed places (lines 3, 30, 42, 69, 79, 83, 95, 122, 128 twice, 194), I found nothing undecided.

**h. The runbook.** The 19 `PY` commands equal the generator's 19 gate jobs token by token (`tokens.py`); 15 guards. Counts hold: 644 members, 132 and 644 labels, 35 hashes and six repository lines (44 lines printed), 68 tests collected, eight levels, 4,096 solutions. The quoted outputs appeared as written on the reduced configuration. After an interruption: the host check needs a new folder; `generate` and the label jobs keep what is written; the predictions, the evaluations and the verdicts start again; a training run resumes from its last epoch (the host check's resumed run equalled the uninterrupted one here, differences 0.0). Remarks: finding 28. `@@CONFIG_SHA@@` stands in 11 lines.

**i. What must not be public.** Nothing found in the 21 changed files: the word that the brief lists under H 0 times, no path of a working machine, no address, no <a name that the brief lists under H> outside `fejepa` and `FEJEPA_REPO`, no personal name known to me, no dash used as punctuation, British spelling throughout. The only text outside ASCII is the three authors' names in a literature reference of `README.md`. `queue_tools_copy/pause.py`, which is not returned, still holds the word once. Not on the list, for the owner to decide: "Authority" gives the times of night of the owner's messages and their language.

## 4. Checked and found correct

- Snapshots at the start and at the end: `tree2` 34 OK, `gate_prep2` 3 OK, `tree` 13 OK; no file in the trees is newer than the brief (executed).
- Configuration hash `5c27fb8f...25cf6`, as line 79; it differs from G-C2.2's configuration only in the listed keys (executed).
- The runbook's order through the command line, with every exit code (executed).
- The host check of `tree2`: "smoke test of c23 passed" after 473 s; identity OK with largest difference 0.0 and tolerance 1.0119; words FAIL, NOT EVALUABLE, "supervised closer"; `same_with_workers` true. This agrees with the author's run (executed, under a guard on the family seeds).
- Tests: `test_c23.py` 17 passed; `test_c22.py` 20 passed in 612.58 s (executed).
- The stamp tool on a scratch copy whose third seed I had set to 102 so that it could not draw; the draft archive of `make_pre3.sh` holds no `docs` folder and its commands refuse (executed).
- The suite cannot draw the sample after the stamp either: the command-line test asserts the reduced configuration's hash on `write-config` before `generate`, and the process test runs `write-config`, `verdict` and `evaluate` only (read).
- The record `gate_code_on_seen_samples.txt` agrees with lines 54 and 68 (read).
- The new `ledger_sha256` works on G-C2.2's returned ledger, whose time field holds text outside ASCII (executed).

## 5. Not checked

- Anything on the host or on a GPU; the level 0.1 mm with the host's solver; the supervised run at full size.
- `test_hex8i.py`, `test_contact.py`, `test_c2.py`: 31 tests passed in a run that a restart of the machine cut off before its summary line; I did not repeat them.
- `gate_code_on_seen_samples.py` (needs G-C2.2's deposit) and the three timing probes were not run in this round.
- The three pinned state hashes: no record of them is in the tree; the check before the draw will show on the host whether files with these hashes reproduce G-C2.2's predictions.
- The owner's messages, the note of 03:52 and draft 0.1.
- The queue's runner, which is not in the review folder: my stand-in runs jobs in the order of their names and skips a job with a done file.
- The new code on Windows (line ends, file locks): read only.

## 6. Notes for the coordinator

- The only change I made in `tree2/`: I removed the `__pycache__` folders that the two test runs had written into `joint/c23`, `c22`, `c2` and `fejoint`. They held `.pyc` files only.
- Left behind: `scratch/round2/` (42 MB), the scripts named above and their data. I deleted every stamp file that I or the tests had made there; none is left anywhere in the review folder.
- In the sandbox two Pardiso solves of one member on the gate's mesh differed in the last bits (relative 1e-14). This does not touch any criterion, and the host uses scipy's solver.
- The session was interrupted twice; the second time the machine restarted.
- The personal names that I searched for under i came from the session's context and from the user-memory snapshot given to me at the start. I do not write them here. No other fact of this report comes from memory.

---

# What the author did after round 2

Written by the author of the reviewed files, not by the reviewer, on 18 November 2026, and handed to the reviewer with round 3. Paths are relative to `joint/`. "Tree 3" is the state that round 3 reviewed; its pre-specification is draft 0.4.

20. *A label-free run without finite predictions.* Done as proposed. a. `c23/train.py`, `predict_label_free`: a recorded end without finite predictions is returned and nothing is predicted again, as `train` does for a supervised run. The runbook, section 4, says that the end is final and has the operator queue the evaluation and the verdict once more, without guards, so that the INVALID verdict is written. b. The pre-specification, "Interpretation": an INVALID is reported with its cause; one that comes from predictions that are not finite is reported as a failure of a label-free network on this gate's members; an outcome that is INVALID, and a part 2 that is INCOMPLETE by a stop condition, are final, the third sample is spent, and anything computed on it afterwards is exploratory. The configuration's `criteria` carry the same rules (`identity`, `final`). Test: `test_the_command_line_stops_for_good_when_a_label_free_run_has_no_numbers`.
21. *The supervised arm's training settings.* Done as proposed, in the text only. "What the gate does not show" has two new points: nothing about a supervised arm whose settings were chosen for the supervised loss, and the unequal risk of the two arms (the label-free arm cannot lose a seed to its training here). "Interpretation", part 2: any wording says that the supervised arm was trained with the label-free arm's settings and was not tuned, and the last sentence names such an arm among what the wording does not carry to. The settings themselves are not changed: the owner agreed to the stability recipe in the supervised arm, and tuning the supervised arm would be a study of its own.
22. *Outcomes not covered.* a. "Seeds without numbers" now says that a seed of either arm in which a member of the third sample has no metrics enters both medians over seeds with infinite errors (`criteria.member_without_metrics`); tested for one and for two such label-free seeds. b. "Part 1, FAIL" has a sentence for a FAIL that comes from a member without metrics. c. "Part 1, PASS" has a sentence for R NOT EVALUABLE. d. "A part that is INVALID or INCOMPLETE is not read; when part 2 is INCOMPLETE, part 1 stands." e. "The medians at each level for every arm whose three runs all have numbers." f. "Stop conditions": a command that the owner stops and does not let run again leaves INCOMPLETE what needs it; the runbook says so in sections 5 and 7 (`criteria.not_resumed`). An interruption that comes from the host is named as no stop of the gate. g. `criteria.incomplete` is rewritten to what the code does.
23. *The supervised arm's raw reading.* Done as proposed: the two ratios are stated with the wording in every case, and the text says when they give another wording.
24. *Statements without a record.* a. The pre-specification now names the three pilots of the eight label levels and their records: the author's two members of seed 7 and the reviewer's twelve of seed 101, both on a processor with another linear solver than the host's (the reviewer's is in the report of round 2; the author's was made again with the new probe, and its report is `probes/c23_precheck/records/pilot_labels_processor_seed7.json`), and a pilot on the host with its solver, 32 members of seed 101, by the new probe `probes/c23_precheck/pilot_labels.py`, which is a sixth job before the stamp and whose report goes into the return package. The probe changes the gate's configuration in the seeds and the numbers of members only, and refuses to sample any family seed but 7, 8, 101 and 102. b. The sentence on a third of a step is removed. c. "The exports and the reference solutions". d. "In G-C2.1 that held for the judged levels from 1 to 6 mm." e. The list exists: "What drafts 0.2 to 0.4 of the pre-specification add to draft 0.1", at the end of this file; "Authority" refers to it. f. The sentence is tied to the two runs on a processor before the stamp.
25. *`identity()` and infinite values.* Done as proposed (`c23/evaluate.py`): equal values count as equal also when both are infinite, and any other difference that is not a number counts as infinite. Tested with the reviewer's case.
26. *The first record of part 1.* First point: done. The verdict holds the SHA-256 of each rows file it read, and part 1 as kept and as compared includes that of the label-free rows; a rows file changed by hand with its `inputs` left alone is now reported (tested). Second point: done. `evaluate_arm` refuses to run, and writes no rows file, while no run of the arm has ended; the command-line test no longer deletes a rows file. Third point: left as it is.
27. *The interlock.* Bytecode: `c23/__main__.py` and `c23/smoke.py` tell Python at their top to write no bytecode, which holds for spawned worker processes too, since they run the top level of the main file first; the runbook checks in 0b and in section 9 that `gate3/` holds no `__pycache__` folder. The queue's start line is not changed. Configuration hash: `generate` now needs `--config-sha` and refuses another hash before it draws; `write-config` takes `--config-sha` and then ends with a code other than 0 unless the hash is the given one, the state files are pinned and the code is the stamped code; the job files give both (jobs 86 and 87). A malformed line of the stamp file is a refusal with a message. A caller who imports the functions, and files outside the list, are as before.
28. *Runbook and queue.* A paragraph "After a stop" in "How the commands are run": what is final, what is continued, and how (the done files moved into the records, the jobs written again with the generator's new `--from`). The warning about a killed worker is repeated for the label jobs. `verdict` refuses a runs folder that is not there or that holds no run and no rows of this gate, and writes nothing (tested). The host check's `largest_difference` is reported in any case.
29. *`repredict.py`.* A state file whose SHA-256 is not the pinned one is not read. `--out` inside G-C2.2's data or runs folder is refused. Predictions that are not finite are recorded and the next seed follows. The exit code stays 0 when the fields differ: the runbook has the operator read `all_identical`.
30. *Tests.* `-B` in the process test of `tests/test_c23.py`; the like test of `tests/test_c22.py` is left, as that file is G-C2.2's. A test of the two stops of the label-free arm at the command line and of the supervised arm's missing run; tests of 22a, 25, 26 and 28. `tests/test_c23.py` has 18 tests.
31. *Smaller things.* `training_labels_sha256` is copied into the rows, and the evaluation of the supervised arm refuses a run trained on other labels than those now in the ledger. "Authority" was compared with the note of 03:52 once more: its six points are those that draft 0.3 lists, ending with the nights on which the host is free; draft 0.2 was wrong there. The stamp tool writes the stamp file with one kind of line end and leaves no bytecode.

The reviewer's remark under i, that "Authority" gives the times of the owner's messages and their language: the pre-specifications of G-C2.1 and G-C2.2 do the same; it is left for the owner.

The configuration hash of tree 3 is `29149f2e0f3708648c27f40bd1ac99942841303b279b3bd8a6705813e7dda5b8`: the `criteria` texts changed, no number did.

---

# Round 3 (18 November 2026, delivered at about 09:50 GMT)

# Review of gate G-C2.3, round 3

**Nothing that I found blocks the stamp.** Findings 32 to 34 are small and are worth repairing before it, because the runbook and the tests are frozen with the tag; they touch the runbook, one test and the generator, not the gate's code or its configuration.

How to read this report. Paths are relative to the review folder of the brief. "Executed" means run by me in this round, on a processor, with reduced configurations and the family seeds 7, 8, 101 and 102 only. "Read" means read and not run. No member of seed 20261118 was drawn, exported or solved; no stamp file was written into `tree3/`; nothing in `tree/`, `tree2/` or `tree3/` was changed. Snapshots at the start and at the end: `tree3` 36 OK, `gate_prep3` 3 OK, `tree2` 34 OK, `tree` 13 OK; no bytecode folder in any tree. My scripts and outputs are in `scratch/round3/`.

## 1. Findings 20 to 31

20. **CLOSED** as raised; a gap in its repair is finding 32. Executed (`cli3.py`, case N1): with the predictions of seed 7 made not finite, `predict-label-free` ends with 1; the same command again ends with 1 and predicts nothing (`attempts.log`: "returned: non-finite predictions"); `evaluate` and `verdict` end with 1, and the verdict is INVALID and kept. Read: pre-specification lines 126, 174, 192; runbook line 122; `criteria.identity`, `criteria.final`.
21. **CLOSED.** Read: lines 172, 183, 184. The settings themselves are not changed: accepted. I had asked for the limit to be named, not for a tuned arm.
22. **CLOSED** a to g. Read: lines 152, 168, 170, 172, 174, 193, 194; the `criteria` of `c23/config.py`; runbook lines 131, 160. Executed: the tests for one and for two label-free seeds with a member without metrics pass. One loose end is in 36.
23. **CLOSED.** Read: line 172.
24. **CLOSED** a to f. a, executed: `pilot_labels.py` from the unpacked draft archive, two members of seed 101: every level converged, `"ok": true`, exit 0; its exports equal those of my own pilot of round 2, and the iterations at each level are the same. The record of the author's run is in the tree and names tree3's configuration hash. b, c, d, f, read: lines 122, 128, 30, 181. e: the list exists; two omissions are in 37.
25. **CLOSED.** Read: `c23/evaluate.py` lines 148 to 160. Executed: the test with my case of round 2 passes ([inf, 10, 20] against [inf, 50, 90] now gives 70 and is not ok).
26. **CLOSED.** Executed: one error halved by hand in the label-free rows file, its `inputs` left alone: the verdict ends with 1; with the file put back, 0. `evaluate --arm supervised_512` before any supervised run: "no run of the arm supervised_512 has ended: there is nothing to evaluate, and no rows are written", exit 1, no rows file, and the first record is then written as usual. The third point is left: accepted; it needs a deliberate act.
27. **CLOSED** for what was taken up. Executed: answers c and d below; a stamp file with a line of three words gives "... has a line that is not a hash and a file name; refusing to run". A caller who imports the functions is as before: accepted.
28. **CLOSED**; remarks on the new paragraph are in 34. Executed: `verdict` on a runs folder that is not there: "holds no run and no rows of this gate; nothing is written there", exit 1, nothing made. After a stop for a reason of the host, with the files moved and `--from` used, the queue ran to its end, and set C was accepted again (`qsim3.py`). Read: runbook lines 19, 77, 111, 144.
29. **CLOSED.** Executed (`repredict3.py`, on reduced base folders): a state that is not the pinned one is not read and nothing is written for it; predictions that are not finite are recorded and the next seed follows; `--out` inside the data or runs folder is refused; the base folders are unchanged. The exit code stays 0 when the fields differ: accepted; the runbook has the operator read `all_identical`, and the set has no guard.
30. **CLOSED.** Executed: `tests/test_c23.py`, `18 passed, 1 warning in 681.80s`, and no `__pycache__` folder in `tree3/` afterwards. `tests/test_c22.py` is left: accepted; step 0c runs in a full checkout, not in `gate3/`.
31. **CLOSED.** Executed: the supervised rows and the verdict hold `training_labels_sha256`; with one training member's ledger entry changed, `evaluate --arm supervised_512` ends with "supervised_512_s5 was trained on other labels than those now in the ledger"; the stamp tool on a scratch copy writes 41 lines without carriage returns, `sha256sum -c` gives 41 OK, and no bytecode is left. "Authority" agrees with `draft01/NOTE_0352_points.md` in the recommendation, the six points and the two things to be done. I see the note in the author's English rendering only.

The remark under i, on the times and the language of the owner's messages: accepted as the owner's to decide.

## 2. New findings

### 32. MINOR. If the state without finite predictions is that of seed 5 or 6, the two commands of section 5 write INCOMPLETE, not INVALID

**Where.** `RUNBOOK_C23.md` lines 122 and 19; `docs/PRESPEC_G-C2.3.md` line 192; `c23/evaluate.py` lines 353 to 360.

**What is wrong.** The guard after a prediction that is not finite cancels the predictions that follow. The verdict says INVALID only when no label-free run is missing; while one is missing it says NOT EVALUATED and INCOMPLETE and keeps no record. So "the operator queues the two commands of section 5 once more, without guards, so that the INVALID verdict is written" holds only if the state concerned is the last one, seed 7. "After a stop" says that such a stop "is not continued", so by the runbook the two other predictions are never made.

**How found.** Executed (`cli3.py`, cases N1 and N2). Seed 7 not finite: `"identity": "INVALID", "self_check": "INVALID", "ranking": "INVALID"`, kept in `verdict_part1.json`. Seed 5 not finite, seeds 6 and 7 not predicted: `"identity": "NOT EVALUATED", "self_check": "INCOMPLETE"`, `"missing": ["label_free_s6", "label_free_s7", ...]`, no kept file. After the two other predictions: INVALID, kept.

**Repair.** In the runbook: the operator queues the predictions that the guard cancelled and then the two commands of section 5, all without guards, and "After a stop" names this as what is still run after this final stop. Or, in `verdict`, a label-free run with a non-finite end decides INVALID before the test for missing runs.

### 33. MINOR. The suite calls `generate` with the gate's real configuration three times, each behind a single refusal

**Where.** `tests/test_c23.py`, `test_commands_refuse_code_that_is_not_the_stamped_code`: lines 522 to 524 (no stamp file, the right configuration hash), line 533 (one wrong hash in the stamp file, the right configuration hash), line 549 (new: a valid stamp file and a wrong configuration hash).

**What is wrong.** Each call proves a refusal by attempting the act with seed 20261118 at stake. If a later edit weakened the refusal concerned, running the suite would draw and export the held-out sample into pytest's temporary folder before the test failed. This is the pattern of round 1's 13d, one level up. The first two calls were in `tree2` already, and I did not raise them in round 2.

**How found.** Read. My run of the file was made under a plugin of my own that refuses every family seed but 7, 8, 101 and 102: 18 passed, and the plugin counted 54 draws, all of these four seeds.

**Repair.** In this test, set `c23.config.config` to the small configuration, as the two command-line tests do, or put in place of `c23.data.generate` a function that fails the test.

### 34. MINOR. "After a stop" against the guard and the generator's `--from`

a. Runbook line 19 has the operator move "the job files and the done files of the failed stage and of the cancelled jobs". The guard that stopped is neither: it ran and ended with 1. Executed (`qsim3.py`): with only the listed files moved, the generator answers "refused: 92z_c23_guard.job.json exists already"; with the guard's two files moved as well, `--from` writes the jobs and the queue runs to its end. The stage's continuations after a pause and the log of the failed attempt, which the same job name writes again, are not named either.
b. Line 19 lists "a failed check of labels" among the final stops. The pre-specification's stop is a label that does not converge or fails its checks. The check also fails when labels are missing because a label job was cut off by the host; by line 194 of the pre-specification that is no stop of the gate. Say which lines of the check's output make the stop final (`"converged": false`, a limit not kept) and which do not (`"missing"` alone).
c. The check that part 1's verdict ended with 0 is applied to set C only (`gate_prep3/make_jobs_c23.py` line 153). Executed: after a final stop at the verdict of part 1, `BC ... --from 94a_c23_label_train` writes the jobs of part 2 and they run; `C ... --from 94a_c23_label_train` is refused. The training members would then be labelled, and after that no first record can be written. Apply the check whenever the first job written sorts after `93z_c23_guard`.
d. Line 122 has the operator queue two commands "without guards". The generator writes every job with its guard, and guard 92z would cancel the verdict, since the evaluation ends with 1 there. Say that the two job files are written by hand and under which names, or give the generator a set for them.

### 35. NOTE. The label-free rows file after the first record

See answer b. If `evaluate --arm label_free` is run again after the first record and writes other bytes, every later verdict ends with a code other than 0, and by line 19 that stop is final. Nothing in the runbook runs it again, and here the bytes were the same. One sentence in "After a stop" would close it: once `verdict_part1.json` exists, job 92 is not written again; if the rows file is lost, report.

### 36. NOTE. Two places where text and code differ slightly

- Pre-specification line 83: "`generate` and every command after it also refuse to run unless the configuration hash given to them is that of the code". `label` and `check-labels` take no hash (read: `c23/__main__.py` line 137; executed: the parser). The stamp file and the manifest cover them. Name the commands.
- Line 174 and `criteria.final` call final an INVALID outcome and a part 2 that is INCOMPLETE by a stop condition. A part 1 left INCOMPLETE by a stop condition (a held-out label that fails, line 188; the owner's stop of the label-free evaluation, line 193) is not named, while the runbook's line 19 calls a failed check of labels final.

### 37. NOTE. The list of additions

Executed: a word-by-word difference of draft 0.1 and draft 0.4. The seventeen items are in the drafts as described, and the last sentence holds: the threshold, S1 to S3, the limit of R, the band, the seeds and the samples are those of draft 0.1. Not in the list: (i) line 194, an interruption that comes from the host is no stop of the gate and the command is run again; this rule decides whether a stopped gate goes on; (ii) line 118 and runbook line 168, the training members' files are compared with the manifest and the ledger before a run starts or resumes, and a run is neither resumed nor evaluated on other labels. Item 14 names the two members of seed 7 only; line 65 now names three pilots.

### 38. NOTE. Smaller things

- The new refusal of the supervised evaluation compares ledger entries, which hold `seconds` and `time`. A training label solved again with the same numbers counts as other labels, and the finished runs can then not be evaluated. It needs a lost label file to arise. Read.
- `pilot_labels.py`: a solve that raises ends the probe with a traceback and without its report. Read.
- `make_jobs_c23.py`: `--from` without a name ends in an IndexError; `--from` a guard's name writes a guard that cancels everything after it. Executed. Harmless.
- Runbook line 13 still names only one of the two refusals of `verdict`.

## 3. Answers a to e

**a.** No repair opens a defect in what the gate judges. The outcomes that the repairs change are stated in the texts: a label-free end without finite predictions is final; `evaluate` refuses while no run of the arm has ended and refuses a supervised run trained on other labels (runbook line 168); any change of the bytes of the label-free rows file after the first record ends later verdicts with a code other than 0. Not stated: finding 32, and the generator's gap in 34c.

**b.** No, if the runbook is followed. The file is written by `evaluate --arm label_free` only, once, before the first verdict; a restart reruns the interrupted command only; "After a stop" starts again from the failed stage, which is job 92 only while no record exists. If the command is run again all the same, the bytes were the same here: executed three times (two workers twice, one worker once), and once more for the supervised rows. Another layout of the same content is reported as a change (executed), so the code's own writer must stay the only writer. On the host: the solver is scipy's sequential one, each worker has one thread, the rows are sorted by member, and G-C2.2's host check found the rows of one worker and of several equal on its reduced configuration (read in its report). G-C2.2's audit found the exports equal to the last bit on another machine, and the labels equal to 1e-15 only (read). No repetition on the same machine with the gate's mesh is on record, so I expect equal bytes on the host and cannot show it.

**c.** Yes, in every process the gate starts, when the script is started by its path, as the runbook does. Read (`multiprocessing/spawn.py` and `subprocess.py` of Python 3.13 here; the host has 3.12): the child's command line repeats `sys.flags` only, so the assignment is not passed on; the child sets it itself, because `prepare()` runs the main file's top level before the process object and any task are unpickled. Executed, in a scratch copy whose pool is spawned, with the gate's own `c23/__main__.py label --workers 2` started with `-I` and without `-B`: no `__pycache__` anywhere; with the flag's line removed, four folders; with the flag set inside `main()` only, the workers wrote caches of `c2/` and `fejoint/`. So it is the top-level place that covers the workers. It would not cover them if the gate were started with `-m`. It breaks nothing: it stops writing only. An existing cache is still read, so the runbook's `find` in 0b and in section 9 stays necessary.

**d.** Yes. `write-config` writes the file and prints all lines first; a repository file that differs raises before; then, given `--config-sha`, it ends with 1 unless the hash is the given one, the states are pinned and the code is the stamped code. Executed: right hash with a stamp 0; wrong hash 1; no stamp 1; malformed stamp 1. `generate` requires the option (without it argparse ends with 2); the order is state hashes, configuration hash, stamp file, draw; a wrong hash under a valid stamp is refused before any folder is made (executed). Jobs 86 and 87 give the hash, each has its guard, and the runbook's 19 commands equal the generator's 19 gate jobs token by token (executed).

**e.** It cannot draw another seed. `--seed` accepts 7, 8, 101 and 102 only; the three other seeds of its configuration are the rest of these four; every draw of the process goes through a wrapper that refuses any other seed and is installed before the configuration is built; an assertion keeps the gate's seed out. Only the `train` split is exported and solved, and the workers load exports and never sample (read). It uses the gate's mesh, levels and solver settings: asserted in its lines 70 and 71, and executed (exports equal to my own pilot's, same iterations). The exit code is right for a job without a guard: 1 after the report is written when a label does not converge or the check fails, 0 otherwise.

## 4. Checked

- The configuration hash of `tree3` is `29149f2e...a5b8`; the configuration differs from tree2's in five `criteria` texts only (executed).
- The runbook's order through `c23/__main__.py` on the reduced configuration, with the new options: every exit code as the runbook states; final verdict with `part1_same_as_first: true`; kept file and label-free rows unchanged to the end (executed).
- `tests/test_c23.py` once: 18 passed. I added two options to the brief's command: my plugin on the family seeds, and a temporary folder in scratch. A first start ended before any test was collected because of an error in my own plugin; no test ran then.
- 69 tests collected for the runbook's suite; the four other test files are unchanged from `tree2` (executed).
- The draft archive of `make_pre3.sh` from `tree3`: 164 entries, the new probe and its record in it, no `docs` folder; the pilot run from it left no bytecode (executed).
- The changed paragraphs of draft 0.4 and of the runbook against the code (read); thirteen bracketed places remain in the pre-specification and `@@CONFIG_SHA@@` stands in 13 lines of the runbook.
- The files that changed in this round hold nothing of round 1's list H (executed; a search).

## 5. Not checked

- Anything on the host, on a GPU or on Windows; Python 3.12's own `spawn.py`.
- The full host check on `tree3`: the author's run; not repeated, as the brief says.
- The four other test files were not run again on `tree3`.
- The note of 03:52 in its original language.
- The queue's runner: my stand-in runs jobs in the order of their names and skips a job with a done file.

## 6. Notes for the coordinator

- Left behind: `scratch/round3/` (12 MB). It holds a copy of the code whose third seed I set to 102 so that it cannot draw, and no stamp file; none is left anywhere in the review folder.
- The personal names that I searched for came from the session's context and from the user-memory snapshot. I do not write them here. No other fact of this report comes from memory.

---

# What the author did after round 3

Written by the author of the reviewed files, not by the reviewer, on 18 November 2026. Paths are relative to `joint/`. No round followed: the changes below were not seen by the reviewer. They touch the runbook, the pre-specification's text, one `criteria` text of the configuration, one test and the working tools; no line of the gate's code that computes, judges or refuses was changed after round 3. The pre-specification is draft 0.5 after them.

32. *Predictions that are not finite in the state of seed 5 or 6.* Repaired in the runbook, not in the code. Section 4: after such an end, which is final, the operator queues without guards the three prediction commands again (those that have ended return at once, those that the guard cancelled now run) and then the two commands of section 5, so that the INVALID verdict is written. "After a stop" refers to it. The generator has a set for these five jobs. The other repair that the reviewer offered, a change of `verdict`, was not taken, so that the judged code stays as round 3 saw it.
33. *The suite and the gate's real configuration.* Done as proposed: in `test_commands_refuse_code_that_is_not_the_stamped_code`, the functions of `c23.data` that draw, export, solve or check are replaced by one that fails the test, so that a refusal that did not hold could not draw the sample.
34. *"After a stop".* a. The paragraph names the files to move: the job files and done files of the failed stage, of the guard that stopped and of the cancelled jobs, the files of the stage's continuations, and the log of the failed attempt. b. It says which failures of the check of labels are final (a level that did not converge, levels that are not the configured ones, a limit that is not kept) and which is not (labels missing after a label command was cut off); sections 3 and 6 say the same. c. The generator applies the check on part 1's verdict whenever the first job written sorts after the guard of that verdict, so also for `BC --from`. d. The generator's set R writes the five jobs of finding 32 without guards.
35. *The label-free rows file after the first record.* The sentence is in "After a stop": once the kept file exists, the evaluation of the label-free arm is not queued again; if the rows file is lost, report.
36. *Text and code.* The pre-specification names the commands that take the configuration hash, and says why `label` and `check-labels` take none. "Final" now covers a part that is INCOMPLETE by a stop condition, in the pre-specification and in `criteria.final`. With this text the configuration hash is `3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e`; the record of the pilot on a processor was made again and names it.
37. *The list of additions.* The two rules are added (an interruption that comes from the host; the labels a supervised run trains on), and the item on the pilots names the three.
38. *Smaller things.* The generator refuses `--from` without a name or with a guard's name. The runbook's line on `verdict` names both refusals. Left as they are: a training label that is solved again counts as another label, by design, as for the evaluated members; a solve that raises ends the pilot probe with a traceback, which a job's log keeps.

Also changed after the round-3 snapshot: the runbook's note on the duration of the test suite (22 to 29 minutes on two processor cores).

What the author ran on the final state: the 18 tests of `tests/test_c23.py` (the three that train and solve after the last change of the code's texts); on the state of round 3, the host check on a processor and the runbook's 69 tests. The whole suite of the package is run again on the stamped state.

---

# What changed between draft 0.5 and the stamped text

Written by the author on 18 November 2026. The reviewer saw none of it. No file of the gate's code changed: the 35 files of `docs/G-C2.3_code.sha256` are those of the state described under "What the author did after round 3".

**The owner's answer.** On 18 November 2026 at 10:31 the owner agreed to the eight levels of the training labels and gave the host to the checks before the stamp at once and to the run from that night. The pre-specification's "Authority", its point on the labels and its line on the host say so; the two open points are closed.

**The checks on the host before the stamp**, all made on 18 November 2026 from a copy of the code that is file for file the stamped code, each ending with code 0 (`records/c23/before_stamp/`):
- the host check (`c23/smoke.py`): passed; identity check of its stand-in networks in order with a largest difference of 0.0; the resumed supervised run equal to the uninterrupted one on the GPU; none of the four pairs of its stand-in networks flagged;
- the predictions of G-C2.2's 132 members from the three state files (`probes/c23_precheck/repredict.py`): each state file has the pinned SHA-256, and every field and amplitude equals G-C2.2's file to the last bit; a state took ten to ten and a half minutes;
- the pilot of the training labels (`probes/c23_precheck/pilot_labels.py`): 32 members of seed 101 at the eight levels with the host's solver, every level converged, the label checks hold;
- the step timing (`probes/c2_timing/step_cost.py`): 0.167 s for a supervised step and 0.671 s for a label-free step in the median;
- two timings that the pre-specification does not use (`probes/c2_timing/time_curve.py`, `probes/f2_cost/energy_cost.py`).

**The pre-specification**: the time of the stamp; the results above in "What was seen before the stamp", "Budget" and "Identity of the label-free networks"; the hashes of the seven new files; the tests; the review; in "Not seen", what the checks on the host read and did; one sentence of "Stop conditions" brought into line with the runbook's section 4.

**The runbook**: the configuration hash in its 13 places; the time of a prediction (about ten minutes for a state, from the check above) and the time to the end of part 1 that follows from it.

**The package's `README.md`**: the status of 18 November 2026, the gate's row, and the folder `records/c23/`.

**Tests on the stamped state**: the whole suite of the package, 156 tests, passed.

**Line ends of two tables.** On 18 November 2026 at 12:07 GMT, after the time written in the pre-specification, the two `.csv` files of `probes/c2_selfcheck/` were given LF line ends in place of the CRLF that the scripts write, so that the commit has one tree under any line-end setting of Git. Their content is unchanged, `conditions_numbers.py` gives the kept record from the converted table byte for byte, and the folder's README says so in one added sentence. Neither file is among those of `docs/G-C2.3_code.sha256`; no text of the pre-specification or the runbook and no file of the code changed with it.

---

# What drafts 0.2 to 0.5 of the pre-specification add to draft 0.1

Written by the author. The owner's message of 18 November 2026, 03:56, answered a note that came with draft 0.1. Draft 0.2 is the state that round 1 reviewed, draft 0.3 the state that round 2 reviewed, draft 0.4 the state that round 3 reviewed, and draft 0.5 the state after the repairs of round 3. `docs/PRESPEC_G-C2.3.md`, "Authority", refers to this list for everything that the author chose after that message.

**Rules that can decide an outcome**

1. *Training labels.* Eight levels, from 0.1 mm, and 4,096 reference solutions; draft 0.1 had seven levels, from 0.75 mm, and 3,584. The supervised loss of a step uses 4 of the 8 levels. This is the point that the pre-specification marks as open for the owner.
2. *Identity.* The verdict is INVALID also when a judged value of a label-free run on G-C2.2's fresh members cannot be computed. A verdict that is INVALID holds no statistic of the third sample. A label-free run that ends without finite predictions is not predicted again. Draft 0.1 had only the case of values that differ.
3. *Spread.* It is divided by the absolute value of the median force, and a pair whose median force is zero is flagged. Draft 0.1 divided by the median.
4. *A member without metrics.* If the reference code cannot compute the metrics of a member of the third sample in a label-free run, part 1 is FAIL and R is NOT EVALUABLE. Draft 0.1 was silent.
5. *R.* It is judged in each run that has a pair above 0.05 and a pair at or below 0.05, and it is NOT EVALUABLE if no run has both. Draft 0.1 said "in each run with at least one pair above 0.05" and had two words only.
6. *Part 2.* The ends of the band are included. The wording is NOT COMPARABLE if a ratio is not a number. A supervised seed without numbers enters the medians over seeds with infinite errors, and so does a seed of either arm in which a member of the third sample has no metrics. Draft 0.1 was silent on these.
7. *Stop conditions.* A label of a training member that fails leaves part 2 INCOMPLETE and part 1 standing, and no other solver settings are tried. A label-free run without finite predictions makes the verdict INVALID. A checkpoint that cannot be read: as in G-C2.2. A command that the owner stops and does not let run again leaves INCOMPLETE what needs it. An outcome that is INVALID, and a part that is INCOMPLETE by a stop condition, are final: the gate is not run again on the third sample. An interruption that comes from the host is no stop of the gate: the interrupted command is run again and the interruption is reported. Draft 0.1 said "as in G-C2.2" for all labels and nothing on the rest.
8. *The labels a supervised run trains on.* Before a run starts or resumes, the training members' files are compared with the manifest and the ledger; a run is neither resumed nor evaluated on other labels than those it was started on. Draft 0.1 was silent.
9. *Procedure.* The first verdict in which part 1 is decided is kept in a file of its own, written once and only while no training member is labelled; every later verdict is compared with it, the SHA-256 of the label-free rows file included. Every command but `write-config` refuses code that is not the stamped code, and `generate` and the commands after it refuse another configuration hash than the one given to them. Before the stamp, on the host: the state files predict G-C2.2's own members again and the fields are compared with G-C2.2's files, and members of a seed used before G-C2.1's stamp are solved at the eight label levels.

**What is reported and how it is worded**

10. *Reported, not judged*: the median error of both arms at each level; the two ratios of the supervised arm read raw over the label-free arm in the condensed reading; in each run, how many of the pairs above 5% and above 10% are flagged.
11. *Interpretation.* Part 1, PASS: the numbers of pairs above 5% and above 10% and how many were flagged; the sentence for the case that S1 was not put to the test; the sentence for the case that R does not hold. Part 1, FAIL: the sentence for a FAIL that comes from a member without metrics. Part 2: the medians at each level; the two ratios of the supervised arm's raw reading with the wording in every case; the statement that the supervised arm was trained with the label-free arm's settings and was not tuned. INVALID: reported with its cause, and as a failure of a label-free network when the cause is predictions that are not finite.
12. *What the gate does not show*, part 2: labels at other levels, and the sentence on interpolation between the eight labelled levels; a supervised arm whose settings were chosen for the supervised loss; the unequal risk of the two arms of losing a seed.

**Statements corrected**

13. Draft 0.1 said that no judged level lay beyond the labelled range. That was wrong (item 1).
14. Draft 0.1 said that a supervised run and the label-free run of its seed visit the members in the same order. That holds in the first epoch only; the initial weights are the same.
15. "Not seen" is stated more exactly: 24 training members were solved at the seven judged levels in G-C2.2's development; members of seeds 7 and 101 were solved at the eight label levels in three pilots, the last of them on the host.
16. The statement on the area under the curve names the two readings that do not favour the spread. The tested member of G-C2.1's supervised arm is named, with the level at which that arm was weakest.
17. The state files' hashes are given, from the record of the owner's archive of 15 November 2026; draft 0.1 left them for the stamp.
18. The labels' processor time is about 22 hours; draft 0.1 said 21. The sentence that a supervised step took about a third of a label-free step on a processor, which had no record, is removed.

The owner agreed to nothing in this list except by the general words of 03:56 on what draft 0.1 held. The threshold, the criteria S1 to S3, the limit of R, the band, the seeds and the samples are those of draft 0.1.

---

# The reviewed states

Written by the author. SHA-256 of the files in scope as each round received them, relative to the repository's root; `gate_prep2/` and `gate_prep3/` hold working tools outside the repository.

**Round 1**

```
8e2298fc828f64ad2538dc0572e6c0843944e0b43db84ffbe0b3bccf4b8cc47c  joint/RUNBOOK_C23.md
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  joint/c23/__init__.py
ff0254175a8044f965e062305886ef5c17b42f4146bfb8be2de2cab8794137f5  joint/c23/__main__.py
4326be31700726c1ecd45546932b6f497d8d3c1aa88f92066b0366a17ff05189  joint/c23/config.py
c07e7bc4cfb5f1eac70c2c8c2c5563b3249f93810c3446195fbe5a466e24a042  joint/c23/data.py
95e4e7a94cbf4812142add060ba5f20b3e109265bd0e7b88398be4b1470bd38d  joint/c23/evaluate.py
faf9f71a1970745ce38c73fe015d89e9e1f91a7375f072a5019a9f6a2cbb3f20  joint/c23/smoke.py
aadf6c6bed54cee984683abe342679530c4c0e3b374d5b159c6b8b23e3312d47  joint/c23/train.py
b28d67a272b296202aa7af5a8f2ebcd3da5e6bfd2b9667f48ee8a5ccde4055b3  joint/docs/PRESPEC_G-C2.3.md
a2965062c4c3fe6ff703572e2cbedfe23527222b4bee917d7e108e11d0ce0efe  joint/probes/c2_timing/step_cost.py
a58246cfbc9e48baf170557efb2208ded584baaf5ddb44828e1b3d008b419d98  joint/probes/c2_timing/time_curve.py
4122f2f72606f2d8b4271a7527c72abaec164b8d099c0edc076a9ef49b8d3fa3  joint/probes/f2_cost/energy_cost.py
ffe789fc498cd8e7842d6f5b94862c8b5f39b73b42d19d741b76657fa4879fc8  joint/tests/test_c23.py
```

**Round 2**

```
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  joint/c23/__init__.py
c7b16828a7357d09e20f70a3070befc64c65653cba47e826220653bf2ad42ef3  joint/c23/__main__.py
1ceba18092c701571c0f9fae23de0754e2ed7491c44d013d8f86f5a343c5503d  joint/c23/config.py
10ddd019b80dc19d7801f424f94940d7bbf8bcfc5dde7dd268011275af5942c1  joint/c23/data.py
7a135e0802a5fb92ff99eade68533ac9e447a51afaac14555b632534919bf017  joint/c23/evaluate.py
747921fcd84bc929e76ece3cbab19dfbbc0b810d74946fbe7bd03c9a4dba4b22  joint/c23/smoke.py
388a1907fe2a0682fb11eeb2fc752d8d45094a1f832a93978c1550b7b9735383  joint/c23/train.py
e975371342a67844951f0ba3b06603ed6d7d25b88137ce068dcf64f767a30565  joint/probes/c23_precheck/repredict.py
8fe694c2c73a79191115c8a0c171325511a70bfbca3ec33cbfe22dc0ffa61808  joint/probes/c2_selfcheck/README.md
e198936e3f57a6828fef8700daa5c69a4cd92f9dfa6428031c7e384e9f8cfdd5  joint/probes/c2_selfcheck/conditions.py
e375d497892d32f06e71ca0a5d4445ad54d1c5beb975edfc444cdd71cfd7e5d2  joint/probes/c2_selfcheck/conditions_index.csv
f012116eed1e2a8bca270198b8a7fea672fc6d7b45781cea918f2509bc88dcd0  joint/probes/c2_selfcheck/conditions_numbers.py
dd726aa37313cf251f348df6f6f4adde72c5a01750e94f262d2fa99a55486d63  joint/probes/c2_selfcheck/gate_code_on_seen_samples.py
286ffcbd239bd343e9652076683528cf4fbafa04818b941c608a3da8c6096546  joint/probes/c2_selfcheck/other_metrics.py
164ed9236558eb810f2015e7b034fa7b8b6bfb1dfb353f5c4a98580e67365b6e  joint/probes/c2_selfcheck/plastic_index.py
19263f8d2f466aae29152a21b37f7e4ac3980e3a45e8f7030a6cb44c93e86644  joint/probes/c2_selfcheck/plastic_index2.py
d5c48f977fa5e9cd8675057e215cd6a9335e41f022a6a9948e88beea5d6d9907  joint/probes/c2_selfcheck/records/conditions.txt
9784b81a138e7b668599a26fa90ba7e651f4e440ff87a046868b3b8b1972932c  joint/probes/c2_selfcheck/records/conditions_numbers.txt
cee9f78489ca218dd8f6ae5ab09d2ac7de416136b00a7e541c31897b41d9f51c  joint/probes/c2_selfcheck/records/gate_code_on_seen_samples.txt
232752cb7a06b364bdeb12c0156d2000b9b683fb3109a32b7682e59a3a78b723  joint/probes/c2_selfcheck/records/other_metrics.txt
c3351fca6947e08e12bf0c9c6a3b8132bc9162c98571cd03d03694dfdee43511  joint/probes/c2_selfcheck/records/plastic_index.txt
0d085549ae1150b182fa100e0f27c6d09396beea7f800e2263294e09f0b86a2e  joint/probes/c2_selfcheck/records/plastic_index2.txt
58766e87d626c5ba5850c6ea4eb31a5b1510b97c12434e414f9d0654b72ee99b  joint/probes/c2_selfcheck/records/selfcheck_indicators.csv
430de964dd3c6b06b5608cd3ce3a3626046a8385c5f772af7ba2d6b9cfe0f21c  joint/probes/c2_selfcheck/records/selfcheck_indicators.txt
7110f9ed764fa259594ce42d1181ae629a16df9a76f599ecd3dd6cfeefdb0b93  joint/probes/c2_selfcheck/records/spread_details.txt
7fea72abc33575b0b45f589a38d8192a391ae5c22efe9d8f869bbb50fe05462d  joint/probes/c2_selfcheck/selfcheck_indicators.py
68ff06bbdcdfcdc255a51514dbb00e6bc3412ce2190c97bc9b66e77db0330247  joint/probes/c2_selfcheck/spread_details.py
18de446363a3b31efe7f7a1c12887ad38001b46a5bf0b4891ae4515999d4fc50  joint/probes/c2_timing/step_cost.py
318f8bc2bb00ec313028f4d37b0cc4b0e7c18ed7b893abf0ad6390db9a34f76d  joint/probes/c2_timing/time_curve.py
118b171f89f97f9e85449d1a8a9c88e159a88b3a8a5bfe299f1c3c67f111c167  joint/probes/f2_cost/energy_cost.py
a35df46e5420d2a678a140f784b568444d8e27893c999a3385e79e39a24f7447  joint/tests/test_c23.py
98453b8a6c2a49c888ea93ba83ae3c2ab05cc93f48410283b8ac89fbc4f7d9f6  joint/docs/PRESPEC_G-C2.3.md
9775ead42c6d78681b4030e49c7cbd2ab4e6fa72bea8f72150c351b4128e814e  joint/RUNBOOK_C23.md
a70616131914a30c6c29327b1912828749fd57b571297e3bd3d0affc04ad0a40  joint/README.md
336d8e3f202cb58a0aa048810c9d41e59eb414d64c6be5343984541490fa433e  gate_prep2/make_jobs_c23.py
d05cdcc5ead1588b10aa78cdaf8c818ee4311e599a2cf946a8076e9819a04da0  gate_prep2/make_pre3.sh
d740c28e3d2332814d6d81cbe67dcfe75b7ddbe9b682a3712ca7b20726a75826  gate_prep2/make_stamp_c23.py
```

**Round 3**

```
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  joint/c23/__init__.py
f6636b5b4153fade230443af8ae0b24f9f372b946f81833f45bf847aa1943ced  joint/c23/__main__.py
b7b48fca1de3c6469d61ab8cf4fb91af4e3b477a657e078ef34f6f3aa0010a7c  joint/c23/config.py
10ddd019b80dc19d7801f424f94940d7bbf8bcfc5dde7dd268011275af5942c1  joint/c23/data.py
d526fb2754cd15b53c228b1707d533c1aa4a22fb79f6c4a5796684b36e36ce61  joint/c23/evaluate.py
dc8e5e657b11f8c30292d62bd00a50b953cc9f8b5e337aef24a4e3d0069aa65c  joint/c23/smoke.py
2e8095b20e5e770b13ab5ee60343ed1cf7abe63fe06b0e9a9f2149f33dae6f83  joint/c23/train.py
78e4298bae3a386bdeb74d075fd9fb2152d5772047bb0f246b7676ea88efa624  joint/probes/c23_precheck/pilot_labels.py
af1083438cd9e7af5c7adee41b2f413b7b390b6e6ba50249745cc55c394d99ea  joint/probes/c23_precheck/records/pilot_labels_processor_seed7.json
3bac275f3f0264143fc23a9dfad790bcbe30d569a5c0e789bfd37711ceea8a9b  joint/probes/c23_precheck/repredict.py
8fe694c2c73a79191115c8a0c171325511a70bfbca3ec33cbfe22dc0ffa61808  joint/probes/c2_selfcheck/README.md
e198936e3f57a6828fef8700daa5c69a4cd92f9dfa6428031c7e384e9f8cfdd5  joint/probes/c2_selfcheck/conditions.py
e375d497892d32f06e71ca0a5d4445ad54d1c5beb975edfc444cdd71cfd7e5d2  joint/probes/c2_selfcheck/conditions_index.csv
f012116eed1e2a8bca270198b8a7fea672fc6d7b45781cea918f2509bc88dcd0  joint/probes/c2_selfcheck/conditions_numbers.py
dd726aa37313cf251f348df6f6f4adde72c5a01750e94f262d2fa99a55486d63  joint/probes/c2_selfcheck/gate_code_on_seen_samples.py
286ffcbd239bd343e9652076683528cf4fbafa04818b941c608a3da8c6096546  joint/probes/c2_selfcheck/other_metrics.py
164ed9236558eb810f2015e7b034fa7b8b6bfb1dfb353f5c4a98580e67365b6e  joint/probes/c2_selfcheck/plastic_index.py
19263f8d2f466aae29152a21b37f7e4ac3980e3a45e8f7030a6cb44c93e86644  joint/probes/c2_selfcheck/plastic_index2.py
d5c48f977fa5e9cd8675057e215cd6a9335e41f022a6a9948e88beea5d6d9907  joint/probes/c2_selfcheck/records/conditions.txt
9784b81a138e7b668599a26fa90ba7e651f4e440ff87a046868b3b8b1972932c  joint/probes/c2_selfcheck/records/conditions_numbers.txt
cee9f78489ca218dd8f6ae5ab09d2ac7de416136b00a7e541c31897b41d9f51c  joint/probes/c2_selfcheck/records/gate_code_on_seen_samples.txt
232752cb7a06b364bdeb12c0156d2000b9b683fb3109a32b7682e59a3a78b723  joint/probes/c2_selfcheck/records/other_metrics.txt
c3351fca6947e08e12bf0c9c6a3b8132bc9162c98571cd03d03694dfdee43511  joint/probes/c2_selfcheck/records/plastic_index.txt
0d085549ae1150b182fa100e0f27c6d09396beea7f800e2263294e09f0b86a2e  joint/probes/c2_selfcheck/records/plastic_index2.txt
58766e87d626c5ba5850c6ea4eb31a5b1510b97c12434e414f9d0654b72ee99b  joint/probes/c2_selfcheck/records/selfcheck_indicators.csv
430de964dd3c6b06b5608cd3ce3a3626046a8385c5f772af7ba2d6b9cfe0f21c  joint/probes/c2_selfcheck/records/selfcheck_indicators.txt
7110f9ed764fa259594ce42d1181ae629a16df9a76f599ecd3dd6cfeefdb0b93  joint/probes/c2_selfcheck/records/spread_details.txt
7fea72abc33575b0b45f589a38d8192a391ae5c22efe9d8f869bbb50fe05462d  joint/probes/c2_selfcheck/selfcheck_indicators.py
68ff06bbdcdfcdc255a51514dbb00e6bc3412ce2190c97bc9b66e77db0330247  joint/probes/c2_selfcheck/spread_details.py
18de446363a3b31efe7f7a1c12887ad38001b46a5bf0b4891ae4515999d4fc50  joint/probes/c2_timing/step_cost.py
318f8bc2bb00ec313028f4d37b0cc4b0e7c18ed7b893abf0ad6390db9a34f76d  joint/probes/c2_timing/time_curve.py
118b171f89f97f9e85449d1a8a9c88e159a88b3a8a5bfe299f1c3c67f111c167  joint/probes/f2_cost/energy_cost.py
61cf722510d9cf4827cb6b08d2936fb83d0ed6f07b2b7c631767727c612eadd2  joint/tests/test_c23.py
4ba878eaf0bea3009c4bfb364f28e0c0635499ea6dd6f92b55120efcffb430ae  joint/docs/PRESPEC_G-C2.3.md
fbd3bf62cedfba1f5490759d565914137786fd342bc0bf1c45f80eade2d739d0  joint/RUNBOOK_C23.md
f14ebf1013725976b18b336bf2e3c562d85c54c36697023589911f9f4690d5f5  joint/README.md
1530da5b1ab39eced9c1ed950b4aca4a65e6bfc2997af45575e7914d5e424d42  gate_prep3/make_jobs_c23.py
d05cdcc5ead1588b10aa78cdaf8c818ee4311e599a2cf946a8076e9819a04da0  gate_prep3/make_pre3.sh
d180b842b56cd00f83ed02f4529ca2e5495a3aa5a8fb18d157c236a2b7ea098e  gate_prep3/make_stamp_c23.py
```
