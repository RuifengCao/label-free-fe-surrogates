"""Audit of gate G-C2.1 from its return package (after the run; not under the stamp).

    python -I audit/c2_recompute.py RECORDS INSTANCES OUT_DIR --regenerate
    python -I audit/c2_recompute.py RECORDS INSTANCES OUT_DIR [--runs a,b] [--ids x,y] [--workers N]
    python -I audit/c2_recompute.py RECORDS INSTANCES OUT_DIR --resolve x,y
    python -I audit/c2_recompute.py RECORDS INSTANCES OUT_DIR --aggregate [--runs a,b]

Run it from the joint/ folder, with c2/ and fejoint/ as stamped (docs/G-C2.1_code.sha256). RECORDS is the return
package's records/ folder (records/c2/return), INSTANCES a folder for the regenerated instances, OUT_DIR the folder
of the outputs (records/c2/audit). The four steps, in this order:
  1. --regenerate: regenerates all 580 instances into INSTANCES with the stamped code, checks that the members are
     the configured draws and that no training member is a held-out one, and compares the files with the returned
     manifest (regenerate.json). The bytes of a file depend on the zlib that numpy's savez_compressed writes
     through: the host's Python had zlib 1.3, and a Python linked to zlib-ng writes the same arrays as other bytes.
     Run this step with zlib 1.3 (on Linux, LD_PRELOAD of the system's libz.so.1.3 provides it); regenerate.json
     records the version used.
  2. (no step flag) for every held-out and tested member, one JSON file in OUT_DIR/members (resumes; the
     environment in environment.json):
     - the returned label on the regenerated instance: its field, evaluated there, against the label's energy, force
       and end displacement, and its optimality residuals;
     - the metrics of the listed runs (default: the three label-free runs) recomputed from the returned predictions
       with the stamped metric function (c2.evaluate.metrics: an exact solve at each predicted end displacement,
       warm-started from the label nearest in e).
  3. --resolve: re-solves the listed members at their levels from the regenerated instances, as the labels were
     solved, and compares with the returned labels and the ledger (resolve.json).
  4. --aggregate: compares every recomputed metric with the returned verdict.json and recomputes C1, C2 and the
     verdict from the recomputed curve errors, with the stamped quantile rule (aggregate.json).
Steps 2 to 4 use one BLAS thread a process, as the host's labels and evaluation did (RUNBOOK_C2.md, sections 4 and
6). The host had no pypardiso: set FEJOINT_SOLVER=legacy where it loads, so that the solves use scipy's SuperLU.
"""
import os
import sys

if "--regenerate" not in sys.argv:                 # steps 2 to 4: one BLAS thread a process
    for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[_k] = "1"

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import pathlib  # noqa: E402
import platform  # noqa: E402
import time  # noqa: E402
import zlib  # noqa: E402

ROOT = pathlib.Path.cwd()
sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402
import scipy  # noqa: E402

from c2.config import config, sha256  # noqa: E402
from c2 import data as C2D  # noqa: E402
from c2.data import load_export, solve_levels  # noqa: E402
from c2.evaluate import metrics, _quantile  # noqa: E402
from c2.instance import ExportedProblem  # noqa: E402
from fejoint import linsolve  # noqa: E402

STAMPED_CONFIG = "795515630ff6f37a819c7503931c7d7cf6e70a9f272e25ac96730394dd361fb4"
LABEL_FREE = ["label_free_s0", "label_free_s1", "label_free_s2"]
KEYS = ("curve_err", "F_err", "e_err", "F_sigma_err", "gap", "bound", "iou_contact", "iou_plastic", "bolt_err",
        "u_rel_l2")


def environment() -> dict:
    return {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "zlib": zlib.ZLIB_RUNTIME_VERSION, "solver": "pardiso" if linsolve._PARDISO is not None else "scipy",
            "blas_threads_env": os.environ.get("OPENBLAS_NUM_THREADS"), "cpus": os.cpu_count()}


def label_of(rec: pathlib.Path, iid: str) -> dict:
    with np.load(rec / "labels" / f"{iid}.npz") as z:
        return {k: z[k] for k in z.files}


def member(job):
    rec, inst, outdir, iid, runs = job
    rec, inst, outdir = pathlib.Path(rec), pathlib.Path(inst), pathlib.Path(outdir)
    out_p = outdir / "members" / f"{iid}.json"
    if out_p.exists():
        return iid, "kept"
    t0 = time.perf_counter()
    ex, _ = load_export(inst / f"{iid}.npz")
    ref = label_of(rec, iid)
    P = ExportedProblem(ex)
    # the label on the regenerated instance
    lab, ref_pl = [], []
    for l in range(ref["D"].size):
        D = float(ref["D"][l])
        e = P.evaluate(ref["z"][l], D)
        ref_pl.append(e["plastic"])
        _, g, _, _ = P.prob.evaluate(np.asarray(ref["z"][l], float), "hencky", tangent=False)
        kkt = P.prob.kkt(np.asarray(ref["z"][l], float), g)
        lab.append({"D": D, "Pi_rel": e["Pi"] / float(ref["Pi"][l]) - 1, "F_rel": e["F"] / float(ref["F"][l]) - 1,
                    "e_diff": e["e"] - float(ref["e"][l]), "res_unconstrained": float(kkt["max_residual_unconstrained"]),
                    "min_gap": float(kkt["min_gap"]), "min_lambda": float(kkt["min_lambda"])})
    # the runs
    res = {}
    for run in runs:
        with np.load(rec / "runs" / run / "preds.npz") as z:
            Z = z[iid]
        res[run] = [metrics(P, ex, Z[l], ref, ref_pl[l], l) for l in range(ref["D"].size)]
    outdir.joinpath("members").mkdir(parents=True, exist_ok=True)
    tmp = out_p.with_suffix(".tmp")
    tmp.write_text(json.dumps({"id": iid, "label_check": lab, "runs": res, "seconds": time.perf_counter() - t0}))
    tmp.replace(out_p)
    return iid, round(time.perf_counter() - t0, 1)


def resolve(rec: pathlib.Path, inst: pathlib.Path, iid: str, cfg: dict) -> dict:
    ex, _ = load_export(inst / f"{iid}.npz")
    ref = label_of(rec, iid)
    led = {e["id"]: e for e in json.loads((rec / "ledger.json").read_text())}[iid]
    ls = cfg["data"]["label_solver"]
    t0 = time.perf_counter()
    s = solve_levels(ex, [float(v) for v in ref["D"]], ls["tol"], ls["max_it"])
    return {"id": iid, "seconds": round(time.perf_counter() - t0, 1),
            "bit_identical": bool(np.array_equal(s["z"], ref["z"])),
            "max_z_diff_over_max_z": float(np.abs(s["z"] - ref["z"]).max() / np.abs(ref["z"]).max()),
            "max_Pi_rel": float(np.max(np.abs(s["Pi"] / ref["Pi"] - 1))),
            "max_F_rel": float(np.max(np.abs(s["F"] / ref["F"] - 1))),
            "max_e_diff_mm": float(np.abs(s["e"] - ref["e"]).max()),
            "iterations": [int(i) for i in s["iterations"]], "ledger_iterations": led["iterations"],
            "converged": [bool(c) for c in s["converged"]]}


def regenerate(rec: pathlib.Path, inst: pathlib.Path, cfg: dict) -> dict:
    """Every instance, written as c2.data.generate writes it, against the returned manifest."""
    man = json.loads((rec / "manifest.json").read_text())
    box = {r["id"]: r for r in man["instances"]}
    mem = C2D.members(cfg)
    same = len(mem) == man["n"] and all(i in box and box[i]["params"] == C2D.asdict(prm) and box[i]["split"] == s
                                        for i, s, prm in mem)
    tr = {json.dumps(C2D.asdict(prm), sort_keys=True) for i, s, prm in mem if s == "train"}
    ev = {json.dumps(C2D.asdict(prm), sort_keys=True) for i, s, prm in mem if s == "eval"}
    cfg_sha = sha256(cfg)
    inst.mkdir(parents=True, exist_ok=True)
    by_split, differ = {}, []
    for iid, split, prm in mem:
        p = inst / f"{iid}.npz"
        with open(p, "wb") as fh:
            np.savez_compressed(fh, **C2D._pack(C2D.export_member(cfg, prm), prm, cfg_sha))
        with np.load(p) as z:
            nodes, nz = int(z["nodes"].shape[0]), int(z["v"].size)
        sha_ok = hashlib.sha256(p.read_bytes()).hexdigest() == box[iid]["sha256"]
        size_ok = nodes == box[iid]["nodes"] and nz == box[iid]["unknowns"]
        c = by_split.setdefault(split, {"files": 0, "sha256_equal": 0, "sizes_equal": 0})
        c["files"] += 1; c["sha256_equal"] += sha_ok; c["sizes_equal"] += size_ok
        if not (sha_ok and size_ok):
            differ.append(iid)
    return {"manifest_config_is_stamped": man["config_sha256"] == cfg_sha,
            "members_are_the_configured_draws": same, "train_eval_shared": len(tr & ev), "by_split": by_split,
            "files": sum(c["files"] for c in by_split.values()),
            "sha256_equal": sum(c["sha256_equal"] for c in by_split.values()), "differ": differ}


def aggregate(rec: pathlib.Path, outdir: pathlib.Path, runs) -> dict:
    v = json.loads((rec / "verdict.json").read_text())
    man = json.loads((rec / "manifest.json").read_text())
    want = sorted(r["id"] for r in man["instances"] if r["split"] in ("eval", "tested"))
    mem = {p.stem: json.loads(p.read_text()) for p in sorted((outdir / "members").glob("*.json"))}
    out = {"members": len(mem), "members_missing": [i for i in want if i not in mem], "label_check": {}, "runs": {},
           "max_abs_diff": {}}
    lc = [x for m in mem.values() for x in m["label_check"]]
    out["label_check"] = {k: float(max(abs(x[k]) for x in lc)) for k in ("Pi_rel", "F_rel", "e_diff", "res_unconstrained")}
    out["label_check"]["min_gap"] = float(min(x["min_gap"] for x in lc))
    out["label_check"]["min_lambda"] = float(min(x["min_lambda"] for x in lc))
    out["label_check"]["levels"] = len(lc)
    for run in runs:
        arm, seed = run.rsplit("_s", 1)
        box = v["arms"][arm][seed]
        diffs = {k: 0.0 for k in KEYS}
        bound_mismatch = 0
        ev = []
        for iid, m in mem.items():
            rows = m["runs"][run]
            brows = box["eval_rows"].get(iid) or box["tested"].get(iid)
            assert len(rows) == len(brows)
            for r, b in zip(rows, brows):
                for k in KEYS:
                    x, y = r[k], b[k]
                    if np.isfinite(x) and np.isfinite(y):
                        diffs[k] = max(diffs[k], abs(x - y))
                    elif np.isnan(x) and np.isnan(y):
                        pass
                    elif not (np.isinf(x) and np.isinf(y) and np.sign(x) == np.sign(y)):
                        diffs[k] = float("inf")
                bound_mismatch += r["within_bound"] != b["within_bound"]
            if iid.startswith("eval_"):
                ev += [abs(r["curve_err"]) for r in rows]
        out["max_abs_diff"][run] = diffs
        out.setdefault("within_bound_mismatches", {})[run] = int(bound_mismatch)
        if len(ev) == 448:
            out["runs"][run] = {"median": _quantile(ev, 0.5), "p90": _quantile(ev, 0.9), "n": len(ev),
                                "infinite": int(np.isinf(ev).sum()),
                                "box_median": box["eval"]["abs_curve_err"]["median"],
                                "box_p90": box["eval"]["abs_curve_err"]["p90"],
                                "box_infinite": box["eval"]["curve_infinite"]}
    if all(r in out["runs"] for r in LABEL_FREE):
        med = [out["runs"][r]["median"] for r in LABEL_FREE]
        p90 = [out["runs"][r]["p90"] for r in LABEL_FREE]
        out["C1_value"], out["C2_value"] = _quantile(med, 0.5), _quantile(p90, 0.5)
        out["C1"], out["C2"] = bool(out["C1_value"] <= 0.05), bool(out["C2_value"] <= 0.10)
        out["verdict"] = "PASS" if out["C1"] and out["C2"] else "FAIL"
        out["box"] = {"C1_value": v["C1_value"], "C2_value": v["C2_value"], "verdict": v["verdict"]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records"); ap.add_argument("instances"); ap.add_argument("out")
    ap.add_argument("--runs", default=",".join(LABEL_FREE))
    ap.add_argument("--ids", default="")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--regenerate", action="store_true")
    ap.add_argument("--resolve", default="")
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    cfg = config()
    assert sha256(cfg) == STAMPED_CONFIG
    rec, inst, outdir = pathlib.Path(a.records), pathlib.Path(a.instances), pathlib.Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    runs = [r for r in a.runs.split(",") if r]
    env = environment()
    if a.regenerate:
        reg = {"environment": env, **regenerate(rec, inst, cfg)}
        (outdir / "regenerate.json").write_text(json.dumps(reg, indent=1))
        print(json.dumps(reg))
        return
    if a.resolve:
        rs = {"environment": env, "members": [resolve(rec, inst, i, cfg) for i in a.resolve.split(",") if i]}
        (outdir / "resolve.json").write_text(json.dumps(rs, indent=1))
        print(json.dumps(rs, indent=1))
        return
    if a.aggregate:
        agg = {"environment": env, **aggregate(rec, outdir, runs)}
        (outdir / "aggregate.json").write_text(json.dumps(agg, indent=1))
        print(json.dumps(agg, indent=1))
        return
    (outdir / "environment.json").write_text(json.dumps(env))
    man = json.loads((rec / "manifest.json").read_text())
    ids = [r["id"] for r in man["instances"] if r["split"] in ("eval", "tested")]
    if a.ids:
        ids = [i for i in a.ids.split(",") if i]
    jobs = [(str(rec), str(inst), str(outdir), iid, runs) for iid in ids]
    if a.workers <= 1:
        for j in jobs:
            print(*member(j), flush=True)
    else:
        import multiprocessing as mp
        with mp.get_context("fork").Pool(a.workers) as pool:
            for r in pool.imap_unordered(member, jobs):
                print(*r, flush=True)


if __name__ == "__main__":
    main()
