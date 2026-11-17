"""Audit of gate G-C2.2, round 3: are the strings that the keep script removes still anywhere in the commit?

The strings are read from the owner's file of strings, which is not in the repository (a JSON object whose values
are the strings). For every path that the commit adds or changes (the list of `git diff --name-status`), read from
an export of the commit, the script counts the occurrences of each string
  - in plain text (for strings in ASCII without regard to case), also in UTF-16 and UTF-32;
  - in encoded forms: hexadecimal (either case, bare, with spaces, colons or commas, and as \\x escapes), base64 in
    both alphabets at the three alignments, \\u escapes, octal escapes of the UTF-8 bytes, percent-encoding, numeric
    character references, lists of decimal byte values, the string reversed and in rot13;
  - by its parts: a file name without its extension; every character outside ASCII of a string singly, in plain
    and in \\u, octal, \\x and percent form; for strings of several words the last word (with its plural and its
    -ing form) as a whole word; for a name that ends in digits, the name without them, as a whole word.
In the binary files (.npz) the names of the stored arrays and the arrays that hold text or single bytes are read
and searched in the same way; arrays of numbers are not.
The output gives counts by the key of each string in the file, never a string or a part of one.

Usage:  python -I b3_round3_strings.py PROPOSED CHANGES.txt STRINGS.json [--out OUT.json]
"""
import argparse
import base64
import codecs
import json
import os
import re
import zipfile


def leaves(o, key=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from leaves(v, f"{key}.{k}" if key else str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from leaves(v, f"{key}[{i}]")
    elif isinstance(o, str):
        yield key, o


def forms(s):
    """name of the form -> list of byte patterns (searched without regard to case where the flag is set)."""
    raw = s.encode("utf-8")
    out = {"plain": [(raw, s.isascii())]}
    out["utf-16 or utf-32"] = [(s.encode(e), False) for e in ("utf-16-le", "utf-16-be", "utf-32-le", "utf-32-be")]
    hx = raw.hex()
    pairs = [hx[i:i + 2] for i in range(0, len(hx), 2)]
    out["hexadecimal"] = [(hx.encode(), True)] + [(sep.join(pairs).encode(), True) for sep in (" ", ":", ",", ", ", "\\x", "0x", ", 0x")]
    b64 = []
    for alphabet in (base64.b64encode, base64.urlsafe_b64encode):
        for shift in range(3):
            enc = alphabet(b"\x00" * shift + raw)
            core = enc[(4 if shift else 0):len(enc) - 4]
            if len(core) >= 6:
                b64.append((core, False))
    out["base64"] = b64
    u4 = "".join("\\u%04x" % ord(c) if ord(c) < 0x10000 else "\\U%08x" % ord(c) for c in s)
    out["\\u escapes"] = [(u4.encode(), True)]
    out["octal escapes"] = [("".join("\\%03o" % b for b in raw).encode(), False), ("".join("\\%o" % b for b in raw).encode(), False)]
    out["percent-encoding"] = [("".join("%%%02x" % b for b in raw).encode(), True)]
    out["character references"] = [("".join("&#%d;" % ord(c) for c in s).encode(), False), ("".join("&#x%x;" % ord(c) for c in s).encode(), True)]
    out["decimal bytes"] = [(sep.join(str(b) for b in raw).encode(), False) for sep in (",", ", ", " ")]
    out["reversed"] = [(s[::-1].encode("utf-8"), s.isascii())]
    if s.isascii():
        out["rot13"] = [(codecs.encode(s, "rot13").encode(), True)]
    return out


def parts(s):
    """Parts of a string that would give it away: name of the part -> list of (pattern, ignore case, whole word)."""
    out = {}
    stem = s.rsplit(".", 1)[0] if re.search(r"\.[A-Za-z0-9]{1,4}$", s) else None
    if stem and len(stem) >= 4:
        out["name without extension"] = [(p, c, False) for name, ps in forms(stem).items() for p, c in ps
                                         if name in ("plain", "hexadecimal", "\\u escapes", "octal escapes", "percent-encoding")]
    singles = []
    for ch in sorted({c for c in s if ord(c) > 127}):
        b = ch.encode("utf-8")
        singles += [(b, False, False), (("\\u%04x" % ord(ch)).encode(), True, False), ("".join("\\%03o" % x for x in b).encode(), False, False),
                    ("".join("\\x%02x" % x for x in b).encode(), True, False), ("".join("%%%02x" % x for x in b).encode(), True, False)]
    if singles:
        out["single characters outside ASCII"] = singles
    words = s.split()
    if s.isascii() and len(words) > 1 and len(words[-1]) >= 4:
        w = words[-1]
        variants = {w, w + "s", (w[:-1] if w.endswith("e") else w) + "ing"}
        out["last word"] = [(v.encode(), True, True) for v in sorted(variants)]
    m = re.fullmatch(r"([A-Za-z]{4,})\d+", s)
    if m:
        out["name without its digits"] = [(m.group(1).encode(), True, True)]
    return out


def npz_text(path):
    """The bytes of an .npz file that can hold text: the names of its arrays, and its arrays of strings or bytes."""
    import numpy as np
    parts, arrays, read = [], 0, 0
    with zipfile.ZipFile(path) as zf:
        parts += [n.encode("utf-8") for n in zf.namelist()]
    with np.load(path, allow_pickle=False) as z:
        for k in z.files:
            arrays += 1
            a = z[k]
            if a.dtype.kind in "SU" or (a.dtype.kind in "ui" and a.dtype.itemsize == 1):
                read += 1
                parts.append(a.tobytes())
    return b"\n".join(parts), arrays, read


def count(data, pat, nocase, word=False):
    rx = re.escape(pat)
    if word:
        rx = rb"(?<![A-Za-z0-9])" + rx + rb"(?![A-Za-z0-9])"
    return len(re.findall(rx, data, flags=re.I if nocase else 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("proposed"); ap.add_argument("changes"); ap.add_argument("strings"); ap.add_argument("--out")
    a = ap.parse_args()
    strings = dict(leaves(json.load(open(a.strings, encoding="utf-8"))))
    rows = [l.rstrip("\n").split("\t") for l in open(a.changes, encoding="utf-8") if l.strip()]
    res = {"strings": {k: {"characters": len(v), "ascii": v.isascii()} for k, v in strings.items()}, "paths": len(rows),
           "text_files_searched": 0, "binary_files_searched": 0, "arrays_in_binary_files": 0, "arrays_read": 0, "hits": {}, "part_hits": {}}
    for st, rel in rows:
        full = os.path.join(a.proposed, rel)
        if rel.endswith(".npz"):
            data, arrays, read = npz_text(full)
            res["binary_files_searched"] += 1; res["arrays_in_binary_files"] += arrays; res["arrays_read"] += read
        else:
            data = open(full, "rb").read()
            res["text_files_searched"] += 1
        for key, s in strings.items():
            for name, pats in forms(s).items():
                n = sum(count(data, p, c) for p, c in pats if len(p) >= 4)
                if n:
                    res["hits"].setdefault(key, {}).setdefault(name, {})[rel] = n
            for name, pats in parts(s).items():
                n = sum(count(data, p, c, w) for p, c, w in pats)
                if n:
                    res["part_hits"].setdefault(key, {}).setdefault(name, {})[rel] = n
    res["forms_searched_for_each_string"] = sorted(forms("ab cd").keys())
    if a.out:
        open(a.out, "w").write(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
