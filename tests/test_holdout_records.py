"""cmame-paper Stage 13 (25 October 2026): the return of PREREG_HOLDOUT's run
(RUNBOOK_CMAME Sec. E, 21 October 2026) as committed under
records/cmame/holdout/return/, its verdict (records/cmame/holdout/verdict.json),
and the facts that records/cmame/README.md and the Stage 13 notes quote from
them.

The claims, the reading H3 and the tally are recomputed here from the
evaluations' per-instance arrays by PREREG_HOLDOUT Sec. 5's rules, without the
adjudicator's code; the adjudication itself is run again in process on the
committed return and compared with the committed verdict. The return's
tarball is not committed: the README is the record of its SHA-256."""

import hashlib
import json
import math
import re
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CM = ROOT / "records" / "cmame"
RET = CM / "holdout" / "return"
VERDICT = CM / "holdout" / "verdict.json"
README = CM / "README.md"
NOTES = ROOT / "BRANCH_NOTES_statics-paper.md"
PREREG = ROOT / "PREREG_HOLDOUT.md"
CONFIG = ROOT / "configs" / "holdout_v1.json"
TAG = "prereg-holdout"
STAMPED_COMMIT = "69fb6989c56fd52c5ecae1cef6323ca22761ca9d"
STAMPED_TREE = "c480c756ada4d933056e7b6918d48462df054da9"
FIRST_COMMIT = "8b5d4436ee4a91836b627ef852cd2f5e98d88b0f"          # RUNBOOK_CMAME Sec. D's
FIRST_TREE = "e288619b0338a6fa497dfabba6c953e8b3a4e553"
TARBALL_SHA256 = "d185ee5990f3865584579979c10ec3f823db8fd32ce2ac0c8ca180c0c556069e"
HOST = "autodl-container-45e441a24a-99d5b40d"
STAGES = ("label_h3d.log", "eval_h3d.log", "label_h2d.log", "eval_h2d.log")
SET_FILES = ("eval.json", "eval_arrays.npz", "manifest.json")
FIRST_START = "2026-10-21T10:02:23Z"
SECOND_STARTS = ("2026-10-21T10:16:04Z", "2026-10-21T10:54:47Z", "2026-10-21T11:58:38Z",
                 "2026-10-21T11:59:17Z")
MISSING = ("python: can't open file '/root/autodl-tmp/FE-JEPA/scripts/holdout_run.py': "
           "[Errno 2] No such file or directory")
METRICS = ("disp_rel_l2", "energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err", "crit_recall")
LABELS = {"disp_rel_l2": "displacement error", "energy_gap_rel": "relative energy gap",
          "vm_rel_l2": "von Mises error", "peak_vm_rel_err": "peak von Mises error",
          "crit_recall": "critical-region recall"}


def _box(utc: str) -> str:
    """A UTC start line's time as the box names a file set aside then (UTC+8)."""
    t = datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)
    return t.strftime("%Y%m%d-%H%M%S")


FILES = sorted([*STAGES, *(f"{s}.{_box(t)}" for s, t in zip(STAGES, SECOND_STARTS)),
                *(f"{s}/{f}" for s in ("h3d", "h2d") for f in SET_FILES),
                "machine.txt", "precheck.txt", "provenance.txt", "pytest.log",
                "pytest.log.20261021-180704", "status.txt"])


def _sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _script(name: str):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _arrays(name: str) -> dict:
    with np.load(RET / name / "eval_arrays.npz", allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def _values(z: dict, row: str, metric: str) -> np.ndarray:
    """(seeds, instances) per-instance values of one row and metric."""
    r = list(z["rows"]).index(row)
    m = list(z["metrics"]).index(metric)
    return z["values"][r, :, :, m]


def _guard(new, base) -> dict:
    """PREREG_HOLDOUT Sec. 5 (PREREG_CM2D Sec. 4): rel = mean(A)/mean(B) - 1,
    SE_rel = sqrt(s_A^2/3 + s_B^2/3) / mean(B) with sample SDs, tau = max(10%,
    2 SE_rel)."""
    b = statistics.fmean(base)
    rel = statistics.fmean(new) / b - 1
    se = math.sqrt(statistics.stdev(new) ** 2 / 3 + statistics.stdev(base) ** 2 / 3) / b
    tau = max(0.10, 2 * se)
    return {"rel": rel, "se": se, "tau": tau, "lower": rel < -tau, "worse": rel > tau}


def _better(a: float, b: float, metric: str) -> bool:
    return a > b if metric == "crit_recall" else a < b


def _pct(x: float, sign: bool = True) -> str:
    return f"{x * 100:+.1f}%" if sign else f"{x * 100:.1f}%"


def _units(text: str) -> list:
    """A Markdown text cut into paragraphs and list items, each with its line
    breaks and indentation folded into single spaces."""
    return [" ".join(u.split()) for u in re.split(r"\n(?=\s*- )|\n\s*\n", text) if u.strip()]


def _unit_with(text: str, needle: str) -> str:
    found = [u for u in _units(text) if needle in u]
    assert len(found) == 1, (needle, len(found))
    return found[0]


def _has(unit: str, *phrases) -> None:
    for p in phrases:
        assert p in unit, (p, unit[:300])


def _section() -> str:
    text = README.read_text(encoding="utf-8")
    start = text.index("## The holdout sets: the run of 21 October 2026")
    nxt = text.find("\n## ", start + 1)
    return text[start:] if nxt < 0 else text[start:nxt]


def _stage_13() -> str:
    notes = NOTES.read_text(encoding="utf-8")
    start = notes.index("## Stage 13 (25 Oct 2026)")
    nxt = notes.find("\n## ", start + 1)
    return notes[start:] if nxt < 0 else notes[start:nxt]


def _status() -> list:
    return [ln.split() for ln in (RET / "status.txt").read_text().splitlines() if ln.strip()]


def _blocks(name: str, first: str) -> list:
    """A file E1 appends to once per attempt, cut at each line that starts
    with `first`."""
    lines = (RET / name).read_text().splitlines()
    starts = [i for i, x in enumerate(lines) if x.startswith(first)]
    return [lines[i:j] for i, j in zip(starts, starts[1:] + [len(lines)])]


# ------------------------------------------------------------- the return --

def test_the_return_is_whole_and_hashed():
    present = sorted(p.relative_to(RET).as_posix() for p in RET.rglob("*") if p.is_file())
    assert present == FILES
    sec = _section()
    listed = dict(re.findall(r"^\| `return/([^`]+)` \| `([0-9a-f]{64})` \|$", sec, re.M))
    assert sorted(listed) == FILES
    for name in FILES:
        assert _sha(RET / name) == listed[name], name
    _has(_unit_with(sec, "`holdout/return/` holds"), f"`{TARBALL_SHA256}`",
         "as the operator sent it and as recomputed on receipt")
    _has(_unit_with(sec, "- `holdout/verdict.json`"), f"`{_sha(VERDICT)}`")
    # E2's provenance file: the checkout when the return was packed, and every other file
    prov = (RET / "provenance.txt").read_text().splitlines()
    assert prov[:6] == [f"HEAD {STAMPED_COMMIT}", f"tree {STAMPED_TREE}", f"describe {TAG}",
                        f"describe-all {TAG}", f"hostname {HOST}", "--- files ---"]
    rows = [ln.split("  ", 1) for ln in prov[6:]]
    assert {p.removeprefix("./"): h for h, p in rows} == \
        {f: _sha(RET / f) for f in FILES if f != "provenance.txt"}


def test_the_attempts_are_those_the_readme_describes():
    st = _status()
    assert len(st) == 16
    first, second = st[:8], st[8:]
    for k, stage in enumerate(STAGES):
        assert first[2 * k] == [stage, "start", FIRST_START, HOST], stage
        assert first[2 * k + 1] == [stage, "exit=2"], stage
        assert second[2 * k] == [stage, "start", SECOND_STARTS[k], HOST], stage
        assert second[2 * k + 1] == [stage, "exit=0"], stage
        # the first attempt's log, set aside when the second started: the missing script
        old = RET / f"{stage}.{_box(SECOND_STARTS[k])}"
        assert old.read_text() == MISSING + "\n", stage
    # E1's checks before each attempt, its record after each
    pre = _blocks("precheck.txt", "Wed Oct 21 ")
    assert pre == [["Wed Oct 21 18:02:11 CST 2026", HOST, "0 %, 2 MiB"],
                   ["Wed Oct 21 18:15:45 CST 2026", HOST, "0 %, 2 MiB"]]
    mach = _blocks("machine.txt", "HEAD ")
    assert len(mach) == 2
    assert mach[0][:2] == [f"HEAD {FIRST_COMMIT}", f"tree {FIRST_TREE}"]
    assert mach[1][:2] == [f"HEAD {STAMPED_COMMIT}", f"tree {STAMPED_TREE}"]
    for b in mach:
        assert b[2] == "NVIDIA GeForce RTX 5090, 595.71.05, 32607 MiB"
        assert f"hostname {HOST}" in b and "96636764160" in b and "nproc 25" in b
    # E0c's suite on the tag, and the earlier one on Sec. D's commit (that commit's count,
    # as Sec. D's return records it)
    summary = r"^{} passed, {} deselected(, \d+ warnings?)? in [0-9.]+s \(\d+:\d\d:\d\d\)$"
    assert re.search(summary.format(684, 3), (RET / "pytest.log").read_text(), re.M)
    assert re.search(summary.format(535, 2), (RET / "pytest.log.20261021-180704").read_text(),
                     re.M)
    spectra = CM / "spectra"
    assert (spectra / "machine.txt").read_text().splitlines()[:2] == \
        [f"HEAD {FIRST_COMMIT}", f"tree {FIRST_TREE}"]
    assert re.search(summary.format(535, 2), (spectra / "pytest.log").read_text(), re.M)


def test_the_labels_and_evaluations_are_the_configurations_sets():
    sys.path.insert(0, str(ROOT / "src"))
    from fejepa.analysis.holdout import holdout_names, load_spec

    spec = load_spec(CONFIG)
    for name, n, residual in (("h3d", 686, "5.3e-11"), ("h2d", 4111, "3.7e-11")):
        sdef = spec["sets"][name]
        names = holdout_names(sdef)
        man = _load(RET / name / "manifest.json")
        assert len(names) == n == sdef["n_holdout"] == man["n"]
        assert [x["file"] for x in man["instances"]] == names, name
        assert man["excluded"] == sdef["excluded"] and man["used_prefix"] == sdef["used_prefix"]
        assert man["corpus_manifest_sha256"] == sdef["manifest_sha256"]
        assert man["method"] == "direct" and man["reused"] == 0
        assert man["ledger"]["total"] == 4 * n
        res = [x["residual"] for x in man["instances"]]
        assert max(res) <= 1e-8 and f"{max(res):.1e}" == residual, name
        ev = _load(RET / name / "eval.json")
        assert ev["git"] == TAG and ev["labels_manifest_sha256"] == _sha(RET / name / "manifest.json")
        assert ev["torch"]["torch"] == "2.12.1+cu130"
        assert ev["torch"]["gpu"] == "NVIDIA GeForce RTX 5090"
        assert ev["content_mismatch"] == [] and ev["arrays_sha256"] == \
            _sha(RET / name / "eval_arrays.npz")
        z = _arrays(name)
        assert list(z["files"]) == names and z["values"].shape[2] == n
        assert list(z["metrics"]) == list(METRICS) and list(z["seeds"]) == [0, 1, 2]


def test_the_verdict_was_made_from_these_files():
    v = _load(VERDICT)
    inp = v["inputs"]
    for name in ("h3d", "h2d"):
        assert inp[name] == {f: {"path": f"records/cmame/holdout/return/{name}/{f}",
                                 "sha256": _sha(RET / name / f)} for f in SET_FILES}
    for f in ("status.txt", "provenance.txt"):
        assert inp[f] == {"path": f"records/cmame/holdout/return/{f}", "sha256": _sha(RET / f)}
    assert inp["prereg"] == {"path": "PREREG_HOLDOUT.md", "sha256": _sha(PREREG)}
    assert inp["recorded_commit"] == {"HEAD": STAMPED_COMMIT, "tree": STAMPED_TREE}
    assert inp["listed"] == {f: _sha(RET / f) for f in FILES if f != "provenance.txt"}
    sys.path.insert(0, str(ROOT / "src"))
    from fejepa.analysis.holdout import load_spec, spec_sha256
    from fejepa.report import read_prereg_entries

    stamped = dict(read_prereg_entries(PREREG))["holdout_v1"]
    assert v["config"] == {"path": "configs/holdout_v1.json",
                           "sha256": spec_sha256(load_spec(CONFIG))} and \
        v["config"]["sha256"] == stamped
    assert v["adjudicator"]["against_stamp"] == {"ref": TAG, "compared": True, "differs": []}
    assert v["deviations"] == [f"{s}: 2 attempts (exits [2, 0])" for s in STAGES]
    assert all(c["ok"] and c["finite"] for s in v["content_checks"].values()
               for c in s.values())


# ------------------------------------------------- the claims, recomputed --

def test_the_claims_follow_from_the_arrays():
    v = _load(VERDICT)
    c = v["claims"]
    h3, h2 = _arrays("h3d"), _arrays("h2d")

    def means(z, row, m):
        return list(_values(z, row, m).mean(axis=1))

    # T1: the label-free transformer better than the supervised one, each seed and the mean
    ok = True
    for m in METRICS:
        a, b = means(h3, "ar", m), means(h3, "labels", m)
        each = [_better(x, y, m) for x, y in zip(a, b)]
        mean = _better(statistics.fmean(a), statistics.fmean(b), m)
        pairs = [x / y - 1 for x in a for y in b]
        rec = c["T1"]["per_metric"][m]
        assert rec["better_in_seed"] == each and rec["better_in_mean"] == mean, m
        assert np.allclose(rec["label_free_per_seed"], a, rtol=1e-12, atol=0), m
        assert np.allclose(rec["supervised_per_seed"], b, rtol=1e-12, atol=0), m
        assert rec["better_all_pairs"] == all(_better(x, y, m) for x in a for y in b), m
        worst = min(pairs) if m == "crit_recall" else max(pairs)
        assert math.isclose(rec["worst_pair_rel"], worst, rel_tol=1e-9), m
        ok = ok and all(each) and mean
    assert c["T1"]["verdict"] == ("REPLICATED" if ok else "NOT REPLICATED") == "REPLICATED"
    # T2: the graph network's displacement error lower on most instances in each seed, its
    # von Mises error higher on at least 95% of the instance-seed pairs
    d_g, d_a = _values(h3, "mgn", "disp_rel_l2"), _values(h3, "ar", "disp_rel_l2")
    share = list((d_g < d_a).mean(axis=1))
    vm = float((_values(h3, "mgn", "vm_rel_l2") > _values(h3, "ar", "vm_rel_l2")).mean())
    assert np.allclose(c["T2"]["disp_lower_share_per_seed"], share, rtol=0, atol=0)
    assert c["T2"]["vm_higher_share_pooled"] == vm == 1.0 and c["T2"]["pairs"] == 3 * 686
    assert c["T2"]["verdict"] == "REPLICATED" and min(share) > 0.5 and vm >= 0.95
    # T3: load cases worse than the zero field, each with a positive energy and no other
    counts = {}
    for row in ("labels", "mgn"):
        r = list(h3["rows"]).index(row)
        g, p = h3["gap_load"][r], h3["pi_load"][r]
        assert np.all(np.isfinite(g)) and np.all(np.isfinite(p))
        keep = np.abs(g - 1) > 1e-9
        assert np.array_equal((g > 1)[keep], (p > 0)[keep]), row
        counts[row] = [int((g[s] > 1).sum()) for s in range(3)]
        rec = c["T3"]["per_row"][row]
        assert (rec["load_cases"], rec["worse"], rec["sign_mismatch"]) == \
            (g.size, sum(counts[row]), 0), row
    assert counts == {"labels": [96, 107, 137], "mgn": [67, 79, 91]}
    assert c["T3"]["verdict"] == "REPLICATED"
    # H1, H2a, H2b (the guard), H2c (halving): two dimensions, seed means
    plan = {"H1": ("ar", "labels", "energy_gap_rel"),
            "H2a": ("labels_knorm", "labels", "energy_gap_rel"),
            "H2b": ("labels_knorm", "labels", "vm_rel_l2")}
    for h, (a, b, m) in plan.items():
        new, base = means(h2, a, m), means(h2, b, m)
        g, rec = _guard(new, base), c[h]
        assert np.allclose(rec["new_per_seed"], new, rtol=1e-12, atol=0), h
        assert np.allclose(rec["base_per_seed"], base, rtol=1e-12, atol=0), h
        for k, kk in (("rel_change", "rel"), ("se_rel", "se"), ("threshold", "tau")):
            assert math.isclose(rec[k], g[kk], rel_tol=1e-9), (h, k)
        assert rec["verdict"] == ("REPLICATED" if g["lower"] else "NOT REPLICATED"), h
    assert (c["H1"]["verdict"], c["H2a"]["verdict"], c["H2b"]["verdict"]) == \
        ("REPLICATED", "NOT REPLICATED", "REPLICATED")
    assert c["H2a"]["failing"] == ["H2a"]
    assert c["H2c"]["rel_change"] == c["H2b"]["rel_change"] < -0.5
    assert c["H2c"]["verdict"] == "REPLICATED"
    # D2: the label-free transformer's displacement error higher, its other metrics better
    ok = True
    for m in METRICS:
        a, b = means(h2, "ar", m), means(h2, "labels", m)
        holds = (lambda x, y: x > y) if m == "disp_rel_l2" else \
            (lambda x, y, m=m: _better(x, y, m))
        each = [holds(x, y) for x, y in zip(a, b)]
        rec = c["D2"]["per_metric"][m]
        assert rec["holds_in_seed"] == each, m
        assert rec["holds_in_mean"] == holds(statistics.fmean(a), statistics.fmean(b)), m
        pairs = [x / y - 1 for x in a for y in b]
        worst = min(pairs) if m in ("disp_rel_l2", "crit_recall") else max(pairs)
        assert math.isclose(rec["worst_pair_rel"], worst, rel_tol=1e-9), m
        assert rec["holds_all_pairs"] == all(holds(x, y) for x in a for y in b), m
        ok = ok and all(each) and rec["holds_in_mean"]
    assert ok and c["D2"]["verdict"] == "REPLICATED"
    # H3: L_K against the label-free transformer, relative energy gap (a reading)
    g = _guard(means(h2, "labels_knorm", "energy_gap_rel"), means(h2, "ar", "energy_gap_rel"))
    r = v["readings"]["H3"]
    assert math.isclose(r["rel_change"], g["rel"], rel_tol=1e-9)
    assert math.isclose(r["threshold"], g["tau"], rel_tol=1e-9)
    assert not g["lower"] and not g["worse"]
    assert r["reading"] == "no difference shown (within the guard)"
    ex = _guard(means(h2, "ar", "energy_gap_rel"), means(h2, "labels_knorm", "energy_gap_rel"))
    assert math.isclose(r["roles_exchanged"]["rel_change"], ex["rel"], rel_tol=1e-9)
    assert math.isclose(r["roles_exchanged"]["threshold"], ex["tau"], rel_tol=1e-9)
    assert not ex["lower"] and not ex["worse"]
    assert v["tally"] == {"REPLICATED": 7, "NOT REPLICATED": 1, "NOT EVALUATED": 0}
    assert v["V"]["verdict"] == "REPRESENTATIVE" and len(v["V"]["quantities"]) == 35
    assert v["V"]["rejected"] == [] and v["V"]["left_out"] == []
    assert set(v["validation_reference"]["claims"].values()) == {"REPLICATED"}


def test_the_adjudicator_reproduces_the_verdict_in_process():
    """Everything in verdict.json but the paths of its inputs, the configuration's
    path and the adjudicator's own record (its code's SHA-256, its comparison with
    the tag, the library versions) is what scripts/adjudicate_holdout.py computes
    from the committed files."""
    sys.path.insert(0, str(ROOT / "src"))
    from fejepa.analysis.holdout import load_spec

    adj = _script("adjudicate_holdout")
    res = adj.adjudicate(RET, load_spec(CONFIG), PREREG, TAG)
    got = json.loads(json.dumps(adj.jsonable(res), allow_nan=False))
    v = _load(VERDICT)
    assert set(got) == set(v) - {"config", "adjudicator"}
    for k in got:
        if k != "inputs":
            assert got[k] == v[k], k

    def rel(x):
        if isinstance(x, dict):
            return {k: (Path(p).relative_to(ROOT).as_posix() if k == "path" else rel(p))
                    for k, p in x.items()}
        return x

    assert rel(got["inputs"]) == v["inputs"]


# ------------------------------------------------------- what is quoted --

def test_the_readme_quotes_the_records():
    sec = _section()
    v = _load(VERDICT)
    c = v["claims"]
    h3m, h2m = _load(RET / "h3d" / "manifest.json"), _load(RET / "h2d" / "manifest.json")
    h3e, h2e = _load(RET / "h3d" / "eval.json"), _load(RET / "h2d" / "eval.json")
    head = _unit_with(sec, "`holdout/return/` holds")
    _has(head, f"stamped commit `{STAMPED_COMMIT[:7]}` (tag `{TAG}`, tree `{STAMPED_TREE}`)",
         f"from {SECOND_STARTS[0]}", f"h3d (686 instances, 2,744 load-case solves, "
         f"{h3m['seconds']:,.1f} s)", f"h2d (4,111 instances, 16,444 solves, "
         f"{h2m['seconds']:.1f} s)", "largest relative residuals 5.3e-11 and 3.7e-11",
         f"h3d ({h3e['seconds']:,.1f} s) and h2d ({h2e['seconds']:.1f} s)", f"`{HOST}`",
         "driver 595.71.05", "torch 2.12.1+cu130", "684 passed, 3 deselected")
    assert h3m["ledger"]["total"] == 2744 and h2m["ledger"]["total"] == 16444
    assert [ln[0] for ln in _status()[8::2]] == list(STAGES)
    _has(head, "one after another in E1's order (each set's labelling, then its evaluation)",
         "the labellings of h3d")
    assert STAGES == ("label_h3d.log", "eval_h3d.log", "label_h2d.log", "eval_h2d.log")
    for name in ("h3d", "h2d"):
        assert json.loads((RET / f"label_{name}.log").read_text().splitlines()[-1])[
            "source_labelled"] == 0
    # the verdict's paragraph: the command, the content checks
    vp = _unit_with(sec, "- `holdout/verdict.json`")
    _has(vp, "`python scripts/adjudicate_holdout.py --return records/cmame/holdout/return "
             "--config configs/holdout_v1.json --prereg PREREG_HOLDOUT.md --out "
             "records/cmame/holdout/verdict.json`",
         "1.7e-5 and 7.9e-5 in h3d and 1.8e-5 and 1.5e-4 in h2d")
    for name, want in (("h3d", ("1.7e-05", "7.9e-05")), ("h2d", ("1.8e-05", "1.5e-04"))):
        cc = v["content_checks"][name]
        assert all(x == 0 for st, ch in cc.items() if not st.startswith("mgn")
                   for k, x in ch.items() if k.endswith("_rel_dev")), name
        got = tuple(f"{max(ch[k] for st, ch in cc.items()):.1e}"
                    for k in ("disp_rel_l2_median_rel_dev", "energy_gap_rel_median_rel_dev"))
        assert got == want, name
    # the table of claims
    lines = sec.splitlines()
    t1 = c["T1"]["per_metric"]
    worst = min(t1, key=lambda m: abs(t1[m]["worst_pair_rel"]))
    assert worst == "crit_recall"
    t2 = c["T2"]["disp_lower_share_per_seed"]
    t3 = c["T3"]["per_row"]

    def seeds(xs, fmt=".4f"):
        return ", ".join(format(x, fmt) for x in xs[:-1]) + " and " + format(xs[-1], fmt)

    def guard_text(h):
        x = c[h]
        return (f"rel {_pct(x['rel_change']).replace('+', '')}, SE_rel {_pct(x['se_rel'], False)}, "
                f"tau {_pct(x['threshold'], False)}")

    d2 = c["D2"]["per_metric"]
    worst2 = min(d2, key=lambda m: abs(d2[m]["worst_pair_rel"]))
    assert worst2 == "peak_vm_rel_err"
    rows = [
        f"| T1 (h3d) | the label-free transformer better than the supervised transformer on all "
        f"five metrics, in each seed and in the seed mean (20 comparisons); in all nine pairs of "
        f"seeds as well, the least favourable {_pct(t1[worst]['worst_pair_rel'], False)} apart "
        f"({LABELS[worst]}) | {c['T1']['verdict']} |",
        f"| T2 (h3d) | the graph network's displacement error lower than the label-free "
        f"transformer's on {t2[0]:.1%}, {t2[1]:.1%} and {t2[2]:.1%} of the instances "
        f"(the rule: above 50% in each seed), its von Mises error higher on 2,058 of the 2,058 "
        f"instance-seed pairs (at least 95%) | {c['T2']['verdict']} |",
        f"| T3 (h3d) | load cases worse than the zero field: {t3['labels']['worse']} of the "
        f"supervised transformer's {t3['labels']['load_cases']:,} (96, 107 and 137 per seed) and "
        f"{t3['mgn']['worse']} of the graph network's (67, 79 and 91), each with a positive "
        f"energy and no other | {c['T3']['verdict']} |",
        f"| H1 (h2d) | relative energy gap, the label-free transformer "
        f"{seeds(c['H1']['new_per_seed'])} against L_D's {seeds(c['H1']['base_per_seed'])}: "
        f"{guard_text('H1')} | {c['H1']['verdict']} |",
        f"| H2a (h2d) | relative energy gap, L_K {seeds(c['H2a']['new_per_seed'])} against "
        f"L_D's: {guard_text('H2a')} | {c['H2a']['verdict']} |",
        f"| H2b (h2d) | von Mises error, L_K {seeds(c['H2b']['new_per_seed'])} against L_D's "
        f"{seeds(c['H2b']['base_per_seed'])}: {guard_text('H2b')} | {c['H2b']['verdict']} |",
        f"| H2c (h2d) | the same comparison against halving: rel "
        f"{_pct(c['H2c']['rel_change']).replace('+', '')}, below -50% | {c['H2c']['verdict']} |",
        f"| D2 (h2d) | the label-free transformer's displacement error higher than L_D's "
        f"({seeds(d2['disp_rel_l2']['label_free_per_seed'])} against "
        f"{seeds(d2['disp_rel_l2']['supervised_per_seed'])}) and its other four metrics "
        f"better, in each seed and in the seed mean (20 comparisons); in all nine pairs of "
        f"seeds as well, the least favourable {_pct(abs(d2[worst2]['worst_pair_rel']), False)} "
        f"apart ({LABELS[worst2]}) | {c['D2']['verdict']} |"]
    assert c["H2a"]["base_per_seed"] == c["H1"]["base_per_seed"]
    for row in rows:
        assert lines.count(row) == 1, row
    assert c["T3"]["per_row"]["labels"]["load_cases"] == 8232
    _has(_unit_with(sec, "- Tally:"), "7 REPLICATED, 1 NOT REPLICATED (H2a, the claim itself",
         "none NOT EVALUATED", "none of PREREG_HOLDOUT Sec. 5's 2,000 resamples of the "
         "validation instances (`holdout/resample.json`, 1,000 per scheme) read H2a NOT "
         "REPLICATED")
    rs = _load(CM / "holdout" / "resample.json")
    assert rs["resamples"] == 1000 and len(rs["schemes"]) == 2
    assert all(s["replicated"]["H2a"] == 1000 for s in rs["schemes"].values())
    ri = v["secondary"]["h2d"]["ratio_interval"]
    k_r, d_r = ri["labels_knorm"]["energy_gap_rel"], ri["labels"]["energy_gap_rel"]
    q = v["V"]["quantities"]["h2d:labels_knorm:energy_gap_rel"]
    gm = v["secondary"]["h2d"]["holdout"]["guard_labels_knorm_vs_labels"]["energy_gap_rel"][
        "guard_medians"]
    h2 = _arrays("h2d")
    top = _values(h2, "labels_knorm", "energy_gap_rel").max(axis=1)
    g = _guard([float(np.median(a)) for a in _values(h2, "labels_knorm", "energy_gap_rel")],
               [float(np.median(a)) for a in _values(h2, "labels", "energy_gap_rel")])
    assert math.isclose(gm["rel_change"], g["rel"], rel_tol=1e-9) and g["lower"]
    assert math.isclose(gm["threshold"], g["tau"], rel_tol=1e-9)
    assert math.isclose(q["ratio_of_means"], k_r["ratio"], rel_tol=1e-12) and not q["rejected"]
    _has(_unit_with(sec, "- Beside H2a (PREREG_HOLDOUT Sec. 6, no verdict):"),
         f"{k_r['ratio']:.2f} times as large on the holdout set",
         f"the holdout set resampled: {k_r['interval_95_holdout'][0]:.2f} to "
         f"{k_r['interval_95_holdout'][1]:.2f}; L_D's ratio {d_r['ratio']:.2f}, "
         f"{d_r['interval_95_holdout'][0]:.2f} to {d_r['interval_95_holdout'][1]:.2f})",
         f"({q['holdout_median']:.4f} and {q['validation_median']:.4f}; V does not reject the "
         f"quantity, p {q['p']:.2f})",
         f"L_K reads rel {_pct(g['rel'])} against L_D, tau {_pct(g['tau'], False)}: lower beyond "
         f"the guard",
         f"its seeds 0, 1 and 2 on the holdout set are {top[0]:.1f}, {top[1]:.1f} and "
         f"{top[2]:.1f}")
    h3 = v["readings"]["H3"]
    _has(_unit_with(sec, "- H3 (a reading):"),
         f"rel {_pct(h3['rel_change'])}, SE_rel {_pct(h3['se_rel'], False)}, "
         f"tau {_pct(h3['threshold'], False)}: no difference shown (within the guard)",
         f"rel {_pct(h3['roles_exchanged']['rel_change'])}, "
         f"tau {_pct(h3['roles_exchanged']['threshold'], False)}, the same")
    _has(_unit_with(sec, "- V: REPRESENTATIVE."), "Of the 35 quantities",
         "none is rejected at the family-wise level of 5%")
    assert v["V"]["alpha"] == 0.05
    _has(_unit_with(sec, "- `deviations`:"), "each of the four stages started twice, with "
         "exits 2 and 0")
    # the two departures
    first = _unit_with(sec, "- The first attempts ran on another commit.")
    _has(first, f"commit `{FIRST_COMMIT[:7]}`", f"tree `{FIRST_TREE}`",
         "`pytest.log.20261021-180704` reads 535 passed, 2 deselected",
         "(the log is undated; it was set aside at 18:07:04 box time, 10:07:04Z, when E0c ran "
         "again)", "E1's checks ran at 18:02:11 box time (10:02:11Z; `precheck.txt`, first block)",
         f"started at {FIRST_START[11:]}", "each exited 2 at once",
         "stops at any other output or count",
         f"its checks at 18:15:45 box time, 10:15:45Z; its first stage at {SECOND_STARTS[0][11:]}",
         "`DEVIATIONS_FINE3D.md` F1 and F2")
    # the box's times against UTC: the precheck blocks and the set-aside log's suffix
    pre = _blocks("precheck.txt", "Wed Oct 21 ")
    utc = [(datetime.strptime(b[0], "%a %b %d %H:%M:%S CST %Y") - timedelta(hours=8))
           .strftime("%H:%M:%SZ") for b in pre]
    assert utc == ["10:02:11Z", "10:15:45Z"]
    assert (datetime.strptime("20261021-180704", "%Y%m%d-%H%M%S") - timedelta(hours=8)
            ).strftime("%H:%M:%SZ") == "10:07:04Z"
    runbook = (ROOT / "RUNBOOK_STATICS.md").read_text(encoding="utf-8")
    assert "git describe --tags --match prereg-holdout   # must print exactly: prereg-holdout" \
        in runbook
    _has(" ".join(first.split()), "`python: can't open file "
         "'/root/autodl-tmp/FE-JEPA/scripts/holdout_run.py': [Errno 2] No such file or "
         "directory`")
    second = _unit_with(sec, "- A set beyond the bounds of Sec. 2")
    _has(second, "between the scan of Sec. 2 (14 October 2026, 05:37 UTC; repeated at the stamp, "
         "18 October 2026, 07:45 UTC) and the return (packed at 20:11 box time on 21 October "
         "2026, 12:11Z)", "of a tail instance nothing but its drawn parameters was made",
         "On 20 October 2026, from 12:13 to 12:41 UTC",
         "`instance_01661`, `instance_01130` and `instance_00608`",
         "`instance_01656` and `instance_00479`, pool positions 75 and 34",
         "the bound of 80 with a band of mesh sizes",
         "None of these instances is in the tail pool[1024:]",
         "on 25 October 2026 at 12:22 UTC")
    assert "as scanned on 14 October 2026 at 05:37 UTC" in PREREG.read_text(encoding="utf-8")
    assert "18 October 2026 at 07:45 UTC" in " ".join(NOTES.read_text(encoding="utf-8").split())
    assert "`holdout_return_20261021-2011.tgz`" in sec
    # the instances named are where the departure says, by the split itself
    sdef = _load(CONFIG)["sets"]["h3d"]
    perm = np.random.default_rng(sdef["split"]["seed"]).permutation(sdef["n_corpus"])
    n_val, prefix = sdef["split"]["n_val"], sdef["used_prefix"]
    val, pool = list(perm[:n_val]), list(perm[n_val:])
    assert {1661, 1130, 608} <= set(int(i) for i in val)
    assert [pool.index(1656), pool.index(479)] == [75, 34] and prefix == 1024
    tail = {f"instance_{int(i):05d}.npz" for i in pool[prefix:]}
    named = {f"instance_{i:05d}.npz" for i in (1661, 1130, 608, 1656, 479)}
    assert not named & tail and not named & set(_load(RET / "h3d" / "manifest.json")["excluded"])


def test_the_stage_13_notes_quote_the_records():
    notes = _stage_13()
    v = _load(VERDICT)
    c = v["claims"]
    gm = v["secondary"]["h2d"]["holdout"]["guard_labels_knorm_vs_labels"]["energy_gap_rel"][
        "guard_medians"]
    _has(_unit_with(notes, "- PREREG_HOLDOUT's run"),
         "Seven claims REPLICATED (T1, T2, T3, H1, H2b, H2c, D2)",
         f"rel {_pct(c['H2a']['rel_change'])} with tau {_pct(c['H2a']['threshold'], False)}",
         "(L_K's seeds " + ", ".join(f"{x:.4f}" for x in c["H2a"]["new_per_seed"][:2])
         + f" and {c['H2a']['new_per_seed'][2]:.4f})",
         "H3: no difference shown. V: REPRESENTATIVE.",
         f"rel {_pct(gm['rel_change'])} against L_D (tau {_pct(gm['threshold'], False)})",
         "each of the four stages started twice, exits 2 and 0",
         f"commit `{FIRST_COMMIT[:7]}`")
    assert [k for k, x in c.items() if x["verdict"] == "REPLICATED"] == \
        ["T1", "T2", "T3", "H1", "H2b", "H2c", "D2"]
