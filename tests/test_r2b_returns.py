"""wp9-pool Stage 5 (19 November 2026): the R2b return of RUNBOOK_R2B Sec. 2
as committed under records/wp9/r2b/return/, the adjudication's verdict
(records/wp9/r2b/r2b_verdict.json), and the facts that DEVIATIONS_R2B.md,
records/wp9/README.md and the Stage 5 notes quote from them.

R2b is recomputed here from the reports, from PREREG_R2B Sec. 5 and without
the adjudicator's code; the adjudication itself is re-run on the committed
return and compared with the committed verdict. The return's tarball is not
committed: the README is the record of its SHA-256."""

import datetime as dt
import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REC = ROOT / "records" / "wp9" / "r2b"
RET = REC / "return"
VERDICT = REC / "r2b_verdict.json"
LEDGER = ROOT / "DEVIATIONS_R2B.md"
README = ROOT / "records" / "wp9" / "README.md"
NOTES = ROOT / "BRANCH_NOTES_wp9-pool.md"
TAG = "prereg-r2b"
STAMPED_COMMIT = "2913a17a46bef90579b98b68db0be8b1d827522a"
STAMPED_TREE = "afe45e4e022fc361cd14874adfede2a8a7173d98"
TARBALL_SHA256 = "104492bf6f9158dad42e8625ad01ca9eb87ff67affd851d36a52c17081717b5f"
HOST1 = "autodl-container-eb3344896e-709d725c"
HOST2 = "autodl-container-1qjylxm03k-f5fe291f"
DRIVER = "595.71.05"
STEPS = ("r2b_s", "amp_r2b_s", "r2b_b", "amp_r2b_b")
FIRST_LOG = "r2b_b.log.20261118-203710"
FILES = sorted([
    "provenance.txt", "session/status.txt", "session/pytest.log",
    *(f"session/{s}.log" for s in STEPS), f"session/{FIRST_LOG}",
    "posthoc/amp_r2b_b.json", "posthoc/amp_r2b_s.json",
    *(f"{a}/{f}" for a in ("r2b_b", "r2b_s") for f in ("report.json", "RESULTS.md"))])
STATUS = (
    "r2b_s.log start 2026-11-10 01:02:06 host {h1} driver {d}",
    "r2b_s.log exit=0 2026-11-13 11:17:29",
    "amp_r2b_s.log start 2026-11-13 11:17:31 host {h1} driver {d}",
    "amp_r2b_s.log exit=0 2026-11-13 12:07:06",
    "r2b_b: r2b_s has a complete report",
    "r2b_b.log start 2026-11-13 12:07:08 host {h1} driver {d}",
    "r2b_s: report exists, skipped",
    "amp_r2b_s: record complete, skipped",
    "r2b_b: r2b_s has a complete report",
    "r2b_b: restarting from its states",
    "r2b_b.log start 2026-11-18 20:37:10 host {h2} driver {d}",
    "r2b_b.log exit=0 2026-11-19 03:01:59",
    "amp_r2b_b.log start 2026-11-19 03:02:00 host {h2} driver {d}",
    "amp_r2b_b.log exit=0 2026-11-19 03:38:19")
"""The session's status file, line by line, as the ledger and the README read it."""
ADJUDICATION = [
    "--r2b-b", "records/wp9/r2b/return/r2b_b/report.json",
    "--r2b-s", "records/wp9/r2b/return/r2b_s/report.json",
    "--amp-b", "records/wp9/r2b/return/posthoc/amp_r2b_b.json",
    "--amp-s", "records/wp9/r2b/return/posthoc/amp_r2b_s.json",
    "--status", "records/wp9/r2b/return/session/status.txt",
    "--phase2b", "records/wp8/e2/baseline/report_phase2b.json",
    "--fine3d-verdict", "records/wp9/fine3d/fine3d_verdict.json",
    "--prereg", "PREREG_R2B.md"]
"""The adjudication as the README gives it, without `--out`."""
ADJUDICATING = ("scripts/adjudicate_r2b.py", "scripts/adjudicate_fine3d.py",
                "scripts/stamp_prereg_r2b.py", "src/fejepa/analysis/adjudicate_fine3d.py",
                "src/fejepa/analysis/adjudicate_w9.py", "src/fejepa/analysis/adjudicate.py",
                "src/fejepa/metrics.py", "src/fejepa/report.py", "configs/r2b_s.json")
BOX = dt.timezone(dt.timedelta(hours=8))
"""Box time, +0800."""


def _sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _rep(arm):
    return _load(RET / f"r2b_{arm}" / "report.json")


def _amp(arm):
    return _load(RET / "posthoc" / f"amp_r2b_{arm}.json")


def _means(evals, metric) -> list:
    return [statistics.fmean(e["per_instance"][metric]) for e in evals]


def _p3(rep, which) -> list:
    """P3's zero-shot pass on the fine set or the validation split, per seed."""
    return rep["results"]["p3_transfer"]["metrics"]["ar"][which]["per_seed_eval"]


def _e8(rep) -> list:
    (pool,) = rep["results"]["e8"]["metrics"]["cells"]["ar"].values()
    return pool["per_seed_eval"]


def _guard(new, base) -> dict:
    """PREREG_R2B Sec. 5: rel = mean(A)/mean(B) - 1, SE_rel = sqrt(s_A^2/3 +
    s_B^2/3) / mean(B) with sample SDs, tau = max(10%, 2 SE_rel)."""
    b = statistics.fmean(base)
    rel = statistics.fmean(new) / b - 1
    se = math.sqrt(statistics.stdev(new) ** 2 / 3 + statistics.stdev(base) ** 2 / 3) / b
    tau = max(0.10, 2 * se)
    return {"rel": rel, "se": se, "tau": tau, "lower": rel < -tau, "worse": rel > tau}


def _pct(x: float, sign: bool = True) -> str:
    """A relative change as the documents quote it: -80.2%, +4.1%, 31.5%."""
    return f"{x * 100:+.1f}%" if sign else f"{x * 100:.1f}%"


def _seeds(xs, fmt=".3f") -> str:
    return " / ".join(format(x, fmt) for x in xs)


def _units(text: str) -> list:
    """A Markdown file cut into paragraphs and list items, each with its line
    breaks and indentation folded into single spaces."""
    return [" ".join(u.split()) for u in re.split(r"\n(?=\s*- )|\n\s*\n", text) if u.strip()]


def _unit_with(text: str, needle: str) -> str:
    found = [u for u in _units(text) if needle in u]
    assert len(found) == 1, (needle, len(found))
    return found[0]


def _has(unit: str, *phrases) -> None:
    for p in phrases:
        assert p in unit, (p, unit[:300])


def _stage_5() -> str:
    notes = NOTES.read_text(encoding="utf-8")
    start = notes.index("## Stage 5 (19 November 2026)")
    nxt = notes.find("\n## ", start + 1)
    return notes[start:] if nxt < 0 else notes[start:nxt]


def _status_lines() -> list:
    return (RET / "session" / "status.txt").read_text().splitlines()


def _when(line: str) -> dt.datetime:
    """The box time a status line records."""
    d, t = re.search(r" (\d{4}-\d\d-\d\d) (\d\d:\d\d:\d\d)", line).groups()
    return dt.datetime.fromisoformat(f"{d}T{t}").replace(tzinfo=BOX)


def _provenance() -> str:
    return (RET / "provenance.txt").read_text()


def _state_times() -> dict:
    """The states' times in the provenance file's listing (box time, to the second)."""
    times, where = {}, None
    for line in _provenance().split("--- states ---\n")[1].splitlines():
        d = re.match(r"^runs/r2b/(\S+)/:$", line)
        f = re.match(r"^-\S+\s+\d+\s+\S+\s+\S+\s+\d+\s+(\S+)\s+(\d\d:\d\d:\d\d)\.\d+\s+\+0800\s+(\S+)$",
                     line)
        if d:
            where = d.group(1)
        elif f and where:
            times[f"{where}/{f.group(3)}"] = f"{f.group(1)} {f.group(2)}"
    return times


def _box(when: dt.datetime) -> str:
    """A box time as the documents write it: 15:22 on 16 November."""
    return f"{when:%H:%M} on {when.day} {when:%B}"


# ------------------------------------------------------------- the return --

def test_the_return_is_whole_and_hashed():
    got = sorted(str(p.relative_to(RET)) for p in RET.rglob("*") if p.is_file())
    assert got == FILES
    prov = _provenance()
    # the box's git lines are the stamped commit's, with one untracked file outside runs/
    assert re.search(rf"^HEAD {STAMPED_COMMIT}$", prov, re.M)
    assert re.search(rf"^tree {STAMPED_TREE}$", prov, re.M)
    assert re.search(rf"^describe {TAG}$", prov, re.M) and re.search(rf"^tags {TAG} $", prov, re.M)
    status = prov.split("--- git status --porcelain ---\n")[1].split("\ntorch ")[0]
    assert len(status.splitlines()) == 1 and status.startswith("?? ")
    # the SHA-256 of the reports and amplitude records the box listed are the committed files'
    listed = dict((m.group(2), m.group(1)) for m in re.finditer(
        r"^([0-9a-f]{64})\s+runs/r2b/(\S+\.json)$", prov, re.M))
    assert sorted(listed) == sorted(
        f for f in FILES if f.endswith("report.json") or f.startswith("posthoc/"))
    for rel, sha in listed.items():
        assert _sha(RET / rel) == sha, rel
    # the states' SHA-256 the box listed are those the reports and the amplitude records record
    pts = dict((m.group(2), m.group(1)) for m in re.finditer(
        r"^([0-9a-f]{64})\s+runs/r2b/(\S+\.pt)$", prov, re.M))
    assert len(pts) == 6 and len(_state_times()) == 6
    for arm in ("b", "s"):
        rep = _rep(arm)
        assert rep["provenance"]["git"] == TAG and rep["solve_ledger"]["total"] == 0
        assert rep["provenance"]["seeds"] == [3, 4, 5]
        assert rep["labels_present"]["fine_val"] == 256
        assert [(d["dir"], d["manifest_sha256"][:12], d["n_instances"])
                for d in rep["provenance"]["datasets"]] == [
            ("runs/data3d_phase2", "dc75628290bb", 2000),
            ("runs/data3d_phase2_fine", "0f859ad98a01", 320)]
        assert rep["runtime_policy"] == {"tf32": True, "device": "cuda",
                                         "torch": "2.12.1+cu130", "gpu": "NVIDIA GeForce RTX 5090"}
        states = rep["results"]["e8"]["metrics"]["d9_restart"]["ar_states"]
        for k in (3, 4, 5):
            assert states[f"s{k}"]["sha256"] == pts[f"r2b_{arm}/e8_states/ar_p1024_s{k}.pt"]
        amp = _amp(arm)
        assert amp["report_sha256"] == _sha(RET / f"r2b_{arm}" / "report.json")
        assert amp["git"] == TAG and amp["config_sha256"] == rep["prereg"]["config_sha256"]
        assert amp["states"] == {f"s{k}": states[f"s{k}"]["sha256"] for k in (3, 4, 5)}
    assert re.search(rf"^hostname {HOST2}$", prov, re.M)
    assert re.search(rf"^NVIDIA GeForce RTX 5090, {re.escape(DRIVER)}, ", prov, re.M)
    assert re.search(r"^nproc 16$", prov, re.M) and "Intel(R) Xeon(R) Gold 6459C" in prov
    assert re.search(r"^oom_kill 0$", prov, re.M)
    assert re.search(r"^torch 2\.12\.1\+cu130 True gmsh 4\.15\.2$", prov, re.M)


def test_the_suite_the_session_ran_is_the_stamped_commits():
    last = (RET / "session" / "pytest.log").read_text().strip().splitlines()[-1]
    m = re.match(r"(\d+) passed, 1 skipped, \d+ warnings in ", last)
    assert m, last
    notes = NOTES.read_text(encoding="utf-8")
    r2 = notes[notes.index("## Stage 4, r2"):]
    stamped = int(re.search(r"^- Suite (\d+)", r2, re.M).group(1))
    assert int(m.group(1)) + 1 == stamped == 822


def test_the_status_file_and_the_two_attempts_logs():
    lines = _status_lines()
    assert lines == [s.format(h1=HOST1, h2=HOST2, d=DRIVER) for s in STATUS]
    assert not any(ln.startswith(("STOP", "session interrupted")) for ln in lines)
    prereg = (ROOT / "PREREG_R2B.md").read_text(encoding="utf-8")
    stamped = dict(re.findall(r"^CONFIG_SHA256\[(\w+)\] = ([0-9a-f]{64})$", prereg, re.M))
    old = (RET / "session" / FIRST_LOG).read_text().splitlines()
    new = (RET / "session" / "r2b_b.log").read_text().splitlines()
    s_log = (RET / "session" / "r2b_s.log").read_text().splitlines()
    assert old[0] == new[0] == f"[prereg] verified against PREREG_R2B.md: {stamped['r2b_b'][:12]}..."
    assert s_log[0] == f"[prereg] verified against PREREG_R2B.md: {stamped['r2b_s'][:12]}..."
    # the first attempt: seeds 3 and 4 in 26:50:49 each, seed 5 to 80% of its steps, no error
    units = [ln for ln in old if ln.startswith("[E8 (AR pretrain)] ") and "/3 (" in ln]
    assert units == [
        "[E8 (AR pretrain)] 1/3 (33%) elapsed 26:50:49 eta 53:41:38 | AR pool1024 s3",
        "[E8 (AR pretrain)] 2/3 (67%) elapsed 53:41:38 eta 26:50:49 | AR pool1024 s4"]
    assert old[-1] == "[pretrain E8 AR pool1024 s5] step 163840/204800 (80%) loss=-4.0939e-02"
    text = "\n".join(old)
    assert "Traceback" not in text and "Killed" not in text and "gate G2" not in text
    # the second: the states read, seed 5 resumed at epoch 161 (step 164,864 = 161 x 1,024)
    assert ("[d9] restart mode: existing unit states/results are consumed and recorded "
            "(see results.e8.metrics.d9_restart)") in new
    assert "[ckpt] resumed E8 AR pool1024 s5 at epoch 161/200 (step 164864)" in new
    assert 161 * 1024 == 164864 and 160 * 1024 == 163840 and 200 * 1024 == 204800
    assert "[E8 (AR pretrain)] done in 05:16:19" in new
    assert new[-1] == "[fejepa] solve ledger: {'per_stage': {}, 'total': 0, 'wall_clock_s': 0.0}"
    d9 = _rep("b")["results"]["e8"]["metrics"]["d9_restart"]
    assert d9["reuse_states"] is True and d9["units_resumed_from_epoch"] == {"ar s5": 161}
    assert [d9["ar_states"][f"s{k}"]["reused"] for k in (3, 4, 5)] == [True, True, False]
    s = _rep("s")
    assert s["d9_reuse_states"] is False
    assert s["results"]["e8"]["metrics"]["d9_restart"]["units_resumed_from_epoch"] == {}
    assert _state_times() == {
        "r2b_b/e8_states/ar_p1024_s3.pt": "2026-11-14 14:54:40",
        "r2b_b/e8_states/ar_p1024_s4.pt": "2026-11-15 17:45:41",
        "r2b_b/e8_states/ar_p1024_s5.pt": "2026-11-19 01:52:00",
        "r2b_s/e8_states/ar_p1024_s3.pt": "2026-11-11 03:46:19",
        "r2b_s/e8_states/ar_p1024_s4.pt": "2026-11-12 06:37:26",
        "r2b_s/e8_states/ar_p1024_s5.pt": "2026-11-13 09:31:10"}
    # the reports' own times (UTC) fall at their steps' ends in the status file
    for arm, line in (("s", lines[1]), ("b", lines[11])):
        ts = dt.datetime.fromisoformat(_rep(arm)["provenance"]["timestamp_utc"])
        assert dt.timedelta(0) <= _when(line) - ts <= dt.timedelta(seconds=10), arm


# ------------------------------------------------------------ the verdict --

def test_the_verdict_reproduces_from_the_committed_return(tmp_path):
    out = tmp_path / "verdict.json"
    res = subprocess.run([sys.executable, "scripts/adjudicate_r2b.py", *ADJUDICATION,
                          "--out", str(out)], cwd=ROOT, capture_output=True, text=True,
                         timeout=900)
    assert res.returncode == 0, res.stderr[-3000:]
    fresh, committed = _load(out), _load(VERDICT)
    # the committed verdict was written by the stamped adjudicating code, in a clean
    # checkout of the stamp, with every input named relative to the repository
    adj = committed["adjudicator"]
    assert adj["git"] == TAG and adj["tag"] == TAG and adj["tag_available"]
    assert adj["differs_from_tag"] == [] and adj["prereg_is_tags"]
    assert adj["prereg_self_hash_ok"] and adj["prereg_is_repository_file"]
    assert adj["prereg_file"] == "PREREG_R2B.md"
    assert sorted(adj["files_sha256"]) == sorted(ADJUDICATING)
    assert sorted(committed["inputs"]) == sorted(ADJUDICATION[1::2])
    for path, sha in committed["inputs"].items():
        assert _sha(ROOT / path) == sha, path
    tag = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet",
                          f"{TAG}^{{commit}}"], capture_output=True, text=True)
    if tag.returncode == 0:
        assert tag.stdout.strip() == STAMPED_COMMIT
        for path in ADJUDICATING:
            blob = subprocess.run(["git", "-C", str(ROOT), "show", f"{TAG}:{path}"],
                                  capture_output=True, check=True).stdout
            assert hashlib.sha256(blob).hexdigest() == adj["files_sha256"][path], path

    # what the adjudicator records about this checkout's code (compared with the tag,
    # or not, where the tag is absent) is not the verdict's
    def own(d):
        return d.startswith(("the adjudicating files differ from",
                             "the adjudicating code and the pre-registration read were not "
                             "compared with")) or "the pre-registration read is not" in d
    for key in ("deviations", "session_and_code_deviations"):
        fresh[key] = [d for d in fresh[key] if not own(d)]
    for k in set(fresh) | set(committed):
        if k != "adjudicator":
            assert fresh.get(k) == committed.get(k), k
    assert committed["R2b"]["verdict"] == "SUPPORTED" and committed["notes"] == []
    assert committed["attempts"] == {"r2b_s": 1, "amp_r2b_s": 1, "r2b_b": 2, "amp_r2b_b": 1}
    assert committed["last_exits"] == {s: 0 for s in STEPS}
    assert committed["machines"] == {"r2b_s": [[HOST1, DRIVER]], "amp_r2b_s": [[HOST1, DRIVER]],
                                     "r2b_b": [[HOST1, DRIVER], [HOST2, DRIVER]],
                                     "amp_r2b_b": [[HOST2, DRIVER]]}
    dev = committed["deviations"]
    assert len(dev) == 3 and committed["session_and_code_deviations"] == dev[:2]
    assert dev[0].startswith("the session's steps started on more than one host or GPU driver: ")
    assert dev[1] == "r2b_b: 2 attempts"
    assert dev[2] == ("R2b b: restarted (units resumed {'ar s5': 161}, states reused "
                      "['s3', 's4'], reuse_states True)")


def test_r2b_recomputed_from_the_reports():
    v = _load(VERDICT)["R2b"]
    b, s = _rep("b"), _rep("s")
    for rep in (b, s):
        for evals in (_p3(rep, "fine"), _p3(rep, "inband"), _e8(rep)):
            assert len(evals) == 3
            for e in evals:
                assert all(len(e["per_instance"][m]) == 256 for m in e["per_instance"])
                assert all(math.isfinite(x) for m in e["per_instance"]
                           for x in e["per_instance"][m])
        # P3's in-band pass is E8's cell: the same states on the same split
        for p, q in zip(_p3(rep, "inband"), _e8(rep)):
            for m in ("disp_rel_l2", "energy_gap_rel"):
                assert p["per_instance"][m] == q["per_instance"][m]

    def ratio(rep):      # Sec. 4: per seed, P3's fine mean over P3's in-band mean
        return [f / i for f, i in zip(_means(_p3(rep, "fine"), "disp_rel_l2"),
                                      _means(_p3(rep, "inband"), "disp_rel_l2"))]

    conds = {
        "fine_displacement": (_means(_p3(s, "fine"), "disp_rel_l2"),
                              _means(_p3(b, "fine"), "disp_rel_l2")),
        "fine_over_inband_ratio": (ratio(s), ratio(b)),
        "K1_inband_energy_gap": (_means(_e8(s), "energy_gap_rel"),
                                 _means(_e8(b), "energy_gap_rel")),
        "K1_inband_displacement": (_means(_e8(s), "disp_rel_l2"),
                                   _means(_e8(b), "disp_rel_l2"))}
    for key, (new, base) in conds.items():
        g, c = _guard(new, base), v["conditions"][key]
        assert g["rel"] == pytest.approx(c["rel_change"], abs=1e-12), key
        assert g["se"] == pytest.approx(c["se_rel"], abs=1e-12), key
        assert g["tau"] == pytest.approx(c["threshold"], abs=1e-12), key
        assert (g["lower"], g["worse"]) == (c["lower"], c["worse"]), key
        # per seed to the last few bits (the means are summed in another order here)
        assert c["new_per_seed"] == pytest.approx(new, rel=1e-13, abs=1e-15), key
        assert c["base_per_seed"] == pytest.approx(base, rel=1e-13, abs=1e-15), key
    supported = (_guard(*conds["fine_displacement"])["lower"]
                 and _guard(*conds["fine_over_inband_ratio"])["lower"]
                 and not _guard(*conds["K1_inband_energy_gap"])["worse"]
                 and not _guard(*conds["K1_inband_displacement"])["worse"])
    assert supported and v["verdict"] == "SUPPORTED" and v["conditions"]["failing"] == []
    # the fresh baseline shows the deficit (Sec. 6's lines, 1.5 and 1.10): no uninformative note
    rsm = {a: statistics.fmean(_means(_p3(r, "fine"), "disp_rel_l2"))
           / statistics.fmean(_means(_p3(r, "inband"), "disp_rel_l2")) for a, r in (("b", b), ("s", s))}
    for a in ("b", "s"):
        assert rsm[a] == pytest.approx(v["values"][a]["ratio_of_seed_means"], abs=1e-12)
        assert v["kp4_line"][a]["below_line"] == (rsm[a] < 1.5)
    cstar = [statistics.median([x for row in _amp("b")["seeds"][f"s{k}"]["fine"]["per_instance"]
                                for x in row["c_star"]]) for k in (3, 4, 5)]
    assert cstar == pytest.approx(v["mechanism"]["b"]["fine"]["c_star_median"]["per_seed"], abs=1e-12)
    assert rsm["b"] >= 1.5 and statistics.fmean(cstar) >= 1.10 and v["uninformative_note"] is None
    # beyond the amplitude: S's fine error against the baseline's after scaling by c*
    after = [statistics.fmean([row["disp_c"] for row in _amp("b")["seeds"][f"s{k}"]["fine"]["per_instance"]])
             for k in (3, 4, 5)]
    g, ba = _guard(conds["fine_displacement"][0], after), v["beyond_amplitude"]
    assert g["rel"] == pytest.approx(ba["guard"]["rel_change"], abs=1e-12)
    assert g["tau"] == pytest.approx(ba["guard"]["threshold"], abs=1e-12)
    assert not g["lower"] and not g["worse"] and ba["S_is"] == "within the guard"


# ------------------------------------------------- what the documents quote --

def _bounds(key, seed, lo, hi, step):
    """The range of the baseline's value at one seed over which a condition's
    reading stays as recorded, the other values held (a grid from lo to hi)."""
    c = _load(VERDICT)["R2b"]["conditions"][key]
    new, base = c["new_per_seed"], list(c["base_per_seed"])
    keep = []
    for k in range(round((hi - lo) / step) + 1):
        b = base[:]
        b[seed] = lo + k * step
        g = _guard(new, b)
        if (g["lower"], g["worse"]) == (c["lower"], c["worse"]):
            keep.append(b[seed])
    return min(keep), max(keep)


def _estimate():
    """The ledger's estimate: seed 5's epoch 161 from seed 4's state and the
    first attempt's unit time (26:50:49 per seed of 200 epochs)."""
    per_epoch = dt.timedelta(hours=26, minutes=50, seconds=49) / 200
    s4 = dt.datetime.fromisoformat(_state_times()["r2b_b/e8_states/ar_p1024_s4.pt"]).replace(tzinfo=BOX)
    return per_epoch, s4 + 161 * per_epoch


def test_the_ledger_quotes_the_records():
    led = LEDGER.read_text(encoding="utf-8")
    lines = _status_lines()
    start, s_amp_end, b_start1 = _when(lines[0]), _when(lines[3]), _when(lines[5])
    b_start2, b_end, amp_start, amp_end = (_when(lines[i]) for i in (10, 11, 12, 13))
    _has(_unit_with(led, "Companion to `PREREG_R2B.md`"), "self-hash `4905049d...`",
         "two departures from the runbook", "what comes from the PI rather than from the return "
         "is marked as his")
    last = (ROOT / "PREREG_R2B.md").read_text().strip().splitlines()[-1]
    assert last.startswith("PREREG_R2B_SHA256 = 4905049d")
    v = _load(VERDICT)
    assert len(v["deviations"]) == 3
    _has(_unit_with(led, "lists three, all of one"), "seeds 3 and 4 reused, seed 5 resumed")
    # B1: the expected line, what the box printed, the session's start in box time and UTC
    utc = start.astimezone(dt.timezone.utc)
    assert (start.day, utc.day) == (10, 9)
    assert "## B1 -- the fine set's labelled count read 60, not the runbook's 320 (9 November " \
           "2026, UK time; 10 November, box time)" in led
    _has(_unit_with(led, "That line was wrong (below)"), "320 instances and 320 labelled",
         "320 instances and 60 labelled", "the PI forwarded at 17:04 UTC on 9 November",
         f"started, at {start:%H:%M:%S} on {start.day} November ({utc:%H:%M:%S} UTC on "
         f"{utc.day} November")
    p2b = _load(ROOT / "records/wp8/e2/baseline/report_phase2b.json")
    r2a = [_load(ROOT / f"records/wp9/fine3d/return/r2a_{a}_m1024/report.json") for a in ("b", "s")]
    for rep in (p2b, *r2a, _rep("b"), _rep("s")):
        fine = [d for d in rep["provenance"]["datasets"] if d["dir"] == "runs/data3d_phase2_fine"]
        assert fine[0]["manifest_sha256"].startswith("0f859ad98a01") and fine[0]["n_instances"] == 320
        assert rep["labels_present"]["fine_val"] == 256 and rep["solve_ledger"]["total"] == 0
    _has(_unit_with(led, "**Why 60.**"), "`labels_present.fine_val` reads 256 and the solve ledger 0",
         "Both runbooks now read 60 labelled, each with a dated note at the line")
    # both runbooks' Sec. 0d read 60 labelled, with their dated notes; 320 labelled is gone
    rb = " ".join((ROOT / "RUNBOOK_R2B.md").read_text().split())
    rf = " ".join((ROOT / "RUNBOOK_FINE3D.md").read_text().split())
    assert "manifest `0f859ad98a01...`, 320 instances, 60 labelled; both dry runs" in rb
    assert "(Corrected on 19 November 2026, after the session: this line said 320 labelled." in rb
    assert "manifest `0f859ad98a01...`, 320 instances, 60 labelled (corrected on 19 November " \
           "2026: this line said 320 labelled;" in rf
    for text in (rb, rf):
        assert "320 instances, 320 labelled" not in text and "DEVIATIONS_R2B B1" in text
    # B2: the status file, the logs and the state times
    facts = _unit_with(led, "records S's arm and its amplitude pass")
    _has(facts, f"from {start:%H:%M:%S} on {start.day} November to {s_amp_end:%H:%M:%S} on "
                f"{s_amp_end.day} November",
         f"baseline's start at {b_start1:%H:%M:%S} on {b_start1.day} November",
         f"host `{HOST1}` with GPU driver {DRIVER}", f"`session/{FIRST_LOG}`",
         "80% of its steps (163,840 of 204,800)",
         "14:54:40 on 14 November and 17:45:41 on 15 November",
         f"again at {b_start2:%H:%M:%S} on {b_start2.day} November",
         f"host `{HOST2}` with driver {DRIVER}",
         "epoch 161 of 200 (step 164,864", f"exit 0 at {b_end:%H:%M:%S} on {b_end.day} November",
         f"from {amp_start:%H:%M:%S} to {amp_end:%H:%M:%S}")
    # the estimate: 26:50:49 per seed, from seed 4's state, epoch 161 and epoch 162
    per_epoch, e161 = _estimate()
    gap = (b_start2 - e161).total_seconds() / 3600
    _has(_unit_with(led, "**When and why the first attempt ended.**"),
         "26:50:49 each", f"{per_epoch.total_seconds() / 60:.2f} min per epoch",
         f"near {_box(e161)}", f"about {per_epoch.total_seconds() / 60:.0f} min later",
         f"about {gap:.0f} h", "the PI stated on 19 November 2026", "weekly rental had run out")
    resumed = _rep("b")["results"]["e8"]["metrics"]["d9_restart"]["units_resumed_from_epoch"]["ar s5"]
    _has(_unit_with(led, "**What ran where.**"), "16 CPUs (Xeon Gold 6459C) and `oom_kill 0`",
         f"driver {DRIVER}", "torch 2.12.1+cu130", f"seed 5 to epoch {resumed}",
         f"seed 5's epochs {resumed + 1} to 200", "a restart evaluates reused states again",
         "undated and naming no host")
    rb_raw = " ".join((ROOT / "RUNBOOK_R2B.md").read_text().split())
    assert "The instance's balance must cover about 210 h" in rb_raw and "### 1c." in \
        (ROOT / "RUNBOOK_R2B.md").read_text()
    _has(_unit_with(led, "**Against the runbook.**"), "about 210 h", "rented by the week",
         f"an estimated {(e161 - start).total_seconds() / 3600:.0f} h after the session's first step",
         "Sec. 1c")
    # the baseline's seed 5 could not have decided the verdict
    lo1, hi1 = _bounds("fine_displacement", 2, 0.001, 2.0, 0.001)
    lo2, hi2 = _bounds("fine_over_inband_ratio", 2, 0.01, 60.0, 0.01)
    c = v["R2b"]["conditions"]
    for key in ("K1_inband_energy_gap", "K1_inband_displacement"):
        x = c[key]["base_per_seed"][2]
        lo, hi = _bounds(key, 2, x / 100, 3 * x, x / 100)
        assert lo <= x / 100 + 1e-15 and hi >= 3 * x * (1 - 1e-9), key
    _has(_unit_with(led, "Holding the other values as they are"),
         f"from about {lo1:.2f} to {hi1:.2f} (it is {c['fine_displacement']['base_per_seed'][2]:.3f})",
         f"from about {lo2:.1f} to {hi2:.1f} (it is "
         f"{c['fine_over_inband_ratio']['base_per_seed'][2]:.2f})",
         "from 0 to three times its own", f"seed 5's last {200 - resumed} epochs")
    assert not any(ln.startswith("STOP") for ln in lines)


def test_the_readme_quotes_the_records():
    text = README.read_text(encoding="utf-8")
    sec = text[text.index("## R2b: the box's return (Stage 5"):]
    _has(_unit_with(sec, "| `r2b/return/` |"), f"`{TARBALL_SHA256}`")
    lines = _status_lines()
    start, s_amp_end, b_start1 = _when(lines[0]), _when(lines[3]), _when(lines[5])
    b_start2, b_end, amp_end = _when(lines[10]), _when(lines[11]), _when(lines[13])
    unit = _unit_with(sec, "The six trained states stay on the box")
    _has(unit, f"from {start:%H:%M:%S} on {start.day} November to {s_amp_end:%H:%M:%S} on "
               f"{s_amp_end.day} November (box time, +0800",
         f"host `{HOST1}`", f"started there at {b_start1:%H:%M:%S} on {b_start1.day} November",
         f"host `{HOST2}` from {b_start2:%H:%M:%S} on {b_start2.day} November",
         f"exit 0 at {b_end:%H:%M:%S} on {b_end.day} November", f"exit 0 at {amp_end:%H:%M:%S}",
         f"GPU driver {DRIVER}", "16 CPUs", "`821 passed, 1 skipped`",
         "(`session/pytest.log`; RUNBOOK_R2B Sec. 0c; undated, and its host is not recorded)",
         "torch 2.12.1+cu130 with CUDA and gmsh 4.15.2",
         "(the PI stated that the instance's weekly rental had run out)")
    assert re.search(r"^torch 2\.12\.1\+cu130 True gmsh 4\.15\.2$", _provenance(), re.M)
    _has(_unit_with(sec, "| `r2b/return/` |"), f"returned on {amp_end.day} November 2026")
    # the command block is the test's adjudication
    block = re.search(r"\n    python scripts/adjudicate_r2b\.py \\\n((?:        .*\n)+)", sec)
    args = " ".join(x.strip().rstrip("\\").strip() for x in block.group(1).splitlines()).split()
    assert args == ADJUDICATION + ["--out", "records/wp9/r2b/r2b_verdict.json"]
    v = _load(VERDICT)["R2b"]
    c = v["conditions"]

    def cond(key, fmt=".3f"):
        x = c[key]
        return (f"{_seeds(x['base_per_seed'], fmt)} and {_seeds(x['new_per_seed'], fmt)}, "
                f"rel {_pct(x['rel_change'])}, tau {_pct(x['threshold'], False)}")

    _has(_unit_with(sec, "**R2b: SUPPORTED.**"), cond("fine_displacement"),
         cond("fine_over_inband_ratio", ".2f"), cond("K1_inband_energy_gap", ".4f"),
         cond("K1_inband_displacement"),
         f"(the ratio of the seed means {v['values']['b']['ratio_of_seed_means']:.2f} and "
         f"{v['values']['s']['ratio_of_seed_means']:.2f})")
    rob, pp = v["robustness"], v["paired_per_seed"]

    def three(xs):
        return "{}, {} and {}".format(*(_pct(x) for x in xs))

    def interval(key):
        r = rob[key]["instance_resampling_95"]
        return f"{_pct(r['low'])} to {_pct(r['high'])}"

    def med(key):
        m = rob[key]["medians"]
        return f"{_pct(m['rel_change'])} (tau {_pct(m['threshold'], False)})"

    def welch(key):
        w = rob[key]["welch_95"]
        return f"{_pct(w['low'])} to {_pct(w['high'])}"

    def factor(key):
        """The smallest f, in steps of 0.01, at which S's values at f times the baseline's,
        seed by seed, are worse beyond the guard."""
        base = c[key]["base_per_seed"]
        return next(f / 100 for f in range(100, 1000) if _guard([f / 100 * b for b in base], base)["worse"])

    _has(_unit_with(sec, "K1 holds because its guard is wide"),
         f"in-band energy gap of {c['K1_inband_energy_gap']['new_per_seed'][0]:.4f} and a "
         f"displacement error of {c['K1_inband_displacement']['new_per_seed'][0]:.3f}",
         f"by {three(pp['K1_inband_energy_gap'])}", f"by {three(pp['K1_inband_displacement'])}",
         f"are {interval('K1_inband_energy_gap')} (the energy gap) and "
         f"{interval('K1_inband_displacement')}",
         f"K1 reads {med('K1_inband_energy_gap')} and {med('K1_inband_displacement')}",
         f"rel's Welch 95% intervals are {welch('K1_inband_energy_gap')} and "
         f"{welch('K1_inband_displacement')}",
         "no value of seed 3 would make K1 fail (rel / tau tends to 1/2 as it grows)",
         "S's in-band errors at {:.2f} and {:.2f} times the baseline's, seed by seed, would have "
         "failed it".format(*(factor(k) for k in ("K1_inband_energy_gap", "K1_inband_displacement"))))
    for key in ("K1_inband_energy_gap", "K1_inband_displacement"):
        new, base = c[key]["new_per_seed"], c[key]["base_per_seed"]
        assert not any(_guard([10 ** (k / 20)] + new[1:], base)["worse"] for k in range(-120, 181))
        g = _guard([1e12] + new[1:], base)
        assert g["rel"] / g["tau"] == pytest.approx(0.5, abs=1e-3)
    _has(_unit_with(sec, "Beside (i) and (ii)"),
         f"{med('fine_displacement')} and {med('fine_over_inband_ratio')}",
         f"{interval('fine_displacement')} and {interval('fine_over_inband_ratio')}",
         f"rel's Welch 95% intervals, {welch('fine_displacement')} and "
         f"{welch('fine_over_inband_ratio')}",
         f"fine displacement error {three(pp['fine_displacement'])}",
         f"the ratio {three(pp['fine_over_inband_ratio'])}")
    cmp = v["comparisons"]

    def g(where, metric, tau=True):
        x = cmp[where][metric]["guard"]
        return f"{_pct(x['rel_change'])} (tau {_pct(x['threshold'], False)})" if tau \
            else _pct(x["rel_change"])

    unit = _unit_with(sec, "Every metric on the fine set (Sec. 6)")
    def seeds(where, metric):
        x = cmp[where][metric]["guard"]
        return f"{_seeds(x['base_per_seed'])} and {_seeds(x['new_per_seed'])}"

    _has(unit, f"energy gap, {seeds('fine', 'energy_gap_rel')}, {g('fine', 'energy_gap_rel')}",
         f"von Mises error, {seeds('fine', 'vm_rel_l2')}, {g('fine', 'vm_rel_l2')}",
         f"peak von Mises error {g('fine', 'peak_vm_rel_err')}",
         f"recall {g('fine', 'crit_recall')}, within it",
         f"displacement error {g('p3_inband', 'disp_rel_l2', False)}",
         f"energy gap {g('p3_inband', 'energy_gap_rel', False)}",
         f"von Mises error {g('p3_inband', 'vm_rel_l2')}",
         f"peak von Mises error {g('p3_inband', 'peak_vm_rel_err')}",
         f"recall {g('p3_inband', 'crit_recall')}")
    assert [cmp["fine"][m]["S_is"] for m in ("energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err",
                                             "crit_recall")] == ["better"] * 3 + ["within the guard"]
    for where in ("p3_inband", "e8_inband"):
        assert all(cmp[where][m]["S_is"] == "within the guard" for m in cmp[where]), where
        assert cmp[where] == cmp["p3_inband"]
    mech, kp4 = v["mechanism"], v["kp4_line"]
    lcs = ("0.0906", "0.0742", "0.0579", "0.0374")

    def by_lc(arm, key):
        return _seeds([mech[arm]["remesh"][key][lc] for lc in lcs])

    _has(_unit_with(sec, "The mechanism (Sec. 6)."),
         f"seed means is {kp4['b']['ratio_of_seed_means']:.2f}, above KP4's line of 1.5 (S's, "
         f"{kp4['s']['ratio_of_seed_means']:.2f}, is below it)",
         f"fine set is {_seeds(mech['b']['fine']['c_star_median']['per_seed'])} (in band "
         f"{_seeds(mech['b']['inband']['c_star_median']['per_seed'])}); S's is "
         f"{_seeds(mech['s']['fine']['c_star_median']['per_seed'])} (in band "
         f"{_seeds(mech['s']['inband']['c_star_median']['per_seed'])})",
         f"c_b reads {by_lc('b', 'c_battery_median_by_lc')}",
         f"energy norm {by_lc('b', 'u_norm_K_ratio_median_by_lc')}",
         f"S's read {by_lc('s', 'c_battery_median_by_lc')} and "
         f"{by_lc('s', 'u_norm_K_ratio_median_by_lc')}")
    ba = v["beyond_amplitude"]["guard"]
    _has(_unit_with(sec, "Beyond the amplitude:"),
         f"{_seeds(ba['new_per_seed'])}, against the baseline's after scaling by c*, "
         f"{_seeds(ba['base_per_seed'])}, rel {_pct(ba['rel_change'])}, tau "
         f"{_pct(ba['threshold'], False)}, within the guard",
         "(on the bottleneck it did: 0.0310 against 0.122, PREREG_R2B Sec. 6)")
    assert "(on the bottleneck it did: 0.0310 against 0.122)" in \
        " ".join((ROOT / "PREREG_R2B.md").read_text().split())
    fp = v["fresh_baseline_vs_phase2b"]

    def fpg(key):
        return f"{_pct(fp[key]['rel_change'])} (tau {_pct(fp[key]['threshold'], False)})"

    assert fp["flags"] == []
    _has(_unit_with(sec, "The fresh baseline beside the Phase-2b seeds 0-2"),
         f"error {fpg('fine_displacement')}", f"energy gap {fpg('inband_energy_gap')}",
         f"displacement error {fpg('inband_displacement')}", "no flag")
    ra = v["r2a_beside"]

    def pair(key):
        x = ra["conditions"][key]
        return (f"{_pct(x['bottleneck']['rel_change'])} (tau "
                f"{_pct(x['bottleneck']['threshold'], False)}) and "
                f"{_pct(x['transformer']['rel_change'])} (tau "
                f"{_pct(x['transformer']['threshold'], False)})")

    assert ra["R2a_verdict"] == "SUPPORTED" and v["verdict"] == "SUPPORTED"
    _has(_unit_with(sec, "R2a (SUPPORTED; `fine3d/fine3d_verdict.json`) beside R2b (SUPPORTED)"),
         f"displacement error {pair('fine_displacement')}",
         f"the ratio {pair('fine_over_inband_ratio')}", f"energy gap {pair('K1_inband_energy_gap')}",
         f"displacement error {pair('K1_inband_displacement')}",
         f"is {ra['fine_reduction_ratio']:.3f} (Sec. 5's {ra['c_star_k']:.3f}, from c*)")


def test_the_stage_5_notes_quote_the_verdict():
    notes = _stage_5()
    v = _load(VERDICT)["R2b"]
    c = v["conditions"]

    def gc(key):
        return f"{_pct(c[key]['rel_change'])} (tau {_pct(c[key]['threshold'], False)}"

    _has(_unit_with(notes, "**R2b SUPPORTED.**"),
         f"fine displacement error {gc('fine_displacement')})",
         f"ratio {gc('fine_over_inband_ratio')}; its mean over the seeds "
         f"{c['fine_over_inband_ratio']['base_mean']:.2f} to "
         f"{c['fine_over_inband_ratio']['new_mean']:.2f}, the ratio of the seed means "
         f"{v['values']['b']['ratio_of_seed_means']:.2f} to "
         f"{v['values']['s']['ratio_of_seed_means']:.2f})",
         f"energy gap {gc('K1_inband_energy_gap')})",
         f"displacement error {gc('K1_inband_displacement')})")
    eg, dp = c["K1_inband_energy_gap"], c["K1_inband_displacement"]
    rob = v["robustness"]
    ie, idp = rob["K1_inband_energy_gap"]["instance_resampling_95"], \
        rob["K1_inband_displacement"]["instance_resampling_95"]
    _has(_unit_with(notes, "K1 holds on a wide guard."),
         f"energy gap of {eg['new_per_seed'][0]:.4f} and a displacement error of "
         f"{dp['new_per_seed'][0]:.3f}",
         f"seeds {min(eg['base_per_seed']):.4f} to {max(eg['base_per_seed']):.4f} and "
         f"{min(dp['base_per_seed']):.3f} to {max(dp['base_per_seed']):.3f}",
         f"{_pct(ie['low'])} to {_pct(ie['high'])} and {_pct(idp['low'])} to {_pct(idp['high'])}")
    assert eg["new_per_seed"][0] == max(eg["new_per_seed"]) and dp["new_per_seed"][0] == max(dp["new_per_seed"])
    ba = v["beyond_amplitude"]["guard"]
    _has(_unit_with(notes, "Beyond the amplitude:"),
         f"{_pct(ba['rel_change'])} (tau {_pct(ba['threshold'], False)}), within the guard")
    mech = v["mechanism"]
    _has(_unit_with(notes, "The baseline's median c* on the fine set"),
         f"is {_seeds(mech['b']['fine']['c_star_median']['per_seed'])}, S's "
         f"{_seeds(mech['s']['fine']['c_star_median']['per_seed'])}",
         f"c_b is {mech['b']['remesh']['c_battery_median_by_lc']['0.0374']:.3f} and its predicted "
         f"energy norm {mech['b']['remesh']['u_norm_K_ratio_median_by_lc']['0.0374']:.3f}",
         f"S's {mech['s']['remesh']['c_battery_median_by_lc']['0.0374']:.3f} and "
         f"{mech['s']['remesh']['u_norm_K_ratio_median_by_lc']['0.0374']:.3f}")
    fp = v["fresh_baseline_vs_phase2b"]
    chk = v["checks"]
    _has(_unit_with(notes, "The fresh baseline against the Phase-2b seeds 0-2"),
         *(f"{_pct(fp[k]['rel_change'])} (tau {_pct(fp[k]['threshold'], False)})"
           for k in ("fine_displacement", "inband_energy_gap", "inband_displacement")),
         "reproduced E8's cell exactly in both arms")
    assert chk["b"]["p3_vs_e8_max_rel_dev"] == chk["s"]["p3_vs_e8_max_rel_dev"] == 0.0
    assert mech["b"]["reproduction_max_rel_dev"] == mech["s"]["reproduction_max_rel_dev"] == 0.0
    ra = v["r2a_beside"]
    _has(_unit_with(notes, "Beside R2a (SUPPORTED):"),
         f"{ra['fine_reduction_ratio']:.3f} of the bottleneck's (Sec. 5's {ra['c_star_k']:.3f})")
    _has(_unit_with(notes, "No report was refused. Three deviations"),
         f"driver {DRIVER}", "seed 5 resumed from epoch 161")
    lines = _status_lines()
    _, e161 = _estimate()
    gap = (_when(lines[10]) - e161).total_seconds() / 3600
    _has(_unit_with(notes, "`DEVIATIONS_R2B.md` (new)"), f"an estimated {gap:.0f} h before the session",
         "against RUNBOOK_R2B's 210 h of balance", "(the PI's account)",
         "which every baseline number the verdict reads comes from")
    days = {2: "two", 3: "three"}[round(gap / 24)]
    _has(_unit_with(notes, "**The return** (`records/wp9/r2b/return/`)"),
         f"on another host about {days} days later (estimated)",
         "no out-of-memory kill on the second host (the first host's count is not in the return)",
         "(the instance's weekly rental had run out, the PI stated)")
    _has(_unit_with(notes, "`RUNBOOK_R2B.md` and `RUNBOOK_FINE3D.md` Sec. 0d"),
         "corrected from 320 to 60")
    tests = [n for n in re.findall(r"^def (test_\w+)", Path(__file__).read_text(), re.M)]
    _has(_unit_with(notes, "`tests/test_r2b_returns.py` ("), f"({len(tests)} tests)")
