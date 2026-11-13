"""Exploratory: the amplitude-condensed reading applied to the host's final model of G-C2.1 (label-free seed 2), without
any retraining, on the 64 former held-out members.
For each member and evaluation level D: z = the model's field at D, z0 = its field at D = 0.1 mm,
z_c = z0 + a (z - z0) with a = argmin_a Pi(z_c; D) (secant iteration on dPi/da with the training energy, contact
unknowns kept >= 0). Then e, F = 4 k_s (D - e), the energy gap and the distance from the reference curve (interpolated
from exact points) of z_c, next to those of z. No reference solution enters the reading itself."""
import sys, json, time
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
sys.path.insert(0, str(paths.joint())); sys.path.insert(0, str(paths.src()))
import numpy as np, torch
from pathlib import Path
from c2.config import config
from c2.data import load_export, manifest
from c2.instance import ExportedProblem
from c2.model import build, field
from c2.train import _prepare, MATMUL_PRECISION
from refcurve import points, curve
part, nparts = int(sys.argv[1]), int(sys.argv[2])
torch.set_num_threads(1); torch.set_float32_matmul_precision(MATMUL_PRECISION)
cfg = config(); DATA = str(paths.data()); dev = torch.device("cpu"); tr = cfg["training"]; NB = tr["bubble_newton_steps"]
torch.serialization.add_safe_globals([torch.torch_version.TorchVersion])
st = torch.load(paths.states() / "label_free_s2/state.pt", map_location="cpu", weights_only=True)
man = manifest(DATA); ids = [r["id"] for r in man["instances"] if r["split"] == "eval"][part::nparts]
LV = [float(v) for v in cfg["data"]["eval_levels_mm"]]; KS = 2.0e4
RET = Path(paths.ret())
nets = None
out_path = Path(paths.work() / f"cond/rows_{part}.jsonl")
done = {json.loads(l)["iid"] for l in open(out_path)} if out_path.exists() else set()


def condense(E, nonneg, z0, z, D, iters=4):
    d = z - z0
    def vg(a):
        a = a.clone().requires_grad_(True)
        zc = z0 + a[:, None] * d
        Pi = E.energy(torch.where(nonneg, zc.clamp_min(0.0), zc), D, iters=NB)
        g, = torch.autograd.grad(Pi.sum(), a)
        return Pi.detach(), g.detach()
    a0 = torch.ones(z.shape[0]); P0, g0 = vg(a0)
    best_a, best_P = a0.clone(), P0.clone()
    a1 = a0 - 0.02 * torch.sign(g0); P1, g1 = vg(a1); n = 2
    for _ in range(iters + 1):
        better = P1 < best_P
        best_a, best_P = torch.where(better, a1, best_a), torch.where(better, P1, best_P)
        den = g1 - g0; den = torch.where(den.abs() < 1e-9, torch.full_like(den, 1e-9), den)
        a2 = (a1 - g1 * (a1 - a0) / den).clamp(0.5, 3.0)
        a0, g0 = a1, g1
        P1, g1 = vg(a2); a1 = a2; n += 1
    better = P1 < best_P
    return torch.where(better, a1, best_a), n


for iid in ids:
    if iid in done: continue
    t0 = time.time()
    it = _prepare(cfg, DATA, [iid], dev, energy=True, labels=False)[0]
    if nets is None:
        torch.manual_seed(0); nets = build(cfg, it["base"].shape[-1] + 1)
        for net, k in zip(nets, ("enc", "dec", "head")):
            net.load_state_dict(st[k]); net.eval()
    mp = it["maps"]; nonneg = torch.cat([mp["nonneg"], torch.zeros(mp["n_z"] - mp["nonneg"].numel(), dtype=torch.bool)])
    lv = torch.as_tensor([0.1] + LV, dtype=torch.float32)
    with torch.no_grad():
        zall = field(*nets, it["base"], mp, lv, cfg["map"]["T"], lift=True)
    z0, z = zall[:1], zall[1:]
    a, n = condense(it["energy"], nonneg, z0.expand_as(z), z, lv[1:])
    zc = z0 + a[:, None] * (z - z0); zc = torch.where(nonneg, zc.clamp_min(0.0), zc)
    ex, q = load_export(Path(DATA) / "inst" / f"{iid}.npz"); P = ExportedProblem(ex)
    lab = np.load(RET / "labels" / f"{iid}.npz"); c = curve(points(iid))
    rows = []
    for l, D in enumerate(LV):
        rec = {"D": D, "a": float(a[l])}
        for name, f in (("raw", z[l]), ("cond", zc[l])):
            r = P.evaluate(f.double().numpy(), D)
            rec[name] = {"gap": r["Pi"] / float(lab["Pi"][l]) - 1, "e_err": r["e"] / float(lab["e"][l]) - 1, "F_err": r["F"] / float(lab["F"][l]) - 1,
                         "curve_err": r["F"] / float(c(r["e"])) - 1, "bolt_err": r["bolt_N"] / float(lab["bolt_N"][l]) - 1}
        rec["m"] = float(lab["e"][l]) / (D - float(lab["e"][l]))
        rows.append(rec)
    with open(out_path, "a") as fh:
        fh.write(json.dumps({"iid": iid, "rows": rows, "evals": n, "seconds": round(time.time() - t0, 1)}) + "\n")
