"""The configuration of gate G-F2.1 and its canonical hash.

The gate trains the CHS surrogate of the development (f2) three times, with seeds with which neither of the recipe's
two training configurations has been run, by the recipe that the development fixed, and reads it on a sample of the
family drawn after the stamp. The recipe's two run
configurations are development presets (f2/devconfig.py) and are pinned here by their SHA-256, with the data they
train on; the gate trains them with seeds the presets do not list, so that the run configurations and their hashes
are the development's own.

The sample's seed is the day of the stamp (f21/stamp_day.py), written into this configuration when the stamp is
prepared, so that every command refuses another seed with the configuration hash. No test and no host check draws
with the gate's configuration: they use reduced configurations whose seeds are days of January 2026, which are
listed among the used seeds here.
"""
from __future__ import annotations

import copy
import datetime
import time

from f2.config import canonical, sha256  # noqa: F401

from .stamp_day import SAMPLE_SEED

GATE = "G-F2.1"
FIRST, SECOND = "fam128_bending_e400", "fam128_bending_more_ux"
# True while a command of f21/__main__.py runs that has found the code to be the stamped code; the command clears
# it when it ends. Otherwise sample_config refuses the gate's own configuration, so that a call of a function (a
# test, a check, a look at the code) does not draw the gate's sample; the reduced configurations of the host check
# and of the tests have other names. A guard against a slip, not against intent: the flag can be set by hand.
_STAMP_VERIFIED = False
PINS = {
    "first_config_sha256": "de8f4d173097aec0aec9bffac24efadabb75229acdf9c9f40055845dc4ca6a07",
    "second_config_sha256": "be9a2235e691cb724e7a83b6a9292e057dfba4d4e1cbf04e2e86e5713459d951",
    "data_sha256": "e46121c6a55482296dcd2a0e3ec62b1e63ec364cad7d9fea206e78df1615b71e",
    "extra_data_sha256": "72450ee831153ebc6c717e05469fd07c4e7029b3dcbf02b2329a069ba980d476",
}
# the files of the repository package that the runs import, pinned as c2/config.py pins its own
REPOSITORY_CODE = {
    "src/fejepa/__init__.py":
        "6b4a69dde91fbd83c5c16707a00e4c9e6a2e02647aca1d3132b313e4b20f9fdc",
    "src/fejepa/models/__init__.py":
        "88d852286c71e468491b7d0b34cec2c467bd4c96724a26ca8ebcc6b8f92306e4",
    "src/fejepa/models/features.py":
        "0af43e0a87fda6bc177e9b446a720ac11e3e116bc29e445446edf846162c208d",
    "src/fejepa/models/fejepa.py":
        "3263988641477cfab564c5c622f8cf3406d98e45078134da8c6905d4b410b847",
    "src/fejepa/train/__init__.py":
        "88d852286c71e468491b7d0b34cec2c467bd4c96724a26ca8ebcc6b8f92306e4",
    "src/fejepa/train/schedule.py":
        "d53b55877c65efc37ee0a3877362451d8227ef84f581df64138ac1b469bd57c5",
}
# seeds that drew members of the family before the stamp: the tests' (f2/config.py); the development's training,
# held-out and extra training members (f2/devconfig.py); the seeds of this gate's tests, host check and session
# simulation (20260102, 20260103); and 20261127, which was drawn once while this file was written (25 November
# 2026: the number of thin members and the range of the plate thickness of that draw were printed, nothing else)
FAMILY_SEEDS_USED = [11, 12, 20260102, 20260103, 20261120, 20261121, 20261124, 20261127]


def config() -> dict:
    return {
        "gate": GATE,
        "recipe": {
            "first": {"preset": FIRST, "config_sha256": PINS["first_config_sha256"],
                      "starts_from": "new networks"},
            "second": {"preset": SECOND, "config_sha256": PINS["second_config_sha256"],
                       "starts_from": "the weights of the same seed's finished first cycle; a new optimiser and "
                                      "schedule",
                       "extra_data_sha256": PINS["extra_data_sha256"]},
            "data_sha256": PINS["data_sha256"],
            "mesh": None,                              # the presets' own (the family's mesh)
            "only": None,                              # every member of the development's data
            "seeds": [5, 6, 7],
            # the development's training seeds (0, 1, 2) and the seeds kept for timings of two epochs (90 to 93)
            "training_seeds_kept_from_the_gate": [0, 1, 2, 90, 91, 92, 93],
        },
        "sample": {
            "n": 64, "prefix": "gate",
            "seed": SAMPLE_SEED,
            "seed_rule": "the day of the stamp in UTC as the integer YYYYMMDD (f21/stamp_day.py), or, if that day is "
                         "among the seeds used before the stamp, the first later day that is not",
            "not_before": 20261125, "not_after": None,
            "family_seeds_used_before_stamp": list(FAMILY_SEEDS_USED),
            "drawn": "uniformly over the family's ranges, as the development's held-out members (f2.family.sample)",
            "levels": "the evaluation levels of the run configurations (seven fractions of the member's device "
                      "range)",
        },
        "judged": {
            "reading": "condensed", "quantity": "abs_curveD_err",
            "what": "the moment over the reference moment at the same rotation of the measuring ring, minus one, in "
                    "absolute value (f2/evaluate.py: curveD_err, to first order in that rotation)",
            "per_seed": ["median", "p90"], "over": "the pairs (member, level) of the sample",
            "across_seeds": "median",
            "lines": {"median": 0.05, "p90": 0.10},
            "not_finite": "a pair whose evaluation fails or whose value is not finite counts as infinite",
            "missing": "FAIL if a cycle of a seed stopped on a non-finite value or its predictions on the sample are "
                       "not finite; INCOMPLETE while a training, a prediction or an evaluation is missing",
        },
        "repository_code": dict(REPOSITORY_CODE),
        # the linear solver of every reference solve (exports, labels, evaluations); the commands that solve refuse
        # a host on which fejoint.linsolve would use another one
        "reference": {"linear_solver": "pardiso"},
        "reported": {
            "thin_band": {"parameter": "tp", "at_most": 12.5},
            "readings": ["raw"],
            "quantities": ["abs_curve_err", "abs_M_err", "ThetaD_err", "gap"],
            "exact": {"quantity": "curveD_exact_err", "signed": "curveD_err", "readings": ["condensed"],
                      "what": "the judged error with the reference solved at the predicted rotation of the measuring "
                              "ring itself (f2/evaluate.py: curveD_exact_err) in the place of the first-order value; "
                              "for the judged reading; the statistics of the judged quantity and the differences "
                              "between the two"},
            "also": ["each seed", "each level", "the worst members", "the development's 31 members"],
        },
    }


def verify_repository(cfg: dict) -> str:
    """The repository files the runs import must have the SHA-256 the configuration pins. Returns the root."""
    import hashlib
    import importlib.util
    from pathlib import Path

    spec = importlib.util.find_spec("fejepa")
    if spec is None or spec.origin is None:
        raise RuntimeError("the repository package fejepa is not on the path (--repo)")
    root = Path(spec.origin).resolve().parents[2]
    bad = [f for f, h in cfg["repository_code"].items()
           if not (root / f).is_file() or hashlib.sha256((root / f).read_bytes()).hexdigest() != h]
    if bad:
        raise RuntimeError(f"repository files differ from the configuration: {bad}")
    return str(root)


def check_sample_seed(cfg: dict, today: int | None = None) -> int:
    """The seed of the sample, from the configuration: a calendar day as YYYYMMDD, within the configured days, not a
    seed that drew members of the family before the stamp, and not a day that has not come yet (UTC; today: for
    tests)."""
    s = cfg["sample"]
    seed = s["seed"]
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("the sample's seed must be an integer written as YYYYMMDD")
    try:
        datetime.date(seed // 10000, seed // 100 % 100, seed % 100)
    except ValueError:
        raise ValueError(f"{seed} is not a day written as YYYYMMDD") from None
    if seed < s["not_before"]:
        raise ValueError(f"the sample's seed {seed} lies before {s['not_before']}")
    if s.get("not_after") is not None and seed > s["not_after"]:
        raise ValueError(f"the sample's seed {seed} lies after {s['not_after']}")
    if seed in s["family_seeds_used_before_stamp"]:
        raise ValueError(f"{seed} drew members of the family before the stamp")
    if seed > (int(time.strftime("%Y%m%d", time.gmtime())) if today is None else int(today)):
        raise ValueError(f"the sample's seed {seed} is a day that has not come (UTC)")
    return seed


def run_config(cfg: dict, cycle: str) -> dict:
    """The run configuration of a cycle: the development preset, on the configured mesh, checked against its pin."""
    from f2 import devconfig

    r = cfg["recipe"][cycle]
    c = devconfig.config(r["preset"])
    if cfg["recipe"]["mesh"] is not None:
        c["data"]["mesh"] = cfg["recipe"]["mesh"]
    if sha256(c) != r["config_sha256"]:
        raise RuntimeError(f"the run configuration of the {cycle} cycle is not the pinned one")
    return c


def sample_config(cfg: dict) -> dict:
    """The configuration under which the sample is generated, labelled, predicted and evaluated: the second cycle's
    run configuration with a data section that holds the sample only (n members drawn with the configured seed,
    named <prefix>_0000 and so on; no training, development or tested member), every member evaluated."""
    seed = check_sample_seed(cfg)
    if cfg["gate"] == GATE and not _STAMP_VERIFIED:
        raise RuntimeError("the sample of gate G-F2.1 is configured by the gate's commands only, from the stamped code")
    s = cfg["sample"]
    c = copy.deepcopy(run_config(cfg, "second"))
    c["gate"] = cfg["gate"]
    d = c["data"]
    d["eval_seed"], d["n_eval"], d["eval_prefix"] = seed, int(s["n"]), str(s["prefix"])
    d["n_train"], d["n_train_labelled"] = 0, 0
    d["dev"], d["tested"] = {}, {}
    d["seeds_seen_before_stamp"] = sorted(set(d["seeds_seen_before_stamp"]) | set(s["family_seeds_used_before_stamp"]))
    c["evaluation"]["sets"], c["evaluation"]["members"] = ["eval"], None
    return c
