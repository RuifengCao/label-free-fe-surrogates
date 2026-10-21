#!/usr/bin/env python3
"""PREREG_K3D: the verdicts H2a-3D and H2b-3D, the reading H3-3D and the
secondary readings, from the box return of RUNBOOK_CMAME Sec. F.

    python scripts/adjudicate_k3d.py --return <return directory> \
        --out records/cmame/k3d/verdict.json

The return must hold `report.json`, `status.txt` and `provenance.txt` (and the
run logs `k3d.log*`, and `holdout_arrays.npz` when the run evaluated the
holdout set), each file the provenance file lists with its SHA-256; the commit
and tree the provenance file records must be `prereg-k3d`'s in this checkout.
PREREG_K3D.md must be stamped (its CONFIG_SHA256 line filled and its last line
its own SHA-256).

It refuses to adjudicate at all (PREREG_K3D Sec. 6) when the report is not a
guard-verified run of PREREG_K3D under its CONFIG_SHA256 line, its
configuration is not this checkout's `configs/k3d_v1.json`, it recorded another
commit than `prereg-k3d`, another source report than the records copy of
Phase-2b's, another corpus or other seeds, a row lacks one evaluation per seed
with its seed values and values for every validation instance, a stored state
did not pass its content check (as the run recorded it, and as recomputed
here from the report's arrays and the source report's), an L_K seed did not
train for every epoch on the labelled pool prefix, or a seed's or the stored
states' evaluations were made by another commit than the return's. The
verdicts read per-seed medians over the validation instances (PREREG_K3D
Sec. 4); every secondary reading is computed or recorded as not evaluated and
never blocks a verdict. The verdict file
records every input's SHA-256 and the adjudicating code's; adjudicating code
that differs from its `prereg-k3d` version is recorded as a deviation."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

LABEL = "k3d_v1"
PREREG_NAME = "PREREG_K3D.md"
TAG = "prereg-k3d"
CONFIG = Path("configs") / f"{LABEL}.json"
SOURCE = Path("records/wp8/e2/baseline/report_phase2b.json")
HOLDOUT_MANIFEST = Path("records/cmame/holdout/return/h3d/manifest.json")
"""PREREG_HOLDOUT's labels manifest of h3d as its return is committed: the
holdout labels the run used must be these (PREREG_K3D Sec. 5)."""
CM2D_VERDICT = Path("records/cmame/cm2d/verdict.json")
METRICS = ("energy_gap_rel", "disp_rel_l2", "vm_rel_l2", "peak_vm_rel_err", "crit_recall")
HIGHER_IS_BETTER = ("crit_recall",)
PRIMARY = "energy_gap_rel"
ROWS = ("ar", "labels", "labels_knorm")
NAMES = {"ar": "the label-free transformer", "labels": "the L_D transformer",
         "labels_knorm": "the stiffness-norm (L_K) transformer"}
HYPOTHESES = {"H2a-3D": ("labels_knorm", "labels", "energy_gap_rel",
                         "the stiffness-norm transformer against the L_D transformer "
                         "(reference)"),
              "H2b-3D": ("labels_knorm", "labels", "vm_rel_l2",
                         "the stiffness-norm transformer against the L_D transformer "
                         "(reference)")}
"""Verdict: (new arm A, reference B, metric, what), PREREG_K3D Sec. 4."""
H3 = ("labels_knorm", "ar", PRIMARY,
      "the stiffness-norm transformer against the label-free transformer (reference)")
PAIRS = (("labels_knorm", "labels"), ("labels_knorm", "ar"), ("ar", "labels"))
"""(A, B) of the secondary comparisons and instance pairs."""
RETURN_FILES = ("report.json", "status.txt", "provenance.txt")
HOLDOUT_ARRAYS = "holdout_arrays.npz"
TORCH = "2.12.1+cu130"
"""The torch version of the Phase-2 run that trained the L_D states (its return)."""
GPU = "NVIDIA GeForce RTX 5090"
ADJUDICATING_FILES = ("scripts/adjudicate_k3d.py", "scripts/k3d_train.py",
                      "scripts/stamp_prereg_k3d.py", "src/fejepa/analysis/adjudicate_w9.py",
                      "src/fejepa/analysis/adjudicate.py", "src/fejepa/analysis/holdout.py",
                      "src/fejepa/report.py")
"""The files whose code decides a verdict or a refusal."""
BOOT_N, BOOT_SEED = 2000, 20261020


def _script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def file_sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path) -> dict:
    return json.loads(Path(path).read_text())


def _soft(fn, *args, **kw):
    """A secondary reading: computed, or recorded as not evaluated (it never
    blocks a verdict)."""
    try:
        return fn(*args, **kw)
    except Exception as exc:                              # noqa: BLE001
        return {"not_evaluated": f"{type(exc).__name__}: {exc}"}


def jsonable(x):
    """The verdict as strict JSON: non-finite floats become strings."""
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, (float, np.floating)):
        return float(x) if math.isfinite(float(x)) else str(float(x))
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


# ------------------------------------------------------------- the values --

def cell(rep: dict, cfg: dict, row: str) -> dict:
    cells = rep.get("cells") or {}
    want = (cfg["reused"][row]["cell"] if row in cfg["reused"]
            else str(int(cfg["train"]["budget"])))
    if row not in cells or want not in cells[row]:
        raise ValueError(f"adjudication refused: the report has no {row} cell at {want}")
    return cells[row][want]


def per_instance(c: dict, metric: str) -> list:
    return [np.asarray(e["per_instance"][metric], float) for e in c["per_seed_eval"]]


def seed_medians(arrs) -> list:
    """Each seed's median over its instances; non-finite when any of its
    values is (PREREG_K3D Sec. 3)."""
    return [float(np.median(a)) if a.size and np.all(np.isfinite(a)) else float("nan")
            for a in arrs]


def seed_means(arrs) -> list:
    return [float(np.mean(a)) if a.size and np.all(np.isfinite(a)) else float("nan")
            for a in arrs]


def pool_prefix_names(n_corpus: int, n_val: int, seed: int, budget: int) -> list:
    """pool[:budget] of the run's split, by name (corpus file i is
    `instance_{i:05d}.npz` in manifest order; the split is
    `numpy.random.default_rng(seed).permutation(n_corpus)`)."""
    perm = np.random.default_rng(int(seed)).permutation(int(n_corpus))
    return [f"instance_{int(i):05d}.npz" for i in perm[int(n_val):int(n_val) + int(budget)]]


def val_names(n_corpus: int, n_val: int, seed: int) -> list:
    """The validation split in the order the run evaluates it, by name
    (perm[:n_val]; validation instance 107 is `instance_00485.npz`)."""
    perm = np.random.default_rng(int(seed)).permutation(int(n_corpus))
    return [f"instance_{int(i):05d}.npz" for i in perm[:int(n_val)]]


# ------------------------------------------------------------- refusals --

def check_report(rep: dict, cfg: dict, prereg_entries: dict | None, source: dict,
                 source_sha256: str, expected_git: str | None) -> dict:
    """Refuse a report that is not PREREG_K3D's run (ValueError); return what
    the verdicts need."""
    from fejepa.report import config_sha256

    pr = rep.get("prereg") or {}
    if pr.get("file") != PREREG_NAME or not pr.get("config_sha256"):
        raise ValueError(f"adjudication refused: the run was not guard-verified against "
                         f"{PREREG_NAME}")
    if prereg_entries is not None and pr["config_sha256"] != prereg_entries.get(LABEL):
        raise ValueError(f"adjudication refused: the run's verified hash is not "
                         f"{PREREG_NAME}'s CONFIG_SHA256[{LABEL}]")
    if rep.get("config") != cfg or config_sha256(cfg) != pr["config_sha256"]:
        raise ValueError(f"adjudication refused: the run's configuration is not {CONFIG}")
    prov = rep.get("provenance") or {}
    if expected_git is not None and prov.get("git") != expected_git:
        raise ValueError(f"adjudication refused: the run ran on {prov.get('git')!r}, "
                         f"not {expected_git!r}")
    if prov.get("source_report_sha256") != cfg["source"]["report_sha256"] or \
            source_sha256 != cfg["source"]["report_sha256"]:
        raise ValueError("adjudication refused: the run's source report is not the records "
                         "copy of Phase-2b's")
    sp = source["provenance"]["datasets"][0]
    if [d.get("manifest_sha256") for d in prov.get("datasets") or []] != [sp["manifest_sha256"]]:
        raise ValueError("adjudication refused: the run used another corpus than Phase-2b's "
                         "in-band corpus")
    seeds = [int(s) for s in cfg["seeds"]]
    if [int(s) for s in prov.get("seeds") or []] != seeds or \
            [int(s) for s in rep.get("seeds") or []] != seeds:
        raise ValueError(f"adjudication refused: the run's seeds are not {seeds}")
    n_val = int(source["config"]["split"]["n_val"])
    for row in ROWS:
        c = cell(rep, cfg, row)
        evs = c.get("per_seed_eval") or []
        if len(evs) != len(seeds):
            raise ValueError(f"adjudication refused: the {row} cell holds {len(evs)} "
                             f"evaluations, not {len(seeds)}")
        for e in evs:
            per = e.get("per_instance") or {}
            if any(not isinstance(e.get(m), (int, float)) for m in METRICS):
                raise ValueError(f"adjudication refused: the {row} cell lacks a seed value "
                                 "of a metric")
            if any(len(per.get(m) or ()) != n_val for m in METRICS):
                raise ValueError(f"adjudication refused: the {row} cell lacks values for "
                                 f"the {n_val} validation instances")
    checks = rep.get("content_checks") or {}
    keys = sorted(f"{r}_s{s}" for r in cfg["reused"] for s in seeds)
    if sorted(checks) != keys or not all((checks[k] or {}).get("ok") is True for k in keys):
        raise ValueError("adjudication refused: a stored state did not pass its content "
                         f"check ({ {k: (checks.get(k) or {}).get('ok') for k in keys} })")
    reused = rep.get("reused") or {}
    for r in cfg["reused"]:
        for s in seeds:
            if (reused.get(f"{r}_s{s}") or {}).get("sha256") != cfg["reused"][r]["sha256"][str(s)]:
                raise ValueError(f"adjudication refused: the {r} state of seed {s} is not "
                                 "the recorded one")
    again = recheck_content(rep, cfg, source, seeds)
    failed = sorted(k for k, v in again.items() if not v["ok"])
    if failed:
        raise ValueError(f"adjudication refused: the stored states {failed} do not reproduce "
                         "the source report's values (recomputed from the report's arrays)")
    tr = cfg["train"]
    names = pool_prefix_names(sp["n_instances"], n_val, source["config"]["split"]["seed"],
                              tr["budget"])
    for s in seeds:
        ps = (rep.get("per_seed") or {}).get(f"s{s}") or {}
        t = ps.get("train") or {}
        if (t.get("loss") != "knorm" or int(t.get("epochs_run", -1)) != int(tr["epochs"])
                or int(t.get("seed", -1)) != s or t.get("files") != names):
            raise ValueError(f"adjudication refused: the L_K seed {s} did not train with L_K "
                             f"for {tr['epochs']} epochs on the labelled pool prefix "
                             f"pool[:{tr['budget']}]")
        if not re.fullmatch(r"[0-9a-f]{64}", str((ps.get("state") or {}).get("sha256", ""))):
            raise ValueError(f"adjudication refused: the L_K seed {s} records no state")
    return {"seeds": seeds, "n_val": n_val, "pool_prefix": names, "content_checks": again,
            "val_names": val_names(sp["n_instances"], n_val, source["config"]["split"]["seed"])}


def recheck_content(rep: dict, cfg: dict, source: dict, seeds: list) -> dict:
    """The content check of every stored state (PREREG_K3D Sec. 3), recomputed
    from the report's cells and the source report's arrays."""
    from fejepa.analysis.holdout import content_check

    tol = float(cfg["content_tol"])
    src_seeds = [int(s) for s in source["provenance"]["seeds"]]
    src_cells = source["results"]["e8"]["metrics"]["cells"]
    out = {}
    for r in cfg["reused"]:
        ref = src_cells[r][cfg["reused"][r]["cell"]]["per_seed_eval"]
        got = cell(rep, cfg, r)["per_seed_eval"]
        for i, s in enumerate(seeds):
            out[f"{r}_s{s}"] = content_check(got[i]["per_instance"],
                                             ref[src_seeds.index(s)]["per_instance"], tol)
    return out


# ------------------------------------------------------------- verdicts --

HUGE = 1e150
"""A per-seed value beyond this counts as non-finite (PREREG_K3D Sec. 4): the
guard's exactly rounded variance overflows near 1e154."""


def _finite(v: float) -> bool:
    return math.isfinite(v) and abs(v) <= HUGE


def reading(base_vals, new_vals) -> dict:
    """The guard (PREREG_K3D Sec. 4) on two arms' per-seed values. The
    reference first: a non-finite value of it, or a mean that is not positive,
    is reported as not evaluated (not raised); then a non-finite value of the
    new arm is a divergence."""
    from fejepa.analysis.adjudicate_w9 import guard

    b = [float(v) for v in base_vals]
    a = [float(v) for v in new_vals]
    if not b or not all(_finite(v) for v in b):
        return {"not_evaluated": "the reference's per-seed values are not all finite",
                "base_per_seed": b, "new_per_seed": a}
    if not sum(b) > 0:
        return {"not_evaluated": "the reference's mean is not positive",
                "base_per_seed": b, "new_per_seed": a}
    if not a:
        return {"not_evaluated": "the new arm has no per-seed values",
                "base_per_seed": b, "new_per_seed": a}
    if not all(_finite(v) for v in a):
        return {"base_mean": float(np.mean(b)), "new_mean": None, "rel_change": None,
                "se_rel": None, "threshold": None, "lower": None, "worse": None,
                "diverged": True, "base_per_seed": b, "new_per_seed": a}
    return guard(b, a)


def _direction(r: dict) -> str:
    if r.get("diverged"):
        return "diverged"
    return "lower" if r.get("lower") else ("worse" if r.get("worse") else "neither")


def _shows(means: dict, direction: str):
    """Whether the seed means show a verdict's direction: their rel has the
    sign the verdict asserts (negative for lower, positive for worse); a
    verdict within the guard asserts none (None)."""
    if direction not in ("lower", "worse") or "not_evaluated" in means:
        return None
    if means.get("diverged"):              # the new arm's seed means diverged: worse
        return direction == "worse"
    if means.get("rel_change") is None:
        return None
    return means["rel_change"] < 0 if direction == "lower" else means["rel_change"] > 0


def median_bootstrap(base: list, new: list, n: int = BOOT_N, seed: int = BOOT_SEED,
                     level: float = 0.95) -> dict:
    """An interval for rel of the per-seed medians from resampling the
    instances, the seeds kept: per resample the same instances for both arms
    and every seed; each seed's value is its median over them, the arm's the
    mean of its seeds' values."""
    def stack(xs):
        arr = np.stack([np.asarray(x, float) for x in xs])
        if not np.all(np.isfinite(arr)):
            raise ValueError("non-finite per-instance values")
        return arr

    B, A = stack(base), stack(new)
    if B.shape[1] != A.shape[1]:
        raise ValueError("the arms' instance counts differ")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, B.shape[1], size=(n, B.shape[1]))
    vb, va = np.median(B[:, idx], axis=2), np.median(A[:, idx], axis=2)
    rel = va.mean(axis=0) / vb.mean(axis=0) - 1
    lo, hi = np.percentile(rel, [50 * (1 - level), 50 * (1 + level)])
    return {"low": float(lo), "high": float(hi), "resamples": n, "level": level}


def beside(base_arrs: list, new_arrs: list, direction: str) -> dict:
    """Beside a primary comparison (no criterion): the guard on seed means
    (PREREG_CM2D's rule) with rel's Welch interval on the seed means, rel's
    Welch interval on the medians, the instance-resampling interval of the
    medians' rel, and whether the seed means show the comparison's direction
    (the sign of their rel; `_shows`)."""
    from fejepa.analysis.adjudicate_w9 import welch_interval

    means = _soft(reading, seed_means(base_arrs), seed_means(new_arrs))
    out = {"seed_means": means,
           "seed_means_welch_95": _soft(welch_interval, seed_means(base_arrs),
                                        seed_means(new_arrs)),
           "welch_95": _soft(welch_interval, seed_medians(base_arrs), seed_medians(new_arrs)),
           "instance_resampling_95": _soft(median_bootstrap, base_arrs, new_arrs)}
    out["seed_means_show_the_direction"] = _shows(means, direction)
    return out


def verdict(base_arrs: list, new_arrs: list, what: str, metric: str) -> dict:
    r = reading(seed_medians(base_arrs), seed_medians(new_arrs))
    if "not_evaluated" in r:
        return {"verdict": "NOT EVALUATED", "reason": r["not_evaluated"],
                "comparison": what, "metric": metric, "statistic": "per-seed medians",
                "base_per_seed": r.get("base_per_seed"), "new_per_seed": r.get("new_per_seed")}
    out = {"comparison": what, "metric": metric, "statistic": "per-seed medians", **r}
    if r["diverged"]:
        out["verdict"] = "NOT SUPPORTED (diverged)"
        out["beside"] = None
        return out
    out["verdict"] = "SUPPORTED" if r["lower"] else "NOT SUPPORTED"
    if r["worse"]:
        out["note"] = "worse beyond the guard"
    out["beside"] = _soft(beside, base_arrs, new_arrs, _direction(r))
    return out


def h3_reading(ref_arrs: list, new_arrs: list) -> dict:
    a, b, metric, what = H3
    r = reading(seed_medians(ref_arrs), seed_medians(new_arrs))
    swapped = {"comparison": "the label-free transformer against the stiffness-norm "
                             "transformer (reference)",
               **reading(seed_medians(new_arrs), seed_medians(ref_arrs))}
    if "not_evaluated" in r:
        return {"reading": "NOT EVALUATED", "reason": r["not_evaluated"],
                "comparison": what, "metric": metric, "statistic": "per-seed medians",
                "base_per_seed": r.get("base_per_seed"), "new_per_seed": r.get("new_per_seed"),
                "roles_exchanged": swapped}
    if r["diverged"]:
        label = "the stiffness-norm transformer diverged"
    elif r["lower"]:
        label = "the stiffness-norm transformer lower beyond the guard"
    elif r["worse"]:
        label = "the label-free transformer lower beyond the guard"
    else:
        label = "no difference shown (within the guard)"
    return {"reading": label, "comparison": what, "metric": metric,
            "statistic": "per-seed medians", **r,
            "beside": None if r["diverged"] else _soft(beside, ref_arrs, new_arrs,
                                                       _direction(r)),
            "roles_exchanged": swapped}


# ---------------------------------------------------- secondary readings --

def _comparison(base_arrs: list, new_arrs: list, metric: str) -> dict:
    out = {}
    for stat, fn in (("medians", seed_medians), ("means", seed_means)):
        r = reading(fn(base_arrs), fn(new_arrs))
        if "not_evaluated" not in r and not r.get("diverged"):
            higher = metric in HIGHER_IS_BETTER
            r["better_direction"] = "higher" if higher else "lower"
            r["new_better_beyond_guard"] = bool(r["worse"] if higher else r["lower"])
            r["new_worse_beyond_guard"] = bool(r["lower"] if higher else r["worse"])
        out[stat] = r
    return out


def seed_table(arrays: dict) -> dict:
    """Per row and metric: per-seed medians and means, and their seed means."""
    out = {}
    for row, per in arrays.items():
        out[row] = {}
        for m, arrs in per.items():
            med, mean = seed_medians(arrs), seed_means(arrs)
            out[row][m] = {"median_per_seed": med, "mean_per_seed": mean,
                           "medians_mean": float(np.mean(med)),
                           "means_mean": float(np.mean(mean))}
    return out


def comparisons(arrays: dict) -> dict:
    """Every metric: L_K against L_D and against the label-free row, and the
    label-free row against L_D, with the guard on medians and on means."""
    return {m: {f"{a}_vs_{b}": _comparison(arrays[b][m], arrays[a][m], m) for a, b in PAIRS}
            for m in METRICS}


def pairing(arrays: dict) -> dict:
    """On how many instance-seed pairs the first network has the lower value
    (ties apart)."""
    out = {}
    for a, b in PAIRS:
        res = {}
        for m in ("energy_gap_rel", "disp_rel_l2", "vm_rel_l2"):
            X, Y = np.concatenate(arrays[a][m]), np.concatenate(arrays[b][m])
            res[m] = {"first_lower": int(np.sum(X < Y)), "ties": int(np.sum(X == Y)),
                      "pairs": int(X.size)}
        out[f"{a}_vs_{b}"] = res
    return out


def worse_than_zero(arrays: dict, seeds: list, names: list | None = None) -> dict:
    """Per row, the instance-seed values with a relative energy gap above 1
    (a prediction further from the solution, in the energy norm, than the zero
    field) and the non-finite ones: counted, and each listed with its seed,
    its validation instance (index and file) and its value."""
    out = {}
    for row, per in arrays.items():
        x = np.concatenate(per[PRIMARY])
        listed = []
        for s, a in zip(seeds, per[PRIMARY]):
            a = np.asarray(a, float)
            for i in np.flatnonzero(~(a <= 1.0)):          # above 1, or not finite
                listed.append({"seed": int(s), "instance": int(i),
                               "file": names[int(i)] if names else None,
                               "value": float(a[i])})
        out[row] = {"count": int(np.sum(x > 1.0)), "of": int(x.size),
                    "non_finite": int(np.sum(~np.isfinite(x))), "values": listed}
    return out


def labels_energy(source: dict, arrays: dict, n_val: int) -> dict:
    """L_K against the labels+energy row of the Phase-2b report (its arrays;
    its states were not kept), relative energy gap and von Mises error;
    descriptive."""
    c = source["results"]["e8"]["metrics"]["cells"]["labels_anchor"]["1024"]
    out = {}
    for m in ("energy_gap_rel", "vm_rel_l2"):
        ref = per_instance(c, m)
        if any(len(x) != n_val for x in ref):
            raise ValueError("the labels+energy arrays are not the validation split's")
        out[m] = _comparison(ref, arrays["labels_knorm"][m], m)
    return out


def gap_closure(arrays: dict) -> dict:
    """The share of the L_D transformer's excess over the label-free
    transformer that L_K removes, (L_D - L_K) / (L_D - label-free), of the
    seed-averaged medians and means; descriptive."""
    out = {}
    for m in ("vm_rel_l2", "energy_gap_rel"):
        out[m] = {}
        for stat, fn in (("medians", seed_medians), ("means", seed_means)):
            b, a, c = (float(np.mean(fn(arrays[r][m]))) for r in ("labels", "labels_knorm", "ar"))
            out[m][stat] = {"labels": b, "labels_knorm": a, "ar": c,
                            "closure": (b - a) / (b - c) if b != c else None}
    return out


def training(rep: dict, seeds: list) -> dict:
    out = {}
    for s in seeds:
        ps = rep["per_seed"][f"s{s}"]
        t = ps["train"]
        loss = [float(v) for v in t.get("loss_by_epoch") or []]
        out[f"s{s}"] = {"epochs_run": t.get("epochs_run"), "steps": t.get("steps"),
                        "loss_by_epoch": loss,
                        "loss_first_epoch": loss[0] if loss else None,
                        "loss_last_epoch": loss[-1] if loss else None,
                        "loss_min": min(loss) if loss else None,
                        "seconds": ps.get("seconds"),
                        "activation_checkpointing": t.get("activation_checkpointing"),
                        "runtime": t.get("runtime"),
                        "resumed_from_epoch": t.get("resumed_from_epoch"),
                        "from_an_earlier_attempt": bool(ps.get("from_disk")),
                        "machine": ps.get("machine")}
    return out


def cm2d_context() -> dict | None:
    """The two-dimensional results (PREREG_CM2D), for comparison; descriptive."""
    p = ROOT / CM2D_VERDICT
    if not p.is_file():
        return None
    v = load_json(p)
    return {h: {k: v[h].get(k) for k in ("verdict", "reading", "rel_change", "threshold")
                if k in v[h]} for h in ("H1", "H2a", "H2b", "H3") if h in v}


# -------------------------------------------------------------- holdout --

def holdout_names(spec_path, set_name: str) -> list:
    from fejepa.analysis.holdout import holdout_names as names, load_spec

    return names(load_spec(spec_path)["sets"][set_name])


def holdout_reading(rep: dict, cfg: dict, npz_path, seeds: list,
                    manifest_record=None, spec_path=None) -> dict:
    """The comparisons of Sec. 4 on the holdout set (no verdict), every
    metric per row and seed, and the load cases worse than the zero field."""
    h = rep.get("holdout")
    if not cfg.get("holdout"):
        return {"not_evaluated": "the configuration names no holdout set"}
    if not h or h.get("skipped"):
        return {"not_evaluated": "the run skipped the holdout set (--skip-holdout)"}
    rec = Path(manifest_record) if manifest_record is not None else ROOT / HOLDOUT_MANIFEST
    if not rec.is_file():
        return {"not_evaluated": f"{HOLDOUT_MANIFEST} is not committed: the labels the run "
                                 "used cannot be compared with PREREG_HOLDOUT's return"}
    if h.get("labels_manifest_sha256") != file_sha256(rec):
        return {"not_evaluated": "the run's holdout labels manifest is not PREREG_HOLDOUT's "
                                 f"returned one ({str(h.get('labels_manifest_sha256'))[:12]}..., "
                                 f"recorded {file_sha256(rec)[:12]}...)"}
    if npz_path is None or not Path(npz_path).is_file():
        return {"not_evaluated": f"the return holds no {HOLDOUT_ARRAYS}"}
    if file_sha256(npz_path) != h.get("arrays_sha256"):
        return {"not_evaluated": f"{HOLDOUT_ARRAYS} is not the run's (SHA-256)"}
    z = np.load(npz_path, allow_pickle=False)
    rows, sds = [str(r) for r in z["rows"]], [int(s) for s in z["seeds"]]
    mets = [str(m) for m in z["metrics"]]
    files = [str(f) for f in z["files"]]
    if rows != list(ROWS) or sds != seeds or sorted(mets) != sorted(METRICS):
        return {"not_evaluated": "the holdout arrays' rows, seeds or metrics are not the run's"}
    want = holdout_names(spec_path or ROOT / cfg["holdout"]["spec"], cfg["holdout"]["set"])
    if files != want:
        return {"not_evaluated": "the holdout arrays do not list the holdout set in pool order"}
    M = z["values"]
    arrays = {r: {m: [M[i, j, :, mets.index(m)] for j in range(len(seeds))] for m in METRICS}
              for i, r in enumerate(ROWS)}
    hyps = {}
    for name, (a, b, metric, what) in {**HYPOTHESES, "H3-3D": H3}.items():
        r = reading(seed_medians(arrays[b][metric]), seed_medians(arrays[a][metric]))
        rm = reading(seed_means(arrays[b][metric]), seed_means(arrays[a][metric]))
        hyps[name] = {"comparison": what, "metric": metric, "medians": r, "means": rm,
                      "direction": None if "not_evaluated" in r else _direction(r),
                      "means_direction": None if "not_evaluated" in rm else _direction(rm)}
    G, P = z["gap_load"], z["pi_load"]
    from fejepa.analysis.holdout import worse_than_zero as wtz

    worse = {f"{r}_s{s}": wtz(G[i, j], P[i, j]) for i, r in enumerate(ROWS)
             for j, s in enumerate(seeds)}
    return {"n": len(files), "hypotheses": hyps, "seed_table": seed_table(arrays),
            "worse_than_zero_load_cases": worse}


# ------------------------------------------------------------ deviations --

def status_attempts(status_text: str | None) -> dict:
    """The run's attempts in the status file: the start lines
    (`k3d.log start <time> ...`) and the exit codes (`k3d.log exit=N`)."""
    t = status_text or ""
    return {"starts": len(re.findall(r"^k3d\.log start\b", t, re.M)),
            "exits": [int(m.group(1)) for m in
                      re.finditer(r"^k3d\.log exit=(-?\d+)\s*$", t, re.M)]}


MACHINE_FIELDS = ("host", "cpu", "gpu_driver", "gpu_uuid")


def _machines_differ(ms: list) -> bool:
    """Two records name different machines when they differ in a field that
    both record (a field not read, None, is not a difference)."""
    for f in MACHINE_FIELDS:
        if len({m.get(f) for m in ms if m.get(f) is not None}) > 1:
            return True
    return False


def _block(text: str, name: str) -> list:
    """The lines of the provenance file's `--- name ---` block."""
    parts = re.split(r"^--- (.+?) ---\s*$", text or "", flags=re.M)
    for i in range(1, len(parts) - 1, 2):
        if parts[i].strip() == name:
            return [x for x in parts[i + 1].splitlines() if x.strip()]
    return []


def return_deviations(rep: dict, seeds: list, prov_text: str | None, ret: Path | None) -> list:
    """The return against the report: the states the box hashed, the files
    moved aside under runs/k3d, the seed result files."""
    out = []
    if prov_text is not None:
        listed = {}
        for line in _block(prov_text, "states"):
            m = re.match(r"^([0-9a-f]{64})\s+\*?(\S+)$", line.strip())
            if m:
                listed[Path(m.group(2)).name] = m.group(1)
        for s in seeds:
            name = Path(str(rep["per_seed"][f"s{s}"]["state"].get("path", ""))).name
            if listed.get(name) != rep["per_seed"][f"s{s}"]["state"]["sha256"]:
                out.append(f"L_K seed {s}: the state on the box ({name}) is not the one the "
                           "report records (provenance.txt, --- states ---)")
        aside = sorted({x.split()[-1] for x in _block(prov_text, "runs/k3d")
                        if ".unusable." in x})
        if aside:
            out.append(f"files moved aside under runs/k3d: {aside}")
    if ret is not None:
        if (rep.get("holdout") or {}).get("skipped"):
            before = sorted(Path(ret).glob("k3d.log.*"))[-2:]
            failed = [f.name for f in before
                      if any(re.search(r"in holdout_(evaluation|instances)$", x)
                             for x in f.read_text(errors="replace").splitlines()[-60:])]
            if len(failed) < 2:
                out.append("the holdout set was skipped without two consecutive failures of "
                           "its evaluation before it (the last two earlier run logs: "
                           f"{[f.name for f in before]}, ending in a holdout traceback: "
                           f"{failed})")
        if not (Path(ret) / "reused.json").is_file():
            out.append("the return holds no reused.json (the stored states' evaluations not "
                       "compared with the return's commit)")
        for s in seeds:
            f = Path(ret) / f"seed_{s}.json"
            if not f.is_file():
                out.append(f"the return holds no seed_{s}.json")
                continue
            prev = load_json(f)
            ps = rep["per_seed"][f"s{s}"]
            same = (prev.get("commit") == ps.get("commit")
                    and (prev.get("state") or {}).get("sha256") == ps["state"]["sha256"]
                    and (prev.get("train") or {}).get("epochs_run") == ps["train"]["epochs_run"])
            if not same:
                out.append(f"seed_{s}.json is not the report's record of seed {s}")
    return out


def deviations(rep: dict, cfg: dict, seeds: list, status_text: str | None,
               run_logs: int | None = None, content_checks: dict | None = None,
               tf32: bool | None = None) -> list:
    out = []
    for k, c in sorted((content_checks or {}).items()):
        over = [m for m in ("energy_gap_rel", "disp_rel_l2", "vm_rel_l2", "peak_vm_rel_err",
                            "crit_recall")
                if not c.get(f"{m}_max_rel_dev", 0.0) <= float(cfg["content_tol"])]
        if over:
            out.append(f"stored state {k}: largest relative deviation above content_tol in "
                       f"{over}")
    if rep.get("reused_evaluations_from_disk"):
        out.append("the stored states' evaluations were taken from an earlier attempt "
                   "(reused.json)")
    hosts = []
    for s in seeds:
        ps = rep["per_seed"][f"s{s}"]
        t = ps["train"]
        if ps.get("from_disk"):
            out.append(f"L_K seed {s}: taken from an earlier attempt (seed_{s}.json)")
        if t.get("resumed_from_epoch") is not None:
            out.append(f"L_K seed {s}: resumed from its epoch checkpoint at epoch "
                       f"{t['resumed_from_epoch']}")
        if bool(t.get("activation_checkpointing")) != bool(cfg["train"]
                                                           ["activation_checkpointing"]):
            out.append(f"L_K seed {s}: activation checkpointing "
                       f"{'on' if t.get('activation_checkpointing') else 'off'}, the "
                       "configuration's is the other")
        rt = t.get("runtime")
        if tf32 is not None and isinstance(rt, dict) and bool(rt.get("tf32_matmul")) != tf32:
            out.append(f"L_K seed {s}: TF32 matmul {'on' if rt.get('tf32_matmul') else 'off'} "
                       f"in training, the source run's policy is "
                       f"{'on' if tf32 else 'off'}")
        mach = ps.get("machine") or {}
        seq = [m for m in (mach.get("start"), *(mach.get("resumed_on") or []), mach.get("end"))
               if isinstance(m, dict)]
        if _machines_differ(seq):
            out.append(f"L_K seed {s}: trained on more than one machine "
                       f"({[[m.get(f) for f in MACHINE_FIELDS] for m in seq]})")
        if seq and all(m.get("gpu_driver") is None for m in seq):
            out.append(f"L_K seed {s}: its GPU driver was not read")
        tv = (ps.get("torch") or {})
        if "version" in tv and (tv.get("version") != TORCH or tv.get("gpu") != GPU):
            out.append(f"L_K seed {s}: trained under torch {tv.get('version')!r} on "
                       f"{tv.get('gpu')!r}")
        hosts.extend(seq)
    if _machines_differ(hosts):
        out.append("the seeds ran on more than one machine")
    torch_v = (rep.get("torch") or {}).get("version")
    if torch_v != TORCH:
        out.append(f"torch {torch_v!r}; the L_D states were trained with {TORCH!r}")
    gpu = (rep.get("gpu") or {}).get("gpu")
    if gpu != GPU:
        out.append(f"GPU {gpu!r}; the L_D states were trained on {GPU!r}")
    if (rep.get("holdout") or {}).get("skipped"):
        out.append("the holdout set was skipped (--skip-holdout)")
    if status_text is not None:
        att = status_attempts(status_text)
        if att["starts"] != 1 or att["exits"] != [0]:
            out.append(f"run attempts in the status file: {att['starts']} started, "
                       f"exit codes {att['exits']}")
    if run_logs is not None and run_logs != 1:
        out.append(f"{run_logs} run logs in the return (one per attempt)")
    return out


# --------------------------------------------------------------- the lot --

def check_commits(rep: dict, seeds: list, prov_text: str | None, ret: Path | None) -> None:
    """Every seed's training, and the stored states' evaluations, made by the
    commit the return records (ValueError)."""
    if prov_text is None:
        return
    head = provenance_commit(prov_text)["HEAD"]
    if rep["provenance"].get("commit") != head:
        raise ValueError("adjudication refused: the report was written by another commit "
                         "than the return's")
    for s in seeds:
        if rep["per_seed"][f"s{s}"].get("commit") != head:
            raise ValueError(f"adjudication refused: L_K seed {s} was trained by another "
                             "commit than the return's")
    if ret is not None and (Path(ret) / "reused.json").is_file() and \
            load_json(Path(ret) / "reused.json").get("commit") != head:
        raise ValueError("adjudication refused: the stored states were evaluated by another "
                         "commit than the return's")


def adjudicate_k3d(rep: dict, cfg: dict, prereg_entries: dict | None, source: dict,
                   source_sha256: str, expected_git: str | None,
                   status_text: str | None = None, run_logs: int | None = None,
                   holdout_npz=None, holdout_manifest=None, holdout_spec=None,
                   prov_text: str | None = None, ret=None) -> dict:
    """PREREG_K3D Sec. 4-6 on one report. Raises ValueError on a refusal."""
    g = check_report(rep, cfg, prereg_entries, source, source_sha256, expected_git)
    check_commits(rep, g["seeds"], prov_text, ret)
    arrays = {r: {m: per_instance(cell(rep, cfg, r), m) for m in METRICS} for r in ROWS}
    out = {"what": "PREREG_K3D verdicts (scripts/adjudicate_k3d.py)",
           "budget": int(cfg["train"]["budget"]), "statistic": "per-seed medians"}
    for h, (a, b, metric, what) in HYPOTHESES.items():
        out[h] = verdict(arrays[b][metric], arrays[a][metric], what, metric)
    out["H3-3D"] = h3_reading(arrays["ar"][PRIMARY], arrays["labels_knorm"][PRIMARY])
    out["content_checks"] = {"recorded": rep["content_checks"],
                             "recomputed": g["content_checks"]}
    out["secondary"] = {
        "seed_table": _soft(seed_table, arrays), "comparisons": _soft(comparisons, arrays),
        "pairing": _soft(pairing, arrays), "worse_than_zero": _soft(worse_than_zero, arrays, g["seeds"], g["val_names"]),
        "labels_energy": _soft(labels_energy, source, arrays, g["n_val"]),
        "gap_closure": _soft(gap_closure, arrays),
        "holdout": _soft(holdout_reading, rep, cfg, holdout_npz, g["seeds"],
                         holdout_manifest, holdout_spec),
        "training": _soft(training, rep, g["seeds"]), "cm2d": _soft(cm2d_context)}
    hold = out["secondary"]["holdout"]
    if isinstance(hold, dict) and "hypotheses" in hold:
        for h in (*HYPOTHESES, "H3-3D"):
            key = "verdict" if h in HYPOTHESES else "reading"
            val = out[h]
            d = None if "rel_change" not in val else _direction(val)
            hh = hold["hypotheses"][h]
            hh["validation_direction"] = d
            hh["same_direction"] = (None if d is None or hh["direction"] is None
                                    else hh["direction"] == d)
            hh["means_same_direction"] = (None if d is None or hh["means_direction"] is None
                                          else hh["means_direction"] == d)
            hold["hypotheses"][h]["validation_" + key] = val.get(key)
    hold_dev = []
    if cfg.get("holdout") and isinstance(rep.get("holdout"), dict) \
            and not rep["holdout"].get("skipped") and isinstance(hold, dict) \
            and "not_evaluated" in hold:
        hold_dev.append(f"the holdout readings are not evaluated: {hold['not_evaluated']}")
    out["deviations"] = (deviations(rep, cfg, g["seeds"], status_text, run_logs,
                                    g["content_checks"],
                                    bool(source["config"].get("tf32", True)))
                         + return_deviations(rep, g["seeds"], prov_text, ret) + hold_dev)
    out["run"] = {"git": rep["provenance"].get("git"),
                  "config_sha256": rep["provenance"].get("config_sha256"),
                  "torch": (rep.get("torch") or {}).get("version"),
                  "gpu": (rep.get("gpu") or {}).get("gpu"),
                  "runtime_policy": rep.get("runtime_policy")}
    return out


# -------------------------------------------------------------- inputs --

def prereg_hash(path) -> dict:
    """The stamped entries of PREREG_K3D.md; refuses an unstamped file or one
    whose last line is not its own SHA-256."""
    from fejepa.report import PREREG_PLACEHOLDER, read_prereg_entries

    entries = dict(read_prereg_entries(path))
    if entries.get(LABEL) in (None, PREREG_PLACEHOLDER):
        raise SystemExit(f"{path}: not stamped")
    if not _script("stamp_prereg_k3d").self_hash_ok(Path(path).read_text(encoding="utf-8")):
        raise SystemExit(f"{path}: its last line is not its own SHA-256")
    return entries


def provenance_files(text: str) -> dict:
    """{relative path: SHA-256} of the files the provenance file lists (the
    `--- files ---` block: `sha256sum` lines over the return)."""
    out = {}
    block = text.split("--- files ---", 1)
    for line in (block[1] if len(block) == 2 else "").splitlines():
        m = re.match(r"^([0-9a-f]{64})\s+\*?(?:\./)?(\S+)$", line.strip())
        if m:
            out[m.group(2)] = m.group(1)
    return out


def provenance_commit(text: str) -> dict:
    """The `HEAD <sha>` and `tree <sha>` lines of the provenance file."""
    out = {}
    for key in ("HEAD", "tree"):
        m = re.search(rf"^{key} ([0-9a-f]{{40}})\s*$", text, re.M)
        out[key] = m.group(1) if m else None
    return out


def _git(*args) -> str | None:
    try:
        p = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True,
                           timeout=30)
        return p.stdout.strip() if p.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def check_commit(prov_text: str, tag: str = TAG) -> str | None:
    """Refuse a return whose recorded commit or tree is not `tag`'s in this
    checkout (SystemExit); return a deviation note when the tag is absent."""
    rec = provenance_commit(prov_text)
    want = {"HEAD": _git("rev-parse", "--verify", "--quiet", f"{tag}^{{commit}}"),
            "tree": _git("rev-parse", "--verify", "--quiet", f"{tag}^{{tree}}")}
    if want["HEAD"] is None:
        return f"the run's commit not compared with {tag} (no such tag in this checkout)"
    if rec != want:
        raise SystemExit(f"the return records HEAD {rec['HEAD']} and tree {rec['tree']}, "
                         f"{tag} is {want['HEAD']} with tree {want['tree']}")
    return None


def load_return(ret: Path) -> tuple:
    """The return's report, its SHA-256, status and provenance text and run
    logs; every file in the return must be listed in the provenance file
    with its SHA-256, and every listed file must be there."""
    missing = [f for f in RETURN_FILES if not (ret / f).is_file()]
    if missing:
        raise SystemExit(f"{ret}: the return lacks {missing} (RUNBOOK_CMAME Sec. F)")
    prov = (ret / "provenance.txt").read_text()
    listed = provenance_files(prov)
    present = sorted(p.relative_to(ret).as_posix() for p in ret.rglob("*")
                     if p.is_file() and p.name != "provenance.txt")
    if sorted(listed) != present:
        raise SystemExit(f"{ret}: the files are not those the provenance file lists "
                         f"(listed only: {sorted(set(listed) - set(present))}; present only: "
                         f"{sorted(set(present) - set(listed))})")
    bad = [f for f, h in listed.items() if file_sha256(ret / f) != h]
    if bad:
        raise SystemExit(f"{ret}: {bad} are not the files the box hashed")
    logs = sorted(p.name for p in ret.glob("k3d.log*"))
    return (load_json(ret / "report.json"), listed["report.json"],
            (ret / "status.txt").read_text(), prov, logs)


def code_against(ref: str) -> dict:
    """The adjudicating files in this checkout against their versions at `ref`."""
    out = {"ref": ref, "compared": False, "differs": []}
    try:
        ok = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet",
                             f"{ref}^{{commit}}"], capture_output=True, timeout=10).returncode == 0
        if not ok:
            out["note"] = f"no {ref} in this checkout"
            return out
        for p in ADJUDICATING_FILES:
            rc = subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", ref, "--", p],
                                capture_output=True, timeout=30).returncode
            if rc == 1:
                out["differs"].append(p)
            elif rc != 0:
                raise RuntimeError(f"git diff exited {rc} on {p}")
        out["compared"] = True
    except Exception as exc:                              # noqa: BLE001
        out["differs"] = []
        out["note"] = f"comparison failed ({type(exc).__name__}: {exc})"
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--return", dest="ret", required=True, help="the return directory")
    ap.add_argument("--prereg", default=str(ROOT / PREREG_NAME))
    ap.add_argument("--config", default=str(ROOT / CONFIG))
    ap.add_argument("--source-report", default=str(ROOT / SOURCE))
    ap.add_argument("--expected-git", default=TAG, help="the git describe the run must record")
    ap.add_argument("--code-ref", default=TAG,
                    help="the commit the adjudicating code is compared with")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    entries = prereg_hash(a.prereg)
    ret = Path(a.ret)
    rep, rep_sha, status, prov, logs = load_return(ret)
    commit_note = check_commit(prov, a.expected_git)
    cfg = load_json(a.config)
    source = load_json(a.source_report)
    npz = ret / HOLDOUT_ARRAYS
    try:
        res = adjudicate_k3d(rep, cfg, entries, source, file_sha256(a.source_report),
                             a.expected_git, status, len(logs),
                             holdout_npz=npz if npz.is_file() else None,
                             prov_text=prov, ret=ret)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if commit_note:
        res["deviations"].append(commit_note)
    res["inputs"] = {
        "return": {f: {"path": str(ret / f), "sha256": h}
                   for f, h in sorted(provenance_files(prov).items())},
        "provenance": {"path": str(ret / "provenance.txt"),
                       "sha256": file_sha256(ret / "provenance.txt")},
        "recorded_commit": provenance_commit(prov),
        "report_sha256": rep_sha,
        "config": {"path": a.config, "sha256": file_sha256(a.config)},
        "source_report": {"path": a.source_report, "sha256": file_sha256(a.source_report)},
        "prereg": {"path": a.prereg, "sha256": file_sha256(a.prereg)},
        "holdout_manifest": ({"path": str(ROOT / HOLDOUT_MANIFEST),
                              "sha256": file_sha256(ROOT / HOLDOUT_MANIFEST)}
                             if (ROOT / HOLDOUT_MANIFEST).is_file() else None),
        **{k: ({"path": str(ROOT / v), "sha256": file_sha256(ROOT / v)}
               if (ROOT / v).is_file() else None)
           for k, v in (("holdout_spec", Path(cfg["holdout"]["spec"]) if cfg.get("holdout")
                         else Path("configs/holdout_v1.json")),
                        ("cm2d_verdict", CM2D_VERDICT))}}
    code = code_against(a.code_ref)
    res["adjudicator"] = {"sha256": {p: file_sha256(ROOT / p) for p in ADJUDICATING_FILES},
                          "against_stamp": code}
    if not code["compared"]:
        res["deviations"].append(f"adjudicating code not compared with {a.code_ref} "
                                 f"({code.get('note')})")
    elif code["differs"]:
        res["deviations"].append(f"adjudicating code differs from {a.code_ref} in "
                                 f"{code['differs']} (its SHA-256 under adjudicator)")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(jsonable(res), indent=1, allow_nan=False) + "\n")
    print(json.dumps({h: res[h]["verdict"] for h in HYPOTHESES} | {
        "H3-3D": res["H3-3D"]["reading"], "deviations": res["deviations"]}, indent=1))


if __name__ == "__main__":
    main()
