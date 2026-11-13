"""Multi-amplitude reading against the one-amplitude condensed reading, pair by pair, for the members that were run.

    python subspace_summary.py SUBSPACE.json STORED_EVAL.json   (the stored file holds the raw and condensed rows of the same model)
"""
import json
import sys

import numpy as np

sub = json.load(open(sys.argv[1]))
st = json.load(open(sys.argv[2]))
cond = {(r["id"], r["D"]): r for r in st["rows"]}
names = {0: "mode 1", 1: "mode 2", 3: "web"}
rows = []
for iid, m in sub["members"].items():
    for r in m["rows"]:
        c = cond[(iid, r["D"])]
        assert abs(c["raw"]["J"] - r["raw"]["J"]) < 2e-3, (iid, r["D"], c["raw"]["J"], r["raw"]["J"])
        rows.append({"id": iid, "D": r["D"], "mech": m["mechanism"], "raw": r["raw"]["J"], "cond": c["cond"]["J"], "sub": r["sub"]["J"],
                     "gap_cond": c["cond"]["gap"], "gap_sub": r["sub"]["gap"]})
print(f"members {len(sub['members'])}, pairs {len(rows)}, basis {sub['basis']}")
for key in ("raw", "cond", "sub"):
    J = np.abs([r[key] for r in rows])
    print(f"  {key:5s} median {100 * np.median(J):5.2f}  p90 {100 * np.percentile(J, 90):5.2f}  over 10%: {int((J > 0.1).sum())}")
oc = [r for r in rows if abs(r["cond"]) > 0.1]
print(f"pairs over 10% under the condensed reading: {len(oc)}; of these still over under the subspace reading: {sum(abs(r['sub']) > 0.1 for r in oc)}")
print(f"pairs under 10% (condensed) that go over (subspace): {sum(abs(r['sub']) > 0.1 for r in rows if abs(r['cond']) <= 0.1)}")
print(f"energy gap, median over the pairs over 10% (condensed): condensed {100 * np.median([r['gap_cond'] for r in oc]):.2f}%, subspace {100 * np.median([r['gap_sub'] for r in oc]):.2f}%")
ratio = [r["sub"] / r["cond"] for r in oc]
print(f"J(subspace) / J(condensed) on those pairs: median {np.median(ratio):.2f}, range {min(ratio):.2f} to {max(ratio):.2f}")
print("by level (condensed over 10% -> subspace over 10%):", {D: (sum(abs(r["cond"]) > 0.1 for r in rows if r["D"] == D), sum(abs(r["sub"]) > 0.1 for r in rows if r["D"] == D)) for D in sorted({r["D"] for r in rows})})
print("by mechanism:", {names.get(k, k): (sum(abs(r["cond"]) > 0.1 for r in rows if r["mech"] == k), sum(abs(r["sub"]) > 0.1 for r in rows if r["mech"] == k)) for k in sorted({r["mech"] for r in rows})})
print("\nmember      mech    D: raw / condensed / subspace (%), levels 3, 4, 6, 8")
for iid, m in sub["members"].items():
    cells = []
    for D in (3.0, 4.0, 6.0, 8.0):
        r = next(x for x in rows if x["id"] == iid and x["D"] == D)
        cells.append(f"{100 * r['raw']:6.1f}/{100 * r['cond']:5.1f}/{100 * r['sub']:5.1f}")
    print(f"{iid}  {names.get(m['mechanism'], m['mechanism']):6s}  " + "   ".join(cells))
