"""Tests of gate G-C2.2's own code (c22/): the configuration against G-C2.1's, the second held-out sample, the
stability recipe, the amplitude-condensed reading, training with resume, and the evaluation in both readings.
The reference code and the parts shared with G-C2.1 are tested in test_c2.py."""
import copy
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

from c2 import config as base
from c2 import data as c2data
from c2.config import TESTED
from c2.instance import ExportedProblem
from c22 import data
from c22.config import (config, sha256, BASE_SHA256, FRESH_EVAL_SEED, FORMER_EVAL_SEED, FAMILY_SEEDS_SEEN,
                        TRAINING_SEEDS, TRAINING_SEEDS_SEEN)

REPO = os.environ.get("FEJEPA_REPO")
JOINT = Path(__file__).resolve().parents[1]
TEST_SEEDS = (7, 8, 101)   # family seeds seen before G-C2.1's stamp: the tests never draw a member of this gate
COARSE = {"h": 10.0, "n_tf": 1, "hx_max": 40.0}


def torch_or_skip():
    return pytest.importorskip("torch")


def small_cfg(n_train=2, n_eval=2, n_former=1, epochs=2):
    cfg = copy.deepcopy(config())
    d = cfg["data"]
    d["n_train"], d["n_eval"], d["n_former"] = n_train, n_eval, n_former
    d["train_seed"], d["eval_seed"], d["former_eval_seed"] = TEST_SEEDS
    d["seeds_seen_before_stamp"] = [s for s in d["seeds_seen_before_stamp"] if s not in TEST_SEEDS]
    d["mesh"] = dict(COARSE)
    d["eval_levels_mm"] = [0.25, 1.5]
    d["tested"] = {"BJ_T1_preloaded": dict(TESTED["BJ_T1_preloaded"])}
    cfg["model"].update(dim=16, depth=1, heads=2)
    cfg["training"]["fields_per_step"] = 2
    cfg["training"]["bubble_newton_steps"] = 4
    cfg["arms"]["label_free"]["epochs"] = epochs
    return cfg


# ---- the configuration ----------------------------------------------------------------------------------------------
def _flat(obj, pre=""):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            out.update(_flat(v, f"{pre}{k}."))
        return out
    return {pre[:-1]: obj}


def test_configuration_is_the_stamped_one_of_c21_with_the_listed_changes():
    b, c = base.config(), config()
    assert sha256(b) == BASE_SHA256 and sha256(c) != BASE_SHA256 and sha256(c) == sha256(config())
    fb, fc = _flat(b), _flat(c)
    changed = {k for k in fb if k in fc and fb[k] != fc[k]}
    removed = {k for k in fb if k not in fc}
    added = {k for k in fc if k not in fb}
    assert changed == {"gate", "data.eval_seed", "data.seeds_seen_before_stamp", "data.n_train_labelled",
                       "arms.label_free.seeds", "evaluation.sets", "criteria.C1", "criteria.C2",
                       "criteria.non_finite_seed", "criteria.incomplete", "criteria.reported_not_judged"}
    assert removed == {k for k in fb if k.startswith("arms.supervised_64.")}
    top = {k.split(".")[0] + "." + k.split(".")[1] if "." in k else k for k in added}
    assert top == {"base.gate", "base.config_sha256", "base.unchanged", "data.former_eval_seed", "data.n_former",
                   "data.training_members", "training.beta2", "training.encoder_gradient_cap",
                   "training.checkpoint_every_epochs", "training_seeds_seen_before_stamp", "evaluation.judged_set",
                   "evaluation.readings", "criteria.amplitudes"}
    assert c["training"]["beta2"] == 0.99
    assert {k: c["training"]["encoder_gradient_cap"][k] for k in ("factor", "window_steps")} == \
        {"factor": 5.0, "window_steps": 256}
    assert c["evaluation"]["readings"]["judged"] == "condensed" and c["evaluation"]["judged_set"] == "eval"
    assert c["data"]["train_seed"] == b["data"]["train_seed"] and c["data"]["eval_levels_mm"] == b["data"]["eval_levels_mm"]


def test_seeds_are_fresh():
    c = config()
    assert c["data"]["eval_seed"] == FRESH_EVAL_SEED and FRESH_EVAL_SEED not in FAMILY_SEEDS_SEEN
    assert c["data"]["former_eval_seed"] == FORMER_EVAL_SEED == base.config()["data"]["eval_seed"]
    assert set(base.SEEDS_SEEN) | {c["data"]["train_seed"], FORMER_EVAL_SEED} == set(FAMILY_SEEDS_SEEN)
    assert c["arms"]["label_free"]["seeds"] == TRAINING_SEEDS and not set(TRAINING_SEEDS) & set(TRAINING_SEEDS_SEEN)
    assert set(base.config()["arms"]["label_free"]["seeds"]) <= set(TRAINING_SEEDS_SEEN)


def test_members_keep_the_training_set_and_add_the_former_sample():
    cfg = small_cfg(n_train=3, n_eval=2, n_former=2)
    m = data.members(cfg)
    assert [i for i, _, _ in m] == ["train_0000", "train_0001", "train_0002", "eval_0000", "eval_0001",
                                    "former_0000", "former_0001", "tested_BJ_T1_preloaded"]
    assert [s for _, s, _ in m] == ["train"] * 3 + ["eval"] * 2 + ["former"] * 2 + ["tested"]
    old = copy.deepcopy(base.config())                       # G-C2.1's code with the same seeds draws the same members
    old["data"].update(n_train=3, n_eval=2, train_seed=TEST_SEEDS[0], eval_seed=TEST_SEEDS[2], tested={},
                       seeds_seen_before_stamp=[])
    mo = {i: q for i, _, q in c2data.members(old)}
    mn = {i: q for i, _, q in m}
    assert all(mn[f"train_{k:04d}"] == mo[f"train_{k:04d}"] for k in range(3))
    assert all(mn[f"former_{k:04d}"] == mo[f"eval_{k:04d}"] for k in range(2))
    for bad in ({"eval_seed": TEST_SEEDS[0]}, {"eval_seed": TEST_SEEDS[2]},
                {"seeds_seen_before_stamp": [TEST_SEEDS[1]]}):
        c = small_cfg(); c["data"].update(bad)
        with pytest.raises(RuntimeError):
            data.members(c)


def test_code_list_holds_the_package_and_c21s_stamped_files():
    sys.path.insert(0, str(JOINT / "c22"))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("c22_main_for_test", JOINT / "c22" / "__main__.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(JOINT / "c22"))
    assert {f for f in mod.CODE if f.startswith("c22/")} == {f"c22/{p.name}" for p in (JOINT / "c22").glob("*.py")}
    stamped = dict(line.split()[::-1] for line in (JOINT / "docs" / "G-C2.1_code.sha256").read_text().splitlines()
                   if line.strip() and not line.split()[1].startswith(".."))
    now = mod.code_hashes()
    assert set(stamped) == {f for f in mod.CODE if not f.startswith("c22/")}
    assert all(now[f] == h for f, h in stamped.items()), "a file stamped for G-C2.1 has changed"
    with pytest.raises(SystemExit):
        mod.main(["evaluate", "--data", "x", "--runs", "y", "--config-sha", "0" * 64])


# ---- the stability recipe -------------------------------------------------------------------------------------------
def test_cap_scales_the_encoder_gradient_to_five_medians():
    torch = torch_or_skip()
    import collections
    from c22.train import cap_encoder_gradient
    cap = {"factor": 5.0, "window_steps": 4, "burst_factor": 10.0}
    net = torch.nn.Linear(3, 2)

    def set_grad(norm):
        g = torch.ones(8)
        g = g / g.norm() * norm
        net.weight.grad = g[:6].reshape(2, 3).clone(); net.bias.grad = g[6:].clone()

    def norm():
        return float(torch.cat([net.weight.grad.reshape(-1), net.bias.grad.reshape(-1)]).norm())

    window = collections.deque(maxlen=4)
    for k, n in enumerate([1.0, 2.0, 3.0]):                 # the window is not full: nothing is scaled
        set_grad(100.0 * n)
        g, ratio, scale = cap_encoder_gradient(net, window, cap)
        assert ratio is None and scale is None and g == pytest.approx(100.0 * n, rel=1e-6) and len(window) == k + 1
    set_grad(4.0); cap_encoder_gradient(net, window, cap)   # window: 100, 200, 300, 4 -> median 150
    set_grad(700.0)
    g, ratio, scale = cap_encoder_gradient(net, window, cap)
    assert scale is None and ratio == pytest.approx(700.0 / 150.0, rel=1e-6) and norm() == pytest.approx(700.0, rel=1e-6)
    assert list(window) == pytest.approx([200.0, 300.0, 4.0, 700.0], rel=1e-6)      # median 250
    set_grad(5000.0)
    g, ratio, scale = cap_encoder_gradient(net, window, cap)
    assert ratio == pytest.approx(20.0, rel=1e-6) and scale == pytest.approx(0.25, rel=1e-6)
    assert norm() == pytest.approx(5.0 * 250.0, rel=1e-5)
    assert window[-1] == pytest.approx(5000.0, rel=1e-6)    # the window keeps the norm before scaling
    window = collections.deque(maxlen=4)                    # the cap first acts at step window_steps + 1
    for k in range(5):
        set_grad(1.0 if k < 3 else 1000.0)                  # steps 4 and 5 burst; only step 5 has a full window
        g, ratio, scale = cap_encoder_gradient(net, window, cap)
        assert (ratio is None and scale is None and norm() == pytest.approx(g, rel=1e-6)) if k < 4 \
            else (ratio == pytest.approx(1000.0, rel=1e-6) and norm() == pytest.approx(5.0, rel=1e-5))
    window = collections.deque([0.0] * 4, maxlen=4)         # a zero median
    set_grad(0.0)
    assert cap_encoder_gradient(net, window, cap) == (0.0, 0.0, None)
    set_grad(3.0)
    g, ratio, scale = cap_encoder_gradient(net, window, cap)
    assert g == pytest.approx(3.0, rel=1e-6) and ratio == float("inf") and scale == 0.0 and norm() == 0.0


# ---- data, labels, the condensed reading ----------------------------------------------------------------------------
@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    """A small configuration's data: 2 training members (not labelled), 2 fresh held-out members, 1 former held-out
    member and 1 tested member, exported and labelled."""
    cfg = small_cfg()
    d = tmp_path_factory.mktemp("c22data")
    data.generate(cfg, d)
    data.label(cfg, d, data.labelled_ids(cfg, d), workers=1)
    return cfg, d


def _ids(d, splits=("eval", "former", "tested")):
    return [r["id"] for r in data.manifest(d)["instances"] if r["split"] in splits]


def test_generate_label_and_check(dataset):
    cfg, d = dataset
    man = data.manifest(d)
    assert man["config_sha256"] == sha256(cfg)
    assert [r["split"] for r in man["instances"]] == ["train"] * 2 + ["eval"] * 2 + ["former"] + ["tested"]
    assert data.labelled_ids(cfg, d) == _ids(d) and not any(i.startswith("train") for i in _ids(d))
    r = data.check_labels(cfg, d)
    assert r["ok"] and r["labels"] == r["needed"] == 4 and not r["missing"] and not r["extra"], r
    lab = data.load_label(d, "former_0000")
    assert list(lab["D"]) == cfg["data"]["eval_levels_mm"] and (np.diff(lab["F"]) > 0).all()
    other = copy.deepcopy(cfg); other["training"]["beta2"] = 0.999
    with pytest.raises(RuntimeError):
        data.generate(other, d)                            # files of another configuration are refused


def test_the_clamped_unknowns_are_the_contact_unknowns(dataset):
    torch = torch_or_skip()
    from c2.model import maps
    cfg, d = dataset
    ex, _ = data.load_export(Path(d) / "inst" / "eval_0000.npz")
    mp, P = maps(ex, "cpu"), ExportedProblem(ex)
    nonneg = np.zeros(mp["n_z"], dtype=bool)
    nonneg[:mp["nonneg"].numel()] = mp["nonneg"].numpy()
    assert set(np.nonzero(nonneg)[0]) == set(int(i) for i in P.prob.cidx)


def test_condense_finds_the_minimum_along_the_ray(dataset):
    """A ray through the exact solution: the amplitude that reaches it is found; with the exact solution outside the
    bounds the result lies on the bound; the energy never rises above the raw field's."""
    torch = torch_or_skip()
    from c2.model import maps
    from c2.torch_energy import InstanceEnergy
    from c22.condense import condense
    cfg, d = dataset
    nb = 10
    ex, _ = data.load_export(Path(d) / "inst" / "eval_0000.npz")
    lab = data.load_label(d, "eval_0000")
    E = InstanceEnergy(ex, device="cpu", dtype=torch.float32)
    mp = maps(ex, "cpu")
    nonneg = torch.cat([mp["nonneg"], torch.zeros(mp["n_z"] - mp["nonneg"].numel(), dtype=torch.bool)])
    zr = torch.as_tensor(lab["z"], dtype=torch.float32)
    D = torch.as_tensor(lab["D"], dtype=torch.float32)
    z0 = (0.4 * zr[:1]).expand(2, -1)                      # stands for the field at the smallest level
    for a_true in (1.3, 0.8):
        z = z0 + (zr - z0) / a_true                        # the exact solution lies at a = a_true on the ray
        a, st = condense(E, z0, z, D, nonneg, nb, 0.5, 3.0, 12, 1e-4)
        zc = torch.where(nonneg, (z0 + a[:, None] * (z - z0)).clamp_min(0.0), z0 + a[:, None] * (z - z0))
        Pc, Pz, Px = E.energy(zc, D, iters=nb), E.energy(z, D, iters=nb), E.energy(zr, D, iters=nb)
        assert torch.allclose(a, torch.full((2,), a_true), atol=2e-2), (a_true, a)
        assert (Pc <= Pz * (1 + 1e-6)).all() and (Pc <= Px * (1 + 2e-3)).all()
        assert not st["at_bound"].any() and st["evals"] <= 12
    z = z0 + (zr - z0) / 1.3
    a, st = condense(E, z0, z, D, nonneg, nb, 0.5, 1.2, 12, 1e-4)
    assert torch.allclose(a, torch.full((2,), 1.2)) and st["at_bound"].all()


# ---- training -------------------------------------------------------------------------------------------------------
def _train_cfg(cfg):
    """The small configuration with a window of three steps and a cap at half the median, so that the cap acts on
    almost every step of a tiny run."""
    c = copy.deepcopy(cfg)
    c["training"]["encoder_gradient_cap"].update(window_steps=3, factor=0.5, burst_factor=0.7)
    c["arms"]["label_free"]["epochs"] = 4
    return c


@pytest.fixture(scope="module")
def train_data(dataset, tmp_path_factory):
    cfg, d = dataset
    c = _train_cfg(cfg)
    dd = tmp_path_factory.mktemp("c22train")
    data.generate(c, dd)
    data.label(c, dd, data.labelled_ids(c, dd), workers=1)
    return c, dd


@pytest.mark.skipif(not REPO, reason="set FEJEPA_REPO to the repository checkout")
def test_train_resume_and_predict(train_data, tmp_path, monkeypatch):
    """A tiny model trains with the recipe; an interrupted run resumes to the same end state, cap events and
    predictions as an uninterrupted one; the predictions hold both readings; a finished run returns at once."""
    torch = torch_or_skip()
    sys.path.insert(0, str(Path(REPO) / "src"))
    import c22.train as ct
    cfg, d = train_data
    a_full, a_int = tmp_path / "full", tmp_path / "interrupted"
    made, real_adamw = [], torch.optim.AdamW
    built, calls, moves, real_build = [], [], [], ct.build
    real_cap, real_clip = ct.cap_encoder_gradient, torch.nn.utils.clip_grad_norm_
    real_replace, real_write = ct._replace, ct._write_json
    monkeypatch.setattr(ct, "_replace", lambda tmp, dst: moves.append(Path(dst).name) or real_replace(tmp, dst))
    monkeypatch.setattr(ct, "_write_json", lambda path, obj: moves.append(Path(path).name) or real_write(path, obj))
    monkeypatch.setattr(torch.optim, "AdamW", lambda *a, **k: made.append(k) or real_adamw(*a, **k))
    monkeypatch.setattr(ct, "build", lambda *a, **k: built.append(real_build(*a, **k)) or built[-1])
    monkeypatch.setattr(ct, "cap_encoder_gradient", lambda enc, w, c: calls.append(("cap", enc)) or real_cap(enc, w, c))
    monkeypatch.setattr(torch.nn.utils, "clip_grad_norm_",
                        lambda params, m: calls.append(("clip", m)) or real_clip(params, m))
    h1 = ct.train(cfg, 5, d, a_full, device="cpu")
    monkeypatch.undo()
    assert made[0]["betas"] == (0.9, 0.99) and h1["betas"] == [0.9, 0.99]
    assert h1["status"] == "finished" and h1["steps"] == 8 and np.isfinite(h1["loss"]).all()
    assert h1["config_sha256"] == sha256(cfg) and h1["matmul_precision"] == "highest"
    # every file a run writes goes through the retried move: a checkpoint an epoch, the history, then the predictions
    assert moves == ["state.pt"] * 4 + ["history.json", "preds.npz", "preds_condensed.npz", "preds_base.npz", "condense.json"]
    assert [c[0] for c in calls] == ["cap", "clip"] * 8     # the cap comes before the global clipping, at every step
    assert all(c[1] is built[0][0] for c in calls[0::2]) and all(c[1] == cfg["training"]["clip"] for c in calls[1::2])
    assert [s for s, _ in h1["cap_events"]] and min(s for s, _ in h1["cap_events"]) >= 4      # the window is 3 steps
    assert all(r > 0.5 for _, r in h1["cap_events"])
    assert h1["bursts"] and all(r > 0.7 for _, r in h1["bursts"])
    assert set(map(tuple, h1["bursts"])) <= set(map(tuple, h1["cap_events"]))
    assert len(h1["bursts"]) < len(h1["cap_events"])        # some capped steps lie below the burst threshold
    ct.train(cfg, 5, d, a_int, device="cpu", stop_after_epoch=2)
    assert not (a_int / "label_free_s5" / "preds.npz").exists()
    where, real = [], torch.load
    monkeypatch.setattr(torch, "load", lambda *a, **k: where.append(k.get("map_location")) or real(*a, **k))
    h2 = ct.train(cfg, 5, d, a_int, device="cpu")
    monkeypatch.undo()
    assert where == ["cpu"] and h2["resumed_from_epoch"] == 2 and h2["resumes"] == [2] and h2["status"] == "finished"
    assert h2["cap_events"] == h1["cap_events"] and h2["bursts"] == h1["bursts"] and h2["loss"] == h1["loss"]
    monkeypatch.setattr(ct, "_prepare", lambda *a, **k: pytest.fail("a finished run loaded its members"))
    assert ct.train(cfg, 5, d, a_full, device="cpu")["status"] == "finished"
    monkeypatch.undo()
    s1 = torch.load(a_full / "label_free_s5" / "state.pt", weights_only=False)
    s2 = torch.load(a_int / "label_free_s5" / "state.pt", weights_only=False)
    assert s1["window"] == s2["window"] and len(s1["window"]) == 3
    for part in ("enc", "dec", "head"):
        for k in s1[part]:
            assert torch.equal(s1[part][k], s2[part][k]), (part, k)
    ids, L = set(_ids(d)), len(cfg["data"]["eval_levels_mm"])
    assert ct.PREDICTION_FILES == ("preds.npz", "preds_condensed.npz", "preds_base.npz", "condense.json")
    for name in ("preds.npz", "preds_condensed.npz", "preds_base.npz"):
        with np.load(a_full / "label_free_s5" / name) as z1, np.load(a_int / "label_free_s5" / name) as z2:
            assert set(z1.files) == set(z2.files) == ids
            for k in z1.files:
                assert z1[k].dtype == np.float32 and np.array_equal(z1[k], z2[k])
                assert z1[k].ndim == 1 if name == "preds_base.npz" else z1[k].shape[0] == L
    info = json.loads((a_full / "label_free_s5" / "condense.json").read_text())
    assert set(info["members"]) == ids and info["levels_mm"] == cfg["data"]["eval_levels_mm"]
    assert info["reading"] == cfg["evaluation"]["readings"]["condensed"]
    run = a_full / "label_free_s5"
    with np.load(run / "preds_condensed.npz") as zc, np.load(run / "preds.npz") as zr, np.load(run / "preds_base.npz") as zb:
        for iid in ids:
            m = info["members"][iid]
            assert len(m["a"]) == L and all(0.5 <= a <= 3.0 for a in m["a"]) and m["evaluations"] <= 12
            assert all(pc <= pr * (1 + 1e-6) for pc, pr in zip(m["Pi_condensed"], m["Pi_raw"]))
            ex, _ = data.load_export(Path(d) / "inst" / f"{iid}.npz")
            P = ExportedProblem(ex)
            assert (zc[iid][:, P.prob.cidx] >= 0).all() and (zc[iid][:, P.prob.fixed] == 0).all()
            # the stored condensed field is the stored base and raw fields, the stored amplitude and the clamp of the
            # reference problem's contact unknowns: the judged field can be computed again from the files
            ray = zb[iid][None, :] + np.asarray(m["a"], dtype=np.float32)[:, None] * (zr[iid] - zb[iid][None, :])
            keep = ray.copy()
            keep[:, P.prob.cidx] = np.maximum(keep[:, P.prob.cidx], 0.0)
            assert np.allclose(zc[iid], keep, rtol=1e-6, atol=1e-9), iid
    for folder, lines in ((a_full, ["start", "ended: finished", "start", "returned: finished"]),
                          (a_int, ["start", "start", "resumed from epoch 2", "ended: finished"])):
        text = (folder / "label_free_s5" / "attempts.log").read_bytes().decode("ascii")       # ASCII on every system
        assert [l.split(" ", 1)[1] for l in text.splitlines()] == lines
        assert all(l[10] == "T" and l[19] in "+-" for l in text.splitlines())                # a time with its offset
    other = copy.deepcopy(cfg); other["training"]["beta2"] = 0.999
    with pytest.raises(RuntimeError, match="generated under another configuration"):       # the data's configuration
        ct.train(other, 5, d, tmp_path / "fresh", device="cpu")
    do = tmp_path / "other_data"
    data.generate(other, do)
    with pytest.raises(RuntimeError, match="holds a run of another configuration"):        # a finished run's history
        ct.train(other, 5, do, a_full, device="cpu")
    (tmp_path / "only_state" / "label_free_s5").mkdir(parents=True)
    shutil.copy(a_int / "label_free_s5" / "state.pt", tmp_path / "only_state" / "label_free_s5" / "state.pt")
    with pytest.raises(RuntimeError, match="belongs to another configuration"):            # a checkpoint alone
        ct.train(other, 5, do, tmp_path / "only_state", device="cpu")
    bad = copy.deepcopy(cfg); bad["arms"]["label_free"]["seeds"] = [0]
    with pytest.raises(RuntimeError, match="before the stamp"):
        ct.train(bad, 0, d, tmp_path / "seen", device="cpu")
    with pytest.raises(RuntimeError, match="not in the configuration"):
        ct.train(cfg, 9, d, tmp_path / "other", device="cpu")


def test_predict_clamps_the_contact_unknowns_and_no_others(dataset, tmp_path, monkeypatch):
    """predict() on fields built so that the ray leaves the admissible set: with z_0 = 0.3 and z = 0.1 on every
    unknown and an amplitude of 2 the ray gives -0.1; the contact unknowns are set to zero and the others are kept."""
    torch = torch_or_skip()
    import c22.condense as cc
    import c22.train as ct
    cfg, d = dataset

    class Net:
        def eval(self):
            pass

        def train(self):
            pass

    def fields(enc, dec, head, base, mp, lv, T, lift=False):
        z = torch.full((lv.numel(), mp["n_z"]), 0.1)
        z[0] = 0.3                                          # the base level comes first
        return z

    def amplitude_two(energy, z0, z, D, nonneg, nb, a_min, a_max, evals, rtol):
        B = z.shape[0]
        return torch.full((B,), 2.0), {"rel_slope": torch.zeros(B), "evals": 1,
                                       "at_bound": torch.zeros(B, dtype=torch.bool),
                                       "converged": torch.ones(B, dtype=torch.bool)}

    monkeypatch.setattr(ct, "field", fields)
    monkeypatch.setattr(cc, "condense", amplitude_two)
    run = tmp_path / "run"
    run.mkdir()
    assert ct.predict(cfg, (Net(), Net(), Net()), d, run, torch.device("cpu"))
    L = len(cfg["data"]["eval_levels_mm"])
    with np.load(run / "preds_condensed.npz") as zc, np.load(run / "preds.npz") as zr, np.load(run / "preds_base.npz") as zb:
        assert set(zc.files) == set(_ids(d))
        for iid in zc.files:
            ex, _ = data.load_export(Path(d) / "inst" / f"{iid}.npz")
            contact = np.zeros(zc[iid].shape[1], dtype=bool)
            contact[np.asarray(ExportedProblem(ex).prob.cidx, dtype=int)] = True
            assert contact.any() and not contact.all() and zc[iid].shape[0] == L
            assert (zc[iid][:, contact] == 0.0).all() and np.allclose(zc[iid][:, ~contact], -0.1, atol=1e-6)
            assert np.allclose(zr[iid], 0.1) and np.allclose(zb[iid], 0.3)
    assert json.loads((run / "condense.json").read_text())["members"][_ids(d)[0]]["a"] == [2.0] * L


@pytest.mark.skipif(not REPO, reason="set FEJEPA_REPO to the repository checkout")
def test_a_non_finite_loss_is_final_and_a_checkpoint_survives_a_busy_file(train_data, tmp_path, monkeypatch):
    torch = torch_or_skip()
    sys.path.insert(0, str(Path(REPO) / "src"))
    import c22.train as ct
    from c22.evaluate import run_status
    cfg, d = train_data
    n, real = [0], ct.step_loss

    def third_is_nan(*a, **k):
        n[0] += 1
        loss, aux = real(*a, **k)
        return (loss * float("nan") if n[0] == 3 else loss), aux

    monkeypatch.setattr(ct, "step_loss", third_is_nan)
    h = ct.train(cfg, 6, d, tmp_path, device="cpu")
    monkeypatch.undo()
    run = tmp_path / "label_free_s6"
    assert h["status"] == "non-finite loss at step 3" and h["steps"] == 2 and len(h["loss"]) == 1
    assert json.loads((run / "history.json").read_text())["status"] == h["status"]
    assert not any((run / f).exists() for f in ct.PREDICTION_FILES) and run_status(run) == "non-finite"
    monkeypatch.setattr(ct, "_prepare", lambda *a, **k: pytest.fail("a stopped run loaded its members"))
    assert ct.train(cfg, 6, d, tmp_path, device="cpu")["status"] == h["status"]            # final: not trained again
    monkeypatch.undo()
    # a file that another program holds for a moment: the move is tried again; a lasting refusal is raised
    tries, real_replace = [], ct.os.replace

    def busy_twice(a, b):
        tries.append(1)
        if len(tries) < 3:
            raise PermissionError("held by another program")
        return real_replace(a, b)

    src, dst = tmp_path / "a.tmp", tmp_path / "a.bin"
    src.write_bytes(b"new"); dst.write_bytes(b"old")
    monkeypatch.setattr(ct.os, "replace", busy_twice)
    ct._replace(src, dst, tries=5, wait=0.0)
    assert dst.read_bytes() == b"new" and not src.exists() and len(tries) == 3
    monkeypatch.setattr(ct.os, "replace", lambda a, b: (_ for _ in ()).throw(PermissionError("held")))
    src.write_bytes(b"newer")
    with pytest.raises(PermissionError):
        ct._replace(src, dst, tries=3, wait=0.0)


# ---- evaluation -----------------------------------------------------------------------------------------------------
def _write_preds(cfg, d, runs, change=None, skip=()):
    """Predictions equal to the labels in both readings (optionally changed: change[(seed, reading)] is applied to a
    member's fields, change[(seed, reading, split)] only to that split's members)."""
    split = {r["id"]: r["split"] for r in data.manifest(d)["instances"]}
    for s in cfg["arms"]["label_free"]["seeds"]:
        run = runs / f"label_free_s{s}"; run.mkdir(parents=True, exist_ok=True)
        if s in skip:
            continue
        for reading, name in (("raw", "preds.npz"), ("condensed", "preds_condensed.npz")):
            Z = {i: data.load_label(d, i)["z"].astype(np.float32) for i in _ids(d)}
            for i in Z:
                f = (change or {}).get((s, reading, split[i])) or (change or {}).get((s, reading))
                if f:
                    Z[i] = f(Z[i])
            np.savez_compressed(run / name, **Z)
        np.savez_compressed(run / "preds_base.npz", **{i: data.load_label(d, i)["z"][0].astype(np.float32) for i in _ids(d)})
        L = len(cfg["data"]["eval_levels_mm"])
        info = {i: {"a": [1.0] * L, "rel_slope": [0.0] * L, "at_bound": [False] * L, "converged": [True] * L,
                    "evaluations": 1, "Pi_raw": [1.0] * L, "Pi_condensed": [1.0] * L} for i in _ids(d)}
        (run / "condense.json").write_text(json.dumps({"levels_mm": cfg["data"]["eval_levels_mm"], "members": info,
                                                       "reading": cfg["evaluation"]["readings"]["condensed"]}))
        (run / "history.json").write_text(json.dumps({"config_sha256": sha256(cfg), "status": "finished"}))


def _stopped(cfg, run, status):
    run.mkdir(parents=True, exist_ok=True)
    (run / "history.json").write_text(json.dumps({"config_sha256": sha256(cfg), "status": status}))


def _stiffer(z):
    return (0.8 * z).astype(np.float32)                    # a smaller end displacement: a point above the curve


def test_evaluation_of_exact_predictions_in_both_readings(dataset, tmp_path):
    cfg, d = dataset
    from c22.evaluate import evaluate
    _write_preds(cfg, d, tmp_path)
    v = evaluate(cfg, d, tmp_path)
    assert v["verdict"] == "PASS" and v["C1_value"] < 1e-6 and v["C2_value"] < 1e-6, v.get("per_seed")
    assert v["judged"] == {"reading": "condensed", "set": "eval"} and v["config_sha256"] == sha256(cfg)
    assert v["reported_readings"]["raw"]["C1_value"] < 1e-6 and v["reported_readings"]["raw"]["C2"]
    for reading in ("condensed", "raw"):
        e = v["readings"][reading]["5"]
        assert set(e["eval_rows"]) == set(_ids(d, ("eval",))) and set(e["former_rows"]) == set(_ids(d, ("former",)))
        assert set(e["tested_rows"]) == set(_ids(d, ("tested",))) and not e["errors"]
        for s in ("eval", "former", "tested"):
            assert e[s]["gap"]["max"] < 1e-6 and e[s]["abs_curve_err"]["n"] == 2 * len(e[f"{s}_rows"])
            assert e[s]["within_bound_fraction"] == 1.0 and e[s]["curve_infinite"] == 0
    one = {"min": 1.0, "max": 1.0, "median": 1.0, "at_bound": 0, "not_converged": 0}
    assert v["amplitudes"]["5"] == {"eval": {"n": 4, **one}, "former": {"n": 2, **one}, "tested": {"n": 2, **one}}
    assert json.loads((tmp_path / "verdict.json").read_text())["verdict"] == "PASS"


def test_the_condensed_reading_of_the_fresh_members_decides(dataset, tmp_path):
    cfg, d = dataset
    from c22.evaluate import evaluate
    seeds = cfg["arms"]["label_free"]["seeds"]
    a, b, c = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    _write_preds(cfg, d, a, change={(s, "raw"): _stiffer for s in seeds})              # only the raw reading is off
    v = evaluate(cfg, d, a)
    assert v["verdict"] == "PASS" and not v["reported_readings"]["raw"]["C1"] and not v["reported_readings"]["raw"]["C2"]
    _write_preds(cfg, d, b, change={(s, "condensed"): _stiffer for s in seeds[:2]})    # two seeds' judged reading
    v = evaluate(cfg, d, b)
    assert v["verdict"] == "FAIL" and not v["C1"] and v["reported_readings"]["raw"]["C1"]
    assert v["per_seed"]["abs_curve_err_median"][2] < 1e-6 < 0.05 < v["per_seed"]["abs_curve_err_median"][0]
    _write_preds(cfg, d, c, change={(s, r, sp): _stiffer for s in seeds for r in ("raw", "condensed")
                                    for sp in ("former", "tested")})                   # only the reported sets
    v = evaluate(cfg, d, c)
    assert v["verdict"] == "PASS" and v["readings"]["condensed"]["5"]["former"]["abs_curve_err"]["median"] > 0.05


def test_missing_and_non_finite_seeds(dataset, tmp_path):
    cfg, d = dataset
    from c22.evaluate import evaluate
    seeds = cfg["arms"]["label_free"]["seeds"]
    a, b, c = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    _write_preds(cfg, d, a, skip=(seeds[0],))
    v = evaluate(cfg, d, a)
    assert v["verdict"] == "INCOMPLETE" and v["missing"] == [f"label_free_s{seeds[0]}"] and "C1_value" not in v
    assert v["readings"] == {"withheld": "the verdict is INCOMPLETE"} and "amplitudes" not in v
    _write_preds(cfg, d, b, skip=(seeds[0],))
    _stopped(cfg, b / f"label_free_s{seeds[0]}", "non-finite loss at step 3")
    v = evaluate(cfg, d, b)                                # one stopped seed: the median over seeds is still finite
    assert v["verdict"] == "PASS" and v["non_finite"] == [f"label_free_s{seeds[0]}"]
    assert v["per_seed"]["abs_curve_err_median"][0] == float("inf") and v["C1_value"] < 1e-6
    _write_preds(cfg, d, c, skip=tuple(seeds[:2]))
    for s in seeds[:2]:
        _stopped(cfg, c / f"label_free_s{s}", "non-finite predictions")
    v = evaluate(cfg, d, c)
    assert v["verdict"] == "FAIL" and v["C1_value"] == float("inf") and v["C2_value"] == float("inf")
    one = tmp_path / "one"                                 # a run with only a part of its prediction files is missing
    _write_preds(cfg, d, one)
    (one / f"label_free_s{seeds[1]}" / "preds_base.npz").unlink()
    assert evaluate(cfg, d, one)["verdict"] == "INCOMPLETE"


def test_evaluation_refuses_runs_and_data_of_another_configuration(dataset, tmp_path, monkeypatch):
    cfg, d = dataset
    import c22.evaluate as ce
    seeds = cfg["arms"]["label_free"]["seeds"]
    a, b, c, e = tmp_path / "a", tmp_path / "b", tmp_path / "c", tmp_path / "e"
    _write_preds(cfg, d, a)                                # a finished run made under another configuration
    (a / f"label_free_s{seeds[1]}" / "history.json").write_text(json.dumps({"config_sha256": "0" * 64, "status": "finished"}))
    with pytest.raises(RuntimeError, match="another configuration"):
        ce.evaluate(cfg, d, a)
    _write_preds(cfg, d, b, skip=(seeds[0],))              # a stopped run made under another configuration
    (b / f"label_free_s{seeds[0]}" / "history.json").write_text(json.dumps({"config_sha256": "0" * 64,
                                                                             "status": "non-finite loss at step 3"}))
    with pytest.raises(RuntimeError, match="another configuration"):
        ce.evaluate(cfg, d, b)
    _write_preds(cfg, d, c)                                # predictions of another reading
    p = c / f"label_free_s{seeds[2]}" / "condense.json"
    info = json.loads(p.read_text()); info["reading"] = dict(info["reading"], a_max=2.0)
    p.write_text(json.dumps(info))
    with pytest.raises(RuntimeError, match="another reading"):
        ce.evaluate(cfg, d, c)
    f = tmp_path / "f"                                     # prediction files and no history
    _write_preds(cfg, d, f)
    (f / f"label_free_s{seeds[0]}" / "history.json").unlink()
    with pytest.raises(RuntimeError, match="no history.json"):
        ce.evaluate(cfg, d, f)
    _write_preds(cfg, d, e)                                # data with a held-out member too few
    man = data.manifest(d)
    short = dict(man, instances=[r for r in man["instances"] if r["id"] != "eval_0001"])
    monkeypatch.setattr(ce, "manifest", lambda _: short)
    with pytest.raises(RuntimeError, match="members in the evaluated sets"):
        ce.evaluate(cfg, d, e)


def test_spawned_workers_give_the_same_labels_and_verdict(dataset, tmp_path, monkeypatch):
    """Where the operating system has no fork the workers are spawned: the labels and the verdict are the same."""
    import multiprocessing as mp
    cfg, d = dataset
    from c22.evaluate import evaluate
    kinds, real_context = [], mp.get_context
    monkeypatch.setattr(mp, "get_all_start_methods", lambda: ["spawn"])
    monkeypatch.setattr(mp, "get_context", lambda kind=None: kinds.append(kind) or real_context(kind))
    for k in data.THREAD_VARIABLES:
        monkeypatch.setenv(k, "0")                          # recorded, so that the test leaves the variable as it was
        monkeypatch.delenv(k)
    dd = tmp_path / "data"
    data.generate(cfg, dd)
    data.label(cfg, dd, data.labelled_ids(cfg, dd), workers=2)
    assert kinds == ["spawn"] and all(os.environ.get(k) == "1" for k in data.THREAD_VARIABLES)
    monkeypatch.setenv(data.THREAD_VARIABLES[0], "3")       # a variable that is set is left as it is
    data.pool(1).close()
    assert os.environ[data.THREAD_VARIABLES[0]] == "3"
    assert data.check_labels(cfg, dd)["ok"]
    for i in _ids(d):
        l1, l2 = data.load_label(d, i), data.load_label(dd, i)
        assert all(np.array_equal(l1[k], l2[k]) for k in l1)
    r1, r2 = tmp_path / "r1", tmp_path / "r2"
    _write_preds(cfg, d, r1, change={(5, "condensed"): _stiffer})
    _write_preds(cfg, dd, r2, change={(5, "condensed"): _stiffer})
    v1, v2 = evaluate(cfg, d, r1, workers=1), evaluate(cfg, dd, r2, workers=2)
    assert v1 == v2 and v1["verdict"] == "PASS" and kinds == ["spawn"] * 3


def test_condense_keeps_the_bounds_and_the_budget():
    """On a quadratic energy with a known minimiser: found inside the bounds within the tolerance; on either bound
    when the minimiser lies outside, and flagged; never more evaluations than allowed, and flagged when they did not
    suffice. A field's result does not depend on the others in the batch."""
    torch = torch_or_skip()
    from c22.condense import condense

    class Quadratic:
        def __init__(self, target):
            self.t, self.calls = torch.as_tensor(target, dtype=torch.float32), 0

        def energy(self, z, D, iters=0):                   # z = a on every unknown; minimum at a = target
            self.calls += 1
            return 10.0 + D * ((z.mean(dim=1) - self.t) ** 2)

    n, targets = 6, [1.7, 0.2, 5.0, 1.0, 2.6]
    z0, z, D = torch.zeros(5, n), torch.ones(5, n), torch.full((5,), 4.0)
    none = torch.zeros(n, dtype=torch.bool)
    E = Quadratic(targets)
    a, st = condense(E, z0, z, D, none, 0, 0.5, 3.0, 12, 1e-4)
    assert E.calls == st["evals"] <= 12
    assert a.tolist() == pytest.approx([1.7, 0.5, 3.0, 1.0, 2.6], abs=2e-3)
    assert st["at_bound"].tolist() == [False, True, True, False, False] and st["converged"].all()
    for k, t in enumerate(targets):                        # each field alone gives the same amplitude
        a1, _ = condense(Quadratic([t]), z0[:1], z[:1], D[:1], none, 0, 0.5, 3.0, 12, 1e-4)
        assert float(a1) == pytest.approx(float(a[k]), abs=2e-3)
    E = Quadratic(targets)
    a, st = condense(E, z0, z, D, none, 0, 0.5, 3.0, 2, 1e-4)
    assert E.calls == st["evals"] == 2 and st["converged"].tolist() == [False, False, False, True, False]
    assert ((a >= 0.5) & (a <= 3.0)).all()
    best = 10.0 + 4.0 * (a - torch.as_tensor(targets)) ** 2
    assert (best <= 10.0 + 4.0 * (1.0 - torch.as_tensor(targets)) ** 2).all()     # never above the energy at a = 1


def test_the_entry_point_runs_as_a_process(tmp_path):
    """`python -I c22/__main__.py`, as the runbook starts it, from another folder: the configuration hash, the code
    hashes, and a configuration file with the same bytes on every system. It draws nothing."""
    import hashlib
    import subprocess
    r = subprocess.run([sys.executable, "-I", str(JOINT / "c22" / "__main__.py"), "write-config", "--out", "c.json"],
                       cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    lines = r.stdout.strip().splitlines()
    assert lines[0] == f"config sha256 {sha256(config())}"
    assert {l.split()[0]: l.split()[1] for l in lines[1:]} == {
        f: hashlib.sha256((JOINT / f).read_bytes()).hexdigest() for f in [l.split()[0] for l in lines[1:]]}
    assert "c22/smoke.py" in [l.split()[0] for l in lines[1:]]
    raw = (tmp_path / "c.json").read_bytes()
    assert b"\r" not in raw and json.loads(raw) == config()
    r = subprocess.run([sys.executable, "-I", str(JOINT / "c22" / "__main__.py"), "evaluate", "--data", "x", "--runs", "y",
                        "--config-sha", "0" * 64], cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode != 0 and "refusing to run" in r.stderr


@pytest.mark.skipif(not REPO, reason="set FEJEPA_REPO to the repository checkout")
def test_the_host_check_passes_on_a_cpu(tmp_path):
    """c22/smoke.py, the runbook's check of a host, on this machine's CPU with two workers. Its reduced
    configuration uses the family seeds 7, 8 and 101 and draws nothing of the gate."""
    torch_or_skip()
    import importlib.util
    spec = importlib.util.spec_from_file_location("c22_smoke_for_test", JOINT / "c22" / "smoke.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    cfg = mod.reduced()
    assert sha256(cfg) != sha256(config()) and cfg["data"]["eval_seed"] != FRESH_EVAL_SEED
    assert (cfg["data"]["train_seed"], cfg["data"]["eval_seed"], cfg["data"]["former_eval_seed"]) == TEST_SEEDS
    out = tmp_path / "smoke"
    mod.main(["--repo", REPO, "--out", str(out), "--device", "cpu", "--workers", "2"])
    rep = json.loads((out / "smoke_report.json").read_text())
    assert rep["check_labels"]["ok"] and rep["evaluate"]["same_with_workers"] and rep["resume"]["same_cap_steps"]
    assert rep["resume"]["max_weight_difference"] == 0.0 and set(rep["resume"]["max_prediction_difference"].values()) == {0.0}
    assert rep["machine"]["torch"] and rep["machine"]["processors"] >= 1 and rep["condense"]["energy_never_higher"]
    assert rep["machine"]["label_solver"] in ("scipy", "pardiso")
    assert set(rep["machine"]["thread_variables_of_the_workers"]) == set(data.THREAD_VARIABLES)
    assert rep["evaluate"]["sets"] == {"eval": 4, "former": 4, "tested": 2}
    with pytest.raises(SystemExit):
        mod.main(["--repo", REPO, "--out", str(out), "--device", "cpu", "--workers", "2"])     # nothing is deleted


# ---- the command line -----------------------------------------------------------------------------------------------
def test_the_command_line_runs_the_runbooks_commands(tmp_path, monkeypatch, capsys):
    """The runbook's commands in their order on a small configuration: write-config with the repository check,
    generate, label for the three labelled splits, check-labels, the three training runs and evaluate; train and
    evaluate refuse another configuration hash, label refuses the training split."""
    torch_or_skip()
    if not REPO:
        pytest.skip("FEJEPA_REPO is not set")
    import importlib.util
    import c22.config as cc
    cfg = small_cfg(n_train=2, n_eval=1, n_former=1, epochs=1)
    monkeypatch.setattr(cc, "config", lambda: copy.deepcopy(cfg))
    spec = importlib.util.spec_from_file_location("c22_main_for_cli_test", JOINT / "c22" / "__main__.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    sha, d, runs = sha256(cfg), str(tmp_path / "data"), str(tmp_path / "runs")

    def run(*argv):
        capsys.readouterr()
        mod.main(list(argv))
        return capsys.readouterr().out.strip().splitlines()

    out = run("write-config", "--out", str(tmp_path / "cfg.json"), "--repo", REPO)
    assert out[0] == f"config sha256 {sha}" and json.loads((tmp_path / "cfg.json").read_text()) == cfg
    assert [l.split()[0] for l in out[1:1 + len(mod.CODE)]] == mod.CODE
    assert sum(l.startswith("repository ") and l.endswith(" checked") for l in out) == len(cfg["repository_code"])
    run("generate", "--data", d)
    assert [r["split"] for r in data.manifest(d)["instances"]] == ["train"] * 2 + ["eval", "former", "tested"]
    with pytest.raises(SystemExit):
        run("label", "--data", d, "--split", "train")
    for split in ("eval", "former", "tested"):
        assert run("label", "--data", d, "--split", split, "--workers", "1")[-1] == "labelled 1"
    assert json.loads(run("check-labels", "--data", d)[-1])["ok"] is True
    with pytest.raises(SystemExit):
        run("train", "--data", d, "--runs", runs, "--seed", "5", "--repo", REPO, "--config-sha", "0" * 64)
    for seed in TRAINING_SEEDS:
        last = run("train", "--data", d, "--runs", runs, "--seed", str(seed), "--repo", REPO, "--config-sha", sha,
                   "--device", "cpu")[-1]
        assert json.loads(last) == {"status": "finished", "steps": 2}
    v = json.loads(run("evaluate", "--data", d, "--runs", runs, "--config-sha", sha, "--workers", "1")[-1])
    assert v["verdict"] in ("PASS", "FAIL") and not v["missing"] and not v["non_finite"]
    stored = json.loads((tmp_path / "runs" / "verdict.json").read_text())
    assert stored["verdict"] == v["verdict"] and stored["C1_value"] == v["C1_value"]
