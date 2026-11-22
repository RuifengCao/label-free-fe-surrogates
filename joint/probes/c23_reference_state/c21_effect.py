"""Probe, 22 Nov 2026: what the figures of G-C2.1's verdict document that contain its one failed reference solve
(supervised_64, seed 1, eval_0046, 0.5 mm) would be with the value that the solve gives from a zero element state
(c21_pair.py). Exploratory; G-C2.1's verdict has no criterion on the supervised arm.
Run from joint/:  python -I -B probes/c23_reference_state/c21_effect.py C21RETURN
C21RETURN is records/c2/return. The quantile is that of audit/c2_write_verdict.py (the rule of c2/evaluate.py)."""
import json
import pathlib
import sys

import numpy as np

LEVELS = (0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0)
FY_SPLIT = 300.0
ARM, SEED, MEMBER, LEVEL = "supervised_64", "1", "eval_0046", 0
VALUE = -0.004491609982833267            # c21_pair.txt: the pair alone, and with the element state set to zero


def quantile(v, q: float) -> float:
    v = np.asarray(v, dtype=float).ravel()
    s = np.sort(v)
    h = (s.size - 1) * q
    lo = int(np.floor(h))
    nxt, t = min(lo + 1, s.size - 1), h - lo
    for x, weight in ((s[lo], 1.0 - t), (s[nxt], t)):
        if np.isinf(x) and weight > 0:
            return float(x)
    big = np.finfo(float).max / 4
    return float(np.quantile(np.where(np.isinf(v), np.sign(v) * big, v), q))


def pct(x, d=4):
    return "infinite" if np.isinf(x) else f"{100 * x:.{d}f}%"


rec = pathlib.Path(sys.argv[1])
v = json.loads((rec / "verdict.json").read_text())
man = json.loads((rec / "manifest.json").read_text())
params = {r["id"]: r["params"] for r in man["instances"]}
ids = sorted(r["id"] for r in man["instances"] if r["split"] == "eval")
low = np.array([params[i]["fy"] for i in ids]) < FY_SPLIT
rows = v["arms"][ARM][SEED]["eval_rows"]
S = np.array([[r["curve_err"] for r in rows[i]] for i in ids], dtype=float)        # signed, members by levels
k = ids.index(MEMBER)
assert np.isinf(S[k, LEVEL]) and rows[MEMBER][LEVEL]["curve_note"].endswith("bubble condensation did not converge")
assert int(np.isinf(S).sum()) == 1
box = v["arms"][ARM][SEED]["eval"]["abs_curve_err"]
lv = np.tile(np.arange(len(LEVELS)), (len(ids), 1))
lowg = np.repeat(low[:, None], len(LEVELS), axis=1)
for name, G in (("returned", S), ("with the converged value", np.where(np.isinf(S), VALUE, S))):
    A = np.abs(G)
    p90 = quantile(A, 0.9)
    t = A > p90
    print(name)
    print(f"  the 448 pairs: median {pct(quantile(A, 0.5))}, 90th percentile {pct(p90)}, median signed "
          f"{pct(quantile(G, 0.5))}, above 10%: {int((A > 0.10).sum())}, infinite: {int(np.isinf(A).sum())}")
    a0, g0 = A[:, LEVEL], G[:, LEVEL]
    print(f"  the 64 pairs at 0.5 mm: median {pct(quantile(a0, 0.5))}, 90th percentile {pct(quantile(a0, 0.9))}, median "
          f"signed {pct(quantile(g0, 0.5))}, above 10%: {int((a0 > 0.10).sum())}")
    print(f"  the tail: pairs above the 90th percentile {int(t.sum())}, at 6 and 8 mm {int((t & (lv >= 5)).sum())}, at 0.5 "
          f"and 1 mm {int((t & (lv <= 1)).sum())}, in members below {FY_SPLIT:g} MPa {int((t & lowg).sum())}")
    if name == "returned":
        assert quantile(A, 0.5) == box["median"] and p90 == box["p90"], "not the returned statistics"
print(f"the member {MEMBER}: yield stress {params[MEMBER]['fy']:.1f} MPa; the pair is at {LEVELS[LEVEL]:g} mm")
