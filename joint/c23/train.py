"""The two arms of gate G-C2.3.

supervised  Train one seed of the supervised arm, with checkpoints and resume, then predict the held-out and tested
            instances in both readings. The run is G-C2.2's (c22.train.train: the same network, training members,
            steps, AdamW with the recipe's beta2, the cap on the encoder's gradient, clipping, cosine schedule,
            checkpoints, attempts.log) with one change: the loss of a step is G-C2.1's supervised loss
            (c2.train.step_loss) on 4 of the labelled levels of the step's member, in place of the energy. The seed
            is set as in the label-free run, before the network is built. The members come in a fresh random order
            every epoch; the order is the label-free run's in the first epoch only, because the two losses draw
            differently from the random stream. Before a run starts or resumes, the training members' instance
            and label files are compared with the manifest and the ledger; the SHA-256 of their ledger entries is
            kept in the run's history, and a run does not resume on other labels.

label-free  Nothing is trained. A state file written by G-C2.2's run of the same seed is read, after its SHA-256 has
            been found equal to the one the configuration pins, and the network predicts this gate's held-out and
            tested instances in both readings (c22.train.predict, unchanged).

Both write <runs>/<arm>_s<seed>/{history.json, attempts.log, preds.npz, preds_condensed.npz, preds_base.npz,
condense.json}; the supervised arm also writes state.pt. No reference solution enters a prediction.
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np

from c2.model import build
from c2.train import MATMUL_PRECISION, verify_repository, _check_manifest, _load_state, _prepare, step_loss
from c22.train import PREDICTION_FILES, _now, _note, cap_encoder_gradient, predict, predictions_written  # noqa: F401
from .data import _replace, _write_json, check_files, ledger_sha256

SUPERVISED = "supervised_512"
LABEL_FREE = "label_free"


def train(cfg: dict, seed: int, data_dir, out_dir, device: str = "cuda", stop_after_epoch: int | None = None) -> dict:
    """Train (or resume) the supervised arm and write out_dir/supervised_512_s<seed>/."""
    from .config import sha256

    arm = SUPERVISED
    a = cfg["arms"][arm]
    if seed not in a["seeds"]:
        raise RuntimeError("the seed is not in the configuration")
    man = _check_manifest(cfg, data_dir)
    cfg_sha = sha256(cfg)
    run = Path(out_dir) / f"{arm}_s{seed}"
    run.mkdir(parents=True, exist_ok=True)
    _note(run, "start")
    print(f"start {arm}_s{seed} {_now()}", flush=True)
    hp = run / "history.json"
    if hp.exists():
        old = json.loads(hp.read_text())
        if old.get("config_sha256") != cfg_sha:
            raise RuntimeError(f"{run} holds a run of another configuration; use a fresh runs directory")
        if str(old.get("status", "")).startswith("non-finite"):
            _note(run, "returned: " + old["status"])
            return old
        if old.get("status") == "finished" and predictions_written(run):
            _note(run, "returned: finished")
            return old
    verify_repository(cfg)
    import torch
    from fejepa.train.schedule import make_scheduler

    torch.set_float32_matmul_precision(MATMUL_PRECISION)
    ids = [r["id"] for r in man["instances"] if r["split"] == "train"]
    assert len(ids) == cfg["data"]["n_train"] == a["labels"], "the manifest does not hold the configured training set"
    check_files(data_dir, ids)                             # instances and labels as the manifest and the ledger say
    labels_sha, n_labelled = ledger_sha256(data_dir, ids)
    assert n_labelled == len(ids), "a training member has no label"
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    dev = torch.device(device)
    items = _prepare(cfg, data_dir, ids, dev, energy=False, labels=True)
    n_lab = sorted({int(it["D_lab"].shape[0]) for it in items})
    assert n_lab == [len(cfg["data"]["train_label_levels_mm"])], f"labelled levels per training member: {n_lab}"
    nets = build(cfg, items[0]["base"].shape[-1] + 1)
    for net in nets:
        net.to(dev)
    enc = nets[0]
    params = [p for net in nets for p in net.parameters()]
    tr = cfg["training"]
    cap = tr["encoder_gradient_cap"]
    opt = torch.optim.AdamW(params, lr=tr["lr"], weight_decay=tr["weight_decay"], betas=(0.9, tr["beta2"]))
    total = a["epochs"] * len(items)
    sched = make_scheduler(opt, total)
    window = collections.deque(maxlen=cap["window_steps"])
    hist = {"config_sha256": cfg_sha, "arm": arm, "seed": seed, "torch": torch.__version__, "device": str(dev),
            "gpu": torch.cuda.get_device_name(0) if dev.type == "cuda" else None,
            "matmul_precision": torch.get_float32_matmul_precision(), "total_steps": total,
            "betas": [0.9, tr["beta2"]], "cap": {k: cap[k] for k in ("factor", "window_steps", "burst_factor")},
            "reference_solutions": int(sum(it["D_lab"].shape[0] for it in items)),
            "training_labels_sha256": labels_sha,
            "loss": [], "epoch_seconds": [], "cap_events": [], "bursts": [], "resumes": [],
            "resumed_from_epoch": None}
    start_epoch, step = 0, 0
    ck = run / "state.pt"
    if ck.exists():
        s = _load_state(ck)
        if s["history"].get("config_sha256") != cfg_sha:
            raise RuntimeError(f"{ck} belongs to another configuration; use a fresh runs directory")
        if s["history"].get("training_labels_sha256") != labels_sha:
            raise RuntimeError(f"{ck} was trained on other labels than those now in the ledger; stop and report")
        for net, k in zip(nets, ("enc", "dec", "head")):
            net.load_state_dict(s[k])
        opt.load_state_dict(s["opt"]); sched.load_state_dict(s["sched"])
        rng.bit_generator.state = s["rng"]; torch.set_rng_state(s["torch_rng"])
        window.extend(s["window"])
        start_epoch, step, hist = s["epoch"], s["step"], s["history"]
        hist["resumed_from_epoch"] = start_epoch
        hist.setdefault("resumes", []).append(start_epoch)
        _note(run, f"resumed from epoch {start_epoch}")
        if start_epoch >= a["epochs"]:
            hist.setdefault("status", "finished"); hist.setdefault("steps", step)
            if not hp.exists():
                _write_json(hp, hist)
            if not predictions_written(run) and not predict(cfg, nets, data_dir, run, dev):
                hist["status"] = "non-finite predictions"
                _write_json(hp, hist)
            _note(run, "ended: " + hist["status"])
            return hist
    for net in nets:
        net.train()
    status = "running"
    every = tr["checkpoint_every_epochs"]
    for epoch in range(start_epoch, a["epochs"]):
        t0 = time.perf_counter()
        order = rng.permutation(len(items))
        loss_sum = 0.0
        for i in order:
            loss, _ = step_loss(cfg, nets, items[i], rng, True, dev)
            if not torch.isfinite(loss):
                status = f"non-finite loss at step {step + 1}"
                break
            opt.zero_grad(set_to_none=True)
            loss.backward()
            _, ratio, scale = cap_encoder_gradient(enc, window, cap)
            if scale is not None:
                hist["cap_events"].append([step + 1, round(ratio, 3)])
            if ratio is not None and ratio > cap["burst_factor"]:
                hist["bursts"].append([step + 1, round(ratio, 3)])
            torch.nn.utils.clip_grad_norm_(params, tr["clip"])
            opt.step()
            sched.step()
            step += 1
            loss_sum += float(loss.detach())
        if status != "running":
            break
        if dev.type == "cuda":
            torch.cuda.synchronize()
        hist["loss"].append(loss_sum / len(items))
        hist["epoch_seconds"].append(round(time.perf_counter() - t0, 2))
        done = epoch + 1
        if done % every == 0 or done == a["epochs"]:
            tmp = ck.with_suffix(".tmp")
            with open(tmp, "wb") as fh:                    # on the disk before it takes the checkpoint's place
                torch.save({"enc": nets[0].state_dict(), "dec": nets[1].state_dict(), "head": nets[2].state_dict(),
                            "opt": opt.state_dict(), "sched": sched.state_dict(), "rng": rng.bit_generator.state,
                            "torch_rng": torch.get_rng_state(), "window": list(window), "epoch": done, "step": step,
                            "history": hist}, fh)
                fh.flush()
                os.fsync(fh.fileno())
            _replace(tmp, ck)
        print(f"epoch {done} loss {hist['loss'][-1]:.6g} {hist['epoch_seconds'][-1]} s; cap events "
              f"{len(hist['cap_events'])}, bursts {len(hist['bursts'])}", flush=True)
        if stop_after_epoch is not None and done >= stop_after_epoch:
            return hist
    hist["status"] = "finished" if status == "running" else status
    hist["steps"] = step
    if dev.type == "cuda":
        hist["peak_memory_GiB"] = torch.cuda.max_memory_allocated() / 2 ** 30
    _write_json(hp, hist)
    if hist["status"] == "finished":
        del items                                          # the reference fields are not needed for the predictions
        if not predict(cfg, nets, data_dir, run, dev):
            hist["status"] = "non-finite predictions"
            _write_json(hp, hist)
    _note(run, "ended: " + hist["status"])
    return hist


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def predict_label_free(cfg: dict, seed: int, state_path, data_dir, out_dir, device: str = "cuda") -> dict:
    """Read G-C2.2's state of the given seed and write out_dir/label_free_s<seed>/ with its predictions on this
    gate's members. Refuses a state file whose SHA-256 is not the pinned one, or that was not written by a finished
    run of G-C2.2's configuration. An end without finite predictions is final, as a supervised run's non-finite stop
    is: the record is returned and nothing is predicted again."""
    from .config import sha256

    arm = LABEL_FREE
    a = cfg["arms"][arm]
    if seed not in a["seeds"]:
        raise RuntimeError("the seed is not in the configuration")
    want = a["state_sha256"][str(seed)]
    got = file_sha256(state_path)
    if got != want:
        raise RuntimeError(f"the state file has SHA-256 {got}; the configuration pins {want}")
    man = _check_manifest(cfg, data_dir)
    cfg_sha = sha256(cfg)
    run = Path(out_dir) / f"{arm}_s{seed}"
    run.mkdir(parents=True, exist_ok=True)
    hp = run / "history.json"
    if hp.exists():
        old = json.loads(hp.read_text())
        if old.get("config_sha256") != cfg_sha:
            raise RuntimeError(f"{run} holds a run of another configuration; use a fresh runs directory")
        if str(old.get("status", "")).startswith("non-finite"):
            _note(run, "returned: " + old["status"])
            return old
        if old.get("status") == "finished" and predictions_written(run):
            _note(run, "returned: finished")
            return old
    _note(run, "start: predictions of the state trained in " + cfg["base"]["gate"])
    print(f"start {arm}_s{seed} {_now()}", flush=True)
    s = _load_state(state_path)
    sh = s["history"]
    if sh.get("config_sha256") != cfg["base"]["config_sha256"] or sh.get("arm") != arm or sh.get("seed") != seed:
        raise RuntimeError("the state was not written by this seed's run of the base gate")
    if s["epoch"] != a["epochs"] or s["step"] != a["epochs"] * cfg["data"]["n_train"]:
        raise RuntimeError(f"the state is not the end of the run: epoch {s['epoch']}, step {s['step']}")
    verify_repository(cfg)
    import torch

    torch.set_float32_matmul_precision(MATMUL_PRECISION)
    dev = torch.device(device)
    first = [r["id"] for r in man["instances"] if r["split"] == "train"][0]
    it = _prepare(cfg, data_dir, [first], dev, energy=False, labels=False)[0]
    nets = build(cfg, it["base"].shape[-1] + 1)
    for net, k in zip(nets, ("enc", "dec", "head")):
        net.load_state_dict(s[k])
        net.to(dev)
    t0 = time.perf_counter()
    ok = predict(cfg, nets, data_dir, run, dev)
    hist = {"config_sha256": cfg_sha, "arm": arm, "seed": seed, "torch": torch.__version__, "device": str(dev),
            "gpu": torch.cuda.get_device_name(0) if dev.type == "cuda" else None,
            "matmul_precision": torch.get_float32_matmul_precision(),
            "trained_in": {"gate": cfg["base"]["gate"], "config_sha256": sh["config_sha256"], "state_sha256": got,
                           "epoch": int(s["epoch"]), "step": int(s["step"]), "torch": sh.get("torch")},
            "predict_seconds": round(time.perf_counter() - t0, 2),
            "status": "finished" if ok else "non-finite predictions"}
    _write_json(hp, hist)
    _note(run, "ended: " + hist["status"])
    return hist
