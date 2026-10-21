#!/usr/bin/env python3
"""K3D (PREREG_K3D): the three-dimensional supervised transformer of Phase-2,
trained again with the stiffness-norm loss L_K in place of the displacement
loss L_D and with nothing else changed, beside the stored states it is compared
with, which are not trained again: Phase-2's L_D transformer (`labels`) and
Phase-2b's label-free transformer (`ar`).

Inputs, each checked before anything trains:
  - the source report (the Phase-2b run, `records/wp8/e2/baseline/
    report_phase2b.json`), by SHA-256; its embedded configuration, by the
    configuration SHA-256 it records, gives the model, the corpus and its
    split, the supervised schedule of E8 (its `sup_epochs` and `sup_lr`), the
    TF32 policy and the runtime (fp32, no compile);
  - the corpus, by the manifest SHA-256 the report records; the training
    instances are the labelled pool prefix pool[:budget] on which E8's
    supervised units at that budget trained, and the evaluation set is the
    run's validation split;
  - the stored states, by the SHA-256 the configuration copies from the
    records of the runs that trained them (`reused`).

Then, in order:
  1. the stored states are evaluated on the validation split with the frozen
     metric suite (`fejepa.metrics.evaluate_model`, as the run's units
     evaluated them), and each must reproduce the report's per-instance
     values (`fejepa.analysis.holdout.content_check`: every value finite, the
     medians of the relative deviations of the displacement error and the
     relative energy gap at most `content_tol`); otherwise the run stops
     before any training (exit status 5). The evaluations are kept
     (`reused.json`);
  2. for each seed, in order, the L_K transformer trains as E8's
     `labels_knorm` unit at that budget and seed would (`run_e8`,
     `supervised_unit`): the model built right after seeding with the seed
     (hence the initial weights of E8's `labels` unit of that seed), the
     training instances in the order the trainer draws from a generator
     seeded with the seed (hence `labels`'s order), `train_supervised` with
     anchor mode "none" and loss "knorm", E8's epochs and learning rate,
     SupervisedConfig's weight decay, clipping and schedule, and the
     encoder's activation checkpointing as the configuration sets it
     (`train.activation_checkpointing`; off in `configs/k3d_v1.json`, as in
     the code that trained Phase-2's L_D states, which predates it; values
     and gradients are the same either way); then the state is saved and
     the trainer's own evaluation on the validation split kept.
     A seed's result file is written before its epoch checkpoint is removed;
     a seed whose result file is usable (this seed, this code, this
     configuration, its state on disk at the recorded SHA-256) is not run
     again; any other result file is moved aside and the seed runs again. An
     interrupted training resumes from its epoch checkpoint (written at most
     every 5 minutes) if this code, configuration and seed wrote it (its
     sidecar file); any other checkpoint is moved aside and the seed trains
     from the start;
  3. if the configuration names a holdout set (`holdout`), every state of
     the three rows predicts every instance of it, with the labels that
     PREREG_HOLDOUT's run computed on the box (its labels manifest, checked
     against the set's definition and recorded by SHA-256, which the
     adjudication compares with PREREG_HOLDOUT's return; every corpus and
     labels file checked against the manifest), and the suite's values are
     kept (`holdout_arrays.npz`);
  4. the report: per row, the cell at the budget (`e8_regimes._agg` over the
     seeds' evaluations, per-instance values included), the content checks,
     the training records, the machines and the code.

Before anything runs on a GPU, the GPU must work (an allocation and a
synchronisation) and be free (90% of its memory); a run on a GPU never falls
back to the CPU. The code's `git describe` and commit are read before
anything else runs, the dry run included; a run that cannot read them
stops, and so does a guarded run (`prereg_guard`) whose `git describe` is
not exactly `prereg-k3d` or whose pre-registration's last line is not its
own SHA-256. The training instances' labels and every holdout corpus and
labels file (by SHA-256) are checked before the GPU is touched, the dry run
included. One run at a time: the run holds a lock on `<out>/.lock` while it
runs. The code is identified by its `git describe` and its commit wherever
an earlier attempt's files are kept or resumed.

With `--skip-holdout` the holdout set is neither checked nor evaluated and
the report records that it was skipped (PREREG_K3D Sec. 6: only after the
holdout evaluation has failed in two consecutive attempts once every seed has
trained). Exit status: 0 done; 2 no
GPU, or a GPU that does not work or is in use (nothing ran on it); 3 an input
refused, or another run holding the lock (a line beginning `STOP:` names
it); 5 a stored state does not reproduce the source report's validation
values (nothing trained); anything else, an error (a traceback).

    python scripts/k3d_train.py configs/k3d_v1.json --dry-run
    python scripts/k3d_train.py configs/k3d_v1.json
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import inspect
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

TAG = "prereg-k3d"
"""The tag a guarded run must run on (`git describe --always --dirty --tags`)."""
ROWS = ("ar", "labels", "labels_knorm")
REUSED = ("ar", "labels")
TRAINED = "labels_knorm"
PROGRESS_EVERY = 32
GPU_FREE = 0.9
"""The share of the GPU's memory that must be free before the run starts."""


def _sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _rel(path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def stop(msg: str, code: int = 3):
    print(f"STOP: {msg}", flush=True)
    raise SystemExit(code)


def _write_json(path, obj: dict) -> None:
    """JSON written to a temporary file, flushed to the disk and moved into
    place (`fejepa.analysis.holdout.write_json_synced`)."""
    from fejepa.analysis.holdout import write_json_synced

    write_json_synced(path, obj)


def git_commit() -> str:
    """The checkout's commit (`git rev-parse HEAD`), or "unavailable"."""
    import subprocess

    try:
        r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                           text=True, timeout=30)
        out = r.stdout.strip()
        return out if r.returncode == 0 and len(out) == 40 else "unavailable"
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def prereg_footer_ok(path) -> bool:
    """The stamped pre-registration's last line is its own SHA-256
    (`scripts/stamp_prereg_k3d.py`'s check)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("stamp_prereg_k3d",
                                                  ROOT / "scripts" / "stamp_prereg_k3d.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    try:
        return bool(mod.self_hash_ok(Path(path).read_text(encoding="utf-8")))
    except OSError:
        return False


def take_lock(out_dir: Path):
    """One run at a time: an exclusive lock on `<out_dir>/.lock`, held while
    the returned file stays open (the system releases it when the process
    ends, however it ends)."""
    import fcntl

    out_dir.mkdir(parents=True, exist_ok=True)
    fh = open(out_dir / ".lock", "a+")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        stop(f"another run of this script holds {out_dir / '.lock'} "
             "(`pgrep -af scripts/k3d_train.py` shows it)")
    return fh


def probe_flush(out_dir: Path) -> None:
    """The dry run's check of the checkpoint writer on this disk: a probe
    written through `atomic_torch_save` (the file and its directory entry
    flushed to the disk) and removed, with the directory if the probe made it;
    a failure stops the dry run here rather than the first epoch checkpoint."""
    from fejepa.train.checkpoint import atomic_torch_save

    made = not out_dir.exists()
    p = out_dir / ".flush_probe.pt"
    try:
        atomic_torch_save({"probe": True}, p)
    except OSError as exc:
        stop(f"{out_dir}: a checkpoint cannot be written and flushed to the disk here "
             f"({type(exc).__name__}: {exc})")
    finally:
        for q in (p, p.with_name(p.name + ".tmp")):
            q.unlink(missing_ok=True)
        if made:
            try:
                out_dir.rmdir()
            except OSError:
                pass


# ------------------------------------------------------------------ inputs --

KEYS = ("source", "reused", "train", "seeds", "content_tol", "holdout", "out", "prereg_file",
        "prereg_guard", "device")
"""The configuration's keys (and an optional `_comment`)."""
TRAIN_KEYS = ("row", "loss", "budget", "epochs", "lr", "weight_decay", "clip", "warmup_frac",
              "activation_checkpointing")


def verify(cfg: dict, label: str) -> dict:
    """The guard, then the configuration's own checks (`check_config`);
    returns what the report records about them."""
    from fejepa.report import config_sha256, verify_prereg

    out = {"config_sha256": config_sha256(cfg), "prereg": None}
    if cfg.get("prereg_guard"):
        pf = _rel(cfg["prereg_file"])
        try:
            out["prereg"] = {"file": cfg["prereg_file"],
                             "config_sha256": verify_prereg(cfg, pf, label=label)}
        except ValueError as exc:
            stop(str(exc))
        if not prereg_footer_ok(pf):
            stop(f"{cfg['prereg_file']}: its last line is not its own SHA-256 (not the "
                 "stamped file)")
    check_config(cfg)
    return out


def check_config(cfg: dict) -> None:
    """The configuration's keys, the source report by SHA-256, the training
    block against the trainer's defaults, the stored rows, the seeds and the
    holdout block (the guard apart)."""
    from fejepa.train.schedule import make_scheduler
    from fejepa.train.supervised import SupervisedConfig

    if sorted(k for k in cfg if k != "_comment") != sorted(KEYS):
        stop(f"the configuration's keys are {sorted(cfg)}, expected {sorted(KEYS)} "
             "(and an optional _comment)")
    if sorted(cfg["train"]) != sorted(TRAIN_KEYS):
        stop(f"train: keys {sorted(cfg['train'])}, expected {sorted(TRAIN_KEYS)}")
    seeds = cfg["seeds"]
    if not (isinstance(seeds, list) and seeds and all(type(s) is int for s in seeds)
            and len(set(seeds)) == len(seeds)):
        stop(f"seeds {seeds!r}: a list of distinct integers")
    if not (isinstance(cfg["content_tol"], float) and 0 < cfg["content_tol"] < 1):
        stop(f"content_tol {cfg['content_tol']!r}: a number between 0 and 1")
    src = cfg["source"]
    got = _sha256(_rel(src["report"]))
    if got != src["report_sha256"]:
        stop(f"{src['report']}: SHA-256 {got[:12]}... is not the source report "
             f"({src['report_sha256'][:12]}...)")
    tr = cfg["train"]
    if tr.get("row") != TRAINED or tr.get("loss") != "knorm":
        stop(f"train: row {tr.get('row')!r} / loss {tr.get('loss')!r} -- this script trains "
             f"the stiffness-norm row ('{TRAINED}', loss 'knorm') only")
    wf = inspect.signature(make_scheduler).parameters["warmup_frac"].default
    if float(tr["warmup_frac"]) != float(wf):
        stop(f"train.warmup_frac {tr['warmup_frac']} is not the trainer's ({wf})")
    sd = {f.name: f.default for f in dataclasses.fields(SupervisedConfig)}
    for k in ("weight_decay", "clip"):
        if float(tr[k]) != float(sd[k]):
            stop(f"train.{k} {tr[k]} is not E8's supervised units' (SupervisedConfig's {sd[k]})")
    if not isinstance(tr.get("activation_checkpointing"), bool):
        stop("train.activation_checkpointing must be true or false")
    if sorted(cfg["reused"]) != sorted(REUSED):
        stop(f"reused: rows {sorted(cfg['reused'])}, expected {sorted(REUSED)}")
    h = cfg.get("holdout")
    if h is not None and not (isinstance(h, dict) and sorted(h) == ["dir", "set", "spec"]):
        stop("holdout: null, or the keys spec, set and dir")


def check_source(report: dict, cfg: dict) -> dict:
    """The source report's configuration: its own hash, and the E8 settings the
    L_K units must share with its supervised units. Returns the settings."""
    from fejepa.report import config_sha256

    rc = report["config"]
    if config_sha256(rc) != report["provenance"]["config_sha256"]:
        stop("the source report's embedded configuration does not hash to its recorded "
             "config_sha256")
    e8 = rc["experiments"]["e8"]
    rt = rc.get("runtime") or {}
    if rt.get("precision", "fp32") != "fp32" or bool(rt.get("compile", False)):
        stop(f"the source report's runtime is {rt}: its supervised units trained in fp32 "
             "without compile, and so does this script")
    tr = cfg["train"]
    budget = int(tr["budget"])
    if budget not in [int(b) for b in e8["budgets"]]:
        stop(f"train.budget {budget}: the source run's E8 trained budgets {e8['budgets']}")
    epochs, lr = int(e8.get("sup_epochs", 200)), float(e8.get("sup_lr", 1.5e-3))
    if int(tr["epochs"]) != epochs or float(tr["lr"]) != lr:
        stop(f"train: epochs {tr['epochs']} / lr {tr['lr']} are not E8's supervised units' "
             f"({epochs} / {lr})")
    if str((rc.get("model") or {}).get("kind", "fejepa")) != "fejepa":
        stop("the source run's transformer is not the FE-JEPA-role model (model.kind)")
    seeds = [int(s) for s in cfg["seeds"]]
    rep_seeds = [int(s) for s in report["provenance"]["seeds"]]
    if any(s not in rep_seeds for s in seeds):
        stop(f"seeds {seeds}: the source report ran {rep_seeds}")
    return {"budget": budget, "epochs": epochs, "lr": lr, "tf32": bool(rc.get("tf32", True)),
            "rep_seeds": rep_seeds}


def instance_sets(report: dict, budget: int, data_dir=None) -> dict:
    """The validation split and the labelled pool prefix pool[:budget], from a
    corpus whose manifest is the report's."""
    from fejepa.analysis.common import instance_files as split_files
    from fejepa.analysis.posthoc import run_files, verified_dir
    from fejepa.data.archive import has_labels

    rc = report["config"]
    where = data_dir or rc["data"]["dir"]
    try:
        d = verified_dir(report, where)               # refuses with SystemExit(message)
        val = run_files(report, "val", None, d)
        pool = split_files(d, split=rc["split"], subset="pool")
    except SystemExit as exc:
        stop(f"the corpus: {exc.code}")
    except (OSError, ValueError, KeyError) as exc:
        stop(f"the corpus {where}: {type(exc).__name__}: {exc}")
    if len(pool) < budget:
        stop(f"the corpus's pool holds {len(pool)} instances; the budget is {budget}")
    missing = [Path(f).name for f in pool[:budget] if not has_labels(f)]
    if missing:                                       # before any GPU time, dry run included
        stop(f"{len(missing)} training instances carry no labels (first {missing[0]})")
    return {"val": val, "train": pool[:budget], "data_dir": str(d)}


def reused_states(cfg: dict, seeds: list) -> dict:
    """{(row, seed): path} of the stored states, each refused unless it has the
    SHA-256 the configuration records for it."""
    out, bad = {}, []
    sdir = _rel(cfg["source"]["states_dir"])
    for row in REUSED:
        r = cfg["reused"][row]
        for s in seeds:
            p = sdir / r["state"].format(seed=int(s))
            want = r["sha256"][str(int(s))]
            if not p.is_file():
                bad.append(f"{p}: missing")
                continue
            got = _sha256(p)
            if got != want:
                bad.append(f"{p}: SHA-256 {got[:12]}..., recorded {want[:12]}...")
            out[(row, int(s))] = p
    if bad:
        stop("stored states refused: " + "; ".join(bad))
    return out


def check_records(report: dict, cfg: dict) -> None:
    """The SHA-256 the configuration copies must be those of their records:
    the label-free states' the source report's E8 record (`d9_restart`), the
    L_D states' the record of Phase-2's state directory
    (`records/wp9/phase2_supervised_states.json`)."""
    rec = report["results"]["e8"]["metrics"]["d9_restart"]["ar_states"]
    for s, want in cfg["reused"]["ar"]["sha256"].items():
        if (rec.get(f"s{s}") or {}).get("sha256") != want:
            stop(f"reused.ar: the seed-{s} SHA-256 is not the source report's E8 record")
    lab = cfg["reused"]["labels"]
    try:
        side = json.loads(_rel(lab["sha256_source"]).read_text())["sha256"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        stop(f"reused.labels: its record {lab['sha256_source']} cannot be read "
             f"({type(exc).__name__})")
    for s, want in lab["sha256"].items():
        if side.get(lab["state"].format(seed=int(s))) != want:
            stop(f"reused.labels: the seed-{s} SHA-256 is not the one {lab['sha256_source']} "
                 "records")


# ------------------------------------------------------------------- GPU --

def gpu_ready(device: str) -> dict:
    """On a GPU: one that works (an allocation and a synchronisation) and is
    free; a run never falls back to the CPU. Returns the GPU's name and memory."""
    if not str(device).startswith("cuda"):
        return {"device": str(device)}
    import torch

    if not torch.cuda.is_available():
        stop("no GPU (torch.cuda.is_available() is False): this run does not fall back to "
             "the CPU", 2)
    try:
        torch.zeros(1, device=device).add_(1)
        torch.cuda.synchronize()
        free, total = torch.cuda.mem_get_info()
        name = torch.cuda.get_device_name()
    except Exception as exc:                           # noqa: BLE001
        stop(f"the GPU does not work ({type(exc).__name__}: "
             f"{(str(exc).splitlines() or [''])[0][:120]})", 2)
    if free < GPU_FREE * total:
        stop(f"the GPU is in use ({(total - free) / 2**30:.1f} of {total / 2**30:.1f} GiB "
             "taken)", 2)
    return {"device": str(device), "gpu": name, "memory_gib": round(total / 2**30, 1)}


def _cpu_model() -> str | None:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return None


def machine(tries: int = 2) -> dict:
    """The host (the container's name), its CPU model, and the first GPU's
    driver and UUID (None where they cannot be read, after `tries` attempts)."""
    import platform
    import subprocess

    drv = uuid = None
    for i in range(tries):
        try:
            r = subprocess.run(["nvidia-smi", "--query-gpu=driver_version,uuid",
                                "--format=csv,noheader"], capture_output=True, text=True,
                               timeout=60)
            if r.returncode == 0 and r.stdout.strip():
                first = [x.strip() for x in r.stdout.strip().splitlines()[0].split(",")]
                drv = first[0] or None
                uuid = first[1] if len(first) > 1 and first[1] else None
                break
        except FileNotFoundError:                         # no tool: no GPU driver to read
            break
        except Exception:                                 # noqa: BLE001 (a failed query)
            pass
        if i + 1 < tries:
            time.sleep(5)
    return {"host": platform.node(), "cpu": _cpu_model(), "gpu_driver": drv, "gpu_uuid": uuid}


def torch_info(device: str) -> dict:
    import torch

    out = {"version": torch.__version__, "cuda": torch.version.cuda,
           "cuda_available": bool(torch.cuda.is_available())}
    if str(device).startswith("cuda") and torch.cuda.is_available():
        out["gpu"] = torch.cuda.get_device_name()
    return out


# ------------------------------------------------------------- evaluation --

class _Progress:
    """The instances of `archs` (a LazyArchives), with a progress line every
    `every`; it has the length of `archs`, which evaluate_model records."""

    def __init__(self, archs, what: str, every: int = PROGRESS_EVERY):
        self.archs, self.what, self.every = archs, what, every

    def __len__(self) -> int:
        return len(self.archs)

    def __iter__(self):
        for i, a in enumerate(self.archs):
            if i % self.every == 0:
                print(f"[k3d] evaluating {self.what}: {i}/{len(self.archs)}", flush=True)
            yield a


def evaluate_state(report: dict, path, seed: int, device: str, files: list, what: str) -> dict:
    """The stored state, built as the report's model and strictly loaded,
    evaluated with the frozen metric suite as the run's units evaluated it."""
    from fejepa.analysis.posthoc import run_model
    from fejepa.data.archive import LazyArchives
    from fejepa.metrics import evaluate_model, torch_predictor

    model = run_model(report, path, seed, device)
    return evaluate_model(torch_predictor(model, device), _Progress(LazyArchives(files), what))


def reference(report: dict, row: str, cell: str, seed_index: int) -> dict:
    cells = report["results"]["e8"]["metrics"]["cells"]
    return cells[row][str(cell)]["per_seed_eval"][seed_index]["per_instance"]


def reused_evaluations(report: dict, cfg: dict, states: dict, seeds: list, rep_seeds: list,
                       sets: dict, device: str) -> dict:
    """Every stored state on the validation split, with its content check."""
    from fejepa.analysis.holdout import content_check

    tol = float(cfg["content_tol"])
    out = {}
    for row in REUSED:
        cell = cfg["reused"][row]["cell"]
        for s in seeds:
            p = states[(row, s)]
            t0 = time.time()
            ev = evaluate_state(report, p, s, device, sets["val"], f"{row} s{s}")
            ref = reference(report, row, cell, rep_seeds.index(s))
            chk = content_check(ev["per_instance"], ref, tol)
            out[f"{row}_s{s}"] = {"row": row, "seed": int(s), "state": str(p),
                                  "sha256": _sha256(p),       # as evaluated, hashed again
                                  "val": ev, "content_check": chk,
                                  "seconds": round(time.time() - t0, 1)}
            print(json.dumps({"reused": f"{row}_s{s}", "content_check": chk}), flush=True)
    return out


def usable_reused(path: Path, code: dict, config_sha: str, keys: list) -> dict | None:
    """An earlier attempt's evaluations of the stored states, if usable: of
    this code (`git describe` and commit) and configuration, every state's,
    every content check passed."""
    try:
        prev = json.loads(path.read_text())
        ok = (prev.get("git") == code["git"] and prev.get("commit") == code["commit"]
              and prev.get("config_sha256") == config_sha
              and sorted(prev["states"]) == sorted(keys)
              and all(v["content_check"]["ok"] is True for v in prev["states"].values()))
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None
    return prev if ok else None


# ---------------------------------------------------------------- training --

def epoch_orders(seed: int, n: int, epochs: int) -> list:
    """The instance order of every epoch as train_supervised draws it: one
    `np.random.default_rng(seed)` and one permutation per epoch, nothing else
    drawn from it (tests/test_k3d_train.py checks the trainer against this)."""
    import numpy as np

    rng = np.random.default_rng(int(seed))
    return [rng.permutation(int(n)).tolist() for _ in range(int(epochs))]


def _sidecar(ckpt: Path) -> Path:
    return ckpt.with_name(ckpt.name + ".json")


def own_checkpoint(ckpt: Path, mine: dict, here: dict) -> list:
    """An epoch checkpoint is resumed only by the code (`git describe` and
    commit), configuration and seed that wrote it (its sidecar file records
    them, and the machines the seed has run on); any other, or one whose
    sidecar cannot be read, is moved aside and the seed trains from the start.
    Then the sidecar, written atomically, names this run. Returns the machines
    of this seed's training: the first is where it started, the last (`here`)
    where it runs now."""
    machines = []
    if ckpt.exists():
        try:
            side = json.loads(_sidecar(ckpt).read_text())
            ok = isinstance(side, dict) and {k: side.get(k) for k in mine} == mine
        except (OSError, ValueError):
            side, ok = {}, False
        if ok:
            ms = side.get("machines")
            machines = [m for m in ms if isinstance(m, dict)] if isinstance(ms, list) else []
        else:
            aside = ckpt.with_name(f"{ckpt.name}.unusable.{time.strftime('%Y%m%d-%H%M%S')}")
            ckpt.rename(aside)
            print(f"[k3d] {ckpt.name} was not written by this code, configuration and seed, "
                  f"or its record cannot be read (moved to {aside.name}); training from the "
                  "start", flush=True)
    machines.append(here)
    _write_json(_sidecar(ckpt), dict(mine, machines=machines))     # temp file, fsync, replace
    return machines


def unit_name(budget: int, seed: int) -> str:
    return f"{TRAINED}_b{int(budget)}_s{int(seed)}"


def train_runtime() -> dict:
    """The TF32 setting the training runs with."""
    import torch

    return {"tf32_matmul": bool(torch.backends.cuda.matmul.allow_tf32),
            "tf32_cudnn": bool(torch.backends.cudnn.allow_tf32),
            "float32_matmul_precision": torch.get_float32_matmul_precision()}


def load_training(files: list) -> list:
    """The training instances with their labels, which every one must carry."""
    from fejepa.data.archive import load_instance

    archs = [load_instance(Path(f)) for f in files]
    missing = [Path(a.path).name for a in archs if a.U_star is None]
    if missing:
        stop(f"{len(missing)} training instances carry no labels (first {missing[0]})")
    return archs


def run_seed(seed: int, report: dict, cfg: dict, src: dict, sets: dict, out_dir: Path,
             device: str, code: dict) -> dict:
    """One seed of the L_K row: build, train (or resume), save, evaluate. The
    caller writes the result file and then removes the seed's checkpoint."""
    from fejepa.experiments.parallel import _apply_runtime, _build_model, _state_dict
    from fejepa.data.archive import LazyArchives
    from fejepa.report import config_sha256
    from fejepa.train.checkpoint import atomic_torch_save
    from fejepa.train.supervised import SupervisedConfig, train_supervised

    t0 = time.time()
    here = machine()
    budget = src["budget"]
    name = unit_name(budget, seed)
    ckpt = out_dir / f"{name}.ckpt"
    machines = own_checkpoint(ckpt, {"git": code["git"], "commit": code["commit"],
                                     "config_sha256": config_sha256(cfg), "seed": int(seed)},
                              here)
    # E8's supervised unit (parallel.supervised_unit): the runtime policy, then
    # the model right after seeding with the seed, then the trainer; the
    # encoder's activation checkpointing is a plain attribute (not a parameter
    # or buffer), so the initial weights do not depend on it
    ckpt_on = bool(cfg["train"]["activation_checkpointing"])
    payload = {"kind": "fejepa",
               "model": dict(report["config"]["model"], activation_checkpointing=ckpt_on),
               "seed": int(seed), "tf32": src["tf32"], "sup": {"device": device}}
    _apply_runtime(payload)
    model = _build_model(payload)
    archs = load_training(sets["train"])
    scfg = SupervisedConfig(epochs=src["epochs"], lr=src["lr"], device=device,
                            anchor_mode="none", loss="knorm", seed=int(seed),
                            precision="fp32", desc=f"K3D {TRAINED} b{budget} s{seed}",
                            ckpt_path=str(ckpt), resume=True)
    t1 = time.time()
    out = train_supervised(model, archs, LazyArchives(sets["val"]), scfg)
    t2 = time.time()
    sp = out_dir / f"{name}.pt"
    atomic_torch_save(_state_dict(model), sp)
    n_train = len(archs)
    del archs
    losses = list((out.get("history") or {}).get("loss") or [])
    orders = epoch_orders(int(seed), n_train, src["epochs"])
    if out.get("resumed_from_epoch") is None:
        machines = [here]          # trained from the start here (a checkpoint that could not
        #                            be read was moved aside by the trainer)
    res = {"seed": int(seed), "git": code["git"], "commit": code["commit"],
           "config_sha256": config_sha256(cfg), "torch": torch_info(device),
           "machine": {"start": machines[0], "resumed_on": machines[1:], "end": machine()},
           "train": {"row": TRAINED, "loss": "knorm", "anchor_mode": "none",
                     "budget": budget, "files": [Path(f).name for f in sets["train"]],
                     "seed": int(seed), "epochs": src["epochs"], "lr": src["lr"],
                     "epochs_run": len(losses), "steps": len(losses) * n_train,
                     "order_sha256": hashlib.sha256(json.dumps(orders).encode()).hexdigest(),
                     "loss_by_epoch": losses, "runtime": train_runtime(),
                     "activation_checkpointing": bool(model.encoder.use_checkpoint),
                     "protocol": out.get("protocol"),
                     "resumed_from_epoch": out.get("resumed_from_epoch")},
           "state": {"path": str(sp), "sha256": _sha256(sp)},
           "val": out["val"]}
    res["seconds"] = {"build_and_load": round(t1 - t0, 1),
                      "train_and_evaluate": round(t2 - t1, 1)}
    return res


def finished(rf: Path, seed: int, code: dict, config_sha: str, epochs: int) -> dict | None:
    """A seed's result file, if it is usable: readable, of this seed, of this
    code (`git describe` and commit) and configuration, trained for every
    epoch, its state on disk at the recorded SHA-256."""
    try:
        prev = json.loads(rf.read_text())
        sp = Path(prev["state"]["path"])
        ok = (int(prev.get("seed", -1)) == int(seed) and prev.get("git") == code["git"]
              and prev.get("commit") == code["commit"]
              and prev.get("config_sha256") == config_sha
              and int(prev["train"]["epochs_run"]) == int(epochs)
              and isinstance(prev["val"]["per_instance"], dict)
              and sp.is_file() and _sha256(sp) == prev["state"]["sha256"])
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None
    return prev if ok else None


def _aside(p: Path, what: str) -> None:
    aside = p.with_name(f"{p.name}.unusable.{time.strftime('%Y%m%d-%H%M%S')}")
    p.rename(aside)
    print(f"[k3d] {what}: {p.name} unusable (moved to {aside.name}); run again", flush=True)


# ---------------------------------------------------------------- holdout --

def holdout_inputs(cfg: dict) -> dict | None:
    """The holdout set the configuration names, if any: PREREG_HOLDOUT's set
    definition (its report and its stored states must be this run's) and the
    labels manifest its run wrote, checked against the definition; the
    manifest's SHA-256 is recorded."""
    h = cfg.get("holdout")
    if not h:
        return None
    from fejepa.analysis.holdout import check_labelled_set, load_spec

    try:
        spec = load_spec(_rel(h["spec"]))
    except (OSError, ValueError) as exc:
        stop(f"holdout: {h['spec']}: {exc}")
    sdef = (spec.get("sets") or {}).get(h["set"])
    if sdef is None:
        stop(f"holdout: {h['spec']} defines no set {h['set']!r}")
    if sdef.get("report_sha256") != cfg["source"]["report_sha256"]:
        stop("holdout: the set's report is not this run's source report")
    for row in REUSED:
        if (sdef.get("rows") or {}).get(row, {}).get("sha256") != cfg["reused"][row]["sha256"]:
            stop(f"holdout: the set's {row} states are not this run's (SHA-256)")
    d = _rel(h["dir"])
    if not (d / "manifest.json").is_file():
        stop(f"holdout: {d / 'manifest.json'} does not exist (PREREG_HOLDOUT's labels)")
    try:
        man = check_labelled_set(h["set"], sdef, d)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        stop(f"holdout: {exc}")
    corpus = Path(sdef["corpus"])
    t0, bad = time.time(), []
    for r in man["instances"]:                    # every file, before any training
        for f, want in ((corpus / r["file"], r["source_sha256"]),
                        (d / "labels" / r["file"], r["labels_sha256"])):
            if not f.is_file():
                bad.append(f"{f}: missing")
            elif _sha256(f) != want:
                bad.append(f"{f}: not the bytes the labels manifest records")
    if bad:
        stop(f"holdout: {len(bad)} files refused (first {bad[0]})")
    print(f"[k3d] holdout {h['set']}: {len(man['instances'])} instances, their corpus and "
          f"labels files verified ({time.time() - t0:.0f} s)", flush=True)
    return {"name": h["set"], "sdef": sdef, "dir": d, "n": len(man["instances"]),
            "manifest_sha256": _sha256(d / "manifest.json")}


def holdout_evaluation(report: dict, hold: dict, paths: dict, seeds: list, device: str,
                       out_dir: Path) -> dict:
    """Every state of the three rows on the holdout set: the suite's five
    values per instance, and per load case the relative energy gap and the
    energy (`holdout.instance_record`)."""
    import numpy as np

    from fejepa.analysis.holdout import (METRICS, holdout_instances, instance_record,
                                         predict, save_npz_synced, worse_than_zero)
    from fejepa.analysis.posthoc import run_model

    models = {k: run_model(report, p, k[1], device) for k, p in paths.items()}
    n = hold["n"]
    M = np.full((len(ROWS), len(seeds), n, len(METRICS)), np.nan)
    G = P = None
    files, t0 = [], time.time()
    for i, arch in enumerate(holdout_instances(hold["name"], hold["sdef"], hold["dir"])):
        if G is None:
            G = np.full((len(ROWS), len(seeds), n, arch.n_loads), np.nan)
            P = np.full(G.shape, np.nan)
        files.append(Path(arch.path).name)
        for (r, s), m in models.items():
            rec = instance_record(predict(m, arch, device), arch)
            ri, si = ROWS.index(r), seeds.index(s)
            M[ri, si, i] = rec["metrics"]
            G[ri, si, i] = rec["gap_load"]
            P[ri, si, i] = rec["pi_load"]
        if (i + 1) % PROGRESS_EVERY == 0 or i + 1 == n:
            print(f"[k3d] holdout {hold['name']}: {i + 1}/{n} | {time.time() - t0:.0f} s",
                  flush=True)
    path = out_dir / "holdout_arrays.npz"
    save_npz_synced(path, rows=np.array(ROWS), seeds=np.array(seeds),
                    metrics=np.array(METRICS), files=np.array(files), values=M,
                    gap_load=G, pi_load=P)
    summary = {f"{r}_s{s}": {k: float(np.mean(M[ROWS.index(r), seeds.index(s), :, j]))
                             for j, k in enumerate(METRICS)} for r in ROWS for s in seeds}
    worse = {f"{r}_s{s}": worse_than_zero(G[ROWS.index(r), seeds.index(s)],
                                          P[ROWS.index(r), seeds.index(s)])
             for r in ROWS for s in seeds}
    return {"set": hold["name"], "n": n, "labels_manifest_sha256": hold["manifest_sha256"],
            "arrays": path.name, "arrays_sha256": _sha256(path),
            "files_sha256": hashlib.sha256("\n".join(files).encode()).hexdigest(),
            "summary": summary, "worse_than_zero": worse,
            "seconds": round(time.time() - t0, 1)}


# -------------------------------------------------------------------- run --

def run(config_path, device_override: str | None = None, data_dir=None,
        dry_run: bool = False, skip_holdout: bool = False) -> dict:
    from fejepa.analysis.common import resolve_device
    from fejepa.report import _git_describe

    cp = Path(config_path)
    cfg = json.loads(cp.read_text())
    ver = verify(cfg, cp.stem)
    git, commit = _git_describe(), git_commit()
    if "unavailable" in (git, commit):
        stop("git describe or the commit could not be read: the code this run uses cannot "
             "be recorded")
    if cfg.get("prereg_guard") and git != TAG:
        stop(f"git describe is {git!r}, not {TAG!r}: a guarded run runs on the stamped tag "
             "without local changes")
    code = {"git": git, "commit": commit}
    report = json.loads(_rel(cfg["source"]["report"]).read_text())
    src = check_source(report, cfg)
    check_records(report, cfg)
    device = resolve_device(device_override or cfg.get("device", "cuda"))
    seeds = [int(s) for s in cfg["seeds"]]
    states = reused_states(cfg, seeds)
    sets = instance_sets(report, src["budget"], data_dir)
    hold = None if skip_holdout else holdout_inputs(cfg)
    out = _rel(cfg["out"])
    out_dir = out.parent
    if dry_run:
        probe_flush(out_dir)
    plan = {"k3d": str(cp), "row": TRAINED, "device": device, "seeds": seeds,
            "budget": src["budget"], "epochs": src["epochs"], "lr": src["lr"],
            "n_train": len(sets["train"]), "n_val": len(sets["val"]),
            "states_verified": len(states),
            "holdout": "skipped" if skip_holdout else (hold["n"] if hold else None),
            "git": git, "commit": commit, "prereg": ver["prereg"]}
    print(json.dumps(plan), flush=True)
    if dry_run:
        return {"dry_run": True, **plan}
    gpu = gpu_ready(device)
    lock = take_lock(out_dir)
    try:
        return _run(cfg, ver, report, src, sets, hold, states, seeds, device, gpu, code, out,
                    out_dir, skip_holdout)
    finally:
        lock.close()


def _run(cfg, ver, report, src, sets, hold, states, seeds, device, gpu, code, out, out_dir,
         skip_holdout) -> dict:
    """The run proper, under the lock: the stored states, the seeds, the
    holdout set, the report."""
    from fejepa.experiments.e8_regimes import _agg
    from fejepa.report import provenance

    # 1. the stored states, before any training
    rp = out_dir / "reused.json"
    keys = [f"{r}_s{s}" for r in REUSED for s in seeds]
    prev = usable_reused(rp, code, ver["config_sha256"], keys) if rp.is_file() else None
    reused_from_disk = prev is not None
    if prev is not None:
        print("[k3d] stored states: evaluations on disk (reused.json); not run again",
              flush=True)
        reused = prev["states"]
    else:
        if rp.is_file():
            _aside(rp, "stored states")
        reused = reused_evaluations(report, cfg, states, seeds, src["rep_seeds"], sets,
                                    device)
        _write_json(rp, {"git": code["git"], "commit": code["commit"],
                         "config_sha256": ver["config_sha256"], "machine": machine(),
                         "runtime": train_runtime(), "states": reused})
    failed = [k for k, v in reused.items() if not v["content_check"]["ok"]]
    if failed:
        stop(f"the stored states {failed} do not reproduce the source report's validation "
             "values; stopped before training", 5)

    # 2. the L_K row, seed by seed
    per_seed = {}
    for s in seeds:
        rf = out_dir / f"seed_{s}.json"
        if rf.is_file():
            prev = finished(rf, s, code, ver["config_sha256"], src["epochs"])
            if prev is not None:
                print(f"[k3d] seed {s}: result on disk ({rf.name}); not run again", flush=True)
                per_seed[f"s{s}"] = dict(prev, from_disk=True)
                continue
            _aside(rf, f"seed {s}")
        res = run_seed(s, report, cfg, src, sets, out_dir, device, code)
        _write_json(rf, res)                      # the result first, then the checkpoint goes
        ck = out_dir / f"{unit_name(src['budget'], s)}.ckpt"
        ck.unlink(missing_ok=True)
        _sidecar(ck).unlink(missing_ok=True)
        per_seed[f"s{s}"] = res
        v = res["val"]
        print(json.dumps({"seed": s, "val": {k: v[k] for k in ("disp_rel_l2", "energy_gap_rel",
                                                               "vm_rel_l2")},
                          "seconds": res["seconds"]}), flush=True)

    # 3. the holdout set, if the configuration names one
    holdout = {"skipped": True} if skip_holdout else None
    if hold:
        paths = {(r, s): states[(r, s)] for r in REUSED for s in seeds}
        paths.update({(TRAINED, s): Path(per_seed[f"s{s}"]["state"]["path"]) for s in seeds})
        holdout = holdout_evaluation(report, hold, paths, seeds, device, out_dir)

    # 4. the report
    from fejepa.runtime import setup_torch

    policy = setup_torch(device, tf32=src["tf32"])
    b = str(src["budget"])
    cells = {r: {cfg["reused"][r]["cell"]: _agg([reused[f"{r}_s{s}"]["val"] for s in seeds])}
             for r in REUSED}
    cells[TRAINED] = {b: _agg([per_seed[f"s{s}"]["val"] for s in seeds])}
    rep = {"what": "K3D: the three-dimensional supervised transformer trained with the "
                   "stiffness-norm loss beside the stored L_D and label-free states "
                   "(PREREG_K3D)",
           "config": cfg, "prereg": ver["prereg"],
           "provenance": dict(provenance(cfg, [sets["data_dir"]], seeds),
                              git=code["git"],    # the reading before the first seed
                              commit=code["commit"],
                              source_report=cfg["source"]["report"],
                              source_report_sha256=_sha256(_rel(cfg["source"]["report"])),
                              source_config_sha256=report["provenance"]["config_sha256"]),
           "runtime_policy": policy, "device": device, "gpu": gpu,
           "torch": torch_info(device),
           "budget": src["budget"], "seeds": seeds, "rows": list(ROWS),
           "cells": cells,
           "content_checks": {k: v["content_check"] for k, v in reused.items()},
           "reused_evaluations_from_disk": reused_from_disk,
           "reused": {k: {kk: v[kk] for kk in ("row", "seed", "state", "sha256", "seconds")}
                      for k, v in reused.items()},
           "per_seed": {k: {kk: v[kk] for kk in v if kk != "val"} for k, v in per_seed.items()},
           "holdout": holdout}
    _write_json(out, rep)
    print(f"[k3d] report -> {out}", flush=True)
    return rep


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--device", default=None)
    ap.add_argument("--data-dir", default=None, help="override the report's corpus directory")
    ap.add_argument("--dry-run", action="store_true",
                    help="verify the guard, the report, the corpus, the states and the "
                         "holdout labels; train nothing")
    ap.add_argument("--skip-holdout", action="store_true",
                    help="neither check nor evaluate the holdout set (PREREG_K3D Sec. 6: only "
                         "after its evaluation has failed in two consecutive attempts)")
    a = ap.parse_args()
    run(a.config, a.device, a.data_dir, dry_run=a.dry_run, skip_holdout=a.skip_holdout)


if __name__ == "__main__":
    main()
