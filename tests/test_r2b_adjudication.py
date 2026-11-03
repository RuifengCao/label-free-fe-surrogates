"""R2b (PREREG_R2B Sec. 5-7): the adjudication on synthetic returns built from
the records -- the Phase-2b report as both arms (S's cells scaled). The
verdict follows Sec. 5 condition by condition (R2a's rule, used as it is),
every refusal of Sec. 7 fires, the deviations are recorded, the readings of
Sec. 6 are computed (R2a beside R2b from fine3d's verdict file), and the
script adjudicates a return end to end, refusing the unstamped draft."""

import copy
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from fejepa.analysis import adjudicate_fine3d as A
from fejepa.report import config_sha256

ROOT = Path(__file__).resolve().parents[1]
P2B = ROOT / "records" / "wp8" / "e2" / "baseline" / "report_phase2b.json"
F3V = ROOT / "records" / "wp9" / "fine3d" / "fine3d_verdict.json"
S_FACTOR = 2.0 ** -10
ENV = {"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin:/usr/local/bin"}


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


J = _mod("adjudicate_r2b")


def _load(p):
    return json.loads(Path(p).read_text())


@pytest.fixture(scope="module")
def recs():
    return _load(P2B), _load(F3V)


def _cfg(name):
    return _load(ROOT / "configs" / f"{name}.json")


def _scale_cell(cell, metric, k):
    """Scale one metric of a cell: per-instance values, per-seed means and the
    cell's summary, consistently."""
    for e in cell["per_seed_eval"]:
        e["per_instance"][metric] = [v * k for v in e["per_instance"][metric]]
        e[metric] = float(np.mean(e["per_instance"][metric]))
    if metric in cell:
        ps = [e[metric] for e in cell["per_seed_eval"]]
        cell[metric] = {"mean": float(np.mean(ps)), "std": float(np.std(ps)), "per_seed": ps}


def _set_seed_means(cell, metric, values):
    for e, v in zip(cell["per_seed_eval"], values, strict=True):
        k = float(v) / e[metric]
        e["per_instance"][metric] = [x * k for x in e["per_instance"][metric]]
        e[metric] = float(v)


def _restamp(r):
    sha = config_sha256(r["config"])
    r["provenance"]["config_sha256"] = sha
    r["prereg"] = {"file": "PREREG_R2B.md", "config_sha256": sha}
    return r


def arm(p2b, name, fine=1.0, egap=1.0, disp=1.0, inband_p3=None, git="prereg-r2b",
        seeds=(3, 4, 5)):
    """An R2b report: the Phase-2b report with the arm's configuration; `disp`
    scales E8's in-band displacement and, unless `inband_p3` is given, P3's
    in-band pass alike; `egap` scales the in-band energy gap of both alike."""
    r = copy.deepcopy(p2b)
    r["config"] = _cfg(name)
    _restamp(r)
    r["provenance"].update(git=git, seeds=list(seeds))
    r["results"]["p3_transfer"]["protocol"]["seeds"] = list(seeds)
    r["d9_reuse_states"] = False
    d9 = r["results"]["e8"]["metrics"]["d9_restart"]
    d9.update(reuse_states=False, units_resumed_from_epoch={},
              ar_states={f"s{s}": {"reused": False, "sha256": hashlib.sha256(
                  f"{name} {s}".encode()).hexdigest()} for s in seeds})
    p3 = r["results"]["p3_transfer"]["metrics"]["ar"]
    _scale_cell(p3["fine"], "disp_rel_l2", fine)
    _scale_cell(p3["inband"], "disp_rel_l2", disp if inband_p3 is None else inband_p3)
    _scale_cell(p3["inband"], "energy_gap_rel", egap)
    c = r["results"]["e8"]["metrics"]["cells"]["ar"]["1024"]
    _scale_cell(c, "energy_gap_rel", egap)
    _scale_cell(c, "disp_rel_l2", disp)
    return r


def _entries():
    return {n: config_sha256(_cfg(n)) for n in ("r2b_b", "r2b_s")}


def _adj(b, s, recs, **kw):
    return J.adjudicate_arms(b, s, recs[0], recs[1], _entries(), s_factor=S_FACTOR, **kw)


def _hand_guard(base, new):
    base, new = np.asarray(base, float), np.asarray(new, float)
    rel = new.mean() / base.mean() - 1
    se = np.sqrt(base.var(ddof=1) / len(base) + new.var(ddof=1) / len(new)) / base.mean()
    return float(rel), float(max(0.10, 2 * se))


def _amp(fine_cstar, report_sha=None, disp_c=(0.08, 0.09, 0.07), repro=0.0, remesh_n=16,
         failed=0, complete=True):
    def summ(c, dc):
        return {"c_star_median": c, "c_battery_median": c, "amp_ratio_median": c,
                "disp": 0.25, "disp_c": dc, "egap": 0.3, "egap_c": 0.05, "complete": complete}
    rep = {"checked": True, "disp_max_rel_dev": repro, "egap_max_rel_dev": repro / 2}
    rem = {"c_battery_median_by_lc": {"0.0906": 1.0, "0.0374": 1.27},
           "u_norm_K_ratio_median_by_lc": {"0.0906": 1.0, "0.0374": 0.75},
           "fscale_ratio_median_by_lc": {"0.0906": 1.0, "0.0374": 0.19},
           "n_geometries": remesh_n, "n_failed": failed, "rows": [{}] * (remesh_n + failed)}
    return {"report_sha256": report_sha,
            "seeds": {f"s{s}": {"inband": {"summary": summ(1.0, 0.014), "reproduction": dict(rep)},
                                "fine": {"summary": summ(c, dc), "reproduction": dict(rep)},
                                "remesh": rem}
                      for s, c, dc in zip((3, 4, 5), fine_cstar, disp_c, strict=True)}}


# --------------------------------------------------------------- verdict --

def test_supported_when_all_three_conditions_hold(recs):
    b = arm(recs[0], "r2b_b")
    s = arm(recs[0], "r2b_s", fine=0.25, egap=0.8, disp=0.6)
    out = _adj(b, s, recs)
    assert out["verdict"] == "SUPPORTED" and out["conditions"]["failing"] == []
    vb, vs = out["values"]["b"], out["values"]["s"]
    rel, tau = _hand_guard(vb["fine_disp"], vs["fine_disp"])
    g = out["conditions"]["fine_displacement"]
    assert math.isclose(g["rel_change"], rel) and math.isclose(g["threshold"], tau)
    assert math.isclose(rel, -0.75, abs_tol=1e-12)
    ratio_b = [f / i for f, i in zip(vb["fine_disp"], vb["p3_inband_disp"], strict=True)]
    assert vb["ratio"] == pytest.approx(ratio_b, rel=1e-12)
    assert vb["ratio_of_seed_means"] == pytest.approx(8.6247, abs=1e-4)
    assert out["uninformative_note"] is None and out["deviations"] == []


@pytest.mark.parametrize("kw,failing", [
    ({"fine": 0.95}, ["(i)", "(ii)"]),
    ({"fine": 0.5, "egap": 0.5, "disp": 0.5}, ["(ii)"]),
    ({"fine": 0.3, "egap": 1.8}, ["(iii)"]),
    ({"fine": 0.3, "disp": 1.4}, ["(iii)"])])
def test_each_condition_fails_on_its_own(recs, kw, failing):
    out = _adj(arm(recs[0], "r2b_b"), arm(recs[0], "r2b_s", **kw), recs)
    assert out["verdict"].startswith("NOT SUPPORTED")
    assert [f.split()[0] for f in out["conditions"]["failing"]] == failing
    if failing == ["(ii)"]:                               # PREREG_R2B Sec. 6, in words
        assert out["condition_ii_alone"] == J.CONDITION_II_ALONE
        assert "the growth (the fine / in-band ratio) is not shown to shrink" in \
            J.CONDITION_II_ALONE
    else:
        assert "condition_ii_alone" not in out


def test_a_diverged_s_seed_fails_and_a_non_finite_baseline_voids(recs):
    b = arm(recs[0], "r2b_b")
    s = arm(recs[0], "r2b_s", fine=0.3)
    _set_seed_means(A.p3_cell(s, "fine"), "disp_rel_l2", [0.05, float("nan"), 0.06])
    out = _adj(b, s, recs)
    assert out["verdict"].startswith("NOT SUPPORTED") and "diverged" in out["verdict"]
    s = arm(recs[0], "r2b_s", fine=0.3)
    _set_seed_means(A.p3_cell(b, "fine"), "disp_rel_l2", [0.2, float("inf"), 0.25])
    out = _adj(b, s, recs)
    assert out["verdict"].startswith("NOT EVALUATED") and "void" in out["verdict"]
    assert out["r2a_beside"] == {"not_evaluated": "R2b not evaluated"}


def test_the_rule_is_r2as(recs):
    """R2b's verdict is fejepa.analysis.adjudicate_fine3d.r2a_verdict on the
    same values (R2b changes no source)."""
    b, s = arm(recs[0], "r2b_b"), arm(recs[0], "r2b_s", fine=0.4, disp=0.8)
    out = _adj(b, s, recs)
    assert out["conditions"] == A.r2a_verdict(A.r2a_values(b), A.r2a_values(s))


# --------------------------------------------------------------- refusals --

def _refused(recs, b, s, match, **kw):
    with pytest.raises(ValueError, match=match):
        _adj(b, s, recs, **kw)


def test_refusals(recs):
    p2b = recs[0]
    good_b, good_s = arm(p2b, "r2b_b"), arm(p2b, "r2b_s", fine=0.3)
    x = copy.deepcopy(good_s)
    x["prereg"]["file"] = "PREREG_FINE3D.md"
    _refused(recs, good_b, x, "not PREREG_R2B.md")
    x = copy.deepcopy(good_s)
    x["config"]["workers"] = 2
    _refused(recs, good_b, x, "does not hash|not a stamped")
    _refused(recs, good_b, arm(p2b, "r2b_b"), "r2b_b's, not r2b_s's")
    x = arm(p2b, "r2b_s")
    x["config"]["model"]["dim"] = 128
    _restamp(x)
    _refused(recs, good_b, x, "beyond PREREG_R2B Sec. 2.*model.dim")
    x = arm(p2b, "r2b_s")
    x["config"]["model"]["kind"] = "bottleneck"
    _restamp(x)
    _refused(recs, good_b, x, "model.kind")
    x = arm(p2b, "r2b_b")
    x["config"]["experiments"]["e8"]["ar_only"] = False
    _restamp(x)
    _refused(recs, x, good_s, "not the AR-only form")
    x = arm(p2b, "r2b_b")
    x["config"]["experiments"]["e8"]["seed_offset"] = 0
    _restamp(x)
    _refused(recs, x, good_s, "seed offset is not 3")
    x = arm(p2b, "r2b_b")
    x["config"]["model"]["decode_scale"] = "l1"
    x["config"]["model"]["decode_scale_factor"] = S_FACTOR
    _restamp(x)
    _refused(recs, x, good_s, "baseline carries S's keys")
    x = arm(p2b, "r2b_s")
    x["config"]["model"]["decode_scale_factor"] = 2.0 ** -9
    _restamp(x)
    _refused(recs, good_b, x, "is not S")
    _refused(recs, good_b, arm(p2b, "r2b_s", git="prereg-r2b-1-gabcdef"), "ran on")
    x = arm(p2b, "r2b_s")
    x["provenance"]["datasets"][1]["manifest_sha256"] = "0" * 64
    _refused(recs, good_b, x, "another corpus")
    _refused(recs, good_b, arm(p2b, "r2b_s", seeds=(0, 1, 2)), "seeds are")
    x = arm(p2b, "r2b_s")
    A.p3_cell(x, "fine")["per_seed_eval"][1]["per_instance"]["vm_rel_l2"].pop()
    _refused(recs, good_b, x, "per-instance values for its 256")
    x = arm(p2b, "r2b_s", inband_p3=1.01)
    _refused(recs, good_b, x, "does not reproduce its E8 AR cell")
    with pytest.raises(ValueError, match="CONFIG_SHA256\\[r2b_s\\]"):
        J.adjudicate_arms(good_b, good_s, p2b, recs[1], dict(_entries(), r2b_s="f" * 64),
                          s_factor=S_FACTOR)
    bad = copy.deepcopy(p2b)
    bad["provenance"]["config_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="not the stamped Phase-2b run"):
        J.adjudicate_arms(good_b, good_s, bad, recs[1], _entries(), s_factor=S_FACTOR)


def test_a_refusal_leaves_r2b_not_evaluated(recs):
    out = J.adjudicate({"b": arm(recs[0], "r2b_b"), "s": arm(recs[0], "r2b_s", seeds=(0, 1, 2))},
                       recs[0], recs[1], _entries(), s_factor=S_FACTOR)
    assert out["R2b"]["verdict"].startswith("NOT EVALUATED: refused: ValueError")
    out = J.adjudicate(None, recs[0], recs[1], missing="R2b needs both reports: x")
    assert out["R2b"] == {"verdict": "NOT EVALUATED: R2b needs both reports: x"}


# ------------------------------------------------------------- deviations --

def test_deviations(recs):
    b, s = arm(recs[0], "r2b_b"), arm(recs[0], "r2b_s", fine=0.3)
    s["solve_ledger"] = {"total": 4}
    s["d9_reuse_states"] = True
    s["results"]["e8"]["metrics"]["d9_restart"]["units_resumed_from_epoch"] = {"ar 1024 4": 37}
    b["runtime_policy"] = dict(b["runtime_policy"], gpu="NVIDIA H100")
    shb = "a" * 64
    out = _adj(b, s, recs, amp_b=_amp((1.25, 1.3, 1.2), shb, repro=0.07, remesh_n=15, failed=1),
               b_sha256=shb)
    dev = out["deviations"]
    assert "R2b s: solve ledger 4 (expected 0)" in dev
    assert any(d.startswith("R2b s: restarted (units resumed {'ar 1024 4': 37}") for d in dev)
    assert any("different gpu ('NVIDIA H100' / 'NVIDIA GeForce RTX 5090')" in d for d in dev)
    assert any(d.startswith("R2b b: the amplitude record's predictions differ") for d in dev)
    assert any(d.startswith("R2b b: the amplitude record's remesh readings are not evaluated")
               for d in dev)
    assert out["mechanism"]["s"] == {"not_evaluated": "no amplitude record given"}


def test_an_amplitude_record_of_another_report_is_not_read(recs):
    b, s = arm(recs[0], "r2b_b"), arm(recs[0], "r2b_s", fine=0.3)
    out = _adj(b, s, recs, amp_b=_amp((1.25, 1.3, 1.2), "b" * 64), b_sha256="c" * 64,
               amp_s={"unreadable": "x is not in the return"})
    assert "measured on another report" in out["mechanism"]["b"]["not_evaluated"]
    assert "cannot be read" in out["mechanism"]["s"]["not_evaluated"]
    assert out["beyond_amplitude"]["not_evaluated"].startswith("ValueError")


# --------------------------------------------------------------- readings --

def test_uninformative_note(recs):
    """A fresh baseline without the deficit (its fine / in-band ratio of seed
    means below 1.5, or its median c* on the fine set below 1.10) makes a NOT
    SUPPORTED R2b uninformative; the verdict stands."""
    p2b = recs[0]
    b = arm(p2b, "r2b_b", fine=0.15)                       # ratio 8.62 x 0.15 = 1.29
    s = arm(p2b, "r2b_s", fine=0.15)
    out = _adj(b, s, recs)
    assert out["verdict"].startswith("NOT SUPPORTED")
    assert "ratio of seed means 1.29 < 1.5" in out["uninformative_note"]
    assert out["uninformative_cstar"].startswith("not evaluated: no usable amplitude record")
    b = arm(p2b, "r2b_b")
    s = arm(p2b, "r2b_s", fine=0.97)
    sha = "d" * 64
    out = _adj(b, s, recs, amp_b=_amp((1.05, 1.08, 1.06), sha), b_sha256=sha)
    assert "median c* on the fine set 1.06 < 1.1" in out["uninformative_note"]
    out = _adj(b, s, recs, amp_b=_amp((1.25, 1.3, 1.2), sha), b_sha256=sha)
    assert out["uninformative_note"] is None and "uninformative_cstar" not in out
    out = _adj(b, arm(p2b, "r2b_s", fine=0.2), recs, amp_b=_amp((1.0, 1.0, 1.0), sha),
               b_sha256=sha)
    assert out["verdict"] == "SUPPORTED" and out["uninformative_note"] is None


def test_readings(recs):
    p2b = recs[0]
    b = arm(p2b, "r2b_b", fine=1.6)                        # the fresh baseline higher
    s = arm(p2b, "r2b_s", fine=0.3, disp=0.7)
    sha = "e" * 64
    out = _adj(b, s, recs, amp_b=_amp((1.25, 1.3, 1.2), sha, disp_c=(0.11, 0.12, 0.10)),
               b_sha256=sha)
    flags = out["fresh_baseline_vs_phase2b"]["flags"]
    assert len(flags) == 1 and flags[0].startswith("fine_displacement: the fresh baseline is "
                                                   "higher than the Phase-2b seeds 0-2")
    vb, vs = out["values"]["b"], out["values"]["s"]
    assert out["paired_per_seed"]["fine_displacement"] == pytest.approx(
        [x / y - 1 for x, y in zip(vs["fine_disp"], vb["fine_disp"], strict=True)])
    assert out["paired_per_seed"]["fine_displacement"] == pytest.approx([0.3 / 1.6 - 1] * 3)
    ba = out["beyond_amplitude"]
    assert ba["guard"]["base_per_seed"] == [0.11, 0.12, 0.10]
    assert ba["guard"]["new_per_seed"] == vs["fine_disp"]
    rel, tau = _hand_guard([0.11, 0.12, 0.10], vs["fine_disp"])
    assert math.isclose(ba["guard"]["rel_change"], rel) and ba["S_is"] == (
        "better" if rel < -tau else "worse" if rel > tau else "within the guard")
    side = out["r2a_beside"]
    f3 = recs[1]["R2a"]["conditions"]
    assert side["R2a_verdict"] == "SUPPORTED"
    for cond in ("fine_displacement", "fine_over_inband_ratio", "K1_inband_energy_gap",
                 "K1_inband_displacement"):
        assert side["conditions"][cond]["bottleneck"]["rel_change"] == f3[cond]["rel_change"]
        assert side["conditions"][cond]["transformer"]["rel_change"] == \
            out["conditions"][cond]["rel_change"]
    assert side["fine_reduction_ratio"] == pytest.approx(
        out["conditions"]["fine_displacement"]["rel_change"]
        / f3["fine_displacement"]["rel_change"])
    sims = _load(ROOT / "records" / "wp9" / "r2b" / "simulations.json")
    assert side["c_star_k"] == sims["k"] == J.C_STAR_K
    kp4 = out["kp4_line"]
    assert kp4["line"] == 1.5 == p2b["config"]["kills"]["KP4_transfer_ratio"]
    assert kp4["b"] == {"ratio_of_seed_means": vb["ratio_of_seed_means"], "below_line": False}
    assert kp4["s"]["ratio_of_seed_means"] == pytest.approx(
        np.mean(vs["fine_disp"]) / np.mean(vs["p3_inband_disp"]))
    assert kp4["s"]["below_line"] is bool(kp4["s"]["ratio_of_seed_means"] < 1.5)
    assert set(out["comparisons"]) == {"fine", "p3_inband", "e8_inband"}
    assert set(out["comparisons"]["fine"]) >= {"energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err",
                                               "crit_recall"}
    assert set(out["robustness"]) == {"fine_displacement", "fine_over_inband_ratio",
                                      "K1_inband_energy_gap", "K1_inband_displacement"}


def test_pinned_inputs_are_the_records():
    assert hashlib.sha256(P2B.read_bytes()).hexdigest() == A.PHASE2B_REPORT_SHA256
    assert hashlib.sha256(F3V.read_bytes()).hexdigest() == J.FINE3D_VERDICT_SHA256
    assert _load(P2B)["provenance"]["config_sha256"] == J.PHASE2B_CONFIG_SHA256 == \
        _mod("make_r2b_configs").BASE_SHA256
    assert J.STEPS == ("r2b_s", "amp_r2b_s", "r2b_b", "amp_r2b_b")
    assert all((ROOT / f).is_file() for f in J.ADJ_FILES)


# ------------------------------------------------------------ the script --

def _stamped(tmp_path):
    st = _mod("stamp_prereg_r2b")
    pf = tmp_path / "PREREG_R2B.md"
    text = (ROOT / "PREREG_R2B.md").read_text(encoding="utf-8")
    if text.rstrip("\n").endswith(st.FOOTER_OPEN):
        pf.write_text(text, encoding="utf-8")
        st.stamp(pf, ROOT / "configs", "4 November 2026")
    else:
        pf.write_text(text, encoding="utf-8")
    return pf


def test_the_script_adjudicates_a_return(recs, tmp_path):
    ret = tmp_path / "return"
    for name, kw in (("r2b_b", {}), ("r2b_s", {"fine": 0.25, "disp": 0.6, "egap": 0.8})):
        (ret / name).mkdir(parents=True)
        (ret / name / "report.json").write_text(json.dumps(arm(recs[0], name, **kw)))
    (ret / "posthoc").mkdir()
    sha_b = hashlib.sha256((ret / "r2b_b" / "report.json").read_bytes()).hexdigest()
    (ret / "posthoc" / "amp_r2b_b.json").write_text(json.dumps(_amp((1.25, 1.3, 1.2), sha_b)))
    (ret / "session").mkdir()
    (ret / "session" / "status.txt").write_text(
        "r2b_s.log start 2026-11-05 10:00:00 host box driver 575.64\n"
        "r2b_s.log exit=0 2026-11-08 21:00:00\n"
        "amp_r2b_s.log start 2026-11-08 21:00:02 host box driver 575.64\n"
        "amp_r2b_s.log exit=0 2026-11-08 21:45:00\n"
        "r2b_b.log start 2026-11-08 21:45:02 host box driver 575.64\n"
        "r2b_b.log exit=0 2026-11-12 08:00:00\n")
    pf = _stamped(tmp_path)
    out = tmp_path / "verdict.json"
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "adjudicate_r2b.py"),
                        "--r2b-b", str(ret / "r2b_b" / "report.json"),
                        "--r2b-s", str(ret / "r2b_s" / "report.json"),
                        "--amp-b", str(ret / "posthoc" / "amp_r2b_b.json"),
                        "--amp-s", str(ret / "posthoc" / "amp_r2b_s.json"),
                        "--status", str(ret / "session" / "status.txt"),
                        "--prereg", str(pf), "--out", str(out)],
                       capture_output=True, text=True, cwd=ROOT, env=ENV)
    assert r.returncode == 0, r.stderr[-3000:]
    v = json.loads(out.read_text())
    assert v["R2b"]["verdict"] == "SUPPORTED" and v["tag"] == "prereg-r2b"
    dev = v["deviations"]
    assert "amp_r2b_b: not started" in dev
    adj = v["adjudicator"]
    if adj["tag_available"]:            # the stamped, tagged commit (on the box)
        assert adj["differs_from_tag"] == [] and adj["prereg_is_tags"] is True
        assert not any("prereg-r2b" in d for d in v["session_and_code_deviations"])
    else:                               # before the tag (the sandbox)
        assert ("the adjudicating code and the pre-registration read were not compared with "
                "prereg-r2b (the tag cannot be read here)") in dev
    assert v["machines"] == {k: [("box", "575.64")] for k in ("r2b_s", "amp_r2b_s", "r2b_b")} \
        or v["machines"] == {k: [["box", "575.64"]] for k in ("r2b_s", "amp_r2b_s", "r2b_b")}
    assert not any("host" in d for d in dev)
    assert v["R2b"]["mechanism"]["s"]["not_evaluated"].startswith("ValueError: the amplitude "
                                                                  "record cannot be read")
    assert "beyond_amplitude" in v["R2b"] and "guard" in v["R2b"]["beyond_amplitude"]
    assert v["attempts"] == {"r2b_s": 1, "amp_r2b_s": 1, "r2b_b": 1}
    assert v["adjudicator"]["prereg_self_hash_ok"] is True
    assert set(v["inputs"]) >= {str(ret / "r2b_b" / "report.json"), str(P2B), str(F3V), str(pf)}
    summary = json.loads(r.stdout)
    assert summary["R2b"] == "SUPPORTED"


def test_the_script_records_hosts_and_the_condition_ii_note(recs, tmp_path):
    """Steps started on two hosts, and a start line without its host and
    driver, are deviations; a NOT SUPPORTED R2b failing condition (ii) alone
    carries its note in words."""
    ret = tmp_path / "return"
    for name, kw in (("r2b_b", {}), ("r2b_s", {"fine": 0.5, "egap": 0.5, "disp": 0.5})):
        (ret / name).mkdir(parents=True)
        (ret / name / "report.json").write_text(json.dumps(arm(recs[0], name, **kw)))
    st = tmp_path / "status.txt"
    st.write_text("r2b_s.log start 2026-11-05 10:00:00 host box driver 575.64\n"
                  "r2b_s.log exit=0 2026-11-08 21:00:00\n"
                  "amp_r2b_s.log start 2026-11-08 21:00:02\n"
                  "amp_r2b_s.log exit=0 2026-11-08 21:45:00\n"
                  "r2b_b.log start 2026-11-08 21:45:02 host box2 driver 580.10\n"
                  "r2b_b.log exit=0 2026-11-12 08:00:00\n"
                  "amp_r2b_b.log start 2026-11-12 08:00:02 host box2 driver \n"
                  "amp_r2b_b.log exit=0 2026-11-12 08:45:00\n")
    pf = _stamped(tmp_path)
    out = tmp_path / "v.json"
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "adjudicate_r2b.py"),
                        "--r2b-b", str(ret / "r2b_b" / "report.json"),
                        "--r2b-s", str(ret / "r2b_s" / "report.json"), "--status", str(st),
                        "--prereg", str(pf), "--out", str(out)],
                       capture_output=True, text=True, cwd=ROOT, env=ENV)
    assert r.returncode == 0, r.stderr[-3000:]
    v = json.loads(out.read_text())
    assert v["R2b"]["verdict"].startswith("NOT SUPPORTED: (ii)")
    dev = v["deviations"]
    assert any(d.startswith("the session's steps started on more than one host or GPU driver")
               for d in dev)
    assert "amp_r2b_s: an attempt's start line does not record its host and driver" in dev
    assert f"R2b: {J.CONDITION_II_ALONE}" in v["notes"]
    assert v["machines"]["amp_r2b_b"] == [["box2", ""]]


def test_the_script_refuses_the_draft_and_other_inputs(tmp_path):
    def run(*extra):
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "adjudicate_r2b.py"),
                               *extra], capture_output=True, text=True, cwd=ROOT, env=ENV)
    draft = (ROOT / "PREREG_R2B.md").read_text(encoding="utf-8")
    if "<fill before tagging>" in draft:
        r = run()
        assert r.returncode != 0 and "not stamped" in r.stderr
    bad = tmp_path / "p2b.json"
    bad.write_text(P2B.read_text() + " ")
    r = run("--phase2b", str(bad))
    assert r.returncode != 0 and "not the Phase-2b report" in r.stderr
    r = run("--fine3d-verdict", str(bad))
    assert r.returncode != 0 and "not fine3d's verdict file" in r.stderr


def test_the_script_without_reports_is_not_evaluated(tmp_path):
    pf = _stamped(tmp_path)
    out = tmp_path / "v.json"
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "adjudicate_r2b.py"),
                        "--r2b-b", str(tmp_path / "missing.json"), "--prereg", str(pf),
                        "--out", str(out)], capture_output=True, text=True, cwd=ROOT, env=ENV)
    assert r.returncode == 0, r.stderr[-2000:]
    v = json.loads(out.read_text())
    assert v["R2b"]["verdict"] == ("NOT EVALUATED: R2b needs both reports: "
                                   f"{tmp_path / 'missing.json'} is not in the return, "
                                   "--r2b-s was not given")
    assert "the session's status file was not given (--status)" in v["deviations"]
