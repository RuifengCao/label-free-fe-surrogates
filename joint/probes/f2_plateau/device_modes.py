"""Sandbox diagnostic: how soft is the member with and without the device's own unknowns? Softest eigenvalues of the
elastic stiffness at preload with the splice plane free (heads and root held), with theta and w0 free or held."""
import sys, time
import numpy as np
import scipy.sparse.linalg as spla
joint, data, member = sys.argv[1:4]
sys.path.insert(0, joint); sys.path.insert(0, joint + "/../src")
from f2.data import load_export
from f2.evaluate import clean
from f2.instance import ExportedProblem, FLAGS

ex, q = load_export(f"{data}/inst/{member}.npz")
z_pre = np.load(f"{data}/pre/{member}.npz")["z"].astype(float)
P = ExportedProblem(ex); prob = P.prob
clean(P); P.loading.delta[:] = 0.0
_, _, K0, _ = prob.evaluate(z_pre, "hencky", tangent=True)
K0 = K0.tocsr()
n_z = K0.shape[0]; ith, iw0 = int(ex["ith"]), int(ex["iw0"])
print("n_z", n_z, "theta index", ith, "w0 index", iw0, "k_th", float(ex["k_th"]), "K0[theta,theta]", K0[ith, ith], "K0[w0,w0]", K0[iw0, iw0])
flags = np.asarray(ex["node_flags"]).astype(bool)
cidx = prob.cidx; node = cidx // 3
plane = flags[node, FLAGS.index("splice_plane")] & ~flags[node, FLAGS.index("bearing_patch")] & ~flags[node, FLAGS.index("root_tube")]
for tag, extra, free_plane in (("theta and w0 free, plane free", [], True), ("theta held, plane free", [ith], True), ("theta and w0 held, plane free", [ith, iw0], True),
                               ("theta and w0 free, every contact held", [], False), ("theta held, every contact held", [ith], False)):
    held = prob.fixed.copy()
    held[cidx[~plane] if free_plane else cidx] = True
    held[extra] = True
    idx = np.nonzero(~held)[0]
    A = K0[idx][:, idx].tocsc()
    w, V = spla.eigsh(A, k=8, sigma=0.0, which="LM")
    o = np.argsort(w); w, V = w[o], V[:, o]
    v = np.zeros(n_z); v[idx] = V[:, 0]
    share = {"theta": v[ith] ** 2, "w0": v[iw0] ** 2, "plane uz": float((v[cidx[plane]] ** 2).sum())}
    wmax = spla.eigsh(A, k=1, which="LA", return_eigenvectors=False)[0]
    print(f"{tag}: softest eigenvalues {np.array2string(w[:6], precision=4)}; largest {wmax:.3g}; ratio {wmax / w[0]:.3g}; "
          f"softest mode's squared shares: " + ", ".join(f"{k} {s:.3f}" for k, s in share.items()))
