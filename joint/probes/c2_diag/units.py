"""The decoder's and head's hidden units in replay checkpoints before and after their collapses (exploratory, after the
G-C2.1 verdict).

    python -I units.py JOINT_DIR DATA_DIR OUT.json LABEL=CKPT [LABEL=CKPT ...]

Each CKPT is a checkpoint that diag_seed.py wrote (networks under the keys enc, dec and head). For each, on the same nine
training members and three displacements as host_states.py: the relative variance of the latents (median over the
members), and for the first and second hidden layers of the decoder and of the head, the largest GELU input of each
unit over every node, displacement and member, with the share of units whose largest input is below -3 and below -5.
"""
import json
import sys
from pathlib import Path

joint, data_dir, out_path = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
pairs = [a.split("=", 1) for a in sys.argv[4:]]
sys.path.insert(0, joint)
sys.path.insert(0, str(Path(joint).parent / "src"))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from c2.config import config  # noqa: E402
from c2.data import manifest  # noqa: E402
from c2.model import build, inputs  # noqa: E402
from c2.train import _prepare, MATMUL_PRECISION  # noqa: E402

torch.set_num_threads(1)
torch.set_float32_matmul_precision(MATMUL_PRECISION)
cfg = config()
man = manifest(data_dir)
train_ids = [r["id"] for r in man["instances"] if r["split"] == "train"]
dev = torch.device("cpu")
members = [0, 64, 128, 192, 256, 320, 384, 448, 511]
items = {i: _prepare(cfg, data_dir, [train_ids[i]], dev, energy=True, labels=False)[0] for i in members}
D3 = torch.tensor([0.5, 2.0, 8.0])
result = {}
for label, path in pairs:
    # diag_seed.py's own checkpoint, which holds a numpy array besides tensors
    st = torch.load(path, map_location="cpu", weights_only=False)
    torch.manual_seed(0)
    nets = build(cfg, items[0]["base"].shape[-1] + 1)
    for net, k in zip(nets, ("enc", "dec", "head")):
        net.load_state_dict(st[k])
        net.eval()
    enc, dec, head = nets
    rvs, umax = [], {}
    with torch.no_grad():
        for i in members:
            h = enc(inputs(items[i]["base"], D3))
            hc = h - h.mean(dim=1, keepdim=True)
            rvs.append(float((hc.pow(2).sum(-1).mean(1) / h.pow(2).sum(-1).mean(1)).mean()))
            pooled = h.mean(dim=-2, keepdim=True)
            u1 = dec[0](torch.cat([h, pooled.expand_as(h)], dim=-1))
            u2 = dec[2](dec[1](u1))
            g1 = head[0](pooled[:, 0])
            g2 = head[2](head[1](g1))
            for k, v in (("decoder layer 1", u1.amax(dim=(0, 1))), ("decoder layer 2", u2.amax(dim=(0, 1))),
                         ("head layer 1", g1.amax(dim=0)), ("head layer 2", g2.amax(dim=0))):
                umax[k] = v if k not in umax else torch.maximum(umax[k], v)
    result[label] = {"step": st["step"], "latent_rel_var_median": float(np.median(rvs)),
                     **{k: {"share_below_-3": float((v < -3).float().mean()), "share_below_-5": float((v < -5).float().mean()),
                            "largest": float(v.max())} for k, v in umax.items()}}
out_path.write_text(json.dumps(result, indent=1))
for label, r in result.items():
    print(f"{label} (step {r['step']}): latents {r['latent_rel_var_median']:.4f}")
    for k in ("decoder layer 1", "decoder layer 2", "head layer 1", "head layer 2"):
        v = r[k]
        print(f"   {k}: largest GELU input {v['largest']:.3g}; below -3 everywhere {100 * v['share_below_-3']:.1f}%, "
              f"below -5 {100 * v['share_below_-5']:.1f}%")
