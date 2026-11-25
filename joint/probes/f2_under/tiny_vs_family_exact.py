"""The small mesh's exact solutions against the family mesh's exact solutions, 31 development members x 7 levels
(no network involved): what the judged quantity would be if a field kept the small mesh's response exactly.

    python3 -I tiny_vs_family_exact.py TINY_SUMMARY FAMILY_SUMMARY TRIAL_EVALUATION OUT.json

The reference curve of a member: monotone cubic (PCHIP) through the origin and the family mesh's seven exact points
(joint rotation, moment). The same proxy is applied to the trial's raw predictions (rebuilt from the recorded signed
errors) and compared with the recorded values of the judged quantity, to show how far the proxy is from the record."""
import json
import sys

import numpy as np
from scipy.interpolate import PchipInterpolator

t, f, ev = (json.load(open(p)) for p in sys.argv[1:4])
ids = sorted(f)
assert sorted(t) == ids and len(ids) == 31
Th_same = max(abs(np.array(t[i]["Theta"]) / np.array(f[i]["Theta"]) - 1).max() for i in ids)
R, Me, C, Pe = [], [], [], []
for i in ids:
    a, b = t[i], f[i]
    curve = PchipInterpolator(np.concatenate([[0.0], b["ThetaD"]]), np.concatenate([[0.0], b["M"]]), extrapolate=True)
    R.append(np.array(a["ThetaD"]) / np.array(b["ThetaD"]))
    Me.append(np.array(a["M"]) / np.array(b["M"]) - 1)
    C.append(np.array(a["M"]) / curve(np.array(a["ThetaD"])) - 1)
    Pe.append(np.array(a["Pi"]) / np.array(b["Pi"]) - 1)
R, Me, C, Pe = map(np.array, (R, Me, C, Pe))
st = lambda x: [round(float(v), 3) for v in (np.median(x), np.percentile(x, 90), x.max())]      # noqa: E731
out = {"members": 31, "levels": 7, "largest relative difference of the device rotations": float(Th_same),
       "joint rotation, small over family, median by level": np.round(np.median(R, 0), 3).tolist(),
       "joint rotation, small over family: median, p10, least": [round(float(v), 3) for v in (np.median(R), np.percentile(R, 10), R.min())],
       "joint rotation |error| %: median, p90, largest": st(100 * abs(R - 1)),
       "moment at the same device rotation, signed %, median by level": np.round(100 * np.median(Me, 0), 2).tolist(),
       "moment at the same device rotation |error| %: median, p90, largest": st(100 * abs(Me)),
       "moment at the same joint rotation (proxy) |error| %: median, p90, largest": st(100 * abs(C)),
       "moment at the same joint rotation (proxy) |error| %, median by level": np.round(100 * np.median(abs(C), 0), 2).tolist(),
       "energy, small over family minus one, signed %, median by level": np.round(100 * np.median(Pe, 0), 2).tolist(),
       "worst members (proxy, largest over levels)": sorted(((ids[k], round(float(100 * abs(C[k]).max()), 1)) for k in range(31)), key=lambda x: -x[1])[:6]}
# the proxy against the record, on the trial's raw predictions
rows = ev["rows"]["0|raw"]["members"]
P, Q = [], []
for i in ids:
    b = f[i]
    curve = PchipInterpolator(np.concatenate([[0.0], b["ThetaD"]]), np.concatenate([[0.0], b["M"]]), extrapolate=True)
    M = np.array(b["M"]) * (1 + np.array([r["M_err"] for r in rows[i]]))
    TD = np.array(b["ThetaD"]) * (1 + np.array([r["ThetaD_err"] for r in rows[i]]))
    P.append(abs(M / curve(TD) - 1)); Q.append([r["abs_curveD_err"] for r in rows[i]])
P, Q = np.array(P), np.array(Q)
out["trial, raw: proxy %: median, p90, largest"] = st(100 * P)
out["trial, raw: record %: median, p90, largest"] = st(100 * Q)
out["trial, raw: |proxy - record| in points: median, p90, largest"] = st(100 * abs(P - Q))
# how much of the trial's error in the judged quantity sits where the small mesh's own error sits
out["rank correlation, small mesh's exact |error| (proxy) with the trial's record, 217 pairs"] = round(float(np.corrcoef(np.argsort(np.argsort(abs(C).ravel())), np.argsort(np.argsort(Q.ravel())))[0, 1]), 3)
out["trial record over small mesh's exact |error| (proxy), median of the ratio"] = round(float(np.median(Q.ravel() / np.maximum(abs(C).ravel(), 1e-12))), 3)
out["pairs where the trial's record is below the small mesh's exact |error| (proxy)"] = int((Q < abs(C)).sum())
json.dump(out, open(sys.argv[4], "w"), indent=1)
for k, v in out.items():
    print(f"{k}: {v}")
