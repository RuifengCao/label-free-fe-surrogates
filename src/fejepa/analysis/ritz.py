"""cmame-paper Stage 14: the per-instance polynomial Ritz-Galerkin baseline and
the enriched c* reading, post hoc (no pre-registration; no verdict reads
them). Their specification was fixed on 20 October 2026, before any paired
computation on the manuscript's instances, after exploratory readings on
freshly drawn instances and on wp9's sets (BRANCH_NOTES_cmame-paper.md,
Stage 14, gives it in full):

* Baseline (the specification's Appendix 1). Per instance, the Ritz-Galerkin
  projection of the finite-element problem on a vector polynomial subspace,
  with the instance's own K and F: per displacement component the functions
  (x/W) L_a(2x/W - 1) L_b(2y/H - 1) [L_c(2z/D - 1)], L the Legendre
  polynomials, W, H, D the bounding box's edge lengths, a + b (+ c) <= p - 1;
  they vanish on the clamped face x = 0. A = P^T K P is pseudo-inverted by
  its eigendecomposition, the directions with eigenvalue at most 1e-13 times
  the largest dropped, without scaling. No label, no training, nothing tuned
  on the manuscript's instances. The whole ladder is reported: 3D p = 6, 7,
  8, 9 (168, 252, 360, 495 unknowns), 2D p = 6, 8 (42, 72).
* Enriched c* (Appendix 2; exploratory, not in the manuscript). Per instance
  and load case, the Ritz projection on span{u} + range(P) of a network's
  prediction u and the coarse space of Appendix 1 at 2D p = 6 (42 unknowns),
  3D p = 8 (360), beside the network scaled by c* (the projection on
  span{u}) and the Ritz solution of that coarse space (the projection on
  range(P)). The Galerkin system of the enriched space has u's column in a
  scale of its own; it is solved with Jacobi scaling and the eigenvalues at
  most 1e-12 times the largest dropped (the reference script's solve; the
  appendix leaves it open). Since both spaces lie in the enriched one, its
  energy gap is at most the smaller of theirs (up to round-off).

Everything here is numpy and scipy; the metrics are the repository's
(fejepa.metrics per load case, fejepa.analysis.holdout.worse_than_zero).
"""

from __future__ import annotations

import json
import os
import time
from math import comb
from pathlib import Path

import numpy as np

CUT = 1e-13
"""Appendix 1: eigenvalues of A = P^T K P at most CUT x the largest are dropped."""
LADDER = {3: (6, 7, 8, 9), 2: (6, 8)}
"""Appendix 1: the polynomial degrees p (a + b (+ c) <= p - 1) reported, all of them."""
ENRICHED_DEGREE = {2: 6, 3: 8}
"""Appendix 2: the coarse space of the enriched reading (2D 42, 3D 360 unknowns)."""
ENRICHED_CUT = 1e-12
"""The enriched solve's eigenvalue cut, after Jacobi scaling (the reference script's)."""
ID_TOL = 1e-6
"""Appendix 1: an instance is the recorded one when its size matches and its
||U*||_K per load case differs from the record by at most this (relative)."""
FIELDS = ("disp_rel_l2", "energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err", "crit_recall")
"""The frozen suite's five metrics (fejepa.metrics.FIELD_KEYS), in its order."""
HIGHER_IS_BETTER = ("crit_recall",)
INBAND_FACTOR = 0.8
"""Appendix 2, in band: complementary when, for each seed, the median enriched
gap is at most this times the smaller of the medians of c* u and of Ritz."""
OOD_PEAK_FACTOR = 0.5
"""Appendix 2, out of distribution: complementary when the enriched peak-stress
error's median is at most this times Ritz's."""


def n_unknowns(dim: int, p: int) -> int:
    """dim x the number of exponent tuples with a + b (+ c) <= p - 1."""
    return int(dim * comb(p - 1 + dim, dim))


# ------------------------------------------------------------------ basis --

def scalar_basis(nodes: np.ndarray, dims, pmax: int):
    """The scalar functions (x/W) L_a(2x/W - 1) L_b(2y/H - 1) [L_c(2z/D - 1)],
    a + b (+ c) <= pmax - 1, at `nodes`, columns in the order (a, b[, c]);
    returns (Phi (n, m), total degree of each column)."""
    from numpy.polynomial import legendre as npleg

    d = nodes.shape[1]
    s = [np.asarray(nodes[:, k], dtype=np.float64) / float(dims[k]) for k in range(d)]
    V = [npleg.legvander(2.0 * s[k] - 1.0, pmax - 1) for k in range(d)]
    cols, deg = [], []
    if d == 2:
        for a in range(pmax):
            for b in range(pmax - a):
                cols.append(s[0] * V[0][:, a] * V[1][:, b])
                deg.append(a + b)
    else:
        for a in range(pmax):
            for b in range(pmax - a):
                for c in range(pmax - a - b):
                    cols.append(s[0] * V[0][:, a] * V[1][:, b] * V[2][:, c])
                    deg.append(a + b + c)
    return np.stack(cols, 1), np.asarray(deg)


def bounding_box(arch) -> tuple:
    """(W, H[, D]) from the instance's metadata, checked against its nodes: the
    mesh spans [0, W] x [0, H] (x [0, D]) and every Dirichlet dof sits on x = 0
    (ValueError otherwise)."""
    ex = arch.meta["extra"]
    d = arch.nodes.shape[1]
    dims = (float(ex["width"]), float(ex["height"])) + ((float(ex["depth"]),) if d == 3 else ())
    lo, hi = arch.nodes.min(0), arch.nodes.max(0)
    if not (np.allclose(lo, 0.0, atol=1e-8) and np.allclose(hi, dims, rtol=0.0, atol=1e-8)):
        raise ValueError(f"the mesh's bounding box {lo.tolist()}-{hi.tolist()} is not "
                         f"[0, {list(dims)}]")
    dn = np.unique(np.nonzero(np.asarray(arch.dirichlet_mask, bool))[0] // d)
    if dn.size == 0 or not np.allclose(arch.nodes[dn, 0], 0.0, atol=1e-8):
        raise ValueError("the Dirichlet dofs are not on the face x = 0")
    return dims


def free_nodes(arch) -> np.ndarray:
    """The nodes whose dofs are free. The Dirichlet set must be node-wise (all
    components of a clamped node), so the free dofs are (node, component)
    pairs in node-major order and component c of the free block is rows c::d."""
    d = arch.nodes.shape[1]
    dm = np.asarray(arch.dirichlet_mask, bool).reshape(-1, d)
    if not np.all(dm.all(1) | ~dm.any(1)):
        raise ValueError("the Dirichlet set is not node-wise")
    return np.nonzero(~dm[:, 0])[0]


def free_block(arch):
    """(K_ff (CSR), F_f (L, n_free)) on the free dofs."""
    import scipy.sparse as sp

    free = np.asarray(arch.free_mask, bool)
    return (sp.csr_matrix(arch.K)[free][:, free].tocsr(),
            np.atleast_2d(np.asarray(arch.F, dtype=np.float64))[:, free])


def pinv_solve(A: np.ndarray, B: np.ndarray, cut: float = CUT):
    """A^+ B by the eigendecomposition of the symmetric A, the directions with
    eigenvalue at most cut x the largest dropped, no scaling (Appendix 1);
    returns (X, dropped)."""
    import scipy.linalg as sla

    w, V = sla.eigh(A)
    keep = w > w.max() * cut
    return V[:, keep] @ ((V[:, keep].T @ B) / w[keep][:, None]), int((~keep).sum())


def coarse_system(arch, pmax: int, Kff, Ff, t: dict | None = None):
    """Phi on the free nodes (n_free_nodes, m) with each column's degree,
    A = P^T K P (d m, d m) and P^T F (d m, L) of the subspace of degree pmax,
    formed per component block without forming P (columns component-major:
    c m + j). `t` receives the times of the basis and of the products."""
    import time as _time

    d = arch.nodes.shape[1]
    t = {} if t is None else t
    t0 = _time.perf_counter()
    fn = free_nodes(arch)
    Phi, deg = scalar_basis(arch.nodes[fn], bounding_box(arch), pmax)
    m = Phi.shape[1]
    t["basis"] = _time.perf_counter() - t0
    t0 = _time.perf_counter()
    Kc = Kff.tocsc()
    A = np.empty((d * m, d * m))
    for e in range(d):
        T = np.asarray(Kc[:, e::d] @ Phi)                         # (nf, m)
        for c in range(d):
            A[c * m:(c + 1) * m, e * m:(e + 1) * m] = Phi.T @ T[c::d]
    A = 0.5 * (A + A.T)
    B = np.vstack([Phi.T @ Ff[:, c::d].T for c in range(d)])      # (d m, L)
    t["kp"] = _time.perf_counter() - t0
    return Phi, deg, A, B


def reconstruct(arch, Phi, sel, v, n_loads: int) -> np.ndarray:
    """U (L, ndof) = P v for the columns `sel` (component-major indices into
    the d m columns of Phi's subspace), zero on the Dirichlet dofs."""
    d = arch.nodes.shape[1]
    m = Phi.shape[1]
    cols, comp = sel % m, sel // m
    nf = int(np.count_nonzero(arch.free_mask))
    Uf = np.empty((n_loads, nf))
    for c in range(d):
        j = comp == c
        Uf[:, c::d] = (Phi[:, cols[j]] @ v[j]).T
    U = np.zeros((n_loads, arch.ndof))
    U[:, np.asarray(arch.free_mask, bool)] = Uf
    return U


def ritz_ladder(arch, ladder, Kff=None, Ff=None):
    """The Ritz solutions for every p of the ladder. The subspaces are nested,
    so A and P^T F are formed once for the largest p and each p takes its
    principal sub-block (the "kp" time is that of the largest p). Returns
    ({p: (U (L, ndof), dropped directions, unknowns)}, times)."""
    import time as _time

    d = arch.nodes.shape[1]
    t = {}
    if Kff is None:
        Kff, Ff = free_block(arch)
    Phi, deg, A, B = coarse_system(arch, max(ladder), Kff, Ff, t)
    degs = np.tile(deg, d)
    out = {}
    for p in ladder:
        t0 = _time.perf_counter()
        sel = np.nonzero(degs <= p - 1)[0]
        v, dropped = pinv_solve(A[np.ix_(sel, sel)], B[sel])
        t[f"solve_{p}"] = _time.perf_counter() - t0
        t0 = _time.perf_counter()
        U = reconstruct(arch, Phi, sel, v, Ff.shape[0])
        t[f"recon_{p}"] = _time.perf_counter() - t0
        out[p] = (U, dropped, int(sel.size))
    return out, t


# ------------------------------------------------------------ enriched c* --

def coarse(arch, p: int, Kff=None, Ff=None) -> dict:
    """The coarse space of degree p on one instance: Phi on the free nodes,
    A = P^T K P, P^T F, the free block and mask."""
    if Kff is None:
        Kff, Ff = free_block(arch)
    Phi, _, A, B = coarse_system(arch, p, Kff, Ff)
    return {"d": arch.nodes.shape[1], "Kff": Kff, "Ff": Ff, "Phi": Phi, "m": Phi.shape[1],
            "A": A, "B": B, "free": np.asarray(arch.free_mask, bool), "ndof": arch.ndof}


def P_apply(C: dict, coef: np.ndarray) -> np.ndarray:
    """P coef on the free dofs: coef (d m, L) -> (L, n_free)."""
    d, m, Phi = C["d"], C["m"], C["Phi"]
    out = np.empty((coef.shape[1], Phi.shape[0] * d))
    for c in range(d):
        out[:, c::d] = (Phi @ coef[c * m:(c + 1) * m]).T
    return out


def Pt_apply(C: dict, Y: np.ndarray) -> np.ndarray:
    """P^T y on the free dofs: Y (L, n_free) -> (d m, L)."""
    d, Phi = C["d"], C["Phi"]
    return np.vstack([Phi.T @ Y[:, c::d].T for c in range(d)])


def ritz_coarse(C: dict):
    """Appendix 1's solve on the coarse space: (U_free (L, n_free), dropped)."""
    v, dropped = pinv_solve(C["A"], C["B"])
    return P_apply(C, v), dropped


def pinv_scaled(G: np.ndarray, rhs: np.ndarray, rcut: float = ENRICHED_CUT):
    """G^+ rhs after Jacobi scaling, the eigenvalues at most rcut x the largest
    dropped; returns (solution, dropped)."""
    import scipy.linalg as sla

    dg = np.sqrt(np.clip(np.diag(G), 1e-300, None))
    Gs = G / dg[:, None] / dg[None, :]
    w, V = sla.eigh(Gs)
    keep = w > w.max() * rcut
    y = V[:, keep] @ ((V[:, keep].T @ (rhs / dg)) / w[keep])
    return y / dg, int((~keep).sum())


def enriched(C: dict, uf: np.ndarray):
    """The Ritz projection on span{u} + range(P), per load case: uf
    (L, n_free) -> (U_free (L, n_free), dropped directions per load case)."""
    Kff, Ff = C["Kff"], C["Ff"]
    uf = np.asarray(uf, dtype=np.float64)
    Ku = np.asarray((Kff @ uf.T).T)
    uKu = np.einsum("li,li->l", uf, Ku)
    Fu = np.einsum("li,li->l", Ff, uf)
    PtKu = Pt_apply(C, Ku)
    n = C["A"].shape[0]
    out = np.empty_like(uf)
    dropped = []
    for j in range(uf.shape[0]):
        G = np.empty((n + 1, n + 1))
        G[0, 0] = uKu[j]
        G[0, 1:] = PtKu[:, j]
        G[1:, 0] = PtKu[:, j]
        G[1:, 1:] = C["A"]
        coef, dr = pinv_scaled(G, np.concatenate([[Fu[j]], C["B"][:, j]]))
        out[j] = coef[0] * uf[j] + P_apply(C, coef[1:, None])[0]
        dropped.append(dr)
    return out, dropped


def full_field(C: dict, Uf: np.ndarray) -> np.ndarray:
    """(L, n_free) -> (L, ndof), zero on the Dirichlet dofs."""
    U = np.zeros((Uf.shape[0], C["ndof"]))
    U[:, C["free"]] = Uf
    return U


# ---------------------------------------------------------------- metrics --

def metrics(U: np.ndarray, arch) -> dict:
    """The repository's five metrics per load case (fejepa.metrics), their
    means over the load battery (as fejepa.metrics.evaluate_fields gives them
    and the records hold them), and the load cases worse than the zero field
    (fejepa.analysis.holdout.worse_than_zero)."""
    from ..anchor.energy import pi_h
    from ..metrics import displacement_errors, energy_gap_rel, vm_suite
    from .holdout import worse_than_zero

    vm = vm_suite(U, arch)
    per = {"disp_rel_l2": displacement_errors(U, arch), "energy_gap_rel": energy_gap_rel(U, arch),
           "vm_rel_l2": vm["vm_rel_l2"], "peak_vm_rel_err": vm["peak_vm_rel_err"],
           "crit_recall": vm["crit_recall"]}
    return {"load": {k: [float(x) for x in v] for k, v in per.items()},
            "mean": {k: float(np.mean(v)) for k, v in per.items()},
            "worse_than_zero": worse_than_zero(per["energy_gap_rel"], pi_h(U, arch.K, arch.F))}


def ustar_norm_K(Kff, Us_free: np.ndarray) -> np.ndarray:
    """Per load case ||U*||_K over the free dofs."""
    Us_free = np.atleast_2d(Us_free)
    return np.sqrt(np.einsum("li,li->l", Us_free, np.asarray((Kff @ Us_free.T).T)))


def identity(size_ok: bool, norms: np.ndarray, ref) -> dict:
    """The identity check of Appendix 1: the size as recorded and ||U*||_K per
    load case within ID_TOL (relative) of the record."""
    ref = np.asarray(ref, dtype=float)
    norms = np.asarray(norms, dtype=float)
    rel = (float(np.max(np.abs(norms - ref) / np.maximum(np.abs(ref), 1e-300)))
           if ref.shape == norms.shape else float("inf"))
    return {"ustar_norm_K_max_rel_diff": rel, "size_ok": bool(size_ok),
            "ok": bool(size_ok and rel <= ID_TOL)}


def paired_shares(mine: np.ndarray, ref: np.ndarray, field: str) -> dict:
    """The share of instances on which the Ritz value is better than the
    model's (strictly; ties counted apart)."""
    mine, ref = np.asarray(mine, dtype=float), np.asarray(ref, dtype=float)
    better = mine > ref if field in HIGHER_IS_BETTER else mine < ref
    return {"ritz_better_share": float(np.mean(better)), "ties": int(np.sum(mine == ref)),
            "model_median": float(np.median(ref)), "n": int(ref.size)}


# --------------------------------------------------------------- the files --

def sha256(path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_config(path) -> dict:
    """The configuration (configs/ritz_v1.json) with its top-level structure
    checked (ValueError otherwise)."""
    cfg = json.loads(Path(path).read_text())
    want = ("_comment", "spec", "out", "baseline", "enriched", "timing")
    if sorted(cfg) != sorted(want):
        raise ValueError(f"{path}: top-level keys {sorted(cfg)}, expected {sorted(want)}")
    sp = cfg["spec"]
    if (float(sp["cut"]) != CUT or {int(k): tuple(v) for k, v in sp["ladder"].items()} != LADDER
            or float(sp["id_tol"]) != ID_TOL
            or {int(k): int(v) for k, v in sp["enriched_degree"].items()} != ENRICHED_DEGREE
            or float(sp["enriched_cut"]) != ENRICHED_CUT
            or float(sp["inband_factor"]) != INBAND_FACTOR
            or float(sp["ood_peak_factor"]) != OOD_PEAK_FACTOR):
        raise ValueError(f"{path}: spec {sp} is not the code's (Appendix 1 and 2)")
    return cfg


def checked(path, want: str | None, what: str) -> Path:
    """`path`, refused (ValueError) unless it is a file with SHA-256 `want`."""
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"{what}: {p} is missing")
    got = sha256(p)
    if want is not None and got != want:
        raise ValueError(f"{what}: {p} has SHA-256 {got[:12]}..., the configuration names "
                         f"{str(want)[:12]}...")
    return p


def complete_lines(path: Path) -> list:
    """The complete lines of a rows file; a last line cut by a kill is removed
    in place (os.truncate: the complete lines are never rewritten)."""
    path = Path(path)
    if not path.is_file():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        os.truncate(path, raw.rfind(b"\n") + 1)
        raw = path.read_bytes()
    return [json.loads(x) for x in raw.decode().splitlines() if x.strip()]


def append_row(fh, row: dict) -> None:
    fh.write(json.dumps(row) + "\n")
    fh.flush()
    os.fsync(fh.fileno())


def write_json(path, obj: dict) -> None:
    """Atomic JSON write (temp file, flushed to the disk, then os.replace)."""
    from .holdout import write_json_synced

    write_json_synced(path, obj)


def machine() -> dict:
    """The host, the libraries and the thread settings: the thread variables
    of the environment, the CPU affinity and, where threadpoolctl is
    installed, the BLAS and OpenMP pools with their thread counts (None
    otherwise), as the cost table's timing records them."""
    import platform

    import scipy

    out = {"python": platform.python_version(), "numpy": np.__version__,
           "scipy": scipy.__version__, "platform": platform.platform(),
           "cpu_count": os.cpu_count(), "hostname": platform.node(),
           "env_threads": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS",
                                                          "OPENBLAS_NUM_THREADS")}}
    try:
        from threadpoolctl import threadpool_info

        out["threadpools"] = [{k: p.get(k) for k in ("internal_api", "num_threads", "version")}
                              for p in threadpool_info()]
    except ImportError:
        out["threadpools"] = None
    try:
        out["affinity"] = len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        out["affinity"] = None
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                out["cpu"] = line.split(":", 1)[1].strip()
                break
    except OSError:
        out["cpu"] = None
    return out


def code_provenance(root) -> dict:
    """The checkout's commit, tree, `git describe` and whether tracked files
    differ from it."""
    import subprocess

    def git(*args):
        try:
            return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                                  text=True, check=True, timeout=60).stdout.strip()
        except Exception:                                  # noqa: BLE001
            return None

    status = git("status", "--porcelain", "--untracked-files=no")
    return {"commit": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"),
            "describe": git("describe", "--always", "--dirty", "--tags"),
            "tracked_changes": None if status is None else bool(status)}


def elapsed(t0: float) -> str:
    return f"{time.time() - t0:.0f} s"
