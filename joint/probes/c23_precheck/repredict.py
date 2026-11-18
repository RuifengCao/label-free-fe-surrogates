#!/usr/bin/env python3
"""Before gate G-C2.3 draws its sample: do predictions made today from G-C2.2's state files equal the prediction
files that G-C2.2's runs left on the same host?

The gate's identity check asks whether its label-free runs reproduce G-C2.2's judged values, but it can answer only
after the held-out sample has been drawn, labelled, predicted and evaluated. This probe asks the question before, on
G-C2.2's own data. For each seed: the state file is hashed and compared with the SHA-256 that the gate pins
(c23/config.py); G-C2.2's network is built and loaded; c22.train.predict writes the fields of G-C2.2's held-out and
tested members, in both readings, into a new folder; every array is compared with G-C2.2's file of the same name.
If the fields are equal to the last bit, the judged values can differ only through the reference solutions,
which the gate solves again; the host check (c23/smoke.py) covers that part on its reduced configuration.

    python -I probes/c23_precheck/repredict.py --repo REPO --data GATE_DATA --runs GATE_RUNS --out NEW
                                               [--seeds 5 6 7] [--device cuda] [--host-check-configuration]

GATE_DATA and GATE_RUNS are G-C2.2's data and runs folders; they are only read. NEW must not exist and must not lie
inside either of them: the new prediction files and the report, repredict.json, are written there. A state file
whose SHA-256 is not the pinned one is not read. Nothing of G-C2.3 is drawn: the configuration is G-C2.2's, whose
members were all seen before. --host-check-configuration takes the reduced configuration of c23/smoke.py in place of
G-C2.2's and skips the pinned hashes, for a dry run on the folders base_data and base_runs that the host check
leaves. The probe ends with 0 also when the fields differ: the report's all_identical says whether they do.
"""
import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = ("preds.npz", "preds_condensed.npz", "preds_base.npz")


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def numbers(obj):
    """Every number in a nested structure of dictionaries and lists, in a fixed order."""
    if isinstance(obj, dict):
        for k in sorted(obj):
            yield from numbers(obj[k])
    elif isinstance(obj, (list, tuple)):
        for x in obj:
            yield from numbers(x)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        yield float(obj)


def main(argv=None):
    here = Path(__file__).resolve().parent                      # the script's own folder must not shadow modules
    sys.path[:] = [p for p in sys.path if not p or Path(p).resolve() != here]
    sys.path.insert(0, str(ROOT))
    ap = argparse.ArgumentParser(prog="c23-repredict")
    for k in ("--repo", "--data", "--runs", "--out"):
        ap.add_argument(k, required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=[5, 6, 7])
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--host-check-configuration", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists():
        raise SystemExit(f"{out} exists; give a new folder (nothing is deleted)")
    for kept in (a.data, a.runs):                               # G-C2.2's folders hold its records: nothing new there
        if Path(kept).resolve() in [out.resolve(), *out.resolve().parents]:
            raise SystemExit(f"{out} lies inside {kept}; give a folder outside G-C2.2's data and runs")
    sys.path.insert(0, str(Path(a.repo) / "src"))
    import numpy as np
    import torch

    from c2.model import build
    from c2.train import MATMUL_PRECISION, verify_repository, _check_manifest, _load_state, _prepare
    from c22.config import config, sha256
    from c22.train import predict

    if a.host_check_configuration:
        from c23.smoke import reduced_base
        cfg, pinned = reduced_base(), None
    else:
        from c23.config import BASE_SHA256, LABEL_FREE_STATES
        cfg, pinned = config(), LABEL_FREE_STATES
        assert sha256(cfg) == BASE_SHA256
    man = _check_manifest(cfg, a.data)
    verify_repository(cfg)
    torch.set_float32_matmul_precision(MATMUL_PRECISION)
    dev = torch.device(a.device)
    cuda = dev.type == "cuda"
    first = [r["id"] for r in man["instances"] if r["split"] == "train"][0]
    it = _prepare(cfg, a.data, [first], dev, energy=False, labels=False)[0]
    rep = {"config_sha256": sha256(cfg), "seeds": {}, "all_identical": True,
           "host": {"platform": platform.platform(), "python": platform.python_version(), "numpy": np.__version__,
                    "torch": torch.__version__, "device": str(dev),
                    "gpu": torch.cuda.get_device_name(0) if cuda else None, "processors": os.cpu_count()}}
    for seed in a.seeds:
        old = Path(a.runs) / f"label_free_s{seed}"
        state_sha = file_sha256(old / "state.pt")
        r = {"state_sha256": state_sha, "state_is_the_pinned_one": None if pinned is None else
             state_sha == pinned[str(seed)], "files": {}}
        if r["state_is_the_pinned_one"] is False:               # as the gate's own command: such a file is not read
            r["identical"] = rep["all_identical"] = False
            rep["seeds"][str(seed)] = r
            print(f"seed {seed}: the state file has SHA-256 {state_sha}, not the pinned one; not read", flush=True)
            continue
        s = _load_state(old / "state.pt")
        h = s["history"]
        assert h.get("config_sha256") == sha256(cfg) and h.get("seed") == seed, "not this seed's run of the gate"
        nets = build(cfg, it["base"].shape[-1] + 1)
        for net, k in zip(nets, ("enc", "dec", "head")):
            net.load_state_dict(s[k])
            net.to(dev)
        new = out / f"label_free_s{seed}"
        new.mkdir(parents=True)
        t0 = time.perf_counter()
        r["finite"] = bool(predict(cfg, nets, a.data, new, dev))
        r["predict_seconds"] = round(time.perf_counter() - t0, 1)
        if not r["finite"]:
            r["identical"] = rep["all_identical"] = False
            rep["seeds"][str(seed)] = r
            print(f"seed {seed}: the predictions are not finite; nothing is compared", flush=True)
            continue
        for f in FILES:
            with np.load(new / f) as x, np.load(old / f) as y:
                same_keys = sorted(x.files) == sorted(y.files)
                diff = {k: float(np.max(np.abs(x[k].astype(np.float64) - y[k].astype(np.float64))))
                        for k in x.files if k in y.files and x[k].shape == y[k].shape}
                shapes = all(x[k].shape == y[k].shape for k in x.files if k in y.files)
                r["files"][f] = {"same_members": same_keys, "same_shapes": shapes, "members": len(x.files),
                                 "members_that_differ": sorted(k for k, v in diff.items() if v > 0.0),
                                 "largest_difference": max(diff.values()) if diff else None,
                                 "largest_value": float(max(np.max(np.abs(y[k])) for k in y.files)),
                                 "identical": bool(same_keys and shapes and all(
                                     np.array_equal(x[k], y[k]) for k in x.files))}
        cn, co = (json.loads((p / "condense.json").read_text()) for p in (new, old))
        xn, xo = list(numbers(cn)), list(numbers(co))
        r["files"]["condense.json"] = {
            "identical": cn == co,
            "largest_difference": (max((abs(p - q) for p, q in zip(xn, xo)), default=0.0)
                                   if len(xn) == len(xo) else None)}
        r["identical"] = all(v["identical"] for v in r["files"].values())
        rep["all_identical"] = rep["all_identical"] and r["identical"] and r["state_is_the_pinned_one"] is not False
        rep["seeds"][str(seed)] = r
        print(f"seed {seed}: identical {r['identical']}; "
              + "; ".join(f"{f} {v['largest_difference']}" for f, v in r["files"].items()), flush=True)
    (out / "repredict.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps({"all_identical": rep["all_identical"]}), flush=True)


if __name__ == "__main__":
    main()
