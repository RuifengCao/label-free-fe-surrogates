"""Outside the rule of the stage-two trial: more views of the control and the two arms (condensed reading unless said).
   python3 -I stage2_extra.py CONTROL.json ARM1.json ARM2.json"""
import json
import os
import sys

WT = os.environ.get("F2_CODE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))   # the checkout this file lies in
sys.path[:0] = [WT + "/joint", WT + "/src"]
import numpy as np                                             # noqa: E402
from f2 import data as D, devconfig                            # noqa: E402

par = {i: q for i, _s, q in D.members(devconfig.config("fam128_bending_more"))}
names = ["control", "arm 1", "arm 2"]
ev = [json.load(open(p)) for p in sys.argv[1:4]]
M = [e["rows"]["0|condensed"]["members"] for e in ev]
ids = sorted(M[0])
assert all(sorted(m) == ids for m in M)


def arr(m, key, sel=None, lev=slice(None)):
    return np.array([[100.0 * d[key] for d in m[i][lev]] for i in ids if sel is None or sel(i)])


def stats(a):
    a = np.asarray(a).ravel()
    return f"{np.median(a):5.2f} / {np.percentile(a, 90):5.2f} / {a.max():5.1f}"


groups = {"all 31": None, "random 16": lambda i: i.startswith("eval_"), "picked 11": lambda i: i.startswith("dev_"),
          "tested 4": lambda i: i.startswith("tested_")}
print("moment at the same joint rotation, median / p90 / largest (%):")
for g, sel in groups.items():
    print(f"  {g:10s} " + " | ".join(f"{n}: {stats(arr(m, 'abs_curveD_err', sel))}" for n, m in zip(names, M)))
for key, label in (("abs_curve_err", "end rotation"), ("abs_M_err", "same device rotation")):
    print(f"{label}, all 31: " + " | ".join(f"{n}: {stats(arr(m, key))}" for n, m in zip(names, M)))
print("raw reading, all 31: " + " | ".join(
    f"{n}: {stats([[100.0 * d['abs_curveD_err'] for d in e['rows']['0|raw']['members'][i]] for i in ids])}" for n, e in zip(names, ev)))
bands = {"thin <12.5": lambda i: par[i].tp < 12.5, "mid": lambda i: 12.5 <= par[i].tp < 17.5, "thick >=17.5": lambda i: par[i].tp >= 17.5}
print("by thickness band: median of e at levels 1-2 | at levels 3-6 | at the last level:")
for b, sel in bands.items():
    print(f"  {b:12s} " + " | ".join(
        f"{n}: {np.median(arr(m, 'abs_curveD_err', sel, slice(0, 2))):.2f}  {np.median(arr(m, 'abs_curveD_err', sel, slice(2, 6))):.2f}  {np.median(arr(m, 'abs_curveD_err', sel, slice(6, 7))):.2f}"
        for n, m in zip(names, M)))
print("signed error, median by level (positive: surrogate too stiff):")
for n, m in zip(names, M):
    print(f"  {n:8s} " + " ".join(f"{v:+6.2f}" for v in np.median(arr(m, "curveD_err"), axis=0)))
print("joint rotation of the surrogate over the reference's at the same device rotation, median by level:")
for n, m in zip(names, M):
    r = np.array([[d["ThetaD"] / d["ThetaD_ref"] for d in m[i]] for i in ids])
    print(f"  {n:8s} " + " ".join(f"{v:6.3f}" for v in np.median(r, axis=0)))
c = arr(M[0], "abs_curveD_err")
for n, m in zip(names[1:], M[1:]):
    a = arr(m, "abs_curveD_err")
    print(f"{n} against the control, member by member: last level better in {(a[:, 6] < c[:, 6]).sum()} of 31; "
          f"levels 1-2 mean error better in {(a[:, :2].mean(1) < c[:, :2].mean(1)).sum()} of 31; "
          f"member maximum better in {(a.max(1) < c.max(1)).sum()} of 31; member median better in {(np.median(a, 1) < np.median(c, 1)).sum()} of 31")
    print(f"   points above 5 %: {(a > 5).sum()} (control {(c > 5).sum()}); above 10 %: {(a > 10).sum()} (control {(c > 10).sum()})")
top = lambda m: sorted(((float(arr(m, 'abs_curveD_err')[k].max()), ids[k]) for k in range(len(ids))), reverse=True)[:5]
for n, m in zip(names, M):
    print(f"largest by member, {n}: " + ", ".join(f"{i} {v:.1f}" for v, i in top(m)))
for n, m in zip(names, M):
    w = m["dev_W1"]
    print(f"W1 by level, {n}: " + " ".join(f"{100 * d['curveD_err']:+.1f}" for d in w))
