"""The measures and the rule of the stage-two trial of 24 November 2026 (joint/probes/f2_stage2/PRESPEC.md), from
evaluation files:   python3 -I stage2_verdict.py CONTROL.json ARM1.json [ARM2.json]

A file that does not exist yet is reported as missing. Reads the condensed reading of seed 0 and the members'
parameters from the code package; prints the six measures, the rule for each arm, the choice, and what the plan
reports outside the rule."""
import json
import os
import sys

WT = os.environ.get("F2_CODE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))   # the checkout this file lies in
sys.path[:0] = [WT + "/joint", WT + "/src"]
import numpy as np                                             # noqa: E402
from f2 import data as D, devconfig                            # noqa: E402

LIMITS = {"P": 5.30, "G1": 3.76, "G2": 1.09, "G3": 4.06, "G4": 3.18, "G5": 0.87}       # per cent, fixed in the plan
CONTROL = {"P": 7.0742, "G1": 3.4209, "G2": 0.9878, "G3": 3.6862, "G4": 2.8869, "G5": 0.7891}
THIN = ["dev_T10hi", "dev_W1", "dev_W2", "eval_0001", "eval_0003", "eval_0005", "eval_0006", "eval_0013"]
PRESET = {"control": "fam128_bending_more", "arm 1": "fam128_bending_more_u", "arm 2": "fam128_bending_more_ux"}
par = {i: q for i, _s, q in D.members(devconfig.config("fam128_bending_more"))}


def measures(path: str, name: str) -> dict | None:
    if not os.path.isfile(path):
        return None
    ev = json.load(open(path))
    cfg_sha = devconfig.sha256(devconfig.config(PRESET[name]))
    assert ev["preset"] == PRESET[name] and ev["config_sha256"] == cfg_sha, f"{path} is not the evaluation of {name}"
    assert ev["status"] == {"0": "finished"}, ev["status"]
    m = ev["rows"]["0|condensed"]["members"]
    assert len(m) == 31 and all(len(lv) == 7 for lv in m.values()) and not ev["rows"]["0|condensed"]["errors"]
    assert sorted(i for i in m if par[i].tp < 12.5) == THIN
    e = {i: np.array([100.0 * d["abs_curveD_err"] for d in lv]) for i, lv in m.items()}
    assert all(np.isfinite(v).all() for v in e.values())
    allp = np.concatenate(list(e.values()))
    rnd = np.concatenate([v for i, v in e.items() if i.startswith("eval_")])
    low = np.concatenate([v[:2] for v in e.values()])
    assert allp.size == 217 and rnd.size == 112 and low.size == 62
    raw = np.array([100.0 * d["abs_curveD_err"] for lv in ev["rows"]["0|raw"]["members"].values() for d in lv])
    nolast = np.concatenate([v[:-1] for v in e.values()])
    bands = {}
    for lo, hi in ((10.0, 12.5), (12.5, 17.5), (17.5, 25.01)):
        bands[f"{lo:g} to {min(hi, 25.0):g} mm"] = float(np.median([e[i][-1] for i in e if lo <= par[i].tp < hi]))
    return {"P": float(np.median([e[i][-1] for i in THIN])), "G1": float(np.median([v[-1] for v in e.values()])),
            "G2": float(np.median(allp)), "G3": float(np.percentile(allp, 90)), "G4": float(np.percentile(rnd, 90)),
            "G5": float(np.median(low)),
            "outside": {"W1 last level": float(e["dev_W1"][-1]), "W2 last level": float(e["dev_W2"][-1]),
                        "largest": float(allp.max()), "largest member": max(e, key=lambda i: e[i].max()),
                        "raw median, p90, largest": [float(np.median(raw)), float(np.percentile(raw, 90)), float(raw.max())],
                        "without the last level: median, p90, largest": [float(np.median(nolast)), float(np.percentile(nolast, 90)), float(nolast.max())],
                        "median by level": [float(np.median([v[k] for v in e.values()])) for k in range(7)],
                        "last level by thickness band": bands,
                        "random 16: median": float(np.median(rnd))}}


names = ["control", "arm 1", "arm 2"]
res = {n: measures(p, n) for n, p in zip(names, sys.argv[1:4])}
c = res["control"]
assert c is not None and all(abs(c[k] - CONTROL[k]) < 5e-5 for k in CONTROL), "the control file does not give the plan's values"
print("measure  limit   " + "  ".join(f"{n:>9s}" for n in names))
for k in LIMITS:
    print(f"{k:7s} {LIMITS[k]:6.2f}   " + "  ".join(f"{res[n][k]:9.4f}" if res[n] else "  missing" for n in names))
passed = {}
for n in names[1:]:
    if res[n] is None:
        print(f"{n}: no evaluation yet")
        continue
    fails = [k for k in LIMITS if not res[n][k] <= LIMITS[k]]
    passed[n] = not fails
    print(f"{n}: " + ("PASSES" if not fails else "does not pass (" + ", ".join(fails) + ")"))
if len(passed) == 2:
    if all(passed.values()):
        gain = res["arm 1"]["P"] - res["arm 2"]["P"]
        choice = "arm 2" if gain >= 0.5 else "arm 1"
        print(f"both pass; P of arm 2 is {gain:+.4f} points below arm 1's: the plan takes {choice}")
    elif any(passed.values()):
        print("the plan takes", [n for n, ok in passed.items() if ok][0])
    else:
        print("no arm passes: the second cycle stays as it was run on 22 November 2026")
else:
    print("the choice waits for both evaluations (a run stopped by a non-finite loss does not pass)")
for n in names:
    if res[n]:
        print(n, "outside the rule:", json.dumps({k: ([round(x, 2) for x in v] if isinstance(v, list) else
                                                      ({a: round(b, 2) for a, b in v.items()} if isinstance(v, dict) else
                                                       (round(v, 2) if isinstance(v, float) else v)))
                                                  for k, v in res[n]["outside"].items()}))
