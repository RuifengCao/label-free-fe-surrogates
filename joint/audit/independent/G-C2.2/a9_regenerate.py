"""Audit of gate G-C2.2: the instances regenerated with the stamped library, against the returned manifest.

The instance files stayed on the laptop; the return package holds their SHA-256 in manifest.json. This script draws
every member again (c22.data.members), exports it (c2.data.export_member), packs it as the stamped code does
(c2.data._pack, numpy.savez_compressed) into memory, and compares the SHA-256 of the bytes with the manifest's.
The bytes depend on the zlib that numpy writes through and on the "creator system" field that zipfile records in
every entry (0 under Windows, 3 under Linux); run it with the zlib of the laptop's Python (zlib 1.3; on Linux,
LD_PRELOAD of the system's libz.so.1.3) and --creator 0. Sizes (nodes, unknowns) and family parameters are compared
as well, so that a difference in the bytes alone can be told from a different instance.

Usage:  LD_PRELOAD=<libz 1.3> python -I -B a9_regenerate.py STAMP RECORDS [--creator 0] [--splits eval,former,tested]
        [--limit N] [--out OUT.json]
"""
import argparse
import hashlib
import io
import json
import os
import sys
import zipfile
import zlib
from dataclasses import asdict

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stamp"); ap.add_argument("records")
    ap.add_argument("--creator", type=int, default=None); ap.add_argument("--splits", default="train,eval,former,tested")
    ap.add_argument("--limit", type=int, default=None); ap.add_argument("--out")
    a = ap.parse_args()
    if a.creator is not None:
        init = zipfile.ZipInfo.__init__

        def patched(self, *args, **kwargs):
            init(self, *args, **kwargs)
            self.create_system = a.creator

        zipfile.ZipInfo.__init__ = patched
    sys.path.insert(0, os.path.join(a.stamp, "joint"))
    from c22.config import config, sha256
    from c22 import data as d22
    from c2.data import export_member, _pack
    cfg = config()
    cfg_sha = sha256(cfg)
    man = json.load(open(os.path.join(a.records, "manifest.json")))
    box = {r["id"]: r for r in man["instances"]}
    splits = a.splits.split(",")
    res = {"zlib_runtime": zlib.ZLIB_RUNTIME_VERSION, "creator": a.creator, "config_sha256_equal_manifest": cfg_sha == man["config_sha256"],
           "by_split": {}, "sha256_differing": [], "sizes_differing": [], "params_differing": []}
    count = {}
    for iid, split, q in d22.members(cfg):
        if split not in splits:
            continue
        count[split] = count.get(split, 0) + 1
        if a.limit is not None and count[split] > a.limit:
            continue
        ex = export_member(cfg, q)
        buf = io.BytesIO()
        np.savez_compressed(buf, **_pack(ex, q, cfg_sha))
        h = hashlib.sha256(buf.getvalue()).hexdigest()
        c = res["by_split"].setdefault(split, {"files": 0, "sha256_equal": 0})
        c["files"] += 1
        c["sha256_equal"] += h == box[iid]["sha256"]
        if h != box[iid]["sha256"]:
            res["sha256_differing"].append(iid)
        if int(ex["nodes"].shape[0]) != box[iid]["nodes"] or int(np.asarray(ex["v"]).size) != box[iid]["unknowns"]:
            res["sizes_differing"].append(iid)
        if asdict(q) != box[iid]["params"]:
            res["params_differing"].append(iid)
    res["files"] = sum(c["files"] for c in res["by_split"].values())
    res["sha256_equal"] = sum(c["sha256_equal"] for c in res["by_split"].values())
    out = json.dumps(res, indent=1)
    if a.out:
        open(a.out, "w").write(out)
    print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in res.items()}))


if __name__ == "__main__":
    main()
