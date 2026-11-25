"""Evaluate a development run of the CHS surrogate (exploratory, not a gate): the metrics of every finished seed in
both readings on the evaluated members at the evaluation levels. Writes <runs>/evaluation.json. Follows
c2/evaluate.py and c22/evaluate.py.

Every metric is computed in float64 by the reference code on the exported problem (f2.instance.ExportedProblem),
never by the training code. Before every exact solve and every energy the problem is cleared of what earlier
solves left in it (clean): the elements' bubble parameters, which start the element iteration of the next
evaluation, and the contact state, which starts the next active-set search. A result then depends on its own inputs
only, whatever the order of the members, runs, readings and levels. (Gate G-C2.3's recomputation found that without
this the element iteration can fail from a state left by another solve.)

What is read from a predicted field z at a level's device rotation Theta, from z alone: the end rotation theta, the
spring moment M = 2 k_th (Theta - theta) and the tests' rotation Theta_D.

    curve_err      M / M*(theta) - 1: the distance of the point (theta, M) from the reference curve, read in moment
                   at the predicted end rotation; M*(theta) from one exact solve under rotation control, started
                   from the labelled solution nearest in end rotation. Infinite when that solve fails or gives a
                   moment that is not positive.
    curveD_err     the same distance in the tests' rotation, M / M*(Theta_D) - 1, to first order: the exact solve at
                   the predicted end rotation gives a point (Theta_D', M') of the reference curve, and
                   M*(Theta_D) ~ M' + dM*/dTheta_D (Theta_D - Theta_D'), the slope from a monotone cubic through
                   the labelled path. With exact=True the reference at the predicted Theta_D is solved for
                   (ExportedProblem.solve_at_ThetaD) and curveD_exact_err is added; with a list of readings in
                   the place of True, for those readings only (each pair then costs several more solves).
    M_err, theta_err, ThetaD_err     against the labelled solution at the same device rotation.
    gap, bound     the energy gap (Pi - Pi*) / Pi* and the certified bound 2 sqrt(2 k_th (Pi - Pi*)) / M* on M_err.
    M_sigma_err, bolt_err_max, bolt1_err, u_rel_l2, iou_contact, iou_plastic     as in G-C2.1.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

from c2.evaluate import _quantile
from c22.data import THREAD_VARIABLES, _write_json
from .data import load_export, load_label, manifest, check_files
from .instance import ExportedProblem, FLAGS
from .model import L_REF

TOL = 1e-3            # contact: gap <= TOL (L_REF Theta + delta) on the splice plane, prediction and reference alike
FILES = {"raw": "preds.npz", "condensed": "preds_condensed.npz"}
KEYS = ("curve_err", "abs_curve_err", "curveD_err", "abs_curveD_err", "M_err", "abs_M_err", "theta_err", "ThetaD_err",
        "M_sigma_err", "gap", "bound", "bolt_err_max", "bolt1_err", "u_rel_l2", "iou_contact", "iou_plastic")


def pool(workers: int):
    """A pool of worker processes for the solves: forked where the operating system can, as c22.data.pool, unless
    torch is loaded in this process; then, and where the system cannot fork, spawned, each worker told to use one
    thread for linear algebra. A fork of a process that has trained with torch can wait for ever on a lock that
    another thread held at the fork (seen once, on 25 November 2026, in a process that trained and then evaluated).
    The command-line evaluations do not load torch and fork as they always have."""
    import multiprocessing as mp

    kind = "fork" if ("fork" in mp.get_all_start_methods() and "torch" not in sys.modules) else "spawn"
    if kind == "spawn":
        for k in THREAD_VARIABLES:
            os.environ.setdefault(k, "1")
    return mp.get_context(kind).Pool(workers)


def clean(P: ExportedProblem) -> None:
    """Forget what earlier solves left in the problem: the elements' bubble parameters and the contact state."""
    for s in P.solids:
        s.bub[:] = 0.0
        s._trial = None
    P.prob.active = None
    P.prob_th.active = None


def _iou(a, b) -> float:
    u = int((a | b).sum())
    return 1.0 if u == 0 else float((a & b).sum() / u)


def path_slope(ref: dict):
    """dM*/dTheta_D along the labelled path (with the preload state, where both are zero), as a function of
    Theta_D: the derivative of the monotone cubic through the labelled points."""
    from scipy.interpolate import PchipInterpolator

    x = np.concatenate([[0.0], np.asarray(ref["ThetaD"], float)])
    y = np.concatenate([[0.0], np.asarray(ref["M"], float)])
    assert np.all(np.diff(x) > 0), "Theta_D does not rise along the labelled path"
    return PchipInterpolator(x, y, extrapolate=True).derivative()


def metrics(P: ExportedProblem, ex: dict, z, ref: dict, ref_plastic: np.ndarray, l: int, slope, tol: float = 1e-12,
            max_it: int = 80, curve: bool = True, exact: bool = False) -> dict:
    """Metrics of one predicted field z at level l against the reference (label arrays). See the module's text."""
    z = np.asarray(z, dtype=np.float64)
    Theta = float(ref["Theta"][l])
    zr = ref["z"][l]
    assert np.all(z[P.prob.fixed] == 0), "a fixed unknown is not zero"
    assert (z[P.prob.cidx] >= 0).all(), "a contact unknown is negative"
    th = float(z[P.ith])
    M = 2.0 * P.k_th * (Theta - th)
    TD = float((P.tD @ z)[0]) / P.d - P.ThetaD_pre
    Mr, thr, TDr, Pr = float(ref["M"][l]), float(ref["theta"][l]), float(ref["ThetaD"][l]), float(ref["Pi"][l])
    out = {"lam": float(ref["lam"][l]), "Theta": Theta, "theta": th, "M": M, "ThetaD": TD, "M_ref": Mr,
           "theta_ref": thr, "ThetaD_ref": TDr, "M_err": M / Mr - 1, "abs_M_err": abs(M / Mr - 1),
           "theta_err": th / thr - 1, "ThetaD_err": TD / TDr - 1, "evaluate_failed": False}
    nan = float("nan")
    ce, cde, note = nan, nan, ""
    if curve:
        near = int(np.argmin(np.abs(np.asarray(ref["theta"]) - th)))     # warm start: the label nearest in theta
        try:
            clean(P)
            c = P.solve_at_theta(th, z0=ref["z"][near], tol=tol, max_it=max_it)
            if c["converged"] and c["M"] > 0:
                ce = M / c["M"] - 1
                M_at_TD = c["M"] + float(slope(c["ThetaD"])) * (TD - c["ThetaD"])
                cde = M / M_at_TD - 1 if M_at_TD > 0 else float("inf")
                out.update(M_curve=float(c["M"]), ThetaD_curve=float(c["ThetaD"]), curve_iterations=c["iterations"])
            else:
                ce = cde = float("inf")
                note = ("the reference at the predicted end rotation did not converge" if not c["converged"]
                        else "the reference moment at the predicted end rotation is not positive")
        except Exception as err:                       # any failure of that solve: an infinite error for this pair
            ce = cde = float("inf")
            note = f"{type(err).__name__}: {err}"
        if exact and np.isfinite(ce):
            try:
                clean(P)
                r = P.solve_at_ThetaD(TD, theta0=th * TD / c["ThetaD"], z0=c["z"], tol=tol, max_it=max_it)
                out["curveD_exact_err"] = M / r["M"] - 1 if (r.get("found") and r["M"] > 0) else float("inf")
                out["curveD_exact_solves"] = int(r["solves"])
            except Exception as err:
                out["curveD_exact_err"] = float("inf")
                note += f" | exact Theta_D: {type(err).__name__}: {err}"
    out.update(curve_err=ce, abs_curve_err=abs(ce), curveD_err=cde, abs_curveD_err=abs(cde), curve_note=note)
    try:
        clean(P)
        e = P.evaluate(z, Theta)
    except Exception as err:
        out.update(M_sigma_err=nan, gap=nan, bound=nan, within_bound=True, iou_contact=nan, iou_plastic=nan,
                   bolt_err_max=nan, bolt1_err=nan, u_rel_l2=nan, evaluate_failed=f"{type(err).__name__}: {err}")
        return out
    gap = e["Pi"] - Pr
    s = L_REF * Theta + float(np.asarray(ex["delta"]).ravel()[0])
    plane = 3 * np.nonzero(np.asarray(ex["node_flags"])[:, FLAGS.index("splice_plane")])[0] + 2
    u, ur = P.T @ z, P.T @ zr
    bound = 2.0 * np.sqrt(2.0 * P.k_th * max(gap, 0.0))
    bolt = np.asarray(e["bolt_N"], float) / np.asarray(ref["bolt_N"][l], float) - 1.0
    out.update(M_sigma_err=e["M_sigma"] / Mr - 1, gap=gap / abs(Pr), bound=bound / abs(Mr),
               within_bound=bool(abs(M - Mr) <= bound * (1 + 1e-9) + 1e-9 * abs(Mr)),
               iou_contact=_iou(z[plane] <= TOL * s, zr[plane] <= TOL * s),
               iou_plastic=_iou(e["plastic"], ref_plastic),
               bolt_err_max=float(np.abs(bolt).max()), bolt1_err=float(bolt[0]),
               u_rel_l2=float(np.linalg.norm(u - ur) / np.linalg.norm(ur)))
    return out


def _member(job):
    """All metrics of one member: its predictions for every finished run and reading (dict key -> (L, n_z))."""
    data_dir, iid, preds, tol, max_it, exact = job           # exact: True, False, or the readings it is solved for
    ex, _ = load_export(Path(data_dir) / "inst" / f"{iid}.npz")
    ref = load_label(data_dir, iid)
    P = ExportedProblem(ex)
    L = ref["Theta"].size
    ref_pl = []
    for l in range(L):
        clean(P)
        ref_pl.append(P.evaluate(ref["z"][l], float(ref["Theta"][l]))["plastic"])
    slope = path_slope(ref)
    out = {}
    for key, Z in preds.items():
        try:
            x = exact if isinstance(exact, bool) else key.split("|", 1)[1] in exact
            out[key] = [metrics(P, ex, Z[l], ref, ref_pl[l], l, slope, tol, max_it, exact=x) for l in range(L)]
        except Exception as err:                           # a prediction the reference code cannot evaluate
            out[key] = {"error": f"{type(err).__name__}: {err}"}
    return iid, out


def _summary(rows: list[dict]) -> dict:
    out = {}
    for k in KEYS:
        v = np.array([r.get(k, np.nan) for r in rows], dtype=float)
        if k not in ("abs_curve_err", "abs_curveD_err"):  # reported metrics: over the pairs that have a value
            v = v[~np.isnan(v)]
        out[k] = {"median": _quantile(v, 0.5), "p10": _quantile(v, 0.1), "p90": _quantile(v, 0.9),
                  "min": float(v.min()), "max": float(v.max()), "n": int(v.size)} if v.size else {"n": 0}
    ok = [r for r in rows if not r["evaluate_failed"]]
    out["within_bound_fraction"] = float(np.mean([r["within_bound"] for r in ok])) if ok else None
    out["evaluate_failed"] = int(sum(bool(r["evaluate_failed"]) for r in rows))
    out["curve_infinite"] = int(sum(np.isinf(r["curve_err"]) for r in rows))
    return out


def run_status(run: Path) -> str:
    from .train import predictions_written

    hp = Path(run) / "history.json"
    if hp.exists() and str(json.loads(hp.read_text()).get("status", "")).startswith("non-finite"):
        return "non-finite"
    return "finished" if predictions_written(run) else "missing"


def evaluate(cfg: dict, data_dir, runs_dir, workers: int = 1, exact=False, only=None, seeds=None,
             write: bool = True) -> dict:
    """Metrics of every finished seed of the configuration in both readings. only: a list of member ids to restrict
    the evaluation to (default: every evaluated member of the configuration that has predictions and a label).
    exact: True to solve the reference at the predicted Theta_D for both readings, or a list of the readings to
    solve it for (the file names them under "exact_readings").
    seeds: other seeds than the configuration's, trained under the same configuration (development: more seeds of
    a run); the result then goes to evaluation_seeds_<a>_<b>.json and leaves evaluation.json as it is.
    write: False to return the result without writing it (a caller that adds to it before it writes it)."""
    from .config import sha256
    from .train import check_manifest, evaluated_ids

    cfg_sha = sha256(cfg)
    man = check_manifest(cfg, data_dir)
    split_of = {r["id"]: r["split"] for r in man["instances"]}
    ids = [i for i in evaluated_ids(cfg, man) if only is None or i in only]
    check_files(data_dir, ids)
    ls = cfg["data"]["label_solver"]
    if not isinstance(exact, bool):
        exact = tuple(str(r) for r in exact)
        if not exact or any(r not in FILES for r in exact):
            raise ValueError(f"exact must be True, False or a list of readings among {sorted(FILES)}")
    out = {"what": cfg["gate"], "preset": cfg.get("preset"), "config_sha256": cfg_sha, "exact_ThetaD": bool(exact),
           "members": ids, "status": {}, "rows": {}, "summary": {}}
    if exact:                                              # a file without exact solves keeps its keys
        out["exact_readings"] = sorted(FILES) if exact is True else sorted(exact)
    preds = {}
    if seeds is not None:
        out["seeds"] = [int(x) for x in seeds]
    for seed in (cfg["arms"]["label_free"]["seeds"] if seeds is None else out["seeds"]):
        run = Path(runs_dir) / f"label_free_s{seed}"
        st = out["status"][str(seed)] = run_status(run)
        if st != "finished":
            continue
        if json.loads((run / "history.json").read_text()).get("config_sha256") != cfg_sha:
            raise RuntimeError(f"{run} holds a run of another configuration")
        for reading, name in FILES.items():
            with np.load(run / name) as z:
                preds[f"{seed}|{reading}"] = {iid: z[iid] for iid in ids}
    jobs = [(str(data_dir), iid, {key: p[iid] for key, p in preds.items()}, ls["tol"], ls["max_it"], exact)
            for iid in sorted(ids)]
    t0, results = time.perf_counter(), []

    def done(r):                                           # a line a member, so that a log shows the evaluation going on
        results.append(r)
        print(r[0], f"evaluated, {len(results)} of {len(jobs)}, {time.perf_counter() - t0:.0f} s", flush=True)

    if workers <= 1:
        for j in jobs:
            done(_member(j))
    else:
        with pool(workers) as p:
            for r in p.imap_unordered(_member, jobs):
                done(r)
    results.sort(key=lambda r: r[0])
    for key in preds:
        rows, errors = {}, {}
        for iid, res in results:
            if isinstance(res[key], dict):
                errors[iid] = res[key]["error"]
            else:
                rows[iid] = res[key]
        out["rows"][key] = {"members": rows, "errors": errors}
        sets = sorted({split_of[i] for i in rows})
        summ = {s: _summary([r for i, v in rows.items() if split_of[i] == s for r in v]) for s in sets}
        if rows:
            summ["all"] = _summary([r for v in rows.values() for r in v])
        out["summary"][key] = summ
    name = "evaluation.json" if seeds is None else "evaluation_seeds_" + "_".join(str(x) for x in out["seeds"]) + ".json"
    if write:
        _write_json(Path(runs_dir) / name, out)
    return out


def label_summary(data_dir) -> dict:
    """The labelled solutions' readings without their fields (a small file for looking at snapshots elsewhere):
    labels/summary.json."""
    data_dir = Path(data_dir)
    led = json.loads((data_dir / "labels" / "ledger.json").read_text())
    out = {}
    for e in led:
        lab = load_label(data_dir, e["id"])
        out[e["id"]] = {k: np.asarray(lab[k], float).tolist() for k in ("lam", "Theta", "Pi", "theta", "M", "ThetaD")}
        out[e["id"]]["bolt_N"] = np.asarray(lab["bolt_N"], float).tolist()
    _write_json(data_dir / "labels" / "summary.json", out)
    return out


def quicklook(summary: dict, snaps: dict) -> dict:
    """Snapshots against the labelled readings, without any solve: per snapshot epoch and member, the moment against
    the label at the same device rotation, and the distance from the labelled path read by a monotone cubic through
    its points (an approximation of curve_err; the path has the preload state and seven levels)."""
    from scipy.interpolate import PchipInterpolator

    out = {}
    for epoch, members in snaps.items():
        rows = {}
        for iid, s in members.items():
            if iid not in summary:
                continue
            lab = summary[iid]
            Mr = np.asarray(lab["M"], float)
            f = PchipInterpolator(np.concatenate([[0.0], lab["theta"]]), np.concatenate([[0.0], Mr]), extrapolate=True)
            g = PchipInterpolator(np.concatenate([[0.0], lab["ThetaD"]]), np.concatenate([[0.0], Mr]), extrapolate=True)
            M, th, TD = (np.asarray(s[k], float) for k in ("M", "theta", "ThetaD"))
            with np.errstate(divide="ignore", invalid="ignore"):
                rows[iid] = {"M_err": (M / Mr - 1).tolist(), "curve_err_approx": (M / f(th) - 1).tolist(),
                             "curveD_err_approx": (M / g(TD) - 1).tolist(),
                             "gap32": (np.asarray(s["Pi"], float) / np.asarray(lab["Pi"], float) - 1).tolist()}
        allv = {k: np.abs(np.array([v for r in rows.values() for v in r[k]], float)) for k in
                ("M_err", "curve_err_approx", "curveD_err_approx")}
        out[epoch] = {"members": rows,
                      "summary": {k: {"median": float(np.nanmedian(v)), "p90": float(np.nanquantile(v, 0.9)),
                                      "max": float(np.nanmax(v))} for k, v in allv.items() if v.size}}
    return out


__all__ = ["clean", "metrics", "evaluate", "label_summary", "quicklook", "path_slope", "run_status", "KEYS", "TOL"]
