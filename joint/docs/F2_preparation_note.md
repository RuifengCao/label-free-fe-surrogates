# CHS surrogate gate: preparation before the pre-specification

8 November 2026. Work done after gate G-F1 and its exploratory runs (`probes/f1_explore`), before any pre-specification of the surrogate gate on the CHS flange-plate splices, provisionally G-F2. Nothing here is a gate, nothing was pre-specified, and no member was drawn with a seed of the gate. The code is in `f2/` (family, export, reference, data, training energy) with its tests in `tests/test_f2.py`; the development paths are in `probes/f2_dev/`.

## 1. The family

**Varied**, uniformly and independently (`f2/family.py`):

| Parameter | Range | B-13 | B-19 |
|---|---|---|---|
| plate thickness $t_p$ | 10 to 25 mm | 12.6 | 19.3 |
| tube face to bolt axis $e_1$ | 55 to 75 mm | 64.4 | 64.2 |
| bolt axis to plate edge $e_2$ | 55 to 75 mm | 65.5 | 64.5 |
| plate yield stress $f_y$ | 345 to 460 MPa | 397 | 373 |
| bolt preload $N_p$, every bolt | 60 to 130 kN | 125 or 111.46 | 125 or 120.89 |

**Fixed**, as Fidalgo's specimens and gate G-F1's model (`fejoint/chs.py` defaults): the 323.9 x 12.4 mm tube with 600 mm beyond the plate, its coupon law, which the weld shares; twelve 3/4 inch bolts, the first at 15 degrees from the tension extreme fibre; holes of 21 mm; the bearing radius of 17.3 mm; the unfused root of 3.4 mm and the fillet leg of 8 mm; the measuring ring 100 mm from the plate's outer face; the coarse mesh.

**Plate law.** Gate G-F1's law of the 12.7 mm plate (`f1/materials.py`), with every stress scaled by $f_y/397$ MPa and the plastic strains unchanged; Young's modulus 201,000 MPa. The member with B-13's geometry, $f_y$ = 397 MPa and $N_p$ = 125 kN is therefore gate G-F1's B-13 with the elastic-plastic bolts of run E3.

**Bolt law.** Run E3's, from the coupon curve by `f1/materials.py`'s rule, unchanged up to its last point (201.0 kN); beyond it a slope of $10^{-4} E_b A_s/(L_b/2)$ instead of zero, so that the energy stays strongly convex in every bolt.

**Preload.** One pre-shortening for all twelve bolts, set by a fixed point so that the mean force of the six bolts of the half model at zero rotation is $N_p$; two solves sufficed in every development member, whose preload states were all elastic. The six forces then differ by the mesh's round-off, at most $1.2 \times 10^{-7}$ relative over the 13 members.

**The tested members** are B-13 and B-19 with their measured geometry and yield stress (Tables 3.1 and 2.2 of the thesis), each at the nominal 125 kN and at the mean of its six bolt forces read at 25 kNm (`f1.readings.measured_preload`): 111.46 kN for B-13 (as run E2 used) and 120.89 kN for B-19.

## 2. The export and the reference

`f2/instance.py` follows `c2/instance.py`.
- **Loading through a rotational spring.** The tube's end section stays plane, $u_z = w_0 - \theta y$, with $w_0$ free. A linear spring of stiffness $k_\theta$ per half model joins the end rotation $\theta$ to a loading device whose rotation $\Theta$ is prescribed. The moment on the joint is $M = 2 k_\theta (\Theta - \theta)$.
- **The moment bound.** For any admissible field $z$, $\lvert M(z) - M^*\rvert \le 2\sqrt{2 k_\theta (\Pi(z) - \Pi^*)}$, with $M^*$ and $\Pi^*$ those of the exact solution at the same $\Theta$.
- **Rotation control.** Under deformation theory the state at a given end rotation does not depend on the device, so the reference curve $M^*(\theta)$ is that of rotation control (`ExportedProblem.solve_at_theta`). `ExportedProblem.solve_at_ThetaD` finds the state at a prescribed $\Theta_D$ by the secant method on rotation control.
- **Readings.** The moment from the spring; the moment from the stresses, $M_\sigma = 2\,\nabla W(z) \cdot v$, with $v$ a virtual rotation of the tube's sections rising linearly from the tube's coarse interface to the end section; the tests' rotation $\Theta_D = u_z(D)/d$ relative to the preload state, as gate G-F1 reads it; $\theta$; the six bolt forces.
- **Files** (`f2/data.py`). The instance file holds the problem only (mesh, laws, the map from the unknowns to the displacements, springs, the pre-shortening, the loading spring, the device range); the preload state lives in a separate file that only the reference code reads, so the training code is never shown a solved field. The pre-shortening itself comes from the preload solve: it is the boundary condition that realises the preload $N_p$.
- **Training energy** (`f2/torch_energy.py`): gate G-C2.1's closed-form Hencky law and element sets, imported unchanged, with three element sets (plate, tube, weld), a pre-shortening per bolt and the loading spring.

## 3. Checks

**Tests** (`tests/test_f2.py`, tiny mesh, 13 tests, all pass):
- the family is deterministic and valid at its corners and for the tested members;
- the plate law at 397 MPa is gate G-F1's, and scales by $f_y/397$ elsewhere; the bolt law is continuous and regularised;
- the preload is uniform and on target, and the preload state is the reading's origin;
- the spring-loaded export equals rotation control at the end rotation it reaches, within $10^{-8}$ in moment and field; the spring, the reaction and the stresses give the same moment;
- the export equals `fejoint.chs.SpliceModel` with the same laws, bolts and preload;
- the moment bound holds for fields near and far from the solution;
- the no-slip variant is stiffer;
- the torch energy and its gradient equal the reference in float64 (energy within $10^{-12}$), and the float32 energy within $10^{-5}$;
- generation, labels and their checks; files of another configuration and a changed label are refused;
- the search at a prescribed $\Theta_D$ returns the state of rotation control;
- the device range of the loading rule rises with the plate's thickness and yield stress and falls with $e_1$, and the moment estimate stays below its cap.

**B-13 against run E3** (coarse mesh, frictionless): the family's B-13 solved through the export, at the end rotations 0.002 to 0.014 rad that E3 also solved, gives E3's moments within $2.4 \times 10^{-10}$, $\Theta_D$ within $1.4 \times 10^{-10}$ and the bolt forces within $3.7 \times 10^{-8}$ (E3 set each bolt's preload to a relative $10^{-6}$).

**B-19 against run E3.** The family's B-19 differs from G-F1's in the plate law (the 12.7 mm plate's scaled, not the 19 mm plate's coupon) and in the plate's Young's modulus (201,000 against 204,500 MPa). At the same end rotations its moments are 0.17% to 0.42% lower, $\Theta_D$ 0.09% to 0.55% higher and the bolt forces within 0.26%.

**Mesh** (run E1's records, B-13, frictionless, elastic bolts): the medium mesh's moments are within 0.4% of the coarse mesh's at the same end rotation up to 0.006 rad, and $\Theta_D$ within 0.2%; bolt 1's force is up to 1.5% higher.

## 4. Development paths

Thirteen members were chosen by hand, none drawn with a seed (`probes/f2_dev/dev_paths.py`):
- B-13 and B-19 at 125 kN;
- the corners W1, W2 (10 mm, 345 MPa) and S1, S2 (25 mm, 460 MPa), with $(e_1, e_2, N_p)$ at (75 mm, 55 mm, 60 kN) and (55 mm, 75 mm, 130 kN);
- T10hi (10 mm, 460 MPa), T25lo (25 mm, 345 MPa) and the centre C (17.5 mm, 402.5 MPa), all three at $e_1 = e_2$ = 65 mm and 95 kN;
- X1 to X4, a half fraction in $(e_1, e_2, N_p)$ at the centre's thickness and yield stress, to separate the effects that the corners confound.

Each was solved frictionless on the coarse mesh, under rotation control from the preload state in steps of 0.002 rad of end rotation, until $\Theta_D$ reached 0.013 rad. B-13 and B-19 were solved with SuperLU, the others with PARDISO; the two give the same solution to round-off (a tiny-mesh solve differed by $5 \times 10^{-15}$).

**Every one of the 131 levels converged within gate G-F1's optimality limits**, and the preload state was elastic in every member, with the largest von Mises stress in the plate between 80 and 262 MPa.

At $\Theta_D$ = 0.011 rad (records in `probes/f2_dev/records`, readings by `probes/f2_dev/analyse.py`):

| Member | $t_p$ | $e_1$ | $e_2$ | $f_y$ | $N_p$ | $M$ (kNm) | $\theta$ (rad) | bolt 1 (kN) |
|---|---|---|---|---|---|---|---|---|
| W1 | 10 | 75 | 55 | 345 | 60 | 82.7 | 0.0131 | 139.6 |
| W2 | 10 | 55 | 75 | 345 | 130 | 118.8 | 0.0139 | 174.5 |
| T10hi | 10 | 65 | 65 | 460 | 95 | 121.6 | 0.0140 | 175.5 |
| B-13 | 12.6 | 64.4 | 65.5 | 397 | 125 | 162.4 | 0.0148 | 177.1 |
| X2 | 17.5 | 75 | 55 | 402.5 | 60 | 229.6 | 0.0162 | 193.6 |
| X4 | 17.5 | 75 | 75 | 402.5 | 130 | 237.6 | 0.0164 | 190.2 |
| C | 17.5 | 65 | 65 | 402.5 | 95 | 257.0 | 0.0169 | 196.6 |
| B-19 | 19.3 | 64.2 | 64.5 | 373 | 125 | 274.8 | 0.0174 | 198.6 |
| X1 | 17.5 | 55 | 55 | 402.5 | 130 | 276.5 | 0.0175 | 199.8 |
| X3 | 17.5 | 55 | 75 | 402.5 | 60 | 283.4 | 0.0176 | 199.7 |
| T25lo | 25 | 65 | 65 | 345 | 95 | 332.7 | 0.0190 | 198.4 |
| S2 | 25 | 75 | 55 | 460 | 60 | 334.8 | 0.0189 | 196.7 |
| S1 | 25 | 55 | 75 | 460 | 130 | 365.6 | 0.0203 | 201.1 |

- **The moment at 0.011 rad spans a factor of 4.4.** The thickness matters most. Over their ranges, the rule of Section 5 gives factors of 4.39 for $t_p$ (before its cap), 1.31 for $e_1$, 1.24 for $f_y$ and 1.07 for $e_2$; W2 carries 44% more than W1. The preload hardly matters there.
- **The end rotation exceeds $\Theta_D$** by the tube's elastic rotation beyond the measuring ring: at 0.011 rad, $\theta - \Theta_D$ is $2.37 \times 10^{-11}$ rad per N mm of moment to within $6 \times 10^{-4}$ rad in every member, the rotation of about 670 mm of elastic tube. At the first level the end rotation is 1.4 (W1) to 4.1 (S1) times $\Theta_D$.
- **Bolt 1 reaches the end of the coupon law** (201.0 kN, the bolt's tensile strength) before 0.013 rad in S1 (at 0.0096 rad), X1 (0.0130 rad) and X3 (0.0128 rad); before 0.011 rad only in S1. Beyond it the law's small final slope holds the force there; the model has no bolt fracture.
- **Against the tests** (reported, not judged): the family's B-13 is 6.3% and 4.8% below the measured moments at 0.005 and 0.01 rad, the family's B-19 8.1% and 3.1% below. These are read by linear interpolation between levels 0.002 rad apart; run E3's paths, 0.001 rad apart, give 6.1%, 4.7%, 7.6% and 2.9%.

## 5. The loading

**Why each member has its own device range.** With one range for the whole family, the strongest member would set it. At S1's top, about 0.064 rad, the weakest member W1 would be far beyond the end of its path (0.014 rad), at about 0.044 rad by linear extrapolation from its last two levels: four times the rotations at which the reference was checked against the tests.

**The spring:** $k_\theta = 4 \times 10^9$ N mm/rad per half model, 8,000 kNm/rad for the whole joint. With the member's half-model secant stiffness $k_s$ and tangent stiffness $k_t$, a relative error $\varepsilon$ of the end rotation shows in the distance from the curve as about $-\varepsilon\,(k_\theta + k_t)/k_s$, as in G-C2.1. Over the 13 members this factor is 1.21 to 1.59 at the first level (G-C2.1's members: 1.08 to 1.2) and 0.63 to 1.51 at $\Theta_D$ = 0.011 rad (G-C2.1's: 1.0 to 2.6 at the largest level). A stiffer spring makes the range less sensitive to the rule's errors but raises both factors: at $8 \times 10^9$ they are 1.43 to 2.18 and 1.08 to 2.78, the largest in W1.

**The rule** (`f2.family.loading`, constants fitted by `probes/f2_dev/fit_loading.py`):

$$\Theta_{max}(q) = \Theta_t + \left(b + \frac{1}{2 k_\theta}\right) M_{est}(q), \qquad M_{est} = \left(M_p^{-4} + M_c^{-4}\right)^{-1/4},$$

$$M_p = A \left(\frac{t_p}{15}\right)^{1.615} \left(\frac{f_y}{400}\right)^{0.754} \left(\frac{e_1}{65}\right)^{-0.864} \left(\frac{e_2}{65}\right)^{0.222},$$

with $\Theta_t$ = 0.011 rad, $b = 2.374 \times 10^{-11}$ rad per N mm, $A$ = 212.6 kNm and $M_c$ = 369.0 kNm.
- $M_{est}$ is within 2.1% below and 2.3% above the 13 members' moments at 0.011 rad.
- At the top of its range each member reaches $\Theta_D$ = 0.0103 to 0.0115 rad, read from its path with the spring.
- Fitted without X3, the rule predicted X3's moment 3.0% high, and X3 would reach 0.0117 rad at its top.
- A preload exponent, fitted too, came out between $-0.02$ and $0.03$ and made the held-out prediction of X3 worse (4.5% high); it is left out.
- The device range ends between 0.0235 rad (W1) and 0.0645 rad (S1).

**Levels** are fractions of each member's range: 0.0625, 0.125, 0.25, 0.375, 0.5, 0.75 and 1 for the evaluation, 0.09375, 0.1875, 0.3125, 0.4375, 0.625 and 0.875 for the labelled training members, as G-C2.1's levels over its 8 mm.

## 6. Cost

- **Size.** 8,194 to 8,851 nodes and 24,602 to 26,573 unknowns on the coarse mesh over the 13 members, against 1,342 to 1,617 nodes and 4,030 to 4,855 unknowns for three G-C2.1 members drawn with a development seed (7): about 5.5 times.
- **Training energy.** One evaluation with its gradient (four fields, float32, ten bubble Newton steps, one CPU thread) took 4.26 s for B-13, against 0.65 s for a G-C2.1 member: 6.5 times (`probes/f2_dev/energy_cost.py`). The network's own cost is not included; attention over 5.5 times as many nodes costs up to 30 times as much.
- **Export** (two preload solves): 49 to 62 s with PARDISO on one thread here, 80 and 114 s with SuperLU.
- **A level** of the reference: 55 to 127 s on average per member with PARDISO (171 and 230 s for B-13 and B-19 with SuperLU), 7 to 11 Newton iterations, with two solves running side by side on the sandbox's two cores. A label of seven levels thus takes about 7 to 15 minutes with PARDISO.

## 7. Left to the pre-specification

- **The judged rotation.** $\Theta_D$, the tests' reading, or the end rotation as in G-C2.1. At small rotations the end rotation is 1.4 to 4.1 times $\Theta_D$, the rest the elastic tube, so a distance from the curve in the end rotation would hide part of an error in the splice. The reference at a prescribed $\Theta_D$ (`solve_at_ThetaD`) took four to five solves in a tiny-mesh check, to a relative $10^{-9}$ in $\Theta_D$ from a start read off three labelled levels, against one at a prescribed end rotation.
- **The yield stress as a parameter.** The plan of 8 November 2026 named four parameters; the fifth, $f_y$, puts B-13 and B-19 into the family with their own yield stresses.
- **The bolts at their tensile strength.** In the strongest corner of the family, bolt 1 reaches the coupon's tensile strength before 0.011 rad; the alternatives are to keep the ranges and state it, or to narrow the thickness or the yield stress.
- **The no-slip bound** as a second reference energy needs its own range rule: it is stiffer, so with this rule its members would stop short of 0.011 rad.
- **The network, the training budget and the cost probe** wait for G-C2.1's verdict.
