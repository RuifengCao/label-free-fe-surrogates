#!/usr/bin/env python3
"""The summary numbers of the reading of plastic depth, recomputed from the records of gate G-C2.2 (condensed reading
unless stated).
usage: python3 conditions_numbers.py JOINT SOURCE [--index OUT.csv] [--pairs OUT.csv]
  JOINT : checkout of the joint folder at wp10-joint (records/c22/return/verdict.json, manifest.json)
  SOURCE: either the gate's return folder (labels/eval_*.npz: F, e, plastic_points of the reference solutions)
          or conditions_index.csv, the table of secant ratio and plastic points that --index writes from it
The secant ratio of a comparison is the secant stiffness F/e of the reference solution at that step divided by its
value at the first step. Descriptive reading of 17 November 2026; not one of the gate's criteria."""
import csv, json, os, sys
import numpy as np
J, SRC = sys.argv[1] + "/records/c22/return/", sys.argv[2]
opt = {sys.argv[i]: sys.argv[i + 1] for i in range(3, len(sys.argv) - 1, 2)}
v = json.load(open(J + "verdict.json")); man = {m["id"]: m["params"] for m in json.load(open(J + "manifest.json"))["instances"]}
S = ("5", "6", "7"); ref = {s: v["readings"]["condensed"][s]["eval_rows"] for s in S}; raw = {s: v["readings"]["raw"][s]["eval_rows"] for s in S}
ids = sorted(ref["5"]); rows = []
if os.path.isdir(SRC):
    for m in ids:
        d = np.load(f"{SRC}/labels/{m}.npz"); k = d["F"] / d["e"]
        for i in range(7):
            rows.append(dict(member=m, step=i + 1, D_mm=float(d["D"][i]), e_ref_mm=float(d["e"][i]), F_ref_N=float(d["F"][i]),
                             secant_ratio=float(k[i] / k[0]), plastic_points=int(d["plastic_points"][i].sum())))
else:
    tab = {(r["member"], int(r["step"])): r for r in csv.DictReader(open(SRC))}
    for m in ids:
        for i in range(7):
            r = tab[(m, i + 1)]; rows.append(dict(member=m, step=i + 1, secant_ratio=float(r["secant_ratio"]), plastic_points=int(r["plastic_points"])))
for r in rows:
    m, i = r["member"], r["step"] - 1
    r.update(fy_MPa=man[m]["fy"], **{f"refined_s{s}": ref[s][m][i]["curve_err"] for s in S}, **{f"raw_s{s}": raw[s][m][i]["curve_err"] for s in S})
A = lambda key: np.array([r[key] for r in rows])
idx, pl, step = A("secant_ratio"), A("plastic_points"), A("step")
E = {s: np.abs(A(f"refined_s{s}")) for s in S}; SG = {s: A(f"refined_s{s}") for s in S}; ER = {s: np.abs(A(f"raw_s{s}")) for s in S}
med3 = lambda f: float(np.median([f(s) for s in S]))
pc = lambda x: f"{100 * x:.3f}%"
print("T-stubs:", len(ids), "| steps:", 7, "| comparisons:", len(rows))
print("every T-stub plastic at its last step:", bool(np.all(pl[step == 7] > 0)))
print("refined, all: median", pc(med3(lambda s: np.median(E[s]))), "| 90th percentile", pc(med3(lambda s: np.quantile(E[s], 0.9))), "| gate's C1, C2:", pc(v["C1_value"]), pc(v["C2_value"]))
print("raw, all:     median", pc(med3(lambda s: np.median(ER[s]))), "| 90th percentile", pc(med3(lambda s: np.quantile(ER[s], 0.9))))
el, deep = pl == 0, idx < 0.125
print("elastic comparisons (no plastic Gauss point in the reference solution):", int(el.sum()), "| median", pc(med3(lambda s: np.median(E[s][el]))), "| per surrogate", [pc(np.median(E[s][el])) for s in S], "| max", [pc(E[s][el].max()) for s in S])
print("comparisons with secant ratio < 1/8:", int(deep.sum()), "| median", pc(med3(lambda s: np.median(E[s][deep]))), "| per surrogate", [pc(np.median(E[s][deep])) for s in S])
big = {s: E[s] > 0.10 for s in S}; anyb = big["5"] | big["6"] | big["7"]
print("differences above 10% per surrogate:", [int(big[s].sum()) for s in S], "| of them with secant ratio < 1/8:", [int((big[s] & deep).sum()) for s in S], "| of them overestimates:", [int((big[s] & (SG[s] > 0)).sum()) for s in S])
mem = sorted({rows[i]["member"] for i in np.flatnonzero(anyb)})
print("distinct comparisons above 10% in any surrogate:", int(anyb.sum()), "| T-stubs:", len(mem), "| their yield stresses (MPa):", sorted(round(man[m]["fy"]) for m in mem), "| largest secant ratio among them: %.3f" % idx[anyb].max())
print("first step: T-stubs with no plastic Gauss point:", int((pl[step == 1] == 0).sum()), "of", len(ids))
print("secant ratio at the last step: min %.3f median %.3f max %.3f" % (idx[step == 7].min(), np.median(idx[step == 7]), idx[step == 7].max()))
if "--index" in opt:
    with open(opt["--index"], "w", newline="") as f:
        w = csv.writer(f); w.writerow(["member", "step", "secant_ratio", "plastic_points"])
        for r in rows: w.writerow([r["member"], r["step"], f"{r['secant_ratio']:.6f}", r["plastic_points"]])
    print("written", opt["--index"])
if "--pairs" in opt and "F_ref_N" in rows[0]:
    with open(opt["--pairs"], "w", newline="") as f:
        cols = list(rows[0]); w = csv.writer(f); w.writerow(cols)
        for r in rows: w.writerow([r[c] if isinstance(r[c], (str, int)) else f"{r[c]:.6g}" for c in cols])
    print("written", opt["--pairs"])
