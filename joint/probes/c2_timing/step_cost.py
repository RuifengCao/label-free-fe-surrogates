#!/usr/bin/env python3
"""Seconds per training step on one host, for the two losses of gate G-C2.3: the energy (label-free) and the
supervised loss. Exploratory, not a gate; nothing is trained to any purpose and no label is needed: the supervised
loss is timed against zero fields, which costs the same as against reference fields.

Each step is G-C2.2's: one training member, 4 fields, AdamW, the global clipping. The stability recipe's cap is left
out; it costs one norm of the encoder's gradient.

    python -I probes/c2_timing/step_cost.py --repo REPO --data DATA --out OUT.json [--members 8] [--steps 40]
                                            [--device cuda]

DATA holds exports of training members made under G-C2.2's configuration, for example by
`python -I c22/__main__.py generate --data DATA --limit 8`.
"""
import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(argv=None):
    here = Path(__file__).resolve().parent                      # the script's own folder must not shadow modules
    sys.path[:] = [p for p in sys.path if not p or Path(p).resolve() != here]
    sys.path.insert(0, str(ROOT))
    ap = argparse.ArgumentParser(prog="c2-step-cost")
    for k in ("--repo", "--data", "--out"):
        ap.add_argument(k, required=True)
    ap.add_argument("--members", type=int, default=8)
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--device", default="cuda")
    a = ap.parse_args(argv)
    Path(a.out).resolve().parent.mkdir(parents=True, exist_ok=True)     # before any timing: the report must land
    sys.path.insert(0, str(Path(a.repo) / "src"))
    import numpy as np
    import torch

    from c2.model import build
    from c2.torch_energy import sparse
    from c2.train import MATMUL_PRECISION, verify_repository, _check_manifest, _prepare, step_loss
    from c2.data import load_export
    from c22.config import config, sha256

    cfg = config()
    man = _check_manifest(cfg, a.data)
    verify_repository(cfg)
    torch.set_float32_matmul_precision(MATMUL_PRECISION)
    dev = torch.device(a.device)
    cuda = dev.type == "cuda"
    ids = [r["id"] for r in man["instances"] if r["split"] == "train"][:a.members]
    tr = cfg["training"]
    levels = torch.as_tensor([0.1, 0.75, 1.5, 2.5, 3.5, 5.0, 7.0, 8.0], dtype=torch.float32, device=dev)
    out = {"config_sha256": sha256(cfg), "members": ids, "fields_per_step": tr["fields_per_step"],
           "host": {"platform": platform.platform(), "python": platform.python_version(), "torch": torch.__version__,
                    "device": str(dev), "gpu": torch.cuda.get_device_name(0) if cuda else None,
                    "threads": torch.get_num_threads(), "processors": os.cpu_count()}, "losses": {}}
    for name, sup in (("energy", False), ("supervised", True)):
        torch.manual_seed(0)
        rng = np.random.default_rng(0)
        if cuda:
            torch.cuda.reset_peak_memory_stats()
        items = _prepare(cfg, a.data, ids, dev, energy=not sup, labels=False)
        if sup:
            for it, iid in zip(items, ids):                     # zero reference fields at the labelled levels
                ex, _ = load_export(Path(a.data) / "inst" / f"{iid}.npz")
                it["T"] = sparse(ex["T_row"], ex["T_col"], ex["T_val"], ex["T_shape"], dev, torch.float32)
                it["D_lab"] = levels
                it["u_lab"] = torch.zeros((levels.numel(), int(ex["T_shape"][0])), dtype=torch.float32, device=dev)
        nets = build(cfg, items[0]["base"].shape[-1] + 1)
        for net in nets:
            net.to(dev).train()
        params = [p for net in nets for p in net.parameters()]
        opt = torch.optim.AdamW(params, lr=tr["lr"], weight_decay=tr["weight_decay"], betas=(0.9, tr["beta2"]))

        def one(it):
            loss, _ = step_loss(cfg, nets, it, rng, sup, dev)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, tr["clip"])
            opt.step()
            if cuda:
                torch.cuda.synchronize()
            return float(loss.detach())

        losses = [one(items[i % len(items)]) for i in range(a.warmup)]
        times = []
        for i in range(a.steps):
            t0 = time.perf_counter()
            losses.append(one(items[i % len(items)]))
            times.append(time.perf_counter() - t0)
        med = float(np.median(times))
        steps = cfg["arms"]["label_free"]["epochs"] * cfg["data"]["n_train"]
        out["losses"][name] = {"seconds_per_step_median": med, "seconds_per_step_mean": float(np.mean(times)),
                               "seconds_per_step_max": float(np.max(times)),
                               "hours_for_a_run_at_the_median": med * steps / 3600.0, "steps_of_a_run": steps,
                               "losses_finite": bool(np.isfinite(losses).all()),
                               "peak_memory_GiB": (torch.cuda.max_memory_allocated() / 2 ** 30) if cuda else None}
        print(name, json.dumps(out["losses"][name]), flush=True)
        del items, nets, opt
    Path(a.out).write_text(json.dumps(out, indent=1))
    print("written", a.out, flush=True)


if __name__ == "__main__":
    main()
