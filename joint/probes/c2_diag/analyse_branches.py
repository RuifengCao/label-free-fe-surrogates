"""Read the branch runs of one seed (exploratory, after the G-C2.1 verdict).

    python3 -I analyse_branches.py OUT.json REPLAY_JSONL BRANCH_JSONL [BRANCH_JSONL ...]

REPLAY_JSONL is the replay the branches left (diag_seed.py); the BRANCH_JSONL files are branch.py's records, one per
variant, the control among them. Prints and writes, per branch:
- for the control, whether every step's loss and gradient norms equal the replay's (bit for bit);
- the probes: the relative variance of the encoder's node latents (mean over the three probe displacements), the same
  after the input layer and before the encoder's final LayerNorm, the median |gain| of that LayerNorm, e / (D + delta),
  and, where branch.py recorded them, the mean square and relative variance after the first block and the mean square
  and node variance of that block's MLP output;
- the lowest relative variance of the latents and its step, and whether the branch collapsed (a probe below a third of
  the branch's first probe);
- the encoder bursts (a step whose encoder gradient norm exceeds ten times its median over the previous 256 steps,
  the replay supplying the steps before the branch) and the steps at which the encoder's gradient was capped
  (variant enc_cap);
- the mean difference of the loss from the control's, over all steps of the branch and over its last 128 (every step
  draws the same member and displacements in every branch).
"""
import json
import sys
from pathlib import Path

import numpy as np

out_path, replay_path, paths = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3:]
replay = {r["step"]: r for r in (json.loads(l) for l in open(replay_path) if l.strip()) if "loss" in r}
runs = {}
for p in paths:
    rows = [json.loads(l) for l in open(p) if l.strip()]
    head = rows[0]
    st = [r for r in rows if "loss" in r]
    pr = [(r["step"], r["probe"]) for r in rows if "probe" in r]
    assert any("done" in r for r in rows), f"{p} did not finish"
    runs[head["variant"]] = {"head": head, "steps": st, "probes": pr}
ctrl = runs["control"]
rs = [replay[k]["grad"]["enc"] for k in sorted(replay)]
ratio = np.array([rs[i] / np.median(rs[i - 256:i]) for i in range(256, len(rs))])
summary = {"replay_share_over_5": float((ratio > 5).mean()), "replay_share_over_10": float((ratio > 10).mean()),
           "replay_steps_rated": int(len(ratio))}
print(f"replay: {100 * (ratio > 5).mean():.2f}% of its steps from step 257 exceed five times the median of the previous "
      f"256, {100 * (ratio > 10).mean():.2f}% ten times ({len(ratio)} steps)")
for v, run in runs.items():
    st, pr = run["steps"], run["probes"]
    assert [r["step"] for r in st] == [r["step"] for r in ctrl["steps"]], f"{v}: steps differ from the control's"
    assert all(r["inst"] == c["inst"] and r["D"] == c["D"] for r, c in zip(st, ctrl["steps"])), f"{v}: draws differ"
    lat = [(s, float(np.mean(p["latent_rel_var"]))) for s, p in pr]
    s_min, v_min = min(lat, key=lambda x: x[1])
    diff = np.array([r["loss"] - c["loss"] for r, c in zip(st, ctrl["steps"])])
    b0 = run["head"]["branch_at_step"]
    enc = [replay[k]["grad"]["enc"] for k in range(b0 - 255, b0 + 1)] + [r["grad"]["enc"] for r in st]
    bursts = [(r["step"], r["grad"]["enc"], r["grad"]["enc"] / float(np.median(enc[k:k + 256])))
              for k, r in enumerate(st) if r["grad"]["enc"] > 10 * float(np.median(enc[k:k + 256]))]
    res = {"branch_at_step": b0, "steps": len(st), "bursts": bursts,
           "probes": [{"step": s, "latent_rel_var": float(np.mean(p["latent_rel_var"])),
                       "pre_norm_rel_var": p["stage_rel_var"][-2], "norm_gain_abs_median": p["norm_gain_abs_median"],
                       "e_over_s": float(np.mean(p["e_over_s"])), "stage_rel_var": p["stage_rel_var"],
                       **({"stage_ms": p["stage_ms"], "stage_node_var": p["stage_node_var"], "first_block": p["first_block"]}
                          if "stage_ms" in p else {})}
                      for s, p in pr],
           "lowest_latent_rel_var": v_min, "lowest_at_step": s_min, "collapsed": v_min < lat[0][1] / 3,
           "capped_steps": [(r["step"], r["cap_scale"]) for r in st if "cap_scale" in r],
           "loss_minus_control_mean": float(diff.mean()), "loss_minus_control_last128": float(diff[-128:].mean())}
    if v == "control":
        res["identical_to_replay"] = all(r["loss"] == replay[r["step"]]["loss"] and r["grad"] == replay[r["step"]]["grad"]
                                         and r["grad_total"] == replay[r["step"]]["grad_total"] for r in st)
    summary[v] = res
out_path.write_text(json.dumps(summary, indent=1))
for v, r in summary.items():
    if not isinstance(r, dict):
        continue
    print(f"=== {v}: branch at step {r['branch_at_step']}, {r['steps']} steps")
    if "identical_to_replay" in r:
        print(f"  identical to the replay at every step: {r['identical_to_replay']}")
    print(f"  lowest latent relative variance {r['lowest_latent_rel_var']:.4f} at step {r['lowest_at_step']}; "
          f"collapsed: {r['collapsed']}")
    print(f"  loss minus control: mean {r['loss_minus_control_mean']:+.4f}, last 128 steps {r['loss_minus_control_last128']:+.4f}")
    print(f"  encoder bursts (> 10 times the median of the previous 256 steps): "
          + (", ".join(f"{s} ({x:.0f} times)" for s, _, x in r["bursts"]) or "none"))
    if r["capped_steps"]:
        print(f"  capped at {len(r['capped_steps'])} steps: " + ", ".join(f"{s} ({c:.3f})" for s, c in r["capped_steps"]))
    for p in r["probes"]:
        extra = ""
        if "stage_ms" in p:
            fb = p["first_block"]
            extra = (f"; after the first block: mean square {p['stage_ms'][1]:.0f}, node variance {p['stage_node_var'][1]:.0f}, "
                     f"relative variance {p['stage_rel_var'][1]:.3f}; "
                     f"its MLP output: mean square {fb['mlp_ms']:.0f}, node variance {fb['mlp_node_var']:.0f}")
        print(f"    step {p['step']}: latents {p['latent_rel_var']:.4f}, input layer {p['stage_rel_var'][0]:.3f}, "
              f"before the final norm {p['pre_norm_rel_var']:.4f}, |gain| median {p['norm_gain_abs_median']:.4f}, "
              f"e/(D+delta) {p['e_over_s']:.4f}" + extra)
