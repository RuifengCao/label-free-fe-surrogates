"""Audit of gate G-C2.2, item 1b, a control: does the judged error depend on how the exact solve is started?

The gate's metric starts the solve at the predicted end displacement from the returned label nearest in e. The
problem is convex, so the reference force F*(e) should not depend on the start. For the pairs given, this script
solves again from zero (no label enters the solve at all) and compares the judged error with the returned one.

Usage:  FEJOINT_SOLVER=legacy python -I -B a13_cold_start.py STAMP RECORDS OUT.json SEED:READING:MEMBER:LEVEL [...]
"""
import json
import os
import sys
import time

import numpy as np


def main():
    stamp, records, out = sys.argv[1:4]
    sys.path.insert(0, os.path.join(stamp, "joint"))
    from c22.config import config
    from c22 import data as d22
    from c2.data import export_member
    from c2.instance import ExportedProblem
    cfg = config()
    members = {m[0]: m[2] for m in d22.members(cfg)}
    v = json.load(open(os.path.join(records, "verdict.json")))
    files = {"condensed": "preds_condensed.npz", "raw": "preds.npz"}
    rows = []
    for spec in sys.argv[4:]:
        seed, reading, iid, l = spec.split(":")
        l = int(l)
        ex = export_member(cfg, members[iid])
        P = ExportedProblem(ex)
        z = np.load(os.path.join(records, "run_files", f"label_free_s{seed}", files[reading]))[iid][l].astype(np.float64)
        D = float(cfg["data"]["eval_levels_mm"][l])
        e = float(z[int(ex["e_idx"])])
        F = 4.0 * float(ex["k_s"]) * (D - e)
        t0 = time.perf_counter()
        c = P.solve_at_e(e, z0=None)
        st = "eval" if iid.startswith("eval") else ("former" if iid.startswith("former") else "tested")
        ret = v["readings"][reading][seed][f"{st}_rows"][iid][l]["curve_err"]
        rows.append({"pair": spec, "converged": bool(c["converged"]), "curve_err_cold_start": F / c["F"] - 1, "returned": ret,
                     "difference": F / c["F"] - 1 - ret, "seconds": round(time.perf_counter() - t0, 1)})
        print(rows[-1], flush=True)
    json.dump(rows, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
