"""Instances of the CHS surrogate gate (draft): the splice of fejoint.chs loaded through a rotational spring, in
exported form, and its exact (deformation-theory) solution for labels and checks. Follows c2/instance.py.

Loading. The tube's end section stays plane, its nodes' u_z = w0 - theta y, with w0 free (no axial force) and the
end rotation theta one unknown. A linear rotational spring of stiffness k_th per half model joins theta to a
loading device whose rotation Theta is prescribed. The moment on the joint is M = 2 k_th (Theta - theta), read
from the single unknown theta.
- Through the spring a moment error costs energy: for any admissible field z, 1/2 k_th (theta - theta*)^2 <=
  Pi(z) - Pi* (the spring is k_th-strongly convex in theta, the rest of Pi convex, z* optimal over a convex set),
  so |M(z) - M*| <= 2 sqrt(2 k_th (Pi(z) - Pi*)).
- Under deformation theory the splice's state at a given end rotation does not depend on the loading device, so
  the reference curve M*(theta) is that of rotation control (ExportedProblem.solve_at_theta).

Preload. Every bolt is pre-shortened by the same delta, set at generation so that the mean of the six bolts'
forces at zero rotation is Np (a fixed point on delta, each step a solve at theta = 0, as gate G-F1 sets its
preload); the six forces then differ by the mesh's round-off only. The preload state's readings are kept in the
export, and the rotation Theta_D of the tests is read relative to it, as gate G-F1 reads it.

Unknowns z (nfull = 3 n + 3 nb + 2): three per node (u_x, u_y, u_z; in the bearing patches the u_z slot holds the
head's separation, at the root pairs the tube node's u_z slot holds the root's opening; the slots of the hanging
nodes and the end section's u_z slots are unused and fixed at zero), the three unknowns (a, theta_1, theta_2) of
each bolt head, w0, and theta (the last). Physical displacements u = T z (fejoint.chs.SpliceModel). Energy
(deformation theory, convex):

    Pi(z) = sum over the plate, tube and weld elements of their condensed Hencky energy (fejoint.nlhex)
            + 1/2 z^T K_lin z            (the heads' tilt springs, weak springs on the head separations)
            + sum_b phi(a_b + delta)     (the half bolts' axial springs, elastic-plastic, pre-shortened)
            + 1/2 k_th (theta - Theta)^2 (the loading spring)

subject to z >= 0 on the contact unknowns (u_z on the splice plane, the head separations, the root openings) and
z = 0 on the fixed unknowns (the symmetry plane's u_x, the plate centre's u_y, the unused slots; for the no-slip
bound also u_x and u_y on the splice plane).

A second moment reading, from the stresses: M_sigma = 2 grad W(z) . v, W = Pi without the loading spring and v a
virtual rotation of the tube's sections, rising linearly from 0 at the tube's coarse interface z_h to 1 at the end
section (1 on theta). For the exact solution M_sigma = M.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from fejoint import chs
from fejoint.nlhex import PlasticHexSet
from fejoint.nlsolve import AxialSprings
from fejoint.plasticity import Hardening, Material, von_mises
from .family import Params, geometry, materials, bolt_curve, MESH

KKT_KEYS = ("min_gap", "min_lambda", "max_complementarity", "max_lambda_inactive", "max_residual_unconstrained")
PARTS = ("p", "t", "w")                 # plate, tube, fillet weld (parts 0, 1, 2 of fejoint.chs.build)
FLAGS = ("splice_plane", "bearing_patch", "end_section", "plate", "tube", "weld", "symmetry_plane", "root_tube",
         "hanging", "measuring_ring")


def build(q: Params, mesh=MESH, splice: str = "frictionless") -> chs.SpliceModel:
    """The splice model of fejoint.chs (rotation control) with the family's laws, and the arrays of the
    spring-loaded problem (m.spring): the free end rotation and the virtual field of the stress reading."""
    g = geometry(q)
    m = chs.SpliceModel(g, mesh, mats=materials(q), bolt_curve=bolt_curve(g), splice=splice)
    x, y, zc = m.nodes.T
    msh = m.msh
    nf, ith = m.nfull, m.ith
    assert ith == nf - 1 and m.iw0 == nf - 2
    zh, z_end = float(msh["grids"]["z_h"]), g.tp + g.L_tube
    tube = np.unique(msh["hexes"][msh["part"] == 1])
    sel = np.setdiff1d(tube[zc[tube] > zh + 1e-9], msh["end"])
    v = np.zeros(nf)
    v[3 * sel + 2] = -y[sel] * (zc[sel] - zh) / (z_end - zh)
    v[ith] = 1.0
    fixed = m.fixed.copy()
    fixed[ith] = False
    assert not fixed[3 * sel + 2].any() and not np.isin(3 * sel + 2, m.cidx).any()
    m.spring = {"fixed": fixed, "v": v, "K": m.probs["rotation"].K_lin}
    return m


def node_flags(m: chs.SpliceModel) -> np.ndarray:
    msh = m.msh
    x, y, zc = m.nodes.T
    f = np.zeros((m.n, len(FLAGS)), bool)
    f[msh["bottom"], 0] = True
    for p in msh["patches"]:
        f[p, 1] = True
    f[msh["end"], 2] = True
    for k in (0, 1, 2):
        f[np.unique(msh["hexes"][msh["part"] == k]), 3 + k] = True
    f[np.abs(x) < 1e-6, 6] = True
    f[msh["root_pairs"][:, 0], 7] = True
    f[[t[0] for t in msh["ties"]], 8] = True
    f[m.ring, 9] = True
    return f


def export(m: chs.SpliceModel, q: Params, k_th: float, delta: float, pre: dict | None = None) -> dict:
    """Arrays of the spring-loaded problem that training and the reference need. delta: the bolts' pre-shortening;
    pre: the preload state's readings (make() fills both)."""
    s = m.spring
    T = m.T.tocoo(); K = s["K"].tocoo()
    out = dict(nodes=m.nodes, T_row=T.row, T_col=T.col, T_val=T.data, T_shape=np.array(T.shape),
               K_row=K.row, K_col=K.col, K_val=K.data, K_shape=np.array(K.shape),
               fixed=s["fixed"], cidx=m.cidx, ith=np.int64(m.ith), iw0=np.int64(m.iw0), k_th=np.float64(k_th),
               head=m.ndof + 3 * np.arange(m.nb), k_ax=np.float64(m.k_ax),
               bolt_e=np.asarray(m.bolts.curve[0], float), bolt_N=np.asarray(m.bolts.curve[1], float),
               bolt_hend=np.float64(m.bolts.curve[2]), delta=np.full(m.nb, float(delta)), v=s["v"],
               node_flags=node_flags(m), iD=np.int64(m.iD), iC=np.int64(m.iC), ring=m.ring,
               d=np.float64(m.g.d), params=np.array([getattr(q, k) for k in Params.__dataclass_fields__]),
               ThetaD_pre=np.float64(pre["ThetaD_abs"] if pre else 0.0),
               uzC_pre=np.float64(pre["uzC"] if pre else 0.0))
    for k, name in enumerate(PARTS):
        mat = m.mats[k]
        h = mat.hardening
        out[f"hexes_{name}"] = m.msh["hexes"][m.msh["part"] == k]
        out[f"E_{name}"], out[f"nu_{name}"] = np.float64(mat.E), np.float64(mat.nu)
        out[f"hard_{name}_alpha"], out[f"hard_{name}_sigma"] = np.asarray(h.alpha, float), np.asarray(h.sigma, float)
        out[f"hard_{name}_hend"] = np.float64(h.h_end)
    return out


class ExportedProblem:
    """The problem of an export, rebuilt from its arrays alone (float64, numpy): the reference at a loading-device
    rotation Theta (spring) or at a prescribed end rotation theta, the preload, and the energy and readings of any
    field. Labels and the evaluation use this class only, so they see exactly what the training code sees."""

    def __init__(self, ex: dict):
        shape = lambda k: tuple(int(v) for v in ex[k])  # noqa: E731
        T = sp.csr_matrix((ex["T_val"], (ex["T_row"], ex["T_col"])), shape=shape("T_shape"))
        K = sp.csr_matrix((ex["K_val"], (ex["K_row"], ex["K_col"])), shape=shape("K_shape"))
        self.n_z = K.shape[0]
        self.ith, self.iw0 = int(ex["ith"]), int(ex["iw0"])
        assert self.ith == self.n_z - 1
        self.k_th = float(ex["k_th"])
        self.head = np.asarray(ex["head"], int).ravel()
        curve = (np.asarray(ex["bolt_e"]), np.asarray(ex["bolt_N"]), float(ex["bolt_hend"]))
        self.bolts = AxialSprings(self.head, self.n_z, float(ex["k_ax"]), N_curve=curve,
                                  delta=np.asarray(ex["delta"], float))
        self.loading = AxialSprings([self.ith], self.n_z, self.k_th, delta=np.zeros(1))
        self.solids = []
        for name in PARTS:
            mat = Material(float(ex[f"E_{name}"]), float(ex[f"nu_{name}"]),
                           Hardening(ex[f"hard_{name}_alpha"], ex[f"hard_{name}_sigma"], float(ex[f"hard_{name}_hend"])))
            self.solids.append(PlasticHexSet(ex["nodes"], ex[f"hexes_{name}"], mat))
        fixed = np.asarray(ex["fixed"], bool)
        cidx = np.asarray(ex["cidx"], int)
        f0 = np.zeros(self.n_z)
        self.prob = chs.WarmContactProblem(T, K, f0, self.solids + [self.bolts, self.loading], fixed, cidx)
        fixed_th = fixed.copy(); fixed_th[self.ith] = True
        self.prob_th = chs.WarmContactProblem(T, K, f0, self.solids + [self.bolts], fixed_th, cidx)
        self.v = np.asarray(ex["v"], float)
        self.T = T
        self.d = float(ex["d"])
        self.tD = T.getrow(3 * int(ex["iD"]) + 2)
        self.tC = T.getrow(3 * int(ex["iC"]) + 2)
        self.ThetaD_pre = float(ex["ThetaD_pre"])

    # ---------------------------------------------------------------- readings
    def _readings(self, z, g_W) -> dict:
        uD, uC = float((self.tD @ z)[0]), float((self.tC @ z)[0])
        return {"theta": float(z[self.ith]), "w0": float(z[self.iw0]), "M_sigma": 2.0 * float(g_W @ self.v),
                "ThetaD": uD / self.d - self.ThetaD_pre, "ThetaD_abs": uD / self.d, "uzD": uD, "uzC": uC,
                "bolt_N": self.bolts._law(z[self.head] + self.bolts.delta)[0].tolist()}

    def max_von_mises(self) -> dict:
        return {name: float(von_mises(s._trial["sig"]).max()) for name, s in zip(PARTS, self.solids)
                if s._trial is not None}

    def _report(self, z, rep) -> dict:
        return {"kkt": {k: float(rep[k]) for k in KKT_KEYS}, "iterations": int(rep["iterations"]),
                "converged": bool(rep["converged"]), "plastic_points": [int(p) for p in rep["plastic_points"]],
                "max_von_mises": self.max_von_mises()}

    # ---------------------------------------------------------------- solves
    def solve(self, Theta: float, z0=None, tol: float = 1e-12, max_it: int = 80) -> dict:
        """The exact deformation-theory solution at loading-device rotation Theta, from z0 (or zero)."""
        self.loading.delta[:] = -Theta
        z = np.zeros(self.n_z) if z0 is None else np.where(self.prob.fixed, 0.0, z0)
        with chs.direct_solver_up_to(self.n_z):
            z, rep = self.prob.solve(z, mode="hencky", tol=tol, max_it=max_it)
        g_W = rep["grad"].copy(); g_W[self.ith] -= self.k_th * (z[self.ith] - Theta)
        r = self._readings(z, g_W)
        return {"z": z, "Pi": float(rep["energy"]), "M": 2.0 * self.k_th * (Theta - r["theta"]), **r,
                **self._report(z, rep)}

    def solve_at_theta(self, theta: float, z0=None, tol: float = 1e-12, max_it: int = 80) -> dict:
        """The reference at a prescribed end rotation theta (rotation control, no loading spring): its moment is
        the reaction, M = 2 dW/dtheta."""
        z = np.zeros(self.n_z) if z0 is None else np.where(self.prob_th.fixed, 0.0, z0)
        z[self.ith] = theta
        with chs.direct_solver_up_to(self.n_z):
            z, rep = self.prob_th.solve(z, mode="hencky", tol=tol, max_it=max_it)
        r = self._readings(z, rep["grad"])
        return {"z": z, "W": float(rep["energy"]), "M": 2.0 * float(rep["grad"][self.ith]), **r,
                **self._report(z, rep)}

    def solve_at_ThetaD(self, ThetaD: float, theta0: float, z0=None, tol: float = 1e-12, max_it: int = 80,
                        rtol: float = 1e-9, max_solves: int = 12) -> dict:
        """The reference at a prescribed Theta_D: the end rotation theta with Theta_D(theta) = ThetaD, found by the
        secant method on rotation-control solves (Theta_D rises with theta), the first from theta0 (for instance
        read from the labelled path) and each solve from the previous one's field. Its moment is that solve's."""
        pts, z = [], z0
        th = float(theta0)
        for k in range(max_solves):
            r = self.solve_at_theta(th, z0=z, tol=tol, max_it=max_it)
            if not r["converged"]:
                return {**r, "solves": k + 1, "found": False}
            pts.append((th, r["ThetaD"]))
            z = r["z"]
            if abs(r["ThetaD"] - ThetaD) <= rtol * abs(ThetaD):
                return {**r, "solves": k + 1, "found": True}
            if len(pts) == 1:
                th = th * ThetaD / r["ThetaD"]
            else:
                (t0, d0), (t1, d1) = pts[-2], pts[-1]
                th = t1 + (ThetaD - d1) * (t1 - t0) / (d1 - d0)
        return {**r, "solves": max_solves, "found": False}

    def preload(self, N_target: float, tol: float = 1e-12, max_it: int = 80, rtol: float = 1e-10,
                max_fixed_point: int = 20) -> dict:
        """Pre-shortening delta, the same for every bolt, such that the bolts' mean force at theta = 0 is N_target
        (fixed point on delta). Sets it in this problem and returns it with the preload state's readings."""
        d = N_target / float(self.bolts.k[0])
        hist = []
        for _ in range(max_fixed_point):
            self.bolts.delta[:] = d
            r = self.solve_at_theta(0.0, tol=tol, max_it=max_it)
            N = np.array(r["bolt_N"])
            hist.append((d, float(N.mean())))
            if abs(N.mean() / N_target - 1.0) < rtol:
                break
            d = d * N_target / float(N.mean())
        return {"delta": d, "forces_N": N.tolist(), "fixed_point": hist, "z": r["z"], "converged": r["converged"],
                "on_target": bool(abs(N.mean() / N_target - 1.0) < rtol), "kkt": r["kkt"],
                "plastic_points": r["plastic_points"], "max_von_mises": r["max_von_mises"],
                "ThetaD_abs": r["ThetaD_abs"], "uzD": r["uzD"], "uzC": r["uzC"], "M": r["M"], "iterations": r["iterations"]}

    def evaluate(self, z: np.ndarray, Theta: float) -> dict:
        """Energy, moment readings, Theta_D and bolt forces of a field z whose fixed entries are zero and whose
        contact entries are >= 0 (any prediction of the network), at loading-device rotation Theta."""
        z = np.asarray(z, float)
        self.loading.delta[:] = -Theta
        E, g, _, info = self.prob.evaluate(z, "hencky", tangent=False)
        g_W = g.copy(); g_W[self.ith] -= self.k_th * (z[self.ith] - Theta)
        r = self._readings(z, g_W)
        return {"Pi": float(E), "M": 2.0 * self.k_th * (Theta - r["theta"]), **r,
                "plastic": np.concatenate([s._trial["plastic"].ravel() for s in self.solids])}


def make(q: Params, mesh=MESH, splice: str = "frictionless", k_th: float = 1.0, tol: float = 1e-12,
         max_it: int = 80):
    """The export of a member with its preload set: the model, a provisional export without preload, the preload
    by fixed point on that export's problem, and the final export. Returns (export, preload record)."""
    m = build(q, mesh, splice)
    P = ExportedProblem(export(m, q, k_th, 0.0))
    pre = P.preload(q.Np * 1e3, tol=tol, max_it=max_it)
    return export(m, q, k_th, pre["delta"], pre), pre


__all__ = ["build", "export", "make", "ExportedProblem", "KKT_KEYS", "FLAGS", "PARTS"]
