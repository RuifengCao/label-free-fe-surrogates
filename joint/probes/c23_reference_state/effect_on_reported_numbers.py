"""After the verdict (20 Nov 2026), exploratory: what the reported numbers that contain the three infinite rows would be with
the values the same solves give from a zeroed bubble state. Reads the returned rows files, the returned verdict and
the returned configuration; its last part (22 Nov 2026) imports the stamped self-check function, so run it from joint/.
  python -I -B probes/c23_reference_state/effect_on_reported_numbers.py RECORDS"""
import json, math, pathlib, sys
rec = pathlib.Path(sys.argv[1])
v = json.loads((rec / "verdict.json").read_text())
rf = {a: json.loads((rec / f"rows_{a}.json").read_text()) for a in ("label_free", "supervised_512")}
CLEAN = {("label_free", "raw", "6", "third", "third_0034", 0): -0.0027282879135048788,
         ("supervised_512", "condensed", "6", "eval", "eval_0063", 0): 1.020935954139211,
         ("supervised_512", "condensed", "6", "eval", "eval_0063", 1): 1.0537772160075902}
def q(vv, p):
    s = sorted(vv); h = (len(s) - 1) * p; lo = math.floor(h); t = h - lo
    a, b = s[lo], s[min(lo + 1, len(s) - 1)]
    if t == 0 or a == b: return a
    if math.isinf(a) or math.isinf(b): return b
    return a + (b - a) * t
def errs(arm, reading, seed, s, clean, level=None):
    r = rf[arm]["readings"][reading][seed][f"{s}_rows"]
    out = []
    for i in sorted(r):
        for k, x in enumerate(r[i]):
            if level is not None and k != level: continue
            e = x["curve_err"]
            if clean and (arm, reading, seed, s, i, k) in CLEAN: e = CLEAN[(arm, reading, seed, s, i, k)]
            out.append(abs(e))
    return out
def stats(arm, reading, s, clean):
    med = [q(errs(arm, reading, seed, s, clean), 0.5) for seed in "567"]
    p90 = [q(errs(arm, reading, seed, s, clean), 0.9) for seed in "567"]
    return med, p90, q(med, 0.5), q(p90, 0.5)
for arm, reading, s in (("label_free", "raw", "third"), ("supervised_512", "condensed", "eval")):
    for clean in (False, True):
        med, p90, c1, c2 = stats(arm, reading, s, clean)
        print(arm, reading, s, "clean" if clean else "returned", "med", [f"{x:.6%}" for x in med], "p90", [f"{x:.6%}" for x in p90], "C1 %.6f%% C2 %.6f%%" % (100*c1, 100*c2),
              "above10", [sum(x > 0.10 for x in errs(arm, reading, seed, s, clean)) for seed in "567"])
# ratios that involve these blocks
def ratio(a, b): return a / b
lfr_ret, lfr_cl = stats("label_free", "raw", "third", False), stats("label_free", "raw", "third", True)
sr = stats("supervised_512", "raw", "third", False)
print("third raw/raw returned:", ratio(sr[2], lfr_ret[2]), ratio(sr[3], lfr_ret[3]), "| clean:", ratio(sr[2], lfr_cl[2]), ratio(sr[3], lfr_cl[3]))
sce_ret, sce_cl = stats("supervised_512", "condensed", "eval", False), stats("supervised_512", "condensed", "eval", True)
lce = stats("label_free", "condensed", "eval", False)
print("eval condensed/condensed returned:", ratio(sce_ret[2], lce[2]), ratio(sce_ret[3], lce[3]), "| clean:", ratio(sce_cl[2], lce[2]), ratio(sce_cl[3], lce[3]))
# by level
for arm, reading, s, seed, lv in (("label_free", "raw", "third", "6", 0), ("supervised_512", "condensed", "eval", "6", 0), ("supervised_512", "condensed", "eval", "6", 1)):
    print(arm, reading, s, "seed", seed, "level", lv, "median returned %.4f%% clean %.4f%%" % (100*q(errs(arm, reading, seed, s, False, lv), 0.5), 100*q(errs(arm, reading, seed, s, True, lv), 0.5)),
          "p90 returned", q(errs(arm, reading, seed, s, False, lv), 0.9), "clean", q(errs(arm, reading, seed, s, True, lv), 0.9))
# part 1 blocks that contain an infinite row
for arm, reading, s, iid, lv in (("label_free", "raw", "third", "third_0034", 0), ("supervised_512", "condensed", "eval", "eval_0063", 0), ("supervised_512", "condensed", "eval", "eval_0063", 1)):
    b = v["self_check_reported"][arm][reading][s]
    print(arm, reading, s, iid, lv, "spread", b["by_member"][iid]["spread"][lv], "flagged", b["by_member"][iid]["flagged"][lv],
          "| block: S1 count", b["not_flagged_pairs_above_0.10_in_any_run"], "S2", b["not_flagged_readings_above_0.05"], "of", b["not_flagged_readings"],
          "auc", b["ranking"]["auc_above_0.05"], "pairs_above", b["pairs_above"])
    others = [abs(rf[arm]["readings"][reading][sd][f"{s}_rows"][iid][lv]["curve_err"]) for sd in "567"]
    print("    errors of the three runs at this pair (returned):", others)
# 22 Nov 2026: every printed figure of docs/G-C2.3_verdict.md that contains one of the three rows, as returned and with the
# values from a zeroed bubble state. The block of part 1 is computed with the stamped function (run from joint/).
import copy
sys.path.insert(0, str(pathlib.Path.cwd()))
from c23.evaluate import self_check  # noqa: E402
cfg = json.loads((rec / "c23_config.json").read_text())
def block(arm, reading, s, clean):
    rows = {seed: copy.deepcopy(rf[arm]["readings"][reading][seed][f"{s}_rows"]) for seed in "567"}
    if clean:
        for (a, r, seed, ss, i, k), e in CLEAN.items():
            if (a, r, ss) == (arm, reading, s):
                rows[seed][i][k]["curve_err"], rows[seed][i][k]["abs_curve_err"] = e, abs(e)
    return self_check(cfg["self_check"], rows, sorted(rows["5"]))
def n_inf(arm, reading, s, clean):
    return sum(math.isinf(x) for seed in "567" for x in errs(arm, reading, seed, s, clean))
def signed(arm, reading, seed, s, clean, level):
    r = rf[arm]["readings"][reading][seed][f"{s}_rows"]
    return [CLEAN.get((arm, reading, seed, s, i, level), r[i][level]["curve_err"]) if clean else r[i][level]["curve_err"] for i in sorted(r)]
b0, b1 = block("label_free", "raw", "third", False), block("label_free", "raw", "third", True)
kept = v["self_check_reported"]["label_free"]["raw"]["third"]
assert all(b0[k] == kept[k] for k in ("flagged", "not_flagged_pairs_above_0.10_in_any_run", "not_flagged_readings_above_0.05", "pairs_above")) \
    and b0["ranking"] == kept["ranking"], "the block as returned is not reproduced"
print("ALL PRINTED FIGURES THAT CONTAIN ONE OF THE THREE ROWS: returned -> with the values from a zeroed bubble state")
print("part 1, label-free raw, third sample: pairs not flagged above 10%%: %d -> %d; readings not flagged above 5%%: %d of %d -> %d of %d; "
      "ranking probability of seed 6: %.4f -> %.4f (seeds 5 and 7: %.4f, %.4f, unchanged: %s); flagged %d -> %d; verdict %s -> %s; R %s -> %s"
      % (b0["not_flagged_pairs_above_0.10_in_any_run"], b1["not_flagged_pairs_above_0.10_in_any_run"],
         b0["not_flagged_readings_above_0.05"], b0["not_flagged_readings"], b1["not_flagged_readings_above_0.05"], b1["not_flagged_readings"],
         b0["ranking"]["auc_above_0.05"][1], b1["ranking"]["auc_above_0.05"][1], b1["ranking"]["auc_above_0.05"][0], b1["ranking"]["auc_above_0.05"][2],
         b0["ranking"]["auc_above_0.05"][0] == b1["ranking"]["auc_above_0.05"][0] and b0["ranking"]["auc_above_0.05"][2] == b1["ranking"]["auc_above_0.05"][2],
         b0["flagged"], b1["flagged"], b0["verdict"], b1["verdict"], b0["ranking"]["R"], b1["ranking"]["R"]))
print("label-free raw, third sample: median of seed 6 and over the seeds %.3f%% -> %.3f%%; 90th percentile of seed 6 %.3f%% -> %.3f%% (over the seeds %.3f%% -> %.3f%%); "
      "pairs above 10%% in seed 6: %d -> %d; infinite: %d -> %d"
      % (100*lfr_ret[2], 100*lfr_cl[2], 100*lfr_ret[1][1], 100*lfr_cl[1][1], 100*lfr_ret[3], 100*lfr_cl[3],
         sum(x > 0.10 for x in errs("label_free", "raw", "6", "third", False)), sum(x > 0.10 for x in errs("label_free", "raw", "6", "third", True)),
         n_inf("label_free", "raw", "third", False), n_inf("label_free", "raw", "third", True)))
print("ratio of the medians, both arms raw, third sample: %.3f -> %.3f (of the 90th percentiles: %.3f -> %.3f)"
      % (ratio(sr[2], lfr_ret[2]), ratio(sr[2], lfr_cl[2]), ratio(sr[3], lfr_ret[3]), ratio(sr[3], lfr_cl[3])))
print("supervised condensed, fresh members of G-C2.2: 90th percentile of seed 6 and over the seeds %.3f%% -> %.3f%%; medians %.3f%% -> %.3f%%; infinite: %d -> %d"
      % (100*sce_ret[3], 100*sce_cl[3], 100*sce_ret[2], 100*sce_cl[2],
         n_inf("supervised_512", "condensed", "eval", False), n_inf("supervised_512", "condensed", "eval", True)))
print("ratio of the 90th percentiles, both arms condensed, fresh members of G-C2.2: %.3f -> %.3f (of the medians: %.3f -> %.3f)"
      % (ratio(sce_ret[3], lce[3]), ratio(sce_cl[3], lce[3]), ratio(sce_ret[2], lce[2]), ratio(sce_cl[2], lce[2])))
a0, a1 = errs("label_free", "raw", "6", "third", False, 0), errs("label_free", "raw", "6", "third", True, 0)
print("label-free raw, seed 6, third sample, at 0.5 mm: median %.2f%% -> %.2f%%; 90th percentile %.2f%% -> %.2f%%; median signed %+.2f%% -> %+.2f%%"
      % (100*q(a0, 0.5), 100*q(a1, 0.5), 100*q(a0, 0.9), 100*q(a1, 0.9),
         100*q(signed("label_free", "raw", "6", "third", False, 0), 0.5), 100*q(signed("label_free", "raw", "6", "third", True, 0), 0.5)))
m0 = [q(errs("label_free", "raw", seed, "third", False, 0), 0.5) for seed in "567"]
m1 = [q(errs("label_free", "raw", seed, "third", True, 0), 0.5) for seed in "567"]
print("the same, median of the three runs' medians at 0.5 mm: %.2f%% -> %.2f%%" % (100*q(m0, 0.5), 100*q(m1, 0.5)))
bs0, bs1 = block("supervised_512", "condensed", "eval", False), block("supervised_512", "condensed", "eval", True)
print("part 1 applied to the supervised runs, condensed, fresh members of G-C2.2: pairs not flagged above 10%%: %d -> %d; readings not flagged above 5%%: %d -> %d of %d"
      % (bs0["not_flagged_pairs_above_0.10_in_any_run"], bs1["not_flagged_pairs_above_0.10_in_any_run"],
         bs0["not_flagged_readings_above_0.05"], bs1["not_flagged_readings_above_0.05"], bs1["not_flagged_readings"]))
tot = [sum(n_inf(a, r, ss, c) for a in ("label_free", "supervised_512") for r in ("condensed", "raw") for ss in ("third", "eval", "tested")) for c in (False, True)]
print("rows with an infinite error: %d -> %d" % (tot[0], tot[1]))
