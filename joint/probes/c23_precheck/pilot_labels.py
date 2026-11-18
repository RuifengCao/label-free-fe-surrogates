#!/usr/bin/env python3
"""Before gate G-C2.3 is stamped: do the labels of the supervised arm's training members solve on this host?

The supervised arm labels its 512 training members at eight levels. The lowest, 0.1 mm, was not solved for a label by
any earlier gate, and a training label that fails ends part 2 (docs/PRESPEC_G-C2.3.md, "Stop conditions"). This probe
solves members of the family drawn with a seed that was used before G-C2.1's stamp, on the gate's mesh, at the gate's
eight levels, with the gate's solver settings and label checks, and reports for each member whether every level
converged, with its iterations and seconds.

    python -I probes/c23_precheck/pilot_labels.py --out NEW [--members 32] [--workers 16] [--seed 101]

NEW must not exist: the exports, the labels and the report, pilot_labels.json, are written there. Nothing of G-C2.3
is drawn: the configuration is the gate's with the data part changed in the seeds and the numbers of members only,
the four family seeds are 7, 8, 101 and 102, and the probe refuses to sample any other family seed. It ends with a
code other than 0 if a label does not converge or fails its checks.
"""
import argparse
import copy
import json
import os
import platform
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SEEN = (7, 8, 101, 102)                                         # family seeds used before G-C2.1's stamp


def main(argv=None):
    here = Path(__file__).resolve().parent                      # the script's own folder must not shadow modules
    sys.path[:] = [p for p in sys.path if not p or Path(p).resolve() != here]
    sys.path.insert(0, str(ROOT))
    ap = argparse.ArgumentParser(prog="c23-pilot-labels")
    ap.add_argument("--out", required=True)
    ap.add_argument("--members", type=int, default=32)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--seed", type=int, default=101, choices=SEEN)
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists():
        raise SystemExit(f"{out} exists; give a new folder (nothing is deleted)")
    import numpy as np
    import scipy

    import c2.family as family
    from c2.data import _solver
    from c23 import data
    from c23.config import config, sha256, THIRD_EVAL_SEED

    real = family.sample

    def seen_only(n, seed, *args, **kwargs):
        if seed not in SEEN:
            raise RuntimeError(f"this probe does not sample the family seed {seed}")
        return real(n, seed, *args, **kwargs)

    family.sample = data.sample = seen_only                     # every draw of this process goes through the refusal
    gate = config()
    cfg = copy.deepcopy(gate)
    d = cfg["data"]
    others = [s for s in SEEN if s != a.seed]
    d["train_seed"], (d["third_eval_seed"], d["eval_seed"], d["former_eval_seed"]) = a.seed, others
    d["seeds_seen_before_stamp"] = [s for s in d["seeds_seen_before_stamp"] if s not in SEEN]
    d["n_train"] = d["n_train_labelled"] = a.members
    d["n_third"] = d["n_eval"] = 1                              # drawn, as the gate's function draws them; not exported
    cfg["arms"]["supervised_512"]["labels"] = a.members
    assert THIRD_EVAL_SEED not in (d["train_seed"], d["third_eval_seed"], d["eval_seed"], d["former_eval_seed"])
    assert d["train_label_levels_mm"] == gate["data"]["train_label_levels_mm"] and d["mesh"] == gate["data"]["mesh"]
    assert d["label_solver"] == gate["data"]["label_solver"]
    t0 = time.time()
    data.generate(cfg, out, splits=("train",))
    export_seconds = round(time.time() - t0, 1)
    ids = data.labelled_ids(cfg, out, ("train",))
    t0 = time.time()
    data.label(cfg, out, ids, workers=a.workers)
    label_seconds = round(time.time() - t0, 1)
    check = data.check_labels(cfg, out, ("train",))
    led = sorted(json.loads((out / "labels" / "ledger.json").read_text()), key=lambda e: e["id"])
    sec = [float(e["seconds"]) for e in led]
    rep = {"gate_config_sha256": sha256(gate), "pilot_config_sha256": sha256(cfg), "family_seed": a.seed,
           "members": len(ids), "levels_mm": d["train_label_levels_mm"], "mesh": d["mesh"],
           "label_solver": d["label_solver"], "linear_solver": _solver(), "workers": a.workers,
           "export_seconds": export_seconds, "label_seconds_wall": label_seconds,
           "label_seconds_per_member": {"median": float(np.median(sec)), "max": float(np.max(sec)),
                                        "sum": float(np.sum(sec))} if sec else None,
           "all_converged": bool(len(led) == len(ids) and all(all(e["converged"]) for e in led)),
           "check_labels": check,
           "per_member": [{k: e[k] for k in ("id", "seconds", "converged", "iterations") if k in e} for e in led],
           "host": {"platform": platform.platform(), "python": platform.python_version(), "numpy": np.__version__,
                    "scipy": scipy.__version__, "processors": os.cpu_count(),
                    "thread_variables": {k: os.environ.get(k) for k in data.THREAD_VARIABLES}}}
    (out / "pilot_labels.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: rep[k] for k in ("family_seed", "members", "levels_mm", "linear_solver", "all_converged",
                                          "label_seconds_wall", "label_seconds_per_member")}), flush=True)
    print(json.dumps(check), flush=True)
    if not (rep["all_converged"] and check.get("ok") is True):
        raise SystemExit("a label did not converge or failed its checks; see pilot_labels.json")


if __name__ == "__main__":
    main()
