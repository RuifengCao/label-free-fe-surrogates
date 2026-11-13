"""Exploratory: the judged quantity of G-C2.1 (distance of the predicted point from the member's reference curve) for the
single-member fitting tests, from the recorded end-displacement errors. The reference curve of a training member is the
monotone (PCHIP) interpolant through the origin and its 7 exact points only, so values near the knee are approximate."""
import json, sys
import numpy as np
from scipy.interpolate import PchipInterpolator
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
base = str(paths.runs() / "overfit") + "/"; LAB = str(paths.work() / "labels") + "/"; KS = 2.0e4
LV = np.array([0.5, 1, 2, 3, 4, 6, 8.0])
for name in ("train_0033_plain", "train_0033_hi", "train_0033_cond", "train_0081_plain", "train_0081_cond"):
    iid = name[:10]; lab = np.load(LAB + iid + ".npz")
    e, F = np.asarray(lab["e"], float), np.asarray(lab["F"], float)
    c = PchipInterpolator(np.concatenate([[0.0], e]), np.concatenate([[0.0], F]), extrapolate=True)
    R = [json.loads(l) for l in open(base + name + ".jsonl") if l.strip()]
    recs = [r for r in R if "step" in r and "raw" in r]
    keys = ["raw"] + (["cond"] if "cond" in recs[0] else [])
    print(f"\n=== {name}   exact e at 4, 6, 8 mm: {np.round(e[4:], 3)}; magnification e/(D-e): {np.round(e[4:] / (LV[4:] - e[4:]), 2)}")
    for k in keys:
        print(f"  [{k}] step | distance from reference curve % at D = 0.5 .. 8 mm")
        for r in recs:
            if r["step"] in (0, 100, 200, 300, 400, 500, 600):
                ep = e * (1 + np.array(r[k]["e_err"])); Fp = 4 * KS * (LV - ep)
                ce = Fp / c(ep) - 1
                print(f"     {r['step']:4d} | " + " ".join(f"{100*v:+7.2f}" for v in ce))
