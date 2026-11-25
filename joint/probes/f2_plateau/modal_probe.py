"""Sandbox diagnostic: how much of the elastic contact step from the closed joint lies in the softest modes of the
member's elastic stiffness with the splice plane free (heads and root held)?"""
import sys, time
import numpy as np
import scipy.sparse.linalg as spla
joint, data, member = sys.argv[1:4]
sys.path.insert(0, joint)
from f2.data import load_export
from f2.evaluate import clean
from f2.instance import ExportedProblem, FLAGS
from f2.precond import ElasticContactStep

ex, q = load_export(f"{data}/inst/{member}.npz")
lab = np.load(f"{data}/labels/{member}.npz")
z_pre = np.load(f"{data}/pre/{member}.npz")["z"].astype(float)
E = ElasticContactStep(ex, z_pre)
P = ExportedProblem(ex); prob = P.prob
clean(P); P.loading.delta[:] = 0.0
_, _, K0, _ = prob.evaluate(z_pre, "hencky", tangent=True)
K0 = K0.tocsr()
flags = np.asarray(ex["node_flags"]).astype(bool)
cidx = prob.cidx; node = cidx // 3
plane = flags[node, FLAGS.index("splice_plane")] & ~flags[node, FLAGS.index("bearing_patch")] & ~flags[node, FLAGS.index("root_tube")]
held = prob.fixed.copy(); held[cidx[~plane]] = True
idx = np.nonzero(~held)[0]
A = K0[idx][:, idx].tocsc()
t0 = time.time()
m = 60
w, V = spla.eigsh(A, k=m, sigma=0.0, which="LM")
order = np.argsort(w); w, V = w[order], V[:, order]
print(f"{m} softest modes of the open stiffness in {time.time() - t0:.1f} s; eigenvalues {w[0]:.3g} ... {w[9]:.3g} ... {w[-1]:.3g}")
for lam in (1.0, 0.25):
    k = int(np.argmin(np.abs(lab["lam"] - lam))); Theta = float(lab["Theta"][k]); Pi_ref = float(lab["Pi"][k])
    th_ref, tD_ref = float(lab["theta"][k]), float(lab["ThetaD"][k])
    z = z_pre.copy(); z[cidx] = np.maximum(z[cidx], 0.0)
    clean(P); P.loading.delta[:] = -Theta
    E0, g, _, _ = prob.evaluate(z, "hencky", tangent=False)
    d = E.step(z, g)[0]
    # the closed-joint solution first: the step with every contact held (the plateau), then what is left
    held_all = prob.fixed.copy(); held_all[cidx] = True
    ib = np.nonzero(~held_all)[0]
    db = np.zeros_like(z); db[ib] = spla.splu(K0[ib][:, ib].tocsc()).solve(-g[ib])
    rest = d - db                                              # from the closed-joint state to the step's end
    def state(dd):
        zt = z + dd; zt[cidx] = np.maximum(zt[cidx], 0.0)
        clean(P); r = P.evaluate(zt, Theta)
        return r["Pi"] / Pi_ref - 1.0, r["theta"] / th_ref, r["ThetaD"] / tD_ref
    print(f"lam {lam}: closed-joint state: excess {state(db)[0]:.2%}, theta/ref {state(db)[1]:.3f}, ThetaD/ref {state(db)[2]:.3f}; "
          f"full step: excess {state(d)[0]:.2%}, theta/ref {state(d)[1]:.3f}, ThetaD/ref {state(d)[2]:.3f}")
    for mm in (1, 2, 3, 5, 10, 20, 40, 60):
        Vm = V[:, :mm]
        c = Vm.T @ rest[idx]
        proj = np.zeros_like(z); proj[idx] = Vm @ c
        cap = np.linalg.norm(proj[idx]) / np.linalg.norm(rest[idx])
        ex_, th_, tD_ = state(db + proj)
        print(f"   closed-joint state + the {mm:2d} softest modes' part of the rest: L2 share {cap:.3f}; excess {ex_:9.2%}; theta/ref {th_:.3f}; ThetaD/ref {tD_:.3f}")
