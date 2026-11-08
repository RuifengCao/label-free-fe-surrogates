# Extended end plate joints (stage C)

This folder holds the work towards a label-free surrogate for the extended end plate joints tested by Girão Coelho, Bijlaard and Simões da Silva (2004). It contains the finite element models, the gates that tested them against the experiments, the pre-registered training gate G-C1.3 with its records and verdict, and the plastic stage C2 on bolted T-stubs with its training gate G-C2.1, its records and verdict. It also holds the first tubular case: bolted circular hollow section (CHS) blank flange-plate splices tested by Fidalgo (2023), with gate G-F1.

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

**`f1/`: the run code of gate G-F1**, the CHS splices of Fidalgo (2023) against their tests, with frictionless and no-slip splices as bounds. `python -m f1 -h` lists its commands; `docs/PRESPEC_G-F1.md` gives the run. `f1/data/` holds the test curves, bolt forces and coupon curves digitised from the thesis's figures, and `f1/digitise/` the scripts that reproduce every data file from the thesis PDF.

**`f2/`: draft code for a surrogate gate on the CHS splices**, provisionally G-F2, not under any stamp: the family of splices (`family.py`), the spring-loaded export with preload (`instance.py`), the data (`data.py`), the configuration (`config.py`) and the energy in torch (`torch_energy.py`). `docs/F2_preparation_note.md` describes it; `tests/test_f2.py` checks it.

**`audit/`: the audit scripts of G-C1.3 and G-C2.1**, written after each run and not under the stamp
- `c13_recompute.py`: regenerates the held-out and tested instances of G-C1.3, re-solves seven of them, and recomputes every metric of the label-free arm from the returned predictions and labels.
- `c13_write_verdict.py`: the tables of G-C1.3's verdict, from the records.
- `c2_recompute.py`: regenerates all 580 instances of G-C2.1, recomputes every metric of the label-free arm on the held-out and tested members from the returned predictions and labels, and re-solves four members.
- `c2_write_verdict.py`: the tables of G-C2.1's verdict, from the records.
- `independent/G-C2.1/`: the scripts of the independent audit of G-C2.1's verdict, written by the auditor without importing the author's audit scripts: `audit_records.py` (labels, ledger, histories, predictions and criteria from the records), `regen.py` (instances regenerated and compared with the manifest), `reeval.py` (held-out pairs re-evaluated with the stamped code), `preds_constraints.py`, `draft_numbers.py` and `round2_checks.py`. Its reports are in `docs/reviews/`.

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
- G-F1, the CHS splices: `PRESPEC_G-F1.md`, with its stamped code in `G-F1_stamped_code/` and the hashes of its code and data in `G-F1_code.sha256`; `G-F1_verdict.md`.
- The files ending in `_text.md` and `_numbers.md` are the parts each verdict is assembled from.
- `F2_preparation_note.md`: exploratory preparation for a surrogate gate on the CHS splices, after G-F1 (8 November 2026). It is not a gate and nothing in it was pre-specified.
- `reviews/`: the independent reviews and audits, as delivered. The reviewer was a separate agent that wrote none of the code. They cover G-C2.1 before its stamp (`review_reports_G-C2.1_2026-11-06.md`) and its verdict (`audit_reports_G-C2.1_2026-11-08.md`), G-F1 before its tag (`review_reports_G-F1_2026-11-07.md`), its run and verdict (`audit_report_G-F1_run_2026-11-07.md`), and its exploratory runs (`review_report_G-F1_explore_2026-11-08.md`). Only the headers, which the author wrote, were edited for this folder: a note's title is given in English and a path is shortened.

**`probes/`: exploratory probes.** None of them is a gate. `probes/elements/` holds the scripts of the element study. `probes/c2_bj1997.py`, `c2_bj1997_compare.py`, `c2_bj1997_digitise.py` and `c2_bj1997_fig10.json` run the reference model of stage C2 on Bursi and Jaspart's T1 and compare it with their test and simulations; `probes/c2_pilot/` holds the CPU pilots of G-C2.1 and their records. `probes/f1_explore/` holds the exploratory runs made after G-F1's verdict, to a plan hashed before they ran (`EXPLORE_PLAN.md`, `PLAN_HASH.txt`): E1, the mesh and C3; E2, one preload value in every bolt; E3, both splice bounds up to 0.01 rad of rotation, with elastic-plastic bolts. It holds the driver `explore.py`, the records, `run.log`, the tables `RESULTS.md` and `ADDENDUM.md`, written after the results from an independent review. G-F1's verdict is unchanged by them. `probes/f2_dev/` holds the development paths of thirteen members of the CHS family chosen by hand, none drawn with a seed (`dev_paths.py`, records in `records/`), their readings (`analyse.py`, `analysis.json`), the fit of the loading range (`fit_loading.py`, `fit_loading.json`, `fit_loading_holdout_X3.json`), the cost of the training energy (`energy_cost.py`, `energy_cost.json`) and the log of a run of `tests/test_f2.py` (`test_f2_final.log`); `docs/F2_preparation_note.md` reports them.

## Status on 8 November 2026

| Gate | Result |
|---|---|
| G-C1a | FAIL: the idealised model is 2.05 to 2.99 times stiffer than the joint tests |
| G-C1a2 | FAIL: the higher-fidelity model is 2.11 to 3.04 times stiffer |
| G-C1b | PASS, narrowly: the T-stub model is 1.10 times the T-stub tests in the geometric mean |
| G-C1c | Reading of the published curves at low moments |
| G-C1.3 | PASS: on unseen layouts of the family, label-free training reproduced the reference model, not the joint tests: its initial stiffness (median error 0.29%) and its contact zone (median overlap 0.944). The reference model itself is 2 to 3 times stiffer than the joint tests (G-C1a). |
| G-C2.1 | FAIL on both criteria: at this budget, label-free training did not reproduce the reference model's plastic force-deformation curve on unseen T-stubs of the family within these limits. In the median over three seeds the distance from the curve was 6.6% (C1: at most 5%) and its 90th percentile 31% (C2: at most 10%). One seed did not train; the two that did reached 6.6% and 2.4% in the median, 31% and 19% at the 90th percentile. |
| G-F1 | FAIL: of the three criteria, C1 (moment at 0.001 rad) and C2 (axial displacement at 800 kN) lie between the frictionless and no-slip bounds; C3 (bolt 1's force increase from 25 to 100 kNm) lies above the frictionless bound |

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
- The logs of the C1.3 cost probes.
- The data cache of the two-dimensional probe, `probes/c13_net/data_cache.npz`; `net_probe.py` rebuilds it on its first run.
- The outputs of the independent audit scripts of G-C2.1; its reports in `docs/reviews/` give their results.
- The scripts of the independent review of the element study. `probes/elements/review_checks.py` reproduces the three of its checks that the note cites.

**Notes on the probes**
- `probes/c13_scale.py`, `gc1b_weld_bracket.py` and `gc1b_weld_bracket_tables.py` read files in `checks/`, so they do not run from this folder alone.
- `probes/c13_segment_effect.json` has no script. A one-off command solved FS1 to FS4 with `fejoint.joint.analyse` under G-C1a's options, on the 10 mm mesh with one layer, with the full beam and with segments of 300 mm and 400 mm. FS4 with the 300 mm segment was recomputed on 10 October 2026 and matched to every digit.
- In `probes/c13_cost/pilot_energy.json` and `pilot_supervised.json`, the local path of the repository checkout was replaced by its branch and commit. Nothing else in them was changed.

## Licence

The repository's licences cover this folder as they cover the rest (see the repository's README):
- the code (`fejoint/`, `c13/`, `c2/`, `f1/` with its scripts in `f1/digitise/`, `f2/`, `audit/`, `tests/`, the scripts in `probes/` and the stamped copies in `docs/G-C1.3_stamped_code/`, `docs/G-C2.1_stamped_code/` and `docs/G-F1_stamped_code/`) under the PolyForm Noncommercial License 1.0.0 (`../LICENSE`);
- the pre-specifications, verdicts and notes in `docs/`, `RUNBOOK_C13.md` with its addendum, `RUNBOOK_C2.md`, the records in `probes/` (the `.json`, `.log` and `.txt` files, and the plan, the results tables and the addendum of `probes/f1_explore/`) and those in `records/c13/`, `records/elements/`, `records/c2/`, `records/f1_dry/` and `records/G-F1/` under the Creative Commons Attribution 4.0 International licence (`../LICENSE-CC-BY-4.0`), as the repository's pre-registration documents and records are;
- the digitised data in `f1/data/` likewise; they are readings of the figures of Fidalgo (2023), which is the source to cite for the measurements.

## References

- Bursi, O.S., Jaspart, J.P. (1997). Benchmarks for finite element modelling of bolted steel connections. *Journal of Constructional Steel Research* 43(1-3), 17-42. doi:10.1016/S0143-974X(97)00031-X
- Fidalgo, A.M. (2023). *Bolted CHS flange-plate connections under tension, bending and combined loads.* PhD thesis, University of Toronto.
- Fidalgo, A., Packer, J.A. (2023). Bolted CHS flange-plate connections under bending. *Journal of Structural Engineering* 149(6), 04023066. doi:10.1061/JSENDH.STENG-12059
- Girão Coelho, A.M., Bijlaard, F.S.K., Simões da Silva, L. (2004). Experimental assessment of the ductility of extended end plate connections. *Engineering Structures* 26(9), 1185-1206. doi:10.1016/j.engstruct.2000.09.001
