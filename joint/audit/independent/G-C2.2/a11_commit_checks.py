"""Audit of gate G-C2.2, item 6: the proposed commit as a whole.

For every path the commit adds or changes (the list of `git diff --name-status`), read from an export of the commit:
  - line ends: a carriage return in a text file;
  - a final line without a line end, trailing blanks and tabs (reported, not errors);
  - absolute paths of a machine (a path that starts at the root with home, root, tmp, mnt, Users and the like, or
    with a drive letter);
  - characters outside ASCII, with em and en dashes (and other dash characters) counted separately;
  - in the English documents and the scripts' comments: words in American spelling, from a list of patterns.
Binary files (.npz) are only counted. For the one modified file, pass the diff of its added lines with --added
(a file of the lines that the commit adds, one a line) so that only the new lines are checked for spelling and
dashes.

Usage:  python -I a11_commit_checks.py PROPOSED CHANGES.txt [--added README_ADDED.txt] [--out OUT.json]
"""
import argparse
import json
import os
import re

DASHES = {"\u2012": "figure dash", "\u2013": "en dash", "\u2014": "em dash", "\u2015": "horizontal bar", "\u2212": "minus sign"}
PATHS = re.compile(r"(?<![\w.])/(home|root|tmp|mnt|Users|var|opt|usr|sessions)/[\w.\-]+|[A-Za-z]:\\\\?[\w]")
AMERICAN = re.compile(
    r"\b(\w*(?:iz(?:e|es|ed|ing|ation|ations|er|ers))|color\w*|behavior\w*|center\w*|modeling|modeled|labeled|labeling|"
    r"canceled|canceling|traveled|analyz\w*|catalog\b|favor\w*|gray\b|fiber\w*|meters?\b|millimeters?\b|defense|license\b|"
    r"artifact\w*|judgment\w*|program\b|fulfill\w*|skeptic\w*|neighbor\w*|toward\b|afterward\b|while\b)", re.I)
ALLOWED = {"size", "sizes", "sized", "seize", "prize", "while", "program", "license", "toward", "artifact", "artifacts"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("proposed"); ap.add_argument("changes"); ap.add_argument("--added"); ap.add_argument("--out")
    a = ap.parse_args()
    rows = [l.rstrip("\n").split("\t") for l in open(a.changes, encoding="utf-8") if l.strip()]
    res = {"paths": len(rows), "status": {}, "binary": 0, "text": 0, "with_cr": [], "no_final_newline": [], "trailing_blanks": {}, "tabs": {},
           "absolute_paths": {}, "non_ascii": {}, "dashes": {}, "american": {}, "empty": [], "largest": []}
    sizes = []
    for st, p in rows:
        res["status"][st] = res["status"].get(st, 0) + 1
        full = os.path.join(a.proposed, p)
        b = open(full, "rb").read()
        sizes.append((len(b), p))
        if p.endswith(".npz"):
            res["binary"] += 1
            continue
        res["text"] += 1
        if not b:
            res["empty"].append(p); continue
        if b"\r" in b:
            res["with_cr"].append(p)
        if not b.endswith(b"\n"):
            res["no_final_newline"].append(p)
        t = b.decode("utf-8")
        n = sum(1 for l in t.split("\n") if l != l.rstrip(" \t"))
        if n:
            res["trailing_blanks"][p] = n
        if "\t" in t:
            res["tabs"][p] = t.count("\t")
        hits = sorted({m.group(0) for m in PATHS.finditer(t)})
        if hits:
            res["absolute_paths"][p] = hits[:6]
        na = sorted({c for c in t if ord(c) > 127})
        if na:
            res["non_ascii"][p] = {"characters": len(na), "code_points": [f"U+{ord(c):04X}" for c in na][:12]}
        d = {DASHES[c]: t.count(c) for c in DASHES if c in t}
        if d:
            res["dashes"][p] = d
        english = p.endswith(".md") or p.endswith(".py")
        if english and st == "A":
            words = sorted({m.group(0).lower() for m in AMERICAN.finditer(t)} - ALLOWED)
            if words:
                res["american"][p] = words
    if a.added:
        t = open(a.added, encoding="utf-8").read()
        res["added_lines_of_modified_file"] = {
            "lines": t.count("\n"), "dashes": {DASHES[c]: t.count(c) for c in DASHES if c in t},
            "non_ascii": sorted({f"U+{ord(c):04X}" for c in t if ord(c) > 127}),
            "american": sorted({m.group(0).lower() for m in AMERICAN.finditer(t)} - ALLOWED),
            "absolute_paths": sorted({m.group(0) for m in PATHS.finditer(t)})}
    res["largest"] = [[n, p] for n, p in sorted(sizes, reverse=True)[:4]]
    res["total_bytes"] = sum(n for n, _ in sizes)
    if a.out:
        open(a.out, "w").write(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
