#!/usr/bin/env python3
"""Timing on one host: the surrogate's prediction of a T-stub's seven-level curve against the reference solve of the
same curve. Exploratory, not a gate; nothing is judged and nothing is trained.

  surrogate   G-C2.2's network with the weights of one of its state files: the fields at the base level and at the
              seven levels in one forward pass, then the amplitude condensation, as c22.train.predict does. The
              preparation of a member (features, maps, its energy on the device) is timed apart.
  reference   c2.data.solve_levels at the seven levels with the gate's solver settings, in this process.

Linear algebra runs on one thread throughout (the thread variables are set before numpy is loaded), as in the
worker processes that made the gate's labels. With --device cuda the surrogate is timed on the GPU and, unless
--no-cpu is given, on one processor thread as well.

    python -I probes/c2_timing/time_curve.py --repo REPO --data DATA --state STATE.pt --out OUT.json
                                             [--set eval] [--members 8] [--fe-members 4] [--device cuda] [--no-cpu]

DATA holds exports made under G-C2.2's configuration, for example by
`python -I c22/__main__.py generate --data DATA --limit 8`. --random-weights replaces the state file by fresh
weights, for a dry run where no state file is at hand; the output says so.
"""
import os

for _k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[_k] = "1"

import argparse  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def main(argv=None):
    here = Path(__file__).resolve().parent                      # the script's own folder must not shadow modules
    sys.path[:] = [p for p in sys.path if not p or Path(p).resolve() != here]
    sys.path.insert(0, str(ROOT))
    ap = argparse.ArgumentParser(prog="c2-timing")
    for k in ("--repo", "--data", "--out"):
        ap.add_argument(k, required=True)
    ap.add_argument("--state")
    ap.add_argument("--random-weights", action="store_true")
    ap.add_argument("--set", default="eval")
    ap.add_argument("--members", type=int, default=8)
    ap.add_argument("--fe-members", type=int, default=4)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--no-cpu", action="store_true")
    a = ap.parse_args(argv)
    Path(a.out).resolve().parent.mkdir(parents=True, exist_ok=True)     # before any timing: the report must land
    if bool(a.state) == a.random_weights:
        raise SystemExit("give --state FILE, or --random-weights for a dry run")
    sys.path.insert(0, str(Path(a.repo) / "src"))
    import numpy as np
    import torch

    from c2.data import load_export, solve_levels, _solver
    from c2.model import build, field
    from c2.train import MATMUL_PRECISION, verify_repository, _check_manifest, _load_state, _prepare
    from c22.condense import condense
    from c22.config import config, sha256

    cfg = config()
    man = _check_manifest(cfg, a.data)
    verify_repository(cfg)
    torch.set_num_threads(1)
    torch.set_float32_matmul_precision(MATMUL_PRECISION)
    rd, tr = cfg["evaluation"]["readings"]["condensed"], cfg["training"]
    levels = list(cfg["data"]["eval_levels_mm"])
    ids = [r["id"] for r in man["instances"] if r["split"] == a.set][:a.members]
    if not ids:
        raise SystemExit(f"no member of the set {a.set} in {a.data}")
    state = _load_state(a.state) if a.state else None
    devices = [a.device] + (["cpu"] if a.device != "cpu" and not a.no_cpu else [])
    out = {"config_sha256": sha256(cfg), "set": a.set, "members": ids, "levels_mm": levels,
           "weights": "fresh, not trained (dry run)" if state is None else
                      {"file": Path(a.state).name, "epoch": int(state["epoch"]), "seed": state["history"].get("seed"),
                       "config_sha256": state["history"].get("config_sha256")},
           "host": {"platform": platform.platform(), "python": platform.python_version(), "numpy": np.__version__,
                    "torch": torch.__version__, "processors": os.cpu_count(), "threads": torch.get_num_threads(),
                    "label_solver": _solver(),
                    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None},
           "surrogate": {}, "reference": {}}

    def sync(dev):
        if dev.type == "cuda":
            torch.cuda.synchronize()

    for name in devices:
        dev = torch.device(name)
        nets, rows = None, {}
        lv = torch.as_tensor([rd["base_level_mm"]] + levels, dtype=torch.float32, device=dev)
        D = lv[1:]
        for k, iid in enumerate([ids[0]] + ids):                 # the first member twice: its first pass warms up
            t0 = time.perf_counter()
            it = _prepare(cfg, a.data, [iid], dev, energy=True, labels=False)[0]
            sync(dev)
            t_prep = time.perf_counter() - t0
            mp, E = it["maps"], it["energy"]
            if nets is None:
                torch.manual_seed(0)
                nets = build(cfg, it["base"].shape[-1] + 1)
                for net, key in zip(nets, ("enc", "dec", "head")):
                    if state is not None:
                        net.load_state_dict(state[key])
                    net.to(dev).eval()
            nonneg = torch.cat([mp["nonneg"], torch.zeros(mp["n_z"] - mp["nonneg"].numel(), dtype=torch.bool,
                                                          device=dev)])
            t0 = time.perf_counter()
            with torch.no_grad():
                zall = field(*nets, it["base"], mp, lv, cfg["map"]["T"], lift=cfg["model"]["lift"] == "web")
            sync(dev)
            t_fwd = time.perf_counter() - t0
            z0, z = zall[:1].expand(D.numel(), -1), zall[1:]
            t0 = time.perf_counter()
            amp, st = condense(E, z0, z, D, nonneg, tr["bubble_newton_steps"], rd["a_min"], rd["a_max"],
                               rd["max_evaluations"], rd["rtol"])
            sync(dev)
            t_cond = time.perf_counter() - t0
            if k > 0:
                rows[iid] = {"nodes": int(it["base"].shape[0]), "prepare_s": t_prep, "forward_s": t_fwd,
                             "condense_s": t_cond, "energy_evaluations": int(st["evals"]),
                             "predict_s": t_fwd + t_cond, "with_preparation_s": t_prep + t_fwd + t_cond}
            del it, E
        med = lambda key: float(np.median([r[key] for r in rows.values()]))   # noqa: E731
        out["surrogate"][name] = {"members": rows,
                                  "median": {key: med(key) for key in ("prepare_s", "forward_s", "condense_s",
                                                                       "predict_s", "with_preparation_s")}}
        print(name, json.dumps(out["surrogate"][name]["median"]), flush=True)
    ls = cfg["data"]["label_solver"]
    for iid in ids[:a.fe_members]:
        ex, _ = load_export(Path(a.data) / "inst" / f"{iid}.npz")
        t0 = time.perf_counter()
        s = solve_levels(ex, levels, ls["tol"], ls["max_it"])
        out["reference"][iid] = {"solve_s": time.perf_counter() - t0, "converged": [bool(v) for v in s["converged"]]}
        print("reference", iid, round(out["reference"][iid]["solve_s"], 1), "s", flush=True)
    if out["reference"]:
        out["reference_median_s"] = float(np.median([r["solve_s"] for r in out["reference"].values()]))
    Path(a.out).write_text(json.dumps(out, indent=1))
    print("written", a.out, flush=True)


if __name__ == "__main__":
    main()
