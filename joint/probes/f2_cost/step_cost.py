#!/usr/bin/env python3
"""Cost of a label-free training step of the CHS surrogate on a host: seconds a step and peak memory, for several
numbers of fields a step, with the step split into the network's forward pass, the energy and the backward pass.

Exploratory, not a gate, and nothing here is stamped. No member of a future gate is drawn: the instances are tested
members of the family (f2.family.TESTED). The network is the one of gates G-C2.1 to G-C2.3 (the repository's
transformer encoder, 8 blocks of width 256 with 8 heads, activation checkpointing) with the draft wrapper of
f2/model.py, and the step is G-C2.2's: the mean of log Pi over the step's fields, AdamW with beta2 0.99, the cap on
the encoder's gradient, clipping at 1, float32 without TF32. The steps start from a new network, so their losses
say nothing about training; only the times and the memory are read.

    python -I probes/f2_cost/step_cost.py --out OUT.json [--device cuda] [--members B-13_nominal,B-19_nominal]
                                          [--fields 4,2,1] [--warmup 3] [--steps 12] [--levels 0] [--mesh NAME]
                                          [--also-without-checkpointing]

--levels N also solves the first N evaluation levels of the first member with the reference code and reports the
seconds of each (a label of a member has seven). --mesh replaces the family's mesh by another of fejoint.chs (for
example tiny), for a dry run on a small machine. --also-without-checkpointing repeats the timing with the encoder's
activation checkpointing off (the same gradients, more memory, no second forward pass of each block). The export of
a member includes its preload solve and takes minutes on a processor.
"""
import argparse
import collections
import json
import os
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = {"dim": 256, "depth": 8, "heads": 8, "activation_checkpointing": True}
TRAIN = {"lr": 1e-3, "weight_decay": 1e-4, "beta2": 0.99, "clip": 1.0, "bubble_newton_steps": 10,
         "cap": {"factor": 5.0, "burst_factor": 10.0, "window_steps": 256}}
MAP_T = 0.001


def main(argv=None):
    here = Path(__file__).resolve().parent                      # the script's own folder must not shadow modules
    sys.path[:] = [p for p in sys.path if not p or Path(p).resolve() != here]
    sys.path.insert(0, str(ROOT))
    if (ROOT.parent / "src").is_dir():
        sys.path.insert(0, str(ROOT.parent / "src"))            # the repository's package (the encoder)
    ap = argparse.ArgumentParser(prog="f2-step-cost")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--members", default="B-13_nominal")
    ap.add_argument("--fields", default="4,2,1")
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--steps", type=int, default=12)
    ap.add_argument("--levels", type=int, default=0)
    ap.add_argument("--mesh")
    ap.add_argument("--no-lift", action="store_true")
    ap.add_argument("--also-without-checkpointing", action="store_true")
    a = ap.parse_args(argv)
    out_path = Path(a.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)          # before any timing: the report must land
    import numpy as np
    import torch

    from c22.train import cap_encoder_gradient
    from f2.config import config
    from f2.data import export_member, solve_levels
    from f2.family import Params
    from f2.model import features, maps, build, field, sample_Theta
    from f2.torch_energy import InstanceEnergy
    from fejepa.train.schedule import make_scheduler

    torch.set_float32_matmul_precision("highest")
    cfg = config()
    if a.mesh:
        cfg["data"]["mesh"] = a.mesh
    dev = torch.device(a.device)
    cuda = dev.type == "cuda"

    def sync():
        if cuda:
            torch.cuda.synchronize()

    out = {"what": "seconds and memory of a label-free training step of the CHS surrogate (draft network wrapper)",
           "mesh": cfg["data"]["mesh"], "model": MODEL, "training": TRAIN, "lift": not a.no_lift,
           "precision": "float32, matmul precision " + torch.get_float32_matmul_precision(),
           "host": {"platform": platform.platform(), "python": platform.python_version(), "torch": torch.__version__,
                    "numpy": np.__version__, "device": str(dev), "gpu": torch.cuda.get_device_name(0) if cuda else None,
                    "gpu_memory_GiB": (torch.cuda.get_device_properties(0).total_memory / 2 ** 30) if cuda else None,
                    "threads": torch.get_num_threads(), "processors": os.cpu_count()},
           "attention_kernels": ({"flash": torch.backends.cuda.flash_sdp_enabled(),
                                  "mem_efficient": torch.backends.cuda.mem_efficient_sdp_enabled(),
                                  "math": torch.backends.cuda.math_sdp_enabled()} if cuda else None),
           "members": [], "by_fields": {}}

    def save():
        tmp = out_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(out, indent=1))
        os.replace(tmp, out_path)

    items, first = [], None
    for name in [m for m in a.members.split(",") if m]:
        q = Params(**cfg["data"]["tested"][name])
        t0 = time.perf_counter()
        ex, pre = export_member(cfg, q)
        t_export = time.perf_counter() - t0
        if first is None:
            first = (ex, pre)
        if cuda:
            m0 = torch.cuda.memory_allocated()
        it = {"id": name, "base": torch.as_tensor(features(ex, q), dtype=torch.float32, device=dev),
              "maps": maps(ex, q, dev), "energy": InstanceEnergy(ex, device=dev, dtype=torch.float32)}
        sync()
        items.append(it)
        out["members"].append({"id": name, "nodes": int(it["base"].shape[0]), "unknowns": it["maps"]["n_z"],
                               "bolt_heads": it["maps"]["nb"], "Theta_max": it["maps"]["Theta_max"],
                               "export_seconds": round(t_export, 2),
                               "device_memory_GiB": ((torch.cuda.memory_allocated() - m0) / 2 ** 30) if cuda else None})
        save()

    if a.levels > 0:                                             # the reference: seconds of a level of a label
        ex, pre = first
        lam = list(cfg["data"]["eval_levels"])[:a.levels]
        ls = cfg["data"]["label_solver"]
        t0 = time.perf_counter()
        sol = solve_levels(ex, np.asarray(pre["z"], float), lam, ls["tol"], ls["max_it"])
        out["reference_levels"] = {"member": out["members"][0]["id"], "fractions": lam,
                                   "seconds_total": round(time.perf_counter() - t0, 2),
                                   "iterations": [int(i) for i in sol["iterations"]],
                                   "converged": [bool(c) for c in sol["converged"]]}
        from fejoint import linsolve
        out["reference_levels"]["solver"] = "pardiso" if linsolve._PARDISO is not None else "scipy"
        save()

    in_dim, nb = items[0]["base"].shape[-1] + 1, items[0]["maps"]["nb"]
    runs = [(int(b), True) for b in a.fields.split(",") if b]
    if a.also_without_checkpointing:
        out["by_fields_without_checkpointing"] = {}
        runs += [(B, False) for B, _ in list(runs)]
    for B, checkpointing in runs:
        rec = {"fields_per_step": B}
        out["by_fields" if checkpointing else "by_fields_without_checkpointing"][str(B)] = rec
        try:
            torch.manual_seed(0)
            rng = np.random.default_rng(0)
            nets = build({"model": dict(MODEL, activation_checkpointing=checkpointing)}, in_dim, nb)
            for net in nets:
                net.to(dev); net.train()
            enc = nets[0]
            params = [p for net in nets for p in net.parameters()]
            opt = torch.optim.AdamW(params, lr=TRAIN["lr"], weight_decay=TRAIN["weight_decay"],
                                    betas=(0.9, TRAIN["beta2"]))
            sched = make_scheduler(opt, a.warmup + a.steps)
            window = collections.deque(maxlen=TRAIN["cap"]["window_steps"])
            if cuda:
                torch.cuda.reset_peak_memory_stats()
            parts = {"network_forward": [], "energy": [], "backward_and_update": [], "step": []}
            losses = []
            for k in range(a.warmup + a.steps):
                it = items[k % len(items)]
                Theta = torch.as_tensor(sample_Theta(rng, it["maps"]["Theta_max"], B), dtype=torch.float32, device=dev)
                sync(); t0 = time.perf_counter()
                z = field(*nets, it["base"], it["maps"], Theta, MAP_T, lift=not a.no_lift)
                sync(); t1 = time.perf_counter()
                Pi = it["energy"].energy(z, Theta, iters=TRAIN["bubble_newton_steps"])
                loss = torch.log(Pi).mean()
                sync(); t2 = time.perf_counter()
                opt.zero_grad(set_to_none=True)
                loss.backward()
                cap_encoder_gradient(enc, window, TRAIN["cap"])
                torch.nn.utils.clip_grad_norm_(params, TRAIN["clip"])
                opt.step(); sched.step()
                sync(); t3 = time.perf_counter()
                losses.append(float(loss.detach()))
                if k >= a.warmup:
                    for key, dt in (("network_forward", t1 - t0), ("energy", t2 - t1),
                                    ("backward_and_update", t3 - t2), ("step", t3 - t0)):
                        parts[key].append(dt)
            rec.update({"seconds": {key: {"median": float(np.median(v)), "mean": float(np.mean(v)),
                                           "max": float(np.max(v))} for key, v in parts.items()},
                        "losses_first_and_last": [losses[0], losses[-1]],
                        "losses_finite": bool(np.isfinite(losses).all()),
                        "peak_memory_GiB": (torch.cuda.max_memory_allocated() / 2 ** 30) if cuda else None,
                        "steps_timed": a.steps})
        except RuntimeError as err:                              # out of memory on the device: record and go on
            if "out of memory" not in str(err).lower():
                raise
            rec["out_of_memory"] = str(err).splitlines()[0][:200]
            rec["peak_memory_GiB"] = (torch.cuda.max_memory_allocated() / 2 ** 30) if cuda else None
        finally:
            nets = params = opt = sched = None
            if cuda:
                torch.cuda.empty_cache()
        save()
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
