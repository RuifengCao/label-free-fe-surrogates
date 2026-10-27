#!/usr/bin/env python3
"""cmame-paper Stage 14 (RUNBOOK_CMAME Sec. G): the enriched c* reading
(Appendix 2, fixed on 20 October 2026 before any computation; exploratory,
post hoc, not in the manuscript). Per instance, load case and seed, three
projections of the finite-element solution, with the label-free networks'
predictions u and the coarse space of Appendix 1 at 2D p = 6 (42 unknowns),
3D p = 8 (360) (fejepa.analysis.ritz):
  cstar     the network scaled by c* = F^T u / u^T K u (the Ritz projection on span{u});
  ritz      the polynomial Ritz solution (on range(P); Appendix 1's solve);
  enriched  the Ritz projection on span{u} + range(P) (Jacobi-scaled, cut 1e-12);
beside the network itself (net). The enriched energy gap is at most the
smaller of the other two (both spaces lie in the enriched one): the rows
record its largest excess per instance (round-off), and each summary flags
it (`bound_ok`: at most 1e-8).

Arms (configs/ritz_v1.json, `enriched.arms`; one per run, --arm):
  b_n1024, s_n1024  wp9 session 2's 2D transformers, the fresh baseline and S,
                    seeds 3-5, on wp9's sets IB (2,048), F2 and F5 (256 each),
                    runs/w9/ood2d (the box's report, pinned to wp9-pool's record);
  phase2b           Phase-2b's 3D label-free transformer, seeds 0-2, on val3d
                    (its 256 validation instances) and fine3d (the first 256 of
                    its fine set);
and, beyond Appendix 2 (`"appendix": false`), on val3d and fine3d:
  phase2b_labels    Phase-2's labels-only transformer (L_D), seeds 0-2;
  phase2b_mgn       Phase-2's graph network, seeds 0-2;
  k3d_labels_knorm  PREREG_K3D's stiffness-norm transformer (L_K), seeds 0-2.

Inputs are checked before anything runs (exit 3 on a refusal): the report by
SHA-256; each state by the report's d9 record or the configuration's list; a
wp9 set by its manifest's SHA-256 as the report records it and each file by
its manifest's SHA-256; a 3D set as scripts/ritz_baseline.py checks it.
Then every seed's model predicts the first `precheck_n` (8) instances of the
set (of its run's validation split when the set has no record of it, as for
L_K on fine3d) and its five recomputed metrics are compared with the
report's per-instance arrays (fejepa.analysis.holdout.content_check,
`content_tol` 1e-3): a model that does not reproduce stops the run with exit
5 before anything is written.

Per instance: the identity check (the size and ||U*||_K against the records,
as Appendix 1's); the predictions on the GPU (this process); the coarse
space, the Ritz solution and per seed the four variants' five metrics per
load case, c*, ||u||_K, the dropped directions and the bound's excess, in
--workers spawned processes; rows written in order to
OUT/enriched/<arm>/<set>/rows.jsonl (a run again resumes after the last
complete line). Once a set is complete: summary.json, with the content check
of the network on every instance; then OUT/enriched/<arm>/reading.json,
rebuilt from every complete set summary of the arm: Appendix 2's two
conditions per seed and whether the arm is complementary (true when a
computed condition holds, false when both are computed and neither holds,
null otherwise), and the same without the instances that fail the identity
check. Per-instance values are the means over the load battery (as the
records); the per-load-case medians are reported beside them; the
out-of-distribution condition must hold for every seed and set.

Exit status: 0 done; 2 no usable GPU with --device cuda; 3 an input refused;
4 an instance that is not the recorded one (everything written, listed); 5 a
model that does not reproduce its records (at the precheck, nothing written;
on the whole set, everything written); anything else an error.

    python scripts/enriched_cstar.py --config configs/ritz_v1.json --arm phase2b --device cuda
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

VARIANTS = ("net", "cstar", "ritz", "enriched")
EVERY = 16
BOUND_TOL = 1e-8
"""The enriched energy gap may exceed the smaller of c* u's and Ritz's by at
most this (round-off; relative energy gap): `bound_ok` in each summary."""
SOLVES = {"ritz": "Appendix 1: eigendecomposition of A = P^T K P, eigenvalues at most 1e-13 "
                  "times the largest dropped, no scaling",
          "enriched": "the Galerkin system of span{u} + range(P) after Jacobi scaling, "
                      "eigendecomposition, eigenvalues at most 1e-12 times the largest dropped "
                      "(the reference script's solve; Appendix 2 leaves it open)"}


class Refused(Exception):
    """An input that is not the one the configuration names (exit 3)."""


class NotReproduced(Exception):
    """A model whose metrics differ from its report's (exit 5)."""


def _json(path, sha, what) -> dict:
    try:
        return json.loads(R.checked(path, sha, what).read_text())
    except ValueError as exc:
        raise Refused(str(exc)) from None


# ------------------------------------------------------------------ inputs --

REPORT_OVERRIDE = {}
"""{arm: path} from --report: the same report (its SHA-256 still checked)
read from another place, e.g. wp9-pool's records copy on the repository side."""


def arm_report(cfg: dict, arm: str) -> dict:
    a = cfg["enriched"]["arms"][arm]
    return _json(REPORT_OVERRIDE.get(arm, a["report"]), a["report_sha256"], f"{arm} report")


def arm_seeds(rep: dict) -> list:
    from fejepa.analysis.posthoc import run_seeds

    return run_seeds(rep)


def arm_states(cfg: dict, arm: str, rep: dict) -> dict:
    """{seed: path} of the arm's states, each checked (Refused otherwise)."""
    a = cfg["enriched"]["arms"][arm]
    st = a["states"]
    seeds = arm_seeds(rep)
    if st["from"] == "d9":
        from fejepa.analysis.posthoc import verified_states

        try:
            return {int(s): Path(p) for s, p in verified_states(rep, st["dir"]).items()}
        except SystemExit as exc:
            raise Refused(f"{arm}: {exc}") from None
    out = {}
    if sorted(st["sha256"]) != sorted(str(s) for s in seeds):
        raise Refused(f"{arm}: the configuration lists states for {sorted(st['sha256'])}, the "
                      f"report's seeds are {seeds}")
    for s in seeds:
        try:
            out[int(s)] = R.checked(st["pattern"].format(seed=s), st["sha256"][str(s)],
                                    f"{arm} state s{s}")
        except ValueError as exc:
            raise Refused(str(exc)) from None
    return out


def record_cells(cfg: dict, arm: str, rep: dict, sname: str):
    """The report's per-seed per-instance arrays of the arm on the set (in the
    order of the run's seeds), or None when the records hold none."""
    a = cfg["enriched"]["arms"][arm]
    desc = (a.get("records") or {}).get(sname)
    if not desc:
        return None
    parts = desc.split(":")
    src = rep
    if parts[0] == "k3d":
        src = _json(a["records_report"], a["records_report_sha256"], f"{arm} records report")
        parts = parts[1:]
    if parts[0] == "holdouts":
        pse = src["results"]["e8"]["metrics"]["holdouts"][parts[1]][parts[2]]["per_seed_eval"]
    elif parts[0] == "cells":
        cells = src["results"]["e8"]["metrics"]["cells"] if "results" in src else src["cells"]
        pse = cells[parts[1]][parts[2]]["per_seed_eval"]
    elif parts[0] == "p3":
        m = src["results"]["p3_transfer"]["metrics"]
        pse = (m["ar"]["fine"] if parts[1] == "ar"
               else m["zero_shot_reported"][parts[1]]["fine"])["per_seed_eval"]
    else:
        raise ValueError(f"records {desc!r}")
    seeds = arm_seeds(rep)
    if len(pse) != len(seeds):
        raise Refused(f"{arm} {sname}: {len(pse)} seeds recorded, the report runs {seeds}")
    return [{"metrics": e["per_instance"], "amplitude": (e.get("amplitude") or {}).get(
        "per_instance")} for e in pse]


def set_jobs(cfg: dict, arm: str, rep: dict, sname: str) -> list:
    """The set's instances on the box, as jobs (path, SHA-256 where recorded,
    the identity record), in the records' order; Refused otherwise."""
    sdef = cfg["enriched"]["sets"][sname]
    if sdef["kind"] == "w9":
        from fejepa.data.archive import load_manifest, manifest_sha256

        h = (rep.get("evaluation") or {}).get("holdouts", {}).get(sname)
        if not h:
            raise Refused(f"{arm}: the report records no set {sname}")
        d = Path(h["dir"])
        try:
            got = manifest_sha256(d)
            recs = load_manifest(d)["instances"]
        except (OSError, ValueError, KeyError) as exc:
            raise Refused(f"{sname}: {exc}") from None
        if got != h["manifest_sha256"]:
            raise Refused(f"{d}/manifest.json: SHA-256 {got[:12]}..., the report's "
                          f"{h['manifest_sha256'][:12]}...")
        if len(recs) != int(sdef["n"]) or \
                [r["file"] for r in recs] != [f"instance_{i:05d}.npz" for i in range(len(recs))]:
            raise Refused(f"{d}: the manifest does not list instance_00000 to "
                          f"instance_{int(sdef['n']) - 1:05d} in order")
        cells = record_cells(cfg, arm, rep, sname)
        amp = cells[0]["amplitude"] if cells else None
        if not amp or len(amp["ustar_norm_K"]) != len(recs):
            raise Refused(f"{arm} {sname}: no per-instance ||U*||_K in the report")
        jobs = [{"i": i, "file": r["file"], "path": str(d / r["file"]), "sha256": r["sha256"],
                 "identity": {"file": r["file"], "size_kind": "n_nodes",
                              "size": int(r["n_nodes"]),
                              "ustar_norm_K": [float(x) for x in amp["ustar_norm_K"][i]]}}
                for i, r in enumerate(recs)]
    elif sdef["kind"] == "run":
        from fejepa.analysis.posthoc import run_files

        idc = sdef["identity"]
        amp = _json(idc["path"], idc["sha256"], f"{sname} identity record")
        per = amp["seeds"]["s0"][idc["part"]]["per_instance"]
        try:
            files = [Path(f) for f in run_files(rep, sdef["which"])]
        except (SystemExit, OSError, ValueError, KeyError) as exc:
            raise Refused(f"{sname}: {exc}") from None
        if [f.name for f in files] != [r["file"] for r in per] or len(files) != int(sdef["n"]):
            raise Refused(f"{sname}: the box's files are not the records' ({len(files)} files)")
        jobs = [{"i": i, "file": f.name, "path": str(f),
                 "identity": {"file": r["file"], "size_kind": "n_nodes",
                              "size": int(r["n_nodes"]),
                              "ustar_norm_K": [float(x) for x in r["ustar_norm_K"]]}}
                for i, (f, r) in enumerate(zip(files, per))]
    else:
        raise ValueError(f"set kind {sdef['kind']!r}")
    missing = [j["path"] for j in jobs if not Path(j["path"]).is_file()]
    if missing:
        raise Refused(f"{sname}: {len(missing)} files missing (first {missing[0]})")
    bad = [j["path"] for j in jobs if "sha256" in j and R.sha256(j["path"]) != j["sha256"]]
    if bad:
        raise Refused(f"{sname}: {len(bad)} files differ from their manifest's SHA-256 "
                      f"(first {bad[0]})")
    for j in jobs:
        j["dim"] = int(sdef["dim"])
    return jobs


def precheck_target(cfg: dict, arm: str, sname: str) -> str:
    """The set whose records the precheck compares with: the set itself when
    the records hold it, else the arm's in-band set of that dimension."""
    a = cfg["enriched"]["arms"][arm]
    if (a.get("records") or {}).get(sname):
        return sname
    inb = [s for s in a["sets"] if cfg["enriched"]["sets"][s]["inband"]
           and (a.get("records") or {}).get(s)]
    if not inb:
        raise Refused(f"{arm} {sname}: no record to check the models against")
    return inb[0]


# ------------------------------------------------------------------ models --

def build_models(cfg: dict, arm: str, rep: dict, states: dict, device: str) -> dict:
    """{seed: model} in eval mode under the run's TF32 policy, strictly loaded."""
    from fejepa.analysis.holdout import row_model

    a = cfg["enriched"]["arms"][arm]
    sdef = {"rows": {a["row"]: {"kind": a["kind"]}}}
    out = {}
    for s, p in states.items():
        try:
            m = row_model(rep, sdef, a["row"], p, s, device)
        except (SystemExit, ValueError) as exc:
            raise Refused(f"{arm} s{s}: {exc}") from None
        m.eval()
        out[int(s)] = m
    return out


def predict_all(models: dict, arch, device: str) -> dict:
    """{seed: (L, ndof) prediction, as the model returns it (float32, the
    array the records' metrics were computed from)}; one preparation for
    every seed (the pack depends on the configuration and the instance only)."""
    import torch

    pack = next(iter(models.values())).prepare_instance(arch, device)
    out = {}
    with torch.no_grad():
        for s, m in models.items():
            out[s] = m.forward_instance(pack).detach().cpu().numpy()
    return out


def precheck(cfg: dict, arm: str, rep: dict, models: dict, sname: str, device: str) -> dict:
    """The models on the first precheck_n instances of the target set, their
    recomputed metrics against the records (NotReproduced otherwise)."""
    from fejepa.analysis.holdout import content_check
    from fejepa.data.archive import load_instance
    from fejepa.metrics import evaluate_fields

    target = precheck_target(cfg, arm, sname)
    cells = record_cells(cfg, arm, rep, target)
    n = int(cfg["enriched"]["precheck_n"])
    tol = float(cfg["enriched"]["content_tol"])
    jobs = set_jobs(cfg, arm, rep, target)[:n]
    got = {s: {k: [] for k in R.FIELDS} for s in models}
    for j in jobs:
        a = load_instance(j["path"])
        for s, U in predict_all(models, a, device).items():
            v = evaluate_fields(U, a)
            for k in R.FIELDS:
                got[s][k].append(v[k])
    out = {}
    for k, s in enumerate(models):
        ref = {f: list(cells[k]["metrics"][f][:len(jobs)]) for f in R.FIELDS}
        out[f"s{s}"] = content_check(got[s], ref, tol)
    bad = {s: c for s, c in out.items() if not c["ok"]}
    res = {"set": target, "n": len(jobs), "tolerance": tol, "checks": out}
    if bad:
        raise NotReproduced(json.dumps({"precheck": res}))
    return res


# ------------------------------------------------------------------ worker --

def compute_row(job: dict) -> dict:
    """One instance: identity, coarse space, Ritz, and per seed the variants
    (in a worker)."""
    from fejepa.analysis.posthoc import amplitude_factor, apply_amplitude
    from fejepa.data.archive import load_instance

    t0 = time.perf_counter()
    if "sha256" in job and R.sha256(job["path"]) != job["sha256"]:
        raise ValueError(f"{job['path']}: SHA-256 differs from the manifest")
    arch = load_instance(job["path"])
    if arch.U_star is None:
        raise ValueError(f"{job['path']}: no labels")
    t = {"load": time.perf_counter() - t0}
    C = R.coarse(arch, int(job["p"]))
    Us = np.atleast_2d(arch.U_star)[:, C["free"]]
    nk = R.ustar_norm_K(C["Kff"], Us)
    idr = job["identity"]
    if idr["file"] != job["file"]:
        raise ValueError(f"record order: {idr['file']} at {job['i']}, expected {job['file']}")
    size = int(arch.n_nodes) if idr["size_kind"] == "n_nodes" else int(C["Kff"].shape[0])
    ident = R.identity(size == idr["size"], nk, idr["ustar_norm_K"])
    ident.update(size_kind=idr["size_kind"], size_recorded=idr["size"], size=size)
    row = {"i": job["i"], "file": job["file"], "n_nodes": int(arch.n_nodes),
           "ndof_free": int(C["Kff"].shape[0]), "p": int(job["p"]), "k": int(C["A"].shape[0]),
           "ustar_norm_K": [float(x) for x in nk], "identity": ident}
    t1 = time.perf_counter()
    Ur, dr = R.ritz_coarse(C)
    row["ritz"] = R.metrics(R.full_field(C, Ur), arch)
    row["ritz_dropped"] = dr
    gr = np.asarray(row["ritz"]["load"]["energy_gap_rel"])
    row["seeds"] = {}
    for s, U_net in zip(job["seeds"], job["preds"]):
        U = np.asarray(U_net, dtype=np.float64)
        c = amplitude_factor(U, arch.K, arch.F, C["free"], Kf=C["Kff"])
        uf = U[:, C["free"]]
        un = np.sqrt(np.maximum(np.einsum("li,li->l", uf, np.asarray((C["Kff"] @ uf.T).T)), 0.0))
        Ue_f, de = R.enriched(C, uf)
        ent = {"net": R.metrics(U_net, arch), "cstar": R.metrics(apply_amplitude(U, c), arch),
               "enriched": R.metrics(R.full_field(C, Ue_f), arch),
               "c_star": [float(x) for x in c], "u_norm_K": [float(x) for x in un],
               "enriched_dropped": [int(x) for x in de]}
        ge = np.asarray(ent["enriched"]["load"]["energy_gap_rel"])
        gc = np.asarray(ent["cstar"]["load"]["energy_gap_rel"])
        ent["bound_excess"] = float(np.max(ge - np.minimum(gc, gr)))
        rec = (job.get("records") or {}).get(str(s))
        if rec is not None:
            ent["repro"] = {
                "energy_gap_rel_rel_diff": abs(ent["net"]["mean"]["energy_gap_rel"] - rec["egap"])
                / max(abs(rec["egap"]), 1e-300)}
            if rec.get("c_star") is not None:
                ent["repro"]["c_star_max_abs_diff"] = float(np.nanmax(np.abs(
                    c - np.asarray(rec["c_star"], float))))
                ru = np.asarray(rec["u_norm_K"], float)
                ent["repro"]["u_norm_K_max_rel_diff"] = float(np.max(np.abs(un - ru)
                                                                     / np.maximum(ru, 1e-300)))
        row["seeds"][str(s)] = ent
    t["projections_and_metrics"] = time.perf_counter() - t1
    row["t"] = t
    return row


def _worker_init(threads: int) -> None:
    try:
        from threadpoolctl import threadpool_limits

        threadpool_limits(int(threads))
    except ImportError:
        pass


def pipelined(produce, fn, workers: int, threads: int):
    """fn(job) for every job `produce` yields (the predictions are made there,
    in this process), yielded in order; with workers > 1, by spawned workers
    with at most 2 x workers jobs in flight; the first error cancels the rest
    and is raised."""
    if workers <= 1:
        for j in produce:
            yield fn(j)
        return
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor

    for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[k] = str(int(threads))
    ex = ProcessPoolExecutor(max_workers=int(workers), mp_context=mp.get_context("spawn"),
                             initializer=_worker_init, initargs=(int(threads),))
    pending = deque()
    try:
        for j in produce:
            pending.append(ex.submit(fn, j))
            while len(pending) >= 2 * workers or (pending and pending[0].done()):
                yield pending.popleft().result()
        while pending:
            yield pending.popleft().result()
    except BaseException:
        ex.shutdown(wait=False, cancel_futures=True)
        raise
    ex.shutdown(wait=True)


# ---------------------------------------------------------------- summary --

def _q(v) -> dict:
    v = np.asarray(v, dtype=float)
    f = v[np.isfinite(v)]
    return {"median": float(np.median(f)) if f.size else None,
            "mean": float(np.mean(f)) if f.size else None, "n": int(f.size),
            "non_finite": int(v.size - f.size)}


def summarise_seeds(rows: list, seeds: list) -> dict:
    out = {}
    for s in seeds:
        per = {v: {f: [] for f in R.FIELDS} for v in VARIANTS}
        flat = {v: {"energy_gap_rel": [], "peak_vm_rel_err": []} for v in VARIANTS}
        for r in rows:
            e = r["seeds"][str(s)]
            src = {"ritz": r["ritz"], "net": e["net"], "cstar": e["cstar"],
                   "enriched": e["enriched"]}
            for v in VARIANTS:
                for f in R.FIELDS:
                    per[v][f].append(src[v]["mean"][f])
                for f in flat[v]:
                    flat[v][f] += src[v]["load"][f]
        ss = {v: {f: _q(per[v][f]) for f in R.FIELDS} for v in VARIANTS}
        med = {v: ss[v]["energy_gap_rel"]["median"] for v in VARIANTS}
        ss["inband_ratio"] = med["enriched"] / min(med["cstar"], med["ritz"])
        ss["ood_peak_ratio"] = (ss["enriched"]["peak_vm_rel_err"]["median"]
                                / ss["ritz"]["peak_vm_rel_err"]["median"])
        fm = {v: {f: float(np.nanmedian(flat[v][f])) for f in flat[v]} for v in VARIANTS}
        ss["per_load_case"] = {
            "median": fm,
            "inband_ratio": fm["enriched"]["energy_gap_rel"] / min(fm["cstar"]["energy_gap_rel"],
                                                                   fm["ritz"]["energy_gap_rel"]),
            "ood_peak_ratio": fm["enriched"]["peak_vm_rel_err"] / fm["ritz"]["peak_vm_rel_err"]}
        ss["bound_excess_max"] = max(r["seeds"][str(s)]["bound_excess"] for r in rows)
        ss["bound_ok"] = bool(ss["bound_excess_max"] <= BOUND_TOL)
        ss["enriched_dropped_max"] = max(max(r["seeds"][str(s)]["enriched_dropped"])
                                         for r in rows)
        ss["worse_than_zero"] = {v: int(sum((r["seeds"][str(s)][v] if v != "ritz" else r["ritz"])
                                            ["worse_than_zero"]["worse"] for r in rows))
                                 for v in VARIANTS}
        rep = [r["seeds"][str(s)].get("repro") for r in rows]
        rep = [x for x in rep if x]
        if rep:
            ss["repro"] = {k: {"median": float(np.nanmedian([x[k] for x in rep if k in x])),
                               "max": float(np.nanmax([x[k] for x in rep if k in x]))}
                           for k in rep[0]}
        out[str(s)] = ss
    return out


def content_all(rows: list, seeds: list, cells, tol: float) -> dict | None:
    """The network's recomputed per-instance metrics on the whole set against
    the records (None when the records hold no array of the set)."""
    if cells is None:
        return None
    from fejepa.analysis.holdout import content_check

    out = {}
    for k, s in enumerate(seeds):
        got = {f: [r["seeds"][str(s)]["net"]["mean"][f] for r in rows] for f in R.FIELDS}
        ref = {f: [cells[k]["metrics"][f][r["i"]] for r in rows] for f in R.FIELDS}
        out[f"s{s}"] = content_check(got, ref, tol)
    return {"tolerance": tol, "checks": out,
            "passed": bool(all(c["ok"] for c in out.values()))}


def summarise(rows: list, seeds: list, cells, tol: float) -> dict:
    ok = [r for r in rows if r["identity"]["ok"]]
    return {"n": len(rows), "n_identity_ok": len(ok),
            "identity_failed": [r["file"] for r in rows if not r["identity"]["ok"]],
            "identity_max_rel_diff": max(r["identity"]["ustar_norm_K_max_rel_diff"]
                                         for r in rows),
            "ritz_dropped_max": max(r["ritz_dropped"] for r in rows),
            "content": content_all(rows, seeds, cells, tol),
            "seeds": summarise_seeds(rows, seeds),
            "seeds_identity_ok": (summarise_seeds(ok, seeds) if ok and len(ok) < len(rows)
                                  else None)}


def reading(cfg: dict, arm: str, base: Path) -> dict:
    """Appendix 2 from every complete set summary of the arm on disk (the
    seeds are the summaries' own, which must agree)."""
    a = cfg["enriched"]["arms"][arm]
    sets = list(a["sets"])
    inband = [n for n in sets if cfg["enriched"]["sets"][n]["inband"]]
    ood = [n for n in sets if not cfg["enriched"]["sets"][n]["inband"]]
    summ, refused = {}, {}
    for n in sets:
        p = base / n / "summary.json"
        if p.is_file():
            s = json.loads(p.read_text())
            if (s.get("content") or {}).get("passed") is False:
                refused[n] = "the network does not reproduce its records on this set"
            elif s.get("complete"):
                summ[n] = s
    keys = {json.dumps([s.get("state_sha256"), s.get("seeds_order")], sort_keys=True)
            for s in summ.values()}
    if len(keys) > 1:
        raise Refused(f"{base}: the set summaries come from different states")
    seeds = next(iter(summ.values()))["seeds_order"] if summ else []

    def conds(sm: dict) -> dict:
        res = {"inband": None, "ood": None}
        if inband and all(n in sm for n in inband):
            r = {n: {str(s): sm[n]["seeds"][str(s)]["inband_ratio"] for s in seeds}
                 for n in inband}
            res["inband"] = {"sets": inband, "ratio": r, "threshold": R.INBAND_FACTOR,
                             "holds": bool(all(v <= R.INBAND_FACTOR for x in r.values()
                                               for v in x.values()))}
        if ood and all(n in sm for n in ood):
            r = {n: {str(s): sm[n]["seeds"][str(s)]["ood_peak_ratio"] for s in seeds}
                 for n in ood}
            res["ood"] = {"sets": ood, "peak_ratio": r, "threshold": R.OOD_PEAK_FACTOR,
                          "holds": bool(all(v <= R.OOD_PEAK_FACTOR for x in r.values()
                                            for v in x.values()))}
        held = [c["holds"] for c in res.values() if c is not None]
        res["complementary"] = True if any(held) else (False if len(held) == 2 else None)
        return res

    out = {"arm": arm, "appendix": bool(a["appendix"]),
           "spec": ("Appendix 2, fixed 20 October 2026; exploratory" if a["appendix"] else
                    "Appendix 2's reading applied to a model beyond it (optional); exploratory"),
           "sets_complete": sorted(summ), "sets_required": sets, "sets_refused": refused,
           "bound_ok": {n: bool(all(v["bound_ok"] for v in s["seeds"].values()))
                        for n, s in summ.items()},
           "all_instances": conds(summ)}
    failed = {n: s["identity_failed"] for n, s in summ.items()}
    if any(failed.values()):
        sm = {n: dict(s, seeds=s["seeds_identity_ok"] or s["seeds"])
              for n, s in summ.items() if s["n_identity_ok"] > 0}
        out["identity_ok_instances"] = conds(sm)
    out["identity_failed"] = failed
    out["choices"] = ("per-instance values are the means over the load battery (as the "
                      "records); the per-load-case medians are in each set's summary; the "
                      "out-of-distribution condition must hold for every seed and set; arms "
                      "are read separately; 'complementary' is true when a computed condition "
                      "holds, false when both are computed and neither holds, null otherwise; "
                      "all_instances reads every instance, identity_ok_instances (present "
                      "when an instance fails the identity check) only those that pass; a set "
                      "whose network does not reproduce its records is left out "
                      "(sets_refused)")
    out["solves"] = SOLVES
    return out


def set_fields(cfg: dict, arm: str, sname: str) -> dict:
    a = cfg["enriched"]["arms"][arm]
    return {"arm": arm, "set": sname, "degree": R.ENRICHED_DEGREE[int(a["dim"])],
            "complete": True, "appendix": bool(a["appendix"]), "row": a["row"],
            "kind": a["kind"], "report": a["report"], "report_sha256": a["report_sha256"],
            "solves": SOLVES, "bound_tol": BOUND_TOL}


KEPT = ("state_sha256", "seeds_order", "torch", "device", "gpu", "workers", "worker_threads",
        "machine", "code", "config_sha256")
"""The fields of a set summary that only the box run knows (kept by --resummarise)."""


def resummarise(cfg: dict, arm: str, d: Path) -> dict:
    """DIR/summary.json rebuilt from DIR/rows.jsonl and the records (the
    repository side, on a return; the box-only fields kept from the summary
    there)."""
    sname = d.name
    if sname not in cfg["enriched"]["arms"][arm]["sets"]:
        raise Refused(f"{d}: not a set of arm {arm}")
    rep = arm_report(cfg, arm)
    seeds = arm_seeds(rep)
    rows = R.complete_lines(d / "rows.jsonl")
    n = int(cfg["enriched"]["sets"][sname]["n"])
    if [r["i"] for r in rows] != list(range(n)):
        raise Refused(f"{d}/rows.jsonl: not the complete set {sname}")
    prev = json.loads((d / "summary.json").read_text()) if (d / "summary.json").is_file() \
        else {}
    if prev.get("seeds_order", seeds) != seeds:
        raise Refused(f"{d}/summary.json: seeds {prev.get('seeds_order')}, the report's {seeds}")
    summ = summarise(rows, seeds, record_cells(cfg, arm, rep, sname),
                     float(cfg["enriched"]["content_tol"]))
    summ.update(set_fields(cfg, arm, sname))
    summ.update({k: prev[k] for k in KEPT if k in prev})
    summ["rows_sha256"] = R.sha256(d / "rows.jsonl")
    R.write_json(d / "summary.json", summ)
    return summ


# -------------------------------------------------------------------- main --

def check_arm(cfg: dict, arm: str) -> dict:
    rep = arm_report(cfg, arm)
    states = arm_states(cfg, arm, rep)
    sets = {}
    for sname in cfg["enriched"]["arms"][arm]["sets"]:
        sets[sname] = len(set_jobs(cfg, arm, rep, sname))
        t = precheck_target(cfg, arm, sname)
        if record_cells(cfg, arm, rep, t) is None:
            raise Refused(f"{arm} {sname}: no records")
    return {"arm": arm, "seeds": sorted(states), "states_verified": len(states), "sets": sets}


def run_arm(cfg: dict, cfg_path: Path, arm: str, device: str, workers: int, threads: int,
            limit: int, only: list | None) -> int:
    import torch

    t_all = time.time()
    a = cfg["enriched"]["arms"][arm]
    rep = arm_report(cfg, arm)
    states = arm_states(cfg, arm, rep)
    seeds = arm_seeds(rep)
    sets = [s for s in a["sets"] if not only or s in only]
    jobs_by_set = {s: set_jobs(cfg, arm, rep, s) for s in sets}      # all refused up front
    if device.startswith("cuda") and not torch.cuda.is_available():
        print("no usable GPU (torch.cuda.is_available() is False)", flush=True)
        return 2
    models = build_models(cfg, arm, rep, states, device)
    sha = {str(s): R.sha256(p) for s, p in states.items()}
    p = R.ENRICHED_DEGREE[int(a["dim"])]
    tol = float(cfg["enriched"]["content_tol"])
    base = Path(cfg["out"]) / "enriched" / arm
    code = 0
    for sname in sets:
        jobs = jobs_by_set[sname]
        out = base / sname
        out.mkdir(parents=True, exist_ok=True)
        rows_path = out / "rows.jsonl"
        done = R.complete_lines(rows_path)
        if [r["file"] for r in done] != [j["file"] for j in jobs[:len(done)]] or \
                [r["i"] for r in done] != list(range(len(done))):
            raise Refused(f"{rows_path}: not a prefix of the set; move it aside")
        start = len(done)
        stop = len(jobs) if not limit else min(len(jobs), start + limit)
        cells = record_cells(cfg, arm, rep, sname)
        if start < stop:
            pre = precheck(cfg, arm, rep, models, sname, device)
            print(json.dumps({"arm": arm, "set": sname, "precheck": {
                "set": pre["set"], "n": pre["n"],
                "median_rel_dev": {s: [c["disp_rel_l2_median_rel_dev"],
                                       c["energy_gap_rel_median_rel_dev"]]
                                   for s, c in pre["checks"].items()}}}), flush=True)
            if start:
                print(f"[enriched {arm} {sname}] resuming after {start} instances on disk",
                      flush=True)
        elif start == len(jobs):
            print(f"[enriched {arm} {sname}] all {len(jobs)} instances on disk", flush=True)
        recs = None
        if cells is not None:
            recs = []
            for i in range(len(jobs)):
                d = {}
                for k, s in enumerate(seeds):
                    amp = cells[k]["amplitude"]
                    d[str(s)] = {"egap": float(cells[k]["metrics"]["energy_gap_rel"][i]),
                                 "c_star": amp["c_star"][i] if amp else None,
                                 "u_norm_K": amp["u_norm_K"][i] if amp else None}
                recs.append(d)

        def produce():
            """The jobs with their predictions, the next instance read in a
            thread while the GPU predicts this one."""
            from concurrent.futures import ThreadPoolExecutor

            from fejepa.data.archive import load_instance

            todo = jobs[start:stop]
            with ThreadPoolExecutor(max_workers=1) as io:
                nxt = io.submit(load_instance, todo[0]["path"]) if todo else None
                for k, j in enumerate(todo):
                    arch = nxt.result()
                    nxt = (io.submit(load_instance, todo[k + 1]["path"]) if k + 1 < len(todo)
                           else None)
                    preds = predict_all(models, arch, device)
                    del arch
                    yield dict(j, p=p, seeds=list(preds), preds=list(preds.values()),
                               records=recs[j["i"]] if recs is not None else None)

        t0 = time.time()
        with open(rows_path, "a") as fh:
            for row in pipelined(produce(), compute_row, workers, threads):
                R.append_row(fh, row)
                i = row["i"]
                if not row["identity"]["ok"]:
                    print(f"[enriched {arm} {sname}] {i + 1}/{len(jobs)} {row['file']}: "
                          "NOT THE RECORDED INSTANCE", flush=True)
                if (i + 1) % EVERY == 0 or i + 1 == stop:
                    print(f"[enriched {arm} {sname}] {i + 1}/{len(jobs)} | "
                          f"{time.time() - t0:.0f} s", flush=True)
        rows = R.complete_lines(rows_path)
        if len(rows) < len(jobs):
            print(f"[enriched {arm} {sname}] {len(rows)}/{len(jobs)} instances on disk; no "
                  f"summary yet", flush=True)
            continue
        summ = summarise(rows, seeds, cells, tol)
        summ.update(set_fields(cfg, arm, sname))
        summ.update({"state_sha256": sha, "seeds_order": seeds,
                     "torch": torch.__version__, "device": device,
                     "gpu": torch.cuda.get_device_name(0) if device.startswith("cuda") else None,
                     "workers": int(workers), "worker_threads": int(threads),
                     "machine": R.machine(), "code": R.code_provenance(ROOT),
                     "config_sha256": R.sha256(cfg_path),
                     "rows_sha256": R.sha256(rows_path)})
        R.write_json(out / "summary.json", summ)
        line = {"arm": arm, "set": sname, "n": summ["n"],
                "identity_failed": len(summ["identity_failed"]),
                "content_passed": (summ["content"] or {}).get("passed"),
                "bound_ok": bool(all(v["bound_ok"] for v in summ["seeds"].values())),
                "bound_excess_max": max(v["bound_excess_max"] for v in summ["seeds"].values()),
                "ratio": {s: [round(v["inband_ratio"], 4), round(v["ood_peak_ratio"], 4)]
                          for s, v in summ["seeds"].items()},
                "seconds": round(time.time() - t0, 1)}
        print(json.dumps(line), flush=True)
        if summ["identity_failed"]:
            code = max(code, 4)
        if (summ["content"] or {}).get("passed") is False:
            code = 5
    r = reading(cfg, arm, base)
    R.write_json(base / "reading.json", r)
    line = {"arm": arm, "sets_complete": r["sets_complete"],
            "complementary": r["all_instances"]["complementary"]}
    if "identity_ok_instances" in r:
        line["complementary_identity_ok"] = r["identity_ok_instances"]["complementary"]
    print(json.dumps(dict(line, seconds=round(time.time() - t_all, 1))), flush=True)
    return code


def main() -> None:
    ap = argparse.ArgumentParser(description="The enriched c* reading (Appendix 2, fixed 20 "
                                             "October 2026; exploratory, post hoc)")
    ap.add_argument("--config", required=True, help="configs/ritz_v1.json")
    ap.add_argument("--arm", required=True, help="an arm of the configuration, or all (with "
                                                 "--check)")
    ap.add_argument("--sets", default=None, help="comma-separated subset of the arm's sets")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--workers", type=int, default=None, help="default: the configuration's")
    ap.add_argument("--worker-threads", type=int, default=None,
                    help="BLAS threads per worker (default: the configuration's)")
    ap.add_argument("--limit", type=int, default=0, help="stop after this many instances per set")
    ap.add_argument("--check", action="store_true", help="verify the inputs only")
    ap.add_argument("--reread", default=None,
                    help="rebuild DIR/reading.json from the set summaries under DIR only "
                         "(DIR = the arm's directory of a return; 'box': OUT/enriched/<arm>)")
    ap.add_argument("--resummarise", default=None,
                    help="rebuild DIR/summary.json from DIR/rows.jsonl and the records "
                         "(DIR = a set's directory of a return)")
    ap.add_argument("--report", default=None,
                    help="read the arm's report from this path (its SHA-256 is still the "
                         "configuration's)")
    a = ap.parse_args()
    try:
        cfg = R.load_config(a.config)
    except (OSError, ValueError, KeyError) as exc:
        print(f"REFUSED: {exc}", flush=True)
        sys.exit(3)
    arms = list(cfg["enriched"]["arms"])
    sel = arms if a.arm == "all" else [a.arm]
    if any(x not in arms for x in sel) or (a.arm == "all" and not a.check):
        ap.error(f"--arm: one of {', '.join(arms)} (all: with --check only)")
    only = a.sets.split(",") if a.sets else None
    if only and any(s not in cfg["enriched"]["arms"][sel[0]]["sets"] for s in only):
        ap.error(f"--sets: of {cfg['enriched']['arms'][sel[0]]['sets']}")
    workers = int(a.workers if a.workers is not None else cfg["enriched"]["workers"])
    threads = int(a.worker_threads if a.worker_threads is not None
                  else cfg["enriched"]["worker_threads"])
    if a.report:
        REPORT_OVERRIDE[sel[0]] = a.report
    code = 0
    try:
        if a.check:
            for arm in sel:
                print(json.dumps(check_arm(cfg, arm)), flush=True)
        elif a.resummarise:
            summ = resummarise(cfg, sel[0], Path(a.resummarise))
            print(json.dumps({"arm": sel[0], "set": summ["set"], "n": summ["n"],
                              "rebuilt": str(Path(a.resummarise) / "summary.json")}), flush=True)
        elif a.reread:
            base = Path(a.reread) if a.reread != "box" else Path(cfg["out"]) / "enriched" / sel[0]
            r = reading(cfg, sel[0], base)
            R.write_json(base / "reading.json", r)
            print(json.dumps({"arm": sel[0], "sets_complete": r["sets_complete"],
                              "complementary": r["all_instances"]["complementary"]}),
                  flush=True)
        else:
            code = run_arm(cfg, Path(a.config), sel[0], a.device, workers, threads, a.limit,
                           only)
    except Refused as exc:
        print(f"REFUSED: {exc}", flush=True)
        sys.exit(3)
    except NotReproduced as exc:
        print(f"NOT REPRODUCED (nothing written for this set): {exc}", flush=True)
        sys.exit(5)
    sys.exit(code)


if __name__ == "__main__":
    main()
