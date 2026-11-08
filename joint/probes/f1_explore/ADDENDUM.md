# G-F1 exploratory runs: addendum written after the results

Written on 8 November 2026, after `RESULTS.md`, from an independent review of the runs. Nothing in `EXPLORE_PLAN.md`, `explore.py`, the records, `run.log` or `RESULTS.md` was changed: they are hashed or reproducible byte for byte, and this note only adds to them.

**Review.** The reviewer worked on a copy of the repository and found no error in a number, a rule or the code:
- Every number of `RESULTS.md` was recomputed with separate code, without `explore.py`'s tables, `f1.verdict` or `f1.readings`, to within its printed rounding.
- The hashes of the plan and the driver equal `PLAN_HASH.txt`, and the gate's code check passes.
- All 10 records converged, on their preload targets and within the KKT limits; they agree with `run.log` level by level.
- `RESULTS.md` is byte-identical to a fresh `explore.py tables`.
- The case `E3_B-13_frictionless_hencky_nominal_coarse_ep-bolts`, solved again from the copy, reproduced its record in every field but the timings.

The points below complete the reading of the results.

## Results against the expectations of the plan

- **E1.** Expected 1% to 4% larger on the medium mesh: it was 2.8% larger (50.97 against 49.59 kN), as expected.
- **E2.**
  - The frictionless C3 at 111.46 kN was expected at about 56 to 57 kN: it was 56.42 kN.
  - Reading (i) was expected to go either way: it went against a single value, narrowly.
  - P* was expected at about 118 to 122 kN: it was 120.0 kN.
- **E3, moments.** As expected: frictionless within 10% of the tests at both rotations for both specimens, no-slip more than 10% above them at 0.005 rad, so the first outcome of the rule.
- **E3, bolt 1: not as expected.** The plan expected bolt 1's force to level off near 175 to 180 kN once it yields. It does so only for B-13 frictionless (177.1 kN at the last level). In the other three paths it goes on rising, to 200.3 kN (B-13 no-slip), 198.2 kN (B-19 frictionless) and 201.0 kN, the bolt law's last point (B-19 no-slip).

## The bolt law at large extensions

- In B-19 no-slip, bolt 1 reaches the law's last point (201.0 kN) from the level at control 0.017 (Theta_D 0.0083 rad, 369.6 kNm), and bolt 2 at control 0.021. They then lie on the law's flat end, beyond the coupon's uniform strain eps_u = 0.058: bolt 1 reaches a mean strain of 0.088 over half its length, bolt 2 0.062 (the law's last point is at 0.056).
- On the flat end a falling force cannot show unloading, so `RESULTS.md`'s check ("no yielded bolt's force fell") is blind there. The reviewer solved this path again with the bolt extensions recorded. The record was reproduced exactly, and every yielded bolt's extension rises at every level (the smallest step is 0.0082 mm), so no bolt unloads.
- The no-slip ratio for B-19 at 0.01 rad (1.37) is read in this range. The rule's outcome does not depend on it, because no-slip already fails at 0.005 rad, where every bolt lies within the coupon data.

## The gate's elastic bolts and C3

- In the gate's frictionless model of B-13 at 125 kN, bolt 1 passes the yield force A_s f_yb = 174.7 kN at about 98.2 kNm, and reads 176.2 kN at 100 kNm (177.9 kN on E1's medium mesh, from about 96.1 kNm). The plan's "elastic bolts are enough up to about 100 kNm" is therefore marginal for C3.
- With E3's elastic-plastic bolts, the frictionless C3 at 125 kN is about 48.0 kN, against the gate's 49.59 kN. This is read from the E3 path's bolt force at 100 kNm (174.65 kN, linear between its levels on either side of the yield) less the gate's at 25 kNm (126.62 kN). C3's miss would be larger, about 4.1 kN instead of 2.50 kN.
- At 111.46 kN and 100 kN bolt 1 stays below the yield force up to 100 kNm (170.0 and 164.9 kN), so E2's C3 values do not depend on the bolt law. Read linearly between 111.46 kN and the elastic-plastic 48.0 kN at 125 kN, P* would be about 118.5 kN instead of 120.0 kN.
- G-F1's verdict is unaffected: it is FAIL either way.

## E1, more fully

- The medium mesh closes 1.38 kN of the 2.50 kN between the coarse C3 and the bracket's edge (55%). The plan's 1.5 kN threshold is itself 60% of that gap.
- With J2 the mesh changes C3 by 2.8%, more than the elastic mesh flag's 1.8% and more than the gate's 2% flag limit.
- Two meshes give no estimate of the converged value. "Not the main cause" is the plan's literal reading; the mesh is a sizeable part of the miss, but alone it does not close it.

## E2 (i), more fully

- C3 differs for both bounds: the uniform 111.46 kN gives 1.18 kN less than the measured set with frictionless contact and 1.02 kN less with no-slip, both just beyond the 1 kN of the rule.
- C1 lies within the rule for both bounds: 0.09 and 0.26 kNm.
- The difference comes from bolts 1 and 2, which the measured set puts below the mean (108.98 and 104.43 kN).

## Smaller points

- **Bolt table.** `RESULTS.md`'s bolt table prints a row wherever the test or either path reaches the moment, while the plan (E3, "Reported") asks for the moments that the path and the test's series both reach. So it gives model values at 150 and 175 kNm for B-13, where the test's series ends at 142.4 kNm.
- **Bolt readings in E3.** E3's steps of 0.001 rad coarsen its bolt readings. For example, bolt 1 at 25 kNm reads 126.85 kN on the E3 path against the gate's 126.62 kN, and no-slip at 100 kNm reads 160.8 kN against the gate's 161.3 kN.
- **First yield.** The "first level with a bolt above 174.7 kN" is a level, not the moment at which the bolt yields; for B-13 frictionless the level is at 111.4 kNm, and the bolt yields at about 98 kNm.
- **Gauge limit.** The test's bolt 1 of B-13 at 125 kNm (180.5 kN) is at the 180 kN to which the gauges were used, although the digitised series runs to 191.5 kN.
- **`run.log` labels.** The E2 lines of `run.log` carry `"preload": "nominal"`, because the driver relabels the record after the path's log lines are written. The records are labelled correctly (`uniform-mean`, `uniform-100`).
- **Edge.** The readings use the unrounded edge 52.0941 kN (the plan writes 52.09); P* is 120.04 kN with it and 120.05 kN with 52.09, 120.0 kN either way.
