"""python -m f1 COMMAND (run from joint/)

  hash [--dry]                                 the configuration's SHA-256
  readings [--dry]                             the test readings and their tolerances
  cases [--dry]                                the case ids, in run order
  run --sha SHA --out DIR [--case ID] [--dry]  run one case, or every case in order (existing records are kept)
  verdict --sha SHA --out DIR [--dry]          evaluate once every case has its record (refuses before that);
                                               write DIR/verdict.json and DIR/numbers.md

Without --dry (the gate: B-13 and T-13), run and verdict refuse to start unless SHA is the configuration's hash and
every file listed in docs/G-F1_code.sha256 has its listed SHA-256. --dry runs the same code on B-19 and T-19, which
were solved during development and are not part of the gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from .config import config, config_hash
from .readings import read_tests
from .run import cases, case_id, run_case
from .verdict import evaluate, numbers_markdown

ROOT = Path(__file__).resolve().parent.parent
CODE_LIST = ROOT / "docs" / "G-F1_code.sha256"


def check_code() -> list:
    """Files whose SHA-256 differs from docs/G-F1_code.sha256 (empty when all match)."""
    bad = []
    for line in CODE_LIST.read_text().splitlines():
        if not line.strip():
            continue
        h, rel = line.split(None, 1)
        p = ROOT / rel.strip()
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != h:
            bad.append(rel.strip())
    return bad


def _guard(args):
    if args.dry:
        return
    if args.sha != config_hash():
        sys.exit(f"refusing to run: the configuration's SHA-256 is {config_hash()}, not {args.sha}")
    if not CODE_LIST.exists():
        sys.exit(f"refusing to run: {CODE_LIST} is missing")
    bad = check_code()
    if bad:
        sys.exit("refusing to run: files differ from docs/G-F1_code.sha256: " + ", ".join(bad))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m f1", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["hash", "readings", "cases", "run", "verdict"])
    ap.add_argument("--sha", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--case", default="")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args(argv)
    cfg = config(args.dry)
    if args.command == "hash":
        print(config_hash(args.dry)); return
    if args.command == "readings":
        print(json.dumps(read_tests(cfg), indent=1)); return
    if args.command == "cases":
        print("\n".join(case_id(c) for c in cases(cfg))); return
    if not args.out:
        sys.exit("--out is required")
    _guard(args)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / "config.json").write_text(json.dumps(cfg, indent=1, sort_keys=True))
    if args.command == "run":
        todo = [c for c in cases(cfg) if not args.case or case_id(c) == args.case]
        if not todo:
            sys.exit(f"no case {args.case!r}")
        for c in todo:
            run_case(cfg, c, out)
        return
    missing = [case_id(c) for c in cases(cfg) if not (out / "records" / f"{case_id(c)}.json").exists()]
    if missing:
        sys.exit(f"refusing to evaluate: {len(missing)} of {len(cases(cfg))} case records are missing "
                 f"({', '.join(missing)}); finish the run first")
    res = evaluate(cfg, read_tests(cfg), out)
    res["config_sha256"] = config_hash(args.dry)
    (out / "verdict.json").write_text(json.dumps(res, indent=1))
    (out / "numbers.md").write_text(numbers_markdown(res))
    print(res["verdict"])


if __name__ == "__main__":
    main()
