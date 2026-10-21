"""cmame-paper Stage 12 (PREREG_K3D Sec. 4-6): scripts/adjudicate_k3d.py on
constructed reports of the run's shape.

The verdicts read the guard on per-seed medians (computed again here from
the per-instance arrays), with the seed-mean reading beside them; a
reference carried by one instance leaves the means unable to show a
reduction while the medians show it; a non-finite reference value leaves a
hypothesis NOT EVALUATED, a non-finite value of the new arm is a divergence;
H3-3D reads one of its four labels. Every refusal of Sec. 6 refuses, the
content check among them as recomputed from the arrays; every deviation is
recorded; the holdout readings are evaluated only with the run's arrays and
PREREG_HOLDOUT's labels manifest; a return's files must be exactly those its
provenance file lists, and its states, seed files and commits the report's."""

import copy
import hashlib
import importlib.util
import json
import math
import statistics
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "configs" / "k3d_v1.json").read_text())
METRICS = ("energy_gap_rel", "disp_rel_l2", "vm_rel_l2", "peak_vm_rel_err", "crit_recall")
SEEDS = (0, 1, 2)
N_VAL, N_CORPUS = 256, 2000
MANIFEST = "dc75628290bb4e10cb28cc63b2ceba6539500d73def5c018a7b7a1ebb2aa8298"


def _adj():
    spec = importlib.util.spec_from_file_location("adjudicate_k3d",
                                                  ROOT / "scripts" / "adjudicate_k3d.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ADJ = _adj()


def _arrays(level: float, seed_factors, rng, spread: float = 0.3) -> list:
    return [level * f * np.exp(rng.normal(0, spread, N_VAL)) for f in seed_factors]


def _cell(per: dict) -> dict:
    """{metric: [array per seed]} -> an E8-shaped cell."""
    evs = []
    for j in range(len(SEEDS)):
        e = {m: float(np.mean(per[m][j])) for m in METRICS}
        e["per_instance"] = {m: [float(x) for x in per[m][j]] for m in METRICS}
        evs.append(e)
    return {"per_seed_eval": evs}


def _world(ratio_gap=0.5, ratio_vm=0.5, ar_ratio=None, seed=0):
    """A report of the run's shape, with the configuration, a source report
    and every check passing. L_K's instance values are L_D's times the
    ratios; the label-free row's relative energy gap is L_K's divided by
    ar_ratio (default: a twentieth of L_D's)."""
    from fejepa.report import config_sha256

    rng = np.random.default_rng(seed)
    ld = {m: _arrays(0.25, (1.0, 1.05, 1.1), rng) for m in METRICS}
    lk = {m: [x * (ratio_gap if m == "energy_gap_rel" else ratio_vm if m == "vm_rel_l2"
                   else 0.9) for x in ld[m]] for m in METRICS}
    ar = {m: [x / 20 for x in ld[m]] for m in METRICS}
    if ar_ratio is not None:
        ar["energy_gap_rel"] = [x / ar_ratio for x in lk["energy_gap_rel"]]
    cfg = copy.deepcopy(CFG)
    names = ADJ.pool_prefix_names(N_CORPUS, N_VAL, 1, 1024)
    rep = {"prereg": {"file": "PREREG_K3D.md", "config_sha256": config_sha256(cfg)},
           "config": cfg,
           "provenance": {"git": "prereg-k3d", "config_sha256": config_sha256(cfg),
                          "source_report_sha256": cfg["source"]["report_sha256"],
                          "datasets": [{"manifest_sha256": MANIFEST}], "seeds": list(SEEDS)},
           "seeds": list(SEEDS), "rows": ["ar", "labels", "labels_knorm"],
           "cells": {"ar": {"1024": _cell(ar)}, "labels": {"1024": _cell(ld)},
                     "labels_knorm": {"1024": _cell(lk)}},
           "content_checks": {f"{r}_s{s}": {"ok": True} for r in ("ar", "labels")
                              for s in SEEDS},
           "reused": {f"{r}_s{s}": {"sha256": cfg["reused"][r]["sha256"][str(s)]}
                      for r in ("ar", "labels") for s in SEEDS},
           "reused_evaluations_from_disk": False,
           "per_seed": {f"s{s}": {
               "train": {"loss": "knorm", "epochs_run": 200, "seed": s, "files": names,
                         "steps": 204800, "activation_checkpointing": False,
                         "resumed_from_epoch": None, "loss_by_epoch": [0.9, 0.2]},
               "state": {"sha256": "ab" * 32}, "seconds": {"train_and_evaluate": 80000.0},
               "machine": {"start": {"host": "box", "gpu_driver": "595.71.05"},
                           "resumed_on": [],
                           "end": {"host": "box", "gpu_driver": "595.71.05"}}}
               for s in SEEDS},
           "torch": {"version": "2.12.1+cu130"}, "gpu": {"gpu": "NVIDIA GeForce RTX 5090"},
           "holdout": None}
    source = {"provenance": {"datasets": [{"manifest_sha256": MANIFEST,
                                           "n_instances": N_CORPUS}], "seeds": list(SEEDS)},
              "config": {"split": {"n_val": N_VAL, "seed": 1}},
              "results": {"e8": {"metrics": {"cells": {
                  "labels_anchor": {"1024": _cell({m: [x * 0.5 for x in ld[m]]
                                                   for m in METRICS})},
                  "ar": {"1024": copy.deepcopy(rep["cells"]["ar"]["1024"])},
                  "labels": {"1024": copy.deepcopy(rep["cells"]["labels"]["1024"])}}}}}}
    return {"rep": rep, "cfg": cfg, "source": source, "ld": ld, "lk": lk, "ar": ar,
            "entries": {"k3d_v1": config_sha256(cfg)}}


def _run(w, **kw):
    return ADJ.adjudicate_k3d(w["rep"], w["cfg"], w["entries"], w["source"],
                              w["cfg"]["source"]["report_sha256"], "prereg-k3d", **kw)


def _guard_by_hand(base: list, new: list) -> dict:
    b = [float(np.median(x)) for x in base]
    a = [float(np.median(x)) for x in new]
    mb, ma = statistics.fmean(b), statistics.fmean(a)
    se = math.sqrt(statistics.variance(b) / 3 + statistics.variance(a) / 3) / mb
    tau = max(0.10, 2 * se)
    return {"rel": ma / mb - 1, "tau": tau, "se": se}


# -------------------------------------------------------------- verdicts --

@pytest.mark.parametrize("ratio,verdict,note", [(0.5, "SUPPORTED", None),
                                                 (1.0, "NOT SUPPORTED", None),
                                                 (2.0, "NOT SUPPORTED", "worse beyond the guard")])
def test_the_verdicts_are_the_guard_on_the_medians(ratio, verdict, note):
    w = _world(ratio_gap=ratio, ratio_vm=ratio)
    res = _run(w)
    for h, m in (("H2a-3D", "energy_gap_rel"), ("H2b-3D", "vm_rel_l2")):
        v = res[h]
        hand = _guard_by_hand(w["ld"][m], w["lk"][m])
        assert v["verdict"] == verdict and v.get("note") == note, h
        assert v["metric"] == m and v["statistic"] == "per-seed medians"
        assert v["rel_change"] == pytest.approx(hand["rel"], rel=1e-12)
        assert v["threshold"] == pytest.approx(hand["tau"], rel=1e-12)
        assert v["se_rel"] == pytest.approx(hand["se"], rel=1e-12)
        assert (hand["rel"] < -hand["tau"]) == (verdict == "SUPPORTED")
        assert v["base_per_seed"] == [float(np.median(x)) for x in w["ld"][m]]
        b = v["beside"]
        assert set(b) == {"seed_means", "seed_means_welch_95", "welch_95",
                          "instance_resampling_95", "seed_means_show_the_direction"}
        lo, hi = b["instance_resampling_95"]["low"], b["instance_resampling_95"]["high"]
        assert lo <= v["rel_change"] <= hi
    assert res["statistic"] == "per-seed medians" and res["deviations"] == []


def test_a_reference_carried_by_one_instance_leaves_the_means_without_a_reduction():
    """Phase-2b's L_D: one instance of one seed at about 1e5 times the rest.
    The seed means cannot show L_K's halving (tau >= 1.98); the medians do."""
    w = _world(ratio_gap=0.5)
    ev = w["rep"]["cells"]["labels"]["1024"]["per_seed_eval"][1]
    ev["per_instance"]["energy_gap_rel"][107] = 23726.9
    res = _run(w)
    v = res["H2a-3D"]
    assert v["verdict"] == "SUPPORTED"
    means = v["beside"]["seed_means"]
    assert means["threshold"] > 1.9 and not means["lower"]       # the guard cannot read lower
    assert means["rel_change"] < 0                              # but the sign shows it
    assert v["beside"]["seed_means_show_the_direction"] is True
    assert v["beside"]["seed_means_welch_95"]["low"] < 0


def test_non_finite_values():
    w = _world()
    w["rep"]["cells"]["labels_knorm"]["1024"]["per_seed_eval"][2]["per_instance"][
        "vm_rel_l2"][5] = float("nan")
    res = _run(w)
    assert res["H2b-3D"]["verdict"] == "NOT SUPPORTED (diverged)"
    assert res["H2a-3D"]["verdict"] == "SUPPORTED"
    json.dumps(ADJ.jsonable(res), allow_nan=False)
    # a non-finite reference value: the content check refuses such a report, so the
    # rule itself is checked (B is checked first, so also when A has one too)
    w = _world()
    base = [np.array(x, float) for x in w["ld"]["energy_gap_rel"]]
    new = [np.array(x, float) for x in w["lk"]["energy_gap_rel"]]
    base[0][0], new[0][0] = float("inf"), float("nan")
    v = ADJ.verdict(base, new, "test", "energy_gap_rel")
    assert v["verdict"] == "NOT EVALUATED" and "the reference" in v["reason"]
    w["rep"]["cells"]["labels"]["1024"]["per_seed_eval"][0]["per_instance"][
        "energy_gap_rel"][0] = float("inf")
    with pytest.raises(ValueError, match="do not reproduce"):
        _run(w)


@pytest.mark.parametrize("ar_ratio,label", [
    (0.5, "the stiffness-norm transformer lower beyond the guard"),
    (2.0, "the label-free transformer lower beyond the guard"),
    (1.0, "no difference shown (within the guard)")])
def test_h3_reads_one_of_its_labels(ar_ratio, label):
    w = _world(ar_ratio=ar_ratio)
    h3 = _run(w)["H3-3D"]
    assert h3["reading"] == label and h3["metric"] == "energy_gap_rel"
    hand = _guard_by_hand(w["ar"]["energy_gap_rel"], w["lk"]["energy_gap_rel"])
    assert h3["rel_change"] == pytest.approx(hand["rel"], rel=1e-12)
    assert "roles_exchanged" in h3 and "verdict" not in h3
    w["rep"]["cells"]["labels_knorm"]["1024"]["per_seed_eval"][1]["per_instance"][
        "energy_gap_rel"][3] = float("nan")
    assert _run(w)["H3-3D"]["reading"] == "the stiffness-norm transformer diverged"


def test_the_secondary_readings():
    w = _world()
    sec = _run(w)["secondary"]
    assert set(sec["comparisons"]) == set(METRICS)
    for m, per in sec["comparisons"].items():
        assert set(per) == {"labels_knorm_vs_labels", "labels_knorm_vs_ar", "ar_vs_labels"}
        for c in per.values():
            assert set(c) == {"medians", "means"}
    assert sec["comparisons"]["crit_recall"]["ar_vs_labels"]["medians"][
        "better_direction"] == "higher"
    p = sec["pairing"]["labels_knorm_vs_labels"]["energy_gap_rel"]
    assert p == {"first_lower": 768, "ties": 0, "pairs": 768}
    assert sec["worse_than_zero"]["labels"] == {"count": 0, "of": 768, "non_finite": 0,
                                                 "values": []}
    assert "not_evaluated" not in sec["labels_energy"]
    assert sec["holdout"] == {"not_evaluated": "the configuration names no holdout set"} or \
        "not_evaluated" in sec["holdout"]
    assert sec["training"]["s0"]["loss_last_epoch"] == 0.2
    assert sec["training"]["s0"]["loss_by_epoch"] == [0.9, 0.2]
    t = sec["seed_table"]["labels"]["energy_gap_rel"]
    assert t["median_per_seed"] == [float(np.median(x)) for x in w["ld"]["energy_gap_rel"]]


# -------------------------------------------------------------- refusals --

def _edit(path: str, value):
    def f(w):
        obj = w["rep"]
        keys = path.split(".")
        for k in keys[:-1]:
            obj = obj[int(k)] if isinstance(obj, list) else obj[k]
        last = keys[-1]
        if value is _DELETE:
            del obj[last]
        elif isinstance(obj, list):
            obj[int(last)] = value
        else:
            obj[last] = value
    return f


_DELETE = object()
REFUSALS = {
    "not guard-verified": _edit("prereg", None),
    "another prereg hash": _edit("prereg.config_sha256", "0" * 64),
    "another configuration": _edit("config.content_tol", 0.01),
    "another commit": _edit("provenance.git", "prereg-k3d-dirty"),
    "another source report": _edit("provenance.source_report_sha256", "1" * 64),
    "another corpus": _edit("provenance.datasets", [{"manifest_sha256": "2" * 64}]),
    "other seeds": _edit("seeds", [0, 1]),
    "a missing row": _edit("cells.ar", _DELETE),
    "a missing evaluation": _edit("cells.labels.1024.per_seed_eval", []),
    "a missing seed value": _edit("cells.labels_knorm.1024.per_seed_eval.0.vm_rel_l2", None),
    "short arrays": _edit("cells.labels.1024.per_seed_eval.1.per_instance.disp_rel_l2", [0.1]),
    "a failed content check": _edit("content_checks.ar_s2.ok", False),
    "a missing content check": _edit("content_checks.labels_s0", _DELETE),
    "another stored state": _edit("reused.labels_s1.sha256", "3" * 64),
    "fewer epochs": _edit("per_seed.s1.train.epochs_run", 199),
    "another loss": _edit("per_seed.s0.train.loss", "disp"),
    "other instances": _edit("per_seed.s2.train.files", ["instance_00000.npz"]),
    "no state": _edit("per_seed.s0.state", {}),
}


@pytest.mark.parametrize("what", sorted(REFUSALS))
def test_refusals(what):
    w = _world()
    if what == "another configuration":
        w["rep"]["config"] = copy.deepcopy(w["cfg"])
    REFUSALS[what](w)
    with pytest.raises(ValueError, match="adjudication refused"):
        _run(w)


def test_the_checks_of_the_inputs_themselves():
    w = _world()
    with pytest.raises(ValueError, match="source report"):
        ADJ.adjudicate_k3d(w["rep"], w["cfg"], w["entries"], w["source"], "4" * 64,
                           "prereg-k3d")
    with pytest.raises(ValueError, match="verified hash"):
        ADJ.adjudicate_k3d(w["rep"], w["cfg"], {"k3d_v1": "5" * 64}, w["source"],
                           w["cfg"]["source"]["report_sha256"], "prereg-k3d")


# ------------------------------------------------------------ deviations --

def test_deviations():
    w = _world()
    r = w["rep"]
    r["reused_evaluations_from_disk"] = True
    r["per_seed"]["s0"]["from_disk"] = True
    r["per_seed"]["s1"]["train"]["resumed_from_epoch"] = 57
    r["per_seed"]["s1"]["machine"]["resumed_on"] = [{"host": "box2", "gpu_driver": "580.95.05"}]
    r["per_seed"]["s2"]["train"]["activation_checkpointing"] = True
    r["torch"]["version"] = "2.13.0+cu130"
    r["gpu"]["gpu"] = "NVIDIA H100"
    r["holdout"] = {"skipped": True}
    status = "k3d.log start a box\nk3d.log exit=137\nk3d.log start b box2\nk3d.log exit=0\n"
    dev = _run(w, status_text=status, run_logs=2)["deviations"]
    want = ("reused.json", "L_K seed 0: taken from an earlier attempt",
            "L_K seed 1: resumed from its epoch checkpoint at epoch 57",
            "L_K seed 1: trained on more than one machine", "L_K seed 2: activation checkpointing on",
            "the seeds ran on more than one machine", "torch '2.13.0+cu130'",
            "GPU 'NVIDIA H100'",
            "the holdout set was skipped", "2 started, exit codes [137, 0]",
            "2 run logs in the return")
    for s in want:
        assert any(s in d for d in dev), s
    assert len(dev) == len(want)
    w = _world()
    for s in SEEDS:
        w["rep"]["per_seed"][f"s{s}"]["machine"] = {"start": {"host": "h", "gpu_driver": None},
                                                   "resumed_on": [],
                                                   "end": {"host": "h", "gpu_driver": None}}
    dev = _run(w, status_text="k3d.log start a h\nk3d.log exit=0\n", run_logs=1)["deviations"]
    assert dev == [f"L_K seed {s}: its GPU driver was not read" for s in SEEDS]


# --------------------------------------------------------------- holdout --

def _holdout(tmp: Path, w: dict, files: list) -> tuple:
    """The run's holdout arrays for `files` (L_K at half L_D), its record in
    the report, and PREREG_HOLDOUT's labels manifest record."""
    from fejepa.metrics import FIELD_KEYS

    rng = np.random.default_rng(3)
    n = len(files)
    M = np.zeros((3, 3, n, 5))
    for k, m in enumerate(FIELD_KEYS):
        base = 0.25 * np.exp(rng.normal(0, 0.3, (3, n)))
        M[1, :, :, k] = base
        M[2, :, :, k] = base * (0.5 if m in ("energy_gap_rel", "vm_rel_l2") else 0.9)
        M[0, :, :, k] = base / 20
    G = np.full((3, 3, n, 4), 0.1)
    G[1, 0, 0, 2] = 3.0
    P = np.where(G > 1, 1.0, -1.0)
    npz = tmp / "holdout_arrays.npz"
    np.savez(npz, rows=np.array(["ar", "labels", "labels_knorm"]), seeds=np.array(SEEDS),
             metrics=np.array(FIELD_KEYS), files=np.array(files), values=M, gap_load=G,
             pi_load=P)
    man = tmp / "manifest.json"
    man.write_text('{"set": "h3d"}')
    w["rep"]["holdout"] = {"set": "h3d", "n": n,
                           "labels_manifest_sha256": hashlib.sha256(man.read_bytes()).hexdigest(),
                           "arrays": npz.name,
                           "arrays_sha256": hashlib.sha256(npz.read_bytes()).hexdigest()}
    return npz, man


def test_the_holdout_readings(tmp_path):
    from fejepa.analysis.holdout import holdout_names, load_spec

    spec = ROOT / "configs" / "holdout_v1.json"
    names = holdout_names(load_spec(spec)["sets"]["h3d"])
    w = _world()
    npz, man = _holdout(tmp_path, w, names)
    res = _run(w, holdout_npz=npz, holdout_manifest=man, holdout_spec=spec)
    h = res["secondary"]["holdout"]
    assert "not_evaluated" not in h, h
    assert h["n"] == 686
    for name in ("H2a-3D", "H2b-3D"):
        assert h["hypotheses"][name]["direction"] == "lower"
        assert h["hypotheses"][name]["same_direction"] is True
        assert h["hypotheses"][name]["validation_verdict"] == "SUPPORTED"
    assert h["hypotheses"]["H3-3D"]["direction"] == "worse"
    assert h["worse_than_zero_load_cases"]["labels_s0"]["worse"] == 1
    assert h["worse_than_zero_load_cases"]["labels_s0"]["sign_mismatch"] == 0
    # each guard
    other = tmp_path / "other.json"
    other.write_text("{}")
    cases = {"PREREG_HOLDOUT's returned one": dict(holdout_manifest=other),
             "is not committed": dict(holdout_manifest=tmp_path / "absent.json"),
             "holds no holdout_arrays.npz": dict(holdout_npz=None, holdout_manifest=man)}
    for msg, kw in cases.items():
        kw = {"holdout_npz": npz, "holdout_manifest": man, **kw}
        out = _run(w, holdout_spec=spec, **kw)["secondary"]["holdout"]
        assert msg in out["not_evaluated"], (msg, out)
    w2 = copy.deepcopy(w)
    w2["rep"]["holdout"]["arrays_sha256"] = "6" * 64
    assert "is not the run's" in _run(w2, holdout_npz=npz, holdout_manifest=man,
                                      holdout_spec=spec)["secondary"]["holdout"]["not_evaluated"]
    npz2, man2 = _holdout(tmp_path, w2, names[::-1])
    assert "pool order" in _run(w2, holdout_npz=npz2, holdout_manifest=man2,
                                holdout_spec=spec)["secondary"]["holdout"]["not_evaluated"]
    w3 = _world()
    w3["rep"]["holdout"] = {"skipped": True}
    assert "skipped" in _run(w3)["secondary"]["holdout"]["not_evaluated"]


# ---------------------------------------------------------------- return --

def test_a_return_holds_exactly_the_files_its_provenance_lists(tmp_path):
    ret = tmp_path / "k3d_return"
    ret.mkdir()
    (ret / "report.json").write_text(json.dumps({"x": 1}))
    (ret / "status.txt").write_text("k3d.log start t box\nk3d.log exit=0\n")
    (ret / "k3d.log").write_text("log\n")

    def listing():
        lines = [f"{hashlib.sha256((ret / f).read_bytes()).hexdigest()}  ./{f}"
                 for f in sorted(p.name for p in ret.iterdir() if p.name != "provenance.txt")]
        return ("HEAD " + "a" * 40 + "\ntree " + "b" * 40 + "\n--- states ---\n"
                + "c" * 64 + "  runs/k3d/labels_knorm_b1024_s0.pt\n--- files ---\n"
                + "\n".join(lines) + "\n")

    (ret / "provenance.txt").write_text(listing())
    rep, sha, status, prov, logs = ADJ.load_return(ret)
    assert rep == {"x": 1} and logs == ["k3d.log"] and status.endswith("exit=0\n")
    assert sha == hashlib.sha256((ret / "report.json").read_bytes()).hexdigest()
    assert ADJ.provenance_commit(prov) == {"HEAD": "a" * 40, "tree": "b" * 40}
    (ret / ".DS_Store").write_text("x")
    with pytest.raises(SystemExit, match="present only"):
        ADJ.load_return(ret)
    (ret / ".DS_Store").unlink()
    (ret / "report.json").write_text(json.dumps({"x": 2}))
    with pytest.raises(SystemExit, match="not the files the box hashed"):
        ADJ.load_return(ret)
    (ret / "provenance.txt").write_text(listing())
    (ret / "k3d.log").unlink()
    with pytest.raises(SystemExit, match="listed only"):
        ADJ.load_return(ret)
    (ret / "status.txt").unlink()
    with pytest.raises(SystemExit, match="lacks"):
        ADJ.load_return(ret)


def test_the_status_file_is_read_as_the_runbook_writes_it():
    t = ("k3d.log start 2026-10-21T10:00:00Z box\nk3d.log exit=130\n"
         "k3d.log start 2026-10-21T11:00:00Z box\nk3d.log exit=0\n")
    assert ADJ.status_attempts(t) == {"starts": 2, "exits": [130, 0]}
    assert ADJ.status_attempts("") == {"starts": 0, "exits": []}


# ------------------------------------------------- after the first reviews --

def test_the_content_check_is_recomputed_from_the_arrays():
    w = _world()
    pi = w["rep"]["cells"]["labels"]["1024"]["per_seed_eval"][1]["per_instance"]
    pi["energy_gap_rel"] = [2 * x for x in pi["energy_gap_rel"]]   # the recorded check says ok
    with pytest.raises(ValueError, match="recomputed from the report's arrays"):
        _run(w)
    w = _world()
    pi = w["rep"]["cells"]["labels"]["1024"]["per_seed_eval"][1]["per_instance"]
    pi["energy_gap_rel"][107] *= 1.5                 # one instance: the median check passes
    res = _run(w)
    assert res["content_checks"]["recomputed"]["labels_s1"]["ok"] is True
    assert any("stored state labels_s1: largest relative deviation above content_tol in "
               "['energy_gap_rel']" in d for d in res["deviations"])


def test_the_seed_means_welch_interval_and_the_gap_closure():
    w = _world(ratio_gap=0.5, ratio_vm=0.5)
    res = _run(w)
    b = res["H2b-3D"]["beside"]
    assert b["seed_means_welch_95"]["rel_change"] == pytest.approx(
        b["seed_means"]["rel_change"], rel=1e-12)
    gc = res["secondary"]["gap_closure"]["vm_rel_l2"]
    for stat, fn in (("medians", np.median), ("means", np.mean)):
        v = {r: float(np.mean([fn(x) for x in w[k]["vm_rel_l2"]]))
             for r, k in (("labels", "ld"), ("labels_knorm", "lk"), ("ar", "ar"))}
        want = (v["labels"] - v["labels_knorm"]) / (v["labels"] - v["ar"])
        assert gc[stat]["closure"] == pytest.approx(want, rel=1e-9)
    assert gc["medians"]["closure"] == pytest.approx(0.5 / 0.95, rel=1e-9)


def test_per_seed_torch_and_machines():
    w = _world()
    ps = w["rep"]["per_seed"]
    ps["s0"]["torch"] = {"version": "2.12.1+cu130", "gpu": "NVIDIA GeForce RTX 5090"}
    ps["s1"]["torch"] = {"version": "2.13.0+cu130", "gpu": "NVIDIA GeForce RTX 5090"}
    # a driver not read on one record is not another machine
    ps["s2"]["machine"]["end"] = {"host": "box", "gpu_driver": None}
    dev = _run(w, status_text="k3d.log start a box\nk3d.log exit=0\n", run_logs=1)["deviations"]
    assert dev == ["L_K seed 1: trained under torch '2.13.0+cu130' on 'NVIDIA GeForce RTX 5090'"]
    ps["s2"]["machine"]["end"] = {"host": "box", "cpu": "Xeon", "gpu_driver": "595.71.05",
                                  "gpu_uuid": "GPU-b"}
    ps["s2"]["machine"]["start"] = {"host": "box", "cpu": "Xeon", "gpu_driver": "595.71.05",
                                    "gpu_uuid": "GPU-a"}
    dev = _run(w, status_text="k3d.log start a box\nk3d.log exit=0\n", run_logs=1)["deviations"]
    assert any(d.startswith("L_K seed 2: trained on more than one machine") for d in dev)
    assert "the seeds ran on more than one machine" in dev


def _provenance(w, head="c" * 40, states=None, aside=()) -> str:
    states = states or {s: w["rep"]["per_seed"][f"s{s}"]["state"]["sha256"] for s in SEEDS}
    lines = ["HEAD " + head, "tree " + "d" * 40, "--- runs/k3d ---",
             "-rw-r--r-- 1 root root 1 2026-10-21 10:00:00.0 +0800 report.json",
             *[f"-rw-r--r-- 1 root root 1 2026-10-21 10:00:00.0 +0800 {n}" for n in aside],
             "--- states ---",
             *[f"{states[s]}  runs/k3d/labels_knorm_b1024_s{s}.pt" for s in SEEDS],
             "--- files ---"]
    return "\n".join(lines) + "\n"


def test_the_return_against_the_report(tmp_path):
    w = _world()
    for s in SEEDS:
        ps = w["rep"]["per_seed"][f"s{s}"]
        ps["commit"] = "c" * 40
        ps["state"]["path"] = f"/root/autodl-tmp/FE-JEPA/runs/k3d/labels_knorm_b1024_s{s}.pt"
        (tmp_path / f"seed_{s}.json").write_text(json.dumps(ps))
    w["rep"]["provenance"]["commit"] = "c" * 40
    (tmp_path / "reused.json").write_text(json.dumps({"commit": "c" * 40}))
    res = _run(w, prov_text=_provenance(w), ret=tmp_path)
    assert not [d for d in res["deviations"] if "seed_" in d or "state on the box" in d]
    bad = _provenance(w, states={0: "e" * 64, 1: w["rep"]["per_seed"]["s1"]["state"]["sha256"],
                                 2: w["rep"]["per_seed"]["s2"]["state"]["sha256"]},
                      aside=["seed_1.json.unusable.20261021-101010"])
    rec = json.loads((tmp_path / "seed_2.json").read_text())
    rec["train"]["epochs_run"] = 7
    (tmp_path / "seed_2.json").write_text(json.dumps(rec))
    dev = _run(w, prov_text=bad, ret=tmp_path)["deviations"]
    assert any(d.startswith("L_K seed 0: the state on the box") for d in dev)
    assert any(d.startswith("files moved aside under runs/k3d: "
                            "['seed_1.json.unusable.20261021-101010']") for d in dev)
    assert "seed_2.json is not the report's record of seed 2" in dev
    # every seed and the stored states' evaluations by the return's commit
    with pytest.raises(ValueError, match="another commit"):
        _run(w, prov_text=_provenance(w, head="f" * 40), ret=tmp_path)
    (tmp_path / "reused.json").write_text(json.dumps({"commit": "a" * 40}))
    with pytest.raises(ValueError, match="stored states were evaluated by another commit"):
        _run(w, prov_text=_provenance(w), ret=tmp_path)


# ------------------------------------- after the independent re-implementation --

def test_the_rule_at_its_edges():
    """A reference whose mean is not positive is NOT EVALUATED; a per-seed
    value beyond 1e150 counts as non-finite; a diverged verdict records no
    guard; NOT EVALUATED records the per-seed values; the roles-exchanged
    reading is always reported."""
    zeros = [np.zeros(N_VAL) for _ in SEEDS]
    pos = [np.full(N_VAL, 0.2) for _ in SEEDS]
    v = ADJ.verdict(zeros, zeros, "t", "energy_gap_rel")
    assert v["verdict"] == "NOT EVALUATED" and "not positive" in v["reason"]
    assert v["base_per_seed"] == [0.0, 0.0, 0.0]
    huge = [np.full(N_VAL, 1e200 * (k + 1)) for k in range(3)]
    v = ADJ.verdict(pos, huge, "t", "energy_gap_rel")
    assert v["verdict"] == "NOT SUPPORTED (diverged)"
    assert v["threshold"] is None and v["worse"] is None and v["lower"] is None
    assert ADJ.verdict(huge, pos, "t", "energy_gap_rel")["verdict"] == "NOT EVALUATED"
    h = ADJ.h3_reading([np.full(N_VAL, np.nan)] * 3, pos)
    assert h["reading"] == "NOT EVALUATED" and "roles_exchanged" in h
    assert h["roles_exchanged"]["diverged"] is True


def test_the_seed_means_show_a_direction_by_their_sign():
    assert ADJ._shows({"rel_change": -0.01}, "lower") is True
    assert ADJ._shows({"rel_change": 0.01}, "lower") is False
    assert ADJ._shows({"rel_change": 0.3}, "worse") is True
    assert ADJ._shows({"rel_change": -0.3}, "neither") is None
    assert ADJ._shows({"not_evaluated": "x"}, "lower") is None


# ------------------------------------------- after the third round of reviews --

def test_the_values_worse_than_the_zero_field_are_listed():
    """PREREG_K3D Sec. 5 lists them: seed, validation instance (index and
    file; instance 107 is instance_00485.npz) and value; non-finite ones too."""
    assert ADJ.val_names(N_CORPUS, N_VAL, 1)[107] == "instance_00485.npz"
    w = _world()
    pi = w["rep"]["cells"]["labels"]["1024"]["per_seed_eval"]
    pi[0]["per_instance"]["energy_gap_rel"][107] = 2.9
    pi[2]["per_instance"]["energy_gap_rel"][5] = 1.5
    wz = _run(w)["secondary"]["worse_than_zero"]["labels"]
    assert wz["count"] == 2 and wz["non_finite"] == 0
    assert wz["values"] == [
        {"seed": 0, "instance": 107, "file": "instance_00485.npz", "value": 2.9},
        {"seed": 2, "instance": 5, "file": ADJ.val_names(N_CORPUS, N_VAL, 1)[5], "value": 1.5}]
    w = _world()
    w["rep"]["cells"]["labels_knorm"]["1024"]["per_seed_eval"][1]["per_instance"][
        "energy_gap_rel"][9] = float("nan")
    wz = _run(w)["secondary"]["worse_than_zero"]["labels_knorm"]
    assert wz["non_finite"] == 1 and wz["values"][0]["seed"] == 1 \
        and wz["values"][0]["instance"] == 9 and math.isnan(wz["values"][0]["value"])


def test_a_diverged_seed_mean_reading_shows_worse():
    assert ADJ._shows({"diverged": True, "rel_change": None}, "worse") is True
    assert ADJ._shows({"diverged": True, "rel_change": None}, "lower") is False


def test_training_tf32_a_missing_reused_json_and_holdout_preconditions(tmp_path):
    w = _world()
    w["rep"]["per_seed"]["s1"]["train"]["runtime"] = {"tf32_matmul": False}
    w["rep"]["per_seed"]["s2"]["train"]["runtime"] = {"tf32_matmul": True}
    dev = _run(w, status_text="k3d.log start a box\nk3d.log exit=0\n", run_logs=1)["deviations"]
    assert dev == ["L_K seed 1: TF32 matmul off in training, the source run's policy is on"]
    # a return without reused.json
    w = _world()
    for s in SEEDS:
        ps = w["rep"]["per_seed"][f"s{s}"]
        ps["commit"] = "c" * 40
        ps["state"]["path"] = f"/x/runs/k3d/labels_knorm_b1024_s{s}.pt"
        (tmp_path / f"seed_{s}.json").write_text(json.dumps(ps))
    w["rep"]["provenance"]["commit"] = "c" * 40
    dev = _run(w, prov_text=_provenance(w), ret=tmp_path)["deviations"]
    assert any(d.startswith("the return holds no reused.json") for d in dev)
    # the holdout set evaluated by the run but its readings not evaluated
    from fejepa.analysis.holdout import holdout_names, load_spec

    spec = ROOT / "configs" / "holdout_v1.json"
    names = holdout_names(load_spec(spec)["sets"]["h3d"])
    w = _world()
    npz, man = _holdout(tmp_path, w, names)
    other = tmp_path / "other.json"
    other.write_text("{}")
    dev = _run(w, holdout_npz=npz, holdout_manifest=other, holdout_spec=spec)["deviations"]
    assert any(d.startswith("the holdout readings are not evaluated: the run's holdout labels "
                            "manifest is not PREREG_HOLDOUT's") for d in dev)
    dev = _run(w, holdout_npz=npz, holdout_manifest=man, holdout_spec=spec)["deviations"]
    assert not any("holdout" in d for d in dev)


def test_a_skipped_holdout_set_needs_two_holdout_failures_before_it(tmp_path):
    """RUNBOOK F1': --skip-holdout only after two consecutive attempts that
    ended in a traceback through the holdout evaluation; otherwise recorded."""
    tb = ("Traceback (most recent call last):\n"
          '  File "/root/autodl-tmp/FE-JEPA/scripts/k3d_train.py", line 870, in _run\n'
          '  File "/root/autodl-tmp/FE-JEPA/scripts/k3d_train.py", line 720, in '
          "holdout_evaluation\nRuntimeError: CUDA error\n")
    w = _world()
    w["rep"]["holdout"] = {"skipped": True}
    for s in SEEDS:
        ps = w["rep"]["per_seed"][f"s{s}"]
        ps["commit"] = "c" * 40
        ps["state"]["path"] = f"/x/runs/k3d/labels_knorm_b1024_s{s}.pt"
        (tmp_path / f"seed_{s}.json").write_text(json.dumps(ps))
    w["rep"]["provenance"]["commit"] = "c" * 40
    (tmp_path / "reused.json").write_text(json.dumps({"commit": "c" * 40}))
    (tmp_path / "k3d.log.20261021-100000").write_text("[k3d] holdout h3d: 1 instances\n" + tb)
    (tmp_path / "k3d.log.20261021-110000").write_text("[k3d] holdout h3d: 1 instances\n" + tb)
    (tmp_path / "k3d.log").write_text("[k3d] report -> x\n")
    dev = _run(w, prov_text=_provenance(w), ret=tmp_path)["deviations"]
    assert "the holdout set was skipped (--skip-holdout)" in dev
    assert not any("without two consecutive failures" in d for d in dev)
    (tmp_path / "k3d.log.20261021-110000").write_text("[k3d] holdout h3d: 1 instances\n"
                                                     "STOP: no GPU\n")
    dev = _run(w, prov_text=_provenance(w), ret=tmp_path)["deviations"]
    assert any("skipped without two consecutive failures" in d for d in dev)
