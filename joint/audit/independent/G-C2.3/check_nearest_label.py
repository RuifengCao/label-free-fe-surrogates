# Independent audit of gate G-C2.3, round 3: from which label does the exact solve of each returned pair start?
#
# What it checks. The stamped metric starts the exact solve of a pair from the label whose end displacement is
# nearest to the pair's predicted end displacement (the first of the nearest, as numpy's argmin takes it). This
# script takes the predicted end displacement of every returned row from the two rows files (the value "e" that
# the stamped evaluation wrote) and the labels' end displacements from the label files, and counts, for each arm
# and reading and at each level, the pairs whose nearest label is that of their own level, of a level below and
# of a level above, and by how many levels. It solves nothing and imports nothing of the repository. As a
# cross-check it reads the same end displacements from the prediction files (the last unknown of a field) and
# counts the pairs for which the two sources give another label.
#
# Usage: python -I check_nearest_label.py <unpacked return package or kept copy whole (rows, labels, run_files)>
#            <summary.json>
import json
import os
import sys

import numpy as np

LEVELS = (0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0)
FILES = {"condensed": "preds_condensed.npz", "raw": "preds.npz"}


def main():
    R, outp = sys.argv[1], sys.argv[2]
    out = {}
    labels = {}
    total_first = same_first = 0
    for arm in ("label_free", "supervised_512"):
        rows = json.load(open(os.path.join(R, f"rows_{arm}.json"), encoding="utf-8"))
        for reading in ("condensed", "raw"):
            own = [0] * 7
            below = [0] * 7
            above = [0] * 7
            steps = {}
            other_source = 0
            n = 0
            for seed in ("5", "6", "7"):
                preds = np.load(os.path.join(R, "run_files", f"{arm}_s{seed}", FILES[reading]))
                for st in ("third", "eval", "tested"):
                    for member, rr in rows["readings"][reading][seed][f"{st}_rows"].items():
                        if member not in labels:
                            with np.load(os.path.join(R, "labels", member + ".npz")) as z:
                                labels[member] = [float(v) for v in z["e"]]
                        ref = labels[member]
                        field_e = preds[member][:, -1].astype(float)
                        for l, r in enumerate(rr):
                            d = [abs(v - r["e"]) for v in ref]
                            k = d.index(min(d))                     # the first of the nearest
                            d2 = [abs(v - float(field_e[l])) for v in ref]
                            other_source += d2.index(min(d2)) != k
                            n += 1
                            if k == l:
                                own[l] += 1
                            elif k < l:
                                below[l] += 1
                            else:
                                above[l] += 1
                            if k != l:
                                steps[k - l] = steps.get(k - l, 0) + 1
            total_first += own[0] + below[0] + above[0]
            same_first += own[0]
            out[f"{arm}|{reading}"] = {"pairs": n, "own_level": own, "level_below": below, "level_above": above,
                                       "by_levels_of_distance": {str(k): v for k, v in sorted(steps.items())},
                                       "other_label_from_the_prediction_files": int(other_source)}
            hi = sum(own[1:]) + sum(below[1:]) + sum(above[1:])
            print(f"{arm}, {reading}: {n} pairs; nearest label not that of the own level, by level: {[b + a for b, a in zip(below, above)]}; "
                  f"above 0.5 mm: own level {sum(own[1:])} of {hi}, a level below {sum(below[1:])}, a level above {sum(above[1:])}; "
                  f"distance in levels: {out[f'{arm}|{reading}']['by_levels_of_distance']}; other label from the prediction files: {other_source}")
    out["at_0.5_mm"] = {"pairs": total_first, "label_of_0.5_mm": same_first}
    print(f"pairs at 0.5 mm whose nearest label is that of 0.5 mm, both arms and both readings: {same_first} of {total_first}")
    json.dump(out, open(outp, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
