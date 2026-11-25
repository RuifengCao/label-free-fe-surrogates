# Records of the development of the CHS surrogate, 20 to 25 November 2026

Exploratory runs, described in `docs/F2_development_note.md`. Nothing here is a result on members that were not seen. Every number of the tables and of sections 5 to 8 of the development note, and of the table and the paragraph below it in "What was seen before the stamp" of `docs/PRESPEC_G-F2.1.md`, can be computed again from the evaluation files below: the median, the 90th percentile (linear interpolation) and the largest value of `abs_curveD_err` over the rows of a seed and a reading. The readings during training in section 3 of the note and its runs with a single member have no file here; the times come from the runs' records and the sizes from the manifests.

`FILES.sha256` lists the SHA-256 of every file of this folder but itself, `as_written.sha256` and this text. The five evaluation files of the laptop's runs (`smaller_mesh/three_lifts_200_epochs/`, `smaller_mesh/200_epochs_seeds_1_2/`, `smaller_mesh/200_then_200_epochs/`) were written there with CRLF line ends; they are kept here with LF line ends and are otherwise unchanged, and `as_written.sha256` lists their SHA-256 as they were written.

## What the files are

A run's files are those that `f2/train.py` and `f2/evaluate.py` write:
- `history.json`: the run's record, written when it ended: its configuration hash, seed, losses, seconds an epoch, the actions of the cap on the encoder's gradient, the hashes of the code it ran.
- `snapshots.json`: at the configured epochs, what the network's fields give at the seven levels for the 31 evaluated members (end rotation, moment, rotation of the measuring ring, energy), in the raw reading. No reference solution enters it.
- `condense.json`: the amplitudes of the condensed reading and the readings of the condensed fields.
- `evaluation.json`: every metric of every pair (member, level) for each finished seed and both readings, computed by the reference code. The keys of `rows` are `<seed>|<reading>`.
- `attempts.log`: every start, resume and end.

The state files and the prediction files of the runs are not here; they are too large.

## Folders

**`host/sessions.jsonl`**: the machine and the library versions of each session of the hosted runtime on which the runs of 400 epochs and all runs on the family's mesh were made.

**`data/`**: what describes the members, without their meshes and fields.
- `family_mesh/`: the 128 training members and the 31 evaluated members on the family's mesh: `manifest.json` (parameters, sizes, file hashes), `generate_log.json` (the preload solves), `labels_ledger.json` (the reference solves of the 31) and `labels_summary.json` (the reference curves: moments, rotations, bolt forces at the seven levels).
- `family_mesh_thin/`: the 32 further training members with thin plates (24 November 2026).
- `smaller_mesh/`: the same members on the smaller mesh: `manifest.json` and `labels_summary.json`.

**`smaller_mesh/`**: runs on the smaller mesh, each against that mesh's own reference solutions.
- `three_lifts_200_epochs/`: the three family runs of 20 and 21 November 2026, seed 0, on the laptop: `evaluation_bending.json`, `evaluation_frame.json`, `evaluation_hinge.json`.
- `200_epochs_seeds_1_2/evaluation.json`: the bending run of 200 epochs with seeds 1 and 2, on the laptop.
- `200_then_200_epochs/evaluation.json`: seed 0 after a second cycle of 200 epochs, on the laptop.
- `400_epochs/`: the three runs of 400 epochs, seeds 0, 1 and 2: `evaluation_seeds_0_1_2.json`, and the record and the snapshots of seed 0.

**`family_mesh/`**: runs on the family's mesh, all with seed 0.
- `first_cycle/`: preset `fam128_bending_e400`, 21 and 22 November 2026. The first cycle of the gate's recipe.
- `second_cycle_22_november/`: preset `fam128_bending_more`, from the first cycle's final weights. With the evaluations of the two moving averages of its weights.
- `trial_24_november/`: the trial of two changes to the second cycle (`probes/f2_stage2/PRESPEC.md`). `arm_1/` is preset `fam128_bending_more_u`, `arm_2/` is preset `fam128_bending_more_ux`, the second cycle of the gate's recipe. `verdict.txt` is the output of `probes/f2_stage2/stage2_verdict.py` and `outside_the_rule.txt` that of `probes/f2_stage2/stage2_extra.py`.
- `trial_25_november/`: the trial of a two-level recipe (`probes/f2_under/PRESPEC.md`), preset `fam128_bending_under_e150`. `verdict.txt` is the output of `probes/f2_under/under_verdict.py`. `outside_the_rule.txt` holds further statistics of the same three evaluation files (the first cycle's, the second cycle's of 22 November 2026 and the trial's), from a script that was not kept. `smaller_mesh_exact_against_family_exact.json` is the output of `probes/f2_under/tiny_vs_family_exact.py`, which compares the reference solutions of the two meshes.

**`code_as_run/`**: the files of `f2/` as the two runs of the gate's recipe had them, each with the SHA-256 that its run's `history.json` records under `code`: `2026-11-21/` for the first cycle and `2026-11-24/` for arm 2 of the trial. The files of the other packages that those runs recorded are unchanged in the repository. `probes/f21_code_equivalence/` compares a stand-in training under these files with one under the stamped files; to do so, copy `joint/` and `src/` of the repository and put the files of one of the two folders in the place of those in `joint/f2/`.

## Limits

- One training run a configuration, apart from the three seeds of the smaller mesh.
- The laptop's runs and the hosted runs differ in machine and library versions; the laptop's are not recorded here beyond what the evaluation files hold.
- The evaluation files hold `Infinity` and `NaN` where a value is infinite or not a number. Python reads them; a strict JSON reader does not.
- The evaluation files of 20 to 22 November 2026 were written before the evaluation recorded which readings have the exact reference at the predicted rotation of the measuring ring; none of them has it.
