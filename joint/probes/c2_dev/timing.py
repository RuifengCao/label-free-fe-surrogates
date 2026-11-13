import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
import time, numpy as np
from common import *
v = verdict()
ids, par = eval_ids()
iid = ids[0]
P, ex, q = problem(iid)
lab = label(iid)
pr = preds("label_free_s1")[iid].astype(np.float64)
rows = v["arms"]["label_free"]["1"]["eval_rows"][iid]
for l in (0, 6):
    D = float(lab["D"][l])
    t0 = time.perf_counter(); e = P.evaluate(lab["z"][l], D); t1 = time.perf_counter() - t0
    print("label level", D, "Pi", e["Pi"], "stored", float(lab["Pi"][l]), "rel diff", e["Pi"] / float(lab["Pi"][l]) - 1, "F", e["F"], float(lab["F"][l]), "F_sigma", e["F_sigma"], "time", round(t1, 3))
    t0 = time.perf_counter(); e2 = P.evaluate(pr[l], D); t2 = time.perf_counter() - t0
    gap = (e2["Pi"] - float(lab["Pi"][l])) / abs(float(lab["Pi"][l]))
    print("  pred: gap", gap, "recorded", rows[l]["gap"], "F_sigma_err", e2["F_sigma"] / float(lab["F"][l]) - 1, "recorded", rows[l]["F_sigma_err"], "e_err", pr[l][P.e_idx] / float(lab["e"][l]) - 1, rows[l]["e_err"], "time", round(t2, 3))
t0 = time.perf_counter(); c = P.solve_at_e(float(pr[6][P.e_idx]), z0=lab["z"][6]); t3 = time.perf_counter() - t0
F = 4 * P.k_s * (8.0 - float(pr[6][P.e_idx]))
print("solve_at_e: F*", c["F"], "converged", c["converged"], "curve_err", F / c["F"] - 1, "recorded", rows[6]["curve_err"], "time", round(t3, 2))
print("params", par[iid], "n_z", P.n_z)
