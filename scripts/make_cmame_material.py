#!/usr/bin/env python3
"""The manuscript's tables, figures and in-text numbers, generated from
the committed records only (no number in the manuscript is typed by hand).

Inputs (their SHA-256 values are written to sources.json):

* records/phase1/report_rec8_v2.json -- the two-dimensional deciding run of
  16 July 2026 (configuration SHA-256 62b26ad8...);
* records/phase1/report_diag.json -- the two-dimensional diagnostic run of
  30 July 2026 (exploratory; read for its six further label-free trainings);
* records/phase1/report_wp2_e2.json -- the two-dimensional WP2/E2 run of
  31 July 2026 (read for its pre-registered criterion K3);
* records/wp8/e2/baseline/report_phase2b.json -- the three-dimensional run of
  28 September 2026 (Phase-2b);
* records/wp8/posthoc/amp_*.json and the other wp8 records read through
  scripts/make_wp8_paper_material.py (post-hoc amplitude readings, E1, E2);
* records/cmame/cm2d/return/report.json and records/cmame/cm2d/verdict.json --
  the two-dimensional comparison with the current code (PREREG_CM2D; run of 9
  October 2026) and its pre-registered verdicts; scripts/adjudicate_cm2d.py,
  checked against the hash the verdict records, for the reuse bound it applied;
* records/cmame/spectra/export/ -- the error spectra of CM2D's networks
  (scripts/cm2d_spectra.py; post hoc);
* records/cmame/timing/fields/ -- the per-load energies, error diagnostics and
  field figures of the three-dimensional networks (scripts/export_fields.py;
  post hoc);
* records/cmame/timing/timing_2d.json, timing_3d.json, machine.txt -- the
  surrogate's inference against exact solves (RUNBOOK_CMAME Sec. A);
* records/cmame/threads/ -- the threads of those solvers, timed again on
  another host (RUNBOOK_W9 Sec. 4).

Outputs (paper/cmame/generated/):

* table_2d.tex, table_3d.tex -- every metric at the largest label budget (2D:
  CM2D); table_2djuly.tex -- the same for the 2D run of 16 July 2026;
* table_label_efficiency.tex -- displacement error and energy gap per budget (3D and
  CM2D); table_label_efficiency_july.tex -- the same for the 2D run of 16 July 2026;
* table_transfer.tex -- the finer three-dimensional mesh, zero-shot and few-shot;
* table_criteria.tex -- every pre-registered criterion with its outcome;
  table_cm2d.tex -- CM2D's comparisons with the readings required beside them;
* table_cost.tex -- the surrogate's inference against exact solves (Section 8.4);
* table_amplitude.tex, table_remesh.tex, table_e1.tex, table_e2.tex -- the
  wp8 tables' rows (shared code) with this manuscript's captions;
* numbers.tex -- one macro per number quoted in the text;
* fig_disp_vs_stress.pdf, fig_energy_gap.pdf, fig_label_efficiency.pdf;
* fig_spectra.pdf, fig_field2d.pdf (2D, post hoc) and fig_field_worst.pdf,
  fig_field_median.pdf, fig_field_fine.pdf (3D, post hoc);
* material.md (the tables and numbers in Markdown) and sources.json.

Field plots show one load case of the instance a rule selected: within the
instance, the load case selected by the same rule (largest or lower median),
applied to that instance's four load cases (FIELD_LOADS).

Seed statistics are the mean and the sample standard deviation (n - 1) of the
per-seed values. "Worse than the zero field" means a relative energy gap above
1 (the zero field's is exactly 1); for an instance it is the mean over its
four load cases, as the evaluation records it; for a single load case it is
equivalent to Pi_h(u) > 0 (Corollary 4 of the manuscript).

The text outputs are deterministic: regenerating from the records reproduces
the committed files byte for byte (tests/test_cmame_material.py).

    python scripts/make_cmame_material.py
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import statistics
from math import floor, log10
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "cmame" / "generated"
REC8 = ROOT / "records" / "wp8"
R2D = ROOT / "records" / "phase1" / "report_rec8_v2.json"
RDIAG = ROOT / "records" / "phase1" / "report_diag.json"
RWP2 = ROOT / "records" / "phase1" / "report_wp2_e2.json"
R3D = REC8 / "e2" / "baseline" / "report_phase2b.json"
AMP = {"transformer": REC8 / "posthoc" / "amp_phase2b.json",
       "m512": REC8 / "posthoc" / "amp_e2_m512.json",
       "m1024": REC8 / "posthoc" / "amp_e2_m1024.json"}
E1_BASE = REC8 / "e1" / "e1_2d_base" / "report.json"
RCM = ROOT / "records" / "cmame" / "cm2d" / "return" / "report.json"
VCM = ROOT / "records" / "cmame" / "cm2d" / "verdict.json"
SPEC = ROOT / "records" / "cmame" / "spectra" / "export"
FLD = ROOT / "records" / "cmame" / "timing" / "fields"
TIM = ROOT / "records" / "cmame" / "timing"
THR = ROOT / "records" / "cmame" / "threads"
RK3 = ROOT / "records" / "cmame" / "k3d" / "return" / "report.json"
VK3 = ROOT / "records" / "cmame" / "k3d" / "verdict.json"
HOLD = ROOT / "records" / "cmame" / "holdout"
RITZ = ROOT / "records" / "cmame" / "ritz" / "return"
RITZ_TGZ = ROOT / "records" / "cmame" / "ritz" / "ritz_return_20261029-1150.tgz"
TIM2 = RITZ / "timing"
MINUS = "−"
HEADER = "% generated from the committed records; do not edit"
WORDS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
         "ten")
BUDGETS = ("16", "64", "256", "1024")
METRICS = ("disp_rel_l2", "energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err", "crit_recall")
NAMES = {"ar": "Label-free", "labels": "Supervised, displacement",
         "labels_anchor": "Supervised, displacement + energy term",
         "ar_ft": "Label-free, then supervised",
         "labels_knorm": "Supervised, energy norm",
         "mgn": "Graph network, displacement", "knn_field": "Nearest-neighbour field",
         "scale_aware_poly": "Scaled polynomial", "zero": "Zero field"}
ARMS_2D = ("ar", "labels", "labels_anchor", "ar_ft", "mgn", "knn_field", "scale_aware_poly",
           "zero")
ARMS_CM = ("ar", "labels", "labels_knorm", "mgn", "knn_field", "scale_aware_poly", "zero")
ARMS_3D = ("ar", "labels", "labels_anchor", "mgn", "knn_field", "scale_aware_poly", "zero")
TRAINED = ("ar", "labels", "labels_anchor", "ar_ft", "labels_knorm", "mgn")
# figure identity: colour AND marker (validated categorical palette; the five
# series validate all-pairs in light mode, scripts of the dataviz method)
STYLE = {"ar": ("#2a78d6", "o"), "labels": ("#e87ba4", "s"),
         "labels_anchor": ("#eda100", "D"), "labels_knorm": ("#008300", "X"),
         "mgn": ("#4a3aa7", "^")}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
# single-hue sequential ramps for fields: displacement magnitude (blue) and
# von Mises stress (orange), light to dark
RAMP_DISP = ("#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b")
RAMP_VM = ("#fee6ce", "#fdd0a2", "#fdae6b", "#fd8d3c", "#f16913", "#d94801", "#a63603",
           "#7f2704")
# the load case each field plot shows: the instance rule applied within the instance
# (figure: (row whose per-load values decide, quantity, rule))
FIELD_LOADS = {"fig5": ("labels", "rel", "max"), "fig6": ("ar", "rel", "median"),
               "fig7": ("ar", "disp", "median"), "fig2d": ("labels", "rel", "median")}
LOADS_3D = ("downward traction on the end face", "axial traction on the end face",
            "shear traction on the top face", "downward body force")
LOADS_2D = ("downward traction on the end edge", "axial traction on the end edge",
            "shear traction on the top edge", "downward body force")


def _wp8():
    spec = importlib.util.spec_from_file_location(
        "make_wp8_paper_material", ROOT / "scripts" / "make_wp8_paper_material.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


W = _wp8()


def _rel(p: Path) -> str:
    return str(Path(p).resolve().relative_to(ROOT))


def load(path: Path, used: dict) -> dict:
    data = Path(path).read_bytes()
    used[_rel(path)] = hashlib.sha256(data).hexdigest()
    return json.loads(data)


def load_npz(path: Path, used: dict) -> dict:
    """The arrays of an .npz record, read from the bytes whose SHA-256 is recorded."""
    import io

    data = Path(path).read_bytes()
    used[_rel(path)] = hashlib.sha256(data).hexdigest()
    with np.load(io.BytesIO(data), allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def pick_load(values, rule: str) -> int:
    """The load case a field plot shows: the instance's rule applied to its load
    cases ("max": the largest value, the first of any tie, as np.argmax; "median":
    0-based rank (n - 1) // 2 in ascending order, as the instance rules)."""
    v = np.asarray(values, dtype=np.float64)
    if rule == "max":
        return int(np.argmax(v))
    if rule == "median":
        return int(np.argsort(v, kind="stable")[(v.size - 1) // 2])
    raise ValueError(rule)


# ---------------------------------------------------------------- reading
def cells(report: dict) -> dict:
    return report["results"]["e8"]["metrics"]["cells"]


def _cell(report: dict, arm: str, b: str) -> dict:
    c = cells(report)[arm]
    return c[b] if b in c else c[max(c, key=int)]   # the label-free cell is keyed by its pool


def seed_values(report: dict, arm: str, b: str, metric: str) -> list:
    return [float(x) for x in _cell(report, arm, b)[metric]["per_seed"]]


def seed_mean(report: dict, arm: str, metric: str, b: str = "1024") -> float:
    return statistics.fmean(seed_values(report, arm, b, metric))


def per_instance(report: dict, arm: str, metric: str, b: str = "1024") -> np.ndarray:
    """(seeds, instances) array of one metric."""
    rows = [e["per_instance"][metric] for e in _cell(report, arm, b)["per_seed_eval"]]
    return np.array(rows, dtype=float)


def worse_than_zero(report: dict, arm: str, b: str = "1024") -> tuple:
    g = per_instance(report, arm, "energy_gap_rel", b)
    return int(np.sum(g > 1.0)), int(g.size)


# ---------------------------------------------------------------- formatting
def num(x: float, sig: int = 3) -> str:
    """`sig` significant digits, fixed notation, thousands separators, typographic minus."""
    if x == 0:
        return "0"
    dec = max(0, sig - 1 - int(floor(log10(abs(x)))))
    r = round(abs(x), dec)
    if r and int(floor(log10(r))) > int(floor(log10(abs(x)))):     # rounded up a decade
        dec = max(0, dec - 1)
    return (MINUS if x < 0 else "") + f"{abs(x):,.{dec}f}"


def ms(values, sig: int = 3) -> str:
    """Seed mean ± sample SD at the mean's precision (as the wp8 tables, with
    thousands separators); one value: the value."""
    v = [float(x) for x in values]
    txt = num(statistics.fmean(v), sig)
    if len(v) == 1:
        return txt
    d = len(txt.split(".")[1]) if "." in txt else 0
    return f"{txt} ± {statistics.stdev(v):,.{d}f}"


def pct(x: float, dec: int = 1) -> str:
    return f"{x * 100:.{dec}f}%"


def spct(x: float, dec: int = 1) -> str:
    return f"{x * 100:+.{dec}f}%".replace("-", MINUS)


def times(x: float, dec: int = 1) -> str:
    return f"{x:.{dec}f}"


def and_list(items) -> str:
    """'a, b and c' (a list of values in running text)."""
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def words(n: int) -> str:
    """A count as the text writes it: in words up to ten, in digits above."""
    return WORDS[n] if 0 <= n <= 10 else f"{n:,}"


def share(win: np.ndarray) -> str:
    """The share of pairs a comparison won, as the text writes it ("all" when every one,
    "none" when none)."""
    if bool(win.all()):
        return "all"
    return "none" if not bool(win.any()) else pct(float(win.mean()))


def upct(x: float) -> str:
    """A share in percent to the unit; one strictly between 0 and 1 is never shown as 0% or
    100% (to one decimal then, or two), as the records' README writes the Ritz shares."""
    for nd in (0, 1, 2):
        txt = f"{100 * x:.{nd}f}"
        if not 0 < x < 1 or float(txt) not in (0.0, 100.0):
            break
    return txt + "%"


def at_least(x: float) -> str:
    """A lower bound in percent: x rounded down to one decimal ("at least ...")."""
    v = floor(round(x * 1000, 6)) / 10
    return (f"{v:.0f}" if v == int(v) else f"{v:.1f}") + "%"


def at_most(x: float) -> str:
    """An upper bound in percent: x rounded up to one decimal ("at most ...")."""
    v = -floor(-round(x * 1000, 6)) / 10
    return (f"{v:.0f}" if v == int(v) else f"{v:.1f}") + "%"


def tex(s: str) -> str:
    """Text-mode LaTeX for a table cell, note or macro (wp8 escaping plus a few symbols)."""
    s = (s.replace("<", "$<$").replace(">", "$>$")
         .replace("≥", "$\\geq$").replace("≤", "$\\leq$").replace("#", "\\#")
         .replace("&", "\\&").replace("⁻³", "$^{-3}$").replace("′", "$'$"))
    s = re.sub(r"\blc (?=[0-9])", "lc = ", s)           # "lc 0.0374" -> "lc = 0.0374"
    s = re.sub(r"\blc\b", "LCMARK", s)                 # the characteristic length l_c
    s = s.replace("~\\", "TIEMARK\\")                  # a tie before a command, not a tilde
    return W._latex_escape(s).replace("LCMARK", "$l_c$").replace("TIEMARK", "~")


# ---------------------------------------------------------------- tables
def _row(r: list, n: int) -> str:
    """A table row; a row of one cell spans every column (a heading inside the table)."""
    if len(r) == 1:
        return rf"\multicolumn{{{n}}}{{@{{}}l}}{{\emph{{{tex(r[0])}}}}} \\"
    return " & ".join(tex(c) for c in r) + r" \\"


def table(head: list, rows: list, caption: str, label: str, notes: list,
          align: str | None = None, rules: tuple = (), note_size: str = "footnotesize") -> str:
    cols = align or ("l" + "c" * (len(head) - 1))
    out = [HEADER,
           r"\begin{table}[tbp]", r"\centering", r"\footnotesize",
           r"\setlength{\tabcolsep}{4pt}",
           rf"\caption{{{tex(caption)}}}", rf"\label{{{label}}}",
           r"\resizebox{\ifdim\width>\textwidth\textwidth\else\width\fi}{!}{%",
           rf"\begin{{tabular}}{{{cols}}}", r"\toprule",
           " & ".join(_head(h) for h in head) + r" \\", r"\midrule"]
    for i, r in enumerate(rows):
        if i in rules:
            out.append(r"\midrule")
        out.append(_row(r, len(head)))
    out += [r"\bottomrule", r"\end{tabular}}"]
    if notes:
        out += ["", r"\smallskip", rf"\begin{{minipage}}{{\linewidth}}\{note_size}\raggedright"]
        out += [tex(n) + (r"\par" if i < len(notes) - 1 else "") for i, n in enumerate(notes)]
        out += [r"\end{minipage}"]
    out += [r"\end{table}", ""]
    return "\n".join(out)


RAGGED = r">{\raggedright\arraybackslash}"          # a ragged-right column


def longtable(head: list, rows: list, caption: str, label: str, notes: list, align: str,
              rules: tuple = (), size: str = "small", sep: str | None = None) -> str:
    """A table that may break across pages (needs the longtable package)."""
    hd = " & ".join(_head(h) for h in head) + r" \\"
    out = [HEADER,
           rf"\begingroup\{size}\setlength{{\LTcapwidth}}{{\linewidth}}"
           + (rf"\setlength{{\tabcolsep}}{{{sep}}}" if sep else ""),
           rf"\begin{{longtable}}{{{align}}}",
           rf"\caption{{{tex(caption)}}}\label{{{label}}}\\", r"\toprule", hd, r"\midrule",
           r"\endfirsthead",
           rf"\caption[]{{{tex(caption)} (continued)}}\\", r"\toprule", hd, r"\midrule",
           r"\endhead", r"\bottomrule", r"\endfoot"]
    for i, r in enumerate(rows):
        if i in rules:
            out.append(r"\midrule")
        out.append(_row(r, len(head)))
    out += [r"\end{longtable}", r"\endgroup", r"\vspace{-\smallskipamount}",
            r"\noindent\begin{minipage}{\linewidth}\footnotesize\raggedright"]
    out += [tex(n) + (r"\par" if i < len(notes) - 1 else "") for i, n in enumerate(notes)]
    out += [r"\end{minipage}", r"\par\medskip", ""]
    return "\n".join(out)


def _head(h: str) -> str:
    parts = [tex(x) for x in h.split("\n")]
    return parts[0] if len(parts) == 1 else r"\shortstack{" + r" \\ ".join(parts) + "}"


def md(head, rows, title, notes) -> str:
    out = [f"### {title}", "", "| " + " | ".join(h.replace("\n", " ") for h in head) + " |",
           "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows] + [""] + [f"- {n}" for n in notes] + [""]
    return "\n".join(out)


HEAD_METRICS = ["Model", "Displacement\nerror", "Relative\nenergy gap", "von Mises\nerror",
                "Peak stress\nerror", "Critical-region\nrecall", "Worse than\nzero field"]


def metric_rows(report: dict, arms) -> list:
    rows = []
    for arm in arms:
        vals = [ms(seed_values(report, arm, "1024", m)) for m in METRICS]
        if arm == "zero":                 # every error is 1 by definition; the top 10% of a
            vals[-1] = "–"                # constant field is undefined (ties)
            rows.append([NAMES[arm]] + vals + ["–"])
            continue
        k, n = worse_than_zero(report, arm)
        rows.append([NAMES[arm]] + vals + [f"{k:,}/{n:,}"])
    return rows


def metric_notes(n_val: int, extra: list) -> list:
    return [
        f"{n_val} validation instances, never trained on; four load cases each. Errors are "
        "relative to the reference finite-element solution, per load case, then averaged over "
        "the load cases; the relative energy gap of the zero field is 1. Trained networks: "
        "mean ± sample standard deviation over 3 seeds; the nearest-neighbour field and the "
        "scaled polynomial are deterministic.",
        "Worse than zero field: instance-seed pairs whose relative energy gap, the mean over "
        "the four load cases as the evaluation records it, exceeds 1, that is, predictions "
        "further from the solution in the energy norm than the zero field on average; the "
        r"count uses the reference solutions. The test of \cref{cor:zero} needs none and "
        r"applies to single load cases (\cref{sec:methods:metrics}).",
        "Critical-region recall: the share of the 10% most stressed elements of the reference "
        "solution that are also among the 10% most stressed of the prediction (higher is "
        "better; in every other column lower is better).",
    ] + extra


def label_efficiency_rows(blocks) -> tuple:
    """blocks: (label, report, arms) per run; each block ends with the label-free row."""
    rows, rules = [], []
    for dim, rep, arms in blocks:
        if rows:
            rules.append(len(rows))
        for arm in arms:
            c = cells(rep)[arm]
            row = [dim, NAMES[arm]]
            for b in BUDGETS:
                if b not in c:
                    row.append("–")
                    continue
                row.append(f"{num(seed_mean(rep, arm, 'disp_rel_l2', b))} / "
                           f"{num(seed_mean(rep, arm, 'energy_gap_rel', b))}")
            rows.append(row)
        d, e = seed_mean(rep, "ar", "disp_rel_l2"), seed_mean(rep, "ar", "energy_gap_rel")
        rows.append([dim, "Label-free (no labels)"] + [f"{num(d)} / {num(e)}"] * 4)
    return rows, tuple(rules)


def transfer_rows(r3: dict) -> list:
    p3 = r3["results"]["p3_transfer"]["metrics"]
    rows = []

    def row(name, blk):
        rows.append([name] + [ms(blk[m]["per_seed"]) for m in METRICS])

    row("Label-free, zero-shot", p3["ar"]["fine"])
    row("Supervised (1,024 labels), zero-shot", p3["zero_shot_reported"]["labels@max"]["fine"])
    row("Graph network (1,024 labels), zero-shot", p3["zero_shot_reported"]["mgn@max"]["fine"])
    for nm, key in (("Nearest-neighbour field", "knn_field"),
                    ("Scaled polynomial", "scale_aware_poly")):
        row(nm, p3["naive_rows"][key])
    for b in ("16", "64"):
        fs = p3["fewshot"][b]
        row(f"Label-free, then {b} fine-mesh labels", fs["finetune"])
        row(f"Supervised from scratch, {b} fine-mesh labels", fs["scratch"])
    return rows


# ---------------------------------------------------------------- provenance
RUNS = (("July run (two dimensions)", "phase1_rec8_v2", R2D),
        ("Diagnostic run (two dimensions, exploratory)", "diag_anchor_b16", RDIAG),
        ("Joint-embedding run (two dimensions)", "wp2_e2_v2", RWP2),
        ("Three-dimensional comparison (the amended run)", "phase2b_v1", R3D),
        ("Latent-regularisation run, label-free network", "e1_2d_base", E1_BASE),
        ("Latent-regularisation run, regularised network", "e1_2d_shaped",
         REC8 / "e1" / "e1_2d_shaped" / "report.json"),
        ("Latent-regularisation run, regulariser on the latent vectors directly",
         "e1_2d_raw_s0", REC8 / "e1" / "e1_2d_raw_s0" / "report.json"),
        ("Bottleneck run, M = 512", "e2_m512", REC8 / "e2" / "e2_m512" / "report.json"),
        ("Bottleneck run, M = 1,024", "e2_m1024", REC8 / "e2" / "e2_m1024" / "report.json"),
        ("Two-dimensional comparison", "cm2d_v1", RCM))


def config_sha256(cfg: dict) -> str:
    """The run guard's canonical configuration hash (fejepa.report.config_sha256)."""
    return hashlib.sha256(json.dumps(cfg, sort_keys=True, separators=(",", ":"))
                          .encode()).hexdigest()


MONTHS = ("January February March April May June July August September October November "
          "December").split()
LATER = ROOT / "records" / "cmame"          # the records of the runs of October 2026


def day_text(iso: str) -> str:
    """'2026-10-21...' as '21 October 2026'."""
    y, mo, d = (int(x) for x in iso[:10].split("-"))
    return f"{d} {MONTHS[mo - 1]} {y}"


def _record(path: Path, used: dict, base: Path) -> str:
    """A record's path relative to `base` and the head of its SHA-256 (the file is read
    and its hash recorded in sources.json)."""
    data = Path(path).read_bytes()
    used[_rel(path)] = hashlib.sha256(data).hexdigest()
    return (rf"\path{{{Path(path).resolve().relative_to(base).as_posix()}}} (SHA-256 "
            rf"\texttt{{{used[_rel(path)][:16]}}}\ldots)")


def _config(stem: str, used: dict) -> tuple:
    cfg_path = ROOT / "configs" / f"{stem}.json"
    data = cfg_path.read_bytes()
    used[_rel(cfg_path)] = hashlib.sha256(data).hexdigest()
    return cfg_path, json.loads(data), used[_rel(cfg_path)]


def _starts(status: Path, used: dict) -> list:
    """The UTC start times that a return's status file records, in its order."""
    data = status.read_bytes()
    used[_rel(status)] = hashlib.sha256(data).hexdigest()
    return re.findall(r" start (\d{4}-\d\d-\d\dT[\d:]+Z)", data.decode("utf-8"))


def hashes_tex(used: dict) -> str:
    """Each run's committed configuration, its hash (recomputed here and checked
    against the hash the run recorded), the records and their SHA-256. The paths of
    the records are given relative to the records directory, those of October 2026
    relative to its subdirectory for them, which is named once."""
    out = [HEADER, r"\begingroup\raggedright", r"\begin{itemize}"]
    later = []
    for name, stem, rep_path in RUNS:
        _, cfg, _ = _config(stem, used)
        rep = load(rep_path, used)
        h = config_sha256(cfg)
        if h != rep["provenance"]["config_sha256"]:
            raise SystemExit(f"{stem}: the committed configuration is not the one the run used")
        base = LATER if Path(rep_path).resolve().is_relative_to(LATER) else ROOT / "records"
        item = (rf"\item {tex(name)}, {day_text(rep['provenance']['timestamp_utc'])}: "
                rf"configuration \path{{configs/{stem}.json}} (SHA-256 "
                rf"\texttt{{{h[:16]}}}\ldots), record {_record(rep_path, used, base)}.")
        (later if base == LATER else out).append(item)
    # the holdout evaluation (PREREG_HOLDOUT): two evaluations and the verdict
    _, cfg, _ = _config("holdout_v1", used)
    h = config_sha256(cfg)
    ev = {s: load(HOLD / "return" / s / "eval.json", used) for s in ("h3d", "h2d")}
    if any(e["config_sha256"] != h for e in ev.values()):
        raise SystemExit("holdout: the committed configuration is not the one the run used")
    starts = _starts(HOLD / "return" / "status.txt", used)
    later.append(rf"\item Holdout evaluation, {day_text(starts[-1])}: configuration "
                 rf"\path{{configs/holdout_v1.json}} (SHA-256 \texttt{{{h[:16]}}}\ldots), "
                 rf"records {_record(HOLD / 'return' / 'h3d' / 'eval.json', used, LATER)} and "
                 rf"{_record(HOLD / 'return' / 'h2d' / 'eval.json', used, LATER)}, verdict "
                 rf"{_record(HOLD / 'verdict.json', used, LATER)}.")
    # the three-dimensional energy-norm run (PREREG_K3D)
    _, cfg, _ = _config("k3d_v1", used)
    h = config_sha256(cfg)
    rk = load(RK3, used)
    if h != rk["provenance"]["config_sha256"]:
        raise SystemExit("k3d_v1: the committed configuration is not the one the run used")
    later.append(rf"\item Three-dimensional energy-norm run, "
                 rf"{day_text(rk['provenance']['timestamp_utc'])}: configuration "
                 rf"\path{{configs/k3d_v1.json}} (SHA-256 \texttt{{{h[:16]}}}\ldots), record "
                 rf"{_record(RK3, used, LATER)}, verdict {_record(VK3, used, LATER)}.")
    # the Ritz baseline (not pre-registered; its scripts record the file's SHA-256)
    _, _, hf = _config("ritz_v1", used)
    for s in RITZ_SETS:
        if load(RITZ / "baseline" / s / "summary.json", used)["config_sha256"] != hf:
            raise SystemExit("ritz_v1: the committed configuration is not the one the run used")
    starts = _starts(RITZ / "status.txt", used)
    later.append(rf"\item Ritz baseline, {day_text(starts[0])}: configuration "
                 rf"\path{{configs/ritz_v1.json}} (SHA-256 of the file "
                 rf"\texttt{{{hf[:16]}}}\ldots), the return as received "
                 rf"{_record(RITZ_TGZ, used, LATER)}, which holds the per-instance values; "
                 r"its summaries and timings are committed unpacked beside it, in "
                 r"\path{ritz/return/}.")
    out += [r"\end{itemize}",
            r"The records of the runs of October 2026 are in \path{records/cmame/}; their "
            r"paths are given relative to it.",
            r"\begin{itemize}"] + later
    out += [r"\end{itemize}", r"\par\endgroup", ""]
    return "\n".join(out)


# ---------------------------------------------------------------- wp8 tables
# the wp8 tables' rows and notes in this manuscript's vocabulary; every
# substitution must apply (a change in the wp8 text then stops the build)
RELABEL = {
    "amp": [("Point-token transformer", "Label-free transformer"),
            ("Fine energy gap\n(median)", "Fine relative\nenergy gap (median)"),
            ("Mean fine energy gap over instances", "Mean fine relative energy gap over "
             "instances"),
            ("(energy gap: per-seed median)", "(relative energy gap: per-seed median)"),
            ("of the prediction u on the evaluated mesh, from that mesh's stiffness K and load F",
             "of the prediction $u$ on the evaluated mesh, from that mesh's stiffness matrix $K$ "
             "and load vector $F$"),
            ("Seeds per architecture", "Seeds per network"),
            (" instance-seed rows measured", " instance-seed evaluations measured"),
            ("of the same states", "of the same trained networks"),
            ("the transformer run's not at all", "the three-dimensional comparison's not at "
             "all"),
            ("never increases the energy error", "never increases the error in the "
             "energy norm"),
            ("In-band: the 256 Phase-2b validation instances", "In-band: the 256 validation "
             "instances"),
            (" (E8, P3; in-band)", " (in-band)"),
            ("Post-hoc reading 4e (E-series runbook, Sec. 4): reported only; no verdict is "
             "revisited.", "Measured after the runs; no verdict is revisited.")],
    "remesh": [("Point-token transformer", "Label-free transformer"),
               ("Predicted energy norm relative to", "Energy norm of the prediction "
                "relative to"),
               ("fscale, the battery's largest nodal load (both architectures multiply their "
                "output by it), relative", "The largest nodal load over the four load cases, "
                "by which both networks multiply their output, relative"),
               ("Post-hoc reading 4e (E-series runbook, Sec. 4): reported only.",
                "Measured after the runs."),
               ("c_b: the battery-level energy-optimal amplitude (label-free)",
                "c_b: the single energy-optimal amplitude of all four load cases of an "
                r"instance (label-free, \cref{sec:transfer:amplitude})")],
    "e2": [("Point-token transformer", "Label-free transformer"),
           ("(resolution ", "(noise guard "),
           ("In-band\nenergy gap", "In-band relative\nenergy gap"),
           (": K1 in-band energy gap", ": accuracy criterion, in-band relative energy gap"),
           ("Verdict: KILLED.", "Outcome: dropped."),
           (", fires)", "; triggered)"),
           (" s line: not triggered", " s limit: not triggered"),
           ("Seeds per architecture", "Seeds per network"),
           ("set-up-free, median of 3 differential pairs of 10 and 110 steps; transformer: one "
            "timed call per phase, its set-up included, and the mean",
            "the median over three repetitions of the time of 110 steps minus that of 10 "
            "steps, divided by 100, which removes the set-up time; transformer: a single timed "
            "step, its set-up included, the mean"),
           ("Resolution: the pre-registered max(10%, 2 × SE_rel) of the difference of seed means.",
            r"Noise guard: as in the note to \cref{tab:criteria}, with the label-free "
            "transformer as the reference; the pre-registration calls it the resolution."),
           ("relative L2 displacement and relative energy gap", "relative displacement "
            "error and relative energy gap"),
           ("; K2 (speed) fine step", "; speed criterion, fine-mesh step"),
           ("In-band: the 256 Phase-2b validation instances", "In-band: the 256 validation "
            "instances"),
           ("one label-free AR training step", "one label-free training step"),
           ("from the E2 bench", "from a dedicated benchmark"),
           ("the bench's instances at these two ends", "the benchmark instances at the two "
            "ends of this range"),
           ("nodes in the bench)", "nodes in the benchmark)"),
           ("its two bench measurements", "its two benchmark measurements")],
    "e1": [("Arm", "Network"),
           ("Energy\ngap", "Relative\nenergy gap"),
           ("(resolution 10%), energy gap", "(resolution 10%), relative energy gap"),
           ("(resolution ", "(noise guard "),
           ("Verdict: NO-GO.", "Outcome: NO-GO; the regulariser was not adopted."),
           ("S: silhouette of the pooled latents over geometry bins", "S: silhouette of the "
            "instance-mean latent vectors over four bins, the quartiles of the first principal "
            "component of the geometry descriptor"),
           ("1-NN: leave-one-out bin accuracy", "1-NN: leave-one-out accuracy of a "
            "nearest-neighbour classifier of the bin"),
           ("SIGReg monitor\n(tokens)", "SIGReg statistic\n(tokens)"),
           ("The raw-token ablation ran one seed and is reported only.",
            "SIGReg statistic (tokens): the regulariser's statistic evaluated on the latent "
            "vectors themselves rather than on the projection head's output (lower is closer "
            "to an isotropic Gaussian). The variant that applies the regulariser to the latent "
            "vectors directly (raw tokens) ran one seed and is reported only."),
           ("AR + SIGReg (head)", "Label-free + SIGReg (head)"),
           ("AR + SIGReg (raw tokens)", "Label-free + SIGReg (raw tokens)"),
           ("K1 (accuracy parity, shaped vs AR)", "Accuracy criterion (regularised against "
            "label-free)"),
           ("S of the shaped arm minus S of the AR arm", "S of the regularised network minus "
            "S of the label-free network"),
           ("(post-hoc reading 4a, same instances): models built from the AR arm's",
            "(measured after the runs, same instances): models built from the label-free "
            "network's")],
}


def relabel(key: str, head: list, rows: list, notes: list) -> tuple:
    def sub(x: str, counts: dict) -> str:
        for i, (a, b) in enumerate(RELABEL[key]):
            if a in x:
                counts[i] = counts.get(i, 0) + x.count(a)
                x = x.replace(a, b)
        return x

    counts: dict = {}
    head = [sub(h, counts) for h in head]
    rows = [["Label-free" if c == "AR" else sub(c, counts) for c in r] for r in rows]
    notes = [sub(n, counts) for n in notes]
    missing = [RELABEL[key][i][0] for i in range(len(RELABEL[key])) if i not in counts]
    if missing:
        raise SystemExit(f"relabel {key}: not found in the wp8 text: {missing}")
    if head[:2] == ["Architecture", "Tokens"]:          # one column: the network
        head = ["Network"] + head[2:]
        rows = [[r[0] if r[1] == "one per node" else f"Token bottleneck, M = {r[1]}"] + r[2:]
                for r in rows]
    return head, rows, notes


# ---------------------------------------------------------------- criteria
def _kill(report: dict, exp: str, idx: int = 0) -> dict:
    return report["results"][exp]["kills"][idx]


def criteria_rows(r2: dict, r3: dict, e1v: dict, e2v: dict, pilot: tuple,
                  rw: dict, vcm: dict, repro_max: float, vho: dict, vk: dict,
                  dates: dict) -> tuple:
    """(rows, rule positions): every pre-registered criterion of the runs the
    manuscript cites, with the measured value and the outcome as recorded, and
    which trainings each criterion read."""
    rows, rules = [], []
    g1 = r2["gate_g1_prime"]
    th = g1["thresholds"]
    rb = g1["reasons"]
    e5 = r2["results"]["e5"]
    if e5["protocol"].get("anchored_source") != "E1' balanced arm":
        raise SystemExit("2D: G1' (a) no longer reads the energy-term sub-experiment")
    xs = [p_["beats_zero_x"] for p_ in e5["metrics"]["per_budget"]]
    naive = sorted(k for k in e5["metrics"]["baselines"] if k != "zero")
    if naive != ["knn_field", "poly", "scale_aware_poly"]:
        raise SystemExit(f"2D: G1' (a) read other baselines than the text names: {naive}")
    b = re.search(r"egap reduction ([0-9.]+) .*vM reduction ([0-9.]+)", rb["b_physics"])
    c = re.search(r"egap \+([0-9.]+), disp \+([0-9.]+)", rb["c_transfer"])
    adv2 = r2["results"]["e8"]["metrics"]["ar_egap_advantage_by_budget"]
    k1n = _kill(r2, "e1")["note"]
    k1best = [float(x) for x in re.findall(r"[0-9.]+", k1n.split(":", 1)[1])]
    e7 = r2["results"]["e7"]
    e4 = r2["results"]["e4"]
    e4_big = max(e4["metrics"]["per_coarsen"], key=lambda r: r["coarsen"])

    def met(ok):
        return "met" if ok else "not met"

    def fired(k):
        return "triggered" if k else "not triggered"

    rows += [
        ["July run (2D), 16 July 2026", "G1′ (a), energy-term sub-experiment (separately "
         f"trained networks): supervised + energy term at least {e5['protocol']['margin']:g} "
         "times better than the zero field in displacement, and better than the two naive "
         f"baselines and the plain polynomial, fitted on {e5['protocol']['fit_budget']:,} "
         "labelled instances, at every budget",
         f"{min(xs):.1f}–{max(xs):.1f} times; baselines beaten at every budget",
         met(g1["conditions"]["a"])],
        ["", r"G1′ (b), \cref{tab:2djuly,tab:labeleffjuly}, 64 labels: the energy term lowers "
         f"the relative energy gap by ≥ {th['egap_reduction'] * 100:.0f}% and the von Mises "
         f"error by ≥ {th['vm_reduction'] * 100:.0f}%",
         f"{float(b.group(1)) * 100:.1f}%, {float(b.group(2)) * 100:.1f}%",
         met(g1["conditions"]["b"])],
        ["", r"G1′ (c), \cref{tab:2djuly,tab:labeleffjuly}, 64 labels: label-free, then "
         "supervised "
         "beats supervised by ≥ 10% in relative energy gap or ≥ 5% in displacement",
         f"{float(c.group(1)) * 100:.1f}%, {float(c.group(2)) * 100:.1f}%",
         met(g1["conditions"]["c"])],
        ["", "Gate G1′ = (a) and (b) and (c)", "", "GO" if g1["passed"] else "NO-GO"],
        ["", "K1, energy-term sub-experiment: the better of the fixed and the gradient-scaled "
         "energy term lowers the relative energy gap by < 25% at every budget",
         " / ".join(f"{x * 100:.1f}%" for x in k1best), fired(_kill(r2, "e1")["triggered"])],
        ["", r"K2, \cref{tab:2djuly}: label-free displacement error > 30% above supervised, "
         "1,024 labels",
         spct(seed_mean(r2, "ar", "disp_rel_l2") / seed_mean(r2, "labels", "disp_rel_l2") - 1),
         fired(_kill(r2, "e8", 0)["triggered"])],
        ["", r"C1-advantage, \cref{tab:labeleffjuly}: label-free relative energy-gap advantage "
         "over supervised < 40% at every budget",
         " / ".join(f"{adv2[k] * 100:.1f}%" for k in BUDGETS),
         fired(_kill(r2, "e8", 1)["triggered"])],
        ["", "K4: a latent-space regulariser raises the standardised effective rank of the "
         "latent vectors by ≤ 1.5 times",
         f"{r2['results']['e3']['metrics']['best_std_ratio']:.2f} times",
         fired(_kill(r2, "e3")["triggered"])],
        ["", f"K5: conjugate gradients from the prediction of a label-free network "
         f"({e7['protocol']['n_eval']} validation instances) save < 20% of the iterations from "
         "zero", spct(e7["metrics"]["savings_learned"]), fired(_kill(r2, "e7")["triggered"])],
        ["", f"K6: a cross-resolution invariance term shrinks the transfer gap by < 10% at "
         f"coarsening {e4_big['coarsen']:g}", spct(e4_big["gap_reduction"]),
         fired(_kill(r2, "e4")["triggered"])],
        ["", "E6 (alignment): within-geometry rank correlation of latent and solution "
         "distances < 0.3", f"{r2['results']['e6']['metrics']['rho_within_mean']:.3f}",
         fired(_kill(r2, "e6")["triggered"])],
        ["", "C5: any pre-registered check of the conditioning bound, the modewise identity or "
         "the conjugate-gradient bound violated", "none", fired(_kill(r2, "wp6")["triggered"])],
    ]
    rules.append(len(rows))
    k3 = _kill(rw, "e2")
    imp = rw["results"]["e2"]["metrics"]["jepa_vs_ar_improvements"]
    bud = list(imp)
    band = float(re.search(r"within ([0-9.]+)%", k3["condition"]).group(1))
    rows += [
        ["Joint-embedding run (2D), 31 July 2026", "K3: a self-supervised joint-embedding "
         "term added to label-free "
         f"pretraining changes the displacement error and the relative energy gap of the "
         f"transformer, fine-tuned with {', '.join(bud[:-1])} and {bud[-1]} labels, by less "
         f"than {band:g}% at every budget (if triggered, the term is dropped)",
         "change with the term, " + " / ".join(bud) + " labels: displacement "
         + " / ".join(spct(imp[bb]["disp"]) for bb in bud) + "; relative energy gap "
         + " / ".join(spct(imp[bb]["egap"]) for bb in bud) + " (positive: more accurate)",
         fired(k3["triggered"])],
    ]
    rules.append(len(rows))
    g2, ref = r3["gate_g2"], r3["gate_g2_reference_all_budgets"]
    t = g2["thresholds"]
    k = t["kills"]
    zero = {bb: seed_mean(r3, "zero", "disp_rel_l2", bb) for bb in BUDGETS}
    anc = {bb: seed_mean(r3, "labels_anchor", "disp_rel_l2", bb) for bb in BUDGETS}
    floor_ = int(t["gate"]["sanity_min_budget"])
    assessed = [bb for bb in BUDGETS if int(bb) >= floor_]
    parity = seed_mean(r3, "ar", "disp_rel_l2") / seed_mean(r3, "labels", "disp_rel_l2") - 1
    adv3 = [1 - seed_mean(r3, "ar", "energy_gap_rel") / seed_mean(r3, "labels",
                                                                   "energy_gap_rel", bb)
            for bb in BUDGETS]
    kp3 = [1 - seed_mean(r3, "labels_anchor", "energy_gap_rel", bb)
           / seed_mean(r3, "labels", "energy_gap_rel", bb) for bb in BUDGETS]
    p3 = r3["results"]["p3_transfer"]["metrics"]
    ratio = p3["ar"]["fine_disp_mean"] / p3["ar"]["inband_disp_mean"]
    naive_fine = min(p3["naive_at_fine"].values())
    rows += [
        ["Initial three-dimensional run, 21 September 2026", "Gate G2 and kill conditions as "
         "registered; the "
         "label-free objective was defective (deviation D14)", "(a), (b), (c) not met; KP1, "
         "KP2, KP4 triggered", "NO-GO"],
        ["Pilot of the amendment (3D), 22 September 2026", f"Label-free displacement error after "
         f"20 epochs < {pilot[1]}", f"{pilot[0]}", met(float(pilot[0]) < float(pilot[1]))],
        ["Three-dimensional comparison, 28 September 2026", f"G2 (a), budgets ≥ {floor_} "
         "(amendment), "
         r"\cref{tab:labeleff}: displacement-supervised transformer with the energy term at "
         f"least {t['gate']['sanity_x']:.0f} times better than the zero field "
         "in displacement, and better than both naive baselines",
         " / ".join(f"{zero[bb] / anc[bb]:.1f}" for bb in assessed) + " times; naive beaten",
         met(g2["conditions"]["a"])],
        ["", "G2 (a), every budget (the registered form, reported for reference)",
         f"{zero['16'] / anc['16']:.2f} times at 16 labels", met(ref["conditions"]["a"])],
        ["", r"G2 (b), \cref{tab:labeleff,tab:3d}: label-free displacement error within +"
         f"{t['gate']['parity_band'] * 100:.0f}% of the displacement-supervised transformer's "
         "at 1,024 labels, and relative "
         f"energy-gap advantage ≥ {t['gate']['egap_adv_min'] * 100:.0f}% at every budget",
         f"{spct(parity)}; " + " / ".join(f"{x * 100:.2f}%" for x in adv3),
         met(g2["conditions"]["b"])],
        ["", r"G2 (c), \cref{tab:transfer}: finer mesh, zero-shot displacement error ≤ "
         f"{t['gate']['transfer_win']} times in-band, and better than both naive baselines",
         f"{ratio:.2f} times; best naive {naive_fine:.3f} against "
         f"{p3['ar']['fine_disp_mean']:.3f}", met(g2["conditions"]["c"])],
        ["", "Gate G2 = (a) and ((b) or (c)), amended", "", "GO" if g2["passed"] else "NO-GO"],
        ["", "Gate G2, registered form (reference)", "", "GO" if ref["passed"] else "NO-GO"],
        ["", f"KP1: supervised (1,024 labels) better than label-free by > "
         f"{k['KP1_parity_pct'] * 100:.0f}% in displacement", spct(parity),
         fired(g2["kills"]["KP1"])],
        ["", f"KP2: relative energy-gap advantage < {k['KP2_egap_adv_min'] * 100:.0f}% at any "
         "budget", f"minimum {min(adv3) * 100:.1f}%", fired(g2["kills"]["KP2"])],
        ["", f"KP3: the energy term lowers the relative energy gap by < "
         f"{k['KP3_anchor_improv_min'] * 100:.0f}% at every budget",
         " / ".join(spct(x) for x in kp3), fired(g2["kills"]["KP3"])],
        ["", f"KP4: finer mesh, zero-shot displacement error > {k['KP4_transfer_ratio']} "
         "times in-band, or a naive baseline better", f"{ratio:.2f} times",
         fired(g2["kills"]["KP4"])],
        ["", "KP5: any pre-registered check of the conditioning bound, the modewise identity or "
         "the conjugate-gradient bound violated", "none", fired(g2["kills"]["KP5"])],
        ["", f"KP6 (alignment): within-geometry rank correlation of latent and solution "
         f"distances < {k['KP6_rho_within_min']}",
         f"{r3['results']['e6']['metrics']['rho_within_mean']:.3f}", fired(g2["kills"]["KP6"])],
    ]
    rules.append(len(rows))
    sd = e1v["S_delta"]
    rows += [
        ["Latent-\\hspace{0pt}regularisation run (2D), 29 September 2026",
         "Latent regularisation, K1: "
         "relative change of the displacement error or of the relative energy gap beyond the "
         "noise guard", "within the guard", fired(e1v["K1_parity"])],
        ["", "Latent regularisation, K2: the separation does not rise in any seed",
         "rose in every seed", fired(e1v["K2_no_effect"])],
        ["", f"Latent regularisation, GO: separation raised by ≥ {e1v['S_effect_floor']:g} in "
         "every seed", " / ".join(f"{x:+.3f}".replace("-", MINUS) for x in sd),
         "NO-GO" if not e1v["GO"] else "GO"],
    ]
    rules.append(len(rows))
    for m in (512, 1024):
        v = e2v[m]
        first = "Bottleneck run (3D), 30 September 2026" if m == 512 else ""
        rows += [
            [first, f"Token bottleneck, M = {m:,}, K1: in-band relative energy gap or "
             "finer-mesh displacement error worse than the label-free transformer's beyond the "
             "noise guard", f"{spct(v['egap_rel_change'])} (guard "
             f"{v['egap_threshold'] * 100:.1f}%), {spct(v['fine_disp_rel_change'])} "
             f"(guard {v['fine_disp_threshold'] * 100:.1f}%)", fired(v["K1_accuracy"])],
            ["", f"Token bottleneck, M = {m:,}, K2: finer-mesh training step longer than "
             f"{v['kill_s']:g} s", f"{v['fine_step_s']:.3f} s", fired(v["K2_speed"])],
            ["", f"Token bottleneck, M = {m:,}: outcome", "",
             "dropped" if v["verdict"] == "KILLED" else v["verdict"]],
        ]
    rules.append(len(rows))
    rows += cm2d_criteria_rows(vcm, repro_max)
    rules.append(len(rows))
    more, more_rules = followup_criteria_rows(vho, vk, dates)
    rules += [len(rows) + r for r in more_rules]
    rows += more
    return rows, tuple(rules)


LD, LK = r"$\mathcal{L}_D$", r"$\mathcal{L}_K$"


def _guard(h: dict) -> str:
    return f"{spct(h['rel_change'])} (guard {pct(h['threshold'])})"


ADJ_CM2D = ROOT / "scripts" / "adjudicate_cm2d.py"


CLAIMS = (("July run", ("K5",)),
          ("Three-dimensional comparison", ("G2 (a)", "G2 (b)", "G2 (c)", "Gate G2", "KP4")),
          ("Two-dimensional comparison", ("H1", "H2a", "H2b", "H3")),
          ("Three-dimensional energy-norm run", None))
"""The runs and criteria of the claims table (Appendix A): a run's rows whose criterion
begins with one of the given labels, every row when None. The claims of the holdout
evaluation are in the holdout table, beside their values on the validation instances."""


def claims_rows(rows: list) -> tuple:
    """(rows, rule positions) of the claims table: the rows of the criteria table that
    decide a claim of the paper, in its order, with the run named on the first row of each
    group and the references to tables of the supplementary material removed."""
    out, rules, run = [], [], ""
    for r in rows:
        if len(r) < 4:
            continue
        if r[0]:
            run = r[0]
        keep = next((labels for name, labels in CLAIMS if run.startswith(name)), False)
        if keep is False or (keep is not None and not r[1].startswith(keep)):
            continue
        crit = re.sub(r",?\s*\\cref\{[^}]*\}", "", r[1])
        first = not out or out[-1][4] != run
        if first and out:
            rules.append(len(out))
        out.append([run if first else "", crit, r[2], r[3], run])
    named = [x[0] for x in out if x[0]]
    if len(named) != len(CLAIMS) or not all(g.startswith(n) for g, (n, _) in
                                             zip(named, CLAIMS, strict=True)):
        raise SystemExit("claims table: the runs of CLAIMS are not in the criteria table, in "
                         "this order")
    return [x[:4] for x in out], tuple(rules)


def adjudicator_constant(v: dict, used: dict, name: str) -> float:
    """A constant of the stamped CM2D adjudicator, read from the script whose SHA-256
    the verdict file records (so the bound the text states is the one that was applied)."""
    data = ADJ_CM2D.read_bytes()
    h = hashlib.sha256(data).hexdigest()
    if h != v["adjudicator"]["sha256"][_rel(ADJ_CM2D)]:
        raise SystemExit("CM2D: scripts/adjudicate_cm2d.py is not the adjudicator that wrote "
                         "the verdict")
    used[_rel(ADJ_CM2D)] = h
    m = re.search(rf"^{name} = (\S+)$", data.decode("utf-8"), re.M)
    if m is None:
        raise SystemExit(f"CM2D: the adjudicator defines no {name}")
    return float(m.group(1))


def _pow10(x: float) -> str:
    """An exact power of ten as LaTeX math."""
    e = round(log10(x))
    if not np.isclose(x, 10.0 ** e, rtol=1e-12, atol=0):
        raise SystemExit(f"{x} is not a power of ten")
    return f"$10^{{{e}}}$"


def cm2d_criteria_rows(v: dict, repro_max: float) -> list:
    """The hypotheses of PREREG_CM2D (run of 9 October 2026), as the stamped
    adjudicator recorded them."""
    for h in ("H1", "H2a", "H2b"):
        if v[h]["verdict"] != "SUPPORTED":
            raise SystemExit(f"CM2D {h}: the text reports SUPPORTED, the verdict reads "
                             f"{v[h]['verdict']}")
    if v["H3"]["reading"] != "no difference shown (within the guard)":
        raise SystemExit(f"CM2D H3: the text reports no difference shown, the verdict reads "
                         f"{v['H3']['reading']}")
    if not v["reuse"]["ok"] or v["deviations"]:
        raise SystemExit("CM2D: a reuse check failed or the adjudicator recorded a deviation")
    if not v["reuse"]["reproduction_max_rel_dev"] <= repro_max:
        raise SystemExit("CM2D: the reuse deviation exceeds the adjudicator's bound")
    word = {"SUPPORTED": "supported"}
    return [
        ["Two-dimensional comparison, 9 October 2026", rf"H1, \cref{{tab:2d,tab:cm2d}}: "
         "label-free transformer lower "
         f"than the displacement-supervised transformer ({LD}) in relative energy gap beyond the noise "
         "guard, 1,024 labels", _guard(v["H1"]), word[v["H1"]["verdict"]]],
        ["", f"H2a: energy-norm-supervised transformer ({LK}) lower than the displacement-supervised transformer "
         f"({LD}) in relative energy gap beyond the guard", _guard(v["H2a"]),
         word[v["H2a"]["verdict"]]],
        ["", "H2b: energy-norm-supervised transformer lower than the displacement-supervised transformer in von "
         "Mises error beyond the guard", _guard(v["H2b"]), word[v["H2b"]["verdict"]]],
        ["", "H3 (a reading, no criterion): energy-norm-supervised transformer against the label-free "
         "transformer in relative energy gap", _guard(v["H3"]), "no difference shown"],
        ["", "Reuse: the label-free networks of the latent-regularisation run reproduce that "
         "run's per-instance relative energy gaps and displacement errors (largest relative "
         f"deviation at most {_pow10(repro_max)})",
         f"largest relative deviation {v['reuse']['reproduction_max_rel_dev']:g}", "passed"],
    ]


HOLD_CLAIMS = ("T1", "T2", "T3", "H1", "H2a", "H2b", "H2c", "D2")


def rpct(x: float) -> str:
    """A signed relative change in percent to one decimal, or more where one decimal would
    show a change strictly between -100% and 0 as -100.0%."""
    for dec in (1, 2, 3):
        txt = spct(x, dec)
        if not -1 < x < 0 or float(txt.replace(MINUS, "-").rstrip("%")) > -100:
            break
    return txt


def _rel_guard(x: dict) -> str:
    return f"{rpct(x['rel_change'])} (guard {pct(x['threshold'])})"


def _comparisons(per_metric: dict, key_seed: str, key_mean: str) -> tuple:
    """(comparisons holding, comparisons) of a claim read per seed and in the seed mean."""
    n = ok = 0
    for rec in per_metric.values():
        for x in list(rec[key_seed]) + [rec[key_mean]]:
            n += 1
            ok += bool(x)
    return ok, n


def followup_criteria_rows(vho: dict, vk: dict, dates: dict) -> tuple:
    """(rows, rule positions) of the holdout evaluation (PREREG_HOLDOUT) and of the
    three-dimensional energy-norm run (PREREG_K3D), as their adjudicators recorded
    them; the text's readings are checked in holdout_material and k3d_material."""
    c = vho["claims"]
    word = {"REPLICATED": "replicated", "NOT REPLICATED": "not replicated"}
    t1 = _comparisons(c["T1"]["per_metric"], "better_in_seed", "better_in_mean")
    d2 = _comparisons(c["D2"]["per_metric"], "holds_in_seed", "holds_in_mean")
    t2 = c["T2"]
    t3 = c["T3"]["per_row"]
    if t3["labels"]["load_cases"] != t3["mgn"]["load_cases"]:
        raise SystemExit("holdout T3: the two networks read different numbers of load cases")
    h3 = vho["readings"]["H3"]
    if h3["reading"] != "no difference shown (within the guard)":
        raise SystemExit("holdout H3: the text reports no difference shown")
    V = vho["V"]
    rows = [
        [f"Holdout evaluation, {dates['holdout']}", "T1 (3D): label-free transformer better "
         "than the displacement-supervised transformer on all five metrics, in each seed and in the seed "
         "mean", f"{t1[0]} of {t1[1]} comparisons", word[c["T1"]["verdict"]]],
        ["", "T2 (3D): graph network's displacement error lower than the label-free "
         "transformer's on more than 50% of the instances in each seed, and its von Mises "
         "error higher on at least 95% of the instance-seed pairs",
         f"{pct(min(t2['disp_lower_share_per_seed']))}–"
         f"{pct(max(t2['disp_lower_share_per_seed']))}; {upct(t2['vm_higher_share_pooled'])}",
         word[t2["verdict"]]],
        ["", "T3 (3D): each displacement-supervised network has load cases worse than the "
         "zero field, "
         "each with a positive energy and no other",
         f"{t3['labels']['worse']:,} and {t3['mgn']['worse']:,} of "
         f"{t3['labels']['load_cases']:,} load cases", word[c["T3"]["verdict"]]],
        ["", f"H1 (2D): label-free transformer lower than the displacement-supervised transformer ({LD}) "
         "in relative energy gap beyond the noise guard", _rel_guard(c["H1"]),
         word[c["H1"]["verdict"]]],
        ["", f"H2a (2D): energy-norm-supervised transformer ({LK}) lower than the "
         "displacement-supervised transformer in relative energy gap beyond the guard",
         _rel_guard(c["H2a"]),
         word[c["H2a"]["verdict"]]],
        ["", "H2b (2D): energy-norm-supervised transformer lower than the displacement-supervised transformer in "
         "von Mises error beyond the guard", _rel_guard(c["H2b"]), word[c["H2b"]["verdict"]]],
        ["", "H2c (2D): energy-norm-supervised transformer's von Mises error less than half the "
         "displacement-supervised transformer's, rel below −50%", spct(c["H2c"]["rel_change"]),
         word[c["H2c"]["verdict"]]],
        ["", "D2 (2D): label-free transformer's displacement error higher than the "
         "displacement-supervised transformer's and its other four metrics better, in each seed and in the seed "
         "mean", f"{d2[0]} of {d2[1]} comparisons", word[c["D2"]["verdict"]]],
        ["", "H3 (2D, a reading without a criterion): energy-norm-supervised transformer against the "
         "label-free transformer in relative energy gap", _rel_guard(h3),
         "no difference shown"],
        ["", "V: the per-instance values of every network and metric distributed alike on "
         "the holdout and the validation instances (two-sided Mann–Whitney tests, Holm's "
         f"procedure at a family-wise level of {pct(V['alpha'], 0)})",
         f"{len(V['quantities'])} quantities, {words(len(V['rejected']))} rejected",
         r"\hspace{0pt}" + V["verdict"].lower()],
    ]
    rules = [len(rows)]
    supported = {"SUPPORTED": "supported", "NOT SUPPORTED": "not supported"}
    rows += [
        [f"Three-dimensional energy-norm run, {dates['k3d']}", f"H2a-3D: energy-norm-supervised "
         f"transformer ({LK}) lower than the displacement-supervised transformer ({LD}) in relative energy "
         "gap beyond the noise guard, on the seeds' medians", _rel_guard(vk["H2a-3D"]),
         supported[vk["H2a-3D"]["verdict"]]],
        ["", "H2b-3D: the same in von Mises error", _rel_guard(vk["H2b-3D"]),
         supported[vk["H2b-3D"]["verdict"]]],
        ["", "H3-3D (a reading without a criterion): energy-norm-supervised transformer against the "
         "label-free transformer in relative energy gap, on the seeds' medians",
         _rel_guard(vk["H3-3D"]), "energy-norm-supervised transformer lower"],
    ]
    if vk["H3-3D"]["reading"] != "the stiffness-norm transformer lower beyond the guard":
        raise SystemExit("K3D H3-3D: the table reports the energy-norm-supervised transformer lower")
    return rows, rules


CM2D_HYP = (("H1", "ar", "labels", "energy_gap_rel"),
            ("H2a", "labels_knorm", "labels", "energy_gap_rel"),
            ("H2b", "labels_knorm", "labels", "vm_rel_l2"),
            ("H3", "labels_knorm", "ar", "energy_gap_rel"))
HYP_NAMES = {a: NAMES[a] for a in ("ar", "labels", "labels_knorm")}
HYP_METRICS = {"energy_gap_rel": "Relative energy gap", "vm_rel_l2": "von Mises error"}


def _interval(lo: float, hi: float, dec: int) -> str:
    return f"{spct(lo, dec)} to {spct(hi, dec)}"


def cm2d_hypothesis_table(v: dict, rc: dict) -> tuple:
    """(head, rows, notes) of the table of PREREG_CM2D's comparisons with the readings
    its Sec. 4 requires beside each (per-seed values, rel, SE_rel and guard; the guard
    on the seeds' medians; Welch's interval; the instance-resampling interval)."""
    head = ["", "H1", "H2a", "H2b", "H3"]
    rows = {k: [k] for k in ("Network A", "Reference B", "Metric", "A, seeds 0, 1, 2",
                             "B, seeds 0, 1, 2", "rel", "SE_rel", "Guard", "Reading",
                             "Medians: rel (guard)", "Welch 95% interval",
                             "Instance resampling 95%")}
    for h, a, b, m in CM2D_HYP:
        x = v[h]
        if not (x["metric"] == m and x["new_per_seed"] == seed_values(rc, a, "1024", m)
                and x["base_per_seed"] == seed_values(rc, b, "1024", m)):
            raise SystemExit(f"CM2D {h}: the verdict's comparison is not the table's")
        rb, w, ir = x["robustness"]["medians"], x["robustness"]["welch_95"], \
            x["robustness"]["instance_resampling_95"]
        if not (np.isclose(w["rel_change"], x["rel_change"], rtol=1e-12, atol=0)
                and w["level"] == ir["level"] == 0.95 and ir["resamples"] == 2000):
            raise SystemExit(f"CM2D {h}: the robustness readings are not those of the table")
        reading = (x["verdict"].lower() if h != "H3" else "no difference shown")
        for k, val in (("Network A", HYP_NAMES[a]), ("Reference B", HYP_NAMES[b]),
                       ("Metric", HYP_METRICS[m]),
                       ("A, seeds 0, 1, 2", ", ".join(num(t) for t in x["new_per_seed"])),
                       ("B, seeds 0, 1, 2", ", ".join(num(t) for t in x["base_per_seed"])),
                       ("rel", spct(x["rel_change"])), ("SE_rel", pct(x["se_rel"])),
                       ("Guard", pct(x["threshold"])), ("Reading", reading),
                       ("Medians: rel (guard)",
                        f"{spct(rb['rel_change'])} ({pct(rb['threshold'])})"),
                       ("Welch 95% interval", _interval(w["low"], w["high"], 0)),
                       ("Instance resampling 95%", _interval(ir["low"], ir["high"], 1))):
            rows[k].append(val)
    ex = v["H3"]["roles_exchanged"]
    notes = [
        r"rel, SE_rel and the noise guard as defined in the note to \cref{tab:criteria}, over "
        "the three seeds' values, each the mean over the 256 validation instances and their "
        "four load cases.",
        "Medians: the same reading on each seed's median over the instances instead of its "
        "mean. Welch: rel ± t × SE_rel, with t the 97.5% quantile of Student's distribution "
        "at the Welch–Satterthwaite degrees of freedom, a symmetric interval that can extend "
        "below −100%. Instance resampling: the 2.5% and "
        "97.5% percentiles of rel over 2,000 resamplings of the 256 validation instances, "
        "the same instances drawn for both networks and every seed, the seeds kept.",
        "H3 is a reading without a criterion. With the roles of A and B exchanged, rel was "
        f"{spct(ex['rel_change'])} against a guard of {pct(ex['threshold'])}.",
    ]
    return head, list(rows.values()), notes


# ---------------------------------------------------------------- numbers
class Numbers(dict):
    def put(self, key: str, value: str) -> None:
        if not key.isalpha():
            raise SystemExit(f"macro name {key!r} is not letters only")
        if key in self:
            raise SystemExit(f"macro {key!r} defined twice")
        self[key] = value


def _sci(x: float, sig: int = 2) -> str:
    """x as m x 10^e (LaTeX math, for macros used in text mode)."""
    e = int(floor(log10(abs(x))))
    m = x / 10 ** e
    return f"${m:.{sig - 1}f} \\times 10^{{{e}}}$"


TAG = {"ar": "Free", "labels": "Lab", "labels_anchor": "Anc", "mgn": "Mgn", "ar_ft": "Ft",
       "labels_knorm": "Knorm"}
MTAG = dict(zip(METRICS, ("Disp", "Gap", "Vm", "Peak", "Recall"), strict=True))


def numbers(r2: dict, rd: dict, r3: dict, amps: dict, e1base: dict, rw: dict,
            rcm: dict) -> Numbers:
    """Every number the manuscript's text quotes, by macro name. Statements the
    text makes about the records ("in every seed", "on every metric") are
    checked here and stop the build when the records disagree. Macro prefixes:
    Two, the 2D run of 16 July 2026; Cm, the 2D comparison with the current code
    (CM2D, run of 9 October 2026); Three, the 3D amended run."""
    N = Numbers()
    tag, mtag = TAG, MTAG
    for dim, rep in (("Two", r2), ("Cm", rcm), ("Three", r3)):
        for arm in TRAINED:
            if arm not in cells(rep):
                continue
            A = tag[arm]
            for m in METRICS:
                N.put(f"num{dim}{A}{mtag[m]}", num(seed_mean(rep, arm, m)))
            k, n = worse_than_zero(rep, arm)
            N.put(f"num{dim}{A}Worse", f"{k:,}")
            N.put(f"num{dim}{A}GapMedian",
                  num(float(np.median(per_instance(rep, arm, "energy_gap_rel")))))
        N.put(f"num{dim}Pairs", f"{per_instance(rep, 'ar', 'energy_gap_rel').size:,}")
        N.put(f"num{dim}Val", f"{per_instance(rep, 'ar', 'energy_gap_rel').shape[1]:,}")
        N.put(f"num{dim}FreeDispFour", f"{seed_mean(rep, 'ar', 'disp_rel_l2'):.4f}")
        N.put(f"num{dim}LabDispFour", f"{seed_mean(rep, 'labels', 'disp_rel_l2'):.4f}")
    # ------------------------------------------------ two dimensions
    d_ar, d_lab = seed_mean(r2, "ar", "disp_rel_l2"), seed_mean(r2, "labels", "disp_rel_l2")
    N.put("numTwoFreeDispExcess", spct(d_ar / d_lab - 1))
    N.put("numTwoFreeDispExcessAbs", pct(abs(d_ar / d_lab - 1)))
    trained2 = [seed_mean(r2, a, "energy_gap_rel") for a in TRAINED if a in cells(r2)]
    N.put("numTwoGapSpread", f"{max(trained2) / min(trained2):.0f}")
    # solves (labels): 2D offline + in-run ledger; 3D from the labels the run consumed
    de2 = r2["data_economy"]
    off = de2["labelled_instances"] * de2["solves_per_labelled_instance"]
    N.put("numTwoSolvesOffline", f"{off:,}")
    N.put("numTwoSolvesRun", f"{de2['ledger']['total']:,}")
    N.put("numTwoSolves", f"{off + de2['ledger']['total']:,}")
    lp = r3["labels_present"]
    n_l = lp["n_loads"]
    n_all = (lp["inband_val_n"] + lp["inband_prefix_n"] + lp["fine_val_n"]
             + lp["fine_prefix_n"])
    N.put("numThreeSolves", f"{n_all * n_l:,}")
    N.put("numThreeEvalSolves", f"{(lp['inband_val_n'] + lp['fine_val_n']) * n_l:,}")
    N.put("numThreeTrainSolves", f"{lp['inband_prefix_n'] * n_l:,}")
    N.put("numThreeFewSolves", f"{lp['fine_prefix_n'] * n_l:,}")
    if not all(a > b for a, b in zip(seed_values(r2, "ar", "1024", "disp_rel_l2"),
                                     seed_values(r2, "labels", "1024", "disp_rel_l2"),
                                     strict=True)):
        raise SystemExit("2D: the text says the label-free displacement error is above the "
                         "supervised one in every seed; the records disagree")
    # label efficiency statements of Section 5.2
    ar_gap = seed_mean(r2, "ar", "energy_gap_rel")
    for arm in ("labels", "labels_anchor", "ar_ft", "mgn"):
        for bb in BUDGETS:
            if not ar_gap < seed_mean(r2, arm, "energy_gap_rel", bb):
                raise SystemExit(f"2D: label-free energy gap not below {arm} at {bb}")
    passes = [bb for bb in BUDGETS if seed_mean(r2, "labels", "disp_rel_l2", bb) < d_ar]
    if passes != ["1024"]:
        raise SystemExit(f"2D: the supervised network passes the label-free one at {passes}")
    if not (seed_mean(r2, "labels_anchor", "disp_rel_l2", "16")
            > seed_mean(r2, "labels", "disp_rel_l2", "16")):
        raise SystemExit("2D: the energy term did not raise the displacement error at 16")
    N.put("numTwoAncSixteenSeeds", ", ".join(
        num(x) for x in seed_values(r2, "labels_anchor", "16", "disp_rel_l2")))
    N.put("numTwoLabOverFreeGap", times(seed_mean(r2, "labels", "energy_gap_rel")
                                        / seed_mean(r2, "ar", "energy_gap_rel")))
    for arm in ("labels", "labels_anchor", "ar_ft", "mgn"):
        for m in ("energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err"):
            if not seed_mean(r2, "ar", m) < seed_mean(r2, arm, m):
                raise SystemExit(f"2D: label-free not better than {arm} in {m}")
        if not seed_mean(r2, "ar", "crit_recall") > seed_mean(r2, arm, "crit_recall"):
            raise SystemExit(f"2D: label-free recall not above {arm}")
    g1 = r2["gate_g1_prime"]
    b = re.search(r"egap reduction ([0-9.]+) \(need >= ([0-9.]+)\), vM reduction ([0-9.]+) "
                  r"\(need >= ([0-9.]+)\)", g1["reasons"]["b_physics"])
    N.put("numGOneGapReduction", pct(float(b.group(1))))
    N.put("numGOneVmReduction", pct(float(b.group(3))))
    c = re.search(r"egap \+([0-9.]+), disp \+([0-9.]+)", g1["reasons"]["c_transfer"])
    N.put("numGOneFtGap", pct(float(c.group(1))))
    N.put("numGOneFtDisp", pct(float(c.group(2))))
    N.put("numGOneRetired", pct(g1["retired_displacement_criterion"]
                                ["fixed_disp_improvement_at_decision"]["value"]))
    e5 = r2["results"]["e5"]["metrics"]["per_budget"]
    N.put("numGOneSanityMin", f"{min(p['beats_zero_x'] for p in e5):.1f}")
    N.put("numGOneSanityMax", f"{max(p['beats_zero_x'] for p in e5):.1f}")
    margin = r2["results"]["e5"]["protocol"]["margin"]
    x16 = (seed_mean(r2, "zero", "disp_rel_l2", "16")
           / seed_mean(r2, "labels_anchor", "disp_rel_l2", "16"))
    if not x16 < margin:
        raise SystemExit("2D: the table's 16-label energy-term network now meets the sanity "
                         "factor; the text says it would not have")
    N.put("numGOneSanityTableSixteen", f"{x16:.1f}")
    # ------------------------------------------------ the joint-embedding comparison (K3)
    k3 = _kill(rw, "e2")
    if not k3["condition"].startswith("K3") or k3["triggered"]:
        raise SystemExit("K3: the record no longer reads 'not triggered'")
    band = float(re.search(r"within ([0-9.]+)%", k3["condition"]).group(1)) / 100
    imp = rw["results"]["e2"]["metrics"]["jepa_vs_ar_improvements"]
    cells_k3 = [(bb, m, v[m]) for bb, v in imp.items() for m in ("disp", "egap")]
    out = [c_ for c_ in cells_k3 if abs(c_[2]) > band]
    gains = [c_ for c_ in out if c_[2] > 0]
    if [(g_[0], g_[1]) for g_ in gains] != [("64", "egap")]:
        raise SystemExit("K3: the single gain outside the band is no longer the 64-label gap")
    N.put("numKthreeBand", pct(band, 0))
    N.put("numKthreeOutside", words(len(out)))
    N.put("numKthreeWorse", words(len(out) - len(gains)))
    N.put("numKthreeGain", pct(gains[0][2]))
    base = rw["results"]["e2"]["metrics"]["table"]["ar_ft"]["64"]["egap"]["per_seed"]
    N.put("numKthreeBaseSeeds", ", ".join(num(x) for x in base[:-1]) + f" and {num(base[-1])}")
    ref64 = seed_values(r2, "ar_ft", "64", "energy_gap_rel")
    if not max(ref64) < min(base):
        raise SystemExit("K3: the 16 July fine-tuned network no longer beats every seed of the "
                         "31 July baseline at 64 labels")
    N.put("numKthreeBaseRef", ms(ref64))
    adv = r2["results"]["e8"]["metrics"]["ar_egap_advantage_by_budget"]
    N.put("numTwoAdvMax", pct(max(adv.values())))
    N.put("numTwoAdvMin", pct(min(adv.values())))
    e7 = r2["results"]["e7"]
    it = e7["metrics"]["iterations_to_tol_mean"]
    N.put("numKfiveZero", f"{it['zero']:.1f}")
    N.put("numKfiveFree", f"{it['learned']:.1f}")
    N.put("numKfiveNaive", f"{it['naive']:.1f}")
    N.put("numKfiveSaving", spct(e7["metrics"]["savings_learned"]))
    N.put("numKfiveNaiveSaving", spct(e7["metrics"]["savings_naive"]))
    N.put("numKfiveTol", f"$10^{{{int(round(log10(e7['protocol']['tol'])))}}}$")
    N.put("numKfiveEval", str(e7["protocol"]["n_eval"]))
    pk = e7["metrics"]["polish_at_k"]
    N.put("numKfiveStartGap", num(pk["0"]["energy_gap_rel"]))
    N.put("numKfiveFiveGap", num(pk["5"]["energy_gap_rel"]))
    N.put("numKfiveTwentyGap", num(pk["20"]["energy_gap_rel"]))
    g0 = pk["0"]["energy_gap_rel"]
    for eps, E in ((1e-7, "Seven"), (1e-12, "Twelve"), (1e-17, "Seventeen")):
        N.put(f"numWarmFraction{E}", pct(float(np.log(1 / g0) / np.log(4 / eps)), 0))
    e4 = sorted(r2["results"]["e4"]["metrics"]["per_coarsen"], key=lambda r: r["coarsen"])
    for row, C in zip(e4, ("Low", "High"), strict=True):
        N.put(f"numCoarsen{C}", f"{row['coarsen']:g}")
        N.put(f"numCoarsen{C}Coarse", num(row["inv_off"]["err_coarse"]))
        N.put(f"numCoarsen{C}Fine", num(row["inv_off"]["err_fine"]))
        N.put(f"numCoarsen{C}Reduction", spct(row["gap_reduction"]))
        if not row["gap_reduction"] < 0:
            raise SystemExit("2D: the text says the regulariser widened the transfer gap")
        N.put(f"numCoarsen{C}Widen", pct(-row["gap_reduction"]))
    disp9 = (seed_values(r2, "ar", "1024", "disp_rel_l2")
             + seed_values(rd, "ar", "1024", "disp_rel_l2"))
    gap9 = (seed_values(r2, "ar", "1024", "energy_gap_rel")
            + seed_values(rd, "ar", "1024", "energy_gap_rel"))
    N.put("numTwoRuns", words(len(disp9)))
    N.put("numTwoRunsDisp", f"{statistics.fmean(disp9):.4f} ± {statistics.stdev(disp9):.4f}")
    N.put("numTwoRunsGap", f"{statistics.fmean(gap9):.4f} ± {statistics.stdev(gap9):.4f}")
    N.put("numDiagSeeds", words(len(seed_values(rd, "ar", "1024", "disp_rel_l2"))))
    arms = rd["results"]["e1"]["metrics"]["per_budget"][0]["arms"]
    scaled = (arms["balanced"]["disp"]["per_seed"]
              + seed_values(rd, "labels_anchor", "16", "disp_rel_l2"))
    fixed = arms["fixed"]["disp"]["per_seed"]
    N.put("numDiagScaledMin", num(min(scaled), 2))
    N.put("numDiagScaledMax", num(max(scaled), 2))
    N.put("numDiagFixedMin", num(min(fixed), 2))
    N.put("numDiagFixedMax", num(max(fixed), 2))
    N.put("numDiagFixedSeeds", words(len(fixed)))
    eb = e1base["results"]["e8"]["metrics"]["cells"]["ar"]
    eb = eb[max(eb, key=int)]
    N.put("numEOneBaseDisp", num(statistics.fmean(eb["disp_rel_l2"]["per_seed"])))
    N.put("numEOneBaseGap", num(statistics.fmean(eb["energy_gap_rel"]["per_seed"])))
    e1v = json.loads((REC8 / "e1" / "e1_verdict.json").read_text())
    N.put("numEOneFloor", f"{e1v['S_effect_floor']:g}")
    N.put("numEOneDeltaMin", f"{min(e1v['S_delta']):.3f}")
    N.put("numEOneDeltaMax", f"{max(e1v['S_delta']):.3f}")
    kap = [rep["results"]["wp6"]["metrics"]["conditioning"]["kappa_range"] for rep in (r2, r3)]
    N.put("numSqrtKappaMin", f"{min(k[0] for k in kap) ** 0.5:.0f}")
    N.put("numSqrtKappaMax", f"{max(k[1] for k in kap) ** 0.5:.0f}")
    modes: dict = {}
    for rep, D in ((r2, "Two"), (r3, "Three")):
        w = rep["results"]["wp6"]["metrics"]
        lo, hi = w["conditioning"]["kappa_range"]
        N.put(f"numKappa{D}Low", _sci(lo))
        N.put(f"numKappa{D}High", _sci(hi))
        N.put(f"numCond{D}", f"{w['conditioning']['max_ratio']:.3f}")
        N.put(f"numModes{D}", _sci(w["mode_contraction"]["max_err"], 1))
        modes[D] = _sci(w["mode_contraction"]["max_err"], 1)
        N.put(f"numCheb{D}", f"{w['chebyshev_polish']['worst_measured_over_bound']:.3f}")
        wit = w["prop1_naive_cross"]["witness"]
        if not (w["prop1_naive_cross"]["naive_extension_falsified"]
                and wit["d_cross"] < wit["a_within_min"]):
            raise SystemExit(f"{D}: the cross-geometry counterexample is not on record")
        N.put(f"numCross{D}", _sci(wit["d_cross"], 3))
        N.put(f"numWithin{D}", _sci(wit["a_within_min"], 3))
        N.put(f"numPremise{D}", f"{w['prop1_premise']['min_separation']:.3f}")
        N.put(f"numRho{D}", f"{rep['results']['e6']['metrics']['rho_within_mean']:.3f}")
    N.put("numModesPhrase", f"{modes['Two']} in both dimensions"
          if modes["Two"] == modes["Three"]
          else f"{modes['Two']} (two dimensions) and {modes['Three']} (three dimensions)")
    # ------------------------------------------------ three dimensions
    for arm in ("labels", "labels_anchor"):
        for m in METRICS:
            hi_better = m == "crit_recall"
            a, s = seed_mean(r3, "ar", m), seed_mean(r3, arm, m)
            per_seed = [(x > y) if hi_better else (x < y) for x, y in zip(
                seed_values(r3, "ar", "1024", m), seed_values(r3, arm, "1024", m), strict=True)]
            if not (((a > s) if hi_better else (a < s)) and all(per_seed)):
                raise SystemExit(f"3D: the label-free network is not better than {arm} in {m} "
                                 "in the mean and in every seed")
    # statements of Sections 6.1-6.4 about the graph network and the budgets
    for m in ("energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err"):
        if not seed_mean(r3, "ar", m) < seed_mean(r3, "mgn", m):
            raise SystemExit(f"3D: label-free not better than the graph network in {m}")
    if not (seed_mean(r3, "ar", "crit_recall") > seed_mean(r3, "mgn", "crit_recall")
            and seed_mean(r3, "mgn", "disp_rel_l2") < seed_mean(r3, "ar", "disp_rel_l2")
            < seed_mean(r3, "mgn", "disp_rel_l2", "64")):
        raise SystemExit("3D: graph network recall/displacement statements do not hold")
    d3 = seed_mean(r3, "ar", "disp_rel_l2")
    g3 = seed_mean(r3, "ar", "energy_gap_rel")
    for arm in ("labels", "labels_anchor", "mgn"):
        for bb in cells(r3)[arm]:
            if not g3 < seed_mean(r3, arm, "energy_gap_rel", bb):
                raise SystemExit(f"3D: label-free energy gap not below {arm} at {bb}")
            if arm != "mgn" and not d3 < seed_mean(r3, arm, "disp_rel_l2", bb):
                raise SystemExit(f"3D: label-free displacement not below {arm} at {bb}")
    worse_anc = [bb for bb in BUDGETS if seed_mean(r3, "labels_anchor", "disp_rel_l2", bb)
                 > seed_mean(r3, "labels", "disp_rel_l2", bb)]
    if worse_anc != ["256"]:
        raise SystemExit(f"3D: the energy term raised the displacement error at {worse_anc}")
    worse_anc_gap = [bb for bb in BUDGETS if seed_mean(r3, "labels_anchor", "energy_gap_rel", bb)
                     > seed_mean(r3, "labels", "energy_gap_rel", bb)]
    if worse_anc_gap != ["256"]:
        raise SystemExit(f"3D: the energy term raised the energy gap at {worse_anc_gap}")
    up_d = sum(a > b for a, b in zip(seed_values(r3, "labels_anchor", "256", "disp_rel_l2"),
                                     seed_values(r3, "labels", "256", "disp_rel_l2"),
                                     strict=True))
    up_g = sum(a > b for a, b in zip(seed_values(r3, "labels_anchor", "256", "energy_gap_rel"),
                                     seed_values(r3, "labels", "256", "energy_gap_rel"),
                                     strict=True))
    if (up_d, up_g) != (3, 1):
        raise SystemExit(f"3D, 256 labels: the energy term raised the displacement error in "
                         f"{up_d} seeds and the energy gap in {up_g}; the text says 3 and 1")
    N.put("numThreeLabWorseTwoFiveSix", f"{worse_than_zero(r3, 'labels', '256')[0]:,}")
    N.put("numThreeAncWorseTwoFiveSix", f"{worse_than_zero(r3, 'labels_anchor', '256')[0]:,}")
    g1024 = per_instance(r3, "labels", "energy_gap_rel", "1024")
    worst = int(np.argmax(g1024.max(axis=0)))
    if not (np.delete(g1024, worst, axis=1).mean()
            < seed_mean(r3, "labels", "energy_gap_rel", "256")):
        raise SystemExit("3D: the rise of the supervised energy gap is not one instance's")
    if not (seed_mean(r3, "labels", "energy_gap_rel", "1024")
            > seed_mean(r3, "labels", "energy_gap_rel", "256")):
        raise SystemExit("3D: the supervised energy gap did not rise from 256 to 1,024")
    N.put("numThreeFreeDispAdvantage",
          pct(1 - seed_mean(r3, "ar", "disp_rel_l2") / seed_mean(r3, "labels", "disp_rel_l2")))
    N.put("numThreeAncOverFreeGap", times(seed_mean(r3, "labels_anchor", "energy_gap_rel")
                                          / seed_mean(r3, "ar", "energy_gap_rel")))
    # the same ratio for the stiffness-norm error: the seed mean of g is the mean of g
    # over every seed, instance and load case (equal counts), so the square root of the
    # ratio of seed means is the ratio of the root-mean-square relative stiffness-norm
    # errors, g^(1/2), over all predictions
    N.put("numThreeAncOverFreeGapRoot", times(np.sqrt(
        seed_mean(r3, "labels_anchor", "energy_gap_rel") / seed_mean(r3, "ar", "energy_gap_rel"))))
    N.put("numThreeMgnOverFreeVm", times(seed_mean(r3, "mgn", "vm_rel_l2")
                                         / seed_mean(r3, "ar", "vm_rel_l2")))
    N.put("numThreeMgnOverFreePeak", times(seed_mean(r3, "mgn", "peak_vm_rel_err")
                                           / seed_mean(r3, "ar", "peak_vm_rel_err")))
    N.put("numThreeFreeOverMgnDisp", times(seed_mean(r3, "ar", "disp_rel_l2")
                                           / seed_mean(r3, "mgn", "disp_rel_l2")))
    lab = per_instance(r3, "labels", "energy_gap_rel")
    N.put("numThreeLabGapMs", ms(seed_values(r3, "labels", "1024", "energy_gap_rel")))
    N.put("numThreeLabGapSeeds", ", ".join(num(x) for x in
                                            seed_values(r3, "labels", "1024", "energy_gap_rel")))
    N.put("numThreeLabWorst", f"{lab.max():,.0f}")
    s_worst = int(np.unravel_index(np.argmax(lab), lab.shape)[0])
    N.put("numThreeLabWorstSeed", str(s_worst))
    worst = [int(np.argmax(lab[i])) for i in range(lab.shape[0])]
    if len(set(worst)) != 1:
        raise SystemExit(f"3D: the supervised arm's worst instance differs between seeds: {worst}")
    w = worst[0]
    N.put("numWorstIndex", str(w))
    N.put("numWorstSeedLabDisp", num(per_instance(r3, "labels", "disp_rel_l2")[s_worst, w], 2))
    N.put("numWorstSeedLabVm", num(per_instance(r3, "labels", "vm_rel_l2")[s_worst, w], 2))
    N.put("numWorstSeedLabPeak", num(per_instance(r3, "labels", "peak_vm_rel_err")[s_worst, w], 3))
    for arm in ("ar", "labels", "mgn"):
        A = tag[arm]
        N.put(f"numWorst{A}Disp", num(per_instance(r3, arm, "disp_rel_l2")[0, w], 2))
        N.put(f"numWorst{A}Gap", num(per_instance(r3, arm, "energy_gap_rel")[0, w], 3))
        N.put(f"numWorst{A}Vm", num(per_instance(r3, arm, "vm_rel_l2")[0, w], 2))
    fr = {m: per_instance(r3, "ar", m) for m in METRICS}
    mg = {m: per_instance(r3, "mgn", m) for m in METRICS}
    disp_lower = (mg["disp_rel_l2"] < fr["disp_rel_l2"]).mean(axis=1)
    vm_higher = mg["vm_rel_l2"] > fr["vm_rel_l2"]
    gap_higher = (mg["energy_gap_rel"] > fr["energy_gap_rel"]).mean(axis=1)
    peak_lower = (mg["peak_vm_rel_err"] < fr["peak_vm_rel_err"]).mean(axis=1)
    N.put("numMgnDispLowerMin", pct(disp_lower.min()))
    N.put("numMgnDispLowerMax", pct(disp_lower.max()))
    N.put("numMgnVmHigher", f"{int(vm_higher.sum()):,}")
    N.put("numMgnGapHigherMin", pct(gap_higher.min()))
    N.put("numMgnPeakLowerMin", pct(peak_lower.min(), 0))
    N.put("numMgnPeakLowerMax", pct(peak_lower.max(), 0))
    both = (mg["disp_rel_l2"] < fr["disp_rel_l2"]) & vm_higher
    N.put("numMgnLowerDispHigherVm", f"{int(both.sum()):,}")
    med_ar = float(np.median(per_instance(r3, "ar", "energy_gap_rel")))
    ratios = [float(np.median(per_instance(r3, a, "energy_gap_rel"))) / med_ar
              for a in ("labels", "labels_anchor", "mgn")]
    N.put("numThreeMedianRatioMin", f"{min(ratios):.0f}")
    N.put("numThreeMedianRatioMax", f"{max(ratios):.0f}")
    # per load case, the label-free network (post-hoc records: |u|_K, |U*|_K and cos_K)
    pos = tot = 0
    for s in amps["transformer"]["seeds"].values():
        for row in s["inband"]["per_instance"]:
            u, us, cs = (np.asarray(row[k], float) for k in ("u_norm_K", "ustar_norm_K", "cos_K"))
            r = u / us
            pos += int(np.sum(r * r - 2 * r * cs + 1 > 1))
            tot += r.size
    N.put("numThreeFreeLoadWorse", f"{pos:,}")
    N.put("numThreeFreeLoads", f"{tot:,}")
    # the gate, both readings
    g2, ref = r3["gate_g2"], r3["gate_g2_reference_all_budgets"]
    t = g2["thresholds"]
    zero = {bb: seed_mean(r3, "zero", "disp_rel_l2", bb) for bb in BUDGETS}
    anc = {bb: seed_mean(r3, "labels_anchor", "disp_rel_l2", bb) for bb in BUDGETS}
    N.put("numGTwoSanityX", f"{t['gate']['sanity_x']:.1f}")
    N.put("numGTwoSanitySixteen", f"{zero['16'] / anc['16']:.2f}")
    N.put("numGTwoSanitySixtyFour", f"{zero['64'] / anc['64']:.1f}")
    N.put("numGTwoSanityMax", f"{zero['1024'] / anc['1024']:.1f}")
    N.put("numGTwoFloor", str(t["gate"]["sanity_min_budget"]))
    N.put("numGTwoParity", spct(seed_mean(r3, "ar", "disp_rel_l2")
                                / seed_mean(r3, "labels", "disp_rel_l2") - 1))
    adv3 = [1 - seed_mean(r3, "ar", "energy_gap_rel") / seed_mean(r3, "labels",
                                                                   "energy_gap_rel", bb)
            for bb in BUDGETS]
    N.put("numGTwoAdvMin", pct(min(adv3)))
    if not (g2["passed"] and not ref["passed"] and g2["kills"]["KP4"]):
        raise SystemExit("3D: the text reports amended GO, reference NO-GO and KP4 triggered")
    # transfer
    p3 = r3["results"]["p3_transfer"]["metrics"]
    N.put("numFineRatio", f"{p3['ar']['fine_disp_mean'] / p3['ar']['inband_disp_mean']:.1f}")
    N.put("numFineKill", f"{t['kills']['KP4_transfer_ratio']:g}")
    N.put("numFineWin", f"{t['gate']['transfer_win']:g}")
    for key, A in (("ar", "Free"), ("labels@max", "Lab"), ("mgn@max", "Mgn")):
        blk = p3["ar"]["fine"] if key == "ar" else p3["zero_shot_reported"][key]["fine"]
        for m in ("disp_rel_l2", "energy_gap_rel", "vm_rel_l2"):
            N.put(f"numFine{A}{mtag[m]}", num(blk[m]["mean"]))
    N.put("numFineKnnDisp", num(p3["naive_at_fine"]["knn_field"]))
    for bb, B in (("16", "Sixteen"), ("64", "SixtyFour")):
        fs = p3["fewshot"][bb]
        for m in ("disp_rel_l2", "energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err"):
            N.put(f"numFew{B}{mtag[m]}", num(fs["finetune"][m]["mean"]))
        N.put(f"numFew{B}ScratchDisp", num(fs["scratch"]["disp_rel_l2"]["mean"]))
    few = p3["fewshot"]["64"]["finetune"]
    inb = p3["ar"]["inband"]
    fac = [few[m]["mean"] / inb[m]["mean"] for m in ("energy_gap_rel", "vm_rel_l2",
                                                     "peak_vm_rel_err")]
    N.put("numFewFactorMin", f"{min(fac):.1f}")
    N.put("numFewFactorMax", f"{max(fac):.1f}")
    # post hoc amplitude (transformer)
    A = amps["transformer"]["seeds"]
    fine = [A[s]["fine"]["summary"] for s in sorted(A)]
    inb_ = [A[s]["inband"]["summary"] for s in sorted(A)]

    def mean(rows, k):
        return statistics.fmean(x[k] for x in rows)

    N.put("numAmpFineDisp", num(mean(fine, "disp")))
    N.put("numAmpFineDispC", num(mean(fine, "disp_c")))
    red = [x["disp_reduction"] for x in fine]
    N.put("numAmpFineRedMin", pct(min(red), 0))
    N.put("numAmpFineRedMax", pct(max(red), 0))
    N.put("numAmpFineGapMedian", num(mean(fine, "egap_median")))
    N.put("numAmpFineGapMedianC", num(mean(fine, "egap_c_median")))
    N.put("numAmpFineCstar", f"{mean(fine, 'c_star_median'):.2f}")
    N.put("numAmpInCstar", f"{mean(inb_, 'c_star_median'):.2f}")
    N.put("numAmpInDisp", num(mean(inb_, "disp")))
    N.put("numAmpInDispC", num(mean(inb_, "disp_c")))
    N.put("numAmpInGap", num(mean(inb_, "egap")))
    N.put("numAmpInGapC", num(mean(inb_, "egap_c")))
    N.put("numAmpRatioBoth", f"{mean(fine, 'disp_c') / mean(inb_, 'disp_c'):.1f}")
    N.put("numAmpRatioFineOnly", f"{mean(fine, 'disp_c') / mean(inb_, 'disp'):.1f}")
    # the amplitude identity on every post-hoc row: egap_c = mean over loads of 1 - cos_K^2
    rows = 0
    dev = 0.0
    for d in amps.values():
        for s in d["seeds"].values():
            for st in ("inband", "fine"):
                for row in s[st]["per_instance"]:
                    cs = np.asarray(row["cos_K"], float)
                    dev = max(dev, abs(row["egap_c"] - float(np.mean(1 - cs * cs))))
                    rows += 1
    N.put("numAmpRows", f"{rows:,}")
    N.put("numAmpIdentity", _sci(dev, 1))
    return N


def _better(metric: str, a, b):
    """Elementwise: a is better than b in `metric` (recall: higher is better)."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return a > b if metric == "crit_recall" else a < b


def _guard_reading(c: dict, metric: str) -> str:
    """One of PREREG_CM2D Sec. 5's comparisons (new arm against the reference):
    'better' or 'worse' beyond the guard, or 'within' it."""
    if c["lower"]:
        return "worse" if metric == "crit_recall" else "better"
    if c["worse"]:
        return "better" if metric == "crit_recall" else "worse"
    return "within"


def cm2d_numbers(N: Numbers, rc: dict, v: dict, r2: dict) -> None:
    """The two-dimensional comparison with the current code (PREREG_CM2D; run of
    9 October 2026), its pre-registered verdicts and the statements of Section 5
    about them, each checked against the report and the stamped adjudicator's
    verdict file."""
    # the verdict file was computed from this report
    for h, (new, base, m) in {"H1": ("ar", "labels", "energy_gap_rel"),
                              "H2a": ("labels_knorm", "labels", "energy_gap_rel"),
                              "H2b": ("labels_knorm", "labels", "vm_rel_l2"),
                              "H3": ("labels_knorm", "ar", "energy_gap_rel")}.items():
        if not (np.allclose(v[h]["new_per_seed"], seed_values(rc, new, "1024", m), rtol=0,
                            atol=0)
                and np.allclose(v[h]["base_per_seed"], seed_values(rc, base, "1024", m),
                                rtol=0, atol=0)):
            raise SystemExit(f"CM2D {h}: the verdict's seed values are not the report's")
        if not v[h]["robustness"]["medians_show_the_direction"]:
            raise SystemExit(f"CM2D {h}: the medians do not show the verdict's direction")
    for h, H in (("H1", "One"), ("H2a", "TwoA"), ("H2b", "TwoB"), ("H3", "Three")):
        N.put(f"numH{H}Rel", pct(abs(v[h]["rel_change"])))
        N.put(f"numH{H}Tau", pct(v[h]["threshold"]))
    if not (v["H3"]["rel_change"] < 0 < v["H3"]["roles_exchanged"]["rel_change"]
            and abs(v["H3"]["roles_exchanged"]["rel_change"])
            < v["H3"]["roles_exchanged"]["threshold"]):
        raise SystemExit("CM2D H3: the reading with the roles exchanged is not within its guard")
    N.put("numHThreeExRel", pct(v["H3"]["roles_exchanged"]["rel_change"]))
    N.put("numHThreeExTau", pct(v["H3"]["roles_exchanged"]["threshold"]))
    # H3 resampled over the instances (seeds kept): the interval excludes zero although
    # the seed-level guard does not separate the two networks
    ir = v["H3"]["robustness"]["instance_resampling_95"]
    if not (ir["high"] < 0 and v["H3"]["robustness"]["welch_95"]["low"] < 0
            < v["H3"]["robustness"]["welch_95"]["high"]):
        raise SystemExit("CM2D H3: the text says the instance-resampling interval excludes zero "
                         "and Welch's interval does not")
    N.put("numHThreeResLow", pct(abs(ir["high"])))
    N.put("numHThreeResHigh", pct(abs(ir["low"])))
    # beside H1 to H2b: Welch's interval and the instance-resampling interval below zero
    for h in ("H1", "H2a", "H2b"):
        rb = v[h]["robustness"]
        if not (rb["welch_95"]["high"] < 0 and rb["instance_resampling_95"]["high"] < 0):
            raise SystemExit(f"CM2D {h}: an interval beside the verdict reaches zero")
    # H2a's ratio of the seed means (against the geometric mean of Section 5.3)
    lab_kn = (seed_mean(rc, "labels", "energy_gap_rel")
              / seed_mean(rc, "labels_knorm", "energy_gap_rel"))
    if not np.isclose(lab_kn, 1 / (1 + v["H2a"]["rel_change"]), rtol=1e-12, atol=0):
        raise SystemExit("CM2D H2a: the ratio of the seed means is not the verdict's")
    N.put("numCmLabOverKnormGap", f"{lab_kn:.2f}")
    # H2a's reduction of the seed-mean relative energy gap, stated for the
    # root-mean-square relative stiffness-norm error (as numThreeAncOverFreeGapRoot)
    N.put("numHTwoARootRel", pct(1 - np.sqrt(1 + v["H2a"]["rel_change"])))
    # the secondary readings of PREREG_CM2D Sec. 5 (exploratory, no verdicts)
    N.put("numCmSecondary", str(sum(len(c) for m in v["secondary"]["comparisons"].values()
                                    for c in m.values())))
    # per seed: the energy-norm-supervised transformer at or below the label-free one on
    # every metric, by little in two seeds and much in one
    for m in METRICS:
        if not _better(m, seed_values(rc, "labels_knorm", "1024", m),
                       seed_values(rc, "ar", "1024", m)).all():
            raise SystemExit(f"CM2D: L_K not better than label-free in every seed in {m}")
    kg = seed_values(rc, "labels_knorm", "1024", "energy_gap_rel")
    fg = seed_values(rc, "ar", "1024", "energy_gap_rel")
    dg = [a / b - 1 for a, b in zip(kg, fg, strict=True)]
    N.put("numHThreeSeedRel", and_list(pct(abs(x), 0) for x in dg))
    # seed 1 makes most of the difference: seeds 0 and 2 alone
    if int(np.argmin(dg)) != 1:
        raise SystemExit("CM2D H3: the text says seed 1 makes most of the difference")
    z2 = statistics.fmean(kg[::2]) / statistics.fmean(fg[::2]) - 1
    if not (z2 < 0 and abs(z2) < abs(v["H3"]["rel_change"]) / 4):
        raise SystemExit("CM2D H3: seeds 0 and 2 alone do not give a small difference")
    N.put("numHThreeSeedsZeroTwo", pct(abs(z2)))
    N.put("numCmKnormGapSeeds", and_list(num(x) for x in
                                          seed_values(rc, "labels_knorm", "1024",
                                                      "energy_gap_rel")))
    N.put("numCmFreeGapSeeds", and_list(num(x) for x in
                                         seed_values(rc, "ar", "1024", "energy_gap_rel")))
    # Section 5.1: label-free against the displacement-supervised transformer, every seed
    for m in METRICS:
        better = _better(m, seed_values(rc, "ar", "1024", m),
                         seed_values(rc, "labels", "1024", m))
        if m == "disp_rel_l2":
            if better.any():
                raise SystemExit("CM2D: the text says the label-free displacement error is "
                                 "above the supervised one in every seed")
        elif not better.all():
            raise SystemExit(f"CM2D: label-free not better than supervised in every seed in {m}")
    d_ar, d_lab = seed_mean(rc, "ar", "disp_rel_l2"), seed_mean(rc, "labels", "disp_rel_l2")
    N.put("numCmFreeDispExcessAbs", pct(d_ar / d_lab - 1))
    ex = [a / b - 1 for a, b in zip(seed_values(rc, "ar", "1024", "disp_rel_l2"),
                                    seed_values(rc, "labels", "1024", "disp_rel_l2"),
                                    strict=True)]
    N.put("numCmFreeDispExcessMin", pct(min(ex), 0))
    N.put("numCmFreeDispExcessMax", pct(max(ex), 0))
    for a, b, key in (("labels", "ar", "LabOverFreeGap"), ("mgn", "labels", "MgnOverLabGap")):
        N.put(f"numCm{key}", times(seed_mean(rc, a, "energy_gap_rel")
                                   / seed_mean(rc, b, "energy_gap_rel")))
    # as numThreeAncOverFreeGapRoot: the ratio of the root-mean-square relative
    # stiffness-norm errors
    N.put("numCmLabOverFreeGapRoot", times(np.sqrt(seed_mean(rc, "labels", "energy_gap_rel")
                                                   / seed_mean(rc, "ar", "energy_gap_rel"))))
    for a, key in (("labels", "LabOverFreeVm"), ("mgn", "MgnOverFreeVm")):
        N.put(f"numCm{key}", times(seed_mean(rc, a, "vm_rel_l2")
                                   / seed_mean(rc, "ar", "vm_rel_l2")))
    # instance-seed pairs (the first network better than the second)
    for a, b, key in (("ar", "labels", "Lab"), ("labels_knorm", "labels", "KnormLab"),
                      ("labels_knorm", "ar", "KnormFree"), ("mgn", "labels", "MgnLab")):
        for m in METRICS:
            N.put(f"numPairCm{key}{MTAG[m]}", share(_better(m, per_instance(rc, a, m),
                                                            per_instance(rc, b, m))))
    # "the lower relative energy gap and the lower von Mises error on X of the pairs":
    # the same pairs, so one share stands for both and for their conjunction
    for a, key in (("ar", "Lab"), ("labels_knorm", "KnormLab")):
        gap = _better("energy_gap_rel", per_instance(rc, a, "energy_gap_rel"),
                      per_instance(rc, "labels", "energy_gap_rel"))
        vm = _better("vm_rel_l2", per_instance(rc, a, "vm_rel_l2"),
                     per_instance(rc, "labels", "vm_rel_l2"))
        if not share(gap) == share(vm) == share(gap & vm):
            raise SystemExit(f"CM2D: {key}: the energy-gap and von Mises shares differ")
    # the two errors rank the label-free and the displacement-supervised transformer in opposite
    # orders, in either direction
    vm_f, vm_l = per_instance(rc, "ar", "vm_rel_l2"), per_instance(rc, "labels", "vm_rel_l2")
    d_f, d_l = per_instance(rc, "ar", "disp_rel_l2"), per_instance(rc, "labels", "disp_rel_l2")
    opp = (((vm_f < vm_l) & (d_l < d_f)) | ((vm_l < vm_f) & (d_f < d_l)))
    N.put("numPairCmOpposite", pct(float(opp.mean())))
    if not opp.mean() > 0.5:
        raise SystemExit("CM2D: the opposite rankings are not on most pairs")
    # the graph network: the lowest displacement error of the table, the largest
    # relative energy gap and von Mises error of the trained networks
    trained = ("ar", "labels", "labels_knorm", "mgn")
    if min(trained, key=lambda a: seed_mean(rc, a, "disp_rel_l2")) != "mgn":
        raise SystemExit("CM2D: the graph network does not have the lowest displacement error")
    # ... by little: below the displacement-supervised transformer's within the noise guard
    c = v["secondary"]["comparisons"]["disp_rel_l2"]["1024"]["mgn_vs_labels"]
    if _guard_reading(c, "disp_rel_l2") != "within" or not c["rel_change"] < 0:
        raise SystemExit("CM2D: the graph network's displacement error is not below the "
                         "supervised transformer's within the guard")
    N.put("numCmMgnBelowLabDisp", pct(abs(c["rel_change"]), 0))
    # the label-free transformer's relative energy gap below the graph network's at
    # every budget at which the graph network was trained
    if not all(seed_mean(rc, "mgn", "energy_gap_rel", bb) > seed_mean(rc, "ar", "energy_gap_rel")
               for bb in cells(rc)["mgn"]):
        raise SystemExit("CM2D: the graph network's relative energy gap is not above the "
                         "label-free one at every budget")
    for m in ("energy_gap_rel", "vm_rel_l2"):
        if max(trained, key=lambda a: seed_mean(rc, a, m)) != "mgn":
            raise SystemExit(f"CM2D: the graph network is not the least accurate in {m}")
    if any(worse_than_zero(rc, a)[0] for a in ("ar", "labels", "labels_knorm")):
        raise SystemExit("CM2D: a transformer has an instance worse than the zero field at 1,024")
    N.put("numCmMgnWorseSixtyFour", f"{worse_than_zero(rc, 'mgn', '64')[0]:,}")
    # budgets: worse than the zero field, and the energy-norm-supervised transformer
    # against the label-free one under the guard (PREREG_CM2D Sec. 5)
    for arm, A in (("labels", "Lab"), ("labels_knorm", "Knorm")):
        for bb, B in (("16", "Sixteen"), ("64", "SixtyFour"), ("256", "TwoFiveSix")):
            N.put(f"numCm{A}Worse{B}", f"{worse_than_zero(rc, arm, bb)[0]:,}")
    comp = v["secondary"]["comparisons"]

    def readings(name: str, bb: str) -> list:
        return [_guard_reading(comp[m][bb][name], m) for m in METRICS]

    # 16 labels: worse beyond the guard on every metric; 64: on every metric but the
    # critical-region recall, which is within; 256 and 1,024: within on every metric
    want = {"16": ["worse"] * 5, "64": ["worse"] * 4 + ["within"], "256": ["within"] * 5,
            "1024": ["within"] * 5}
    for bb, w in want.items():
        got = readings("labels_knorm_vs_label_free", bb)
        if got != w:
            raise SystemExit(f"CM2D: L_K against label-free at {bb} labels reads {got}")
    # with 256 labels the seed means are within the guard, the pairs still mostly the
    # label-free transformer's
    w256 = _better("energy_gap_rel", per_instance(rc, "ar", "energy_gap_rel"),
                   per_instance(rc, "labels_knorm", "energy_gap_rel", "256"))
    if not w256.mean() > 0.5:
        raise SystemExit("CM2D: with 256 labels the label-free transformer does not have the "
                         "lower relative energy gap on most pairs")
    N.put("numPairCmFreeKnormGapTwoFiveSix", share(w256))
    for bb in BUDGETS:
        got = readings("labels_vs_label_free", bb)
        if any(got[METRICS.index(m)] != "worse" for m in METRICS if m != "disp_rel_l2"):
            raise SystemExit(f"CM2D: L_D not worse than label-free beyond the guard at {bb}: "
                             f"{got}")
    le = v["secondary"]["label_efficiency"]
    if (le["labels"]["first_budget_below_label_free"] != {"energy_gap_rel": None,
                                                          "disp_rel_l2": 1024}):
        raise SystemExit("CM2D: L_D's first budget below the label-free row is not as stated")
    passes = [bb for bb in cells(rc)["mgn"] if seed_mean(rc, "mgn", "disp_rel_l2", bb)
              < seed_mean(rc, "ar", "disp_rel_l2")]
    if passes != ["1024"]:
        raise SystemExit(f"CM2D: the graph network passes the label-free one at {passes}")
    if (le["labels_knorm"]["first_budget_below_label_free"]
            != {"energy_gap_rel": 1024, "disp_rel_l2": 1024}):
        raise SystemExit("CM2D: L_K's first budget below the label-free row is not 1,024")
    adv = le["labels"]["label_free_advantage_in_energy_gap"]
    N.put("numCmAdvMax", pct(max(adv.values())))
    N.put("numCmAdvMin", pct(min(adv.values())))
    if not (max(adv, key=adv.get) == "16" and min(adv, key=adv.get) == "1024"):
        raise SystemExit("CM2D: the label-free advantage is not largest at 16 and smallest at "
                         "1,024")
    # the two runs' supervised transformers (other code; descriptive)
    jl = v["secondary"]["july_labels_only"]
    for bb in BUDGETS:
        if not (np.isclose(jl[bb]["energy_gap_rel"]["july"], seed_mean(r2, "labels",
                                                                     "energy_gap_rel", bb))
                and np.isclose(jl[bb]["energy_gap_rel"]["now"],
                               seed_mean(rc, "labels", "energy_gap_rel", bb))):
            raise SystemExit("CM2D: July's labels-only row is not the July report's")
    N.put("numTwoLabGapSixteen", num(seed_mean(r2, "labels", "energy_gap_rel", "16")))
    N.put("numCmLabGapSixteen", num(seed_mean(rc, "labels", "energy_gap_rel", "16")))
    if not (seed_mean(rc, "labels", "energy_gap_rel", "16")
            > seed_mean(r2, "labels", "energy_gap_rel", "16")):
        raise SystemExit("CM2D: the text says the later code's 16-label supervised gap is higher")
    # the displacement errors of the same networks with the two codes, at 1,024 labels
    drop = [seed_mean(r2, a, "disp_rel_l2") / seed_mean(rc, a, "disp_rel_l2")
            for a in ("ar", "labels", "mgn")]
    N.put("numJulyOverCmDispMin", f"{min(drop):.1f}")
    N.put("numJulyOverCmDispMax", f"{max(drop):.1f}")
    trained_cm = [seed_mean(rc, a, "disp_rel_l2") for a in ("ar", "labels", "labels_knorm",
                                                             "mgn")]
    N.put("numCmDispSpread", f"{max(trained_cm) / min(trained_cm):.2f}")
    trained_july = [seed_mean(r2, a, "disp_rel_l2") for a in TRAINED if a in cells(r2)]
    N.put("numTwoDispSpread", f"{max(trained_july) / min(trained_july):.2f}")
    # the nearest-neighbour field is the same in both 2D runs (same corpus and labels)
    for bb in BUDGETS:
        for m in METRICS:
            if not np.isclose(seed_mean(rc, "knn_field", m, bb), seed_mean(r2, "knn_field", m, bb),
                              rtol=1e-6, atol=0):
                raise SystemExit("CM2D: the nearest-neighbour field differs between the 2D runs")
    # solves: the labels of the 256 validation and 1,024 pool instances
    de = rc["data_economy"]
    if not (de["labelled_val"] == 256 and de["labelled_pool_prefix"] == 1024
            and de["ledger"]["total"] == 0):
        raise SystemExit("CM2D: the labelled instances are not the 256 + 1,024 of the text")
    k = de["solves_per_labelled_instance"]
    N.put("numCmSolves", f"{de['labelled_instances'] * k:,}")
    N.put("numCmSolvesVal", f"{de['labelled_val'] * k:,}")
    N.put("numCmSolvesTrain", f"{de['labelled_pool_prefix'] * k:,}")


# ---------------------------------------------------------------- spectra (post hoc)
SPEC_EDGES = -2.0 + 0.125 * np.arange(69)          # scripts/cm2d_spectra.py's LOG_EDGES


def _tail_index(k: float) -> int:
    """The first log bin of the modes with lambda_m >= 10^k R(U*) (k an edge)."""
    j = int(np.searchsorted(SPEC_EDGES, k))
    if not np.isclose(SPEC_EDGES[j], k):
        raise ValueError(k)
    return j + 1


def _tails(S: np.ndarray) -> np.ndarray:
    """(..., bins) share of a binned spectrum in its bins b and above."""
    t = np.cumsum(S[..., ::-1], axis=-1)[..., ::-1]
    with np.errstate(invalid="ignore", divide="ignore"):
        return t / S.sum(axis=-1, keepdims=True)


def spectral_arrays(z: dict) -> dict:
    """Per row, seed, instance and load case: the normalised Rayleigh quotient
    rho = R(e) / R(U*), the squared relative displacement error delta^2 and the
    relative energy gap g (= rho delta^2), from the export's norms."""
    rq_star = z["uK_star"] / z["u2_star"]
    with np.errstate(invalid="ignore", divide="ignore"):
        rho = (z["eK"] / z["e2"]) / rq_star[None, None]
    d2 = z["e2"] / z["u2_star"][None, None]
    g = z["rel"]
    if not np.allclose(rho * d2, g, rtol=1e-8, atol=0):
        raise SystemExit("spectra: g = rho delta^2 does not hold on the exported arrays")
    return {"rows": [str(r) for r in z["rows"]], "rho": rho, "d2": d2, "g": g}


def _gm(x) -> float:
    return float(np.exp(np.mean(np.log(np.asarray(x, dtype=float)))))


def spectra_numbers(N: Numbers, sj: dict, z: dict, rc: dict) -> None:
    """The error spectra of CM2D's networks at 1,024 labels (post hoc; RUNBOOK_CMAME
    Sec. D): every reading the text quotes is recomputed here from the per-load
    arrays and checked against the export's summary."""
    if not np.array_equal(z["log_edges"], SPEC_EDGES):
        raise SystemExit("spectra: the export's log bins are not those this script reads")
    A = spectral_arrays(z)
    rows, rho, d2, g = A["rows"], A["rho"], A["d2"], A["g"]
    if rows != ["ar", "labels", "labels_knorm", "mgn"] or rho.shape[1:] != (3, 256, 4):
        raise SystemExit("spectra: the export's rows or shape are not CM2D's")
    dg = sj["diagnostics"]
    ix = {r: i for i, r in enumerate(rows)}
    rq_star = z["uK_star"] / z["u2_star"]
    rho_i = (z["eK_ieee"] / z["e2_ieee"]) / rq_star[None, None]       # TF32 off
    g_i = z["eK_ieee"] / z["uK_star"][None, None]
    j4 = _tail_index(4)

    def same(a, b, what):
        if not np.isclose(a, b, rtol=1e-9, atol=0):
            raise SystemExit(f"spectra: {what}: {a} recomputed, {b} in the export's summary")

    stiff_n = set()
    for r in rows:
        i = ix[r]
        med = float(np.median(rho[i]))
        same(med, dg["rows"][r]["rayleigh_ratio_median"], f"{r} median quotient")
        N.put(f"numSpecRq{TAG[r]}", num(med))
        for k, key, tag in ((2, "SK_log", "K"), (1, "S2_log", "Euc")):
            sh = float(np.median(_tails(z[key][i])[..., _tail_index(k)]))
            same(sh, dg["rows"][r][f"share_{'eK' if key == 'SK_log' else 'e2'}_above_median"]
                 [f"1e{k}"], f"{r} {key} share above 10^{k}")
            N.put(f"numSpecShare{tag}{TAG[r]}", pct(sh, 0) if sh >= 0.095 else pct(sh, 1))
        ie = float(np.median(rho_i[i]))
        same(ie, dg["rows"][r]["ieee"]["rayleigh_ratio_median"], f"{r} quotient, TF32 off")
        N.put(f"numSpecIeeeRq{TAG[r]}", num(ie))
        tf = dg["rows"][r]["tf32"]
        x = float(np.median(z["dK_tf32"][i] / z["eK"][i]))
        same(x, tf["dK_over_eK_median"], f"{r} rounding against the error")
        N.put(f"numSpecTf{TAG[r]}", pct(x, 1) if x >= 0.001 else pct(x, 2))
        # the rounding in the modes at or above 10^4 R(U*), on the triples that reach them
        num4, den4 = (z[k][i][..., j4:].sum(-1) for k in ("SK_log_tf32", "SK_log"))
        ok = den4 > 0
        if int(ok.sum()) != tf["dK_over_eK_above_n"]["1e4"]:
            raise SystemExit(f"spectra: {r}: the triples reaching 10^4 R(U*)")
        stiff_n.add(int(ok.sum()))
        x4 = float(np.median(num4[ok] / den4[ok]))
        same(x4, tf["dK_over_eK_above_median"]["1e4"], f"{r} rounding at or above 10^4")
        if r in ("ar", "labels_knorm"):
            N.put(f"numSpecTfStiff{TAG[r]}", pct(x4, 0))
        # the area- and element-weighted von Mises errors (Section 3.3)
        for key, M in (("vm_area", "VmArea"), ("vm_elem", "VmElem")):
            v = float(np.median(z[key][i]))
            same(v, dg["rows"][r][f"{key}_median"], f"{r} median {key}")
            N.put(f"numSpec{M}{TAG[r]}", num(v))
    # the triples whose spectra reach 10^4 R(U*): the same load cases in every row and
    # seed, since the spectrum of K and R(U*) do not depend on the network
    reach = z["SK_log_star"][..., j4:].sum(-1) > 0
    if stiff_n != {int(reach.sum()) * rho.shape[1]}:
        raise SystemExit("spectra: the load cases reaching 10^4 R(U*) differ between rows or "
                         "seeds")
    N.put("numSpecTfStiffN", f"{stiff_n.pop():,}")
    N.put("numSpecTfStiffLoads", f"{int(reach.sum()):,}")
    N.put("numSpecLoadCases", f"{reach.size:,}")
    N.put("numSpecLoads", f"{rho[0].size:,}")
    # H2b's element-wise ratio is the report's; weighted by element area instead
    la, kn = ix["labels"], ix["labels_knorm"]
    elem = float(z["vm_elem"][la].mean() / z["vm_elem"][kn].mean())
    if not np.isclose(elem, seed_mean(rc, "labels", "vm_rel_l2")
                      / seed_mean(rc, "labels_knorm", "vm_rel_l2"), rtol=1e-9, atol=0):
        raise SystemExit("spectra: the exported von Mises errors are not the report's")
    N.put("numSpecVmElemRatio", f"{elem:.2f}")
    N.put("numSpecVmAreaRatio", f"{float(z['vm_area'][la].mean() / z['vm_area'][kn].mean()):.2f}")
    ref = dg["reference"]
    x = float(np.median(rq_star / z["lam_min"][:, None]))
    same(x, ref["rayleigh_over_lam_min_median"], "the solution's quotient over the smallest "
         "eigenvalue")
    same(float(np.median(z["rq_star_over_lam_min"])), x, "the exported quotient over the "
         "smallest eigenvalue")
    N.put("numSpecRqStarOverMin", f"{x:.2f}")
    for k, key, tag, src in ((2, "SK_log_star", "K", "share_uK_above_median"),
                             (1, "S2_log_star", "Euc", "share_u2_above_median")):
        sh = float(np.median(_tails(z[key])[..., _tail_index(k)]))
        same(sh, ref[src][f"1e{k}"], f"solution {key} share")
        N.put(f"numSpecShare{tag}Star", pct(sh, 1))
    # pairs: geometric-mean ratios over the triples (same seed, instance and load case),
    # overall, per seed and with TF32 off
    for a, b, key in (("labels", "labels_knorm", "LabKnorm"), ("labels_knorm", "ar", "KnormFree"),
                      ("mgn", "labels", "MgnLab")):
        pr = dg["pairs"][f"{a}_vs_{b}"]
        ia, ib = ix[a], ix[b]
        q, dd, gg = (_gm(x[ia] / x[ib]) for x in (rho, d2, g))
        same(q, pr["geomean_ratio_rayleigh"], f"{key} quotient ratio")
        same(dd, pr["geomean_ratio_disp_sq"], f"{key} delta^2 ratio")
        same(gg, pr["geomean_ratio_gap"], f"{key} gap ratio")
        above = float(np.mean(rho[ia] > rho[ib]))
        same(above, pr["share_first_above"], f"{key} share above")
        N.put(f"numSpec{key}Rq", f"{q:.2f}")
        N.put(f"numSpec{key}Disp", f"{dd:.2f}")
        N.put(f"numSpec{key}Gap", f"{gg:.2f}")
        N.put(f"numSpec{key}Above", pct(above))
        same(_gm(rho_i[ia] / rho_i[ib]), pr["ieee"]["geomean_ratio_rayleigh"],
             f"{key} quotient ratio, TF32 off")
        same(_gm(g_i[ia] / g_i[ib]), pr["ieee"]["geomean_ratio_gap"],
             f"{key} gap ratio, TF32 off")
        for s, x in enumerate(pr.get("by_seed", ())):
            same(_gm(rho[ia][s] / rho[ib][s]), x["geomean_ratio_rayleigh"], f"{key} s{s} rho")
            same(_gm(d2[ia][s] / d2[ib][s]), x["geomean_ratio_disp_sq"], f"{key} s{s} delta^2")
            same(_gm(g[ia][s] / g[ib][s]), x["geomean_ratio_gap"], f"{key} s{s} gap")
    ia, ib = ix["labels"], ix["labels_knorm"]
    seeds = range(rho.shape[1])
    q = [_gm(rho[ia][s] / rho[ib][s]) for s in seeds]
    dd = [_gm(d2[ia][s] / d2[ib][s]) for s in seeds]
    gg = [_gm(g[ia][s] / g[ib][s]) for s in seeds]
    pr = dg["pairs"]["labels_vs_labels_knorm"]
    # each network's quotient averaged geometrically over its seeds first (no pairing of
    # the seeds of the two networks), then compared per instance and load case
    sa, sb = (np.exp(np.log(rho[i]).mean(axis=0)) for i in (ia, ib))
    x = float(np.mean(sa > sb))
    same(x, pr["share_first_above_seed_geomean"], "seed geometric means")
    N.put("numSpecLabKnormAboveSeedGm", pct(x))
    N.put("numSpecLabKnormRqSeeds", and_list(f"{t:.2f}" for t in q))
    N.put("numSpecLabKnormDispSeeds", and_list(f"{t:.2f}" for t in dd))
    x = float(np.mean(d2[ia] < d2[ib]))
    same(x, pr["share_first_disp_lower"], "L_D's delta the smaller")
    N.put("numSpecLabKnormDispLower", pct(x))
    # the spectral share of the log of the gap ratio; above one exactly in the seed in
    # which L_D's errors were the smaller (by eq:factor, given a gap ratio above one)
    shares = [np.log(a) / np.log(c) for a, c in zip(q, gg, strict=True)]
    if not (all(c > 1 for c in gg) and sum(t < 1 for t in dd) == 1):
        raise SystemExit("spectra: the text names one seed in which L_D's errors were smaller")
    N.put("numSpecSpectralShare", pct(np.log(_gm(rho[ia] / rho[ib]))
                                      / np.log(_gm(g[ia] / g[ib])), 0))
    N.put("numSpecSpectralShareMin", pct(min(shares), 0))
    N.put("numSpecSpectralShareMax", pct(max(shares), 0))
    qi, gi = _gm(rho_i[ia] / rho_i[ib]), _gm(g_i[ia] / g_i[ib])
    N.put("numSpecIeeeLabKnormRq", f"{qi:.2f}")
    N.put("numSpecIeeeLabKnormGap", f"{gi:.1f}")
    if not (qi > _gm(rho[ia] / rho[ib]) and gi > _gm(g[ia] / g[ib])):
        raise SystemExit("spectra: the text says the readings as run understate the difference")
    # ... between the networks trained in the two norms only: with TF32 off the quotient
    # ratios of the networks trained in the same norm come no further apart
    for a, b in (("labels_knorm", "ar"), ("mgn", "labels")):
        if not (abs(np.log(_gm(rho_i[ix[a]] / rho_i[ix[b]])))
                <= abs(np.log(_gm(rho[ix[a]] / rho[ix[b]]))) + np.log(1.01)):
            raise SystemExit(f"spectra: TF32 off moves {a} and {b} apart")
    # the energy-norm-supervised transformer's errors the smaller in every seed, by far in seed 1
    kd = [_gm(d2[ix["labels_knorm"]][s] / d2[ix["ar"]][s]) for s in seeds]
    if not (max(kd) < 1 and int(np.argmin(kd)) == 1):
        raise SystemExit("spectra: the energy-norm-supervised transformer's errors are not the smaller "
                         "in every seed, by far in seed 1")
    N.put("numSpecKnormFreeDispSeeds", and_list(f"{t:.2f}" for t in kd))
    # per load case: worse than the zero field exactly when Pi_h(u) > 0 (Corollary
    # "Zero-field test and ranking", the energies against the error norms); the
    # rescaling by c* never increases the gap and leaves no prediction worse than the
    # zero field (Proposition "Energy-optimal amplitude")
    for r in rows:
        c, i = sj["counts"][r], ix[r]
        k = int(np.sum(z["pi"][i] > 0))
        if not (np.array_equal(z["pi"][i] > 0, z["eK"][i] > z["uK_star"][None])
                and k == c["load_cases_pi_positive"]
                and not c["load_cases_rel_gap_above_1_after_cstar"]
                and np.all(z["rel_c"][i] <= z["rel"][i] * (1 + 1e-9))
                and np.all(z["rel_c"][i] <= 1)):
            raise SystemExit(f"spectra: {r}'s load cases worse than the zero field")
        N.put(f"numSpecLoadWorse{TAG[r]}", f"{k:,}")
    if N["numSpecLoadWorseFree"] != N["numSpecLoadWorseLab"]:
        raise SystemExit("spectra: the text gives one count for the label-free and the "
                         "supervised transformer")
    # the bound of Proposition "Energy gap and stress error" (plane stress)
    gam = z["gamma_star"][None, None]
    ratio = z["vm_area"] ** 2 / ((1 + gam) * g)
    worst = float(np.max(ratio))
    same(worst, max(dg["rows"][r]["prop1_bound_ratio_max"] for r in rows), "bound ratio")
    if not worst <= 1:
        raise SystemExit("spectra: the stress bound fails on a load case")
    N.put("numSpecBoundMax", f"{worst:.2f}")
    N.put("numSpecFigIndex", str(sj["selections"]["fig2d"]["index"]))
    nf = [int(z["n_free"].min()), int(z["n_free"].max())]
    if nf != [sj["eigen"]["n_free_min_median_max"][0], sj["eigen"]["n_free_min_median_max"][2]]:
        raise SystemExit("spectra: the free degrees of freedom")
    N.put("numSpecFreeMin", f"{nf[0]:,}")
    N.put("numSpecFreeMax", f"{nf[1]:,}")


# ---------------------------------------------------------------- 3D field export (post hoc)
def field_numbers(N: Numbers, fj: dict, ez: dict) -> None:
    """Readings of the three-dimensional field export (RUNBOOK_CMAME Sec. A; Phase-2b's
    networks at 1,024 labels): per load case, the errors' normalised Rayleigh
    quotients, the predictions worse than the zero field before and after the
    rescaling by c*, the two von Mises errors and the stress bound; recomputed here
    from the per-load arrays and checked against the export's summary."""
    arms = [str(a) for a in ez["arms"]]
    if arms != ["ar", "labels", "mgn"] or ez["pi"].shape[1:] != (3, 256, 4):
        raise SystemExit("fields: the export's arms or shape are not Phase-2b's at 1,024 labels")
    with np.errstate(invalid="ignore", divide="ignore"):
        rho = (ez["eK"] / ez["e2"]) / (ez["uK_star"] / ez["u2_star"])[None, None]
        g = ez["eK"] / ez["uK_star"][None, None]
        bound = ez["vm_vol"] ** 2 / ((1 + ez["gamma_star"])[None, None] * g)
    if not np.allclose(g, ez["rel"], rtol=1e-6, atol=0):
        raise SystemExit("fields: the energies' relative gap is not the error's")
    dg, cnt = fj["diagnostics"], fj["counts"]
    for i, a in enumerate(arms):
        med = float(np.nanmedian(rho[i]))
        if not np.isclose(med, dg[a]["rayleigh_ratio_median"], rtol=1e-9, atol=0):
            raise SystemExit(f"fields: {a}'s median quotient")
        N.put(f"numFieldRq{TAG[a]}", num(med))
        for key in ("vm_vol", "vm_elem"):
            v = float(np.nanmedian(ez[key][i]))
            if not np.isclose(v, dg[a][f"{key}_median"], rtol=1e-9, atol=0):
                raise SystemExit(f"fields: {a}'s median {key}")
            N.put(f"numField{'VmVol' if key == 'vm_vol' else 'VmElem'}{TAG[a]}", num(v))
        k = int(np.sum(ez["pi"][i] > 0))
        if not (np.array_equal(ez["pi"][i] > 0, ez["eK"][i] > ez["uK_star"][None])
                and np.all(ez["rel_c"][i] <= ez["rel"][i] * (1 + 1e-9))
                and k == cnt[a]["load_cases_pi_positive"] == cnt[a]["load_cases_rel_gap_above_1"]
                and cnt[a]["load_cases_rel_gap_above_1_after_cstar"] == 0
                and cnt[a]["load_cases_cstar_increased_gap"] == 0
                and int(np.sum(ez["rel_c"][i] > 1)) == 0):
            raise SystemExit(f"fields: {a}'s load cases worse than the zero field")
        N.put(f"numFieldLoadWorse{TAG[a]}", f"{k:,}")
        if a != "ar":
            above = float(np.mean(rho[i] > rho[0]))
            if not np.isclose(above, dg[a]["rayleigh_above_label_free_share"], rtol=1e-12):
                raise SystemExit(f"fields: {a}'s share above the label-free quotient")
            N.put(f"numFieldRqAbove{TAG[a]}", pct(above))
    if N["numFieldLoadWorseFree"] != N["numThreeFreeLoadWorse"]:
        raise SystemExit("fields: the label-free load cases worse than the zero field disagree "
                         "with the post-hoc amplitude records")
    worst = float(np.nanmax(bound))
    if not (worst <= 1 and np.isclose(worst, max(dg[a]["prop1_bound_ratio_max"] for a in arms),
                                      rtol=1e-9)):
        raise SystemExit("fields: the stress bound")
    N.put("numFieldBoundMax", f"{worst:.2f}")
    N.put("numFieldLoads", f"{ez['pi'][0].size:,}")


def field_load(fig: str, z: dict) -> int:
    """The load case a field plot shows (FIELD_LOADS)."""
    row, qty, rule = FIELD_LOADS[fig]
    if qty == "rel":
        vals = z[f"rel_{row}"]
    else:
        vals = (np.linalg.norm(z[f"U_{row}"] - z["U_star"], axis=1)
                / np.linalg.norm(z["U_star"], axis=1))
    return pick_load(vals, rule)


def figure_numbers(N: Numbers, figs: dict) -> None:
    """The load case of each field plot, and the readings the text quotes for them."""
    for fig, key in (("fig5", "Worst"), ("fig6", "Median"), ("fig7", "Fine"),
                     ("fig2d", "TwoD")):
        z = figs[fig]
        j = field_load(fig, z)
        names = LOADS_2D if fig == "fig2d" else LOADS_3D
        N.put(f"numFig{key}Load", names[j])
    # the fine-mesh instance's load case: the text says the prediction is too small and
    # that the rescaling leaves the shape
    z = figs["fig7"]
    j = field_load("fig7", z)
    c = float(z["c_ar"][j])
    if not (c > 1 and _rel_disp(z, "U_ar", j, c) < 0.25 * _rel_disp(z, "U_ar", j)):
        raise SystemExit("fig7: the label-free prediction is not too small, or the rescaling "
                         "does not remove most of its error")
    # the worst instance's load case: the volume share on which a network's von Mises
    # stress exceeds twice the reference's; the label-free displacement has the
    # reference's shape and too large an amplitude (c* < 1, and the rescaling removes
    # most of its error)
    z = figs["fig5"]
    j = field_load("fig5", z)
    for r in ("ar", "labels", "mgn"):
        over = z[f"vm_{r}"][j].astype(float) > 2 * z["vm_ref"][j].astype(float)
        N.put(f"numFigWorstTwice{TAG[r]}", pct(float(z["vol"][over].sum() / z["vol"].sum()), 0))
    c = float(z["c_ar"][j])
    d, dc = _rel_disp(z, "U_ar", j), _rel_disp(z, "U_ar", j, c)
    if not (c < 1 and dc < 0.25 * d):
        raise SystemExit("fig5: the label-free prediction is not too large, or the rescaling "
                         "does not remove most of its error")
    N.put("numFigWorstFreeDisp", num(d, 2))
    N.put("numFigWorstFreeC", num(c, 2))
    N.put("numFigWorstFreeDispC", num(dc, 2))
    # the typical instance's load case: both supervised networks better than the zero field
    z = figs["fig6"]
    j = field_load("fig6", z)
    if not all(z[f"rel_{r}"][j] < 1 and z[f"pi_{r}"][j] < 0 for r in ("labels", "mgn")):
        raise SystemExit("fig6: a supervised prediction is worse than the zero field")
    z = figs["fig2d"]
    j = field_load("fig2d", z)
    us = z["U_star"][j]
    d = [float(np.linalg.norm(z[f"U_{r}"][j] - us) / np.linalg.norm(us))
         for r in ("ar", "labels", "labels_knorm", "mgn")]
    g = [float(z[f"rel_{r}"][j]) for r in ("ar", "labels", "labels_knorm", "mgn")]
    N.put("numFigTwoDDispMin", num(min(d), 2))
    N.put("numFigTwoDDispMax", num(max(d), 2))
    N.put("numFigTwoDGapMin", num(min(g), 2))
    N.put("numFigTwoDGapMax", num(max(g), 2))


def _hms(text: str) -> float:
    h, m, sec = (int(x) for x in text.split(":"))
    return h + m / 60 + sec / 3600


def timing_numbers(N: Numbers, e2: dict, used: dict) -> None:
    """Training times, read from the committed run logs and the deviation ledger."""
    led = (ROOT / "DEVIATIONS_PHASE2.md")
    txt = led.read_text(encoding="utf-8")
    used[_rel(led)] = hashlib.sha256(led.read_bytes()).hexdigest()
    m = re.search(r"AR 3 x ([0-9.]+) h", txt)
    if not m:
        raise SystemExit("DEVIATIONS_PHASE2.md: the Phase-2b AR training time is not on record")
    per_seed_3d = float(m.group(1))
    flat = " ".join(txt.split())
    d14 = re.search(r"scored disp_rel_l2 ([0-9.]+) and energy_gap_rel ([0-9.]+)", flat)
    alpha = re.search(r"alpha = ([0-9.e-]+) reproduces both", flat)
    pilot = re.search(r"20 AR epochs\): disp ([0-9.]+) < ([0-9.]+), passed", flat)
    audit = re.search(r"Independent audit [^:]*: ([0-9]+)/([0-9]+) after", flat)
    if not (d14 and alpha and pilot and audit):
        raise SystemExit("DEVIATIONS_PHASE2.md: a D14, pilot or audit figure is not on record")
    N.put("numDfourteenDisp", d14.group(1))
    N.put("numDfourteenGap", d14.group(2))
    a_m, a_e = alpha.group(1).split("e")
    N.put("numDfourteenAlpha", f"${a_m} \\times 10^{{{int(a_e)}}}$")
    N.put("numPilotDisp", f"{float(pilot.group(1)):.3f}")
    N.put("numPilotLimit", f"{float(pilot.group(2)):.2f}")
    N.put("numAuditItems", f"{audit.group(1)} of {audit.group(2)}")
    N.put("numTimeThreeSeed", f"{per_seed_3d:.1f}")
    per_seed_e2 = []
    for M in (512, 1024):
        log = REC8 / "e2" / f"e2_m{M}" / "run.log"
        t = log.read_text(encoding="utf-8")
        used[_rel(log)] = hashlib.sha256(log.read_bytes()).hexdigest()
        if "workers=1" not in t:
            raise SystemExit(f"{log}: the seeds did not run one after another")
        d = re.search(r"\[E8 \(AR pretrain\)\] done in ([0-9:]+)", t)
        per_seed_e2.append(_hms(d.group(1)) / 3)
    N.put("numTimeBottleneckSeedMin", f"{min(per_seed_e2):.1f}")
    N.put("numTimeBottleneckSeedMax", f"{max(per_seed_e2):.1f}")
    N.put("numTimeBottleneckSpeedup", f"{per_seed_3d / statistics.fmean(per_seed_e2):.0f}")
    log = REC8 / "e1" / "e1_2d_base" / "run.log"
    t = log.read_text(encoding="utf-8")
    used[_rel(log)] = hashlib.sha256(log.read_bytes()).hexdigest()
    if "workers=3" not in t:
        raise SystemExit(f"{log}: the three seeds did not run in parallel")
    d = re.search(r"\[E8 \(AR pretrain\)\] done in ([0-9:]+)", t)
    mins = round(_hms(d.group(1)) * 60)
    N.put("numTimeTwoParallel", f"{mins // 60} h {mins % 60} min")
    # the bottleneck against the transformer (E2 records)
    a = e2["archs"]
    t_in, t_fi = a["transformer"]["step_ms"]["inband_0"], a["transformer"]["step_ms"]["fine"]
    r_step = [t_in / a[k]["step_ms"]["inband_0"] for k in ("m512", "m1024")]
    r_gap = [statistics.fmean(a[k]["egap"]) / statistics.fmean(a["transformer"]["egap"])
             for k in ("m512", "m1024")]
    r_fine = [statistics.fmean(a[k]["fine_disp"]) / statistics.fmean(a["transformer"]["fine_disp"])
              for k in ("m512", "m1024")]
    N.put("numEtwoStepMin", f"{min(r_step):.0f}")
    N.put("numEtwoStepMax", f"{max(r_step):.0f}")
    N.put("numEtwoGapMin", f"{min(r_gap):.1f}")
    N.put("numEtwoGapMax", f"{max(r_gap):.1f}")
    N.put("numEtwoFineMin", f"{min(r_fine):.1f}")
    N.put("numEtwoFineMax", f"{max(r_fine):.1f}")
    N.put("numEtwoNodesIn", f"{e2['nodes']['inband_0']:,}")
    N.put("numEtwoNodesFine", f"{e2['nodes']['fine']:,}")
    N.put("numEtwoTransformerFineStep", f"{t_fi / 1000:.1f}")


# ---------------------------------------------------------------- cost (Section 8.4)
COST_SOLVERS = ("direct", "cg", "cg_warm", "cg_match", "cg_match_cstar")
COST_SETS = (("2D", "timing_2d.json", "val"), ("3D", "timing_3d.json", "val"),
             ("3D, fine mesh", "timing_3d.json", "fine"))
COST_TAG = {"2D": "Two", "3D": "ThreeVal", "3D, fine mesh": "ThreeFine"}


def _round2(x: float) -> int:
    """x to two significant figures, as an integer."""
    e = int(floor(log10(abs(x)))) - 1
    return int(round(x / 10 ** e) * 10 ** e)


def secs(x: float) -> str:
    """A wall time as the cost table writes it."""
    if x < 0.01:
        return f"{x * 1e3:.1f} ms"
    if x < 1:
        return f"{x * 1e3:.0f} ms"
    if x < 10:
        return f"{x:.2f} s"
    return f"{x:.1f} s" if x < 100 else f"{x:.0f} s"


def _med(rows: list, key: str) -> float:
    return statistics.median(float(r[key]) for r in rows)


def _med_loads(rows: list, key: str) -> float:
    """The median over every load case of the set."""
    return statistics.median(float(x) for r in rows for x in r[key])


def _med_solved(rows: list, key: str) -> float:
    """The median over the instances on which the value was measured."""
    return statistics.median(float(r[key]) for r in rows if r.get(key) is not None)


def cost_material(N: Numbers, used: dict) -> tuple:
    """The cost table and its numbers, from the per-instance records of RUNBOOK_CMAME
    Sec. G1 (28 October 2026: the timings of Sec. A run again on the machine of the Ritz
    baseline, beside the Ritz projection's own; medians over the instances, computed here)
    and the thread readings of RUNBOOK_W9 Sec. 4 (another host of the same type). Refuses
    a record in which a solver fell back to the direct solve or missed its target, whose
    timed model does not reproduce its report, or in which a solve is missing for any
    reason but the direct solver's time budget, which the script spends instance by
    instance (a skipped instance must then be the set's last ones)."""
    recs = {f: load(TIM2 / f, used) for f in ("timing_2d.json", "timing_3d.json")}
    mach = (RITZ / "machine.txt").read_bytes()
    used[_rel(RITZ / "machine.txt")] = hashlib.sha256(mach).hexdigest()
    mtxt = mach.decode("utf-8")
    cpu = re.search(r"^Model name:\s+(?:Intel\(R\) )?(.+)$", mtxt, re.M).group(1)
    nproc = int(re.search(r"^nproc (\d+)$", mtxt, re.M).group(1))
    cols, shared, budget = {}, None, {}
    for name, f, s in COST_SETS:
        rec = recs[f]
        if rec["skipped_families"] or rec["settings"]["solvers"] != list(COST_SOLVERS):
            raise SystemExit(f"{f}: not the cost table's solvers, or a family was skipped")
        chk = rec["check_against_report"]
        if not chk["checked"] or max(chk["disp_rel_l2_max_rel_dev"],
                                     chk["energy_gap_rel_max_rel_dev"]) > 1e-9:
            raise SystemExit(f"{f}: the timed model does not reproduce its report")
        rows = rec["results"][s]["per_instance"]
        skipped = [i for i, r in enumerate(rows) if r["direct_s"] is None]
        for i, r in enumerate(rows):
            if (r["cg_fallback"] or r["cg_warm_fallback"] or r["cg_match_unreached"]
                    or r["cg_match_cstar_unreached"] or r["cg_match_iters_mismatch"]
                    or r["cg_match_cstar_iters_mismatch"]
                    or any(r.get(f"{k}_s") is None for k in COST_SOLVERS if k != "direct")
                    or (r["direct_s"] is None and r.get("direct_skipped") != "budget")):
                raise SystemExit(f"{f} {s} {r['file']}: a solve is missing, fell back or "
                                 "missed its target")
        if skipped and skipped != list(range(len(rows) - len(skipped), len(rows))):
            raise SystemExit(f"{f} {s}: the direct solve skipped an instance before its last")
        if skipped:
            spent = sum(sum(r["direct_runs"]) for r in rows if r["direct_s"] is not None)
            if not spent >= rec["settings"]["solve_budget_s"]:
                raise SystemExit(f"{f} {s}: the direct solve skipped an instance within budget")
            budget[name] = (len(rows) - len(skipped), len(rows), rec["settings"]["solve_budget_s"])
        mc = rec["machine"]
        here = (mc["gpu"], mc["env_threads"]["OMP_NUM_THREADS"], mc["torch_threads"],
                rec["settings"]["cg_tol"])
        if shared not in (None, here):
            raise SystemExit("the two timing records ran in different settings")
        shared = here
        loads = {int(r["n_loads"]) for r in rows}
        if len(loads) != 1:
            raise SystemExit(f"{f} {s}: instances with different numbers of load cases")
        cols[name] = {"n": len(rows), "loads": loads.pop(), "rows": rows,
                      **{k: _med(rows, k) for k in (
                          "n_nodes", "surrogate_cold_s", "surrogate_warm_s", "cg_s",
                          "cg_warm_s", "cg_match_s", "cg_match_cstar_s", "energy_gap_rel",
                          "disp_rel_l2", "energy_gap_rel_cstar", "disp_rel_l2_cstar",
                          "cg_match_over_surrogate_cold", "cg_match_cstar_over_surrogate_cold",
                          "cg_warm_iteration_saving")},
                      **{k: _med_solved(rows, k) for k in ("direct_s",
                                                           "direct_over_surrogate_cold")},
                      **{f"{k}_per_load": _med_loads(rows, f"{k}_iters")
                         for k in ("cg", "cg_warm", "cg_match")},
                      "cg_match_disp_per_load": _med_loads(rows, "cg_match_disp_at_match"),
                      "worse_loads": sorted(float(x) for r in rows for x in r["cg_match_targets"]
                                            if float(x) > 1),
                      "worse_instances": sum(1 for r in rows if float(r["energy_gap_rel"]) > 1),
                      "settings": rec["settings"]}
    if list(budget) != ["3D, fine mesh"]:
        raise SystemExit(f"the direct solve's budget ended a set other than the text says: "
                         f"{list(budget)}")
    gpu, env_threads, torch_threads, tol = shared
    if str(env_threads) != str(torch_threads) or int(env_threads) != nproc:
        raise SystemExit("the timing's thread settings are not the machine's allotment")
    # the Ritz projection, timed on the same instances by scripts/ritz_timing.py
    rt = {"2D": load(TIM2 / "ritz_timing_2d.json", used)["results"]["val"],
          **{n: load(TIM2 / "ritz_timing_3d.json", used)["results"][s]
             for n, s in (("3D", "val"), ("3D, fine mesh", "fine"))}}
    rmach = {load(TIM2 / f, used)["machine"]["cpu"] for f in ("ritz_timing_2d.json",
                                                             "ritz_timing_3d.json")}
    if rmach != {f"Intel(R) {cpu}"}:
        raise SystemExit("the Ritz projection was timed on another machine than the table's")
    ritz_threads = {pl["num_threads"] for f in ("ritz_timing_2d.json", "ritz_timing_3d.json")
                    for pl in load(TIM2 / f, used)["machine"]["threadpools"]}
    if ritz_threads != {nproc}:
        raise SystemExit("the Ritz projection's BLAS threads are not the machine's allotment")
    ladder = {"2D": RITZ_LADDER[2], "3D": RITZ_LADDER[3], "3D, fine mesh": RITZ_LADDER[3]}
    for name in cols:
        r = rt[name]
        if ([x["file"] for x in r["rows"]] != [x["file"] for x in cols[name]["rows"]]
                or r["summary"]["K_max_rel_diff_max"] != 0.0 or not r["summary"]["complete"]):
            raise SystemExit(f"Ritz timing {name}: not the cost table's instances, or the "
                             "assembled K is not the instance's")
        cols[name]["assembly_s"] = _med(r["rows"], "assembly_s")
        if cols[name]["assembly_s"] != r["summary"]["assembly_s_median"]:
            raise SystemExit(f"Ritz timing {name}: the assembly median is not the record's")
        for p in ladder[name]:
            m = statistics.median(float(x["p"][str(p)]["ritz_s"]) for x in r["rows"])
            if (m != r["summary"]["p"][str(p)]["ritz_s"]
                    or any(x["p"][str(p)]["dropped"] for x in r["rows"])):
                raise SystemExit(f"Ritz timing {name} p = {p}: the median is not the record's")
            cols[name][f"ritz_{p}_s"] = m
    head = ["", *(n for n, _, _ in COST_SETS)]
    C = [cols[n] for n, _, _ in COST_SETS]

    def span(lo: float, hi: float) -> str:
        """A range of two wall times in one unit."""
        if hi < 0.01:
            return f"{lo * 1e3:.1f}–{hi * 1e3:.1f} ms"
        if hi < 1:
            return f"{lo * 1e3:.0f}–{hi * 1e3:.0f} ms"
        return f"{lo:.2f}–{hi:.2f} s"

    rows = [["Instances (load cases)", *(f"{c['n']} ({c['n'] * c['loads']})" for c in C)],
            ["Nodes, median", *(f"{round(c['n_nodes']):,}" for c in C)],
            ["Surrogate, first call", *(secs(c["surrogate_cold_s"]) for c in C)],
            ["Surrogate, repeated call", *(secs(c["surrogate_warm_s"]) for c in C)],
            ["Sparse direct solve", *(secs(c["direct_s"]) for c in C)],
            ["CG from the zero field", *(secs(c["cg_s"]) for c in C)],
            ["CG from the prediction", *(secs(c["cg_warm_s"]) for c in C)],
            ["CG to the prediction's accuracy", *(secs(c["cg_match_s"]) for c in C)],
            ["the same, after rescaling by c*", *(secs(c["cg_match_cstar_s"]) for c in C)],
            ["Assembly of $K$, the repository's assembler", *(secs(c["assembly_s"]) for c in C)],
            ["Ritz projection after assembly",
             *(span(c[f"ritz_{ps[0]}_s"], c[f"ritz_{ps[-1]}_s"])
               for c, ps in zip(C, (ladder[n] for n, _, _ in COST_SETS), strict=True))],
            ["CG iterations per load case",
             *(f"{c['cg_per_load']:,.0f} / {c['cg_match_per_load']:,.0f}" for c in C)],
            ["Surrogate's relative energy gap", *(num(c["energy_gap_rel"], 2) for c in C)],
            ["Surrogate's displacement error", *(num(c["disp_rel_l2"], 2) for c in C)],
            ["Energy gap after rescaling by c*",
             *(num(c["energy_gap_rel_cstar"], 2) for c in C)],
            ["Displacement error after rescaling by c*",
             *(num(c["disp_rel_l2_cstar"], 2) for c in C)],
            ["CG's displacement error at that accuracy",
             *(num(c["cg_match_disp_per_load"], 2) for c in C)]]
    # the threads of the solvers, timed again on another host of the same type
    thr2 = {}
    for k in ("env", "one"):
        rec = load(THR / f"timing_2d_{k}.json", used)
        thr2[k] = {q: _med(rec["results"]["val"]["per_instance"], q) for q in ("direct_s", "cg_s")}
        n_2d_thr = len(rec["results"]["val"]["per_instance"])
    gain2 = {q: 1 - thr2["one"][q] / thr2["env"][q] for q in ("direct_s", "cg_s")}
    thr, thr_n = {}, set()
    for k in ("env", "one", "env2"):
        rec = load(THR / f"timing_3d_{k}.json", used)
        thr[k] = {s: {q: _med(rec["results"][s]["per_instance"], q)
                      for q in ("direct_s", "cg_s")} for s in ("val", "fine")}
        thr_n.add(tuple(len(rec["results"][s]["per_instance"]) for s in ("val", "fine")))
    if len(thr_n) != 1:
        raise SystemExit("records/cmame/threads: the three timings timed different sets")
    n_val_thr, n_fine_thr = thr_n.pop()
    pools = {}
    for k in ("env", "one"):
        b = load(THR / f"blas_{k}.log", used)
        n_thr = {int(pl["num_threads"]) for pl in b["pools"]}
        if len(n_thr) != 1 or len(b["pools"]) != 2:
            raise SystemExit(f"blas_{k}.log: not two pools of one thread count")
        pools[k] = n_thr.pop()
    tmach = (THR / "machine.txt").read_bytes()
    used[_rel(THR / "machine.txt")] = hashlib.sha256(tmach).hexdigest()
    tcpu = re.search(r"^Model name:\s+(?:Intel\(R\) )?(.+)$", tmach.decode("utf-8"),
                     re.M).group(1)
    if tcpu != cpu or pools["env"] != nproc:
        raise SystemExit("records/cmame/threads: not a host of the cost table's type and "
                         "thread allotment")
    direct_dev = max(abs(thr["one"][s]["direct_s"] / thr["env"][s]["direct_s"] - 1)
                     for s in ("val", "fine"))
    cg_gain = [1 - thr["one"][s]["cg_s"] / thr["env"][s]["cg_s"] for s in ("val", "fine")]
    drift = max(abs(thr["env2"][s][q] / thr["env"][s][q] - 1) for s in ("val", "fine")
                for q in ("direct_s", "cg_s"))
    if not (direct_dev < 0.03 and min(cg_gain) > 0 and drift < 0.03):
        raise SystemExit("records/cmame/threads: the readings are not the text's")
    cpu_tex = cpu.replace("(R)", "").replace("  ", " ")
    fine = cols["3D, fine mesh"]
    st = cols["3D"]["settings"]
    worse = and_list([num(x, 3) for x in fine["worse_loads"]])
    solved, total, limit = budget["3D, fine mesh"]
    notes = [
        "Medians over the instances (CG iterations, from the zero field / to the prediction's "
        "accuracy, and CG's displacement error: over the load cases). 2D: the first "
        f"{cols['2D']['n']} validation instances of the two-dimensional comparison; 3D: the "
        f"first {cols['3D']['n']} validation and {fine['n']} fine-mesh instances of the "
        "three-dimensional comparison; the label-free transformers of seed 0. Wall times per "
        "instance, all load cases together, without the assembly, which the surrogate does "
        "not need.",
        f"Surrogate: one {gpu} with TF32, preparing the inputs and copying the prediction back "
        f"included; first call after an untimed warm-up on {st['warmup']} validation "
        f"instances, repeated call the median of {st['repeats'] - 1} further passes. Solvers: "
        f"the CPU of the same machine ({cpu_tex}, {nproc} CPUs, the thread environment set to "
        f"{env_threads}): SuperLU, which produced the labels, and unpreconditioned conjugate "
        "gradients (CG) to a relative residual of $10^{-10}$, from the zero field or from the "
        "prediction. CG to the prediction's accuracy stops, on each load case, at the first "
        "iterate whose relative energy error is at most the prediction's: it reads the "
        "reference solution, a lower bound. The fine-mesh direct solve used up its budget of "
        f"{limit:.0f} s after {words(solved)} of the {words(total)} instances; its median, and "
        f"the ratios that use it, are over those {words(solved)}.",
        r"Ritz projection (\cref{sec:methods:ritz}), from the lowest to the highest degree "
        f"($p = 6$ to 9 in 3D, 6 and 8 in 2D), with the machine's {nproc} BLAS threads: the "
        "time after the assembly of $K$, which is listed apart (in 2D the assembler also builds "
        "the four load vectors), for the free block, the basis, $\\Phi^{\\top}K\\Phi$ and "
        "$\\Phi^{\\top}F$, the small solve and the reconstruction.",
        f"On the fine mesh, {words(len(fine['worse_loads']))} of the {fine['n'] * fine['loads']} "
        f"load cases had a relative energy gap above 1 ({worse}) and "
        f"{words(fine['worse_instances'])} of the {words(fine['n'])} instances a mean above 1; "
        r"CG matches such a load case with no iteration. Threads: \cref{sec:cost:inference} "
        "and the supplementary material."]
    for name, _, _ in COST_SETS:
        c, tag = cols[name], COST_TAG[name]
        N.put(f"numCost{tag}DirectRatio", f"{c['direct_over_surrogate_cold']:.0f}"
              if c["direct_over_surrogate_cold"] >= 10 else f"{c['direct_over_surrogate_cold']:.1f}")
        N.put(f"numCost{tag}MatchRatio", f"{c['cg_match_over_surrogate_cold']:.1f}")
        N.put(f"numCost{tag}Gap", num(c["energy_gap_rel"], 2))
    N.put("numCostFineDirectSolved", words(solved))
    N.put("numCostFineDirectTotal", words(total))
    saving = [cols[n]["cg_warm_iteration_saving"] for n, _, _ in COST_SETS]
    if not (min(saving) < 0 < max(saving)):
        raise SystemExit("the warm start's median change of iterations is not of both signs")
    N.put("numCostWarmMore", pct(-min(saving)))
    N.put("numCostWarmFewer", pct(max(saving)))
    N.put("numCostCgTol", "$10^{-10}$" if tol == 1e-10 else _sci(tol, 1))
    # the break-even of Section 8.4: the labels of the 3D training instances at the median
    # direct solve, and the predictions after which one seed's training is recovered
    c3 = cols["3D"]
    hours = float(N["numTimeThreeSeed"])
    n_train = int(N["numThreeTrainSolves"].replace(",", "")) // c3["loads"]
    save_direct = c3["direct_s"] - c3["surrogate_cold_s"]
    save_match = c3["cg_match_s"] - c3["surrogate_cold_s"]
    if not (save_direct > 0 and save_match > 0):
        raise SystemExit("the surrogate is not faster than the solves it is set against")
    N.put("numCostLabelMin", f"{n_train * c3['direct_s'] / 60:.0f}")
    N.put("numCostBreakEvenDirect", f"{_round2(hours * 3600 / save_direct):,}")
    N.put("numCostBreakEvenMatch", f"{_round2(hours * 3600 / save_match):,}")
    N.put("numThreadsHost", str(pools["env"]))
    N.put("numThreadsDirectDev", pct(direct_dev))
    N.put("numThreadsCgGainMin", pct(min(cg_gain), 0))
    N.put("numThreadsCgGainMax", pct(max(cg_gain), 0))
    N.put("numThreadsValN", str(n_val_thr))
    N.put("numThreadsFineN", str(n_fine_thr))
    N.put("numThreadsDrift", pct(drift))
    N.put("numThreadsTwoN", str(n_2d_thr))
    N.put("numThreadsTwoDirect", pct(gain2["direct_s"]))
    N.put("numThreadsTwoCg", pct(gain2["cg_s"]))
    N.put("numCostThreads", str(env_threads))
    # the Ritz projection against the assembly and the surrogate (Section 8.4)
    rv = [cols["3D"][f"ritz_{p}_s"] for p in RITZ_LADDER[3]]
    rf_ = [cols["3D, fine mesh"][f"ritz_{p}_s"] for p in RITZ_LADDER[3]]
    if not (rv == sorted(rv) and rf_ == sorted(rf_)):
        raise SystemExit("the Ritz projection's time does not grow with p")
    def span_ends(lo: float, hi: float) -> tuple:
        """The two ends of a range as the table's span writes them, each with the unit."""
        v, unit = span(lo, hi).rsplit(" ", 1)
        a, b = v.split("–")
        return f"{a} {unit}", f"{b} {unit}"

    for tag, x in (("Val", rv), ("Fine", rf_)):
        lo, hi = span_ends(x[0], x[-1])
        N.put(f"numCostRitz{tag}Min", lo)
        N.put(f"numCostRitz{tag}Max", hi)
    N.put("numCostAsmVal", secs(cols["3D"]["assembly_s"]))
    N.put("numCostAsmFine", secs(cols["3D, fine mesh"]["assembly_s"]))
    over = [cols[n]["assembly_s"] / cols[n][f"ritz_{p}_s"] for n in ("3D", "3D, fine mesh")
            for p in RITZ_LADDER[3]]
    N.put("numCostAsmOverRitzMin", f"{min(over):.0f}")
    N.put("numCostAsmOverRitzMax", f"{max(over):.0f}")
    N.put("numCostSurrVal", secs(cols["3D"]["surrogate_cold_s"]))
    N.put("numCostSurrFine", secs(cols["3D, fine mesh"]["surrogate_cold_s"]))
    if not (rv[0] < cols["3D"]["surrogate_cold_s"] < rv[-1]
            and rf_[-1] < cols["3D, fine mesh"]["surrogate_cold_s"]):
        raise SystemExit("the Ritz projection against the surrogate is not as the text says")
    return head, rows, notes


def timing_rerun_numbers(N: Numbers, used: dict) -> None:
    """The earlier timing of the same instances and networks on another machine (RUNBOOK_CMAME
    Sec. A, 8 October 2026), against the cost table's (28 October 2026): the surrogate's
    accuracy the same to round-off, and the conjugate-gradient iterations within a few."""
    worst, iters = 0.0, 0
    for f, sets in (("timing_2d.json", ("val",)), ("timing_3d.json", ("val", "fine"))):
        old, new = load(TIM / f, used), load(TIM2 / f, used)
        if (old["state_sha256"] != new["state_sha256"] or old["report"] != new["report"]
                or old["settings"]["cg_tol"] != new["settings"]["cg_tol"]):
            raise SystemExit(f"{f}: the two timings did not time the same network")
        for s in sets:
            ro, rn = old["results"][s]["per_instance"], new["results"][s]["per_instance"]
            if [r["file"] for r in ro] != [r["file"] for r in rn]:
                raise SystemExit(f"{f} {s}: the two timings timed different instances")
            for a, b in zip(ro, rn, strict=True):
                for k in METRICS + ("energy_gap_rel_cstar", "disp_rel_l2_cstar", "cstar"):
                    x, y = np.asarray(a[k], dtype=float), np.asarray(b[k], dtype=float)
                    worst = max(worst, float(np.max(np.abs(y - x) / np.abs(x))))
                for k in ("cg_iters", "cg_warm_iters", "cg_match_iters"):
                    iters = max(iters, max(abs(x - y) for x, y in zip(a[k], b[k], strict=True)))
    mach = (TIM / "machine.txt").read_bytes()
    used[_rel(TIM / "machine.txt")] = hashlib.sha256(mach).hexdigest()
    mtxt = mach.decode("utf-8")
    cpu = re.search(r"^Model name:\s+(?:Intel\(R\) )?(.+)$", mtxt, re.M).group(1)
    nproc = int(re.search(r"^nproc (\d+)$", mtxt, re.M).group(1))
    if not (worst < 1e-12 and 0 < iters <= 5):
        raise SystemExit("the two timings' accuracies or iteration counts are not the text's")
    N.put("numRerunCpu", cpu.replace("(R)", "").replace("  ", " "))
    N.put("numRerunThreads", str(nproc))
    N.put("numRerunAccDev", _sci(worst, 1))
    N.put("numRerunIters", words(iters))


# ---------------------------------------------------------------- K3D (PREREG_K3D)
K3D_HYP = (("H2a-3D", "labels_knorm", "labels", "energy_gap_rel"),
           ("H2b-3D", "labels_knorm", "labels", "vm_rel_l2"),
           ("H3-3D", "labels_knorm", "ar", "energy_gap_rel"))


def as_e8(rep: dict) -> dict:
    """A report whose cells sit at its top level (K3D's), in the layout of an e8 report,
    so that the readers above apply."""
    return {"results": {"e8": {"metrics": {"cells": rep["cells"]}}}}


def seed_medians(report: dict, arm: str, metric: str, b: str = "1024") -> list:
    """Each seed's median over the instances (PREREG_K3D Sec. 3: numpy.median)."""
    return [float(x) for x in np.median(per_instance(report, arm, metric, b), axis=1)]


def _ival(w: dict, dec: int = 1) -> str:
    return _interval(w["low"], w["high"], dec)


def k3d_material(N: Numbers, k: dict, vk: dict, r3: dict) -> tuple:
    """The three-dimensional energy-norm run (PREREG_K3D): its verdicts with the readings
    that its Sec. 4 requires beside each, recomputed where the report allows, the numbers
    the text quotes, and the tables (the verdicts; in the supplementary material, the
    secondary comparisons and the medians)."""
    # the stored networks were evaluated again and reproduced Phase-2b's values exactly
    for arm in ("ar", "labels"):
        for m in METRICS:
            if not np.array_equal(per_instance(k, arm, m), per_instance(r3, arm, m)):
                raise SystemExit(f"K3D: the stored {arm} networks do not reproduce Phase-2b's "
                                 f"{m}")
    for kind, cc in vk["content_checks"].items():
        for st, ch in cc.items():
            if any(x != 0.0 for kk, x in ch.items() if kk.endswith("_rel_dev")):
                raise SystemExit(f"K3D: the content check {kind} {st} is not exact")
    if vk["deviations"] or vk["statistic"] != "per-seed medians" or vk["budget"] != 1024:
        raise SystemExit("K3D: the verdict records a deviation, or another statistic or budget")
    for h, a, b, m in K3D_HYP:
        x = vk[h]
        if not (x["metric"] == m and x["statistic"] == "per-seed medians"
                and np.allclose(x["new_per_seed"], seed_medians(k, a, m), rtol=1e-12, atol=0)
                and np.allclose(x["base_per_seed"], seed_medians(k, b, m), rtol=1e-12, atol=0)):
            raise SystemExit(f"K3D {h}: the verdict's values are not the report's medians")
        sm = x["beside"]["seed_means"]
        if not (np.isclose(sm["new_mean"], seed_mean(k, a, m), rtol=1e-12, atol=0)
                and np.isclose(sm["base_mean"], seed_mean(k, b, m), rtol=1e-12, atol=0)):
            raise SystemExit(f"K3D {h}: the verdict's seed means are not the report's")
        if not x["beside"]["seed_means_show_the_direction"]:
            raise SystemExit(f"K3D {h}: the seed means do not show the verdict's direction")
        ir = x["beside"]["instance_resampling_95"]
        if not (ir["resamples"] == 2000 and ir["level"] == x["beside"]["welch_95"]["level"]
                == x["beside"]["seed_means_welch_95"]["level"] == 0.95):
            raise SystemExit(f"K3D {h}: the intervals beside the verdict are not at 95%")
    for h in ("H2a-3D", "H2b-3D"):
        x = vk[h]
        if not (x["verdict"] == "SUPPORTED"
                and all(n_ < b_ for n_, b_ in zip(x["new_per_seed"], x["base_per_seed"],
                                                  strict=True))):
            raise SystemExit(f"K3D {h}: the text reports SUPPORTED, lower in each seed")
    h3 = vk["H3-3D"]
    w = h3["beside"]["welch_95"]
    if not (h3["reading"] == "the stiffness-norm transformer lower beyond the guard"
            and w["low"] < 0 < w["high"]):
        raise SystemExit("K3D H3-3D: the text reports a reduction beyond the guard whose Welch "
                         "interval includes zero")
    # the seed means of H2a-3D cannot show a reduction: the guard exceeds 100%
    g = vk["H2a-3D"]["beside"]["seed_means"]
    if not (g["threshold"] > 1 and g["rel_change"] < 0 and not g["lower"]):
        raise SystemExit("K3D H2a-3D: the seed-mean guard is not the text's")
    gv = vk["H2b-3D"]["beside"]["seed_means"]
    if not gv["lower"]:
        raise SystemExit("K3D H2b-3D: the seed means do not read lower beyond the guard")
    # pairs, and predictions worse than the zero field, from the report's arrays
    gap = {a: per_instance(k, a, "energy_gap_rel") for a in ("ar", "labels", "labels_knorm")}
    pk = vk["secondary"]["pairing"]["labels_knorm_vs_ar"]["energy_gap_rel"]
    win = int((gap["labels_knorm"] < gap["ar"]).sum())
    if not (pk["first_lower"] == win and pk["ties"] == 0 and pk["pairs"] == gap["ar"].size):
        raise SystemExit("K3D: the pairs of L_K against the label-free transformer differ")
    wz = vk["secondary"]["worse_than_zero"]
    for a in gap:
        if wz[a]["count"] != int((gap[a] > 1).sum()):
            raise SystemExit(f"K3D: the predictions of {a} worse than the zero field differ")
    if wz["labels_knorm"]["count"] or wz["ar"]["count"]:
        raise SystemExit("K3D: the text says no transformer trained in the energy norm, "
                         "with or without labels, was worse than the zero field")
    # the secondary comparisons (exploratory): L_K against the label-free transformer
    comp = vk["secondary"]["comparisons"]
    n_comp = sum(len(stat) for m in comp.values() for stat in m.values())
    if n_comp != 30:
        raise SystemExit(f"K3D: {n_comp} secondary comparisons; the text says 30")
    vs_free = {m: comp[m]["labels_knorm_vs_ar"]["medians"] for m in METRICS}
    better = {m: (vs_free[m]["lower"] if m != "crit_recall" else vs_free[m]["worse"])
              for m in METRICS}
    if better != {"disp_rel_l2": True, "energy_gap_rel": True, "vm_rel_l2": True,
                  "peak_vm_rel_err": True, "crit_recall": False} or \
            vs_free["crit_recall"]["lower"]:
        raise SystemExit(f"K3D: L_K against the label-free transformer on medians reads "
                         f"{better}")
    # the holdout readings (no verdict)
    ho = vk["secondary"]["holdout"]
    if ho["n"] != 686:
        raise SystemExit("K3D: the holdout readings are not on the 686 instances")
    for h in ("H2a-3D", "H2b-3D", "H3-3D"):
        x = ho["hypotheses"][h]
        if not (x["direction"] == "lower" and x["same_direction"]):
            raise SystemExit(f"K3D {h}: the holdout reading is not the validation's")
    # numbers
    for h, H in (("H2a-3D", "Gap"), ("H2b-3D", "Vm"), ("H3-3D", "Free")):
        x = vk[h]
        N.put(f"numKd{H}Rel", pct(abs(x["rel_change"])))
        N.put(f"numKd{H}Tau", pct(x["threshold"]))
        y = ho["hypotheses"][h]["medians"]
        N.put(f"numKdHold{H}Rel", pct(abs(y["rel_change"])))
        N.put(f"numKdHold{H}Tau", pct(y["threshold"]))
    N.put("numKdMeansVmRel", pct(abs(gv["rel_change"])))
    N.put("numKdMeansVmTau", pct(gv["threshold"]))
    wv = vk["H2b-3D"]["beside"]["seed_means_welch_95"]
    if not wv["low"] < 0 < wv["high"]:
        raise SystemExit("K3D H2b-3D: the text says the Welch interval of the seed-mean "
                         "reduction includes zero")
    N.put("numKdMeansVmWelchLow", spct(wv["low"]))
    N.put("numKdMeansVmWelchHigh", spct(wv["high"]))
    N.put("numKdMeansGapRel", pct(abs(g["rel_change"]), 2))
    N.put("numKdMeansGapTau", pct(g["threshold"]))
    N.put("numKdFreePairs", f"{win:,}")
    N.put("numKdFreeWelchLow", spct(w["low"]))
    N.put("numKdFreeWelchHigh", spct(w["high"]))
    N.put("numKdFreeDispRel", pct(abs(vs_free["disp_rel_l2"]["rel_change"])))
    N.put("numKdFreeVmRel", pct(abs(vs_free["vm_rel_l2"]["rel_change"])))
    N.put("numKdFreePeakRel", pct(abs(vs_free["peak_vm_rel_err"]["rel_change"])))
    N.put("numKdSecondary", str(n_comp))
    fm = h3["base_per_seed"]
    N.put("numKdFreeMedMin", num(min(fm), 2))
    N.put("numKdFreeMedMax", num(max(fm), 2))
    N.put("numKdKnormGapMedian", num(statistics.fmean(h3["new_per_seed"]), 2))
    N.put("numKdLabGapMedian", num(statistics.fmean(vk["H2a-3D"]["base_per_seed"]), 2))
    N.put("numKdFreeGapMedian", num(statistics.fmean(fm), 2))
    # the share of the L_D transformer's excess over the label-free transformer that L_K
    # removes, on the seed-averaged medians (PREREG_K3D Sec. 5, descriptive), recomputed
    gc = vk["secondary"]["gap_closure"]
    for m, M in (("vm_rel_l2", "Vm"), ("energy_gap_rel", "Gap")):
        md = {a: statistics.fmean(seed_medians(k, a, m)) for a in ("labels", "labels_knorm", "ar")}
        c = (md["labels"] - md["labels_knorm"]) / (md["labels"] - md["ar"])
        if not np.isclose(c, gc[m]["medians"]["closure"], rtol=1e-12, atol=0):
            raise SystemExit(f"K3D: the share of the gap closed in {m} is not the verdict's")
        if not c > 1:
            raise SystemExit(f"K3D: the text says the change of norm closed the whole gap in {m}")
        N.put(f"numKdClosure{M}", pct(c))
    for m in METRICS:
        N.put(f"numThreeKnorm{MTAG[m]}", num(seed_mean(k, "labels_knorm", m)))
    N.put("numThreeKnormWorse", f"{wz['labels_knorm']['count']:,}")
    # the table of the verdicts (PREREG_K3D Sec. 4)
    names = {"labels_knorm": NAMES["labels_knorm"], "labels": f"Supervised ({LD})",
             "ar": NAMES["ar"]}
    head = ["", "H2a-3D", "H2b-3D", "H3-3D"]
    rows = {key: [key] for key in (
        "Network A", "Reference B", "Metric", "A, seeds 0, 1, 2", "B, seeds 0, 1, 2", "rel",
        "SE_rel", "Guard", "Reading", "Welch 95% interval", "Instance resampling 95%",
        "Seed means: rel (guard)", "Seed means: Welch 95%", "Holdout: rel (guard)",
        "Holdout, seed means: rel (guard)")}
    reading = {"SUPPORTED": "supported", "NOT SUPPORTED": "not supported"}
    for h, a, b, m in K3D_HYP:
        x, bs, y = vk[h], vk[h]["beside"], ho["hypotheses"][h]
        for key, val in (
                ("Network A", names[a]), ("Reference B", names[b]), ("Metric", HYP_METRICS[m]),
                ("A, seeds 0, 1, 2", ", ".join(num(t) for t in x["new_per_seed"])),
                ("B, seeds 0, 1, 2", ", ".join(num(t) for t in x["base_per_seed"])),
                ("rel", spct(x["rel_change"])), ("SE_rel", pct(x["se_rel"])),
                ("Guard", pct(x["threshold"])),
                ("Reading", reading[x["verdict"]] if h != "H3-3D" else "A lower"),
                ("Welch 95% interval", _ival(bs["welch_95"])),
                ("Instance resampling 95%", _ival(bs["instance_resampling_95"])),
                ("Seed means: rel (guard)", _rel_guard(bs["seed_means"])),
                ("Seed means: Welch 95%", _ival(bs["seed_means_welch_95"], 0)),
                ("Holdout: rel (guard)", _rel_guard(y["medians"])),
                ("Holdout, seed means: rel (guard)", _rel_guard(y["means"]))):
            rows[key].append(val)
    ex = h3["roles_exchanged"]
    notes = [
        "Every reading is of the seeds' values, each seed's median over the 256 validation "
        "instances (the pre-registered statistic) unless the row says seed means; rel, "
        r"SE_rel and the noise guard as defined in the note to \cref{tab:criteria}. "
        "Welch: rel ± t × SE_rel at the Welch–Satterthwaite degrees of freedom, a symmetric "
        "interval that can extend below −100%. Instance resampling: the 2.5% and 97.5% "
        "percentiles of rel over 2,000 resamplings of the 256 instances, the same instances "
        "for both networks and every seed, the seeds kept, each seed's value the median of "
        f"its resampled values. Holdout: the same readings on the {ho['n']} held-out "
        r"instances of \cref{sec:holdout}, without a verdict.",
        f"H3-3D is a reading without a criterion. With the roles of A and B exchanged, rel was "
        f"{spct(ex['rel_change'])} against a guard of {pct(ex['threshold'])}."]
    # supplementary: the medians and means of every metric, and the 30 comparisons
    sup_head = ["Network", "Statistic", "Displacement\nerror", "Relative\nenergy gap",
                "von Mises\nerror", "Peak stress\nerror", "Critical-region\nrecall"]
    sup_rows = []
    for a in ("ar", "labels", "labels_knorm"):
        st_ = vk["secondary"]["seed_table"][a]
        for stat, key in (("median", "median_per_seed"), ("mean", "mean_per_seed")):
            sup_rows.append([names[a] if stat == "median" else "",
                             "seed medians" if stat == "median" else "seed means"]
                            + [ms(st_[m][key]) for m in METRICS])
    comp_head = ["Comparison (A against B)", "Metric", "Medians: rel (guard)", "Reading",
                 "Seed means: rel (guard)", "Reading"]
    comp_rows = []
    label = {"labels_knorm_vs_labels": f"Energy norm against displacement ({LD})",
             "labels_knorm_vs_ar": "Energy norm against label-free",
             "ar_vs_labels": f"Label-free against supervised ({LD})"}
    mname = dict(zip(METRICS, ("Displacement error", "Relative energy gap", "von Mises error",
                               "Peak stress error", "Critical-region recall"), strict=True))

    def rd(c_, m):
        if c_.get("diverged"):
            return "diverged"
        hi = m == "crit_recall"
        if c_["lower"]:
            return "A worse" if hi else "A better"
        if c_["worse"]:
            return "A better" if hi else "A worse"
        return "within"

    for cname in label:
        for m in METRICS:
            c_ = comp[m][cname]
            comp_rows.append([label[cname] if m == "disp_rel_l2" else "", mname[m],
                              _rel_guard(c_["medians"]), rd(c_["medians"], m),
                              _rel_guard(c_["means"]), rd(c_["means"], m)])
    return (head, list(rows.values()), notes), (sup_head, sup_rows), (comp_head, comp_rows)


# ---------------------------------------------------------------- the norm and the labels
NL_ARMS = ("labels", "labels_knorm", "ar")      # displacement, energy norm with and without labels
NL_TAG = {"labels": "Lab", "labels_knorm": "Knorm", "ar": "Free"}


def _nl_values(report: dict) -> dict:
    """Per arm, per seed: the median over the instances of the relative energy-norm error
    g^(1/2) (each instance's g the mean over its load cases, as the evaluation records it)
    and of the von Mises error; and the same as means over the instances."""
    out = {}
    for arm in NL_ARMS:
        e = np.sqrt(per_instance(report, arm, "energy_gap_rel"))
        v = per_instance(report, arm, "vm_rel_l2")
        out[arm] = {"E_med": [float(x) for x in np.median(e, axis=1)],
                    "Vm_med": [float(x) for x in np.median(v, axis=1)],
                    "E_mean": [float(x) for x in e.mean(axis=1)],
                    "Vm_mean": [float(x) for x in v.mean(axis=1)]}
    return out


def norm_label_material(N: Numbers, k: dict, rcm: dict) -> dict:
    """The norm of the loss against the labels (Fig. 1): the same transformer trained on the
    solutions with the displacement loss, on the solutions in the energy norm, and on the
    energy without solutions; in three dimensions the energy-norm run's report (which
    evaluated the two stored transformers again, reproducing their values exactly), in two
    the two-dimensional comparison's. Descriptive: the medians over the instances of the
    relative energy-norm error g^(1/2) and of the von Mises error, averaged over the three
    seeds, and their ratios; the pre-registered verdicts are those of Table A.1. Every
    statement the text makes about these numbers is checked here."""
    fig = {}
    for dim, rep in (("Three", k), ("Cm", rcm)):
        val = _nl_values(rep)
        m = {a: {q: statistics.fmean(val[a][q]) for q in val[a]} for a in NL_ARMS}
        for a in NL_ARMS:
            N.put(f"numNl{dim}E{NL_TAG[a]}", num(m[a]["E_med"]))
            N.put(f"numNl{dim}Vm{NL_TAG[a]}", num(m[a]["Vm_med"]))
        r = {(q, s_): m["labels" if s_ == "Norm" else "ar"][f"{q}_{st}"]
             / m["labels_knorm"][f"{q}_{st}"]
             for q in ("E", "Vm") for s_ in ("Norm", "Label") for st in ("med",)}
        for q in ("E", "Vm"):
            N.put(f"numNl{dim}Norm{q}", f"{r[(q, 'Norm')]:.1f}")
            N.put(f"numNl{dim}Label{q}", f"{r[(q, 'Label')]:.2f}")
            N.put(f"numNl{dim}Norm{q}Mean",
                  f"{m['labels'][f'{q}_mean'] / m['labels_knorm'][f'{q}_mean']:.1f}")
        # the text: changing the norm moves both errors far more than removing the labels;
        # the energy norm is the better with labels and without, in each seed
        for q in ("E", "Vm"):
            rn, rl = r[(q, "Norm")], r[(q, "Label")]
            if not (rn >= 2 and 1 < rl <= 1.35 and np.log(rn) > 3 * np.log(rl)):
                raise SystemExit(f"norm and labels ({dim}, {q}): the text says the norm moved "
                                 "the error by a factor of at least two, the labels by at most "
                                 "1.35, a third of the norm's effect on a logarithmic scale")
            for st in ("med", "mean"):
                lab, kn, fr = (val[a][f"{q}_{st}"] for a in NL_ARMS)
                if not all(x > y and x > z for x, y, z in zip(lab, kn, fr, strict=True)):
                    raise SystemExit(f"norm and labels ({dim}, {q}, {st}): the displacement "
                                     "loss is not the worst in every seed")
        fig[dim] = {"med": m, "seeds": val}
    # three dimensions: the label-free transformer within the factor that the text quotes of
    # the energy-norm-supervised one, in both errors
    within = float(N["numNlThreeLabelE"])
    q1 = round(within, 1)
    if not (q1 >= within and q1 >= float(N["numNlThreeLabelVm"])):
        raise SystemExit("norm and labels: the text says the label-free transformer came within "
                         "a factor of " + f"{q1}")
    N.put("numNlThreeLabelWithin", f"{q1:.1f}")
    # the highlight: the von Mises error cut "sixfold" (to the nearest integer)
    N.put("numNlThreeNormVmWord", words(round(float(N["numNlThreeNormVm"]))))
    return fig


# ---------------------------------------------------------------- holdout (PREREG_HOLDOUT)
def _arrays_values(z: dict, row: str, metric: str) -> np.ndarray:
    """(seeds, instances) per-instance values of a holdout evaluation's arrays."""
    return z["values"][list(z["rows"]).index(row), :, :, list(z["metrics"]).index(metric)]


def holdout_material(N: Numbers, vho: dict, used: dict, r3: dict, rcm: dict,
                     vcm: dict) -> tuple:
    """The holdout evaluation (PREREG_HOLDOUT): the eight claims with their values on the
    validation and the holdout instances, H3 and V; the readings beside H2a (Sec. 6),
    recomputed from the arrays; the sets, from the labels manifests; the numbers the text
    quotes; and the tables (the claims, and the means and medians that any revision
    reports beside the validation ones)."""
    c = vho["claims"]
    want = {h: "REPLICATED" for h in HOLD_CLAIMS} | {"H2a": "NOT REPLICATED"}
    if {h: c[h]["verdict"] for h in HOLD_CLAIMS} != want or c["H2a"]["failing"] != ["H2a"]:
        raise SystemExit("holdout: the verdicts are not those the text reports")
    if vho["tally"] != {"REPLICATED": 7, "NOT REPLICATED": 1, "NOT EVALUATED": 0}:
        raise SystemExit("holdout: the tally is not the text's")
    V = vho["V"]
    if not (V["verdict"] == "REPRESENTATIVE" and V["rejected"] == [] and V["left_out"] == []
            and len(V["quantities"]) == 35 and V["alpha"] == 0.05):
        raise SystemExit("holdout: V is not the text's")
    if set(vho["validation_reference"]["claims"].values()) != {"REPLICATED"}:
        raise SystemExit("holdout: a claim's rule does not read REPLICATED on the validation "
                         "instances")
    if len(vho["deviations"]) != 4 or not all("2 attempts (exits [2, 0])" in d
                                              for d in vho["deviations"]):
        raise SystemExit("holdout: the deviations are not the two attempts of each stage")
    man = {s: load(HOLD / "return" / s / "manifest.json", used) for s in ("h3d", "h2d")}
    z = {s: load_npz(HOLD / "return" / s / "eval_arrays.npz", used) for s in ("h3d", "h2d")}
    for s, mf in man.items():
        tail = mf["n_corpus"] - mf["split"]["n_val"] - mf["used_prefix"]
        if not (mf["n"] == tail - len(mf["excluded"]) == z[s]["values"].shape[2]
                and mf["method"] == "direct" and mf["reused"] == 0
                and mf["ledger"]["total"] == 4 * mf["n"]):
            raise SystemExit(f"holdout {s}: the set is not the text's")
        S = {"h3d": "Three", "h2d": "Two"}[s]
        N.put(f"numHold{S}N", f"{mf['n']:,}")
        N.put(f"numHold{S}Tail", f"{tail:,}")
        N.put(f"numHold{S}Excl", f"{len(mf['excluded']):,}")
        N.put(f"numHold{S}Solves", f"{mf['ledger']['total']:,}")
    # T1 to T3, H1 to D2 on the validation instances (the values of Sections 5 and 6)
    t1v = sum(bool(_better(m, [seed_mean(r3, "ar", m)], [seed_mean(r3, "labels", m)])[0])
              + int(_better(m, seed_values(r3, "ar", "1024", m),
                            seed_values(r3, "labels", "1024", m)).sum()) for m in METRICS)
    d2v = 0
    for m in METRICS:
        a, b = seed_values(rcm, "ar", "1024", m), seed_values(rcm, "labels", "1024", m)
        holds = (np.array(a) > np.array(b)) if m == "disp_rel_l2" else _better(m, a, b)
        mean_ok = (statistics.fmean(a) > statistics.fmean(b)) if m == "disp_rel_l2" else \
            bool(_better(m, [statistics.fmean(a)], [statistics.fmean(b)])[0])
        d2v += int(holds.sum()) + int(mean_ok)
    t1h = _comparisons(c["T1"]["per_metric"], "better_in_seed", "better_in_mean")
    d2h = _comparisons(c["D2"]["per_metric"], "holds_in_seed", "holds_in_mean")
    if not (t1v == d2v == 20 and t1h == d2h == (20, 20)):
        raise SystemExit("holdout: T1 or D2 does not hold in every comparison")
    fr, mg = (per_instance(r3, a, "disp_rel_l2") for a in ("ar", "mgn"))
    t2v = (mg < fr).mean(axis=1)
    t2vm = float((per_instance(r3, "mgn", "vm_rel_l2") > per_instance(r3, "ar",
                                                                      "vm_rel_l2")).mean())
    t2 = c["T2"]
    t3 = c["T3"]["per_row"]
    if any(t3[r]["sign_mismatch"] or t3[r]["finite"] != t3[r]["load_cases"]
           for r in ("labels", "mgn")):
        raise SystemExit("holdout T3: a load case worse than the zero field without a positive "
                         "energy, or a value that is not finite")
    head = ["Claim", "Statement", "Validation", "Holdout", "Outcome"]
    cm = {h: vcm[h] for h in ("H1", "H2a", "H2b", "H3")}
    word = {"REPLICATED": "replicated", "NOT REPLICATED": "not replicated"}
    rows = [
        ["T1 (3D)", "Label-free transformer better than the displacement-supervised transformer on all five "
         "metrics, each seed and the seed mean", f"{t1v} of 20", f"{t1h[0]} of 20",
         word[c["T1"]["verdict"]]],
        ["T2 (3D)", "Graph network: lower displacement error than the label-free transformer "
         "on most instances, each seed; higher von Mises error on at least 95% of the pairs",
         f"{pct(t2v.min())}–{pct(t2v.max())}; {upct(t2vm)}",
         f"{pct(min(t2['disp_lower_share_per_seed']))}–"
         f"{pct(max(t2['disp_lower_share_per_seed']))}; {upct(t2['vm_higher_share_pooled'])}",
         word[t2["verdict"]]],
        ["T3 (3D)", "Load cases worse than the zero field, displacement-supervised "
         "transformer and graph "
         "network, each with a positive energy",
         f"{N['numFieldLoadWorseLab']} and {N['numFieldLoadWorseMgn']} of {N['numFieldLoads']}",
         f"{t3['labels']['worse']:,} and {t3['mgn']['worse']:,} of "
         f"{t3['labels']['load_cases']:,}", word[c["T3"]["verdict"]]],
        ["H1 (2D)", "Label-free below the displacement-supervised transformer in relative energy gap, "
         "beyond the guard", _rel_guard(cm["H1"]), _rel_guard(c["H1"]),
         word[c["H1"]["verdict"]]],
        ["H2a (2D)", "Energy-norm-supervised below the displacement-supervised transformer in relative "
         "energy gap, "
         "beyond the guard", _rel_guard(cm["H2a"]), _rel_guard(c["H2a"]),
         r"\hspace{0pt}" + word[c["H2a"]["verdict"]]],
        ["H2b (2D)", "The same in von Mises error", _rel_guard(cm["H2b"]), _rel_guard(c["H2b"]),
         word[c["H2b"]["verdict"]]],
        ["H2c (2D)", "The same, by more than half", spct(cm["H2b"]["rel_change"]),
         spct(c["H2c"]["rel_change"]), word[c["H2c"]["verdict"]]],
        ["D2 (2D)", "Label-free transformer: higher displacement error than the "
         "displacement-supervised one, lower errors on the other four metrics, each seed and the seed mean",
         f"{d2v} of 20", f"{d2h[0]} of 20", word[c["D2"]["verdict"]]],
        ["H3 (2D)", "A reading: energy-norm-supervised against label-free transformer, relative "
         "energy gap", _rel_guard(cm["H3"]), _rel_guard(vho["readings"]["H3"]),
         "no difference shown"],
        ["V", "Per-instance values alike on the holdout and validation instances, "
         f"{len(V['quantities'])} quantities", "–", "none rejected",
         r"\hspace{0pt}" + V["verdict"].lower()]]
    if not (abs(c["H2c"]["rel_change"] - c["H2b"]["rel_change"]) == 0
            and c["H2c"]["threshold"] == -0.5):
        raise SystemExit("holdout H2c: not the comparison of H2b against halving")
    if not all(cm[h]["verdict"] == "SUPPORTED" for h in ("H1", "H2a", "H2b")):
        raise SystemExit("holdout: the validation verdicts are not those of the text")
    notes = [
        r"Validation: the values of \cref{sec:norm,sec:labelfree,sec:checks} on the validation "
        r"instances (T3 per load case). Holdout: "
        f"the same stored networks on {N['numHoldThreeN']} (3D) and {N['numHoldTwoN']} (2D) "
        "held-out instances. T1 and D2: the comparisons that hold, five metrics in three seeds and the "
        "seed mean; T2: the lowest and highest share over the seeds, and the share of the "
        "instance-seed pairs; H1 to H3: rel and the noise guard of the note to "
        r"\cref{tab:claims}; H2c: the rel of H2b, against −50%. V: per network and metric, a "
        "two-sided Mann–Whitney test of the holdout against the validation instances, the "
        f"{len(V['quantities'])} p-values taken together by Holm's procedure at a family-wise "
        f"level of {pct(V['alpha'], 0)} " + r"(supplementary Section~\SuppPrereg)."]
    # the readings beside H2a (PREREG_HOLDOUT Sec. 6; no verdict)
    h2a = c["H2a"]
    kn = _arrays_values(z["h2d"], "labels_knorm", "energy_gap_rel")
    lb = _arrays_values(z["h2d"], "labels", "energy_gap_rel")
    if not (np.allclose(kn.mean(axis=1), h2a["new_per_seed"], rtol=1e-12, atol=0)
            and np.allclose(lb.mean(axis=1), h2a["base_per_seed"], rtol=1e-12, atol=0)):
        raise SystemExit("holdout H2a: the arrays are not the verdict's")
    gm = vho["secondary"]["h2d"]["holdout"]["guard_labels_knorm_vs_labels"]["energy_gap_rel"][
        "guard_medians"]
    if not (np.allclose(gm["new_per_seed"], np.median(kn, axis=1), rtol=1e-12, atol=0)
            and np.allclose(gm["base_per_seed"], np.median(lb, axis=1), rtol=1e-12, atol=0)
            and gm["lower"]):
        raise SystemExit("holdout H2a: the guard on the medians is not the text's")
    ri = vho["secondary"]["h2d"]["ratio_interval"]["labels_knorm"]["energy_gap_rel"]
    q = V["quantities"]["h2d:labels_knorm:energy_gap_rel"]
    if not (q["holdout_worse"] and not q["rejected"]
            and np.isclose(q["ratio_of_means"], ri["ratio"], rtol=1e-12, atol=0)
            and ri["interval_95_holdout"][0] > 1):
        raise SystemExit("holdout H2a: the ratio of the means is not the text's")
    top = kn.max(axis=1)
    if not (int(np.argmin(top)) == 1 and top.max() > 100):
        raise SystemExit("holdout H2a: the largest gaps are not those the text names")
    N.put("numHoldHTwoARel", pct(abs(h2a["rel_change"])))
    N.put("numHoldHTwoATau", pct(h2a["threshold"]))
    N.put("numHoldHTwoASeedZero", pct(1 - h2a["new_per_seed"][0] / h2a["base_per_seed"][0], 0))
    if not 0 < h2a["new_per_seed"][0] < h2a["base_per_seed"][0]:
        raise SystemExit("holdout H2a: seed 0 is not below the displacement-supervised transformer's")
    N.put("numHoldHTwoANewSeeds", and_list(num(x) for x in h2a["new_per_seed"]))
    N.put("numHoldHTwoABaseSeeds", and_list(num(x) for x in h2a["base_per_seed"]))
    N.put("numHoldHTwoATop", f"{top.max():.0f}")
    N.put("numHoldHTwoATopSeeds", and_list(f"{x:.1f}" for x in top))
    N.put("numHoldHTwoARatio", f"{ri['ratio']:.2f}")
    N.put("numHoldHTwoARatioLow", f"{ri['interval_95_holdout'][0]:.2f}")
    N.put("numHoldHTwoARatioHigh", f"{ri['interval_95_holdout'][1]:.2f}")
    N.put("numHoldHTwoAMedHold", num(q["holdout_median"]))
    N.put("numHoldHTwoAMedVal", num(q["validation_median"]))
    N.put("numHoldHTwoAMedRel", pct(abs(gm["rel_change"])))
    N.put("numHoldHTwoAMedTau", pct(gm["threshold"]))
    for h, H in (("H1", "One"), ("H2b", "TwoB")):
        N.put(f"numHoldH{H}Rel", pct(abs(c[h]["rel_change"])))
        N.put(f"numHoldH{H}Tau", pct(c[h]["threshold"]))
    h3 = vho["readings"]["H3"]
    N.put("numHoldHThreeRel", spct(h3["rel_change"]))
    N.put("numHoldHThreeTau", pct(h3["threshold"]))
    if not h3["rel_change"] > 0:
        raise SystemExit("holdout H3: the text says the label-free transformer's gap was the "
                         "lower on the seed means")
    N.put("numHoldTwoFreeGap", num(h3["base_mean"]))
    N.put("numHoldTwoKnormGap", num(h3["new_mean"]))
    N.put("numHoldTThreeLab", f"{t3['labels']['worse']:,}")
    N.put("numHoldTThreeMgn", f"{t3['mgn']['worse']:,}")
    N.put("numHoldTThreeLoads", f"{t3['labels']['load_cases']:,}")
    N.put("numHoldVQuantities", str(len(V["quantities"])))
    dev: dict = {}
    for cc in vho["content_checks"].values():
        for st, ch in cc.items():
            arm = st.rsplit("_s", 1)[0]
            dev[arm] = max(dev.get(arm, 0.0), *(ch[k] for k in ("disp_rel_l2_median_rel_dev",
                                                              "energy_gap_rel_median_rel_dev")))
    if any(v for a, v in dev.items() if a != "mgn") or not 0 < dev["mgn"] <= 1e-3:
        raise SystemExit(f"holdout: the content checks are not those the text states: {dev}")
    N.put("numHoldContentDev", _sci(dev["mgn"], 1))
    N.put("numHoldStates", words(sum(len(cc) for cc in vho["content_checks"].values())))
    if t2["vm_higher_share_pooled"] != 1.0:
        raise SystemExit("holdout T2: the text says every pair had the higher von Mises error")
    N.put("numHoldVAlpha", pct(V["alpha"], 0))
    # the predictions and load cases worse than the zero field on the held-out instances of
    # two dimensions (Sec. 6, reported without a verdict), recomputed from the arrays; on the
    # validation instances no transformer had such a prediction (Section 6.1)
    sh = vho["secondary"]["h2d"]["holdout"]
    rows2 = [str(r) for r in z["h2d"]["rows"]]
    for row, R in (("ar", "Free"), ("labels", "Lab"), ("labels_knorm", "Knorm"), ("mgn", "Mgn")):
        inst = int((_arrays_values(z["h2d"], row, "energy_gap_rel") > 1).sum())
        g_, pi_ = z["h2d"]["gap_load"][rows2.index(row)], z["h2d"]["pi_load"][rows2.index(row)]
        loads = int((g_ > 1).sum())
        w = sh["worse_than_zero"][row]["all_seeds"]
        if not (inst == sh["mean_gap_above_one"][row]["total"] and loads == w["worse"]
                and w["sign_mismatch"] == 0 and bool(((pi_ > 0) == (g_ > 1)).all())):
            raise SystemExit(f"holdout h2d {row}: the predictions worse than the zero field are "
                             "not the verdict's")
        N.put(f"numHoldTwoWorseInst{R}", f"{inst:,}" if inst else "none")
        N.put(f"numHoldTwoWorseLoad{R}", f"{loads:,}")
    N.put("numHoldTwoPairs", f"{sh['mean_gap_above_one']['ar']['pairs']:,}")
    N.put("numHoldTwoLoads", f"{sh['worse_than_zero']['ar']['all_seeds']['load_cases']:,}")
    sv = vho["secondary"]["h2d"]["validation"]["mean_gap_above_one"]
    if any(sv[r]["total"] for r in ("ar", "labels", "labels_knorm")) or \
            sh["mean_gap_above_one"]["ar"]["total"]:
        raise SystemExit("holdout: the text says no transformer had a prediction worse than the "
                         "zero field on the validation instances, nor the label-free one held out")
    N.put("numHoldTTwoMin", pct(min(t2["disp_lower_share_per_seed"])))
    N.put("numHoldTTwoMax", pct(max(t2["disp_lower_share_per_seed"])))
    # the means and medians beside the validation ones (Sec. 5), every quantity of V
    vhead = ["Network", "Metric", "Validation:\nmean / median", "Holdout:\nmean / median",
             "Ratio of the\nmeans (95%)"]
    vrows, vrules = [], []
    short = dict(zip(METRICS, ("Displacement", "Energy gap", "von Mises", "Peak stress",
                               "Recall"), strict=True))
    nets = {"ar": "Label-free", "labels": "Supervised, displacement",
            "labels_knorm": "Supervised, energy norm",
            "mgn": "Graph network"}
    for s_, S in (("h3d", "Three dimensions"), ("h2d", "Two dimensions")):
        if vrows:
            vrules.append(len(vrows))
        n_h = V["quantities"][f"{s_}:ar:disp_rel_l2"]["n_holdout"]
        vrows.append([f"{S}, {n_h:,} held-out instances"])
        for row in ("ar", "labels", "labels_knorm", "mgn"):
            for i, m in enumerate(METRICS):
                key = f"{s_}:{row}:{m}"
                if key not in V["quantities"]:
                    continue
                x = V["quantities"][key]
                r_ = vho["secondary"][s_]["ratio_interval"][row][m]
                vrows.append([nets[row] if i == 0 else "", short[m],
                              f"{num(x['validation_mean'])} / {num(x['validation_median'])}",
                              f"{num(x['holdout_mean'])} / {num(x['holdout_median'])}",
                              f"{r_['ratio']:.2f} ({r_['interval_95_holdout'][0]:.2f}–"
                              f"{r_['interval_95_holdout'][1]:.2f})"])
    vnotes = [
        "Per network and metric, the mean and the median over the instances of each "
        "instance's value averaged over the seeds; the validation values recomputed by the "
        "holdout evaluation, whose check of the reports' displacement errors and relative "
        "energy gaps they passed (the graph networks' to within "
        f"{_sci(max(ch[k] for cc in vho['content_checks'].values() for ch in cc.values() for k in ('disp_rel_l2_median_rel_dev', 'energy_gap_rel_median_rel_dev')), 1)} "
        "in the median). Ratio: holdout mean over validation mean, with a 95% percentile "
        "interval from 2,000 resamplings of the holdout instances. V's two-sided "
        "Mann–Whitney tests compare the per-instance values; Holm's procedure rejected none "
        f"of their p-values, which the evaluation's verdict records, at a family-wise level of "
        f"{pct(V['alpha'], 0)}. The energy-norm-supervised transformer was "
        "evaluated in 2D only: its 3D counterpart was trained after this evaluation "
        r"(\cref{sec:norm:three})."]
    return (head, rows, notes), (vhead, vrows, vnotes, tuple(vrules))


# ---------------------------------------------------------------- Ritz baseline (post hoc)
RITZ_SETS = ("val3d", "fine3d", "h3d", "val2d", "h2d")
RITZ_LADDER = {3: (6, 7, 8, 9), 2: (6, 8)}
RITZ_DETERMINISTIC = ("zero", "scale_aware_poly", "knn_field")


def ritz_summaries(used: dict) -> dict:
    """The Ritz baseline's summaries (scripts/ritz_baseline.py; the per-instance rows that
    they summarise are in the committed return, and tests/test_ritz_return.py rebuilds the
    summaries from them byte for byte). Refuses a set with an instance that failed its
    identity check, a dropped direction, or a load case worse than the zero field."""
    out = {}
    for s in RITZ_SETS:
        d = load(RITZ / "baseline" / s / "summary.json", used)
        dim = 3 if s.endswith("3d") else 2
        if (d["n_used"] != d["n"] or d["identity_failed"] or d["size_mismatch"]
                or d["cut"] != 1e-13 or tuple(d["ladder_p"]) != RITZ_LADDER[dim]
                or d["spec"] != "Appendix 1, fixed 20 October 2026 (post hoc)"):
            raise SystemExit(f"Ritz {s}: the summary is not the specification's")
        for p, lad in d["ladder"].items():
            w = lad["worse_than_zero"]
            if (lad["dropped_max"] or lad["dropped_instances"] or w["worse"]
                    or w["sign_mismatch"] or w["instances_mean_gap_above_one"]):
                raise SystemExit(f"Ritz {s} p = {p}: a direction dropped or a load case "
                                 "worse than the zero field")
            if lad["k"] != dim * len([1 for a in range(int(p)) for b in range(int(p) - a)
                                      for c_ in (range(int(p) - a - b) if dim == 3 else [0])]):
                raise SystemExit(f"Ritz {s} p = {p}: not the specification's unknowns")
        out[s] = d
    return out


def _ritz_better(d: dict, model: str, p: int, metric: str) -> list:
    return [float(e[metric]["ritz_better_share"]) for e in d["ladder"][str(p)]["paired"][model]]


def _net_better(d: dict, model: str, p: int, metric: str) -> list:
    """Per seed, the share of the instances on which the network is strictly better."""
    return [1 - float(e[metric]["ritz_better_share"]) - e[metric]["ties"] / e[metric]["n"]
            for e in d["ladder"][str(p)]["paired"][model]]


def _trained(d: dict) -> list:
    return [m for m in d["ladder"][str(d["ladder_p"][0])]["paired"]
            if m.split(":")[1].split("@")[0].split(" ")[0] not in RITZ_DETERMINISTIC]


def ritz_rows(d: dict, worse: bool = True) -> list:
    """The Ritz projection's rows of an accuracy table: the instance means of the five
    metrics per p (each instance's value the mean over its load cases), deterministic."""
    rows = []
    for p in d["ladder_p"]:
        lad = d["ladder"][str(p)]
        row = [f"Ritz projection, $p = {p}$"] + [num(lad["mean"][m]) for m in METRICS]
        if worse:
            row.append(f"{lad['worse_than_zero']['instances_mean_gap_above_one']:,}/{d['n']:,}")
        rows.append(row)
    return rows


RITZ_TABLE_MODELS = {
    "val3d": ("phase2b:ar@1024", "phase2b:labels@1024", "phase2b:labels_anchor@1024",
              "k3d:labels_knorm@1024", "phase2b:mgn@1024", "e2_m512:ar@1024",
              "e2_m1024:ar@1024", "phase2b:knn_field@1024", "phase2b:scale_aware_poly@1024",
              "phase2b:zero@1024"),
    "h3d": None, "val2d": ("cm2d:ar@1024", "cm2d:labels@1024", "cm2d:labels_knorm@1024",
                           "cm2d:mgn@1024", "cm2d:knn_field@1024",
                           "cm2d:scale_aware_poly@1024", "cm2d:zero@1024"),
    "h2d": None, "fine3d": None}
RITZ_MODEL_NAMES = {"ar": "Label-free", "labels": "Supervised, displacement",
                    "labels_anchor": "Supervised, displacement + "
                    "energy term", "labels_knorm": "Supervised, energy norm",
                    "mgn": "Graph network, displacement",
                    "knn_field": "Nearest-neighbour field",
                    "scale_aware_poly": "Scaled polynomial", "zero": "Zero field"}
RITZ_SET_NAMES = {"val3d": "3D, validation", "h3d": "3D, holdout", "fine3d": "3D, finer mesh",
                  "val2d": "2D, validation", "h2d": "2D, holdout"}


def _model_name(label: str) -> str:
    tag, rest = label.split(":", 1)
    if tag in ("e2_m512", "e2_m1024"):
        base = f"Token bottleneck, M = {int(tag.split('_m')[1]):,}"
    else:
        arm = rest.split("@")[0].split(" ")[0]
        base = RITZ_MODEL_NAMES.get(arm, {"finetune": "Label-free, then fine-mesh labels",
                                          "scratch": "Supervised from scratch, fine-mesh "
                                          "labels"}.get(arm, arm))
    if "@" in rest and rest.split("@")[1].split(" ")[0] not in ("1024", "max"):
        base += f", {rest.split('@')[1].split(' ')[0]} labels"
    if "zero-shot" in rest:
        base += ", zero-shot"
    return base


def ritz_material(N: Numbers, R: dict) -> tuple:
    """The Ritz baseline's rows of the accuracy tables, the paired shares the text quotes
    (every statement it makes about them checked here), and the table of the shares for
    the supplementary material."""
    v3, f3, h3, v2, h2 = (R[s] for s in RITZ_SETS)
    N.put("numRitzThreeK", and_list(f"{v3['ladder'][str(p)]['k']:,}" for p in v3["ladder_p"]))
    N.put("numRitzTwoK", and_list(f"{v2['ladder'][str(p)]['k']:,}" for p in v2["ladder_p"]))
    N.put("numRitzThreeKMax", f"{v3['ladder'][str(v3['ladder_p'][-1])]['k']:,}")
    N.put("numRitzTwoKSix", f"{v2['ladder']['6']['k']:,}")
    N.put("numRitzTwoKEight", f"{v2['ladder']['8']['k']:,}")
    free3, free2 = "phase2b:ar@1024", "cm2d:ar@1024"
    # 3D validation: the label-free transformer
    for p, P in ((6, "Six"), (9, "Nine")):
        x = _ritz_better(v3, free3, p, "disp_rel_l2")
        N.put(f"numRitzValFreeDisp{P}Min", upct(min(x)))
        N.put(f"numRitzValFreeDisp{P}Max", upct(max(x)))
        x = _ritz_better(h3, _h3_free(h3), p, "disp_rel_l2")
        N.put(f"numRitzHoldFreeDisp{P}Min", upct(min(x)))
        N.put(f"numRitzHoldFreeDisp{P}Max", upct(max(x)))
        N.put(f"numRitzValGap{P}", num(v3["ladder"][str(p)]["median"]["energy_gap_rel"], 2))
        N.put(f"numRitzValPeak{P}", num(v3["ladder"][str(p)]["median"]["peak_vm_rel_err"], 2))
        N.put(f"numRitzFineGap{P}", num(f3["ladder"][str(p)]["median"]["energy_gap_rel"], 2))
    if not all(min(_ritz_better(v3, free3, p, "disp_rel_l2")) > 0.5 for p in v3["ladder_p"]):
        raise SystemExit("Ritz: the text says its displacement error is the smaller on most "
                         "instances at every degree")
    ratios = [v3["ladder"][str(p)]["median"]["peak_vm_rel_err"] / e["peak_vm_rel_err"]
              ["model_median"] for p in v3["ladder_p"]
              for e in v3["ladder"][str(p)]["paired"][free3]]
    top = str(max(v3["ladder_p"]))
    if not min(v3["ladder"][top]["median"]["peak_vm_rel_err"] / e["peak_vm_rel_err"]
               ["model_median"] for e in v3["ladder"][top]["paired"][free3]) > 2:
        raise SystemExit("Ritz: the abstract says that at the top of its ladder its median peak "
                         "stress error is more than twice the label-free transformer's, in "
                         "each seed")
    N.put("numRitzValPeakRatioMin", f"{min(ratios):.1f}")
    N.put("numRitzValPeakRatioMax", f"{max(ratios):.1f}")
    peak_net = [s for p in v3["ladder_p"] for s in _net_better(v3, free3, p, "peak_vm_rel_err")]
    N.put("numRitzValFreePeakMin", at_least(min(peak_net)))
    hold_peak = [s for p in h3["ladder_p"]
                 for s in _net_better(h3, _h3_free(h3), p, "peak_vm_rel_err")]
    N.put("numRitzHoldFreePeakMin", at_least(min(hold_peak)))
    nets3 = _trained(v3)
    disp9 = [s for m in nets3 for s in _ritz_better(v3, m, 9, "disp_rel_l2")]
    N.put("numRitzValNineDispAll", at_least(min(disp9)))
    kn = "k3d:labels_knorm@1024"
    kn_gap = [s for p in v3["ladder_p"] for s in _net_better(v3, kn, p, "energy_gap_rel")]
    N.put("numRitzValKnormGapMin", at_least(min(kn_gap)))
    hk_gap = [s for p in h3["ladder_p"] for s in _net_better(h3, kn.split("@")[0], p,
                                                               "energy_gap_rel")]
    N.put("numRitzHoldKnormGapMin", at_least(min(hk_gap)))
    miss = max(round((1 - s) * h3["n"]) for p in h3["ladder_p"]
               for s in _net_better(h3, kn.split("@")[0], p, "peak_vm_rel_err"))
    if not 0 < miss <= 10:
        raise SystemExit("Ritz: the text says the energy-norm-supervised transformer's peak error was the "
                         "lower on all but a few held-out instances")
    N.put("numRitzHoldKnormPeakMiss", words(miss))
    kn_peak = [s for p in v3["ladder_p"] for s in _net_better(v3, kn, p, "peak_vm_rel_err")]
    if min(kn_peak) != 1.0:
        raise SystemExit("Ritz: the text says the energy-norm-supervised transformer had the lower peak "
                         "von Mises error on every validation instance at every degree")
    # the medians of the label-free transformer's gap: comparable at the top of the ladder
    fm = [e["energy_gap_rel"]["model_median"] for e in v3["ladder"]["9"]["paired"][free3]]
    if not min(fm) <= v3["ladder"]["9"]["median"]["energy_gap_rel"] <= max(fm):
        raise SystemExit("Ritz: its median energy gap at p = 9 is not within the label-free "
                         "transformer's seeds")
    # 2D validation
    d2 = [s for p in v2["ladder_p"] for s in _ritz_better(v2, free2, p, "disp_rel_l2")]
    N.put("numRitzTwoFreeDispMin", upct(min(d2)))
    N.put("numRitzTwoFreeDispMax", upct(max(d2)))
    for p, P in ((6, "Six"), (8, "Eight")):
        x = _ritz_better(v2, free2, p, "energy_gap_rel")
        N.put(f"numRitzTwoFreeGap{P}Min", upct(min(x)))
        N.put(f"numRitzTwoFreeGap{P}Max", upct(max(x)))
    p2 = [s for p in v2["ladder_p"] for s in _net_better(v2, free2, p, "peak_vm_rel_err")]
    N.put("numRitzTwoFreePeakMin", at_least(min(p2)))
    # the finer mesh: every network, the fine-tuned ones included
    nets_f = _trained(f3)
    gap_f = [s for m in nets_f for p in f3["ladder_p"]
             for s in _ritz_better(f3, m, p, "energy_gap_rel")]
    N.put("numRitzFineGapAll", at_least(min(gap_f)))

    def peak_range(models):
        x = [s for m in models for p in f3["ladder_p"]
             for s in _net_better(f3, m, p, "peak_vm_rel_err")]
        return min(x), max(x)

    # on the finer mesh its displacement, energy and von Mises errors stay close to their
    # in-band values and its peak stress error does not (the instance means of the tables)
    for p in f3["ladder_p"]:
        r_ = {m: f3["ladder"][str(p)]["mean"][m] / v3["ladder"][str(p)]["mean"][m]
              for m in ("disp_rel_l2", "energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err")}
        if not (max(r_["disp_rel_l2"], r_["energy_gap_rel"], r_["vm_rel_l2"]) < 1.2
                and r_["peak_vm_rel_err"] > 1.3):
            raise SystemExit(f"Ritz p = {p}: the fine mesh's errors are not those the text "
                             f"describes: {r_}")
    lo, hi = peak_range(["phase2b:ar (zero-shot)"])
    N.put("numRitzFineFreePeakMin", upct(lo))
    N.put("numRitzFineFreePeakMax", upct(hi))
    lo, hi = peak_range(["e2_m512:ar (zero-shot)", "e2_m1024:ar (zero-shot)"])
    N.put("numRitzFineBnPeakMin", upct(lo))
    N.put("numRitzFineBnPeakMax", upct(hi))
    lo, hi = peak_range(["phase2b:labels@max (zero-shot)"])
    N.put("numRitzFineLabPeakMax", at_most(hi))
    lo, hi = peak_range(["phase2b:mgn@max (zero-shot)"])
    if hi != 0:
        raise SystemExit("Ritz: the text says the graph network had the lower peak error on "
                         "no fine-mesh instance")
    lo, hi = peak_range(["phase2b:finetune@64"])
    N.put("numRitzFineFtPeakMin", upct(lo))
    N.put("numRitzFineFtPeakMax", upct(hi))
    # the supplementary table: the share of the instances on which the Ritz projection is
    # the more accurate, lowest to highest over the seeds, every network and baseline of the
    # accuracy tables, per set and degree
    head = ["Set", "Model", "$p$", "Displacement\nerror", "Relative\nenergy gap",
            "von Mises\nerror", "Peak stress\nerror", "Critical-region\nrecall"]
    rows, rules = [], []
    for s in RITZ_SETS:
        d = R[s]
        models = RITZ_TABLE_MODELS[s] or list(d["ladder"][str(d["ladder_p"][0])]["paired"])
        if rows:
            rules.append(len(rows))
        for i, m in enumerate(models):
            for j, p in enumerate(d["ladder_p"]):
                cells_ = []
                for f in METRICS:
                    x = _ritz_better(d, m, p, f)
                    lo_, hi_ = upct(min(x)), upct(max(x))
                    cells_.append(lo_ if lo_ == hi_ else f"{lo_}–{hi_}")
                rows.append([RITZ_SET_NAMES[s] if (i == 0 and j == 0) else "",
                             _model_name(m) if j == 0 else "", str(p)] + cells_)
    notes = [
        "The share of the instances on which the Ritz projection was strictly the more "
        "accurate than the model, for each seed of a trained network (the lowest and the "
        "highest over the three seeds; one value when they agree), and for the deterministic "
        "baselines. Higher is better in critical-region recall, lower in every other metric; "
        "ties, which occur only in critical-region recall, are counted with neither. A share "
        "strictly between 0% and 100% is never shown as either. Networks at 1,024 labelled "
        "instances; on the finer mesh the networks trained in-band are applied zero-shot and "
        "the few-shot networks are those of the transfer comparison. The shares for every "
        "other network and budget of the summaries are in the records."]
    return {"val3d": ritz_rows(v3), "val2d": ritz_rows(v2), "fine3d": ritz_rows(f3, worse=False),
            "pairs": (head, rows, notes, tuple(rules))}


def ritz_versus_networks(R: dict, r3: dict, rcm: dict, k: dict) -> None:
    """The text's reading of the accuracy tables: at the top of its ladder the Ritz
    projection beat the label-free transformer's seed means on every metric but the peak
    stress error, in both dimensions, and the energy-norm-supervised transformer beat it in
    relative energy gap, von Mises error and peak stress error and lost in displacement error
    and critical-region recall."""
    better = {m: (lambda a, b: a > b) if m == "crit_recall" else (lambda a, b: a < b)
              for m in METRICS}
    for s_, rep_free, rep_kn in (("val3d", r3, k), ("val2d", rcm, rcm)):
        top = R[s_]["ladder"][str(R[s_]["ladder_p"][-1])]["mean"]
        ritz_wins = {m for m in METRICS if better[m](top[m], seed_mean(rep_free, "ar", m))}
        if ritz_wins != set(METRICS) - {"peak_vm_rel_err"}:
            raise SystemExit(f"Ritz {s_}: the text says the top of the ladder beat the label-free "
                             "transformer on every metric but the peak stress error")
        kn_wins = {m for m in METRICS if better[m](seed_mean(rep_kn, "labels_knorm", m), top[m])}
        if kn_wins != {"energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err"}:
            raise SystemExit(f"Ritz {s_}: the text says the energy-norm-supervised transformer "
                             "beat the top of the ladder in energy gap, von Mises and peak "
                             "stress error only")


def _h3_free(h3: dict) -> str:
    """The holdout set's label for the label-free transformer."""
    ms_ = [m for m in h3["ladder"][str(h3["ladder_p"][0])]["paired"]
           if m.split(":")[1].startswith("ar")]
    if len(ms_) != 1:
        raise SystemExit(f"Ritz h3d: not one label-free row: {ms_}")
    return ms_[0]


def _params_transformer(f: int, sd: int, D: int = 256, depth: int = 8) -> tuple:
    """Parameters of models/fejepa.py: (encoder + decoder, auxiliary heads), by formula
    (checked against the torch modules in tests/test_cmame_material.py)."""
    enc = f * D + D + depth * (12 * D * D + 13 * D) + 2 * D
    dec = (4 * D * D + 2 * D) + (2 * D * D + D) + (D * sd + sd)
    aux = (f * D + 7 * D * D + 10 * D) + (2 * D * D + 2 * D)
    return enc + dec, aux


def _params_graph(f: int, sd: int, D: int = 256, depth: int = 8) -> int:
    """Parameters of models/gnn.py, by formula (checked against torch in the tests)."""
    mlp = lambda i: i * D + D * D + 4 * D                                       # noqa: E731
    return mlp(f) + mlp(sd + 1) + depth * (mlp(2 * D) + mlp(3 * D)) + (D * D + D + D * sd + sd)


def extra_numbers(N: Numbers, r2: dict, r3: dict, amps: dict) -> None:
    """Mesh sizes, network sizes, paired per-instance comparisons and the residual-test
    bracket of Section 3.6."""
    A = amps["transformer"]["seeds"]
    s0 = A[sorted(A)[0]]
    nin = np.array([r["n_nodes"] for r in s0["inband"]["per_instance"]])
    nfi = np.array([r["n_nodes"] for r in s0["fine"]["per_instance"]])
    N.put("numNodesInMin", f"{nin.min():,}")
    N.put("numNodesInMax", f"{nin.max():,}")
    N.put("numNodesInMedian", f"{int(np.median(nin)):,}")
    N.put("numNodesFineMin", f"{nfi.min():,}")
    N.put("numNodesFineMax", f"{nfi.max():,}")
    N.put("numNodesFineMedian", f"{int(np.median(nfi)):,}")
    used, aux = _params_transformer(f=20, sd=3)
    N.put("numParamsTransformer", f"{used / 1e6:.1f}")
    N.put("numParamsAux", f"{aux / 1e6:.1f}")
    N.put("numParamsGraph", f"{_params_graph(f=20, sd=3) / 1e6:.1f}")
    for dim, rep in (("Two", r2), ("Three", r3)):
        for arm, A_ in (("labels", "Lab"), ("labels_anchor", "Anc")):
            for m, M in (("disp_rel_l2", "Disp"), ("energy_gap_rel", "Gap"),
                         ("vm_rel_l2", "Vm"), ("peak_vm_rel_err", "Peak"),
                         ("crit_recall", "Recall")):
                a, b = per_instance(rep, "ar", m), per_instance(rep, arm, m)
                win = (a > b) if m == "crit_recall" else (a < b)
                N.put(f"numPair{dim}{A_}{M}", share(win))
    # Section 5.1, read after the run: the noise guard of the two-dimensional comparison
    # (Table A.1; the three-dimensional pre-registration fixed none) applied to the
    # label-free transformer against the two displacement-supervised transformers on the five
    # metrics; the text names the differences that lie within it
    within, total = [], 0
    for arm in ("labels", "labels_anchor"):
        for m in METRICS:
            a, b = (np.asarray(seed_values(r3, x, "1024", m), float) for x in ("ar", arm))
            rel = a.mean() / b.mean() - 1
            se = np.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size) / b.mean()
            total += 1
            if abs(rel) <= max(0.1, 2 * se):
                within.append((arm, m))
    if within != [("labels", "energy_gap_rel"), ("labels", "peak_vm_rel_err"),
                  ("labels_anchor", "crit_recall")]:
        raise SystemExit(f"3D: the differences within the noise guard are not the text's: "
                         f"{within}")
    N.put("numThreeGuardWithin", words(len(within)))
    N.put("numThreeGuardTotal", words(total))
    w2 = r2["results"]["wp6"]["metrics"]["conditioning"]["kappa_range"]
    tol = r2["results"]["e7"]["protocol"]["tol"]
    N.put("numKappaTauTwo", _sci(w2[1] * tol * tol, 2))
    N.put("numTauSqKappaTwo", _sci(tol * tol / w2[1], 1))
    N.put("numTauSquared", f"$10^{{{int(round(2 * log10(tol)))}}}$")


def numbers_tex(N: dict) -> str:
    out = [HEADER]
    for k in sorted(N):
        v = N[k]
        if v.startswith("$") and v.endswith("$") and v.count("$") == 2:
            body = rf"\ensuremath{{{v[1:-1]}}}"        # usable in text and in math
        else:
            body = tex(v)
        out.append(rf"\newcommand{{\{k}}}{{{body}}}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- figures
def _style():
    return {"font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK,
            "xtick.color": INK2, "ytick.color": INK2, "axes.linewidth": 0.8,
            "pdf.fonttype": 42, "legend.frameon": False}


def _axes(ax):
    ax.grid(True, which="major", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def _save(fig, out: Path, name: str) -> Path:
    p = out / f"{name}.pdf"
    fig.savefig(p, dpi=300, metadata={"CreationDate": None})
    return p


FIG_NAMES = {a: NAMES[a] for a in ("ar", "labels", "labels_anchor", "labels_knorm", "mgn")}
"""Legend names: the tables' row names."""
LEGEND_ORDER = ("ar", "labels_knorm", "labels_anchor", "labels", "mgn")


def _shared_legend(fig, axes, extra=()):
    """One legend for several panels: each series once, in LEGEND_ORDER."""
    seen = {}
    for ax in np.ravel(axes):
        for h, lab in zip(*ax.get_legend_handles_labels(), strict=True):
            seen.setdefault(lab, h)
    order = [FIG_NAMES[a] for a in LEGEND_ORDER] + list(extra)
    labs = [lab for lab in order if lab in seen] + [lab for lab in seen if lab not in order]
    return [seen[lab] for lab in labs], labs


def figures(r2: dict, r3: dict, k: dict, out: Path) -> list:
    """r2: the two-dimensional comparison (CM2D's report); r3: the three-dimensional run;
    k: the three-dimensional energy-norm run (its energy-norm-supervised transformer)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

    fmt = FuncFormatter(lambda v, _: f"{v:g}")
    written = []
    with plt.rc_context(_style()):
        # displacement error against von Mises error, per instance and seed (3D)
        fig, ax = plt.subplots(figsize=(4.6, 3.6), constrained_layout=True)
        for arm in ("labels", "mgn", "ar", "labels_knorm"):
            col, mk = STYLE[arm]
            rep = k if arm == "labels_knorm" else r3
            x = per_instance(rep, arm, "disp_rel_l2").ravel()
            y = per_instance(rep, arm, "vm_rel_l2").ravel()
            ax.scatter(x, y, s=10, marker=mk, color=col, alpha=0.5, linewidths=0,
                       label=FIG_NAMES[arm])
        ax.set_xscale("log")
        ax.set_yscale("log")
        for axis in (ax.xaxis, ax.yaxis):
            axis.set_major_formatter(fmt)
            axis.set_minor_formatter(NullFormatter())
        ax.set_xlabel("Relative displacement error (log scale)")
        ax.set_ylabel("Relative von Mises error (log scale)")
        _axes(ax)
        hh, ll = ax.get_legend_handles_labels()
        order = [ll.index(FIG_NAMES[a]) for a in LEGEND_ORDER if FIG_NAMES[a] in ll]
        leg = ax.legend([hh[i] for i in order], [ll[i] for i in order], loc="upper left",
                        fontsize=7, markerscale=1.8, handletextpad=0.3)
        for h in leg.legend_handles:
            h.set_alpha(1)
        written.append(_save(fig, out, "fig_disp_vs_stress"))
        plt.close(fig)

        # distribution of the relative energy gap, 3D and 2D
        fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.3), constrained_layout=True, sharey=True)
        for ax, (title, rep) in zip(axes, (("Three dimensions", r3), ("Two dimensions", r2)),
                                    strict=True):
            for arm in ("ar", "labels_knorm", "labels_anchor", "labels", "mgn"):
                src = k if (rep is r3 and arm == "labels_knorm") else rep
                if arm not in cells(src):
                    continue
                col, mk = STYLE[arm]
                v = np.sort(per_instance(src, arm, "energy_gap_rel").ravel())
                y = np.arange(1, v.size + 1) / v.size
                ax.step(v, y, where="post", color=col, linewidth=1.5, label=FIG_NAMES[arm])
                i = (v.size - 1) // 2
                ax.plot([v[i]], [y[i]], marker=mk, color=col, markersize=5.5,
                        markeredgecolor="white", markeredgewidth=0.8, linestyle="none")
            ax.axvline(1.0, color=INK2, linestyle="--", linewidth=0.8)
            ax.text(1.15, 0.04, "zero field", rotation=90, fontsize=7, color=INK2, va="bottom")
            ax.set_xscale("log")
            ax.xaxis.set_major_locator(LogLocator(base=10, numticks=12))
            ax.xaxis.set_major_formatter(fmt)
            ax.xaxis.set_minor_formatter(NullFormatter())
            ax.set_title(title, fontsize=8, color=INK, loc="left")
            ax.set_xlabel("Relative energy gap (log scale)")
            _axes(ax)
        axes[0].set_ylabel("Fraction of instance-seed pairs at or below")
        h, lab = _shared_legend(fig, axes)
        fig.legend(h, lab, loc="outside lower center", ncol=2, fontsize=7, handlelength=1.8)
        written.append(_save(fig, out, "fig_energy_gap"))
        plt.close(fig)

        # label efficiency, 3D and 2D, displacement and energy gap
        fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.2), constrained_layout=True)
        xs = [int(bb) for bb in BUDGETS]
        for ci, (title, rep) in enumerate((("Three dimensions", r3), ("Two dimensions", r2))):
            for ri, (m, ylab) in enumerate((("disp_rel_l2", "Relative displacement error"),
                                            ("energy_gap_rel", "Relative energy gap"))):
                ax = axes[ri, ci]
                for arm in ("labels", "labels_knorm", "labels_anchor", "mgn"):
                    if arm not in cells(rep):
                        continue
                    col, mk = STYLE[arm]
                    c = cells(rep)[arm]
                    bx = [int(bb) for bb in BUDGETS if bb in c]
                    by = [seed_mean(rep, arm, m, str(bb)) for bb in bx]
                    ax.plot(bx, by, color=col, marker=mk, markersize=5, linewidth=1.4,
                            markeredgecolor="white", markeredgewidth=0.6, label=FIG_NAMES[arm])
                col, _ = STYLE["ar"]
                ax.axhline(seed_mean(rep, "ar", m), color=col, linewidth=1.6,
                           label="Label-free, no labels")
                ax.set_xscale("log")
                ax.set_yscale("log")
                ax.set_xticks(xs)
                ax.set_xticklabels([f"{x:,}" for x in xs])
                ax.minorticks_off()
                ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
                ax.yaxis.set_major_formatter(fmt)
                if ri == 0:
                    ax.set_title(title, fontsize=8, color=INK, loc="left")
                else:
                    ax.set_xlabel("Labelled training instances (log scale)")
                if ci == 0:
                    ax.set_ylabel(ylab + " (log scale)")
                _axes(ax)
        h, lab = _shared_legend(fig, axes, extra=("Label-free, no labels",))
        fig.legend(h, lab, loc="outside lower center", ncol=2, fontsize=7)
        written.append(_save(fig, out, "fig_label_efficiency"))
        plt.close(fig)
    return written


def fig_norm_labels(nl: dict, out: Path) -> Path:
    """Fig. 1: the same transformer trained on the solutions with the displacement loss, on
    the solutions in the energy norm, and on the energy without solutions, in three and two
    dimensions; each cell gives the median over the validation instances of the relative
    energy-norm error E = g^(1/2) and of the von Mises error, averaged over the three seeds
    (norm_label_material). The fourth cell, a displacement loss without solutions, does not
    exist."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, Rectangle

    W, H, GX, GY = 1.25, 0.72, 0.42, 0.36
    X0, X1, Y0, Y1 = 0.0, W + GX, 0.0, H + GY
    name = {"labels": "supervised", "labels_knorm": "supervised", "ar": "label-free"}
    with plt.rc_context(_style()):
        fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0))
        for ax, (dim, title) in zip(axes, (("Three", "Three dimensions"),
                                           ("Cm", "Two dimensions")), strict=True):
            m = nl[dim]["med"]
            ax.set_xlim(-0.75, X1 + W + 0.05)
            ax.set_ylim(-0.42, Y1 + H + 0.30)
            ax.axis("off")

            def cell(x, y, arm):
                col, mk = STYLE[arm]
                ax.add_patch(Rectangle((x, y), W, H, facecolor="white", edgecolor=INK2,
                                       linewidth=0.8))
                ax.plot([x + 0.09], [y + H - 0.12], marker=mk, color=col, markersize=6,
                        markeredgecolor="white", markeredgewidth=0.6, linestyle="none")
                ax.text(x + 0.17, y + H - 0.12, name[arm], ha="left", va="center",
                        fontsize=7.5, color=col, fontweight="bold")
                ax.text(x + W / 2, y + 0.34, f"E  {num(m[arm]['E_med'])}", ha="center",
                        va="center", fontsize=7.5, color=INK)
                ax.text(x + W / 2, y + 0.15, f"vM  {num(m[arm]['Vm_med'])}", ha="center",
                        va="center", fontsize=7.5, color=INK)

            cell(X0, Y1, "labels")
            cell(X0, Y0, "labels_knorm")
            cell(X1, Y0, "ar")
            ax.add_patch(Rectangle((X1, Y1), W, H, facecolor="#f3f2ef", edgecolor=INK2,
                                   linewidth=0.8, hatch="////"))
            ax.text(X1 + W / 2, Y1 + H / 2, "not possible: a\ndisplacement loss\nneeds the "
                    "solutions", ha="center", va="center", fontsize=6.8, color=INK2,
                    bbox={"facecolor": "#f3f2ef", "edgecolor": "none", "pad": 1.2})
            ax.text(X0 + W / 2, Y1 + H + 0.06, "with solutions", ha="center", fontsize=7.5,
                    color=INK)
            ax.text(X1 + W / 2, Y1 + H + 0.06, "without solutions", ha="center", fontsize=7.5,
                    color=INK)
            ax.text(-0.08, Y1 + H / 2, "displacement\nloss", ha="right", va="center",
                    fontsize=7.5, color=INK)
            ax.text(-0.08, Y0 + H / 2, "energy-norm\nloss", ha="right", va="center",
                    fontsize=7.5, color=INK)
            ax.text(-0.73, Y1 + H + 0.24, title, ha="left", fontsize=8.5, color=INK,
                    fontweight="bold")
            rn = {q: m["labels"][f"{q}_med"] / m["labels_knorm"][f"{q}_med"] for q in ("E", "Vm")}
            rl = {q: m["ar"][f"{q}_med"] / m["labels_knorm"][f"{q}_med"] for q in ("E", "Vm")}
            ax.add_patch(FancyArrowPatch((X0 + W / 2, Y1 - 0.02), (X0 + W / 2, Y0 + H + 0.02),
                                         arrowstyle="-|>", mutation_scale=9, color=INK,
                                         linewidth=1.0))
            ax.text(X0 + W / 2 + 0.06, (Y1 + Y0 + H) / 2,
                    f"change the norm: E \u00f7{rn['E']:.1f}, vM \u00f7{rn['Vm']:.1f}", ha="left",
                    va="center", fontsize=7, color=INK)
            ax.add_patch(FancyArrowPatch((X0 + W + 0.02, Y0 + H / 2), (X1 - 0.02, Y0 + H / 2),
                                         arrowstyle="-|>", mutation_scale=9, color=INK2,
                                         linewidth=0.9))
            ax.text(X0 + W + GX / 2, Y0 - 0.17,
                    f"remove the solutions: E \u00d7{rl['E']:.2f}, vM \u00d7{rl['Vm']:.2f}",
                    ha="center", va="center", fontsize=7, color=INK2)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02, wspace=0.05)
        p_ = _save(fig, out, "fig_norm_labels")
        plt.close(fig)
    return p_


def fig_e2(e2: dict, out: Path) -> Path:
    """The wp8 cost/accuracy figure of E2 with this manuscript's names (same data,
    same layout as scripts/make_wp8_paper_material.py)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FixedLocator, FuncFormatter, LogLocator, NullFormatter

    pal = {None: "#2a78d6", 512: "#eb6834", 1024: "#1baf7a"}
    mk = {None: "o", 512: "s", 1024: "^"}
    with plt.rc_context(_style()):
        fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), constrained_layout=True)
        n = e2["nodes"]
        panels = (("inband_0", "egap", f"In-band ({n['inband_0']:,}-node step)",
                   "Relative energy gap (log scale)", True, (10, 1e4)),
                  ("fine", "fine_disp", f"Finer mesh, zero-shot ({n['fine']:,}-node step)",
                   "Relative displacement error", False, (10, 1e5)))
        place = {("inband_0", 512): (0.30, 0.86), ("inband_0", 1024): (0.30, 0.50),
                 ("fine", 512): (0.25, 0.47), ("fine", 1024): (0.25, 0.90)}
        for ax, (ph, metric, title, ylab, logy, xlim) in zip(axes, panels, strict=True):
            for key, _label, m in W.E2_ARCHS:
                a = e2["archs"][key]
                name = "Label-free transformer" if m is None else f"Token bottleneck, M = {m:,}"
                x, ys = a["step_ms"][ph], a[metric]
                ax.scatter([x] * len(ys), ys, s=16, marker=mk[m], color=pal[m], alpha=0.45,
                           linewidths=0, zorder=2)
                ax.scatter([x], [statistics.fmean(ys)], s=56, marker=mk[m], color=pal[m],
                           edgecolors="white", linewidths=1.5, zorder=3, label=name)
                if m is None:
                    ax.annotate(name, (x, statistics.fmean(ys)), xytext=(-9, 0),
                                textcoords="offset points", fontsize=7, color=INK,
                                va="center", ha="right")
                else:
                    ax.annotate(name, (x, statistics.fmean(ys)), xytext=place[(ph, m)],
                                textcoords="axes fraction", fontsize=7, color=INK,
                                va="center", ha="left",
                                arrowprops={"arrowstyle": "-", "color": INK2,
                                            "linewidth": 0.6, "shrinkA": 2, "shrinkB": 5})
            ax.set_xscale("log")
            ax.set_xlim(*xlim)
            if logy:
                ax.set_yscale("log")
                ax.set_ylim(0.005, 0.1)
                ax.yaxis.set_major_locator(FixedLocator([0.005, 0.01, 0.02, 0.05, 0.1]))
                ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
                ax.yaxis.set_minor_formatter(NullFormatter())
            else:
                ax.set_ylim(0, 0.7)
            ax.set_title(title, fontsize=8, color=INK, loc="left")
            ax.set_xlabel("Label-free training step (ms, log scale)")
            ax.set_ylabel(ylab)
            _axes(ax)
            ax.xaxis.set_major_locator(LogLocator(base=10))
            ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
            ax.xaxis.set_minor_formatter(NullFormatter())
        axes[1].legend(loc="lower left", fontsize=7, handletextpad=0.3, borderaxespad=0.2)
        p = _save(fig, out, "fig_e2_cost_accuracy")
        plt.close(fig)
    return p


# ---------------------------------------------------------------- post-hoc figures
SPEC_ORDER = ("mgn", "labels", "labels_knorm", "ar")      # drawing order, roughest first


def fig_spectra(z: dict, out: Path) -> Path:
    """Two dimensions, 1,024 labels (post hoc): (a) per load case, the normalised
    Rayleigh quotient rho against the relative displacement error delta, with lines
    of equal relative energy gap g = rho delta^2; (b) the median share of the error's
    squared stiffness norm in the modes at or above lambda / R(U*)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import LogLocator, NullFormatter

    A = spectral_arrays(z)
    ix = {r: i for i, r in enumerate(A["rows"])}
    with plt.rc_context(_style()):
        fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.3), constrained_layout=True)
        ax = axes[0]
        for r in SPEC_ORDER:
            col, mk = STYLE[r]
            ax.scatter(np.sqrt(A["d2"][ix[r]]).ravel(), A["rho"][ix[r]].ravel(), s=2.5,
                       color=col, alpha=0.16, linewidths=0, rasterized=True, zorder=2)
        for r in SPEC_ORDER:
            col, mk = STYLE[r]
            ax.plot([np.sqrt(np.nanmedian(A["d2"][ix[r]]))], [np.nanmedian(A["rho"][ix[r]])],
                    marker=mk, color=col, markersize=8, markeredgecolor="white",
                    markeredgewidth=1.0, linestyle="none", zorder=4, label=FIG_NAMES[r])
        xlim, ylim = (6e-4, 2.0), (0.15, 3e4)
        xs = np.logspace(np.log10(xlim[0]), np.log10(xlim[1]), 200)
        for gv, txt in ((1e-3, "0.001"), (1e-2, "0.01"), (1e-1, "0.1"), (1.0, "1")):
            ax.plot(xs, gv / xs ** 2, color=INK2, linewidth=0.6, linestyle="--", zorder=1)
            x0 = max(xlim[0], np.sqrt(gv / ylim[1])) * 1.35
            ax.text(x0, gv / x0 ** 2, f"$g={txt}$", fontsize=6.5, color=INK2, rotation=-38,
                    rotation_mode="anchor", ha="left", va="bottom", zorder=3)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_xlabel(r"Relative displacement error $\delta$ (log scale)")
        ax.set_ylabel(r"Normalised Rayleigh quotient $\rho$ (log scale)")
        ax.set_title("Per load case, with the medians", fontsize=8, color=INK, loc="left")
        _axes(ax)
        ax = axes[1]
        x = 10.0 ** SPEC_EDGES
        for r in ("ar", "labels_knorm", "labels", "mgn"):
            col, _ = STYLE[r]
            y = np.nanmedian(_tails(z["SK_log"][ix[r]]).reshape(-1, SPEC_EDGES.size + 1),
                             axis=0)[1:]
            ax.plot(x, y, color=col, linewidth=1.6, label=FIG_NAMES[r], zorder=3)
        y = np.nanmedian(_tails(z["SK_log_star"]).reshape(-1, SPEC_EDGES.size + 1), axis=0)[1:]
        ax.plot(x, y, color=INK2, linewidth=1.2, linestyle="--", label="Solution", zorder=2)
        ax.set_xscale("log")
        ax.set_xlim(0.1, 10 ** 5.5)
        ax.set_ylim(-0.02, 1.02)
        ax.xaxis.set_major_locator(LogLocator(base=10, numticks=8))
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_xlabel(r"$\lambda_m/R(U^\ast)$ (log scale)")
        ax.set_ylabel(r"Share of $\|e\|_K^2$ in modes at or above")
        ax.set_title("Median over load cases", fontsize=8, color=INK, loc="left")
        _axes(ax)
        h, lab = _shared_legend(fig, axes, extra=("Solution",))
        fig.legend(h, lab, loc="outside lower center", ncol=3, fontsize=7, handlelength=1.8)
        p = _save(fig, out, "fig_spectra")
        plt.close(fig)
    return p


def _sequential(colours):
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list("ramp", list(colours))


def _rel_disp(z: dict, key: str, j: int, c: float = 1.0) -> float:
    us = z["U_star"][j]
    return float(np.linalg.norm(c * z[key][j] - us) / np.linalg.norm(us))


SHORT = {"ar": "Label-free", "labels": "Supervised,\ndisplacement",
         "labels_knorm": "Supervised,\nenergy norm",
         "mgn": "Graph network"}


def _gap_line(d: float, g: float, pi: float) -> str:
    """A field panel's readings: the relative displacement error, the relative energy
    gap and the sign of the stored energy, which by Corollary "Zero-field test and
    ranking" is positive exactly when g > 1."""
    if (pi > 0) != (g > 1) or pi == 0:
        raise SystemExit("field plot: the sign of the energy disagrees with the energy gap")
    sign = r"$\Pi_h(u)>0$" if pi > 0 else r"$\Pi_h(u)<0$"
    return rf"$\delta={num(d)}$, $g={num(g)}$" + "\n" + sign


def fig_field2d(z: dict, out: Path) -> Path:
    """The 2D figure instance (seed 0): the von Mises stress of the reference solution
    and of the four networks on the load case FIELD_LOADS selects; the networks trained
    in the energy norm on the first row, those trained on the displacement error on
    the second."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.cm import ScalarMappable
    from matplotlib.colors import Normalize

    j = field_load("fig2d", z)
    cmap = _sequential(RAMP_VM)
    norm = Normalize(0.0, float(z["vm_ref"][j].max()))
    grid = ((("Reference", "vm_ref", None), (SHORT["ar"], "vm_ar", "ar"),
             (SHORT["labels_knorm"].replace("\n", " "), "vm_labels_knorm", "labels_knorm")),
            ((SHORT["labels"], "vm_labels", "labels"), (SHORT["mgn"], "vm_mgn", "mgn"), None))
    with plt.rc_context(_style()):
        fig, axes = plt.subplots(2, 3, figsize=(7.0, 3.55), constrained_layout=True)
        for row, panels in enumerate(grid):
            for col, panel in enumerate(panels):
                ax = axes[row, col]
                ax.axis("off")
                if panel is None:
                    cax = ax.inset_axes([0.08, 0.42, 0.84, 0.09])
                    cb = fig.colorbar(ScalarMappable(norm, cmap), cax=cax,
                                      orientation="horizontal", extend="max")
                    cb.set_label("von Mises stress", fontsize=7)
                    cb.ax.tick_params(labelsize=7)
                    continue
                name, key, r = panel
                ax.tripcolor(z["nodes"][:, 0], z["nodes"][:, 1], z["elements"],
                             facecolors=z[key][j], cmap=cmap, norm=norm, edgecolors="face",
                             linewidth=0.15, rasterized=True)
                ax.set_aspect("equal")
                sub = "\n\n" if r is None else "\n" + _gap_line(_rel_disp(z, f"U_{r}", j),
                                                                 float(z[f"rel_{r}"][j]),
                                                                 float(z[f"pi_{r}"][j]))
                ax.set_title(name + sub, fontsize=7, color=INK)
        p = _save(fig, out, "fig_field2d")
        plt.close(fig)
    return p


def _visible_faces(nodes: np.ndarray, tets: np.ndarray) -> dict:
    """The boundary triangles of a meshed box on its three faces visible in the cabinet
    projection (front z = max, top y = max, end x = max), with their tetrahedra."""
    faces = np.concatenate([tets[:, idx] for idx in ((0, 1, 2), (0, 1, 3), (0, 2, 3),
                                                     (1, 2, 3))])
    owner = np.tile(np.arange(tets.shape[0]), 4)
    _, inv, cnt = np.unique(np.sort(faces, axis=1), axis=0, return_inverse=True,
                            return_counts=True)
    b = cnt[inv.ravel()] == 1
    tri, own = faces[b], owner[b]
    lo, hi = nodes.min(axis=0), nodes.max(axis=0)
    tol = 1e-8 * float((hi - lo).max())
    out = {}
    for name, axis, val in (("front", 2, hi[2]), ("top", 1, hi[1]), ("end", 0, hi[0])):
        on = np.all(np.abs(nodes[tri][:, :, axis] - val) < tol, axis=1)
        out[name] = (tri[on], own[on])
    if any(v[0].size == 0 for v in out.values()):
        raise SystemExit("field plot: a visible face of the box has no boundary triangle")
    return {"faces": out, "lo": lo, "hi": hi}


def _cabinet(p: np.ndarray) -> np.ndarray:
    """Oblique (cabinet) projection of a right-handed frame seen from +z (x to the right,
    y up): depth, towards -z, recedes up and to the right."""
    c, a = 0.45, np.deg2rad(35.0)
    return np.stack([p[..., 0] - c * p[..., 2] * np.cos(a), p[..., 1] - c * p[..., 2] * np.sin(a)],
                    axis=-1)


def _draw_box(ax, nodes, vis, values, per: str, cmap, norm) -> None:
    from matplotlib.collections import PolyCollection

    for tri, own in vis["faces"].values():
        col = values[tri].mean(axis=1) if per == "node" else values[own]
        ax.add_collection(PolyCollection(_cabinet(nodes[tri]), array=col, cmap=cmap, norm=norm,
                                         edgecolors="face", linewidths=0.15, rasterized=True))
    (x0, y0, z0), (x1, y1, z1) = vis["lo"], vis["hi"]
    for poly in (((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)),
                 ((x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)),
                 ((x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1))):
        q = _cabinet(np.array(poly + (poly[0],), dtype=float))
        ax.plot(q[:, 0], q[:, 1], color=INK2, linewidth=0.5)
    ax.set_aspect("equal")
    ax.autoscale_view()
    ax.axis("off")


def fig_fields3d(figs: dict, out: Path) -> list:
    """The three-dimensional field plots (RUNBOOK_CMAME Sec. A's figure files), each on
    the load case FIELD_LOADS selects within its instance."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.cm import ScalarMappable
    from matplotlib.colors import Normalize

    names = (("Reference", None), ("Label-free", "ar"), ("Supervised, displacement", "labels"),
             ("Graph network, displacement", "mgn"))
    cd, cv = _sequential(RAMP_DISP), _sequential(RAMP_VM)
    written = []
    with plt.rc_context(_style()):
        for fig_key, name, rows in (("fig5", "fig_field_worst", ("disp", "vm")),
                                    ("fig6", "fig_field_median", ("vm",))):
            z = figs[fig_key]
            j = field_load(fig_key, z)
            vis = _visible_faces(z["nodes"], z["tets"])
            mag = {r: np.linalg.norm(z["U_star" if r is None else f"U_{r}"][j].reshape(-1, 3),
                                     axis=1) for _, r in names}
            vm = {r: z["vm_ref" if r is None else f"vm_{r}"][j] for _, r in names}
            fig, axes = plt.subplots(len(rows), 4, figsize=(7.0, 1.05 * len(rows) + 0.75),
                                     constrained_layout=True, squeeze=False)
            for i, q in enumerate(rows):
                vals, cmap, per = (mag, cd, "node") if q == "disp" else (vm, cv, "elem")
                norm = Normalize(0.0, float(vals[None].max()))
                for k, (title, r) in enumerate(names):
                    ax = axes[i, k]
                    _draw_box(ax, z["nodes"], vis, vals[r], per, cmap, norm)
                    if i == 0:
                        sub = "\n\n" if r is None else "\n" + _gap_line(
                            _rel_disp(z, f"U_{r}", j), float(z[f"rel_{r}"][j]),
                            float(z[f"pi_{r}"][j]))
                        ax.set_title(title + sub, fontsize=7, color=INK)
                cb = fig.colorbar(ScalarMappable(norm, cmap), ax=axes[i, :], location="right",
                                  shrink=0.9, aspect=12, extend="max", pad=0.01)
                cb.set_label("Displacement\nmagnitude" if q == "disp" else "von Mises\nstress",
                             fontsize=7)
                cb.ax.tick_params(labelsize=6.5)
            written.append(_save(fig, out, name))
            plt.close(fig)
        # the fine-mesh instance: the label-free prediction before and after the rescaling
        z = figs["fig7"]
        j = field_load("fig7", z)
        vis = _visible_faces(z["nodes"], z["tets"])
        c = float(z["c_ar"][j])
        fields = (("Reference", z["U_star"][j], None),
                  ("Label-free", z["U_ar"][j], _rel_disp(z, "U_ar", j)),
                  (r"Label-free, rescaled by $c^\ast$", c * z["U_ar"][j],
                   _rel_disp(z, "U_ar", j, c)))
        mags = [np.linalg.norm(u.reshape(-1, 3), axis=1) for _, u, _ in fields]
        norm = Normalize(0.0, float(mags[0].max()))
        fig, axes = plt.subplots(1, 3, figsize=(7.0, 1.95), constrained_layout=True)
        for ax, (title, _, d), m in zip(axes, fields, mags, strict=True):
            _draw_box(ax, z["nodes"], vis, m, "node", cd, norm)
            sub = "\n" if d is None else "\n" + rf"$\delta={num(d)}$"
            if "rescaled" in title:
                sub += rf", $c^\ast={num(c)}$"
            ax.set_title(title + sub, fontsize=7, color=INK)
        cb = fig.colorbar(ScalarMappable(norm, cd), ax=axes, location="right", shrink=0.9,
                          aspect=12, extend="max", pad=0.01)
        cb.set_label("Displacement\nmagnitude", fontsize=7)
        cb.ax.tick_params(labelsize=6.5)
        written.append(_save(fig, out, "fig_field_fine"))
        plt.close(fig)
    return written


# ---------------------------------------------------------------- main
CAP_2D = ("Two-dimensional plates, every metric at the largest label budget. The supervised "
          "networks were trained on 1,024 labelled instances; the label-free transformer on "
          "the same 1,024 instances without their solutions.")
CAP_2DJULY = (r"Two-dimensional plates, the July run with the earlier code: every metric at "
              r"the largest label budget, on the instances of \cref{tab:2d}.")
CAP_3D = ("Three-dimensional solids, every metric at the largest label budget. The supervised "
          "networks were trained on 1,024 labelled instances; the label-free transformer on "
          "the same 1,024 instances without their solutions.")
CAP_LE = ("Label efficiency: relative displacement error / relative energy gap against the "
          "number of labelled training instances (seed means).")
CAP_LEJULY = ("The July run (two dimensions, earlier code): relative displacement error / "
              "relative energy gap against the number of labelled training instances (seed "
              "means).")
CAP_TR = ("Three-dimensional solids on the finer mesh (lc = 0.0374), never trained on. "
          "Zero-shot rows use the networks trained in-band; few-shot rows train, with labels, "
          "on the first 16 or on all of the 64 fine-mesh instances reserved for few-shot "
          "training.")
CAP_CR = "Every pre-registered criterion of the runs reported here, with its outcome."
CAP_CL = ("The pre-registered claims of the comparisons reported in this paper, with the "
          "outcomes that the code recorded at the time.")
CAP_CM2D = ("The pre-registered hypotheses of the two-dimensional comparison, with 1,024 "
            "labelled instances, as its adjudicator recorded them, and the readings its "
            "pre-registration required beside each.")
CAP_AMP = ("Post hoc, three-dimensional: errors of the label-free networks before and after "
           "scaling each prediction by its energy-optimal amplitude c*, in-band and on the "
           "finer mesh (zero-shot).")
CAP_REM = ("Post hoc, three-dimensional: the energy-optimal amplitude c_b of the four load "
           "cases of an instance together, for the label-free networks, on fixed geometries "
           "and loads meshed at four mesh sizes lc.")
CAP_E2 = ("Token bottleneck against the label-free transformer, which has one token per "
          "node, both trained on the energy alone with the same corpus, split, seeds and "
          "schedule (three dimensions).")
CAP_COST = ("Time of the label-free transformer's inference against solves of the same "
            "systems, on the same instances, with the surrogate's accuracy there.")
CAP_E1 = ("Isotropic Gaussian regularisation of the latent vectors added to the label-free "
          r"objective (two dimensions, with the later code of \cref{sec:methods:networks}).")
CAP_K3D = ("The pre-registered hypotheses of the three-dimensional energy-norm run, with "
           "1,024 labelled instances, as its adjudicator recorded them, and the readings its "
           "pre-registration required beside each.")
CAP_HOLD = ("The claims of the three- and two-dimensional comparisons read again on held-out "
            "instances, as the adjudicator of the holdout evaluation recorded them, beside "
            "their values on the validation instances.")
CAP_HOLDV = ("Holdout evaluation: the mean and the median of every network and metric on the "
             "validation and on the held-out instances.")
CAP_RITZP = ("The Ritz projection paired with the networks and baselines: the share of the "
             "instances on which the projection was the more accurate, per set and degree $p$.")
CAP_KMED = ("Three-dimensional energy-norm run: every metric of the three transformers on "
            "the 256 validation instances, the seeds' medians and the seeds' means over the "
            "instances (mean ± sample standard deviation over the three seeds).")
CAP_KCMP = ("Three-dimensional energy-norm run: the 30 secondary comparisons, exploratory, "
            "each with the noise guard, on the seeds' medians and on the seeds' means.")


def build() -> dict:
    used: dict = {}
    r2, rd, r3 = load(R2D, used), load(RDIAG, used), load(R3D, used)
    rw = load(RWP2, used)
    amps = {k: load(p, used) for k, p in AMP.items()}
    e1base = load(E1_BASE, used)
    wused: dict = {}
    e1, e2 = W.read_e1(REC8, wused), W.read_e2(REC8, wused)
    ampw = W.read_amplitude(REC8, wused)
    probe_path = W.default_probe(REC8)
    probe = W._load(probe_path, wused) if probe_path else None
    if probe:
        W._check_probe(e1, probe)
    e1v = load(REC8 / "e1" / "e1_verdict.json", used)
    e2v = {m: load(REC8 / "e2" / f"e2_verdict_M{m}.json", used) for m in (512, 1024)}
    used.update(wused)
    rcm, vcm = load(RCM, used), load(VCM, used)
    sj, sz = load(SPEC / "spectra.json", used), load_npz(SPEC / "spectra_val.npz", used)
    fj, ez = load(FLD / "fields.json", used), load_npz(FLD / "energies_val.npz", used)
    figs = {"fig2d": load_npz(SPEC / "fig2d.npz", used),
            **{f: load_npz(FLD / f"{f}.npz", used) for f in ("fig5", "fig6", "fig7")}}

    N = numbers(r2, rd, r3, amps, e1base, rw, rcm)
    cm2d_numbers(N, rcm, vcm, r2)
    spectra_numbers(N, sj, sz, rcm)
    field_numbers(N, fj, ez)
    figure_numbers(N, figs)
    timing_numbers(N, e2, used)
    h_cost, r_cost, n_cost = cost_material(N, used)
    timing_rerun_numbers(N, used)
    rk, vk = load(RK3, used), load(VK3, used)
    k = as_e8(rk)
    (h_k3d, r_k3d, n_k3d), (h_kmed, r_kmed), (h_kcmp, r_kcmp) = k3d_material(N, k, vk, r3)
    nl = norm_label_material(N, k, rcm)
    vho = load(HOLD / "verdict.json", used)
    (h_ho, r_ho, n_ho), (h_hv, r_hv, n_hv, rules_hv) = holdout_material(N, vho, used, r3, rcm,
                                                                        vcm)
    R = ritz_summaries(used)
    rz = ritz_material(N, R)
    ritz_versus_networks(R, r3, rcm, k)
    dates = {"holdout": day_text(_starts(HOLD / "return" / "status.txt", used)[-1]),
             "k3d": day_text(rk["provenance"]["timestamp_utc"])}
    t = ampw["archs"]["transformer"]
    lcs = [float(x) for x in t["lc"]]
    fine_lc = float(e2["corpus"]["lc_fine"])
    cb = {lc: statistics.fmean(v) for lc, v in zip(lcs, t["remesh_cb"], strict=True)}
    inb = [cb[lc] for lc in lcs if lc != fine_lc]
    N.put("numRemeshGeometries", str(W._one([n for a in ampw["archs"].values()
                                              for n in a["n_geometries"]], "geometries")))
    N.put("numRemeshInDev", pct(max(abs(x - 1) for x in inb), 0))
    N.put("numRemeshFine", f"{cb[fine_lc]:.2f}")
    extra_numbers(N, r2, r3, amps)
    n2 = per_instance(r2, "ar", "disp_rel_l2").shape[1]
    ncm = per_instance(rcm, "ar", "disp_rel_l2").shape[1]
    n3 = per_instance(r3, "ar", "disp_rel_l2").shape[1]
    rows2 = metric_rows(r2, ARMS_2D)
    rows3 = (metric_rows(r3, ("ar", "labels", "labels_anchor"))
             + metric_rows(k, ("labels_knorm",))
             + metric_rows(r3, ("mgn", "knn_field", "scale_aware_poly")) + rz["val3d"]
             + metric_rows(r3, ("zero",)))
    rowscm = (metric_rows(rcm, ("ar", "labels", "labels_knorm", "mgn", "knn_field",
                                "scale_aware_poly")) + rz["val2d"] + metric_rows(rcm, ("zero",)))
    def ritz_note(k_: str, ps: tuple) -> str:
        deg = and_list([f"$p = {ps[0]}$", *(str(p_) for p_ in ps[1:])])
        return (r"Ritz projection (\cref{sec:methods:ritz}), added after the pre-registered runs: "
                "computed per instance from its own stiffness matrix and loads, without labels "
                f"or training, with {k_} "
                f"unknowns at {deg}; deterministic, so its count of predictions worse than "
                "the zero field is over the instances.")
    notescm = metric_notes(ncm, [
        r"The two-dimensional comparison (\cref{sec:methods:prereg}). "
        "The label-free row evaluates, without retraining them, the label-free networks of "
        r"the latent-regularisation run (supplementary Section~\SuppSide), trained on the "
        r"same 1,024 instances. Supervised, energy norm: the same transformer trained on "
        r"$\mathcal{L}_K$ \eqref{eq:lk} instead of $\mathcal{L}_D$ \eqref{eq:ld}, with "
        "everything else unchanged.", ritz_note(N["numRitzTwoK"], RITZ_LADDER[2])])
    notes2 = metric_notes(n2, [
        "The July run (16 July 2026). Its code did not multiply the load scale back onto the "
        r"output (\cref{sec:methods:networks}); we attribute the narrow spread of the "
        "displacement errors to this; no experiment isolated it."])
    notes3 = metric_notes(n3, [
        r"The three-dimensional comparison (\cref{sec:methods:prereg}). Supervised, energy "
        r"norm: the three-dimensional energy-norm run (\cref{sec:norm:three}), the same "
        r"transformer trained on $\mathcal{L}_K$ \eqref{eq:lk} with the same labelled "
        "instances, settings and seeds, beside the stored label-free and "
        "displacement-supervised transformers, which it evaluated again, reproducing their "
        "values exactly.",
        ritz_note(N["numRitzThreeK"], RITZ_LADDER[3])])
    hle = ["Run", "Model", "16", "64", "256", "1,024"]
    rle, rules_le = label_efficiency_rows((
        ("3D", r3, ("labels", "labels_anchor", "mgn", "knn_field")),
        ("2D", rcm, ("labels", "labels_knorm", "mgn", "knn_field"))))
    nle = ["Seed means over 3 seeds; the nearest-neighbour field is deterministic. A dash marks "
           "a budget at which the model was not trained (the graph network was trained at 64 "
           r"and 1,024 labels only). 3D: the three-dimensional comparison (\cref{tab:3d}); 2D: "
           r"the two-dimensional comparison (\cref{tab:2d}). The label-free row repeats its "
           "single value, which uses the same 1,024 instances without labels."]
    rlj, _ = label_efficiency_rows((
        ("2D, July", r2, ("labels", "labels_anchor", "ar_ft", "mgn", "knn_field")),))
    hlj = ["Model", "16", "64", "256", "1,024"]
    rlj = [r[1:] for r in rlj]
    nlj = ["Seed means over 3 seeds; the nearest-neighbour field is deterministic, and the "
           r"same as in \cref{tab:labeleff}. The graph network was trained at every budget in "
           "this run. The label-free row repeats its single value, which uses the same 1,024 "
           "instances without labels."]
    htr = ["Model", "Displacement\nerror", "Relative\nenergy gap", "von Mises\nerror",
           "Peak stress\nerror", "Critical-region\nrecall"]
    rtr = transfer_rows(r3)
    rtr = rtr[:5] + rz["fine3d"] + rtr[5:]
    p3 = r3["results"]["p3_transfer"]["metrics"]
    ntr = [f"{per_instance(r3, 'ar', 'disp_rel_l2').shape[1]} fine-mesh evaluation instances "
           f"(median {N['numNodesFineMedian']} nodes), disjoint from the 64 instances reserved "
           "for few-shot training. "
           "Mean ± sample standard deviation over 3 seeds; the naive baselines are "
           "deterministic and built from the 1,024 in-band labelled instances.",
           f"In-band, the label-free network's displacement error is "
           f"{p3['ar']['inband_disp_mean']:.4f}; the zero-shot ratio is therefore "
           f"{p3['ar']['fine_disp_mean'] / p3['ar']['inband_disp_mean']:.2f}.",
           "Few-shot training minimises the relative displacement error $\\mathcal{L}_D$ "
           r"\eqref{eq:ld}, without the energy term, for 50 epochs at learning rate "
           "1.5 × 10⁻³, from the trained label-free network of the same seed or from random "
           "initialisation (scratch); the few-shot comparison was pre-registered as reported "
           r"only. Ritz projection: \cref{sec:methods:ritz}, added after the pre-registered runs, "
           "deterministic, on the fine meshes themselves, with nothing trained."]
    hcr = ["Run", "Criterion", "Measured", "Outcome"]
    pilot = (N["numPilotDisp"], N["numPilotLimit"])
    repro_max = adjudicator_constant(vcm, used, "REPRO_MAX")
    rcr, rules_cr = criteria_rows(r2, r3, e1v, e2v, pilot, rw, vcm, repro_max, vho, vk, dates)
    rcl, rules_cl = claims_rows(rcr)
    ncl = ["The criteria are those of the pre-registration documents, which number their own; "
           r"the runs are those of \cref{sec:methods:prereg}. Gates decide whether a study "
           "proceeds to its next stage, kill conditions withdraw a claim when triggered. G2 (a) "
           "is a sanity check of the supervised side, (b) the accuracy of the label-free "
           "network and (c) its transfer to the finer mesh; the amendment of the "
           "three-dimensional gate, written after the initial run, assessed (a) from 64 "
           r"labels only; its naive baselines are the nearest-neighbour field and the scaled "
           r"polynomial of \cref{sec:methods:networks}. The holdout evaluation's claims are in "
           r"\cref{tab:holdout}. "
           "Supplementary Section~\\SuppPrereg{} lists every criterion of every "
           "run with its notes, and the departures from the plans.",
           "Noise guard: a comparison of a network A with a reference B over three seeds "
           "each, with rel = mean(A)/mean(B) − 1 and SE_rel = $(s_A^2/3 + s_B^2/3)^{1/2}$ "
           "divided by mean(B), where $s_A$ and $s_B$ are the sample standard deviations over "
           "the seeds, finds A lower beyond the guard when rel is below minus the guard, "
           "max(10%, 2 SE_rel), and higher beyond it when rel exceeds the guard; within it no "
           "difference is shown, which is not equivalence. The three-dimensional energy-norm "
           "run applies it to each seed's median over the instances. $\\mathcal{L}_D$ and "
           r"$\mathcal{L}_K$ are the losses \eqref{eq:ld} and \eqref{eq:lk}."]
    hcm, rhy, ncm2 = cm2d_hypothesis_table(vcm, rcm)
    ncr = ["Runs are named as in \\cref{tab:runs} and dated by their records; the pilot of "
           "the amendment is the short run that the amendment required before the "
           r"three-dimensional comparison (Section~\ref{app:prereg}). Labels are those of the "
           "pre-registration documents, each of which numbers its own criteria. Gates (G1′, G2) decide whether "
           "the study proceeds to its next stage. Kill conditions withdraw a claim, or abandon "
           "a component, when triggered: in two dimensions K1–K6, C1-advantage (the claimed "
           "advantage in relative energy gap), C5 (the pre-registered checks of "
           r"Section~\ref{app:repro:checks}) and E6 (latent alignment); in three dimensions KP1–KP6, "
           "with KP5 the counterpart of C5. The latent-regularisation and bottleneck runs "
           "number their criteria afresh, with the meanings given here. A criterion reads the "
           "trained networks of the tables it names; the energy-term sub-experiment of the "
           "July run trained its own supervised networks with and without the energy term, "
           "with the same configuration. K4, E6 and KP6 concern latent representations, which "
           "this paper does not use. Standardised effective rank: the participation ratio of "
           "the eigenvalues of the covariance of the latent vectors, each dimension "
           "standardised. The 3D amendment, the deviations and the joint-embedding term are "
           r"described below, the latent regularisation and the token bottleneck in "
           r"Section~\ref{app:e1}, the July run in Section~\ref{app:july}.",
           "Noise guard: a comparison of a network A with a reference B over three seeds "
           "each, with rel = mean(A)/mean(B) − 1 and SE_rel = $(s_A^2/3 + s_B^2/3)^{1/2}$ "
           "divided by mean(B), where $s_A$ and $s_B$ are the sample standard deviations over "
           "the seeds, finds A lower beyond the guard when rel is below minus the guard, "
           "max(10%, 2 SE_rel), and higher beyond it when rel exceeds the guard; within it no "
           "difference is shown, which is not equivalence. The hypotheses H1–H3 of the 2D "
           r"comparison use it (\cref{tab:cm2d}), and so do the latent-regularisation and "
           "bottleneck runs, with the label-free network as B (their pre-registrations call "
           "it the resolution), the holdout evaluation, and the three-dimensional "
           r"energy-norm run, which applies it to each seed's median over the instances "
           r"(\cref{tab:k3d}). $\mathcal{L}_D$ and $\mathcal{L}_K$ are the losses "
           r"\eqref{eq:ld} and \eqref{eq:lk}."]
    h_amp, r_amp = W.amp_rows(ampw)
    h_rem, r_rem = W.remesh_rows(ampw, e2)
    h_e2, r_e2 = W.e2_rows(e2)
    h_e1, r_e1 = W.e1_rows(e1, probe)
    files = {
        "table_2d.tex": table(HEAD_METRICS, rowscm, CAP_2D, "tab:2d", notescm,
                              rules=(4, 6, 8)),
        "table_2djuly.tex": table(HEAD_METRICS, rows2, CAP_2DJULY, "tab:2djuly", notes2,
                                  rules=(5, 7)),
        "table_3d.tex": table(HEAD_METRICS, rows3, CAP_3D, "tab:3d", notes3,
                              rules=(5, 7, 11)),
        "table_label_efficiency.tex": table(hle, rle, CAP_LE, "tab:labeleff", nle,
                                            align="llcccc", rules=rules_le),
        "table_label_efficiency_july.tex": table(hlj, rlj, CAP_LEJULY, "tab:labeleffjuly",
                                                 nlj, align="lcccc"),
        "table_transfer.tex": table(htr, rtr, CAP_TR, "tab:transfer", ntr, rules=(3, 5, 9)),
        "table_k3d.tex": table(h_k3d, r_k3d, CAP_K3D, "tab:k3d", n_k3d, align="lccc",
                               rules=(3, 5, 9, 11, 13)),
        "table_holdout.tex": table(h_ho, r_ho, CAP_HOLD, "tab:holdout", n_ho,
                                   align="@{}" + "".join(
                                       RAGGED + f"p{{{w}\\linewidth}}"
                                       for w in ("0.07", "0.455", "0.14", "0.14", "0.155"))
                                   + "@{}", rules=(3, 9), note_size="scriptsize"),
        "table_holdout_values.tex": longtable(h_hv, r_hv, CAP_HOLDV, "tab:holdoutvalues", n_hv,
                                              align="@{}llccc@{}", rules=rules_hv,
                                              size="footnotesize", sep="3pt"),
        "table_ritz_pairs.tex": longtable(*rz["pairs"][:2], CAP_RITZP, "tab:ritzpairs",
                                          rz["pairs"][2], align="@{}llcccccc@{}",
                                          rules=rz["pairs"][3]),
        "table_k3d_medians.tex": table(h_kmed, r_kmed, CAP_KMED, "tab:kmedians", [],
                                       align="llccccc", rules=(2, 4)),
        "table_k3d_comparisons.tex": table(h_kcmp, r_kcmp, CAP_KCMP, "tab:kcomparisons", [],
                                           align="llcccc", rules=(5, 10)),
        "table_cm2d.tex": table(hcm, rhy, CAP_CM2D, "tab:cm2d", ncm2, align="lcccc",
                                rules=(3, 5, 9)),
        "table_claims.tex": longtable(hcr, rcl, CAP_CL, "tab:claims", ncl,
                                      align="@{}" + "".join(
                                          RAGGED + f"p{{{w}\\linewidth}}"
                                          for w in ("0.145", "0.405", "0.21", "0.12"))
                                      + "@{}",
                                      rules=rules_cl, size="footnotesize"),
        "table_criteria.tex": longtable(hcr, rcr, CAP_CR, "tab:criteria", ncr,
                                        align="@{}" + "".join(
                                            RAGGED + f"p{{{w}\\linewidth}}"
                                            for w in ("0.145", "0.405", "0.21", "0.12"))
                                        + "@{}",
                                        rules=rules_cr),
        "table_amplitude.tex": table(*relabel("amp", h_amp, r_amp, W.amp_notes(ampw, e2))[:2],
                                     CAP_AMP, "tab:amplitude",
                                     relabel("amp", h_amp, r_amp, W.amp_notes(ampw, e2))[2]),
        "table_remesh.tex": table(*relabel("remesh", h_rem, r_rem,
                                           W.remesh_notes(ampw, e2))[:2], CAP_REM, "tab:remesh",
                                  relabel("remesh", h_rem, r_rem, W.remesh_notes(ampw, e2))[2]),
        "table_e2.tex": table(*relabel("e2", h_e2, r_e2, W.e2_notes(e2))[:2], CAP_E2, "tab:e2",
                              relabel("e2", h_e2, r_e2, W.e2_notes(e2))[2]),
        "table_e1.tex": table(*relabel("e1", h_e1, r_e1, W.e1_notes(e1, probe))[:2], CAP_E1,
                              "tab:e1", relabel("e1", h_e1, r_e1, W.e1_notes(e1, probe))[2]),
        "table_cost.tex": table(h_cost, r_cost, CAP_COST, "tab:cost", n_cost, align="lccc",
                                rules=(2, 4, 9, 11, 12), note_size="scriptsize"),
        "numbers.tex": numbers_tex(N),
        "hashes.tex": hashes_tex(used),
    }
    files["material.md"] = (
        "# Manuscript material (generated from the committed records; do not edit)\n\n"
        + md(HEAD_METRICS, rowscm, CAP_2D, notescm) + "\n"
        + md(HEAD_METRICS, rows2, CAP_2DJULY, notes2) + "\n"
        + md(HEAD_METRICS, rows3, CAP_3D, notes3)
        + "\n" + md(hle, rle, CAP_LE, nle) + "\n" + md(hlj, rlj, CAP_LEJULY, nlj) + "\n"
        + md(htr, rtr, CAP_TR, ntr) + "\n"
        + md(hcr, rcl, CAP_CL, ncl) + "\n"
        + md(hcr, rcr, CAP_CR, ncr) + "\n" + md(hcm, rhy, CAP_CM2D, ncm2)
        + "\n" + md(h_cost, r_cost, CAP_COST, n_cost)
        + "\n" + md(h_k3d, r_k3d, CAP_K3D, n_k3d) + "\n" + md(h_ho, r_ho, CAP_HOLD, n_ho)
        + "\n" + md(h_hv, r_hv, CAP_HOLDV, n_hv)
        + "\n" + md(*rz["pairs"][:2], CAP_RITZP, rz["pairs"][2])
        + "\n" + md(h_kmed, r_kmed, CAP_KMED, []) + "\n" + md(h_kcmp, r_kcmp, CAP_KCMP, [])
        + "\n## In-text numbers\n\n"
        + "\n".join(f"- `{k}`: {N[k]}" for k in sorted(N)) + "\n")
    files["sources.json"] = json.dumps({"generator": "scripts/make_cmame_material.py",
                                        "inputs_sha256": dict(sorted(used.items()))},
                                       indent=1) + "\n"
    return {"files": files, "r2": r2, "rcm": rcm, "r3": r3, "e2": e2, "numbers": N,
            "spectra": sz, "figs": figs, "k": k, "nl": nl}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--no-figures", action="store_true")
    a = ap.parse_args()
    b = build()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, text in b["files"].items():
        (out / name).write_text(text, encoding="utf-8")
    written = [out / n for n in b["files"]]
    if not a.no_figures:
        written += figures(b["rcm"], b["r3"], b["k"], out)
        written.append(fig_norm_labels(b["nl"], out))
        written.append(fig_e2(b["e2"], out))
        written.append(fig_spectra(b["spectra"], out))
        written.append(fig_field2d(b["figs"]["fig2d"], out))
        written += fig_fields3d(b["figs"], out)
    print("\n".join(str(p) for p in written))


if __name__ == "__main__":
    main()
