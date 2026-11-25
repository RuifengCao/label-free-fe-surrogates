"""Sandbox diagnostic: the raw and the amplitude-condensed readings (c22/condense.py, as the evaluation applies it)
of a saved run for one member, on one or more meshes, each against its own labels. No training.

    python3 -I condensed_preview.py JOINT_DIR STATE.pt MEMBER OUT_PREFIX DATA_DIR [DATA_DIR ...]
"""
import sys, time
import numpy as np
import torch
joint, state, member, out = sys.argv[1:5]; datas = sys.argv[5:]
sys.path.insert(0, joint); sys.path.insert(0, joint + "/../src")
from c22.condense import condense
from f2 import devconfig
from f2.evaluate import clean
from f2.instance import ExportedProblem
from f2.data import load_export
from f2.model import build, field, readings
from f2.train import build_item

torch.set_num_threads(2)
s = torch.load(state, map_location="cpu", weights_only=False)      # a checkpoint written by f2/train.py
cfg = devconfig.config(s["history"]["preset"])
rd = cfg["evaluation"]["readings"]["condensed"]
print(f"state of {s['history']['preset']}: epoch {s['epoch']}, step {s['step']}; condensed reading: base level {rd['base_level']}, a in [{rd['a_min']}, {rd['a_max']}]")
dev = torch.device("cpu")


def chunked(m, x, chunk=512):
    B, N, E = x.shape; H = m.num_heads; d = E // H
    W, b = m.in_proj_weight, m.in_proj_bias
    q, k, v = (torch.nn.functional.linear(x, W[i * E:(i + 1) * E], b[i * E:(i + 1) * E]).view(B, N, H, d).transpose(1, 2) for i in range(3))
    o = torch.empty(B, H, N, d); kt = k.transpose(-1, -2)
    for a in range(0, N, chunk):
        o[:, :, a:a + chunk] = torch.softmax((q[:, :, a:a + chunk] @ kt) / d ** 0.5, dim=-1) @ v
    return m.out_proj(o.transpose(1, 2).reshape(B, N, E))


nets = None
for data in datas:
    tag = data.rstrip("/").split("/")[-1]
    it = build_item(data, member, dev, cfg["model"]["lift"])
    mp = it["maps"]
    if nets is None:
        nets = build(cfg, it["base"].shape[-1] + 1, mp["nb"])
        for net, kk in zip(nets, ("enc", "dec", "head")):
            net.load_state_dict(s[kk]); net.eval()
        for blk in nets[0].blocks:
            blk.attn.forward = (lambda m: (lambda h, *a, **kw: (chunked(m, h), None)))(blk.attn)
    lab = np.load(f"{data}/labels/{member}.npz")
    ex, q = load_export(f"{data}/inst/{member}.npz")
    P = ExportedProblem(ex)
    lam = [rd["base_level"]] + [float(x) for x in lab["lam"]]
    t0 = time.time(); zs = []
    with torch.no_grad():
        for l in lam:                                             # one field at a time: the memory of the attention
            Th = torch.as_tensor([l * mp["Theta_max"]], dtype=torch.float32)
            zs.append(field(*nets, it["base"], mp, Th, cfg["map"]["T"], gate=cfg["map"]["kind"]))
    zall = torch.cat(zs); z0, z = zall[:1].expand(len(lam) - 1, -1), zall[1:]
    Theta = torch.as_tensor(np.asarray(lab["Theta"], np.float32))
    print(f"{tag}: fields in {time.time() - t0:.0f} s", flush=True)
    t0 = time.time()
    a, st = condense(it["energy"], z0, z, Theta, mp["nonneg"], cfg["training"]["bubble_newton_steps"], rd["a_min"], rd["a_max"], rd["max_evaluations"], rd["rtol"])
    zc = z0 + a[:, None] * (z - z0); zc = torch.where(mp["nonneg"], zc.clamp_min(0.0), zc)
    print(f"{tag}: amplitudes {np.round(a.numpy(), 3).tolist()} in {st['evals']} evaluations, {time.time() - t0:.0f} s; at a bound {st['at_bound'].tolist()}", flush=True)
    np.savez_compressed(f"{out}_{tag}.npz", z=z.numpy(), zc=zc.numpy(), z0=zall[0].numpy(), a=a.numpy(), Theta=Theta.numpy())
    for name, f in (("raw", z), ("condensed", zc)):
        with torch.no_grad():
            r = readings(it["energy"], mp, f, Theta)
        th, tD = r["theta"].double().numpy(), r["ThetaD"].double().numpy()
        M = 2.0 * mp["k_th"] * (np.asarray(lab["Theta"], float) - th)
        ex_ = []
        for l in range(f.shape[0]):
            zn = f[l].double().numpy(); zn[P.prob.cidx] = np.maximum(zn[P.prob.cidx], 0.0)
            clean(P); ex_.append(P.evaluate(zn, float(lab["Theta"][l]))["Pi"] / float(lab["Pi"][l]) - 1.0)
        Me = M / np.asarray(lab["M"], float) - 1.0
        print(f"{tag} {name:9s}: theta/ref {np.round(th / lab['theta'], 3).tolist()}  ThetaD/ref {np.round(tD / lab['ThetaD'], 3).tolist()}\n"
              f"{tag} {name:9s}: M err % {np.round(100 * Me, 1).tolist()}  energy excess % {np.round(100 * np.array(ex_), 1).tolist()}\n"
              f"{tag} {name:9s}: |M err| median {np.median(np.abs(Me)):.1%}, largest {np.abs(Me).max():.1%}; energy excess median {np.median(ex_):.1%}", flush=True)
    del it, P
