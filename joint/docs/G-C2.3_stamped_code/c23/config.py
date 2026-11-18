"""The configuration of gate G-C2.3 and its canonical hash.

G-C2.3 is gate G-C2.2 (plastic T-stubs under spring loading, label-free training with the stability recipe, the
amplitude-condensed reading) with nothing retrained in its label-free arm. Its configuration is G-C2.2's stamped
configuration with the changes made here and nothing else:

  held-out    64 fresh members (a third seed) are judged; G-C2.2's fresh members and the tested members are
              reported (G-C2.1's held-out members are not evaluated again);
  label-free  the three networks trained in G-C2.2 (seeds 5, 6, 7), identified by the SHA-256 of their state files;
              they are not trained again, only read on the members of this gate;
  self-check  on the fresh members, the spread of the force over the three label-free runs is compared with a
              threshold fixed here, and the cases it flags with the judged error (part 1);
  supervised  the same network, trained on reference solutions of all 512 training members at eight levels with
              G-C2.2's steps, schedule and stability recipe, three seeds, and compared with the label-free arm
              (part 2).

The family, its training members, the loading, the evaluation levels, the network, the label-free loss, the
sampling, the schedule, the budget, the stability recipe, the judged quantity and the two readings are G-C2.2's. The
code of c22/, c2/ and fejoint/ is used as stamped for G-C2.2.
"""
from __future__ import annotations

import copy

from c22 import config as base
from c22.config import canonical, sha256  # noqa: F401  (the same canonical form and hash as G-C2.1 and G-C2.2)

BASE_SHA256 = "ef5376a4d6c3cc98d7888121439c8d959ee817d332958dd6b1141b25e78734bb"   # G-C2.2's stamped configuration

THIRD_EVAL_SEED = 20261118      # the held-out members judged by this gate; not drawn before the stamp
# Family seeds whose members were exported, solved or trained on before the stamp. A held-out sample may use none.
FAMILY_SEEDS_SEEN = list(base.FAMILY_SEEDS_SEEN) + [base.FRESH_EVAL_SEED]
TRAINING_SEEDS = list(base.TRAINING_SEEDS)          # 5, 6, 7: the label-free runs of G-C2.2, and the supervised arm
# SHA-256 of the state files of G-C2.2's three runs (label_free_s<seed>/state.pt, after epoch 200).
LABEL_FREE_STATES = {"5": "5859ca7737e94b502660dddd082891a18f981b6df4228ff2a7c59d865ca7dcf5",
                     "6": "adb9992ae19846afd56e9f75d9dfe533edcf5a47fbca9c6a210f18581032c0b1",
                     "7": "80c56c73af04b4321f52a9acfd037a476837bfa6ec0cc8e55524dbf63988bc53"}
# G-C2.2's verdict (records/c22/return/verdict.json): the judged values of each run on its fresh members.
G22_PER_SEED = {"condensed": {"abs_curve_err_median": [0.008284227273415379, 0.007972382816471169,
                                                       0.007818943658160049],
                              "abs_curve_err_p90": [0.03663936677608451, 0.03766036133923352,
                                                    0.036562399536675616]},
                "raw": {"abs_curve_err_median": [0.014451064308929451, 0.013340824465134682, 0.013638353687949134],
                        "abs_curve_err_p90": [0.10944432481632067, 0.10470516659288157, 0.10542708497194714]}}
# The levels of the training labels: the base level of the condensed reading, the six training levels of G-C2.1's
# supervised arm, and the largest evaluation level. Every level at which a network is read (the base level and the
# seven evaluation levels) then lies within the labelled range; the evaluation levels between lie between labelled ones.
SUPERVISED_LABEL_LEVELS = [0.1, 0.75, 1.5, 2.5, 3.5, 5.0, 7.0, 8.0]
SPREAD_THRESHOLD = 0.0045


def config() -> dict:
    cfg = copy.deepcopy(base.config())
    assert sha256(cfg) == BASE_SHA256, "c22/config.py is not the configuration stamped for G-C2.2"
    cfg["gate"] = "G-C2.3"
    cfg["base"] = {"gate": "G-C2.2", "config_sha256": BASE_SHA256,
                   "unchanged": "family, training members, loading, evaluation levels, network, label-free loss, "
                                "sampling, learning rate, schedule, budget, stability recipe, judged quantity, "
                                "the raw and the condensed reading"}
    d = cfg["data"]
    d["third_eval_seed"], d["n_third"] = THIRD_EVAL_SEED, 64
    d["seeds_seen_before_stamp"] = list(FAMILY_SEEDS_SEEN)
    d["train_label_levels_mm"] = list(SUPERVISED_LABEL_LEVELS)
    read_at = [cfg["evaluation"]["readings"]["condensed"]["base_level_mm"]] + list(d["eval_levels_mm"])
    assert min(SUPERVISED_LABEL_LEVELS) <= min(read_at) and max(read_at) <= max(SUPERVISED_LABEL_LEVELS)
    d["n_train_labelled"] = d["n_train"]           # the supervised arm: every training member is labelled
    cfg["arms"] = {
        "label_free": {"loss": "energy", "labels": 0, "epochs": 200, "seeds": list(TRAINING_SEEDS),
                       "trained_in": "G-C2.2; the state files are read, nothing is trained",
                       "state_sha256": dict(LABEL_FREE_STATES),
                       "identity": {"values": copy.deepcopy(G22_PER_SEED), "tolerance": 1e-4,
                                    "how": "the judged values of each run on G-C2.2's fresh members, computed again "
                                           "from the state files, must equal G-C2.2's within the tolerance"}},
        "supervised_512": {"loss": "supervised", "labels": d["n_train"], "epochs": 200,
                           "seeds": list(TRAINING_SEEDS),
                           "how": "G-C2.2's run with the supervised loss of G-C2.1 in place of the energy: the same "
                                  "network, training members, steps, optimiser, schedule, clipping and stability "
                                  "recipe, and a fresh random order of the members every epoch; each step takes 4 "
                                  "of the labelled levels of its member"}}
    # Training seeds used before this stamp: G-C2.2's list, and its own runs 5, 6 and 7, which are this gate's
    # label-free runs. No supervised run of this configuration has been made with any seed.
    cfg["training_seeds_seen_before_stamp"] = sorted(set(base.TRAINING_SEEDS_SEEN) | set(base.TRAINING_SEEDS))
    ev = cfg["evaluation"]
    ev["sets"] = ["third", "eval", "tested"]
    ev["judged_set"] = "third"
    cfg["self_check"] = {
        "arm": "label_free", "set": "third", "reading": "condensed",
        "force": "F = 4 k_s (D - e), the spring reading of a run's field at the level's D; no reference solution",
        "spread": "for each (member, level) pair, (max - min) / |median| of F over the three runs; a pair whose "
                  "median F is zero is flagged",
        "threshold": SPREAD_THRESHOLD,
        "flag": "a pair is flagged when its spread is at least the threshold",
        "threshold_from": "the upper quartile of the spread over the 448 pairs of G-C2.1's held-out members "
                          "(0.004504), rounded; found in an exploratory reading of G-C2.2's records"}
    cfg["comparison"] = {
        "arms": ["supervised_512", "label_free"], "set": "third", "reading": "condensed",
        "statistics": "for each arm, the median over its three seeds of the median, and of the 90th percentile, "
                      "over the 448 pairs of |F / F*(e) - 1|",
        "ratios": "supervised over label-free, for each of the two statistics",
        "band": [2.0 / 3.0, 1.5], "band_ends": "included"}
    cfg["criteria"] = {
        "S1": "part 1: no pair that is not flagged has |F / F*(e) - 1| above 0.10 in any of the three runs",
        "S2": "part 1: of the (pair, run) readings of the pairs that are not flagged, at most 0.01 have "
              "|F / F*(e) - 1| above 0.05",
        "S3": "part 1: at most 0.35 of the 448 pairs are flagged",
        "self_check": "PASS iff S1, S2 and S3",
        "R": "part 1, the ranking: in each run that has a pair above 0.05 and a pair at or below 0.05, the "
             "probability that a pair above 0.05 has a larger spread than a pair at or below 0.05 (ties count half) "
             "is at least 0.90; HOLDS iff so in every such run, NOT EVALUABLE if there is no such run",
        "comparison": "part 2: 'comparable' iff both ratios lie in the band; 'supervised closer' iff both ratios "
                      "are below 1 and at least one is below the band; 'label-free closer' iff both are above 1 "
                      "and at least one is above the band; 'mixed' otherwise",
        "identity": "if a label-free run does not reproduce G-C2.2's judged values on G-C2.2's fresh members "
                    "within the tolerance, neither part is evaluated: the verdict is INVALID. The same holds when a "
                    "value cannot be computed: a label-free run without finite predictions, or a member of G-C2.2's "
                    "fresh sample without metrics in a label-free run. An end without finite predictions is final: "
                    "the run is not predicted again",
        "non_finite_seed": "a supervised seed whose run stopped on a non-finite loss or on non-finite predictions "
                           "enters the medians over seeds with infinite errors",
        "member_without_metrics": "a member of the judged set whose metrics the reference code cannot compute: in a "
                                  "label-free run, part 1 is FAIL and R is NOT EVALUABLE; in a run of either arm, "
                                  "the seed enters the medians over seeds of part 2 with infinite errors",
        "training_label_failure": "if a label of a training member does not converge or fails its checks, the "
                                  "supervised arm is not trained and part 2 stays INCOMPLETE; part 1 stands. No "
                                  "other solver settings are tried",
        "infinite_pairs": "a pair whose reference solve at the predicted end displacement fails, or gives a force "
                          "that is not positive, has an infinite error, which counts as above every threshold",
        "incomplete": "part 1 is INCOMPLETE while the label-free arm has not been evaluated or one of its runs has "
                      "neither predictions nor a non-finite end; part 2 is INCOMPLETE while an arm has not been "
                      "evaluated or one of its runs has neither predictions nor a non-finite stop",
        "not_resumed": "a command that is stopped and not run again leaves INCOMPLETE what needs it: both parts for "
                       "the evaluation of the label-free arm, part 2 for a supervised run or the evaluation of the "
                       "supervised arm",
        "final": "an outcome that is INVALID, and a part that is INCOMPLETE by a stop condition, are final: the gate "
                 "is not run again on this sample",
        "reported_not_judged": "both readings of both arms on every set, with the values C1 and C2 of G-C2.2 "
                               "would take; the median error of both arms at each level; the ratios of the "
                               "supervised arm read raw over the label-free arm in the judged reading; the pairs "
                               "above 0.05 and 0.10 and how many of them are flagged; the spread and the flags on "
                               "the other sets and in the raw reading; the spread of the supervised runs; the time "
                               "and the reference solutions each arm needed; the cap's actions",
    }
    return cfg
