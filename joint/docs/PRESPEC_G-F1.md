# Pre-specification of gate G-F1

Stamped 7 November 2026, 17:18 GMT. At that time no result of a model of B-13 or T-13 had been read or compared with the tests.

**This stamp replaces the first one** (7 November 2026, 03:08 GMT, commit `e966200`), which was pushed but never tagged or run. A review before tagging found two places where the code did not do what that stamp's text said or implied. Neither changes a computed value:
- a level whose solve raised a numerical error, instead of failing to converge, stopped the whole run, and the case's record was lost with it, so even values read from the converged levels before it would have been missing, against the validity rule below;
- `python -m f1 verdict` computed a FAIL from an incomplete set of records instead of refusing.

Of the gate's code only `f1/run.py` and `f1/__main__.py` changed (with their tests in `tests/test_f1.py`); the configuration and its hash did not. The code now:
- records a level whose solve raises a numerical error as not converged, with the error, and ends the path;
- records a case whose preload raises a numerical error with the error and no levels;
- counts the preload state as converged only if every bolt carries its target;
- writes each record to a temporary file and renames it into place, with the configuration's SHA-256 in it;
- refuses to compute the verdict until every case has its record.

## Question

Does friction at the splice explain the response of preloaded bolted CHS blank flange-plate joints before and just after the preload is overcome? The question is put to the reference model of stage C (`fejoint/chs.py`), used as two bounds:
- **frictionless**: the plate slides freely on the splice plane (the reference model of the earlier gates);
- **no-slip**: no point of the plate's splice face moves in the plane, while contact stays unilateral. This is infinite friction everywhere, stiffer than any real friction.

The tests are B-13 (bending) and T-13 (axial tension) of Fidalgo (2023), both with 12.6 mm plates. The gate asks whether each measured quantity lies between the two bounds. No result of a model of B-13 or T-13 had been read when this was stamped; the next section lists what had been seen.

This is a finite element question. Its answer decides how the reference energy of the tubular case is chosen for the surrogate that follows.

## What was seen before the stamp

- **B-19 and T-19** (19.3 mm plates) were solved during development, on 6 and 7 November 2026, and compared with their tests and with the author's finite element model.
  - Frictionless, elastic: at $\Theta_D$ = 0.001 rad the moment was 79 kNm, against 135 to 140 kNm measured, 138 kNm in the author's model and 147 kNm with no-slip.
  - Axial, T-19 geometry, at 400 kN: displacement 0.37 mm frictionless, 0.17 mm no-slip, about 0.17 mm measured.
  - At $\Theta_D$ = 0.0005 rad the B-19 test lay above both bounds: 107 to 116 kNm measured, 83 kNm no-slip.
  - Without preload the frictionless model agreed with the author's model without preload to within 10% (bending) and 20% (axial).
  - Bolt 1 of B-19: no-slip within 3% of the test up to 100 kNm; frictionless 15% high at 100 kNm.
- **The digitised test data of B-13 and T-13** were read; the test readings below come from them.
- **B-13 was solved twice before the stamp, and neither result was read or compared with anything.**
  - A test of the contact solver (`tests/test_chs.py`, solver equivalence) used B-13's geometry on the tiny mesh, at 100 kN preload and 0.001 rad, until 7 November 2026; it now uses B-19. The test only asserts that two solvers agree.
  - On 7 November 2026 a development batch started a B-13 path (frictionless, elastic, coarse mesh) by mistake; it was stopped within about two minutes and its log deleted unread.
- **The other tests** (`tests/test_f1.py`, `tests/test_chs.py`) solve only B-19 and T-19, on tiny meshes.
- **A dry run of this code on B-19 and T-19** (`python -m f1 run --dry`: the 14 cases of the gate's design, at the dry configuration's comparison points) was made on 7 November 2026 to check convergence and run time. Every level of every case converged within the KKT limits. The 14 cases took 1 h 42 min on two cores, while the test suite ran alongside. The records and the verdict tables of the dry run are in `records/f1_dry/`.
  - With J2 deformation theory, B-19's moment at $\Theta_D$ = 0.001 rad was 78.6 kNm frictionless and 147.0 kNm no-slip (test 137.7 ± 7.0 kNm). Bolt 1's increase from 25 to 100 kNm was 34.4 kN and 17.6 kN (test 19.5 ± 1.5 kN). T-19's mean displacement at 1300 kN was 1.818 mm and 0.745 mm (test 1.143 ± 0.053 mm). Each test value lay between the two bounds.
  - Reading the same paths with every other level (twice the step) changed these values by at most 0.23 kNm, 0.39 kN and 0.008 mm. The error of the linear reading between levels falls with the square of the step, so at the configured steps it is about a quarter of that, well inside the tolerances.
  - The first plastic points appeared at these levels: B-19's plate at $\Theta_D$ = 0.0012 rad (frictionless), its weld at 0.0010 rad (no-slip), T-19's plate at 658 kN (frictionless). The elastic bounds differed from the values above by at most 0.01 kNm in C1 and 0.24 kN in C3; in C2 the frictionless bound was 1.631 mm elastic instead of 1.818 mm.
  - With B-19's measured preloads the bounds were 78.1 and 146.0 kNm (C1) and 35.9 and 18.7 kN (C3). At $\Theta_D$ = 0.0005 rad the test (111.1 ± 16.1 kNm) again lay above both bounds (44.2 and 83.3 kNm).
  - The mesh flag was raised for C3: on the medium mesh the increase of bolt 1 was 3.5% (frictionless) and 3.6% (no-slip) larger. Moments and displacements differed by at most 0.6%.
  - The code was changed in four places after the dry run started, none of which changes a computed value: `f1/run.py` flushes its progress log after each line; the help of `python -m f1` shows the module's description; an unused helper was removed from `f1/readings.py`; the text on the hardening points in `f1/config.py` and `f1/materials.py` says at most 14 points, not 15 (the code is the same, but the text is part of the configuration, so its hash changed). The dry verdict was computed afterwards with the first stamp's code, and again with the code stamped here; the files were the same. One case was solved again with each (J2 deformation theory, frictionless): B-19 with the first stamp's code, T-19 with the code stamped here. Every number of both records but the timings was the same as in the dry run; the second record also has the fields added since.
- **Checks before tagging the first stamp**, on 7 November 2026 (every solve on B-19 or T-19):
  - B-19 frictionless with J2 deformation theory was taken to 178 kNm, and T-19 frictionless to 1,763 kN, beyond the dry run's 116 kNm and 1,350 kN. Every level converged within the KKT limits, with at most 6 Newton iterations and up to 1,216 and 12,332 plastic Gauss points.
  - B-19 on the medium mesh (the preload and one level; every medium case of the gate has the same size) needed at most 2.6 GB of memory.
  - With B-19's measured preloads the moment at zero load, which the readings take as zero, was 0.003 kNm. With the nominal preload it is zero to round-off, because the mesh is symmetric about the neutral plane.
  - The models of B-13 and T-13 were built, not solved, to check their meshes, sizes and preload targets.
  - In an independent check, one B-19 case was solved again with the first stamp's code; every number of its record but the timings was the same as in the dry run.
- **Expectation, stated before the run.** From B-19: C1 likely holds; C3 likely holds, nearer the no-slip end; C2 is uncertain, because the 12.6 mm plate bends soon after the preload is overcome at about 600 kN. The point at 0.0005 rad (reported only) may again lie above both bounds, and C3's mesh flag may be raised again.

## Authority for the criteria

- Proposed to the project owner on 7 November 2026, in the note "Fidalgo model, first results and decisions" (in Chinese, Section 6). The owner replied at 00:55 GMT to follow every recommendation and continue.
- Three refinements were made after that reply and before this stamp:
  1. The criteria use J2 deformation theory for the plate, tube and weld; the elastic results are reported. The 12.6 mm plate may yield locally by the comparison points, and an elastic bound could then confuse yielding with friction.
  2. The reading tolerances are defined from the digitised data (below), instead of the proposed flat 2 kNm and 0.05 mm.
  3. In C3 the bolt force at the lower moment is the mean of the two dotted series. Bolts 1 and 2 cannot be told apart there.
- The owner may still change anything. A change after this stamp is reported as a change after results.

## Configuration

**The configuration** is `f1/config.py` (the `config()` dictionary, without `--dry`).
- Its canonical JSON (sorted keys, no whitespace) has SHA-256 `c2fdf0fff32fd24f3714f8231b3d6e87a83bbf7d268ef2a1283f02c78c051d87`.
- `python -m f1 run` and `python -m f1 verdict` refuse to start unless they are given this hash and every file listed in `docs/G-F1_code.sha256` has its listed hash.

**Code and data at stamping** (paths relative to `joint/`): `docs/G-F1_code.sha256` lists every file for `sha256sum -c`. A copy of the code is kept in `docs/G-F1_stamped_code`.

**The gate's code**, run by `python -m f1`:

| File | SHA-256 |
|---|---|
| `f1/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `f1/__main__.py` | `762000db398d6fe74a252ec1c2639e4a68c6abd7fa5855be094f571750c23363` |
| `f1/config.py` | `12720d13c7cff292d36acab17ad30f3d0226bad3e160ef8eeb48b359df6b72e7` |
| `f1/materials.py` | `5ee5ef9af510bfe1acfb561078dc1a2976be37a3514fcb7735d230b3954d94bd` |
| `f1/readings.py` | `733f3b874de09085f191139657a17998206bc167113f56678af2967dcf67f8e3` |
| `f1/run.py` | `b1e9875a8c5aa327f47730583364003e58a016bfaef645b02da998210a4edf73` |
| `f1/verdict.py` | `d31380235b8454f4040f6bc5cc50931edab667360231a869352f9b9b35c6c697` |
| `fejoint/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `fejoint/chs.py` | `335fb6adee3df4a4d99fdde9b88cf4134dadb2a74378273393159c5df76d9b88` |
| `fejoint/hex8i.py` | `27e4964ef755c1055fd9159e860db2f7542952fac9e1237053ef3cdd1babc0f7` |
| `fejoint/nlhex.py` | `2f67dfd9603d3bfb400066d4bedbe514223d80468fc3e0b98ba4f7c7951cb522` |
| `fejoint/nlsolve.py` | `c1181535a45d9ad0928213ada75c436d2957293c36ae2ae559aee3c82310f788` |
| `fejoint/contact.py` | `75885802990155b4634a8be58035658ead51510f0758ad1ce2d2778b5750db8a` |
| `fejoint/linsolve.py` | `a829f4f5d6becd7c1081db542f3ade923dc95ed7725527a2ad9f948a6eb6739a` |
| `fejoint/plasticity.py` | `8bfb3d00b558e366d63d4a940146fb34975e81ba7d00d37d3fe8ed30d629d94c` |

**The scripts that made the data** from the thesis PDF (not run by the gate):

| File | SHA-256 |
|---|---|
| `f1/digitise/digi.py` | `b38ff8c6f8816b1e771797077249488e6c729cfb2397a12ae6055097c31f15df` |
| `f1/digitise/boltforce.py` | `5385fdc17647883cb6b1179dd374ea629c052d1c30870964723d86e7842562f4` |
| `f1/digitise/axial.py` | `9e7917592e0d40c20c76b8694dfc900514245caa1a8980539afac4830e409bf4` |
| `f1/digitise/make_fidalgo_data.py` | `915006b411cbf6781f0ed64ea3689b25b563c22a8bd67f91b3be36d8faae2b1a` |

**The data** (`f1/data`; the configuration also pins those it reads):

| File | SHA-256 |
|---|---|
| `f1/data/B13_FE3_fig37.csv` | `65f2c2ad47557d20d7fc917fafa0c53ece1910b8c5e6795eb72da08ef7c9f481` |
| `f1/data/B13_test_fig33.csv` | `4ba7c42918a8e0a17f546523bf8d432b716b5ae97499b7ec3d15585ab415e998` |
| `f1/data/B13_test_fig37.csv` | `660611e31196e2f56b8a2fd779296c4a2a3f944cfee15772adbd2580fc29d76b` |
| `f1/data/B19_FE3_fig37.csv` | `1b15693e02903a66dce0708b09b0bd9446f5c9d9e25e8d7bf871a2eb33084c9a` |
| `f1/data/B19_test_fig33.csv` | `55f487cf9c3a1f35135fa62198d13673157b0db625a0caa2478a722d41f94228` |
| `f1/data/B19_test_fig37.csv` | `1d3529d125497141315ec59b7fd3728ccfabc08ebd70f3ec3d1e69e2ec265058` |
| `f1/data/T13_test_fig222.csv` | `7cc0c4913ceedce76dddb2bd07788b0f9fc7bfa35b6d67225baae221c386aa8a` |
| `f1/data/T13_test_fig25.csv` | `5b6505fac594fc3e3377ef6ad6cf281bbdb3388dde4d440166ce98ed74799a46` |
| `f1/data/T19_test_fig222.csv` | `c58d33e94cb2af1c0d3bdb6bfb1e19ef3404e8294738dff5929848403b73159e` |
| `f1/data/T19_test_fig25.csv` | `e1d9b6abebee6ef2a4dd5e9bb1164ba9249c934309e64d4f724cca37e0354e95` |
| `f1/data/boltforce_B13.csv` | `3704d0226caa81876f54869a586dd4034b5c68b45398e4c62c66f218d510270c` |
| `f1/data/boltforce_B19.csv` | `342530027cca69994d282fc5dcf1284bc0a4b041a89eebce78e88e4c5a7de2a7` |
| `f1/data/material_bolt_eng.csv` | `5b7f1267936b9c731b44cdaf7a22d7a47270a15980e01b51b652d1ee4ae0128b` |
| `f1/data/material_chs_eng.csv` | `bd2e5912c9532f4fb754d5d7f9c68d7f3b5f55a9ca51eb3f4481deecb9acb024` |
| `f1/data/material_plate13_eng.csv` | `436579d9316dcb4b73fd42fadf0ed9ed080d98e0a4b6e116c7245970d767965e` |
| `f1/data/material_plate19_eng.csv` | `23aed4b0f41f75765a59aa2eba80f20ab5dd4d9c5f161e4fc47da5c30ccf82d7` |

## Model, fixed in advance

All inputs come from the thesis unless marked otherwise; the data sheet of 6 November 2026 gives the page of each.

**Geometry** (`f1/config.py`, `fejoint/chs.py`)
- B-13: plate 12.6 mm, $e_1$ 64.4 mm, $e_2$ 65.5 mm (Table 3.1). T-13: plate 12.6 mm, $e_1$ 63.9 mm, $e_2$ 65.2 mm (Table 2.1).
- Blank plate (no central hole). Tube 323.9 mm outside diameter, wall 12.4 mm (Table 2.2), modelled to 600 mm beyond the plate.
- 12 bolts on the circle of radius $d/2 + e_1$, the first at 15 degrees from the tension extreme fibre; holes 21 mm, stair-stepped on the mesh.
- Weld: the inner 3.4 mm of the wall is not fused (a crack with frictionless unilateral contact); the outer part is fused; an 8 mm fillet outside, its volume exact (drawings A.2 and A.8).

**Materials** (`f1/materials.py`)
- Young's moduli of Table 2.2: plate 201,000 MPa (12.7 mm plate), tube 191,700 MPa, bolts 217,100 MPa. Poisson's ratio 0.3 (assumed).
- J2 deformation theory with isotropic hardening from the digitised coupon curves (Fig. 2.18): the 12.7 mm plate's curve for the plate, the tube's for the tube and for the weld (assumed). Each curve starts at $f_y$ of Table 2.2 and is non-decreasing.

**Bolts**
- Elastic. Area 213.8 mm², that is $\pi/4\,(d_b\sqrt{0.75})^2$ with $d_b$ = 19.05 mm (thesis Section 2.7.2).
- Length $L_b$ = head/2 + grip + washer + nut/2 (thesis eq. 2.24) = 11.9/2 + 2 $t_p$ + 3.8 + 18.65/2 mm. Head and nut are the standard heavy hex sizes; the washer is the middle of the F436 range 3.1 to 4.5 mm (not given in the thesis).
- Each half bolt is an axial spring of stiffness $E_b A_s/(L_b/2)$ between a rigid head plane and the splice plane. The head plane is in frictionless unilateral contact with the plate's outer face within 17.3 mm of the bolt axis (the mean of the head's 15.9 mm and the washer's 18.65 mm; not given in the thesis). It tilts against springs $E_b I_s/(L_b/2)$.
- Preload: 125 kN in every bolt at zero load (thesis p. 48, CSA S16:19), set by a pre-shortening per bolt.

**Splice and symmetry**
- Half the joint about the bending plane (bolts 1 to 6). One side of the splice: the plane between the plates is a rigid support with unilateral contact.
- Frictionless or no-slip (the two bounds). The free sliding along the bending plane is removed by fixing $u_y$ at the plate's centre. In the frictionless model it carries no force; in the no-slip model the centre is one of the fixed points.

**Loading**
- Bending: the tube's end section stays plane. Its rotation $\theta$ about the axis normal to the bending plane is prescribed, and its axial translation is free (no axial force). Steps of 0.0005 rad.
  - The path stops after the first level with $\Theta_D \ge$ 0.0012 rad and $M \ge$ 105 kNm, or at 0.03 rad.
- Axial: the end section stays plane and parallel. Its axial displacement $w_0$ is prescribed, in steps of 0.1 mm.
  - The path stops after the first level with $T \ge$ 850 kN, or at 5 mm.
- Each level starts from the previous one. The solution of each level does not depend on the path, because deformation theory is used and the contact is frictionless or fixed.

**Readings**, each relative to the preload state:
- $\Theta_D = u_z(D)/d$: D is the tube's outer face at the tension extreme fibre, 100 mm from the plate's outer face. This follows the author's finite element model (thesis p. 50); the rings of the tests were 100 mm from the connection.
- $M$: twice the reaction to $\theta$ (half model).
- $T$: twice the reaction to $w_0$.
- Axial displacement: $u_z(D) + u_z(C)$, C opposite D on the same ring. This is the mean of the two LVDTs.
- The bolt forces of bolts 1 to 6.

**Mesh and solver**
- The `coarse` mesh of `fejoint/chs.py`: 1.875 degree steps next to the bolts and 3.75 degrees elsewhere; 2 layers in the plate; 5,352 or 5,496 cells (by specimen) and about 25,000 to 26,000 unknowns.
- In the dry run (B-19 and T-19, elastic, both bounds) coarse and medium differed by at most 0.6% in moment and displacement and by 3.6% in the increase of bolt 1.
- Contact problems are solved by the iteration of `fejoint.nlsolve` (sequential quadratic programming with a primal-dual active set), in `fejoint.chs.WarmContactProblem`, which starts the active set from the previous level; the result does not depend on it.
- Tolerance 1e-10, at most 60 iterations, the KKT limits of `f1/config.py`.

## Test readings (`f1/readings.py`, computed before the stamp)

| Reading | Specimen | Value | Tolerance | From |
|---|---|---|---|---|
| C1: moment at $\Theta_D$ = 0.001 rad | B-13 | 75.00 kNm | 4.81 kNm | Fig. 3.3: 73.00; Fig. 3.7(a): 76.99 |
| C3: increase of bolt 1 from 25 to 100 kNm | B-13 | 55.57 kN | 3.48 kN | 162.28 at 100 kNm; 108.98 and 104.43 (bolts 1 and 2) at 25 kNm |
| C2: mean LVDT displacement at 800 kN | T-13 | 0.934 mm | 0.051 mm | Fig. 2.5: 0.935; Fig. 2.22(a): 0.933 |
| Reported: moment at $\Theta_D$ = 0.0005 rad | B-13 | 59.50 kNm | 7.36 kNm | 57.40 and 61.59 |

**Tolerances**:
- Moments: half the difference between the two figures, plus half the change of the mean curve over one pixel of rotation (8.0e-5 rad) either side, plus one pixel of moment (0.7 kNm).
- Bolt force: half the difference of the two dotted series at 25 kNm, plus two pixels (0.6 kN each).
- Displacement: half the difference between the two figures, plus 0.05 mm (about one pixel).

## Criteria

Each criterion compares the test value with the two bounds' values (J2 deformation theory, coarse mesh, nominal preload). A model value is read off its path by linear interpolation between the two levels around the comparison point; the preload state counts as the level before the first. A criterion holds when the test value lies within [min - tol, max + tol] of the two bounds' values.

**C1** (B-13). The measured moment at $\Theta_D$ = 0.001 rad lies between the frictionless and no-slip moments.

**C2** (T-13). The measured mean displacement at 800 kN lies between the frictionless and no-slip displacements.

**C3** (B-13). The measured increase of bolt 1's force from 25 to 100 kNm lies between the frictionless and no-slip increases.

**Validity.** A criterion does not hold if either bound's value is missing, or if any level up to and including the one used did not converge or broke a KKT limit. The path does not reach the point in the first case. A level whose solve raises a numerical error counts as not converged: it is recorded with the error, and the path stops. A numerical error is a `RuntimeError` other than `NotImplementedError` and `RecursionError`, an `ArithmeticError` or numpy's `LinAlgError`; any other error stops the run. The preload state counts as converged only if its solve converged and every bolt carries its target to a relative 1e-6; a case whose preload raises a numerical error has no levels.

**Verdict.** G-F1 passes if and only if C1, C2 and C3 all hold.

**Mesh flag.** Each gated quantity is recomputed with elastic models on the coarse and the medium mesh. The medium mesh is solved only at the levels around the comparison points. A quantity is flagged if the two meshes differ by more than 2%. The flag is reported, not part of the verdict.

## Reported, not part of the verdict

- The same three comparisons with elastic models.
- B-13 with the measured preload: bolts 1 to 6 at their Fig. 3.4(a) forces at 25 kNm, 109.0, 104.4, 126.2, 102.3, 115.8 and 111.0 kN, for C1 and C3. B-13's bolts relaxed under self-weight before the test (thesis p. 48).
- The moment at $\Theta_D$ = 0.0005 rad against the reading above, both theories.
- Every path: moments, rotations, displacements, bolt forces, KKT residuals, plastic Gauss points.

## If the gate fails

The candidate causes, written before the run:
- the plates' initial out-of-flatness after welding (the drawings allow ±2 mm), which can pre-compress the region under the tube;
- B-13's uneven preload (the measured-preload case above);
- what the model leaves out: friction under the heads and nuts, and the shanks bearing on the hole walls;
- the definition of the rotation (the LVDT offset $L$ is not given);
- the digitising of the figures;
- the material model (hardening from the coupons; the weld given the tube's curve);
- the coarse mesh (see the mesh flag).

No part of the model is changed after the run. Whatever is found is reported.

## How it is run

From `joint/`, on a CPU (no GPU is needed; the dry run took 1 h 42 min on two cores):
```
python -m f1 run --sha c2fdf0fff32fd24f3714f8231b3d6e87a83bbf7d268ef2a1283f02c78c051d87 --out records/G-F1
python -m f1 verdict --sha c2fdf0fff32fd24f3714f8231b3d6e87a83bbf7d268ef2a1283f02c78c051d87 --out records/G-F1
```
Each case's record is written when the case ends. `run` keeps the records it finds, so a run that was cut off is continued by giving the same command again. `verdict` refuses until every case has its record.

A dry run of the same code on B-19 and T-19, which are not part of the gate: `python -m f1 run --dry --out <dir>`, then `python -m f1 verdict --dry --out <dir>`. The one made before the stamp is in `records/f1_dry/`.

## References

- Fidalgo, A.M. (2023). *Bolted CHS flange-plate connections under tension, bending and combined loads.* PhD thesis, University of Toronto. https://tspace.library.utoronto.ca/bitstream/1807/129860/1/Fidalgo_Augusto_Madrigali_202311_PhD_thesis.pdf
- Fidalgo, A., Packer, J.A. (2023). Bolted CHS flange-plate connections under bending. *Journal of Structural Engineering* 149(6), 04023066. doi:10.1061/JSENDH.STENG-12059
- Fidalgo, A., Packer, J.A. (2022). Evaluation of bolted CHS flange-plate connections under axial tension. *Journal of Constructional Steel Research* 196, 107399. doi:10.1016/j.jcsr.2022.107399
- ASME B18.2.6, heavy hex structural bolts and nuts; ASTM F436, hardened steel washers (sizes as listed by suppliers).
