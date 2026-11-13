import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
import json, glob, numpy as np
from common import *
q = lambda x, p: float(np.quantile(np.asarray(x, float), p)) if len(x) else float("nan")
ids, par = eval_ids()
for seed in (1, 2):
    R = [json.loads(l) for f in glob.glob(str(paths.work() / "tail" / f"a3_s{seed}_p*.jsonl")) for l in open(f)]
    for dn in ("tan", "amp"):
        S = [r for r in R if r["dir"] == dn]
        if not S: continue
        mem = sorted({r["iid"] for r in S}); full = [m for m in mem if sum(1 for r in S if r["iid"] == m) == 7]
        S = [r for r in S if r["iid"] in full]
        a = lambda k: np.array([r[k] for r in S], float)
        print(f"\nseed {seed} dir {dn}: {len(full)} members complete, {len(S)} pairs")
        print(f"  distance from curve  before: median {100*q(abs(a('curve_err0')),.5):6.2f}%  p90 {100*q(abs(a('curve_err0')),.9):6.2f}%   after: median {100*q(abs(a('curve_err')),.5):6.2f}%  p90 {100*q(abs(a('curve_err')),.9):6.2f}%   max {100*abs(a('curve_err')).max():.1f}%")
        print(f"  gap before median {100*q(a('gap0'),.5):.3f}% p90 {100*q(a('gap0'),.9):.3f}%  after median {100*q(a('gap'),.5):.3f}% p90 {100*q(a('gap'),.9):.3f}%;  evals median {np.median(a('n_eval')):.0f} max {a('n_eval').max():.0f}; worst slope reduction {a('slope_red').max():.1e}")
        print("   level   before med/p90     after med/p90    |e_err| b/a med     |Fsig_err| after med   gap b/a med    |bolt_err| b/a med")
        for D in LEVELS:
            s = a('D') == D
            print(f"   D={D:3.1f}  {100*q(abs(a('curve_err0'))[s],.5):6.2f} {100*q(abs(a('curve_err0'))[s],.9):7.2f}   {100*q(abs(a('curve_err'))[s],.5):6.2f} {100*q(abs(a('curve_err'))[s],.9):7.2f}    {100*q(abs(a('e_err0'))[s],.5):5.2f} {100*q(abs(a('e_err'))[s],.5):5.2f}        {100*q(abs(a('Fsig_err'))[s],.5):6.2f}          {100*q(a('gap0')[s],.5):5.3f} {100*q(a('gap')[s],.5):5.3f}    {100*q(abs(a('bolt_err0'))[s],.5):5.2f} {100*q(abs(a('bolt_err'))[s],.5):5.2f}")
