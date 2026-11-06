"""The energy of an exported stage C2 instance in torch, for training (c2.instance holds the reference in numpy).

Deformation theory in closed form. With e the deviatoric strain (tensor components) and ebar = sqrt(2/3 e:e), the
Hencky energy density is W = kappa/2 (tr eps)^2 + Phi(ebar), where Phi' = q(ebar) is the von Mises stress:
Phi = 3/2 G ebar^2 up to the first yield, ebar_0 = sigma_0 / (3 G), then piecewise quadratic, with q piecewise
linear of slope 3 G h_k / (3 G + h_k) on the segment where the hardening slope is h_k (positive everywhere in the
family). This is the energy fejoint.plasticity returns from the virgin state (tests/test_c2.py checks it).

The bubble parameters of each element are found by damped Newton steps on the element energy without gradient
tracking, then held fixed. At the minimiser the gradient with respect to the nodal displacements is the envelope
gradient, so autograd through the strains gives the training gradient. With any bubble values the energy is an
upper bound of the condensed energy, which is the minimum over them.

All functions take a batch of fields of one instance: z (B, n_z) -> energies (B,), with the loading spring
1/2 k_s (e - D)^2 of each field's loading-device displacement D (B,) (c2.instance).
"""
from __future__ import annotations

import numpy as np


def _t():
    import torch
    return torch


class HenckyLaw:
    """Closed-form piecewise-quadratic Phi(ebar) of a hardening curve (alpha_k, sigma_k, final slope), E, nu."""

    def __init__(self, alpha, sigma, h_end, E, nu, device, dtype):
        torch = _t()
        G = E / (2 * (1 + nu)); Kb = E / (3 * (1 - 2 * nu))
        alpha, sigma = np.asarray(alpha, float), np.asarray(sigma, float)
        h = np.r_[np.diff(sigma) / np.diff(alpha), h_end] if alpha.size > 1 else np.array([h_end])
        assert (h > 0).all(), "the closed form needs a positive hardening slope everywhere"
        eb = sigma / (3 * G) + alpha                         # breakpoints in ebar
        s = 3 * G * h / (3 * G + h)                          # dq / d ebar on each plastic segment
        phi = np.empty(eb.size)
        phi[0] = 1.5 * G * eb[0] ** 2
        for k in range(eb.size - 1):
            dk = eb[k + 1] - eb[k]
            phi[k + 1] = phi[k] + sigma[k] * dk + 0.5 * s[k] * dk * dk
        f = lambda a: torch.as_tensor(a, dtype=dtype, device=device)  # noqa: E731
        self.G, self.K = G, Kb
        self.eb, self.sig, self.s, self.phi = f(eb), f(sigma), f(s), f(phi)
        Id = np.zeros((6, 6)); Id[:3, :3] = -1.0 / 3.0; Id[range(3), range(3)] = 2.0 / 3.0; Id[3, 3] = Id[4, 4] = Id[5, 5] = 0.5
        Mv = np.array([1.0, 1, 1, 0, 0, 0])
        self.Id, self.KMM = f(Id), f(Kb * np.outer(Mv, Mv))

    @staticmethod
    def _dev(eps):
        torch = _t()
        tr = eps[..., 0] + eps[..., 1] + eps[..., 2]
        m = tr / 3.0
        e = torch.stack([eps[..., 0] - m, eps[..., 1] - m, eps[..., 2] - m,
                         0.5 * eps[..., 3], 0.5 * eps[..., 4], 0.5 * eps[..., 5]], dim=-1)   # tensor components
        e2 = (e[..., :3] ** 2).sum(-1) + 2.0 * (e[..., 3:] ** 2).sum(-1)
        return tr, e, e2

    def energy(self, eps):
        """eps (..., 6) engineering Voigt -> W (...)."""
        torch = _t()
        tr, _, e2 = self._dev(eps)
        eb = torch.sqrt(2.0 / 3.0 * e2 + 1e-30)
        k = torch.clamp(torch.searchsorted(self.eb, eb.detach().contiguous(), right=True) - 1, min=0)
        d = eb - self.eb[k]
        plastic = eb > self.eb[0]
        Phi = torch.where(plastic, self.phi[k] + self.sig[k] * d + 0.5 * self.s[k] * d * d, 1.5 * self.G * eb * eb)
        return 0.5 * self.K * tr * tr + Phi

    def stress_tangent(self, eps):
        """sig (..., 6) and the tangent D (..., 6, 6), closed form (no autograd)."""
        torch = _t()
        tr, e, e2 = self._dev(eps)
        eb = torch.sqrt(2.0 / 3.0 * e2 + 1e-30)
        k = torch.clamp(torch.searchsorted(self.eb, eb.contiguous(), right=True) - 1, min=0)
        plastic = eb > self.eb[0]
        q = torch.where(plastic, self.sig[k] + self.s[k] * (eb - self.eb[k]), 3.0 * self.G * eb)
        qp = torch.where(plastic, self.s[k], torch.full_like(eb, 3.0 * self.G))
        phi = torch.where(plastic, 2.0 / 3.0 * q / eb, torch.full_like(eb, 2.0 * self.G))
        c2 = torch.where(plastic, 4.0 / 9.0 * (qp * eb - q) / eb ** 3, torch.zeros_like(eb))
        sig = phi[..., None] * e
        sig = torch.cat([sig[..., :3] + (self.K * tr)[..., None], sig[..., 3:]], dim=-1)
        D = self.KMM + phi[..., None, None] * self.Id + c2[..., None, None] * (e[..., :, None] * e[..., None, :])
        return sig, D


class ElementSet:
    """The B matrices of one material set of an instance (computed by fejoint.hex8i in float64), on a device."""

    def __init__(self, nodes, hexes, law: HenckyLaw, device, dtype):
        torch = _t()
        from fejoint import hex8i as H
        G, Kb = law.G, law.K
        E = 9 * Kb * G / (3 * Kb + G); nu = (3 * Kb - 2 * G) / (2 * (3 * Kb + G))
        _, Kua, Kaa, Bu, Ba, det = H.element_matrices(np.asarray(nodes)[np.asarray(hexes)], H.elastic_D(E, nu))
        C = -np.linalg.solve(Kaa, np.transpose(Kua, (0, 2, 1)))           # elastic condensation alpha = C u_e
        f = lambda a: torch.as_tensor(np.ascontiguousarray(a), dtype=dtype, device=device)  # noqa: E731
        self.Bu, self.Ba, self.det, self.C = f(Bu), f(Ba), f(det), f(C)    # (8,E,6,24), (8,E,6,9), (8,E), (E,9,24)
        self.dofs = torch.as_tensor(H.element_dofs(np.asarray(hexes)), dtype=torch.long, device=device)
        self.law = law
        self.shift = f(1e-9 * np.einsum("eii->e", Kaa) / 9.0)
        self.eye9 = torch.eye(9, dtype=dtype, device=device)

    def strains(self, ue, alpha):                     # (B,E,24), (B,E,9) -> (B,E,8,6)
        torch = _t()
        return torch.einsum("geij,bej->begi", self.Bu, ue) + torch.einsum("geij,bej->begi", self.Ba, alpha)

    def element_energy(self, ue, alpha):              # -> (B,E)
        torch = _t()
        return torch.einsum("beg,ge->be", self.law.energy(self.strains(ue, alpha)), self.det)

    def bubbles(self, ue, iters: int = 10, halvings: int = 8):
        """Damped Newton on every element energy, no gradient tracking. ue (B,E,24) -> alpha (B,E,9). A step is
        taken only where it satisfies the Armijo condition (up to round-off), so no element energy increases."""
        torch = _t()
        with torch.no_grad():
            alpha = torch.einsum("eij,bej->bei", self.C, ue)
            for _ in range(iters):
                eps = self.strains(ue, alpha)
                sig, D = self.law.stress_tangent(eps)
                ra = torch.einsum("geij,begi,ge->bej", self.Ba, sig, self.det)
                Kaa = torch.einsum("geji,begjk,gekl,ge->beil", self.Ba, D, self.Ba, self.det)
                Kaa = Kaa + self.shift[None, :, None, None] * self.eye9
                da = -torch.linalg.solve(Kaa, ra[..., None])[..., 0]
                E0 = torch.einsum("beg,ge->be", self.law.energy(eps), self.det)
                slope = (ra * da).sum(-1)
                tol = 1e-7 * E0.abs() if E0.dtype == torch.float32 else 1e-13 * E0.abs()
                t = torch.ones_like(E0)
                for _h in range(halvings):
                    ok = self.element_energy(ue, alpha + t[..., None] * da) <= E0 + 1e-4 * t * slope + tol
                    if bool(ok.all()):
                        break
                    t = torch.where(ok, t, 0.5 * t)
                else:
                    ok = self.element_energy(ue, alpha + t[..., None] * da) <= E0 + 1e-4 * t * slope + tol
                    t = torch.where(ok, t, torch.zeros_like(t))
                alpha = alpha + torch.where(t[..., None] > 0, t[..., None] * da, torch.zeros_like(da))
        return alpha

    def energy(self, u, iters: int = 10):              # u (B, 3n) -> (B,)
        ue = u[:, self.dofs]
        alpha = self.bubbles(ue.detach(), iters=iters)
        return self.element_energy(ue, alpha).sum(-1)


class BoltSprings:
    """The half bolts' axial springs (fejoint.nlsolve.AxialSprings): energy phi(a + delta) of each head unknown a."""

    def __init__(self, k, e_pts, N_pts, h_end, delta, device, dtype):
        torch = _t()
        e_pts, N_pts = np.asarray(e_pts, float), np.asarray(N_pts, float)
        slopes = np.r_[np.diff(N_pts) / np.diff(e_pts), h_end]
        cum = np.r_[0.0, np.cumsum(0.5 * (N_pts[:-1] + N_pts[1:]) * np.diff(e_pts))] + 0.5 * N_pts[0] * e_pts[0]
        f = lambda a: torch.as_tensor(a, dtype=dtype, device=device)  # noqa: E731
        self.k, self.delta = float(k), float(delta)
        self.e, self.N, self.sl, self.cum = f(e_pts), f(N_pts), f(slopes), f(cum)

    def force(self, a):
        torch = _t()
        e = a + self.delta
        j = torch.clamp(torch.searchsorted(self.e, e.detach().contiguous(), right=True) - 1, min=0)
        return torch.where(e > self.e[0], self.N[j] + self.sl[j] * (e - self.e[j]), self.k * e)

    def energy(self, a):                               # (B, nb) -> (B,)
        torch = _t()
        e = a + self.delta
        j = torch.clamp(torch.searchsorted(self.e, e.detach().contiguous(), right=True) - 1, min=0)
        d = e - self.e[j]
        return torch.where(e > self.e[0], self.cum[j] + self.N[j] * d + 0.5 * self.sl[j] * d * d,
                           0.5 * self.k * e * e).sum(-1)


def sparse(row, col, val, shape, device, dtype):
    torch = _t()
    idx = torch.as_tensor(np.vstack([row, col]), dtype=torch.long)
    return torch.sparse_coo_tensor(idx, torch.as_tensor(val, dtype=dtype), tuple(int(s) for s in shape),
                                   check_invariants=True).coalesce().to(device)


class InstanceEnergy:
    """Pi(z) of one exported instance (the dict of c2.instance.export) for a batch of fields z (B, n_z)."""

    def __init__(self, ex: dict, device="cpu", dtype=None):
        torch = _t()
        dtype = torch.float32 if dtype is None else dtype
        self.device, self.dtype = device, dtype
        E, nu = float(ex["E"]), float(ex["nu"])
        lf = HenckyLaw(ex["hard_f_alpha"], ex["hard_f_sigma"], float(ex["hard_f_hend"]), E, nu, device, dtype)
        lw = HenckyLaw(ex["hard_w_alpha"], ex["hard_w_sigma"], float(ex["hard_w_hend"]), E, nu, device, dtype)
        self.sets = [ElementSet(ex["nodes"], ex["hexes_f"], lf, device, dtype),
                     ElementSet(ex["nodes"], ex["hexes_w"], lw, device, dtype)]
        self.T = sparse(ex["T_row"], ex["T_col"], ex["T_val"], ex["T_shape"], device, dtype)
        self.K = sparse(ex["K_row"], ex["K_col"], ex["K_val"], ex["K_shape"], device, dtype)
        self.head = torch.as_tensor(np.asarray(ex["head"]).ravel(), dtype=torch.long, device=device)
        self.bolts = BoltSprings(float(ex["k_ax"]), ex["bolt_e"], ex["bolt_N"], float(ex["bolt_hend"]),
                                 float(ex["delta"]), device, dtype)
        self.e_idx, self.k_s = int(ex["e_idx"]), float(ex["k_s"])

    def physical(self, z):                             # (B, n_z) -> (B, 3n)
        torch = _t()
        return torch.sparse.mm(self.T, z.T.contiguous()).T

    def energy(self, z, D, iters: int = 10):           # (B, n_z), (B,) -> (B,)
        torch = _t()
        u = self.physical(z)
        E = 0.5 * (z * torch.sparse.mm(self.K, z.T.contiguous()).T).sum(-1)
        for s in self.sets:
            E = E + s.energy(u, iters=iters)
        return E + self.bolts.energy(z[:, self.head]) + 0.5 * self.k_s * (z[:, self.e_idx] - D) ** 2


__all__ = ["HenckyLaw", "ElementSet", "BoltSprings", "InstanceEnergy", "sparse"]
