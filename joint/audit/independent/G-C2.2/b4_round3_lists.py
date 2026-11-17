"""Audit of gate G-C2.2, round 3: the three lists of the return package with the two placeholders.

In the corrected commit the names of the two launchers that are left out are replaced by placeholders in
return_files.sha256, return_listing.txt and keep_report.json. This script checks, with the owner's file of strings
(not in the repository; its entries launcher_pause and launcher_continuation are the two file names):
  - return_files.sha256: one line for every file of the received package and no other; every hash equal to the
    file's; the two placeholder lines carry the hashes of the two launchers, each under the right placeholder; how
    many lines name a file that exists under its listed name (the lines that `sha256sum -c` can check);
  - return_listing.txt: equal to the listing of the archive given (as `tar --numeric-owner -tvzf` prints it at
    UTC) except in the two lines of the launchers, which differ from it in the name alone;
  - keep_report.json: its list of the files left out names the same seven files with the same hashes and sizes,
    the two launchers under their placeholders; its counts against the kept copy;
  - that none of the three lists holds a character outside ASCII or an escape sequence.
The output gives counts and truth values only.

Usage:  python -I b4_round3_lists.py RECEIVED_UNPACKED PROPOSED LISTING STRINGS.json [--out OUT.json]
        RECEIVED_UNPACKED holds gate_records after unpacking; LISTING is the archive's listing with numeric owners.
"""
import argparse
import hashlib
import json
import os
import re

PLACE = {"launcher_pause": "queue/<launcher of the pause>.bat", "launcher_continuation": "queue/<launcher of the continuation>.bat"}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("received"); ap.add_argument("proposed"); ap.add_argument("listing"); ap.add_argument("strings"); ap.add_argument("--out")
    a = ap.parse_args()
    st = json.load(open(a.strings, encoding="utf-8"))
    rec = os.path.join(a.received, "gate_records")
    rc = os.path.join(a.proposed, "joint", "records", "c22")
    files = {}
    for d, _, fs in os.walk(rec):
        for f in fs:
            p = os.path.join(d, f)
            files[os.path.relpath(p, rec).replace(os.sep, "/")] = p
    real = {PLACE[k]: "queue/" + st[k] for k in PLACE}                 # placeholder -> name in the package
    res = {}
    lines = [l.split("  ", 1) for l in open(os.path.join(rc, "return_files.sha256"), encoding="utf-8").read().splitlines()]
    listed = {name: h for h, name in lines}
    names = {real.get(n, n) for n in listed}
    res["return_files.sha256"] = {
        "lines": len(lines), "received_files": len(files), "one_line_for_every_file_and_no_other": names == set(files) and len(listed) == len(lines),
        "hashes_equal": sum(sha(files[real.get(n, n)]) == h for n, h in listed.items() if real.get(n, n) in files),
        "placeholder_lines": sum(n in real for n in listed),
        "placeholders_carry_the_right_launcher": all(listed.get(pl) == sha(files[nm]) for pl, nm in real.items()),
        "lines_naming_an_existing_file": sum(n in files for n in listed), "sorted_by_name": [n for _, n in lines] == sorted(n for _, n in lines)}
    mine = open(a.listing, encoding="utf-8").read().splitlines()
    theirs = open(os.path.join(rc, "return_listing.txt"), encoding="utf-8").read().splitlines()
    diff = [(x, y) for x, y in zip(mine, theirs) if x != y]
    octal = {pl: "".join(c if ord(c) < 128 else "".join("\\%03o" % b for b in c.encode()) for c in nm) for pl, nm in real.items()}
    ok = []
    for x, y in diff:
        hit = [pl for pl, o in octal.items() if x.endswith("gate_records/" + o) and y.endswith("gate_records/" + pl)
               and x[:len(x) - len(o)] == y[:len(y) - len(pl)]]
        ok.append(len(hit) == 1)
    res["return_listing.txt"] = {"lines": len(theirs), "lines_of_the_archive_listing": len(mine), "lines_differing": len(diff),
                                 "differing_in_the_name_of_a_launcher_alone": sum(ok)}
    kr = json.load(open(os.path.join(rc, "keep_report.json"), encoding="utf-8"))
    kept = {}
    for d, _, fs in os.walk(os.path.join(rc, "return")):
        for f in fs:
            p = os.path.join(d, f)
            kept[os.path.relpath(p, os.path.join(rc, "return")).replace(os.sep, "/")] = p
    left = {real.get(x["file"], x["file"]): x for x in kr["left_out"]}
    res["keep_report.json"] = {
        "left_out": len(kr["left_out"]), "left_out_equal_received_less_kept": set(left) == set(files) - set(kept),
        "left_out_hashes_and_sizes_equal": all(sha(files[n]) == x["sha256"] and os.path.getsize(files[n]) == x["bytes"] for n, x in left.items()),
        "placeholders_in_left_out": sum(x["file"] in real for x in kr["left_out"]), "names_replaced_in_the_lists": kr.get("names_replaced_in_the_lists"),
        "rows": len(kr["files"]), "rows_equal_kept_files": {r["file"] for r in kr["files"]} == set(kept),
        "row_hashes_equal": sum(sha(files[r["file"]]) == r["sha256_received"] and sha(kept[r["file"]]) == r["sha256_kept"] for r in kr["files"]),
        "counts": {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in kr.items() if k not in ("files", "left_out")},
        "changed_rows": sum(r["changed"] for r in kr["files"])}
    esc = re.compile(rb"[\x80-\xff]|\\u[0-9a-fA-F]{4}|\\[0-7]{3}|\\x[0-9a-fA-F]{2}")
    res["escapes_or_characters_outside_ascii"] = {f: len(esc.findall(open(os.path.join(rc, f), "rb").read())) for f in ("return_files.sha256", "return_listing.txt", "keep_report.json", "return_kept.sha256")}
    if a.out:
        open(a.out, "w").write(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
