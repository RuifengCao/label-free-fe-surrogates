"""Checks of the CHS flange-plate splice model (fejoint.chs): the mesh (volumes, holes, fillet, ties, faces), the
contact model (preload, symmetry, equilibrium, the far field against beam theory, axial control), the warm-started
contact solver against fejoint.nlsolve.ContactProblem, and the no-slip bounding variant. A very coarse mesh (TINY)
keeps the suite short; the meshes the runs use are built and checked for volume only."""
from collections import Counter

import numpy as np
import pytest

from fejoint import chs
from fejoint.nlsolve import ContactProblem

TINY = chs.MESHES["tiny"]


@pytest.fixture(scope="module")
def b19_tiny():
    g = chs.fidalgo("B-19")
    m = chs.SpliceModel(g, TINY)
    pre = m.set_preload(125e3)
    return g, m, pre


@pytest.mark.parametrize("name", ["B-13", "B-19"])
@pytest.mark.parametrize("mesh", ["coarse", "medium"])
def test_mesh_volumes_holes_fillet(name, mesh):
    g = chs.fidalgo(name)
    msh = chs.build(g, mesh)
    c = chs.mesh_checks(g, msh)
    assert c["min_detJ"] > 0
    assert abs(c["plate_volume_ratio"] - 1) < 2e-3          # chords of the polar mesh
    assert abs(c["tube_volume_ratio"] - 1) < 4e-3           # 7.5 degree chords beyond z_h
    assert abs(c["fillet_volume_ratio"] - 1) < 1e-3         # outer nodes moved onto the weld face
    assert all(abs(v - 1) < 0.12 for v in c["hole_volume_ratio"])
    assert len(msh["patches"]) == 6 and len({p.size for p in msh["patches"]}) == 1


def test_mesh_ties_and_faces():
    g = chs.fidalgo("B-19")
    msh = chs.build(g, "coarse")
    nodes, hexes = msh["nodes"], msh["hexes"]
    coarse = msh["grids"]["phi_coarse"]
    for s, ia, ib, wa, wb, _ in msh["ties"]:
        r, ph, z = chs.cyl(nodes[[s, ia, ib]])
        assert np.allclose(r, r[0], atol=1e-6) and np.allclose(z, z[0], atol=1e-6)
        assert ph[1] < ph[0] < ph[2] and np.isclose(ph[2] - ph[1], chs.STEP)
        assert np.isclose(wa + wb, 1.0) and np.isclose(wb, (ph[0] - ph[1]) / chs.STEP)
        assert np.isclose(coarse, ph[1]).any() and np.isclose(coarse, ph[2]).any()
    faces = Counter()
    for h in hexes:
        for f in [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
            faces[tuple(sorted(h[list(f)]))] += 1
    assert max(faces.values()) == 2
    # the fused part of the wall shares its faces with the plate; the root does not
    rp = msh["root_pairs"]
    assert rp.shape[0] == len(msh["grids"]["phi_fine"])
    assert np.allclose(nodes[rp[:, 0]], nodes[rp[:, 1]])


def test_preload_symmetry_and_equilibrium(b19_tiny):
    g, m, pre = b19_tiny
    assert np.allclose(pre["forces_N"], 125e3, rtol=1e-6)
    z, rep = m.solve(0.0)
    r = m.readings(z, rep)
    assert abs(r["M_kNm"]) < 1e-6 and abs(r["theta_section"]) < 1e-9
    assert abs(r["reaction_y_N"]) < 1e-3
    assert max(abs(v) for v in r["kkt"].values()) < 1e-8


def test_bending_far_field_and_root(b19_tiny):
    g, m, pre = b19_tiny
    z, rep = m.solve(0.002)
    r = m.readings(z, rep)
    assert r["converged"] and max(abs(v) for v in r["kkt"].values()) < 1e-8
    assert abs(r["reaction_y_N"]) < 1e-3 * r["M_kNm"] * 1e3       # no force along y
    E_I = g.E_t * np.pi / 64 * (g.d ** 4 - (g.d - 2 * g.t) ** 4)
    dz = g.L_tube - g.z_meas
    beam = r["M_kNm"] * 1e6 * dz / E_I                                # beam theory between the ring and the end
    assert abs((r["theta_end"] - r["theta_section"]) / beam - 1) < 0.01
    # tension side opens: bolt 1 gains force and bolt 6 hardly changes
    assert r["bolt_force_kN"][0] > 125.0 and abs(r["bolt_force_kN"][5] - 125.0) < 1.0
    # the unfused root: separations >= 0, contact forces >= 0, complementary. In this elastic range it stays
    # closed all round (the plate tilts into the wall's inner corner on the tension side, 7 November 2026)
    u = (m.T @ z).reshape(-1, 3)
    rp = m.msh["root_pairs"]
    sep = u[rp[:, 0], 2] - u[rp[:, 1], 2]
    lam = rep["grad"][3 * rp[:, 0] + 2]
    scale = np.abs(rep["grad"]).max()
    assert sep.min() >= -1e-12 and lam.min() >= -1e-9 * scale
    assert np.abs(sep * lam).max() <= 1e-9 * scale * max(np.abs(u).max(), 1e-300)
    assert lam.max() > 0


def test_axial_control_is_symmetric(b19_tiny):
    g, m, pre = b19_tiny
    z0 = m.z.copy()
    z, rep = m.solve(0.05, control="axial")
    r = m.readings(z, rep)
    assert r["T_kN"] > 0 and abs(r["M_kNm"]) < 1e-6 * r["T_kN"] * g.R
    b = np.array(r["bolt_force_kN"])
    assert np.allclose(b, b[::-1], rtol=1e-9)          # mirror about y = 0: bolts 1 and 6, 2 and 5, 3 and 4
    assert np.allclose(b, b.mean(), rtol=1e-4)         # near the 12-fold symmetry (the O-grid core breaks it)
    m.solve(0.0, z0=z0)                                               # back to rotation control at theta = 0


def test_warm_start_matches_contactproblem():
    g = chs.fidalgo("B-19")
    m = chs.SpliceModel(g, TINY)
    m.set_preload(100e3)
    z1, rep1 = m.solve(0.001)
    cold = ContactProblem(m.prob.T, m.prob.K_lin, m.prob.f, m.prob.sets, m.prob.fixed, m.prob.cidx)
    zs = np.zeros(m.nfull); zs[m.ith] = 0.001
    with chs.direct_solver_up_to(m.nfull):
        z2, rep2 = cold.solve(zs)
    assert np.allclose(z1, z2, rtol=0, atol=1e-9 * np.abs(z1).max())
    assert np.isclose(rep1["grad"][m.ith], rep2["grad"][m.ith], rtol=1e-8)


def test_no_slip_is_stiffer():
    g = chs.fidalgo("B-19")
    out = {}
    for splice in ("frictionless", "no-slip"):
        m = chs.SpliceModel(g, TINY, splice=splice)
        m.set_preload(125e3)
        z, rep = m.solve(0.001)
        out[splice] = m.readings(z, rep)["M_kNm"]
    assert out["no-slip"] > out["frictionless"] > 0


def test_rare_branches_of_the_model_and_solver(capsys):
    """Branches the runs do not take: a short interval of the mesh spacing, the tube's section modulus, commit
    (the next solve is unchanged), the solver's verbose print, and a line search that finds no point it can
    evaluate (the solve stops, not converged). The solver's second convergence test, after the step, cannot be
    reached: the same test before the step has already ended the loop (as in fejoint.nlsolve)."""
    assert np.array_equal(chs._fit(0.0, 1.0, 1.0, 1.2, 2.0), [0.0, 1.0])
    g = chs.fidalgo("B-19")
    n = 400
    r = g.R - g.t + (np.arange(n) + 0.5) * g.t / n
    phi = (np.arange(4 * n) + 0.5) * 2 * np.pi / (4 * n)
    inertia = ((r[:, None] * np.sin(phi[None, :])) ** 2 * r[:, None]).sum() * (g.t / n) * (2 * np.pi / (4 * n))
    assert np.isclose(g.S_tube, inertia / g.R, rtol=1e-6)
    m = chs.SpliceModel(g, TINY)
    m.set_preload(125e3)
    z0 = m.z.copy()
    capsys.readouterr()
    z1, rep1 = m.solve(0.001, verbose=True)
    assert rep1["converged"] and "'it': 1" in capsys.readouterr().out
    m.commit()
    z2, rep2 = m.solve(0.001, z0=z0)
    assert rep2["converged"] and np.allclose(z2, z1, rtol=0, atol=1e-9 * np.abs(z1).max())
    real = m.probs["rotation"].evaluate

    def no_trial_point(z, mode, tangent=True):
        if not tangent:
            raise RuntimeError("cannot evaluate")
        return real(z, mode, tangent=tangent)

    m.probs["rotation"].evaluate = no_trial_point
    z3, rep3 = m.solve(0.002, z0=z0)
    assert not rep3["converged"] and rep3["iterations"] == 0


def test_fully_fused_variant_builds():
    g = chs.fidalgo("B-19", root=0.0, leg=0.0)
    msh = chs.build(g, TINY)
    assert msh["root_pairs"].shape == (0, 2) and not (msh["part"] == 2).any()
    c = chs.mesh_checks(g, msh)
    assert c["min_detJ"] > 0 and abs(c["plate_volume_ratio"] - 1) < 0.02     # TINY resolves the holes coarsely
