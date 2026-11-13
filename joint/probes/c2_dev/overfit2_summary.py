"""Second round of single-member fitting tests (dev/overfit2_dev.py): energy gap, end-displacement error, bolt-force
error and the judged quantity of G-C2.1 (distance from the member's reference curve, here through the origin and the
member's 7 exact points only) for the raw and the condensed reading, by step; the amplitude solve's convergence.
Arguments: record files. Exploratory."""
import json, sys
import numpy as np
from scipy.interpolate import PchipInterpolator
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
LAB = str(paths.work() / "labels") + "/"; KS = 2.0e4
LV = np.array([0.5, 1, 2, 3, 4, 6, 8.0])
for path in sys.argv[1:]:
    R = [json.loads(l) for l in open(path) if l.strip()]
    head = R[0]; recs = [r for r in R if "raw" in r]; end = [r for r in R if r.get("end")]
    iid = head["member"]; lab = np.load(LAB + iid + ".npz")
    e, F = np.asarray(lab["e"], float), np.asarray(lab["F"], float)
    c = PchipInterpolator(np.concatenate([[0.0], e]), np.concatenate([[0.0], F]), extrapolate=True)
    J = lambda r, k: 4 * KS * (LV - e * (1 + np.array(r[k]["e_err"]))) / c(e * (1 + np.array(r[k]["e_err"]))) - 1
    print(f"\n=== {path.split('/')[-1]}: {head['variant']}, {head['steps']} steps, lr {head['lr']}, amplitude within [{head['amin']}, {head['amax']}], "
          f"solve evaluations {head['train_evals']} (step) / {head['read_evals']} (reading); {end[0]['status'] + ', ' + str(end[0]['seconds']) + ' s' if end else 'not ended'}")
    keys = ["raw"] + (["cond"] if "cond" in recs[0] else [])
    sel = [r for r in recs if r["step"] % 100 == 0 or r is recs[-1]]
    for k in keys:
        print(f"  [{k}] step | judged quantity % at 3, 4, 6, 8 mm | energy gap % at 4, 6, 8 | end-displacement error % at 4, 6, 8 | bolt-force error % at 4, 6, 8" + (" | a at 4, 6, 8" if k == "cond" else ""))
        for r in sel:
            print(f"     {r['step']:5d} | " + " ".join(f"{100*v:6.1f}" for v in J(r, k)[3:]) + " | " + " ".join(f"{100*v:5.2f}" for v in r[k]["gap"][4:]) + " | "
                  + " ".join(f"{100*v:+6.1f}" for v in r[k]["e_err"][4:]) + " | " + " ".join(f"{100*v:+6.1f}" for v in r[k]["bolt_err"][4:])
                  + (" | " + " ".join(f"{v:.3f}" for v in r["a"][4:]) if k == "cond" else ""))
        last = np.array([J(r, k) for r in recs[-5:]])
        print(f"     last five readings, judged quantity at 4, 6, 8 mm: median {np.round(100*np.median(last, axis=0)[4:], 1)}, min {np.round(100*last.min(axis=0)[4:], 1)}, max {np.round(100*last.max(axis=0)[4:], 1)}; small levels (0.5, 1, 2 mm) median {np.round(100*np.median(last, axis=0)[:3], 1)}")
    if "a_info" in recs[0]:
        nc = sum(sum(1 for v in r["a_info"]["converged"] if not v) for r in recs); ab = sum(sum(r["a_info"]["at_bound"]) for r in recs)
        print(f"  readings: amplitude solves not converged {nc}, at a bound {ab}, of {7 * len(recs)}; largest relative slope {max(max(r['a_info']['rel_slope']) for r in recs):.1e}; a over all readings from {min(min(r['a']) for r in recs):.3f} to {max(max(r['a']) for r in recs):.3f}")
    ts = [r["train_solve"] for r in recs if "train_solve" in r]
    if ts:
        n = sum(t["n"] for t in ts)
        print(f"  training steps: amplitude solves {n}, not converged {sum(t['not_converged'] for t in ts)}, at a bound {sum(t['at_bound'] for t in ts)}; a from {min(t['a_min'] for t in ts):.3f} to {max(t['a_max'] for t in ts):.3f}; largest relative slope {max(t['slope_max'] for t in ts):.1e}")
    secs = [(r["step"], r["sec"]) for r in recs if "sec" in r]
    if len(secs) > 2: print(f"  seconds per {secs[1][0] - secs[0][0]} steps between readings (reading included): median {np.median(np.diff([s for _, s in secs])):.0f}")
