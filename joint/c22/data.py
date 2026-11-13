"""Instances of gate G-C2.2: G-C2.1's data code with a second held-out sample.

Splits: train (the 512 training members of G-C2.1), eval (64 fresh held-out members, judged), former (the 64
held-out members of G-C2.1, reported), tested (the four tested members, reported). The export, the solver, the label
files, the ledger and the file checks are c2.data's; this module only adds the split and lets the worker processes
start where the operating system has no fork.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

from c2.data import (export_member, _pack, stored_identity, _sha256_file, _label_one, levels, manifest, check_files,
                     load_export, load_label)  # noqa: F401
from c2.family import Params, sample, violations

LABELLED_SPLITS = ("eval", "former", "tested")


def _replace(tmp: Path, dst: Path, tries: int = 40, wait: float = 0.5) -> None:
    """Move tmp onto dst. Where another program holds a file open for a moment, which makes the move fail with
    PermissionError on Windows, the move is tried again, for up to tries * wait seconds."""
    for k in range(tries):
        try:
            os.replace(tmp, dst)
            return
        except PermissionError:
            if k == tries - 1:
                raise
            time.sleep(wait)


def _write_json(p: Path, obj) -> None:
    """Write obj to p as JSON through a temporary file and a retried move (the format of c2's writers)."""
    tmp = Path(p).with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=1))
    _replace(tmp, Path(p))


def members(cfg: dict) -> list[tuple[str, str, Params]]:
    """(id, split, parameters) for every instance, in a fixed order."""
    d = cfg["data"]
    if d["eval_seed"] in d["seeds_seen_before_stamp"]:
        raise RuntimeError("the held-out seed was used before the stamp")
    if d["eval_seed"] in (d["train_seed"], d["former_eval_seed"]):
        raise RuntimeError("the held-out seed is not fresh")
    tr, _ = sample(d["n_train"], seed=d["train_seed"])
    ev, _ = sample(d["n_eval"], seed=d["eval_seed"])
    fo, _ = sample(d["n_former"], seed=d["former_eval_seed"])
    out = [(f"train_{i:04d}", "train", q) for i, q in enumerate(tr)]
    out += [(f"eval_{i:04d}", "eval", q) for i, q in enumerate(ev)]
    out += [(f"former_{i:04d}", "former", q) for i, q in enumerate(fo)]
    for name, p in d["tested"].items():
        q = Params(**p)
        assert not violations(q), f"{name} is not a member of the family"
        out.append((f"tested_{name}", "tested", q))
    return out


def generate(cfg: dict, data_dir, splits=("train", "eval", "former", "tested"), limit: int | None = None) -> Path:
    """Export every member of the given splits and write the manifest (as c2.data.generate). Resumes: a file already
    written is kept if it was made for the same member under the same configuration, and refused otherwise."""
    from .config import sha256

    cfg_sha = sha256(cfg)
    data_dir = Path(data_dir)
    (data_dir / "inst").mkdir(parents=True, exist_ok=True)
    recs = []
    todo = [m for m in members(cfg) if m[1] in splits]
    if limit is not None:
        per = {}
        todo = [m for m in todo if per.setdefault(m[1], []).append(m) or len(per[m[1]]) <= limit]
    for iid, split, q in todo:
        p = data_dir / "inst" / f"{iid}.npz"
        if p.exists():
            params, made_under = stored_identity(p)
            if params != asdict(q) or made_under != cfg_sha:
                raise RuntimeError(f"{p} was made for another member or configuration; use a fresh directory")
        else:
            ex = export_member(cfg, q)
            tmp = p.with_suffix(".tmp")
            with open(tmp, "wb") as fh:
                np.savez_compressed(fh, **_pack(ex, q, cfg_sha))
            _replace(tmp, p)
        with np.load(p) as z:
            n_nodes, nfull = int(z["nodes"].shape[0]), int(z["v"].size)
        recs.append({"id": iid, "split": split, "params": asdict(q), "file": f"inst/{iid}.npz",
                     "sha256": _sha256_file(p), "nodes": n_nodes, "unknowns": nfull})
    _write_json(data_dir / "manifest.json", {"config_sha256": cfg_sha, "n": len(recs), "instances": recs})
    return data_dir / "manifest.json"


THREAD_VARIABLES = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")


def pool(workers: int):
    """A pool of worker processes: forked where the operating system can, spawned otherwise. A spawned worker reads
    the environment when it starts; it is told there to use one thread for linear algebra, as G-C2.1's runbook told
    its forked workers in the shell. A variable that is already set is left as it is."""
    import multiprocessing as mp

    kind = "fork" if "fork" in mp.get_all_start_methods() else "spawn"
    if kind == "spawn":
        for k in THREAD_VARIABLES:
            os.environ.setdefault(k, "1")
    return mp.get_context(kind).Pool(workers)


def label(cfg: dict, data_dir, ids, workers: int = 1) -> None:
    """Solve the listed instances at their split's levels (resumes) and record each in the ledger (as
    c2.data.label; each worker process solves whole instances, the ledger is written by this process only)."""
    data_dir = Path(data_dir)
    (data_dir / "labels").mkdir(exist_ok=True)
    rec = {r["id"]: r for r in manifest(data_dir)["instances"]}
    led_p = data_dir / "labels" / "ledger.json"
    ledger = json.loads(led_p.read_text()) if led_p.exists() else []
    done = {e["id"] for e in ledger}
    ls = cfg["data"]["label_solver"]
    jobs = [(str(data_dir), iid, rec[iid]["sha256"], levels(cfg, rec[iid]["split"]), ls["tol"], ls["max_it"])
            for iid in ids if not (iid in done and (data_dir / "labels" / f"{iid}.npz").exists())]

    def record(e):
        nonlocal ledger
        ledger = [x for x in ledger if x["id"] != e["id"]] + [e]
        _write_json(led_p, ledger)
        print(e["id"], e["seconds"], "s", "converged" if all(e["converged"]) else "NOT CONVERGED", flush=True)

    if workers <= 1:
        for j in jobs:
            record(_label_one(j))
    else:
        with pool(workers) as p:
            for e in p.imap_unordered(_label_one, jobs):
                record(e)


def labelled_ids(cfg: dict, data_dir) -> list[str]:
    """The members that must carry labels: the two held-out samples and the tested members."""
    return [r["id"] for r in manifest(data_dir)["instances"] if r["split"] in LABELLED_SPLITS]


def check_labels(cfg: dict, data_dir) -> dict:
    """As c2.data.check_labels, on this gate's labelled members: each labelled once at the judged levels, files
    matching the manifest and the ledger, every level converged, the worst optimality residual of each kind within
    the configured limits, and the two force readings of each reference (spring and stresses) equal."""
    from .config import sha256

    man = manifest(data_dir)
    split = {r["id"]: r["split"] for r in man["instances"]}
    need = labelled_ids(cfg, data_dir)
    led = json.loads((Path(data_dir) / "labels" / "ledger.json").read_text())
    by = {e["id"]: e for e in led}
    missing = [i for i in need if i not in by]
    extra = sorted(set(by) - set(need))
    check_files(data_dir, [i for i in need if i in by])
    lim = cfg["data"]["kkt_limits"]
    worst = {k: (min if op == ">=" else max)(e["kkt_worst"][k] for e in led) for k, (op, _) in lim.items()}
    ok_kkt = {k: bool(worst[k] >= v if op == ">=" else worst[k] <= v) for k, (op, v) in lim.items()}
    lv_ok = all(by[i]["levels"] == sorted(levels(cfg, split[i])) for i in need if i in by)
    conv = all(all(e["converged"]) for e in led)
    fe = max(e["F_vs_F_sigma"] for e in led) if led else None
    ok = (man["config_sha256"] == sha256(cfg) and not missing and not extra and lv_ok and conv
          and all(ok_kkt.values()) and fe is not None and fe <= 1e-6)
    return {"labels": len(led), "needed": len(need), "missing": missing, "extra": extra, "levels_ok": lv_ok,
            "converged": conv, "worst": worst, "within_limits": ok_kkt, "max_F_vs_F_sigma": fe, "ok": bool(ok)}
