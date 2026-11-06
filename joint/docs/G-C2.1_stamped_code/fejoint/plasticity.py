"""Small-strain J2 plasticity at the integration points: deformation theory and incremental flow theory.

One radial-return routine serves both. Flow theory: one backward-Euler step from the state of the previous load
step (strain-driven, Simo and Hughes 1998, Box 3.2). Deformation theory (Hencky): the same step taken from the
virgin state, which gives the J2 deformation-theory stress for any non-decreasing isotropic hardening curve
(stage C2 theory check, 5 November 2026). Each call also returns the incremental potential density, whose
derivative with respect to the strain is the returned stress (Ortiz and Stainier 1999):

    W_n(eps) = kappa/2 (tr eps)^2 + q^2 / (6 G) + Psi(alpha) - Psi(alpha_n),   Psi(alpha) = int_0^alpha sigma_y(a) da,

q the von Mises stress after the return and alpha the equivalent plastic strain after it. From the virgin state
this is the Hencky energy, convex in eps whenever sigma_y is non-decreasing.

Hardening: isotropic, sigma_y(alpha) piecewise linear through the points (alpha_k, sigma_k), alpha_0 = 0, and a
final slope beyond the last point. Non-decreasing curves only (convexity).

Voigt order as fejoint.hex8i: strains [e_xx, e_yy, e_zz, g_xy, g_yz, g_zx] with engineering shears; stresses
[s_xx, s_yy, s_zz, s_xy, s_yz, s_zx]. Plastic strains are stored in the same engineering form as the strains.
Units: MPa, mm.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

M = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0])
IDEV = np.zeros((6, 6))
IDEV[:3, :3] = -1.0 / 3.0
IDEV[np.arange(3), np.arange(3)] = 2.0 / 3.0
IDEV[3, 3] = IDEV[4, 4] = IDEV[5, 5] = 0.5


@dataclass
class Hardening:
    """sigma_y(alpha): piecewise linear through (alpha_k, sigma_k), alpha_0 = 0, then slope h_end."""
    alpha: np.ndarray
    sigma: np.ndarray
    h_end: float = 0.0

    def __post_init__(self):
        self.alpha = np.asarray(self.alpha, dtype=float)
        self.sigma = np.asarray(self.sigma, dtype=float)
        assert self.alpha[0] == 0.0 and np.all(np.diff(self.alpha) > 0), "alpha must start at 0 and increase"
        assert np.all(np.diff(self.sigma) >= 0) and self.h_end >= 0, "hardening must not decrease (convexity)"
        slopes = np.diff(self.sigma) / np.diff(self.alpha)
        self.slopes = np.r_[slopes, self.h_end]                              # slope on [alpha_k, alpha_k+1)
        seg = 0.5 * (self.sigma[:-1] + self.sigma[1:]) * np.diff(self.alpha)
        self.cum = np.r_[0.0, np.cumsum(seg)]                                 # Psi at the breakpoints

    @classmethod
    def bilinear(cls, sy0: float, H: float) -> "Hardening":
        return cls(np.array([0.0]), np.array([sy0]), h_end=H)

    def _k(self, a):
        return np.clip(np.searchsorted(self.alpha, a, side="right") - 1, 0, self.alpha.size - 1)

    def sy(self, a):
        k = self._k(a)
        return self.sigma[k] + self.slopes[k] * (a - self.alpha[k])

    def slope(self, a):
        return self.slopes[self._k(a)]

    def Psi(self, a):
        k = self._k(a)
        d = a - self.alpha[k]
        return self.cum[k] + self.sigma[k] * d + 0.5 * self.slopes[k] * d * d


@dataclass
class Material:
    E: float
    nu: float
    hardening: Hardening | None = None             # None: elastic

    @property
    def G(self): return self.E / (2.0 * (1.0 + self.nu))
    @property
    def K(self): return self.E / (3.0 * (1.0 - 2.0 * self.nu))
    @property
    def elastic(self): return self.hardening is None

    def D_el(self):
        return self.K * np.outer(M, M) + 2.0 * self.G * IDEV


def _ddot(a, b):
    return (a[..., 0] * b[..., 0] + a[..., 1] * b[..., 1] + a[..., 2] * b[..., 2]
            + 2.0 * (a[..., 3] * b[..., 3] + a[..., 4] * b[..., 4] + a[..., 5] * b[..., 5]))


def radial_return(eps, ep_n, a_n, mat: Material, tangent: bool = True):
    """One backward-Euler J2 step at every point.

    eps (P, 6) total strain; ep_n (P, 6) plastic strain and a_n (P,) equivalent plastic strain of the previous
    step (zeros for deformation theory). Returns sig (P, 6), D (P, 6, 6) consistent tangent (or None), ep (P, 6),
    a (P,), W (P,) incremental potential density, plastic (P,) bool."""
    eps = np.asarray(eps, dtype=float)
    P = eps.shape[0]
    G, Kb = mat.G, mat.K
    ee = eps - ep_n
    tr = ee[:, 0] + ee[:, 1] + ee[:, 2]
    e = ee.copy()
    e[:, :3] -= tr[:, None] / 3.0
    e[:, 3:] *= 0.5                                         # tensor components
    s_tr = 2.0 * G * e
    q_tr = np.sqrt(1.5 * np.maximum(_ddot(s_tr, s_tr), 0.0))
    if mat.elastic:
        sig = s_tr.copy(); sig[:, :3] += (Kb * tr)[:, None]
        W = 0.5 * Kb * tr ** 2 + q_tr ** 2 / (6.0 * G)
        D = np.broadcast_to(mat.D_el(), (P, 6, 6)).copy() if tangent else None
        return sig, D, ep_n.copy(), a_n.copy(), W, np.zeros(P, bool)
    hd = mat.hardening
    f_tr = q_tr - hd.sy(a_n)
    pl = f_tr > 1e-12 * np.maximum(hd.sigma[0], 1.0)
    dg = np.zeros(P)
    if pl.any():
        qi, ai, fi = q_tr[pl], a_n[pl], f_tr[pl]
        lo, hi = np.zeros(qi.size), qi / (3.0 * G)          # phi(lo) > 0 >= phi(hi)
        x = fi / (3.0 * G + hd.slope(ai))
        for _ in range(60):
            phi = qi - 3.0 * G * x - hd.sy(ai + x)
            lo = np.where(phi > 0, x, lo); hi = np.where(phi <= 0, x, hi)
            xn = x + phi / (3.0 * G + hd.slope(ai + x))
            bad = (xn <= lo) | (xn >= hi)
            xn = np.where(bad, 0.5 * (lo + hi), xn)
            if np.all(np.abs(xn - x) <= 1e-14 * np.maximum(x, 1e-300) + 1e-300):
                x = xn
                break
            x = xn
        dg[pl] = x
    qs = np.where(q_tr > 0, q_tr, 1.0)
    fac = np.where(pl, 1.0 - 3.0 * G * dg / qs, 1.0)
    s = s_tr * fac[:, None]
    sig = s.copy(); sig[:, :3] += (Kb * tr)[:, None]
    a = a_n + dg
    flow = np.where(pl, 1.5 * dg / qs, 0.0)[:, None] * s_tr    # tensor components of the plastic increment
    ep = ep_n + flow * np.array([1.0, 1.0, 1.0, 2.0, 2.0, 2.0])
    q = q_tr - 3.0 * G * dg
    W = 0.5 * Kb * tr ** 2 + q ** 2 / (6.0 * G) + hd.Psi(a) - hd.Psi(a_n)
    D = None
    if tangent:
        D = np.broadcast_to(Kb * np.outer(M, M), (P, 6, 6)) + (2.0 * G * fac)[:, None, None] * IDEV[None]
        if pl.any():
            nrm = np.sqrt(np.maximum(_ddot(s_tr, s_tr), 1e-300))
            Nb = s_tr / nrm[:, None]                        # unit deviatoric direction, tensor components
            Hl = hd.slope(a)
            c2 = np.where(pl, 6.0 * G * G * (dg / qs - 1.0 / (3.0 * G + Hl)), 0.0)
            D = D + c2[:, None, None] * np.einsum("pi,pj->pij", Nb, Nb)
    return sig, D, ep, a, W, pl


def hencky(eps, mat: Material, tangent: bool = True):
    """Deformation theory: the radial return from the virgin state. Returns sig, D, W, plastic, alpha (the
    equivalent plastic strain)."""
    P = np.asarray(eps).shape[0]
    sig, D, _, a, W, pl = radial_return(eps, np.zeros((P, 6)), np.zeros(P), mat, tangent)
    return sig, D, W, pl, a


def von_mises(sig):
    s = np.asarray(sig, dtype=float).copy()
    p = (s[..., 0] + s[..., 1] + s[..., 2]) / 3.0
    s[..., :3] -= p[..., None]
    return np.sqrt(1.5 * _ddot(s, s))


__all__ = ["Hardening", "Material", "radial_return", "hencky", "von_mises", "M", "IDEV"]
