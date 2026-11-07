"""The configuration of gate G-F1 (bolted CHS blank flange-plate splices of Fidalgo 2023: splice contact with bolt
preload, frictionless and no-slip models as two bounds, against the tests) and its canonical hash.

The choices of the run are here; the pre-specification stamps the canonical JSON's SHA-256, and the SHA-256 of each
code and data file (docs/G-F1_code.sha256). The gate's specimens are B-13 (bending) and T-13 (axial tension), not
solved before the stamp. B-19 and T-19 were solved during development (6 and 7 November 2026) and serve only for dry
runs of this code (`dry` configuration); they are not part of the gate.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"

# Plate material by nominal thickness: coupon curve (Fig. 2.18 of the thesis, digitised), Table 2.2 values, and
# the weighting factor w of the necking extension (thesis eq. 2.23).
PLATES = {"12.7": {"curve": "material_plate13_eng.csv", "E": 201000.0, "fy": 397.0, "fu": 484.0, "eu": 0.1335,
                   "w": 0.4},
          "19.0": {"curve": "material_plate19_eng.csv", "E": 204500.0, "fy": 373.0, "fu": 475.0, "eu": 0.1764,
                   "w": 0.0}}
TUBE = {"curve": "material_chs_eng.csv", "E": 191700.0, "fy": 380.0, "fu": 446.0, "eu": 0.1545, "w": 0.5}

# Measured geometry: bending specimens Table 3.1, axial specimens Table 2.1 (plate thickness tp, e1, e2).
SPECIMENS = {
    "B-13": {"test": "bending", "tp": 12.6, "e1": 64.4, "e2": 65.5, "plate": "12.7"},
    "T-13": {"test": "axial", "tp": 12.6, "e1": 63.9, "e2": 65.2, "plate": "12.7"},
    "B-19": {"test": "bending", "tp": 19.3, "e1": 64.2, "e2": 64.5, "plate": "19.0"},
    "T-19": {"test": "axial", "tp": 19.3, "e1": 65.1, "e2": 64.8, "plate": "19.0"},
}

# Test data (digitised from the thesis; f1/digitise reproduces every file from the thesis PDF).
TESTS = {
    "B-13": {"moment_rotation": ["B13_test_fig33.csv", "B13_test_fig37.csv"], "bolt_forces": "boltforce_B13.csv"},
    "B-19": {"moment_rotation": ["B19_test_fig33.csv", "B19_test_fig37.csv"], "bolt_forces": "boltforce_B19.csv"},
    "T-13": {"load_displacement": ["T13_test_fig25.csv", "T13_test_fig222.csv"]},
    "T-19": {"load_displacement": ["T19_test_fig25.csv", "T19_test_fig222.csv"]},
}

# The comparison points. Bending: the moment at Theta_D = theta (criterion C1, gated) and at the reported points;
# the increase of bolt 1's force between two moments (C3). Axial: the mean LVDT displacement at the load T (C2).
POINTS = {
    "B-13": {"theta": 0.001, "theta_reported": [0.0005], "bolt_moments_kNm": [25.0, 100.0]},
    "T-13": {"T_kN": 800.0},
    "B-19": {"theta": 0.001, "theta_reported": [0.0005], "bolt_moments_kNm": [25.0, 100.0]},
    "T-19": {"T_kN": 1300.0},
}

# Reading tolerances (one pixel of the digitised figures) added to half the spread between the two figures.
PIXEL = {"theta_rad": 8.0e-5, "moment_kNm": 0.7, "bolt_kN": 0.6, "displacement_mm": 0.05}

LOADING = {"bending": {"control": "rotation", "step": 0.0005, "max": 0.03,
                       "stop": "after the first level with Theta_D >= 1.2 theta and M >= the larger bolt moment + 5 kNm"},
           "axial": {"control": "axial", "step": 0.1, "max": 5.0,
                     "stop": "after the first level with T >= T_kN + 50 kN"}}

KKT_LIMITS = {"min_gap": (">=", -1e-12), "min_lambda": (">=", -1e-8), "max_complementarity": ("<=", 1e-8),
              "max_lambda_inactive": ("<=", 1e-6), "max_residual_unconstrained": ("<=", 1e-6)}


def sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def config(dry: bool = False) -> dict:
    names = ["B-19", "T-19"] if dry else ["B-13", "T-13"]
    files = sorted({f for n in names for v in TESTS[n].values() for f in ([v] if isinstance(v, str) else v)}
                   | {PLATES[SPECIMENS[n]["plate"]]["curve"] for n in names} | {TUBE["curve"]})
    return {
        "gate": "G-F1-dry" if dry else "G-F1",
        "specimens": {n: dict(SPECIMENS[n]) for n in names},
        "tests": {n: copy.deepcopy(TESTS[n]) for n in names},
        "points": {n: copy.deepcopy(POINTS[n]) for n in names},
        "pixel": dict(PIXEL),
        "data_sha256": {f: sha256(DATA / f) for f in files},
        "model": {
            "code": "fejoint.chs.SpliceModel, half joint about the bending plane, one side of the splice",
            "fixed_geometry": "tube 323.9 mm outside diameter, wall 12.4 mm; 12 bolts, first at 15 degrees from the "
                              "tension extreme fibre; holes 21 mm; bearing radius 17.3 mm; unfused root 3.4 mm; fillet "
                              "leg 8 mm; tube modelled to 600 mm beyond the plate; measuring ring 100 mm from the "
                              "plate's outer face (fejoint.chs.FlangeSplice defaults)",
            "mesh": "coarse",
            "mesh_flag": {"mesh": "medium", "theory": "elastic", "limit": 0.02},
            "splices": ["frictionless", "no-slip"],
            "theories": {"gated": "hencky", "reported": ["elastic"]},
            "materials": {"plates": {k: dict(v) for k, v in PLATES.items()}, "tube": dict(TUBE), "weld": "tube",
                          "nu": 0.3,
                          "hardening": "f1/materials.py: true stress against equivalent plastic strain from the "
                                       "coupon curve between engineering strains 0.004 and eu (thesis eqs 2.21 and "
                                       "2.22), from fy at zero plastic strain, non-decreasing, at most 14 points; "
                                       "beyond necking thesis eq. 2.23 with the coupon's w, at true strains 1.5 and "
                                       "2.5 times the necking strain and 0.6, final slope to 1.0"},
            "bolts": {"law": "elastic", "E": 217100.0, "As": 213.8,
                      "length": "head / 2 + 2 tp + washer + nut / 2 = 11.9 / 2 + 2 tp + 3.8 + 18.65 / 2 mm"},
            "preload_kN": 125.0,
            "measured_preload": {"specimens": [n for n in names if SPECIMENS[n]["test"] == "bending"],
                                 "rule": "bolts 1 to 6 at the bolt forces of Fig. 3.4 at 25 kNm: bolt 1 the upper and "
                                         "bolt 2 the lower dotted series, bolts 3 and 4 the cyan lines, bolt 5 the "
                                         "upper and bolt 6 the lower red series; reported only",
                                 "theory": "hencky"},
        },
        "loading": copy.deepcopy(LOADING),
        "solver": {"tol": 1e-10, "max_it": 60, "kkt_limits": {k: list(v) for k, v in KKT_LIMITS.items()}},
        "criteria": {
            "C1": "bending: the test moment at Theta_D = theta lies between the two splice models' moments, each "
                  "widened by the reading tolerance",
            "C2": "axial: the test's mean LVDT displacement at T_kN lies between the two models' displacements, "
                  "widened by the reading tolerance",
            "C3": "bending: the increase of bolt 1's force between the two bolt moments lies between the two "
                  "models' increases, widened by the reading tolerance",
            "verdict": "PASS if and only if C1, C2 and C3 hold; a criterion whose model values are missing or come "
                       "from a level that did not converge, or broke a KKT limit, does not hold",
        },
    }


def canonical(cfg: dict) -> str:
    return json.dumps(cfg, sort_keys=True, separators=(",", ":"))


def config_hash(dry: bool = False) -> str:
    return hashlib.sha256(canonical(config(dry)).encode()).hexdigest()


__all__ = ["config", "config_hash", "canonical", "sha256", "SPECIMENS", "TESTS", "POINTS", "PIXEL", "PLATES", "TUBE",
           "LOADING", "KKT_LIMITS", "DATA"]
