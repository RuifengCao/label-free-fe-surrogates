"""Development runs of the label-free arm of gate G-C2.1 with optional training-stability changes
(exploratory, after the verdict; not under any stamp; no verdict changes).

    python -I dev/train_dev2.py --name NAME --seed S --recipe {none,cap,beta2,cap+beta2} --epochs E
                                [--stop-on-collapse] [--after-collapse STEPS] [--device cuda] [--members N]
                                [--extend] [--snapshots E1,E2,...]

train_dev2.py is train_dev.py with two additions and no other change: --extend continues a run that has finished
its E0 epochs to E > E0 epochs from its last checkpoint (the first E0 epochs of the gate's schedule are the same
steps whatever E is, so the extended run is the run that would have been made with --epochs E from the start), and
--snapshots saves the three networks at the end of the listed epochs (runs/NAME/snap_eK.pt).

The run follows c2.train.train step by step: the same seeds, initialisation, member order, displacements, AdamW,
clipping at 1.0 and the cosine schedule of the gate's 200 epochs (so E < 200 epochs are the first E epochs of the
gate's schedule). What a recipe changes, and nothing else:

  cap     before clipping, the encoder's gradient is scaled down to at most 5 times the median of its norm over the
          previous 256 steps (from step 257 on), as in probes/c2_diag/branch.py;
  beta2   AdamW's beta2 is 0.99 instead of 0.999.

Records, in runs/NAME/:
  steps.jsonl    every step: loss, displacements, gradient norms of encoder, decoder and head before clipping,
                 the global norm, the learning rate, the cap's scale when it acted; every 64 steps a probe on the
                 first training member (as branch.py); every 512 steps the share of hidden units of the decoder
                 and the head that are inactive on nine training members (as units.py)
  state.pt       a checkpoint at every epoch's end (resume: run the same command again)
  summary.json   status, epoch losses, bursts, cap events, collapses, timing
  preds.npz      at the end, the fields of the held-out and tested members at the seven evaluation levels

A burst is a step whose encoder gradient norm exceeds ten times its median over the previous 256 steps. A collapse
is a probe at which the relative variance of the latents (mean over the three displacements) has fallen below a
third of its value at the probe before. Both as in probes/c2_diag/RESULTS.md.
"""
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
STAMPED_SHA = "795515630ff6f37a819c7503931c7d7cf6e70a9f272e25ac96730394dd361fb4"
CAP, WINDOW, BURST = 5.0, 256, 10.0
PROBE_EVERY, UNITS_EVERY = 64, 512
TEST = {k: os.environ[k] for k in os.environ if k.startswith("C2DEV_TEST_")}      # test hooks; empty in a real run
if TEST:
    CAP = float(TEST.get("C2DEV_TEST_CAP", CAP)); WINDOW = int(TEST.get("C2DEV_TEST_WINDOW", WINDOW))
    PROBE_EVERY = int(TEST.get("C2DEV_TEST_PROBE_EVERY", PROBE_EVERY))
    UNITS_EVERY = int(TEST.get("C2DEV_TEST_UNITS_EVERY", UNITS_EVERY))
FAKE_COLLAPSE = int(TEST["C2DEV_TEST_COLLAPSE_STEP"]) if "C2DEV_TEST_COLLAPSE_STEP" in TEST else None
UNIT_MEMBERS = [0, 64, 128, 192, 256, 320, 384, 448, 511]

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True)
ap.add_argument("--seed", type=int, required=True)
ap.add_argument("--recipe", required=True, choices=["none", "cap", "beta2", "cap+beta2"])
ap.add_argument("--epochs", type=int, required=True)
ap.add_argument("--stop-on-collapse", action="store_true")
ap.add_argument("--after-collapse", type=int, default=512, help="steps to go on recording after a collapse")
ap.add_argument("--device", default="cuda")
ap.add_argument("--members", type=int, default=None, help="use only the first N training members (tests only)")
ap.add_argument("--data", default=str(DATA))
ap.add_argument("--runs", default=str(BASE / "runs"))
ap.add_argument("--no-preds", action="store_true")
ap.add_argument("--extend", action="store_true", help="continue a finished run to --epochs")
ap.add_argument("--snapshots", default="", help="epochs at whose end the networks are saved, comma-separated")
args = ap.parse_args()

sys.path.insert(0, str(JOINT))
sys.path.insert(0, str(REPO / "src"))

import numpy as np  # noqa: E402

from c2.config import config, sha256  # noqa: E402
from c2.data import manifest  # noqa: E402
from c2.model import build, field, inputs  # noqa: E402
from c2.train import _prepare, step_loss, predict, verify_repository, MATMUL_PRECISION  # noqa: E402

cfg = config()
assert sha256(cfg) == STAMPED_SHA, "the configuration differs from the stamped one"
verify_repository(cfg)
import torch  # noqa: E402
from fejepa.train.schedule import make_scheduler  # noqa: E402


def now() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


run = Path(args.runs) / args.name
run.mkdir(parents=True, exist_ok=True)
steps_path, ck_path, sum_path = run / "steps.jsonl", run / "state.pt", run / "summary.json"
EXTENDING = False
if sum_path.exists() and json.loads(sum_path.read_text()).get("status", "running") != "running":
    prev = json.loads(sum_path.read_text())
    if not (args.extend and prev["status"] == "finished" and prev["epochs_done"] < args.epochs):
        print(f"{args.name}: already ended ({prev['status']}); nothing to do", flush=True)
        sys.exit(0)
    EXTENDING = True
    print(f"{args.name}: extending the finished run from epoch {prev['epochs_done']} to {args.epochs}", flush=True)
SNAPSHOTS = {int(v) for v in args.snapshots.split(",") if v.strip()}

torch.set_float32_matmul_precision(MATMUL_PRECISION)
a, tr = cfg["arms"]["label_free"], cfg["training"]
man = manifest(args.data)
assert man["config_sha256"] == STAMPED_SHA, "the instances were made under another configuration"
train_ids = [r["id"] for r in man["instances"] if r["split"] == "train"]
assert len(train_ids) == cfg["data"]["n_train"]
if args.members:
    train_ids = train_ids[:args.members]
dev = torch.device(args.device)
torch.manual_seed(args.seed)
rng = np.random.default_rng(args.seed)
t_prep = time.time()
items = _prepare(cfg, args.data, train_ids, dev, energy=True, labels=False)
nets = build(cfg, items[0]["base"].shape[-1] + 1)
enc, dec, head = nets
for net in nets:
    net.to(dev)
params = [p for net in nets for p in net.parameters()]
betas = (0.9, 0.99) if "beta2" in args.recipe else (0.9, 0.999)
opt = torch.optim.AdamW(params, lr=tr["lr"], weight_decay=tr["weight_decay"], betas=betas)
total = a["epochs"] * cfg["data"]["n_train"]                  # the gate's schedule, whatever --epochs and --members
sched = make_scheduler(opt, total)
use_cap = "cap" in args.recipe
window = collections.deque(maxlen=WINDOW)
state = {"epoch": 0, "step": 0, "prev_rel_var": None, "collapse_step": None, "collapses": [], "bursts": [],
         "cap_events": [], "epoch_loss": [], "epoch_seconds": [], "resumes": []}

if ck_path.exists():
    s = torch.load(ck_path, map_location=dev, weights_only=False)
    assert s["meta"] == {"seed": args.seed, "recipe": args.recipe, "members": len(train_ids)}, "another run's state"
    for net, k in zip(nets, ("enc", "dec", "head")):
        net.load_state_dict(s[k])
    opt.load_state_dict(s["opt"]); sched.load_state_dict(s["sched"])
    rng.bit_generator.state = s["rng"]; torch.set_rng_state(s["torch_rng"].cpu())   # the state is loaded onto the device
    window.extend(s["window"])
    state = s["state"]
    state["resumes"].append({"epoch": state["epoch"], "time": now(), "extend": EXTENDING})
    kept = [l for l in open(steps_path) if l.strip() and json.loads(l).get("step", 0) <= state["step"]]
    with open(steps_path, "w") as fh:                         # drop the records after the checkpoint
        fh.writelines(kept)
    print(f"{args.name}: resumed at epoch {state['epoch']}, step {state['step']}", flush=True)

probe_item = items[0]
probe_D = torch.tensor([0.5, 2.0, 8.0], device=dev)
unit_items = [items[i] for i in UNIT_MEMBERS if i < len(items)]


def gnorm(net) -> float:
    g = [p.grad.detach().reshape(-1) for p in net.parameters() if p.grad is not None]
    return float(torch.linalg.vector_norm(torch.cat(g))) if g else 0.0


def _rel_var(t) -> float:
    tc = t - t.mean(dim=1, keepdim=True)
    return float((tc.pow(2).sum(-1).mean(1) / t.pow(2).sum(-1).mean(1)).mean())


def _ms(t) -> float:
    return float(t.pow(2).sum(-1).mean())


def _nv(t) -> float:
    return float((t - t.mean(dim=1, keepdim=True)).pow(2).sum(-1).mean())


@torch.no_grad()
def probe_stats() -> dict:
    """As probes/c2_diag/branch.py: the first training member at D = 0.5, 2 and 8 mm."""
    for net in nets:
        net.eval()
    x = enc.inp(inputs(probe_item["base"], probe_D))
    stages, ms, nv = [_rel_var(x)], [_ms(x)], [_nv(x)]
    first = {}
    for k, blk in enumerate(enc.blocks):
        if k == 0:
            hh = blk.ln1(x)
            att = blk.attn(hh, hh, hh, need_weights=False)[0]
            mlp = blk.mlp(blk.ln2(x + att))
            first = {"attn_ms": _ms(att), "attn_node_var": _nv(att), "mlp_ms": _ms(mlp), "mlp_node_var": _nv(mlp)}
        x = blk(x)
        stages.append(_rel_var(x)); ms.append(_ms(x)); nv.append(_nv(x))
    h = enc.norm(x)
    hc = h - h.mean(dim=1, keepdim=True)
    rel_var = (hc.pow(2).sum(-1).mean(1) / h.pow(2).sum(-1).mean(1)).tolist()
    z = field(enc, dec, head, probe_item["base"], probe_item["maps"], probe_D, cfg["map"]["T"], lift=True)
    s = probe_D + probe_item["maps"]["delta"]
    for net in nets:
        net.train()
    return {"latent_rel_var": rel_var, "e_over_s": (z[:, -1] / s).tolist(), "stage_rel_var": stages,
            "stage_ms": ms, "stage_node_var": nv, "first_block": first,
            "dec_last_w": float(dec[-1].weight.norm()), "head_last_w": float(head[-1].weight.norm())}


@torch.no_grad()
def unit_stats() -> dict:
    """As probes/c2_diag/units.py: for the two hidden layers of the decoder and of the head, the share of units whose
    largest GELU input over every node, displacement and member is below -3 and below -5."""
    for net in nets:
        net.eval()
    umax = {}
    for it in unit_items:
        h = enc(inputs(it["base"], probe_D))
        pooled = h.mean(dim=-2, keepdim=True)
        u1 = dec[0](torch.cat([h, pooled.expand_as(h)], dim=-1))
        u2 = dec[2](dec[1](u1))
        g1 = head[0](pooled[:, 0])
        g2 = head[2](head[1](g1))
        for k, v in (("dec1", u1.amax(dim=(0, 1))), ("dec2", u2.amax(dim=(0, 1))), ("head1", g1.amax(dim=0)),
                     ("head2", g2.amax(dim=0))):
            umax[k] = v if k not in umax else torch.maximum(umax[k], v)
    for net in nets:
        net.train()
    return {k: {"below_-3": float((v < -3).float().mean()), "below_-5": float((v < -5).float().mean())}
            for k, v in umax.items()}


def save(status: str) -> None:
    tmp = ck_path.with_suffix(".tmp")
    torch.save({"enc": enc.state_dict(), "dec": dec.state_dict(), "head": head.state_dict(), "opt": opt.state_dict(),
                "sched": sched.state_dict(), "rng": rng.bit_generator.state, "torch_rng": torch.get_rng_state(),
                "window": list(window), "state": state,
                "meta": {"seed": args.seed, "recipe": args.recipe, "members": len(train_ids)}}, tmp)
    os.replace(tmp, ck_path)
    summary(status)


def summary(status: str) -> None:
    out = {"name": args.name, "status": status, "time": now(), "seed": args.seed, "recipe": args.recipe,
           "betas": list(betas), "cap": CAP if use_cap else None, "epochs_asked": args.epochs,
           "epochs_done": state["epoch"], "steps": state["step"], "members": len(train_ids),
           "schedule_total_steps": total, "device": str(dev),
           "gpu": torch.cuda.get_device_name(0) if dev.type == "cuda" else None, "torch": torch.__version__,
           "epoch_loss": state["epoch_loss"], "epoch_seconds": state["epoch_seconds"],
           "bursts": state["bursts"], "cap_events": state["cap_events"], "collapses": state["collapses"],
           "resumes": state["resumes"], "config_sha256": STAMPED_SHA, "test_hooks": TEST,
           "peak_memory_GiB": (torch.cuda.max_memory_allocated() / 2 ** 30) if dev.type == "cuda" else None}
    tmp = sum_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=1))
    os.replace(tmp, sum_path)


print(f"{args.name}: seed {args.seed}, recipe {args.recipe}, {args.epochs} epochs of {len(train_ids)} members on {dev}"
      f" (prepared in {time.time() - t_prep:.0f} s), started {now()}", flush=True)
log = open(steps_path, "a")
if state["step"] == 0:
    log.write(json.dumps({"header": True, "name": args.name, "seed": args.seed, "recipe": args.recipe,
                          "betas": list(betas), "cap": CAP if use_cap else None, "window": WINDOW,
                          "torch": torch.__version__, "device": str(dev), "started": now(),
                          "test_hooks": TEST}) + "\n")
    p0 = probe_stats()
    state["prev_rel_var"] = float(np.mean(p0["latent_rel_var"]))
    log.write(json.dumps({"step": 0, "probe": p0, "units": unit_stats()}) + "\n"); log.flush()
for net in nets:
    net.train()
status, stop_at = "running", None
if state["collapse_step"] is not None and args.stop_on_collapse:
    stop_at = state["collapse_step"] + args.after_collapse
summary(status)
while state["epoch"] < args.epochs and status == "running":
    t0 = time.perf_counter()
    order = rng.permutation(len(items))
    loss_sum = 0.0
    for i in order:
        loss, D = step_loss(cfg, nets, items[i], rng, False, dev)
        if not torch.isfinite(loss):
            status = f"non-finite loss at step {state['step']}"
            break
        opt.zero_grad(set_to_none=True)
        loss.backward()
        g = {"enc": gnorm(enc), "dec": gnorm(dec), "head": gnorm(head)}
        rec = {}
        if len(window) == WINDOW:
            med = float(np.median(window))
            if g["enc"] > BURST * med:
                state["bursts"].append({"step": state["step"] + 1, "ratio": g["enc"] / med})
                rec["burst"] = g["enc"] / med
            if use_cap and g["enc"] > CAP * med:
                scale = CAP * med / g["enc"]
                for p in enc.parameters():
                    if p.grad is not None:
                        p.grad.mul_(scale)
                state["cap_events"].append({"step": state["step"] + 1, "ratio": g["enc"] / med})
                rec["cap_scale"] = scale
        window.append(g["enc"])
        total_norm = float(torch.nn.utils.clip_grad_norm_(params, tr["clip"]))
        opt.step()
        sched.step()
        state["step"] += 1
        step = state["step"]
        lv = float(loss.detach())
        loss_sum += lv
        rec = {"step": step, "inst": int(i), "D": [round(float(x), 4) for x in D], "loss": lv, "grad": g,
               "grad_total": total_norm, "lr": opt.param_groups[0]["lr"], **rec}
        if step % PROBE_EVERY == 0:
            pr = probe_stats()
            rec["probe"] = pr
            rv = float(np.mean(pr["latent_rel_var"]))
            if (state["prev_rel_var"] is not None and rv < state["prev_rel_var"] / 3.0) or step == FAKE_COLLAPSE:
                state["collapses"].append({"step": step, "rel_var": rv, "before": state["prev_rel_var"]})
                rec["collapse"] = True
                rec["units"] = unit_stats()
                print(f"  collapse at the probe of step {step}: relative variance {state['prev_rel_var']:.4f} -> "
                      f"{rv:.4f}", flush=True)
                if state["collapse_step"] is None:
                    state["collapse_step"] = step
                    if args.stop_on_collapse:
                        stop_at = step + args.after_collapse
            state["prev_rel_var"] = rv
        if step % UNITS_EVERY == 0 and "units" not in rec:
            rec["units"] = unit_stats()
        log.write(json.dumps(rec) + "\n")
        if step % 16 == 0 or step <= 16:
            log.flush()
        if stop_at is not None and step >= stop_at:
            status = f"stopped {args.after_collapse} steps after the collapse at step {state['collapse_step']}"
            break
    log.flush()
    if status.startswith("non-finite") or status.startswith("stopped"):
        break
    if dev.type == "cuda":
        torch.cuda.synchronize()
    state["epoch"] += 1
    state["epoch_loss"].append(loss_sum / len(items))
    state["epoch_seconds"].append(round(time.perf_counter() - t0, 2))
    print(f"epoch {state['epoch']} loss {state['epoch_loss'][-1]:.6g} {state['epoch_seconds'][-1]} s "
          f"({state['epoch_seconds'][-1] / len(items):.3f} s a step); bursts {len(state['bursts'])}, "
          f"cap events {len(state['cap_events'])}, collapses {len(state['collapses'])}", flush=True)
    save("running")
    if state["epoch"] in SNAPSHOTS:
        tmp = (run / f"snap_e{state['epoch']}.pt").with_suffix(".tmp")
        torch.save({"enc": enc.state_dict(), "dec": dec.state_dict(), "head": head.state_dict(),
                    "step": state["step"], "meta": {"seed": args.seed, "recipe": args.recipe,
                                                    "members": len(train_ids)}}, tmp)
        os.replace(tmp, run / f"snap_e{state['epoch']}.pt")
log.close()
if status == "running":
    status = "finished"
u_end = unit_stats()
p_end = probe_stats()
with open(steps_path, "a") as fh:
    fh.write(json.dumps({"end": True, "step": state["step"], "status": status, "probe": p_end, "units": u_end,
                         "time": now()}) + "\n")
tmp = (run / "final_state.pt").with_suffix(".tmp")
torch.save({"enc": enc.state_dict(), "dec": dec.state_dict(), "head": head.state_dict(), "step": state["step"],
            "meta": {"seed": args.seed, "recipe": args.recipe, "members": len(train_ids)}}, tmp)
os.replace(tmp, run / "final_state.pt")
if not args.no_preds and not status.startswith("non-finite"):
    ok = predict(cfg, nets, args.data, run / "preds.npz", dev)
    print("predictions written" if ok else "predictions not finite, not written", flush=True)
summary(status)
print(f"{args.name}: {status}; {state['step']} steps; bursts {len(state['bursts'])}, cap events "
      f"{len(state['cap_events'])}, collapses {len(state['collapses'])}; ended {now()}", flush=True)
