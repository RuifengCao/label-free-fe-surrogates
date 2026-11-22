"""The kept copy of G-C2.3's return package (after the run; not under the stamp).

    python -I audit/c23_keep.py RECEIVED KEPT OUT STRINGS.json [LISTING]

RECEIVED is the unpacked return package (its gate3_records/ folder), KEPT the folder to write and OUT the folder of
the lists (records/c23). The repository holds the kept copy in records/c23/return without its label and prediction
files, which are deposited outside it (c23_deposit.py). Every file is copied, with these differences:
  - in text files (.log, .json, .py, .txt) the line ends CR LF, which the laptop's Windows wrote, become LF, the
    line end of every text file of this repository;
  - in text files the path of the working folder on the laptop, a folder of the owner's user account, is replaced
    by W, the name the runbook gives that folder, in both its spellings: the Windows path, with single and with
    doubled backslashes, and the path under which the operator's Linux shell mounts it;
  - the model states of the host check are not kept: the repository's rules leave them out (*.pt).
The package of this gate holds no launcher and none of the scripts with which the owner pauses and continues a run
(RUNBOOK_C23.md, section 9), so nothing else is left out and no other word is replaced. The name of the folder that
is replaced is not in this repository. It is read from STRINGS.json, the file that the owner keeps with G-C2.2's
package as received (its entry operator_name; audit/c22_keep.py). Without it the copy cannot be made again; with
it, it is made again byte for byte.

The script writes into OUT:
  - keep_report.json: what was changed and left out, by counts, with the SHA-256 of every file as received and as
    kept;
  - return_files.sha256: the SHA-256 of the files as received;
  - return_kept.sha256: the SHA-256 of the files as kept;
  - return_listing.txt, when LISTING is given: the archive's listing as `tar --numeric-owner -tvzf` prints it at
    UTC.
"""
import hashlib
import json
import pathlib
import re
import sys

TEXT = {".log", ".json", ".py", ".txt"}


def main(received: pathlib.Path, kept: pathlib.Path, out: pathlib.Path, strings: pathlib.Path, listing=None) -> None:
    st = json.loads(strings.read_text(encoding="utf-8"))
    name = st["operator_name"].encode()
    sep = rb"(?:\\\\|\\)"                                   # a backslash, or the two that a JSON string writes for one
    folder = re.compile(rb"[A-Za-z]:" + sep + rb"Users" + sep + rb"[^\\\r\n\"]+" + sep + re.escape(name) + sep + rb"c2dev|mnt/"
                        + re.escape(name) + rb"/c2dev")
    left_out, crlf, paths, rows = [], [], {}, []
    for p in sorted(received.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(received).as_posix()
        raw = p.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if p.suffix == ".pt":
            left_out.append({"file": rel, "sha256": sha, "bytes": len(raw)})
            continue
        assert all(ord(c) < 128 for c in rel), "a file name outside ASCII"
        data = raw
        if p.suffix in TEXT:
            if b"\r\n" in data:
                data = data.replace(b"\r\n", b"\n")
                crlf.append(rel)
            data, n = folder.subn(b"W", data)
            if n:
                paths[rel] = n
            assert name not in data and name.lower() not in data.lower(), f"{rel}: the name outside the folder's path"
            assert b"\r" not in data, rel
            assert all(b < 128 for b in data), f"{rel}: a byte outside ASCII"
        else:
            assert p.suffix == ".npz", rel
        q = kept / rel
        q.parent.mkdir(parents=True, exist_ok=True)
        q.write_bytes(data)
        rows.append({"file": rel, "sha256_received": sha, "sha256_kept": hashlib.sha256(data).hexdigest(),
                     "changed": data != raw})
    rep = {"received_files": len(rows) + len(left_out), "kept_files": len(rows), "left_out": left_out,
           "line_ends_converted": crlf, "folder_replaced": paths,
           "unchanged": sum(not r["changed"] for r in rows), "files": rows}
    (out / "keep_report.json").write_text(json.dumps(rep, indent=1) + "\n")
    as_received = {r["file"]: r["sha256_received"] for r in rows}
    as_received.update({r["file"]: r["sha256"] for r in left_out})
    (out / "return_files.sha256").write_text("".join(f"{as_received[k]}  {k}\n" for k in sorted(as_received)))
    (out / "return_kept.sha256").write_text("".join(f"{r['sha256_kept']}  {r['file']}\n" for r in rows))
    if listing is not None:
        text = listing.read_text()
        assert all(ord(c) < 128 for c in text)
        (out / "return_listing.txt").write_text(text)
    print(json.dumps({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in rep.items()}))


if __name__ == "__main__":
    main(*map(pathlib.Path, sys.argv[1:6]))
