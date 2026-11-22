"""Audit of gate G-C2.3 from its return package (not under the stamp).

This script follows audit/c22_recompute.py, the audit of G-C2.2, step for step. It was written on 19 November 2026,
after the gate's run had ended and its verdict was known: nothing in it was fixed in advance. No record dates the
script: this is the author's statement.

    python -I audit/c23_recompute.py RECORDS INSTANCES OUT --regenerate [--creator 0]
    python -I audit/c23_recompute.py RECORDS INSTANCES OUT --fields [--ids x,y] [--workers N]
    python -I audit/c23_recompute.py RECORDS INSTANCES OUT --select RULE
    python -I audit/c23_recompute.py RECORDS INSTANCES OUT --curves NAME [--workers N] [--budget SECONDS] [--reverse]
    python -I audit/c23_recompute.py RECORDS INSTANCES OUT --host ARM [--ids x,y] [--workers N] [--budget SECONDS]
    python -I audit/c23_recompute.py RECORDS INSTANCES OUT --resolve x,y
    python -I audit/c23_recompute.py RECORDS INSTANCES OUT --aggregate
    python -I audit/c23_recompute.py RECORDS INSTANCES OUT --records

Run it from the joint/ folder, with c2/, c22/, c23/ and fejoint/ as stamped (docs/G-C2.3_code.sha256). RECORDS is the
return package's gate3_records/ folder or the kept copy whole, INSTANCES a folder for the regenerated instances, OUT
the folder of the outputs (records/c23/audit). The repository holds the kept copy in records/c23/return without its
label and prediction files: without them --fields, --curves, --host, --resolve and --records stop at a missing
file. --aggregate needs neither them nor the instances.

A run is named by its arm and seed: label_free_s5 to label_free_s7 (the networks of G-C2.2, which this gate only
reads) and supervised_512_s5 to supervised_512_s7. The steps:
  1. --regenerate: regenerates all 644 instances into INSTANCES with the stamped code, checks that the members are
     the configured draws and that no two of the four sets share a member, and compares the files with the returned
     manifest (regenerate.json). The bytes of a file depend on two things outside the stamped code: the zlib that
     numpy's savez_compressed writes through, and the system that writes the archive, which zipfile records in
     every entry (0 under Windows, 3 under Linux). The host was a Windows laptop whose Python writes through
     zlib 1.3: run this step with zlib 1.3 (on Linux, LD_PRELOAD of the system's libz.so.1.3 provides it) and
     with --creator 0. regenerate.json records the zlib and the creator used and, apart from the bytes, compares
     the arrays' sizes. The third sample was drawn on the host on 18 November 2026, from the tag's code, before this
     step was first run.
  2. --fields: for every held-out and tested member, one JSON file in OUT/fields (resumes):
     - the returned label on the regenerated instance: its field, evaluated there, against the label's energy, force
       and end displacement, and its optimality residuals;
     - for every run, the returned condensed field against keep(z_0 + a (z - z_0)), computed in float32 from the
       returned base field, raw field and amplitude;
     - for every run and both readings, every metric of every level that needs no solve (c2.evaluate.metrics with
       curve=False), and the field's own end displacement e and spring force F = 4 k_s (D - e), which part 1 uses.
  3. --select RULE: writes OUT/pairs_NAME.json, a list of pairs (member, run, reading, level) whose judged error is
     to be recomputed with an exact solve. RULE is one of
       part1           the label-free runs in the judged reading on the judged set (1,344 pairs): part 1 and the
                       label-free side of part 2
       supervised      the supervised runs in the judged reading on the judged set (1,344 pairs)
       side            the supervised runs read raw on the judged set (1,344 pairs): the ratios that the
                       pre-specification has stated beside the wording
       judged          part1 and supervised together
       all             every pair of both readings on the three sets, for the six runs
       tail:T:N:SEED   of the label-free runs in the judged reading on the judged set: every pair whose returned
                       error is at least T in absolute value, and N more drawn without replacement with numpy's
                       default_rng(SEED)
     NAME is the rule with ':' replaced by '_'.
  4. --curves NAME: for the pairs of OUT/pairs_NAME.json, the stamped metric function with its exact solve at the
     predicted end displacement, one JSON file a pair in OUT/curves (resumes; stops starting members after
     --budget seconds; --reverse takes the members in reverse order, for a second process on the same list).
     Step 6 packs these files into OUT/curves.json, which is what the records keep.
     --host ARM: step 4 again, in the visiting order of the stamped evaluation. It was added on 20 November 2026,
     after step 4 had shown that the error of a pair can depend on the pair that the same problem object solved
     before it (docs/G-C2.3_verdict.md, the section on the defect of the measuring code). ARM is label_free or
     supervised_512. For each member of the judged set, or of --ids: one problem object, and for each run of the
     arm the judged reading and then the reported one, each over the levels in order, as c23/evaluate.py visits
     them; one JSON file a member in OUT/host_order/ARM, written when the member is complete (resumes by whole
     members). Step 6 packs these files into OUT/host_order.json, which is what the records keep.
  5. --resolve: re-solves the listed members at their levels from the regenerated instances, as the labels were
     solved, and compares with the returned labels and the ledger (resolve.json).
  6. --aggregate (aggregate.json):
     (a) from the per-pair rows of the two returned rows files, with this script's own quantile: every run's median
         and 90th percentile of the judged error for both readings and the three sets, the medians over the seeds,
         the ratios and the wording of part 2 by the pre-specification's text, the ratios with the supervised arm
         read raw, and the identity values against the configuration's; with this script's own code, the spread,
         the flags, S1 to S3 and the ranking of part 1 for both arms, both readings and the three sets; all compared
         with the returned verdict.json;
     (b) every recomputed metric of steps 2 and 4 against the returned rows, for step 4 in each of its two orders;
         where every pair of an arm's reading on the judged set has been recomputed, the statistics, part 1 and the
         ratios again from the recomputed errors; the pairs recomputed in both orders against each other;
     (c) the amplitude counts from the returned condense.json files;
     (d) each run's history and attempts.
     Where the folders OUT/curves and OUT/host_order exist, this step writes OUT/curves.json and
     OUT/host_order.json again from them; where they do not, as in the repository, it reads the two packed files.
     The step takes the configuration from the stamped code and does not read the returned configuration file;
     step 7 compares that file with the stamped one.
  7. --records: reads the returned records without computing a field (records.json): the returned configuration
     against the stamped one; the manifest; the ledger (every member once, at its configured levels, converged, its
     residuals within the configured limits, the label files and the instances it names by their SHA-256, and the
     two hashes of ledger entries that the rows files and the supervised histories carry); the prediction files
     (the members they hold, their shapes and types); each supervised run's log against its history and each
     label-free run's log against its history; the inputs that the verdict records against the files; and how every
     command of the queue ended.
Steps 2 to 5 use one BLAS thread a process, as the host's labels and evaluation did. The host had no pypardiso: set
FEJOINT_SOLVER=legacy where it loads, so that the solves use scipy's SuperLU.
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
import re  # noqa: E402
import time  # noqa: E402
import zlib  # noqa: E402
from dataclasses import asdict  # noqa: E402

ROOT = pathlib.Path.cwd()
sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402
import scipy  # noqa: E402

from c23.config import config, sha256  # noqa: E402
from c23 import data as C23D  # noqa: E402
from c2.data import load_export, solve_levels, export_member, _pack  # noqa: E402
from c2.evaluate import metrics  # noqa: E402
from c2.instance import ExportedProblem  # noqa: E402
from fejoint import linsolve  # noqa: E402

STAMPED_CONFIG = "3b41c26636637e7279f0a43f95406af3b37700c18d979c6d8dd8ec477e055f9e"
FILES = {"condensed": "preds_condensed.npz", "raw": "preds.npz"}
ARMS = ("label_free", "supervised_512")
SPLITS = ("train", "third", "eval", "tested")
CHEAP = ("F_err", "e_err", "F_sigma_err", "gap", "bound", "iou_contact", "iou_plastic", "bolt_err", "u_rel_l2", "e", "F")
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


def runs_of(cfg: dict, arm: str | None = None) -> list[str]:
    return [f"{a}_s{s}" for a in ARMS if arm in (None, a) for s in cfg["arms"][a]["seeds"]]


def arm_seed(run: str) -> tuple[str, str]:
    arm, seed = run.rsplit("_s", 1)
    return arm, seed


def label_of(rec: pathlib.Path, iid: str) -> dict:
    with np.load(rec / "labels" / f"{iid}.npz") as z:
        return {k: z[k] for k in z.files}


def run_dir(rec: pathlib.Path, run: str) -> pathlib.Path:
    return rec / "run_files" / run


def field_of(rec: pathlib.Path, run: str, reading: str, iid: str) -> np.ndarray:
    with np.load(run_dir(rec, run) / FILES[reading]) as z:
        return z[iid]


def sets_of(rec: pathlib.Path, cfg: dict) -> dict:
    man = json.loads((rec / "manifest.json").read_text())
    return {r["id"]: r["split"] for r in man["instances"] if r["split"] in cfg["evaluation"]["sets"]}


def rows_files(rec: pathlib.Path) -> dict:
    return {arm: json.loads((rec / f"rows_{arm}.json").read_text()) for arm in ARMS}


def problem(inst: pathlib.Path, rec: pathlib.Path, iid: str):
    ex, _ = load_export(inst / f"{iid}.npz")
    ref = label_of(rec, iid)
    P = ExportedProblem(ex)
    ref_pl = [P.evaluate(ref["z"][l], float(ref["D"][l]))["plastic"] for l in range(ref["D"].size)]
    return ex, ref, P, ref_pl


def own_e_F(P, z, D: float) -> tuple[float, float]:
    """The field's end displacement and its spring force, as the gate's rows carry them."""
    e = float(np.asarray(z, dtype=np.float64)[P.e_idx])
    return e, 4.0 * P.k_s * (D - e)


def fields_member(job):
    """Step 2 for one member."""
    rec, inst, outdir, iid, runs = job
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
    out, parts = {}, {}
    for run in runs:
        rd = run_dir(rec, run)
        raw, cond = field_of(rec, run, "raw", iid), field_of(rec, run, "condensed", iid)
        with np.load(rd / "preds_base.npz") as z:
            base = z[iid]
        info = json.loads((rd / "condense.json").read_text())["members"][iid]
        a = np.asarray(info["a"], dtype=np.float32)
        ok = raw.dtype == np.float32 and cond.dtype == np.float32 and base.dtype == np.float32 \
            and raw.shape == cond.shape == (L, base.size) and a.shape == (L,)
        zc = base[None, :] + a[:, None] * (raw - base[None, :])
        zc = np.where(nonneg[None, :], np.maximum(zc, np.float32(0)), zc)
        d = np.abs(zc.astype(np.float64) - cond.astype(np.float64))
        parts[run] = {"shapes_and_types_ok": bool(ok), "finite": bool(np.isfinite(raw).all() and np.isfinite(cond).all()
                                                                     and np.isfinite(base).all()),
                      "max_abs_diff": float(d.max()), "unknowns_differing": int((d > 0).sum()),
                      "max_abs_field": float(np.abs(cond).max()), "amplitude_as_float32_equal": bool(
                          np.array_equal(a.astype(np.float64), np.asarray(info["a"], dtype=np.float64)))}
        for reading, Z in (("condensed", cond), ("raw", raw)):
            rows = []
            for l in range(L):
                r = metrics(P, ex, Z[l], ref, ref_pl[l], l, curve=False)
                r["e"], r["F"] = own_e_F(P, Z[l], float(ref["D"][l]))
                rows.append(r)
            out[f"{run}|{reading}"] = rows
    write_json(out_p, {"id": iid, "label_check": lab, "condensed_from_parts": parts, "runs": out,
                       "seconds": time.perf_counter() - t0})
    return iid, round(time.perf_counter() - t0, 1)


def curve_file(outdir: pathlib.Path, iid: str, run: str, reading: str, l: int) -> pathlib.Path:
    return outdir / "curves" / f"{iid}__{run}_{reading}_l{l}.json"


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
    for run, reading, l in todo:
        if (run, reading) not in cache:
            cache[(run, reading)] = field_of(rec, run, reading, iid)
        t1 = time.perf_counter()
        row = metrics(P, ex, cache[(run, reading)][l], ref, ref_pl[l], l)
        row["e"], row["F"] = own_e_F(P, cache[(run, reading)][l], float(ref["D"][l]))
        row.update(id=iid, run=run, reading=reading, level=l, seconds=time.perf_counter() - t1)
        write_json(curve_file(outdir, iid, run, reading, l), row)
    return iid, len(todo), round(time.perf_counter() - t0, 1)


def host_file(outdir: pathlib.Path, arm: str, iid: str) -> pathlib.Path:
    return outdir / "host_order" / arm / f"{iid}.json"


def host_member(job):
    """Step 4 in the gate's own visiting order, for one member and one arm: one problem object for the member, as
    in the stamped evaluation; for each run of the arm the judged reading and then the reported one, each over the
    levels in order. The reference code keeps the bubble parameters of its last solve as the start of the next
    one, so a pair's solve can depend on the pair visited before it (see the note in the audit record); a member
    is therefore kept whole or not at all, never taken up half-way."""
    rec, inst, outdir, arm, iid, runs, readings = job
    rec, inst, outdir = pathlib.Path(rec), pathlib.Path(inst), pathlib.Path(outdir)
    f = host_file(outdir, arm, iid)
    if f.exists():
        return iid, 0, 0.0
    t0 = time.perf_counter()
    ex, ref, P, ref_pl = problem(inst, rec, iid)
    rows = []
    for run in runs:
        for reading in readings:
            Z = field_of(rec, run, reading, iid)
            for l in range(ref["D"].size):
                t1 = time.perf_counter()
                row = metrics(P, ex, Z[l], ref, ref_pl[l], l)
                row["e"], row["F"] = own_e_F(P, Z[l], float(ref["D"][l]))
                row.update(id=iid, run=run, reading=reading, level=l, seconds=time.perf_counter() - t1)
                rows.append(row)
    write_json(f, rows)
    return iid, len(rows), round(time.perf_counter() - t0, 1)


def select(rec: pathlib.Path, outdir: pathlib.Path, cfg: dict, rule: str) -> dict:
    ev = cfg["evaluation"]
    judged, jset = ev["readings"]["judged"], ev["judged_set"]
    split = sets_of(rec, cfg)
    L = len(cfg["data"]["eval_levels_mm"])
    name = rule.replace(":", "_")
    ids = [i for i in sorted(split) if split[i] == jset]

    def block(arm, reading):
        return [[i, run, reading, l] for i in ids for run in runs_of(cfg, arm) for l in range(L)]

    if rule == "part1":
        pairs, note = block("label_free", judged), "the label-free runs in the judged reading on the judged set"
    elif rule == "supervised":
        pairs, note = block("supervised_512", judged), "the supervised runs in the judged reading on the judged set"
    elif rule == "side":
        pairs, note = block("supervised_512", "raw"), "the supervised runs read raw on the judged set"
    elif rule == "judged":
        pairs = block("label_free", judged) + block("supervised_512", judged)
        note = "every pair of the judged reading on the judged set, both arms"
    elif rule == "all":
        pairs = [[i, run, r, l] for i in sorted(split) for run in runs_of(cfg) for r in FILES for l in range(L)]
        note = "every pair of both readings on the three sets, for the six runs"
    elif rule.startswith("tail:"):
        _, thr, n, rs = rule.split(":")
        thr, n, rs = float(thr), int(n), int(rs)
        rows = rows_files(rec)["label_free"]["readings"][judged]
        every = block("label_free", judged)
        err = [abs(float(rows[arm_seed(run)[1]][f"{jset}_rows"][i][l]["curve_err"])) for i, run, _, l in every]
        tail = [p for p, e in zip(every, err) if not e < thr]            # not-a-number and infinite count as large
        rest = [p for p, e in zip(every, err) if e < thr]
        pick = np.random.default_rng(rs).choice(len(rest), size=min(n, len(rest)), replace=False)
        pairs = tail + [rest[k] for k in sorted(int(k) for k in pick)]
        note = (f"of the label-free runs in the judged reading on the judged set: the {len(tail)} pairs whose returned "
                f"error is at least {thr} in absolute value and {len(pairs) - len(tail)} of the other {len(rest)}, drawn "
                f"without replacement with numpy.random.default_rng({rs})")
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
    """Every instance, written as c23.data.generate writes it, against the returned manifest. creator: the system
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
    mem = C23D.members(cfg)
    same = len(mem) == man["n"] and all(i in box and box[i]["params"] == asdict(prm) and box[i]["split"] == s
                                        for i, s, prm in mem)
    key = {s: {json.dumps(asdict(prm), sort_keys=True) for i, t, prm in mem if t == s} for s in SPLITS}
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


def rel(x, y) -> float:
    if x is None or y is None:
        return 0.0 if x is y else float("inf")
    x, y = float(x), float(y)
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


def err_of(row: dict) -> float:
    """The judged error of a pair; a pair without a number counts as infinite, as the pre-specification has it."""
    e = row.get("abs_curve_err", None)
    if e is None:
        e = abs(float(row["curve_err"]))
    e = float(e)
    return e if math.isfinite(e) else float("inf")


def own_auc(score, positive):
    """The probability that a positive pair has a larger score than a negative pair, ties counting half."""
    pos = [s for s, p in zip(score, positive) if p]
    neg = [s for s, p in zip(score, positive) if not p]
    if not pos or not neg:
        return None
    neg.sort()
    import bisect
    wins = 0.0
    for s in pos:
        lo, hi = bisect.bisect_left(neg, s), bisect.bisect_right(neg, s)
        wins += lo + 0.5 * (hi - lo)
    return wins / (len(pos) * len(neg))


def own_part1(sc: dict, F_by_run: list, err_by_run: list) -> dict:
    """Part 1 by the configuration's texts, written out here. F_by_run, err_by_run: one list of pairs for each run,
    the pairs in one order."""
    n = len(F_by_run[0])
    spread, flag = [], []
    for k in range(n):
        f = sorted(float(F[k]) for F in F_by_run)
        med = f[len(f) // 2] if len(f) % 2 else 0.5 * (f[len(f) // 2 - 1] + f[len(f) // 2])
        s = (f[-1] - f[0]) / abs(med) if (med != 0 and all(math.isfinite(x) for x in f)) else float("inf")
        spread.append(s)
        flag.append(bool(s >= sc["threshold"]))
    nf = [k for k in range(n) if not flag[k]]
    above10 = sum(1 for k in nf if any(e[k] > 0.10 for e in err_by_run))
    readings = len(nf) * len(err_by_run)
    above05 = sum(1 for k in nf for e in err_by_run if e[k] > 0.05)
    share = above05 / readings if readings else 0.0
    out = {"pairs": n, "flagged": sum(flag), "flagged_share": sum(flag) / n,
           "not_flagged_pairs_above_0.10_in_any_run": above10, "not_flagged_readings": readings,
           "not_flagged_readings_above_0.05": above05, "not_flagged_share_above_0.05": share,
           "pairs_above": {t: {"total": [sum(1 for x in e if x > float(t)) for e in err_by_run],
                               "flagged": [sum(1 for k, x in enumerate(e) if x > float(t) and flag[k]) for e in err_by_run]}
                           for t in ("0.05", "0.1")},
           "spread_max": max(spread), "S1": above10 == 0, "S2": share <= 0.01, "S3": sum(flag) / n <= 0.35}
    out["verdict"] = "PASS" if (out["S1"] and out["S2"] and out["S3"]) else "FAIL"
    aucs = [own_auc(spread, [x > 0.05 for x in e]) for e in err_by_run]
    have = [a for a in aucs if a is not None]
    out["auc_above_0.05"] = aucs
    out["R"] = "NOT EVALUABLE" if not have else ("HOLDS" if min(have) >= 0.90 else "DOES NOT HOLD")
    out["_spread"], out["_flag"] = spread, flag
    return out


def own_wording(band, r1: float, r2: float) -> str:
    """The wording of part 2 by the pre-specification's text."""
    lo, hi = band
    if math.isnan(r1) or math.isnan(r2):
        return "NOT COMPARABLE"
    if lo <= r1 <= hi and lo <= r2 <= hi:
        return "comparable"
    if r1 < 1 and r2 < 1 and (r1 < lo or r2 < lo):
        return "supervised closer"
    if r1 > 1 and r2 > 1 and (r1 > hi or r2 > hi):
        return "label-free closer"
    return "mixed"


def ratio(a: float, b: float) -> float:
    if math.isinf(a) and math.isinf(b):
        return float("nan")
    if b == 0:
        return float("inf") if a > 0 else float("nan")
    return a / b


def part1_against(mine: dict, kept: dict) -> dict:
    """The differences between this script's part 1 and a block of the returned verdict."""
    out = {k: mine[k] == kept[k] for k in ("pairs", "flagged", "not_flagged_pairs_above_0.10_in_any_run", "not_flagged_readings",
                                           "not_flagged_readings_above_0.05", "S1", "S2", "S3", "verdict", "pairs_above")}
    out["R"] = mine["R"] == kept["ranking"]["R"]
    out["flagged_share"] = rel(mine["flagged_share"], kept["flagged_share"])
    out["not_flagged_share_above_0.05"] = rel(mine["not_flagged_share_above_0.05"], kept["not_flagged_share_above_0.05"])
    out["auc_above_0.05"] = max(rel(a, b) for a, b in zip(mine["auc_above_0.05"], kept["ranking"]["auc_above_0.05"]))
    ids = list(kept["by_member"])
    ks = [x for i in ids for x in kept["by_member"][i]["spread"]]
    kf = [bool(x) for i in ids for x in kept["by_member"][i]["flagged"]]
    out["flags_equal"] = kf == mine["_flag"]
    out["spread"] = max(rel(a, b) for a, b in zip(mine["_spread"], ks))
    out["all_equal"] = all(v is True or (not isinstance(v, bool) and v <= 1e-12) for v in out.values())
    return out


def part1_of(v: dict) -> dict:
    """What part 1 of a verdict file consists of (as c23.evaluate._part1 has it): what the label-free rows were
    computed from, the SHA-256 of their file, the identity check, the self-check and the three words."""
    return {"config_sha256": v["config_sha256"], "inputs": v["inputs"].get("label_free"),
            "rows_sha256": v.get("rows_sha256", {}).get("label_free"), "identity": v["identity"],
            "self_check": v.get("self_check"),
            "verdict": {k: v["verdict"][k] for k in ("identity", "self_check", "ranking")}}


def aggregate(rec: pathlib.Path, outdir: pathlib.Path, cfg: dict) -> dict:
    v = json.loads((rec / "verdict.json").read_text())
    v1 = json.loads((rec / "verdict_part1.json").read_text())
    rf = rows_files(rec)
    ev, cmp_ = cfg["evaluation"], cfg["comparison"]
    judged, jset, sets = ev["readings"]["judged"], ev["judged_set"], list(ev["sets"])
    split = sets_of(rec, cfg)
    L = len(cfg["data"]["eval_levels_mm"])
    ids_of = {s: sorted(i for i in split if split[i] == s) for s in sets}
    out = {"returned": {k: v.get(k) for k in ("gate", "config_sha256", "judged", "status", "missing", "non_finite",
                                                "not_evaluated", "verdict", "part1_same_as_first", "identity", "cost")},
           "config_is_stamped": v.get("config_sha256") == sha256(cfg),
           "rows_files": {arm: {"config_is_stamped": rf[arm]["config_sha256"] == sha256(cfg), "arm": rf[arm]["arm"],
                                "sha256": hashlib.sha256((rec / f"rows_{arm}.json").read_bytes()).hexdigest(),
                                "sha256_in_verdict": v["rows_sha256"].get(arm),
                                "inputs_equal_verdicts": rf[arm]["inputs"] == v["inputs"].get(arm)} for arm in ARMS}}

    def rows_of(run, reading, s):
        arm, seed = arm_seed(run)
        return rf[arm]["readings"][reading][seed][f"{s}_rows"]

    # (a) the statistics of both arms from the returned per-pair rows, with this script's own quantile
    crit, worst = {}, 0.0
    for arm in ARMS:
        crit[arm] = {}
        for reading in FILES:
            crit[arm][reading] = {}
            for s in sets:
                per = {}
                for run in runs_of(cfg, arm):
                    rows = rows_of(run, reading, s)
                    assert sorted(rows) == ids_of[s] and all(len(rows[i]) == L for i in ids_of[s])
                    e = [err_of(r) for i in ids_of[s] for r in rows[i]]
                    per[run] = {"n": len(e), "median": own_quantile(e, 0.5), "p90": own_quantile(e, 0.9), "max": max(e),
                                "infinite": int(sum(math.isinf(x) for x in e)),
                                "above_0.05": int(sum(x > 0.05 for x in e)), "above_0.10": int(sum(x > 0.10 for x in e))}
                med = [per[run]["median"] for run in runs_of(cfg, arm)]
                p90 = [per[run]["p90"] for run in runs_of(cfg, arm)]
                box = v["statistics"][arm][reading][s]
                c1, c2 = own_quantile(med, 0.5), own_quantile(p90, 0.5)
                worst = max([worst, rel(c1, box["C1_value"]), rel(c2, box["C2_value"])]
                            + [rel(a, b) for a, b in zip(med, box["per_seed"]["abs_curve_err_median"])]
                            + [rel(a, b) for a, b in zip(p90, box["per_seed"]["abs_curve_err_p90"])])
                crit[arm][reading][s] = {"per_run": per, "C1_value": c1, "C2_value": c2,
                                         "returned_C1_value": box["C1_value"], "returned_C2_value": box["C2_value"]}
    out["statistics_from_returned_rows"] = crit
    out["statistics_largest_relative_difference_from_returned"] = worst

    def ratios(sup, lf):
        r1, r2 = ratio(sup["C1_value"], lf["C1_value"]), ratio(sup["C2_value"], lf["C2_value"])
        return {"ratio_of_medians": r1, "ratio_of_p90": r2, "wording": own_wording(cmp_["band"], r1, r2)}

    def ratios_against(mine, kept):
        return {"ratio_of_medians": rel(mine["ratio_of_medians"], kept["ratio_of_medians"]),
                "ratio_of_p90": rel(mine["ratio_of_p90"], kept["ratio_of_p90"]), "wording_equal": mine["wording"] == kept["wording"]}

    sup, lf = crit["supervised_512"], crit["label_free"]
    mine_j = ratios(sup[judged][jset], lf[judged][jset])
    mine_side = ratios(sup["raw"][jset], lf[judged][jset])
    out["part2"] = {"judged": mine_j, "judged_against_returned": ratios_against(mine_j, v["comparison"]),
                    "supervised_raw_over_label_free_judged": mine_side,
                    "side_against_returned": ratios_against(mine_side, v["comparison"]["supervised_raw_against_label_free_judged"]["raw"]),
                    "reported": {r: {s: ratios(sup[r][s], lf[r][s]) for s in sets} for r in FILES},
                    "returned_wording": v["verdict"]["comparison"], "wording_equal": mine_j["wording"] == v["verdict"]["comparison"]}
    out["part2"]["reported_against_returned"] = {r: {s: ratios_against(out["part2"]["reported"][r][s], v["comparison"]["reported"][r][s])
                                                     for s in sets} for r in FILES}

    # the identity values: this gate's label-free rows on G-C2.2's fresh members against the configuration's
    idv = cfg["arms"]["label_free"]["identity"]
    worst_id = 0.0
    for reading, want in idv["values"].items():
        got = {"abs_curve_err_median": [lf[reading]["eval"]["per_run"][run]["median"] for run in runs_of(cfg, "label_free")],
               "abs_curve_err_p90": [lf[reading]["eval"]["per_run"][run]["p90"] for run in runs_of(cfg, "label_free")]}
        for k in want:
            worst_id = max(worst_id, max(diff(a, b) for a, b in zip(got[k], want[k])))
    out["identity"] = {"largest_difference_from_the_configurations_values": worst_id, "tolerance": idv["tolerance"],
                       "ok": worst_id <= idv["tolerance"], "returned": v["identity"]}

    # part 1, with this script's own code, for both arms, both readings and the three sets
    p1 = {}
    for arm in ARMS:
        p1[arm] = {}
        for reading in FILES:
            p1[arm][reading] = {}
            for s in sets:
                F = [[float(r["F"]) for i in ids_of[s] for r in rows_of(run, reading, s)[i]] for run in runs_of(cfg, arm)]
                E = [[err_of(r) for i in ids_of[s] for r in rows_of(run, reading, s)[i]] for run in runs_of(cfg, arm)]
                mine = own_part1(cfg["self_check"], F, E)
                kept = v["self_check_reported"][arm][reading][s]
                agree = part1_against(mine, kept)
                p1[arm][reading][s] = {**{k: x for k, x in mine.items() if not k.startswith("_")}, "against_returned": agree}
    out["part1_from_returned_rows"] = p1
    j1 = p1["label_free"][judged][jset]
    out["part1"] = {"own_self_check": j1["verdict"], "own_ranking": j1["R"],
                    "equal_to_returned_words": j1["verdict"] == v["verdict"]["self_check"] and j1["R"] == v["verdict"]["ranking"],
                    "judged_block_is_the_reported_block": v["self_check"] == v["self_check_reported"]["label_free"][judged][jset],
                    "all_blocks_equal_to_returned": all(p1[a][r][s]["against_returned"]["all_equal"] for a in ARMS for r in FILES for s in sets),
                    "kept_part1_record_equals_the_final_verdicts": part1_of(v1) == part1_of(v)}

    # (b) the recomputed metrics against the returned rows
    fl = {p.stem: json.loads(p.read_text()) for p in sorted((outdir / "fields").glob("*.json"))}
    cheap = {k: 0.0 for k in CHEAP}
    n_fields, bound_mismatch, failed_mismatch = 0, 0, 0
    for iid, m in fl.items():
        for key, rows in m["runs"].items():
            run, reading = key.split("|")
            box = rows_of(run, reading, split[iid])[iid]
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
        out["condensed_from_parts"] = {"member_run_pairs": len(cp), "all_shapes_and_types_ok": all(x["shapes_and_types_ok"] for x in cp),
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
    rec_rows = {}
    for r in cv:
        b = rows_of(r["run"], r["reading"], split[r["id"]])[r["id"]][r["level"]]
        g = by.setdefault(f"{r['reading']}|{split[r['id']]}|{r['run']}",
                          {"pairs": 0, "max_abs_diff_curve_err": 0.0, "max_rel_diff_curve_err": 0.0,
                           "largest_returned_abs_curve_err": 0.0, "infinite_returned": 0, "infinite_recomputed": 0, "seconds": 0.0})
        g["pairs"] += 1
        g["max_abs_diff_curve_err"] = max(g["max_abs_diff_curve_err"], diff(r["curve_err"], b["curve_err"]))
        g["max_rel_diff_curve_err"] = max(g["max_rel_diff_curve_err"], rel(float(r["curve_err"]), float(b["curve_err"])))
        if math.isfinite(float(b["curve_err"])):
            g["largest_returned_abs_curve_err"] = max(g["largest_returned_abs_curve_err"], abs(float(b["curve_err"])))
        g["infinite_returned"] += not math.isfinite(float(b["curve_err"]))
        g["infinite_recomputed"] += not math.isfinite(float(r["curve_err"]))
        g["seconds"] += r["seconds"]
        for k in KEYS:
            alld[k] = max(alld[k], diff(r[k], b[k]))
        rec_rows[(r["run"], r["reading"], r["id"], r["level"])] = r
    out["curves"] = {"pairs": len(cv), "by_reading_set_run": by, "max_abs_diff": alld,
                     "seconds": float(sum(r["seconds"] for r in cv))}

    # step 4 again in the gate's own visiting order (host_member): whole members, both readings of one arm
    ho = {}
    if (outdir / "host_order").is_dir():
        ho = {arm: {q.stem: json.loads(q.read_text()) for q in sorted((outdir / "host_order" / arm).glob("*.json"))}
              for arm in ARMS if (outdir / "host_order" / arm).is_dir()}
        write_json(outdir / "host_order.json", ho)
    elif (outdir / "host_order.json").exists():
        ho = json.loads((outdir / "host_order.json").read_text())
    order = [judged] + list(ev["readings"]["reported"])
    hby, hd, host_rows, noted, n_host = {}, {k: 0.0 for k in KEYS}, {}, [], 0
    for arm, members in ho.items():
        want = [(run, reading, l) for run in runs_of(cfg, arm) for reading in order for l in range(L)]
        for iid, rows in members.items():
            assert [(r["run"], r["reading"], r["level"]) for r in rows] == want and all(r["id"] == iid for r in rows)
            for r in rows:
                b = rows_of(r["run"], r["reading"], split[iid])[iid][r["level"]]
                g = hby.setdefault(f"{r['reading']}|{split[iid]}|{r['run']}",
                                   {"pairs": 0, "max_abs_diff_curve_err": 0.0, "max_rel_diff_curve_err": 0.0,
                                    "infinite_returned": 0, "infinite_recomputed": 0, "notes_differing": 0, "seconds": 0.0})
                n_host += 1
                g["pairs"] += 1
                g["max_abs_diff_curve_err"] = max(g["max_abs_diff_curve_err"], diff(r["curve_err"], b["curve_err"]))
                g["max_rel_diff_curve_err"] = max(g["max_rel_diff_curve_err"], rel(float(r["curve_err"]), float(b["curve_err"])))
                g["infinite_returned"] += not math.isfinite(float(b["curve_err"]))
                g["infinite_recomputed"] += not math.isfinite(float(r["curve_err"]))
                g["notes_differing"] += r["curve_note"] != b["curve_note"]
                g["seconds"] += r["seconds"]
                for k in KEYS:
                    hd[k] = max(hd[k], diff(r[k], b[k]))
                if r["curve_note"] or b["curve_note"]:
                    noted.append({"id": iid, "run": r["run"], "reading": r["reading"], "level": r["level"],
                                  "recomputed": [r["curve_err"], r["curve_note"]], "returned": [b["curve_err"], b["curve_note"]]})
                host_rows[(r["run"], r["reading"], iid, r["level"])] = r
    out["host_order"] = {"members": {arm: len(m) for arm, m in ho.items()}, "pairs": n_host, "by_reading_set_run": hby,
                         "max_abs_diff": hd, "pairs_with_a_note": noted,
                         "seconds": float(sum(g["seconds"] for g in hby.values()))}
    # the pairs recomputed in both orders: where the two recomputations differ
    both = [(k, rec_rows[k], host_rows[k]) for k in sorted(set(rec_rows) & set(host_rows))]
    out["two_orders"] = {"pairs_in_both": len(both),
                         "max_abs_diff_curve_err_where_both_finite": max(
                             [diff(a["curve_err"], b["curve_err"]) for _, a, b in both
                              if math.isfinite(float(a["curve_err"])) and math.isfinite(float(b["curve_err"]))] or [0.0]),
                         "finite_in_one_only": [{"run": k[0], "reading": k[1], "id": k[2], "level": k[3],
                                                 "other_order": [a["curve_err"], a["curve_note"]],
                                                 "gates_order": [b["curve_err"], b["curve_note"]]} for k, a, b in both
                                                if math.isfinite(float(a["curve_err"])) != math.isfinite(float(b["curve_err"]))]}

    def recomputed(arm, reading, rec_rows=rec_rows):          # None unless every pair of the arm's reading on the judged set is there
        per, F, E = {}, [], []
        for run in runs_of(cfg, arm):
            rows = [rec_rows.get((run, reading, i, l)) for i in ids_of[jset] for l in range(L)]
            if any(r is None for r in rows):
                return None
            e = [err_of(r) for r in rows]
            per[run] = {"median": own_quantile(e, 0.5), "p90": own_quantile(e, 0.9), "n": len(e)}
            F.append([float(r["F"]) for r in rows])
            E.append(e)
        return {"per_run": per, "C1_value": own_quantile([p["median"] for p in per.values()], 0.5),
                "C2_value": own_quantile([p["p90"] for p in per.values()], 0.5), "_F": F, "_E": E}

    rc = {(arm, reading): recomputed(arm, reading) for arm in ARMS for reading in FILES}
    out["statistics_from_recomputed_curves"] = {f"{arm}|{reading}": ({k: x for k, x in b.items() if not k.startswith("_")} if b else None)
                                                for (arm, reading), b in rc.items()}
    lfj = rc[("label_free", judged)]
    if lfj:
        mine = own_part1(cfg["self_check"], lfj["_F"], lfj["_E"])
        out["part1_from_recomputed_curves"] = {**{k: x for k, x in mine.items() if not k.startswith("_")},
                                               "against_returned": part1_against(mine, v["self_check"])}
        for name, key in (("part2_from_recomputed_curves", ("supervised_512", judged)),
                          ("side_ratios_from_recomputed_curves", ("supervised_512", "raw"))):
            if rc[key]:
                out[name] = ratios(rc[key], lfj)
    # the same from the rows recomputed in the gate's own order
    hc = {(arm, reading): recomputed(arm, reading, host_rows) for arm in ARMS for reading in FILES}
    hst = {f"{arm}|{reading}": ({k: x for k, x in b.items() if not k.startswith("_")} if b else None)
           for (arm, reading), b in hc.items()}
    for (arm, reading), b in hc.items():
        if b:
            box = crit[arm][reading][jset]
            hst[f"{arm}|{reading}"]["largest_relative_difference_from_returned"] = max(
                [rel(b["C1_value"], box["returned_C1_value"]), rel(b["C2_value"], box["returned_C2_value"])]
                + [rel(b["per_run"][run][k], box["per_run"][run][k]) for run in runs_of(cfg, arm) for k in ("median", "p90")])
    out["statistics_from_host_order"] = hst
    hlf = hc[("label_free", judged)]
    if hlf:
        mine = own_part1(cfg["self_check"], hlf["_F"], hlf["_E"])
        out["part1_from_host_order"] = {**{k: x for k, x in mine.items() if not k.startswith("_")},
                                        "against_returned": part1_against(mine, v["self_check"])}
        for name, key, kept in (("part2_from_host_order", ("supervised_512", judged), v["comparison"]),
                                ("side_ratios_from_host_order", ("supervised_512", "raw"),
                                 v["comparison"]["supervised_raw_against_label_free_judged"]["raw"])):
            if hc[key]:
                out[name] = {**ratios(hc[key], hlf), "against_returned": ratios_against(ratios(hc[key], hlf), kept)}

    # (c) the amplitudes, (d) the runs
    amp, runs = {}, {}
    for run in runs_of(cfg):
        arm, seed = arm_seed(run)
        rd = run_dir(rec, run)
        info = json.loads((rd / "condense.json").read_text())
        amp[run] = {}
        for s in sets:
            a = [x for i in ids_of[s] for x in info["members"][i]["a"]]
            amp[run][s] = {"n": len(a), "min": float(min(a)), "max": float(max(a)), "median": float(np.median(a)),
                           "at_bound": int(sum(b for i in ids_of[s] for b in info["members"][i]["at_bound"])),
                           "at_the_lower_bound": int(sum(x <= ev["readings"]["condensed"]["a_min"] for x in a)),
                           "at_the_upper_bound": int(sum(x >= ev["readings"]["condensed"]["a_max"] for x in a)),
                           "not_converged": int(sum(not c for i in ids_of[s] for c in info["members"][i]["converged"])),
                           "median_energy_drop": float(np.median([(p - q) / p for i in ids_of[s] for p, q in
                                                                  zip(info["members"][i]["Pi_raw"], info["members"][i]["Pi_condensed"])]))}
        h = json.loads((rd / "history.json").read_text())
        at = (rd / "attempts.log").read_text().replace("\r", "").strip().split("\n")
        runs[run] = {"status": h.get("status"), "config_is_stamped": h.get("config_sha256") == sha256(cfg), "arm": h.get("arm"),
                     "seed": h.get("seed"), "torch": h.get("torch"), "gpu": h.get("gpu"), "attempts": at,
                     "reading_is_configured": info["reading"] == ev["readings"]["condensed"]
                     and info["levels_mm"] == list(cfg["data"]["eval_levels_mm"])}
        if arm == "supervised_512":
            runs[run].update({"steps": h.get("steps"), "total_steps": h.get("total_steps"), "epochs": len(h["loss"]),
                              "first_epoch_loss": float(h["loss"][0]), "mean_loss_last_ten_epochs": float(np.mean(h["loss"][-10:])),
                              "max_epoch_loss": float(max(h["loss"])), "cap_events": len(h["cap_events"]), "bursts": len(h["bursts"]),
                              "resumes": h.get("resumes"), "hours": float(sum(h["epoch_seconds"]) / 3600),
                              "reference_solutions": h.get("reference_solutions"),
                              "training_labels_sha256": h.get("training_labels_sha256"), "peak_memory_GiB": h.get("peak_memory_GiB")})
        else:
            runs[run].update({"trained_in": h.get("trained_in"), "predict_seconds": h.get("predict_seconds"),
                              "state_is_pinned": h.get("trained_in", {}).get("state_sha256") == cfg["arms"]["label_free"]["state_sha256"][seed]})
    out["amplitudes"], out["runs"] = amp, runs
    return out


def records(rec: pathlib.Path, cfg: dict) -> dict:
    out = {}
    cfg_sha = sha256(cfg)
    raw = (rec / "c23_config.json").read_bytes()
    out["configuration"] = {"returned_file_sha256": hashlib.sha256(raw).hexdigest(),
                            "returned_equals_stamped": json.loads(raw) == cfg,
                            "returned_bytes_equal_this_systems": raw == json.dumps(cfg, indent=1, sort_keys=True).encode("ascii"),
                            "stamped_sha256": cfg_sha}
    man = json.loads((rec / "manifest.json").read_text())
    box = {r["id"]: r for r in man["instances"]}
    split_all = {r["id"]: r["split"] for r in man["instances"]}
    split = sets_of(rec, cfg)
    led = json.loads((rec / "ledger.json").read_text())
    by = {e["id"]: e for e in led}
    d = cfg["data"]
    levels = {s: list(d["train_label_levels_mm"] if s == "train" else d["eval_levels_mm"]) for s in SPLITS}
    lim = d["kkt_limits"]
    worst = {k: (min if op == ">=" else max)(e["kkt_worst"][k] for e in led) for k, (op, _) in lim.items()}
    label_files = sorted(p.stem for p in (rec / "labels").glob("*.npz"))
    v = json.loads((rec / "verdict.json").read_text())

    def entries_sha(ids):                                   # as c23.data.ledger_sha256 hashes the entries of some members
        e = sorted((x for x in led if x["id"] in set(ids)), key=lambda x: x["id"])
        return hashlib.sha256(json.dumps(e, sort_keys=True).encode("ascii")).hexdigest()

    train_ids = [i for i, s in split_all.items() if s == "train"]
    out["manifest"] = {"n": man["n"], "config_is_stamped": man["config_sha256"] == cfg_sha,
                       "sha256": hashlib.sha256((rec / "manifest.json").read_bytes()).hexdigest(),
                       "by_split": {s: sum(1 for r in man["instances"] if r["split"] == s) for s in SPLITS}}
    out["ledger"] = {"entries": len(led), "members_once_each": sorted(by) == sorted(split_all) and len(by) == len(led),
                     "levels_are_configured": all(e["levels"] == levels[split_all[e["id"]]] for e in led),
                     "levels_solved": int(sum(len(e["levels"]) for e in led)),
                     "reference_solutions_of_training_members": int(sum(len(by[i]["levels"]) for i in train_ids)),
                     "all_converged": all(all(e["converged"]) for e in led),
                     "worst": worst, "limits": lim,
                     "within_limits": {k: bool(worst[k] >= x if op == ">=" else worst[k] <= x) for k, (op, x) in lim.items()},
                     "max_F_vs_F_sigma": max(e["F_vs_F_sigma"] for e in led),
                     "iterations_max": max(max(e["iterations"]) for e in led),
                     "seconds_sum": float(sum(e["seconds"] for e in led)),
                     "seconds_sum_of_training_members": float(sum(by[i]["seconds"] for i in train_ids)),
                     "solvers": sorted({e["solver"] for e in led}),
                     "first_time": min(e["time"][:19] for e in led), "last_time": max(e["time"][:19] for e in led),
                     "label_files": len(label_files), "label_files_are_the_evaluated_members": label_files == sorted(split),
                     "label_sha256_equal": int(sum(hashlib.sha256((rec / "labels" / f"{i}.npz").read_bytes()).hexdigest()
                                                   == by[i]["label_sha256"] for i in label_files)),
                     "inst_sha256_equal_manifest": int(sum(by[i]["inst_sha256"] == box[i]["sha256"] for i in by)),
                     "evaluated_entries_sha256": entries_sha(split),
                     "evaluated_entries_sha256_equals_the_verdicts": all(entries_sha(split) == v["inputs"][a]["evaluated_labels_sha256"] for a in ARMS),
                     "training_entries_sha256": entries_sha(train_ids)}
    preds = {}
    for run in runs_of(cfg):
        arm, seed = arm_seed(run)
        rd = run_dir(rec, run)
        ok, n = True, {}
        for name in ("preds.npz", "preds_condensed.npz", "preds_base.npz"):
            with np.load(rd / name) as z:
                n[name] = len(z.files)
                ok &= sorted(z.files) == sorted(split)
                for i in z.files:
                    a = z[i]
                    want = (box[i]["unknowns"],) if name == "preds_base.npz" else (len(d["eval_levels_mm"]), box[i]["unknowns"])
                    ok &= a.dtype == np.float32 and a.shape == want and bool(np.isfinite(a).all())
        preds[run] = {"members_in_each_file": n, "members_shapes_types_finite_ok": bool(ok),
                      "sha256_equal_the_verdicts": all(hashlib.sha256((rd / f).read_bytes()).hexdigest() == v["inputs"][arm]["runs"][run][f]
                                                       for f in FILES.values())}
        h = json.loads((rd / "history.json").read_text())
        text = "".join((rec / "queue" / f).read_text(errors="replace") for f in sorted(os.listdir(rec / "queue"))
                       if re.fullmatch(rf"\d+[a-z]?_c23_(train|predict)_s{seed}\.log", f)
                       and (("train" in f) == (arm == "supervised_512"))).replace("\r", "")
        if arm == "supervised_512":
            rows = re.findall(r"^epoch (\d+) loss ([\d.e+-]+) ([\d.]+) s; cap events (\d+), bursts (\d+)", text, flags=re.M)
            epochs = [int(r[0]) for r in rows]
            steps = h["total_steps"] // len(h["loss"])
            preds[run]["training_labels_sha256_is_the_ledgers"] = h.get("training_labels_sha256") == entries_sha(train_ids)
            preds[run]["log"] = {
                "epoch_lines": len(rows), "epochs_are_1_to_n": epochs == list(range(1, len(h["loss"]) + 1)),
                "losses_equal_history": all(rel(float(r[1]), x) <= 5.1e-6 for r, x in zip(rows, h["loss"])),   # six digits printed
                "seconds_equal_history": all(float(r[2]) == x for r, x in zip(rows, h["epoch_seconds"])),
                "cap_events_equal_history": all(int(r[3]) == sum(1 for c in h["cap_events"] if c[0] <= (k + 1) * steps)
                                                for k, r in enumerate(rows)),          # the history counts steps from 1
                "bursts_equal_history": all(int(r[4]) == sum(1 for c in h["bursts"] if c[0] <= (k + 1) * steps)
                                            for k, r in enumerate(rows)),
                "finished_line": '{"status": "finished", "steps": %d}' % h["total_steps"] in text}
        else:
            preds[run]["log"] = {"finished_line": json.dumps({"status": "finished", "predict_seconds": h["predict_seconds"]}) in text}
    out["predictions_and_logs"] = preds
    jobs = []
    for f in sorted(os.listdir(rec / "queue")):
        if f.endswith(".done.json"):
            dn = json.loads((rec / "queue" / f).read_text())
            jobs.append({k: dn.get(k) for k in ("name", "returncode", "killed", "started", "ended", "seconds", "cancelled",
                                                "error") if k in dn})
    gate = [j for j in jobs if "_c23_" in j["name"]]
    out["queue"] = {"commands": jobs, "commands_of_the_gate": len(gate),
                    "commands_before_the_stamp": len(jobs) - len(gate),
                    "not_zero": [j["name"] for j in jobs if j.get("returncode") != 0],
                    "killed": [j["name"] for j in jobs if j.get("killed")],
                    "cancelled": [j["name"] for j in jobs if j.get("cancelled")],
                    "in_the_order_of_their_names": [j["started"] for j in gate] == sorted(j["started"] for j in gate)}
    last = {}
    for name in ("92_c23_evaluate_label_free", "93_c23_verdict_part1", "98_c23_evaluate_supervised_512", "99_c23_verdict_final"):
        lines = (rec / "queue" / f"{name}.log").read_text(errors="replace").replace("\r", "").strip().split("\n")
        last[name] = lines[-2:]
    out["last_lines"] = last
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
    ap.add_argument("--host", default="")
    ap.add_argument("--resolve", default="")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--records", dest="records_step", action="store_true")
    ap.add_argument("--reverse", action="store_true")
    ap.add_argument("--creator", type=int, default=None)
    a = ap.parse_args()
    cfg = config()
    assert sha256(cfg) == STAMPED_CONFIG
    rec, inst, outdir = pathlib.Path(a.records), pathlib.Path(a.instances), pathlib.Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    env = environment()
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
        print(json.dumps({k: agg[k] for k in ("returned", "config_is_stamped", "rows_files",
                                              "statistics_largest_relative_difference_from_returned", "part2", "identity",
                                              "part1", "fields", "label_check", "condensed_from_parts") if k in agg}, indent=1))
        print(json.dumps({"curves": {k: agg["curves"][k] for k in ("pairs", "max_abs_diff", "seconds")},
                          "statistics_from_recomputed_curves": agg.get("statistics_from_recomputed_curves"),
                          "part1_from_recomputed_curves": agg.get("part1_from_recomputed_curves"),
                          "part2_from_recomputed_curves": agg.get("part2_from_recomputed_curves"),
                          "side_ratios_from_recomputed_curves": agg.get("side_ratios_from_recomputed_curves")}, indent=1))
        print(json.dumps({"host_order": {k: agg["host_order"][k] for k in ("members", "pairs", "max_abs_diff", "pairs_with_a_note", "seconds")},
                          "two_orders": agg["two_orders"],
                          "statistics_from_host_order": agg.get("statistics_from_host_order"),
                          "part1_from_host_order": agg.get("part1_from_host_order"),
                          "part2_from_host_order": agg.get("part2_from_host_order"),
                          "side_ratios_from_host_order": agg.get("side_ratios_from_host_order")}, indent=1))
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
        jobs = [(str(rec), str(inst), str(outdir), iid, runs_of(cfg)) for iid in ids]
        work = fields_member
    elif a.host:
        assert a.host in ARMS
        ev = cfg["evaluation"]
        readings = [ev["readings"]["judged"]] + list(ev["readings"]["reported"])     # the stamped loading order
        write_json(outdir / f"environment_host_{a.host}.json", env)
        ids = [i for i in a.ids.split(",") if i] or [i for i in sorted(split) if split[i] == ev["judged_set"]]
        jobs = [(str(rec), str(inst), str(outdir), a.host, iid, runs_of(cfg, a.host), readings)
                for iid in sorted(ids, reverse=a.reverse) if not host_file(outdir, a.host, iid).exists()]
        work = host_member
    elif a.curves:
        write_json(outdir / "environment_curves.json", env)
        pairs = json.loads((outdir / f"pairs_{a.curves}.json").read_text())["pairs"]
        by = {}
        for iid, run, reading, l in pairs:
            by.setdefault(iid, []).append((run, reading, l))
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
        with C23D.pool(a.workers) as p:
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
