"""Checks of the plastic reference code (fejoint.plasticity, nlhex, nlsolve, tstub_pl) and of the G-C2.1 run code
(c2). Torch tests need torch; training tests also need the FE-JEPA repository: set FEJEPA_REPO to its checkout,
whose files c2/config.py pins; otherwise they are skipped. Meshes here are coarse (COARSE) to keep the suite short."""
import copy
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

from fejoint.plasticity import Hardening, Material, radial_return, hencky, von_mises
from fejoint.tstub import TStubPair, analyse
from fejoint.tstub_pl import PlasticTStubModel
from c2.config import config, sha256, SEEDS_SEEN, TESTED
from c2.family import sample, violations, Params, geometry
from c2.instance import build, export, ExportedProblem
from c2 import data

REPO = os.environ.get("FEJEPA_REPO")
TEST_SEEDS = (7, 8)        # seeds seen before the stamp: the tests never draw, export or solve a member of the gate
COARSE = {"h": 10.0, "n_tf": 1, "hx_max": 40.0}
E, NU = 210000.0, 0.3
MATS = {"bilinear": Material(E, NU, Hardening.bilinear(355.0, 2100.0)),
        "multilinear": Material(E, NU, Hardening([0, 0.015, 0.05, 0.15], [355, 360, 450, 520], h_end=100.0)),
        "plateau": Material(E, NU, Hardening([0, 0.02], [355, 355], h_end=0.0))}


def torch_or_skip():
    return pytest.importorskip("torch")


def small_cfg(n_train=2, n_eval=2, epochs=2):
    cfg = copy.deepcopy(config())
    d = cfg["data"]
    d["n_train"], d["n_eval"] = n_train, n_eval
    d["train_seed"], d["eval_seed"] = TEST_SEEDS
    d["seeds_seen_before_stamp"] = [s for s in d["seeds_seen_before_stamp"] if s not in TEST_SEEDS]
    d["mesh"] = dict(COARSE)
    d["eval_levels_mm"], d["train_label_levels_mm"] = [0.25, 1.5], [0.5, 2.0]
    d["n_train_labelled"] = n_train
    d["tested"] = {"BJ_T1_preloaded": dict(TESTED["BJ_T1_preloaded"])}
    cfg["model"].update(dim=16, depth=1, heads=2)
    cfg["training"]["fields_per_step"] = 2
    cfg["training"]["bubble_newton_steps"] = 4
    for a in cfg["arms"].values():
        a["epochs"] = epochs
        a["labels"] = min(a["labels"], n_train)
    return cfg


# ---- the material law -----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", list(MATS))
def test_hencky_energy_stress_tangent_and_yield(name):
    mat = MATS[name]
    rng = np.random.default_rng(0)
    eps = rng.normal(size=(300, 6)) * rng.uniform(2e-4, 8e-3, size=(300, 1))    # elastic and plastic points
    sig, D, W, pl, a = hencky(eps, mat)
    assert 0.2 < pl.mean() < 0.95
    h = 1e-8
    for k in range(6):
        e2 = eps.copy(); e2[:, k] += h; e1 = eps.copy(); e1[:, k] -= h
        s2, _, W2, _, _ = hencky(e2, mat); s1, _, W1, _, _ = hencky(e1, mat)
        assert np.max(np.abs((W2 - W1) / (2 * h) - sig[:, k])) <= 1e-6 * np.abs(sig).max()
        assert np.max(np.abs((s2 - s1) / (2 * h) - D[:, :, k])) <= 1e-5 * np.abs(D).max()
    assert np.max(np.abs(von_mises(sig)[pl] - mat.hardening.sy(a[pl]))) <= 1e-9 * mat.hardening.sigma[0]
    # flow theory along a proportional path equals deformation theory (isotropic hardening, radial path)
    ep, al = np.zeros((300, 6)), np.zeros(300)
    for s in range(1, 21):
        sk, _, ep, al, _, _ = radial_return(eps * s / 20, ep, al, mat)
    assert np.max(np.abs(sk - sig)) <= 1e-9 * np.abs(sig).max()
    # convexity of the energy along random chords
    ea, eb = rng.normal(scale=6e-3, size=(1000, 6)), rng.normal(scale=6e-3, size=(1000, 6))
    Wa, Wb, Wm = (hencky(e, mat, False)[2] for e in (ea, eb, 0.5 * (ea + eb)))
    assert np.max(Wm - 0.5 * (Wa + Wb)) <= 1e-12 * np.abs(Wa).max()


def test_flow_tangent_and_potential_from_a_plastic_state():
    mat = MATS["multilinear"]
    rng = np.random.default_rng(1)
    eps = rng.normal(scale=6e-3, size=(200, 6))
    _, _, ep, al, _, _ = radial_return(eps, np.zeros((200, 6)), np.zeros(200), mat)
    e2 = 1.1 * eps + rng.normal(scale=1e-3, size=eps.shape)
    s0, D0, *_ = radial_return(e2, ep, al, mat)
    h = 1e-8
    for k in range(6):
        a = e2.copy(); a[:, k] += h; b = e2.copy(); b[:, k] -= h
        ra, rb = radial_return(a, ep, al, mat), radial_return(b, ep, al, mat)
        assert np.max(np.abs((ra[0] - rb[0]) / (2 * h) - D0[:, :, k])) <= 1e-5 * np.abs(D0).max()
        assert np.max(np.abs((ra[4] - rb[4]) / (2 * h) - s0[:, k])) <= 1e-6 * np.abs(s0).max()


# ---- the plastic T-stub model -----------------------------------------------------------------------------------------
T1 = TStubPair(t_f=10.7, t_w=7.1, b=150.0, L=80.0, w=90.0, bolt_y=(20.0,), H=120.0, corner="root", r=15.0,
               d=12.0, As=84.3, head=7.5, nut=10.8, bearing_r=12.0, n_washers=2, washer_t=2.5, x_meas=60.0)


def test_elastic_limit_equals_the_linear_tstub():
    lin = analyse(T1, h=10.0, n_tf=1)
    for mat in (Material(E, NU, None), Material(E, NU, Hardening.bilinear(1e9, 1000.0))):
        m = PlasticTStubModel(T1, mat, mat, h=10.0, n_tf=1, control="force")
        for mode in ("hencky", "flow"):
            z, rep = m.solve(10000.0, mode=mode)
            r = m.readings(z, rep)
            assert rep["converged"]
            assert abs(10000.0 / r["Delta_web_mm"] / 1000.0 / lin["K_kN_per_mm"] - 1) <= 1e-9
            assert abs(4 * sum(r["bolt_force_N"]) / lin["bolt_force_total_N"] - 1) <= 1e-9


def test_preload_and_displacement_control():
    mat = Material(E, NU, Hardening.bilinear(431.0, 2100.0))
    m = PlasticTStubModel(T1, mat, mat, h=10.0, n_tf=1, control="displacement")
    pre = m.set_preload(60000.0)
    z, rep = m.solve(0.0, control="force")
    assert abs(m.readings(z, rep)["bolt_force_N"][0] / 60000.0 - 1) <= 1e-6 and pre["delta"] > 0
    z, rep = m.solve(1.0)
    r = m.readings(z, rep)
    assert rep["converged"] and r["F_N"] > 0 and abs(r["d_end_mm"] - 1.0) <= 1e-12
    assert all(abs(v) <= 1e-8 for k, v in r["kkt"].items() if k != "min_gap") and r["kkt"]["min_gap"] >= -1e-12


# ---- the family and the exported problem ------------------------------------------------------------------------------
def test_config_hash_is_stable_and_seeds_are_fresh():
    a, b = config(), config()
    assert sha256(a) == sha256(b)
    assert a["data"]["train_seed"] not in SEEDS_SEEN and a["data"]["eval_seed"] not in SEEDS_SEEN
    assert set(TEST_SEEDS) <= set(SEEDS_SEEN) and a["data"]["seeds_seen_before_stamp"] == SEEDS_SEEN
    c = copy.deepcopy(a); c["map"]["T"] = 2e-3
    assert sha256(c) != sha256(a)
    with pytest.raises(AssertionError):
        c = copy.deepcopy(a); c["data"]["train_seed"] = 7
        data.members(c)


def test_members_are_deterministic_and_valid():
    cfg = small_cfg()
    m1, m2 = data.members(cfg), data.members(cfg)
    assert [x[0] for x in m1] == [x[0] for x in m2] and [x[2] for x in m1] == [x[2] for x in m2]
    assert len({x[0] for x in m1}) == len(m1)
    assert all(not violations(x[2]) for x in m1)
    full = config()
    for name, p in full["data"]["tested"].items():
        assert not violations(Params(**p)), name


@pytest.fixture(scope="module")
def member():
    q = sample(1, TEST_SEEDS[0])[0][0]
    m = build(q, mesh=COARSE)
    return q, m, export(m, q)


def test_exported_problem_equals_the_model(member):
    """The spring-loaded export reproduces the model under displacement control at the same end displacement
    (deformation theory: the state at a given end displacement does not depend on the loading device)."""
    q, m, ex = member
    P = ExportedProblem(ex)
    r = P.solve(1.5)
    assert r["converged"] and 0 < r["e"] < 1.5
    assert abs(r["F_sigma"] / r["F"] - 1) <= 1e-8                     # the two readings of the exact solution
    z, rep = m.solve(r["e"], mode="hencky", z0=np.zeros(m.nfull))
    F_model = m.readings(z, rep)["F_N"]
    assert rep["converged"] and abs(F_model / r["F"] - 1) <= 1e-8
    re = P.solve_at_e(r["e"])
    assert re["converged"] and abs(re["F"] / r["F"] - 1) <= 1e-8


def test_force_reading_bound(member):
    """|F(z) - F*| <= 4 sqrt(2 k_s (Pi(z) - Pi*)) for feasible fields z near and far from the solution."""
    q, m, ex = member
    P = ExportedProblem(ex)
    r = P.solve(1.0)
    rng = np.random.default_rng(2)
    for amp in (1e-3, 1e-2, 1e-1):
        z = np.where(P.prob.fixed, 0.0, r["z"] * (1 + amp * rng.normal(size=r["z"].size)))
        z[P.prob.cidx] = np.maximum(z[P.prob.cidx], 0.0)
        e = P.evaluate(z, 1.0)
        assert e["Pi"] >= r["Pi"] - 1e-9 * r["Pi"]
        assert abs(e["F"] - r["F"]) <= 4.0 * np.sqrt(2.0 * P.k_s * max(e["Pi"] - r["Pi"], 0.0)) * (1 + 1e-9)


# ---- the training energy (torch) --------------------------------------------------------------------------------------
def test_closed_form_hencky_equals_the_return_mapping():
    torch = torch_or_skip()
    from c2.torch_energy import HenckyLaw
    from c2.family import steel
    mat = steel(355.0)
    hd = mat.hardening
    law = HenckyLaw(hd.alpha, hd.sigma, hd.h_end, E, NU, "cpu", torch.float64)
    eps = np.random.default_rng(3).normal(scale=1e-2, size=(500, 6))
    sn, Dn, Wn, _, _ = hencky(eps, mat)
    st, Dt = law.stress_tangent(torch.as_tensor(eps))
    Wt = law.energy(torch.as_tensor(eps)).numpy()
    assert np.max(np.abs(Wt - Wn)) <= 1e-12 * np.abs(Wn).max()
    assert np.max(np.abs(st.numpy() - sn)) <= 1e-12 * np.abs(sn).max()
    assert np.max(np.abs(Dt.numpy() - Dn)) <= 1e-12 * np.abs(Dn).max()


def test_torch_energy_and_gradient_equal_the_reference(member):
    torch = torch_or_skip()
    from c2.torch_energy import InstanceEnergy
    q, m, ex = member
    P = ExportedProblem(ex)
    r = P.solve(2.0)
    rng = np.random.default_rng(4)
    Z = np.stack([r["z"], np.where(P.prob.fixed, 0.0, r["z"] * (1 + 0.1 * rng.normal(size=r["z"].size)))])
    Z[:, P.prob.cidx] = np.maximum(Z[:, P.prob.cidx], 0.0)
    zt = torch.tensor(Z, requires_grad=True)
    D = torch.tensor([2.0, 2.0], dtype=torch.float64)
    Et = InstanceEnergy(ex, dtype=torch.float64).energy(zt, D, iters=30)
    Et.sum().backward()
    free = ~P.prob.fixed
    P.loading.delta[:] = -2.0
    for b in range(2):
        Pi, g = P.prob.evaluate(Z[b], "hencky", tangent=False)[:2]
        assert abs(float(Et[b].detach()) / Pi - 1) <= 1e-12
        assert np.max(np.abs(zt.grad[b].numpy()[free] - g[free])) <= 1e-9 * np.abs(g[free]).max()
    E32 = InstanceEnergy(ex).energy(torch.tensor(Z[:1], dtype=torch.float32), torch.tensor([2.0]), iters=10)
    assert abs(float(E32[0]) / r["Pi"] - 1) <= 1e-5


# ---- the network and the run ------------------------------------------------------------------------------------------
@pytest.mark.skipif(not REPO, reason="set FEJEPA_REPO to the repository checkout")
def test_field_meets_the_constraints(member):
    torch = torch_or_skip()
    sys.path.insert(0, str(Path(REPO) / "src"))
    from c2.model import features, maps, build as build_net, field
    q, m, ex = member
    cfg = small_cfg()
    torch.manual_seed(0)
    nets = build_net(cfg, 21)
    for net in nets[1:]:                                # non-zero last layers, so the map is exercised
        torch.nn.init.normal_(net[-1].weight, std=0.5); torch.nn.init.normal_(net[-1].bias, std=0.5)
    base = torch.as_tensor(features(ex, q), dtype=torch.float32)
    mp = maps(ex, "cpu")
    D = torch.tensor([0.1, 1.0, 4.0])
    fixed, e_idx = np.asarray(ex["fixed"]), int(ex["e_idx"])
    zs = {}
    for lift in (False, True):
        z = zs[lift] = field(*nets, base, mp, D, 1e-3, lift=lift).detach().numpy()
        assert np.isfinite(z).all() and (z[:, np.asarray(ex["cidx"])] >= 0).all()
        assert np.all(z[:, fixed] == 0) and np.all(z[:, e_idx] != 0)
    web = np.zeros(fixed.size, bool); web[3 * np.nonzero(np.asarray(ex["node_flags"])[:, 4])[0]] = True
    web &= ~fixed
    assert web.sum() > 0
    shift = zs[True] - zs[False]
    assert np.allclose(shift[:, web], zs[True][:, [e_idx]], rtol=0, atol=1e-5) and np.all(shift[:, ~web] == 0)
    if float(ex["delta"]) == 0.0:
        z0 = field(*nets, base, mp, torch.tensor([0.0]), 1e-3, lift=True).detach().numpy()
        assert np.all(z0 == 0)


# ---- the run: data, labels, evaluation and verdict, training ---------------------------------------------------------
@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    """A small configuration's data, exported and labelled: 2 training (labelled), 2 held-out, 1 tested member."""
    cfg = small_cfg()
    d = tmp_path_factory.mktemp("c2data")
    data.generate(cfg, d)
    data.label(cfg, d, data.labelled_ids(cfg, d), workers=1)
    return cfg, d


def _ids(d, splits=("eval", "tested")):
    return [r["id"] for r in data.manifest(d)["instances"] if r["split"] in splits]


def _write_preds(cfg, d, runs, change=None, skip=()):
    """Predictions equal to the labels (optionally changed) for every run of the configuration."""
    for arm, a in cfg["arms"].items():
        for s in a["seeds"]:
            run = runs / f"{arm}_s{s}"; run.mkdir(parents=True, exist_ok=True)
            if (arm, s) in skip:
                continue
            Z = {i: data.load_label(d, i)["z"].astype(np.float32) for i in _ids(d)}
            if change and (arm, s) in change:
                Z = {i: change[(arm, s)](z) for i, z in Z.items()}
            np.savez_compressed(run / "preds.npz", **Z)


def test_generate_label_and_load(dataset):
    cfg, d = dataset
    man = data.manifest(d)
    assert man["config_sha256"] == sha256(cfg) and man["n"] == 2 + 2 + 1
    r = man["instances"][2]
    ex, q = data.load_export(d / r["file"])
    direct = data.export_member(cfg, q)
    assert set(ex) == set(direct) and all(np.array_equal(np.asarray(ex[k]), np.asarray(direct[k])) for k in ex)
    lab = data.load_label(d, r["id"])
    assert list(lab["D"]) == sorted(cfg["data"]["eval_levels_mm"]) and lab["z"].shape == (2, int(ex["e_idx"]) + 1)
    chk = data.check_labels(cfg, d)
    assert chk["ok"] and chk["labels"] == chk["needed"] == 5 and chk["max_F_vs_F_sigma"] <= 1e-8, chk
    led = json.loads((d / "labels" / "ledger.json").read_text())
    tr = [e for e in led if e["id"].startswith("train")]
    assert tr and all(e["levels"] == sorted(cfg["data"]["train_label_levels_mm"]) for e in tr)


def test_files_of_another_configuration_or_a_changed_label_are_refused(dataset, tmp_path):
    cfg, d = dataset
    c = tmp_path / "copy"
    shutil.copytree(d, c)
    other = copy.deepcopy(cfg); other["data"]["mesh"]["h"] = 8.0
    with pytest.raises(RuntimeError):
        data.generate(other, c)
    iid = _ids(c)[0]
    lab = data.load_label(c, iid)
    np.savez_compressed(c / "labels" / f"{iid}.npz", **{**lab, "z": 2 * lab["z"]})
    with pytest.raises(RuntimeError):
        data.check_files(c, [iid])
    shutil.copy(d / "labels" / f"{iid}.npz", c / "labels" / f"{iid}.npz")
    led = json.loads((c / "labels" / "ledger.json").read_text())
    led[0]["kkt_worst"]["max_residual_unconstrained"] = 1e-3
    (c / "labels" / "ledger.json").write_text(json.dumps(led))
    assert not data.check_labels(cfg, c)["ok"]


def test_evaluation_of_exact_predictions(dataset, tmp_path):
    """Predictions equal to the reference: no curve error, no gap, full overlaps, PASS."""
    cfg, d = dataset
    from c2.evaluate import evaluate
    _write_preds(cfg, d, tmp_path)
    v = evaluate(cfg, d, tmp_path)
    assert v["verdict"] == "PASS" and v["C1_value"] < 1e-6 and v["C2_value"] < 1e-6, v.get("per_seed")
    ev = v["arms"]["label_free"]["0"]["eval"]
    assert ev["gap"]["max"] < 1e-6 and ev["abs_F_err"]["max"] < 1e-6 and ev["iou_contact"]["min"] == 1.0
    assert ev["within_bound_fraction"] == 1.0 and ev["evaluate_failed"] == 0 and ev["curve_infinite"] == 0


def test_quantile_keeps_infinite_order_statistics():
    """The 90th percentile of 448 pairs: infinite as soon as the upper order statistic it uses is infinite (45
    infinite pairs), finite below that (44), and np.quantile's value when no pair is infinite."""
    from c2.evaluate import _quantile
    inf = float("inf")
    base = list(np.linspace(0.01, 0.5, 448))
    assert _quantile(base[:403] + [inf] * 45, 0.9) == inf
    assert np.isfinite(_quantile(base[:404] + [inf] * 44, 0.9))
    assert _quantile(base[:402] + [inf] * 46, 0.9) == inf
    assert _quantile(base, 0.9) == float(np.quantile(base, 0.9)) and _quantile(base, 0.5) == float(np.median(base))
    assert _quantile([0.02, inf, inf], 0.5) == inf and _quantile([0.02, 0.03, inf], 0.5) == 0.03


def test_non_finite_infinite_and_missing_label_free_seeds(dataset, tmp_path):
    """A non-finite label-free seed enters the medians as infinite; pairs with infinite curve errors keep the 90th
    percentile infinite, never not-a-number; a missing seed gives INCOMPLETE."""
    cfg, d = dataset
    from c2.evaluate import evaluate
    def compress(z):                                   # e far below the unloaded state: the reference force < 0
        z = z.copy(); z[:, -1] = -1.0                  # e is the last unknown of every member
        return z

    _write_preds(cfg, d, tmp_path, change={("label_free", 2): compress},
                 skip={("label_free", 1)})
    (tmp_path / "label_free_s1" / "history.json").write_text(json.dumps({"status": "non-finite loss at step 7"}))
    v = evaluate(cfg, d, tmp_path)
    assert v["status"]["label_free_s1"] == "non-finite" and v["non_finite"] == ["label_free_s1"]
    ev2 = v["arms"]["label_free"]["2"]["eval"]
    assert ev2["curve_infinite"] == ev2["abs_curve_err"]["n"] and ev2["abs_curve_err"]["p90"] == float("inf")
    assert v["per_seed"]["abs_curve_err_p90"][1:] == [float("inf"), float("inf")]
    assert v["verdict"] == "FAIL" and v["C1_value"] == float("inf") and v["C2_value"] == float("inf")
    (tmp_path / "label_free_s1" / "history.json").unlink()
    _write_preds(cfg, d, tmp_path, change={("label_free", 2): compress})
    v = evaluate(cfg, d, tmp_path)                    # one seed of three infinite: the medians still pass
    assert v["verdict"] == "PASS" and v["per_seed"]["abs_curve_err_p90"][2] == float("inf")
    (tmp_path / "label_free_s2" / "preds.npz").unlink()
    v = evaluate(cfg, d, tmp_path)
    assert v["verdict"] == "INCOMPLETE" and v["missing"] == ["label_free_s2"] and "C1_value" not in v
    assert v["arms"]["label_free"] == {"withheld": "the verdict is INCOMPLETE"}


@pytest.mark.skipif(not REPO, reason="set FEJEPA_REPO to the repository checkout")
@pytest.mark.parametrize("arm", ["label_free", "supervised_64"])
def test_train_resume_and_predict(dataset, tmp_path, arm, monkeypatch):
    """A tiny model trains; an interrupted run resumes (checkpoint loaded on the CPU) to the same end state as an
    uninterrupted one; a finished run returns without loading its members; the bench runs."""
    torch = torch_or_skip()
    sys.path.insert(0, str(Path(REPO) / "src"))
    import c2.train as ct
    cfg, d = dataset
    a_full, a_int = tmp_path / "full", tmp_path / "interrupted"
    h1 = ct.train(cfg, arm, 0, d, a_full, device="cpu", ckpt_every_epochs=1)
    assert h1["status"] == "finished" and np.isfinite(h1["loss"]).all()
    assert h1["config_sha256"] == sha256(cfg) and h1["matmul_precision"] == "highest"
    ct.train(cfg, arm, 0, d, a_int, device="cpu", ckpt_every_epochs=1, stop_after_epoch=1)
    assert not (a_int / f"{arm}_s0" / "preds.npz").exists()
    where, real = [], torch.load
    monkeypatch.setattr(torch, "load", lambda *a, **k: where.append(k.get("map_location")) or real(*a, **k))
    h2 = ct.train(cfg, arm, 0, d, a_int, device="cpu", ckpt_every_epochs=1)
    monkeypatch.undo()
    assert where == ["cpu"] and h2["resumed_from_epoch"] == 1 and h2["resumes"] == [1] and h2["status"] == "finished"
    monkeypatch.setattr(ct, "_prepare", lambda *a, **k: pytest.fail("a finished run loaded its members"))
    assert ct.train(cfg, arm, 0, d, a_full, device="cpu")["status"] == "finished"
    monkeypatch.undo()
    s1 = torch.load(a_full / f"{arm}_s0" / "state.pt", weights_only=False)
    s2 = torch.load(a_int / f"{arm}_s0" / "state.pt", weights_only=False)
    for part in ("enc", "dec", "head"):
        for k in s1[part]:
            assert torch.equal(s1[part][k], s2[part][k]), (part, k)
    with np.load(a_full / f"{arm}_s0" / "preds.npz") as z1, np.load(a_int / f"{arm}_s0" / "preds.npz") as z2:
        assert set(z1.files) == set(z2.files) == set(_ids(d))
        for k in z1.files:
            assert z1[k].dtype == np.float32 and z1[k].shape[0] == len(cfg["data"]["eval_levels_mm"])
            assert np.array_equal(z1[k], z2[k])
    if arm == "label_free":
        b = ct.bench(cfg, d, device="cpu", instances=2, warmup=1, steps=2)
        assert b["losses_finite"] and len(b["losses"]) == 3


@pytest.mark.skipif(not REPO, reason="set FEJEPA_REPO to the repository checkout")
def test_a_non_finite_stop_is_final(dataset, tmp_path, monkeypatch):
    """A run that meets a non-finite loss records it, writes no predictions, and is never retried; so is a run whose
    predictions are not finite; a run folder of another configuration is refused."""
    torch = torch_or_skip()
    sys.path.insert(0, str(Path(REPO) / "src"))
    import c2.train as ct
    cfg, d = dataset
    real = ct.field
    monkeypatch.setattr(ct, "field", lambda *a, **k: real(*a, **k) * float("nan"))
    h1 = ct.train(cfg, "label_free", 1, d, tmp_path, device="cpu", ckpt_every_epochs=1)
    monkeypatch.undo()
    run = tmp_path / "label_free_s1"
    assert h1["status"] == "non-finite loss at step 0" and not (run / "preds.npz").exists()
    before = (run / "history.json").read_text()
    h2 = ct.train(cfg, "label_free", 1, d, tmp_path, device="cpu", ckpt_every_epochs=1)
    assert h2["status"] == h1["status"] and (run / "history.json").read_text() == before
    monkeypatch.setattr(ct, "field", lambda *a, **k: real(*a, **k) * (1.0 if torch.is_grad_enabled() else float("nan")))
    h3 = ct.train(cfg, "label_free", 2, d, tmp_path, device="cpu", ckpt_every_epochs=1)
    monkeypatch.undo()
    run2 = tmp_path / "label_free_s2"
    assert h3["status"] == "non-finite predictions" and not (run2 / "preds.npz").exists()
    assert ct.train(cfg, "label_free", 2, d, tmp_path, device="cpu")["status"] == "non-finite predictions"
    assert (run2 / "attempts.log").read_text().count("start") == 2
    (tmp_path / "y" / "label_free_s0").mkdir(parents=True)
    (tmp_path / "y" / "label_free_s0" / "history.json").write_text(json.dumps({"config_sha256": "0" * 64}))
    with pytest.raises(RuntimeError):
        ct.train(cfg, "label_free", 0, d, tmp_path / "y", device="cpu")


@pytest.mark.skipif(not REPO, reason="set FEJEPA_REPO to the repository checkout")
def test_repository_files_are_checked():
    sys.path.insert(0, str(Path(REPO) / "src"))
    from c2.train import verify_repository
    cfg = config()
    assert Path(verify_repository(cfg)) == Path(REPO).resolve()
    bad = copy.deepcopy(cfg); bad["repository_code"]["src/fejepa/train/schedule.py"] = "0" * 64
    with pytest.raises(RuntimeError):
        verify_repository(bad)
