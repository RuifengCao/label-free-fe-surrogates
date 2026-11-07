"""Criteria and verdict of gate G-F1 from the case records (f1/run.py) and the test readings (f1/readings.py).

Model values at a comparison point are read off a path by linear interpolation between the two levels that
bracket the point, the preload state (all readings zero, bolts at their preload) counting as the level before the
first. A value is missing when the path does not reach the point, and invalid when any level up to and including
the bracketing one did not converge or broke a KKT limit; a criterion with a missing or invalid model value does not
hold. Each criterion holds when the test value lies within [min - tol, max + tol] of the two splice models' values.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .run import case_id


def points_of(name: str, cfg: dict, reported: bool = False):
    pts = cfg["points"][name]
    if cfg["specimens"][name]["test"] == "bending":
        out = [("Theta_D", pts["theta"])] + [("M_kNm", m) for m in pts["bolt_moments_kNm"]]
        if reported:
            out += [("Theta_D", t) for t in pts["theta_reported"]]
        return out
    return [("T_kN", pts["T_kN"])]


def _value(lev, key):
    if key == "bolt1_kN":
        return lev["bolts_kN"][0]
    return lev[key]


def at_point(rec: dict, key: str, target: float, value_key: str):
    """(value, status): status 'ok', 'missing' or 'invalid'."""
    pre = {"Theta_D": 0.0, "M_kNm": 0.0, "T_kN": 0.0, "delta_mm": 0.0, "bolts_kN": rec["preload"]["forces_kN"],
           "converged": rec["preload"]["converged"], "kkt_ok": rec["preload"]["kkt_ok"]}
    lv = [pre] + rec["levels"]
    for i in range(1, len(lv)):
        if lv[i][key] >= target:
            if not all(l["converged"] and l["kkt_ok"] for l in lv[:i + 1]):
                return None, "invalid"
            x0, x1 = lv[i - 1][key], lv[i][key]
            y0, y1 = _value(lv[i - 1], value_key), _value(lv[i], value_key)
            t = 0.0 if x1 == x0 else (target - x0) / (x1 - x0)
            return float(y0 + t * (y1 - y0)), "ok"
    return None, "missing"


def model_quantity(rec: dict, name: str, cfg: dict, criterion: str, theta=None):
    """The model's value for a criterion: C1 moment at theta, C3 increase of bolt 1, C2 displacement at T."""
    pts = cfg["points"][name]
    if criterion == "C1":
        return at_point(rec, "Theta_D", pts["theta"] if theta is None else theta, "M_kNm")
    if criterion == "C3":
        lo, s_lo = at_point(rec, "M_kNm", pts["bolt_moments_kNm"][0], "bolt1_kN")
        hi, s_hi = at_point(rec, "M_kNm", pts["bolt_moments_kNm"][1], "bolt1_kN")
        if s_lo != "ok" or s_hi != "ok":
            return None, s_hi if s_lo == "ok" else s_lo
        return hi - lo, "ok"
    if criterion == "C2":
        return at_point(rec, "T_kN", pts["T_kN"], "delta_mm")
    raise ValueError(criterion)


def bracket(test: dict, a, b):
    if a is None or b is None:
        return False
    lo, hi = min(a, b) - test["tolerance"], max(a, b) + test["tolerance"]
    return bool(lo <= test["value"] <= hi)


def _records(out: Path) -> dict:
    return {p.stem: json.loads(p.read_text()) for p in sorted((Path(out) / "records").glob("*.json"))}


def evaluate(cfg: dict, readings: dict, out: Path) -> dict:
    recs = _records(out)
    mesh, splices = cfg["model"]["mesh"], cfg["model"]["splices"]
    gated_theory = cfg["model"]["theories"]["gated"]

    def rec(name, splice, theory, preload="nominal", m=None):
        return recs.get(case_id({"specimen": name, "splice": splice, "theory": theory, "preload": preload,
                                  "mesh": m or mesh}))

    def crit(name, criterion, theory, preload="nominal", theta=None):
        vals = {}
        for sp in splices:
            r = rec(name, sp, theory, preload)
            vals[sp] = model_quantity(r, name, cfg, criterion, theta) if r is not None else (None, "no record")
        if criterion == "C1":
            test = readings[name]["C1"] if theta is None else readings[name]["reported_theta"][str(theta)]
        else:
            test = readings[name][criterion]
        ok_all = all(v[1] == "ok" for v in vals.values())
        holds = ok_all and bracket(test, vals[splices[0]][0], vals[splices[1]][0])
        return {"test": test, "models": {sp: {"value": v[0], "status": v[1]} for sp, v in vals.items()},
                "holds": bool(holds)}

    result = {"gate": cfg["gate"], "criteria": {}, "reported": {}}
    for name, spec in cfg["specimens"].items():
        names = ["C1", "C3"] if spec["test"] == "bending" else ["C2"]
        for c in names:
            result["criteria"][c] = dict(crit(name, c, gated_theory), specimen=name)
            result["reported"][f"{c} elastic"] = dict(crit(name, c, "elastic"), specimen=name)
            if spec["test"] == "bending":
                result["reported"][f"{c} measured preload"] = dict(crit(name, c, gated_theory, "measured"), specimen=name)
        if spec["test"] == "bending":
            for t in cfg["points"][name]["theta_reported"]:
                result["reported"][f"C1 at Theta_D = {t}"] = dict(crit(name, "C1", gated_theory, theta=t), specimen=name)
                result["reported"][f"C1 at Theta_D = {t} elastic"] = dict(crit(name, "C1", "elastic", theta=t),
                                                                          specimen=name)
        # mesh flag: elastic medium against elastic coarse, for the gated quantities
        mf = cfg["model"]["mesh_flag"]
        for sp in splices:
            rc, rm = rec(name, sp, mf["theory"]), rec(name, sp, mf["theory"], m=mf["mesh"])
            for c in names:
                vc = model_quantity(rc, name, cfg, c) if rc else (None, "no record")
                vm = model_quantity(rm, name, cfg, c) if rm else (None, "no record")
                ratio = vm[0] / vc[0] if vc[1] == "ok" and vm[1] == "ok" and vc[0] else None
                result["reported"][f"mesh flag {name} {sp} {c}"] = {
                    "coarse": vc[0], "medium": vm[0], "status": [vc[1], vm[1]], "ratio": ratio,
                    "flagged": (ratio is None) or abs(ratio - 1) > mf["limit"]}
    result["verdict"] = "PASS" if all(v["holds"] for v in result["criteria"].values()) and \
        {"C1", "C2", "C3"} <= set(result["criteria"]) else "FAIL"
    return result


def numbers_markdown(result: dict) -> str:
    def f(x, d=3):
        return "missing" if x is None else f"{x:.{d}f}"
    lines = [f"# {result['gate']}: numbers", "", f"**Verdict: {result['verdict']}**", "",
             "| Criterion | Specimen | Test | Tolerance | Frictionless | No-slip | Holds |", "|---|---|---|---|---|---|---|"]
    for c, v in sorted(result["criteria"].items()):
        m = v["models"]
        lines.append(f"| {c} | {v['specimen']} | {f(v['test']['value'])} | {f(v['test']['tolerance'])} | "
                     f"{f(m['frictionless']['value'])} ({m['frictionless']['status']}) | "
                     f"{f(m['no-slip']['value'])} ({m['no-slip']['status']}) | {v['holds']} |")
    lines += ["", "## Reported, not part of the verdict", "",
              "| Item | Specimen | Test | Tolerance | Frictionless | No-slip | Within |", "|---|---|---|---|---|---|---|"]
    for k, v in result["reported"].items():
        if k.startswith("mesh flag"):
            continue
        m = v["models"]
        lines.append(f"| {k} | {v['specimen']} | {f(v['test']['value'])} | {f(v['test']['tolerance'])} | "
                     f"{f(m['frictionless']['value'])} | {f(m['no-slip']['value'])} | {v['holds']} |")
    lines += ["", "| Mesh flag | Coarse | Medium | Ratio | Flagged |", "|---|---|---|---|---|"]
    for k, v in result["reported"].items():
        if k.startswith("mesh flag"):
            lines.append(f"| {k[10:]} | {f(v['coarse'])} | {f(v['medium'])} | {f(v['ratio'], 4)} | {v['flagged']} |")
    return "\n".join(lines) + "\n"


__all__ = ["points_of", "at_point", "model_quantity", "bracket", "evaluate", "numbers_markdown"]
