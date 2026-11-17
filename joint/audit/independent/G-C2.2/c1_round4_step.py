"""Round 4, item 1: the step from the commit with the array files to the commit without them.

Usage:  python c1_round4_step.py BEFORE AFTER DEPOSIT.json [--out OUT.json]

BEFORE and AFTER are two exports of the repository (folders).  The script walks both, compares
the sets of paths and the bytes of every common path, and says

  - which paths are gone, and whether they are exactly the paths of DEPOSIT.json under
    joint/records/c22/return/;
  - which paths are new and which are changed;
  - whether every file left in joint/records/c22/return/ has the bytes it had before.

It imports nothing of the author's and prints no content of a file.
"""
import argparse
import hashlib
import json
import pathlib
import sys

RET = "joint/records/c22/return/"


def walk(root):
    root = pathlib.Path(root)
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_symlink():
            out[p.relative_to(root).as_posix()] = ("link", None)
        elif p.is_file():
            out[p.relative_to(root).as_posix()] = ("file", hashlib.sha256(p.read_bytes()).hexdigest())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("deposit")
    ap.add_argument("--out")
    a = ap.parse_args()
    b, s = walk(a.before), walk(a.after)
    gone = sorted(set(b) - set(s))
    new = sorted(set(s) - set(b))
    changed = sorted(p for p in set(b) & set(s) if b[p] != s[p])
    links = sorted(p for p, v in list(b.items()) + list(s.items()) if v[0] == "link")
    dep = json.loads(pathlib.Path(a.deposit).read_text())
    listed = sorted(RET + f["path"] for f in dep["files"])
    left = sorted(p for p in s if p.startswith(RET))
    left_same = all(b.get(p) == s[p] for p in left)
    was = sorted(p for p in b if p.startswith(RET))
    res = {
        "paths_before": len(b), "paths_after": len(s),
        "gone": len(gone), "gone_are_the_listed_files": gone == listed,
        "gone_outside_return": [p for p in gone if not p.startswith(RET)],
        "new": new, "changed": changed, "symbolic_links": links,
        "return_before": len(was), "return_after": len(left),
        "return_left_identical": left_same,
        "return_after_plus_listed_is_return_before": sorted(left + listed) == was,
        "listed_hashes_equal_files_before": all(
            b.get(RET + f["path"], (None, None))[1] == f["sha256"] for f in dep["files"]),
    }
    print(json.dumps(res, indent=1))
    if a.out:
        pathlib.Path(a.out).write_text(json.dumps(res, indent=1) + "\n")
    ok = (res["gone_are_the_listed_files"] and left_same and not links
          and res["return_after_plus_listed_is_return_before"])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
