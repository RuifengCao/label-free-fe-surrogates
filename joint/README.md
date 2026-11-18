# Extended end plate joints (stage C)

This folder holds the work towards a label-free surrogate for the extended end plate joints tested by Girão Coelho, Bijlaard and Simões da Silva (2004). It contains the finite element models, the gates that tested them against the experiments, the pre-registered training gate G-C1.3 with its records and verdict, and the plastic stage C2 on bolted T-stubs: its training gate G-C2.1 with its records and verdict, the exploratory work after that verdict, and its second training gate G-C2.2 with its records and verdict. It also holds the first tubular case: bolted circular hollow section (CHS) blank flange-plate splices tested by Fidalgo (2023), with gate G-F1.

## Contents

**`fejoint/`: the finite element code**
- `hex8i.py`: eight-node hexahedra with incompatible modes.
- `contact.py`: frictionless unilateral contact, solved by the primal-dual active set method.
- `linsolve.py`: the sparse solver.
- `joint.py`: the idealised joint model of G-C1a.
- `specimens.py`: the tested details.
- `joint_hf.py`, `tstub_hf.py`, `tstub.py`, `delft_tstubs.py`: the higher-fidelity joint and T-stub models of G-C1a2 and G-C1b, and the T-stub tests.
- `family.py`, `export.py`: the joint family of stage C1.3, and its condensed nodal problem.
- `plasticity.py`, `nlhex.py`, `nlsolve.py`, `tstub_pl.py`: the plastic models of stage C2. J2 plasticity in deformation-theory and flow-theory form with one radial return; the incompatible-mode hexahedra with their bubble parameters condensed by Newton's method at the element level; sequential quadratic programming with contact; the T-stub with plastic flange, web and bolts, preload, and force or displacement control.
- `chs.py`: the CHS blank flange-plate splice of gate G-F1. A structured mesh in cylindrical coordinates with stair-stepped holes, an unfused weld root and a fillet, coarse O-grid core and far tube tied by hanging nodes; preloaded half bolts; bending or axial control; a frictionless or a no-slip splice.

**`c13/`: the run code of gate G-C1.3.** `RUNBOOK_C13.md` gives its commands in order. `RUNBOOK_C13_addendum.md` records what the operator was given beyond it after the stamp.

**`c2/`: the run code of gate G-C2.1**, label-free training on plastic T-stubs loaded through a spring. `RUNBOOK_C2.md` gives its commands in order.

**`c22/`: the run code of gate G-C2.2**, G-C2.1's problem with two changes of method: a stability recipe in the training, and a condensed reading of the predicted point, in which one amplitude of the field is set by minimising the energy. It is judged on a fresh held-out sample. It imports `c2/` and `fejoint/` as stamped for G-C2.1 and adds its own configuration, training, reading and evaluation, with a check of the host (`c22/smoke.py`). `RUNBOOK_C22.md` gives its commands in order.

**`c23/`: the run code of gate G-C2.3**, which trains nothing new in the label-free arm: the three networks of G-C2.2 are read from their state files and predict a third held-out sample. Part 1 judges a self-check, the spread of the predicted force over the three networks against a threshold fixed in advance. Part 2 trains the same network on reference solutions of the 512 training members and compares the two arms. It imports `c22/`, `c2/` and `fejoint/` as stamped for G-C2.2 and adds its own configuration, splits, supervised training and evaluation in two steps, with a check of the host (`c23/smoke.py`). `RUNBOOK_C23.md` gives its commands in order.

**`f1/`: the run code of gate G-F1**, the CHS splices of Fidalgo (2023) against their tests, with frictionless and no-slip splices as bounds. `python -m f1 -h` lists its commands; `docs/PRESPEC_G-F1.md` gives the run. `f1/data/` holds the test curves, bolt forces and coupon curves digitised from the thesis's figures, and `f1/digitise/` the scripts that reproduce every data file from the thesis PDF.

**`f2/`: draft code for a surrogate gate on the CHS splices**, provisionally G-F2, not under any stamp: the family of splices (`family.py`), the spring-loaded export with preload (`instance.py`), the data (`data.py`), the configuration (`config.py`) and the energy in torch (`torch_energy.py`). `docs/F2_preparation_note.md` describes it; `tests/test_f2.py` checks it.

**`audit/`: the audit scripts of G-C1.3, G-C2.1 and G-C2.2**, not under the stamp. Those of G-C1.3 and G-C2.1 were written after each run. Of G-C2.2's, steps 1 to 6 of the recomputation were written while its evaluation ran, before its result was known; its step 7, the packing of the solves, the option `--reverse` and the other three scripts were written after the run (the author's statement; no record dates them)
- `c13_recompute.py`: regenerates the held-out and tested instances of G-C1.3, re-solves seven of them, and recomputes every metric of the label-free arm from the returned predictions and labels.
- `c13_write_verdict.py`: the tables of G-C1.3's verdict, from the records.
- `c2_recompute.py`: regenerates all 580 instances of G-C2.1, recomputes every metric of the label-free arm on the held-out and tested members from the returned predictions and labels, and re-solves four members.
- `c2_write_verdict.py`: the tables of G-C2.1's verdict, from the records.
- `c22_recompute.py`: regenerates all 644 instances of G-C2.2; recomputes the criteria from the returned per-pair values, every metric that needs no solve for every returned field, and the judged error with its exact solve for every pair of the judged reading on the judged set; re-solves four members; and checks the returned records. Its steps `--fields`, `--curves`, `--resolve` and `--records` need the kept copy whole (`c22_deposit.py restore`).
- `c22_write_verdict.py`: the tables of G-C2.2's verdict, from the records.
- `c22_keep.py`: writes the kept copy of G-C2.2's return package, of which `records/c22/return/` holds all but the label and prediction files, the lists of its hashes, its listing and the report of what was changed and left out. It reads the strings that it replaces from a file that is not in the repository.
- `c22_deposit.py`: makes the archive of the 141 label and prediction files of that copy, which is deposited outside the repository, and `records/c22/deposit.json`; with `restore` it checks a downloaded archive and then writes its files into `records/c22/return/`, and with `check` it compares that folder with the list of the kept copy's hashes. Written on 17 November 2026.
- `independent/G-C2.1/`: the scripts of the independent audit of G-C2.1's verdict, written by the auditor without importing the author's audit scripts: `audit_records.py` (labels, ledger, histories, predictions and criteria from the records), `regen.py` (instances regenerated and compared with the manifest), `reeval.py` (held-out pairs re-evaluated with the stamped code), `preds_constraints.py`, `draft_numbers.py` and `round2_checks.py`. Its reports are in `docs/reviews/`.
- `independent/G-C2.2/`: the scripts of the independent audit of G-C2.2's verdict, written by the auditor without importing the author's audit scripts: `a1_criteria.py` (the criteria from the per-pair values), `a2_select_pairs.py`, `a3_recompute_pairs.py` and `a15_pairs_summary.py` (the judged error of 161 pairs with exact solves), `a13_cold_start.py`, `a14_resolve_label.py`, `a9_regenerate.py` (the instances), `a10_all_fields_force.py`, `a4_run_checks.py` (configuration, code, sample, ledger, histories, queue, host check), `a5_condensed_reading.py`, `a7_document_tables.py`, `a12_text_numbers.py`, `a8_author_outputs.py`, `a6_kept_copy.py`, `a11_commit_checks.py`, from its second round `b1_round2_tables.py` (the cells of the added tables) and `b2_round2_step_times.py` (the slow stretches of the runs), and from its third round `b3_round3_strings.py` (the replaced strings, in plain and encoded forms, in every path of the commit) and `b4_round3_lists.py` (the three lists with the placeholders), and from its fourth round `c1_round4_step.py` (the step from the commit with the label and prediction files to the commit without them), `c2_round4_deposit.py` (the deposit's record and the archive, with a reader of the tar format of its own), `c3_round4_restore_tests.py` (what `audit/c22_deposit.py` does with wrong archives and records) and `c4_round4_archive_strings.py` (the replaced strings in the archive). Its reports are in `docs/reviews/`. Of the scripts of the first three rounds, `a3_recompute_pairs.py`, `a4_run_checks.py`, `a5_condensed_reading.py`, `a6_kept_copy.py`, `a10_all_fields_force.py`, `a13_cold_start.py`, `a14_resolve_label.py` and `b4_round3_lists.py` read label or prediction files and need the kept copy whole (`c22_deposit.py restore`). The scripts of the fourth round need the archive, and `c1_round4_step.py` the earlier state of the commit, which is not in the repository.

**`records/c13/`: the records of G-C1.3**
- `return/`: the files of the operator's return package `c13_return.tar.gz` (SHA-256 `8b88839c9f452bbdd2e2e906d790d34505dc784bf862e5dbe055225326d6cb7b`), as received, with their hashes in `return_files.sha256`.
- `audit/recompute.json` and `audit/recompute_blas2.json`: the recomputation, with the BLAS of numpy and scipy on 25 threads as on the host, and on 2.

**`records/elements/`: the records of the element study** (`docs/element_study_note.md`)
- `study.jsonl`: the 70 runs of seven element kinds on meshes from 20 mm to 2.5 mm;
- `washer_radius.jsonl`, `review_checks.json` and `checks.json`: the washer patches, three checks of the review, and the checks of the elements;
- `tables.md` and `convergence.png`, written from `study.jsonl` and `checks.json` by `probes/elements/write_report.py`.

**`records/c2/`: the records of stage C2**
- `bj1997_*`: the reference model on Bursi and Jaspart's T-stub T1, preloaded: deformation and flow theory on the 5 mm mesh, deformation theory on the 2.5 mm mesh (`probes/c2_bj1997.py`).
- `return/`: the files of the operator's return package of G-C2.1, `c2_return.tar.gz` (SHA-256 `7b6f19e6c316b0a3bf39c6821206f9e061dc2d8b1fc09724acdad125946b3ae0`), as received, with their hashes in `return_files.sha256` and the archive's listing in `return_listing.txt`.
- `audit/`: the author's recomputation (`audit/c2_recompute.py`): `regenerate.json`, the folder `members/` (one file a member) and `environment.json` beside it, `resolve.json` and `aggregate.json`. `numpy253/` holds a first pass with numpy 2.5.3, stopped after six members.

**`records/c22/`: the records of gate G-C2.2**
- `host_check/`: the report and the log of the check of the gate's code on its host, the owner's laptop, run before the stamp on a reduced configuration that draws nothing of the gate (`c22/smoke.py`, 13 November 2026). The two files were written on Windows and are stored with Unix line endings; in the log the path of the working folder was shortened.
- `return/`: the files of the return package of G-C2.2, `c22_return.tar.gz` (SHA-256 `4b40742f0bcb92a2992b9ae3e114500f58b79d39025da1adbf23f44372bb3249`), made on the owner's laptop. They are kept with Unix line endings, with the path of the working folder replaced by `W`, with the operator's name in one message replaced by "the operator", and with words replaced in one comment of a launcher and in one line of the record of incidents; seven files are not kept, and the names of two of them are replaced by placeholders in the lists (`audit/c22_keep.py`; `docs/G-C2.2_verdict.md` lists the differences). `return_files.sha256` gives the hashes of the 268 files as received, `return_kept.sha256` those of the 261 files as kept, `keep_report.json` what was changed and left out, and `return_listing.txt` the archive's listing with numeric owners and with those two names replaced. Of the 261 files as kept this folder holds 120. The other 141, the label files and the prediction files of the three runs, are deposited at Zenodo as one archive, https://doi.org/10.5281/zenodo.24320576; `deposit.json` gives the size and the SHA-256 of the archive and of each file, `audit/c22_deposit.py restore` writes the files back into this folder, and `.gitignore` keeps them out of a commit. The 20 array files of the host check in `return/smoke/` are small and stay here.
- `audit/`: the author's recomputation (`audit/c22_recompute.py`): `regenerate.json`, `records.json`, the folder `fields/` (one file a member), `pairs_judged.json` and `curves.json` (the exact solves), `resolve.json` and `aggregate.json`, with the environments beside them.

**`records/c23/`: the records of gate G-C2.3**
- `before_stamp/`: the reports and the logs of the checks made on the gate's host, the owner's laptop, on 18 November 2026 before the stamp, from a copy of the code that draws nothing of the gate: the host check on a reduced configuration (`c23/smoke.py`); the predictions of G-C2.2's members from the three state files against the prediction files that G-C2.2's runs left (`probes/c23_precheck/repredict.py`); the pilot of the training labels on 32 members of a family seed used before G-C2.1's stamp (`probes/c23_precheck/pilot_labels.py`); and three timings (`probes/c2_timing/`, `probes/f2_cost/`). The files were written on Windows and are stored with Unix line endings; in the logs the path of the working folder was replaced by `W`.

**`records/f1_dry/`: the dry run of gate G-F1** on B-19 and T-19, made before the stamp with `python -m f1 run --dry` and `python -m f1 verdict --dry`: the 14 records in `records/`, the progress log `run.log`, the configuration `config.json` and the verdict tables `numbers.md` and `verdict.json`. `docs/PRESPEC_G-F1.md` says which code it ran.

**`records/G-F1/`: the run of gate G-F1** on B-13 and T-13, from the tagged commit (`prereg-f1`) with `python -m f1 run` and `python -m f1 verdict`: the 14 records in `records/`, the progress log `run.log`, the configuration `config.json` and the verdict tables `numbers.md` and `verdict.json`. `docs/G-F1_verdict.md` gives the verdict and the run record.

**`tests/`: the tests.** From this folder, with the repository one level up:
```bash
FEJEPA_REPO=.. python -m pytest -q -p no:cacheprovider tests
```

**`docs/`: pre-specifications, verdicts and notes**
- `contact_energy_note.md`: the energy objective under frictionless contact.
- G-C1a, the idealised joint model against the joint tests: `PRESPEC_G-C1a.md`, `G-C1a_verdict.md`.
- G-C1a2, the higher-fidelity joint model: `PRESPEC_G-C1a2.md`, `G-C1a2_verdict.md`.
- G-C1b, the T-stubs: `PRESPEC_G-C1b.md`, `G-C1b_verdict.md`, and `G-C1b_addendum_welds.md`, which is not pre-specified.
- G-C1c, the low-moment secants of the published joint curves: `PRESPEC_G-C1c.md`, `G-C1c_reading.md`.
- `source_GiraoCoelho2006.md`: the authors' own finite element model of the T-stubs.
- `C1.3_preparation_note.md`, `C1.3_data_design.md`: exploratory checks before stage C1.3.
- `element_study_note.md`: an exploratory check after G-C1.3 of the element kind, the mesh and the integration rule.
- G-C1.3, the training gate: `PRESPEC_G-C1.3.md`, with its stamped code in `G-C1.3_stamped_code/` and the hashes in `G-C1.3_code.sha256`; `G-C1.3_verdict.md`.
- G-C2.1, the plastic training gate: `PRESPEC_G-C2.1.md`, with its stamped code in `G-C2.1_stamped_code/` and the hashes in `G-C2.1_code.sha256`; `G-C2.1_verdict.md`.
- G-C2.2, the second plastic training gate: `PRESPEC_G-C2.2.md`, with the stamped copy of its new code in `G-C2.2_stamped_code/` and the hashes of all its code in `G-C2.2_code.sha256`, and `G-C2.2_verdict.md`.
- G-C2.3, the self-check and the comparison with supervised training: `PRESPEC_G-C2.3.md`, with the stamped copy of its new code in `G-C2.3_stamped_code/` and the hashes of all its code in `G-C2.3_code.sha256`. It has not been run yet.
- G-F1, the CHS splices: `PRESPEC_G-F1.md`, with its stamped code in `G-F1_stamped_code/` and the hashes of its code and data in `G-F1_code.sha256`; `G-F1_verdict.md`.
- The files ending in `_text.md` and `_numbers.md` are the parts from which the verdicts of G-C1a, G-C1a2, G-C1b with its addendum, G-C1.3 and G-C2.1 are assembled. The verdicts of G-F1 and G-C2.2 are single files; the part "Numbers" of G-C2.2's is written by `audit/c22_write_verdict.py`.
- `F2_preparation_note.md`: exploratory preparation for a surrogate gate on the CHS splices, after G-F1 (8 November 2026). It is not a gate and nothing in it was pre-specified.
- `reviews/`: the independent reviews and audits, as delivered. The reviewer was a separate agent that wrote none of the code. They cover G-C2.1 before its stamp (`review_reports_G-C2.1_2026-11-06.md`) and its verdict (`audit_reports_G-C2.1_2026-11-08.md`), G-F1 before its tag (`review_reports_G-F1_2026-11-07.md`), its run and verdict (`audit_report_G-F1_run_2026-11-07.md`), its exploratory runs (`review_report_G-F1_explore_2026-11-08.md`), the code, pre-specification and runbook of G-C2.2 before its stamp (`review_report_G-C2.2_2026-11-12.md`) and its verdict (`audit_report_G-C2.2_2026-11-15.md`), and the code, pre-specification and runbook of G-C2.3 before its stamp (`review_report_G-C2.3_2026-11-18.md`). Only the headers, which the author wrote, were edited for this folder: a note's title is given in English and a path is shortened. The file of G-C2.2's stamp holds three rounds; the author's notes on what was done stand between them and are marked as the author's, and the paths of the working machine are shortened in the reports. The file of G-C2.2's verdict holds the auditor's reports of its rounds, each followed by the author's notes on what was done. The file of G-C2.3's stamp holds its rounds in the same way, and a list of what the later drafts of its pre-specification add to the first.

**`probes/`: exploratory probes.** None of them is a gate. `probes/elements/` holds the scripts of the element study. `probes/c2_bj1997.py`, `c2_bj1997_compare.py`, `c2_bj1997_digitise.py` and `c2_bj1997_fig10.json` run the reference model of stage C2 on Bursi and Jaspart's T1 and compare it with their test and simulations; `probes/c2_pilot/` holds the CPU pilots of G-C2.1 and their records. `probes/c2_diag/` holds the diagnostics made after G-C2.1's verdict (9 and 10 November 2026): why its seed 0 did not train (`RESULTS.md`), the collapses of two replays branched with three remedies (`BRANCHES.md`), and the host's final states (`HOST_STATES.md`). `probes/c2_dev/` holds the development work that followed (10 to 13 November 2026): the tail of G-C2.1 read again, the stability recipe in short runs and in two runs of full length, and the condensed reading (`README.md`, with the scripts and the small records). Neither changes G-C2.1's verdict; `docs/PRESPEC_G-C2.2.md` says what of them was seen before its stamp. `probes/c2_selfcheck/` holds the readings of G-C2.2's records made after its verdict (17 and 18 November 2026): where the error is large, and four quantities that need no reference solution, among them the spread of the force over the three training runs (`README.md`, the scripts as they were run, and their outputs in `records/`); gate G-C2.3 was designed after them, and `docs/PRESPEC_G-C2.3.md` says what of them was seen before its stamp. `probes/c23_precheck/` holds two checks made on the host before G-C2.3's stamp, which draw nothing of the gate: `repredict.py` predicts G-C2.2's members again from the three state files and compares the fields with the prediction files that G-C2.2's runs left, so that the gate's identity check is not first met after its sample has been drawn; `pilot_labels.py` solves members of a family seed used before G-C2.1's stamp at the eight levels of the supervised arm's labels, on the gate's mesh. `probes/c2_timing/` holds two timing scripts for a host: `step_cost.py`, the seconds of a training step with the energy and with the supervised loss, and `time_curve.py`, the surrogate's prediction of a seven-level curve against the reference solve of the same curve. `probes/f1_explore/` holds the exploratory runs made after G-F1's verdict, to a plan hashed before they ran (`EXPLORE_PLAN.md`, `PLAN_HASH.txt`): E1, the mesh and C3; E2, one preload value in every bolt; E3, both splice bounds up to 0.01 rad of rotation, with elastic-plastic bolts. It holds the driver `explore.py`, the records, `run.log`, the tables `RESULTS.md` and `ADDENDUM.md`, written after the results from an independent review. G-F1's verdict is unchanged by them. `probes/f2_dev/` holds the development paths of thirteen members of the CHS family chosen by hand, none drawn with a seed (`dev_paths.py`, records in `records/`), their readings (`analyse.py`, `analysis.json`), the fit of the loading range (`fit_loading.py`, `fit_loading.json`, `fit_loading_holdout_X3.json`), the cost of the training energy (`energy_cost.py`, `energy_cost.json`) and the log of a run of `tests/test_f2.py` (`test_f2_final.log`); `docs/F2_preparation_note.md` reports them. `probes/f2_cost/energy_cost.py` times the same training energy on the host of a gate, on the family's mesh, with the memory it takes on the device.

## Status on 18 November 2026

| Gate | Result |
|---|---|
| G-C1a | FAIL: the idealised model is 2.05 to 2.99 times stiffer than the joint tests |
| G-C1a2 | FAIL: the higher-fidelity model is 2.11 to 3.04 times stiffer |
| G-C1b | PASS, narrowly: the T-stub model is 1.10 times the T-stub tests in the geometric mean |
| G-C1c | Reading of the published curves at low moments |
| G-C1.3 | PASS: on unseen layouts of the family, label-free training reproduced the reference model, not the joint tests: its initial stiffness (median error 0.29%) and its contact zone (median overlap 0.944). The reference model itself is 2 to 3 times stiffer than the joint tests (G-C1a). |
| G-C2.1 | FAIL on both criteria: at this budget, label-free training did not reproduce the reference model's plastic force-deformation curve on unseen T-stubs of the family within these limits. In the median over three seeds the distance from the curve was 6.6% (C1: at most 5%) and its 90th percentile 31% (C2: at most 10%). One seed did not train; the two that did reached 6.6% and 2.4% in the median, 31% and 19% at the 90th percentile. |
| G-C2.2 | PASS: with a stability recipe in the training, and the force read after one amplitude of the field has been set by minimising the energy (the condensed reading), label-free training reproduced the reference model's plastic force-deformation curve on 64 fresh T-stubs of the family. In the median over three seeds the distance from the curve was 0.80% (C1: at most 5%) and its 90th percentile 3.66% (C2: at most 10%). Read without the condensation, the same three models give 1.36% and 10.54%, which would miss C2. No seed collapsed. In each seed 5 or 6 of the 448 pairs remain above 10%; over the three seeds they are eight member and level pairs of five members with a yield stress below 300 MPa, the worst at 50% to 69%. This compares the network with the reference model (5 mm mesh, small strains, frictionless contact, deformation theory under monotonic loading), not with the T-stub tests, and it does not show which of the two changes is needed. |
| G-C2.3 | Stamped on 18 November 2026; not yet run. On a third held-out sample it asks two further questions: whether the spread of the predicted force over the three label-free networks of G-C2.2 flags their large errors, with a threshold fixed in advance, and how close to the reference model the same network comes when it is trained on reference solutions at equal budget. |
| G-F1 | FAIL: of the three criteria, C1 (moment at 0.001 rad) and C2 (axial displacement at 800 kN) lie between the frictionless and no-slip bounds; C3 (bolt 1's force increase from 25 to 100 kNm) lies above the frictionless bound |

After G-C2.1's verdict, exploratory work (`probes/c2_diag/` and `probes/c2_dev/`, 9 to 13 November 2026) found the following. None of it is a gate, and every reading was made on G-C2.1's held-out members, which the choices of method had seen:
- In G-C2.1's seed 0 the loss rose to that of the starting field in the eighth epoch and stayed there. In its final state the latents do not vary between the nodes, and the first layers of its decoder and head are dead.
- With AdamW's second-moment coefficient at 0.99 and a cap on the encoder's gradient, two seeds ran the whole schedule on a laptop GPU without a collapse.
- The tail of G-C2.1 is an error of the end displacement, magnified where a member is weak against the spring. A reading that sets one amplitude of the field by minimising the energy removes much of it.
- As G-C2.1 read them, the two full-length models have medians of 1.42% and 1.55% and 90th percentiles of 7.27% and 8.03%; in the condensed reading, 0.84% and 0.95%, and 3.00% and 3.22%.

After G-F1's verdict, exploratory runs (`probes/f1_explore/`, 8 November 2026) found the following:
- Between 0.005 and 0.01 rad of rotation the frictionless bound lies 3% to 8% below the tests of B-13 and B-19, and the no-slip bound 37% to 66% above them.
- The medium mesh raises C3's frictionless value by 1.4 kN, to 50.97 kN.
- With one preload value in every bolt, C3 holds at 111.5 kN and at 100 kN. Read linearly between the computed values, it would have held up to about 120 kN, 4% below the nominal 125 kN (about 118.5 kN with elastic-plastic bolts, `ADDENDUM.md`).

The preparation for a surrogate gate on the CHS splices (`f2/`, `probes/f2_dev/`, `docs/F2_preparation_note.md`, 8 November 2026) is exploratory and pre-specifies nothing.

The gap of G-C1a is not a discretisation effect: the five element kinds that do not lock converge to the same stiffness, and on the C1.3 mesh the current element is about 1% stiffer than it, up to 2.7% for FS1 depending on two nodes just outside the washer patches (`docs/element_study_note.md`, exploratory, 16 October 2026).

## Not in this folder

- The run scripts and audit records of gates G-C1a to G-C1c, which the verdicts cite as `checks/...`. They are kept with the project owner's records.
- The papers, and the page image of Bursi and Jaspart (1997) that `probes/c2_bj1997_digitise.py` reads.
- The instance files and training labels of G-C1.3, the predictions of its supervised arms and its model states, which were left on the GPU host. `audit/c13_recompute.py` regenerates the held-out and tested instances.
- The instance files and training labels of G-C2.1, and its model states, which were left on the GPU host. `audit/c2_recompute.py` regenerates the instances.
- The instance files and model states of G-C2.2, which stay on the owner's laptop, and seven files of its return package (`records/c22/keep_report.json`); the owner keeps the model states, the seven files and the package as received outside the repository. `audit/c22_recompute.py` regenerates the instances.
- The 141 label and prediction files of G-C2.2's return package, which are deposited at Zenodo, https://doi.org/10.5281/zenodo.24320576 (`records/c22/deposit.json`).
- The model states, fields, predictions and most step records of the development runs of `probes/c2_dev/`, which stay on the owner's laptop. Its `README.md` lists what is kept.
- The logs of the C1.3 cost probes.
- The data cache of the two-dimensional probe, `probes/c13_net/data_cache.npz`; `net_probe.py` rebuilds it on its first run.
- The outputs of the independent audit scripts of G-C2.1 and of G-C2.2; the reports in `docs/reviews/` give their results.
- The scripts of the independent review of the element study. `probes/elements/review_checks.py` reproduces the three of its checks that the note cites.

**Notes on the probes**
- `probes/c13_scale.py`, `gc1b_weld_bracket.py` and `gc1b_weld_bracket_tables.py` read files in `checks/`, so they do not run from this folder alone.
- `probes/c13_segment_effect.json` has no script. A one-off command solved FS1 to FS4 with `fejoint.joint.analyse` under G-C1a's options, on the 10 mm mesh with one layer, with the full beam and with segments of 300 mm and 400 mm. FS4 with the 300 mm segment was recomputed on 10 October 2026 and matched to every digit.
- In `probes/c13_cost/pilot_energy.json` and `pilot_supervised.json`, the local path of the repository checkout was replaced by its branch and commit. Nothing else in them was changed.

## Licence

The repository's licences cover this folder as they cover the rest (see the repository's README):
- the code (`fejoint/`, `c13/`, `c2/`, `c22/`, `c23/`, `f1/` with its scripts in `f1/digitise/`, `f2/`, `audit/`, `tests/`, the scripts in `probes/` and the stamped copies in `docs/G-C1.3_stamped_code/`, `docs/G-C2.1_stamped_code/`, `docs/G-C2.2_stamped_code/`, `docs/G-C2.3_stamped_code/` and `docs/G-F1_stamped_code/`) under the PolyForm Noncommercial License 1.0.0 (`../LICENSE`);
- the pre-specifications, verdicts and notes in `docs/`, `RUNBOOK_C13.md` with its addendum, `RUNBOOK_C2.md`, `RUNBOOK_C22.md`, `RUNBOOK_C23.md`, the records in `probes/` (the `.json`, `.jsonl`, `.npz`, `.log`, `.csv` and `.txt` files, the plan, the results tables and the addendum of `probes/f1_explore/`, and the notes of `probes/c2_diag/`, `probes/c2_dev/` and `probes/c2_selfcheck/`) and those in `records/c13/`, `records/elements/`, `records/c2/`, `records/c22/`, `records/c23/`, `records/f1_dry/` and `records/G-F1/` under the Creative Commons Attribution 4.0 International licence (`../LICENSE-CC-BY-4.0`), as the repository's pre-registration documents and records are;
- the digitised data in `f1/data/` likewise; they are readings of the figures of Fidalgo (2023), which is the source to cite for the measurements.

## References

- Bursi, O.S., Jaspart, J.P. (1997). Benchmarks for finite element modelling of bolted steel connections. *Journal of Constructional Steel Research* 43(1-3), 17-42. doi:10.1016/S0143-974X(97)00031-X
- Fidalgo, A.M. (2023). *Bolted CHS flange-plate connections under tension, bending and combined loads.* PhD thesis, University of Toronto.
- Fidalgo, A., Packer, J.A. (2023). Bolted CHS flange-plate connections under bending. *Journal of Structural Engineering* 149(6), 04023066. doi:10.1061/JSENDH.STENG-12059
- Girão Coelho, A.M., Bijlaard, F.S.K., Simões da Silva, L. (2004). Experimental assessment of the ductility of extended end plate connections. *Engineering Structures* 26(9), 1185-1206. doi:10.1016/j.engstruct.2000.09.001
