"""Second reading: spot checks of the new tables of docs/G-C2.1_verdict_numbers.md with the auditor's own code
(tested members overall, infinite pairs with predicted e and preload ratio, the tail table), and the ledger's
residuals of the 68 held-out and tested members. Usage: python -I -B round2_checks.py RECORDS OUT_JSON"""
import json
import math
import sys
from pathlib import Path

import numpy as np

REC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
v = json.loads((REC / "verdict.json").read_text())
man = json.loads((REC / "manifest.json").read_text())
prm = {r["id"]: r["params"] for r in man["instances"]}
ev = sorted(r["id"] for r in man["instances"] if r["split"] == "eval")
fy = np.array([prm[i]["fy"] for i in ev])
RUNS = [("label_free", s) for s in "012"] + [("supervised_64", s) for s in "012"]
TESTED = ("tested_BJ_T1_preloaded", "tested_BJ_T1_snug", "tested_BJ_T2_preloaded", "tested_BJ_T2_snug")


def q(x, p):
    s = sorted(float(t) for t in x)
    h = (len(s) - 1) * p
    lo = math.floor(h)
    t = h - lo
    a, b = s[lo], s[min(lo + 1, len(s) - 1)]
    if t == 0:
        return a
    if math.isinf(b):
        return math.inf
    return a + t * (b - a)


R = {"tested_overall": {}, "infinite": {}, "tail": {}}
for arm, s in RUNS:
    run = f"{arm}_s{s}"
    box = v["arms"][arm][s]
    allrows = []
    for t in TESTED:
        rows = box["tested"][t]
        allrows += rows
        R["tested_overall"][f"{run}:{t[7:]}"] = {
            "dist": q([abs(r["curve_err"]) for r in rows], .5), "signed": q([r["curve_err"] for r in rows], .5),
            "F_err": q([r["F_err"] for r in rows], .5), "gap": q([r["gap"] for r in rows], .5),
            "e_err": q([r["e_err"] for r in rows], .5), "inf": sum(math.isinf(r["curve_err"]) for r in rows)}
    R["tested_overall"][f"{run}:all four"] = {
        "dist": q([abs(r["curve_err"]) for r in allrows], .5), "signed": q([r["curve_err"] for r in allrows], .5),
        "F_err": q([r["F_err"] for r in allrows], .5), "bound": q([r["bound"] for r in allrows], .5),
        "e_err": q([r["e_err"] for r in allrows], .5), "F_sigma_err": q([r["F_sigma_err"] for r in allrows], .5),
        "gap": q([r["gap"] for r in allrows], .5), "iou_contact": q([r["iou_contact"] for r in allrows], .5),
        "iou_plastic": q([r["iou_plastic"] for r in allrows], .5), "bolt_err": q([r["bolt_err"] for r in allrows], .5),
        "u_rel_l2": q([r["u_rel_l2"] for r in allrows], .5), "within": sum(r["within_bound"] for r in allrows),
        "inf": sum(math.isinf(r["curve_err"]) for r in allrows)}
    # infinite pairs: predicted e from preds.npz, preload ratio from the manifest
    with np.load(REC / "runs" / run / "preds.npz") as z:
        P = {k: z[k] for k in z.files}
    for split, d in (("held-out", box["eval_rows"]), ("tested", box["tested"])):
        got = [(iid, l, float(P[iid][l, -1]), prm[iid]["rho"], r["curve_note"]) for iid, rows in d.items()
               for l, r in enumerate(rows) if math.isinf(r["curve_err"])]
        if got:
            R["infinite"][f"{run}:{split}"] = {"n": len(got), "e_min": min(g[2] for g in got),
                                               "e_max": max(g[2] for g in got), "rho_min": min(g[3] for g in got),
                                               "rho_max": max(g[3] for g in got), "notes": sorted({g[4] for g in got})}
    A = np.array([[abs(r["curve_err"]) for r in box["eval_rows"][i]] for i in ev])
    p90 = q(A.ravel(), .9)
    tail = [(i, l) for i in range(64) for l in range(7) if A[i, l] > p90]
    R["tail"][run] = {"p90": p90, "n": len(tail), "at_6_8": sum(l >= 5 for _, l in tail),
                      "at_05_1": sum(l <= 1 for _, l in tail), "low_fy": sum(fy[i] < 300 for i, _ in tail),
                      "above10_8mm": int((A[:, 6] > .1).sum()),
                      "above10_8mm_fy_ge300": int(((A[:, 6] > .1) & (fy >= 300)).sum())}
led = {e["id"]: e for e in json.loads((REC / "ledger.json").read_text())}
R["ledger_res_unconstrained_68"] = max(led[i]["kkt_worst"]["max_residual_unconstrained"]
                                       for i in ev + list(TESTED))
R["ledger_min_lambda_68"] = min(led[i]["kkt_worst"]["min_lambda"] for i in ev + list(TESTED))
conv = lambda o: o.item() if hasattr(o, "item") else str(o)  # noqa: E731
OUT.write_text(json.dumps(R, indent=1, default=conv))
print(json.dumps(R, indent=1, default=conv))
