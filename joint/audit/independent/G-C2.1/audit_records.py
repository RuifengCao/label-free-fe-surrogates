"""Independent audit of the G-C2.1 return package: labels and ledger, training histories and logs, predictions,
criteria and per-pair columns recomputed from the records (no FE solve). Written by the auditor; does not import the
author's audit scripts. Usage: python -I -B audit_records.py RECORDS OUT_JSON"""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

REC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
K_S = 2.0e4
EVAL_LV = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
TRAIN_LV = [0.75, 1.5, 2.5, 3.5, 5.0, 7.0]
LIMITS = {"min_gap": (">=", -1e-12), "min_lambda": (">=", -1e-8), "max_complementarity": ("<=", 1e-8),
          "max_lambda_inactive": ("<=", 1e-6), "max_residual_unconstrained": ("<=", 1e-6)}
RUNS = [f"label_free_s{s}" for s in range(3)] + [f"supervised_64_s{s}" for s in range(3)]
R = {}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def q_lin(v, q):
    """My own quantile: linear interpolation between order statistics (numpy's default), infinite if an infinite
    order statistic carries positive weight."""
    s = sorted(float(x) for x in v)
    n = len(s)
    h = (n - 1) * q
    lo = math.floor(h)
    t = h - lo
    a = s[lo]
    b = s[min(lo + 1, n - 1)]
    if t == 0:
        return a
    if math.isinf(a) or math.isinf(b):
        return math.inf if (math.isinf(b) and b > 0) else (a if math.isinf(a) else math.inf)
    return a + t * (b - a)


man = json.loads((REC / "manifest.json").read_text())
inst = man["instances"]
byid = {r["id"]: r for r in inst}
train_ids = [r["id"] for r in inst if r["split"] == "train"]
eval_ids = [r["id"] for r in inst if r["split"] == "eval"]
tested_ids = [r["id"] for r in inst if r["split"] == "tested"]
R["manifest"] = {"n": man["n"], "len": len(inst), "config": man["config_sha256"], "train": len(train_ids),
                 "eval": len(eval_ids), "tested": len(tested_ids),
                 "ids_unique": len({r["id"] for r in inst}) == len(inst),
                 "eval_sorted": eval_ids == sorted(eval_ids)}

# ---------------------------------------------------------------- labels and ledger
led = json.loads((REC / "ledger.json").read_text())
need = train_ids[:64] + eval_ids + tested_ids
lid = [e["id"] for e in led]
lab = {"entries": len(led), "unique": len(set(lid)), "set_equals_needed": set(lid) == set(need),
       "levels_ok": all(e["levels"] == (TRAIN_LV if byid[e["id"]]["split"] == "train" else EVAL_LV) for e in led),
       "converged": all(all(e["converged"]) for e in led),
       "n_levels": sum(len(e["levels"]) for e in led),
       "inst_sha_equals_manifest": all(e["inst_sha256"] == byid[e["id"]]["sha256"] for e in led),
       "solver": sorted({e["solver"] for e in led}),
       "seconds_min": min(e["seconds"] for e in led), "seconds_max": max(e["seconds"] for e in led),
       "iterations_max": max(max(e["iterations"]) for e in led),
       "iterations_total": sum(sum(e["iterations"]) for e in led),
       "F_vs_F_sigma_max_ledger": max(e["F_vs_F_sigma"] for e in led)}
worst = {k: (min if op == ">=" else max)(e["kkt_worst"][k] for e in led) for k, (op, _) in LIMITS.items()}
lab["worst"] = worst
lab["within"] = {k: (worst[k] >= v if op == ">=" else worst[k] <= v) for k, (op, v) in LIMITS.items()}
cl = json.loads((REC / "check_labels.log").read_text().strip().splitlines()[-1])
lab["check_labels_log_worst_equal"] = cl["worst"] == worst and cl["max_F_vs_F_sigma"] == lab["F_vs_F_sigma_max_ledger"]
# label.log against the ledger
ll = (REC / "label.log").read_text()
lines = re.findall(r"^(\S+) ([\d.]+) s (converged|NOT CONVERGED)$", ll, flags=re.M)
lab["label_log_lines"] = len(lines)
lab["label_log_ids_unique"] = len({x[0] for x in lines}) == len(lines)
lab["label_log_seconds_equal_ledger"] = all(abs(float(s) - {e["id"]: e["seconds"] for e in led}[i]) < 1e-9
                                             for i, s, _ in lines)
# returned label files (eval, tested)
mx_fs, mx_F, mx_e, bad = 0.0, 0.0, 0.0, []
for iid in eval_ids + tested_ids:
    p = REC / "labels" / f"{iid}.npz"
    e = {x["id"]: x for x in led}[iid]
    if sha(p) != e["label_sha256"]:
        bad.append(iid)
    with np.load(p) as z:
        D, Z, Pi, ee, F, Fs = z["D"], z["z"], z["Pi"], z["e"], z["F"], z["F_sigma"]
        assert list(D) == EVAL_LV and Z.shape == (7, byid[iid]["unknowns"]), iid
        mx_e = max(mx_e, float(np.abs(Z[:, -1] - ee).max()))
        mx_F = max(mx_F, float(np.max(np.abs(4 * K_S * (D - ee) - F) / np.abs(F))))
        mx_fs = max(mx_fs, float(np.max(np.abs(F - Fs) / np.abs(F))))
        assert (Pi > 0).all() and (F > 0).all()
lab["returned_label_files"] = len(eval_ids + tested_ids)
lab["label_sha_mismatch"] = bad
lab["max_abs_e_minus_zlast"] = mx_e
lab["max_rel_F_minus_4ks(D-e)"] = mx_F
lab["max_rel_F_vs_F_sigma_returned"] = mx_fs
R["labels"] = lab

# ---------------------------------------------------------------- training
tr = {}
for run in RUNS:
    h = json.loads((REC / "runs" / run / "history.json").read_text())
    loss = np.asarray(h["loss"], float)
    es = np.asarray(h["epoch_seconds"], float)
    spe = 512 if run.startswith("label_free") else 64
    log = (REC / f"train_{run}.log").read_text()
    ep = re.findall(r"^epoch (\d+) loss (\S+) (\S+) s$", log, flags=re.M)
    att = (REC / "runs" / run / "attempts.log").read_text().strip().splitlines()
    tr[run] = {"status": h.get("status"), "steps": h.get("steps"), "total_steps": h.get("total_steps"),
               "config": h.get("config_sha256"), "arm": h.get("arm"), "seed": h.get("seed"),
               "resumes": h.get("resumes"), "resumed_from_epoch": h.get("resumed_from_epoch"),
               "matmul_precision": h.get("matmul_precision"), "gpu": h.get("gpu"), "torch": h.get("torch"),
               "epochs": int(loss.size), "loss_finite": bool(np.isfinite(loss).all()),
               "loss_first": float(loss[0]), "loss_last": float(loss[-1]),
               "mean_1_20": float(loss[:20].mean()), "mean_181_200": float(loss[-20:].mean()),
               "min": float(loss.min()), "argmin_epoch": int(loss.argmin()) + 1, "max": float(loss.max()),
               "argmax_epoch": int(loss.argmax()) + 1,
               "epoch_s_median": float(np.median(es)), "epoch_s_min": float(es.min()), "epoch_s_max": float(es.max()),
               "s_per_step_median_epoch": float(np.median(es) / spe),
               "train_hours_sum_epochs": float(es.sum() / 3600),
               "peak_GiB": h.get("peak_memory_GiB"),
               "log_epoch_lines": len(ep),
               "log_losses_match_6sig": all(abs(float(l) - x) <= 5e-6 * abs(x) for (_, l, _), x in zip(ep, loss)),
               "log_seconds_match": all(abs(float(s) - x) < 1e-9 for (_, _, s), x in zip(ep, es)),
               "log_end": log.strip().splitlines()[-3:],
               "attempts": att}
R["training"] = tr

# ---------------------------------------------------------------- predictions and per-pair columns
v = json.loads((REC / "verdict.json").read_text())
labels = {}
for iid in eval_ids + tested_ids:
    with np.load(REC / "labels" / f"{iid}.npz") as z:
        labels[iid] = {k: z[k] for k in z.files}
pred = {}
for run in RUNS:
    arm, s = run.rsplit("_s", 1)
    box = v["arms"][arm][s]
    with np.load(REC / "runs" / run / "preds.npz") as z:
        keys = sorted(z.files)
        P = {k: z[k] for k in z.files}
    d = {"keys_ok": keys == sorted(eval_ids + tested_ids), "n_keys": len(keys),
         "dtype": sorted({str(P[k].dtype) for k in keys}),
         "shapes_ok": all(P[k].shape == (7, byid[k]["unknowns"]) for k in keys),
         "finite": all(bool(np.isfinite(P[k]).all()) for k in keys)}
    de, dF, n = 0.0, 0.0, 0
    e_ratio, nrm = [], []
    for iid in keys:
        rows = box["eval_rows"].get(iid) or box["tested"][iid]
        L = labels[iid]
        for l in range(7):
            ep = float(np.float64(P[iid][l, -1]))
            D = float(L["D"][l])
            e_err = ep / float(L["e"][l]) - 1
            F_err = 4 * K_S * (D - ep) / float(L["F"][l]) - 1
            assert rows[l]["D"] == D
            de = max(de, abs(e_err - rows[l]["e_err"]))
            dF = max(dF, abs(F_err - rows[l]["F_err"]))
            n += 1
            if iid in eval_ids:
                e_ratio.append(ep / float(L["e"][l]))
                nrm.append(float(np.linalg.norm(P[iid][l].astype(float)) / np.linalg.norm(L["z"][l])))
    d.update(pairs_checked=n, max_abs_diff_e_err=de, max_abs_diff_F_err=dF,
             e_ratio_median=float(np.median(e_ratio)), norm_ratio_median=float(np.median(nrm)),
             norm_ratio_max=float(np.max(nrm)))
    allv_eval = np.concatenate([P[k].ravel() for k in eval_ids])
    allv_all = np.concatenate([P[k].ravel() for k in keys])
    d.update(values_eval=int(allv_eval.size), distinct_eval=int(np.unique(allv_eval).size),
             values_all=int(allv_all.size), distinct_all=int(np.unique(allv_all).size),
             max_abs_all=float(np.abs(allv_all).max()), max_abs_eval=float(np.abs(allv_eval).max()))
    pred[run] = d
    if run == "label_free_s0":
        S0 = P
R["predictions"] = pred

# seed 0: distinct values per pair, how close to the starting field (T ln2 (D + delta) on the non-negative unknowns)
s0 = {}
dist_pp = [int(np.unique(S0[k][l]).size) for k in eval_ids for l in range(7)]
s0["distinct_per_pair_min_median_max"] = [min(dist_pp), float(np.median(dist_pp)), max(dist_pp)]
e0 = np.array([[S0[k][l, -1] for l in range(7)] for k in eval_ids], float)
s0["e_pred_min_max"] = [float(e0.min()), float(e0.max())]
s0["e_pred_negative_pairs"] = int((e0 < 0).sum())
s0["e_pred_by_level_median"] = [float(np.median(e0[:, l])) for l in range(7)]
e_ref = np.array([[labels[k]["e"][l] for l in range(7)] for k in eval_ids], float)
s0["e_ref_by_level_median"] = [float(np.median(e_ref[:, l])) for l in range(7)]
R["seed0"] = s0

# ---------------------------------------------------------------- criteria from the per-pair rows
crit = {}
med, p90 = [], []
for s in "012":
    box = v["arms"]["label_free"][s]
    rows = [r for iid in eval_ids for r in box["eval_rows"][iid]]
    a = [abs(r["curve_err"]) for r in rows]
    assert all((math.isinf(r["abs_curve_err"]) and math.isinf(r["curve_err"])) or r["abs_curve_err"] == abs(r["curve_err"]) for r in rows)
    m, p = q_lin(a, 0.5), q_lin(a, 0.9)
    med.append(m); p90.append(p)
    crit[f"s{s}"] = {"n": len(a), "infinite": sum(math.isinf(x) for x in a), "median": m, "p90": p,
                     "box_median": box["eval"]["abs_curve_err"]["median"], "box_p90": box["eval"]["abs_curve_err"]["p90"],
                     "box_infinite": box["eval"]["curve_infinite"],
                     "notes": sorted({r["curve_note"] for r in rows if r["curve_note"]})}
crit["C1_value"], crit["C2_value"] = q_lin(med, 0.5), q_lin(p90, 0.5)
crit["C1"], crit["C2"] = crit["C1_value"] <= 0.05, crit["C2_value"] <= 0.10
crit["verdict"] = "PASS" if crit["C1"] and crit["C2"] else "FAIL"
crit["box"] = {"C1_value": v["C1_value"], "C2_value": v["C2_value"], "C1": v["C1"], "C2": v["C2"], "verdict": v["verdict"],
               "per_seed": v["per_seed"]}
crit["equal_to_box"] = (crit["C1_value"] == v["C1_value"], crit["C2_value"] == v["C2_value"],
                        [crit[f"s{s}"]["median"] - crit[f"s{s}"]["box_median"] for s in "012"],
                        [crit[f"s{s}"]["p90"] - crit[f"s{s}"]["box_p90"] for s in "012"])
R["criteria"] = crit

# every pair's within_bound, evaluate_failed, infinite notes over all runs (eval and tested)
wb = {}
for run in RUNS:
    arm, s = run.rsplit("_s", 1)
    box = v["arms"][arm][s]
    rows = [r for d_ in (box["eval_rows"], box["tested"]) for rr in d_.values() for r in rr]
    wb[run] = {"pairs": len(rows), "within_bound_false": sum(not r["within_bound"] for r in rows),
               "evaluate_failed": sum(bool(r["evaluate_failed"]) for r in rows),
               "infinite_eval": sum(math.isinf(r["curve_err"]) for rr in box["eval_rows"].values() for r in rr),
               "infinite_tested": sum(math.isinf(r["curve_err"]) for rr in box["tested"].values() for r in rr),
               "nan_curve": sum(math.isnan(r["curve_err"]) for r in rows),
               "errors": box["errors"]}
R["pairs"] = wb
OUT.write_text(json.dumps(R, indent=1, default=str))
print(json.dumps(R, indent=1, default=str))
