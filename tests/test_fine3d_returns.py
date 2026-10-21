"""wp9-pool Stage 3 (21 October 2026): the fine3d return of RUNBOOK_FINE3D
Sec. 2 as committed under records/wp9/fine3d/return/, the adjudication's
verdict (records/wp9/fine3d/fine3d_verdict.json), and the facts that
DEVIATIONS_FINE3D.md, records/wp9/README.md and the Stage 3 notes quote from
them.

R2a, R3-E and R3-V are recomputed here from the reports, from PREREG_FINE3D
Sec. 6 and without the adjudicator's code; the adjudication itself is re-run
on the committed return and compared with the committed verdict. The
return's tarball is not committed: the README is the record of its
SHA-256."""

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
REC = ROOT / "records" / "wp9" / "fine3d"
RET = REC / "return"
VERDICT = REC / "fine3d_verdict.json"
LEDGER = ROOT / "DEVIATIONS_FINE3D.md"
README = ROOT / "records" / "wp9" / "README.md"
NOTES = ROOT / "BRANCH_NOTES_wp9-pool.md"
TAG = "prereg-fine3d"
STAMPED_COMMIT = "5a312232796e417bedac582aa77872922f84c07c"
STAMPED_TREE = "371b2913f93137fb63bd633f365eff810f8f2fe3"
TARBALL_SHA256 = "8c85f9cd71c401cabaad5ba94b244534b3c888c247038a5232fe478a3ed26bef"
STEPS = ("r2a_b_m1024", "r2a_s_m1024", "amp_r2a_b_m1024", "amp_r2a_s_m1024", "r3_eft_b16",
         "r3_lft_b16")
FILES = sorted([
    "provenance.txt", "session/status.txt", "session/pytest.log",
    *(f"session/{s}.log" for s in STEPS),
    "posthoc/amp_r2a_b_m1024.json", "posthoc/amp_r2a_s_m1024.json",
    *(f"{a}/{f}" for a in ("r2a_b_m1024", "r2a_s_m1024") for f in ("report.json", "RESULTS.md")),
    *(f"{a}/{f}" for a in ("r3_eft_b16", "r3_lft_b16")
      for f in ("report.json", "seed_0.json", "seed_1.json", "seed_2.json"))])
ADJUDICATION = [
    "--r2a-b", "records/wp9/fine3d/return/r2a_b_m1024/report.json",
    "--r2a-s", "records/wp9/fine3d/return/r2a_s_m1024/report.json",
    "--amp-b", "records/wp9/fine3d/return/posthoc/amp_r2a_b_m1024.json",
    "--amp-s", "records/wp9/fine3d/return/posthoc/amp_r2a_s_m1024.json",
    "--r3", "records/wp9/fine3d/return/r3_eft_b16/report.json",
    "--r3-labelled", "records/wp9/fine3d/return/r3_lft_b16/report.json",
    "--status", "records/wp9/fine3d/return/session/status.txt",
    "--phase2b", "records/wp8/e2/baseline/report_phase2b.json",
    "--e2", "records/wp8/e2/e2_m1024/report.json", "--prereg", "PREREG_FINE3D.md"]
"""The adjudication as the README gives it, without `--out`."""
ADJUDICATING = ("src/fejepa/analysis/adjudicate_fine3d.py", "src/fejepa/analysis/adjudicate_w9.py",
                "src/fejepa/analysis/adjudicate.py", "src/fejepa/metrics.py",
                "src/fejepa/report.py", "scripts/adjudicate_fine3d.py",
                "scripts/stamp_prereg_fine3d.py", "configs/r2a_s_m1024.json")
SEEDS_R3 = ("s0", "s1", "s2")


def _sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _r2a(arm):
    return _load(RET / f"r2a_{arm}_m1024" / "report.json")


def _r3(arm):
    return _load(RET / f"r3_{arm}_b16" / "report.json")


def _means(evals, metric) -> list:
    return [statistics.fmean(e["per_instance"][metric]) for e in evals]


def _p3(rep, which) -> list:
    """P3's zero-shot pass of an R2a report on the fine set or the validation
    split, per seed."""
    return rep["results"]["p3_transfer"]["metrics"]["ar"][which]["per_seed_eval"]


def _e8(rep) -> list:
    (pool,) = rep["results"]["e8"]["metrics"]["cells"]["ar"].values()
    return pool["per_seed_eval"]


def _r3_evals(rep, which) -> list:
    return [rep["per_seed"][s][which] for s in SEEDS_R3]


def _guard(new, base) -> dict:
    """PREREG_FINE3D Sec. 6: rel = mean(A)/mean(B) - 1, SE_rel = sqrt(s_A^2/3 +
    s_B^2/3) / mean(B) with sample SDs, tau = max(10%, 2 SE_rel)."""
    b = statistics.fmean(base)
    rel = statistics.fmean(new) / b - 1
    se = math.sqrt(statistics.stdev(new) ** 2 / 3 + statistics.stdev(base) ** 2 / 3) / b
    tau = max(0.10, 2 * se)
    return {"rel": rel, "se": se, "tau": tau, "lower": rel < -tau, "worse": rel > tau}


def _pct(x: float, sign: bool = True) -> str:
    """A relative change as the documents quote it: -94.0%, +1.1%, 13.7%."""
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


def _stage_3() -> str:
    notes = NOTES.read_text(encoding="utf-8")
    start = notes.index("## Stage 3 (21 October 2026)")
    nxt = notes.find("\n## ", start + 1)
    return notes[start:] if nxt < 0 else notes[start:nxt]


def _status() -> list:
    return [ln.split() for ln in (RET / "session" / "status.txt").read_text().splitlines()]


def _provenance() -> str:
    return (RET / "provenance.txt").read_text()


# ------------------------------------------------------------- the return --

def test_the_return_is_whole_and_hashed():
    got = sorted(str(p.relative_to(RET)) for p in RET.rglob("*") if p.is_file())
    assert got == FILES
    # one attempt per step, in the session's order, each exit 0
    assert [(s[0], s[1]) for s in _status()] == [
        (f"{st}.log", w) for st in STEPS for w in ("start", "exit=0")]
    prov = _provenance()
    # the SHA-256 of the reports and amplitude records the box listed are the committed files'
    listed = dict((m.group(2), m.group(1)) for m in re.finditer(
        r"^([0-9a-f]{64})\s+runs/fine3d/(\S+\.json)$", prov, re.M))
    assert sorted(listed) == sorted(
        f for f in FILES if f.endswith("report.json") or f.startswith("posthoc/"))
    for rel, sha in listed.items():
        assert _sha(RET / rel) == sha, rel
    # the states' SHA-256 the box listed are those the reports record
    pts = dict((m.group(2), m.group(1)) for m in re.finditer(
        r"^([0-9a-f]{64})\s+runs/(\S+\.pt)$", prov, re.M))
    assert len(pts) == 3 + 3 + 3 + 3 + 3
    for arm in ("b", "s"):
        rep = _r2a(arm)
        assert rep["provenance"]["git"] == TAG and rep["solve_ledger"]["total"] == 0
        assert rep["provenance"]["seeds"] == [3, 4, 5]
        states = rep["results"]["e8"]["metrics"]["d9_restart"]["ar_states"]
        for k in (3, 4, 5):
            assert states[f"s{k}"]["sha256"] == \
                pts[f"fine3d/r2a_{arm}_m1024/e8_states/ar_p1024_s{k}.pt"]
    # the box listed R3's directories with each file's size: the per-seed result
    # files, whose SHA-256 it did not list, have those sizes
    sizes, where = {}, None
    for line in prov.split("--- states ---\n")[1].splitlines():
        d = re.match(r"^runs/(fine3d/\S+)/:$", line)
        f = re.match(r"^-\S+\s+\d+\s+\S+\s+\S+\s+(\d+)\s+\S+\s+\S+\s+\S+\s+(\S+)$", line)
        if d:
            where = d.group(1)
        elif f and where:
            sizes[f"{where}/{f.group(2)}"] = int(f.group(1))
    for arm in ("eft", "lft"):
        for name in ("report.json", "seed_0.json", "seed_1.json", "seed_2.json"):
            assert (RET / f"r3_{arm}_b16" / name).stat().st_size == \
                sizes[f"fine3d/r3_{arm}_b16/{name}"], (arm, name)
    host = re.search(r"^hostname (\S+)$", prov, re.M).group(1)
    driver = re.search(r"^NVIDIA GeForce RTX 5090, ([0-9.]+), ", prov, re.M).group(1)
    for arm in ("eft", "lft"):
        rep = _r3(arm)
        assert rep["provenance"]["git"] == TAG
        for k, s in enumerate(SEEDS_R3):
            seed = rep["per_seed"][s]
            assert seed == _load(RET / f"r3_{arm}_b16" / f"seed_{k}.json")
            assert seed["git"] == TAG
            assert seed["state"]["sha256"] == pts[f"fine3d/r3_{arm}_b16/{arm}_b16_s{k}.pt"]
            assert seed["source_state"]["sha256"] == pts[f"phase2/e8_states/ar_p1024_s{k}.pt"]
            assert seed["train"]["resumed_from_epoch"] is None
            m = seed["machine"]
            assert m["resumed_on"] == []
            assert m["start"] == m["end"] == {"host": host, "gpu_driver": driver}
    assert (host, driver) == ("autodl-container-45e441a24a-99d5b40d", "595.71.05")
    assert re.search(r"^oom_kill 0$", prov, re.M)
    assert re.search(r"^torch 2\.12\.1\+cu130 True gmsh 4\.15\.2$", prov, re.M)


def test_the_suite_the_session_ran_is_the_stamped_commits():
    last = (RET / "session" / "pytest.log").read_text().strip().splitlines()[-1]
    m = re.match(r"(\d+) passed, 1 skipped, \d+ warnings in ", last)
    assert m, last
    notes = NOTES.read_text(encoding="utf-8")
    r5 = notes[notes.index("## Stage 2, r5"):]
    stamped = int(re.search(r"^- Suite (\d+)", r5, re.M).group(1))
    assert int(m.group(1)) + 1 == stamped == 705


# ------------------------------------------------------------ the verdict --

def test_the_verdict_reproduces_from_the_committed_return(tmp_path):
    out = tmp_path / "verdict.json"
    res = subprocess.run([sys.executable, "scripts/adjudicate_fine3d.py", *ADJUDICATION,
                          "--out", str(out)], cwd=ROOT, capture_output=True, text=True,
                         timeout=600)
    assert res.returncode == 0, res.stderr[-3000:]
    fresh, committed = _load(out), _load(VERDICT)
    # the committed verdict was written by the stamped adjudicating code, in a clean
    # checkout of the stamp, with every input named relative to the repository
    adj = committed["adjudicator"]
    assert adj["git"] == TAG and adj["tag"] == TAG and adj["tag_available"]
    assert adj["differs_from_tag"] == [] and adj["prereg_is_tags"]
    assert adj["prereg_self_hash_ok"] and adj["prereg_is_repository_file"]
    assert adj["prereg_file"] == "PREREG_FINE3D.md"
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
    assert committed["deviations"] == [] and committed["notes"] == []
    assert committed["attempts"] == {s: 1 for s in STEPS}
    assert committed["last_exits"] == {s: 0 for s in STEPS}


def test_r2a_recomputed_from_the_reports():
    v = _load(VERDICT)["R2a"]
    b, s = _r2a("b"), _r2a("s")
    for rep in (b, s):
        for evals in (_p3(rep, "fine"), _p3(rep, "inband"), _e8(rep)):
            assert len(evals) == 3
            for e in evals:
                assert all(len(e["per_instance"][m]) == 256 for m in e["per_instance"])
                assert all(math.isfinite(x) for m in e["per_instance"]
                           for x in e["per_instance"][m])

    def ratio(rep):      # Sec. 5: per seed, P3's fine mean over P3's in-band mean
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
        assert g["tau"] == pytest.approx(c["threshold"], abs=1e-12), key
        assert (g["lower"], g["worse"]) == (c["lower"], c["worse"]), key
        assert c["new_per_seed"] == pytest.approx(new, abs=1e-15), key
        assert c["base_per_seed"] == pytest.approx(base, abs=1e-15), key
    fine = _guard(*conds["fine_displacement"])
    supported = (fine["lower"] and _guard(*conds["fine_over_inband_ratio"])["lower"]
                 and not _guard(*conds["K1_inband_energy_gap"])["worse"]
                 and not _guard(*conds["K1_inband_displacement"])["worse"])
    assert supported and v["verdict"] == "SUPPORTED"
    # the R2b rule: R2a SUPPORTED and the fine displacement error's rel <= -45%
    assert fine["rel"] <= -0.45 + 1e-12
    assert v["r2b"] == {"recommended": True,
                        "why": f"R2a SUPPORTED and S's fine displacement error rel "
                               f"{fine['rel'] * 100:.2f}% <= -45%"}


def test_r3_recomputed_from_the_reports():
    v = _load(VERDICT)["R3"]
    e, lab = _r3("eft"), _r3("lft")
    for rep in (e, lab):
        for which in ("fine", "inband"):
            for ev in _r3_evals(rep, which):
                assert all(len(ev["per_instance"][m]) == 256 for m in ev["per_instance"])
    for name, metric in (("R3-E", "energy_gap_rel"), ("R3-V", "vm_rel_l2")):
        new, base = _means(_r3_evals(e, "fine"), metric), _means(_r3_evals(lab, "fine"), metric)
        g, c = _guard(new, base), v["verdicts"][name]
        assert c["metric"] == metric
        assert g["rel"] == pytest.approx(c["guard"]["rel_change"], abs=1e-12)
        assert g["tau"] == pytest.approx(c["guard"]["threshold"], abs=1e-12)
        assert not g["lower"] and not g["worse"]
        assert c["verdict"] == "NOT SUPPORTED"
        # every seed's energy arm is lower than its labelled arm
        assert all(n < r for n, r in zip(new, base))
    # the labelled arm against the Phase-2b record of the same fine-tuning (Sec. 7)
    p2b = _load(ROOT / "records" / "wp8" / "e2" / "baseline" / "report_phase2b.json")
    rec = p2b["results"]["p3_transfer"]["metrics"]["fewshot"]["16"]["finetune"]["per_seed_eval"]
    for metric, x in v["readings"]["labelled_vs_record"].items():
        assert x["guard"]["base_per_seed"] == \
            pytest.approx(_means(rec, metric), abs=1e-15), metric
        assert x["guard"]["new_per_seed"] == \
            pytest.approx(_means(_r3_evals(lab, "fine"), metric), abs=1e-15)
        assert x["new_is"] == "within the guard", metric
    assert v["readings"]["record_flags"] == [] and v["deviations"] == [] and v["notes"] == []


# ------------------------------------------------------- the quoted facts --

def test_the_ledger_quotes_the_records():
    led = LEDGER.read_text(encoding="utf-8")
    st = _status()
    first, last = st[0], st[-1]
    assert (first[2], first[3][:5]) == ("2026-10-20", "01:29")
    assert (last[2], last[3][:5]) == ("2026-10-21", "16:35")
    _has(_unit_with(led, "This visit ran the fine3d session first"),
         "01:29 on 20 October to 16:35 on 21 October, box time (+0800)",
         f"after the session's last step ended ({last[3]})",
         "10:02 UTC, 18:02 box time")
    lft = [s for s in st if s[0] == "r3_lft_b16.log" and s[1] == "start"]
    assert len(lft) == 1 and (lft[0][2], lft[0][3]) == ("2026-10-21", "06:25:10")
    prov = _provenance()
    head = re.search(r"^HEAD ([0-9a-f]{40})$", prov, re.M).group(1)
    tree = re.search(r"^tree ([0-9a-f]{40})$", prov, re.M).group(1)
    desc = re.search(r"^describe (\S+)$", prov, re.M).group(1)
    assert re.search(r"^tags $", prov, re.M)
    status = prov.split("--- git status --porcelain ---\n")[1].split("\ntorch ")[0]
    assert len(status.splitlines()) == 1 and status.startswith("?? ")
    f2 = _unit_with(led, "In this return they name commit")
    _has(f2, f"`{head}`", f"`{tree}`", f"`{desc}`", "no tag", "one untracked file",
         f"`{STAMPED_COMMIT}`", f"`{STAMPED_TREE}`")
    assert desc == f"prereg-cm2d-2-g{head[:7]}" and head != STAMPED_COMMIT
    _has(f2, "two commits after branch cmame-paper's tag `prereg-cm2d`",
         "after 06:25:10 on 21 October, box time (the session script's last check of "
         "the commit, before R3's labelled arm)")
    code = _unit_with(led, "What the records show about the session's code.")
    _has(code, "`704 passed, 1 skipped`", "torch 2.12.1+cu130 with CUDA and gmsh 4.15.2",
         "RTX 5090, driver 595.71.05", "25 CPUs (Xeon Platinum 8470Q)", "`oom_kill 0`",
         "the four reports and the two amplitude records")
    assert re.search(r"^nproc 25$", prov, re.M)
    assert "Model name:                         Intel(R) Xeon(R) Platinum 8470Q" in prov
    assert not any("STOP" in " ".join(s) for s in st)
    _has(_unit_with(led, "Companion to `PREREG_FINE3D.md`"), "self-hash `534f5dba...`")
    stamped = (ROOT / "PREREG_FINE3D.md").read_text().strip().splitlines()[-1]
    assert stamped.startswith("PREREG_FINE3D_SHA256 = 534f5dba")


def test_the_readme_quotes_the_records():
    text = README.read_text(encoding="utf-8")
    sec = text[text.index("## fine3d: the box's return (Stage 3"):]
    _has(_unit_with(sec, "| `fine3d/return/` |"), f"`{TARBALL_SHA256}`")
    _has(_unit_with(sec, "The trained and fine-tuned states stay on the box"),
         "from 01:29 on 20 October to 16:35 on 21 October (box time, +0800",
         "`autodl-container-45e441a24a-99d5b40d`, 595.71.05", "`704 passed, 1 skipped`")
    # the command block is the test's adjudication
    block = re.search(r"\n    python scripts/adjudicate_fine3d\.py \\\n((?:        .*\n)+)", sec)
    args = " ".join(x.strip().rstrip("\\").strip() for x in block.group(1).splitlines()).split()
    assert args == ADJUDICATION + ["--out", "records/wp9/fine3d/fine3d_verdict.json"]
    v = _load(VERDICT)
    c = v["R2a"]["conditions"]

    def cond(key, fmt=".3f"):
        x = c[key]
        return (f"{_seeds(x['base_per_seed'], fmt)} and {_seeds(x['new_per_seed'], fmt)}, "
                f"rel {_pct(x['rel_change'])}, tau {_pct(x['threshold'], False)}")

    r2a = _unit_with(sec, "**R2a: SUPPORTED.**")
    assert v["R2a"]["verdict"] == "SUPPORTED"
    rsm = v["R2a"]["values"]
    _has(r2a, cond("fine_displacement"), cond("fine_over_inband_ratio", ".2f"),
         cond("K1_inband_energy_gap", ".4f"), cond("K1_inband_displacement"),
         f"(the ratio of the seed means {rsm['b']['ratio_of_seed_means']:.2f} and "
         f"{rsm['s']['ratio_of_seed_means']:.2f})")
    _has(_unit_with(sec, "**R2b: recommended**"),
         f"lower by {-c['fine_displacement']['rel_change'] * 100:.1f}%, beyond the line of 45%")
    r3 = v["R3"]
    for name, needle in (("R3-E", "**R3-E: NOT SUPPORTED.**"),
                         ("R3-V", "**R3-V: NOT SUPPORTED.**")):
        g = r3["verdicts"][name]["guard"]
        assert r3["verdicts"][name]["verdict"] == "NOT SUPPORTED"
        _has(_unit_with(sec, needle), _seeds(g["base_per_seed"]), _seeds(g["new_per_seed"]),
             f"rel {_pct(g['rel_change'])}, tau {_pct(g['threshold'], False)}")
    assert min(r3["verdicts"][k]["guard"]["threshold"] for k in ("R3-E", "R3-V")) > 1
    _has(_unit_with(sec, "neither R3 verdict could have been SUPPORTED"),
         "With tau above 100%", "rel cannot fall below -100%")
    beside = _unit_with(sec, "Beside R3-E and R3-V (Sec. 6-7)")
    d = r3["readings"]["vs_labelled"]["disp_rel_l2"]
    _has(beside, f"{_seeds(d['guard']['base_per_seed'])} and {_seeds(d['guard']['new_per_seed'])}",
         f"rel {_pct(d['guard']['rel_change'])}, tau {_pct(d['guard']['threshold'], False)}, "
         f"within the guard", "within the guard on every metric")
    assert d["new_is"] == "within the guard"
    # the labelled arm against the Phase-2b record: every metric, its rel, tau and seeds
    lr = r3["readings"]["labelled_vs_record"]
    assert r3["readings"]["record_flags"] == []
    lines = sec.splitlines()
    for metric, label in (("energy_gap_rel", "relative energy gap"),
                          ("disp_rel_l2", "displacement error"),
                          ("vm_rel_l2", "von Mises error"),
                          ("peak_vm_rel_err", "peak von Mises error"),
                          ("crit_recall", "critical-region recall")):
        g = lr[metric]["guard"]
        assert lr[metric]["new_is"] == "within the guard", metric
        row = (f"| {label} | {_seeds(g['base_per_seed'])} | {_seeds(g['new_per_seed'])} | "
               f"{_pct(g['rel_change'])} | {_pct(g['threshold'], False)} |")
        assert lines.count(row) == 1, row
    assert len(lr) == 5
    # every tau quoted in the section is 2 SE_rel (each above the 10% floor)
    assert c["failing"] == [] and c["verdict"] == "SUPPORTED"
    taus = [c[k]["threshold"] for k in ("fine_displacement", "fine_over_inband_ratio",
                                        "K1_inband_energy_gap", "K1_inband_displacement")]
    taus += [r3["verdicts"][k]["guard"]["threshold"] for k in ("R3-E", "R3-V")]
    taus += [d["guard"]["threshold"]] + [x["guard"]["threshold"] for x in lr.values()]
    assert min(taus) > 0.10
    _has(_unit_with(sec, "The verdicts of PREREG_FINE3D Sec. 6"),
         "every tau here is 2 SE_rel")


def test_the_stage_3_notes_quote_the_verdict():
    notes = _stage_3()
    v = _load(VERDICT)
    c = v["R2a"]["conditions"]
    _has(_unit_with(notes, "**R2a SUPPORTED.**"),
         f"fine displacement error {_pct(c['fine_displacement']['rel_change'])} "
         f"(tau {_pct(c['fine_displacement']['threshold'], False)})",
         f"ratio {_pct(c['fine_over_inband_ratio']['rel_change'])} "
         f"(tau {_pct(c['fine_over_inband_ratio']['threshold'], False)}; its mean over the "
         f"seeds {c['fine_over_inband_ratio']['base_mean']:.2f} to "
         f"{c['fine_over_inband_ratio']['new_mean']:.2f}, the ratio of the seed means "
         f"{v['R2a']['values']['b']['ratio_of_seed_means']:.2f} to "
         f"{v['R2a']['values']['s']['ratio_of_seed_means']:.2f})",
         f"energy gap {_pct(c['K1_inband_energy_gap']['rel_change'])}",
         f"displacement error {_pct(c['K1_inband_displacement']['rel_change'])}")
    _has(_unit_with(notes, "**R2b recommended**"), "The PI decided on 21 October 2026 to run R2b")
    r3 = v["R3"]
    ge, gv = r3["verdicts"]["R3-E"]["guard"], r3["verdicts"]["R3-V"]["guard"]
    _has(_unit_with(notes, "**R3-E and R3-V NOT SUPPORTED.**"),
         f"energy gap {_pct(ge['rel_change'])} (tau {_pct(ge['threshold'], False)})",
         f"von Mises error {_pct(gv['rel_change'])} (tau {_pct(gv['threshold'], False)})",
         "With tau above 100%, neither could have been SUPPORTED")
    assert min(ge["threshold"], gv["threshold"]) > 1
    # R2a's readings
    rob = v["R2a"]["robustness"]["fine_displacement"]
    med, rs = rob["medians"], rob["instance_resampling_95"]
    mech = v["R2a"]["mechanism"]
    e2 = v["R2a"]["fresh_baseline_vs_e2"]
    unit = _unit_with(notes, "R2a. On per-seed medians")
    _has(unit, f"reads {_pct(med['rel_change'])} (tau {_pct(med['threshold'], False)})",
         f"is {_pct(rs['low'])} to {_pct(rs['high'])}",
         f"fine set is {_seeds(mech['b']['fine']['c_star_median']['per_seed'])}, S's "
         f"{_seeds(mech['s']['fine']['c_star_median']['per_seed'])}",
         f"in band {_seeds(mech['b']['inband']['c_star_median']['per_seed'])} and "
         f"{_seeds(mech['s']['inband']['c_star_median']['per_seed'])}",
         f"fine displacement error {_pct(e2['fine_displacement']['rel_change'])} "
         f"(tau {_pct(e2['fine_displacement']['threshold'], False)})",
         f"in-band energy gap {_pct(e2['inband_energy_gap']['rel_change'])} "
         f"(tau {_pct(e2['inband_energy_gap']['threshold'], False)})",
         f"in-band displacement error {_pct(e2['inband_displacement']['rel_change'])} "
         f"(tau {_pct(e2['inband_displacement']['threshold'], False)})")
    assert e2["flags"] == [] and not any(e2[k]["lower"] or e2[k]["worse"]
                                         for k in e2 if k != "flags")
    chk = v["R2a"]["checks"]
    _has(unit, f"{chk['b']['p3_vs_e8_max_rel_dev']:.1e} and {chk['s']['p3_vs_e8_max_rel_dev']:.1e}",
         f"{mech['b']['reproduction_max_rel_dev'] * 100:.2f}% and "
         f"{mech['s']['reproduction_max_rel_dev'] * 100:.3f}%")
    # R3's readings
    rd = r3["readings"]
    pe = rd["vs_labelled"]["energy_gap_rel"]["paired_per_seed_rel"]
    pv = rd["vs_labelled"]["vm_rel_l2"]["paired_per_seed_rel"]
    assert all(x < 0 for x in pe + pv)
    unit = _unit_with(notes, "R3. Every seed's energy arm is lower")
    amp = rd["amplitude"]["labelled"]["fine"]["c_star_median"]
    rme, rmv = rd["robustness"]["R3-E"], rd["robustness"]["R3-V"]
    _has(unit, "energy gap by {:.1f}%, {:.1f}% and {:.1f}%".format(*(-x * 100 for x in pe)),
         "von Mises error by {:.1f}%, {:.1f}% and {:.1f}%".format(*(-x * 100 for x in pv)),
         f"fine energy gap {ge['base_per_seed'][1]:.3f} against {ge['base_per_seed'][0]:.3f} "
         f"and {ge['base_per_seed'][2]:.3f}",
         f"von Mises error {gv['base_per_seed'][1]:.3f} against {gv['base_per_seed'][0]:.3f} "
         f"and {gv['base_per_seed'][2]:.3f}",
         f"median c* {amp[1]:.3f} against {amp[0]:.3f} and {amp[2]:.3f}",
         f"R3-E reads {_pct(rme['medians']['rel_change'])} "
         f"(tau {_pct(rme['medians']['threshold'], False)})",
         f"R3-V {_pct(rmv['medians']['rel_change'])} "
         f"(tau {_pct(rmv['medians']['threshold'], False)})",
         f"{_pct(rme['instance_resampling_95']['low'])} to "
         f"{_pct(rme['instance_resampling_95']['high'])} and "
         f"{_pct(rmv['instance_resampling_95']['low'])} to "
         f"{_pct(rmv['instance_resampling_95']['high'])}")
    unit = _unit_with(notes, "The labelled arm against the Phase-2b record of the same")
    lr = rd["labelled_vs_record"]
    _has(unit, "the fine energy gap {}, {} and {}".format(
             *(_pct(x) for x in lr["energy_gap_rel"]["paired_per_seed_rel"])),
         "the displacement error {}, {} and {}".format(
             *(_pct(x) for x in lr["disp_rel_l2"]["paired_per_seed_rel"])))
    er = rd["energy_vs_record"]
    for metric, words in (("energy_gap_rel", "the fine energy gap"),
                          ("vm_rel_l2", "the von Mises error"),
                          ("peak_vm_rel_err", "the peak von Mises error"),
                          ("disp_rel_l2", "the displacement error")):
        g = er[metric]["guard"]
        _has(unit, f"{words} {_pct(g['rel_change'])} (tau {_pct(g['threshold'], False)})")
    assert [er[m]["new_is"] for m in ("energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err",
                                      "disp_rel_l2")] == ["better"] * 3 + ["within the guard"]
    unit = _unit_with(notes, "In band, after fine-tuning at the fine mesh")
    ib = rd["inband_vs_before"]

    def move(arm, metric):
        g = ib[arm][metric]["guard"]
        return f"{g['base_mean']:.3f} to {g['new_mean']:.3f}"

    _has(unit, f"energy arm's displacement error {move('energy', 'disp_rel_l2')}",
         f"von Mises error {move('energy', 'vm_rel_l2')}",
         f"labelled arm's displacement error {move('labelled', 'disp_rel_l2')}",
         f"energy gap {move('labelled', 'energy_gap_rel')} (seed 1: "
         f"{ib['labelled']['energy_gap_rel']['guard']['new_per_seed'][1]:.3f})")
    assert [ib["energy"][m]["new_is"] for m in ("disp_rel_l2", "vm_rel_l2")] == ["worse"] * 2
    assert ib["labelled"]["disp_rel_l2"]["new_is"] == "worse"
    assert ib["labelled"]["energy_gap_rel"]["new_is"] == "within the guard"
