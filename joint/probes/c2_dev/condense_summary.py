"""Summary of condense_eval.py: the judged quantity of G-C2.1 (distance from the reference curve) for the host's final
label-free model of seed 2 on the 64 former held-out members, raw field against amplitude-condensed field, overall, by
level and by governing mechanism (closed-form estimate at 4 mm, fit4.json). Exploratory."""
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
NAMES = ["mode 1 (flange)", "mode 2 (flange + bolt)", "mode 3 (bolt)", "web yielding"]
mech = {i: int(np.argmin(A * modes(par[i]))) for i in ids}
R = [json.loads(l) for f in sorted(glob.glob(str(paths.work() / "cond/rows_*.jsonl"))) for l in open(f)]
print("members done:", len(R), "of", len(ids), "| seconds per member median", np.median([r["seconds"] for r in R]), "| energy evaluations per member", sorted({r["evals"] for r in R}))
rows = [dict(iid=r["iid"], mech=mech[r["iid"]], **x) for r in R for x in r["rows"]]
q = lambda v, pp: float(np.quantile(np.asarray(v, float), pp)) if len(v) else float("nan")
def line(tag, S):
    if not S: return
    c0 = np.abs([s["raw"]["curve_err"] for s in S]); c1 = np.abs([s["cond"]["curve_err"] for s in S])
    e0 = np.abs([s["raw"]["e_err"] for s in S]); e1 = np.abs([s["cond"]["e_err"] for s in S])
    g0 = np.array([s["raw"]["gap"] for s in S]); g1 = np.array([s["cond"]["gap"] for s in S])
    b0 = np.abs([s["raw"]["bolt_err"] for s in S]); b1 = np.abs([s["cond"]["bolt_err"] for s in S])
    print(f"{tag:34s} n {len(S):3d} | curve dist med/p90: raw {100*q(c0,.5):6.2f} {100*q(c0,.9):6.2f}  cond {100*q(c1,.5):6.2f} {100*q(c1,.9):6.2f} | >10%: {int((c0>.1).sum()):3d} -> {int((c1>.1).sum()):3d} | |e err| med: {100*q(e0,.5):5.2f} -> {100*q(e1,.5):5.2f} | gap med: {100*q(g0,.5):5.2f} -> {100*q(g1,.5):5.2f} | |bolt err| med: {100*q(b0,.5):5.2f} -> {100*q(b1,.5):5.2f} | worse after: {int((c1>c0+1e-4).sum())}")
line("all pairs", rows)
for D in (0.5, 1, 2, 3, 4, 6, 8):
    line(f"  D = {D}", [s for s in rows if s["D"] == D])
for k in (1, 0, 3):
    S = [s for s in rows if s["mech"] == k]
    line(f"{NAMES[k]} ({len({s['iid'] for s in S})} members)", S)
    line("    D = 6, 8", [s for s in S if s["D"] >= 6])
    line("    D = 3, 4", [s for s in S if 3 <= s["D"] <= 4])
a = np.array([s["a"] for s in rows]); D = np.array([s["D"] for s in rows])
print("amplitude a: min %.3f median %.3f max %.3f; at D >= 6: min %.3f median %.3f max %.3f; at the clamp (0.5 or 3.0): %d" % (a.min(), np.median(a), a.max(), a[D >= 6].min(), np.median(a[D >= 6]), a[D >= 6].max(), int(((a <= 0.5001) | (a >= 2.9999)).sum())))
# members: worst pairs after condensation
W = sorted(rows, key=lambda s: -abs(s["cond"]["curve_err"]))[:12]
print("worst after condensation:")
for s in W: print(f"   {s['iid']} D {s['D']:3.1f} {NAMES[s['mech']]:24s} raw {100*s['raw']['curve_err']:+7.2f}% cond {100*s['cond']['curve_err']:+7.2f}%  a {s['a']:.3f}  e err {100*s['raw']['e_err']:+6.1f} -> {100*s['cond']['e_err']:+6.1f}  bolt err {100*s['raw']['bolt_err']:+6.1f} -> {100*s['cond']['bolt_err']:+6.1f}")
json.dump({"n_members": len(R)}, open(paths.work() / "cond/summary_stub.json", "w"))
