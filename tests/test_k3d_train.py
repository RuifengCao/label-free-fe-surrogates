"""cmame-paper Stage 12 (PREREG_K3D Sec. 2, 3, 6, 7): scripts/k3d_train.py on a
CPU miniature of a Phase-2-shaped run whose E8 trained the labels-only and the
stiffness-norm rows beside its label-free states.

The script's L_K states are E8's `labels_knorm` states byte for byte, with
activation checkpointing off or on (the same initial weights, order and
loss); the stored states are evaluated to the report's own values; the
report's cells equal E8's. It refuses, before anything trains, a
configuration, a source report, a corpus, unlabelled training instances, a
stored state or a record that is not as named, a guarded run off its tag or
with a pre-registration whose last line does not verify, a second run while
one holds the lock, a missing, failing or busy GPU (exit status 2), a holdout
set that is not PREREG_HOLDOUT's or a holdout file that is not the manifest's,
and stored states that do not reproduce the report (exit status 5, no seed
trained). An interrupted seed resumes from its epoch checkpoint to the same
bytes; finished seeds and the stored states' evaluations are kept; a valid
checkpoint, result or evaluation of another configuration or commit is moved
aside. The holdout set is evaluated with its labels manifest recorded, or
skipped on request; the report then adjudicates (scripts/adjudicate_k3d.py)
end to end. Nothing here depends on the machine's GPU or torch build."""

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")

ROOT = Path(__file__).resolve().parents[1]
MODEL = {"dim": 16, "depth": 1, "heads": 2, "features": {"load_summary": True, "geometry": True}}
SEEDS = [0, 1]
N_VAL, BUDGET = 4, 4


def _sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _holdout_spec(tmp: Path, data: Path, rp: Path, cfg_reused: dict) -> tuple:
    """A PREREG_HOLDOUT-shaped configuration whose h3d set is the
    miniature's pool tail (one instance excluded), labelled as Sec. E labels."""
    from fejepa.analysis.holdout import expected_names, label_set
    from fejepa.data.archive import manifest_sha256

    tail = expected_names(12, N_VAL, 1, BUDGET)
    rows = {r: {"state": str(tmp / "p2" / "e8_states" / cfg_reused[r]["state"]),
                "cell": cfg_reused[r]["cell"], "kind": "fejepa",
                "sha256": cfg_reused[r]["sha256"], "sha256_source": "test"}
            for r in ("ar", "labels")}
    rows["mgn"] = {"state": str(tmp / "none_s{seed}.pt"), "cell": "4", "kind": "mgn",
                   "sha256": {str(s): "0" * 64 for s in SEEDS}, "sha256_source": "test"}
    sdef = {"corpus": str(data), "manifest_sha256": manifest_sha256(data), "n_corpus": 12,
            "split": {"n_val": N_VAL, "seed": 1}, "used_prefix": BUDGET,
            "excluded": [tail[0]], "n_holdout": len(tail) - 1, "report": str(rp),
            "report_sha256": _sha(rp), "rows": rows}
    h2d = dict(sdef, rows=dict(rows, labels_knorm=rows["labels"]))
    h2d["rows"] = {k: h2d["rows"][k] for k in ("ar", "labels", "labels_knorm", "mgn")}
    spec = {"_comment": "test", "prereg_file": str(tmp / "PREREG_HOLDOUT.md"),
            "seeds": SEEDS, "out": str(tmp / "holdout"),
            "labels": {"method": "direct", "stage": "holdout-labels", "residual_max": 1e-8},
            "content_tol": 1e-3, "sets": {"h3d": sdef, "h2d": h2d},
            "criteria": {"guard_band": 0.10, "guard_k": 2.0, "most": 0.5, "almost_all": 0.95,
                         "halved": -0.5, "representative_alpha": 0.05}}
    sp = tmp / "holdout_v1.json"
    sp.write_text(json.dumps(spec, indent=1))
    label_set("h3d", sdef, tmp / "holdout" / "h3d", log=lambda *_: None)
    return sp, tmp / "holdout" / "h3d"


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    from fejepa.experiments.runner import run_config
    from fejepa.fe.synthetic import generate_synthetic_dataset

    tmp = tmp_path_factory.mktemp("k3d")
    data = generate_synthetic_dataset(tmp / "corpus", n=12, seed=3, labelled="all")
    cfg = {"data": {"dir": str(data), "n": 12, "seed": 3, "backend": "synthetic",
                    "labelled_policy": "asis"},
           "split": {"n_val": N_VAL, "seed": 1}, "model": MODEL,
           "sup": {"epochs": 2, "lr": 1.5e-3}, "pretrain": {"epochs": 1, "lr": 1e-3},
           "experiments": {"e8": {"enabled": True, "budgets": [2, BUDGET],
                                  "pool_sizes": [BUDGET], "seeds": len(SEEDS),
                                  "ar_epochs": 1, "sup_epochs": 2, "include_mgn": False,
                                  "include_ar_ft": False, "include_anchor": False,
                                  "include_knorm": True}},
           "runtime": {"compile": False, "precision": "fp32"},
           "device": "cpu", "workers": 1, "tf32": False, "prereg_guard": False,
           "out": str(tmp / "p2" / "report.json")}
    (tmp / "p2.json").write_text(json.dumps(cfg))
    run_config(tmp / "p2.json")
    rp = tmp / "p2" / "report.json"
    rep = json.loads(rp.read_text())
    sd = tmp / "p2" / "e8_states"
    ar = rep["results"]["e8"]["metrics"]["d9_restart"]["ar_states"]
    labels = {f"labels_b{BUDGET}_s{s}.pt": _sha(sd / f"labels_b{BUDGET}_s{s}.pt") for s in SEEDS}
    rec = tmp / "labels_record.json"
    rec.write_text(json.dumps({"sha256": labels}))
    reused = {"ar": {"state": f"ar_p{BUDGET}_s{{seed}}.pt", "cell": str(BUDGET),
                     "sha256": {k[1:]: v["sha256"] for k, v in ar.items()},
                     "sha256_source": str(rp)},
              "labels": {"state": f"labels_b{BUDGET}_s{{seed}}.pt", "cell": str(BUDGET),
                         "sha256": {str(s): labels[f"labels_b{BUDGET}_s{s}.pt"]
                                    for s in SEEDS},
                         "sha256_source": str(rec)}}
    spec, hdir = _holdout_spec(tmp, data, rp, reused)
    base = {"source": {"report": str(rp), "report_sha256": _sha(rp), "states_dir": str(sd)},
            "reused": reused,
            "train": {"row": "labels_knorm", "loss": "knorm", "budget": BUDGET, "epochs": 2,
                      "lr": 1.5e-3, "weight_decay": 1e-4, "clip": 1.0, "warmup_frac": 0.05,
                      "activation_checkpointing": False},
            "seeds": SEEDS, "content_tol": 1e-6, "holdout": None,
            "out": str(tmp / "k3d" / "report.json"), "prereg_file": "PREREG_K3D.md",
            "prereg_guard": False, "device": "cpu"}
    return {"tmp": tmp, "data": data, "report_path": rp, "report": rep, "states": sd,
            "base": base, "spec": spec, "holdout_dir": hdir, "mod": _script("k3d_train")}


def _cfg(world, tmp: Path, name: str = "k3d_v1", **edit) -> Path:
    cfg = json.loads(json.dumps(world["base"]))
    cfg["out"] = str(tmp / "out" / "report.json")
    for k, v in edit.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k].update(v)
        else:
            cfg[k] = v
    p = tmp / f"{name}.json"
    p.write_text(json.dumps(cfg, indent=1))
    return p


@pytest.fixture(autouse=True)
def _git(monkeypatch):
    """The code's `git describe`, fixed (the script records it and compares
    it across attempts; a test checkout may have no tag or no git)."""
    from fejepa import report as rmod

    monkeypatch.setattr(rmod, "_git_describe", lambda: "test-describe")


def _stop(mod, capsys, *args, **kw) -> tuple:
    with pytest.raises(SystemExit) as ex:
        mod.run(*args, **kw)
    return ex.value.code, capsys.readouterr().out


@pytest.fixture(scope="module")
def full(world, tmp_path_factory):
    """The script run once to the end as a guarded run on its tag (the guard's
    check of the stamped hash and the code's `git describe` replaced),
    activation checkpointing off, with the holdout set."""
    from fejepa import report as rmod

    tmp = tmp_path_factory.mktemp("k3d_full")
    p = _cfg(world, tmp, prereg_guard=True,
             holdout={"spec": str(world["spec"]), "set": "h3d",
                      "dir": str(world["holdout_dir"])})
    want = rmod.config_sha256(json.loads(p.read_text()))
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(rmod, "verify_prereg", lambda cfg, pf, label=None: rmod.config_sha256(cfg))
        mp.setattr(world["mod"], "prereg_footer_ok", lambda path: True)
        mp.setattr(rmod, "_git_describe", lambda: "prereg-k3d")
        rep = world["mod"].run(p)
    assert rep["prereg"] == {"file": "PREREG_K3D.md", "config_sha256": want}
    return {"tmp": tmp, "config": p, "report": rep, "hash": want}


# ---------------------------------------------------------------- the run --

@pytest.mark.parametrize("ckpt", [False, True])
def test_the_lk_states_are_e8s_byte_for_byte(world, full, tmp_path, ckpt):
    mod = world["mod"]
    if ckpt:
        rep = mod.run(_cfg(world, tmp_path, train={"activation_checkpointing": True}))
        out = tmp_path / "out"
    else:
        rep, out = full["report"], full["tmp"] / "out"
    for s in SEEDS:
        mine = out / f"labels_knorm_b{BUDGET}_s{s}.pt"
        assert _sha(mine) == _sha(world["states"] / f"labels_knorm_b{BUDGET}_s{s}.pt")
        ps = rep["per_seed"][f"s{s}"]
        assert ps["state"]["sha256"] == _sha(mine)
        t = ps["train"]
        assert t["activation_checkpointing"] is ckpt and t["epochs_run"] == 2
        assert t["steps"] == 2 * BUDGET and len(t["loss_by_epoch"]) == 2
        assert t["resumed_from_epoch"] is None and t["loss"] == "knorm"
        assert t["files"] == [Path(f).name for f in mod.instance_sets(
            world["report"], BUDGET)["train"]]
        order = mod.epoch_orders(s, BUDGET, 2)
        assert t["order_sha256"] == hashlib.sha256(json.dumps(order).encode()).hexdigest()
    # the cells are E8's, and the stored states reproduce the report exactly
    e8 = world["report"]["results"]["e8"]["metrics"]["cells"]
    for row in ("ar", "labels", "labels_knorm"):
        got, want = rep["cells"][row][str(BUDGET)], e8[row][str(BUDGET)]
        for m in ("energy_gap_rel", "disp_rel_l2", "vm_rel_l2", "peak_vm_rel_err",
                  "crit_recall"):
            assert got[m]["per_seed"] == want[m]["per_seed"], (row, m)
            for a, b in zip(got["per_seed_eval"], want["per_seed_eval"], strict=True):
                assert a["per_instance"][m] == b["per_instance"][m]
    for k, c in rep["content_checks"].items():
        assert c["ok"] and c["finite"] and c["energy_gap_rel_max_rel_dev"] == 0.0, k
    assert rep["reused_evaluations_from_disk"] is False
    assert rep["rows"] == ["ar", "labels", "labels_knorm"]


def test_the_trainer_draws_the_order_epoch_orders_names(monkeypatch):
    """train_supervised's permutations are epoch_orders' (one generator
    seeded with the seed, one permutation per epoch, nothing else drawn)."""
    from fejepa.train import supervised

    mod = _script("k3d_train")
    want = mod.epoch_orders(7, 3, 3)
    seen = []
    real = np.random.default_rng

    class Spy:
        def __init__(self, seed):
            self.g = real(seed)

        def permutation(self, n):
            p = self.g.permutation(n)
            seen.append(p.tolist())
            return p

    monkeypatch.setattr(supervised.np.random, "default_rng", Spy)
    from fejepa.fe.synthetic import synthetic_instance
    from fejepa.experiments.parallel import _build_model

    r = real(5)
    archs = [synthetic_instance(r, nx=4, ny=3, labelled=True) for _ in range(3)]
    model = _build_model({"kind": "fejepa", "model": MODEL, "seed": 7})
    supervised.train_supervised(model, archs, archs[:1], supervised.SupervisedConfig(
        epochs=3, lr=1e-3, device="cpu", anchor_mode="none", loss="knorm", seed=7,
        log_every=-1))
    assert seen == want


# -------------------------------------------------------------- refusals --

def test_configuration_refusals(world, tmp_path, capsys):
    mod = world["mod"]
    cases = {
        "a key": dict(extra=1),
        "a training key": dict(train={"anchor_mode": "none"}),
        "the loss": dict(train={"loss": "disp"}),
        "the learning rate": dict(train={"lr": 1e-3}),
        "the epochs": dict(train={"epochs": 3}),
        "the budget": dict(train={"budget": 3}),
        "the weight decay": dict(train={"weight_decay": 0.0}),
        "the warm-up": dict(train={"warmup_frac": 0.1}),
        "checkpointing": dict(train={"activation_checkpointing": "off"}),
        "the seeds": dict(seeds=[0, 0]),
        "unknown seeds": dict(seeds=[0, 5]),
        "content_tol": dict(content_tol=0),
        "a holdout block": dict(holdout={"spec": "x", "set": "h3d"}),
        "the source report": dict(source={"report_sha256": "0" * 64}),
        "a stored state's record": dict(reused={"ar": dict(world["base"]["reused"]["ar"],
                                                           sha256={"0": "1" * 64,
                                                                   "1": "2" * 64})}),
    }
    for what, edit in cases.items():
        code, out = _stop(mod, capsys, _cfg(world, tmp_path, **edit), dry_run=True)
        assert code == 3 and out.startswith("STOP: "), what
    assert not (tmp_path / "out").exists()


def test_a_changed_stored_state_or_record_is_refused(world, tmp_path, capsys):
    mod = world["mod"]
    sd = tmp_path / "states"
    shutil.copytree(world["states"], sd)
    with open(sd / f"labels_b{BUDGET}_s1.pt", "ab") as f:
        f.write(b"\0")
    code, out = _stop(mod, capsys, _cfg(world, tmp_path, source={"states_dir": str(sd)}),
                      dry_run=True)
    assert code == 3 and "stored states refused" in out and f"labels_b{BUDGET}_s1.pt" in out
    # the labels' record must hold the SHA-256 the configuration copies
    rec = tmp_path / "rec.json"
    rec.write_text(json.dumps({"sha256": {}}))
    lab = dict(world["base"]["reused"]["labels"], sha256_source=str(rec))
    code, out = _stop(mod, capsys, _cfg(world, tmp_path, reused={"labels": lab}),
                      dry_run=True)
    assert code == 3 and "reused.labels" in out


def test_a_guarded_run_runs_on_its_tag_only(world, tmp_path, capsys, monkeypatch):
    from fejepa import report as rmod

    mod = world["mod"]
    st = _script("stamp_prereg_k3d")
    p = _cfg(world, tmp_path, name="k3d_t", prereg_guard=True,
             prereg_file=str(tmp_path / "PREREG_T.md"))
    (tmp_path / "PREREG_T.md").write_text("CONFIG_SHA256[k3d_t] = <fill before tagging>\n"
                                          + st.FOOTER_OPEN + "\n")
    code, out = _stop(mod, capsys, p, dry_run=True)
    assert code == 3 and "unstamped" in out
    cfg = json.loads(p.read_text())
    text = f"CONFIG_SHA256[k3d_t] = {rmod.config_sha256(cfg)}\n" + st.FOOTER_OPEN + "\n"
    (tmp_path / "PREREG_T.md").write_text(text)                  # the footer still open
    code, out = _stop(mod, capsys, p, dry_run=True)
    assert code == 3 and "its last line is not its own SHA-256" in out
    own = hashlib.sha256(text.encode()).hexdigest()
    (tmp_path / "PREREG_T.md").write_text(text.replace(st.FOOTER_OPEN,
                                                       f"PREREG_K3D_SHA256 = {own}"))
    monkeypatch.setattr(rmod, "_git_describe", lambda: "prereg-k3d-1-gabcdef1")
    code, out = _stop(mod, capsys, p, dry_run=True)
    assert code == 3 and "not 'prereg-k3d'" in out
    monkeypatch.setattr(rmod, "_git_describe", lambda: "prereg-k3d")
    plan = mod.run(p, dry_run=True)
    assert plan["git"] == "prereg-k3d" and plan["prereg"]["config_sha256"] == \
        rmod.config_sha256(cfg)
    assert plan["states_verified"] == 2 * len(SEEDS) and plan["n_train"] == BUDGET


@pytest.mark.parametrize("fault", ["absent", "fails", "busy"])
def test_the_gpu_must_work_and_be_free(world, tmp_path, capsys, monkeypatch, fault):
    """Exit status 2 before anything is written; the same on any machine
    (the GPU calls are replaced)."""
    mod = world["mod"]
    real_zeros = torch.zeros
    monkeypatch.setattr(torch.cuda, "is_available", lambda: fault != "absent")
    monkeypatch.setattr(torch.cuda, "synchronize", lambda *a, **k: None)
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda *a, **k: "Fake GPU")
    monkeypatch.setattr(torch.cuda, "mem_get_info",
                        lambda *a, **k: (2 << 30, 32 << 30) if fault == "busy"
                        else (31 << 30, 32 << 30))

    def zeros(*a, **k):
        if fault == "fails":
            raise RuntimeError("CUDA error: an illegal memory access was encountered")
        return real_zeros(1)

    monkeypatch.setattr(torch, "zeros", zeros)
    code, out = _stop(mod, capsys, _cfg(world, tmp_path), device_override="cuda")
    assert code == 2
    assert {"absent": "no GPU", "fails": "the GPU does not work",
            "busy": "the GPU is in use"}[fault] in out
    assert not (tmp_path / "out").exists()


def test_stored_states_that_do_not_reproduce_stop_before_training(world, tmp_path, capsys):
    mod = world["mod"]
    rep = json.loads(world["report_path"].read_text())
    cell = rep["results"]["e8"]["metrics"]["cells"]["labels"][str(BUDGET)]["per_seed_eval"][1]
    cell["per_instance"]["energy_gap_rel"] = [2 * v for v in
                                              cell["per_instance"]["energy_gap_rel"]]
    rp = tmp_path / "report.json"
    rp.write_text(json.dumps(rep))
    code, out = _stop(mod, capsys, _cfg(world, tmp_path, source={
        "report": str(rp), "report_sha256": _sha(rp)}))
    assert code == 5 and "labels_s1" in out
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == [".lock", "reused.json"]


def test_the_holdout_must_be_preregistered_holdouts(world, tmp_path, capsys):
    mod = world["mod"]
    good = {"spec": str(world["spec"]), "set": "h3d", "dir": str(world["holdout_dir"])}
    code, out = _stop(mod, capsys, _cfg(world, tmp_path, holdout=dict(good, set="h4d")),
                      dry_run=True)
    assert code == 3 and "defines no set" in out
    code, out = _stop(mod, capsys, _cfg(world, tmp_path, holdout=dict(
        good, dir=str(tmp_path / "nolabels"))), dry_run=True)
    assert code == 3 and "does not exist" in out
    spec = json.loads(Path(good["spec"]).read_text())
    spec["sets"]["h3d"]["rows"]["labels"]["sha256"] = {"0": "1" * 64, "1": "2" * 64}
    sp = tmp_path / "holdout_v1.json"
    sp.write_text(json.dumps(spec))
    code, out = _stop(mod, capsys, _cfg(world, tmp_path, holdout=dict(good, spec=str(sp))),
                      dry_run=True)
    assert code == 3 and "labels states are not this run's" in out
    hd = tmp_path / "h3d"
    shutil.copytree(good["dir"], hd)
    man = json.loads((hd / "manifest.json").read_text())
    man["excluded"] = []
    (hd / "manifest.json").write_text(json.dumps(man))
    code, out = _stop(mod, capsys, _cfg(world, tmp_path, holdout=dict(good, dir=str(hd))),
                      dry_run=True)
    assert code == 3 and "excluded" in out
    plan = mod.run(_cfg(world, tmp_path, holdout=good), dry_run=True)
    assert plan["holdout"] == 3
    assert mod.run(_cfg(world, tmp_path, holdout=good), dry_run=True,
                   skip_holdout=True)["holdout"] == "skipped"


# --------------------------------------------------------------- restart --

def test_an_interrupted_seed_resumes_to_the_same_bytes(world, full, tmp_path):
    from fejepa.train import supervised

    mod = world["mod"]
    p = _cfg(world, tmp_path)
    real = supervised.train_supervised

    def interrupted(model, archs, val, cfg, **kw):
        cfg.stop_after_epoch = 1
        real(model, archs, val, cfg, **kw)
        raise KeyboardInterrupt

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(supervised, "train_supervised", interrupted)
        with pytest.raises(KeyboardInterrupt):
            mod.run(p)
    out = tmp_path / "out"
    ck = out / f"labels_knorm_b{BUDGET}_s0.ckpt"
    assert ck.is_file() and json.loads((out / (ck.name + ".json")).read_text())["seed"] == 0
    rep = mod.run(p)
    for s in SEEDS:
        assert _sha(out / f"labels_knorm_b{BUDGET}_s{s}.pt") == \
            _sha(full["tmp"] / "out" / f"labels_knorm_b{BUDGET}_s{s}.pt")
    t0 = rep["per_seed"]["s0"]["train"]
    assert t0["resumed_from_epoch"] == 1 and len(t0["loss_by_epoch"]) == 2
    assert t0["loss_by_epoch"] == full["report"]["per_seed"]["s0"]["train"]["loss_by_epoch"]
    assert rep["per_seed"]["s1"]["train"]["resumed_from_epoch"] is None
    assert rep["reused_evaluations_from_disk"] is True
    assert not ck.exists() and not (out / (ck.name + ".json")).exists()
    # run again: every seed and the stored states' evaluations are kept
    again = mod.run(p)
    assert all(again["per_seed"][f"s{s}"].get("from_disk") for s in SEEDS)
    assert again["cells"] == rep["cells"]


def test_foreign_checkpoints_and_results_are_moved_aside(world, full, tmp_path):
    mod = world["mod"]
    p = _cfg(world, tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    ck = out / f"labels_knorm_b{BUDGET}_s0.ckpt"
    ck.write_bytes(b"not a checkpoint")
    (out / (ck.name + ".json")).write_text(json.dumps({"git": "x", "config_sha256": "y",
                                                       "seed": 1}))
    (out / "seed_1.json").write_text(json.dumps({"seed": 1, "git": "other"}))
    rep = mod.run(p)
    names = sorted(x.name for x in out.iterdir())
    assert any(n.startswith(ck.name + ".unusable.") for n in names)
    assert any(n.startswith("seed_1.json.unusable.") for n in names)
    for s in SEEDS:
        assert rep["per_seed"][f"s{s}"]["train"]["resumed_from_epoch"] is None
        assert _sha(out / f"labels_knorm_b{BUDGET}_s{s}.pt") == \
            _sha(full["tmp"] / "out" / f"labels_knorm_b{BUDGET}_s{s}.pt")


# --------------------------------------------------------------- holdout --

def test_the_holdout_set_is_evaluated_with_its_manifest_recorded(world, full):
    from fejepa.analysis.holdout import holdout_names, load_spec

    h = full["report"]["holdout"]
    sdef = load_spec(world["spec"])["sets"]["h3d"]
    names = holdout_names(sdef)
    assert h["set"] == "h3d" and h["n"] == len(names) == 3
    assert h["labels_manifest_sha256"] == _sha(world["holdout_dir"] / "manifest.json")
    z = np.load(full["tmp"] / "out" / h["arrays"])
    assert _sha(full["tmp"] / "out" / h["arrays"]) == h["arrays_sha256"]
    assert [str(f) for f in z["files"]] == names
    assert z["values"].shape == (3, len(SEEDS), 3, 5) and np.all(np.isfinite(z["values"]))
    assert z["gap_load"].shape == z["pi_load"].shape == (3, len(SEEDS), 3, 4)
    mets = [str(m) for m in z["metrics"]]
    for k, w in h["worse_than_zero"].items():
        assert w["sign_mismatch"] == 0 and w["finite"] == w["load_cases"] == 12, k
    for i, r in enumerate(("ar", "labels", "labels_knorm")):
        for j, s in enumerate(SEEDS):
            k = mets.index("energy_gap_rel")
            assert h["summary"][f"{r}_s{s}"]["energy_gap_rel"] == \
                pytest.approx(float(np.mean(z["values"][i, j, :, k])))


def test_the_report_adjudicates_end_to_end(world, full, tmp_path):
    """The miniature's report through scripts/adjudicate_k3d.py's checks and
    readings (the source report and configuration are the miniature's)."""
    adj = _script("adjudicate_k3d")
    cfg = json.loads(full["config"].read_text())
    rep = json.loads((full["tmp"] / "out" / "report.json").read_text())
    man = tmp_path / "manifest.json"
    shutil.copyfile(world["holdout_dir"] / "manifest.json", man)
    entries = {"k3d_v1": full["hash"]}
    res = adj.adjudicate_k3d(rep, cfg, entries, world["report"], _sha(world["report_path"]),
                             "prereg-k3d", status_text="k3d.log start t box\nk3d.log exit=0\n",
                             run_logs=1, holdout_npz=full["tmp"] / "out" / "holdout_arrays.npz",
                             holdout_manifest=man, holdout_spec=world["spec"])
    for h in ("H2a-3D", "H2b-3D"):
        assert res[h]["verdict"] in ("SUPPORTED", "NOT SUPPORTED"), res[h]
        assert res[h]["statistic"] == "per-seed medians" and "beside" in res[h]
    assert res["H3-3D"]["reading"] != "NOT EVALUATED"
    sec = res["secondary"]
    assert "not_evaluated" not in sec["holdout"], sec["holdout"]
    assert sec["holdout"]["n"] == 3 and sec["worse_than_zero"]["labels_knorm"]["of"] == \
        len(SEEDS) * N_VAL
    for k in ("seed_table", "comparisons", "pairing", "training"):
        assert "not_evaluated" not in sec[k], k
    # the GPU is a deviation here (a CPU run); the torch version only where it is
    # not the box's (on the box, 2.12.1+cu130, it is not)
    assert any(d.startswith("torch ") for d in res["deviations"]) == \
        (str(torch.__version__) != adj.TORCH)
    assert any(d.startswith("GPU ") for d in res["deviations"])
    # a manifest other than PREREG_HOLDOUT's leaves the holdout readings not evaluated
    man.write_text("{}")
    res2 = adj.adjudicate_k3d(rep, cfg, entries, world["report"], _sha(world["report_path"]),
                              "prereg-k3d", holdout_npz=full["tmp"] / "out" / "holdout_arrays.npz",
                              holdout_manifest=man, holdout_spec=world["spec"])
    assert "not PREREG_HOLDOUT's" in res2["secondary"]["holdout"]["not_evaluated"]
    assert res2["H2a-3D"] == res["H2a-3D"]



# ------------------------------------------------- after the first reviews --

def test_the_corpus_and_the_training_labels_are_checked_before_the_gpu(world, tmp_path, capsys):
    from fejepa.data.archive import has_labels

    mod = world["mod"]
    other = tmp_path / "corpus"
    shutil.copytree(world["data"], other)
    man = json.loads((other / "manifest.json").read_text())
    man["seed"] = 99
    (other / "manifest.json").write_text(json.dumps(man))
    code, out = _stop(mod, capsys, _cfg(world, tmp_path), data_dir=str(other), dry_run=True)
    assert code == 3 and out.startswith("STOP: the corpus:")
    code, out = _stop(mod, capsys, _cfg(world, tmp_path), data_dir=str(tmp_path / "none"),
                      dry_run=True)
    assert code == 3 and out.startswith("STOP: the corpus")
    # a training instance without its labels, in a corpus whose manifest is the run's
    shutil.rmtree(other)
    shutil.copytree(world["data"], other)
    f = Path(mod.instance_sets(world["report"], BUDGET, str(other))["train"][2])
    with np.load(f, allow_pickle=False) as z:
        arrays = {k: z[k] for k in z.files if k != "U_star"}
    np.savez(f.with_suffix(""), **arrays)
    assert not has_labels(f)
    code, out = _stop(mod, capsys, _cfg(world, tmp_path), data_dir=str(other), dry_run=True)
    assert code == 3 and "carry no labels" in out and f.name in out


def test_a_holdout_file_that_is_not_the_manifests_is_refused_before_training(world, tmp_path,
                                                                           capsys):
    mod = world["mod"]
    hd = tmp_path / "h3d"
    shutil.copytree(world["holdout_dir"], hd)
    lab = sorted((hd / "labels").iterdir())[1]
    with open(lab, "ab") as fh:
        fh.write(b"\0")
    code, out = _stop(mod, capsys, _cfg(world, tmp_path, holdout={
        "spec": str(world["spec"]), "set": "h3d", "dir": str(hd)}), dry_run=True)
    assert code == 3 and "holdout: 1 files refused" in out and lab.name in out
    lab.unlink()
    code, out = _stop(mod, capsys, _cfg(world, tmp_path, holdout={
        "spec": str(world["spec"]), "set": "h3d", "dir": str(hd)}), dry_run=True)
    assert code == 3 and "missing" in out


def test_one_run_at_a_time(world, tmp_path, capsys):
    import fcntl

    mod = world["mod"]
    p = _cfg(world, tmp_path)
    (tmp_path / "out").mkdir()
    with open(tmp_path / "out" / ".lock", "a+") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        code, out = _stop(mod, capsys, p)
    assert code == 3 and "another run of this script holds" in out
    assert sorted(x.name for x in (tmp_path / "out").iterdir()) == [".lock"]
    mod.run(p)                                     # the lock is free once its holder is gone
    mod.run(p)                                     # and the run releases its own


def test_valid_files_of_another_configuration_or_commit_are_moved_aside(world, full, tmp_path):
    """A valid epoch checkpoint and reused.json of another configuration, and
    a valid seed result of another commit (the identity checks themselves,
    not the readers' fallbacks)."""
    from fejepa.train import supervised

    mod = world["mod"]
    other = _cfg(world, tmp_path, name="other", content_tol=2e-6)   # another config hash
    real = supervised.train_supervised

    def interrupted(model, archs, val, cfg, **kw):
        cfg.stop_after_epoch = 1
        real(model, archs, val, cfg, **kw)
        raise KeyboardInterrupt

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(supervised, "train_supervised", interrupted)
        with pytest.raises(KeyboardInterrupt):
            mod.run(other)
    out = tmp_path / "out"
    ck = out / f"labels_knorm_b{BUDGET}_s0.ckpt"
    assert ck.is_file() and (out / "reused.json").is_file()
    # a valid seed-1 result of this configuration but another commit, its state on disk
    res1 = json.loads((full["tmp"] / "out" / "seed_1.json").read_text())
    st = out / f"labels_knorm_b{BUDGET}_s1.pt"
    shutil.copyfile(res1["state"]["path"], st)
    from fejepa.report import config_sha256

    p = _cfg(world, tmp_path)                       # the run's own configuration
    res1.update(config_sha256=config_sha256(json.loads(p.read_text())),
                git="test-describe", commit="f" * 40,
                state={"path": str(st), "sha256": _sha(st)})
    (out / "seed_1.json").write_text(json.dumps(res1))
    rep = mod.run(p)
    names = sorted(x.name for x in out.iterdir())
    for stem in (ck.name, "seed_1.json", "reused.json"):
        assert any(n.startswith(stem + ".unusable.") for n in names), (stem, names)
    assert rep["per_seed"]["s0"]["train"]["resumed_from_epoch"] is None
    assert not rep["per_seed"]["s1"].get("from_disk")
    assert rep["reused_evaluations_from_disk"] is False
    for s in SEEDS:
        assert _sha(out / f"labels_knorm_b{BUDGET}_s{s}.pt") == \
            _sha(full["tmp"] / "out" / f"labels_knorm_b{BUDGET}_s{s}.pt")


def test_the_records_of_code_machine_and_torch(world, full):
    mod = world["mod"]
    rep = full["report"]
    head = mod.git_commit()
    assert rep["provenance"]["commit"] == head and len(head) == 40
    for s in SEEDS:
        ps = rep["per_seed"][f"s{s}"]
        assert ps["commit"] == head and ps["torch"]["version"] == str(torch.__version__)
        m = ps["machine"]
        assert set(m["start"]) == {"host", "cpu", "gpu_driver", "gpu_uuid"}
        assert m["resumed_on"] == [] and m["start"]["host"] == m["end"]["host"]
    side = mod.machine(tries=1)
    assert side["host"] and set(side) == {"host", "cpu", "gpu_driver", "gpu_uuid"}


def test_the_dry_run_probes_the_checkpoint_writer(world, tmp_path, capsys, monkeypatch):
    """The dry run writes a probe through atomic_torch_save (flushed to the
    disk) and removes it, leaving nothing; a disk on which that fails stops
    the dry run (exit status 3), not the first epoch checkpoint."""
    from fejepa.train import checkpoint as ckmod

    mod = world["mod"]
    p = _cfg(world, tmp_path)
    plan = mod.run(p, dry_run=True)
    assert plan["dry_run"] is True and not (tmp_path / "out").exists()
    (tmp_path / "out").mkdir()
    mod.run(p, dry_run=True)
    assert list((tmp_path / "out").iterdir()) == []

    def no_fsync(path, directory=False):
        if not directory:
            raise OSError(22, "Invalid argument")

    monkeypatch.setattr(ckmod, "_fsync_path", no_fsync)
    code, out = _stop(mod, capsys, p, dry_run=True)
    assert code == 3 and "cannot be written and flushed to the disk" in out
    assert list((tmp_path / "out").iterdir()) == []
