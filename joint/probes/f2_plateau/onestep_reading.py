"""Sandbox diagnostic: a network's fields followed by a few elastic contact steps (f2/precond.py), read against the
labels: what one or two linear contact solves add to a prediction. No training.

    python3 -I onestep_reading.py JOINT_DIR DATA_DIR MEMBER FIELDS.npz [STEPS]
"""
import sys, time
import numpy as np
joint, data, member, fields = sys.argv[1:5]; steps = int(sys.argv[5]) if len(sys.argv) > 5 else 2
sys.path.insert(0, joint); sys.path.insert(0, joint + "/../src")
from f2.data import load_export
from f2.evaluate import clean
from f2.instance import ExportedProblem
from f2.precond import ElasticContactStep

ex, q = load_export(f"{data}/inst/{member}.npz")
lab = np.load(f"{data}/labels/{member}.npz")
z_pre = np.load(f"{data}/pre/{member}.npz")["z"].astype(float)
f = np.load(fields)
t0 = time.time(); S = ElasticContactStep(ex, z_pre)
print(f"set-up {time.time() - t0:.0f} s ({S.c.size} contact unknowns, {S.i.size} others)", flush=True)
P = ExportedProblem(ex); cidx = P.prob.cidx; k_th = float(ex["k_th"])
Z = f["z"].astype(float)
for k in range(steps + 1):
    rows = []; t0 = time.time()
    for l in range(Z.shape[0]):
        Theta = float(lab["Theta"][l])
        z = Z[l].copy(); z[cidx] = np.maximum(z[cidx], 0.0)
        clean(P); P.loading.delta[:] = -Theta
        E, g, _, _ = P.prob.evaluate(z, "hencky", tangent=False)
        clean(P); r = P.evaluate(z, Theta)
        M = 2.0 * k_th * (Theta - r["theta"])
        rows.append((r["theta"] / float(lab["theta"][l]), r["ThetaD"] / float(lab["ThetaD"][l]), M / float(lab["M"][l]) - 1.0, r["Pi"] / float(lab["Pi"][l]) - 1.0))
        if k < steps:
            Z[l] = z + S.step(z, g)[0]
    a = np.array(rows)
    print(f"after {k} steps: theta/ref {np.round(a[:, 0], 3).tolist()}  ThetaD/ref {np.round(a[:, 1], 3).tolist()}\n"
          f"after {k} steps: M err % {np.round(100 * a[:, 2], 1).tolist()}  energy excess % {np.round(100 * a[:, 3], 2).tolist()}\n"
          f"after {k} steps: |M err| median {np.median(np.abs(a[:, 2])):.2%}, largest {np.abs(a[:, 2]).max():.2%} ({time.time() - t0:.0f} s)", flush=True)
