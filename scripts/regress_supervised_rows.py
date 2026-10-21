#!/usr/bin/env python3
"""cmame-paper Stage 12 (PREREG_K3D Sec. 7): does this checkout train E8's
supervised rows bitwise as another checkout does, when the label-free row is
known to differ?

`scripts/regress_against_branch.py` compares every number of two runs of a
miniature of a stamped configuration. Against the code that trained Phase-2's
supervised states (wp7-3d `99d3674` and `e672110`, early September 2026) the
label-free row differs by design -- DEVIATIONS_PHASE2 D14 corrected the
label-free objective after Phase-2 -- and with it everything computed from
it. This script runs the same miniature (`regress_against_branch.miniature`,
each side in its own process importing its own source tree, CPU, one thread,
a fresh pass and a restart pass) and compares only what does not depend on the
label-free row: E8's cells of the supervised rows (labels-only, labels+energy,
graph network) and of the naive rows, bitwise, and the bytes of the supervised
rows' state files. The other differences are counted by where they are, to
show that each lies on a path that reads the label-free states.

    python scripts/regress_supervised_rows.py --other ../FE-JEPA-e672110/src \
        --config configs/phase2_v1.json --work runs/regress_p2 \
        --out records/cmame/k3d/regression_phase2_e672110.json

Exit status 0 iff the compared rows and state files are identical.
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SUPERVISED = ("labels", "labels_anchor", "mgn")
NAIVE = ("zero", "scale_aware_poly", "knn_field")
STATE_ROWS = ("labels", "mgn")
"""The rows whose largest-budget states E8 keeps (besides the label-free row)."""
LABEL_FREE_PATHS = ("/results/e8/metrics/cells/ar/", "/results/e8/metrics/ar_egap_advantage",
                    "/results/e8/metrics/d9_restart/", "/results/e8/kills",
                    "/results/e8/protocol/ar_only", "/results/p3_transfer/", "/results/wp6/",
                    "/gate_g2", "/labels_present")
"""Where the label-free row's states, or what is computed from them, enter the
report (P3 fine-tunes them, WP6 inspects them, gate G2 and E8's kills compare
them) and the keys the later code adds to the report ('labels_present',
'gate_g2_reference_all_budgets', E8's 'ar_only' flag)."""


def _rab():
    spec = importlib.util.spec_from_file_location("regress_against_branch",
                                                  ROOT / "scripts" / "regress_against_branch.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def summarise(this: dict, other: dict, rab) -> dict:
    out = {"rows": {}, "other_differences": {}}
    for name in ("fresh", "restart"):
        a, b = this["reports"][name], other["reports"][name]
        ca, cb = a["results"]["e8"]["metrics"]["cells"], b["results"]["e8"]["metrics"]["cells"]
        rows = {}
        for r in SUPERVISED + NAIVE:
            diffs, n = rab.compare(ca.get(r), cb.get(r), f"/{r}")
            rows[r] = {"floats": n, "differences": len(diffs), "first": diffs[:5],
                       "present": r in ca and r in cb}
        out["rows"][name] = rows
        diffs, _ = rab.compare(a, b, "")
        where = collections.Counter()
        outside = []
        for d in diffs:
            path = d.split(":")[0]
            hit = next((p for p in LABEL_FREE_PATHS if path.startswith(p)), None)
            if hit is None and not any(path.startswith(f"/results/e8/metrics/cells/{r}/")
                                       for r in SUPERVISED + NAIVE):
                outside.append(d)
            where[hit or "elsewhere"] += 1
        out["other_differences"][name] = {"by_path": dict(sorted(where.items())),
                                          "outside_label_free_paths": outside[:20]}
    names = sorted(n for n in set(this["states"]) | set(other["states"])
                   if n.split("_b")[0] in STATE_ROWS)
    out["state_files_identical"] = {n: this["states"].get(n) == other["states"].get(n)
                                    for n in names}
    out["identical"] = bool(
        names and all(out["state_files_identical"].values())
        and all(v["present"] and v["differences"] == 0
                for rows in out["rows"].values() for v in rows.values())
        and not any(v["outside_label_free_paths"] for v in out["other_differences"].values()))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--other", required=True, help="the other checkout's src directory")
    ap.add_argument("--src", default=str(ROOT / "src"), help="this side (default: here)")
    ap.add_argument("--config", default=str(ROOT / "configs" / "phase2_v1.json"))
    ap.add_argument("--work", default="runs/regress_supervised")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rab = _rab()
    for side in (a.src, a.other):
        if not Path(side, "fejepa", "__init__.py").exists():
            raise SystemExit(f"{side}: no fejepa package there (pass a checkout's src directory)")
    cfg = json.loads(Path(a.config).read_text())
    work = Path(a.work)
    this = rab.run_side(a.src, cfg, work / "this")
    other = rab.run_side(a.other, cfg, work / "other")
    summary = {"this_src_tree": rab.src_tree(a.src), "other_src_tree": rab.src_tree(a.other),
               "config": rab._rel(a.config), **summarise(this, other, rab)}
    text = json.dumps(summary, indent=1)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text + "\n")
    print(text)
    sys.exit(0 if summary["identical"] else 1)


if __name__ == "__main__":
    main()
