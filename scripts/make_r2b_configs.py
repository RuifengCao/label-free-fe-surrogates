#!/usr/bin/env python3
"""R2b (PREREG_R2B Sec. 2): generate the two configurations of the
pre-registration -- never edited by hand.

From the Phase-2b configuration (configs/phase2b_v1.json; refused unless its
canonical SHA-256 is PREREG_PHASE2B's stamped CONFIG_SHA256), in the AR-only
form E2 took (PREREG_E2: E8 as AR pretraining only, P3 zero-shot only, the
FE-JEPA-only probes e6 and wp6 disabled; scripts/make_e_series_configs.py's
own edit, imported, not copied):
  r2b_b   the Phase-2b label-free (AR) transformer trained again on fresh
          seeds 3-5 (`e8.seed_offset = 3`): S's reference
  r2b_s   as r2b_b with S: decode_scale "l1" times S3_FACTOR (2^-10, the
          factor R2a used, scripts/make_fine3d_configs.py), and
          features.load_density
Both keep everything else of the Phase-2b configuration (corpus, split, the
1,024-instance training prefix, 200 epochs at 1e-3, dims, TF32, one worker)
and add only their own output directory, the guard on PREREG_R2B.md and a
comment. Each is therefore R2a's configuration of the same role
(configs/r2a_b_m1024.json, configs/r2a_s_m1024.json) without the
bottleneck's three model keys (kind, n_tokens, decode_k); a test checks it.

    python scripts/make_r2b_configs.py            # writes the two configs
    python scripts/make_r2b_configs.py --check    # the committed files are the generator's
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "configs/phase2b_v1.json"
BASE_SHA256 = "316f5e6e282db9c11509d8d1d2ed54d229ded9d6367c63b3a13abd7709ba4899"
"""PREREG_PHASE2B's stamped CONFIG_SHA256 (canonical: fejepa.report.config_sha256)."""
PREREG_FILE = "PREREG_R2B.md"
OUT_ROOT = "runs/r2b"
FRESH_SEED_OFFSET = 3
ARMS = {"r2b_b": {"s": False}, "r2b_s": {"s": True}}


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def s3_factor() -> float:
    """R2a's factor (scripts/make_fine3d_configs.py, S3_FACTOR): one constant
    for both experiments."""
    return float(_load("make_fine3d_configs", "scripts/make_fine3d_configs.py").S3_FACTOR)


def ar_only(experiments: dict) -> dict:
    """E2's AR-only form of the experiments block (make_e_series_configs)."""
    return _load("make_e_series_configs",
                 "scripts/make_e_series_configs.py")._disable_all_but_e8(experiments)


def r2b_config(base: dict, arm: str) -> dict:
    spec = ARMS[arm]
    cfg = json.loads(json.dumps(base))
    cfg["experiments"] = ar_only(cfg["experiments"])
    cfg["experiments"]["e8"]["seed_offset"] = FRESH_SEED_OFFSET
    factor = s3_factor()
    if spec["s"]:
        cfg["model"] = dict(cfg["model"], decode_scale="l1", decode_scale_factor=factor,
                            features=dict(cfg["model"]["features"], load_density=True))
    cfg["out"] = f"{OUT_ROOT}/{arm}/report.json"
    cfg["prereg_file"], cfg["prereg_guard"] = PREREG_FILE, True
    n = int(cfg["experiments"]["e8"]["seeds"])
    what = (f"the Phase-2b label-free transformer, AR on pool[:1024] x 200 epochs, seeds "
            f"{FRESH_SEED_OFFSET}-{FRESH_SEED_OFFSET + n - 1}"
            + (f", with S (decode_scale l1 x {factor!r}, load densities)" if spec["s"]
               else ", fresh baseline"))
    cfg["_comment"] = f"R2b arm {arm}: {what}; see {PREREG_FILE}"
    return cfg


def load_base(path: str = BASE) -> dict:
    sys.path.insert(0, str(ROOT / "src"))
    from fejepa.report import config_sha256

    base = json.loads((ROOT / path).read_text())
    got = config_sha256(base)
    if got != BASE_SHA256:
        raise SystemExit(f"{path}: config SHA-256 {got[:12]}... is not PREREG_PHASE2B's stamped "
                         f"configuration ({BASE_SHA256[:12]}...)")
    return base


def config_of(arm: str, base: dict | None = None) -> dict:
    return r2b_config(base if base is not None else load_base(), arm)


def render(cfg: dict) -> str:
    return json.dumps(cfg, indent=1) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(ROOT / "configs"))
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero unless the files in --out-dir are the generator's")
    a = ap.parse_args()
    base = load_base()
    out = Path(a.out_dir)
    bad = []
    for arm in ARMS:
        f = out / f"{arm}.json"
        text = render(config_of(arm, base))
        if a.check:
            if not f.is_file() or f.read_text() != text:
                bad.append(str(f))
            continue
        f.write_text(text)
        print(f"{f}  {hashlib.sha256(text.encode()).hexdigest()[:12]}")
    if bad:
        raise SystemExit(f"not the generator's output: {bad}")


if __name__ == "__main__":
    main()
