"""Sandbox diagnostic: the fields that a saved run gives for one member on two meshes (the one it was trained on and
another), read against each mesh's own labels. No training. The attention is evaluated in chunks of rows to keep the
memory low on a processor; the chunked form is checked against the module's own on the first mesh.

    python3 -I transfer_probe.py JOINT_DIR STATE.pt MEMBER DATA_DIR [DATA_DIR ...]
"""
import sys, time
import numpy as np
import torch
joint, state, member = sys.argv[1:4]; datas = sys.argv[4:]
sys.path.insert(0, joint); sys.path.insert(0, joint + "/../src")
from f2 import devconfig
from f2.evaluate import clean
from f2.instance import ExportedProblem
from f2.data import load_export
from f2.model import build, field, readings
from f2.train import build_item

torch.set_num_threads(2)
try:
    s = torch.load(state, map_location="cpu", weights_only=True)
except Exception as err:                                           # noqa: BLE001
    print("weights_only load refused:", type(err).__name__, str(err)[:120]); s = torch.load(state, map_location="cpu", weights_only=False)
cfg = devconfig.config(s["history"]["preset"])
print(f"state of {s['history']['preset']}: epoch {s['epoch']}, step {s['step']}")
dev = torch.device("cpu")


def chunked(m, x, chunk=512):
    B, N, E = x.shape; H = m.num_heads; d = E // H
    W, b = m.in_proj_weight, m.in_proj_bias
    q, k, v = (torch.nn.functional.linear(x, W[i * E:(i + 1) * E], b[i * E:(i + 1) * E]).view(B, N, H, d).transpose(1, 2) for i in range(3))
    out = torch.empty(B, H, N, d)
    kt = k.transpose(-1, -2)
    for a in range(0, N, chunk):
        out[:, :, a:a + chunk] = torch.softmax((q[:, :, a:a + chunk] @ kt) / d ** 0.5, dim=-1) @ v
    return m.out_proj(out.transpose(1, 2).reshape(B, N, E))


nets = None
for k_d, data in enumerate(datas):
    it = build_item(data, member, dev, cfg["model"]["lift"])
    if nets is None:
        nets = build(cfg, it["base"].shape[-1] + 1, it["maps"]["nb"])
        for net, kk in zip(nets, ("enc", "dec", "head")):
            net.load_state_dict(s[kk]); net.eval()
    lab = np.load(f"{data}/labels/{member}.npz")
    ex, q = load_export(f"{data}/inst/{member}.npz")
    P = ExportedProblem(ex)
    n = it["maps"]["n"]
    rows = []
    for l in range(len(lab["lam"])):
        Theta = torch.as_tensor([float(lab["Theta"][l])], dtype=torch.float32)
        t0 = time.time()
        with torch.no_grad():
            if k_d == 0 and l == 0:                                # the chunked attention against the module's own
                z_own = field(*nets, it["base"], it["maps"], Theta, cfg["map"]["T"], gate=cfg["map"]["kind"])
            for blk in nets[0].blocks:
                blk.attn.forward = (lambda m: (lambda h, *a, **kw: (chunked(m, h), None)))(blk.attn)
            z = field(*nets, it["base"], it["maps"], Theta, cfg["map"]["T"], gate=cfg["map"]["kind"])
            if k_d == 0 and l == 0:
                print(f"chunked attention against the module's own: largest difference of the field {float((z - z_own).abs().max()):.2e} (largest entry {float(z_own.abs().max()):.3g})")
            r = readings(it["energy"], it["maps"], z, Theta)
        zn = z[0].double().numpy(); zn[P.prob.cidx] = np.maximum(zn[P.prob.cidx], 0.0)
        clean(P); e = P.evaluate(zn, float(Theta[0]))
        M = 2.0 * it["maps"]["k_th"] * (float(Theta[0]) - float(r["theta"][0]))
        rows.append((float(lab["lam"][l]), float(r["theta"][0]) / float(lab["theta"][l]), float(r["ThetaD"][0]) / float(lab["ThetaD"][l]),
                     M / float(lab["M"][l]) - 1.0, e["Pi"] / float(lab["Pi"][l]) - 1.0, time.time() - t0))
        print(f"   {data.rstrip('/').split('/')[-1]} ({n} nodes) level {rows[-1][0]:.4f}: theta/ref {rows[-1][1]:.3f}  ThetaD/ref {rows[-1][2]:.3f}  M err {rows[-1][3]:+.1%}  energy excess {rows[-1][4]:.1%}  ({rows[-1][5]:.0f} s)", flush=True)
    a = np.array(rows)
    print(f"{data.rstrip('/').split('/')[-1]}: |M err| median {np.median(np.abs(a[:, 3])):.1%}, largest {np.abs(a[:, 3]).max():.1%}; energy excess median {np.median(a[:, 4]):.1%}; theta/ref median {np.median(a[:, 1]):.2f}; ThetaD/ref median {np.median(a[:, 2]):.2f}", flush=True)
    del it, P
