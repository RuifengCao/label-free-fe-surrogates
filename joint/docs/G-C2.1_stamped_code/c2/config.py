"""The configuration of gate G-C2.1 (the stage C2 pilot: label-free training on plastic T-stubs) and its canonical
hash.

The choices of the run are here; the pre-specification stamps the canonical JSON's SHA-256. The remaining numbers
inside the code (solver tolerances and iteration limits, mesh details, the family's fixed values) are pinned by the
SHA-256 of each code file, which the pre-specification also stamps.
The repository code the run imports is pinned by the SHA-256 of each file (repository_code); training and the bench
refuse to run against other files.
"""
from __future__ import annotations

import hashlib
import json

from .family import RANGES, CLEAR, D_MAX, K_SPRING, MESH, BOLT, BOLT_LAW, REG, E, NU

# Seeds of the family drawn before the stamp, kept out of the run's samples: development checks of 5 and 6 November
# 2026 (7), the test suite (7, 8), and two dry runs of the runbook on a reduced configuration on 6 November 2026
# (101, 102).
SEEDS_SEEN = [7, 8, 101, 102]

# The repository files the run imports (an import trace of train and bench), unchanged since wp9-pool 92dfc93.
REPOSITORY_CODE = {
    "src/fejepa/__init__.py": "6b4a69dde91fbd83c5c16707a00e4c9e6a2e02647aca1d3132b313e4b20f9fdc",
    "src/fejepa/models/__init__.py": "88d852286c71e468491b7d0b34cec2c467bd4c96724a26ca8ebcc6b8f92306e4",
    "src/fejepa/models/features.py": "0af43e0a87fda6bc177e9b446a720ac11e3e116bc29e445446edf846162c208d",
    "src/fejepa/models/fejepa.py": "3263988641477cfab564c5c622f8cf3406d98e45078134da8c6905d4b410b847",
    "src/fejepa/train/__init__.py": "88d852286c71e468491b7d0b34cec2c467bd4c96724a26ca8ebcc6b8f92306e4",
    "src/fejepa/train/schedule.py": "d53b55877c65efc37ee0a3877362451d8227ef84f581df64138ac1b469bd57c5",
}

N_Y = BOLT_LAW[0][1] * BOLT["As"]          # the bolt's nominal yield force, N
TESTED = {                                  # Bursi and Jaspart (1997) T1 and T2 as members of the family
    "BJ_T1_preloaded": {"t_f": 10.7, "t_w": 7.1, "r": 15.0, "w": 90.0, "n": 30.0, "fy": 431.0, "rho": 60700.0 / N_Y},
    "BJ_T1_snug": {"t_f": 10.7, "t_w": 7.1, "r": 15.0, "w": 90.0, "n": 30.0, "fy": 431.0, "rho": 0.0},
    "BJ_T2_preloaded": {"t_f": 16.0, "t_w": 9.5, "r": 18.0, "w": 90.0, "n": 30.0, "fy": 282.0, "rho": 60700.0 / N_Y},
    "BJ_T2_snug": {"t_f": 16.0, "t_w": 9.5, "r": 18.0, "w": 90.0, "n": 30.0, "fy": 282.0, "rho": 0.0},
}

KKT_LIMITS = {"min_gap": (">=", -1e-12), "min_lambda": (">=", -1e-8), "max_complementarity": ("<=", 1e-8),
              "max_lambda_inactive": ("<=", 1e-6), "max_residual_unconstrained": ("<=", 1e-6)}


def config() -> dict:
    return {
        "gate": "G-C2.1",
        "family": {"ranges": {k: list(v) for k, v in RANGES.items()}, "clear_mm": CLEAR, "D_max_mm": D_MAX,
                   "loading": {"spring_N_per_mm": K_SPRING,
                               "how": "the web's end section rigid in x (one unknown e), joined by a linear spring "
                                      "to the loading device, whose displacement D is prescribed; the force on the "
                                      "pair F = 4 k_s (D - e)"},
                   "fixed": "rolled T-stub pair, quarter model; L 80 mm, one bolt row at y = 20 mm, web to H = 120 mm; "
                            "M12 bolts, two washers, bearing radius 12 mm; E 210000, nu 0.3",
                   "steel": "elastic to fy, plateau to 2% strain, linear to 1.35 fy at 15%, then E/10000; a "
                            "slope of E/10000 added throughout the plastic range",
                   "bolt": {"law_strain_stress": [list(p) for p in BOLT_LAW], "regulariser_MPa": REG},
                   "theory": "J2 deformation theory (Hencky), small strain; frictionless unilateral contact",
                   "E": E, "nu": NU},
        "data": {"train_seed": 20261106, "eval_seed": 20261107, "n_train": 512, "n_eval": 64,
                 "tested": {k: dict(v) for k, v in TESTED.items()},
                 "seeds_seen_before_stamp": list(SEEDS_SEEN), "mesh": dict(MESH),
                 "eval_levels_mm": [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0],
                 "train_label_levels_mm": [0.75, 1.5, 2.5, 3.5, 5.0, 7.0], "n_train_labelled": 64,
                 "label_solver": {"tol": 1e-12, "max_it": 80,
                                  "order": "levels in increasing order, each from the previous level's solution"},
                 "kkt_limits": {k: list(v) for k, v in KKT_LIMITS.items()}},
        "repository_code": dict(REPOSITORY_CODE),
        "model": {"dim": 256, "depth": 8, "heads": 8, "activation_checkpointing": True,
                  "decoder": "a copy of the repository's FieldDecoder (node latent and pooled latent, two GELU "
                             "layers), last layer zeroed at the start",
                  "head": "the end section's u_x (e) and the bolt head's three unknowns from the pooled latent (two "
                          "GELU layers), last layer zeroed",
                  "features": "centred RMS-normalised coordinates (3), Dirichlet flags (3), node flags (7), family "
                              "parameters over their range maxima (7), loading-device displacement over D_max (1)",
                  "output_scale": "D + delta (mm): every nodal output, e and the head's axial unknown times it, the "
                                  "head's two tilts times it over the bearing radius",
                  "lift": "web"},
        "map": {"kind": "softplus", "T": 1e-3,
                "on": "u_x of the plane between the flanges and the separation slots of the bearing patch"},
        "training": {"optimizer": "AdamW", "lr": 1e-3, "weight_decay": 1e-4, "clip": 1.0,
                     "schedule": "cosine with linear warm-up over the first 5% of steps (the repository's)",
                     "batch": "one instance per step with 4 end displacements; instances in a fresh random order "
                              "each epoch",
                     "D_sampling": "sqrt(D) uniform between sqrt(0.1) and sqrt(D_max) (label-free); 4 of the "
                                   "labelled levels without replacement (supervised)",
                     "D_min_mm": 0.1, "fields_per_step": 4,
                     "energy_loss": "mean over the step's fields of log Pi (Pi > 0 for D > 0)",
                     "bubble_newton_steps": 10,
                     "supervised_loss": "mean squared error of the physical displacement over (D + delta)^2",
                     "precision": "float32 weights, activations and energy; float32 matmul precision 'highest' "
                                  "(no TF32)",
                     "non_finite": "a non-finite loss stops the run; the stop is final and is not retried"},
        "arms": {
            "label_free": {"loss": "energy", "labels": 0, "epochs": 200, "seeds": [0, 1, 2]},
            "supervised_64": {"loss": "supervised", "labels": 64, "epochs": 200, "seeds": [0, 1, 2]},
        },
        "evaluation": {
            "sets": ["eval", "tested"],
            "precision": "float64, the reference code (fejoint.nlhex, fejoint.nlsolve) on the exported problem",
            "force": "the point (e, F) of a field, F = 4 k_s (D - e) its spring reading; judged by its distance "
                     "from the reference curve in force at the predicted end displacement, F / F*(e) - 1, F*(e) from "
                     "an exact solve under displacement control",
            "contact_tolerance": "u_x <= 1e-3 (D + delta) on the plane between the flanges, for prediction and "
                                 "reference alike",
            "metrics": ["F_pred / F*(e_pred) - 1", "F_pred / F_ref - 1 at the same D",
                        "the stress reading F_sigma = 4 grad W . v over F_ref, minus 1",
                        "e_pred / e_ref - 1", "energy gap (Pi - Pi*) / Pi*",
                        "certified bound 4 sqrt(2 k_s (Pi - Pi*)) / F_ref", "contact intersection over union",
                        "plastic Gauss points intersection over union", "bolt force N_pred / N_ref - 1",
                        "physical displacement relative L2 error"],
        },
        "criteria": {
            "C1": "label-free arm: the median over its three seeds of the median over the 448 held-out (member, "
                  "level) pairs of |F_pred / F*(e_pred) - 1| is at most 0.05",
            "C2": "label-free arm: the median over its three seeds of the 90th percentile over the same pairs of "
                  "|F_pred / F*(e_pred) - 1| is at most 0.10",
            "verdict": "PASS iff C1 and C2",
            "non_finite_seed": "a label-free seed whose run stopped on a non-finite loss or non-finite "
                               "predictions, or whose metrics of a member fail altogether, enters the medians over "
                               "seeds with infinite errors",
            "infinite_pairs": "a pair whose reference solve at the predicted end displacement fails, or gives a "
                              "force that is not positive, has an infinite curve error, which enters the median and "
                              "the 90th percentile as such",
            "incomplete": "INCOMPLETE while a label-free seed has neither predictions nor a non-finite stop",
            "reported_not_judged": "every metric for every arm and seed; the supervised arm against the label-free "
                                   "one, with no winner set in advance; the tested members (Bursi and Jaspart T1 and "
                                   "T2 under the family's nominal laws)",
        },
    }


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def sha256(obj) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()
