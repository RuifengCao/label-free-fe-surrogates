"""Hardening curves of gate G-F1 from the digitised coupon curves (Fidalgo 2023, Fig. 2.18 and Table 2.2).

Up to necking: engineering points between strains 0.004 and eu are turned into true stress and true strain (thesis
eqs 2.21 and 2.22), the true stress made non-decreasing, and the equivalent plastic strain taken as the true strain
less the true stress over E. The curve starts at fy (Table 2.2) at zero plastic strain; points closer than 1e-4 in
plastic strain to the previous one, or lower in stress, are dropped, and the rest thinned to at most 14 points
(evenly by index, the first and last kept). Beyond necking: the thesis's weighted extension (eq. 2.23),
sigma_T = sigma_T' [w (1 + eps_T - eps_T') + (1 - w) (eps_T / eps_T')^eps_T'], at true strains 1.5 and 2.5 times
the necking strain and at 0.6, with a final slope through the point at 1.0. Every curve is non-decreasing, so the
deformation-theory energy stays convex (fejoint.plasticity).
"""
from __future__ import annotations

import numpy as np

from fejoint.plasticity import Hardening, Material

from .config import DATA


def hardening_points(spec: dict):
    d = np.loadtxt(DATA / spec["curve"], delimiter=",", skiprows=3)
    e, s = d[:, 0], d[:, 1]
    sel = (e >= 0.004) & (e <= spec["eu"] + 1e-9)
    e, s = e[sel], s[sel]
    eT, sT = np.log1p(e), s * (1 + e)
    sT = np.maximum.accumulate(sT)
    a = eT - sT / spec["E"]
    pts = [(0.0, float(spec["fy"]))]
    for ai, si in zip(a, sT):
        if ai > pts[-1][0] + 1e-4 and si >= pts[-1][1]:
            pts.append((float(ai), float(si)))
    A = np.array(pts)
    idx = np.unique(np.r_[0, np.round(np.linspace(0, len(A) - 1, 14)).astype(int)])
    A = A[idx]
    eTn, sTn = float(np.log1p(spec["eu"])), float(spec["fu"] * (1 + spec["eu"]))
    ext = []
    for eT_ in (1.5 * eTn, 2.5 * eTn, 0.6, 1.0):
        sl = sTn * (spec["w"] * (1 + eT_ - eTn) + (1 - spec["w"]) * (eT_ / eTn) ** eTn)
        ext.append((eT_ - sl / spec["E"], sl))
    h_end = (ext[-1][1] - ext[-2][1]) / (ext[-1][0] - ext[-2][0])
    curve = np.vstack([A, np.array(ext[:-1])])
    curve[:, 1] = np.maximum.accumulate(curve[:, 1])
    return curve[:, 0], curve[:, 1], float(h_end)


def material(spec: dict, theory: str, nu: float = 0.3) -> Material:
    if theory == "elastic":
        return Material(spec["E"], nu)
    alpha, sigma, h_end = hardening_points(spec)
    return Material(spec["E"], nu, Hardening(alpha, sigma, h_end=h_end))


__all__ = ["hardening_points", "material"]
