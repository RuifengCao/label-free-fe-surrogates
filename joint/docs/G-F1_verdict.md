# Gate G-F1: verdict

**Verdict: FAIL.** C1 and C2 hold; C3 does not.

**What was pre-specified**
- `docs/PRESPEC_G-F1.md`, configuration SHA-256 `c2fdf0fff32fd24f3714f8231b3d6e87a83bbf7d268ef2a1283f02c78c051d87`, stamped at 17:18 GMT on 7 November 2026. That stamp replaced a first one (03:08 GMT, commit `e966200`), which was never tagged or run; the pre-specification says why.
- The tag `prereg-f1`, made by the project owner at 18:07 GMT the same evening, points to commit `c423d91`. The run used that commit, unchanged.

**Where the numbers come from**
- Every number below comes from `records/G-F1/verdict.json` and `records/G-F1/numbers.md`, which `python -m f1 verdict` wrote from the 14 case records in `records/G-F1/records/`.
- **Independent audit** (7 November 2026), with its own code:
  - The 14 records are complete, carry the stamped configuration hash, converged at every level within the KKT limits, and agree with `run.log` level by level, including the restart.
  - Every criterion, reported item and mesh flag, recomputed from the records without `f1/verdict.py`, equals `verdict.json`; so does the verdict. The test readings equal the pre-specification's table and a separate reading of the data files.
  - `B-13_frictionless_hencky_nominal_coarse`, solved again from the tagged commit, reproduced its record in every field but the timings.

## Criteria

J2 deformation theory, coarse mesh, nominal preload of 125 kN. A criterion holds when the test value lies within [min - tol, max + tol] of the two bounds' values.

| Criterion | Specimen | Test | Tolerance | Frictionless | No-slip | Holds |
|---|---|---|---|---|---|---|
| C1: moment at $\Theta_D$ = 0.001 rad (kNm) | B-13 | 75.00 | 4.81 | 41.68 | 82.47 | yes |
| C2: mean LVDT displacement at 800 kN (mm) | T-13 | 0.934 | 0.051 | 2.074 | 0.811 | yes |
| C3: increase of bolt 1's force from 25 to 100 kNm (kN) | B-13 | 55.57 | 3.48 | 49.59 | 34.79 | **no** |

- C1 and C2 lie nearer the no-slip end.
- C3: the bounds widened by the tolerance span 31.31 to 53.07 kN. The test value lies 2.50 kN above that range, and 5.98 kN above the frictionless value.
- Every model value has the status "ok": the paths reached the comparison points, and every level up to them converged within the KKT limits.

## Run record

- **Host**: Linux, two cores, the environment of the dry run. Python 3.13.17, numpy 2.5.3, scipy 1.18.1 (OpenBLAS 0.3.34); the linear systems were solved with SuperLU.
- **First window**: started at 18:07:41 GMT from the tagged commit, clean. The guard checked the configuration hash and the 35 files of `docs/G-F1_code.sha256`. The window was cut off by its time limit (`timeout 7000`) at 20:04:22, during the case `T-13_frictionless_elastic_nominal_medium`, before that case wrote anything. Twelve records were whole; none was cut off, and no temporary file was left.
- **Second window**: the same command, started at 20:04:38. It kept the twelve records ("exists, skipped" in `run.log`), ran the last two cases and ended at 20:35:33.
- **Verdict**: `python -m f1 verdict` at 20:35, after `sha256sum -c docs/G-F1_code.sha256` passed again.
- The 14 records hold 114 levels. Every level converged within the KKT limits, with at most 6 Newton iterations; every preload state was on its targets. Each record carries the configuration's SHA-256. The records' own times add up to 8,512 s (2 h 22 min).
- `run.log` is the progress output of both windows. Its two lines starting with `#` were written by the commands that started the windows.

## Reported, not part of the verdict

| Item | Specimen | Test | Tolerance | Frictionless | No-slip | Within |
|---|---|---|---|---|---|---|
| C1, elastic | B-13 | 75.00 | 4.81 | 41.70 | 82.49 | yes |
| C3, elastic | B-13 | 55.57 | 3.48 | 59.79 | 35.24 | yes |
| C2, elastic | T-13 | 0.934 | 0.051 | 1.784 | 0.807 | yes |
| C1, measured preload (J2) | B-13 | 75.00 | 4.81 | 41.01 | 80.90 | yes |
| C3, measured preload (J2) | B-13 | 55.57 | 3.48 | 57.61 | 40.68 | yes |
| Moment at $\Theta_D$ = 0.0005 rad (J2 and elastic) | B-13 | 59.50 | 7.36 | 22.55 | 45.31 | no, above both |

**Mesh flag** (elastic, medium against coarse; flagged above 2%):

| Quantity | Coarse | Medium | Ratio | Flagged |
|---|---|---|---|---|
| B-13 frictionless C1 | 41.70 | 41.61 | 0.998 | no |
| B-13 frictionless C3 | 59.79 | 60.85 | 1.018 | no |
| B-13 no-slip C1 | 82.49 | 82.77 | 1.003 | no |
| B-13 no-slip C3 | 35.24 | 36.40 | 1.033 | yes |
| T-13 frictionless C2 | 1.784 | 1.797 | 1.007 | no |
| T-13 no-slip C2 | 0.807 | 0.806 | 0.999 | no |

**Paths**
- The first plastic points, all in the plate, appeared at these levels: B-13 frictionless at $\Theta_D$ = 0.0011 rad (43.8 kNm), B-13 no-slip at 0.0009 rad (77.5 kNm), T-13 frictionless at 337 kN, T-13 no-slip at 708 kN.
- Reading the gated paths with every other level (twice the step) changed the values by at most 0.24 kNm (C1), 0.47 kN (C3) and 0.015 mm (C2). The error of the linear reading falls with the square of the step, so at the configured steps it is about a quarter of that. A quadratic or cubic reading through the neighbouring levels gives a frictionless C3 0.09 to 0.20 kN higher, mostly from the 25 kNm point, where bolt 1's force curve bends upward.
- Every path, with its moments, rotations, displacements, bolt forces, KKT residuals and plastic Gauss points, is in `records/G-F1/records/`.

## Against the expectation stated before the run

- "C1 likely holds": it held, nearer the no-slip end.
- "C3 likely holds, nearer the no-slip end": it did not hold. The test lies beyond the frictionless end.
- "C2 is uncertain": it held, near the no-slip end.
- "The point at 0.0005 rad may again lie above both bounds": it did.
- "C3's mesh flag may be raised again": it was, for the no-slip bound (3.3%); the frictionless bound moved by 1.8%.

## The candidate causes listed before the run

The pre-specification lists them and says that no part of the model is changed after the run. What the reported results say about each, without deciding between them:

- **B-13's uneven preload.** With the measured preloads (109.0, 104.4, 126.2, 102.3, 115.8 and 111.0 kN; reported only), C3's bounds are 57.61 and 40.68 kN, and the test lies between them; C1 also holds.
- **The material model.** With elastic models, C3's bounds are 59.79 and 35.24 kN and contain the test. Yielding in the J2 model lowers the frictionless bound by 10.2 kN; on that path the plate yields from 44 kNm, the weld from 54 kNm and the tube from 90 kNm.
- **The coarse mesh.** On the medium mesh (elastic), bolt 1's increase was 1.8% larger for the frictionless bound. If the J2 frictionless value moved by as much, it would be about 50.5 kN, still below 52.09 kN, the test less its tolerance. But the mesh effect on the J2 value was not measured: the mesh flag uses elastic models, and yielding lowers this value by 10.2 kN on the coarse mesh, four times the gap. A change of about 15% in that effect on a finer mesh would close the gap, so the mesh is not excluded.
- **The digitising.** C3's tolerance is half the spread of the two dotted series at 25 kNm plus two pixels. The miss, 2.50 kN beyond it, is about four pixels of force. Taking either dotted series alone as bolt 1 at 25 kNm gives 53.30 or 57.85 kN, both above the bracket. One pixel of moment, not in the tolerance, moves the reading at 100 kNm by 0.3 to 0.45 kN; that reading rests on three digitised points between 90 and 110 kNm. At 100 kNm the lower dotted series (139.0 kN) lies near the model's bolt 2 at 45 degrees and far from its bolt 1, as the identification of bolts 1 and 2 assumes.
- **The rotation's definition** does not enter C3, which uses moments and bolt forces only.
- **The plates' out-of-flatness, and friction under the heads and nuts or the shanks bearing on the hole walls**, are not examined by this run.

## What it means

The gate asked whether each measured quantity lies between the frictionless and no-slip bounds. Two of three do: the moment at 0.001 rad and the axial displacement at 800 kN lie between the bounds, near the no-slip end. Bolt 1's force rises from 25 to 100 kNm by more than the frictionless model gives with the nominal 125 kN preload. Under the pre-specified rule, the two splice bounds of this model do not explain the whole response of B-13 and T-13, and G-F1 fails.

The pre-specification ties the gate to the choice of the reference energy for the tubular case's surrogate. That choice is the project owner's and is not made here.
