# Independent audit of gate G-C2.3: the units of work for the checks of the defect of the measuring code.
#
# What it does. It writes the lists of units that solve_pairs.py takes, for everything but the sample of pairs
# (make_units.py writes that one). A unit is a list of steps on one problem object of one member; see the header
# of solve_pairs.py for the steps. The lists:
#   A.json        the three returned infinite rows and the failure of the author's first recomputation, each after
#                 the pair at 8 mm that precedes it and from a zero element state (members third_0034, eval_0063);
#   A_chain.json  the whole member third_0034 of the label-free arm in the visiting order of the stamped evaluation:
#                 the seven labels evaluated first, then for each seed the condensed reading and the raw one;
#   C.json        the failed solve of gate G-C2.1 (eval_0046, supervised seed 1 at 0.5 mm, after seed 0 at 8 mm);
#                 give solve_pairs.py that gate's instances, labels and runs;
#   E.json        the set energies at the failing first evaluation of third_0034, from the kept state and from zero;
#   D.json        ten members of the third sample other than third_0034, drawn with numpy's
#                 default_rng(2026112202): after each of four solves at 8 mm (seeds 5 and 6, condensed and raw),
#                 probes of the first evaluation at 0.5 mm for the six pairs of the label-free arm;
#   F.json        every evaluated member: a probe at 0.5 mm from the element state of the member's own label at 8 mm;
#   G.json        round 2: after one solve at 8 mm in three members (two states that fail, one that does not), probes
#                 for all twelve pairs of both arms and both readings at 0.5 mm and 1 mm (and 2 mm for eval_0063).
# In the audit not every unit of D.json and F.json was run; the reports say how many were.
#
# Usage: python -I make_defect_units.py <folder with the returned manifest.json> <folder for the lists>
import json
import os
import sys

import numpy as np


def pair(run, reading, level, evaluate=True):
    return {"op": "pair", "run": run, "reading": reading, "level": level, "evaluate": evaluate}


def probe(run, reading, level, cap=400):
    return {"op": "probe", "run": run, "reading": reading, "level": level, "cap": cap}


Z = {"op": "zero"}


def main():
    rec, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    man = json.load(open(os.path.join(rec, "manifest.json"), encoding="utf-8"))
    evaluated = [r["id"] for r in man["instances"] if r["split"] in ("third", "eval", "tested")]
    lf5, lf6, lf7 = "label_free_s5", "label_free_s6", "label_free_s7"
    s5, s6 = "supervised_512_s5", "supervised_512_s6"
    lists = {}
    lists["A"] = [
        {"id": "A1_third0034_s6raw", "member": "third_0034",
         "steps": [Z, pair(lf6, "condensed", 6), probe(lf6, "raw", 0), pair(lf6, "raw", 0), pair(lf6, "raw", 1), Z, probe(lf6, "raw", 0),
                   pair(lf6, "raw", 0)]},
        {"id": "A2_third0034_s7cond", "member": "third_0034",
         "steps": [Z, pair(lf6, "raw", 6), probe(lf7, "condensed", 0), pair(lf7, "condensed", 0), Z, pair(lf6, "condensed", 6),
                   probe(lf7, "condensed", 0), pair(lf7, "condensed", 0), Z, probe(lf7, "condensed", 0), pair(lf7, "condensed", 0)]},
        {"id": "A3_eval0063_s6cond", "member": "eval_0063",
         "steps": [Z, pair(s5, "raw", 6), probe(s6, "condensed", 0), pair(s6, "condensed", 0), probe(s6, "condensed", 1),
                   pair(s6, "condensed", 1), probe(s6, "condensed", 2), pair(s6, "condensed", 2), Z, pair(s6, "condensed", 0), Z,
                   pair(s6, "condensed", 1)]}]
    chain = [{"op": "label", "level": l} for l in range(7)]
    for seed in (5, 6, 7):
        for reading in ("condensed", "raw"):
            chain += [pair(f"label_free_s{seed}", reading, l) for l in range(7)]
    lists["A_chain"] = [{"id": "A4_chain_third0034_label_free", "member": "third_0034", "steps": chain}]
    c0, c1 = "supervised_64_s0", "supervised_64_s1"
    lists["C"] = [{"id": "C1_c21_eval0046", "member": "eval_0046",
                   "steps": [Z, pair(c0, "raw", 6), probe(c1, "raw", 0), pair(c1, "raw", 0), Z, probe(c1, "raw", 0), pair(c1, "raw", 0),
                             {"op": "fresh"}, pair(c1, "raw", 0)]}]
    lists["E"] = [{"id": "E1_third0034_energy", "member": "third_0034",
                   "steps": [Z, probe(lf7, "condensed", 0), pair(lf6, "condensed", 6, False), probe(lf7, "condensed", 0), probe(lf6, "raw", 0)]}]
    members = [f"third_{i:04d}" for i in range(64) if i != 34]
    rng = np.random.default_rng(2026112202)
    lists["D"] = []
    for m in [members[i] for i in rng.permutation(len(members))[:10]]:
        for seed, reading in ((5, "condensed"), (5, "raw"), (6, "condensed"), (6, "raw")):
            steps = [Z, pair(f"label_free_s{seed}", reading, 6, False)]
            steps += [probe(f"label_free_s{s2}", r2, 0, 200) for s2 in (5, 6, 7) for r2 in ("condensed", "raw")]
            lists["D"].append({"id": f"D_{m}_after_s{seed}_{reading}_8mm", "member": m, "steps": steps})
    lists["F"] = [{"id": f"F2_{m}", "member": m, "steps": [Z, {"op": "label_state", "level": 6}, probe(lf5, "condensed", 0, 300)]}
                  for m in evaluated]
    runs = [f"{a}_s{s}" for a in ("label_free", "supervised_512") for s in (5, 6, 7)]

    def every(level):
        return [probe(r, rd, level, 300) for r in runs for rd in ("condensed", "raw")]

    lists["G"] = [
        {"id": "G1_third_0034_after_lf_s6_condensed_8mm", "member": "third_0034", "steps": [Z, pair(lf6, "condensed", 6, False)] + every(0) + every(1)},
        {"id": "G2_eval_0063_after_sup_s5_raw_8mm", "member": "eval_0063", "steps": [Z, pair(s5, "raw", 6, False)] + every(0) + every(1) + every(2)},
        {"id": "G3_third_0000_after_lf_s5_condensed_8mm", "member": "third_0000", "steps": [Z, pair(lf5, "condensed", 6, False)] + every(0) + every(1)}]
    for name, units in lists.items():
        json.dump(units, open(os.path.join(out, name + ".json"), "w", encoding="utf-8"), indent=1)
        print(name, len(units), "units,", sum(len(u["steps"]) for u in units), "steps")


if __name__ == "__main__":
    main()
