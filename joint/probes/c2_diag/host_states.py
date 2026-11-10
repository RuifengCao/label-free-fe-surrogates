"""The final states of G-C2.1's three label-free runs on the host (exploratory, after the verdict; not under any
stamp).

    python -I host_states.py JOINT_DIR DATA_DIR STATES_DIR OUT.json

STATES_DIR holds label_free_s0/state.pt, label_free_s1/state.pt and label_free_s2/state.pt as the host saved them after
epoch 200. They are loaded with torch.load(weights_only=True), allowing torch.torch_version.TorchVersion besides the
defaults (the history records torch.__version__). For each seed, at its final state:

- probes on nine training members (positions 0, 64, ..., 448 and 511 in the manifest's training list) at D = 0.5, 2
  and 8 mm: the relative variance of the node vectors after the input layer, after each block and after the final
  LayerNorm (the latents); the mean square and node variance of the residual stream after the input layer and after the
  first block; the mean square and node variance of the first block's attention and MLP outputs; e / (D + delta);
- the first block's MLP on the first training member: the share of its hidden units whose GELU input is below -3 at
  every node and displacement, and the share whose input varies between nodes by less than 1% of its mean square;
- the gradient norms of the encoder (whole, input layer, each block, final LayerNorm), decoder and head, the loss, and
  the loss of the starting field (the networks as c2.train.train builds them, last layers zero), on the same sixteen
  draws: members from numpy's default_rng(12345), then four displacements each by c2.train.step_loss;
- AdamW's second moments: the median of sqrt(v) over the encoder's input layer, each block, its final LayerNorm, the
  decoder and the head;
- the norms of the first block's MLP weights and biases, and the median |gain| of the final LayerNorm;
- the inputs of the GELUs in the decoder's and the head's two hidden layers over the nine members and three
  displacements: for each hidden unit its largest input, and the share of units whose largest input is below -3
  (and -5), where GELU's slope is below 0.012 in size (and 7.2e-6); and the gradient norms of each layer's weights and biases.
"""
import json
import sys
from pathlib import Path

joint, data_dir, states_dir, out_path = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
sys.path.insert(0, joint)
sys.path.insert(0, str(Path(joint).parent / "src"))

import numpy as np  # noqa: E402
import torch  # noqa: E402
from torch.torch_version import TorchVersion  # noqa: E402

from c2.config import config  # noqa: E402
from c2.data import manifest  # noqa: E402
from c2.model import build, field, inputs  # noqa: E402
from c2.train import _prepare, step_loss, MATMUL_PRECISION  # noqa: E402

torch.set_num_threads(1)
torch.set_float32_matmul_precision(MATMUL_PRECISION)
cfg = config()
man = manifest(data_dir)
train_ids = [r["id"] for r in man["instances"] if r["split"] == "train"]
dev = torch.device("cpu")
cache = {}


def item(i):
    if i not in cache:
        cache[i] = _prepare(cfg, data_dir, [train_ids[i]], dev, energy=True, labels=False)[0]
    return cache[i]


def fresh():
    torch.manual_seed(0)
    nets = build(cfg, item(0)["base"].shape[-1] + 1)
    for net in nets:
        net.train()
    return nets


def load(seed):
    with torch.serialization.safe_globals([TorchVersion]):
        st = torch.load(states_dir / f"label_free_s{seed}" / "state.pt", map_location="cpu", weights_only=True)
    nets = fresh()
    for net, k in zip(nets, ("enc", "dec", "head")):
        net.load_state_dict(st[k])
    return nets, st


def rv(t):
    tc = t - t.mean(dim=1, keepdim=True)
    return float((tc.pow(2).sum(-1).mean(1) / t.pow(2).sum(-1).mean(1)).mean())


def ms(t):
    return float(t.pow(2).sum(-1).mean())


def nv(t):
    return float((t - t.mean(dim=1, keepdim=True)).pow(2).sum(-1).mean())


D3 = torch.tensor([0.5, 2.0, 8.0])
members = [0, 64, 128, 192, 256, 320, 384, 448, 511]


@torch.no_grad()
def probe(nets, i):
    enc, dec, head = nets
    for net in nets:
        net.eval()
    it = item(i)
    x = enc.inp(inputs(it["base"], D3))
    out = {"input_rel_var": rv(x), "input_ms": ms(x), "input_node_var": nv(x), "block_rel_var": []}
    for k, blk in enumerate(enc.blocks):
        if k == 0:
            hh = blk.ln1(x)
            att = blk.attn(hh, hh, hh, need_weights=False)[0]
            pre = blk.mlp[0](blk.ln2(x + att))
            mlp = blk.mlp(blk.ln2(x + att))
            out.update({"attn_ms": ms(att), "attn_node_var": nv(att), "mlp_ms": ms(mlp), "mlp_node_var": nv(mlp)})
            if i == 0:
                dead = (pre.amax(dim=(0, 1)) < -3).float().mean()
                pv = (pre - pre.mean(dim=1, keepdim=True)).pow(2).mean(dim=(0, 1))
                flat = (pv < 0.01 * pre.pow(2).mean(dim=(0, 1))).float().mean()
                out.update({"mlp_hidden_dead_share": float(dead), "mlp_hidden_flat_share": float(flat)})
        x = blk(x)
        out["block_rel_var"].append(rv(x))
        if k == 0:
            out.update({"block1_ms": ms(x), "block1_node_var": nv(x)})
    y = enc.norm(x)
    h = enc(inputs(it["base"], D3))
    assert torch.equal(y, h)
    out["latent_rel_var"] = rv(y)
    pooled = h.mean(dim=-2, keepdim=True)
    u1 = dec[0](torch.cat([h, pooled.expand_as(h)], dim=-1))
    u2 = dec[2](dec[1](u1))
    g1 = head[0](pooled[:, 0])
    g2 = head[2](head[1](g1))
    unit_max = {"decoder layer 1": u1.amax(dim=(0, 1)), "decoder layer 2": u2.amax(dim=(0, 1)),
                "head layer 1": g1.amax(dim=0), "head layer 2": g2.amax(dim=0)}
    z = field(enc, dec, head, it["base"], it["maps"], D3, cfg["map"]["T"], lift=True)
    out["e_over_s"] = float((z[:, -1] / (D3 + it["maps"]["delta"])).mean())
    for net in nets:
        net.train()
    return out, unit_max


def gnorm(params):
    g = [p.grad.detach().reshape(-1) for p in params if p.grad is not None]
    return float(torch.linalg.vector_norm(torch.cat(g))) if g else 0.0


def grads(nets, draws):
    enc, dec, head = nets
    groups = {"encoder": list(enc.parameters()), "input layer": list(enc.inp.parameters()),
              **{f"block {k + 1}": list(b.parameters()) for k, b in enumerate(enc.blocks)},
              "final norm": list(enc.norm.parameters()), "decoder": list(dec.parameters()), "head": list(head.parameters()),
              **{f"decoder layer {k + 1} {w}": [getattr(dec[2 * k], w)] for k in range(3) for w in ("weight", "bias")},
              **{f"head layer {k + 1} {w}": [getattr(head[2 * k], w)] for k in range(3) for w in ("weight", "bias")}}
    rows, losses = [], []
    rng = np.random.default_rng(12345)
    for i in draws:
        loss, D = step_loss(cfg, nets, item(i), rng, False, dev)
        for net in nets:
            net.zero_grad(set_to_none=True)
        loss.backward()
        rows.append({k: gnorm(v) for k, v in groups.items()})
        losses.append(float(loss.detach()))
    return {k: float(np.median([r[k] for r in rows])) for k in rows[0]}, losses


def adam_v(nets, st):
    enc, dec, head = nets
    names = [(f"enc.{n}", p) for n, p in enc.named_parameters()] + [(f"dec.{n}", p) for n, p in dec.named_parameters()] \
        + [(f"head.{n}", p) for n, p in head.named_parameters()]
    state = st["opt"]["state"]
    assert len(state) == len(names)
    out = {}
    for idx, (n, p) in enumerate(names):
        v = state[idx]["exp_avg_sq"]
        assert v.shape == p.shape, n
        if n.startswith("enc.inp"):
            key = "input layer"
        elif n.startswith("enc.blocks."):
            key = f"block {int(n.split('.')[2]) + 1}"
        elif n.startswith("enc.norm"):
            key = "final norm"
        else:
            key = n.split(".")[0].replace("dec", "decoder")
        out.setdefault(key, []).append(v.sqrt().reshape(-1))
    return {k: float(torch.cat(v).median()) for k, v in out.items()}


draw_rng = np.random.default_rng(12345)
draws = [int(draw_rng.integers(len(train_ids))) for _ in range(16)]
result = {"members": [train_ids[i] for i in members], "draws": [train_ids[i] for i in draws]}
start = fresh()
for net, ln in ((start[1], start[1][-1]), (start[2], start[2][-1])):
    assert float(ln.weight.detach().abs().max()) == 0.0 and float(ln.bias.detach().abs().max()) == 0.0
_, start_losses = grads(start, draws)
result["start_losses"] = start_losses
for seed in (0, 1, 2):
    nets, st = load(seed)
    enc = nets[0]
    both = [probe(nets, i) for i in members]
    pr = [b[0] for b in both]
    umax = {k: torch.stack([b[1][k] for b in both]).amax(0) for k in both[0][1]}
    dead = {k: {"units": int(v.numel()), "share_below_-3": float((v < -3).float().mean()),
                "share_below_-5": float((v < -5).float().mean()), "largest": float(v.max())} for k, v in umax.items()}
    g, losses = grads(nets, draws)
    blk = enc.blocks[0]
    result[seed] = {
        "epoch": st["epoch"], "step": st["step"],
        "probe_first_member": pr[0],
        "probe_median_over_members": {k: float(np.median([p[k] for p in pr])) for k in pr[0]
                                      if not isinstance(pr[0][k], list) and not k.startswith("mlp_hidden")},
        "latent_rel_var_by_member": [p["latent_rel_var"] for p in pr],
        "grad_median": g, "losses": losses,
        "loss_minus_start_mean": float(np.mean(np.array(losses) - np.array(start_losses))),
        "adam_sqrt_v_median": adam_v(nets, st),
        "block1_mlp_norms": {"w1": float(blk.mlp[0].weight.detach().norm()), "b1": float(blk.mlp[0].bias.detach().norm()),
                             "w2": float(blk.mlp[2].weight.detach().norm()), "b2": float(blk.mlp[2].bias.detach().norm())},
        "final_norm_gain_abs_median": float(enc.norm.weight.detach().abs().median()),
        "gelu_inputs_over_nine_members": dead,
    }
out_path.write_text(json.dumps(result, indent=1))
for seed in (0, 1, 2):
    r = result[seed]
    p, m = r["probe_first_member"], r["probe_median_over_members"]
    print(f"=== seed {seed}: epoch {r['epoch']}, step {r['step']}")
    print(f"  latents, relative variance: first member {p['latent_rel_var']:.4f}; nine members "
          f"{min(r['latent_rel_var_by_member']):.4f} to {max(r['latent_rel_var_by_member']):.4f}")
    print(f"  first member: input layer {p['input_rel_var']:.3f}; after each block " + ", ".join(f"{x:.4f}" for x in p["block_rel_var"]))
    print(f"  first member: input layer mean square {p['input_ms']:.0f} (node variance {p['input_node_var']:.0f}); after block 1 "
          f"{p['block1_ms']:.0f} ({p['block1_node_var']:.0f}); block 1 attention {p['attn_ms']:.0f} ({p['attn_node_var']:.1f}), "
          f"MLP {p['mlp_ms']:.0f} ({p['mlp_node_var']:.1f})")
    print(f"  medians over the nine members: after block 1 mean square {m['block1_ms']:.0f}, node variance {m['block1_node_var']:.1f}; "
          f"MLP {m['mlp_ms']:.0f} ({m['mlp_node_var']:.1f}); e/(D+delta) {m['e_over_s']:.4f}")
    print(f"  block 1 MLP hidden units: below -3 everywhere {100 * p['mlp_hidden_dead_share']:.1f}%, nearly the same at every node "
          f"{100 * p['mlp_hidden_flat_share']:.1f}%; norms {json.dumps({k: round(v, 2) for k, v in r['block1_mlp_norms'].items()})}")
    print(f"  final LayerNorm median |gain| {r['final_norm_gain_abs_median']:.4f}")
    print("  gradient norms (median over 16 draws): " + ", ".join(f"{k} {v:.3g}" for k, v in r["grad_median"].items()))
    print("  AdamW sqrt(v) medians: " + ", ".join(f"{k} {v:.3g}" for k, v in r["adam_sqrt_v_median"].items()))
    print(f"  loss minus the starting field's on the same draws: mean {r['loss_minus_start_mean']:+.4f}")
    for k, v in r["gelu_inputs_over_nine_members"].items():
        print(f"  {k} ({v['units']} units): largest GELU input over the nine members {v['largest']:.3g}; units below -3 at every "
              f"node and displacement {100 * v['share_below_-3']:.1f}%, below -5 {100 * v['share_below_-5']:.1f}%")
