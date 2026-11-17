"""Audit of gate G-C2.2, item 1b, step 3: the agreement of the auditor's recomputed pairs with the returned values.

Reads the JSON lines written by a3_recompute_pairs.py and prints, for each class of the sample and in all: the
number of pairs, the largest absolute and relative difference of the signed distance F/F*(e) - 1 from the value in
verdict.json, the range of the returned distances covered, and the checks made on the way (convergence of every
solve, fixed and contact unknowns of the field, the regenerated instance against the manifest and the label).

Usage:  python -I a15_pairs_summary.py PAIRS_OUT.jsonl [--out OUT.json]
"""
import argparse
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs_out"); ap.add_argument("--out")
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(a.pairs_out)]
    groups = {}
    for r in rows:
        key = f"{r['why'].split()[0]} {r['reading']} {r['set']}"
        for k in (key, f"all {r['reading']} {r['set']}", "all"):
            g = groups.setdefault(k, {"pairs": 0, "max_abs_difference": 0.0, "max_rel_difference": 0.0, "smallest_abs_returned": float("inf"),
                                      "largest_abs_returned": 0.0, "seconds": 0.0})
            g["pairs"] += 1
            g["max_abs_difference"] = max(g["max_abs_difference"], abs(r["difference"]))
            g["max_rel_difference"] = max(g["max_rel_difference"], abs(r["difference"] / r["returned_curve_err"]))
            g["smallest_abs_returned"] = min(g["smallest_abs_returned"], abs(r["returned_curve_err"]))
            g["largest_abs_returned"] = max(g["largest_abs_returned"], abs(r["returned_curve_err"]))
            g["seconds"] += r["seconds"]
    res = {"groups": groups, "pairs": len(rows), "distinct": len({(r["seed"], r["reading"], r["id"], r["level"]) for r in rows}),
           "members": len({r["id"] for r in rows}), "all_converged": all(r["converged"] for r in rows),
           "all_fixed_unknowns_zero": all(r["fixed_zero"] for r in rows), "all_contact_unknowns_non_negative": all(r["contact_nonneg"] for r in rows),
           "all_instances_equal_manifest": all(all(r["instance"][k] for k in ("params_equal_manifest", "split_equal", "nodes_equal", "unknowns_equal")) for r in rows),
           "labels_on_regenerated_instances": {k: max(r["instance"][k] for r in rows) for k in ("label_Pi_rel", "label_F_rel", "label_e_abs")},
           "max_abs_difference_of_F_err": max(abs(r["F_err_same_D"] - r["returned_F_err"]) for r in rows),
           "max_abs_difference_of_e_err": max(abs(r["e_err"] - r["returned_e_err"]) for r in rows),
           "pairs_above_10_percent_recomputed": sum(abs(r["returned_curve_err"]) > 0.10 for r in rows if r["reading"] == "condensed" and r["set"] == "eval"),
           "by_seed_judged": {s: sum(1 for r in rows if r["seed"] == s and r["reading"] == "condensed" and r["set"] == "eval") for s in ("5", "6", "7")},
           "processor_hours": sum(r["seconds"] for r in rows) / 3600}
    if a.out:
        open(a.out, "w").write(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
