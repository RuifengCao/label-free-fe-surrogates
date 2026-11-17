"""Audit of gate G-C2.2, item 1a: the criteria C1 and C2 from the per-pair values of verdict.json.

What it checks, with its own code (no import from the gate's code or from the author's audit scripts):
  - for every reading (condensed, raw), set (eval, former, tested) and seed, the median, the 90th percentile and
    the largest value of |F/F*(e) - 1| over the pairs, computed from the per-pair rows with a quantile written here
    (linear interpolation between order statistics, the convention of the pre-specified code), and compared with
    the summaries stored in verdict.json;
  - C1 and C2 as the median over the three seeds of the per-seed median and 90th percentile of the judged reading
    (condensed) on the judged set (eval), the thresholds 0.05 and 0.10, and the verdict;
  - the same two values for the raw reading (reported, not judged);
  - that abs_curve_err equals |curve_err| in every row, that no row is infinite or not a number, and the counts of
    pairs, members and levels.

Usage:  python -I a1_criteria.py RECORDS [--out OUT.json]
        RECORDS is the folder gate_records of the return package (it holds verdict.json).
"""
import argparse
import json
import math
import os


def quantile(values, q):
    """Linear interpolation between the order statistics at position (n - 1) q."""
    s = sorted(values)
    h = (len(s) - 1) * q
    lo = int(math.floor(h))
    hi = min(lo + 1, len(s) - 1)
    t = h - lo
    if t == 0:
        return s[lo]
    return s[lo] + t * (s[hi] - s[lo])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    ap.add_argument("--out")
    a = ap.parse_args()
    v = json.load(open(os.path.join(a.records, "verdict.json")))
    seeds = ["5", "6", "7"]
    sets = {"eval": 64, "former": 64, "tested": 4}
    levels = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
    out = {"per": {}, "problems": []}
    worst_rel = 0.0
    for reading in ("condensed", "raw"):
        for s, n_members in sets.items():
            for seed in seeds:
                entry = v["readings"][reading][seed]
                rows = entry[f"{s}_rows"]
                if len(rows) != n_members:
                    out["problems"].append(f"{reading} {s} {seed}: {len(rows)} members")
                vals = []
                for iid, rr in rows.items():
                    if [r["D"] for r in rr] != levels:
                        out["problems"].append(f"{reading} {s} {seed} {iid}: levels {[r['D'] for r in rr]}")
                    for r in rr:
                        c, ac = r["curve_err"], r["abs_curve_err"]
                        if not (isinstance(c, float) and math.isfinite(c)):
                            out["problems"].append(f"{reading} {s} {seed} {iid} D={r['D']}: curve_err {c}")
                        if ac != abs(c):
                            out["problems"].append(f"{reading} {s} {seed} {iid} D={r['D']}: abs differs")
                        if r["curve_note"] or r["evaluate_failed"]:
                            out["problems"].append(f"{reading} {s} {seed} {iid} D={r['D']}: note or failure")
                        vals.append(abs(c))
                if entry["errors"]:
                    out["problems"].append(f"{reading} {seed}: errors {list(entry['errors'])}")
                mine = {"n": len(vals), "median": quantile(vals, 0.5), "p90": quantile(vals, 0.9), "max": max(vals),
                        "above_5": sum(x > 0.05 for x in vals), "above_10": sum(x > 0.10 for x in vals)}
                theirs = entry[s]["abs_curve_err"]
                for k in ("n", "median", "p90", "max"):
                    d = abs(mine[k] - theirs[k]) / max(abs(theirs[k]), 1e-300)
                    worst_rel = max(worst_rel, d)
                    if d > 1e-12:
                        out["problems"].append(f"{reading} {s} {seed} {k}: mine {mine[k]} stored {theirs[k]}")
                out["per"][f"{reading}|{s}|{seed}"] = mine
    out["largest_relative_difference_from_stored_summaries"] = worst_rel
    crit = {}
    for reading in ("condensed", "raw"):
        med = [out["per"][f"{reading}|eval|{seed}"]["median"] for seed in seeds]
        p90 = [out["per"][f"{reading}|eval|{seed}"]["p90"] for seed in seeds]
        c1, c2 = quantile(med, 0.5), quantile(p90, 0.5)
        crit[reading] = {"per_seed_median": med, "per_seed_p90": p90, "C1_value": c1, "C2_value": c2,
                         "C1": c1 <= 0.05, "C2": c2 <= 0.10}
    out["criteria"] = crit
    mine_verdict = "PASS" if (crit["condensed"]["C1"] and crit["condensed"]["C2"]) else "FAIL"
    out["verdict_mine"] = mine_verdict
    out["verdict_returned"] = v["verdict"]
    out["returned"] = {"C1_value": v["C1_value"], "C2_value": v["C2_value"], "C1": v["C1"], "C2": v["C2"],
                       "per_seed": v["per_seed"], "raw": v["reported_readings"]["raw"],
                       "judged": v["judged"], "status": v["status"], "missing": v["missing"],
                       "non_finite": v["non_finite"], "config_sha256": v["config_sha256"]}
    out["differences"] = {
        "C1": crit["condensed"]["C1_value"] - v["C1_value"], "C2": crit["condensed"]["C2_value"] - v["C2_value"],
        "raw_C1": crit["raw"]["C1_value"] - v["reported_readings"]["raw"]["C1_value"],
        "raw_C2": crit["raw"]["C2_value"] - v["reported_readings"]["raw"]["C2_value"],
        "per_seed_median": [m - r for m, r in zip(crit["condensed"]["per_seed_median"], v["per_seed"]["abs_curve_err_median"])],
        "per_seed_p90": [m - r for m, r in zip(crit["condensed"]["per_seed_p90"], v["per_seed"]["abs_curve_err_p90"])]}
    text = json.dumps(out, indent=1)
    if a.out:
        with open(a.out, "w") as fh:
            fh.write(text)
    print(json.dumps({k: out[k] for k in ("criteria", "verdict_mine", "verdict_returned", "differences",
                                          "largest_relative_difference_from_stored_summaries", "problems")}, indent=1))
    for k, m in out["per"].items():
        print(k, m)


if __name__ == "__main__":
    main()
