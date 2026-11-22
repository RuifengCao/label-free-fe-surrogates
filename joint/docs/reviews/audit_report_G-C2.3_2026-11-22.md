# Independent audit of the G-C2.3 verdict: reports as delivered

Reports of the independent auditor (a separate agent that wrote none of the code, the records or the draft) to the author, all on 22 November 2026: round 1 at about 01:45 GMT, round 2 at about 02:10 GMT and round 3 at about 02:40 GMT. Round 1 audited the return package as received and the proposed commit as it then stood: the kept records, the verdict document with its tables, the author's audit scripts and probes, and the README. Rounds 2 and 3 each audited the commit as corrected after the round before.

Notes of the author for this folder:
- The proposed commit that round 1 audited is the author's local state with the tree `9917f09c465e4c4cecb58f8a5bf09d0afb8450e6` (parent `d603fd8`). Round 2 audited the state with the tree `8fbcf808bf874eeb50168c0ed2b654deca15612e`, and round 3 the state with the tree `7ea167474b3c5963328b27ff71aed5e86413c4ae` (2,019 files, 432 changed paths against the stamp).
- **What was changed after round 3, and not seen by the auditor.** In this file: the report of round 3, the author's notes on it and this header. In `joint/audit/independent/G-C2.3/`: the auditor's script `check_nearest_label.py`, filed as delivered. In `joint/README.md`, the line on `independent/G-C2.3/`: what `check_recomputation.py` needs, the new script, and whose files the one list of `make_defect_units.py` on G-C2.1 needs. In `joint/docs/G-C2.3_verdict.md`: one sentence under "What it is", and the sentences on the third round in the paragraph "Independent audit". In `joint/probes/c23_reference_state/README.md`: the two points under the table of `nearest_label.py`. Each of these is a correction that round 3 proposed, in its words or close to them. Nothing else was changed.
- `scratch/` is the auditor's working folder on the development machine and is not kept. The names of sections and the wordings quoted in the reports are those of the audited states.
- The auditor returned each report as a message; the text of each is given here without a change.
- What the author did about each point follows each report under "What was done" and is marked as the author's.

---

**Round 1, as delivered**

# Independent audit of the verdict of gate G-C2.3

Report of the independent auditor to the author, 22 November 2026. Audited: the proposed commit (parent `d603fd8`, tag `prereg-c23`; 417 changed paths), which has not been pushed, and the return package `c23_return.tar.gz` as received. I wrote none of the audited code, records or documents. I changed none of them, pushed nothing and sent nothing. My scripts are listed at the end; their outputs are in my folder `scratch/`.

**Conclusion.** The verdict holds. From the returned per-pair rows my own code gives identity OK, self-check PASS (S1, S2 and S3 hold), ranking HOLDS and "label-free closer", identical to `verdict.json` in all 8,399 values that I compared, and the 137 errors that I recomputed with exact solves from a zero element state (stamped library, my own driver) agree with the returned ones within 2.7e-13. The defect of the measuring code is real and is as the document describes it, the verdict of part 1 stands, and the run kept to the pre-specification in everything that decides the verdict. The numbers of the documents are right (3,176 table cells derived again, none differing), but six statements should be corrected before the push (Errors 1 to 6) and several things that a reader needs are left out; none of them touches a judged number.

## Verified

**1. The verdict from the returned files** (`verdict_from_rows.py`: own quantile, own ranking probability by counting, own rule of the wording)

- **Rows.** 11,088 rows in the two rows files; 3 have an infinite error, all with the note "RuntimeError: bubble condensation did not converge"; no field failed its evaluation; no member is without metrics.
- **Part 1** (label-free arm, condensed reading, third sample, 448 pairs):
  - 121 pairs flagged (27.0%); no pair that is not flagged above 10% in any run; 8 of 981 readings of the pairs that are not flagged above 5% (0.815%). S1, S2, S3 hold: PASS.
  - R: 0.9091, 0.9123, 0.9492, HOLDS.
  - Pairs above 5%: 25, 26, 26, of which flagged 22, 23, 24. Pairs above 10%: 8, 8, 7, all flagged; they are 10 pairs. Largest error not flagged: 5.61%, 6.10%, 6.01%.
- **Part 2** (third sample):
  - Label-free arm, condensed: medians 0.7944%, 0.8439%, 0.7774%; 90th percentiles 3.7471%, 3.7154%, 3.8097%; over the seeds 0.7944% and 3.7471%.
  - Supervised arm, condensed: 69.52%, 66.93%, 58.75% and 113.60%, 111.92%, 110.43%; over the seeds 66.93% and 111.92%.
  - Supervised arm, raw: 1.7071%, 1.6331%, 1.7324% and 6.7902%, 6.6129%, 5.3010%; over the seeds 1.7071% and 6.6129%.
  - Ratios: 84.25497316902958 and 29.86937438984068, "label-free closer"; supervised raw over label-free condensed 2.1487860799914285 and 1.7648109467915576, the same wording; both raw 1.2570 and 0.6863, "comparable".
- **Identity.** The six medians and six 90th percentiles of the label-free runs on the fresh members of G-C2.2 equal the pinned values; largest difference 0.0. The pinned values are those of G-C2.2's returned `verdict.json`, in both readings.
- **Against the verdict files.** 8,399 values of `verdict.json` and `verdict_part1.json` compared (every statistic of both arms, both readings and three sets; the median by level; every count, criterion, spread and flag of the twelve blocks of part 1; the ratios and wordings; the identity; the hashes of the rows files): none differs.
- **The kept part 1.** `verdict_part1.json` holds the part 1 of the final verdict (identity, self-check with every spread and flag, inputs, the hash of the label-free rows file). It shows the comparison as INCOMPLETE, the supervised arm as not evaluated and 0 training members labelled.
- **The stamped verdict function.** Run by my own driver on folders rebuilt from the package as received, `c23.evaluate.verdict` writes a `verdict.json` with SHA-256 `ae394314f233a663eb9812eb41aeac73fc84fbba7da5d26cf861cb7b444019ff`: the bytes of the kept copy.

**2. The error of single pairs, recomputed** (`make_units.py`, `solve_pairs.py`: stamped `ExportedProblem.solve_at_e`, my own driver and my own formula; the host's numpy 2.4.6 and its sparse solver, one thread a process)

- **Rule of the sample**, fixed before the solves. Every pair is solved on a new problem object, so from a zero element state.
  - B1: every pair of the label-free arm, condensed, whose returned error exceeds 10% in some run, in all three runs (10 pairs, 30 readings).
  - B2: every such pair that is not flagged and exceeds 5% in some run, in all three runs (3 pairs, 9 readings).
  - B3: for each arm, seed and reading on the third sample (12 blocks), the four pairs at ranks 224, 225, 403 and 404, which the median and the 90th percentile interpolate (48 readings).
  - B4, drawn with numpy's `default_rng(20261122)`: 12 of the 128 judged pairs at 0.5 mm in seeds 6 and 7; 8 pairs of the supervised arm condensed and 8 raw; 8 of the label-free arm raw; on the fresh members of G-C2.2, 6 label-free condensed and 4 supervised raw; on the tested members, 2 and 2.
- **Result.** All 137 pairs converge from zero. The largest difference of the signed error from the returned row is 2.7e-13 in absolute terms (`third_0001`, seed 7, 8 mm) and 3.0e-12 in relative terms. By stratum: B1, 30 readings, of which 23 are above 10%, 2.7e-13; B2, 9 readings, of which 8 are above 5%, 3.0e-14; B3, 48 readings, 1.6e-14; B4, 50 readings, 1.4e-14. The largest judged error of the gate, 103.06% (`third_0011`, seed 6, 8 mm), comes out as 1.0305620032839546 against the returned 1.030562003283979.
- **What this adds to the author's recomputation.** The author's two orders both start a pair from the state that another pair left. These solves start from zero, on another operating system than the host's, and still give the returned errors. That includes the 12 pairs of B4 at 0.5 mm, which on the host followed a solve at 8 mm: largest difference 4.4e-16.

**3. The defect of the measuring code** (`solve_pairs.py` with the units of the defect; I did not use the author's probes)

- **The state and the order, by reading the stamped code.**
  - Each element set keeps its bubble parameters (`bub`) and starts every evaluation from them. Only `warm()` and `commit()` write them, and the solver calls `warm()` after its first evaluation and after every accepted step (`joint/fejoint/nlhex.py`, `joint/fejoint/nlsolve.py`).
  - `ExportedProblem.evaluate` does not call `warm()`: evaluating a label or a predicted field leaves the state as it was. Measured: the state was unchanged after each of 7 label evaluations and 42 evaluations of predicted fields.
  - The two problems of a member share their element sets (`joint/c2/instance.py`). `joint/c23/evaluate.py` builds one object for a member and visits, for each seed, the condensed reading and then the raw one, each over the seven levels. So a solve starts from the state that the solve of the pair before it left, and the first pair of a member starts from zero. The document's description is right.
  - I found no other state that passes from pair to pair (inferred, from reading the four files): the plastic history (`ep`, `a`) is not read in the deformation theory mode, `_trial` is overwritten by each evaluation, the active set starts empty in every solve, the warm start is the label nearest in end displacement, and each member gets a new object in whichever worker process takes it.
- **A whole member in the gate's order.** `third_0034`, label-free arm, one object, 42 pairs: 41 errors equal the returned ones within 3.3e-15, and the 22nd pair (seed 6, raw, 0.5 mm) fails with the returned note. The visiting order is the one described.
- **The three infinite rows.**
  - `third_0034`, seed 6, raw, 0.5 mm, after "seed 6, condensed, 8 mm": the first evaluation of the solve needs 15 and 62 element iterations in the two sets, against a cap of 60, and the solve fails. The state stays as it was, and the next pair (1 mm) converges from it to the returned value. From zero: 3 and 2 iterations, error -0.2728% (document: -0.27%).
  - `eval_0063`, supervised seed 6, condensed, after "seed 5, raw, 8 mm": 61 and 14 iterations at 0.5 mm, fails; the same at 1 mm, fails; 16 and 13 at 2 mm, +64.0432%, the returned value bit for bit. From zero: +102.0936% and +105.3777% (document: +102.1%, +105.4%).
- **The failure of the author's first recomputation.** `third_0034`, seed 7, condensed, 0.5 mm:
  - after "seed 6, raw, 8 mm" (the gate's order): 14 and 19 iterations, +0.372769%, the returned value bit for bit;
  - after "seed 6, condensed, 8 mm" (the other order): 15 and 62 iterations, fails;
  - from zero: +0.372769%.
  - Its spread is 0.000143 and it is not flagged. With that error infinite my code gives 1 pair not flagged above 10%, 9 of 981 readings (0.917%), S1 fails, S2 and S3 hold, R 0.9091, 0.9123, 0.9153: as the document says.
- **A converged solve does not depend on the state**, to the accuracy tested: see section 2 (zero state against the host's chained state) and the 41 pairs above.
- **The same energy.** At the failing first evaluation of `third_0034`, with the cap raised, the two sets reach from the kept state the energies 172.2623055275566 and 125.87613177510924, and from zero 172.26230552755663 and 125.87613177510926: relative differences 1.6e-16 and 1.1e-16.
- **G-C2.1.** `eval_0046`, supervised seed 1, 0.5 mm, with that gate's instance (its SHA-256 is the manifest's), label and predictions:
  - after "seed 0, 8 mm" (my error for that pair equals the returned one within 1.3e-13) the first evaluation needs 16 and 89 iterations and the solve fails with the returned note;
  - from zero, and on a new object, -0.449161% with 4 and 3 iterations. The document's -0.45% is right.
  - Of that gate's rows only this one carries the note. Its 47 other infinite rows are those of label-free seed 0, with the note of a reference force that is not positive.
- **The erratum of G-C2.1, figure by figure**, from that gate's `verdict.json` with my own code and the value -0.449161%:
  - 128 to 127 pairs above 10%; 1 to 0 infinite; 90th percentile 20.608% to 20.466%; median 5.982% to 5.970% (6.0% as printed);
  - at 0.5 mm: median 10.791% to 10.624%, 90th percentile 28.685% to 27.751%, 34 to 33 pairs above 10%;
  - in the tail: 18 to 19 pairs at 6 and 8 mm, 23 to 22 at 0.5 and 1 mm; 45 pairs in the tail and 22 in members below 300 MPa unchanged; the two signed medians unchanged.
  - Every figure of the erratum is right. I found no other printed figure of that document that contains the pair, apart from the count of infinite distances at 0.5 mm in its table by level, which "no infinite distance" covers.
- **The four files** `fejoint/nlhex.py`, `fejoint/nlsolve.py`, `c2/evaluate.py` and `c2/instance.py` have the same SHA-256 in the hash lists of G-C2.1 and G-C2.3. G-C2.2's 5,544 returned rows carry no note and none is infinite.
- **How the failure arises, measured** (probes without a solve of the pair: the number of element iterations of the first evaluation at 0.5 mm from a given state).
  - After a solve at 8 mm, from zero (9 states of three members: condensed and raw pairs of seeds 5 and 6): the first evaluation at 0.5 mm needs 18 to 24 iterations in its slower set, and in every one of the 9 states the same numbers for all six pairs that could follow. The number is set by the state left, not by the pair that follows.
  - From the state of a member's own label at 8 mm, which is the state of an exact solution close to those that its pairs leave (68 members: 44 of the third sample, 22 fresh members of G-C2.2, 2 tested): 9 to 49 iterations in the slower set, median 17, 90th percentile 22; none above the cap. The two members with a failed row need 20 (`third_0034`) and 21 (`eval_0063`) from that state, against 62 and 61 from the states that their own pairs left. `third_0014` needs 49 from it, against 22 from the state of its pair "seed 5, condensed, 8 mm". So the number changes several-fold between neighbouring states of one member: nothing about a member tells in advance which state fails, and the cap of 60 is not far above the largest ordinary values.
- **My judgement of the author's conclusions.**
  - The verdict of part 1 stands. The stamped code fixes the order, the order gives finite errors for all 1,344 judged readings, and those errors are the right ones whatever the starting state.
  - "One direction" is warranted for a single error and for S1, S2 and S3: a failed solve can only add an infinite error. It needs a clause for R and for part 2 (Smaller points).
  - The counts 128 and 1,320 are right. The count "1 of 128" is not a further observation (Error 1).
  - The statement that the gate as a procedure is weakened is fair and is not overstated.

**4. The run against the pre-specification and the runbook** (`check_records.py`)

- **Configuration.** The returned `c23_config.json` has the canonical SHA-256 `3b41c266...5f9e` of the pre-specification and equals, as an object, the configuration that the stamped `c23/config.py` builds. Its file has the SHA-256 of the operator's record (`6ee7ed75...`).
- **Code.** The 41 lines of `joint/docs/G-C2.3_code.sha256` match the stamped files. The 35 hash lines that the configuration command printed on the host equal that list, followed by 6 lines "repository ... checked".
- **Samples.** The parameters of all 644 members of the manifest are the configured draws (512 with seed 20261106, 64 with 20261118, 64 with 20261113, 4 fixed), and no two members share their parameters. The 644 instance files that the author regenerated have the manifest's SHA-256. I exported five members again (`third_0034`, `third_0001`, `eval_0063`, `train_0076`, `tested_BJ_T1_preloaded`): all 33 arrays of each equal the file's.
- **When the third sample was drawn.** The generation job started at 20:45:19 GMT on 18 November, eight hours after the tag (12:44:17 by the operator's record). In the package the seed 20261118 occurs in the configuration only; no record made before the stamp names it.
- **Ledger.**
  - 644 entries, one a member; 5,020 levels (4,096 of training members at eight levels, 924 at seven).
  - Every level converged, with at most 26 iterations against 80; worst residuals 2.3e-11, 6.1e-11 and 3.9e-10 against limits of 1e-8, 1e-6 and 1e-6; the two force readings differ by at most 9.4e-13.
  - The 132 label files of the package have the ledger's SHA-256, and the ledger's instances are the manifest's.
  - The entries of the held-out and tested members are dated 20:48:20 to 21:04:46 on 18 November, those of the training members 00:06:20 to 01:10:13 on 19 November.
- **The supervised arm.**
  - Three runs, seeds 5, 6, 7, each `finished` with 102,400 steps in 200 epochs, losses finite, no resume.
  - The settings that a history records (betas, the cap's three numbers, total steps, precision, library version, device) equal those of G-C2.2's label-free histories.
  - The returned configuration differs from G-C2.2's returned one only in the gate's name, the base, the arms, the samples and label levels, the evaluated sets, the self-check, the comparison, the criteria and the list of training seeds seen. Its blocks for the training, the model, the map, the family and the repository code are equal.
  - Each history carries `f9e6eaca263f...`, which is the SHA-256 that I compute from the ledger's 512 training entries.
  - Each log has 200 epoch lines whose losses, seconds and counts are the history's. Hours 4.846, 4.956, 4.857; cap events 9,648, 9,846, 10,352.
- **The label-free arm.** Each run's history names the pinned state file by its SHA-256, epoch 200, step 102,400, and G-C2.2's configuration.
- **Order of events.** The verdict of part 1 was written by job 93 at 00:05:16 on 19 November; the label job of the training members started at 00:05:17 and its first ledger entry is dated 00:06:20. No training job is given a rows file or a verdict, and the stamped training modules do not name them.
- **The queue.**
  - 40 jobs: 6 before the stamp, 34 of the gate (19 commands, 15 guards). All ended with code 0, none was killed, no name occurs twice.
  - The 19 commands are the 19 command lines of the runbook, word for word and in its order. Each guard reads the job before it.
  - Every job started in the second in which the one before it ended, except the generation, 420 s after the guard of the configuration command.
- **Inputs of the verdict.** The 12 prediction files that the evaluation reads, the manifest and the hash of the ledger entries of the 132 evaluated members are those that `verdict.json` records. All 18 prediction files hold 132 members with the expected shapes, finite.
- **The section "Run record"** agrees with the records in every time, duration and count that I compared: host, preconditions, generation, labels, predictions, both evaluations, both verdicts, the table of the three runs, the queue.
- **Departures found.** The four of the section "Deviations" are described rightly: the warning stands in the logs of the three predictions and the three training runs (and of the host check); the evaluations took 9,471 s and 10,689 s; the suite ran on another machine with numpy 2.5.3 and another sparse solver. One more of the kind of deviation 1 is under Missing.

**5. The verdict document against the records** (`check_document.py`, `check_recomputation.py`)

- **The generated tables.** 3,080 cells of the 21 tables and four lines of numbers that rest on the returned files, derived again from the rows files, the manifest, the configuration, the amplitude records, the histories of both gates and the ledger: 2,306 numbers and counts, 774 words and names. None differs. The two tables of the author's recomputation, 96 cells, derived again from `host_order.json` and `curves.json` against the returned rows: none differs.
- **The numbers of the text** that I compared with my own values, all right: every figure of the section "Verdict"; the amplitudes at the lower limit (378, 344, 298 of 448: 84%, 77%, 67%); the factors "about 40" and "about 17" (39.2 and 16.9); the three missed pairs with their errors and spreads; the flags by level; the raw block of part 1 (212 flagged; 4 pairs; 31 of 708; 0.849 to 0.859); the levels of the supervised arm read raw; the cap's actions; the times; the hashes of `verdict.json` as received and as kept and of `verdict_part1.json`; 5,418 and 5,670 pairs; and the section on the expectation.
- **What the three infinite rows would change**, with my values from a zero state: median over the seeds 1.3536% in place of 1.3580%; 45 pairs in place of 46; ratio 1.2611 in place of 1.2570, still "comparable"; 3 pairs and 30 readings in place of 4 and 31; 120.10% in place of 120.46%. The five figures of the document are right. The list is not complete (Error 2).
- **The wording against "Interpretation, fixed in advance".** The section "Verdict" has everything that the pre-specification asks of a wording of part 1 and of part 2. The statement that the ratios 84 and 30 are an artefact of the reading is supported by the records: the amplitude is at its lower limit in 67% to 84% of the pairs, the end displacement is 47% to 49% too small in the median, and the same fields read raw are within 1.7% in the median.

**6. The author's recomputation** (the author's scripts run by me on copies in `scratch/`; `check_recomputation.py`; `check_condensed.py`)

- **`c23_recompute.py --aggregate`** on `joint/records/c23/return/` and a copy of `joint/records/c23/audit/` writes `aggregate.json` again byte for byte except the SHA-256 of the two rows files, as the document says. It also writes `curves.json` and `host_order.json` again unchanged.
- **`c23_recompute.py --records`** on the package as I unpacked it writes `records.json` again with the stored content; only the environment differs (numpy 2.4.6 here, 2.5.3 in the stored record).
- **`c23_write_verdict.py`** on the kept records writes the part "Numbers" of the document exactly (46,700 characters).
- **Environments.** The stored records name numpy 2.5.3 for the records, the instances and the pairs in another order, and numpy 2.4.6 for the fields, both runs in the gate's order, both re-solves and the last step; zlib 1.3 for the instances. That is what the document says.
- **The stored solves against the returned rows, with my code.**
  - Gate's order: 5,418 pairs, largest difference of the error 6.01e-13, of the other metrics 1.95e-14, 3 rows infinite as returned and as recomputed, 36.68 processor hours.
  - Other order: 1,371 pairs, 4.02e-13, one row infinite that the host returned finite, 4.62 processor hours.
  - Where both orders are finite they differ by at most 4.0e-13.
- **Mutation test of the aggregate step.** I changed one value at a time in a copy of the records and ran the step: a judged row, the returned wording, the kept part 1, a force of a reported row, a recomputed error in each order, a recomputed energy gap. Each change shows in the output. A change of the returned configuration file does not show there, because the step takes the configuration from the stamped code; `--records` compares that file.
- **The condensed fields.** With numpy alone, in float32, keep(z_0 + a (z - z_0)) equals the returned condensed field bit for bit in all 792 arrays.
- **The re-solved members.** The four training members are the draw of `default_rng(20261120)` (I drew them again: `train_0076`, `train_0236`, `train_0375`, `train_0379`), and their four label files have the ledger's SHA-256. The stored differences are at most 8.2e-15 and 3.9e-15 of the largest unknown, with the ledger's iterations.
- **The labels shared with G-C2.2.** The 68 label files of G-C2.2's fresh members and of the tested members have the SHA-256 that G-C2.2's deposit record gives.

**7. The kept copy, the deposit and what the commit would publish** (`check_kept.py`, `check_public.py`; the author's `c23_keep.py` run by me)

- **The archive.** 211,205,734 bytes, SHA-256 `68f00849...2618`, equal to the file that came with it. It holds 400 files, and `return_files.sha256` gives the hash of each as I unpacked it. `return_listing.txt` equals the listing that I made with numeric owners (429 lines).
- **The kept files.** Of the 245 files in `joint/records/c23/return/`, 115 are byte for byte as received, 118 differ by line ends alone, and 12 by line ends and one replacement of the working folder's path each. That is 130 files with converted line ends and 12 with the path replaced, as declared. Nothing else differs.
- **Left out.** Five files, the model states of the host check; `keep_report.json` lists them with the hashes that I find.
- **`c23_keep.py`**, run on my unpacked package, writes `keep_report.json`, `return_files.sha256`, `return_kept.sha256` and `return_listing.txt` byte for byte as the commit holds them, and a kept copy that differs from `joint/records/c23/return/` only by the 150 label and prediction files.
- **The deposit.** `c23_arrays.tar`: 206,366,720 bytes, SHA-256 `b4c697d9...fa52`; 150 members, 206,242,833 bytes; each member has the size and the SHA-256 of `deposit.json` and the bytes of the package; owner and group 0, mode 0644, one time. The 150 are the 132 label files and the three prediction files of each of the six runs, exactly the files of the kept list that the tree does not hold. The author's `c23_deposit.py check`, run by me on the tree, reports 245 of the 395 kept files, none wrong, none that the list does not name, and the 150 missing ones as those of the deposit.
- **Strings.** In the 417 changed paths (23,261,253 bytes), and in the 862 members of the 56 array archives among them, none of the five strings occurs: in plain text without regard to case, with doubled backslashes or forward slashes, reversed, in ROT13, in hexadecimal, percent-encoded, in base64 at its three alignments, in UTF-16, or as JSON escapes. The same holds for the account name that the received logs show in their paths, which my script takes from the package itself.
- **Paths, addresses, names.** No path of a home or temporary folder, no e-mail address and no name of an assistant. I searched for names of assistants and of tool vendors with a list that I do not file, because a name of such a list may be one of the five strings; `check_public.py` takes the list as an optional file. Two names of services occur: the hosting service of the repository, once, in the operator's record of the push check (`joint/records/c23/return/preconditions.log`); and a compute provider, three times, in the text of G-C2.1's two verdict files that this commit does not change.

**8. The commit as a whole** (`check_public.py`)

- No carriage return in any of the 417 paths.
- No path that a `.gitignore` of the tree would drop. The 245 kept files in the tree are the 395 of the kept list less the 150 deposited ones, and the 56 array files of the host check are there, as the README says.
- No em or en dash in a changed text file. In the Markdown files no American spelling from my list, apart from the proper name of the code's licence in the README.

## Errors

**1. The failure of the first recomputation is counted as a further observation; it is the host's own bad state, met a second time.** Small in its effect, but it is the document's evidence for "partly chance".
- **Where.** `joint/docs/G-C2.3_verdict.md`, "What stands, and what does not", fourth point: "Solves in that position failed in 2 chains among 1,320 on the host and in 1 of 128 in the author's first recomputation."
- **What the records say.**
  - The state that made the recomputation fail is the one that made the host's row of `third_0034` fail: the state left by "seed 6, condensed, 8 mm". From that one state the host's next pair (seed 6, raw, 0.5 mm) and the recomputation's next pair (seed 7, condensed, 0.5 mm) both need 62 element iterations. I reach the state a third way, from zero, and it fails in the same way.
  - Whether the first evaluation at 0.5 mm ends within the cap is set by the state left, not by the run whose pair follows: in each of the 9 states that I probed, the six possible next pairs need the same numbers of iterations.
  - The 128 states that precede a judged pair in the other order (seeds 5 and 6, condensed, 8 mm) all occurred on the host too, where a reported pair followed them. So the other order tested no state that the host had not tested, and its one failure could be read from the returned rows.
- **Suggested correction.** "On the host 2 of the 1,320 states left by a pair at 8 mm made the next solve fail. The failure of the first recomputation is the first of them again (`third_0034` after seed 6, condensed, 8 mm), met there by a judged pair and on the host by a reported one. In the gate's order the 128 judged pairs at 0.5 mm follow the raw pairs at 8 mm of seeds 5 and 6, and none of these left such a state." If a rate is wanted: at 2 in 1,320, and with the 124 judged pairs at 0.5 mm in seeds 6 and 7 that are not flagged, there was about one chance in six that part 1 would have read FAIL in the gate's own order without any error of the surrogate (inferred).
- **Number of the verdict touched:** none.

**2. The list of reported figures that contain the three infinite rows is incomplete.**
- **Where.** The same document, "Where it acted in the gate's run", the point that begins "The three rows enter reported numbers, and no judged one."
- **What the records say.** With the three values from a zero state, 18 printed cells of the part "Numbers" change (`check_document.py` with its last argument). The text names the changes behind 8 of them. Not named:
  - the 90th percentile of label-free seed 6 read raw on the third sample: 10.191% printed, 10.012% with the value;
  - the ranking probability of seed 6 in the raw block of part 1: 0.859 printed, 0.868;
  - the ratio of the 90th percentiles on the fresh members of G-C2.2, both condensed: 32.876 printed, 32.780;
  - three cells of label-free seed 6 read raw at 0.5 mm in the tables by level: median 0.95% (0.91%), 90th percentile 3.70% (3.06%), median signed +0.06% (+0.03%);
  - four cells that follow from the rows themselves: the counts "Infinite" of two tables, and the count and the table of the infinite rows.
  - `joint/probes/c23_reference_state/effect_on_reported_numbers.txt` has the first and the third of these and the median and the 90th percentile at 0.5 mm. It has neither the ranking probability with the value nor the signed median at 0.5 mm.
- **Suggested correction.** Name the six figures, or say that the list gives the larger changes and point to a table that holds them all; extend the probe's script by the ranking probability and the signed median at 0.5 mm.
- **Number of the verdict touched:** none; all are reported numbers.

**3. The status row of the README, and what the section "Consequences" fixes for statements outside the repository, leave out what the pre-specification asks of any wording.**
- **Where.** `joint/README.md`, the row G-C2.3 of the status table; `joint/docs/G-C2.3_verdict.md`, "Consequences", second point.
- **What the pre-specification says** ("Interpretation, fixed in advance").
  - Any wording of a PASS of part 1 says that the check needs three training runs and that the threshold was set on T-stubs of this family, and gives the share of pairs flagged and, for each run, the pairs above 5% and above 10% and how many of them were flagged.
  - For part 2 the two ratios of the supervised arm read raw over the label-free arm read condensed are stated with the wording in every case, with the medians at each level and what each arm needed. Any wording says that the supervised arm was trained with the label-free arm's settings and was not tuned, and that the wording does not carry to another family, mesh or budget, or to a supervised arm with settings of its own.
- **What the row has.** The share flagged, the 8 of 981 readings, "at equal budget and without tuning", and the four statistics.
- **What it does not have.** That the threshold was set on this family; the counts for each run (25, 26, 26 above 5%, of which 22, 23, 24 flagged; 8, 8, 7 above 10%, all flagged); the two ratios 2.15 and 1.76 as ratios; what each arm needed; where the wording does not carry. "Consequences" asks of outside statements only "its reading and its margins".
- **Suggested correction.** Add to the row one sentence with the counts for each run and the origin of the threshold, the two ratios, and a clause that the wording holds for this family, mesh and budget and for a supervised arm that was not tuned; or point to the section "Verdict" for them. In "Consequences", say that an outside statement carries the elements that the pre-specification lists.
- **Number of the verdict touched:** none.

**4. The size "about two" that is to be quoted outside the repository is the mixed reading. The like-for-like reading is left out of that rule, and where it is given, its closeness to the band's end is not.**
- **Where.** `joint/docs/G-C2.3_verdict.md`, "Consequences", second point, and "What this means", the point "Read alike, both raw"; the README row has the like-for-like reading without its ratios.
- **What the records say.**
  - 2.15 and 1.76 compare the label-free arm after the condensation with the supervised arm without it.
  - With both arms read raw the rule gives "comparable" on the third sample, with ratios 1.257 and 0.686. The second is 0.02 above the band's end of 0.667.
  - On the fresh members of G-C2.2 the same reading gives 1.322 and 0.589, "mixed" (the document's own table).
  - In both samples the supervised arm is the closer one at the 90th percentile when both are read raw.
- **Why it matters.** A reader of "label-free closer, by about two" outside the repository takes it as a statement about the two ways of training. The records support it only for the pair of readings "as each arm was built".
- **Suggested correction.** In "Consequences": "... with the size that the raw reading of the supervised arm gives, about two, and with the statement that with both arms read raw the two are comparable and the supervised arm has the smaller 90th percentile; ...". In "What this means", add the ratio 0.69 against the band's end 0.667, and that the same reading is "mixed" on the fresh members of G-C2.2.
- **Number of the verdict touched:** none; the wording by the rule stays "label-free closer".

**5. "Every prediction file ... has the SHA-256 that the verdict records" holds for 12 of the 18 files.** Small.
- **Where.** `joint/docs/G-C2.3_verdict.md`, "The recomputation", the point "The records".
- **What the records say.** `verdict.json` and the rows files record a hash for `preds.npz` and `preds_condensed.npz` of each run. They record none for the six `preds_base.npz`, and the author's step compares only the two (`FILES` in `joint/audit/c23_recompute.py`). The base files are covered by `return_files.sha256` and by the condensed fields, which are reproduced from them bit for bit.
- **Suggested correction.** "The twelve prediction files that the evaluation reads have the SHA-256 that the verdict records; the six files of base fields are not among the verdict's inputs."
- **Number of the verdict touched:** none.

**6. "Its files are in the return package" is said of the queue; the queue's runner is not in the package.** Small.
- **Where.** `joint/docs/G-C2.3_verdict.md`, "What was pre-specified", third point.
- **What the records say.** The package holds the job files, the done files, the logs, the guard, the waiting job and the generator of the jobs. The runbook's section 9 says that the runner and the scripts of pausing are not in it, and they are not. The three scripts in the package have the SHA-256 that the operator recorded at 12:54 on 18 November, before the gate's jobs were written.
- **Suggested correction.** "... its job files, logs, guard, waiting job and job generator are in the return package; the runner is not."
- **Number of the verdict touched:** none.

## Missing

- **The paragraph on this audit** in the verdict document (the mark `[[...]]`) and its mention in the README, as expected at this stage.
- **A departure of the kind of deviation 1.** Each of the four label commands ends its output with a line "labelled 64", "labelled 64", "labelled 4" or "labelled 512", which the stamped command prints and no comment of the runbook states. By the reading that makes the warning a deviation, these four lines are one too; or deviation 1 should say that it lists warnings only.
- **That the failure follows the state and not the pair** (see Error 1). With it a reader can see from the returned rows alone which other orders fail.
- **Whether the reference solutions are exposed to the defect.** They are not in the same way: a label is solved level by level in rising order, each from the level before, on an object of its own, and all 5,020 levels converged. One sentence would settle a question that the section raises.
- **The second path of the same state.** After the solve, the evaluation of the predicted field for the other metrics also starts from the kept state, under the same cap. It ended within the cap for all 11,088 fields (no `evaluate_failed`), also for the three rows whose solve failed. The document does not say that this path exists.
- **The margin of S1.** The document gives the margins of S2 and R. S1 held with a wide one, where the pre-specification had found none on the first sample: the smallest spread among the 10 pairs above 10% is 0.0334, 7.4 times the threshold, and the largest error not flagged is 6.10%.
- **Records of two statements.** The owner's decision of 20 November 2026 ("Consequences") and the operator's report of part 1 with the two hashes, which the runbook's section 5 asks for, are not among the records of the commit. The document could say where they are kept.

## Smaller points

- **"One direction".** For R an infinite error can raise the probability as well as lower it (a failed pair with a large spread counts as above 5%). In part 2 a failed solve in the label-free arm would move the ratios down, and one in the supervised arm up. Neither happened: no judged row is infinite. A clause would make the sentence exact.
- **"128 of the 1,344 judged pairs ... started from another element state".** True by the order of the script. The step `--curves` resumes a member pair by pair, and a resumed member would continue from a zero state; no record shows whether a member was resumed (inferred from the script).
- **"One reading from the limit"** (S2, in the section on the expectation): nine readings would still hold, the tenth would not. The sentence under "The margins are small" says it exactly.
- **"Which the supervised arm cannot use"** claims more than was tested; "which fails on these supervised networks" is what the records show.
- **Bounds in the text and values in the tables.** 6.1e-13, 4.1e-13, 4.5e-16, 8.3e-15 and 4.0e-15 in the text are 6.0e-13, 4.0e-13, 4.4e-16, 8.2e-15 and 3.9e-15 in the part "Numbers": the text rounds up, the tables to the nearest.
- **The citation of `records.json`** for the statement that each command started in the second in which the one before it ended: the file holds the times, not the comparison. The statement is right.
- **The commit's date** (12:43:41) is in no record that I have; the tag's time is in the operator's record.
- **`c23_recompute.py --aggregate`** takes the configuration from the stamped code and does not read the returned file; its docstring could say so.
- **The kept ledger** carries the name of the host's time zone in the language of its system, as JSON escapes, in all 644 entries. G-C2.2's kept ledger has the same.
- **Two slips of my own.**
  - My first runs imported the stamped library without switching off the writing of bytecode and left four `__pycache__` folders (19 files) in my copy of the stamped export. I removed them: the export has its 1,590 files again and its 41 pinned files match their hashes. My scripts now switch the writing off. Nothing else of the audited material was touched.
  - The first version of `check_public.py` held its list of names inside the script, and two helper files of my scratch folder held paths of my working machine. I took the list out of the script and deleted the two helpers. A search by code over my whole folder now finds the five strings only in the file of the environment that I was given and in the 12 received logs of the unpacked package.

## Not checked

- **Exact solves** beyond my sample and my units: 137 of the 11,088 errors from a zero state, one member of 42 pairs in the gate's order, and the units of the defect. I did not repeat the author's 5,418 solves in the gate's order.
- **The author's steps** `--regenerate`, `--fields`, `--host`, `--curves` and `--resolve`: not run by me. I checked their stored outputs against the returned rows and against the claims made of them, and the regenerated instance files against the manifest.
- **The author's scripts**, read in part: of `c23_recompute.py` the selection, the two solve steps, the helpers, the first half of the last step and the part of `--records` on predictions and the queue; `c23_keep.py` whole; `c23_write_verdict.py` and `c23_deposit.py` only at their heads. Of `c23_deposit.py` I ran `check` only, not `pack` and not `restore`; I compared the archive with `deposit.json` and with the package by my own code.
- **The training of the supervised arm**: not repeated. Its model states and 508 of its 512 label files are not in my materials.
- **The 69 tests** of the runbook: not run.
- **The commit and the tag** as git objects, and the commit's date: the exports hold no history.
- **The deposit's DOI** and anything on the network.
- **The statements of the operator and of the owner**: the start at 20:31, that nothing of the queue changed after 20:44:59, what was read between the two parts, the decision of 20 November.
- **Spelling**: by a list of patterns, not by reading every sentence of the 417 paths.

## Scripts

To be filed under `joint/audit/independent/G-C2.3/`. None imports a script or a probe of the author's, and none holds a path of a machine or one of the five strings. Each takes its paths as arguments and states in its header what it checks. `solve_pairs.py` and `check_records.py` import the stamped library (`c2`, `c23`, `fejoint`) and switch off the writing of bytecode.

| Script | What it checks |
|---|---|
| `verdict_from_rows.py` | the verdict, every statistic and every block of part 1 from the two rows files, against `verdict.json` and `verdict_part1.json` |
| `make_units.py` | the sample of pairs for the exact solves, by the rule of section 2 |
| `solve_pairs.py` | exact solves and probes of the element iteration on one problem object, step by step, with the element state under control |
| `check_records.py` | configuration, code hashes, samples, ledger, runs, queue, order of events, inputs and logs |
| `check_document.py` | the cells of the generated tables; with a last argument, the cells that contain chosen rows |
| `check_recomputation.py` | the stored outputs of the author's recomputation, its two tables, the environments, the four training members, the labels shared with G-C2.2 |
| `check_condensed.py` | the condensed fields from the raw fields, the base fields and the amplitudes |
| `check_kept.py` | the archive, the kept copy, the lists, the listing and the deposit |
| `summarise_solves.py` | the results of `solve_pairs.py` against the returned rows: the sample by stratum, the units of the defect, the probes |
| `check_public.py` | the five strings in plain and encoded forms, paths, addresses, names from an optional list, line ends, dashes, spelling, `.gitignore` |

---

**What was done after round 1 (the author)**

Errors
1. The count "1 of 128": corrected as proposed. The section on the defect now says, under "What it is", that whether the first evaluation of a solve ends within the cap is set by the element state left and by the level of the pair, with the audit's measurement; under "What the recomputation found", that the first recomputation met the host's bad state a second time and is no further observation; and under "What stands, and what does not", the host's 2 states in 1,320 and the estimate of about one chance in six, called rough because two events carry it. The author checked the premise in the stamped code (`c2/evaluate.py`: the exact solve of every pair starts from the label nearest in end displacement) and the estimate: 62 of the 64 pairs at 0.5 mm are not flagged, so 124 judged pairs of seeds 6 and 7 are not, and 1 - (1 - 2/1320)^124 is 0.17.
2. The list of reported figures: complete now. The document names the 18 cells, and `probes/c23_reference_state/effect_on_reported_numbers.py` was extended: it computes the block of part 1 with the three values by the stamped function, the ranking probability and the signed median at 0.5 mm, and its output ends with a list of every printed figure that contains one of the rows. The author's values are the auditor's.
3. The status row of the README and the section "Consequences": the row now has the origin of the threshold, that the check needs three training runs, the counts for each run, the two ratios of the raw reading, what each arm needed and where the wording does not carry, and it points to the document for the medians at each level. "Consequences" says that an outside statement of part 1 carries the elements that the pre-specification lists, and what a statement of part 2 carries.
4. The size "about two": "Consequences" now gives the size as each reading gives it, about two with the label-free arm read condensed and the supervised arm read raw, and comparable with both read raw, where the supervised arm has the smaller 90th percentile. "What this means" says that the first sets one arm after the condensation against the other without it, gives the ratios 1.26 and 0.69 with the band's end, and the "mixed" of G-C2.2's fresh members. The README's row has the ratios of both readings.
5. The prediction files: corrected as proposed.
6. The queue's files: corrected as proposed.

Missing
1. The paragraph "Independent audit" and the README's lines on the audit: written.
2. The lines "labelled N": deviation 1 now lists them with the warning, as output that no comment of the runbook mentions.
3. That the failure follows the state: see error 1.
4. The reference solutions: one point added under "What it is". The author checked it in `c2/data.py` (`solve_levels`).
5. The second path of the element state: one point added under "What it is". The author checked the order of the two computations in `c2/evaluate.py` (`metrics`).
6. The margin of S1: added to the point on the margins. The author's count from the returned files gives the same: 10 pairs, the smallest spread 0.0334 (`third_0003` at 6 mm), 7.4 times the threshold.
7. The two statements: the document now says that the owner's decision is a message and the operator's report of part 1 a note, that the owner keeps both, and that neither is in the repository.

Smaller points
- "One direction": the point now says what an infinite error can do to S1, S2, S3, R and the ratios of part 2, and that no judged row is infinite.
- The 128 pairs: the author compared the times of the per-pair files of the first recomputation with the seconds that each file records. In every one of the 64 members the 21 files were written one after another, each within 0.01 s of the time that the solve before it left, so no member was resumed part-way. The document says so, and that these files are not kept.
- "One reading from the limit": replaced by the counts.
- "Which the supervised arm cannot use": replaced as proposed.
- Bounds and rounded values: "The recomputation" now says that the text rounds its bounds up and the tables round to the nearest.
- The citation of `records.json`: it is now cited for the times.
- The commit's date: the document says that it is in the repository's history.
- `audit/c23_recompute.py --aggregate`: its header now says that the step takes the configuration from the stamped code.
- The name of the time zone in the kept ledger: left as it is, as in G-C2.2's kept ledger.
- The two names of services: left as they are. One is in the operator's record as received; the other is in text of G-C2.1's verdict that this commit does not change (the commit adds the erratum above it).
- The auditor's two slips: nothing for the author to do. After the audit the stamped export had its 1,590 files and no bytecode folder.

Not checked by the auditor, and done by the author
- The tests: the whole suite of the folder passed on the state that round 1 audited, 156 tests. The changes made after round 1 touch no file that a test imports or reads.

---

**Round 2, as delivered**

# Independent audit of the verdict of gate G-C2.3: round 2

Report of the independent auditor to the author, 22 November 2026, on the corrected commit (428 changed paths against the stamp, 17 of them changed since round 1). I changed nothing in the audited material, pushed nothing and sent nothing. Scripts changed or added in this round are listed at the end; their outputs are in my folder `scratch/`.

**Conclusion.** The verdict stands as in round 1, and the corrections are right and complete for errors 2 to 6, for the seven omissions and for the smaller points; the part "Numbers" is unchanged, and nothing that the commit would publish holds one of the five strings. One new statement goes beyond what was measured and is wrong for one arm: that the run and the reading of the pair that follows never decide whether a solve fails (Error 1). The paragraph on this audit was written before the audit had ended and needs its last sentences rewritten (Error 2). No number of the verdict is touched.

## Verified

**1. What was filed**

- **My report of round 1.** Lines 15 to 260 of `joint/docs/reviews/audit_report_G-C2.3_2026-11-22.md` are byte for byte the text that I delivered (41,690 bytes).
- **My scripts.** The ten files of `joint/audit/independent/G-C2.3/` are byte for byte those that I delivered.
- **The author's notes "What was done after round 1".** Each note describes what I find in the corrected commit. Two remarks: the note on error 1 gives the premise rightly ("the label nearest in end displacement"), the document does not (Error 1); and "each within 0.01 s" is 0.0104 s at most.

**2. The corrections of round 1**

- **Error 1 (the count "1 of 128").** Corrected in "What the recomputation found" and in "What stands, and what does not": the failure of the first recomputation is now called the host's bad state met a second time and no further observation. The new point under "What it is" is not right as worded (Error 1 below).
- **Error 2 (the figures that contain the three rows).** The document now names all 18 cells; I counted them against my list of round 1: 5 of the label-free arm read raw on the third sample, 1 ratio, 3 of the raw block of part 1, 3 by level, 4 of the supervised arm read condensed on the fresh members of G-C2.2 with its ratio, 2 of the infinite rows. `check_document.py` with the three values still finds 18 changed cells in the corrected document. The extended probe, run by me from the stamped library on the repository's files and on the package as received, writes its stored output byte for byte, and its values are mine (0.8592 to 0.8678; 3.70% to 3.06%; +0.06% to +0.03%; 32.876 to 32.780).
- **Error 3 (README row, "Consequences").** The row now has the three training runs, the origin of the threshold, the counts for each run, the ratios 2.15 and 1.76, what each arm needed, a pointer for the medians at each level and where the wording does not carry. Its numbers are right (12.55 to 14.08 hours; 4,096 solutions and 16.9 processor hours; 4.85 to 4.96 hours). "Consequences" lists the elements of part 1 and of part 2; one small gap is under Smaller points.
- **Error 4 (the size "about two").** Corrected in "Consequences", in "What this means" (ratios 1.26 and 0.69 with the band's end; 1.32 and 0.59, "mixed", on the fresh members of G-C2.2) and in the row.
- **Errors 5 and 6.** Corrected as proposed.
- **Missing 1 to 7.** The paragraph on the audit is written (Error 2 below). Deviation 1 lists the four lines "labelled N". The two points on the reference solutions and on the second path of the element state are right by the stamped code (`c2/data.py`, `solve_levels`; `c2/evaluate.py`, `metrics`) and by my measurements of round 1. The margin of S1 is given with my numbers (10 pairs, 0.0334, 7.4 times, 6.1%). The two statements are now said to be kept by the owner and not to be in the repository.
- **Smaller points.** Each is taken up as the notes say: the sentence on S1, S2, S3, R and the ratios; the counts in place of "one reading from the limit"; "which fails on these supervised networks"; the sentence on bounds; the citation of `records.json` for the times; the commit's date; the header of `audit/c23_recompute.py`.

**3. The new statements**

- **"About one in six".** 1 - (1 - 2/1320)^124 is 0.171, one in 5.8. The premises hold. Of the 64 pairs at 0.5 mm, 62 are not flagged, so 124 of the 128 judged pairs of seeds 6 and 7 are not. On the host 2 of 1,320 states failed, and every bad state showed: each of the 1,320 was followed by a pair at 0.5 mm, and at 0.5 mm every pair of both arms and both readings takes the same label as its start (measured in three states; inferred for the others). The wording is fair: it is called rough, with the reason. An exact 95% interval for 2 in 1,320 is 0.02% to 0.55%, which puts the chance between 2% and 49%.
- **"Each member was computed in one piece"** (`check_curve_times.py`, new). The 1,371 per-pair files of the first recomputation equal their rows in `curves.json`. In each of the 64 members the 21 files are in the order of the list, and over all 1,305 pairs of neighbouring files the time since the file before, less the file's own recorded seconds, lies between -0.003 s and +0.010 s (median 0.0003 s). A resumed member would show at least the seconds of a new problem object there. At most two members were in work at once; the solves ran from 20:07:38 to 22:44:49 GMT on 19 November, with pauses between members only. The statement is right.
- **The margin of S1 and the sentence on what an infinite error can do.** Right; one word under Smaller points.
- **The README's row against "Interpretation, fixed in advance".** It now has what the pre-specification asks of a wording of part 1 and of part 2.

**4. The part "Numbers", the author's steps, the records**

- The part "Numbers" is the one of round 1, character for character (46,700 characters), and `audit/c23_write_verdict.py` writes it exactly from the kept records.
- `audit/c23_recompute.py --aggregate` writes `aggregate.json` again byte for byte except the SHA-256 of the two rows files. Its header has the new sentence; nothing else of it changed.
- `joint/records/` is unchanged since round 1. I ran my checks of the kept copy, the deposit, the tables of the recomputation and the 3,080 cells again on the corrected commit: all as in round 1.

**5. What the corrected commit would publish** (`check_public.py`, on the 17 paths changed since round 1, 375,236 bytes, and on all 428 paths, 23,443,267 bytes)

- None of the five strings and no account name of the received paths, in any of the forms of round 1; no e-mail address; no carriage return; no em or en dash; no American spelling but the proper name of the code's licence in the README. No changed path is dropped by a `.gitignore`.
- My report as filed and the author's notes hold no name from my list and no path.
- Patterns of a home or temporary folder occur in one file only: the filed copy of my own `check_public.py`, which holds them as search patterns, with the name of an operating system in a comment. The new version holds neither (see Scripts).
- The other names from my list in the 17 paths are those of round 1's kind, in the author's documents: operating systems, solvers, the graphics processor, the tensor library, the deposit.

## Errors

**1. The new point under "What it is" says more than was measured, and its premise is not what the stamped code does.**
- **Where.** `joint/docs/G-C2.3_verdict.md`, "A defect of the measuring code", "What it is": "The exact solve of every pair starts from the same displacement field, the label nearest in end displacement. Whether its first evaluation ends within the cap is therefore set by the element state that was left and by the level of the pair, and not by the run or the reading of the pair that follows." And, in the same section, the older sentence: "A failure carries on to the next pair, because a failed solve leaves the element state as it was: hence the two rows of `eval_0063`."
- **What the stamped code does.** A solve starts from the label nearest to the predicted end displacement of its own pair, with that end displacement put in (`c2/evaluate.py`, `metrics`; `c2/instance.py`, `solve_at_e`). The start is therefore not the same field for every pair of a level. For the supervised arm read condensed, whose end displacements are about half, the nearest label is often the one a level below.
- **What I measured.** Round 1: nine states, pairs at 0.5 mm, the six pairs of the label-free arm. The document describes that measurement rightly, but the sentence before it speaks of every level, both arms and both readings. Round 2 (`make_defect_units.py`, list G; `solve_pairs.py`): after one solve at 8 mm in three members, probes of the first evaluation for all twelve pairs of both arms and both readings.
  - At 0.5 mm all twelve pairs need the same numbers of element iterations: 15 and 62 after "seed 6, condensed, 8 mm" of `third_0034`, 61 and 14 after supervised "seed 5, raw, 8 mm" of `eval_0063`, 24 and 15 after "seed 5, condensed, 8 mm" of `third_0000`. Here the sentence holds, for both arms.
  - At 1 mm the nine pairs whose nearest label is that of 1 mm need 16 and 19, 16 and 13, 22 and 14. The three pairs of the supervised arm read condensed, whose nearest label is that of 0.5 mm, need the numbers of 0.5 mm again: 15 and 62, 61 and 14, 24 and 15. In the first two states that is above the cap of 60, where the other nine are far below it.
  - At 2 mm in `eval_0063`: 13 and 13 for the nine, 16 and 13 for the three, whose nearest label is that of 1 mm.
- **What follows.** At one level the reading does decide, through the label that it makes the nearest. That, and not the kept state alone, is why the row of `eval_0063` at 1 mm failed (supervised, read condensed: its start is the label of 0.5 mm again), while in `third_0034` the pair at 1 mm converged from the same kept state (label-free: its start is the label of 1 mm).
- **Suggested correction.** "The exact solve of a pair starts from the label nearest to the pair's predicted end displacement. Whether its first evaluation ends within the cap is set by the element state that was left and by that label. At 0.5 mm every pair starts from the label of 0.5 mm, so that there the run and the reading of the pair that follows make no difference; the independent audit measured this for the six label-free pairs after each of nine solves at 8 mm, and for all twelve pairs of both arms after three. Above 0.5 mm the label is that of the pair's own level for the label-free arm and for the supervised arm read raw; for the supervised arm read condensed, whose end displacements are about half, it is often the label one level below." And: "A failure carries on to the next pair where that pair starts from the same label, because a failed solve leaves the element state as it was: hence the two rows of `eval_0063`, whose pair at 1 mm, read condensed, starts from the label of 0.5 mm again."
- **Number of the verdict touched:** none. The estimate of one in six rests on pairs at 0.5 mm and is not affected.
- **My part in it.** Round 1 said "the number is set by the state left, not by the pair that follows" of the pairs that I had probed, at 0.5 mm in the label-free arm, without naming that limit in the same sentence.

**2. The paragraph "Independent audit" gives the outcome of an audit that had not ended, and one clause says more than the audit found.** Small.
- **Where.** `joint/docs/G-C2.3_verdict.md`, "Independent audit": "in two rounds", "It found that the verdict holds and that no number of this document was wrong", "Its six errors, and its list of what was missing, ...; they were corrected before the push."
- **What the reports say.** Round 1 derived 3,176 table cells again, none differing, and found right the numbers of the text that it compared; it did not compare every number of the document (its section "Not checked"). The six errors are those of round 1. Round 2 finds two more statements to correct, one of them this paragraph.
- **Suggested correction.** "It found that the verdict holds and found no wrong number among the 3,176 table cells and the numbers of the text that it derived again. The six errors of its first round and its list of what was missing concerned statements of this document and of the README. Its second round found the corrections right but for one new statement, on what decides whether a solve fails, and for this paragraph. All were corrected before the push."
- **Number of the verdict touched:** none.

## Missing

- **The README's lines on my scripts** are right as far as they go. They do not say that `solve_pairs.py`, `check_records.py` and `check_condensed.py` also need the instance files, which the repository does not hold (`audit/c23_recompute.py --regenerate` writes them); that `check_kept.py` needs the archive of the deposit and a listing of the package, and `check_public.py` a list of the changed paths and the file of the strings; and that `check_document.py` runs on the files of the repository. The two scripts added in this round need a line: `make_defect_units.py` (the units of the defect, from the manifest) and `check_curve_times.py` (it needs the per-pair files of the first recomputation, which are not kept).
- **The evidence for "computed in one piece" is not kept.** The sentence rests on file times that no reader can see. Either keep the times as a small record beside `curves.json`, or cite this report for them.
- **The report of round 2 and the final header** of the audit report file, as the header of that file already says.

## Smaller points

- **"It would lower a ratio ... and raise it"** ("What stands, and what does not"): "could". One infinite row among 448 moves a median or a 90th percentile only if the pair's true error lay below it.
- **"The same element state is the start of a second computation."** After a converged solve the evaluation starts from the state that this solve has just left; only after a failed solve is it the state kept from the pair before. "The element state is also the start of ..." is exact.
- **"Consequences", the point on part 2.** It names what each arm needed and where the wording does not carry, but not "both statistics of both arms" and "the medians at each level", which the pre-specification names in the same sentence. The README's row has both.
- **The extended probe** prints the three counts of infinite rows ("1 -> 0", "2 -> 0", "3 -> 0") as fixed text and does not compute them. They are right.
- **"About one in six."** The range that two events allow, 2% to 49%, could stand beside "rough".
- **The operator's report "at 00:10"** is a new statement with a time; the document says that the note is not in the repository, and I have no record of it.
- **My script as filed.** Run on the files of the repository, the filed `verdict_from_rows.py` reports five differences: the SHA-256 of the two rows files (three comparisons) and of the manifest (two), which the verdict records for the host's files with CR LF line ends. `check_records.py` reported the manifest's hash as unequal on the kept copy for the same reason. Both now accept the files with either line ends and say which they found; on the repository's files and on the package as received they report no difference.

## Not checked

- **The suite.** I did not run the 156 tests of which the author's note speaks. No test of `joint/tests/` names one of the 17 paths changed since round 1.
- **The tree hash** that the header of the audit report file gives for the state of round 1, the commit's date and the tag as git objects: the exports hold no history.
- **The owner's message and the operator's note**, which the document now says the owner keeps.
- **`audit/c23_deposit.py restore`**: not run. I built the kept copy whole with `audit/c23_keep.py` instead and ran `check_records.py` and `check_condensed.py` on it.
- **The probes of round 2** cover three states of three members. I did not probe other states, and no pair above 2 mm.
- **Exact solves of round 1**: not repeated; nothing that they rest on has changed.

## Scripts changed or added in this round

To replace or join the filed copies in `joint/audit/independent/G-C2.3/`. None holds a path of a machine or one of the five strings; each has a header that says what it checks.

| Script | Change |
|---|---|
| `check_public.py` | changed, as asked for this round: the patterns of a home folder, a temporary folder and the folder of accounts are put together from parts, so that the file no longer holds the literals that it and the repository's own scans search for; the name of an operating system is gone from its header. Tested on 14 sample paths (all found) and on the tree of round 1 (same result as before). |
| `verdict_from_rows.py` | changed: a hash that the verdict records is compared with the file as it is and as it would be with the host's line ends |
| `check_records.py` | changed: the same for the manifest's hash |
| `make_defect_units.py` | new: writes the lists of units for the checks of the defect (lists A, A_chain, C, E, D, F of round 1, which I had made by hand, and list G of round 2); it reproduces the lists that I ran |
| `check_curve_times.py` | new: the file times of the per-pair files of the author's first recomputation against the seconds that each file records |

---

**What was done after round 2 (the author)**

Errors
1. What decides whether a solve fails: corrected with the wording proposed and with a count of the author's own. The author's sentence had said that every pair starts from the same displacement field; that was the author's reading of the stamped code, and it was wrong. `probes/c23_reference_state/nearest_label.py`, written after the report, reads the returned labels and predictions and counts the pairs whose nearest label is not that of their own level, 396 pairs at each level for an arm's reading: none at 0.5 mm in either arm or reading (1,584 pairs); none for the label-free arm read condensed and for the supervised arm read raw; 15 for the label-free arm read raw, at 4, 6 and 8 mm; and 395, 391 and four times 396 above 0.5 mm for the supervised arm read condensed. For `eval_0063` (supervised seed 6, condensed) the label nearest to the pair at 1 mm is that of 0.5 mm, and for `third_0034` that of 1 mm, as the report says. The point on the failure that carries on to the next pair is corrected in the same way.
2. The paragraph "Independent audit": rewritten as proposed. It names three rounds and says of the third only that it read the corrected state.

Missing
1. The README's lines on the auditor's scripts: they now say what each script needs and name the two new scripts.
2. The evidence for "computed in one piece": the document now cites the audit's second round for the times. No new record is kept.
3. The report of round 2: filed above. The header of this file is completed after the third round.

Smaller points
- "Would" and "could": corrected.
- "The element state is also the start of a second computation": corrected, with the state from which the evaluation starts after a solve that converged and after one that failed.
- "Consequences", the point on part 2: both statistics of both arms and the medians at each level are added.
- The extended probe: it now counts the infinite rows; its stored output is unchanged byte for byte.
- "About one in six": the interval is added. The author computed it again: 2.3% to 49.3%.
- The operator's report: now "at about 00:10". The time is that of the note, which is not in the repository.
- "Within 0.01 s" in the author's notes after round 1: 0.0104 s at most, as the report says. The note is left as it was written.
- The auditor's scripts: the three changed ones and the two new ones are filed as delivered, twelve files in all.

---

**Round 3, as delivered**

# Independent audit of the verdict of gate G-C2.3: round 3

Report of the independent auditor to the author, 22 November 2026, on the commit corrected after round 2: 2,019 files, 432 changed paths against the stamp (429 added, 3 modified), 12 of them changed since round 2. I changed nothing in the audited material, pushed nothing and sent nothing. One script is added in this round; the outputs are in my folder `scratch/`.

**Conclusion.** The verdict stands as in rounds 1 and 2. The two errors of round 2, its three items under Missing and its smaller points are all taken up. The corrections are right and not overstated, with one exception: a new line of the README says that `check_recomputation.py` needs the kept copy whole, and it does not (Error 1, harmless). The new counts of the nearest label are right by a count of my own, the sentence on `third_0034` at 1 mm and the interval are right, the paragraph "Independent audit" describes the audit rightly and says of this round only that it read the corrected state, the part "Numbers" is unchanged, and nothing that the commit would publish holds one of the five strings. Beyond Error 1 I find nothing to correct, only smaller points of wording, the first of them about a sentence that I proposed myself. No number of the verdict is touched. What the author still adds after this round I have not seen; it is listed in its own section below.

## Verified

**1. What was filed**

- **My reports of rounds 1 and 2.** Both stand whole in `joint/docs/reviews/audit_report_G-C2.3_2026-11-22.md`, byte for byte the texts that I delivered (41,690 and 17,396 bytes).
- **My scripts.** The twelve files of `joint/audit/independent/G-C2.3/` are byte for byte those that I delivered.
- **The header of the audit report file.** The two trees that it names are those of the states that I audited. I added every file of each export to an empty repository of my own (`git add -A -f`, all plain files, then `git write-tree`): the state of round 1 gives `9917f09c465e4c4cecb58f8a5bf09d0afb8450e6` and that of round 2 `8fbcf808bf874eeb50168c0ed2b654deca15612e`, as the header says. The state that I read in this round gives `7ea167474b3c5963328b27ff71aed5e86413c4ae`. The times "about 01:45" and "about 02:10 GMT" are those of my two deliveries.
- **The changes since round 2.** A comparison of the two exports file by file finds the 12 paths of the list and no other: 8 changed, 4 added.
- **The author's notes "What was done after round 2".** Each note describes what I find, with one exception: the README's lines are right for eleven of the twelve scripts (Error 1).

**2. The corrections of round 2**

- **Error 1 (what decides whether a solve fails).** Corrected in "What it is" with the wording that I proposed and a count of the author's own, and in "Where it acted" for the failure that carries on. Both are right by the returned records and by my probes. One remark on exactness, which concerns my own wording, is under Smaller points.
- **Error 2 (the paragraph "Independent audit").** Rewritten as proposed. It describes the audit rightly: three rounds on 22 November 2026; the work with code of my own; "no wrong number among the 3,176 table cells and the numbers of the text that it derived again" (3,080 and 96 cells, both derived again on this state, none differing); the six errors of round 1; the two findings of round 2. Of this round it says only "a third round read the corrected state". That is true, and it claims nothing of what this round found.
- **Missing 1 (the README's lines on my scripts).** Written; right but for Error 1. See 3 below.
- **Missing 2 (the evidence for "computed in one piece").** The document now says that the per-pair files are not kept and cites my second round for their times. That is one of the two ways that I named.
- **Missing 3.** The report of round 2 is filed; the header says that it is completed after this round.
- **Smaller points.** Each is taken up as the notes say.
  - "Could" stands for "would".
  - The start of the second computation is given for a solve that converged and for one that failed. It is right by my units of rounds 1 and 2: none of the 61 evaluations of a predicted field changed the element state, and after each of the 6 failed solves the state has the fingerprint that it had before.
  - "Consequences" now has both statistics of both arms and the medians at each level ("gives or points to", the reading that the README's row takes).
  - The extended probe computes its three counts of infinite rows. Run by me on the repository's files and on the package as received, it writes its stored output byte for byte.
  - The interval stands beside "rough".
  - The operator's report is now "at about 00:10" (Not checked).

**3. The new statements**

- **The counts of the nearest label** (`check_nearest_label.py`, new). My own count, from the end displacements in the two rows files and the labels' end displacements, with the prediction files as a second source (no pair gets another label from them): 132 evaluated members, 396 pairs at each level for an arm's reading.
  - At 0.5 mm, 1,584 of 1,584 pairs have the label of 0.5 mm as their nearest. "At 0.5 mm every returned pair, of both arms and both readings, starts from the label of 0.5 mm" is right.
  - Above 0.5 mm there are 2,376 pairs for an arm's reading. The label-free arm read condensed and the supervised arm read raw: 2,376 of 2,376 at their own level. The label-free arm read raw: 2,361 at their own level, the other 15 one level below (1 at 4 mm, 1 at 6 mm, 13 at 8 mm). "For all but 15 pairs" is right.
  - The supervised arm read condensed: 2,370 of 2,376 at a lower level, 2,248 of them one level below and 122 two levels below; 6 at their own level (1 at 1 mm, 5 at 2 mm). "Nearly always the label of a level below" is right. "About half" is right: the predicted end displacement is 0.52 of the label's in the median, and 0.49 to 0.65 for nine pairs in ten.
  - The author's probe `nearest_label.py`, run by me on the package as received and on the restored kept copy, writes its stored output byte for byte. Its numbers are mine, and the table of the probes' README is that output.
- **"In `third_0034` the pair at 1 mm starts from the label of 1 mm, and it converged from the same kept state."** Right, by three records.
  - The returned row (label-free, seed 6, raw, 1 mm) has a finite error, 0.44%, and no note.
  - Its nearest label is that of 1 mm.
  - In my chain of round 1, the whole member in the gate's order, the element state has the same fingerprint before the failed solve at 0.5 mm and before the solve at 1 mm, and the solve at 1 mm gives the returned error within 2.2e-16.
  - For `eval_0063` the pair at 1 mm (supervised, seed 6, condensed) has the label of 0.5 mm as its nearest, its returned row is infinite, and my probes of round 2, from the state that the pair before had left, give 61 and 14 iterations at 0.5 mm and at 1 mm.
- **"The six label-free pairs after each of nine solves at 8 mm, and ... all twelve pairs of both arms after three."** These are my measurements of rounds 1 and 2, described rightly.
- **"Between 2% and 49%."** The exact 95% interval for 2 in 1,320 is 0.018% to 0.546%. For 124 pairs that gives 2.25% to 49.30%, around 17.1%. The author's "2.3% to 49.3%" is the same.
- **The README's lines on what each script needs.** I ran what I could as the lines say.
  - On the files of the repository as they are: `verdict_from_rows.py` (8,399 values compared, no difference), `make_units.py` (the 137 units of round 1, byte for byte), `make_defect_units.py` (see the last of the Smaller points), `check_document.py` (3,080 cells, none differing), and `summarise_solves.py` on my results with the repository's rows. Right.
  - The kept copy whole. I ran the author's `c23_deposit.py restore` for the first time. From the repository's 245 files and the archive of the deposit it writes 150 files, each byte for byte the file of the package as received; `c23_deposit.py check` and my own comparison find the 395 files of `return_kept.sha256` with their hashes. On that copy, with the instance files, `check_records.py` and `check_condensed.py` write the summaries of round 2 byte for byte. On the repository's copy as it is, `check_condensed.py` stops at the first prediction file. Right.
  - `check_kept.py`, `check_public.py` and `check_curve_times.py`: the lines name what their arguments are. Right.
  - `check_recomputation.py`: not right (Error 1).

**4. The part "Numbers", the author's steps, the records**

- The part "Numbers" is that of rounds 1 and 2, character for character (46,700 characters), and `audit/c23_write_verdict.py` writes it exactly from the kept records.
- `audit/c23_recompute.py --aggregate` writes `aggregate.json` again as in round 2: byte for byte but for the SHA-256 of the two rows files, and it changes no other file of the records of the recomputation. Neither audit script of the author's is among the 12 paths.
- `joint/records/` is unchanged since round 2.

**5. What the corrected commit would publish** (`check_public.py`, on the 12 paths changed since round 2, 279,967 bytes, and on all 432 paths, 23,484,446 bytes)

- None of the five strings and no account name of the received paths, in any of the forms of round 1. No pattern of a home or temporary folder, now that the filed `check_public.py` puts its patterns together from parts. No e-mail address, no carriage return, no em or en dash, and no American spelling but the proper name of the code's licence in the README.
- The only bytes outside ASCII are four letters in the names of the authors of a paper that the README cites, as at the stamp.
- No path is dropped by a `.gitignore`: by my reading of the rules, and by git itself, which adds all 2,019 files without force and gives the same tree.
- My reports as filed, the author's notes and my scripts hold no name from my list and no path. The names from my list in the 12 paths are of the kind of rounds 1 and 2 (operating systems, solvers, the graphics processor, the tensor library, the deposit); they stand in the README, the verdict document and the probes' README.
- A second pass over each of the 12 files, with the text check that I use for my own reports, found nothing.

## Errors

**1. The README says that `check_recomputation.py` needs the kept copy whole. It does not.** Small and harmless: a reader who follows the line restores 150 files that the script never opens.
- **Where.** `joint/README.md`, the line on `independent/G-C2.3/`: "`check_recomputation.py` needs the kept copy whole and the four training label files."
- **What the records say.** Of the return folder the script reads the two rows files and the ledger; its usage line names the folder as a whole, which may be the origin of the line. Besides, it reads the verdict document, the records of the author's recomputation, the deposit record of the base gate and the four training label files. It opens no label or prediction file of the return package. Run on the repository's files as they are, with the four files, it ends without an error and writes the summary of round 2 byte for byte.
- **Suggested correction.** "`check_recomputation.py` runs on the files of the repository and needs the four training label files besides."
- **Number of the verdict touched:** none.

## Missing

- **A line of the README for `check_nearest_label.py`**, if the script is filed. For example, in the list: "`check_nearest_label.py` (from which label the exact solve of each returned pair starts)"; and in the sentence on needs: it needs the kept copy whole and no instance files.
- **The report of this round and the final header** of the audit report file, as that header already says. See the next section but one.

## Smaller points

- **"Whether its first evaluation ends within the cap is set by the element state that was left and by that label."** The wording is mine, of round 2, and it is not exact. By the stamped code the solve starts from the nearest label with the pair's own end displacement put in (`c2/instance.py`, `solve_at_e`), so a third thing enters the first evaluation. In everything that was measured it made no difference.
  - My 84 probes of round 2 cover seven combinations of a state and a label. Within one combination the end displacements are up to 2.5 times apart, and the energy of one of the two element sets at that evaluation differs up to 28-fold (that of the other set is the same for all). The numbers of iterations are the same for every pair of a combination.
  - The 128 states that the label-free pairs "seeds 5 and 6, condensed, 8 mm" left on the third sample were each followed by one pair on the host (the raw pair of the same seed at 0.5 mm) and by another in the author's first recomputation (the condensed pair of the next seed). In both, the solve failed after the same single state and after no other.
  - Exact would be: "The exact solve of a pair starts from the label nearest to the pair's predicted end displacement, with that end displacement put in. Whether its first evaluation ends within the cap was set, in everything that was measured, by the element state that was left and by that label." The first point under the table of `nearest_label.py` in the probes' README ("There a failure depends on the element state left and not on the pair that follows") would take the same words.
  - No number depends on it. The estimate of one in six rests on what was observed on the host.
- **The probes' README, second point under that table.** "So above 0.5 mm their solves start from the label of a level below" holds for 2,370 of the 2,376 pairs, as the table above it shows. The verdict document's "nearly always" is the exact form.
- **List C of `make_defect_units.py`** (the failed solve of G-C2.1) needs that gate's files and not this gate's: its labels and prediction files are in the repository (`records/c2/return`), its instance files are written by `audit/c2_recompute.py --regenerate`. The header of the script says so; the README's sentence on `solve_pairs.py` does not.
- **The counts of this state.** The export of this round has 2,019 files and its list 432 paths, as the note of the environment says. If another count was given with the task, or is to be written into the final header, these are the numbers that I find.
- **A precision on my own report of round 2.** I wrote that `make_defect_units.py` "reproduces the lists that I ran". It writes the lists A, C, E, D and G byte for byte as I ran them, and the one unit of A_chain that I ran. Of list F it writes the form in which I ran 66 of my 68 members. The two others (`third_0000`, `third_0001`) I had probed with an earlier form, whose first three steps are those of the later one. No reported number depends on the difference.

## What the author still adds after this round, not seen by me

- my report of this round, as delivered, in the audit report file;
- the author's notes on it;
- the final header of that file, with the time of this round; I suggest that it name the tree of the state that this round read, `7ea167474b3c5963328b27ff71aed5e86413c4ae`;
- the script `check_nearest_label.py` in `joint/audit/independent/G-C2.3/` and its line in the README;
- the corrections of this round, if they are made: the README's line (Error 1) and the wordings under Smaller points.

None of these is audited. The paragraph "Independent audit" says that "a third round read the corrected state". Once the items above are added, the pushed state is no longer the state that was read. The header of the audit report file, or that paragraph, should then say that what was changed after the third round was not seen by the auditor, and list it. If the paragraph is to say what this round found, this is accurate: "A third round read the corrected state and found one line of the README to correct and smaller points of wording."

## Not checked

- **The suite.** I did not run the tests. No test of `joint/tests/` names one of the 12 paths changed since round 2.
- **The commit, its parent and the tag as git objects, and the commit's date:** the exports hold no history. The trees of the three states I did compute.
- **The operator's note** behind "at about 00:10", and the owner's records. The time agrees with the records as far as they go: part 1 was written at 00:05:16.
- **The deposit's DOI** and anything on the network.
- **Exact solves:** none in this round. Nothing that the solves and probes of rounds 1 and 2 rest on has changed.
- **The author's steps** `--regenerate`, `--fields`, `--host`, `--curves` and `--resolve`, and `c23_deposit.py pack`: not run by me, as before. `restore` and `check` I ran in this round.
- **The unchanged text.** Of the 12 paths I read every changed line; I did not read the unchanged parts of the documents again.

## Scripts changed or added in this round

One new script, to join the filed copies in `joint/audit/independent/G-C2.3/`. It holds no path of a machine and none of the five strings, and it imports nothing of the repository. The twelve filed scripts are unchanged.

| Script | Change |
|---|---|
| `check_nearest_label.py` | new: for each arm, reading and level, the returned pairs whose nearest label is that of their own level, of a level below or of a level above, and by how many levels, from the end displacements in the rows files and in the label files; the prediction files as a second source. It needs the kept copy whole and solves nothing. |

---

**What was done after round 3 (the author)**

Errors
1. The README's line on `check_recomputation.py`: corrected as proposed.

Missing
1. The line for `check_nearest_label.py`: added, with what the script needs. The script is filed as delivered, thirteen files in all.
2. The report of round 3 and the final header: filed. The header names the trees of the three audited states and lists what was changed after round 3.

Smaller points
- "Set by the element state that was left and by that label": the verdict document and the probes' README now have the exact form proposed, with "in everything that was measured".
- The probes' README, the second point under the table: now "nearly always".
- List C of `make_defect_units.py`: the README now says that `solve_pairs.py` needs G-C2.1's files for it, and where they are.
- The counts of the state: 2,019 files and 432 paths. The author's message to the auditor had given 2,018 and 431; that was the author's miscount.
- The precision on `make_defect_units.py` and its list F: nothing for the author to do.
- The paragraph "Independent audit": it now says what the third round found, in the words proposed, and that the auditor has not seen what was changed after that round.

The tests: not run again. The whole suite of the folder passed on the state that round 1 audited (156 tests), and nothing that was changed since is imported or read by a test.
