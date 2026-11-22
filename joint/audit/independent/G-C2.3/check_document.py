# Independent audit of gate G-C2.3: the generated tables of the verdict document against the returned records.
#
# What it checks. It parses the Markdown tables of the part "Numbers" of docs/G-C2.3_verdict.md and derives every
# cell that it can again from the returned files, with the auditor's own code: the two rows files, the manifest,
# the configuration, the amplitude records, the histories of this gate and of the base gate, and the ledger. A
# numeric cell counts as equal when the auditor's value, rounded to the digits that the document prints, is the
# printed one (half a unit of the last digit, with a slack of 1e-9 relative for values that sit on a rounding
# boundary); a word or a count must be the same. The script prints, for each table, the number of cells derived
# again and the cells that do not match. The tables of the author's own recomputation are not derived here.
#
# Usage: python -I check_document.py <verdict document> <unpacked return package (gate3_records)>
#            <records of the base gate (records/c22/return)> <summary.json> [<replacements.json>]
# With the optional last argument, a JSON object {"arm|reading|seed|member|level index": signed error}, the named
# rows take the given errors before the cells are derived: the cells that then do not match are the printed
# figures that contain those rows.
import json
import math
import os
import re
import sys

SEEDS = ("5", "6", "7")
ARMS = ("label_free", "supervised_512")
ARM_NAME = {"label_free": "label-free", "supervised_512": "supervised"}
READINGS = ("condensed", "raw")
SETS = ("third", "eval", "tested")
SET_NAME = {"third": "third sample", "eval": "fresh members of G-C2.2", "tested": "tested"}
LEVELS = (0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0)
NUM = re.compile(r"[+-]?(?:\d[\d,]*\.?\d*(?:e[+-]?\d+)?|infinite|n/a)")


def q(values, p):
    s = sorted(values)
    h = (len(s) - 1) * p
    lo = int(math.floor(h))
    hi = min(lo + 1, len(s) - 1)
    t = h - lo
    if t == 0:
        return s[lo]
    if math.isinf(s[hi]):
        return s[hi]
    return s[lo] + (s[hi] - s[lo]) * t


def med3(v):
    return sorted(v)[1]


def auc(score, positive):
    pos = [s for s, p in zip(score, positive) if p]
    neg = [s for s, p in zip(score, positive) if not p]
    if not pos or not neg:
        return None
    tot = 0.0
    for a in pos:
        for b in neg:
            tot += 1.0 if a > b else (0.5 if a == b else 0.0)
    return tot / (len(pos) * len(neg))


class Checker:
    def __init__(self):
        self.cells = 0
        self.words = 0
        self.bad = []
        self.by_table = {}
        self.table = ""

    def start(self, name):
        self.table = name
        self.by_table[name] = [0, 0]

    def _count(self, ok, where, shown, mine):
        self.cells += 1
        self.by_table[self.table][0] += 1
        if not ok:
            self.by_table[self.table][1] += 1
            self.bad.append([self.table, where, shown, repr(mine)])

    def text(self, where, shown, mine):
        self.words += 1
        self._count(shown.strip() == str(mine).strip(), where, shown, mine)

    def numbers(self, where, shown, mine, scale=1.0):
        """shown: the cell's text; mine: a value or a list of values (None for n/a, inf for infinite)."""
        mine = list(mine) if isinstance(mine, (list, tuple)) else [mine]
        toks = [t for t in NUM.findall(shown)]
        ok = len(toks) == len(mine)
        if ok:
            for t, v in zip(toks, mine):
                if t == "n/a":
                    ok &= v is None or (isinstance(v, float) and math.isnan(v))
                elif t.lstrip("+-") == "infinite":
                    ok &= v is not None and math.isinf(v)
                else:
                    if v is None or math.isinf(v) or math.isnan(v):
                        ok = False
                        continue
                    tt = t.replace(",", "")
                    val = float(tt)
                    mant = tt.lower().split("e")[0]
                    dec = len(mant.split(".")[1]) if "." in mant else 0
                    unit = 10.0 ** (-dec)
                    if "e" in tt.lower():
                        unit *= 10.0 ** int(tt.lower().split("e")[1])
                    x = v * scale
                    ok &= abs(x - val) <= 0.5 * unit + 1e-9 * max(abs(x), unit)
                    if t[0] in "+-" and x != 0 and round(x / unit) != 0:
                        ok &= (t[0] == "-") == (x < 0)
        self._count(ok, where, shown, mine)


def tables(text):
    """name of the heading or bold line before a table -> list of tables (header cells, rows of cells)."""
    out, lines, i, last = [], text.splitlines(), 0, ""
    while i < len(lines):
        l = lines[i]
        if l.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[-| ]+\|$", lines[i + 1]):
            head = [c.strip() for c in l.strip().strip("|").split("|")]
            rows, j = [], i + 2
            while j < len(lines) and lines[j].startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            out.append((last, head, rows))
            i = j
            continue
        if l.strip():
            last = l.strip()
        i += 1
    return out


def main():
    docp, R, base, outp = sys.argv[1:5]
    doc = open(docp, encoding="utf-8").read()
    numbers = doc[doc.index("## Numbers"):]
    J = lambda p: json.load(open(os.path.join(R, p), encoding="utf-8"))  # noqa: E731
    rf = {a: J(f"rows_{a}.json") for a in ARMS}
    cfg, man, led = J("c23_config.json"), J("manifest.json"), J("ledger.json")
    if len(sys.argv) > 5:                   # optional: other values for chosen rows, to list the cells that hold them
        for key, val in json.load(open(sys.argv[5], encoding="utf-8")).items():
            arm, rd, sd, mm, lv = key.split("|")
            for st in SETS:
                rr = rf[arm]["readings"][rd][sd][f"{st}_rows"]
                if mm in rr:
                    rr[mm][int(lv)].update(curve_err=val, abs_curve_err=abs(val), curve_note="")
    prm = {r["id"]: r["params"] for r in man["instances"]}
    thr = cfg["self_check"]["threshold"]

    def rows(arm, rd, seed, s):
        return rf[arm]["readings"][rd][seed][f"{s}_rows"]

    def members(s):
        return sorted(rows("label_free", "condensed", "5", s))

    def errs(arm, rd, seed, s, level=None, key="curve_err", absolute=True):
        r = rows(arm, rd, seed, s)
        return [(abs(r[m][l][key]) if absolute else r[m][l][key]) for m in members(s) for l in range(7)
                if level is None or l == level]

    def block(arm, rd, s):
        ms = members(s)
        pairs = [(m, l) for m in ms for l in range(7)]
        sp, fl = {}, {}
        for m, l in pairs:
            F = [rows(arm, rd, sd, s)[m][l]["F"] for sd in SEEDS]
            d = abs(med3(F))
            sp[(m, l)] = (max(F) - min(F)) / d if d > 0 else float("inf")
            fl[(m, l)] = sp[(m, l)] >= thr
        e = {sd: {(m, l): abs(rows(arm, rd, sd, s)[m][l]["curve_err"]) for m, l in pairs} for sd in SEEDS}
        nf = [p for p in pairs if not fl[p]]
        b = {"pairs": pairs, "spread": sp, "flag": fl, "err": e, "nf": nf,
             "flagged": sum(fl.values()),
             "nf10": sum(1 for p in nf if any(e[sd][p] > 0.10 for sd in SEEDS)),
             "nf05": sum(1 for p in nf for sd in SEEDS if e[sd][p] > 0.05), "nfread": 3 * len(nf)}
        b["S1"], b["S2"], b["S3"] = b["nf10"] == 0, (b["nf05"] / b["nfread"] if b["nfread"] else 0) <= 0.01, b["flagged"] / len(pairs) <= 0.35
        b["auc05"] = [auc([sp[p] for p in pairs], [e[sd][p] > 0.05 for p in pairs]) for sd in SEEDS]
        b["auc10"] = [auc([sp[p] for p in pairs], [e[sd][p] > 0.10 for p in pairs]) for sd in SEEDS]
        have = [a for a in b["auc05"] if a is not None]
        b["R"] = "NOT EVALUABLE" if not have else ("HOLDS" if min(have) >= 0.90 else "DOES NOT HOLD")
        return b

    C = Checker()
    T = tables(numbers)
    by_head = {}
    for last, head, rws in T:
        by_head.setdefault(head[0] + "|" + head[1] + "|" + str(len(head)), []).append((last, head, rws))

    def find(first, second, n, k=0):
        return by_head[f"{first}|{second}|{n}"][k]

    J3 = block("label_free", "condensed", "third")
    # --- the criteria
    C.start("part 1: criteria")
    _, _, rws = find("Criterion", "Limit", 4)
    C.numbers("S1", rws[0][2], J3["nf10"]); C.text("S1 holds", rws[0][3], "yes" if J3["S1"] else "no")
    C.numbers("S2", rws[1][2], [J3["nf05"], J3["nfread"], 100 * J3["nf05"] / J3["nfread"]]); C.text("S2 holds", rws[1][3], "yes" if J3["S2"] else "no")
    C.numbers("S3", rws[2][2], [J3["flagged"], 448, 100 * J3["flagged"] / 448]); C.text("S3 holds", rws[2][3], "yes" if J3["S3"] else "no")
    C.numbers("R", rws[3][2], J3["auc05"]); C.text("R word", rws[3][3], J3["R"])
    # --- the runs of part 1
    C.start("part 1: runs")
    _, _, rws = find("Run", "Median", 10)
    for i, sd in enumerate(SEEDS):
        e = [J3["err"][sd][p] for p in J3["pairs"]]
        fl = [J3["flag"][p] for p in J3["pairs"]]
        r = rws[i]
        C.text("run", r[0], f"label-free, seed {sd}")
        C.numbers("median", r[1], q(e, 0.5), 100); C.numbers("p90", r[2], q(e, 0.9), 100); C.numbers("largest", r[3], max(e), 100)
        C.numbers("above 5%", r[4], sum(x > 0.05 for x in e)); C.numbers("flagged", r[5], sum(x > 0.05 and f for x, f in zip(e, fl)))
        C.numbers("above 10%", r[6], sum(x > 0.10 for x in e)); C.numbers("flagged", r[7], sum(x > 0.10 and f for x, f in zip(e, fl)))
        C.numbers("largest not flagged", r[8], max(x for x, f in zip(e, fl) if not f), 100)
        C.numbers("infinite", r[9], sum(math.isinf(x) for x in e))
    m = re.search(r"The spread over the 448 pairs: median (\S+), upper quartile (\S+), 90th percentile (\S+), largest (\S+)\. "
                  r"The probability that a pair above 10% has a larger spread than a pair at or below 10%: (\S+), (\S+), (\S+) \(reported\)", numbers)
    spv = [J3["spread"][p] for p in J3["pairs"]]
    C.start("part 1: spread line")
    for k, v in enumerate([q(spv, 0.5), q(spv, 0.75), q(spv, 0.9), max(spv)] + J3["auc10"]):
        C.numbers(f"value {k}", m.group(k + 1).rstrip(".,"), v)
    # --- by level
    C.start("part 1: by level")
    _, _, rws = find("Level", "Pairs flagged", 7)
    for l in range(7):
        ps = [p for p in J3["pairs"] if p[1] == l]
        a5 = [p for p in ps if any(J3["err"][sd][p] > 0.05 for sd in SEEDS)]
        a10 = [p for p in ps if any(J3["err"][sd][p] > 0.10 for sd in SEEDS)]
        r = rws[l]
        C.numbers("level", r[0], LEVELS[l])
        C.numbers("flagged", r[1], [sum(J3["flag"][p] for p in ps), len(ps)])
        C.numbers("above 5%", r[2], len(a5)); C.numbers("flagged", r[3], sum(J3["flag"][p] for p in a5))
        C.numbers("above 10%", r[4], len(a10)); C.numbers("flagged", r[5], sum(J3["flag"][p] for p in a10))
        C.numbers("median spread", r[6], q([J3["spread"][p] for p in ps], 0.5))
    # --- the pairs above 5%
    C.start("part 1: pairs above 5% in some run")
    _, _, rws = find("Member", "$t_f$ (mm)", 9)
    want = [p for p in J3["pairs"] if any(J3["err"][sd][p] > 0.05 for sd in SEEDS)]
    C.numbers("number of rows", str(len(rws)), len(want))
    for r, p in zip(rws, want):
        mm, l = p
        C.text("member", r[0], mm)
        C.numbers("t_f", r[1], prm[mm]["t_f"]); C.numbers("f_y", r[2], prm[mm]["fy"]); C.numbers("w", r[3], prm[mm]["w"]); C.numbers("n", r[4], prm[mm]["n"])
        C.numbers("level", r[5], LEVELS[l])
        C.numbers("errors", r[6], [rows("label_free", "condensed", sd, "third")[mm][l]["curve_err"] for sd in SEEDS], 100)
        C.numbers("spread", r[7], J3["spread"][p]); C.text("flagged", r[8], "yes" if J3["flag"][p] else "no")
    m = re.search(r"\n(\d+) pairs, (\d+) of them not flagged\.", numbers)
    C.numbers("count line", m.group(1), len(want)); C.numbers("count line", m.group(2), sum(not J3["flag"][p] for p in want))
    # --- part 1 on the other blocks
    C.start("part 1 on the other sets and readings")
    _, _, rws = find("Arm", "Reading", 10)
    k = 0
    blocks = {}
    for arm in ARMS:
        for rd in READINGS:
            for s in SETS:
                b = blocks[(arm, rd, s)] = block(arm, rd, s)
                r = rws[k]; k += 1
                C.text("arm", r[0], ARM_NAME[arm]); C.text("reading", r[1], rd); C.text("set", r[2], SET_NAME[s])
                C.numbers("flagged", r[3], [b["flagged"], len(b["pairs"])]); C.numbers("nf10", r[4], b["nf10"])
                C.numbers("nf05", r[5], [b["nf05"], b["nfread"]])
                C.text("S", r[6], ", ".join("holds" if x else "fails" for x in (b["S1"], b["S2"], b["S3"])))
                C.text("would read", r[7], "PASS" if b["S1"] and b["S2"] and b["S3"] else "FAIL")
                C.numbers("auc", r[8], b["auc05"]); C.text("ranking", r[9], b["R"])
    # --- part 2 statistics
    stat = {}
    for si, s in enumerate(SETS):
        C.start(f"part 2: statistics, {SET_NAME[s]}")
        _, _, rws = find("Arm", "Reading", 8, si)
        k = 0
        for arm in ARMS:
            for rd in READINGS:
                e = {sd: errs(arm, rd, sd, s) for sd in SEEDS}
                med = [q(e[sd], 0.5) for sd in SEEDS]; p90 = [q(e[sd], 0.9) for sd in SEEDS]
                stat[(arm, rd, s)] = (med3(med), med3(p90))
                r = rws[k]; k += 1
                C.text("arm", r[0], ARM_NAME[arm]); C.text("reading", r[1], rd)
                C.numbers("medians", r[2], med, 100); C.numbers("median over seeds", r[3], med3(med), 100)
                C.numbers("p90", r[4], p90, 100); C.numbers("p90 over seeds", r[5], med3(p90), 100)
                C.numbers("above 10%", r[6], [sum(x > 0.10 for x in e[sd]) for sd in SEEDS])
                C.numbers("infinite", r[7], sum(math.isinf(x) for sd in SEEDS for x in e[sd]))
    # --- ratios
    C.start("part 2: ratios")
    _, _, rws = find("Set", "Supervised arm read", 6)

    def word(a, b):
        lo, hi = 2 / 3, 1.5
        if lo <= a <= hi and lo <= b <= hi:
            return "comparable"
        if a < 1 and b < 1:
            return "supervised closer"
        if a > 1 and b > 1:
            return "label-free closer"
        return "mixed"
    spec = [("third", "condensed", "condensed"), ("third", "raw", "condensed"), ("third", "raw", "raw"), ("eval", "condensed", "condensed"),
            ("eval", "raw", "raw"), ("tested", "condensed", "condensed"), ("tested", "raw", "raw")]
    for r, (s, a, b) in zip(rws, spec):
        r1 = stat[("supervised_512", a, s)][0] / stat[("label_free", b, s)][0]
        r2 = stat[("supervised_512", a, s)][1] / stat[("label_free", b, s)][1]
        C.text("set", r[0].split(" (")[0], SET_NAME[s]); C.text("sup", r[1], a); C.text("lf", r[2], b)
        C.numbers("ratio medians", r[3], r1); C.numbers("ratio p90", r[4], r2); C.text("wording", r[5], word(r1, r2))
    C.numbers("number of rows", str(len(rws)), len(spec))
    # --- by level: median, p90, signed median
    for name, first, fn, signed, with_runs in (("median error by level", 0, lambda v: q(v, 0.5), False, True),
                                               ("90th percentile by level", 1, lambda v: q(v, 0.9), False, False),
                                               ("median signed error by level", 2, lambda v: q(v, 0.5), True, False)):
        C.start(name)
        _, _, rws = find("Arm", "Reading", 10, first + 1)
        k = 0
        for arm in ARMS:
            for rd in READINGS:
                per = []
                for sd in SEEDS:
                    vals = [fn(errs(arm, rd, sd, "third", level=l, absolute=not signed)) for l in range(7)]
                    per.append(vals)
                    r = rws[k]; k += 1
                    C.text("arm", r[0], ARM_NAME[arm]); C.text("reading", r[1], rd); C.text("run", r[2], f"seed {sd}")
                    for l in range(7):
                        C.numbers(f"level {l}", r[3 + l], vals[l], 100)
                if with_runs:
                    r = rws[k]; k += 1
                    C.text("run", r[2], "**median of the runs**")
                    for l in range(7):
                        C.numbers(f"level {l}", r[3 + l], med3([per[i][l] for i in range(3)]), 100)
        C.numbers("number of rows", str(len(rws)), k)
    # --- identity
    C.start("identity")
    _, _, rws = find("Reading", "Seed", 6)
    k = 0
    for rd in READINGS:
        for i, sd in enumerate(SEEDS):
            e = errs("label_free", rd, sd, "eval")
            w = cfg["arms"]["label_free"]["identity"]["values"][rd]
            r = rws[k]; k += 1
            C.text("reading", r[0], rd); C.text("seed", r[1], sd)
            C.text("median here", r[2], repr(q(e, 0.5))); C.text("median pinned", r[3], repr(w["abs_curve_err_median"][i]))
            C.text("p90 here", r[4], repr(q(e, 0.9))); C.text("p90 pinned", r[5], repr(w["abs_curve_err_p90"][i]))
    # --- what each arm needed
    C.start("what each arm needed")
    _, _, rws = find("Run", "Reference solutions for training", 6)
    k = 0
    for arm in ARMS:
        for sd in SEEDS:
            h = J(f"run_files/{arm}_s{sd}/history.json")
            r = rws[k]; k += 1
            if arm == "label_free":
                hb = json.load(open(os.path.join(base, f"run_files/label_free_s{sd}/history.json"), encoding="utf-8"))
                C.numbers("solutions", r[1], 0); C.numbers("hours", r[2], sum(hb["epoch_seconds"]) / 3600)
                C.numbers("steps", r[3], hb["steps"]); C.numbers("peak", r[4], hb["peak_memory_GiB"]); C.numbers("predict", r[5], h["predict_seconds"])
            else:
                C.numbers("solutions", r[1], h["reference_solutions"]); C.numbers("hours", r[2], sum(h["epoch_seconds"]) / 3600)
                C.numbers("steps", r[3], h["steps"]); C.numbers("peak", r[4], h["peak_memory_GiB"]); C.text("predict", r[5], "not recorded")
    split = {r["id"]: r["split"] for r in man["instances"]}
    tr = [e for e in led if split[e["id"]] == "train"]
    m = re.search(r"The ([\d,]+) reference solutions of the (\d+) training members, which the three supervised runs share, took ([\d,]+) seconds "
                  r"summed over the worker processes \(([\d.]+) processor hours\)", numbers)
    secs = sum(e["seconds"] for e in tr)
    C.numbers("solutions", m.group(1), sum(len(e["levels"]) for e in tr)); C.numbers("members", m.group(2), len(tr))
    C.numbers("seconds", m.group(3), secs); C.numbers("hours", m.group(4), secs / 3600)
    # --- amplitudes
    C.start("amplitudes")
    _, _, rws = find("Run", "Set", 10)
    k = 0
    for arm in ARMS:
        for sd in SEEDS:
            c = J(f"run_files/{arm}_s{sd}/condense.json")
            lo, hi = c["reading"]["a_min"], c["reading"]["a_max"]
            for s in SETS:
                a, conv, fall = [], [], []
                for mm in members(s):
                    x = c["members"][mm]
                    a += x["a"]; conv += x["converged"]
                    fall += [(pr - pc) / pr for pr, pc in zip(x["Pi_raw"], x["Pi_condensed"])]
                r = rws[k]; k += 1
                C.text("run", r[0], f"{ARM_NAME[arm]}, seed {sd}"); C.text("set", r[1], SET_NAME[s])
                C.numbers("fields", r[2], len(a)); C.numbers("smallest", r[3], min(a)); C.numbers("median", r[4], q(a, 0.5)); C.numbers("largest", r[5], max(a))
                C.numbers("at lower", r[6], sum(v <= lo for v in a)); C.numbers("at upper", r[7], sum(v >= hi for v in a))
                C.numbers("tolerance not met", r[8], sum(not v for v in conv)); C.numbers("fall", r[9], q(fall, 0.5), 100)
    # --- supervised training
    C.start("supervised training")
    _, _, rws = find("Run", "Loss, first epoch", 10)
    for r, sd in zip(rws, SEEDS):
        h = J(f"run_files/supervised_512_s{sd}/history.json")
        es = h["epoch_seconds"]
        C.numbers("first", r[1], h["loss"][0]); C.numbers("mean last ten", r[2], sum(h["loss"][190:200]) / 10); C.numbers("largest", r[3], max(h["loss"]))
        C.numbers("capped", r[4], len(h["cap_events"])); C.numbers("bursts", r[5], len(h["bursts"])); C.numbers("hours", r[6], sum(es) / 3600)
        C.numbers("step seconds", r[7], [min(es) / 512, q(es, 0.5) / 512, max(es) / 512])
        C.text("resumed", r[8], "none" if h["resumed_from_epoch"] is None else str(h["resumed_from_epoch"]))
        C.text("ledger hash", r[9], "`" + h["training_labels_sha256"][:12] + "`")
    # --- the other readings
    keys = ("abs_F_err", "F_err", "e_err", "F_sigma_err", "gap", "bound", "bolt_err", "u_rel_l2")
    for si, s in enumerate(("third", "eval")):
        C.start(f"other readings, {SET_NAME[s]}")
        _, _, rws = find("Arm", "Reading", 14, si)
        k = 0
        for arm in ARMS:
            for rd in READINGS:
                for sd in SEEDS:
                    g = [x for mm in members(s) for x in rows(arm, rd, sd, s)[mm]]
                    r = rws[k]; k += 1
                    C.text("arm", r[0], ARM_NAME[arm]); C.text("reading", r[1], rd); C.text("seed", r[2], sd)
                    for j, key in enumerate(keys):
                        C.numbers(key, r[3 + j], q([x[key] for x in g], 0.5), 100)
                    C.numbers("iou contact", r[11], q([x["iou_contact"] for x in g], 0.5)); C.numbers("iou plastic", r[12], q([x["iou_plastic"] for x in g], 0.5))
                    C.numbers("within", r[13], sum(bool(x["within_bound"]) for x in g) / len(g), 100)
    C.start("other readings by level, third sample")
    _, _, rws = find("Arm", "Reading", 15)
    k = 0
    for arm in ARMS:
        for rd in READINGS:
            for sd in SEEDS:
                for l in range(7):
                    g = [rows(arm, rd, sd, "third")[mm][l] for mm in members("third")]
                    md = lambda key: q([x[key] for x in g], 0.5)  # noqa: E731
                    r = rws[k]; k += 1
                    C.text("arm", r[0], ARM_NAME[arm]); C.text("reading", r[1], rd); C.text("seed", r[2], sd); C.numbers("D", r[3], LEVELS[l])
                    C.numbers("F_err", r[4], md("F_err"), 100); C.numbers("abs", r[5], md("abs_F_err"), 100); C.numbers("bound", r[6], md("bound"), 100)
                    C.numbers("within", r[7], [sum(bool(x["within_bound"]) for x in g), len(g)])
                    C.numbers("e_err", r[8], md("e_err"), 100); C.numbers("F_sigma", r[9], md("F_sigma_err"), 100); C.numbers("gap", r[10], md("gap"), 100)
                    C.numbers("iou c", r[11], md("iou_contact")); C.numbers("iou p", r[12], md("iou_plastic"))
                    C.numbers("bolt", r[13], md("bolt_err"), 100); C.numbers("u", r[14], md("u_rel_l2"), 100)
    C.numbers("number of rows", str(len(rws)), k)
    # --- infinite rows
    C.start("rows with an infinite error")
    _, _, rws = find("Arm", "Reading", 7)
    inf = [(arm, rd, sd, s, mm, l, rows(arm, rd, sd, s)[mm][l]["curve_note"]) for arm in ARMS for rd in READINGS for sd in SEEDS for s in SETS
           for mm in members(s) for l in range(7) if math.isinf(rows(arm, rd, sd, s)[mm][l]["curve_err"])]
    C.numbers("number of rows", str(len(rws)), len(inf))
    for r, (arm, rd, sd, s, mm, l, note) in zip(rws, inf):
        C.text("arm", r[0], ARM_NAME[arm]); C.text("reading", r[1], rd); C.text("seed", r[2], sd); C.text("set", r[3], SET_NAME[s])
        C.text("member", r[4], mm); C.numbers("level", r[5], LEVELS[l]); C.text("note", r[6], note)
    m = re.search(r"Of the ([\d,]+) returned rows, (\d+) have an infinite error and (\d+) a field", numbers)
    n_all = sum(len(rows(arm, rd, sd, s)[mm]) for arm in ARMS for rd in READINGS for sd in SEEDS for s in SETS for mm in members(s))
    n_fail = sum(bool(x["evaluate_failed"]) for arm in ARMS for rd in READINGS for sd in SEEDS for s in SETS for mm in members(s) for x in rows(arm, rd, sd, s)[mm])
    C.numbers("rows", m.group(1), n_all); C.numbers("infinite", m.group(2), len(inf)); C.numbers("failed", m.group(3), n_fail)
    # --- tested members
    C.start("tested members")
    _, _, rws = find("Member", "Arm", 10)
    k = 0
    for mm in members("tested"):
        for arm in ARMS:
            for rd in READINGS:
                r = rws[k]; k += 1
                C.text("member", r[0], mm.replace("tested_", "")); C.text("arm", r[1], ARM_NAME[arm]); C.text("reading", r[2], rd)
                for l in range(7):
                    C.numbers(f"level {l}", r[3 + l], [rows(arm, rd, sd, "tested")[mm][l]["curve_err"] for sd in SEEDS], 100)
    print("tables found in the part Numbers:", len(T))
    for name, (n, b) in C.by_table.items():
        print(f"  {name}: {n} cells derived again, {b} not matching")
    print("cells derived again:", C.cells, "(numbers and counts:", C.cells - C.words, ", words and names:", C.words, ") | not matching:", len(C.bad))
    for b in C.bad[:60]:
        print("  NOT MATCHING:", b)
    json.dump({"cells": C.cells, "words_and_names": C.words, "not_matching": C.bad, "by_table": C.by_table}, open(outp, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
