"""Train one seed of gate G-C2.2, with checkpoints and resume, then predict the held-out and tested instances at the
evaluation levels in both readings.

The run is G-C2.1's label-free run (c2.train.train: the same loss, sampling, AdamW, clipping, cosine schedule, one
instance a step in a fresh random order every epoch) with the stability recipe of the configuration and nothing else:

  beta2   AdamW's second-moment coefficient is the configuration's (0.99) instead of the default 0.999;
  cap     before the global clipping, the encoder's gradient is scaled down to at most `factor` times the median of
          its norm over the previous `window_steps` steps (norms before any scaling), once that many steps have run.

After training, each held-out and tested member's fields at the evaluation levels are written twice: the network's
field (preds.npz, G-C2.1's raw reading) and the amplitude-condensed field (preds_condensed.npz, c22.condense), with
the network's field at the base level (preds_base.npz), the amplitudes and the state of each amplitude's iteration
(condense.json), so that the condensed fields can be computed again from the files. No reference solution enters.

Every start, resume and end of a run is written to its attempts.log, which is the complete record. The list
`resumes` of history.json is not: a resume enters it only if a checkpoint or the history is written after it."""
from __future__ import annotations

import collections
import datetime
import json
import os
import time
from pathlib import Path

import numpy as np

from c2.data import manifest
from c2.model import build, field
from c2.train import MATMUL_PRECISION, verify_repository, _check_manifest, _load_state, _prepare, step_loss
from .data import _replace, _write_json

PREDICTION_FILES = ("preds.npz", "preds_condensed.npz", "preds_base.npz", "condense.json")


def _now() -> str:
    """Local time with its offset from UTC, in ASCII on every system (a zone's name is not)."""
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _note(run: Path, text: str) -> None:
    """One line in the run's attempts.log (as c2.train._note, with the time as above)."""
    with open(run / "attempts.log", "a", encoding="ascii") as fh:
        fh.write(f"{_now()} {text}\n")
        fh.flush()


def _gnorm(net) -> float:
    import torch

    g = [p.grad.detach().reshape(-1) for p in net.parameters() if p.grad is not None]
    return float(torch.linalg.vector_norm(torch.cat(g))) if g else 0.0


def cap_encoder_gradient(enc, window, cap: dict) -> tuple[float, float | None, float | None]:
    """The stability recipe's cap, applied to the encoder's gradient in place. Returns the norm before scaling, its
    ratio to the median of the window (None until the window is full), and the scale applied (None if not scaled).
    The window receives the norm before scaling."""
    g = _gnorm(enc)
    ratio = scale = None
    if len(window) == cap["window_steps"]:
        med = float(np.median(window))
        # a zero median: no gradient gives the ratio 0, any gradient is cut to zero and recorded with an infinite ratio
        ratio = g / med if med > 0 else (0.0 if g == 0 else float("inf"))
        if g > cap["factor"] * med:
            scale = cap["factor"] * med / g
            for p in enc.parameters():
                if p.grad is not None:
                    p.grad.mul_(scale)
    window.append(g)
    return g, ratio, scale


def train(cfg: dict, seed: int, data_dir, out_dir, device: str = "cuda", stop_after_epoch: int | None = None) -> dict:
    """Train (or resume) and write out_dir/label_free_s<seed>/{state.pt, history.json, attempts.log, preds.npz,
    preds_condensed.npz, preds_base.npz, condense.json}."""
    from .config import sha256

    arm = "label_free"
    a = cfg["arms"][arm]
    if seed not in a["seeds"]:
        raise RuntimeError("the seed is not in the configuration")
    if seed in cfg["training_seeds_seen_before_stamp"]:
        raise RuntimeError("a training seed used before the stamp")
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
    assert len(ids) == cfg["data"]["n_train"], "the manifest does not hold the configured training set"
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    dev = torch.device(device)
    items = _prepare(cfg, data_dir, ids, dev, energy=True, labels=False)
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
            "loss": [], "epoch_seconds": [], "cap_events": [], "bursts": [], "resumes": [],
            "resumed_from_epoch": None}
    start_epoch, step = 0, 0
    ck = run / "state.pt"
    if ck.exists():
        s = _load_state(ck)
        if s["history"].get("config_sha256") != cfg_sha:
            raise RuntimeError(f"{ck} belongs to another configuration; use a fresh runs directory")
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
            loss, _ = step_loss(cfg, nets, items[i], rng, False, dev)
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
    if hist["status"] == "finished" and not predict(cfg, nets, data_dir, run, dev):
        hist["status"] = "non-finite predictions"
        _write_json(hp, hist)
    _note(run, "ended: " + hist["status"])
    return hist


def predictions_written(run: Path) -> bool:
    return all((Path(run) / f).exists() for f in PREDICTION_FILES)


def predict(cfg, nets, data_dir, run, dev) -> bool:
    """Fields of the held-out and tested instances at the evaluation levels, (L, nfull) per instance id, float32:
    the network's fields (preds.npz) and the amplitude-condensed fields (preds_condensed.npz), with the network's
    field at the base level, (nfull,) per instance id (preds_base.npz), and the amplitudes (condense.json). If any
    value is not finite, nothing is written and False is returned."""
    import torch

    from .condense import condense

    rd = cfg["evaluation"]["readings"]["condensed"]
    tr = cfg["training"]
    man = manifest(data_dir)
    ids = [r["id"] for r in man["instances"] if r["split"] in cfg["evaluation"]["sets"]]
    lv = torch.as_tensor([rd["base_level_mm"]] + list(cfg["data"]["eval_levels_mm"]), dtype=torch.float32, device=dev)
    D = lv[1:]
    for net in nets:
        net.eval()
    raw, cond, base, info = {}, {}, {}, {}
    for iid in ids:
        it = _prepare(cfg, data_dir, [iid], dev, energy=True, labels=False)[0]
        mp, E = it["maps"], it["energy"]
        nonneg = torch.cat([mp["nonneg"], torch.zeros(mp["n_z"] - mp["nonneg"].numel(), dtype=torch.bool, device=dev)])
        with torch.no_grad():
            zall = field(*nets, it["base"], mp, lv, cfg["map"]["T"], lift=cfg["model"]["lift"] == "web")
        z0, z = zall[:1].expand(D.numel(), -1), zall[1:]
        a, st = condense(E, z0, z, D, nonneg, tr["bubble_newton_steps"], rd["a_min"], rd["a_max"],
                         rd["max_evaluations"], rd["rtol"])
        with torch.no_grad():
            zc = z0 + a[:, None] * (z - z0)
            zc = torch.where(nonneg, zc.clamp_min(0.0), zc)
            Pr, Pc = E.energy(z, D, iters=tr["bubble_newton_steps"]), E.energy(zc, D, iters=tr["bubble_newton_steps"])
        raw[iid], cond[iid] = z.float().cpu().numpy(), zc.float().cpu().numpy()
        base[iid] = zall[0].float().cpu().numpy()
        info[iid] = {"a": a.double().tolist(), "rel_slope": st["rel_slope"].double().tolist(),
                     "at_bound": [bool(v) for v in st["at_bound"]], "converged": [bool(v) for v in st["converged"]],
                     "evaluations": int(st["evals"]), "Pi_raw": Pr.double().tolist(), "Pi_condensed": Pc.double().tolist()}
        del it, E
    for net in nets:
        net.train()
    finite = all(np.isfinite(v).all() for arrays in (raw, cond, base) for v in arrays.values()) \
        and all(np.isfinite(r["a"]).all() for r in info.values())
    if not finite:
        return False
    run = Path(run)
    for name, arrays in (("preds.npz", raw), ("preds_condensed.npz", cond), ("preds_base.npz", base)):
        tmp = run / (name + ".tmp")
        with open(tmp, "wb") as fh:
            np.savez_compressed(fh, **arrays)
        _replace(tmp, run / name)
    tmp = run / "condense.tmp"                             # written last: with it the predictions are whole
    tmp.write_text(json.dumps({"levels_mm": list(cfg["data"]["eval_levels_mm"]), "reading": rd, "members": info}))
    _replace(tmp, run / "condense.json")
    return True
