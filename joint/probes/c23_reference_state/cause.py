"""Probe written on 20 Nov 2026, after the verdict: what state makes the reference solve of third_0034 fail.
Run from joint/ with FEJOINT_SOLVER=legacy:  python -I -B probes/c23_reference_state/cause.py RECORDS INSTANCES OUT.json"""
import os, sys, pathlib, json
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
sys.path.insert(0, str(pathlib.Path.cwd()))
import numpy as np, scipy
from c2.data import load_export
from c2.evaluate import metrics
from c2.instance import ExportedProblem

rec, inst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
iid = "third_0034"
FILES = {"condensed": "preds_condensed.npz", "raw": "preds.npz"}

def field(run, reading):
    with np.load(rec / "run_files" / run / FILES[reading]) as z:
        return z[iid]

def fresh():
    ex, _ = load_export(inst / f"{iid}.npz")
    with np.load(rec / "labels" / f"{iid}.npz") as z:
        ref = {k: z[k] for k in z.files}
    P = ExportedProblem(ex)
    ref_pl = [P.evaluate(ref["z"][l], float(ref["D"][l]))["plastic"] for l in range(ref["D"].size)]
    return ex, ref, P, ref_pl

def one(P, ex, ref, ref_pl, run, reading, l):
    r = metrics(P, ex, field(run, reading)[l], ref, ref_pl[l], l)
    return r["curve_err"], r["curve_note"]

print("numpy", np.__version__, "scipy", scipy.__version__)
out = {}
# 1. the failing order, keeping the bubble state the first solve leaves
ex, ref, P, ref_pl = fresh()
print("bubble state of a new problem object: max abs", [float(np.abs(s.bub).max()) for s in P.solids])
a = one(P, ex, ref, ref_pl, "label_free_s6", "condensed", 6)
B8 = [s.bub.copy() for s in P.solids]
print("1a s6 condensed l6:", a, "| bubble state left: max abs", [float(np.abs(b).max()) for b in B8])
b = one(P, ex, ref, ref_pl, "label_free_s7", "condensed", 0)
print("1b then s7 condensed l0, state kept:", b)
out["kept"] = [a, b]
# 2. a new problem object given only that bubble state
ex, ref, P, ref_pl = fresh()
for s, b8 in zip(P.solids, B8):
    s.bub = b8.copy()
c = one(P, ex, ref, ref_pl, "label_free_s7", "condensed", 0)
print("2  new object, bubble state of 1a put in, s7 condensed l0:", c)
out["state_only"] = c
# 3. the failing order with the bubble state set back to zero in between
ex, ref, P, ref_pl = fresh()
a3 = one(P, ex, ref, ref_pl, "label_free_s6", "condensed", 6)
for s in P.solids:
    s.bub = np.zeros_like(s.bub)
d = one(P, ex, ref, ref_pl, "label_free_s7", "condensed", 0)
print("3  same order, bubble state zeroed in between:", a3, d)
out["zeroed"] = [a3, d]
# 4. the host's own infinite pair (s6 raw l0 after s6 condensed l6), same three ways
ex, ref, P, ref_pl = fresh()
one(P, ex, ref, ref_pl, "label_free_s6", "condensed", 6)
e1 = one(P, ex, ref, ref_pl, "label_free_s6", "raw", 0)
ex, ref, P, ref_pl = fresh()
one(P, ex, ref, ref_pl, "label_free_s6", "condensed", 6)
for s in P.solids:
    s.bub = np.zeros_like(s.bub)
e2 = one(P, ex, ref, ref_pl, "label_free_s6", "raw", 0)
print("4  s6 raw l0 after s6 condensed l6: state kept", e1, "| zeroed", e2)
out["host_pair"] = {"kept": e1, "zeroed": e2}
# 5. where the failure sits: the first evaluation of the solve, element Newton from the kept state
ex, ref, P, ref_pl = fresh()
z7 = np.asarray(field("label_free_s7", "condensed")[0], float)
e_pred = float(z7[P.e_idx])
near = int(np.argmin(np.abs(np.asarray(ref["e"]) - e_pred)))
z0 = np.where(P.prob_e.fixed, 0.0, ref["z"][near]); z0[P.e_idx] = e_pred
u = P.prob_e.T @ z0
print("5  e_pred", e_pred, "nearest label level", near, "of e", [round(float(v), 4) for v in ref["e"]])
for k, (s, b8) in enumerate(zip(P.solids, B8)):
    for cap in (60, 200, 1000, 5000):
        s.bub = b8.copy()
        try:
            E, R, K, info = s.evaluate(u, mode="hencky", tangent=False, max_it=cap)
            print(f"   set {k}: cap {cap}: converged in {info['bubble_iterations']} element iterations, energy {E!r}")
            Ew = E
            break
        except RuntimeError as err:
            print(f"   set {k}: cap {cap}: {err}")
    s.bub = np.zeros_like(s.bub)
    E0, _, _, info0 = s.evaluate(u, mode="hencky", tangent=False)
    print(f"   set {k}: from zero: {info0['bubble_iterations']} element iterations, energy {E0!r}")
json.dump(out, open(sys.argv[3], "w"), indent=1, default=str)
