"""The elastic contact step of an exported member (development draft, exploratory, nothing stamped).

For a field z and the gradient g of the energy at z, the step d minimises the quadratic model

    1/2 d' K0 d + g' d    subject to    z_c + d_c >= 0 on the contact unknowns,

with K0 the tangent of the member at its preload state (the elastic stiffness with the bolts and the loading spring).
For a linear elastic member in frictionless unilateral contact z + d is the solution itself; with plasticity it is a
modified Newton step. The step needs no reference solution and no solve of the nonlinear problem: one sparse
factorisation of K0 with the contact unknowns held, and the dense Schur complement on the contact unknowns, both made
once for a member; then two sparse back-substitutions and a small dense active-set solve for every step.

The quadratic problem is solved by the primal-dual active set iteration of fejoint.contact.solve_signorini, written on
the Schur complement. It starts from every contact held, as that function does.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse.linalg as spla

from .instance import ExportedProblem


class ElasticContactStep:
    def __init__(self, ex: dict, z_pre: np.ndarray):
        P = ExportedProblem(ex)
        for s in P.solids:
            s.bub[:] = 0.0
            s._trial = None
        P.loading.delta[:] = 0.0
        _, _, K0, _ = P.prob.evaluate(np.asarray(z_pre, float), "hencky", tangent=True)
        prob = P.prob
        self.n_z = K0.shape[0]
        self.free, self.cidx = prob.free, prob.cidx
        A = K0.tocsr()[self.free][:, self.free].tocsc()
        c = np.asarray(prob.c_free, int)
        inner = np.ones(A.shape[0], bool); inner[c] = False
        i = np.nonzero(inner)[0]
        self.i, self.c = i, c
        self.lu = spla.splu(A[i][:, i].tocsc())
        self.Aic = A[i][:, c].tocsc()
        self.Aci = A[c][:, i].tocsr()
        Acc = A[c][:, c].toarray()
        S = np.empty_like(Acc)
        for j in range(c.size):                                  # the Schur complement, a column at a time
            S[:, j] = Acc[:, j] - self.Aci @ self.lu.solve(self.Aic[:, j].toarray().ravel())
        self.S = 0.5 * (S + S.T)
        self.rho = float(np.diag(self.S).mean())

    def _reduced(self, ghat: np.ndarray, lo: np.ndarray, max_it: int = 100):
        """min 1/2 d'S d + ghat'd subject to d >= lo (lo <= 0), by the primal-dual active set iteration."""
        S, n = self.S, lo.size
        act = np.ones(n, bool)
        for it in range(1, max_it + 1):
            d = np.where(act, lo, 0.0)
            ina = ~act
            if ina.any():
                d[ina] = np.linalg.solve(S[np.ix_(ina, ina)], -ghat[ina] - S[np.ix_(ina, act)] @ lo[act])
            lam = S @ d + ghat
            new = (lam - self.rho * (d - lo)) > 0
            if np.array_equal(new, act):
                return d, act, it
            act = new
        return d, act, max_it

    def step(self, z: np.ndarray, g: np.ndarray):
        """z, g (n_z,): the step d (n_z,), zero on the fixed unknowns, with its active set and its iterations."""
        zf, gf = np.asarray(z, float)[self.free], np.asarray(g, float)[self.free]
        gi, gc = gf[self.i], gf[self.c]
        ghat = gc - self.Aci @ self.lu.solve(gi)
        lo = -np.maximum(zf[self.c], 0.0)
        dc, act, its = self._reduced(ghat, lo)
        di = -self.lu.solve(gi + self.Aic @ dc)
        df = np.zeros_like(zf); df[self.i] = di; df[self.c] = dc
        d = np.zeros(self.n_z); d[self.free] = df
        return d, act, its


__all__ = ["ElasticContactStep"]
