"""Checks of the gate G-F1 code (f1): configuration hash and data pins, test readings, hardening curves, the
interpolation and bracketing of the verdict, the code check of the command line, and a dry run of the whole pipeline
(every case kind, the verdict and its tables) on B-19 and T-19 with the "tiny" meshes and longer steps. B-13 and T-13,
the gate's specimens, are never solved here."""
import copy
import json

import numpy as np
import pytest

from f1 import config as C
from f1.config import config, config_hash, canonical
from f1.materials import hardening_points
from f1.readings import read_tests, moment_reading, rising_branch
from f1.run import cases, case_id, run_case, bracket_values
from f1.verdict import at_point, bracket, evaluate, numbers_markdown
from f1 import __main__ as cli


def test_config_hash_is_stable_and_pins_data():
    cfg = config()
    assert config_hash() == config_hash() and len(config_hash()) == 64
    assert set(cfg["specimens"]) == {"B-13", "T-13"} and set(config(True)["specimens"]) == {"B-19", "T-19"}
    for f, h in cfg["data_sha256"].items():
        assert C.sha256(C.DATA / f) == h
    assert canonical(cfg) == canonical(json.loads(canonical(cfg)))


def test_readings_are_the_stated_rules():
    r = read_tests(config())
    c1 = r["B-13"]["C1"]
    assert np.isclose(c1["value"], np.mean(c1["per_figure"]))
    assert c1["tolerance"] >= abs(c1["per_figure"][0] - c1["per_figure"][1]) / 2 + C.PIXEL["moment_kNm"]
    c3 = r["B-13"]["C3"]
    assert np.isclose(c3["value"], c3["upper_hi"] - (c3["upper_lo"] + c3["lower_lo"]) / 2)
    c2 = r["T-13"]["C2"]
    assert np.isclose(c2["value"], np.mean(c2["per_figure"])) and c2["tolerance"] >= C.PIXEL["displacement_mm"]
    assert len(r["B-13"]["measured_preload_kN"]) == 6
    th, M = rising_branch("B13_test_fig33.csv")
    assert np.all(np.diff(th) > 0) and np.all(np.diff(M) >= 0)
    with pytest.raises(ValueError):
        moment_reading(["B13_test_fig33.csv", "B13_test_fig37.csv"], 0.5)
    from f1.readings import bolt_at, displacement_at, _series
    with pytest.raises(ValueError):
        bolt_at("boltforce_B13.csv", "1-2 upper", 1000.0)
    with pytest.raises(ValueError):
        _series("boltforce_B13.csv", "bolt 7")
    with pytest.raises(ValueError):
        displacement_at("T13_test_fig25.csv", 5000.0)


def test_hardening_curves_are_convex_and_start_at_fy():
    for spec in list(C.PLATES.values()) + [C.TUBE]:
        a, s, h = hardening_points(spec)
        assert a[0] == 0 and s[0] == spec["fy"] and np.all(np.diff(a) > 0) and np.all(np.diff(s) >= 0) and h >= 0
        assert len(a) <= 18


def test_interpolation_and_bracket():
    rec = {"preload": {"forces_kN": [125.0] * 6, "converged": True, "kkt_ok": True},
           "levels": [{"Theta_D": 0.0005, "M_kNm": 40.0, "T_kN": 0.0, "delta_mm": 0.0, "bolts_kN": [127.0] * 6,
                       "converged": True, "kkt_ok": True},
                      {"Theta_D": 0.0015, "M_kNm": 90.0, "T_kN": 0.0, "delta_mm": 0.0, "bolts_kN": [140.0] * 6,
                       "converged": True, "kkt_ok": True}]}
    assert at_point(rec, "Theta_D", 0.001, "M_kNm") == (65.0, "ok")
    assert at_point(rec, "Theta_D", 0.00025, "M_kNm") == (20.0, "ok")          # from the preload state
    assert at_point(rec, "Theta_D", 0.002, "M_kNm") == (None, "missing")
    bad = copy.deepcopy(rec); bad["levels"][0]["kkt_ok"] = False
    assert at_point(bad, "Theta_D", 0.001, "M_kNm") == (None, "invalid")
    t = {"value": 10.0, "tolerance": 1.0}
    assert bracket(t, 9.5, 12.0) and bracket(t, 12.0, 9.5) and bracket(t, 11.0, 12.0) and not bracket(t, 11.5, 12.0)
    assert not bracket(t, None, 12.0)


def test_gate_refuses_wrong_hash_and_changed_code(tmp_path, monkeypatch):
    with pytest.raises(SystemExit):
        cli.main(["run", "--sha", "0" * 64, "--out", str(tmp_path)])
    lst = tmp_path / "code.sha256"
    target = C.DATA / "boltforce_B13.csv"
    lst.write_text(f"{'0' * 64}  {target.relative_to(cli.ROOT)}\n")
    monkeypatch.setattr(cli, "CODE_LIST", lst)
    assert cli.check_code() == [str(target.relative_to(cli.ROOT))]
    lst.write_text(f"{C.sha256(target)}  {target.relative_to(cli.ROOT)}\n")
    assert cli.check_code() == []


def test_command_line_paths_without_solving(tmp_path, monkeypatch, capsys):
    """hash, readings and cases print; run refuses a missing or failing code list and an unknown case; existing
    records are kept; the mesh flag needs its coarse record. Nothing is solved."""
    with pytest.raises(SystemExit):
        cli.main(["-h"])
    assert "verdict --sha SHA --out DIR" in capsys.readouterr().out
    cli.main(["hash"]); cli.main(["hash", "--dry"])
    out = capsys.readouterr().out.split()
    assert out == [config_hash(), config_hash(True)]
    cli.main(["readings", "--dry"]); assert '"B-19"' in capsys.readouterr().out
    cli.main(["cases"]); ids = capsys.readouterr().out.split()
    assert ids == [case_id(c) for c in cases(config())] and len(ids) == 14
    with pytest.raises(SystemExit, match="--out"):
        cli.main(["run", "--dry"])
    monkeypatch.setattr(cli, "CODE_LIST", tmp_path / "absent.sha256")
    with pytest.raises(SystemExit, match="missing"):
        cli.main(["run", "--sha", config_hash(), "--out", str(tmp_path)])
    lst = tmp_path / "code.sha256"
    lst.write_text(f"{'0' * 64}  f1/config.py\n")
    monkeypatch.setattr(cli, "CODE_LIST", lst)
    with pytest.raises(SystemExit, match="f1/config.py"):
        cli.main(["verdict", "--sha", config_hash(), "--out", str(tmp_path)])
    with pytest.raises(SystemExit, match="no case"):
        cli.main(["run", "--dry", "--case", "B-13_frictionless_hencky_nominal_coarse", "--out", str(tmp_path)])
    cfg = config(True)
    case = cases(cfg)[0]
    (tmp_path / "records").mkdir(exist_ok=True)
    (tmp_path / "records" / f"{case_id(case)}.json").write_text("{}")
    logs = []
    assert run_case(cfg, case, tmp_path, log=logs.append).name == f"{case_id(case)}.json"
    assert logs and "skipped" in logs[0]
    flag = next(c for c in cases(cfg) if c["mesh"] == "medium")
    with pytest.raises(FileNotFoundError):
        run_case(cfg, flag, tmp_path / "other", log=logs.append)


def test_verdict_without_records_fails_and_prints(tmp_path):
    cfg = config(True)
    res = evaluate(cfg, read_tests(cfg), tmp_path)
    assert res["verdict"] == "FAIL" and set(res["criteria"]) == {"C1", "C2", "C3"}
    assert all(m["status"] == "no record" for v in res["criteria"].values() for m in v["models"].values())
    assert all(v["flagged"] for k, v in res["reported"].items() if k.startswith("mesh flag"))
    md = numbers_markdown(res)
    assert "missing (no record)" in md and "**Verdict: FAIL**" in md
    rec = {"preload": {"forces_kN": [125.0] * 6, "converged": True, "kkt_ok": True},
           "levels": [{"Theta_D": 0.001, "M_kNm": 30.0, "T_kN": 0.0, "delta_mm": 0.0, "bolts_kN": [126.0] * 6,
                       "converged": True, "kkt_ok": True}]}
    from f1.verdict import model_quantity
    assert model_quantity(rec, "B-19", cfg, "C3") == (None, "missing")
    with pytest.raises(ValueError):
        model_quantity(rec, "B-19", cfg, "C4")


def test_remaining_branches_without_solving(tmp_path, monkeypatch, capsys):
    """Branches the other tests leave: a blank line in the code list, the run loop and the verdict through the
    command line, broken KKT limits, comparison points a path does not reach, and the reported points."""
    from f1.config import KKT_LIMITS
    from f1.run import kkt_ok
    from f1.verdict import points_of
    target = C.DATA / "boltforce_B13.csv"
    lst = tmp_path / "code.sha256"
    lst.write_text(f"\n{C.sha256(target)}  {target.relative_to(cli.ROOT)}\n\n")
    monkeypatch.setattr(cli, "CODE_LIST", lst)
    assert cli.check_code() == []
    cfg = config(True)
    cid = case_id(cases(cfg)[0])
    out = tmp_path / "out"
    (out / "records").mkdir(parents=True)
    (out / "records" / f"{cid}.json").write_text("{}")
    cli.main(["run", "--dry", "--case", cid, "--out", str(out)])
    assert capsys.readouterr().out.strip() == f"{cid}.json exists, skipped"
    cli.main(["verdict", "--dry", "--out", str(tmp_path / "empty")])
    assert capsys.readouterr().out.split() == ["FAIL"]
    res = json.loads((tmp_path / "empty" / "verdict.json").read_text())
    assert res["verdict"] == "FAIL" and res["config_sha256"] == config_hash(True)
    assert "**Verdict: FAIL**" in (tmp_path / "empty" / "numbers.md").read_text()
    assert json.loads((tmp_path / "empty" / "config.json").read_text()) == json.loads(canonical(cfg))
    at_limits = {k: lim for k, (op, lim) in KKT_LIMITS.items()}
    assert kkt_ok(at_limits)
    for k, (op, lim) in KKT_LIMITS.items():
        assert not kkt_ok({**at_limits, k: lim - 1.0 if op == ">=" else lim + 1.0})
        assert not kkt_ok({**at_limits, k: float("nan")})
    lv = [{"control_value": c, "Theta_D": th, "M_kNm": m} for c, th, m in
          [(0.0005, 0.0004, 20.0), (0.001, 0.0008, 40.0), (0.0015, 0.0012, 60.0)]]
    assert bracket_values("B-19", cfg, {"levels": lv}) == [0.0005, 0.001, 0.0015]   # 100 kNm is not reached
    assert bracket_values("B-19", cfg, {"levels": lv[:1]}) == []                     # no point is reached
    assert points_of("B-19", cfg, reported=True) == points_of("B-19", cfg) + [("Theta_D", 0.0005)]


def test_an_unconverged_level_ends_the_path(monkeypatch):
    """A level that does not converge is kept and ends the path; the verdict then treats the point as invalid or
    missing. The model is built and preloaded on the tiny mesh; only the level is replaced."""
    import f1.run as run_module
    fake = {"control_value": 0.0005, "M_kNm": 0.0, "T_kN": 0.0, "Theta_D": 0.0, "delta_mm": 0.0,
            "converged": False, "kkt_ok": False, "seconds": 0.0}
    monkeypatch.setattr(run_module, "_level", lambda *a, **k: dict(fake))
    logs = []
    rec = run_module.run_path("B-19", config(True), "frictionless", "elastic", "nominal", "tiny", log=logs.append)
    assert len(rec["levels"]) == 1 and not rec["levels"][0]["converged"] and len(logs) == 1
    assert rec["preload"]["converged"] and rec["preload"]["kkt_ok"]


def test_dry_pipeline_tiny(tmp_path):
    """Every case kind of the dry configuration (B-19, T-19), the mesh flag and the verdict, on tiny meshes."""
    cfg = config(True)
    cfg["model"]["mesh"] = "tiny"
    cfg["model"]["mesh_flag"]["mesh"] = "tiny-flag"
    cfg["loading"]["bending"]["step"] = 0.001
    cfg["loading"]["axial"]["step"] = 0.3
    logs = []
    for c in cases(cfg):
        run_case(cfg, c, tmp_path, log=logs.append)
    recs = {p.stem: json.loads(p.read_text()) for p in (tmp_path / "records").glob("*.json")}
    assert set(recs) == {case_id(c) for c in cases(cfg)}
    for k, r in recs.items():
        assert r["preload"]["converged"] and r["preload"]["kkt_ok"], k
        assert all(l["converged"] and l["kkt_ok"] for l in r["levels"]), k
    b = recs["B-19_frictionless_hencky_nominal_tiny"]
    assert b["levels"][-1]["Theta_D"] >= 1.2 * 0.001 and b["levels"][-1]["M_kNm"] >= 105.0
    t = recs["T-19_no-slip_hencky_nominal_tiny"]
    assert t["levels"][-1]["T_kN"] >= 1350.0 and t["control"] == "axial"
    m = recs["B-19_no-slip_hencky_measured_tiny"]
    assert np.allclose(m["preload"]["forces_kN"], m["preload"]["targets_kN"], rtol=1e-5)
    flag = recs["B-19_frictionless_elastic_nominal_tiny-flag"]
    assert [l["control_value"] for l in flag["levels"]] == bracket_values(
        "B-19", cfg, recs["B-19_frictionless_elastic_nominal_tiny"])
    res = evaluate(cfg, read_tests(cfg), tmp_path)
    assert set(res["criteria"]) == {"C1", "C2", "C3"} and res["verdict"] in ("PASS", "FAIL")
    for v in res["criteria"].values():
        assert all(m_["status"] == "ok" for m_ in v["models"].values())
    assert any(k.startswith("mesh flag") for k in res["reported"])
    md = numbers_markdown(res)
    assert "| C1 | B-19 |" in md and "Mesh flag" in md
