"""R0-a: which training members to solve. Stratified at random: fy < 300 MPa ('weak') and the rest, alternating."""
import json, sys
import numpy as np
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
man = json.load(open(paths.data() / "manifest.json"))
tr = [r for r in man["instances"] if r["split"] == "train"]
rng = np.random.default_rng(20261111)
weak = [r["id"] for r in tr if r["params"]["fy"] < 300]
rest = [r["id"] for r in tr if r["params"]["fy"] >= 300]
w = list(rng.permutation(weak)[:16]); o = list(rng.permutation(rest)[:16])
order = [x for pair in zip(w, o) for x in pair]
json.dump({"seed": 20261111, "weak": w, "rest": o, "order": order}, open(paths.work() / "selection.json", "w"), indent=1)
par = {r["id"]: r["params"] for r in tr}
for i in order[:8]: print(i, {k: round(v, 1) for k, v in par[i].items()})
print(len(weak), len(rest), len(order))
