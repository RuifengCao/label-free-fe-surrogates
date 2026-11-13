"""The judged error of G-C2.1's label-free seeds against the error of the end displacement times e/(D - e), from the
returned rows alone (written for this note; arithmetic only, no solve).

The gate reads the force of a predicted point from the spring, F = 4 k_s (D - e). An end displacement that is off by
the relative error x therefore puts the force off by -x e/(D - e); on a flat part of the reference curve that is the
judged error. Prints, for seeds 1 and 2: the correlation of the two and the median of their ratio at 4, 6 and 8 mm;
the factor e/(D - e) of the reference at 8 mm; the pairs with fy < 300 MPa at 6 and 8 mm against all the others.

    python -I magnification.py
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
import json

import numpy as np

v = json.load(open(paths.ret() / "verdict.json"))
ref = json.load(open(paths.work() / "eval_ref.json"))["members"]
LEVELS = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
q = lambda x, p: 100 * float(np.quantile(np.abs(x), p))

m8 = np.array([m["e"][6] / (8.0 - m["e"][6]) for m in ref.values()])
F8 = np.array([m["F"][6] for m in ref.values()])
print(f"reference at 8 mm, {len(m8)} members: e/(D - e) from {m8.min():.2f} to {m8.max():.2f}, median {np.median(m8):.2f};"
      f" above 1.5 in {int((m8 > 1.5).sum())}, above 2.5 in {int((m8 > 2.5).sum())}; force {F8.min() / 1e3:.0f} to {F8.max() / 1e3:.0f} kN;"
      f" correlation of log factor and log force {np.corrcoef(np.log(m8), np.log(F8))[0, 1]:.3f}")
for seed in ("1", "2"):
    rows = v["arms"]["label_free"][seed]["eval_rows"]
    print(f"\nlabel-free seed {seed}")
    for l in (4, 5, 6):
        J = np.array([rows[i][l]["curve_err"] for i in rows])
        X = np.array([-ref[i]["e"][l] / (LEVELS[l] - ref[i]["e"][l]) * rows[i][l]["e_err"] for i in rows])
        print(f"   D = {LEVELS[l]:.0f} mm: correlation {np.corrcoef(J, X)[0, 1]:.4f}; judged error over the product, median {np.median(J / X):.3f}")
    weak = [(i, l) for i in rows for l in (5, 6) if ref[i]["params"]["fy"] < 300]
    rest = [(i, l) for i in rows for l in range(7) if (i, l) not in set(weak)]
    for name, S in (("fy < 300 MPa, 6 and 8 mm", weak), ("all other pairs", rest)):
        J = np.array([rows[i][l]["curve_err"] for i, l in S]); E = np.array([rows[i][l]["e_err"] for i, l in S])
        G = np.array([rows[i][l]["gap"] for i, l in S])
        print(f"   {name}: {len(S)} pairs; judged error median {q(J, .5):.2f}%, 90th percentile {q(J, .9):.2f}%, above 10% in {int((np.abs(J) > 0.1).sum())};"
              f" end displacement too small in {int((E < 0).sum())}, median error {100 * float(np.median(E)):+.1f}%; energy gap median {100 * float(np.median(G)):.2f}%")
