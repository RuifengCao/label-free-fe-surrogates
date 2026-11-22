# Gate G-C2.3: verdict

**What was pre-specified**
- `docs/PRESPEC_G-C2.3.md`, configuration SHA-256 `3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e`, stamped at 12:02 GMT on 18 November 2026.
- The tag `prereg-c23`, made at 12:44:17 GMT the same day (the operator's record), points to commit `d603fd8`, which is dated 12:43:41 GMT in the repository's history. The code is pinned file by file in `docs/G-C2.3_code.sha256` (41 files).
- The commands are those of `RUNBOOK_C23.md`. They were run by the job queue of the owner's laptop, which is outside the stamp. The queue's job files and logs, its guard, its waiting job and the generator of the job files are in the return package; its runner is not, as section 9 of the runbook says.

**Where the numbers come from**
- **The return package**: `c23_return.tar.gz`, SHA-256 `68f008496aa4215278c0dee7c39651a62b6fd5a74f457f260398c03392102618`, 211,205,734 bytes, made on the laptop on 19 November 2026 between 19:45 and 19:47 GMT (the operator's record). The SHA-256 written beside it matches the file.
  - `records/c23/return_files.sha256` lists the SHA-256 of its 400 files as received, and `records/c23/return_listing.txt` is the archive's listing, with the numbers of the owner and the group in place of the name of the account that packed it.
  - The files are kept with the differences listed under "The records as kept" below: 245 of them in `records/c23/return/`, and the 150 label and prediction files in a deposit outside the repository, which `records/c23/deposit.json` lists.
- **The verdict and every metric** come from `verdict.json`, `rows_label_free.json` and `rows_supervised_512.json` of the return package, which the stamped `c23/evaluate.py` wrote on the laptop. The SHA-256 of `verdict.json` is `43323a365a9c55aba8f46477a528e6ec883cefa5242e2d8b89a1bc165ab2b83e` as received and `ae394314f233a663eb9812eb41aeac73fc84fbba7da5d26cf861cb7b444019ff` as kept in `records/c23/return/`, with LF line ends.
- **Part 1 was final before part 2 began.** `verdict_part1.json` (SHA-256 `5cd63a8e644af210f04ca7899e9a6bd54b65786c218fb9d256d0623bb09d776d` as received) was written at 00:05:16 GMT on 19 November 2026, before any training member had a label; the final verdict states that its part 1 is that one.
- **The author's recomputation**: `audit/c23_recompute.py` (not under the stamp). It follows the audit script of G-C2.2 and was written on 19 November 2026, after the run had ended and its verdict was known. Its step in the gate's own visiting order was added on 20 November 2026, after the defect described below had been found (the author's statement; no record dates the script). Its outputs are in `records/c23/audit/`. What it covers is stated under "The recomputation" below.
- **The tables** at the end are generated from those records by `audit/c23_write_verdict.py`, written after the run.

**Independent audit.** A separate agent that wrote none of the code, the records or this document audited the return package as received and the proposed commit before the push, in three rounds on 22 November 2026. With code of its own it recomputed the verdict from the returned rows, solved 137 pairs again from a zero element state with its own driver on the stamped library, tested the defect of the measuring code with probes of its own, and checked the run against the pre-specification, this document with its tables, the author's recomputation and the kept copy. It found that the verdict holds, and it found no wrong number among the 3,176 table cells and the numbers of the text that it derived again. The six errors of its first round and its list of what was missing concerned statements of this document and of the README. Its second round found the corrections right but for one new statement, on what decides whether a solve fails, and for this paragraph. These were corrected. A third round read the corrected state and found one line of the README to correct and smaller points of wording. The auditor has not seen what was changed after that round; the header of the file of its reports lists it. Its reports are in `docs/reviews/audit_report_G-C2.3_2026-11-22.md`, each followed by the author's notes on what was done, and its scripts in `audit/independent/G-C2.3/`.

## Run record

**Host** (`smoke/smoke_report.json` of 18 November; `preconditions.log`, written by the operator)
- The owner's laptop, the host of G-C2.2: Windows 11 (`Windows-11-10.0.26200-SP0`), an NVIDIA GeForce RTX 4070 Laptop GPU with 8 GiB, 32 logical processors.
- Python 3.12.16, numpy 2.4.6, scipy 1.18.1, torch 2.12.1 with CUDA 13.2. Worker processes are started by spawn and use one thread each for linear algebra. The sparse solver is scipy's SuperLU.

**Preconditions** (section 0 of the runbook; `preconditions.log`)
- The tree was taken from the tag: an archive of 108 files, SHA-256 `38efa55dcf0aa939d0d92e55122e105751bd3cb1f14e50d1ddbc79f32c36f1e7`, with the same hash on the laptop. Its 41 pinned files matched their hashes there, at 12:48 GMT on 18 November and again at 20:32, before the first command.
- The 69 tests of the runbook passed on a full export of commit `d603fd8` on the operator's Linux machine, between 12:46:56 and 13:10:19 GMT on 18 November.
- The three state files of G-C2.2's label-free runs have the SHA-256 pinned in the configuration.
- The owner gave the start at 20:31 GMT. The host check (`c23/smoke.py`, a reduced configuration) passed on the laptop from the stamped tree between 20:32:43 and 20:38:18.
- The configuration command printed the stamped hash at 20:38.

**Generation, labels and predictions** (18 November)
- Generation: 20:45:19 to 20:47:16, 644 members: 512 for training, 64 of the third sample, 64 fresh members of G-C2.2 and 4 tested members. From then on members of seed 20261118 existed.
- Labels of the held-out and tested members, with 16 worker processes: 20:47:17 to 21:04:46. 132 members at seven levels; every level converged. The check of the labels passed at 21:04:47.
- Predictions of the three label-free states, in both readings: 21:04:47 to 21:27:24 (227 s, 486 s and 644 s).

**Part 1**
- Evaluation of the label-free arm: 18 November 21:27:24 to 19 November 00:05:16, with 16 worker processes, exit code 0.
- The verdict was written at 00:05:16 on 19 November: identity OK, self-check PASS, ranking HOLDS, comparison INCOMPLETE. The same command wrote `verdict_part1.json`.
- The operator reported part 1 to the owner at about 00:10, with the SHA-256 of `verdict_part1.json` and of the label-free rows file, as section 5 of the runbook asks. The report is a note that the owner keeps; it is not in the repository.

**Part 2** (19 November)
- Labels of the 512 training members at eight levels, 4,096 reference solutions: 00:05:17 to 01:10:13, with 16 worker processes; every level converged. The check of all 644 labelled members passed at 01:10:14.
- Training, each run 102,400 steps in 200 epochs:

| Seed | Started | Ended | Hours of training | Interruptions |
|---|---|---|---|---|
| 5 | 01:10:14 | 06:05:23 | 4.85 | none |
| 6 | 06:05:23 | 11:15:47 | 4.96 | none |
| 7 | 11:15:47 | 16:20:26 | 4.86 | none |

- Each run ended with the status `finished` and wrote its predictions in both readings. No run stopped on a non-finite value, and none was resumed.
- Evaluation of the supervised arm: 16:20:26 to 19:18:36, with 16 worker processes, exit code 0.
- The final verdict was written at 19:18:37: identity OK, self-check PASS, ranking HOLDS, comparison "label-free closer"; `"part1_same_as_first": true`; `"missing"`, `"non_finite"` and `"not_evaluated"` empty.

**The queue**: the 34 commands and guards of the gate ended with exit code 0, as had the six jobs run before the stamp. None was killed, and no name occurs twice. Each command of the gate started in the second in which the one before it ended, with one exception: the generation started seven minutes after the configuration command, when the gate's remaining jobs had been queued (the times of the commands are in `records/c23/audit/records.json`).

## Deviations

None of them changes a threshold, a criterion, a reading, a level or a seed.

1. **Output that no comment of the runbook mentions.** The runbook's rule is to report any output that differs from a comment. Two kinds of lines were not reported during the run. Each prediction of a label-free state and each start of a supervised run printed one warning of PyTorch, that the invariants of sparse tensors are not checked; it is the warning of G-C2.2's runs (deviation 4 of `docs/G-C2.2_verdict.md`) and of the host check. And each of the four label commands ended its output with a line that counts the members labelled (`labelled 64`, `labelled 64`, `labelled 4` and `labelled 512`), which the stamped command prints.
2. **What the operator read between the two parts.** Part 1 was final at 00:05:16 on 19 November, and the runbook has the operator report it then. The operator also took the label-free rows and the kept record of part 1 from the laptop and recomputed part 1 from the rows with a script written for that purpose, while the training labels were being solved. The operator then read the pairs that the check missed and computed what S2 would be at three other thresholds; that reading is exploratory and enters nothing here. These rows are also the label-free side of part 2. Nothing of the queue was written or changed after 20:44:59 on 18 November, when the gate's remaining jobs were queued; the supervised arm was labelled, trained and evaluated by those jobs (the operator's statement; the queue's records show every job started within two seconds of the end of the one before it).
3. **The length of the two evaluations.** The runbook estimates two hours for each; they took 2 h 38 min and 2 h 58 min. Its line for a report is eight hours.
4. **The suite on another machine.** As the runbook provides, the 69 tests ran on the operator's Linux machine and not on the laptop. That machine has numpy 2.5.3 and PARDISO, where the laptop has numpy 2.4.6 and scipy's solver alone.

The records show no other departure. Every reference level converged within the configured limits, every returned file that the verdict names as an input has the SHA-256 that the verdict gives, and the queue ran as stated above (`records/c23/audit/records.json`).

**The records as kept.** The kept copy holds the package's files with these differences; `records/c23/return_files.sha256` gives the hashes as received and `records/c23/return_kept.sha256` as kept. The repository holds the kept copy without its label and prediction files (the last point).
- In 130 text files the line ends CR LF, which Windows wrote, are LF.
- In 12 logs of the queue the path of the working folder on the laptop is replaced by `W`.
- Five files are not kept: the model states of the host check, which the repository's rules leave out. `records/c23/keep_report.json` lists them with their hashes.
- The other 265 files are byte for byte as received.
- `audit/c23_keep.py` makes the copy, its report and the lists from the package as received, the archive's listing and a file of the strings that are replaced. That file is not in the repository; the owner keeps it with the package.
- The kept copy has 395 files, and `records/c23/return/` holds 245 of them. The other 150 are the label and prediction files, each with the bytes it had in the package: the 132 files of `labels/` and `preds.npz`, `preds_condensed.npz` and `preds_base.npz` of each of the six runs, 206,242,833 bytes together. They are deposited at Zenodo as one archive, `c23_arrays.tar` (206,366,720 bytes, SHA-256 `b4c697d9e010bb89e909ecfc37e27143e062e4d998c2f4a86a658413c743fa52`), https://doi.org/10.5281/zenodo.24380492; the DOI was reserved before this commit, and the record is published when the commit has been pushed. `records/c23/deposit.json` gives the size and the SHA-256 of the archive and of each file, and `audit/c23_deposit.py` makes the archive from a whole kept copy and restores the folder from it.
- The 68 label files of G-C2.2's fresh members and of the tested members have the bytes of the same files in G-C2.2's deposit: the labels were solved again on the host and came out bit for bit.
- The labels of the 512 training members, the instance files and the three supervised model states are not in the package. They stay on the laptop until this verdict has been audited, as the runbook provides.

The measuring code has a defect that the run did not show and the recomputation found. It is no departure from the stamped procedure, and it is described in a section of its own, after the verdict.

## Verdict

**Identity: OK.** Computed again from the three state files, the judged values of each label-free run on G-C2.2's fresh members equal G-C2.2's exactly, in both readings (largest difference 0.0, against a tolerance of 1e-4).

**Part 1, the self-check: PASS, judged as pre-specified. The ranking R HOLDS.**
- Judged: the three label-free networks of G-C2.2, read after the amplitude condensation, on the 64 members of the third sample at seven levels, 448 pairs. A pair is flagged when the spread of the predicted force over the three runs is at least 0.0045.
- **S1** holds: no pair that is not flagged has an error above 10% in any run. S1 was put to the test: 10 pairs are above 10% in at least one run (8, 8 and 7 pairs in the three runs), and all of them are flagged.
- **S2** holds: 8 of the 981 readings of the pairs that are not flagged are above 5%, that is 0.82% against a limit of 1%. The largest error that is not flagged is 6.1%.
- **S3** holds: 121 of the 448 pairs are flagged, 27.0% against a limit of 35%.
- **R** holds: in the three runs, the probability that a pair above 5% has a larger spread than a pair at or below 5% is 0.909, 0.912 and 0.949, against a limit of 0.90.
- In the three runs 25, 26 and 26 pairs are above 5%, of which 22, 23 and 24 are flagged; 8, 8 and 7 are above 10%, all flagged.
- The check needs three training runs, and the threshold was set on T-stubs of this family.

**Part 2, the comparison at equal budget: "label-free closer", by the rule as pre-specified.**
- Judged: both arms in the condensed reading on the same 448 pairs; for each arm the median over its three seeds of the per-seed median error and of the per-seed 90th percentile.
- Label-free arm: 0.79% and 3.75% (seeds: 0.79%, 0.84%, 0.78% and 3.75%, 3.72%, 3.81%).
- Supervised arm, condensed: 66.9% and 111.9% (seeds: 69.5%, 66.9%, 58.7% and 113.6%, 111.9%, 110.4%).
- The ratios, supervised over label-free, are 84.3 and 29.9. Both are above 1 and above 3/2: "label-free closer".
- **The size of these two ratios is an artefact of the reading and must not be quoted as the size of the difference.** The condensed reading was developed on the label-free networks. Applied to the supervised networks it sets the amplitude to its lower limit, 0.5, in 84%, 77% and 67% of the pairs of the three runs, and nearly halves their displacements (see "What this means").
- **The supervised arm read raw**, which the pre-specification has stated beside the wording in every case: 1.71% and 6.61% (seeds: 1.71%, 1.63%, 1.73% and 6.79%, 6.61%, 5.30%). Over the label-free arm's condensed reading the ratios are 2.15 and 1.76. They give the same wording, "label-free closer".
- Both arms read raw (reported): 1.36% and 9.64% for the label-free arm against 1.71% and 6.61%; ratios 1.26 and 0.69, "comparable" by the same rule. The label-free arm has the smaller median and the supervised arm the smaller 90th percentile.
- The supervised arm was trained with the label-free arm's settings and was not tuned.
- What each arm needed. Label-free: no reference solution; 14.08, 12.70 and 12.55 hours of training (G-C2.2's records) at a peak of 3.5 GiB of GPU memory. Supervised: 4,096 reference solutions, 16.9 processor hours (65 minutes with 16 worker processes), shared by the three runs; 4.85, 4.96 and 4.86 hours of training at a peak of 0.46 GiB.
- Whatever the wording, it does not carry to another family, mesh or budget, or to a supervised arm whose settings were chosen for the supervised loss.

**The recomputation**
- The author recomputed the following on another machine, from the returned rows, predictions and labels and from instances regenerated with the stamped code. The machine: Linux, Python 3.13.18, scipy 1.18.1 with its SuperLU, one BLAS thread a process. The host was Windows with Python 3.12.16. Where this text gives a bound for a difference, the bound is rounded up; the part "Numbers" prints the same differences rounded to the nearest.
  - **The numpy version.** The steps of 19 November 2026 (the records, the instances and the judged reading in a visiting order of the author's own) ran under numpy 2.5.3 and not under the host's numpy 2.4.6. This was the author's slip. Every later step ran under numpy 2.4.6. The records in `records/c23/audit/` name the environment of each step; for a step that was started more than once, that of its last start.
  - **The instances.** All 644 regenerated files have the manifest's SHA-256, when written through zlib 1.3 and with the archive's creator field as Windows writes it. The members are the configured draws, and no two of the four sets share a member.
  - **The verdict file, with the stamped code.** Run on Linux on folders rebuilt from the package, the stamped `verdict` command writes a `verdict.json` that has the SHA-256 of the kept copy, `ae394314...`: the bytes of the returned file with LF line ends.
  - **The verdict from the returned per-pair rows, with the script's own code**: every run's median and 90th percentile, their medians over the seeds, the ratios and the wording of part 2, the identity values, and every count, criterion and word of part 1 are the returned ones exactly, for both arms, both readings and the three sets. The part 1 that was kept before any training member was labelled is the part 1 of the final verdict.
  - **The error of 5,418 pairs in the gate's own visiting order**, with the stamped metric function and its exact solve at each predicted end displacement (36.7 processor hours): every pair of both arms in both readings on the third sample, 5,376 pairs, and the 42 pairs of the supervised arm on `eval_0063`. The signed errors agree with the returned ones to within 6.1e-13 in absolute terms, and the other metrics of these pairs to within 2.0e-14. The three returned rows with an infinite error are infinite again, with the same note. Every run's median and 90th percentile recomputed from these errors, and their medians over the seeds, differ from the returned ones by at most 5.9e-13 in relative terms; the judged ratios differ by less than 1e-13 and the ratios with the supervised arm read raw by less than 6e-13. Part 1 recomputed from these errors is the returned one in every count: PASS, and R HOLDS.
  - **The judged reading in another visiting order** (the first step, on 19 November; 4.6 processor hours): the 1,344 judged pairs of the label-free arm, one reading at a time, and the first 27 pairs of the supervised arm read raw; that step was not continued once the defect had been found. 1,370 of the 1,371 errors agree with the returned ones to within 4.1e-13. One solve failed. The section on the defect of the measuring code describes it.
  - **Every metric that needs no solve**, for all 11,088 returned fields (six runs, two readings, 132 members, seven levels): the largest absolute difference from a returned value is 2.0e-14, and the containment in the bound is the returned one for every field.
  - **The condensed fields.** Computed again in float32 from the returned base fields, raw fields and amplitudes, the 792 arrays (132 members, six runs) equal the returned condensed fields bit for bit.
  - **The labels.** Evaluated on the regenerated instances, the 924 returned label fields give the label's force and end displacement exactly and its energy to within 4.5e-16 in relative terms; their largest unconstrained residual there is 1.5e-10. Four members (two of the third sample, one fresh member of G-C2.2, one tested) were re-solved from the regenerated instances: not bit for bit, with differences of at most 4.0e-15 of the largest unknown, in the ledger's numbers of iterations.
  - **Four training members**, drawn without replacement from the 512 with numpy's `default_rng(20261120)`, were re-solved in the same way: differences of at most 8.3e-15 of the largest unknown, in the ledger's numbers of iterations. Their label files are not in the package. The author took them from the laptop on 20 November 2026; they have the SHA-256 that the returned ledger gives (`records/c23/audit/resolve_train.json`).
  - **The records.** The returned configuration is the stamped one, byte for byte. The ledger holds the 644 labelled members once each, at the configured levels, 5,020 levels in all, every one converged and within the configured limits. The 132 label files have the ledger's SHA-256, and the instances that the ledger names are those of the manifest. Every prediction file holds the 132 members with the expected shapes. The twelve prediction files that the evaluation reads, the raw and the condensed fields of each run, have the SHA-256 that the verdict records; the six files of base fields are not among the verdict's inputs. Each supervised run's log gives its history's losses, times and counts, and its history names the ledger's training entries by their hash.
  - **The last step on the repository's copy.** Run on `records/c23/return/` and `records/c23/audit/` as the repository holds them, without the label and prediction files and without instances, the step that compares everything writes `aggregate.json` again, byte for byte except the SHA-256 of the two rows files, which the repository keeps with LF line ends.
- **Not recomputed with exact solves**: the error of the 5,670 pairs on G-C2.2's fresh members and on the tested members, other than the supervised arm's 42 pairs on `eval_0063`. Their other metrics were recomputed (above). The reported numbers that rest on those errors are the returned ones. The label-free arm's errors on G-C2.2's fresh members enter the identity check: their medians and 90th percentiles equal G-C2.2's exactly, and G-C2.2's audit recomputed those of the condensed reading.
- The training of the supervised arm was not repeated. Its model states were not returned; they stay on the laptop.

## A defect of the measuring code, found by the recomputation

**What it is**
- The error of a pair needs an exact solve of the reference model at the predicted end displacement. The reference code keeps, for each set of elements, the internal (bubble) parameters of its last solve and starts its next evaluation from them (`fejoint/nlhex.py`, the attribute `bub`).
- The stamped evaluation of an arm builds one problem object for a member and visits that member's pairs one after another: for each run the condensed reading and then the raw one, each over the seven levels. So the solve of a pair starts from the element state that the pair before it left.
- The element iteration is capped at 60 steps. Where the pair before was at 8 mm and the pair itself is at 0.5 mm, the iteration has in a few cases not ended within the cap. The solve then raises "bubble condensation did not converge", and the stamped metric writes an infinite error, as it does for any failure of that solve.
- The exact solve of a pair starts from the label nearest to the pair's predicted end displacement, with that end displacement put in. Whether its first evaluation ends within the cap was set, in everything that was measured, by the element state that was left and by that label. At 0.5 mm every returned pair, of both arms and both readings, starts from the label of 0.5 mm (`probes/c23_reference_state/nearest_label.txt`), so that there the run and the reading of the pair that follows make no difference. The independent audit measured this: the first evaluation at 0.5 mm needed the same numbers of element iterations for the six label-free pairs after each of nine solves at 8 mm, and for all twelve pairs of both arms after three. Above 0.5 mm the label is that of the pair's own level for the label-free arm read condensed and for the supervised arm read raw, and for all but 15 pairs of the label-free arm read raw. For the supervised arm read condensed, whose end displacements are about half, it is nearly always the label of a level below.
- For one such pair the cause was isolated (`third_0034`; `probes/c23_reference_state/`, written and run after the run): a new problem object that is given nothing but the element state left by the pair before fails in the same way; with that state set to zero the solve converges. From the kept state one set of elements needs 62 steps where the cap is 60; from zero it needs 2, and reaches the same energy to within 2e-16 in relative terms.
- The element state is also the start of a second computation. After the exact solve, the stamped metric evaluates the predicted field itself for the other metrics, under the same cap, from the state that the solve has left; after a failed solve that is the state kept from the pair before. That evaluation ended within the cap for all 11,088 returned fields, also in the three rows whose solve failed. An evaluation does not write the element state; only a solve does.
- The reference solutions are not exposed in the same way. The labels of a member are solved on a problem object of their own, level by level in rising order, each from the level below, and all 5,020 levels converged.

**Where it acted in the gate's run.** Three of the 11,088 returned rows carry that note. None of them is in the judged reading on the judged sample.

| Arm | Reading | Seed | Set | Member | Level | Returned | With the element state set to zero |
|---|---|---|---|---|---|---|---|
| label-free | raw | 6 | third sample | `third_0034` | 0.5 mm | infinite | -0.27% |
| supervised | condensed | 6 | fresh members of G-C2.2 | `eval_0063` | 0.5 mm | infinite | +102.1% |
| supervised | condensed | 6 | fresh members of G-C2.2 | `eval_0063` | 1 mm | infinite | +105.4% |

- A failure carries on to the next pair where that pair starts from the same label, because a failed solve leaves the element state as it was: hence the two rows of `eval_0063`, whose pair at 1 mm, read condensed, starts from the label of 0.5 mm again. In `third_0034` the pair at 1 mm starts from the label of 1 mm, and it converged from the same kept state.
- The three rows enter reported numbers, and no judged one. With the values of the last column, 18 printed cells of the part "Numbers" would change (`probes/c23_reference_state/effect_on_reported_numbers.txt`):
  - the label-free arm read raw on the third sample: the median of seed 6, which is also the median over the seeds, 1.354% in place of 1.358%; the 90th percentile of seed 6, 10.012% in place of 10.191% (the median over the seeds is seed 7's and stays); 45 pairs above 10% in seed 6 in place of 46; no infinite row in place of 1;
  - the ratio of the medians with both arms read raw, 1.261 in place of 1.257; the wording "comparable" would stand;
  - the reported block of part 1 for the raw reading on the third sample: 3 pairs not flagged above 10% in place of 4, 30 of 708 readings above 5% in place of 31, and a ranking probability of seed 6 of 0.868 in place of 0.859; the block would still read FAIL, and R would still not hold;
  - label-free seed 6 read raw at 0.5 mm, in the tables by level: a median of 0.91% in place of 0.95%, a 90th percentile of 3.06% in place of 3.70% and a median signed error of +0.03% in place of +0.06%;
  - the supervised arm read condensed on G-C2.2's fresh members: the 90th percentile of seed 6, which is also the median over the seeds, 120.1% in place of 120.5%; no infinite row in place of 2; and the ratio of the 90th percentiles with both arms read condensed, 32.78 in place of 32.88;
  - the count and the table of the rows with an infinite error.
- These values are computed after the run and are exploratory.

**What the recomputation found.** The author's first recomputation, on 19 November 2026, visited the judged reading alone. The first pair of seeds 6 and 7 of each member then followed the last condensed pair of the seed before, not the last raw pair as on the host: 128 of the 1,344 judged pairs of the label-free arm started from another element state than on the host. Each member was computed in one piece: the times of the per-pair files show that none was resumed part-way. Those files are not kept; the independent audit checked their times in its second round.
- 1,343 of the 1,344 errors agree with the returned ones to within 4.1e-13.
- One solve failed: `third_0034`, seed 7, 0.5 mm, where the host returned 0.37%. The pair is not flagged (its spread is 0.00014).
- That solve followed seed 6's condensed pair at 8 mm. The element state that this pair leaves is the one behind the host's own infinite row of `third_0034` (seed 6, raw, 0.5 mm, which follows the same pair in the gate's order). So the first recomputation met the host's bad state a second time, with a judged pair behind it where the host had a reported one. It is no further observation of the defect.
- **Read by the letter of the rule, S1 does not hold in that visiting order, and part 1 would be FAIL.** S2 and S3 hold there (9 of 981 readings above 5%, 0.92%), and R holds (0.909, 0.912 and 0.915). In the gate's own order the solve converges, and the recomputation that follows that order gives the returned value bit for bit.

**What stands, and what does not**
- The verdict of part 1 is the one that the stamped code returned on the host, in the order that the stamped code fixes. It stands as the verdict of the gate.
- On a single error the defect works in one direction. It can turn a finite error into an infinite one; it cannot make a large error small, because a solve that converges ends at the minimiser of a convex problem, whatever state it started from. The converged solves bear this out: where both visiting orders converged, the errors agree to within 4.1e-13, and the independent audit's 137 solves from a zero element state agree with the returned errors to within 2.7e-13. An infinite error can only count against S1 and S2, and it does not enter S3. It could move R either way, and in part 2 it could lower a ratio if it fell in the label-free arm and raise one if it fell in the supervised arm; no judged row is infinite, so neither happened. So the facts behind the PASS are not weakened: every judged error is finite and was reproduced, and every pair above 10% is flagged.
- What is weakened is the gate as a procedure. The rule that a failed solve counts as an infinite error was written for predictions whose end displacement the reference model cannot reach. It was not known that the solve could fail for a reason that has nothing to do with the prediction. S1 could therefore have failed without any error of the surrogate, and whether it did depended on the order of the evaluation.
- That it did not is partly chance. On the host, 2 of the 1,320 element states left by a pair at 8 mm made the next solve fail. In the gate's order the 128 judged pairs at 0.5 mm of seeds 6 and 7 follow the raw pairs at 8 mm of seeds 5 and 6, and none of those left such a state. At the host's rate of 2 in 1,320, and with 124 of those 128 pairs not flagged, the chance that part 1 would have read FAIL in the gate's own order without any error of the surrogate was about one in six. Only two events carry that estimate, so it is rough: an exact 95% interval for 2 in 1,320 puts the chance between 2% and 49%.
- The stamped code is not changed. A later gate that uses this reference code states in its own pre-specification how its exact solves are started and how a failed solve is treated.

**The earlier gates**
- **G-C2.1.** Its verdict reports one failed reference solve: the supervised arm's seed 1 at 0.5 mm on `eval_0046` ("an infinite distance"). It is the same defect. Solved alone the pair gives -0.45%; after the pair before it in that gate's order (seed 0 at 8 mm) the solve fails; with the element state set to zero in between it gives -0.45% again. In the tables of `docs/G-C2.1_verdict.md` that run has 1 infinite distance and 128 pairs above 10%; with the converged value they are 0 and 127, and the run's 90th percentile is 20.5% in place of 20.6% (`probes/c23_reference_state/c21_effect.txt` gives every figure that contains the pair). The supervised arm is descriptive in G-C2.1, so that gate's verdict is not touched. An erratum is added to that document in this commit.
- **G-C2.2.** None of its 5,544 returned rows carries a note. Its author's recomputation also visited the judged reading alone (the rule `judged` of `audit/c22_recompute.py`), and its independent audit solved three pairs from a zero field; neither looked at the element state, and no solve happened to fail.
- The four files concerned (`fejoint/nlhex.py`, `fejoint/nlsolve.py`, `c2/evaluate.py`, `c2/instance.py`) are byte for byte those stamped for G-C2.1.

## What this means

**Part 1, as fixed in advance (PASS).** On a third sample, three training runs that agreed within 0.45% in force held no error above 10%, and at most one reading in a hundred above 5%.
- The check needs three training runs. The threshold was set on T-stubs of this family.
- 27.0% of the pairs were flagged. In the three runs 25, 26 and 26 pairs were above 5%, of which 22, 23 and 24 were flagged, and 8, 8 and 7 were above 10%, all of them flagged.
- **The margins.** S1 held with room: the smallest spread among the 10 pairs above 10% is 0.0334, 7.4 times the threshold, and the largest error of a pair that is not flagged is 6.1%. S2 and R held narrowly. S2 allows 9 readings above 5% among the 981 that are not flagged, and there are 8. R is 0.909 and 0.912 in two runs against a limit of 0.90. On G-C2.2's fresh members, which had been read when the threshold was chosen, the same rule left no reading above 5% among 990 and gave 0.944 to 0.956.
- **The three pairs that the check missed** are not flagged and lie just above 5%: `third_0001` at 2 mm (5.5%, 5.5%, 5.6%; spread 0.0008), `third_0005` at 2 mm (5.6%, 6.1%, 6.0%; spread 0.0039) and `third_0044` at 6 mm (5.0%, 5.1%, 5.0%; spread 0.0011). The three networks are wrong there by nearly the same amount, which the spread cannot see.
- **The check holds for the condensed reading only.** Applied unchanged to the raw reading of the same networks it fails all three criteria on the third sample (212 pairs flagged; 4 pairs not flagged above 10%, one of them a failed solve; 31 of 708 readings above 5%), and R does not hold (0.85 to 0.86). Applied to the three supervised networks it fails as well.
- By level, the flags follow the plastic range: 2, 1 and 5 of 64 pairs are flagged at 0.5, 1 and 2 mm, and 21, 27, 24 and 41 at 3, 4, 6 and 8 mm.

**Part 2: the direction, and its size**
- The wording by the rule is "label-free closer", with the supervised arm read condensed (judged) and with it read raw (stated beside it). The text therefore need not say that the wording depends on how the supervised networks are read. The size does depend on it: by a factor of about 40 in the ratio of the medians and of about 17 in the ratio of the 90th percentiles.
- **Why the condensed reading fails on the supervised networks.** The condensation scales the field's increment over the base field by one amplitude that minimises the energy. The supervised networks' fields are close to the reference in displacement but not low in energy. The energy then falls all the way to the lower limit of the amplitude: 378, 344 and 298 of the 448 fields of the three runs end at 0.5, and the largest amplitude of a run is 0.64 to 0.72. The energy falls by 11% to 13% in the median, and the end displacement is nearly halved. The label-free networks' amplitudes lie between 0.77 and 1.21 with a median of 1.000, none at a limit.
- **Read as each arm was built**, the label-free arm condensed and the supervised arm raw, the label-free arm is closer by a factor of about two: 0.79% against 1.71% in the median and 3.75% against 6.61% at the 90th percentile (ratios 2.15 and 1.76). This sets one arm after the condensation against the other without it.
- **Read alike, both raw**, the two arms are comparable by the rule: the label-free arm has the smaller median (1.36% against 1.71%, a ratio of 1.26) and the supervised arm the smaller 90th percentile (6.61% against 9.64%, a ratio of 0.69, close to the band's end of 0.667). On G-C2.2's fresh members the same reading gives ratios of 1.32 and 0.59, "mixed" by the rule (reported). In both samples the supervised arm is the closer one at the 90th percentile when both are read raw. The label-free arm's advantage in the tail comes from the condensation, which fails on these supervised networks.
- **By level** (median of the three runs' medians): the supervised arm read raw is worse at small displacements (4.3%, 2.0% and 1.9% at 0.5, 1 and 2 mm, against 0.5%, 0.4% and 0.5% for the label-free arm condensed) and better at 8 mm (1.2% against 1.8%). 0.5 mm lies between its labelled levels of 0.1 and 0.75 mm.
- **The supervised arm was not tuned.** Its learning rate, schedule and stability recipe are those developed on label-free runs. Its cap acted on 9,648, 9,846 and 10,352 of the 102,400 steps of a run, against 1,805 to 2,154 in the label-free runs of G-C2.2.
- **Equal budget means equal members, steps and network, not equal time.** On this laptop the supervised arm took less time than the label-free arm: 4.85 to 4.96 hours of training a run, and 65 minutes once for the reference solutions that the three runs share, against 12.55 to 14.08 hours of training a run.

**Against the expectation stated before the run**
- S3 was expected to hold, at about the 25% and 26% flagged before: 27.0%.
- S2 was expected to hold, at about the 0.1% and 0% seen before, against a limit of 1%: it holds at 0.82%, with 8 readings where 9 would still hold and 10 would not.
- S1 was called uncertain, with about two chances in three, and about seven pairs above 10% were expected: there are 10, all flagged.
- R was expected to hold: it holds, in two runs by one hundredth.
- **Part 2 was expected to favour the supervised arm in the median. It did not**: the label-free arm has the smaller median in every reading. The 90th percentile was called uncertain: it favours the label-free arm when that arm is read condensed and the supervised arm when both are read raw.

**What it does not show**
- Everything the pre-specification lists under "What the gate does not show".
- Part 1: nothing about errors that the three runs share; the three missed pairs are of that kind.
- Part 2: nothing about a supervised arm with settings of its own, with fewer labels, or with a reading developed for it.
- Nothing about the measuring code beyond what the section on its defect states.

## Consequences

- The verdict is the one that the stamped code returned on the host: self-check PASS, ranking HOLDS, comparison "label-free closer". The defect of the measuring code is stated beside it, and G-C2.1's verdict document receives an erratum (the owner's decision of 20 November 2026, given to the author in a message that the owner keeps; it is not in the repository).
- Outside this repository a statement of part 1 carries what the pre-specification asks of any wording: that the check needs three training runs, that the threshold was set on T-stubs of this family, the share of pairs flagged, and each run's pairs above 5% and above 10% with how many of them were flagged. It also names the reading and gives the margins.
- A statement of part 2 gives both statistics of both arms and the size as each reading gives it: about two with the label-free arm read condensed and the supervised arm read raw (ratios 2.15 and 1.76), and comparable with both arms read raw, where the supervised arm has the smaller 90th percentile. It gives or points to the medians at each level, and it says that the supervised arm was trained with the label-free arm's settings and was not tuned, what each arm needed, that the supervised arm took less time, and that the wording does not carry to another family, mesh or budget, or to a supervised arm with settings of its own.
- The ratios 84 and 30 are not quoted.
- The next gate that uses the reference code fixes the start of its exact solves.

## Numbers

Generated by `audit/c23_write_verdict.py` from `records/c23/return/`, `records/c23/audit/` and, for the training of the label-free networks, `records/c22/return/`. The error is $\lvert F/F^*(e) - 1\rvert$, the judged error; a signed error is $F/F^*(e) - 1$. A run is an arm and a seed. The third sample has 64 members at seven levels, 448 pairs a run. A signed value below zero that rounds to zero is printed as -0.00%.

### Part 1: the criteria (label-free runs, condensed reading, third sample)

| Criterion | Limit | Value | Holds |
|---|---|---|---|
| S1: pairs that are not flagged with an error above 10% in any run | none | 0 | yes |
| S2: readings above 5% among the readings of the pairs that are not flagged | at most 1% | 8 of 981 (0.82%) | yes |
| S3: pairs flagged | at most 35% | 121 of 448 (27.0%) | yes |
| R: in each run, the probability that a pair above 5% has a larger spread than a pair at or below 5% | at least 0.90 | 0.909, 0.912, 0.949 | HOLDS |

The threshold of the spread is 0.0045. Returned: self-check PASS, ranking HOLDS, identity OK; the part 1 of the final verdict is the one kept before any training member was labelled: True.

| Run | Median | 90th percentile | Largest | Pairs above 5% | Of them flagged | Pairs above 10% | Of them flagged | Largest error of a pair not flagged | Infinite |
|---|---|---|---|---|---|---|---|---|---|
| label-free, seed 5 | 0.794% | 3.747% | 58.8% | 25 | 22 | 8 | 8 | 5.61% | 0 |
| label-free, seed 6 | 0.844% | 3.715% | 103.1% | 26 | 23 | 8 | 8 | 6.10% | 0 |
| label-free, seed 7 | 0.777% | 3.810% | 59.2% | 26 | 24 | 7 | 7 | 6.01% | 0 |

The spread over the 448 pairs: median 0.00189, upper quartile 0.00478, 90th percentile 0.00902, largest 0.2688. The probability that a pair above 10% has a larger spread than a pair at or below 10%: 1.0000, 0.9989, 0.9981 (reported).

**By level**

| Level | Pairs flagged | Pairs above 5% in some run | Of them flagged | Pairs above 10% in some run | Of them flagged | Median spread |
|---|---|---|---|---|---|---|
| 0.5 mm | 2 of 64 | 2 | 2 | 0 | 0 | 0.00038 |
| 1 mm | 1 of 64 | 0 | 0 | 0 | 0 | 0.00047 |
| 2 mm | 5 of 64 | 3 | 1 | 1 | 1 | 0.00050 |
| 3 mm | 21 of 64 | 4 | 4 | 1 | 1 | 0.00334 |
| 4 mm | 27 of 64 | 3 | 3 | 1 | 1 | 0.00367 |
| 6 mm | 24 of 64 | 8 | 7 | 2 | 2 | 0.00344 |
| 8 mm | 41 of 64 | 10 | 10 | 5 | 5 | 0.00660 |

**The pairs above 5% in some run** (signed errors of seeds 5, 6 and 7)

| Member | $t_f$ (mm) | $f_y$ (MPa) | $w$ (mm) | $n$ (mm) | Level | Condensed, seeds 5, 6, 7 | Spread | Flagged |
|---|---|---|---|---|---|---|---|---|
| third_0001 | 8.6 | 263 | 91 | 34 | 2 mm | +5.5%, +5.5%, +5.6% | 0.0008 | no |
| third_0001 | 8.6 | 263 | 91 | 34 | 6 mm | +7.0%, +6.8%, +6.2% | 0.0074 | yes |
| third_0001 | 8.6 | 263 | 91 | 34 | 8 mm | +11.6%, +17.8%, +9.0% | 0.0757 | yes |
| third_0003 | 19.8 | 284 | 85 | 39 | 3 mm | +4.1%, +4.3%, +6.5% | 0.0228 | yes |
| third_0003 | 19.8 | 284 | 85 | 39 | 4 mm | +5.4%, +6.0%, +6.3% | 0.0084 | yes |
| third_0003 | 19.8 | 284 | 85 | 39 | 6 mm | +8.7%, +12.5%, +8.7% | 0.0334 | yes |
| third_0003 | 19.8 | 284 | 85 | 39 | 8 mm | +20.7%, +39.8%, +18.7% | 0.1645 | yes |
| third_0005 | 8.4 | 372 | 94 | 31 | 2 mm | +5.6%, +6.1%, +6.0% | 0.0039 | no |
| third_0005 | 8.4 | 372 | 94 | 31 | 8 mm | +5.1%, +4.1%, +4.6% | 0.0091 | yes |
| third_0011 | 8.2 | 242 | 105 | 29 | 0.5 mm | +8.5%, +6.2%, +10.0% | 0.0121 | yes |
| third_0011 | 8.2 | 242 | 105 | 29 | 2 mm | +9.5%, +7.5%, +11.7% | 0.0364 | yes |
| third_0011 | 8.2 | 242 | 105 | 29 | 3 mm | +12.9%, +10.6%, +19.3% | 0.0741 | yes |
| third_0011 | 8.2 | 242 | 105 | 29 | 4 mm | +24.4%, +18.1%, +24.5% | 0.0497 | yes |
| third_0011 | 8.2 | 242 | 105 | 29 | 6 mm | +46.7%, +48.6%, +32.3% | 0.1083 | yes |
| third_0011 | 8.2 | 242 | 105 | 29 | 8 mm | +58.8%, +103.1%, +59.2% | 0.2688 | yes |
| third_0019 | 14.0 | 250 | 80 | 38 | 6 mm | +4.9%, +6.7%, +6.5% | 0.0159 | yes |
| third_0027 | 19.9 | 255 | 72 | 32 | 8 mm | +4.5%, +5.8%, +5.0% | 0.0113 | yes |
| third_0044 | 13.1 | 246 | 79 | 38 | 6 mm | +5.0%, +5.1%, +5.0% | 0.0011 | no |
| third_0044 | 13.1 | 246 | 79 | 38 | 8 mm | +7.2%, +8.7%, +7.4% | 0.0136 | yes |
| third_0045 | 17.4 | 251 | 92 | 30 | 6 mm | +6.0%, +5.3%, +6.8% | 0.0140 | yes |
| third_0045 | 17.4 | 251 | 92 | 30 | 8 mm | +14.2%, +8.0%, +9.2% | 0.0546 | yes |
| third_0049 | 19.5 | 263 | 77 | 32 | 3 mm | +3.7%, +4.6%, +5.7% | 0.0186 | yes |
| third_0049 | 19.5 | 263 | 77 | 32 | 8 mm | +4.4%, +5.1%, +5.6% | 0.0104 | yes |
| third_0053 | 16.7 | 240 | 75 | 38 | 3 mm | +8.7%, +8.1%, +8.7% | 0.0059 | yes |
| third_0054 | 8.0 | 300 | 99 | 31 | 0.5 mm | +6.6%, +5.1%, +5.0% | 0.0053 | yes |
| third_0054 | 8.0 | 300 | 99 | 31 | 6 mm | +9.1%, +6.4%, +5.1% | 0.0361 | yes |
| third_0054 | 8.0 | 300 | 99 | 31 | 8 mm | +14.6%, +16.4%, +10.0% | 0.0548 | yes |
| third_0058 | 18.3 | 303 | 86 | 25 | 4 mm | +5.8%, +3.2%, +5.0% | 0.0243 | yes |
| third_0058 | 18.3 | 303 | 86 | 25 | 6 mm | +5.4%, +5.4%, +4.7% | 0.0065 | yes |
| third_0058 | 18.3 | 303 | 86 | 25 | 8 mm | +6.9%, +5.9%, +5.1% | 0.0161 | yes |

30 pairs, 3 of them not flagged.

### Part 1 on the other sets, in the raw reading and for the supervised runs (reported, not judged)

| Arm | Reading | Set | Pairs flagged | Pairs not flagged above 10% in some run | Readings not flagged above 5% | S1, S2, S3 | Would read | Ranking probability, seeds 5, 6, 7 | Ranking |
|---|---|---|---|---|---|---|---|---|---|
| label-free | condensed | third sample | 121 of 448 | 0 | 8 of 981 | holds, holds, holds | PASS | 0.909, 0.912, 0.949 | HOLDS |
| label-free | condensed | fresh members of G-C2.2 | 118 of 448 | 0 | 0 of 990 | holds, holds, holds | PASS | 0.956, 0.944, 0.952 | HOLDS |
| label-free | condensed | tested | 6 of 28 | 0 | 0 of 66 | holds, holds, holds | PASS | n/a, n/a, n/a | NOT EVALUABLE |
| label-free | raw | third sample | 212 of 448 | 4 | 31 of 708 | fails, fails, fails | FAIL | 0.849, 0.859, 0.858 | DOES NOT HOLD |
| label-free | raw | fresh members of G-C2.2 | 222 of 448 | 4 | 18 of 678 | fails, fails, fails | FAIL | 0.875, 0.884, 0.888 | DOES NOT HOLD |
| label-free | raw | tested | 15 of 28 | 0 | 2 of 39 | holds, fails, fails | FAIL | 0.771, 0.654, 0.926 | DOES NOT HOLD |
| supervised | condensed | third sample | 317 of 448 | 131 | 393 of 393 | fails, fails, fails | FAIL | n/a, n/a, n/a | NOT EVALUABLE |
| supervised | condensed | fresh members of G-C2.2 | 312 of 448 | 136 | 408 of 408 | fails, fails, fails | FAIL | n/a, n/a, n/a | NOT EVALUABLE |
| supervised | condensed | tested | 16 of 28 | 12 | 36 of 36 | fails, fails, fails | FAIL | n/a, n/a, n/a | NOT EVALUABLE |
| supervised | raw | third sample | 363 of 448 | 0 | 26 of 255 | holds, fails, fails | FAIL | 0.606, 0.596, 0.552 | DOES NOT HOLD |
| supervised | raw | fresh members of G-C2.2 | 362 of 448 | 1 | 11 of 258 | fails, fails, fails | FAIL | 0.584, 0.653, 0.640 | DOES NOT HOLD |
| supervised | raw | tested | 21 of 28 | 0 | 1 of 21 | holds, fails, fails | FAIL | 0.615, 0.413, 0.587 | DOES NOT HOLD |

The first row is the judged one. The threshold was set for the three label-free networks read condensed; the other rows apply it unchanged.

### Part 2: the two statistics of each arm

**Third sample** (448 pairs a run), judged

| Arm | Reading | Median, seeds 5, 6, 7 | Median over the seeds | 90th percentile, seeds 5, 6, 7 | Median over the seeds | Pairs above 10%, seeds 5, 6, 7 | Infinite |
|---|---|---|---|---|---|---|---|
| label-free | condensed | 0.794%, 0.844%, 0.777% | 0.794% | 3.747%, 3.715%, 3.810% | 3.747% | 8, 8, 7 | 0 |
| label-free | raw | 1.442%, 1.358%, 1.276% | 1.358% | 8.790%, 10.191%, 9.636% | 9.636% | 39, 46, 43 | 1 |
| supervised | condensed | 69.522%, 66.935%, 58.747% | 66.935% | 113.599%, 111.924%, 110.429% | 111.924% | 448, 448, 448 | 0 |
| supervised | raw | 1.707%, 1.633%, 1.732% | 1.707% | 6.790%, 6.613%, 5.301% | 6.613% | 26, 20, 10 | 0 |

**Fresh members of G-C2.2** (448 pairs a run), reported

| Arm | Reading | Median, seeds 5, 6, 7 | Median over the seeds | 90th percentile, seeds 5, 6, 7 | Median over the seeds | Pairs above 10%, seeds 5, 6, 7 | Infinite |
|---|---|---|---|---|---|---|---|
| label-free | condensed | 0.828%, 0.797%, 0.782% | 0.797% | 3.664%, 3.766%, 3.656% | 3.664% | 6, 5, 6 | 0 |
| label-free | raw | 1.445%, 1.334%, 1.364% | 1.364% | 10.944%, 10.471%, 10.543% | 10.543% | 47, 48, 48 | 0 |
| supervised | condensed | 73.281%, 72.582%, 65.394% | 72.582% | 121.051%, 120.457%, 118.818% | 120.457% | 448, 448, 448 | 2 |
| supervised | raw | 1.833%, 1.803%, 1.558% | 1.803% | 6.213%, 6.431%, 4.688% | 6.213% | 15, 22, 4 | 0 |

**Tested** (28 pairs a run), reported

| Arm | Reading | Median, seeds 5, 6, 7 | Median over the seeds | 90th percentile, seeds 5, 6, 7 | Median over the seeds | Pairs above 10%, seeds 5, 6, 7 | Infinite |
|---|---|---|---|---|---|---|---|
| label-free | condensed | 0.942%, 0.844%, 0.771% | 0.844% | 1.777%, 1.881%, 1.615% | 1.777% | 0, 0, 0 | 0 |
| label-free | raw | 0.687%, 1.255%, 0.912% | 0.912% | 5.046%, 4.091%, 4.250% | 4.250% | 0, 0, 0 | 0 |
| supervised | condensed | 74.658%, 73.934%, 65.455% | 73.934% | 106.600%, 107.323%, 100.995% | 106.600% | 28, 28, 28 | 0 |
| supervised | raw | 1.539%, 1.372%, 2.165% | 1.539% | 3.990%, 5.037%, 5.055% | 5.037% | 0, 1, 0 | 0 |

**The ratios, supervised over label-free**

| Set | Supervised arm read | Label-free arm read | Ratio of the medians | Ratio of the 90th percentiles | Wording by the rule |
|---|---|---|---|---|---|
| third sample (**judged**) | condensed | condensed | 84.255 | 29.869 | label-free closer |
| third sample (stated beside it) | raw | condensed | 2.149 | 1.765 | label-free closer |
| third sample (reported) | raw | raw | 1.257 | 0.686 | comparable |
| fresh members of G-C2.2 (reported) | condensed | condensed | 91.042 | 32.876 | label-free closer |
| fresh members of G-C2.2 (reported) | raw | raw | 1.322 | 0.589 | mixed |
| tested (reported) | condensed | condensed | 87.592 | 59.973 | label-free closer |
| tested (reported) | raw | raw | 1.687 | 1.185 | label-free closer |

The band of "comparable" is 0.6667 to 1.5, the ends included. Returned: comparison label-free closer; ratios 84.25497316902958 and 29.86937438984068; with the supervised arm read raw 2.1487860799914285 and 1.7648109467915576.

### The median error by level (third sample, 64 members a level)

| Arm | Reading | Run | 0.5 mm | 1 mm | 2 mm | 3 mm | 4 mm | 6 mm | 8 mm |
|---|---|---|---|---|---|---|---|---|---|
| label-free | condensed | seed 5 | 0.42% | 0.38% | 0.50% | 1.26% | 1.18% | 0.85% | 1.91% |
| label-free | condensed | seed 6 | 0.59% | 0.42% | 0.55% | 1.14% | 1.20% | 1.08% | 1.78% |
| label-free | condensed | seed 7 | 0.47% | 0.44% | 0.46% | 1.06% | 1.11% | 1.01% | 1.76% |
| label-free | condensed | **median of the runs** | 0.47% | 0.42% | 0.50% | 1.14% | 1.18% | 1.01% | 1.78% |
| label-free | raw | seed 5 | 0.75% | 0.67% | 1.04% | 1.77% | 1.71% | 1.58% | 7.76% |
| label-free | raw | seed 6 | 0.95% | 0.84% | 0.94% | 1.59% | 1.48% | 1.76% | 8.15% |
| label-free | raw | seed 7 | 0.72% | 0.93% | 0.88% | 1.92% | 1.19% | 1.63% | 7.28% |
| label-free | raw | **median of the runs** | 0.75% | 0.84% | 0.94% | 1.77% | 1.48% | 1.63% | 7.76% |
| supervised | condensed | seed 5 | 71.33% | 74.69% | 70.71% | 52.80% | 37.07% | 71.62% | 101.55% |
| supervised | condensed | seed 6 | 73.83% | 68.90% | 62.79% | 52.20% | 35.99% | 71.00% | 99.79% |
| supervised | condensed | seed 7 | 64.35% | 61.33% | 47.19% | 45.46% | 36.96% | 71.85% | 98.42% |
| supervised | condensed | **median of the runs** | 71.33% | 68.90% | 62.79% | 52.20% | 36.96% | 71.62% | 99.79% |
| supervised | raw | seed 5 | 4.31% | 2.27% | 1.87% | 1.18% | 1.36% | 1.26% | 1.09% |
| supervised | raw | seed 6 | 4.59% | 2.03% | 2.23% | 1.47% | 1.43% | 1.01% | 1.44% |
| supervised | raw | seed 7 | 3.02% | 1.97% | 1.68% | 1.79% | 1.41% | 1.47% | 1.18% |
| supervised | raw | **median of the runs** | 4.31% | 2.03% | 1.87% | 1.47% | 1.41% | 1.26% | 1.18% |

**90th percentile of the error by level** (from the per-pair rows)

| Arm | Reading | Run | 0.5 mm | 1 mm | 2 mm | 3 mm | 4 mm | 6 mm | 8 mm |
|---|---|---|---|---|---|---|---|---|---|
| label-free | condensed | seed 5 | 1.15% | 1.29% | 2.40% | 3.32% | 3.76% | 5.00% | 6.36% |
| label-free | condensed | seed 6 | 1.07% | 1.00% | 1.66% | 3.70% | 3.34% | 5.21% | 5.88% |
| label-free | condensed | seed 7 | 1.22% | 1.39% | 2.33% | 3.65% | 4.17% | 4.88% | 5.42% |
| label-free | raw | seed 5 | 2.85% | 2.14% | 4.23% | 5.12% | 5.40% | 22.21% | 45.62% |
| label-free | raw | seed 6 | 3.70% | 1.98% | 4.28% | 5.61% | 5.44% | 18.73% | 43.89% |
| label-free | raw | seed 7 | 2.54% | 2.17% | 3.77% | 5.33% | 6.58% | 20.76% | 44.34% |
| supervised | condensed | seed 5 | 92.26% | 90.44% | 92.15% | 80.91% | 71.10% | 130.43% | 192.47% |
| supervised | condensed | seed 6 | 93.45% | 90.42% | 87.02% | 77.58% | 68.50% | 130.98% | 194.67% |
| supervised | condensed | seed 7 | 83.02% | 83.47% | 70.87% | 71.04% | 68.39% | 131.56% | 195.66% |
| supervised | raw | seed 5 | 17.76% | 6.45% | 6.36% | 4.78% | 3.30% | 4.04% | 7.79% |
| supervised | raw | seed 6 | 13.07% | 4.98% | 5.78% | 4.54% | 3.35% | 3.40% | 4.21% |
| supervised | raw | seed 7 | 8.96% | 4.30% | 4.22% | 5.14% | 3.62% | 4.17% | 6.77% |

**Median signed error by level**

| Arm | Reading | Run | 0.5 mm | 1 mm | 2 mm | 3 mm | 4 mm | 6 mm | 8 mm |
|---|---|---|---|---|---|---|---|---|---|
| label-free | condensed | seed 5 | +0.42% | +0.38% | +0.46% | +0.50% | +1.18% | +0.85% | +1.91% |
| label-free | condensed | seed 6 | +0.57% | +0.42% | +0.52% | +0.86% | +1.20% | +1.05% | +1.78% |
| label-free | condensed | seed 7 | +0.45% | +0.44% | +0.42% | +0.63% | +1.11% | +1.01% | +1.76% |
| label-free | raw | seed 5 | -0.30% | -0.03% | +0.30% | +0.59% | +1.49% | +0.98% | +7.76% |
| label-free | raw | seed 6 | +0.06% | +0.30% | +0.37% | +0.91% | +1.31% | +0.88% | +8.15% |
| label-free | raw | seed 7 | +0.00% | +0.26% | +0.51% | +0.55% | +1.19% | +0.64% | +7.28% |
| supervised | condensed | seed 5 | +71.33% | +74.69% | +70.71% | +52.80% | +37.07% | +71.62% | +101.55% |
| supervised | condensed | seed 6 | +73.83% | +68.90% | +62.79% | +52.20% | +35.99% | +71.00% | +99.79% |
| supervised | condensed | seed 7 | +64.35% | +61.33% | +47.19% | +45.46% | +36.96% | +71.85% | +98.42% |
| supervised | raw | seed 5 | +3.55% | -0.28% | +0.35% | -0.63% | +0.53% | -0.08% | +0.25% |
| supervised | raw | seed 6 | +4.18% | -1.02% | +0.87% | -0.50% | +0.78% | +0.18% | +0.68% |
| supervised | raw | seed 7 | -1.30% | -0.32% | -0.58% | -1.17% | +0.78% | -0.37% | +0.55% |

### The identity of the label-free networks (fresh members of G-C2.2)

| Reading | Seed | Median here | In the configuration | 90th percentile here | In the configuration |
|---|---|---|---|---|---|
| condensed | 5 | 0.008284227273415379 | 0.008284227273415379 | 0.03663936677608451 | 0.03663936677608451 |
| condensed | 6 | 0.007972382816471169 | 0.007972382816471169 | 0.03766036133923352 | 0.03766036133923352 |
| condensed | 7 | 0.007818943658160049 | 0.007818943658160049 | 0.036562399536675616 | 0.036562399536675616 |
| raw | 5 | 0.014451064308929451 | 0.014451064308929451 | 0.10944432481632067 | 0.10944432481632067 |
| raw | 6 | 0.013340824465134682 | 0.013340824465134682 | 0.10470516659288157 | 0.10470516659288157 |
| raw | 7 | 0.013638353687949134 | 0.013638353687949134 | 0.10542708497194714 | 0.10542708497194714 |

Largest difference 0.0, against a tolerance of 0.0001.

### What each arm needed

| Run | Reference solutions for training | Hours of training | Steps | Peak GPU memory (GiB) | Seconds of prediction here |
|---|---|---|---|---|---|
| label-free, seed 5 (trained in G-C2.2) | 0 | 14.08 | 102,400 | 3.52 | 225 |
| label-free, seed 6 (trained in G-C2.2) | 0 | 12.70 | 102,400 | 3.52 | 483 |
| label-free, seed 7 (trained in G-C2.2) | 0 | 12.55 | 102,400 | 3.52 | 641 |
| supervised, seed 5 | 4,096 | 4.85 | 102,400 | 0.46 | not recorded |
| supervised, seed 6 | 4,096 | 4.96 | 102,400 | 0.46 | not recorded |
| supervised, seed 7 | 4,096 | 4.86 | 102,400 | 0.46 | not recorded |

The 4,096 reference solutions of the 512 training members, which the three supervised runs share, took 60,927 seconds summed over the worker processes (16.92 processor hours).

### The amplitudes of the condensed reading

The amplitude is limited to 0.5 to 3.0. The energies are those of the training energy in float32, of the raw and of the condensed field; the fall is relative to the raw field's energy.

| Run | Set | Fields | Smallest | Median | Largest | At the lower limit | At the upper limit | Tolerance not met | Median fall of the energy |
|---|---|---|---|---|---|---|---|---|---|
| label-free, seed 5 | third sample | 448 | 0.776 | 1.0000 | 1.210 | 0 | 0 | 12 | 0.0024% |
| label-free, seed 5 | fresh members of G-C2.2 | 448 | 0.811 | 1.0018 | 1.187 | 0 | 0 | 5 | 0.0029% |
| label-free, seed 5 | tested | 28 | 0.933 | 0.9916 | 1.025 | 0 | 0 | 0 | 0.0049% |
| label-free, seed 6 | third sample | 448 | 0.781 | 1.0001 | 1.175 | 0 | 0 | 14 | 0.0024% |
| label-free, seed 6 | fresh members of G-C2.2 | 448 | 0.802 | 1.0004 | 1.180 | 0 | 0 | 9 | 0.0030% |
| label-free, seed 6 | tested | 28 | 0.945 | 0.9926 | 1.022 | 0 | 0 | 0 | 0.0046% |
| label-free, seed 7 | third sample | 448 | 0.771 | 1.0015 | 1.206 | 0 | 0 | 12 | 0.0025% |
| label-free, seed 7 | fresh members of G-C2.2 | 448 | 0.807 | 1.0012 | 1.174 | 0 | 0 | 11 | 0.0031% |
| label-free, seed 7 | tested | 28 | 0.931 | 0.9930 | 1.026 | 0 | 0 | 0 | 0.0061% |
| supervised, seed 5 | third sample | 448 | 0.500 | 0.5000 | 0.637 | 378 | 0 | 2 | 12.8785% |
| supervised, seed 5 | fresh members of G-C2.2 | 448 | 0.500 | 0.5000 | 0.645 | 388 | 0 | 3 | 13.9626% |
| supervised, seed 5 | tested | 28 | 0.500 | 0.5000 | 0.527 | 27 | 0 | 0 | 16.8466% |
| supervised, seed 6 | third sample | 448 | 0.500 | 0.5000 | 0.707 | 344 | 0 | 5 | 11.1516% |
| supervised, seed 6 | fresh members of G-C2.2 | 448 | 0.500 | 0.5000 | 0.718 | 363 | 0 | 3 | 12.9926% |
| supervised, seed 6 | tested | 28 | 0.500 | 0.5000 | 0.633 | 23 | 0 | 1 | 11.3786% |
| supervised, seed 7 | third sample | 448 | 0.500 | 0.5000 | 0.724 | 298 | 0 | 5 | 10.6164% |
| supervised, seed 7 | fresh members of G-C2.2 | 448 | 0.500 | 0.5000 | 0.727 | 320 | 0 | 3 | 11.0543% |
| supervised, seed 7 | tested | 28 | 0.500 | 0.5000 | 0.658 | 20 | 0 | 0 | 12.1410% |

### The supervised runs: training

| Run | Loss, first epoch | Mean loss, epochs 191 to 200 | Largest epoch loss | Capped steps | Bursts | Hours | Seconds a step: least, median, most | Resumed from epoch | Trained on the labels with ledger hash |
|---|---|---|---|---|---|---|---|---|---|
| supervised, seed 5 | 9.247e-03 | 1.122e-05 | 9.247e-03 | 9,648 | 3,618 | 4.85 | 0.161, 0.171, 0.173 | none | `f9e6eaca263f` |
| supervised, seed 6 | 9.620e-03 | 1.155e-05 | 9.620e-03 | 9,846 | 3,756 | 4.96 | 0.162, 0.173, 0.184 | none | `f9e6eaca263f` |
| supervised, seed 7 | 9.407e-03 | 1.083e-05 | 9.407e-03 | 10,352 | 4,083 | 4.86 | 0.168, 0.170, 0.186 | none | `f9e6eaca263f` |

### The other readings (medians over the pairs of a set; reported, not judged)

**Third sample**

| Arm | Reading | Seed | Force at the same $D$, absolute | Force at the same $D$, signed | End displacement, signed | Stress reading of the force, signed | Energy gap | Certified bound on the force error | Bolt force, signed | Displacement, relative $L^2$ | Contact IoU | Plastic IoU | Within the bound |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| label-free | condensed | 5 | 0.363% | +0.259% | -0.688% | +0.161% | 0.161% | 5.099% | +0.000% | 1.773% | 0.982 | 0.854 | 100.0% |
| label-free | condensed | 6 | 0.400% | +0.247% | -0.743% | +0.345% | 0.154% | 5.101% | -0.000% | 1.983% | 0.982 | 0.867 | 100.0% |
| label-free | condensed | 7 | 0.390% | +0.246% | -0.725% | +0.518% | 0.147% | 4.803% | -0.001% | 1.877% | 0.980 | 0.852 | 100.0% |
| label-free | raw | 5 | 0.536% | +0.182% | -0.693% | +0.583% | 0.164% | 5.209% | +0.000% | 2.623% | 0.982 | 0.854 | 100.0% |
| label-free | raw | 6 | 0.463% | +0.184% | -0.903% | +0.657% | 0.167% | 5.138% | -0.000% | 2.510% | 0.983 | 0.865 | 100.0% |
| label-free | raw | 7 | 0.455% | +0.159% | -0.731% | +0.639% | 0.151% | 4.882% | -0.000% | 2.406% | 0.980 | 0.853 | 100.0% |
| supervised | condensed | 5 | 15.198% | +15.198% | -48.688% | -35.794% | 13.712% | 46.162% | -4.459% | 49.021% | 0.823 | 0.545 | 100.0% |
| supervised | condensed | 6 | 14.646% | +14.646% | -48.482% | -37.950% | 12.397% | 43.400% | -4.453% | 48.442% | 0.798 | 0.535 | 100.0% |
| supervised | condensed | 7 | 14.409% | +14.409% | -47.423% | -35.038% | 11.165% | 41.312% | -4.179% | 47.292% | 0.877 | 0.545 | 100.0% |
| supervised | raw | 5 | 0.674% | +0.060% | -0.176% | +11.171% | 31.203% | 69.727% | -0.001% | 3.563% | 0.759 | 0.357 | 100.0% |
| supervised | raw | 6 | 0.657% | +0.200% | -0.512% | +4.777% | 27.147% | 66.121% | -0.002% | 3.697% | 0.714 | 0.349 | 100.0% |
| supervised | raw | 7 | 0.585% | -0.079% | +0.234% | +6.946% | 24.544% | 60.630% | -0.001% | 3.474% | 0.832 | 0.385 | 100.0% |

**Fresh members of G-C2.2**

| Arm | Reading | Seed | Force at the same $D$, absolute | Force at the same $D$, signed | End displacement, signed | Stress reading of the force, signed | Energy gap | Certified bound on the force error | Bolt force, signed | Displacement, relative $L^2$ | Contact IoU | Plastic IoU | Within the bound |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| label-free | condensed | 5 | 0.435% | +0.316% | -0.714% | +0.157% | 0.218% | 6.159% | +0.000% | 1.514% | 0.971 | 0.858 | 100.0% |
| label-free | condensed | 6 | 0.368% | +0.283% | -0.713% | +0.200% | 0.205% | 5.914% | +0.000% | 1.617% | 0.972 | 0.856 | 100.0% |
| label-free | condensed | 7 | 0.351% | +0.320% | -0.691% | +0.262% | 0.194% | 5.673% | +0.001% | 1.539% | 0.973 | 0.860 | 100.0% |
| label-free | raw | 5 | 0.603% | +0.223% | -0.831% | +0.396% | 0.222% | 6.209% | +0.000% | 2.492% | 0.971 | 0.859 | 100.0% |
| label-free | raw | 6 | 0.549% | +0.224% | -0.843% | +0.437% | 0.211% | 6.020% | +0.000% | 2.336% | 0.972 | 0.860 | 100.0% |
| label-free | raw | 7 | 0.557% | +0.228% | -0.945% | +0.539% | 0.197% | 5.712% | +0.001% | 2.340% | 0.974 | 0.862 | 100.0% |
| supervised | condensed | 5 | 17.411% | +17.411% | -48.453% | -37.135% | 16.535% | 51.433% | -3.487% | 48.567% | 0.856 | 0.537 | 100.0% |
| supervised | condensed | 6 | 17.685% | +17.685% | -48.437% | -40.737% | 14.922% | 50.132% | -4.121% | 48.473% | 0.790 | 0.517 | 100.0% |
| supervised | condensed | 7 | 17.321% | +17.321% | -47.448% | -38.786% | 13.462% | 46.729% | -3.573% | 47.018% | 0.889 | 0.548 | 100.0% |
| supervised | raw | 5 | 0.820% | -0.057% | +0.198% | +10.585% | 36.810% | 77.310% | +0.000% | 3.353% | 0.788 | 0.368 | 100.0% |
| supervised | raw | 6 | 0.771% | -0.077% | +0.129% | +1.590% | 33.199% | 73.261% | -0.002% | 3.388% | 0.727 | 0.331 | 100.0% |
| supervised | raw | 7 | 0.719% | -0.167% | +0.441% | +2.631% | 28.488% | 67.791% | +0.000% | 3.056% | 0.848 | 0.386 | 100.0% |

### The other readings by level, third sample (medians over the 64 members at each level; reported, not judged)

| Arm | Reading | Seed | $D$ (mm) | Force at the same $D$, signed | Absolute | Certified bound | Within the bound | End displacement, signed | Stress reading of the force, signed | Energy gap | Contact IoU | Plastic IoU | Bolt force, signed | Displacement, relative $L^2$ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| label-free | condensed | 5 | 0.5 | +0.05% | 0.05% | 3.27% | 64 of 64 | -0.44% | -0.32% | 0.067% | 0.969 | 1.000 | +0.21% | 1.03% |
| label-free | condensed | 5 | 1 | +0.05% | 0.05% | 2.74% | 64 of 64 | -0.38% | -0.39% | 0.056% | 0.982 | 1.000 | +0.08% | 0.96% |
| label-free | condensed | 5 | 2 | +0.06% | 0.08% | 2.92% | 64 of 64 | -0.48% | +0.56% | 0.071% | 0.964 | 0.802 | -0.01% | 1.32% |
| label-free | condensed | 5 | 3 | +0.22% | 0.59% | 4.34% | 64 of 64 | -0.86% | -0.20% | 0.140% | 0.974 | 0.821 | +0.00% | 3.49% |
| label-free | condensed | 5 | 4 | +1.02% | 1.02% | 7.49% | 64 of 64 | -1.64% | +0.08% | 0.269% | 1.000 | 0.794 | -0.00% | 2.74% |
| label-free | condensed | 5 | 6 | +0.75% | 0.75% | 10.32% | 64 of 64 | -0.78% | +1.68% | 0.375% | 1.000 | 0.810 | +0.01% | 2.12% |
| label-free | condensed | 5 | 8 | +1.78% | 1.78% | 18.65% | 64 of 64 | -1.05% | +6.74% | 0.904% | 1.000 | 0.760 | -0.01% | 4.79% |
| label-free | condensed | 6 | 0.5 | +0.06% | 0.07% | 3.26% | 64 of 64 | -0.57% | -0.10% | 0.065% | 0.976 | 1.000 | +0.04% | 1.17% |
| label-free | condensed | 6 | 1 | +0.06% | 0.06% | 2.68% | 64 of 64 | -0.43% | -0.13% | 0.055% | 0.970 | 1.000 | +0.04% | 1.04% |
| label-free | condensed | 6 | 2 | +0.08% | 0.09% | 2.91% | 64 of 64 | -0.48% | -0.04% | 0.068% | 0.970 | 0.832 | -0.29% | 1.23% |
| label-free | condensed | 6 | 3 | +0.60% | 0.63% | 3.91% | 64 of 64 | -1.18% | +1.38% | 0.113% | 1.000 | 0.826 | +0.00% | 3.74% |
| label-free | condensed | 6 | 4 | +0.94% | 0.94% | 6.74% | 64 of 64 | -1.70% | +0.46% | 0.250% | 1.000 | 0.797 | -0.00% | 2.77% |
| label-free | condensed | 6 | 6 | +0.90% | 0.90% | 11.14% | 64 of 64 | -0.78% | +1.07% | 0.426% | 1.000 | 0.775 | -0.00% | 2.14% |
| label-free | condensed | 6 | 8 | +1.67% | 1.67% | 17.63% | 64 of 64 | -0.88% | +5.90% | 0.856% | 1.000 | 0.779 | -0.01% | 4.55% |
| label-free | condensed | 7 | 0.5 | +0.06% | 0.06% | 2.86% | 64 of 64 | -0.47% | -0.07% | 0.054% | 0.975 | 1.000 | +0.10% | 1.13% |
| label-free | condensed | 7 | 1 | +0.07% | 0.07% | 2.59% | 64 of 64 | -0.44% | -0.08% | 0.050% | 0.970 | 1.000 | -0.05% | 1.02% |
| label-free | condensed | 7 | 2 | +0.06% | 0.07% | 2.71% | 64 of 64 | -0.45% | +0.09% | 0.061% | 0.964 | 0.796 | -0.16% | 1.17% |
| label-free | condensed | 7 | 3 | +0.34% | 0.63% | 4.07% | 64 of 64 | -1.17% | +0.74% | 0.118% | 0.979 | 0.829 | +0.00% | 3.20% |
| label-free | condensed | 7 | 4 | +0.88% | 0.88% | 6.89% | 64 of 64 | -1.48% | +1.48% | 0.246% | 1.000 | 0.800 | -0.00% | 2.57% |
| label-free | condensed | 7 | 6 | +0.89% | 0.89% | 10.87% | 64 of 64 | -0.78% | +1.50% | 0.390% | 1.000 | 0.797 | -0.00% | 2.01% |
| label-free | condensed | 7 | 8 | +1.61% | 1.61% | 16.97% | 64 of 64 | -0.93% | +3.24% | 0.722% | 1.000 | 0.764 | -0.01% | 4.04% |
| label-free | raw | 5 | 0.5 | -0.04% | 0.09% | 3.30% | 64 of 64 | +0.32% | +0.38% | 0.068% | 0.969 | 1.000 | +0.23% | 1.23% |
| label-free | raw | 5 | 1 | -0.00% | 0.10% | 2.74% | 64 of 64 | +0.04% | +0.11% | 0.058% | 0.982 | 1.000 | +0.12% | 1.10% |
| label-free | raw | 5 | 2 | +0.04% | 0.21% | 2.97% | 64 of 64 | -0.33% | +0.72% | 0.074% | 0.964 | 0.810 | +0.01% | 1.67% |
| label-free | raw | 5 | 3 | +0.22% | 0.88% | 4.41% | 64 of 64 | -1.09% | +0.56% | 0.143% | 0.979 | 0.804 | +0.00% | 4.68% |
| label-free | raw | 5 | 4 | +1.07% | 1.26% | 7.50% | 64 of 64 | -2.03% | -0.71% | 0.271% | 1.000 | 0.804 | -0.00% | 3.73% |
| label-free | raw | 5 | 6 | +0.82% | 1.42% | 10.33% | 64 of 64 | -0.92% | +0.95% | 0.393% | 1.000 | 0.817 | +0.01% | 3.42% |
| label-free | raw | 5 | 8 | +7.05% | 7.05% | 19.72% | 64 of 64 | -3.96% | +4.85% | 0.996% | 1.000 | 0.772 | -0.02% | 6.96% |
| label-free | raw | 6 | 0.5 | +0.00% | 0.11% | 3.29% | 64 of 64 | -0.03% | +0.04% | 0.067% | 0.976 | 1.000 | +0.08% | 1.44% |
| label-free | raw | 6 | 1 | +0.04% | 0.11% | 2.69% | 64 of 64 | -0.29% | +0.39% | 0.056% | 0.970 | 1.000 | -0.01% | 1.42% |
| label-free | raw | 6 | 2 | +0.07% | 0.16% | 2.95% | 64 of 64 | -0.44% | +0.03% | 0.069% | 0.967 | 0.818 | +0.01% | 1.48% |
| label-free | raw | 6 | 3 | +0.41% | 0.87% | 3.98% | 64 of 64 | -1.82% | +1.50% | 0.115% | 0.993 | 0.821 | +0.00% | 4.36% |
| label-free | raw | 6 | 4 | +1.03% | 1.13% | 6.82% | 64 of 64 | -1.73% | +0.77% | 0.252% | 1.000 | 0.811 | -0.00% | 3.26% |
| label-free | raw | 6 | 6 | +0.74% | 1.49% | 11.16% | 64 of 64 | -0.67% | +2.17% | 0.432% | 1.000 | 0.777 | +0.01% | 3.57% |
| label-free | raw | 6 | 8 | +7.36% | 7.36% | 20.15% | 64 of 64 | -4.76% | +3.96% | 0.997% | 1.000 | 0.788 | -0.02% | 8.87% |
| label-free | raw | 7 | 0.5 | +0.00% | 0.10% | 2.95% | 64 of 64 | -0.01% | +0.25% | 0.056% | 0.973 | 1.000 | +0.12% | 1.37% |
| label-free | raw | 7 | 1 | +0.04% | 0.12% | 2.61% | 64 of 64 | -0.28% | +0.49% | 0.051% | 0.970 | 1.000 | -0.10% | 1.46% |
| label-free | raw | 7 | 2 | +0.08% | 0.17% | 2.75% | 64 of 64 | -0.57% | -0.08% | 0.065% | 0.964 | 0.807 | -0.02% | 1.32% |
| label-free | raw | 7 | 3 | +0.29% | 0.91% | 4.13% | 64 of 64 | -0.95% | +0.64% | 0.121% | 0.977 | 0.825 | +0.00% | 4.73% |
| label-free | raw | 7 | 4 | +0.91% | 0.91% | 6.95% | 64 of 64 | -2.02% | +1.13% | 0.251% | 1.000 | 0.804 | -0.00% | 3.29% |
| label-free | raw | 7 | 6 | +0.61% | 1.51% | 11.07% | 64 of 64 | -0.64% | +1.45% | 0.407% | 1.000 | 0.802 | +0.01% | 2.88% |
| label-free | raw | 7 | 8 | +6.75% | 6.75% | 18.82% | 64 of 64 | -4.46% | +2.09% | 0.905% | 1.000 | 0.787 | -0.01% | 8.43% |
| supervised | condensed | 5 | 0.5 | +5.39% | 5.39% | 30.26% | 64 of 64 | -42.58% | -31.60% | 5.689% | 0.827 | 1.000 | -2.40% | 43.49% |
| supervised | condensed | 5 | 1 | +6.09% | 6.09% | 27.43% | 64 of 64 | -44.69% | -36.23% | 5.775% | 0.838 | 1.000 | -6.03% | 46.05% |
| supervised | condensed | 5 | 2 | +7.13% | 7.13% | 28.40% | 64 of 64 | -46.81% | -36.78% | 6.606% | 0.872 | 0.113 | -20.54% | 47.90% |
| supervised | condensed | 5 | 3 | +12.33% | 12.33% | 38.03% | 64 of 64 | -48.47% | -40.69% | 10.464% | 0.847 | 0.401 | -3.97% | 48.36% |
| supervised | condensed | 5 | 4 | +28.52% | 28.52% | 63.10% | 64 of 64 | -50.06% | -44.37% | 18.795% | 0.646 | 0.503 | -0.33% | 50.35% |
| supervised | condensed | 5 | 6 | +59.15% | 59.15% | 106.42% | 64 of 64 | -49.82% | -29.37% | 38.216% | 0.707 | 0.547 | -4.58% | 49.98% |
| supervised | condensed | 5 | 8 | +88.28% | 88.28% | 148.68% | 64 of 64 | -49.92% | -19.61% | 55.341% | 0.727 | 0.612 | -3.66% | 50.06% |
| supervised | condensed | 6 | 0.5 | +5.14% | 5.14% | 31.16% | 64 of 64 | -43.23% | -39.49% | 6.111% | 0.707 | 1.000 | -3.48% | 45.52% |
| supervised | condensed | 6 | 1 | +5.99% | 5.99% | 26.24% | 64 of 64 | -43.75% | -39.15% | 5.366% | 0.888 | 1.000 | -6.35% | 45.14% |
| supervised | condensed | 6 | 2 | +6.10% | 6.10% | 26.46% | 64 of 64 | -41.71% | -39.01% | 5.882% | 0.891 | 0.072 | -18.58% | 43.09% |
| supervised | condensed | 6 | 3 | +11.85% | 11.85% | 34.07% | 64 of 64 | -48.02% | -41.28% | 8.471% | 0.867 | 0.378 | -8.30% | 48.81% |
| supervised | condensed | 6 | 4 | +29.05% | 29.05% | 59.47% | 64 of 64 | -50.29% | -41.28% | 18.053% | 0.829 | 0.533 | -0.27% | 50.42% |
| supervised | condensed | 6 | 6 | +58.84% | 58.84% | 112.22% | 64 of 64 | -49.90% | -31.70% | 42.913% | 0.481 | 0.528 | -4.80% | 49.97% |
| supervised | condensed | 6 | 8 | +88.79% | 88.79% | 155.88% | 64 of 64 | -50.04% | -19.74% | 60.352% | 0.748 | 0.600 | -3.62% | 50.03% |
| supervised | condensed | 7 | 0.5 | +4.94% | 4.94% | 27.78% | 64 of 64 | -40.37% | -36.46% | 4.909% | 0.874 | 1.000 | -2.47% | 42.26% |
| supervised | condensed | 7 | 1 | +5.34% | 5.34% | 24.50% | 64 of 64 | -39.93% | -37.06% | 4.775% | 0.896 | 1.000 | -5.20% | 41.10% |
| supervised | condensed | 7 | 2 | +5.20% | 5.20% | 24.66% | 64 of 64 | -34.62% | -31.71% | 4.991% | 0.884 | 0.218 | -14.21% | 35.67% |
| supervised | condensed | 7 | 3 | +11.63% | 11.63% | 35.15% | 64 of 64 | -47.17% | -38.14% | 9.035% | 0.874 | 0.491 | -7.81% | 47.36% |
| supervised | condensed | 7 | 4 | +28.88% | 28.88% | 61.58% | 64 of 64 | -50.15% | -34.60% | 18.751% | 0.864 | 0.495 | -0.36% | 50.58% |
| supervised | condensed | 7 | 6 | +59.10% | 59.10% | 107.01% | 64 of 64 | -49.69% | -26.89% | 37.550% | 0.739 | 0.523 | -4.96% | 49.94% |
| supervised | condensed | 7 | 8 | +86.41% | 86.41% | 149.31% | 64 of 64 | -50.00% | -25.28% | 56.111% | 0.879 | 0.592 | -3.55% | 49.83% |
| supervised | raw | 5 | 0.5 | +0.42% | 0.65% | 40.62% | 64 of 64 | -3.19% | +11.27% | 9.902% | 0.808 | 1.000 | -1.40% | 6.73% |
| supervised | raw | 5 | 1 | -0.04% | 0.34% | 38.71% | 64 of 64 | +0.31% | +12.20% | 11.872% | 0.830 | 0.000 | +0.21% | 4.22% |
| supervised | raw | 5 | 2 | +0.07% | 0.40% | 39.79% | 64 of 64 | -0.38% | +11.62% | 13.567% | 0.839 | 0.071 | -0.63% | 3.66% |
| supervised | raw | 5 | 3 | -0.32% | 0.78% | 53.62% | 64 of 64 | +1.12% | +4.60% | 20.738% | 0.617 | 0.316 | +0.00% | 4.20% |
| supervised | raw | 5 | 4 | +0.43% | 1.17% | 94.77% | 64 of 64 | -0.88% | +1.99% | 48.876% | 0.409 | 0.346 | -0.01% | 2.83% |
| supervised | raw | 5 | 6 | -0.08% | 1.11% | 160.13% | 64 of 64 | +0.05% | +18.07% | 86.804% | 0.568 | 0.462 | +0.00% | 2.17% |
| supervised | raw | 5 | 8 | +0.23% | 1.04% | 222.57% | 64 of 64 | -0.17% | +34.64% | 131.347% | 0.712 | 0.548 | -0.00% | 2.50% |
| supervised | raw | 6 | 0.5 | +0.53% | 0.61% | 41.80% | 64 of 64 | -3.86% | -1.07% | 11.112% | 0.652 | 1.000 | -3.11% | 8.18% |
| supervised | raw | 6 | 1 | -0.20% | 0.32% | 35.57% | 64 of 64 | +1.03% | +5.27% | 9.717% | 0.864 | 0.000 | +2.38% | 3.84% |
| supervised | raw | 6 | 2 | +0.16% | 0.44% | 35.41% | 64 of 64 | -0.81% | +0.18% | 10.337% | 0.880 | 0.059 | +0.00% | 3.36% |
| supervised | raw | 6 | 3 | -0.20% | 0.74% | 48.83% | 64 of 64 | +1.23% | +0.72% | 18.014% | 0.786 | 0.319 | +0.00% | 4.31% |
| supervised | raw | 6 | 4 | +0.62% | 1.13% | 90.68% | 64 of 64 | -1.21% | +7.23% | 43.685% | 0.713 | 0.343 | -0.00% | 2.82% |
| supervised | raw | 6 | 6 | +0.16% | 0.90% | 176.86% | 64 of 64 | -0.13% | +18.71% | 103.431% | 0.010 | 0.443 | -0.01% | 2.12% |
| supervised | raw | 6 | 8 | +0.64% | 1.35% | 243.73% | 64 of 64 | -0.31% | +30.20% | 149.199% | 0.444 | 0.538 | +0.00% | 2.41% |
| supervised | raw | 7 | 0.5 | -0.13% | 0.38% | 36.63% | 64 of 64 | +1.28% | +5.55% | 8.856% | 0.855 | 1.000 | -2.26% | 5.35% |
| supervised | raw | 7 | 1 | -0.05% | 0.29% | 31.96% | 64 of 64 | +0.34% | +3.43% | 8.162% | 0.901 | 0.000 | +1.15% | 3.34% |
| supervised | raw | 7 | 2 | -0.09% | 0.34% | 30.37% | 64 of 64 | +0.62% | +3.92% | 7.421% | 0.874 | 0.090 | +0.91% | 3.44% |
| supervised | raw | 7 | 3 | -0.63% | 1.02% | 48.41% | 64 of 64 | +2.19% | +5.06% | 18.161% | 0.752 | 0.359 | +0.00% | 5.51% |
| supervised | raw | 7 | 4 | +0.64% | 1.17% | 88.72% | 64 of 64 | -1.22% | +19.33% | 39.689% | 0.636 | 0.369 | -0.00% | 3.64% |
| supervised | raw | 7 | 6 | -0.32% | 1.36% | 163.69% | 64 of 64 | +0.25% | +25.49% | 93.536% | 0.536 | 0.445 | -0.01% | 2.15% |
| supervised | raw | 7 | 8 | +0.50% | 1.12% | 229.05% | 64 of 64 | -0.28% | +19.73% | 130.249% | 0.789 | 0.521 | -0.00% | 2.42% |

### The rows with an infinite error

Of the 11,088 returned rows, 3 have an infinite error and 0 a field that the reference code could not evaluate. No member is without metrics in a run: True.

| Arm | Reading | Seed | Set | Member | Level | Note written by the evaluation |
|---|---|---|---|---|---|---|
| label-free | raw | 6 | third sample | third_0034 | 0.5 mm | RuntimeError: bubble condensation did not converge |
| supervised | condensed | 6 | fresh members of G-C2.2 | eval_0063 | 0.5 mm | RuntimeError: bubble condensation did not converge |
| supervised | condensed | 6 | fresh members of G-C2.2 | eval_0063 | 1 mm | RuntimeError: bubble condensation did not converge |

### The four tested members (reported, not judged): signed error

| Member | Arm | Reading | 0.5 mm | 1 mm | 2 mm | 3 mm | 4 mm | 6 mm | 8 mm |
|---|---|---|---|---|---|---|---|---|---|
| BJ_T1_preloaded | label-free | condensed | +0.5%, +0.3%, +0.3% | +0.2%, +0.2%, +0.3% | +0.2%, +0.3%, +0.1% | +0.7%, +1.1%, +0.5% | +0.8%, +0.8%, +0.8% | +1.5%, +1.8%, +1.5% | +1.7%, +2.3%, +1.7% |
| BJ_T1_preloaded | label-free | raw | +0.3%, +0.3%, +0.1% | -0.2%, +0.1%, +0.3% | +0.4%, +1.5%, +0.7% | +0.2%, +1.2%, +0.3% | +0.6%, +0.5%, -0.4% | -0.4%, -0.3%, -1.0% | +2.8%, +3.5%, +2.6% |
| BJ_T1_preloaded | supervised | condensed | +73.4%, +82.0%, +76.0% | +84.7%, +88.4%, +86.7% | +89.8%, +86.4%, +80.1% | +48.1%, +53.9%, +48.0% | +42.0%, +42.0%, +41.8% | +75.6%, +75.3%, +74.7% | +106.5%, +107.1%, +106.3% |
| BJ_T1_preloaded | supervised | raw | +1.9%, +8.4%, +3.5% | +1.2%, +3.5%, +2.5% | +1.5%, +2.3%, +2.3% | -2.6%, +0.4%, -2.7% | -0.8%, -0.8%, -1.1% | -0.4%, -0.9%, -1.9% | -1.3%, -0.3%, -1.6% |
| BJ_T1_snug | label-free | condensed | +1.3%, +1.4%, +1.2% | +1.4%, +1.1%, +1.1% | +1.1%, +1.2%, +1.3% | -0.1%, -0.2%, -0.4% | +1.1%, +0.8%, +0.7% | +1.7%, +1.7%, +1.6% | +1.9%, +2.5%, +1.6% |
| BJ_T1_snug | label-free | raw | -0.6%, -2.1%, -0.6% | -2.8%, -1.4%, -0.5% | -0.7%, -0.2%, +0.3% | +0.1%, +0.4%, +0.8% | +1.4%, +1.1%, +1.5% | +0.6%, +0.4%, +1.5% | +5.0%, +4.9%, +4.1% |
| BJ_T1_snug | supervised | condensed | +101.4%, +107.7%, +94.3% | +115.2%, +116.9%, +101.6% | +115.0%, +116.5%, +90.7% | +73.8%, +71.5%, +65.3% | +41.9%, +40.4%, +41.0% | +75.5%, +76.5%, +75.9% | +106.9%, +107.0%, +106.2% |
| BJ_T1_snug | supervised | raw | +8.1%, +11.8%, +3.8% | +4.8%, +5.4%, +4.0% | -0.1%, +1.2%, +0.5% | -3.3%, -4.1%, -5.8% | -0.4%, -2.1%, -1.3% | -1.3%, +0.1%, -0.6% | -1.4%, -1.3%, -2.5% |
| BJ_T2_preloaded | label-free | condensed | +0.0%, +0.4%, +0.1% | +0.3%, +0.3%, +0.5% | +0.2%, +0.9%, +0.7% | -0.1%, +0.5%, +0.5% | +0.7%, +0.7%, +0.9% | +0.9%, +0.9%, +1.0% | +1.6%, +1.1%, +1.6% |
| BJ_T2_preloaded | label-free | raw | -1.0%, -1.0%, -0.8% | -0.4%, -0.7%, +0.1% | -0.0%, +1.0%, +1.5% | -1.4%, -0.6%, -0.8% | +1.0%, +1.3%, +0.6% | -0.5%, -1.8%, -2.6% | +5.1%, +3.7%, +5.0% |
| BJ_T2_preloaded | supervised | condensed | +56.7%, +67.2%, +65.6% | +70.7%, +72.8%, +58.9% | +72.5%, +75.0%, +38.8% | +29.9%, +29.8%, +23.3% | +27.7%, +29.2%, +29.4% | +61.5%, +62.3%, +61.0% | +101.0%, +101.6%, +100.7% |
| BJ_T2_preloaded | supervised | raw | -3.7%, +1.4%, -0.5% | -2.1%, -1.9%, -1.9% | -2.4%, -1.4%, -2.8% | -2.9%, -3.0%, -4.7% | -0.6%, +1.6%, +2.0% | -1.5%, +0.2%, -2.6% | -0.3%, +0.9%, -0.8% |
| BJ_T2_snug | label-free | condensed | +1.0%, +0.7%, +0.6% | +1.2%, +0.8%, +0.6% | +0.8%, +0.8%, +0.7% | -2.9%, -2.1%, -2.5% | +0.5%, +0.1%, +0.6% | +1.0%, +1.0%, +1.0% | +2.1%, +1.3%, +1.6% |
| BJ_T2_snug | label-free | raw | -3.3%, -3.0%, -2.6% | -6.1%, -5.2%, -4.2% | -2.5%, -2.7%, -2.9% | -4.6%, -3.5%, -4.4% | +0.1%, -0.0%, -0.5% | -0.5%, -1.3%, -1.4% | +6.8%, +5.5%, +6.5% |
| BJ_T2_snug | supervised | condensed | +81.5%, +89.0%, +80.4% | +85.0%, +68.8%, +60.2% | +102.0%, +63.1%, +47.0% | +63.3%, +59.5%, +58.5% | +27.2%, +28.2%, +28.2% | +60.4%, +62.2%, +61.4% | +100.6%, +101.3%, +100.7% |
| BJ_T2_snug | supervised | raw | +0.4%, +4.9%, -1.5% | -2.1%, +1.6%, -3.1% | -2.0%, +0.6%, -6.2% | -5.2%, -4.6%, -6.0% | -1.3%, +0.2%, +0.2% | -3.5%, +0.2%, -1.4% | -0.9%, +0.6%, -0.7% |

Each cell gives seeds 5, 6 and 7.

### The author's recomputation (`audit/c23_recompute.py`, records in `records/c23/audit/`)

- Environment, from the record of each step: Python 3.13.18, scipy 1.18.1, solver scipy, 2 processors, BLAS threads a process 1; numpy 2.4.6 for the fields, the pairs in the gate's order (label-free arm), the pairs in the gate's order (supervised arm), the re-solved members, the re-solved training members, the last step; numpy 2.5.3 for the records, the instances, the pairs in another order.
- Regenerated instances (`regenerate.json`; zlib 1.3, archive creator field 0): 644 of 644 files have the manifest's SHA-256 and 644 its sizes; the members are the configured draws: True; members shared between two sets: 0.
- From the returned per-pair rows, with the script's own quantile and its own code for part 1 (`aggregate.json`): largest relative difference of a statistic from the returned one 0; the wording of part 2 equal: True; the verdict and the ranking of part 1 equal: True; every reported block of part 1 equal: True; the identity values within the tolerance: True.
- Metrics that need no solve, recomputed for 11,088 fields of 132 members (members not recomputed: 0): largest absolute difference from the returned rows F_err 0, e_err 0, F_sigma_err 2.0e-14, gap 5.3e-15, bound 5.5e-15, iou_contact 0, iou_plastic 0, bolt_err 0, u_rel_l2 3.3e-16, e 0, F 0; containment in the bound differing in 0 fields.
- The returned labels on the regenerated instances, 924 levels: largest relative difference in energy 4.4e-16, in force 0; in end displacement 0 mm; largest unconstrained residual 1.5e-10; smallest gap 0; smallest multiplier -6.1e-11.
- The condensed fields from the returned base fields, raw fields and amplitudes, in float32, for 792 member and run pairs: largest absolute difference 0 (0 unknowns differ; the largest unknown is 6.88 in size).
- The error with its exact solve, recomputed in the order of the gate's own evaluation for 5,418 pairs (36.68 processor hours): largest absolute difference of the signed error from the returned one 6.0e-13; largest absolute difference of the other metrics 2.0e-14.

| Reading, set, run | Pairs recomputed | Largest absolute difference of the error | Infinite as returned | Infinite as recomputed |
|---|---|---|---|---|
| condensed, eval, supervised_512_s5 | 7 | 1.2e-14 | 0 | 0 |
| condensed, eval, supervised_512_s6 | 7 | 5.1e-15 | 2 | 2 |
| condensed, eval, supervised_512_s7 | 7 | 1.1e-14 | 0 | 0 |
| condensed, third, label_free_s5 | 448 | 9.1e-14 | 0 | 0 |
| condensed, third, label_free_s6 | 448 | 9.4e-14 | 0 | 0 |
| condensed, third, label_free_s7 | 448 | 1.6e-13 | 0 | 0 |
| condensed, third, supervised_512_s5 | 448 | 2.7e-13 | 0 | 0 |
| condensed, third, supervised_512_s6 | 448 | 1.7e-13 | 0 | 0 |
| condensed, third, supervised_512_s7 | 448 | 2.2e-13 | 0 | 0 |
| raw, eval, supervised_512_s5 | 7 | 6.7e-15 | 0 | 0 |
| raw, eval, supervised_512_s6 | 7 | 4.4e-15 | 0 | 0 |
| raw, eval, supervised_512_s7 | 7 | 1.1e-14 | 0 | 0 |
| raw, third, label_free_s5 | 448 | 6.0e-13 | 0 | 0 |
| raw, third, label_free_s6 | 448 | 2.4e-13 | 1 | 1 |
| raw, third, label_free_s7 | 448 | 5.2e-14 | 0 | 0 |
| raw, third, supervised_512_s5 | 448 | 1.1e-13 | 0 | 0 |
| raw, third, supervised_512_s6 | 448 | 2.2e-13 | 0 | 0 |
| raw, third, supervised_512_s7 | 448 | 2.3e-13 | 0 | 0 |

- A row with a note in the gate's order: third_0034, label_free_s6, raw, 0.5 mm: recomputed infinite (RuntimeError: bubble condensation did not converge), returned infinite (RuntimeError: bubble condensation did not converge).
- A row with a note in the gate's order: eval_0063, supervised_512_s6, condensed, 0.5 mm: recomputed infinite (RuntimeError: bubble condensation did not converge), returned infinite (RuntimeError: bubble condensation did not converge).
- A row with a note in the gate's order: eval_0063, supervised_512_s6, condensed, 1 mm: recomputed infinite (RuntimeError: bubble condensation did not converge), returned infinite (RuntimeError: bubble condensation did not converge).
- From the errors recomputed in the gate's order, where every pair of an arm's reading on the third sample was recomputed: largest relative difference of a run's median or 90th percentile from the returned one label_free condensed 7.9e-14, label_free raw 9.4e-14, supervised_512 condensed 1.0e-14, supervised_512 raw 5.8e-13.
- From the same errors, the judged ratios: 84.2550 and 29.8694, wording "label-free closer"; relative difference from the returned ones 6.0e-14 and 7.9e-14; wording equal: True.
- From the same errors, the ratios with the supervised arm read raw: 2.1488 and 1.7648, wording "label-free closer"; relative difference from the returned ones 5.1e-13 and 1.1e-13; wording equal: True.
- Part 1 from the errors recomputed in the order of the gate's own evaluation: 121 of 448 pairs flagged; pairs not flagged above 10% in some run 0; readings above 5% among those not flagged 8 of 981; S1 True, S2 True, S3 True: PASS; R 0.909, 0.912, 0.949: HOLDS. Equal to the returned part 1 in every count and word: True; the flags equal: True.
- The error with its exact solve, recomputed in another order (one reading at a time) for 1,371 pairs (4.62 processor hours): largest absolute difference of the signed error from the returned one infinite (see the table); largest absolute difference of the other metrics 6.2e-15.

| Reading, set, run | Pairs recomputed | Largest absolute difference of the error | Infinite as returned | Infinite as recomputed |
|---|---|---|---|---|
| condensed, third, label_free_s5 | 448 | 4.0e-13 | 0 | 0 |
| condensed, third, label_free_s6 | 448 | 7.3e-14 | 0 | 0 |
| condensed, third, label_free_s7 | 448 | infinite | 0 | 1 |
| raw, third, supervised_512_s5 | 14 | 8.9e-14 | 0 | 0 |
| raw, third, supervised_512_s6 | 7 | 8.1e-15 | 0 | 0 |
| raw, third, supervised_512_s7 | 6 | 6.3e-15 | 0 | 0 |

- Part 1 from the errors recomputed in another order (one reading at a time): 121 of 448 pairs flagged; pairs not flagged above 10% in some run 1; readings above 5% among those not flagged 9 of 981; S1 False, S2 True, S3 True: FAIL; R 0.909, 0.912, 0.915: HOLDS. Equal to the returned part 1 in every count and word: False; the flags equal: True.
- Pairs recomputed in both orders: 1,371. Where both errors are finite, their largest absolute difference is 4.0e-13. Finite in one order only: third_0034, label_free_s7, condensed, 0.5 mm (the other order: infinite, RuntimeError: bubble condensation did not converge; the gate's order: +0.37%).
- Held-out and tested members re-solved from the regenerated instances (`resolve.json`): third_0034: bit for bit False, largest difference 9.7e-16 of the largest unknown, 2.2e-16 in energy, 5.6e-16 in force, iterations equal to the ledger's True, converged True; third_0001: bit for bit False, largest difference 2.3e-15 of the largest unknown, 7.8e-16 in energy, 2.6e-14 in force, iterations equal to the ledger's True, converged True; eval_0063: bit for bit False, largest difference 3.9e-15 of the largest unknown, 4.4e-16 in energy, 3.1e-15 in force, iterations equal to the ledger's True, converged True; tested_BJ_T1_preloaded: bit for bit False, largest difference 3.8e-15 of the largest unknown, 4.4e-16 in energy, 1.8e-15 in force, iterations equal to the ledger's True, converged True.
- Training members re-solved from the regenerated instances (`resolve_train.json`): train_0076: bit for bit False, largest difference 8.2e-15 of the largest unknown, 4.4e-16 in energy, 1.1e-15 in force, iterations equal to the ledger's True, converged True; train_0236: bit for bit False, largest difference 5.0e-15 of the largest unknown, 2.2e-16 in energy, 6.7e-16 in force, iterations equal to the ledger's True, converged True; train_0375: bit for bit False, largest difference 1.9e-15 of the largest unknown, 2.2e-16 in energy, 6.7e-16 in force, iterations equal to the ledger's True, converged True; train_0379: bit for bit False, largest difference 1.8e-15 of the largest unknown, 4.4e-16 in energy, 2.2e-16 in force, iterations equal to the ledger's True, converged True.
