"""The host's label-free loss histories with the effect of the drawn displacements removed (exploratory, after the
G-C2.1 verdict).

    python3 -I analyse_host.py JOINT_DIR RECORDS_DIR OUT.json seed0.jsonl seed1.jsonl

An epoch's mean loss moves with the loading-device displacements D that the epoch drew: the loss is the log of the
energy, which grows with D. The draws depend on the seed alone (numpy's default_rng: a permutation of the 512
training members each epoch, then four D a step, by c2.train.sample_D), so they are drawn again here and checked
against the replays' records. Each epoch gets X, the mean over its steps of the mean of ln D, and Q, the same for
(ln D)^2. Within a run, L_e = a(block of 5 epochs) + b1 X_e + b2 Q_e is fitted by least squares to the host's 200
epoch means of the three seeds together (one set of block levels per seed, b1 and b2 shared). The adjusted mean
L_e - b1 (X_e - mean X) - b2 (Q_e - mean Q) is what the epoch would have shown at the average draw. A second fit,
to the replays' single steps before their first collapse with one level per member, checks b1 and b2.
"""
import json
import sys
from pathlib import Path

import numpy as np

joint, rec, out_path = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
replays = sys.argv[4:]
sys.path.insert(0, joint)
sys.path.insert(0, str(Path(joint).parent / "src"))
from c2.config import config  # noqa: E402
from c2.train import sample_D  # noqa: E402

cfg = config()
epochs, B = cfg["arms"]["label_free"]["epochs"], cfg["training"]["fields_per_step"]
h0 = json.loads((rec / "runs" / "label_free_s0" / "history.json").read_text())
n_train = h0["total_steps"] // epochs                 # one step per training member and epoch: 512
assert n_train * epochs == h0["total_steps"] == 102400


def draws(seed):
    rng = np.random.default_rng(seed)
    inst, D = np.empty((epochs, n_train), int), np.empty((epochs, n_train, B))
    for e in range(epochs):
        inst[e] = rng.permutation(n_train)
        for k in range(n_train):
            D[e, k] = sample_D(rng, cfg, B)
    return inst, D


seeds = (0, 1, 2)
dr = {s: draws(s) for s in seeds}
out = {"check_against_replays": {}, "fit_host": {}, "fit_replay": {}, "adjusted": {}}

# 1. the regenerated draws against the replays' records
rep = {}
for path in replays:
    rows = [json.loads(l) for l in open(path) if l.strip()]
    s = next(r for r in rows if "seed" in r)["seed"]
    st = [r for r in rows if "loss" in r]
    inst, D = dr[s]
    ok_i = all(int(r["inst"]) == int(inst.reshape(-1)[r["step"] - 1]) for r in st)
    dmax = max(float(np.max(np.abs(np.array(r["D"]) - D.reshape(-1, B)[r["step"] - 1]))) for r in st)
    out["check_against_replays"][s] = {"steps": len(st), "members_equal": ok_i, "max_abs_D_difference": dmax}
    rep[s] = st
    print(f"seed {s}: {len(st)} replayed steps, members equal: {ok_i}, largest |D difference| {dmax:.2e} (D logged to 4 decimals)")

# 2. fit on the host's epoch means
hist = {s: np.array(json.loads((rec / "runs" / f"label_free_s{s}" / "history.json").read_text())["loss"]) for s in seeds}
lnD = {s: np.log(dr[s][1]) for s in seeds}
X = {s: lnD[s].mean(axis=(1, 2)) for s in seeds}
Q = {s: (lnD[s] ** 2).mean(axis=(1, 2)) for s in seeds}
blk = 5
rows, y = [], []
nb = epochs // blk
for j, s in enumerate(seeds):
    for e in range(epochs):
        r = np.zeros(len(seeds) * nb + 2)
        r[j * nb + e // blk] = 1.0
        r[-2], r[-1] = X[s][e], Q[s][e]
        rows.append(r); y.append(hist[s][e])
A, y = np.array(rows), np.array(y)
coef, *_ = np.linalg.lstsq(A, y, rcond=None)
res = y - A @ coef
b1, b2 = coef[-2], coef[-1]
dof = len(y) - A.shape[1]
cov = np.linalg.inv(A.T @ A) * (res @ res / dof)
out["fit_host"] = {"b1": b1, "b2": b2, "se_b1": float(np.sqrt(cov[-2, -2])), "se_b2": float(np.sqrt(cov[-1, -1])),
                   "residual_sd": float(res.std(ddof=0)), "block_epochs": blk}
print(f"host fit: b1 {b1:.4f} (se {np.sqrt(cov[-2, -2]):.4f}), b2 {b2:.4f} (se {np.sqrt(cov[-1, -1]):.4f}), "
      f"residual sd {res.std():.4f}")
# slope of the epoch loss in ln D at the average draw, for reading b1 and b2 together
Xbar = float(np.mean([X[s] for s in seeds])); Qbar = float(np.mean([Q[s] for s in seeds]))
mean_lnD = float(np.mean([lnD[s].mean() for s in seeds]))
print(f"  slope d(loss)/d(ln D) at the mean ln D ({mean_lnD:.3f}): {b1 + 2 * b2 * mean_lnD:.3f}")
out["fit_host"]["slope_at_mean_lnD"] = float(b1 + 2 * b2 * mean_lnD)

# 3. check: fit on the replays' steps before their first collapse, one level per member
before_collapse = {0: 2752, 1: 1856}     # the last probe before each replay's collapse (analyse_replays.py)
Xs, Qs, ys, mem, sd = [], [], [], [], []
for s, st in rep.items():
    for r in st:
        if r["step"] <= before_collapse[s]:
            l = np.log(np.array(r["D"]))
            Xs.append(l.mean()); Qs.append((l ** 2).mean()); ys.append(r["loss"]); mem.append(r["inst"]); sd.append(s)
Xs, Qs, ys, mem, sd = map(np.array, (Xs, Qs, ys, mem, sd))
um = np.unique(mem)
M = (mem[:, None] == um[None, :]).astype(float)
S1 = (sd == 1).astype(float)[:, None]
A2 = np.hstack([M, S1, Xs[:, None], Qs[:, None]])
c2_, *_ = np.linalg.lstsq(A2, ys, rcond=None)
r2 = ys - A2 @ c2_
out["fit_replay"] = {"steps": int(len(ys)), "b1": float(c2_[-2]), "b2": float(c2_[-1]), "residual_sd": float(r2.std()),
                     "raw_sd": float(ys.std()), "slope_at_mean_lnD": float(c2_[-2] + 2 * c2_[-1] * mean_lnD)}
print(f"replay fit ({len(ys)} steps, {len(um)} member levels): b1 {c2_[-2]:.4f}, b2 {c2_[-1]:.4f}, "
      f"slope at mean ln D {c2_[-2] + 2 * c2_[-1] * mean_lnD:.3f}; step loss sd {ys.std():.3f} raw, {r2.std():.3f} after")

# 4. adjusted epoch means
for s in seeds:
    adj = hist[s] - b1 * (X[s] - Xbar) - b2 * (Q[s] - Qbar)
    blocks = {}
    for a, b in ((0, 5), (5, 10), (10, 20), (20, 50), (50, 100), (100, 150), (150, 200)):
        blocks[f"{a + 1}-{b}"] = {"raw": float(hist[s][a:b].mean()), "adjusted": float(adj[a:b].mean())}
    late_sd = {"raw": float(hist[s][100:].std()), "adjusted": float(adj[100:].std())}
    out["adjusted"][s] = {"epochs": adj.tolist(), "blocks": blocks, "sd_epochs_101_200": late_sd}
    # rises: an epoch more than 0.03 above the median of the (up to five) epochs before it, from epoch 4 on
    rises = [{"epoch": e + 1, "adjusted": float(adj[e]), "median_before": float(np.median(adj[max(0, e - 5):e]))}
             for e in range(3, epochs) if adj[e] - np.median(adj[max(0, e - 5):e]) > 0.03]
    out["adjusted"][s]["rises_over_0.03"] = rises
    print(f"=== seed {s}")
    print("  epochs 1-24 adjusted:", np.round(adj[:24], 3).tolist())
    print("  epochs 1-24 raw:     ", np.round(hist[s][:24], 3).tolist())
    for k, v in blocks.items():
        print(f"  epochs {k:>7}: raw {v['raw']:.4f}, adjusted {v['adjusted']:.4f}")
    print(f"  sd of the epoch means over epochs 101-200: raw {late_sd['raw']:.4f}, adjusted {late_sd['adjusted']:.4f}")
    for r in rises:
        print(f"  rise in epoch {r['epoch']}: {r['adjusted']:.3f} against a median of {r['median_before']:.3f} before "
              f"(+{r['adjusted'] - r['median_before']:.3f})")
    if s == 0:
        tail = adj[7:]
        out["adjusted"][s]["epochs_8_200"] = {"mean": float(tail.mean()), "sd": float(tail.std()),
                                              "min": float(tail.min()), "max": float(tail.max())}
        print(f"  epochs 8-200: mean {tail.mean():.4f}, sd {tail.std():.4f}, range {tail.min():.4f} to {tail.max():.4f}")
    if s == 1:
        out["adjusted"][s]["epochs_15_18_mean"] = float(adj[14:18].mean())
        print(f"  epochs 15-18: mean {adj[14:18].mean():.4f}")
for s, st in rep.items():
    loss = np.array([r["loss"] for r in st])
    em = loss[: len(loss) // n_train * n_train].reshape(-1, n_train).mean(1)
    k = len(em)
    adj_rep = em - b1 * (X[s][:k] - Xbar) - b2 * (Q[s][:k] - Qbar)
    out["adjusted"][s]["replay_epochs"] = adj_rep.tolist()
    print(f"  replay seed {s} adjusted epochs 1-{k}:", np.round(adj_rep, 3).tolist())
out_path.write_text(json.dumps(out, indent=1))
