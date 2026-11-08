"""Development paths of the CHS surrogate family (draft, before any pre-specification): members chosen by hand at
the family's corners and centre, and gate G-F1's specimens under the family's laws, solved under rotation control
from the preload to Theta_D >= STOP. They set the loading (the rotational spring and the device's range) and the
cost of a label; they are not drawn with any seed and are kept out of every sample.

    python -I probes/f2_dev/dev_paths.py --out DIR --members NAME[,NAME...] [--mesh coarse] [--splice frictionless]

One JSON record per member, written whole when its path ends.
"""
import os
import sys

for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_k] = "1"

import argparse
import json
import pathlib
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if not p or pathlib.Path(p).resolve() != HERE]
sys.path.insert(0, str(HERE.parents[1]))

import numpy as np  # noqa: E402

from f2.family import Params, TESTED  # noqa: E402
from f2 import instance as I  # noqa: E402

DEV = {
    "B-13_nominal": TESTED["B-13_nominal"],
    "B-19_nominal": TESTED["B-19_nominal"],
    "W1": {"tp": 10.0, "e1": 75.0, "e2": 55.0, "fy": 345.0, "Np": 60.0},
    "W2": {"tp": 10.0, "e1": 55.0, "e2": 75.0, "fy": 345.0, "Np": 130.0},
    "S1": {"tp": 25.0, "e1": 55.0, "e2": 75.0, "fy": 460.0, "Np": 130.0},
    "S2": {"tp": 25.0, "e1": 75.0, "e2": 55.0, "fy": 460.0, "Np": 60.0},
    "C": {"tp": 17.5, "e1": 65.0, "e2": 65.0, "fy": 402.5, "Np": 95.0},
    "T10hi": {"tp": 10.0, "e1": 65.0, "e2": 65.0, "fy": 460.0, "Np": 95.0},
    "T25lo": {"tp": 25.0, "e1": 65.0, "e2": 65.0, "fy": 345.0, "Np": 95.0},
    # a half fraction in (e1, e2, Np) at the centre's tp and fy, to separate their effects from the corners'
    "X1": {"tp": 17.5, "e1": 55.0, "e2": 55.0, "fy": 402.5, "Np": 130.0},
    "X2": {"tp": 17.5, "e1": 75.0, "e2": 55.0, "fy": 402.5, "Np": 60.0},
    "X3": {"tp": 17.5, "e1": 55.0, "e2": 75.0, "fy": 402.5, "Np": 60.0},
    "X4": {"tp": 17.5, "e1": 75.0, "e2": 75.0, "fy": 402.5, "Np": 130.0},
}
STEP, CAP, STOP = 0.002, 0.04, 0.013


def run(name: str, mesh: str, splice: str, out: pathlib.Path):
    path = out / f"{name}_{splice}_{mesh}.json"
    if path.exists():
        print(path.name, "exists", flush=True)
        return
    q = Params(**DEV[name])
    t0 = time.time()
    ex, pre = I.make(q, mesh=mesh, splice=splice, k_th=1.0)
    t_make = time.time() - t0
    P = I.ExportedProblem(ex)
    rec = {"member": name, "params": DEV[name], "mesh": mesh, "splice": splice,
           "unknowns": int(ex["fixed"].size), "free": int((~ex["fixed"]).sum()), "nodes": int(ex["nodes"].shape[0]),
           "cells": int(sum(ex[f"hexes_{p}"].shape[0] for p in I.PARTS)),
           "preload": {k: v for k, v in pre.items() if k != "z"}, "make_seconds": round(t_make, 1), "levels": []}
    print(json.dumps({"member": name, "make_s": rec["make_seconds"], "preload_kN": [round(f / 1e3, 4) for f in pre["forces_N"]],
                      "vm": pre["max_von_mises"]}), flush=True)
    z = pre["z"]
    k = 0
    part = path.with_name(path.stem + ".partial.json")
    zpart = path.with_name(path.stem + ".partial_z.npy")
    if part.exists() and zpart.exists():                 # resume after a cut-off run (the state does not depend on
        old = json.loads(part.read_text())              # the start under deformation theory; it saves iterations)
        assert old["params"] == rec["params"] and abs(old["preload"]["delta"] / pre["delta"] - 1) < 1e-9
        rec["levels"], rec["resumed_after_level"] = old["levels"], len(old["levels"])
        z, k = np.load(zpart), len(old["levels"])
    while True:
        k += 1
        th = round(STEP * k, 10)
        t1 = time.time()
        r = P.solve_at_theta(th, z0=z)
        z = r["z"]
        lev = {"theta": th, **{x: r[x] for x in ("M", "ThetaD", "uzD", "uzC", "w0", "bolt_N", "kkt", "iterations",
                                                 "converged", "plastic_points", "max_von_mises")},
               "W": r["W"], "seconds": round(time.time() - t1, 1)}
        rec["levels"].append(lev)
        print(json.dumps({"member": name, "theta": th, "M_kNm": round(r["M"] / 1e6, 3), "ThetaD": round(r["ThetaD"], 6),
                          "b1_kN": round(r["bolt_N"][0] / 1e3, 2), "it": r["iterations"], "conv": r["converged"],
                          "s": lev["seconds"]}), flush=True)
        if not r["converged"] or r["ThetaD"] >= STOP or th >= CAP - 1e-12:
            break
        np.save(zpart, z)
        part.write_text(json.dumps(rec))
    rec["seconds"] = round(time.time() - t0, 1)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(rec, indent=1))
    os.replace(tmp, path)
    for p in (part, zpart):
        if p.exists():
            p.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--members", required=True)
    ap.add_argument("--mesh", default="coarse")
    ap.add_argument("--splice", default="frictionless")
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for name in a.members.split(","):
        run(name, a.mesh, a.splice, out)


if __name__ == "__main__":
    main()
