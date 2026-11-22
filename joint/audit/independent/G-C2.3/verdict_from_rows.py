# Independent audit of gate G-C2.3: the verdict from the returned per-pair rows, with code of the auditor's own.
#
# What it checks. From rows_label_free.json and rows_supervised_512.json of the return package (the per-pair
# metrics that the stamped evaluation wrote) it computes, without importing any code of the repository:
#   - every run's median and 90th percentile of the judged error, for both arms, both readings and the three sets,
#     their medians over the seeds, and the ratios and the wording of part 2 (judged, stated beside it, reported);
#   - the spread of the predicted force over the three runs, the flags, S1, S2, S3 and the ranking R of part 1,
#     on the judged block and on every reported block;
#   - the identity values against those pinned in the returned configuration;
#   - the median error by level.
# It compares each of them with verdict.json and with verdict_part1.json and prints every difference it finds.
# The hashes that the verdict records for the rows files and the manifest are those of the host's files, with
# CR LF line ends; the script accepts the files with these or with LF line ends and says which it found.
# The auditor's own results are written to a JSON file for the other scripts.
#
# Usage: python -I verdict_from_rows.py <folder with the rows files, verdict.json, verdict_part1.json and
#            c23_config.json> <output json>
import hashlib
import json
import math
import sys

INF = float("inf")
SEEDS = ("5", "6", "7")
ARMS = ("label_free", "supervised_512")
READINGS = ("condensed", "raw")
SETS = ("third", "eval", "tested")


def quantile(values, q):
    """Linear interpolation between order statistics; infinite when an infinite one has a positive weight."""
    s = sorted(values)
    h = (len(s) - 1) * q
    lo = int(math.floor(h))
    hi = min(lo + 1, len(s) - 1)
    t = h - lo
    a, b = s[lo], s[hi]
    if (math.isinf(a) and 1 - t > 0) or (math.isinf(b) and t > 0):
        return a if math.isinf(a) and 1 - t > 0 else b
    if t == 0:
        return a
    return a + (b - a) * t


def median3(v):
    return sorted(v)[1]


def auc(score, positive):
    """P(a positive pair has the larger score than a negative one), ties counting half; by direct counting."""
    pos = [s for s, p in zip(score, positive) if p]
    neg = [s for s, p in zip(score, positive) if not p]
    if not pos or not neg:
        return None
    neg_sorted = sorted(neg)
    import bisect
    total = 0.0
    for s in pos:
        below = bisect.bisect_left(neg_sorted, s)
        equal = bisect.bisect_right(neg_sorted, s) - below
        total += below + 0.5 * equal
    return total / (len(pos) * len(neg))


def self_check(rows_by_seed, members, threshold):
    """rows_by_seed: seed -> member -> list of rows (one a level)."""
    pairs = [(m, l) for m in members for l in range(len(rows_by_seed[SEEDS[0]][m]))]
    spread, flag, errs = [], [], {s: [] for s in SEEDS}
    for m, l in pairs:
        F = [rows_by_seed[s][m][l]["F"] for s in SEEDS]
        med = abs(median3(F))
        sp = (max(F) - min(F)) / med if med > 0 else INF
        spread.append(sp)
        flag.append(sp >= threshold)
        for s in SEEDS:
            errs[s].append(rows_by_seed[s][m][l]["abs_curve_err"])
    n = len(pairs)
    nf = [i for i in range(n) if not flag[i]]
    above10 = sum(1 for i in nf if any(errs[s][i] > 0.10 for s in SEEDS))
    readings = len(nf) * len(SEEDS)
    above05 = sum(1 for i in nf for s in SEEDS if errs[s][i] > 0.05)
    share05 = above05 / readings if readings else 0.0
    S1, S2, S3 = above10 == 0, share05 <= 0.01, sum(flag) / n <= 0.35
    aucs05 = [auc(spread, [e > 0.05 for e in errs[s]]) for s in SEEDS]
    aucs10 = [auc(spread, [e > 0.10 for e in errs[s]]) for s in SEEDS]
    have = [a for a in aucs05 if a is not None]
    R = "NOT EVALUABLE" if not have else ("HOLDS" if min(have) >= 0.90 else "DOES NOT HOLD")
    fin = sorted(v for v in spread if math.isfinite(v))
    return {"pairs": n, "flagged": sum(flag), "flagged_share": sum(flag) / n,
            "not_flagged_pairs_above_0.10_in_any_run": above10, "not_flagged_readings": readings,
            "not_flagged_readings_above_0.05": above05, "not_flagged_share_above_0.05": share05,
            "largest_error_not_flagged": [max((errs[s][i] for i in nf), default=None) for s in SEEDS],
            "pairs_above": {t: {"total": [sum(1 for e in errs[s] if e > float(t)) for s in SEEDS],
                                "flagged": [sum(1 for i, e in enumerate(errs[s]) if e > float(t) and flag[i])
                                            for s in SEEDS]} for t in ("0.05", "0.1")},
            "spread_quantiles": {q: quantile(fin, float(q)) for q in ("0.5", "0.75", "0.9")} if fin else {},
            "spread_max": max(spread), "S1": S1, "S2": S2, "S3": S3,
            "verdict": "PASS" if (S1 and S2 and S3) else "FAIL",
            "ranking": {"auc_above_0.05": aucs05, "auc_above_0.10": aucs10, "R": R},
            "spread": {f"{m}|{l}": sp for (m, l), sp in zip(pairs, spread)},
            "flag": {f"{m}|{l}": f for (m, l), f in zip(pairs, flag)}}


def wording(r_med, r_p90, lo=2.0 / 3.0, hi=1.5):
    r = (r_med, r_p90)
    if any(math.isnan(x) for x in r):
        return "NOT COMPARABLE"
    if all(lo <= x <= hi for x in r):
        return "comparable"
    if all(x < 1 for x in r) and any(x < lo for x in r):
        return "supervised closer"
    if all(x > 1 for x in r) and any(x > hi for x in r):
        return "label-free closer"
    return "mixed"


def ratio(a, b):
    if math.isinf(a) and math.isinf(b):
        return float("nan")
    if b == 0:
        return INF if a > 0 else float("nan")
    return a / b


def close(a, b, rel=1e-12):
    if a is None or b is None:
        return a is b
    if isinstance(a, bool) or isinstance(b, bool) or isinstance(a, str) or isinstance(b, str):
        return a == b
    if math.isinf(a) or math.isinf(b):
        return a == b
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-300)


def main():
    folder, outp = sys.argv[1], sys.argv[2]
    load = lambda name: json.load(open(f"{folder}/{name}", encoding="utf-8"))  # noqa: E731
    rows = {"label_free": load("rows_label_free.json"), "supervised_512": load("rows_supervised_512.json")}
    V, V1, cfg = load("verdict.json"), load("verdict_part1.json"), load("c23_config.json")
    sha = lambda name: hashlib.sha256(open(f"{folder}/{name}", "rb").read()).hexdigest()  # noqa: E731
    threshold = cfg["self_check"]["threshold"]
    diffs, checked = [], 0
    worst = 0.0

    def cmp(what, mine, theirs, rel=1e-12):
        nonlocal checked, worst
        checked += 1
        if isinstance(mine, float) and isinstance(theirs, (int, float)) and not isinstance(theirs, bool) \
                and math.isfinite(mine) and math.isfinite(theirs) and theirs != 0:
            worst = max(worst, abs(mine - theirs) / abs(theirs))
        if not close(mine, theirs, rel):
            diffs.append((what, mine, theirs))

    out = {"statistics": {}, "self_check": {}, "comparison": {}, "by_level": {}, "counts": {}}
    members = {s: sorted(rows["label_free"]["readings"]["condensed"]["5"][f"{s}_rows"]) for s in SETS}
    out["members"] = {s: len(members[s]) for s in SETS}
    n_inf, n_rows, n_failed, notes = 0, 0, 0, []
    for arm in ARMS:
        out["statistics"][arm], out["by_level"][arm] = {}, {}
        for rd in READINGS:
            out["statistics"][arm][rd], out["by_level"][arm][rd] = {}, {}
            for st in SETS:
                med, p90, above10, ninf, largest = [], [], [], [], []
                for seed in SEEDS:
                    rr = rows[arm]["readings"][rd][seed][f"{st}_rows"]
                    assert sorted(rr) == members[st], (arm, rd, seed, st)
                    errs = [r["abs_curve_err"] for m in members[st] for r in rr[m]]
                    for m in members[st]:
                        for l, r in enumerate(rr[m]):
                            n_rows += 1
                            assert r["abs_curve_err"] == abs(r["curve_err"])
                            if math.isinf(r["curve_err"]):
                                n_inf += 1
                                notes.append([arm, rd, seed, st, m, r["D"], r["curve_note"]])
                            if r["evaluate_failed"]:
                                n_failed += 1
                    med.append(quantile(errs, 0.5)); p90.append(quantile(errs, 0.9))
                    above10.append(sum(1 for e in errs if e > 0.10))
                    ninf.append(sum(1 for e in errs if math.isinf(e)))
                    largest.append(max(errs))
                    summ = rows[arm]["readings"][rd][seed][st]["abs_curve_err"]
                    cmp(f"rows summary median {arm} {rd} {seed} {st}", med[-1], summ["median"])
                    cmp(f"rows summary p90 {arm} {rd} {seed} {st}", p90[-1], summ["p90"])
                mine = {"median": med, "p90": p90, "C1": median3(med), "C2": median3(p90), "above10": above10,
                        "infinite": ninf, "largest": largest}
                out["statistics"][arm][rd][st] = mine
                theirs = V["statistics"][arm][rd][st]
                for i in range(3):
                    cmp(f"median {arm} {rd} {st} seed {SEEDS[i]}", med[i], theirs["per_seed"]["abs_curve_err_median"][i])
                    cmp(f"p90 {arm} {rd} {st} seed {SEEDS[i]}", p90[i], theirs["per_seed"]["abs_curve_err_p90"][i])
                cmp(f"C1 {arm} {rd} {st}", mine["C1"], theirs["C1_value"])
                cmp(f"C2 {arm} {rd} {st}", mine["C2"], theirs["C2_value"])
                # the median error by level
                nl = len(rows[arm]["readings"][rd]["5"][f"{st}_rows"][members[st][0]])
                per_run = [[quantile([rows[arm]["readings"][rd][seed][f"{st}_rows"][m][l]["abs_curve_err"]
                                      for m in members[st]], 0.5) for l in range(nl)] for seed in SEEDS]
                of_runs = [median3([per_run[i][l] for i in range(3)]) for l in range(nl)]
                out["by_level"][arm][rd][st] = {"median_per_run": per_run, "median_of_runs": of_runs}
                tb = V["by_level"][arm][rd][st]
                for i in range(3):
                    for l in range(nl):
                        cmp(f"by level {arm} {rd} {st} {i} {l}", per_run[i][l], tb["median_per_run"][i][l])
                for l in range(nl):
                    cmp(f"by level, runs {arm} {rd} {st} {l}", of_runs[l], tb["median_of_runs"][l])
                # part 1 on this block
                sc = self_check({seed: rows[arm]["readings"][rd][seed][f"{st}_rows"] for seed in SEEDS},
                                members[st], threshold)
                out["self_check"][f"{arm}|{rd}|{st}"] = sc
                ts = V["self_check_reported"][arm][rd][st]
                for k in ("pairs", "flagged", "flagged_share", "not_flagged_pairs_above_0.10_in_any_run",
                          "not_flagged_readings", "not_flagged_readings_above_0.05", "not_flagged_share_above_0.05",
                          "spread_max", "S1", "S2", "S3", "verdict"):
                    cmp(f"self-check {k} {arm} {rd} {st}", sc[k], ts[k])
                for i in range(3):
                    cmp(f"self-check largest not flagged {arm} {rd} {st} {i}", sc["largest_error_not_flagged"][i],
                        ts["largest_error_not_flagged"][i])
                    cmp(f"auc05 {arm} {rd} {st} {i}", sc["ranking"]["auc_above_0.05"][i],
                        ts["ranking"]["auc_above_0.05"][i])
                    cmp(f"auc10 {arm} {rd} {st} {i}", sc["ranking"]["auc_above_0.10"][i],
                        ts["ranking"]["auc_above_0.10"][i])
                    for t in ("0.05", "0.1"):
                        for kk in ("total", "flagged"):
                            cmp(f"pairs above {t} {kk} {arm} {rd} {st} {i}", sc["pairs_above"][t][kk][i],
                                ts["pairs_above"][t][kk][i])
                cmp(f"R {arm} {rd} {st}", sc["ranking"]["R"], ts["ranking"]["R"])
                for q in ("0.5", "0.75", "0.9"):
                    cmp(f"spread quantile {q} {arm} {rd} {st}", sc["spread_quantiles"].get(q),
                        ts["spread_quantiles"].get(q))
                for m in members[st]:
                    for l in range(nl):
                        cmp(f"spread {arm} {rd} {st} {m} {l}", sc["spread"][f"{m}|{l}"], ts["by_member"][m]["spread"][l])
                        cmp(f"flag {arm} {rd} {st} {m} {l}", sc["flag"][f"{m}|{l}"], ts["by_member"][m]["flagged"][l])
    out["counts"] = {"rows": n_rows, "infinite": n_inf, "evaluate_failed": n_failed, "infinite_rows": notes}

    # part 1, judged block against the verdict's own block and the kept part 1
    judged = out["self_check"]["label_free|condensed|third"]
    for name, v in (("verdict.json", V), ("verdict_part1.json", V1)):
        ts = v["self_check"]
        for k in ("pairs", "flagged", "not_flagged_pairs_above_0.10_in_any_run", "not_flagged_readings",
                  "not_flagged_readings_above_0.05", "S1", "S2", "S3", "verdict"):
            cmp(f"{name} judged self-check {k}", judged[k], ts[k])
        cmp(f"{name} judged R", judged["ranking"]["R"], ts["ranking"]["R"])
        cmp(f"{name} word self_check", judged["verdict"], v["verdict"]["self_check"])
        cmp(f"{name} word ranking", judged["ranking"]["R"], v["verdict"]["ranking"])
    same_part1 = all(V[k] == V1[k] for k in ("identity", "self_check")) and \
        V["inputs"]["label_free"] == V1["inputs"]["label_free"] and \
        V["rows_sha256"]["label_free"] == V1["rows_sha256"]["label_free"] and \
        all(V["verdict"][k] == V1["verdict"][k] for k in ("identity", "self_check", "ranking"))
    out["part1_kept_equals_final"] = same_part1
    out["part1_kept_comparison_word"] = V1["verdict"].get("comparison")
    out["part1_kept_not_evaluated"] = V1.get("not_evaluated")
    out["part1_kept_training_members_labelled"] = V1["cost"]["training_members_labelled"]

    # part 2
    st = out["statistics"]

    def comp(sup_rd, lf_rd, s):
        a, b = st["supervised_512"][sup_rd][s], st["label_free"][lf_rd][s]
        r1, r2 = ratio(a["C1"], b["C1"]), ratio(a["C2"], b["C2"])
        return {"ratio_of_medians": r1, "ratio_of_p90": r2, "wording": wording(r1, r2)}

    out["comparison"]["judged"] = comp("condensed", "condensed", "third")
    out["comparison"]["supervised_raw_over_label_free_condensed"] = comp("raw", "condensed", "third")
    out["comparison"]["reported"] = {rd: {s: comp(rd, rd, s) for s in SETS} for rd in READINGS}
    c = V["comparison"]
    for k in ("ratio_of_medians", "ratio_of_p90", "wording"):
        cmp(f"judged comparison {k}", out["comparison"]["judged"][k], c[k])
        cmp(f"supervised raw over label-free judged {k}",
            out["comparison"]["supervised_raw_over_label_free_condensed"][k],
            c["supervised_raw_against_label_free_judged"]["raw"][k])
        for rd in READINGS:
            for s in SETS:
                cmp(f"reported comparison {rd} {s} {k}", out["comparison"]["reported"][rd][s][k],
                    c["reported"][rd][s][k])
    cmp("word comparison", out["comparison"]["judged"]["wording"], V["verdict"]["comparison"])

    # identity
    want = cfg["arms"]["label_free"]["identity"]["values"]
    worst_id = 0.0
    for rd, w in want.items():
        for k, key in (("abs_curve_err_median", "median"), ("abs_curve_err_p90", "p90")):
            for i in range(3):
                worst_id = max(worst_id, abs(st["label_free"][rd]["eval"][key][i] - w[k][i]))
    out["identity"] = {"largest_difference": worst_id, "tolerance": cfg["arms"]["label_free"]["identity"]["tolerance"],
                       "ok": worst_id <= cfg["arms"]["label_free"]["identity"]["tolerance"]}
    cmp("identity largest difference", out["identity"]["largest_difference"], V["identity"]["largest_difference"])
    cmp("identity ok", out["identity"]["ok"], V["identity"]["ok"])
    cmp("identity word", "OK" if out["identity"]["ok"] else "INVALID", V["verdict"]["identity"])

    # the hashes that the verdict records for its inputs
    out["sha256"] = {n: sha(n) for n in ("verdict.json", "verdict_part1.json", "rows_label_free.json",
                                         "rows_supervised_512.json", "c23_config.json", "manifest.json")}
    # The verdict records the hashes of the files as the host wrote them, with CR LF line ends. The repository keeps
    # the files with LF line ends, so a recorded hash is compared with the file as it is and with the file as it
    # would be with the host's line ends; which of the two forms agrees is reported.

    def host_form(name):
        data = open(f"{folder}/{name}", "rb").read()
        return hashlib.sha256(data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()

    out["sha256_with_host_line_ends"] = {n: host_form(n) for n in ("rows_label_free.json", "rows_supervised_512.json", "manifest.json")}
    forms_seen = set()

    def cmp_hash(what, name, recorded):
        as_is, as_host = out["sha256"][name], out["sha256_with_host_line_ends"][name]
        forms_seen.add("as the file is" if recorded == as_is else ("with the host's line ends" if recorded == as_host else "neither"))
        cmp(what, recorded in (as_is, as_host), True)

    cmp_hash("rows sha label_free", "rows_label_free.json", V["rows_sha256"]["label_free"])
    cmp_hash("rows sha supervised", "rows_supervised_512.json", V["rows_sha256"]["supervised_512"])
    cmp_hash("rows sha label_free in the kept part 1", "rows_label_free.json", V1["rows_sha256"]["label_free"])
    for arm in ARMS:
        cmp(f"inputs {arm}: verdict against rows", V["inputs"][arm] == rows[arm]["inputs"], True)
        cmp_hash(f"manifest sha {arm}", "manifest.json", V["inputs"][arm]["manifest_sha256"])
    out["recorded_hashes_agree"] = sorted(forms_seen)

    out["compared_values"] = checked
    out["differences"] = [[w, repr(m), repr(t)] for w, m, t in diffs]
    out["largest_relative_difference_of_a_finite_value"] = worst
    json.dump(out, open(outp, "w", encoding="utf-8"), indent=1)
    j = out["self_check"]["label_free|condensed|third"]
    print("rows:", n_rows, "infinite:", n_inf, "fields not evaluable:", n_failed)
    for r in notes:
        print("  infinite row:", r)
    print("part 1 (judged):", {k: j[k] for k in ("pairs", "flagged", "not_flagged_pairs_above_0.10_in_any_run",
                                                  "not_flagged_readings", "not_flagged_readings_above_0.05",
                                                  "not_flagged_share_above_0.05", "S1", "S2", "S3", "verdict")})
    print("  R:", j["ranking"], " pairs above:", j["pairs_above"])
    print("  largest error not flagged:", j["largest_error_not_flagged"])
    for arm in ARMS:
        for rd in READINGS:
            s = st[arm][rd]["third"]
            print(f"third {arm} {rd}: medians {s['median']} p90 {s['p90']} C1 {s['C1']} C2 {s['C2']}")
    print("part 2:", out["comparison"]["judged"], out["comparison"]["supervised_raw_over_label_free_condensed"])
    print("  both raw:", out["comparison"]["reported"]["raw"]["third"])
    print("identity:", out["identity"])
    print("kept part 1 equals the final part 1:", same_part1, "| kept verdict: comparison",
          out["part1_kept_comparison_word"], "| not evaluated", out["part1_kept_not_evaluated"],
          "| training members labelled", out["part1_kept_training_members_labelled"])
    print("the hashes of the rows files and of the manifest that the verdict records agree with the files:", ", ".join(sorted(forms_seen)))
    print("values compared with the verdict files:", checked, "| differences:", len(diffs),
          "| largest relative difference of a finite value:", worst)
    for d in diffs[:40]:
        print("  DIFFERENT:", d)


if __name__ == "__main__":
    main()
