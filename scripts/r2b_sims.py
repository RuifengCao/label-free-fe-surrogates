#!/usr/bin/env python3
"""R2b (PREREG_R2B Sec. 5): properties of R2b's rule by simulation, recorded
before the stamp (records/wp9/r2b/simulations.json).

R2b's rule is R2a's (PREREG_FINE3D Sec. 6): S against the fresh baseline,
three seeds per arm, (i) the fine displacement error lower beyond the guard,
(ii) the fine / in-band displacement ratio lower beyond it, (iii) K1: neither
the in-band energy gap nor the in-band displacement error worse beyond it;
the guard is the E-series rule (rel = mean(new)/mean(ref) - 1 beyond tau =
max(10%, 2 x SE_rel)). Seed values are drawn log-normal around each arm's
true mean (scripts/fine3d_sims.py's draw, imported, not copied) with the
coefficients of variation of the Phase-2b transformer (records/wp8/e2/
baseline/report_phase2b.json, seeds 0-2: P3's fine and in-band displacement
errors, E8's in-band energy gap per seed) for both arms unless stated; a
seed's in-band displacement draw is the one both the ratio and K1 read (P3's
in-band pass reproduces E8's cell). S's true means are the baseline's times
(1 - d) on the fine set and (1 + d_in) in band.

  power      P(SUPPORTED) by S's true fine reduction d (0-90%) and its true
             change of the in-band errors d_in (both in-band metrics alike:
             +10%, 0, -10%, -30%, -50%, -70%).
  anchors    the effects the records suggest, each with its in-band
             displacement and energy-gap changes: c* on the transformer (wp8
             4e, records/wp8/posthoc/amp_phase2b.json: scaling each load case
             by its energy-optimal amplitude), the same fine reduction with the
             in band unchanged, S on the token bottleneck as R2a measured it
             (records/wp9/fine3d/fine3d_verdict.json), and that times k = the
             ratio of c*'s fine reductions on the transformer and the
             bottleneck (scripts/fine3d_sims.py's k, 0.87) on all three
             changes, and half of it; c* on the bottleneck, for reference;
             and k times S's fine reduction on the bottleneck with its in-band
             reductions as R2a measured them.
             For each: P(SUPPORTED), the share of trials in which each
             condition holds, and the observed fine rel's median and 5th and
             95th percentiles; with S's spreads 0.5 and 1.5 times the
             baseline's and at R2a's S arm's coefficients of variation; with
             the spreads drawn in every trial from their uncertainty given
             three seeds (fine3d_sims.spread_draws: sigma^2 = 2 s^2 / chi2_2,
             at most 4 times the estimate, one draw per metric shared by both
             arms); with both arms' spreads twice the estimates; with a
             correlation within a seed (rho 0.5 between its fine and in-band
             displacement errors and between its in-band displacement error
             and energy gap, rho^2 between the fine error and the energy gap);
             and on five seeds per arm.
  value      per anchor, the expected value of R2b on three and on five seeds
             per arm, a supported R2b worth v (1.5, 2 or 3) times the cost of
             six runs and a NOT SUPPORTED one nothing (PREREG_FINE3D Sec. 6's
             convention), five seeds costing 10/6 of six runs.

    python scripts/r2b_sims.py --out records/wp9/r2b/simulations.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

TRIALS = 200_000
SEED = 20261103
FINE3D_VERDICT = "records/wp9/fine3d/fine3d_verdict.json"
FINE_CUTS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
INBAND_CHANGES = (0.1, 0.0, -0.1, -0.3, -0.5, -0.7)
VALUES = (1.5, 2.0, 3.0)
SPREAD_CAP = 4.0
RHO = 0.5


def _f3():
    spec = importlib.util.spec_from_file_location("fine3d_sims", ROOT / "scripts" / "fine3d_sims.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


F3 = _f3()
KEYS = ("fine", "inband_disp", "inband_egap")


def spreads(rep: dict) -> dict:
    """The coefficients of variation of the three metrics R2b's rule reads
    (fine3d_sims' `spreads`)."""
    p3 = rep["results"]["p3_transfer"]["metrics"]["ar"]
    e8 = rep["results"]["e8"]["metrics"]["cells"]["ar"]["1024"]
    return {"fine": F3.cv(p3["fine"]["disp_rel_l2"]["per_seed"]),
            "inband_disp": F3.cv(p3["inband"]["disp_rel_l2"]["per_seed"]),
            "inband_egap": F3.cv(e8["energy_gap_rel"]["per_seed"])}


def _normals(rng, shape: tuple, rho: float):
    """Standard normals (trials, seeds, 3) for (fine, in-band displacement,
    in-band energy gap), correlated within a seed by the AR(1) matrix (rho,
    rho, rho^2) when rho > 0."""
    z = rng.standard_normal((*shape, 3))
    if rho:
        c = np.array([[1.0, rho, rho * rho], [rho, 1.0, rho], [rho * rho, rho, 1.0]])
        z = z @ np.linalg.cholesky(c).T
    return z


def rule(fb, ib, eb, fs, is_, es) -> tuple:
    """R2b's rule (R2a's) over trials: (supported, (i), (ii), (iii), the
    observed fine rel)."""
    lo_f, _, rel_f = F3.guard_vec(fb, fs)
    lo_r, _, _ = F3.guard_vec(fb / ib, fs / is_)
    _, wo_e, _ = F3.guard_vec(eb, es)
    _, wo_d, _ = F3.guard_vec(ib, is_)
    k1 = ~wo_e & ~wo_d
    return lo_f & lo_r & k1, lo_f, lo_r, k1, rel_f


def simulate(rng, cvs: dict, d: float, d_disp: float, d_egap: float, n: int = TRIALS,
             n_seeds: int = 3, s_mult: float = 1.0, cvs_s: dict | None = None,
             rho: float = 0.0, drawn: bool = False, both_mult: float = 1.0) -> dict:
    """One case: the baseline's spreads `cvs` (times `both_mult` for both
    arms); S's the baseline's times `s_mult`, or `cvs_s`; with `drawn`, each
    trial's spreads drawn from their uncertainty (spread_draws, capped at
    SPREAD_CAP, shared by both arms, S's then times `s_mult`)."""
    base = {k: both_mult * v for k, v in cvs.items()}
    if drawn:
        c_b = F3.spread_draws(rng, base, n, SPREAD_CAP)
    else:
        c_b = {k: np.full((n, 1), v) for k, v in base.items()}
    if cvs_s is not None:
        c_s = {k: np.full((n, 1), both_mult * v) for k, v in cvs_s.items()}
    else:
        c_s = {k: s_mult * v for k, v in c_b.items()}
    shape = (n, n_seeds)
    zb, zs = _normals(rng, shape, rho), _normals(rng, shape, rho)
    mean_s = {"fine": 1.0 - d, "inband_disp": 1.0 + d_disp, "inband_egap": 1.0 + d_egap}
    b = [F3.from_normal(zb[..., j], 1.0, c_b[k]) for j, k in enumerate(KEYS)]
    s = [F3.from_normal(zs[..., j], mean_s[k], c_s[k]) for j, k in enumerate(KEYS)]
    sup, c1, c2, c3, rel = rule(*b, *s)
    q = np.quantile(rel, (0.05, 0.5, 0.95))
    return {"p_supported": float(sup.mean()), "p_i": float(c1.mean()), "p_ii": float(c2.mean()),
            "p_iii": float(c3.mean()),
            "fine_rel_observed": {"q05": float(q[0]), "median": float(q[1]), "q95": float(q[2])}}


def anchors(amp_t: dict, amp_b: dict, r2a: dict, k: float) -> dict:
    """The effects the records suggest: (d, d_disp, d_egap)."""
    def cut(amp, name, a, b):
        sm = amp["seed_means"][name]
        return float(1.0 - sm[b] / sm[a])
    c_t = {"fine": cut(amp_t, "fine", "disp", "disp_c"),
           "inband_disp": -cut(amp_t, "inband", "disp", "disp_c"),
           "inband_egap": -cut(amp_t, "inband", "egap", "egap_c")}
    c = r2a["conditions"]
    s_b = {"fine": -float(c["fine_displacement"]["rel_change"]),
           "inband_disp": float(c["K1_inband_displacement"]["rel_change"]),
           "inband_egap": float(c["K1_inband_energy_gap"]["rel_change"])}
    c_bn = {"fine": cut(amp_b, "fine", "disp", "disp_c"),
            "inband_disp": -cut(amp_b, "inband", "disp", "disp_c"),
            "inband_egap": -cut(amp_b, "inband", "egap", "egap_c")}
    return {
        "c* on the transformer": c_t,
        "c* on the transformer, in band unchanged": dict(c_t, inband_disp=0.0, inband_egap=0.0),
        "S on the bottleneck (R2a)": s_b,
        "S on the bottleneck times k": {kk: k * v for kk, v in s_b.items()},
        "half of S on the bottleneck": {kk: 0.5 * v for kk, v in s_b.items()},
        "c* on the bottleneck (for reference)": c_bn,
        "S on the bottleneck times k on the fine set only": dict(s_b, fine=k * s_b["fine"])}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=TRIALS)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    p2b = json.loads((ROOT / F3.P2B).read_text())
    amp_t = json.loads((ROOT / F3.AMP_T).read_text())
    amp_b = json.loads((ROOT / F3.AMP_B).read_text())
    r2a = json.loads((ROOT / FINE3D_VERDICT).read_text())["R2a"]
    cvs = spreads(p2b)

    def cut(path):
        sm = json.loads((ROOT / path).read_text())["seed_means"]["fine"]
        return float(1.0 - sm["disp_c"] / sm["disp"])
    k = cut(F3.AMP_T) / cut(F3.AMP_B)
    vals = r2a["values"]
    cv_r2a = {arm: {"fine": F3.cv(vals[arm]["fine_disp"]),
                    "inband_disp": F3.cv(vals[arm]["inband_disp"]),
                    "inband_egap": F3.cv(vals[arm]["inband_egap"])} for arm in ("b", "s")}
    rng = np.random.default_rng(SEED)
    n = a.trials

    power = {}
    for din in INBAND_CHANGES:
        row = {}
        for d in FINE_CUTS:
            row[f"fine {-d:+.0%}"] = simulate(rng, cvs, d, din, din, n)["p_supported"]
        power[f"in band {din:+.0%}"] = row

    anc = anchors(amp_t, amp_b, r2a, k)
    variants = (("S's spreads the baseline's", {}),
                ("S's spreads 0.5 times", {"s_mult": 0.5}),
                ("S's spreads 1.5 times", {"s_mult": 1.5}),
                ("S's spreads R2a's S arm's", {"cvs_s": cv_r2a["s"]}),
                ("spreads drawn", {"drawn": True}),
                ("spreads drawn, S's 0.5 times", {"drawn": True, "s_mult": 0.5}),
                ("both arms' spreads twice", {"both_mult": 2.0}),
                (f"rho {RHO}", {"rho": RHO}),
                ("five seeds per arm", {"n_seeds": 5}),
                ("five seeds per arm, spreads drawn", {"n_seeds": 5, "drawn": True}))
    anchored = {}
    for name, e in anc.items():
        anchored[name] = {"effect": e, "cases": {}}
        for vname, kw in variants:
            anchored[name]["cases"][vname] = simulate(rng, cvs, e["fine"], e["inband_disp"],
                                                      e["inband_egap"], n, **kw)
    seeds = {}
    for din in (0.0, -0.3, -0.5):
        for d in (0.3, 0.5, 0.7, 0.9):
            seeds[f"in band {din:+.0%}; fine {-d:+.0%}"] = {
                str(nb): simulate(rng, cvs, d, din, din, n, n_seeds=nb)["p_supported"]
                for nb in (3, 5)}
    value = {}
    for name in anc:
        cs = anchored[name]["cases"]
        out = {}
        for tag, three, five in (("estimates", "S's spreads the baseline's", "five seeds per arm"),
                                 ("spreads drawn", "spreads drawn",
                                  "five seeds per arm, spreads drawn")):
            p3, p5 = cs[three]["p_supported"], cs[five]["p_supported"]
            out[tag] = {f"{v:g}": {"3": v * p3 - 1.0, "5": v * p5 - 5.0 / 3.0} for v in VALUES}
        value[name] = out
    res = {"what": "R2b: properties of R2b's rule (R2a's, PREREG_FINE3D Sec. 6) on the Phase-2b "
                   "transformer's seed spreads, by simulation (scripts/r2b_sims.py); log-normal "
                   "seed values, three seeds per arm unless stated",
           "trials": n, "seed": SEED, "guard": {"band": F3.GUARD_BAND, "k": F3.GUARD_K},
           "cv": cvs, "cv_r2a": cv_r2a, "k": k, "spread_cap": SPREAD_CAP, "rho": RHO,
           "power": power, "anchors": anchored, "seeds": seeds,
           "value": {"what": "expected value of R2b, a supported R2b worth v times the cost of "
                             "six runs; five seeds cost 10/6", "by_anchor": value}}
    text = json.dumps(res, indent=1)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
