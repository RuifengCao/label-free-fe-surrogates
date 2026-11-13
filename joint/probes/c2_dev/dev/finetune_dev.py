"""Fine-tuning of a trained model on the whole training family of G-C2.1, with the gate's loss or with the
amplitude-condensed loss (exploratory development run, after the verdict; not under any stamp; no verdict changes).

    python -I dev/finetune_dev.py --name NAME --loss {plain,cond} --sampling {sqrt,uniform} [--epochs 10]
                                  [--state states/label_free_s2/state.pt] [--seed 0] [--lr 1e-4]

The problem is the gate's: the same 512 training members, spring, energy and evaluation levels. What changes:

  --loss plain     the gate's loss: the mean of log Pi over the step's four fields;
  --loss cond      the mean of log Pi over the four fields after amplitude condensation (dev/condense.py:
                   z_c = z_0 + a (z - z_0), z_0 the network's own field at D = 0.1 mm, a = argmin Pi, no gradient
                   through a), plus --raw-weight (0.25) times the gate's loss on the raw fields and on z_0;
  --sampling sqrt     the gate's sampling of D (sqrt(D) uniform on [0.1, 8] mm);
  --sampling uniform  D uniform on [0.1, 8] mm.

Training: one member a step in a fresh random order each epoch, four fields a step, AdamW afresh (the gate's weight
decay and clipping) with the adopted stability recipe (--recipe cap+beta2: beta2 = 0.99, and the encoder's gradient
scaled down to at most 5 times the median of its norm over the previous 256 steps). The learning rate rises linearly
over --warmup steps to --lr, stays, and falls to zero on a half cosine over the last --anneal-epochs epochs.

Readings: before training (epoch 0) and at the end of the epochs in --pred-epochs, the 64 former held-out members are
read raw and amplitude-condensed and judged against their exact reference curves (dev/evalcond.py, eval_ref.json).
No reference solution enters training or a reading.

Records, in runs/NAME/: steps.jsonl (every step), eval_eK.json (readings and judged rows at epoch K), state.pt
(checkpoint at every epoch's end; resume: run the same command again), fields_final.npz, final_state.pt, summary.json.
A probe every 64 steps watches the relative variance of the latents on the first training member; a fall below a
third of the value at the probe before is recorded as a collapse and stops the run."""
import argparse
import collections
import datetime
import json
import os
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
JOINT, REPO, DATA = BASE / "code" / "joint", BASE / "code" / "repo", BASE / "data"
CAP, WINDOW, BURST, PROBE_EVERY, D_BASE = 5.0, 256, 10.0, 64, 0.1
TEST = {k: os.environ[k] for k in os.environ if k.startswith("C2DEV_TEST_")}      # test hooks; empty in a real run
if TEST:
    WINDOW = int(TEST.get("C2DEV_TEST_WINDOW", WINDOW)); PROBE_EVERY = int(TEST.get("C2DEV_TEST_PROBE_EVERY", PROBE_EVERY))
    CAP = float(TEST.get("C2DEV_TEST_CAP", CAP))

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True)
ap.add_argument("--loss", required=True, choices=["plain", "cond"])
ap.add_argument("--sampling", required=True, choices=["sqrt", "uniform"])
ap.add_argument("--epochs", type=int, default=10)
ap.add_argument("--anneal-epochs", type=int, default=2)
ap.add_argument("--pred-epochs", default="2,5,8,10")
ap.add_argument("--lr", type=float, default=1e-4)
ap.add_argument("--warmup", type=int, default=100)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--recipe", default="cap+beta2", choices=["none", "cap+beta2"])
ap.add_argument("--raw-weight", type=float, default=0.25)
ap.add_argument("--amin", type=float, default=0.5)
ap.add_argument("--amax", type=float, default=3.0)
ap.add_argument("--train-evals", type=int, default=7)
ap.add_argument("--read-evals", type=int, default=12)
ap.add_argument("--state", default="states/label_free_s2/state.pt")
ap.add_argument("--device", default="cuda")
ap.add_argument("--members", type=int, default=None, help="use only the first N training members (tests only)")
ap.add_argument("--eval-members", type=int, default=None, help="read only the first N held-out members (tests only)")
ap.add_argument("--data", default=str(DATA))
ap.add_argument("--runs", default=str(BASE / "runs"))
ap.add_argument("--ref", default=str(BASE / "eval_ref.json"))
args = ap.parse_args()
sys.path.insert(0, str(JOINT))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from c2.config import config  # noqa: E402
from c2.data import manifest  # noqa: E402
from c2.model import build, field, inputs  # noqa: E402
from c2.train import _prepare, sample_D, MATMUL_PRECISION  # noqa: E402
from condense import condense  # noqa: E402
from evalcond import evaluate_model, judge, report  # noqa: E402


def now() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


cfg = config()
tr = cfg["training"]
NB, T_MAP = tr["bubble_newton_steps"], cfg["map"]["T"]
run = Path(args.runs) / args.name
run.mkdir(parents=True, exist_ok=True)
steps_path, ck_path, sum_path = run / "steps.jsonl", run / "state.pt", run / "summary.json"
if sum_path.exists() and json.loads(sum_path.read_text()).get("status", "running") != "running":
    print(f"{args.name}: already ended ({json.loads(sum_path.read_text())['status']}); nothing to do", flush=True)
    sys.exit(0)
torch.set_float32_matmul_precision(MATMUL_PRECISION)
ref = json.loads(Path(args.ref).read_text())
eval_ids = list(ref["members"])[:args.eval_members] if args.eval_members else list(ref["members"])
pred_epochs = sorted({int(v) for v in args.pred_epochs.split(",") if v.strip()} | {args.epochs})
man = manifest(args.data)
train_ids = [r["id"] for r in man["instances"] if r["split"] == "train"]
if args.members:
    train_ids = train_ids[:args.members]
dev = torch.device(args.device)
torch.manual_seed(args.seed)
rng = np.random.default_rng(args.seed)
t_prep = time.time()
items = _prepare(cfg, args.data, train_ids, dev, energy=True, labels=False)
nets = build(cfg, items[0]["base"].shape[-1] + 1)
enc, dec, head = nets
init = Path(args.state) if Path(args.state).is_absolute() else BASE / args.state
torch.serialization.add_safe_globals([torch.torch_version.TorchVersion])
try:
    s0 = torch.load(init, map_location="cpu", weights_only=True)
except Exception:                                   # a development checkpoint also holds numpy and Python objects
    s0 = torch.load(init, map_location="cpu", weights_only=False)
for net, k in zip(nets, ("enc", "dec", "head")):
    net.load_state_dict(s0[k])
    net.to(dev)
del s0
params = [p for net in nets for p in net.parameters()]
use_recipe = args.recipe == "cap+beta2"
betas = (0.9, 0.99) if use_recipe else (0.9, 0.999)
opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=tr["weight_decay"], betas=betas)
n = len(items)
total, flat_end = args.epochs * n, (args.epochs - args.anneal_epochs) * n
window = collections.deque(maxlen=WINDOW)
meta = {"loss": args.loss, "sampling": args.sampling, "seed": args.seed, "epochs": args.epochs,
        "anneal_epochs": args.anneal_epochs, "lr": args.lr, "warmup": args.warmup, "recipe": args.recipe,
        "raw_weight": args.raw_weight, "members": n, "init": init.name}
state = {"epoch": 0, "step": 0, "prev_rel_var": None, "collapses": [], "bursts": [], "cap_events": [],
         "epoch_loss": [], "epoch_seconds": [], "resumes": [], "evals": {}, "solve": {"fields": 0, "not_converged": 0,
                                                                                    "at_bound": 0}}
if ck_path.exists():
    s = torch.load(ck_path, map_location=dev, weights_only=False)
    assert s["meta"] == meta, "another run's state"
    for net, k in zip(nets, ("enc", "dec", "head")):
        net.load_state_dict(s[k])
    opt.load_state_dict(s["opt"])
    rng.bit_generator.state = s["rng"]; torch.set_rng_state(s["torch_rng"])
    window.extend(s["window"])
    state = s["state"]
    state["resumes"].append({"epoch": state["epoch"], "time": now()})
    kept = [l for l in open(steps_path) if l.strip() and json.loads(l).get("step", 0) <= state["step"]]
    with open(steps_path, "w") as fh:                         # drop the records after the checkpoint
        fh.writelines(kept)
    print(f"{args.name}: resumed at epoch {state['epoch']}, step {state['step']}", flush=True)
probe_item = items[0]
probe_D = torch.tensor([0.5, 2.0, 8.0], device=dev)
base_t = torch.tensor([D_BASE], dtype=torch.float32, device=dev)


def lr_at(step: int) -> float:
    """The learning rate of step number `step` (1-based)."""
    lr = args.lr * min(1.0, step / max(1, args.warmup))
    if step > flat_end and total > flat_end:
        lr *= 0.5 * (1.0 + np.cos(np.pi * (step - flat_end) / (total - flat_end)))
    return float(lr)


def gnorm(net) -> float:
    g = [p.grad.detach().reshape(-1) for p in net.parameters() if p.grad is not None]
    return float(torch.linalg.vector_norm(torch.cat(g))) if g else 0.0


@torch.no_grad()
def probe() -> dict:
    for net in nets:
        net.eval()
    h = enc(inputs(probe_item["base"], probe_D))
    hc = h - h.mean(dim=1, keepdim=True)
    rel_var = (hc.pow(2).sum(-1).mean(1) / h.pow(2).sum(-1).mean(1)).tolist()
    z = field(enc, dec, head, probe_item["base"], probe_item["maps"], probe_D, T_MAP, lift=True)
    s = probe_D + probe_item["maps"]["delta"]
    for net in nets:
        net.train()
    return {"latent_rel_var": rel_var, "e_over_s": (z[:, -1] / s).tolist()}


def save(status: str) -> None:
    tmp = ck_path.with_suffix(".tmp")
    torch.save({"enc": enc.state_dict(), "dec": dec.state_dict(), "head": head.state_dict(), "opt": opt.state_dict(),
                "rng": rng.bit_generator.state, "torch_rng": torch.get_rng_state(), "window": list(window),
                "state": state, "meta": meta}, tmp)
    os.replace(tmp, ck_path)
    summary(status)


def summary(status: str) -> None:
    out = {"name": args.name, "status": status, "time": now(), **meta, "betas": list(betas),
           "cap": CAP if use_recipe else None, "epochs_done": state["epoch"], "steps": state["step"],
           "device": str(dev), "gpu": torch.cuda.get_device_name(0) if dev.type == "cuda" else None,
           "torch": torch.__version__, "epoch_loss": state["epoch_loss"], "epoch_seconds": state["epoch_seconds"],
           "bursts": state["bursts"], "cap_events": len(state["cap_events"]), "collapses": state["collapses"],
           "resumes": state["resumes"], "evals": state["evals"], "train_solve": state["solve"],
           "amin": args.amin, "amax": args.amax, "train_evals": args.train_evals, "read_evals": args.read_evals,
           "eval_members": len(eval_ids), "test_hooks": TEST, "script": "finetune_dev.py",
           "peak_memory_GiB": (torch.cuda.max_memory_allocated() / 2 ** 30) if dev.type == "cuda" else None}
    tmp = sum_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=1))
    os.replace(tmp, sum_path)


def read_and_judge(epoch: int, final: bool) -> None:
    key = f"e{epoch}"
    path = run / f"eval_{key}.json"
    if key in state["evals"] and path.exists():
        return
    t0 = time.time()
    res = evaluate_model(cfg, nets, args.data, ref, dev, args.read_evals, args.amin, args.amax, eval_ids,
                         run / "fields_final.npz" if final else None)
    jd = judge(res, ref)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"name": args.name, "epoch": epoch, "step": state["step"], "readings": res, **jd}))
    os.replace(tmp, path)
    state["evals"][key] = {"step": state["step"], "seconds": round(time.time() - t0, 1),
                           "raw": jd["summary"]["raw"]["all"], "cond": jd["summary"]["cond"]["all"],
                           "solve": jd["solve"]}
    print(report(f"{args.name} epoch {epoch}", jd), flush=True)
    print(f"  (read and judged in {time.time() - t0:.0f} s)", flush=True)


def step_loss(it):
    B = tr["fields_per_step"]
    if args.sampling == "uniform":
        Dn = rng.uniform(tr["D_min_mm"], cfg["family"]["D_max_mm"], size=B)
    else:
        Dn = sample_D(rng, cfg, B)
    D = torch.as_tensor(Dn, dtype=torch.float32, device=dev)
    E, mp = it["energy"], it["maps"]
    if args.loss == "plain":
        z = field(enc, dec, head, it["base"], mp, D, T_MAP, lift=True)
        return torch.log(E.energy(z, D, iters=NB)).mean(), D, None
    nonneg = it.get("nonneg")
    if nonneg is None:
        nonneg = torch.cat([mp["nonneg"], torch.zeros(mp["n_z"] - mp["nonneg"].numel(), dtype=torch.bool, device=dev)])
        it["nonneg"] = nonneg
    D_all = torch.cat([D, base_t])
    z_all = field(enc, dec, head, it["base"], mp, D_all, T_MAP, lift=True)
    z, z0 = z_all[:B], z_all[B:B + 1]
    a, info = condense(E, z0.detach().expand_as(z), z.detach(), D, nonneg, NB, args.amin, args.amax, args.train_evals)
    zc = z0 + a[:, None] * (z - z0)
    zc = torch.where(nonneg, zc.clamp_min(0.0), zc)
    loss = torch.log(E.energy(zc, D, iters=NB)).mean() + args.raw_weight * torch.log(E.energy(z_all, D_all, iters=NB)).mean()
    return loss, D, (a, info)


print(f"{args.name}: loss {args.loss}, sampling {args.sampling}, {args.epochs} epochs of {n} members on {dev} from "
      f"{init.name} (prepared in {time.time() - t_prep:.0f} s), started {now()}", flush=True)
log = open(steps_path, "a")
if state["step"] == 0:
    log.write(json.dumps({"header": True, "name": args.name, **meta, "betas": list(betas), "torch": torch.__version__,
                          "device": str(dev), "started": now(), "test_hooks": TEST}) + "\n")
    p0 = probe()
    state["prev_rel_var"] = float(np.mean(p0["latent_rel_var"]))
    log.write(json.dumps({"step": 0, "probe": p0}) + "\n"); log.flush()
    read_and_judge(0, False)
    save("running")
for net in nets:
    net.train()
status = "running"
summary(status)
while state["epoch"] < args.epochs and status == "running":
    t0 = time.perf_counter()
    order = rng.permutation(n)
    loss_sum = 0.0
    for i in order:
        step = state["step"] + 1
        for g_ in opt.param_groups:
            g_["lr"] = lr_at(step)
        loss, D, solve = step_loss(items[i])
        if not torch.isfinite(loss):
            status = f"non-finite loss at step {step}"
            break
        opt.zero_grad(set_to_none=True)
        loss.backward()
        g = {"enc": gnorm(enc), "dec": gnorm(dec), "head": gnorm(head)}
        rec = {}
        if len(window) == WINDOW:
            med = float(np.median(window))
            if g["enc"] > BURST * med:
                state["bursts"].append({"step": step, "ratio": g["enc"] / med})
                rec["burst"] = g["enc"] / med
            if use_recipe and g["enc"] > CAP * med:
                scale = CAP * med / g["enc"]
                for p in enc.parameters():
                    if p.grad is not None:
                        p.grad.mul_(scale)
                state["cap_events"].append(step)
                rec["cap_scale"] = scale
        window.append(g["enc"])
        total_norm = float(torch.nn.utils.clip_grad_norm_(params, tr["clip"]))
        opt.step()
        state["step"] = step
        lv = float(loss.detach())
        loss_sum += lv
        rec = {"step": step, "inst": int(i), "D": [round(float(x), 4) for x in D], "loss": lv, "grad": g,
               "grad_total": total_norm, "lr": opt.param_groups[0]["lr"], **rec}
        if solve is not None:
            a, info = solve
            rec["a"] = [round(float(x), 4) for x in a]
            nc, ab = int((~info["converged"]).sum()), int(info["at_bound"].sum())
            state["solve"]["fields"] += int(a.numel()); state["solve"]["not_converged"] += nc; state["solve"]["at_bound"] += ab
            if nc or ab:
                rec["solve"] = {"not_converged": nc, "at_bound": ab}
        if step % PROBE_EVERY == 0:
            pr = probe()
            rec["probe"] = pr
            rv = float(np.mean(pr["latent_rel_var"]))
            if state["prev_rel_var"] is not None and rv < state["prev_rel_var"] / 3.0:
                state["collapses"].append({"step": step, "rel_var": rv, "before": state["prev_rel_var"]})
                rec["collapse"] = True
                status = f"collapse at the probe of step {step}"
            state["prev_rel_var"] = rv
        log.write(json.dumps(rec) + "\n")
        if step % 16 == 0 or step <= 16:
            log.flush()
        if status != "running":
            break
    log.flush()
    if status != "running":
        break
    if dev.type == "cuda":
        torch.cuda.synchronize()
    state["epoch"] += 1
    state["epoch_loss"].append(loss_sum / n)
    state["epoch_seconds"].append(round(time.perf_counter() - t0, 2))
    print(f"epoch {state['epoch']} loss {state['epoch_loss'][-1]:.6g} {state['epoch_seconds'][-1]} s "
          f"({state['epoch_seconds'][-1] / n:.3f} s a step); bursts {len(state['bursts'])}, cap events "
          f"{len(state['cap_events'])}; amplitude solves not converged {state['solve']['not_converged']}, at a bound "
          f"{state['solve']['at_bound']} of {state['solve']['fields']}", flush=True)
    if state["epoch"] in pred_epochs:
        read_and_judge(state["epoch"], state["epoch"] == args.epochs)
    save("running")
log.close()
if status == "running":
    status = "finished"
with open(steps_path, "a") as fh:
    fh.write(json.dumps({"end": True, "step": state["step"], "status": status, "probe": probe(), "time": now()}) + "\n")
tmp = (run / "final_state.pt").with_suffix(".tmp")
torch.save({"enc": enc.state_dict(), "dec": dec.state_dict(), "head": head.state_dict(), "step": state["step"],
            "meta": meta}, tmp)
os.replace(tmp, run / "final_state.pt")
summary(status)
print(f"{args.name}: {status}; {state['step']} steps; ended {now()}", flush=True)
