"""One stand-in training with the f2 package of a given tree, on a processor (made on 25 November 2026, before the
stamp of gate G-F2.1, to compare the development's code as the recipe's runs had it with the stamped code).

    python3 -I run_one.py TREE PRESET DATA OUT [--init-from STATE] [--extra-data DIR] [--seed 0] [--epochs N]

TREE holds joint/ and src/. PRESET is a development preset at stand-in size ("dry", "dry_more_ux"), run on the
smaller mesh with one thread; --epochs sets another number of epochs than the preset's three. Prints the SHA-256 of
the run configuration and of the tree's f2 files."""
import argparse
import hashlib
import inspect
import json
import os
import pathlib
import sys

for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[k] = "1"
os.environ["FEJOINT_SOLVER"] = "legacy"                   # as the training commands: no sparse solver in this process
sys.dont_write_bytecode = True
ap = argparse.ArgumentParser()
for x in ("tree", "preset", "data", "out"):
    ap.add_argument(x)
ap.add_argument("--init-from"); ap.add_argument("--extra-data"); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--epochs", type=int)
a = ap.parse_args()
tree = pathlib.Path(a.tree).resolve()
here = pathlib.Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if not p or pathlib.Path(p).resolve() != here]
sys.path.insert(0, str(tree / "joint"))
sys.path.insert(1, str(tree / "src"))

import torch  # noqa: E402

torch.set_num_threads(1)
from f2 import devconfig  # noqa: E402
from f2.config import sha256  # noqa: E402
from f2.train import train  # noqa: E402

cfg = devconfig.config(a.preset)
cfg["data"]["mesh"] = "tiny"
if a.epochs is not None:
    cfg["arms"]["label_free"]["epochs"] = a.epochs
kw = {"device": "cpu"}
names = inspect.signature(train).parameters
if a.init_from:
    kw["init_from"] = a.init_from
if a.extra_data:
    kw["extra_dir"] = a.extra_data
assert all(k in names for k in kw), [k for k in kw if k not in names]
h = train(cfg, a.seed, a.data, a.out, **kw)
files = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((tree / "joint" / "f2").glob("*.py"))}
print(json.dumps({"preset": a.preset, "config_sha256": sha256(cfg), "status": h["status"], "steps": h.get("steps"),
                  "loss": h["loss"], "f2_files": files}))
