"""Single-member fitting test, second round (exploratory, after the G-C2.1 verdict; not under any stamp).

As dev/overfit_dev.py (the host's final model of G-C2.1, label-free seed 2, trained on ONE training member from its
final state), with three changes:

  1. the amplitude is condensed by dev/condense.py (bracketed, safeguarded secant) within [--amin, --amax]
     (default 0.5 to 3; the first round used an unguarded secant within 0.6 to 1.6);
  2. --read-cond records the condensed reading at every evaluation for the variants that do not train on it;
  3. the final weights are saved (runs/overfit2/ID_VARIANT_final.pt).

    python -I dev/overfit2_dev.py --member ID --variant {plain,hi,cond} --steps N [--read-cond] [--every 25]

  plain   the gate's loss (mean log Pi of four fields) and its sampling of D (sqrt(D) uniform on [0.1, 8] mm)
  hi      the gate's loss, D uniform on [3, 8] mm
  cond    the gate's sampling; the loss is the mean log Pi of the fields whose load-induced part has its amplitude
          condensed, z_c = z_0 + a (z - z_0), z_0 the network's own field at D = 0.1 mm (a carries no gradient: at
          the minimum dPi/da = 0), plus a quarter of the gate's loss on the raw fields and on z_0, which keeps the raw
          amplitude and the field at 0.1 mm trained. The same loss as in the first round.

AdamW starts afresh with the gate's weight decay and clipping; the learning rate rises linearly over --warmup steps
to --lr and then stays. Every --every steps: the energy gap, the end-displacement error and the bolt-force error at
the seven evaluation levels against the member's exact solutions (numpy reference code, float64), for the raw field
and for the condensed field, with the amplitudes and how well the one-dimensional solve converged.
Records: runs/overfit2/ID_VARIANT.jsonl. Needs states/label_free_s2/state.pt and dev_labels/ID.npz."""
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
ap.add_argument("--every", type=int, default=25)
ap.add_argument("--device", default="cuda")
ap.add_argument("--warmup", type=int, default=100, help="steps over which the learning rate rises linearly to --lr")
ap.add_argument("--read-cond", action="store_true", help="record the condensed reading too (plain, hi)")
ap.add_argument("--amin", type=float, default=0.5)
ap.add_argument("--amax", type=float, default=3.0)
ap.add_argument("--train-evals", type=int, default=7, help="energy evaluations of the amplitude solve in a step")
ap.add_argument("--read-evals", type=int, default=12, help="energy evaluations of the amplitude solve in a reading")
ap.add_argument("--data", default=str(DATA))
ap.add_argument("--state", default=str(BASE / "states" / "label_free_s2" / "state.pt"))
ap.add_argument("--labels", default=str(BASE / "dev_labels"))
ap.add_argument("--out", default=str(BASE / "runs" / "overfit2"))
args = ap.parse_args()
sys.path.insert(0, str(JOINT))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from c2.config import config  # noqa: E402
from c2.data import load_export  # noqa: E402
from c2.instance import ExportedProblem  # noqa: E402
from c2.model import build, field  # noqa: E402
from c2.train import _prepare, sample_D, MATMUL_PRECISION  # noqa: E402
from condense import condense  # noqa: E402

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
use_cond = args.variant == "cond" or args.read_cond
acc = {"n": 0, "not_converged": 0, "at_bound": 0, "a_min": float("inf"), "a_max": 0.0, "slope_max": 0.0}


def fld(D):
    return field(enc, dec, head, it["base"], mp, D, cfg["map"]["T"], lift=True)


def keep_nonneg(z):
    return torch.where(nonneg, z.clamp_min(0.0), z)


def evaluate() -> dict:
    for net in nets:
        net.eval()
    out = {}
    with torch.no_grad():
        z = fld(lv_t)
        z0 = fld(base_t)
    fields = {"raw": z}
    if use_cond:
        a, info = condense(E, z0.expand_as(z), z, lv_t, nonneg, NB, args.amin, args.amax, args.read_evals)
        fields["cond"] = keep_nonneg(z0 + a[:, None] * (z - z0))
        out["a"] = [round(float(v), 4) for v in a]
        out["a_info"] = {"rel_slope": [float(v) for v in info["rel_slope"]], "evals": info["evals"],
                         "at_bound": [bool(v) for v in info["at_bound"]],
                         "converged": [bool(v) for v in info["converged"]]}
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
tag = f"{iid}_{args.variant}" + ("_rc" if args.read_cond and args.variant != "cond" else "")
log = open(out_dir / f"{tag}.jsonl", "w")
log.write(json.dumps({"member": iid, "variant": args.variant, "read_cond": use_cond, "steps": args.steps,
                      "lr": args.lr, "device": str(dev), "torch": torch.__version__, "state": Path(args.state).name,
                      "warmup": args.warmup, "amin": args.amin, "amax": args.amax, "train_evals": args.train_evals,
                      "read_evals": args.read_evals, "script": "overfit2_dev.py"}) + "\n")
t0 = time.time()
rec = {"step": 0, **evaluate()}
log.write(json.dumps(rec) + "\n"); log.flush()
key = "cond" if use_cond else "raw"
print(0, key, "gap %:", [round(100 * v, 2) for v in rec[key]["gap"]], "| e err %:",
      [round(100 * v, 1) for v in rec[key]["e_err"]], "| a:", rec.get("a"), flush=True)
status = "finished"
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
        a, info = condense(E, z0.detach().expand_as(z), z.detach(), D, nonneg, NB, args.amin, args.amax,
                           args.train_evals)
        acc["n"] += 4
        acc["not_converged"] += int((~info["converged"]).sum()); acc["at_bound"] += int(info["at_bound"].sum())
        acc["a_min"] = min(acc["a_min"], float(a.min())); acc["a_max"] = max(acc["a_max"], float(a.max()))
        acc["slope_max"] = max(acc["slope_max"], float(info["rel_slope"][~info["at_bound"]].max()) if bool((~info["at_bound"]).any()) else 0.0)
        zc = keep_nonneg(z0 + a[:, None] * (z - z0))
        loss = torch.log(E.energy(zc, D, iters=NB)).mean() + 0.25 * torch.log(E.energy(z_all, D_all, iters=NB)).mean()
    else:
        loss = torch.log(E.energy(fld(D), D, iters=NB)).mean()
    if not torch.isfinite(loss):
        log.write(json.dumps({"step": step, "status": "non-finite loss"}) + "\n")
        status = f"non-finite loss at step {step}"
        break
    opt.zero_grad(set_to_none=True)
    loss.backward()
    gn = float(torch.nn.utils.clip_grad_norm_(params, tr["clip"]))
    opt.step()
    if step % args.every == 0 or step == args.steps:
        rec = {"step": step, "loss": float(loss.detach()), "grad": gn, "sec": round(time.time() - t0, 1), **evaluate()}
        if args.variant == "cond":
            rec["train_solve"] = dict(acc)
            acc.update({"n": 0, "not_converged": 0, "at_bound": 0, "a_min": float("inf"), "a_max": 0.0, "slope_max": 0.0})
        log.write(json.dumps(rec) + "\n"); log.flush()
        print(step, round(time.time() - t0), "s |", key, "gap %:", [round(100 * v, 2) for v in rec[key]["gap"]], "| e err %:",
              [round(100 * v, 1) for v in rec[key]["e_err"]], "| a:", rec.get("a"), flush=True)
tmp = out_dir / f"{tag}_final.tmp"
torch.save({"enc": enc.state_dict(), "dec": dec.state_dict(), "head": head.state_dict(), "member": iid,
            "variant": args.variant, "steps": args.steps}, tmp)
tmp.replace(out_dir / f"{tag}_final.pt")
log.write(json.dumps({"end": True, "status": status, "seconds": round(time.time() - t0, 1)}) + "\n")
log.close()
print(f"{tag}: {status}; {round(time.time() - t0)} s", flush=True)
