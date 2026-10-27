#!/usr/bin/env python3
"""cmame-paper Stage 14 (RUNBOOK_CMAME Sec. G): the Ritz baseline's row of
the manuscript's cost table, on the instances and under the protocol of
scripts/time_inference_vs_solve.py (which RUNBOOK_CMAME G1 runs again on the
same machine, so that every row of the table comes from one host): the
first `n_val` (32) instances of the run's validation split and the first
`n_fine` (8) of its fine set (3D: Phase-2b's run; 2D: E1's), after `warmup`
(4) validation instances run untimed; one process, the machine's own thread
settings (recorded).

Per instance, timed apart (Appendix 1: the Ritz work and the assembly of K
are reported separately):
  - `assembly_s`: K assembled again from the mesh with the repository's
    assembler (3D fejepa.fe.tet3d.assemble_tet, K only; 2D
    fejepa.fe.elasticity.assemble_plate, which builds the load battery
    too), checked against the instance's K (`K_max_rel_diff`);
  - `free_s`: the free block of K and F;
  - per p of the ladder, each p on its own (no sub-block of a larger p):
    `basis_s` (the polynomial basis on the free nodes), `kp_s` (K P, P^T K P
    and P^T F, per component block), `solve_s` (the eigendecomposition and
    the pseudo-inverse, Appendix 1), `recon_s` (P v on every dof), and
    `ritz_s` = free_s + basis_s + kp_s + solve_s + recon_s;
  a step whose first run takes under one second is run three times and the
  median kept (the cost table's rule); the solution's five metrics (means
  over the load battery) and the dropped directions are recorded, untimed.
Instance files are read before the clock starts (as the cost table's
solvers, which time the solve of K and F already in memory). The output is
rewritten after every instance; reported only.

Exit status: 0 done; 3 an input refused (a line beginning `REFUSED:` names
it; nothing timed); anything else an error (a traceback, or a one-line
message such as an instance without labels).

    python scripts/ritz_timing.py --config configs/ritz_v1.json --dim 3 \\
        --out runs/ritz/timing/ritz_timing_3d.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fejepa.analysis import ritz as R  # noqa: E402

REPEAT_BELOW_S = 1.0
"""As scripts/time_inference_vs_solve.py: a step faster than this is run three
times and the median kept."""
PARTS = ("basis_s", "kp_s", "solve_s", "recon_s")


def repeated(fn, seconds) -> list:
    """[fn(), ...]: one run, or three when the first run's `seconds(result)`
    is under REPEAT_BELOW_S (the first run decides, as in the cost table's
    scripts/time_inference_vs_solve.py)."""
    runs = [fn()]
    if seconds(runs[0]) < REPEAT_BELOW_S:
        runs += [fn(), fn()]
    return runs


def _timed(fn):
    """(result of the last run, [seconds per run]) under `repeated`'s rule."""
    def once():
        t0 = time.perf_counter()
        out = fn()
        return out, time.perf_counter() - t0

    runs = repeated(once, lambda r: r[1])
    return runs[-1][0], [t for _, t in runs]


def assemble(arch):
    """K from the instance's mesh and material, by the repository's assembler."""
    if arch.nodes.shape[1] == 3:
        from fejepa.fe.tet3d import assemble_tet

        return assemble_tet(arch.nodes, arch.elements, arch.meta["material"])
    from fejepa.fe.elasticity import assemble_plate

    ex = arch.meta["extra"]
    return assemble_plate(arch.nodes, arch.elements, arch.meta["material"], ex["width"],
                          ex["height"], np.ones(4))[0]


def one_p(arch, p: int, Kff, Ff) -> dict:
    """One run of the Ritz work at degree p, each part timed."""
    t = {}
    Phi, _, A, B = R.coarse_system(arch, p, Kff, Ff, t)
    t0 = time.perf_counter()
    v, dropped = R.pinv_solve(A, B)
    t["solve"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    U = R.reconstruct(arch, Phi, np.arange(A.shape[0]), v, Ff.shape[0])
    t["recon"] = time.perf_counter() - t0
    return {"basis_s": t["basis"], "kp_s": t["kp"], "solve_s": t["solve"],
            "recon_s": t["recon"], "U": U, "dropped": dropped}


def time_instance(arch, ladder) -> dict:
    from fejepa.metrics import evaluate_fields

    if arch.U_star is None:
        raise SystemExit(f"{arch.path}: no labels")
    K2, ta = _timed(lambda: assemble(arch))
    D = (K2.tocsr() - arch.K.tocsr()).tocoo()
    kdiff = (float(np.abs(D.data).max()) if D.nnz else 0.0) / float(np.abs(arch.K.data).max())
    (Kff, Ff), tf = _timed(lambda: R.free_block(arch))
    row = {"file": Path(str(arch.path)).name, "n_nodes": int(arch.n_nodes),
           "n_free_dof": int(Kff.shape[0]), "assembly_s": statistics.median(ta),
           "assembly_runs": ta, "K_max_rel_diff": kdiff, "free_s": statistics.median(tf),
           "free_runs": tf, "p": {}}
    for p in ladder:
        runs = repeated(lambda: one_p(arch, p, Kff, Ff), lambda r: sum(r[k] for k in PARTS))
        e = {k: statistics.median([x[k] for x in runs]) for k in PARTS}
        e["ritz_s"] = row["free_s"] + sum(e[k] for k in PARTS)
        e["runs"] = len(runs)
        e["k"] = R.n_unknowns(arch.nodes.shape[1], p)
        e["dropped"] = runs[-1]["dropped"]
        e.update(evaluate_fields(runs[-1]["U"], arch))
        row["p"][str(p)] = e
    return row


def summarise(rows: list, ladder) -> dict:
    def med(v):
        return float(np.median(v)) if len(v) else None

    out = {"n": len(rows), "n_free_dof_median": med([r["n_free_dof"] for r in rows]),
           "assembly_s_median": med([r["assembly_s"] for r in rows]),
           "free_s_median": med([r["free_s"] for r in rows]),
           "K_max_rel_diff_max": max([r["K_max_rel_diff"] for r in rows] or [0.0]), "p": {}}
    for p in ladder:
        P = str(p)
        out["p"][P] = {k: med([r["p"][P][k] for r in rows])
                       for k in PARTS + ("ritz_s",) + R.FIELDS}
        out["p"][P]["dropped_max"] = max([r["p"][P]["dropped"] for r in rows] or [0])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="The Ritz baseline's cost-table row (post hoc)")
    ap.add_argument("--config", required=True, help="configs/ritz_v1.json")
    ap.add_argument("--dim", required=True, choices=["2", "3"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    from fejepa.analysis.posthoc import run_files
    from fejepa.data.archive import LazyArchives

    try:
        cfg = R.load_config(a.config)
        spec = cfg["timing"][f"{a.dim}d"]
        report = json.loads(R.checked(spec["report"], spec["report_sha256"],
                                      f"timing {a.dim}d report").read_text())
    except (OSError, ValueError, KeyError) as exc:
        print(f"REFUSED: {exc}", flush=True)
        sys.exit(3)
    dim = int(a.dim)
    ladder = R.LADDER[dim]
    try:
        sets = {"val": run_files(report, "val", int(spec["n_val"]))}
        if int(spec["n_fine"]) > 0:
            sets["fine"] = run_files(report, "fine", int(spec["n_fine"]))
    except SystemExit as exc:
        print(f"REFUSED: {exc}", flush=True)
        sys.exit(3)
    res = {"what": "the polynomial Ritz baseline's cost-table row (Appendix 1; post hoc; "
                   "reported only)",
           "code": R.code_provenance(ROOT), "machine": R.machine(),
           "config_sha256": R.sha256(a.config), "report": spec["report"],
           "report_sha256": spec["report_sha256"],
           "settings": {"warmup": int(spec["warmup"]), "repeat_below_s": REPEAT_BELOW_S,
                        "ladder_p": list(ladder), "cut": R.CUT,
                        "excluded": "reading the instance file"},
           "sets": {k: {"n": len(v), "first": Path(str(v[0])).name,
                        "last": Path(str(v[-1])).name} for k, v in sets.items()},
           "results": {}}
    t_all = time.time()
    for arch in LazyArchives(sets["val"][:max(0, int(spec["warmup"]))]):     # untimed
        time_instance(arch, ladder)
    for name, files in sets.items():
        rows = []
        for i, arch in enumerate(LazyArchives(files)):
            rows.append(time_instance(arch, ladder))
            res["results"][name] = {"rows": rows, "summary": dict(summarise(rows, ladder),
                                                                  complete=i + 1 == len(files))}
            R.write_json(a.out, res)
            r = rows[-1]
            top = r["p"][str(ladder[-1])]
            print(f"[ritz-timing] {name} {i + 1}/{len(files)} dof {r['n_free_dof']} | assembly "
                  f"{r['assembly_s']:.3f} s, ritz p{ladder[-1]} {top['ritz_s']:.3f} s, gap "
                  f"{top['energy_gap_rel']:.3g} | {time.time() - t_all:.0f} s", flush=True)
    line = {name: {"n": v["summary"]["n"], "assembly_s": v["summary"]["assembly_s_median"],
                   "ritz_s": {p: e["ritz_s"] for p, e in v["summary"]["p"].items()},
                   "K_max_rel_diff_max": v["summary"]["K_max_rel_diff_max"]}
            for name, v in res["results"].items()}
    print(json.dumps(line), flush=True)


if __name__ == "__main__":
    main()
