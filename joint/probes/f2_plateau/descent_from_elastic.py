"""Sandbox diagnostic: from the elastic contact solution of a level, how fast do first-order iterations on the field
itself (Jacobi-scaled projected gradient with backtracking) and modified Newton steps close what plasticity leaves?"""
import sys, time
import numpy as np
joint, data, member = sys.argv[1:4]; lam = float(sys.argv[4]); n_it = int(sys.argv[5])
sys.path.insert(0, joint); sys.path.insert(0, joint + "/../src")
from f2.data import load_export
from f2.evaluate import clean
from f2.instance import ExportedProblem
from f2.precond import ElasticContactStep

ex, q = load_export(f"{data}/inst/{member}.npz")
lab = np.load(f"{data}/labels/{member}.npz")
z_pre = np.load(f"{data}/pre/{member}.npz")["z"].astype(float)
k = int(np.argmin(np.abs(lab["lam"] - lam))); Theta = float(lab["Theta"][k]); Pi_ref = float(lab["Pi"][k])
th_ref, tD_ref = float(lab["theta"][k]), float(lab["ThetaD"][k])
S = ElasticContactStep(ex, z_pre)
P = ExportedProblem(ex); prob = P.prob; cidx, free, fixed = prob.cidx, prob.free, prob.fixed
clean(P); P.loading.delta[:] = 0.0
_, _, K0, _ = prob.evaluate(z_pre, "hencky", tangent=True)
diag = K0.tocsr().diagonal()

def energy(z):
    clean(P); P.loading.delta[:] = -Theta
    E, g, _, _ = prob.evaluate(z, "hencky", tangent=False)
    return E, g
def project(z):
    z = z.copy(); z[cidx] = np.maximum(z[cidx], 0.0); z[fixed] = 0.0; return z
def read(z):
    clean(P); r = P.evaluate(z, Theta); return r["theta"] / th_ref, r["ThetaD"] / tD_ref

zc = project(z_pre); E, g = energy(zc)
z_el = project(zc + S.step(zc, g)[0])
for name in ("modified Newton", "jacobi"):
    z = z_el.copy(); E, g = energy(z); t = 1.0; t0 = time.time(); evals = 1
    print(f"{name} from the elastic solution at lam {lam}:")
    for it in range(n_it + 1 if name == "jacobi" else 11):
        if it in (0, 1, 2, 3, 5, 10, 20, 40, 80, 160, 320) or it == n_it:
            th, tD = read(z)
            print(f"   it {it:4d}: energy excess {E / Pi_ref - 1:9.4%}  theta/ref {th:.3f}  ThetaD/ref {tD:.3f}  ({evals} energy evaluations, {time.time() - t0:.0f} s)", flush=True)
        if name == "modified Newton":
            z = project(z + S.step(z, g)[0]); E, g = energy(z); evals += 1
            continue
        d = np.zeros_like(z); d[free] = -g[free] / diag[free]
        stuck = (z[cidx] <= 0.0) & (d[cidx] < 0.0); d[cidx[stuck]] = 0.0
        t = 2.0 * t
        while True:
            zt = project(z + t * d)
            try:
                Et, gt = energy(zt)
            except RuntimeError:
                Et = np.inf
            evals += 1
            if np.isfinite(Et) and Et <= E + 1e-4 * float(g @ (zt - z)):
                break
            t *= 0.5
            if t < 1e-12:
                break
        if t < 1e-12:
            print("   line search failed"); break
        z, E, g = zt, Et, gt
