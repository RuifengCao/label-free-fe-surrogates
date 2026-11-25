"""Gate G-F2.1: the data, the two training cycles, the predictions on the sample, the evaluations and the verdict.

Every step is the development's code (f2) called under the configurations that f21/config.py pins; this module adds
what the development did not have: the sample drawn after the stamp, the prediction of a finished run on it, and
the verdict. A gate configuration G (f21.config.config(), or the reduced one of f21/smoke.py) drives every function.

Folders, all given by the caller:
    data        the development's members on the family's mesh: the 128 training members (exported, never solved
                beyond their preload) and the 31 members of the development (labelled; reported, not judged)
    data_thin   the second cycle's 32 extra training members (exported only)
    data_gate   the sample: sample.json (its seed and the hash of its draw, written before the first member), the
                members, their labels
    runs        runs/<first preset>/label_free_s<seed>/ and runs/<second preset>/label_free_s<seed>/, as f2.train
                writes them; each cycle's folder also holds its predictions on the development's 31 members
    runs_gate   runs_gate/label_free_s<seed>/: the finished second cycle's predictions on the sample, in both
                readings, with a history.json that names the state they were made from; or, for a seed that has no
                finished run, a history.json that says why it has no predictions

What the functions hold to, whatever a queue or an operator does:
    a cycle counts as finished only when its record says so and its end-of-cycle predictions are written
    (condense.json, which f2.train.predict writes last);
    after a stop for good (a non-finite loss or non-finite predictions) no training that has not been started is
    started;
    no seed predicts the sample, and the development's members are not evaluated, before every training of the gate
    has ended or, after a stop for good, will not be started;
    the sample is evaluated only when every seed has predictions on it or a record that it has none, and only on
    labels that pass their checks;
    the verdict refuses an evaluation whose inputs are not those on record.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from .config import check_sample_seed, run_config, sample_config, sha256

SAMPLE_FILE = "sample.json"
CYCLES = ("first", "second")


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _write_json(p: Path, obj) -> None:
    from c22.data import _replace

    tmp = Path(str(p) + ".tmp")
    with open(tmp, "w", encoding="ascii", newline="\n") as fh:
        fh.write(json.dumps(obj, indent=1))
    _replace(tmp, Path(p))


def _read(p: Path) -> dict:
    return json.loads(Path(p).read_text()) if Path(p).exists() else {}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def preset(G: dict, cycle: str) -> str:
    return G["recipe"][cycle]["preset"]


def run_dir(G: dict, runs, cycle: str, seed: int) -> Path:
    return Path(runs) / preset(G, cycle) / f"label_free_s{seed}"


def evaluation_file(G: dict) -> str:
    return "evaluation_seeds_" + "_".join(str(s) for s in G["recipe"]["seeds"]) + ".json"


# ---------------------------------------------------------------------------------------------------------------
# the data


def sample_folder(G: dict, data_gate) -> dict:
    """The record of the sample that a folder holds (sample.json). It must be this configuration's sample."""
    sf = Path(data_gate) / SAMPLE_FILE
    if not sf.exists():
        raise RuntimeError(f"{data_gate} holds no {SAMPLE_FILE}: the sample has not been generated there")
    rec = json.loads(sf.read_text())
    if rec.get("gate_config_sha256") != sha256(G):
        raise RuntimeError(f"the sample in {data_gate} was generated under another gate configuration")
    if rec.get("seed") != G["sample"]["seed"]:
        raise RuntimeError(f"the sample in {data_gate} was drawn with seed {rec.get('seed')}, not the configuration's")
    return rec


def require_solver(G: dict) -> str:
    """The linear solver of this process's reference solves; an error if the configuration names another one."""
    from f2.data import _solver

    have, want = _solver(), (G.get("reference") or {}).get("linear_solver")
    if want is not None and have != want:
        raise RuntimeError(f"the linear solver of this host is {have}, not the configured {want}; stop and report")
    return have


def check_preloads(data_dir) -> int:
    """Every member that the folder's manifest lists has a preload solve on record that converged and reached its
    target (generate_log.json); otherwise an error. Returns the number of members."""
    from f2 import data

    data_dir = Path(data_dir)
    ids = [r["id"] for r in data.manifest(data_dir)["instances"]]
    log_p = data_dir / "generate_log.json"
    log = {e["id"]: e for e in (json.loads(log_p.read_text()) if log_p.exists() else [])}
    none = [i for i in ids if i not in log]
    if none:
        raise RuntimeError(f"the generation log of {data_dir} holds no preload record for {len(none)} members "
                           f"(first {none[0]}); stop and report")
    bad = [i for i in ids if not (log[i]["preload"]["converged"] and log[i]["preload"]["on_target"])]
    if bad:
        raise RuntimeError(f"preload not converged or not on target in {data_dir}: {bad}; stop and report")
    return len(ids)


def generate(G: dict, what: str, data_dir, workers: int = 1):
    """Export the members of one of the three data folders, each with its preload solve: what "train" (the
    development's members), "thin" (the second cycle's extra training members) or "sample" (the sample, drawn with
    the configuration's seed). Ends with an error if a preload did not converge or is not on target."""
    from f2 import data

    require_solver(G)
    only = list(G["recipe"]["only"]) if G["recipe"]["only"] else None
    data_dir = Path(data_dir)
    if what == "train":
        cfg = run_config(G, "first")
        if data.data_sha256(cfg) != G["recipe"]["data_sha256"]:
            raise RuntimeError("the development's data configuration is not the pinned one")
        out = data.generate(cfg, data_dir, workers=workers, only=only)
    elif what == "thin":
        x = data.extra_config(run_config(G, "second"))
        if x is None or data.data_sha256(x) != G["recipe"]["second"]["extra_data_sha256"]:
            raise RuntimeError("the extra members' data configuration is not the pinned one")
        out = data.generate(x, data_dir, splits=("train",), workers=workers)
    elif what == "sample":
        seed = check_sample_seed(G)
        sf = data_dir / SAMPLE_FILE
        old = sample_folder(G, data_dir) if sf.exists() else None     # another configuration's folder: refused here
        if old is None and data_dir.exists() and any(data_dir.iterdir()):
            raise RuntimeError(f"{data_dir} holds files but no {SAMPLE_FILE}; give a new folder")
        cfg = sample_config(G)
        drawn = [[iid, dataclasses.asdict(q)] for iid, split, q in data.members(cfg) if split == "eval"]
        if len(drawn) != G["sample"]["n"]:
            raise RuntimeError(f"the draw gave {len(drawn)} members, not {G['sample']['n']}")
        draw_sha = sha256({"members": drawn})
        if old is not None:
            if old.get("draw_sha256") != draw_sha:
                raise RuntimeError(f"the draw differs from the one that {sf} records; stop and report")
        else:
            data_dir.mkdir(parents=True, exist_ok=True)
            _write_json(sf, {"gate": G["gate"], "gate_config_sha256": sha256(G), "seed": seed,
                             "data_sha256": data.data_sha256(cfg), "members": len(drawn), "draw_sha256": draw_sha,
                             "written": _now()})
        out = data.generate(cfg, data_dir, splits=("eval",), workers=workers)
    else:
        raise ValueError("what must be train, thin or sample")
    check_preloads(data_dir)
    return out


def data_config(G: dict, what: str, data_dir) -> dict:
    """The configuration a labelled data folder was generated under."""
    if what == "train":
        return run_config(G, "second")
    sample_folder(G, data_dir)
    return sample_config(G)


def label(G: dict, what: str, data_dir, workers: int = 1) -> int:
    """The exact solutions of the labelled members of a data folder: the development's 31 (what "train") or the
    sample's (what "sample")."""
    from f2 import data
    from f2.evaluate import label_summary

    require_solver(G)
    cfg = data_config(G, what, data_dir)
    ids = [r["id"] for r in data.manifest(data_dir)["instances"] if r["split"] in data.LABELLED_SPLITS]
    data.label(cfg, data_dir, ids, workers=workers)
    label_summary(data_dir)
    return len(ids)


def _reference_member(job):
    """What the evaluation needs of a labelled member beyond the label's own checks, tested without a prediction:
    the rotation of the measuring ring rises along the labelled path (f2.evaluate.path_slope), and the reference
    code evaluates every labelled state (f2.evaluate._member). Returns (id, None) or (id, what failed)."""
    data_dir, iid = job
    from f2.data import load_export, load_label
    from f2.evaluate import clean
    from f2.instance import ExportedProblem

    try:
        ref = load_label(data_dir, iid)
        x = np.concatenate([[0.0], np.asarray(ref["ThetaD"], float)])
        if not np.all(np.diff(x) > 0):
            return iid, "the rotation of the measuring ring does not rise along the labelled path"
        ex, _ = load_export(Path(data_dir) / "inst" / f"{iid}.npz")
        P = ExportedProblem(ex)
        for l in range(ref["Theta"].size):
            clean(P)
            P.evaluate(ref["z"][l], float(ref["Theta"][l]))["plastic"]
    except Exception as err:                               # reported as a failed check, not as a traceback
        return iid, f"{type(err).__name__}: {err}"
    return iid, None


def check_labels(G: dict, what: str, data_dir, workers: int = 1) -> dict:
    """The checks of the labels of a data folder (what "train" or "sample"): the development's (f2.data.check_labels:
    every label there once at its levels, files as the manifest and the ledger name them, preloads on target, every
    level converged, optimality within the limits, the two moment readings equal); the configured linear solver in
    every ledger entry; what the evaluation needs of each member (_reference_member); and, for the sample, the
    number of its members."""
    from f2 import data
    from f2.evaluate import pool

    cfg = data_config(G, what, data_dir)
    led_p = Path(data_dir) / "labels" / "ledger.json"
    led = json.loads(led_p.read_text()) if led_p.exists() else []
    if not led:
        return {"labels": 0, "ok": False, "why": "no label is written"}
    r = data.check_labels(cfg, data_dir)
    have = {e["id"] for e in led}
    want = (G.get("reference") or {}).get("linear_solver")
    r["solvers"] = sorted({str(e.get("solver")) for e in led})
    r["solver_ok"] = bool(want is None or r["solvers"] == [want])
    jobs = [(str(data_dir), i) for i in data.labelled_ids(cfg, data_dir) if i in have]
    if workers <= 1:
        res = [_reference_member(j) for j in jobs]
    else:
        with pool(workers) as p:
            res = list(p.imap_unordered(_reference_member, jobs))
    r["reference_notes"] = {iid: why for iid, why in sorted(res) if why}
    r["reference_ok"] = not r["reference_notes"]
    r["ok"] = bool(r["ok"] and r["solver_ok"] and r["reference_ok"])
    if what == "sample":
        n = sum(1 for x in data.manifest(data_dir)["instances"] if x["split"] == "eval")
        r["members"] = n
        r["ok"] = bool(r["ok"] and n == G["sample"]["n"])
    return r


# ---------------------------------------------------------------------------------------------------------------
# the trainings


def cycle_state(G: dict, runs, cycle: str, seed: int) -> str:
    """Where a cycle of a seed stands, from its folder: "finished" (its record says so, with every step, and its
    end-of-cycle predictions are written), "stopped" (for good, on a non-finite value), "under way" (started and not
    ended: it resumes when its command is run again) or "not started"."""
    run = run_dir(G, runs, cycle, seed)
    hp = run / "history.json"
    if hp.exists():
        h = json.loads(hp.read_text())
        if h.get("config_sha256") != G["recipe"][cycle]["config_sha256"] or h.get("seed") != seed:
            raise RuntimeError(f"{run} does not hold this seed's run of the pinned {cycle}-cycle configuration")
        status = str(h.get("status", ""))
        if status.startswith("non-finite"):
            return "stopped"
        if status == "finished" and h.get("steps") == h.get("total_steps") and (run / "condense.json").exists():
            return "finished"
        return "under way"                                 # its steps are done, its predictions are not written
    return "under way" if run.exists() and any(run.iterdir()) else "not started"


def training_states(G: dict, runs) -> dict:
    return {s: {c: cycle_state(G, runs, c, s) for c in CYCLES} for s in G["recipe"]["seeds"]}


def settled(G: dict, runs) -> tuple[bool, str]:
    """True once no training of the gate will run any more: every cycle of every seed is finished or has stopped
    for good, or, once a run has stopped for good, was never started. Otherwise False and what is still to run."""
    st = training_states(G, runs)
    stop = any(x == "stopped" for d in st.values() for x in d.values())
    for s, d in st.items():
        for c in CYCLES:
            if d[c] == "under way":
                return False, f"the {c} cycle of seed {s} is under way"
            if d[c] == "not started" and not stop:
                return False, f"the {c} cycle of seed {s} has not been trained"
    return True, ""


def train(G: dict, cycle: str, seed: int, data_dir, runs, device: str = "cuda", max_hours: float | None = None,
          extra_dir=None, stop_after_epoch: int | None = None) -> dict:
    """One cycle of one seed (f2.train.train under the cycle's pinned run configuration; resumes). The second cycle
    starts from the weights of the same seed's finished first cycle. A cycle that has not been started is not
    started once a run of the gate has stopped for good."""
    from f2.train import train as train2

    if seed not in G["recipe"]["seeds"]:
        raise RuntimeError("the seed is not one of the gate's")
    if seed in G["recipe"]["training_seeds_kept_from_the_gate"]:
        raise RuntimeError("a training seed of the development or of the timings")
    cfg = run_config(G, cycle)
    st = training_states(G, runs)
    if st[seed][cycle] == "not started":
        gone = [f"{c} cycle of seed {s}" for s, d in st.items() for c in CYCLES if d[c] == "stopped"]
        if gone:
            raise RuntimeError(f"a run of the gate has stopped for good ({gone[0]}); no training that has not been "
                               "started is started")
    init = None
    if cycle == "second":
        if st[seed]["first"] != "finished":
            raise RuntimeError(f"the first cycle of seed {seed} has not finished")
        init = run_dir(G, runs, "first", seed) / "state.pt"
    return train2(cfg, seed, data_dir, Path(runs) / preset(G, cycle), device=device, max_hours=max_hours,
                  stop_after_epoch=stop_after_epoch, init_from=init, other_seed=True, extra_dir=extra_dir)


def predict_sample(G: dict, seed: int, runs, data_gate, runs_gate, device: str = "cuda") -> dict:
    """The predictions of a seed's finished second cycle on the sample, in both readings, written to
    runs_gate/label_free_s<seed>/ as f2.train.predict writes a run's own predictions, with a history.json that names
    the state. Refused before every training of the gate has ended or will not be started (settled). A seed without
    a finished run gets a history.json that says why it has no predictions. An end without finite predictions is
    final. A record once written is returned as it is: nothing is predicted twice."""
    from f2.train import PREDICTION_FILES, predictions_written

    if seed not in G["recipe"]["seeds"]:
        raise RuntimeError("the seed is not one of the gate's")
    sample_folder(G, data_gate)
    cfg = sample_config(G)
    cfg_sha = sha256(cfg)
    out = Path(runs_gate) / f"label_free_s{seed}"
    hp = out / "history.json"
    if hp.exists():
        old = json.loads(hp.read_text())
        if old.get("config_sha256") != cfg_sha or old.get("seed") != seed:
            raise RuntimeError(f"{out} holds predictions of another configuration or seed; use a fresh folder")
        status = str(old.get("status", ""))
        if status.startswith(("non-finite", "no predictions")) or (status == "finished" and predictions_written(out)):
            return old
        if status == "finished":                           # the record is there and its files are not
            raise RuntimeError(f"{out} holds the record of finished predictions without their files; restore the "
                               "files (nothing is predicted twice)")
    ok, why = settled(G, runs)
    if not ok:
        raise RuntimeError(f"no seed predicts the sample before every training of the gate has ended: {why}")
    mine = training_states(G, runs)[seed]
    if any(x != "finished" for x in mine.values()):       # only after a stop for good: this seed has no finished run
        c = next(c for c in CYCLES if mine[c] != "finished")
        reason = (f"the {c} cycle stopped on a non-finite value" if mine[c] == "stopped"
                  else f"the {c} cycle was not started after a run of the gate had stopped for good")
        hist = {"gate": G["gate"], "config_sha256": cfg_sha, "arm": "label_free", "seed": seed, "trainings": mine,
                "prediction_files": None, "status": "no predictions: " + reason, "written": _now()}
        out.mkdir(parents=True, exist_ok=True)
        _write_json(hp, hist)
        return hist
    src, first = run_dir(G, runs, "second", seed), run_dir(G, runs, "first", seed)
    h2, h1 = _read(src / "history.json"), _read(first / "history.json")
    state_first = file_sha256(first / "state.pt")
    if (h2.get("init_from") or {}).get("sha256") != state_first:
        raise RuntimeError("the second cycle did not start from this seed's first-cycle state")
    import torch

    from f2.model import build
    from f2.train import MATMUL_PRECISION, build_item, check_manifest, evaluated_ids, predict

    man = check_manifest(cfg, data_gate)
    state = src / "state.pt"
    s = torch.load(state, map_location="cpu", weights_only=False)
    if s["history"].get("config_sha256") != h2["config_sha256"] or s["step"] != h2["total_steps"] \
            or s["history"].get("seed") != seed:
        raise RuntimeError("the state is not the end of this seed's second cycle")
    torch.set_float32_matmul_precision(MATMUL_PRECISION)
    dev = torch.device(device)
    it = build_item(data_gate, evaluated_ids(cfg, man)[0], dev, cfg["model"]["lift"])
    nets = build(cfg, it["base"].shape[-1] + 1, it["maps"]["nb"])
    del it
    for net, k in zip(nets, ("enc", "dec", "head")):
        net.load_state_dict(s[k])
        net.to(dev)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    ok = predict(cfg, nets, data_gate, out, dev)
    hist = {"gate": G["gate"], "config_sha256": cfg_sha, "data_sha256": man["config_sha256"], "arm": "label_free",
            "seed": seed, "torch": torch.__version__, "device": str(dev),
            "gpu": torch.cuda.get_device_name(0) if dev.type == "cuda" else None,
            "trained_in": {"second": {"preset": h2.get("preset"), "config_sha256": h2["config_sha256"],
                                      "state_sha256": file_sha256(state), "epoch": int(s["epoch"]),
                                      "step": int(s["step"]), "extra_data_sha256": h2.get("extra_data_sha256"),
                                      "init_from_sha256": state_first},
                           "first": {"preset": h1.get("preset"), "config_sha256": h1["config_sha256"],
                                     "state_sha256": state_first, "steps": h1.get("steps")}},
            "predict_seconds": round(time.perf_counter() - t0, 2),
            "prediction_files": {f: file_sha256(out / f) for f in PREDICTION_FILES} if ok else None,
            "status": "finished" if ok else "non-finite predictions", "written": _now()}
    _write_json(hp, hist)
    return hist


# ---------------------------------------------------------------------------------------------------------------
# the evaluations


def _data_inputs(data_dir) -> dict:
    from f2.data import _solver

    return {"manifest_sha256": file_sha256(Path(data_dir) / "manifest.json"),
            "ledger_sha256": file_sha256(Path(data_dir) / "labels" / "ledger.json"), "linear_solver": _solver()}


def _prediction_inputs(run_of: dict) -> dict:
    """SHA-256 of the prediction files of each seed as they are now (None for a seed without predictions)."""
    from f2.train import PREDICTION_FILES, predictions_written

    return {str(s): ({f: file_sha256(Path(run) / f) for f in PREDICTION_FILES} if predictions_written(run) else None)
            for s, run in run_of.items()}


def evaluate(G: dict, what: str, runs, data_dir, workers: int = 1) -> dict:
    """The metrics of the gate's seeds: on the development's 31 members from the second cycle's own predictions
    (what "dev": runs is the runs folder) or on the sample (what "sample": runs is runs_gate; for the readings of
    reported.exact the reference at the predicted rotation of the measuring ring is solved too). Written beside the
    runs, with the SHA-256 of what was read ("inputs").

    Refused, with nothing written: the development's members before every training of the gate has ended (settled);
    the sample unless every seed has predictions on it or a record that it has none; prediction files of the sample
    that are not those their record names; labels that fail their checks; a host whose linear solver is not the
    configured one; inputs that changed while the evaluation ran."""
    from f2.evaluate import evaluate as evaluate2

    seeds = list(G["recipe"]["seeds"])
    if what == "dev":
        ok, why = settled(G, runs)
        if not ok:
            raise RuntimeError(f"the development's members are evaluated when every training has ended: {why}")
        cfg, where, kind, exact = run_config(G, "second"), Path(runs) / preset(G, "second"), "train", False
        run_of = {s: where / f"label_free_s{s}" for s in seeds}
        finished = [s for s in seeds if cycle_state(G, runs, "second", s) == "finished"]
    elif what == "sample":
        sample_folder(G, data_dir)
        cfg, where, kind, exact = sample_config(G), Path(runs), "sample", list(G["reported"]["exact"]["readings"])
        run_of = {s: where / f"label_free_s{s}" for s in seeds}
        finished = []
        for s in seeds:                                    # a record for every seed; the files it names, unchanged
            h = _read(run_of[s] / "history.json")
            status = str(h.get("status", ""))
            if status == "finished":
                if not h.get("prediction_files"):
                    raise RuntimeError(f"the record of seed {s} names no prediction files")
                for f, want in h["prediction_files"].items():
                    if file_sha256(run_of[s] / f) != want:
                        raise RuntimeError(f"{run_of[s] / f} is not the file that the predictions' record names")
                finished.append(s)
            elif not status.startswith(("non-finite", "no predictions")):
                raise RuntimeError(f"seed {s} has neither predictions on the sample nor a record that it has none; "
                                   "the sample is evaluated once, when every seed has one of the two")
    else:
        raise ValueError("what must be dev or sample")
    require_solver(G)
    inputs = {"predictions": _prediction_inputs(run_of), **_data_inputs(data_dir)}
    r = check_labels(G, kind, data_dir, workers=workers)
    if not r["ok"]:
        raise RuntimeError(f"the labels of {data_dir} fail their checks; nothing is evaluated")
    ev = evaluate2(cfg, data_dir, where, workers=workers, exact=exact, seeds=seeds, write=False)
    if {"predictions": _prediction_inputs(run_of), **_data_inputs(data_dir)} != inputs:
        raise RuntimeError("a prediction file, the manifest or the ledger changed while the evaluation ran")
    missing = [s for s in finished if ev["status"].get(str(s)) != "finished"]
    if missing:
        raise RuntimeError(f"seeds with a finished record and without readable predictions: {missing}")
    ev["inputs"] = inputs
    _write_json(where / evaluation_file(G), ev)
    return ev


def _values(ev: dict, seed: int, reading: str, key: str, n_levels: int, members=None, level=None) -> np.ndarray:
    """A seed's values of one quantity in absolute value, one for each pair (member, level): infinite where the
    member's metrics failed, where the value is missing and where it is not finite."""
    rows = ev["rows"].get(f"{seed}|{reading}")
    if rows is None:
        return np.array([])
    out = []
    for iid in ev["members"]:
        if members is not None and iid not in members:
            continue
        r = rows["members"].get(iid)
        if r is not None and len(r) != n_levels:
            raise RuntimeError(f"{iid}: {len(r)} levels, not {n_levels}")
        for l in range(n_levels):
            if level is not None and l != level:
                continue
            x = r[l].get(key) if r is not None else None
            x = abs(float(x)) if x is not None else float("inf")
            out.append(x if np.isfinite(x) else float("inf"))
    return np.array(out, dtype=float)


def _signed(ev: dict, seed: int, reading: str, key: str, n_levels: int) -> np.ndarray:
    """A seed's values of one quantity with their signs, one for each pair (member, level): not-a-number where the
    member's metrics failed or the value is missing."""
    rows = ev["rows"][f"{seed}|{reading}"]["members"]
    out = []
    for iid in ev["members"]:
        r = rows.get(iid)
        for l in range(n_levels):
            x = r[l].get(key) if r is not None else None
            out.append(float(x) if x is not None else float("nan"))
    return np.array(out, dtype=float)


def _stats(v: np.ndarray) -> dict:
    from c2.evaluate import _quantile

    if v.size == 0:
        return {"n": 0}
    return {"median": _quantile(v, 0.5), "p90": _quantile(v, 0.9), "max": float(v.max()), "n": int(v.size),
            "not_finite": int(np.isinf(v).sum())}


def verdict(G: dict, runs, data_dir, data_gate, runs_gate) -> dict:
    """The gate's verdict from the files as they are: PASS, FAIL, or INCOMPLETE while a training, a prediction or an
    evaluation is missing and nothing has failed. Writes nothing. An evaluation whose inputs are not those on record
    is refused with an error: of the sample, the manifest, the ledger and the prediction files that the predictions'
    records name; of the development's members, the manifest, the ledger and the prediction files as they are now.
    A FAIL is complete once every seed has its record on the sample and what the finished seeds gave is evaluated."""
    from f2 import data
    from f2.train import evaluated_ids

    J, X, seeds = G["judged"], G["reported"]["exact"], list(G["recipe"]["seeds"])
    v = {"gate": G["gate"], "gate_config_sha256": sha256(G), "seeds": seeds, "judged": dict(J), "per_seed": {},
         "runs": {}, "reported": {}, "exact": {"quantity": X["quantity"], "reading": J["reading"], "per_seed": {}},
         "statistics": "every statistic is of absolute values over pairs (member, level); a pair whose evaluation "
                       "failed or whose value is missing or not finite enters as infinite"}
    failed, waiting = [], []
    for s in seeds:
        rec = {}
        for cyc in CYCLES:
            h = _read(run_dir(G, runs, cyc, s) / "history.json")
            rec[cyc] = {k: h.get(k) for k in ("status", "steps", "total_steps", "config_sha256", "resumes",
                                              "peak_memory_GiB", "torch", "gpu")}
            rec[cyc]["state"] = cycle_state(G, runs, cyc, s)
            if "epoch_seconds" in h:
                rec[cyc].update(training_seconds=float(sum(h["epoch_seconds"])), cap_events=len(h["cap_events"]),
                                bursts=len(h["bursts"]))
        rec["sample"] = {k: _read(Path(runs_gate) / f"label_free_s{s}" / "history.json").get(k)
                         for k in ("status", "trained_in", "prediction_files")}
        v["runs"][str(s)] = rec
        sst = rec["sample"]["status"]
        if "stopped" in (rec["first"]["state"], rec["second"]["state"]) or (sst is not None and sst != "finished"):
            failed.append(s)                               # a stop for good, or no finite predictions on the sample
        elif rec["first"]["state"] != "finished" or rec["second"]["state"] != "finished" or sst is None:
            waiting.append(s)
    v["failed_seeds"], v["waiting_seeds"] = failed, waiting
    status = {s: v["runs"][str(s)]["sample"]["status"] for s in seeds}
    predicted = [s for s in seeds if status[s] == "finished"]
    cfg2 = run_config(G, "second")
    n_levels = len(cfg2["data"]["eval_levels"])
    ep = Path(runs_gate) / evaluation_file(G)
    ev = json.loads(ep.read_text()) if ep.exists() else None
    done = (ev is not None and all(ev["status"].get(str(s)) == "finished" for s in predicted)) \
        or (not predicted and all(x is not None for x in status.values()))
    if ev is not None:
        sample_folder(G, data_gate)
        if ev["config_sha256"] != sha256(sample_config(G)):
            raise RuntimeError("the sample's evaluation was made under another configuration")
        man = data.manifest(data_gate)
        ids = sorted(r["id"] for r in man["instances"] if r["split"] == "eval")
        n_members = G["sample"]["n"]
        if sorted(ev["members"]) != ids or len(ids) != n_members:
            raise RuntimeError(f"the evaluation's members are not the {n_members} members of the sample's manifest")
        if sorted(ev.get("exact_readings", [])) != sorted(X["readings"]):
            raise RuntimeError("the sample's evaluation does not hold the exact value for the configured readings")
        inp = ev.get("inputs") or {}
        now = {"manifest_sha256": file_sha256(Path(data_gate) / "manifest.json"),
               "ledger_sha256": file_sha256(Path(data_gate) / "labels" / "ledger.json")}
        if any(inp.get(k) != x for k, x in now.items()):
            raise RuntimeError("the sample's manifest or ledger is not the one the evaluation read; evaluate again")
        for s in seeds:
            if (inp.get("predictions") or {}).get(str(s)) != v["runs"][str(s)]["sample"]["prediction_files"]:
                raise RuntimeError(f"the evaluation did not read the prediction files that the record of seed {s} "
                                   "names; evaluate again")
        params = {r["id"]: r["params"] for r in man["instances"]}
        band = G["reported"]["thin_band"]
        thin = [i for i in ev["members"] if params[i][band["parameter"]] <= band["at_most"]]
        v["sample"] = {"seed": G["sample"]["seed"], "members": n_members, "levels": n_levels,
                       "pairs": n_members * n_levels, "thin_members": len(thin),
                       "evaluation_sha256": file_sha256(ep), "inputs": inp}
        pairs = [(i, l) for i in ev["members"] for l in range(n_levels)]     # the order of _values
        for s in seeds:
            if ev["status"].get(str(s)) != "finished":
                continue
            x = _values(ev, s, J["reading"], J["quantity"], n_levels)
            if x.size != n_members * n_levels:
                raise RuntimeError(f"seed {s}: {x.size} pairs, not {n_members * n_levels}")
            v["per_seed"][str(s)] = _stats(x)
            rep = {"thin_band": _stats(_values(ev, s, J["reading"], J["quantity"], n_levels, members=thin)),
                   "by_level": [_stats(_values(ev, s, J["reading"], J["quantity"], n_levels, level=l)) for l in range(n_levels)],
                   "errors": sorted(ev["rows"][f"{s}|{J['reading']}"]["errors"]),
                   "not_finite_pairs": [[i, l] for (i, l), e in zip(pairs, x) if np.isinf(e)]}
            worst = {i: float(_values(ev, s, J["reading"], J["quantity"], n_levels, members=[i]).max()) for i in ev["members"]}
            rep["worst_members"] = sorted(worst.items(), key=lambda kv: -kv[1])[:5]
            for rd in [J["reading"]] + list(G["reported"]["readings"]):
                rep[rd] = {q: _stats(_values(ev, s, rd, q, n_levels)) for q in [J["quantity"]] + list(G["reported"]["quantities"])}
            v["exact"]["per_seed"][str(s)] = _stats(_values(ev, s, J["reading"], X["quantity"], n_levels))
            first, exact = (_signed(ev, s, J["reading"], k, n_levels) for k in (X["signed"], X["quantity"]))
            both = np.isfinite(first) & np.isfinite(exact)            # the pairs in which both values are finite
            d = np.abs(first[both] - exact[both])
            rep["first_order_minus_exact"] = {"pairs": int(d.size), **(
                {"median": float(np.median(d)), "p90": float(np.quantile(d, 0.9)), "max": float(d.max())} if d.size else {})}
            v["reported"][str(s)] = rep
    dp = Path(runs) / preset(G, "second") / evaluation_file(G)
    if dp.exists():
        dv = json.loads(dp.read_text())
        if dv["config_sha256"] != sha256(cfg2):
            raise RuntimeError("the evaluation of the development's members was made under another configuration")
        if sorted(dv["members"]) != sorted(evaluated_ids(cfg2)):
            raise RuntimeError("the evaluation of the development's members does not hold the configuration's members")
        inp = dv.get("inputs") or {}
        read = {"manifest_sha256": Path(data_dir) / "manifest.json",
                "ledger_sha256": Path(data_dir) / "labels" / "ledger.json"}
        gone = [str(p) for p in read.values() if not p.exists()]
        if gone:
            raise RuntimeError(f"{gone[0]} is not there: the evaluation of the development's members cannot be "
                               "compared with what it read")
        if any(inp.get(k) != file_sha256(p) for k, p in read.items()):
            raise RuntimeError("the development's manifest or ledger is not the one its evaluation read; evaluate again")
        have = _prediction_inputs({s: run_dir(G, runs, "second", s) for s in seeds})
        if any((inp.get("predictions") or {}).get(str(s)) != have[str(s)] for s in seeds):
            raise RuntimeError("the prediction files of the development's members are not those their evaluation "
                               "read; evaluate again")
        v["development_members"] = {
            str(s): {rd: _stats(_values(dv, s, rd, J["quantity"], n_levels)) for rd in [J["reading"]] + list(G["reported"]["readings"])}
            for s in seeds if dv["status"].get(str(s)) == "finished"}
        v["development"] = {"members": len(dv["members"]), "evaluation_sha256": file_sha256(dp), "inputs": inp}
    dev_done = all(str(s) in v.get("development_members", {}) for s in seeds
                   if v["runs"][str(s)]["second"]["state"] == "finished")
    lines = J["lines"]
    if failed:                                             # complete once what the finished seeds gave is on record
        v["verdict"], v["why"] = "FAIL", f"seeds that did not finish or stopped on a non-finite value: {failed}"
        v["complete"] = bool(settled(G, runs)[0] and done and dev_done and all(x is not None for x in status.values()))
    elif waiting or not done or not dev_done or len(v["per_seed"]) != len(seeds):
        v["verdict"], v["why"] = "INCOMPLETE", "a training, a prediction or an evaluation is missing"
        v["complete"] = False
    else:
        from c2.evaluate import _quantile

        across = {k: _quantile(np.array([v["per_seed"][str(s)][k] for s in seeds]), 0.5) for k in J["per_seed"]}
        v["across_seeds"] = across
        ok = all(across[k] <= lines[k] for k in J["per_seed"])
        v["verdict"] = "PASS" if ok else "FAIL"
        v["why"] = "; ".join(f"{k} {100 * across[k]:.3f}% against {100 * lines[k]:g}%" for k in J["per_seed"])
        xa = {k: _quantile(np.array([v["exact"]["per_seed"][str(s)][k] for s in seeds]), 0.5) for k in J["per_seed"]}
        v["exact"]["across_seeds"] = xa
        v["exact"]["same_side_of_each_line"] = {k: bool((xa[k] <= lines[k]) == (across[k] <= lines[k])) for k in J["per_seed"]}
        v["complete"] = True
    return v
