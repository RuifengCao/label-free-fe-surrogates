"""Audit of gate G-C2.2, item 1b, step 1: choose the pairs whose judged error is recomputed with an exact solve.

The choice is the auditor's and is made from the per-pair values of verdict.json, in this order of priority:
  A  judged reading and set (condensed, eval): for each seed, the 7 pairs with the largest distance (they include
     every pair above 10%);
  B  judged reading and set: for each seed, the pairs at ranks 221 to 226 of the sorted distances (the median
     interpolates between ranks 223 and 224, counted from 0) and at ranks 400 to 405 (the 90th percentile
     interpolates between ranks 402 and 403); and the 3 pairs nearest 5% and the 3 nearest 10%;
  C  judged reading and set: a random sample of 14 pairs a seed (numpy generator seeded with --rng);
  D  raw reading on eval (the author did not recompute these with exact solves): for each seed ranks 401 to 404,
     the 2 largest, and 4 random pairs;
  E  the reported sets: for each seed, condensed former: the 2 largest and 2 random; raw former: 2 random;
     tested: 1 random pair in each reading.
A pair is listed once. The list is written in priority order as JSON: [seed, reading, set, member, level index].

Usage:  python -I a2_select_pairs.py RECORDS --out PAIRS.json [--rng 20261115]
"""
import argparse
import json
import os

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rng", type=int, default=20261115)
    a = ap.parse_args()
    v = json.load(open(os.path.join(a.records, "verdict.json")))
    rng = np.random.default_rng(a.rng)
    seeds = ["5", "6", "7"]

    def pairs(reading, s, seed):
        rows = v["readings"][reading][seed][f"{s}_rows"]
        return sorted(((r["abs_curve_err"], iid, l) for iid, rr in rows.items() for l, r in enumerate(rr)))

    chosen, why = [], {}

    def add(seed, reading, s, iid, l, tag):
        key = (seed, reading, s, iid, l)
        if key not in why:
            why[key] = tag
            chosen.append(key)

    for seed in seeds:                                   # A
        p = pairs("condensed", "eval", seed)
        for x, iid, l in p[-7:][::-1]:
            add(seed, "condensed", "eval", iid, l, "A largest")
    for seed in seeds:                                   # B
        p = pairs("condensed", "eval", seed)
        for k in list(range(221, 227)) + list(range(400, 406)):
            add(seed, "condensed", "eval", p[k][1], p[k][2], f"B rank {k}")
        for thr in (0.05, 0.10):
            for x, iid, l in sorted(p, key=lambda t: abs(t[0] - thr))[:3]:
                add(seed, "condensed", "eval", iid, l, f"B near {thr}")
    blocks = []
    for seed in seeds:                                   # C, D, E are interleaved by seed below
        p = pairs("condensed", "eval", seed)
        c = [(seed, "condensed", "eval", p[k][1], p[k][2], "C random") for k in rng.choice(len(p), 14, replace=False)]
        p = pairs("raw", "eval", seed)
        d = [(seed, "raw", "eval", p[k][1], p[k][2], f"D rank {k}") for k in range(401, 405)]
        d += [(seed, "raw", "eval", x[1], x[2], "D largest") for x in p[-2:]]
        d += [(seed, "raw", "eval", p[k][1], p[k][2], "D random") for k in rng.choice(len(p), 4, replace=False)]
        p = pairs("condensed", "former", seed)
        e = [(seed, "condensed", "former", x[1], x[2], "E largest") for x in p[-2:]]
        e += [(seed, "condensed", "former", p[k][1], p[k][2], "E random") for k in rng.choice(len(p), 2, replace=False)]
        p = pairs("raw", "former", seed)
        e += [(seed, "raw", "former", p[k][1], p[k][2], "E random") for k in rng.choice(len(p), 2, replace=False)]
        for reading in ("condensed", "raw"):
            p = pairs(reading, "tested", seed)
            k = int(rng.integers(len(p)))
            e.append((seed, reading, "tested", p[k][1], p[k][2], "E random"))
        blocks.append((c, d, e))
    # interleave so that a job stopped early has covered every class: D first halves, then C, then the rest
    order = []
    for c, d, e in blocks:
        order += d[:6]
    for c, d, e in blocks:
        order += c[:7]
    for c, d, e in blocks:
        order += e + d[6:]
    for c, d, e in blocks:
        order += c[7:]
    for seed, reading, s, iid, l, tag in order:
        add(seed, reading, s, iid, l, tag)
    out = [{"seed": k[0], "reading": k[1], "set": k[2], "id": k[3], "level": k[4], "why": why[k]} for k in chosen]
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    count = {}
    for r in out:
        t = r["why"].split()[0] + " " + r["reading"] + " " + r["set"]
        count[t] = count.get(t, 0) + 1
    print(len(out), "pairs;", count, "; members", len({r["id"] for r in out}))


if __name__ == "__main__":
    main()
