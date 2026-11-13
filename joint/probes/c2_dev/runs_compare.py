"""Exploratory: the laptop development runs against the host's G-C2.1 runs of the same seed.
(1) per-epoch training loss, laptop run minus host run (same seed draws the same members and loading levels, so the
    difference is the model's); (2) mean loss over blocks of ten epochs; (3) bursts and cap events by epoch."""
import json, sys
import numpy as np
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
B = sys.argv[1] if len(sys.argv) > 1 else str(paths.runs()) + "/"
H = sys.argv[2] if len(sys.argv) > 2 else str(paths.ret() / "runs") + "/"
host = {s: json.load(open(f"{H}label_free_s{s}/history.json"))["loss"] for s in (0, 1, 2)}
names = ("L1_control_s0", "L1_control_s1", "L2_recipe_s0", "L2_recipe_s1", "L2_recipe_s3", "L2_recipe_s4")
runs = {n: json.load(open(B + n + "/summary.json")) for n in names}
for n in names:
    s = runs[n]; L = s["epoch_loss"]; seed = s["seed"]
    print(f"\n{n}: status '{s['status']}', epochs {s['epochs_done']}, steps {s['steps']}, bursts {len(s['bursts'])}"
          f" (largest {max([b['ratio'] for b in s['bursts']], default=0):.0f} times), cap events {len(s['cap_events'])}, collapses {len(s['collapses'])}")
    print("   bursts (step, epoch, ratio): " + ", ".join(f"({b['step']}, {1 + b['step'] // 512}, {b['ratio']:.0f})" for b in s["bursts"]))
    if s["cap_events"]:
        ep = [1 + (c["step"] if isinstance(c, dict) else c) // 512 for c in s["cap_events"]]
        print("   cap events in epochs 1-5, 6-10, ..., 26-30:", np.histogram(ep, bins=[1, 6, 11, 16, 21, 26, 31])[0].tolist())
    print("   seconds per step, median over epochs: %.3f" % np.median(np.array(s["epoch_seconds"]) / 512))
    if seed in host:
        d = np.array(L) - np.array(host[seed][:len(L)])
        print("   loss minus host's same seed, by epoch: " + " ".join(f"{x:+.3f}" for x in d))
print("\nmean loss over epochs 1-10 / 11-20 / 21-30:")
for tag, L in [(f"host seed {s}", host[s]) for s in (0, 1, 2)] + [(n, runs[n]["epoch_loss"]) for n in names if runs[n]["epochs_done"] >= 30]:
    print(f"   {tag:16s} " + " / ".join(f"{np.mean(L[a:b]):.4f}" for a, b in ((0, 10), (10, 20), (20, 30))))
