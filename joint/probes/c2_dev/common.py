"""Helpers for the exploratory re-reading of G-C2.1's returned predictions (not pre-registered; changes no verdict)."""
import sys, json
from pathlib import Path
import numpy as np

import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
JOINT = str(paths.joint())
DATA = Path(paths.data())
RET = Path(paths.ret())
if JOINT not in sys.path:
    sys.path.insert(0, JOINT)
from c2.data import load_export          # noqa: E402
from c2.instance import ExportedProblem  # noqa: E402

LEVELS = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
KS = 2.0e4


def verdict():
    return json.loads((RET / "verdict.json").read_text())


def label(iid):
    with np.load(RET / "labels" / f"{iid}.npz") as z:
        return {k: z[k] for k in z.files}


def preds(run):
    with np.load(RET / "runs" / run / "preds.npz") as z:
        return {k: z[k] for k in z.files}


def problem(iid):
    ex, q = load_export(DATA / "inst" / f"{iid}.npz")
    return ExportedProblem(ex), ex, q


def eval_ids():
    man = json.loads((DATA / "manifest.json").read_text())
    return [r["id"] for r in man["instances"] if r["split"] == "eval"], {r["id"]: r["params"] for r in man["instances"]}
