"""A field of one mesh of a member carried to another mesh of the same member (development, 25 November 2026;
nothing here is stamped).

The source field's physical displacements u = T z are a trilinear finite-element function on the source mesh's
hexahedra. They are evaluated at the target mesh's nodes: each node is sought in the source elements of the parts
(plate, tube, weld) it belongs to, so that the two nodes of a root pair, which share a position, take their values
from their own parts; a node that lies in no source element, as on a curved face that the two meshes cut
differently, takes the nearest element's shape functions continued beyond the element. The target unknowns are then
set so that the target's physical displacements T z are these values wherever the target leaves a nodal unknown
free:

    an unknown that is a displacement itself          z_i = u_i
    an unknown that T combines with others            z_i = (u_i - sum over j != i of T_ij z_j) / T_ii
        (a head's separation in a bearing patch, a root's opening)
    the heads' unknowns, w0 and theta                 copied
    the fixed unknowns                                zero (the caller's; so is keeping the contact unknowns >= 0)

All of this is linear in the source field: prolongation() returns the matrix A with z_target = A z_source.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from scipy.spatial import cKDTree

from fejoint.hex8i import XI
from .instance import FLAGS, PARTS

PART_FLAGS = ("plate", "tube", "weld")            # the node flags of the parts, in the order of PARTS


def _shape(xi: np.ndarray):
    """Shape functions (P, 8) and their derivatives (P, 8, 3) of the trilinear hexahedron at xi (P, 3)."""
    a = 1.0 + xi[:, None, :] * XI[None, :, :]                 # (P, 8, 3)
    N = a.prod(axis=2) / 8.0
    dN = np.empty(a.shape)
    dN[:, :, 0] = XI[None, :, 0] * a[:, :, 1] * a[:, :, 2] / 8.0
    dN[:, :, 1] = XI[None, :, 1] * a[:, :, 0] * a[:, :, 2] / 8.0
    dN[:, :, 2] = XI[None, :, 2] * a[:, :, 0] * a[:, :, 1] / 8.0
    return N, dN


EXTEND = 1.5        # a node may lie this far beyond an element, in local coordinates, and still take its continued functions


def _iterate(Xc, p, steps: int, box: float):
    """Damped Gauss-Newton on |X(xi) - p|^2 from the element's centre, steps of at most a half, xi kept in
    [-box, box]^3. Returns xi and the largest component of X(xi) - p."""
    xi = np.zeros_like(p)
    eye = np.eye(3)
    for _ in range(steps):
        N, dN = _shape(xi)
        r = np.einsum("pa,pai->pi", N, Xc) - p
        J = np.einsum("paj,pai->pij", dN, Xc)                  # d X_i / d xi_j
        H = np.einsum("pki,pkj->pij", J, J)
        H = H + (1e-12 * np.einsum("pii->p", H))[:, None, None] * eye
        d = np.linalg.solve(H, np.einsum("pki,pk->pi", J, r)[..., None])[..., 0]
        xi = np.clip(xi - np.clip(d, -0.5, 0.5), -box, box)
    N, _ = _shape(xi)
    return xi, np.abs(np.einsum("pa,pai->pi", N, Xc) - p).max(axis=1)


def _project(Xc, p, steps: int):
    """The point of each element nearest to its point: |X(xi) - p|^2 minimised over [-1, 1]^3 from the element's
    centre. Each step is a Gauss-Newton step in the coordinates that are free to move (a coordinate at a bound
    stays there while the descent points out of the box), cut to the box and halved until the distance falls.
    Returns xi and the distances."""
    def at(x):
        N, dN = _shape(x)
        return np.einsum("pa,pai->pi", N, Xc) - p, np.einsum("paj,pai->pij", dN, Xc)

    xi = np.zeros_like(p)
    eye = np.eye(3)
    r, J = at(xi)
    f = (r ** 2).sum(axis=1)
    for _ in range(steps):
        g = np.einsum("pki,pk->pi", J, r)
        held = ((xi >= 1.0) & (g < 0)) | ((xi <= -1.0) & (g > 0))
        H = np.einsum("pki,pkj->pij", J, J)
        H = H + (1e-12 * np.einsum("pii->p", H) + 1e-300)[:, None, None] * eye
        H = np.where(held[:, :, None] | held[:, None, :], eye[None], H)
        d = -np.linalg.solve(H, np.where(held, 0.0, g)[..., None])[..., 0]
        need = np.ones(p.shape[0], bool)
        t = 1.0
        for _h in range(20):
            cand = np.clip(xi + t * d, -1.0, 1.0)
            fc = (at(cand)[0] ** 2).sum(axis=1)
            ok = need & (fc < f)
            xi[ok], f[ok] = cand[ok], fc[ok]
            need &= ~ok
            if not need.any():
                break
            t *= 0.5
        r, J = at(xi)
    return xi, np.sqrt(f)


def locate(nodes: np.ndarray, hexes: np.ndarray, pts: np.ndarray, k: int = 24, steps: int = 60):
    """For each point: an element, local coordinates xi (P, 3) in it, by how much the largest coordinate exceeds 1
    (zero for a point inside), and the distance left between X(xi) and the point (zero unless projected).

    The candidates of a point are the elements whose bounding boxes (widened by a twentieth of their size) hold it,
    nearest centroid first, then the other elements by their centroids' distance, k in all. In each candidate
    X(xi) = point is solved by a damped Gauss-Newton iteration from the element's centre; the candidate with the
    smallest excess is taken if that excess is at most EXTEND (the element's functions continued beyond it: a node
    on a curved face that the two meshes cut differently, or in a hole that they shape differently). A point with
    no such candidate (beyond a fillet's sloping face, where two edges of the element are in line and the map has
    no nearby solution outside) takes the nearest point of the nearest element instead."""
    X = np.asarray(nodes, float)[np.asarray(hexes)]            # (E, 8, 3)
    k = min(k, X.shape[0])
    lo, hi, cen = X.min(axis=1), X.max(axis=1), X.mean(axis=1)
    m = 0.05 * (hi - lo).max(axis=1)
    cand = np.empty((pts.shape[0], k), int)
    for a in range(0, pts.shape[0], 2048):                     # in slices, to bound the memory
        q = pts[a:a + 2048]
        inside = ((q[:, None, :] >= (lo - m[:, None])[None]) & (q[:, None, :] <= (hi + m[:, None])[None])).all(axis=2)
        d2 = ((q[:, None, :] - cen[None]) ** 2).sum(axis=2)
        d2 = np.where(inside, d2, d2 + 4.0 * d2.max() + 1.0)
        cand[a:a + 2048] = np.argsort(d2, axis=1, kind="stable")[:, :k]
    def solve_in(points, cands, n_steps):
        kk = cands.shape[1]
        Xc = X[cands.ravel()]                                  # (P kk, 8, 3)
        p = np.repeat(points, kk, axis=0)
        xi, res = _iterate(Xc, p, n_steps, 4.0)
        out = np.maximum(np.abs(xi).max(axis=1) - 1.0, 0.0)
        out[out < 1e-9] = 0.0
        out[(res > 1e-9 * np.ptp(Xc, axis=1).max(axis=1)) | (out > EXTEND)] = np.inf
        out = out.reshape(-1, kk)
        b = out.argmin(axis=1)
        r = np.arange(points.shape[0])
        return cands[r, b], xi.reshape(-1, kk, 3)[r, b], out[r, b]

    # most points lie inside one of their first few candidates, where a few steps settle; the rest get all k
    elem, xi, out = solve_in(pts, cand[:, :min(k, 6)], 12)
    again = np.nonzero(out > 0)[0]
    if again.size:
        elem[again], xi[again], out[again] = solve_in(pts[again], cand[again], steps)
    dist = np.zeros(pts.shape[0])
    miss = np.nonzero(~np.isfinite(out))[0]
    if miss.size:                                              # the nearest point of the nearest candidate
        xb, d = _project(X[cand[miss].ravel()], np.repeat(pts[miss], k, axis=0), steps)
        d = d.reshape(-1, k)
        b = d.argmin(axis=1)
        r2 = np.arange(miss.size)
        elem[miss], xi[miss], out[miss], dist[miss] = cand[miss, b], xb.reshape(-1, k, 3)[r2, b], 0.0, d[r2, b]
    return elem, xi, out, dist


def interpolation(ex_s: dict, ex_t: dict):
    """(3 n_t, 3 n_s) sparse: the source's nodal displacements evaluated at the target's nodes, and a report. A
    target node at the position of a source node of one of its parts takes that node's value as it is."""
    ns, nt = np.asarray(ex_s["nodes"], float), np.asarray(ex_t["nodes"], float)
    flags = np.asarray(ex_t["node_flags"]).astype(bool)
    W = np.zeros((nt.shape[0], 8))
    over = np.full(nt.shape[0], np.inf)
    dist = np.full(nt.shape[0], np.inf)
    conn = np.zeros((nt.shape[0], 8), int)
    same = np.zeros(nt.shape[0], bool)
    close = 1e-9 * float(np.ptp(ns, axis=0).max())
    for part, flag in zip(PARTS, PART_FLAGS):
        sel = np.nonzero(flags[:, FLAGS.index(flag)])[0]
        hexes = np.asarray(ex_s[f"hexes_{part}"])
        if sel.size == 0 or hexes.shape[0] == 0:
            continue
        own = np.unique(hexes)
        d0, j = cKDTree(ns[own]).query(nt[sel])
        hit = d0 <= close
        idx = sel[hit]
        W[idx], conn[idx], over[idx], dist[idx], same[idx] = 0.0, own[j[hit]][:, None], 0.0, 0.0, True
        W[idx, 0] = 1.0
        rest = sel[~hit & ~same[sel]]
        if rest.size == 0:
            continue
        e, x, o, d = locate(ns, hexes, nt[rest])
        take = (d < dist[rest]) | ((d == dist[rest]) & (o < over[rest]))
        idx = rest[take]
        W[idx], over[idx], dist[idx], conn[idx] = _shape(x[take])[0], o[take], d[take], hexes[e[take]]
    if not np.isfinite(dist).all():
        raise RuntimeError(f"{int((~np.isfinite(dist)).sum())} target nodes belong to no part of the source mesh")
    rows = np.repeat(np.arange(nt.shape[0]), 8)
    P1 = sp.csr_matrix((W.ravel(), (rows, conn.ravel())), shape=(nt.shape[0], ns.shape[0]))
    P1.eliminate_zeros()
    P = sp.kron(P1, sp.identity(3, format="csr"), format="csr")
    info = {"target_nodes": int(nt.shape[0]), "source_nodes": int(ns.shape[0]), "at_a_source_node": int(same.sum()),
            "continued_beyond_an_element": int((over > 1e-6).sum()), "largest_excess": float(over.max()),
            "projected_onto_an_element": int((dist > 0).sum()), "largest_projection_distance_mm": float(dist.max()),
            "smallest_weight": float(W.min()), "largest_weight": float(W.max())}
    return P, info


def _T(ex: dict) -> sp.csr_matrix:
    return sp.csr_matrix((np.asarray(ex["T_val"], float), (np.asarray(ex["T_row"]), np.asarray(ex["T_col"]))),
                         shape=tuple(int(s) for s in np.asarray(ex["T_shape"])))


def prolongation(ex_s: dict, ex_t: dict):
    """(A, info): A (n_z target, n_z source) sparse with z_target = A z_source (see the module's text), and a
    report with the interpolation's and the numbers of unknowns of each kind."""
    n_s, n_t = int(np.asarray(ex_s["nodes"]).shape[0]), int(np.asarray(ex_t["nodes"]).shape[0])
    nz_s, nz_t = int(np.asarray(ex_s["v"]).size), int(np.asarray(ex_t["v"]).size)
    tail = nz_t - 3 * n_t
    if tail != nz_s - 3 * n_s:
        raise RuntimeError("the two meshes do not have the same unknowns beyond the nodal ones")
    P, info = interpolation(ex_s, ex_t)
    T_s, T_t = _T(ex_s), _T(ex_t)
    U = (P @ T_s).tocsr()                                      # (3 n_t, nz_s): the values wanted at the target's nodes
    fixed = np.asarray(ex_t["fixed"], bool)
    free = ~fixed[:3 * n_t]
    Tn = T_t[:, :3 * n_t].tocsr()
    diag = np.asarray(Tn.diagonal()).ravel()
    alone = np.asarray((Tn != 0).sum(axis=1)).ravel() == 1     # the row's only nodal entry
    others = np.asarray((T_t[:, 3 * n_t:] != 0).sum(axis=1)).ravel() > 0
    ordinary = free & alone & ~others & (diag == 1.0)
    special = free & ~ordinary
    if (np.abs(diag[special]) != 1.0).any():
        raise RuntimeError("a free nodal unknown does not enter its own displacement with +1 or -1")
    Tx = Tn[special][:, special].tolil()
    Tx.setdiag(0.0)
    if Tx.tocsr().count_nonzero():
        raise RuntimeError("a combined unknown depends on another combined unknown")
    pick = lambda mask: sp.csr_matrix((np.ones(int(mask.sum())), (np.nonzero(mask)[0], np.nonzero(mask)[0])),  # noqa: E731
                                      shape=(nz_t, 3 * n_t))
    C = sp.csr_matrix((np.ones(tail), (3 * n_t + np.arange(tail), 3 * n_s + np.arange(tail))), shape=(nz_t, nz_s))
    Z0 = pick(ordinary) @ U + C
    inv = np.zeros(3 * n_t)
    inv[special] = 1.0 / diag[special]
    A = (Z0 + pick(special) @ sp.diags(inv) @ (U - T_t @ Z0)).tocsr()
    A.eliminate_zeros()
    info.update({"ordinary": int(ordinary.sum()), "combined": int(special.sum()), "fixed_nodal": int((~free).sum()),
                 "beyond_nodal": int(tail), "nonzeros": int(A.nnz)})
    return A, info


def check(ex_s: dict, ex_t: dict, A, seed: int = 0) -> dict:
    """How well T_target A z reproduces the interpolated displacements for a random source field: the largest
    difference over the free nodal unknowns' own displacements (zero up to round-off by construction), and over
    all nodes (the hanging nodes and the end section follow their own constraints)."""
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(int(np.asarray(ex_s["v"]).size))
    z[np.asarray(ex_s["fixed"], bool)] = 0.0
    P, _ = interpolation(ex_s, ex_t)
    want = P @ (_T(ex_s) @ z)
    zt = A @ z
    zt[np.asarray(ex_t["fixed"], bool)] = 0.0
    got = _T(ex_t) @ zt
    n_t = int(np.asarray(ex_t["nodes"]).shape[0])
    free = ~np.asarray(ex_t["fixed"], bool)[:3 * n_t]
    return {"largest_difference_free": float(np.abs(got - want)[free].max()),
            "largest_difference_all": float(np.abs(got - want).max()), "scale": float(np.abs(want).max())}


__all__ = ["locate", "interpolation", "prolongation", "check", "PART_FLAGS"]
