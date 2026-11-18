"""Check of a host before gate G-C2.3 runs on it, on a reduced configuration: the coarse mesh, a small model, a few
epochs, and the family seeds 7, 8, 101 and 102, which were used before G-C2.1's stamp. Nothing of the gate is drawn,
exported, solved or trained: the reduced configurations have other hashes, and the gate's held-out seed is not used.

It runs every stage the runbook runs, in the runbook's order. First, under G-C2.2's reduced configuration
(c22.smoke), three label-free runs of two epochs, which stand for G-C2.2's three runs, and their evaluation. Then,
under this gate's reduced configuration: generate; the labels of the held-out members (with worker processes) and
their check; the predictions of the three label-free states; their evaluation and the verdict of part 1; only then
the labels of the training members and the check of all labels; the supervised arm (once without interruption, once
interrupted after two epochs and resumed); its evaluation; and the verdict with the identity check, the self-check
and the comparison, whose part 1 must be the one written before. It records the machine in its report.

    python -I c23/smoke.py --repo REPO --out DIR [--device cuda] [--workers 4]
"""
import argparse
import copy
import json
import os
import platform
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True            # also in a spawned worker process, which runs this file's top level first
ROOT = Path(__file__).resolve().parents[1]
SEEDS = [5, 6, 7]


def reduced_base():
    """G-C2.2's reduced configuration, with three seeds of two epochs."""
    from c22.smoke import reduced

    cfg = reduced()
    cfg["arms"]["label_free"]["epochs"] = 2
    cfg["arms"]["label_free"]["seeds"] = list(SEEDS)
    return cfg


def reduced(base_sha: str, state_sha: dict, identity_values: dict):
    from c2.config import TESTED
    from c23.config import config

    cfg = copy.deepcopy(config())
    d = cfg["data"]
    d["n_train"], d["n_third"], d["n_eval"] = 4, 2, 2
    d["train_seed"], d["third_eval_seed"], d["eval_seed"], d["former_eval_seed"] = 7, 102, 8, 101
    d["seeds_seen_before_stamp"] = [s for s in d["seeds_seen_before_stamp"] if s not in (7, 8, 101, 102)]
    d["mesh"] = {"h": 10.0, "n_tf": 1, "hx_max": 40.0}
    d["eval_levels_mm"] = [0.5, 4.0]
    d["train_label_levels_mm"] = [0.1, 0.75, 2.5, 8.0]          # from the base level of the condensed reading up
    d["n_train_labelled"] = 4
    d["tested"] = {"BJ_T1_preloaded": dict(TESTED["BJ_T1_preloaded"])}
    cfg["model"].update(dim=32, depth=1, heads=2)
    cfg["training"]["encoder_gradient_cap"].update(window_steps=3, factor=0.5, burst_factor=1.0)
    cfg["base"]["config_sha256"] = base_sha
    lf = cfg["arms"]["label_free"]
    lf["epochs"], lf["state_sha256"] = 2, dict(state_sha)
    lf["identity"]["values"] = identity_values
    # The stand-in networks are far from the reference, so their values are tens of times those of the gate: the
    # tolerance is scaled with them, so that the check asks of a host what the gate's tolerance asks of the gate.
    largest = max([x for r in identity_values.values() for vals in r.values() for x in vals if x != float("inf")]
                  or [0.01])
    lf["identity"]["tolerance"] = 1e-4 * max(1.0, largest / 0.01)
    cfg["arms"]["supervised_512"].update(labels=4, epochs=4, seeds=[5])   # one seed is enough to run every stage
    return cfg


def main(argv=None):
    here = Path(__file__).resolve().parent                      # the script's own folder must not shadow modules
    sys.path[:] = [p for p in sys.path if not p or Path(p).resolve() != here]
    sys.path.insert(0, str(ROOT))
    ap = argparse.ArgumentParser(prog="c23-smoke")
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
    from c22 import data as data22
    from c22.config import sha256
    from c22.evaluate import evaluate as evaluate22
    from c22.train import train as train22
    from c23 import data
    from c23.evaluate import evaluate_arm, verdict
    from c23.train import train, predict_label_free, file_sha256

    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} is not empty; give a new folder (nothing is deleted)")
    cuda = args.device == "cuda"
    free, total = torch.cuda.mem_get_info() if cuda else (None, None)       # of the device, all programs counted
    rep = {"device": args.device, "workers": args.workers,
           "machine": {"platform": platform.platform(), "python": platform.python_version(), "numpy": np.__version__,
                       "scipy": scipy.__version__, "torch": torch.__version__, "processors": os.cpu_count(),
                       "start_methods": mp.get_all_start_methods(), "label_solver": _solver(),
                       "thread_variables_at_start": {k: os.environ.get(k) for k in data.THREAD_VARIABLES},
                       "gpu": torch.cuda.get_device_name(0) if cuda else None,
                       "gpu_memory_GiB": round(total / 2 ** 30, 2) if cuda else None,
                       "gpu_memory_in_use_MiB": round((total - free) / 2 ** 20) if cuda else None},
           "seconds": {}}
    # the stand-in for G-C2.2: three label-free runs under its reduced configuration, and their evaluation
    t = time.time()
    b = reduced_base()
    d22, r22 = out / "base_data", out / "base_runs"
    data22.generate(b, d22)
    data22.label(b, d22, data22.labelled_ids(b, d22), workers=args.workers)
    assert data22.check_labels(b, d22)["ok"]
    for s in SEEDS:
        assert train22(b, s, d22, r22, device=args.device)["status"] == "finished"
    v22 = evaluate22(b, d22, r22, workers=args.workers)
    rep["seconds"]["base_gate"] = round(time.time() - t, 1); t = time.time()
    states = {str(s): file_sha256(r22 / f"label_free_s{s}" / "state.pt") for s in SEEDS}
    values = {"condensed": v22["per_seed"], "raw": v22["reported_readings"]["raw"]["per_seed"]}
    # this gate, reduced
    cfg = reduced(sha256(b), states, values)
    rep["config_sha256"], rep["base_config_sha256"] = sha256(cfg), sha256(b)
    d, runs, part = out / "data", out / "runs", out / "runs_resumed"
    data.generate(cfg, d)
    rep["seconds"]["generate"] = round(time.time() - t, 1); t = time.time()
    held = ("third", "eval", "tested")
    data.label(cfg, d, data.labelled_ids(cfg, d, held), workers=args.workers)
    rep["seconds"]["label_held_out"] = round(time.time() - t, 1); t = time.time()
    rep["machine"]["thread_variables_of_the_workers"] = {k: os.environ.get(k) for k in data.THREAD_VARIABLES}
    rep["check_labels_held_out"] = data.check_labels(cfg, d, held)       # as the runbook: before the training labels
    assert rep["check_labels_held_out"]["ok"], rep["check_labels_held_out"]
    for s in SEEDS:
        h = predict_label_free(cfg, s, r22 / f"label_free_s{s}" / "state.pt", d, runs, device=args.device)
        assert h["status"] == "finished", h
    rep["seconds"]["predict_label_free"] = round(time.time() - t, 1); t = time.time()
    refused = False
    try:                                                    # a state of another seed must be refused
        predict_label_free(cfg, 5, r22 / "label_free_s6" / "state.pt", d, out / "runs_refused", device=args.device)
    except RuntimeError:
        refused = True
    assert refused
    lf = evaluate_arm(cfg, d, runs, "label_free", workers=args.workers)
    v_part = verdict(cfg, d, runs)                          # before the supervised arm: part 1 is already final
    rep["seconds"]["evaluate_label_free"] = round(time.time() - t, 1)
    rep["before_supervised"] = {"verdict": v_part["verdict"], "not_evaluated": v_part["not_evaluated"]}
    assert v_part["verdict"]["identity"] == "OK" and v_part["verdict"]["comparison"] == "INCOMPLETE", v_part["verdict"]
    assert v_part["verdict"]["self_check"] in ("PASS", "FAIL") and v_part["not_evaluated"] == ["supervised_512"]
    assert v_part["part1_same_as_first"] is True
    rows_file = (runs / "rows_label_free.json").read_bytes()
    part1_file = (runs / "verdict_part1.json").read_bytes()
    t = time.time()
    data.label(cfg, d, data.labelled_ids(cfg, d, ("train",)), workers=args.workers)      # as the runbook: after part 1
    rep["seconds"]["label_train"] = round(time.time() - t, 1); t = time.time()
    rep["check_labels"] = data.check_labels(cfg, d)
    assert rep["check_labels"]["ok"], rep["check_labels"]
    v_again = verdict(cfg, d, runs)                         # the training labels do not make the label-free rows stale
    assert ({k: x for k, x in v_again.items() if k != "cost"} == {k: x for k, x in v_part.items() if k != "cost"}
            and v_again["cost"]["training_members_labelled"] == cfg["data"]["n_train"])
    h1 = train(cfg, 5, d, runs, device=args.device)
    rep["seconds"]["train_full"] = round(time.time() - t, 1); t = time.time()
    train(cfg, 5, d, part, device=args.device, stop_after_epoch=2)
    h2 = train(cfg, 5, d, part, device=args.device)
    rep["seconds"]["train_resumed"] = round(time.time() - t, 1); t = time.time()
    assert h1["status"] == h2["status"] == "finished" and h2["resumes"] == [2], (h1["status"], h2["status"],
                                                                                  h2["resumes"])
    name = "supervised_512_s5"
    s1 = torch.load(runs / name / "state.pt", map_location="cpu", weights_only=False)
    s2 = torch.load(part / name / "state.pt", map_location="cpu", weights_only=False)
    rep["resume"] = {
        "max_weight_difference": float(max((s1[p][k].float() - s2[p][k].float()).abs().max()
                                           for p in ("enc", "dec", "head") for k in s1[p])),
        "loss_full": h1["loss"], "loss_resumed": h2["loss"], "reference_solutions": h1["reference_solutions"]}
    diff = {}
    for f in ("preds.npz", "preds_condensed.npz", "preds_base.npz"):
        with np.load(runs / name / f) as a, np.load(part / name / f) as c:
            diff[f] = float(max(np.abs(a[k] - c[k]).max() for k in a.files))
            rep.setdefault("members_predicted", sorted(a.files))
    rep["resume"]["max_prediction_difference"] = diff
    sup_w = evaluate_arm(cfg, d, runs, "supervised_512", workers=args.workers)
    rep["seconds"]["evaluate_supervised_workers"] = round(time.time() - t, 1); t = time.time()
    v1 = verdict(cfg, d, runs)
    sup_1 = evaluate_arm(cfg, d, runs, "supervised_512", workers=1)
    rep["seconds"]["evaluate_supervised_single"] = round(time.time() - t, 1); t = time.time()
    v2 = verdict(cfg, d, runs)
    rep["seconds"]["verdict"] = round(time.time() - t, 2)
    assert sup_w == sup_1 and v1 == v2
    assert (runs / "rows_label_free.json").read_bytes() == rows_file          # the label-free arm was evaluated once
    assert (runs / "verdict_part1.json").read_bytes() == part1_file           # part 1 as first written, not overwritten
    assert v1["part1_same_as_first"] is True
    assert v1.get("self_check") == v_part.get("self_check") and v1["identity"] == v_part["identity"]
    stale = json.loads(rows_file)                           # rows computed from other files must be refused
    stale["inputs"]["evaluated_labels_sha256"] = "0" * 64
    (runs / "rows_label_free.json").write_text(json.dumps(stale))
    try:
        verdict(cfg, d, runs)
        refused = False
    except RuntimeError:
        refused = True
    finally:
        (runs / "rows_label_free.json").write_bytes(rows_file)
    assert refused and verdict(cfg, d, runs) == v1
    changed = json.loads(part1_file)                        # a part 1 that differs from the first must be reported
    changed["verdict"]["self_check"] = "PASS" if changed["verdict"]["self_check"] == "FAIL" else "FAIL"
    (runs / "verdict_part1.json").write_text(json.dumps(changed, indent=1))
    try:
        differs = verdict(cfg, d, runs)["part1_same_as_first"] is False
    finally:
        (runs / "verdict_part1.json").write_bytes(part1_file)
    assert differs and verdict(cfg, d, runs) == v1
    sc = v1.get("self_check", {})
    rep["evaluate"] = {"same_with_workers": sup_w == sup_1, "verdict": v1["verdict"], "identity": v1["identity"],
                       "part1_same_as_first": v1["part1_same_as_first"],
                       "self_check": {k: sc.get(k) for k in ("pairs", "flagged", "S1", "S2", "S3", "verdict")},
                       "comparison": {k: v1["comparison"][k] for k in ("ratio_of_medians", "ratio_of_p90", "wording")},
                       "statistics_third": {arm: v1["statistics"][arm]["condensed"]["third"]
                                            for arm in v1["statistics"]},
                       "cost": v1["cost"],
                       "sets": {s: lf["readings"]["condensed"]["5"][s]["abs_curve_err"]["n"]
                                for s in ("third", "eval", "tested")}}
    assert v1["verdict"]["identity"] == "OK" and v1["verdict"]["comparison"] != "INCOMPLETE", v1["verdict"]
    (out / "smoke_report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1), flush=True)
    print("smoke test of c23 passed", flush=True)


if __name__ == "__main__":
    main()
