"""Sandbox diagnostic: does the single-precision gradient used in training give the same elastic contact step as
the double-precision gradient of the reference code? States: the closed (preload) state, and the fields of saved
runs."""
import sys
import numpy as np
import torch
joint, data, member = sys.argv[1:4]; runs = sys.argv[4:]
sys.path.insert(0, joint)
sys.path.insert(0, joint + "/../src")
from f2 import devconfig
from f2.data import load_export
from f2.evaluate import clean
from f2.instance import ExportedProblem
from f2.model import build, field
from f2.precond import ElasticContactStep
from f2.torch_energy import InstanceEnergy
from f2.train import build_item

torch.set_num_threads(1)
ex, q = load_export(f"{data}/inst/{member}.npz")
lab = np.load(f"{data}/labels/{member}.npz")
z_pre = np.load(f"{data}/pre/{member}.npz")["z"].astype(float)
E = ElasticContactStep(ex, z_pre)
P = ExportedProblem(ex); cidx = P.prob.cidx
dev = torch.device("cpu")
en32 = InstanceEnergy(ex, device=dev, dtype=torch.float32)
en64 = InstanceEnergy(ex, device=dev, dtype=torch.float64)

def g_torch(en, z, Theta, dtype):
    zt = torch.as_tensor(z[None], dtype=dtype).requires_grad_(True)
    Pi = en.energy(zt, torch.as_tensor([Theta], dtype=dtype), iters=10)
    (g,) = torch.autograd.grad(Pi.sum(), zt)
    return g[0].double().numpy(), float(Pi[0])

def state(z, Theta, k):
    zt = z.copy(); zt[cidx] = np.maximum(zt[cidx], 0.0)
    clean(P); r = P.evaluate(zt, Theta)
    return r["Pi"] / float(lab["Pi"][k]) - 1.0, r["theta"] / float(lab["theta"][k]), r["ThetaD"] / float(lab["ThetaD"][k])

def report(tag, z, lam):
    k = int(np.argmin(np.abs(lab["lam"] - lam))); Theta = float(lab["Theta"][k])
    z = z.astype(float).copy()
    clean(P); P.loading.delta[:] = -Theta
    _, g_ref, _, _ = P.prob.evaluate(z, "hencky", tangent=False)
    g64, _ = g_torch(en64, z, Theta, torch.float64)
    z32 = z.astype(np.float32).astype(float)                    # the field as training holds it
    g32, _ = g_torch(en32, z32, Theta, torch.float32)
    free = E.free
    def rel(a, b): return np.linalg.norm((a - b)[free]) / np.linalg.norm(b[free])
    e0 = state(z, Theta, k)
    out = [f"{tag} lam {lam}: start excess {e0[0]:.2%}, theta/ref {e0[1]:.3f}, ThetaD/ref {e0[2]:.3f}; "
           f"|g|: {np.linalg.norm(g_ref[free]):.3g}; torch64 against reference {rel(g64, g_ref):.1e}; single against double {rel(g32, g64):.1e}"]
    for name, g, z0 in (("reference", g_ref, z), ("torch64", g64, z), ("single", g32, z32)):
        d = E.step(z0, g)[0]
        e = state(z0 + d, Theta, k)
        out.append(f"      step from the {name:9s} gradient: |d| {np.linalg.norm(d):.4g}; excess {e[0]:9.2%}; theta/ref {e[1]:.3f}; ThetaD/ref {e[2]:.3f}")
    print("\n".join(out), flush=True)

zc = z_pre.copy(); zc[cidx] = np.maximum(zc[cidx], 0.0)
if not runs:
    for lam in (1.0, 0.25, 0.0625):
        report("closed state", zc, lam)
for r in runs:
    s = torch.load(f"{r}/label_free_s0/state.pt", map_location="cpu", weights_only=False)
    cfg = devconfig.config(s["history"]["preset"])
    it = build_item(data, member, dev, cfg["model"]["lift"])
    nets = build(cfg, it["base"].shape[-1] + 1, it["maps"]["nb"])
    for net, kk in zip(nets, ("enc", "dec", "head")):
        net.load_state_dict(s[kk]); net.eval()
    for lam in (1.0, 0.25, 0.0625):
        k = int(np.argmin(np.abs(lab["lam"] - lam)))
        Theta = torch.as_tensor([float(lab["Theta"][k])], dtype=torch.float32)
        with torch.no_grad():
            z = field(*nets, it["base"], it["maps"], Theta, cfg["map"]["T"], gate=cfg["map"]["kind"])[0].double().numpy()
        report(f"{s['history']['preset']} at step {s['step']}", z, lam)
