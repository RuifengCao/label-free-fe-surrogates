"""Audit of gate G-C2.2, item 4: the stored outputs of the author's recomputation, compared by the auditor's own
code with the returned verdict.json (and, where they exist, with the auditor's own recomputed pairs).

  curves.json        the author's judged errors with exact solves: are the pairs exactly the 1,344 pairs of the
                     judged reading on the judged set, each once; the largest absolute difference of curve_err from
                     the returned row; each seed's median and 90th percentile and C1, C2 computed here from the
                     author's recomputed values;
  fields/*.json      the author's metrics that need no solve, for every returned field: the largest absolute
                     difference of each metric from the returned row, and the containment in the bound;
  label checks       the largest values stored for the returned labels on the regenerated instances;
  own pairs          the author's recomputed curve_err against the auditor's (a3_recompute_pairs.py), for the pairs
                     both computed.

This reads the author's output files only; it imports none of the author's scripts.

Usage:  python -I a8_author_outputs.py RECORDS AUTHOR_AUDIT [--own PAIRS_OUT.jsonl] [--out OUT.json]
        RECORDS: gate_records of the return package; AUTHOR_AUDIT: joint/records/c22/audit of the proposed commit.
"""
import argparse
import json
import math
import os

KEYS = ("F_err", "e_err", "F_sigma_err", "gap", "bound", "iou_contact", "iou_plastic", "bolt_err", "u_rel_l2")


def quantile(values, q):
    s = sorted(values)
    h = (len(s) - 1) * q
    lo = int(math.floor(h)); hi = min(lo + 1, len(s) - 1); t = h - lo
    return s[lo] if t == 0 else s[lo] + t * (s[hi] - s[lo])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records"); ap.add_argument("author"); ap.add_argument("--own"); ap.add_argument("--out")
    a = ap.parse_args()
    v = json.load(open(os.path.join(a.records, "verdict.json")))
    man = {r["id"]: r for r in json.load(open(os.path.join(a.records, "manifest.json")))["instances"]}
    res = {}
    cv = json.load(open(os.path.join(a.author, "curves.json")))
    want = {(i, s, "condensed", l) for i, r in man.items() if r["split"] == "eval" for s in (5, 6, 7) for l in range(7)}
    got = [(r["id"], int(r["seed"]), r["reading"], int(r["level"])) for r in cv]
    worst, per = 0.0, {5: [], 6: [], 7: []}
    notes = 0
    author = {}
    for r in cv:
        row = v["readings"][r["reading"]][str(r["seed"])][f"{man[r['id']]['split']}_rows"][r["id"]][r["level"]]
        worst = max(worst, abs(r["curve_err"] - row["curve_err"]))
        per[int(r["seed"])].append(abs(r["curve_err"]))
        notes += bool(r.get("curve_note")) + bool(r.get("evaluate_failed"))
        author[(str(r["seed"]), r["reading"], r["id"], int(r["level"]))] = r["curve_err"]
    med = [quantile(per[s], 0.5) for s in (5, 6, 7)]; p90 = [quantile(per[s], 0.9) for s in (5, 6, 7)]
    res["curves"] = {"rows": len(cv), "distinct": len(set(got)), "exactly_the_judged_pairs": set(got) == want and len(got) == len(want),
                     "max_abs_diff_curve_err_from_returned": worst, "rows_with_a_note_or_failure": notes,
                     "per_seed_median": med, "per_seed_p90": p90, "C1": quantile(med, 0.5), "C2": quantile(p90, 0.5),
                     "max_diff_of_a_seed_median_or_p90_from_returned": max(
                         [abs(x - y) for x, y in zip(med, v["per_seed"]["abs_curve_err_median"])] + [abs(x - y) for x, y in zip(p90, v["per_seed"]["abs_curve_err_p90"])]),
                     "C1_diff": abs(quantile(med, 0.5) - v["C1_value"]), "C2_diff": abs(quantile(p90, 0.5) - v["C2_value"]),
                     "processor_hours": sum(r["seconds"] for r in cv) / 3600}
    fd = os.path.join(a.author, "fields")
    files = sorted(f for f in os.listdir(fd) if f.endswith(".json"))
    worstk = {k: 0.0 for k in KEYS}
    n = bound = 0
    lab = {"Pi_rel": 0.0, "F_rel": 0.0, "e_diff": 0.0, "res_unconstrained": 0.0, "levels": 0}
    parts = {"pairs": 0, "max_abs_diff": 0.0, "unknowns_differing": 0, "not_ok": 0}
    for f in files:
        m = json.load(open(os.path.join(fd, f)))
        iid = m["id"]
        for key, rows in m["runs"].items():
            seed, reading = key.split("|")
            box = v["readings"][reading][seed][f"{man[iid]['split']}_rows"][iid]
            for r, b in zip(rows, box):
                n += 1
                for k in KEYS:
                    worstk[k] = max(worstk[k], abs(r[k] - b[k]))
                bound += r["within_bound"] != b["within_bound"]
        for x in m["label_check"]:
            lab["levels"] += 1
            for k in ("Pi_rel", "F_rel", "e_diff", "res_unconstrained"):
                lab[k] = max(lab[k], abs(x[k]))
        for x in m["condensed_from_parts"].values():
            parts["pairs"] += 1
            parts["max_abs_diff"] = max(parts["max_abs_diff"], x["max_abs_diff"]); parts["unknowns_differing"] += x["unknowns_differing"]
            parts["not_ok"] += not (x["shapes_and_types_ok"] and x["finite"] and x["amplitude_as_float32_equal"])
    res["fields"] = {"files": len(files), "members_equal_the_evaluated_sets": sorted(f[:-5] for f in files) == sorted(i for i, r in man.items() if r["split"] != "train"),
                     "fields": n, "max_abs_diff": worstk, "largest_of_all": max(worstk.values()), "within_bound_differing": bound}
    res["label_check"] = lab
    res["condensed_from_parts"] = parts
    if a.own and os.path.exists(a.own):
        own = [json.loads(l) for l in open(a.own)]
        both = [(o, author[(o["seed"], o["reading"], o["id"], o["level"])]) for o in own if (o["seed"], o["reading"], o["id"], o["level"]) in author]
        res["own_pairs_against_author"] = {"own_pairs": len(own), "in_both": len(both),
                                           "max_abs_diff": max((abs(o["curve_err"] - x) for o, x in both), default=None)}
    if a.out:
        open(a.out, "w").write(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
