"""Regenerate the held-out and tested instances of G-C2.1 with the stamped code (no solve). Exploratory analysis."""
import sys, time, json
JOINT, DATA = sys.argv[1], sys.argv[2]
sys.path.insert(0, JOINT)
from c2 import config, data
cfg = config.config()
print("config sha", config.sha256(cfg))
t0 = time.time()
p = data.generate(cfg, DATA, splits=("eval", "tested"))
print("generated", p, round(time.time() - t0, 1), "s")
man = json.load(open(p))
print(man["n"], man["instances"][0]["nodes"], man["instances"][0]["unknowns"])
