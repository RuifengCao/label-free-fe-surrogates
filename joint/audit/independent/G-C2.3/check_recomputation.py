# Independent audit of gate G-C2.3: the stored outputs of the author's recomputation against the returned rows,
# and the two tables of the verdict document that report them.
#
# What it checks, with the auditor's own code (the author's scripts are not imported):
#   1. host_order.json (the exact solves in the gate's visiting order) and curves.json (the solves in another
#      order): for each reading, set and run the number of pairs, the largest absolute difference of the signed
#      error from the returned row, and the rows that are infinite as returned and as recomputed; the same for the
#      other metrics; the processor hours;
#   2. the two tables of the part "Numbers" that give these values, cell by cell;
#   3. the pairs present in both orders: where both are finite, their largest difference; the pairs finite in one
#      order only;
#   4. the environment that each stored record names;
#   5. the four training label files that the author took from the host: their SHA-256 against the returned
#      ledger, and the draw of the four members with numpy's default_rng(20261120);
#   6. the label files of the fresh members of the base gate and of the tested members against the base gate's
#      deposit record.
#
# Usage: python -I check_recomputation.py <verdict document> <records/c23/audit of the proposed tree>
#            <unpacked return package (gate3_records)> <folder with the four training label files>
#            <deposit.json of the base gate> <summary.json>
import glob
import hashlib
import json
import math
import os
import re
import sys

import numpy as np

OTHER = ("F_err", "e_err", "F_sigma_err", "gap", "bound", "iou_contact", "iou_plastic", "bolt_err", "u_rel_l2", "e", "F")


def main():
    docp, aud, R, train_dir, dep22, outp = sys.argv[1:7]
    J = lambda p: json.load(open(p, encoding="utf-8"))  # noqa: E731
    rf = {a: J(os.path.join(R, f"rows_{a}.json")) for a in ("label_free", "supervised_512")}

    def returned(run, reading, member, level):
        arm, seed = run.rsplit("_s", 1)
        for s in ("third", "eval", "tested"):
            rr = rf[arm]["readings"][reading][seed][f"{s}_rows"]
            if member in rr:
                return s, rr[member][level]

    def table(rows):
        by, other, secs = {}, 0.0, 0.0
        for r in rows:
            s, b = returned(r["run"], r["reading"], r["id"], r["level"])
            k = (r["reading"], s, r["run"])
            e = by.setdefault(k, {"n": 0, "max": 0.0, "inf_ret": 0, "inf_rec": 0})
            e["n"] += 1
            a, c = r["curve_err"], b["curve_err"]
            e["inf_ret"] += math.isinf(c)
            e["inf_rec"] += math.isinf(a)
            if math.isinf(a) or math.isinf(c):
                if a != c:
                    e["max"] = float("inf")
            else:
                e["max"] = max(e["max"], abs(a - c))
            for key in OTHER:
                other = max(other, abs(r[key] - b[key]))
            secs += r["seconds"]
        return by, other, secs

    out = {}
    host = J(os.path.join(aud, "host_order.json"))
    host_rows = [r for arm in host for m in host[arm] for r in host[arm][m]]
    curves = J(os.path.join(aud, "curves.json"))
    doc = open(docp, encoding="utf-8").read()
    tabs = re.findall(r"\| Reading, set, run \| Pairs recomputed \|[^\n]*\n\|[-|]+\|\n((?:\|[^\n]*\n)+)", doc)
    bad, cells = [], 0
    for name, rows, tab in (("gate's order", host_rows, tabs[0]), ("another order", curves, tabs[1])):
        by, other, secs = table(rows)
        fin = [v["max"] for v in by.values() if math.isfinite(v["max"])]
        out[name] = {"pairs": len(rows), "groups": len(by), "largest_finite_difference_of_the_error": max(fin),
                     "largest_difference_of_the_other_metrics": other, "processor_hours": secs / 3600,
                     "infinite_as_returned": sum(v["inf_ret"] for v in by.values()),
                     "infinite_as_recomputed": sum(v["inf_rec"] for v in by.values())}
        print(name, out[name])
        lines = [[c.strip() for c in l.strip().strip("|").split("|")] for l in tab.strip().splitlines()]
        want = {f"{k[0]}, {k[1]}, {k[2]}": v for k, v in by.items()}
        if len(lines) != len(want):
            bad.append((name, "rows", len(lines), len(want)))
        for c in lines:
            v = want.get(c[0])
            cells += 4
            if v is None:
                bad.append((name, c[0], "no such group"))
                continue
            shown = float("inf") if c[2] == "infinite" else float(c[2])
            ok = (shown == v["max"]) if math.isinf(shown) or math.isinf(v["max"]) else abs(shown - v["max"]) <= 0.051 * 10 ** math.floor(math.log10(shown)) * 1.0001 if shown else v["max"] == 0
            if int(c[1].replace(",", "")) != v["n"] or not ok or int(c[3]) != v["inf_ret"] or int(c[4]) != v["inf_rec"]:
                bad.append((name, c, v))
    print("cells of the two tables derived again:", cells, "| not matching:", len(bad), bad[:5])
    out["tables"] = {"cells": cells, "not_matching": [str(b) for b in bad]}
    # 3. the two orders against each other
    h = {(r["id"], r["run"], r["reading"], r["level"]): r for r in host_rows}
    both = [(c, h[(c["id"], c["run"], c["reading"], c["level"])]) for c in curves if (c["id"], c["run"], c["reading"], c["level"]) in h]
    fin = [abs(a["curve_err"] - b["curve_err"]) for a, b in both if math.isfinite(a["curve_err"]) and math.isfinite(b["curve_err"])]
    one = [(a["id"], a["run"], a["reading"], a["level"], a["curve_err"], b["curve_err"]) for a, b in both
           if math.isfinite(a["curve_err"]) != math.isfinite(b["curve_err"])]
    out["two_orders"] = {"pairs_in_both": len(both), "largest_difference_where_both_finite": max(fin), "finite_in_one_only": one}
    print("two orders:", out["two_orders"])
    # which pairs of the other order sit at the first level of seeds 6 and 7 (the 128 that the document names)
    part1 = [c for c in curves if c["run"].startswith("label_free")]
    first = [c for c in part1 if c["level"] == 0 and c["run"][-1] in "67"]
    out["other_order"] = {"label_free_pairs": len(part1), "first_level_of_seeds_6_and_7": len(first),
                          "supervised_pairs": len(curves) - len(part1),
                          "supervised_pairs_by_member_and_run": sorted({(c["id"], c["run"]): 0 for c in curves if not c["run"].startswith("label_free")})}
    print("other order:", {k: v for k, v in out["other_order"].items()})
    # 4. environments
    env = {}
    for p in sorted(glob.glob(os.path.join(aud, "*.json"))):
        d = J(p)
        e = d.get("environment") if isinstance(d, dict) else None
        if os.path.basename(p).startswith("environment_"):
            e = d
        if e:
            env[os.path.basename(p)] = {k: e[k] for k in ("python", "numpy", "scipy", "zlib", "solver", "blas_threads_env", "cpus")}
    out["environments"] = env
    for k, v in env.items():
        print("  environment", k, v)
    # 5. the four training members
    led = {e["id"]: e for e in J(os.path.join(R, "ledger.json"))}
    rt = J(os.path.join(aud, "resolve_train.json"))
    ids = [m["id"] for m in rt["members"]]
    draw = sorted(f"train_{int(i):04d}" for i in np.random.default_rng(20261120).choice(512, size=4, replace=False))
    files = {}
    for i in ids:
        p = os.path.join(train_dir, "labels", i + ".npz")
        files[i] = os.path.exists(p) and hashlib.sha256(open(p, "rb").read()).hexdigest() == led[i]["label_sha256"]
    out["training_members"] = {"re_solved": ids, "drawn_by_the_auditor": draw, "same": sorted(ids) == draw, "label_files_have_ledger_sha256": files,
                               "largest_difference_of_the_unknowns": max(m["max_z_diff_over_max_z"] for m in rt["members"]),
                               "iterations_as_ledger": all(m["iterations"] == m["ledger_iterations"] for m in rt["members"])}
    print("training members:", out["training_members"])
    rs = J(os.path.join(aud, "resolve.json"))
    out["held_out_members"] = {"re_solved": [m["id"] for m in rs["members"]], "largest_difference_of_the_unknowns": max(m["max_z_diff_over_max_z"] for m in rs["members"]),
                               "bit_identical": [m["bit_identical"] for m in rs["members"]],
                               "iterations_as_ledger": all(m["iterations"] == m["ledger_iterations"] for m in rs["members"])}
    print("held-out members:", out["held_out_members"])
    # 6. the labels shared with the base gate's deposit
    d22 = J(dep22)
    fl = d22.get("files")
    if isinstance(fl, dict):
        fl = [dict(v, file=k) if isinstance(v, dict) else {"file": k, "sha256": v} for k, v in fl.items()]
    sha22 = {(f.get("file") or f.get("name") or f.get("path")): f["sha256"] for f in fl}
    same = diff = absent = 0
    for i, e in led.items():
        if i.startswith(("eval_", "tested_")):
            k = next((k for k in sha22 if k.endswith(f"labels/{i}.npz")), None)
            if k is None:
                absent += 1
            elif sha22[k] == e["label_sha256"]:
                same += 1
            else:
                diff += 1
    out["labels_shared_with_base_gate"] = {"same_sha256": same, "different": diff, "not_in_base_deposit": absent}
    print("labels of the base gate's fresh members and of the tested members against the base gate's deposit:", out["labels_shared_with_base_gate"])
    json.dump(out, open(outp, "w", encoding="utf-8"), indent=1, default=str)


if __name__ == "__main__":
    main()
