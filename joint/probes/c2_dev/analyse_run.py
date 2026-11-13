"""Summarise a development run's records (steps.jsonl, summary.json): epochs, bursts, cap events, collapses, the
probes around a collapse, inactive units."""
import sys, json
import numpy as np
run = sys.argv[1]
R = [json.loads(l) for l in open(f"{run}/steps.jsonl") if l.strip()]
S = json.load(open(f"{run}/summary.json"))
steps = [r for r in R if "loss" in r]
print(f"{S['name']}: status {S['status']}; recipe {S['recipe']} betas {S['betas']} cap {S['cap']}; seed {S['seed']}; epochs done {S['epochs_done']}; steps {S['steps']}; gpu {S.get('gpu')}; peak memory {S.get('peak_memory_GiB')}")
print("  epoch losses:", [round(v, 4) for v in S["epoch_loss"]], "| seconds per step by epoch:", [round(v / S["members"], 3) for v in S["epoch_seconds"]])
enc = np.array([r["grad"]["enc"] for r in steps]); dec = np.array([r["grad"]["dec"] for r in steps]); tot = np.array([r["grad_total"] for r in steps])
print(f"  gradient norms over {len(steps)} steps: encoder median {np.median(enc):.3f}, decoder median {np.median(dec):.1f}, global median {np.median(tot):.1f}; steps with the global norm above the clip of 1: {int((tot > 1).sum())}")
print(f"  bursts (encoder norm above 10 times its median over the 256 steps before): {len(S['bursts'])}:", [(b["step"], round(b["ratio"], 1)) for b in S["bursts"]][:20])
print(f"  cap events: {len(S['cap_events'])}", [(b["step"], round(b["ratio"], 1)) for b in S["cap_events"]][:12], "..." if len(S["cap_events"]) > 12 else "")
print(f"  collapses: {S['collapses']}")
pr = [(r["step"], r["probe"]) for r in R if "probe" in r and "step" in r]
rv = [(s, float(np.mean(p["latent_rel_var"]))) for s, p in pr]
print("  latent relative variance at probes: min %.4f at step %d; last %.4f" % (min(rv, key=lambda t: t[1])[1], min(rv, key=lambda t: t[1])[0], rv[-1][1]))
if S["collapses"]:
    c = S["collapses"][0]["step"]
    print("  around the first collapse (step, relative variance, first-block MLP mean square, node variance after block 1, e/(D+delta) at 8 mm):")
    for s, p in pr:
        if c - 260 <= s <= c + 200 or s == pr[-1][0]:
            print(f"     {s:6d}  {np.mean(p['latent_rel_var']):.4f}   {p['first_block']['mlp_ms']:10.1f}   {p['stage_node_var'][1]:9.1f}   {p['e_over_s'][2]:.4f}")
    b = [x for x in S["bursts"] if c - 128 <= x["step"] <= c]
    print("  bursts in the 128 steps before the collapse probe:", [(x["step"], round(x["ratio"], 1)) for x in b])
un = [(r.get("step"), r["units"]) for r in R if "units" in r]
print("  inactive units (share of units whose largest GELU input is below -3 / below -5): step: dec1, dec2, head1, head2")
for s, u in un[:1] + un[-4:]:
    print(f"     {s}: " + ", ".join(f"{k} {100*u[k]['below_-3']:.1f}%/{100*u[k]['below_-5']:.1f}%" for k in ("dec1", "dec2", "head1", "head2")))
