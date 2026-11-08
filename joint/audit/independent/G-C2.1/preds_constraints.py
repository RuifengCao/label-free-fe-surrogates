"""Predictions against the regenerated instances: fixed unknowns zero, contact unknowns non-negative (all runs);
seed 0 of the label-free arm against the network's starting field. Auditor's script.
Usage: python -I -B preds_constraints.py RECORDS INST_DIR OUT_JSON"""
import json
import math
import sys
from pathlib import Path

import numpy as np

REC, INST, OUT = map(Path, sys.argv[1:4])
RUNS = [f"label_free_s{s}" for s in range(3)] + [f"supervised_64_s{s}" for s in range(3)]
T = 1e-3
LV = np.array([0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0])
man = json.loads((REC / "manifest.json").read_text())
ids = [r["id"] for r in man["instances"] if r["split"] in ("eval", "tested")]
params = {r["id"]: r["params"] for r in man["instances"]}
ex = {}
for iid in ids:
    with np.load(INST / f"{iid}.npz") as z:
        ex[iid] = {k: z[k] for k in ("fixed", "cidx", "e_idx", "delta", "node_flags", "nodes", "head", "v")}
R = {"constraints": {}}
for run in RUNS:
    with np.load(REC / "runs" / run / "preds.npz") as z:
        P = {k: z[k].astype(np.float64) for k in z.files}
    nfix_bad, ncon_neg, min_con, n_fixed, n_con = 0, 0, math.inf, 0, 0
    for iid in ids:
        f = np.asarray(ex[iid]["fixed"], bool)
        c = np.asarray(ex[iid]["cidx"], int)
        Z = P[iid]
        nfix_bad += int((Z[:, f] != 0).sum())
        ncon_neg += int((Z[:, c] < 0).sum())
        min_con = min(min_con, float(Z[:, c].min()))
        n_fixed += f.sum() * 7
        n_con += c.size * 7
    R["constraints"][run] = {"fixed_nonzero": nfix_bad, "contact_negative": ncon_neg, "contact_min": min_con,
                             "fixed_values": int(n_fixed), "contact_values": int(n_con)}
    if run == "label_free_s0":
        S0 = P
# seed 0 against the starting field: zero, and T ln2 (D + delta) on the non-negative unknowns
d0, rel_label, rel_start, uniform = [], [], [], []
labs = {}
for iid in ids:
    with np.load(REC / "labels" / f"{iid}.npz") as z:
        labs[iid] = {"z": z["z"], "e": z["e"], "F": z["F"]}
for iid in [i for i in ids if i.startswith("eval_")]:
    e = ex[iid]
    n = e["nodes"].shape[0]
    f = np.asarray(e["fixed"], bool)
    c = np.asarray(e["cidx"], int)
    for l, D in enumerate(LV):
        start = np.zeros(S0[iid].shape[1])
        start[c] = T * math.log(2.0) * (D + float(e["delta"]))
        zr = labs[iid]["z"][l]
        diff = S0[iid][l] - start
        rel_start.append(float(np.linalg.norm(diff) / np.linalg.norm(zr)))
        rel_label.append(float(np.linalg.norm(S0[iid][l]) / np.linalg.norm(zr)))
        d0.append(float(np.linalg.norm(start) / np.linalg.norm(zr)))
        # is the nodal field uniform over the free, non-contact nodes? (u_x, u_y, u_z per node)
        U = S0[iid][l][:3 * n].reshape(n, 3)
        Fm = f[:3 * n].reshape(n, 3)
        cm = np.zeros(3 * n, bool); cm[c] = True; cm = cm.reshape(n, 3)
        web = np.asarray(e["node_flags"])[:, 4].astype(bool)
        row = []
        for j in range(3):
            sel = ~Fm[:, j] & ~cm[:, j] & (~web if j == 0 else np.ones(n, bool))
            row.append(int(np.unique(U[sel, j]).size))
        uniform.append(row)
uniform = np.array(uniform)
R["seed0"] = {"norm_start_over_label_median": float(np.median(d0)),
              "norm_pred_over_label_median": float(np.median(rel_label)),
              "norm_pred_minus_start_over_label_median": float(np.median(rel_start)),
              "norm_pred_minus_start_over_label_max": float(np.max(rel_start)),
              "distinct_ux_uy_uz_free_noncontact_nonweb(x)_max_per_pair": uniform.max(axis=0).tolist(),
              "distinct_ux_uy_uz_median_per_pair": np.median(uniform, axis=0).tolist()}
# example pair: the values of seed 0's field
iid, l = "eval_0000", 6
e = ex[iid]; n = e["nodes"].shape[0]
R["seed0"]["example_eval_0000_8mm_unique_values"] = np.unique(np.round(S0[iid][l], 9)).tolist()
R["seed0"]["example_eval_0000_8mm_start_softplus"] = T * math.log(2) * (8.0 + float(e["delta"]))
# infinite pairs of seed 0 and the preload ratio
v = json.loads((REC / "verdict.json").read_text())
inf_members = {}
for iid, rows in v["arms"]["label_free"]["0"]["eval_rows"].items():
    k = sum(math.isinf(r["curve_err"]) for r in rows)
    if k:
        inf_members[iid] = k
rho = {i: params[i]["rho"] for i in ids if i.startswith("eval_")}
R["seed0"]["members_with_infinite"] = len(inf_members)
R["seed0"]["rho_of_members_with_infinite_min_max"] = [min(rho[i] for i in inf_members), max(rho[i] for i in inf_members)]
R["seed0"]["rho_of_members_without_infinite_min_max"] = [min(rho[i] for i in rho if i not in inf_members),
                                                          max(rho[i] for i in rho if i not in inf_members)]
R["seed0"]["e_pred_of_infinite_pairs_min_max"] = [
    min(float(S0[i][l, -1]) for i in inf_members for l, r in enumerate(v["arms"]["label_free"]["0"]["eval_rows"][i]) if math.isinf(r["curve_err"])),
    max(float(S0[i][l, -1]) for i in inf_members for l, r in enumerate(v["arms"]["label_free"]["0"]["eval_rows"][i]) if math.isinf(r["curve_err"]))]
OUT.write_text(json.dumps(R, indent=1))
print(json.dumps(R, indent=1))
