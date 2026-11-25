# CHS surrogate: development, 20 to 25 November 2026

Exploratory. Nothing here was pre-specified apart from the two trials of sections 6 and 7, and no number here is a result on members that were not seen: the 31 evaluated members were read after every run and at snapshots during every run. The preparation before this work (the family, the export, the reference, the loading) is in `docs/F2_preparation_note.md`. What a gate makes of the outcome is in `docs/PRESPEC_G-F2.1.md`. The records are in `records/f2_dev/`, with a list of their own.

## 1. What was built

- `f2/model.py`: the network of the T-stub gates (the repository's transformer encoder over the nodes, a copy of its field decoder, a head for the unknowns that belong to no node) with the features of a CHS member and with a lift: a fixed field of the member, multiplied by the end rotation that the head gives, is added to the nodal outputs, so that the network gives the tube's displacements as a correction to a simple motion that follows the end section.
- `f2/train.py`: label-free training with checkpoints and resume. The loss of a step is the mean of log Π over four device rotations of one member, Π being the total potential energy of the reference model with the loading spring. The stability settings are those of gate G-C2.2.
- `f2/evaluate.py`: every metric computed by the reference code in double precision on the exported problem.
- `f2/devconfig.py`: every configuration that was run, by name. `f2/precond.py` and `f2/prolong.py` serve trials that were not adopted (sections 4 and 7).
- `tests/test_f2_dev.py`.

**The two readings** are those of gate G-C2.2: the network's field itself (raw), and the field after one amplitude has been set by minimising the training energy (condensed).

**The errors.** For a member and a level, the field gives the end rotation, the moment through the loading spring, and the rotation of the measuring ring, which is the rotation the tests report.
- *At the same device rotation*: the moment against the labelled solution's. This is the easiest reading: a surrogate whose joint opens too little shows a small error here, because the spring hides it.
- *At the same end rotation*: the moment against the reference curve at the predicted end rotation, from one exact solve.
- *At the same rotation of the measuring ring*: the moment against the reference curve at the predicted rotation of the measuring ring, to first order from that solve. The elastic tube beyond the ring makes up most of the end rotation at small loads, so this reading is the strictest of the three, and it is the one a moment-rotation curve shows. All numbers below are this reading unless they say otherwise, as median, 90th percentile and largest value over the 217 pairs of the 31 members and seven levels.

## 2. Members and meshes

- 128 training members drawn with seed 20261120. Exported with their preload state; never solved further.
- 31 evaluated members: 16 drawn with seed 20261121, eleven picked by hand at corners and centres of the family, and the tested splices B-13 and B-19 at two preloads each.
- From 24 November 2026, 32 further training members with plates of 10 to 12.5 mm, seed 20261124 (section 6).
- **The family's mesh** (called coarse in the code) is the mesh of gate G-F1's coarse runs: B-13 has 8,632 nodes and 25,916 unknowns.
- **A smaller mesh** (called tiny) has 2,543 nodes for B-13. It was used to try things at a fraction of the cost. It is a stiffer model: at the same device rotations B-13's moment is 0.9% to 5.1% higher and the rotation of its measuring ring 4.8% to 10.7% lower. Numbers on the smaller mesh are against that mesh's own reference solutions.

## 3. First runs: the joint opens late (20 and 21 November 2026)

- **One member, 600 steps, family's mesh.** The end rotation reached 26% to 43% of the reference's, the measuring ring did not rotate, and the energy stayed 12% to 34% above the reference's. A lift that rotates the whole tube rigidly about its base was worse; a lift with a separate rotation of the tube's base was slightly better on the smaller mesh after 1,000 steps.
- **Three family runs on the smaller mesh**, 128 training members, 200 epochs (25,600 steps), seed 0, with three lifts: pure bending of the tube (bending), a beam with a base rotation (frame), and the same with the plate following the base where it rises (hinge). On the owner's laptop, where a step on the family's mesh takes 5.0 s.
  - For the first 40 epochs the joint stayed almost closed in all three: at epoch 40 the error of the moment at the same device rotation was still 14% to 16% in the median, and the measuring ring rotated by less than a fifth of the reference's. Then the joint opened: with the bending lift the median fell to 7.9% at epoch 70 and 4.2% at epoch 100.
  - At the end, at the same device rotation, raw reading: 0.6% and 5.8% (median and 90th percentile) with bending, 1.6% and 11% with hinge, 2.2% and 11% with frame. At the same rotation of the measuring ring, raw: 4.4% and 13.4% with bending, 12.7% and 30.9% with hinge, 15.5% and 38.5% with frame. **The simplest lift was the best, and only it was used afterwards.**
  - The last level was not converged when the schedule ended: every one of the 31 members was too stiff there.

## 4. Why the start is slow, and what was tried against it (21 November 2026)

`probes/f2_plateau/` holds the scripts; all on one member of the smaller mesh, most on a processor.
- The network first settles on the state with the splice plane closed everywhere. Its energy is only one to two tenths above the solution's, and leaving it means moving a soft, global mode that pointwise first-order descent hardly moves.
- The elastic contact solution of a member (one sparse factorisation, a small quadratic programme a level) is the reference solution at the four lowest levels within 0.03% in energy, and differs from it at the last level by what plasticity adds.
- Losses built on it were tried for some tens to hundreds of steps: the distance to the elastic contact step, to the elastic solution, each alone, added to the energy, or as an anchor at the low levels. **None was adopted.** The energy alone opens the joint, later.
- **Carrying weights between meshes.** A network trained on the smaller mesh gives, on the family's mesh and without further training, rotations and moments like those on its own mesh, but a rough field with more than twice the reference's energy. Trained on at once on the family's mesh, alone or in turn with the smaller mesh, the joint closed again within an epoch; the runs were ended by their stop rule. **The family's mesh is trained from new networks.**

## 5. Longer training, and a second cycle (21 and 22 November 2026)

The runs of 400 epochs and the second cycle on the family's mesh were made on a hosted runtime with an RTX PRO 6000, where a step on the family's mesh takes 0.67 s; the two runs of 200 epochs on the laptop.

| Run | Mesh | Seed | Median | 90th percentile | Largest |
|---|---|---|---|---|---|
| 200 epochs | smaller | 0 | 4.40% | 11.79% | 61.0% |
| 400 epochs | smaller | 0 | 0.93% | 3.10% | 17.2% |
| 400 epochs | smaller | 1 | 1.28% | 4.11% | 51.4% |
| 400 epochs | smaller | 2 | 1.17% | 3.52% | 30.0% |
| 200 epochs, then 200 more from its weights at a peak rate of 3e-4 | smaller | 0 | 1.67% | 4.92% | 53.1% |
| 400 epochs: **the first cycle** | family's | 0 | 1.53% | 5.39% | 67.9% |
| the first cycle, then 200 epochs from its weights at a peak rate of 3e-4 | family's | 0 | 0.99% | 3.69% | 56.9% |

- **Twice the steps closed most of the gap** on the smaller mesh, and the three seeds agree within about a fifth. Seed 0 is the best of the three; the family's mesh has seed 0 only.
- On the smaller mesh, 200 and 200 epochs were worse than 400 in one go (one run each, on two machines).
- On the family's mesh a second cycle helped. Two moving averages of its weights, kept beside it, gave 1.00% and 3.69%, and 1.21% and 4.11%: no gain, and they were dropped.
- **What was left**: the last level (median 3.42%, every member too stiff) and thin plates (the thinnest hand-picked member 56.9% at its last level).

## 6. Trial of two changes to the second cycle (24 November 2026)

Plan and rule fixed before the runs: `probes/f2_stage2/PRESPEC.md`. Both arms are second cycles from the first cycle's final weights, with the same 25,600 steps. Arm 1 draws the device rotations of the training steps uniformly and up to 1.15 times the device range. Arm 2 does the same and adds the 32 further training members.

| Measure (per cent) | Line | Control | Arm 1 | Arm 2 |
|---|---|---|---|---|
| P: median at the last level, 8 members with plates under 12.5 mm | at most 5.30 | 7.07 | 4.27 | 2.78 |
| G1: median at the last level, 31 members | at most 3.76 | 3.42 | 1.76 | 1.86 |
| G2: median, 217 pairs | at most 1.09 | 0.99 | 1.06 | 1.07 |
| G3: 90th percentile, 217 pairs | at most 4.06 | 3.69 | 3.46 | 2.99 |
| G4: 90th percentile, the 16 random members | at most 3.18 | 2.89 | 2.97 | 2.53 |
| G5: median at the two lowest levels | at most 0.87 | 0.79 | **1.04** | **1.01** |

- **By the rule neither arm passed**, both on G5, and the second cycle of 22 November 2026 was to be kept.
- Outside the rule: the largest error fell from 56.9% to 17.6% and 12.2%; all 31 members improved at the last level, and 29 and 27 of them got worse at the two lowest levels. The uniform draw moves training steps from small rotations to large ones: the share of steps below one eighth of the device range falls from 27% to 10%.
- **Arm 2 was adopted all the same**, as a stated deviation from the rule, by the owner's decision of 25 November 2026. `docs/PRESPEC_G-F2.1.md` gives the reasons and what the deviation means.

## 7. Trial of a two-level recipe (25 November 2026)

Plan and rule fixed before the run: `probes/f2_under/PRESPEC.md`. A network on the family's mesh was trained for 150 epochs as a correction to the field of the finished 400-epoch network of the smaller mesh, carried to the family's mesh.
- Result: 4.69%, 11.64% and 34.3%, the rule's lowest class. **Not adopted.**
- Why, as far as it was looked into: the error of the trial is close to the error of the smaller mesh's own exact solution read as a solution of the family's mesh (moment at the same rotation of the measuring ring 3.8%, 9.2% and 11.8% apart). The correction did not remove the discretisation error of the field underneath.

## 8. The recipe at the end of the development

1. The first cycle: preset `fam128_bending_e400`, new networks, 400 epochs on the 128 training members, peak learning rate 1e-3.
2. The second cycle: preset `fam128_bending_more_ux`, from the first cycle's final weights with a new optimiser and schedule, 160 epochs on 160 training members, peak learning rate 3e-4, device rotations uniform up to 1.15 times the device range.
3. The condensed reading.

With seed 0 on the 31 members: 1.07%, 2.99% and 12.2%; raw 1.29%, 3.94% and 20.8%. On the 16 random members 1.02%, 2.53% and 4.4%; on the four tested members 0.51%, 1.60% and 2.1%.

## 9. What the development does not show

- **One seed on the family's mesh.** How much two runs of the recipe differ there is not known.
- **Members seen.** The 31 members were watched throughout, and the recipe's last step was chosen on them against a rule.
- **Nothing about tests.** Every error is against the frictionless reference model, which is itself 3% to 8% below the measured moments of B-13 and B-19 (`docs/F2_preparation_note.md`).
- **Cost.** An epoch of the first cycle took 85.5 s and one of the second 107.0 s on the RTX PRO 6000: about 14.3 hours for one seed. No comparison with the cost of the reference solve was made.
