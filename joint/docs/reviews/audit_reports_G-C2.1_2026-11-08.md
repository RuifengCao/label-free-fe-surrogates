# Independent audit of the G-C2.1 verdict: reports as delivered

Verbatim reports of the independent auditor (a separate agent that wrote none of the code or the draft) to the author, 8 November 2026: round 1 at about 15:05 GMT, round 2 at about 18:58 GMT. Round 1 audited the return package, the records and the first draft of the verdict, its provisional tables, the two audit scripts and the README. Paths under /tmp are the auditor's scratch copies in the development sandbox.

---

G-C2.1 audit: the records and the FAIL verdict hold up. My own code reproduces every criterion and per-pair value I checked. The errors below are in the draft text, the tables and the writer script. I edited nothing in the repository and ran no git command that changes state.

**Verified**
- **Archive.** The SHA-256 (7b6f19e6…ae0) and the size (51,271,219 bytes) match. Its 110 files are the same set as records/c2/return/, byte for byte. return_files.sha256 checks 110 of 110 and lists exactly those files. return_listing.txt equals my own `tar tvz --full-time` listing at UTC+8 (119 entries).
- **Provenance.**
  - commit.txt is 896e04009189…, the commit of tag prereg-c2 (read-only git).
  - config.log has the stamped hash, 20 code hashes equal to the PRESPEC table, and 6 repository lines. The returned c2_config.json equals the stamped configuration (canonical SHA-256 795515…fb4).
  - sha256_check.log shows 26 OK and pytest.log shows 31 passed. Both the working copy and the clean export pass all 26 hashes.
- **Labels.**
  - The ledger has 132 unique entries: the first 64 training, 64 held-out and 4 tested members. That is 860 levels, all at the configured values, all converged (at most 25 iterations).
  - The worst residuals equal check_labels.log and are within the limits. All 132 instance hashes equal the manifest's.
  - The 68 returned label files match the ledger hashes. In them e equals the last unknown and F = 4k_s(D−e) exactly, and |F−F_σ|/F ≤ 2.8e-13.
  - label.log has 132 "converged" lines, with times equal to the ledger's (32.9 to 144.3 s).
- **Training.** All six runs finished with their configured steps (102,400 or 12,800) and 200 epochs, no resume, one start and one end in attempts.log, finite losses. The log lines equal the histories.
- **Predictions.** Each run holds exactly the 64+4 members, shape (7, n_z), float32, finite. Against the regenerated instances, every run has its 181,979 fixed values at zero and its 139,160 contact values non-negative.
- **Criteria.** My own quantile on the per-pair rows gives per-seed medians 170.122, 0.066114 and 0.024115, and 90th percentiles 5075.06, 0.311600 and 0.185615, with 44 infinite pairs. C1 = 0.066114, C2 = 0.311600, FAIL. All are identical to verdict.json. I also recomputed e_err and F_err for all 2,856 pairs from preds.npz and the labels: the largest difference is 0.
- **Regeneration.** I regenerated all 580 instances. With zlib 1.3, all 580 SHA-256 values and sizes equal the manifest's. With zlib-ng, 0 of 5 hashes match but the arrays are identical.
- **Re-evaluation with the stamped library.**
  - 12 exact solves: eval_0026 (241 MPa) for seeds 0 to 2 at 0.5 to 8 mm, and eval_0030 (362 MPa) for seeds 1 and 2 at 1 and 6 mm.
  - The 11 finite distances agree with verdict.json within 3.1e-13 (relative 7.0e-13). The infinite one is reproduced: F* = −140.6 N at e = 0.00041 mm.
  - The energy readings of all six runs on these two members (84 pairs) agree in every column within 5.7e-14.
- **Tables and text.** 882 cells of the provisional tables re-derived with no mismatch. Every number in the draft text matches the records at its rounding.

**Errors**
1. "audit/c2_recompute.py … reproduces them" is not yet established; when I looked, 2 of 68 members were done. The provisional line "Recomputed … C1 6.611%, C2 31.160%, FAIL" was generated from a placeholder aggregate.json in the scratch folder `fakeaud/` (2 members, returned values 0).
2. c2_write_verdict.py will fail on the real regenerate.json: `reg['sizes_equal']` exists only under `by_split`. Its sentence would also call all 580 files "held-out and tested instances".
3. "Seeds 1 and 2 trained, and the criteria fail on them too" is wrong for C1, which turns on seed 0, as the next bullet says.
4. The 2,061,038 unknowns and 5,192 distinct values count all 68 members, but the table heading says "held-out pairs". On the 64 held-out members the figures are 4,940 of 1,939,420; the other runs have 1.756 to 1.760 million.
5. "softplus floor" is the wrong term. The starting value is T·ln2·(D+δ), the softplus of the zeroed output (model.py, lines 60 to 63 and 90).
6. Deviation 1, "no slower than": the bench's 0.1669 s is slower than seed 0's 0.1638 s. "Within the range" is accurate.
7. "Those of the label-free seeds are largest at 8 mm": seed 0's median is largest at 0.5 mm. This should say seeds 1 and 2.
8. The README status row drops "at this budget … within these limits" from the fixed interpretation, so it claims more than the pre-specification allows.

**Missing**
1. Overall values for the four tested members, for each arm and seed. "Reported, not judged" asks for them "by level and overall"; the tables give only per-pair rows.
2. A departure that is not listed. Seed 0's loss ended at 10.74 in epoch 200, and averaged 10.64 over the last 20 epochs. RUNBOOK section 5 expects "about 10.3 to 10.6" ("numbers, not criteria"). Its general rule says to stop and report on output that differs from a comment, and no report is recorded. Seeds 1 and 2 ended at 10.40 and 10.42.

**Smaller points**
- Suggested addition: seed 0's fields are spatially uniform. In every pair all free non-contact nodes share one u_y and, off the web, one u_x; u_z differs only in float32 rounding. This is why the field has so few distinct values.
- Measured against the label's norm, the seed 0 fields are 0.50% from the starting field in the median (at most 3.5%) and 0.57% from zero.
- All 44 infinite pairs are in preloaded members (ρ 0.23 to 0.88), with predicted e of 0.0004 to 0.0016 mm.
- These claims need a source or an "(inferred)" mark:
  - the Chinese runbook (no record in the repository, unlike RUNBOOK_C13_addendum.md);
  - the evaluation's solver, which is not logged;
  - "packed at 16:29", which is the time of the records/ folder; the gzip header carries no time.
- "32 GiB" should be 31.8 GiB (32,607 MiB).
- "third provenance line" should be "third entry". A 208-CPU shell suggests a shell outside the single tmux session, or a changed CPU set (inferred).
- The tail claims need numbers:
  - Of the 45 pairs above each seed's 90th percentile, 32 (seed 1) and 38 (seed 2) are in the 20 members below 300 MPa, and 33 and 31 are at 6 and 8 mm.
  - At 8 mm, 25 and 13 of the pairs above 10% are in members at or above 300 MPa.
  - Use one definition of "tail".
  - Seed 2 shows only one of the pilot's two places.
- "C2 failed in every seed" and "met C2" should read "every seed's 90th percentile exceeded 10%".
- "within 2.3% and 0.8%" should be "in the median".
- "would use the same training code" is a plan and should be marked as one.
- The supervised losses print as 0.0000; use scientific notation.
- Optional: the commit is dated 21:18:56 GMT and the tag 22:10:42 GMT, against the stated stamp at 20:38.
- README: environment.json sits beside members/, not inside it.
- c2_recompute.py:
  - It writes the manifest's hash into the instances, not the stamped hash; the two are equal here.
  - aggregate() treats NaN against NaN as an infinite difference and does not compare within_bound. Neither affects the label-free runs.
- No en or em dashes, paths, tool names or American spellings in the draft, the README or either script.

All my scripts are in /tmp/claude-0/-home-claude/8ff2db7c-f7cd-5897-8207-48e2e1d8242b/scratchpad/audit_c2/scripts and the outputs in /tmp/claude-0/-home-claude/8ff2db7c-f7cd-5897-8207-48e2e1d8242b/scratchpad/audit_c2/out; the main ones are:
- audit_records.py → audit_records.json
- regen.py → regen_all_zlib13.json, regen_5_zlibng.json
- preds_constraints.py → preds_constraints.json
- reeval.py → reeval.json, reeval.log
- draft_numbers.py → draft_numbers.json
- check_provisional.py → check_provisional.json

The regenerated instances are in /tmp/claude-0/-home-claude/8ff2db7c-f7cd-5897-8207-48e2e1d8242b/scratchpad/audit_c2/inst_z13. The FE solves took about 8 minutes of CPU.

---

# Round 2 (8 November 2026, about 18:58 GMT): second reading of the final documents

Second reading of the G-C2.1 verdict: the final documents are sound. I found one error in the text (line 84), and everything else is minor. All 8 errors and 2 omissions from round one are fixed, and the smaller points are taken up except one: the numbers file still says "packed" (point 1 below). I edited nothing in the repository, ran no git command that changes state, and used under a minute of CPU.

**Error**
- Line 84: "Every metric of the three label-free runs was recomputed … by the author and by the audit, each with its own code." The audit did not recompute every metric. It recomputed:
  - e_err and F_err for all 2,856 pairs;
  - the criteria from the per-pair rows;
  - all readings for only two members (12 exact solves and 84 energy readings).

  Line 85 says the author recomputed them all, so line 84 should say "by the author", with the audit's narrower checks left to line 86.

**Smaller points**
1. The numbers file's run record still says "Archive packed at 2026-11-08 16:29:14 CST". The text now dates only the folder. Write instead that `records/` was last changed at 16:29:14 CST.
2. Line 12, "It dates the folder the package was assembled in 16:29 CST", needs a "to": "dates … to 16:29 CST".
3. Line 23: the five zlib-ng files differ only in SHA-256. Their node and unknown counts equal the manifest's, so "differ from them" overstates it.
4. Line 88:
   - "as on the host" is inferred from the hash match, since the host did not log its zlib; mark it "(inferred)".
   - "they differ" should be "the five the audit tried differ".
5. Line 72, "a report could not have changed the run", is an inference. Either mark it or say "no pre-specified stop applies".
6. Line 110, "each seed's 90th percentile", should be "each trained seed's": 44 of seed 0's 45 tail pairs are at 0.5 and 1 mm.
7. Line 103 (optional precision): the shared u_x holds off the web and off the bearing patch, whose x slot holds the separation. Including the patch there are two values. u_y is shared by all free nodes, contact plane included.

**Verified**
- **Numbers file.** I reran the writer into my folder and the output is byte-identical (SHA-256 520e0282…). The assembled verdict equals the text up to "The tables follow", then an empty line, then the numbers, which is G-C1.3's rule.
- **Earlier table cells.** All 882 cells I re-derived in round one still match.
- **New tables, checked with my own code.**
  - Tail table: all six runs, every column.
  - Tested members overall: all six "all four" rows and three member rows. The borderline roundings are right (15.749 shows as 15.7, 2.155 as 2.2, −0.947 as −0.9).
  - Infinite pairs:
    - seed 0 held-out: e 0.0004 to 0.0016 mm, ρ 0.23 to 0.88;
    - seed 0 tested: e 0.0004 to 0.0008 mm, ρ 0.82;
    - supervised seed 1: e 0.1040 mm, ρ 0.84.
- **The recomputation subsection, against records/c2/audit.**
  - aggregate.json: 68 of 68 members, every difference 0, no bound mismatches, C1, C2 and FAIL identical to the returned ones.
  - Label check: 3.3e-16, 0 and 0. The residual 1.3e-10 equals the ledger's worst over these 68 members.
  - regenerate.json: 580 of 580 files match, and the manifest's configuration is the stamped one.
  - resolve.json: the four re-solves are bit-identical, with the ledger's iterations.
  - numpy253/: differences of 2.96e-12, 2.6e-14 and at most 1.99e-14.
- **Independent audit paragraph.** It matches my round-one results.
- **Seed 0 uniformity.** u_x and u_y take one value in every pair, and u_z varies by at most 3.8e-6 of its size.
- **Text.** All its numbers check against the records.
- **Spelling and format.** None of the six files has en or em dashes, paths, tool names or American spellings.
- **README.** The G-C2.1 parts are now correct: the status row carries "at this budget … within these limits", and numpy253/ and environment.json are placed correctly.
- **c2_recompute.py.** It now writes the stamped hash, checks the manifest's hash, and handles NaN pairs and within_bound.
- The working copy's audit/__pycache__ is git-ignored.

The rerun numbers are in /tmp/claude-0/-home-claude/8ff2db7c-f7cd-5897-8207-48e2e1d8242b/scratchpad/audit_c2/out/numbers_rerun.md. The spot-check script is /tmp/claude-0/-home-claude/8ff2db7c-f7cd-5897-8207-48e2e1d8242b/scratchpad/audit_c2/scripts/round2_checks.py, with its results in /tmp/claude-0/-home-claude/8ff2db7c-f7cd-5897-8207-48e2e1d8242b/scratchpad/audit_c2/out/round2_checks.json.

---

*Author's note: all of the round-two points were taken up in the final text: the error and points 1 to 7.*
