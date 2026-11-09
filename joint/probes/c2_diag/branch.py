"""Branch a CPU replay of a G-C2.1 label-free seed at one of its checkpoints, change one thing, and continue
(exploratory, after the verdict; not under any stamp).

    python -I branch.py JOINT_DIR DATA_DIR CKPT REPLAY_JSONL OUT_JSONL VARIANT STEPS [PROBE_EVERY]

CKPT is a checkpoint that diag_seed.py wrote (networks, optimiser, schedule, both random generators, place in the
epoch); REPLAY_JSONL is that replay's record, which supplies the encoder gradient norms of the 256 steps before the
branch. The branch then takes STEPS steps on the same members and displacements as the replay, recorded as
diag_seed.py records them, with a probe every PROBE_EVERY steps (default 16; a probe draws no random numbers, so it
does not change the trajectory). VARIANT is one of:

  control   nothing changed: must reproduce the replay bit for bit;
  enc_cap   before clipping, the encoder's gradient is scaled down to at most CAP = 5 times the median of its norm
            over the previous 256 steps (0.67% and 0.92% of the replays' steps exceed 5 times, the bursts included;
            the bursts before the collapses were 11 to 92 times);
  beta2     AdamW's beta2 is 0.99 from the branch on, instead of 0.999;
  lr_half   the learning rate is halved from the branch on.
"""
import collections
import json
import os
import sys
import time
from pathlib import Path

joint, data_dir, ckpt_path, replay_path, out_path = (sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]),
                                                       Path(sys.argv[4]), Path(sys.argv[5]))
variant, steps = sys.argv[6], int(sys.argv[7])
probe_every = int(sys.argv[8]) if len(sys.argv) > 8 else 16
assert variant in ("control", "enc_cap", "beta2", "lr_half"), variant
CAP, WINDOW = 5.0, 256
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
dev = torch.device("cpu")
cache = {}


def item(i):
    if i not in cache:
        cache[i] = _prepare(cfg, data_dir, [train_ids[i]], dev, energy=True, labels=False)[0]
    return cache[i]


st = torch.load(ckpt_path, map_location="cpu", weights_only=False)
seed = None
for l in open(replay_path):
    r = json.loads(l)
    if "seed" in r:
        seed = r["seed"]
        break
torch.manual_seed(seed)                      # as diag_seed.py, so that build() draws the same initial weights
first = item(0)
nets = build(cfg, first["base"].shape[-1] + 1)
enc, dec, head = nets
params = [p for net in nets for p in net.parameters()]
opt = torch.optim.AdamW(params, lr=tr["lr"], weight_decay=tr["weight_decay"])
total = a["epochs"] * len(train_ids)
sched = make_scheduler(opt, total)
for net, k in zip(nets, ("enc", "dec", "head")):
    net.load_state_dict(st[k])
opt.load_state_dict(st["opt"])
sched.load_state_dict(st["sched"])
rng = np.random.default_rng(seed)
rng.bit_generator.state = st["rng"]
torch.set_rng_state(st["torch_rng"])
step, epoch, order, pos = st["step"], st["epoch"], st["order"], st["pos"]
if variant == "beta2":
    for g in opt.param_groups:
        g["betas"] = (g["betas"][0], 0.99)
if variant == "lr_half":
    sched.base_lrs = [b * 0.5 for b in sched.base_lrs]
    for g in opt.param_groups:
        g["lr"] *= 0.5
before = [r for r in (json.loads(l) for l in open(replay_path) if l.strip()) if "loss" in r and r["step"] <= step]
assert [r["step"] for r in before][-WINDOW:] == list(range(step - WINDOW + 1, step + 1)), "replay record incomplete"
window = collections.deque((r["grad"]["enc"] for r in before[-WINDOW:]), maxlen=WINDOW)
probe = item(0)
probe_D = torch.tensor([0.5, 2.0, 8.0])


def gnorm(net):
    g = [p.grad.detach().reshape(-1) for p in net.parameters() if p.grad is not None]
    return float(torch.linalg.vector_norm(torch.cat(g))) if g else 0.0


def _rel_var(t):                             # (3, N, dim) -> mean over the three displacements of the relative variance
    tc = t - t.mean(dim=1, keepdim=True)
    return float((tc.pow(2).sum(-1).mean(1) / t.pow(2).sum(-1).mean(1)).mean())


def _ms(t):                                  # mean over displacements and nodes of the squared norm of a node's vector
    return float(t.pow(2).sum(-1).mean())


def _nv(t):                                  # the same for its distance from the mean over the nodes
    return float((t - t.mean(dim=1, keepdim=True)).pow(2).sum(-1).mean())


@torch.no_grad()
def probe_stats():
    for net in nets:
        net.eval()
    h = enc(inputs(probe["base"], probe_D))
    hc = h - h.mean(dim=1, keepdim=True)
    rel_var = (hc.pow(2).sum(-1).mean(1) / h.pow(2).sum(-1).mean(1)).tolist()
    x = enc.inp(inputs(probe["base"], probe_D))     # the same forward pass, stage by stage
    stages, ms, nv = [_rel_var(x)], [_ms(x)], [_nv(x)]
    for k, blk in enumerate(enc.blocks):
        if k == 0:                                  # the first block's two branches, as Block.forward adds them
            hh = blk.ln1(x)
            att = blk.attn(hh, hh, hh, need_weights=False)[0]
            mlp = blk.mlp(blk.ln2(x + att))
            first = {"attn_ms": _ms(att), "attn_node_var": _nv(att), "mlp_ms": _ms(mlp), "mlp_node_var": _nv(mlp)}
        x = blk(x)
        stages.append(_rel_var(x)); ms.append(_ms(x)); nv.append(_nv(x))
    y = enc.norm(x)
    stages.append(_rel_var(y)); ms.append(_ms(y)); nv.append(_nv(y))
    assert torch.equal(y, h), "staged forward differs from the encoder's"
    gain = enc.norm.weight.detach()
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
            "head_last_w": float(head[-1].weight.norm()), "head_last_b": float(head[-1].bias.norm()),
            "stage_rel_var": stages, "stage_ms": ms, "stage_node_var": nv, "first_block": first,
            "norm_gain": float(gain.norm()), "norm_gain_abs_median": float(gain.abs().median()),
            "norm_bias": float(enc.norm.bias.detach().norm())}


out = open(out_path, "w")
out.write(json.dumps({"seed": seed, "branch_at_step": step, "variant": variant, "steps": steps,
                      "cap": CAP if variant == "enc_cap" else None, "torch": torch.__version__,
                      "threads": torch.get_num_threads()}) + "\n")
out.write(json.dumps({"step": step, "probe": probe_stats()}) + "\n"); out.flush()
for net in nets:
    net.train()
end, t_start = step + steps, time.time()
while step < end:
    if order is None:
        order, pos = rng.permutation(len(train_ids)), 0
    while pos < len(order) and step < end:
        i = int(order[pos])
        t0 = time.time()
        loss, D = step_loss(cfg, nets, item(i), rng, False, dev)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        g = {"enc": gnorm(enc), "dec": gnorm(dec), "head": gnorm(head)}
        cap_scale = None
        if variant == "enc_cap":
            limit = CAP * float(np.median(window))
            if g["enc"] > limit:
                cap_scale = limit / g["enc"]
                for p in enc.parameters():
                    if p.grad is not None:
                        p.grad.mul_(cap_scale)
        window.append(g["enc"])
        total_norm = float(torch.nn.utils.clip_grad_norm_(params, tr["clip"]))
        opt.step()
        sched.step()
        step += 1; pos += 1
        rec = {"step": step, "inst": i, "D": [round(float(x), 4) for x in D], "loss": float(loss.detach()),
               "grad": g, "grad_total": total_norm, "lr": opt.param_groups[0]["lr"], "sec": round(time.time() - t0, 2)}
        if cap_scale is not None:
            rec["cap_scale"] = cap_scale
        if step % probe_every == 0:
            rec["probe"] = probe_stats()
        out.write(json.dumps(rec) + "\n"); out.flush()
        if len(cache) > 64:
            for k in list(cache)[:-32]:
                if k != 0:
                    del cache[k]
    if pos >= len(order):
        order, epoch = None, epoch + 1
out.write(json.dumps({"done": True, "step": step, "seconds": round(time.time() - t_start, 1)}) + "\n")
out.close()
