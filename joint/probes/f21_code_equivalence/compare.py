"""Compare two stand-in trainings made by run_one.py: the losses of every epoch and every tensor of the final states.

    python3 -I compare.py RUN_A RUN_B          (the folders that hold history.json and state.pt)"""
import json
import pathlib
import sys

import torch

a, b = (pathlib.Path(p) for p in sys.argv[1:3])
ha, hb = (json.loads((p / "history.json").read_text()) for p in (a, b))
sa, sb = (torch.load(p / "state.pt", map_location="cpu", weights_only=False) for p in (a, b))
out = {"configuration equal": ha["config_sha256"] == hb["config_sha256"], "status": [ha["status"], hb["status"]],
       "steps": [ha["steps"], hb["steps"]], "losses equal to the last bit": ha["loss"] == hb["loss"],
       "largest difference of a loss": max(abs(x - y) for x, y in zip(ha["loss"], hb["loss"]))}
n = diff = 0
worst = 0.0
for k in ("enc", "dec", "head"):
    assert sorted(sa[k]) == sorted(sb[k])
    for name in sa[k]:
        x, y = sa[k][name], sb[k][name]
        n += 1
        if not torch.equal(x, y):
            diff += 1
            worst = max(worst, float((x.double() - y.double()).abs().max()))
out.update({"tensors of the final states": n, "tensors that differ": diff, "largest difference of a weight": worst})
print(json.dumps(out))
