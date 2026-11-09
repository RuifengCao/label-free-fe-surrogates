"""Exploratory diagnostic after the G-C2.1 verdict (not under any stamp): replay the first steps of a label-free run
on the CPU, with the stamped code, the stamped configuration and the run's own seeds, and log what the run's history
cannot show: the loss of every step, the gradient norms of the three networks, the size of the last layers, and how
different the node latents of the encoder are from one another on a fixed probe instance.

    python -I diag_seed.py JOINT_DIR DATA_DIR OUT_JSONL SEED STEPS [PROBE_EVERY]

JOINT_DIR is the joint/ folder of the stamped tree (git archive prereg-c2); DATA_DIR holds manifest.json and inst/
(the regenerated instances, identical to the host's). The replay follows c2.train.train step for step: the same
torch and numpy seeds, the same initialisation, epoch order, D samples, AdamW, clipping and warm-up schedule. Only
the device differs (CPU, float32, matmul precision 'highest'), so the replay can drift from the host's run in the
last bits and, over many steps, further.
"""
import json
import os
import sys
import time
from pathlib import Path

joint, data_dir, out_path, seed, steps = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
probe_every = int(sys.argv[6]) if len(sys.argv) > 6 else 25
sys.path.insert(0, joint)
sys.path.insert(0, str(Path(joint).parent / "src"))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from c2.config import config  # noqa: E402
from c2.data import manifest  # noqa: E402
from c2.model import build, field, inputs  # noqa: E402
from c2.train import _prepare, step_loss, MATMUL_PRECISION  # noqa: E402
from fejepa.train.schedule import make_scheduler  # noqa: E402

torch.set_num_threads(int(os.environ.get("DIAG_THREADS", "1")))
cfg = config()
a = cfg["arms"]["label_free"]
tr = cfg["training"]
man = manifest(data_dir)
train_ids = [r["id"] for r in man["instances"] if r["split"] == "train"]
torch.set_float32_matmul_precision(MATMUL_PRECISION)
torch.manual_seed(seed)
rng = np.random.default_rng(seed)
dev = torch.device("cpu")
cache = {}


def item(i):
    if i not in cache:
        cache[i] = _prepare(cfg, data_dir, [train_ids[i]], dev, energy=True, labels=False)[0]
    return cache[i]


first = item(0)                                    # in_dim from the first training instance, as train() does
nets = build(cfg, first["base"].shape[-1] + 1)
enc, dec, head = nets
params = [p for net in nets for p in net.parameters()]
opt = torch.optim.AdamW(params, lr=tr["lr"], weight_decay=tr["weight_decay"])
total = a["epochs"] * len(train_ids)
sched = make_scheduler(opt, total)
probe = item(0)
probe_D = torch.tensor([0.5, 2.0, 8.0])


def gnorm(net):
    g = [p.grad.detach().reshape(-1) for p in net.parameters() if p.grad is not None]
    return float(torch.linalg.vector_norm(torch.cat(g))) if g else 0.0


@torch.no_grad()
def probe_stats():
    for net in nets:
        net.eval()
    h = enc(inputs(probe["base"], probe_D))                      # (3, N, dim)
    hc = h - h.mean(dim=1, keepdim=True)
    rel_var = (hc.pow(2).sum(-1).mean(1) / h.pow(2).sum(-1).mean(1)).tolist()   # 0 when every node has one latent
    z = field(enc, dec, head, probe["base"], probe["maps"], probe_D, cfg["map"]["T"], lift=True)
    s = (probe_D + probe["maps"]["delta"])
    e_over_s = (z[:, -1] / s).tolist()
    n = probe["maps"]["n"]
    u = z[:, :3 * n].reshape(3, n, 3)
    free = ~probe["maps"]["fixed"][:3 * n].reshape(n, 3)
    uy = [float(u[k, :, 1][free[:, 1]].std()) for k in range(3)]
    for net in nets:
        net.train()
    return {"latent_rel_var": rel_var, "e_over_s": e_over_s, "uy_std": uy,
            "dec_last_w": float(dec[-1].weight.norm()), "dec_last_b": float(dec[-1].bias.norm()),
            "head_last_w": float(head[-1].weight.norm()), "head_last_b": float(head[-1].bias.norm())}


ckpt = out_path.with_suffix(".ckpt.pt")
step, epoch, order, pos = 0, 0, None, 0
if ckpt.exists():                                 # resume: restore everything, drop log lines past the checkpoint
    st = torch.load(ckpt, map_location="cpu", weights_only=False)
    for net, k in zip(nets, ("enc", "dec", "head")):
        net.load_state_dict(st[k])
    opt.load_state_dict(st["opt"]); sched.load_state_dict(st["sched"])
    rng.bit_generator.state = st["rng"]; torch.set_rng_state(st["torch_rng"])
    step, epoch, order, pos = st["step"], st["epoch"], st["order"], st["pos"]
    keep = [l for l in out_path.read_text().splitlines() if json.loads(l).get("step", -1) <= step and "done" not in l]
    out_path.write_text("\n".join(keep) + "\n")
    out = open(out_path, "a")
    out.write(json.dumps({"resumed_at_step": step}) + "\n"); out.flush()
else:
    out = open(out_path, "a")
    out.write(json.dumps({"seed": seed, "steps": steps, "torch": torch.__version__, "threads": torch.get_num_threads(),
                          "total_steps": total}) + "\n")
    out.write(json.dumps({"step": 0, "probe": probe_stats()}) + "\n"); out.flush()
for net in nets:
    net.train()
t_start = time.time()
while step < steps:
    if order is None:
        order, pos = rng.permutation(len(train_ids)), 0
    while pos < len(order) and step < steps:
        i = int(order[pos])
        t0 = time.time()
        loss, D = step_loss(cfg, nets, item(i), rng, False, dev)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        g = {"enc": gnorm(enc), "dec": gnorm(dec), "head": gnorm(head)}
        total_norm = float(torch.nn.utils.clip_grad_norm_(params, tr["clip"]))
        opt.step()
        sched.step()
        step += 1; pos += 1
        rec = {"step": step, "inst": i, "D": [round(float(x), 4) for x in D], "loss": float(loss.detach()),
               "grad": g, "grad_total": total_norm, "lr": opt.param_groups[0]["lr"], "sec": round(time.time() - t0, 2)}
        if step % probe_every == 0:
            rec["probe"] = probe_stats()
        out.write(json.dumps(rec) + "\n"); out.flush()
        if step % 64 == 0:
            tmp = ckpt.with_suffix(".tmp")
            torch.save({"enc": enc.state_dict(), "dec": dec.state_dict(), "head": head.state_dict(),
                        "opt": opt.state_dict(), "sched": sched.state_dict(), "rng": rng.bit_generator.state,
                        "torch_rng": torch.get_rng_state(), "step": step, "epoch": epoch, "order": order,
                        "pos": pos}, tmp)
            tmp.replace(ckpt)
        if len(cache) > 64:                      # keep the memory small
            for k in list(cache)[:-32]:
                if k != 0:
                    del cache[k]
    if pos >= len(order):
        order, epoch = None, epoch + 1
out.write(json.dumps({"done": True, "step": step, "seconds": round(time.time() - t_start, 1)}) + "\n")
out.close()
