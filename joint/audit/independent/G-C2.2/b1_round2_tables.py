"""Audit of gate G-C2.2, round 2: the tables added to the part "Numbers" of the verdict document, derived again.

The corrected document has three new groups of generated tables:
  - the other readings by level, for the fresh held-out members and for the held-out members of G-C2.1 (both
    readings, three seeds, seven levels: medians over the 64 members at a level, and the count within the bound);
  - the tested members overall (for each reading and seed: each member over its seven levels, and all four members
    over their 28 pairs: medians, and the count within the bound);
  - every reading of the tested members by level (single values).
Every cell is computed here from the per-pair rows of verdict.json with the auditor's own code (own quantile, own
formatting) and compared, as text, with the cell of the document. The tables are found by the names of their
columns, not by their position. The sentence that counts the returned rows above the first new table is checked too.
Nothing of the author's writer is imported.

Usage:  python -I b1_round2_tables.py RECORDS DOCUMENT [--out OUT.json]
        RECORDS is the folder gate_records of the return package, DOCUMENT the corrected verdict document.
"""
import argparse
import json
import math
import os
import re

SEEDS = ["5", "6", "7"]
LEVELS = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
READINGS = ["condensed", "raw"]


def quantile(values, q):
    s = sorted(values)
    h = (len(s) - 1) * q
    lo = int(math.floor(h)); hi = min(lo + 1, len(s) - 1); t = h - lo
    return s[lo] if t == 0 else s[lo] + t * (s[hi] - s[lo])


def med(rows, key):
    return quantile([r[key] for r in rows], 0.5)


def pct(x, d=2):
    return f"{100 * x:.{d}f}%"


def spct(x, d=2):
    return f"{100 * x:+.{d}f}%"


def other(rows):
    """The eleven cells of the other readings of a group of per-pair rows."""
    return [spct(med(rows, "F_err")), pct(med(rows, "abs_F_err")), pct(med(rows, "bound")),
            f"{sum(1 for r in rows if r['within_bound'])} of {len(rows)}", spct(med(rows, "e_err")), spct(med(rows, "F_sigma_err")),
            pct(med(rows, "gap"), 3), f"{med(rows, 'iou_contact'):.3f}", f"{med(rows, 'iou_plastic'):.3f}", spct(med(rows, "bolt_err")),
            pct(med(rows, "u_rel_l2"))]


def tables(text):
    """Every markdown table of the text: (header cells, rows of cells, line number of the header)."""
    out, cur = [], None
    for n, line in enumerate(text.split("\n"), 1):
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cur is None:
                cur = (cells, [], n)
                out.append(cur)
            elif not all(set(c) <= set("-: ") for c in cells):
                cur[1].append(cells)
        else:
            cur = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records"); ap.add_argument("document"); ap.add_argument("--out")
    a = ap.parse_args()
    v = json.load(open(os.path.join(a.records, "verdict.json")))
    text = open(a.document, encoding="utf-8").read()
    tabs = tables(text)

    def rows(reading, seed, s):
        return v["readings"][reading][seed][f"{s}_rows"]

    mine = {}
    for s in ("eval", "former"):
        t = []
        for reading in READINGS:
            for seed in SEEDS:
                r = rows(reading, seed, s)
                for k, d in enumerate(LEVELS):
                    t.append([reading, seed, f"{d:g}"] + other([r[i][k] for i in sorted(r)]))
        mine[f"by level, {s}"] = t
    t1, t2 = [], []
    for reading in READINGS:
        for seed in SEEDS:
            r = rows(reading, seed, "tested")
            groups = [(i.replace("tested_", ""), r[i]) for i in sorted(r)]
            groups.append(("all four", [x for _, g in groups for x in g]))
            for label, g in groups:
                t1.append([reading, seed, label, pct(quantile([abs(x["curve_err"]) for x in g], 0.5)), spct(med(g, "curve_err"))] + other(g))
            for i in sorted(r):
                for k, d in enumerate(LEVELS):
                    t2.append([reading, seed, i.replace("tested_", ""), f"{d:g}", spct(r[i][k]["curve_err"])] + other([r[i][k]]))
    mine["tested overall"] = t1
    mine["tested by level"] = t2

    by_level = [t for t in tabs if t[0][:4] == ["Reading", "Seed", "$D$ (mm)", "Force at the same $D$, signed"]]
    overall = [t for t in tabs if t[0][:5] == ["Reading", "Seed", "Member", "Distance", "Signed distance"]]
    tlevel = [t for t in tabs if t[0][:5] == ["Reading", "Seed", "Member", "$D$ (mm)", "Signed distance"]]
    found = {"by level, eval": by_level[0] if len(by_level) > 0 else None, "by level, former": by_level[1] if len(by_level) > 1 else None,
             "tested overall": overall[0] if overall else None, "tested by level": tlevel[0] if tlevel else None}
    labels = {"by level, eval": 3, "by level, former": 3, "tested overall": 3, "tested by level": 4}
    res, total, wrong = {"tables_found": {k: (None if t is None else {"header_line": t[2], "columns": len(t[0]), "rows": len(t[1])}) for k, t in found.items()},
                         "counts_of_tables_by_header": [len(by_level), len(overall), len(tlevel)]}, 0, 0
    for key, t in found.items():
        m = mine[key]
        if t is None:
            res[key] = "table not found"; continue
        bad = []
        if len(t[1]) != len(m):
            bad.append(f"rows: document {len(t[1])}, auditor {len(m)}")
        n = 0
        for i, (x, y) in enumerate(zip(m, t[1])):
            if len(x) != len(y):
                bad.append(f"row {i}: {len(y)} cells in the document, {len(x)} derived")
            for j, (cx, cy) in enumerate(zip(x, y)):
                if j < labels[key]:
                    if cx != cy:
                        bad.append(f"label, row {i}: document '{cy}', auditor '{cx}'")
                    continue
                n += 1
                if cx != cy:
                    bad.append(f"row {i} column {j}: document '{cy}', auditor '{cx}'")
        res[key] = {"cells": n, "differing": bad[:20], "number_differing": len(bad)}
        total += n; wrong += len(bad)
    res["total_cells"] = total; res["differing_cells"] = wrong
    every = [x for reading in READINGS for seed in SEEDS for s in ("eval", "former", "tested") for r in rows(reading, seed, s).values() for x in r]
    sentence = (f"Of the {len(every):,} returned rows, {sum(math.isinf(x['curve_err']) for x in every)} have an infinite distance "
                f"and {sum(bool(x['evaluate_failed']) for x in every)} a field that the reference code could not evaluate.")
    res["sentence_on_the_rows"] = {"derived": sentence, "in_document": sentence in text}
    res["within_bound_all"] = all(x["within_bound"] for x in every)
    res["cells_showing_minus_zero"] = sum(c in ("-0.00%", "-0.000%") for t in mine.values() for row in t for c in row)
    if a.out:
        open(a.out, "w").write(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
