"""Parameter family of the stage C2 pilot: rolled T-stub pairs with M12 bolts, plastic flange, web and bolts.

Geometry as fejoint.tstub.TStubPair (quarter model: one T-stub on the plane between the flanges, half the
width, half the length; one bolt). Sampled uniformly and independently:
    t_f   flange thickness                 t_w   web thickness
    r     root radius                      w     bolt gauge (bolts at z = +-w/2)
    n     bolt axis to flange tip (the flange width is b = w + 2 n)
    fy    yield stress of flange and web (same steel)
    rho   bolt pre-shortening as a fraction of the half bolt's yield extension N_y / k_ax (0: snug)
Fixed: length L = 80 mm, bolt row at y = 20 mm, web modelled to H = 120 mm, M12 bolts with two washers
(as Bursi and Jaspart's T1), bolt law, hardening shape. The web's end section is rigid in x and loaded through a
linear spring of stiffness K_SPRING (per quarter model) by a loading device whose displacement D is prescribed,
sampled in [0, D_MAX] during training (c2.instance gives the reason).
Validity: the bearing patch must clear the root and the flange tip by at least CLEAR.

Steel (nominal law, as the stage C2 reference runs use): elastic to fy, plateau to 2% strain, then linear to
1.35 fy at 15% strain, then a slope of E / 10000; a slope of E / 10000 is also added throughout the plastic range
as a regulariser (it keeps the energy strongly convex; the plateau then rises slightly, and the hardening segment
ends about 3 MPa above 1.35 fy). Bolt (half bolt, axial spring): yield at 880 MPa on A_s,
plateau to 2% strain over the half bolt's length, then linear to 960 MPa at 6%, then the same small slope.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np

from fejoint.tstub import TStubPair
from fejoint.plasticity import Hardening, Material

RANGES = {"t_f": (8.0, 20.0), "t_w": (6.0, 12.0), "r": (8.0, 18.0), "w": (70.0, 110.0), "n": (20.0, 40.0),
          "fy": (235.0, 460.0), "rho": (0.0, 0.9)}
E, NU = 210000.0, 0.3
REG = 1e-4 * E
CLEAR = 2.0
D_MAX = 8.0                       # loading-device displacement, mm
K_SPRING = 2.0e4                  # loading spring per quarter model, N/mm
BOLT = dict(d=12.0, As=84.3, head=7.5, nut=10.8, bearing_r=12.0, n_washers=2, washer_t=2.5)
BOLT_LAW = [(880.0 / E, 880.0), (0.02, 880.0), (0.06, 960.0)]       # (strain, stress), nominal
MESH = dict(h=5.0, n_tf=2, hx_max=20.0)


@dataclass(frozen=True)
class Params:
    t_f: float; t_w: float; r: float; w: float; n: float; fy: float; rho: float


def geometry(q: Params) -> TStubPair:
    return TStubPair(t_f=q.t_f, t_w=q.t_w, b=q.w + 2 * q.n, L=80.0, w=q.w, bolt_y=(20.0,), H=120.0, corner="root",
                     r=q.r, E=E, nu=NU, x_meas=60.0, **BOLT)


def steel(fy: float) -> Material:
    pts = [(fy / E, fy), (0.02, fy), (0.15, 1.35 * fy)]
    al = np.array([max(e - s / E, 0.0) for e, s in pts]); al[0] = 0.0
    sg = np.array([s for _, s in pts]) + REG * al
    return Material(E, NU, Hardening(al, sg, h_end=REG))


def bolt_curve(g: TStubPair, k_ax: float):
    """The half bolt's force-extension law beyond yield for fejoint.nlsolve.AxialSprings."""
    Lh = g.L_b / 2
    e = np.array([BOLT_LAW[0][1] * g.As / k_ax] + [s_ * Lh for s_, _ in BOLT_LAW[1:]])
    N = np.array([s * g.As for _, s in BOLT_LAW]) + REG * g.As * np.r_[0.0, [s_ - BOLT_LAW[0][0] for s_, _ in BOLT_LAW[1:]]]
    return (e, N, REG * g.As / Lh)


def violations(q: Params) -> list[str]:
    g = geometry(q)
    out = []
    root_edge = g.t_w / 2 + g.r
    if g.w / 2 - g.bearing_r < root_edge + CLEAR:
        out.append("bearing patch reaches the root")
    if q.n < g.bearing_r + CLEAR:
        out.append("bearing patch reaches the flange tip")
    if q.t_w > q.t_f + 2.0:
        out.append("web much thicker than the flange")
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


__all__ = ["RANGES", "Params", "geometry", "steel", "bolt_curve", "violations", "sample", "D_MAX", "K_SPRING", "MESH",
           "asdict"]
