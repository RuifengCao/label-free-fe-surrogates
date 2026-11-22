"""Probe, 20 Nov 2026 (after the verdict): a pair after its predecessor in the gate's order, with the bubble state kept and zeroed.
Run from joint/ with FEJOINT_SOLVER=legacy:
  python -I -B probes/c23_reference_state/pairs.py RECORDS INSTANCES MEMBER RUN:READING:LEVEL[,RUN:READING:LEVEL...]   (visited in this order)
The first pair listed is the predecessor; every later pair is solved once with the state kept and, in a second pass, with
the state zeroed before it."""
import os, sys, pathlib
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
sys.path.insert(0, str(pathlib.Path.cwd()))
import numpy as np
from c2.data import load_export
from c2.evaluate import metrics
from c2.instance import ExportedProblem
rec, inst, iid = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
pairs = [(a, b, int(c)) for a, b, c in (p.split(":") for p in sys.argv[4].split(","))]
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
for mode in ("kept", "zeroed"):
    ex, ref, P, ref_pl = fresh()
    for n, (run, reading, l) in enumerate(pairs):
        if mode == "zeroed" and n > 0:
            for s in P.solids:
                s.bub = np.zeros_like(s.bub)
        r = metrics(P, ex, field(run, reading)[l], ref, ref_pl[l], l)
        print(mode, iid, run, reading, l, repr(r["curve_err"]), repr(r["curve_note"]), "evaluate_failed", r["evaluate_failed"], flush=True)
