"""Bolted circular hollow section (CHS) blank flange-plate splice under bending: mesh and contact model.

The specimens are B-13 and B-19 of Fidalgo (2023, PhD thesis, University of Toronto, Chapter 3; Fidalgo and
Packer 2023, J. Struct. Eng. 149(6) 04023066): a 323.9 mm tube welded to a blank (solid) circular plate, two
such plates bolted face to face with 12 bolts, in four-point bending. The model follows the C2 T-stub model
(fejoint.tstub_pl) in everything but the geometry:
  symmetry  half the joint about the bending plane x = 0 (bolts 1 to 6) and one side of the splice; the plane
            between the plates, z = 0, is a rigid frictionless support (u_z >= 0), which is the mirror condition;
  bolts     each half bolt is an axial spring of stiffness E_b A_s / (L_b / 2) between a rigid head plane and
            the splice plane, with a pre-shortening delta per bolt for the preload; the head plane is in
            unilateral frictionless contact with the plate's outer face over the bearing annulus and tilts
            against bending springs E_b I_s / (L_b / 2);
  load      the tube's end section stays plane and rotates by theta about the x axis (prescribed), with a free
            axial translation w0, so no axial force acts; the moment is the reaction to theta;
  weld      partial-penetration groove weld: the tube wall is fused to the plate over its outer part and not
            over its inner `root` (a crack whose faces are in frictionless unilateral contact); a fillet of leg
            `leg` outside, stair-stepped on the mesh (cells whose centroid lies inside the triangle).
Mesh: structured hexahedra in cylindrical coordinates (r, phi, z), phi measured from the tension extreme fibre
(x = r sin phi, y = -r cos phi), refined in phi around the bolts; bolt holes stair-stepped (cells whose centroid
lies inside the hole are removed). The plate's centre is an O-grid (a square and a ring of radial lines) on a
coarse phi grid of 7.5 degree steps, and so is the tube beyond z_h; the fine nodes on these two interfaces are
tied to the coarse ones by linear interpolation in phi (hanging nodes).
Units: N, mm, MPa. Angles in degrees unless stated.
"""
from __future__ import annotations

import contextlib
from dataclasses import dataclass, asdict
import numpy as np
import scipy.sparse as sp

from . import hex8i as H
from . import linsolve as _ls
from .contact import solve_signorini
from .nlhex import PlasticHexSet
from .nlsolve import ContactProblem, AxialSprings
from .plasticity import Material

DEG = np.pi / 180.0
STEP = 7.5                     # coarse phi step (degrees); divides the bolt pitch and the first bolt's angle


@contextlib.contextmanager
def direct_solver_up_to(n: int):
    """Let fejoint.linsolve use SuperLU for systems of up to n unknowns (its default stops at DIRECT_MAX and
    switches to AMG-CG, which converges slowly on these thin-plate problems). Restored on exit."""
    old = _ls.DIRECT_MAX
    _ls.DIRECT_MAX = max(old, int(n))
    try:
        yield
    finally:
        _ls.DIRECT_MAX = old


class WarmContactProblem(ContactProblem):
    """fejoint.nlsolve.ContactProblem whose first primal-dual active set guess is the contact state the last
    solve ended with (ContactProblem starts every solve from all constraints active). Same iteration otherwise;
    the result does not depend on the starting guess, only the number of active-set iterations does."""

    active = None

    def solve(self, z0, mode="hencky", tol=1e-10, max_it=60, armijo=1e-4, verbose=False):
        z = np.asarray(z0, float).copy()
        assert (z[self.cidx] >= -1e-12).all(), "the starting point violates a contact constraint"
        z[self.cidx] = np.maximum(z[self.cidx], 0.0)
        hist = []
        E, g, Hm, info = self.evaluate(z, mode)
        for s in self.sets:
            s.warm()
        active0 = self.active
        converged = False
        self.pdas_iterations = []
        for it in range(1, max_it + 1):
            A = Hm[self.free][:, self.free].tocsr()
            sol = solve_signorini(A, -g[self.free], self.c_free, g=z[self.cidx], active0=active0)
            active0 = sol["active"]
            self.pdas_iterations.append(sol["iterations"])
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
                while True:
                    zt = z + t * dz
                    zt[self.cidx] = np.maximum(zt[self.cidx], 0.0)
                    try:
                        Et, _, _, _ = self.evaluate(zt, mode, tangent=False)
                    except RuntimeError:
                        Et = np.inf
                    if np.isfinite(Et) and (Et <= E + armijo * t * slope or t < 1e-8):
                        break
                    if t < 1e-8:
                        break
                    t *= 0.5
                if not np.isfinite(Et):
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
            if t == 1.0 and step_norm <= tol * zscale:
                converged = True
                break
        self.active = active0
        rep = self.kkt(z, g)
        rep.update({"iterations": len(hist), "converged": converged, "energy": E, "history": hist,
                    "grad": g, "plastic_points": [i["plastic_points"] for i in info],
                    "pdas_iterations": list(self.pdas_iterations)})
        return z, rep


@dataclass
class FlangeSplice:
    name: str
    tp: float                  # plate thickness
    e1: float                  # tube outer face to hole centre
    e2: float                  # hole centre to plate edge
    E_p: float                 # plate Young's modulus
    d: float = 323.9           # tube outside diameter
    t: float = 12.4            # tube wall
    E_t: float = 191700.0      # tube (and weld) Young's modulus
    E_b: float = 217100.0      # bolt Young's modulus
    nu: float = 0.3
    n_bolts: int = 12
    phi0: float = 15.0         # first bolt, from the tension extreme fibre
    d_hole: float = 21.0
    db: float = 19.05
    As: float = 213.8          # bolt area, pi / 4 (db sqrt(0.75))^2
    r_bear: float = 17.3       # bearing radius of the head or washer on the plate
    head_h: float = 11.9       # heavy hex head height (3/4 inch)
    nut_h: float = 18.65       # heavy hex nut height
    washer_t: float = 3.8      # hardened washer, middle of 3.1 to 4.5 mm
    root: float = 3.4          # unfused depth of the groove weld at the inner side of the wall
    leg: float = 8.0           # fillet leg (0: no fillet)
    L_tube: float = 600.0      # tube modelled beyond the plate's outer face
    z_meas: float = 100.0      # measuring ring, from the plate's outer face

    @property
    def R(self): return self.d / 2
    @property
    def r_i(self): return self.R - self.t
    @property
    def r2(self): return self.R + self.e1           # bolt circle radius
    @property
    def r1(self): return self.R + self.e1 + self.e2  # plate radius
    @property
    def L_b(self):                                    # whole bolt, Fidalgo (2023) eq. 2.24, grip = 2 tp
        return self.head_h / 2 + 2 * self.tp + self.washer_t + self.nut_h / 2
    @property
    def bolt_phi(self):                               # bolts of the half model (1 to n/2)
        return self.phi0 + np.arange(self.n_bolts // 2) * 360.0 / self.n_bolts
    @property
    def S_tube(self):                                 # elastic section modulus of the tube
        return np.pi / 64 * (self.d ** 4 - (self.d - 2 * self.t) ** 4) / self.R


def fidalgo(name: str, **kw) -> FlangeSplice:
    """Specimens B-13 and B-19: plate thickness and e1, e2 measured (Table 3.1), Young's moduli Table 2.2."""
    base = {"B-13": dict(tp=12.6, e1=64.4, e2=65.5, E_p=201000.0),
            "B-19": dict(tp=19.3, e1=64.2, e2=64.5, E_p=204500.0)}[name]
    base.update(kw)
    return FlangeSplice(name=name, **base)


MESHES = {
    # n_bolt / n_other: phi parts per 7.5 degree interval next to a bolt / elsewhere; n_tp plate layers;
    # n_in parts from r_c to the tube's inner face; n_fw layers in the fused part of the wall; n_leg parts of
    # the fillet leg (radial and axial); h_toe first step after the toe, h_mid largest step up to the bearing
    # annulus; n_b1 parts across the bearing ring, n_b2 across the hole radius; h_out step to the plate edge;
    # n_t ring layers of the O-grid; hz_near largest axial step up to z_h, hz_far beyond.
    "coarse": dict(n_bolt=4, n_other=2, n_tp=2, n_in=1, n_fw=1, n_leg=2, h_toe=4.0, h_mid=10.0, n_b1=1,
                   n_b2=2, h_out=12.0, n_t=2, hz_near=25.0, hz_far=75.0),
    "medium": dict(n_bolt=6, n_other=2, n_tp=3, n_in=2, n_fw=2, n_leg=2, h_toe=3.0, h_mid=8.0, n_b1=2,
                   n_b2=3, h_out=9.0, n_t=2, hz_near=20.0, hz_far=60.0),
    "fine": dict(n_bolt=8, n_other=3, n_tp=4, n_in=2, n_fw=2, n_leg=4, h_toe=2.0, h_mid=6.0, n_b1=3,
                 n_b2=4, h_out=7.0, n_t=3, hz_near=15.0, hz_far=50.0),
    # for tests and dry runs of the code only
    "tiny": dict(n_bolt=2, n_other=1, n_tp=1, n_in=1, n_fw=1, n_leg=1, h_toe=8.0, h_mid=20.0, n_b1=1, n_b2=1,
                 h_out=25.0, n_t=1, hz_near=50.0, hz_far=150.0),
    "tiny-flag": dict(n_bolt=2, n_other=1, n_tp=2, n_in=1, n_fw=1, n_leg=1, h_toe=8.0, h_mid=20.0, n_b1=1, n_b2=1,
                      h_out=25.0, n_t=1, hz_near=50.0, hz_far=150.0),
}


def _fit(x0, x1, h0, growth, hmax):
    """Points from x0 to x1: steps h0, h0 growth, ... capped at hmax, scaled to end exactly at x1."""
    L = x1 - x0
    if L <= h0 * 1.5:
        return np.array([x0, x1])
    steps, h = [], h0
    while sum(steps) < L:
        steps.append(h)
        h = min(h * growth, hmax)
    if len(steps) > 1 and sum(steps) - L > 0.5 * steps[-1]:
        steps.pop()
    s = np.array(steps) * L / sum(steps)
    return x0 + np.r_[0.0, np.cumsum(s)]


def _uniform(x0, x1, h):
    return np.linspace(x0, x1, max(1, int(np.ceil((x1 - x0) / h - 1e-9))) + 1)


def phi_grids(g: FlangeSplice, m: dict):
    """Coarse (7.5 degree) and fine phi grids over [0, 180]; the coarse grid is a subset of the fine one."""
    assert abs(g.phi0 / STEP - round(g.phi0 / STEP)) < 1e-9 and abs(360.0 / g.n_bolts / STEP
                                                                   - round(360.0 / g.n_bolts / STEP)) < 1e-9
    coarse = np.arange(0.0, 180.0 + 1e-9, STEP)
    fine = [0.0]
    for a, b in zip(coarse[:-1], coarse[1:]):
        near = np.any(np.isclose(g.bolt_phi, a)) or np.any(np.isclose(g.bolt_phi, b))
        fine.extend(np.linspace(a, b, (m["n_bolt"] if near else m["n_other"]) + 1)[1:])
    return coarse, np.array(fine)


def r_grid(g: FlangeSplice, m: dict, r_c: float):
    rh, rb = g.d_hole / 2, g.r_bear
    assert r_c < g.r_i and g.R + g.leg < g.r2 - rb and g.r2 + rb < g.r1 and 0 <= g.root < g.t
    parts = [np.linspace(r_c, g.r_i, m["n_in"] + 1), np.array([g.r_i, g.r_i + g.root]),
             np.linspace(g.r_i + g.root, g.R, m["n_fw"] + 1)]
    if g.root == 0:                                   # fully fused wall (complete-penetration weld)
        parts[1] = np.array([g.r_i])
    toe = g.R
    if g.leg > 0:
        parts.append(np.linspace(g.R, g.R + g.leg, m["n_leg"] + 1))
        toe = g.R + g.leg
    parts += [_fit(toe, g.r2 - rb, m["h_toe"], 1.3, m["h_mid"]),
              np.linspace(g.r2 - rb, g.r2 - rh, m["n_b1"] + 1), np.linspace(g.r2 - rh, g.r2, m["n_b2"] + 1),
              np.linspace(g.r2, g.r2 + rh, m["n_b2"] + 1), np.linspace(g.r2 + rh, g.r2 + rb, m["n_b1"] + 1),
              _uniform(g.r2 + rb, g.r1, m["h_out"])]
    return np.unique(np.round(np.concatenate(parts), 9))


def z_grids(g: FlangeSplice, m: dict):
    zp = np.linspace(0.0, g.tp, m["n_tp"] + 1)
    z0 = g.tp
    near = []
    if g.leg > 0:
        near.append(np.linspace(g.tp, g.tp + g.leg, m["n_leg"] + 1))
        z0 = g.tp + g.leg
    h0 = g.leg / m["n_leg"] if g.leg > 0 else g.tp / m["n_tp"]
    zm, zh = g.tp + g.z_meas, g.tp + 1.5 * g.z_meas
    near += [_fit(z0, zm, h0, 1.3, m["hz_near"]), _uniform(zm, zh, m["hz_near"])]
    zn = np.unique(np.round(np.concatenate(near), 9))
    zf = _fit(zh, g.tp + g.L_tube, zn[-1] - zn[-2], 1.3, m["hz_far"])
    return zp, zn, zf


def _block(us, vs, ws, f):
    """Structured hexahedra on the tensor grid us x vs x ws, mapped by f(U, V, W) -> (X, Y, Z)."""
    P, hx = H.box_mesh(us, vs, ws)
    X, Y, Z = f(P[:, 0], P[:, 1], P[:, 2])
    return np.column_stack([X, Y, Z]), hx


def _polar(R_, PHI, Z):
    return R_ * np.sin(PHI * DEG), -R_ * np.cos(PHI * DEG), Z


def cyl(nodes):
    """(r, phi in degrees, z) of Cartesian nodes."""
    x, y, z = np.asarray(nodes).T
    return np.hypot(x, y), np.degrees(np.arctan2(x, -y)), z


def build(g: FlangeSplice, mesh: str | dict = "medium", r_c_frac: float = 0.9, a_frac: float = 0.5):
    """Nodes, hexahedra (node order of fejoint.hex8i), part per cell (0 plate, 1 tube, 2 fillet weld) and the
    sets the model needs: hanging-node ties, root pairs, bearing patches, faces."""
    m = MESHES[mesh] if isinstance(mesh, str) else dict(mesh)
    coarse, fine = phi_grids(g, m)
    r_c = r_c_frac * g.r_i
    a = a_frac * r_c
    rs = r_grid(g, m, r_c)
    zp, zn, zf = z_grids(g, m)
    blocks = []
    # plate, outer polar part
    blocks.append(_block(rs, fine, zp, _polar) + (0,))
    # plate, O-grid core: square x in [0, a], y in [-a, a], lines through the square's points on the coarse rays
    lo = coarse[coarse <= 45.0 + 1e-9]
    mid = coarse[(coarse >= 45.0 - 1e-9) & (coarse <= 135.0 + 1e-9)]
    xs = a * np.tan(lo * DEG); xs[-1] = a
    ys = -a / np.tan(mid * DEG); ys[0], ys[-1] = -a, a; ys[np.isclose(mid, 90.0)] = 0.0
    blocks.append(_block(xs, ys, zp, lambda X, Y, Z: (X, Y, Z)) + (0,))

    def square_point(phi):
        p = np.asarray(phi, float)
        x = np.where(p <= 45.0, a * np.tan(p * DEG), np.where(p >= 135.0, a * np.tan((180.0 - p) * DEG), a))
        y = np.where(p <= 45.0, -a, np.where(p >= 135.0, a, -a / np.tan(np.clip(p, 1.0, 179.0) * DEG)))
        # exact values on the grid lines, so that the ring's inner nodes coincide with the square's
        for i, ph in enumerate(lo):
            x = np.where(np.isclose(p, ph), xs[i], x); x = np.where(np.isclose(p, 180.0 - ph), xs[i], x)
        for j, ph in enumerate(mid):
            y = np.where(np.isclose(p, ph), ys[j], y)
        return x, y

    def ring(S, PHI, Z):
        xq, yq = square_point(PHI)
        xc, yc, _ = _polar(r_c, PHI, Z)
        return (1 - S) * xq + S * xc, (1 - S) * yq + S * yc, Z
    blocks.append(_block(np.linspace(0.0, 1.0, m["n_t"] + 1), coarse, zp, ring) + (0,))
    # tube: near part on the fine grid, far part (beyond z_h) on the coarse grid
    rt = rs[(rs >= g.r_i - 1e-9) & (rs <= g.R + 1e-9)]
    blocks.append(_block(rt, fine, zn, _polar) + (1,))
    blocks.append(_block(rt, coarse, zf, _polar) + (1,))
    # fillet weld, stair-stepped
    if g.leg > 0:
        rw = rs[(rs >= g.R - 1e-9) & (rs <= g.R + g.leg + 1e-9)]
        zw = zn[zn <= g.tp + g.leg + 1e-9]
        nd, hx = _block(rw, fine, zw, _polar)
        rc_, _, zc_ = cyl(nd[hx].mean(axis=1))
        keep = (rc_ - g.R) + (zc_ - g.tp) <= g.leg + 1e-9
        blocks.append((nd, hx[keep], 2))
    # merge coincident nodes
    nodes_l, hex_l, part_l, off = [], [], [], 0
    for nd, hx, p in blocks:
        nodes_l.append(nd); hex_l.append(hx + off); part_l.append(np.full(hx.shape[0], p)); off += nd.shape[0]
    nodes = np.concatenate(nodes_l); hexes = np.concatenate(hex_l); part = np.concatenate(part_l)
    _, first, inv = np.unique(np.round(nodes, 6), axis=0, return_index=True, return_inverse=True)
    nodes, hexes = nodes[first], inv.ravel()[hexes]
    if g.leg > 0:
        # the fillet's outer staircase nodes go onto the weld face (u + v = leg in the r-z plane, u = r - R,
        # v = z - tp), along the line to the corner (R, tp): the diagonal cells become triangles and the fillet
        # volume is exact
        r, ph, z = cyl(nodes)
        u, v = r - g.R, z - g.tp
        out_ = (u > 1e-9) & (v > 1e-9) & (u + v > g.leg + 1e-9)
        s = g.leg / (u[out_] + v[out_])
        rn, zn_ = g.R + s * u[out_], g.tp + s * v[out_]
        nodes[out_, 0], nodes[out_, 1] = _polar(rn, ph[out_], 0.0)[:2]
        nodes[out_, 2] = zn_
    # bolt holes in the plate (stair-stepped)
    bx, by, _ = _polar(g.r2, g.bolt_phi, 0.0)
    c = nodes[hexes].mean(axis=1)
    hole = np.zeros(hexes.shape[0], bool)
    hole_volumes = []
    for xb_, yb_ in zip(bx, by):
        this = (part == 0) & (np.hypot(c[:, 0] - xb_, c[:, 1] - yb_) < g.d_hole / 2)
        hole_volumes.append(float(cell_volumes(nodes, hexes[this]).sum()))
        hole |= this
    hexes, part = hexes[~hole], part[~hole]
    used = np.unique(hexes)
    renum = -np.ones(nodes.shape[0], int); renum[used] = np.arange(used.size)
    nodes, hexes = nodes[used], renum[hexes]
    # unfused root: the tube's nodes on the plate at r = r_i become nodes of their own
    r, ph, z = cyl(nodes)
    rootn = np.nonzero(np.isclose(r, g.r_i, atol=1e-6) & np.isclose(z, g.tp, atol=1e-6))[0]
    if g.root == 0:
        rootn = rootn[:0]
    dup = {int(k): nodes.shape[0] + i for i, k in enumerate(rootn)}
    nodes = np.vstack([nodes, nodes[rootn]])
    tube_cells = np.nonzero(part == 1)[0]
    sub = hexes[tube_cells]
    for k, v in dup.items():
        sub[sub == k] = v
    hexes[tube_cells] = sub
    root_pairs = np.array([[v, k] for k, v in dup.items()], int).reshape(-1, 2)   # (tube node, plate node)
    assert not np.isin(root_pairs[:, 1], hexes[part == 1]).any(), "the tube still holds a root node"
    # hanging nodes on the two coarse interfaces
    r, ph, z = cyl(nodes)
    on_coarse = np.isclose(ph[:, None], coarse[None, :], atol=1e-6).any(axis=1)
    zh = zf[0]
    ties = []
    for sel, key in ((np.isclose(r, r_c, atol=1e-6), "core"),
                     (np.isclose(z, zh, atol=1e-6) & (r > g.r_i - 1e-6) & (r < g.R + 1e-6), "tube")):
        masters = {}
        for i in np.nonzero(sel & on_coarse)[0]:
            masters[(round(float(r[i]), 5), round(float(z[i]), 5), round(float(ph[i]), 5))] = int(i)
        for i in np.nonzero(sel & ~on_coarse)[0]:
            k = int(np.searchsorted(coarse, ph[i]))
            pa, pb = coarse[k - 1], coarse[k]
            wb = (ph[i] - pa) / (pb - pa)
            ia = masters[(round(float(r[i]), 5), round(float(z[i]), 5), round(float(pa), 5))]
            ib = masters[(round(float(r[i]), 5), round(float(z[i]), 5), round(float(pb), 5))]
            ties.append((int(i), ia, ib, 1.0 - wb, wb, key))
    # bearing patches: plate nodes on the outer face within r_bear of a bolt axis
    top = np.nonzero(np.isclose(z, g.tp, atol=1e-6))[0]
    plate_nodes = np.unique(hexes[part == 0])
    top = np.intersect1d(top, plate_nodes)
    patches = [top[np.hypot(nodes[top, 0] - xb_, nodes[top, 1] - yb_) <= g.r_bear + 1e-6] for xb_, yb_ in zip(bx, by)]
    hanging = np.array([t[0] for t in ties], int)
    bottom = np.setdiff1d(np.nonzero(np.isclose(z, 0.0, atol=1e-6))[0], hanging)
    end = np.nonzero(np.isclose(z, g.tp + g.L_tube, atol=1e-6))[0]
    return {"nodes": nodes, "hexes": hexes, "part": part, "ties": ties, "root_pairs": root_pairs,
            "patches": patches, "bottom": bottom, "end": end, "bolt_xy": np.column_stack([bx, by]),
            "hole_volumes": hole_volumes,
            "grids": {"phi_coarse": coarse, "phi_fine": fine, "r": rs, "z_plate": zp, "z_near": zn, "z_far": zf,
                      "r_c": r_c, "a": a, "z_h": zh},
            "mesh": m}


def mesh_checks(g: FlangeSplice, msh: dict) -> dict:
    """Jacobians at the Gauss points, volumes by part against the geometry, hole and fillet areas."""
    nodes, hexes, part = msh["nodes"], msh["hexes"], msh["part"]
    X = nodes[hexes]
    dets = []
    for p in H.GAUSS:
        J = np.einsum("ai,eaj->eij", H.dN_dxi(p), X)
        dets.append(np.linalg.det(J))
    dets = np.array(dets)                                       # (8, E)
    vol = dets.sum(axis=0)
    out = {"cells": int(hexes.shape[0]), "nodes": int(nodes.shape[0]), "min_detJ": float(dets.min()),
           "max_detJ_ratio_in_cell": float((dets.max(axis=0) / dets.min(axis=0)).max())}
    holes = len(g.bolt_phi) * np.pi * (g.d_hole / 2) ** 2 * g.tp
    plate_exact = 0.5 * np.pi * g.r1 ** 2 * g.tp - holes          # half plate
    tube_exact = 0.5 * np.pi * (g.R ** 2 - g.r_i ** 2) * g.L_tube
    fillet_exact = np.pi * (g.R + g.leg / 3) * g.leg ** 2 / 2       # half ring of triangles (Pappus)
    out["plate_volume_ratio"] = float(vol[part == 0].sum() / plate_exact)
    out["tube_volume_ratio"] = float(vol[part == 1].sum() / tube_exact)
    if g.leg > 0:
        out["fillet_volume_ratio"] = float(vol[part == 2].sum() / fillet_exact)
    out["hole_volume_ratio"] = [float(v / (np.pi * (g.d_hole / 2) ** 2 * g.tp)) for v in msh["hole_volumes"]]
    return out


def cell_volumes(nodes, hexes):
    X = nodes[hexes]
    return sum(np.linalg.det(np.einsum("ai,eaj->eij", H.dN_dxi(p), X)) for p in H.GAUSS)


class SpliceModel:
    """Half joint (x >= 0) on one side of the splice, solved with fejoint.nlsolve.ContactProblem.

    Unknowns z: one slot per physical degree of freedom (3 per node), then (a, theta_1, theta_2) per bolt head
    (axial displacement and tilts about the x and y axes through the bolt axis), then w0 and theta of the end
    section. The physical displacement is u = T z:
      plain nodes      u = z (identity);
      hanging nodes    u = linear interpolation of the two coarse nodes beside them (slots unused, fixed at 0);
      bearing patch    u_z = a + theta_1 (x - x_b) + theta_2 (y - y_b) - s, the slot holding the separation s >= 0
                       between the head plane and the plate;
      root pairs       u_z(tube node) = u_z(plate node) + s, the tube node's slot holding s >= 0;
      end section      u_z = w0 - theta y (the end nodes' z slots unused, fixed at 0); theta prescribed.
    Constraints: z >= 0 on the plate's face z = 0 (contact with the splice plane), on the head separations and on
    the root separations; u_x = 0 on x = 0 (symmetry); u_y = 0 at the centre of the plate's face z = 0 (removes
    the free sliding along y, which carries no force). The moment on the whole joint is twice the reaction to
    theta.
    """

    def __init__(self, g: FlangeSplice, mesh: str | dict = "medium", mats: dict | None = None, bolt_curve=None,
                 reg: float = 1e-6, k_rot_factor: float = 1.0, splice: str = "frictionless"):
        """splice: "frictionless" (the reference), or "no-slip", a bounding variant in which every node of the
        plate's face z = 0 keeps u_x = u_y = 0 (contact still unilateral in z): infinite friction everywhere,
        stiffer than any finite friction coefficient."""
        assert splice in ("frictionless", "no-slip")
        self.splice = splice
        self.g = g
        msh = build(g, mesh)
        self.msh = msh
        nodes, hexes, part = msh["nodes"], msh["hexes"], msh["part"]
        self.nodes = nodes
        n = nodes.shape[0]; ndof = 3 * n; nb = len(msh["patches"])
        self.n, self.ndof, self.nb = n, ndof, nb
        self.iw0, self.ith = ndof + 3 * nb, ndof + 3 * nb + 1
        nfull = ndof + 3 * nb + 2
        self.nfull = nfull
        x, y, zc = nodes.T
        Lh = g.L_b / 2
        self.k_ax = g.E_b * g.As / Lh
        d_s = np.sqrt(4 * g.As / np.pi); I_s = np.pi * d_s ** 4 / 64
        self.k_rot = k_rot_factor * g.E_b * I_s / Lh
        rows, cols, vals = [], [], []
        special = np.zeros(ndof, bool)
        unused = np.zeros(nfull, bool)
        ties = msh["ties"]
        masters = set()
        for s_, ia, ib, wa, wb, _ in ties:
            for c in range(3):
                rows += [3 * s_ + c] * 2; cols += [3 * ia + c, 3 * ib + c]; vals += [wa, wb]
                special[3 * s_ + c] = True; unused[3 * s_ + c] = True
            masters.update((ia, ib))
        for b, p in enumerate(msh["patches"]):
            base = ndof + 3 * b
            xb, yb = msh["bolt_xy"][b]
            for col, val in ((base, np.ones(p.size)), (base + 1, x[p] - xb), (base + 2, y[p] - yb),
                             (None, -np.ones(p.size))):
                rows += list(3 * p + 2); cols += list(3 * p + 2 if col is None else np.full(p.size, col))
                vals += list(val)
            special[3 * p + 2] = True
        rp = msh["root_pairs"]
        for q, o in rp:
            rows += [3 * q + 2, 3 * q + 2]; cols += [3 * o + 2, 3 * q + 2]; vals += [1.0, 1.0]
            special[3 * q + 2] = True
        end = msh["end"]
        rows += list(3 * end + 2) * 2; cols += [self.iw0] * end.size + [self.ith] * end.size
        vals += [1.0] * end.size + list(-y[end])
        special[3 * end + 2] = True; unused[3 * end + 2] = True
        patch_all = np.concatenate(msh["patches"])
        others = np.r_[3 * np.array(sorted(masters), int) + 2, 3 * rp[:, 1] + 2]
        assert not special[others].any(), "a master or a root plate node has a transformed row"
        ident = np.nonzero(~special)[0]
        rows += list(ident); cols += list(ident); vals += [1.0] * ident.size
        self.T = sp.csr_matrix((np.array(vals, float), (np.array(rows), np.array(cols))), shape=(ndof, nfull))
        # linear part: head tilt springs, weak springs on the head separations
        diag = np.zeros(nfull)
        for b, p in enumerate(msh["patches"]):
            base = ndof + 3 * b
            diag[base + 1] = diag[base + 2] = self.k_rot
            diag[3 * p + 2] += reg * self.k_ax / p.size
        K_lin = sp.diags(diag).tocsr()
        fixed = unused.copy()
        sym = np.nonzero(np.abs(x) < 1e-6)[0]
        fixed[3 * sym] = True
        bottom = msh["bottom"]
        self.iy = int(bottom[np.argmin(np.hypot(x[bottom], y[bottom]))])
        assert np.hypot(x[self.iy], y[self.iy]) < 1e-6
        fixed[3 * self.iy + 1] = True
        if splice == "no-slip":
            fixed[3 * bottom] = True; fixed[3 * bottom + 1] = True
        fixed[self.ith] = True                          # theta is prescribed under both controls
        fixed_ax = fixed.copy(); fixed_ax[self.iw0] = True   # axial control: w0 prescribed, theta = 0
        self.cidx = np.r_[3 * bottom + 2, 3 * patch_all + 2, 3 * rp[:, 0] + 2]
        self.n_bottom = bottom.size
        if mats is None:
            mats = {0: Material(g.E_p, g.nu), 1: Material(g.E_t, g.nu), 2: Material(g.E_t, g.nu)}
        self.mats = mats
        self.bolts = AxialSprings(ndof + 3 * np.arange(nb), nfull, self.k_ax, N_curve=bolt_curve)
        self.sets = [PlasticHexSet(nodes, hexes[part == k], mats[k]) for k in (0, 1, 2) if (part == k).any()]
        self.sets.append(self.bolts)
        self.probs = {"rotation": WarmContactProblem(self.T, K_lin, np.zeros(nfull), self.sets, fixed, self.cidx),
                      "axial": WarmContactProblem(self.T, K_lin, np.zeros(nfull), self.sets, fixed_ax, self.cidx)}
        self.prob = self.probs["rotation"]
        self.fixed = fixed
        self.delta = np.zeros(nb)
        self.z = np.zeros(nfull)
        # readings: the tension-side point D and the compression-side point C on the measuring ring, the ring
        zm = g.tp + g.z_meas
        r, ph, zz = cyl(nodes)
        ring = np.nonzero(np.isclose(zz, zm, atol=1e-6) & np.isclose(r, g.R, atol=1e-6))[0]
        ring = np.intersect1d(ring, np.unique(hexes[part == 1]))
        self.ring = ring
        self.iD = int(ring[np.argmin(np.abs(ph[ring]))]); self.iC = int(ring[np.argmax(ph[ring])])
        assert abs(ph[self.iD]) < 1e-6 and abs(ph[self.iC] - 180.0) < 1e-6
        self.meta = {"geometry": asdict(g), "L_b": g.L_b, "k_ax": self.k_ax, "k_rot": self.k_rot,
                     "mesh": {k: (v if not isinstance(v, np.ndarray) else None) for k, v in msh["mesh"].items()},
                     "nodes": int(n), "cells": int(hexes.shape[0]), "unknowns": int(nfull),
                     "free_unknowns": int((~fixed).sum()), "ties": len(ties), "root_pairs": int(rp.shape[0]),
                     "patch_nodes": [int(p.size) for p in msh["patches"]]}

    def solve(self, value: float, mode: str = "hencky", z0=None, control: str = "rotation", **kw):
        """Rotation control: theta = value, w0 free (pure bending). Axial control: w0 = value, theta = 0 (tension
        through the tube's end section kept plane and parallel)."""
        self.bolts.delta[:] = self.delta
        self.prob = self.probs[control]
        self.control = control
        z = (self.z if z0 is None else z0).copy()
        if control == "rotation":
            z[self.ith] = value
        else:
            z[self.ith] = 0.0
            z[self.iw0] = value
        with direct_solver_up_to(self.nfull):
            z, rep = self.prob.solve(z, mode=mode, **kw)
        self.z = z
        return z, rep

    def bolt_forces(self, z):
        return self.bolts._law(z[self.ndof + 3 * np.arange(self.nb)] + self.delta)[0]

    def readings(self, z, rep) -> dict:
        g = self.g
        u = (self.T @ z).reshape(-1, 3)
        M = 2.0 * float(rep["grad"][self.ith])
        yr = self.nodes[self.ring, 1]
        A = np.column_stack([np.ones(yr.size), -yr])
        c0, th_sec = np.linalg.lstsq(A, u[self.ring, 2], rcond=None)[0]
        bz = u[self.msh["bottom"], 2]
        axial = getattr(self, "control", "rotation") == "axial"
        return {"theta_end": float(z[self.ith]), "w0": float(z[self.iw0]), "M_kNm": M / 1e6,
                "T_kN": (2.0 * float(rep["grad"][self.iw0]) / 1e3) if axial else 0.0,
                "delta_ring_mm": float(u[self.iD, 2] + u[self.iC, 2]),
                "pdas_iterations": rep.get("pdas_iterations"),
                "Theta_D": float(u[self.iD, 2] / g.d), "uz_D": float(u[self.iD, 2]), "uz_C": float(u[self.iC, 2]),
                "theta_section": float(th_sec), "w_section": float(c0),
                "bolt_force_kN": [float(b) / 1e3 for b in self.bolt_forces(z)],
                "contact_fraction": float((bz <= 1e-9 * max(np.abs(u).max(), 1e-300)).mean()),
                "reaction_y_N": float(rep["grad"][3 * self.iy + 1]),
                "kkt": {k: rep[k] for k in ("min_gap", "min_lambda", "max_complementarity", "max_lambda_inactive",
                                           "max_residual_unconstrained")},
                "iterations": rep["iterations"], "converged": rep["converged"],
                "plastic_points": rep.get("plastic_points"), "max_von_mises": self.max_von_mises()}

    def max_von_mises(self) -> dict:
        """Largest von Mises stress at the Gauss points of each body, from the last evaluation (MPa)."""
        from .plasticity import von_mises
        names = {0: "plate", 1: "tube", 2: "weld"}
        out = {}
        hex_sets = [s for s in self.sets if isinstance(s, PlasticHexSet)]
        parts = [k for k in (0, 1, 2) if (self.msh["part"] == k).any()]
        for k, s in zip(parts, hex_sets):
            if s._trial is not None:
                out[names[k]] = float(von_mises(s._trial["sig"]).max())
        return out

    def set_preload(self, N_target: float, mode: str = "hencky", tol: float = 1e-6, max_it: int = 30):
        """Pre-shortening per bolt so that every bolt carries N_target at theta = 0 (fixed point on delta)."""
        self.delta = np.full(self.nb, N_target / self.k_ax)
        hist = []
        for _ in range(max_it):
            snap = [s.snapshot() for s in self.sets]
            z, rep = self.solve(0.0, mode=mode, z0=np.zeros(self.nfull))
            N = self.bolt_forces(z)
            hist.append((self.delta.copy(), N.copy()))
            if np.abs(N / N_target - 1).max() < tol:
                break
            for s, sn in zip(self.sets, snap):
                s.restore(sn)
            self.delta = self.delta * N_target / N
        return {"delta": self.delta.copy(), "forces_N": N.copy(), "iterations": len(hist)}

    def commit(self):
        for s in self.sets:
            s.commit()


__all__ = ["FlangeSplice", "fidalgo", "MESHES", "build", "mesh_checks", "cyl", "SpliceModel"]
