#!/usr/bin/env python3
"""Details of indicator D (spread of the predicted force over the training runs) and of C (change made by the rescaling).
usage: python3 spread_details.py JOINT RETURN
Exploratory, 18 November 2026. Threshold of D: the upper quartile over the former sample, carried to the others."""
import json, sys, itertools
import numpy as np
from scipy.stats import rankdata
J, RET = sys.argv[1] + "/records/c22/return/", sys.argv[2]
v = json.load(open(J + "verdict.json")); S = ("5", "6", "7")
def load(setname):
    rows = {r: {s: v["readings"][r][s][setname + "_rows"] for s in S} for r in ("condensed", "raw")}
    ids = sorted(rows["condensed"]["5"])
    g = lambda r, s, k: np.array([[rows[r][s][m][i][k] for i in range(7)] for m in ids], dtype=float)
    d = {"ids": ids, "err": {s: g("condensed", s, "abs_curve_err") for s in S},
         "rel": {s: 1 + g("condensed", s, "F_err") for s in S},
         "C": {s: np.abs((1 + g("condensed", s, "F_err")) / (1 + g("raw", s, "F_err")) - 1) for s in S}}
    try:
        Fr, er = zip(*[(np.load(f"{RET}/labels/{m}.npz")["F"], np.load(f"{RET}/labels/{m}.npz")["e"]) for m in ids])
        Fr, er = np.array(Fr), np.array(er); d["O"] = (Fr / er) / (Fr[:, :1] / er[:, :1])
    except FileNotFoundError:
        d["O"] = None
    return d
def spread(d, runs=S):
    st = np.stack([d["rel"][s] for s in runs]); return (st.max(0) - st.min(0)) / np.median(st, 0)
def auc(score, pos):
    n1 = int(pos.sum()); n0 = len(pos) - n1
    if not n1 or not n0: return float("nan")
    r = rankdata(score); return float((r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
D = {k: load(k) for k in ("former", "eval", "tested")}
tau = float(np.quantile(spread(D["former"]).ravel(), 0.75))
print(f"threshold on the spread, from the former sample: {100 * tau:.3f}% of the force")
pc = lambda x: ", ".join(f"{100 * t:.2f}" for t in x)
for k in ("former", "eval", "tested"):
    d = D[k]; sp = spread(d).ravel(); flag = sp >= tau; n = len(sp)
    print(f"\n{k}: {n} cases, flagged {int(flag.sum())} ({100 * flag.mean():.1f}%)")
    E = {s: d["err"][s].ravel() for s in S}
    print("  not flagged: median %s | p90 %s | max %s | above 5%%: %s" % (pc([np.median(E[s][~flag]) for s in S]),
          pc([np.quantile(E[s][~flag], 0.9) for s in S]), pc([E[s][~flag].max() for s in S]), [int((E[s][~flag] > 0.05).sum()) for s in S]))
    if flag.any():
        print("  flagged    : median %s | p90 %s | max %s | above 5%%: %s | above 10%%: %s" % (pc([np.median(E[s][flag]) for s in S]),
              pc([np.quantile(E[s][flag], 0.9) for s in S]), pc([E[s][flag].max() for s in S]),
              [int((E[s][flag] > 0.05).sum()) for s in S], [int((E[s][flag] > 0.10).sum()) for s in S]))
    if d["O"] is not None:
        deep = d["O"].ravel() < 0.125; steps = np.tile(np.arange(1, 8), len(d["ids"]))
        print(f"  flagged and FE secant ratio < 1/8: {int((flag & deep).sum())} of {int(deep.sum())} deep cases; flagged but not deep: {int((flag & ~deep).sum())}"
              f" | flagged by step 1..7: {[int((flag & (steps == i)).sum()) for i in range(1, 8)]}")
    # smallest flagged share that still contains every case above 5% (any run)
    any5 = np.any([E[s] > 0.05 for s in S], axis=0)
    if any5.any():
        need = float((sp >= sp[any5].min()).mean())
        print(f"  cases above 5% in any run: {int(any5.sum())}; smallest spread among them {100 * sp[any5].min():.3f}%; share flagged at that threshold {100 * need:.1f}%")
print("\nspread of two runs only (threshold = its own upper quartile on the former sample), judged on the eval sample:")
for a, b in itertools.combinations(S, 2):
    t2 = float(np.quantile(spread(D["former"], (a, b)).ravel(), 0.75)); sp = spread(D["eval"], (a, b)).ravel(); flag = sp >= t2
    for s in (a, b):
        e = D["eval"]["err"][s].ravel()
        print(f"  runs {a},{b}, difference of run {s}: AUC above 5% {auc(sp, e > 0.05):.3f} | flagged {int(flag.sum())} | caught "
              f"{int((flag & (e > 0.10)).sum())}/{int((e > 0.10).sum())} of >10%, {int((flag & (e > 0.05)).sum())}/{int((e > 0.05).sum())} of >5% | largest unflagged {100 * e[~flag].max():.1f}%")
print("\nchange made by the rescaling (one run is enough): threshold = upper quartile on the former sample, three runs pooled")
tc = float(np.quantile(np.concatenate([D["former"]["C"][s].ravel() for s in S]), 0.75))
for k in ("former", "eval"):
    for s in S:
        e, c = D[k]["err"][s].ravel(), D[k]["C"][s].ravel(); flag = c >= tc
        print(f"  {k}, run {s}: flagged {int(flag.sum())} | caught {int((flag & (e > 0.10)).sum())}/{int((e > 0.10).sum())} of >10%, "
              f"{int((flag & (e > 0.05)).sum())}/{int((e > 0.05).sum())} of >5% | not flagged: median {100 * np.median(e[~flag]):.2f}%, p90 {100 * np.quantile(e[~flag], 0.9):.2f}%, max {100 * e[~flag].max():.1f}%")
