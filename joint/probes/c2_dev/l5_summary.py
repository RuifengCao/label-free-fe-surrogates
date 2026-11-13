"""L5 (full-family fine-tune from the host seed-2 model): the three arms side by side.

Reads runs/<arm>/eval_eK.json and runs/<arm>/summary.json (written by finetune_dev.py) and prints, for each arm and
each recorded epoch, the judged quantity under the raw and the condensed reading (median, 90th percentile with linear
interpolation, pairs over 10% of 448); at the last epoch the same by mechanism and by level, the pairs over 10% shared
between arms, the amplitude statistics and the training events.

    python l5_summary.py RUNS_DIR [EVAL_REF_JSON]
"""
import json
import sys
from pathlib import Path

import numpy as np

runs = Path(sys.argv[1])
ref = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
ARMS = [("L5a_plain_sqrt", "a: gate loss, sqrt sampling"), ("L5b_plain_uniform", "b: gate loss, uniform D"),
        ("L5c_cond_uniform", "c: condensed loss, uniform D")]
EPOCHS = [0, 2, 5, 8, 10]
names = {int(k): v for k, v in ref["mechanism_names"].items()} if ref and isinstance(ref["mechanism_names"], dict) \
    else (dict(enumerate(ref["mechanism_names"])) if ref else {})


def stats(J):
    J = np.abs(np.asarray(J, float))
    return 100 * np.median(J), 100 * np.percentile(J, 90), int((J > 0.10).sum()), len(J)


def line(rows, key):
    m, p, o, n = stats([r[key]["J"] for r in rows])
    return f"{m:5.2f} / {p:5.2f} / {o:3d} of {n}"


data = {}
for arm, label in ARMS:
    data[arm] = {e: json.load(open(runs / arm / f"eval_e{e}.json")) for e in EPOCHS if (runs / arm / f"eval_e{e}.json").exists()}

print("C1 median % / C2 90th percentile % / pairs over 10%   (raw | condensed)")
for arm, label in ARMS:
    print(f"\n{label}")
    for e, d in data[arm].items():
        print(f"  e{e:<2d}  {line(d['rows'], 'raw')} | {line(d['rows'], 'cond')}")

last = max(EPOCHS)
print(f"\nEpoch {last}, by mechanism (raw | condensed)")
mechs = sorted({r["mechanism"] for r in data[ARMS[0][0]][last]["rows"]})
for arm, label in ARMS:
    print(f"  {label}")
    rows = data[arm][last]["rows"]
    for mch in mechs:
        sub = [r for r in rows if r["mechanism"] == mch]
        print(f"    {str(names.get(mch, mch)):24s} {line(sub, 'raw')} | {line(sub, 'cond')}")
print(f"\nEpoch {last}, by level (raw | condensed)")
levels = sorted({r["D"] for r in data[ARMS[0][0]][last]["rows"]})
for arm, label in ARMS:
    print(f"  {label}")
    rows = data[arm][last]["rows"]
    for D in levels:
        sub = [r for r in rows if r["D"] == D]
        print(f"    D = {D:<4g}                 {line(sub, 'raw')} | {line(sub, 'cond')}")

print(f"\nEpoch 0 (the start, same for all arms), condensed, by mechanism and level")
rows0 = data[ARMS[0][0]][0]["rows"]
for mch in mechs:
    print(f"    {str(names.get(mch, mch)):24s} {line([r for r in rows0 if r['mechanism'] == mch], 'cond')}")
for D in levels:
    print(f"    D = {D:<4g}                 {line([r for r in rows0 if r['D'] == D], 'cond')}")

print(f"\nPairs over 10% under the condensed reading at epoch {last}: overlap between arms")
over = {arm: {(r["id"], r["D"]) for r in data[arm][last]["rows"] if abs(r["cond"]["J"]) > 0.10} for arm, _ in ARMS}
over0 = {(r["id"], r["D"]) for r in rows0 if abs(r["cond"]["J"]) > 0.10}
allthree = set.intersection(*over.values())
anyarm = set.union(*over.values())
print(f"  start {len(over0)}; a {len(over['L5a_plain_sqrt'])}, b {len(over['L5b_plain_uniform'])}, c {len(over['L5c_cond_uniform'])};"
      f" in all three {len(allthree)}; in any {len(anyarm)}; in all three and at the start {len(allthree & over0)}")
members = {}
for i, D in allthree:
    members.setdefault(i, []).append(D)
mech_of = {r["id"]: r["mechanism"] for r in rows0}
print(f"  members with a pair over 10% in all three arms: {len(members)}")
for i in sorted(members, key=lambda k: (-len(members[k]), k)):
    worst = max(abs(r["cond"]["J"]) for arm, _ in ARMS for r in data[arm][last]["rows"] if r["id"] == i)
    print(f"    {i}  {str(names.get(mech_of[i], mech_of[i])):22s} levels {sorted(members[i])}  worst {100 * worst:5.1f}%")
by_mech = {}
for i, D in allthree:
    by_mech[mech_of[i]] = by_mech.get(mech_of[i], 0) + 1
print("  shared pairs by mechanism:", {str(names.get(k, k)): v for k, v in sorted(by_mech.items())})

print(f"\nSign of the error (condensed, epoch {last}): pairs over 10% that are over-stiff (J > 0) or over-soft (J < 0)")
for arm, label in ARMS:
    rows = [r for r in data[arm][last]["rows"] if abs(r["cond"]["J"]) > 0.10]
    print(f"  {label}: over-stiff {sum(r['cond']['J'] > 0 for r in rows)}, over-soft {sum(r['cond']['J'] < 0 for r in rows)}")

print(f"\nAmplitude a at epoch {last} (reading) and the solver")
for arm, label in ARMS:
    d = data[arm][last]
    a = np.array([r["a"] for r in d["rows"]])
    print(f"  {label}: a median {np.median(a):.3f}, range {a.min():.3f} to {a.max():.3f}; solve {d['solve']}")

print("\nEnergy gap (median, %) and end-displacement error (median of |.|, %) at the last epoch, raw | condensed")
for arm, label in ARMS:
    rows = data[arm][last]["rows"]
    g = [100 * np.median([r[k]["gap"] for r in rows]) for k in ("raw", "cond")]
    e = [100 * np.median([abs(r[k]["e_err"]) for r in rows]) for k in ("raw", "cond")]
    print(f"  {label}: gap {g[0]:.3f} | {g[1]:.3f}; e error {e[0]:.2f} | {e[1]:.2f}")

print("\nTraining")
for arm, label in ARMS:
    s = json.load(open(runs / arm / "summary.json"))
    ratios = [round(b["ratio"], 1) for b in s["bursts"]]
    print(f"  {label}: status {s['status']}, {s['steps']} steps, bursts {len(s['bursts'])} {ratios}, cap events {s['cap_events']},"
          f" collapses {len(s['collapses'])}, resumes {len(s['resumes'])}, seconds {sum(s['epoch_seconds']):.0f},"
          f" train solve {s.get('train_solve')}, peak memory {s['peak_memory_GiB']:.2f} GiB")
    print(f"      epoch loss {[round(v, 3) for v in s['epoch_loss']]}")
