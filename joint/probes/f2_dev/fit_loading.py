"""The loading rule of the CHS surrogate family from the development paths (no model is solved).

For each member, its rotation-control path gives the moment M and the end rotation theta at the tests' rotation
Theta_D = THETA_TARGET. Through a loading spring k per half model, the device rotation at which a member reaches a
state is Theta = theta + M / (2 k) (deformation theory: the state at a given end rotation does not depend on the
device). The rule sets the top of each member's device range, Theta_max(q), from closed-form estimates of M and
theta at THETA_TARGET, fitted here:
    theta_t = THETA_TARGET + b M_t                      (the tube's elastic rotation beyond the ring)
    M_t = (M_p^-n + M_c^-n)^(-1/n),  M_p = A (tp/15)^a (fy/400)^c (e1/65)^d (e2/65)^e (Np/95)^f
                                                       (a smooth minimum with a cap M_c; n = 4)
Reported for candidate springs: the Theta_D each member reaches at Theta_max(q), and the first-order magnification
of a relative error of theta in the distance from the curve, (k + k_t) / k_s (k_t, k_s the member's tangent and
secant stiffness, half model), at the first level and at THETA_TARGET.

    python -I probes/f2_dev/fit_loading.py --records DIR [--out FILE]
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if not p or pathlib.Path(p).resolve() != HERE]
sys.path.insert(0, str(HERE.parents[1]))

import numpy as np  # noqa: E402
from scipy.optimize import least_squares  # noqa: E402

from f2 import family  # noqa: E402

THETA_TARGET = family.THETA_TARGET

N_SMOOTH = 4.0


def path(rec):
    lv = [l for l in rec["levels"] if l["converged"]]
    th = np.array([0.0] + [l["theta"] for l in lv])
    M = np.array([0.0] + [l["M"] for l in lv])          # N mm, whole joint
    TD = np.array([0.0] + [l["ThetaD"] for l in lv])
    return th, M, TD


def at_target(rec):
    th, M, TD = path(rec)
    if TD[-1] < THETA_TARGET:
        return None
    k = int(np.searchsorted(TD, THETA_TARGET))
    Mt, tht = float(np.interp(THETA_TARGET, TD, M)), float(np.interp(THETA_TARGET, TD, th))
    kt = (M[k] - M[k - 1]) / 2 / (th[k] - th[k - 1])
    return {"M_t": Mt, "theta_t": tht, "k_sec_t": Mt / 2 / tht, "k_tan_t": float(kt), "k_sec0": M[1] / 2 / th[1]}


def M_rule(p, q):
    A, a, c, Mc, d, e, f = (list(p) + [0.0, 0.0, 0.0])[:7]
    Mp = (A * (q["tp"] / 15.0) ** a * (q["fy"] / 400.0) ** c * (q["e1"] / 65.0) ** d * (q["e2"] / 65.0) ** e
          * (q["Np"] / 95.0) ** f)
    return (Mp ** -N_SMOOTH + Mc ** -N_SMOOTH) ** (-1.0 / N_SMOOTH)


def ThetaD_at_device(rec, k, Theta):
    th, M, TD = path(rec)
    dev = th + M / (2 * k)
    if Theta > dev[-1]:
        return None                                     # beyond the solved path
    return float(np.interp(Theta, dev, TD))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--out")
    ap.add_argument("--target", type=float, help="Theta_D at the top of the range (default: f2.family's)")
    ap.add_argument("--with-Np", action="store_true", help="also fit an exponent of the preload")
    ap.add_argument("--hold-out", default="", help="members left out of the fit and predicted (comma list)")
    a = ap.parse_args()
    global THETA_TARGET
    if a.target is not None:
        THETA_TARGET = a.target
    recs = {json.loads(p.read_text())["member"]: json.loads(p.read_text())
            for p in sorted(pathlib.Path(a.records).glob("*_frictionless_coarse.json"))}
    pts = {n: (r["params"], at_target(r)) for n, r in recs.items()}
    pts = {n: v for n, v in pts.items() if v[1] is not None}
    held = [n for n in a.hold_out.split(",") if n]
    names = [n for n in pts if n not in held]
    Mt = np.array([pts[n][1]["M_t"] for n in names]); tht = np.array([pts[n][1]["theta_t"] for n in names])
    b = float(np.sum(Mt * (tht - THETA_TARGET)) / np.sum(Mt * Mt))
    res = lambda p: np.log([M_rule(p, pts[n][0]) for n in names]) - np.log(Mt)  # noqa: E731
    full = len(names) >= 10
    extra = (3 if a.with_Np else 2) if full else 0
    x0 = [2.0e8, 1.4, 1.0, 4.5e8] + [0.0] * extra
    lo = [1e7, 0.2, 0.0, 1e8] + [-4.0, -4.0, -2.0][:extra]
    hi = [1e10, 3.0, 3.0, 2e9] + [4.0, 4.0, 2.0][:extra]
    fit = least_squares(res, x0=x0, x_scale=[1e8, 1, 1, 1e8] + [1] * extra, bounds=(lo, hi))
    p = fit.x
    out = {"Theta_target": THETA_TARGET, "members": names, "b_per_Nmm": b,
           "L_eff_mm": b * 191700.0 * np.pi / 64 * (323.9 ** 4 - 299.1 ** 4),
           "theta_rule_max_abs_error": float(np.max(np.abs(THETA_TARGET + b * Mt - tht))),
           "M_rule": {"A_Nmm": p[0], "a": p[1], "c": p[2], "M_c_Nmm": p[3], "n": N_SMOOTH,
                      "d_e1": p[4] if extra else 0.0, "e_e2": p[5] if extra else 0.0,
                      "f_Np": p[6] if extra == 3 else 0.0,
                      "log_residuals": dict(zip(names, map(float, res(p))))},
           "springs": {}, "held_out": {}}
    for n in held:
        if n in pts:
            out["held_out"][n] = {"M_t": pts[n][1]["M_t"], "M_rule": M_rule(p, pts[n][0]),
                                  "log_error": float(np.log(M_rule(p, pts[n][0]) / pts[n][1]["M_t"]))}
    for k in (2e9, 3e9, 4e9, 6e9, 8e9):
        rows = {}
        for n in list(names) + [h for h in held if h in pts]:
            q, t = pts[n]
            Mr = M_rule(p, q)
            Theta_max = THETA_TARGET + b * Mr + Mr / (2 * k)
            rows[n] = {"Theta_max": Theta_max, "ThetaD_at_top": ThetaD_at_device(recs[n], k, Theta_max),
                       "magnification_first": 1 + k / t["k_sec0"],
                       "magnification_target": (k + t["k_tan_t"]) / t["k_sec_t"]}
        out["springs"][f"{k:.0e}"] = rows
    txt = json.dumps(out, indent=1)
    if a.out:
        pathlib.Path(a.out).write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
