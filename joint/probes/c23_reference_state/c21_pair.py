"""Probe, 20 Nov 2026: the one 'bubble condensation did not converge' pair of G-C2.1 (supervised_64 s1, eval_0046, 0.5 mm).
Run from joint/ with FEJOINT_SOLVER=legacy:  python -I -B probes/c23_reference_state/c21_pair.py RETURN INSTANCES"""
import os, sys, pathlib
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
sys.path.insert(0, str(pathlib.Path.cwd()))
import numpy as np
from c2.data import load_export
from c2.evaluate import metrics
from c2.instance import ExportedProblem
ret, inst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
iid = "eval_0046"
def field(run):
    with np.load(ret / "runs" / run / "preds.npz") as z:
        return z[iid]
def fresh():
    ex, _ = load_export(inst / f"{iid}.npz")
    with np.load(ret / "labels" / f"{iid}.npz") as z:
        ref = {k: z[k] for k in z.files}
    P = ExportedProblem(ex)
    ref_pl = [P.evaluate(ref["z"][l], float(ref["D"][l]))["plastic"] for l in range(ref["D"].size)]
    return ex, ref, P, ref_pl
def one(P, ex, ref, ref_pl, run, l):
    r = metrics(P, ex, field(run)[l], ref, ref_pl[l], l)
    return r["curve_err"], r["curve_note"]
ex, ref, P, ref_pl = fresh()
print("alone, new object: supervised_64_s1 l0:", one(P, ex, ref, ref_pl, "supervised_64_s1", 0))
ex, ref, P, ref_pl = fresh()
a = one(P, ex, ref, ref_pl, "supervised_64_s0", 6)
b = one(P, ex, ref, ref_pl, "supervised_64_s1", 0)
print("after supervised_64_s0 l6 (the gate's order):", a, "->", b)
ex, ref, P, ref_pl = fresh()
a = one(P, ex, ref, ref_pl, "supervised_64_s0", 6)
for s in P.solids:
    s.bub = np.zeros_like(s.bub)
print("same order, bubble state zeroed in between:", one(P, ex, ref, ref_pl, "supervised_64_s1", 0))
