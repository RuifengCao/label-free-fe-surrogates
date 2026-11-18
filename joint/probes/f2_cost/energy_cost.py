#!/usr/bin/env python3
"""Cost of the training energy of one CHS splice instance on a host: the seconds and the memory that the energy of a
batch of fields and its gradient take. Every label-free training step needs both, so this is a lower bound on the
time of a step; no network is involved, because none exists for this family yet.

Exploratory, not a gate. No member of a future gate is drawn: the instance is one of the tested members.
probes/f2_dev/energy_cost.py timed the same energy on one processor thread against a T-stub of G-C2.1
(docs/F2_preparation_note.md), on the family's mesh, which is the coarse one; this script times it on the host of a
gate, on its device, with the memory it takes there. Its fields are the preload state with a small random change:
they are not a plastic reference state and are not made admissible, which does not change the time. The export
before the timing includes the preload solve and takes minutes on a processor.

    python -I probes/f2_cost/energy_cost.py --out OUT.json [--device cuda] [--member B-13_nominal] [--fields 4]
                                            [--repeats 20] [--mesh NAME]

--mesh replaces the family's mesh by another of fejoint.chs (for example tiny), for a dry run on a small machine.
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
    ap = argparse.ArgumentParser(prog="f2-energy-cost")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--member", default="B-13_nominal")
    ap.add_argument("--fields", type=int, default=4)
    ap.add_argument("--repeats", type=int, default=20)
    ap.add_argument("--mesh")
    a = ap.parse_args(argv)
    Path(a.out).resolve().parent.mkdir(parents=True, exist_ok=True)     # before any timing: the report must land
    import numpy as np
    import torch

    from f2.config import config
    from f2.data import export_member
    from f2.family import Params
    from f2.torch_energy import InstanceEnergy

    cfg = config()
    if a.mesh:
        cfg["data"]["mesh"] = a.mesh
    q = Params(**cfg["data"]["tested"][a.member])
    t0 = time.perf_counter()
    ex, pre = export_member(cfg, q)
    t_export = time.perf_counter() - t0
    dev = torch.device(a.device)
    cuda = dev.type == "cuda"
    if cuda:
        torch.cuda.reset_peak_memory_stats()
        m0 = torch.cuda.memory_allocated()
    t0 = time.perf_counter()
    E = InstanceEnergy(ex, device=dev, dtype=torch.float32)
    if cuda:
        torch.cuda.synchronize()
    t_build = time.perf_counter() - t0
    n_z = int(ex["T_shape"][1])
    z_pre = np.asarray(pre["z"], dtype=np.float32) if "z" in pre else np.zeros(n_z, dtype=np.float32)
    Theta = torch.linspace(0.25, 1.0, a.fields, device=dev) * float(ex["Theta_max"])
    rng = np.random.default_rng(0)

    def one():
        """The seconds of the energy of `fields` fields near the preload state with its gradient with respect to the
        fields, and whether both are finite. Drawing the fields and the finiteness check are outside the timing."""
        z = torch.as_tensor(z_pre[None] + 1e-3 * rng.standard_normal((a.fields, n_z)).astype(np.float32),
                            device=dev).requires_grad_(True)
        if cuda:
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        Pi = E.energy(z, Theta, iters=10)
        Pi.sum().backward()
        if cuda:
            torch.cuda.synchronize()
        dt = time.perf_counter() - t0
        return dt, bool(torch.isfinite(Pi).all() and torch.isfinite(z.grad).all())

    finite = [one()[1] for _ in range(3)]                        # warm-up, not timed
    times = []
    for _ in range(a.repeats):
        dt, ok = one()
        finite.append(ok)
        times.append(dt)
    out = {"member": a.member, "mesh": cfg["data"]["mesh"], "nodes": int(np.asarray(ex["nodes"]).shape[0]),
           "unknowns": n_z, "elements": {p: int(np.asarray(ex[f"hexes_{p}"]).shape[0]) for p in ("p", "t", "w")},
           "fields_per_evaluation": a.fields, "bubble_newton_steps": 10, "precision": "float32",
           "export_seconds": round(t_export, 2), "build_energy_seconds": round(t_build, 3),
           "seconds_per_energy_and_gradient": {"median": float(np.median(times)), "mean": float(np.mean(times)),
                                               "min": float(np.min(times)), "max": float(np.max(times))},
           "all_finite": all(finite),
           "peak_memory_GiB": (torch.cuda.max_memory_allocated() / 2 ** 30) if cuda else None,
           "energy_memory_GiB_per_instance": ((torch.cuda.memory_allocated() - m0) / 2 ** 30) if cuda else None,
           "host": {"platform": platform.platform(), "python": platform.python_version(), "torch": torch.__version__,
                    "device": str(dev), "gpu": torch.cuda.get_device_name(0) if cuda else None,
                    "threads": torch.get_num_threads(), "processors": os.cpu_count()},
           "note": "a lower bound on the time of a label-free training step: the network's forward and backward "
                   "pass and the optimiser are not included"}
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
