# Pre-specification of gate G-C2.1

Stamped 6 November 2026, 20:38 GMT. At that time no member drawn with this gate's seeds had been exported or solved, and no training of this gate had started.

## Question

Can the project's transformer, trained on the total potential energy alone and never shown a solution, predict the force-deformation response of bolted T-stubs it has not seen, in the plastic range:
- with yielding flanges, webs and bolts, bolt preload and contact;
- along a monotonic loading path from the elastic range to about 4 to 6 mm of end displacement?

The prediction is judged by its distance from the force-deformation curve of the reference finite element model.

**Hypothesis.** Trained on the energy alone, the transformer meets C1 and C2 below on the held-out members.

- **The reference** is the plastic T-stub model of stage C2 (`fejoint/tstub_pl.py`, with `fejoint/plasticity.py`, `fejoint/nlhex.py` and `fejoint/nlsolve.py`), loaded as `c2/instance.py` sets out:
  - one T-stub of a symmetric pair on the plane between the flanges, a quarter model (half the width, half the length);
  - small-strain J2 plasticity in deformation-theory (Hencky) form, the family's nominal steel law in the flange, the root and the web;
  - incompatible-mode hexahedra with their bubble parameters condensed at the element level; the 5 mm mesh with two layers through the flange;
  - frictionless unilateral contact on the plane between the flanges and under the bolt head, whose rigid bearing plane may tilt against the bolt's bending springs;
  - the half bolt as an elastic-plastic axial spring, pre-shortened for the preload.
- **Loading through a spring.** The web's end section is rigid in its axis, with one end displacement $e$. A linear spring of stiffness $k_s = 20$ kN/mm per quarter model joins it to a loading device whose displacement $D$ is prescribed. The force on the pair is $F = 4 k_s (D - e)$, read from the single unknown $e$.
  - For any admissible field $z$, $\lvert F(z) - F^*\rvert \le 4\sqrt{2 k_s (\Pi(z) - \Pi^*)}$, with $F^*$ and $\Pi^*$ those of the exact solution at the same $D$: the spring makes the energy $k_s$-strongly convex in $e$ (`c2/instance.py`; checked in the tests).
  - Under deformation theory the T-stub's state at a given end displacement does not depend on the loading device: the reference curve $F^*(e)$ is that of displacement control (tests, within $10^{-8}$).
- **What is judged: the distance from the reference curve.** A prediction gives a point $(e, F)$ on the force-deformation plane, both read from its field. Its error is $F/F^*(e) - 1$, with $F^*(e)$ the reference force at the predicted end displacement, from an exact solve with $e$ prescribed.
  - The error belongs to the predicted point and the T-stub, not to the loading device.
  - In the elastic range it is the error of the secant stiffness, as in G-C1.3. With $k_T$ the T-stub's stiffness and $\varepsilon$ the relative error of $e$, it is about $-\varepsilon\,(1 + k_s/k_T)$: never much smaller than the error of $e$.
  - On a plastic plateau, where $F^*$ is flat, it equals to first order the force error at the same $D$, $-\varepsilon\, e/(D - e)$.
- **Why the spring, and why this one.**
  - With the end displacement prescribed directly, the force is the stress resultant in the stiff web, where a force error costs little energy. In the CPU pilots under displacement control the force read from the stresses was off by 35% in the median after 1,920 steps and 12.6% after 9,600, while the energy gap fell to 8.2% (below).
  - Through the spring the force is read from $e$, and a force error costs energy in proportion to its square over $k_s$. With a stiff spring, 100 kN/mm per quarter and $D$ up to 4 mm, the median distance from the reference curve was 14.7% after 9,600 steps: on the plateau $e/(D - e)$ was 2 to 13, and the error of $e$ was magnified by that factor.
  - With $k_s = 20$ kN/mm the factor is 1.0 to 2.6 at the largest level in the seven members solved on the gate's mesh before the stamp (below). Their secant stiffness at the first level is 110 to 260 kN/mm per quarter, five to thirteen times $k_s$. In the elastic range the force at the same $D$ is then set mostly by the spring and hides the T-stub's error; the distance from the curve does not.
- **Deformation theory against flow theory.** On Bursi and Jaspart's T1, preloaded, with their measured laws, the two differ by at most 0.20% in force up to 9.7 mm of web deformation (coarse mesh; `records/c2/bj1997_T1_preloaded_coarse.json`). The threshold set on 5 November 2026 was 2%. Under monotonic loading the deformation theory stands in for the flow theory.
- **Mesh.** On the same T-stub the 2.5 mm mesh with three layers through the flange gives forces within 0.8% of the 5 mm mesh with two layers from 0.8 mm of web deformation on, and 1.8% above it at 0.4 mm (`records/c2/bj1997_T1_preloaded_fine.json`).
- **Distance of the reference to the T1 test and to the authors' model** (preloaded T1, its measured laws and geometry; the curves digitised from their Fig. 10, `probes/c2_bj1997_fig10.json`):
  - at 0.5 mm of web deformation the reference is within 1.2% of the test, on either mesh;
  - from 1 to 8 mm it lies 9% to 14% above the test;
  - against the authors' simulations it runs from 4% to 5% below at 1 mm to 8% to 9% above at 6 to 8 mm.
- **The gate does not test the reference against the experiments.** The gap above is stated and not explained. The family's members carry the family's nominal laws, not measured ones.

## Authority

**The C plan of 9 October 2026** set out stage C2: plasticity after the elastic stage C1.3.

**The owner** wrote the following (messages translated from Chinese; the originals are kept in the correspondence record):
- 5 November 2026, 21:32: if plasticity needs the GPU, the timeline is not to slip; at best Dr Song runs it on the server this week or next.
- 5 November 2026, 21:33: the timeline need not be long; the work that does not need the GPU can all be done in the next few days.
- 5 November 2026, 21:33: record this arrangement, and start when told to start.
- 6 November 2026: "Start."
- 6 November 2026, 20:24: Dr Song is to run it on the server; for the other decisions left to the owner, the owner asked for a full assessment with recommendations.
- 6 November 2026, 20:34: R2b has probably not started yet; run C2 first, as it is the more urgent.

**Defaults recorded on 5 November 2026**, used because the owner set nothing else:
- deformation theory (Hencky) first, flow theory only as the reference check, with a 2% threshold on their difference in three dimensions (met above);
- the GPU run waits until R2b, the run then due on the box, has finished. The owner reversed this on 6 November 2026 at 20:34 (above): this run goes first, and R2b starts after its return package has been sent.

**Departure from a recorded default.** The default ran the GPU pilot on the C1.3 family of end plate joints. This gate runs it on a family of T-stubs instead.
- The C1.3 export condenses the bolt heads, the rigid end section and the beam segment exactly, as linear constraints. Plastic bolts and a plastic beam end break that condensation.
- Carrying the joint model over would need a new export with nonlinear heads and segment, which could not be checked in the time set.
- The T-stub is the component the joint's tension zone is built from, and the plastic T-stub has published tests and an independent finite element model (Bursi and Jaspart 1997).

**Not set by the owner:** the thresholds, the parameter ranges, the loading, the judged quantity, the arms and the budget. This document fixes them. The owner may change them until the first training run starts; a change is recorded with this document.

**Chosen here**
- The judged quantity, the distance from the reference curve, and its thresholds: a median of at most 5%, the threshold of G-C1.3's C1, and a 90th percentile of at most 10%, so that the tail is judged too.
- The loading: the spring at $k_s = 20$ kN/mm per quarter model, and $D$ up to 8 mm, which takes the seven members solved on the gate's mesh before the stamp to 4.0 to 5.8 mm of end displacement.
- The loss: the mean of $\log \Pi$ over the step's fields. $\Pi > 0$ for $D > 0$, and its logarithm weighs a field at 0.1 mm like one at 8 mm without any solution. Its minimiser is that of $\Pi$.
- The web lifted with the end section: the network gives the web's $u_x$ as $e$ plus a correction, $e$ itself from the head network.
- One supervised arm of 64 members at six levels each. G-C1.3's supervised arms were descriptive, and each label here costs a plastic solve.
- The budget: 200 epochs for each arm, as in G-C1.3. The supervised arm thus takes an eighth of the label-free arm's steps.

**Changes.** Any change after this stamp is reported as a change after the stamp. No threshold, metric or arm changes once the first training run has started.

## What was seen before the stamp

**Earlier gates.** All the results of G-C1a, G-C1a2, G-C1b with its addendum, G-C1c, G-C1.3 (PASS) and the element study.

**The reference code** was checked on its own (`tests/test_c2.py`):
- the material law: energy, stress and tangent against finite differences, the yield condition, convexity, flow theory along proportional paths against deformation theory;
- the elastic limit: the plastic model with an elastic law, and with a yield stress that is never reached, reproduces the linear T-stub model `fejoint.tstub.analyse` within $10^{-9}$, in both theories;
- preload; the spring-loaded export against the model under displacement control at the same end displacement; the force bound;
- the training energy (`c2/torch_energy.py`) against the reference in float64: energies within $10^{-12}$, gradients within $10^{-9}$;
- the evaluation: exact predictions pass; seeds that stop, whose predictions are not finite or that are missing are treated as the criteria state.

**Bursi and Jaspart's T1, preloaded** (`probes/c2_bj1997.py`), as stated under the question. T2 and the snug-tight tests were not run.
- The probe sets the measured preload, 60.7 kN a bolt, by the pre-shortening that gives it at zero load.
- The family instead pre-shortens the half bolt by $\rho N_y / k_{ax}$, which ignores the compression of the clamped parts. The tested T1, at $\rho = 60.7/74.2$, carries 55.6 kN at $D = 0$.

**Members of the family** drawn before the stamp, all with seeds in SEEDS_SEEN (7, 8, 101 and 102):
- development checks on members of seed 7;
- the test suite, which exports, solves and trains on members of seeds 7 and 8 with a coarse mesh;
- the CPU pilots below, with seed 8 for training and 7 for held-out members;
- a review of the code, whose checks solved the preloaded T1 and members 0 to 2 of seeds 7 and 8 on the gate's mesh, at the gate's levels (member 1 of seed 8 at the training label levels). Every level converged. The figures quoted above for $e/(D - e)$, the secant stiffness and the end displacements come from these seven solves.
- In those solves, made with the solver as it then was, the relative residual of the unconstrained unknowns exceeded $10^{-8}$ in three of the seven members, at most $2.9 \times 10^{-8}$. Near the optimum the Armijo test had cut steps whose predicted decrease lay below the round-off of the energy, and convergence was declared on a cut step.
  - The solver now takes the full step when the predicted decrease is below $10^{-13}$ of the energy, and declares convergence only on a full step (`fejoint/nlsolve.py`). Solved again with it, the three members end with residuals of at most $6 \times 10^{-11}$, and their forces are unchanged to 0.1 N.
  - The label check's upper limits on those residuals and on the multipliers of separated unknowns, $10^{-8}$ in the draft, were also set at $10^{-6}$, G-C1.3's values. Every multiplier is still to be no lower than $-10^{-8}$.
- a second review of the code, after these changes, whose checks solved the preloaded T1, members 0 and 2 of seed 7 and member 1 of seed 8 again on the gate's mesh (27 levels, every one converged, residuals at most $6 \times 10^{-11}$), solved at prescribed end displacements around the labels of member 0 of seed 7 and of T1, solved T1 at $D = 0$, and trained and evaluated small models on members of seeds 7 and 8 on the coarse mesh;
- two dry runs of the runbook on a reduced configuration, in the development machine: seeds 101 and 102, four training and two held-out members, the coarse mesh, a model of width 32 and depth 1, six epochs an arm, three evaluation levels. The first ran every section, from the worktree to the return package, with the bench and the training on the CPU; the second ran the labels and the evaluation with two worker processes, and the training on the CPU. Both also solved the four tested members on the coarse mesh.

**Members built but not solved**: the 22 corners of the ranges of $t_f$, $t_w$, $r$, $w$ and $n$ that are members of the family ($f_y$ and $\rho$ do not change the mesh), to bound the size of the linear systems. The largest has about 4,600 free unknowns (5,053 in all), so the labels and the evaluation use PARDISO or scipy's direct solver.

**The CPU pilots** (`probes/c2_pilot/`), not the gate. The coarse mesh (10 mm, one layer through the flange), 32 training members, 6 held-out members and the preloaded T1, a small model (width 64, depth 2, 4 heads), one seed, the configuration's training settings otherwise, CPU.

Held-out medians (`probes/c2_pilot/README.md` gives every run):

| Loading | Error judged | Material | Steps | Median | 90th percentile | Energy gap |
|---|---|---|---|---|---|---|
| displacement control | force from the stresses | plastic | 1,920 | 34.8% to 102.8% | 80.0% to 192.8% | 34.9% to 71.3% |
| displacement control | force from the stresses | plastic | 9,600 | 12.6% | 38.5% | 8.2% |
| spring, 100 kN/mm, $D$ to 4 mm | force at the same $D$ | elastic | 1,920 | 5.6% | 31.7% | 6.8% |
| spring, 100 kN/mm, $D$ to 4 mm | force at the same $D$ | plastic | 9,600 | 11.2% | 20.1% | 4.8% |
| spring, 100 kN/mm, $D$ to 4 mm | distance from the curve | plastic | 9,600 | 14.7% | 32.4% | 4.8% |
| spring, 20 kN/mm, $D$ to 8 mm (the gate's) | distance from the curve | plastic | 1,920 | 35.0% | 170.0% | 10.1% |
| spring, 20 kN/mm, $D$ to 8 mm (the gate's) | distance from the curve | plastic | 4,800 | 26.2% | 80.6% | 4.6% |
| spring, 20 kN/mm, $D$ to 8 mm (the gate's) | distance from the curve | plastic | 9,600 | 9.6% | 37.9% | 2.6% |

- Under displacement control the force read from the stresses stayed far from the reference while the energy came close. Of the three runs at 1,920 steps, two ended there (34.8% and 35.1%); the third (`trend_coarse_a.json`, 102.8%) was read at epoch 60 of a 300-epoch schedule, without the web lifted. An elastic control there was void: its preload was a hundred times too large by a scripting error (`probes/c2_pilot/README.md`).
- With the stiff spring the force error at the same $D$ was 4% to 8% up to $D = 1$ mm and 15% to 16% beyond, and so was the distance from the curve on the plateau, as the first-order relation above says.
- With the gate's spring, after 1,920 steps, the force error at the same $D$ was 2% to 3% at $D$ up to 2 mm while the distance from the curve was 14% to 20% there: the reading at the same $D$ would have hidden the error.
- With the gate's spring, after 9,600 steps, the median distance from the curve was 5.6% to 9.4% at $D$ up to 3 mm and 11.4% to 14.3% at 4 to 8 mm; the force error at the same $D$ was 1.0% to 1.6% up to 2 mm. The median error of $e$ was 10.4%.
- On the preloaded T1 the distance was 25% to 27% at $D$ of 0.5 and 1 mm, where its end displacement is under 0.2 mm, and 4.6% to 13% from 2 to 8 mm.

**This gate's samples.** No member drawn with 20261106 or 20261107 has been exported or solved.

**The tested members.** Bursi and Jaspart's T1 and T2, preloaded and snug, as members of the family: their geometry and yield stress with the family's nominal laws, bolt, web length and loading. The preloaded T1 was solved in this form by the test suite, the pilots and both reviews' checks, and all four by the dry runs on the coarse mesh. They are reported, not judged.

## Expected outcome, stated before the run

- **C1 is uncertain.** The pilot with the gate's loading ended at a median distance of 9.6%, down from 26.2% at half its steps. The run's model is larger, and it trains on 16 times as many members for more than ten times as many steps per seed, on a finer mesh. In G-C1.3 the step from pilot to gate took the median error from 7.9% to 0.29%; whether the plastic problem gains as much is not known.
- **C2 is likely to fail.** The pilot's 90th percentile was 37.9%. Its tail came from two places (`probes/c2_pilot/README.md`):
  - the weakest held-out member (a thin flange, a wide gauge and a low yield stress, with half the others' plastic force), 32% to 89% from $D = 3$ mm on;
  - the two smallest levels of two of the six held-out members, where the end displacement is under 0.2 mm: 22% to 54% (25% to 27% on the preloaded T1, which is reported only).
- **The errors are expected to lean one way.** In the pilot the predicted end displacements were mostly too small and the forces too large: the signed median distance was +8.5%.
- **The gate is therefore expected to fail**, on C2 at least.
- **The supervised arm** was not piloted. No expectation is stated for it.

## Configuration

**The configuration** is `c2/config.py`.
- Its canonical JSON has SHA-256 `795515630ff6f37a819c7503931c7d7cf6e70a9f272e25ac96730394dd361fb4`.
- The training and evaluation commands refuse to run unless they are given this hash.

**The repository code** the run imports is pinned in the configuration, file by file. The list comes from an import trace of training and the bench. The files are unchanged since wp9-pool 92dfc93. Training, the bench and `write-config --repo` refuse to run against other files.

| File | SHA-256 |
|---|---|
| `src/fejepa/__init__.py` | `6b4a69dde91fbd83c5c16707a00e4c9e6a2e02647aca1d3132b313e4b20f9fdc` |
| `src/fejepa/models/__init__.py` | `88d852286c71e468491b7d0b34cec2c467bd4c96724a26ca8ebcc6b8f92306e4` |
| `src/fejepa/models/features.py` | `0af43e0a87fda6bc177e9b446a720ac11e3e116bc29e445446edf846162c208d` |
| `src/fejepa/models/fejepa.py` | `3263988641477cfab564c5c622f8cf3406d98e45078134da8c6905d4b410b847` |
| `src/fejepa/train/__init__.py` | `88d852286c71e468491b7d0b34cec2c467bd4c96724a26ca8ebcc6b8f92306e4` |
| `src/fejepa/train/schedule.py` | `d53b55877c65efc37ee0a3877362451d8227ef84f581df64138ac1b469bd57c5` |

**SHA-256 of the gate's own code at stamping** (paths relative to `joint/`):

| File | SHA-256 |
|---|---|
| `c2/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `c2/__main__.py` | `a15c8a16a6dee2abb301dff54c060c44a287ca321262f780eb59a1aab09fb906` |
| `c2/config.py` | `f39c7c9bb0b6ef133f8c8b037c8a164870bf186a15ac853d38a53c79fd482d98` |
| `c2/family.py` | `ca8c205727008ccd01a1ae4963478e1dd6726c676ea1ebd436ec06c5e7e08f0d` |
| `c2/instance.py` | `a6c9feb3944f60758e1827ee85e55c4c4c200806c1fa5ade5fb30976737457ba` |
| `c2/data.py` | `e692ec41cbd8d9b24e72554d1be440e137ea3ec8567e834c53c257953a24b98f` |
| `c2/model.py` | `ccdc8aa50c442218dc92672ed0473049ec12af9800de7e0255abe37d46b50cc0` |
| `c2/train.py` | `40b8259b280a635e365f3fa3fc762db9dda555c1cc7627926f0af50aa5415598` |
| `c2/evaluate.py` | `60d92fe6b9291da8b2a62a7c32a30834c1299a0e6e77cd78512d20accaf455ff` |
| `c2/torch_energy.py` | `9c3ff9e41e54c0561b652aae2b936cbcd8946a91b2536f12f192b32706e03ef1` |
| `fejoint/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `fejoint/tstub.py` | `0d09c29d09d8a7b0318a1b40860a068fecd34ff04a74e1563cceeacc00b51afd` |
| `fejoint/tstub_pl.py` | `bcdb509c8695b1aa2c154eb8a98e32758ce85e92a8504cdba7e5b2e65fccd96d` |
| `fejoint/joint.py` | `23b7fb48f9a587384c797b597408e85b8c8e368dad69631af90c16c564a5c044` |
| `fejoint/hex8i.py` | `27e4964ef755c1055fd9159e860db2f7542952fac9e1237053ef3cdd1babc0f7` |
| `fejoint/contact.py` | `75885802990155b4634a8be58035658ead51510f0758ad1ce2d2778b5750db8a` |
| `fejoint/linsolve.py` | `a829f4f5d6becd7c1081db542f3ade923dc95ed7725527a2ad9f948a6eb6739a` |
| `fejoint/plasticity.py` | `8bfb3d00b558e366d63d4a940146fb34975e81ba7d00d37d3fe8ed30d629d94c` |
| `fejoint/nlhex.py` | `2f67dfd9603d3bfb400066d4bedbe514223d80468fc3e0b98ba4f7c7951cb522` |
| `fejoint/nlsolve.py` | `c1181535a45d9ad0928213ada75c436d2957293c36ae2ae559aee3c82310f788` |

A copy of these files is kept in `docs/G-C2.1_stamped_code`. The file `docs/G-C2.1_code.sha256` lists every hash for `sha256sum -c`.

## Data

**Family** (`c2/family.py`)
- Seven parameters, each sampled uniformly within its range: flange thickness $t_f$ 8 to 20 mm, web thickness $t_w$ 6 to 12 mm, root radius $r$ 8 to 18 mm, bolt gauge $w$ 70 to 110 mm, bolt axis to flange tip $n$ 20 to 40 mm, yield stress $f_y$ 235 to 460 MPa (flange and web alike), and the preload ratio $\rho$ 0 to 0.9.
  - The half bolt is shorter than its grip by $\delta = \rho N_y / k_{ax}$, with $N_y$ the bolt's nominal yield force and $k_{ax}$ its axial stiffness; $\rho = 0$ is snug. The bolt's force at zero load is below $\rho N_y$, because the clamped parts compress.
- Members that break the validity rules are rejected and redrawn: the bearing patch clears the root and the flange tip by at least 2 mm, and the web is at most 2 mm thicker than the flange.
- Fixed: length 80 mm, one bolt row at 20 mm from the end of the quarter model, web modelled to 120 mm, M12 bolts with two washers and a bearing radius of 12 mm, $E = 210{,}000$ MPa, $\nu = 0.3$; the loading spring, 20 kN/mm per quarter model.
- **Steel**: elastic to $f_y$, a plateau to 2% strain, linear to $1.35 f_y$ at 15%, then a slope of $E/10{,}000$. A slope of $E/10{,}000$ is added throughout the plastic range, which keeps the energy strongly convex; it raises the stress at 15% strain by about 3 MPa.
- **Bolt**: yield at 880 MPa on the tensile stress area, a plateau to 2% strain over the half bolt's length, linear to 960 MPa at 6%, then the same small slope.

**Samples**
- 512 training members, seed 20261106.
- 64 held-out members, seed 20261107.
- The four tested members, reported and not judged.
- The code refuses any seed used before the stamp.

**Levels.** The held-out and tested members are judged at loading-device displacements $D$ of 0.5, 1, 2, 3, 4, 6 and 8 mm: 448 held-out pairs of member and level.
- In the seven members solved on the gate's mesh before the stamp, the end displacement was 0.04 to 0.08 mm at $D = 0.5$ mm and 4.0 to 5.8 mm at 8 mm. Yielding began at $D$ of 1 to 3 mm, and the force curves flattened from about 3 to 4 mm.
- The supervised arm's members are labelled at 0.75, 1.5, 2.5, 3.5, 5 and 7 mm, so that its training levels differ from the judged ones.

**Export** (`c2/instance.py`): the problem of each member in arrays (mesh, hardening curves, the map from the unknowns to the nodal displacements, the linear springs, the bolt's law and pre-shortening, the loading spring, the virtual field of the stress reading), without any solve.
- Labels and the evaluation rebuild the problem from these arrays alone (`ExportedProblem`).

**Labels.** Exact solutions at the levels, in increasing order, each level from the previous level's solution (deformation theory: the solution does not depend on the path; the start only saves iterations). Sequential quadratic programming with a primal-dual active set step and an Armijo search on the energy, stopped at a relative step of $10^{-12}$. Each label keeps both force readings, the spring's and the stresses'.

## Model and training

**Network**
- The repository's encoder (`fejepa.models.fejepa.build_encoder`, pinned above): width 256, depth 8, 8 heads, with its activation checkpointing.
- A copy of its field decoder (node latent and pooled latent, two GELU layers), last layer zeroed at the start.
- A head network for the end displacement $e$ and the bolt head's three unknowns (an axial displacement and two tilts), from the pooled latent, two GELU layers, last layer zeroed.
- Per-node features (21): centred, RMS-normalised coordinates (3), Dirichlet flags (3), node flags (7), the family parameters over their range maxima (7), and $D$ over 8 mm (1).
- Every output times $D + \delta$; the tilts also over the bearing radius. The web's $u_x$ is $e$ plus the network's correction.
- Softplus at $T = 10^{-3}$ on the non-negative unknowns: $u_x$ on the plane between the flanges and the separation slots of the bearing patch.
- The fixed unknowns are set to zero exactly: the symmetry planes, and the unused slots of the end section.

**Training**
- AdamW, learning rate $10^{-3}$, weight decay $10^{-4}$, gradient clipping at 1.0, for both arms.
- The repository's cosine schedule with 5% warm-up, over each run's own steps.
- One member per step, in a fresh random order each epoch, with four loading levels per step.
  - Label-free: $\sqrt{D}$ uniform between $\sqrt{0.1}$ and $\sqrt{8}$ mm.
  - Supervised: four of the member's six labelled levels, without replacement.
- **Label-free loss**: the mean over the four fields of $\log \Pi$, with $\Pi$ the energy of the deformation theory in float32 (`c2/torch_energy.py`), the loading spring included. The bubble parameters of each element come from ten damped Newton steps without gradient tracking; at their minimiser the gradient is the envelope gradient.
- **Supervised loss**: the mean squared error of the physical displacements over $(D + \delta)^2$.
- Float32 weights, activations and energy, with float32 matrix products at the precision "highest" (no TF32).
- A non-finite loss stops the run, and a run whose predictions are not finite records that instead of predictions. Either stop is final and is not retried.
- Every attempt of a run is logged in `attempts.log` in its run folder.

**Arms**, three seeds each (0, 1, 2):

| Arm | Loss | Training members used | Labelled fields | Steps per seed |
|---|---|---|---|---|
| label_free | mean of $\log \Pi$ | 512 | 0 | 102,400 (200 epochs) |
| supervised_64 | mean squared error over $(D + \delta)^2$ | the first 64 | 384 | 12,800 (200 epochs) |

**Budget**
- 345,600 steps in all.
- The bench (section 3 of the runbook) times label-free steps of the full model on the GPU host before any training, on the first 8 training members: 5 warm-up steps, then 40 timed.
- At 0.30 s a step the training would take at most about 29 hours.

## Criteria (on the label-free arm, held-out members)

The point of a field is $(e, F)$: $e$ its end displacement and $F = 4 k_s (D - e)$ its spring reading. Its error is $F/F^*(e) - 1$, with $F^*(e)$ the reference force at end displacement $e$: an exact solve with $e$ prescribed, in float64 by the reference code on the exported problem, started from the label nearest in $e$.

**C1.** The median over the three seeds of the per-seed median of $\lvert F/F^*(e) - 1\rvert$ over the 448 held-out pairs is at most 0.05.

**C2.** The median over the three seeds of the per-seed 90th percentile of $\lvert F/F^*(e) - 1\rvert$ over the same pairs is at most 0.10.

**Verdict.** G-C2.1 passes if and only if C1 and C2 hold.
- A pair whose solve at the predicted end displacement fails or does not converge, or gives a force that is not positive, has an infinite error. It enters the median and the 90th percentile as such.
- A label-free seed whose run stopped on a non-finite loss, or whose predictions were not finite, or for one of whose members the metrics failed altogether, is final. It enters the medians over seeds with infinite errors. A FAIL that such a seed decides is reported as a failure of training at these settings, with the seeds named.
- A label-free seed missing for any other reason makes the verdict INCOMPLETE.
- Supervised seeds do not enter the verdict. A missing or non-finite supervised seed is reported as such.

**Reported, not judged**
- For every arm and seed, on the held-out and the tested members, by level and overall:
  - the signed distance from the reference curve, and the pairs with an infinite error, with the reason;
  - the force error at the same $D$, $F/F_{ref} - 1$, with the certified bound $4\sqrt{2 k_s (\Pi - \Pi^*)}/F_{ref}$ and the fraction of pairs inside it (1 by the theorem);
  - the force read from the stresses, $F_\sigma = 4\,\nabla W(z) \cdot v$, $W$ the energy without the loading spring and $v$ a ramp in the web, against $F_{ref}$;
  - the error of the end displacement $e$ at the same $D$;
  - the energy gap $(\Pi - \Pi^*)/\Pi^*$;
  - the contact overlap on the plane between the flanges ($u_x \le 10^{-3}(D + \delta)$, prediction and reference alike);
  - the overlap of the plastic Gauss points;
  - the bolt force error and the relative error of the physical displacements.
- A pair whose energy the reference code cannot evaluate has these readings not a number; such pairs are counted.
- The four tested members.
- The supervised arm against the label-free arm, with no winner set in advance.
- The metrics of every pair, in `verdict.json`.

## Interpretation, fixed in advance

**PASS.** Label-free training of the project's transformer reproduced the reference model's force-deformation curve: its predicted points lay within 5% of the curve in force in the median, and within 10% at the 90th percentile, through the elastic, yielding and hardening range.
- This holds over 64 unseen T-stubs of this family at seven loading levels each, in the median over three training seeds.
- It holds on the 5 mm mesh, for small strains, frictionless contact and the deformation theory under monotonic loading.
- The gap of the reference model to the T-stub tests stands as stated.
- Any wording says that the surrogate reproduces the reference model, not the tests, and gives that gap.

**FAIL on C2 only.** The median is within 5%, but the tail is not within 10%. The pairs above 10% are listed by member and level.

**FAIL on C1 only.** Not expected: a 90th percentile within 10% with a median above 5%. Reported as such.

**FAIL on both.** At this budget the label-free surrogate does not reproduce the plastic force-deformation curve within these limits.

**In every FAIL**
- The thresholds stay.
- The supervised arm and the reported readings are described, not substituted for the criteria.
- Any next stage is pre-specified anew.

**INCOMPLETE.** A label-free seed is missing for a reason other than a final stop.
- It is resumed from its last checkpoint, or run again from the start if it has none, with the stamped code and configuration. Nothing else changes.
- While the verdict is INCOMPLETE, the evaluation withholds every label-free metric and forms no criterion value.
- If a resumed run fails again with the same error, stop and report. Any change then, as after a bench stop, is a change after the stamp.

## What the gate does not show

- Anything about the T-stub tests, that is, the experiments.
- Unloading, cyclic loading or any load path that is not monotonic: the deformation theory holds for proportional loading only.
- Large displacements, friction, fracture, or bolts that bend.
- Other meshes, or T-stubs outside this family.
- How the worst members fare beyond the 90th percentile.
- Where along the curve a prediction lies for its $D$: the error of $e$ at the same $D$ is reported, not judged.

## Stop conditions

- **Checks.** A precondition, test, hash or count in the runbook differs from what the runbook states: stop and report before going on.
- **The bench.** Its mean exceeds 0.30 s a step, any of its 45 losses is not finite, or the training set's energies and the peak memory leave less than 2 GB of the GPU's memory: stop before any training, and report to the owner.
- **The labels.** The label check fails: stop before any training, and report. It fails if a member that needs labels is not labelled once at its split's levels, if a level did not converge, if a file differs from the manifest or the ledger, if the two force readings of a reference differ by more than $10^{-6}$ relatively, or if a worst optimality residual lies outside the limits in `c2/config.py`: gap no lower than $-10^{-12}$, multiplier no lower than $-10^{-8}$, complementarity at most $10^{-8}$, the multipliers of separated unknowns and the residuals of unconstrained unknowns at most $10^{-6}$ (relative, as `fejoint.nlsolve` reports them).
- **Errors.** A training run that ends with an error other than a final stop: stop the training loop and report.
- **Time.** Training has not finished within one and a half times the time the bench bounds: report to the owner. The runs go on unless the owner stops them.
  - A stop before the three label-free seeds have ended leaves the verdict INCOMPLETE until they are resumed.
  - A stop after that leaves the supervised seeds not run reported as missing; the verdict stands.
- Nothing else uses the GPU during the bench and the training.

## Procedure

`RUNBOOK_C2.md`, run on the GPU host, in its sections:
0. preconditions, the worktree, the hash check and the tests;
1. the configuration hash and the repository check;
2. generation, without solves;
3. the bench and its stop rule;
4. labels for the held-out, tested and first 64 training members, and their check;
5. the six training runs, which resume if interrupted;
6. evaluation;
7. the return package.

## References

- Bursi, O.S., Jaspart, J.P. (1997). Benchmarks for finite element modelling of bolted steel connections. *Journal of Constructional Steel Research* 43(1-3), 17-42. doi:10.1016/S0143-974X(97)00031-X
- Ortiz, M., Stainier, L. (1999). The variational formulation of viscoplastic constitutive updates. *Computer Methods in Applied Mechanics and Engineering* 171(3-4), 419-444. doi:10.1016/S0045-7825(98)00219-9
- Simo, J.C., Hughes, T.J.R. (1998). *Computational Inelasticity*. Springer, New York.
- Taylor, R.L., Beresford, P.J., Wilson, E.L. (1976). A non-conforming element for stress analysis. *International Journal for Numerical Methods in Engineering* 10(6), 1211-1219. doi:10.1002/nme.1620100602
