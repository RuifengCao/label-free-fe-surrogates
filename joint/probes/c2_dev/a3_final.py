import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
import json, glob, numpy as np
from common import *
q = lambda x, p: float(np.quantile(np.asarray(x, float), p)) if len(x) else float("nan")
ids, par = eval_ids()
A1 = json.load(open(paths.work() / "tail" / "a1_rows.json"))
out = {}
for seed in (1, 2):
    base = {(x["iid"], x["l"]): x for x in A1[f"label_free_s{seed}"]}
    R = [json.loads(l) for f in glob.glob(str(paths.work() / "tail" / f"a3_s{seed}_p*.jsonl")) for l in open(f)]
    for dn in ("tan", "load", "amp"):
        S = {(r["iid"], r["l"]): r for r in R if r["dir"] == dn}
        if not S: continue
        keys = sorted(S); n = len(keys)
        b = lambda k: np.array([base[kk][k] for kk in keys], float)
        a = lambda k: np.array([S[kk][k] for kk in keys], float)
        D, fy, m = b("D"), b("fy"), b("m")
        r0, r1 = np.abs(a("curve_err0")), np.abs(a("curve_err"))
        assert np.allclose(r0, b("R0"), rtol=1e-9, atol=1e-12)
        hyp = np.where((D >= 4) & (m > 1.5), r1 * 1.5 / m, r1)
        print(f"\n=== seed {seed}, direction {dn}: {n} pairs ({len(set(k[0] for k in keys))} members) ===")
        print(f"  all        before: median {100*q(r0,.5):6.2f}%  p90 {100*q(r0,.9):6.2f}%  over10 {int((r0>.1).sum()):3d} | after: median {100*q(r1,.5):6.2f}%  p90 {100*q(r1,.9):6.2f}%  over10 {int((r1>.1).sum()):3d}  max {100*r1.max():.0f}%")
        print(f"  gap median {100*q(a('gap0'),.5):.3f}% -> {100*q(a('gap'),.5):.3f}% ; |e_err| median {100*q(np.abs(a('e_err0')),.5):.2f}% -> {100*q(np.abs(a('e_err')),.5):.2f}% , p90 {100*q(np.abs(a('e_err0')),.9):.2f}% -> {100*q(np.abs(a('e_err')),.9):.2f}% ; evals median {np.median(a('n_eval')):.0f}, max {a('n_eval').max():.0f}; pairs where the slope fell by less than 100x: {int((a('slope_red') > 1e-2).sum())}")
        for D0 in LEVELS:
            s = D == D0
            print(f"   D={D0:3.1f}: {100*q(r0[s],.5):6.2f} / {100*q(r0[s],.9):6.2f}  ->  {100*q(r1[s],.5):6.2f} / {100*q(r1[s],.9):6.2f}    |e_err| med {100*q(np.abs(a('e_err0'))[s],.5):5.2f} -> {100*q(np.abs(a('e_err'))[s],.5):5.2f}   p90 {100*q(np.abs(a('e_err0'))[s],.9):5.2f} -> {100*q(np.abs(a('e_err'))[s],.9):5.2f}   gap med {100*q(a('gap0')[s],.5):5.2f} -> {100*q(a('gap')[s],.5):5.2f}")
        for name, s in (("fy<300 and D>=6", (fy < 300) & (D >= 6)), ("m>1.5", m > 1.5), ("m<=1.5", m <= 1.5), ("fy>=345", fy >= 345)):
            print(f"   {name:16s} ({int(s.sum()):3d}): median {100*q(r0[s],.5):6.2f} -> {100*q(r1[s],.5):6.2f}%   p90 {100*q(r0[s],.9):6.2f} -> {100*q(r1[s],.9):6.2f}%   over10 {int((r0[s]>.1).sum())} -> {int((r1[s]>.1).sum())}   |e_err| med {100*q(np.abs(a('e_err0'))[s],.5):.2f} -> {100*q(np.abs(a('e_err'))[s],.5):.2f}%")
        print(f"  hypothetical (first order, same e errors): corrected reading and magnification capped at 1.5 for D>=4: median {100*q(hyp,.5):.2f}%  p90 {100*q(hyp,.9):.2f}%  over10 {int((hyp>.1).sum())}")
        worse = int((r1 > r0 * 1.2 + 0.01).sum()); better = int((r1 < r0 / 1.2 - 0.01).sum())
        print(f"  pairs clearly better {better}, clearly worse {worse}")
        out[f"s{seed}_{dn}"] = dict(n=n, med0=q(r0,.5), p900=q(r0,.9), med1=q(r1,.5), p901=q(r1,.9), over0=int((r0>.1).sum()), over1=int((r1>.1).sum()))
json.dump(out, open(paths.work() / "tail" / "a3_final.json", "w"), indent=1)
