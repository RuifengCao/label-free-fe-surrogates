#!/usr/bin/env python3
"""cmame-paper Stage 12: operating characteristics of PREREG_K3D's decision
rule -- the E-series noise guard on three per-seed values per arm, each
seed's value its median over the validation instances -- by simulation, and
the seed-mean form of the same guard at the reference's recorded seed means.

Medians. Each arm's three per-seed medians are log-normal around the arm's
true level with coefficient of variation c_ref (reference) or c_new (new
arm); the new arm's true level is r times the reference's. Per trial, as the
adjudication computes it: rel = mean(new)/mean(ref) - 1, SE_rel =
sqrt(s_new^2/3 + s_ref^2/3)/mean(ref) with sample standard deviations,
tau = max(10%, 2 x SE_rel); "lower beyond the guard" iff rel < -tau, "worse
beyond the guard" iff rel > tau. The references' spreads are those of the
stored states' per-seed medians on the validation split (the Phase-2b
report's arrays): Phase-2's L_D transformer 10.2% in the relative energy gap
(H2a-3D's reference; simulated at 10%) and 5.9% in the relative L2 von Mises
error (H2b-3D's; at 6%), the label-free transformer 23.3% in the relative
energy gap (H3-3D's; at 23%).

At L_K's two-dimensional spread. H2a-3D and H2b-3D with the new arm's
per-seed medians at the coefficients of variation L_K's had in two
dimensions (CM2D's return: 37% in the relative energy gap, 19% in the von
Mises error).

Wide spreads and the two hypotheses together. H2a-3D and H2b-3D with the
new arm's spread at 75% and 100% (a standard deviation from three seeds has a
95% interval of about 0.52 to 6.3 times the estimate); and, without a true
difference in either quantity, the share of trials in which at least one of
the two, and both, read lower beyond the guard, with the seed effects on the
two medians correlated within an arm (rho 0, 0.5, 0.95), at L_K's
two-dimensional spreads.

Seed means. The guard on seed means with the reference at its recorded
three values (L_D's seed means of the relative energy gap 0.2966 / 92.99 /
0.3649 and of the von Mises error 0.2722 / 0.5299 / 0.3071; the middle ones
are carried by one validation instance), the new arm log-normal: SE_rel of
the reference alone, the smallest tau, and the share of trials "lower beyond
the guard" by r and c_new.

    python scripts/k3d_sims.py --out records/cmame/k3d_sims.json
    python scripts/k3d_sims.py --check records/cmame/k3d_sims.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

SEED = 20261020
TRIALS = 200_000
N_SEEDS = 3
BAND, K = 0.10, 2.0
REFS = {"H2a-3D": 0.10, "H2b-3D": 0.06, "H3-3D": 0.23}
"""The references' seed spreads of the per-seed medians (simulated values)."""
NEW = (0.05, 0.10, 0.20, 0.30, 0.50)
RATIOS = {"H2a-3D": (0.5, 0.7, 0.8, 0.9, 1.0), "H2b-3D": (0.5, 0.7, 0.8, 0.9, 1.0),
          "H3-3D": (0.5, 0.8, 1.0, 1.25, 2.0)}
MEANS = {"energy_gap_rel": (0.29662, 92.989, 0.36494),
         "vm_rel_l2": (0.27219, 0.52986, 0.30708)}
"""L_D's recorded seed means (the Phase-2b report's, to five significant
digits; tests/test_k3d_prereg.py checks them against the report)."""
MEAN_RATIOS = (0.1, 0.3, 0.5, 0.6, 0.7)
LK_2D = {"H2a-3D": 0.37, "H2b-3D": 0.19}
WIDE = (0.75, 1.00)
"""New-arm spreads beyond the measured ones: a standard deviation from three
seeds has a 95% interval of about 0.52 to 6.3 times the estimate."""
RHO = (0.0, 0.5, 0.95)
"""Correlations of a seed's effects on the two medians (relative energy gap,
von Mises error) within an arm: H2a-3D and H2b-3D read the same states, and in
both arms the two medians have had the same rank order across seeds."""
"""L_K's seed spread in two dimensions (CM2D's return): the coefficients of
variation of its per-seed medians, 37% in the relative energy gap and 19% in
the von Mises error."""


def _lognormal(rng, level, cv: float, size) -> np.ndarray:
    s = np.sqrt(np.log1p(cv * cv))
    return np.exp(rng.normal(np.log(level) - s * s / 2, s, size=size))


def _guard(ref: np.ndarray, new: np.ndarray) -> dict:
    mb, ma = ref.mean(axis=1), new.mean(axis=1)
    se = np.sqrt(ref.var(axis=1, ddof=1) / N_SEEDS + new.var(axis=1, ddof=1) / N_SEEDS) / mb
    tau = np.maximum(BAND, K * se)
    rel = ma / mb - 1
    return {"lower": round(float(np.mean(rel < -tau)), 5),
            "worse": round(float(np.mean(rel > tau)), 5),
            "tau_median": round(float(np.median(tau)), 4)}


def medians(rng, trials: int) -> dict:
    out = {}
    for h, c_ref in REFS.items():
        out[h] = {f"c_ref={c_ref:.2f},c_new={c:.2f}": {
            f"r={r:g}": _guard(_lognormal(rng, 1.0, c_ref, (trials, N_SEEDS)),
                               _lognormal(rng, r, c, (trials, N_SEEDS)))
            for r in RATIOS[h]} for c in NEW}
    return out


def seed_means(rng, trials: int) -> dict:
    out = {}
    for m, vals in MEANS.items():
        b = np.asarray(vals, float)
        se_b = float(b.std(ddof=1) / np.sqrt(N_SEEDS) / b.mean())
        cells = {}
        for c in NEW:
            row = {}
            for r in MEAN_RATIOS:
                # the new arm's level: r times the reference's mean without its
                # largest seed, so that r reads as a reduction of the typical seed
                level = r * float(np.mean(np.sort(b)[:2]))
                new = _lognormal(rng, level, c, (trials, N_SEEDS))
                ref = np.broadcast_to(b, new.shape)
                row[f"r={r:g}"] = _guard(ref, new)
            cells[f"c_new={c:.2f}"] = row
        out[m] = {"reference_seed_means": list(vals), "se_rel_of_the_reference_alone":
                  round(se_b, 4), "smallest_tau": round(max(BAND, K * se_b), 4),
                  "cells": cells}
    return out


def at_lk_2d_spread(rng, trials: int) -> dict:
    """H2a-3D and H2b-3D with the new arm at L_K's two-dimensional spread."""
    return {h: {f"c_ref={REFS[h]:.2f},c_new={c:.2f}": {
        f"r={r:g}": _guard(_lognormal(rng, 1.0, REFS[h], (trials, N_SEEDS)),
                           _lognormal(rng, r, c, (trials, N_SEEDS)))
        for r in RATIOS[h]}} for h, c in LK_2D.items()}


def wide_spreads(rng, trials: int) -> dict:
    """H2a-3D and H2b-3D with the new arm at spreads beyond the measured ones."""
    return {h: {f"c_ref={REFS[h]:.2f},c_new={c:.2f}": {
        f"r={r:g}": _guard(_lognormal(rng, 1.0, REFS[h], (trials, N_SEEDS)),
                           _lognormal(rng, r, c, (trials, N_SEEDS)))
        for r in (0.5, 0.7, 0.8, 1.0)} for c in WIDE} for h in ("H2a-3D", "H2b-3D")}


def _pair(rng, cv: tuple, rho: float, trials: int) -> tuple:
    """Per trial and seed, the two medians of one arm, log-normal around 1,
    their seed effects correlated with rho."""
    z1 = rng.standard_normal((trials, N_SEEDS))
    z2 = rho * z1 + np.sqrt(1.0 - rho * rho) * rng.standard_normal((trials, N_SEEDS))
    out = []
    for z, c in zip((z1, z2), cv, strict=True):
        s = np.sqrt(np.log1p(c * c))
        out.append(np.exp(s * z - s * s / 2))
    return out


def joint(rng, trials: int) -> dict:
    """Without a true difference in either quantity, at the references'
    spreads and L_K's two-dimensional ones: the share of trials in which at
    least one of H2a-3D and H2b-3D, and both, read lower beyond the guard."""
    out = {}
    for rho in RHO:
        rg, rv = _pair(rng, (REFS["H2a-3D"], REFS["H2b-3D"]), rho, trials)
        ng, nv = _pair(rng, (LK_2D["H2a-3D"], LK_2D["H2b-3D"]), rho, trials)
        lo = []
        for ref, new in ((rg, ng), (rv, nv)):
            mb, ma = ref.mean(axis=1), new.mean(axis=1)
            se = np.sqrt(ref.var(axis=1, ddof=1) / N_SEEDS + new.var(axis=1, ddof=1)
                         / N_SEEDS) / mb
            lo.append(ma / mb - 1 < -np.maximum(BAND, K * se))
        out[f"rho={rho:g}"] = {"either": round(float(np.mean(lo[0] | lo[1])), 5),
                               "both": round(float(np.mean(lo[0] & lo[1])), 5),
                               "h2a": round(float(np.mean(lo[0])), 5),
                               "h2b": round(float(np.mean(lo[1])), 5)}
    return out


def simulate(trials: int = TRIALS) -> dict:
    rng = np.random.default_rng(SEED)
    return {"what": "PREREG_K3D operating characteristics (scripts/k3d_sims.py)",
            "seed": SEED, "trials_per_cell": trials, "seeds_per_arm": N_SEEDS,
            "guard": {"band": BAND, "k": K}, "model": "log-normal per-seed values",
            "medians": medians(rng, trials),
            "seed_means_at_the_recorded_reference": seed_means(rng, trials),
            "medians_at_lk_2d_spread": at_lk_2d_spread(rng, trials),
            "medians_at_wide_new_arm_spreads": wide_spreads(rng, trials),
            "joint_null_at_lk_2d_spread": joint(rng, trials)}


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--out")
    g.add_argument("--check", help="exit non-zero unless this file is the simulation's output")
    a = ap.parse_args()
    text = json.dumps(simulate(), indent=1) + "\n"
    if a.check:
        if Path(a.check).read_text() != text:
            raise SystemExit(f"{a.check}: not this simulation's output")
        return
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
