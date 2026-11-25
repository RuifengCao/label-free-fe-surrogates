"""Train one seed of a development run of the CHS surrogate (exploratory, not a gate), with checkpoints and resume,
then predict the evaluated members at the evaluation levels in both readings. Follows c22/train.py.

The run is label-free: the loss of a step is the mean of log Pi over the step's fields of one member, Pi the
deformation-theory energy of the spring-loaded instance (f2.torch_energy, float32) at device rotations drawn for the
step; AdamW with the configuration's beta2, the cap on the encoder's gradient (c22.train.cap_encoder_gradient), the
global clipping and the repository's cosine schedule. No reference solution enters training, the snapshots or the
predictions.

Files of a run, out_dir/label_free_s<seed>/:
    state.pt              the checkpoint (networks, optimiser, schedule, generators, history), replaced at the end of
                          an epoch once checkpoint_minutes have passed since the last one, and at the end
    progress.json         the losses and times so far, rewritten with every checkpoint (small; for watching a run)
    snapshots.json        at the configured epochs: what the network's fields say at the evaluation levels for the
                          evaluated members (end rotation, spring moment, Theta_D, float32 energy), raw reading
    history.json          written once, when the run ends
    attempts.log          every start, resume, pause and end
    preds.npz, preds_condensed.npz, preds_base.npz, condense.json     as c22.train.predict

Where the configuration asks for them (training.ema), exponential moving averages of the weights are kept beside the
weights that are trained: after every step, average <- d average + (1 - d) weights, one average for each decay d,
each starting from the weights the run starts from. They take no part in training. Each has a run folder of its own,
<out_dir>_ema<digits of d>/label_free_s<seed>/, with average.json (what it is), snapshots.json at the same epochs,
and at the end history.json, progress.json and the four prediction files, so that the evaluation reads it as it
reads any run. The averages are kept in state.pt.

Members are built on the device when a step needs them and at most resident_members of them are kept there, so the
number of training members is not bounded by the device's memory.

Where the configuration asks for them, the device rotations of a step are drawn in another way (training.Theta_kind,
training.Theta_top; f2.model.sample_Theta), and extra training members join those of training.members
(training.extra_members): they come from a data directory of their own (f2.data.extra_config, extra_dir) and an
epoch is one step on every training member, the extra ones included. Snapshots, predictions and the evaluation are
those of data_dir as before.
"""
from __future__ import annotations

import collections
import contextlib
import datetime
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np

from c22.data import _replace, _write_json
from c22.train import cap_encoder_gradient
from .data import load_export, manifest, data_sha256
from .model import features, maps, build, field, readings, sample_Theta

MATMUL_PRECISION = "highest"          # float32 matmuls without TF32
PREDICTION_FILES = ("preds.npz", "preds_condensed.npz", "preds_base.npz", "condense.json")
CODE = ("f2/model.py", "f2/train.py", "f2/torch_energy.py", "f2/devconfig.py", "f2/config.py", "f2/family.py",
        "f2/instance.py", "f2/data.py", "f2/precond.py", "c2/torch_energy.py", "c22/condense.py", "c22/train.py")
REPOSITORY_CODE = ("src/fejepa/models/fejepa.py", "src/fejepa/train/schedule.py")
ROOT = Path(__file__).resolve().parents[1]


def _now() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _note(run: Path, text: str) -> None:
    with open(run / "attempts.log", "a", encoding="ascii") as fh:
        fh.write(f"{_now()} {text}\n")
        fh.flush()


def code_hashes() -> dict:
    """SHA-256 of the code a run imports, for its record (a development run pins nothing)."""
    import importlib.util

    out = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in CODE}
    spec = importlib.util.find_spec("fejepa")
    if spec is None or spec.origin is None:
        raise RuntimeError("the repository package fejepa is not on the path (--repo)")
    repo = Path(spec.origin).resolve().parents[2]
    out.update({f: hashlib.sha256((repo / f).read_bytes()).hexdigest() for f in REPOSITORY_CODE})
    return out


def launcher_gone() -> bool:
    """True when this training was started by the command `together` and that process has ended (a paused or
    stopped job): the training then stops too, and resumes from its checkpoint when it is started again."""
    pid = os.environ.get("F2_PARENT_PID")
    if not pid:
        return False
    pid = int(pid)
    if os.name == "nt":
        import ctypes

        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x00100000, False, pid)            # SYNCHRONIZE
        if not h:
            return True
        try:
            return k.WaitForSingleObject(h, 0) != 0x102       # WAIT_TIMEOUT: still running
        finally:
            k.CloseHandle(h)
    try:
        os.kill(pid, 0)
        return False
    except OSError:
        return True


def check_manifest(cfg: dict, data_dir) -> dict:
    man = manifest(data_dir)
    if man["config_sha256"] != data_sha256(cfg):
        raise RuntimeError("the data were generated under another family or data configuration")
    return man


def training_ids(cfg: dict, man: dict) -> list[str]:
    """The training members: ["train", n] is the first n members of the split train; otherwise a list of ids."""
    m = cfg["training"]["members"]
    have = [r["id"] for r in man["instances"]]
    if len(m) == 2 and m[0] == "train" and isinstance(m[1], int):
        ids = [r["id"] for r in man["instances"] if r["split"] == "train"][:m[1]]
        if len(ids) != m[1]:
            raise RuntimeError(f"the data hold {len(ids)} training members; the configuration asks for {m[1]}")
        return ids
    missing = [i for i in m if i not in have]
    if missing:
        raise RuntimeError(f"members not in the data: {missing}")
    return list(m)


def evaluated_ids(cfg: dict, man: dict | None = None) -> list[str]:
    """The evaluated members: the configuration's list, or every member of its evaluated sets. They follow from
    the configuration alone, whether or not their exports are in the data directory yet."""
    from .data import members

    ev = cfg["evaluation"]
    if ev.get("members"):
        return list(ev["members"])
    return [iid for iid, split, _ in members(cfg) if split in ev["sets"]]


_CARRIED = {}                          # (coarse data, data, member) -> the member's transfer, kept on the processor


def carried(under_dir, data_dir, iid: str, ex: dict) -> dict:
    """What carries a field of the member's coarser mesh (under_dir) to its mesh of data_dir: the matrix A of
    f2.prolong.prolongation as coordinate arrays, the shift z_pre - A z_pre_coarse of the two preload states (the
    carried field is the member's own preload state plus the carried change from the coarser mesh's preload
    state), the coarser export and the transfer's report. Worked out once for each member of a process."""
    key = (str(under_dir), str(data_dir), iid)
    if key not in _CARRIED:
        from .prolong import prolongation

        exu, qu = load_export(Path(under_dir) / "inst" / f"{iid}.npz")
        A, info = prolongation(exu, ex)
        with np.load(Path(under_dir) / "pre" / f"{iid}.npz") as pre:
            zpu = np.asarray(pre["z"], float)
        with np.load(Path(data_dir) / "pre" / f"{iid}.npz") as pre:
            zp = np.asarray(pre["z"], float)
        Ac = A.tocoo()
        _CARRIED[key] = {"ex": exu, "q": qu, "rows": np.vstack([Ac.row, Ac.col]).astype(np.int64),
                         "vals": Ac.data.astype(np.float32), "shape": tuple(Ac.shape),
                         "shift": (zp - A @ zpu).astype(np.float32), "info": info}
    return _CARRIED[key]


def build_item(data_dir, iid: str, device, lift: str, step: bool = False, under: dict | None = None) -> dict:
    """Base features, maps and the energy of one member on the device; with step, also the member's elastic contact
    step (f2/precond.py, on the processor) and the scale of each unknown over s (as f2.model.field scales them);
    with under (see train), also what the field underneath needs of the member."""
    import torch
    from .torch_energy import InstanceEnergy

    ex, q = load_export(Path(data_dir) / "inst" / f"{iid}.npz")
    it = {"id": iid, "base": torch.as_tensor(features(ex, q), dtype=torch.float32, device=device),
          "maps": maps(ex, q, device, lift), "energy": InstanceEnergy(ex, device=device, dtype=torch.float32)}
    if under is not None:
        c = carried(under["dir"], data_dir, iid, ex)
        it["under"] = {"base": torch.as_tensor(features(c["ex"], c["q"]), dtype=torch.float32, device=device),
                       "maps": maps(c["ex"], c["q"], device, under["lift"]),
                       "A": torch.sparse_coo_tensor(torch.as_tensor(c["rows"], device=device),
                                                    torch.as_tensor(c["vals"], device=device), c["shape"]).coalesce(),
                       "shift": torch.as_tensor(c["shift"], device=device), "info": c["info"]}
    if step:
        from .model import L_REF
        from .precond import ElasticContactStep

        with np.load(Path(data_dir) / "pre" / f"{iid}.npz") as pre:
            z_pre = np.asarray(pre["z"], float)
        it["step"] = ElasticContactStep(ex, z_pre)
        mp = it["maps"]
        unit = torch.ones(mp["n_z"], dtype=torch.float32, device=device)
        unit[3 * mp["n"]:3 * mp["n"] + 3 * mp["nb"]] = mp["head_scale"]
        unit[mp["n_z"] - 1] = 1.0 / L_REF
        it["unit"] = unit
        zc = torch.as_tensor(z_pre.astype(np.float32), device=device)          # the preload state, contacts closed
        zc[mp["nonneg"]] = zc[mp["nonneg"]].clamp(min=0.0)
        it["z_closed"] = zc
    return it


class Items:
    """The training members, built on the device on demand; at most `capacity` of them stay there (the oldest
    built leaves first)."""

    def __init__(self, data_dir, ids, device, lift: str, capacity: int, step: bool = False, under: dict | None = None):
        self.ids, self.device, self.lift, self.step, self.under = list(ids), device, lift, step, under
        # one data directory for all members, or one for each member (members from two directories)
        self.dirs = list(data_dir) if isinstance(data_dir, (list, tuple)) else [data_dir] * len(self.ids)
        if len(self.dirs) != len(self.ids):
            raise ValueError("one data directory for all members, or one for each")
        self.capacity = max(1, int(capacity))
        self.cache = collections.OrderedDict()
        self.built = 0

    def __len__(self):
        return len(self.ids)

    def get(self, k: int) -> dict:
        it = self.cache.get(k)
        if it is None:
            while len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
            it = self.cache[k] = build_item(self.dirs[k], self.ids[k], self.device, self.lift, self.step,
                                            under=self.under)
            self.built += 1
        return it


def under_field(under: dict, it: dict, Theta):
    """The field underneath (B, n_z), without gradient: the frozen coarser-mesh networks' field of the member at
    the rotations Theta, carried to the member's mesh (carried), the contact unknowns kept non-negative and the
    fixed unknowns zero."""
    import torch

    ub, mp = it["under"], it["maps"]
    with torch.no_grad():
        zs = field(*under["nets"], ub["base"], ub["maps"], Theta, under["T"], gate=under["gate"])
        z0 = torch.sparse.mm(ub["A"], zs.T.contiguous()).T + ub["shift"]
        z0 = torch.where(mp["nonneg"], z0.clamp_min(0.0), z0)
        return torch.where(mp["fixed"], torch.zeros_like(z0), z0)


def predicted(cfg: dict, nets, it: dict, Theta, under: dict | None = None):
    """The networks' fields of member it at the rotations Theta (with the field underneath, if the run has one)."""
    return field(*nets, it["base"], it["maps"], Theta, cfg["map"]["T"], gate=cfg["map"]["kind"],
                 under=None if under is None else under_field(under, it, Theta))


def step_loss(cfg: dict, nets, it: dict, rng, device, under: dict | None = None):
    """The loss of one step on member it (the mean of log Pi over the step's fields) and its device rotations."""
    import torch

    tr = cfg["training"]
    mp = it["maps"]
    Theta = torch.as_tensor(sample_Theta(rng, mp["Theta_max"], tr["fields_per_step"], tr["lam_min"],
                                         kind=tr.get("Theta_kind", "sqrt"), top=float(tr.get("Theta_top", 1.0))),
                            dtype=torch.float32, device=device)
    z = predicted(cfg, nets, it, Theta, under)
    kind = tr.get("loss_kind", "energy")
    if kind == "elastic_contact_step":
        return step_target_loss(it, z, Theta, tr["bubble_newton_steps"]), Theta
    if kind == "elastic_solution":
        return elastic_target_loss(it, z, Theta, tr["bubble_newton_steps"]), Theta
    Pi = it["energy"].energy(z, Theta, iters=tr["bubble_newton_steps"])
    if kind == "energy_and_elastic":      # the energy, plus the fit to the elastic solution at the low levels only
        low = Theta <= float(tr["anchor_max_level"]) * mp["Theta_max"]
        if not bool(low.any()):
            return torch.log(Pi).mean(), Theta
        zc = it["z_closed"][None].repeat(int(low.sum()), 1).requires_grad_(True)
        (g,) = torch.autograd.grad(it["energy"].energy(zc, Theta[low], iters=tr["bubble_newton_steps"]).sum(), zc)
        r2 = step_residual(it, z[low], g, Theta[low], z0=zc.detach())
        if tr.get("anchor_on", "all") == "contact":               # the gaps only: the rest is left to the energy
            r2 = r2[:, mp["nonneg"]]
        return torch.log(Pi).mean() + float(tr["step_weight"]) * r2.sum(dim=1).sum() / Theta.shape[0], Theta
    if kind in ("energy_and_step", "energy_and_contact_step"):    # the energy, plus the step loss summed per field
        (g,) = torch.autograd.grad(Pi.sum(), z, retain_graph=True)
        r2 = step_residual(it, z, g.detach(), Theta)
        if kind == "energy_and_contact_step":                     # on the contact unknowns only
            r2 = r2[:, mp["nonneg"]]
        return torch.log(Pi).mean() + float(tr["step_weight"]) * r2.sum(dim=1).mean(), Theta
    return torch.log(Pi).mean(), Theta


def step_residual(it: dict, z, g, Theta, z0=None):
    """(B, n_z): the squares of (z - (z0 + d)) over each unknown's scale, z0 the fields detached (or the states
    given) and d their elastic contact steps (f2/precond.py) from the energy's gradients g at z0."""
    import torch
    from .model import L_REF

    mp = it["maps"]
    z0 = z.detach() if z0 is None else z0
    zn, gn = z0.double().cpu().numpy(), g.double().cpu().numpy()
    d = np.stack([it["step"].step(zn[b], gn[b])[0] for b in range(zn.shape[0])])
    target = z0 + torch.as_tensor(d, dtype=z.dtype, device=z.device)
    scale = (L_REF * Theta + mp["delta"])[:, None] * it["unit"][None, :]
    return ((z - target) / scale) ** 2


def elastic_target_loss(it: dict, z, Theta, iters: int):
    """The loss of the fields z (B, n_z) against the member's elastic contact solutions at their device rotations:
    the closed preload state plus its elastic contact step (f2/precond.py). The target does not depend on z; it is
    the solution of the member with the preload tangent, which is the model's solution while the member is elastic."""
    import torch

    zc = it["z_closed"][None].repeat(z.shape[0], 1).requires_grad_(True)
    Pi = it["energy"].energy(zc, Theta, iters=iters)
    (g,) = torch.autograd.grad(Pi.sum(), zc)
    return step_residual(it, z, g, Theta, z0=zc.detach()).mean()


def step_target_loss(it: dict, z, Theta, iters: int):
    """The loss of the fields z (B, n_z) against their own elastic contact steps: the mean square of
    (z - (z0 + d)) over the scale of each unknown, with z0 the fields detached and d the step of f2/precond.py from
    the energy's gradient at z0. No reference solution enters; the gradient of the loss is the step itself."""
    import torch

    z0 = z.detach().requires_grad_(True)
    Pi = it["energy"].energy(z0, Theta, iters=iters)
    (g,) = torch.autograd.grad(Pi.sum(), z0)
    return step_residual(it, z, g, Theta).mean()


def ema_tag(decay: float) -> str:
    """The digits of a decay after the point: 0.999 gives "999"."""
    s = repr(float(decay))
    if not 0.0 < float(decay) < 1.0 or "e" in s:
        raise ValueError("a decay lies strictly between 0 and 1 and is written without an exponent")
    return s.split(".")[1]


def ema_run(out_dir, decay: float, arm: str, seed: int) -> Path:
    """The run folder of the weights averaged with `decay`: in a runs directory of its own beside out_dir."""
    out = Path(out_dir)
    return out.with_name(out.name + "_ema" + ema_tag(decay)) / f"{arm}_s{seed}"


@contextlib.contextmanager
def averaged(nets, avg):
    """The networks with the averaged weights `avg` in place of their own, which come back afterwards unchanged."""
    import torch

    own = [{k: p.detach().clone() for k, p in net.named_parameters()} for net in nets]
    with torch.no_grad():
        for net, e in zip(nets, avg):
            for k, p in net.named_parameters():
                p.copy_(e[k])
    try:
        yield
    finally:
        with torch.no_grad():
            for net, o in zip(nets, own):
                for k, p in net.named_parameters():
                    p.copy_(o[k])


def _levels(cfg: dict, mp: dict, device, base: bool):
    import torch

    lam = ([cfg["evaluation"]["readings"]["condensed"]["base_level"]] if base else []) + list(cfg["data"]["eval_levels"])
    return torch.as_tensor(lam, dtype=torch.float32, device=device) * mp["Theta_max"]


def snapshot(cfg: dict, nets, data_dir, ids, dev, under: dict | None = None) -> dict:
    """What the network's fields say at the evaluation levels, per evaluated member (raw reading; no reference).
    A member whose export is not in the data directory yet is left out."""
    import torch

    out = {}
    for net in nets:
        net.eval()
    for iid in ids:
        if not (Path(data_dir) / "inst" / f"{iid}.npz").exists():
            continue
        it = build_item(data_dir, iid, dev, cfg["model"]["lift"], under=under)
        Theta = _levels(cfg, it["maps"], dev, base=False)
        with torch.no_grad():
            z = predicted(cfg, nets, it, Theta, under)
            r = readings(it["energy"], it["maps"], z, Theta)
            Pi = it["energy"].energy(z, Theta, iters=cfg["training"]["bubble_newton_steps"])
        out[iid] = {"Theta": Theta.double().tolist(), "Pi": Pi.double().tolist(),
                    **{k: v.double().tolist() for k, v in r.items()}}
        del it
    for net in nets:
        net.train()
    return out


def predictions_written(run: Path) -> bool:
    return all((Path(run) / f).exists() for f in PREDICTION_FILES)


def predict(cfg: dict, nets, data_dir, run, dev, under: dict | None = None) -> bool:
    """Fields of the evaluated members at the evaluation levels, (L, n_z) per member id, float32: the network's
    fields (preds.npz) and the amplitude-condensed fields (preds_condensed.npz), with the network's field at the
    base level (preds_base.npz) and the amplitudes with the fields' own readings (condense.json). If any value is
    not finite, nothing is written and False is returned."""
    import torch

    from c22.condense import condense

    rd = cfg["evaluation"]["readings"]["condensed"]
    nbub = cfg["training"]["bubble_newton_steps"]
    ids = evaluated_ids(cfg, manifest(data_dir))
    missing = [i for i in ids if not (Path(data_dir) / "inst" / f"{i}.npz").exists()]
    if missing:
        raise RuntimeError(f"exports of evaluated members are missing ({len(missing)}, first {missing[0]}): generate "
                           "them and run train again; it goes on at the predictions")
    for net in nets:
        net.eval()
    raw, cond, base, info = {}, {}, {}, {}
    for iid in ids:
        it = build_item(data_dir, iid, dev, cfg["model"]["lift"], under=under)
        mp, E = it["maps"], it["energy"]
        lv = _levels(cfg, mp, dev, base=True)
        Theta = lv[1:]
        with torch.no_grad():
            zall = predicted(cfg, nets, it, lv, under)
        z0, z = zall[:1].expand(Theta.numel(), -1), zall[1:]
        a, st = condense(E, z0, z, Theta, mp["nonneg"], nbub, rd["a_min"], rd["a_max"], rd["max_evaluations"],
                         rd["rtol"])
        with torch.no_grad():
            zc = z0 + a[:, None] * (z - z0)
            zc = torch.where(mp["nonneg"], zc.clamp_min(0.0), zc)
            Pr, Pc = E.energy(z, Theta, iters=nbub), E.energy(zc, Theta, iters=nbub)
            rr, rc = readings(E, mp, z, Theta), readings(E, mp, zc, Theta)
        raw[iid], cond[iid] = z.float().cpu().numpy(), zc.float().cpu().numpy()
        base[iid] = zall[0].float().cpu().numpy()
        info[iid] = {"Theta": Theta.double().tolist(), "a": a.double().tolist(),
                     "rel_slope": st["rel_slope"].double().tolist(),
                     "at_bound": [bool(v) for v in st["at_bound"]], "converged": [bool(v) for v in st["converged"]],
                     "evaluations": int(st["evals"]), "Pi_raw": Pr.double().tolist(), "Pi_condensed": Pc.double().tolist(),
                     "raw": {k: v.double().tolist() for k, v in rr.items()},
                     "condensed": {k: v.double().tolist() for k, v in rc.items()}}
        del it, E
    for net in nets:
        net.train()
    finite = all(np.isfinite(v).all() for arrays in (raw, cond, base) for v in arrays.values()) \
        and all(np.isfinite(r["a"]).all() for r in info.values())
    if not finite:
        return False
    run = Path(run)
    for name, arrays in (("preds.npz", raw), ("preds_condensed.npz", cond), ("preds_base.npz", base)):
        tmp = run / (name + ".tmp")
        with open(tmp, "wb") as fh:
            np.savez_compressed(fh, **arrays)
        _replace(tmp, run / name)
    tmp = run / "condense.tmp"                             # written last: with it the predictions are whole
    tmp.write_text(json.dumps({"levels": list(cfg["data"]["eval_levels"]), "reading": rd, "members": info}))
    _replace(tmp, run / "condense.json")
    return True


def train(cfg: dict, seed: int, data_dir, out_dir, device: str = "cuda", stop_after_epoch: int | None = None,
          max_hours: float | None = None, checkpoint_minutes: float = 10.0, init_from=None,
          companion_dir=None, other_seed: bool = False, extra_dir=None, under_dir=None, under_state=None) -> dict:
    """Train (or resume) and write the run's files. Returns the history; its status is "finished", "paused" (the
    time limit or stop_after_epoch was reached: run again to go on) or a non-finite stop. init_from: the state.pt of
    another run whose networks' weights a new run starts from (its optimiser, schedule and history are not taken;
    a resumed run ignores it). With 0 among the snapshot epochs a new run takes a snapshot before its first step.
    With training["companion"] = {"mesh", "steps"}, every step on a member of data_dir is followed by that many
    steps on members drawn at random from companion_dir, which holds the same family on the companion mesh; the
    snapshots and the predictions are those of data_dir. other_seed: train a seed that the configuration does not
    list (development: more seeds of a run; the configuration and its hash stay as they are). With
    training["extra_members"], extra_dir holds those members (generated under f2.data.extra_config); they are
    training members like the others. With model["under"] = {"preset", "mesh"}, the networks' outputs are a
    correction to a field underneath (f2.model.field): under_state is the state.pt of a finished run of that preset
    on that mesh, whose networks stay as they are, and under_dir holds the same members on that mesh; the field
    underneath is the member's preload state plus the carried change of the coarser network's field from the
    coarser mesh's preload state (under_field, carried)."""
    from .config import sha256

    arm = "label_free"
    a = cfg["arms"][arm]
    if seed not in a["seeds"] and not other_seed:
        raise RuntimeError("the seed is not in the configuration")
    man = check_manifest(cfg, data_dir)
    cfg_sha = sha256(cfg)
    comp = cfg["training"].get("companion")
    if comp is not None:
        if companion_dir is None:
            raise RuntimeError("the configuration trains with a companion mesh; give its data directory")
        other = json.loads(json.dumps(cfg))
        other["data"]["mesh"] = comp["mesh"]
        man2 = check_manifest(other, companion_dir)
    xm, ids_x, man_x = cfg["training"].get("extra_members"), [], None
    if xm is not None:
        from .data import extra_config

        if comp is not None:
            raise RuntimeError("extra members and a companion mesh are not combined")
        if extra_dir is None:
            raise RuntimeError("the configuration trains with extra members; give their data directory (--extra-data)")
        man_x = check_manifest(extra_config(cfg), extra_dir)
        ids_x = [r["id"] for r in man_x["instances"] if r["split"] == "train"]
        if len(ids_x) != int(xm["n"]):
            raise RuntimeError(f"the extra data hold {len(ids_x)} members; the configuration asks for {xm['n']}")
    uc, ucfg = cfg["model"].get("under"), None
    if uc is not None:
        from .devconfig import config as preset_config

        if comp is not None or xm is not None:
            raise RuntimeError("a field underneath is not combined with a companion mesh or extra members")
        if under_dir is None or under_state is None:
            raise RuntimeError("the configuration trains on a field underneath; give --under-data and --under-state")
        ucfg = preset_config(uc["preset"])
        ucfg["data"]["mesh"] = uc["mesh"]
        man_u = check_manifest(ucfg, under_dir)
    run = Path(out_dir) / f"{arm}_s{seed}"
    run.mkdir(parents=True, exist_ok=True)
    decays = [float(x) for x in (cfg["training"].get("ema") or {}).get("decays", [])]
    if len(set(ema_tag(x) for x in decays)) != len(decays):
        raise RuntimeError("the decays of the averages must differ")
    runs_e = [ema_run(out_dir, x, arm, seed) for x in decays]
    _note(run, "start")
    print(f"start {cfg.get('preset', '')} {arm}_s{seed} {_now()}", flush=True)
    hp = run / "history.json"
    if hp.exists():
        old = json.loads(hp.read_text())
        if old.get("config_sha256") != cfg_sha:
            raise RuntimeError(f"{run} holds a run of another configuration; use a fresh runs directory")
        if str(old.get("status", "")).startswith("non-finite"):
            _note(run, "returned: " + old["status"])
            return old
        if old.get("status") == "finished" and predictions_written(run) and all(predictions_written(r) for r in runs_e):
            _note(run, "returned: finished")
            return old
    code = code_hashes()
    import torch
    from fejepa.train.schedule import make_scheduler

    torch.set_float32_matmul_precision(MATMUL_PRECISION)
    ids = training_ids(cfg, man)
    if set(ids) & set(ids_x):
        raise RuntimeError("an extra member has the name of a training member")
    watched = evaluated_ids(cfg, man)
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    dev = torch.device(device)
    tr = cfg["training"]
    under, under_record = None, None
    if uc is not None:
        if training_ids(ucfg, man_u) != ids:
            raise RuntimeError("the data underneath do not hold the same training members")
        src = Path(under_state)
        su = torch.load(src, map_location="cpu", weights_only=False)
        hu = su["history"]
        if hu.get("config_sha256") != sha256(ucfg):
            raise RuntimeError("the state underneath is not a run of the configured preset on the configured mesh")
        if su.get("epoch") != ucfg["arms"][arm]["epochs"]:
            raise RuntimeError("the run underneath has not finished its epochs")
        exu, qu = load_export(Path(under_dir) / "inst" / f"{ids[0]}.npz")
        nets_u = build(ucfg, features(exu, qu).shape[-1] + 1, int(np.asarray(exu["head"]).size))
        for net, k in zip(nets_u, ("enc", "dec", "head")):
            net.load_state_dict(su[k])
            net.to(dev)
            net.eval()
            for prm in net.parameters():
                prm.requires_grad_(False)
        under = {"dir": str(under_dir), "nets": nets_u, "lift": ucfg["model"]["lift"], "T": ucfg["map"]["T"],
                 "gate": ucfg["map"]["kind"]}
        under_record = {"file": src.name, "sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
                        "preset": hu.get("preset"), "mesh": uc["mesh"], "config_sha256": hu.get("config_sha256"),
                        "data_sha256": man_u["config_sha256"], "seed": hu.get("seed"), "epoch": su.get("epoch"),
                        "step": su.get("step")}
        del su, exu
    items = Items([data_dir] * len(ids) + [extra_dir] * len(ids_x), ids + ids_x, dev, cfg["model"]["lift"],
                  tr["resident_members"], step=tr.get("loss_kind", "energy") != "energy", under=under)
    n_comp, items2 = 0, None
    if comp is not None:
        if training_ids(cfg, man2) != ids:
            raise RuntimeError("the companion data do not hold the same training members")
        n_comp = int(comp["steps"])
        items2 = Items(companion_dir, ids, dev, cfg["model"]["lift"], tr["resident_members"],
                       step=tr.get("loss_kind", "energy") != "energy")
    first = items.get(0)
    nets = build(cfg, first["base"].shape[-1] + 1, first["maps"]["nb"])
    for net in nets:
        net.to(dev)
    enc = nets[0]
    params = [p for net in nets for p in net.parameters()]
    cap = tr["encoder_gradient_cap"]
    opt = torch.optim.AdamW(params, lr=tr["lr"], weight_decay=tr["weight_decay"], betas=(0.9, tr["beta2"]))
    total = a["epochs"] * len(items) * (1 + n_comp)
    sched = make_scheduler(opt, total)
    window = collections.deque(maxlen=cap["window_steps"])
    hist = {"config_sha256": cfg_sha, "data_sha256": man["config_sha256"], "preset": cfg.get("preset"), "arm": arm,
            "seed": seed, "code": code, "torch": torch.__version__, "numpy": np.__version__, "device": str(dev),
            "gpu": torch.cuda.get_device_name(0) if dev.type == "cuda" else None,
            "matmul_precision": torch.get_float32_matmul_precision(), "members": ids + ids_x, "total_steps": total,
            "epochs": a["epochs"], "betas": [0.9, tr["beta2"]],
            "cap": {k: cap[k] for k in ("factor", "window_steps", "burst_factor")},
            "loss": [], "epoch_seconds": [], "cap_events": [], "bursts": [], "resumes": [], "snapshots": [],
            "resumed_from_epoch": None}
    if man_x is not None:                                      # a run without extra members keeps its history's form
        hist["extra_data_sha256"] = man_x["config_sha256"]
    if under_record is not None:                               # likewise a run without a field underneath
        hist["under"] = under_record
        hist["under_transfer_of_first_member"] = first_info = items.get(0)["under"]["info"]
        _note(run, f"field underneath: {under_record['preset']} on mesh {under_record['mesh']}, seed "
                   f"{under_record['seed']}, step {under_record['step']}")
        print("transfer of the first member:", json.dumps(first_info), flush=True)
    start_epoch, step = 0, 0
    saved_avg = None
    ck = run / "state.pt"
    if ck.exists():
        s = torch.load(ck, map_location="cpu", weights_only=False)
        saved_avg = s.get("ema")
        if s["history"].get("config_sha256") != cfg_sha:
            raise RuntimeError(f"{ck} belongs to another configuration; use a fresh runs directory")
        for net, k in zip(nets, ("enc", "dec", "head")):
            net.load_state_dict(s[k])
        opt.load_state_dict(s["opt"]); sched.load_state_dict(s["sched"])
        rng.bit_generator.state = s["rng"]; torch.set_rng_state(s["torch_rng"])
        window.extend(s["window"])
        start_epoch, step, hist = s["epoch"], s["step"], s["history"]
        hist["resumed_from_epoch"] = start_epoch
        hist.setdefault("resumes", []).append(start_epoch)
        if hist.get("code") != code:                           # a development run may be resumed after an edit
            hist.setdefault("code_at_resumes", []).append({"epoch": start_epoch, "code": code})
        _note(run, f"resumed from epoch {start_epoch}")
        print(f"resumed from epoch {start_epoch}", flush=True)
    elif init_from is not None:
        src = Path(init_from)
        s0 = torch.load(src, map_location="cpu", weights_only=False)
        for net, k in zip(nets, ("enc", "dec", "head")):
            net.load_state_dict(s0[k])
        hist["init_from"] = {"file": src.name, "sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
                             "preset": s0["history"].get("preset"), "epoch": s0.get("epoch"), "step": s0.get("step"),
                             "config_sha256": s0["history"].get("config_sha256")}
        _note(run, f"weights from a run of {hist['init_from']['preset']} at step {hist['init_from']['step']}")
        del s0
    if under_record is not None and (hist.get("under") or {}).get("sha256") != under_record["sha256"]:
        raise RuntimeError("the run was started on another state underneath; use a fresh runs directory")
    avg = []
    if decays:
        if saved_avg is not None:
            if [float(x) for x in saved_avg["decays"]] != decays:
                raise RuntimeError(f"{ck} holds averages with other decays; use a fresh runs directory")
            avg = [[{k: v.to(dev) for k, v in e.items()} for e in one] for one in saved_avg["weights"]]
        else:
            if start_epoch:                                    # a checkpoint written without averages
                hist.setdefault("averages_restarted_at_epoch", []).append(start_epoch)
                _note(run, f"the averages start again from the weights of epoch {start_epoch}")
            avg = [[{k: p.detach().clone() for k, p in net.named_parameters()} for net in nets] for _ in decays]
        for x, re in zip(decays, runs_e):
            re.mkdir(parents=True, exist_ok=True)
            what = {"weights": "exponential moving average of the weights of the run named in `of`", "decay": x,
                    "of": f"{Path(out_dir).name}/{run.name}", "config_sha256": cfg_sha, "seed": seed}
            ap = re / "average.json"
            if ap.exists() and json.loads(ap.read_text()) != what:
                raise RuntimeError(f"{re} holds the average of another run; use a fresh runs directory")
            _write_json(ap, what)

    def progress(state: str) -> None:
        _write_json(run / "progress.json", {
            "time": _now(), "state": state, "preset": cfg.get("preset"), "seed": seed, "epoch": len(hist["loss"]),
            "epochs": a["epochs"], "step": step, "total_steps": total, "loss": hist["loss"],
            "epoch_seconds": hist["epoch_seconds"], "cap_events": len(hist["cap_events"]),
            "bursts": len(hist["bursts"]), "members_built": items.built})

    def checkpoint(done: int) -> None:
        tmp = ck.with_suffix(".tmp")
        with open(tmp, "wb") as fh:                        # on the disk before it takes the checkpoint's place
            state = {"enc": nets[0].state_dict(), "dec": nets[1].state_dict(), "head": nets[2].state_dict(),
                     "opt": opt.state_dict(), "sched": sched.state_dict(), "rng": rng.bit_generator.state,
                     "torch_rng": torch.get_rng_state(), "window": list(window), "epoch": done, "step": step,
                     "history": hist}
            if decays:                                         # a run without averages keeps its checkpoint's form
                state["ema"] = {"decays": decays, "weights": avg}
            torch.save(state, fh)
            fh.flush()
            os.fsync(fh.fileno())
        _replace(tmp, ck)

    def take_snapshot(done: int) -> None:
        sp = run / "snapshots.json"
        snaps = json.loads(sp.read_text()) if sp.exists() else {}
        snaps[str(done)] = snapshot(cfg, nets, data_dir, watched, dev, under)
        _write_json(sp, snaps)
        for one, re in zip(avg, runs_e):                       # the same reading of each average, in its own folder
            se = re / "snapshots.json"
            es = json.loads(se.read_text()) if se.exists() else {}
            with averaged(nets, one):
                es[str(done)] = snapshot(cfg, nets, data_dir, watched, dev, under)
            _write_json(se, es)
        if done not in hist["snapshots"]:
            hist["snapshots"].append(done)

    if start_epoch == 0 and 0 in tr["snapshot_epochs"] and 0 not in hist["snapshots"]:
        take_snapshot(0)                                       # what the starting weights give, before any step
    for net in nets:
        net.train()
    status = "running"
    t_start = t_ck = t_print = t_prog = time.perf_counter()
    for epoch in range(start_epoch, a["epochs"]):
        t0 = time.perf_counter()
        order = rng.permutation(len(items))
        loss_sum, comp_sum = 0.0, 0.0
        for i in order:
            if launcher_gone():
                _note(run, "stopped: the launching process has ended")
                raise SystemExit("the launching process has ended; the run resumes from its checkpoint")
            for which in range(1 + n_comp):                # the member, then the steps on the companion mesh
                it = items.get(int(i)) if which == 0 else items2.get(int(rng.integers(len(items2))))
                loss, _ = step_loss(cfg, nets, it, rng, dev, under if which == 0 else None)
                if not torch.isfinite(loss):
                    status = f"non-finite loss at step {step + 1}"
                    break
                opt.zero_grad(set_to_none=True)
                loss.backward()
                _, ratio, scale = cap_encoder_gradient(enc, window, cap)
                if scale is not None:
                    hist["cap_events"].append([step + 1, round(ratio, 3)])
                if ratio is not None and ratio > cap["burst_factor"]:
                    hist["bursts"].append([step + 1, round(ratio, 3)])
                torch.nn.utils.clip_grad_norm_(params, tr["clip"])
                opt.step()
                sched.step()
                step += 1
                if avg:
                    with torch.no_grad():
                        for x, one in zip(decays, avg):
                            for net, e in zip(nets, one):
                                for k, p in net.named_parameters():
                                    e[k].lerp_(p, 1.0 - x)
                if which == 0:
                    loss_sum += float(loss.detach())
                else:
                    comp_sum += float(loss.detach())
            if status != "running":
                break
        if status != "running":
            break
        if dev.type == "cuda":
            torch.cuda.synchronize()
        hist["loss"].append(loss_sum / len(items))
        if n_comp:
            hist.setdefault("companion_loss", []).append(comp_sum / (len(items) * n_comp))
        hist["epoch_seconds"].append(round(time.perf_counter() - t0, 2))
        done = epoch + 1
        last = done == a["epochs"]
        if done in tr["snapshot_epochs"]:
            take_snapshot(done)
        now = time.perf_counter()
        out_of_time = max_hours is not None and (now - t_start) >= max_hours * 3600.0
        stop = (stop_after_epoch is not None and done >= stop_after_epoch) or out_of_time
        if last or stop or (now - t_ck) >= checkpoint_minutes * 60.0:
            checkpoint(done)
            t_ck = time.perf_counter()
        if last or stop or (now - t_prog) >= 60.0:
            progress("paused" if (stop and not last) else "running")
            t_prog = now
        if last or stop or (now - t_print) >= 30.0:
            print(f"epoch {done}/{a['epochs']} step {step} loss {hist['loss'][-1]:.6g} "
                  f"{hist['epoch_seconds'][-1]} s; cap events {len(hist['cap_events'])}, bursts "
                  f"{len(hist['bursts'])}", flush=True)
            t_print = now
        if stop and not last:
            _note(run, f"paused after epoch {done}")
            return dict(hist, status="paused")
    hist["status"] = "finished" if status == "running" else status
    hist["steps"] = step
    if dev.type == "cuda":
        hist["peak_memory_GiB"] = torch.cuda.max_memory_allocated() / 2 ** 30
    _write_json(hp, hist)
    progress(hist["status"])
    if hist["status"] == "finished" and not predictions_written(run) and not predict(cfg, nets, data_dir, run, dev, under):
        hist["status"] = "non-finite predictions"
        _write_json(hp, hist)
    if hist["status"] == "finished":                           # each average is predicted as the run itself was
        for x, one, re in zip(decays, avg, runs_e):
            he = dict(hist, weights=json.loads((re / "average.json").read_text()))
            if not predictions_written(re):
                with averaged(nets, one):
                    if not predict(cfg, nets, data_dir, re, dev, under):
                        he["status"] = "non-finite predictions"
            _write_json(re / "history.json", he)
            _write_json(re / "progress.json", {
                "time": _now(), "state": he["status"], "preset": cfg.get("preset"), "seed": seed,
                "epoch": len(hist["loss"]), "epochs": a["epochs"], "step": step, "total_steps": total,
                "loss": hist["loss"], "epoch_seconds": hist["epoch_seconds"], "cap_events": len(hist["cap_events"]),
                "bursts": len(hist["bursts"]), "members_built": items.built, "weights": he["weights"]})
            _note(run, f"average with decay {x}: " + he["status"])
    _note(run, "ended: " + hist["status"])
    return hist
