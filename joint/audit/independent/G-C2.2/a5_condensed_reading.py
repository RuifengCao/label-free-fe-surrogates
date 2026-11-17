"""Audit of gate G-C2.2, item 2 (the judged reading): are the returned condensed predictions what the
pre-specification defines, and were the limits on the amplitude and on the energy evaluations kept?

  files       every prediction file holds the 132 evaluated members; raw and condensed fields (7, n_z) float32,
              base fields (n_z,) float32, n_z the manifest's number of unknowns; all values finite;
  definition  z_c = keep(z_0 + a (z - z_0)) is computed again here in float32 from the returned base field z_0, raw
              field z and amplitude a, keep setting the contact unknowns (the export's cidx, regenerated with the
              stamped library) to at least zero, and compared bit for bit with the returned condensed field;
              the fixed unknowns of both readings are zero and the contact unknowns are not negative;
  limits      0.5 <= a <= 3 for every field; at most 12 energy evaluations for every member; the counts of
              amplitudes on a bound and of iterations that had not met the tolerance; the relative slope left; the
              recorded training energies of the raw and of the condensed field;
  minimum     for a sample of fields (--sample N a seed, with the worst member at 8 mm always included), the energy
              of z_c(a') in float64 with the reference code of the stamped library, for a' around the returned
              amplitude and on a coarse grid of the interval: is the returned amplitude the minimiser, to the
              stated tolerance?

Usage:  FEJOINT_SOLVER=legacy python -I a5_condensed_reading.py STAMP RECORDS CACHE [--sample 3] [--out OUT.json]
        CACHE is a folder of the auditor's where the regenerated exports are kept (made if absent).
"""
import argparse
import json
import os
import sys

import numpy as np

SETS = ("eval", "former", "tested")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stamp"); ap.add_argument("records"); ap.add_argument("cache")
    ap.add_argument("--sample", type=int, default=3); ap.add_argument("--out")
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(a.stamp, "joint"))
    from c22.config import config
    from c22 import data as d22
    from c2.data import export_member
    from c2.instance import ExportedProblem
    cfg = config()
    rd = cfg["evaluation"]["readings"]["condensed"]
    R = a.records
    man = {r["id"]: r for r in json.load(open(os.path.join(R, "manifest.json")))["instances"]}
    ids = [i for i, r in man.items() if r["split"] in SETS]
    members = {m[0]: m[2] for m in d22.members(cfg)}
    os.makedirs(a.cache, exist_ok=True)

    def export(iid):
        p = os.path.join(a.cache, iid + ".npz")
        if not os.path.exists(p):
            ex = export_member(cfg, members[iid])
            np.savez(p, **{k: np.asarray(v) for k, v in ex.items()})
        with np.load(p) as z:
            return {k: z[k] for k in z.files}

    masks = {}
    for iid in ids:
        ex = export(iid)
        n_z = int(ex["v"].size)
        nonneg = np.zeros(n_z, bool); nonneg[np.asarray(ex["cidx"], int)] = True
        masks[iid] = (nonneg, np.asarray(ex["fixed"], bool), n_z)
    res = {"members": len(ids), "seeds": {}}
    rng = np.random.default_rng(20261115)
    sample_rows = []
    for seed in (5, 6, 7):
        run = os.path.join(R, "run_files", f"label_free_s{seed}")
        raw, cond, base = (np.load(os.path.join(run, f)) for f in ("preds.npz", "preds_condensed.npz", "preds_base.npz"))
        cj = json.load(open(os.path.join(run, "condense.json")))
        info = cj["members"]
        s = {"files_hold_the_members": [sorted(z.files) == sorted(ids) for z in (raw, cond, base)],
             "condense_json_members": sorted(info) == sorted(ids), "reading_equals_configuration": cj["reading"] == rd,
             "levels": cj["levels_mm"] == cfg["data"]["eval_levels_mm"]}
        bad_shape, not_finite, differing_arrays, differing_values, fixed_nonzero, contact_negative = [], 0, 0, 0, 0, 0
        max_abs = 0.0
        clamped = 0
        per_set = {k: {"a": [], "at_bound": 0, "not_converged": 0, "rel_slope": [], "rise": [], "evals": []} for k in SETS}
        for iid in ids:
            nonneg, fixed, n_z = masks[iid]
            z, zc, z0 = raw[iid], cond[iid], base[iid]
            if z.shape != (7, n_z) or zc.shape != (7, n_z) or z0.shape != (n_z,) or not (z.dtype == zc.dtype == z0.dtype == np.float32):
                bad_shape.append(iid)
            not_finite += int((~np.isfinite(z)).sum() + (~np.isfinite(zc)).sum() + (~np.isfinite(z0)).sum())
            m = info[iid]
            av = np.asarray(m["a"], dtype=np.float64)
            a32 = av.astype(np.float32)
            assert (a32.astype(np.float64) == av).all(), "an amplitude is not a float32 value"
            mine = z0[None, :] + a32[:, None] * (z - z0[None, :])            # float32 throughout
            assert mine.dtype == np.float32
            clamped += int((nonneg[None, :] & (mine < 0)).sum())
            mine = np.where(nonneg[None, :], np.maximum(mine, np.float32(0.0)), mine)
            d = mine != zc
            differing_values += int(d.sum()); differing_arrays += int(d.any())
            max_abs = max(max_abs, float(np.abs(zc).max()))
            fixed_nonzero += int((z[:, fixed] != 0).sum() + (zc[:, fixed] != 0).sum())
            contact_negative += int((z[:, nonneg] < 0).sum() + (zc[:, nonneg] < 0).sum())
            ps = per_set[man[iid]["split"]]
            ps["a"] += m["a"]; ps["at_bound"] += sum(m["at_bound"]); ps["not_converged"] += sum(not c for c in m["converged"])
            ps["rel_slope"] += m["rel_slope"]; ps["evals"].append(m["evaluations"])
            ps["rise"] += [(c - r) / r for c, r in zip(m["Pi_condensed"], m["Pi_raw"])]
            for l in range(7):
                if m["converged"][l] and not m["at_bound"][l] and m["rel_slope"][l] > rd["rtol"]:
                    s.setdefault("converged_with_slope_above_rtol", []).append([iid, l, m["rel_slope"][l]])
        s.update(bad_shape=bad_shape, values_not_finite=not_finite, arrays_differing_from_recomputed=differing_arrays,
                 values_differing_from_recomputed=differing_values, largest_unknown=max_abs, contact_values_clamped=clamped,
                 fixed_unknowns_not_zero=fixed_nonzero, contact_unknowns_negative=contact_negative)
        for k, ps in per_set.items():
            av = np.array(ps["a"]); rise = np.array(ps["rise"])
            s[k] = {"fields": int(av.size), "a_min": float(av.min()), "a_median": float(np.median(av)), "a_max": float(av.max()),
                    "inside_bounds": bool((av >= rd["a_min"]).all() and (av <= rd["a_max"]).all()),
                    "at_bound": int(ps["at_bound"]), "not_converged": int(ps["not_converged"]),
                    "max_rel_slope": float(max(ps["rel_slope"])), "max_evaluations": int(max(ps["evals"])),
                    "fields_with_energy_raised": int((rise > 0).sum()), "largest_rise": float(max(rise.max(), 0.0)),
                    "median_fall": float(np.median(-rise)), "a_equal_1": int((av == 1.0).sum())}
        res["seeds"][seed] = s
        # the sample for the check of the minimum, in float64 with the reference energy
        pick = [("eval_0001", 6)]
        ev = [i for i in ids if man[i]["split"] == "eval"]
        nc = [(i, l) for i in ev for l in range(7) if not info[i]["converged"][l]]
        if nc:
            pick.append(nc[int(rng.integers(len(nc)))])
        while len(pick) < a.sample:
            pick.append((ev[int(rng.integers(len(ev)))], int(rng.integers(7))))
        for iid, l in pick:
            ex = export(iid)
            P = ExportedProblem(ex)
            nonneg = masks[iid][0]
            z, z0 = raw[iid][l].astype(np.float64), base[iid].astype(np.float64)
            D = float(cfg["data"]["eval_levels_mm"][l])
            a0 = float(info[iid]["a"][l])

            def Pi(x):
                zc = z0 + x * (z - z0)
                zc = np.where(nonneg, np.maximum(zc, 0.0), zc)
                return P.evaluate(zc, D)["Pi"]

            h = 1e-3
            p0, pm, pp = Pi(a0), Pi(a0 - h), Pi(a0 + h)
            grid = [0.5, 0.75, 0.9, 1.0, 1.1, 1.25, 1.5, 2.0, 3.0]
            pg = [Pi(x) for x in grid]
            curv = (pp - 2 * p0 + pm) / h ** 2
            slope = (pp - pm) / (2 * h)
            sample_rows.append({"seed": seed, "id": iid, "level": l, "a": a0, "converged": info[iid]["converged"][l],
                                "recorded_rel_slope": info[iid]["rel_slope"][l], "Pi_float64_at_a": p0,
                                "recorded_Pi_condensed_float32": info[iid]["Pi_condensed"][l], "rel_difference_of_the_two_energies": p0 / info[iid]["Pi_condensed"][l] - 1,
                                "rel_slope_float64": abs(slope) / p0, "distance_to_minimiser_estimate": -slope / curv if curv > 0 else None,
                                "lowest_grid_energy_relative_to_a": min(pg) / p0 - 1, "grid_minimiser": grid[int(np.argmin(pg))],
                                "Pi_at_1_relative_to_a": Pi(1.0) / p0 - 1})
    res["minimum_sample"] = sample_rows
    out = json.dumps(res, indent=1)
    if a.out:
        open(a.out, "w").write(out)
    print(out)


if __name__ == "__main__":
    main()
