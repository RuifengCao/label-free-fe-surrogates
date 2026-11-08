# G-F1 exploratory runs: independent review (8 November 2026)

A separate agent reviewed the exploratory runs E1 to E3 (`joint/probes/f1_explore/`) after they ended, working on a copy of the repository only. Report as returned, unedited apart from this header; its last paragraph, a note on the stored project conventions it used, is left out. Its scripts and outputs are in this folder: `check_records.py`, `recompute.py`, `compare_records.py`, `rerun_b19ns_ext.py`, `recompute_full.txt`, `rerun_b19ns_extensions.json`. The paths it quotes under `/tmp/review_f1x` were on the sandbox and are not kept.

---

**Bottom line.** The runs and RESULTS.md are sound:
- **Numbers:** every number in RESULTS.md recomputes from the CSV files and records with my own code to within its printed rounding.
- **Hashes:** they match, and the gate code check passes.
- **Records:** all 10 converged, on their preload targets and within the KKT limits.
- **Reproducibility:** RESULTS.md is byte-identical to a fresh `explore.py tables` run, and a re-solved E3 case reproduced its record in every field.

The four readings follow the plan's rules literally: E1 "not the main cause", E2 (i) "unevenness matters", E2 (ii) P* = 120.0 kN, E3 "envelope". I found no MUST FIX. RESULTS.md does leave out results that go against the plan's stated expectations (yielded bolts rising to 198 to 201 kN; two B-19 no-slip bolts strained past eps_u), and the E1 and E2 (i) readings are worded more strongly or less completely than the numbers support.

## 1. Plan against code
The code matches the plan on every point that affects a result:
- **E1a/E1 control values:** `R.bracket_values` of the gate record plus 0.006 gives V = [0.001, 0.0015, 0.002, 0.0025, 0.005, 0.0055, 0.006]. My own bracket code gives the same.
- **Meshes:** coarse, and medium (n_tp 3 against 2).
- **E2 preloads:** 111.46268518518518 kN, exactly the np.mean of my own reading of Fig. 3.4 at 25 kNm, and 100 kN. Set via `preload_kN` on a deep copy; configured steps and stop rule.
- **E3 settings:** step 0.001, cap 0.05. The stop is `theta = 0.0105/1.2`, which equals 0.00875 exactly in floating point, and `1.2*0.00875 == 0.0105`. M >= 105 for both specimens (bolt moments [25, 100]); B-19 uses `config(True)`.
- **Bolt law:** `bolt_points()`/`bolt_curve()` (explore.py 242-260) implement the plan's line 47 exactly: engineering stress made non-decreasing on strains 0.004 to 0.058; start at (f_yb/E_b, f_yb); 1e-4 spacing; thinned to 14 points; flat beyond the last point (`slope_end` 0.0). Continuity with the elastic branch is exact (k_ax·e_p[0] − N_p[0] = 0.0 N, checked for L_b 44.275 and 57.675 mm). The curve is strictly increasing (all 13 slopes positive), and the last force is 200.993 kN.
- **`f1.run.model` replacement** (explore.py 268-272): line for line `f1/run.py` 59-63. The only differences are the dropped type annotations, `R.geometry` (the same object) and `bolt_curve=bolt_curve(g)`. `run_path` resolves `model` at call time, and the original is restored after each case.
- **Checks:** E1a (lines 193-196) and E3 (lines 428-435) at relative 1e-6.
- **Reading logic:** E1, E2 (i), E2 (ii) and the E3 rule all follow the plan. The pause test can only be true when neither bound holds, so the branch order (481-490) is equivalent to the plan's.

Small mismatches, none of which changes a result:
- a. E1 (372, 374) and E2 (ii) (413) use the unrounded edge 52.0941 where the plan says 52.09; P* is 120.039 with it and 120.047 with 52.09. E1 uses `abs(...) < 1.5` where the plan says "within"; E2 (i) uses `<=`.
- b. "Exceeds A_s f_yb" is coded as `>=` (154, 465). A recount with `>` gives identical counts.
- c. The unloading test has an unstated relative tolerance of 1e-9 (470).
- d. Zero common levels counts as a failed check (195, 429), and an 'invalid' status counts as not holding. Neither is in the plan; both are sensible.
- e. Bolt table (451-459): a row is printed when any of test, frictionless or no-slip reaches M. The plan (line 55) says "wherever the path and the test's upper dotted series both reach". So RESULTS.md lines 72-73 give model values at 150 and 175 kNm, where the B-13 series ends at 142.4 kNm.
- f. The pause text (488) drops "the reference model is reworked in this range first"; the both-hold text (484) drops "then". Neither outcome was triggered.
- g. The mesh flag 1.0177 is hard-coded (370), not computed. My value from the gate's elastic records is 1.01769.
- h. `guard()` runs after the gate modules are imported (41-46 against 511), so "before it runs anything" holds for solves, not imports. Threads are set with `setdefault` (22-23), so an inherited value would win.
- i. The Cases table's "KKT ok" column (342) ignores the preload's `kkt_ok`. All preload values are true.
- j. The E2 relabel (136) happens after `run_path` logs (`f1/run.py` 152). So run.log's E2 lines carry `"preload": "nominal"`.

## 2. Hashes
- `sha256sum` of EXPLORE_PLAN.md (00ebfaba…2229f64) and explore.py (740f38f1…0bcbc2) equals PLAN_HASH.txt.
- `sha256sum -c docs/G-F1_code.sha256` passes for all 35 files, and `git diff HEAD` shows f1/, fejoint/ and the gate and dry records unchanged.
- run.log lines 1-2 carry 00ebfaba8e93 / 740f38f10952 and "35 files".
- File times agree with the claimed order: explore.py 01:00:48, plan 01:11:23, PLAN_HASH.txt 01:19:17, first run line 01:19:44 UTC.

## 3. Records
All 10 pass every check:
- They parse, and the case fields match the file names.
- **Preload:** converged and on target; worst relative error 8.1e-11 (125 kN, 111.4627 kN, 100 kN).
- **Levels:** all 123 converged and within KKT_LIMITS by my own check. Worst values: min_gap 0, min_lambda −1.8e-12, complementarity 9.8e-13, lambda_inactive 4.2e-12, residual 1.4e-11.
- **run.log:** the 123 level lines match the records in value, M (to 3 decimals), Theta_D, delta, converged, kkt_ok and s, and each case_done equals the record's seconds.
- **Metadata:** correct.
- **config_sha256:** equals the SHA-256 of my own rebuilt copies and of the copies built by explore.py's functions.
- **base_config_sha256:** c2fdf0ff… is the gate's hash (records/G-F1/config.json). d5f71fcd… for B-19 matches records/f1_dry/config.json and verdict.json; the dry records themselves carry no config_sha256, which predates this work.
- **Stop rules and cap:** E2 and E3 stop at the first level that meets the rule.
- **E3 yielded bolts:** no yielded bolt's force decreases. The smallest increments after yield are 0.148 to 0.775 kN, except bolt 1 of B-19 no-slip, whose force stays at exactly 200.99338 kN from control 0.017 to 0.021 (bolt 2 reaches it at 0.021). That is the law's flat end, where a force check cannot see unloading. I re-solved that path and recorded the extensions: the record was reproduced exactly (791 of 791 values), and every yielded bolt's extension rises strictly (smallest step 0.0082 mm), so nothing unloads. Bolt 1 reaches an average strain of 0.088 (2.535 mm over L_b/2) and bolt 2 0.062, both beyond eps_u = 0.058.

## 4. Recomputation (own code; values listed as mine / RESULTS.md)
Every value lies within half a unit of its last printed digit. The largest difference is 0.049: B-19 test bolt 1 at 100 kNm, 139.3506 against 139.4.

| Item | Mine | RESULTS.md |
|---|---|---|
| Edge (test less tolerance) | 55.5722 − 3.4781 = 52.0941 | 52.09 |
| E1a check | 6 levels, 2.0258e-12 | 6, 2.03e-12 |
| E1 C3 coarse / medium / ratio | 49.5901 / 50.9689 / 1.02780 | 49.59 / 50.97 / 1.0278 |
| E1 C1 coarse / medium / ratio | 41.6805 / 41.5493 / 0.99685 | 41.68 / 41.55 / 0.9969 |
| E1 bolt 1 at 25 / 100 kNm, coarse; medium | 126.6176 / 176.2077; 126.9632 / 177.9321 | 126.62 / 176.21; 126.96 / 177.93 |
| Elastic mesh flag | 1.01769 | 1.0177 |
| E2 frictionless C1, C3, M(0.0005): nominal / measured / mean / 100 | 41.6805, 49.5901, 22.5542 / 41.0131, 57.6053, 22.1784 / 41.1076, 56.4224, 22.2467 / 40.5553, 62.2000, 21.9885 | 41.68, 49.59, 22.55 / 41.01, 57.61, 22.18 / 41.11, 56.42, 22.25 / 40.56, 62.20, 21.99 |
| E2 no-slip, same order | 82.4744, 34.7857, 45.3060 / 80.8972, 40.6831, 44.4796 / 81.1561, 39.6648, 44.5975 / 79.9209, 44.3694, 43.9644 | 82.47, 34.79, 45.31 / 80.90, 40.68, 44.48 / 81.16, 39.66, 44.60 / 79.92, 44.37, 43.96 |
| P* | 120.039, rounds to 120.0; no-slip C3 lower at all three preloads | 120.0 |
| E3 check (B-13 fr, B-13 ns, B-19 fr, B-19 ns) | 5 / 3.153e-12; 3 / 6.591e-12; 4 / 1.353e-12; 4 / 2.658e-12 | 5 / 3.15e-12; 3 / 6.59e-12; 4 / 1.35e-12; 4 / 2.66e-12 |
| B-13 test at 0.002, 0.003, 0.005, 0.0075, 0.01 | 96.160, 113.754, 137.736, 155.258, 166.782 | 96.2, 113.8, 137.7, 155.3, 166.8 |
| B-13 FE (3) | 90.509, 111.724, 132.996, 148.802, 163.962 | 90.5, 111.7, 133.0, 148.8, 164.0 |
| B-13 frictionless (r) | 74.468 (0.774), 100.343 (0.882), 129.272 (0.9385), 147.459 (0.9498), 158.883 (0.9526) | 74.5 (0.77), 100.3 (0.88), 129.3 (0.94), 147.5 (0.95), 158.9 (0.95) |
| B-13 no-slip (r) | 143.740 (1.495), 184.499 (1.622), 228.952 (1.662), 257.846 (1.661), 275.164 (1.650) | 143.7 (1.49), 184.5 (1.62), 229.0 (1.66), 257.8 (1.66), 275.2 (1.65) |
| B-19 test | 173.584, 203.234, 239.160, 264.052, 277.885 | 173.6, 203.2, 239.2, 264.1, 277.9 |
| B-19 FE (3) | 177.699, 210.195, 264.635, 287.262, 295.131 | 177.7, 210.2, 264.6, 287.3, 295.1 |
| B-19 frictionless (r) | 136.411 (0.786), 176.408 (0.868), 220.895 (0.9236), 251.775 (0.9535), 269.879 (0.9712) | 136.4 (0.79), 176.4 (0.87), 220.9 (0.92), 251.8 (0.95), 269.9 (0.97) |
| B-19 no-slip (r) | 217.676 (1.254), 264.634 (1.302), 326.780 (1.366), 362.518 (1.373), 380.797 (1.370) | 217.7 (1.25), 264.6 (1.30), 326.8 (1.37), 362.5 (1.37), 380.8 (1.37) |
| B-13 bolt 1 (test, fr, ns) at 100 / 125 / 150 / 175 kNm | 162.279, 174.652, 160.826 / 180.549, 175.434, 174.852 / n.r., 176.400, 175.470 / n.r., n.r., 176.448 | 162.3, 174.7, 160.8 / 180.5, 175.4, 174.9 / n.r., 176.4, 175.5 / n.r., n.r., 176.4 |
| B-19 bolt 1, same order | 139.351, 160.218, 143.919 / 148.200, 173.451, 156.603 / 162.271, 175.357, 171.421 / 177.278, 176.327, 174.582 | 139.4, 160.2, 143.9 / 148.2, 173.5, 156.6 / 162.3, 175.4, 171.4 / 177.3, 176.3, 174.6 |
| First level above yield (control, M, Theta_D) | B-13 fr 0.006, 111.424, 0.0035828; B-13 ns 0.004, 119.928, 0.0015617; B-19 fr 0.005, 141.094, 0.0020902; B-19 ns 0.005, 181.825, 0.0013722 | same, rounded |
| Plastic-point lists, Cases table (60 entries) | identical | |

The rising-branch details (dropping non-increasing rotations; the running maximum of M) change no test or FE (3) value. Rule: frictionless 0.9385, 0.9526, 0.9236, 0.9712 (holds); no-slip 1.66, 1.65, 1.37, 1.37 (does not). Full output: /tmp/review_f1x/recompute_full.txt.

## 5. Re-solve
`explore.py run E3 --case B-13_frictionless --out /tmp/review_f1x/rerun` passed the plan hash and the guard, and ran in 1305.5 s. All 641 leaf fields are identical to the stored record, timings excluded: levels, KKT values, plastic points, iterations, metadata and both hashes. There are no structural differences.

## 6. Repository hygiene
- No "claude" in any capitalisation, and no /home or /tmp paths, in the 15 new files.
- No en or em dashes; the only non-ASCII character is "²" in "mm²" (EXPLORE_PLAN.md line 47).
- British spelling throughout (digitised, labelled, levelling, towards); no American forms found.
- `__pycache__/explore.cpython-313.pyc` is git-ignored; `git status -uall` lists exactly the 15 intended files.

## 7. Anything else
Results against expectations, not reported (the plan, line 3, promises to report them):
- **Bolt 1 does not level off in three of four paths.** The plan's line 66 expects its force to level off near 175 to 180 kN. That holds for B-13 frictionless (177.1 kN at the end) but not for B-13 no-slip (200.3 kN), B-19 frictionless (198.2 kN) or B-19 no-slip (201.0 kN, the law's end). RESULTS.md stops the bolt table at 175 kNm and has no comparison with the expectations.
- **Two B-19 no-slip bolts pass eps_u.** Bolt 1 reaches 201.0 kN from control 0.017 (Theta_D 0.0083 rad, M 369.6 kNm) and goes on to a strain of 0.088; bolt 2 reaches 0.062. The B-19 no-slip moment at 0.01 rad (r 1.37) is read in that range. The outcome is unchanged: no-slip fails at 0.005 rad too, with bolts still inside the data.

Elastic gate bolts already pass A_s f_yb before 100 kNm:
- **Where:** on the gate's 125 kN frictionless path, bolt 1 passes 174.67 kN at 98.2 kNm and reads 176.21 kN at 100 kNm. On E1's medium mesh it passes at 96.1 kNm and reads 177.93 kN. E2's lower-preload paths stay below yield (170.0 and 164.9 kN).
- **Effect:** with E3's bolt law, the frictionless C3 at 125 kN would be about 48.1 kN (estimated from the E3 path), so P* would be about 118.5 kN rather than 120.0. The plan's "enough up to about 100 kNm" is marginal for C3, and the 1.5 kN shift is 60% of the 2.50 kN miss.

Wording of the readings:
- **E1:** the reading is literal, but the medium mesh closes 1.38 kN of the 2.50 kN gap to 52.09 (55%). The J2 mesh ratio (1.028) exceeds both the elastic flag (1.018) and the 2% limit, and two meshes give no convergence estimate. "Not the main cause" reads stronger than these numbers; the plan's 1.5 kN threshold is itself 60% of the gap.
- **E2 (i):** the plan (line 35) requires naming what differs; RESULTS.md line 50 defers to the table. C3 differs for both bounds (frictionless −1.18 kN; no-slip −1.02 kN, just beyond the threshold), and C1 is within for both (0.09 and 0.26 kNm).

Robustness of the E3 outcome:
- **Margin:** the smallest margin is 0.9236 against 0.90 (B-19, 0.005 rad).
- **Interpolation:** quadratic instead of linear reading changes the ratios by at most 0.12%.
- **Mesh:** E3 is coarse only.
- **Small rotations:** frictionless "holds" only at the rule's two rotations; at 0.002 to 0.003 rad its ratios are 0.77 to 0.88.
- **Author's model:** FE (3) itself is at 1.11 for B-19 at 0.005 rad.

Smaller points:
- **E3 bolt readings:** E3's 0.001 step coarsens the bolt readings. Bolt 1 at 25 kNm reads 126.85 against the gate's 126.62; no-slip at 100 kNm reads 160.8 against 161.3.
- **First yield:** the "first level" above yield (control 0.006, 111.4 kNm) is not the yield moment (about 98.2 kNm).
- **Gauge limit:** B-13's test bolt 1 at 125 kNm (180.5 kN) is at the 180 kN gauge limit given in the data file's header, although the series runs to 191.5 kN.
- **README.md, outside my scope:** `joint/README.md` in the original was modified at 02:56 UTC, after my copy was made, and will go out with the push. Its three new result sentences are correct as rounded: 2.9 to 7.6% below, 36.6 to 66.2% above, +1.38 kN, P* 120.04 kN and 3.97%. But "C3 would have held at 120 kN or less" extends below the lowest computed preload (100 kN), and the elastic-bolt caveat applies to the 120 kN figure. Its hygiene is fine (only ã and õ are non-ASCII).

## MUST FIX
None.

## SHOULD FIX
Do not hand-edit RESULTS.md or explore.py: the hashes and byte-reproducibility depend on them, and plan line 78 requires a DEVIATIONS.md entry first. Put these in a dated addendum labelled as written after the results.
1. **Bolt law beyond eps_u:** state that bolts 1 and 2 of B-19 no-slip pass the law's last point and eps_u (from control 0.017 and 0.021), that the force check is blind there, and that a re-solve showed the extensions rising (no unloading).
2. **Expectations:** add a comparison with the plan's expectations. Bolt 1's "levels off near 175 to 180 kN" fails for three paths (198 to 201 kN); E1, E2 and the E3 ratios were as expected.
3. **E1:** add the 55% gap fraction, the J2 ratio of 1.028 against the elastic flag of 1.018, and "two meshes only".
4. **Elastic bolts:** note that bolt 1 passes A_s f_yb at 98.2 kNm (96.1 kNm medium); with E3's law, C3 at 125 kN would be about 48.1 kN and P* about 118.5 kN.
5. **E2 (i):** name the quantities and bounds that differ (C3 for both bounds, −1.18 and −1.02 kN; C1 within).
6. **Bolt table:** note that its rows go beyond plan line 55 (values where the test series does not reach).
7. **run.log:** note that its E2 lines are labelled "preload": "nominal", while the records are labelled correctly.

## NOTE
- Threshold details 1a to 1d and 1f to 1i above.
- The stop threshold is exact in floating point.
- The dry records lack config_sha256; the B-19 base hash checks against records/f1_dry/config.json.
- E3 margins, interpolation, step and first-yield remarks as in section 7.
- Gauge limit at 180 kN.
- Cosmetic, all from the hashed code:
  - RESULTS.md line 100 prints the tuple "(0.005, 0.01)".
  - The E3 plastic-point lists (lines 75, 77, 96, 98) lack the legend "(plate, tube, weld, bolts)".
  - The E3 check line (56) has no "passed".
  - run.log's two "done" lines (115, 138) are not labelled by process.
- README.md: see section 7.

Scripts and outputs, all in /tmp/review_f1x:
- /tmp/review_f1x/scripts/check_records.py
- /tmp/review_f1x/scripts/recompute.py
- /tmp/review_f1x/scripts/compare_records.py
- /tmp/review_f1x/scripts/rerun_b19ns_ext.py
- /tmp/review_f1x/recompute_full.txt
- /tmp/review_f1x/rerun/records/E3_B-13_frictionless_hencky_nominal_coarse_ep-bolts.json
- /tmp/review_f1x/rerun_b19ns/record.json and /tmp/review_f1x/rerun_b19ns/extensions.json

Nothing was written to the original repository.
