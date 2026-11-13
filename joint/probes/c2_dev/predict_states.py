"""R0-a: fields of the host's final models (G-C2.1, label-free seeds) on chosen members at the seven evaluation levels,
on CPU. First check: the held-out fields must reproduce the returned preds.npz."""
import sys, json
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
sys.path.insert(0, str(paths.joint())); sys.path.insert(0, str(paths.src()))
import numpy as np, torch
from pathlib import Path
from c2.config import config
from c2.data import manifest
from c2.model import build, field
from c2.train import _prepare, MATMUL_PRECISION
torch.set_num_threads(1); torch.set_float32_matmul_precision(MATMUL_PRECISION)
cfg = config(); DATA = str(paths.data()); dev = torch.device("cpu")
seed = int(sys.argv[1]); mode = sys.argv[2]
torch.serialization.add_safe_globals([torch.torch_version.TorchVersion])          # the history holds torch.__version__
st = torch.load(paths.states() / f"label_free_s{seed}/state.pt", map_location="cpu", weights_only=True)
print("state keys", sorted(st.keys()), "epoch", st["epoch"], "step", st["step"], "status", st["history"].get("status"))
man = manifest(DATA)
sel = json.load(open(paths.work() / "selection.json"))
ids = [r["id"] for r in man["instances"] if r["split"] == "eval"] if mode == "eval" else sel["order"]
lv = torch.as_tensor(cfg["data"]["eval_levels_mm"], dtype=torch.float32)
nets = None; preds = {}
with torch.no_grad():
    for k, iid in enumerate(ids):
        it = _prepare(cfg, DATA, [iid], dev, energy=False, labels=False)[0]
        if nets is None:
            torch.manual_seed(0)
            nets = build(cfg, it["base"].shape[-1] + 1)
            for net, key in zip(nets, ("enc", "dec", "head")):
                net.load_state_dict(st[key]); net.eval()
        preds[iid] = field(*nets, it["base"], it["maps"], lv, cfg["map"]["T"], lift=cfg["model"]["lift"] == "web").float().numpy()
        if k % 8 == 0: print(k, iid, flush=True)
np.savez_compressed(paths.work() / f"out/preds_s{seed}_{mode}.npz", **preds)
if mode == "eval":
    ret = np.load(paths.ret() / f"runs/label_free_s{seed}/preds.npz")
    worst = 0.0; worst_e = 0.0
    for iid in ids:
        a, b = preds[iid].astype(np.float64), ret[iid].astype(np.float64)
        worst = max(worst, float(np.abs(a - b).max() / np.abs(b).max()))
        worst_e = max(worst_e, float(np.abs(a[:, -1] / b[:, -1] - 1).max()))
    print(f"seed {seed}: held-out fields against the returned ones: largest difference over the field's largest entry {worst:.2e}; largest relative difference of e {worst_e:.2e}")
