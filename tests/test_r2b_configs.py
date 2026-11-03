"""R2b (PREREG_R2B Sec. 2): the two configurations are the generator's; each
differs from the stamped Phase-2b configuration only in the keys Sec. 2 names
(E2's AR-only edit among them, imported from its generator) and from R2a's
configuration of the same role only in the bottleneck's three model keys, its
output and its pre-registration; S's factor is R2a's; the runner accepts both
for the transformer, AR only, on the fresh seeds."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from fejepa.analysis.adjudicate_w9 import config_diff
from fejepa.report import config_sha256

ROOT = Path(__file__).resolve().parents[1]
S_KEYS = {("model", "decode_scale"), ("model", "decode_scale_factor"),
          ("model", "features", "load_density")}
AR_ONLY = {("experiments", "e8", "ar_only"), ("experiments", "e6", "enabled"),
           ("experiments", "wp6", "enabled"), ("experiments", "p3_transfer", "fewshot_budgets"),
           ("experiments", "p3_transfer", "naive_budget")}
NAMED = {("_comment",), ("out",), ("prereg_file",), ("experiments", "e8", "seed_offset")}


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _cfg(name):
    return json.loads((ROOT / "configs" / f"{name}.json").read_text())


def test_the_committed_configurations_are_the_generators():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "make_r2b_configs.py"), "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr[-2000:]
    assert list(_mod("make_r2b_configs").ARMS) == ["r2b_b", "r2b_s"]


def test_the_generator_refuses_another_base(tmp_path, monkeypatch):
    g = _mod("make_r2b_configs")
    base = _cfg("phase2b_v1")
    assert config_sha256(base) == g.BASE_SHA256
    assert f"CONFIG_SHA256 = {g.BASE_SHA256}" in (ROOT / "PREREG_PHASE2B.md").read_text()
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "phase2b_v1.json").write_text(json.dumps(dict(base, workers=3)))
    monkeypatch.setattr(g, "ROOT", tmp_path)
    with pytest.raises(SystemExit, match="not PREREG_PHASE2B's stamped"):
        g.load_base()


def test_r2b_differs_from_phase2b_only_in_the_named_keys():
    base = _cfg("phase2b_v1")
    b, s = _cfg("r2b_b"), _cfg("r2b_s")
    assert config_diff(b, base) == NAMED | AR_ONLY
    assert config_diff(s, base) == NAMED | AR_ONLY | S_KEYS
    assert config_diff(b, s) == {("_comment",), ("out",)} | S_KEYS
    for c in (b, s):
        ex = c["experiments"]
        assert ex["e8"]["ar_only"] is True and ex["e8"]["seed_offset"] == 3
        assert ex["e8"]["seeds"] == 3 and ex["e8"]["pool_sizes"] == [1024]
        assert ex["e8"]["ar_epochs"] == 200 and c["pretrain"] == {"epochs": 200, "lr": 0.001}
        assert ex["e6"]["enabled"] is False and ex["wp6"]["enabled"] is False
        assert ex["p3_transfer"]["fewshot_budgets"] == [] and ex["p3_transfer"]["naive_budget"] == 0
        assert "kind" not in c["model"]                       # the FE-JEPA transformer
        assert (c["model"]["dim"], c["model"]["depth"], c["model"]["heads"]) == (256, 8, 8)
        assert c["prereg_file"] == "PREREG_R2B.md" and c["prereg_guard"] is True
        assert c["tf32"] is True and c["workers"] == 1
    assert b["out"] == "runs/r2b/r2b_b/report.json" and s["out"] == "runs/r2b/r2b_s/report.json"
    assert "kind" not in base["model"] and "ar_only" not in base["experiments"]["e8"]


def test_the_ar_only_edit_is_e2s():
    """The AR-only keys are E2's edit of the same experiments (imported by the
    generator from scripts/make_e_series_configs.py, not copied)."""
    e2 = _cfg("e2_m1024")
    base = _cfg("phase2b_v1")
    exp = {p for p in config_diff(e2, base) if p[0] == "experiments"}
    assert exp == AR_ONLY
    assert _cfg("r2b_b")["experiments"] == dict(e2["experiments"],
                                                e8=dict(e2["experiments"]["e8"], seed_offset=3))


def test_r2b_is_r2a_without_the_bottleneck():
    for r2b, r2a in (("r2b_b", "r2a_b_m1024"), ("r2b_s", "r2a_s_m1024")):
        assert config_diff(_cfg(r2b), _cfg(r2a)) == {
            ("model", "kind"), ("model", "n_tokens"), ("model", "decode_k"), ("_comment",),
            ("out",), ("prereg_file",)}


def test_s_factor_is_r2as():
    s = _cfg("r2b_s")["model"]
    f3 = _mod("make_fine3d_configs")
    assert s["decode_scale"] == "l1" and s["features"]["load_density"] is True
    assert s["decode_scale_factor"] == f3.S3_FACTOR == 2.0 ** -10 == \
        _cfg("r2a_s_m1024")["model"]["decode_scale_factor"]
    assert "decode_scale" not in _cfg("r2b_b")["model"]


def test_r2b_configurations_pass_the_runners_checks():
    pytest.importorskip("torch")
    from fejepa.experiments.runner import run_config

    for name in ("r2b_b", "r2b_s"):
        out = run_config(ROOT / "configs" / f"{name}.json", dry_run=True)
        assert out["model_kind"] == "fejepa" and out["ar_only"] is True
        assert out["experiments_enabled"] == ["e8", "p3_transfer"]
        assert out["plan_steps"] == {"e8": 614400, "total": 614400}
        assert out["label_need_pool_prefix"] == 0
