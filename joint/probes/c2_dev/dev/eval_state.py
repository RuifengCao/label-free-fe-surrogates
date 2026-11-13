"""Read and judge a saved model on the 64 former held-out members of G-C2.1, raw and amplitude-condensed
(exploratory development code; not under any stamp).

    python -I dev/eval_state.py --name NAME --state PATH [--fields] [--part I/N]

The state file holds the three networks under the keys enc, dec, head (the gate's state.pt, a development run's
final_state.pt or state.pt). Writes runs/eval/NAME.json (per member and level: end displacements, energies,
amplitudes; the judged rows and summaries) and, with --fields, runs/eval/NAME_fields.npz."""
import argparse
import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True)
ap.add_argument("--state", required=True)
ap.add_argument("--device", default="cuda")
ap.add_argument("--fields", action="store_true")
ap.add_argument("--part", default=None, help="I/N: only every N-th member starting at I (tests)")
ap.add_argument("--read-evals", type=int, default=12)
ap.add_argument("--amin", type=float, default=0.5)
ap.add_argument("--amax", type=float, default=3.0)
ap.add_argument("--data", default=str(BASE / "data"))
ap.add_argument("--ref", default=str(BASE / "eval_ref.json"))
ap.add_argument("--out", default=str(BASE / "runs" / "eval"))
args = ap.parse_args()
sys.path.insert(0, str(BASE / "code" / "joint"))
sys.path.insert(0, str(BASE / "code" / "repo" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import torch  # noqa: E402

from c2.config import config  # noqa: E402
from c2.model import build  # noqa: E402
from c2.train import _prepare, MATMUL_PRECISION  # noqa: E402
from evalcond import evaluate_model, judge, report  # noqa: E402

torch.set_float32_matmul_precision(MATMUL_PRECISION)
cfg = config()
dev = torch.device(args.device)
ref = json.loads(Path(args.ref).read_text())
ids = list(ref["members"])
if args.part:
    i, n = (int(v) for v in args.part.split("/"))
    ids = ids[i::n]
state = Path(args.state) if Path(args.state).is_absolute() else BASE / args.state
torch.serialization.add_safe_globals([torch.torch_version.TorchVersion])
try:
    st = torch.load(state, map_location="cpu", weights_only=True)
except Exception:                                   # a development checkpoint also holds numpy and Python objects
    st = torch.load(state, map_location="cpu", weights_only=False)
probe = _prepare(cfg, args.data, ids[:1], dev, energy=False, labels=False)[0]
torch.manual_seed(0)
nets = build(cfg, probe["base"].shape[-1] + 1)
for net, k in zip(nets, ("enc", "dec", "head")):
    net.load_state_dict(st[k])
    net.to(dev)
out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
t0 = time.time()
res = evaluate_model(cfg, nets, args.data, ref, dev, args.read_evals, args.amin, args.amax, ids,
                     out / f"{args.name}_fields.npz" if args.fields else None)
jd = judge(res, ref)
tmp = out / f"{args.name}.json.tmp"
tmp.write_text(json.dumps({"name": args.name, "state": str(state), "members": len(ids), "seconds": round(time.time() - t0, 1),
                           "device": str(dev), "torch": torch.__version__, "read_evals": args.read_evals,
                           "amin": args.amin, "amax": args.amax, "readings": res, **jd}))
tmp.replace(out / f"{args.name}.json")
print(report(args.name, jd), flush=True)
print(f"{args.name}: {len(ids)} members in {time.time() - t0:.0f} s", flush=True)
