"""Development configurations of the CHS surrogate: exploratory runs, not a gate. Nothing here is stamped, and the
members drawn here are seen: a later gate must list TRAIN_SEED and EVAL_SEED among the seeds used before its stamp.

A configuration is the draft of f2/config.py with the sections that the draft leaves open (the network, the map,
the training, the readings) filled in for development, and with a development sample:

    train    members drawn with TRAIN_SEED (label-free: exported, never solved beyond their preload);
    eval     members drawn with EVAL_SEED (random held-out members of the development);
    dev      the eleven hand-picked development members of probes/f2_dev that are not tested members;
    tested   B-13 and B-19 at the nominal and the measured preload (f2.family.TESTED).

All presets share the family and the data sections, so that one data directory serves them all (the data carry the
hash of these two sections only, f2.data.data_sha256).
"""
from __future__ import annotations

import copy

from . import config as base
from .config import canonical, sha256  # noqa: F401

TRAIN_SEED, EVAL_SEED = 20261120, 20261121
N_TRAIN, N_EVAL = 128, 16
EXTRA_SEED = 20261124                  # the extra training members of the presets that have them (seen, like the others)

# probes/f2_dev/dev_paths.py without B-13 and B-19 (these are tested members)
DEV_MEMBERS = {
    "W1": {"tp": 10.0, "e1": 75.0, "e2": 55.0, "fy": 345.0, "Np": 60.0},
    "W2": {"tp": 10.0, "e1": 55.0, "e2": 75.0, "fy": 345.0, "Np": 130.0},
    "S1": {"tp": 25.0, "e1": 55.0, "e2": 75.0, "fy": 460.0, "Np": 130.0},
    "S2": {"tp": 25.0, "e1": 75.0, "e2": 55.0, "fy": 460.0, "Np": 60.0},
    "C": {"tp": 17.5, "e1": 65.0, "e2": 65.0, "fy": 402.5, "Np": 95.0},
    "T10hi": {"tp": 10.0, "e1": 65.0, "e2": 65.0, "fy": 460.0, "Np": 95.0},
    "T25lo": {"tp": 25.0, "e1": 65.0, "e2": 65.0, "fy": 345.0, "Np": 95.0},
    "X1": {"tp": 17.5, "e1": 55.0, "e2": 55.0, "fy": 402.5, "Np": 130.0},
    "X2": {"tp": 17.5, "e1": 75.0, "e2": 55.0, "fy": 402.5, "Np": 60.0},
    "X3": {"tp": 17.5, "e1": 55.0, "e2": 75.0, "fy": 402.5, "Np": 60.0},
    "X4": {"tp": 17.5, "e1": 75.0, "e2": 75.0, "fy": 402.5, "Np": 130.0},
}

# name -> what differs from the defaults below
PRESETS = {
    # one tested member, to compare ways of building the field (the lift) before a family run
    **{f"one_{k}": {"members": ["tested_B-13_nominal"], "epochs": 600, "lift": k,
                    "evaluated": ["tested_B-13_nominal"], "snapshot_epochs": [50, 100, 200, 300, 400, 500, 600]}
       for k in ("bending", "rigid", "beam", "v", "none")},
    # the same on the tiny mesh (run with --mesh tiny and its own data directory): cheap steps, to compare lifts
    **{f"tiny_{k}": {"members": ["tested_B-13_nominal"], "epochs": 2000, "lift": k,
                     "evaluated": ["tested_B-13_nominal"], "snapshot_epochs": list(range(250, 2001, 250))}
       for k in ("bending", "rigid", "frame", "hinge")},
    # the tiny single-member runs with the opening pull let through the contact map (f2.model.open_gate), and a
    # control with the same early readings; "cpu_*": two fields a step, for a short comparison on a processor
    **{f"tiny_{k}_open": {"members": ["tested_B-13_nominal"], "epochs": 2000, "lift": k, "map": "softplus_open",
                          "evaluated": ["tested_B-13_nominal"],
                          "snapshot_epochs": [25, 50, 100, 150] + list(range(250, 2001, 250))}
       for k in ("bending", "frame", "hinge")},
    "tiny_frame_early": {"members": ["tested_B-13_nominal"], "epochs": 2000, "lift": "frame",
                         "evaluated": ["tested_B-13_nominal"],
                         "snapshot_epochs": [25, 50, 100, 150] + list(range(250, 2001, 250))},
    **{f"cpu_frame{tag}": {"members": ["tested_B-13_nominal"], "epochs": 2000, "lift": "frame", "map": kind,
                           "fields_per_step": 2, "evaluated": ["tested_B-13_nominal"],
                           "snapshot_epochs": [10, 25, 50, 75, 100, 150, 200, 300, 400]}
       for tag, kind in (("", "softplus"), ("_open", "softplus_open"))},
    # the loss against the member's own elastic contact step (f2/precond.py) in place of the energy
    "cpu_frame_step": {"members": ["tested_B-13_nominal"], "epochs": 2000, "lift": "frame",
                       "loss": "elastic_contact_step", "fields_per_step": 2, "evaluated": ["tested_B-13_nominal"],
                       "snapshot_epochs": [10, 25, 50, 75, 100, 150, 200, 300, 400]},
    # the same over a whole short schedule (the rate falls to zero by step 400), and the energy loss started from
    # the weights of a step-loss run (train --init-from)
    "cpu_frame_step_e400": {"members": ["tested_B-13_nominal"], "epochs": 400, "lift": "frame",
                            "loss": "elastic_contact_step", "fields_per_step": 2,
                            "evaluated": ["tested_B-13_nominal"],
                            "snapshot_epochs": [10, 25, 50, 100, 150, 200, 250, 300, 350, 400]},
    "cpu_frame_step_lr1e4": {"members": ["tested_B-13_nominal"], "epochs": 400, "lift": "frame", "lr": 1e-4,
                             "loss": "elastic_contact_step", "fields_per_step": 2,
                             "evaluated": ["tested_B-13_nominal"],
                             "snapshot_epochs": [0, 10, 25, 50, 100, 150, 200, 250, 300, 350, 400]},
    "cpu_frame_both_w01_lr1e4": {"members": ["tested_B-13_nominal"], "epochs": 400, "lift": "frame", "lr": 1e-4,
                                 "loss": "energy_and_step", "step_weight": 0.1, "fields_per_step": 2,
                                 "evaluated": ["tested_B-13_nominal"],
                                 "snapshot_epochs": [0, 10, 25, 50, 100, 150, 200, 250, 300, 350, 400]},
    "cpu_frame_polish": {"members": ["tested_B-13_nominal"], "epochs": 400, "lift": "frame", "fields_per_step": 2,
                         "evaluated": ["tested_B-13_nominal"],
                         "snapshot_epochs": [0, 5, 10, 25, 50, 75, 100, 150, 200, 300, 400]},
    # two phases: the fit to the member's elastic contact solutions (a target that does not depend on the field),
    # then the energy loss from those weights at a lower rate (train --init-from)
    "cpu_frame_elastic_e300": {"members": ["tested_B-13_nominal"], "epochs": 300, "lift": "frame",
                               "loss": "elastic_solution", "fields_per_step": 2,
                               "evaluated": ["tested_B-13_nominal"],
                               "snapshot_epochs": [10, 25, 50, 100, 150, 200, 250, 300]},
    "cpu_frame_energy_lr1e4": {"members": ["tested_B-13_nominal"], "epochs": 300, "lift": "frame", "lr": 1e-4,
                               "fields_per_step": 2, "evaluated": ["tested_B-13_nominal"],
                               "snapshot_epochs": [0, 5, 10, 25, 50, 100, 150, 200, 250, 300]},
    # the energy loss with an anchor: at the levels up to anchor_max_level of the device range, where the member is
    # elastic, the fit to its elastic contact solution is added (a target that does not depend on the field)
    **{f"cpu_frame_anchor{tag}": {"members": ["tested_B-13_nominal"], "epochs": 400, "lift": "frame",
                                  "loss": "energy_and_elastic", "step_weight": w, "anchor_max_level": 0.375,
                                  "fields_per_step": 2, "evaluated": ["tested_B-13_nominal"],
                                  "snapshot_epochs": [10, 25, 50, 75, 100, 150, 200, 250, 300, 350, 400]}
       for tag, w in (("_w01", 0.1), ("_w1", 1.0), ("_w001", 0.01))},
    # the same anchor on the contact unknowns only (the gaps of the elastic solution)
    **{f"cpu_frame_gaps{tag}": {"members": ["tested_B-13_nominal"], "epochs": 400, "lift": "frame",
                                "loss": "energy_and_elastic", "step_weight": w, "anchor_max_level": 0.375,
                                "anchor_on": "contact", "fields_per_step": 2, "evaluated": ["tested_B-13_nominal"],
                                "snapshot_epochs": [10, 25, 50, 75, 100, 150, 200, 250, 300, 350, 400]}
       for tag, w in (("_w1", 1.0), ("_w10", 10.0), ("_w100", 100.0))},
    "cpu_none_step": {"members": ["tested_B-13_nominal"], "epochs": 2000, "lift": "none",
                      "loss": "elastic_contact_step", "fields_per_step": 2, "evaluated": ["tested_B-13_nominal"],
                      "snapshot_epochs": [10, 25, 50, 75, 100, 150, 200, 300, 400]},
    **{f"cpu_frame_both{tag}": {"members": ["tested_B-13_nominal"], "epochs": 2000, "lift": "frame",
                                "loss": "energy_and_step", "step_weight": w, "fields_per_step": 2,
                                "evaluated": ["tested_B-13_nominal"],
                                "snapshot_epochs": [10, 25, 50, 75, 100, 150, 200, 300, 400]}
       for tag, w in (("_w01", 0.1), ("_w1", 1.0), ("_w001", 0.01))},
    **{f"cpu_{k}_contact{tag}": {"members": ["tested_B-13_nominal"], "epochs": 2000, "lift": k,
                                 "loss": "energy_and_contact_step", "step_weight": w, "fields_per_step": 2,
                                 "evaluated": ["tested_B-13_nominal"],
                                 "snapshot_epochs": [10, 25, 50, 75, 100, 150, 200, 300, 400]}
       for k in ("frame", "bending") for tag, w in (("_w01", 0.1), ("_w1", 1.0), ("_w10", 10.0))},
    **{f"tiny_{k}_contact{tag}": {"members": ["tested_B-13_nominal"], "epochs": 2000, "lift": k,
                                  "loss": "energy_and_contact_step", "step_weight": w,
                                  "evaluated": ["tested_B-13_nominal"],
                                  "snapshot_epochs": [25, 50, 100, 150] + list(range(250, 2001, 250))}
       for k in ("frame", "bending") for tag, w in (("_w01", 0.1), ("_w1", 1.0), ("_w10", 10.0))},
    **{f"tiny_frame_both{tag}": {"members": ["tested_B-13_nominal"], "epochs": 2000, "lift": "frame",
                                 "loss": "energy_and_step", "step_weight": w, "evaluated": ["tested_B-13_nominal"],
                                 "snapshot_epochs": [25, 50, 100, 150] + list(range(250, 2001, 250))}
       for tag, w in (("_w01", 0.1), ("_w1", 1.0), ("_w001", 0.01))},
    **{f"tiny_{k}_step": {"members": ["tested_B-13_nominal"], "epochs": 2000, "lift": k,
                          "loss": "elastic_contact_step", "evaluated": ["tested_B-13_nominal"],
                          "snapshot_epochs": [25, 50, 100, 150] + list(range(250, 2001, 250))}
       for k in ("frame", "none")},
    # family runs on the tiny mesh (--mesh tiny): 25,600 steps each, cheap enough to compare lifts at a real budget
    **{f"tfam128_{k}": {"members": ["train", 128], "epochs": 200, "lift": k, "resident_members": 8,
                        "snapshot_epochs": [1, 2, 5, 10, 20, 40, 70, 100, 130, 160, 200]}
       for k in ("bending", "rigid", "frame", "hinge")},
    **{f"tfam128_{k}_open": {"members": ["train", 128], "epochs": 200, "lift": k, "map": "softplus_open",
                             "resident_members": 8,
                             "snapshot_epochs": [1, 2, 5, 10, 20, 40, 70, 100, 130, 160, 200]}
       for k in ("bending", "frame", "hinge")},
    "one_hinge": {"members": ["tested_B-13_nominal"], "epochs": 600, "lift": "hinge",
                  "evaluated": ["tested_B-13_nominal"], "snapshot_epochs": [50, 100, 200, 300, 400, 500, 600]},
    "fam128_hinge": {"members": ["train", 128], "epochs": 100, "lift": "hinge",
                     "snapshot_epochs": [1, 2, 5, 10, 20, 35, 50, 75, 100]},
    "one_frame": {"members": ["tested_B-13_nominal"], "epochs": 600, "lift": "frame",
                  "evaluated": ["tested_B-13_nominal"], "snapshot_epochs": [50, 100, 200, 300, 400, 500, 600]},
    "fam128_frame": {"members": ["train", 128], "epochs": 100, "lift": "frame",
                     "snapshot_epochs": [1, 2, 5, 10, 20, 35, 50, 75, 100]},
    # runs that start from the weights of another run (train --init-from), for example a tiny-mesh run carried on
    # on the family's mesh: a snapshot before the first step, then a short budget
    **{f"one_{k}_ft": {"members": ["tested_B-13_nominal"], "epochs": 600, "lift": k,
                       "evaluated": ["tested_B-13_nominal"], "snapshot_epochs": [0, 25, 50, 100, 200, 300, 400, 600]}
       for k in ("bending", "frame", "hinge")},
    **{f"fam128_{k}_ft": {"members": ["train", 128], "epochs": 40, "lift": k, "resident_members": 8,
                          "snapshot_epochs": [0, 1, 2, 5, 10, 20, 30, 40]}
       for k in ("bending", "frame", "hinge")},
    # carried on on two meshes at once: every step on a member of the family's mesh is followed by three steps on
    # members of the tiny mesh (train --companion), which keep what the weights learnt there; 10 epochs, 5,120 steps
    **{f"fam128_{k}_mix3{tag}": {"members": ["train", 128], "epochs": 10, "lift": k, "lr": lr, "resident_members": 8,
                                 "companion": {"mesh": "tiny", "steps": 3},
                                 "snapshot_epochs": [0, 1, 2, 3, 5, 7, 10]}
       for k in ("bending", "frame", "hinge") for tag, lr in (("_lr1e4", 1e-4), ("_lr3e4", 3e-4))},
    # the same at a tenth of the rate, so that the first steps on the new mesh do not undo what the weights hold
    **{f"fam128_{k}_ft_lr1e4": {"members": ["train", 128], "epochs": 40, "lift": k, "lr": 1e-4, "resident_members": 8,
                                "snapshot_epochs": [0, 1, 2, 5, 10, 20, 30, 40]}
       for k in ("bending", "frame", "hinge")},
    # the first family runs: 12,800 steps, an eighth of G-C2.2's budget
    **{f"fam128_{k}": {"members": ["train", 128], "epochs": 100, "lift": k,
                       "snapshot_epochs": [1, 2, 5, 10, 20, 35, 50, 75, 100]} for k in ("bending", "rigid", "beam")},
    # the family runs of the tiny mesh at their budget, for the family's mesh on a GPU with memory to spare: every
    # training member stays on the device (128 coarse members take about 5 GiB), so no step waits for a member to
    # be built again; "e400" has twice the steps
    **{f"fam128_bending_e{e}": {"members": ["train", 128], "epochs": e, "lift": "bending", "resident_members": 128,
                                "snapshot_epochs": [x for x in (1, 2, 5, 10, 20, 40, 70, 100, 130, 160, 200, 250,
                                                                300, 350, 400) if x <= e]}
       for e in (200, 400)},
    # a second cycle on the tiny mesh, from the final weights of a tfam128 run (train --init-from): the same 200
    # epochs with a fresh warm-up and cosine schedule at a lower peak rate; every training member stays on the device
    "tfam128_bending_more": {"members": ["train", 128], "epochs": 200, "lift": "bending", "lr": 3e-4,
                             "resident_members": 128,
                             "snapshot_epochs": [0, 10, 20, 40, 70, 100, 130, 160, 200]},
    # a second cycle on the family's mesh, from the final weights of a fam128_bending_e400 run (train --init-from):
    # 200 epochs with a fresh warm-up and cosine schedule at the lower peak rate of tfam128_bending_more; two
    # exponential moving averages of the weights are kept, with horizons of about 1,000 and 5,000 steps (8 and 39
    # epochs), read at the snapshots and predicted at the end; every training member stays on the device
    "fam128_bending_more": {"members": ["train", 128], "epochs": 200, "lift": "bending", "lr": 3e-4,
                            "resident_members": 128, "ema": [0.999, 0.9998],
                            "snapshot_epochs": [0, 10, 20, 40, 70, 100, 130, 160, 200]},
    # two changes of that second cycle, each from the same starting weights and with the same 25,600 steps, without
    # the averages (trial of 24 November 2026, probes/f2_stage2/PRESPEC.md): "u" draws the device rotation
    # uniformly between lam_min and 1.15 times the member's device range; "ux" does the same and adds 32 training
    # members with thin plates (tp between 10 and 12.5 mm, the other parameters over the family's ranges), drawn
    # with a seed of their own into a data directory of their own (generate --extra, train --extra-data): 160
    # members and 160 epochs, with the snapshots at the same steps
    "fam128_bending_more_u": {"members": ["train", 128], "epochs": 200, "lift": "bending", "lr": 3e-4,
                              "resident_members": 128, "Theta": {"kind": "uniform", "top": 1.15},
                              "snapshot_epochs": [0, 10, 20, 40, 70, 100, 130, 160, 200]},
    "fam128_bending_more_ux": {"members": ["train", 128], "epochs": 160, "lift": "bending", "lr": 3e-4,
                               "resident_members": 160, "Theta": {"kind": "uniform", "top": 1.15},
                               "extra_members": {"n": 32, "seed": EXTRA_SEED, "ranges": {"tp": [10.0, 12.5]}},
                               "snapshot_epochs": [0, 8, 16, 32, 56, 80, 104, 128, 160]},
    "fam64_bending": {"members": ["train", 64], "epochs": 200, "lift": "bending",
                      "snapshot_epochs": [2, 4, 10, 20, 40, 70, 100, 150, 200]},
    # a correction to a field underneath (train --under-data, --under-state): the finished run of
    # "fam128_bending_e400" on the tiny mesh gives, carried to the family's mesh, the field that the networks'
    # outputs are added to (f2.model.field, f2.train.under_field); otherwise the recipe of "fam128_bending_e400",
    # with 150 epochs (19,200 steps) and a snapshot before the first step
    "fam128_bending_under_e150": {"members": ["train", 128], "epochs": 150, "lift": "bending",
                                  "resident_members": 128, "under": {"preset": "fam128_bending_e400", "mesh": "tiny"},
                                  "snapshot_epochs": [0, 5, 10, 20, 30, 40, 60, 80, 100, 125, 150]},
    # for the tests and dry runs of the code only (tiny mesh, a few steps)
    "dry": {"members": ["train", 2], "epochs": 3, "lift": "bending", "dim": 32, "depth": 2, "heads": 4,
            "snapshot_epochs": [1, 3], "max_evaluations": 4, "evaluated": ["eval_0000", "tested_B-13_nominal"]},
    # a second cycle with two averages of the weights at the size of "dry" (train --init-from a "dry" run)
    "dry_more": {"members": ["train", 2], "epochs": 3, "lift": "bending", "dim": 32, "depth": 2, "heads": 4,
                 "lr": 3e-4, "ema": [0.5, 0.9], "snapshot_epochs": [0, 1, 3], "max_evaluations": 4,
                 "evaluated": ["eval_0000", "tested_B-13_nominal"]},
    # a correction to a field underneath at the size of "dry" (train --under-data, --under-state of a "dry" run)
    "dry_under": {"members": ["train", 2], "epochs": 3, "lift": "bending", "dim": 32, "depth": 2, "heads": 4,
                  "under": {"preset": "dry", "mesh": "tiny"}, "snapshot_epochs": [0, 1, 3], "max_evaluations": 4,
                  "evaluated": ["eval_0000", "tested_B-13_nominal"]},
    # the two changed second cycles at the size of "dry" (train --init-from a "dry" run; "dry_more_ux" with two extra
    # members, generate --extra)
    "dry_more_u": {"members": ["train", 2], "epochs": 3, "lift": "bending", "dim": 32, "depth": 2, "heads": 4,
                   "lr": 3e-4, "Theta": {"kind": "uniform", "top": 1.15}, "snapshot_epochs": [0, 1, 3],
                   "max_evaluations": 4, "evaluated": ["eval_0000", "tested_B-13_nominal"]},
    "dry_more_ux": {"members": ["train", 2], "epochs": 3, "lift": "bending", "dim": 32, "depth": 2, "heads": 4,
                    "lr": 3e-4, "Theta": {"kind": "uniform", "top": 1.15},
                    "extra_members": {"n": 2, "seed": EXTRA_SEED, "ranges": {"tp": [10.0, 12.5]}},
                    "snapshot_epochs": [0, 1, 3], "max_evaluations": 4,
                    "evaluated": ["eval_0000", "tested_B-13_nominal"]},
}


def config(preset: str) -> dict:
    p = PRESETS[preset]
    cfg = copy.deepcopy(base.config())
    cfg["gate"] = "F2 development (exploratory run, not a gate)"
    cfg["preset"] = preset
    d = cfg["data"]
    d["train_seed"], d["eval_seed"], d["n_train"], d["n_eval"] = TRAIN_SEED, EVAL_SEED, N_TRAIN, N_EVAL
    d["dev"] = {k: dict(v) for k, v in DEV_MEMBERS.items()}
    d["n_train_labelled"] = 0                                    # label-free: no training member is solved
    cfg["model"] = {
        "dim": p.get("dim", 256), "depth": p.get("depth", 8), "heads": p.get("heads", 8),
        "activation_checkpointing": True,
        "decoder": "a copy of the repository's FieldDecoder (node latent and pooled latent, two GELU layers), last "
                   "layer zeroed at the start",
        "head": "each bolt head's three unknowns, w0 and theta from the pooled latent (two GELU layers), last layer "
                "zeroed",
        "features": "centred RMS-normalised coordinates (3), Dirichlet flags (3), node flags (10), family "
                    "parameters over their range maxima (5), the fraction of the member's device range (1)",
        "output_scale": "s = L_REF Theta + delta (mm), L_REF = 300 mm: every nodal output, the heads' axial "
                        "unknowns and w0 times s, the heads' tilts times s over the bearing radius, theta times "
                        "s / L_REF",
        "lift": p["lift"]}
    if "under" in p:                                             # the presets without it keep their configuration
        cfg["model"]["under"] = {
            "preset": str(p["under"]["preset"]), "mesh": str(p["under"]["mesh"]),
            "what": "the networks' outputs are a correction to a field underneath: the field of a finished run of "
                    "`preset` on mesh `mesh`, whose networks stay as they are, carried to this mesh as this mesh's "
                    "preload state plus the carried change from the other mesh's preload state (displacements "
                    "evaluated at this mesh's nodes with the other mesh's shape functions; f2/prolong.py). Nodal "
                    "displacements, the heads' unknowns, w0 and theta add to it; a contact unknown is the map of the "
                    "output shifted so that a zero output gives the value underneath (f2.model.field)"}
    cfg["map"] = {"kind": p.get("map", "softplus"), "T": 1e-3,
                  "on": "the contact unknowns (splice plane, head separations, root openings)"}
    if cfg["map"]["kind"] == "softplus_open":
        cfg["map"]["backward"] = ("a gradient that pulls a contact unknown up passes unreduced; one that pushes it "
                                  "down is multiplied by the map's slope (f2.model.open_gate)")
    cfg["training"] = {
        "members": list(p["members"]),
        "optimizer": "AdamW", "lr": float(p.get("lr", 1e-3)), "weight_decay": 1e-4, "beta2": 0.99, "clip": 1.0,
        "encoder_gradient_cap": {"factor": 5.0, "window_steps": 256, "burst_factor": 10.0},
        "schedule": "cosine with linear warm-up over the first 5% of steps (the repository's)",
        "batch": "one member a step with fields_per_step device rotations; members in a fresh random order "
                 "each epoch",
        "Theta_sampling": "sqrt(Theta) uniform between sqrt(lam_min Theta_max) and sqrt(Theta_max)",
        "lam_min": 0.0125, "fields_per_step": p.get("fields_per_step", 4),
        "energy_loss": "mean over the step's fields of log Pi", "bubble_newton_steps": 10,
        "precision": "float32 weights, activations and energy; float32 matmul precision 'highest' (no TF32)",
        "checkpoint_every_epochs": p.get("checkpoint_every_epochs", 1),
        "snapshot_epochs": list(p.get("snapshot_epochs", [])),
        "resident_members": p.get("resident_members", 48),
        "non_finite": "a non-finite loss stops the run"}
    if "Theta" in p:                                             # the presets without it keep their configuration
        from .model import THETA_KINDS
        kind, top = str(p["Theta"]["kind"]), float(p["Theta"]["top"])
        assert kind in THETA_KINDS and top >= 1.0
        cfg["training"]["Theta_kind"], cfg["training"]["Theta_top"] = kind, top
        cfg["training"]["Theta_sampling"] = (
            ("Theta uniform" if kind == "uniform" else "sqrt(Theta) uniform")
            + " between lam_min Theta_max and Theta_top Theta_max (f2.model.sample_Theta); above Theta_max the "
              "rotations lie beyond the evaluation levels")
    if "extra_members" in p:                                     # the presets without them keep their configuration
        xm = p["extra_members"]
        cfg["training"]["extra_members"] = {
            "n": int(xm["n"]), "seed": int(xm["seed"]), "prefix": "trainx",
            "ranges": {k: [float(v[0]), float(v[1])] for k, v in xm["ranges"].items()},
            "what": "training members added to those of `members`: drawn with their own seed over the family's "
                    "ranges with the listed parts replaced, exported into a data directory of their own "
                    "(f2.data.extra_config) and never solved beyond their preload; an epoch is one step on every "
                    "training member, these included"}
    if "companion" in p:                                         # the presets without it keep their configuration
        cfg["training"]["companion"] = {"mesh": str(p["companion"]["mesh"]), "steps": int(p["companion"]["steps"])}
        cfg["training"]["companion_steps"] = (
            "after every step on a training member, `steps` steps on training members drawn at random from the same "
            "family on the companion mesh (the same loss, optimiser and schedule; every step counts in the schedule)")
    if "ema" in p:                                               # the presets without it keep their configuration
        cfg["training"]["ema"] = {
            "decays": [float(x) for x in p["ema"]],
            "what": "exponential moving averages of the weights, one for each decay d: after every step, average <- "
                    "d average + (1 - d) weights, each starting from the weights the run starts from; they take no "
                    "part in training; they are read at the snapshots and predicted at the end, each in a runs "
                    "directory of its own, <runs>_ema<digits of d> (f2/train.py)"}
    if p.get("loss", "energy") != "energy":                      # the presets without it keep their configuration
        assert p["loss"] in ("elastic_contact_step", "elastic_solution", "energy_and_step", "energy_and_contact_step",
                             "energy_and_elastic")
        cfg["training"]["loss_kind"] = p["loss"]
        if p["loss"] == "energy_and_elastic":
            cfg["training"]["step_weight"] = float(p["step_weight"])
            cfg["training"]["anchor_max_level"] = float(p["anchor_max_level"])
            if p.get("anchor_on", "all") != "all":
                assert p["anchor_on"] == "contact"
                cfg["training"]["anchor_on"] = "contact"           # only the contact unknowns enter the fit
            cfg["training"]["combined_loss"] = (
                "the energy loss plus step_weight times the fit to the elastic solution, with the squares summed over "
                "the unknowns of the step's fields at or below anchor_max_level of the device range and divided by "
                "the number of the step's fields")
        if p["loss"] in ("elastic_solution", "energy_and_elastic"):
            cfg["training"]["elastic_solution_loss"] = (
                "mean square, over the step's fields and unknowns, of (z - z_el) over each unknown's scale: z_el the "
                "member's preload state with the contacts closed plus its elastic contact step at the field's device "
                "rotation (f2/precond.py); it does not depend on z")
        if p["loss"] in ("energy_and_step", "energy_and_contact_step"):
            cfg["training"]["step_weight"] = float(p["step_weight"])
            cfg["training"]["combined_loss"] = (
                "the energy loss plus step_weight times the step loss with the squares summed over a field's "
                + ("contact unknowns" if p["loss"] == "energy_and_contact_step" else "unknowns") + " (not averaged)")
        if p["loss"] not in ("elastic_solution", "energy_and_elastic"):
            cfg["training"]["step_loss"] = (
            "mean square, over the step's fields and unknowns, of (z - (z0 + d)) over each unknown's scale: z0 the "
            "field detached, d the minimiser of the quadratic model of the energy at z0 with the member's tangent at "
            "its preload state, under the contact constraints (f2/precond.py); no reference solution")
    cfg["arms"] = {"label_free": {"loss": p.get("loss", "energy"), "labels": 0, "epochs": p["epochs"],
                                  "seeds": p.get("seeds", [0])}}
    cfg["evaluation"] = {
        "sets": ["eval", "dev", "tested"],
        "members": list(p["evaluated"]) if "evaluated" in p else None,     # None: every member of the sets
        "precision": "float64, the reference code on the exported problem; the elements' state and the contact "
                     "guess are cleared before every exact solve and every energy",
        "readings": {
            "raw": "the network's field z at the level's Theta",
            "condensed": {
                "field": "z_c = keep(z_0 + a (z - z_0)): z_0 the network's field at base_level, keep the contact "
                         "unknowns set to at least zero",
                "amplitude": "a minimises the training energy of z_c at the level's Theta over a_min <= a <= "
                             "a_max (c22/condense.py)",
                "base_level": 0.0125, "a_min": 0.5, "a_max": 3.0,
                "max_evaluations": p.get("max_evaluations", 12), "rtol": 1e-4}},
        "contact_tolerance": "gap <= 1e-3 (L_REF Theta + delta) on the splice plane",
    }
    return cfg


__all__ = ["config", "PRESETS", "DEV_MEMBERS", "TRAIN_SEED", "EVAL_SEED", "EXTRA_SEED", "canonical", "sha256"]
