"""cmame-paper Stage 14 (RUNBOOK_CMAME Sec. G): scripts/ritz_baseline.py,
scripts/enriched_cstar.py and scripts/ritz_timing.py end to end, on a
miniature box shaped like the real one: a 3D gmsh corpus with its seeded
split and labelled validation instances, a 3D fine set, a 2D corpus of gmsh
plates, PREREG_HOLDOUT-style holdout sets labelled by its own code, three
wp9-style 2D sets with per-file SHA-256 in their manifests; random-weight
transformer and graph-network states for the seeds of each run; reports with
every row's per-instance arrays computed as the runs computed them (and the
wp9 reports' amplitude records), the identity records (amp, spectra,
PREREG_HOLDOUT's arrays) and a configuration naming them all.

Checked: every input verified (the check modes print one line per set or
arm); the baseline on every set (one with two worker processes, equal to one
process), the identity on every instance, the ladder never worse with p,
the summaries and pairings recomputed from the rows and the records, a run
cut off and resumed equal to one run, a summary rebuilt from the rows alone;
a changed report, corpus manifest, labels file or wp9 file refused before
anything is computed, an instance that is not the recorded one written and
listed with exit 4; the enriched reading on every arm, its bound, its
precheck (a perturbed record stops the run with exit 5 before anything is
written), its Ritz rows equal to the baseline's at the same degree, its
reading recomputed from the summaries; a changed state refused; the timing
of the cost-table row with the assembly apart."""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("torch")

ROOT = Path(__file__).resolve().parents[1]
ENV = {"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin:/usr/local/bin"}
BASE = ROOT / "scripts" / "ritz_baseline.py"
ENR = ROOT / "scripts" / "enriched_cstar.py"
TIM = ROOT / "scripts" / "ritz_timing.py"
FIELDS = ("disp_rel_l2", "energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err", "crit_recall")
N_VAL, USED, POOL = 3, 2, 4
MODEL2 = {"dim": 16, "depth": 1, "heads": 2, "mgn_dim": 8, "mgn_depth": 1,
          "features": {"load_summary": True, "geometry": True}}
MODEL3 = dict(MODEL2, features=dict(MODEL2["features"], spatial_dim=3))
SPEC = {"fixed": "20 October 2026", "cut": 1e-13, "ladder": {"3": [6, 7, 8, 9], "2": [6, 8]},
        "id_tol": 1e-06, "enriched_degree": {"2": 6, "3": 8}, "enriched_cut": 1e-12,
        "inband_factor": 0.8, "ood_peak_factor": 0.5}


def _sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _run(script, *args, cwd=None):
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True,
                          text=True, env=ENV, cwd=cwd)


def _write(path: Path, obj) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj))
    return _sha(path)


# ---------------------------------------------------------------- corpora --

def _label(arch):
    from fejepa.fe.solve import solve_fe_displacement

    U, _ = solve_fe_displacement(arch.K, arch.F, np.asarray(arch.free_mask, bool),
                                 method="direct")
    return U


def _label_val(corpus: Path) -> None:
    from fejepa.data.archive import add_labels, load_instance, mark_labelled
    from fejepa.experiments.protocol import load_split

    sp = load_split(str(corpus), N_VAL, seed=1)
    for f in sp.val_files:
        add_labels(f, _label(load_instance(f)))
    mark_labelled(corpus, {Path(f).name for f in sp.val_files})


def _corpus_3d(out: Path, n: int, seed: int, label: str) -> Path:
    """A gmsh3d corpus (about 300 nodes per instance: enough distinct
    coordinates for degree 8, as on the real meshes, so that no direction is
    dropped near the cut)."""
    from fejepa.data.archive import add_labels, instance_files, load_instance
    from fejepa.fe.gmsh3d import generate_gmsh3d_dataset

    generate_gmsh3d_dataset(out, n=n, seed=seed, lc=0.3)
    if label == "val":
        _label_val(out)
    else:
        for f in instance_files(out):
            add_labels(f, _label(load_instance(f)))
    return out


def _corpus_2d(out: Path, n: int) -> Path:
    from fejepa.data.archive import save_instance, write_manifest
    from fejepa.fe.elasticity import LOAD_NAMES
    from fejepa.fe.generator import build_instance, sample_params

    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(4)
    recs = []
    for i in range(n):
        params = sample_params(rng)
        params["target_h"] = 0.25
        arch = build_instance(params)
        fn = f"instance_{i:05d}.npz"
        save_instance(arch, out / fn)
        recs.append({"file": fn, "n_nodes": arch.n_nodes,
                     "n_holes": arch.meta["extra"]["n_holes"], "labelled": False})
    write_manifest(out, recs, {"backend": "gmsh", "seed": 4, "labelled_policy": "none",
                               "load_names": LOAD_NAMES})
    _label_val(out)
    return out


def _w9_set(out: Path, name: str, n: int, seed: int) -> dict:
    """A wp9-style evaluation set: labelled plates, a manifest whose records
    carry each file's SHA-256 (fejepa.fe.ood2d's record)."""
    from fejepa.data.archive import manifest_sha256, save_instance, write_manifest
    from fejepa.fe.generator import sample_params
    from fejepa.fe.ood2d import _record, labelled_instance

    out.mkdir(parents=True, exist_ok=True)
    recs = []
    for i, child in enumerate(np.random.SeedSequence(seed).spawn(n)):
        params = dict(sample_params(np.random.default_rng(child)), family=name)
        params["target_h"] = 0.25
        arch = labelled_instance(params)
        path = out / f"instance_{i:05d}.npz"
        save_instance(arch, path)
        recs.append(_record(path, arch, params))
    write_manifest(out, recs, {"backend": "gmsh", "family": name, "seed": seed,
                               "labelled_policy": "all"})
    return {"dir": str(out), "family": name, "seed": seed, "n_instances": n,
            "manifest_sha256": manifest_sha256(out)}


# ------------------------------------------------------------ models, records --

def _save(kind: str, model: dict, seed: int, path: Path) -> str:
    import torch

    from fejepa.experiments.parallel import _build_model

    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(_build_model({"kind": kind, "model": model, "seed": seed}).state_dict(), path)
    return _sha(path)


def _predict(kind: str, model: dict, state: Path, seed: int, arch) -> np.ndarray:
    import torch

    from fejepa.analysis.common import build_model_from_config

    m = build_model_from_config(dict(model, kind=kind), state_path=str(state), seed=seed)
    with torch.no_grad():
        return m.forward_instance(m.prepare_instance(arch, "cpu")).detach().cpu().numpy()


def _evals(kind, model, states: dict, archs: list, amplitude=False) -> list:
    """per_seed_eval entries (in the states' seed order) as the runs record them."""
    from fejepa.analysis.posthoc import amplitude_factor, energy_norms
    from fejepa.metrics import evaluate_fields

    out = []
    for s, p in states.items():
        per = {k: [] for k in FIELDS}
        amp = {"c_star": [], "u_norm_K": [], "ustar_norm_K": []}
        for a in archs:
            U = _predict(kind, model, p, s, a)
            v = evaluate_fields(U, a)
            for k in FIELDS:
                per[k].append(float(v[k]))
            free = np.asarray(a.free_mask, bool)
            amp["c_star"].append(amplitude_factor(U, a.K, a.F, free).tolist())
            amp["u_norm_K"].append(energy_norms(U, a.K, free).tolist())
            amp["ustar_norm_K"].append(energy_norms(a.U_star, a.K, free).tolist())
        e = {**{k: float(np.mean(v)) for k, v in per.items()}, "per_instance": per}
        if amplitude:
            e["amplitude"] = {"per_instance": amp}
        out.append(e)
    return out


def _det(archs: list) -> list:
    """A deterministic row (the zero field) as one per_seed_eval entry."""
    from fejepa.metrics import evaluate_fields

    per = {k: [] for k in FIELDS}
    for a in archs:
        v = evaluate_fields(np.zeros_like(a.U_star), a)
        for k in FIELDS:
            per[k].append(float(v[k]))
    return [{"per_instance": per}]


def _states(tmp: Path, d: str, pattern: str, kind: str, model: dict, seeds, base: int) -> dict:
    out = {}
    for s in seeds:
        p = tmp / d / pattern.format(seed=s)
        _save(kind, model, base + s, p)
        out[int(s)] = p
    return out


def _holdout_spec(tmp: Path, c3: Path, c2: Path) -> tuple:
    from fejepa.analysis.holdout import label_set, load_spec
    from fejepa.data.archive import manifest_sha256

    from fejepa.analysis.holdout import ROWS

    def sdef(name, corpus, n):
        return {"corpus": str(corpus), "manifest_sha256": manifest_sha256(corpus),
                "n_corpus": n, "split": {"n_val": N_VAL, "seed": 1}, "used_prefix": USED,
                "excluded": [], "n_holdout": n - N_VAL - USED, "report": "unused",
                "report_sha256": "0" * 64,
                "rows": {r: {"state": "unused", "cell": "4", "kind": "fejepa",
                             "sha256": {str(s): "0" * 64 for s in (0, 1, 2)},
                             "sha256_source": "test"} for r in ROWS[name]}}

    spec = {"_comment": "test", "prereg_file": "unused", "seeds": [0, 1, 2],
            "out": str(tmp / "runs" / "holdout"),
            "labels": {"method": "direct", "stage": "holdout-labels", "residual_max": 1e-8},
            "content_tol": 1e-3, "sets": {"h3d": sdef("h3d", c3, 9), "h2d": sdef("h2d", c2, 9)},
            "criteria": {"guard_band": 0.1, "guard_k": 2.0, "most": 0.5, "almost_all": 0.95,
                         "halved": -0.5, "representative_alpha": 0.05}}
    sp = tmp / "configs" / "holdout_v1.json"
    _write(sp, spec)
    spec = load_spec(sp)
    for name, s in spec["sets"].items():
        label_set(name, s, tmp / "runs" / "holdout" / name, log=lambda *a: None)
    return sp, spec


def _holdout_archs(spec: dict, name: str) -> list:
    from fejepa.analysis.holdout import holdout_instances

    return list(holdout_instances(name, spec["sets"][name], Path(spec["out"]) / name))


def build_miniature(tmp: Path) -> dict:
    """The miniature box's inputs and its configuration (tmp/configs/ritz_v1.json);
    nothing run yet."""
    from fejepa.analysis.posthoc import run_files
    from fejepa.anchor.energy import pi_h
    from fejepa.data.archive import load_instance, manifest_sha256
    from fejepa.report import config_sha256

    runs = tmp / "runs"
    c3 = _corpus_3d(runs / "data3d_phase2", 9, 5, "val")
    f3 = _corpus_3d(runs / "data3d_phase2_fine", 4, 6, "all")
    c2 = _corpus_2d(runs / "data2d", 9)
    hspec_path, hspec = _holdout_spec(tmp, c3, c2)
    rec = tmp / "records"
    seeds = (0, 1, 2)

    # Phase-2b-like 3D run: ar (d9 record), labels and mgn (listed), its report
    ar3 = _states(tmp, "runs/phase2/e8_states", f"ar_p{POOL}_s{{seed}}.pt", "fejepa", MODEL3,
                  seeds, 0)
    lab3 = _states(tmp, "runs/phase2/e8_states", "labels_b4_s{seed}.pt", "fejepa", MODEL3,
                   seeds, 10)
    mgn3 = _states(tmp, "runs/phase2/e8_states", "mgn_b4_s{seed}.pt", "mgn", MODEL3, seeds, 20)
    lk3 = _states(tmp, "runs/k3d", "labels_knorm_b4_s{seed}.pt", "fejepa", MODEL3, seeds, 30)
    cfg3 = {"model": MODEL3, "tf32": False, "split": {"n_val": N_VAL, "seed": 1},
            "data": {"dir": str(c3)}, "experiments": {"e8": {"pool_sizes": [POOL]}},
            "data_transfer": {"dir": str(f3), "n": 4, "seed": 0, "lc": 0.0374,
                              "split": {"n_eval": 3, "n_fewshot_prefix": 1}}}
    rep3 = {"config": cfg3,
            "provenance": {"config_sha256": config_sha256(cfg3), "seeds": list(seeds),
                           "datasets": [{"dir": str(c3), "manifest_sha256": manifest_sha256(c3)},
                                        {"dir": str(f3),
                                         "manifest_sha256": manifest_sha256(f3)}]},
            "results": {"e8": {"metrics": {
                "cells": {}, "d9_restart": {"ar_states": {f"s{s}": {"sha256": _sha(p)}
                                                          for s, p in ar3.items()}}}}}}
    val3 = [load_instance(f) for f in run_files(rep3, "val")]
    fine3 = [load_instance(f) for f in run_files(rep3, "fine")]
    cells = rep3["results"]["e8"]["metrics"]["cells"]
    cells["ar"] = {str(POOL): {"per_seed_eval": _evals("fejepa", MODEL3, ar3, val3)}}
    cells["labels"] = {str(POOL): {"per_seed_eval": _evals("fejepa", MODEL3, lab3, val3)}}
    cells["mgn"] = {str(POOL): {"per_seed_eval": _evals("mgn", MODEL3, mgn3, val3)}}
    cells["zero"] = {str(POOL): {"per_seed_eval": _det(val3)}}
    rep3["results"]["p3_transfer"] = {"metrics": {
        "ar": {"fine": {"per_seed_eval": _evals("fejepa", MODEL3, ar3, fine3)}},
        "zero_shot_reported": {
            "labels@max": {"fine": {"per_seed_eval": _evals("fejepa", MODEL3, lab3, fine3)}},
            "mgn@max": {"fine": {"per_seed_eval": _evals("mgn", MODEL3, mgn3, fine3)}}},
        "naive_rows": {"zero_field": {"per_seed_eval": _det(fine3)}}, "fewshot": {}}}
    p_rep3 = rec / "report_phase2b.json"
    s_rep3 = _write(p_rep3, rep3)
    from fejepa.analysis.posthoc import energy_norms

    def amp_rows(archs, pse):
        """posthoc_amplitude's per-instance rows of one seed: the instance, its
        ||U*||_K and the seed's own displacement error and energy gap."""
        return {"per_instance": [{"file": Path(str(a.path)).name, "n_nodes": int(a.n_nodes),
                                  "ustar_norm_K": energy_norms(a.U_star, a.K, np.asarray(
                                      a.free_mask, bool)).tolist(),
                                  "disp": pse["per_instance"]["disp_rel_l2"][i],
                                  "egap": pse["per_instance"]["energy_gap_rel"][i]}
                                 for i, a in enumerate(archs)]}

    p_amp = rec / "amp_phase2b.json"
    fine_ar = rep3["results"]["p3_transfer"]["metrics"]["ar"]["fine"]["per_seed_eval"]
    s_amp = _write(p_amp, {"seeds": {f"s{s}": {
        "inband": amp_rows(val3, cells["ar"][str(POOL)]["per_seed_eval"][k]),
        "fine": amp_rows(fine3, fine_ar[k])} for k, s in enumerate(seeds)}})
    k3 = {"config": {"source": {"report": str(p_rep3), "report_sha256": s_rep3}},
          "provenance": {"seeds": list(seeds), "datasets": [rep3["provenance"]["datasets"][0]]},
          "seeds": list(seeds),
          "cells": {"ar": cells["ar"],
                    "labels_knorm": {str(POOL): {"per_seed_eval": _evals("fejepa", MODEL3, lk3,
                                                                         val3)}}}}
    p_k3 = rec / "k3d_report.json"
    s_k3 = _write(p_k3, k3)

    # CM2D-like 2D run and a second report with the same deterministic row
    ar2 = _states(tmp, "runs/e1_2d_base/e8_states", f"ar_p{POOL}_s{{seed}}.pt", "fejepa",
                  MODEL2, seeds, 40)
    cfg2 = {"model": MODEL2, "tf32": False, "split": {"n_val": N_VAL, "seed": 1},
            "data": {"dir": str(c2)}, "experiments": {"e8": {"pool_sizes": [POOL]}}}
    rep2 = {"config": cfg2,
            "provenance": {"config_sha256": config_sha256(cfg2), "seeds": list(seeds),
                           "datasets": [{"dir": str(c2), "manifest_sha256": manifest_sha256(c2)}]},
            "results": {"e8": {"metrics": {"cells": {}, "d9_restart": {"ar_states": {
                f"s{s}": {"sha256": _sha(p)} for s, p in ar2.items()}}}}}}
    val2 = [load_instance(f) for f in run_files(rep2, "val")]
    rep2["results"]["e8"]["metrics"]["cells"] = {
        "ar": {str(POOL): {"per_seed_eval": _evals("fejepa", MODEL2, ar2, val2)}},
        "zero": {str(POOL): {"per_seed_eval": _det(val2)}}}
    p_rep2 = rec / "report_cm2d.json"
    s_rep2 = _write(p_rep2, rep2)
    p_rep2b = rec / "report_july.json"
    rep2b = json.loads(json.dumps(rep2))
    del rep2b["results"]["e8"]["metrics"]["cells"]["ar"]
    s_rep2b = _write(p_rep2b, rep2b)
    p_spec = rec / "spectra_val.npz"
    Kn = [(a.U_star[:, np.asarray(a.free_mask, bool)], a) for a in val2]
    np.savez(p_spec, files=np.array([Path(str(a.path)).name for a in val2]),
             n_free=np.array([int(np.count_nonzero(a.free_mask)) for a in val2]),
             uK_star=np.array([energy_norms(a.U_star, a.K, np.asarray(a.free_mask, bool)) ** 2
                               for _, a in Kn]))
    s_spec = _sha(p_spec)

    # PREREG_HOLDOUT-like arrays (R1's and K3D's) and the returned manifests
    hold = {}
    for name, (rows, kind_of, sts, model) in {
            "h3d": (("ar", "labels"), {"ar": "fejepa", "labels": "fejepa"},
                    {"ar": ar3, "labels": lab3}, MODEL3),
            "h2d": (("ar",), {"ar": "fejepa"}, {"ar": ar2}, MODEL2)}.items():
        archs = _holdout_archs(hspec, name)
        vals = np.array([[[[e["per_instance"][k][i] for k in FIELDS]
                           for i in range(len(archs))]
                          for e in _evals(kind_of[r], model, sts[r], archs)] for r in rows])
        pi = np.array([pi_h(a.U_star, a.K, a.F) for a in archs])
        files = np.array([Path(str(a.path)).name for a in archs])
        p = rec / "holdout" / name / "eval_arrays.npz"
        p.parent.mkdir(parents=True, exist_ok=True)
        np.savez(p, rows=np.array(rows), seeds=np.array(seeds), metrics=np.array(FIELDS),
                 files=files, values=vals, pi_star=pi)
        man = Path(hspec["out"]) / name / "manifest.json"
        shutil.copy(man, rec / "holdout" / name / "manifest.json")
        hold[name] = {"arrays": str(p), "arrays_sha256": _sha(p), "manifest": str(
            rec / "holdout" / name / "manifest.json"), "manifest_sha256": _sha(man),
            "archs": archs}
    lkv = _evals("fejepa", MODEL3, lk3, hold["h3d"]["archs"])
    vk = np.array([[[[e["per_instance"][k][i] for k in FIELDS]
                     for i in range(len(hold["h3d"]["archs"]))] for e in lkv]])
    p_k3h = rec / "k3d_holdout_arrays.npz"
    np.savez(p_k3h, rows=np.array(["labels_knorm"]), seeds=np.array(seeds),
             metrics=np.array(FIELDS),
             files=np.array([Path(str(a.path)).name for a in hold["h3d"]["archs"]]), values=vk)

    # wp9-like 2D runs b and s, their sets and reports
    w9sets = {"IB": _w9_set(runs / "w9" / "ood2d" / "IB", "IB", 3, 91007),
              "F2": _w9_set(runs / "w9" / "ood2d" / "F2", "F2", 2, 91002),
              "F5": _w9_set(runs / "w9" / "ood2d" / "F5", "F5", 2, 91005)}
    w9 = {}
    for k, arm in enumerate(("b_n1024", "s_n1024")):
        st = _states(tmp, f"runs/w9/{arm}/e8_states", f"ar_p{POOL}_s{{seed}}.pt", "fejepa",
                     MODEL2, (3, 4, 5), 50 + 10 * k)
        cfgw = dict(cfg2)
        rep = {"config": cfgw,
               "provenance": {"config_sha256": config_sha256(cfgw), "seeds": [3, 4, 5],
                              "datasets": rep2["provenance"]["datasets"]},
               "evaluation": {"holdouts": w9sets},
               "results": {"e8": {"metrics": {
                   "d9_restart": {"ar_states": {f"s{s}": {"sha256": _sha(p)}
                                                for s, p in st.items()}},
                   "holdouts": {}}}}}
        for name, h in w9sets.items():
            from fejepa.data.archive import instance_files

            archs = [load_instance(f) for f in instance_files(Path(h["dir"]))]
            rep["results"]["e8"]["metrics"]["holdouts"][name] = {str(POOL): {
                "per_seed_eval": _evals("fejepa", MODEL2, st, archs, amplitude=True)}}
        p = runs / "w9" / arm / "report.json"
        w9[arm] = {"report": str(p), "report_sha256": _write(p, rep)}

    cfg = {
        "_comment": "test", "spec": SPEC, "out": str(runs / "ritz"),
        "baseline": {"workers": 1, "worker_threads": 1, "sets": {
            "val3d": {"dim": 3, "kind": "run", "which": "val", "n": N_VAL,
                      "report": str(p_rep3), "report_sha256": s_rep3,
                      "identity": {"kind": "amp", "part": "inband", "path": str(p_amp),
                                   "sha256": s_amp, "order": f"cells:ar:{POOL}"},
                      "paired": [{"tag": "phase2b", "kind": "cells", "path": str(p_rep3),
                                  "sha256": s_rep3},
                                 {"tag": "k3d", "kind": "cells", "path": str(p_k3),
                                  "sha256": s_k3, "rows": ["labels_knorm"], "order_row": "ar"}]},
            "fine3d": {"dim": 3, "kind": "run", "which": "fine", "n": 3,
                       "report": str(p_rep3), "report_sha256": s_rep3,
                       "identity": {"kind": "amp", "part": "fine", "path": str(p_amp),
                                    "sha256": s_amp, "order": "p3:ar"},
                       "paired": [{"tag": "phase2b", "kind": "p3", "path": str(p_rep3),
                                   "sha256": s_rep3}]},
            "h3d": {"dim": 3, "kind": "holdout", "set": "h3d", "n": 4, "spec": str(hspec_path),
                    "spec_sha256": _sha(hspec_path), "labels_dir": str(runs / "holdout" / "h3d"),
                    "labels_manifest_sha256": hold["h3d"]["manifest_sha256"],
                    "identity": {"kind": "pi_star", "path": hold["h3d"]["arrays"],
                                 "sha256": hold["h3d"]["arrays_sha256"],
                                 "manifest": hold["h3d"]["manifest"]},
                    "paired": [{"tag": "r1", "kind": "arrays", "path": hold["h3d"]["arrays"],
                                "sha256": hold["h3d"]["arrays_sha256"]},
                               {"tag": "k3d", "kind": "arrays", "path": str(p_k3h),
                                "sha256": _sha(p_k3h), "rows": ["labels_knorm"]}]},
            "val2d": {"dim": 2, "kind": "run", "which": "val", "n": N_VAL,
                      "report": str(p_rep2), "report_sha256": s_rep2,
                      "identity": {"kind": "spectra", "path": str(p_spec), "sha256": s_spec},
                      "paired": [{"tag": "cm2d", "kind": "cells", "path": str(p_rep2),
                                  "sha256": s_rep2},
                                 {"tag": "july", "kind": "cells", "path": str(p_rep2b),
                                  "sha256": s_rep2b}],
                      "not_paired": "test"},
            "h2d": {"dim": 2, "kind": "holdout", "set": "h2d", "n": 4, "spec": str(hspec_path),
                    "spec_sha256": _sha(hspec_path), "labels_dir": str(runs / "holdout" / "h2d"),
                    "labels_manifest_sha256": hold["h2d"]["manifest_sha256"],
                    "identity": {"kind": "pi_star", "path": hold["h2d"]["arrays"],
                                 "sha256": hold["h2d"]["arrays_sha256"],
                                 "manifest": hold["h2d"]["manifest"]},
                    "paired": [{"tag": "r1", "kind": "arrays", "path": hold["h2d"]["arrays"],
                                "sha256": hold["h2d"]["arrays_sha256"]}]}}},
        "enriched": {
            "workers": 1, "worker_threads": 1, "content_tol": 1e-3, "precheck_n": 2,
            "sets": {"IB": {"dim": 2, "kind": "w9", "inband": True, "n": 3},
                     "F2": {"dim": 2, "kind": "w9", "inband": False, "n": 2},
                     "F5": {"dim": 2, "kind": "w9", "inband": False, "n": 2},
                     "val3d": {"dim": 3, "kind": "run", "which": "val", "inband": True,
                               "n": N_VAL, "identity": {"kind": "amp", "part": "inband",
                                                        "path": str(p_amp), "sha256": s_amp}},
                     "fine3d": {"dim": 3, "kind": "run", "which": "fine", "inband": False,
                                "n": 3, "identity": {"kind": "amp", "part": "fine",
                                                     "path": str(p_amp), "sha256": s_amp}}},
            "arms": {
                **{arm: {"dim": 2, "appendix": True, "row": "ar", "kind": "fejepa",
                         "report": w9[arm]["report"], "report_sha256": w9[arm]["report_sha256"],
                         "report_source": "test",
                         "states": {"from": "d9", "dir": str(runs / "w9" / arm / "e8_states")},
                         "sets": ["IB", "F2", "F5"],
                         "records": {n: f"holdouts:{n}:{POOL}" for n in ("IB", "F2", "F5")}}
                   for arm in ("b_n1024", "s_n1024")},
                "phase2b": {"dim": 3, "appendix": True, "row": "ar", "kind": "fejepa",
                            "report": str(p_rep3), "report_sha256": s_rep3,
                            "states": {"from": "d9", "dir": str(runs / "phase2" / "e8_states")},
                            "sets": ["val3d", "fine3d"],
                            "records": {"val3d": f"cells:ar:{POOL}", "fine3d": "p3:ar"}},
                "phase2b_labels": {"dim": 3, "appendix": False, "row": "labels",
                                   "kind": "fejepa", "report": str(p_rep3),
                                   "report_sha256": s_rep3,
                                   "states": {"from": "list", "pattern": str(
                                       runs / "phase2" / "e8_states" / "labels_b4_s{seed}.pt"),
                                       "sha256": {str(s): _sha(p) for s, p in lab3.items()},
                                       "sha256_source": "test"},
                                   "sets": ["val3d", "fine3d"],
                                   "records": {"val3d": f"cells:labels:{POOL}",
                                               "fine3d": "p3:labels@max"}},
                "phase2b_mgn": {"dim": 3, "appendix": False, "row": "mgn", "kind": "mgn",
                                "report": str(p_rep3), "report_sha256": s_rep3,
                                "states": {"from": "list", "pattern": str(
                                    runs / "phase2" / "e8_states" / "mgn_b4_s{seed}.pt"),
                                    "sha256": {str(s): _sha(p) for s, p in mgn3.items()},
                                    "sha256_source": "test"},
                                "sets": ["val3d", "fine3d"],
                                "records": {"val3d": f"cells:mgn:{POOL}",
                                            "fine3d": "p3:mgn@max"}},
                "k3d_labels_knorm": {"dim": 3, "appendix": False, "row": "labels_knorm",
                                     "kind": "fejepa", "report": str(p_rep3),
                                     "report_sha256": s_rep3,
                                     "states": {"from": "list", "pattern": str(
                                         runs / "k3d" / "labels_knorm_b4_s{seed}.pt"),
                                         "sha256": {str(s): _sha(p) for s, p in lk3.items()},
                                         "sha256_source": "test"},
                                     "sets": ["val3d", "fine3d"],
                                     "records": {"val3d": f"k3d:cells:labels_knorm:{POOL}"},
                                     "records_report": str(p_k3),
                                     "records_report_sha256": s_k3}}},
        "timing": {"3d": {"report": str(p_rep3), "report_sha256": s_rep3, "n_val": 2,
                          "n_fine": 1, "warmup": 1},
                   "2d": {"report": str(p_rep2), "report_sha256": s_rep2, "n_val": 2,
                          "n_fine": 0, "warmup": 1}}}
    cp = tmp / "configs" / "ritz_v1.json"
    _write(cp, cfg)
    return {"tmp": tmp, "cfg_path": cp, "cfg": cfg, "hspec": hspec, "val3": val3,
            "fine3": fine3, "val2": val2, "hold": hold, "w9sets": w9sets,
            "reports": {"phase2b": p_rep3, "cm2d": p_rep2}}


@pytest.fixture(scope="module")
def box(tmp_path_factory):
    pytest.importorskip("gmsh")
    pytest.importorskip("skfem")
    m = build_miniature(tmp_path_factory.mktemp("ritzbox"))
    tmp, cp, cfg = m["tmp"], m["cfg_path"], m["cfg"]
    logs = {}
    for s in ("val3d", "fine3d", "h3d", "val2d", "h2d"):
        r = _run(BASE, "--config", cp, "--set", s, cwd=tmp)
        assert r.returncode == 0, (s, r.stdout[-3000:], r.stderr[-3000:])
        logs[f"ritz_{s}"] = r.stdout
    for arm in cfg["enriched"]["arms"]:
        r = _run(ENR, "--config", cp, "--arm", arm, "--device", "cpu", cwd=tmp)
        assert r.returncode == 0, (arm, r.stdout[-3000:], r.stderr[-3000:])
        logs[f"enriched_{arm}"] = r.stdout
    return dict(m, logs=logs)


def _rows(box, *parts) -> list:
    from fejepa.analysis.ritz import complete_lines

    return complete_lines(Path(box["cfg"]["out"]).joinpath(*parts) / "rows.jsonl")


def _summary(box, *parts) -> dict:
    return json.loads((Path(box["cfg"]["out"]).joinpath(*parts) / "summary.json").read_text())


def _strip_t(rows: list) -> list:
    return [{k: v for k, v in r.items() if k != "t"} for r in rows]


def _close(a, b, rtol=1e-8, atol=1e-12, where="") -> None:
    """Equal structures, floats to round-off (other BLAS thread counts in
    the workers round differently), everything else exactly."""
    if isinstance(a, dict):
        assert isinstance(b, dict) and sorted(a) == sorted(b), where
        for k in a:
            _close(a[k], b[k], rtol, atol, f"{where}.{k}")
    elif isinstance(a, list):
        assert isinstance(b, list) and len(a) == len(b), where
        for i, (x, y) in enumerate(zip(a, b)):
            _close(x, y, rtol, atol, f"{where}[{i}]")
    elif isinstance(a, float) or isinstance(b, float):
        assert np.isclose(a, b, rtol=rtol, atol=atol), (where, a, b)
    else:
        assert a == b, (where, a, b)


def _cfg_copy(box, tmp: Path, edit) -> Path:
    cfg = json.loads(box["cfg_path"].read_text())
    cfg["out"] = str(tmp / "out")
    edit(cfg)
    p = tmp / "ritz_v1.json"
    p.write_text(json.dumps(cfg))
    return p


# ------------------------------------------------------------------- tests --

def test_the_check_modes_verify_every_input(box):
    r = _run(BASE, "--config", box["cfg_path"], "--set", "all", "--check", cwd=box["tmp"])
    assert r.returncode == 0, r.stdout + r.stderr
    lines = [json.loads(x) for x in r.stdout.splitlines()]
    assert [x["set"] for x in lines] == ["val3d", "fine3d", "h3d", "val2d", "h2d"]
    assert [x["n"] for x in lines] == [3, 3, 4, 3, 4]
    r = _run(ENR, "--config", box["cfg_path"], "--arm", "all", "--check", cwd=box["tmp"])
    assert r.returncode == 0, r.stdout + r.stderr
    lines = [json.loads(x) for x in r.stdout.splitlines()]
    assert [x["arm"] for x in lines] == list(box["cfg"]["enriched"]["arms"])
    assert lines[0] == {"arm": "b_n1024", "seeds": [3, 4, 5], "states_verified": 3,
                        "sets": {"IB": 3, "F2": 2, "F5": 2}}
    assert all(x["states_verified"] == 3 for x in lines)


def test_the_baseline_rows_and_summaries(box):
    from fejepa.analysis import ritz as R

    for s, n in (("val3d", 3), ("fine3d", 3), ("h3d", 4), ("val2d", 3), ("h2d", 4)):
        rows = _rows(box, "baseline", s)
        summ = _summary(box, "baseline", s)
        d = box["cfg"]["baseline"]["sets"][s]["dim"]
        assert len(rows) == n == summ["n"] == summ["n_used"] and summ["identity_failed"] == []
        assert summ["identity_max_rel_diff"] < 1e-9
        assert summ["rows_sha256"] == _sha(Path(box["cfg"]["out"]) / "baseline" / s /
                                           "rows.jsonl")
        assert [r["i"] for r in rows] == list(range(n))
        for r in rows:
            assert r["identity"]["ok"] and r["identity"]["size_ok"]
            assert list(r["ritz"]) == [str(p) for p in R.LADDER[d]]
            g = [r["ritz"][p]["mean"]["energy_gap_rel"] for p in r["ritz"]]
            assert all(b <= a + 1e-10 for a, b in zip(g, g[1:]))
            for p, e in r["ritz"].items():
                assert e["k"] == R.n_unknowns(d, int(p))
                assert e["worse_than_zero"]["sign_mismatch"] == 0
                assert np.isclose(e["mean"]["energy_gap_rel"],
                                  np.mean(e["load"]["energy_gap_rel"]))
        for p, e in summ["ladder"].items():
            vals = [r["ritz"][p]["mean"]["energy_gap_rel"] for r in rows]
            assert np.isclose(e["median"]["energy_gap_rel"], np.median(vals))
            assert e["k"] == R.n_unknowns(d, int(p))
        line = json.loads(box["logs"][f"ritz_{s}"].strip().splitlines()[-1])
        assert line["set"] == s and line["n"] == n and line["identity_failed"] == 0
    # the pairing recomputed from the rows and the records
    rows = _rows(box, "baseline", "h3d")
    summ = _summary(box, "baseline", "h3d")
    with np.load(box["hold"]["h3d"]["arrays"]) as z:
        ref = z["values"][0, 1, :, 1]                       # ar, seed 1, energy gap
    mine = np.array([r["ritz"]["8"]["mean"]["energy_gap_rel"] for r in rows])
    q = summ["ladder"]["8"]["paired"]["r1:ar"][1]
    assert q["seed"] == "s1" and np.isclose(q["energy_gap_rel"]["ritz_better_share"],
                                            np.mean(mine < ref))
    assert set(summ["ladder"]["6"]["paired"]) == {"r1:ar", "r1:labels", "k3d:labels_knorm"}
    v3 = _summary(box, "baseline", "val3d")
    assert set(v3["ladder"]["9"]["paired"]) == {"phase2b:ar@4", "phase2b:labels@4",
                                                "phase2b:mgn@4", "phase2b:zero@4",
                                                "k3d:labels_knorm@4"}
    assert v3["record_checks"] == {
        "identity_order": {"against": f"cells:ar:{POOL}", "seeds": [0, 1, 2],
                           "max_rel_diff": 0.0},
        "k3d:order_row:ar": {"max_rel_diff": 0.0}}
    assert _summary(box, "baseline", "fine3d")["record_checks"] == {
        "identity_order": {"against": "p3:ar", "seeds": [0, 1, 2], "max_rel_diff": 0.0}}
    v2 = _summary(box, "baseline", "val2d")
    assert v2["record_checks"]["zero@4"]["reports"] == ["cm2d", "july"]
    assert v2["not_paired"] == "test"
    f3 = _summary(box, "baseline", "fine3d")
    assert set(f3["ladder"]["6"]["paired"]) == {"phase2b:ar (zero-shot)",
                                                "phase2b:labels@max (zero-shot)",
                                                "phase2b:mgn@max (zero-shot)",
                                                "phase2b:zero_field"}
    zero = f3["ladder"]["6"]["paired"]["phase2b:zero_field"][0]
    assert zero["seed"] == "det" and zero["energy_gap_rel"]["ritz_better_share"] == 1.0


def test_workers_resume_and_resummarise_change_nothing(box, tmp_path):
    cp = _cfg_copy(box, tmp_path, lambda c: None)
    r = _run(BASE, "--config", cp, "--set", "h2d", "--workers", "2", "--worker-threads", "1",
             "--limit", "2", cwd=box["tmp"])
    assert r.returncode == 0, r.stdout + r.stderr
    out = tmp_path / "out" / "baseline" / "h2d"
    assert "no summary yet" in r.stdout and not (out / "summary.json").exists()
    with open(out / "rows.jsonl", "a") as fh:                   # a line cut by a kill
        fh.write('{"i": 2, "file": "cut')
    r = _run(BASE, "--config", cp, "--set", "h2d", "--workers", "2", cwd=box["tmp"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "resuming after 2 instances on disk" in r.stdout
    from fejepa.analysis.ritz import complete_lines

    _close(_strip_t(complete_lines(out / "rows.jsonl")), _strip_t(_rows(box, "baseline", "h2d")))
    a = json.loads((out / "summary.json").read_text())
    b = _summary(box, "baseline", "h2d")
    for k in ("ladder", "n", "n_used", "identity_failed", "record_checks"):
        if k == "ladder":
            for p in a[k]:
                for kk in ("median", "mean", "worse_than_zero", "paired", "dropped_max"):
                    _close(a[k][p][kk], b[k][p][kk], where=f"{p}.{kk}")
        else:
            assert a[k] == b[k], k
    assert a["workers"] == 2
    keep = (out / "summary.json").read_text()
    (out / "summary.json").unlink()
    r = _run(BASE, "--config", cp, "--set", "h2d", "--resummarise", out, cwd=box["tmp"])
    assert r.returncode == 0, r.stdout + r.stderr
    again = json.loads((out / "summary.json").read_text())
    assert {k: v for k, v in again.items() if k not in ("workers", "worker_threads", "machine",
                                                        "code", "config_sha256")} == \
        {k: v for k, v in json.loads(keep).items() if k not in ("workers", "worker_threads",
                                                                "machine", "code",
                                                                "config_sha256")}
    r = _run(BASE, "--config", cp, "--set", "h2d", cwd=box["tmp"])           # done: no work
    assert r.returncode == 0 and "all 4 instances on disk" in r.stdout


def test_the_baseline_refuses_changed_inputs(box, tmp_path):
    import copy

    cfg = box["cfg"]
    # a report that is not the configuration's
    rep = Path(cfg["baseline"]["sets"]["val3d"]["report"])
    bad = tmp_path / "report.json"
    bad.write_bytes(rep.read_bytes() + b" ")
    cp = _cfg_copy(box, tmp_path, lambda c: c["baseline"]["sets"]["val3d"].update(
        report=str(bad)))
    r = _run(BASE, "--config", cp, "--set", "val3d", cwd=box["tmp"])
    assert r.returncode == 3 and "REFUSED" in r.stdout and "SHA-256" in r.stdout
    assert not (tmp_path / "out").exists()
    # an identity record whose instances are in another order than the report's
    amp = json.loads(Path(cfg["baseline"]["sets"]["fine3d"]["identity"]["path"]).read_text())
    per = amp["seeds"]["s1"]["fine"]["per_instance"]
    per[0]["egap"], per[1]["egap"] = per[1]["egap"], per[0]["egap"]
    p_amp = tmp_path / "amp.json"
    s_amp = _write(p_amp, amp)
    cp = _cfg_copy(box, tmp_path, lambda c: c["baseline"]["sets"]["fine3d"]["identity"].update(
        path=str(p_amp), sha256=s_amp))
    r = _run(BASE, "--config", cp, "--set", "fine3d", cwd=box["tmp"])
    assert r.returncode == 3 and "instance order?" in r.stdout, r.stdout + r.stderr
    assert not (tmp_path / "out" / "baseline" / "fine3d" / "rows.jsonl").exists()
    # a corpus whose manifest is not the report's
    c3 = Path(json.loads(rep.read_text())["config"]["data"]["dir"])
    shadow = tmp_path / "shadow"
    shutil.copytree(c3, shadow / c3.name)
    man = shadow / c3.name / "manifest.json"
    man.write_text(man.read_text() + "\n")
    r3 = json.loads(rep.read_text())
    r3["config"]["data"]["dir"] = str(shadow / c3.name)
    for d in r3["provenance"]["datasets"]:
        if d["dir"] == str(c3):
            d["dir"] = str(shadow / c3.name)
    p3 = tmp_path / "report3.json"
    s3 = _write(p3, r3)
    cp = _cfg_copy(box, tmp_path, lambda c: c["baseline"]["sets"]["val3d"].update(
        report=str(p3), report_sha256=s3))
    r = _run(BASE, "--config", cp, "--set", "val3d", cwd=box["tmp"])
    assert r.returncode == 3 and "manifest" in r.stdout, r.stdout + r.stderr
    # a holdout labels file that is not the labels manifest's, and a holdout
    # labels manifest that is not the returned one
    hd = Path(cfg["baseline"]["sets"]["h2d"]["labels_dir"])
    lab = tmp_path / "labels_h2d"
    shutil.copytree(hd, lab)
    first = sorted((lab / "labels").iterdir())[0]
    first.write_bytes(first.read_bytes() + b"\0")
    cp = _cfg_copy(box, tmp_path, lambda c: c["baseline"]["sets"]["h2d"].update(
        labels_dir=str(lab)))
    r = _run(BASE, "--config", cp, "--set", "h2d", cwd=box["tmp"])
    assert r.returncode == 3 and "REFUSED" in r.stdout and first.name in r.stdout, r.stdout
    assert not (tmp_path / "out" / "baseline" / "h2d" / "rows.jsonl").exists()
    cp = _cfg_copy(box, tmp_path, lambda c: c["baseline"]["sets"]["h2d"].update(
        labels_manifest_sha256="0" * 64))
    r = _run(BASE, "--config", cp, "--set", "h2d", cwd=box["tmp"])
    assert r.returncode == 3 and "labels manifest" in r.stdout
    # rows on disk that are not a prefix of the set
    cp = _cfg_copy(box, tmp_path, lambda c: None)
    out = tmp_path / "out" / "baseline" / "val2d"
    out.mkdir(parents=True)
    (out / "rows.jsonl").write_text(json.dumps({"i": 0, "file": "other.npz"}) + "\n")
    r = _run(BASE, "--config", cp, "--set", "val2d", cwd=box["tmp"])
    assert r.returncode == 3 and "not a prefix" in r.stdout
    # a specification that is not the code's
    cp = _cfg_copy(box, tmp_path, lambda c: c["spec"].update(cut=1e-12))
    r = _run(BASE, "--config", cp, "--set", "val2d", cwd=box["tmp"])
    assert r.returncode == 3 and "not the code's" in r.stdout
    assert copy.deepcopy(cfg) == box["cfg"]


def test_an_instance_that_is_not_the_recorded_one(box, tmp_path):
    """The identity record says otherwise for one instance: every row is
    written, the instance is listed, left out of the pairing, exit 4."""
    cfg = box["cfg"]
    idc = cfg["baseline"]["sets"]["val2d"]["identity"]
    with np.load(idc["path"]) as z:
        Z = {k: z[k] for k in z.files}
    Z["uK_star"] = Z["uK_star"].copy()
    Z["uK_star"][1] *= 1.0 + 1e-4
    p = tmp_path / "spectra_val.npz"
    np.savez(p, **Z)
    cp = _cfg_copy(box, tmp_path, lambda c: c["baseline"]["sets"]["val2d"]["identity"].update(
        path=str(p), sha256=_sha(p)))
    r = _run(BASE, "--config", cp, "--set", "val2d", cwd=box["tmp"])
    assert r.returncode == 4, r.stdout + r.stderr
    assert "NOT THE RECORDED INSTANCE" in r.stdout
    summ = json.loads((tmp_path / "out" / "baseline" / "val2d" / "summary.json").read_text())
    assert summ["n"] == 3 and summ["n_used"] == 2 and len(summ["identity_failed"]) == 1
    assert summ["ladder"]["6"]["paired"]["cm2d:ar@4"][0]["energy_gap_rel"]["n"] == 2


def test_the_enriched_rows_bound_and_reproduction(box):
    from fejepa.analysis import ritz as R

    cfg = box["cfg"]
    for arm, a in cfg["enriched"]["arms"].items():
        seeds = [3, 4, 5] if a["dim"] == 2 else [0, 1, 2]
        log = box["logs"][f"enriched_{arm}"]
        pre = [json.loads(x) for x in log.splitlines() if x.startswith('{"arm"') and
               '"precheck"' in x]
        assert [p["set"] for p in pre] == a["sets"]
        for p in pre:
            want = "val3d" if (arm, p["set"]) == ("k3d_labels_knorm", "fine3d") else p["set"]
            assert p["precheck"]["set"] == want
            assert all(v == [0.0, 0.0] for v in p["precheck"]["median_rel_dev"].values())
        for s in a["sets"]:
            rows = _rows(box, "enriched", arm, s)
            summ = _summary(box, "enriched", arm, s)
            n = cfg["enriched"]["sets"][s]["n"]
            assert len(rows) == n and summ["n_identity_ok"] == n and summ["complete"]
            assert summ["seeds_order"] == seeds and summ["degree"] == R.ENRICHED_DEGREE[a["dim"]]
            st = a["states"]
            want = ({str(sd): _sha(Path(st["dir"]) / f"ar_p{POOL}_s{sd}.pt") for sd in seeds}
                    if st["from"] == "d9" else st["sha256"])
            assert summ["state_sha256"] == want
            assert summ["solves"]["ritz"].startswith("Appendix 1") and summ["bound_tol"] == 1e-8
            assert all(v["bound_ok"] for v in summ["seeds"].values())
            for r in rows:
                assert r["identity"]["ok"] and r["k"] == R.n_unknowns(a["dim"], r["p"])
                assert set(r["seeds"]) == {str(x) for x in seeds}
                for e in r["seeds"].values():
                    assert e["bound_excess"] <= 1e-9
                    ge = np.array(e["enriched"]["load"]["energy_gap_rel"])
                    gc = np.array(e["cstar"]["load"]["energy_gap_rel"])
                    gn = np.array(e["net"]["load"]["energy_gap_rel"])
                    assert np.all(gc <= gn + 1e-9) and np.all(ge <= gc + 1e-9)
                    if "repro" in e:
                        assert e["repro"]["energy_gap_rel_rel_diff"] < 1e-9
                        if "c_star_max_abs_diff" in e["repro"]:
                            assert e["repro"]["c_star_max_abs_diff"] < 1e-9
            cont = summ["content"]
            if (arm, s) == ("k3d_labels_knorm", "fine3d"):
                assert cont is None
            else:
                assert cont["passed"] and all(c["energy_gap_rel_max_rel_dev"] == 0.0
                                              for c in cont["checks"].values())
            for sd in seeds:
                ss = summ["seeds"][str(sd)]
                med = {v: np.median([(r["seeds"][str(sd)][v] if v != "ritz" else r["ritz"])
                                     ["mean"]["energy_gap_rel"] for r in rows])
                       for v in ("cstar", "ritz", "enriched")}
                assert np.isclose(ss["inband_ratio"],
                                  med["enriched"] / min(med["cstar"], med["ritz"]))
        rd = json.loads((Path(cfg["out"]) / "enriched" / arm / "reading.json").read_text())
        assert rd["sets_complete"] == sorted(a["sets"]) and rd["appendix"] is a["appendix"]
        inb = [s for s in a["sets"] if cfg["enriched"]["sets"][s]["inband"]]
        ood = [s for s in a["sets"] if not cfg["enriched"]["sets"][s]["inband"]]
        r_in = [_summary(box, "enriched", arm, s)["seeds"][str(sd)]["inband_ratio"]
                for s in inb for sd in seeds]
        r_od = [_summary(box, "enriched", arm, s)["seeds"][str(sd)]["ood_peak_ratio"]
                for s in ood for sd in seeds]
        hi, ho = all(v <= 0.8 for v in r_in), all(v <= 0.5 for v in r_od)
        ai = rd["all_instances"]
        assert ai["inband"]["holds"] is hi and ai["ood"]["holds"] is ho
        assert ai["complementary"] is (hi or ho)
        assert "identity_ok_instances" not in rd and rd["identity_failed"] == {
            s: [] for s in a["sets"]}


def test_the_enriched_ritz_is_the_baselines(box):
    """On val3d and fine3d the enriched reading's Ritz solution (p = 8, formed
    at that degree) is the baseline's p = 8 (a sub-block of p = 9)."""
    for s in ("val3d", "fine3d"):
        base = _rows(box, "baseline", s)
        enr = _rows(box, "enriched", "phase2b", s)
        for b, e in zip(base, enr):
            assert b["file"] == e["file"]
            for f in FIELDS:
                assert np.allclose(b["ritz"]["8"]["load"][f], e["ritz"]["load"][f], rtol=1e-6,
                                   atol=1e-10), (s, f)


def test_enriched_workers_equal_one_process_and_refusals(box, tmp_path):
    cp = _cfg_copy(box, tmp_path, lambda c: None)
    r = _run(ENR, "--config", cp, "--arm", "phase2b", "--device", "cpu", "--workers", "2",
             "--worker-threads", "1", cwd=box["tmp"])
    assert r.returncode == 0, r.stdout + r.stderr
    for s in ("val3d", "fine3d"):
        from fejepa.analysis.ritz import complete_lines

        a = complete_lines(tmp_path / "out" / "enriched" / "phase2b" / s / "rows.jsonl")
        _close(_strip_t(a), _strip_t(_rows(box, "enriched", "phase2b", s)), where=s)
    # a state that is not the configuration's: refused before anything is built
    lab = Path(box["cfg"]["enriched"]["arms"]["phase2b_labels"]["states"]["pattern"].format(
        seed=1))
    sdir = tmp_path / "states"
    sdir.mkdir()
    for s in (0, 1, 2):
        src = Path(str(lab).replace("_s1.pt", f"_s{s}.pt"))
        (sdir / src.name).write_bytes(src.read_bytes() + (b"\0" if s == 1 else b""))
    cp2 = _cfg_copy(box, tmp_path, lambda c: c["enriched"]["arms"]["phase2b_labels"][
        "states"].update(pattern=str(sdir / "labels_b4_s{seed}.pt")))
    r = _run(ENR, "--config", cp2, "--arm", "phase2b_labels", "--device", "cpu", cwd=box["tmp"])
    assert r.returncode == 3 and "REFUSED" in r.stdout and "s1" in r.stdout, r.stdout
    assert not (tmp_path / "out" / "enriched" / "phase2b_labels").exists()
    # a record that the model does not reproduce: exit 5 before the set is written
    rep = json.loads(Path(box["cfg"]["enriched"]["arms"]["b_n1024"]["report"]).read_text())
    pse = rep["results"]["e8"]["metrics"]["holdouts"]["F2"][str(POOL)]["per_seed_eval"][1]
    pse["per_instance"]["energy_gap_rel"] = [x * 1.1 for x in
                                            pse["per_instance"]["energy_gap_rel"]]
    p = tmp_path / "report_b.json"
    sha = _write(p, rep)
    cp3 = _cfg_copy(box, tmp_path, lambda c: c["enriched"]["arms"]["b_n1024"].update(
        report=str(p), report_sha256=sha))
    r = _run(ENR, "--config", cp3, "--arm", "b_n1024", "--device", "cpu", "--sets", "F2",
             cwd=box["tmp"])
    assert r.returncode == 5 and "NOT REPRODUCED" in r.stdout, r.stdout + r.stderr
    assert not (tmp_path / "out" / "enriched" / "b_n1024" / "F2" / "rows.jsonl").exists()
    # a wp9 file that is not its manifest's
    d = Path(box["w9sets"]["F5"]["dir"])
    shadow = tmp_path / "F5"
    shutil.copytree(d, shadow)
    f0 = shadow / "instance_00000.npz"
    f0.write_bytes(f0.read_bytes() + b"\0")
    rep = json.loads(Path(box["cfg"]["enriched"]["arms"]["s_n1024"]["report"]).read_text())
    rep["evaluation"]["holdouts"]["F5"]["dir"] = str(shadow)
    p = tmp_path / "report_s.json"
    sha = _write(p, rep)
    cp4 = _cfg_copy(box, tmp_path, lambda c: c["enriched"]["arms"]["s_n1024"].update(
        report=str(p), report_sha256=sha))
    r = _run(ENR, "--config", cp4, "--arm", "s_n1024", "--device", "cpu", "--sets", "F5",
             cwd=box["tmp"])
    assert r.returncode == 3 and "instance_00000.npz" in r.stdout, r.stdout + r.stderr


def test_the_reading_refuses_mixed_states_and_handles_missing_sets(box, tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location("enriched_cstar", ENR)
    ec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ec)
    cfg = box["cfg"]
    base = tmp_path / "phase2b"
    shutil.copytree(Path(cfg["out"]) / "enriched" / "phase2b", base)
    r = ec.reading(cfg, "phase2b", base)
    assert r["sets_complete"] == ["fine3d", "val3d"]
    (base / "fine3d" / "summary.json").unlink()
    r = ec.reading(cfg, "phase2b", base)
    assert r["all_instances"]["ood"] is None
    held = r["all_instances"]["inband"]["holds"]
    assert r["all_instances"]["complementary"] is (True if held else None)
    s = json.loads((base / "val3d" / "summary.json").read_text())
    s2 = dict(s, state_sha256={"0": "x"})
    shutil.copytree(base / "val3d", base / "fine3d", dirs_exist_ok=True)
    (base / "fine3d" / "summary.json").write_text(json.dumps(s2))
    with pytest.raises(ec.Refused, match="different states"):
        ec.reading(cfg, "phase2b", base)
    # a summary whose network did not reproduce is refused, not read
    (base / "fine3d" / "summary.json").write_text(json.dumps(dict(
        s, content={"passed": False})))
    r = ec.reading(cfg, "phase2b", base)
    assert r["sets_refused"] == {"fine3d": "the network does not reproduce its records on "
                                           "this set"}


def test_the_timing_row(box, tmp_path):
    for dim, sets in (("3", {"val": 2, "fine": 1}), ("2", {"val": 2})):
        out = tmp_path / f"ritz_timing_{dim}d.json"
        r = _run(TIM, "--config", box["cfg_path"], "--dim", dim, "--out", out, cwd=box["tmp"])
        assert r.returncode == 0, r.stdout + r.stderr
        t = json.loads(out.read_text())
        assert {k: v["n"] for k, v in t["sets"].items()} == sets
        assert t["settings"]["warmup"] == 1 and t["machine"]["cpu_count"]
        for name, res in t["results"].items():
            assert res["summary"]["complete"] and res["summary"]["K_max_rel_diff_max"] < 1e-12
            for row in res["rows"]:
                for p, e in row["p"].items():
                    parts = sum(e[k] for k in ("basis_s", "kp_s", "solve_s", "recon_s"))
                    assert np.isclose(e["ritz_s"], row["free_s"] + parts)
                    assert e["runs"] in (1, 3)
        # the accuracy recorded is the baseline's for the same instance and p
        bset = "val3d" if dim == "3" else "val2d"
        base = {r["file"]: r for r in _rows(box, "baseline", bset)}
        for row in t["results"]["val"]["rows"]:
            for p, e in row["p"].items():
                assert np.isclose(e["energy_gap_rel"],
                                  base[row["file"]]["ritz"][p]["mean"]["energy_gap_rel"],
                                  rtol=1e-6)


def test_the_repository_side_rebuilds_summaries_and_readings(box, tmp_path):
    """What G3 runs on a return: each set's summary rebuilt from its rows
    and the records (a wp9 arm's report read from another place, its SHA-256
    still checked), and each arm's reading from the summaries, equal to the
    box's."""
    out = Path(box["cfg"]["out"]) / "enriched"
    for arm, sname in (("b_n1024", "F2"), ("phase2b", "fine3d"), ("k3d_labels_knorm", "fine3d")):
        d = tmp_path / arm / sname
        shutil.copytree(out / arm / sname, d)
        args = ["--config", box["cfg_path"], "--arm", arm, "--resummarise", d]
        if arm == "b_n1024":
            moved = tmp_path / "report_b.json"
            shutil.copy(box["cfg"]["enriched"]["arms"][arm]["report"], moved)
            args += ["--report", moved]
        r = _run(ENR, *args, cwd=tmp_path)
        assert r.returncode == 0, r.stdout + r.stderr
        assert json.loads((d / "summary.json").read_text()) == \
            json.loads((out / arm / sname / "summary.json").read_text())
    bad = tmp_path / "report_bad.json"
    bad.write_bytes(Path(box["cfg"]["enriched"]["arms"]["b_n1024"]["report"]).read_bytes() + b" ")
    r = _run(ENR, "--config", box["cfg_path"], "--arm", "b_n1024", "--resummarise",
             tmp_path / "b_n1024" / "F2", "--report", bad, cwd=tmp_path)
    assert r.returncode == 3 and "SHA-256" in r.stdout
    for arm in ("s_n1024", "phase2b"):
        d = tmp_path / "reading" / arm
        shutil.copytree(out / arm, d)
        (d / "reading.json").unlink()
        r = _run(ENR, "--config", box["cfg_path"], "--arm", arm, "--reread", d, cwd=tmp_path)
        assert r.returncode == 0, r.stdout + r.stderr
        assert json.loads((d / "reading.json").read_text()) == \
            json.loads((out / arm / "reading.json").read_text())


def test_the_timing_repeats_by_the_first_run():
    """The cost table's rule: a step whose first run takes under one second
    runs three times; the later runs' times do not decide."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("ritz_timing", TIM)
    rt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rt)
    for times, n in (([0.5, 2.0, 0.1], 3), ([1.5, 0.1, 0.1], 1), ([0.99, 0.99, 5.0], 3)):
        it = iter(times)
        assert len(rt.repeated(lambda: next(it), lambda t: t)) == n, times
    out, ts = rt._timed(lambda: 7)
    assert out == 7 and len(ts) == 3                      # far under one second
