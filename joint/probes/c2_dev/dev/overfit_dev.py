"""Single-member fitting test (exploratory, after the G-C2.1 verdict; not under any stamp).

Can the host's final model of G-C2.1 (label-free seed 2) fit ONE training member when it trains on that member alone,
starting from its final state?

    python -I dev/overfit_dev.py --member ID --variant {plain,hi,cond} --steps N [--lr 1e-4] [--every 20]

  plain   the gate's loss (mean log Pi of four fields) and its sampling of D (sqrt(D) uniform on [0.1, 8] mm)
  hi      the gate's loss, D uniform on [3, 8] mm
  cond    the gate's sampling; the loss is taken on the field whose load-induced part has its amplitude condensed:
          z_c = z_0 + a (z - z_0), z_0 the network's own field at D = 0.1 mm, a = argmin_a Pi(z_c; D) by a secant
          iteration (a carries no gradient: at the minimum dPi/da = 0), plus a quarter of the gate's loss on the raw
          fields, which keeps the raw amplitude and the field at 0.1 mm trained

AdamW starts afresh (the host ended its cosine schedule at a learning rate of zero, and three steps at 1e-4 from its
final moments raised the energy), with the gate's weight decay and clipping; the learning rate rises linearly over
the first --warmup steps to --lr and then stays. Every --every steps: the
energy gap and the end-displacement error at the seven evaluation levels against the member's exact solutions
(numpy reference code, float64), for the raw field and, in cond, for the condensed field too.
Records: runs/overfit/ID_VARIANT.jsonl. Needs states/label_free_s2/state.pt and dev_labels/ID.npz."""
import argparse
import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
JOINT, REPO, DATA = BASE / "code" / "joint", BASE / "code" / "repo", BASE / "data"
ap = argparse.ArgumentParser()
ap.add_argument("--member", required=True)
ap.add_argument("--variant", required=True, choices=["plain", "hi", "cond"])
ap.add_argument("--steps", type=int, required=True)
ap.add_argument("--lr", type=float, default=1e-4)
ap.add_argument("--every", type=int, default=20)
ap.add_argument("--device", default="cuda")
ap.add_argument("--host-opt", action="store_true", help="continue from the host's AdamW moments (default: afresh)")
ap.add_argument("--warmup", type=int, default=100, help="steps over which the learning rate rises linearly to --lr")
ap.add_argument("--data", default=str(DATA))
ap.add_argument("--state", default=str(BASE / "states" / "label_free_s2" / "state.pt"))
ap.add_argument("--labels", default=str(BASE / "dev_labels"))
ap.add_argument("--out", default=str(BASE / "runs" / "overfit"))
args = ap.parse_args()
sys.path.insert(0, str(JOINT))
sys.path.insert(0, str(REPO / "src"))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from c2.config import config  # noqa: E402
from c2.data import load_export  # noqa: E402
from c2.instance import ExportedProblem  # noqa: E402
from c2.model import build, field  # noqa: E402
from c2.train import _prepare, sample_D, MATMUL_PRECISION  # noqa: E402

D_BASE = 0.1
torch.set_float32_matmul_precision(MATMUL_PRECISION)
cfg = config()
tr = cfg["training"]
dev = torch.device(args.device)
torch.serialization.add_safe_globals([torch.torch_version.TorchVersion])     # the history holds torch.__version__
st = torch.load(args.state, map_location="cpu", weights_only=True)
iid = args.member
it = _prepare(cfg, args.data, [iid], dev, energy=True, labels=False)[0]
torch.manual_seed(0)
nets = build(cfg, it["base"].shape[-1] + 1)
for net, k in zip(nets, ("enc", "dec", "head")):
    net.load_state_dict(st[k])
    net.to(dev)
enc, dec, head = nets
params = [p for net in nets for p in net.parameters()]
opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=tr["weight_decay"])
if args.host_opt:                        # continue with the host's AdamW moments
    opt.load_state_dict(st["opt"])
E, mp = it["energy"], it["maps"]
nonneg = torch.cat([mp["nonneg"], torch.zeros(mp["n_z"] - mp["nonneg"].numel(), dtype=torch.bool, device=dev)])
lab = np.load(Path(args.labels) / f"{iid}.npz")
ex, q = load_export(Path(args.data) / "inst" / f"{iid}.npz")
P = ExportedProblem(ex)
LV = [float(v) for v in lab["D"]]
lv_t = torch.as_tensor(LV, dtype=torch.float32, device=dev)
base_t = torch.tensor([D_BASE], dtype=torch.float32, device=dev)
rng = np.random.default_rng(12345)
NB = tr["bubble_newton_steps"]


def fld(D):
    return field(enc, dec, head, it["base"], mp, D, cfg["map"]["T"], lift=True)


def keep_nonneg(z):
    return torch.where(nonneg, z.clamp_min(0.0), z)


def condense(z0, z, D, iters: int = 3):
    """Per field: a minimising Pi(z0 + a (z - z0); D), by a secant iteration on dPi/da; contact unknowns kept >= 0."""
    d = z - z0

    def vg(a):
        a = a.clone().requires_grad_(True)
        Pi = E.energy(keep_nonneg(z0 + a[:, None] * d), D, iters=NB)
        g, = torch.autograd.grad(Pi.sum(), a)
        return Pi.detach(), g.detach()

    a0 = torch.ones(z.shape[0], device=z.device)
    P0, g0 = vg(a0)
    best_a, best_P = a0.clone(), P0.clone()
    a1 = a0 - 0.02 * torch.sign(g0)
    P1, g1 = vg(a1)
    for _ in range(iters + 1):
        better = P1 < best_P
        best_a, best_P = torch.where(better, a1, best_a), torch.where(better, P1, best_P)
        den = g1 - g0
        den = torch.where(den.abs() < 1e-9, torch.full_like(den, 1e-9), den)
        a2 = (a1 - g1 * (a1 - a0) / den).clamp(0.6, 1.6)
        a0, g0 = a1, g1
        P1, g1 = vg(a2)
        a1 = a2
    return torch.where(P1 < best_P, a1, best_a)


def evaluate() -> dict:
    for net in nets:
        net.eval()
    out = {}
    with torch.no_grad():
        z = fld(lv_t)
        z0 = fld(base_t)
    fields = {"raw": z}
    if args.variant == "cond":
        a = condense(z0.expand_as(z), z, lv_t)
        fields["cond"] = keep_nonneg(z0 + a[:, None] * (z - z0))
        out["a"] = [round(float(v), 4) for v in a]
    for name, f in fields.items():
        g, ee, bb = [], [], []
        fn = f.double().cpu().numpy()
        for l, D in enumerate(LV):
            r = P.evaluate(fn[l], D)
            g.append(r["Pi"] / float(lab["Pi"][l]) - 1)
            ee.append(r["e"] / float(lab["e"][l]) - 1)
            bb.append(r["bolt_N"] / float(lab["bolt_N"][l]) - 1)
        out[name] = {"gap": g, "e_err": ee, "bolt_err": bb}
    for net in nets:
        net.train()
    return out


out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)
log = open(out_dir / f"{iid}_{args.variant}.jsonl", "w")
log.write(json.dumps({"member": iid, "variant": args.variant, "steps": args.steps, "lr": args.lr, "device": str(dev),
                      "torch": torch.__version__, "state": Path(args.state).name, "host_opt": args.host_opt,
                      "warmup": args.warmup}) + "\n")
t0 = time.time()
rec = {"step": 0, **evaluate()}
log.write(json.dumps(rec) + "\n"); log.flush()
key = "cond" if args.variant == "cond" else "raw"
print(0, "gap %:", [round(100 * v, 2) for v in rec["raw"]["gap"]], "| e err %:", [round(100 * v, 1) for v in rec["raw"]["e_err"]],
      flush=True)
for step in range(1, args.steps + 1):
    for g in opt.param_groups:
        g["lr"] = args.lr * min(1.0, step / max(1, args.warmup))
    if args.variant == "hi":
        D = torch.as_tensor(rng.uniform(3.0, 8.0, size=4), dtype=torch.float32, device=dev)
    else:
        D = torch.as_tensor(sample_D(rng, cfg, 4), dtype=torch.float32, device=dev)
    if args.variant == "cond":
        D_all = torch.cat([D, base_t])
        z_all = fld(D_all)
        z, z0 = z_all[:4], z_all[4:5]
        a = condense(z0.detach().expand_as(z), z.detach(), D)
        zc = keep_nonneg(z0 + a[:, None] * (z - z0))
        loss = torch.log(E.energy(zc, D, iters=NB)).mean() + 0.25 * torch.log(E.energy(z_all, D_all, iters=NB)).mean()
    else:
        loss = torch.log(E.energy(fld(D), D, iters=NB)).mean()
    if not torch.isfinite(loss):
        log.write(json.dumps({"step": step, "status": "non-finite loss"}) + "\n")
        break
    opt.zero_grad(set_to_none=True)
    loss.backward()
    gn = float(torch.nn.utils.clip_grad_norm_(params, tr["clip"]))
    opt.step()
    if step % args.every == 0 or step == args.steps:
        rec = {"step": step, "loss": float(loss.detach()), "grad": gn, "sec": round(time.time() - t0, 1), **evaluate()}
        log.write(json.dumps(rec) + "\n"); log.flush()
        print(step, round(time.time() - t0), "s | gap %:", [round(100 * v, 2) for v in rec[key]["gap"]], "| e err %:",
              [round(100 * v, 1) for v in rec[key]["e_err"]], flush=True)
log.write(json.dumps({"end": True, "seconds": round(time.time() - t0, 1)}) + "\n")
log.close()
