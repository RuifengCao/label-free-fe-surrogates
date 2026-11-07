"""Model runs of gate G-F1: one case per call, a JSON record per case.

A case is (specimen, splice, theory, preload, mesh):
  splice   "frictionless" or "no-slip" (fejoint.chs.SpliceModel);
  theory   "hencky" (J2 deformation theory, f1/materials.py; the gated cases) or "elastic";
  preload  "nominal" (125 kN in every bolt) or "measured" (bolts 1 to 6 at their forces in Fig. 3.4 at the lower
           bolt moment; reported only);
  mesh     "coarse" (every path) or "medium" (the mesh flag: elastic, at the levels that bracket the comparison
           points on the coarse elastic path).
Each case sets the preload at zero load, then loads in equal steps of the end-section rotation theta (bending) or
the end-section axial displacement w0 (axial), each level warm-started from the previous one, until the stop rule
of the configuration holds or the cap is reached, or a level does not converge (recorded, then the path stops).
Readings are taken relative to the preload state: Theta_D (bending) and the mean ring displacement delta (axial).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from fejoint import chs

from .config import PLATES, TUBE, KKT_LIMITS
from .materials import material
from .readings import measured_preload


def _print(msg):
    print(msg, flush=True)


def geometry(name: str, cfg: dict) -> chs.FlangeSplice:
    s = cfg["specimens"][name]
    return chs.FlangeSplice(name=name, tp=s["tp"], e1=s["e1"], e2=s["e2"], E_p=PLATES[s["plate"]]["E"],
                            E_t=TUBE["E"])


def model(name: str, cfg: dict, splice: str, theory: str, mesh: str) -> chs.SpliceModel:
    g = geometry(name, cfg)
    plate = PLATES[cfg["specimens"][name]["plate"]]
    mats = {0: material(plate, theory), 1: material(TUBE, theory), 2: material(TUBE, theory)}
    return chs.SpliceModel(g, mesh, mats=mats, splice=splice)


def kkt_ok(kkt: dict) -> bool:
    for k, (op, lim) in KKT_LIMITS.items():
        v = kkt[k]
        if not np.isfinite(v) or (op == ">=" and v < lim) or (op == "<=" and v > lim):
            return False
    return True


def _level(m: chs.SpliceModel, value: float, control: str, ref: dict, solver: dict) -> dict:
    t0 = time.time()
    z, rep = m.solve(value, control=control, tol=solver["tol"], max_it=solver["max_it"])
    r = m.readings(z, rep)
    out = {"control_value": value, "M_kNm": r["M_kNm"], "T_kN": r["T_kN"],
           "Theta_D": r["Theta_D"] - ref["Theta_D"], "delta_mm": r["delta_ring_mm"] - ref["delta_ring_mm"],
           "theta_section": r["theta_section"] - ref["theta_section"], "bolts_kN": r["bolt_force_kN"],
           "converged": bool(r["converged"]), "kkt": r["kkt"], "kkt_ok": kkt_ok(r["kkt"]),
           "plastic_points": r["plastic_points"], "max_von_mises": r["max_von_mises"],
           "newton_iterations": r["iterations"], "pdas_iterations": r["pdas_iterations"],
           "reaction_y_N": r["reaction_y_N"], "seconds": round(time.time() - t0, 1)}
    return out


def _stop(name: str, cfg: dict, lev: dict) -> bool:
    pts = cfg["points"][name]
    if cfg["specimens"][name]["test"] == "bending":
        return lev["Theta_D"] >= 1.2 * pts["theta"] and lev["M_kNm"] >= max(pts["bolt_moments_kNm"]) + 5.0
    return lev["T_kN"] >= pts["T_kN"] + 50.0


def preload_targets(name: str, cfg: dict, preload: str):
    if preload == "nominal":
        return cfg["model"]["preload_kN"] * 1e3
    pts, tests = cfg["points"][name], cfg["tests"][name]
    return np.array(measured_preload(tests["bolt_forces"], pts["bolt_moments_kNm"][0])) * 1e3


def run_path(name: str, cfg: dict, splice: str, theory: str, preload: str, mesh: str, values=None,
             log=_print) -> dict:
    """The case's path. values: explicit control values (the mesh flag); otherwise the configured steps."""
    kind = cfg["specimens"][name]["test"]
    ld = cfg["loading"][kind]
    t0 = time.time()
    m = model(name, cfg, splice, theory, mesh)
    pre = m.set_preload(preload_targets(name, cfg, preload))
    z0, rep0 = m.solve(0.0, tol=cfg["solver"]["tol"], max_it=cfg["solver"]["max_it"])
    r0 = m.readings(z0, rep0)
    rec = {"case": {"specimen": name, "splice": splice, "theory": theory, "preload": preload, "mesh": mesh},
           "meta": {k: v for k, v in m.meta.items() if k != "mesh"}, "mesh": m.meta["mesh"],
           "preload": {"targets_kN": (np.atleast_1d(preload_targets(name, cfg, preload)) / 1e3).tolist(),
                       "forces_kN": (pre["forces_N"] / 1e3).tolist(), "delta_mm": pre["delta"].tolist(),
                       "iterations": pre["iterations"], "converged": bool(rep0["converged"]),
                       "kkt": r0["kkt"], "kkt_ok": kkt_ok(r0["kkt"]), "max_von_mises": r0["max_von_mises"],
                       "plastic_points": r0["plastic_points"]},
           "control": ld["control"], "levels": []}
    ref = {"Theta_D": r0["Theta_D"], "delta_ring_mm": r0["delta_ring_mm"], "theta_section": r0["theta_section"]}
    seq = values if values is not None else [round(ld["step"] * k, 10) for k in range(1, int(round(ld["max"] / ld["step"])) + 1)]
    for v in seq:
        lev = _level(m, v, ld["control"], ref, cfg["solver"])
        rec["levels"].append(lev)
        log(json.dumps({"case": rec["case"], "value": v, "M_kNm": round(lev["M_kNm"], 3), "T_kN": round(lev["T_kN"], 2),
                        "Theta_D": lev["Theta_D"], "delta_mm": lev["delta_mm"], "converged": lev["converged"],
                        "kkt_ok": lev["kkt_ok"], "s": lev["seconds"]}))
        if not lev["converged"]:
            break
        if values is None and _stop(name, cfg, lev):
            break
    rec["seconds"] = round(time.time() - t0, 1)
    return rec


def case_id(case: dict) -> str:
    return "_".join([case["specimen"], case["splice"], case["theory"], case["preload"], case["mesh"]])


def cases(cfg: dict) -> list:
    """Gated first, then reported; the mesh flag last (it needs the coarse elastic paths)."""
    out = []
    names = list(cfg["specimens"])
    for th in [cfg["model"]["theories"]["gated"]] + cfg["model"]["theories"]["reported"]:
        for n in names:
            for sp in cfg["model"]["splices"]:
                out.append({"specimen": n, "splice": sp, "theory": th, "preload": "nominal", "mesh": cfg["model"]["mesh"]})
    for n in cfg["model"]["measured_preload"]["specimens"]:
        for sp in cfg["model"]["splices"]:
            out.append({"specimen": n, "splice": sp, "theory": cfg["model"]["measured_preload"]["theory"],
                        "preload": "measured", "mesh": cfg["model"]["mesh"]})
    mf = cfg["model"]["mesh_flag"]
    for n in names:
        for sp in cfg["model"]["splices"]:
            out.append({"specimen": n, "splice": sp, "theory": mf["theory"], "preload": "nominal", "mesh": mf["mesh"]})
    return out


def bracket_values(name: str, cfg: dict, coarse: dict) -> list:
    """Control values of the coarse path's levels around each gated comparison point: the last level below it and
    the two after (the medium mesh's values differ a little, so its bracketing pair may shift by one level)."""
    from .verdict import points_of
    lv = coarse["levels"]
    vals = set()
    for key, target in points_of(name, cfg):
        xs = [l[key] for l in lv]
        i = next((k for k, x in enumerate(xs) if x >= target), None)
        if i is None:
            continue
        vals.update(lv[k]["control_value"] for k in range(max(i - 1, 0), min(i + 2, len(lv))))
    return sorted(vals)


def run_case(cfg: dict, case: dict, out: Path, log=_print) -> Path:
    out = Path(out); (out / "records").mkdir(parents=True, exist_ok=True)
    path = out / "records" / f"{case_id(case)}.json"
    if path.exists():
        log(f"{path.name} exists, skipped")
        return path
    values = None
    if case["mesh"] == cfg["model"]["mesh_flag"]["mesh"]:
        coarse = dict(case, mesh=cfg["model"]["mesh"])
        cpath = out / "records" / f"{case_id(coarse)}.json"
        if not cpath.exists():
            raise FileNotFoundError(f"the mesh flag needs {cpath.name} first")
        values = bracket_values(case["specimen"], cfg, json.loads(cpath.read_text()))
    rec = run_path(case["specimen"], cfg, case["splice"], case["theory"], case["preload"], case["mesh"], values, log)
    path.write_text(json.dumps(rec, indent=1))
    return path


__all__ = ["geometry", "model", "run_path", "run_case", "cases", "case_id", "kkt_ok", "bracket_values"]
