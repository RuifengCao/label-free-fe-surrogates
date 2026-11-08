"""Readings of the development paths (probes/f2_dev/dev_paths.py): the family's B-13 against exploratory run E3's
record, the family's B-19 against E3's, both against the tests, and for every member the quantities that set the
loading: the moment and the end rotation at Theta_D = THETA_TARGET, the half model's secant and tangent stiffness
there and at the first level, and the cost of a level. No model is solved.

    python -I probes/f2_dev/analyse.py --records DIR [--out FILE]
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if not p or pathlib.Path(p).resolve() != HERE]
sys.path.insert(0, str(HERE.parents[1]))

import numpy as np  # noqa: E402

from f1.config import TESTS  # noqa: E402
from f1.readings import moment_reading  # noqa: E402
from f2.family import THETA_TARGET, K_TH  # noqa: E402

E3 = HERE.parent / "f1_explore" / "records"


def path_of(rec):
    lv = [l for l in rec["levels"] if l["converged"]]
    th = np.array([0.0] + [l["theta"] for l in lv])
    M = np.array([0.0] + [l["M"] / 1e6 for l in lv])                  # kNm, whole joint
    TD = np.array([0.0] + [l["ThetaD"] for l in lv])
    b1 = np.array([rec["preload"]["forces_N"][0] / 1e3] + [l["bolt_N"][0] / 1e3 for l in lv])
    return th, M, TD, b1


def at_ThetaD(rec, target):
    th, M, TD, _ = path_of(rec)
    if TD[-1] < target:
        return None
    return float(np.interp(target, TD, M)), float(np.interp(target, TD, th))


def against_e3(rec, e3_name):
    e3 = json.loads((E3 / e3_name).read_text())
    by = {round(l["control_value"], 10): l for l in e3["levels"]}
    rows = []
    for l in rec["levels"]:
        o = by.get(round(l["theta"], 10))
        if o is None:
            continue
        b = np.array(l["bolt_N"]) / 1e3
        rows.append({"theta": l["theta"], "M_rel": l["M"] / 1e6 / o["M_kNm"] - 1,
                     "ThetaD_rel": l["ThetaD"] / o["Theta_D"] - 1,
                     "bolts_rel_max": float(np.max(np.abs(b / np.array(o["bolts_kN"]) - 1)))})
    return rows


def against_tests(rec, spec):
    out = {}
    files = TESTS[spec]["moment_rotation"]
    for t in (0.001, 0.005, 0.01):
        m = at_ThetaD(rec, t)
        if m is None:
            continue
        rd = moment_reading(files, t)
        out[str(t)] = {"model_kNm": m[0], "test_kNm": rd["value"], "tolerance_kNm": rd["tolerance"],
                       "ratio": m[0] / rd["value"]}
    return out


def member_summary(rec):
    th, M, TD, b1 = path_of(rec)
    lv = [l for l in rec["levels"] if l["converged"]]
    t = at_ThetaD(rec, THETA_TARGET)
    s = {"member": rec["member"], "params": rec["params"], "levels": len(lv), "last_theta": float(th[-1]),
         "last_ThetaD": float(TD[-1]), "last_M_kNm": float(M[-1]), "bolt1_last_kN": float(b1[-1]),
         "k_sec0_half": float(M[1] * 1e6 / 2 / th[1]), "make_s": rec["make_seconds"],
         "s_per_level": float(np.mean([l["seconds"] for l in lv])),
         "iterations_per_level": float(np.mean([l["iterations"] for l in lv])),
         "plastic_points_last": lv[-1]["plastic_points"], "kkt_ok": all(
             l["kkt"]["min_gap"] >= -1e-12 and l["kkt"]["min_lambda"] >= -1e-8 and l["kkt"]["max_complementarity"] <= 1e-8
             and l["kkt"]["max_lambda_inactive"] <= 1e-6 and l["kkt"]["max_residual_unconstrained"] <= 1e-6 for l in lv),
         "preload_max_von_mises": rec["preload"]["max_von_mises"], "preload_plastic": rec["preload"]["plastic_points"]}
    if t is not None:
        Mt, tht = t
        k = int(np.searchsorted(TD, THETA_TARGET))
        kt = (M[k] - M[k - 1]) * 1e6 / 2 / (th[k] - th[k - 1])
        s.update({"M_t_kNm": Mt, "theta_t": tht, "k_sec_t_half": Mt * 1e6 / 2 / tht, "k_tan_t_half": float(kt)})
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    recs = {p.stem: json.loads(p.read_text()) for p in sorted(pathlib.Path(a.records).glob("*_frictionless_coarse.json"))}
    out = {"Theta_target": THETA_TARGET, "K_TH": K_TH, "members": [member_summary(r) for r in recs.values()]}
    for name, e3, spec in (("B-13_nominal", "E3_B-13_frictionless_hencky_nominal_coarse_ep-bolts.json", "B-13"),
                           ("B-19_nominal", "E3_B-19_frictionless_hencky_nominal_coarse_ep-bolts.json", "B-19")):
        r = recs.get(f"{name}_frictionless_coarse")
        if r:
            out[f"{name}_vs_E3"] = against_e3(r, e3)
            out[f"{name}_vs_tests"] = against_tests(r, spec)
            e3rec = json.loads((E3 / e3).read_text())
            e3rec = {"member": "E3", "params": {}, "preload": e3rec["preload"], "make_seconds": None,
                     "levels": [{"theta": l["control_value"], "M": l["M_kNm"] * 1e6, "ThetaD": l["Theta_D"],
                                 "bolt_N": [b * 1e3 for b in l["bolts_kN"]], "converged": l["converged"]}
                                for l in e3rec["levels"]]}
            e3rec["preload"]["forces_N"] = [f * 1e3 for f in e3rec["preload"]["forces_kN"]]
            out[f"{name}_E3_vs_tests"] = against_tests(e3rec, spec)
    txt = json.dumps(out, indent=1)
    if a.out:
        pathlib.Path(a.out).write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
