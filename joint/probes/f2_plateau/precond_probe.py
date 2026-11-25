"""Sandbox diagnostic (exploratory, nothing stamped): how fast do descent iterations on the field itself reach the
reference of one member at one device rotation, with and without the member's elastic stiffness as a preconditioner?

No network: the unknowns z are iterated directly, from the preload state (joint closed). Variants:

    plain     projected gradient, Armijo backtracking from the last accepted step length
    jacobi    the same with the gradient divided by the diagonal of the elastic tangent K0 (at the preload state)
    bonded    step = -K0^-1 g on the unknowns that are not contact unknowns (contacts held); the contact unknowns take
              a projected Jacobi step
    open      step = -K0^-1 g with the splice-plane contacts free and the other contacts held; projected
    qp        step = the minimiser of the quadratic model with K0 under the contact constraints (the reference's
              Signorini sub-solver with K0 in place of the current tangent): a modified Newton step

    python3 -I precond_probe.py JOINT_DIR DATA_DIR MEMBER LAM OUT.json [ITERS]
"""
import json
import sys
import time

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

joint, data, member, lam_s, out_path = sys.argv[1:6]
iters = int(sys.argv[6]) if len(sys.argv) > 6 else 40
sys.path.insert(0, joint)
from f2.data import load_export                                  # noqa: E402
from f2.evaluate import clean                                    # noqa: E402
from f2.instance import ExportedProblem, FLAGS                   # noqa: E402
from fejoint.contact import solve_signorini                      # noqa: E402

ex, q = load_export(f"{data}/inst/{member}.npz")
lab = np.load(f"{data}/labels/{member}.npz")
z_pre = np.load(f"{data}/pre/{member}.npz")["z"].astype(float)
lam = float(lam_s)
k = int(np.argmin(np.abs(lab["lam"] - lam)))
assert abs(float(lab["lam"][k]) - lam) < 1e-12, "LAM must be one of the label's levels"
Theta, Pi_ref = float(lab["Theta"][k]), float(lab["Pi"][k])
th_ref, tD_ref, z_ref = float(lab["theta"][k]), float(lab["ThetaD"][k]), lab["z"][k].astype(float)

P = ExportedProblem(ex)
prob = P.prob
free = prob.free
cidx = prob.cidx
flags = np.asarray(ex["node_flags"]).astype(bool)
node, comp = cidx // 3, cidx % 3
kind = np.where(flags[node, FLAGS.index("bearing_patch")], "head",
                np.where(flags[node, FLAGS.index("root_tube")], "root",
                         np.where(flags[node, FLAGS.index("splice_plane")], "plane", "other")))
print("contact unknowns:", {str(t): int((kind == t).sum()) for t in np.unique(kind)}, "components", np.unique(comp).tolist())


def energy(z, tangent=False):
    clean(P)
    P.loading.delta[:] = -Theta
    E, g, H, _ = prob.evaluate(z, "hencky", tangent=tangent)
    return E, g, H


def readings(z):
    clean(P)
    r = P.evaluate(z, Theta)
    return r["theta"], r["ThetaD"]


# the elastic tangent at the preload state (device at rest)
clean(P)
P.loading.delta[:] = 0.0
_, _, K0, _ = prob.evaluate(z_pre, "hencky", tangent=True)
K0 = K0.tocsr()
diag = K0.diagonal()
E_ref, g_ref, _ = energy(z_ref)
print(f"member {member} lam {lam} Theta {Theta:.6f}: Pi_ref {Pi_ref:.6g} (re-evaluated {E_ref:.6g}), open contacts in the reference "
      f"{int((z_ref[cidx] > 1e-9).sum())} of {cidx.size}")
E0, g0, _ = energy(z_pre)
print(f"start (preload state): energy excess {E0 / Pi_ref - 1:.3%}")

is_c = np.zeros(K0.shape[0], bool); is_c[cidx] = True
fixed = prob.fixed
held_all = fixed | is_c                                           # bonded: every contact held
plane = np.zeros(K0.shape[0], bool); plane[cidx[kind == "plane"]] = True
held_open = fixed | (is_c & ~plane)                               # open: only the splice plane free


def factor(held):
    idx = np.nonzero(~held)[0]
    A = K0[idx][:, idx].tocsc()
    t0 = time.time()
    lu = spla.splu(A)
    return idx, lu, time.time() - t0


idx_b, lu_b, t_b = factor(held_all)
idx_o, lu_o, t_o = factor(held_open)
print(f"factorisations: bonded {idx_b.size} unknowns {t_b:.2f} s; open {idx_o.size} unknowns {t_o:.2f} s")
try:
    w = spla.eigsh(K0[idx_o][:, idx_o].tocsc(), k=1, sigma=0.0, which="LM", return_eigenvectors=False)
    wmax = spla.eigsh(K0[idx_o][:, idx_o].tocsc(), k=1, which="LA", return_eigenvectors=False)
    print(f"open stiffness: smallest eigenvalue {float(w[0]):.4g}, largest {float(wmax[0]):.4g}, ratio {float(wmax[0] / w[0]):.3g}")
except Exception as err:                                          # noqa: BLE001
    print("eigenvalues of the open stiffness not found:", type(err).__name__, err)


def project(z):
    z = z.copy()
    z[cidx] = np.maximum(z[cidx], 0.0)
    z[fixed] = 0.0
    return z


def direction(name, z, g):
    d = np.zeros_like(z)
    if name == "plain":
        d[free] = -g[free]
    elif name == "jacobi":
        d[free] = -g[free] / diag[free]
    elif name == "bonded":
        d[idx_b] = lu_b.solve(-g[idx_b])
        d[cidx] = -g[cidx] / diag[cidx]
    elif name == "open":
        d[idx_o] = lu_o.solve(-g[idx_o])
    elif name == "qp":
        sol = solve_signorini(K0[free][:, free].tocsr(), -g[free], prob.c_free, g=z[cidx])
        d[free] = sol["x"]
    # a contact at zero that the direction pushes further down does not move
    stuck = (z[cidx] <= 0.0) & (d[cidx] < 0.0)
    d[cidx[stuck]] = 0.0
    return d


def run(name, n_it):
    z = project(z_pre)
    E, g, _ = energy(z)
    t = 1.0
    rows = []
    evals = 1
    t0 = time.time()
    for it in range(n_it + 1):
        th, tD = readings(z)
        rows.append({"it": it, "evals": evals, "excess": E / Pi_ref - 1.0, "theta": th / th_ref, "ThetaD": tD / tD_ref,
                     "open": int((z[cidx] > 1e-9).sum()), "err": float(np.linalg.norm(z - z_ref) / np.linalg.norm(z_ref))})
        if it == n_it:
            break
        d = direction(name, z, g)
        slope = float(g @ d)
        if slope >= 0.0:
            rows[-1]["note"] = "no descent direction"
            break
        t = min(1.0, 2.0 * t) if name in ("bonded", "open", "qp") else 2.0 * t
        while True:
            zt = project(z + t * d)
            try:
                Et, gt, _ = energy(zt)
            except RuntimeError:
                Et = np.inf
            evals += 1
            if np.isfinite(Et) and Et <= E + 1e-4 * float(g @ (zt - z)):
                break
            t *= 0.5
            if t < 1e-12:
                break
        if t < 1e-12:
            rows[-1]["note"] = "line search failed"
            break
        z, E, g = zt, Et, gt
    return rows, time.time() - t0


out = {"member": member, "lam": lam, "Theta": Theta, "contact_kinds": {str(t): int((kind == t).sum()) for t in np.unique(kind)},
       "start_excess": E0 / Pi_ref - 1.0, "runs": {}}
for name, n_it in (("qp", min(iters, 25)), ("open", iters), ("bonded", iters), ("jacobi", 4 * iters), ("plain", 4 * iters)):
    rows, sec = run(name, n_it)
    out["runs"][name] = {"rows": rows, "seconds": sec}
    pick = [r for r in rows if r["it"] in (0, 1, 2, 3, 5, 10, 20, 40, 80, 160) or r is rows[-1]]
    print(f"\n{name}: {len(rows) - 1} iterations, {rows[-1]['evals']} energy evaluations, {sec:.0f} s")
    for r in pick:
        print(f"   it {r['it']:4d}: energy excess {r['excess']:10.4%}  theta/ref {r['theta']:.3f}  ThetaD/ref {r['ThetaD']:.3f}  "
              f"open {r['open']:4d}  field error {r['err']:.3f}  {r.get('note', '')}")
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=1)
