#!/usr/bin/env python3
"""Can a prediction tell, without any FE solution, where the surrogate is far from the FE model?
usage: python3 selfcheck_indicators.py JOINT RETURN [OUT.csv]
  JOINT : checkout of the joint folder at wp10-joint (records/c22/return/verdict.json)
  RETURN: unpacked return folder with labels/<member>.npz (FE force F and end displacement e at the seven steps)

Exploratory, 18 November 2026, written before any of the indicators below had been computed on either sample
(one row had been seen: the worst case of the fresh sample, run 5). Nothing here was fixed in advance of the
evaluation; no threshold is tuned: indicators are compared by rank statistics and at one flagged share (one quarter).

Samples: "former" = the 64 held-out T-stubs of the first evaluation; "eval" = the 64 fresh T-stubs of the second
evaluation. Each has 448 cases (T-stub x step) and three training runs. All quantities are of the rescaled prediction.
Target: the judged difference |F / F_FE(e) - 1| (verdict rows, abs_curve_err).
Indicators that use the prediction and the FE model's energy, but no FE solution:
  A  own secant stiffness ratio: (F/e at this step) / (F/e at the first step) of the predicted curve (small = deep)
  B  mismatch of the two force readings of one prediction, |F_sigma / F - 1|: F from the loading spring, F_sigma from
     the stresses; they are equal for the FE solution
  C  change of the predicted force made by the rescaling, |F_rescaled / F_raw - 1|
  D  spread of the predicted force over the three training runs, (max - min) / median
For comparison, an indicator that needs the FE solution:
  O  secant stiffness ratio of the FE solution (the index of the conditions analysis of 17 November)
The record stores errors relative to the FE values; the predicted F, e and F_sigma are rebuilt from them. In B, C and
D the FE values cancel, so these three could be computed from the verdict rows alone."""
import csv, json, sys
import numpy as np
from scipy.stats import rankdata, spearmanr

J, RET = sys.argv[1] + "/records/c22/return/", sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else None
v = json.load(open(J + "verdict.json"))
S = ("5", "6", "7")


def load(setname):
    rows = {r: {s: v["readings"][r][s][setname + "_rows"] for s in S} for r in ("condensed", "raw")}
    ids = sorted(rows["condensed"]["5"])
    Fr, er = [], []
    for m in ids:
        d = np.load(f"{RET}/labels/{m}.npz"); Fr.append(d["F"]); er.append(d["e"])
    Fr, er = np.array(Fr), np.array(er)                                   # members x 7
    g = lambda r, s, k: np.array([[rows[r][s][m][i][k] for i in range(7)] for m in ids], dtype=float)
    out = {"ids": ids, "O": (Fr / er) / (Fr[:, :1] / er[:, :1])}
    F = {}
    for s in S:
        Fs, es = Fr * (1 + g("condensed", s, "F_err")), er * (1 + g("condensed", s, "e_err"))
        F[s] = Fs
        out[s] = {"err": g("condensed", s, "abs_curve_err"), "signed": g("condensed", s, "curve_err"),
                  "A": (Fs / es) / (Fs[:, :1] / es[:, :1]),
                  "B": np.abs((1 + g("condensed", s, "F_sigma_err")) / (1 + g("condensed", s, "F_err")) - 1),
                  "C": np.abs((1 + g("condensed", s, "F_err")) / (1 + g("raw", s, "F_err")) - 1)}
    stack = np.stack([F[s] for s in S])
    out["D"] = (stack.max(0) - stack.min(0)) / np.median(stack, 0)
    return out


def auc(score, positive):
    """Probability that a positive case has the larger score (ties count half)."""
    n1 = int(positive.sum()); n0 = len(positive) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(score)
    return float((r[positive].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def score_of(d, s, name):
    """Larger score = more suspect."""
    if name == "O":
        return -d["O"].ravel()
    if name == "A":
        return -d[s]["A"].ravel()
    if name == "D":
        return d["D"].ravel()
    return d[s][name].ravel()


NAMES = ("A", "B", "C", "D", "O")
LABEL = {"A": "A own secant ratio", "B": "B force mismatch", "C": "C rescaling change", "D": "D spread of runs",
         "O": "O FE secant ratio*"}
data = {k: load(k) for k in ("former", "eval")}
table = []
for setname, d in data.items():
    print(f"\n=== {setname}: {len(d['ids'])} T-stubs, 448 cases; values are for runs 5, 6, 7 ===")
    n10 = [int((d[s]['err'].ravel() > 0.10).sum()) for s in S]; n5 = [int((d[s]['err'].ravel() > 0.05).sum()) for s in S]
    print(f"cases above 10%: {n10}; above 5%: {n5}; missing indicator values: "
          f"{[int(np.isnan(d[s]['B']).sum()) for s in S]}")
    print("indicator            | Spearman with the difference | AUC, above 5%        | AUC, above 10%       | "
          "top quarter flagged: caught of >10% | of >5% | largest unflagged")
    for name in NAMES:
        rho, a5, a10, c10, c5, mx = [], [], [], [], [], []
        for s in S:
            e, sc = d[s]["err"].ravel(), score_of(d, s, name)
            rho.append(spearmanr(sc, e).statistic); a5.append(auc(sc, e > 0.05)); a10.append(auc(sc, e > 0.10))
            flag = sc >= np.quantile(sc, 0.75)
            c10.append(f"{int((flag & (e > 0.10)).sum())}/{int((e > 0.10).sum())}")
            c5.append(f"{int((flag & (e > 0.05)).sum())}/{int((e > 0.05).sum())}"); mx.append(100 * e[~flag].max())
            table.append([setname, name, s, f"{rho[-1]:.3f}", f"{a5[-1]:.3f}", f"{a10[-1]:.3f}", c10[-1], c5[-1], f"{mx[-1]:.2f}"])
        f3 = lambda x, n=2: ", ".join(f"{t:.{n}f}" for t in x)
        print(f"{LABEL[name]:20s} | {f3(rho):28s} | {f3(a5, 3):20s} | {f3(a10, 3):20s} | {', '.join(c10):24s} | "
              f"{', '.join(c5):20s} | {f3(mx, 1)}%")
print("\n* needs the FE solution; shown for comparison only.")
print("\n=== an absolute threshold carried from the first sample to the second ===")
print("threshold = upper quartile of the indicator over the former sample (three runs pooled); applied to eval")
for name in NAMES:
    pooled = np.concatenate([score_of(data["former"], s, name) for s in S]); tau = float(np.quantile(pooled, 0.75))
    res = []
    for s in S:
        e, sc = data["eval"][s]["err"].ravel(), score_of(data["eval"], s, name)
        flag = sc >= tau
        res.append(f"{int(flag.sum())} flagged, {int((flag & (e > 0.10)).sum())}/{int((e > 0.10).sum())} of >10%, "
                   f"{int((flag & (e > 0.05)).sum())}/{int((e > 0.05).sum())} of >5%, largest unflagged {100 * e[~flag].max():.1f}%")
    shown = -tau if name in ("A", "O") else tau
    print(f"{LABEL[name]:20s} threshold {shown:.4f} | " + " | ".join(res))
if OUT:
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sample", "indicator", "run", "spearman", "auc_above5", "auc_above10", "top_quarter_caught_above10",
                    "top_quarter_caught_above5", "largest_unflagged_pct"])
        w.writerows(table)
    print("\nwritten", OUT)
