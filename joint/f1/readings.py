"""Test readings of gate G-F1 from the digitised curves (f1/data), with their reading tolerances.

Bending, moment at a rotation: each figure's curve is read on its rising branch (up to the largest moment, the
points where the rotation does not increase dropped) by linear interpolation; the test value is the mean of the two
figures (Figs 3.3 and 3.7); the tolerance is half their difference, plus half the change of the mean curve over one
pixel of rotation either side, plus one pixel of moment.
Bending, bolt 1's force increase between two moments: bolt 1 is the upper dotted series at the higher moment (the
figure labels it); at the lower moment the two dotted series of bolts 1 and 2 overlap, so their mean is used; the
tolerance is half their difference there plus two pixels of force.
Axial, mean LVDT displacement at a load: for each figure (Figs 2.5 and 2.22) the left and right lines are each
fitted by a quadratic in the load over the digitised rows, and their mean is evaluated; the test value is the mean
of the two figures; the tolerance is half their difference plus the displacement pixel tolerance.
Units: kNm, rad, kN, mm.
"""
from __future__ import annotations

import numpy as np

from .config import DATA, PIXEL


def rising_branch(name):
    d = np.loadtxt(DATA / name, delimiter=",", skiprows=3)
    th, M = d[:, 0], d[:, 1]
    j = int(np.argmax(M))
    th, M = th[:j + 1], M[:j + 1]
    keep = np.r_[True, np.diff(np.maximum.accumulate(th)) > 0] & np.r_[True, np.diff(th) > 0]
    return th[keep], np.maximum.accumulate(M[keep])


def moment_at(name, theta):
    th, M = rising_branch(name)
    if not th[0] <= theta <= th[-1]:
        raise ValueError(f"{name}: rotation {theta} outside the digitised rising branch")
    return float(np.interp(theta, th, M))


def moment_reading(files, theta):
    m = [moment_at(f, theta) for f in files]
    px = PIXEL["theta_rad"]
    mean = lambda t: float(np.mean([moment_at(f, t) for f in files]))  # noqa: E731
    slope_term = abs(mean(theta + px) - mean(max(theta - px, 0.0))) / 2
    tol = abs(m[0] - m[1]) / 2 + slope_term + PIXEL["moment_kNm"]
    return {"value": float(np.mean(m)), "tolerance": float(tol), "per_figure": m, "slope_term": float(slope_term)}


def _series(name, label):
    rows = []
    for line in (DATA / name).read_text().splitlines():
        if line.startswith("#") or line.startswith("series,"):
            continue
        s, m, b = line.rsplit(",", 2)
        if s == label:
            rows.append((float(m), float(b)))
    a = np.array(sorted(rows))
    if a.size == 0:
        raise ValueError(f"{name}: no series {label!r}")
    return a[:, 0], a[:, 1]


def bolt_at(name, label, M):
    m, b = _series(name, label)
    if not m[0] - 1e-9 <= M <= m[-1] + 1e-9:
        raise ValueError(f"{name}: moment {M} outside series {label!r}")
    return float(np.interp(M, m, b))


def bolt_increase_reading(name, M_lo, M_hi):
    up_lo, lo_lo = bolt_at(name, "1-2 upper", M_lo), bolt_at(name, "1-2 lower", M_lo)
    up_hi = bolt_at(name, "1-2 upper", M_hi)
    value = up_hi - (up_lo + lo_lo) / 2
    tol = abs(up_lo - lo_lo) / 2 + 2 * PIXEL["bolt_kN"]
    return {"value": float(value), "tolerance": float(tol), "upper_lo": up_lo, "lower_lo": lo_lo, "upper_hi": up_hi}


def measured_preload(name, M=25.0):
    """Bolts 1 to 6 at the moment M (kN), by the rule in the configuration."""
    return [bolt_at(name, "1-2 upper", M), bolt_at(name, "1-2 lower", M), bolt_at(name, "3", M),
            bolt_at(name, "4", M), bolt_at(name, "5-6 upper", M), bolt_at(name, "5-6 lower", M)]


def displacement_at(name, T):
    d = np.loadtxt(DATA / name, delimiter=",", skiprows=3)
    if not d[:, 0].min() <= T <= d[:, 0].max():
        raise ValueError(f"{name}: load {T} outside the digitised rows")
    pl, pr = np.polyfit(d[:, 0], d[:, 1], 2), np.polyfit(d[:, 0], d[:, 2], 2)
    return float((np.polyval(pl, T) + np.polyval(pr, T)) / 2)


def displacement_reading(files, T):
    v = [displacement_at(f, T) for f in files]
    tol = abs(v[0] - v[1]) / 2 + PIXEL["displacement_mm"]
    return {"value": float(np.mean(v)), "tolerance": float(tol), "per_figure": v}


def read_tests(cfg: dict) -> dict:
    out = {}
    for name, spec in cfg["specimens"].items():
        pts, tests = cfg["points"][name], cfg["tests"][name]
        if spec["test"] == "bending":
            out[name] = {"C1": moment_reading(tests["moment_rotation"], pts["theta"]),
                         "reported_theta": {str(t): moment_reading(tests["moment_rotation"], t)
                                            for t in pts["theta_reported"]},
                         "C3": bolt_increase_reading(tests["bolt_forces"], *pts["bolt_moments_kNm"]),
                         "measured_preload_kN": measured_preload(tests["bolt_forces"], pts["bolt_moments_kNm"][0])}
        else:
            out[name] = {"C2": displacement_reading(tests["load_displacement"], pts["T_kN"])}
    return out


__all__ = ["moment_reading", "bolt_increase_reading", "measured_preload", "displacement_reading", "read_tests",
           "rising_branch"]
