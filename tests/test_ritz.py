"""cmame-paper Stage 14: the polynomial Ritz-Galerkin baseline and the
enriched c* projection (fejepa.analysis.ritz), on small instances of both
dimensions: the subspace sizes of Appendix 1's ladder, the basis vanishing on
the clamped face, the nested ladder equal to each degree solved on its own,
Galerkin orthogonality, the energy gap non-increasing along the ladder and
equal to 1 - (P^T F)^T v / ||U*||_K^2, the pseudo-inverse's cut, the
enriched projection never worse than c* u or the Ritz solution (and exact
when u is the solution), and the refusals of a mesh or a Dirichlet set the
basis does not fit and of a configuration whose specification is not the
code's."""

import json
from pathlib import Path

import numpy as np
import pytest

from fejepa.analysis import ritz as R

ROOT = Path(__file__).resolve().parents[1]


def _labelled(arch):
    from fejepa.fe.solve import solve_fe_displacement

    arch.U_star, _ = solve_fe_displacement(arch.K, arch.F, np.asarray(arch.free_mask, bool),
                                           method="direct")
    return arch


@pytest.fixture(scope="module")
def inst3d():
    """An unstructured gmsh3d instance (823 nodes): enough distinct
    coordinates in every direction for degree 8 (a structured mesh with few
    layers makes the high-degree columns dependent, and the cut drops them)."""
    pytest.importorskip("gmsh")
    from fejepa.fe.gmsh3d import gmsh3d_instance

    return gmsh3d_instance(np.random.default_rng(7), lc=0.2, labelled=True)


@pytest.fixture(scope="module")
def inst2d():
    pytest.importorskip("gmsh")
    from fejepa.fe.generator import build_instance, sample_params

    prm = sample_params(np.random.default_rng(4))
    prm["target_h"] = 0.12
    return _labelled(build_instance(prm))


def test_the_ladder_sizes_are_appendix_1s():
    assert R.LADDER == {3: (6, 7, 8, 9), 2: (6, 8)} and R.CUT == 1e-13
    assert R.ENRICHED_DEGREE == {2: 6, 3: 8} and R.ID_TOL == 1e-6
    sizes = {d: [R.n_unknowns(d, p) for p in R.LADDER[d]] for d in (2, 3)}
    assert sizes == {3: [168, 252, 360, 495], 2: [42, 72]}
    assert [R.n_unknowns(d, R.ENRICHED_DEGREE[d]) for d in (2, 3)] == [42, 360]
    x = np.random.default_rng(0).uniform(size=(50, 3))
    for d in (2, 3):
        for p in R.LADDER[d]:
            Phi, deg = R.scalar_basis(x[:, :d], (1.0,) * d, p)
            assert d * Phi.shape[1] == R.n_unknowns(d, p) and deg.max() == p - 1


def test_the_basis_vanishes_on_the_clamped_face_and_is_nested():
    rng = np.random.default_rng(1)
    for d in (2, 3):
        x = rng.uniform(size=(40, d)) * np.array([2.0, 1.0, 0.7][:d])
        x[:10, 0] = 0.0
        Phi9, deg9 = R.scalar_basis(x, (2.0, 1.0, 0.7)[:d], max(R.LADDER[d]))
        assert np.all(Phi9[:10] == 0.0)
        Phi6, _ = R.scalar_basis(x, (2.0, 1.0, 0.7)[:d], 6)
        sub = Phi9[:, deg9 <= 5]                            # the same functions, another order
        assert sub.shape == Phi6.shape
        for j in range(Phi6.shape[1]):
            assert np.min(np.max(np.abs(sub - Phi6[:, [j]]), axis=0)) == 0.0


def test_pinv_solve_and_its_cut():
    rng = np.random.default_rng(2)
    M = rng.standard_normal((12, 12))
    A = M @ M.T + 12 * np.eye(12)
    B = rng.standard_normal((12, 3))
    X, dropped = R.pinv_solve(A, B)
    assert dropped == 0 and np.allclose(X, np.linalg.solve(A, B), rtol=1e-10)
    Q = rng.standard_normal((12, 4))
    S = np.hstack([Q, Q[:, :1]])                            # a repeated column
    X, dropped = R.pinv_solve(S.T @ S, S.T @ B)
    assert dropped == 1 and np.allclose(S @ X, Q @ np.linalg.lstsq(Q, B, rcond=None)[0])


@pytest.mark.parametrize("which", ["inst3d", "inst2d"])
def test_ritz_ladder_properties(which, request):
    from fejepa.metrics import energy_gap_rel

    a = request.getfixturevalue(which)
    d = a.nodes.shape[1]
    sols, t = R.ritz_ladder(a, R.LADDER[d])
    assert {"basis", "kp"} <= set(t) and all(f"solve_{p}" in t for p in R.LADDER[d])
    Kff, Ff = R.free_block(a)
    free = np.asarray(a.free_mask, bool)
    nk2 = R.ustar_norm_K(Kff, a.U_star[:, free]) ** 2
    gaps = []
    for p, (U, dropped, k) in sols.items():
        assert k == R.n_unknowns(d, p) and dropped == 0
        assert np.all(U[:, ~free] == 0.0)
        g = energy_gap_rel(U, a)
        alt = 1.0 - np.einsum("li,li->l", Ff, U[:, free]) / nk2
        assert np.allclose(g, alt, rtol=0, atol=1e-10)
        assert np.all(g >= -1e-12) and np.all(g <= 1.0)
        # Galerkin orthogonality: the residual is orthogonal to the subspace
        C = R.coarse(a, p)
        res = np.asarray((Kff @ U[:, free].T).T) - Ff
        assert np.max(np.abs(R.Pt_apply(C, res))) <= 1e-9 * np.max(np.abs(C["B"]))
        # the nested sub-block equals the degree solved on its own
        Uf, dr = R.ritz_coarse(C)
        assert dr == 0 and np.allclose(R.full_field(C, Uf), U, rtol=0,
                                       atol=1e-9 * np.abs(U).max())
        gaps.append(g)
    for lo, hi in zip(gaps, gaps[1:]):                      # nested spaces: never worse
        assert np.all(hi <= lo + 1e-12)


@pytest.mark.parametrize("which", ["inst3d", "inst2d"])
def test_the_enriched_projection(which, request):
    from fejepa.analysis.posthoc import amplitude_factor, apply_amplitude
    from fejepa.metrics import energy_gap_rel

    a = request.getfixturevalue(which)
    d = a.nodes.shape[1]
    C = R.coarse(a, R.ENRICHED_DEGREE[d])
    free = C["free"]
    Ur, _ = R.ritz_coarse(C)
    gr = energy_gap_rel(R.full_field(C, Ur), a)
    rng = np.random.default_rng(5)
    for kind in ("random", "near", "exact", "coarse"):
        if kind == "random":
            u = rng.standard_normal(a.U_star.shape) * np.abs(a.U_star).max()
        elif kind == "near":
            u = 1.4 * a.U_star + 0.02 * np.abs(a.U_star).max() * rng.standard_normal(
                a.U_star.shape)
        elif kind == "exact":
            u = a.U_star.copy()
        else:
            u = R.full_field(C, Ur) * 2.0                   # in range(P)
        u[:, ~free] = 0.0
        Ue, dropped = R.enriched(C, u[:, free])
        ge = energy_gap_rel(R.full_field(C, Ue), a)
        gc = energy_gap_rel(apply_amplitude(u, amplitude_factor(u, a.K, a.F, free)), a)
        assert np.all(ge <= np.minimum(gc, gr) + 1e-9), kind
        if kind == "exact":
            assert np.all(ge <= 1e-9) and dropped == [0] * a.n_loads
        if kind == "coarse":                                # u adds nothing: one direction
            assert dropped == [1] * a.n_loads                # dropped, the Ritz gap kept
            assert np.allclose(ge, gr, rtol=1e-7, atol=1e-12)
        if kind in ("random", "near"):
            assert dropped == [0] * a.n_loads


def test_the_basis_refuses_what_it_does_not_fit(inst3d):
    import copy

    a = copy.deepcopy(inst3d)
    a.nodes = a.nodes + np.array([0.1, 0.0, 0.0])          # the box no longer starts at 0
    with pytest.raises(ValueError, match="bounding box"):
        R.bounding_box(a)
    b = copy.deepcopy(inst3d)
    dm = np.asarray(b.dirichlet_mask, bool).copy()
    first = int(np.nonzero(dm)[0][0])
    dm[first] = False                                     # one component of a clamped node
    b.dirichlet_mask = dm
    with pytest.raises(ValueError, match="node-wise"):
        R.free_nodes(b)
    c = copy.deepcopy(inst3d)
    far = int(np.argmax(c.nodes[:, 0]))
    dm = np.asarray(c.dirichlet_mask, bool).copy()
    dm[3 * far:3 * far + 3] = True                        # a clamped node at x = W
    c.dirichlet_mask = dm
    with pytest.raises(ValueError, match="x = 0"):
        R.bounding_box(c)


def test_metrics_and_identity(inst2d):
    m = R.metrics(inst2d.U_star, inst2d)
    assert set(m) == {"load", "mean", "worse_than_zero"} and list(m["mean"]) == list(R.FIELDS)
    assert max(abs(m["mean"][k]) for k in ("disp_rel_l2", "energy_gap_rel", "vm_rel_l2",
                                           "peak_vm_rel_err")) < 1e-12
    assert m["mean"]["crit_recall"] == 1.0 and m["worse_than_zero"]["worse"] == 0
    z = R.metrics(np.zeros_like(inst2d.U_star), inst2d)
    assert np.allclose(z["load"]["energy_gap_rel"], 1.0)
    assert R.identity(True, [1.0, 2.0], [1.0, 2.0 * (1 + 5e-7)])["ok"]
    assert not R.identity(True, [1.0, 2.0], [1.0, 2.0 * (1 + 2e-6)])["ok"]
    assert not R.identity(False, [1.0], [1.0])["ok"]
    assert not R.identity(True, [1.0, 2.0], [1.0])["ok"]
    s = R.paired_shares([1.0, 2.0, 3.0], [2.0, 2.0, 1.0], "energy_gap_rel")
    assert (s["ritz_better_share"], s["ties"]) == (1 / 3, 1)
    s = R.paired_shares([1.0, 2.0, 3.0], [2.0, 2.0, 1.0], "crit_recall")
    assert s["ritz_better_share"] == 1 / 3


def test_complete_lines_drops_a_cut_last_line(tmp_path):
    p = tmp_path / "rows.jsonl"
    p.write_text('{"i": 0}\n{"i": 1}\n{"i": 2, "cut')
    assert [r["i"] for r in R.complete_lines(p)] == [0, 1]
    assert p.read_text() == '{"i": 0}\n{"i": 1}\n'
    assert R.complete_lines(tmp_path / "none.jsonl") == []


def test_the_configuration_is_the_codes_specification(tmp_path):
    cfg = R.load_config(ROOT / "configs" / "ritz_v1.json")
    assert cfg["spec"]["fixed"] == "20 October 2026"
    for key, val in (("cut", 1e-12), ("id_tol", 1e-5), ("enriched_cut", 1e-13),
                     ("inband_factor", 0.9), ("ood_peak_factor", 0.4),
                     ("ladder", {"3": [6, 7, 8], "2": [6, 8]}),
                     ("enriched_degree", {"2": 6, "3": 9})):
        bad = json.loads(json.dumps(cfg))
        bad["spec"][key] = val
        p = tmp_path / "bad.json"
        p.write_text(json.dumps(bad))
        with pytest.raises(ValueError, match="not the code's"):
            R.load_config(p)
    extra = dict(cfg, more=1)
    p = tmp_path / "extra.json"
    p.write_text(json.dumps(extra))
    with pytest.raises(ValueError, match="top-level keys"):
        R.load_config(p)
