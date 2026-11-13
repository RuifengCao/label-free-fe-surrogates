"""Multi-amplitude (subspace) condensed reading: feasibility test (exploratory, after the verdict of G-C2.1; no stamp).

For a member and a target level D_i the reading is the minimiser of the energy over the fields

    z = z_0 + sum_j C_ij s_i b_j,     b_j = (z(D_j) - z_0) / |z(D_j) - z_0|,   s_i = |z(D_i) - z_0|,

with the contact unknowns clamped at zero, where z(D_j) are the network's own fields of the same member at the basis
levels and z_0 its field at D = 0.1 mm. No label enters a reading. The one-amplitude condensed reading is the special
case C_ij = a_i for j = i and 0 otherwise, so the minimum over the subspace cannot lie above it (exact minimisation).
Start: the raw field (C_ii = 1). Optimiser: L-BFGS on sum_i Pi_i / Pi_i(start); for each target the lowest energy
seen is kept, so every reported energy is at or below the raw energy.

Judging as in dev/evalcond.py (F / F*(e) - 1 against the member's exact curve in eval_ref.json; energy gap).

    python subspace_eval.py --base C2DEV_DIR --state STATE.pt --name NAME [--ids a,b,c | --part I/N]
                            [--basis gate | 0.5,1,...] [--evals 60] [--out DIR]
"""
import argparse
import json
import sys
import time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--base", required=True, help="the c2dev directory (code/, data/, dev/)")
ap.add_argument("--state", required=True)
ap.add_argument("--name", required=True)
ap.add_argument("--ids", default=None)
ap.add_argument("--part", default=None)
ap.add_argument("--basis", default="gate")
ap.add_argument("--evals", type=int, default=60)
ap.add_argument("--history", type=int, default=30)
ap.add_argument("--ref", default=None)
ap.add_argument("--out", default=".")
ap.add_argument("--device", default="cpu")
args = ap.parse_args()
BASE = Path(args.base)
sys.path.insert(0, str(BASE / "code" / "joint"))
sys.path.insert(0, str(BASE / "code" / "repo" / "src"))
sys.path.insert(0, str(BASE / "dev"))

import numpy as np  # noqa: E402
import torch  # noqa: E402
from scipy.interpolate import PchipInterpolator  # noqa: E402

from c2.config import config  # noqa: E402
from c2.model import build, field  # noqa: E402
from c2.train import _prepare, MATMUL_PRECISION  # noqa: E402

D_BASE = 0.1
torch.set_float32_matmul_precision(MATMUL_PRECISION)
cfg = config()
dev = torch.device(args.device)
ref = json.loads(Path(args.ref or BASE / "eval_ref.json").read_text())
ids = list(ref["members"])
if args.ids:
    ids = [i.strip() for i in args.ids.split(",")]
if args.part:
    i, n = (int(v) for v in args.part.split("/"))
    ids = ids[i::n]
targets = [float(v) for v in ref["levels_mm"]]
basis = targets if args.basis == "gate" else sorted({float(v) for v in args.basis.split(",")} | set(targets))
own = [basis.index(D) for D in targets]                     # the basis vector of each target's own level

torch.serialization.add_safe_globals([torch.torch_version.TorchVersion])
try:
    st = torch.load(args.state, map_location="cpu", weights_only=True)
except Exception:
    st = torch.load(args.state, map_location="cpu", weights_only=False)
probe = _prepare(cfg, str(BASE / "data"), ids[:1], dev, energy=False, labels=False)[0]
torch.manual_seed(0)
nets = build(cfg, probe["base"].shape[-1] + 1)
for net, k in zip(nets, ("enc", "dec", "head")):
    net.load_state_dict(st[k])
    net.to(dev).eval()
nb = cfg["training"]["bubble_newton_steps"]
ks = float(ref["k_s"])
out_path = Path(args.out) / f"{args.name}.json"
res = json.loads(out_path.read_text())["members"] if out_path.exists() else {}

for iid in ids:
    if iid in res:
        continue
    t0 = time.time()
    it = _prepare(cfg, str(BASE / "data"), [iid], dev, energy=True, labels=False)[0]
    mp, E = it["maps"], it["energy"]
    nonneg = torch.cat([mp["nonneg"], torch.zeros(mp["n_z"] - mp["nonneg"].numel(), dtype=torch.bool, device=dev)])
    lv = torch.as_tensor([D_BASE] + basis, dtype=torch.float32, device=dev)
    with torch.no_grad():
        zall = field(*nets, it["base"], mp, lv, cfg["map"]["T"], lift=cfg["model"]["lift"] == "web")
    z0, zb = zall[0], zall[1:]
    B = zb - z0
    norms = B.norm(dim=1)
    Bn = B / norms[:, None]
    s = norms[own]                                          # (T,)
    Dt = torch.as_tensor(targets, dtype=torch.float32, device=dev)
    T, K = len(targets), len(basis)
    C = torch.zeros(T, K, device=dev)
    C[torch.arange(T), own] = 1.0
    C.requires_grad_(True)

    def fields(Cm):
        zc = z0 + (Cm * s[:, None]) @ Bn
        return torch.where(nonneg, zc.clamp_min(0.0), zc)

    with torch.no_grad():
        Pi0 = E.energy(fields(C), Dt, iters=nb)
    best = {"Pi": Pi0.clone(), "C": C.detach().clone()}
    trace, n_eval = [], [0]
    opt = torch.optim.LBFGS([C], lr=1.0, max_iter=args.evals, max_eval=args.evals, history_size=args.history,
                            line_search_fn="strong_wolfe", tolerance_grad=1e-10, tolerance_change=1e-14)

    def closure():
        opt.zero_grad()
        Pi = E.energy(fields(C), Dt, iters=nb)
        f = (Pi / Pi0).sum()
        f.backward()
        with torch.no_grad():
            ok = torch.isfinite(Pi) & (Pi < best["Pi"])
            best["Pi"] = torch.where(ok, Pi, best["Pi"])
            best["C"] = torch.where(ok[:, None], C.detach(), best["C"])
        n_eval[0] += 1
        trace.append(float(f))
        return f

    try:
        opt.step(closure)
    except Exception as exc:                                # keep what was found
        print(f"{iid}: optimiser stopped: {exc}", flush=True)
    with torch.no_grad():
        zc = fields(best["C"])
        Pis = E.energy(zc, Dt, iters=nb)
        zr = fields(torch.eye(K, device=dev)[own])
    m = ref["members"][iid]
    curve = PchipInterpolator(np.asarray(m["curve_e"]), np.asarray(m["curve_F"]), extrapolate=True)
    rows = []
    for l, D in enumerate(targets):
        row = {"D": D}
        for key, e, Pi in (("raw", float(zr[l, -1]), float(Pi0[l])), ("sub", float(zc[l, -1]), float(Pis[l]))):
            row[key] = {"J": 4 * ks * (D - e) / float(curve(e)) - 1, "e_err": e / m["e"][l] - 1, "gap": Pi / m["Pi"][l] - 1}
        rows.append(row)
    res[iid] = {"mechanism": m["mechanism"], "rows": rows, "C": best["C"].tolist(), "evals": n_eval[0],
                "trace": [trace[0], trace[-1], min(trace)], "seconds": round(time.time() - t0, 1)}
    out_path.write_text(json.dumps({"name": args.name, "state": args.state, "basis": basis, "evals": args.evals, "members": res}))
    tail = "  ".join(f"D={r['D']:g}: {100 * r['raw']['J']:6.1f}->{100 * r['sub']['J']:6.1f}" for r in rows if r["D"] >= 3)
    print(f"{iid} mech {m['mechanism']} evals {n_eval[0]} {time.time() - t0:5.0f} s | J raw->sub  {tail}", flush=True)
    del it, E
