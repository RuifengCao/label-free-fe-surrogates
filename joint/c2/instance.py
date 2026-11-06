"""Instances of gate G-C2.1: the plastic T-stub of fejoint.tstub_pl loaded through a spring, in exported form, and
its exact (deformation-theory) solution for labels and checks.

Loading. The web's end section is rigid in x: all its nodes share one unknown e, their u_x. A linear spring of
stiffness k_s joins it to the loading device, whose displacement D is prescribed. The force on the pair is
F = 4 k_s (D - e) (quarter model), read from the single unknown e.
- Why a spring: with the end displacement prescribed directly, the force is a dual quantity, the stress resultant
  in the stiff web; there, force errors cost energy only through the web's large stiffness, and fields whose
  energy was close carried large force errors (CPU pilots of 6 November 2026). Through the spring a force error
  costs at least delta_F^2 / (2 k_s) per quarter: for any admissible field z, 1/2 k_s (e - e*)^2 <= Pi(z) - Pi*
  (the spring is k_s-strongly convex in e, the rest of Pi convex, z* optimal over a convex set), so
  |F(z) - F*| <= 4 sqrt(2 k_s (Pi(z) - Pi*)).
- Under deformation theory the T-stub's state at a given end displacement does not depend on the loading device,
  so the reference curve F(e) is that of displacement control (ExportedProblem.solve_at_e, tests).

Unknowns z (length nfull + 1, nfull = 3 n + 3): three per node (u_x, u_y, u_z; on the bearing patch the u_x slot
holds the separation s >= 0 from the head plane), the bolt head's three unknowns (a, b, c), and e (the last). The
u_x slots of the end section's nodes are unused and fixed at zero: T maps their u_x to e. Physical displacements
u = T z. Energy (deformation theory, convex):

    Pi(z) = sum over the flange and web elements of their condensed Hencky energy (fejoint.nlhex)
            + 1/2 z^T K_lin z    (head tilt springs, shear springs, weak bonded springs)
            + phi(a + delta)      (the half bolt's axial spring, elastic-plastic, pre-shortened by delta)
            + 1/2 k_s (e - D)^2   (the loading spring)

subject to z >= 0 on the contact unknowns (u_x on the plane between the flanges, s on the bearing patch) and z = 0
on the Dirichlet unknowns (symmetry planes, the unused slots). Pi > 0 for D > 0.

A second force reading, from the stresses: F_sigma = 4 grad W(z) . v, W = Pi without the loading spring, v rising
linearly from 0 at x0 to 1 at the end section in the web (and 1 on e). For the exact solution F_sigma = F.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from fejoint.tstub_pl import PlasticTStubModel
from fejoint.nlhex import PlasticHexSet
from fejoint.nlsolve import ContactProblem, AxialSprings
from fejoint.plasticity import Hardening, Material
from .family import Params, geometry, steel, bolt_curve, MESH, K_SPRING

KKT_KEYS = ("min_gap", "min_lambda", "max_complementarity", "max_lambda_inactive", "max_residual_unconstrained")


def build(q: Params, mesh: dict = MESH) -> PlasticTStubModel:
    """The model (fejoint.tstub_pl, displacement control) with the family's laws and preload, the virtual field of
    the stress reading, and the arrays of the spring-loaded problem (m.spring)."""
    g = geometry(q)
    mat = steel(q.fy)
    m0 = PlasticTStubModel(g, mat, mat, control="displacement", **mesh)
    bc = bolt_curve(g, m0.k_ax)
    m = PlasticTStubModel(g, mat, mat, control="displacement", bolt_curve=bc, **mesh)
    m.delta = q.rho * float(bc[1][0]) / m.k_ax
    m.bolts.delta[:] = m.delta
    x = m.nodes[:, 0]
    x_end = x.max()
    x0 = g.t_f + g.r + 10.0
    web = np.unique(m.hexes[m.part == 1])
    sel = web[x[web] >= x0 - 1e-9]
    nf, e_idx = m.nfull, m.nfull
    v = np.zeros(nf + 1)
    v[3 * sel] = (x[sel] - x0) / (x_end - x0)
    v[3 * m.endn] = 0.0
    v[e_idx] = 1.0
    T = sp.hstack([m.T_phys.tocsr(), sp.csr_matrix((3 * m.n, 1))]).tolil()
    for r in 3 * m.endn:
        assert T[r, r] == 1.0 and T[r].nnz == 1
        T[r, r] = 0.0
        T[r, e_idx] = 1.0
    T = T.tocsr(); T.eliminate_zeros()
    K = sp.block_diag([m.probs["displacement"].K_lin, sp.csr_matrix((1, 1))]).tocsr()
    fixed = np.zeros(nf + 1, bool)
    fixed[:nf] = m.probs["force"].fixed
    fixed[3 * m.endn] = True
    m.spring = {"T": T, "K": K, "fixed": fixed, "cidx": m.prob.cidx, "e_idx": e_idx, "unused": 3 * m.endn,
                "v": v, "k_s": K_SPRING}
    return m


def export(m: PlasticTStubModel, q: Params) -> dict:
    """Arrays of the spring-loaded problem that the training code needs (no solve)."""
    s = m.spring
    T = s["T"].tocoo(); K = s["K"].tocoo()
    flags = np.zeros((m.n, 7), bool)
    x, y, zc = m.nodes.T
    g = m.g
    flags[m.contact, 0] = True                                   # plane between the flanges
    for p in m.patches:
        flags[p, 1] = True                                       # bearing patch (s in the x slot)
    flags[m.endn, 2] = True                                      # end section (u_x = e)
    flags[np.unique(m.hexes[m.part == 0]), 3] = True             # flange
    flags[np.unique(m.hexes[m.part == 1]), 4] = True             # web and root
    flags[np.isclose(zc, 0.0), 5] = True                         # web mid-plane (u_z = 0)
    flags[np.isclose(y, g.L / 2), 6] = True                      # mid-length plane (u_y = 0)
    hf, hw = m.sets[0].mat.hardening, m.sets[1].mat.hardening
    bc = m.bolts.curve
    return dict(nodes=m.nodes, hexes_f=m.hexes[m.part == 0], hexes_w=m.hexes[m.part == 1],
                hard_f_alpha=hf.alpha, hard_f_sigma=hf.sigma, hard_f_hend=np.float64(hf.h_end),
                hard_w_alpha=hw.alpha, hard_w_sigma=hw.sigma, hard_w_hend=np.float64(hw.h_end),
                E=np.float64(210000.0), nu=np.float64(0.3),
                T_row=T.row, T_col=T.col, T_val=T.data, T_shape=np.array(T.shape),
                K_row=K.row, K_col=K.col, K_val=K.data, K_shape=np.array(K.shape),
                fixed=s["fixed"], unused=s["unused"], cidx=s["cidx"], e_idx=np.int64(s["e_idx"]),
                k_s=np.float64(s["k_s"]), head=m.head_a, k_ax=np.float64(m.k_ax), bolt_e=bc[0], bolt_N=bc[1],
                bolt_hend=np.float64(bc[2]), delta=np.float64(m.delta), v=s["v"], node_flags=flags, params=np.array([getattr(q, k) for k in Params.__dataclass_fields__]))


class ExportedProblem:
    """The problem of an export, rebuilt from its arrays alone (float64, numpy): the reference solution at any
    loading-device displacement D, the reference at a prescribed end displacement e, and the energy and readings of
    any field. Labels and the evaluation use this class only, so they see exactly what the training code sees."""

    def __init__(self, ex: dict):
        E, nu = float(ex["E"]), float(ex["nu"])
        mf = Material(E, nu, Hardening(ex["hard_f_alpha"], ex["hard_f_sigma"], float(ex["hard_f_hend"])))
        mw = Material(E, nu, Hardening(ex["hard_w_alpha"], ex["hard_w_sigma"], float(ex["hard_w_hend"])))
        shape = lambda k: tuple(int(v) for v in ex[k])  # noqa: E731
        T = sp.csr_matrix((ex["T_val"], (ex["T_row"], ex["T_col"])), shape=shape("T_shape"))
        K = sp.csr_matrix((ex["K_val"], (ex["K_row"], ex["K_col"])), shape=shape("K_shape"))
        self.n_z = K.shape[0]
        self.e_idx = int(ex["e_idx"])
        assert self.e_idx == self.n_z - 1
        self.k_s = float(ex["k_s"])
        self.head = np.asarray(ex["head"], int).ravel()
        curve = (np.asarray(ex["bolt_e"]), np.asarray(ex["bolt_N"]), float(ex["bolt_hend"]))
        self.bolts = AxialSprings(self.head, self.n_z, float(ex["k_ax"]), N_curve=curve,
                                  delta=np.full(self.head.size, float(ex["delta"])))
        self.loading = AxialSprings([self.e_idx], self.n_z, self.k_s, delta=np.zeros(1))
        self.solids = [PlasticHexSet(ex["nodes"], ex["hexes_f"], mf), PlasticHexSet(ex["nodes"], ex["hexes_w"], mw)]
        fixed = np.asarray(ex["fixed"], bool)
        cidx = np.asarray(ex["cidx"], int)
        self.prob = ContactProblem(T, K, np.zeros(self.n_z), self.solids + [self.bolts, self.loading], fixed, cidx)
        fixed_e = fixed.copy(); fixed_e[self.e_idx] = True
        self.prob_e = ContactProblem(T, K, np.zeros(self.n_z), self.solids + [self.bolts], fixed_e, cidx)
        self.v = np.asarray(ex["v"], float)
        self.T = T

    def _readings(self, z, g_W, D):
        e = float(z[self.e_idx])
        return {"e": e, "F": 4.0 * self.k_s * (D - e), "F_sigma": 4.0 * float(g_W @ self.v),
                "bolt_N": float(self.bolts._law(z[self.head] + self.bolts.delta)[0][0])}

    def solve(self, D: float, z0=None, tol: float = 1e-12, max_it: int = 80) -> dict:
        """The exact deformation-theory solution at loading-device displacement D, from z0 (or zero)."""
        self.loading.delta[:] = -D
        z = np.zeros(self.n_z) if z0 is None else np.where(self.prob.fixed, 0.0, z0)
        z, rep = self.prob.solve(z, mode="hencky", tol=tol, max_it=max_it)
        g_W = rep["grad"].copy(); g_W[self.e_idx] -= self.k_s * (z[self.e_idx] - D)
        out = {"z": z, "Pi": float(rep["energy"]), **self._readings(z, g_W, D),
               "kkt": {k: float(rep[k]) for k in KKT_KEYS}, "iterations": int(rep["iterations"]),
               "converged": bool(rep["converged"]), "plastic_points": [int(p) for p in rep["plastic_points"]]}
        return out

    def solve_at_e(self, e: float, z0=None, tol: float = 1e-12, max_it: int = 80) -> dict:
        """The reference at a prescribed end displacement e (displacement control, no loading spring): its force is
        the end reaction, F = 4 dW/de."""
        z = np.zeros(self.n_z) if z0 is None else np.where(self.prob_e.fixed, 0.0, z0)
        z[self.e_idx] = e
        z, rep = self.prob_e.solve(z, mode="hencky", tol=tol, max_it=max_it)
        return {"z": z, "W": float(rep["energy"]), "F": 4.0 * float(rep["grad"][self.e_idx]),
                "converged": bool(rep["converged"]), "kkt": {k: float(rep[k]) for k in KKT_KEYS}}

    def evaluate(self, z: np.ndarray, D: float) -> dict:
        """Energy, force readings, bolt force and plastic Gauss points of a field z whose fixed entries are zero and
        whose contact entries are >= 0 (any prediction of the network), at loading-device displacement D."""
        z = np.asarray(z, float)
        self.loading.delta[:] = -D
        E, g, _, info = self.prob.evaluate(z, "hencky", tangent=False)
        g_W = g.copy(); g_W[self.e_idx] -= self.k_s * (z[self.e_idx] - D)
        return {"Pi": float(E), **self._readings(z, g_W, D),
                "plastic": np.concatenate([s._trial["plastic"].ravel() for s in self.solids])}


__all__ = ["build", "export", "ExportedProblem", "KKT_KEYS"]
