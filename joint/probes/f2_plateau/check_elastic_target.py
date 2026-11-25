import sys, numpy as np, torch
joint, data, member = sys.argv[1:4]
sys.path.insert(0, joint); sys.path.insert(0, joint + "/../src")
from f2 import devconfig as d
from f2.model import readings
from f2 import train as T
torch.set_num_threads(1)
for k, h in (("tfam128_frame", "53351c98ed06"), ("tfam128_hinge", "875629b2c2cb"), ("tfam128_bending", "dce1f4026f98"), ("tiny_frame", "1779d384516d"), ("one_bending", "94fb316ff861")):
    assert d.sha256(d.config(k))[:12] == h, k
print("existing presets keep their hashes;", {k: d.sha256(d.config(k))[:12] for k in ("cpu_frame_step", "cpu_frame_step_e400", "cpu_frame_elastic_e300", "cpu_frame_energy_lr1e4")})
cfg = d.config("cpu_frame_elastic_e300")
print(cfg["training"]["loss_kind"], [k for k in cfg["training"] if "loss" in k])
dev = torch.device("cpu")
it = T.build_item(data, member, dev, "frame", step=True)
lab = np.load(f"{data}/labels/{member}.npz")
Theta = torch.as_tensor(lab["Theta"], dtype=torch.float32)
zc = it["z_closed"][None].repeat(len(Theta), 1).requires_grad_(True)
Pi = it["energy"].energy(zc, Theta, iters=10); (g,) = torch.autograd.grad(Pi.sum(), zc)
zn, gn = zc.detach().double().numpy(), g.double().numpy()
dd = np.stack([it["step"].step(zn[b], gn[b])[0] for b in range(len(Theta))])
target = zc.detach() + torch.as_tensor(dd, dtype=torch.float32)
r = readings(it["energy"], it["maps"], target, Theta)
with torch.no_grad():
    Pt = it["energy"].energy(target, Theta, iters=10)
print("levels", np.round(lab["lam"], 4).tolist())
print("elastic target: theta/ref", np.round(r["theta"].numpy() / lab["theta"], 3).tolist())
print("elastic target: ThetaD/ref", np.round(r["ThetaD"].numpy() / lab["ThetaD"], 3).tolist())
print("elastic target: energy excess % (single precision energy against the labels)", np.round(100 * (Pt.numpy() / lab["Pi"] - 1), 2).tolist())
z = torch.zeros_like(target, requires_grad=True)
print("loss of the zero field", float(T.elastic_target_loss(it, z, Theta, 10)))
print("loss of the target itself", float(T.elastic_target_loss(it, target.clone().requires_grad_(True), Theta, 10)))
