#!/usr/bin/env python3
"""R2b: adjudicate PREREG_R2B (Sec. 5-7) from the box's return.

R2b reads its two reports (`b`: the Phase-2b label-free transformer trained
again on the fresh seeds 3-5; `s`: the same with S) and, for the mechanism
readings only, their post-hoc amplitude records (scripts/posthoc_amplitude.py).
The Phase-2b report (the configuration both arms are generated from, and the
seeds 0-2 the fresh baseline is read beside) and fine3d's verdict file (R2a,
read beside R2b) are the records copies, each checked by SHA-256; the stamped
CONFIG_SHA256 lines are read from PREREG_R2B.md, and both reports must have
run on the tag. The rule is R2a's (fejepa.analysis.adjudicate_fine3d, whose
functions are used as they are: R2b changes no source). A report that is not
given, not in the return or not readable leaves R2b NOT EVALUATED; an
unreadable amplitude record leaves the mechanism readings unevaluated.
Secondary readings never block the verdict: one that cannot be computed is
reported as not evaluated. The verdict file records the inputs' SHA-256, the
session's attempts and each step's last exit (with `--status`), and the
adjudicating code: its `git describe`, its files' SHA-256 and whether they
and the pre-registration read are the tag's. A difference, a tag that cannot
be read, a footer that does not verify, a status file not given or not in
the return, repeated or missing steps and a step whose last attempt did not
exit 0 are deviations; "deviations" holds them with R2b's own, and "notes"
the uninformative note and the flags against the Phase-2b seeds 0-2.

    python scripts/adjudicate_r2b.py \
        --r2b-b <return>/r2b_b/report.json --r2b-s <return>/r2b_s/report.json \
        --amp-b <return>/posthoc/amp_r2b_b.json --amp-s <return>/posthoc/amp_r2b_s.json \
        --status <return>/session/status.txt \
        --out records/wp9/r2b/r2b_verdict.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fejepa.analysis import adjudicate_fine3d as A  # noqa: E402
from fejepa.analysis.adjudicate import require_stamped  # noqa: E402
from fejepa.analysis.adjudicate_w9 import _soft, config_diff, guard  # noqa: E402
from fejepa.report import config_sha256  # noqa: E402

PREREG_NAME = "PREREG_R2B.md"
TAG = "prereg-r2b"
LABELS = {"b": "r2b_b", "s": "r2b_s"}
PHASE2B = "records/wp8/e2/baseline/report_phase2b.json"
PHASE2B_CONFIG_SHA256 = "316f5e6e282db9c11509d8d1d2ed54d229ded9d6367c63b3a13abd7709ba4899"
"""PREREG_PHASE2B's stamped configuration, from which both arms are generated."""
FINE3D_VERDICT = "records/wp9/fine3d/fine3d_verdict.json"
FINE3D_VERDICT_SHA256 = "9c93a1a6ca6bd20a3a1827efe722f1f712cb07e4e7992786fb0d7b6d1cfd5693"
"""fine3d's verdict file (wp9-pool Stage 3): R2a, read beside R2b."""
AR_ONLY_KEYS = {("experiments", "e8", "ar_only"), ("experiments", "e6", "enabled"),
                ("experiments", "wp6", "enabled"),
                ("experiments", "p3_transfer", "fewshot_budgets"),
                ("experiments", "p3_transfer", "naive_budget")}
"""E2's AR-only edit of the Phase-2b experiments (scripts/make_e_series_configs.py)."""
ALLOWED_DIFF = {("_comment",), ("out",), ("prereg_file",), ("experiments", "e8", "seed_offset"),
                *AR_ONLY_KEYS, *A.S_KEYS}
"""The keys in which an R2b configuration may differ from the Phase-2b
configuration (PREREG_R2B Sec. 2); the guard is on in both."""
FRESH_SEEDS = [3, 4, 5]
C_STAR_K = 0.8697758470700758
"""PREREG_R2B Sec. 5: the ratio of c*'s fine reductions on the transformer and
the bottleneck (records/wp9/r2b/simulations.json, `k`), beside the ratio S's
fine reductions on the two show."""
STEPS = ("r2b_s", "amp_r2b_s", "r2b_b", "amp_r2b_b")
ADJ_FILES = ("scripts/adjudicate_r2b.py", "scripts/adjudicate_fine3d.py",
             "scripts/stamp_prereg_r2b.py", "src/fejepa/analysis/adjudicate_fine3d.py",
             "src/fejepa/analysis/adjudicate_w9.py", "src/fejepa/analysis/adjudicate.py",
             "src/fejepa/metrics.py", "src/fejepa/report.py", "configs/r2b_s.json")
"""The adjudicating code and what it reads here (S's factor): compared with
the tag's copies; the pre-registration read is compared with the tag's
PREREG_R2B.md."""
CONDITIONS = (("fine_displacement", "fine_disp"), ("fine_over_inband_ratio", "ratio"),
              ("K1_inband_energy_gap", "inband_egap"), ("K1_inband_displacement", "inband_disp"))
"""Each condition of the verdict and the per-seed values it reads (A.r2a_values)."""


def _sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ checks --

def check_arm(role: str, rep: dict, p2b: dict, prereg_entries: dict | None,
              expected_git: str | None, s_factor: float | None) -> dict:
    """Refuse an R2b report that is not what PREREG_R2B stamped for `role`
    ('b' or 's'); return what the record needs."""
    label = LABELS[role]
    require_stamped(rep, f"R2b {role} report", PREREG_NAME)
    cfg = rep["config"]
    if config_sha256(cfg) != rep["provenance"].get("config_sha256"):
        raise ValueError(f"the R2b {role} report's configuration does not hash to its recorded "
                         "config_sha256")
    if Path(cfg["out"]).parent.name != label:
        raise ValueError(f"the R2b {role} report is {Path(cfg['out']).parent.name}'s, "
                         f"not {label}'s")
    if p2b["provenance"]["config_sha256"] != PHASE2B_CONFIG_SHA256:
        raise ValueError("the Phase-2b report is not the stamped Phase-2b run")
    diff = config_diff(cfg, p2b["config"])
    extra = diff - ALLOWED_DIFF
    if extra:
        raise ValueError(f"the R2b {role} configuration differs from the Phase-2b configuration "
                         f"beyond PREREG_R2B Sec. 2: "
                         f"{sorted('.'.join(map(str, p)) for p in extra)}")
    ex = cfg["experiments"]
    if not (ex["e8"].get("ar_only") is True and ex["e6"].get("enabled") is False
            and ex["wp6"].get("enabled") is False
            and ex["p3_transfer"].get("fewshot_budgets") == []
            and int(ex["p3_transfer"].get("naive_budget", -1)) == 0):
        raise ValueError(f"the R2b {role} configuration is not the AR-only form of PREREG_R2B "
                         "Sec. 2")
    if int(ex["e8"].get("seed_offset", 0) or 0) != FRESH_SEEDS[0]:
        raise ValueError(f"the R2b {role} configuration's seed offset is not {FRESH_SEEDS[0]}")
    m = cfg["model"]
    has_s = bool(diff & A.S_KEYS)
    if role == "b" and has_s:
        raise ValueError("the R2b baseline carries S's keys")
    if role == "s" and not (m.get("decode_scale") == "l1"
                            and (m.get("features") or {}).get("load_density") is True
                            and (s_factor is None
                                 or float(m.get("decode_scale_factor")) == float(s_factor))):
        raise ValueError(f"the R2b S configuration is not S (decode_scale "
                         f"{m.get('decode_scale')!r}, factor {m.get('decode_scale_factor')!r}, "
                         f"load_density "
                         f"{(m.get('features') or {}).get('load_density')!r})")
    if prereg_entries is not None:
        want = prereg_entries.get(label)
        if want is None or rep["prereg"]["config_sha256"] != want:
            raise ValueError(f"the R2b {role} report's verified hash is not "
                             f"PREREG_R2B's CONFIG_SHA256[{label}]")
    prov = rep["provenance"]
    if expected_git is not None and prov.get("git") != expected_git:
        raise ValueError(f"the R2b {role} report ran on {prov.get('git')!r}, not "
                         f"{expected_git!r}")
    if [d.get("manifest_sha256") for d in prov["datasets"]] != \
            [d.get("manifest_sha256") for d in p2b["provenance"]["datasets"]]:
        raise ValueError(f"the R2b {role} report ran on another corpus")
    if [int(s) for s in prov.get("seeds")] != FRESH_SEEDS or \
            [int(s) for s in rep["results"]["p3_transfer"]["protocol"]["seeds"]] != FRESH_SEEDS:
        raise ValueError(f"the R2b {role} report's seeds are {prov.get('seeds')} (P3: "
                         f"{rep['results']['p3_transfer']['protocol']['seeds']}), not "
                         f"{FRESH_SEEDS}")
    n = len(FRESH_SEEDS)
    A._cells_ok(A.e8_cell(rep), n, A.N_INBAND, f"the R2b {role} report's E8 AR cell")
    A._cells_ok(A.p3_cell(rep, "fine"), n, A.N_FINE, f"the R2b {role} report's P3 fine cell")
    A._cells_ok(A.p3_cell(rep, "inband"), n, A.N_INBAND,
                f"the R2b {role} report's P3 in-band cell")
    p3_e8 = A.p3_e8_deviation(rep)
    if not p3_e8 <= A.P3_E8_MAX_REL_DEV:
        raise ValueError(f"the R2b {role} report's P3 in-band pass does not reproduce its E8 AR "
                         f"cell (seed means differ by up to {p3_e8:.3g}, more than "
                         f"{A.P3_E8_MAX_REL_DEV:g}"
                         + ("; finite in one of the two only" if math.isinf(p3_e8) else "")
                         + "): P3 did not evaluate the states E8 trained")
    d9 = rep["results"]["e8"]["metrics"]["d9_restart"]
    return {"label": label, "config_sha256": prov["config_sha256"], "git": prov.get("git"),
            "states": {k: v.get("sha256") for k, v in d9["ar_states"].items()},
            "resumed": d9.get("units_resumed_from_epoch") or {},
            "reused": sorted(k for k, v in d9["ar_states"].items() if v.get("reused")),
            "reuse_states": bool(rep.get("d9_reuse_states")),
            "p3_vs_e8_max_rel_dev": p3_e8,
            "ledger_total": int((rep.get("solve_ledger") or {}).get("total", 0)),
            "timestamp_utc": prov.get("timestamp_utc"), **A._runtime(rep)}


# ---------------------------------------------------------------- readings --

def uninformative(vb: dict, mech_b: dict | None) -> str | None:
    """PREREG_R2B Sec. 6 (R2a's lines): a fresh baseline that does not show the
    deficit S is meant to remove makes a NOT SUPPORTED R2b uninformative about
    S's mechanism."""
    low = []
    ratio = vb["ratio_of_seed_means"]
    if math.isfinite(ratio) and ratio < A.UNINFORMATIVE_RATIO_MIN:
        low.append(f"fine / in-band ratio of seed means {ratio:.3g} < "
                   f"{A.UNINFORMATIVE_RATIO_MIN}")
    if isinstance(mech_b, dict) and "fine" in mech_b:
        c = mech_b["fine"]["c_star_median"]["seed_mean"]
        if c < A.UNINFORMATIVE_CSTAR_MIN:
            low.append(f"median c* on the fine set {c:.3g} < {A.UNINFORMATIVE_CSTAR_MIN}")
    if not low:
        return None
    return ("the fresh baseline does not show the deficit S is meant to remove ("
            + "; ".join(low) + "): a NOT SUPPORTED R2b is uninformative about S's "
            "mechanism; the verdict stands")


def phase2b_reading(b: dict, p2b: dict) -> dict:
    """The fresh baseline (seeds 3-5) beside the Phase-2b run (seeds 0-2, the
    same configuration otherwise): a coarse check of the training path; a
    difference beyond the guard is a flag, never a verdict."""
    out = {}
    for name, get in (("fine_displacement",
                       lambda r: A.seed_means(A.p3_cell(r, "fine"), "disp_rel_l2")),
                      ("inband_energy_gap",
                       lambda r: A.seed_means(A.e8_cell(r), "energy_gap_rel")),
                      ("inband_displacement",
                       lambda r: A.seed_means(A.e8_cell(r), "disp_rel_l2"))):
        out[name] = _soft(guard, get(p2b), get(b))
    out["flags"] = [
        f"{k}: the fresh baseline is {'lower' if g['lower'] else 'higher'} than the Phase-2b "
        f"seeds 0-2 beyond the guard (rel {g['rel_change']:+.1%}, tau {g['threshold']:.1%})"
        for k, g in out.items() if isinstance(g, dict) and "not_evaluated" not in g
        and not g.get("diverged") and (g["lower"] or g["worse"])]
    return out


def paired(vb: dict, vs: dict) -> dict:
    """Per seed, S's value over the baseline's minus 1, for each condition's
    metric (the arms of a seed share its initial weights and instance order)."""
    out = {}
    for cond, key in CONDITIONS:
        out[cond] = [x / y - 1 if math.isfinite(x) and math.isfinite(y) and y else float("nan")
                     for y, x in zip(vb[key], vs[key], strict=True)]
    return out


def beyond_amplitude(s: dict, amp_b: dict | None, b_sha256: str | None) -> dict:
    """S's fine displacement error against the fresh baseline's after scaling
    each load case by its c* (the baseline's amplitude record, per seed), with
    the guard: whether S does more than correct the amplitude."""
    if amp_b is None:
        return {"not_evaluated": "no amplitude record of the fresh baseline given"}
    try:
        A.check_amp(amp_b, b_sha256)
        seeds = [f"s{x}" for x in FRESH_SEEDS]
        if sorted(amp_b["seeds"]) != sorted(seeds):
            raise ValueError(f"the baseline's amplitude record holds seeds {sorted(amp_b['seeds'])}")
        base = [float(amp_b["seeds"][k]["fine"]["summary"]["disp_c"]) for k in seeds]
        g = guard(base, A.seed_means(A.p3_cell(s, "fine"), "disp_rel_l2"))
    except Exception as exc:                              # noqa: BLE001
        return {"not_evaluated": f"{type(exc).__name__}: {exc}"}
    return {"guard": g, "S_is": A._direction(g, "disp_rel_l2")}


def kp4_reading(b: dict, vb: dict, vs: dict) -> dict:
    """Beside condition (ii): each arm's fine / in-band ratio of seed means
    against KP4's line (the configuration's `kills.KP4_transfer_ratio`, 1.5 in
    PREREG_PHASE2B, at which the Phase-2b transformer's 8.62 retired its
    transfer zone)."""
    line = float(b["config"]["kills"]["KP4_transfer_ratio"])
    out = {"line": line}
    for role, v in (("b", vb), ("s", vs)):
        r = v["ratio_of_seed_means"]
        out[role] = {"ratio_of_seed_means": r,
                     "below_line": (bool(r < line) if math.isfinite(r) else None)}
    return out


def r2a_beside(f3v: dict | None, verdict: dict) -> dict:
    """R2a's conditions (the bottleneck) beside R2b's (the transformer), and the
    ratio of S's fine reductions on the two beside c*'s (Sec. 5's k)."""
    if not isinstance(f3v, dict) or "conditions" not in (f3v.get("R2a") or {}):
        return {"not_evaluated": "no fine3d verdict file with R2a's conditions given"}
    r2a = f3v["R2a"]
    out = {"R2a_verdict": r2a.get("verdict"), "conditions": {}}
    for cond, _ in CONDITIONS:
        gb, gt = r2a["conditions"].get(cond) or {}, verdict.get(cond) or {}
        out["conditions"][cond] = {
            "bottleneck": {"rel_change": gb.get("rel_change"), "threshold": gb.get("threshold")},
            "transformer": {"rel_change": gt.get("rel_change"), "threshold": gt.get("threshold")}}
    fb = (r2a["conditions"].get("fine_displacement") or {}).get("rel_change")
    ft = (verdict.get("fine_displacement") or {}).get("rel_change")
    ok = all(isinstance(x, (int, float)) and math.isfinite(x) for x in (fb, ft)) and fb
    out["fine_reduction_ratio"] = float(ft / fb) if ok else None
    out["c_star_k"] = C_STAR_K
    return out


CONDITION_II_ALONE = ("condition (ii) alone fails: S's fine displacement error is lower beyond "
                      "the guard and its in-band errors are not worse, but the growth (the fine "
                      "/ in-band ratio) is not shown to shrink beyond the guard")
"""PREREG_R2B Sec. 6: the words the verdict file gives a NOT SUPPORTED R2b whose
only failing condition is (ii)."""


def machines(status_text: str) -> dict:
    """{step: [(host, driver) of each attempt's start]} from the session's
    status file (scripts/r2b_session.sh writes them on every start line)."""
    out = {}
    for line in status_text.splitlines():
        m = re.match(r"(\S+)\.log start \S+ \S+ host (\S*) driver ?(\S*)$", line.strip())
        if m:
            out.setdefault(m.group(1), []).append((m.group(2), m.group(3)))
    return out


def machine_deviations(mach: dict) -> list:
    """More than one host or GPU driver among the steps' starts, or a start
    line without them, is a deviation (a driver that could not be read is not
    counted as another one)."""
    dev = []
    hosts = {h for v in mach.values() for h, _ in v if h}
    drivers = {d for v in mach.values() for _, d in v if d}
    if len(hosts) > 1 or len(drivers) > 1:
        dev.append("the session's steps started on more than one host or GPU driver: "
                   + "; ".join(f"{k} {v}" for k, v in sorted(mach.items())))
    return dev


# ------------------------------------------------------------- adjudicate --

def adjudicate_arms(b: dict, s: dict, p2b: dict, f3v: dict | None = None,
                    prereg_entries: dict | None = None, expected_git: str | None = TAG,
                    s_factor: float | None = None, amp_b: dict | None = None,
                    amp_s: dict | None = None, b_sha256: str | None = None,
                    s_sha256: str | None = None) -> dict:
    checks = {"b": check_arm("b", b, p2b, prereg_entries, expected_git, s_factor),
              "s": check_arm("s", s, p2b, prereg_entries, expected_git, s_factor)}
    vb, vs = A.r2a_values(b), A.r2a_values(s)
    try:
        verdict = A.r2a_verdict(vb, vs)
    except ValueError as exc:      # a non-finite value of the fresh baseline: the comparison is void
        verdict = {"verdict": "NOT EVALUATED: a per-seed value of the fresh baseline is not "
                              f"finite: the comparison is void ({exc})", "void": True}
    mech = {}
    for role, amp, sha in (("b", amp_b, b_sha256), ("s", amp_s, s_sha256)):
        if amp is None:
            mech[role] = {"not_evaluated": "no amplitude record given"}
            continue
        try:
            chk = A.check_amp(amp, sha)
            mech[role] = dict(A.mechanism(amp, chk["remesh_not_evaluated"]),
                              reproduction_max_rel_dev=chk["reproduction_max_rel_dev"])
        except Exception as exc:                          # noqa: BLE001
            mech[role] = {"not_evaluated": f"{type(exc).__name__}: {exc}"}
    out = {"verdict": verdict["verdict"], "conditions": verdict, "values": {"b": vb, "s": vs}}
    out["uninformative_note"] = None
    if not verdict.get("void") and [f.split()[0] for f in verdict.get("failing") or []] == ["(ii)"]:
        out["condition_ii_alone"] = CONDITION_II_ALONE
    if not verdict.get("void") and verdict["verdict"] != "SUPPORTED":
        if "not_evaluated" in mech["b"]:
            why = ("no usable amplitude record of the fresh baseline ("
                   + mech["b"]["not_evaluated"] + ")")
        elif not math.isfinite(mech["b"]["fine"]["c_star_median"]["seed_mean"]):
            why = "the fresh baseline's median c* on the fine set is not finite"
        else:
            why = None
        out["uninformative_note"] = uninformative(vb, None if why else mech["b"])
        if why:
            out["uninformative_cstar"] = "not evaluated: " + why
    deviations = [f"R2b {r}: solve ledger {c['ledger_total']} (expected 0)"
                  for r, c in checks.items() if c["ledger_total"]]
    deviations += [f"R2b {r}: restarted (units resumed {c['resumed']}, states reused "
                   f"{c['reused']}, reuse_states {c['reuse_states']})"
                   for r, c in checks.items() if c["resumed"] or c["reuse_states"] or c["reused"]]
    diff = [k for k in A.RUNTIME_KEYS if checks["b"][k] != checks["s"][k]]
    if diff:
        deviations.append("R2b: the two arms ran with different " + ", ".join(
            f"{k} ({checks['b'][k]!r} / {checks['s'][k]!r})" for k in diff))
    deviations += [f"R2b {r}: the amplitude record's predictions differ from the report's by up "
                   f"to {m['reproduction_max_rel_dev']:.3g} (more than {A.AMP_REPRODUCTION_MAX:g})"
                   for r, m in mech.items() if "not_evaluated" not in m
                   and not m["reproduction_max_rel_dev"] <= A.AMP_REPRODUCTION_MAX]
    deviations += [f"R2b {r}: the amplitude record's remesh readings are not evaluated: "
                   f"{m['remesh']['not_evaluated']}"
                   for r, m in mech.items() if "not_evaluated" not in m
                   and "not_evaluated" in (m.get("remesh") or {})]
    out.update({"robustness": A.r2a_robustness(b, s), "paired_per_seed": paired(vb, vs),
                "comparisons": A.r2a_comparisons(b, s),
                "fresh_baseline_vs_phase2b": phase2b_reading(b, p2b),
                "kp4_line": _soft(kp4_reading, b, vb, vs),
                "beyond_amplitude": beyond_amplitude(s, amp_b, b_sha256),
                "r2a_beside": (r2a_beside(f3v, verdict) if not verdict.get("void")
                               else {"not_evaluated": "R2b not evaluated"}),
                "mechanism": mech, "checks": checks, "deviations": deviations})
    return out


def adjudicate(arms: dict | None, p2b: dict, f3v: dict | None = None,
               prereg_entries: dict | None = None, expected_git: str | None = TAG,
               s_factor: float | None = None, missing: str | None = None) -> dict:
    """`arms`: {"b": report, "s": report, "amp_b"?, "amp_s"?, "b_sha256"?,
    "s_sha256"?} or None (`missing` says why). A refusal, or any error while
    reading the reports, leaves R2b NOT EVALUATED with the reason."""
    out = {"prereg": PREREG_NAME, "tag": expected_git}
    if arms is None:
        out["R2b"] = {"verdict": "NOT EVALUATED: " + (missing or "no R2b reports")}
        return out
    try:
        out["R2b"] = adjudicate_arms(arms["b"], arms["s"], p2b, f3v, prereg_entries,
                                     expected_git, s_factor, arms.get("amp_b"),
                                     arms.get("amp_s"), arms.get("b_sha256"),
                                     arms.get("s_sha256"))
    except Exception as exc:                              # noqa: BLE001
        out["R2b"] = {"verdict": f"NOT EVALUATED: refused: {type(exc).__name__}: {exc}"}
    return out


# ---------------------------------------------------------- the code read --

def _git_show(root: Path, tag: str, path: str) -> bytes | None:
    r = subprocess.run(["git", "-C", str(root), "show", f"{tag}:{path}"], capture_output=True,
                       timeout=60)
    return r.stdout if r.returncode == 0 else None


def adjudicator_record(prereg: Path, tag: str, root: Path = ROOT) -> dict:
    """The adjudicating files and the pre-registration read, against the
    tag's copies in the repository at `root`."""
    from fejepa.report import _git_describe

    files = {f: _sha256(root / f) for f in ADJ_FILES}
    tagged = {f: _git_show(root, tag, f) for f in (*ADJ_FILES, PREREG_NAME)}
    available = all(v is not None for v in tagged.values())
    text = Path(prereg).read_text(encoding="utf-8")
    return {"git": _git_describe(), "files_sha256": files, "tag": tag,
            "tag_available": available,
            "differs_from_tag": ([f for f in ADJ_FILES
                                  if hashlib.sha256(tagged[f]).hexdigest() != files[f]]
                                 if available else None),
            "prereg_file": str(prereg), "prereg_sha256": _sha256(prereg),
            "prereg_is_tags": (hashlib.sha256(tagged[PREREG_NAME]).hexdigest()
                               == _sha256(prereg)) if available else None,
            "prereg_is_repository_file":
                Path(prereg).resolve() == (root / PREREG_NAME).resolve(),
            "prereg_self_hash_ok": bool(_script("stamp_prereg_r2b").self_hash_ok(text))}


def code_deviations(rec: dict, prereg) -> list:
    """The deviations the adjudicator's own record shows."""
    tag = rec["tag"]
    if not rec["tag_available"]:
        dev = [f"the adjudicating code and the pre-registration read were not compared with "
               f"{tag} (the tag cannot be read here)"]
    else:
        dev = ([f"the adjudicating files differ from {tag}: {rec['differs_from_tag']}"]
               if rec["differs_from_tag"] else [])
        if not rec["prereg_is_tags"]:
            dev.append(f"{prereg}: the pre-registration read is not {tag}'s {PREREG_NAME}")
    if not rec["prereg_self_hash_ok"]:
        dev.append(f"{prereg}: its last line does not verify (PREREG_R2B_SHA256)")
    return dev


def main() -> None:
    from fejepa.report import PREREG_PLACEHOLDER, read_prereg_entries

    f3s = _script("adjudicate_fine3d")          # strict JSON and the status file's readers
    ap = argparse.ArgumentParser()
    ap.add_argument("--r2b-b", default=None, help="the fresh baseline's report (r2b_b)")
    ap.add_argument("--r2b-s", default=None, help="S's report (r2b_s)")
    ap.add_argument("--amp-b", default=None)
    ap.add_argument("--amp-s", default=None)
    ap.add_argument("--status", default=None, help="the session's status.txt (attempts)")
    ap.add_argument("--phase2b", default=str(ROOT / PHASE2B))
    ap.add_argument("--fine3d-verdict", default=str(ROOT / FINE3D_VERDICT))
    ap.add_argument("--prereg", default=str(ROOT / PREREG_NAME))
    ap.add_argument("--expected-git", default=TAG,
                    help="the git describe every report must carry ('' = not checked)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if _sha256(a.phase2b) != A.PHASE2B_REPORT_SHA256:
        raise SystemExit(f"{a.phase2b}: not the Phase-2b report")
    if _sha256(a.fine3d_verdict) != FINE3D_VERDICT_SHA256:
        raise SystemExit(f"{a.fine3d_verdict}: not fine3d's verdict file")
    entries = dict(read_prereg_entries(a.prereg))
    if any(v == PREREG_PLACEHOLDER for v in entries.values()):
        raise SystemExit(f"{a.prereg}: not stamped")
    s_factor = json.loads((ROOT / "configs" / "r2b_s.json").read_text())["model"][
        "decode_scale_factor"]

    def present(p):
        return p if p and Path(p).is_file() else None

    def read(p):
        """(the parsed file, None), or (None, why it cannot be read)."""
        try:
            return A.load_json(p), None
        except Exception as exc:                              # noqa: BLE001
            return None, f"{p} is not readable ({type(exc).__name__}: {exc})"

    def amp(p):
        if not p:
            return None                                   # not given
        if not present(p):
            return {"unreadable": f"{p} is not in the return"}
        rec, why = read(p)
        return rec if why is None else {"unreadable": why}

    missing, arms = None, None
    b, s = present(a.r2b_b), present(a.r2b_s)
    if b and s:
        (rb, wb), (rs, ws) = read(b), read(s)
        if wb or ws:
            missing = "; ".join(w for w in (wb, ws) if w)
        else:
            arms = {"b": rb, "s": rs, "b_sha256": _sha256(b), "s_sha256": _sha256(s),
                    "amp_b": amp(a.amp_b), "amp_s": amp(a.amp_s)}
    else:
        missing = "R2b needs both reports: " + ", ".join(
            f"{p} is not in the return" if p else f"{flag} was not given"
            for flag, p, ok in (("--r2b-b", a.r2b_b, b), ("--r2b-s", a.r2b_s, s)) if not ok)
    res = adjudicate(arms, A.load_json(a.phase2b), A.load_json(a.fine3d_verdict), entries,
                     a.expected_git or None, s_factor, missing)
    rec = adjudicator_record(Path(a.prereg), TAG)
    res["adjudicator"] = rec
    dev = code_deviations(rec, a.prereg)
    if a.status:
        if present(a.status):
            text = Path(a.status).read_text()
            att, ends = f3s.attempts(text), f3s.last_exits(text)
            res["attempts"], res["last_exits"] = att, ends
            res["machines"] = machines(text)
            dev += machine_deviations(res["machines"])
            dev += [f"{k}: an attempt's start line does not record its host and driver"
                    for k in att if len(res["machines"].get(k, ())) != att[k]]
            dev += [f"{k}: {v} attempts" for k, v in att.items() if v > 1]
            dev += [f"{k}: not started" for k in STEPS if k not in att]
            dev += [f"{k}: its last attempt has no exit line (interrupted)" if v is None
                    else f"{k}: its last attempt exited {v}"
                    for k, v in ends.items() if v != 0]
        else:
            res["attempts"] = res["last_exits"] = res["machines"] = None
            dev.append(f"the session's status file is not in the return ({a.status})")
    else:
        res["attempts"] = res["last_exits"] = res["machines"] = None
        dev.append("the session's status file was not given (--status)")
    res["session_and_code_deviations"] = dev
    r2b = res["R2b"]
    res["deviations"] = dev + list(r2b.get("deviations") or [])
    notes = [f"R2b: {r2b['uninformative_note']}"] if r2b.get("uninformative_note") else []
    if r2b.get("condition_ii_alone"):
        notes.append(f"R2b: {r2b['condition_ii_alone']}")
    if r2b.get("uninformative_cstar"):
        notes.append(f"R2b: the uninformative note's c* reading is {r2b['uninformative_cstar']}")
    notes += [f"R2b: {f}" for f in (r2b.get("fresh_baseline_vs_phase2b") or {}).get("flags")
              or []]
    res["notes"] = notes
    res["inputs"] = {str(p): _sha256(p) for p in (a.r2b_b, a.r2b_s, a.amp_b, a.amp_s, a.status,
                                                  a.phase2b, a.fine3d_verdict, a.prereg)
                     if present(p)}
    text = json.dumps(f3s.strict(res), indent=1, allow_nan=False)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text + "\n")
    summary = {"R2b": r2b.get("verdict"), "deviations": res["deviations"], "notes": res["notes"]}
    print(json.dumps(f3s.strict(summary), indent=1, allow_nan=False))


if __name__ == "__main__":
    main()
