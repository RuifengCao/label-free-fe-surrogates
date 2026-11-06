"""CPU pilot of G-C2.1's label-free training with evaluations along the way (not the gate). Reuses a pilot data
directory made by pilot_cpu.py (exports and held-out labels, seeds 8 and 7), and the gate's own training and
evaluation code (c2.train.step_loss, c2.model, c2.evaluate.metrics), with the configuration's settings except the
model size, the number of members and the number of steps.
Usage: python pilot_trend.py JOINT DATA OUT --epochs 300 --eval_at 30,60,120,200,300 [--dim 64 --depth 2] [--lr 1e-3]"""
import argparse, copy, json, sys, time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("joint"); ap.add_argument("data"); ap.add_argument("out")
ap.add_argument("--epochs", type=int, default=300); ap.add_argument("--eval_at", default="30,60,120,200,300")
ap.add_argument("--dim", type=int, default=64); ap.add_argument("--depth", type=int, default=2)
ap.add_argument("--lr", type=float, default=1e-3); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--fields", type=int, default=4)
ap.add_argument("--lift", default="none")
ap.add_argument("--d_fixed", type=float, default=0.0, help="train at this end displacement only (0: the configured sampling)")
ap.add_argument("--train_ids", default="", help="comma-separated ids to train on (default: the training split)")
a = ap.parse_args()
sys.path.insert(0, a.joint); sys.path.insert(0, str(Path(a.joint).parent / "src"))
import numpy as np
import torch
from c2.config import config
from c2.data import manifest, load_export, load_label
from c2.train import _prepare, step_loss
from c2.model import build, field
from c2.instance import ExportedProblem
from c2.evaluate import metrics
from fejepa.train.schedule import make_scheduler

cfg = copy.deepcopy(config())
cfg["model"].update(dim=a.dim, depth=a.depth, heads=4, activation_checkpointing=False)
cfg["training"]["lr"] = a.lr
cfg["training"]["fields_per_step"] = a.fields
cfg["model"]["lift"] = a.lift
if a.d_fixed > 0:
    cfg["training"]["D_min_mm"] = a.d_fixed
    cfg["family"]["D_max_mm"] = a.d_fixed
man = manifest(a.data)
tr = [r["id"] for r in man["instances"] if r["split"] == "train"]
if a.train_ids:
    tr = a.train_ids.split(",")
ev = [r["id"] for r in man["instances"] if r["split"] in ("eval", "tested")]
torch.manual_seed(a.seed); rng = np.random.default_rng(a.seed)
dev = torch.device("cpu")
items = _prepare(cfg, a.data, tr, dev, energy=True, labels=False)
nets = build(cfg, items[0]["base"].shape[-1] + 1)
params = [p for n in nets for p in n.parameters()]
opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=cfg["training"]["weight_decay"])
total = a.epochs * len(items)
sched = make_scheduler(opt, total)
eval_at = {int(v) for v in a.eval_at.split(",")}
probs = {}
for iid in ev:
    ex, _ = load_export(Path(a.data) / "inst" / f"{iid}.npz")
    P = ExportedProblem(ex); ref = load_label(a.data, iid)
    probs[iid] = (P, ex, ref, [P.evaluate(ref["z"][l], float(ref["D"][l]))["plastic"] for l in range(ref["D"].size)])
ev_items = _prepare(cfg, a.data, ev, dev, energy=False, labels=False)
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
log = {"args": vars(a), "members": len(items), "steps_total": total, "loss": [], "evals": []}
t0 = time.time()
for epoch in range(1, a.epochs + 1):
    for n in nets: n.train()
    s = 0.0
    for i in rng.permutation(len(items)):
        loss, _ = step_loss(cfg, nets, items[i], rng, False, dev)
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(params, cfg["training"]["clip"]); opt.step(); sched.step()
        s += float(loss.detach())
    log["loss"].append(s / len(items))
    if epoch in eval_at:
        for n in nets: n.eval()
        rows = {}
        with torch.no_grad():
            for it in ev_items:
                P, ex, ref, rpl = probs[it["id"]]
                lv = torch.as_tensor(ref["D"], dtype=torch.float32)
                Z = field(*nets, it["base"], it["maps"], lv, cfg["map"]["T"], lift=a.lift == "web").double().numpy()
                rows[it["id"]] = [metrics(P, ex, Z[l], ref, rpl[l], l) for l in range(ref["D"].size)]
        evr = [r for k, v in rows.items() if k.startswith("eval") for r in v]
        by = {}
        for r in evr:
            by.setdefault(r["D"], []).append(r)
        med = lambda k, rr: float(np.median([abs(r[k]) for r in rr]))  # noqa: E731
        e = {"epoch": epoch, "step": epoch * len(items), "seconds": round(time.time() - t0),
             "median_abs_curve_err": med("curve_err", evr), "p90_abs_curve_err": float(np.quantile([abs(r["curve_err"]) for r in evr], 0.9)),
             "by_level_median_abs_curve_err": {str(k): med("curve_err", v) for k, v in sorted(by.items())},
             "tested_curve_err": {k: [round(r["curve_err"], 4) for r in v] for k, v in rows.items() if k.startswith("tested")},
             "median_abs_F_err": med("F_err", evr), "p90_abs_F_err": float(np.quantile([abs(r["F_err"]) for r in evr], 0.9)),
             "median_abs_F_sigma_err": med("F_sigma_err", evr), "median_abs_e_err": med("e_err", evr),
             "median_gap": float(np.median([r["gap"] for r in evr])), "median_bound": float(np.median([r["bound"] for r in evr])),
             "median_iou_contact": float(np.median([r["iou_contact"] for r in evr])),
             "median_iou_plastic": float(np.median([r["iou_plastic"] for r in evr])),
             "median_abs_bolt_err": med("bolt_err", evr), "within_bound": float(np.mean([r["within_bound"] for r in evr])),
             "by_level_median_abs_F_err": {str(k): med("F_err", v) for k, v in sorted(by.items())},
             "by_level_median_gap": {str(k): float(np.median([r["gap"] for r in v])) for k, v in sorted(by.items())},
             "tested_F_err": {k: [round(r["F_err"], 4) for r in v] for k, v in rows.items() if k.startswith("tested")}}
        log["evals"].append(e)
        print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in e.items()}), flush=True)
        (out / "trend.json").write_text(json.dumps(log, indent=1))
    if epoch % 10 == 0:
        print(f"epoch {epoch} loss {log['loss'][-1]:.5f} {round(time.time() - t0)} s", flush=True)
(out / "trend.json").write_text(json.dumps(log, indent=1))
torch.save({"enc": nets[0].state_dict(), "dec": nets[1].state_dict(), "head": nets[2].state_dict(), "cfg": cfg,
            "args": vars(a)}, out / "model.pt")
print("done", flush=True)
