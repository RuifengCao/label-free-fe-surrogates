"""Regenerate instances of G-C2.1 with the stamped code (c2.data.members, export_member, _pack), written exactly as
c2.data.generate writes them (np.savez_compressed to an open file), and compare their SHA-256, node and unknown counts
with the returned manifest. Usage (from a joint/ folder holding the stamped c2/ and fejoint/):
    python -I -B regen.py JOINT RECORDS OUT_DIR ids|eval,tested|train:N  REPORT_JSON
Auditor's script; does not import the author's audit scripts."""
import hashlib
import json
import sys
import time
import zlib
from pathlib import Path

JOINT, REC, OUT, SEL, REPORT = sys.argv[1:6]
sys.path.insert(0, JOINT)
import numpy as np  # noqa: E402
from c2.config import config, sha256  # noqa: E402
from c2 import data as C2D  # noqa: E402

cfg = config()
cfg_sha = sha256(cfg)
man = json.loads((Path(REC) / "manifest.json").read_text())
box = {r["id"]: r for r in man["instances"]}
mem = C2D.members(cfg)
same = len(mem) == man["n"] == len(man["instances"]) and all(
    box[i]["params"] == C2D.asdict(q) and box[i]["split"] == s for i, s, q in mem)
want = set()
for part in SEL.split(","):
    if part.startswith("train:"):
        want |= {i for i, s, _ in mem if s == "train"} & {f"train_{k:04d}" for k in range(int(part[6:]))}
    elif part in ("eval", "tested", "train"):
        want |= {i for i, s, _ in mem if s == part}
    else:
        want.add(part)
out = Path(OUT)
out.mkdir(parents=True, exist_ok=True)
rows = []
t0 = time.perf_counter()
for iid, split, q in mem:
    if iid not in want:
        continue
    p = out / f"{iid}.npz"
    with open(p, "wb") as fh:
        np.savez_compressed(fh, **C2D._pack(C2D.export_member(cfg, q), q, cfg_sha))
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    with np.load(p) as z:
        nodes, nz = int(z["nodes"].shape[0]), int(z["v"].size)
    rows.append({"id": iid, "sha256_equal": h == box[iid]["sha256"], "sizes_equal":
                 nodes == box[iid]["nodes"] and nz == box[iid]["unknowns"]})
rep = {"zlib_runtime": zlib.ZLIB_RUNTIME_VERSION, "numpy": np.__version__, "python": sys.version.split()[0],
       "config_sha256": cfg_sha, "config_equals_manifest": cfg_sha == man["config_sha256"],
       "members_are_configured_draws": same,
       "train_eval_param_overlap": len({json.dumps(C2D.asdict(q), sort_keys=True) for i, s, q in mem if s == "train"}
                                       & {json.dumps(C2D.asdict(q), sort_keys=True) for i, s, q in mem if s == "eval"}),
       "files": len(rows), "sha256_equal": sum(r["sha256_equal"] for r in rows),
       "sizes_equal": sum(r["sizes_equal"] for r in rows),
       "differ": [r["id"] for r in rows if not r["sha256_equal"]], "seconds": round(time.perf_counter() - t0, 1)}
Path(REPORT).write_text(json.dumps(rep, indent=1))
print(json.dumps(rep))
