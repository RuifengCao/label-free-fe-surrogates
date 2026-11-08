"""The numbers the draft verdict cites, recomputed by the auditor from the returned records (verdict.json per-pair
rows, manifest, histories, bench, logs). Usage: python -I -B draft_numbers.py RECORDS JOINT PRESPEC OUT_JSON"""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

REC, JOINT, PRESPEC, OUT = sys.argv[1:5]
REC = Path(REC)
sys.path.insert(0, JOINT)
LV = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
RUNS = [("label_free", s) for s in "012"] + [("supervised_64", s) for s in "012"]
v = json.loads((REC / "verdict.json").read_text())
man = json.loads((REC / "manifest.json").read_text())
prm = {r["id"]: r["params"] for r in man["instances"]}
ev = sorted(r["id"] for r in man["instances"] if r["split"] == "eval")
fy = np.array([prm[i]["fy"] for i in ev])
N = {}


def q(v_, p):
    s = sorted(float(x) for x in v_)
    h = (len(s) - 1) * p
    lo = math.floor(h)
    t = h - lo
    a, b = s[lo], s[min(lo + 1, len(s) - 1)]
    if t == 0:
        return a
    if math.isinf(b):
        return math.inf
    return a + t * (b - a)


def grid(arm, s, key):
    rows = v["arms"][arm][s]["eval_rows"]
    return np.array([[r[key] for r in rows[i]] for i in ev], float)


for arm, s in RUNS:
    k = f"{arm}_s{s}"
    A = np.abs(grid(arm, s, "curve_err"))
    S = grid(arm, s, "curve_err")
    d = {"median": q(A.ravel(), .5), "p90": q(A.ravel(), .9), "above10": int((A > .1).sum()),
         "above10_by_level": [int((A[:, l] > .1).sum()) for l in range(7)],
         "median_by_level": [q(A[:, l], .5) for l in range(7)], "p90_by_level": [q(A[:, l], .9) for l in range(7)],
         "signed_median": q(S.ravel(), .5), "signed_median_by_level": [q(S[:, l], .5) for l in range(7)]}
    for key in ("F_err", "e_err", "gap", "u_rel_l2", "iou_contact", "iou_plastic", "F_sigma_err", "bolt_err", "bound"):
        G = grid(arm, s, key)
        d[key + "_median"] = q(G[~np.isnan(G)].ravel(), .5)
    d["absF_median"] = q(np.abs(grid(arm, s, "F_err")).ravel(), .5)
    a8 = A[:, 6]
    lo = fy < 300
    d["n_below300"] = int(lo.sum())
    d["median8_below300"] = q(a8[lo], .5)
    d["median8_atabove300"] = q(a8[~lo], .5)
    d["pearson8"] = float(np.corrcoef(a8, fy)[0, 1]) if np.isfinite(a8).all() else None
    top = np.argsort(-a8, kind="stable")[:5]
    d["top5_8mm"] = [(ev[j], round(float(fy[j]), 2), float(a8[j]), float(A[j, 0])) for j in top]
    # the tail: the pairs at or above the per-seed 90th percentile
    thr = d["p90"]
    tail = [(i, l) for i in range(64) for l in range(7) if A[i, l] > thr]
    d["tail_n"] = len(tail)
    d["tail_low_fy"] = sum(fy[i] < 300 for i, _ in tail)
    d["tail_by_level"] = [sum(1 for _, l in tail if l == ll) for ll in range(7)]
    d["tail_low_fy_at_ge2mm"] = sum(1 for i, l in tail if fy[i] < 300 and l >= 2)
    d["tail_members"] = len({i for i, _ in tail})
    ab = [(i, l) for i in range(64) for l in range(7) if A[i, l] > .1]
    d["above10_low_fy"] = sum(fy[i] < 300 for i, _ in ab)
    d["above10_low_fy_ge2mm"] = sum(1 for i, l in ab if fy[i] < 300 and l >= 2)
    d["above10_ge2mm"] = sum(1 for i, l in ab if l >= 2)
    d["above10_at_8mm_low_fy"] = sum(1 for i, l in ab if fy[i] < 300 and l == 6)
    # largest level of each run's median
    d["argmax_level_median"] = LV[int(np.argmax(d["median_by_level"]))]
    d["argmin_level_median"] = LV[int(np.argmin(d["median_by_level"]))]
    N[k] = d

# tested members
T = {}
for arm, s in RUNS:
    for t, rows in v["arms"][arm][s]["tested"].items():
        T[f"{arm}_s{s}:{t[7:]}"] = [r["curve_err"] for r in rows]
N["tested"] = T
N["s0_tested_min_finite_abs"] = min(abs(x) for k_, r in T.items() if k_.startswith("label_free_s0") for x in r
                                    if math.isfinite(x))
# fy range of held-out
N["fy_range"] = [float(fy.min()), float(fy.max())]
N["fy_of"] = {i: prm[i]["fy"] for i in ("eval_0026", "eval_0049", "eval_0043", "eval_0046", "eval_0034", "eval_0052")}

# bench against training instance sizes
b = json.loads((REC / "bench.json").read_text())
nodes = {r["id"]: r["nodes"] for r in man["instances"]}
tr = [r["id"] for r in man["instances"] if r["split"] == "train"]
N["bench"] = {"mean": b["seconds_per_step_mean"], "median": b["seconds_per_step_median"], "max": b["seconds_per_step_max"],
              "n_losses": len(b["losses"]), "finite": b["losses_finite"], "peak": b["peak_memory_GiB"],
              "energies": b["energy_GiB_training_set"], "sum_GiB": b["peak_memory_GiB"] + b["energy_GiB_training_set"],
              "pred_h": 345600 * b["seconds_per_step_mean"] / 3600,
              "bench_nodes_mean": float(np.mean([nodes[i] for i in b["instances"]])),
              "train_nodes_mean": float(np.mean([nodes[i] for i in tr])),
              "gpu_MiB_total": 32607, "gpu_GiB_total": 32607 / 1024, "threads": b["threads"],
              "bench_instances_are_first8": b["instances"] == tr[:8]}

# config: the returned c2_config.json against the stamped configuration, its canonical hash
from c2.config import config, sha256, canonical  # noqa: E402
cj = json.loads((REC / "c2_config.json").read_text())
N["config"] = {"returned_json_equals_stamped": cj == json.loads(json.dumps(config())),
               "returned_json_canonical_sha256": hashlib.sha256(canonical(cj)).hexdigest(),
               "stamped_sha256": sha256(config())}
# config.log: twenty hashes against the pre-specification's table, six repository lines
cl = (REC / "config.log").read_text().splitlines()
pre = Path(PRESPEC).read_text()
tab = dict(re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", pre, flags=re.M))
lines20 = [ln.split() for ln in cl[1:21]]
N["config_log"] = {"first": cl[0], "n_lines": len(cl),
                   "twenty_equal_prespec": all(len(x) == 2 and tab.get(x[0]) == x[1] for x in lines20) and len(lines20) == 20,
                   "repo_lines": sum(1 for ln in cl if ln.startswith("repository ") and ln.endswith(" checked")),
                   "repo_equal_prespec": all(tab.get(ln.split()[1]) == ln.split()[2] for ln in cl if ln.startswith("repository ")),
                   "prespec_table_entries": len(tab)}
# loss trajectory of seed 0
h0 = json.loads((REC / "runs" / "label_free_s0" / "history.json").read_text())["loss"]
N["s0_loss_first10"] = h0[:10]
N["s0_loss_by_20"] = [float(np.mean(h0[i:i + 20])) for i in range(0, 200, 20)]
for s in "12":
    h = json.loads((REC / "runs" / f"label_free_s{s}" / "history.json").read_text())["loss"]
    N[f"s{s}_loss_by_20"] = [float(np.mean(h[i:i + 20])) for i in range(0, 200, 20)]
Path(OUT).write_text(json.dumps(N, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
print("ok")
