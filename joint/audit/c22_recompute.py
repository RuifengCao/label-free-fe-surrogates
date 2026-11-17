"""Audit of gate G-C2.2 from its return package (not under the stamp).

Steps 1 to 6 were written while the gate's evaluation ran, before its result was known, and tried on the files of
the host check. Step 7, the packing of the solves into one file and the option --reverse were added after the run.
No record dates the script: this is the author's statement.

    python -I audit/c22_recompute.py RECORDS INSTANCES OUT --regenerate [--creator 0]
    python -I audit/c22_recompute.py RECORDS INSTANCES OUT --fields [--ids x,y] [--workers N]
    python -I audit/c22_recompute.py RECORDS INSTANCES OUT --select RULE
    python -I audit/c22_recompute.py RECORDS INSTANCES OUT --curves NAME [--workers N] [--budget SECONDS] [--reverse]
    python -I audit/c22_recompute.py RECORDS INSTANCES OUT --resolve x,y
    python -I audit/c22_recompute.py RECORDS INSTANCES OUT --aggregate
    python -I audit/c22_recompute.py RECORDS INSTANCES OUT --records

Run it from the joint/ folder, with c2/, c22/ and fejoint/ as stamped (docs/G-C2.1_code.sha256 and
docs/G-C2.2_code.sha256). RECORDS is the return package's gate_records/ folder or the kept copy whole, INSTANCES a
folder for the regenerated instances, OUT the folder of the outputs (records/c22/audit). The repository holds the
kept copy in records/c22/return without its label and prediction files (c22_deposit.py restore writes them
there): without them --fields, --curves, --resolve and --records stop at a missing file. The steps:
  1. --regenerate: regenerates all 644 instances into INSTANCES with the stamped code, checks that the members are
     the configured draws and that no two of the four sets share a member, and compares the files with the returned
     manifest (regenerate.json). The bytes of a file depend on two things outside the stamped code: the zlib that
     numpy's savez_compressed writes through, and the system that writes the archive, which zipfile records in
     every entry (0 under Windows, 3 under Linux). The host was a Windows laptop whose Python writes through
     zlib 1.3: run this step with zlib 1.3 (on Linux, LD_PRELOAD of the system's libz.so.1.3 provides it) and
     with --creator 0. regenerate.json records the zlib and the creator used and, apart from the bytes, compares
     the arrays' sizes.
  2. --fields: for every held-out and tested member, one JSON file in OUT/fields (resumes):
     - the returned label on the regenerated instance: its field, evaluated there, against the label's energy, force
       and end displacement, and its optimality residuals;
     - for every seed, the returned condensed field against keep(z_0 + a (z - z_0)), computed in float32 from the
       returned base field, raw field and amplitude;
     - for every seed and both readings, every metric of every level that needs no solve (c2.evaluate.metrics with
       curve=False): the errors of force and end displacement at the same D, the stress reading, the energy gap,
       the bound, the two intersections over union, the bolt force and the displacement error.
  3. --select RULE: writes OUT/pairs_NAME.json, a list of pairs (member, seed, reading, level) whose judged error is
     to be recomputed with an exact solve. RULE is one of
       judged          every pair of the judged reading on the judged set (1,344 pairs)
       all             every pair of both readings on the three sets (5,544 pairs)
       tail:T:N:SEED   of the judged reading on the judged set: every pair whose returned error is at least T in
                       absolute value, and N more drawn without replacement with numpy's default_rng(SEED)
     NAME is the rule with ':' replaced by '_'.
  4. --curves NAME: for the pairs of OUT/pairs_NAME.json, the stamped metric function with its exact solve at the
     predicted end displacement, one JSON file a pair in OUT/curves (resumes; stops starting members after
     --budget seconds; --reverse takes the members in reverse order, for a second process on the same list).
     Step 6 packs these files into OUT/curves.json, which is what the records keep.
  5. --resolve: re-solves the listed members at their levels from the regenerated instances, as the labels were
     solved, and compares with the returned labels and the ledger (resolve.json).
  6. --aggregate: (a) recomputes, with its own quantile, every seed's median and 90th percentile of the judged error
     from the per-pair rows of the returned verdict.json, for both readings and the three sets, then C1, C2 and the
     verdict, and compares them with the returned ones; (b) compares every recomputed metric of steps 2 and 4 with
     the returned rows; (c) recomputes the amplitude counts from the returned condense.json files; (d) reads each
     run's history and attempts (aggregate.json).
  7. --records: reads the returned records without computing a field (records.json): the returned configuration
     against the stamped one; the ledger (every labelled member once, at the configured levels, converged, its
     residuals within the configured limits, the label files and the instances it names by their SHA-256); the
     prediction files (the members they hold, their shapes and types); each run's log against its history; and
     how every command of the queue ended.
Steps 2 to 5 use one BLAS thread a process, as the host's labels and evaluation did. The host had no pypardiso: set
FEJOINT_SOLVER=legacy where it loads, so that the solves use scipy's SuperLU.

--reduced runs the script on the output of the host check (c22/smoke.py), whose configuration is the reduced one:
a check of this script, not of the gate.
"""
import os
import sys

if "--regenerate" not in sys.argv:                 # steps 2 to 6: one BLAS thread a process
    for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[_k] = "1"

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import pathlib  # noqa: E402
import platform  # noqa: E402
import time  # noqa: E402
import zlib  # noqa: E402
from dataclasses import asdict  # noqa: E402

ROOT = pathlib.Path.cwd()
sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402
import scipy  # noqa: E402

from c22.config import config, sha256  # noqa: E402
from c22 import data as C22D  # noqa: E402
from c2.data import load_export, solve_levels, export_member, _pack  # noqa: E402
from c2.evaluate import metrics  # noqa: E402
from c2.instance import ExportedProblem  # noqa: E402
from fejoint import linsolve  # noqa: E402

STAMPED_CONFIG = "ef5376a4d6c3cc98d7888121439c8d959ee817d332958dd6b1141b25e78734bb"
FILES = {"condensed": "preds_condensed.npz", "raw": "preds.npz"}
THRESHOLDS = {"C1": 0.05, "C2": 0.10}
CHEAP = ("F_err", "e_err", "F_sigma_err", "gap", "bound", "iou_contact", "iou_plastic", "bolt_err", "u_rel_l2")
KEYS = ("curve_err",) + CHEAP


def environment() -> dict:
    return {"python": platform.python_version(), "platform": platform.platform(), "numpy": np.__version__,
            "scipy": scipy.__version__, "zlib": zlib.ZLIB_RUNTIME_VERSION,
            "solver": "pardiso" if linsolve._PARDISO is not None else "scipy",
            "blas_threads_env": os.environ.get("OPENBLAS_NUM_THREADS"), "cpus": os.cpu_count()}


def write_json(p: pathlib.Path, obj, indent=None) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=indent))
    tmp.replace(p)


def label_of(rec: pathlib.Path, iid: str) -> dict:
    with np.load(rec / "labels" / f"{iid}.npz") as z:
        return {k: z[k] for k in z.files}


def run_dir(rec: pathlib.Path, seed) -> pathlib.Path:
    return rec / "run_files" / f"label_free_s{seed}"


def field_of(rec: pathlib.Path, seed, reading: str, iid: str) -> np.ndarray:
    with np.load(run_dir(rec, seed) / FILES[reading]) as z:
        return z[iid]


def sets_of(rec: pathlib.Path, cfg: dict) -> dict:
    man = json.loads((rec / "manifest.json").read_text())
    return {r["id"]: r["split"] for r in man["instances"] if r["split"] in cfg["evaluation"]["sets"]}


def problem(inst: pathlib.Path, rec: pathlib.Path, iid: str):
    ex, _ = load_export(inst / f"{iid}.npz")
    ref = label_of(rec, iid)
    P = ExportedProblem(ex)
    ref_pl = [P.evaluate(ref["z"][l], float(ref["D"][l]))["plastic"] for l in range(ref["D"].size)]
    return ex, ref, P, ref_pl


def fields_member(job):
    """Step 2 for one member."""
    rec, inst, outdir, iid, seeds = job
    rec, inst, outdir = pathlib.Path(rec), pathlib.Path(inst), pathlib.Path(outdir)
    out_p = outdir / "fields" / f"{iid}.json"
    if out_p.exists():
        return iid, "kept"
    t0 = time.perf_counter()
    ex, ref, P, ref_pl = problem(inst, rec, iid)
    L = ref["D"].size
    lab = []
    for l in range(L):
        D = float(ref["D"][l])
        e = P.evaluate(ref["z"][l], D)
        _, g, _, _ = P.prob.evaluate(np.asarray(ref["z"][l], float), "hencky", tangent=False)
        kkt = P.prob.kkt(np.asarray(ref["z"][l], float), g)
        lab.append({"D": D, "Pi_rel": e["Pi"] / float(ref["Pi"][l]) - 1, "F_rel": e["F"] / float(ref["F"][l]) - 1,
                    "e_diff": e["e"] - float(ref["e"][l]), "res_unconstrained": float(kkt["max_residual_unconstrained"]),
                    "min_gap": float(kkt["min_gap"]), "min_lambda": float(kkt["min_lambda"])})
    nonneg = np.zeros(ref["z"].shape[1], dtype=bool)
    nonneg[np.asarray(P.prob.cidx)] = True
    runs, parts = {}, {}
    for seed in seeds:
        rd = run_dir(rec, seed)
        raw, cond = field_of(rec, seed, "raw", iid), field_of(rec, seed, "condensed", iid)
        with np.load(rd / "preds_base.npz") as z:
            base = z[iid]
        info = json.loads((rd / "condense.json").read_text())["members"][iid]
        a = np.asarray(info["a"], dtype=np.float32)
        ok = raw.dtype == np.float32 and cond.dtype == np.float32 and base.dtype == np.float32 \
            and raw.shape == cond.shape == (L, base.size) and a.shape == (L,)
        zc = base[None, :] + a[:, None] * (raw - base[None, :])
        zc = np.where(nonneg[None, :], np.maximum(zc, np.float32(0)), zc)
        d = np.abs(zc.astype(np.float64) - cond.astype(np.float64))
        parts[str(seed)] = {"shapes_and_types_ok": bool(ok), "finite": bool(np.isfinite(raw).all() and np.isfinite(cond).all()
                                                                            and np.isfinite(base).all()),
                            "max_abs_diff": float(d.max()), "unknowns_differing": int((d > 0).sum()),
                            "max_abs_field": float(np.abs(cond).max()), "amplitude_as_float32_equal": bool(
                                np.array_equal(a.astype(np.float64), np.asarray(info["a"], dtype=np.float64)))}
        for reading, Z in (("condensed", cond), ("raw", raw)):
            runs[f"{seed}|{reading}"] = [metrics(P, ex, Z[l], ref, ref_pl[l], l, curve=False) for l in range(L)]
    write_json(out_p, {"id": iid, "label_check": lab, "condensed_from_parts": parts, "runs": runs,
                       "seconds": time.perf_counter() - t0})
    return iid, round(time.perf_counter() - t0, 1)


def curve_file(outdir: pathlib.Path, iid: str, seed, reading: str, l: int) -> pathlib.Path:
    return outdir / "curves" / f"{iid}__s{seed}_{reading}_l{l}.json"


def curves_member(job):
    """Step 4 for the listed pairs of one member."""
    rec, inst, outdir, iid, pairs = job
    rec, inst, outdir = pathlib.Path(rec), pathlib.Path(inst), pathlib.Path(outdir)
    todo = [(s, r, l) for s, r, l in pairs if not curve_file(outdir, iid, s, r, l).exists()]
    if not todo:
        return iid, 0, 0.0
    t0 = time.perf_counter()
    ex, ref, P, ref_pl = problem(inst, rec, iid)
    cache = {}
    for seed, reading, l in todo:
        if (seed, reading) not in cache:
            cache[(seed, reading)] = field_of(rec, seed, reading, iid)
        t1 = time.perf_counter()
        row = metrics(P, ex, cache[(seed, reading)][l], ref, ref_pl[l], l)
        row.update(id=iid, seed=seed, reading=reading, level=l, seconds=time.perf_counter() - t1)
        write_json(curve_file(outdir, iid, seed, reading, l), row)
    return iid, len(todo), round(time.perf_counter() - t0, 1)


def select(rec: pathlib.Path, outdir: pathlib.Path, cfg: dict, rule: str) -> dict:
    ev = cfg["evaluation"]
    judged, jset = ev["readings"]["judged"], ev["judged_set"]
    seeds = cfg["arms"]["label_free"]["seeds"]
    split = sets_of(rec, cfg)
    L = len(cfg["data"]["eval_levels_mm"])
    name = rule.replace(":", "_")
    if rule == "judged":
        pairs = [[i, s, judged, l] for i in sorted(split) if split[i] == jset for s in seeds for l in range(L)]
        note = "every pair of the judged reading on the judged set"
    elif rule == "all":
        pairs = [[i, s, r, l] for i in sorted(split) for s in seeds for r in FILES for l in range(L)]
        note = "every pair of both readings on the three sets"
    elif rule.startswith("tail:"):
        _, thr, n, rs = rule.split(":")
        thr, n, rs = float(thr), int(n), int(rs)
        v = json.loads((rec / "verdict.json").read_text())
        every = [[i, s, judged, l] for i in sorted(split) if split[i] == jset for s in seeds for l in range(L)]
        err = [abs(v["readings"][judged][str(s)][f"{jset}_rows"][i][l]["curve_err"]) for i, s, _, l in every]
        tail = [p for p, e in zip(every, err) if not e < thr]            # not-a-number and infinite count as large
        rest = [p for p, e in zip(every, err) if e < thr]
        pick = np.random.default_rng(rs).choice(len(rest), size=min(n, len(rest)), replace=False)
        pairs = tail + [rest[k] for k in sorted(int(k) for k in pick)]
        note = (f"of the judged reading on the judged set: the {len(tail)} pairs whose returned error is at least {thr} "
                f"in absolute value and {len(pairs) - len(tail)} of the other {len(rest)}, drawn without replacement "
                f"with numpy.random.default_rng({rs})")
    else:
        raise SystemExit(f"unknown rule {rule}")
    out = {"rule": rule, "note": note, "n": len(pairs), "pairs": pairs}
    write_json(outdir / f"pairs_{name}.json", out)
    return {k: out[k] for k in ("rule", "note", "n")}


def resolve(rec: pathlib.Path, inst: pathlib.Path, iid: str, cfg: dict) -> dict:
    ex, _ = load_export(inst / f"{iid}.npz")
    ref = label_of(rec, iid)
    led = {e["id"]: e for e in json.loads((rec / "ledger.json").read_text())}[iid]
    ls = cfg["data"]["label_solver"]
    t0 = time.perf_counter()
    s = solve_levels(ex, [float(v) for v in ref["D"]], ls["tol"], ls["max_it"])
    return {"id": iid, "seconds": round(time.perf_counter() - t0, 1),
            "bit_identical": bool(np.array_equal(s["z"], ref["z"])),
            "max_z_diff_over_max_z": float(np.abs(s["z"] - ref["z"]).max() / np.abs(ref["z"]).max()),
            "max_Pi_rel": float(np.max(np.abs(s["Pi"] / ref["Pi"] - 1))),
            "max_F_rel": float(np.max(np.abs(s["F"] / ref["F"] - 1))),
            "max_e_diff_mm": float(np.abs(s["e"] - ref["e"]).max()),
            "iterations": [int(i) for i in s["iterations"]], "ledger_iterations": led["iterations"],
            "converged": [bool(c) for c in s["converged"]]}


def regenerate(rec: pathlib.Path, inst: pathlib.Path, cfg: dict, creator=None) -> dict:
    """Every instance, written as c22.data.generate writes it, against the returned manifest. creator: the system
    that zipfile records as the archive's creator (None: this system's)."""
    if creator is not None:
        import zipfile
        init = zipfile.ZipInfo.__init__

        def as_host(self, *args, **kwargs):
            init(self, *args, **kwargs)
            self.create_system = creator

        zipfile.ZipInfo.__init__ = as_host
    man = json.loads((rec / "manifest.json").read_text())
    box = {r["id"]: r for r in man["instances"]}
    mem = C22D.members(cfg)
    same = len(mem) == man["n"] and all(i in box and box[i]["params"] == asdict(prm) and box[i]["split"] == s
                                        for i, s, prm in mem)
    key = {s: {json.dumps(asdict(prm), sort_keys=True) for i, t, prm in mem if t == s}
           for s in ("train", "eval", "former", "tested")}
    names = sorted(key)
    shared = {f"{a}&{b}": len(key[a] & key[b]) for k, a in enumerate(names) for b in names[k + 1:]}
    cfg_sha = sha256(cfg)
    inst.mkdir(parents=True, exist_ok=True)
    by_split, differ, sizes_differ = {}, [], []
    for iid, split, prm in mem:
        p = inst / f"{iid}.npz"
        with open(p, "wb") as fh:
            np.savez_compressed(fh, **_pack(export_member(cfg, prm), prm, cfg_sha))
        with np.load(p) as z:
            nodes, nz = int(z["nodes"].shape[0]), int(z["v"].size)
        sha_ok = hashlib.sha256(p.read_bytes()).hexdigest() == box[iid]["sha256"]
        size_ok = nodes == box[iid]["nodes"] and nz == box[iid]["unknowns"]
        c = by_split.setdefault(split, {"files": 0, "sha256_equal": 0, "sizes_equal": 0})
        c["files"] += 1
        c["sha256_equal"] += sha_ok
        c["sizes_equal"] += size_ok
        if not sha_ok:
            differ.append(iid)
        if not size_ok:
            sizes_differ.append(iid)
    return {"zip_creator": "this system's" if creator is None else creator,
            "manifest_config_is_stamped": man["config_sha256"] == cfg_sha,
            "members_are_the_configured_draws": same, "members_shared_between_sets": shared, "by_split": by_split,
            "files": sum(c["files"] for c in by_split.values()),
            "sha256_equal": sum(c["sha256_equal"] for c in by_split.values()),
            "sizes_equal": sum(c["sizes_equal"] for c in by_split.values()),
            "sha256_differ": differ, "sizes_differ": sizes_differ}


def own_quantile(values, q: float) -> float:
    """Linear interpolation between the order statistics, written out here; an infinite order statistic with a
    positive weight makes the quantile infinite."""
    s = sorted(float(x) for x in values)
    h = (len(s) - 1) * q
    lo = math.floor(h)
    t = h - lo
    a, b = s[lo], s[min(lo + 1, len(s) - 1)]
    if (math.isinf(a) and 1 - t > 0) or (math.isinf(b) and t > 0):
        return a if (math.isinf(a) and 1 - t > 0) else b
    if math.isinf(a) or math.isinf(b):
        return b if t > 0 else a
    return a + (b - a) * t


def rel(x: float, y: float) -> float:
    if x == y:
        return 0.0
    if math.isinf(x) or math.isinf(y) or math.isnan(x) or math.isnan(y):
        return float("inf")
    return abs(x - y) / max(abs(x), abs(y))


def diff(x, y) -> float:
    x, y = float(x), float(y)
    if math.isnan(x) and math.isnan(y):
        return 0.0
    if math.isinf(x) or math.isinf(y) or math.isnan(x) or math.isnan(y):
        return 0.0 if x == y else float("inf")
    return abs(x - y)


def aggregate(rec: pathlib.Path, outdir: pathlib.Path, cfg: dict) -> dict:
    v = json.loads((rec / "verdict.json").read_text())
    ev = cfg["evaluation"]
    judged, jset, sets = ev["readings"]["judged"], ev["judged_set"], list(ev["sets"])
    seeds = cfg["arms"]["label_free"]["seeds"]
    split = sets_of(rec, cfg)
    L = len(cfg["data"]["eval_levels_mm"])
    out = {"returned": {k: v.get(k) for k in ("gate", "config_sha256", "judged", "status", "missing", "non_finite",
                                                "verdict", "C1_value", "C2_value", "C1", "C2", "per_seed")},
           "config_is_stamped": v.get("config_sha256") == sha256(cfg)}

    def rows_of(reading, seed, s):
        return v["readings"][reading][str(seed)][f"{s}_rows"]

    # (a) the criteria from the returned per-pair rows, with this script's own quantile
    crit, worst = {}, 0.0
    for reading in FILES:
        crit[reading] = {}
        for s in sets:
            per = {}
            for seed in seeds:
                rows = rows_of(reading, seed, s)
                ids = sorted(i for i in split if split[i] == s)
                assert sorted(rows) == ids and all(len(rows[i]) == L for i in ids)
                e = [abs(r["curve_err"]) for i in ids for r in rows[i]]
                box = v["readings"][reading][str(seed)][s]["abs_curve_err"]
                per[str(seed)] = {"n": len(e), "median": own_quantile(e, 0.5), "p90": own_quantile(e, 0.9),
                                  "max": max(e), "infinite": int(sum(math.isinf(x) for x in e)),
                                  "above_0.05": int(sum(x > 0.05 for x in e)), "above_0.10": int(sum(x > 0.10 for x in e)),
                                  "members_with_a_pair_above_0.10": int(sum(any(abs(r["curve_err"]) > 0.10 for r in rows[i])
                                                                            for i in ids)),
                                  "returned_median": box["median"], "returned_p90": box["p90"], "returned_n": box["n"]}
                worst = max(worst, rel(per[str(seed)]["median"], box["median"]), rel(per[str(seed)]["p90"], box["p90"]))
            med = [per[str(seed)]["median"] for seed in seeds]
            p90 = [per[str(seed)]["p90"] for seed in seeds]
            c1, c2 = own_quantile(med, 0.5), own_quantile(p90, 0.5)
            crit[reading][s] = {"per_seed": per, "C1_value": c1, "C2_value": c2,
                                "C1": bool(c1 <= THRESHOLDS["C1"]), "C2": bool(c2 <= THRESHOLDS["C2"])}
    j = crit[judged][jset]
    out["criteria_from_returned_rows"] = crit
    out["own_verdict"] = "PASS" if (j["C1"] and j["C2"]) else "FAIL"
    rr = v.get("reported_readings", {})
    out["criteria_agree_with_returned"] = {
        "largest_relative_difference_of_a_seed_median_or_p90": worst,
        "C1_value": rel(j["C1_value"], v["C1_value"]), "C2_value": rel(j["C2_value"], v["C2_value"]),
        "verdict_equal": out["own_verdict"] == v["verdict"],
        "reported_readings": {r: {"C1_value": rel(crit[r][jset]["C1_value"], rr[r]["C1_value"]),
                                  "C2_value": rel(crit[r][jset]["C2_value"], rr[r]["C2_value"])} for r in rr}}

    # (b) the recomputed metrics against the returned rows
    fl = {p.stem: json.loads(p.read_text()) for p in sorted((outdir / "fields").glob("*.json"))}
    cheap = {k: 0.0 for k in CHEAP}
    n_fields, bound_mismatch, failed_mismatch = 0, 0, 0
    for iid, m in fl.items():
        for key, rows in m["runs"].items():
            seed, reading = key.split("|")
            box = rows_of(reading, seed, split[iid])[iid]
            for r, b in zip(rows, box):
                n_fields += 1
                for k in CHEAP:
                    cheap[k] = max(cheap[k], diff(r[k], b[k]))
                bound_mismatch += r["within_bound"] != b["within_bound"]
                failed_mismatch += bool(r["evaluate_failed"]) != bool(b["evaluate_failed"])
    lc = [x for m in fl.values() for x in m["label_check"]]
    cp = [x for m in fl.values() for x in m["condensed_from_parts"].values()]
    out["fields"] = {"members": len(fl), "members_missing": sorted(i for i in split if i not in fl), "fields": n_fields,
                     "max_abs_diff": cheap, "within_bound_mismatches": int(bound_mismatch),
                     "evaluate_failed_mismatches": int(failed_mismatch)}
    if lc:
        out["label_check"] = {k: float(max(abs(x[k]) for x in lc)) for k in ("Pi_rel", "F_rel", "e_diff", "res_unconstrained")}
        out["label_check"].update(min_gap=float(min(x["min_gap"] for x in lc)),
                                  min_lambda=float(min(x["min_lambda"] for x in lc)), levels=len(lc))
    if cp:
        out["condensed_from_parts"] = {"member_seed_pairs": len(cp), "all_shapes_and_types_ok": all(x["shapes_and_types_ok"] for x in cp),
                                       "all_finite": all(x["finite"] for x in cp),
                                       "max_abs_diff": float(max(x["max_abs_diff"] for x in cp)),
                                       "unknowns_differing": int(sum(x["unknowns_differing"] for x in cp)),
                                       "max_abs_field": float(max(x["max_abs_field"] for x in cp)),
                                       "all_amplitudes_float32": all(x["amplitude_as_float32_equal"] for x in cp)}
    if (outdir / "curves").is_dir():                          # the files of step 4, packed into one for the records
        cv = [json.loads(p.read_text()) for p in sorted((outdir / "curves").glob("*.json"))]
        write_json(outdir / "curves.json", cv)
    else:
        cv = json.loads((outdir / "curves.json").read_text()) if (outdir / "curves.json").exists() else []
    by = {}
    alld = {k: 0.0 for k in KEYS}
    rec_err = {}
    for r in cv:
        b = rows_of(r["reading"], r["seed"], split[r["id"]])[r["id"]][r["level"]]
        g = by.setdefault(f"{r['reading']}|{split[r['id']]}|{r['seed']}",
                          {"pairs": 0, "max_abs_diff_curve_err": 0.0, "max_rel_diff_curve_err": 0.0,
                           "largest_returned_abs_curve_err": 0.0, "seconds": 0.0})
        g["pairs"] += 1
        g["max_abs_diff_curve_err"] = max(g["max_abs_diff_curve_err"], diff(r["curve_err"], b["curve_err"]))
        g["max_rel_diff_curve_err"] = max(g["max_rel_diff_curve_err"], rel(float(r["curve_err"]), float(b["curve_err"])))
        g["largest_returned_abs_curve_err"] = max(g["largest_returned_abs_curve_err"], abs(b["curve_err"]))
        g["seconds"] += r["seconds"]
        for k in KEYS:
            alld[k] = max(alld[k], diff(r[k], b[k]))
        rec_err[(r["reading"], split[r["id"]], str(r["seed"]), r["id"], r["level"])] = abs(r["curve_err"])
    out["curves"] = {"pairs": len(cv), "by_reading_set_seed": by, "max_abs_diff": alld,
                     "seconds": float(sum(r["seconds"] for r in cv))}
    n_judged = sum(1 for i in split if split[i] == jset) * L
    full = {}
    for seed in seeds:
        e = [x for (rd, s, sd, _, _), x in rec_err.items() if rd == judged and s == jset and sd == str(seed)]
        if len(e) == n_judged:
            full[str(seed)] = {"median": own_quantile(e, 0.5), "p90": own_quantile(e, 0.9), "n": len(e)}
    if len(full) == len(seeds):
        c1 = own_quantile([full[str(s)]["median"] for s in seeds], 0.5)
        c2 = own_quantile([full[str(s)]["p90"] for s in seeds], 0.5)
        out["criteria_from_recomputed_curves"] = {"per_seed": full, "C1_value": c1, "C2_value": c2,
                                                  "verdict": "PASS" if (c1 <= THRESHOLDS["C1"] and c2 <= THRESHOLDS["C2"]) else "FAIL"}

    # (c) the amplitudes, (d) the runs
    amp, runs = {}, {}
    for seed in seeds:
        rd = run_dir(rec, seed)
        info = json.loads((rd / "condense.json").read_text())
        amp[str(seed)] = {}
        for s in sets:
            ids = [i for i in sorted(split) if split[i] == s]
            a = [x for i in ids for x in info["members"][i]["a"]]
            mine = {"n": len(a), "min": float(min(a)), "max": float(max(a)), "median": float(np.median(a)),
                    "at_bound": int(sum(b for i in ids for b in info["members"][i]["at_bound"])),
                    "not_converged": int(sum(not c for i in ids for c in info["members"][i]["converged"]))}
            amp[str(seed)][s] = {**mine, "equal_to_returned": mine == v.get("amplitudes", {}).get(str(seed), {}).get(s)}
        h = json.loads((rd / "history.json").read_text())
        at = (rd / "attempts.log").read_text().replace("\r", "").strip().split("\n")
        runs[str(seed)] = {"status": h.get("status"), "steps": h.get("steps"), "total_steps": h.get("total_steps"),
                           "config_is_stamped": h.get("config_sha256") == sha256(cfg), "seed": h.get("seed"),
                           "epochs": len(h["loss"]), "mean_loss_last_ten_epochs": float(np.mean(h["loss"][-10:])),
                           "max_epoch_loss": float(max(h["loss"])), "cap_events": len(h["cap_events"]),
                           "bursts": len(h["bursts"]), "resumes": h.get("resumes"),
                           "hours": float(sum(h["epoch_seconds"]) / 3600), "torch": h.get("torch"), "gpu": h.get("gpu"),
                           "peak_memory_GiB": h.get("peak_memory_GiB"), "attempts": at,
                           "reading_is_configured": info["reading"] == ev["readings"]["condensed"]
                           and info["levels_mm"] == list(cfg["data"]["eval_levels_mm"])}
    out["amplitudes"], out["runs"] = amp, runs
    return out


def records(rec: pathlib.Path, cfg: dict) -> dict:
    import re
    out = {}
    cfg_sha = sha256(cfg)
    raw = (rec / "c22_config.json").read_bytes()
    out["configuration"] = {"returned_file_sha256": hashlib.sha256(raw).hexdigest(),
                            "returned_equals_stamped": json.loads(raw) == cfg,
                            "returned_bytes_equal_this_systems": raw == json.dumps(cfg, indent=1, sort_keys=True).encode("ascii"),
                            "stamped_sha256": cfg_sha}
    man = json.loads((rec / "manifest.json").read_text())
    box = {r["id"]: r for r in man["instances"]}
    split = sets_of(rec, cfg)
    led = json.loads((rec / "ledger.json").read_text())
    by = {e["id"]: e for e in led}
    lv = list(cfg["data"]["eval_levels_mm"])
    lim = cfg["data"]["kkt_limits"]
    worst = {k: (min if op == ">=" else max)(e["kkt_worst"][k] for e in led) for k, (op, _) in lim.items()}
    label_files = sorted(p.stem for p in (rec / "labels").glob("*.npz"))
    out["manifest"] = {"n": man["n"], "config_is_stamped": man["config_sha256"] == cfg_sha,
                       "by_split": {s: sum(1 for r in man["instances"] if r["split"] == s)
                                    for s in ("train", "eval", "former", "tested")}}
    out["ledger"] = {"entries": len(led), "members_once_each": sorted(by) == sorted(split) and len(by) == len(led),
                     "levels_are_configured": all(e["levels"] == lv for e in led),
                     "all_converged": all(all(e["converged"]) for e in led),
                     "worst": worst, "limits": lim,
                     "within_limits": {k: bool(worst[k] >= v if op == ">=" else worst[k] <= v) for k, (op, v) in lim.items()},
                     "max_F_vs_F_sigma": max(e["F_vs_F_sigma"] for e in led),
                     "iterations_max": max(max(e["iterations"]) for e in led),
                     "seconds_sum": float(sum(e["seconds"] for e in led)),
                     "solvers": sorted({e["solver"] for e in led}),
                     "first_time": min(e["time"] for e in led), "last_time": max(e["time"] for e in led),
                     "label_files": len(label_files), "label_files_are_the_ledgers": label_files == sorted(by),
                     "label_sha256_equal": int(sum(hashlib.sha256((rec / "labels" / f"{i}.npz").read_bytes()).hexdigest()
                                                   == by[i]["label_sha256"] for i in by)),
                     "inst_sha256_equal_manifest": int(sum(by[i]["inst_sha256"] == box[i]["sha256"] for i in by))}
    preds = {}
    for seed in cfg["arms"]["label_free"]["seeds"]:
        rd = run_dir(rec, seed)
        ok, n = True, {}
        for name in ("preds.npz", "preds_condensed.npz", "preds_base.npz"):
            with np.load(rd / name) as z:
                n[name] = len(z.files)
                ok &= sorted(z.files) == sorted(split)
                for i in z.files:
                    a = z[i]
                    want = (box[i]["unknowns"],) if name == "preds_base.npz" else (len(lv), box[i]["unknowns"])
                    ok &= a.dtype == np.float32 and a.shape == want and bool(np.isfinite(a).all())
        preds[str(seed)] = {"members_in_each_file": n, "members_shapes_types_finite_ok": bool(ok)}
        h = json.loads((rd / "history.json").read_text())
        text = "".join((rec / "queue" / f).read_text(errors="replace") for f in sorted(os.listdir(rec / "queue"))
                       if re.fullmatch(rf"7\d_c22_train_s{seed}(_c)*\.log", f))
        rows = re.findall(r"^epoch (\d+) loss ([\d.]+) ([\d.]+) s; cap events (\d+), bursts (\d+)", text, flags=re.M)
        epochs = [int(r[0]) for r in rows]
        steps = h["total_steps"] // len(h["loss"])
        preds[str(seed)]["log"] = {
            "epoch_lines": len(rows), "epochs_are_1_to_n": epochs == list(range(1, len(h["loss"]) + 1)),
            "losses_equal_history": all(abs(float(r[1]) - x) <= 5.1e-5 for r, x in zip(rows, h["loss"])),
            "seconds_equal_history": all(float(r[2]) == x for r, x in zip(rows, h["epoch_seconds"])),
            "cap_events_equal_history": all(int(r[3]) == sum(1 for c in h["cap_events"] if c[0] <= (k + 1) * steps)
                                            for k, r in enumerate(rows)),          # the history counts steps from 1
            "bursts_equal_history": all(int(r[4]) == sum(1 for c in h["bursts"] if c[0] <= (k + 1) * steps)
                                        for k, r in enumerate(rows)),
            "finished_line": '{"status": "finished", "steps": %d}' % h["total_steps"] in text}
    out["predictions_and_logs"] = preds
    jobs = []
    for f in sorted(os.listdir(rec / "queue")):
        if f.endswith(".done.json"):
            d = json.loads((rec / "queue" / f).read_text())
            jobs.append({k: d.get(k) for k in ("name", "returncode", "killed", "started", "ended", "seconds", "cancelled",
                                               "error") if k in d})
    out["queue"] = {"commands": jobs, "not_zero": [j["name"] for j in jobs if j.get("returncode") != 0],
                    "cancelled": [j["name"] for j in jobs if j.get("cancelled")]}
    ev = (rec / "queue" / "77_c22_evaluate.log").read_text(errors="replace").replace("\r", "").strip().split("\n")
    out["evaluation_log_last_lines"] = ev[-2:]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    ap.add_argument("instances")
    ap.add_argument("out")
    ap.add_argument("--ids", default="")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--budget", type=float, default=float("inf"))
    ap.add_argument("--regenerate", action="store_true")
    ap.add_argument("--fields", action="store_true")
    ap.add_argument("--select", default="")
    ap.add_argument("--curves", default="")
    ap.add_argument("--resolve", default="")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--records", dest="records_step", action="store_true")
    ap.add_argument("--reduced", action="store_true")
    ap.add_argument("--reverse", action="store_true")
    ap.add_argument("--creator", type=int, default=None)
    a = ap.parse_args()
    if a.reduced:
        from c22.smoke import reduced
        cfg = reduced()
    else:
        cfg = config()
        assert sha256(cfg) == STAMPED_CONFIG
    rec, inst, outdir = pathlib.Path(a.records), pathlib.Path(a.instances), pathlib.Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    env = environment()
    seeds = cfg["arms"]["label_free"]["seeds"]
    if a.regenerate:
        reg = {"environment": env, **regenerate(rec, inst, cfg, a.creator)}
        write_json(outdir / "regenerate.json", reg, indent=1)
        print(json.dumps(reg))
        return
    if a.select:
        print(json.dumps(select(rec, outdir, cfg, a.select)))
        return
    if a.resolve:
        rs = {"environment": env, "members": [resolve(rec, inst, i, cfg) for i in a.resolve.split(",") if i]}
        write_json(outdir / "resolve.json", rs, indent=1)
        print(json.dumps(rs, indent=1))
        return
    if a.aggregate:
        agg = {"environment": env, **aggregate(rec, outdir, cfg)}
        write_json(outdir / "aggregate.json", agg, indent=1)
        print(json.dumps({k: agg[k] for k in ("returned", "own_verdict", "criteria_agree_with_returned", "fields",
                                              "label_check", "condensed_from_parts") if k in agg}, indent=1))
        print(json.dumps({"curves": {k: agg["curves"][k] for k in ("pairs", "max_abs_diff", "seconds")},
                          "criteria_from_recomputed_curves": agg.get("criteria_from_recomputed_curves")}, indent=1))
        return
    if a.records_step:
        r = {"environment": env, **records(rec, cfg)}
        write_json(outdir / "records.json", r, indent=1)
        print(json.dumps(r, indent=1))
        return
    split = sets_of(rec, cfg)
    if a.fields:
        write_json(outdir / "environment_fields.json", env)
        ids = [i for i in a.ids.split(",") if i] or sorted(split)
        jobs = [(str(rec), str(inst), str(outdir), iid, seeds) for iid in ids]
        work = fields_member
    elif a.curves:
        write_json(outdir / "environment_curves.json", env)
        pairs = json.loads((outdir / f"pairs_{a.curves}.json").read_text())["pairs"]
        by = {}
        for iid, seed, reading, l in pairs:
            by.setdefault(iid, []).append((seed, reading, l))
        jobs = [(str(rec), str(inst), str(outdir), iid, p) for iid, p in sorted(by.items(), reverse=a.reverse)
                if any(not curve_file(outdir, iid, s, r, l).exists() for s, r, l in p)]
        work = curves_member
    else:
        raise SystemExit("name a step")
    t0 = time.perf_counter()
    if a.workers <= 1:
        for jb in jobs:
            if time.perf_counter() - t0 > a.budget:
                print("budget reached", flush=True)
                break
            print(*work(jb), flush=True)
    else:
        with C22D.pool(a.workers) as p:
            pending = []
            it = iter(jobs)
            done = False
            while not done or pending:
                while not done and len(pending) < a.workers:
                    if time.perf_counter() - t0 > a.budget:
                        print("budget reached", flush=True)
                        done = True
                        break
                    try:
                        pending.append(p.apply_async(work, (next(it),)))
                    except StopIteration:
                        done = True
                still = []
                for r in pending:
                    if r.ready():
                        print(*r.get(), flush=True)
                    else:
                        still.append(r)
                pending = still
                time.sleep(0.2)


if __name__ == "__main__":
    main()
