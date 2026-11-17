"""Audit of gate G-C2.2, item 1b, step 2: the judged error of chosen pairs, recomputed from the returned predictions
and labels with the stamped library and the auditor's own driver.

For each pair (seed, reading, member, level) of the list written by a2_select_pairs.py:
  - the member is drawn again with the stamped code (c22.data.members) and exported again (c2.data.export_member);
    its family parameters and sizes are compared with the returned manifest, and the returned label fields of the
    lowest and highest level are evaluated on the regenerated problem and compared with the label's own energy,
    force and end displacement (this ties the regenerated instance to the one the laptop solved);
  - the predicted field is read from the run's preds_condensed.npz (condensed) or preds.npz (raw); its end
    displacement e and its spring force F = 4 k_s (D - e) are read here, not by the gate's metric function;
  - the reference force F*(e) is an exact solve with e prescribed (c2.instance.ExportedProblem.solve_at_e of the
    stamped library), started from the returned label nearest in e; the judged error is F / F*(e) - 1;
  - the result is compared with curve_err of the same pair in the returned verdict.json.
The stamped library is used for the model, the export and the solve; nothing of the author's audit scripts and
nothing of c2.evaluate or c22.evaluate is imported. Set FEJOINT_SOLVER=legacy so that the solves use SuperLU.

Results are appended to OUT as JSON lines, one a pair, as they finish; pairs already in OUT are skipped.

Usage:  FEJOINT_SOLVER=legacy python -I a3_recompute_pairs.py STAMP RECORDS PAIRS.json OUT.jsonl [--workers 2]
        STAMP is the export of the stamped commit (it holds joint/c22, joint/c2, joint/fejoint);
        RECORDS is the folder gate_records of the return package.
"""
import argparse
import json
import os
import sys
import time

import numpy as np

FILES = {"condensed": "preds_condensed.npz", "raw": "preds.npz"}
_state = {}


def _init(stamp, records):
    sys.path.insert(0, os.path.join(stamp, "joint"))
    from c22.config import config, sha256
    from c22 import data as d22
    cfg = config()
    _state.update(cfg=cfg, sha=sha256(cfg), records=records, members={m[0]: m for m in d22.members(cfg)},
                  manifest={r["id"]: r for r in json.load(open(os.path.join(records, "manifest.json")))["instances"]},
                  problems={}, preds={})


def _problem(iid):
    from dataclasses import asdict
    from c2.data import export_member
    from c2.instance import ExportedProblem
    if iid not in _state["problems"]:
        _, split, q = _state["members"][iid]
        rec = _state["manifest"][iid]
        ex = export_member(_state["cfg"], q)
        P = ExportedProblem(ex)
        with np.load(os.path.join(_state["records"], "labels", iid + ".npz")) as z:
            lab = {k: z[k] for k in z.files}
        check = {"params_equal_manifest": asdict(q) == rec["params"], "split_equal": split == rec["split"],
                 "nodes_equal": int(ex["nodes"].shape[0]) == rec["nodes"], "unknowns_equal": int(ex["v"].size) == rec["unknowns"]}
        dPi = dF = de = 0.0
        for l in (0, lab["D"].size - 1):
            r = P.evaluate(lab["z"][l], float(lab["D"][l]))
            dPi = max(dPi, abs(r["Pi"] / float(lab["Pi"][l]) - 1))
            dF = max(dF, abs(r["F"] / float(lab["F"][l]) - 1))
            de = max(de, abs(r["e"] - float(lab["e"][l])))
        check.update(label_Pi_rel=dPi, label_F_rel=dF, label_e_abs=de)
        if len(_state["problems"]) > 6:                      # keep the memory small
            _state["problems"].pop(next(iter(_state["problems"])))
        _state["problems"][iid] = (ex, P, lab, check)
    return _state["problems"][iid]


def _field(seed, reading, iid, l):
    key = (seed, reading)
    if key not in _state["preds"]:
        _state["preds"][key] = np.load(os.path.join(_state["records"], "run_files", f"label_free_s{seed}", FILES[reading]))
    return _state["preds"][key][iid][l]


def one(job):
    seed, reading, s, iid, l = job["seed"], job["reading"], job["set"], job["id"], job["level"]
    t0 = time.perf_counter()
    ex, P, lab, check = _problem(iid)
    z32 = _field(seed, reading, iid, l)
    z = np.asarray(z32, dtype=np.float64)
    D = float(lab["D"][l])
    fixed = np.asarray(ex["fixed"], bool)
    cidx = np.asarray(ex["cidx"], int)
    e_idx = int(ex["e_idx"])
    k_s = float(ex["k_s"])
    out = dict(job, D=D, dtype=str(z32.dtype), fixed_zero=bool(np.all(z[fixed] == 0)), contact_nonneg=bool((z[cidx] >= 0).all()),
               instance=check, k_s=k_s)
    e = float(z[e_idx])
    F = 4.0 * k_s * (D - e)
    near = int(np.argmin(np.abs(np.asarray(lab["e"]) - e)))
    c = P.solve_at_e(e, z0=lab["z"][near])
    out.update(e=e, F=F, F_star=c["F"], converged=bool(c["converged"]),
               curve_err=(F / c["F"] - 1) if (c["converged"] and c["F"] > 0) else float("inf"),
               F_err_same_D=F / float(lab["F"][l]) - 1, e_err=e / float(lab["e"][l]) - 1,
               seconds=round(time.perf_counter() - t0, 1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stamp"); ap.add_argument("records"); ap.add_argument("pairs"); ap.add_argument("out")
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    jobs = json.load(open(a.pairs))
    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            r = json.loads(line)
            done.add((r["seed"], r["reading"], r["id"], r["level"]))
    jobs = [j for j in jobs if (j["seed"], j["reading"], j["id"], j["level"]) not in done]
    v = json.load(open(os.path.join(a.records, "verdict.json")))
    import multiprocessing as mp
    with mp.get_context("fork").Pool(a.workers, initializer=_init, initargs=(a.stamp, a.records)) as pool, open(a.out, "a") as fh:
        for r in pool.imap(one, jobs, chunksize=1):
            row = v["readings"][r["reading"]][r["seed"]][f"{r['set']}_rows"][r["id"]][r["level"]]
            r["returned_curve_err"] = row["curve_err"]
            r["difference"] = r["curve_err"] - row["curve_err"]
            r["returned_F_err"] = row["F_err"]
            r["returned_e_err"] = row["e_err"]
            fh.write(json.dumps(r) + "\n"); fh.flush()
            print(r["seed"], r["reading"], r["id"], r["level"], r["why"], f"{r['curve_err']:+.6f}", f"{r['difference']:.1e}", r["seconds"], "s", flush=True)


if __name__ == "__main__":
    main()
