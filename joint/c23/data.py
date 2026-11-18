"""Instances of gate G-C2.3: G-C2.2's data code with a third held-out sample and labelled training members.

Splits: train (the 512 training members of G-C2.1, labelled at the training levels for the supervised arm), third
(64 fresh held-out members, judged), eval (the fresh held-out members of G-C2.2, reported), tested (the four tested
members, reported). G-C2.1's held-out members are not part of this gate. The export, the solver, the label files, the
ledger, the worker processes and the file checks are c2.data's and c22.data's; this module only adds the splits.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from c2.data import (export_member, _pack, stored_identity, _sha256_file, levels, manifest, check_files,
                     load_export, load_label)  # noqa: F401
from c2.family import Params, sample, violations
from c22.data import _replace, _write_json, pool, label, THREAD_VARIABLES  # noqa: F401

SPLITS = ("train", "third", "eval", "tested")
LABELLED_SPLITS = SPLITS                           # every member carries labels: the training members for the
#                                                    supervised arm, the others for the evaluation


def members(cfg: dict) -> list[tuple[str, str, Params]]:
    """(id, split, parameters) for every instance, in a fixed order."""
    d = cfg["data"]
    if d["third_eval_seed"] in d["seeds_seen_before_stamp"]:
        raise RuntimeError("the held-out seed was used before the stamp")
    if d["third_eval_seed"] in (d["train_seed"], d["eval_seed"], d["former_eval_seed"]):
        raise RuntimeError("the held-out seed is not fresh")
    tr, _ = sample(d["n_train"], seed=d["train_seed"])
    th, _ = sample(d["n_third"], seed=d["third_eval_seed"])
    ev, _ = sample(d["n_eval"], seed=d["eval_seed"])
    out = [(f"train_{i:04d}", "train", q) for i, q in enumerate(tr)]
    out += [(f"third_{i:04d}", "third", q) for i, q in enumerate(th)]
    out += [(f"eval_{i:04d}", "eval", q) for i, q in enumerate(ev)]
    for name, p in d["tested"].items():
        q = Params(**p)
        assert not violations(q), f"{name} is not a member of the family"
        out.append((f"tested_{name}", "tested", q))
    return out


def generate(cfg: dict, data_dir, splits=SPLITS) -> Path:
    """Export every member of the given splits and write the manifest (as c22.data.generate). Resumes: a file already
    written is kept if it was made for the same member under the same configuration, and refused otherwise."""
    from .config import sha256

    cfg_sha = sha256(cfg)
    data_dir = Path(data_dir)
    (data_dir / "inst").mkdir(parents=True, exist_ok=True)
    recs = []
    todo = [m for m in members(cfg) if m[1] in splits]
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


def ledger_sha256(data_dir, ids) -> tuple[str, int]:
    """The SHA-256 of the ledger entries of the given members, in the order of their ids, and their number. Each
    entry pins its instance file and its label file, so the value changes if one of these labels is solved again;
    it does not change when other members are labelled."""
    ids = set(ids)
    led = sorted((e for e in json.loads((Path(data_dir) / "labels" / "ledger.json").read_text()) if e["id"] in ids),
                 key=lambda e: e["id"])
    return hashlib.sha256(json.dumps(led, sort_keys=True).encode("ascii")).hexdigest(), len(led)


def labelled_ids(cfg: dict, data_dir, splits=LABELLED_SPLITS) -> list[str]:
    """The members of the given splits; all of them must carry labels before the evaluation."""
    return [r["id"] for r in manifest(data_dir)["instances"] if r["split"] in splits]


def check_labels(cfg: dict, data_dir, splits=LABELLED_SPLITS) -> dict:
    """As c22.data.check_labels, on the members of the given splits: each labelled once at its split's levels, files
    matching the manifest and the ledger, every level converged, the worst optimality residual of each kind within
    the configured limits, and the two force readings of each reference (spring and stresses) equal. Ledger entries
    of members outside the given splits are ignored, so that the evaluation members can be checked before the
    training members are labelled."""
    from .config import sha256

    man = manifest(data_dir)
    split = {r["id"]: r["split"] for r in man["instances"]}
    need = labelled_ids(cfg, data_dir, splits)
    led = [e for e in json.loads((Path(data_dir) / "labels" / "ledger.json").read_text())
           if split.get(e["id"]) in splits or e["id"] not in split]
    by = {e["id"]: e for e in led}
    missing = [i for i in need if i not in by]
    extra = sorted(set(by) - set(need))
    check_files(data_dir, [i for i in need if i in by])
    lim = cfg["data"]["kkt_limits"]
    worst = ({k: (min if op == ">=" else max)(e["kkt_worst"][k] for e in led) for k, (op, _) in lim.items()}
             if led else {})
    ok_kkt = {k: bool(worst[k] >= v if op == ">=" else worst[k] <= v) for k, (op, v) in lim.items()} if led else {}
    lv_ok = all(by[i]["levels"] == sorted(levels(cfg, split[i])) for i in need if i in by)
    conv = all(all(e["converged"]) for e in led)
    fe = max(e["F_vs_F_sigma"] for e in led) if led else None
    ok = (man["config_sha256"] == sha256(cfg) and not missing and not extra and lv_ok and conv and bool(led)
          and all(ok_kkt.values()) and fe is not None and fe <= 1e-6)
    return {"splits": list(splits), "labels": len(led), "needed": len(need), "missing": missing, "extra": extra,
            "levels_ok": lv_ok, "converged": conv, "worst": worst, "within_limits": ok_kkt, "max_F_vs_F_sigma": fe,
            "ok": bool(ok)}
