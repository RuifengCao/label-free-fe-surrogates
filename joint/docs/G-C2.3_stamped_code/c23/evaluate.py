"""Evaluate gate G-C2.3 as pre-specified, in two steps.

evaluate_arm  the metrics of one arm's runs on every evaluated member, written to <runs>/rows_<arm>.json with the
              SHA-256 of the files they were computed from. This is the long step (an exact solve for every
              prediction), and each arm needs it once: the label-free arm before the supervised arm is trained.
verdict       the identity check, part 1 and part 2 from the rows files, written to <runs>/verdict.json. It computes
              no metric, takes seconds, and refuses rows that were computed from other files than those now present.
              The first verdict in which part 1 is decided is also kept, whole, in <runs>/verdict_part1.json, which
              is never overwritten: part 1 is final there. That file is written only while no training member has a
              label and the supervised arm has not been evaluated. Every later verdict says whether its part 1 is
              the one kept.

Every metric is G-C2.1's (c2.evaluate.metrics): computed in float64 by the reference code on the exported problem,
never by the training code. To each (member, level) row the prediction's own point is added: its end displacement e
and its spring force F = 4 k_s (D - e), read from the predicted field alone.

identity    the label-free runs must reproduce G-C2.2's judged values on G-C2.2's fresh members; otherwise INVALID,
            also when a value cannot be computed (a run without finite predictions, a member without metrics).
part 1      the self-check: the spread of F over the three label-free runs against the fixed threshold, the flagged
            pairs against the judged error (S1, S2, S3), and the ranking R.
part 2      the comparison of the supervised arm with the label-free arm in the judged reading on the fresh members.

A run's status comes from its files, as in G-C2.2 (c22.evaluate.run_status); a run folder that was not made under
this configuration, or whose condensed reading is not the configured one, is refused."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from c2.data import load_export, load_label
from c2.evaluate import metrics, _summary, _quantile
from c2.instance import ExportedProblem
from c22.evaluate import run_status, check_run, FILES
from .data import manifest, check_files, ledger_sha256, pool, _write_json

LABEL_FREE, SUPERVISED = "label_free", "supervised_512"
ABOVE = (0.05, 0.10)


def _member(job):
    """All metrics of one member (as c2.evaluate._member), with each prediction's own e and F added to its rows."""
    data_dir, iid, preds = job
    ex, _ = load_export(Path(data_dir) / "inst" / f"{iid}.npz")
    ref = load_label(data_dir, iid)
    P = ExportedProblem(ex)
    ref_pl = [P.evaluate(ref["z"][l], float(ref["D"][l]))["plastic"] for l in range(ref["D"].size)]
    out = {}
    for run, Z in preds.items():
        try:
            rows = []
            for l in range(ref["D"].size):
                r = metrics(P, ex, Z[l], ref, ref_pl[l], l)
                e = float(np.asarray(Z[l], dtype=np.float64)[P.e_idx])
                r["e"], r["F"] = e, 4.0 * P.k_s * (float(ref["D"][l]) - e)
                rows.append(r)
            out[run] = rows
        except Exception as err:                           # a prediction the reference code cannot evaluate
            out[run] = {"error": f"{type(err).__name__}: {err}"}
    return iid, out


def _stats(per_seed: list[dict | None]) -> dict:
    """The two statistics of one arm and reading on one set, from the per-seed summaries (None: an infinite seed)."""
    med = [float("inf") if s is None else s["abs_curve_err"]["median"] for s in per_seed]
    p90 = [float("inf") if s is None else s["abs_curve_err"]["p90"] for s in per_seed]
    return {"per_seed": {"abs_curve_err_median": med, "abs_curve_err_p90": p90},
            "C1_value": _quantile(med, 0.5), "C2_value": _quantile(p90, 0.5)}


def auc(score, positive) -> float | None:
    """The probability that a positive pair has the larger score than a negative one, ties counting half.
    None when there is no positive or no negative pair."""
    score, positive = np.asarray(score, dtype=float), np.asarray(positive, dtype=bool)
    n1 = int(positive.sum())
    n0 = positive.size - n1
    if n1 == 0 or n0 == 0:
        return None
    order = np.argsort(score, kind="stable")
    ranks = np.empty(score.size)
    s = score[order]
    i = 0
    while i < s.size:                                      # mean ranks over ties
        j = i
        while j + 1 < s.size and s[j + 1] == s[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return float((ranks[positive].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def self_check(sc: dict, rows_by_seed: dict, ids: list[str]) -> dict:
    """The spread of the spring force over the runs, the flags, and S1, S2, S3 and R for one set and reading.
    rows_by_seed: seed -> {member: its rows}. The same function gives the reported values on the other sets."""
    seeds = list(rows_by_seed)
    F = np.array([[[r["F"] for r in rows_by_seed[s][i]] for i in ids] for s in seeds], dtype=float)
    err = np.array([[[r["abs_curve_err"] for r in rows_by_seed[s][i]] for i in ids] for s in seeds], dtype=float)
    den = np.abs(np.median(F, axis=0))
    with np.errstate(divide="ignore", invalid="ignore"):
        spread = np.where(den > 0, (F.max(axis=0) - F.min(axis=0)) / den, np.inf)
    flag = spread >= sc["threshold"]
    n = int(flag.size)
    un = err[:, ~flag]                                      # runs x pairs that are not flagged
    above10_pairs = int((un > 0.10).any(axis=0).sum())
    share05 = float((un > 0.05).mean()) if un.size else 0.0
    out = {"threshold": sc["threshold"], "runs": [str(s) for s in seeds], "pairs": n, "flagged": int(flag.sum()),
           "flagged_share": float(flag.mean()),
           "not_flagged_pairs_above_0.10_in_any_run": above10_pairs,
           "not_flagged_readings": int(un.size), "not_flagged_readings_above_0.05": int((un > 0.05).sum()),
           "not_flagged_share_above_0.05": share05,
           "largest_error_not_flagged": [float(u.max()) if u.size else None for u in un],
           "pairs_above": {str(t): {"total": [int((e > t).sum()) for e in err],
                                    "flagged": [int((e[flag] > t).sum()) for e in err]} for t in ABOVE},
           "spread_quantiles": {q: float(np.quantile(spread[np.isfinite(spread)], float(q)))
                                for q in ("0.5", "0.75", "0.9")} if np.isfinite(spread).any() else {},
           "spread_max": float(spread.max()),
           "S1": above10_pairs == 0, "S2": share05 <= 0.01, "S3": float(flag.mean()) <= 0.35}
    out["verdict"] = "PASS" if (out["S1"] and out["S2"] and out["S3"]) else "FAIL"
    aucs = [auc(spread.ravel(), (e > 0.05).ravel()) for e in err]
    have = [a for a in aucs if a is not None]
    out["ranking"] = {"auc_above_0.05": aucs, "auc_above_0.10": [auc(spread.ravel(), (e > 0.10).ravel()) for e in err],
                      "R": "NOT EVALUABLE" if not have else ("HOLDS" if min(have) >= 0.90 else "DOES NOT HOLD")}
    out["by_member"] = {i: {"spread": [float(v) for v in spread[k]], "flagged": [bool(v) for v in flag[k]]}
                        for k, i in enumerate(ids)}
    return out


def compare(band, sup: dict, lf: dict) -> dict:
    """Part 2: the ratios supervised over label-free of the two statistics, and the wording they allow."""
    lo, hi = band
    with np.errstate(divide="ignore", invalid="ignore"):
        r = [float(np.float64(sup[k]) / np.float64(lf[k])) for k in ("C1_value", "C2_value")]
    if any(np.isnan(x) for x in r):
        word = "NOT COMPARABLE"
    elif all(lo <= x <= hi for x in r):
        word = "comparable"
    elif all(x < 1 for x in r):
        word = "supervised closer"
    elif all(x > 1 for x in r):
        word = "label-free closer"
    else:
        word = "mixed"
    return {"ratio_of_medians": r[0], "ratio_of_p90": r[1], "band": [lo, hi], "wording": word}


def identity(a: dict, recomputed: dict) -> dict:
    """The label-free runs against G-C2.2's judged values on G-C2.2's fresh members (per seed, both readings).
    Two values that are equal count as equal also when both are infinite, as in a host check's stand-in values; any
    other difference that is not a number counts as infinite."""
    worst = 0.0
    for reading, want in a["identity"]["values"].items():
        for k, v in want.items():
            got, ref = np.asarray(recomputed[reading]["per_seed"][k], dtype=float), np.asarray(v, dtype=float)
            with np.errstate(invalid="ignore"):
                diff = np.where(got == ref, 0.0, np.abs(got - ref))          # equal infinite values are equal
            worst = max(worst, float(np.max(np.where(np.isnan(diff), np.inf, diff))))
    return {"largest_difference": worst, "tolerance": a["identity"]["tolerance"],
            "ok": bool(worst <= a["identity"]["tolerance"])}


def _sha(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _inputs(cfg: dict, data_dir, runs_dir, arm: str) -> dict:
    """What the rows of an arm depend on: the manifest, the ledger entries of the evaluated members (each pins its
    instance file and its label file), and each run's status and prediction files. The ledger file as a whole is not
    among them: the entries of the training members are added after the label-free arm has been evaluated."""
    runs = {}
    for seed in cfg["arms"][arm]["seeds"]:
        name = f"{arm}_s{seed}"
        st = run_status(Path(runs_dir) / name)
        runs[name] = {"status": st}
        if st == "finished":
            runs[name].update({f: _sha(Path(runs_dir) / name / f) for f in sorted(FILES.values())})
    sets = cfg["evaluation"]["sets"]
    sha, n = ledger_sha256(data_dir, [r["id"] for r in manifest(data_dir)["instances"] if r["split"] in sets])
    return {"manifest_sha256": _sha(Path(data_dir) / "manifest.json"), "evaluated_labels": n,
            "evaluated_labels_sha256": sha, "runs": runs}


def _sets(cfg: dict, man: dict):
    """The evaluated members by set, after checking that the data hold the configured sets."""
    ev, d = cfg["evaluation"], cfg["data"]
    split_of = {r["id"]: r["split"] for r in man["instances"]}
    n_of = {s: sum(1 for v in split_of.values() if v == s) for s in ev["sets"]}
    want = {"third": d["n_third"], "eval": d["n_eval"], "tested": len(d["tested"])}
    if n_of != {s: want[s] for s in ev["sets"]}:
        raise RuntimeError(f"the data hold {n_of} members in the evaluated sets; the configuration has {want}")
    return split_of, n_of


def evaluate_arm(cfg: dict, data_dir, runs_dir, arm: str, workers: int = 1) -> dict:
    """The metrics of every finished run of one arm, in both readings, on every evaluated member."""
    from .config import sha256

    ev = cfg["evaluation"]
    readings = [ev["readings"]["judged"]] + list(ev["readings"]["reported"])
    cfg_sha = sha256(cfg)
    man = manifest(data_dir)
    if man["config_sha256"] != cfg_sha:
        raise RuntimeError("the data were generated under another configuration")
    split_of, n_of = _sets(cfg, man)
    ids = [i for i, s in split_of.items() if s in ev["sets"]]
    n_levels = len(cfg["data"]["eval_levels_mm"])
    check_files(data_dir, ids)
    out = {"gate": cfg["gate"], "config_sha256": cfg_sha, "arm": arm, "inputs": _inputs(cfg, data_dir, runs_dir, arm),
           "runs": {}, "readings": {}}
    if all(r["status"] == "missing" for r in out["inputs"]["runs"].values()):
        raise RuntimeError(f"no run of the arm {arm} has ended: there is nothing to evaluate, and no rows are written")
    labels_now = (ledger_sha256(data_dir, [i for i, s in split_of.items() if s == "train"])[0]
                  if arm == SUPERVISED else None)
    finished = []
    for seed in cfg["arms"][arm]["seeds"]:
        name = f"{arm}_s{seed}"
        st = out["inputs"]["runs"][name]["status"]
        if st != "missing":
            check_run(cfg, cfg_sha, Path(runs_dir) / name, st)
            h = json.loads((Path(runs_dir) / name / "history.json").read_text())
            if arm == SUPERVISED and h.get("training_labels_sha256") != labels_now:
                raise RuntimeError(f"{name} was trained on other labels than those now in the ledger")
            out["runs"][name] = {k: h[k] for k in ("status", "steps", "total_steps", "reference_solutions",
                                                   "training_labels_sha256", "peak_memory_GiB", "trained_in",
                                                   "predict_seconds", "torch", "gpu", "resumes") if k in h}
            if "epoch_seconds" in h:
                out["runs"][name].update(training_seconds=float(sum(h["epoch_seconds"])),
                                         cap_events=len(h["cap_events"]), bursts=len(h["bursts"]))
        if st == "finished":
            finished.append(seed)
    preds = {}
    for seed in finished:
        for reading in readings:
            with np.load(Path(runs_dir) / f"{arm}_s{seed}" / FILES[reading]) as z:
                preds[f"{seed}|{reading}"] = {iid: z[iid] for iid in ids}
    jobs = [(str(data_dir), iid, {key: p[iid] for key, p in preds.items()}) for iid in sorted(ids)]
    if not preds:
        results = []
    elif workers <= 1:
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
                    raise RuntimeError(f"{arm} {key}, set {s}: {pairs} pairs, not {n_of[s] * n_levels}")
        out["readings"].setdefault(reading, {})[seed] = entry
    if _inputs(cfg, data_dir, runs_dir, arm) != out["inputs"]:
        raise RuntimeError("a file changed while the arm was evaluated; evaluate it again")
    _write_json(Path(runs_dir) / f"rows_{arm}.json", out)
    return out


def _part1(v: dict) -> dict:
    """What part 1 of a verdict consists of: what the label-free rows were computed from, the SHA-256 of their file
    (the same rows give the label-free side of part 2), the identity check, the self-check with every pair's spread
    and flag, and the three words."""
    return {"config_sha256": v["config_sha256"], "inputs": v["inputs"].get(LABEL_FREE),
            "rows_sha256": v.get("rows_sha256", {}).get(LABEL_FREE), "identity": v["identity"],
            "self_check": v.get("self_check"),
            "verdict": {k: v["verdict"][k] for k in ("identity", "self_check", "ranking")}}


def verdict(cfg: dict, data_dir, runs_dir) -> dict:
    """The identity check, part 1 and part 2, from the rows files of the arms that have been evaluated."""
    from .config import sha256

    ev = cfg["evaluation"]
    judged, judged_set = ev["readings"]["judged"], ev["judged_set"]
    readings = [judged] + list(ev["readings"]["reported"])
    cfg_sha = sha256(cfg)
    runs_dir = Path(runs_dir)
    vp = runs_dir / "verdict.json"
    if vp.exists() and json.loads(vp.read_text()).get("config_sha256") != cfg_sha:
        raise RuntimeError(f"{vp} is the verdict of another configuration; give this gate's runs folder")
    if not any((runs_dir / f"rows_{arm}.json").exists() or (runs_dir / f"{arm}_s{seed}").is_dir()
               for arm in (LABEL_FREE, SUPERVISED) for seed in cfg["arms"][arm]["seeds"]):
        raise RuntimeError(f"{runs_dir} holds no run and no rows of this gate; nothing is written there")
    man = manifest(data_dir)
    if man["config_sha256"] != cfg_sha:
        raise RuntimeError("the data were generated under another configuration")
    split_of, _ = _sets(cfg, man)
    n_levels = len(cfg["data"]["eval_levels_mm"])
    arms = {arm: list(cfg["arms"][arm]["seeds"]) for arm in (LABEL_FREE, SUPERVISED)}
    out = {"gate": cfg["gate"], "config_sha256": cfg_sha, "judged": {"reading": judged, "set": judged_set},
           "status": {}, "missing": [], "non_finite": [], "not_evaluated": [], "runs": {}, "inputs": {},
           "rows_sha256": {}}
    rd = {}
    for arm, seeds in arms.items():
        p = Path(runs_dir) / f"rows_{arm}.json"
        now = _inputs(cfg, data_dir, runs_dir, arm)
        if p.exists():
            rows = json.loads(p.read_text())
            if rows["config_sha256"] != cfg_sha or rows["arm"] != arm:
                raise RuntimeError(f"{p} was written under another configuration")
            if rows["inputs"] != now:
                raise RuntimeError(f"{p} was computed from other files than those now present; evaluate the arm again")
            rd[arm], out["inputs"][arm], out["rows_sha256"][arm] = rows["readings"], rows["inputs"], _sha(p)
            out["runs"].update(rows["runs"])
        else:
            rd[arm] = {}
            out["not_evaluated"].append(arm)
        for seed in seeds:
            name = f"{arm}_s{seed}"
            st = out["status"][name] = now["runs"][name]["status"] if p.exists() else "missing"
            if st != "finished":
                out["missing" if st == "missing" else "non_finite"].append(name)

    def status(arm, seed):
        return out["status"][f"{arm}_s{seed}"]

    def summaries(arm, reading, s):                         # None: a seed that counts with infinite errors
        return [None if status(arm, seed) == "non-finite"
                else rd[arm].get(reading, {}).get(str(seed), {}).get(s) for seed in arms[arm]]

    def rows_of(arm, reading, s):
        return {seed: rd[arm][reading][str(seed)][f"{s}_rows"] for seed in arms[arm]}

    def whole(arm, reading, s):                             # every run finished and every member evaluated
        return all(status(arm, seed) == "finished" and s in rd[arm].get(reading, {}).get(str(seed), {})
                   for seed in arms[arm])

    def members(s):
        return sorted(i for i, v in split_of.items() if v == s)

    def by_level(arm, reading, s):
        """The median error at each level: of each run over the members of the set, and the middle of the runs."""
        ids, rows = members(s), rows_of(arm, reading, s)
        med = [[_quantile([rows[seed][i][lv]["abs_curve_err"] for i in ids], 0.5) for lv in range(n_levels)]
               for seed in arms[arm]]
        return {"levels_mm": list(cfg["data"]["eval_levels_mm"]), "median_per_run": med,
                "median_of_runs": [_quantile([m[lv] for m in med], 0.5) for lv in range(n_levels)]}

    missing = {arm: any(status(arm, seed) == "missing" for seed in arms[arm]) for arm in arms}
    v = {}
    # identity of the label-free runs: INVALID also when the base gate's values cannot be computed again
    lf = cfg["arms"][LABEL_FREE]
    stats_eval = {r: _stats(summaries(LABEL_FREE, r, "eval")) for r in readings} if not missing[LABEL_FREE] else None
    if missing[LABEL_FREE]:
        out["identity"], v["identity"] = None, "NOT EVALUATED"
    elif not all(whole(LABEL_FREE, r, "eval") for r in readings):
        out["identity"] = {"ok": False, "largest_difference": None, "tolerance": lf["identity"]["tolerance"],
                           "why": "a label-free run has no finite predictions, or a member of the base gate's "
                                  "sample has no metrics: the base gate's values cannot be computed again"}
        v["identity"] = "INVALID"
    else:
        out["identity"] = identity(lf, stats_eval)
        v["identity"] = "OK" if out["identity"]["ok"] else "INVALID"
    invalid = v["identity"] == "INVALID"
    # the reported statistics of every arm, reading and set: None while a run of the arm is missing, and, when the
    # identity check fails, for every set but the base gate's, so that an invalid verdict holds no judged number
    out["statistics"] = {arm: {r: {s: (None if missing[arm] or (invalid and (s != "eval" or arm != LABEL_FREE))
                                       else _stats(summaries(arm, r, s))) for s in ev["sets"]}
                               for r in readings} for arm in arms}
    out["by_level"] = {arm: {r: {s: (by_level(arm, r, s) if not missing[arm] and not invalid and whole(arm, r, s)
                                     else None) for s in ev["sets"]} for r in readings} for arm in arms}
    # part 1
    sc = cfg["self_check"]
    assert sc["arm"] == LABEL_FREE, "the self-check is defined on the label-free arm"
    if missing[LABEL_FREE]:
        v["self_check"] = v["ranking"] = "INCOMPLETE"
    elif invalid:
        v["self_check"] = v["ranking"] = "INVALID"
    elif not whole(LABEL_FREE, sc["reading"], sc["set"]):   # a member of the judged set has no metrics in some run
        v["self_check"], v["ranking"] = "FAIL", "NOT EVALUABLE"
    else:
        out["self_check"] = self_check(sc, rows_of(LABEL_FREE, sc["reading"], sc["set"]), members(sc["set"]))
        v["self_check"], v["ranking"] = out["self_check"]["verdict"], out["self_check"]["ranking"]["R"]
    out["self_check_reported"] = None if invalid else {
        arm: {r: {s: (self_check(sc, rows_of(arm, r, s), members(s)) if not missing[arm] and whole(arm, r, s)
                      else None) for s in ev["sets"]} for r in readings} for arm in arms}
    # part 2
    cp = cfg["comparison"]
    if missing[LABEL_FREE] or missing[SUPERVISED]:
        v["comparison"] = "INCOMPLETE"
    elif invalid:
        v["comparison"] = "INVALID"
    else:
        st = out["statistics"]
        out["comparison"] = compare(cp["band"], st[SUPERVISED][cp["reading"]][cp["set"]],
                                    st[LABEL_FREE][cp["reading"]][cp["set"]])
        out["comparison"]["reported"] = {r: {s: compare(cp["band"], st[SUPERVISED][r][s], st[LABEL_FREE][r][s])
                                             for s in ev["sets"]} for r in readings}
        # the supervised arm read raw against the label-free arm in the judged reading: stated with the wording
        out["comparison"]["supervised_raw_against_label_free_judged"] = {
            r: compare(cp["band"], st[SUPERVISED][r][cp["set"]], st[LABEL_FREE][cp["reading"]][cp["set"]])
            for r in readings if r != cp["reading"]}
        v["comparison"] = out["comparison"]["wording"]
    # what each arm needed
    led_p = Path(data_dir) / "labels" / "ledger.json"
    led = json.loads(led_p.read_text()) if led_p.exists() else []
    tr = [e for e in led if split_of.get(e["id"]) == "train"]
    out["cost"] = {"training_members_labelled": len(tr),
                   "reference_solutions_for_training": int(sum(len(e["levels"]) for e in tr)),
                   "label_seconds_for_training_summed_over_workers": float(sum(e["seconds"] for e in tr)),
                   "note": "the label-free arm was trained in G-C2.2 (its records hold the times); its runs here "
                           "only predict"}
    out["verdict"] = v
    # Part 1 is final with the first verdict in which it is decided: that verdict is kept whole in verdict_part1.json
    # and never overwritten. It is written only while no training member has a label and the supervised arm has not
    # been evaluated, so that a kept file shows part 1 as it stood before part 2 began. Every verdict made while the
    # kept file exists says whether its part 1 is the kept one.
    p1 = Path(runs_dir) / "verdict_part1.json"
    if not p1.exists() and v["self_check"] != "INCOMPLETE":
        if tr or SUPERVISED not in out["not_evaluated"]:
            out["part1_first"] = "absent, although training members are labelled or the supervised arm is evaluated"
        else:
            _write_json(p1, out)
    out["part1_same_as_first"] = (_part1(json.loads(p1.read_text())) == _part1(json.loads(json.dumps(out)))
                                  if p1.exists() else None)
    _write_json(vp, out)
    return out
