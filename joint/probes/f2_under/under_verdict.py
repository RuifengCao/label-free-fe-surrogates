"""The measures and the outcome class of the trial of a field underneath of 25 November 2026
(joint/probes/f2_under/PRESPEC.md), from evaluation files:

    python3 -I under_verdict.py CONTROL.json FIRST.json [TRIAL.json]

CONTROL: the evaluation of the second cycle of 22 November 2026 (600 epochs in all); FIRST: that of the first cycle
(400 epochs); TRIAL: that of the trial, reported as missing while it does not exist. Reads the condensed reading of
seed 0; prints the two measures of the rule, the class, and what the plan reports outside the rule."""
import json
import os
import sys

WT = os.environ.get("F2_CODE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))   # the checkout this file lies in
sys.path[:0] = [WT + "/joint", WT + "/src"]
import numpy as np                                             # noqa: E402
from f2 import data as D, devconfig                            # noqa: E402

PRESET = {"control": "fam128_bending_more", "first": "fam128_bending_e400", "trial": "fam128_bending_under_e150"}
FIXED = {"control": (0.9878, 3.6862), "first": (1.5312, 5.3943)}   # per cent: median and 90th percentile, in the plan
THIN = ["dev_T10hi", "dev_W1", "dev_W2", "eval_0001", "eval_0003", "eval_0005", "eval_0006", "eval_0013"]
par = {i: q for i, _s, q in D.members(devconfig.config("fam128_bending_more"))}


def measures(path: str, name: str) -> dict | None:
    if not path or not os.path.isfile(path):
        return None
    ev = json.load(open(path))
    cfg_sha = devconfig.sha256(devconfig.config(PRESET[name]))
    assert ev["preset"] == PRESET[name] and ev["config_sha256"] == cfg_sha, f"{path} is not the evaluation of {name}"
    assert ev["status"] == {"0": "finished"}, ev["status"]
    m = ev["rows"]["0|condensed"]["members"]
    assert len(m) == 31 and all(len(lv) == 7 for lv in m.values()) and not ev["rows"]["0|condensed"]["errors"]
    e = {i: np.array([100.0 * d["abs_curveD_err"] for d in lv]) for i, lv in m.items()}
    assert all(np.isfinite(v).all() for v in e.values())
    allp = np.concatenate(list(e.values()))
    rnd = np.concatenate([v for i, v in e.items() if i.startswith("eval_")])
    assert allp.size == 217 and rnd.size == 112
    raw = np.array([100.0 * d["abs_curveD_err"] for lv in ev["rows"]["0|raw"]["members"].values() for d in lv])
    return {"median": float(np.median(allp)), "p90": float(np.percentile(allp, 90)),
            "outside": {"largest": float(allp.max()), "largest member": max(e, key=lambda i: e[i].max()),
                        "thin band, last level, median": float(np.median([e[i][-1] for i in THIN])),
                        "all members, last level, median": float(np.median([v[-1] for v in e.values()])),
                        "levels 1 and 2, median": float(np.median(np.concatenate([v[:2] for v in e.values()]))),
                        "median by level": [round(float(np.median([v[k] for v in e.values()])), 4) for k in range(7)],
                        "random 16: median, p90": [float(np.median(rnd)), float(np.percentile(rnd, 90))],
                        "points above 5 and above 10 per cent": [int((allp > 5).sum()), int((allp > 10).sum())],
                        "raw reading: median, p90, largest": [float(np.median(raw)), float(np.percentile(raw, 90)),
                                                              float(raw.max())]}}


names = ["control", "first", "trial"]
paths = (sys.argv[1:4] + [None, None, None])[:3]
res = {n: measures(p, n) for n, p in zip(names, paths)}
for n in ("control", "first"):
    assert res[n] is not None, f"the {n} evaluation is needed"
    assert abs(res[n]["median"] - FIXED[n][0]) < 5e-5 and abs(res[n]["p90"] - FIXED[n][1]) < 5e-5, \
        f"the {n} file does not give the plan's values: {res[n]['median']:.4f}, {res[n]['p90']:.4f}"
print("all 31 members, seven levels, condensed reading, moment at the same joint rotation, per cent")
print("            " + "  ".join(f"{n:>9s}" for n in names))
for k in ("median", "p90"):
    print(f"{k:10s}  " + "  ".join(f"{res[n][k]:9.4f}" if res[n] else "  missing" for n in names))
t = res["trial"]
if t is None:
    print("trial: no evaluation yet")
else:
    def within(n):
        return t["median"] <= res[n]["median"] and t["p90"] <= res[n]["p90"]

    cls = "A" if within("control") else "B" if within("first") else "C"
    print({"A": "class A: within 150 epochs the trial reaches the control's median and 90th percentile (600 epochs)",
           "B": "class B: the trial reaches the first cycle's values (400 epochs) but not the control's",
           "C": "class C: the trial does not reach the first cycle's values"}[cls])
print("outside the rule:")
for n in names:
    if res[n]:
        print(f"  {n}: " + json.dumps(res[n]["outside"]))
