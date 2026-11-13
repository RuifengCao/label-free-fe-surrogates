"""Summary of respring_eval.py runs (argument: the directory with rows_*.jsonl): the condensed reading of the host's
seed-2 model under the old spring and under the member-scaled spring, at the same exact end displacements. Exploratory."""
import sys, json, glob
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
import numpy as np
from common import eval_ids
ids, par = eval_ids()
L, As, fyb = 80.0, 84.3, 880.0
x = json.load(open(paths.work() / "fit4.json"))["4.0"]["x"]; A = np.exp(x[:4]); p = float(np.exp(x[4]))
def modes(q):
    m = q["w"] / 2 - q["t_w"] / 2 - 0.8 * q["r"]; n = min(q["n"], 1.25 * m)
    Mpl = 0.25 * L * q["t_f"] ** 2 * q["fy"]; B = 4 * As * fyb
    return np.array([4 * Mpl / m, (2 * Mpl + n * B) / (m + n), B, q["t_w"] * L * q["fy"]])
mech = {i: int(np.argmin(A * modes(par[i]))) for i in ids}
NAMES = ["mode 1 (flange)", "mode 2 (flange + bolt)", "mode 3 (bolt)", "web yielding"]
d = sys.argv[1]
R = [json.loads(l) for f in sorted(glob.glob(d + "/rows_*.jsonl")) for l in open(f)]
X = [dict(iid=r["iid"], mech=mech[r["iid"]], **x) for r in R for x in r["rows"]]
frs = sorted({x["fr"] for x in X})
print(f"members {len(R)}; pairs inside the trained range {len(X)} of {len(R) * len(frs)} asked (levels {frs})")
q = lambda v, pp: float(np.quantile(np.asarray(v, float), pp)) if len(v) else float("nan")
def line(tag, S, n_asked=None):
    if not S: print(f"{tag}: none"); return
    a = lambda k: np.abs([s[k] for s in S])
    co, cn, ro, rn = a("J_cond_old"), a("J_cond_new"), a("J_raw_old"), a("J_raw_new")
    print(f"{tag:30s} n {len(S):3d}" + (f" of {n_asked}" if n_asked else "") + f" | condensed, new spring: med {100*q(cn,.5):5.2f} p90 {100*q(cn,.9):6.2f} >10%: {int((cn>.1).sum()):3d} | condensed, old spring at the same e*: med {100*q(co,.5):5.2f} p90 {100*q(co,.9):6.2f} >10%: {int((co>.1).sum()):3d}"
          f" | raw, new spring, same e error: med {100*q(rn,.5):5.2f} p90 {100*q(rn,.9):6.2f} >10%: {int((rn>.1).sum()):3d} | raw old: p90 {100*q(ro,.9):6.2f} >10%: {int((ro>.1).sum()):3d} | m old/new med {np.median([s['m_old'] for s in S]):.2f}/{np.median([s['m_new'] for s in S]):.2f} | e* med {np.median([s['es'] for s in S]):.2f}")
line("all pairs inside the range", X, len(R) * len(frs))
for fr in frs: line(f"  level {fr:.2f} of D_max", [s for s in X if s["fr"] == fr], len(R))
for k in (1, 0, 3):
    S = [s for s in X if s["mech"] == k]; nm = sum(1 for r in R if mech[r["iid"]] == k)
    line(f"{NAMES[k]} ({nm} members)", S, nm * len(frs))
dd = np.abs(np.array([s["J_cond_new"] for s in X]) - np.array([s["J_cond_old"] for s in X]))
print("condensed, new minus old spring, percentage points: median %.3f p90 %.3f max %.3f" % tuple(100 * np.quantile(dd, t) for t in (.5, .9, 1)))
mo = np.array([s["m_old"] for s in X]); mn = np.array([s["m_new"] for s in X])
print("magnification new/old: min %.2f median %.2f max %.2f" % ((mn / mo).min(), np.median(mn / mo), (mn / mo).max()))
miss = {fr: len(R) - sum(1 for s in X if s["fr"] == fr) for fr in frs}; print("pairs outside the range by level:", miss)
missm = {NAMES[k]: sum(1 for r in R if mech[r["iid"]] == k) * len(frs) - sum(1 for s in X if s["mech"] == k) for k in (1, 0, 3)}; print("pairs outside the range by mechanism:", missm)
print("slopes left by the 1-D solve (|dPi/da|): old spring median %.1e max %.1e; new spring median %.1e max %.1e" % (np.median(np.abs([s["g_old"] for s in X])), np.max(np.abs([s["g_old"] for s in X])), np.median(np.abs([s["g_new"] for s in X])), np.max(np.abs([s["g_new"] for s in X]))))
