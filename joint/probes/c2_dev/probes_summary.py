"""How steady the probes stayed in each development run: the latents' relative variance, the first block's MLP output,
the head's e/(D+delta) at 8 mm; the largest fall between two probes; what the probes show after the largest bursts."""
import sys, json
import numpy as np
for run in sys.argv[1:]:
    R = [json.loads(l) for l in open(f"{run}/steps.jsonl") if l.strip()]
    S = json.load(open(f"{run}/summary.json"))
    pr = [(r["step"], r["probe"]) for r in R if "probe" in r and "step" in r and "end" not in r]
    st = np.array([s for s, _ in pr]); rv = np.array([np.mean(p["latent_rel_var"]) for _, p in pr])
    ms = np.array([p["first_block"]["mlp_ms"] for _, p in pr]); es = np.array([p["e_over_s"][2] for _, p in pr])
    late = st >= 512
    fall = rv[:-1] / np.maximum(rv[1:], 1e-12); k = int(np.argmax(np.where(st[1:] >= 512, fall, 0)))
    print(f"\n{S['name']} ({S['recipe']}, seed {S['seed']}, {S['steps']} steps): probes {len(pr)}")
    print(f"  relative variance from step 512 on: min {rv[late].min():.4f} at step {st[late][rv[late].argmin()]}, median {np.median(rv[late]):.4f}; largest fall between two probes: {rv[k]:.4f} -> {rv[k+1]:.4f} at step {st[k+1]} (factor {fall[k]:.2f})")
    print(f"  first block's MLP mean square: median {np.median(ms[late]):.0f}, max {ms[late].max():.0f} at step {st[late][ms[late].argmax()]}, last {ms[-1]:.0f}")
    print(f"  e/(D+delta) at 8 mm from step 512 on: min {es[late].min():.4f}, last {es[-1]:.4f}")
    big = sorted(S["bursts"], key=lambda b: -b["ratio"])[:3]
    for b in sorted(big, key=lambda b: b["step"]):
        j = int(np.searchsorted(st, b["step"]))
        seq = [(int(st[i]), round(float(rv[i]), 3), int(ms[i])) for i in range(max(j - 1, 0), min(j + 4, len(st)))]
        print(f"  burst of {b['ratio']:.0f} times at step {b['step']}: (step, relative variance, first-block mean square) {seq}")
    loss = np.array([r["loss"] for r in R if "loss" in r])
    print(f"  non-finite losses: {int((~np.isfinite(loss)).sum())}; seconds per step median {np.median([v / S['members'] for v in S['epoch_seconds']]):.3f}")
