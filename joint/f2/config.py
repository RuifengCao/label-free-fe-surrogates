"""The configuration of the CHS surrogate gate (DRAFT: not stamped; sections for the model, training, evaluation
and criteria are written with the pre-specification) and its canonical hash. Follows c2/config.py.

Until the stamp the seeds are unset: f2.data refuses to draw the training and evaluation members, and the tests
draw with seeds of their own (tests/test_f2.py).
"""
from __future__ import annotations

import hashlib
import json

from .family import RANGES, TESTED, K_TH, THETA_TARGET, B_TUBE, M_RULE, MESH, BOLT, BOLT_REG, E_P, PLATE_BASE, CLEAR

KKT_LIMITS = {"min_gap": (">=", -1e-12), "min_lambda": (">=", -1e-8), "max_complementarity": ("<=", 1e-8),
              "max_lambda_inactive": ("<=", 1e-6), "max_residual_unconstrained": ("<=", 1e-6)}
SEEDS_SEEN = [11, 12]          # the tests' seeds


def config() -> dict:
    return {
        "gate": "G-F2 (draft)",
        "family": {
            "ranges": {k: list(v) for k, v in RANGES.items()}, "clear_mm": CLEAR,
            "fixed": "fejoint.chs.FlangeSplice defaults: tube 323.9 x 12.4 mm, 600 mm beyond the plate; 12 bolts of "
                     "3/4 inch, the first at 15 degrees from the tension extreme fibre; holes 21 mm; bearing radius "
                     "17.3 mm; unfused root 3.4 mm; fillet leg 8 mm; measuring ring 100 mm from the plate",
            "plate": {"law": f"gate G-F1's {PLATE_BASE} mm plate law (f1/materials.py), stresses scaled by fy / 397",
                      "E": E_P},
            "tube_and_weld": "gate G-F1's tube law (f1/materials.py), E 191700",
            "bolt": {"law": "exploratory run E3's (coupon curve by f1/materials.py's rule)", **BOLT,
                     "final_slope": f"{BOLT_REG} E_b A_s / (L_b / 2) beyond the last point"},
            "theory": "J2 deformation theory (Hencky), small strain; unilateral contact on the splice plane, under "
                      "the bolt heads and at the weld's root",
            "splice": "frictionless",
            "preload": "every bolt pre-shortened by the same delta, set by a fixed point so that the six bolts' mean "
                       "force at zero rotation is Np",
            "loading": {"k_th_Nmm_per_rad_half_model": K_TH, "Theta_target": THETA_TARGET,
                        "how": "end section plane, w0 free; theta joined by a linear spring to the loading device, "
                               "whose rotation Theta in [0, Theta_max(q)] is prescribed; M = 2 k_th (Theta - theta)",
                        "range": "Theta_max(q) = Theta_target + (B_tube + 1 / (2 k_th)) M_est(q); M_est the smooth "
                                 "minimum (exponent n) of A (tp/15)^tp (fy/400)^fy (e1/65)^e1 (e2/65)^e2 and the cap; "
                                 "fitted on the development paths of 8 November 2026 (probes/f2_dev)",
                        "B_tube_rad_per_Nmm": B_TUBE, "M_est": dict(M_RULE)},
        },
        "data": {"train_seed": None, "eval_seed": None, "n_train": 512, "n_eval": 64,
                 "tested": {k: dict(v) for k, v in TESTED.items()}, "seeds_seen_before_stamp": list(SEEDS_SEEN),
                 "mesh": MESH,
                 "eval_levels": [0.0625, 0.125, 0.25, 0.375, 0.5, 0.75, 1.0],
                 "train_label_levels": [0.09375, 0.1875, 0.3125, 0.4375, 0.625, 0.875], "n_train_labelled": 64,
                 "label_solver": {"tol": 1e-12, "max_it": 80,
                                  "order": "levels in increasing order, the first from the preload state, each next "
                                           "from the previous level's solution"},
                 "kkt_limits": {k: list(v) for k, v in KKT_LIMITS.items()}},
    }


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def sha256(obj) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()
