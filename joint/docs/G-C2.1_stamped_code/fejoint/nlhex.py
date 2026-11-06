"""Incompatible-mode hexahedra (fejoint.hex8i) with a nonlinear material at the Gauss points.

Each element carries its nine bubble parameters alpha, eliminated by static condensation as in the linear
element, but now from the nonlinear element equilibrium

    r_a(u_e, alpha) = sum_g B_a,g^T sigma(eps_g) det J_g = 0,      eps_g = B_u,g u_e + B_a,g alpha,

solved by Newton's method per element (all elements at once). The condensed element energy is the minimum over
alpha of sum_g W(eps_g) det J_g, convex in u_e when W is convex, and its gradient and Hessian are

    r_u = sum_g B_u^T sigma det J,   K_e = K_uu - K_ua K_aa^-1 K_au   (consistent tangent blocks),

by the envelope theorem at the converged alpha. With an elastic material this is exactly fejoint.hex8i.

Two modes:
  "hencky"  deformation theory: every evaluation returns from the virgin state, so the energy is the Hencky
            energy of the current displacement and no history is kept;
  "flow"    incremental flow theory: the return starts from the state of the last converged step (plastic
            strain and equivalent plastic strain at each Gauss point), and commit() stores the new state.
Units: N, mm, MPa.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from . import hex8i as H
from .plasticity import Material, radial_return


class PlasticHexSet:
    def __init__(self, nodes: np.ndarray, hexes: np.ndarray, mat: Material):
        self.nodes = np.asarray(nodes, float)
        self.hexes = np.asarray(hexes)
        self.mat = mat
        self.ne = self.hexes.shape[0]
        Kuu, Kua, Kaa, Bu, Ba, det = H.element_matrices(self.nodes[self.hexes], mat.D_el())
        self.Bu, self.Ba, self.det = Bu, Ba, det             # (8, E, 6, 24), (8, E, 6, 9), (8, E)
        self.Kaa_el, self.Kua_el = Kaa, Kua
        self.dofs = H.element_dofs(self.hexes)               # (E, 24)
        self.ep = np.zeros((self.ne, 8, 6))                  # committed state (flow theory)
        self.a = np.zeros((self.ne, 8))
        self.bub = np.zeros((self.ne, 9))                    # last bubble parameters (warm start)
        self._trial = None

    # ---- element level ------------------------------------------------------------------------------------
    def _strains(self, ue, alpha):
        return (np.einsum("geij,ej->egi", self.Bu, ue) + np.einsum("geij,ej->egi", self.Ba, alpha))   # (E, 8, 6)

    def _material(self, eps, mode, tangent=True):
        E_ = eps.shape[0]
        if mode == "hencky":
            epn, an = np.zeros((E_ * 8, 6)), np.zeros(E_ * 8)
        else:
            epn, an = self.ep.reshape(-1, 6), self.a.reshape(-1)
        sig, D, ep, a, W, pl = radial_return(eps.reshape(-1, 6), epn, an, self.mat, tangent=tangent)
        r = lambda v, s: v.reshape((E_, 8) + s)  # noqa: E731
        return r(sig, (6,)), (r(D, (6, 6)) if tangent else None), r(ep, (6,)), r(a, ()), r(W, ()), r(pl, ())

    def _material_sub(self, eps, mode, sel):
        """Energy densities (e, 8) for the elements sel only (used by the bubble line search)."""
        E_ = eps.shape[0]
        if mode == "hencky":
            epn, an = np.zeros((E_ * 8, 6)), np.zeros(E_ * 8)
        else:
            epn, an = self.ep[sel].reshape(-1, 6), self.a[sel].reshape(-1)
        W = radial_return(eps.reshape(-1, 6), epn, an, self.mat, tangent=False)[4]
        return W.reshape(E_, 8)

    def evaluate(self, u: np.ndarray, mode: str = "hencky", tangent: bool = True, tol: float = 1e-11,
                 max_it: int = 60):
        """Energy, residual (3n,) and condensed tangent (sparse 3n x 3n or None) of the set at the nodal
        displacement u (3n,). The trial state is kept for commit()."""
        assert mode in ("hencky", "flow")
        ue = u[self.dofs]
        if self.mat.elastic:                                 # exact one-step condensation from the elastic blocks
            alpha = -np.linalg.solve(self.Kaa_el, np.einsum("eji,ej->ei", self.Kua_el, ue)[..., None])[..., 0]
            it_used = 0
        else:
            alpha = self.bub.copy()
            scale = np.maximum(np.abs(ue).max(axis=1), 1e-300)
            # a tiny shift keeps the bubble Hessian invertible where every point of an element sits on a yield
            # plateau (zero hardening); it changes the Newton path, not the root r_a = 0
            shift = 1e-9 * np.einsum("eii->e", self.Kaa_el)[:, None, None] / 9.0 * np.eye(9)[None]
            it_used = 0
            # damped Newton per element on the convex element energy min_alpha sum_g W(eps_g) det J_g
            for it in range(max_it):
                eps = self._strains(ue, alpha)
                sig, D, _, _, W, _ = self._material(eps, mode)
                Ee = np.einsum("eg,ge->e", W, self.det)
                ra = np.einsum("geij,egi,ge->ej", self.Ba, sig, self.det)
                Kaa = np.einsum("geji,egjk,gekl,ge->eil", self.Ba, D, self.Ba, self.det) + shift
                da = -np.linalg.solve(Kaa, ra[..., None])[..., 0]
                slope = np.einsum("ej,ej->e", ra, da)
                t = np.ones(self.ne)
                todo = np.ones(self.ne, bool)
                for _ in range(40):
                    at = alpha[todo] + t[todo, None] * da[todo]
                    eps_t = (np.einsum("geij,ej->egi", self.Bu[:, todo], ue[todo])
                             + np.einsum("geij,ej->egi", self.Ba[:, todo], at))
                    Et = np.einsum("eg,ge->e", self._material_sub(eps_t, mode, todo), self.det[:, todo])
                    ok = Et <= Ee[todo] + 1e-4 * t[todo] * slope[todo] + 1e-13 * np.abs(Ee[todo])
                    idx = np.nonzero(todo)[0]
                    t[idx[~ok]] *= 0.5
                    todo[idx[ok]] = False
                    if not todo.any():
                        break
                step = t[:, None] * da
                alpha = alpha + step
                it_used = it + 1
                if np.all(np.abs(step).max(axis=1) <= tol * scale):
                    break
            else:
                raise RuntimeError("bubble condensation did not converge")
        eps = self._strains(ue, alpha)
        sig, D, ep, a, W, pl = self._material(eps, mode, tangent=tangent)
        energy = float(np.einsum("eg,ge->", W, self.det))
        re = np.einsum("geij,egi,ge->ej", self.Bu, sig, self.det)              # (E, 24)
        R = np.zeros(u.size)
        np.add.at(R, self.dofs, re)
        K = None
        if tangent:
            DBu = np.einsum("egij,gejk->egik", D, self.Bu)
            DBa = np.einsum("egij,gejk->egik", D, self.Ba)
            Kuu = np.einsum("geji,egjk,ge->eik", self.Bu, DBu, self.det)
            Kua = np.einsum("geji,egjk,ge->eik", self.Bu, DBa, self.det)
            Kaa = np.einsum("geji,egjk,ge->eik", self.Ba, DBa, self.det)
            Ke = Kuu - Kua @ np.linalg.solve(Kaa, np.transpose(Kua, (0, 2, 1)))
            Ke = 0.5 * (Ke + np.transpose(Ke, (0, 2, 1)))
            rows = np.repeat(self.dofs, 24, axis=1).ravel()
            cols = np.tile(self.dofs, (1, 24)).ravel()
            K = sp.coo_matrix((Ke.ravel(), (rows, cols)), shape=(u.size, u.size)).tocsr()
        self._trial = {"ep": ep, "a": a, "bub": alpha, "sig": sig, "eps": eps, "plastic": pl}
        return energy, R, K, {"bubble_iterations": it_used, "plastic_points": int(pl.sum())}

    def commit(self):
        """Store the last evaluated state as the converged state of this step (flow theory) and as the warm start."""
        t = self._trial
        self.ep, self.a, self.bub = t["ep"].copy(), t["a"].copy(), t["bub"].copy()

    def warm(self):
        """Keep only the bubble warm start from the last evaluation (deformation theory)."""
        self.bub = self._trial["bub"].copy()

    def snapshot(self):
        return {"ep": self.ep.copy(), "a": self.a.copy(), "bub": self.bub.copy()}

    def restore(self, s):
        self.ep, self.a, self.bub = s["ep"].copy(), s["a"].copy(), s["bub"].copy()


__all__ = ["PlasticHexSet"]
