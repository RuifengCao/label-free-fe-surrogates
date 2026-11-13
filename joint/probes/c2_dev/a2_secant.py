"""Secant-energy (Castigliano) reading from the returned records, arithmetic only:
mean force over [D_k, D_k+1] = 4 (Pi_k+1 - Pi_k) / (D_k+1 - D_k), for the network's energies and the exact ones."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
import numpy as np
from common import *
v = verdict(); ids, par = eval_ids()
q = lambda x, p: float(np.quantile(np.asarray(x, float), p))
for seed in ("1", "2"):
    rows = v["arms"]["label_free"][seed]["eval_rows"]
    print(f"\nlabel_free seed {seed}: secant-energy force over each interval, relative error against the exact secant")
    allv = []
    for k in range(6):
        errs = []; r0 = []
        for iid in ids:
            lab = label(iid)
            P0, P1 = float(lab["Pi"][k]), float(lab["Pi"][k + 1])
            G0, G1 = rows[iid][k]["gap"] * P0, rows[iid][k + 1]["gap"] * P1
            errs.append((G1 - G0) / (P1 - P0)); r0.append(max(abs(rows[iid][k]["curve_err"]), abs(rows[iid][k + 1]["curve_err"])))
        allv += errs
        print(f"  [{LEVELS[k]:3.1f},{LEVELS[k+1]:3.1f}] mm: |err| median {100*q(np.abs(errs),.5):6.2f}%  p90 {100*q(np.abs(errs),.9):6.2f}%  max {100*np.max(np.abs(errs)):6.2f}%   signed median {100*q(errs,.5):+.2f}%")
    print(f"  all 384 intervals: median {100*q(np.abs(allv),.5):.2f}%  p90 {100*q(np.abs(allv),.9):.2f}%")
