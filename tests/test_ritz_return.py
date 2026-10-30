"""cmame-paper Stage 15 (29 October 2026): the return of RUNBOOK_CMAME Sec. G (the
polynomial Ritz baseline and the enriched c*, run on 28 October 2026) as committed
under records/cmame/ritz/: the tarball as the operator sent it, its files other than
the per-instance rows unpacked beside it, and the facts that records/cmame/README.md
and the Stage 15 notes quote from them.

Sec. G3's repository side is run again here: every baseline summary and every
summary of the three-dimensional enriched arms is rebuilt from the tarball's rows and
the records, every arm's reading from its summaries, and each must equal the
committed file byte for byte. wp9's two arms read their reports from the box (the
configuration pins wp9-pool's records copies by SHA-256, which this branch does not
carry): their readings are rebuilt here, their summaries were rebuilt on receipt."""

import hashlib
import importlib.util
import json
import re
import shutil
import tarfile
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
RITZ = ROOT / "records" / "cmame" / "ritz"
TARBALL = RITZ / "ritz_return_20261029-1150.tgz"
RET = RITZ / "return"
README = ROOT / "records" / "cmame" / "README.md"
NOTES = ROOT / "BRANCH_NOTES_statics-paper.md"
RUNBOOK = ROOT / "RUNBOOK_STATICS.md"
CONFIG = ROOT / "configs" / "ritz_v1.json"
OLD_TIMING = ROOT / "records" / "cmame" / "timing"
TARBALL_SHA256 = "c0f5621fac38e8a946c34c7870a6c284305e2c2f0ccec29b24946a0f984c96af"
TARBALL_BYTES = 23818923
COMMIT = "0c1d59a6a973b8a6436269a1fbf708be43b8a59b"
TREE = "d36f70537aadbf7a98e1a265aebea6daaa111b0b"
HOST = "autodl-container-45e441a24a-99d5b40d"
FIRST_START = "2026-10-28T17:26:48Z"
F = ("energy_gap_rel", "disp_rel_l2", "vm_rel_l2", "peak_vm_rel_err", "crit_recall")
SETS = ("val3d", "fine3d", "h3d", "val2d", "h2d")
ARMS = ("b_n1024", "s_n1024", "phase2b", "phase2b_labels", "phase2b_mgn", "k3d_labels_knorm")
W9 = ("b_n1024", "s_n1024")
PAIRS = (("val3d", "phase2b:ar@1024"), ("val3d", "k3d:labels_knorm@1024"),
         ("fine3d", "phase2b:ar (zero-shot)"), ("h3d", "r1:ar"), ("h3d", "k3d:labels_knorm"),
         ("val2d", "cm2d:ar@1024"), ("val2d", "cm2d:labels_knorm@1024"), ("h2d", "r1:ar"))
"""The pairings the README quotes: the label-free transformers and L_K on every set."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _script(name: str):
    spec = importlib.util.spec_from_file_location(f"_ritz_return_{name}",
                                                  ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _members() -> dict:
    """The tarball's regular files: path below ritz_return/ -> bytes."""
    out = {}
    with tarfile.open(TARBALL, "r:gz") as t:
        for m in t.getmembers():
            assert not m.name.startswith("/") and ".." not in Path(m.name).parts, m.name
            assert m.isfile() or m.isdir(), m.name
            assert Path(m.name).parts[0] == "ritz_return", m.name
            if m.isfile():
                out[str(Path(m.name).relative_to("ritz_return"))] = t.extractfile(m).read()
    return out


@pytest.fixture(scope="module")
def members():
    return _members()


def _rows(data: bytes) -> list:
    return [json.loads(x) for x in data.decode().splitlines() if x.strip()]


# ------------------------------------------------------------ the quoted tables --

def g3(x: float) -> str:
    return f"{x:.3g}"


def _span(vals, fmt) -> str:
    lo, hi = fmt(min(vals)), fmt(max(vals))
    return lo if lo == hi else f"{lo} to {hi}"


def _pct(x: float) -> str:
    """A share in percent, to the unit; one strictly between 0 and 1 is never shown as
    0% or 100% (to one decimal then, or two)."""
    for nd in (0, 1, 2):
        txt = f"{100 * x:.{nd}f}"
        if not 0 < x < 1 or float(txt) not in (0.0, 100.0):
            break
    return txt + "%"


def ladder_table(ret: Path = RET) -> str:
    rows = ["| set | p | unknowns | relative energy gap | displacement error | von Mises error "
            "| peak von Mises error | critical-region recall |",
            "|---|---|---|---|---|---|---|---|"]
    for s in SETS:
        d = _json(ret / "baseline" / s / "summary.json")
        for p in map(str, d["ladder_p"]):
            lad = d["ladder"][p]
            rows.append(f"| {s} ({d['n']}) | {p} | {lad['k']} | "
                        + " | ".join(g3(lad["median"][f]) for f in F) + " |")
    return "\n".join(rows)


def pairing_table(ret: Path = RET) -> str:
    rows = ["| set | model (median energy gap; peak von Mises error) | p | relative energy gap "
            "| displacement error | von Mises error | peak von Mises error "
            "| critical-region recall |",
            "|---|---|---|---|---|---|---|---|"]
    for s, m in PAIRS:
        d = _json(ret / "baseline" / s / "summary.json")
        ps = list(map(str, d["ladder_p"]))
        e0 = d["ladder"][ps[0]]["paired"][m]
        head = (f"`{m}` ({_span([e['energy_gap_rel']['model_median'] for e in e0], g3)}; "
                f"{_span([e['peak_vm_rel_err']['model_median'] for e in e0], g3)})")
        for j, p in enumerate(ps):
            ent = d["ladder"][p]["paired"][m]
            cells = [_span([e[f]["ritz_better_share"] for e in ent], _pct) for f in F]
            rows.append(f"| {s if j == 0 else ''} | {head if j == 0 else ''} | {p} | "
                        + " | ".join(cells) + " |")
    return "\n".join(rows)


def _med(summary: dict, key: str):
    v = summary[key]
    return v["median"] if isinstance(v, dict) else v


def timing_table(ret: Path = RET, old: Path = OLD_TIMING) -> str:
    rt = {d: _json(ret / "timing" / f"ritz_timing_{d}.json")["results"] for d in ("3d", "2d")}
    ct = {d: _json(ret / "timing" / f"timing_{d}.json")["results"] for d in ("3d", "2d")}
    ot = {d: _json(old / f"timing_{d}.json")["results"] for d in ("3d", "2d")}
    cols = (("3d", "val", "3D validation"), ("3d", "fine", "3D fine set"),
            ("2d", "val", "2D validation"))

    def cell(d, s, key):
        new = ct[d][s]["summary"]
        txt = f"{g3(_med(new, key))} ({g3(_med(ot[d][s]['summary'], key))})"
        if key == "direct_s" and new["direct_n_solved"] != new["n_instances"]:
            txt += f", {new['direct_n_solved']} of {new['n_instances']} solved"
        return txt

    lines = ["| seconds, median (8 October 2026 in brackets) | "
             + " | ".join(c[2] for c in cols) + " |", "|---|" + "---|" * len(cols)]
    lines.append("| instances, median free dofs | " + " | ".join(
        f"{rt[d][s]['summary']['n']}, {rt[d][s]['summary']['n_free_dof_median']:,.0f}"
        for d, s, _ in cols) + " |")
    lines.append("| network inference, cold (GPU) | "
                 + " | ".join(cell(d, s, "surrogate_cold_s") for d, s, _ in cols) + " |")
    lines.append("| Ritz after assembly, by p (3D 6 to 9; 2D 6, 8) | " + " | ".join(
        ", ".join(g3(rt[d][s]["summary"]["p"][p]["ritz_s"])
                  for p in sorted(rt[d][s]["summary"]["p"], key=int)) for d, s, _ in cols) + " |")
    lines.append("| assembly of K (the repository's assembler) | " + " | ".join(
        g3(rt[d][s]["summary"]["assembly_s_median"]) for d, s, _ in cols) + " |")
    for key, name in (("direct_s", "direct solve"), ("cg_s", "conjugate gradients"),
                      ("cg_match_s", "conjugate gradients to the network's accuracy")):
        lines.append(f"| {name} | " + " | ".join(cell(d, s, key) for d, s, _ in cols) + " |")
    return "\n".join(lines)


def _inband(cfg: dict, s: str) -> bool:
    return bool(cfg["enriched"]["sets"][s]["inband"])


def enriched_table(ret: Path = RET) -> str:
    cfg = _json(CONFIG)
    rows = ["| arm | set | ratio per seed | per load case | reading of the arm |",
            "|---|---|---|---|---|"]
    word = {True: "complementary", False: "not complementary", None: "undecided"}
    for arm in ARMS:
        r = _json(ret / "enriched" / arm / "reading.json")
        sets = sorted(r["sets_complete"], key=lambda x: (not _inband(cfg, x), x))
        for j, s in enumerate(sets):
            sd = _json(ret / "enriched" / arm / s / "summary.json")["seeds"]
            key = "inband_ratio" if _inband(cfg, s) else "ood_peak_ratio"
            role = "in band, at most 0.8" if _inband(cfg, s) else "peak, at most 0.5"
            a = ", ".join(f"{sd[k][key]:.3f}" for k in sd)
            b = ", ".join(f"{sd[k]['per_load_case'][key]:.3f}" for k in sd)
            name = f"`{arm}`" + ("" if r["appendix"] else " (beyond Appendix 2)")
            rows.append(f"| {name if j == 0 else ''} | {s} ({role}) | {a} | {b} | "
                        f"{word[r['all_instances']['complementary']] if j == 0 else ''} |")
    return "\n".join(rows)


def per_load_case_reading(arm: str, ret: Path = RET):
    """Appendix 2's rule on the per-load-case medians (the sensitivity reading fixed on
    27 October 2026, before the run): in band, every seed at most 0.8 on every
    in-band set; out of distribution, every seed at most 0.5 on every other set."""
    cfg = _json(CONFIG)
    r = _json(ret / "enriched" / arm / "reading.json")
    ib, od = [], []
    for s in r["sets_complete"]:
        sd = _json(ret / "enriched" / arm / s / "summary.json")["seeds"]
        if _inband(cfg, s):
            ib += [sd[k]["per_load_case"]["inband_ratio"] <= 0.8 for k in sd]
        else:
            od += [sd[k]["per_load_case"]["ood_peak_ratio"] <= 0.5 for k in sd]
    inband = all(ib) if ib else None
    ood = all(od) if od else None
    if inband or ood:
        return True
    return False if (inband is False and ood is False) else None


# --------------------------------------------------------------- the return --

def test_the_tarball_is_the_one_received(members):
    data = TARBALL.read_bytes()
    assert len(data) == TARBALL_BYTES and _sha(data) == TARBALL_SHA256
    assert len(members) == 69
    assert sum(1 for k in members if k.endswith("/rows.jsonl")) == 19


def test_the_unpacked_files_are_the_tarballs(members):
    here = {str(p.relative_to(RET)): p.read_bytes() for p in RET.rglob("*") if p.is_file()}
    want = {k: v for k, v in members.items() if not k.endswith("/rows.jsonl")}
    assert sorted(here) == sorted(want) and len(here) == 50
    for k, v in want.items():
        assert here[k] == v, k


def test_provenance_lists_every_file(members):
    prov = members["provenance.txt"].decode().splitlines()
    assert prov[:5] == [f"HEAD {COMMIT}", f"tree {TREE}", "describe-all prereg-k3d-2-g0c1d59a",
                        f"hostname {HOST}", "--- files ---"]
    listed = {p.removeprefix("./"): h for h, p in (x.split("  ", 1) for x in prov[5:] if x)}
    assert listed == {k: _sha(v) for k, v in members.items() if k != "provenance.txt"}


def test_the_fifteen_steps_ran_once_each_in_order(members):
    g = RUNBOOK.read_text(encoding="utf-8").split("\n## G. ", 1)[1]
    logs = re.findall(r"^run (\S+\.log) python ", g, re.M)
    assert len(logs) == 15
    status = [x for x in members["status.txt"].decode().splitlines() if x.strip()]
    assert len(status) == 30
    times = []
    for k, log in enumerate(logs):
        m = re.fullmatch(rf"{re.escape(log)} start (\S+) {HOST}", status[2 * k])
        assert m, status[2 * k]
        times.append(m.group(1))
        assert status[2 * k + 1] == f"{log} exit=0"
    assert times[0] == FIRST_START and times == sorted(times)
    assert members["precheck.txt"].decode().splitlines() == [
        "Thu Oct 29 01:26:27 CST 2026", HOST, "0 %, 2 MiB"]
    mach = members["machine.txt"].decode().splitlines()
    assert mach[:3] == [f"HEAD {COMMIT}", f"tree {TREE}",
                        "NVIDIA GeForce RTX 5090, 595.71.05, 32607 MiB"]
    for want in (f"hostname {HOST}", "nproc 25", "96636764160", "oom 0", "oom_kill 0"):
        assert want in mach, want
    assert re.search(r"^806 passed, 3 deselected, 4 warnings in [0-9.]+s \(\d+:\d\d:\d\d\)$",
                     members["pytest.log"].decode(), re.M)
    cfg = _json(CONFIG)
    check = [json.loads(x) for x in members["check.log"].decode().splitlines()]
    assert [c.get("set") or c.get("arm") for c in check] == list(SETS) + list(ARMS)
    for c in check[:5]:
        assert c == {"set": c["set"], "n": cfg["baseline"]["sets"][c["set"]]["n"],
                     "files": "present", "inputs": "verified"}
    for c in check[5:]:
        a = cfg["enriched"]["arms"][c["arm"]]
        assert c["states_verified"] == 3 and list(c["sets"]) == list(a["sets"])
        assert all(c["sets"][s] == cfg["enriched"]["sets"][s]["n"] for s in a["sets"])
    for name, text in members.items():
        if name.endswith(".log"):
            body = text.decode()
            for bad in ("Traceback", "REFUSED", "NOT REPRODUCED", "NOT THE RECORDED INSTANCE"):
                assert bad not in body, (name, bad)


def test_the_rows_are_complete_in_order_and_hashed(members):
    cfg = _json(CONFIG)
    for k, data in members.items():
        if not k.endswith("/rows.jsonl"):
            continue
        rows = _rows(data)
        parts = Path(k).parts
        n = (cfg["baseline"]["sets"][parts[1]]["n"] if parts[0] == "baseline"
             else cfg["enriched"]["sets"][parts[2]]["n"])
        assert [r["i"] for r in rows] == list(range(n)), k
        assert len({r["file"] for r in rows}) == n, k
        summ = _json(RET / Path(k).parent / "summary.json")
        assert summ["rows_sha256"] == _sha(data), k


def test_the_identity_and_the_ritz_solutions_are_clean(members):
    for s in SETS:
        d = _json(RET / "baseline" / s / "summary.json")
        assert d["n_used"] == d["n"] and d["identity_failed"] == [] and d["size_mismatch"] == []
        assert d["identity_max_rel_diff"] <= 3e-12
        for lad in d["ladder"].values():
            assert lad["dropped_max"] == 0 and lad["worse_than_zero"]["worse"] == 0
    # the enriched reading's Ritz rows (p = 8) against the baseline's p = 8
    for s in ("val3d", "fine3d"):
        base = {r["file"]: r["ritz"]["8"]["load"] for r in
                _rows(members[f"baseline/{s}/rows.jsonl"])}
        worst = 0.0
        for arm in ARMS[2:]:
            for r in _rows(members[f"enriched/{arm}/{s}/rows.jsonl"]):
                assert r["ritz_dropped"] == 0
                for f in F:
                    a = np.asarray(base[r["file"]][f], float)
                    b = np.asarray(r["ritz"]["load"][f], float)
                    worst = max(worst, float(np.max(np.abs(a - b) / np.maximum(
                        np.maximum(np.abs(a), np.abs(b)), 1e-300))))
        assert worst <= 1e-9, (s, worst)
    for arm in ARMS:
        r = _json(RET / "enriched" / arm / "reading.json")
        assert r["sets_refused"] == {} and all(r["bound_ok"].values()), arm
        for s in r["sets_complete"]:
            sm = _json(RET / "enriched" / arm / s / "summary.json")
            assert sm["identity_failed"] == [] and sm["ritz_dropped_max"] == 0, (arm, s)
            for k, v in sm["seeds"].items():
                assert v["bound_ok"] is True and v["enriched_dropped_max"] == 0, (arm, s, k)


def _copy_set(members, rel: str, dst: Path) -> Path:
    dst.mkdir(parents=True)
    (dst / "rows.jsonl").write_bytes(members[f"{rel}/rows.jsonl"])
    shutil.copy(RET / rel / "summary.json", dst / "summary.json")
    return dst


def test_the_summaries_and_readings_rebuild_byte_for_byte(members, tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    base = _script("ritz_baseline")
    enr = _script("enriched_cstar")
    cfg = base.R.load_config(CONFIG)
    for s in SETS:
        d = _copy_set(members, f"baseline/{s}", tmp_path / "baseline" / s)
        rows = base.R.complete_lines(d / "rows.jsonl")
        assert [r["file"] for r in rows] == base.set_names(cfg, s)
        prev = _json(d / "summary.json")
        keep = {k: prev[k] for k in ("workers", "worker_threads", "machine", "code",
                                     "config_sha256") if k in prev}
        base.write_summary(cfg, s, d, rows, keep)
        assert (d / "summary.json").read_bytes() == (RET / "baseline" / s / "summary.json") \
            .read_bytes(), s
    for arm in ARMS:
        adir = tmp_path / "enriched" / arm
        sets = _json(RET / "enriched" / arm / "reading.json")["sets_complete"]
        for s in sets:
            d = _copy_set(members, f"enriched/{arm}/{s}", adir / s)
            if arm not in W9:
                enr.resummarise(cfg, arm, d)
                assert (d / "summary.json").read_bytes() == \
                    (RET / "enriched" / arm / s / "summary.json").read_bytes(), (arm, s)
        enr.R.write_json(adir / "reading.json", enr.reading(cfg, arm, adir))
        assert (adir / "reading.json").read_bytes() == \
            (RET / "enriched" / arm / "reading.json").read_bytes(), arm


def _beaten_everywhere(model: str) -> bool:
    """The class the README names: the supervised transformers trained on the
    displacement error, with or without the energy term, at every budget (zero-shot on
    the fine set included), the graph networks and the deterministic baselines."""
    head = re.split(r"[@ ]", model.split(":", 1)[1])[0]
    return head in ("labels", "labels_anchor", "mgn", "knn_field", "scale_aware_poly", "zero")


def test_the_ritz_gap_is_the_lower_against_the_class_the_readme_names():
    for s in SETS:
        d = _json(RET / "baseline" / s / "summary.json")
        ps = list(map(str, d["ladder_p"]))
        names = [m for m in d["ladder"][ps[0]]["paired"] if _beaten_everywhere(m)]
        assert len(names) >= 2, s
        for p in ps:
            for m in names:
                for e in d["ladder"][p]["paired"][m]:
                    assert e["energy_gap_rel"]["ritz_better_share"] == 1.0, (s, p, m)
    assert ("Against the supervised transformers trained on the displacement error, with "
            "or without the energy term (every budget, zero-shot on the fine set included), "
            "the graph networks and the deterministic baselines, the Ritz solution's "
            "relative energy gap is the lower on every instance at every p, on every set."
            ) in " ".join(_section().split())


def test_the_sensitivity_reading_agrees_with_the_reading():
    for arm in ARMS:
        r = _json(RET / "enriched" / arm / "reading.json")
        assert per_load_case_reading(arm) == r["all_instances"]["complementary"], arm
    got = {a: _json(RET / "enriched" / a / "reading.json")["all_instances"]["complementary"]
           for a in ARMS}
    assert got == {"b_n1024": False, "s_n1024": False, "phase2b": False,
                   "phase2b_labels": False, "phase2b_mgn": False, "k3d_labels_knorm": True}


# --------------------------------------------------------------- the quotes --

def _section() -> str:
    text = README.read_text(encoding="utf-8")
    start = text.index("## Ritz baseline and enriched c*: the run of 28 October 2026")
    nxt = text.find("\n## ", start + 1)
    return text[start:] if nxt < 0 else text[start:nxt]


def _stage_15() -> str:
    notes = NOTES.read_text(encoding="utf-8")
    start = notes.index("## Stage 15 (29 Oct 2026)")
    nxt = notes.find("\n## ", start + 1)
    return notes[start:] if nxt < 0 else notes[start:nxt]


def test_the_readme_quotes_the_return():
    sec = _section()
    for table in (ladder_table(), pairing_table(), timing_table(), enriched_table()):
        assert table in sec, table.splitlines()[0]
    flat = " ".join(sec.split())
    for want in (f"`{TARBALL_SHA256}`", "23,818,923 bytes", f"`{COMMIT[:7]}`", f"`{TREE}`",
                 "`prereg-k3d-2-g0c1d59a`", "806 passed, 3 deselected", FIRST_START,
                 "The 5,565 instances", "2.5e-12", "1.3e-10", "all 25 files"):
        assert want in flat, want
    worst = max(_json(RET / "baseline" / s / "summary.json")["identity_max_rel_diff"]
                for s in SETS)
    assert f"{worst:.1e}" == "2.5e-12"
    assert sum(_json(RET / "baseline" / s / "summary.json")["n"] for s in SETS) == 5565


def test_the_stage_15_notes_quote_the_return():
    st = " ".join(_stage_15().split())
    for want in (f"`{TARBALL_SHA256}`", f"`{COMMIT[:7]}`", "27 October 2026",
                 "29 October 2026", "per-load-case", "`tests/test_ritz_return.py`"):
        assert want in st, want
