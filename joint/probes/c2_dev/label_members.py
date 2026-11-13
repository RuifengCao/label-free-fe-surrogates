"""R0-a: exact solutions of chosen training members at the gate's seven evaluation levels, with the stamped code and
the gate's solver settings (tol 1e-12, at most 80 iterations)."""
import sys, json, time
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
sys.path.insert(0, str(paths.joint()))
import numpy as np
from pathlib import Path
from c2.config import config
from c2.data import load_export, solve_levels
cfg = config()
lv = cfg["data"]["eval_levels_mm"]
part, nparts = int(sys.argv[1]), int(sys.argv[2])
order = json.load(open(paths.work() / "selection.json"))["order"][part::nparts]
out = Path(paths.work() / "labels")
for iid in order:
    p = out / f"{iid}.npz"
    if p.exists(): continue
    ex, q = load_export(Path(paths.data() / "inst") / f"{iid}.npz")
    t0 = time.perf_counter()
    s = solve_levels(ex, lv, 1e-12, 80)
    tmp = Path(str(p) + ".tmp")
    with open(tmp, "wb") as fh:
        np.savez_compressed(fh, D=s["D"], z=s["z"], Pi=s["Pi"], e=s["e"], F=s["F"], F_sigma=s["F_sigma"], bolt_N=s["bolt_N"])
    tmp.replace(p)
    worst = max(max(abs(r[k]) for k in r) for r in s["kkt"])
    with open(paths.work() / f"out/label_log_{part}.jsonl", "a") as fh:
        fh.write(json.dumps({"id": iid, "seconds": round(time.perf_counter() - t0, 1), "converged": [bool(c) for c in s["converged"]],
                             "iterations": [int(i) for i in s["iterations"]], "F_vs_F_sigma": float(np.max(np.abs(s["F"] - s["F_sigma"]) / np.abs(s["F"]))), "kkt_worst_abs": float(worst)}) + "\n")
