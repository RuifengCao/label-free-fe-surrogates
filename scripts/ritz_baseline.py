#!/usr/bin/env python3
"""cmame-paper Stage 14 (RUNBOOK_CMAME Sec. G): the per-instance polynomial
Ritz-Galerkin baseline on the manuscript's own instances, post hoc. The
specification (Appendix 1, fixed on 20 October 2026; BRANCH_NOTES Stage 14
and fejepa.analysis.ritz) is applied unchanged; the whole ladder is reported
(3D p = 6, 7, 8, 9; 2D p = 6, 8).

Sets (configs/ritz_v1.json, `baseline.sets`), each read from the box's own
files, in the order of the records:
  val3d   the 256 validation instances of runs/data3d_phase2 (Phase-2b's split);
  fine3d  the first 256 of runs/data3d_phase2_fine (Phase-2b's fine set);
  h3d     PREREG_HOLDOUT's 686 holdout instances of runs/data3d_phase2, with the
          labels its run computed (runs/holdout/h3d);
  val2d   the 256 validation instances of runs/data2d (CM2D's split);
  h2d     PREREG_HOLDOUT's 4,111 holdout instances of runs/data2d (runs/holdout/h2d).
The labels are the box's (the corpus files' own for val3d, fine3d and val2d,
the holdout run's label files for h3d and h2d); nothing is solved again.

Inputs are checked before any computation (exit 3 on a refusal): each report
and record by the SHA-256 the configuration names, each corpus by its
manifest's SHA-256 as the report records it, the holdout sets as
PREREG_HOLDOUT's run checks them (the corpus manifest, the labels manifest,
which must be the one its return carries, and per instance the corpus file's
and the label file's SHA-256), and the set's file list against the records'.

Per instance: the identity check of Appendix 1 (the size and ||U*||_K per load
case against the records: amp_phase2b.json for the 3D sets, CM2D's spectral
export for val2d, Pi_h(U*) of PREREG_HOLDOUT's arrays for h3d and h2d;
relative difference at most 1e-6); the Ritz ladder (one P^T K P at the
largest p, each p its principal sub-block); per p the five metrics per load
case (the repository's functions) and their means over the load battery, the
load cases worse than the zero field, the dropped directions; the times of
the Ritz parts, measured in a worker beside others (information only: the
cost table's times are scripts/ritz_timing.py's, on an idle machine).
Instances are computed by --workers processes (spawned; each limited to
--worker-threads BLAS threads) and written in order, one line each, to
OUT/baseline/<set>/rows.jsonl; a run again resumes after the last complete
line. Once the set is complete, OUT/baseline/<set>/summary.json: per p the
medians and means, the counts, and the pairing with every recorded model's
per-instance values on the set (the share of instances on which the Ritz
solution is better, per model, seed and metric), the instances that fail the
identity check listed apart and left out of the pairing.

--check verifies every input of the set(s) and prints one line per set; it
computes and writes nothing. --resummarise DIR rebuilds DIR/summary.json from
DIR/rows.jsonl with the records alone (the repository side, on a return).

Exit status: 0 done; 3 an input refused (the message names it; nothing
computed); 4 an instance that is not the recorded one (everything written,
the summary lists it); anything else an error.

    python scripts/ritz_baseline.py --config configs/ritz_v1.json --set val3d
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import deque
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fejepa.analysis import ritz as R  # noqa: E402

SETS = ("val3d", "fine3d", "h3d", "val2d", "h2d")
DETERMINISTIC = ("zero", "knn_field", "scale_aware_poly")
"""Rows that do not depend on a seed; where several reports carry one, their
per-instance values must agree (a check of the instance order)."""
EVERY = 16
"""A progress line every this many instances (and the last)."""


class Refused(Exception):
    """An input that is not the one the configuration names (exit 3)."""


# ------------------------------------------------------------------ inputs --

def _json(path, sha, what) -> dict:
    try:
        return json.loads(R.checked(path, sha, what).read_text())
    except ValueError as exc:
        raise Refused(str(exc)) from None


def _npz(path, sha, what) -> dict:
    try:
        with np.load(R.checked(path, sha, what), allow_pickle=False) as z:
            return {k: z[k] for k in z.files}
    except ValueError as exc:
        raise Refused(str(exc)) from None


def identity_record(sdef: dict, sname: str) -> list:
    """Per instance, in the set's order: {"file", "size_kind", "size",
    "ustar_norm_K"} from the record the configuration names."""
    idc = sdef["identity"]
    if idc["kind"] == "amp":
        a = _json(idc["path"], idc["sha256"], f"{sname} identity record")
        per = a["seeds"]["s0"][idc["part"]]["per_instance"]
        return [{"file": r["file"], "size_kind": "n_nodes", "size": int(r["n_nodes"]),
                 "ustar_norm_K": [float(x) for x in r["ustar_norm_K"]]} for r in per]
    if idc["kind"] == "spectra":
        z = _npz(idc["path"], idc["sha256"], f"{sname} identity record")
        return [{"file": str(f), "size_kind": "n_free", "size": int(n),
                 "ustar_norm_K": np.sqrt(np.asarray(u, float)).tolist()}
                for f, n, u in zip(z["files"], z["n_free"], z["uK_star"])]
    if idc["kind"] == "pi_star":
        z = _npz(idc["path"], idc["sha256"], f"{sname} identity record")
        man = _json(idc["manifest"], sdef["labels_manifest_sha256"], f"{sname} returned labels "
                    "manifest")
        nodes = {r["file"]: int(r["n_nodes"]) for r in man["instances"]}
        if [str(f) for f in z["files"]] != [r["file"] for r in man["instances"]]:
            raise Refused(f"{sname}: the arrays' files are not the labels manifest's")
        return [{"file": str(f), "size_kind": "n_nodes", "size": nodes[str(f)],
                 "ustar_norm_K": np.sqrt(np.maximum(-2.0 * np.asarray(p, float), 0.0)).tolist()}
                for f, p in zip(z["files"], z["pi_star"])]
    raise ValueError(f"identity kind {idc['kind']!r}")


def set_names(cfg: dict, sname: str) -> list:
    """The set's file names in the records' order (no box file needed)."""
    sdef = cfg["baseline"]["sets"][sname]
    names = [r["file"] for r in identity_record(sdef, sname)]
    if len(names) != int(sdef["n"]):
        raise Refused(f"{sname}: the identity record lists {len(names)} instances, the "
                      f"configuration {sdef['n']}")
    return names


def box_jobs(cfg: dict, sname: str) -> list:
    """The set's instances on the box, as worker jobs, checked against the
    configuration and the records (Refused otherwise)."""
    sdef = cfg["baseline"]["sets"][sname]
    idrec = identity_record(sdef, sname)
    names = [r["file"] for r in idrec]
    if sdef["kind"] == "run":
        from fejepa.analysis.posthoc import run_files

        report = _json(sdef["report"], sdef["report_sha256"], f"{sname} report")
        try:
            files = [Path(f) for f in run_files(report, sdef["which"])]
        except (SystemExit, OSError, ValueError, KeyError) as exc:   # verified_dir's refusal
            raise Refused(f"{sname}: {exc}") from None
        if [f.name for f in files] != names:
            raise Refused(f"{sname}: the box's {sdef['which']} files are not the records' "
                          f"({len(files)} files)")
        jobs = [{"i": i, "file": f.name, "path": str(f)} for i, f in enumerate(files)]
    elif sdef["kind"] == "holdout":
        from fejepa.analysis.holdout import check_labelled_set, holdout_files, load_spec

        try:
            spec = load_spec(R.checked(sdef["spec"], sdef["spec_sha256"], f"{sname} spec"))
            hdef = spec["sets"][sdef["set"]]
            holdout_files(hdef)                            # the corpus manifest and the tail
            R.checked(Path(sdef["labels_dir"]) / "manifest.json",
                      sdef["labels_manifest_sha256"], f"{sname} labels manifest")
            man = check_labelled_set(sdef["set"], hdef, sdef["labels_dir"])
        except (OSError, ValueError, KeyError) as exc:
            raise Refused(f"{sname}: {exc}") from None
        if [r["file"] for r in man["instances"]] != names:
            raise Refused(f"{sname}: the labels manifest's files are not the records'")
        corpus = Path(hdef["corpus"])
        jobs = [{"i": i, "file": r["file"], "path": str(corpus / r["file"]),
                 "source_sha256": r["source_sha256"],
                 "labels": str(Path(sdef["labels_dir"]) / "labels" / r["file"]),
                 "labels_sha256": r["labels_sha256"]}
                for i, r in enumerate(man["instances"])]
    else:
        raise ValueError(f"set kind {sdef['kind']!r}")
    for j, r in zip(jobs, idrec):
        j.update(dim=int(sdef["dim"]), identity=r)
    missing = [j["path"] for j in jobs if not Path(j["path"]).is_file()]
    missing += [j["labels"] for j in jobs if "labels" in j and not Path(j["labels"]).is_file()]
    if missing:
        raise Refused(f"{sname}: {len(missing)} files missing (first {missing[0]})")
    bad = [j["path"] for j in jobs if "source_sha256" in j
           and R.sha256(j["path"]) != j["source_sha256"]]
    bad += [j["labels"] for j in jobs if "labels" in j
            and R.sha256(j["labels"]) != j["labels_sha256"]]
    if bad:
        raise Refused(f"{sname}: {len(bad)} files differ from the labels manifest's SHA-256 "
                      f"(first {bad[0]})")
    return jobs


# ------------------------------------------------------------------ worker --

def load_job(job: dict):
    """The job's instance with its labels, each file checked against the
    SHA-256 the job names (ValueError otherwise)."""
    from fejepa.data.archive import load_instance

    if "source_sha256" in job and R.sha256(job["path"]) != job["source_sha256"]:
        raise ValueError(f"{job['path']}: its bytes differ from those its label was solved from")
    arch = load_instance(job["path"])
    if "labels" in job:
        from fejepa.analysis.holdout import _read_labels

        if R.sha256(job["labels"]) != job["labels_sha256"]:
            raise ValueError(f"{job['labels']}: its bytes differ from the labels manifest's")
        U, src, src_sha = _read_labels(Path(job["labels"]))
        if src != job["file"] or src_sha != job["source_sha256"]:
            raise ValueError(f"{job['labels']}: names another corpus file")
        arch.U_star = U
    if arch.U_star is None:
        raise ValueError(f"{job['path']}: no labels")
    return arch


def compute_row(job: dict) -> dict:
    """One instance: identity, the Ritz ladder, the metrics (in a worker)."""
    t0 = time.perf_counter()
    arch = load_job(job)
    t_load = time.perf_counter() - t0
    if arch.nodes.shape[1] != job["dim"]:
        raise ValueError(f"{job['file']}: dimension {arch.nodes.shape[1]}, expected {job['dim']}")
    Kff, Ff = R.free_block(arch)
    free = np.asarray(arch.free_mask, bool)
    nk = R.ustar_norm_K(Kff, np.atleast_2d(arch.U_star)[:, free])
    idr = job["identity"]
    if idr["file"] != job["file"]:
        raise ValueError(f"record order: {idr['file']} at {job['i']}, expected {job['file']}")
    size = int(arch.n_nodes) if idr["size_kind"] == "n_nodes" else int(Kff.shape[0])
    ident = R.identity(size == idr["size"], nk, idr["ustar_norm_K"])
    ident.update(size_kind=idr["size_kind"], size_recorded=idr["size"], size=size)
    row = {"i": job["i"], "file": job["file"], "n_nodes": int(arch.n_nodes),
           "ndof_free": int(Kff.shape[0]), "ustar_norm_K": [float(x) for x in nk],
           "identity": ident}
    ladder = R.LADDER[job["dim"]]
    sols, t = R.ritz_ladder(arch, ladder, Kff, Ff)
    t["load"] = t_load
    row["ritz"] = {}
    for p, (U, dropped, k) in sols.items():
        t1 = time.perf_counter()
        m = R.metrics(U, arch)
        m.update(k=k, dropped=dropped)
        row["ritz"][str(p)] = m
        t[f"metrics_{p}"] = time.perf_counter() - t1
    row["t"] = t
    return row


def _worker_init(threads: int) -> None:
    """Limit a spawned worker's BLAS threads (set before numpy loads them)."""
    try:
        from threadpoolctl import threadpool_limits

        threadpool_limits(int(threads))
    except ImportError:
        pass


def ordered_rows(jobs: list, fn, workers: int, threads: int):
    """fn(job) for every job, yielded in order: in this process (workers <= 1)
    or by spawned workers with at most 2 x workers jobs in flight; the first
    error cancels what is not running and is raised."""
    if workers <= 1:
        for j in jobs:
            yield fn(j)
        return
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor

    for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[k] = str(int(threads))                 # inherited by the workers
    ex = ProcessPoolExecutor(max_workers=int(workers), mp_context=mp.get_context("spawn"),
                             initializer=_worker_init, initargs=(int(threads),))
    pending, it = deque(), iter(jobs)
    try:
        for j in it:
            pending.append(ex.submit(fn, j))
            if len(pending) >= 2 * workers:
                break
        while pending:
            row = pending.popleft().result()
            nxt = next(it, None)
            if nxt is not None:
                pending.append(ex.submit(fn, nxt))
            yield row
    except BaseException:
        ex.shutdown(wait=False, cancel_futures=True)
        raise
    ex.shutdown(wait=True)


# ----------------------------------------------------------------- records --

def _datasets(rep: dict) -> list:
    ds = rep["provenance"]["datasets"]
    return ds if isinstance(ds, list) else json.loads(ds)


def _seed_labels(rep: dict, n: int) -> list:
    seeds = [int(s) for s in (rep.get("provenance") or {}).get("seeds") or rep.get("seeds") or []]
    if n == len(seeds):
        return [f"s{s}" for s in seeds]
    return ["det"] if n == 1 else [f"k{k}" for k in range(n)]


def _per_instance(pse: list, n: int, label: str) -> list:
    rows = [e["per_instance"] for e in pse]
    for r in rows:
        if any(len(r[f]) != n for f in R.FIELDS):
            raise Refused(f"{label}: per-instance arrays are not of length {n}")
    return rows


def identity_order(sdef: dict, sname: str, primary: dict) -> dict | None:
    """The identity record's own per-instance values of each seed (amp's
    `disp` and `egap`, which scripts/posthoc_amplitude.py recorded from the
    run's states) against the set's report arrays that `order` names: equal
    when the two lists of instances are in one order (Refused otherwise; None
    when the identity record holds no such values)."""
    idc = sdef["identity"]
    if not idc.get("order"):
        return None
    amp = _json(idc["path"], idc["sha256"], f"{sname} identity record")
    parts = idc["order"].split(":")
    if parts[0] == "cells":
        pse = primary["results"]["e8"]["metrics"]["cells"][parts[1]][parts[2]]["per_seed_eval"]
    elif parts == ["p3", "ar"]:
        pse = primary["results"]["p3_transfer"]["metrics"]["ar"]["fine"]["per_seed_eval"]
    else:
        raise ValueError(f"identity order {idc['order']!r}")
    seeds = [int(x) for x in primary["provenance"]["seeds"]]
    if len(pse) != len(seeds):
        raise Refused(f"{sname}: {len(pse)} seeds in {idc['order']}, the report runs {seeds}")
    worst = 0.0
    for k, sd in enumerate(seeds):
        per = amp["seeds"][f"s{sd}"][idc["part"]]["per_instance"]
        for mine, theirs in (("disp", "disp_rel_l2"), ("egap", "energy_gap_rel")):
            a1 = np.asarray([r[mine] for r in per], float)
            a2 = np.asarray(pse[k]["per_instance"][theirs], float)
            if a1.shape != a2.shape:
                raise Refused(f"{sname}: the identity record and {idc['order']} differ in length")
            worst = max(worst, float(np.max(np.abs(a1 - a2) / np.maximum(np.abs(a2), 1e-300))))
    if not worst <= 1e-9:
        raise Refused(f"{sname}: the identity record's values differ from the report's "
                      f"{idc['order']} ({worst:.1e}): instance order?")
    return {"against": idc["order"], "seeds": seeds, "max_rel_diff": worst}


def paired_records(cfg: dict, sname: str) -> tuple:
    """({label: [(seed label, {field: per-instance list})]}, checks) for every
    recorded model of every source the configuration pairs with the set;
    deterministic rows that several reports carry must agree."""
    sdef = cfg["baseline"]["sets"][sname]
    n = int(sdef["n"])
    names = set_names(cfg, sname)
    out, det, checks = {}, {}, {}
    primary = None
    if sdef["kind"] == "run":
        primary = _json(sdef["report"], sdef["report_sha256"], f"{sname} report")
        corpus = {d.get("dir"): d.get("manifest_sha256") for d in _datasets(primary)}
        order = identity_order(sdef, sname, primary)
        if order is not None:
            checks["identity_order"] = order
    for src in sdef["paired"]:
        tag, kind = src["tag"], src["kind"]
        if kind in ("cells", "p3"):
            rep = _json(src["path"], src["sha256"], f"{sname} paired {tag}")
            got = {d.get("dir"): d.get("manifest_sha256") for d in _datasets(rep)}
            for d in ("runs/data3d_phase2_fine",) if kind == "p3" else \
                    (primary["config"]["data"]["dir"],):
                if got.get(d) != corpus.get(d):
                    raise Refused(f"{sname} paired {tag}: not on {d} with the set's manifest")
            if "split" in rep["config"]:
                if rep["config"]["split"] != primary["config"]["split"]:
                    raise Refused(f"{sname} paired {tag}: split {rep['config']['split']}")
            elif rep["config"].get("source", {}).get("report_sha256") != sdef["report_sha256"]:
                raise Refused(f"{sname} paired {tag}: neither a split nor the set's report")
            if kind == "p3":
                dt, pt = rep["config"]["data_transfer"], primary["config"]["data_transfer"]
                if {k: dt[k] for k in ("n", "seed", "lc", "split")} != \
                        {k: pt[k] for k in ("n", "seed", "lc", "split")}:
                    raise Refused(f"{sname} paired {tag}: fine set {dt}")
        if kind == "cells":
            c = rep["results"]["e8"]["metrics"]["cells"] if "results" in rep else rep["cells"]
            rows = src.get("rows") or list(c)
            for r in rows:
                for b in sorted(c[r], key=int):
                    lab = f"{tag}:{r}@{b}"
                    pse = c[r][b]["per_seed_eval"]
                    out[lab] = list(zip(_seed_labels(rep, len(pse)), _per_instance(pse, n, lab)))
                    if r in DETERMINISTIC:
                        det.setdefault(f"{r}@{b}", []).append((tag, pse[0]["per_instance"]))
            if src.get("order_row"):                       # its instance order is the set's
                o = src["order_row"]
                pc = primary["results"]["e8"]["metrics"]["cells"]
                worst = 0.0
                for b in c[o]:
                    for e, f in zip(c[o][b]["per_seed_eval"], pc[o][b]["per_seed_eval"]):
                        for k in R.FIELDS:
                            a1 = np.asarray(e["per_instance"][k], float)
                            a2 = np.asarray(f["per_instance"][k], float)
                            worst = max(worst, float(np.max(np.abs(a1 - a2)
                                                            / np.maximum(np.abs(a2), 1e-300))))
                if not worst <= 1e-9:
                    raise Refused(f"{sname} paired {tag}: its {o} row differs from the set's "
                                  f"report ({worst:.1e}): instance order?")
                checks[f"{tag}:order_row:{o}"] = {"max_rel_diff": worst}
        elif kind == "p3":
            m = rep["results"]["p3_transfer"]["metrics"]
            lab = f"{tag}:ar (zero-shot)"
            pse = m["ar"]["fine"]["per_seed_eval"]
            out[lab] = list(zip(_seed_labels(rep, len(pse)), _per_instance(pse, n, lab)))
            for k, v in (m.get("zero_shot_reported") or {}).items():
                if v is not None:
                    lab = f"{tag}:{k} (zero-shot)"
                    pse = v["fine"]["per_seed_eval"]
                    out[lab] = list(zip(_seed_labels(rep, len(pse)), _per_instance(pse, n, lab)))
            for k, v in (m.get("naive_rows") or {}).items():
                lab = f"{tag}:{k}"
                pse = v["per_seed_eval"]
                out[lab] = list(zip(_seed_labels(rep, len(pse)), _per_instance(pse, n, lab)))
                det.setdefault(k, []).append((tag, pse[0]["per_instance"]))
            for b, rows in (m.get("fewshot") or {}).items():
                for k, v in rows.items():
                    lab = f"{tag}:{k}@{b}"
                    pse = v["per_seed_eval"]
                    out[lab] = list(zip(_seed_labels(rep, len(pse)), _per_instance(pse, n, lab)))
        elif kind == "arrays":
            z = _npz(src["path"], src["sha256"], f"{sname} paired {tag}")
            if [str(f) for f in z["files"]] != names:
                raise Refused(f"{sname} paired {tag}: its files are not the set's")
            if [str(m) for m in z["metrics"]] != list(R.FIELDS):
                raise Refused(f"{sname} paired {tag}: metrics {list(z['metrics'])}")
            for ri, r in enumerate(str(x) for x in z["rows"]):
                if src.get("rows") and r not in src["rows"]:
                    continue
                out[f"{tag}:{r}"] = [
                    (f"s{int(s)}", {f: z["values"][ri, si, :, k].tolist()
                                    for k, f in enumerate(R.FIELDS)})
                    for si, s in enumerate(z["seeds"])]
        else:
            raise ValueError(f"paired kind {kind!r}")
    for key, entries in det.items():
        if len(entries) < 2:
            continue
        ref, worst = entries[0][1], 0.0
        for _, pi in entries[1:]:
            for f in R.FIELDS:
                a, b = np.asarray(ref[f], float), np.asarray(pi[f], float)
                worst = max(worst, float(np.max(np.abs(a - b) / np.maximum(np.abs(a), 1e-300))))
        if worst > 1e-9:
            raise Refused(f"{sname}: the deterministic row {key} differs between reports "
                          f"({[t for t, _ in entries]}, {worst:.1e}): instance order?")
        checks[key] = {"reports": [t for t, _ in entries], "max_rel_diff": worst}
    return out, checks


# ---------------------------------------------------------------- summary --

def summarise(rows: list, dim: int, records: dict | None) -> dict:
    ok = [r for r in rows if r["identity"]["ok"]]
    idx = [r["i"] for r in ok]
    s = {"n": len(rows), "n_used": len(ok),
         "identity_failed": [r["file"] for r in rows if not r["identity"]["ok"]],
         "identity_max_rel_diff": max(r["identity"]["ustar_norm_K_max_rel_diff"] for r in rows),
         "size_mismatch": [r["file"] for r in rows if not r["identity"]["size_ok"]],
         "ladder": {}}
    for p in R.LADDER[dim]:
        P = str(p)
        vals = {f: np.array([r["ritz"][P]["mean"][f] for r in ok]) for f in R.FIELDS}
        wz = [r["ritz"][P]["worse_than_zero"] for r in ok]
        e = {"k": R.n_unknowns(dim, p),
             "dropped_max": max([r["ritz"][P]["dropped"] for r in ok] or [0]),
             "dropped_instances": int(sum(r["ritz"][P]["dropped"] > 0 for r in ok)),
             "worse_than_zero": {"load_cases": int(sum(w["load_cases"] for w in wz)),
                                 "worse": int(sum(w["worse"] for w in wz)),
                                 "sign_mismatch": int(sum(w["sign_mismatch"] for w in wz)),
                                 "instances_mean_gap_above_one":
                                     int(np.sum(vals["energy_gap_rel"] > 1.0))},
             "median": {f: float(np.median(v)) if v.size else None for f, v in vals.items()},
             "mean": {f: float(np.mean(v)) if v.size else None for f, v in vals.items()},
             "seconds_median_contended": {
                 k: float(np.median([r["t"][f"{k}_{p}"] for r in ok])) if ok else None
                 for k in ("solve", "recon", "metrics")},
             "paired": {}}
        for label, seeds in (records or {}).items():
            per = []
            for sl, sd in seeds:
                q = {"seed": sl}
                for f in R.FIELDS:
                    q[f] = R.paired_shares(vals[f], np.asarray(sd[f], float)[idx], f)
                per.append(q)
            e["paired"][label] = per
        s["ladder"][P] = e
    s["seconds_median_contended"] = {k: float(np.median([r["t"][k] for r in ok])) if ok else None
                                     for k in ("load", "basis", "kp")}
    s["timing_note"] = ("measured in a worker process beside others (contended): for "
                        "information only; the cost table's times are scripts/ritz_timing.py's. "
                        "kp is formed once at the largest p of the ladder (each smaller p takes "
                        "its principal sub-block)")
    return s


def write_summary(cfg: dict, sname: str, out: Path, rows: list, extra: dict) -> dict:
    sdef = cfg["baseline"]["sets"][sname]
    records, checks = paired_records(cfg, sname)
    summ = summarise(rows, int(sdef["dim"]), records)
    summ.update({"set": sname, "spec": "Appendix 1, fixed 20 October 2026 (post hoc)",
                 "cut": R.CUT, "ladder_p": list(R.LADDER[int(sdef["dim"])]),
                 "paired_sources": [dict(s) for s in sdef["paired"]],
                 "not_paired": sdef.get("not_paired"), "record_checks": checks,
                 "rows_sha256": R.sha256(out / "rows.jsonl")}, **extra)
    R.write_json(out / "summary.json", summ)
    return summ


# -------------------------------------------------------------------- main --

def check_set(cfg: dict, sname: str) -> dict:
    jobs = box_jobs(cfg, sname)
    paired_records(cfg, sname)
    return {"set": sname, "n": len(jobs), "files": "present", "inputs": "verified"}


def run_set(cfg: dict, cfg_path: Path, sname: str, workers: int, threads: int,
            limit: int) -> int:
    t_all = time.time()
    jobs = box_jobs(cfg, sname)
    paired_records(cfg, sname)                             # refused before any work
    names = [j["file"] for j in jobs]
    out = Path(cfg["out"]) / "baseline" / sname
    out.mkdir(parents=True, exist_ok=True)
    rows_path = out / "rows.jsonl"
    done = R.complete_lines(rows_path)
    if [r["file"] for r in done] != names[:len(done)] or \
            [r["i"] for r in done] != list(range(len(done))):
        raise Refused(f"{rows_path}: not a prefix of the set; move it aside")
    start = len(done)
    stop = len(jobs) if not limit else min(len(jobs), start + limit)
    if start == len(jobs):
        print(f"[ritz {sname}] all {len(jobs)} instances on disk", flush=True)
    elif start:
        print(f"[ritz {sname}] resuming after {start} instances on disk", flush=True)
    bad = []
    with open(rows_path, "a") as fh:
        for row in ordered_rows(jobs[start:stop], compute_row, workers, threads):
            R.append_row(fh, row)
            i = row["i"]
            if not row["identity"]["ok"]:
                bad.append(row["file"])
                print(f"[ritz {sname}] {i + 1}/{len(jobs)} {row['file']}: "
                      "NOT THE RECORDED INSTANCE "
                      f"(size {row['identity']['size']} recorded "
                      f"{row['identity']['size_recorded']}, ||U*||_K rel diff "
                      f"{row['identity']['ustar_norm_K_max_rel_diff']:.1e})", flush=True)
            if (i + 1) % EVERY == 0 or i + 1 == stop:
                g = " ".join(f"p{p}:{row['ritz'][p]['mean']['energy_gap_rel']:.4g}"
                             for p in row["ritz"])
                print(f"[ritz {sname}] {i + 1}/{len(jobs)} {row['file']} dofs "
                      f"{row['ndof_free']} gap {g} id "
                      f"{row['identity']['ustar_norm_K_max_rel_diff']:.1e} | "
                      f"{R.elapsed(t_all)}", flush=True)
    rows = R.complete_lines(rows_path)
    if len(rows) < len(jobs):
        print(f"[ritz {sname}] {len(rows)}/{len(jobs)} instances on disk; no summary yet",
              flush=True)
        return 0
    summ = write_summary(cfg, sname, out, rows, {
        "workers": int(workers), "worker_threads": int(threads), "machine": R.machine(),
        "code": R.code_provenance(ROOT), "config_sha256": R.sha256(cfg_path)})
    line = {"set": sname, "n": summ["n"], "n_used": summ["n_used"],
            "identity_failed": len(summ["identity_failed"]),
            "identity_max_rel_diff": summ["identity_max_rel_diff"],
            "median_gap": {p: e["median"]["energy_gap_rel"] for p, e in summ["ladder"].items()},
            "dropped_max": {p: e["dropped_max"] for p, e in summ["ladder"].items()},
            "worse_than_zero": {p: e["worse_than_zero"]["worse"]
                                for p, e in summ["ladder"].items()},
            "sign_mismatch": sum(e["worse_than_zero"]["sign_mismatch"]
                                 for e in summ["ladder"].values()),
            "seconds": round(time.time() - t_all, 1)}
    print(json.dumps(line), flush=True)
    return 4 if summ["identity_failed"] else 0


def main() -> None:
    ap = argparse.ArgumentParser(description="The polynomial Ritz-Galerkin baseline "
                                             "(Appendix 1, fixed 20 October 2026; post hoc)")
    ap.add_argument("--config", required=True, help="configs/ritz_v1.json")
    ap.add_argument("--set", required=True, help=f"one of {', '.join(SETS)}, or all "
                                                   "(with --check)")
    ap.add_argument("--workers", type=int, default=None, help="default: the configuration's")
    ap.add_argument("--worker-threads", type=int, default=None,
                    help="BLAS threads per worker (default: the configuration's)")
    ap.add_argument("--limit", type=int, default=0, help="stop after this many instances")
    ap.add_argument("--check", action="store_true", help="verify the inputs only")
    ap.add_argument("--resummarise", default=None,
                    help="rebuild DIR/summary.json from DIR/rows.jsonl (repository side)")
    a = ap.parse_args()
    try:
        cfg = R.load_config(a.config)
    except (OSError, ValueError, KeyError) as exc:
        print(f"REFUSED: {exc}", flush=True)
        sys.exit(3)
    sets = list(SETS) if a.set == "all" else [a.set]
    if any(s not in SETS for s in sets) or (a.set == "all" and not a.check):
        ap.error(f"--set: one of {', '.join(SETS)} (all: with --check only)")
    workers = int(a.workers if a.workers is not None else cfg["baseline"]["workers"])
    threads = int(a.worker_threads if a.worker_threads is not None
                  else cfg["baseline"]["worker_threads"])
    code = 0
    try:
        if a.resummarise:
            d = Path(a.resummarise)
            rows = R.complete_lines(d / "rows.jsonl")
            names = set_names(cfg, sets[0])
            if [r["file"] for r in rows] != names:
                raise Refused(f"{d}/rows.jsonl: not the complete set {sets[0]}")
            prev = json.loads((d / "summary.json").read_text()) if (d / "summary.json").is_file() \
                else {}
            keep = {k: prev[k] for k in ("workers", "worker_threads", "machine", "code",
                                         "config_sha256") if k in prev}
            summ = write_summary(cfg, sets[0], d, rows, keep)
            print(json.dumps({"set": sets[0], "n": summ["n"], "n_used": summ["n_used"],
                              "rebuilt": str(d / "summary.json")}), flush=True)
        elif a.check:
            for s in sets:
                print(json.dumps(check_set(cfg, s)), flush=True)
        else:
            code = run_set(cfg, Path(a.config), sets[0], workers, threads, a.limit)
    except Refused as exc:
        print(f"REFUSED: {exc}", flush=True)
        sys.exit(3)
    sys.exit(code)


if __name__ == "__main__":
    main()
