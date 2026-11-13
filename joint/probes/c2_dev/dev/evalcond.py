"""Readings and judging of a model on the 64 former held-out members of G-C2.1 (exploratory development code, after
the verdict; not under any stamp; no verdict changes).

evaluate_model: for every member and evaluation level, the raw field and the amplitude-condensed field
(dev/condense.py; no reference solution enters a reading) with their end displacements and energies (float32, the
training energy).
judge: the gate's judged quantity for each reading, F / F*(e) - 1 with F = 4 k_s (D - e) and F*(e) interpolated
(monotone, PCHIP) through the member's exact points in eval_ref.json; the gate itself solves F*(e) exactly, and the
interpolation agrees with exact solves to 0.03% (90th percentile) for end displacements above 1 mm. Also the energy
gap against the exact energy. Summaries over the 448 pairs as in the gate (C1: median, C2: 90th percentile), by level
and by governing mechanism."""
import json
from pathlib import Path

import numpy as np

D_BASE = 0.1


def evaluate_model(cfg, nets, data_dir, ref: dict, dev, read_evals: int = 12, a_min: float = 0.5, a_max: float = 3.0,
                   ids=None, fields_path=None) -> dict:
    import torch

    from c2.model import field
    from c2.train import _prepare
    from condense import condense

    ids = list(ref["members"]) if ids is None else list(ids)
    lv = torch.as_tensor([D_BASE] + list(ref["levels_mm"]), dtype=torch.float32, device=dev)
    nb = cfg["training"]["bubble_newton_steps"]
    for net in nets:
        net.eval()
    out, fields = {}, {}
    for iid in ids:
        it = _prepare(cfg, data_dir, [iid], dev, energy=True, labels=False)[0]
        mp, E = it["maps"], it["energy"]
        nonneg = torch.cat([mp["nonneg"], torch.zeros(mp["n_z"] - mp["nonneg"].numel(), dtype=torch.bool, device=dev)])
        with torch.no_grad():
            zall = field(*nets, it["base"], mp, lv, cfg["map"]["T"], lift=cfg["model"]["lift"] == "web")
        z0, z, D = zall[:1].expand(len(lv) - 1, -1), zall[1:], lv[1:]
        a, info = condense(E, z0, z, D, nonneg, nb, a_min, a_max, read_evals)
        with torch.no_grad():
            zc = z0 + a[:, None] * (z - z0)
            zc = torch.where(nonneg, zc.clamp_min(0.0), zc)
            Pr, Pc = E.energy(z, D, iters=nb), E.energy(zc, D, iters=nb)
        out[iid] = {"e_raw": z[:, -1].double().tolist(), "e_cond": zc[:, -1].double().tolist(),
                    "Pi_raw": Pr.double().tolist(), "Pi_cond": Pc.double().tolist(), "a": a.double().tolist(),
                    "rel_slope": info["rel_slope"].double().tolist(), "at_bound": [bool(v) for v in info["at_bound"]],
                    "converged": [bool(v) for v in info["converged"]], "evals": info["evals"]}
        if fields_path is not None:
            fields[iid] = z.float().cpu().numpy()
            fields[iid + "__c"] = zc.float().cpu().numpy()
        del it, E
    for net in nets:
        net.train()
    if fields_path is not None:
        tmp = Path(str(fields_path) + ".tmp")
        with open(tmp, "wb") as fh:
            np.savez_compressed(fh, **fields)
        tmp.replace(fields_path)
    return out


def judge(res: dict, ref: dict) -> dict:
    """Rows (one per member and level) and summaries of the two readings."""
    from scipy.interpolate import PchipInterpolator

    ks, rows = float(ref["k_s"]), []
    for iid, r in res.items():
        m = ref["members"][iid]
        curve = PchipInterpolator(np.asarray(m["curve_e"]), np.asarray(m["curve_F"]), extrapolate=True)
        for l, D in enumerate(m["D"]):
            row = {"id": iid, "D": D, "mechanism": m["mechanism"], "m": m["e"][l] / (D - m["e"][l]), "a": r["a"][l]}
            for k in ("raw", "cond"):
                e = r[f"e_{k}"][l]
                row[k] = {"J": 4 * ks * (D - e) / float(curve(e)) - 1, "e_err": e / m["e"][l] - 1,
                          "gap": r[f"Pi_{k}"][l] / m["Pi"][l] - 1}
            rows.append(row)

    def stats(sel, k):
        J = np.abs([x[k]["J"] for x in sel])
        if not len(J):
            return None
        return {"n": int(len(J)), "median": float(np.median(J)), "p90": float(np.quantile(J, 0.9)),
                "over_10": int((J > 0.1).sum()), "gap_median": float(np.median([x[k]["gap"] for x in sel])),
                "e_err_abs_median": float(np.median(np.abs([x[k]["e_err"] for x in sel])))}

    names = ref["mechanism_names"]
    summ = {}
    for k in ("raw", "cond"):
        s = {"all": stats(rows, k)}
        for D in ref["levels_mm"]:
            s[f"D={D:g}"] = stats([x for x in rows if x["D"] == D], k)
        for j in sorted({x["mechanism"] for x in rows}):
            s[names[j]] = stats([x for x in rows if x["mechanism"] == j], k)
            s[names[j] + ", D>=6"] = stats([x for x in rows if x["mechanism"] == j and x["D"] >= 6], k)
        summ[k] = s
    solve = {"not_converged": int(sum((not c) for r in res.values() for c in r["converged"])),
             "at_bound": int(sum(b for r in res.values() for b in r["at_bound"])),
             "rel_slope_max": float(max(s for r in res.values() for s, b in zip(r["rel_slope"], r["at_bound"]) if not b)),
             "a_min": float(min(min(r["a"]) for r in res.values())), "a_max": float(max(max(r["a"]) for r in res.values()))}
    return {"rows": rows, "summary": summ, "solve": solve}


def line(tag: str, summ: dict) -> str:
    def f(s):
        return f"C1 {100 * s['median']:.2f}% C2 {100 * s['p90']:.2f}% over10 {s['over_10']}/{s['n']}"
    return f"{tag}: raw {f(summ['raw']['all'])} | condensed {f(summ['cond']['all'])}"


def report(tag: str, jd: dict) -> str:
    out = [line(tag, jd["summary"])]
    for key in jd["summary"]["cond"]:
        if key == "all":
            continue
        r, c = jd["summary"]["raw"][key], jd["summary"]["cond"][key]
        out.append(f"    {key:32s} n {c['n']:3d} | raw med {100 * r['median']:6.2f} p90 {100 * r['p90']:6.2f} over10 {r['over_10']:3d}"
                   f" | condensed med {100 * c['median']:6.2f} p90 {100 * c['p90']:6.2f} over10 {c['over_10']:3d}"
                   f" | gap med raw {100 * r['gap_median']:5.2f} condensed {100 * c['gap_median']:5.2f}")
    s = jd["solve"]
    out.append(f"    amplitude solve: a from {s['a_min']:.3f} to {s['a_max']:.3f}; not converged {s['not_converged']}; at a bound "
               f"{s['at_bound']}; largest relative slope {s['rel_slope_max']:.1e}")
    return "\n".join(out)
