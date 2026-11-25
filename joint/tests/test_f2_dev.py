"""Checks of the development code of the CHS surrogate (f2/model.py, f2/train.py, f2/evaluate.py, f2/devconfig.py;
drafts, nothing stamped): the lift fields, the field of the network, training with pause and resume, the
predictions, and the evaluation with its cleared state. Tiny mesh; torch tests need torch, and training tests also
need the repository: set FEJEPA_REPO to its checkout."""
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

from f2 import devconfig, data as D, instance as I
from f2.family import Params, TESTED, loading, geometry
from f2.model import LIFTS, LIFT_KINDS, lift_field, lift_fields, features, maps

TINY = "tiny"
REPO = os.environ.get("FEJEPA_REPO")
needs_repo = pytest.mark.skipif(not REPO, reason="set FEJEPA_REPO to the repository checkout")
MEMBER = "tested_B-13_nominal"


def torch_or_skip():
    return pytest.importorskip("torch")


def dry_config() -> dict:
    cfg = devconfig.config("dry")
    cfg["data"]["mesh"] = TINY
    cfg["data"]["eval_levels"] = [0.25, 1.0]                     # two levels keep the labels and the solves short
    cfg["evaluation"]["members"] = [MEMBER]
    return cfg


@pytest.fixture(scope="module")
def bare():
    """B-13 exported without its preload solve (no pre-shortening): enough for the lift fields."""
    q = Params(**TESTED["B-13_nominal"])
    k_th, Tm = loading(q)
    ex = I.export(I.build(q, TINY), q, k_th, 0.0)
    ex["Theta_max"] = np.float64(Tm)
    return q, ex


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    cfg = dry_config()
    d = tmp_path_factory.mktemp("f2dev")
    D.generate(cfg, d, only=["train_0000", "train_0001", MEMBER])
    D.label(cfg, d, [MEMBER])
    return cfg, d


def test_presets_share_the_data_and_differ_in_the_run():
    a, b = devconfig.config("one_bending"), devconfig.config("fam128_rigid")
    assert D.data_sha256(a) == D.data_sha256(b)
    assert devconfig.sha256(a) != devconfig.sha256(b)
    ids = [m[0] for m in D.members(a)]
    assert len(ids) == len(set(ids)) == devconfig.N_TRAIN + devconfig.N_EVAL + len(devconfig.DEV_MEMBERS) + len(TESTED)
    for s in (devconfig.TRAIN_SEED, devconfig.EVAL_SEED):
        assert s not in a["data"]["seeds_seen_before_stamp"]


def test_lift_fields(bare):
    """Every lift is zero on theta, on the fixed and on the contact unknowns. Far from the plate the lift 'bending'
    is the pure bending of the tube: its energy is the beam's within 5%; 'beam' carries the constrained sections'
    excess, 'v' also the shear, and no lift strains the last layer of elements only."""
    q, ex = bare
    P = I.ExportedProblem(ex)
    n_z, ith = int(ex["v"].size), int(ex["ith"])
    nonneg = np.zeros(n_z, bool); nonneg[np.asarray(ex["cidx"], int)] = True
    g = geometry(q)
    L = ex["nodes"][:, 2].max() - float(ex["z_h"])
    U_beam = 0.5 * float(ex["E_t"]) * np.pi / 8 * (g.R ** 4 - g.r_i ** 4) / L       # half tube, unit end rotation
    th, U = 1e-5, {}
    for kind in LIFTS:
        lf = lift_field(ex, q, kind)
        assert lf[ith] == 0 and not lf[np.asarray(ex["fixed"], bool)].any() and not lf[nonneg].any()
        z = th * lf
        z[ith] = th
        for s in P.solids:
            s.bub[:] = 0.0
        U[kind] = P.evaluate(z, th)["Pi"] / th ** 2
    assert not lift_field(ex, q, "none").any()
    assert U["bending"] == pytest.approx(U_beam, rel=0.05)
    assert U["bending"] < U["beam"] < U["v"] < U["none"] < U["rigid"]
    assert U["beam"] == pytest.approx(1.346 * U_beam, rel=0.03)  # (1 - nu) / ((1 + nu)(1 - 2 nu)) at nu = 0.3
    # the lift "frame": axial translation, rotation about the base, pure bending from the base to the end section
    F = lift_fields(ex, q, "frame")
    iw0 = int(ex["iw0"])
    assert not F[:, np.asarray(ex["fixed"], bool) | nonneg].any() and not F[:, [ith, iw0]].any()
    assert np.array_equal(lift_fields(ex, q, "bending"), np.stack([0 * lf, 0 * lf, lift_field(ex, q, "bending")]))

    def energy(w, phi, theta):
        z = w * F[0] + phi * F[1] + (theta - phi) * F[2]
        z[iw0], z[ith] = w, theta
        for s in P.solids:
            s.bub[:] = 0.0
        return P.evaluate(z, theta)["Pi"]

    Lt = ex["nodes"][:, 2].max() - g.tp
    U_full = 0.5 * float(ex["E_t"]) * np.pi / 8 * (g.R ** 4 - g.r_i ** 4) / Lt
    assert energy(0.0, 0.0, th) / th ** 2 == pytest.approx(U_full, rel=0.05)
    assert energy(0.0, th, th) > 20 * energy(0.0, 0.0, th)       # a rigid rotation strains the base only, but much


@needs_repo
def test_field_is_admissible(bare):
    """The network's field has zeros on the fixed unknowns and non-negative contact unknowns, for every lift, and
    with zeroed last layers it is the map's floor times the scale."""
    torch = torch_or_skip()
    sys.path.insert(0, str(Path(REPO) / "src"))
    from f2.model import build, field, L_REF

    q, ex = bare
    cfg = dry_config()
    base = torch.as_tensor(features(ex, q), dtype=torch.float32)
    Theta = torch.tensor([0.001, 0.02], dtype=torch.float32)
    for kind in LIFT_KINDS:
        mp = maps(ex, q, "cpu", kind)
        torch.manual_seed(0)
        cfg["model"]["lift"] = kind
        nets = build(cfg, base.shape[-1] + 1, mp["nb"])
        with torch.no_grad():
            z0 = field(*nets, base, mp, Theta, 1e-3)
            for net in nets[1:]:
                net[-1].weight.normal_(0.0, 0.3)
            z = field(*nets, base, mp, Theta, 1e-3)
        s = L_REF * Theta + mp["delta"]
        floor = 1e-3 * float(np.log(2.0)) * s
        assert torch.allclose(z0[:, mp["nonneg"]], floor[:, None].expand(-1, int(mp["nonneg"].sum())), rtol=1e-5)
        assert not z0[:, ~mp["nonneg"]].any()
        assert z.shape == (2, mp["n_z"]) and bool(torch.isfinite(z).all())
        assert not z[:, mp["fixed"]].any() and bool((z[:, mp["nonneg"]] >= 0).all())
        assert z[:, :3 * mp["n"]].abs().max() > 0


@pytest.fixture(scope="module")
def runs(dataset, tmp_path_factory):
    """The dry configuration trained twice with the same seed: in one go, and with a pause after two epochs."""
    if not REPO:
        pytest.skip("FEJEPA_REPO is not set")
    torch_or_skip()
    sys.path.insert(0, str(Path(REPO) / "src"))
    from f2.train import train

    cfg, d = dataset
    a, b = tmp_path_factory.mktemp("straight"), tmp_path_factory.mktemp("paused")
    ha = train(cfg, 0, d, a, device="cpu")
    hp = train(cfg, 0, d, b, device="cpu", stop_after_epoch=2)
    assert hp["status"] == "paused" and not (b / "label_free_s0" / "history.json").exists()
    hb = train(cfg, 0, d, b, device="cpu")
    return cfg, d, a, b, ha, hb


@needs_repo
def test_open_gate_keeps_the_values_and_lets_an_opening_pull_through(bare):
    """The gate "softplus_open": the same field as the softplus map; in the backward pass a pull that opens a
    contact passes unreduced and a push that closes it is multiplied by the map's slope; a contact held far in the
    closed range opens under it and does not under the plain map."""
    torch = torch_or_skip()
    sys.path.insert(0, str(Path(REPO) / "src"))
    from f2.model import build, field, open_gate, GATES

    assert GATES == ("softplus", "softplus_open")
    T = 1e-3
    u = torch.tensor([-0.05, -0.005, 0.0, 0.004, 0.3], dtype=torch.float64, requires_grad=True)
    plain = T * torch.nn.functional.softplus(u / T)
    gated = open_gate()(u, T)
    assert torch.equal(plain, gated)
    slope = torch.sigmoid(u.detach() / T)
    for sign in (-1.0, 1.0):                                    # the loss sign * sum(value): pull up, push down
        (g,) = torch.autograd.grad(sign * gated.sum(), u, retain_graph=True)
        (gp,) = torch.autograd.grad(sign * plain.sum(), u, retain_graph=True)
        assert torch.allclose(gp, sign * slope)
        assert torch.allclose(g, -torch.ones_like(u) if sign < 0 else slope)

    def descend(fn, steps=200, lr=1e-2):                        # (value - 0.1)^2 from a closed contact
        w = torch.tensor([-0.05], dtype=torch.float64, requires_grad=True)
        for _ in range(steps):
            (g,) = torch.autograd.grad(((fn(w) - 0.1) ** 2).sum(), w)
            w = (w - lr * g).detach().requires_grad_(True)
        return float(fn(w))

    assert descend(lambda w: T * torch.nn.functional.softplus(w / T)) < 1e-12       # the plain map stays closed
    assert abs(descend(lambda w: open_gate()(w, T)) - 0.1) < 0.02                   # the gate opens it

    q, ex = bare
    cfg = dry_config()
    base = torch.as_tensor(features(ex, q), dtype=torch.float32)
    Theta = torch.tensor([0.001, 0.02], dtype=torch.float32)
    mp = maps(ex, q, "cpu", "frame")
    cfg["model"]["lift"] = "frame"
    torch.manual_seed(0)
    nets = build(cfg, base.shape[-1] + 1, mp["nb"])
    with torch.no_grad():
        for net in nets[1:]:
            net[-1].weight.normal_(0.0, 0.3)
        nets[1][-1].bias.fill_(-0.5)                            # every contact held closed: outputs well below -T
    za = field(*nets, base, mp, Theta, T)
    zb = field(*nets, base, mp, Theta, T, gate="softplus_open")
    assert torch.equal(za, zb) and float(za[:, mp["nonneg"]].max()) < 1e-12
    w = nets[1][-1].weight
    (ga,) = torch.autograd.grad(-za[:, mp["nonneg"]].sum(), w, retain_graph=True)   # a loss that pulls them open
    (gb,) = torch.autograd.grad(-zb[:, mp["nonneg"]].sum(), w, retain_graph=True)
    assert float(ga.abs().sum()) < 1e-12 < 1.0 < float(gb.abs().sum())  # only the gate lets the pull reach the decoder
    (gc,) = torch.autograd.grad(zb[:, mp["nonneg"]].sum(), w)   # a loss that pushes them closed: the slope, nothing
    assert float(gc.abs().sum()) < 1e-12
    with pytest.raises(AssertionError):
        field(*nets, base, mp, Theta, T, gate="relu")


def test_training_pause_and_resume(runs):
    cfg, d, a, b, ha, hb = runs
    assert ha["status"] == hb["status"] == "finished" and ha["steps"] == hb["steps"] == 6
    assert hb["resumes"] == [2] and ha["resumes"] == []
    assert ha["loss"] == pytest.approx(hb["loss"], rel=1e-6)
    ra, rb = a / "label_free_s0", b / "label_free_s0"
    for name in ("preds.npz", "preds_condensed.npz", "preds_base.npz"):
        with np.load(ra / name) as za, np.load(rb / name) as zb:
            assert za.files == zb.files == [MEMBER]
            assert np.allclose(za[MEMBER], zb[MEMBER], rtol=1e-4, atol=1e-7)
    snaps = json.loads((ra / "snapshots.json").read_text())
    assert sorted(snaps) == ["1", "3"] and set(snaps["3"][MEMBER]) == {"Theta", "Pi", "theta", "M", "ThetaD"}
    prog = json.loads((ra / "progress.json").read_text())
    assert prog["state"] == "finished" and prog["epoch"] == 3 and prog["step"] == 6
    log = (rb / "attempts.log").read_text()
    assert "paused after epoch 2" in log and "resumed from epoch 2" in log and "ended: finished" in log
    assert train_again_returns(cfg, d, a, ha)


def train_again_returns(cfg, d, a, ha) -> bool:
    from f2.train import train

    return train(cfg, 0, d, a, device="cpu")["loss"] == ha["loss"]


def test_elastic_contact_step(dataset):
    """f2/precond.py: the step from the Schur complement is the minimiser of the quadratic model under the contact
    constraints (the reference's sub-solver gives the same), and from the preload state it lowers the energy."""
    from f2.evaluate import clean
    from f2.instance import ExportedProblem
    from f2.precond import ElasticContactStep
    from fejoint.contact import solve_signorini

    cfg, d = dataset
    ex, _ = D.load_export(Path(d) / "inst" / f"{MEMBER}.npz")
    with np.load(Path(d) / "pre" / f"{MEMBER}.npz") as pre:
        z_pre = np.asarray(pre["z"], float)
    with np.load(Path(d) / "labels" / f"{MEMBER}.npz") as lab:
        Theta, Pi_ref = float(lab["Theta"][-1]), float(lab["Pi"][-1])
    E = ElasticContactStep(ex, z_pre)
    P = ExportedProblem(ex)
    z = z_pre.copy(); z[P.prob.cidx] = np.maximum(z[P.prob.cidx], 0.0)
    clean(P); P.loading.delta[:] = -Theta
    E0, g, _, _ = P.prob.evaluate(z, "hencky", tangent=False)
    step, held, its = E.step(z, g)
    assert its < 100 and not step[P.prob.fixed].any() and (z[P.prob.cidx] + step[P.prob.cidx] >= -1e-12).all()
    clean(P); P.loading.delta[:] = 0.0
    _, _, K0, _ = P.prob.evaluate(z_pre, "hencky", tangent=True)
    free = P.prob.free
    ref = solve_signorini(K0.tocsr()[free][:, free].tocsr(), -g[free], P.prob.c_free, g=z[P.prob.cidx])
    assert np.abs(step[free] - ref["x"]).max() <= 1e-8 * np.abs(ref["x"]).max()
    zt = z + step; zt[P.prob.cidx] = np.maximum(zt[P.prob.cidx], 0.0)
    clean(P); P.loading.delta[:] = -Theta
    E1 = P.prob.evaluate(zt, "hencky", tangent=False)[0]
    assert Pi_ref <= E1 * (1 + 1e-9) and (E1 - Pi_ref) < 0.5 * (E0 - Pi_ref)     # more than half of the excess gone


@needs_repo
def test_step_losses_and_starting_weights(dataset, runs, tmp_path):
    """The losses built on the elastic contact step train without a reference, a run can start from another run's
    weights, and 0 among the snapshot epochs gives a snapshot before the first step."""
    torch = torch_or_skip()
    import copy
    from f2.train import train

    cfg, d, a = runs[0], runs[1], runs[2]
    for kind, level, on in (("elastic_contact_step", None, None), ("energy_and_step", None, None),
                            ("energy_and_contact_step", None, None), ("elastic_solution", None, None),
                            ("energy_and_elastic", 1.0, None), ("energy_and_elastic", 1.0, "contact"),
                            ("energy_and_elastic", 0.0, None)):
        c = copy.deepcopy(cfg)
        c["training"]["loss_kind"] = kind
        c["training"]["step_weight"] = 0.1
        if level is not None:
            c["training"]["anchor_max_level"] = level              # 1: every field is anchored; 0: none is
        if on is not None:
            c["training"]["anchor_on"] = on
        c["arms"]["label_free"]["loss"] = kind
        h = train(c, 0, d, tmp_path / f"{kind}_{level}_{on}", device="cpu")
        assert h["status"] == "finished" and len(h["loss"]) == 3 and all(np.isfinite(h["loss"]))
    assert devconfig.config("cpu_frame_gaps_w10")["training"]["anchor_on"] == "contact"
    assert "anchor_on" not in devconfig.config("cpu_frame_anchor_w1")["training"]
    assert devconfig.config("fam128_bending_ft_lr1e4")["training"]["lr"] == 1e-4
    assert devconfig.config("cpu_frame_energy_lr1e4")["training"]["lr"] == 1e-4
    assert devconfig.config("tfam128_frame")["training"]["lr"] == 1e-3
    assert "loss_kind" not in devconfig.config("tfam128_frame")["training"]
    c = copy.deepcopy(cfg)
    c["training"]["snapshot_epochs"] = [0, 3]
    state = a / "label_free_s0" / "state.pt"
    h = train(c, 0, d, tmp_path / "from", device="cpu", init_from=state)
    assert h["status"] == "finished" and h["init_from"]["step"] == 6 and h["snapshots"] == [0, 3]
    snaps = json.loads((tmp_path / "from" / "label_free_s0" / "snapshots.json").read_text())
    done = json.loads((a / "label_free_s0" / "snapshots.json").read_text())
    assert snaps["0"][MEMBER]["theta"] == pytest.approx(done["3"][MEMBER]["theta"], rel=1e-5)   # the same weights
    fresh = train(c, 0, d, tmp_path / "fresh", device="cpu")
    assert fresh["snapshots"] == [0, 3] and "init_from" not in fresh
    assert torch.isfinite(torch.tensor(fresh["loss"])).all()


def test_training_with_a_companion_mesh(dataset, runs, tmp_path):
    """With a companion mesh, every step on a member is followed by steps on members of the companion data; the
    schedule counts them all, the run pauses and resumes, and the data must be those of the companion mesh."""
    torch_or_skip()
    import copy
    from f2.train import train

    cfg, d = runs[0], runs[1]
    c = copy.deepcopy(cfg)
    c["training"]["companion"] = {"mesh": TINY, "steps": 2}        # the same data stand in for the companion mesh
    with pytest.raises(RuntimeError, match="companion"):
        train(c, 0, d, tmp_path / "none", device="cpu")
    h = train(c, 0, d, tmp_path / "mix", device="cpu", companion_dir=d)
    assert h["status"] == "finished" and h["steps"] == 3 * 2 * 3 and h["total_steps"] == 18
    assert len(h["loss"]) == 3 and len(h["companion_loss"]) == 3 and all(np.isfinite(h["companion_loss"]))
    hp = train(c, 0, d, tmp_path / "mix2", device="cpu", companion_dir=d, stop_after_epoch=1)
    assert hp["status"] == "paused"
    hb = train(c, 0, d, tmp_path / "mix2", device="cpu", companion_dir=d)
    assert hb["status"] == "finished" and hb["loss"] == pytest.approx(h["loss"], rel=1e-5)
    assert hb["companion_loss"] == pytest.approx(h["companion_loss"], rel=1e-5)
    wrong = copy.deepcopy(c)
    wrong["training"]["companion"]["mesh"] = "coarse"
    with pytest.raises(RuntimeError, match="another family or data"):
        train(wrong, 0, d, tmp_path / "wrong", device="cpu", companion_dir=d)
    assert devconfig.config("fam128_bending_mix3_lr1e4")["training"]["companion"] == {"mesh": "tiny", "steps": 3}
    assert "companion" not in devconfig.config("tfam128_bending")["training"]


def test_another_configuration_is_refused(runs):
    from f2.train import train

    cfg, d, a, *_ = runs
    other = json.loads(json.dumps(cfg))
    other["training"]["lr"] = 2e-3
    with pytest.raises(RuntimeError, match="another configuration"):
        train(other, 0, d, a, device="cpu")
    other = json.loads(json.dumps(cfg))
    other["data"]["eval_levels"] = [0.5]
    with pytest.raises(RuntimeError, match="another family or data"):
        train(other, 0, d, a, device="cpu")


def test_another_seed_of_the_same_configuration(runs, tmp_path):
    """A seed that the configuration does not list is refused before anything is written, and trained when it is
    asked for: the same configuration and hash, its own run folder."""
    from f2.train import train

    cfg, d, a, b, ha, hb = runs
    with pytest.raises(RuntimeError, match="not in the configuration"):
        train(cfg, 3, d, tmp_path, device="cpu")
    assert not (tmp_path / "label_free_s3").exists()
    h = train(cfg, 3, d, tmp_path, device="cpu", stop_after_epoch=1, other_seed=True)
    assert h["status"] == "paused" and h["seed"] == 3 and h["config_sha256"] == ha["config_sha256"]
    assert len(h["loss"]) == 1 and h["loss"][0] != ha["loss"][0]
    assert (tmp_path / "label_free_s3" / "state.pt").exists()


def test_exact_solution_has_no_error_in_any_order(dataset):
    """The labelled solutions, given as predictions, lie on the reference curve in both rotations, whatever was
    solved before (the evaluation clears the problem's state before every solve)."""
    from f2.evaluate import metrics, clean, path_slope

    cfg, d = dataset
    ex, _ = D.load_export(d / "inst" / f"{MEMBER}.npz")
    ref = D.load_label(d, MEMBER)
    P = I.ExportedProblem(ex)
    slope = path_slope(ref)
    pl = []
    for l in range(2):
        clean(P)
        pl.append(P.evaluate(ref["z"][l], float(ref["Theta"][l]))["plastic"])
    rows = [metrics(P, ex, ref["z"][l], ref, pl[l], l, slope, exact=(l == 0)) for l in (0, 1, 1, 0)]
    for r in rows:
        assert abs(r["curve_err"]) < 1e-9 and abs(r["curveD_err"]) < 1e-9 and r["curve_note"] == ""
        assert r["M_err"] == 0 and r["u_rel_l2"] == 0                 # read from the same field
        # the energy and the bolt forces are computed again from the field: they equal the label's up to rounding
        # (a relative difference of 1.4e-16 in the energy was seen once, in a run on a loaded machine)
        assert abs(r["gap"]) < 1e-12 and r["bolt_err_max"] < 1e-12
        assert r["iou_contact"] == 1 and r["iou_plastic"] == 1 and r["within_bound"]
    assert abs(rows[0]["curveD_exact_err"]) < 1e-8
    for k in ("curve_err", "curveD_err", "M_curve", "ThetaD_curve", "gap"):
        assert rows[0][k] == rows[3][k] and rows[1][k] == rows[2][k]
    # a field off the solution: its moment error stays within the certified bound, and its curve error is finite
    z = ref["z"][1] * 1.02
    r = metrics(P, ex, z, ref, pl[1], 1, slope)
    assert r["gap"] > 0 and r["within_bound"] and np.isfinite(r["curve_err"]) and abs(r["curve_err"]) > 1e-4


def test_evaluation_and_quicklook(runs):
    from f2.evaluate import evaluate, label_summary, quicklook

    cfg, d, a, *_ = runs
    v = evaluate(cfg, d, a)
    assert v["status"] == {"0": "finished"} and sorted(v["rows"]) == ["0|condensed", "0|raw"]
    for key in v["rows"]:
        rows = v["rows"][key]["members"][MEMBER]
        assert len(rows) == 2 and not v["rows"][key]["errors"]
        assert all(np.isfinite(r["M_err"]) and not r["evaluate_failed"] for r in rows)
        assert v["summary"][key]["tested"]["abs_M_err"]["n"] == 2
    assert json.loads((a / "evaluation.json").read_text())["members"] == [MEMBER]
    q = quicklook(label_summary(d), json.loads((a / "label_free_s0" / "snapshots.json").read_text()))
    raw = v["rows"]["0|raw"]["members"][MEMBER]
    assert q["3"]["members"][MEMBER]["M_err"] == pytest.approx([r["M_err"] for r in raw], rel=1e-4, abs=1e-6)
    # other seeds of the same configuration go to their own file and leave evaluation.json as it is
    before = (a / "evaluation.json").read_bytes()
    w = evaluate(cfg, d, a, seeds=[0, 3])
    assert w["seeds"] == [0, 3] and w["status"] == {"0": "finished", "3": "missing"}
    assert sorted(w["rows"]) == ["0|condensed", "0|raw"]
    assert [r["M_err"] for r in w["rows"]["0|raw"]["members"][MEMBER]] == [r["M_err"] for r in raw]
    assert (a / "evaluation_seeds_0_3.json").exists() and (a / "evaluation.json").read_bytes() == before


@needs_repo
def test_averages_of_the_weights(dataset, runs, tmp_path):
    """Exponential moving averages of the weights follow their rule, leave the trained weights as a run without
    them has them, come through a pause, are read at the snapshots, and are predicted and evaluated in run folders
    of their own."""
    torch = torch_or_skip()
    import copy
    from f2.train import train, ema_run, ema_tag, averaged, PREDICTION_FILES
    from f2.evaluate import evaluate

    cfg, d, a, _, ha, _ = runs
    assert ema_tag(0.999) == "999" and ema_tag(0.9998) == "9998" and ema_tag(0.5) == "5"
    with pytest.raises(ValueError):
        ema_tag(1.0)
    plain = copy.deepcopy(cfg)
    plain["training"]["snapshot_epochs"] = [0, 1, 3]
    c = copy.deepcopy(plain)
    c["training"]["ema"] = {"decays": [0.5, 0.9]}
    out0, out, out2 = tmp_path / "plain", tmp_path / "avg", tmp_path / "avg_paused"
    h0 = train(plain, 0, d, out0, device="cpu")
    first, seen = [], []                                        # the weights before the first step and after every step

    def before_step(opt, args, kwargs):
        if not first:
            first.append([p.detach().clone() for g in opt.param_groups for p in g["params"]])

    def after_step(opt, args, kwargs):
        seen.append([p.detach().clone() for g in opt.param_groups for p in g["params"]])

    from torch.optim.optimizer import register_optimizer_step_pre_hook, register_optimizer_step_post_hook

    hooks = [register_optimizer_step_pre_hook(before_step), register_optimizer_step_post_hook(after_step)]
    try:
        h = train(c, 0, d, out, device="cpu")
    finally:
        for hook in hooks:
            hook.remove()
    assert h["status"] == h0["status"] == "finished" and h["steps"] == 6 == len(seen)
    # the averages take no part in training: the run is the run without them, up to the rounding by which two
    # runs of one configuration differ on a processor (about 1e-7 in a weight)
    assert h["loss"] == pytest.approx(h0["loss"], rel=1e-6) and h["loss"] == pytest.approx(ha["loss"], rel=1e-6)
    s0 = torch.load(out0 / "label_free_s0" / "state.pt", map_location="cpu", weights_only=False)
    s = torch.load(out / "label_free_s0" / "state.pt", map_location="cpu", weights_only=False)
    assert "ema" not in s0 and s["ema"]["decays"] == [0.5, 0.9]
    for k in ("enc", "dec", "head"):
        assert all(torch.allclose(s[k][name], s0[k][name], rtol=1e-4, atol=1e-6) for name in s[k])
    # the rule, recomputed from the weights before the first step and after every step
    start = json.loads((out0 / "label_free_s0" / "snapshots.json").read_text())["0"]
    names = [(i, name) for i in range(3) for name in s["ema"]["weights"][0][i]]
    assert len(names) == len(seen[0]) == len(first[0])
    for j, x in enumerate((0.5, 0.9)):
        e = [w.clone() for w in first[0]]
        for step in seen:
            for q in range(len(e)):
                e[q].lerp_(step[q], 1.0 - x)
        got = [s["ema"]["weights"][j][i][name] for i, name in names]
        assert all(torch.allclose(g, v, rtol=1e-5, atol=1e-8) for g, v in zip(got, e))
        assert max(float((g - w).abs().max()) for g, w in zip(got, seen[-1])) > 1e-4     # an average is not the weights
    # the files of each average
    snaps = json.loads((out / "label_free_s0" / "snapshots.json").read_text())
    assert snaps["0"] == start and sorted(snaps) == ["0", "1", "3"]
    for x in (0.5, 0.9):
        re = ema_run(out, x, "label_free", 0)
        assert re == tmp_path / ("avg_ema" + ema_tag(x)) / "label_free_s0"
        assert all((re / name).exists() for name in PREDICTION_FILES + ("history.json", "progress.json", "average.json"))
        es = json.loads((re / "snapshots.json").read_text())
        assert sorted(es) == ["0", "1", "3"] and es["0"] == snaps["0"] and es["3"] != snaps["3"]
        he = json.loads((re / "history.json").read_text())
        assert he["status"] == "finished" and he["weights"]["decay"] == x and he["config_sha256"] == h["config_sha256"]
        with np.load(re / "preds.npz") as za, np.load(out / "label_free_s0" / "preds.npz") as zb:
            assert za.files == zb.files == [MEMBER] and not np.allclose(za[MEMBER], zb[MEMBER], rtol=1e-9, atol=0.0)
    # the evaluation reads an average's folder as it reads a run
    v = evaluate(c, d, ema_run(out, 0.9, "label_free", 0).parent)
    assert v["status"] == {"0": "finished"} and sorted(v["rows"]) == ["0|condensed", "0|raw"]
    assert all(np.isfinite(r["M_err"]) for r in v["rows"]["0|raw"]["members"][MEMBER])
    # a pause: the averages come back from the checkpoint
    hp = train(c, 0, d, out2, device="cpu", stop_after_epoch=2)
    assert hp["status"] == "paused"
    sp = torch.load(out2 / "label_free_s0" / "state.pt", map_location="cpu", weights_only=False)
    assert sp["epoch"] == 2 and sp["ema"]["decays"] == [0.5, 0.9]
    h2 = train(c, 0, d, out2, device="cpu")
    assert h2["status"] == "finished" and h2["resumes"] == [2]
    s2 = torch.load(out2 / "label_free_s0" / "state.pt", map_location="cpu", weights_only=False)
    for j in range(2):
        for i, name in names:
            assert torch.allclose(s2["ema"]["weights"][j][i][name], s["ema"]["weights"][j][i][name], rtol=1e-4, atol=1e-6)
    for x in (0.5, 0.9):
        with np.load(ema_run(out2, x, "label_free", 0) / "preds.npz") as za, np.load(ema_run(out, x, "label_free", 0) / "preds.npz") as zb:
            assert np.allclose(za[MEMBER], zb[MEMBER], rtol=1e-4, atol=1e-7)
    # a finished run whose averages were not predicted yet predicts them when it is run again
    gone = ema_run(out, 0.5, "label_free", 0)
    for name in PREDICTION_FILES:
        (gone / name).unlink()
    h3 = train(c, 0, d, out, device="cpu")
    assert h3["status"] == "finished" and all((gone / name).exists() for name in PREDICTION_FILES)
    # another configuration (other decays) is refused in the same folder
    c2 = copy.deepcopy(c)
    c2["training"]["ema"] = {"decays": [0.5, 0.99]}
    with pytest.raises(RuntimeError):
        train(c2, 0, d, out, device="cpu")
    # the networks keep their own weights after a reading with averaged ones
    from f2.train import build_item
    from f2.model import build
    it = build_item(d, "train_0000", torch.device("cpu"), c["model"]["lift"])
    nets = build(c, it["base"].shape[-1] + 1, it["maps"]["nb"])
    own = [p.detach().clone() for net in nets for p in net.parameters()]
    with averaged(nets, [{k: torch.zeros_like(p) for k, p in net.named_parameters()} for net in nets]):
        assert all(float(p.abs().sum()) == 0.0 for net in nets for p in net.parameters())
    assert all(torch.equal(p, o) for p, o in zip([p for net in nets for p in net.parameters()], own))


def test_rotation_sampling_kinds():
    """The default draw is the draw of every run before 24 November 2026, number for number; the uniform kind fills
    its range, and a top above 1 reaches beyond the device range in both kinds."""
    from f2.model import sample_Theta, LAM_MIN

    Tm = 0.0235
    a, b = np.random.default_rng(5), np.random.default_rng(5)
    legacy = a.uniform(np.sqrt(LAM_MIN * Tm), np.sqrt(Tm), size=4) ** 2
    assert np.array_equal(legacy, sample_Theta(b, Tm, 4))
    u = sample_Theta(np.random.default_rng(1), Tm, 20000, kind="uniform", top=1.15)
    assert LAM_MIN * Tm <= u.min() and u.max() <= 1.15 * Tm and (u > Tm).any()
    assert abs(u.mean() / Tm - (LAM_MIN + 1.15) / 2) < 0.01
    s = sample_Theta(np.random.default_rng(1), Tm, 20000, top=1.15)
    assert LAM_MIN * Tm <= s.min() and s.max() <= 1.15 * Tm and (s > Tm).any() and s.mean() < u.mean()
    with pytest.raises(AssertionError):
        sample_Theta(np.random.default_rng(1), Tm, 2, kind="other")


# configuration hashes of code package f2dev_2026-11-22a (the runs of 21 and 22 November 2026 carry them)
PINS_22A = {
    "fam128_bending_e400": "de8f4d173097aec0aec9bffac24efadabb75229acdf9c9f40055845dc4ca6a07",
    "fam128_bending_more": "f2eced7a4990b1934783dd6d2ce05cbd4eafc6dcf757b23e3f856bf8ebd64c2a",
    "tfam128_bending": "dce1f4026f98659db993137fff72512c5bc11fc6611d68c028e2eaf8338cc999",
    "tfam128_bending_more": "8791c5663fffd86662b1c648247aab673037e356448cf7c1160704991c23c62a",
    "dry": "a1aad4cb7ba1dae96fbe1927ec1a8e4716b7bfc6cc6b599151a1ec36994c7b85",
    "dry_more": "d8e77c3789d04dff4bb1a2179c50297aac77147ce56bdabd0012eef4f4e6aa4e",
}
DATA_22A = "e46121c6a55482296dcd2a0e3ec62b1e63ec364cad7d9fea206e78df1615b71e"


def test_the_stage_two_trial_leaves_earlier_configurations_and_changes_only_what_it_says():
    """The presets that existed on 22 November 2026 keep their configuration hashes, and every preset keeps the
    data hash, so the runs made then are read, resumed and compared as before. The two presets of the trial differ
    from the second cycle they are compared with only in the averages, the draw of the rotations and, for "ux", the
    extra members with their epochs; all three make 25,600 steps."""
    for p, h in PINS_22A.items():
        assert devconfig.sha256(devconfig.config(p)) == h, p
    assert all(D.data_sha256(devconfig.config(p)) == DATA_22A for p in devconfig.PRESETS)
    base, u, ux = (devconfig.config(p) for p in ("fam128_bending_more", "fam128_bending_more_u",
                                                 "fam128_bending_more_ux"))

    def rest(cfg, drop):
        out = {k: v for k, v in cfg.items() if k not in ("training", "preset", "arms")}
        out["training"] = {k: v for k, v in cfg["training"].items() if k not in drop}
        return out

    assert rest(base, ("ema", "Theta_sampling")) == rest(u, ("Theta_kind", "Theta_top", "Theta_sampling"))
    assert base["arms"] == u["arms"] and "ema" not in u["training"] and "ema" not in ux["training"]
    assert (u["training"]["Theta_kind"], u["training"]["Theta_top"]) == ("uniform", 1.15)
    moved = ("resident_members", "snapshot_epochs", "extra_members")
    assert rest(u, moved) == rest(ux, moved)
    steps = [c["arms"]["label_free"]["epochs"] * n for c, n in ((base, 128), (u, 128), (ux, 128 + 32))]
    assert steps == [25600, 25600, 25600]
    assert [e * 160 for e in ux["training"]["snapshot_epochs"]] == [e * 128 for e in u["training"]["snapshot_epochs"]]


def test_extra_training_members():
    """The extra members of a preset: drawn with their own seed inside the family, in the given part of the ranges,
    with names and a data hash of their own; the preset's own members and data hash are untouched."""
    from f2.family import RANGES, sample, violations

    c = devconfig.config("fam128_bending_more_ux")
    assert D.extra_config(devconfig.config("fam128_bending_more")) is None
    x = D.extra_config(c)
    m = D.members(x)
    assert [i for i, _, _ in m] == [f"trainx_{k:04d}" for k in range(32)] and {s for _, s, _ in m} == {"train"}
    assert all(10.0 <= q.tp <= 12.5 for _, _, q in m) and not any(violations(q) for _, _, q in m)
    assert all(RANGES[k][0] <= getattr(q, k) <= RANGES[k][1] for _, _, q in m for k in RANGES)
    assert m == D.members(D.extra_config(devconfig.config("fam128_bending_more_ux")))
    assert D.data_sha256(x) != D.data_sha256(c) == DATA_22A
    mine = D.members(c)
    assert len(mine) == devconfig.N_TRAIN + devconfig.N_EVAL + len(devconfig.DEV_MEMBERS) + len(TESTED)
    assert not {i for i, _, _ in mine} & {i for i, _, _ in m}
    assert not {tuple(sorted(vars(q).items())) for _, _, q in mine} & {tuple(sorted(vars(q).items())) for _, _, q in m}
    assert devconfig.EXTRA_SEED not in (devconfig.TRAIN_SEED, devconfig.EVAL_SEED)
    assert devconfig.EXTRA_SEED not in c["data"]["seeds_seen_before_stamp"]
    with pytest.raises(ValueError):
        sample(1, 3, ranges={"tp": (9.0, 12.0)})
    twice = D.members(D.extra_config(devconfig.config("dry_more_ux")))
    assert [i for i, _, _ in twice] == ["trainx_0000", "trainx_0001"] and [q for _, _, q in twice] == [q for _, _, q in m[:2]]


@needs_repo
def test_second_cycle_with_uniform_rotations_and_extra_members(dataset, runs, tmp_path, monkeypatch):
    """A second cycle from another run's weights, with the device rotation drawn uniformly beyond the device range
    and with extra training members from a data directory of their own: the extra data are asked for and checked,
    the run trains on all members, pauses and resumes, and is evaluated on the data of the preset."""
    torch_or_skip()
    import copy
    import f2.train as T
    from f2.evaluate import evaluate

    cfg, d, a, _, ha, _ = runs
    start = a / "label_free_s0" / "state.pt"
    c = copy.deepcopy(cfg)
    c["training"].update(Theta_kind="uniform", Theta_top=1.15, snapshot_epochs=[0, 1, 3], lr=3e-4,
                         extra_members={"n": 2, "seed": devconfig.EXTRA_SEED, "prefix": "trainx",
                                        "ranges": {"tp": [10.0, 12.5]}})
    with pytest.raises(RuntimeError, match="extra members"):
        T.train(c, 0, d, tmp_path / "none", device="cpu", init_from=start)
    x = D.extra_config(c)
    dx = tmp_path / "extra"
    D.generate(x, dx, splits=("train",))
    man = D.manifest(dx)
    assert [r["id"] for r in man["instances"]] == ["trainx_0000", "trainx_0001"]
    assert man["config_sha256"] == D.data_sha256(x) != D.manifest(d)["config_sha256"]
    assert all(10.0 <= r["params"]["tp"] <= 12.5 for r in man["instances"])
    with pytest.raises(RuntimeError, match="another family or data configuration"):
        T.train(c, 0, d, tmp_path / "wrong", device="cpu", init_from=start, extra_dir=d)
    seen = []
    draw = T.sample_Theta

    def recording(rng, Theta_max, B, lam_min, kind="sqrt", top=1.0):
        out = draw(rng, Theta_max, B, lam_min, kind=kind, top=top)
        seen.append((kind, top, float(out.max() / Theta_max)))
        return out

    monkeypatch.setattr(T, "sample_Theta", recording)
    out, out2 = tmp_path / "straight", tmp_path / "paused"
    h = T.train(c, 0, d, out, device="cpu", init_from=start, extra_dir=dx)
    assert h["status"] == "finished" and h["steps"] == h["total_steps"] == 3 * 4
    assert h["members"] == ["train_0000", "train_0001", "trainx_0000", "trainx_0001"]
    assert h["extra_data_sha256"] == D.data_sha256(x) and h["init_from"]["preset"] == "dry"
    assert len(seen) == 12 and {(k, t) for k, t, _ in seen} == {("uniform", 1.15)}
    assert max(r for *_, r in seen) > 1.0 and all(r <= 1.15 * (1 + 1e-6) for *_, r in seen)
    hp = T.train(c, 0, d, out2, device="cpu", init_from=start, extra_dir=dx, stop_after_epoch=2)
    assert hp["status"] == "paused"
    h2 = T.train(c, 0, d, out2, device="cpu", extra_dir=dx)
    assert h2["status"] == "finished" and h2["resumes"] == [2] and h2["loss"] == pytest.approx(h["loss"], rel=1e-6)
    snaps = json.loads((out / "label_free_s0" / "snapshots.json").read_text())
    assert sorted(snaps) == ["0", "1", "3"] and list(snaps["0"]) == [MEMBER]
    v = evaluate(c, d, out)
    assert v["status"] == {"0": "finished"} and sorted(v["rows"]) == ["0|condensed", "0|raw"]
    assert all(np.isfinite(r["M_err"]) for key in v["rows"] for r in v["rows"][key]["members"][MEMBER])
    # the run before the trial is untouched by it: the same configuration trains to the same losses
    monkeypatch.setattr(T, "sample_Theta", draw)
    assert train_again_returns(cfg, d, a, ha)


# ---- a field underneath (25 November 2026): f2/prolong.py, f2.model.field(under=), train --under-data --under-state

@pytest.fixture(scope="module")
def plain(tmp_path_factory):
    """Four members of the preset "dry" on the tiny mesh under the preset's own configuration (a run with a field
    underneath looks the coarser run's configuration up by the preset's name), and a finished "dry" run on them."""
    torch_or_skip()
    from f2.train import train

    cfg = devconfig.config("dry")
    cfg["data"]["mesh"] = TINY
    d = tmp_path_factory.mktemp("f2under")
    D.generate(cfg, d, only=["train_0000", "train_0001", "eval_0000", MEMBER])
    runs = tmp_path_factory.mktemp("f2under_runs")
    h = train(cfg, 0, d, runs / "dry", device="cpu")
    assert h["status"] == "finished"
    return cfg, d, runs


def test_transfer_of_a_mesh_onto_itself_is_the_identity(bare):
    from f2.prolong import prolongation, interpolation, check

    q, ex = bare
    A, info = prolongation(ex, ex)
    n = ex["nodes"].shape[0]
    assert info["at_a_source_node"] == n and info["continued_beyond_an_element"] == 0
    assert info["projected_onto_an_element"] == 0
    fixed = np.asarray(ex["fixed"], bool)
    z = np.random.default_rng(0).standard_normal(A.shape[1])
    z[fixed] = 0.0
    assert np.array_equal((A @ z)[~fixed], z[~fixed])
    assert check(ex, ex, A)["largest_difference_free"] == 0.0
    P, _ = interpolation(ex, ex)
    hanging = np.asarray(ex["node_flags"])[:, I.FLAGS.index("hanging")].astype(bool)
    u = np.random.default_rng(1).standard_normal(3 * n)
    assert np.array_equal((P @ u).reshape(n, 3)[~hanging], u.reshape(n, 3)[~hanging])


def test_transfer_from_the_tiny_to_the_family_mesh(bare):
    """B-13 without its preload: the family's mesh takes the tiny mesh's displacements at its nodes. A linear
    displacement is reproduced at every node but the few that are projected (beyond the fillet's sloping face), the
    free unknowns' own displacements are the interpolated ones, and the report stays within what was seen on
    25 November 2026 (the two meshes shape the bolt holes differently: nodes of the family's mesh lie up to one
    element beyond the tiny mesh there)."""
    from f2.prolong import prolongation, interpolation, check

    q, ex_t = bare
    k_th, Tm = loading(q)
    ex_f = I.export(I.build(q, "coarse"), q, k_th, 0.0)
    A, info = prolongation(ex_t, ex_f)
    assert A.shape == (int(ex_f["v"].size), int(ex_t["v"].size))
    assert info["projected_onto_an_element"] <= 12 and info["largest_projection_distance_mm"] < 2.0
    assert info["largest_excess"] < 1.1 and -0.6 < info["smallest_weight"] and info["largest_weight"] < 1.6
    assert info["at_a_source_node"] > 1000
    c = check(ex_t, ex_f, A)
    assert c["largest_difference_free"] < 1e-10 * c["scale"]
    P, _ = interpolation(ex_t, ex_f)
    ns, nt = np.asarray(ex_t["nodes"], float), np.asarray(ex_f["nodes"], float)
    B = np.random.default_rng(2).standard_normal((3, 3))
    err = np.abs(P @ (0.3 + ns @ B.T).ravel() - (0.3 + nt @ B.T).ravel()).reshape(-1, 3).max(axis=1)
    assert (err > 1e-8).sum() == info["projected_onto_an_element"]
    assert np.allclose(np.asarray(P.sum(axis=1)).ravel(), 1.0)


def test_points_are_found_in_a_distorted_element():
    """The local coordinates of points in and just outside one distorted hexahedron, and of a point beyond a face
    with two edges in line (the fillet's section), which takes the nearest point of the element."""
    from f2.prolong import locate, _shape, EXTEND
    from fejoint.hex8i import XI

    rng = np.random.default_rng(0)
    X = XI * np.array([3.0, 2.0, 1.0]) + 0.3 * rng.standard_normal((8, 3))
    xi = rng.uniform(-1.2, 1.2, size=(50, 3))
    pts = _shape(xi)[0] @ X
    e, x, over, dist = locate(X, np.arange(8)[None], pts)
    assert np.abs(x - xi).max() < 1e-9 and (dist == 0).all()
    assert np.allclose(over, np.maximum(np.abs(xi).max(axis=1) - 1.0, 0.0), atol=1e-9) and over.max() <= EXTEND
    # a section with corners (0,0), (8,0), (4,4), (0,8): the third lies on the line from the second to the fourth
    S = np.array([[0.0, 0.0], [8.0, 0.0], [4.0, 4.0], [0.0, 8.0]])
    Xf = np.array([[a, b, c] for c in (0.0, 5.0) for a, b in S])
    p = np.array([[6.0 + 0.3, 2.0 + 0.3, 2.5]])                 # 0.42 beyond the sloping face
    e, x, over, dist = locate(Xf, np.arange(8)[None], p)
    assert over[0] == 0.0 and abs(dist[0] - 0.3 * np.sqrt(2.0)) < 1e-6 and np.abs(x).max() <= 1.0 + 1e-12


def test_field_underneath_is_where_the_networks_start(plain):
    torch = torch_or_skip()
    from f2 import train as T
    from f2.model import build, field, UNDER_FLOOR, L_REF
    from f2.data import load_export

    cfg, d, runs = plain
    s = torch.load(runs / "dry" / "label_free_s0" / "state.pt", map_location="cpu", weights_only=False)
    exu, qu = load_export(d / "inst" / f"{MEMBER}.npz")
    nets_u = build(cfg, features(exu, qu).shape[-1] + 1, int(np.asarray(exu["head"]).size))
    for net, k in zip(nets_u, ("enc", "dec", "head")):
        net.load_state_dict(s[k])
        net.eval()
    under = {"dir": str(d), "nets": nets_u, "lift": cfg["model"]["lift"], "T": cfg["map"]["T"], "gate": cfg["map"]["kind"]}
    it = T.build_item(d, MEMBER, torch.device("cpu"), "bending", under=under)
    mp = it["maps"]
    assert float(it["under"]["shift"].abs().max()) == 0.0        # the same mesh: no change of the preload state
    Theta = torch.tensor([0.1, 0.5, 1.0]) * mp["Theta_max"]
    with torch.no_grad():
        own = field(*nets_u, it["base"], mp, Theta, cfg["map"]["T"], gate=cfg["map"]["kind"])
        own = torch.where(mp["nonneg"], own.clamp_min(0.0), own)
        z0 = T.under_field(under, it, Theta)
    assert torch.allclose(z0, own, rtol=0.0, atol=1e-6 * float(own.abs().max()))
    c = devconfig.config("dry_under")
    torch.manual_seed(0)
    nets = build(c, it["base"].shape[-1] + 1, mp["nb"])
    with torch.no_grad():
        z = T.predicted(c, nets, it, Theta, under)
    floor = UNDER_FLOOR * c["map"]["T"] * (L_REF * Theta + mp["delta"])[:, None]
    assert torch.equal(z[:, ~mp["nonneg"]], z0[:, ~mp["nonneg"]])
    want = torch.maximum(z0, floor.expand_as(z0))[:, mp["nonneg"]]
    assert torch.allclose(z[:, mp["nonneg"]], want, rtol=1e-4, atol=1e-9)
    loss, _ = T.step_loss(c, nets, it, np.random.default_rng(0), torch.device("cpu"), under)
    loss.backward()
    assert torch.isfinite(loss) and float(nets[1][-1].weight.grad.abs().max()) > 0
    assert all(not p.requires_grad or p.grad is None for net in nets_u for p in net.parameters())


def test_training_on_a_field_underneath(plain, tmp_path):
    torch_or_skip()
    from f2.train import train, predictions_written

    cfg, d, runs = plain
    state = runs / "dry" / "label_free_s0" / "state.pt"
    c = devconfig.config("dry_under")
    c["data"]["mesh"] = TINY
    with pytest.raises(RuntimeError, match="field underneath"):
        train(c, 0, d, tmp_path / "none", device="cpu")
    h = train(c, 0, d, tmp_path / "a", device="cpu", under_dir=d, under_state=state)
    run = tmp_path / "a" / "label_free_s0"
    assert h["status"] == "finished" and predictions_written(run)
    assert h["under"]["sha256"] == hashlib.sha256(state.read_bytes()).hexdigest()
    assert h["under"]["preset"] == "dry" and h["under"]["mesh"] == TINY and h["under"]["epoch"] == 3
    assert h["under_transfer_of_first_member"]["projected_onto_an_element"] == 0
    snaps = json.loads((run / "snapshots.json").read_text())
    assert set(snaps) == {"0", "1", "3"} and set(snaps["0"]) == {"eval_0000", MEMBER}
    hp = train(c, 0, d, tmp_path / "b", device="cpu", under_dir=d, under_state=state, stop_after_epoch=1)
    assert hp["status"] == "paused"
    hb = train(c, 0, d, tmp_path / "b", device="cpu", under_dir=d, under_state=state)
    assert hb["status"] == "finished" and hb["loss"] == h["loss"]
    # the state of a run of another configuration is refused; so is another state of the right one at a resume
    with pytest.raises(RuntimeError, match="not a run of the configured preset"):
        train(c, 0, d, tmp_path / "wrong", device="cpu", under_dir=d, under_state=run / "state.pt")
    other = train(cfg, 3, d, runs / "dry", device="cpu", other_seed=True)
    assert other["status"] == "finished"
    hq = train(c, 0, d, tmp_path / "q", device="cpu", under_dir=d, under_state=state, stop_after_epoch=1)
    assert hq["status"] == "paused"
    with pytest.raises(RuntimeError, match="another state underneath"):
        train(c, 0, d, tmp_path / "q", device="cpu", under_dir=d, under_state=runs / "dry" / "label_free_s3" / "state.pt")


def test_the_field_underneath_leaves_earlier_configurations():
    """The presets without a field underneath have no entry for it, and the two with one name a preset and a mesh."""
    with_under = {k for k in devconfig.PRESETS if "under" in devconfig.config(k)["model"]}
    assert with_under == {"fam128_bending_under_e150", "dry_under"}
    a, b = devconfig.config("fam128_bending_under_e150"), devconfig.config("fam128_bending_e400")
    assert a["model"]["under"]["preset"] == "fam128_bending_e400" and a["model"]["under"]["mesh"] == "tiny"
    assert a["arms"]["label_free"]["epochs"] == 150 and 0 in a["training"]["snapshot_epochs"]
    drop = lambda c: {k: v for k, v in c["training"].items() if k != "snapshot_epochs"}  # noqa: E731
    assert drop(a) == drop(b) and a["map"] == b["map"] and D.data_sha256(a) == D.data_sha256(b)
    assert {k: v for k, v in a["model"].items() if k != "under"} == b["model"]
