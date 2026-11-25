"""Gate G-F2.1: the verdict's statistics computed again from the rows of the sample's evaluation file, with the
standard library only. This file imports nothing of the gate's code (f21/, f2/, c2/) and nothing but json, math and
sys, so that an error in f21/gate.py's statistics would not be repeated here.

    python -I probes/f21_recompute/recompute.py EVALUATION.json VERDICT.json [MANIFEST.json] [--members N]

EVALUATION.json is runs_gate/evaluation_seeds_5_6_7.json, VERDICT.json is records/verdict.json, and MANIFEST.json,
if given, is data_gate/manifest.json (for the members with thin plates). The lines, the reading, the quantity and the
seeds are written here as the pre-specification gives them (docs/PRESPEC_G-F2.1.md); they are not read from the
verdict. Prints what it computed and each comparison, and ends with the exit code 0 only if every value agrees with
the verdict file within 1e-12 (relative, for values above one) and the verdict is the same. --members is for trying this file on the host check's
reduced output, which holds two members; without it the evaluation must hold the 64 of the gate.

What it does not check: the rows themselves. They come from the reference code's solves on the predicted fields
(f2/evaluate.py), which this file takes as given.
"""
import json
import math
import sys

SEEDS = (5, 6, 7)
READING, QUANTITY, EXACT = "condensed", "abs_curveD_err", "curveD_exact_err"
LINES = {"median": 0.05, "p90": 0.10}
MEMBERS, LEVELS = 64, 7
THIN_AT_MOST = 12.5
TOL = 1e-12


def quantile(values, q):
    """Linear interpolation between the order statistics (numpy's default); infinite if an infinite order statistic
    has a positive weight."""
    s = sorted(values)
    h = (len(s) - 1) * q
    lo = int(math.floor(h))
    hi = min(lo + 1, len(s) - 1)
    t = h - lo
    if (math.isinf(s[lo]) and 1.0 - t > 0) or (math.isinf(s[hi]) and t > 0):
        return math.inf
    return s[lo] + t * (s[hi] - s[lo]) if t > 0 else s[lo]


def values(ev, seed, key, members=None, level=None, reading=READING):
    """Absolute values over the pairs (member, level); infinite where a member has no rows, a value is missing or
    it is not finite."""
    rows = ev["rows"][f"{seed}|{reading}"]["members"]
    out = []
    for iid in ev["members"]:
        if members is not None and iid not in members:
            continue
        r = rows.get(iid)
        if r is not None and len(r) != LEVELS:
            raise SystemExit(f"{iid}: {len(r)} levels")
        for l in range(LEVELS):
            if level is not None and l != level:
                continue
            x = None if r is None else r[l].get(key)
            x = math.inf if x is None else abs(float(x))
            out.append(x if math.isfinite(x) else math.inf)
    return out


def same(a, b):
    if a is None or b is None:
        return a is b
    if math.isinf(a) or math.isinf(b):
        return a == b
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def main(argv):
    global MEMBERS
    argv = list(argv)
    if "--members" in argv:
        i = argv.index("--members")
        MEMBERS = int(argv[i + 1])
        del argv[i:i + 2]
    ev = json.load(open(argv[1], encoding="utf-8"))
    v = json.load(open(argv[2], encoding="utf-8"))
    man = json.load(open(argv[3], encoding="utf-8")) if len(argv) > 3 else None
    checks = []

    def check(what, mine, theirs):
        ok = same(mine, theirs)
        checks.append(ok)
        print(f"  {'agrees ' if ok else 'DIFFERS'} {what}: {mine!r} here, {theirs!r} in the verdict file")

    assert len(ev["members"]) == len(set(ev["members"])) == MEMBERS, f"the evaluation does not hold {MEMBERS} members"
    finished = [s for s in SEEDS if ev["status"].get(str(s)) == "finished"]
    per = {}
    for s in finished:
        x = values(ev, s, QUANTITY)
        assert len(x) == MEMBERS * LEVELS
        per[s] = {"median": quantile(x, 0.5), "p90": quantile(x, 0.9), "max": max(x), "not_finite": sum(math.isinf(y) for y in x)}
        print(f"seed {s}: median {100 * per[s]['median']:.4f}%  p90 {100 * per[s]['p90']:.4f}%  largest {100 * per[s]['max']:.3f}%  "
              f"pairs not finite {per[s]['not_finite']}")
        for k in ("median", "p90", "max", "not_finite"):
            check(f"seed {s} {k}", per[s][k], v["per_seed"].get(str(s), {}).get(k))
        for l in range(LEVELS):
            check(f"seed {s} level {l + 1} median", quantile(values(ev, s, QUANTITY, level=l), 0.5),
                  v["reported"][str(s)]["by_level"][l]["median"])
        if EXACT and READING in ev.get("exact_readings", []):
            xe = values(ev, s, EXACT)
            for k, q in (("median", 0.5), ("p90", 0.9)):
                check(f"seed {s} exact value {k}", quantile(xe, q), v["exact"]["per_seed"][str(s)][k])
        if man is not None:
            thin = {r["id"] for r in man["instances"] if r["params"]["tp"] <= THIN_AT_MOST}
            xt = values(ev, s, QUANTITY, members=thin)
            check(f"seed {s} thin plates ({len(thin)} members) median", quantile(xt, 0.5) if xt else None,
                  v["reported"][str(s)]["thin_band"].get("median"))
            check(f"seed {s} thin plates p90", quantile(xt, 0.9) if xt else None, v["reported"][str(s)]["thin_band"].get("p90"))
    failed = [int(s) for s in v.get("failed_seeds", [])]
    if failed:
        mine = "FAIL"
    elif len(per) != len(SEEDS):
        mine = "INCOMPLETE"
    else:
        across = {k: quantile([per[s][k] for s in SEEDS], 0.5) for k in LINES}
        for k in LINES:
            print(f"across seeds, {k}: {100 * across[k]:.4f}% against the line {100 * LINES[k]:g}%")
            check(f"across seeds {k}", across[k], v.get("across_seeds", {}).get(k))
        mine = "PASS" if all(across[k] <= LINES[k] for k in LINES) else "FAIL"
    ok = all(checks) and mine == v["verdict"]
    print(f"verdict here: {mine}; in the verdict file: {v['verdict']}" + (f" (failed seeds, taken from the file: {failed})" if failed else ""))
    print("RECOMPUTATION", "AGREES" if ok else "DOES NOT AGREE", f"({sum(checks)} of {len(checks)} values)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
