# G-F1: exploratory runs after the verdict (E1 to E3)

**Status.** Written on 8 November 2026 and hashed into `PLAN_HASH.txt`, with `explore.py`, before any of these runs. Exploratory: no hypothesis is tested and no verdict is given. The verdict of gate G-F1 (`docs/G-F1_verdict.md`: FAIL, C3 not holding) stands unchanged. Every result is reported, including any that goes against the expectations written here. Requested by the project owner on 8 November 2026 ("as recommended"), after an evaluation note of the same day.

**Code.** The gate's code is imported unchanged; `explore.py` checks every file listed in `docs/G-F1_code.sha256` against its hash before it runs anything. The only new code is `explore.py`. It changes the gate's set-up on copies of the configuration in memory, and, for E3's bolts only, by replacing `f1.run.model` inside its own process with the same function plus a bolt curve. Every path of `explore.py` was run on the tiny meshes before the hash; those numbers are not used. They were seen, though: the sentence on the bolt law's last force and the expectation on bolt 1's force under E3 were added after the tiny runs showed the yielded bolt levelling off, and the tiny meshes' moments in E3 were seen too. Apart from a corrected section reference to the thesis, nothing else in this plan was changed after a tiny run.

**Shared settings.** As in the gate unless stated: J2 deformation theory (`hencky`) for the plate, tube and weld (`f1/materials.py`); the configuration's contact solver, tolerance and KKT limits; the preload set at zero load; readings relative to the preload state; values at comparison points read by `f1.verdict.at_point` and `f1.verdict.model_quantity` (linear between the two bracketing levels); test values read by `f1.readings`. Case records are written whole when each case ends.

## E1. The mesh and C3

**Purpose.** Does the coarse mesh account for C3's miss? The verdict says the mesh is not excluded: the mesh flag uses elastic models by design, and yielding lowers the frictionless C3 by 10.2 kN on the coarse mesh.

**E1a, check.** B-13, frictionless, J2, nominal preload, coarse mesh, at the control values V: those that `f1.run.bracket_values` gives for the gate's record `B-13_frictionless_hencky_nominal_coarse` (the last level below each gated comparison point and the two after), with 0.006 added. Each level is warm-started from the previous one, so the steps differ from the gate's path. At every control value of V that the gate's record also has, M, Theta_D and the six bolt forces must equal the record's to a relative 1e-6. Deformation theory has no history, so the solution at a control value should not depend on the steps taken to reach it. If the check fails, nothing further runs and the failure is reported.

**E1.** The same case and control values on the medium mesh (three plate layers against the coarse mesh's two, and finer in plan; `fejoint.chs.MESHES`).

**Reported.** C3 and C1 on the medium mesh, next to the coarse values; bolt 1 at 25 and 100 kNm; plastic points; the ratio of the medium C3 to the coarse C3, next to the elastic mesh flag's 1.018.

**Reading, written before running.** The test less its tolerance is 52.09 kN (55.57 - 3.48).
- Medium C3 of at least 52.09 kN: the mesh alone can account for the miss.
- Medium C3 within 1.5 kN of the coarse 49.59 kN: the mesh is not the main cause.
- Otherwise: reported as found, without a reading.

**Expectation.** The medium value 1% to 4% larger, 50.1 to 51.6 kN. This is uncertain, because three layers resolve the yielding through the plate's thickness better than two.

## E2. One preload value in every bolt

**Purpose.** (i) Does one preload value in every bolt reproduce the gate's measured-preload results? This decides whether a single preload input can stand for the uneven measured set in a surrogate. (ii) How sensitive is C3 to the preload?

**Cases.** B-13, frictionless and no-slip, J2, coarse mesh, every bolt at P = 111.46 kN and at P = 100 kN; the configured steps and stop rule; four paths. P = 111.46 kN is the mean of the six forces of the gate's measured-preload case (`f1.readings.measured_preload` of Fig. 3.4 at 25 kNm: 108.98, 104.43, 126.25, 102.29, 115.80 and 111.03 kN), computed by `explore.py` from the data, not typed in. The preload is set on a copy of the configuration (`preload_kN`); the records are labelled `uniform-mean` and `uniform-100`.

**Reported.** C1, C3 and the moment at Theta_D = 0.0005 rad for each case, next to the gate's nominal (125 kN) and measured-preload values.

**Reading, written before running.**
- (i) If, for both bounds, C3 at P = 111.46 kN lies within 1 kN of the measured-preload C3 and C1 within 1 kNm of the measured-preload C1: one preload value reproduces the uneven set for these quantities. Otherwise the unevenness matters, and the quantities and bounds that differ are reported.
- (ii) The frictionless C3 against P, linear between the points at 100, 111.46 and 125 kN (the gate): P*, the preload at which it equals 52.09 kN, that is the uniform preload below which C3 would have held while the no-slip C3 stays the lower value. Reported to the nearest 0.5 kN; not a criterion.

**Expectation.** The frictionless C3 at 111.46 kN about 56 to 57 kN, within 1 to 2 kN of the measured-preload 57.61 kN, so (i) may go either way; P* about 118 to 122 kN.

## E3. Towards the resistance

**Purpose.** How far each bound lies from the tests beyond the gate's range, up to Theta_D = 0.01 rad, where the test curves bend over. The answer informs the owner's choice of the reference energy for the surrogate (rule below).

**Cases.** B-13 and B-19, frictionless and no-slip, J2, coarse mesh, nominal preload; four paths. B-19 uses the dry configuration (`f1.config.config(True)`), B-13 the gate's.

**Changes from the gate**, on copies inside `explore.py`:
1. **Elastic-plastic bolts** (the gate's are elastic, which is enough up to about 100 kNm but not towards the resistance). The half bolt keeps the gate's spring stiffness E_b A_s / (L_b / 2), with E_b = 217,100 MPa and A_s = 213.8 mm². It is elastic up to the force A_s f_yb, with f_yb = 817 MPa (thesis Table 2.2, A325T), about 174.7 kN. Beyond that its force follows, in engineering terms, the bolt coupon curve (`f1/data/material_bolt_eng.csv`, Fig. 2.18(d)), by the rule that `f1/materials.py` applies to the plates' curves: the curve between strains 0.004 and eps_u = 0.058 (Table 2.2) is made non-decreasing; from the point (f_yb / E_b, f_yb), each point more than 1e-4 in strain beyond the last one kept and not lower in stress is kept; the points are thinned to at most 14 (evenly by index, the first and last kept). Each point is taken as extension eps L_b / 2 and force sigma A_s, and the force stays at the last point's value beyond it. The force is non-decreasing in the extension, so the energy stays convex (`fejoint.nlsolve.AxialSprings`). The last point's force is 201.0 kN, about 4% below the mean strength of the four full-size bolts tested to failure, 210 kN (thesis Section 2.3.3); where the bolts govern, the model is weaker by up to that much.
2. **Steps and cap.** Steps of 0.001 rad in the end-section rotation (the gate's 0.0005 rad), with a cap of 0.05 rad (the gate's 0.03 rad).
3. **Stop.** The path stops after the first level with Theta_D of at least 0.0105 rad and M of at least 105 kNm (the gate's moment condition). This is done by setting the stop rule's comparison rotation to 0.00875 rad on the copy.

**Check, before anything else is read.** At every control value that an E3 path shares with the gate's coarse J2 nominal record (the dry-run record for B-19), at levels where no bolt exceeds A_s f_yb in either record, M, Theta_D and the six bolt forces must agree to a relative 1e-6. If they do not, the failure is reported and nothing else of E3 is read.

**Reported.**
- M at Theta_D = 0.002, 0.003, 0.005, 0.0075 and 0.01 rad, with the test (`f1.readings.moment_reading`, both figures) and the author's finite element model FE (3) (Fig. 3.7, digitised: `B13_FE3_fig37.csv`, `B19_FE3_fig37.csv`), and the ratios to the test.
- Bolt 1's force at M = 100, 125, 150 and 175 kNm wherever the path and the test's upper dotted series both reach, against that series (the figure labels it bolt 1 above about 75 kNm; the gauges were used up to 180 kN).
- The first level at which a bolt exceeds A_s f_yb; plastic points; any decrease of a yielded bolt's force along the path. The bolts' deformation-theory law holds only while a yielded bolt does not unload; with a non-decreasing law, a falling force means unloading.

**Rule for the choice of the reference energy, written before running** (from the evaluation note of 8 November 2026). Take the ratio r of model to test at Theta_D = 0.005 and 0.01 rad for B-13 and B-19. A bound *holds* when its four ratios all lie within [0.90, 1.10]; a value that is not reached counts as not holding.
- Frictionless holds and no-slip does not: train both bounds (envelope).
- Both hold: train both bounds; friction then governs the stiffness but not the resistance.
- No-slip holds and frictionless does not: train the no-slip bound only.
- For B-13 or for B-19, neither bound within [0.90, 1.10] at 0.01 rad: no surrogate yet; the reference model is reworked in this range first.
- Any other outcome: train both bounds, with the ratios reported.
The rule informs the owner's choice; it does not make it. The 10% band is the author's own model's distance from the tests in this range: 2% to 4% (B-13) and 6% to 11% (B-19) between 0.004 and 0.01 rad.

**Expectation.** Frictionless within 10% of the tests at both rotations for both specimens: a development run on B-19 with a different bolt law gave 0.92 at 0.005 rad and 0.96 at 0.009 rad. No-slip more than 10% above the tests at 0.005 rad for both specimens; its ratio was 1.07 to 1.10 at 0.001 rad and rising. So the first outcome: train both bounds. Once bolt 1 yields, its force levels off near 175 to 180 kN, below the test's readings above 175 kN (the digitised series reach about 190 kN).

## Runs

- **Host.** Linux, two cores, the environment of the gate's run: Python 3.13.17, numpy 2.5.3, scipy 1.18.1 (OpenBLAS 0.3.34), SuperLU.
- **Processes.** Two at a time, each with one thread for the numerical libraries; windows of at most two hours.
- **Restarts.** A case with a record is skipped, so a window that is cut off is continued with the same command.
- **Order.** E1a, then E1, then E2 in one process; E3's four paths in the other.
- **Outputs.** In `probes/f1_explore/`: `records/` (one JSON record per case, carrying the SHA-256 of its configuration copy and of the unmodified configuration), `run.log`, and `RESULTS.md` (the tables and the readings by the rules above, written by `python probes/f1_explore/explore.py tables`).

## Rules

- This plan and `explore.py` are hashed into `PLAN_HASH.txt` before any of these runs. Any later change is written into `DEVIATIONS.md`, with its reason, before it is made.
- No result is excluded. All of this is labelled exploratory, after the verdict and not pre-registered, here and in any paper.
