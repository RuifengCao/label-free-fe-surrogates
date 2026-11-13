"""Exploratory projection, not a result: what the judged quantity would be under the member-scaled loading rule v0
(DELTA = 4 mm, D_max = 9 mm, levels at 0.08, 0.17, 0.32, 0.44, 0.56, 0.80, 1.0 of D_max) IF the surrogate made the same
relative end-displacement error at the same exact end displacement as the host's seed-2 model does in G-C2.1
(interpolated in the exact end displacement between the seven old levels, held constant outside them).
It isolates the effect of the smaller magnification; the surrogate of the new problem would be trained anew."""
import sys, json, glob
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
import numpy as np
from scipy.optimize import brentq
from common import *
from refcurve import points, curve
ids, par = eval_ids()
L, As, fyb = 80.0, 84.3, 880.0
x = json.load(open(paths.work() / "fit4.json"))["4.0"]["x"]; A = np.exp(x[:4]); p = float(np.exp(x[4]))
def modes(q):
    m = q["w"] / 2 - q["t_w"] / 2 - 0.8 * q["r"]; n = min(q["n"], 1.25 * m)
    Mpl = 0.25 * L * q["t_f"] ** 2 * q["fy"]; B = 4 * As * fyb
    return np.array([4 * Mpl / m, (2 * Mpl + n * B) / (m + n), B, q["t_w"] * L * q["fy"]])
def F_est(q): return float(((A * modes(q)) ** (-p)).sum() ** (-1 / p))
mech = {i: int(np.argmin(A * modes(par[i]))) for i in ids}
NAMES = ["mode 1 (flange)", "mode 2 (flange + bolt)", "mode 3 (bolt)", "web yielding"]
R = {json.loads(l)["iid"]: json.loads(l) for f in sorted(glob.glob(str(paths.work() / "cond/rows_*.jsonl"))) for l in open(f)}
DELTA, DMAX = 4.0, 9.0; FR = [0.08, 0.17, 0.32, 0.44, 0.56, 0.80, 1.0]
q_ = lambda v, pp: float(np.quantile(np.asarray(v, float), pp))
out = {"raw": [], "cond": []}
for i in ids:
    pts = points(i); C = curve(pts); em = max(pt[0] for pt in pts); lab = label(i)
    def Fx(e):
        return float(C(e)) if e <= em else float(C(em)) + max(float(C.derivative()(em)), 0.0) * (e - em)
    ks = F_est(par[i]) / (4 * DELTA)
    e_old = np.asarray(lab["e"], float)
    for key in ("raw", "cond"):
        err_old = np.array([r[key]["e_err"] for r in R[i]["rows"]])
        for fr in FR:
            D = fr * DMAX
            e = brentq(lambda t: t + Fx(t) / (4 * ks) - D, 0.0, D)
            err = float(np.interp(e, e_old, err_old))
            ep = e * (1 + err); Fp = 4 * ks * (D - ep)
            out[key].append(dict(iid=i, mech=mech[i], fr=fr, e=e, m=e / (D - e), err=err, c=Fp / Fx(ep) - 1, inside=e <= em + 1e-9))
for key in ("raw", "cond"):
    S = out[key]; c = np.abs([s["c"] for s in S])
    print(f"\n[{key} reading] projected under rule v0: median {100*q_(c,.5):.2f}%  p90 {100*q_(c,.9):.2f}%  over 10%: {int((c>.1).sum())} of {len(c)}  (pairs beyond the member's solved range: {sum(not s['inside'] for s in S)})")
    for fr in FR:
        cc = np.abs([s["c"] for s in S if s["fr"] == fr]); mm = [s["m"] for s in S if s["fr"] == fr]
        print(f"   level {fr:4.2f} D_max: median {100*q_(cc,.5):5.2f}%  p90 {100*q_(cc,.9):6.2f}%  over 10%: {int((cc>.1).sum()):2d} | magnification median {np.median(mm):.2f}")
    for k in (1, 0, 3):
        cc = np.abs([s["c"] for s in S if s["mech"] == k])
        print(f"   {NAMES[k]:24s}: median {100*q_(cc,.5):5.2f}%  p90 {100*q_(cc,.9):6.2f}%  over 10%: {int((cc>.1).sum()):2d} of {len(cc)}")
