"""Checks of gate G-F2.1's code (f21): the pinned run configurations, the list of stamped files against the
imports, the rules of the sample's seed and the sample's configuration, the stamp check and the command line's
refusals, what the gate's functions refuse on made-up folders, the verdict's arithmetic on made-up files and, with
torch and the repository (set FEJEPA_REPO to its checkout), the host check on the reduced configuration. No test
draws with the gate's own configuration: the reduced configurations take days of January 2026 only."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

from f2 import data as D, devconfig
from f21 import config as C, gate

JOINT = Path(__file__).resolve().parents[1]
REPO = os.environ.get("FEJEPA_REPO")
needs_repo = pytest.mark.skipif(not REPO, reason="set FEJEPA_REPO to the repository checkout")
PAST = 20260102                        # a day of the past, listed among the used seeds: never the gate's
FAR = 99991231                         # "today" for the rule function, where the clock must not decide a test


@pytest.fixture(autouse=True)
def _guard_closed(monkeypatch):
    """Every test starts with the guard of the gate's sample closed, whatever ran before it in the process."""
    monkeypatch.setattr(C, "_STAMP_VERIFIED", False)


def main_module():
    spec = importlib.util.spec_from_file_location("f21_main", JOINT / "f21" / "__main__.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def smoke_module():
    spec = importlib.util.spec_from_file_location("f21_smoke", JOINT / "f21" / "smoke.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_run_configurations_are_the_pinned_development_presets():
    G = C.config()
    first, second = C.run_config(G, "first"), C.run_config(G, "second")
    assert first == devconfig.config(C.FIRST) and second == devconfig.config(C.SECOND)
    assert C.sha256(first) == C.PINS["first_config_sha256"] and C.sha256(second) == C.PINS["second_config_sha256"]
    assert D.data_sha256(first) == D.data_sha256(second) == C.PINS["data_sha256"]
    assert D.data_sha256(D.extra_config(second)) == C.PINS["extra_data_sha256"]
    assert (first["arms"]["label_free"]["epochs"], first["training"]["members"]) == (400, ["train", 128])
    assert (second["arms"]["label_free"]["epochs"], second["training"]["extra_members"]["n"]) == (160, 32)
    assert not set(G["recipe"]["seeds"]) & set(G["recipe"]["training_seeds_kept_from_the_gate"])
    bad = json.loads(json.dumps(G))
    bad["recipe"]["first"]["config_sha256"] = "0" * 64
    with pytest.raises(RuntimeError):
        C.run_config(bad, "first")


def _imports(start: list[str]) -> set[str]:
    """The files below joint/ that the given modules import, by their import statements (those inside functions
    too)."""
    def find(mod):
        p = JOINT.joinpath(*mod.split("."))
        return p.with_suffix(".py") if p.with_suffix(".py").is_file() else (p / "__init__.py" if (p / "__init__.py").is_file() else None)

    seen, todo = {}, list(start)
    while todo:
        m = todo.pop()
        f = find(m) if m not in seen else None
        if f is None:
            continue
        seen[m] = f
        pkg = m if f.name == "__init__.py" else m.rpartition(".")[0]
        parts = m.split(".")
        todo += [".".join(parts[:k]) for k in range(1, len(parts))]
        for node in ast.walk(ast.parse(f.read_text())):
            if isinstance(node, ast.Import):
                todo += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    up = pkg.split(".")
                    up = up[:len(up) - (node.level - 1)] if node.level > 1 else up
                    base = ".".join([x for x in up if x] + ([node.module] if node.module else []))
                todo += [base] + [base + "." + a.name for a in node.names]
    return {str(f.relative_to(JOINT)).replace(os.sep, "/") for f in seen.values()}


def test_code_list_is_what_the_gate_imports():
    m = main_module()
    assert len(m.CODE) == len(set(m.CODE)) and all((JOINT / f).is_file() for f in m.CODE)
    assert set(m.CODE) == _imports(["f21", "f21.__main__", "f21.config", "f21.gate", "f21.smoke"])


def test_data_list_is_what_the_family_reads_and_is_gate_f1s():
    from f1.config import PLATES, TUBE
    from f2 import family

    m = main_module()
    assert sorted(m.DATA) == sorted("f1/data/" + x for x in (PLATES[family.PLATE_BASE]["curve"], TUBE["curve"], family.BOLT["curve"]))
    stamped = {}                                               # gate G-F1's stamp: hash, then name
    for line in (JOINT / "docs" / "G-F1_code.sha256").read_text().splitlines():
        if line.strip():
            h, name = line.split(None, 1)
            stamped[name.strip()] = h
    have = m.code_hashes()
    assert len(have) == len(m.CODE) + len(m.DATA) == 48
    assert all(have[f] == stamped[f] for f in m.DATA)          # the curves are the ones that gate G-F1 stamped


def _seeded(G: dict, seed) -> dict:
    G2 = copy.deepcopy(G)
    G2["sample"]["seed"] = seed
    return G2


def test_sample_seed_rules():
    from f21.stamp_day import SAMPLE_SEED

    G = C.config()
    s = G["sample"]
    assert s["seed"] == SAMPLE_SEED and s["not_before"] == 20261125 and s["not_after"] is None
    assert C.check_sample_seed(G, today=s["seed"]) == s["seed"]            # the rule only: nothing is drawn here
    with pytest.raises(ValueError, match="has not come"):
        C.check_sample_seed(G, today=s["seed"] - 1)
    for seed in s["family_seeds_used_before_stamp"] + [s["not_before"] - 1, 20261131, 5, 202611270, True, "20261125", 20261125.0]:
        with pytest.raises(ValueError):
            C.check_sample_seed(_seeded(G, seed), today=FAR)
    assert {11, 12, devconfig.TRAIN_SEED, devconfig.EVAL_SEED, devconfig.EXTRA_SEED, PAST, 20260103} <= set(s["family_seeds_used_before_stamp"])
    assert C.sha256(_seeded(G, s["seed"] + 1)) != C.sha256(G)              # the seed is part of the hashed configuration
    R = smoke_module().reduced()                               # the reduced configuration: days of January 2026 only
    assert (R["sample"]["seed"], R["sample"]["not_before"], R["sample"]["not_after"]) == (PAST, 20260101, 20260131)
    assert R["reference"]["linear_solver"] is None and G["reference"]["linear_solver"] == "pardiso"
    for seed, why in ((20251231, "lies before"), (20260201, "lies after"), (20260103, "drew members")):
        with pytest.raises(ValueError, match=why):
            C.check_sample_seed(_seeded(R, seed))
    for day in (s["not_before"], s["seed"], 20261231):         # no day that the stamp could fall on passes its rule
        with pytest.raises(ValueError, match="lies after"):
            C.check_sample_seed(_seeded(R, day), today=FAR)


def test_the_gates_sample_is_not_configured_outside_its_commands(tmp_path, monkeypatch):
    G = C.config()
    monkeypatch.setattr(C, "check_sample_seed", lambda cfg, today=None: cfg["sample"]["seed"])     # whatever the day is
    drawn = []
    monkeypatch.setattr(D, "members", lambda cfg: drawn.append(cfg) or [])
    assert C._STAMP_VERIFIED is False
    with pytest.raises(RuntimeError, match="by the gate's commands only"):
        C.sample_config(G)
    with pytest.raises(RuntimeError, match="by the gate's commands only"):
        gate.generate(G, "sample", tmp_path / "s")
    assert drawn == [] and not (tmp_path / "s").exists()       # nothing was drawn and nothing written
    assert C.sample_config(smoke_module().reduced())["gate"] != C.GATE     # a reduced configuration is not held back


def test_sample_configuration():
    R = smoke_module().reduced()                               # accepts the past day; the gate's own does not
    with pytest.raises(ValueError):
        C.sample_config(_seeded(C.config(), PAST))
    c = C.sample_config(R)
    second = C.run_config(R, "second")
    assert {k: v for k, v in c.items() if k not in ("data", "evaluation", "gate")} == \
           {k: v for k, v in second.items() if k not in ("data", "evaluation", "gate")}
    d = c["data"]
    assert (d["eval_seed"], d["n_eval"], d["eval_prefix"], d["n_train"], d["dev"], d["tested"]) == (PAST, 2, "gate", 0, {}, {})
    assert d["mesh"] == second["data"]["mesh"] and d["eval_levels"] == second["data"]["eval_levels"]
    assert c["evaluation"]["sets"] == ["eval"] and c["evaluation"]["members"] is None
    assert c["evaluation"]["readings"] == second["evaluation"]["readings"]
    m = D.members(c)
    assert [(i, s) for i, s, _ in m] == [("gate_0000", "eval"), ("gate_0001", "eval")]
    assert D.data_sha256(c) != D.data_sha256(second)
    big = json.loads(json.dumps(R))
    big["sample"]["n"] = 5                                     # a larger sample starts with the same members
    assert [q for _, _, q in D.members(C.sample_config(big))][:2] == [q for _, _, q in m]


def test_every_member_of_the_sample_is_evaluated():
    from f2.train import evaluated_ids

    assert evaluated_ids(C.sample_config(smoke_module().reduced())) == ["gate_0000", "gate_0001"]


def test_reported_exact_value_is_for_the_judged_reading():
    G = C.config()
    x = G["reported"]["exact"]
    assert x["readings"] == [G["judged"]["reading"]] and x["quantity"] not in G["reported"]["quantities"]
    assert G["judged"]["quantity"] == "abs_" + x["signed"] and G["judged"]["reading"] not in G["reported"]["readings"]


def test_development_members_are_unchanged():
    c = devconfig.config(C.SECOND)
    m = D.members(c)
    assert [sum(1 for _, s, _ in m if s == k) for k in ("train", "eval", "dev", "tested")] == [128, 16, 11, 4]
    assert (m[0][0], m[128][0]) == ("train_0000", "eval_0000")
    x = D.members(D.extra_config(c))
    assert len(x) == 32 and all(i.startswith("trainx_") and s == "train" and q.tp <= 12.5 for i, s, q in x)




def _stamp(m, tmp_path, monkeypatch):
    """A stamp file for the code as it is, in a temporary folder; the tree's own bytecode folders are not looked at
    (the test process writes them, a host's commands do not)."""
    monkeypatch.setattr(m, "STAMP_FILE", tmp_path / "stamp.sha256")
    monkeypatch.setattr(m, "bytecode_folders", lambda: [])
    lines = [f"{h}  {f}" for f, h in m.code_hashes().items()]
    (tmp_path / "stamp.sha256").write_text("\n".join(lines) + "\n")
    return lines


def test_stamp_check(tmp_path, monkeypatch):
    m = main_module()
    monkeypatch.setattr(m, "STAMP_FILE", tmp_path / "stamp.sha256")
    assert "not stamped" in m.not_stamped()
    lines = _stamp(m, tmp_path, monkeypatch)
    assert m.not_stamped() is None
    (tmp_path / "stamp.sha256").write_text("\n".join(lines[1:]) + "\n")
    assert "does not list" in m.not_stamped()
    (tmp_path / "stamp.sha256").write_text("\n".join(["0" * 64 + "  " + lines[0].split()[1]] + lines[1:]) + "\n")
    assert "differ" in m.not_stamped()
    (tmp_path / "stamp.sha256").write_text("\n".join(lines) + "\n")
    monkeypatch.setattr(m, "bytecode_folders", lambda: ["f2/__pycache__"])
    assert "bytecode" in m.not_stamped()


def test_bytecode_folders_are_those_of_the_stamped_packages(tmp_path, monkeypatch):
    m = main_module()
    for d in ("f21/__pycache__", "f2/__pycache__", "fejoint/sub/__pycache__", "tests/__pycache__", "probes/x/__pycache__"):
        (tmp_path / d).mkdir(parents=True)
    monkeypatch.setattr(m, "ROOT", tmp_path)
    assert [x.replace(os.sep, "/") for x in m.bytecode_folders()] == ["f2/__pycache__", "f21/__pycache__", "fejoint/sub/__pycache__"]


@needs_repo
def test_command_line_refuses_without_stamp_and_with_another_hash(tmp_path, monkeypatch):
    m = main_module()
    monkeypatch.setattr(m, "STAMP_FILE", tmp_path / "none.sha256")
    sha = C.sha256(C.config())
    args = ["generate", "--what", "train", "--data", str(tmp_path / "d"), "--repo", REPO]
    with pytest.raises(SystemExit, match="not stamped"):
        m.main(args + ["--config-sha", sha])
    with pytest.raises(SystemExit, match="differs"):
        m.main(args + ["--config-sha", "0" * 64])
    assert not (tmp_path / "d").exists()
    m.main(["write-config", "--out", str(tmp_path / "new" / "c.json"), "--repo", REPO])      # makes its folder
    assert C.sha256(json.loads((tmp_path / "new" / "c.json").read_text())) == sha
    with pytest.raises(SystemExit, match="not the stamped one"):
        m.main(["write-config", "--out", str(tmp_path / "c.json"), "--repo", REPO, "--config-sha", sha])
    _stamp(m, tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="not the stamped one"):
        m.main(["write-config", "--out", str(tmp_path / "c.json"), "--repo", REPO, "--config-sha", "0" * 64])
    monkeypatch.setattr(D, "_solver", lambda: C.config()["reference"]["linear_solver"])
    m.main(["write-config", "--out", str(tmp_path / "c.json"), "--repo", REPO, "--config-sha", sha])
    monkeypatch.setattr(D, "_solver", lambda: "scipy")         # a host without the configured solver
    with pytest.raises(SystemExit, match="linear solver"):
        m.main(["write-config", "--out", str(tmp_path / "c.json"), "--repo", REPO, "--config-sha", sha])
    m.main(["write-config", "--out", str(tmp_path / "c.json"), "--repo", REPO])              # without the hash: only prints
    with pytest.raises(RuntimeError, match="linear solver"):   # and the commands that solve refuse such a host
        m.main(args + ["--config-sha", sha])
    assert not (tmp_path / "d").exists()


@needs_repo
def test_chain_and_together(tmp_path, monkeypatch, capfd):
    m = main_module()
    for bad in ("train --cycle first --seed 5 --data d --runs r --config-sha x", "predict --seed 5", "smoke --out x",
                "verdict --final"):
        with pytest.raises(SystemExit, match="chain runs"):
            m.main(["chain", "--do", f"write-config --out {tmp_path / 'a.json'} --repo {REPO}", "--do", bad])
    assert not (tmp_path / "a.json").exists()                  # refused before its first command
    m.main(["chain", "--do", f"write-config --out {tmp_path / 'a.json'} --repo {REPO}",
            "--do", f"write-config --out {tmp_path / 'b.json'} --repo {REPO}"])
    assert (tmp_path / "a.json").read_bytes() == (tmp_path / "b.json").read_bytes()
    with pytest.raises(SystemExit):                            # a chain ends at its first error
        m.main(["chain", "--do", f"write-config --out {tmp_path / 'c.json'} --repo {REPO} --config-sha {'0' * 64}",
                "--do", f"write-config --out {tmp_path / 'd.json'} --repo {REPO}"])
    assert (tmp_path / "c.json").exists() and not (tmp_path / "d.json").exists()
    with pytest.raises(SystemExit) as e:                       # together: waits for all, names the failed one
        m.main(["together", "--logs", str(tmp_path / "logs"),
                "--do", f"write-config --out {tmp_path / 'e.json'} --repo {REPO}",
                "--do", f"write-config --out {tmp_path / 'f.json'} --repo {REPO} --config-sha {'0' * 64}"])
    assert e.value.code == 1 and (tmp_path / "e.json").exists() and (tmp_path / "f.json").exists()
    out = capfd.readouterr().out
    assert "all ended; failed: ['write-config --out" in out and "f.json" in out.split("all ended; failed:")[1]
    assert "config sha256" in (tmp_path / "logs" / "together_0.log").read_text()
    m.main(["together", "--logs", str(tmp_path / "logs2"), "--do", f"write-config --out {tmp_path / 'g.json'} --repo {REPO}"])


FILES4 = ("preds.npz", "preds_condensed.npz", "preds_base.npz", "condense.json")


def _history(G, cyc, s, status="finished"):
    return {"status": status, "steps": 6, "total_steps": 6, "config_sha256": G["recipe"][cyc]["config_sha256"],
            "seed": s, "epoch_seconds": [1.0, 2.0], "cap_events": [], "bursts": []}


def _made_up(tmp_path, G, values: dict, errors=(), failed=None, missing=None, exact_shift=0.001, not_started=()):
    """Files as the gate leaves them, with given judged values for each seed (a number, or seven numbers a member).
    The signed value is minus the judged one, and the exact value of the judged reading lies exact_shift beyond it.
    failed: ((seed, cycle), status) for a cycle that stopped for good; its seed has a record without predictions.
    missing: a seed whose predictions on the sample are not made yet. not_started: seeds without any run."""
    from f2.train import evaluated_ids

    runs, d, dg, rg = tmp_path / "runs", tmp_path / "data", tmp_path / "data_gate", tmp_path / "runs_gate"
    cfg, cfg2 = C.sample_config(G), C.run_config(G, "second")
    ids = [f"gate_{i:04d}" for i in range(G["sample"]["n"])]
    dg.mkdir(parents=True, exist_ok=True)
    (dg / "sample.json").write_text(json.dumps({"seed": G["sample"]["seed"], "gate_config_sha256": C.sha256(G)}))
    (dg / "manifest.json").write_text(json.dumps({"config_sha256": D.data_sha256(cfg), "instances": [
        {"id": i, "split": "eval", "params": {"tp": 11.0 if k == 0 else 20.0}} for k, i in enumerate(ids)]}))
    (dg / "labels").mkdir(exist_ok=True)
    (dg / "labels" / "ledger.json").write_text("[]")
    inputs = {"predictions": {}, "manifest_sha256": gate.file_sha256(dg / "manifest.json"),
              "ledger_sha256": gate.file_sha256(dg / "labels" / "ledger.json"), "linear_solver": "made up"}
    ev = {"config_sha256": C.sha256(cfg), "members": ids, "status": {}, "rows": {}, "exact_readings": ["condensed"],
          "inputs": inputs}
    dids = evaluated_ids(cfg2)
    (d / "labels").mkdir(parents=True, exist_ok=True)
    (d / "manifest.json").write_text(json.dumps({"made": "up"}))
    (d / "labels" / "ledger.json").write_text("[]")
    dv = {"config_sha256": C.sha256(cfg2), "members": dids, "status": {}, "rows": {},
          "inputs": {"predictions": {}, "manifest_sha256": gate.file_sha256(d / "manifest.json"),
                     "ledger_sha256": gate.file_sha256(d / "labels" / "ledger.json"), "linear_solver": "made up"}}
    for s in G["recipe"]["seeds"]:
        gone = failed is not None and failed[0][0] == s
        if s not in not_started:
            for cyc in ("first", "second"):
                if gone and failed[0][1] == "first" and cyc == "second":
                    continue                               # no second cycle after a first that stopped
                run = gate.run_dir(G, runs, cyc, s)
                run.mkdir(parents=True, exist_ok=True)
                st = failed[1] if gone and failed[0][1] == cyc else "finished"
                (run / "history.json").write_text(json.dumps(_history(G, cyc, s, st)))
                if st == "finished":
                    (run / "condense.json").write_text("{}")
        out = rg / f"label_free_s{s}"
        if s == missing:
            continue
        out.mkdir(parents=True, exist_ok=True)
        if gone or s in not_started:
            (out / "history.json").write_text(json.dumps({"status": "no predictions: made up", "seed": s,
                                                          "config_sha256": C.sha256(cfg), "prediction_files": None}))
            inputs["predictions"][str(s)] = None
            ev["status"][str(s)] = dv["status"][str(s)] = "missing"
            continue
        for f in FILES4:
            (out / f).write_bytes(f"{s} {f}".encode())
        files = {f: gate.file_sha256(out / f) for f in FILES4}
        (out / "history.json").write_text(json.dumps({"status": "finished", "seed": s, "config_sha256": C.sha256(cfg),
                                                      "trained_in": {}, "prediction_files": files}))
        inputs["predictions"][str(s)] = files
        ev["status"][str(s)] = dv["status"][str(s)] = "finished"
        x = values[s]
        for rd in ("condensed", "raw"):
            rows = {}
            for i in ids:
                if i in errors:
                    continue
                rows[i] = []
                for l in range(7):
                    e = x if isinstance(x, float) else x[l]
                    rows[i].append({"abs_curveD_err": e, "curveD_err": -e, "gap": 0.1})
                    if rd == "condensed":
                        rows[i][-1]["curveD_exact_err"] = -(e + exact_shift)
            ev["rows"][f"{s}|{rd}"] = {"members": rows, "errors": {i: "made up" for i in errors}}
            dv["rows"][f"{s}|{rd}"] = {"members": {i: [{"abs_curveD_err": 0.03}] * 7 for i in dids}, "errors": {}}
    (rg / gate.evaluation_file(G)).parent.mkdir(parents=True, exist_ok=True)
    (rg / gate.evaluation_file(G)).write_text(json.dumps(ev))
    (runs / gate.preset(G, "second")).mkdir(parents=True, exist_ok=True)
    (runs / gate.preset(G, "second") / gate.evaluation_file(G)).write_text(json.dumps(dv))
    return runs, d, dg, rg


def _edit(path, change):
    x = json.loads(Path(path).read_text())
    change(x)
    Path(path).write_text(json.dumps(x))


def test_verdict_on_made_up_files(tmp_path):
    G = smoke_module().reduced()
    name = gate.evaluation_file(G)
    a = _made_up(tmp_path / "a", G, {5: 0.01, 6: 0.02, 7: 0.2})         # one seed above both lines: the median decides
    v = gate.verdict(G, *a)
    assert v["verdict"] == "PASS" and v["complete"] and v["across_seeds"] == {"median": 0.02, "p90": 0.02}
    assert v["per_seed"]["7"] == {"median": 0.2, "p90": 0.2, "max": 0.2, "n": 14, "not_finite": 0}
    assert v["sample"]["thin_members"] == 1 and v["reported"]["5"]["thin_band"]["n"] == 7
    assert v["sample"]["seed"] == PAST and v["sample"]["inputs"]["manifest_sha256"] == gate.file_sha256(a[2] / "manifest.json")
    assert v["sample"]["inputs"]["ledger_sha256"] == hashlib.sha256(b"[]").hexdigest()
    assert v["runs"]["5"]["sample"]["prediction_files"] == v["sample"]["inputs"]["predictions"]["5"]
    assert "curveD_exact_err" not in v["reported"]["5"]["raw"] and v["reported"]["5"]["raw"]["gap"]["median"] == 0.1
    assert len(v["reported"]["5"]["by_level"]) == 7 and v["reported"]["5"]["not_finite_pairs"] == []
    assert sorted(v["development_members"]) == ["5", "6", "7"] and v["development"]["members"] == len(json.loads(
        (a[0] / gate.preset(G, "second") / name).read_text())["members"])
    x = v["exact"]                                                      # the exact value, reported beside the judged one
    assert x["per_seed"]["7"]["median"] == pytest.approx(0.201) and x["across_seeds"]["p90"] == pytest.approx(0.021)
    assert x["same_side_of_each_line"] == {"median": True, "p90": True}
    d = v["reported"]["6"]["first_order_minus_exact"]
    assert d["pairs"] == 14 and d["median"] == pytest.approx(0.001) and d["max"] == pytest.approx(0.001)
    text = main_module().verdict_text(v)
    assert text.startswith("Gate G-F2.1 host check (reduced): PASS") and "on the same side of each line" in text
    assert "not all on record" not in text
    near = _made_up(tmp_path / "near", G, {5: 0.0495, 6: 0.0495, 7: 0.0495})   # the exact value beyond a line
    v = gate.verdict(G, *near)
    assert v["verdict"] == "PASS" and v["exact"]["same_side_of_each_line"] == {"median": False, "p90": True}
    assert "median NO" in main_module().verdict_text(v)
    b = _made_up(tmp_path / "b", G, {5: 0.01, 6: 0.06, 7: 0.2})         # two seeds above the median's line
    assert gate.verdict(G, *b)["verdict"] == "FAIL"
    levels = [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.5]                  # the last level of every member is far off
    c = _made_up(tmp_path / "c", G, {5: levels, 6: levels, 7: 0.01})
    v = gate.verdict(G, *c)
    assert v["verdict"] == "FAIL" and v["across_seeds"]["median"] == 0.01      # 12 values of 0.01 and 2 of 0.5:
    assert v["across_seeds"]["p90"] == pytest.approx(0.01 + 0.7 * 0.49)       # the 90th percentile lies between them
    d = _made_up(tmp_path / "d", G, {5: 0.01, 6: 0.01, 7: 0.01}, errors=("gate_0001",))
    v = gate.verdict(G, *d)                                             # a member whose metrics failed: seven infinities
    assert v["per_seed"]["5"]["not_finite"] == 7 and v["per_seed"]["5"]["median"] == float("inf") and v["verdict"] == "FAIL"
    assert v["reported"]["5"]["not_finite_pairs"] == [["gate_0001", l] for l in range(7)]
    assert "gate_0001 level 7" in main_module().verdict_text(v)
    f = _made_up(tmp_path / "f", G, {5: 0.01, 6: 0.01, 7: 0.01}, missing=7)
    v = gate.verdict(G, *f)
    assert v["verdict"] == "INCOMPLETE" and v["waiting_seeds"] == [7] and "across_seeds" not in v["exact"]
    assert not v["complete"] and "INCOMPLETE" in main_module().verdict_text(v)


def test_verdict_counts_a_cycle_as_finished_only_with_its_predictions(tmp_path):
    G = smoke_module().reduced()
    runs, d, dg, rg = _made_up(tmp_path, G, {5: 0.01, 6: 0.01, 7: 0.01})
    assert gate.verdict(G, runs, d, dg, rg)["verdict"] == "PASS"
    (gate.run_dir(G, runs, "second", 7) / "condense.json").unlink()        # as if cut off in its last predictions
    assert gate.cycle_state(G, runs, "second", 7) == "under way" and gate.settled(G, runs) == (False, "the second cycle of seed 7 is under way")
    v = gate.verdict(G, runs, d, dg, rg)
    assert v["verdict"] == "INCOMPLETE" and v["waiting_seeds"] == [7] and v["runs"]["7"]["second"]["state"] == "under way"
    (gate.run_dir(G, runs, "second", 7) / "condense.json").write_text("{}")
    _edit(gate.run_dir(G, runs, "first", 6) / "history.json", lambda h: h.update(seed=5))
    with pytest.raises(RuntimeError, match="does not hold this seed's run"):
        gate.verdict(G, runs, d, dg, rg)


def test_verdict_needs_the_development_members_and_refuses_what_is_not_on_record(tmp_path):
    G = smoke_module().reduced()
    name = gate.evaluation_file(G)
    vals = {5: 0.01, 6: 0.01, 7: 0.01}
    runs, d, dg, rg = _made_up(tmp_path / "a", G, vals)
    dev = runs / gate.preset(G, "second") / name
    keep = dev.read_text()
    dev.unlink()                                               # without the development's members: not complete
    assert gate.verdict(G, runs, d, dg, rg)["verdict"] == "INCOMPLETE"
    dev.write_text(keep)
    _edit(dev, lambda x: x["status"].update({"7": "missing"}))
    assert gate.verdict(G, runs, d, dg, rg)["verdict"] == "INCOMPLETE"
    _edit(dev, lambda x: x.update(config_sha256="0" * 64))
    with pytest.raises(RuntimeError, match="another configuration"):
        gate.verdict(G, runs, d, dg, rg)
    dev.write_text(keep)
    _edit(dev, lambda x: x["members"].pop())
    with pytest.raises(RuntimeError, match="does not hold the configuration's members"):
        gate.verdict(G, runs, d, dg, rg)
    dev.write_text(keep)                                       # the development's evaluation against what it read
    assert gate.verdict(G, runs, d, dg, rg)["verdict"] == "PASS"
    (d / "labels" / "ledger.json").write_text("[ ]")
    with pytest.raises(RuntimeError, match="development's manifest or ledger"):
        gate.verdict(G, runs, d, dg, rg)
    (d / "labels" / "ledger.json").write_text("[]")
    (d / "manifest.json").rename(d / "manifest.away")
    with pytest.raises(RuntimeError, match="is not there"):
        gate.verdict(G, runs, d, dg, rg)
    (d / "manifest.away").rename(d / "manifest.json")
    run5 = gate.run_dir(G, runs, "second", 5)                  # prediction files that the evaluation did not read
    for f in FILES4:
        if not (run5 / f).exists():
            (run5 / f).write_bytes(b"later")
    with pytest.raises(RuntimeError, match="prediction files of the development's members"):
        gate.verdict(G, runs, d, dg, rg)
    _edit(dev, lambda x: x["inputs"]["predictions"].update({"5": {f: gate.file_sha256(run5 / f) for f in FILES4}}))
    assert gate.verdict(G, runs, d, dg, rg)["verdict"] == "PASS"
    (run5 / "preds.npz").write_bytes(b"changed")
    with pytest.raises(RuntimeError, match="prediction files of the development's members"):
        gate.verdict(G, runs, d, dg, rg)
    cases = {                                                  # the sample's evaluation against what is on record
        "the prediction files": lambda p: _edit(p[3] / "label_free_s5" / "history.json", lambda h: h["prediction_files"].update({"preds.npz": "f" * 64})),
        "manifest or ledger": lambda p: (p[2] / "manifest.json").write_text((p[2] / "manifest.json").read_text() + " "),
        "members are not": lambda p: _edit(p[3] / name, lambda x: x["members"].__setitem__(1, x["members"][0])),
        "exact value": lambda p: _edit(p[3] / name, lambda x: x.pop("exact_readings")),
        "another configuration": lambda p: _edit(p[3] / name, lambda x: x.update(config_sha256="0" * 64)),
        "another gate configuration": lambda p: _edit(p[2] / "sample.json", lambda x: x.update(gate_config_sha256="0" * 64)),
        "not the configuration's": lambda p: _edit(p[2] / "sample.json", lambda x: x.update(seed=20260103)),
    }
    for k, (why, change) in enumerate(cases.items()):
        paths = _made_up(tmp_path / f"c{k}", G, vals)
        assert gate.verdict(G, *paths)["verdict"] == "PASS"
        change(paths)
        with pytest.raises(RuntimeError, match=why):
            gate.verdict(G, *paths)


def test_after_a_stop_for_good(tmp_path):
    G = smoke_module().reduced()
    vals = {5: 0.01, 6: 0.01, 7: 0.01}
    # a second cycle stopped: the two other seeds finished and are reported; the verdict is FAIL and complete
    a = _made_up(tmp_path / "a", G, vals, failed=((6, "second"), "non-finite loss at step 4"))
    assert gate.cycle_state(G, a[0], "second", 6) == "stopped" and gate.settled(G, a[0]) == (True, "")
    v = gate.verdict(G, *a)
    assert (v["verdict"], v["failed_seeds"], v["waiting_seeds"], v["complete"]) == ("FAIL", [6], [], True)
    assert sorted(v["per_seed"]) == ["5", "7"] and "across_seeds" not in v
    rec6 = a[3] / "label_free_s6" / "history.json"             # the record that seed 6 has no predictions: lost
    keep6 = rec6.read_text()
    rec6.unlink()
    v = gate.verdict(G, *a)
    assert (v["verdict"], v["failed_seeds"], v["complete"]) == ("FAIL", [6], False)
    rec6.write_text(keep6)
    assert gate.verdict(G, *a)["complete"] is True
    (a[3] / gate.evaluation_file(G)).unlink()                  # what the finished seeds gave is not on record yet
    v = gate.verdict(G, *a)
    assert (v["verdict"], v["complete"]) == ("FAIL", False) and "not all on record" in main_module().verdict_text(v)
    # the first training stopped: nothing else was started, and nothing is started afterwards
    b = _made_up(tmp_path / "b", G, vals, failed=((5, "first"), "non-finite loss at step 2"), not_started=(6, 7))
    assert gate.training_states(G, b[0]) == {5: {"first": "stopped", "second": "not started"},
                                             6: {"first": "not started", "second": "not started"},
                                             7: {"first": "not started", "second": "not started"}}
    assert gate.settled(G, b[0]) == (True, "")
    for cyc, s in (("first", 6), ("second", 5)):
        with pytest.raises(RuntimeError, match="stopped for good|has not finished"):
            gate.train(G, cyc, s, b[1], b[0], device="cpu")
    assert not gate.run_dir(G, b[0], "first", 6).exists()
    v = gate.verdict(G, *b)
    assert (v["verdict"], v["failed_seeds"], v["complete"]) == ("FAIL", [5, 6, 7], True) and v["per_seed"] == {}


def test_predictions_on_the_sample_wait_for_every_training(tmp_path):
    G = smoke_module().reduced()
    vals = {5: 0.01, 6: 0.01, 7: 0.01}
    runs, d, dg, rg = _made_up(tmp_path / "a", G, vals, missing=5)
    for s in (6, 7):                                           # as if seed 5 were the first to finish
        (rg / f"label_free_s{s}" / "history.json").unlink()
    (gate.run_dir(G, runs, "second", 7) / "history.json").unlink()         # seed 7 is still in its second cycle
    assert gate.settled(G, runs) == (False, "the second cycle of seed 7 is under way")
    with pytest.raises(RuntimeError, match="before every training of the gate has ended"):
        gate.predict_sample(G, 5, runs, dg, rg, device="cpu")
    assert not (rg / "label_free_s5").exists()                 # a refusal leaves no folder
    with pytest.raises(RuntimeError, match="when every training has ended"):
        gate.evaluate(G, "dev", runs, d)
    with pytest.raises(RuntimeError, match="not one of the gate's"):
        gate.predict_sample(G, 0, runs, dg, rg, device="cpu")
    # after a stop for good a seed without a finished run gets its record, once
    runs, d, dg, rg = _made_up(tmp_path / "b", G, vals, failed=((6, "first"), "non-finite loss at step 2"), not_started=(7,))
    for s in (6, 7):
        (rg / f"label_free_s{s}" / "history.json").unlink()
    h6 = gate.predict_sample(G, 6, runs, dg, rg, device="cpu")
    h7 = gate.predict_sample(G, 7, runs, dg, rg, device="cpu")
    assert h6["status"] == "no predictions: the first cycle stopped on a non-finite value"
    assert h7["status"] == "no predictions: the first cycle was not started after a run of the gate had stopped for good"
    assert gate.predict_sample(G, 6, runs, dg, rg, device="cpu") == h6 and h6["prediction_files"] is None
    h5 = json.loads((rg / "label_free_s5" / "history.json").read_text())
    assert gate.predict_sample(G, 5, runs, dg, rg, device="cpu") == h5     # a finished record with its files: returned
    (rg / "label_free_s5" / "preds.npz").unlink()
    with pytest.raises(RuntimeError, match="nothing is predicted twice"):
        gate.predict_sample(G, 5, runs, dg, rg, device="cpu")
    (rg / "label_free_s5" / "preds.npz").write_bytes(b"5 preds.npz")
    v = gate.verdict(G, runs, d, dg, rg)
    assert (v["verdict"], v["failed_seeds"], v["complete"]) == ("FAIL", [6, 7], True) and sorted(v["per_seed"]) == ["5"]


def test_sample_evaluation_refusals(tmp_path, monkeypatch):
    G = smoke_module().reduced()
    vals = {5: 0.01, 6: 0.01, 7: 0.01}
    runs, d, dg, rg = _made_up(tmp_path / "a", G, vals)
    (rg / "label_free_s7" / "history.json").unlink()           # a seed without predictions and without a record
    with pytest.raises(RuntimeError, match="neither predictions on the sample nor a record"):
        gate.evaluate(G, "sample", rg, dg)
    runs, d, dg, rg = _made_up(tmp_path / "b", G, vals)
    (rg / "label_free_s5" / "preds.npz").write_bytes(b"other")
    with pytest.raises(RuntimeError, match="not the file"):
        gate.evaluate(G, "sample", rg, dg)
    runs, d, dg, rg = _made_up(tmp_path / "c", G, vals)
    before = (rg / gate.evaluation_file(G)).read_bytes()
    with pytest.raises(RuntimeError, match="fail their checks"):           # the made-up ledger holds no label
        gate.evaluate(G, "sample", rg, dg)
    assert (rg / gate.evaluation_file(G)).read_bytes() == before           # nothing was written
    assert gate.check_labels(G, "sample", dg) == {"labels": 0, "ok": False, "why": "no label is written"}
    (dg / "labels" / "ledger.json").unlink()
    assert gate.check_labels(G, "sample", dg)["ok"] is False
    G2 = _configured_solver(G)                                 # a configuration that names its linear solver
    runs, d, dg, rg = _made_up(tmp_path / "e", G2, vals)
    monkeypatch.setattr(D, "_solver", lambda: "scipy")         # and a host that has another one
    for call in (lambda: gate.evaluate(G2, "sample", rg, dg), lambda: gate.label(G2, "sample", dg),
                 lambda: gate.generate(G2, "sample", tmp_path / "new")):
        with pytest.raises(RuntimeError, match="linear solver"):
            call()
    with pytest.raises(RuntimeError, match="another gate configuration"):  # a folder of another configuration
        gate.label(G, "sample", dg)


def _configured_solver(G):
    G2 = copy.deepcopy(G)
    G2["reference"]["linear_solver"] = "pardiso"
    return G2


def test_sample_export_refusals_draw_nothing(tmp_path, monkeypatch):
    G = smoke_module().reduced()
    drawn = []
    monkeypatch.setattr(D, "members", lambda cfg: drawn.append(cfg) or [])
    monkeypatch.setattr(D, "generate", lambda *a, **k: pytest.fail("nothing may be exported"))
    for seed, why in ((20260103, "drew members"), (20251231, "lies before"), (20260201, "lies after"), (C.config()["sample"]["seed"], "lies after")):
        with pytest.raises(ValueError, match=why):
            gate.generate(_seeded(G, seed), "sample", tmp_path / "s")
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "stray.txt").write_text("x")
    with pytest.raises(RuntimeError, match="give a new folder"):
        gate.generate(G, "sample", tmp_path / "t")
    (tmp_path / "u").mkdir()
    (tmp_path / "u" / "sample.json").write_text(json.dumps({"seed": PAST, "gate_config_sha256": "0" * 64}))
    with pytest.raises(RuntimeError, match="another gate configuration"):
        gate.generate(G, "sample", tmp_path / "u")
    assert drawn == [] and not (tmp_path / "s").exists()
    with pytest.raises(RuntimeError, match="the draw gave 0 members"):     # only now is the draw asked for
        gate.generate(G, "sample", tmp_path / "s")
    assert len(drawn) == 1 and not (tmp_path / "s").exists()
    (tmp_path / "u" / "sample.json").write_text(json.dumps({"seed": PAST, "gate_config_sha256": C.sha256(G), "draw_sha256": "0" * 64}))
    monkeypatch.setattr(D, "members", lambda cfg: [(f"gate_{k:04d}", "eval", D.Params(*([1.0] * len(D.Params.__dataclass_fields__)))) for k in range(2)])
    with pytest.raises(RuntimeError, match="the draw differs"):
        gate.generate(G, "sample", tmp_path / "u")


def test_a_preload_that_is_not_on_target_stops_the_export(tmp_path, monkeypatch):
    G = smoke_module().reduced()

    def folder(name, entries):
        p = tmp_path / name
        p.mkdir()
        (p / "manifest.json").write_text(json.dumps({"instances": [{"id": i} for i in ("a", "b")]}))
        (p / "generate_log.json").write_text(json.dumps([{"id": i, "preload": pre} for i, pre in entries.items()]))
        return p

    ok = {"converged": True, "on_target": True}
    assert gate.check_preloads(folder("good", {"a": ok, "b": ok})) == 2
    for name, entries, why in (("off", {"a": ok, "b": {"converged": True, "on_target": False}}, "not on target"),
                               ("open", {"a": {"converged": False, "on_target": True}, "b": ok}, "not converged"),
                               ("gap", {"a": ok}, "no preload record")):
        with pytest.raises(RuntimeError, match=why):
            gate.check_preloads(folder(name, entries))
    bad = folder("thin", {"a": ok, "b": {"converged": True, "on_target": False}})
    monkeypatch.setattr(D, "generate", lambda *a, **k: bad / "manifest.json")      # the export itself ends normally
    for what in ("train", "thin"):
        with pytest.raises(RuntimeError, match="not on target"):
            gate.generate(G, what, bad)


def test_reference_check_of_a_labelled_member(tmp_path):
    np = pytest.importorskip("numpy")
    (tmp_path / "labels").mkdir()
    np.savez(tmp_path / "labels" / "m.npz", ThetaD=np.array([0.1, 0.3, 0.2]), Theta=np.zeros(3), z=np.zeros((3, 2)))
    assert gate._reference_member((str(tmp_path), "m")) == ("m", "the rotation of the measuring ring does not rise along the labelled path")
    np.savez(tmp_path / "labels" / "n.npz", ThetaD=np.array([0.1, 0.2, 0.3]), Theta=np.zeros(3), z=np.zeros((3, 2)))
    iid, why = gate._reference_member((str(tmp_path), "n"))    # its export is missing: reported, not raised
    assert iid == "n" and why.startswith("FileNotFoundError")


@needs_repo
def test_verdict_command_and_its_exit_codes(tmp_path, monkeypatch, capfd):
    m = main_module()
    R = smoke_module().reduced()
    monkeypatch.setattr(C, "config", lambda: copy.deepcopy(R))
    _stamp(m, tmp_path, monkeypatch)
    sha, vals = C.sha256(R), {5: 0.01, 6: 0.01, 7: 0.01}

    def run(paths, *more):
        runs, d, dg, rg = paths
        m.main(["verdict", "--runs", str(runs), "--data", str(d), "--data-gate", str(dg), "--runs-gate", str(rg),
                "--out", str(paths[0].parent / "out"), "--repo", REPO, "--config-sha", sha, *more])
        return json.loads((paths[0].parent / "out" / "verdict.json").read_text())

    a = _made_up(tmp_path / "a", R, vals)
    seen = []
    verdict0 = gate.verdict
    monkeypatch.setattr(gate, "verdict", lambda *x: seen.append(C._STAMP_VERIFIED) or verdict0(*x))
    v = run(a, "--final")
    assert seen == [True] and C._STAMP_VERIFIED is False       # open while the stamped command runs, closed after it
    assert v["verdict"] == "PASS" and len(v["code"]) == 48 and v["libraries"]["python"] and "PASS" in capfd.readouterr().out
    b = _made_up(tmp_path / "b", R, vals, missing=7)
    assert run(b)["verdict"] == "INCOMPLETE"                   # without --final: written, and the command ends with 0
    with pytest.raises(SystemExit, match="incomplete"):
        run(b, "--final")
    assert C._STAMP_VERIFIED is False                          # closed after a command that ended with an error too
    c = _made_up(tmp_path / "c", R, vals, failed=((6, "second"), "non-finite loss at step 4"))
    assert run(c, "--final")["verdict"] == "FAIL"
    (c[3] / gate.evaluation_file(R)).unlink()
    with pytest.raises(SystemExit, match="incomplete"):        # a FAIL whose reported values are not on record yet
        run(c, "--final")
    assert json.loads((tmp_path / "c" / "out" / "verdict.json").read_text())["verdict"] == "FAIL"
    with pytest.raises(SystemExit, match="differs"):
        m.main(["verdict", "--runs", "r", "--data", "d", "--data-gate", "g", "--runs-gate", "h", "--out", str(tmp_path / "o"),
                "--repo", REPO, "--config-sha", "0" * 64])


def test_evaluation_pool_is_not_forked_once_torch_is_loaded(monkeypatch):
    import multiprocessing as mp

    from f2 import evaluate as E

    made = []

    class Context:
        def __init__(self, kind):
            self.kind = kind

        def Pool(self, n):
            made.append((self.kind, n))

    can_fork = "fork" in mp.get_all_start_methods()
    monkeypatch.setattr(mp, "get_context", Context)
    monkeypatch.delitem(sys.modules, "torch", raising=False)
    for k in E.THREAD_VARIABLES:
        monkeypatch.delenv(k, raising=False)
    E.pool(3)                                                  # torch not loaded: as c22.data.pool
    assert made == [("fork" if can_fork else "spawn", 3)] and (not can_fork or not any(k in os.environ for k in E.THREAD_VARIABLES))
    monkeypatch.setitem(sys.modules, "torch", object())
    E.pool(2)                                                  # torch loaded: never forked
    assert made[1] == ("spawn", 2) and all(os.environ[k] == "1" for k in E.THREAD_VARIABLES)


@needs_repo
def test_host_check_on_the_reduced_configuration(tmp_path):
    pytest.importorskip("torch")
    sys.path.insert(0, str(Path(REPO) / "src"))
    main_module().main(["smoke", "--out", str(tmp_path / "smoke"), "--repo", REPO, "--device", "cpu", "--workers", "2"])
    rep = json.loads((tmp_path / "smoke" / "smoke.json").read_text())
    assert rep["ok"] and all(rep["checks"].values()) and len(rep["checks"]) == 19 and rep["sample_seed"] == PAST
    assert rep["stages"] == {k: "ended with exit code 0" for k in ("data", "train", "evaluate")}
    h = json.loads((tmp_path / "smoke" / "runs_gate" / "label_free_s5" / "history.json").read_text())
    state = tmp_path / "smoke" / "runs" / "dry_more_ux" / "label_free_s5" / "state.pt"
    assert h["trained_in"]["second"]["state_sha256"] == hashlib.sha256(state.read_bytes()).hexdigest()
