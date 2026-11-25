"""The first-order step of the judged quantity against the exact value, on members of the development (made on
25 November 2026, before the stamp of gate G-F2.1; no member of the gate's sample is touched).

The judged error of a pair (member, level) is M / M*(Theta_D) - 1: the predicted moment over the reference moment
at the predicted rotation of the measuring ring. f2/evaluate.py takes M*(Theta_D) to first order: one exact solve at
the predicted end rotation theta gives a point (Theta_D', M') of the reference curve, and
M*(Theta_D) ~ M' + s(Theta_D') (Theta_D - Theta_D'), with the slope s from scipy's PchipInterpolator through the
origin and the member's seven labelled points, continued beyond the last point by its last piece. The error depends
on the predicted field through three recorded numbers only (theta, M, Theta_D), so that both the first-order value
and the exact one can be computed again from an evaluation file, without the prediction files:

    python3 -I first_order.py estimate EVALUATION LABELS_SUMMARY KEY OUT.json
        from the records alone: the judged value computed again from each row's readings, the length of the
        first-order step, and what the cubic gives beyond the first order (an estimate of the neglected part);
    python3 -I first_order.py data PRESET DATA_DIR MEMBER,MEMBER,... [--workers N] [--manifest FILE --ledger FILE]
        the exports and the labels of the listed members of a development preset, in a folder of their own
        (the development's commands; with the recorded manifest and ledger, their hashes are compared);
    python3 -I first_order.py exact EVALUATION KEY PRESET DATA_DIR MEMBER,MEMBER,... OUT.json [--workers N]
        for each pair of the listed members: the solve at the recorded end rotation, compared with the row's
        record, and the reference at the recorded Theta_D itself (ExportedProblem.solve_at_ThetaD), as
        f2.evaluate.metrics makes them, with the number of solves and the seconds.

KEY is "<seed>|<reading>", for instance "0|condensed". The packages are looked for two folders above this file."""
import argparse
import json
import pathlib
import sys
import time

import numpy as np

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[2]


def _paths() -> None:
    here = pathlib.Path(__file__).resolve().parent
    sys.path[:] = [p for p in sys.path if not p or pathlib.Path(p).resolve() != here]
    sys.path.insert(0, str(ROOT))
    if (ROOT.parent / "src").is_dir():
        sys.path.insert(0, str(ROOT.parent / "src"))


def _stats(x) -> dict:
    x = np.asarray(x, float)
    return {"median": float(np.median(x)), "p90": float(np.quantile(x, 0.9)), "max": float(x.max()), "n": int(x.size)}


def estimate(a) -> dict:
    from scipy.interpolate import PchipInterpolator

    ev, lab = json.load(open(a.evaluation)), json.load(open(a.labels))
    rows = ev["rows"][a.key]["members"]
    per, diff, step, beyond, outside = {}, [], [], [], 0
    for iid in ev["members"]:
        b = lab[iid]
        f = PchipInterpolator(np.concatenate([[0.0], b["ThetaD"]]), np.concatenate([[0.0], b["M"]]), extrapolate=True)
        s = f.derivative()
        worst = 0.0
        for r in rows[iid]:
            M, TD, Mc, TDc = r["M"], r["ThetaD"], r["M_curve"], r["ThetaD_curve"]
            first = Mc + float(s(TDc)) * (TD - TDc)                 # the first-order reference moment, as f2.evaluate
            diff.append(abs((M / first - 1) - r["curveD_err"]))
            step.append(abs(TD - TDc) / TD)
            # the cubic's own change from Theta_D' to Theta_D against its first-order part: what the step leaves out
            beyond.append(abs((float(f(TD)) - float(f(TDc))) - float(s(TDc)) * (TD - TDc)) / first)
            outside += int(max(TD, TDc) > b["ThetaD"][-1])
            worst = max(worst, step[-1])
        per[iid] = worst
    order = sorted(per, key=lambda i: -per[i])
    out = {"evaluation": pathlib.Path(a.evaluation).name, "key": a.key, "pairs": len(step),
           "largest |recomputed - recorded| of the judged value": float(max(diff)),
           "relative length of the first-order step |Theta_D - Theta_D'| / Theta_D": _stats(step),
           "the cubic beyond the first order, relative to the reference moment": _stats(beyond),
           "pairs with a rotation beyond the last labelled point": outside,
           "members by their longest step": [[i, per[i]] for i in order]}
    return out


def data_cmd(a) -> dict:
    from f2 import data, devconfig

    cfg = devconfig.config(a.preset)
    ids = a.members.split(",")
    data.generate(cfg, a.data, workers=a.workers, only=ids)
    data.label(cfg, a.data, ids, workers=a.workers)
    man = {r["id"]: r for r in data.manifest(a.data)["instances"]}
    led = {e["id"]: e for e in json.loads((pathlib.Path(a.data) / "labels" / "ledger.json").read_text())}
    out = {"preset": a.preset, "members": ids, "solver": sorted({led[i]["solver"] for i in ids}),
           "converged": all(all(led[i]["converged"]) for i in ids)}
    if a.manifest and a.ledger:
        m0 = {r["id"]: r for r in json.load(open(a.manifest))["instances"]}
        l0 = {e["id"]: e for e in json.load(open(a.ledger))}
        out["export equal to the record's, by SHA-256"] = {i: man[i]["sha256"] == m0[i]["sha256"] for i in ids}
        out["label equal to the record's, by SHA-256"] = {i: led[i]["label_sha256"] == l0[i]["label_sha256"] for i in ids}
    return out


def _member(job):
    data_dir, iid, rows, tol, max_it = job
    from f2.data import load_export, load_label
    from f2.evaluate import clean, path_slope
    from f2.instance import ExportedProblem

    ex, _ = load_export(pathlib.Path(data_dir) / "inst" / f"{iid}.npz")
    ref = load_label(data_dir, iid)
    P = ExportedProblem(ex)
    slope = path_slope(ref)
    out = []
    for r in rows:
        th, M, TD = float(r["theta"]), float(r["M"]), float(r["ThetaD"])
        near = int(np.argmin(np.abs(np.asarray(ref["theta"]) - th)))
        t0 = time.perf_counter()
        clean(P)
        c = P.solve_at_theta(th, z0=ref["z"][near], tol=tol, max_it=max_it)
        t1 = time.perf_counter()
        first = c["M"] + float(slope(c["ThetaD"])) * (TD - c["ThetaD"])
        o = {"Theta": r["Theta"], "curve_converged": bool(c["converged"]),
             "M_curve_minus_record_relative": float(c["M"] / r["M_curve"] - 1),
             "ThetaD_curve_minus_record_relative": float(c["ThetaD"] / r["ThetaD_curve"] - 1),
             "first_order": float(M / first - 1), "recorded": float(r["curveD_err"]),
             "step": float(abs(TD - c["ThetaD"]) / TD), "curve_seconds": round(t1 - t0, 2)}
        clean(P)
        x = P.solve_at_ThetaD(TD, theta0=th * TD / c["ThetaD"], z0=c["z"], tol=tol, max_it=max_it)
        o.update(found=bool(x.get("found")), solves=int(x["solves"]), exact_seconds=round(time.perf_counter() - t1, 2),
                 exact=float(M / x["M"] - 1) if (x.get("found") and x["M"] > 0) else float("inf"))
        out.append(o)
    return iid, out


def exact(a) -> dict:
    from f2 import devconfig
    from f2.evaluate import pool

    ev = json.load(open(a.evaluation))
    rows = ev["rows"][a.key]["members"]
    ls = devconfig.config(a.preset)["data"]["label_solver"]
    ids = a.members.split(",")
    jobs = [(a.data, i, rows[i], ls["tol"], ls["max_it"]) for i in ids]
    t0, res = time.perf_counter(), {}
    if a.workers <= 1:
        it = map(_member, jobs)
        for iid, r in it:
            res[iid] = r
            print(iid, f"done, {len(res)} of {len(jobs)}, {time.perf_counter() - t0:.0f} s", flush=True)
    else:
        with pool(a.workers) as p:
            for iid, r in p.imap_unordered(_member, jobs):
                res[iid] = r
                print(iid, f"done, {len(res)} of {len(jobs)}, {time.perf_counter() - t0:.0f} s", flush=True)
    flat = [r for i in ids for r in res[i]]
    ok = [r for r in flat if np.isfinite(r["exact"])]
    d = [abs(r["first_order"] - r["exact"]) for r in ok]
    out = {"evaluation": pathlib.Path(a.evaluation).name, "key": a.key, "preset": a.preset, "members": ids,
           "pairs": len(flat), "pairs with the exact value": len(ok),
           "largest |first-order value computed here - recorded|": float(max(abs(r["first_order"] - r["recorded"]) for r in flat)),
           "largest relative difference of the solve at the end rotation from the record (moment, rotation)":
               [float(max(abs(r["M_curve_minus_record_relative"]) for r in flat)),
                float(max(abs(r["ThetaD_curve_minus_record_relative"]) for r in flat))],
           "|first-order - exact|, in units of the error (0.01 is one percentage point)": _stats(d) if d else None,
           "|recorded| of these pairs": _stats([abs(r["recorded"]) for r in ok]) if ok else None,
           "|exact| of these pairs": _stats([abs(r["exact"]) for r in ok]) if ok else None,
           "solves of the search a pair": _stats([r["solves"] for r in flat]),
           "seconds a pair: the solve at the end rotation, the search": [_stats([r["curve_seconds"] for r in flat]),
                                                                        _stats([r["exact_seconds"] for r in flat])],
           "wall seconds": round(time.perf_counter() - t0, 1), "workers": a.workers, "rows": res}
    return out


def main(argv=None) -> None:
    _paths()
    ap = argparse.ArgumentParser(prog="first_order")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("estimate")
    for x in ("evaluation", "labels", "key", "out"):
        p.add_argument(x)
    p = sub.add_parser("data")
    for x in ("preset", "data", "members"):
        p.add_argument(x)
    p.add_argument("--workers", type=int, default=1); p.add_argument("--manifest"); p.add_argument("--ledger")
    p = sub.add_parser("exact")
    for x in ("evaluation", "key", "preset", "data", "members", "out"):
        p.add_argument(x)
    p.add_argument("--workers", type=int, default=1)
    a = ap.parse_args(argv)
    out = {"estimate": estimate, "data": data_cmd, "exact": exact}[a.cmd](a)
    if a.cmd != "data":
        with open(a.out, "w", encoding="ascii", newline="\n") as fh:
            fh.write(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))


if __name__ == "__main__":
    main()
