"""Reference curve F*(e) of each held-out member, from exact points only:
 the 7 labels (e_ref, F_ref), the origin, and every run's (e_pred, F*(e_pred)) = (e_pred, F_spring / (1 + curve_err)),
 which the gate's evaluation computed with an exact solve at prescribed e. Monotone (PCHIP) interpolation in e."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
import numpy as np
from scipy.interpolate import PchipInterpolator
from common import *

_v = None
def points(iid):
    global _v
    if _v is None: _v = verdict()
    lab = label(iid)
    pts = [(0.0, 0.0, "origin")] + [(float(lab["e"][l]), float(lab["F"][l]), "label") for l in range(7)]
    for arm in ("label_free", "supervised_64"):
        for seed in ("0", "1", "2"):
            for l, r in enumerate(_v["arms"][arm][seed]["eval_rows"][iid]):
                ce = r["curve_err"]
                if ce is None or not np.isfinite(ce) or not np.isfinite(r["e_err"]): continue
                D = float(lab["D"][l]); ep = float(lab["e"][l]) * (1 + r["e_err"])
                if ep <= 0: continue
                Fs = 4 * KS * (D - ep); Fstar = Fs / (1 + ce)
                if not np.isfinite(Fstar) or Fstar <= 0: continue
                pts.append((ep, Fstar, f"{arm}_s{seed}_l{l}"))
    pts.sort()
    return pts

def curve(pts):
    e = np.array([p[0] for p in pts]); F = np.array([p[1] for p in pts])
    keep = np.concatenate([[True], np.diff(e) > 1e-9 * max(e.max(), 1.0)])
    return PchipInterpolator(e[keep], F[keep], extrapolate=True)

if __name__ == "__main__":
    ids, par = eval_ids()
    loo = []; nmono = 0; npts = []
    for iid in ids:
        pts = points(iid); npts.append(len(pts))
        e = np.array([p[0] for p in pts]); F = np.array([p[1] for p in pts])
        nmono += int(np.sum(np.diff(F) < -1e-6 * F.max()))
        for k in range(1, len(pts) - 1):
            if pts[k][2] == "origin": continue
            c = curve(pts[:k] + pts[k + 1:])
            loo.append((pts[k][0], pts[k][2], float(c(pts[k][0])) / pts[k][1] - 1))
    err = np.abs([x[2] for x in loo]); es = np.array([x[0] for x in loo])
    print("members", len(ids), "points per member min/median/max", min(npts), int(np.median(npts)), max(npts), "non-monotone neighbours", nmono)
    print("leave-one-out |rel err|: median %.4f%%  p90 %.4f%%  p99 %.3f%%  max %.3f%%" % tuple(100 * np.quantile(err, q) for q in (.5, .9, .99, 1.0)))
    for lo, hi in ((0, .05), (.05, .2), (.2, 1), (1, 3), (3, 9)):
        s = (es >= lo) & (es < hi)
        if s.any(): print(f"  e in [{lo},{hi}) mm: n {int(s.sum()):5d}  median {100*np.median(err[s]):.4f}%  p90 {100*np.quantile(err[s],.9):.4f}%  max {100*err[s].max():.3f}%")
    lab_only = [x for x in loo if x[1] == "label"]
    print("labels only: median %.4f%% p90 %.4f%% max %.3f%%" % tuple(100 * np.quantile(np.abs([x[2] for x in lab_only]), q) for q in (.5, .9, 1.0)))
