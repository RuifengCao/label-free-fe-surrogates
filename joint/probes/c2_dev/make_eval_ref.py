"""Reference data of the 64 former held-out members of G-C2.1 for the development scripts on the laptop:
the exact end displacement, force, energy and bolt force at the seven evaluation levels (the gate's labels), the exact
points of each member's reference curve F*(e) (labels, origin, and the exact solves at prescribed e that the gate's
evaluation made for every arm and seed), and the governing mechanism by the closed-form estimate (fit4.json, 4 mm).
Written to eval_ref.json; nothing here is used in training or in a reading, only in judging."""
import sys, json
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
import numpy as np
from common import eval_ids, label, KS
from refcurve import points
ids, par = eval_ids()
L, As, fyb = 80.0, 84.3, 880.0
x = json.load(open(paths.work() / "fit4.json"))["4.0"]["x"]; A = np.exp(x[:4]); p = float(np.exp(x[4]))
def modes(q):
    m = q["w"] / 2 - q["t_w"] / 2 - 0.8 * q["r"]; n = min(q["n"], 1.25 * m)
    Mpl = 0.25 * L * q["t_f"] ** 2 * q["fy"]; B = 4 * As * fyb
    return np.array([4 * Mpl / m, (2 * Mpl + n * B) / (m + n), B, q["t_w"] * L * q["fy"]])
out = {"k_s": KS, "levels_mm": [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0], "mechanism_names": ["mode 1 (flange)", "mode 2 (flange + bolt)", "mode 3 (bolt)", "web yielding"], "members": {}}
for i in ids:
    lab = label(i); pts = points(i)
    e = np.array([q_[0] for q_ in pts]); F = np.array([q_[1] for q_ in pts])
    keep = np.concatenate([[True], np.diff(e) > 1e-9 * max(e.max(), 1.0)])
    out["members"][i] = {"D": [float(v) for v in lab["D"]], "e": [float(v) for v in lab["e"]], "F": [float(v) for v in lab["F"]],
                         "Pi": [float(v) for v in lab["Pi"]], "bolt_N": [float(v) for v in lab["bolt_N"]],
                         "curve_e": [float(v) for v in e[keep]], "curve_F": [float(v) for v in F[keep]],
                         "mechanism": int(np.argmin(A * modes(par[i]))), "params": {k: float(v) for k, v in par[i].items()}}
json.dump(out, open(paths.work() / "eval_ref.json", "w"))
print(len(out["members"]), "members;", sum(len(m["curve_e"]) for m in out["members"].values()), "curve points")
