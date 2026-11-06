"""Evaluate gate G-C2.1 as pre-specified: the metrics of every arm and seed on the held-out and tested instances at
the evaluation levels, the criteria on the label-free arm, the verdict. Writes <runs>/verdict.json.

Every metric is computed in float64 by the reference code on the exported problem (c2.instance.ExportedProblem),
never by the training code. A run's status comes from its files, as for gate G-C1.3: a history.json whose status
starts with "non-finite" means a final stop; otherwise predictions (preds.npz) mean finished, and their absence means
missing. A label-free seed that stopped enters the medians over seeds with infinite errors; a missing label-free seed
makes the verdict INCOMPLETE. Supervised seeds do not enter the verdict.

Within a finished run, a pair whose reference solve at the predicted end displacement fails, or gives a force that
is not positive, has an infinite curve error, which enters the median and the 90th percentile as such; a pair whose
energy the reference code cannot evaluate has not-a-number in the reported metrics only (counted in the summary).
A member whose metrics fail altogether leaves the run without an eval summary, and the seed then counts as
infinite."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .data import load_export, load_label, manifest, check_files
from .instance import ExportedProblem

TOL = 1e-3            # contact: u_x <= TOL (D + delta) on the plane between the flanges, prediction and reference


def _iou(a, b):
    u = int((a | b).sum())
    return 1.0 if u == 0 else float((a & b).sum() / u)


def metrics(P: ExportedProblem, ex: dict, z, ref: dict, ref_plastic: np.ndarray, l: int, curve: bool = True) -> dict:
    """Metrics of one predicted field z at level l against the reference (label arrays).

    The prediction's point on the force-deformation plane is (e, F), F = 4 k_s (D - e) its spring reading, both read
    from z alone. The judged error is the distance of that point from the reference curve, read in force at the
    predicted deformation: F / F*(e) - 1, F*(e) the reference force at end displacement e (an exact solve under
    displacement control, warm-started from the label nearest in e). It does not depend on the loading device; it
    is infinite when that solve does not converge or the reference force there is not positive. The other metrics
    need the energy of the field; if the reference code cannot evaluate it, they are not-a-number and
    evaluate_failed is set. Also returned: the error of F against the reference at the same D, with its certified
    bound 4 sqrt(2 k_s (Pi - Pi*))."""
    z = np.asarray(z, dtype=np.float64)
    D = float(ref["D"][l])
    zr = ref["z"][l]
    assert np.all(z[P.prob.fixed] == 0), "a fixed unknown is not zero"
    assert (z[P.prob.cidx] >= 0).all(), "a contact unknown is negative"
    e_pred = float(z[P.e_idx])
    F = 4.0 * P.k_s * (D - e_pred)
    Fr, Pr, er = float(ref["F"][l]), float(ref["Pi"][l]), float(ref["e"][l])
    curve_err, curve_note = float("nan"), ""
    if curve:
        near = int(np.argmin(np.abs(np.asarray(ref["e"]) - e_pred)))     # warm start: the label nearest in e
        try:
            c = P.solve_at_e(e_pred, z0=ref["z"][near])
            curve_err = F / c["F"] - 1 if (c["converged"] and c["F"] > 0) else float("inf")
            if not c["converged"]:
                curve_note = "the reference at the predicted end displacement did not converge"
            elif c["F"] <= 0:
                curve_note = "the reference force at the predicted end displacement is not positive"
        except Exception as err:                       # any failure of that solve: an infinite error for this pair
            curve_err, curve_note = float("inf"), f"{type(err).__name__}: {err}"
    out = {"D": D, "curve_err": curve_err, "abs_curve_err": abs(curve_err), "curve_note": curve_note,
           "F_err": F / Fr - 1, "abs_F_err": abs(F / Fr - 1), "e_err": e_pred / er - 1, "evaluate_failed": False}
    try:
        e = P.evaluate(z, D)
    except Exception as err:
        nan = float("nan")
        out.update(F_sigma_err=nan, gap=nan, bound=nan, within_bound=True, iou_contact=nan, iou_plastic=nan,
                   bolt_err=nan, u_rel_l2=nan, evaluate_failed=f"{type(err).__name__}: {err}")
        return out
    gap = e["Pi"] - Pr
    s = D + float(ex["delta"])
    plane = 3 * np.nonzero(np.asarray(ex["node_flags"])[:, 0])[0]
    u, ur = P.T @ z, P.T @ zr
    bound = 4.0 * np.sqrt(2.0 * P.k_s * max(gap, 0.0))
    out.update(F_sigma_err=e["F_sigma"] / Fr - 1, gap=gap / abs(Pr), bound=bound / abs(Fr),
               within_bound=bool(abs(F - Fr) <= bound * (1 + 1e-9) + 1e-9 * abs(Fr)),
               iou_contact=_iou(z[plane] <= TOL * s, zr[plane] <= TOL * s),
               iou_plastic=_iou(e["plastic"], ref_plastic),
               bolt_err=e["bolt_N"] / float(ref["bolt_N"][l]) - 1,
               u_rel_l2=float(np.linalg.norm(u - ur) / np.linalg.norm(ur)))
    return out


def _member(job):
    """All metrics of one member: its predictions for every finished run (dict run -> (L, n_z))."""
    data_dir, iid, preds = job
    ex, _ = load_export(Path(data_dir) / "inst" / f"{iid}.npz")
    ref = load_label(data_dir, iid)
    P = ExportedProblem(ex)
    ref_pl = [P.evaluate(ref["z"][l], float(ref["D"][l]))["plastic"] for l in range(ref["D"].size)]
    out = {}
    for run, Z in preds.items():
        try:
            out[run] = [metrics(P, ex, Z[l], ref, ref_pl[l], l) for l in range(ref["D"].size)]
        except Exception as err:                           # a prediction the reference code cannot evaluate
            out[run] = {"error": f"{type(err).__name__}: {err}"}
    return iid, out


def _quantile(v, q: float) -> float:
    """np.quantile (its linear interpolation) with infinite values kept infinite. The quantile is infinite when an
    infinite order statistic has a positive weight in the interpolation; otherwise it is np.quantile's value, computed
    with finite stand-ins for the infinite values (on the infinities themselves np.quantile gives not-a-number, even
    when their weight is zero)."""
    v = np.asarray(v, dtype=float)
    s = np.sort(v)
    h = (s.size - 1) * q
    lo = int(np.floor(h))
    nxt, t = min(lo + 1, s.size - 1), h - lo
    for x, weight in ((s[lo], 1.0 - t), (s[nxt], t)):
        if np.isinf(x) and weight > 0:
            return float(x)
    big = np.finfo(float).max / 4
    return float(np.quantile(np.where(np.isinf(v), np.sign(v) * big, v), q))


def _summary(rows: list[dict]) -> dict:
    out = {}
    for k in ("curve_err", "abs_curve_err", "F_err", "abs_F_err", "F_sigma_err", "e_err", "gap", "bound",
              "iou_contact", "iou_plastic", "bolt_err", "u_rel_l2"):
        v = np.array([r[k] for r in rows], dtype=float)
        if k != "abs_curve_err":                   # the reported metrics: over the pairs the reference code evaluated
            v = v[~np.isnan(v)]
        out[k] = {"median": _quantile(v, 0.5), "p10": _quantile(v, 0.1), "p90": _quantile(v, 0.9),
                  "min": float(v.min()), "max": float(v.max()), "mean": float(v.mean()), "n": int(v.size)} \
            if v.size else {"n": 0}
    ok = [r for r in rows if not r["evaluate_failed"]]
    out["within_bound_fraction"] = float(np.mean([r["within_bound"] for r in ok])) if ok else None
    out["evaluate_failed"] = int(sum(bool(r["evaluate_failed"]) for r in rows))
    out["curve_infinite"] = int(sum(np.isinf(r["curve_err"]) for r in rows))
    return out


def run_status(run: Path) -> str:
    hp = run / "history.json"
    if hp.exists() and str(json.loads(hp.read_text()).get("status", "")).startswith("non-finite"):
        return "non-finite"
    return "finished" if (run / "preds.npz").exists() else "missing"


def evaluate(cfg: dict, data_dir, runs_dir, workers: int = 1) -> dict:
    from .config import sha256

    man = manifest(data_dir)
    assert man["config_sha256"] == sha256(cfg), "the data were generated under another configuration"
    split_of = {r["id"]: r["split"] for r in man["instances"]}
    ids = [i for i, s in split_of.items() if s in cfg["evaluation"]["sets"]]
    check_files(data_dir, ids)
    out = {"config_sha256": sha256(cfg), "arms": {}, "status": {}, "missing": [], "non_finite": []}
    finished = []
    for arm, a in cfg["arms"].items():
        for seed in a["seeds"]:
            name = f"{arm}_s{seed}"
            st = out["status"][name] = run_status(Path(runs_dir) / name)
            if st == "finished":
                finished.append(name)
            else:
                out["missing" if st == "missing" else "non_finite"].append(name)
    preds = {}
    for name in finished:
        with np.load(Path(runs_dir) / name / "preds.npz") as z:
            preds[name] = {iid: z[iid] for iid in ids}
    jobs = [(str(data_dir), iid, {name: preds[name][iid] for name in finished}) for iid in sorted(ids)]
    if workers <= 1:
        results = [_member(j) for j in jobs]
    else:
        import multiprocessing as mp
        with mp.get_context("fork").Pool(workers) as pool:
            results = sorted(pool.imap_unordered(_member, jobs), key=lambda r: r[0])   # the order of a single worker
    per = {name: {"eval": {}, "tested": {}, "errors": {}} for name in finished}
    for iid, res in results:
        for name, rows in res.items():
            if isinstance(rows, dict):
                per[name]["errors"][iid] = rows["error"]
            else:
                per[name]["eval" if split_of[iid] == "eval" else "tested"][iid] = rows
    n_eval = cfg["data"]["n_eval"]
    for name in finished:
        arm, seed = name.rsplit("_s", 1)
        p = per[name]
        rows = [r for v in p["eval"].values() for r in v]
        entry = {"errors": p["errors"], "tested": dict(sorted(p["tested"].items())),
                 "eval_rows": dict(sorted(p["eval"].items()))}
        if len(p["eval"]) == n_eval:
            entry["eval"] = _summary(rows)
        out["arms"].setdefault(arm, {})[seed] = entry
    lf = cfg["arms"]["label_free"]["seeds"]
    if any(out["status"][f"label_free_s{s}"] == "missing" for s in lf):
        out["verdict"] = "INCOMPLETE"
        out["arms"]["label_free"] = {"withheld": "the verdict is INCOMPLETE"}
    else:
        med, p90 = [], []
        for s in lf:
            e = out["arms"].get("label_free", {}).get(str(s), {})
            if out["status"][f"label_free_s{s}"] == "non-finite" or "eval" not in e:
                med.append(float("inf")); p90.append(float("inf"))
            else:
                med.append(e["eval"]["abs_curve_err"]["median"]); p90.append(e["eval"]["abs_curve_err"]["p90"])
        out["per_seed"] = {"abs_curve_err_median": med, "abs_curve_err_p90": p90}
        out["C1_value"] = _quantile(med, 0.5)
        out["C2_value"] = _quantile(p90, 0.5)
        assert not (np.isnan(out["C1_value"]) or np.isnan(out["C2_value"])), "a criterion value is not a number"
        out["C1"] = bool(out["C1_value"] <= 0.05)
        out["C2"] = bool(out["C2_value"] <= 0.10)
        out["verdict"] = "PASS" if (out["C1"] and out["C2"]) else "FAIL"
    tmp = Path(runs_dir) / "verdict.tmp"
    tmp.write_text(json.dumps(out, indent=1))
    tmp.replace(Path(runs_dir) / "verdict.json")
    return out
