"""The configuration of gate G-C2.2 and its canonical hash.

G-C2.2 is gate G-C2.1 (plastic T-stubs under spring loading, label-free training) with a changed method. Its
configuration is G-C2.1's stamped configuration with the changes made here and nothing else:

  training    the stability recipe: AdamW's beta2 0.99, and the encoder's gradient scaled down to at most 5 times the
              median of its norm over the previous 256 steps (before the global clipping);
  reading     the judged point is read from the amplitude-condensed field (c22/condense.py); the raw reading of
              G-C2.1 is reported;
  held-out    64 fresh members (a new seed) are judged; the 64 held-out members of G-C2.1 are reported;
  seeds       three new training seeds; no supervised arm.

The family, its training members, the loading, the levels, the network, the loss, the schedule, the budget, the judged
quantity and the thresholds are G-C2.1's. The code of c2/ and fejoint/ is used as stamped for G-C2.1.
"""
from __future__ import annotations

import copy

from c2 import config as base
from c2.config import canonical, sha256  # noqa: F401  (the same canonical form and hash as G-C2.1)

BASE_SHA256 = "795515630ff6f37a819c7503931c7d7cf6e70a9f272e25ac96730394dd361fb4"   # G-C2.1's stamped configuration

FRESH_EVAL_SEED = 20261113      # the held-out members judged by this gate; not drawn before the stamp
FORMER_EVAL_SEED = 20261107     # the held-out members of G-C2.1; seen throughout the development, reported only
# Family seeds whose members were exported, solved or trained on before the stamp. A held-out sample may use none.
FAMILY_SEEDS_SEEN = list(base.SEEDS_SEEN) + [20261106, 20261107]
# Training seeds used before the stamp: 0, 1, 2 in G-C2.1; 0, 1, 3, 4 in the development runs of November 2026.
TRAINING_SEEDS_SEEN = [0, 1, 2, 3, 4]
TRAINING_SEEDS = [5, 6, 7]


def config() -> dict:
    cfg = copy.deepcopy(base.config())
    assert sha256(cfg) == BASE_SHA256, "c2/config.py is not the configuration stamped for G-C2.1"
    cfg["gate"] = "G-C2.2"
    cfg["base"] = {"gate": "G-C2.1", "config_sha256": BASE_SHA256,
                   "unchanged": "family, training members, loading, levels, network, loss, sampling, learning rate, "
                                "schedule, budget, judged quantity, thresholds"}
    d = cfg["data"]
    d["eval_seed"] = FRESH_EVAL_SEED
    d["former_eval_seed"], d["n_former"] = FORMER_EVAL_SEED, 64
    d["seeds_seen_before_stamp"] = list(FAMILY_SEEDS_SEEN)
    d["training_members"] = "seed 20261106, the 512 training members of G-C2.1 (the seed is reused on purpose)"
    d["n_train_labelled"] = 0                      # no supervised arm: no training member is labelled
    tr = cfg["training"]
    tr["beta2"] = 0.99
    tr["encoder_gradient_cap"] = {
        "factor": 5.0, "window_steps": 256, "burst_factor": 10.0,
        "how": "before the global clipping, the encoder's gradient is scaled down to at most factor times the median "
               "of its norm over the previous window_steps steps (norms before any scaling), from step "
               "window_steps + 1 on; a step whose ratio exceeds burst_factor is recorded as a burst"}
    tr["checkpoint_every_epochs"] = 1
    cfg["arms"] = {"label_free": {"loss": "energy", "labels": 0, "epochs": 200, "seeds": list(TRAINING_SEEDS)}}
    cfg["training_seeds_seen_before_stamp"] = list(TRAINING_SEEDS_SEEN)
    ev = cfg["evaluation"]
    ev["sets"] = ["eval", "former", "tested"]
    ev["judged_set"] = "eval"
    ev["readings"] = {
        "judged": "condensed", "reported": ["raw"],
        "raw": "the point (e, F) of the network's field z at the level's D, as in G-C2.1",
        "condensed": {
            "field": "z_c = keep(z_0 + a (z - z_0)): z the network's field at the level's D, z_0 its field at "
                     "base_level_mm, keep the contact unknowns set to at least zero",
            "amplitude": "a minimises the training energy (float32, c2.torch_energy) of z_c at the level's D over "
                         "a_min <= a <= a_max: a safeguarded secant iteration on dPi/da from a = 1, at most "
                         "max_evaluations energy evaluations, stopped at |dPi/da| <= rtol Pi; the evaluated point "
                         "of lowest energy is returned",
            "base_level_mm": tr["D_min_mm"], "a_min": 0.5, "a_max": 3.0, "max_evaluations": 12, "rtol": 1e-4,
            "labels": "none: no reference solution enters a reading"}}
    cfg["criteria"] = {
        "C1": "the median over the three seeds of the median over the 448 (member, level) pairs of the fresh "
              "held-out members of |F / F*(e) - 1|, (e, F) read from the condensed field, is at most 0.05",
        "C2": "the median over the three seeds of the 90th percentile over the same pairs of |F / F*(e) - 1|, read "
              "the same way, is at most 0.10",
        "verdict": "PASS iff C1 and C2",
        "non_finite_seed": "a seed whose run stopped on a non-finite loss or on non-finite predictions (raw or "
                           "condensed), or whose metrics of a judged member fail altogether, enters the medians "
                           "over seeds with infinite errors",
        "infinite_pairs": "a pair whose reference solve at the predicted end displacement fails, or gives a force "
                          "that is not positive, has an infinite curve error, which enters the median and the 90th "
                          "percentile as such",
        "incomplete": "INCOMPLETE while a seed has neither predictions nor a non-finite stop",
        "amplitudes": "an amplitude on a bound, or not converged after max_evaluations, is used as it is and counted",
        "reported_not_judged": "the raw reading on the fresh held-out members with the values C1 and C2 would take "
                               "for it; both readings on the 64 held-out members of G-C2.1 and on the tested "
                               "members; every metric of G-C2.1 for both readings; the amplitudes; the cap's "
                               "actions and the bursts of each run",
    }
    return cfg
