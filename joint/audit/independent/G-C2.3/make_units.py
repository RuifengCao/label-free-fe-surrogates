# Independent audit of gate G-C2.3: the sample of pairs whose error the auditor recomputes with exact solves.
#
# What it does. It reads the two returned rows files and writes the list of units for solve_pairs.py. Every unit
# is one pair, solved on a new problem object (element state zero). The rule of the sample, fixed before any of
# these solves was made (all on the third sample unless a set is named):
#   B1  label-free arm, condensed reading: every pair whose returned error exceeds 10% in at least one run, in all
#       three runs;
#   B2  label-free arm, condensed reading: every pair that is not flagged and whose returned error exceeds 5% in
#       at least one run, in all three runs;
#   B3  for each arm, seed and reading (12 blocks of 448 pairs): the four pairs whose errors are the order
#       statistics that the median (ranks 224 and 225) and the 90th percentile (ranks 403 and 404) interpolate;
#   B4  drawn with numpy's default_rng(20261122), in this order and without replacement inside a stratum:
#       12 of the 128 pairs of the label-free arm, condensed, at 0.5 mm in seeds 6 and 7 (in the gate's order
#          they start from the element state of a solve at 8 mm);
#       8 pairs of the supervised arm condensed and 8 raw; 8 pairs of the label-free arm raw;
#       on the fresh members of G-C2.2: 6 pairs label-free condensed, 4 supervised raw;
#       on the tested members: 2 pairs label-free condensed, 2 supervised raw.
# Pairs whose returned error is infinite are left to the units of the defect and are not drawn here.
#
# Usage: python -I make_units.py <folder with the rows files and c23_config.json> <units.json>
import json
import math
import sys

import numpy as np

SEEDS = ("5", "6", "7")


def main():
    folder, outp = sys.argv[1], sys.argv[2]
    rows = {a: json.load(open(f"{folder}/rows_{a}.json", encoding="utf-8")) for a in ("label_free", "supervised_512")}
    thr = json.load(open(f"{folder}/c23_config.json", encoding="utf-8"))["self_check"]["threshold"]
    units, seen = [], set()

    def add(tag, arm, seed, reading, member, level):
        key = (arm, seed, reading, member, level)
        r = None
        for s in ("third", "eval", "tested"):
            rr = rows[arm]["readings"][reading][seed][f"{s}_rows"]
            if member in rr:
                r = rr[member][level]
        if key in seen or math.isinf(r["curve_err"]):
            return False
        seen.add(key)
        units.append({"id": f"{tag}_{arm}_s{seed}_{reading}_{member}_L{level}", "member": member, "tag": tag,
                      "steps": [{"op": "pair", "run": f"{arm}_s{seed}", "reading": reading, "level": level,
                                 "evaluate": False}]})
        return True

    lf = rows["label_free"]["readings"]["condensed"]
    members = sorted(lf["5"]["third_rows"])
    err = {s: {(m, l): lf[s]["third_rows"][m][l]["abs_curve_err"] for m in members for l in range(7)} for s in SEEDS}
    F = {s: {(m, l): lf[s]["third_rows"][m][l]["F"] for m in members for l in range(7)} for s in SEEDS}
    for m in members:
        for l in range(7):
            f = sorted(F[s][(m, l)] for s in SEEDS)
            flagged = (f[2] - f[0]) / abs(f[1]) >= thr
            worst = max(err[s][(m, l)] for s in SEEDS)
            if worst > 0.10:
                for s in SEEDS:
                    add("B1", "label_free", s, "condensed", m, l)
            elif worst > 0.05 and not flagged:
                for s in SEEDS:
                    add("B2", "label_free", s, "condensed", m, l)
    for arm in ("label_free", "supervised_512"):
        for reading in ("condensed", "raw"):
            for s in SEEDS:
                rr = rows[arm]["readings"][reading][s]["third_rows"]
                order = sorted(((rr[m][l]["abs_curve_err"], m, l) for m in members for l in range(7)))
                for rank in (224, 225, 403, 404):
                    _, m, l = order[rank - 1]
                    add("B3", arm, s, reading, m, l)
    rng = np.random.default_rng(20261122)

    def draw(tag, n, arm, reading, pool):
        pool = list(pool)
        got = 0
        for i in rng.permutation(len(pool)):
            if got == n:
                break
            s, m, l = pool[i]
            got += bool(add(tag, arm, s, reading, m, l))

    draw("B4a", 12, "label_free", "condensed", [(s, m, 0) for s in ("6", "7") for m in members])
    third = [(s, m, l) for s in SEEDS for m in members for l in range(7)]
    draw("B4b", 8, "supervised_512", "condensed", third)
    draw("B4c", 8, "supervised_512", "raw", third)
    draw("B4d", 8, "label_free", "raw", third)
    ev = sorted(lf["5"]["eval_rows"])
    te = sorted(lf["5"]["tested_rows"])
    draw("B4e", 6, "label_free", "condensed", [(s, m, l) for s in SEEDS for m in ev for l in range(7)])
    draw("B4f", 4, "supervised_512", "raw", [(s, m, l) for s in SEEDS for m in ev for l in range(7)])
    draw("B4g", 2, "label_free", "condensed", [(s, m, l) for s in SEEDS for m in te for l in range(7)])
    draw("B4h", 2, "supervised_512", "raw", [(s, m, l) for s in SEEDS for m in te for l in range(7)])
    json.dump(units, open(outp, "w", encoding="utf-8"), indent=1)
    by = {}
    for u in units:
        by[u["tag"]] = by.get(u["tag"], 0) + 1
    print(len(units), "units:", by)


if __name__ == "__main__":
    main()
