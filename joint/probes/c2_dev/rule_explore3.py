import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
import numpy as np, json
from scipy.optimize import least_squares
from common import *
from refcurve import points, curve
ids, par = eval_ids()
L, As, fyb = 80.0, 84.3, 880.0
C = {i: curve(points(i)) for i in ids}
emax = {i: max(p[0] for p in points(i)) for i in ids}
P = {k: np.array([par[i][k] for i in ids]) for k in ("t_f", "t_w", "r", "w", "n", "fy", "rho")}
m = P["w"] / 2 - P["t_w"] / 2 - 0.8 * P["r"]; n = np.minimum(P["n"], 1.25 * m)
Mpl = 0.25 * L * P["t_f"] ** 2 * P["fy"]; B = 4 * As * fyb
MODES = np.stack([4 * Mpl / m, (2 * Mpl + n * B) / (m + n), np.full(len(ids), B), P["t_w"] * L * P["fy"]], axis=1)
def est(x, M):
    a = np.exp(x[:4]); p = np.exp(x[4])
    return (((a * M) ** (-p)).sum(axis=1)) ** (-1 / p)
out = {}
for et in (2.0, 3.0, 4.0, 5.0):
    sel0 = np.array([emax[i] >= et - 0.08 for i in ids])
    F = np.array([float(C[i](et)) if s else np.nan for i, s in zip(ids, sel0)])
    M, Fv = MODES[sel0], F[sel0]
    best = None
    for p0 in (1.0, 2.0, 4.0, 8.0):
        res = least_squares(lambda x: np.log(est(x, M)) - np.log(Fv), x0=[0.4, 0.2, 0.05, 0.1, np.log(p0)], bounds=([-1, -1, -1, -1, np.log(0.5)], [2, 2, 2, 2, np.log(20)]))
        if best is None or res.cost < best.cost: best = res
    rr = Fv / est(best.x, M); loo = []
    for k in range(len(Fv)):
        s = np.arange(len(Fv)) != k
        rk = least_squares(lambda x: np.log(est(x, M[s])) - np.log(Fv[s]), x0=best.x, bounds=([-1, -1, -1, -1, np.log(0.5)], [2, 2, 2, 2, np.log(20)]))
        loo.append(Fv[k] / est(rk.x, M[k:k+1])[0])
    loo = np.array(loo)
    gov = (np.exp(best.x[:4]) * M).argmin(axis=1)
    print(f"e_t = {et}: {len(Fv)} members; factors on modes 1-4: {np.round(np.exp(best.x[:4]), 3)}, exponent {np.exp(best.x[4]):.2f}; fit sd of log {np.log(rr).std():.3f} (ratio {rr.min():.2f} to {rr.max():.2f}); leave-one-out sd {np.log(loo).std():.3f} ({loo.min():.2f} to {loo.max():.2f}); governing mode counts {np.bincount(gov, minlength=4)}")
    out[str(et)] = {"x": [float(v) for v in best.x], "sd": float(np.log(rr).std()), "loo_sd": float(np.log(loo).std()), "loo_min": float(loo.min()), "loo_max": float(loo.max()), "n": int(len(Fv))}
json.dump(out, open(paths.work() / "fit4.json", "w"), indent=1)
