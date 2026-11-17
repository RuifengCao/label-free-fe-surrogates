"""Audit of gate G-C2.2: one returned label solved again by the auditor.

For the members given, the instance is regenerated with the stamped library and solved at the seven levels as the
labels were (c2.data.solve_levels: increasing levels, each from the one before, the configured tolerance and
iteration limit). The result is compared with the returned label file and with the ledger.

Usage:  FEJOINT_SOLVER=legacy python -I -B a14_resolve_label.py STAMP RECORDS OUT.json MEMBER [MEMBER ...]
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
    from c2.data import export_member, solve_levels
    cfg = config()
    members = {m[0]: m[2] for m in d22.members(cfg)}
    led = {e["id"]: e for e in json.load(open(os.path.join(records, "ledger.json")))}
    ls = cfg["data"]["label_solver"]
    rows = []
    for iid in sys.argv[4:]:
        ex = export_member(cfg, members[iid])
        with np.load(os.path.join(records, "labels", iid + ".npz")) as z:
            ref = {k: z[k] for k in z.files}
        t0 = time.perf_counter()
        s = solve_levels(ex, [float(v) for v in ref["D"]], ls["tol"], ls["max_it"])
        rows.append({"id": iid, "seconds": round(time.perf_counter() - t0, 1), "bit_identical": bool(np.array_equal(s["z"], ref["z"])),
                     "max_z_difference_over_largest_unknown": float(np.abs(s["z"] - ref["z"]).max() / np.abs(ref["z"]).max()),
                     "max_rel_energy": float(np.max(np.abs(s["Pi"] / ref["Pi"] - 1))), "max_rel_force": float(np.max(np.abs(s["F"] / ref["F"] - 1))),
                     "max_abs_end_displacement_mm": float(np.abs(s["e"] - ref["e"]).max()),
                     "iterations": [int(i) for i in s["iterations"]], "ledger_iterations": led[iid]["iterations"],
                     "converged": [bool(c) for c in s["converged"]]})
        print(rows[-1], flush=True)
    json.dump(rows, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
