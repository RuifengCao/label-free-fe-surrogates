# G-F1: independent review reports before tagging (7 November 2026)

Two rounds by a separate agent that did not write the code, on its own clean export of commit `e966200`, under the rules: nothing solved for B-13 or T-13 (models built only); B-19 and T-19 solved lightly; the repository copy left unchanged. Reports as returned, unedited apart from this header. The changes they led to are in the second stamp (7 November 2026, 17:18 GMT); see Section 5 of the project owner's note in Chinese, 'Complete check before tagging G-F1' (7 November 2026), which is kept with his records.

---

## Round 1: review of export e966200

**Bottom line.** I found nothing blocking. On every rule I checked, the code does what docs/PRESPEC_G-F1.md says. The hash and code-list guard will pass on this export. The meshes for B-13 and T-13 build. The test readings come out exactly as in the pre-spec table. The dry-run outputs are consistent with each other and can be reproduced bit for bit. There are two process risks, both tied to the 2-hour cut-off and restart scheme. Neither would change the verdict silently, but either could produce a FAIL that does not reflect the model. Fixing either one in code changes the stamped hashes and means stamping again. The other option is a written operator rule, fixed before the run.

### SHOULD FIX

**1. An error inside a case stops the whole run and loses the record.**
- Where: f1/run.py:90 and :104 (`set_preload` and `_level` are not wrapped), f1/__main__.py:80-81 (the loop over cases).
- These errors are not caught anywhere:
  - `RuntimeError("active set did not settle…")` from fejoint/contact.py:49, raised via chs.py:75;
  - `RuntimeError("bubble condensation…")` from nlhex.py:114, raised at a level's first evaluation (chs.py:67);
  - a `LinAlgError`.
- What happens: the error passes through `run_case` and `main`. No record is written for that case, so even its converged levels are lost. The cases after it are never run. Every restart re-solves the same case and fails at the same point.
- The pre-spec and the run.py docstring say something different: a level that does not converge is recorded, and the path stops there.
- How it could change the verdict, if it happens:
  - If the failing level comes after the comparison points were crossed (for example the stop level), the pre-spec would count C1 and C3 as valid. The code gives "no record", so FAIL.
  - If the failure is in B-13's gated cases, T-13's gated cases never run, so C2 is "no record".
  - Either way the failure is visible (a traceback, and "no record" in the tables).
- How likely: low. In the dry run the active-set solver needed at most 13 of its 100 iterations, and Newton at most 6 of 60.
- I reproduced this on B-19 with the tiny mesh, by forcing the active-set solver to fail: the error propagated and no record was written.
- Fix: catch the error per level and record the level as not converged, with the message, then stamp again. Or agree in writing before the run how such an error is treated. Note that the progress log has no bolt forces, so C3 cannot be rebuilt from the log.

**2. `verdict` does not check that all 14 records exist.**
- Where: f1/verdict.py:78-127, called from f1/__main__.py:83.
- With records missing, `verdict` returns FAIL with status "no record" instead of refusing. If the job wrapper runs `verdict` after a run that was cut off or crashed, it writes a premature FAIL to verdict.json and numbers.md. I confirmed that an empty records directory gives FAIL.
- Mitigation: run `verdict` only after every id from `python -m f1 cases` exists in records/ and parses. Or add that check to the code and stamp again.

### MINOR

**3. Records are not written atomically** (f1/run.py:169). If the job is killed during `write_text`, a truncated file is left. On restart it is reported as "exists, skipped" (run.py:158). It then fails with a JSONDecodeError at run.py:167 (in the medium-mesh case) or verdict.py:75. I demonstrated this. The failure is loud, and the window is milliseconds. Mitigation: after each kill, check that every record loads as JSON before restarting.

**4. Nothing is saved within a case.** A case longer than 2 hours can never finish under the restart scheme. The dry run's longest case took 21 minutes on the medium mesh and at most about 10 minutes on the coarse mesh. The gate's meshes are the same sizes (below). Only a gated path that runs to its cap (60 bending or 50 axial levels) with heavy yielding could come near 2 hours. The dry run had no restart (run.log has no "skipped" lines), so the gate will be the first run that uses the skip logic outside the tests.

**5. `bracket_values` (f1/run.py:140-152)** allows for the medium mesh crossing one level later than the coarse mesh, but not one level earlier. If it crosses earlier, `at_point` interpolates between levels that are not neighbours. That only happens when the target lies within the mesh difference (under 1%) of level i−1. The weight is then about 1, so the error is negligible against the 2% limit. The mesh flag is reported only, so no action is needed.

**6. `set_preload` (chs.py:604-618) records only the number of iterations, not whether its fixed point converged.** At the preload level, `at_point` uses `forces_kN` from set_preload's last solve. In the dry run every preload took 2 iterations. For B-19 with measured preload I checked that these forces equal the bolt forces of the reference state exactly.

**7. Provenance.** Records carry neither the configuration hash nor the code hash, and every command overwrites config.json. This is consistent with the pre-spec's account that the dry verdict was recomputed with the stamped code.

### Checked and correct (no action)
- **Units and definitions:**
  - M = 2·grad[θ]/1e6 kNm; T = 2·grad[w0]/1e3 kN; factor 2 only, for the half model.
  - Θ_D = u_z(D)/323.9, with D at φ=0, r=R, z=tp+100.
  - Axial displacement = u_z(D) + u_z(C), with C at φ=180°.
  - Bolt 1 is the bolt at 15°, index 0 of `bolts_kN`.
  - All readings are taken relative to the preload state; the bolt forces are absolute.
  - The model inputs match the pre-spec: E values, ν, bolt area, L_b, stiffnesses, bearing radius 17.3 mm, weld root and fillet, 600 mm tube, stop rules (0.0012 rad and 105 kNm; 850 kN), steps and caps.
- **Verdict logic:** C3 = b1(100) − b1(25). Interpolation is linear, with the preload state as level 0. The bracket is [min−tol, max+tol]. Validity requires every level up to the one used, including the preload state, to have converged within the KKT limits. PASS only if C1, C2 and C3 are all present and all hold.
- **Edge cases:**
  - M(θ) and T(w0) cannot decrease, because the energy is convex in the unknowns and the control together, so the first crossing is unique in M and T. Θ_D and the displacement are monotonic on every dry path.
  - The equal-x branch cannot be reached.
  - A NaN or a level that did not converge gives "missing" or "invalid", as the pre-spec requires.
  - A zero coarse value makes the mesh flag "flagged", which is the conservative side.
- **Preload state assumed to have M = 0:** for B-19 with measured preload the actual value is 0.0028 kNm, and w0 there is 0.0044 mm. Negligible; the nominal case is symmetric.
- **KKT scaling:** the force scale is the largest reaction, which in bending is the θ-reaction in N·mm. So the 1e-6 limit allows nodal residuals of tens of N. This is pre-registered. Dry-run residuals are at most 2e-10, and the 1e-10 step-size test is what controls accuracy.
- **Pre-spec wording:**
  - "u_y fixed at the plate's centre carries no force" is true for the frictionless bound. In no-slip that node is one of the no-slip constraints and carries 50 to 605 N in the B-19 dry run.
  - The solver is `chs.WarmContactProblem`. I compared it with `nlsolve.ContactProblem`: the solve loop is identical apart from the warm start.

### What I executed (B-13 and T-13 never solved)
- **Hashes:** `sha256sum -c docs/G-F1_code.sha256` passes for all 35 files. The stamped copy is identical to the live files. The pre-spec's hash table matches the code list. `config_hash()`, computed in Python and not passed to any command, equals the pre-spec's hash. The dry config.json equals `config(True)`.
- **Test readings:** `read_tests(config())` (test data only) reproduces the table: 75.00±4.81, 55.57±3.48, 0.934±0.051, 59.50±7.36. Measured preloads: 109.0, 104.4, 126.2, 102.3, 115.8, 111.0 kN.
- **B-13 and T-13 geometry only** (mesh build, mesh checks, model constructor; no solve, no preload, no readings): all assertions pass.

  | Specimen | Coarse cells | Coarse unknowns | Medium cells | Medium unknowns |
  |---|---|---|---|---|
  | B-13 | 5,496 | 25,916 | 13,392 | 56,000 |
  | T-13 | 5,352 | 25,259 | 13,392 | 56,000 |

  The coarse sizes match the pre-spec's numbers; the medium sizes are identical to the dry run's.
- **Hardening curves:** 17 points each, strictly increasing, starting at f_y.
- **Dry-run consistency:** recomputing the verdict from the dry records with the exported code gives verdict.json and numbers.md byte-identical. run.log matches all 113 levels and the case order. Total time 6,130 s (1 h 42 min).
- **Coarser reading step:** reading every other level reproduces the pre-spec's claim: largest changes 0.229 kNm, 0.388 kN, 0.0083 mm.
- **Reproduction:** I solved B-19 no-slip, J2, measured preload, coarse mesh again. Every number is identical to the dry record (difference 0.0), including iterations and plastic points; 405 s single-threaded.
- **Memory:** one SuperLU factorization of the B-19 medium mesh (53,670 free unknowns) peaks at 2.6 GB. That fits in 7 GB for one process; two medium cases at once would be tight.
- **Failure paths:** the three demonstrations described in findings 1, 2 and 3.
- **Tests:** `pytest tests/test_f1.py tests/test_chs.py` gives 22 passed in 9 min 12 s.

**Repository copy.** My first Python import created `f1/__pycache__` in the copy. I deleted it, so only the `f1/` directory's timestamp changed, and all 35 hashes still verify. All other work, including the scripts and logs, is in the scratch folder `review_work/`.

---

## Round 2: review of fix.diff on e966200

**Bottom line.** Nothing blocking. The changes do what your summary says. They leave every computed value of a complete, error-free run unchanged, and that run's verdict too. NaN from a failed level cannot reach the verdict. One small code point is worth changing before you stamp again (MemoryError, below). There are also five wording fixes for the pre-spec.

### SHOULD FIX (one line, before stamping)
- **f1/run.py:39, `MemoryError` in `NUMERICAL_ERRORS`.**
  - Running out of memory depends on the machine and on whatever else runs on it, not on the model.
  - Caught, it is recorded as non-convergence. The record then exists, so a restart skips that case and it is never retried.
  - In a gated case, that criterion would not hold and the gate would FAIL because of the machine, not the model.
  - "Numerical error" in the pre-spec does not naturally cover memory.
  - Fix: drop `MemoryError`, so the run stops and can be retried as before. Or name it in the pre-spec.
  - Likelihood is low. Coarse cases use much less memory than medium ones, and the medium cases are reported only. On Linux, running out of memory usually kills the process outright, which stops the run and gets retried, as before.

### MINOR
- **Broad exception classes.** `RuntimeError` also covers `NotImplementedError` and `RecursionError`, and `ArithmeticError` covers `ZeroDivisionError`. These are programming errors, but they would be recorded as non-convergence instead of stopping the run. I found none on the gate's code path, and the error text is kept in the record.
- **NaN in records.** Failed levels write the bare token `NaN`. Python's json reads it back (verified), but strict JSON readers such as jq or JavaScript reject the file. verdict.json and numbers.md never contain NaN (verified).
- **`config_sha256` is not checked.** `verdict` does not compare it, and it is identical under both stamps, so it does not identify the code version. Records from the new code can be told apart by the new fields. Optionally, `verdict` could refuse records that lack the field or carry a different hash.
- **No fsync before `os.replace`.** A process kill (the cut-off case) leaves whole records; a machine crash might not. No action needed.

### 1. Does the change do what it says, and does it leave a complete, error-free run alone?
Yes. The call sequence is unchanged. `preload_targets` is now called once instead of twice; it is a pure function, so nothing changes. `on_target` uses the same test and tolerance as `set_preload`'s own stop test (relative, strict, below 1e-6). So it is True whenever the preload converged; every dry preload converged in 2 iterations. The one deliberate tightening: a preload that reaches 30 iterations without converging now makes that case's criteria "invalid". The Validity section states this.

Checked by running:
- **Re-solve.** T-19 no-slip, J2, nominal, coarse with the revised `run_case` gives every number identical to the dry record. `config_sha256` equals `config_hash(True)`, `on_target` is True, and no .tmp file is left.
- **Dry verdict.** The revised `verdict --dry` on a copy of records/f1_dry gives verdict.json, numbers.md and config.json byte-identical to the originals. With one record removed it refuses.
- **Tests.** The revised tests/test_f1.py: 11 passed in 9 min 28 s.

### 2. Can NaN reach the verdict wrongly?
No. A failed level is always the last level of its path. Since `NaN >= target` is False, it can never be the crossing level or its interpolation partner. Values read before it are kept, and the validity check covers only levels up to the one used.

I injected failures into copies of the dry records:

| Injected failure | Result |
|---|---|
| (a) failed level after the last level, B-19 frictionless J2 | C1 and C3 identical to the intact record, status "ok" |
| (b) failed level at B-19 no-slip's C1 crossing | C1 "missing"; C3 "ok", since its points were crossed earlier |
| (c) preload error, T-19 no-slip | C2 "missing" |
| (d) coarse elastic record failing right after the C1 crossing | `bracket_values` ignores the NaN level; it may still return the failed level's control value, which is harmless |

The mesh flag and `numbers_markdown` only ever receive None, never NaN. The JSON round trip works.

### 3. What can still lose a record or stop the run?
- **Model building and data reading** (run.py:111-113) are outside the try blocks. An error there stops the run with no record. I built all 12 distinct gate models without solving, and read B-13's measured targets; every one succeeded. The models: B-13 and T-13; both splices; J2 and elastic on coarse; elastic on medium.
- **Non-numerical errors inside a solve** (ValueError, AssertionError, …) still stop the run and lose that case's record. I found no numerical source for them: singular or unsettled systems raise RuntimeError or LinAlgError, which are caught, and NaN energies end the line search with converged False.
- **KeyboardInterrupt and SystemExit** are not caught, so they stop the run, as intended.
- **A kill during a write** leaves only NAME.json.tmp. `run` re-runs that case and `evaluate`'s `glob("*.json")` ignores the file (I checked the glob).
- **An out-of-memory kill** loses the case in progress, which is retried on restart, as before.

### 4. Does the pre-spec text now match the code?
Mostly. These need correcting:
- **Validity, "to within 1e-6":** make it "to a relative 1e-6" (the code tests |N/N_target − 1| < 1e-6).
- **"A case whose preload raises an error":** make it "a numerical error"; other errors stop the run. Also say which classes count as "numerical error", or drop `MemoryError` as above.
- **Top note, "Only f1/run.py and f1/__main__.py changed":** add "of the gate's code"; tests/test_f1.py changed too. In the revised copy, only those two files fail the old code list.
- **"One solve of B-19 on the medium mesh … 2.6 GB":** I measured one sparse factorization of the medium-mesh stiffness, with the model built but no preload and no active-set loop. A full level also holds the stiffness matrix and its free part, so its peak is somewhat higher. Reword it, or measure a full level.
- **"With the nominal preload it is zero":** make it "zero to round-off".

The rest of the changed text matches the code: the u_y wording, the `WarmContactProblem` wording, the validity rules, and "How it is run". The check to 178 kNm and 1,763 kN is not from my review, and I did not verify it.

The export copy is still untouched. My round-2 work is in the scratch folder `review_work/` (joint_r2/ and the check_r2_*.py scripts).

---

## What was done with round 2 (added by the author of the code)

- `MemoryError` dropped; `NotImplementedError` and `RecursionError` excluded from the numerical errors (they stop the run), with a test of both an excluded level error and a non-numerical preload error.
- The five wording fixes made. The memory sentence now gives the full medium-mesh measurement: the preload and one level of B-19 on the medium mesh, peak 2.6 GB (2,616 MB, process maximum resident set).
- NaN in records, `config_sha256` not checked by `verdict`, and fsync: left as they are.
