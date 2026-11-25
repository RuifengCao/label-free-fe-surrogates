import sys, time
import numpy as np
joint, data, member = sys.argv[1:4]
sys.path.insert(0, joint)
from f2.data import load_export
from f2.evaluate import clean
from f2.instance import ExportedProblem
from f2.precond import ElasticContactStep
from fejoint.contact import solve_signorini

ex, q = load_export(f"{data}/inst/{member}.npz")
lab = np.load(f"{data}/labels/{member}.npz")
z_pre = np.load(f"{data}/pre/{member}.npz")["z"].astype(float)
t0 = time.time(); E = ElasticContactStep(ex, z_pre); t_setup = time.time() - t0
print(f"set-up {t_setup:.1f} s; contact unknowns {E.c.size}; inner unknowns {E.i.size}; S symmetric positive: min eig {np.linalg.eigvalsh(E.S).min():.4g}")
P = ExportedProblem(ex)
for lam in (1.0, 0.25):
    k = int(np.argmin(np.abs(lab["lam"] - lam))); Theta = float(lab["Theta"][k]); Pi_ref = float(lab["Pi"][k])
    z = z_pre.copy(); z[P.prob.cidx] = np.maximum(z[P.prob.cidx], 0.0)
    clean(P); P.loading.delta[:] = -Theta
    E0, g, _, _ = P.prob.evaluate(z, "hencky", tangent=False)
    t0 = time.time(); d, act, its = E.step(z, g); t_step = time.time() - t0
    # the same step by the reference's sub-solver with the same matrix
    clean(P); P.loading.delta[:] = 0.0
    _, _, K0, _ = P.prob.evaluate(z_pre, "hencky", tangent=True)
    free = P.prob.free
    t0 = time.time(); sol = solve_signorini(K0.tocsr()[free][:, free].tocsr(), -g[free], P.prob.c_free, g=z[P.prob.cidx]); t_ref = time.time() - t0
    dref = np.zeros_like(z); dref[free] = sol["x"]
    zt = z + d; zt[P.prob.cidx] = np.maximum(zt[P.prob.cidx], 0.0)
    clean(P); P.loading.delta[:] = -Theta
    E1, _, _, _ = P.prob.evaluate(zt, "hencky", tangent=False)
    r = P.evaluate(zt, Theta)
    print(f"lam {lam}: step {t_step * 1e3:.0f} ms ({its} active-set iterations) against {t_ref:.1f} s for the sub-solver; "
          f"difference of the two steps {np.abs(d - dref).max() / np.abs(dref).max():.2e}; held contacts {int(act.sum())}/{act.size}; "
          f"energy excess {E0 / Pi_ref - 1:.3%} -> {E1 / Pi_ref - 1:.3%}; theta/ref {r['theta'] / float(lab['theta'][k]):.3f}, ThetaD/ref {r['ThetaD'] / float(lab['ThetaD'][k]):.3f}")
