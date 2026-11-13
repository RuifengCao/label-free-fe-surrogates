"""The GPU run of seed 0 without the recipe against the CPU replay of ../c2_diag, step by step (written for this
note): the member and the displacements drawn at each step, and the difference of the losses.

    python -I draws_check.py
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
import json

gpu = {r["step"]: r for r in map(json.loads, open(paths.runs() / "L1_control_s0" / "steps.jsonl")) if "loss" in r}
cpu = {r["step"]: r for r in map(json.loads, open(paths.HERE.parent / "c2_diag" / "records" / "seed0.jsonl")) if "loss" in r}
steps = sorted(set(gpu) & set(cpu))
print(f"steps in both records: {len(steps)}; the same member at {sum(gpu[k]['inst'] == cpu[k]['inst'] for k in steps)};"
      f" the same displacements at {sum(gpu[k]['D'] == cpu[k]['D'] for k in steps)}")
print("first four steps (member, loss on the GPU, loss in the replay):", [(gpu[k]["inst"], gpu[k]["loss"], cpu[k]["loss"]) for k in steps[:4]])
for n in (4, 64, 256, 1024, len(steps)):
    print(f"largest difference of the losses over the first {n} steps: {max(abs(gpu[k]['loss'] - cpu[k]['loss']) for k in steps[:n]):.1e}")
