"""Tests of gate G-C2.3's own code (c23/): the configuration against G-C2.2's, the third held-out sample, the
self-check (spread, flags, S1 to S3, the ranking), the wording of the comparison, the identity check, the verdict
step on rows files written here with made-up errors and forces (what makes rows stale, the first part 1 kept apart,
the words of each outcome), the list of stamped code, the entry point, the supervised training (the recipe, the
initial weights, resume) and the runbook's commands in their order on a small configuration. The host check
c23/smoke.py runs the same pipeline with worker processes and is run apart; the code shared with G-C2.2 is tested in
test_c22.py and test_c2.py."""
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

from c2.evaluate import _summary
from c22 import config as base
from c22.train import PREDICTION_FILES
from c23 import data
from c23.config import (config, sha256, BASE_SHA256, THIRD_EVAL_SEED, FAMILY_SEEDS_SEEN, SPREAD_THRESHOLD,
                        SUPERVISED_LABEL_LEVELS, G22_PER_SEED)
from c23.evaluate import auc, self_check, compare, identity, verdict, _stats, _inputs

REPO = os.environ.get("FEJEPA_REPO")
JOINT = Path(__file__).resolve().parents[1]
TEST_SEEDS = (7, 8, 101, 102)   # family seeds seen before G-C2.1's stamp: the tests never draw a member of this gate


def reduced():
    cfg = copy.deepcopy(config())
    d = cfg["data"]
    d["n_train"], d["n_third"], d["n_eval"] = 3, 2, 2
    d["train_seed"], d["third_eval_seed"], d["eval_seed"], d["former_eval_seed"] = 7, 102, 8, 101
    d["seeds_seen_before_stamp"] = [s for s in d["seeds_seen_before_stamp"] if s not in TEST_SEEDS]
    return cfg


def test_configuration_is_the_stamped_base_with_the_listed_changes():
    cfg, b = config(), base.config()
    assert sha256(b) == BASE_SHA256 and cfg["base"]["config_sha256"] == BASE_SHA256
    assert cfg["gate"] == "G-C2.3" and sha256(cfg) != BASE_SHA256
    same = ("family", "model", "map", "repository_code")
    assert all(cfg[k] == b[k] for k in same)
    assert cfg["training"] == b["training"]                              # the recipe and the schedule are G-C2.2's
    changed = {k for k in cfg["data"] if cfg["data"][k] != b["data"].get(k)}
    assert changed == {"third_eval_seed", "n_third", "seeds_seen_before_stamp", "train_label_levels_mm",
                       "n_train_labelled"}
    assert cfg["data"]["train_label_levels_mm"] == SUPERVISED_LABEL_LEVELS and len(SUPERVISED_LABEL_LEVELS) == 8
    # every level at which a network is read lies within the labelled range: the base level of the condensed reading
    # and the evaluation levels; no evaluation level but the largest is a labelled level
    base_level = cfg["evaluation"]["readings"]["condensed"]["base_level_mm"]
    assert min(SUPERVISED_LABEL_LEVELS) == base_level == cfg["training"]["D_min_mm"] == 0.1
    assert max(SUPERVISED_LABEL_LEVELS) == max(cfg["data"]["eval_levels_mm"]) == cfg["family"]["D_max_mm"] == 8.0
    assert set(SUPERVISED_LABEL_LEVELS) & set(cfg["data"]["eval_levels_mm"]) == {8.0}
    assert len(SUPERVISED_LABEL_LEVELS) >= cfg["training"]["fields_per_step"]
    assert cfg["data"]["n_train_labelled"] == cfg["data"]["n_train"] == 512
    assert cfg["evaluation"]["readings"] == b["evaluation"]["readings"]
    assert cfg["evaluation"]["sets"] == ["third", "eval", "tested"] and cfg["evaluation"]["judged_set"] == "third"
    assert cfg["arms"]["label_free"]["seeds"] == cfg["arms"]["supervised_512"]["seeds"] == [5, 6, 7]
    assert cfg["arms"]["supervised_512"]["epochs"] == b["arms"]["label_free"]["epochs"] == 200
    assert cfg["self_check"]["threshold"] == SPREAD_THRESHOLD == 0.0045
    assert cfg["arms"]["label_free"]["identity"]["values"] == G22_PER_SEED


def test_the_held_out_seed_is_fresh():
    cfg = config()
    d = cfg["data"]
    assert THIRD_EVAL_SEED not in FAMILY_SEEDS_SEEN and base.FRESH_EVAL_SEED in FAMILY_SEEDS_SEEN
    assert d["third_eval_seed"] == THIRD_EVAL_SEED and d["seeds_seen_before_stamp"] == FAMILY_SEEDS_SEEN
    assert THIRD_EVAL_SEED not in (d["train_seed"], d["eval_seed"], d["former_eval_seed"])
    assert {d["train_seed"], d["eval_seed"], d["former_eval_seed"]} <= set(FAMILY_SEEDS_SEEN)
    # the two refusals of members(), on the small configuration: no test calls members() with the gate's seed
    for seen in (7, 8, 101):                                # the held-out seed equals another split's seed
        bad = reduced()
        bad["data"]["third_eval_seed"] = seen
        with pytest.raises(RuntimeError, match="not fresh"):
            data.members(bad)
    bad = reduced()
    bad["data"]["seeds_seen_before_stamp"].append(102)      # the held-out seed is in the list of seen seeds
    with pytest.raises(RuntimeError, match="used before the stamp"):
        data.members(bad)


def test_members_and_splits_on_seen_seeds():
    m = data.members(reduced())
    assert [s for _, s, _ in m].count("train") == 3
    assert [i for i, s, _ in m if s == "third"] == ["third_0000", "third_0001"]
    assert {s for _, s, _ in m} == set(data.SPLITS) and len({i for i, _, _ in m}) == len(m)
    third = [q for _, s, q in m if s == "third"]
    others = [q for _, s, q in m if s in ("train", "eval")]
    assert not any(s == "former" for _, s, _ in m)                       # G-C2.1's held-out members are not used
    assert all(q not in others for q in third)


def rows(F, err):
    return [{"F": float(f), "abs_curve_err": float(e)} for f, e in zip(F, err)]


def test_auc_counts_ties_as_half():
    assert auc([1, 2, 3, 4], [False, False, True, True]) == 1.0
    assert auc([4, 3, 2, 1], [False, False, True, True]) == 0.0
    assert auc([1, 1, 1, 1], [False, True, False, True]) == 0.5
    assert auc([1, 2, 2, 3], [False, False, True, True]) == pytest.approx(0.875)
    assert auc([1, 2], [False, False]) is None and auc([1, 2], [True, True]) is None


def test_self_check_flags_and_criteria():
    sc = {"threshold": 0.0045}
    ids = ["a", "b"]
    # member a: the runs agree (spread 0.002 and 0.004); member b: they do not (0.01 and 0.2)
    F = {5: {"a": [100.0, 100.0], "b": [100.0, 100.0]},
         6: {"a": [100.2, 100.4], "b": [101.0, 120.0]},
         7: {"a": [100.1, 100.2], "b": [100.5, 110.0]}}
    small, big = [0.01, 0.02], [0.06, 0.30]
    by = {s: {"a": rows(F[s]["a"], small), "b": rows(F[s]["b"], big)} for s in F}
    r = self_check(sc, by, ids)
    assert r["pairs"] == 4 and r["flagged"] == 2 and r["by_member"]["a"]["flagged"] == [False, False]
    assert r["by_member"]["b"]["flagged"] == [True, True]
    assert r["by_member"]["a"]["spread"][0] == pytest.approx(0.2 / 100.1)
    assert r["S1"] and r["S2"] and not r["S3"] and r["verdict"] == "FAIL"          # half of the pairs are flagged
    assert r["pairs_above"]["0.1"] == {"total": [1, 1, 1], "flagged": [1, 1, 1]}
    assert r["ranking"]["auc_above_0.05"] == [1.0, 1.0, 1.0] and r["ranking"]["R"] == "HOLDS"
    # a large error where the runs agree: S1 and S2 fail
    by2 = copy.deepcopy(by)
    by2[6]["a"][1]["abs_curve_err"] = 0.11
    r2 = self_check(sc, by2, ids)
    assert not r2["S1"] and r2["not_flagged_pairs_above_0.10_in_any_run"] == 1
    assert r2["not_flagged_readings"] == 6 and r2["not_flagged_readings_above_0.05"] == 1 and not r2["S2"]
    # an infinite error counts as above every threshold; a spread on the threshold is flagged
    by3 = copy.deepcopy(by)
    by3[5]["a"][0]["abs_curve_err"] = float("inf")
    assert not self_check(sc, by3, ids)["S1"]
    # the comparison is "at least the threshold" in floating point: these forces give 0.004500000000000028, which
    # is flagged, and a spread just below the threshold is not
    edge = {s: {"a": rows([100.0 + 0.45 * k], [0.0])} for k, s in enumerate((5, 6, 7))}
    edge[7]["a"][0]["F"] = 100.0
    assert self_check(sc, edge, ["a"])["flagged"] == 1
    edge[6]["a"][0]["F"] = 100.44
    assert self_check(sc, edge, ["a"])["flagged"] == 0
    # the spread is over the absolute value of the median: negative forces are flagged as positive ones are
    neg = {s: {"a": rows([f], [0.0])} for s, f in zip((5, 6, 7), (-100.0, -100.2, -100.6))}
    r = self_check(sc, neg, ["a"])
    assert r["flagged"] == 1 and r["by_member"]["a"]["spread"][0] == pytest.approx(0.6 / 100.2)
    zero = {s: {"a": rows([f], [0.0])} for s, f in zip((5, 6, 7), (-1.0, 0.0, 1.0))}
    assert self_check(sc, zero, ["a"])["flagged"] == 1


def test_self_check_passes_when_few_pairs_are_flagged_and_the_rest_is_clean():
    sc = {"threshold": 0.0045}
    ids = [f"m{i}" for i in range(10)]
    by = {s: {i: rows([100.0 + 0.1 * k], [0.01]) for i in ids} for k, s in enumerate((5, 6, 7))}
    for k, s in enumerate((5, 6, 7)):
        by[s]["m0"] = rows([100.0 + 5.0 * k], [0.20])
    r = self_check(sc, by, ids)
    assert r["flagged"] == 1 and r["verdict"] == "PASS" and r["largest_error_not_flagged"] == [0.01] * 3


def test_wording_of_the_comparison():
    band = [2.0 / 3.0, 1.5]
    lf = {"C1_value": 0.008, "C2_value": 0.036}
    w = lambda a, b: compare(band, {"C1_value": a, "C2_value": b}, lf)["wording"]   # noqa: E731
    assert w(0.008, 0.036) == "comparable" and w(0.0054, 0.05) == "comparable"
    assert w(0.004, 0.030) == "supervised closer" and w(0.007, 0.020) == "supervised closer"
    assert w(0.020, 0.040) == "label-free closer" and w(0.009, 0.060) == "label-free closer"
    assert w(0.004, 0.060) == "mixed" and w(0.004, 0.040) == "mixed"
    assert w(float("inf"), 0.040) == "label-free closer"
    both = {"C1_value": float("inf"), "C2_value": 0.1}
    assert compare(band, both, dict(both))["wording"] == "NOT COMPARABLE"
    two, three = {"C1_value": 2.0, "C2_value": 2.0}, {"C1_value": 3.0, "C2_value": 3.0}
    assert compare(band, three, two)["wording"] == compare(band, two, three)["wording"] == "comparable"   # the ends


def test_identity_check_and_statistics():
    a = config()["arms"]["label_free"]
    exact = {r: {"per_seed": copy.deepcopy(v)} for r, v in G22_PER_SEED.items()}
    assert identity(a, exact) == {"largest_difference": 0.0, "tolerance": 1e-4, "ok": True}
    off = copy.deepcopy(exact)
    off["raw"]["per_seed"]["abs_curve_err_p90"][1] += 2e-4
    r = identity(a, off)
    assert not r["ok"] and r["largest_difference"] == pytest.approx(2e-4)
    # equal infinite values are equal and hide no other difference; any other difference that is not a number counts
    inf = float("inf")
    b = {"identity": {"tolerance": 1.0, "values": {"raw": {"p90": [inf, 10.0, 20.0]}}}}
    assert identity(b, {"raw": {"per_seed": {"p90": [inf, 10.0, 20.0]}}}) == {
        "largest_difference": 0.0, "tolerance": 1.0, "ok": True}
    r = identity(b, {"raw": {"per_seed": {"p90": [inf, 50.0, 90.0]}}})
    assert not r["ok"] and r["largest_difference"] == 70.0
    for got in ([5.0, 10.0, 20.0], [inf, inf, 20.0], [inf, float("nan"), 20.0], [-inf, 10.0, 20.0]):
        r = identity(b, {"raw": {"per_seed": {"p90": got}}})
        assert not r["ok"] and r["largest_difference"] == inf
    s = _stats([{"abs_curve_err": {"median": m, "p90": p}} for m, p in ((0.01, 0.05), (0.02, 0.04), (0.03, 0.06))])
    assert s["C1_value"] == 0.02 and s["C2_value"] == 0.05
    s = _stats([None, None, {"abs_curve_err": {"median": 0.01, "p90": 0.05}}])
    assert s["C1_value"] == float("inf") and s["C2_value"] == float("inf")


# ---- the verdict step, on rows files written here ----------------------------------------------------------------

def metric_row(F, err):
    r = {k: 0.0 for k in ("F_err", "abs_F_err", "F_sigma_err", "e_err", "gap", "bound", "iou_contact", "iou_plastic",
                          "bolt_err", "u_rel_l2")}
    r.update(curve_err=float(err), abs_curve_err=float(err), evaluate_failed=False, within_bound=True, F=float(F),
             e=1.0)
    return r


def fake_data(tmp_path, cfg):
    """A manifest and a ledger of the held-out and tested members only, as after section 3 of the runbook."""
    d = tmp_path / "data"
    (d / "labels").mkdir(parents=True)
    m = [(i, s) for i, s, _ in data.members(cfg)]
    (d / "manifest.json").write_text(json.dumps({"config_sha256": sha256(cfg), "n": len(m),
                                                 "instances": [{"id": i, "split": s} for i, s in m]}))
    (d / "labels" / "ledger.json").write_text(json.dumps(
        [{"id": i, "levels": cfg["data"]["eval_levels_mm"], "seconds": 2.0} for i, s in m if s != "train"]))
    return d


def label_training_members(cfg, d):
    led = json.loads((d / "labels" / "ledger.json").read_text())
    led += [{"id": i, "levels": cfg["data"]["train_label_levels_mm"], "seconds": 3.0}
            for i, s, _ in data.members(cfg) if s == "train"]
    (d / "labels" / "ledger.json").write_text(json.dumps(led))


def fake_arm(cfg, d, runs, arm, err_of, F_of, non_finite=(), no_metrics=()):
    """Run folders and a rows file as evaluate_arm writes them, from made-up errors and forces of (seed, id, level).
    non_finite: seeds whose run stopped without finite predictions. no_metrics: (seed, reading, id) whose metrics the
    reference code could not compute, which leaves that member's set without a summary."""
    ev = cfg["evaluation"]
    man = json.loads((d / "manifest.json").read_text())
    seeds = cfg["arms"][arm]["seeds"]
    for seed in seeds:
        run = runs / f"{arm}_s{seed}"
        run.mkdir(parents=True, exist_ok=True)
        if seed in non_finite:
            (run / "history.json").write_text(json.dumps({"status": "non-finite loss at step 3"}))
            continue
        for f in PREDICTION_FILES:
            (run / f).write_text(f"{arm} {seed} {f}")
    out = {"gate": cfg["gate"], "config_sha256": sha256(cfg), "arm": arm, "inputs": _inputs(cfg, d, runs, arm),
           "runs": {}, "readings": {}}
    for reading in [ev["readings"]["judged"]] + list(ev["readings"]["reported"]):
        for seed in seeds:
            if seed in non_finite:
                continue
            entry = {"errors": {}}
            for st in ev["sets"]:
                rows = {r["id"]: [metric_row(F_of(seed, r["id"], lv), err_of(seed, r["id"], lv))
                                  for lv in range(len(cfg["data"]["eval_levels_mm"]))]
                        for r in man["instances"] if r["split"] == st}
                lost = [i for i in rows if (seed, reading, i) in no_metrics]
                for i in lost:
                    entry["errors"][i] = "AssertionError: a contact unknown is negative"
                    del rows[i]
                entry[f"{st}_rows"] = rows
                if not lost:
                    entry[st] = _summary([x for v in rows.values() for x in v])
            out["readings"].setdefault(reading, {})[str(seed)] = entry
    (runs / f"rows_{arm}.json").write_text(json.dumps(out))


def fake_gate(tmp_path, lf_err, identity_value=0.01, **lost):
    """Data and the label-free arm: every error 0.01 and the runs agreeing, apart from what lf_err says."""
    cfg = reduced()
    cfg["arms"]["label_free"]["identity"]["values"] = {
        r: {"abs_curve_err_median": [identity_value] * 3, "abs_curve_err_p90": [identity_value] * 3}
        for r in ("condensed", "raw")}
    d, runs = fake_data(tmp_path, cfg), tmp_path / "runs"
    runs.mkdir()
    far = {k for k, e in lf_err.items() if e[1]}                         # the pairs on which the runs disagree

    def F_of(seed, i, lv):
        return 100.0 + (5.0 if (i, lv) in far else 0.1) * cfg["arms"]["label_free"]["seeds"].index(seed)

    fake_arm(cfg, d, runs, "label_free", lambda seed, i, lv: lf_err.get((i, lv), (0.01, False))[0], F_of, **lost)
    return cfg, d, runs


def test_verdict_part_1_is_fixed_before_the_supervised_arm(tmp_path):
    # one pair of the third sample is far off and the runs disagree on it: flagged, so S1 to S3 hold
    cfg, d, runs = fake_gate(tmp_path, {("third_0000", 6): (0.20, True)})
    v = verdict(cfg, d, runs)
    assert v["verdict"] == {"identity": "OK", "self_check": "PASS", "ranking": "HOLDS", "comparison": "INCOMPLETE"}
    assert v["not_evaluated"] == ["supervised_512"] and v["part1_same_as_first"] is True
    assert v["self_check"]["pairs"] == 14 and v["self_check"]["flagged"] == 1
    assert v["cost"]["training_members_labelled"] == 0
    part1 = (runs / "verdict_part1.json").read_bytes()
    kept = json.loads(part1)
    v_json = json.loads(json.dumps(v))
    assert kept == {k: x for k, x in v_json.items() if k != "part1_same_as_first"}      # the whole first verdict
    assert kept["verdict"]["comparison"] == "INCOMPLETE" and kept["self_check"]["verdict"] == "PASS"
    # the training members are labelled afterwards: the ledger file changes, the label-free rows are not stale
    before = _inputs(cfg, d, runs, "label_free")
    label_training_members(cfg, d)
    assert _inputs(cfg, d, runs, "label_free") == before and before["evaluated_labels"] == 2 + 2 + 4
    v2 = verdict(cfg, d, runs)
    assert v2["verdict"] == v["verdict"] and v2["cost"]["training_members_labelled"] == 3
    assert v2["cost"]["reference_solutions_for_training"] == 3 * len(SUPERVISED_LABEL_LEVELS)
    # the supervised arm, closer in both statistics: the wording, and part 1 as first written
    fake_arm(cfg, d, runs, "supervised_512", lambda seed, i, lv: 0.004, lambda seed, i, lv: 100.0)
    v3 = verdict(cfg, d, runs)
    assert v3["verdict"] == {"identity": "OK", "self_check": "PASS", "ranking": "HOLDS",
                             "comparison": "supervised closer"}
    assert v3["comparison"]["ratio_of_medians"] == pytest.approx(0.4) and v3["not_evaluated"] == []
    assert v3["part1_same_as_first"] is True and (runs / "verdict_part1.json").read_bytes() == part1
    assert v3["self_check"] == v["self_check"] and v3["identity"] == v["identity"]
    # a part 1 that differs from the one first written is reported, and the first is left as it is
    other = dict(kept, verdict=dict(kept["verdict"], self_check="FAIL"))
    (runs / "verdict_part1.json").write_text(json.dumps(other, indent=1))
    assert verdict(cfg, d, runs)["part1_same_as_first"] is False
    assert json.loads((runs / "verdict_part1.json").read_text()) == other
    (runs / "verdict_part1.json").write_bytes(part1)
    assert verdict(cfg, d, runs) == v3
    # so is a label-free rows file that is not the one part 1 was read from, although its recorded inputs are those
    # of the files present: the same rows give the label-free side of part 2
    rows_file = (runs / "rows_label_free.json").read_bytes()
    assert v3["rows_sha256"]["label_free"] == hashlib.sha256(rows_file).hexdigest() == kept["rows_sha256"]["label_free"]
    edited = json.loads(rows_file)
    edited["readings"]["condensed"]["5"]["eval_rows"]["eval_0000"][0]["abs_curve_err"] = 0.0100001
    (runs / "rows_label_free.json").write_text(json.dumps(edited))
    assert verdict(cfg, d, runs)["part1_same_as_first"] is False
    (runs / "rows_label_free.json").write_bytes(rows_file)
    assert verdict(cfg, d, runs) == v3
    # what else the final verdict reports: the medians by level, and the supervised arm read raw
    lv = v3["by_level"]["label_free"]["condensed"]["third"]
    assert lv["levels_mm"] == cfg["data"]["eval_levels_mm"] and lv["median_of_runs"][:6] == [0.01] * 6
    assert lv["median_of_runs"][6] == pytest.approx(0.105)               # two members: 0.20 and 0.01
    assert v3["by_level"]["supervised_512"]["condensed"]["third"]["median_per_run"] == [[0.004] * 7] * 3
    assert v3["comparison"]["supervised_raw_against_label_free_judged"]["raw"]["wording"] == "supervised closer"
    # a later verdict whose part 1 is not decided says that it is not the one kept
    (runs / "rows_label_free.json").unlink()
    later = verdict(cfg, d, runs)
    assert later["verdict"]["self_check"] == "INCOMPLETE" and later["part1_same_as_first"] is False
    (runs / "rows_label_free.json").write_bytes(rows_file)
    # the kept file is written only before part 2 begins: once it is gone, it is not made again
    (runs / "verdict_part1.json").unlink()
    gone = verdict(cfg, d, runs)
    assert gone["part1_same_as_first"] is None and "absent" in gone["part1_first"]
    assert not (runs / "verdict_part1.json").exists() and gone["verdict"] == v3["verdict"]


def test_verdict_refuses_rows_computed_from_other_files(tmp_path):
    cfg, d, runs = fake_gate(tmp_path, {})
    verdict(cfg, d, runs)
    pred = runs / "label_free_s6" / "preds_condensed.npz"
    kept = pred.read_bytes()
    pred.write_text("another prediction")
    with pytest.raises(RuntimeError, match="other files"):
        verdict(cfg, d, runs)
    pred.write_bytes(kept)
    verdict(cfg, d, runs)
    led_p = d / "labels" / "ledger.json"
    led = json.loads(led_p.read_text())
    again = [dict(e, seconds=9.0) if e["id"] == "eval_0001" else e for e in led]   # a held-out label solved again
    led_p.write_text(json.dumps(again))
    with pytest.raises(RuntimeError, match="other files"):
        verdict(cfg, d, runs)
    led_p.write_text(json.dumps(led[::-1]))                              # the order of the entries does not matter
    verdict(cfg, d, runs)
    # another configuration is refused in three places: a runs folder that holds its verdict, the manifest, the rows
    other = copy.deepcopy(cfg)
    other["self_check"]["threshold"] = 0.004
    with pytest.raises(RuntimeError, match="the verdict of another configuration"):
        verdict(other, d, runs)
    kept = (runs / "verdict.json").read_bytes()
    (runs / "verdict.json").unlink()
    with pytest.raises(RuntimeError, match="generated under another configuration"):
        verdict(other, d, runs)
    man = json.loads((d / "manifest.json").read_text())
    (d / "manifest.json").write_text(json.dumps(dict(man, config_sha256=sha256(other))))
    with pytest.raises(RuntimeError, match="written under another configuration"):
        verdict(other, d, runs)
    assert not (runs / "verdict.json").exists()
    (d / "manifest.json").write_text(json.dumps(man))
    (runs / "verdict.json").write_bytes(kept)
    verdict(cfg, d, runs)


def test_verdict_words_of_the_other_outcomes(tmp_path):
    # a large error on which the runs agree: not flagged, S1 fails; the ranking does not hold either
    cfg, d, runs = fake_gate(tmp_path / "a", {("third_0001", 3): (0.12, False)})
    v = verdict(cfg, d, runs)
    assert v["verdict"]["self_check"] == "FAIL" and v["verdict"]["ranking"] == "DOES NOT HOLD"
    assert v["self_check"]["S1"] is False and v["self_check"]["S3"] is True and v["verdict"]["identity"] == "OK"
    # no pair above 0.05: the criteria hold and the ranking cannot be evaluated
    cfg, d, runs = fake_gate(tmp_path / "b", {})
    v = verdict(cfg, d, runs)
    assert v["verdict"]["self_check"] == "PASS" and v["verdict"]["ranking"] == "NOT EVALUABLE"
    # the label-free runs do not reproduce the base gate's values: nothing is read
    cfg, d, runs = fake_gate(tmp_path / "c", {}, identity_value=0.012)
    v = verdict(cfg, d, runs)
    assert v["verdict"] == {"identity": "INVALID", "self_check": "INVALID", "ranking": "INVALID",
                            "comparison": "INCOMPLETE"} and "self_check" not in v
    assert v["identity"]["largest_difference"] == pytest.approx(0.002)
    fake_arm(cfg, d, runs, "supervised_512", lambda seed, i, lv: 0.004, lambda seed, i, lv: 100.0)
    v = verdict(cfg, d, runs)
    assert v["verdict"]["comparison"] == "INVALID" and "comparison" not in v and v["part1_same_as_first"] is True
    # an invalid verdict holds no judged number: only the label-free values on the base gate's own sample
    assert v["self_check_reported"] is None
    assert [arm for arm in v["statistics"] for r in v["statistics"][arm] for s in v["statistics"][arm][r]
            if v["statistics"][arm][r][s] is not None] == ["label_free", "label_free"]
    assert all(x is None for arm in v["by_level"].values() for r in arm.values() for x in r.values())
    # a folder that is not there, or that holds nothing of this gate, is refused and nothing is written
    cfg = reduced()
    d = fake_data(tmp_path / "d", cfg)
    for missing in (tmp_path / "d" / "no_such_folder", tmp_path / "d"):
        with pytest.raises(RuntimeError, match="holds no run and no rows of this gate"):
            verdict(cfg, d, missing)
    assert not (tmp_path / "d" / "no_such_folder").exists() and not (tmp_path / "d" / "verdict.json").exists()
    # the runs predicted and no rows of the label-free arm: nothing is judged and no part 1 is kept
    (tmp_path / "d" / "runs" / "label_free_s5").mkdir(parents=True)
    v = verdict(cfg, d, tmp_path / "d" / "runs")
    assert v["verdict"] == {"identity": "NOT EVALUATED", "self_check": "INCOMPLETE", "ranking": "INCOMPLETE",
                            "comparison": "INCOMPLETE"}
    assert v["part1_same_as_first"] is None and not (tmp_path / "d" / "runs" / "verdict_part1.json").exists()


def test_verdict_when_a_run_or_a_member_gives_no_numbers(tmp_path):
    sup = ("supervised_512", lambda seed, i, lv: 0.004, lambda seed, i, lv: 100.0)
    # a member of the base gate's sample without metrics in one label-free run: the identity cannot be shown, so it
    # is INVALID and neither part is judged
    cfg, d, runs = fake_gate(tmp_path / "a", {}, no_metrics={(6, "raw", "eval_0000")})
    v = verdict(cfg, d, runs)
    assert v["verdict"]["identity"] == "INVALID" and v["verdict"]["self_check"] == v["verdict"]["ranking"] == "INVALID"
    assert v["identity"]["ok"] is False and v["identity"]["largest_difference"] is None and "self_check" not in v
    fake_arm(cfg, d, runs, *sup)
    assert verdict(cfg, d, runs)["verdict"]["comparison"] == "INVALID"
    # a label-free run without finite predictions: the same
    cfg, d, runs = fake_gate(tmp_path / "b", {}, non_finite=(7,))
    v = verdict(cfg, d, runs)
    assert v["verdict"]["identity"] == "INVALID" and v["non_finite"] == ["label_free_s7"]
    assert not any(name.startswith("label_free") for name in v["missing"])
    # a member of the judged set without metrics in a label-free run, the identity being in order: part 1 fails
    cfg, d, runs = fake_gate(tmp_path / "c", {}, no_metrics={(5, "condensed", "third_0001")})
    v = verdict(cfg, d, runs)
    assert v["verdict"] == {"identity": "OK", "self_check": "FAIL", "ranking": "NOT EVALUABLE",
                            "comparison": "INCOMPLETE"} and v["part1_same_as_first"] is True
    # in part 2 that label-free seed counts with infinite errors, as a supervised seed without numbers does
    fake_arm(cfg, d, runs, *sup)
    v = verdict(cfg, d, runs)
    lf_third = v["statistics"]["label_free"]["condensed"]["third"]
    assert lf_third["per_seed"]["abs_curve_err_median"] == [float("inf"), 0.01, 0.01] and lf_third["C1_value"] == 0.01
    assert v["verdict"]["comparison"] == "supervised closer" and v["verdict"]["self_check"] == "FAIL"
    assert v["by_level"]["label_free"]["condensed"]["third"] is None and "self_check" not in v
    cfg, d, runs = fake_gate(tmp_path / "c2", {}, no_metrics={(5, "condensed", "third_0001"),
                                                              (6, "condensed", "third_0000")})
    verdict(cfg, d, runs)
    fake_arm(cfg, d, runs, *sup)
    v = verdict(cfg, d, runs)                                            # two such seeds: both statistics infinite
    assert v["statistics"]["label_free"]["condensed"]["third"]["C1_value"] == float("inf")
    assert v["comparison"]["ratio_of_medians"] == 0.0 and v["verdict"]["comparison"] == "supervised closer"
    # supervised seeds that stopped on a non-finite loss count with infinite errors: one of three leaves the middle
    # value finite, two of three make both statistics infinite
    cfg, d, runs = fake_gate(tmp_path / "d", {})
    verdict(cfg, d, runs)
    fake_arm(cfg, d, runs, *sup, non_finite=(6,))
    v = verdict(cfg, d, runs)
    assert v["non_finite"] == ["supervised_512_s6"] and v["verdict"]["comparison"] == "supervised closer"
    third = v["statistics"]["supervised_512"]["condensed"]["third"]
    assert third["per_seed"]["abs_curve_err_median"][1] == float("inf")
    assert v["by_level"]["supervised_512"]["condensed"]["third"] is None
    cfg, d, runs = fake_gate(tmp_path / "e", {})
    verdict(cfg, d, runs)
    fake_arm(cfg, d, runs, *sup, non_finite=(5, 6))
    v = verdict(cfg, d, runs)
    assert v["verdict"]["comparison"] == "label-free closer" and v["comparison"]["ratio_of_medians"] == float("inf")
    # a member of the judged set without metrics in a supervised run: that seed counts with infinite errors too
    cfg, d, runs = fake_gate(tmp_path / "f", {})
    verdict(cfg, d, runs)
    fake_arm(cfg, d, runs, *sup, no_metrics={(7, "condensed", "third_0000")})
    v = verdict(cfg, d, runs)
    assert v["statistics"]["supervised_512"]["condensed"]["third"]["per_seed"]["abs_curve_err_p90"][2] == float("inf")
    assert v["verdict"]["comparison"] == "supervised closer" and v["non_finite"] == []


# ---- the stamped code and the entry point ---------------------------------------------------------------------------

def load_main(name):
    import importlib.util
    sys.path.insert(0, str(JOINT / "c23"))                               # as when the script is run by its path
    try:
        spec = importlib.util.spec_from_file_location(name, JOINT / "c23" / "__main__.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(JOINT / "c23"))
    return mod


def test_code_list_holds_the_package_and_c22s_stamped_files():
    mod = load_main("c23_main_for_test")
    assert {f for f in mod.CODE if f.startswith("c23/")} == {f"c23/{p.name}" for p in (JOINT / "c23").glob("*.py")}
    stamped = dict(line.split()[::-1] for line in (JOINT / "docs" / "G-C2.2_code.sha256").read_text().splitlines()
                   if line.strip() and not line.split()[1].startswith(".."))
    now = mod.code_hashes()
    assert set(stamped) == {f for f in mod.CODE if not f.startswith("c23/")} and len(mod.CODE) == 35
    assert all(now[f] == h for f, h in stamped.items()), "a file stamped for G-C2.2 has changed"
    assert mod.states_filled(config())
    blank = copy.deepcopy(config())
    blank["arms"]["label_free"]["state_sha256"]["6"] = "TO BE FILLED"
    assert not mod.states_filled(blank)
    with pytest.raises(SystemExit):
        mod.main(["verdict", "--data", "x", "--runs", "y", "--config-sha", "0" * 64])


def test_commands_refuse_code_that_is_not_the_stamped_code(tmp_path, monkeypatch, capsys):
    """Every command but write-config needs the file of hashes written at the stamp beside the code, with the hash of
    every file of the code list as it is now. Before the stamp there is none, so generate cannot draw the sample."""
    mod = load_main("c23_main_for_stamp_test")
    sha = sha256(config())
    stamp = tmp_path / "G-C2.3_code.sha256"
    monkeypatch.setattr(mod, "STAMP_FILE", stamp)

    def reached(*args, **kwargs):                           # a refusal that did not hold must not draw the sample
        raise AssertionError("a command went past its refusal")

    for name in ("generate", "members", "sample", "label", "labelled_ids", "check_labels"):
        monkeypatch.setattr(data, name, reached)
    assert "not stamped" in mod.not_stamped()
    commands = (["generate", "--data", str(tmp_path / "d"), "--config-sha", sha],
                ["label", "--data", str(tmp_path / "d"), "--split", "third"],
                ["check-labels", "--data", str(tmp_path / "d")],
                ["verdict", "--data", str(tmp_path / "d"), "--runs", str(tmp_path / "r"), "--config-sha", sha],
                ["evaluate", "--data", str(tmp_path / "d"), "--runs", str(tmp_path / "r"), "--config-sha", sha,
                 "--arm", "label_free"])
    for argv in commands:
        with pytest.raises(SystemExit, match="not stamped"):
            mod.main(argv)
    assert not (tmp_path / "d").exists() and not (tmp_path / "r").exists()
    lines = [f"{h}  {f}" for f, h in mod.code_hashes().items()]
    stamp.write_text("\n".join(lines) + "\n")
    assert mod.not_stamped() is None
    wrong = ["0" * 64 + "  c23/data.py" if x.endswith("  c23/data.py") else x for x in lines]
    stamp.write_text("\n".join(wrong) + "\n")
    assert "c23/data.py" in mod.not_stamped()
    with pytest.raises(SystemExit, match="c23/data.py"):
        mod.main(commands[0])
    stamp.write_text("\n".join(lines[1:]) + "\n")                        # a file of the code list is not in it
    assert "c23/__init__.py" in mod.not_stamped()
    stamp.write_text("\n".join(lines) + "\nnot a line of hashes at all\n")
    assert "not a hash and a file name" in mod.not_stamped()
    capsys.readouterr()
    mod.main(["write-config", "--out", str(tmp_path / "c.json")])        # write-config runs without a stamp
    assert capsys.readouterr().out.splitlines()[2] == "code as stamped: False"
    with pytest.raises(SystemExit, match="not the stamped one"):         # and ends with an error if asked to check
        mod.main(["write-config", "--out", str(tmp_path / "c.json"), "--config-sha", sha])
    # with the stamp in order, generate still refuses another configuration hash before it draws anything
    stamp.write_text("\n".join(lines) + "\n")
    mod.main(["write-config", "--out", str(tmp_path / "c.json"), "--config-sha", sha])
    with pytest.raises(SystemExit, match="not the stamped one"):
        mod.main(["write-config", "--out", str(tmp_path / "c.json"), "--config-sha", "0" * 64])
    with pytest.raises(SystemExit, match="refusing to run"):
        mod.main(["generate", "--data", str(tmp_path / "d"), "--config-sha", "0" * 64])
    assert not (tmp_path / "d").exists()


def test_the_entry_point_runs_as_a_process(tmp_path):
    """`python -I c23/__main__.py`, as the runbook starts it, from another folder: the configuration hash, the line
    on the state files, the code hashes, and a configuration file with the same bytes on every system. It draws
    nothing: no member is sampled by write-config."""
    import subprocess
    main = str(JOINT / "c23" / "__main__.py")
    r = subprocess.run([sys.executable, "-I", "-B", main, "write-config", "--out", "c.json"], cwd=tmp_path,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    lines = r.stdout.strip().splitlines()
    assert lines[0] == f"config sha256 {sha256(config())}" and lines[1] == "state files pinned: True"
    assert lines[2] in ("code as stamped: True", "code as stamped: False")       # False until the stamp is made
    code = [line.split() for line in lines[3:]]
    assert len(code) == 35 and "c23/smoke.py" in [f for f, _ in code]
    assert all(hashlib.sha256((JOINT / f).read_bytes()).hexdigest() == h for f, h in code)
    raw = (tmp_path / "c.json").read_bytes()
    assert b"\r" not in raw and json.loads(raw) == json.loads(json.dumps(config()))
    for cmd in (["verdict"], ["evaluate", "--arm", "label_free"]):
        r = subprocess.run([sys.executable, "-I", "-B", main, *cmd, "--data", "x", "--runs", "y",
                            "--config-sha", "0" * 64], cwd=tmp_path, capture_output=True, text=True)
        assert r.returncode != 0 and "refusing to run" in r.stderr


# ---- training and the command line, on a small configuration ---------------------------------------------------------

@pytest.fixture(scope="module")
def small_gate(tmp_path_factory):
    """A stand-in for G-C2.2 (three label-free runs of one epoch under its reduced configuration, evaluated) and this
    gate's reduced configuration built on it, as c23/smoke.py builds them, with fewer members. Family seeds 7, 8, 101
    and 102 only."""
    pytest.importorskip("torch")
    if not REPO:
        pytest.skip("set FEJEPA_REPO to the repository checkout")
    sys.path.insert(0, str(Path(REPO) / "src"))
    from c22 import data as data22
    from c22.evaluate import evaluate as evaluate22
    from c22.train import train as train22
    from c23.smoke import reduced_base, reduced, SEEDS
    from c23.train import file_sha256

    b = reduced_base()
    b["data"].update(n_train=2, n_eval=1, n_former=1)
    b["arms"]["label_free"]["epochs"] = 1
    root = tmp_path_factory.mktemp("c23gate")
    d22, r22 = root / "base_data", root / "base_runs"
    data22.generate(b, d22)
    data22.label(b, d22, data22.labelled_ids(b, d22), workers=1)
    for seed in SEEDS:
        assert train22(b, seed, d22, r22, device="cpu")["status"] == "finished"
    v22 = evaluate22(b, d22, r22, workers=1)
    states = {str(seed): file_sha256(r22 / f"label_free_s{seed}" / "state.pt") for seed in SEEDS}
    cfg = reduced(sha256(b), states, {"condensed": v22["per_seed"], "raw": v22["reported_readings"]["raw"]["per_seed"]})
    cfg["data"].update(n_train=2, n_third=1, n_eval=1, n_train_labelled=2)
    cfg["arms"]["label_free"]["epochs"] = 1
    cfg["arms"]["supervised_512"].update(labels=2, epochs=2)
    drawn = {cfg["data"][k] for k in ("train_seed", "third_eval_seed", "eval_seed", "former_eval_seed")}
    assert drawn == set(TEST_SEEDS) and b["data"]["eval_seed"] == cfg["data"]["eval_seed"]
    return b, cfg, root


@pytest.fixture(scope="module")
def labelled_data(small_gate, tmp_path_factory):
    _, cfg, _ = small_gate
    d = tmp_path_factory.mktemp("c23data")
    data.generate(cfg, d)
    data.label(cfg, d, data.labelled_ids(cfg, d), workers=1)
    assert data.check_labels(cfg, d)["ok"]
    return d


def test_supervised_training_keeps_the_recipe_and_the_initial_weights(small_gate, labelled_data, tmp_path, monkeypatch):
    """The supervised run is G-C2.2's run with the supervised loss: it starts from the weights the label-free run of
    its seed starts from; AdamW has the recipe's beta2; every step takes the supervised loss, then the cap, then the
    clipping; an interrupted run resumes to the same end state and predictions; a finished run returns at once."""
    torch = pytest.importorskip("torch")
    import c22.train as t22
    import c23.train as t23
    b, cfg, root = small_gate
    d = labelled_data

    class Built(Exception):
        pass

    def stop_after(build):
        def f(*a, **k):
            raise Built([copy.deepcopy(net.state_dict()) for net in build(*a, **k)])
        return f

    monkeypatch.setattr(t22, "build", stop_after(t22.build))
    monkeypatch.setattr(t23, "build", stop_after(t23.build))
    with pytest.raises(Built) as lf:
        t22.train(b, 5, root / "base_data", tmp_path / "lf", device="cpu")
    with pytest.raises(Built) as sup:
        t23.train(cfg, 5, d, tmp_path / "sup", device="cpu")
    with pytest.raises(Built) as other:
        t22.train(b, 6, root / "base_data", tmp_path / "lf", device="cpu")
    monkeypatch.undo()
    same = [bool((x[k] == y[k]).all()) for x, y in zip(lf.value.args[0], sup.value.args[0]) for k in x]
    assert same and all(same)
    assert not all(bool((x[k] == y[k]).all()) for x, y in zip(lf.value.args[0], other.value.args[0]) for k in x)

    made, calls, sups = [], [], []
    real_adamw, real_cap, real_clip, real_loss = (torch.optim.AdamW, t23.cap_encoder_gradient,
                                                  torch.nn.utils.clip_grad_norm_, t23.step_loss)
    monkeypatch.setattr(torch.optim, "AdamW", lambda *a, **k: made.append(k) or real_adamw(*a, **k))
    monkeypatch.setattr(t23, "cap_encoder_gradient", lambda enc, w, c: calls.append("cap") or real_cap(enc, w, c))
    monkeypatch.setattr(torch.nn.utils, "clip_grad_norm_",
                        lambda params, m: calls.append("clip") or real_clip(params, m))

    def loss(cfg_, nets, it, rng, sup_, dev):
        sups.append(sup_)
        out = real_loss(cfg_, nets, it, rng, sup_, dev)
        calls.append("loss")
        return out

    monkeypatch.setattr(t23, "step_loss", loss)
    h = t23.train(cfg, 5, d, tmp_path / "full", device="cpu")
    monkeypatch.undo()
    assert made[0]["betas"] == (0.9, 0.99) and h["betas"] == [0.9, 0.99] and made[0]["lr"] == cfg["training"]["lr"]
    assert h["status"] == "finished" and h["steps"] == h["total_steps"] == 4 and np.isfinite(h["loss"]).all()
    assert h["config_sha256"] == sha256(cfg) and h["arm"] == "supervised_512" and h["reference_solutions"] == 2 * 4
    assert h["training_labels_sha256"] == data.ledger_sha256(d, ["train_0000", "train_0001"])[0]
    assert sups == [True] * 4 and calls == ["loss", "cap", "clip"] * 4
    t23.train(cfg, 5, d, tmp_path / "part", device="cpu", stop_after_epoch=1)
    h2 = t23.train(cfg, 5, d, tmp_path / "part", device="cpu")
    assert h2["status"] == "finished" and h2["resumes"] == [1] and h2["loss"] == h["loss"]
    name = "supervised_512_s5"
    s1 = torch.load(tmp_path / "full" / name / "state.pt", map_location="cpu", weights_only=False)
    s2 = torch.load(tmp_path / "part" / name / "state.pt", map_location="cpu", weights_only=False)
    assert all(bool((s1[p][k] == s2[p][k]).all()) for p in ("enc", "dec", "head") for k in s1[p])
    for f in ("preds.npz", "preds_condensed.npz", "preds_base.npz"):
        with np.load(tmp_path / "full" / name / f) as x, np.load(tmp_path / "part" / name / f) as y:
            assert sorted(x.files) == sorted(y.files) == ["eval_0000", "tested_BJ_T1_preloaded", "third_0000"]
            assert all((x[k] == y[k]).all() for k in x.files)
    log = (tmp_path / "full" / name / "attempts.log").read_text()
    assert t23.train(cfg, 5, d, tmp_path / "full", device="cpu") == json.loads(
        (tmp_path / "full" / name / "history.json").read_text())
    assert (tmp_path / "full" / name / "attempts.log").read_text().startswith(log)
    with pytest.raises(RuntimeError, match="seed"):
        t23.train(cfg, 6, d, tmp_path / "full", device="cpu")            # not a seed of the small configuration
    # a run does not resume on other labels than it started with, and does not start on a label the ledger does not
    # describe
    t23.train(cfg, 5, d, tmp_path / "other", device="cpu", stop_after_epoch=1)
    led_p = Path(d) / "labels" / "ledger.json"
    led_text = led_p.read_text()
    led = json.loads(led_text)
    try:
        led_p.write_text(json.dumps([dict(e, seconds=e["seconds"] + 1.0) if e["id"] == "train_0001" else e
                                     for e in led]))
        with pytest.raises(RuntimeError, match="other labels"):
            t23.train(cfg, 5, d, tmp_path / "other", device="cpu")
        led_p.write_text(json.dumps([dict(e, label_sha256="0" * 64) if e["id"] == "train_0000" else e for e in led]))
        with pytest.raises(RuntimeError, match="differs from the ledger"):
            t23.train(cfg, 5, d, tmp_path / "fresh", device="cpu")
    finally:
        led_p.write_text(led_text)
    assert t23.train(cfg, 5, d, tmp_path / "other", device="cpu")["status"] == "finished"


def test_the_command_line_runs_the_runbooks_commands(small_gate, tmp_path, monkeypatch, capsys):
    """The runbook's commands in the runbook's order on the small configuration: write-config with the repository
    check, generate, the labels of the held-out sets and their check, the predictions of the three label-free states,
    their evaluation and the verdict of part 1, only then the labels of the training members and the check of all
    labels, the supervised run, its evaluation and the final verdict. The printed lines are those the runbook quotes."""
    import c23.config as cc
    b, cfg, root = small_gate
    monkeypatch.setattr(cc, "config", lambda: copy.deepcopy(cfg))
    mod = load_main("c23_main_for_cli_test")
    stamp = tmp_path / "G-C2.3_code.sha256"                              # the file the stamp will write
    stamp.write_text("".join(f"{h}  {f}\n" for f, h in mod.code_hashes().items()))
    monkeypatch.setattr(mod, "STAMP_FILE", stamp)
    sha, d, runs = sha256(cfg), str(tmp_path / "data"), str(tmp_path / "runs")
    at = ("--data", d, "--runs", runs)

    def run(*argv):
        capsys.readouterr()
        mod.main(list(argv))
        return capsys.readouterr().out.strip().splitlines()

    def stops(*argv):
        """The command's output when it ends with a code other than 0, as the queue's guard reads it."""
        capsys.readouterr()
        with pytest.raises(SystemExit) as end:
            mod.main(list(argv))
        assert end.value.code not in (0, None)
        return capsys.readouterr().out.strip().splitlines()

    out = run("write-config", "--out", str(tmp_path / "cfg.json"), "--repo", REPO, "--config-sha", sha)
    assert out[:3] == [f"config sha256 {sha}", "state files pinned: True", "code as stamped: True"]
    assert [line.split()[0] for line in out[3:3 + len(mod.CODE)]] == mod.CODE
    rest = out[3 + len(mod.CODE):]
    assert [line.startswith("repository ") and line.endswith(" checked") for line in rest] == [True] * 6
    assert json.loads((tmp_path / "cfg.json").read_text()) == json.loads(json.dumps(cfg))
    stops("write-config", "--out", str(tmp_path / "cfg2.json"), "--config-sha", "0" * 64)
    stops("generate", "--data", d, "--config-sha", "0" * 64)             # another configuration: nothing is drawn
    assert not (tmp_path / "data").exists()
    assert run("generate", "--data", d, "--config-sha", sha)[-1].endswith("manifest.json")
    assert [r["split"] for r in data.manifest(d)["instances"]] == ["train"] * 2 + ["third", "eval", "tested"]
    with pytest.raises(SystemExit):
        run("label", "--data", d, "--split", "former")
    for split in ("third", "eval", "tested"):
        assert run("label", "--data", d, "--split", split, "--workers", "1")[-1] == "labelled 1"
    r = json.loads(run("check-labels", "--data", d, "--splits", "third", "eval", "tested")[-1])
    assert r["ok"] is True and r["labels"] == r["needed"] == 3 and r["missing"] == []
    with pytest.raises(SystemExit):
        run("check-labels", "--data", d)                                 # the training members have no labels yet
    state = {seed: str(root / "base_runs" / f"label_free_s{seed}" / "state.pt") for seed in (5, 6, 7)}
    with pytest.raises(SystemExit):
        run("predict-label-free", *at, "--seed", "5", "--state", state[5], "--repo", REPO, "--config-sha", "0" * 64)
    with pytest.raises(RuntimeError, match="pins"):                     # the state of another seed
        run("predict-label-free", *at, "--seed", "5", "--state", state[6], "--repo", REPO, "--config-sha", sha,
            "--device", "cpu")
    assert not (tmp_path / "runs").exists()
    kept = {seed: Path(state[seed]).read_bytes() for seed in state}
    for seed in (5, 6, 7):
        last = json.loads(run("predict-label-free", *at, "--seed", str(seed), "--state", state[seed], "--repo", REPO,
                              "--config-sha", sha, "--device", "cpu")[-1])
        assert last["status"] == "finished" and set(last) == {"status", "predict_seconds"}
    assert all(Path(state[seed]).read_bytes() == kept[seed] for seed in state)   # the state files are only read
    assert not (tmp_path / "runs" / "label_free_s5" / "state.pt").exists()
    early = json.loads(stops("verdict", *at, "--config-sha", sha)[-1])  # nothing evaluated yet: the queue would stop
    assert early["verdict"]["self_check"] == "INCOMPLETE" and early["part1_same_as_first"] is None
    assert not (tmp_path / "runs" / "verdict_part1.json").exists()
    out = run("evaluate", *at, "--config-sha", sha, "--arm", "label_free", "--workers", "1")
    assert json.loads(out[-1]) == {f"label_free_s{seed}": "finished" for seed in (5, 6, 7)}
    stops("verdict", *at, "--config-sha", sha, "--final")                # part 1 is in order, the gate is not final
    v = json.loads(run("verdict", *at, "--config-sha", sha)[-1])
    assert v["verdict"]["identity"] == "OK" and v["verdict"]["comparison"] == "INCOMPLETE"
    assert v["verdict"]["self_check"] in ("PASS", "FAIL") and v["not_evaluated"] == ["supervised_512"]
    assert v["missing"] == ["supervised_512_s5"] and v["non_finite"] == [] and v["part1_same_as_first"] is True
    part1 = (tmp_path / "runs" / "verdict_part1.json").read_bytes()
    with pytest.raises(RuntimeError, match="nothing to evaluate"):       # no supervised run yet: no rows are written
        run("evaluate", *at, "--config-sha", sha, "--arm", "supervised_512", "--workers", "1")
    assert not (tmp_path / "runs" / "rows_supervised_512.json").exists()
    assert run("label", "--data", d, "--split", "train", "--workers", "1")[-1] == "labelled 2"
    r = json.loads(run("check-labels", "--data", d)[-1])
    assert r["ok"] is True and r["labels"] == r["needed"] == 5
    with pytest.raises(SystemExit):
        run("train", *at, "--seed", "5", "--repo", REPO, "--config-sha", "0" * 64)
    last = run("train", *at, "--seed", "5", "--repo", REPO, "--config-sha", sha, "--device", "cpu")[-1]
    assert json.loads(last) == {"status": "finished", "steps": 4}
    out = run("evaluate", *at, "--config-sha", sha, "--arm", "supervised_512", "--workers", "1")
    assert json.loads(out[-1]) == {"supervised_512_s5": "finished"}
    v2 = json.loads(run("verdict", *at, "--config-sha", sha, "--final")[-1])
    assert v2["not_evaluated"] == v2["missing"] == v2["non_finite"] == [] and v2["part1_same_as_first"] is True
    assert all(v2["verdict"][k] == v["verdict"][k] for k in ("identity", "self_check", "ranking"))
    assert v2["verdict"]["comparison"] in ("comparable", "supervised closer", "label-free closer", "mixed")
    assert (tmp_path / "runs" / "verdict_part1.json").read_bytes() == part1
    stored = json.loads((tmp_path / "runs" / "verdict.json").read_text())
    assert stored["verdict"] == v2["verdict"] and stored["cost"]["reference_solutions_for_training"] == 2 * 4
    assert stored["identity"]["largest_difference"] <= 1e-4
    assert set(stored["statistics"]) == {"label_free", "supervised_512"}


def test_the_command_line_stops_for_good_when_a_label_free_run_has_no_numbers(small_gate, labelled_data, tmp_path,
                                                                             monkeypatch, capsys):
    """A label-free state whose predictions are not finite: the command ends with a code other than 0, the end is
    final (the same command does not predict again), the evaluation and the verdict end with a code other than 0, and
    the verdict is INVALID. Also: the evaluation of the supervised arm ends with a code other than 0 while one of
    its runs is missing."""
    import c23.config as cc
    import c23.evaluate as ce
    import c23.train as ct
    b, cfg, root = small_gate
    monkeypatch.setattr(cc, "config", lambda: copy.deepcopy(cfg))
    mod = load_main("c23_main_for_stop_test")
    stamp = tmp_path / "G-C2.3_code.sha256"
    stamp.write_text("".join(f"{h}  {f}\n" for f, h in mod.code_hashes().items()))
    monkeypatch.setattr(mod, "STAMP_FILE", stamp)
    sha, at = sha256(cfg), ("--data", str(labelled_data), "--runs", str(tmp_path / "runs"))
    state = {seed: str(root / "base_runs" / f"label_free_s{seed}" / "state.pt") for seed in (5, 6, 7)}

    def call(*argv):
        """The command's exit code, as the queue's guard reads it, and its printed lines."""
        capsys.readouterr()
        try:
            mod.main(list(argv))
            code = 0
        except SystemExit as end:
            code = 0 if end.code in (0, None) else 1
        return code, capsys.readouterr().out.strip().splitlines()

    def predict_seed(seed):
        return call("predict-label-free", *at, "--seed", str(seed), "--state", state[seed], "--repo", REPO,
                    "--config-sha", sha, "--device", "cpu")

    real, calls = ct.predict, []

    def not_finite(cfg_, nets, data_dir, run, dev):
        calls.append(str(run))
        real(cfg_, nets, data_dir, run, dev)
        return False                                        # as c22.train.predict reports values that are not finite

    assert predict_seed(5)[0] == 0
    monkeypatch.setattr(ct, "predict", not_finite)
    code, out = predict_seed(6)
    assert code == 1 and json.loads(out[-1])["status"] == "non-finite predictions" and len(calls) == 1
    monkeypatch.setattr(ct, "predict", real)
    code, out = predict_seed(6)                             # the end is final: nothing is predicted again
    assert code == 1 and json.loads(out[-1])["status"] == "non-finite predictions" and len(calls) == 1
    log = (tmp_path / "runs" / "label_free_s6" / "attempts.log").read_text()
    assert "returned: non-finite predictions" in log
    assert predict_seed(7)[0] == 0
    code, out = call("evaluate", *at, "--config-sha", sha, "--arm", "label_free", "--workers", "1")
    assert code == 1 and json.loads(out[-1]) == {"label_free_s5": "finished", "label_free_s6": "non-finite",
                                                 "label_free_s7": "finished"}
    code, out = call("verdict", *at, "--config-sha", sha)
    v = json.loads(out[-1])
    assert code == 1 and v["non_finite"] == ["label_free_s6"]
    assert v["verdict"] == {"identity": "INVALID", "self_check": "INVALID", "ranking": "INVALID",
                            "comparison": "INCOMPLETE"}
    stored = json.loads((tmp_path / "runs" / "verdict.json").read_text())
    assert stored["identity"]["ok"] is False and "self_check" not in stored
    assert all(x is None for r in stored["statistics"]["label_free"].values() for s, x in r.items() if s != "eval")
    # the supervised arm: a missing run among those evaluated ends the command with a code other than 0
    monkeypatch.setattr(ce, "evaluate_arm", lambda *a_, **k_: {"inputs": {"runs": {
        "supervised_512_s5": {"status": "finished"}, "supervised_512_s6": {"status": "missing"}}}})
    code, out = call("evaluate", *at, "--config-sha", sha, "--arm", "supervised_512")
    assert code == 1 and json.loads(out[-1])["supervised_512_s6"] == "missing"
    monkeypatch.setattr(ce, "evaluate_arm", lambda *a_, **k_: {"inputs": {"runs": {
        "supervised_512_s5": {"status": "finished"}, "supervised_512_s6": {"status": "non-finite"}}}})
    assert call("evaluate", *at, "--config-sha", sha, "--arm", "supervised_512")[0] == 0
