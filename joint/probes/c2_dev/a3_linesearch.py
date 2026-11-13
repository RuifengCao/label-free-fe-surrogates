"""Exploratory (not pre-registered; changes no verdict): one-dimensional energy line searches on the returned
predictions of G-C2.1's label-free seeds, with the stamped numpy reference code. For a predicted field z at loading
displacement D, minimise Pi(z + t d; D) over the scalar t along
  amp: d = z                      (amplitude of the whole field)
  tan: d = finite-difference path tangent of the network's own fields over D (neighbouring levels)
and read the point (e, F = 4 k_s (D - e)) again. Distance from the reference curve by the interpolated exact curve."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
import json, time, os
import numpy as np
from common import *
from refcurve import points, curve

def evalg(P, z, D):
    P.loading.delta[:] = -D
    E, g, _, _ = P.prob.evaluate(z, "hencky", tangent=False)
    return float(E), g

def search(P, z, d, D, h, clamp=None, max_eval=6, rtol=1e-3):
    """Secant iteration on phi'(t) = grad Pi(z + t d) . d (phi convex). Returns t, Pi, z_t, evaluations, |phi'|/|phi'0|."""
    def at(t):
        zt = z + t * d; de = d
        if clamp is not None:
            neg = zt[clamp] < 0
            if neg.any():
                zt[clamp[neg]] = 0.0; de = d.copy(); de[clamp[neg]] = 0.0
        E, g = evalg(P, zt, D)
        return E, float(g @ de), zt
    E0, s0, z0 = at(0.0)
    hist = [(0.0, E0, s0, z0)]
    if s0 == 0.0: return 0.0, E0, z0, 1, 0.0
    t1 = -np.sign(s0) * h
    E1, s1, z1 = at(t1); hist.append((t1, E1, s1, z1))
    n = 2
    while n < max_eval:
        (ta, Ea, sa, _), (tb, Eb, sb, _) = hist[-2], hist[-1]
        if abs(sb) <= rtol * abs(s0) or sb == sa: break
        # bracket-aware secant: prefer the two points whose slopes have opposite signs, if any
        neg = [p for p in hist if p[2] < 0]; pos = [p for p in hist if p[2] > 0]
        if neg and pos:
            pa = max(neg, key=lambda p: p[0]) if s0 < 0 else min(neg, key=lambda p: p[0])
            pb = min(pos, key=lambda p: p[0]) if s0 < 0 else max(pos, key=lambda p: p[0])
            ta, sa, tb, sb = pa[0], pa[2], pb[0], pb[2]
        tn = tb - sb * (tb - ta) / (sb - sa)
        if not (neg and pos):
            tn = tb + np.clip(tn - tb, -8 * abs(tb - ta) - 1e-12, 8 * abs(tb - ta) + 1e-12)   # limited extrapolation
        En, sn, zn = at(tn); hist.append((tn, En, sn, zn)); n += 1
    best = min(hist, key=lambda p: p[1])
    return best[0], best[1], best[3], n, abs(best[2]) / abs(s0)

def run(seed, ids, out_path, levels=range(7), dirs=("amp", "tan")):
    v = verdict()
    pr = preds(f"label_free_s{seed}")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line); done.add((r["iid"], r["l"], r["dir"]))
    with open(out_path, "a") as fo:
        for iid in ids:
            if all((iid, l, dn) in done for l in levels for dn in dirs): continue
            P, ex, q = problem(iid)
            lab = label(iid); c = curve(points(iid))
            Z = pr[iid].astype(np.float64)
            cidx = np.asarray(P.prob.cidx, int)
            rows = v["arms"]["label_free"][str(seed)]["eval_rows"][iid]
            for l in levels:
                D = float(lab["D"][l]); z = Z[l]
                Pi_ref, e_ref, F_ref = float(lab["Pi"][l]), float(lab["e"][l]), float(lab["F"][l])
                for dn in dirs:
                    if (iid, l, dn) in done: continue
                    t0 = time.perf_counter()
                    if dn == "amp":
                        d, h, cl = z.copy(), 0.02, None
                    elif dn == "load":      # amplitude of the load-induced part: z0 = the network's own fields extrapolated to D = 0
                        z0 = 2.0 * Z[0] - Z[1]; z0[cidx] = np.maximum(z0[cidx], 0.0)
                        d, h, cl = z - z0, 0.02, cidx
                    else:
                        a, b = max(l - 1, 0), min(l + 1, 6)
                        d = (Z[b] - Z[a]) / (float(lab["D"][b]) - float(lab["D"][a])); h, cl = 0.02 * D, cidx
                    t, Pi_new, zt, n, red = search(P, z, d, D, h, clamp=cl)
                    rd = P.evaluate(zt, D)
                    e_new = rd["e"]; F_new = rd["F"]
                    rec = dict(seed=seed, iid=iid, l=l, D=D, dir=dn, t=float(t), n_eval=n, slope_red=float(red),
                               gap0=rows[l]["gap"], gap=Pi_new / Pi_ref - 1, e_err0=rows[l]["e_err"], e_err=e_new / e_ref - 1,
                               F_err0=rows[l]["F_err"], F_err=F_new / F_ref - 1, Fsig_err0=rows[l]["F_sigma_err"], Fsig_err=rd["F_sigma"] / F_ref - 1,
                               curve_err0=rows[l]["curve_err"], curve_err=F_new / float(c(e_new)) - 1,
                               curve_err0_interp=4 * KS * (D - e_ref * (1 + rows[l]["e_err"])) / float(c(e_ref * (1 + rows[l]["e_err"]))) - 1,
                               bolt_err0=rows[l]["bolt_err"], bolt_err=rd["bolt_N"] / float(lab["bolt_N"][l]) - 1,
                               secs=time.perf_counter() - t0)
                    fo.write(json.dumps(rec) + "\n"); fo.flush()

if __name__ == "__main__":
    seed, part, nparts = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    ids, _ = eval_ids()
    sel = ids[part::nparts]
    if len(sys.argv) > 4: sel = sel[: int(sys.argv[4])]
    dirs = tuple(os.environ.get("DIRS", "tan,amp").split(","))
    run(seed, sel, paths.work() / "tail" / f"a3_s{seed}_p{part}.jsonl", dirs=dirs)
