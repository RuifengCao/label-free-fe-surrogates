"""Audit of gate G-C2.2, item 3: the generated tables of the verdict document, derived again from the records.

Every cell of the tables of the part "Numbers" that can be derived from the return package is computed here with
the auditor's own code (own quantile, own counts) from verdict.json, manifest.json, the three condense.json and the
three history.json, formatted as the document formats it, and compared with the cell in the document. The tables of
the section on the author's recomputation are not covered here (they are compared with the author's stored outputs
by a8_author_outputs.py).

Usage:  python -I a7_document_tables.py RECORDS DOCUMENT [--out OUT.json]
        RECORDS is the folder gate_records of the return package, DOCUMENT the verdict document.
"""
import argparse
import json
import math
import os
import re

SEEDS = ["5", "6", "7"]
LEVELS = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]


def quantile(values, q):
    s = sorted(values)
    h = (len(s) - 1) * q
    lo = int(math.floor(h)); hi = min(lo + 1, len(s) - 1); t = h - lo
    return s[lo] if t == 0 else s[lo] + t * (s[hi] - s[lo])


def median(v):
    return quantile(v, 0.5)


def pct(x, d):
    return f"{100 * x:.{d}f}%"


def spct(x, d):
    return f"{100 * x:+.{d}f}%"


def tables(text):
    """The markdown tables of the document, each as (nearest headings, list of rows of cells)."""
    out, head, sub, rows = [], "", "", None
    for line in text.splitlines():
        if line.startswith("### "):
            head, sub = line[4:].strip(), ""
        elif line.startswith("## "):
            head, sub = line[3:].strip(), ""
        elif line.startswith("**") and line.rstrip().endswith("**"):
            sub = line.strip("* \n")
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if rows is None:
                rows = []
                out.append((head, sub, rows))
            if not all(set(c) <= set("-: ") for c in cells):
                rows.append(cells)
        else:
            rows = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records"); ap.add_argument("document"); ap.add_argument("--out")
    a = ap.parse_args()
    R = a.records
    v = json.load(open(os.path.join(R, "verdict.json")))
    man = {r["id"]: r for r in json.load(open(os.path.join(R, "manifest.json")))["instances"]}
    cond = {s: json.load(open(os.path.join(R, "run_files", f"label_free_s{s}", "condense.json")))["members"] for s in SEEDS}
    hist = {s: json.load(open(os.path.join(R, "run_files", f"label_free_s{s}", "history.json"))) for s in SEEDS}
    doc = tables(open(a.document, encoding="utf-8").read())

    def rows(reading, st, seed):
        return v["readings"][reading][seed][f"{st}_rows"]

    def flat(reading, st, seed, key="abs_curve_err"):
        return [r[key] for rr in rows(reading, st, seed).values() for r in rr]

    mine = {}                                         # (table key) -> list of rows of cells, header excluded

    def crit(reading):
        out = []
        for seed in SEEDS:
            x = flat(reading, "eval", seed)
            rr = rows(reading, "eval", seed)
            out.append([seed, pct(median(x), 3), pct(quantile(x, 0.9), 3), pct(max(x), 1), str(sum(t > 0.05 for t in x)), str(sum(t > 0.10 for t in x)),
                        str(sum(any(r["abs_curve_err"] > 0.10 for r in q) for q in rr.values())), str(sum(math.isinf(t) for t in x))])
        med = median([median(flat(reading, "eval", s)) for s in SEEDS]); p90 = median([quantile(flat(reading, "eval", s), 0.9) for s in SEEDS])
        out.append(["Median over the seeds", pct(med, 3), pct(p90, 3), "", "", "", "", ""])
        return out

    mine["criteria condensed"] = crit("condensed")
    mine["criteria raw"] = crit("raw")
    t = []
    for st, name, n in (("former", "held-out of G-C2.1", 448), ("tested", "tested", 28)):
        for reading in ("condensed", "raw"):
            for seed in SEEDS:
                x = flat(reading, st, seed); rr = rows(reading, st, seed)
                t.append([name, reading, seed, str(len(x)), pct(median(x), 3), pct(quantile(x, 0.9), 3), pct(max(x), 1), str(sum(q > 0.05 for q in x)),
                          str(sum(q > 0.10 for q in x)), str(sum(any(r["abs_curve_err"] > 0.10 for r in q) for q in rr.values()))])
    mine["reported sets"] = t

    def by_level(fun):
        out = []
        for reading in ("condensed", "raw"):
            for seed in SEEDS:
                rr = rows(reading, "eval", seed)
                out.append([reading, seed] + [fun([q[l] for q in rr.values()]) for l in range(7)])
        return out

    mine["level median"] = by_level(lambda q: pct(median([r["abs_curve_err"] for r in q]), 2))
    mine["level p90"] = by_level(lambda q: pct(quantile([r["abs_curve_err"] for r in q], 0.9), 2))
    mine["level above"] = by_level(lambda q: str(sum(r["abs_curve_err"] > 0.10 for r in q)))
    mine["level signed"] = by_level(lambda q: spct(median([r["curve_err"] for r in q]), 2))
    t = []
    for reading in ("condensed", "raw"):
        for seed in SEEDS:
            rr = rows(reading, "eval", seed)
            lo = [q[6]["abs_curve_err"] for i, q in rr.items() if man[i]["params"]["fy"] < 300]
            hi = [q[6]["abs_curve_err"] for i, q in rr.items() if man[i]["params"]["fy"] >= 300]
            t.append([reading, seed, pct(median(lo), 2), pct(quantile(lo, 0.9), 2), str(sum(x > 0.10 for x in lo)),
                      pct(median(hi), 2), pct(quantile(hi, 0.9), 2), str(sum(x > 0.10 for x in hi))])
    mine["yield"] = t
    mine["yield counts"] = [sum(man[i]["params"]["fy"] < 300 for i in rows("condensed", "eval", "5")), sum(man[i]["params"]["fy"] >= 300 for i in rows("condensed", "eval", "5"))]

    def tail(st):
        out = []
        for iid in sorted(rows("condensed", st, "5")):
            for l in range(7):
                c = [rows("condensed", st, s)[iid][l] for s in SEEDS]
                if any(r["abs_curve_err"] > 0.10 for r in c):
                    p = man[iid]["params"]
                    out.append([iid, f"{p['t_f']:.1f}", f"{p['fy']:.0f}", f"{p['w']:.0f}", f"{p['n']:.0f}", f"{LEVELS[l]:g} mm",
                                ", ".join(spct(r["curve_err"], 1) for r in c),
                                ", ".join(spct(rows("raw", st, s)[iid][l]["curve_err"], 1) for s in SEEDS),
                                ", ".join(f"{cond[s][iid]['a'][l]:.3f}" for s in SEEDS)])
        return out

    mine["tail eval"] = tail("eval")
    mine["tail former"] = tail("former")

    def other(st):
        out = []
        for reading in ("condensed", "raw"):
            for seed in SEEDS:
                g = lambda k: median(flat(reading, st, seed, k))   # noqa: E731
                wb = flat(reading, st, seed, "within_bound")
                out.append([reading, seed, pct(g("abs_F_err"), 3), spct(g("F_err"), 3), spct(g("e_err"), 3), spct(g("F_sigma_err"), 3), pct(g("gap"), 3),
                            pct(g("bound"), 3), spct(g("bolt_err"), 3), pct(g("u_rel_l2"), 3), f"{g('iou_contact'):.3f}", f"{g('iou_plastic'):.3f}",
                            pct(sum(wb) / len(wb), 1)])
        return out

    mine["other eval"] = other("eval")
    mine["other former"] = other("former")
    t = []
    names = {"eval": "fresh held-out", "former": "held-out of G-C2.1", "tested": "tested"}

    def sci(x):
        return "0" if x == 0 else f"{x:.1e}"

    for seed in SEEDS:
        for st in ("eval", "former", "tested"):
            ids = [i for i in cond[seed] if man[i]["split"] == st]
            av = [x for i in ids for x in cond[seed][i]["a"]]
            rise = [(c - r) / r for i in ids for c, r in zip(cond[seed][i]["Pi_condensed"], cond[seed][i]["Pi_raw"])]
            t.append([seed, names[st], str(len(av)), f"{min(av):.3f}", f"{median(av):.4f}", f"{max(av):.3f}",
                      str(sum(x for i in ids for x in cond[seed][i]["at_bound"])), str(sum(not x for i in ids for x in cond[seed][i]["converged"])),
                      f"{max(x for i in ids for x in cond[seed][i]['rel_slope']):.1e}", str(sum(x > 0 for x in rise)), sci(max(max(rise), 0.0)),
                      f"{median([-x for x in rise]):.1e}"])
    mine["amplitudes"] = t
    t = []
    for seed in SEEDS:
        h = hist[seed]
        loss, ep = h["loss"], h["epoch_seconds"]
        ps = sorted(x / 512 for x in ep)
        t.append([seed, f"{sum(loss[:10]) / 10:.4f}", f"{sum(loss[-10:]) / 10:.4f}", f"{max(loss):.4f}", str(len(h["cap_events"])), str(len(h["bursts"])),
                  f"{sum(ep) / 3600:.2f}", f"{ps[0]:.3f}, {median(ps):.3f}, {ps[-1]:.3f}",
                  "none" if h["resumed_from_epoch"] is None else str(h["resumed_from_epoch"]), f"{h['peak_memory_GiB']:.2f}"])
    mine["training"] = t
    t = []
    for iid in sorted(rows("condensed", "tested", "5")):
        for reading in ("condensed", "raw"):
            t.append([iid.replace("tested_", ""), reading] + [", ".join(spct(rows(reading, "tested", s)[iid][l]["curve_err"], 1) for s in SEEDS) for l in range(7)])
    mine["tested"] = t

    # ---- match the document's tables
    def find(head, sub=None, nth=0):
        hits = [rows_ for h, s, rows_ in doc if head in h and (sub is None or sub in s)]
        return hits[nth][1:] if hits else None

    pairs = [("criteria condensed", find("Criteria (condensed", "Condensed reading")), ("criteria raw", find("Criteria (condensed", "Raw reading")),
             ("reported sets", find("The two reported sets")),
             ("level median", find("The distance by level", "Median distance")), ("level p90", find("The distance by level", "90th percentile")),
             ("level above", find("The distance by level", "Pairs above 10%")), ("level signed", find("The distance by level", "Median signed")),
             ("yield", find("The distance at 8 mm")),
             ("tail eval", find("The pairs above 10%", "Fresh held-out")), ("tail former", find("The pairs above 10%", "Held-out members of G-C2.1")),
             ("other eval", find("The other readings", "Fresh held-out")), ("other former", find("The other readings", "Held-out members of G-C2.1")),
             ("amplitudes", find("The amplitudes of the condensed reading")), ("training", find("Training")), ("tested", find("The four tested members"))]
    res, total, wrong = {}, 0, 0
    for key, theirs in pairs:
        m = mine[key]
        if theirs is None:
            res[key] = "table not found in the document"; continue
        bad = []
        if len(theirs) != len(m):
            bad.append(f"rows: document {len(theirs)}, auditor {len(m)}")
        n = 0
        for i, (x, y) in enumerate(zip(m, theirs)):
            for j, (cx, cy) in enumerate(zip(x, y)):
                if j < {"criteria condensed": 1, "criteria raw": 1, "reported sets": 3, "tail eval": 1, "tail former": 1, "amplitudes": 2, "training": 1, "tested": 2}.get(key, 2):
                    if cx != cy:
                        bad.append(f"label row {i}: document '{cy}', auditor '{cx}'")
                    continue
                if cx == "" and cy == "":
                    continue
                n += 1
                if cx.replace("-0.0%", "+0.0%") != cy.replace("-0.0%", "+0.0%"):
                    bad.append(f"row {i} column {j}: document '{cy}', auditor '{cx}'")
        res[key] = {"cells": n, "differing": bad}
        total += n; wrong += len(bad)
    res["total_cells"] = total; res["differing_cells"] = wrong
    res["yield_counts"] = mine["yield counts"]
    res["mine"] = mine
    if a.out:
        open(a.out, "w").write(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "mine"}, indent=1))


if __name__ == "__main__":
    main()
