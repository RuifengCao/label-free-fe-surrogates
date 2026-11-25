# Probes on the closed-joint plateau of the CHS surrogate (development, 21 November 2026)

Exploratory. Nothing here is stamped or pre-specified. All runs were on one member (`tested_B-13_nominal`) on the
tiny mesh, with the reference code in double precision unless a script says otherwise.

Every script takes the `joint` directory, a data directory (`inst/`, `pre/`, `labels/`) and a member id:

    python3 -I SCRIPT.py JOINT_DIR DATA_DIR MEMBER [more]

| script | question |
|---|---|
| `precond_probe.py` | Starting from the preload state, how fast do iterations on the field itself reach the reference, with and without the elastic stiffness as a preconditioner? (`... LAM OUT.json [ITERS]`) |
| `check_step.py` | Does the elastic contact step of `f2/precond.py` equal the reference's Signorini sub-solver with the same matrix, and what does it cost? |
| `modal_probe.py` | How much of the step beyond the closed-joint state lies in the softest modes of the stiffness with the splice plane free? |
| `device_modes.py` | Softest eigenvalues with the loading device's unknowns free or held, and with the contacts free or held. |
| `grad_precision.py` | Does the single-precision gradient used in training give the same step as the double-precision gradient? (`... [RUN_DIR ...]` adds the fields of saved runs) |
| `descent_from_elastic.py` | From the elastic contact solution of a level, how fast do modified Newton steps and Jacobi-scaled projected gradient steps close what plasticity leaves? (`... LAM ITERS`) |
| `check_elastic_target.py` | The elastic contact solution at the label's levels against the labels; the elastic-solution loss at the target and at zero. |
| `transfer_probe.py` | The fields that a saved run gives for one member on the mesh it was trained on and on another mesh, each against its own labels (`JOINT_DIR STATE.pt MEMBER DATA_DIR [DATA_DIR ...]`). |
| `condensed_preview.py` | The raw and the amplitude-condensed readings of a saved run for one member on one or more meshes; writes the fields (`JOINT_DIR STATE.pt MEMBER OUT_PREFIX DATA_DIR [DATA_DIR ...]`). |
| `onestep_reading.py` | Those fields followed by a few elastic contact steps, read against the labels (`JOINT_DIR DATA_DIR MEMBER FIELDS.npz [STEPS]`). |
| `compare.py` | Snapshots of development runs against the member's labels (`DATA_DIR MEMBER RUN_DIR ...`; no `JOINT_DIR`). |

`precond_lam1.log` and `precond_lam1.json` are the output of `precond_probe.py` at the top level (LAM 1).
