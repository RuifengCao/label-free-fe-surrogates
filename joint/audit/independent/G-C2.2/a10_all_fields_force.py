"""Audit of gate G-C2.2, item 1 (all fields, no solve): the returned rows of verdict.json tied to the returned
prediction and label files.

For every returned field (three seeds, two readings, 132 members, seven levels: 5,544 fields) the end displacement e
is read from the prediction file (the last unknown) and the spring force F = 4 k_s (D - e) is formed here, with the
family's spring of 20 kN/mm per quarter model. Against the label of the same member and level this gives
    F_err = F / F_ref - 1   and   e_err = e / e_ref - 1,
which are compared with the same two entries of the member's rows in verdict.json. This uses numpy only: no code of
the gate and none of the author's. It shows that the rows of verdict.json belong to the returned predictions and
labels, for every field; it does not recompute the judged error, which needs an exact solve (a3_recompute_pairs.py).

Usage:  python -I a10_all_fields_force.py RECORDS [--out OUT.json]
"""
import argparse
import json
import os

import numpy as np

K_S = 2.0e4          # N/mm per quarter model (pre-specification of G-C2.1, unchanged in G-C2.2)
FILES = {"condensed": "preds_condensed.npz", "raw": "preds.npz"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records"); ap.add_argument("--out")
    a = ap.parse_args()
    R = a.records
    v = json.load(open(os.path.join(R, "verdict.json")))
    man = {r["id"]: r for r in json.load(open(os.path.join(R, "manifest.json")))["instances"]}
    ids = [i for i, r in man.items() if r["split"] in ("eval", "former", "tested")]
    labels = {}
    for iid in ids:
        with np.load(os.path.join(R, "labels", iid + ".npz")) as z:
            labels[iid] = {k: z[k] for k in ("D", "e", "F")}
            assert labels[iid]["D"].tolist() == [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
            # the label's own force is the spring reading of its end displacement
            assert np.allclose(labels[iid]["F"], 4 * K_S * (labels[iid]["D"] - labels[iid]["e"]), rtol=1e-12, atol=0)
    res = {"fields": 0, "max_abs_diff_F_err": 0.0, "max_abs_diff_e_err": 0.0, "by_reading_seed": {}}
    for seed in ("5", "6", "7"):
        for reading, name in FILES.items():
            z = np.load(os.path.join(R, "run_files", f"label_free_s{seed}", name))
            dF = dE = 0.0
            n = 0
            for iid in ids:
                Z = z[iid].astype(np.float64)
                rows = v["readings"][reading][seed][f"{man[iid]['split']}_rows"][iid]
                lab = labels[iid]
                for l in range(7):
                    e = float(Z[l, -1])
                    F = 4.0 * K_S * (float(lab["D"][l]) - e)
                    dF = max(dF, abs((F / float(lab["F"][l]) - 1) - rows[l]["F_err"]))
                    dE = max(dE, abs((e / float(lab["e"][l]) - 1) - rows[l]["e_err"]))
                    n += 1
            res["by_reading_seed"][f"{reading}|{seed}"] = {"fields": n, "max_abs_diff_F_err": dF, "max_abs_diff_e_err": dE}
            res["fields"] += n
            res["max_abs_diff_F_err"] = max(res["max_abs_diff_F_err"], dF)
            res["max_abs_diff_e_err"] = max(res["max_abs_diff_e_err"], dE)
    if a.out:
        open(a.out, "w").write(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
