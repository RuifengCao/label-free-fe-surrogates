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
A level whose solve raises a numerical error (see _numerical) is recorded as not converged, with the error and NaN
readings, and the path stops; a case whose preload raises one is recorded with the error and no levels. Any other
error stops the run. The preload state counts as converged only if its solve converged and every bolt carries its
target to a relative 1e-6.
Readings are taken relative to the preload state: Theta_D (bending) and the mean ring displacement delta (axial).
Each record is written when its case ends, to a temporary file renamed into place, so a run cut off part way
leaves only whole records; it carries the SHA-256 of the configuration it was run with.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np

from fejoint import chs

from .config import PLATES, TUBE, KKT_LIMITS, canonical
from .materials import material
from .readings import measured_preload

# Errors of a solve that end the path (or the case, in the preload) instead of the run: the contact solver's and
# the bubble condensation's RuntimeError, SuperLU's RuntimeError on a singular factor, numpy's LinAlgError and
# arithmetic errors. NotImplementedError and RecursionError, though RuntimeErrors, are programming errors and stop
# the run, as does every other error (running out of memory included, so that the case is tried again on restart).
NUMERICAL_ERRORS = (RuntimeError, ArithmeticError, np.linalg.LinAlgError)
PRELOAD_TOL = 1e-6


def _numerical(e: BaseException) -> bool:
    return isinstance(e, NUMERICAL_ERRORS) and not isinstance(e, (NotImplementedError, RecursionError))


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


def _failed_level(value: float, error: BaseException, n_bolts: int, seconds: float) -> dict:
    """A level whose solve raised a numerical error: not converged, no readings (NaN), the error kept."""
    nan = float("nan")
    return {"control_value": value, "M_kNm": nan, "T_kN": nan, "Theta_D": nan, "delta_mm": nan, "theta_section": nan,
            "bolts_kN": [nan] * n_bolts, "converged": False, "kkt": None, "kkt_ok": False, "plastic_points": None,
            "max_von_mises": None, "newton_iterations": None, "pdas_iterations": None, "reaction_y_N": None,
            "error": f"{type(error).__name__}: {error}", "seconds": round(seconds, 1)}


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
    case = {"specimen": name, "splice": splice, "theory": theory, "preload": preload, "mesh": mesh}
    targets_N = preload_targets(name, cfg, preload)
    rec = {"case": case, "meta": {k: v for k, v in m.meta.items() if k != "mesh"}, "mesh": m.meta["mesh"],
           "preload": {}, "control": ld["control"], "levels": []}
    try:
        pre = m.set_preload(targets_N)
        z0, rep0 = m.solve(0.0, tol=cfg["solver"]["tol"], max_it=cfg["solver"]["max_it"])
        r0 = m.readings(z0, rep0)
    except Exception as e:
        if not _numerical(e):
            raise
        rec["preload"] = {"targets_kN": (np.atleast_1d(targets_N) / 1e3).tolist(), "forces_kN": [float("nan")] * m.nb,
                          "converged": False, "kkt_ok": False, "error": f"{type(e).__name__}: {e}"}
        log(json.dumps({"case": case, "preload_error": rec["preload"]["error"]}))
        rec["seconds"] = round(time.time() - t0, 1)
        return rec
    on_target = bool(np.all(np.abs(pre["forces_N"] / targets_N - 1.0) < PRELOAD_TOL))
    rec["preload"] = {"targets_kN": (np.atleast_1d(targets_N) / 1e3).tolist(),
                      "forces_kN": (pre["forces_N"] / 1e3).tolist(), "delta_mm": pre["delta"].tolist(),
                      "iterations": pre["iterations"], "on_target": on_target,
                      "converged": bool(rep0["converged"]) and on_target,
                      "kkt": r0["kkt"], "kkt_ok": kkt_ok(r0["kkt"]), "max_von_mises": r0["max_von_mises"],
                      "plastic_points": r0["plastic_points"]}
    ref = {"Theta_D": r0["Theta_D"], "delta_ring_mm": r0["delta_ring_mm"], "theta_section": r0["theta_section"]}
    seq = values if values is not None else [round(ld["step"] * k, 10) for k in range(1, int(round(ld["max"] / ld["step"])) + 1)]
    for v in seq:
        t1 = time.time()
        try:
            lev = _level(m, v, ld["control"], ref, cfg["solver"])
        except Exception as e:
            if not _numerical(e):
                raise
            lev = _failed_level(v, e, m.nb, time.time() - t1)
        rec["levels"].append(lev)
        log(json.dumps({"case": rec["case"], "value": v, "M_kNm": round(lev["M_kNm"], 3), "T_kN": round(lev["T_kN"], 2),
                        "Theta_D": lev["Theta_D"], "delta_mm": lev["delta_mm"], "converged": lev["converged"],
                        "kkt_ok": lev["kkt_ok"], "s": lev["seconds"], **({"error": lev["error"]} if "error" in lev else {})}))
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
    rec["config_sha256"] = hashlib.sha256(canonical(cfg).encode()).hexdigest()
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(rec, indent=1))
    os.replace(tmp, path)
    return path


__all__ = ["geometry", "model", "run_path", "run_case", "cases", "case_id", "kkt_ok", "bracket_values"]
