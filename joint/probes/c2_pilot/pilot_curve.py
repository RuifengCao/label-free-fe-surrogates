"""Evaluate a saved pilot model (pilot_trend.py's model.pt) with the full metrics of c2.evaluate, including the
distance from the reference curve at the predicted deformation (exact solves). Not the gate.
Usage: python pilot_curve.py JOINT DATA RUN_DIR [D_MAX the model was trained with, default the family's]"""
import json, sys
from pathlib import Path

sys.path.insert(0, sys.argv[1]); sys.path.insert(0, str(Path(sys.argv[1]).parent / "src"))
import numpy as np
import torch
from c2.data import manifest, load_export, load_label
from c2.instance import ExportedProblem
from c2.model import features, maps, build, field
from c2.evaluate import metrics
import c2.model
if len(sys.argv) > 4:
    c2.model.D_MAX = float(sys.argv[4])      # the load feature's scale the model was trained with

data, run = Path(sys.argv[2]), Path(sys.argv[3])
st = torch.load(run / "model.pt", weights_only=False)
cfg, args = st["cfg"], st["args"]
nets = build(cfg, 21)
for n_, k in zip(nets, ("enc", "dec", "head")):
    n_.load_state_dict(st[k]); n_.eval()
rows = {}
for r in manifest(data)["instances"]:
    if r["split"] not in ("eval", "tested"):
        continue
    iid = r["id"]
    ex, q = load_export(data / "inst" / f"{iid}.npz"); ref = load_label(data, iid); P = ExportedProblem(ex)
    with torch.no_grad():
        Z = field(*nets, torch.as_tensor(features(ex, q), dtype=torch.float32), maps(ex, "cpu"),
                  torch.as_tensor(ref["D"], dtype=torch.float32), cfg["map"]["T"],
                  lift=args.get("lift", "none") == "web").double().numpy()
    rpl = [P.evaluate(ref["z"][l], float(ref["D"][l]))["plastic"] for l in range(ref["D"].size)]
    rows[iid] = [metrics(P, ex, Z[l], ref, rpl[l], l) for l in range(ref["D"].size)]
evr = [x for k, v in rows.items() if k.startswith("eval") for x in v]
med = lambda k: float(np.median([abs(x[k]) for x in evr]))  # noqa: E731
p90 = lambda k: float(np.quantile([abs(x[k]) for x in evr], 0.9))  # noqa: E731
by = {}
for x in evr:
    by.setdefault(x["D"], []).append(x)
out = {"run": run.name, "median_abs_curve_err": med("curve_err"), "p90_abs_curve_err": p90("curve_err"),
       "median_abs_F_err": med("F_err"), "p90_abs_F_err": p90("F_err"), "median_abs_e_err": med("e_err"),
       "median_abs_F_sigma_err": med("F_sigma_err"), "median_gap": float(np.median([x["gap"] for x in evr])),
       "by_level_median_abs_curve_err": {str(k): float(np.median([abs(x["curve_err"]) for x in v])) for k, v in sorted(by.items())},
       "by_level_median_abs_F_err": {str(k): float(np.median([abs(x["F_err"]) for x in v])) for k, v in sorted(by.items())},
       "tested": {k: [{kk: round(x[kk], 4) for kk in ("D", "curve_err", "F_err", "e_err", "gap")} for x in v]
                  for k, v in rows.items() if k.startswith("tested")}}
(run / "curve_eval.json").write_text(json.dumps({"summary": out, "rows": rows}, indent=1))
print(json.dumps(out, indent=1))
