# Gate G-C2.2: verdict

**What was pre-specified**
- `docs/PRESPEC_G-C2.2.md`, configuration SHA-256 `ef5376a4d6c3cc98d7888121439c8d959ee817d332958dd6b1141b25e78734bb`, stamped at 08:59 GMT on 13 November 2026.
- The tag `prereg-c22`, made at 12:44 GMT the same day, points to commit `6d9da9b`, which is dated 11:17 GMT. The code is pinned file by file in `docs/G-C2.1_code.sha256` and `docs/G-C2.2_code.sha256`.
- The commands are those of `RUNBOOK_C22.md`. They were run by the job queue of the owner's laptop, a script outside the stamp; its files are in the return package.

**Where the numbers come from**
- **The return package**: `c22_return.tar.gz`, SHA-256 `4b40742f0bcb92a2992b9ae3e114500f58b79d39025da1adbf23f44372bb3249`, 119,319,209 bytes, made on the laptop on 15 November 2026 between 12:12 and 12:15 GMT (the operator's record: in the archive the folder of the records is dated 12:12 and its newest file 12:13:53; the archive file on the laptop is dated 12:15). The SHA-256 written beside it matches the file.
  - `records/c22/return_files.sha256` lists the SHA-256 of its 268 files as received, and `records/c22/return_listing.txt` is the archive's listing, with the numbers of the owner and the group in place of the name of the account that packed it and with the names of two files replaced by placeholders (see "The records as kept").
  - The files are kept with the differences listed under "The records as kept" below: 120 of them in `records/c22/return/`, and the 141 label and prediction files in a deposit outside the repository, which `records/c22/deposit.json` lists.
- **The verdict and every metric** come from `verdict.json` of the return package, which the stamped `c22/evaluate.py` wrote on the laptop. Its SHA-256 is `3c77fd3d34cbf4a248824269842b778f373c5aac6853216403db81266d5dce64` as received and `d7f80645f820134b0412ef3423a1d6f2b2eeb26bb5178d3e58fc1aa1796a58b1` as kept in `records/c22/return/`, with LF line ends.
- **The author's recomputation**: `audit/c22_recompute.py` (not under the stamp). Its steps 1 to 6 were written while the evaluation ran, before its result was known, and tried on the files of the host check; step 7, which reads the records, the packing of the solves into one file and the option `--reverse` were added afterwards (the author's statement; no record dates the script). Its outputs are in `records/c22/audit/`. What it covers is stated under "The recomputation" below.
- **The tables** at the end are generated from those records by `audit/c22_write_verdict.py`, written after the run.

**Independent audit.** A separate agent that wrote none of the code, the records or this document audited the return package as received and the proposed commit before the push, in four rounds on 15 and 17 November 2026: the records as kept, a draft of this document with its tables, the author's audit scripts and the README. Its reports are in `docs/reviews/audit_report_G-C2.2_2026-11-15.md` and its scripts in `audit/independent/G-C2.2/`.
- **What it confirmed, with its own code and, for the solves and the instances, its own driver on the stamped library.** C1, C2 and the verdict from the returned per-pair values, with no difference from `verdict.json`. The judged error of 161 pairs with exact solves, to within 5.4e-14 of the returned values: 107 of the 1,344 judged pairs, among them every pair above 10% and the pairs around each seed's median and 90th percentile, and 54 pairs of the raw reading and of the reported sets. The 644 instances, regenerated with the manifest's hashes. The condensed fields, bit for bit from their parts, with every amplitude within its limits. The configuration, the code hashes, the three drawn samples with a sampler of its own, the ledger, the 600 epoch lines of the logs against the histories, and the order of the queue's commands. 759 cells of the tables of the draft, none differing.
- **What it found wrong in the first round.** Six errors and four omissions, one of them this paragraph, which could not yet report an audit, none in a number of the verdict: a hash given for the wrong copy of `verdict.json`; two statements of the README that said more than this document or the pre-specification; the time of a step offered as a sign of a restart; an account name in the archive's listing; the name of other work of the owner in a kept launcher; a departure that was not listed (deviation 7); no statement on the rule about other training (deviation 3); and the other readings by level and those of the tested members, which were in `verdict.json` alone.
- **Second round.** The auditor checked each correction against the records, derived the 3,330 cells of the added tables and the 759 earlier ones again with its own code, none differing, and checked the 426 paths of the commit as it then stood. It confirmed the corrections except one, and found two errors, both about what the commit would publish and none about a number: the strings that `audit/c22_keep.py` removes stood in that script in hexadecimal, and the names of the two launchers that are left out said, in three lists, what the words removed from `incidents.log` had said. It did not repeat the exact solves, the regeneration of the instances or the checks of the run, because the records and the stamped code had not changed.
- **After the second round** the author took the strings out of the script and replaced the two names in the lists (see "The records as kept"). In a third round, on 17 November 2026, the auditor searched the 430 paths of the commit as it then stood for the five strings, in plain text and in the encoded forms that its report lists, and found none; found that `audit/c22_keep.py`, run with the file of strings and the archive's listing, makes the kept copy, its report and its lists again byte for byte, and that the two names are replaced in all three lists; and found that the final texts state its two earlier rounds correctly. It found no error; its report lists what was still to be written and five smaller points.
- **After the third round** the owner decided, on 17 November 2026, that the 141 label and prediction files of the kept copy would be deposited outside the repository and not committed (see "The records as kept"). The author took them out of the commit, added `audit/c22_deposit.py` and `records/c22/deposit.json`, and changed this document and the README to say where the files are. In a fourth round, on 17 November 2026, the auditor checked this step with its own code and its own reader of the archive's format. Exactly the 141 files of `records/c22/deposit.json` were gone from the commit; the 120 files left and the 141 of the archive are the 261 kept files, byte for byte; the archive has the size and the hash that the record and this document give, and its headers hold paths and numbers alone; `restore` gave the folder of the earlier state back and refused the changed archives that the auditor tried; the tables of this document are written again byte for byte without the deposited files; and none of the five strings is in the paths of the commit as they then stood, in the archive or in the texts for the deposit. It found four errors and three omissions, none in a number: the texts said "the array files" where 20 small array files of the host check stay in the repository; `audit/c22_deposit.py` admitted two kinds of unsafe name when the record was changed to fit, and packed a folder that was not whole without a complaint; the heads of two scripts and a heading of the README described the state before; no rule kept the restored files out of a commit; the DOI was not yet reserved when the document said that it was; and this paragraph could not yet report the round.
- Every error and omission is corrected here, in the records as kept and in the README; what was done about each smaller point is in the author's notes. The reports are filed as delivered, each followed by those notes. The auditor did not see the last changes, which were made after the fourth round and are listed in the notes on it.
- **What it did not check** is listed at the end of its reports: among other things the training itself, the exact solves outside its sample, and every statement that rests on the owner's or the operator's word.

## Run record

**Host** (`smoke/smoke_report.json` of 13 November; the log of the environment's setup of 10 November, which is in the package and not kept here)
- The owner's laptop: Windows 11 (`Windows-11-10.0.26200-SP0`), an NVIDIA GeForce RTX 4070 Laptop GPU with 8 GiB, 32 logical processors.
- Python 3.12.16, numpy 2.4.6, scipy 1.18.1, torch 2.12.1 with CUDA 13.2. Worker processes are started by spawn and use one thread each for linear algebra. The sparse solver is scipy's SuperLU.
- The NVIDIA driver was 610.74 when the environment was set up on 10 November. The runs did not record it.

**Preconditions** (sections 0 and 1 of the runbook; `preconditions.log`, written by the operator)
- The tree was taken from the tag: an archive of 101 files, SHA-256 `2fddd104386c45f9d4b19a8911a5c511cd85f6ead44ae6184260f7db9237f115`, with the same hash on the laptop. Its 34 pinned files matched their hashes there.
- The 51 tests of the runbook passed on a full checkout of commit `6d9da9b` on the operator's Linux machine, between 11:43:40 and 11:58 GMT on 13 November, before the tag was made (deviation 7).
- The host check (`c22/smoke.py`, a reduced configuration) passed on the laptop's GPU on 13 November between 12:46:57 and 12:51:08: an interrupted and resumed run ended with the weights, losses, capped steps and prediction files of the uninterrupted one, with no difference.
- The configuration command printed the stamped hash. The file it wrote, `c22_config.json`, is the stamped configuration, with the same bytes as on the operator's machine.

**Generation and labels** (13 November)
- Generation: 12:53:48 to 12:58:13, 644 members. From then on members of seed 20261113 existed.
- Labels, with 16 worker processes: the fresh held-out members from 12:58:13 to 13:06:36, G-C2.1's held-out members to 13:17:08, the tested members to 13:19:23. 132 members at seven levels, each labelled once; every level converged, in at most 23 iterations.
- The check of the labels passed at 13:19:23: `"labels": 132, "needed": 132, "missing": []`, `"ok": true`. The largest unconstrained residual is 1.3e-10, and the two force readings of a reference differ by at most 4.8e-13.

**Training** (each run 102,400 steps in 200 epochs; `run_files/*/attempts.log`, `history.json`, the queue's logs)

| Seed | Started | Ended | Hours of training | Interruptions |
|---|---|---|---|---|
| 5 | 13 November, 13:19:24 | 14 November, 07:56:43 | 14.08 | paused by the owner after epoch 75, from 13 November 21:19:08 to 14 November 01:44:51 |
| 6 | 14 November, 07:57:41 | 14 November, 20:53:08 | 12.70 | none |
| 7 | 14 November, 20:53:19 | 15 November, 09:32:10 | 12.55 | none |

- Each run ended with the status `finished` and wrote its predictions in both readings. No run stopped on a non-finite value.
- The mean loss over the last ten epochs was 10.364, 10.345 and 10.361. The runbook's comment expects it near 10.34 to 10.37. The single epochs of those ten ran from 10.27 to 10.43.
- The cap acted on 2,154, 1,805 and 2,000 steps, and 233, 136 and 218 steps were bursts.
- From the first start to the last end the three runs took 44 h 13 min, 39.3 h of them training. The report at 96 hours was not due.

**Evaluation**: 15 November, 09:32:11 to 11:32:35, with 16 worker processes, exit code 0. Its last line is `{"verdict": "PASS", "C1_value": 0.007972382816471169, "C2_value": 0.03663936677608451, "missing": [], "non_finite": []}`.

**The queue**: every command of the runbook ended with exit code 0, except the first attempt of seed 5, which the pause stopped. Every guard let the queue go on, and no command was cancelled (`records/c22/audit/records.json`).

## Deviations

None of them changes a threshold, a metric, a reading or a seed.

1. **The pause, and a restart of the laptop, during the run of seed 5** (`incidents.log`, written by the operator on 14 November).
   - The owner paused the run at 21:19:05 on 13 November and closed the queue's window at 21:20:15, having written to the operator at 21:13 that the laptop would be restarted to install Windows updates and the GPU then used for other things. The owner continued the run at 01:42:56 on 14 November, and it resumed from the checkpoint of epoch 75 at 01:44:51. The work of 75 s on epoch 76 was lost.
   - The runbook provides for a pause of a training run and for a restart of the laptop. A resumed run is the same run; the pre-specification does not claim that it ends in the same state to the last bit as an uninterrupted one.
   - Whether the laptop was restarted, and which updates were installed, is not recorded. So the software of the host may have changed after epoch 75 of seed 5: Windows, and possibly the driver of the GPU. The Python environment of the queue is its own and was not touched (inferred from the torch version in the histories of seeds 6 and 7, which is that of the host check; the history of seed 5 carries the version of its first start).
   - One observation fits a restart with updates and does not prove one: the free space of the disk rose from 50 to 84 GB between two readings of the operator, on 13 November at 20:43 and on 14 November at 01:51; they are not in the returned records. The time of a step fell after the pause, from a median of 0.75 s over the 75 epochs before it to 0.34 s over the 125 after it, but this says nothing about a restart: the same two regimes occur within the runs of seeds 6 and 7, which were not interrupted (deviation 3).
2. **The queue after the closed window.** When the window was closed, the queue had begun to record the waiting job of the pause as ended; it was stopped before it wrote the record, so the job stayed pending and nothing was cancelled. Had the record been written, and had the queue been started before the run was continued, the guard after seed 5 would have cancelled the later commands. The owner continued the run first and started the queue second. No command ran out of order.
3. **The time of a step, and the other load on the laptop.** The runbook gives 0.38 s for the idle laptop and up to 0.8 s when it is in use, as "recorded and not a criterion". The epochs' means ran from 0.33 s to 0.83 s: 430 of the 600 epochs took less than 0.38 s a step, and 13 took more than 0.8 s, 11 of seed 5 and 2 of seed 6.
   - The slow epochs come in stretches. 160 epochs took 0.6 s a step or more: epochs 1 to 71 and 73 to 75 of seed 5, all but one of the epochs before the pause (7.9 h); epochs 150 to 192 and 199 to 200 of seed 6, from about 15:45 to 20:15 and from about 20:35 to 20:45 on 14 November (4.7 h); and epochs 1 to 16, 19 to 33 and 39 to 48 of seed 7, from its start at 20:53 on 14 November until about 01:35 on 15 November (4.2 h). The clock times are inferred from the start and end lines of the runs and the epochs' times; those of seed 6 hold to within ten minutes, because about 14 minutes of that run lie outside its epochs and the records do not place them. Ten more epochs took between 0.38 and 0.6 s.
   - The pre-specification says that no other training uses the GPU during the runs, and the runbook that the development queue of the laptop is empty. The queue's records show the gate's jobs in an unbroken sequence, each started within a second of the end of the one before, apart from the pause, when the queue was closed. That nothing else was queued is the operator's statement: the package holds the job files of the gate alone, as section 6 of the runbook provides. The owner states that no other training used the GPU during the days of the runs and that the slow stretches were the owner's own use of the laptop (the owner's statement to the author on 17 November 2026).
4. **A warning in the training logs.** Each start of a training run printed one warning of PyTorch, that the invariants of sparse tensors are not checked. The runbook's comments do not mention it, and its rule is to report any output that differs from a comment. The same warning appeared in the development runs and in the host check. It was not reported during the run.
5. **The return package.** Beyond the files that section 6 of the runbook lists, the operator added the queue's scripts, as that section asks, and the record of the pause (`PAUSED_20261114_014256.json`, `74_c22_train_s5.kill`, `74_c22_train_s5.go`), the operator's record of incidents (`incidents.log`), the log of the environment's setup and `check_gpu.py`.
6. **What the operator read during the runs.** The operator read each run's epoch lines, that is losses, times and the counts of capped steps and bursts, while the runs went on, and reported them to the owner. No error of a prediction was computed or read before the evaluation ended (the operator's statement; the records show only that the evaluation ran once, after the three training runs, and started one second after the last of them had ended).
7. **The suite before the tag.** The runbook places all of its section 0 after the tag. Section 0c, the 51 tests, ran from 11:43:40 to 11:58 on 13 November on a checkout of commit `6d9da9b`, after the push and before the tag was made at 12:44:25; sections 0a and 0b ran at 12:45 and 12:46 (`preconditions.log`). The commit is the one that the tag names. The tests ran on the operator's Linux machine, with numpy 2.5.3 and with PARDISO installed, where the laptop has numpy 2.4.6 and scipy's solver alone; the same 51 tests had passed on the stamped files with the laptop's solver before the push.

The records show no other departure.

**The records as kept.** The kept copy holds the package's files with these differences; `records/c22/return_files.sha256` gives the hashes as received and `records/c22/return_kept.sha256` as kept. The repository holds the kept copy without its label and prediction files (the last point).
- In 67 text files the line ends CR LF, which Windows wrote, are LF.
- In six logs and one script of the queue the path of the working folder on the laptop is replaced by `W`. The kept `queue/make_jobs.py` is therefore not the script as it ran: its path of the queue reads `W/queue`.
- In one launcher of the queue (`queue/start.bat`) the name by which the owner addresses the operator is replaced by "the operator" in a message, and the name of another piece of the owner's work by "another project" in a comment.
- In the operator's record of incidents (`incidents.log`) the words that say what the owner used the GPU for during the pause are replaced by "for other things".
- Seven files are not kept: the two scripts of the queue that pause and continue a run and their two launchers, whose prompts to the owner and file names are in Chinese; the log of the environment's setup, which lists the programs that were using the laptop's GPU on 10 November; and the two model states of the host check, which the repository's rules leave out. `records/c22/keep_report.json` lists them with their hashes. The names of the two launchers say in Chinese what the launchers are for; there, in `return_files.sha256` and in the listing they are replaced by `queue/<launcher of the pause>.bat` and `queue/<launcher of the continuation>.bat`. The owner keeps the seven files outside the repository, with the package as received and the three model states of the gate.
- The other 192 files are byte for byte as received.
- `audit/c22_keep.py` makes the copy, its report and the three lists from the package as received, the archive's listing and a file of the five strings that are replaced. That file is not in the repository; the owner keeps it with the package, and without it the copy cannot be made again.
- The hashes and the sizes of the files as received are given. The length of a replaced string therefore follows from the kept file, and a reader who guesses the string could confirm the guess. This cannot be avoided while those hashes are given.
- The ledger's time stamps carry the name of the time zone as the laptop's Windows gives it, in Chinese; in the file it is written in escapes.
- Run on the unpacked package, `sha256sum -c` with `return_files.sha256` checks 266 of its 268 lines; the two launchers stand under their placeholders.
- The kept copy has 261 files, and `records/c22/return/` holds 120 of them. The other 141 are the label and prediction files, each with the bytes it had in the package: the 132 files of `labels/` (the labels of the 64 fresh held-out members, of the 64 held-out members of G-C2.1 and of the four tested members) and `preds.npz`, `preds_condensed.npz` and `preds_base.npz` of each of the three runs, 117,562,958 bytes together. On 17 November 2026 the owner decided to keep array files of this size out of the repository; the 20 array files of the host check (`smoke/`, 477,551 bytes together) are small and stay. The 141 files are deposited at Zenodo as one archive, `c22_arrays.tar` (117,678,080 bytes, SHA-256 `54ea26fabd31d9939cc7480f6ade9cac4b21ec79c2bd43018acfc61a44ada7ca`), https://doi.org/10.5281/zenodo.24320576; the DOI was reserved before this commit, and the record is published when the commit has been pushed. `records/c22/deposit.json` gives the size and the SHA-256 of the archive and of each file. `audit/c22_deposit.py` makes the archive from a whole kept copy and, with `restore`, checks a downloaded archive and writes its files into `records/c22/return/`. Four steps of the recomputation (`--fields`, `--curves`, `--resolve` and `--records`), eight scripts of the independent audit, which the README names, and a check of `return_kept.sha256` with `sha256sum -c` need the copy whole; the tables of this document are written from the 120 files and the author's outputs alone. `records/c22/.gitignore` keeps the restored files out of a commit.

## Verdict

**PASS, judged as pre-specified.**
- **C1**: the median over the three seeds of the per-seed median distance from the reference curve is 0.80%, against a threshold of 5%. The seeds give 0.83%, 0.80% and 0.78%.
- **C2**: the median over the three seeds of the per-seed 90th percentile of that distance is 3.66%, against a threshold of 10%. The seeds give 3.66%, 3.77% and 3.66%.
- Both are read from the condensed fields of the 64 fresh held-out members at seven levels, 448 pairs a seed, as pre-specified.
- The raw reading, reported and not judged, gives 1.36% and 10.54% on the same pairs: it would meet C1 and miss C2.
- No seed stopped and none was missing. No pair has an infinite error, and the reference code evaluated every field.

**The recomputation**
- The author recomputed the following on another machine, from the returned predictions and labels and from instances regenerated with the stamped code. The machine: Linux, Python 3.13.18, with the host's numpy 2.4.6 and scipy 1.18.1, scipy's SuperLU, one BLAS thread a process. The host was Windows with Python 3.12.16.
  - **The instances.** All 644 regenerated files have the manifest's SHA-256, when written through zlib 1.3 and with the archive's creator field as Windows writes it. The members are the configured draws, and no two of the four sets share a member.
  - **The criteria from the returned per-pair values**, with the script's own quantile: every seed's median and 90th percentile, C1, C2 and the verdict are the returned ones exactly, in both readings and on the three sets.
  - **The judged error of all 1,344 judged pairs**, with the stamped metric function and its exact solve at each predicted end displacement (3.5 processor hours). The signed distances agree with the returned ones to within 8.1e-14 in absolute terms. The seeds' medians and 90th percentiles recomputed from them differ from the returned ones by at most 1.3e-14, C1 by 1.1e-16 and C2 by 3.5e-16. The verdict is PASS.
  - **Every metric that needs no solve**, for all 5,544 returned fields (three seeds, two readings, 132 members, seven levels): the largest absolute difference from a returned value is 8.0e-15, and the containment in the bound is the returned one for every field.
  - **The condensed fields.** Computed again in float32 from the returned base fields, raw fields and amplitudes, the 396 arrays (132 members, three seeds) equal the returned condensed fields bit for bit.
  - **The labels.** Evaluated on the regenerated instances, the 924 returned label fields give the label's force and end displacement exactly and its energy to within 4.4e-16 in relative terms; their largest unconstrained residual there is 1.3e-10. Four members (two fresh held-out, one of G-C2.1's, one tested) were re-solved from the regenerated instances: not bit for bit, with differences of at most 3.8e-15 of the largest unknown, in the ledger's numbers of iterations.
  - **The records.** The returned configuration is the stamped one, byte for byte. The ledger holds the 132 labelled members once each, at the configured levels, all converged and within the configured limits, and the label files have its SHA-256. Every prediction file holds the 132 members with the expected shapes. Each run's log gives its history's losses, times and counts.
- **Not recomputed with exact solves**: the judged error of the raw reading and of the two reported sets, 4,200 pairs. Their other metrics were recomputed (above). The reported numbers that rest on those distances are the returned ones.
- The training was not repeated. The model states were not returned; they stay on the laptop.

## What this means

**As fixed in advance (PASS).** With the two stability settings, label-free training of the project's transformer reproduced the reference model's force-deformation curve on 64 T-stubs that neither the training nor the choice of the method had seen: within 5% in force in the median and within 10% at the 90th percentile, in the median over three training seeds.
- The point is read after one amplitude of the field has been set by minimising the energy. Any wording says so, and gives the raw reading beside it: see the next paragraph.
- The limits stated for a PASS of G-C2.1 hold: the 5 mm mesh, small strains, frictionless contact, the deformation theory under monotonic loading, and the gap of the reference model to the T-stub tests.
- G-C2.1's verdict stands. G-C2.2 is a new gate with a changed method; it does not show which of the two changes is needed.

**The raw reading does not meet C2.** Read without the condensation, the same three models give a median of 1.36% and a 90th percentile of 10.54% on the fresh held-out members (seeds: 10.94%, 10.47%, 10.54%). C1 would hold and C2 would not, by half a percentage point. The pass rests on the reading that was pre-specified as the judged one.

**Where the two readings differ.** Up to 4 mm they are close: the medians lie between 0.4% and 1.6% in both. At 6 and 8 mm the raw fields are too stiff, and the condensation removes most of that.
- At 8 mm the median distance is 9.2% to 9.9% raw and 2.0% to 2.2% condensed; the 90th percentile is 43% to 44% raw and 6.6% to 7.5% condensed.
- Of the 64 pairs at 8 mm, 30 or 31 are above 10% raw and 3 or 4 condensed.
- The amplitudes lie between 0.80 and 1.19, with a median of 1.00; none ended on a bound. In 5, 9 and 11 of the 448 fresh fields the iteration had not met its tolerance after 12 evaluations; those amplitudes were used as they were, as pre-specified.

**The tail that remains.** In the condensed reading 6, 5 and 6 of the 448 pairs are above 10%, in 4, 3 and 3 members; over the three seeds they are eight pairs of five members.
- All eight are too stiff, and all five members have a yield stress below 300 MPa. Six of the eight pairs are at 6 or 8 mm.
- One member carries half of them: `eval_0001`, the member with the thinnest flange of the five (8.6 mm) and a yield stress of 239 MPa. Its distance grows with the level in every seed, from 8% to 10% at 3 mm to between 50% and 69% at 8 mm; its raw distance at 8 mm is 164% to 183%.
- At 8 mm the 17 fresh members below 300 MPa have a median distance of 5.8% to 6.3% and a 90th percentile of 12% to 18%; the 47 at or above 300 MPa have 1.6% to 1.7% and 3.4% to 4.8%, with no pair above 10%.
- The tail follows the member and the level, not the seed, as it did in development.

**Against the expectation stated before the run**
- C1 was expected to hold, at about the 0.84% and 0.95% of the two development models: it is 0.80%.
- C2 was expected to hold, "with less certainty", at about their 3.00% and 3.22% with 2 and 5 pairs above 10%: it is 3.66%, with 5 or 6 pairs above 10%. No seed collapsed.
- The raw reading was expected to meet C1 and to lie near the threshold of C2, where it had been 7.27% and 8.03%: it met C1 and lies at 10.54%, on the other side of the threshold. On G-C2.1's held-out members, the sample of the development runs, the same three models give 7.6% to 8.7%. The fresh sample has more members whose raw field is too stiff at 8 mm: 30 or 31 members with a raw pair above 10%, against 20 to 23 there.
- The gate was expected to pass, and passed.

**The other reported readings**
- **G-C2.1's held-out members** (reported; read many times in development): condensed, a median of 0.93% to 0.99% and a 90th percentile of 3.2% to 3.4%, with 6, 3 and 5 pairs above 10%; raw, 1.39% to 1.45% and 7.6% to 8.7%. One of these members, `former_0017`, is read worse by the condensed reading than by the raw one at 8 mm (12% against 7%): there the amplitude shrinks the field.
- **The four tested members** (28 pairs a seed): condensed, every pair within 2.9% of the reference curve; raw, within 6.9%. As in G-C2.1, this compares the network with the reference model, not with the tests.
- **The other metrics** on the fresh members, condensed reading, medians over the 448 pairs: the force at the same $D$ within 0.35% to 0.44%, the end displacement low by 0.7%, the displacement field within 1.5% to 1.6% in the relative $L^2$ norm, the contact region with an intersection over union of 0.97 and the plastic region with 0.86. Every field lies within its certified bound, whose median is about 6% of the reference force.
- **By level, and the tested members**: the tables at the end give these readings by level for the two held-out sets in both readings, and every reading of the tested members by level and overall.
- **The cap and the bursts**: the cap acted on about 2% of the steps of each run (1,805 to 2,154 of 102,400), and 136 to 233 steps were bursts. No run's loss stayed at the level of the starting field, as seed 0 of G-C2.1 had.

**What it does not show**
- Everything the pre-specifications of G-C2.1 and G-C2.2 list.
- Whether the recipe is needed, and the share of each of the two changes: there is no arm without the recipe, and the old training was not rerun. That no seed of three collapsed here, where one of three collapsed for good in G-C2.1, is on other seeds, another host and other held-out members.
- Anything beyond 8 mm, or for members outside the family. Within the family the reading is weakest for a yield stress below 300 MPa at the levels of 6 and 8 mm; the records show this association, not its cause.

## Consequences

- The route chosen on 11 November 2026, the same problem with a changed method, ends with a PASS. G-C2.1's FAIL stands beside it.
- Outside this repository the result is stated with its reading: the force is read after the condensation, and the raw reading, which misses C2 at 10.5%, is given beside it.
- The members with a low yield stress at large levels are the open weakness. Any work on it, and any next stage, is pre-specified anew.

## Numbers

Generated by `audit/c22_write_verdict.py` from `records/c22/return/` and `records/c22/audit/`. The distance is $\lvert F/F^*(e) - 1\rvert$, the judged error; a signed distance is $F/F^*(e) - 1$. A signed value below zero that rounds to zero is printed as -0.00%.

### Criteria (condensed reading; 64 fresh held-out members at seven levels, 448 pairs a seed)

**Condensed reading (judged)**

| Seed | Median | 90th percentile | Largest | Pairs above 5% | Pairs above 10% | Members with a pair above 10% | Infinite |
|---|---|---|---|---|---|---|---|
| 5 | 0.828% | 3.664% | 50.1% | 26 | 6 | 4 | 0 |
| 6 | 0.797% | 3.766% | 68.6% | 24 | 5 | 3 | 0 |
| 7 | 0.782% | 3.656% | 51.0% | 25 | 6 | 3 | 0 |
| Median over the seeds | 0.797% | 3.664% | | | | | |

C1: 0.797% against 5%. C2: 3.664% against 10%. Returned: C1 0.007972382816471169, C2 0.03663936677608451, PASS.

**Raw reading (reported, not judged)**

| Seed | Median | 90th percentile | Largest | Pairs above 5% | Pairs above 10% | Members with a pair above 10% | Infinite |
|---|---|---|---|---|---|---|---|
| 5 | 1.445% | 10.944% | 183.4% | 83 | 47 | 30 | 0 |
| 6 | 1.334% | 10.471% | 164.0% | 84 | 48 | 31 | 0 |
| 7 | 1.364% | 10.543% | 176.2% | 82 | 48 | 30 | 0 |
| Median over the seeds | 1.364% | 10.543% | | | | | |

What C1 and C2 would be for the raw reading: 1.364% and 10.543% (returned: 0.013638353687949134 and 0.10542708497194714).

### The two reported sets, both readings

| Set | Reading | Seed | Pairs | Median | 90th percentile | Largest | Pairs above 5% | Pairs above 10% | Members with a pair above 10% |
|---|---|---|---|---|---|---|---|---|---|
| held-out of G-C2.1 | condensed | 5 | 448 | 0.927% | 3.379% | 29.5% | 22 | 6 | 5 |
| held-out of G-C2.1 | condensed | 6 | 448 | 0.956% | 3.341% | 27.3% | 19 | 3 | 2 |
| held-out of G-C2.1 | condensed | 7 | 448 | 0.993% | 3.201% | 14.1% | 19 | 5 | 4 |
| held-out of G-C2.1 | raw | 5 | 448 | 1.451% | 8.716% | 97.7% | 77 | 37 | 23 |
| held-out of G-C2.1 | raw | 6 | 448 | 1.452% | 7.736% | 85.3% | 74 | 35 | 22 |
| held-out of G-C2.1 | raw | 7 | 448 | 1.387% | 7.634% | 93.0% | 79 | 33 | 20 |
| tested | condensed | 5 | 28 | 0.942% | 1.777% | 2.9% | 0 | 0 | 0 |
| tested | condensed | 6 | 28 | 0.844% | 1.881% | 2.5% | 0 | 0 | 0 |
| tested | condensed | 7 | 28 | 0.771% | 1.615% | 2.5% | 0 | 0 | 0 |
| tested | raw | 5 | 28 | 0.687% | 5.046% | 6.8% | 4 | 0 | 0 |
| tested | raw | 6 | 28 | 1.255% | 4.091% | 5.5% | 2 | 0 | 0 |
| tested | raw | 7 | 28 | 0.912% | 4.250% | 6.5% | 1 | 0 | 0 |

### The distance by level, fresh held-out members (64 a level)

**Median distance**

| Reading | Seed | 0.5 mm | 1 mm | 2 mm | 3 mm | 4 mm | 6 mm | 8 mm |
|---|---|---|---|---|---|---|---|---|
| condensed | 5 | 0.48% | 0.42% | 0.53% | 1.05% | 1.10% | 1.12% | 2.21% |
| condensed | 6 | 0.49% | 0.42% | 0.49% | 1.07% | 1.35% | 1.23% | 2.02% |
| condensed | 7 | 0.56% | 0.41% | 0.42% | 1.17% | 0.95% | 1.22% | 1.97% |
| raw | 5 | 1.12% | 0.85% | 1.37% | 1.27% | 1.19% | 1.55% | 9.43% |
| raw | 6 | 1.09% | 0.73% | 1.04% | 1.33% | 1.55% | 1.60% | 9.91% |
| raw | 7 | 1.16% | 0.84% | 1.25% | 1.29% | 1.21% | 2.08% | 9.16% |

**90th percentile of the distance**

| Reading | Seed | 0.5 mm | 1 mm | 2 mm | 3 mm | 4 mm | 6 mm | 8 mm |
|---|---|---|---|---|---|---|---|---|
| condensed | 5 | 1.24% | 1.00% | 2.80% | 3.06% | 3.08% | 4.89% | 6.61% |
| condensed | 6 | 1.05% | 1.08% | 3.06% | 3.12% | 3.62% | 4.88% | 6.60% |
| condensed | 7 | 1.18% | 0.93% | 3.54% | 3.13% | 3.71% | 5.15% | 7.50% |
| raw | 5 | 2.55% | 3.12% | 5.31% | 3.66% | 4.44% | 21.98% | 42.87% |
| raw | 6 | 3.02% | 1.89% | 4.90% | 4.01% | 5.27% | 17.82% | 43.59% |
| raw | 7 | 2.83% | 2.16% | 3.52% | 3.88% | 5.19% | 21.36% | 42.88% |

**Pairs above 10%**

| Reading | Seed | 0.5 mm | 1 mm | 2 mm | 3 mm | 4 mm | 6 mm | 8 mm |
|---|---|---|---|---|---|---|---|---|
| condensed | 5 | 0 | 0 | 0 | 0 | 1 | 1 | 4 |
| condensed | 6 | 0 | 0 | 0 | 0 | 1 | 1 | 3 |
| condensed | 7 | 0 | 0 | 0 | 1 | 1 | 1 | 3 |
| raw | 5 | 1 | 0 | 0 | 1 | 2 | 13 | 30 |
| raw | 6 | 0 | 0 | 1 | 1 | 3 | 12 | 31 |
| raw | 7 | 1 | 0 | 0 | 1 | 3 | 13 | 30 |

**Median signed distance**

| Reading | Seed | 0.5 mm | 1 mm | 2 mm | 3 mm | 4 mm | 6 mm | 8 mm |
|---|---|---|---|---|---|---|---|---|
| condensed | 5 | +0.48% | +0.42% | +0.44% | +0.97% | +1.10% | +1.12% | +2.21% |
| condensed | 6 | +0.49% | +0.41% | +0.41% | +1.01% | +1.35% | +1.23% | +2.02% |
| condensed | 7 | +0.55% | +0.41% | +0.37% | +0.97% | +0.95% | +1.22% | +1.97% |
| raw | 5 | +0.17% | -0.13% | +0.95% | +0.55% | +0.70% | +0.99% | +9.43% |
| raw | 6 | +0.11% | +0.22% | +0.73% | +0.46% | +0.86% | +0.68% | +9.91% |
| raw | 7 | +0.06% | +0.37% | +0.59% | +0.54% | +0.93% | +0.77% | +9.16% |

### The distance at 8 mm and the yield stress (fresh held-out members)

17 members have a yield stress below 300 MPa and 47 at or above it.

| Reading | Seed | Median, below | 90th percentile, below | Above 10%, below | Median, at or above | 90th percentile, at or above | Above 10%, at or above |
|---|---|---|---|---|---|---|---|
| condensed | 5 | 5.92% | 17.91% | 4 | 1.57% | 4.82% | 0 |
| condensed | 6 | 6.34% | 13.79% | 3 | 1.69% | 4.21% | 0 |
| condensed | 7 | 5.84% | 12.01% | 3 | 1.57% | 3.36% | 0 |
| raw | 5 | 34.05% | 70.58% | 13 | 8.38% | 23.58% | 17 |
| raw | 6 | 29.77% | 68.65% | 12 | 8.69% | 18.24% | 19 |
| raw | 7 | 33.22% | 68.88% | 11 | 8.13% | 20.76% | 19 |

### The pairs above 10% in the condensed reading, by member and level

Signed distances of seeds 5, 6 and 7; a pair is listed if any seed is above 10% in the condensed reading.

**Fresh held-out members**

| Member | $t_f$ (mm) | $f_y$ (MPa) | $w$ (mm) | $n$ (mm) | Level | Condensed, seeds 5, 6, 7 | Raw, seeds 5, 6, 7 | Amplitude, seeds 5, 6, 7 |
|---|---|---|---|---|---|---|---|---|
| eval_0001 | 8.6 | 239 | 102 | 26 | 3 mm | +7.7%, +8.7%, +10.4% | +28.3%, +23.4%, +23.3% | 1.072, 1.051, 1.044 |
| eval_0001 | 8.6 | 239 | 102 | 26 | 4 mm | +12.1%, +16.6%, +13.7% | +57.3%, +48.4%, +52.0% | 1.118, 1.081, 1.099 |
| eval_0001 | 8.6 | 239 | 102 | 26 | 6 mm | +26.4%, +33.1%, +25.0% | +119.6%, +106.0%, +113.2% | 1.168, 1.128, 1.157 |
| eval_0001 | 8.6 | 239 | 102 | 26 | 8 mm | +50.1%, +68.6%, +51.0% | +183.4%, +164.0%, +176.2% | 1.187, 1.131, 1.174 |
| eval_0009 | 17.0 | 238 | 99 | 24 | 8 mm | +13.7%, +8.2%, +8.9% | +64.6%, +69.4%, +64.6% | 1.148, 1.180, 1.162 |
| eval_0016 | 14.4 | 289 | 77 | 38 | 8 mm | +21.8%, +8.9%, +10.5% | +41.2%, +46.3%, +43.1% | 1.069, 1.135, 1.117 |
| eval_0044 | 10.5 | 266 | 76 | 29 | 8 mm | +6.5%, +11.1%, +9.2% | +42.1%, +35.7%, +35.9% | 1.112, 1.076, 1.083 |
| eval_0062 | 19.7 | 273 | 91 | 39 | 8 mm | +15.3%, +17.7%, +14.2% | +43.2%, +43.8%, +42.4% | 1.102, 1.095, 1.103 |

8 member and level pairs in 5 members.

**Held-out members of G-C2.1**

| Member | $t_f$ (mm) | $f_y$ (MPa) | $w$ (mm) | $n$ (mm) | Level | Condensed, seeds 5, 6, 7 | Raw, seeds 5, 6, 7 | Amplitude, seeds 5, 6, 7 |
|---|---|---|---|---|---|---|---|---|
| former_0010 | 16.7 | 282 | 95 | 40 | 8 mm | +29.5%, +8.7%, +11.9% | +40.1%, +43.9%, +40.0% | 1.038, 1.128, 1.101 |
| former_0017 | 17.8 | 412 | 77 | 21 | 8 mm | +11.8%, +11.5%, +12.0% | +6.5%, +7.1%, +6.6% | 0.942, 0.952, 0.941 |
| former_0038 | 9.9 | 242 | 78 | 34 | 6 mm | +11.5%, +13.4%, +9.1% | +17.2%, +15.6%, +13.5% | 1.023, 1.009, 1.018 |
| former_0038 | 9.9 | 242 | 78 | 34 | 8 mm | +15.5%, +27.3%, +13.9% | +42.6%, +37.3%, +39.0% | 1.082, 1.030, 1.075 |
| former_0043 | 15.3 | 249 | 77 | 38 | 6 mm | +7.8%, +7.6%, +10.2% | +35.1%, +34.2%, +35.9% | 1.120, 1.116, 1.113 |
| former_0043 | 15.3 | 249 | 77 | 38 | 8 mm | +19.8%, +9.9%, +14.1% | +57.7%, +60.5%, +57.5% | 1.122, 1.165, 1.140 |
| former_0046 | 9.8 | 265 | 105 | 22 | 8 mm | +10.0%, +3.6%, +4.7% | +80.5%, +69.0%, +76.4% | 1.153, 1.140, 1.155 |

7 member and level pairs in 5 members.

### The other readings (medians over the pairs of a set; reported, not judged)

**Fresh held-out members**

| Reading | Seed | Force at the same $D$, absolute | Force at the same $D$, signed | End displacement, signed | Stress reading of the force, signed | Energy gap | Certified bound on the force error | Bolt force, signed | Displacement, relative $L^2$ | Contact IoU | Plastic IoU | Within the bound |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| condensed | 5 | 0.435% | +0.316% | -0.714% | +0.157% | 0.218% | 6.159% | +0.000% | 1.514% | 0.971 | 0.858 | 100.0% |
| condensed | 6 | 0.368% | +0.283% | -0.713% | +0.200% | 0.205% | 5.914% | +0.000% | 1.617% | 0.972 | 0.856 | 100.0% |
| condensed | 7 | 0.351% | +0.320% | -0.691% | +0.262% | 0.194% | 5.673% | +0.001% | 1.539% | 0.973 | 0.860 | 100.0% |
| raw | 5 | 0.603% | +0.223% | -0.831% | +0.396% | 0.222% | 6.209% | +0.000% | 2.492% | 0.971 | 0.859 | 100.0% |
| raw | 6 | 0.549% | +0.224% | -0.843% | +0.437% | 0.211% | 6.020% | +0.000% | 2.336% | 0.972 | 0.860 | 100.0% |
| raw | 7 | 0.557% | +0.228% | -0.945% | +0.539% | 0.197% | 5.712% | +0.001% | 2.340% | 0.974 | 0.862 | 100.0% |

**Held-out members of G-C2.1**

| Reading | Seed | Force at the same $D$, absolute | Force at the same $D$, signed | End displacement, signed | Stress reading of the force, signed | Energy gap | Certified bound on the force error | Bolt force, signed | Displacement, relative $L^2$ | Contact IoU | Plastic IoU | Within the bound |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| condensed | 5 | 0.367% | +0.250% | -0.789% | +0.260% | 0.213% | 6.190% | +0.000% | 1.994% | 0.972 | 0.837 | 100.0% |
| condensed | 6 | 0.397% | +0.237% | -0.729% | +0.051% | 0.206% | 5.904% | +0.000% | 1.791% | 0.975 | 0.856 | 100.0% |
| condensed | 7 | 0.402% | +0.300% | -0.759% | +0.149% | 0.199% | 5.752% | +0.001% | 1.904% | 0.975 | 0.851 | 100.0% |
| raw | 5 | 0.561% | +0.167% | -0.721% | +0.766% | 0.228% | 6.314% | +0.000% | 2.815% | 0.974 | 0.837 | 100.0% |
| raw | 6 | 0.549% | +0.111% | -0.617% | +0.580% | 0.208% | 6.022% | +0.001% | 2.615% | 0.975 | 0.853 | 100.0% |
| raw | 7 | 0.504% | +0.117% | -0.572% | +0.704% | 0.203% | 5.793% | +0.001% | 2.639% | 0.974 | 0.848 | 100.0% |

### The other readings by level (medians over the 64 members of a set at each level; reported, not judged)

Of the 5,544 returned rows, 0 have an infinite distance and 0 a field that the reference code could not evaluate.

**Fresh held-out members**

| Reading | Seed | $D$ (mm) | Force at the same $D$, signed | Absolute | Certified bound | Within the bound | End displacement, signed | Stress reading of the force, signed | Energy gap | Contact IoU | Plastic IoU | Bolt force, signed | Displacement, relative $L^2$ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| condensed | 5 | 0.5 | +0.07% | 0.07% | 3.78% | 64 of 64 | -0.49% | -0.47% | 0.075% | 0.963 | 1.000 | +0.24% | 0.97% |
| condensed | 5 | 1 | +0.06% | 0.07% | 2.95% | 64 of 64 | -0.45% | -0.65% | 0.067% | 0.979 | 1.000 | +0.00% | 0.88% |
| condensed | 5 | 2 | +0.08% | 0.10% | 3.40% | 64 of 64 | -0.42% | +0.66% | 0.094% | 0.964 | 0.818 | +0.00% | 1.14% |
| condensed | 5 | 3 | +0.68% | 0.69% | 5.64% | 64 of 64 | -1.54% | -0.02% | 0.214% | 0.931 | 0.821 | +0.00% | 3.17% |
| condensed | 5 | 4 | +0.83% | 0.83% | 9.43% | 64 of 64 | -1.23% | +0.30% | 0.411% | 1.000 | 0.845 | -0.00% | 2.11% |
| condensed | 5 | 6 | +1.05% | 1.05% | 13.01% | 64 of 64 | -0.76% | +0.59% | 0.501% | 1.000 | 0.828 | +0.00% | 1.47% |
| condensed | 5 | 8 | +2.05% | 2.05% | 20.96% | 64 of 64 | -0.98% | +6.59% | 1.060% | 1.000 | 0.732 | -0.00% | 2.67% |
| condensed | 6 | 0.5 | +0.07% | 0.07% | 3.62% | 64 of 64 | -0.49% | -0.16% | 0.074% | 0.966 | 1.000 | +0.18% | 1.16% |
| condensed | 6 | 1 | +0.07% | 0.08% | 2.88% | 64 of 64 | -0.40% | +0.04% | 0.062% | 0.979 | 1.000 | +0.14% | 1.02% |
| condensed | 6 | 2 | +0.08% | 0.09% | 3.28% | 64 of 64 | -0.40% | +0.25% | 0.083% | 0.963 | 0.829 | +0.00% | 1.15% |
| condensed | 6 | 3 | +0.69% | 0.69% | 5.56% | 64 of 64 | -1.71% | +1.67% | 0.213% | 0.936 | 0.825 | +0.00% | 3.14% |
| condensed | 6 | 4 | +1.05% | 1.05% | 8.85% | 64 of 64 | -1.23% | +0.27% | 0.382% | 1.000 | 0.837 | +0.00% | 2.12% |
| condensed | 6 | 6 | +1.18% | 1.18% | 12.99% | 64 of 64 | -0.76% | -0.31% | 0.519% | 1.000 | 0.829 | +0.00% | 2.17% |
| condensed | 6 | 8 | +1.91% | 1.91% | 20.60% | 64 of 64 | -0.93% | +3.36% | 1.007% | 1.000 | 0.732 | -0.00% | 3.75% |
| condensed | 7 | 0.5 | +0.06% | 0.07% | 3.27% | 64 of 64 | -0.52% | +0.04% | 0.062% | 0.965 | 1.000 | +0.16% | 1.32% |
| condensed | 7 | 1 | +0.06% | 0.06% | 2.72% | 64 of 64 | -0.41% | +0.19% | 0.059% | 0.983 | 1.000 | -0.02% | 1.08% |
| condensed | 7 | 2 | +0.07% | 0.09% | 3.35% | 64 of 64 | -0.36% | +0.40% | 0.090% | 0.967 | 0.798 | +0.25% | 0.94% |
| condensed | 7 | 3 | +0.65% | 0.65% | 5.28% | 64 of 64 | -1.71% | +0.29% | 0.200% | 0.933 | 0.833 | +0.00% | 3.38% |
| condensed | 7 | 4 | +0.83% | 0.83% | 8.92% | 64 of 64 | -1.16% | -0.36% | 0.383% | 1.000 | 0.842 | -0.00% | 1.64% |
| condensed | 7 | 6 | +1.12% | 1.12% | 12.87% | 64 of 64 | -0.75% | -0.05% | 0.528% | 1.000 | 0.831 | +0.00% | 1.95% |
| condensed | 7 | 8 | +1.88% | 1.88% | 19.77% | 64 of 64 | -0.87% | +7.03% | 0.964% | 1.000 | 0.740 | -0.00% | 2.78% |
| raw | 5 | 0.5 | +0.03% | 0.15% | 3.80% | 64 of 64 | -0.15% | +0.24% | 0.076% | 0.957 | 1.000 | +0.25% | 1.72% |
| raw | 5 | 1 | -0.02% | 0.13% | 2.99% | 64 of 64 | +0.13% | -0.18% | 0.068% | 0.980 | 1.000 | +0.11% | 1.26% |
| raw | 5 | 2 | +0.21% | 0.34% | 3.67% | 64 of 64 | -0.98% | +0.56% | 0.104% | 0.963 | 0.799 | +0.00% | 1.96% |
| raw | 5 | 3 | +0.30% | 0.79% | 5.70% | 64 of 64 | -0.75% | +0.22% | 0.216% | 0.925 | 0.815 | +0.00% | 3.66% |
| raw | 5 | 4 | +0.62% | 1.04% | 9.53% | 64 of 64 | -1.15% | +0.40% | 0.423% | 1.000 | 0.837 | -0.00% | 3.15% |
| raw | 5 | 6 | +0.84% | 1.40% | 13.45% | 64 of 64 | -0.78% | +0.66% | 0.542% | 1.000 | 0.832 | +0.00% | 2.61% |
| raw | 5 | 8 | +8.56% | 8.56% | 22.32% | 64 of 64 | -4.98% | +3.84% | 1.169% | 1.000 | 0.753 | -0.01% | 7.06% |
| raw | 6 | 0.5 | +0.02% | 0.15% | 3.66% | 64 of 64 | -0.11% | +0.19% | 0.075% | 0.966 | 1.000 | +0.17% | 1.45% |
| raw | 6 | 1 | +0.04% | 0.12% | 2.88% | 64 of 64 | -0.22% | +0.19% | 0.063% | 0.980 | 1.000 | +0.12% | 1.14% |
| raw | 6 | 2 | +0.16% | 0.25% | 3.34% | 64 of 64 | -0.80% | +0.47% | 0.086% | 0.963 | 0.815 | +0.00% | 1.79% |
| raw | 6 | 3 | +0.30% | 0.79% | 5.61% | 64 of 64 | -1.03% | +2.06% | 0.218% | 0.940 | 0.820 | +0.00% | 3.73% |
| raw | 6 | 4 | +0.70% | 1.29% | 8.86% | 64 of 64 | -1.30% | +0.10% | 0.406% | 1.000 | 0.841 | +0.00% | 2.89% |
| raw | 6 | 6 | +0.58% | 1.54% | 13.07% | 64 of 64 | -0.54% | -0.18% | 0.564% | 1.000 | 0.826 | +0.00% | 2.74% |
| raw | 6 | 8 | +8.92% | 8.92% | 22.48% | 64 of 64 | -5.34% | +1.02% | 1.170% | 1.000 | 0.764 | -0.01% | 8.13% |
| raw | 7 | 0.5 | +0.01% | 0.16% | 3.31% | 64 of 64 | -0.06% | +0.34% | 0.064% | 0.967 | 1.000 | +0.17% | 1.69% |
| raw | 7 | 1 | +0.05% | 0.12% | 2.76% | 64 of 64 | -0.34% | +0.38% | 0.061% | 0.983 | 1.000 | +0.11% | 1.39% |
| raw | 7 | 2 | +0.14% | 0.25% | 3.37% | 64 of 64 | -0.77% | +0.72% | 0.092% | 0.969 | 0.793 | +0.36% | 1.71% |
| raw | 7 | 3 | +0.32% | 0.70% | 5.43% | 64 of 64 | -1.05% | +0.66% | 0.207% | 0.929 | 0.838 | +0.00% | 3.38% |
| raw | 7 | 4 | +0.72% | 0.94% | 8.94% | 64 of 64 | -1.29% | -0.66% | 0.391% | 1.000 | 0.838 | -0.00% | 2.41% |
| raw | 7 | 6 | +0.66% | 2.00% | 13.26% | 64 of 64 | -0.54% | -0.07% | 0.559% | 1.000 | 0.833 | +0.00% | 2.72% |
| raw | 7 | 8 | +8.63% | 8.63% | 20.73% | 64 of 64 | -5.07% | +3.67% | 1.099% | 1.000 | 0.766 | -0.00% | 7.19% |

**Held-out members of G-C2.1**

| Reading | Seed | $D$ (mm) | Force at the same $D$, signed | Absolute | Certified bound | Within the bound | End displacement, signed | Stress reading of the force, signed | Energy gap | Contact IoU | Plastic IoU | Bolt force, signed | Displacement, relative $L^2$ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| condensed | 5 | 0.5 | +0.07% | 0.07% | 3.34% | 64 of 64 | -0.54% | -0.37% | 0.073% | 0.975 | 1.000 | +0.15% | 1.23% |
| condensed | 5 | 1 | +0.07% | 0.08% | 2.98% | 64 of 64 | -0.51% | -0.30% | 0.067% | 0.974 | 1.000 | -0.01% | 1.20% |
| condensed | 5 | 2 | +0.11% | 0.11% | 3.17% | 64 of 64 | -0.56% | +0.99% | 0.082% | 0.968 | 0.795 | -0.30% | 1.50% |
| condensed | 5 | 3 | +0.32% | 0.65% | 4.87% | 64 of 64 | -0.99% | -0.69% | 0.189% | 0.953 | 0.797 | +0.00% | 3.69% |
| condensed | 5 | 4 | +1.21% | 1.21% | 8.64% | 64 of 64 | -1.68% | -0.12% | 0.438% | 1.000 | 0.794 | -0.00% | 2.81% |
| condensed | 5 | 6 | +1.22% | 1.22% | 13.23% | 64 of 64 | -0.82% | +1.21% | 0.636% | 1.000 | 0.813 | +0.01% | 2.81% |
| condensed | 5 | 8 | +1.86% | 1.86% | 20.61% | 64 of 64 | -0.97% | +4.87% | 1.090% | 1.000 | 0.802 | -0.00% | 5.01% |
| condensed | 6 | 0.5 | +0.07% | 0.07% | 3.29% | 64 of 64 | -0.47% | -0.63% | 0.072% | 0.978 | 1.000 | +0.17% | 1.13% |
| condensed | 6 | 1 | +0.06% | 0.07% | 2.92% | 64 of 64 | -0.39% | -0.43% | 0.066% | 0.972 | 1.000 | +0.15% | 0.98% |
| condensed | 6 | 2 | +0.07% | 0.09% | 2.97% | 64 of 64 | -0.43% | +0.10% | 0.072% | 0.982 | 0.831 | +0.07% | 1.34% |
| condensed | 6 | 3 | +0.58% | 0.68% | 4.33% | 64 of 64 | -1.37% | +0.20% | 0.142% | 0.956 | 0.796 | +0.00% | 2.71% |
| condensed | 6 | 4 | +1.18% | 1.18% | 8.70% | 64 of 64 | -1.57% | +0.39% | 0.398% | 1.000 | 0.807 | -0.00% | 2.74% |
| condensed | 6 | 6 | +1.21% | 1.26% | 13.91% | 64 of 64 | -0.82% | +1.54% | 0.635% | 0.978 | 0.816 | +0.00% | 4.19% |
| condensed | 6 | 8 | +1.73% | 1.73% | 20.93% | 64 of 64 | -0.84% | +4.26% | 1.042% | 1.000 | 0.832 | -0.00% | 6.07% |
| condensed | 7 | 0.5 | +0.08% | 0.08% | 3.07% | 64 of 64 | -0.58% | -0.24% | 0.064% | 0.977 | 1.000 | +0.08% | 1.32% |
| condensed | 7 | 1 | +0.06% | 0.06% | 2.71% | 64 of 64 | -0.46% | -0.11% | 0.056% | 0.975 | 1.000 | -0.15% | 0.92% |
| condensed | 7 | 2 | +0.07% | 0.08% | 2.91% | 64 of 64 | -0.43% | +0.18% | 0.070% | 0.973 | 0.808 | +0.31% | 1.14% |
| condensed | 7 | 3 | +0.41% | 0.61% | 4.47% | 64 of 64 | -1.33% | +0.10% | 0.158% | 0.957 | 0.794 | +0.00% | 3.24% |
| condensed | 7 | 4 | +1.19% | 1.19% | 9.02% | 64 of 64 | -1.61% | +0.35% | 0.410% | 1.000 | 0.805 | -0.00% | 2.72% |
| condensed | 7 | 6 | +1.30% | 1.31% | 13.88% | 64 of 64 | -0.83% | +0.63% | 0.645% | 0.925 | 0.813 | +0.00% | 3.06% |
| condensed | 7 | 8 | +1.71% | 1.71% | 21.05% | 64 of 64 | -0.82% | +3.30% | 1.092% | 0.865 | 0.805 | -0.00% | 5.97% |
| raw | 5 | 0.5 | +0.03% | 0.13% | 3.37% | 64 of 64 | -0.22% | +0.48% | 0.076% | 0.976 | 1.000 | +0.14% | 1.32% |
| raw | 5 | 1 | -0.03% | 0.12% | 3.04% | 64 of 64 | +0.14% | +0.38% | 0.069% | 0.977 | 1.000 | +0.02% | 1.44% |
| raw | 5 | 2 | +0.21% | 0.26% | 3.23% | 64 of 64 | -1.11% | +0.82% | 0.086% | 0.972 | 0.784 | -0.40% | 2.14% |
| raw | 5 | 3 | +0.12% | 0.71% | 5.15% | 64 of 64 | -0.35% | +0.93% | 0.201% | 0.949 | 0.777 | +0.00% | 3.89% |
| raw | 5 | 4 | +0.66% | 1.07% | 8.94% | 64 of 64 | -1.14% | +0.09% | 0.441% | 1.000 | 0.781 | -0.00% | 4.31% |
| raw | 5 | 6 | +0.08% | 1.73% | 13.77% | 64 of 64 | -0.08% | +1.79% | 0.692% | 1.000 | 0.812 | +0.01% | 5.34% |
| raw | 5 | 8 | +6.35% | 6.35% | 21.19% | 64 of 64 | -3.59% | +3.85% | 1.103% | 1.000 | 0.818 | -0.01% | 7.51% |
| raw | 6 | 0.5 | +0.01% | 0.12% | 3.34% | 64 of 64 | -0.12% | +0.01% | 0.075% | 0.976 | 1.000 | +0.19% | 1.43% |
| raw | 6 | 1 | +0.02% | 0.12% | 2.94% | 64 of 64 | -0.10% | +0.04% | 0.070% | 0.973 | 1.000 | +0.22% | 1.28% |
| raw | 6 | 2 | +0.10% | 0.22% | 3.07% | 64 of 64 | -0.64% | -0.11% | 0.075% | 0.981 | 0.827 | +0.22% | 1.80% |
| raw | 6 | 3 | +0.01% | 0.67% | 4.53% | 64 of 64 | +0.11% | +1.45% | 0.170% | 0.956 | 0.784 | +0.00% | 3.26% |
| raw | 6 | 4 | +0.59% | 1.15% | 8.95% | 64 of 64 | -1.06% | +0.92% | 0.402% | 1.000 | 0.795 | +0.00% | 3.53% |
| raw | 6 | 6 | +0.07% | 1.73% | 14.39% | 64 of 64 | -0.09% | +2.00% | 0.659% | 0.984 | 0.812 | +0.01% | 6.59% |
| raw | 6 | 8 | +6.23% | 6.23% | 21.23% | 64 of 64 | -3.35% | +3.15% | 1.089% | 1.000 | 0.834 | -0.00% | 9.07% |
| raw | 7 | 0.5 | +0.03% | 0.15% | 3.17% | 64 of 64 | -0.23% | +0.70% | 0.066% | 0.975 | 1.000 | +0.06% | 1.77% |
| raw | 7 | 1 | -0.01% | 0.12% | 2.78% | 64 of 64 | +0.04% | +0.64% | 0.058% | 0.974 | 1.000 | +0.02% | 1.28% |
| raw | 7 | 2 | +0.11% | 0.22% | 2.91% | 64 of 64 | -0.65% | +0.30% | 0.070% | 0.980 | 0.806 | +0.11% | 1.92% |
| raw | 7 | 3 | +0.09% | 0.81% | 4.75% | 64 of 64 | -0.29% | +1.27% | 0.177% | 0.956 | 0.788 | +0.00% | 4.00% |
| raw | 7 | 4 | +0.51% | 1.26% | 9.25% | 64 of 64 | -1.09% | +0.43% | 0.423% | 1.000 | 0.804 | +0.00% | 2.96% |
| raw | 7 | 6 | +0.22% | 1.52% | 14.01% | 64 of 64 | -0.29% | +0.94% | 0.659% | 0.925 | 0.812 | +0.00% | 5.86% |
| raw | 7 | 8 | +6.17% | 6.17% | 21.25% | 64 of 64 | -3.37% | +1.72% | 1.122% | 0.872 | 0.816 | -0.00% | 8.84% |

### The amplitudes of the condensed reading

The energies are those of the training energy in float32, of the raw and of the condensed field; their differences are relative to the raw field's energy.

| Seed | Set | Fields | Smallest | Median | Largest | On a bound | Tolerance not met | Largest relative slope left | Fields whose energy the condensation raised | Largest rise | Median fall |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | fresh held-out | 448 | 0.811 | 1.0018 | 1.187 | 0 | 5 | 2.9e-04 | 0 | 0 | 2.9e-05 |
| 5 | held-out of G-C2.1 | 448 | 0.909 | 0.9981 | 1.182 | 0 | 11 | 2.9e-04 | 1 | 9.7e-08 | 3.5e-05 |
| 5 | tested | 28 | 0.933 | 0.9916 | 1.025 | 0 | 0 | 6.8e-05 | 0 | 0 | 4.9e-05 |
| 6 | fresh held-out | 448 | 0.802 | 1.0004 | 1.180 | 0 | 9 | 3.5e-04 | 1 | 1.1e-07 | 3.0e-05 |
| 6 | held-out of G-C2.1 | 448 | 0.904 | 0.9978 | 1.165 | 0 | 17 | 2.3e-04 | 0 | 0 | 4.0e-05 |
| 6 | tested | 28 | 0.945 | 0.9926 | 1.022 | 0 | 0 | 9.8e-05 | 0 | 0 | 4.6e-05 |
| 7 | fresh held-out | 448 | 0.807 | 1.0012 | 1.174 | 0 | 11 | 2.9e-04 | 0 | 0 | 3.1e-05 |
| 7 | held-out of G-C2.1 | 448 | 0.919 | 0.9973 | 1.173 | 0 | 8 | 2.9e-04 | 0 | 0 | 3.9e-05 |
| 7 | tested | 28 | 0.931 | 0.9930 | 1.026 | 0 | 0 | 3.9e-05 | 0 | 0 | 6.1e-05 |

### Training

| Seed | Mean loss, epochs 1 to 10 | Mean loss, epochs 191 to 200 | Largest epoch loss | Capped steps | Bursts | Hours of training | Seconds a step: least, median, most | Resumed from epoch | Peak GPU memory (GiB) |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 10.5567 | 10.3639 | 10.6239 | 2154 | 233 | 14.08 | 0.330, 0.349, 0.828 | 75 | 3.52 |
| 6 | 10.5488 | 10.3448 | 10.6288 | 1805 | 136 | 12.70 | 0.348, 0.363, 0.833 | none | 3.52 |
| 7 | 10.5728 | 10.3608 | 10.6314 | 2000 | 218 | 12.55 | 0.351, 0.367, 0.753 | none | 3.52 |

### The four tested members (reported, not judged): signed distance from the curve

| Member | Reading | 0.5 mm | 1 mm | 2 mm | 3 mm | 4 mm | 6 mm | 8 mm |
|---|---|---|---|---|---|---|---|---|
| BJ_T1_preloaded | condensed | +0.5%, +0.3%, +0.3% | +0.2%, +0.2%, +0.3% | +0.2%, +0.3%, +0.1% | +0.7%, +1.1%, +0.5% | +0.8%, +0.8%, +0.8% | +1.5%, +1.8%, +1.5% | +1.7%, +2.3%, +1.7% |
| BJ_T1_preloaded | raw | +0.3%, +0.3%, +0.1% | -0.2%, +0.1%, +0.3% | +0.4%, +1.5%, +0.7% | +0.2%, +1.2%, +0.3% | +0.6%, +0.5%, -0.4% | -0.4%, -0.3%, -1.0% | +2.8%, +3.5%, +2.6% |
| BJ_T1_snug | condensed | +1.3%, +1.4%, +1.2% | +1.4%, +1.1%, +1.1% | +1.1%, +1.2%, +1.3% | -0.1%, -0.2%, -0.4% | +1.1%, +0.8%, +0.7% | +1.7%, +1.7%, +1.6% | +1.9%, +2.5%, +1.6% |
| BJ_T1_snug | raw | -0.6%, -2.1%, -0.6% | -2.8%, -1.4%, -0.5% | -0.7%, -0.2%, +0.3% | +0.1%, +0.4%, +0.8% | +1.4%, +1.1%, +1.5% | +0.6%, +0.4%, +1.5% | +5.0%, +4.9%, +4.1% |
| BJ_T2_preloaded | condensed | +0.0%, +0.4%, +0.1% | +0.3%, +0.3%, +0.5% | +0.2%, +0.9%, +0.7% | -0.1%, +0.5%, +0.5% | +0.7%, +0.7%, +0.9% | +0.9%, +0.9%, +1.0% | +1.6%, +1.1%, +1.6% |
| BJ_T2_preloaded | raw | -1.0%, -1.0%, -0.8% | -0.4%, -0.7%, +0.1% | -0.0%, +1.0%, +1.5% | -1.4%, -0.6%, -0.8% | +1.0%, +1.3%, +0.6% | -0.5%, -1.8%, -2.6% | +5.1%, +3.7%, +5.0% |
| BJ_T2_snug | condensed | +1.0%, +0.7%, +0.6% | +1.2%, +0.8%, +0.6% | +0.8%, +0.8%, +0.7% | -2.9%, -2.1%, -2.5% | +0.5%, +0.1%, +0.6% | +1.0%, +1.0%, +1.0% | +2.1%, +1.3%, +1.6% |
| BJ_T2_snug | raw | -3.3%, -3.0%, -2.6% | -6.1%, -5.2%, -4.2% | -2.5%, -2.7%, -2.9% | -4.6%, -3.5%, -4.4% | +0.1%, -0.0%, -0.5% | -0.5%, -1.3%, -1.4% | +6.8%, +5.5%, +6.5% |

Each cell gives seeds 5, 6 and 7.

**The tested members overall** (medians over each member's seven levels, and over all 28 tested pairs of a run)

| Reading | Seed | Member | Distance | Signed distance | Force at the same $D$, signed | Absolute | Certified bound | Within the bound | End displacement, signed | Stress reading of the force, signed | Energy gap | Contact IoU | Plastic IoU | Bolt force, signed | Displacement, relative $L^2$ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| condensed | 5 | BJ_T1_preloaded | 0.67% | +0.67% | +0.38% | 0.38% | 6.15% | 7 of 7 | -0.86% | -1.08% | 0.255% | 1.000 | 0.840 | +0.35% | 1.57% |
| condensed | 5 | BJ_T1_snug | 1.25% | +1.25% | +0.30% | 0.30% | 6.06% | 7 of 7 | -0.97% | -1.13% | 0.267% | 0.949 | 0.802 | +1.63% | 1.70% |
| condensed | 5 | BJ_T2_preloaded | 0.34% | +0.34% | +0.04% | 0.07% | 4.27% | 7 of 7 | -0.36% | -0.22% | 0.085% | 1.000 | 0.917 | +0.12% | 1.05% |
| condensed | 5 | BJ_T2_snug | 0.97% | +0.97% | +0.18% | 0.46% | 5.43% | 7 of 7 | -0.82% | -1.48% | 0.216% | 1.000 | 0.917 | +1.74% | 2.40% |
| condensed | 5 | all four | 0.94% | +0.88% | +0.29% | 0.34% | 5.94% | 28 of 28 | -0.85% | -0.82% | 0.242% | 1.000 | 0.886 | +0.37% | 1.58% |
| condensed | 6 | BJ_T1_preloaded | 0.81% | +0.81% | +0.62% | 0.62% | 6.17% | 7 of 7 | -1.08% | +0.52% | 0.257% | 0.986 | 0.785 | +0.16% | 1.87% |
| condensed | 6 | BJ_T1_snug | 1.16% | +1.16% | +0.29% | 0.29% | 6.29% | 7 of 7 | -1.06% | -0.52% | 0.284% | 0.923 | 0.778 | +1.46% | 1.17% |
| condensed | 6 | BJ_T2_preloaded | 0.68% | +0.68% | +0.33% | 0.33% | 3.98% | 7 of 7 | -0.71% | +2.33% | 0.081% | 1.000 | 0.944 | -0.00% | 2.15% |
| condensed | 6 | BJ_T2_snug | 0.82% | +0.79% | +0.11% | 0.12% | 4.53% | 7 of 7 | -0.65% | -0.10% | 0.170% | 1.000 | 0.924 | +0.61% | 1.58% |
| condensed | 6 | all four | 0.84% | +0.81% | +0.28% | 0.31% | 5.73% | 28 of 28 | -0.75% | +0.47% | 0.224% | 1.000 | 0.889 | +0.18% | 1.58% |
| condensed | 7 | BJ_T1_preloaded | 0.50% | +0.50% | +0.28% | 0.28% | 6.17% | 7 of 7 | -0.83% | +0.49% | 0.257% | 0.973 | 0.837 | +0.25% | 1.39% |
| condensed | 7 | BJ_T1_snug | 1.16% | +1.16% | +0.29% | 0.29% | 6.19% | 7 of 7 | -0.90% | -0.14% | 0.275% | 0.923 | 0.802 | +1.42% | 1.46% |
| condensed | 7 | BJ_T2_preloaded | 0.70% | +0.70% | +0.30% | 0.30% | 3.72% | 7 of 7 | -0.79% | +3.02% | 0.084% | 1.000 | 0.934 | -0.12% | 2.44% |
| condensed | 7 | BJ_T2_snug | 0.66% | +0.64% | +0.10% | 0.63% | 4.66% | 7 of 7 | -0.57% | -0.26% | 0.180% | 1.000 | 0.930 | +0.67% | 1.38% |
| condensed | 7 | all four | 0.77% | +0.69% | +0.29% | 0.30% | 5.66% | 28 of 28 | -0.81% | +0.60% | 0.220% | 1.000 | 0.909 | +0.04% | 1.59% |
| raw | 5 | BJ_T1_preloaded | 0.36% | +0.29% | +0.08% | 0.09% | 6.16% | 7 of 7 | -0.27% | -1.15% | 0.256% | 1.000 | 0.829 | +0.37% | 0.97% |
| raw | 5 | BJ_T1_snug | 0.74% | +0.15% | +0.08% | 0.58% | 6.16% | 7 of 7 | -0.25% | +0.39% | 0.298% | 0.949 | 0.799 | +1.72% | 2.08% |
| raw | 5 | BJ_T2_preloaded | 1.02% | -0.38% | -0.04% | 0.49% | 4.28% | 7 of 7 | +0.40% | +0.45% | 0.104% | 1.000 | 0.918 | +0.13% | 4.62% |
| raw | 5 | BJ_T2_snug | 3.27% | -2.53% | -0.45% | 0.49% | 5.88% | 7 of 7 | +2.26% | +2.22% | 0.217% | 1.000 | 0.924 | +1.74% | 4.83% |
| raw | 5 | all four | 0.69% | -0.12% | -0.02% | 0.47% | 6.11% | 28 of 28 | +0.12% | +0.37% | 0.251% | 1.000 | 0.887 | +0.38% | 2.56% |
| raw | 6 | BJ_T1_preloaded | 0.45% | +0.45% | +0.34% | 0.34% | 6.18% | 7 of 7 | -0.61% | +1.12% | 0.257% | 0.986 | 0.781 | +0.07% | 1.92% |
| raw | 6 | BJ_T1_snug | 1.14% | +0.36% | +0.22% | 0.33% | 6.31% | 7 of 7 | -0.27% | -0.70% | 0.286% | 0.923 | 0.787 | +1.58% | 1.81% |
| raw | 6 | BJ_T2_preloaded | 1.03% | -0.64% | -0.08% | 0.45% | 4.00% | 7 of 7 | +0.81% | +1.97% | 0.096% | 1.000 | 0.940 | -0.00% | 2.32% |
| raw | 6 | BJ_T2_snug | 2.98% | -2.68% | -0.44% | 0.79% | 4.87% | 7 of 7 | +2.39% | +2.74% | 0.184% | 1.000 | 0.926 | +1.74% | 3.23% |
| raw | 6 | all four | 1.25% | +0.03% | -0.01% | 0.43% | 5.84% | 28 of 28 | -0.01% | +1.66% | 0.231% | 1.000 | 0.875 | +0.12% | 2.30% |
| raw | 7 | BJ_T1_preloaded | 0.42% | +0.33% | +0.06% | 0.19% | 6.17% | 7 of 7 | -0.33% | +0.70% | 0.257% | 0.973 | 0.856 | +0.25% | 1.26% |
| raw | 7 | BJ_T1_snug | 0.76% | +0.76% | +0.43% | 0.43% | 6.27% | 7 of 7 | -1.10% | +0.01% | 0.282% | 0.923 | 0.791 | +1.43% | 1.31% |
| raw | 7 | BJ_T2_preloaded | 0.84% | +0.12% | +0.01% | 0.59% | 3.73% | 7 of 7 | -0.13% | +5.16% | 0.104% | 1.000 | 0.934 | -0.05% | 1.98% |
| raw | 7 | BJ_T2_snug | 2.94% | -2.60% | -0.50% | 0.63% | 5.29% | 7 of 7 | +2.27% | +5.86% | 0.211% | 1.000 | 0.914 | +1.74% | 3.28% |
| raw | 7 | all four | 0.91% | +0.13% | +0.02% | 0.48% | 5.68% | 28 of 28 | -0.13% | +2.03% | 0.227% | 1.000 | 0.889 | +0.05% | 2.12% |

**Every reading of the tested members, by level**

| Reading | Seed | Member | $D$ (mm) | Signed distance | Force at the same $D$, signed | Absolute | Certified bound | Within the bound | End displacement, signed | Stress reading of the force, signed | Energy gap | Contact IoU | Plastic IoU | Bolt force, signed | Displacement, relative $L^2$ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| condensed | 5 | BJ_T1_preloaded | 0.5 | +0.46% | +0.07% | 0.07% | 3.90% | 1 of 1 | -0.43% | -0.02% | 0.072% | 0.920 | 1.000 | +0.38% | 1.10% |
| condensed | 5 | BJ_T1_preloaded | 1 | +0.19% | +0.04% | 0.04% | 3.09% | 1 of 1 | -0.19% | -1.52% | 0.066% | 1.000 | 1.000 | +0.36% | 0.41% |
| condensed | 5 | BJ_T1_preloaded | 2 | +0.23% | +0.05% | 0.05% | 3.50% | 1 of 1 | -0.23% | -1.08% | 0.094% | 0.956 | 0.731 | +0.30% | 0.40% |
| condensed | 5 | BJ_T1_preloaded | 3 | +0.67% | +0.38% | 0.38% | 6.15% | 1 of 1 | -1.12% | -0.55% | 0.255% | 1.000 | 0.767 | -0.00% | 1.57% |
| condensed | 5 | BJ_T1_preloaded | 4 | +0.84% | +0.71% | 0.71% | 8.99% | 1 of 1 | -1.13% | -2.73% | 0.398% | 1.000 | 0.896 | +0.35% | 1.62% |
| condensed | 5 | BJ_T1_preloaded | 6 | +1.47% | +1.34% | 1.34% | 13.60% | 1 of 1 | -1.09% | -4.99% | 0.596% | 1.000 | 0.840 | +1.64% | 2.64% |
| condensed | 5 | BJ_T1_preloaded | 8 | +1.67% | +1.56% | 1.56% | 18.34% | 1 of 1 | -0.86% | +3.24% | 0.814% | 1.000 | 0.675 | +0.01% | 1.58% |
| condensed | 5 | BJ_T1_snug | 0.5 | +1.25% | +0.27% | 0.27% | 5.54% | 1 of 1 | -0.97% | +2.32% | 0.241% | 0.949 | 1.000 | +3.66% | 2.07% |
| condensed | 5 | BJ_T1_snug | 1 | +1.41% | +0.30% | 0.30% | 5.83% | 1 of 1 | -1.10% | -1.14% | 0.267% | 0.846 | 1.000 | +9.75% | 1.49% |
| condensed | 5 | BJ_T1_snug | 2 | +1.11% | +0.26% | 0.26% | 5.13% | 1 of 1 | -0.92% | -1.13% | 0.206% | 0.923 | 0.752 | +6.34% | 1.16% |
| condensed | 5 | BJ_T1_snug | 3 | -0.12% | -0.07% | 0.07% | 6.06% | 1 of 1 | +0.20% | -0.11% | 0.264% | 0.868 | 0.764 | +0.00% | 1.02% |
| condensed | 5 | BJ_T1_snug | 4 | +1.10% | +1.00% | 1.00% | 9.20% | 1 of 1 | -1.57% | -1.47% | 0.431% | 1.000 | 0.876 | +0.00% | 1.70% |
| condensed | 5 | BJ_T1_snug | 6 | +1.74% | +1.58% | 1.58% | 13.89% | 1 of 1 | -1.28% | -3.26% | 0.634% | 1.000 | 0.802 | +1.63% | 2.67% |
| condensed | 5 | BJ_T1_snug | 8 | +1.87% | +1.76% | 1.76% | 19.15% | 1 of 1 | -0.97% | +2.81% | 0.901% | 1.000 | 0.676 | +0.02% | 2.15% |
| condensed | 5 | BJ_T2_preloaded | 0.5 | +0.01% | +0.00% | 0.00% | 4.27% | 1 of 1 | -0.01% | -0.70% | 0.085% | 0.948 | 1.000 | +0.55% | 1.00% |
| condensed | 5 | BJ_T2_preloaded | 1 | +0.34% | +0.04% | 0.04% | 2.82% | 1 of 1 | -0.36% | -0.71% | 0.058% | 0.989 | 1.000 | +0.12% | 0.45% |
| condensed | 5 | BJ_T2_preloaded | 2 | +0.21% | +0.03% | 0.03% | 2.59% | 1 of 1 | -0.24% | +0.16% | 0.056% | 1.000 | 0.984 | +0.40% | 0.42% |
| condensed | 5 | BJ_T2_preloaded | 3 | -0.10% | -0.07% | 0.07% | 3.24% | 1 of 1 | +0.39% | -0.22% | 0.082% | 1.000 | 0.811 | +0.00% | 1.05% |
| condensed | 5 | BJ_T2_preloaded | 4 | +0.71% | +0.71% | 0.71% | 6.36% | 1 of 1 | -1.43% | +2.97% | 0.215% | 1.000 | 0.917 | -0.21% | 4.02% |
| condensed | 5 | BJ_T2_preloaded | 6 | +0.92% | +0.88% | 0.88% | 10.49% | 1 of 1 | -0.72% | -1.94% | 0.333% | 1.000 | 0.871 | +0.54% | 7.60% |
| condensed | 5 | BJ_T2_preloaded | 8 | +1.63% | +1.55% | 1.55% | 16.99% | 1 of 1 | -0.83% | +2.41% | 0.643% | 1.000 | 0.912 | -0.30% | 3.12% |
| condensed | 5 | BJ_T2_snug | 0.5 | +0.97% | +0.14% | 0.14% | 3.53% | 1 of 1 | -0.82% | -0.93% | 0.106% | 1.000 | 1.000 | +2.42% | 0.68% |
| condensed | 5 | BJ_T2_snug | 1 | +1.22% | +0.18% | 0.18% | 4.02% | 1 of 1 | -1.03% | -3.95% | 0.138% | 1.000 | 1.000 | +7.93% | 1.29% |
| condensed | 5 | BJ_T2_snug | 2 | +0.77% | +0.12% | 0.12% | 3.15% | 1 of 1 | -0.67% | -1.48% | 0.085% | 1.000 | 0.860 | +3.79% | 0.59% |
| condensed | 5 | BJ_T2_snug | 3 | -2.89% | -1.25% | 1.25% | 5.43% | 1 of 1 | +6.53% | -3.11% | 0.244% | 0.733 | 0.873 | +1.74% | 11.57% |
| condensed | 5 | BJ_T2_snug | 4 | +0.46% | +0.46% | 0.46% | 6.24% | 1 of 1 | -0.92% | +3.67% | 0.216% | 1.000 | 0.930 | -0.00% | 5.53% |
| condensed | 5 | BJ_T2_snug | 6 | +0.97% | +0.93% | 0.93% | 11.36% | 1 of 1 | -0.76% | -4.14% | 0.399% | 1.000 | 0.874 | +0.49% | 6.19% |
| condensed | 5 | BJ_T2_snug | 8 | +2.07% | +1.96% | 1.96% | 19.44% | 1 of 1 | -1.06% | +0.83% | 0.854% | 1.000 | 0.917 | -0.15% | 2.40% |
| condensed | 6 | BJ_T1_preloaded | 0.5 | +0.27% | +0.04% | 0.04% | 3.73% | 1 of 1 | -0.25% | +0.52% | 0.066% | 0.895 | 1.000 | +0.16% | 0.80% |
| condensed | 6 | BJ_T1_preloaded | 1 | +0.20% | +0.04% | 0.04% | 3.00% | 1 of 1 | -0.20% | -0.01% | 0.062% | 0.986 | 1.000 | +0.06% | 0.48% |
| condensed | 6 | BJ_T1_preloaded | 2 | +0.34% | +0.08% | 0.08% | 3.33% | 1 of 1 | -0.34% | +0.41% | 0.085% | 0.971 | 0.778 | +0.20% | 0.78% |
| condensed | 6 | BJ_T1_preloaded | 3 | +1.12% | +0.62% | 0.62% | 6.17% | 1 of 1 | -1.83% | +2.92% | 0.257% | 0.974 | 0.750 | -0.00% | 3.00% |
| condensed | 6 | BJ_T1_preloaded | 4 | +0.81% | +0.69% | 0.69% | 9.51% | 1 of 1 | -1.08% | +0.65% | 0.445% | 1.000 | 0.872 | +0.41% | 1.97% |
| condensed | 6 | BJ_T1_preloaded | 6 | +1.78% | +1.62% | 1.62% | 14.59% | 1 of 1 | -1.32% | +0.16% | 0.686% | 1.000 | 0.785 | +1.71% | 2.87% |
| condensed | 6 | BJ_T1_preloaded | 8 | +2.31% | +2.17% | 2.17% | 21.65% | 1 of 1 | -1.20% | +4.83% | 1.134% | 1.000 | 0.655 | +0.01% | 1.87% |
| condensed | 6 | BJ_T1_snug | 0.5 | +1.37% | +0.29% | 0.29% | 5.71% | 1 of 1 | -1.06% | -0.76% | 0.256% | 0.923 | 1.000 | +3.92% | 1.17% |
| condensed | 6 | BJ_T1_snug | 1 | +1.10% | +0.24% | 0.24% | 5.29% | 1 of 1 | -0.86% | -1.12% | 0.219% | 0.923 | 1.000 | +4.46% | 0.90% |
| condensed | 6 | BJ_T1_snug | 2 | +1.16% | +0.26% | 0.26% | 5.41% | 1 of 1 | -0.95% | -2.43% | 0.229% | 0.923 | 0.701 | +7.59% | 0.92% |
| condensed | 6 | BJ_T1_snug | 3 | -0.22% | -0.13% | 0.13% | 6.29% | 1 of 1 | +0.38% | -0.52% | 0.284% | 0.868 | 0.758 | +0.00% | 0.95% |
| condensed | 6 | BJ_T1_snug | 4 | +0.80% | +0.73% | 0.73% | 9.22% | 1 of 1 | -1.14% | -0.43% | 0.433% | 1.000 | 0.866 | +0.00% | 1.41% |
| condensed | 6 | BJ_T1_snug | 6 | +1.69% | +1.54% | 1.54% | 14.00% | 1 of 1 | -1.25% | -0.29% | 0.643% | 1.000 | 0.770 | +1.46% | 2.49% |
| condensed | 6 | BJ_T1_snug | 8 | +2.55% | +2.38% | 2.38% | 23.03% | 1 of 1 | -1.32% | +0.29% | 1.303% | 1.000 | 0.778 | +0.02% | 1.93% |
| condensed | 6 | BJ_T2_preloaded | 0.5 | +0.42% | +0.04% | 0.04% | 3.98% | 1 of 1 | -0.42% | +1.14% | 0.074% | 0.949 | 1.000 | +0.26% | 1.40% |
| condensed | 6 | BJ_T2_preloaded | 1 | +0.31% | +0.03% | 0.03% | 2.69% | 1 of 1 | -0.33% | +0.59% | 0.053% | 0.989 | 1.000 | +0.06% | 0.90% |
| condensed | 6 | BJ_T2_preloaded | 2 | +0.87% | +0.11% | 0.11% | 2.51% | 1 of 1 | -0.97% | +0.82% | 0.052% | 0.971 | 0.968 | -1.19% | 2.15% |
| condensed | 6 | BJ_T2_preloaded | 3 | +0.52% | +0.33% | 0.33% | 3.22% | 1 of 1 | -1.84% | +2.89% | 0.081% | 1.000 | 0.786 | -0.00% | 3.34% |
| condensed | 6 | BJ_T2_preloaded | 4 | +0.68% | +0.68% | 0.68% | 6.10% | 1 of 1 | -1.38% | +2.33% | 0.198% | 1.000 | 0.944 | -0.05% | 1.68% |
| condensed | 6 | BJ_T2_preloaded | 6 | +0.91% | +0.87% | 0.87% | 11.01% | 1 of 1 | -0.71% | +5.39% | 0.366% | 1.000 | 0.878 | +0.34% | 4.01% |
| condensed | 6 | BJ_T2_preloaded | 8 | +1.06% | +1.01% | 1.01% | 14.04% | 1 of 1 | -0.54% | +2.53% | 0.439% | 1.000 | 0.931 | -0.18% | 2.60% |
| condensed | 6 | BJ_T2_snug | 0.5 | +0.69% | +0.10% | 0.10% | 3.22% | 1 of 1 | -0.58% | -0.68% | 0.089% | 1.000 | 1.000 | +0.61% | 0.69% |
| condensed | 6 | BJ_T2_snug | 1 | +0.79% | +0.11% | 0.11% | 3.35% | 1 of 1 | -0.67% | -2.37% | 0.096% | 1.000 | 1.000 | +4.54% | 0.92% |
| condensed | 6 | BJ_T2_snug | 2 | +0.82% | +0.12% | 0.12% | 3.17% | 1 of 1 | -0.71% | -1.44% | 0.086% | 1.000 | 0.899 | +3.61% | 0.67% |
| condensed | 6 | BJ_T2_snug | 3 | -2.13% | -0.69% | 0.69% | 4.53% | 1 of 1 | +3.61% | -0.10% | 0.170% | 0.733 | 0.862 | +1.74% | 6.41% |
| condensed | 6 | BJ_T2_snug | 4 | +0.10% | +0.10% | 0.10% | 5.74% | 1 of 1 | -0.21% | +1.14% | 0.183% | 1.000 | 0.938 | +0.00% | 1.59% |
| condensed | 6 | BJ_T2_snug | 6 | +0.99% | +0.95% | 0.95% | 12.02% | 1 of 1 | -0.78% | +12.57% | 0.446% | 1.000 | 0.878 | +0.55% | 6.28% |
| condensed | 6 | BJ_T2_snug | 8 | +1.27% | +1.21% | 1.21% | 15.54% | 1 of 1 | -0.65% | +9.07% | 0.545% | 1.000 | 0.924 | +0.16% | 1.58% |
| condensed | 7 | BJ_T1_preloaded | 0.5 | +0.32% | +0.05% | 0.05% | 3.62% | 1 of 1 | -0.29% | +1.12% | 0.062% | 0.944 | 1.000 | +0.25% | 1.39% |
| condensed | 7 | BJ_T1_preloaded | 1 | +0.28% | +0.05% | 0.05% | 2.85% | 1 of 1 | -0.28% | +0.49% | 0.056% | 0.973 | 1.000 | -0.02% | 0.88% |
| condensed | 7 | BJ_T1_preloaded | 2 | +0.09% | +0.02% | 0.02% | 3.56% | 1 of 1 | -0.09% | +0.22% | 0.097% | 0.955 | 0.837 | +0.30% | 0.41% |
| condensed | 7 | BJ_T1_preloaded | 3 | +0.50% | +0.28% | 0.28% | 6.17% | 1 of 1 | -0.83% | +0.44% | 0.257% | 0.947 | 0.777 | -0.00% | 1.24% |
| condensed | 7 | BJ_T1_preloaded | 4 | +0.84% | +0.71% | 0.71% | 8.65% | 1 of 1 | -1.13% | -1.62% | 0.369% | 1.000 | 0.888 | +0.32% | 1.73% |
| condensed | 7 | BJ_T1_preloaded | 6 | +1.47% | +1.34% | 1.34% | 13.37% | 1 of 1 | -1.09% | +2.03% | 0.576% | 1.000 | 0.780 | +1.42% | 2.52% |
| condensed | 7 | BJ_T1_preloaded | 8 | +1.66% | +1.56% | 1.56% | 19.19% | 1 of 1 | -0.86% | +6.97% | 0.891% | 1.000 | 0.661 | +0.01% | 2.01% |
| condensed | 7 | BJ_T1_snug | 0.5 | +1.16% | +0.25% | 0.25% | 5.34% | 1 of 1 | -0.90% | +0.24% | 0.224% | 0.923 | 1.000 | +3.43% | 1.46% |
| condensed | 7 | BJ_T1_snug | 1 | +1.10% | +0.24% | 0.24% | 5.26% | 1 of 1 | -0.86% | -0.14% | 0.217% | 0.923 | 1.000 | +5.85% | 1.30% |
| condensed | 7 | BJ_T1_snug | 2 | +1.28% | +0.29% | 0.29% | 5.36% | 1 of 1 | -1.05% | -1.40% | 0.224% | 0.897 | 0.711 | +9.03% | 1.16% |
| condensed | 7 | BJ_T1_snug | 3 | -0.36% | -0.21% | 0.21% | 6.19% | 1 of 1 | +0.62% | -1.97% | 0.275% | 0.842 | 0.802 | +0.00% | 1.79% |
| condensed | 7 | BJ_T1_snug | 4 | +0.68% | +0.61% | 0.61% | 8.38% | 1 of 1 | -0.96% | -2.76% | 0.358% | 1.000 | 0.907 | +0.06% | 1.43% |
| condensed | 7 | BJ_T1_snug | 6 | +1.63% | +1.49% | 1.49% | 13.05% | 1 of 1 | -1.21% | -0.09% | 0.560% | 1.000 | 0.782 | +1.42% | 2.50% |
| condensed | 7 | BJ_T1_snug | 8 | +1.59% | +1.49% | 1.49% | 19.13% | 1 of 1 | -0.82% | +6.29% | 0.899% | 1.000 | 0.670 | +0.02% | 2.17% |
| condensed | 7 | BJ_T2_preloaded | 0.5 | +0.11% | +0.01% | 0.01% | 3.72% | 1 of 1 | -0.11% | +1.10% | 0.065% | 0.948 | 1.000 | +0.50% | 1.31% |
| condensed | 7 | BJ_T2_preloaded | 1 | +0.52% | +0.06% | 0.06% | 2.51% | 1 of 1 | -0.55% | +0.72% | 0.046% | 0.989 | 1.000 | -0.12% | 1.32% |
| condensed | 7 | BJ_T2_preloaded | 2 | +0.70% | +0.09% | 0.09% | 2.50% | 1 of 1 | -0.79% | +1.74% | 0.052% | 1.000 | 0.969 | -0.94% | 2.13% |
| condensed | 7 | BJ_T2_preloaded | 3 | +0.46% | +0.30% | 0.30% | 3.28% | 1 of 1 | -1.65% | +3.02% | 0.084% | 1.000 | 0.798 | -0.00% | 3.12% |
| condensed | 7 | BJ_T2_preloaded | 4 | +0.91% | +0.90% | 0.90% | 5.96% | 1 of 1 | -1.83% | +4.95% | 0.189% | 1.000 | 0.934 | -0.07% | 2.44% |
| condensed | 7 | BJ_T2_preloaded | 6 | +0.95% | +0.91% | 0.91% | 11.32% | 1 of 1 | -0.75% | +11.69% | 0.387% | 1.000 | 0.876 | -0.14% | 2.54% |
| condensed | 7 | BJ_T2_preloaded | 8 | +1.57% | +1.49% | 1.49% | 17.01% | 1 of 1 | -0.80% | +19.01% | 0.644% | 1.000 | 0.919 | -0.30% | 3.75% |
| condensed | 7 | BJ_T2_snug | 0.5 | +0.57% | +0.08% | 0.08% | 2.86% | 1 of 1 | -0.49% | -0.26% | 0.070% | 1.000 | 1.000 | +0.67% | 0.51% |
| condensed | 7 | BJ_T2_snug | 1 | +0.62% | +0.09% | 0.09% | 2.90% | 1 of 1 | -0.52% | -1.51% | 0.072% | 1.000 | 1.000 | +4.18% | 0.69% |
| condensed | 7 | BJ_T2_snug | 2 | +0.66% | +0.10% | 0.10% | 2.80% | 1 of 1 | -0.57% | -1.07% | 0.067% | 1.000 | 0.930 | +4.56% | 0.73% |
| condensed | 7 | BJ_T2_snug | 3 | -2.46% | -0.94% | 0.94% | 4.66% | 1 of 1 | +4.90% | -0.27% | 0.180% | 0.733 | 0.876 | +1.74% | 8.20% |
| condensed | 7 | BJ_T2_snug | 4 | +0.64% | +0.63% | 0.63% | 6.03% | 1 of 1 | -1.29% | +5.06% | 0.202% | 1.000 | 0.936 | -0.00% | 5.37% |
| condensed | 7 | BJ_T2_snug | 6 | +1.02% | +0.98% | 0.98% | 11.19% | 1 of 1 | -0.80% | +7.97% | 0.387% | 1.000 | 0.867 | -0.02% | 1.38% |
| condensed | 7 | BJ_T2_snug | 8 | +1.61% | +1.53% | 1.53% | 18.20% | 1 of 1 | -0.82% | +7.67% | 0.748% | 1.000 | 0.911 | -0.18% | 2.98% |
| raw | 5 | BJ_T1_preloaded | 0.5 | +0.29% | +0.05% | 0.05% | 3.90% | 1 of 1 | -0.27% | +0.13% | 0.072% | 0.920 | 1.000 | +0.39% | 0.97% |
| raw | 5 | BJ_T1_preloaded | 1 | -0.19% | -0.04% | 0.04% | 3.09% | 1 of 1 | +0.19% | -1.15% | 0.066% | 1.000 | 1.000 | +0.38% | 0.58% |
| raw | 5 | BJ_T1_preloaded | 2 | +0.36% | +0.08% | 0.08% | 3.50% | 1 of 1 | -0.36% | -1.21% | 0.094% | 0.956 | 0.722 | +0.30% | 0.41% |
| raw | 5 | BJ_T1_preloaded | 3 | +0.16% | +0.09% | 0.09% | 6.16% | 1 of 1 | -0.27% | +0.29% | 0.256% | 1.000 | 0.765 | -0.00% | 0.86% |
| raw | 5 | BJ_T1_preloaded | 4 | +0.59% | +0.50% | 0.50% | 9.00% | 1 of 1 | -0.79% | -2.41% | 0.399% | 1.000 | 0.895 | +0.37% | 1.52% |
| raw | 5 | BJ_T1_preloaded | 6 | -0.39% | -0.36% | 0.36% | 13.73% | 1 of 1 | +0.29% | -3.74% | 0.608% | 1.000 | 0.829 | +1.80% | 2.90% |
| raw | 5 | BJ_T1_preloaded | 8 | +2.77% | +2.59% | 2.59% | 18.38% | 1 of 1 | -1.44% | +2.99% | 0.817% | 1.000 | 0.679 | +0.01% | 2.01% |
| raw | 5 | BJ_T1_snug | 0.5 | -0.59% | -0.13% | 0.13% | 5.61% | 1 of 1 | +0.46% | +3.75% | 0.246% | 0.949 | 1.000 | +5.32% | 0.94% |
| raw | 5 | BJ_T1_snug | 1 | -2.80% | -0.62% | 0.62% | 6.16% | 1 of 1 | +2.25% | +2.14% | 0.298% | 0.846 | 1.000 | +13.65% | 2.49% |
| raw | 5 | BJ_T1_snug | 2 | -0.74% | -0.17% | 0.17% | 5.22% | 1 of 1 | +0.63% | +0.39% | 0.212% | 0.923 | 0.737 | +8.04% | 0.96% |
| raw | 5 | BJ_T1_snug | 3 | +0.15% | +0.08% | 0.08% | 6.06% | 1 of 1 | -0.25% | -0.55% | 0.264% | 0.868 | 0.758 | +0.00% | 0.93% |
| raw | 5 | BJ_T1_snug | 4 | +1.40% | +1.27% | 1.27% | 9.20% | 1 of 1 | -1.99% | -1.87% | 0.431% | 1.000 | 0.879 | +0.00% | 2.08% |
| raw | 5 | BJ_T1_snug | 6 | +0.63% | +0.58% | 0.58% | 13.94% | 1 of 1 | -0.47% | -2.52% | 0.638% | 1.000 | 0.799 | +1.72% | 2.63% |
| raw | 5 | BJ_T1_snug | 8 | +5.02% | +4.69% | 4.69% | 19.40% | 1 of 1 | -2.60% | +2.05% | 0.924% | 1.000 | 0.689 | +0.02% | 3.20% |
| raw | 5 | BJ_T2_preloaded | 0.5 | -1.02% | -0.09% | 0.09% | 4.28% | 1 of 1 | +1.05% | +0.35% | 0.086% | 0.948 | 1.000 | +0.55% | 1.78% |
| raw | 5 | BJ_T2_preloaded | 1 | -0.38% | -0.04% | 0.04% | 2.83% | 1 of 1 | +0.41% | +0.05% | 0.058% | 0.989 | 1.000 | +0.13% | 0.84% |
| raw | 5 | BJ_T2_preloaded | 2 | -0.05% | -0.01% | 0.01% | 2.60% | 1 of 1 | +0.05% | +0.45% | 0.056% | 1.000 | 0.984 | +0.44% | 0.35% |
| raw | 5 | BJ_T2_preloaded | 3 | -1.41% | -1.00% | 1.00% | 3.65% | 1 of 1 | +5.50% | +3.37% | 0.104% | 1.000 | 0.608 | +0.00% | 6.00% |
| raw | 5 | BJ_T2_preloaded | 4 | +1.02% | +1.02% | 1.02% | 6.37% | 1 of 1 | -2.07% | +2.74% | 0.216% | 1.000 | 0.918 | -0.21% | 4.63% |
| raw | 5 | BJ_T2_preloaded | 6 | -0.51% | -0.49% | 0.49% | 10.59% | 1 of 1 | +0.40% | -1.57% | 0.339% | 1.000 | 0.869 | +0.60% | 8.64% |
| raw | 5 | BJ_T2_preloaded | 8 | +5.10% | +4.84% | 4.84% | 17.33% | 1 of 1 | -2.60% | +1.68% | 0.668% | 1.000 | 0.918 | -0.41% | 4.62% |
| raw | 5 | BJ_T2_snug | 0.5 | -3.27% | -0.49% | 0.49% | 3.90% | 1 of 1 | +2.87% | +2.54% | 0.130% | 1.000 | 1.000 | +6.68% | 3.35% |
| raw | 5 | BJ_T2_snug | 1 | -6.12% | -0.94% | 0.94% | 4.98% | 1 of 1 | +5.51% | +2.22% | 0.212% | 1.000 | 1.000 | +15.47% | 7.34% |
| raw | 5 | BJ_T2_snug | 2 | -2.53% | -0.39% | 0.39% | 3.41% | 1 of 1 | +2.26% | +1.39% | 0.099% | 1.000 | 0.602 | +6.93% | 2.94% |
| raw | 5 | BJ_T2_snug | 3 | -4.64% | -2.56% | 2.56% | 5.88% | 1 of 1 | +13.35% | +2.46% | 0.286% | 0.733 | 0.779 | +1.74% | 18.46% |
| raw | 5 | BJ_T2_snug | 4 | +0.08% | +0.08% | 0.08% | 6.25% | 1 of 1 | -0.16% | +3.96% | 0.217% | 1.000 | 0.930 | -0.00% | 4.83% |
| raw | 5 | BJ_T2_snug | 6 | -0.47% | -0.45% | 0.45% | 11.45% | 1 of 1 | +0.37% | -3.78% | 0.405% | 1.000 | 0.870 | +0.55% | 7.24% |
| raw | 5 | BJ_T2_snug | 8 | +6.85% | +6.49% | 6.49% | 20.00% | 1 of 1 | -3.49% | -0.14% | 0.903% | 1.000 | 0.924 | -0.32% | 4.52% |
| raw | 6 | BJ_T1_preloaded | 0.5 | +0.27% | +0.04% | 0.04% | 3.73% | 1 of 1 | -0.25% | +0.52% | 0.066% | 0.895 | 1.000 | +0.16% | 0.80% |
| raw | 6 | BJ_T1_preloaded | 1 | +0.11% | +0.02% | 0.02% | 3.00% | 1 of 1 | -0.11% | +0.08% | 0.062% | 0.986 | 1.000 | +0.07% | 0.43% |
| raw | 6 | BJ_T1_preloaded | 2 | +1.54% | +0.34% | 0.34% | 3.38% | 1 of 1 | -1.53% | -0.77% | 0.087% | 0.971 | 0.781 | -0.11% | 1.92% |
| raw | 6 | BJ_T1_preloaded | 3 | +1.24% | +0.69% | 0.69% | 6.18% | 1 of 1 | -2.03% | +2.71% | 0.257% | 0.974 | 0.751 | -0.00% | 3.19% |
| raw | 6 | BJ_T1_preloaded | 4 | +0.45% | +0.38% | 0.38% | 9.51% | 1 of 1 | -0.61% | +1.12% | 0.446% | 1.000 | 0.873 | +0.43% | 1.81% |
| raw | 6 | BJ_T1_preloaded | 6 | -0.26% | -0.24% | 0.24% | 14.73% | 1 of 1 | +0.20% | +1.54% | 0.700% | 1.000 | 0.774 | +1.88% | 2.91% |
| raw | 6 | BJ_T1_preloaded | 8 | +3.55% | +3.32% | 3.32% | 21.68% | 1 of 1 | -1.84% | +4.58% | 1.138% | 1.000 | 0.664 | +0.01% | 2.29% |
| raw | 6 | BJ_T1_snug | 0.5 | -2.08% | -0.46% | 0.46% | 5.94% | 1 of 1 | +1.65% | +1.86% | 0.277% | 0.923 | 1.000 | +7.08% | 1.93% |
| raw | 6 | BJ_T1_snug | 1 | -1.40% | -0.31% | 0.31% | 5.42% | 1 of 1 | +1.11% | +0.81% | 0.230% | 0.923 | 1.000 | +6.64% | 1.52% |
| raw | 6 | BJ_T1_snug | 2 | -0.19% | -0.05% | 0.05% | 5.45% | 1 of 1 | +0.16% | -1.35% | 0.232% | 0.923 | 0.723 | +8.82% | 1.23% |
| raw | 6 | BJ_T1_snug | 3 | +0.39% | +0.22% | 0.22% | 6.31% | 1 of 1 | -0.65% | -1.53% | 0.286% | 0.868 | 0.758 | +0.00% | 0.89% |
| raw | 6 | BJ_T1_snug | 4 | +1.14% | +1.04% | 1.04% | 9.22% | 1 of 1 | -1.62% | -0.91% | 0.433% | 1.000 | 0.868 | +0.00% | 1.81% |
| raw | 6 | BJ_T1_snug | 6 | +0.36% | +0.33% | 0.33% | 14.06% | 1 of 1 | -0.27% | +0.60% | 0.649% | 1.000 | 0.761 | +1.58% | 2.40% |
| raw | 6 | BJ_T1_snug | 8 | +4.94% | +4.61% | 4.61% | 23.15% | 1 of 1 | -2.55% | -0.70% | 1.316% | 1.000 | 0.787 | +0.01% | 2.68% |
| raw | 6 | BJ_T2_preloaded | 0.5 | -0.98% | -0.09% | 0.09% | 4.00% | 1 of 1 | +1.00% | +2.57% | 0.075% | 0.949 | 1.000 | +0.25% | 0.82% |
| raw | 6 | BJ_T2_preloaded | 1 | -0.74% | -0.08% | 0.08% | 2.71% | 1 of 1 | +0.81% | +1.72% | 0.054% | 0.989 | 1.000 | +0.07% | 0.62% |
| raw | 6 | BJ_T2_preloaded | 2 | +1.03% | +0.14% | 0.14% | 2.51% | 1 of 1 | -1.16% | +0.64% | 0.052% | 0.971 | 0.968 | -1.22% | 2.32% |
| raw | 6 | BJ_T2_preloaded | 3 | -0.64% | -0.45% | 0.45% | 3.51% | 1 of 1 | +2.49% | +5.50% | 0.096% | 1.000 | 0.592 | -0.00% | 1.32% |
| raw | 6 | BJ_T2_preloaded | 4 | +1.30% | +1.29% | 1.29% | 6.14% | 1 of 1 | -2.62% | +1.89% | 0.201% | 1.000 | 0.940 | -0.10% | 2.81% |
| raw | 6 | BJ_T2_preloaded | 6 | -1.83% | -1.76% | 1.76% | 11.34% | 1 of 1 | +1.44% | +6.27% | 0.388% | 1.000 | 0.875 | +0.45% | 5.94% |
| raw | 6 | BJ_T2_preloaded | 8 | +3.73% | +3.54% | 3.54% | 14.28% | 1 of 1 | -1.91% | +1.97% | 0.454% | 1.000 | 0.933 | -0.27% | 3.75% |
| raw | 6 | BJ_T2_snug | 0.5 | -2.98% | -0.44% | 0.44% | 3.53% | 1 of 1 | +2.61% | +2.34% | 0.106% | 1.000 | 1.000 | +4.16% | 2.78% |
| raw | 6 | BJ_T2_snug | 1 | -5.21% | -0.79% | 0.79% | 4.12% | 1 of 1 | +4.66% | +2.74% | 0.145% | 1.000 | 1.000 | +10.41% | 5.82% |
| raw | 6 | BJ_T2_snug | 2 | -2.68% | -0.41% | 0.41% | 3.46% | 1 of 1 | +2.39% | +1.60% | 0.102% | 1.000 | 0.748 | +6.92% | 3.23% |
| raw | 6 | BJ_T2_snug | 3 | -3.51% | -1.70% | 1.70% | 4.87% | 1 of 1 | +8.90% | +4.35% | 0.197% | 0.733 | 0.770 | +1.74% | 11.60% |
| raw | 6 | BJ_T2_snug | 4 | -0.04% | -0.04% | 0.04% | 5.75% | 1 of 1 | +0.08% | +1.24% | 0.184% | 1.000 | 0.939 | +0.00% | 1.40% |
| raw | 6 | BJ_T2_snug | 6 | -1.27% | -1.22% | 1.22% | 12.23% | 1 of 1 | +1.00% | +13.43% | 0.462% | 1.000 | 0.876 | +0.65% | 7.90% |
| raw | 6 | BJ_T2_snug | 8 | +5.48% | +5.20% | 5.20% | 16.07% | 1 of 1 | -2.80% | +8.04% | 0.583% | 1.000 | 0.926 | +0.00% | 2.65% |
| raw | 7 | BJ_T1_preloaded | 0.5 | +0.14% | +0.02% | 0.02% | 3.62% | 1 of 1 | -0.13% | +1.28% | 0.062% | 0.944 | 1.000 | +0.25% | 1.26% |
| raw | 7 | BJ_T1_preloaded | 1 | +0.34% | +0.06% | 0.06% | 2.85% | 1 of 1 | -0.33% | +0.43% | 0.056% | 0.973 | 1.000 | -0.02% | 0.93% |
| raw | 7 | BJ_T1_preloaded | 2 | +0.74% | +0.16% | 0.16% | 3.58% | 1 of 1 | -0.74% | -0.42% | 0.098% | 0.955 | 0.856 | +0.30% | 0.83% |
| raw | 7 | BJ_T1_preloaded | 3 | +0.33% | +0.19% | 0.19% | 6.17% | 1 of 1 | -0.55% | +0.70% | 0.257% | 0.947 | 0.776 | -0.00% | 0.99% |
| raw | 7 | BJ_T1_preloaded | 4 | -0.42% | -0.36% | 0.36% | 8.75% | 1 of 1 | +0.57% | +0.01% | 0.377% | 1.000 | 0.864 | +0.40% | 1.64% |
| raw | 7 | BJ_T1_preloaded | 6 | -0.99% | -0.90% | 0.90% | 13.59% | 1 of 1 | +0.74% | +3.68% | 0.596% | 1.000 | 0.767 | +1.62% | 2.64% |
| raw | 7 | BJ_T1_preloaded | 8 | +2.58% | +2.42% | 2.42% | 19.21% | 1 of 1 | -1.34% | +6.80% | 0.893% | 1.000 | 0.662 | +0.01% | 2.37% |
| raw | 7 | BJ_T1_snug | 0.5 | -0.57% | -0.12% | 0.12% | 5.40% | 1 of 1 | +0.45% | +1.56% | 0.229% | 0.923 | 1.000 | +4.98% | 0.67% |
| raw | 7 | BJ_T1_snug | 1 | -0.52% | -0.11% | 0.11% | 5.31% | 1 of 1 | +0.41% | +1.12% | 0.221% | 0.923 | 1.000 | +7.27% | 0.79% |
| raw | 7 | BJ_T1_snug | 2 | +0.29% | +0.07% | 0.07% | 5.38% | 1 of 1 | -0.24% | -0.60% | 0.226% | 0.897 | 0.742 | +9.94% | 0.99% |
| raw | 7 | BJ_T1_snug | 3 | +0.76% | +0.43% | 0.43% | 6.27% | 1 of 1 | -1.25% | -3.77% | 0.282% | 0.868 | 0.791 | +0.00% | 1.31% |
| raw | 7 | BJ_T1_snug | 4 | +1.46% | +1.32% | 1.32% | 8.42% | 1 of 1 | -2.07% | -3.82% | 0.361% | 1.000 | 0.906 | +0.01% | 2.13% |
| raw | 7 | BJ_T1_snug | 6 | +1.48% | +1.35% | 1.35% | 13.05% | 1 of 1 | -1.10% | +0.01% | 0.560% | 1.000 | 0.781 | +1.43% | 2.47% |
| raw | 7 | BJ_T1_snug | 8 | +4.14% | +3.87% | 3.87% | 19.30% | 1 of 1 | -2.14% | +5.79% | 0.914% | 1.000 | 0.677 | +0.02% | 2.99% |
| raw | 7 | BJ_T2_preloaded | 0.5 | -0.76% | -0.07% | 0.07% | 3.73% | 1 of 1 | +0.77% | +1.98% | 0.065% | 0.948 | 1.000 | +0.50% | 0.98% |
| raw | 7 | BJ_T2_preloaded | 1 | +0.12% | +0.01% | 0.01% | 2.51% | 1 of 1 | -0.13% | +1.14% | 0.046% | 0.989 | 1.000 | -0.11% | 0.96% |
| raw | 7 | BJ_T2_preloaded | 2 | +1.53% | +0.20% | 0.20% | 2.52% | 1 of 1 | -1.71% | +0.81% | 0.053% | 0.985 | 0.984 | -1.07% | 3.01% |
| raw | 7 | BJ_T2_preloaded | 3 | -0.84% | -0.59% | 0.59% | 3.65% | 1 of 1 | +3.25% | +6.09% | 0.104% | 1.000 | 0.571 | +0.00% | 1.98% |
| raw | 7 | BJ_T2_preloaded | 4 | +0.64% | +0.64% | 0.64% | 5.97% | 1 of 1 | -1.29% | +5.16% | 0.189% | 1.000 | 0.934 | -0.05% | 1.93% |
| raw | 7 | BJ_T2_preloaded | 6 | -2.61% | -2.50% | 2.50% | 11.86% | 1 of 1 | +2.05% | +13.03% | 0.425% | 1.000 | 0.871 | -0.02% | 2.11% |
| raw | 7 | BJ_T2_preloaded | 8 | +4.97% | +4.72% | 4.72% | 17.33% | 1 of 1 | -2.54% | +18.00% | 0.668% | 1.000 | 0.922 | -0.42% | 5.23% |
| raw | 7 | BJ_T2_snug | 0.5 | -2.60% | -0.39% | 0.39% | 3.12% | 1 of 1 | +2.27% | +2.35% | 0.083% | 1.000 | 1.000 | +3.75% | 2.50% |
| raw | 7 | BJ_T2_snug | 1 | -4.18% | -0.63% | 0.63% | 3.46% | 1 of 1 | +3.70% | +2.56% | 0.102% | 1.000 | 1.000 | +8.83% | 4.51% |
| raw | 7 | BJ_T2_snug | 2 | -2.94% | -0.45% | 0.45% | 3.15% | 1 of 1 | +2.63% | +2.08% | 0.084% | 1.000 | 0.860 | +8.01% | 3.27% |
| raw | 7 | BJ_T2_snug | 3 | -4.42% | -2.39% | 2.39% | 5.29% | 1 of 1 | +12.46% | +5.86% | 0.232% | 0.733 | 0.689 | +1.74% | 15.77% |
| raw | 7 | BJ_T2_snug | 4 | -0.50% | -0.50% | 0.50% | 6.16% | 1 of 1 | +1.01% | +5.94% | 0.211% | 1.000 | 0.931 | -0.00% | 3.28% |
| raw | 7 | BJ_T2_snug | 6 | -1.37% | -1.32% | 1.32% | 11.44% | 1 of 1 | +1.08% | +8.80% | 0.404% | 1.000 | 0.864 | +0.08% | 2.12% |
| raw | 7 | BJ_T2_snug | 8 | +6.50% | +6.17% | 6.17% | 18.82% | 1 of 1 | -3.32% | +6.51% | 0.800% | 1.000 | 0.914 | -0.35% | 5.18% |

### The author's recomputation (`audit/c22_recompute.py`, records in `records/c22/audit/`)

- Environment: Python 3.13.18, numpy 2.4.6, scipy 1.18.1, solver scipy, Linux-6.18.44-fc-v470-x86_64-with-glibc2.39, 2 processors, one BLAS thread a process.
- Regenerated instances (`regenerate.json`; zlib 1.3, archive creator field 0): 644 of 644 files have the manifest's SHA-256 and 644 its sizes; the members are the configured draws: True; members shared between two sets: 0.
- Criteria from the returned per-pair rows with the script's own quantile (`aggregate.json`): largest relative difference of a seed's median or 90th percentile from the returned one 0; of C1 0; of C2 0; verdict equal: True.
- Metrics that need no solve, recomputed for 5544 fields of 132 members (members missing: 0): largest absolute difference from the returned rows F_err 0, e_err 0, F_sigma_err 8.0e-15, gap 4.5e-16, bound 7.0e-15, iou_contact 0, iou_plastic 0, bolt_err 0, u_rel_l2 3.3e-16; containment in the bound differing in 0 fields.
- The returned labels on the regenerated instances, 924 levels: largest relative difference in energy 4.4e-16, in force 0; in end displacement 0 mm; largest unconstrained residual 1.3e-10; smallest gap 0; smallest multiplier -8.3e-12.
- The condensed fields from the returned base fields, raw fields and amplitudes, in float32, for 396 member and seed pairs: largest absolute difference 0 (0 unknowns differ; the largest unknown is 6.76 in size).
- The judged error with its exact solve, recomputed for 1344 pairs (3.51 processor hours): largest absolute difference of the signed distance from the returned one 8.1e-14.

| Reading, set, seed | Pairs recomputed | Largest absolute difference of the distance | Largest returned distance among them |
|---|---|---|---|
| condensed, eval, 5 | 448 | 6.0e-14 | 50.1% |
| condensed, eval, 6 | 448 | 3.5e-14 | 68.6% |
| condensed, eval, 7 | 448 | 8.1e-14 | 51.0% |

| Seed | Median, recomputed | Returned | 90th percentile, recomputed | Returned |
|---|---|---|---|---|
| 5 | 0.008284227273417155 | 0.008284227273415379 | 0.036639366776084155 | 0.03663936677608451 |
| 6 | 0.00797238281647128 | 0.007972382816471169 | 0.03766036133923343 | 0.03766036133923352 |
| 7 | 0.007818943658161714 | 0.007818943658160049 | 0.03656239953666294 | 0.036562399536675616 |

Recomputed C1 0.00797238281647128 and C2 0.036639366776084155, PASS; returned 0.007972382816471169 and 0.03663936677608451, PASS.

- Members re-solved from the regenerated instances (`resolve.json`): eval_0001: bit for bit False, largest difference 3.6e-15 of the largest unknown, 1.0e-15 in energy, 2.2e-15 in force, iterations equal to the ledger's True, converged True; eval_0030: bit for bit False, largest difference 7.6e-16 of the largest unknown, 2.2e-16 in energy, 8.9e-16 in force, iterations equal to the ledger's True, converged True; former_0017: bit for bit False, largest difference 1.9e-15 of the largest unknown, 4.4e-16 in energy, 6.2e-15 in force, iterations equal to the ledger's True, converged True; tested_BJ_T1_preloaded: bit for bit False, largest difference 3.8e-15 of the largest unknown, 4.4e-16 in energy, 1.8e-15 in force, iterations equal to the ledger's True, converged True.
- Records (`records.json`): the returned configuration is the stamped one: True; 132 labelled members, once each: True, at the configured levels: True, all converged: True, residuals within the limits: True; label files with the ledger's SHA-256: 132; every prediction file holds the 132 members with the expected shapes: True; each log gives its history's losses, times and counts: True; commands that did not end with code 0: 74_c22_train_s5; cancelled: 0.
