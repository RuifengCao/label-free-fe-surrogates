# G-F1: independent audit of the run and the verdict (7 November 2026)

Round 3 of the separate agent that reviewed the gate's code before tagging (rounds 1 and 2: `review_reports_G-F1_2026-11-07.md` in this folder). It worked on copies only. Report as returned, unedited apart from this header.

---

## G-F1 round 3: audit of the run (commit c423d91, tag prereg-f1)

**Bottom line.** The run and the verdict are sound. All 14 records are complete and consistent with run.log. My own code, without f1/verdict.py, reproduces every number in verdict.json exactly. Re-solving B-13 frictionless J2 on the coarse mesh reproduces its record exactly. **FAIL on C3 stands under the pre-registered rules.** Nothing in the code or the reading rules produced it spuriously. The margin is modest, though. The main cause is the nominal preload, which the pre-spec anticipated. The mesh effect on the J2 quantity itself is not measured.

### 1. Integrity: everything passes
- **Records:** 14 records, all parse, no .tmp files. Every record's case fields match its file name, and every record has config_sha256 = c2fdf0ff…1d87.
- **Convergence:**
  - Every preload converged and is within a relative 1e-6 of its target.
  - Every level converged. Every KKT value is within its limit by my own check: min_gap exactly 0, all others at most 4e-10. Newton needed at most 6 iterations.
- **Paths:**
  - Coarse paths use the configured steps, and the stop rule holds at the last level and at no earlier one.
  - The medium-mesh control values equal my own bracketing of the coarse elastic records.
- **run.log:**
  - It has the two "#" lines and the 14 cases in pre-spec order. Every record's levels equal its log lines (value, M, T, Θ_D, δ, converged, kkt_ok).
  - The 12 cases logged before the restart are exactly the 12 "exists, skipped" lines.
  - The case that was cut off (T-13 frictionless medium) had logged no level. That fits its 1,024 s run after the restart.
  - Record timestamps are in case order. The 12 records' times sum to 6,669 s; adding the 330 s of the interrupted case gives the 7,000 s window.

### 2. Recomputation (my own code, no f1/verdict.py)

| Item | Frictionless | No-slip | Test ± tol | Holds |
|---|---|---|---|---|
| C1 | 41.680 | 82.474 | 75.00 ± 4.81 | yes |
| C2 | 2.074 | 0.811 | 0.934 ± 0.051 | yes |
| **C3** | **49.590** | **34.786** | **55.57 ± 3.48** | **no: 2.504 kN above the top of the bracket (53.068)** |
| C1 elastic | 41.70 | 82.49 | 75.00 ± 4.81 | yes |
| C3 elastic | 59.79 | 35.24 | 55.57 ± 3.48 | yes |
| C2 elastic | 1.784 | 0.807 | 0.934 ± 0.051 | yes |
| C1 measured preload | 41.01 | 80.90 | 75.00 ± 4.81 | yes |
| C3 measured preload | 57.61 | 40.68 | 55.57 ± 3.48 | yes |
| Moment at 0.0005 rad (J2 and elastic) | 22.55 | 45.31 | 59.50 ± 7.36 | no |

- **Mesh flags** (medium/coarse ratio):
  - B-13 frictionless: C1 0.9979, C3 1.0177.
  - B-13 no-slip: C1 1.0033, **C3 1.0328 (flagged)**.
  - T-13 C2: 1.0073 frictionless, 0.9990 no-slip.
- **Comparison with verdict.json:** the verdict is FAIL in both, and the largest difference in any value is 0.

### 3. Test readings
verdict.json's test readings equal the pre-spec table: 75.00 ± 4.81, 55.57 ± 3.48, 0.934 ± 0.051 and 59.50 ± 7.36. They also equal my own recomputation from the CSV files, done with separate code.

### 4. Re-solve of B-13 frictionless J2, coarse mesh
I ran `python -m f1 run --sha c2fd… --case B-13_frictionless_hencky_nominal_coarse` from a copy of the c423d91 export, and the hash guard passed. It took 11 minutes on one thread. All 11 levels match the gate's record in every field except the timings: config_sha256, on_target, KKT values, plastic points and iteration counts. config.json is also identical.

### 5. How robust is the C3 failure?
- **Interpolation error.** Reading every other level changes the frictionless C3 by −0.466 kN, which confirms your 0.47. At the configured step the error is about a quarter of that, roughly 0.12 kN.
  - Quadratic and cubic readings through the neighbouring levels give 49.68 to 49.79 kN, so +0.09 to +0.20 kN.
  - Almost all of it comes from the 25 kNm point, where bolt 1's force curve bends upward, so the straight-line reading slightly underestimates C3.
  - The corrected gap is therefore about 2.3 to 2.4 kN.
- **Mesh effect.** For the elastic frictionless C3, medium against coarse is +1.77% (+1.06 kN). Applied to the J2 value it would add 0.88 kN, leaving a gap of about 1.4 to 1.5 kN.
  - The mesh effect on the J2 quantity itself is not measured, because the mesh flag uses elastic models by design.
  - On the coarse mesh, yielding lowers the frictionless C3 by 10.2 kN (59.79 elastic to 49.59 J2), four times the gap. The plate starts to yield at about 44 kNm, the weld at 54 and the tube at 90; at 98 kNm, 563 plate points have yielded.
  - A change of about 15% in that yielding effect with a finer mesh would close the rest of the gap.
  - I tried a sensitivity run with 3 plate layers instead of 2, outside the gate. Within the 10-minute limit it reached only the 25 kNm point: 126.59 against 126.62 kN. It never reached the 100 kNm point, where the yielding acts, so this question stays open.
- **Preload, the main cause.** B-13's bolts 1 and 2 carried 109.0 and 104.4 kN at 25 kNm; the gated models use 125 kN.
  - With the measured preloads (a reported item), the frictionless C3 is 57.61 kN, the bracket is 37.20 to 61.08, and C3 holds.
  - Lowering bolt 1's preload by about 16 kN raises the model's increase by about 8 kN.
  - The pre-spec's "If the gate fails" section lists this cause.
- **Reading rules checked:**
  - **Bolt identity.** At 100 kNm the test's lower dotted series reads 139.0 kN. That lies between the model's bolt 2 at 45° (153.1 frictionless, 133.2 no-slip, measured preload) and far from bolt 1 (168.9 and 151.5). So bolts 1 and 2 are the 15° and 45° bolts, as the rule assumes.
  - **Which series is bolt 1 at 25 kNm.** Taking either dotted series gives a test value of 53.30 or 57.85 kN. Both are above the top of the bracket (53.07), so the choice does not cause the failure.
  - **Moment pixel.** One pixel of moment (0.58 kNm) moves the 100 kNm test reading by about 0.3 to 0.45 kN. The tolerance does not include this, but it is small.
  - **Sparse data.** The 100 kNm reading rests on only 3 digitised points between 90 and 110 kNm.

### Housekeeping
I worked only on copies in review_work/r3/ and wrote nothing to the repository or to the export. The export already contains `__pycache__` folders and rewritten records/f1_dry output files, all timestamped 17:37 to 17:38, before the run; their contents are identical to the committed files.
