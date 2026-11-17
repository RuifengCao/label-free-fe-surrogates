# Independent audit of the G-C2.2 verdict: reports as delivered

Reports of the independent auditor (a separate agent that wrote none of the code, the records or the draft) to the author: round 1 at about 17:55 GMT and round 2 at about 18:30 GMT on 15 November 2026, and round 3 at about 15:55 GMT on 17 November 2026, and round 4 at about 17:50 GMT on 17 November 2026. Round 1 audited the return package as received and the proposed commit as it then stood: the records as kept, the draft of the verdict with its generated tables, the three audit scripts and the README. Round 2 audited the corrections. Round 3 audited the corrections of the two errors of round 2 and the final texts. Round 4 audited the commit after the label and prediction files were taken out of it.

Notes of the author for this folder:
- In the reports, `fdb5d65` is the author's local name for the state that round 1 audited (tree `4b307f0643c3b856a0e09c15676e5955c1c9f5c2`), and `f7a500e` for the state that round 2 audited (tree `01986870dbf92e44bf299a2587eae6b985aa1985`), and `0d50429` for the state that round 3 audited (tree `0f16bd18d7be93777ed79c137f7e1781a9cd8542`), and `c247c42` for the state that round 4 audited (tree `c2a47c36ddd7ca738b64f6173ce60fd623935379`). None of these states was pushed; the pushed commit is the state after the last corrections.
- `scratch/` is the auditor's working folder on the development machine and is not kept. The line numbers in the reports are those of the audited states.
- The auditor returned each report as a message; the text of each is given here without a change.
- What the author did about each point follows each report under "What was done" and is marked as the author's.

---

**Round 1, as delivered**

# Independent audit of the verdict of gate G-C2.2

Report of the independent auditor to the author, 15 November 2026. Audited: the proposed commit `fdb5d65` (parent `6d9da9b`, tag `prereg-c22`), which has not been pushed, and the return package `c22_return.tar.gz` as received. I wrote none of the audited code, records or documents. I changed none of them, pushed nothing and sent nothing. My scripts are in `joint/audit/independent/G-C2.2/` (listed at the end); their outputs are in my folder `scratch/`.

**Conclusion.** The verdict holds: from the returned per-pair values my own code gives C1 = 0.007972382816471169 and C2 = 0.03663936677608451, PASS, identical to `verdict.json`, and the 161 judged errors that I recomputed with exact solves (stamped library, my own driver) agree with the returned ones within 5.4e-14. The run kept to the pre-specification in everything that decides the verdict: configuration, code, sample, seeds, steps, reading and thresholds. The numbers of the documents are right (759 generated table cells derived again, none differing), but the commit should not be pushed as it is: six errors are listed below, among them one wrong hash, two statements of the README that say more than the verdict document or the pre-specification allow, and two files that would publish what should stay out.

## Verified

**1. The criteria**

- **From the per-pair values of `verdict.json`, with my own quantile** (`a1_criteria.py`).
  - Condensed reading on the 64 fresh held-out members, 448 pairs a seed: medians 0.008284227273415379, 0.007972382816471169, 0.007818943658160049; 90th percentiles 0.03663936677608451, 0.03766036133923352, 0.036562399536675616.
  - C1 = 0.007972382816471169 (at most 0.05), C2 = 0.03663936677608451 (at most 0.10), PASS. The differences from the returned values are 0.
  - Raw reading (reported): 0.013638353687949134 and 0.10542708497194714. C1 would hold, C2 would not. Differences from the returned values: 0.
  - All 18 stored summaries (two readings, three sets, three seeds: count, median, 90th percentile, largest) are reproduced exactly, 72 values.
  - None of the 5,544 rows is infinite or not a number, and none carries a note or a failure.
- **Every row tied to the returned files, without a solve** (`a10_all_fields_force.py`, numpy only). For all 5,544 fields (three seeds, two readings, 132 members, seven levels) I read the end displacement from the prediction file, formed F = 4 k_s (D - e) and compared the errors of force and of end displacement at the same D with the row: the largest difference is 0 for both.
- **The instances** (`a9_regenerate.py`, stamped library, my driver). All 644 regenerated files have the manifest's SHA-256 when written through zlib 1.3 with the creator field 0; sizes and family parameters equal the manifest's. Control: with the environment's own zlib and creator field, 0 of 2 hashes match.
- **The judged error with exact solves** (`a2_select_pairs.py`, `a3_recompute_pairs.py`, `a15_pairs_summary.py`). I chose 161 pairs in 66 members and computed F / F*(e) - 1 myself: e and F read from the field by my code, F*(e) from the stamped library's solve at the prescribed end displacement. All 161 solves converged; 0.89 processor hours.

  | Class of pairs | Pairs | Largest absolute difference from the returned signed distance | Returned distances covered |
  |---|---|---|---|
  | Judged reading and set: the 7 largest of each seed (all 17 pairs above 10% are among them) | 21 | 3.0e-14 | 8.7% to 68.6% |
  | Judged: ranks 221 to 226 and 400 to 405 of each seed (around the order statistics of the median and of the 90th percentile), and the 3 nearest 5% and 10% | 46 | 3.5e-14 | 0.77% to 8.1% |
  | Judged: random (generator seeded 20261115) | 40 | 5.4e-14 | 0.07% to 5.3% |
  | Raw reading, fresh members: ranks 401 to 404, the 2 largest and 4 random of each seed | 30 | 4.9e-14 | 0.25% to 183.4% |
  | Held-out members of G-C2.1, condensed: the 2 largest and 2 random of each seed | 12 | 5.1e-14 | 0.40% to 29.5% |
  | Held-out members of G-C2.1, raw: random | 6 | 4.7e-15 | 0.78% to 9.0% |
  | Tested members, condensed and raw: random | 6 | 3.8e-15 | 0.11% to 1.5% |
  | All | 161 | 5.4e-14 (relative 3.6e-12) | |

  - Of the judged reading and set this is 107 of 1,344 pairs (37, 35 and 35 by seed). On these 107 my values and the author's recomputed ones (`records/c22/audit/curves.json`) differ by at most 7.4e-14.
  - For the 66 members the returned label fields of the lowest and of the highest level, evaluated on my regenerated instances, give the label's force and end displacement exactly and its energy within 3.3e-16.
- **Controls.**
  - The start of the solve (`a13_cold_start.py`). The gate starts each exact solve from the label nearest in end displacement. I solved three pairs from zero, so that no label enters the solve: the worst pair of the gate (`eval_0001`, seed 6, 8 mm, 68.6%), the pair at rank 401 of seed 5, just below its 90th percentile (`eval_0055`, 6 mm, 3.52%), and one raw pair (`eval_0030`, seed 7, 8 mm, 5.88%). The judged errors differ from the returned ones by 1.8e-14, 3.8e-15 and 9.1e-15.
  - One label solved again (`a14_resolve_label.py`): `eval_0044`, a member of the tail that the author did not re-solve. Not bit for bit; the largest difference is 1.3e-14 of the largest unknown, 6.7e-16 in energy and 1.8e-15 in force; the iterations are the ledger's (2, 2, 8, 13, 11, 12, 6).

**2. The run against the pre-specification and the runbook** (`a4_run_checks.py`, `a5_condensed_reading.py`)

- **Configuration.** The returned `c22_config.json` has the bytes that the stamped `c22/config.py` writes (SHA-256 `8196ab91...2e72`); its canonical SHA-256 is `ef5376a4...34bb`, the pre-specified one. The manifest, the three histories and `verdict.json` carry the same hash.
- **Code.**
  - The 34 lines of `docs/G-C2.2_code.sha256` and the 26 of `docs/G-C2.1_code.sha256` check against the stamped files, and the 8 hashes of the pre-specification's table equal the files.
  - The 34 hashes that the configuration command printed on the laptop equal the list.
  - The archive of the tree: the runbook's `git archive` command on commit `6d9da9b` gives SHA-256 `2fddd104...f115`, 942,080 bytes, 101 files, as `preconditions.log` records.
  - The tag `prereg-c22` is an annotated tag on `6d9da9b`, made at 12:44:25 GMT on 13 November. The commit is dated 11:17:03 GMT.
- **The held-out sample.**
  - The manifest holds 644 members: 512 training, 64 fresh held-out, 64 of G-C2.1, 4 tested.
  - A sampler that I wrote from the family's ranges and rejection rules reproduces the parameters of all three drawn sets exactly: seed 20261106 (training), 20261113 (fresh), 20261107 (G-C2.1's). The tested members are the configured ones. No two members have the same parameters.
  - The fresh members were generated between 12:53:48 and 12:58:13 on 13 November, after the commit, the tag and sections 0 and 1 of the runbook. In the stamped tree the seed 20261113 appears only in the configuration, the pre-specification, the runbook and the review report.
  - 448 pairs a seed: 64 members at the seven levels 0.5, 1, 2, 3, 4, 6 and 8 mm.
- **Labels.** The ledger has 132 entries, once each, at the seven levels, all converged in at most 23 iterations, with the sparse solver `scipy` in every entry. The worst unconstrained residual is 1.33e-10 and the two force readings differ by at most 4.8e-13; every residual is within its limit. The 132 label files have the ledger's SHA-256, and the ledger's instance hashes are the manifest's. The three logs hold 64, 64 and 4 lines ending in `converged` and none with `NOT CONVERGED`. The labels are dated 12:59:21 to 13:19:23.
- **Training.**
  - Seeds 5, 6 and 7; each 102,400 steps in 200 epochs, status `finished`; 307,200 steps in all, which is the budget. Betas 0.9 and 0.99; cap factor 5, window 256, burst factor 10.
  - No capped step before step 257 (the first are 257, 258 and 267). Capped steps 2,154, 1,805 and 2,000; bursts 233, 136 and 218; every burst is a capped step with a ratio above 10. All 600 epoch losses are finite.
  - All 600 epoch lines of the queue's logs equal the histories: the loss at its six printed digits, the seconds exactly, and both running counts.
  - `attempts.log`: seed 5 started at 13:19:24, started again at 01:43:10, resumed from epoch 75 at 01:44:51 and ended at 07:56:43; seeds 6 and 7 have one start and one end each.
  - Hours of training 14.08, 12.70 and 12.55 (39.32 in all). From the first start to the last end: 44 h 12 min 46 s.
- **The reading that is judged.**
  - Each of the nine prediction files holds exactly the 132 members, as float32 arrays of the expected shapes, all values finite. In both readings the fixed unknowns are zero and the contact unknowns are not negative.
  - For all 396 member and seed pairs I computed keep(z_0 + a (z - z_0)) in float32 from the returned base field, raw field and amplitude, keep acting on the contact unknowns of the regenerated instance: all 11,856,537 values equal the returned condensed fields bit for bit.
  - `condense.json` of each run carries the configured reading and levels. Every one of the 2,772 amplitudes lies between 0.5 and 3 (they run from 0.80 to 1.19); none is on a bound; no member used more than 12 energy evaluations.
  - Tolerance not met after 12 evaluations: 5, 9 and 11 fresh fields; 11, 17 and 8 of G-C2.1's; 0 tested. These are the counts of `verdict.json`.
  - The recorded training energy of the condensed field is above that of the raw field in 2 of 2,772 fields, by at most 1.1e-7 of the energy.
  - That the amplitude minimises the energy, checked in float64 with the reference energy of the stamped library on 30 fields of 22 members (10 a seed: the worst pair of the gate, one field whose tolerance was not met, 8 random; all seven levels occur). The energy at the returned amplitude equals the recorded float32 training energy within 2.8e-7. The relative slope there equals the recorded one within 5.1e-6; it is at most 8.5e-5 in the 27 fields recorded as converged (tolerance 1e-4) and at most 2.9e-4 in the 3 that are not. No point of a grid of nine amplitudes from 0.5 to 3 has a lower energy, and the minimiser estimated from slope and curvature lies within 5.5e-4 of the returned amplitude.
  - The base fields fit the base level of 0.1 mm: their end displacements are 0.006 to 0.030 mm, 0.19 of the end displacement at 0.5 mm in the median (a plausibility check, not a proof).
- **Order of events.**
  - The 11 commands of the runbook ran with the runbook's arguments, and no other command of the gate ran. The queue holds 22 job records, one of them the host check made before the stamp.
  - Each job started within one second of the end of the job before it, except for the pause and for 2 min 40 s between the configuration and the generation, when the operator read the output of sections 0 and 1.
  - The evaluation started at 09:32:11 on 15 November, one second after the last training run ended, and ended at 11:32:35 with exit code 0. `verdict.json` is written by the evaluation alone. The training code is called without labels (read in `c22/train.py`).
  - Every exit code is 0 except that of the paused first attempt of seed 5 (code 1, killed). All 8 guards wrote "the queue goes on". No record of a cancelled job exists.
  - The document's account of the queue after the closed window (deviation 2) agrees with the guard's code (read in `queue/guard.py`).
- **Judged and reported.** `verdict.json` names the condensed reading and the set `eval` as judged; its C1 and C2 are those of that reading and set; the raw reading is under `reported_readings`.
- **Host check.** `smoke/smoke_report.json` meets each condition of section 0d of the runbook: the versions named there, the GPU, 1,120 MiB of GPU memory in use (limit 3,000), one linear algebra thread in the workers, `check_labels.ok`, `evaluate.same_with_workers` and `condense.energy_never_higher` true, and the resumed run equal to the uninterrupted one (all differences 0.0). The log ends with `smoke test of c22 passed`.
- **The other logs.** Apart from the warning that deviation 4 reports (one for each of the four starts of a training run, and one in each of the two logs of the host check), no log holds a warning, an error or an unexpected line.
- **Departures.** From the records I find six: the pause of seed 5 with the possible restart; the state of the queue after the closed window; step times above the runbook's 0.8 s in 13 epochs; the warning that the runbook's comments do not mention; files in the package beyond section 6 of the runbook; and the suite run before the tag. The document lists the first five as its deviations 1 to 5 and adds one that the records cannot show (deviation 6, what the operator read). The last of mine is not listed (Missing 1). One description is misleading (error 4), and deviation 5 omits one file (Smaller points).

**3. The verdict document against the records** (`a7_document_tables.py`, `a12_text_numbers.py`)

- **Generated tables.** I derived 759 cells of the 15 tables of the part "Numbers" with my own code and formatting, from `verdict.json`, the manifest, the three `condense.json` and the three histories. None differs.
  - Criteria, both readings: 46. The two reported sets: 84. By level (median, 90th percentile, pairs above 10%, median signed): 168. Yield stress at 8 mm: 36. Pairs above 10% (fresh, and G-C2.1's): 120. The other readings (two sets): 132. Amplitudes: 90. Training: 27. Tested members: 56.
- **The lines and tables of the author's recomputation** (lines 343 to 366): every number equals the stored outputs in `records/c22/audit/` (item 4).
- **The text.** The part before "Numbers" holds 384 numerals by my count (the parts of dates and times counted singly). I compared all of them with the records; they match at their rounding, with the exceptions listed under Errors and Smaller points. The records cannot show three things: the two readings of the free disk space (the document says so), the end of the interval "12:12 and 12:15", and when the recomputation script was written.
- **The deviations.** The times of the pause, the 75 s lost, the step times (0.33 to 0.83 s; 430 of 600 epochs below 0.38 s; 13 above 0.8 s, 11 of seed 5 and 2 of seed 6) and the counts of the section "The records as kept" (67, six and one, one, seven, 193) agree with `incidents.log`, the queue's files, the histories and my comparison of the two copies.
- **The tail.**
  - 6, 5 and 6 pairs above 10% in 4, 3 and 3 members; over the three seeds eight pairs in five members, all five with a yield stress below 300 MPa (238 to 289 MPa), all eight too stiff in every seed, six of them at 6 or 8 mm, four in `eval_0001`.
  - Four of the eight are above 10% in all three seeds, one in two seeds and three in one seed.
  - `eval_0001`: 7.7%, 8.7% and 10.4% at 3 mm, rising in every seed from 3 mm to 50.1%, 68.6% and 51.0% at 8 mm; raw 183.4%, 164.0% and 176.2% at 8 mm.
  - At 8 mm no member at or above 300 MPa has a pair above 10% in the condensed reading.
- **The pass rests on the condensed reading, and the raw reading is given beside it.** The section "What this means" repeats the fixed PASS interpretation word for word, with its three points, and adds "see the next paragraph", where the raw reading is given (1.36% and 10.54%; C2 missed by 0.54 of a percentage point). The commit message gives both readings.
- **The comparison with G-C2.1's members.** In the raw reading 30, 31 and 30 fresh members have a pair above 10%, each of them at 8 mm and too stiff there; on G-C2.1's members 23, 22 and 20, likewise.
- **`former_0017`** is the only pair above 10% in the condensed reading that the raw reading reads better, in all three seeds (11.8%, 11.5% and 12.0% against 6.5%, 7.1% and 6.6%; amplitudes 0.94 to 0.95).

**4. The author's recomputation**

- **`c22_write_verdict.py`**, run again on the kept records and the stored outputs, writes the part "Numbers" of the document byte for byte (226 lines, 17,159 bytes).
- **`c22_recompute.py --aggregate` and `--records`**, run again on the kept records with the stamped library, give the stored `aggregate.json` and `records.json` in every entry.
- **The stored outputs, compared with `verdict.json` by my code** (`a8_author_outputs.py`).
  - `curves.json` holds 1,344 rows, exactly the pairs of the judged reading on the judged set, each once. The largest absolute difference of the signed distance from the returned one is 8.08e-14.
  - From the author's values I get medians and 90th percentiles that differ from the returned ones by at most 1.27e-14, C1 by 1.1e-16 and C2 by 3.5e-16; 3.51 processor hours.
  - `fields/`: 132 files, 5,544 fields. The largest absolute difference of a metric from the returned row is 8.0e-15 (the stress reading of the force); the containment in the bound is the returned one in every field.
  - Labels: 924 levels, energy within 4.4e-16, force and end displacement exact, largest unconstrained residual 1.33e-10. Condensed fields: 396 pairs, 0 unknowns differ.
  - `resolve.json`: four members, as the document says (differences of at most 3.8e-15 of the largest unknown, the ledger's iterations).
  - `regenerate.json`: 644 of 644, which my own regeneration confirms.
- **Reading of the three scripts.** I found no wrong key, no wrong set and no placeholder value. The comparisons can fail: the queue's guard does write `cancelled` into the record of a job that it cancels, which is what `--records` counts; the pattern for the training logs follows the names that the queue gives to continuations; the hashes fail without zlib 1.3 (my control above). Two small points are under Smaller points.
- What the document says about the recomputation is true of the stored outputs, including "not recomputed with exact solves": 4,200 pairs (5,544 less 1,344).

**5. The kept copy of the return package** (`a6_kept_copy.py`)

- **The archive.** SHA-256 `4b40742f...3249`, 119,319,209 bytes; the hash file that came with it matches. It holds 283 members: 268 files and 15 folders. `return_listing.txt` is identical to the listing that `tar tvzf` prints at UTC (283 lines). The newest member is dated 12:13:53 GMT on 15 November.
- **`return_files.sha256`**: 268 lines; all 268 hashes equal the files that I unpacked.
- **`return_kept.sha256`**: 261 lines; all equal the files of `records/c22/return/`. All 261 files are in the commit.
- **Differences between kept and received**, line by line:
  - 193 files are identical;
  - 60 differ by line ends alone;
  - 7 by line ends and one line each: six logs, in which the path of the working folder is `W`, and one launcher, in which the name by which the owner addresses the operator is "the operator" (twice in that line);
  - 1 (`queue/make_jobs.py`, which had no CR LF) by one line with the path.
  - So CR LF became LF in 67 files, 68 files changed, and no other line differs. No kept text file holds a carriage return.
- **Left out**: exactly seven files; their hashes in `keep_report.json` equal the received files. The 261 rows of `keep_report.json` carry the right hashes as received and as kept.
- **`c22_keep.py`**, run again on the received package, reproduces the 261 kept files and `keep_report.json` byte for byte.
- **Privacy search.** In the 251 text files of the kept copy and the other new files, and in the 161 binary files (2,629 arrays; the arrays that hold text were read), I found no path of a personal folder, no account name of the laptop, no name of the owner or of a collaborator (as far as their names were known to me), no e-mail address and no host name. Two findings are errors 5 and 6.

**6. The proposed commit** (`a11_commit_checks.py`, read-only git commands)

- 410 paths, 409 added and `joint/README.md` modified, the same list as `proposed_changes.txt`. Every added file has mode 100644, like the earlier audit scripts; the README's mode is unchanged.
- 249 text files, none with a carriage return, a tab or trailing blanks; 161 binary files. Total 126 MB; the largest file has 14.0 MB.
- No tracked file matches a rule of `.gitignore`. The rules `runs/` and `*.pt` drop nothing by accident: the kept copy has no folder of that name (its folders are `run_files`, `runs_full` and `runs_resumed`), and the two `.pt` files are among the seven declared as left out.
- No absolute path of this machine and none of a personal folder in a new file. The only path with a drive letter is inside the library's warning in six logs: the path of that library's build, not of the laptop.
- No em or en dash and no character outside ASCII in the new files and in the ten lines that the commit adds to the README, apart from two accented letters in a cited name on a line that held them before.
- British spelling: a list of patterns for American forms finds nothing in the document, the three scripts and the README's added lines.
- Both exports that I was given equal fresh exports of the two commits, and the working tree of the proposed commit is clean.

## Errors

1. **A hash that does not belong to the file named.** `joint/docs/G-C2.2_verdict.md`, "Where the numbers come from", third bullet (line 12): "`records/c22/return/verdict.json` (SHA-256 `3c77fd3d...ce64`)".
   - The records: `3c77fd3d...ce64` is the hash of `verdict.json` as received (`return_files.sha256`, line 268). The file at the path named is the kept copy, with LF line ends (103,601 CR LF converted), and has `d7f80645f820134b0412ef3423a1d6f2b2eeb26bb5178d3e58fc1aa1796a58b1` (`return_kept.sha256`, line 261).
   - Correction: "come from `verdict.json` of the return package (SHA-256 `3c77...` as received; kept in `records/c22/return/` with LF line ends, SHA-256 `d7f8...`)".
2. **The README says more about the recomputation than the verdict document.** `joint/README.md`, the paragraph on `audit/` (line 28): "G-C2.2's recomputation was written while its evaluation ran, before its result was known".
   - The document (line 13) says this of steps 1 to 6 of `c22_recompute.py` only: step 7 and the packing of the solves were added afterwards, and `c22_write_verdict.py` was written after the run (line 14). The first line of the script's own description says "after the run". No record dates the script, so in either form the claim rests on the author's word.
   - Correction: "steps 1 to 6 of G-C2.2's recomputation were written while its evaluation ran, before its result was known; its step 7 and the two other scripts after the run", and the same in the script's description.
3. **The README's status row drops the limits of the fixed interpretation.** `joint/README.md`, row G-C2.2 of the status table (line 95).
   - The pre-specification fixes for a PASS: "The limits stated for a PASS of G-C2.1 hold: the 5 mm mesh, small strains, frictionless contact, the deformation theory under monotonic loading, and the gap of the reference model to the T-stub tests", and "it does not show which of the two changes is needed". The row has neither. The row of G-C1.3 carries its limit ("not the joint tests"), and the audit of G-C2.1 made the same point for that gate's row.
   - In the same row, "Eight member and level pairs of five members with a low yield stress remain above 10%" counts the pairs that are above 10% in at least one seed. In a single seed 6, 5 and 6 pairs are above 10%.
   - Correction: add "This compares the network with the reference model (5 mm mesh, small strains, frictionless contact, deformation theory under monotonic loading), not with the T-stub tests, and does not show which of the two changes is needed", and write "In each seed 5 or 6 of the 448 pairs remain above 10%; over the three seeds they are eight member and level pairs of five members with a yield stress below 300 MPa, the worst at 50% to 69%".
4. **An observation that carries no weight is offered for the restart.** `joint/docs/G-C2.2_verdict.md`, deviation 1, fourth bullet (line 61): "Two observations fit a restart with updates and do not prove one: ... the median time of a step of seed 5 fell from 0.75 s over the 75 epochs before the pause to 0.34 s over the 125 after it."
   - The two numbers are right (0.745 and 0.345 s). But the histories show the same two regimes inside runs that were not interrupted. Seed 6 ran its epochs 1 to 149 at 0.36 s a step in the mean, its epochs 150 to 192 at 0.74 s and its last two above 0.6 s; the slow stretch lasted from about 15:48 to 20:19 on 14 November (inferred from the epoch times). Seed 7 ran its epochs 1 to 16, 19 to 33 and 39 to 48 at 0.69 to 0.75 s a step, until about 01:34 on 15 November (inferred), and its epochs 49 to 200 at 0.37 s in the mean.
   - So the step time follows the use of the laptop, and its fall after the pause says nothing about a restart. Before the pause every epoch of seed 5 took 0.39 s a step or more, and 74 of the 75 more than 0.6 s, from the first epoch on.
   - Correction: drop the step time from this bullet, or add the two later slow stretches and say that the step time shows when the laptop was in use. The readings of the disk remain the operator's, outside the records, as the document says.
5. **The archive's listing publishes an account name.** `joint/records/c22/return_listing.txt`, all 283 lines.
   - The owner and group columns hold the name of the account under which the archive was packed: a machine-made name of three letters, a hyphen and 24 characters, which reads as the identifier of a working session (inferred). It is not a personal name, but it identifies the operator's environment and has no use in the record. The listing of G-C2.1 shows a neutral account there.
   - Correction: store the listing without these two columns, or with numeric owners, and say so where the document calls it "the archive's own listing" (line 10) and in the README (line 54).
6. **A kept launcher names other work of the owner.** `joint/records/c22/return/queue/start.bat`, line 4 (a comment).
   - The comment says that the installer's copy was "already checked for" something: one word and a year, which read as the name of a piece of the owner's work outside this repository (inferred). `c22_keep.py` replaces the folder and the operator's name and leaves this.
   - Correction: replace the words in `c22_keep.py` and declare it with the other differences (document, lines 70 to 76; README, line 54), then write `return_kept.sha256` and `keep_report.json` again; or leave the launcher out and list its hash, which makes eight files not kept.

## Missing

1. **A departure that the records show and the document does not list.** Section 0c of the runbook, the suite, ran from 11:43:40 to 11:58 on a checkout of commit `6d9da9b` (`preconditions.log`). The tag was made at 12:44:25, and sections 0a and 0b ran at 12:45 and 12:46. The runbook puts all of section 0 after the tag ("When"). It has no effect on the result: the commit is the one that the tag names, and I reproduced the archive's hash from it. The sentence "The records show no other departure" (line 68) should take it in. For completeness: the suite ran in an environment with numpy 2.5.3 and with the second sparse solver installed, where the laptop has numpy 2.4.6 and scipy's solver alone; the log says that the same 51 tests had passed with the laptop's solver before the push.
2. **The rule on other training.** The pre-specification says "No other training uses the GPU during the runs", and the runbook that the development queue is empty. The document does not say whether this held. The return package cannot show it: it holds only the gate's jobs of the queue. What the records show is that no job of the queue ran between the gate's jobs, and that the machine carried another load for about 8 h of seed 5, 4.7 h of seed 6 and 4.2 h of seed 7 (error 4). The document should state, on the owner's or the operator's word, that this load was the owner's use of the laptop and that nothing else trained.
3. **Reported readings that are only in `verdict.json`.** The pre-specification lists as reported "Every metric G-C2.1 reported, for both readings", and G-C2.1's pre-specification asked for them "by level and overall" on the held-out and the tested members. The document gives the other readings as medians over all pairs of the two held-out sets. It has no table of them by level (G-C2.1's verdict has "The other readings by level") and none for the tested members (G-C2.1's has "Every reading of the tested members, by level" and "The tested members overall"). Either add these tables or say that these readings are in `verdict.json` only.
4. **The paragraph "Independent audit"** (line 16) says that none has been made. It will need this audit's result.

## Smaller points

- **Claims that need a source or "(inferred)".**
  - "made on the laptop ... between 12:12 and 12:15 GMT" (line 9): the folder is dated 12:12 and the newest member 12:13:53; the gzip header carries no time; nothing in the package gives 12:15.
  - Deviation 6, "No error of a prediction was computed or read before the evaluation ended": this is the operator's statement. The records support it only as far as the order of the queue's jobs goes.
  - Deviation 1, the inference from the unchanged library version "in the three histories" (line 60): the history of seed 5 carries the version written at its first start, because a resumed run takes its history from the checkpoint. Only the histories of seeds 6 and 7 show the version after the pause. Write "in the histories of seeds 6 and 7".
- **The verdict block does not give the raw reading.** The fixed interpretation says "Any wording says so, and gives the raw reading beside it". The block "Verdict" (lines 80 to 84) names the reading but leaves the raw numbers to the next section. One more bullet would do: "The raw reading, reported and not judged: 1.36% and 10.54%; it would meet C1 and miss C2."
- **Deviation 5** does not name `incidents.log`, which the operator wrote into the package and which section 6 of the runbook does not list.
- **"Within the family the reading is weakest where the plateau is longest"** (line 133) is an explanation. The records show the association with a yield stress below 300 MPa and with the levels 6 and 8 mm, not its cause.
- **The owner is "he"** twice in deviation 1 (line 58); elsewhere the document keeps to roles. The same bullet, and the kept `incidents.log`, say what the owner used the GPU for during the pause; the pre-specification needs only that the owner paused the run to use the GPU. Whether that detail stays is the owner's choice.
- **`return_files.sha256`** lists the two launchers with Chinese names in escaped form (lines 207 and 208), so a plain `sha256sum -c` on the unpacked package cannot check these two lines; the other 266 it can.
- **The kept `queue/make_jobs.py`** reads `home() / "W/queue"` after the replacement. This is declared, but the kept file is no longer the script that ran.
- **README, line 79**: "The files ending in `_text.md` and `_numbers.md` are the parts each verdict is assembled from". G-C2.2's verdict has no such parts; its part "Numbers" is written into the one file.
- **The time of the stamp** (optional): the pre-specification and the document give 08:59 GMT; the commit is dated 11:17:03 and the tag 12:44:25. All three lie before the generation at 12:53:48.
- **`c22_recompute.py`**: `--records` compares the epoch seconds of the log with the history within 0.0051 s, although the log prints the stored value; an exact comparison is stricter (mine was exact, and they are equal).
- **`c22_write_verdict.py`** has "132 members" as fixed text in its line on the prediction files; the check behind it uses the manifest's members.
- **The 140 JSON files of `records/c22/audit/`** end without a line end, unlike `keep_report.json`. Harmless.
- **The loss of single epochs.** The runbook's comment expects the loss "over its last ten epochs ... near 10.34 to 10.37". The means are 10.364, 10.345 and 10.361, as the document says; the single epochs of those ten run from 10.27 to 10.43.

## Not checked

- **The training.** The model states stayed on the laptop. That the returned predictions are the outputs of the trained networks, and that the resumed run of seed 5 drew the same members and levels as an uninterrupted one, follows from the stamped code and the host check (inferred), not from a recomputation.
- **That no member of seed 20261113 existed before the stamp.** This rests on the pre-specification. I checked only that the stamped tree uses the seed nowhere else and that the queue generated the members after the tag.
- **Exact solves outside my sample.** I solved 161 of the 5,544 pairs: 107 of the 1,344 judged ones, 30 of the 1,344 of the raw reading on the fresh members, and 24 of the 2,856 of the two reported sets. For the other judged pairs I rely on the author's stored recomputation, which I compared with the returned rows and did not run again. For the raw reading and the reported sets nobody has recomputed the other 4,146 judged errors.
- **The metrics that need the energy** (gap, bound, stress reading, the two overlaps, bolt force, displacement norm): I did not compute them from the fields. I compared the author's stored values with the returned rows for all 5,544 fields, and I computed the float64 energy only for the 30 fields of the minimum check.
- **The steps `--regenerate`, `--fields`, `--select`, `--curves` and `--resolve`** of the author's script were not run again; my own regeneration, sample of solves and one re-solve stand beside them.
- **The 51 tests** of the runbook were not run.
- **Statements outside the records**: the owner's message of 21:13, the readings of the disk, whether the laptop was restarted, what the operator read during the runs, what loaded the laptop in the slow stretches, and when the recomputation script was written.
- **`queue/setup_log.txt`**: read only to confirm that the driver version named in the document stands in it once. I quote nothing from it.
- **Spelling**: by a list of patterns and by reading, not with a dictionary.
- **The remote repository**: nothing was fetched or pushed. The tag and the commits were read in the local repository only.
- **Files of the repository that the commit does not touch**, the folder `records/c22/host_check/` among them.

## Scripts

All are in `joint/audit/independent/G-C2.2/`. None imports the author's audit scripts. Those that load the stamped library were run with `FEJOINT_SOLVER=legacy` and one linear algebra thread.

A note on my own handling: my first runs imported the stamped library from the export of the stamped commit that I was given, and so left bytecode caches in three of its folders (`joint/c22`, `joint/c2`, `joint/fejoint`). I removed them and compared the export with a fresh export of commit `6d9da9b`: no difference. Later runs used a fresh export in `scratch/` and wrote no bytecode. No stamped file was changed at any time.

| Script | What it checks |
|---|---|
| `a1_criteria.py` | C1, C2 and every stored summary from the per-pair rows, with my own quantile |
| `a2_select_pairs.py` | the choice of the 161 pairs |
| `a3_recompute_pairs.py` | the judged error of the chosen pairs with exact solves, my own driver on the stamped library |
| `a15_pairs_summary.py` | the agreement of those pairs with the returned values, by class |
| `a13_cold_start.py` | the judged error with the solve started from zero |
| `a14_resolve_label.py` | one label solved again |
| `a9_regenerate.py` | all 644 instances regenerated, their hashes against the manifest |
| `a10_all_fields_force.py` | force and end displacement of all 5,544 fields against the rows, numpy only |
| `a4_run_checks.py` | configuration, code hashes, sample (own sampler), ledger, histories against logs, queue, host check |
| `a5_condensed_reading.py` | the condensed fields from their parts, the limits of the amplitude, the minimum in float64 |
| `a7_document_tables.py` | 759 cells of the generated tables |
| `a12_text_numbers.py` | the numbers behind the prose |
| `a8_author_outputs.py` | the author's stored outputs against `verdict.json` and against my pairs |
| `a6_kept_copy.py` | the kept copy against the received package, the files left out, the privacy search |
| `a11_commit_checks.py` | line ends, paths, dashes, characters and spelling of the 410 paths |

---

**What was done after round 1 (the author)**

Errors
1. The hash of `verdict.json`: corrected. The document gives both hashes and says which copy has which.
2. The README on the recomputation: corrected as proposed, and the same in the description of `audit/c22_recompute.py`. Both say that this is the author's statement and that no record dates the scripts.
3. The README's status row: the limits of the fixed interpretation and "does not show which of the two changes is needed" are added, and the pairs above 10% are given for a seed and over the three seeds.
4. The time of a step: taken out of the observations on a restart. Deviation 3 of the document now lists the slow stretches of the three runs with their hours, and deviation 1 says that the fall of the step time after the pause says nothing about a restart. The clock times of the stretches in the document are the author's, inferred from the starts of the runs and the epochs' times: about 15:40 to 20:10 on 14 November for epochs 150 to 192 of seed 6, where the report has 15:48 to 20:19, and until about 01:30 on 15 November for seed 7, where the report has 01:34.
5. The archive's listing: stored again with numeric owners (`tar --numeric-owner -tvzf`, at UTC). The document and the README say so.
6. The launcher: `audit/c22_keep.py` now replaces the name of the other work by "another project". This is declared in the script, in the document, in the README and in `keep_report.json` (`words_replaced`); `return_kept.sha256` and `keep_report.json` were written again.

Missing
1. The suite before the tag: listed as deviation 7 and named in the preconditions.
2. The rule on other training: deviation 3 states the rule, what the queue's records show, the operator's statement that nothing else was queued, and that what loaded the laptop in the slow stretches is not recorded.
3. The reported readings: tables added to the part "Numbers" by `audit/c22_write_verdict.py`: the other readings by level for the two held-out sets in both readings, the tested members overall, and every reading of the tested members by level.
4. The paragraph "Independent audit": written.

Smaller points
- "between 12:12 and 12:15": marked as the operator's record, with what the archive and the laptop show.
- Deviation 6: marked as the operator's statement, with what the records show.
- "in the three histories": now "in the histories of seeds 6 and 7".
- The verdict block: the raw reading is added as a bullet.
- Deviation 5: `incidents.log` is named.
- "weakest where the plateau is longest": replaced by the association that the records show.
- "he": the bullet keeps to roles. What the owner used the GPU for during the pause is left out: the document says "for other things", and `audit/c22_keep.py` replaces the words in the kept `incidents.log` likewise, declared with the other differences. With it 192 files are kept byte for byte, not 193.
- The escaped names in `return_files.sha256`, and the kept `queue/make_jobs.py`: both stated in the document.
- The README's line on `_text.md` and `_numbers.md`: corrected.
- The time of the stamp: the date of the commit is added to the document.
- `audit/c22_recompute.py --records`: the comparison of the seconds is exact now; `records.json` is unchanged.
- `audit/c22_write_verdict.py`: the number of members is computed from the manifest.
- The JSON files without a final line end: left as they are.
- The loss of single epochs: the range is added to the run record.

---

**Round 2, as delivered**

# Independent audit of the verdict of gate G-C2.2: round 2

Report of the independent auditor to the author, 15 November 2026, on the corrected commit (local name `f7a500e`, parent `6d9da9b`), which has not been pushed. The rules are those of round 1: I changed none of the author's files, pushed nothing and sent nothing. In this round I changed two of my scripts and added two (listed at the end); the outputs are in my folder `scratch/`. Line numbers are those of the corrected commit.

**Conclusion.** The corrections of round 1 are right and complete for errors 1 to 5, for the four omissions and for the smaller points, and the author's notes say what was done. The 3,330 cells of the tables that were added agree with my own derivation from `verdict.json`, as do the 759 earlier cells, and nothing that bears on the verdict has changed: the outputs of the recomputation are untouched, and the kept copy differs from the one of round 1 in two declared lines. Two errors remain, both about what the commit publishes: the script that removes three strings carries them in hexadecimal, and the names of the two launchers that are left out still say, in three record files, what the words removed from `incidents.log` said.

## Verified

**1. The corrections of round 1, point by point**

- **Error 1 (the hash).** The document (line 12) gives `3c77fd3d...ce64` for `verdict.json` as received and `d7f80645...58b1` for the kept copy. Both are right (`return_files.sha256`, line 268; `return_kept.sha256`, line 261).
- **Error 2 (when the recomputation was written).** The README (line 28), the document (line 13) and the description of `c22_recompute.py` now agree that steps 1 to 6 came before the result and the rest after, and each marks this as the author's statement. One small difference is under Smaller points.
- **Error 3 (the status row).** The row of the README (line 96) carries the limits of the fixed interpretation and "it does not show which of the two changes is needed", and gives the pairs above 10% for a seed (5 or 6 of 448) and over the three seeds (eight pairs of five members).
- **Error 4 (the step time).** Deviation 1 (line 65) keeps the disk as the one observation and says that the fall of the step time says nothing about a restart. Deviation 3 (line 68) lists the slow stretches. Its numbers are right (`b2_round2_step_times.py`): 160 epochs took 0.6 s a step or more (74, 45 and 41 by seed), in the stretches named, with 7.89, 4.70 and 4.21 hours; 10 epochs lie between 0.38 and 0.6 s and 430 below 0.38 s. The clock times are discussed in item 3.
- **Error 5 (the listing).** `return_listing.txt` is identical to the output of `tar --numeric-owner -tvzf` on the received archive at UTC (283 lines); its owner column holds one pair of numbers. The document (line 10) and the README (line 55) say so.
- **Error 6 (the launcher).** In the kept `queue/start.bat` the name is replaced by "another project", once, and this is declared in the document (line 80), the README (line 55), the script's description and `keep_report.json` (`words_replaced`). The correction is not complete: error 1 below.
- **Missing 1.** Deviation 7 (line 73) and the preconditions (line 31) give the suite's times and the tag's as `preconditions.log` has them.
- **Missing 2.** Deviation 3 (line 69) states the rule and what the records show. Two adjustments are under Smaller points. The last two sentences wait for the owner; as they stand they claim nothing that the records contradict, and each names its source.
- **Missing 3.** The tables are added (item 2), and the section on the other reported readings points to them (line 138).
- **Missing 4.** The paragraph is written (item 3).
- **Smaller points.** Each of the fourteen entries of the author's notes describes what I find in the corrected commit (one claim in them is the subject of error 2): the source of "12:12 and 12:15", the operator's statement in deviation 6, "the histories of seeds 6 and 7", the raw reading in the verdict block (line 93, with the right numbers), `incidents.log` in deviation 5, the association in place of the explanation (line 144), roles in place of the pronoun, the two statements on `return_files.sha256` and `queue/make_jobs.py` (lines 85 and 79), the README's line on the parts, the date of the commit (line 5), the exact comparison of the seconds, the computed number of members, the JSON files left as they are, and the range of the single epochs' losses (line 49; 10.27 to 10.43 is right).

**2. The new tables** (`b1_round2_tables.py`, `a7_document_tables.py`)

- I derived every cell of the three new groups of tables with my own code from the per-pair rows of `verdict.json`, finding the tables by the names of their columns: 3,330 cells, none differing.
  - The other readings by level, fresh held-out members: 42 rows, 462 cells. The same for the held-out members of G-C2.1: 42 rows, 462 cells.
  - The tested members overall: 30 rows, 390 cells.
  - Every reading of the tested members by level: 168 rows, 2,016 cells.
- The sentence above the first of them is right: of the 5,544 returned rows none has an infinite distance and none a field that the reference code could not evaluate.
- The 759 cells of round 1 are unchanged: derived again on the corrected document, none differs. In all 4,089 cells, none differing.
- `c22_write_verdict.py` of the corrected commit, run on the kept records and the stored outputs, writes the whole part "Numbers" byte for byte: 532 lines, 56,133 bytes (306 lines more than in round 1).

**3. The new and changed statements of the document**

- I read the 30 changed or new lines of the text part (lines 1 to 151) against the records. Every number in them is right at its rounding. What rests on a statement outside the records is now marked as such.
- **The clock times of deviation 3.** Neither the author's times nor mine can be called right: the records fix them only between two bounds. A run's history gives the seconds of each epoch but not the time of the set-up before the first epoch nor of the predictions after the last. Counted forward from the run's start line with no set-up, a time is the earliest possible; counted back from its end line with no predictions, the latest possible. The two middle columns add an allowance to each count.

  | End of epoch | Earliest possible | Forward, with 100 s of set-up | Back, with 249 s of predictions | Latest possible | The document |
  |---|---|---|---|---|---|
  | Seed 6, 149 (the stretch begins) | 15:38:23 | 15:40:03 | 15:47:58 | 15:52:07 | about 15:40 |
  | Seed 6, 192 (it ends) | 20:09:04 | 20:10:44 | 20:18:39 | 20:22:48 | about 20:10 |
  | Seed 6, 198 | 20:28:11 | 20:29:51 | 20:37:46 | 20:41:55 | about 20:30 |
  | Seed 6, 200 | 20:39:23 | 20:41:03 | 20:48:59 | 20:53:08 | about 20:40 |
  | Seed 7, 48 (the last stretch ends) | 01:31:51 | 01:33:31 | 01:33:49 | 01:37:58 | about 01:30 |

  - The 100 s and the 249 s are what the two parts of seed 5 show: its first part reaches the end of epoch 75 at 21:17:52 with 100 s of set-up, where `incidents.log` has the checkpoint at 21:17:53, and its second part has 249 s outside its epochs.
  - Seed 7 has 368 s outside its epochs, about these two together (349 s); so both counts meet, and its last stretch ended at about 01:34. The document's "about 01:30" leaves out the set-up and is three to four minutes early.
  - Seed 6 has 824 s outside its epochs, 475 s more than the two allowances. The records do not show where they lie (the run's start line itself came 57 s after the queue started the job, against 0 to 8 s for the other starts). So its long stretch began between about 15:40 and 15:48 and ended between about 20:11 and 20:19. The document's times are the early edge of this, my times of round 1 the late edge.
  - With "about" the document's times can stand. "To within ten minutes" would say what the records support.
- **Deviation 7 and the preconditions**: right (item 1).
- **Deviation 1**: roles throughout; the times are those of the records; the inference on the library version now rests on the histories of seeds 6 and 7, which carry the version of the host check.
- **"The records as kept"** (lines 77 to 85). My comparison of the kept files with the received ones (`a6_kept_copy.py`): 192 identical; 60 differ by line ends alone; 7 by line ends and declared lines (six logs with one line each for the path; `queue/start.bat` with two lines, one for the operator's name and one for the other name); 2 without a change of line ends by one declared line each (`queue/make_jobs.py` for the path, `incidents.log` for the replaced words). No other line differs. So 67 files with line ends converted, 69 files changed, 192 unchanged, 261 kept and 7 left out, as the document says.
- **The paragraph "Independent audit"** (lines 16 to 20) states my findings of round 1 correctly: the numbers (161 pairs within 5.4e-14, 107 of the 1,344 judged pairs, 54 others, 644 instances, 600 epoch lines, 759 cells) and the list of the six errors and four omissions are those of my report. Three remarks on its wording are under Missing and Smaller points.

**4. The kept copy again**

- `c22_keep.py` of the corrected commit, run on the received package, reproduces the 261 kept files and `keep_report.json` byte for byte.
- `return_kept.sha256`: 261 lines, all equal to the kept files. `return_files.sha256` is unchanged.
- Between the two audited states only five files under `records/c22/` differ: `keep_report.json`, `return_kept.sha256`, `return_listing.txt`, and one line each of `return/incidents.log` and `return/queue/start.bat`.
- `c22_recompute.py --aggregate` and `--records` of the corrected commit, run again, write files identical to the stored `aggregate.json` and `records.json`; the folder `records/c22/audit/` is unchanged from round 1.
- **Privacy search**, now over all 426 paths of the commit, the report file and my scripts as filed among them (265 text files and the two of the host check; the binary files are those of round 1): no path of a personal folder, no account name, no name of the owner or of a collaborator (as far as known to me), no e-mail address, no host name, and none of the three removed strings in plain text. New in this round is a search for the removed strings in encoded form, which finds error 1 below.

**5. The report file** (`joint/docs/reviews/audit_report_G-C2.2_2026-11-15.md`)

- It contains my round 1 report as one block without a change: the 36,359 characters and 217 lines of the text that I checked before sending it, identical to the copy that the author saved.
- The header is accurate: the roles, the date, round 1 at about 17:55 GMT, what round 1 audited, and the tree `4b307f06...f5c2` of the state then audited (read in the local repository). The time of round 2 is a placeholder (Missing 1).
- The author's notes after the report describe the corrections as I find them, with two exceptions that follow from the errors below: the note on error 6 (line 243) and the note on the pronoun (line 258) say that the name is replaced and the words are left out, which holds for the kept files and not for the commit.
- The 15 scripts filed in `joint/audit/independent/G-C2.2/` are mine of round 1 (13 are identical to my present ones; the two others differ by my changes of this round).

**6. The commit as a whole** (`a11_commit_checks.py`, read-only git commands)

- 426 paths, 425 added and `joint/README.md` modified, the same list as `proposed_changes2.txt`; the difference from the state of round 1 is `round2_changes.diff` exactly (26 files). Every added file has mode 100644. The export that I was given equals a fresh export, and the working tree is clean.
- 265 text files, none with a carriage return, a tab or trailing blanks; 161 binary files; 126 MB in all.
- No tracked file matches a rule of `.gitignore`; the 261 kept files and the 15 scripts are all in the commit.
- No absolute path of a machine in a new file, apart from the library's build path inside its warning in six logs, as in round 1.
- Characters outside ASCII and dashes: only in the filed copy of my `a11_commit_checks.py` (five dash characters in line 21), which I have corrected (item 7), and the two accented letters of the README's first paragraph, as before.
- British spelling: the list of patterns finds nothing in the document, the README's changed lines, the report file and the author's three scripts. In my scripts it finds only code: the pattern list itself and two argument names of the standard library.

**7. My script `a11_commit_checks.py`**

- As asked, I wrote the five dash characters of line 21 as escapes. The file is ASCII now, the table of dashes has the same five entries, and nothing else in it changed. All 17 of my scripts are ASCII.

## Errors

1. **The script that removes the strings publishes them.** `joint/audit/c22_keep.py`, lines 30, 33 and 34.
   - The three strings that the script takes out of the kept copy stand in it as hexadecimal byte strings: the name by which the owner addresses the operator (line 30), the name of the owner's other work (line 33) and the words on the use of the GPU during the pause (line 34). I checked without printing them that each decodes to printable text that stands in the received file and not in the kept one. Any reader can decode them, so the corrected commit still publishes all three, and error 6 of round 1 is corrected in the kept copy only.
   - Line 30 was there in round 1. I read it then and did not raise it; the same holds for it, though the author may judge a name of that kind differently from the two others.
   - Correction: give the strings to the script from outside the repository, as arguments or in a small file that the owner keeps with the package as received, and record only the counts in `keep_report.json`, as now. The document and the script's description should then say that the kept copy can be made again only with those strings.
2. **The names of the two launchers say what the removed words said.** `joint/records/c22/return_files.sha256` (lines 207 and 208), `joint/records/c22/return_listing.txt` (lines 219 and 220) and `joint/records/c22/keep_report.json` (lines 21 and 26).
   - The two launchers that are left out have Chinese file names, which stand in these three files in escapes. Both names say what the owner used the GPU for during the pause: they hold the word that the replaced words of `incidents.log` gave in English (checked on the decoded names, without printing them). So the words are replaced in `incidents.log` (document, line 81), but the commit still says the same in these three files, and the author's note that what the owner used the GPU for "is left out" (report file, line 258) does not hold for the commit as a whole.
   - This is wrong whichever way the owner decides. If the words are to stay out, the two names need a neutral placeholder in all three files, declared with the other differences, and the listing is then the archive's listing with two names replaced. If they may stay, the replacement in `incidents.log` and its declarations can be taken back.

## Missing

1. **The bullet "Second round" (document, line 19) and the time in the header of the report file (line 3).**
   - The time: this report was delivered at about 18:30 GMT on 15 November 2026.
   - What the bullet may truthfully say of this round: the auditor checked each correction against the records; derived the 3,330 cells of the added tables and the 759 earlier ones again with its own code, none differing; found that the writer produces the part "Numbers" byte for byte, that `c22_keep.py` reproduces the kept copy and its report, that the two steps of the recomputation that it ran again reproduce their stored outputs, and that the listing is the archive's with numeric owners; compared the report file with the report as delivered; and checked the 426 paths of the commit. It confirmed the corrections of round 1 except that of error 6, and found two errors, both about what the commit publishes and none about a number: the removed strings in hexadecimal in `c22_keep.py`, and the names of the two launchers. It did not repeat the exact solves, the regeneration of the instances or the checks of the run, because the records and the stamped code had not changed.
   - The sentence "They are corrected here, in the records as kept and in the README" (line 18) will be true once error 1 is corrected.
2. **My scripts as filed.** The README (line 37) lists the 15 scripts of round 1. Two were added in this round and two changed (see Scripts), and the filed copies of the two changed ones are those of round 1. The sentence of the README on the reviews (line 82) already speaks of two reports.

## Smaller points

- **The paragraph "Independent audit".**
  - "What it confirmed, with its own code" (line 17): the exact solves and the regenerated instances came from the stamped library, driven by my code. "With its own code and, for the solves and the instances, its own driver on the stamped library" is exact.
  - "One of them the absence of this paragraph" (line 18): the paragraph was there and said that no audit had been made. "One of them this paragraph, which could not yet report an audit" is exact.
- **Deviation 3, the rule on other training** (line 69).
  - "Each started within a second of the end of the one before" holds for the gate's jobs apart from the pause: from 21:20:15 on 13 November to 01:43:07 on 14 November the queue was closed and ran nothing. Add "apart from the pause, when the queue was closed".
  - "Its returned records hold the gate's jobs alone" follows from section 6 of the runbook, which copies no other job files; it is not a finding about the queue. What the records show is the unbroken sequence; that nothing else was queued is the operator's statement, as the sentence says.
- **What was added after the run** is told in three ways: the document (line 13) names step 7 and the packing of the solves; the script's description adds the option `--reverse`; the README (line 28) names step 7 and the two other scripts. The script's description is the fullest; the two others could follow it.
- **A weaker trace of the removed strings.** `return_files.sha256` gives the hash of each file as received. A reader who guesses a replaced string can therefore confirm the guess from the kept file. This cannot be avoided while the hashes as received are published, and the strings are short. It is the owner's choice; a sentence in the document would make it a known one.
- **README, line 80**: "the gates before G-F1" is right in the order of the stamps (G-C2.1 was stamped before G-F1) and not in the order of the README's own table, where G-C2.2 stands before G-F1. Naming the gates would remove the doubt.
- **32 cells of the new tables print "-0.00%"**: a median or value below zero that rounds to zero. They are right; a note under the tables would spare the reader a question.
- **The name of line 30 of `c22_keep.py`** occurs in lower case, inside paths, in three review files that are already in the repository and are not part of this commit (`docs/reviews/review_reports_G-C2.1_2026-11-06.md`, `audit_reports_G-C2.1_2026-11-08.md`, `review_report_G-F1_explore_2026-11-08.md`). If the name is to stay out of the repository's text, these are the other places.
- **The message of the corrected commit** is a draft ("local draft", "not pushed"). The message of round 1 gave both readings, as the fixed interpretation asks; the final message should do so again.

## Not checked

- **Everything listed under "Not checked" in round 1** remains so. In particular I did not repeat the exact solves, the regeneration of the instances, the re-solve of a label, the checks of the condensed reading or the checks of the run: the records, the outputs of the recomputation and the stamped code are unchanged, which I verified by comparing the two states file by file.
- **The owner's answers that are still open**: what loaded the laptop in the slow stretches and whether anything else trained on the GPU; whether the words on the use of the GPU stay out.
- **Statements that rest on the owner's or the operator's word** and were added in this round: the time of the archive file on the laptop (12:15), that the operator queued nothing else, that the owner was using the laptop on 13 November, and where the owner keeps the files that are left out.
- **The final texts of the bullet "Second round", of the header's time and of the author's notes on this round**, which do not exist yet, and the final commit and its message.
- **Spelling**: by the list of patterns and by reading, as before.

## Scripts

To be filed in `joint/audit/independent/G-C2.2/` with those of round 1. None imports the author's audit scripts.

| Script | Round 2 | What it checks |
|---|---|---|
| `b1_round2_tables.py` | new | the 3,330 cells of the three new groups of tables, and the sentence on the returned rows |
| `b2_round2_step_times.py` | new | the slow stretches, their hours, and the earliest and latest clock times that the records allow |
| `a6_kept_copy.py` | changed | now also: other declared replacements given on the command line; every path that the commit changes; the removed strings in hexadecimal and base64. Its output names files by their path from the repository's root |
| `a11_commit_checks.py` | changed | the five dash characters of line 21 written as escapes; nothing else |
| the other 13 | unchanged | identical to the filed copies; `a7_document_tables.py` was run again on the corrected document |

---

**What was done after round 2 (the author)**

Errors
1. The strings are out of `audit/c22_keep.py`. It reads the five strings that it replaces from a file that is not in the repository and that the owner keeps with the package as received; this holds for the operator's name as well. The script's description and the document say that the copy cannot be made again without that file. The kept files are unchanged by this: the same 261 files, byte for byte.
2. The words stay out. The names of the two launchers are replaced by `queue/<launcher of the pause>.bat` and `queue/<launcher of the continuation>.bat` in `return_files.sha256`, `keep_report.json` and `return_listing.txt`, which `audit/c22_keep.py` now writes itself. This is declared in the script, in the document and in the README. The notes after round 1 on error 6 and on the pronoun hold for the commit only from here on.

Missing
1. The time in the header and the bullet "Second round" of the document are written from the report.
2. The 17 scripts are filed as they stood after round 2, and the README lists them.

Smaller points
- The paragraph "Independent audit": both wordings are taken over.
- Deviation 3, the rule on other training: "apart from the pause, when the queue was closed" is added, and the sentence now separates the unbroken sequence, which the records show, from the operator's statement.
- Deviation 3, the clock times: they are now the middle of the report's two allowances, about 15:45 to 20:15 and 20:35 to 20:45 for seed 6 and about 01:35 for seed 7, with "to within ten minutes" for seed 6 and its reason.
- What was added after the run: the document and the README follow the script's description.
- The weaker trace of the replaced strings: stated in the document.
- The README's line on the parts of the verdicts names the gates.
- "-0.00%": a note at the head of the part "Numbers".
- The name in three review files that are already in the repository: they are not part of this commit and are left as they are; the owner is told.
- The message of the commit: the final one gives both readings.

---

**Round 3, as delivered**

# Independent audit of the verdict of gate G-C2.2: round 3

Report of the independent auditor to the author, delivered at about 15:55 GMT on 17 November 2026, on the commit as it stands (local name `0d50429`, parent `6d9da9b`), which has not been pushed. The round was begun on 15 November on an earlier state and was cut off before a report; everything below was checked again on the present state. The rules are those of rounds 1 and 2: I changed none of the author's files, pushed nothing and sent nothing. The author gave me the file of the five strings to read. I print and quote none of its values; my scripts give counts only. Line numbers are those of the present state.

**Conclusion.** Both errors of round 2 are corrected. None of the five strings is left in the 430 paths of the commit, in plain text or in any of the encoded forms that I searched, and `c22_keep.py`, run with the file of strings and the archive's listing, makes the kept copy, its report and its three lists again byte for byte. The final texts state my two earlier rounds and the records correctly. I found no error; what is still to be written, and four smaller points, are listed below.

## Verified

**1. The strings: error 1 of round 2** (`b3_round3_strings.py`)

- **The search.** All 430 paths of the commit, my filed scripts and the report file among them: 269 text files, and 161 binary files, of whose 2,629 arrays the 18 that hold text or single bytes were read, with the names of all arrays.
  - Each of the five strings was searched in plain text (without regard to case), in UTF-16 and UTF-32, in hexadecimal (bare, with separators, as byte escapes), in base64 (both alphabets, the three alignments), in unicode escapes, in octal escapes, in percent-encoding, as numeric character references, as lists of decimal bytes, reversed and in rot13.
  - Parts were searched too: a file name without its extension; every character outside ASCII singly, plain and in four escaped spellings; the last word of a string of several words, with its plural and its -ing form, as a whole word; a name without its final digits, as a whole word.
  - Result: no occurrence of a string, in any form, and none of a part.
- **Controls.** The same search on the state of round 2 finds the three hexadecimal strings in `c22_keep.py` and the two names in the three lists; on the state of round 1 it finds the plain words in the document, in `incidents.log` and in `queue/start.bat`. So the search can find them.
- **`c22_keep.py`** no longer holds a string: it reads the five from the file. Run with that file and the archive's listing, it reproduces byte for byte the 261 kept files, `keep_report.json`, `return_files.sha256`, `return_kept.sha256` and `return_listing.txt`. The listing that I gave it is my own output of `tar --numeric-owner -tvzf` on the received archive at UTC.
- **What the texts say.** The script's description, the document (line 86) and the README (line 35) say that the strings are read from a file outside the repository and that the copy cannot be made again without it. That is the case. One wording is under Smaller points.
- My 19 scripts as they stand hold none of the five strings either (plain, hexadecimal, base64 and unicode escapes checked).

**2. The two names: error 2 of round 2** (`b4_round3_lists.py`)

- **`return_files.sha256`**: 268 lines, one for every file of the received package and no other; all 268 hashes equal the files; the two placeholder lines carry the hashes of the two launchers, each under the right placeholder; 266 lines name a file that exists under that name, which is what `sha256sum -c` can check, as the document says (line 89).
- **`return_listing.txt`**: 283 lines; it differs from the archive's listing with numeric owners in the two lines of the launchers, and there in the name alone.
- **`keep_report.json`**: the seven files left out are the received files less the kept ones, with the right hashes and sizes, the two launchers under their placeholders; its 261 rows carry the right hashes as received and as kept; its counts are 67 files with line ends converted, 7 with the folder replaced, 1 with the name, 2 with words, 192 unchanged.
- None of these three lists, nor `return_kept.sha256`, holds a character outside ASCII or an escape sequence.
- **Nothing else in the commit says what the removed words said**: this is the search of parts in item 1 (the characters of the two names singly, and the last word of the removed words in its three forms).
- **The placeholders are declared** in the script's description, in the document (lines 10 and 84) and in the README (line 55).
- **The kept files against the received ones** (`a6_kept_copy.py`): 192 identical, 60 with line ends converted alone, 7 with line ends and declared lines, 2 with one declared line each, and no other difference. The 261 kept files are those of round 2, byte for byte; under `records/c22/` only the three lists with the placeholders have changed since then.

**3. The final texts**

- **The paragraph "Independent audit"** (lines 16 to 22) states my rounds 1 and 2 correctly: the numbers of round 1, the six errors and four omissions, and for round 2 the 3,330 and 759 cells, the 426 paths, "the corrections except one" and the two errors with their nature. "In three rounds on 15 and 17 November 2026" is right. Its sentence on the third round is still a stub; see Smaller points.
- **Deviation 3** (lines 70 and 71).
  - The clock times are the middle of the two counts with their allowances that I gave in round 2. For seed 6 they are about 15:45 to 20:15 and 20:35 to 20:45, each within nine minutes of the earliest and of the latest time that the records allow, so "to within ten minutes" holds; "about 14 minutes" outside its epochs is right (824 s). For seed 7, "about 01:35" is within two minutes of both counts with their allowances.
  - The sentence on the rule separates what the records show (the unbroken sequence, apart from the pause) from the operator's statement, and is right.
  - The last sentence gives the owner's statement of 17 November 2026 as the owner's, with its date. The records can neither confirm nor contradict it. Nothing else in the document depends on the two sentences that it replaces.
- **"The records as kept"** (lines 79 to 89): every bullet and count agrees with my comparison and with the lists (67, six and one, one launcher with two replacements, one line of `incidents.log`, seven files, the two placeholders, 192, five strings, 266 of 268).
- **The README**: its changed lines (28, 35, 55, 80, 82) agree with the document and the scripts' descriptions. Line 37 is under Smaller points.
- **The author's notes after round 2** (report file, from line 408) say what was done. I find the two corrections, the two items under "Missing" and seven of the nine smaller points in the commit as described. Of the other two, one leaves three files outside this commit as they are and says that the owner is told, and one is a promise about the final message of the commit; neither can be checked in the commit.
- **The report file** holds my round 1 report (36,359 characters, 217 lines) and my round 2 report (21,568 characters, 134 lines), each once and without a change, identical to the copies that the author saved. Its header gives the rounds by day correctly; the time of round 3 is a placeholder.
- **The part "Numbers"**: `c22_write_verdict.py` writes it byte for byte (532 lines, 56,201 bytes, with the new note on "-0.00%"). The 3,330 cells of the added tables and the 759 earlier ones, derived again on the present document, do not differ.
- **The recomputation**: `c22_recompute.py` is unchanged since round 2. Its steps `--aggregate` and `--records`, run again, give the stored files in every entry but one: the entry `platform` of the environment block, which names the machine's kernel and has changed with a restart of the machine since 15 November.

**4. The commit as a whole** (`a11_commit_checks.py`, read-only git commands)

- 430 paths, 429 added and `joint/README.md` modified, the same list as `proposed_changes4.txt`. Every added file has mode 100644. The export that I was given equals a fresh export; the working tree is clean; the difference from the state of 15 November is `round3b_changes.diff` exactly.
- 269 text files, none with a carriage return, a tab or trailing blanks; 161 binary files; 126 MB in all.
- No tracked file matches a rule of `.gitignore`; the 261 kept files and the 19 scripts are in the commit.
- No absolute path of a machine in a new file, apart from the library's build path inside its warning in six logs. No path of a personal folder, no account name, no e-mail address.
- No dash character anywhere. The only characters outside ASCII are the two accented letters of the README's first paragraph.
- British spelling: the list of patterns finds nothing in the document, the README's changed lines, the report file and the author's scripts; in my scripts it finds only code (the pattern list itself, and names of functions and arguments).
- Of the 19 filed scripts, 18 are identical to mine. `b3_round3_strings.py` differs by a change that I made today (see Scripts).

## Errors

None.

## Smaller points

- **Still to be written.**
  - The sentence on the third round (document, line 20). It may truthfully say: in a third round, on 17 November 2026, the auditor searched the 430 paths of the commit for the five strings in plain text and in the encoded forms that its report lists, and found none; found that `audit/c22_keep.py`, run with the file of strings and the archive's listing, makes the kept copy, its report and its lists again byte for byte, and that the two names are replaced in all three lists; and found that the final texts state its two earlier rounds correctly. It found no error; its report lists what was still to be written and four smaller points.
  - The time of round 3 in the header of the report file (line 3): about 15:55 GMT on 17 November 2026.
  - The README (line 37) lists 17 of my scripts. The two of this round, `b3_round3_strings.py` and `b4_round3_lists.py`, are filed and not yet listed.
- **"Every point is corrected here, in the records as kept and in the README"** (document, line 21). The author's notes leave two smaller points as they are, each with its reason: the JSON files without a final line end (round 1) and the name in three review files that are not part of this commit (round 2). "Every error and omission is corrected here ...; what was done about each smaller point is in the author's notes" is exact, and it would also cover the points of this round.
- **The owner's answers of 17 November are not yet in the author's notes.** The note on Missing 2 after round 1 (report file, line 247) says that deviation 3 states "that what loaded the laptop in the slow stretches is not recorded"; the document now gives the owner's statement instead. The notes after this round are the place to say what changed on 17 November: the owner's statement in deviation 3, and the owner's agreement that the words stay out.
- **"Makes the copy and the three lists"** (document, line 86). The script writes four files beside the copy: `keep_report.json`, `return_files.sha256`, `return_kept.sha256` and, from the archive's listing, `return_listing.txt`. "The copy, its report and the three lists" is exact; the listing is a third input beside the package and the file of strings.
- **The weaker trace** (document, line 87) has one more part: the listing gives the size of each file as received, so the length of a replaced string follows from the size of the kept file. It needs no change; it belongs to the same sentence if the author wishes to be complete.
- **The message of the commit** is still the draft. The author's note says that the final one gives both readings.

## Not checked

- **Everything listed under "Not checked" in rounds 1 and 2** remains so. In this round I did not repeat the exact solves, the regeneration of the instances or the checks of the run: the kept files are those of round 2 and the outputs of the recomputation those of round 1, byte for byte, and the stamped code is unchanged.
- **The owner's statement of 17 November** (no other training on the GPU during the days of the runs; the slow stretches as the owner's own use of the laptop) and the owner's agreement on the words: I have them from the author only.
- **Where the file of strings and the files left out are kept**: the document says that the owner keeps them with the package as received. I read the file of strings where the author pointed me to it; it is not in the commit.
- **Forms of encoding that I did not think of.** The search covers the forms listed in item 1. The numeric arrays of the binary files were not searched; they are those of round 1.
- **The texts that do not exist yet**: the sentence on the third round, the author's notes on this round, and the final commit with its message.
- **Spelling**: by the list of patterns and by reading, as before.

## Scripts

To be filed in `joint/audit/independent/G-C2.2/` with the others. None imports the author's audit scripts, and none holds a private string: the strings are read from the owner's file at run time, and the outputs give counts and truth values only.

| Script | Round 3 | What it checks |
|---|---|---|
| `b3_round3_strings.py` | new on 15 November; changed on 17 November | the five strings in plain and encoded forms, and their parts, in every path of the commit. The change of 17 November: it also reads the arrays of the binary files that hold text or single bytes, and the names of all their arrays. The filed copy is the one of 15 November |
| `b4_round3_lists.py` | new on 15 November; unchanged | the three lists with the two placeholders against the received package and the archive's listing |
| the other 17 | unchanged | identical to the filed copies; `a6_kept_copy.py`, `a7_document_tables.py`, `a11_commit_checks.py` and `b1_round2_tables.py` were run again on the present state |

---

**What was done after round 3 (the author)**

- The sentence on the third round in the document, and the time of round 3 in the header of this file, are written from the report.
- The README lists the 19 scripts. They are filed as they stood at the end of round 3, `b3_round3_strings.py` with its change of 17 November.
- "Every point is corrected": the sentence now speaks of the errors and omissions and points to these notes for the smaller points.
- "The copy and the three lists": now "the copy, its report and the three lists", with the archive's listing named as an input.
- The weaker trace of the replaced strings: the sizes are added to the sentence.
- The owner's answers of 17 November 2026. The owner stated that no other training used the GPU during the days of the runs and that the slow stretches were the owner's own use of the laptop. The last sentence of deviation 3 gives this statement, in place of the two sentences that the note on Missing 2 after round 1 describes. The owner also agreed that the words on the use of the GPU during the pause stay out of the repository, so the replacement in `incidents.log` and the two placeholders stand.
- The message of the commit gives both readings.
- The auditor did not see the state after these last changes, which touch the document, the README, this file and the copy of `b3_round3_strings.py`. On that state the author ran three of the auditor's scripts again: `b3_round3_strings.py` finds none of the five strings and no part of one in the 430 paths; `b4_round3_lists.py` finds the three lists right; `a11_commit_checks.py` finds no carriage return, no dash and no absolute path of a machine apart from the library's build path.
- Later on 17 November 2026 the owner asked why the commit was so large (430 paths, 126 MB, of which 118 MB in array files) and decided that array files of this size stay out of the repository and are deposited at Zenodo; what is already in the repository's history is left as it is. The author took the 141 array files of the kept copy out of the commit (the 132 label files and the nine prediction files), added `audit/c22_deposit.py`, which makes the deposited archive and puts its files back, and `records/c22/deposit.json`, and changed the document and the README to say where the files are. The kept copy itself, its report, its lists and `audit/c22_keep.py` are unchanged. The owner asked for a fourth round on these changes.

---

**Round 4, as delivered**

# Independent audit of the verdict of gate G-C2.2: round 4

Report of the independent auditor to the author, delivered at about 17:50 GMT on 17 November 2026, on the state with the local name `c247c42` (tree `c2a47c36ddd7`, 291 paths, not pushed) and on `received5/`. Only what changed since round 3 was audited, under the rules of the earlier rounds. I quote none of the five strings.

## (a) Does the record still stand complete with the archive?

Yes, provided that the deposited archive is the one that I was given. The 120 files of `records/c22/return/` and the 141 of the archive are the 261 kept files, byte for byte.
- **The step** from the 430 paths: exactly the 141 files of `deposit.json` are gone, two paths are new, three text files differ, and the 120 files left are unchanged.
- **Record and archive.** The 141 entries agree with the files and both lists (64, 64 and 4 labels, 9 prediction files, 117,562,958 bytes). The archive has the size and hash of the record and the document. My own reader of the format finds 141 plain files in the listed order, headers as the record's `format` says, right checksums, zero padding, and outside the files no text but paths, numbers and the format's mark. Each member equals the file of the package as received.
- **The script.** `pack` on a whole kept copy writes the archive and the record again byte for byte (interpreter 3.11, 3.12 and 3.13). `restore` in a copy of the state gives the folder of the 430 paths; `sha256sum -c` then passes for all 261 lines, before it for 120. With the true record `restore` refused five changed archives before reading a member. With a record changed to fit, it refused a changed file, a member more or fewer, another order, links, an absolute name and names climbing out of `labels/`. `check` does what its description says.
- **The tables.** `c22_write_verdict.py` on the state without the arrays writes the part "Numbers" byte for byte and opens no array file.
- **The strings.** None of the five, in any form of round 3, in the 291 paths, the six other files of `received5/`, the archive's headers, the names of its 2,244 arrays or the archive as a stream of bytes. The stream has 89 matches of parts (2 of a last word, in `preds.npz` and `preds_condensed.npz` of `run_files/label_free_s5/`; 87 of single characters, in 15 and 18 files), all in compressed arrays of numbers: chance (inferred).

## (b) Errors

1. **"The array files" are not all deposited.** The kept copy has 161; the 20 of the host check (`return/smoke/`, 477,551 bytes) stay in the repository. Wrong as written: document lines 80 and 91; README line 35; `records/c22/deposit.json` line 3; `audit/c22_deposit.py` lines 1, 10 to 11 and 62; `received5/README.md` line 3. "The 141 array files" (document lines 11, 21; README lines 36, 56, 122) follows them. "The labels and the predictions" is exact.
2. **`audit/c22_deposit.py` is unsafe in two places.**
   - Lines 31 and 84: the test of a name admits `..` as the run's folder and backslashes. With a record and an archive changed together, `restore` wrote `preds_x.npz` beside `labels/`, still inside the target; where the backslash separates folders, such a name would leave the target (inferred; not run). The true record prevents both: the archive's hash is tested first (line 76).
   - Lines 47 to 70: `pack` does not test that the copy is whole. On the folder as the repository holds it, it wrote an archive of no file and a record with `n_files` 0, with exit status 0; given `records/c22/deposit.json`, it would replace the record.
3. **Statements that the removal made wrong, left unchanged.** `audit/c22_keep.py` lines 1 ("kept in the repository") and 5 (KEPT is `records/c22/return`). `audit/c22_recompute.py` line 16 names `records/c22/return` as RECORDS, where `--records` now stops with a missing-file error and `--fields`, `--curves` and `--resolve` read deposited files too; only the README (line 33) says that the archive is needed.
4. **README line 87.** The heading "Status on 13 November 2026" stands over a table that now gives the verdict of 15 November; the commit changes the row and not the heading. I missed this in rounds 1 to 3.

## (c) Omissions

- **No ignore rule.** After `restore` the 141 files are untracked in the checkout and no rule of `.gitignore` covers them, so a commit of everything would bring them back.
- **"The DOI was reserved before this commit"** (document line 91) is not true of the state that I saw; it must be true before the final commit. The copy of `deposit.json` in the deposit must carry the real DOI.
- **Still to be written**: document line 16 ("three rounds", "the three audit scripts") and the last sentences of lines 21 and 22; the report file's header (line 3) and the name of this state (line 6); README line 38; the author's notes.

## (d) Smaller points

- **Which scripts need the array files.** Beside those four steps of the recomputation, eight of my 19 scripts: `a3`, `a4`, `a5`, `a10`, `a13`, `a14` (labels or predictions), `a6` and `b4` (the whole kept copy against the package as received). The other eleven need none; eight of them, run without the arrays, gave their earlier results. So "the scripts of the independent audit" (document line 91) holds for eight.
- **`restore`** writes as it checks (four files before it refused a changed fifth); `check` tests neither single sizes nor the block `archive`. Both need a changed record.
- **Document line 20**, "four smaller points": my round 3 list has five; the count was mine.
- **The outward texts** overstate nothing: the metadata and the commit's message give the raw reading beside the verdict, and the deposit's README gives no result. The description names the condensed reading without saying what it is, which document line 117 asks of any wording. The texts name a branch, not a commit. The summary has 29 words and ends with "(suite 138)". The texts are ASCII, without a dash, British by my patterns and without the former name.
- **Confirmed**: "Written on 17 November 2026" (absent at 15:56 GMT, present at 17:07, so after the run); 126 MB and 118 MB; the author's reruns of `b3`, `b4` and `a11`; the changes after round 3 are those of the notes.

## (e) The placeholder `10.5281/zenodo.PENDING`

Five places, once each: `joint/records/c22/deposit.json` line 4 (the value of `doi`); `joint/docs/G-C2.2_verdict.md` line 91; `joint/README.md` lines 56 and 122; `received5/commit_message_slim.txt` line 9. In the last four it follows `https://doi.org/`. It is not in `received5/README.md`, `received5/zenodo_metadata.txt`, `audit/c22_deposit.py`, the report file or the archive. After the substitution, `pack` with the real DOI must write `deposit.json` byte for byte.

## (f) Not checked

- The deposit: that a DOI is reserved, that the deposited archive is this one, that the record is published. A download and `restore` after publication is the test.
- The owner's decision of 17 November: I have it from the author.
- That the suite of 138 passes: not run. No test and no tested code is among the 291 paths.
- `restore` where the backslash separates folders; other versions of the interpreter.
- Everything not checked in rounds 1 to 3; no solve, regeneration or check of the run was repeated.

**Scripts** to be filed, none importing the author's or holding a string: `c1_round4_step.py`, `c2_round4_deposit.py`, `c3_round4_restore_tests.py` (38 cases), `c4_round4_archive_strings.py`.

---

**What was done after round 4 (the author)**

- Error 1, "the array files". The texts now say "the label and prediction files": the document (the points on the return package and on the records as kept, and the paragraph on the audit), the README, the entry `what` of `records/c22/deposit.json`, the head of `audit/c22_deposit.py` and the README of the deposit. The document and the README now say that the 20 array files of the host check stay in the repository. The note after round 3 above is left as the auditor read it; its "141 array files" are the 132 label files and the nine prediction files that it names.
- Error 2, the script. A name may now hold only letters, digits and the underscore in each of its parts, so `..` and the backslash are refused, and `restore` also refuses a file whose place would lie outside the target folder. `pack` now takes the list of the kept copy's hashes as an argument, stops if a label or prediction file of that list is missing from the copy or is not the listed file, and writes nothing in that case. From the smaller points: `restore` checks the archive and every file before it writes one; `check` compares the size of each deposited file that the folder holds with the record, and names the missing files that are not deposited apart from the deposited ones; its description says that it does not read the archive.
- Error 3, the heads of two scripts. `audit/c22_keep.py` and `audit/c22_recompute.py` now say that the repository holds the kept copy without its label and prediction files, and the second says which steps stop without them. No line of code of the two scripts is changed.
- Error 4. The heading of the README's table is now "Status on 17 November 2026".
- The ignore rule. `records/c22/.gitignore` leaves the restored files out of a commit.
- The DOI. The owner reserved `10.5281/zenodo.24320576` on 17 November 2026 at about 17:14 GMT (the owner's message to the author), while round 4 ran and before the final state of the commit was made. It stands in the four places of the commit that the report lists and in the message of the commit, in place of the placeholder. The file of the deposit named `deposit.json` is the committed file.
- Still to be written: the paragraph on the audit in the document, the header of this file and the README's list of the auditor's scripts, now 23, are written. The README names the eight scripts that need the kept copy whole, and the document the four steps of the recomputation.
- "Four smaller points" of round 3: now "five".
- The outward texts. The description of the deposit and the message of the commit now say what the condensed reading is. The README of the deposit and its description name the tree of the commit beside the branch, because the commit's own name is not known before the owner makes it.
- The four scripts of round 4 are filed as delivered.
- The auditor did not see the state after these changes. They touch the document, the README, this file, `audit/c22_deposit.py`, the heads of `audit/c22_keep.py` and `audit/c22_recompute.py` and `records/c22/deposit.json`; `records/c22/.gitignore` and the four scripts of round 4 are added. On that state the author ran the auditor's scripts again:
  - `c1_round4_step.py`, against the state of the 430 paths: the 141 listed files are gone and no other; seven paths are new (the author's script, the record, the ignore file and the four scripts of round 4); five text files differ; the 120 files left in `records/c22/return/` are unchanged.
  - `c2_round4_deposit.py`: the record, with the real DOI, agrees with the files, with both lists and with the archive, which is unchanged (the same size and SHA-256).
  - `c3_round4_restore_tests.py`, its 38 cases against the corrected script: the two names that round 4 found admitted, `..` as a run's folder and backslashes, are refused; where a wrong file follows right ones, nothing is written; no case writes outside the target. One case of `check` now ends with status 0 where it ended with 1: a folder that holds the label files and not the nine others, which the corrected `check` reports as missing deposited files and not as an error. A record whose sizes or whose entry `archive` are wrong still passes `check` on a folder without the deposited files, as its description now says; `restore` tests both.
  - `c4_round4_archive_strings.py`: the same output as in round 4, none of the five strings in the archive.
  - `b3_round3_strings.py` on the 296 paths: none of the five strings and no part of one. `b4_round3_lists.py`, on an export with the files restored: the three lists right. `a11_commit_checks.py`: no carriage return, no dash, and no absolute path of a machine apart from the library's build path in six logs; it also reports a made-up path in a test case of `c3_round4_restore_tests.py`.
- The author's own tests of the corrected `pack`: on the folder as the repository holds it, and on a whole copy with one changed label file, it stops and writes nothing; a further file with a fitting name that the list does not name is not packed. In a checkout with the files restored, nothing is left to commit.
