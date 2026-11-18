#!/usr/bin/env python3
"""Where the label-free surrogate of gate G-C2.2 agrees with the finite element model: the judged distance
|F / F*(e) - 1| of the refined (condensed) reading on the 64 fresh held-out T-stubs, split by displacement level,
yield stress, flange thickness and preload. Descriptive reading of the gate's public records (17 Nov 2026); no gate.
usage: python3 conditions.py JOINT"""
import json, sys
import numpy as np
J = sys.argv[1] + "/records/c22/return/"
v = json.load(open(J + "verdict.json")); man = {m["id"]: m["params"] for m in json.load(open(J + "manifest.json"))["instances"]}
S = ("5", "6", "7")
rows = {r: {s: v["readings"][r][s]["eval_rows"] for s in S} for r in ("condensed", "raw")}
ids = sorted(rows["condensed"]["5"]); L = [x["D"] for x in rows["condensed"]["5"][ids[0]]]
def arr(r, s, sel=None, lev=None):
    return np.array([abs(x["curve_err"]) for m in ids if (sel is None or sel(man[m])) for i, x in enumerate(rows[r][s][m]) if (lev is None or i in lev)])
def line(name, sel=None, lev=None, r="condensed"):
    out = []
    for s in S:
        a = arr(r, s, sel, lev)
        out.append((a.size, 100 * np.median(a), 100 * np.quantile(a, 0.9), 100 * a.max(), int((a > 0.10).sum()), int((a > 0.05).sum())))
    n = out[0][0]
    f = lambda k: ", ".join(f"{o[k]:.2f}" for o in out)
    print(f"{name:42s} n={n:4d} | median {f(1)} | p90 {f(2)} | max {f(3)} | >10%: {[o[4] for o in out]} | >5%: {[o[5] for o in out]}")
print("REFINED reading, fresh 64 T-stubs, seeds 5 6 7")
line("all")
print("-- by displacement level D of the loading device (mm)")
for i, D in enumerate(L): line(f"D = {D}", lev=[i])
print("-- by yield stress")
for lo, hi in ((235, 300), (300, 355), (355, 460.01), (300, 460.01)):
    line(f"fy in [{lo}, {hi:.0f})", sel=lambda p, lo=lo, hi=hi: lo <= p["fy"] < hi)
print("-- fy >= 300, by level"); 
for i, D in enumerate(L): line(f"  fy >= 300, D = {D}", sel=lambda p: p["fy"] >= 300, lev=[i])
print("-- fy < 300, by level")
for i, D in enumerate(L): line(f"  fy < 300, D = {D}", sel=lambda p: p["fy"] < 300, lev=[i])
print("-- by flange thickness")
for lo, hi in ((8, 12), (12, 16), (16, 20.01)): line(f"t_f in [{lo}, {hi:.0f})", sel=lambda p, lo=lo, hi=hi: lo <= p["t_f"] < hi)
print("-- by preload ratio")
for lo, hi in ((0, 0.3), (0.3, 0.6), (0.6, 0.91)): line(f"rho in [{lo}, {hi})", sel=lambda p, lo=lo, hi=hi: lo <= p["rho"] < hi)
print("-- counts: members by fy band:", {b: sum(1 for m in ids if lo <= man[m]["fy"] < hi) for b, (lo, hi) in {"<300": (0, 300), "300-355": (300, 355), ">=355": (355, 999)}.items()})
print("\nRAW reading (no refinement)")
line("all", r="raw"); line("fy >= 300", sel=lambda p: p["fy"] >= 300, r="raw"); line("fy < 300", sel=lambda p: p["fy"] < 300, r="raw")
for i, D in enumerate(L): line(f"D = {D}", lev=[i], r="raw")
# rank correlation of a member's largest refined error (median over seeds) with its parameters
from scipy.stats import spearmanr
score = np.array([np.median([max(abs(x["curve_err"]) for x in rows["condensed"][s][m]) for s in S]) for m in ids])
for k in ("fy", "t_f", "t_w", "r", "w", "n", "rho"):
    rho, p = spearmanr(score, [man[m][k] for m in ids]); print(f"spearman(largest error of a member, {k}) = {rho:+.2f} (p = {p:.3f})")
