#!/usr/bin/env python3
"""R2b: stamp PREREG_R2B.md (its Sec. 7) in one step, refusing anything but
the approved draft (scripts/stamp_prereg_fine3d.py's procedure, for R2b's two
configurations):

  1. the two configurations are the generator's (scripts/make_r2b_configs.py);
  2. the file is the approved draft, byte for byte (DRAFT_SHA256): both
     CONFIG_SHA256 lines open, the footer open, the status line the draft's;
  3'. `src` is the tree the cross-branch regression ran (records/wp9/README.md,
     "this side"; PREREG_R2B Sec. 8), so that the stamped code is the code
     the regression speaks for;
  3. each CONFIG_SHA256 line is filled with its configuration's canonical
     SHA-256 (fejepa.report.stamp_prereg, as `fejepa prereg --stamp` does);
  4. the status line records the stamp date;
  5. the footer records the file's SHA-256, computed over the file with the
     footer reading `PREREG_R2B_SHA256 = <record after commit>`;
  6. the result is read back and checked: every line is its configuration's
     hash and the footer verifies.

Then: commit; run the full suite on that commit (the box will); tag it
`prereg-r2b` (annotated: `git tag -a prereg-r2b -m ...`); push the branch and
the tag (RUNBOOK_R2B Sec. 0 fetches both).

    python scripts/stamp_prereg_r2b.py --date "4 November 2026"
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

PREREG = "PREREG_R2B.md"
DRAFT_STATUS = ("**Status:** r1 DRAFT (3 November 2026), not stamped; the two CONFIG_SHA256 "
                "lines below are open. Stamping fills them both at once, before any run "
                "(Sec. 7); post-stamp criterion changes are prohibited.")
FOOTER_OPEN = "PREREG_R2B_SHA256 = <record after commit>"
DRAFT_SHA256 = "53923fe9c32597e7c84c03a1c630c797c279f3c0ce9eb70286bb70ca95d277ed"
"""SHA-256 of the approved draft (PREREG_R2B.md as committed before the stamp);
a test keeps it equal to the committed draft, or to the draft the stamped file
came from."""
README_TREE = re.compile(r"\| this side \| [^|]*`src` = tree `([0-9a-f]{40})` \|")
_FOOTER = re.compile(r"^PREREG_R2B_SHA256 = (.+)$", re.M)
_DATE = re.compile(r"^[1-9]\d? (January|February|March|April|May|June|July|August|September|"
                   r"October|November|December) 20\d\d$")


def stamped_status(date: str) -> str:
    return (f"**Status:** r1, stamped {date} before any run: the two CONFIG_SHA256 lines "
            "below are filled, and the last line is this file's SHA-256 (Sec. 7); "
            "post-stamp criterion changes are prohibited.")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def src_tree_ok() -> tuple:
    """(ok, this tree, the README's) -- `src` against the regression's record."""
    here = _load("regress_against_branch").src_tree(ROOT / "src")
    m = README_TREE.search((ROOT / "records" / "wp9" / "README.md").read_text())
    want = m.group(1) if m else None
    return here == want, here, want


def self_hash_ok(text: str) -> bool:
    m = _FOOTER.findall(text)
    if len(m) != 1 or not re.fullmatch(r"[0-9a-f]{64}", m[0]):
        return False
    blank = _FOOTER.sub(FOOTER_OPEN, text, count=1)
    return hashlib.sha256(blank.encode("utf-8")).hexdigest() == m[0]


def stamp(prereg: Path, configs: Path, date: str, check_generator: bool = True) -> dict:
    from fejepa.report import (PREREG_PLACEHOLDER, config_sha256, read_prereg_entries,
                               stamp_prereg)

    if not _DATE.match(date):
        raise SystemExit(f"--date {date!r}: write it as e.g. '4 November 2026'")
    mk = _load("make_r2b_configs")
    arms = list(mk.ARMS)
    cfgs = {}
    for arm in arms:
        f = configs / f"{arm}.json"
        cfgs[arm] = json.loads(f.read_text())
        if check_generator and f.read_text() != mk.render(mk.config_of(arm)):
            raise SystemExit(f"{f}: not the generator's output (scripts/make_r2b_configs.py)")
    text = prereg.read_text(encoding="utf-8")
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != DRAFT_SHA256:
        raise SystemExit(f"{prereg}: not the approved draft (SHA-256 "
                         f"{hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]}..., approved "
                         f"{str(DRAFT_SHA256)[:12]}...)")
    if check_generator:
        ok, here, want = src_tree_ok()
        if not ok:
            raise SystemExit(f"src is tree {here[:12]}..., not the tree the regression ran "
                             f"({str(want)[:12]}..., records/wp9/README.md): run "
                             "scripts/regress_against_branch.py again first")
    entries = read_prereg_entries(prereg)
    if [lab for lab, _ in entries] != arms:
        raise SystemExit(f"{prereg}: the CONFIG_SHA256 lines are {[lab for lab, _ in entries]}, "
                         f"not {arms}")
    if any(v != PREREG_PLACEHOLDER for _, v in entries):
        raise SystemExit(f"{prereg}: already (partly) stamped -- nothing changed")
    if text.count(DRAFT_STATUS) != 1:
        raise SystemExit(f"{prereg}: the status line is not the approved draft's")
    if len(_FOOTER.findall(text)) != 1 or not text.rstrip("\n").endswith(FOOTER_OPEN):
        raise SystemExit(f"{prereg}: the last line is not `{FOOTER_OPEN}`")
    hashes = {arm: stamp_prereg(prereg, cfgs[arm], label=arm) for arm in arms}
    text = prereg.read_text(encoding="utf-8").replace(DRAFT_STATUS, stamped_status(date))
    own = hashlib.sha256(text.encode("utf-8")).hexdigest()
    text = _FOOTER.sub(f"PREREG_R2B_SHA256 = {own}", text, count=1)
    prereg.write_text(text, encoding="utf-8")
    back = dict(read_prereg_entries(prereg))
    if any(back[a] != config_sha256(cfgs[a]) for a in arms) or not \
            self_hash_ok(prereg.read_text(encoding="utf-8")):
        raise SystemExit(f"{prereg}: the stamped file does not verify")
    return {"config_sha256": hashes, "prereg_sha256": own, "date": date}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="the stamp date, e.g. '4 November 2026'")
    ap.add_argument("--prereg", default=str(ROOT / PREREG))
    ap.add_argument("--configs", default=str(ROOT / "configs"))
    a = ap.parse_args()
    res = stamp(Path(a.prereg), Path(a.configs), a.date)
    print(json.dumps(res, indent=1))
    print("next: commit; run the full suite on that commit; tag it (annotated) "
          "prereg-r2b; push the branch and the tag")


if __name__ == "__main__":
    main()
