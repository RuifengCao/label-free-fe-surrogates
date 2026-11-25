"""Readings of the snapshots of single-member runs against the member's reference path (sandbox diagnostic)."""
import json, sys
import numpy as np

data, member = sys.argv[1], sys.argv[2]
lab = np.load(f"{data}/labels/{member}.npz")
ref = {k: np.asarray(lab[k], float) for k in ("theta", "ThetaD", "M", "Pi", "lam")}
print("levels (fraction of the device range):", ref["lam"].tolist())
for run in sys.argv[3:]:
    try:
        snaps = json.load(open(f"{run}/label_free_s0/snapshots.json"))
    except OSError:
        print(run, "no snapshots"); continue
    print(run.rstrip("/").split("/")[-1])
    for ep in sorted(snaps, key=int):
        s = snaps[ep][member]
        th = np.asarray(s["theta"]) / ref["theta"]
        tD = np.asarray(s["ThetaD"]) / ref["ThetaD"]
        Me = np.asarray(s["M"]) / ref["M"] - 1.0
        Pe = np.asarray(s["Pi"]) / ref["Pi"] - 1.0
        f = lambda a, p=2: "[" + " ".join(f"{x:.{p}f}" for x in a) + "]"
        print(f"  step {int(ep):4d}: theta/ref {f(th)}  ThetaD/ref {f(tD)}  M err% {f(100 * Me, 0)}  energy excess% {f(100 * Pe, 1)}")
