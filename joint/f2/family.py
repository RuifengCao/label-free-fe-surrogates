"""Parameter family of the CHS surrogate gate (draft for the pre-specification): bolted CHS blank flange-plate
splices of Fidalgo (2023) in bending, modelled as fejoint.chs.SpliceModel does for gate G-F1, with the plate's
thickness, the bolts' edge distances, the plate's yield stress and the bolt preload varied.

Varied, sampled uniformly and independently:
    tp   plate thickness, mm
    e1   tube outer face to bolt axis, mm
    e2   bolt axis to plate edge, mm
    fy   yield stress of the plate, MPa
    Np   preload of every bolt at zero load, kN (one value for all twelve bolts)
Fixed, as Fidalgo's specimens and the fejoint.chs.FlangeSplice defaults: the 323.9 x 12.4 mm tube and its coupon
law, which the weld shares; twelve 3/4 inch bolts (A325) with the elastic-plastic law of their coupon; holes,
washers, bearing radius, the unfused root of the groove weld and the fillet; 600 mm of tube beyond the plate; the
measuring ring 100 mm from the plate's outer face.

Plate law: the 12.7 mm plate's (gate G-F1's B-13 plate; f1/materials.py) with every stress scaled by fy / 397 MPa,
plastic strains unchanged; Young's modulus 201,000 MPa. The member with B-13's measured geometry, fy = 397 MPa and
Np = 125 kN is therefore gate G-F1's B-13 with the elastic-plastic bolts of the exploratory run E3
(probes/f1_explore), the model the tests checked.

Bolt law: E3's (the coupon curve by f1/materials.py's rule: engineering points from 0.004 to the uniform strain,
non-decreasing, at most 14 points, the first at the yield stress), on A_s over half the bolt's length; beyond its
last point a slope of E_b / 10000 on A_s over the half bolt instead of E3's zero, so that the energy stays strongly
convex in every bolt. Within the coupon's range the law is E3's.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np

from fejoint import chs
from fejoint.plasticity import Hardening, Material
from f1.config import DATA, PLATES, TUBE
from f1.materials import hardening_points

RANGES = {"tp": (10.0, 25.0), "e1": (55.0, 75.0), "e2": (55.0, 75.0), "fy": (345.0, 460.0), "Np": (60.0, 130.0)}
PLATE_BASE = "12.7"                    # the plate whose law is scaled
E_P = PLATES[PLATE_BASE]["E"]          # 201,000 MPa
NU = 0.3
BOLT = {"curve": "material_bolt_eng.csv", "E": 217100.0, "fy": 817.0, "eu": 0.0580, "As": 213.8}
BOLT_REG = 1e-4                        # final slope of the bolt law, as a fraction of E_b A_s / (L_b / 2)
CLEAR = 2.0                            # mm: the bearing ring must clear the fillet's toe and the plate's edge
MESH = "coarse"

# Gate G-F1's specimens as members of the family: measured geometry (Table 3.1 of the thesis), the plate's yield
# stress of Table 2.2, and two preloads each, the nominal 125 kN and the mean of the six bolt forces read at 25 kNm
# (f1.readings.measured_preload: B-13 111.46 kN, as exploratory run E2 used it; B-19 120.89 kN).
TESTED = {
    "B-13_nominal": {"tp": 12.6, "e1": 64.4, "e2": 65.5, "fy": 397.0, "Np": 125.0},
    "B-13_measured-mean": {"tp": 12.6, "e1": 64.4, "e2": 65.5, "fy": 397.0, "Np": 111.46268518518518},
    "B-19_nominal": {"tp": 19.3, "e1": 64.2, "e2": 64.5, "fy": 373.0, "Np": 125.0},
    "B-19_measured-mean": {"tp": 19.3, "e1": 64.2, "e2": 64.5, "fy": 373.0, "Np": 120.88897414553998},
}


@dataclass(frozen=True)
class Params:
    tp: float; e1: float; e2: float; fy: float; Np: float


def geometry(q: Params, name: str = "member") -> chs.FlangeSplice:
    return chs.FlangeSplice(name=name, tp=q.tp, e1=q.e1, e2=q.e2, E_p=E_P, E_t=TUBE["E"], E_b=BOLT["E"],
                            As=BOLT["As"], nu=NU)


def plate_material(fy: float) -> Material:
    alpha, sigma, h_end = hardening_points(PLATES[PLATE_BASE])
    s = fy / PLATES[PLATE_BASE]["fy"]
    return Material(E_P, NU, Hardening(alpha, sigma * s, h_end=h_end * s))


def tube_material() -> Material:
    alpha, sigma, h_end = hardening_points(TUBE)
    return Material(TUBE["E"], NU, Hardening(alpha, sigma, h_end=h_end))


def materials(q: Params) -> dict:
    """Material of each part of fejoint.chs.build: 0 plate, 1 tube, 2 fillet weld (the tube's law)."""
    t = tube_material()
    return {0: plate_material(q.fy), 1: t, 2: t}


def bolt_points() -> list:
    """(engineering strain, stress) of the bolt from its coupon curve, by f1/materials.py's rule (E3's points)."""
    d = np.loadtxt(DATA / BOLT["curve"], delimiter=",", skiprows=3)
    e, s = d[:, 0], d[:, 1]
    sel = (e >= 0.004) & (e <= BOLT["eu"] + 1e-9)
    e, s = e[sel], np.maximum.accumulate(s[sel])
    pts = [(BOLT["fy"] / BOLT["E"], BOLT["fy"])]
    for ei, si in zip(e, s):
        if ei > pts[-1][0] + 1e-4 and si >= pts[-1][1]:
            pts.append((float(ei), float(si)))
    A = np.array(pts)
    idx = np.unique(np.r_[0, np.round(np.linspace(0, len(A) - 1, 14)).astype(int)])
    return [tuple(map(float, r)) for r in A[idx]]


def bolt_curve(g: chs.FlangeSplice):
    """The half bolt's force-extension law beyond yield for fejoint.nlsolve.AxialSprings: (extensions, forces,
    final slope)."""
    Lh = g.L_b / 2
    A = np.array(bolt_points())
    return (A[:, 0] * Lh, A[:, 1] * g.As, BOLT_REG * g.E_b * g.As / Lh)


# Loading (f2.instance): a rotational spring of stiffness K_TH per half model between the end rotation and the
# loading device, whose range [0, Theta_max(q)] is set per member so that the member reaches about THETA_TARGET
# of the tests' rotation Theta_D at its top. Through the spring a state of end rotation theta and moment M is reached
# at the device rotation Theta = theta + M / (2 K_TH), so
#     Theta_max(q) = THETA_TARGET + (B_TUBE + 1 / (2 K_TH)) M_est(q),
# with theta at THETA_TARGET taken as THETA_TARGET + B_TUBE M (the tube's elastic rotation beyond the measuring
# ring, about 670 mm of tube) and M_est a closed-form estimate of the moment there: a smooth minimum (exponent 4)
# of a power law in the parameters and a cap. The constants were fitted on the 13 development members of
# 8 November 2026 (probes/f2_dev/fit_loading.py, frictionless, coarse mesh): M_est within 2.3% of their moments,
# Theta_D at their tops 0.0103 to 0.0115 rad; fitted without X3, the rule predicted X3's moment within 3.0%.
# The preload has no measurable effect on the moment at THETA_TARGET and is left out.
K_TH = 4.0e9                  # N mm / rad, half model (8,000 kNm/rad for the whole joint)
THETA_TARGET = 0.011
B_TUBE = 2.374e-11            # rad per N mm
M_RULE = {"A": 2.126e8, "tp": 1.615, "fy": 0.754, "e1": -0.864, "e2": 0.222, "cap": 3.690e8, "n": 4.0}


def moment_estimate(q: Params) -> float:
    """M_est(q), N mm: the moment of the whole joint at Theta_D = THETA_TARGET, estimated without solving."""
    r = M_RULE
    Mp = r["A"] * (q.tp / 15.0) ** r["tp"] * (q.fy / 400.0) ** r["fy"] * (q.e1 / 65.0) ** r["e1"] * (q.e2 / 65.0) ** r["e2"]
    return (Mp ** -r["n"] + r["cap"] ** -r["n"]) ** (-1.0 / r["n"])


def loading(q: Params) -> tuple[float, float]:
    """(k_th, Theta_max) of a member: the loading spring and the top of its device range."""
    return K_TH, THETA_TARGET + (B_TUBE + 1.0 / (2.0 * K_TH)) * moment_estimate(q)


def violations(q: Params) -> list[str]:
    g = geometry(q)
    out = []
    if g.r2 - g.r_bear < g.R + g.leg + CLEAR:
        out.append("bearing ring reaches the fillet's toe")
    if g.r2 + g.r_bear > g.r1 - CLEAR:
        out.append("bearing ring reaches the plate's edge")
    return out


def sample(n: int, seed: int, max_tries: int = 100000):
    rng = np.random.default_rng(seed)
    keys = list(Params.__dataclass_fields__)
    out, draws = [], 0
    while len(out) < n:
        draws += 1
        if draws > max_tries:
            raise RuntimeError("too many rejections")
        q = Params(**{k: float(rng.uniform(*RANGES[k])) for k in keys})
        if not violations(q):
            out.append(q)
    return out, draws


__all__ = ["RANGES", "Params", "TESTED", "geometry", "plate_material", "tube_material", "materials", "bolt_points",
           "bolt_curve", "loading", "violations", "sample", "MESH", "K_TH", "THETA_TARGET", "asdict"]
