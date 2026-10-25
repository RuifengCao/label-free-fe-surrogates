"""cmame-paper Stage 13 (25 October 2026): the return of PREREG_K3D's run
(RUNBOOK_CMAME Sec. F, 22-25 October 2026) as committed under
records/cmame/k3d/return/, its verdict (records/cmame/k3d/verdict.json), and
the facts that records/cmame/README.md and the Stage 13 notes quote from them.

The verdicts, the reading H3-3D and the secondary readings quoted are
recomputed here from the report's per-instance arrays by PREREG_K3D Sec. 4's
rule, without the adjudicator's code; the adjudication itself is run again in
process on the committed return and compared with the committed verdict. The
return's tarball is not committed: the README is the record of its SHA-256."""

import hashlib
import json
import math
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CM = ROOT / "records" / "cmame"
RET = CM / "k3d" / "return"
VERDICT = CM / "k3d" / "verdict.json"
README = CM / "README.md"
NOTES = ROOT / "BRANCH_NOTES_cmame-paper.md"
PREREG = ROOT / "PREREG_K3D.md"
CONFIG = ROOT / "configs" / "k3d_v1.json"
SOURCE = ROOT / "records" / "wp8" / "e2" / "baseline" / "report_phase2b.json"
TAG = "prereg-k3d"
STAMPED_COMMIT = "7614ae26c142b2149c40e67571d5c125aac0c18e"
STAMPED_TREE = "30398e29d00df1ebe7c8e9027f0b76c0cbb12b3c"
TARBALL_SHA256 = "d6dc142e05c3bc21ba3d718118faeb287bdaf081bcde3f59e94e90f602b33f52"
HOST = "autodl-container-45e441a24a-99d5b40d"
START = "2026-10-22T14:00:41Z"
CLONE = "/work/label-free-fe-surrogates"
"""Where the adjudicating clone stood: the script writes three paths from it."""
FILES = sorted(["holdout_arrays.npz", "k3d.log", "machine.txt", "precheck.txt",
                "provenance.txt", "pytest.log", "report.json", "reused.json", "seed_0.json",
                "seed_1.json", "seed_2.json", "status.txt"])
METRICS = ("energy_gap_rel", "disp_rel_l2", "vm_rel_l2", "peak_vm_rel_err", "crit_recall")


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


def _guard(new, base) -> dict:
    """PREREG_K3D Sec. 4: rel = mean(A)/mean(B) - 1, SE_rel = sqrt(s_A^2/3 +
    s_B^2/3) / mean(B) with sample SDs, tau = max(10%, 2 SE_rel)."""
    b = statistics.fmean(base)
    rel = statistics.fmean(new) / b - 1
    se = math.sqrt(statistics.stdev(new) ** 2 / 3 + statistics.stdev(base) ** 2 / 3) / b
    tau = max(0.10, 2 * se)
    return {"rel": rel, "se": se, "tau": tau, "lower": rel < -tau, "worse": rel > tau}


def _arrays(rep: dict, row: str, metric: str) -> list:
    """Per seed, the row's per-instance values on the 256 validation instances."""
    return [np.asarray(e["per_instance"][metric], float)
            for e in rep["cells"][row]["1024"]["per_seed_eval"]]


def _medians(arrs) -> list:
    return [float(np.median(a)) for a in arrs]


def _means(arrs) -> list:
    return [float(np.mean(a)) for a in arrs]


def _pct(x: float, sign: bool = True) -> str:
    return f"{x * 100:+.1f}%" if sign else f"{x * 100:.1f}%"


def _seeds(xs, fmt) -> str:
    return ", ".join(format(x, fmt) for x in xs[:-1]) + " and " + format(xs[-1], fmt)


def _units(text: str) -> list:
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
    start = text.index("## K3D: the run of 22-25 October 2026")
    nxt = text.find("\n## ", start + 1)
    return text[start:] if nxt < 0 else text[start:nxt]


def _stage_13() -> str:
    notes = NOTES.read_text(encoding="utf-8")
    start = notes.index("## Stage 13 (25 Oct 2026)")
    nxt = notes.find("\n## ", start + 1)
    return notes[start:] if nxt < 0 else notes[start:nxt]


def _listing() -> dict:
    """`runs/k3d/` as F2's provenance file lists it: name -> time (box clock)."""
    prov = (RET / "provenance.txt").read_text()
    block = prov.split("--- runs/k3d ---\n", 1)[1].split("--- states ---", 1)[0]
    out = {}
    for ln in block.splitlines():
        f = ln.split()
        if len(f) == 9 and f[0].startswith("-"):
            out[f[8]] = datetime.strptime(f"{f[5]} {f[6][:8]}", "%Y-%m-%d %H:%M:%S")
    return out


# ------------------------------------------------------------- the return --

def test_the_return_is_whole_and_hashed():
    assert sorted(p.name for p in RET.iterdir()) == FILES
    sec = _section()
    listed = dict(re.findall(r"^\| `return/([^`]+)` \| `([0-9a-f]{64})` \|$", sec, re.M))
    assert sorted(listed) == FILES
    for name in FILES:
        assert _sha(RET / name) == listed[name], name
    _has(_unit_with(sec, "`k3d/return/` holds"), f"`{TARBALL_SHA256}`",
         "as the operator sent it and as recomputed on receipt")
    _has(_unit_with(sec, "- `k3d/verdict.json`"), f"`{_sha(VERDICT)}`")
    prov = (RET / "provenance.txt").read_text()
    lines = prov.splitlines()
    assert lines[:4] == [f"HEAD {STAMPED_COMMIT}", f"tree {STAMPED_TREE}", f"describe {TAG}",
                         f"hostname {HOST}"]
    files = prov.split("--- files ---\n", 1)[1].splitlines()
    assert {p.removeprefix("./"): h for h, p in (x.split("  ", 1) for x in files)} == \
        {f: _sha(RET / f) for f in FILES if f != "provenance.txt"}
    # the three L_K states stay on the box: their SHA-256 are the report's
    states = prov.split("--- states ---\n", 1)[1].split("--- files ---", 1)[0].splitlines()
    rep = _load(RET / "report.json")
    assert [x.split("  ")[0] for x in states] == \
        [rep["per_seed"][f"s{s}"]["state"]["sha256"] for s in (0, 1, 2)]


def test_one_attempt_on_the_stamped_commit():
    status = [x for x in (RET / "status.txt").read_text().splitlines() if x.strip()]
    assert status == [f"k3d.log start {START} {HOST}", "k3d.log exit=0"]
    pre = (RET / "precheck.txt").read_text().splitlines()
    assert pre == ["Thu Oct 22 22:00:15 CST 2026", HOST, "0 %, 2 MiB"]
    mach = (RET / "machine.txt").read_text().splitlines()
    assert mach[:3] == [f"HEAD {STAMPED_COMMIT}", f"tree {STAMPED_TREE}",
                        "NVIDIA GeForce RTX 5090, 595.71.05, 32607 MiB"]
    for want in (f"hostname {HOST}", "96636764160", "oom 0", "oom_kill 0", "nproc 25"):
        assert want in mach, want
    assert 96636764160 == 90 * 2 ** 30
    summary = r"^760 passed, 3 deselected(, \d+ warnings?)? in [0-9.]+s \(\d+:\d\d:\d\d\)$"
    assert re.search(summary, (RET / "pytest.log").read_text(), re.M)
    rep = _load(RET / "report.json")
    sys.path.insert(0, str(ROOT / "src"))
    from fejepa.report import config_sha256, read_prereg_entries

    stamped = dict(read_prereg_entries(PREREG))["k3d_v1"]
    assert rep["provenance"]["config_sha256"] == stamped == config_sha256(rep["config"])
    assert rep["config"] == _load(CONFIG)
    assert rep["provenance"]["git"] == TAG and rep["provenance"]["commit"] == STAMPED_COMMIT
    assert rep["torch"]["version"] == "2.12.1+cu130" and rep["torch"]["cuda_available"]
    assert rep["torch"]["gpu"] == "NVIDIA GeForce RTX 5090"
    for s in (0, 1, 2):
        ps = rep["per_seed"][f"s{s}"]
        assert (ps["git"], ps["commit"]) == (TAG, STAMPED_COMMIT), s
        assert ps["train"]["epochs_run"] == 200 and ps["train"]["loss"] == "knorm", s
        assert ps["machine"]["resumed_on"] == [], s
    log = (RET / "k3d.log").read_text()
    assert "Traceback" not in log
    assert log.count("[k3d] holdout h3d: 686/686 | 2692 s") == 1


def test_the_verdict_was_made_from_these_files():
    v = _load(VERDICT)
    inp = v["inputs"]
    assert inp["return"] == {f: {"path": f"records/cmame/k3d/return/{f}", "sha256": _sha(RET / f)}
                             for f in FILES if f != "provenance.txt"}
    assert inp["provenance"] == {"path": "records/cmame/k3d/return/provenance.txt",
                                 "sha256": _sha(RET / "provenance.txt")}
    assert inp["recorded_commit"] == {"HEAD": STAMPED_COMMIT, "tree": STAMPED_TREE}
    assert inp["report_sha256"] == _sha(RET / "report.json")
    for key, rel in (("config", "configs/k3d_v1.json"),
                     ("source_report", "records/wp8/e2/baseline/report_phase2b.json"),
                     ("prereg", "PREREG_K3D.md")):
        assert inp[key] == {"path": rel, "sha256": _sha(ROOT / rel)}, key
    # three paths the script writes from its own location: the adjudicating clone's
    for key, rel in (("holdout_manifest", "records/cmame/holdout/return/h3d/manifest.json"),
                     ("holdout_spec", "configs/holdout_v1.json"),
                     ("cm2d_verdict", "records/cmame/cm2d/verdict.json")):
        assert inp[key] == {"path": f"{CLONE}/{rel}", "sha256": _sha(ROOT / rel)}, key
    assert v["adjudicator"]["against_stamp"] == {"ref": TAG, "compared": True, "differs": []}
    assert v["deviations"] == []
    for kind in ("recorded", "recomputed"):
        assert all(ch["ok"] and ch["finite"] for ch in v["content_checks"][kind].values())
        assert max(x for ch in v["content_checks"][kind].values() for k, x in ch.items()
                   if k.endswith("_rel_dev")) == 0.0


# ------------------------------------------------ the verdicts, recomputed --

def test_the_verdicts_follow_from_the_report():
    rep, v = _load(RET / "report.json"), _load(VERDICT)
    arr = {r: {m: _arrays(rep, r, m) for m in METRICS} for r in ("ar", "labels", "labels_knorm")}
    for r in arr:
        assert all(a.size == 256 and np.all(np.isfinite(a)) for m in METRICS for a in arr[r][m])
    plan = {"H2a-3D": ("labels", "energy_gap_rel"), "H2b-3D": ("labels", "vm_rel_l2"),
            "H3-3D": ("ar", "energy_gap_rel")}
    for h, (base, m) in plan.items():
        new_med, base_med = _medians(arr["labels_knorm"][m]), _medians(arr[base][m])
        g, rec = _guard(new_med, base_med), v[h]
        assert rec["metric"] == m and rec["statistic"] == "per-seed medians", h
        assert np.allclose(rec["new_per_seed"], new_med, rtol=1e-12, atol=0), h
        assert np.allclose(rec["base_per_seed"], base_med, rtol=1e-12, atol=0), h
        for k, kk in (("rel_change", "rel"), ("se_rel", "se"), ("threshold", "tau")):
            assert math.isclose(rec[k], g[kk], rel_tol=1e-9), (h, k)
        assert (rec["lower"], rec["worse"]) == (g["lower"], g["worse"]) == (True, False), h
        means = _guard(_means(arr["labels_knorm"][m]), _means(arr[base][m]))
        bm = rec["beside"]["seed_means"]
        assert math.isclose(bm["rel_change"], means["rel"], rel_tol=1e-9), h
        assert math.isclose(bm["threshold"], means["tau"], rel_tol=1e-9), h
        assert (bm["lower"], bm["worse"]) == (means["lower"], means["worse"]), h
    assert v["H2a-3D"]["verdict"] == v["H2b-3D"]["verdict"] == "SUPPORTED"
    assert v["H3-3D"]["reading"] == "the stiffness-norm transformer lower beyond the guard"
    ex = _guard(_medians(arr["ar"]["energy_gap_rel"]), _medians(arr["labels_knorm"]["energy_gap_rel"]))
    r = v["H3-3D"]["roles_exchanged"]
    assert math.isclose(r["rel_change"], ex["rel"], rel_tol=1e-9) and ex["worse"] and r["worse"]
    assert math.isclose(r["threshold"], ex["tau"], rel_tol=1e-9)
    # the instance that carries L_D's seed means: validation instance 107 of the split
    # (n_val 256, seed 1, of 2,000), instance_00485
    gaps = arr["labels"]["energy_gap_rel"][1]
    k = int(np.argmax(gaps))
    perm = np.random.default_rng(1).permutation(2000)
    assert k == 107 and f"instance_{int(perm[k]):05d}.npz" == "instance_00485.npz"
    assert round(float(gaps[k])) == 23727
    # the holdout set's 686 instances: per-seed medians
    with np.load(RET / "holdout_arrays.npz", allow_pickle=False) as z:
        hv, rows, mets = z["values"], list(z["rows"]), list(z["metrics"])
    assert hv.shape == (3, 3, 686, 5)
    hold = v["secondary"]["holdout"]["hypotheses"]
    for h, (base, m) in plan.items():
        med = {row: [float(np.median(hv[rows.index(row), s, :, mets.index(m)])) for s in range(3)]
               for row in (base, "labels_knorm")}
        g = _guard(med["labels_knorm"], med[base])
        assert math.isclose(hold[h]["medians"]["rel_change"], g["rel"], rel_tol=1e-9), h
        assert math.isclose(hold[h]["medians"]["threshold"], g["tau"], rel_tol=1e-9), h
        assert g["lower"] and hold[h]["same_direction"] is True, h


def test_the_secondary_readings_quoted_follow_from_the_report():
    rep, v = _load(RET / "report.json"), _load(VERDICT)
    sec = v["secondary"]
    arr = {r: {m: _arrays(rep, r, m) for m in METRICS} for r in ("ar", "labels", "labels_knorm")}
    for m in METRICS:
        g = _guard(_medians(arr["labels_knorm"][m]), _medians(arr["ar"][m]))
        rec = sec["comparisons"][m]["labels_knorm_vs_ar"]["medians"]
        assert math.isclose(rec["rel_change"], g["rel"], rel_tol=1e-9), m
        assert math.isclose(rec["threshold"], g["tau"], rel_tol=1e-9), m
        better = g["worse"] if m == "crit_recall" else g["lower"]
        assert rec["new_better_beyond_guard"] == better == (m != "crit_recall"), m
    for m, want in (("energy_gap_rel", 738), ("disp_rel_l2", 528), ("vm_rel_l2", 676)):
        x = np.concatenate(arr["labels_knorm"][m])
        y = np.concatenate(arr["ar"][m])
        assert int((x < y).sum()) == want == sec["pairing"]["labels_knorm_vs_ar"][m]["first_lower"]
    for row, want in (("ar", 0), ("labels", 18), ("labels_knorm", 0)):
        x = np.concatenate(arr[row]["energy_gap_rel"])
        assert int((x > 1).sum()) == want == sec["worse_than_zero"][row]["count"], row
        assert sec["worse_than_zero"][row]["of"] == 768
    src = _load(SOURCE)["results"]["e8"]["metrics"]["cells"]["labels_anchor"]["1024"]
    for m in ("energy_gap_rel", "vm_rel_l2"):
        ref = [np.asarray(e["per_instance"][m], float) for e in src["per_seed_eval"]]
        g = _guard(_medians(arr["labels_knorm"][m]), _medians(ref))
        rec = sec["labels_energy"][m]["medians"]
        assert math.isclose(rec["rel_change"], g["rel"], rel_tol=1e-9) and g["lower"], m
        assert math.isclose(rec["threshold"], g["tau"], rel_tol=1e-9), m
    for m in ("vm_rel_l2", "energy_gap_rel"):
        b, a, c = (statistics.fmean(_medians(arr[r][m])) for r in ("labels", "labels_knorm", "ar"))
        assert math.isclose(sec["gap_closure"][m]["medians"]["closure"], (b - a) / (b - c),
                            rel_tol=1e-9), m


def test_the_adjudicator_reproduces_the_verdict_in_process():
    """Everything in verdict.json but its inputs and the adjudicator's own record
    (its code's SHA-256 and its comparison with the tag) is what
    scripts/adjudicate_k3d.py computes from the committed files."""
    adj = _script("adjudicate_k3d")
    rep, rep_sha, status, prov, logs = adj.load_return(RET)
    assert rep_sha == _sha(RET / "report.json") and logs == ["k3d.log"]
    res = adj.adjudicate_k3d(rep, _load(CONFIG), adj.prereg_hash(PREREG), _load(SOURCE),
                             _sha(SOURCE), TAG, status, len(logs),
                             holdout_npz=RET / "holdout_arrays.npz", prov_text=prov, ret=RET)
    got = json.loads(json.dumps(adj.jsonable(res), allow_nan=False))
    v = _load(VERDICT)
    assert set(got) == set(v) - {"inputs", "adjudicator"}
    for k in got:
        assert got[k] == v[k], k


# ------------------------------------------------------- what is quoted --

def test_the_readme_quotes_the_records():
    sec = _section()
    v = _load(VERDICT)
    t = _listing()
    start = datetime(2026, 10, 22, 22, 0, 41)                    # START on the box's clock
    done = [t["seed_0.json"], t["seed_1.json"], t["seed_2.json"]]
    spans = [b - a for a, b in zip([t["reused.json"]] + done[:2], done)]
    mins = sorted(round(s.total_seconds() / 60) for s in spans)
    assert (mins[0], mins[-1]) == (22 * 60 + 26, 22 * 60 + 29)
    total = t["report.json"] - start
    assert round(total.total_seconds() / 60) == 68 * 60 + 20
    head = _unit_with(sec, "`k3d/return/` holds")
    _has(head, f"stamped commit `{STAMPED_COMMIT[:7]}` (tag `{TAG}`, tree `{STAMPED_TREE}`)",
         f"started at {START} and exited 0",
         f"by {t['reused.json']:%H:%M:%S} on 22 October (`reused.json`)",
         f"finished at {done[0]:%H:%M:%S} on 23 October, {done[1]:%H:%M:%S} on 24 October and "
         f"{done[2]:%H:%M:%S} on 25 October, each 22 h 26 min to 22 h 29 min after the one "
         f"before (seed 0 after the stored states' evaluations)",
         "686 instances evaluated in 2,692 s",
         f"report written at {t['report.json']:%H:%M:%S} on 25 October, 68 h 20 min after the "
         f"start", "RTX 5090 (driver 595.71.05), torch 2.12.1+cu130",
         "96,636,764,160 bytes (90 GiB)", "(`oom_kill 0`)", "760 passed, 3 deselected")
    vp = _unit_with(sec, "- `k3d/verdict.json`")
    _has(vp, f"in a clone of its own at `{CLONE}`",
         "`python scripts/adjudicate_k3d.py --return records/cmame/k3d/return --prereg "
         "PREREG_K3D.md --config configs/k3d_v1.json --source-report "
         "records/wp8/e2/baseline/report_phase2b.json --out records/cmame/k3d/verdict.json`",
         "`inputs.holdout_manifest`, `inputs.holdout_spec` and `inputs.cm2d_verdict`",
         "recorded no deviation", "largest relative deviation 0 in every metric")

    def item(needle, h, fmt_new, fmt_base, verdict_text):
        x = v[h]
        _has(_unit_with(sec, needle),
             f"{_seeds(x['new_per_seed'], fmt_new)} against L_D's "
             f"{_seeds(x['base_per_seed'], fmt_base)}: rel {_pct(x['rel_change'])}, "
             f"SE_rel {_pct(x['se_rel'], False)}, tau {_pct(x['threshold'], False)}")
        assert x["verdict"] == verdict_text

    item("- H2a-3D, SUPPORTED:", "H2a-3D", ".5f", ".4f", "SUPPORTED")
    item("- H2b-3D, SUPPORTED:", "H2b-3D", ".4f", ".4f", "SUPPORTED")
    h3 = v["H3-3D"]
    _has(_unit_with(sec, "- H3-3D (a reading):"),
         f"label-free transformer's {_seeds(h3['base_per_seed'], '.5f')}: "
         f"rel {_pct(h3['rel_change'])}, SE_rel {_pct(h3['se_rel'], False)}, tau "
         f"{_pct(h3['threshold'], False)}: the stiffness-norm transformer lower beyond the guard",
         f"rel {_pct(h3['roles_exchanged']['rel_change'])}, tau "
         f"{_pct(h3['roles_exchanged']['threshold'], False)}: the label-free transformer worse "
         f"beyond the guard")
    sm = {h: v[h]["beside"]["seed_means"] for h in ("H2a-3D", "H2b-3D", "H3-3D")}
    ho = v["secondary"]["holdout"]["hypotheses"]
    _has(_unit_with(sec, "- Beside them, with no criterion:"),
         f"H2a-3D rel {sm['H2a-3D']['rel_change'] * 100:+.2f}%, tau "
         f"{_pct(sm['H2a-3D']['threshold'], False)}, within the guard",
         f"seed 1 at {v['H2a-3D']['beside']['seed_means']['base_per_seed'][1]:.2f}",
         "`instance_00485`",
         f"H2b-3D {_pct(sm['H2b-3D']['rel_change'])}, tau {_pct(sm['H2b-3D']['threshold'], False)}",
         f"H3-3D {_pct(sm['H3-3D']['rel_change'])}, tau {_pct(sm['H3-3D']['threshold'], False)}, "
         f"lower beyond it",
         *(f"{h} {_pct(ho[h]['medians']['rel_change'])} (tau "
           f"{_pct(ho[h]['medians']['threshold'], False)})" for h in ho))
    assert not sm["H2a-3D"]["lower"] and sm["H2b-3D"]["lower"] and sm["H3-3D"]["lower"]

    def interval(x):
        return f"{_pct(x['low'])} to {_pct(x['high'])}"

    bs = {h: v[h]["beside"] for h in ("H2a-3D", "H2b-3D", "H3-3D")}
    welch = [interval(bs[h]["welch_95"]) for h in bs]
    boot = [interval(bs[h]["instance_resampling_95"]) for h in bs]
    smw = [interval(bs[h]["seed_means_welch_95"]) for h in bs]
    assert all(1.9 < bs[h]["welch_95"]["df"] < 2.1 for h in bs)
    assert bs["H3-3D"]["welch_95"]["low"] < 0 < bs["H3-3D"]["welch_95"]["high"]
    assert all(bs[h]["seed_means_show_the_direction"] is True for h in bs)
    assert all(bs[h]["instance_resampling_95"]["resamples"] == 2000 for h in bs)
    _has(_unit_with(sec, "- Beside them as well (PREREG_K3D Sec. 4)"),
         f"H2a-3D {welch[0]}, H2b-3D {welch[1]}, H3-3D {welch[2]} (H3-3D's includes no "
         f"difference)", f"the seeds kept: {boot[0]}, {boot[1]} and {boot[2]}",
         f"On the seed means, Welch: {smw[0]}, {smw[1]} and {smw[2]}",
         f"cannot show a reduction (tau {_pct(sm['H2a-3D']['threshold'], False)})")
    mem = _unit_with(sec, "The container's memory limit, 96,636,764,160 bytes (90 GiB)")
    _has(mem, "PREREG_K3D Sec. 7 says 92 GiB",
         "F0c's comment expects 98,784,247,808 or `max`",
         "`records/cmame/timing/`, `spectra/` and `threads/` record (8-11 October 2026)",
         "above the 64 GB of PREREG_K3D Sec. 6 and F0c's stop threshold, 64,000,000,000",
         "No other departure from PREREG_K3D or RUNBOOK_CMAME Sec. F is known")
    assert "96636764160" in (RET / "machine.txt").read_text().split()
    holdout = (CM / "holdout" / "return" / "machine.txt").read_text().split()
    assert holdout.count("96636764160") == 2
    for d in ("timing", "spectra", "threads"):
        assert "98784247808" in (CM / d / "machine.txt").read_text().split(), d
    assert 98784247808 == 92 * 2 ** 30
    k3d = " ".join(PREREG.read_text(encoding="utf-8").split())
    assert "(92 GiB on the box)" in k3d and "memory limit is at least 64 GB" in k3d
    assert "# 98784247808 (92 GiB) or max; a number under 64000000000: stop" in \
        (ROOT / "RUNBOOK_CMAME.md").read_text(encoding="utf-8")
    s = v["secondary"]
    cmp = {m: s["comparisons"][m]["labels_knorm_vs_ar"]["medians"] for m in METRICS}
    _has(_unit_with(sec, "- L_K against the label-free transformer, the five metrics:"),
         f"relative energy gap {_pct(cmp['energy_gap_rel']['rel_change'])}, displacement error "
         f"{_pct(cmp['disp_rel_l2']['rel_change'])}, von Mises error "
         f"{_pct(cmp['vm_rel_l2']['rel_change'])} and peak von Mises error "
         f"{_pct(cmp['peak_vm_rel_err']['rel_change'])}, each lower beyond the guard",
         f"critical-region recall {_pct(cmp['crit_recall']['rel_change'])}, within it (tau "
         f"{_pct(cmp['crit_recall']['threshold'], False)})", "on 738, 528 and 676 of the 768")
    _has(_unit_with(sec, "- Instance-seed pairs worse than the zero field"),
         "the label-free transformer 0, L_D 18, L_K 0")
    le = s["labels_energy"]
    _has(_unit_with(sec, "- L_K against the labels+energy row"),
         f"relative energy gap {_pct(le['energy_gap_rel']['medians']['rel_change'])} (tau "
         f"{_pct(le['energy_gap_rel']['medians']['threshold'], False)}), von Mises error "
         f"{_pct(le['vm_rel_l2']['medians']['rel_change'])} (tau "
         f"{_pct(le['vm_rel_l2']['medians']['threshold'], False)})")
    gc = s["gap_closure"]
    _has(_unit_with(sec, "- The share of the gap between L_D and the label-free transformer"),
         f"{gc['vm_rel_l2']['medians']['closure']:.0%} in the von Mises error and "
         f"{gc['energy_gap_rel']['medians']['closure']:.0%} in the relative energy gap")


def test_the_stage_13_notes_quote_the_records():
    notes = _stage_13()
    v = _load(VERDICT)
    a, b, h = v["H2a-3D"], v["H2b-3D"], v["H3-3D"]
    _has(_unit_with(notes, "- PREREG_K3D's run"),
         f"H2a-3D SUPPORTED (relative energy gap, per-seed medians: rel {_pct(a['rel_change'])}, "
         f"tau {_pct(a['threshold'], False)})",
         f"H2b-3D SUPPORTED (von Mises error: {_pct(b['rel_change'])}, tau "
         f"{_pct(b['threshold'], False)})",
         f"({_pct(h['rel_change'])}, tau {_pct(h['threshold'], False)})", "No deviation.",
         f"H3-3D's Welch 95% interval on the per-seed medians runs from "
         f"{_pct(h['beside']['welch_95']['low'])} to {_pct(h['beside']['welch_95']['high'])}",
         "The container's memory limit, 90 GiB, is not the 92 GiB")
    _has(_unit_with(notes, "- PREREG_K3D was stamped on 21 October 2026"),
         dict(_script_entries())["k3d_v1"], _self_hash()[:8])


def _script_entries():
    sys.path.insert(0, str(ROOT / "src"))
    from fejepa.report import read_prereg_entries

    return read_prereg_entries(PREREG)


def _self_hash() -> str:
    last = PREREG.read_text(encoding="utf-8").strip().splitlines()[-1]
    m = re.fullmatch(r"PREREG_K3D_SHA256 = ([0-9a-f]{64})", last)
    assert m
    return m.group(1)
