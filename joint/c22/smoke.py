"""Check of a host before gate G-C2.2 runs on it, on a reduced configuration: the coarse mesh, a small model, four
epochs, and the family seeds 7, 8 and 101, which were used before G-C2.1's stamp. Nothing of the gate is drawn,
exported, solved or trained: the reduced configuration has another hash, and the gate's held-out seed is not used.

It runs every stage the runbook runs, with worker processes for the labels and the evaluation and with the training
on the given device: generate, label, check-labels, train (once without interruption, once interrupted after two
epochs and resumed), predict in both readings, evaluate. It records the machine in its report.

    python -I c22/smoke.py --repo REPO --out DIR [--device cuda] [--workers 4]
"""
import argparse
import copy
import json
import os
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def reduced():
    from c2.config import TESTED
    from c22.config import config

    cfg = copy.deepcopy(config())
    d = cfg["data"]
    d["n_train"], d["n_eval"], d["n_former"] = 4, 2, 2
    d["train_seed"], d["eval_seed"], d["former_eval_seed"] = 7, 8, 101
    d["seeds_seen_before_stamp"] = [s for s in d["seeds_seen_before_stamp"] if s not in (7, 8, 101)]
    d["mesh"] = {"h": 10.0, "n_tf": 1, "hx_max": 40.0}
    d["eval_levels_mm"] = [0.5, 4.0]
    d["tested"] = {"BJ_T1_preloaded": dict(TESTED["BJ_T1_preloaded"])}
    cfg["model"].update(dim=32, depth=1, heads=2)
    cfg["training"]["encoder_gradient_cap"].update(window_steps=3, factor=0.5, burst_factor=1.0)
    cfg["arms"]["label_free"]["epochs"] = 4
    cfg["arms"]["label_free"]["seeds"] = [5]                  # one seed is enough to run every stage
    return cfg


def main(argv=None):
    here = Path(__file__).resolve().parent                      # the script's own folder must not shadow modules
    sys.path[:] = [p for p in sys.path if not p or Path(p).resolve() != here]
    sys.path.insert(0, str(ROOT))
    ap = argparse.ArgumentParser(prog="c22-smoke")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args(argv)
    sys.path.insert(0, str(Path(args.repo) / "src"))
    import multiprocessing as mp

    import numpy as np
    import scipy
    import torch

    from c2.data import _solver
    from c22 import data
    from c22.config import sha256
    from c22.evaluate import evaluate
    from c22.train import train

    cfg = reduced()
    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} is not empty; give a new folder (nothing is deleted)")
    d, full, part = out / "data", out / "runs_full", out / "runs_resumed"
    cuda = args.device == "cuda"
    free, total = torch.cuda.mem_get_info() if cuda else (None, None)       # of the device, all programs counted
    rep = {"config_sha256": sha256(cfg), "device": args.device, "workers": args.workers,
           "machine": {"platform": platform.platform(), "python": platform.python_version(), "numpy": np.__version__,
                       "scipy": scipy.__version__, "torch": torch.__version__, "processors": os.cpu_count(),
                       "start_methods": mp.get_all_start_methods(), "label_solver": _solver(),
                       "thread_variables_at_start": {k: os.environ.get(k) for k in data.THREAD_VARIABLES},
                       "gpu": torch.cuda.get_device_name(0) if cuda else None,
                       "gpu_memory_GiB": round(total / 2 ** 30, 2) if cuda else None,
                       "gpu_memory_in_use_MiB": round((total - free) / 2 ** 20) if cuda else None},
           "seconds": {}}
    t = time.time()
    data.generate(cfg, d)
    rep["seconds"]["generate"] = round(time.time() - t, 1); t = time.time()
    data.label(cfg, d, data.labelled_ids(cfg, d), workers=args.workers)
    rep["seconds"]["label"] = round(time.time() - t, 1); t = time.time()
    rep["machine"]["thread_variables_of_the_workers"] = {k: os.environ.get(k) for k in data.THREAD_VARIABLES}
    rep["check_labels"] = data.check_labels(cfg, d)
    assert rep["check_labels"]["ok"], rep["check_labels"]
    h1 = train(cfg, 5, d, full, device=args.device)
    rep["seconds"]["train_full"] = round(time.time() - t, 1); t = time.time()
    train(cfg, 5, d, part, device=args.device, stop_after_epoch=2)
    h2 = train(cfg, 5, d, part, device=args.device)
    rep["seconds"]["train_resumed"] = round(time.time() - t, 1); t = time.time()
    assert h1["status"] == h2["status"] == "finished" and h2["resumes"] == [2], (h1["status"], h2["status"], h2["resumes"])
    s1 = torch.load(full / "label_free_s5" / "state.pt", map_location="cpu", weights_only=False)
    s2 = torch.load(part / "label_free_s5" / "state.pt", map_location="cpu", weights_only=False)
    rep["resume"] = {
        "max_weight_difference": float(max((s1[p][k].float() - s2[p][k].float()).abs().max()
                                           for p in ("enc", "dec", "head") for k in s1[p])),
        "loss_full": h1["loss"], "loss_resumed": h2["loss"],
        "cap_events_full": len(h1["cap_events"]), "cap_events_resumed": len(h2["cap_events"]),
        "same_cap_steps": [s for s, _ in h1["cap_events"]] == [s for s, _ in h2["cap_events"]]}
    diff = {}
    for name in ("preds.npz", "preds_condensed.npz", "preds_base.npz"):
        with np.load(full / "label_free_s5" / name) as a, np.load(part / "label_free_s5" / name) as b:
            diff[name] = float(max(np.abs(a[k] - b[k]).max() for k in a.files))
            rep.setdefault("members_predicted", sorted(a.files))
    rep["resume"]["max_prediction_difference"] = diff
    info = json.loads((full / "label_free_s5" / "condense.json").read_text())["members"]
    amps = [v for m in info.values() for v in m["a"]]
    rep["condense"] = {"a_min": min(amps), "a_max": max(amps),
                       "energy_never_higher": all(pc <= pr * (1 + 1e-6) for m in info.values()
                                                  for pc, pr in zip(m["Pi_condensed"], m["Pi_raw"])),
                       "at_bound": int(sum(b for m in info.values() for b in m["at_bound"])),
                       "not_converged": int(sum(not c for m in info.values() for c in m["converged"]))}
    t = time.time()
    v1 = evaluate(cfg, d, full, workers=args.workers)
    rep["seconds"]["evaluate_workers"] = round(time.time() - t, 1); t = time.time()
    v2 = evaluate(cfg, d, full, workers=1)
    rep["seconds"]["evaluate_single"] = round(time.time() - t, 1)
    rep["evaluate"] = {"same_with_workers": v1 == v2, "verdict": v1["verdict"], "C1_value": v1["C1_value"],
                       "C2_value": v1["C2_value"], "raw": {k: v1["reported_readings"]["raw"][k] for k in ("C1_value", "C2_value")},
                       "sets": {s: v1["readings"]["condensed"]["5"][s]["abs_curve_err"]["n"] for s in ("eval", "former", "tested")},
                       "amplitudes": v1["amplitudes"]["5"]}
    assert v1 == v2
    (out / "smoke_report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1), flush=True)
    print("smoke test of c22 passed", flush=True)


if __name__ == "__main__":
    main()
