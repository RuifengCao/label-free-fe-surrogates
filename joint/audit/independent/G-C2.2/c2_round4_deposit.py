"""Round 4, item 2: the deposit record and the archive, read with an own reader of the tar format.

Usage:  python c2_round4_deposit.py DEPOSIT.json ARCHIVE KEPT_WHOLE KEPT.sha256 FILES.sha256
                                    [--received RECEIVED_UNPACKED] [--out OUT.json]

DEPOSIT.json   the record of the deposit (joint/records/c22/deposit.json)
ARCHIVE        the archive that is deposited
KEPT_WHOLE     a whole kept copy (a folder with all 261 files)
KEPT.sha256    the list of the kept files (return_kept.sha256)
FILES.sha256   the list of the files as received (return_files.sha256)
RECEIVED_UNPACKED   the unpacked return package (its gate_records/ folder), if it is at hand: the
               members of the archive are then compared with the files as received, byte for byte

What it checks:

  - the record: its entries against the files of the whole kept copy (bytes and SHA-256), against
    the two lists, the counts by kind, the sum of the bytes, the order, the size and the hash of
    the archive;
  - which files of the kept copy have the ending .npz and are not in the record;
  - the archive, block by block: every header field of every member, the checksum, the padding
    after each member, the end of the archive, and every byte of the headers that is not zero
    and belongs to no field that the record's "format" describes.

The reader below is written from the description of the ustar format (512-byte blocks; the header
fields at fixed offsets; numbers in octal).  It does not use the standard library's tar module and
imports nothing of the author's.
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys

BLOCK = 512
FIELDS = [("name", 0, 100), ("mode", 100, 8), ("uid", 108, 8), ("gid", 116, 8), ("size", 124, 12),
          ("mtime", 136, 12), ("chksum", 148, 8), ("typeflag", 156, 1), ("linkname", 157, 100),
          ("magic", 257, 6), ("version", 263, 2), ("uname", 265, 32), ("gname", 297, 32),
          ("devmajor", 329, 8), ("devminor", 337, 8), ("prefix", 345, 155), ("pad", 500, 12)]


def text(b):
    return b.split(b"\0", 1)[0].decode("ascii")


def octal(b):
    s = b.rstrip(b"\0 ").decode("ascii")
    return int(s, 8) if s else None


def read_archive(data):
    """Return (members, problems, end).  A member is a dict of its header fields and its place."""
    members, problems = [], []
    pos = 0
    while pos + BLOCK <= len(data):
        h = data[pos:pos + BLOCK]
        if h == b"\0" * BLOCK:
            break
        f = {k: h[o:o + n] for k, o, n in FIELDS}
        stored = octal(f["chksum"])
        summed = sum(h[:148]) + 8 * 32 + sum(h[156:])
        size = octal(f["size"])
        m = {"offset": pos, "name": text(f["name"]), "prefix": text(f["prefix"]),
             "mode": octal(f["mode"]), "uid": octal(f["uid"]), "gid": octal(f["gid"]),
             "size": size, "mtime": octal(f["mtime"]), "typeflag": f["typeflag"].decode("latin-1"),
             "linkname": text(f["linkname"]), "magic": f["magic"], "version": f["version"],
             "uname": text(f["uname"]), "gname": text(f["gname"]),
             "devmajor": f["devmajor"], "devminor": f["devminor"],
             "raw": {k: v for k, v in f.items()}, "checksum_ok": stored == summed}
        if not m["checksum_ok"]:
            problems.append("checksum of the header at %d" % pos)
        if f["pad"] != b"\0" * 12:
            problems.append("bytes after the prefix field at %d" % pos)
        for k in ("name", "linkname", "uname", "gname", "prefix"):
            body = f[k].split(b"\0", 1)
            if len(body) == 2 and body[1].strip(b"\0"):
                problems.append("bytes after the end of %s at %d" % (k, pos))
        start = pos + BLOCK
        m["data"] = (start, size)
        fill = (-size) % BLOCK
        if data[start + size:start + size + fill] != b"\0" * fill:
            problems.append("padding after the member at %d is not zero" % pos)
        members.append(m)
        pos = start + size + fill
    end = {"end_offset": pos, "trailing_bytes": len(data) - pos,
           "trailing_all_zero": data[pos:] == b"\0" * (len(data) - pos),
           "length_multiple_of_10240": len(data) % 10240 == 0,
           "at_least_two_zero_blocks": len(data) - pos >= 2 * BLOCK}
    return members, problems, end


def sha_list(path):
    out = {}
    for line in pathlib.Path(path).read_text().splitlines():
        h, name = line.split("  ", 1)
        out[name] = h
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deposit")
    ap.add_argument("archive")
    ap.add_argument("kept")
    ap.add_argument("kept_list")
    ap.add_argument("files_list")
    ap.add_argument("--received")
    ap.add_argument("--out")
    a = ap.parse_args()
    dep = json.loads(pathlib.Path(a.deposit).read_text())
    kept = pathlib.Path(a.kept)
    files = dep["files"]
    paths = [f["path"] for f in files]
    res = {}

    # the record against the whole kept copy and the two lists
    on_disk = {p.relative_to(kept).as_posix(): p for p in kept.rglob("*") if p.is_file()}
    klist, flist = sha_list(a.kept_list), sha_list(a.files_list)
    bad = []
    for f in files:
        p = on_disk.get(f["path"])
        if p is None:
            bad.append(f["path"] + ": not in the kept copy")
            continue
        b = p.read_bytes()
        if len(b) != f["bytes"] or hashlib.sha256(b).hexdigest() != f["sha256"]:
            bad.append(f["path"] + ": bytes or hash differ from the file")
        if klist.get(f["path"]) != f["sha256"]:
            bad.append(f["path"] + ": hash differs from the list of the kept files")
        if flist.get(f["path"]) != f["sha256"]:
            bad.append(f["path"] + ": hash differs from the list of the files as received")
    kinds = {"labels/eval_": 0, "labels/former_": 0, "labels/tested_": 0, "run_files/": 0, "other": 0}
    for p in paths:
        for k in kinds:
            if p.startswith(k):
                kinds[k] += 1
                break
        else:
            kinds["other"] += 1
    npz_all = sorted(p for p in on_disk if p.endswith(".npz"))
    res["record"] = {
        "entries": len(files), "n_files": dep["n_files"], "entries_wrong": bad,
        "paths_unique": len(set(paths)) == len(paths),
        "order_is_byte_order": paths == sorted(paths, key=lambda s: s.encode()),
        "kinds": kinds,
        "prediction_files": sorted(p for p in paths if p.startswith("run_files/")),
        "sum_of_bytes": sum(f["bytes"] for f in files),
        "bytes_of_the_files": dep["bytes_of_the_files"],
        "kept_files": len(on_disk), "kept_list_lines": len(klist), "files_list_lines": len(flist),
        "npz_in_kept_copy": len(npz_all),
        "npz_not_in_record": sorted(set(npz_all) - set(paths)),
        "bytes_of_npz_not_in_record": sum(on_disk[p].stat().st_size for p in set(npz_all) - set(paths)),
        "record_not_npz": sorted(p for p in paths if not p.endswith(".npz")),
        "keys": sorted(dep), "doi": dep["doi"],
    }

    # the archive
    data = pathlib.Path(a.archive).read_bytes()
    members, problems, end = read_archive(data)
    arch = dep["archive"]
    names = [(m["prefix"] + "/" if m["prefix"] else "") + m["name"] for m in members]
    content_bad = []
    for m, f in zip(members, files):
        s, n = m["data"]
        if n != f["bytes"] or hashlib.sha256(data[s:s + n]).hexdigest() != f["sha256"]:
            content_bad.append(f["path"])

    if a.received:
        rec = pathlib.Path(a.received)
        differ = []
        for m, f in zip(members, files):
            s, n = m["data"]
            q = rec / f["path"]
            if not q.is_file() or q.read_bytes() != data[s:s + n]:
                differ.append(f["path"])
        res["members_against_the_files_as_received"] = {"compared": len(members), "differing": differ}

    def values(key):
        return sorted({repr(m[key]) for m in members})

    header_bytes_other = 0
    for m in members:
        # every byte of the header that is not zero must lie in a field that is accounted for
        raw = m["raw"]
        for k in ("linkname", "uname", "gname", "prefix", "pad"):
            header_bytes_other += sum(1 for c in raw[k] if c)
    res["archive"] = {
        "bytes": len(data), "bytes_in_record": arch["bytes"],
        "sha256": hashlib.sha256(data).hexdigest(), "sha256_in_record": arch["sha256"],
        "name_in_record": arch["name"], "format_in_record": arch["format"],
        "members": len(members), "names_equal_record_in_order": names == paths,
        "content_wrong": content_bad, "problems": problems,
        "mode": values("mode"), "uid": values("uid"), "gid": values("gid"),
        "mtime": values("mtime"), "typeflag": values("typeflag"), "magic": values("magic"),
        "version": values("version"), "uname": values("uname"), "gname": values("gname"),
        "linkname": values("linkname"), "prefix": values("prefix"),
        "devmajor": values("devmajor"), "devminor": values("devminor"),
        "nonzero_bytes_in_link_owner_prefix_fields": header_bytes_other,
        "longest_name": max(len(n) for n in names),
        "header_and_padding_bytes": len(data) - sum(m["size"] for m in members),
        "end": end,
    }
    # every printable run of four or more characters in the bytes that are not file content
    outside = bytearray()
    pos = 0
    for m in members:
        s, n = m["data"]
        outside += data[pos:s]
        pos = s + n
    outside += data[pos:]
    runs = sorted({r.decode("ascii") for r in re.findall(rb"[\x20-\x7e]{4,}", bytes(outside))})
    known = set(paths)
    other = [r for r in runs if r not in known and not re.fullmatch(r"[0-7 ]+", r)
             and r not in ("ustar",)]
    res["archive"]["bytes_outside_file_content"] = len(outside)
    res["archive"]["printable_runs_outside_content"] = len(runs)
    res["archive"]["runs_that_are_not_a_listed_path_or_an_octal_number_or_the_magic"] = other

    print(json.dumps(res, indent=1, default=repr))
    if a.out:
        pathlib.Path(a.out).write_text(json.dumps(res, indent=1, default=repr) + "\n")
    ok = (not bad and not content_bad and not problems and names == paths
          and res["archive"]["sha256"] == arch["sha256"] and len(data) == arch["bytes"]
          and res["record"]["sum_of_bytes"] == dep["bytes_of_the_files"] and not other)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
