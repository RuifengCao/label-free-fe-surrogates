#!/usr/bin/env python3
"""Exploratory (17 Nov 2026, no gate): relate the judged distance of G-C2.2's refined reading to how far each
T-stub is into the plastic range, measured on the reference (finite element) curve itself.
Index of a pair: secant stiffness of the reference curve at that level divided by its secant stiffness at the
first level (0.5 mm); 1 = still on the initial line, small = far into the plastic range.
usage: python3 plastic_index.py JOINT RETURN   (RETURN holds labels/eval_*.npz of the gate's return)"""
import json, sys
import numpy as np
from scipy.stats import spearmanr
J, R = sys.argv[1] + "/records/c22/return/", sys.argv[2]
v = json.load(open(J + "verdict.json")); man = {m["id"]: m["params"] for m in json.load(open(J + "manifest.json"))["instances"]}
S = ("5", "6", "7"); rows = {s: v["readings"]["condensed"][s]["eval_rows"] for s in S}; raw = {s: v["readings"]["raw"][s]["eval_rows"] for s in S}
ids = sorted(rows["5"])
idx, sign, err, lev, fy, pl = [], {s: [] for s in S}, {s: [] for s in S}, [], [], []
errraw = {s: [] for s in S}
for m in ids:
    d = np.load(f"{R}/labels/{m}.npz"); k = d["F"] / d["e"]; s_rel = k / k[0]
    for i in range(7):
        idx.append(s_rel[i]); lev.append(float(d["D"][i])); fy.append(man[m]["fy"]); pl.append(int(d["plastic_points"][i].sum()))
        for s in S:
            err[s].append(abs(rows[s][m][i]["curve_err"])); sign[s].append(rows[s][m][i]["curve_err"]); errraw[s].append(abs(raw[s][m][i]["curve_err"]))
idx = np.array(idx); lev = np.array(lev); fy = np.array(fy); pl = np.array(pl)
E = {s: np.array(err[s]) for s in S}; SG = {s: np.array(sign[s]) for s in S}; ER = {s: np.array(errraw[s]) for s in S}
print("pairs:", idx.size, "| index range %.3f to %.3f" % (idx.min(), idx.max()))
print("pairs with no plastic Gauss point in the reference solution:", int((pl == 0).sum()), "by level:", {D: int(((pl == 0) & (lev == D)).sum()) for D in sorted(set(lev))})
print("\n-- refined reading by secant-stiffness index (share of the initial secant stiffness that is left)")
edges = [(0.75, 9), (0.5, 0.75), (0.25, 0.5), (0.125, 0.25), (0.0, 0.125)]
for lo, hi in edges:
    sel = (idx >= lo) & (idx < hi)
    f = lambda q: ", ".join(f"{100 * q(E[s][sel]):.2f}" for s in S)
    print(f"index in [{lo}, {hi}) n={int(sel.sum()):3d} | median {f(np.median)} | p90 {f(lambda a: np.quantile(a, 0.9))} | max {f(np.max)} | >10%: {[int((E[s][sel] > 0.10).sum()) for s in S]} | raw p90 " + ", ".join(f"{100 * np.quantile(ER[s][sel], 0.9):.1f}" for s in S))
for s in S:
    r, p = spearmanr(idx, E[s]); print(f"seed {s}: spearman(index, distance) = {r:+.2f} (p = {p:.1e})")
print("\n-- sign of the distance (positive = surrogate force above the reference force at the same end displacement)")
for D in sorted(set(lev)):
    sel = lev == D
    print(f"D = {D}: share positive " + ", ".join(f"{100 * (SG[s][sel] > 0).mean():.0f}%" for s in S) + " | median signed " + ", ".join(f"{100 * np.median(SG[s][sel]):+.2f}" for s in S))
print("all: share positive " + ", ".join(f"{100 * (SG[s] > 0).mean():.0f}%" for s in S))
for thr in (0.05, 0.10):
    print(f"pairs above {int(100 * thr)}%: positive / all = " + ", ".join(f"{int(((E[s] > thr) & (SG[s] > 0)).sum())}/{int((E[s] > thr).sum())}" for s in S))
print("\n-- where are the pairs above 10% (any seed)?")
anyb = np.zeros(idx.size, bool)
for s in S: anyb |= E[s] > 0.10
k = 0
for m in ids:
    for i in range(7):
        if anyb[k]: print(m, "D =", lev[k], "fy = %.0f" % fy[k], "t_f = %.1f" % man[m]["t_f"], "index = %.3f" % idx[k], "distances", [round(100 * E[s][k], 1) for s in S])
        k += 1
print("\n-- index by yield-stress band at 8 mm: median index", {b: round(float(np.median(idx[(lev == 8.0) & (fy >= lo) & (fy < hi)])), 3) for b, (lo, hi) in {"<300": (0, 300), ">=300": (300, 999)}.items()})
