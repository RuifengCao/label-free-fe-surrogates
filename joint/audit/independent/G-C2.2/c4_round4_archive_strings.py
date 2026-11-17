"""Round 4, item 7: the five strings in the deposited archive, read as a stream of bytes.

Usage:  python -I -B c4_round4_archive_strings.py ARCHIVE DEPOSIT.json STRINGS.json B3_SCRIPT [--out OUT.json]

ARCHIVE       the deposited archive
DEPOSIT.json  its record (for the place of each file in the archive)
STRINGS.json  the owner's file of the five strings (not in the repository)
B3_SCRIPT     the path of b3_round3_strings.py, the auditor's own script of round 3, whose lists of
              forms and parts are used here

Every byte of the archive is searched for every form and every part that round 3 searched in the
files of the commit.  A match is then placed:

  - in the headers, the padding or the end of the archive;
  - in the structure of a file (the headers, names and directory of the .npz container);
  - in the compressed data of one array of a file; for these the array is uncompressed, its type is
    read and the same pattern is searched in its uncompressed bytes.

Short patterns (a single character outside ASCII, a short word) are expected to occur by chance in
compressed data of this size, so a match in compressed data of an array of numbers that has no
match in a name or in text says nothing.  The output gives counts by the key of the string, the
kind of the form and the place, and the paths of the files; never a string, a part or a length.
"""
import argparse
import importlib.util
import io
import json
import pathlib
import re
import struct
import zipfile
import zlib

BLOCK = 512


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive")
    ap.add_argument("deposit")
    ap.add_argument("strings")
    ap.add_argument("b3")
    ap.add_argument("--out")
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("b3_round3_strings", a.b3)
    b3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b3)
    strings = dict(b3.leaves(json.load(open(a.strings, encoding="utf-8"))))
    data = pathlib.Path(a.archive).read_bytes()
    rec = json.loads(pathlib.Path(a.deposit).read_text())
    spans, pos = [], 0
    for f in rec["files"]:
        spans.append((pos + BLOCK, pos + BLOCK + f["bytes"], f["path"]))
        pos += BLOCK + f["bytes"] + ((-f["bytes"]) % BLOCK)
    layout = {}

    def entries(path, member):
        if path not in layout:
            out = []
            with zipfile.ZipFile(io.BytesIO(member)) as zf:
                for zi in zf.infolist():
                    h = zi.header_offset
                    nlen, xlen = struct.unpack("<HH", member[h + 26:h + 30])
                    start = h + 30 + nlen + xlen
                    out.append((start, start + zi.compress_size, zi.compress_type))
            layout[path] = out
        return layout[path]

    def place(offset, rx, flags):
        for s, e, path in spans:
            if s <= offset < e:
                member, rel = data[s:e], offset - s
                for start, end, ctype in entries(path, member):
                    if start <= rel < end:
                        raw = zlib.decompress(member[start:end], -15) if ctype == 8 else member[start:end]
                        hl = struct.unpack("<H", raw[8:10])[0]
                        kind = re.search(r"'descr': '([^']*)'", raw[10:10 + hl].decode("latin-1")).group(1)
                        numbers = kind.lstrip("<>|=")[0] in "fiuc"
                        inside = len(re.findall(rx, raw, flags=flags))
                        return path, ("compressed data of an array of numbers" if numbers
                                      else "compressed data of an array that is not of numbers"), inside
                return path, "structure of the file (headers, names, directory)", None
        return None, "headers, padding or end of the archive", None

    res = {"bytes": len(data), "files": len(spans), "whole_strings": {}, "parts": {}}
    for key, s in strings.items():
        for name, pats in b3.forms(s).items():
            for p, c in pats:
                if len(p) < 4:
                    continue
                rx, flags = re.escape(p), (re.I if c else 0)
                for m in re.finditer(rx, data, flags=flags):
                    path, where, inside = place(m.start(), rx, flags)
                    d = res["whole_strings"].setdefault(key, {}).setdefault(name, {}).setdefault(where, {"matches": 0, "files": []})
                    d["matches"] += 1
                    if path and path not in d["files"]:
                        d["files"].append(path)
        for name, pats in b3.parts(s).items():
            for p, c, w in pats:
                rx = re.escape(p)
                if w:
                    rx = rb"(?<![A-Za-z0-9])" + rx + rb"(?![A-Za-z0-9])"
                flags = re.I if c else 0
                for m in re.finditer(rx, data, flags=flags):
                    path, where, inside = place(m.start(), rx, flags)
                    d = res["parts"].setdefault(key, {}).setdefault(name, {}).setdefault(
                        where, {"matches": 0, "files": [], "also_in_the_uncompressed_bytes": 0})
                    d["matches"] += 1
                    d["also_in_the_uncompressed_bytes"] += 1 if inside else 0
                    if path and path not in d["files"]:
                        d["files"].append(path)
    for group in ("whole_strings", "parts"):
        for key in res[group]:
            for name in res[group][key]:
                for where, d in res[group][key][name].items():
                    d["n_files"] = len(d["files"])
                    d["files"] = sorted(d["files"])[:4]
    print(json.dumps(res, indent=1))
    if a.out:
        pathlib.Path(a.out).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
