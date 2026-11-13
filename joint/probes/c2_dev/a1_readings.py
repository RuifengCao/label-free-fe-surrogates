"""Exploratory re-reading of G-C2.1's returned records by arithmetic alone (no solve, no training).
Readings of a predicted field's point on the force-deformation plane:
  R0 (the gate's): (e_pred, F_spring), F_spring = 4 k_s (D - e_pred)            -> recorded curve_err
  R1b:             (e_pred, F_sigma), F_sigma the stress reading of the field    -> F_sigma / F*(e_pred) - 1, exact
F*(e_pred) is recovered from the recorded rows: F*(e_pred) = F_spring / (1 + curve_err)."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
import json, numpy as np
from common import *

v = verdict()
ids, par = eval_ids()
out = {}
def q(x, p): return float(np.quantile(np.asarray(x, float), p))
for arm in ("label_free", "supervised_64"):
    for seed in ("0", "1", "2"):
        rows = v["arms"][arm][seed]["eval_rows"]
        rec = []
        for iid in ids:
            lab = label(iid)
            for l, r in enumerate(rows[iid]):
                D, er, Fr = float(lab["D"][l]), float(lab["e"][l]), float(lab["F"][l])
                ep = er * (1 + r["e_err"]); Fs = 4 * KS * (D - ep)
                Fsig = Fr * (1 + r["F_sigma_err"]) if r["F_sigma_err"] == r["F_sigma_err"] else float("nan")
                ce = r["curve_err"]
                Fstar = Fs / (1 + ce) if np.isfinite(ce) else float("nan")
                r1b = Fsig / Fstar - 1 if np.isfinite(Fstar) else float("inf")
                rec.append(dict(iid=iid, l=l, D=D, fy=par[iid]["fy"], rho=par[iid]["rho"], tf=par[iid]["t_f"], e_ref=er, F_ref=Fr, e_pred=ep,
                                R0=abs(ce), R0s=ce, R1b=abs(r1b), R1bs=r1b, e_err=r["e_err"], F_err=r["F_err"], Fsig_err=r["F_sigma_err"],
                                gap=r["gap"], bound=r["bound"], m=er / (D - er), u=r["u_rel_l2"]))
        out[(arm, seed)] = rec
        a = lambda k: np.array([x[k] for x in rec], float)
        print(f"\n=== {arm} seed {seed}: 448 pairs ===")
        print(f" R0  (gate, spring reading): median {q(a('R0'),.5)*100:8.2f}%  p90 {q(a('R0'),.9)*100:9.2f}%")
        fin = np.where(np.isfinite(a('R1b')), a('R1b'), 1e9)
        print(f" R1b (e_pred, stress force): median {q(fin,.5)*100:8.2f}%  p90 {q(fin,.9)*100:9.2f}%   (signed median {q(np.where(np.isfinite(a('R1bs')),a('R1bs'),1e9),.5)*100:+.2f}%)")
        print("  level:   |R0| med/p90      |R1b| med/p90     |e_err| med   |F_err sameD| med  |Fsig_err| med/p90   gap med    m=e/(D-e) med")
        for D in LEVELS:
            s = a('D') == D
            f = fin[s]
            print(f"  D={D:4.1f}  {q(a('R0')[s],.5)*100:7.2f} {q(a('R0')[s],.9)*100:8.2f}   {q(f,.5)*100:7.2f} {q(f,.9)*100:8.2f}    {q(abs(a('e_err')[s]),.5)*100:7.2f}      {q(abs(a('F_err')[s]),.5)*100:7.2f}        {q(abs(a('Fsig_err')[s]),.5)*100:7.2f} {q(abs(a('Fsig_err')[s]),.9)*100:7.2f}   {q(a('gap')[s],.5)*100:7.3f}   {q(a('m')[s],.5):6.2f}")
json.dump({f"{k[0]}_s{k[1]}": val for k, val in out.items()}, open(paths.work() / "tail" / "a1_rows.json", "w"))
