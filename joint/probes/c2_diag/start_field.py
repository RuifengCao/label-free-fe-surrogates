"""The loss of the starting field on the draws of chosen epochs of a host run (exploratory, after the G-C2.1 verdict).

    python -I start_field.py JOINT_DIR DATA_DIR OUT.json SEED EPOCHS

EPOCHS is a comma-separated list of epoch numbers (1 to 200). The networks are built as c2.train.train builds them;
the last layers of the decoder and the head start at zero, so the predicted field is the starting field whatever the
other weights are, and it is checked here that their outputs are exactly zero. The numpy generator is advanced
through the run's draws (a permutation of the 512 training members each epoch, four D a step, by c2.train.sample_D
inside c2.train.step_loss), and on the chosen epochs each step's loss is computed by c2.train.step_loss without
gradients. The mean over an epoch is then the epoch mean that a run whose field stayed at the start would have
logged, on the same members and the same D as the host's run.
"""
import json
import os
import sys
import time
from pathlib import Path

joint, data_dir, out_path, seed = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4])
want = sorted(int(x) for x in sys.argv[5].split(","))
sys.path.insert(0, joint)
sys.path.insert(0, str(Path(joint).parent / "src"))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from c2.config import config  # noqa: E402
from c2.data import manifest  # noqa: E402
from c2.model import build, field  # noqa: E402
from c2.train import _prepare, step_loss, sample_D, MATMUL_PRECISION  # noqa: E402

torch.set_num_threads(int(os.environ.get("DIAG_THREADS", "1")))
cfg = config()
tr = cfg["training"]
man = manifest(data_dir)
train_ids = [r["id"] for r in man["instances"] if r["split"] == "train"]
torch.set_float32_matmul_precision(MATMUL_PRECISION)
torch.manual_seed(seed)
rng = np.random.default_rng(seed)
dev = torch.device("cpu")
cache = {}


def item(i):
    if i not in cache:
        if len(cache) >= 16:                     # each member is visited once an epoch: keep the memory small
            del cache[next(k for k in cache if k != 0)]
        cache[i] = _prepare(cfg, data_dir, [train_ids[i]], dev, energy=True, labels=False)[0]
    return cache[i]


nets = build(cfg, item(0)["base"].shape[-1] + 1)
enc, dec, head = nets
for net in nets:
    net.eval()
for name, layer in (("decoder", dec[-1]), ("head", head[-1])):
    assert float(layer.weight.detach().abs().max()) == 0.0 and float(layer.bias.detach().abs().max()) == 0.0, name
res = {"seed": seed, "torch": torch.__version__, "epochs": {}}
t0 = time.time()
with torch.no_grad():
    for epoch in range(1, max(want) + 1):
        order = rng.permutation(len(train_ids))
        if epoch not in want:
            for _ in order:
                sample_D(rng, cfg, tr["fields_per_step"])
            continue
        losses = []
        for i in order:
            loss, D = step_loss(cfg, nets, item(int(i)), rng, False, dev)
            losses.append(float(loss))
            if len(losses) % 64 == 0:
                print(f"  epoch {epoch}: {len(losses)} steps, running mean {np.mean(losses):.4f} ({time.time() - t0:.0f} s)",
                      flush=True)
        res["epochs"][epoch] = {"mean": float(np.mean(losses)), "steps": len(losses)}
        print(f"epoch {epoch}: starting-field mean loss {np.mean(losses):.6f} ({time.time() - t0:.0f} s)", flush=True)
        out_path.write_text(json.dumps(res, indent=1))
