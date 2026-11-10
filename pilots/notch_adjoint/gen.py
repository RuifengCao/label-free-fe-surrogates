"""Notched-plate family: geometry, graded P2 mesh, stiffness, unit loads, quantity of interest, references.

Plane stress, E = 1, nu = 0.3; plate [0, 1] x [-1, 1], bottom edge clamped, top edge loaded.
U-shaped edge notch on x = 0: depth d, root radius rho, centre height y_c (see PLAN.md).
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import triangle as tr
from skfem import MeshTri, Basis, FacetBasis, ElementTriP2, ElementVector, BilinearForm, LinearForm, asm, condense, solve
from skfem.helpers import grad
from skfem.models.elasticity import linear_elasticity

E, NU = 1.0, 0.3
MU = E / (2 * (1 + NU))
LAM_PS = E * NU / (1 - NU ** 2)          # plane-stress first Lame parameter
R_Q = 0.03                               # radius of the region of the quantity of interest


def sample_params(rng, n):
    out = []
    while len(out) < n:
        d = rng.uniform(0.15, 0.35)
        rho = rng.uniform(0.03, 0.10)
        yc = rng.uniform(-0.3, 0.3)
        if d >= rho + 0.03:
            out.append((d, rho, yc))
    return out


def pslg(d, rho, yc, n_arc=40):
    pts = [(0.0, -1.0), (1.0, -1.0), (1.0, 1.0), (0.0, 1.0), (0.0, yc + rho), (d - rho, yc + rho)]
    for k in range(1, n_arc):
        a = np.pi / 2 - np.pi * k / n_arc          # from +90 deg to -90 deg through 0 (the root)
        pts.append((d - rho + rho * np.cos(a), yc + rho * np.sin(a)))
    pts += [(d - rho, yc - rho), (0.0, yc - rho)]
    n = len(pts)
    segs = [(i, (i + 1) % n) for i in range(n)]
    return np.array(pts), np.array(segs)


def make_mesh(d, rho, yc, h_max=0.08):
    v, s = pslg(d, rho, yc)
    t = tr.triangulate(dict(vertices=v, segments=s), "pq30a%g" % (np.sqrt(3) / 4 * h_max ** 2))
    root = np.array([d, yc])
    h_min = rho / 6.0
    for _ in range(4):
        cen = t["vertices"][t["triangles"]].mean(axis=1)
        r = np.linalg.norm(cen - root, axis=1)
        h = h_min + (h_max - h_min) * np.clip(r / 0.6, 0.0, 1.0)
        t["triangle_max_area"] = np.sqrt(3) / 4 * h ** 2
        t = tr.triangulate(t, "rpq30a")
    return MeshTri(t["vertices"].T.copy(), t["triangles"].T.copy())


def build(params, solve_reference=True):
    d, rho, yc = params
    m = make_mesh(d, rho, yc)
    e = ElementVector(ElementTriP2())
    ib = Basis(m, e, intorder=4)
    K = asm(linear_elasticity(LAM_PS, MU), ib).tocsr()
    top = m.facets_satisfying(lambda x: np.isclose(x[1], 1.0))
    fb = FacetBasis(m, e, facets=top, intorder=4)
    F_t = asm(LinearForm(lambda v, w: v[1]), fb)
    F_b = asm(LinearForm(lambda v, w: v[1] * (w.x[0] - 0.5) / 0.5), fb)
    # quantity of interest: mean sigma_yy over elements whose centroids are within R_Q of the root point
    cen = m.p[:, m.t].mean(axis=1)
    elems = np.nonzero(np.hypot(cen[0] - d, cen[1] - yc) < R_Q)[0]
    qb = Basis(m, e, elements=elems, intorder=4)
    area = asm(LinearForm(lambda v, w: v), Basis(m, ElementTriP2(), elements=elems, intorder=4)).sum()
    q = asm(LinearForm(lambda v, w: E / (1 - NU ** 2) * (NU * grad(v)[0, 0] + grad(v)[1, 1])), qb) / area
    D = ib.get_dofs(lambda x: np.isclose(x[1], -1.0)).flatten()
    # node locations and their x/y dof indices (vertices, then edge midpoints)
    pts = np.hstack([m.p, m.p[:, m.facets].mean(axis=1)]).T
    ix = np.concatenate([ib.nodal_dofs[0], ib.facet_dofs[0]])
    iy = np.concatenate([ib.nodal_dofs[1], ib.facet_dofs[1]])
    assert np.allclose(ib.doflocs[:, ix].T, pts) and np.allclose(ib.doflocs[:, iy].T, pts)
    inst = dict(params=np.array(params), pts=pts, ix=ix, iy=iy, K=K, F_t=F_t, F_b=F_b, q=q, D=D,
                n_dof=K.shape[0], n_elem=m.t.shape[1], n_qoi_elems=len(elems), qoi_area=area)
    if solve_reference:
        def sol(f):
            x = np.zeros(K.shape[0])
            return solve(*condense(K, f, x=x, D=D))
        inst["U_t"], inst["U_b"], inst["Z"] = sol(F_t), sol(F_b), sol(q)
    return inst


if __name__ == "__main__":
    import time
    rng = np.random.default_rng(2026)
    for p in sample_params(rng, 3) + [(0.33, 0.03, 0.0), (0.18, 0.10, 0.25)]:
        t0 = time.time()
        I = build(p)
        Jt = I["q"] @ I["U_t"]
        nominal = 1.0 / (1.0 - p[0])                     # net-section stress for unit remote tension
        print("d=%.3f rho=%.3f yc=%+.3f dofs=%d elems=%d qoi_elems=%d  J_t=%.3f  J_t/net=%.2f  ||Z||_K=%.3f  %.1fs" % (
            *p, I["n_dof"], I["n_elem"], I["n_qoi_elems"], Jt, Jt / nominal, np.sqrt(I["Z"] @ I["K"] @ I["Z"]), time.time() - t0))
