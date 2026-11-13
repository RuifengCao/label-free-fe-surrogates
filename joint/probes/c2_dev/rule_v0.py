"""R0-b, step 2: a member-scaled loading rule for the T-stubs, tried on the 64 development members.
F_est(q): smooth minimum of four scaled closed-form mechanisms (EN 1993-1-8 modes 1 to 3 of the T-stub, and yielding of
the web), constants fitted at an end displacement of 4 mm.  k_s(q) = F_est(q) / (4 DELTA) per quarter model, D_max the same
for every member."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
import numpy as np, json
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
C = {i: curve(points(i)) for i in ids}; emax = {i: max(pt[0] for pt in points(i)) for i in ids}
FR = [0.0625, 0.125, 0.25, 0.375, 0.5, 0.75, 1.0]
q10 = lambda v, pp: float(np.quantile(np.asarray(v, float), pp))
print("constants: factors", np.round(A, 3), "exponent", round(p, 2))
for DELTA, ET in ((4.0, 5.0), (3.2, 4.0), (5.0, 5.0)):
    DMAX = ET + DELTA
    rows = []
    for i in ids:
        ks = F_est(par[i]) / (4 * DELTA)
        def Fx(e, i=i):                                  # the curve, continued beyond its last exact point with its last slope
            em = emax[i]
            return float(C[i](e)) if e <= em else float(C[i](em)) + max(float(C[i].derivative()(em)), 0.0) * (e - em)
        g = lambda e, D: e + Fx(e) / (4 * ks) - D
        r = {"id": i, "ks": ks}
        for fr in FR:
            D = fr * DMAX
            e = brentq(g, 0.0, D, args=(D,))
            r[fr] = (e, e / (D - e), e <= emax[i] + 1e-9)
        rows.append(r)
    ks = np.array([r["ks"] for r in rows]) / 1e3
    print(f"\nspring stretch at the estimate DELTA = {DELTA} mm, D_max = {DMAX} mm: k_s from {ks.min():.1f} to {ks.max():.1f} kN/mm per quarter (median {np.median(ks):.1f}; G-C2.1: 20)")
    print("   level D (mm) | end displacement e: min / median / max | factor e/(D-e): min / median / p90 / max | members beyond their solved range")
    for fr in FR:
        e = np.array([r[fr][0] for r in rows]); m = np.array([r[fr][1] for r in rows]); out = sum(not r[fr][2] for r in rows)
        print(f"   {fr*DMAX:6.3f}       | {e.min():5.2f} / {np.median(e):5.2f} / {e.max():5.2f}            | {m.min():5.2f} / {np.median(m):5.2f} / {q10(m,.9):5.2f} / {m.max():5.2f}                  | {out}")
