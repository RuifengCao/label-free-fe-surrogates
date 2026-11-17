"""The kept copy of G-C2.2's return package (after the run; not under the stamp).

    python -I audit/c22_keep.py RECEIVED KEPT OUT STRINGS.json [LISTING]

RECEIVED is the unpacked return package (its gate_records/ folder), KEPT the folder to write and OUT the folder of
the lists (records/c22). The repository holds the kept copy in records/c22/return without its label and prediction
files, which are deposited outside it (c22_deposit.py). Every file is copied, with these differences:
  - in text files (.log, .json, .py, .bat, .txt, and the queue's marker files .kill and .go) the line ends CR LF,
    which the laptop's Windows wrote, become LF, the line end of every text file of this repository;
  - in text files the path of the working folder on the laptop, a folder of the owner's user account, is replaced
    by W, the name the runbook gives that folder, in both its spellings: the Windows path and the path under
    which the operator's Linux shell mounts it;
  - in the message of one launcher, the name by which the owner addresses the operator is replaced by
    "the operator", and in a comment of the same launcher the name of another piece of the owner's work is
    replaced by "another project";
  - in the operator's record of incidents, the words that say what the owner used the GPU for during the pause
    are replaced by "for other things";
  - seven files are not kept: the two scripts of the queue that pause and continue a run and the two launchers that
    start them, whose prompts to the owner and file names are not in English; the log of the environment's setup,
    which lists the programs that were using the laptop's GPU; and the two model states of the host check, which
    the repository's rules leave out (*.pt). In the lists that this script writes, the names of the two launchers
    are replaced by the placeholders of NAMES below.
The strings that are replaced are not in this repository. They are read from STRINGS.json, a file of five entries
that the owner keeps with the package as received: operator_name, other_work, use_of_gpu, launcher_pause and
launcher_continuation. Without it the copy cannot be made again; with it, it is made again byte for byte.

The script writes into OUT:
  - keep_report.json: what was changed and left out, by counts, with the SHA-256 of every file as received and as
    kept;
  - return_files.sha256: the SHA-256 of the 268 files as received;
  - return_kept.sha256: the SHA-256 of the files as kept;
  - return_listing.txt, when LISTING is given: the archive's listing as `tar --numeric-owner -tvzf` prints it at
    UTC, with the names of the two launchers replaced.
"""
import hashlib
import json
import pathlib
import re
import sys

TEXT = {".log", ".json", ".py", ".bat", ".txt", ".kill", ".go"}
LEFT_OUT = ("queue/pause.py", "queue/resume.py", "queue/setup_log.txt")
# file, entry of STRINGS.json, replacement: each occurs once in its file
WORDS = (("queue/start.bat", "other_work", b"another project"),
         ("incidents.log", "use_of_gpu", b"for other things"))
# entry of STRINGS.json (a file name in the folder queue/), placeholder in the lists
NAMES = (("launcher_pause", "queue/<launcher of the pause>.bat"),
         ("launcher_continuation", "queue/<launcher of the continuation>.bat"))


def tar_spelling(name: str) -> str:
    """A file name as GNU tar lists it in the C locale: bytes outside ASCII as octal escapes."""
    return "".join(c if ord(c) < 128 else "".join(f"\\{b:03o}" for b in c.encode()) for c in name)


def main(received: pathlib.Path, kept: pathlib.Path, out: pathlib.Path, strings: pathlib.Path, listing=None) -> None:
    st = json.loads(strings.read_text(encoding="utf-8"))
    name = st["operator_name"].encode()
    folder = re.compile(rb"[A-Za-z]:\\Users\\[^\\\r\n]+\\" + re.escape(name) + rb"\\c2dev|mnt/" + re.escape(name)
                        + rb"/c2dev")
    placeholder = {"queue/" + st[key]: new for key, new in NAMES}
    left_out, crlf, paths, names, words, rows = [], [], {}, {}, {}, []
    for p in sorted(received.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(received).as_posix()
        raw = p.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if rel in placeholder or rel in LEFT_OUT or p.suffix == ".pt":
            left_out.append({"file": placeholder.get(rel, rel), "sha256": sha, "bytes": len(raw)})
            continue
        assert all(ord(c) < 128 for c in rel), "a file name outside ASCII that is not declared"
        data = raw
        if p.suffix in TEXT:
            if b"\r\n" in data:
                data = data.replace(b"\r\n", b"\n")
                crlf.append(rel)
            data, n = folder.subn(b"W", data)
            if n:
                paths[rel] = n
            if name in data:
                names[rel] = data.count(name)
                data = data.replace(name, b"the operator")
            for file, key, new in WORDS:
                if rel == file:
                    old = st[key].encode()
                    assert data.count(old) == 1, rel
                    data = data.replace(old, new)
                    words[rel] = 1
            assert b"\r" not in data, rel
        q = kept / rel
        q.parent.mkdir(parents=True, exist_ok=True)
        q.write_bytes(data)
        rows.append({"file": rel, "sha256_received": sha, "sha256_kept": hashlib.sha256(data).hexdigest(),
                     "changed": data != raw})
    assert len(left_out) == 7 and sum(r["file"] in placeholder.values() for r in left_out) == len(NAMES)
    rep = {"received_files": len(rows) + len(left_out), "kept_files": len(rows), "left_out": left_out,
           "names_replaced_in_the_lists": len(NAMES),
           "line_ends_converted": crlf, "folder_replaced": paths, "name_replaced": names,
           "words_replaced": words,
           "unchanged": sum(not r["changed"] for r in rows), "files": rows}
    (out / "keep_report.json").write_text(json.dumps(rep, indent=1) + "\n")
    as_received = {r["file"]: r["sha256_received"] for r in rows}
    as_received.update({r["file"]: r["sha256"] for r in left_out})
    (out / "return_files.sha256").write_text("".join(f"{as_received[k]}  {k}\n" for k in sorted(as_received)))
    (out / "return_kept.sha256").write_text("".join(f"{r['sha256_kept']}  {r['file']}\n" for r in rows))
    if listing is not None:
        text = listing.read_text()
        for old, new in placeholder.items():
            spelled = tar_spelling(old)
            assert text.count(spelled) == 1, "a launcher's name is not once in the listing"
            text = text.replace(spelled, new)
        assert all(ord(c) < 128 for c in text)
        (out / "return_listing.txt").write_text(text)
    print(json.dumps({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in rep.items()}))


if __name__ == "__main__":
    main(*map(pathlib.Path, sys.argv[1:6]))
