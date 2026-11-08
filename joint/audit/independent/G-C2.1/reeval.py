"""Independent re-evaluation of chosen held-out pairs of G-C2.1 with the stamped reference code (not the author's
script, not c2.evaluate.metrics): the instance regenerated with the stamped code, the problem rebuilt from it
(c2.instance.ExportedProblem), an exact solve at the predicted end displacement (solve_at_e, warm start from the label
nearest in e) for the distance from the curve, and the energy readings of every run from ExportedProblem.evaluate.
Usage (BLAS threads 1, FEJOINT_SOLVER=legacy):
    python -I -B reeval.py JOINT RECORDS INST_DIR OUT_JSON  member:run1+run2:levels  [member:...]
levels as comma-free indices, e.g. 0123456, or '-' for no curve solves (energy readings only, every run)."""
import json
import math
import sys
import time
from pathlib import Path

JOINT, REC, INST, OUT = sys.argv[1:5]
JOBS = sys.argv[5:]
sys.path.insert(0, JOINT)
import numpy as np  # noqa: E402
from c2.data import load_export  # noqa: E402
from c2.instance import ExportedProblem  # noqa: E402
from fejoint import linsolve  # noqa: E402

REC, INST = Path(REC), Path(INST)
RUNS = [f"label_free_s{s}" for s in range(3)] + [f"supervised_64_s{s}" for s in range(3)]
v = json.loads((REC / "verdict.json").read_text())
out = {"solver": "pardiso" if linsolve._PARDISO is not None else "scipy", "numpy": np.__version__, "pairs": []}
if Path(OUT).exists():
    out = json.loads(Path(OUT).read_text())
done = {(p["id"], p["run"], p["l"], p["kind"]) for p in out["pairs"]}
preds = {}
for run in RUNS:
    with np.load(REC / "runs" / run / "preds.npz") as z:
        preds[run] = {k: z[k] for k in z.files}


def box_row(run, iid, l):
    arm, s = run.rsplit("_s", 1)
    b = v["arms"][arm][s]
    return (b["eval_rows"].get(iid) or b["tested"][iid])[l]


def iou(a, b):
    u = int((a | b).sum())
    return 1.0 if u == 0 else float((a & b).sum() / u)


for job in JOBS:
    iid, runs, lv = job.split(":")
    ex, q = load_export(INST / f"{iid}.npz")
    with np.load(REC / "labels" / f"{iid}.npz") as z:
        lab = {k: z[k] for k in z.files}
    P = ExportedProblem(ex)
    k_s, delta = P.k_s, float(ex["delta"])
    plane = 3 * np.nonzero(np.asarray(ex["node_flags"])[:, 0])[0]
    # energy readings of every run at every level (no solve)
    evr_l = {}
    for run in RUNS:
        for l in range(7):
            if (iid, run, l, "energy") in done:
                continue
            D = float(lab["D"][l]); z = preds[run][iid][l].astype(np.float64); zr = lab["z"][l]
            if l not in evr_l:
                evr_l[l] = P.evaluate(zr, D)
                evr_l[l] = {"Pi": evr_l[l]["Pi"], "F_sigma": evr_l[l]["F_sigma"], "plastic": evr_l[l]["plastic"].copy()}
            ev, evr = P.evaluate(z, D), evr_l[l]
            Fr, Pr = float(lab["F"][l]), float(lab["Pi"][l])
            F = 4 * k_s * (D - float(z[-1]))
            gap = ev["Pi"] - Pr
            s = D + delta
            mine = {"F_err": F / Fr - 1, "e_err": float(z[-1]) / float(lab["e"][l]) - 1,
                    "F_sigma_err": ev["F_sigma"] / Fr - 1, "gap": gap / abs(Pr),
                    "bound": 4 * math.sqrt(2 * k_s * max(gap, 0.0)) / abs(Fr),
                    "within_bound": abs(F - Fr) <= 4 * math.sqrt(2 * k_s * max(gap, 0.0)) * (1 + 1e-9) + 1e-9 * abs(Fr),
                    "iou_contact": iou(z[plane] <= 1e-3 * s, zr[plane] <= 1e-3 * s),
                    "iou_plastic": iou(ev["plastic"], evr["plastic"]),
                    "bolt_err": ev["bolt_N"] / float(lab["bolt_N"][l]) - 1,
                    "u_rel_l2": float(np.linalg.norm(P.T @ z - P.T @ zr) / np.linalg.norm(P.T @ zr)),
                    "label_Pi_rel": evr["Pi"] / Pr - 1, "label_F_sigma_rel": evr["F_sigma"] / Fr - 1}
            b = box_row(run, iid, l)
            diff = {k: (abs(mine[k] - b[k]) if not isinstance(mine[k], bool) else mine[k] == b[k]) for k in mine
                    if k in b}
            out["pairs"].append({"id": iid, "run": run, "l": l, "kind": "energy", "mine": mine, "diff": diff})
    # the distance from the curve, by exact solves
    if lv != "-":
        for run in runs.split("+"):
            for l in map(int, lv):
                if (iid, run, l, "curve") in done:
                    continue
                D = float(lab["D"][l]); z = preds[run][iid][l].astype(np.float64)
                e_pred = float(z[-1])
                F = 4 * k_s * (D - e_pred)
                near = int(np.argmin(np.abs(lab["e"] - e_pred)))
                t0 = time.process_time()
                try:
                    c = P.solve_at_e(e_pred, z0=lab["z"][near])
                    ce = F / c["F"] - 1 if (c["converged"] and c["F"] > 0) else math.inf
                    Fstar, conv = c["F"], c["converged"]
                except Exception as err:  # noqa: BLE001
                    ce, Fstar, conv = math.inf, None, f"{type(err).__name__}: {err}"
                cpu = time.process_time() - t0
                b = box_row(run, iid, l)
                out["pairs"].append({"id": iid, "run": run, "l": l, "kind": "curve", "D": D, "e_pred": e_pred,
                                     "F": F, "F_star": Fstar, "converged": conv, "curve_err": ce,
                                     "box_curve_err": b["curve_err"], "box_note": b["curve_note"],
                                     "abs_diff": (abs(ce - b["curve_err"]) if math.isfinite(ce) and math.isfinite(b["curve_err"])
                                                  else (0.0 if ce == b["curve_err"] else math.inf)),
                                     "rel_diff": (abs(ce - b["curve_err"]) / max(abs(b["curve_err"]), 1e-300)
                                                  if math.isfinite(ce) and math.isfinite(b["curve_err"]) else None),
                                     "cpu_s": round(cpu, 1), "warm_start_level": near})
                Path(OUT).write_text(json.dumps(out, indent=1))
                print(iid, run, D, ce, b["curve_err"], round(cpu, 1), flush=True)
    Path(OUT).write_text(json.dumps(out, indent=1))
print("done", flush=True)
