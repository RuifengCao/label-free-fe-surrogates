"""Audit of gate G-C2.2, item 3: the numbers behind the prose of the verdict document and of the README's status
row, computed from the return package with the auditor's own code. The script prints the facts; the comparison with
the sentences of the document is made by reading (the report lists each).

Usage:  python -I a12_text_numbers.py RECORDS [--out OUT.json]
"""
import argparse
import json
import math
import os

SEEDS = ["5", "6", "7"]
LEVELS = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]


def quantile(values, q):
    s = sorted(values)
    h = (len(s) - 1) * q
    lo = int(math.floor(h)); hi = min(lo + 1, len(s) - 1); t = h - lo
    return s[lo] if t == 0 else s[lo] + t * (s[hi] - s[lo])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records"); ap.add_argument("--out")
    a = ap.parse_args()
    R = a.records
    v = json.load(open(os.path.join(R, "verdict.json")))
    man = {r["id"]: r for r in json.load(open(os.path.join(R, "manifest.json")))["instances"]}
    cond = {s: json.load(open(os.path.join(R, "run_files", f"label_free_s{s}", "condense.json")))["members"] for s in SEEDS}
    rows = lambda rd, st, s: v["readings"][rd][s][f"{st}_rows"]   # noqa: E731
    f = {}
    # the tail of the judged reading
    above = {s: [(i, l) for i, rr in rows("condensed", "eval", s).items() for l, r in enumerate(rr) if r["abs_curve_err"] > 0.10] for s in SEEDS}
    union = sorted(set().union(*above.values()))
    f["tail"] = {"pairs_above_10_by_seed": [len(above[s]) for s in SEEDS], "members_by_seed": [len({i for i, _ in above[s]}) for s in SEEDS],
                 "union_pairs": len(union), "union_members": sorted({i for i, _ in union}),
                 "pairs_above_10_in_all_three_seeds": sorted(set(above["5"]) & set(above["6"]) & set(above["7"])),
                 "pairs_above_10_in_exactly_one_seed": [p for p in union if sum(p in above[s] for s in SEEDS) == 1],
                 "union_pairs_at_6_or_8_mm": sum(l >= 5 for _, l in union),
                 "all_union_signed_positive": all(rows("condensed", "eval", s)[i][l]["curve_err"] > 0 for i, l in union for s in SEEDS),
                 "fy_of_union_members": {i: round(man[i]["params"]["fy"], 1) for i, _ in union},
                 "tf_of_union_members": {i: round(man[i]["params"]["t_f"], 2) for i, _ in union},
                 "share_of_eval_0001": sum(i == "eval_0001" for i, _ in union)}
    f["eval_0001"] = {s: {"condensed_signed_percent": [round(100 * r["curve_err"], 2) for r in rows("condensed", "eval", s)["eval_0001"]],
                          "raw_signed_percent": [round(100 * r["curve_err"], 2) for r in rows("raw", "eval", s)["eval_0001"]]} for s in SEEDS}
    f["eval_0001_condensed_increasing_from_3mm"] = all(all(x < y for x, y in zip(z[3:], z[4:])) for z in (f["eval_0001"][s]["condensed_signed_percent"] for s in SEEDS))
    f["eval_0001_condensed_increasing_over_all_levels"] = all(all(x < y for x, y in zip(z, z[1:])) for z in (f["eval_0001"][s]["condensed_signed_percent"] for s in SEEDS))
    # raw reading at 8 mm, fresh and former
    for st in ("eval", "former"):
        f[f"raw_{st}"] = {
            "members_with_a_pair_above_10": [sum(any(r["abs_curve_err"] > 0.10 for r in rr) for rr in rows("raw", st, s).values()) for s in SEEDS],
            "members_above_10_at_8mm": [sum(rr[6]["abs_curve_err"] > 0.10 for rr in rows("raw", st, s).values()) for s in SEEDS],
            "of_them_too_stiff_at_8mm": [sum(rr[6]["curve_err"] > 0.10 for rr in rows("raw", st, s).values()) for s in SEEDS],
            "members_above_10_only_below_8mm": [sum(any(r["abs_curve_err"] > 0.10 for r in rr[:6]) and not rr[6]["abs_curve_err"] > 0.10 for rr in rows("raw", st, s).values()) for s in SEEDS],
            "p90_percent": [round(100 * quantile([r["abs_curve_err"] for rr in rows("raw", st, s).values() for r in rr], 0.9), 3) for s in SEEDS]}
        f[f"condensed_{st}_8mm_above_10"] = [sum(rr[6]["abs_curve_err"] > 0.10 for rr in rows("condensed", st, s).values()) for s in SEEDS]
    # by level, both readings, the range of the medians up to 4 mm
    med = {rd: [[quantile([rr[l]["abs_curve_err"] for rr in rows(rd, "eval", s).values()], 0.5) for l in range(7)] for s in SEEDS] for rd in ("condensed", "raw")}
    f["medians_up_to_4mm_percent_min_max"] = {rd: [round(100 * min(min(m[:5]) for m in med[rd]), 3), round(100 * max(max(m[:5]) for m in med[rd]), 3)] for rd in med}
    # former_0017 at 8 mm
    f["former_0017_8mm"] = {s: {"condensed": round(100 * rows("condensed", "former", s)["former_0017"][6]["curve_err"], 2),
                                "raw": round(100 * rows("raw", "former", s)["former_0017"][6]["curve_err"], 2), "a": round(cond[s]["former_0017"]["a"][6], 4)} for s in SEEDS}
    # members read worse by the condensed reading than by the raw one at 8 mm, with a pair above 10%
    f["former_pairs_above_10_condensed_and_worse_than_raw"] = {s: sorted((i, LEVELS[l]) for i, rr in rows("condensed", "former", s).items() for l, r in enumerate(rr)
                                                                   if r["abs_curve_err"] > 0.10 and r["abs_curve_err"] > rows("raw", "former", s)[i][l]["abs_curve_err"]) for s in SEEDS}
    f["eval_pairs_above_10_condensed_and_worse_than_raw"] = {s: sorted((i, LEVELS[l]) for i, rr in rows("condensed", "eval", s).items() for l, r in enumerate(rr)
                                                                 if r["abs_curve_err"] > 0.10 and r["abs_curve_err"] > rows("raw", "eval", s)[i][l]["abs_curve_err"]) for s in SEEDS}
    # how often the condensed reading is worse than the raw one, fresh members
    f["eval_pairs_where_condensed_is_worse_than_raw"] = [sum(r["abs_curve_err"] > rows("raw", "eval", s)[i][l]["abs_curve_err"] for i, rr in rows("condensed", "eval", s).items() for l, r in enumerate(rr)) for s in SEEDS]
    # tested
    f["tested_max_percent"] = {rd: round(100 * max(r["abs_curve_err"] for s in SEEDS for rr in rows(rd, "tested", s).values() for r in rr), 3) for rd in ("condensed", "raw")}
    # amplitudes of the fresh fields
    av = [x for s in SEEDS for i, m in cond[s].items() if man[i]["split"] == "eval" for x in m["a"]]
    f["amplitudes_eval_all_seeds"] = {"min": min(av), "max": max(av), "median": quantile(av, 0.5), "n": len(av)}
    # within bound and certified bound
    f["within_bound_all"] = all(r["within_bound"] for rd in ("condensed", "raw") for st in ("eval", "former", "tested") for s in SEEDS for rr in rows(rd, st, s).values() for r in rr)
    f["evaluate_failed_any"] = any(r["evaluate_failed"] for rd in ("condensed", "raw") for st in ("eval", "former", "tested") for s in SEEDS for rr in rows(rd, st, s).values() for r in rr)
    f["infinite_any"] = any(math.isinf(r["curve_err"]) for rd in ("condensed", "raw") for st in ("eval", "former", "tested") for s in SEEDS for rr in rows(rd, st, s).values() for r in rr)
    f["raw_C2_minus_threshold_percentage_points"] = round(100 * (v["reported_readings"]["raw"]["C2_value"] - 0.10), 3)
    f["fy_min_at_or_above_300_with_pair_above_10_condensed_8mm"] = [sum(rr[6]["abs_curve_err"] > 0.10 and man[i]["params"]["fy"] >= 300 for i, rr in rows("condensed", "eval", s).items()) for s in SEEDS]
    if a.out:
        open(a.out, "w").write(json.dumps(f, indent=1))
    print(json.dumps(f, indent=1))


if __name__ == "__main__":
    main()
