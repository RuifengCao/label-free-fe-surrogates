import sys, json
import numpy as np
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
base = str(paths.runs() / "overfit") + "/"
LV = [0.5, 1, 2, 3, 4, 6, 8]
for name in ("train_0033_plain", "train_0033_hi", "train_0033_cond", "train_0081_plain", "train_0081_cond"):
    R = [json.loads(l) for l in open(base + name + ".jsonl") if l.strip()]
    head = R[0]; recs = [r for r in R if "step" in r and "raw" in r]; end = [r for r in R if r.get("end")]
    print(f"\n=== {name}: {head['steps']} steps, lr {head['lr']}, warm-up {head.get('warmup')}, device {head['device']}; seconds {end[0]['seconds'] if end else '?'}")
    keys = ["raw"] + (["cond"] if "cond" in recs[0] else [])
    for k in keys:
        print(f"  [{k} field]   step | energy gap % at D = 0.5, 1, 2, 3, 4, 6, 8 mm | end-displacement error % | bolt-force error % at 4, 6, 8")
        for r in recs:
            if r["step"] in (0, 25, 50, 100, 200, 300, 400, 500, 600):
                print(f"     {r['step']:4d} | " + " ".join(f"{100*v:6.2f}" for v in r[k]["gap"]) + " | " + " ".join(f"{100*v:+6.1f}" for v in r[k]["e_err"]) + " | " + " ".join(f"{100*v:+6.1f}" for v in r[k]["bolt_err"][4:]))
    if "a" in recs[-1]: print("  condensed amplitudes a at the seven levels: start", recs[0]["a"], "| end", recs[-1]["a"])
    g0, g1 = np.array(recs[0]["raw"]["gap"]), np.array(recs[-1][keys[-1]]["gap"])
    print(f"  gap at 8 mm: {100*g0[6]:.2f}% -> {100*g1[6]:.2f}% ; at 6 mm: {100*g0[5]:.2f}% -> {100*g1[5]:.2f}% ; at 4 mm: {100*g0[4]:.2f}% -> {100*g1[4]:.2f}% ; small levels (0.5, 1, 2): {np.round(100*g0[:3], 2)} -> {np.round(100*g1[:3], 2)}")
