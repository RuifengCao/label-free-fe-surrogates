"""Instances of the CHS surrogate gate (draft): generate the exports (each with its preload set by a solve at zero
rotation), label them (solves at the split's loading levels), check and load them. Follows c2/data.py.

Layout of a data directory:
    manifest.json             one record per instance: id, split, family parameters, file SHA-256, sizes, the
                              member's device range and the preload's check
    inst/<id>.npz             the export of f2.instance.export: the problem, the bolts' pre-shortening that gives the
                              preload, the family parameters and the configuration hash it was made under; no
                              solution field
    pre/<id>.npz              the preload state (z at zero rotation, the six bolt forces), for the reference code only:
                              labels and the evaluation start from it; training never reads it
    labels/<id>.npz           the exact solutions at the split's loading-device rotations (written by `label` only):
                              lam, Theta (L,), z (L, n_z), Pi, theta, M, M_sigma, ThetaD (L,), bolt_N (L, nb)
    labels/ledger.json        every labelled instance: id, levels, time, iterations, convergence, worst optimality
                              residuals, the SHA-256 of the instance file solved and of the label file written
Levels are fractions lam of the member's device range Theta_max (the export's), the same fractions for every member.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .family import Params, sample, violations, loading
from .instance import make, ExportedProblem, KKT_KEYS

SKIP = ("params_json", "config_sha256")


def members(cfg: dict) -> list[tuple[str, str, Params]]:
    """(id, split, parameters) for every instance, in a fixed order."""
    d = cfg["data"]
    for s in (d["train_seed"], d["eval_seed"]):
        assert s is not None and s not in d["seeds_seen_before_stamp"], "a seed unset or used before the stamp"
    tr, _ = sample(d["n_train"], seed=d["train_seed"])
    ev, _ = sample(d["n_eval"], seed=d["eval_seed"])
    out = [(f"train_{i:04d}", "train", q) for i, q in enumerate(tr)]
    out += [(f"eval_{i:04d}", "eval", q) for i, q in enumerate(ev)]
    for name, p in d["tested"].items():
        q = Params(**p)
        assert not violations(q), f"{name} is not a member of the family"
        out.append((f"tested_{name}", "tested", q))
    return out


def levels(cfg: dict, split: str) -> list[float]:
    d = cfg["data"]
    return list(d["train_label_levels"] if split == "train" else d["eval_levels"])


def export_member(cfg: dict, q: Params):
    k_th, Theta_max = loading(q)
    ex, pre = make(q, mesh=cfg["data"]["mesh"], splice=cfg["family"]["splice"], k_th=k_th,
                   tol=cfg["data"]["label_solver"]["tol"], max_it=cfg["data"]["label_solver"]["max_it"])
    ex["Theta_max"] = np.float64(Theta_max)
    return ex, pre


def _pack(ex: dict, q: Params, cfg_sha: str) -> dict:
    out = {k: np.asarray(v) for k, v in ex.items()}
    out["params_json"] = np.frombuffer(json.dumps(asdict(q)).encode(), np.uint8)
    out["config_sha256"] = np.bytes_(cfg_sha)
    return out


def load_export(path) -> tuple[dict, Params]:
    with np.load(path, allow_pickle=False) as z:
        ex = {k: z[k] for k in z.files if k not in SKIP}
        q = Params(**json.loads(bytes(z["params_json"].tobytes()).decode()))
    return ex, q


def stored_identity(path) -> tuple[dict, str]:
    with np.load(path, allow_pickle=False) as z:
        return (json.loads(bytes(z["params_json"].tobytes()).decode()),
                bytes(z["config_sha256"]).decode() if "config_sha256" in z.files else "")


def _write_json_atomic(p: Path, obj) -> None:
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=1))
    tmp.replace(p)


def _savez_atomic(p: Path, **arrays) -> None:
    tmp = Path(str(p) + ".tmp")
    with open(tmp, "wb") as fh:
        np.savez_compressed(fh, **arrays)
    tmp.replace(p)


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _export_one(job):
    cfg, data_dir, iid, q, cfg_sha = job
    data_dir = Path(data_dir)
    p, pp = data_dir / "inst" / f"{iid}.npz", data_dir / "pre" / f"{iid}.npz"
    t0 = time.perf_counter()
    ex, pre = export_member(cfg, q)
    _savez_atomic(pp, z=pre["z"], forces_N=np.array(pre["forces_N"]), delta=np.float64(pre["delta"]))
    _savez_atomic(p, **_pack(ex, q, cfg_sha))
    return {"id": iid, "seconds": round(time.perf_counter() - t0, 1),
            "preload": {k: pre[k] for k in ("delta", "forces_N", "converged", "on_target", "kkt", "plastic_points",
                                           "max_von_mises", "iterations")}}


def generate(cfg: dict, data_dir, splits=("train", "eval", "tested"), limit: int | None = None,
             workers: int = 1) -> Path:
    """Export every member of the given splits (each with its preload solve) and write the manifest. Resumes: a
    file already written is kept if it was made for the same member under the same configuration, and refused
    otherwise. Each worker process exports whole members; the manifest is written by this process only."""
    from .config import sha256

    cfg_sha = sha256(cfg)
    data_dir = Path(data_dir)
    for sub in ("inst", "pre"):
        (data_dir / sub).mkdir(parents=True, exist_ok=True)
    todo = [m for m in members(cfg) if m[1] in splits]
    if limit is not None:
        per = {}
        todo = [m for m in todo if per.setdefault(m[1], []).append(m) or len(per[m[1]]) <= limit]
    log_p = data_dir / "generate_log.json"
    log = {e["id"]: e for e in (json.loads(log_p.read_text()) if log_p.exists() else [])}
    jobs = []
    for iid, split, q in todo:
        p = data_dir / "inst" / f"{iid}.npz"
        if p.exists() and (data_dir / "pre" / f"{iid}.npz").exists():
            params, made_under = stored_identity(p)
            if params != asdict(q) or made_under != cfg_sha:
                raise RuntimeError(f"{p} was made for another member or configuration; use a fresh directory")
        else:
            jobs.append((cfg, str(data_dir), iid, q, cfg_sha))

    def record(e):
        log[e["id"]] = e
        _write_json_atomic(log_p, list(log.values()))
        ok = e["preload"]["converged"] and e["preload"]["on_target"]
        print(e["id"], e["seconds"], "s", "preload ok" if ok else "PRELOAD NOT ON TARGET", flush=True)

    if workers <= 1:
        for j in jobs:
            record(_export_one(j))
    else:
        import multiprocessing as mp
        with mp.get_context("fork").Pool(workers) as pool:
            for e in pool.imap_unordered(_export_one, jobs):
                record(e)
    recs = []
    for iid, split, q in todo:
        p = data_dir / "inst" / f"{iid}.npz"
        with np.load(p) as z:
            n_nodes, n_z, Tm = int(z["nodes"].shape[0]), int(z["v"].size), float(z["Theta_max"])
        recs.append({"id": iid, "split": split, "params": asdict(q), "file": f"inst/{iid}.npz",
                     "sha256": _sha256_file(p), "pre_sha256": _sha256_file(data_dir / "pre" / f"{iid}.npz"),
                     "nodes": n_nodes, "unknowns": n_z, "Theta_max": Tm,
                     "preload_ok": bool(log.get(iid, {}).get("preload", {}).get("on_target", True))})
    _write_json_atomic(data_dir / "manifest.json", {"config_sha256": cfg_sha, "n": len(recs), "instances": recs})
    return data_dir / "manifest.json"


def solve_levels(ex: dict, z_pre: np.ndarray, lam, tol: float, max_it: int) -> dict:
    """Exact solutions at the loading-device rotations lam Theta_max, in increasing order, the first from the
    preload state and each next from the previous one (deformation theory: the solution at a level does not depend
    on the path; the start only saves iterations)."""
    P = ExportedProblem(ex)
    Tm = float(ex["Theta_max"])
    lam = sorted(float(v) for v in lam)
    z, rows = z_pre, []
    for a in lam:
        r = P.solve(a * Tm, z0=z, tol=tol, max_it=max_it)
        z = r["z"]
        rows.append(r)
    out = {"lam": np.array(lam), "Theta": np.array(lam) * Tm, "z": np.stack([r["z"] for r in rows])}
    for k in ("Pi", "theta", "M", "M_sigma", "ThetaD", "w0"):
        out[k] = np.array([r[k] for r in rows])
    out["bolt_N"] = np.array([r["bolt_N"] for r in rows])
    out["plastic_points"] = np.array([r["plastic_points"] for r in rows])
    out.update(iterations=[r["iterations"] for r in rows], converged=[r["converged"] for r in rows],
               kkt=[r["kkt"] for r in rows])
    return out


def _label_one(job):
    data_dir, iid, inst_sha, pre_sha, lv, tol, max_it = job
    data_dir = Path(data_dir)
    inst, pre = data_dir / "inst" / f"{iid}.npz", data_dir / "pre" / f"{iid}.npz"
    if _sha256_file(inst) != inst_sha or _sha256_file(pre) != pre_sha:
        raise RuntimeError(f"{iid}: files differ from the manifest")
    ex, _ = load_export(inst)
    with np.load(pre) as zp:
        z_pre = zp["z"]
    t0 = time.perf_counter()
    s = solve_levels(ex, z_pre, lv, tol, max_it)
    out = data_dir / "labels" / f"{iid}.npz"
    _savez_atomic(out, **{k: s[k] for k in ("lam", "Theta", "z", "Pi", "theta", "M", "M_sigma", "ThetaD", "w0",
                                            "bolt_N", "plastic_points")})
    worst = {k: (min if k.startswith("min") else max)(r[k] for r in s["kkt"]) for k in KKT_KEYS}
    return {"id": iid, "levels": [float(v) for v in s["lam"]], "seconds": round(time.perf_counter() - t0, 2),
            "iterations": s["iterations"], "converged": s["converged"], "kkt_worst": worst,
            "M_vs_M_sigma": float(np.max(np.abs(s["M"] - s["M_sigma"]) / np.abs(s["M"]))),
            "ThetaD_last": float(s["ThetaD"][-1]), "time": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "solver": _solver(), "inst_sha256": inst_sha, "label_sha256": _sha256_file(out)}


def label(cfg: dict, data_dir, ids, workers: int = 1) -> None:
    """Solve the listed instances at their split's levels (resumes) and record each in the ledger. Each worker
    process solves whole instances; the ledger is written by this process only."""
    data_dir = Path(data_dir)
    (data_dir / "labels").mkdir(exist_ok=True)
    man = manifest(data_dir)
    rec = {r["id"]: r for r in man["instances"]}
    led_p = data_dir / "labels" / "ledger.json"
    ledger = json.loads(led_p.read_text()) if led_p.exists() else []
    done = {e["id"] for e in ledger}
    ls = cfg["data"]["label_solver"]
    jobs = [(str(data_dir), iid, rec[iid]["sha256"], rec[iid]["pre_sha256"], levels(cfg, rec[iid]["split"]),
             ls["tol"], ls["max_it"])
            for iid in ids if not (iid in done and (data_dir / "labels" / f"{iid}.npz").exists())]

    def record(e):
        nonlocal ledger
        ledger = [x for x in ledger if x["id"] != e["id"]] + [e]
        _write_json_atomic(led_p, ledger)
        print(e["id"], e["seconds"], "s", "converged" if all(e["converged"]) else "NOT CONVERGED", flush=True)

    if workers <= 1:
        for j in jobs:
            record(_label_one(j))
    else:
        import multiprocessing as mp
        with mp.get_context("fork").Pool(workers) as pool:
            for e in pool.imap_unordered(_label_one, jobs):
                record(e)


def _solver() -> str:
    from fejoint import linsolve
    return "pardiso" if linsolve._PARDISO is not None else "scipy"


def labelled_ids(cfg: dict, data_dir) -> list[str]:
    """The members that must carry labels: eval, tested, and the first n_train_labelled training members."""
    man = manifest(data_dir)
    tr = [r["id"] for r in man["instances"] if r["split"] == "train"][:cfg["data"]["n_train_labelled"]]
    return tr + [r["id"] for r in man["instances"] if r["split"] in ("eval", "tested")]


def check_files(data_dir, ids) -> None:
    data_dir = Path(data_dir)
    rec = {r["id"]: r for r in manifest(data_dir)["instances"]}
    led = {e["id"]: e for e in json.loads((data_dir / "labels" / "ledger.json").read_text())}
    for iid in ids:
        if _sha256_file(data_dir / "inst" / f"{iid}.npz") != rec[iid]["sha256"]:
            raise RuntimeError(f"instance {iid} differs from the manifest")
        e = led[iid]
        if e["inst_sha256"] != rec[iid]["sha256"] or _sha256_file(data_dir / "labels" / f"{iid}.npz") != e["label_sha256"]:
            raise RuntimeError(f"label {iid} differs from the ledger")


def load_label(data_dir, iid) -> dict:
    with np.load(Path(data_dir) / "labels" / f"{iid}.npz") as z:
        return {k: z[k] for k in z.files}


def manifest(data_dir) -> dict:
    return json.loads((Path(data_dir) / "manifest.json").read_text())


def check_labels(cfg: dict, data_dir) -> dict:
    """Every member that needs labels labelled once at its split's levels, files matching the manifest and the
    ledger, every preload on target, every level converged, the worst optimality residual of each kind within the
    configured limits, and the two moment readings of each reference (spring and stresses) equal."""
    from .config import sha256

    man = manifest(data_dir)
    split = {r["id"]: r["split"] for r in man["instances"]}
    need = labelled_ids(cfg, data_dir)
    led = json.loads((Path(data_dir) / "labels" / "ledger.json").read_text())
    by = {e["id"]: e for e in led}
    missing = [i for i in need if i not in by]
    check_files(data_dir, [i for i in need if i in by])
    lim = cfg["data"]["kkt_limits"]
    worst = {k: (min if op == ">=" else max)(e["kkt_worst"][k] for e in led) for k, (op, _) in lim.items()}
    ok_kkt = {k: bool(worst[k] >= v if op == ">=" else worst[k] <= v) for k, (op, v) in lim.items()}
    lv_ok = all(by[i]["levels"] == sorted(levels(cfg, split[i])) for i in need if i in by)
    conv = all(all(e["converged"]) for e in led)
    pre_ok = all(r["preload_ok"] for r in man["instances"])
    fe = max(e["M_vs_M_sigma"] for e in led) if led else None
    ok = (man["config_sha256"] == sha256(cfg) and not missing and lv_ok and conv and pre_ok and all(ok_kkt.values())
          and fe is not None and fe <= 1e-6)
    return {"labels": len(led), "needed": len(need), "missing": missing, "levels_ok": lv_ok, "converged": conv,
            "preload_ok": pre_ok, "worst": worst, "within_limits": ok_kkt, "max_M_vs_M_sigma": fe, "ok": bool(ok)}
