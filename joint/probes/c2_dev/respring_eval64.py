"""Exploratory check of one claim: with the amplitude-condensed reading, the distance from the reference curve is the
over-stiffness of the network's own ray of fields, so it does not fall when the loading spring is made softer.
Host's final label-free model of G-C2.1, seed 2; no retraining. For a member and a level of the member-scaled rule v0
(k' = F_est / (4 DELTA), D' = fraction of 9 mm): e* = exact end displacement under the new spring (from the member's
reference curve), D_old = the loading level of G-C2.1 with the same exact end displacement, ray = z0 + a (z(D_old) - z0).
Read the ray (a) raw, (b) condensed under the old spring at D_old, (c) condensed under the new spring at D'."""
import sys, json, time
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
sys.path.insert(0, str(paths.joint())); sys.path.insert(0, str(paths.src()))
import numpy as np, torch
from pathlib import Path
from scipy.optimize import brentq
from c2.config import config
from c2.model import build, field
from c2.train import _prepare, MATMUL_PRECISION
from common import eval_ids
from refcurve import points, curve
torch.set_num_threads(1); torch.set_float32_matmul_precision(MATMUL_PRECISION)
cfg = config(); DATA = str(paths.data()); dev = torch.device("cpu"); NB = cfg["training"]["bubble_newton_steps"]
torch.serialization.add_safe_globals([torch.torch_version.TorchVersion])
st = torch.load(paths.states() / "label_free_s2/state.pt", map_location="cpu", weights_only=True)
ids_all, par = eval_ids()
L, As, fyb = 80.0, 84.3, 880.0
x = json.load(open(paths.work() / "fit4.json"))["4.0"]["x"]; A = np.exp(x[:4]); p = float(np.exp(x[4]))
def modes(q):
    m = q["w"] / 2 - q["t_w"] / 2 - 0.8 * q["r"]; n = min(q["n"], 1.25 * m)
    Mpl = 0.25 * L * q["t_f"] ** 2 * q["fy"]; B = 4 * As * fyb
    return np.array([4 * Mpl / m, (2 * Mpl + n * B) / (m + n), B, q["t_w"] * L * q["fy"]])
def F_est(q): return float(((A * modes(q)) ** (-p)).sum() ** (-1 / p))
KS, DELTA, DMAX = 2.0e4, 4.0, 9.0; FR = [0.08, 0.17, 0.32, 0.44, 0.56, 0.80, 1.0]
ids = sys.argv[2].split(","); out_path = Path(paths.work() / f"proj64/rows_{sys.argv[1]}.jsonl")
nets = None


def condense(E, nonneg, z0, z, D, ks, iters=5):
    E.k_s = ks; d = z - z0
    def vg(a):
        a = a.clone().requires_grad_(True)
        zc = z0 + a[:, None] * d
        Pi = E.energy(torch.where(nonneg, zc.clamp_min(0.0), zc), D, iters=NB)
        g, = torch.autograd.grad(Pi.sum(), a)
        return Pi.detach(), g.detach()
    a0 = torch.ones(z.shape[0]); P0, g0 = vg(a0); best_a, best_P = a0.clone(), P0.clone()
    a1 = a0 - 0.03 * torch.sign(g0); P1, g1 = vg(a1)
    for _ in range(iters + 1):
        better = P1 < best_P; best_a, best_P = torch.where(better, a1, best_a), torch.where(better, P1, best_P)
        den = g1 - g0; den = torch.where(den.abs() < 1e-9, torch.full_like(den, 1e-9), den)
        a2 = (a1 - g1 * (a1 - a0) / den).clamp(0.4, 4.0)
        a0, g0 = a1, g1; P1, g1 = vg(a2); a1 = a2
    better = P1 < best_P; best_a = torch.where(better, a1, best_a)
    _, gb = vg(best_a)
    return best_a, gb


for iid in ids:
    t0 = time.time()
    it = _prepare(cfg, DATA, [iid], dev, energy=True, labels=False)[0]
    if nets is None:
        torch.manual_seed(0); nets = build(cfg, it["base"].shape[-1] + 1)
        for net, k in zip(nets, ("enc", "dec", "head")):
            net.load_state_dict(st[k]); net.eval()
    mp = it["maps"]; nonneg = torch.cat([mp["nonneg"], torch.zeros(mp["n_z"] - mp["nonneg"].numel(), dtype=torch.bool)])
    E = it["energy"]; assert abs(E.k_s - KS) < 1e-6
    pts = points(iid); C = curve(pts); em = max(pt[0] for pt in pts)
    kn = F_est(par[iid]) / (4 * DELTA)
    rows = []
    for fr in FR:
        Dn = fr * DMAX
        es = brentq(lambda t: t + float(C(min(t, em))) / (4 * kn) - Dn, 0.0, Dn)
        if es > em: continue                                    # beyond the member's solved range
        Fs = float(C(es)); Do = es + Fs / (4 * KS)
        if Do > 8.0 or Do < 0.1: continue                       # outside the levels the network was trained on
        rows.append(dict(fr=fr, Dn=Dn, es=es, Fs=Fs, Do=Do))
    if rows:
        lv = torch.as_tensor([0.1] + [r["Do"] for r in rows], dtype=torch.float32)
        with torch.no_grad():
            zall = field(*nets, it["base"], mp, lv, cfg["map"]["T"], lift=True)
        z0, z = zall[:1].expand(len(rows), -1), zall[1:]
        Do = lv[1:]; Dn = torch.as_tensor([r["Dn"] for r in rows], dtype=torch.float32)
        ao, go = condense(E, nonneg, z0, z, Do, KS); an, gn = condense(E, nonneg, z0, z, Dn, kn); E.k_s = KS
        e0 = z0[:, -1]; ez = z[:, -1]
        for j, r in enumerate(rows):
            ep = float(ez[j]); eo = float(e0[j] + ao[j] * (ez[j] - e0[j])); en = float(e0[j] + an[j] * (ez[j] - e0[j]))
            J = lambda e, D, k: 4 * k * (D - e) / float(C(e)) - 1
            r.update(m_old=r["es"] / (r["Do"] - r["es"]), m_new=r["es"] / (r["Dn"] - r["es"]), a_old=float(ao[j]), a_new=float(an[j]),
                     g_old=float(go[j]), g_new=float(gn[j]),
                     e_raw=ep / r["es"] - 1, e_old=eo / r["es"] - 1, e_new=en / r["es"] - 1,
                     J_raw_old=J(ep, r["Do"], KS), J_raw_new=J(ep, r["Dn"], kn), J_cond_old=J(eo, r["Do"], KS), J_cond_new=J(en, r["Dn"], kn))
    with open(out_path, "a") as fh:
        fh.write(json.dumps({"iid": iid, "k_new": kn, "rows": rows, "seconds": round(time.time() - t0, 1)}) + "\n")
