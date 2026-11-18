#!/usr/bin/env python3
"""Exploratory: the other reported metrics of G-C2.2's refined reading, split by the same plasticity index.
usage: python3 other_metrics.py JOINT RETURN"""
import json, sys
import numpy as np
J, R = sys.argv[1] + "/records/c22/return/", sys.argv[2]
v = json.load(open(J + "verdict.json")); S = ("5", "6", "7"); rows = {s: v["readings"]["condensed"][s]["eval_rows"] for s in S}
ids = sorted(rows["5"]); idx, pl = [], []
M = {k: {s: [] for s in S} for k in ("abs_curve_err", "abs_F_err", "e_err", "u_rel_l2", "bolt_err", "iou_plastic", "iou_contact", "within_bound", "bound")}
for m in ids:
    d = np.load(f"{R}/labels/{m}.npz"); k = d["F"] / d["e"]
    for i in range(7):
        idx.append(k[i] / k[0]); pl.append(int(d["plastic_points"][i].sum()))
        for s in S:
            for key in M:
                x = rows[s][m][i][key]; M[key][s].append(np.nan if x is None else abs(float(x)))
idx = np.array(idx); pl = np.array(pl)
groups = (("all", idx > -1), ("elastic (no plastic point)", pl == 0), ("plastic, index >= 0.25", (pl > 0) & (idx >= 0.25)), ("0.125 <= index < 0.25", (idx >= 0.125) & (idx < 0.25)), ("index < 0.125", idx < 0.125))
for key in M:
    print("\n" + key)
    for name, sel in groups:
        a = {s: np.array(M[key][s])[sel] for s in S}
        med = ", ".join(f"{100 * np.nanmedian(a[s]):.2f}" for s in S); p90 = ", ".join(f"{100 * np.nanquantile(a[s], 0.9):.2f}" for s in S); p10 = ", ".join(f"{100 * np.nanquantile(a[s], 0.1):.2f}" for s in S)
        print(f"  {name:28s} n={int(sel.sum()):3d} | median {med} | p10 {p10} | p90 {p90} | nan {[int(np.isnan(a[s]).sum()) for s in S]}")
