"""Data of the CPU pilots of G-C2.1 (not the gate): exports a small family sample with the gate's own code (seeds 8 for
training and 7 for held-out members, both seen and outside the gate; the preloaded T1 as a tested member) and labels
the held-out and tested members. pilot_trend.py trains on it. Its earlier versions also trained and evaluated
(pilot_coarse_summary.json); that part went out of date with the evaluation's change to the curve metric and was
removed, since every later pilot trained through pilot_trend.py.
Usage: python pilot_cpu.py JOINT OUT [--mesh coarse|run] [--n_train N] [--n_eval N] [--workers N] [--elastic]"""
import argparse, copy, sys, time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("joint"); ap.add_argument("out")
ap.add_argument("--mesh", default="coarse")
ap.add_argument("--n_train", type=int, default=32); ap.add_argument("--n_eval", type=int, default=6)
ap.add_argument("--workers", type=int, default=1)
ap.add_argument("--elastic", action="store_true", help="control: yield stresses of steel and bolt times 100")
a = ap.parse_args()
sys.path.insert(0, a.joint); sys.path.insert(0, str(Path(a.joint).parent / "src"))
import numpy as np
from c2.config import config
from c2 import data
if a.elastic:                                   # an elastic control of the same family (not the gate)
    import c2.family as fam, c2.instance as inst
    from fejoint.plasticity import Hardening, Material
    def steel_el(fy):
        f = 100.0 * fy
        pts = [(f / fam.E, f), (0.02 + f / fam.E, f), (0.15 + f / fam.E, 1.35 * f)]
        al = np.array([max(e - s_ / fam.E, 0.0) for e, s_ in pts]); al[0] = 0.0
        sg = np.array([s_ for _, s_ in pts]) + fam.REG * al
        return Material(fam.E, fam.NU, Hardening(al, sg, h_end=fam.REG))
    fam.BOLT_LAW[:] = [(100 * 880.0 / fam.E, 100 * 880.0), (0.02 + 100 * 880.0 / fam.E, 100 * 880.0), (0.06 + 100 * 880.0 / fam.E, 100 * 960.0)]
    inst.steel = steel_el
    _build = inst.build
    def build_el(q, mesh=fam.MESH):              # the preload from the nominal bolt yield force, not the scaled one
        m = _build(q, mesh)
        m.delta = q.rho * 880.0 * fam.BOLT["As"] / m.k_ax
        m.bolts.delta[:] = m.delta
        return m
    inst.build = build_el
    data.build = build_el

cfg = copy.deepcopy(config())
d = cfg["data"]
d["n_train"], d["n_eval"] = a.n_train, a.n_eval
d["train_seed"], d["eval_seed"] = 8, 7
d["seeds_seen_before_stamp"] = []
if a.mesh == "coarse":
    d["mesh"] = {"h": 10.0, "n_tf": 1, "hx_max": 40.0}
d["eval_levels_mm"] = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
d["tested"] = {"BJ_T1_preloaded": dict(d["tested"]["BJ_T1_preloaded"])}
out = Path(a.out); D = out / "data"
t0 = time.time()
data.generate(cfg, D)
ids = [r["id"] for r in data.manifest(D)["instances"] if r["split"] in ("eval", "tested")]
data.label(cfg, D, ids, workers=a.workers)
print("labels", round(time.time() - t0), "s", flush=True)
