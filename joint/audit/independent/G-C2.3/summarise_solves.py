# Independent audit of gate G-C2.3: the results of solve_pairs.py against the returned rows.
#
# What it checks. It reads the result files that solve_pairs.py wrote and the two returned rows files, and prints:
#   1. for the sample (units of one pair each, from a zero element state): by stratum the number of pairs, the
#      largest absolute and relative difference of the signed error from the returned row, and every pair that
#      differs by more than a tolerance or is infinite on one side only;
#   2. for the units of several steps (the defect): every solve with the auditor's error, the returned one, their
#      difference, the notes, the size of the element state before and after, and whether the evaluation of the
#      predicted field changed the state; every probe with its numbers of element iterations and set energies;
#   3. for the probes after a state at 8 mm: whether the numbers of iterations depend on which pair follows, and
#      the distribution of the larger of the two numbers over the states.
# For units of another gate (rows held in that gate's verdict.json) give --c21 <verdict.json>.
#
# Usage: python -I summarise_solves.py <folder with the rows files> <results folder> [<results folder> ...]
#            [--c21 <verdict.json of G-C2.1>] [--tolerance 1e-9]
import glob
import json
import math
import os
import sys


def main():
    args = sys.argv[1:]
    tol, c21 = 1e-9, None
    if "--tolerance" in args:
        i = args.index("--tolerance")
        tol = float(args[i + 1])
        del args[i:i + 2]
    if "--c21" in args:
        i = args.index("--c21")
        c21 = json.load(open(args[i + 1], encoding="utf-8"))
        del args[i:i + 2]
    R, folders = args[0], args[1:]
    rows = {}

    def returned(run, reading, member, level):
        arm, seed = run.rsplit("_s", 1)
        if c21 is not None and arm in c21["arms"]:
            e = c21["arms"][arm][seed]
            for key in ("eval_rows", "tested"):
                if member in e[key]:
                    return e[key][member][level]
        if arm not in rows:
            p = os.path.join(R, f"rows_{arm}.json")
            if not os.path.exists(p):
                return None
            rows[arm] = json.load(open(p, encoding="utf-8"))
        for st in ("third", "eval", "tested"):
            rr = rows[arm]["readings"][reading][seed][f"{st}_rows"]
            if member in rr:
                return rr[member][level]
        return None

    sample, after8, labelstate = {}, [], []
    for folder in folders:
        for f in sorted(glob.glob(os.path.join(folder, "*.json"))):
            d = json.load(open(f, encoding="utf-8"))
            steps = d["steps"]
            ops = [s["op"] for s in steps]
            if ops == ["pair"]:                                  # the sample
                s = steps[0]
                r = returned(s["run"], s["reading"], d["member"], s["level"])
                a, b = s["curve_err"], r["curve_err"]
                both = math.isfinite(a) and math.isfinite(b)
                sample.setdefault(d["id"].split("_")[0], []).append(
                    (abs(a - b) if both else float("inf"), abs(a - b) / abs(b) if both and b else float("inf"), d["id"], a, b, s["seconds"]))
                continue
            if "label_state" in ops:                             # a probe from the state of a label
                k = ops.index("label_state")
                p = steps[k + 1]
                labelstate.append((d["member"], steps[k]["level"], p["level"], p["bubble_iterations"]))
                continue
            probes = [s for s in steps if s["op"] == "probe"]
            pairs = [s for s in steps if s["op"] == "pair"]
            if d["id"].startswith("D_"):                         # six probes after one solve at 8 mm
                after8.append((d["id"], [tuple(p["bubble_iterations"]) for p in probes], pairs[0]["curve_err"]))
                continue
            print("==", d["id"], d["member"])
            for s in steps:
                if s["op"] in ("zero", "fresh"):
                    print("   ", s["op"])
                elif s["op"] == "label":
                    print("    label at level", s["level"], "| state changed:", s["state_changed"], s.get("note", ""))
                elif s["op"] == "probe":
                    print(f"    probe {s['run']} {s['reading']} level {s['level']}: element iterations {s['bubble_iterations']}, "
                          f"set energies {s.get('set_energies')}, state size {[round(v, 4) for v in s['state_size_before']]}")
                else:
                    r = returned(s["run"], s["reading"], d["member"], s["level"])
                    a = s["curve_err"]
                    b = r["curve_err"] if r else float("nan")
                    diff = abs(a - b) if math.isfinite(a) and math.isfinite(b) else ("both infinite" if a == b else "ONE INFINITE")
                    print(f"    pair {s['run']} {s['reading']} level {s['level']}: mine {a!r}, returned {b!r}, difference {diff}; "
                          f"note [{s['note']}], returned note [{r['curve_note'] if r else ''}]; state {[round(v, 4) for v in s['state_size_before']]} -> "
                          f"{[round(v, 4) for v in s['state_size_after']]}; evaluation changed the state: {s.get('evaluate_changed_state')}")
    if sample:
        print("== the sample (one pair a unit, zero element state)")
        n = 0
        worst_abs = worst_rel = 0.0
        for tag in sorted(sample):
            v = sample[tag]
            n += len(v)
            worst_abs, worst_rel = max(worst_abs, max(x[0] for x in v)), max(worst_rel, max(x[1] for x in v))
            print(f"    {tag}: {len(v)} pairs, largest absolute difference {max(x[0] for x in v):.2e}, largest relative {max(x[1] for x in v):.2e}, "
                  f"largest returned error {max(abs(x[4]) for x in v):.4f}, seconds {sum(x[5] for x in v):.0f}")
        print(f"    total {n} pairs, largest absolute difference {worst_abs:.3e}, largest relative {worst_rel:.3e}")
        bad = [x[2:5] for v in sample.values() for x in v if not x[0] <= tol]
        print(f"    pairs differing by more than {tol} or infinite on one side:", bad or "none")
        above = [x for x in sample.get("B1", []) if abs(x[4]) > 0.10]
        print("    readings of B1 whose returned error is above 10%:", len(above))
    if after8:
        same = sum(1 for _, its, _ in after8 if len(set(its)) == 1)
        big = sorted(max(v for v in its[0] if isinstance(v, int)) if all(isinstance(v, int) for v in its[0]) else 10 ** 6 for _, its, _ in after8)
        print("== probes after a solve at 8 mm:", len(after8), "states;", same, "with the same numbers of iterations for all six next pairs;",
              "larger of the two numbers: least", big[0], "median", big[len(big) // 2], "most", big[-1], "; above the cap of 60:", sum(v > 60 for v in big))
    if labelstate:
        first = [x for x in labelstate if x[1] == 6 and x[2] == 0]
        big = sorted(max(x[3]) if all(isinstance(v, int) for v in x[3]) else 10 ** 6 for x in first)
        print("== probes at 0.5 mm from the state of the label at 8 mm:", len(first), "members; larger of the two numbers: least", big[0],
              "median", big[len(big) // 2], "90th percentile", big[int(0.9 * (len(big) - 1))], "most", big[-1], "; above 40:", sum(v > 40 for v in big),
              "; above the cap of 60:", sum(v > 60 for v in big))
        sets = {}
        for m, _, _, _ in first:
            sets[m.split("_")[0]] = sets.get(m.split("_")[0], 0) + 1
        print("    members by set:", sets)


if __name__ == "__main__":
    main()
