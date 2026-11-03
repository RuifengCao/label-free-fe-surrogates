"""R2b (PREREG_R2B Sec. 2, 3 and 8): the exact R2b path on a CPU miniature --
the generator's S configuration (the Phase-2b transformer with S, E8 AR on the
fresh seeds, P3 zero-shot), shrunk to gmsh3d corpora of a dozen instances and
run through run-config as the session runs it, then the post-hoc amplitude
pass on its report as the session runs it, and its remesh pass at two coarse
mesh sizes. The run
trains and evaluates the fresh seeds and reads no instance of the in-band
corpus's tail or of the fine set's few-shot prefix (PREREG_R2B Sec. 3); P3
evaluates exactly the states E8 trained (its in-band pass equals E8's AR cell
per instance, bit for bit on CPU); the amplitude pass reproduces the report's
rows exactly; the baseline's miniature starts each seed from the same weights
as S's."""

import copy
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("torch")
pytest.importorskip("gmsh")

from fejepa.experiments.runner import run_config
from fejepa.metrics import FIELD_KEYS

ROOT = Path(__file__).resolve().parents[1]
ENV = {"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin:/usr/local/bin"}

_READ = None


def _audit(event, args):
    """Files opened for reading while _READ is a list (an audit hook cannot be
    removed, so it records only then)."""
    if _READ is not None and event == "open" and isinstance(args[0], (str, os.PathLike)) \
            and (args[1] is None or "r" in str(args[1])):
        _READ.append(os.fspath(args[0]))


sys.addaudithook(_audit)


def _gen():
    spec = importlib.util.spec_from_file_location("make_r2b_configs",
                                                  ROOT / "scripts" / "make_r2b_configs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mini(tmp, arm):
    """configs/<arm>.json as the generator makes it from the stamped Phase-2b
    configuration, with the corpora, the model and the training shrunk."""
    base = json.loads((ROOT / "configs" / "phase2b_v1.json").read_text())
    mini = copy.deepcopy(base)
    mini.update(data=dict(base["data"], dir=str(tmp / "data3d"), n=14, lc_range=[0.30, 0.36]),
                data_transfer=dict(base["data_transfer"], dir=str(tmp / "fine3d"), n=8, lc=0.24,
                                   split={"n_eval": 4, "n_fewshot_prefix": 4}),
                split={"n_val": 4, "seed": 1}, workers=1)
    mini["model"].update(dim=16, depth=1, heads=2, mgn_dim=16, mgn_depth=1)
    mini["experiments"]["e8"].update(pool_sizes=[8], seeds=2, ar_epochs=2, sup_epochs=2)
    cfg = _gen().r2b_config(mini, arm)
    cfg.update(prereg_guard=False, out=str(tmp / arm / "report.json"), device="cpu", tf32=False)
    return cfg


@pytest.fixture(scope="module")
def run_s(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("r2b_path")
    cfg = _mini(tmp, "r2b_s")
    p = tmp / "r2b_s_mini.json"
    p.write_text(json.dumps(cfg))
    from fejepa.data.archive import instance_files

    global _READ
    _READ = []
    try:
        run_config(p)
        read = list(_READ)
    finally:
        _READ = None
    return (tmp, cfg, json.loads((tmp / "r2b_s" / "report.json").read_text()),
            {"read": read, "files": instance_files(tmp / "data3d"),
             "fine_files": instance_files(tmp / "fine3d")})


def test_the_s_run_trains_and_evaluates_the_fresh_seeds(run_s):
    tmp, cfg, rep, _ = run_s
    m = rep["config"]["model"]
    assert "kind" not in m and m["decode_scale"] == "l1"
    assert m["decode_scale_factor"] == 2.0 ** -10 and m["features"]["load_density"] is True
    assert rep["provenance"]["seeds"] == [3, 4]
    assert rep["results"]["p3_transfer"]["protocol"]["seeds"] == [3, 4]
    assert list(rep["results"]["e8"]["metrics"]["cells"]) == ["ar"]
    assert list(rep["results"]["p3_transfer"]["metrics"]["ar"]) >= ["fine", "inband"]
    assert sorted(p.name for p in (tmp / "r2b_s" / "e8_states").glob("ar_*.pt")) == \
        ["ar_p8_s3.pt", "ar_p8_s4.pt"]
    assert int(rep["solve_ledger"]["total"]) == 0 or rep["solve_ledger"]["per_stage"]


def test_p3_evaluates_exactly_the_states_e8_trained(run_s):
    """P3 reloads each state from disk into a model built from the report's
    configuration; E8's AR cell evaluated the model it trained. On CPU the two
    agree per instance, bit for bit (the adjudication refuses more than 1e-3)."""
    from fejepa.analysis import adjudicate_fine3d as A

    _, _, rep, _ = run_s
    p3, e8 = A.p3_cell(rep, "inband"), A.e8_cell(rep)
    assert len(p3["per_seed_eval"]) == len(e8["per_seed_eval"]) == 2
    for a, b in zip(p3["per_seed_eval"], e8["per_seed_eval"], strict=True):
        for k in FIELD_KEYS:
            assert a["per_instance"][k] == b["per_instance"][k], k
    assert A.p3_e8_deviation(rep) == 0.0


def test_the_s_run_reads_no_tail_and_no_few_shot_prefix(run_s):
    """PREREG_R2B Sec. 3: the validation split is fixed by its seed and the
    training pool is the first of the split's pool files, so the pool files
    after it (the tail R1's holdout is drawn from) are never opened; P3 reads
    the fine set's evaluation instances and not its few-shot prefix."""
    from fejepa.experiments.protocol import load_split

    tmp, cfg, _, io = run_s
    split = load_split(tmp / "data3d", int(cfg["split"]["n_val"]), int(cfg["split"]["seed"]))
    pool = int(cfg["experiments"]["e8"]["pool_sizes"][0])
    tail = {str(f) for f in split.pool_files[pool:]}
    assert len(tail) == 2 and len(io["files"]) == 14
    opened = {str(Path(f)) for f in io["read"]}
    assert not opened & tail
    assert {str(f) for f in split.pool_files[:pool]} <= opened      # the pool was read
    assert {str(f) for f in split.val_files} <= opened
    n_eval = int(cfg["data_transfer"]["split"]["n_eval"])
    fine = [str(f) for f in io["fine_files"]]
    assert len(fine) == 8
    assert set(fine[:n_eval]) <= opened and not opened & set(fine[n_eval:])


def test_the_amplitude_pass_reproduces_the_s_report(run_s, tmp_path):
    """scripts/posthoc_amplitude.py on the S report as the session runs it,
    without the remesh pass (on the CPU the transformer's attention over a
    remesh geometry's fine mesh does not fit in memory; on the box it ran on
    the Phase-2b states in wp8 4e): the states of seeds 3 and 4, each
    reproducing its own rows of the report exactly; the adjudication reads the
    record, its remesh readings not evaluated."""
    from fejepa.analysis import adjudicate_fine3d as A

    tmp, _, rep, _ = run_s
    out = tmp_path / "amp_s.json"
    rp = tmp / "r2b_s" / "report.json"
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "posthoc_amplitude.py"),
                        "--report", str(rp), "--states-dir", str(tmp / "r2b_s" / "e8_states"),
                        "--n-inband", "4", "--n-fine", "4", "--device", "cpu",
                        "--out", str(out)],
                       capture_output=True, text=True, env=ENV)
    assert r.returncode == 0, r.stderr[-2000:]
    amp = json.loads(out.read_text())
    assert sorted(amp["seeds"]) == ["s3", "s4"] and amp["model_kind"] == "fejepa"
    for s in amp["seeds"].values():
        for name in ("inband", "fine"):
            rpr = s[name]["reproduction"]
            assert rpr["checked"] and rpr["disp_max_rel_dev"] == rpr["egap_max_rel_dev"] == 0.0
    chk = A.check_amp(amp, hashlib.sha256(rp.read_bytes()).hexdigest())
    assert chk["reproduction_max_rel_dev"] == 0.0 and "no remesh pass" in chk["remesh_not_evaluated"]
    mech = A.mechanism(amp, chk["remesh_not_evaluated"])
    assert mech["fine"]["c_star_median"]["per_seed"] and "not_evaluated" in mech["remesh"]


def test_the_remesh_pass_runs_on_the_transformer_with_s(run_s, monkeypatch):
    """The remesh pass of scripts/posthoc_amplitude.py on the S states (the
    script's own model loader and rows), at two coarse mesh sizes in place of
    the four of the box (see above): every geometry meshed at every size, c_b
    and the energy norms finite, the summary complete."""
    spec = importlib.util.spec_from_file_location("posthoc_amplitude",
                                                  ROOT / "scripts" / "posthoc_amplitude.py")
    pa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pa)
    from fejepa.analysis.posthoc import run_model, verified_states

    tmp, _, rep, _ = run_s
    states = verified_states(rep, tmp / "r2b_s" / "e8_states")
    models = {s: run_model(rep, p, s, "cpu") for s, p in states.items()}
    monkeypatch.setattr(pa, "REMESH_LC", (0.36, 0.30))
    rows = list(pa.remesh_rows(models, 2, "cpu"))
    assert len(rows) == 2
    for g in rows:
        assert sorted(g) == [3, 4]
        for row in g.values():
            assert "error" not in row and [b["lc"] for b in row["by_lc"]] == [0.36, 0.30]
            assert all(math.isfinite(b["c_battery"]) and b["n_nodes"] > 0 for b in row["by_lc"])
            assert all(np.all(np.isfinite(b["u_norm_K"])) for b in row["by_lc"])
    summ = pa.remesh_summary([g[3] for g in rows])
    assert summ["n_geometries"] == 2 and summ["n_failed"] == 0
    assert set(summ) >= {"c_battery_median_by_lc", "u_norm_K_ratio_median_by_lc"}


def test_the_baseline_starts_each_seed_from_s_weights(run_s):
    """The baseline's miniature, one epoch: its first AR unit's network is
    built from the seed exactly as S's (the same initial weights; PREREG_R2B
    Sec. 2), and the run differs from S's only in what S changes."""
    torch = pytest.importorskip("torch")
    from fejepa.experiments.parallel import _build_model

    tmp, cfg_s, _, _ = run_s
    cfg_b = _mini(tmp, "r2b_b")
    from fejepa.analysis.adjudicate_w9 import config_diff

    assert config_diff(cfg_b, cfg_s) == {("_comment",), ("out",), ("model", "decode_scale"),
                                         ("model", "decode_scale_factor"),
                                         ("model", "features", "load_density")}
    for seed in (3, 4):
        a = _build_model({"kind": "fejepa", "model": cfg_b["model"], "seed": seed}).state_dict()
        b = _build_model({"kind": "fejepa", "model": cfg_s["model"], "seed": seed}).state_dict()
        assert all(torch.equal(a[k], b[k]) for k in a)
