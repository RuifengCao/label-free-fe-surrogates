"""Evaluate gate G-C2.2 as pre-specified: the metrics of every seed in both readings on the fresh held-out members,
the held-out members of G-C2.1 and the tested members; the criteria on the condensed reading of the fresh held-out
members; the verdict. Writes <runs>/verdict.json.

Every metric is G-C2.1's (c2.evaluate.metrics): computed in float64 by the reference code on the exported problem,
never by the training code. A run's status comes from its files: a history.json whose status starts with
"non-finite" means a final stop; otherwise the prediction files mean finished, and their absence means missing.
A run folder that was not made under this configuration, or whose condensed reading is not the configured one, is
refused, and so are data whose sets do not have the configured sizes.
A seed that stopped enters the medians over seeds with infinite errors; a missing seed makes the verdict INCOMPLETE.
Pairs with an infinite curve error and members whose metrics fail are treated as in G-C2.1."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from c2.evaluate import _member, _summary, _quantile
from .data import manifest, check_files, pool, _write_json
from .train import PREDICTION_FILES

FILES = {"condensed": "preds_condensed.npz", "raw": "preds.npz"}
THRESHOLDS = {"C1": 0.05, "C2": 0.10}


def run_status(run: Path) -> str:
    hp = Path(run) / "history.json"
    if hp.exists() and str(json.loads(hp.read_text()).get("status", "")).startswith("non-finite"):
        return "non-finite"
    done = all((Path(run) / f).exists() for f in PREDICTION_FILES)
    return "finished" if done else "missing"


def check_run(cfg: dict, cfg_sha: str, run: Path, status: str) -> None:
    """Refuse a run folder that this configuration did not make: its history must carry the configuration's hash,
    and the condensed reading of a finished run must be the configured one at the configured levels."""
    hp = Path(run) / "history.json"
    if not hp.exists():
        raise RuntimeError(f"{run} holds predictions and no history.json; evaluate a fresh runs directory")
    hist = json.loads(hp.read_text())
    if hist.get("config_sha256") != cfg_sha:
        raise RuntimeError(f"{run} holds a run of another configuration; evaluate a fresh runs directory")
    if status == "finished":
        c = json.loads((Path(run) / "condense.json").read_text())
        rd, lv = cfg["evaluation"]["readings"]["condensed"], list(cfg["data"]["eval_levels_mm"])
        if c["reading"] != rd or c["levels_mm"] != lv:
            raise RuntimeError(f"{run} holds predictions of another reading or other levels")


def _criteria(per_seed: list[dict | None]) -> dict:
    """C1 and C2 from the per-seed summaries of one reading on the judged set (None: the seed counts as infinite)."""
    med = [float("inf") if s is None else s["abs_curve_err"]["median"] for s in per_seed]
    p90 = [float("inf") if s is None else s["abs_curve_err"]["p90"] for s in per_seed]
    c1, c2 = _quantile(med, 0.5), _quantile(p90, 0.5)
    assert not (np.isnan(c1) or np.isnan(c2)), "a criterion value is not a number"
    return {"per_seed": {"abs_curve_err_median": med, "abs_curve_err_p90": p90}, "C1_value": c1, "C2_value": c2,
            "C1": bool(c1 <= THRESHOLDS["C1"]), "C2": bool(c2 <= THRESHOLDS["C2"])}


def evaluate(cfg: dict, data_dir, runs_dir, workers: int = 1) -> dict:
    from .config import sha256

    ev = cfg["evaluation"]
    judged, judged_set = ev["readings"]["judged"], ev["judged_set"]
    readings = [judged] + list(ev["readings"]["reported"])
    cfg_sha = sha256(cfg)
    man = manifest(data_dir)
    if man["config_sha256"] != cfg_sha:
        raise RuntimeError("the data were generated under another configuration")
    split_of = {r["id"]: r["split"] for r in man["instances"]}
    ids = [i for i, s in split_of.items() if s in ev["sets"]]
    n_of = {s: sum(1 for v in split_of.values() if v == s) for s in ev["sets"]}
    d = cfg["data"]
    want = {"eval": d["n_eval"], "former": d["n_former"], "tested": len(d["tested"])}
    if n_of != {s: want[s] for s in ev["sets"]}:
        raise RuntimeError(f"the data hold {n_of} members in the evaluated sets; the configuration has {want}")
    n_levels = len(d["eval_levels_mm"])
    check_files(data_dir, ids)
    seeds = cfg["arms"]["label_free"]["seeds"]
    out = {"gate": cfg["gate"], "config_sha256": cfg_sha, "judged": {"reading": judged, "set": judged_set},
           "status": {}, "missing": [], "non_finite": [], "readings": {}}
    finished = []
    for seed in seeds:
        name = f"label_free_s{seed}"
        st = out["status"][name] = run_status(Path(runs_dir) / name)
        if st != "missing":
            check_run(cfg, cfg_sha, Path(runs_dir) / name, st)
        if st == "finished":
            finished.append(seed)
        else:
            out["missing" if st == "missing" else "non_finite"].append(name)
    preds, amplitudes = {}, {}
    for seed in finished:
        run = Path(runs_dir) / f"label_free_s{seed}"
        for reading in readings:
            with np.load(run / FILES[reading]) as z:
                preds[f"{seed}|{reading}"] = {iid: z[iid] for iid in ids}
        amplitudes[seed] = json.loads((run / "condense.json").read_text())["members"]
    jobs = [(str(data_dir), iid, {key: p[iid] for key, p in preds.items()}) for iid in sorted(ids)]
    if workers <= 1:
        results = [_member(j) for j in jobs]
    else:
        with pool(workers) as p:
            results = sorted(p.imap_unordered(_member, jobs), key=lambda r: r[0])   # the order of a single worker
    per = {key: {s: {} for s in ev["sets"]} | {"errors": {}} for key in preds}
    for iid, res in results:
        for key, rows in res.items():
            if isinstance(rows, dict):
                per[key]["errors"][iid] = rows["error"]
            else:
                per[key][split_of[iid]][iid] = rows
    for key, p in per.items():
        seed, reading = key.split("|")
        entry = {"errors": p["errors"]}
        for s in ev["sets"]:
            entry[f"{s}_rows"] = dict(sorted(p[s].items()))
            if len(p[s]) == n_of[s]:                       # a member whose metrics failed leaves the set unsummarised
                entry[s] = _summary([r for v in p[s].values() for r in v])
                pairs = entry[s]["abs_curve_err"]["n"]
                if pairs != n_of[s] * n_levels:
                    raise RuntimeError(f"{key}, set {s}: {pairs} pairs, not {n_of[s] * n_levels}")
        out["readings"].setdefault(reading, {})[seed] = entry
    for seed in finished:
        a = amplitudes[seed]
        out.setdefault("amplitudes", {})[str(seed)] = {}
        for s in ev["sets"]:                                 # the judged set and the reported ones, each on its own
            flat = lambda k: [v for iid in ids if split_of[iid] == s for v in a[iid][k]]   # noqa: E731,B023
            out["amplitudes"][str(seed)][s] = {
                "n": len(flat("a")), "min": float(min(flat("a"))), "max": float(max(flat("a"))),
                "median": float(np.median(flat("a"))), "at_bound": int(sum(flat("at_bound"))),
                "not_converged": int(sum(not c for c in flat("converged")))}
    if any(out["status"][f"label_free_s{s}"] == "missing" for s in seeds):
        out["verdict"] = "INCOMPLETE"
        out["readings"] = {"withheld": "the verdict is INCOMPLETE"}
        out.pop("amplitudes", None)
    else:
        def summaries(reading):
            return [None if out["status"][f"label_free_s{s}"] == "non-finite"
                    else out["readings"].get(reading, {}).get(str(s), {}).get(judged_set) for s in seeds]

        out.update(_criteria(summaries(judged)))
        out["verdict"] = "PASS" if (out["C1"] and out["C2"]) else "FAIL"
        out["reported_readings"] = {r: _criteria(summaries(r)) for r in ev["readings"]["reported"]}
    _write_json(Path(runs_dir) / "verdict.json", out)
    return out
