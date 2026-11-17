"""The label and prediction files of gate G-C2.2's return package, which are deposited outside the
repository (after the run; not under the stamp).

The kept copy of the return package (see c22_keep.py) has 261 files. The repository holds 120
of them in records/c22/return/. The other 141 are the files of the gate's labels and
predictions, kept unchanged: the labels of the 132 members and the three prediction files of
each run. They are deposited as one archive; records/c22/deposit.json names the deposit and
gives the size and the SHA-256 of the archive and of each file. The array files of the host
check are small and stay in the repository.

  python -I audit/c22_deposit.py pack KEPT KEPT.sha256 ARCHIVE DEPOSIT.json DOI
      KEPT is a kept copy that is whole, as c22_keep.py writes it, and KEPT.sha256 the list of
      its hashes (records/c22/return_kept.sha256). Writes the archive of the label and
      prediction files and DEPOSIT.json. Stops, and writes nothing, if one of these files of
      the list is missing from KEPT or is not the listed file.
  python -I audit/c22_deposit.py restore ARCHIVE DEPOSIT.json RETURN
      Checks the archive and each of its files against DEPOSIT.json and then writes the files
      into RETURN, for a checkout records/c22/return, which then holds the kept copy whole.
      Nothing is written unless the archive and every file are right.
  python -I audit/c22_deposit.py check DEPOSIT.json RETURN KEPT.sha256
      Checks DEPOSIT.json against the list of the kept copy's hashes, and every file that
      RETURN holds against that list; says whether RETURN holds the kept copy whole. It does
      not read the archive, so it tests neither the entry archive of the record nor the size
      of a file that RETURN does not hold. Its exit status is 1 if the record or a file is
      wrong, if RETURN holds a file that the list does not name, or if a file is missing that
      is not deposited.

The archive is a plain ustar file made by this script alone, so that it is the same on every
machine: the files in the byte order of their paths, mode 0644, owner and group 0, and one
time for all, that of the return package.
"""
import hashlib
import io
import json
import pathlib
import re
import sys
import tarfile

NAME = re.compile(r"(labels/[A-Za-z0-9_]+\.npz|run_files/[A-Za-z0-9_]+/preds[A-Za-z0-9_]*\.npz)")
MTIME = 1794744900          # 15 November 2026, 12:15:00 GMT
FORMAT = ("plain ustar; the files in the byte order of their paths, mode 0644, owner and "
          "group 0, time 2026-11-15T12:15:00Z")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_list(path):
    kept = {}
    for line in pathlib.Path(path).read_text(encoding="ascii").splitlines():
        h, name = line.split(maxsplit=1)
        kept[name.lstrip("*")] = h
    return kept


def pack(kept, kept_list, archive, deposit, doi):
    kept, archive, hashes = pathlib.Path(kept), pathlib.Path(archive), read_list(kept_list)
    paths = sorted((p for p in hashes if NAME.fullmatch(p)), key=lambda s: s.encode())
    if not paths:
        sys.exit("the list names no label or prediction file")
    files, blobs = [], []
    for p in paths:
        if not (kept / p).is_file():
            sys.exit(f"missing from the kept copy: {p}")
        data = (kept / p).read_bytes()
        if sha(data) != hashes[p]:
            sys.exit(f"not the kept file: {p}")
        files.append({"path": p, "bytes": len(data), "sha256": hashes[p]})
        blobs.append(data)
    with tarfile.open(archive, "w", format=tarfile.USTAR_FORMAT) as tar:
        for f, data in zip(files, blobs):
            info = tarfile.TarInfo(f["path"])
            info.size, info.mtime, info.mode = len(data), MTIME, 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            tar.addfile(info, io.BytesIO(data))
    raw = archive.read_bytes()
    record = {
        "gate": "G-C2.2",
        "what": "the label and prediction files of the kept copy of the return package; the repository does not hold them",
        "doi": doi,
        "archive": {"name": archive.name, "bytes": len(raw), "sha256": sha(raw), "format": FORMAT},
        "n_files": len(files),
        "bytes_of_the_files": sum(f["bytes"] for f in files),
        "files": files,
    }
    pathlib.Path(deposit).write_text(json.dumps(record, indent=1) + "\n", encoding="ascii")
    print(f"{len(files)} files, {record['bytes_of_the_files']} bytes; archive {len(raw)} bytes, sha256 {record['archive']['sha256']}")


def restore(archive, deposit, ret):
    record = json.loads(pathlib.Path(deposit).read_text(encoding="ascii"))
    raw = pathlib.Path(archive).read_bytes()
    if len(raw) != record["archive"]["bytes"] or sha(raw) != record["archive"]["sha256"]:
        sys.exit("the archive is not the one that the deposit record names")
    ret, want, todo = pathlib.Path(ret), record["files"], []
    root = ret.resolve()
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tar:
        members = tar.getmembers()
        if [m.name for m in members] != [f["path"] for f in want]:
            sys.exit("the archive's files are not the listed ones in the listed order")
        for m, f in zip(members, want):
            if not m.isfile() or not NAME.fullmatch(m.name):
                sys.exit(f"not a label or prediction file: {m.name}")
            out = ret / m.name
            if root not in out.resolve().parents:
                sys.exit(f"outside the target folder: {m.name}")
            data = tar.extractfile(m).read()
            if len(data) != f["bytes"] or sha(data) != f["sha256"]:
                sys.exit(f"wrong content: {m.name}")
            if out.exists() and (not out.is_file() or out.read_bytes() != data):
                sys.exit(f"something else is already there: {out}")
            todo.append((out, data))
    written = 0
    for out, data in todo:
        if not out.exists():
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            written += 1
    print(f"archive and {len(want)} files checked; {written} written into {ret}, {len(todo) - written} were already there")


def check(deposit, ret, kept_list):
    record = json.loads(pathlib.Path(deposit).read_text(encoding="ascii"))
    kept, files = read_list(kept_list), record["files"]
    listed = {f["path"]: f for f in files}
    ok = ([f["path"] for f in files] == sorted(listed, key=lambda s: s.encode())
          and sorted(listed) == sorted(p for p in kept if NAME.fullmatch(p))
          and all(kept[p] == f["sha256"] for p, f in listed.items())
          and record["n_files"] == len(files)
          and record["bytes_of_the_files"] == sum(f["bytes"] for f in files))
    print(f"the deposit record lists the {len(listed)} label and prediction files of the kept copy with its hashes: {'yes' if ok else 'NO'}")
    ret = pathlib.Path(ret)
    held = {p.relative_to(ret).as_posix() for p in ret.rglob("*") if p.is_file()}
    wrong = []
    for p in sorted(held & set(kept)):
        data = (ret / p).read_bytes()
        if sha(data) != kept[p] or (p in listed and len(data) != listed[p]["bytes"]):
            wrong.append(p)
    extra = sorted(held - set(kept))
    missing = set(kept) - held
    other, deposited = sorted(missing - set(listed)), sorted(missing & set(listed))
    print(f"{ret} holds {len(held & set(kept))} of the {len(kept)} kept files; wrong content: {len(wrong)}; files that the list does not name: {len(extra)}")
    for name, group in (("wrong content", wrong), ("not in the list", extra), ("missing and not deposited", other)):
        if group:
            print(f"{name}: {len(group)}: {' '.join(group[:20])}")
    if deposited:
        print(f"missing: {len(deposited)} of the {len(listed)} label and prediction files, which the deposit holds")
    if not missing:
        print("the kept copy is whole")
    if not ok or wrong or extra or other:
        sys.exit(1)


if __name__ == "__main__":
    commands = {"pack": (pack, 5), "restore": (restore, 3), "check": (check, 3)}
    if len(sys.argv) < 2 or sys.argv[1] not in commands or len(sys.argv) != 2 + commands[sys.argv[1]][1]:
        sys.exit(__doc__)
    commands[sys.argv[1]][0](*sys.argv[2:])
