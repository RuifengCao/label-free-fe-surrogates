"""Checks of the CHS surrogate family's code (f2, draft): the family, the spring-loaded export against rotation
control, the preload, the moment bound, the stress reading, and the torch energy against the numpy reference.
The tiny mesh of fejoint.chs keeps the suite short; no member is drawn with a seed of the gate."""
import numpy as np
import pytest

from fejoint import chs
from fejoint.plasticity import Material
from f1.config import PLATES
from f1.materials import material as f1_material
from f2.family import (Params, RANGES, TESTED, sample, violations, plate_material, materials, bolt_curve,
                       geometry, BOLT_REG)
from f2 import instance as I

TINY = "tiny"
DEV_SEEDS = (11, 12)        # seeds for the tests only


def torch_or_skip():
    return pytest.importorskip("torch")


@pytest.fixture(scope="module")
def member():
    q = Params(**TESTED["B-13_nominal"])
    ex, pre = I.make(q, mesh=TINY, k_th=4e9)
    return q, ex, pre


def test_family_is_deterministic_and_valid():
    a, na = sample(5, DEV_SEEDS[0])
    b, nb = sample(5, DEV_SEEDS[0])
    assert a == b and na == nb
    for q in a:
        for k, (lo, hi) in RANGES.items():
            assert lo <= getattr(q, k) <= hi
    corners = [Params(**{k: RANGES[k][i % 2] for k in RANGES}) for i in range(2)]
    for q in corners + [Params(**p) for p in TESTED.values()]:
        assert not violations(q)


def test_plate_law_is_the_gate_s_scaled():
    """At fy = 397 MPa the plate law is gate G-F1's 12.7 mm plate law; elsewhere every stress scales by fy / 397."""
    ref = f1_material(PLATES["12.7"], "hencky")
    m397, m460 = plate_material(397.0), plate_material(460.0)
    assert m397.E == ref.E == 201000.0 and m397.nu == ref.nu
    assert np.array_equal(m397.hardening.alpha, ref.hardening.alpha)
    assert np.allclose(m397.hardening.sigma, ref.hardening.sigma, rtol=0, atol=1e-12)
    assert np.allclose(m460.hardening.sigma, ref.hardening.sigma * 460 / 397, rtol=1e-14)
    assert m460.hardening.h_end == pytest.approx(ref.hardening.h_end * 460 / 397, rel=1e-14)
    mats = materials(Params(**TESTED["B-13_nominal"]))
    assert mats[1] is mats[2]                                    # the weld has the tube's law


def test_bolt_law_continuous_and_regularised():
    g = geometry(Params(**TESTED["B-13_nominal"]))
    e, N, h = bolt_curve(g)
    k_ax = g.E_b * g.As / (g.L_b / 2)
    assert N[0] == pytest.approx(k_ax * e[0], rel=1e-12)        # yield on the elastic line
    assert np.all(np.diff(e) > 0) and np.all(np.diff(N) >= 0)
    assert h == pytest.approx(BOLT_REG * k_ax, rel=1e-12)


def test_preload_is_uniform_and_on_target(member):
    q, ex, pre = member
    N = np.array(pre["forces_N"])
    assert pre["converged"] and pre["on_target"]
    assert abs(N.mean() / (q.Np * 1e3) - 1) < 1e-10
    assert np.abs(N / N.mean() - 1).max() < 1e-5                 # mesh round-off only
    assert np.allclose(ex["delta"], pre["delta"]) and pre["plastic_points"] == [0, 0, 0, 0]
    P = I.ExportedProblem(ex)
    r = P.solve(0.0)
    assert abs(r["M"]) < 1e-6 * 1e6 and abs(r["ThetaD"]) < 1e-9   # the preload state is the reading's origin


def test_spring_loaded_export_equals_rotation_control(member):
    """The state at a device rotation is the state of rotation control at the end rotation it reaches; the moment
    of the spring, of the reaction and of the stresses agree."""
    q, ex, pre = member
    P = I.ExportedProblem(ex)
    r = P.solve(0.01)
    assert r["converged"] and 0 < r["theta"] < 0.01
    assert abs(r["M_sigma"] / r["M"] - 1) <= 1e-8
    rt = P.solve_at_theta(r["theta"])
    assert rt["converged"] and abs(rt["M"] / r["M"] - 1) <= 1e-8
    assert np.abs(rt["z"] - r["z"]).max() <= 1e-8 * np.abs(r["z"]).max()
    assert abs(rt["ThetaD"] - r["ThetaD"]) <= 1e-9 * abs(r["ThetaD"])


def test_spring_loaded_export_equals_the_gate_s_model(member):
    """fejoint.chs.SpliceModel with the same laws, bolts and preload gives the same moment at the same rotation."""
    q, ex, pre = member
    g = geometry(q)
    m = chs.SpliceModel(g, TINY, mats=materials(q), bolt_curve=bolt_curve(g))
    m.delta = np.asarray(ex["delta"], float).copy()
    z0, rep0 = m.solve(0.0, z0=np.zeros(m.nfull), tol=1e-12, max_it=80)
    ref0 = m.readings(z0, rep0)
    z, rep = m.solve(0.003, tol=1e-12, max_it=80)
    rm = m.readings(z, rep)
    rt = I.ExportedProblem(ex).solve_at_theta(0.003)
    assert abs(rm["M_kNm"] * 1e6 / rt["M"] - 1) <= 1e-8
    assert abs((rm["Theta_D"] - ref0["Theta_D"]) / rt["ThetaD"] - 1) <= 1e-8
    assert np.allclose(np.array(rm["bolt_force_kN"]) * 1e3, rt["bolt_N"], rtol=1e-8)


def test_moment_reading_bound(member):
    """|M(z) - M*| <= 2 sqrt(2 k_th (Pi(z) - Pi*)) for feasible fields z near and far from the solution."""
    q, ex, pre = member
    P = I.ExportedProblem(ex)
    r = P.solve(0.008)
    rng = np.random.default_rng(2)
    for amp in (1e-3, 1e-2, 1e-1):
        z = np.where(P.prob.fixed, 0.0, r["z"] * (1 + amp * rng.normal(size=r["z"].size)))
        z[P.prob.cidx] = np.maximum(z[P.prob.cidx], 0.0)
        e = P.evaluate(z, 0.008)
        assert e["Pi"] >= r["Pi"] - 1e-9 * abs(r["Pi"])
        assert abs(e["M"] - r["M"]) <= 2.0 * np.sqrt(2.0 * P.k_th * max(e["Pi"] - r["Pi"], 0.0)) * (1 + 1e-9)


def test_no_slip_is_stiffer():
    q = Params(**TESTED["B-13_nominal"])
    out = {}
    for sp in ("frictionless", "no-slip"):
        ex, pre = I.make(q, mesh=TINY, splice=sp, k_th=4e9)
        out[sp] = I.ExportedProblem(ex).solve_at_theta(0.002)
        assert out[sp]["converged"]
    assert out["no-slip"]["M"] > out["frictionless"]["M"]


def test_torch_energy_and_gradient_equal_the_reference(member):
    torch = torch_or_skip()
    from f2.torch_energy import InstanceEnergy
    q, ex, pre = member
    P = I.ExportedProblem(ex)
    Th = 0.012
    r = P.solve(Th)
    rng = np.random.default_rng(4)
    Z = np.stack([r["z"], np.where(P.prob.fixed, 0.0, r["z"] * (1 + 0.1 * rng.normal(size=r["z"].size)))])
    Z[:, P.prob.cidx] = np.maximum(Z[:, P.prob.cidx], 0.0)
    zt = torch.tensor(Z, requires_grad=True)
    Tt = torch.tensor([Th, Th], dtype=torch.float64)
    Et = InstanceEnergy(ex, dtype=torch.float64).energy(zt, Tt, iters=30)
    Et.sum().backward()
    free = ~P.prob.fixed
    P.loading.delta[:] = -Th
    for b in range(2):
        Pi, g = P.prob.evaluate(Z[b], "hencky", tangent=False)[:2]
        assert abs(float(Et[b].detach()) / Pi - 1) <= 1e-12
        assert np.max(np.abs(zt.grad[b].numpy()[free] - g[free])) <= 1e-9 * np.abs(g[free]).max()
    E32 = InstanceEnergy(ex).energy(torch.tensor(Z[:1], dtype=torch.float32), torch.tensor([Th]), iters=10)
    assert abs(float(E32[0]) / r["Pi"] - 1) <= 1e-5


# ---- the data pipeline ---------------------------------------------------------------------------------------------
def small_cfg():
    import copy
    from f2.config import config
    cfg = copy.deepcopy(config())
    d = cfg["data"]
    d["n_train"], d["n_eval"] = 1, 1
    d["train_seed"], d["eval_seed"] = DEV_SEEDS
    d["seeds_seen_before_stamp"] = []
    d["mesh"] = TINY
    d["eval_levels"], d["train_label_levels"] = [0.25, 1.0], [0.5]
    d["n_train_labelled"] = 1
    d["tested"] = {"B-13_nominal": dict(TESTED["B-13_nominal"])}
    return cfg


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    from f2 import data
    cfg = small_cfg()
    root = tmp_path_factory.mktemp("f2data")
    data.generate(cfg, root)
    data.label(cfg, root, data.labelled_ids(cfg, root))
    return cfg, root


def test_generate_label_and_check(dataset):
    from f2 import data
    cfg, root = dataset
    r = data.check_labels(cfg, root)
    assert r["ok"], r
    man = data.manifest(root)
    assert [x["split"] for x in man["instances"]] == ["train", "eval", "tested"]
    ex, q = data.load_export(root / "inst" / "eval_0000.npz")
    lab = data.load_label(root, "eval_0000")
    assert np.allclose(lab["Theta"], np.array(cfg["data"]["eval_levels"]) * float(ex["Theta_max"]))
    P = I.ExportedProblem(ex)
    s = P.solve(float(lab["Theta"][-1]))                     # from zero: the same state as the label's
    assert abs(s["M"] / lab["M"][-1] - 1) <= 1e-8 and abs(s["ThetaD"] / lab["ThetaD"][-1] - 1) <= 1e-8
    with np.load(root / "inst" / "eval_0000.npz") as z:
        assert "z" not in z.files                            # no solution field in the training file


def test_changed_files_or_configuration_are_refused(dataset, tmp_path):
    import copy
    import shutil
    from f2 import data
    cfg, root = dataset
    other = copy.deepcopy(cfg); other["data"]["eval_levels"] = [0.5, 1.0]
    with pytest.raises(RuntimeError):
        data.generate(other, root)                           # files made under another configuration
    work = tmp_path / "copy"
    shutil.copytree(root, work)
    lab = work / "labels" / "eval_0000.npz"
    with np.load(lab) as z:
        arrs = {k: z[k] for k in z.files}
    arrs["M"] = arrs["M"] * 1.01
    np.savez_compressed(lab, **arrs)
    with pytest.raises(RuntimeError):
        data.check_files(work, ["eval_0000"])


def test_reference_at_a_prescribed_ThetaD(member):
    """The secant search on rotation control finds the end rotation of a given Theta_D; its moment is the curve's."""
    q, ex, pre = member
    P = I.ExportedProblem(ex)
    r = P.solve_at_theta(0.004, z0=pre["z"])
    s = P.solve_at_ThetaD(r["ThetaD"], theta0=0.0035, z0=pre["z"])
    assert s["found"] and s["solves"] <= 6
    assert abs(s["theta"] / 0.004 - 1) <= 1e-7 and abs(s["M"] / r["M"] - 1) <= 1e-7


def test_loading_rule():
    """The device range rises with the plate's thickness and yield stress and falls with e1; the moment estimate
    stays below its cap; B-13's range is the one the development paths were checked with (probes/f2_dev)."""
    from f2.family import loading, moment_estimate, M_RULE, K_TH, THETA_TARGET
    base = Params(**TESTED["B-13_nominal"])
    k, T0 = loading(base)
    assert k == K_TH and THETA_TARGET < T0 < 0.1
    for field, up in (("tp", True), ("fy", True), ("e1", False)):
        hi = Params(**{**base.__dict__, field: RANGES[field][1]})
        assert (loading(hi)[1] > T0) == up
    strongest = Params(tp=25.0, e1=55.0, e2=75.0, fy=460.0, Np=130.0)
    assert moment_estimate(strongest) < M_RULE["cap"]
    assert abs(T0 - 0.0347) < 5e-4
