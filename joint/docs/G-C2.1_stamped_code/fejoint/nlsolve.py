"""Convex nonlinear problems with frictionless unilateral contact: sequential quadratic programming.

Unknowns z (reduced coordinates, as the linear models build them: separations in the slots of contact nodes,
bolt-head unknowns, and so on). The physical nodal displacement is u = T z. The energy is

    Pi(z) = sum_sets E_set(T z) + 1/2 z^T K_lin z - f^T z,

E_set the condensed energy of a PlasticHexSet (convex for deformation theory, and per step for flow theory),
K_lin the linear part (elastic bodies, springs, bolt heads; positive semi-definite), f the loads. Constraints:
z_c >= 0 on the contact unknowns c, and z_d = prescribed values on the Dirichlet unknowns d (displacement
control lives here). The feasible set is convex.

Each iteration solves the contact problem of the second-order model with the primal-dual active set method
(fejoint.contact.solve_signorini), then backtracks along the step until the energy decreases enough (Armijo).
Both ends of the step are feasible, so every trial point is. A trial point a set cannot evaluate counts as an
infinite energy. When the predicted decrease is below the round-off of the energy, the full step is taken. With a
convex energy every accepted step lowers Pi (up to round-off), and the iteration stops when a full Newton step is
negligible; the optimality residuals of the nonlinear problem are reported at the end, as fejoint.contact reports
them for the linear one.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from .contact import solve_signorini


class ContactProblem:
    def __init__(self, T: sp.spmatrix, K_lin: sp.spmatrix, f: np.ndarray, sets: list, fixed: np.ndarray,
                 cidx: np.ndarray):
        self.T = T.tocsr()
        self.TT = self.T.T.tocsr()
        self.K_lin = K_lin.tocsr()
        self.f = np.asarray(f, float)
        self.sets = list(sets)
        self.fixed = np.asarray(fixed, bool)
        self.cidx = np.asarray(cidx, int)
        n = self.f.size
        assert self.T.shape[1] == n and self.K_lin.shape == (n, n) and self.fixed.size == n
        assert not self.fixed[self.cidx].any(), "a contact unknown is also prescribed"
        self.free = np.nonzero(~self.fixed)[0]
        self.pos = -np.ones(n, int); self.pos[self.free] = np.arange(self.free.size)
        self.c_free = self.pos[self.cidx]

    def evaluate(self, z, mode, tangent=True):
        u = self.T @ z
        E = 0.5 * float(z @ (self.K_lin @ z)) - float(self.f @ z)
        g = self.K_lin @ z - self.f
        Hs = self.K_lin.copy() if tangent else None
        info = []
        for s in self.sets:
            if getattr(s, "reduced", False):                 # acts on the reduced unknowns directly
                e, R, K, inf = s.evaluate(z, mode=mode, tangent=tangent)
                E += e
                g = g + R
                if tangent:
                    Hs = Hs + K
            else:
                e, R, K, inf = s.evaluate(u, mode=mode, tangent=tangent)
                E += e
                g = g + self.TT @ R
                if tangent:
                    Hs = Hs + (self.TT @ K @ self.T)
            info.append(inf)
        return E, g, (Hs.tocsr() if tangent else None), info

    def solve(self, z0: np.ndarray, mode: str = "hencky", tol: float = 1e-10, max_it: int = 60,
              armijo: float = 1e-4, verbose: bool = False):
        """Minimise from z0, whose prescribed entries are already set. Returns (z, report)."""
        z = np.asarray(z0, float).copy()
        assert (z[self.cidx] >= -1e-12).all(), "the starting point violates a contact constraint"
        z[self.cidx] = np.maximum(z[self.cidx], 0.0)
        hist = []
        E, g, Hm, info = self.evaluate(z, mode)
        for s in self.sets:
            s.warm()
        active0 = None
        converged = False
        for it in range(1, max_it + 1):
            A = Hm[self.free][:, self.free].tocsr()
            sol = solve_signorini(A, -g[self.free], self.c_free, g=z[self.cidx], active0=active0)
            active0 = sol["active"]
            dz = np.zeros_like(z); dz[self.free] = sol["x"]
            slope = float(g @ dz)
            step_norm = float(np.abs(dz).max())
            zscale = max(float(np.abs(z).max()), 1e-300)
            if step_norm <= tol * zscale:
                converged = True
                hist.append({"it": it, "E": E, "step": step_norm, "t": 0.0})
                break
            t = 1.0
            if -slope > 1e-13 * max(abs(E), 1e-300):
                # Armijo backtracking. Near the optimum the predicted decrease falls below what the energy can
                # resolve (round-off of E); there the test is noise, so the full Newton step is taken instead.
                while True:
                    zt = z + t * dz
                    zt[self.cidx] = np.maximum(zt[self.cidx], 0.0)    # round-off only: both ends feasible
                    try:
                        Et, _, _, _ = self.evaluate(zt, mode, tangent=False)
                    except RuntimeError:          # a set could not evaluate this trial point (bubbles): shorten it
                        Et = np.inf
                    if np.isfinite(Et) and (Et <= E + armijo * t * slope or t < 1e-8):
                        break
                    if t < 1e-8:
                        break
                    t *= 0.5
                if not np.isfinite(Et):           # no evaluable point along the step: stop, not converged
                    break
            zt = z + t * dz
            zt[self.cidx] = np.maximum(zt[self.cidx], 0.0)
            z = zt
            E, g, Hm, info = self.evaluate(z, mode)
            for s in self.sets:
                s.warm()
            hist.append({"it": it, "E": E, "step": step_norm, "t": t, "slope": slope,
                         "plastic_points": [i["plastic_points"] for i in info]})
            if verbose:
                print(hist[-1], flush=True)
            if t == 1.0 and step_norm <= tol * zscale:      # converged only on a full step
                converged = True
                break
        rep = self.kkt(z, g)
        rep.update({"iterations": len(hist), "converged": converged, "energy": E, "history": hist,
                    "grad": g, "plastic_points": [i["plastic_points"] for i in info]})
        return z, rep

    def kkt(self, z, g):
        """Optimality residuals of the nonlinear problem at z, relative to the largest force and displacement
        components: contact gaps >= 0, multipliers >= 0, complementarity, equilibrium elsewhere."""
        free = self.free
        lam = np.zeros_like(z); lam[free] = g[free]
        fscale = max(float(np.abs(g[self.fixed]).max()) if self.fixed.any() else 0.0, float(np.abs(self.f).max()),
                     1e-300)
        uscale = max(float(np.abs(z).max()), 1e-300)
        other = np.ones(z.size, bool); other[self.cidx] = False; other[self.fixed] = False
        act = z[self.cidx] <= 1e-12 * uscale
        return {"min_gap": float(z[self.cidx].min() / uscale) if self.cidx.size else 0.0,
                "min_lambda": float(lam[self.cidx].min() / fscale) if self.cidx.size else 0.0,
                "max_complementarity": float(np.abs(lam[self.cidx] * z[self.cidx]).max() / (fscale * uscale))
                if self.cidx.size else 0.0,
                "max_lambda_inactive": float(np.abs(lam[self.cidx[~act]]).max() / fscale) if (~act).any() else 0.0,
                "max_residual_unconstrained": float(np.abs(lam[other]).max() / fscale) if other.any() else 0.0}



class AxialSprings:
    """Bolts as axial springs on chosen reduced unknowns z_i, with a pre-shortening delta_i:
    extension e_i = z_i + delta_i, force N(e), energy phi(e) = int_0^e N. Elastic, or elastic-plastic with a
    non-decreasing force-extension curve after yield (convex phi), taken in deformation-theory form in both
    modes (valid while each bolt's extension does not decrease, which every run reports). Reduced-coordinate set
    for ContactProblem."""
    reduced = True

    def __init__(self, idx, n, k, N_curve=None, delta=None):
        self.idx = np.asarray(idx, int)
        self.n = int(n)
        self.k = np.broadcast_to(np.asarray(k, float), self.idx.shape).copy()
        self.delta = np.zeros(self.idx.size) if delta is None else np.asarray(delta, float).copy()
        self.curve = N_curve                         # None, or (e_pts, N_pts, slope_end): N(e) beyond e_pts[0]

    def _law(self, e):
        k = self.k
        N, kt, phi = k * e, k.copy(), 0.5 * k * e * e
        if self.curve is None:
            return N, kt, phi
        e_p, N_p, s_end = self.curve
        e_p, N_p = np.asarray(e_p, float), np.asarray(N_p, float)
        slopes = np.r_[np.diff(N_p) / np.diff(e_p), s_end]
        cum = np.r_[0.0, np.cumsum(0.5 * (N_p[:-1] + N_p[1:]) * np.diff(e_p))] + 0.5 * N_p[0] * e_p[0]
        y = e > e_p[0]
        if y.any():
            ey = e[y]
            j = np.clip(np.searchsorted(e_p, ey, side="right") - 1, 0, e_p.size - 1)
            d = ey - e_p[j]
            N[y] = N_p[j] + slopes[j] * d
            kt[y] = slopes[j]
            phi[y] = cum[j] + N_p[j] * d + 0.5 * slopes[j] * d * d
        return N, kt, phi

    def evaluate(self, z, mode="hencky", tangent=True):
        e = z[self.idx] + self.delta
        N, kt, phi = self._law(e)
        g = np.zeros(self.n); np.add.at(g, self.idx, N)
        K = sp.coo_matrix((kt, (self.idx, self.idx)), shape=(self.n, self.n)).tocsr() if tangent else None
        self._last = {"N": N, "e": e}
        return float(phi.sum()), g, K, {"plastic_points": int((e > (self.curve[0][0] if self.curve else np.inf)).sum())}

    def warm(self):
        pass

    def commit(self):
        pass

    def snapshot(self):
        return {}

    def restore(self, s):
        pass


__all__ = ["ContactProblem", "AxialSprings"]
