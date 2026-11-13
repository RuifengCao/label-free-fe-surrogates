"""A second route to the raw reading of a full-length run (section 10), as a check of the reading script.

The predictions that the training script wrote at its end (preds.npz, float32 fields at the seven judged levels) are
read with the stamped float64 reference code, judged against records/eval_ref.json, and compared pair by pair with
the rows that the reading script (dev/eval_state.py) wrote for the same model.

    python second_route.py PREDS_NPZ EVAL_JSON

The predictions are not kept in the repository; the printout of the run of seed 1 is records/logs/l6_second_route.log.
"""
import json
import os
import sys
import time

import numpy as np
from scipy.interpolate import PchipInterpolator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402
from common import KS, LEVELS, problem  # noqa: E402

preds_path, eval_json = sys.argv[1:3]
E = json.load(open(eval_json))
R = json.load(open(paths.work() / "eval_ref.json"))["members"]
rows = {(r["id"], r["D"]): r for r in E["rows"]}
P = np.load(preds_path)
ids = sorted(k for k in P.files if k.startswith("eval_"))
J2, dJ, de = [], [], []
t0 = time.time()
for iid in ids:
    prob, ex, q = problem(iid)
    m = R[iid]
    e_c = np.array(m["curve_e"])
    F_c = np.array(m["curve_F"])
    keep = np.concatenate([[True], np.diff(e_c) > 1e-9 * max(e_c.max(), 1.0)])
    c = PchipInterpolator(e_c[keep], F_c[keep], extrapolate=True)
    Z = np.asarray(P[iid], dtype=np.float64)
    for l, D in enumerate(LEVELS):
        e = float(prob.evaluate(Z[l], D)["e"])
        J = 4 * KS * (D - e) / float(c(e)) - 1
        row = rows[(iid, D)]
        J2.append(J)
        dJ.append(J - row["raw"]["J"])
        de.append(e / m["e"][l] - 1 - row["raw"]["e_err"])
J2 = np.abs(J2)
print(f"{E['name']}: members {len(ids)}, pairs {len(J2)}, {time.time() - t0:.0f} s")
print(f"second route, raw: median {100 * np.median(J2):.2f}%, 90th percentile {100 * np.percentile(J2, 90):.2f}%, above 10%: {int((J2 > 0.1).sum())}")
print(f"largest difference of the judged error to the reading script's rows: {np.abs(dJ).max():.2e}; of the end-displacement error: {np.abs(de).max():.2e}")
