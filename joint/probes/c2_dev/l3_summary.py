"""L3: the full-length recipe run of seed 0 (cap + beta2 = 0.99, 200 epochs) against the host's G-C2.1 runs.

(1) per-epoch training loss against the host's runs (the same seed draws the same members and loading levels, so the
    difference to the host's seed 0 is the model's); (2) bursts, cap events and collapses by block of epochs;
(3) the latents' relative variance at the probes; (4) the reading on the 64 former held-out members (raw, condensed)
    against a stored reading of another model.

    python l3_summary.py RUN_DIR HOST_RUNS_DIR [EVAL_JSON [OTHER_EVAL_JSON]]
"""
import json
import sys

import numpy as np

run, H = sys.argv[1], sys.argv[2]
S = json.load(open(f"{run}/summary.json"))
host = {s: json.load(open(f"{H}/label_free_s{s}/history.json"))["loss"] for s in (0, 1, 2)}
L = np.array(S["epoch_loss"])
print(f"{S['name']}: status {S['status']}, seed {S['seed']}, recipe {S['recipe']}, epochs {S['epochs_done']}, steps {S['steps']},"
      f" bursts {len(S['bursts'])}, cap events {len(S['cap_events'])}, collapses {len(S['collapses'])}, resumes {len(S.get('resumes', []))}")
print("\nmean training loss by block of epochs")
blocks = [(0, 10), (10, 20), (20, 30), (30, 60), (60, 100), (100, 150), (150, 180), (180, 190), (190, 200)]
print("  block      " + "  ".join(f"{a + 1:3d}-{b:<3d}" for a, b in blocks))
for tag, arr in [("host seed 0", host[0]), ("host seed 1", host[1]), ("host seed 2", host[2]), ("this run   ", L)]:
    print(f"  {tag}" + "  ".join(f"{np.mean(arr[a:b]):7.4f}" for a, b in blocks))
d = L - np.array(host[S["seed"]][:len(L)])
print("  this run minus the host's same seed, by block: " + "  ".join(f"{np.mean(d[a:b]):+.4f}" for a, b in blocks))
print(f"  epochs with a lower loss than the host's same seed: {int((d < 0).sum())} of {len(d)}; last 20 epochs: {int((d[-20:] < 0).sum())} of 20")
for s in (0, 1, 2):
    print(f"  host seed {s}: epochs with loss above 10.8 after epoch 10: {int((np.array(host[s][10:]) > 10.8).sum())}; max after epoch 10: {max(host[s][10:]):.3f}; last epoch {host[s][-1]:.4f}")
print(f"  this run   : epochs with loss above 10.8 after epoch 10: {int((L[10:] > 10.8).sum())}; max after epoch 10: {L[10:].max():.3f}; last epoch {L[-1]:.4f}")

bs = np.array([b["step"] for b in S["bursts"]]); br = np.array([b["ratio"] for b in S["bursts"]])
cs = np.array([(c["step"] if isinstance(c, dict) else c) for c in S["cap_events"]])
edges = [0, 30, 60, 100, 150, 200]
print("\nbursts over ten times the running median, and cap events, by block of epochs")
for a, b in zip(edges[:-1], edges[1:]):
    m = (bs >= a * 512) & (bs < b * 512)
    print(f"  epochs {a + 1:3d}-{b:<3d}: bursts {int(m.sum()):3d} (largest {br[m].max() if m.any() else 0:6.0f} times), cap events {int(((cs >= a * 512) & (cs < b * 512)).sum()):4d}")
print(f"  bursts over 100 times: {int((br > 100).sum())}; over 1000 times: {int((br > 1000).sum())}; largest {br.max():.0f} times at step {int(bs[br.argmax()])} (epoch {1 + int(bs[br.argmax()]) // 512})")

pr = []
for l in open(f"{run}/steps.jsonl"):
    if '"probe"' in l:
        r = json.loads(l)
        if "step" in r and "end" not in r:
            pr.append((r["step"], float(np.mean(r["probe"]["latent_rel_var"]))))
st = np.array([p[0] for p in pr]); rv = np.array([p[1] for p in pr])
late = st >= 512
fall = rv[:-1] / np.maximum(rv[1:], 1e-12)
k = int(np.argmax(np.where(st[1:] >= 512, fall, 0)))
print(f"\nprobes {len(pr)}: latent relative variance from step 512 on: min {rv[late].min():.4f} at step {int(st[late][rv[late].argmin()])},"
      f" median {np.median(rv[late]):.4f}, last {rv[-1]:.4f}; largest fall between two probes {rv[k]:.4f} -> {rv[k + 1]:.4f} at step {int(st[k + 1])} (factor {fall[k]:.2f})")
print(f"seconds per step, median over epochs: {np.median(np.array(S['epoch_seconds']) / 512):.3f}")

if len(sys.argv) > 3:
    names = {0: "mode 1", 1: "mode 2", 3: "web"}

    def st3(rows, key):
        J = np.abs([r[key]["J"] for r in rows])
        return f"{100 * np.median(J):5.2f} / {100 * np.percentile(J, 90):5.2f} / {int((J > 0.1).sum()):3d} of {len(J)}"

    for path in sys.argv[3:]:
        E = json.load(open(path))
        rows = E["rows"]
        print(f"\n{path.split('/')[-2]}/{path.split('/')[-1]}: raw {st3(rows, 'raw')} | condensed {st3(rows, 'cond')}")
        for mch in sorted({r["mechanism"] for r in rows}):
            sub = [r for r in rows if r["mechanism"] == mch]
            print(f"    {names.get(mch, mch):8s} raw {st3(sub, 'raw')} | condensed {st3(sub, 'cond')}")
        for D in sorted({r["D"] for r in rows}):
            sub = [r for r in rows if r["D"] == D]
            g = [100 * np.median([r[k]["gap"] for r in sub]) for k in ("raw", "cond")]
            print(f"    D = {D:<4g} raw {st3(sub, 'raw')} | condensed {st3(sub, 'cond')} | gap median raw {g[0]:.3f}% condensed {g[1]:.3f}%")
        over = [(r["id"], r["D"], round(100 * r["cond"]["J"], 1)) for r in rows if abs(r["cond"]["J"]) > 0.1]
        print(f"    condensed pairs over 10%: {over if len(over) <= 12 else len(over)}")
        raw_over = {}
        for r in rows:
            if abs(r["raw"]["J"]) > 0.1:
                raw_over.setdefault(r["id"], []).append((r["D"], round(100 * r["raw"]["J"], 1)))
        print(f"    raw: members with a pair over 10%: {len(raw_over)}; signs: over-stiff {sum(r['raw']['J'] > 0.1 for r in rows)}, over-soft {sum(r['raw']['J'] < -0.1 for r in rows)}")
        a = np.array([r["a"] for r in rows])
        print(f"    amplitude a: median {np.median(a):.3f}, range {a.min():.3f} to {a.max():.3f}; solve {E.get('solve')}")
        print(f"    worst raw pairs: {sorted([(round(100 * abs(r['raw']['J']), 1), r['id'], r['D']) for r in rows])[-5:]}")
