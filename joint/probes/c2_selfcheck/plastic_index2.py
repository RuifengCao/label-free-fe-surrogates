#!/usr/bin/env python3
"""Exploratory follow-up to plastic_index.py: elastic against plastic pairs, the index by level, and the same split on
G-C2.1's held-out members (reported, not judged, and used in development).
usage: python3 plastic_index2.py JOINT RETURN"""
import json, sys, glob, os
import numpy as np
J, R = sys.argv[1] + "/records/c22/return/", sys.argv[2]
v = json.load(open(J + "verdict.json")); S = ("5", "6", "7")
def load(key):
    rows = {s: v["readings"]["condensed"][s][key] for s in S}; raw = {s: v["readings"]["raw"][s][key] for s in S}
    ids = sorted(rows["5"]); idx, lev, pl = [], [], []; E = {s: [] for s in S}; ER = {s: [] for s in S}
    for m in ids:
        d = np.load(f"{R}/labels/{m}.npz"); k = d["F"] / d["e"]
        for i in range(7):
            idx.append(k[i] / k[0]); lev.append(float(d["D"][i])); pl.append(int(d["plastic_points"][i].sum()))
            for s in S: E[s].append(abs(rows[s][m][i]["curve_err"])); ER[s].append(abs(raw[s][m][i]["curve_err"]))
    return ids, np.array(idx), np.array(lev), np.array(pl), {s: np.array(E[s]) for s in S}, {s: np.array(ER[s]) for s in S}
def show(name, sel, E):
    f = lambda q: ", ".join(f"{100 * q(E[s][sel]):.2f}" for s in S)
    print(f"{name:34s} n={int(sel.sum()):3d} | median {f(np.median)} | p90 {f(lambda a: np.quantile(a, 0.9))} | max {f(np.max)} | >10%: {[int((E[s][sel] > 0.10).sum()) for s in S]} | >5%: {[int((E[s][sel] > 0.05).sum()) for s in S]}")
print(sorted(set(os.path.basename(p).split('_')[0] for p in glob.glob(R + "/labels/*.npz"))), list(v["readings"]["condensed"]["5"].keys()))
for key, title in (("eval_rows", "FRESH held-out members (judged)"), ("former_rows", "G-C2.1's held-out members (reported, used in development)")):
    ids, idx, lev, pl, E, ER = load(key)
    print("\n==", title, "members", len(ids))
    show("no plastic Gauss point (elastic)", pl == 0, E); show("plastic", pl > 0, E)
    show("index >= 0.25", idx >= 0.25, E); show("0.125 <= index < 0.25", (idx >= 0.125) & (idx < 0.25), E); show("index < 0.125", idx < 0.125, E)
    show("index >= 0.125", idx >= 0.125, E)
    print("   raw reading:"); show("   index >= 0.125", idx >= 0.125, ER); show("   index < 0.125", idx < 0.125, ER)
    for D in sorted(set(lev)):
        a = idx[lev == D]; print(f"   D = {D}: index min {a.min():.3f} median {np.median(a):.3f} max {a.max():.3f} | pairs with index < 0.125: {int((a < 0.125).sum())}")
    worst = max(float(idx[E[s] > 0.10].max()) if (E[s] > 0.10).any() else 0 for s in S); print(f"   largest index among pairs above 10% (any seed): {worst:.3f}")
    for thr in (0.05,):
        w = max(float(idx[E[s] > thr].max()) for s in S); print(f"   largest index among pairs above 5% (any seed): {w:.3f}")
    mem = {}
    for k_, m in enumerate([m for m in ids for _ in range(7)]):
        if any(E[s][k_] > 0.10 for s in S): mem.setdefault(m, []).append(lev[k_])
    print("   members with a pair above 10% (any seed):", len(mem), "| distinct pairs:", sum(len(x) for x in mem.values()))
