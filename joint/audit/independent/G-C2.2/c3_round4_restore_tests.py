"""Round 4, item 3: what the author's deposit script does with archives and records that are wrong.

Usage:  python c3_round4_restore_tests.py SCRIPT ARCHIVE DEPOSIT.json RETURN_SLIM KEPT.sha256 WORK
                                          [--python PYTHON] [--out OUT.json]

SCRIPT        the author's audit/c22_deposit.py; it is run as a program and never imported
ARCHIVE       the deposited archive
DEPOSIT.json  its record
RETURN_SLIM   records/c22/return as the repository holds it, without the array files
KEPT.sha256   the list of the kept files
WORK          a new, empty folder for the test cases (nothing is ever removed from it)

Four groups of cases:

  A  the real archive, changed, with the real record (what a reader meets if the download is not
     the deposited archive);
  B  the real archive, changed, with a record whose size and hash of the archive are changed to
     fit (the record itself would have to be changed for these);
  C  small archives and records written together by the writer below, with names that try to
     leave the folder and with members that are not plain files;
  D  the command "check" on folders and records that are wrong.

Every case reports the exit status, the first line of the message and the files that were
written.  The archives are written by the function ustar_member below, not by the standard
library's tar module.
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

BLOCK = 512
MTIME = 1794744900


def octal(n, width):
    return ("%0*o" % (width - 1, n)).encode() + b"\0"


def ustar_member(name, data=b"", typeflag=b"0", linkname=b"", prefix=b""):
    """One member in the ustar format: its header, its content and the padding."""
    name = name if isinstance(name, bytes) else name.encode()
    h = bytearray(BLOCK)
    h[0:len(name)] = name
    h[100:108] = octal(0o644, 8)
    h[108:116] = octal(0, 8)
    h[116:124] = octal(0, 8)
    h[124:136] = octal(len(data), 12)
    h[136:148] = octal(MTIME, 12)
    h[148:156] = b" " * 8
    h[156:157] = typeflag
    h[157:157 + len(linkname)] = linkname
    h[257:263] = b"ustar\0"
    h[263:265] = b"00"
    h[345:345 + len(prefix)] = prefix
    h[148:156] = ("%06o" % sum(h)).encode() + b"\0 "
    return bytes(h) + data + b"\0" * ((-len(data)) % BLOCK)


def close(body):
    body += b"\0" * (2 * BLOCK)
    return body + b"\0" * ((-len(body)) % 10240)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def record_for(archive_bytes, files, base=None):
    r = dict(base) if base else {"gate": "test", "what": "test", "doi": "test"}
    r["archive"] = {"name": "t.tar", "bytes": len(archive_bytes), "sha256": sha(archive_bytes), "format": "test"}
    r["n_files"] = len(files)
    r["bytes_of_the_files"] = sum(f["bytes"] for f in files)
    r["files"] = files
    return r


def entry(path, data):
    return {"path": path, "bytes": len(data), "sha256": sha(data)}


def files_under(root):
    root = pathlib.Path(root)
    if not root.exists():
        return []
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() or p.is_symlink())


class Runner:
    def __init__(self, python, script, work):
        self.python, self.script, self.work = python, script, pathlib.Path(work)
        self.results = {}

    def folder(self, case):
        d = self.work / case
        d.mkdir(parents=True)
        return d

    def run(self, case, args, cwd):
        p = subprocess.run([self.python, "-I", "-B", str(self.script)] + args, cwd=cwd,
                           capture_output=True, text=True)
        lines = (p.stdout + p.stderr).strip().splitlines()
        return p.returncode, [ln.replace(str(self.work.resolve()), "WORK") for ln in lines]

    def restore(self, case, archive_bytes, record, note, before=None):
        d = self.folder(case)
        (d / "t.tar").write_bytes(archive_bytes)
        (d / "deposit.json").write_text(json.dumps(record, indent=1) + "\n", encoding="ascii")
        (d / "top" / "ret").mkdir(parents=True)
        for rel, data in (before or {}).items():
            q = d / "top" / "ret" / rel
            q.parent.mkdir(parents=True, exist_ok=True)
            q.write_bytes(data)
        had = set(files_under(d / "top"))
        code, lines = self.run(case, ["restore", "t.tar", "deposit.json", "top/ret"], d)
        now = files_under(d / "top")
        self.results[case] = {"note": note, "exit": code, "message": lines[-1][:160] if lines else "",
                              "written": [f for f in now if f not in had][:6],
                              "n_written": len([f for f in now if f not in had]),
                              "outside_ret": [f for f in now if not f.startswith("ret/")]}
        (d / "t.tar").write_bytes(b"")          # keep the scratch folder small
        return d

    def check(self, case, record, ret_src, kept_list, change, note):
        d = self.folder(case)
        shutil.copytree(ret_src, d / "ret")
        (d / "deposit.json").write_text(json.dumps(record, indent=1) + "\n", encoding="ascii")
        change(d / "ret")
        code, lines = self.run(case, ["check", "deposit.json", "ret", str(pathlib.Path(kept_list).resolve())], d)
        self.results[case] = {"note": note, "exit": code, "messages": [ln[:200] for ln in lines]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("archive")
    ap.add_argument("deposit")
    ap.add_argument("return_slim")
    ap.add_argument("kept_list")
    ap.add_argument("work")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--out")
    a = ap.parse_args()
    script = pathlib.Path(a.script).resolve()
    real = pathlib.Path(a.archive).read_bytes()
    rec = json.loads(pathlib.Path(a.deposit).read_text())
    files = rec["files"]
    r = Runner(a.python, script, a.work)

    # where the members of the real archive lie
    offsets, pos = [], 0
    for f in files:
        offsets.append(pos)
        pos += BLOCK + f["bytes"] + ((-f["bytes"]) % BLOCK)
    end = pos

    # A: the real record
    b = bytearray(real); b[offsets[0] + BLOCK + 100] ^= 1
    r.restore("A1_one_bit_of_a_file", bytes(b), rec, "real record; one bit of the first file changed")
    r.restore("A2_cut_short", real[:-10240], rec, "real record; the last 10,240 bytes cut off")
    r.restore("A3_one_byte_more", real + b"\0", rec, "real record; one zero byte added at the end")
    b = bytearray(real); b[offsets[3] + 1] ^= 1
    r.restore("A4_one_bit_of_a_header", bytes(b), rec, "real record; one bit of a name in a header changed")
    extra = ustar_member("labels/eval_9999.npz", b"more")
    r.restore("A5_one_member_more", close(real[:end] + extra), rec, "real record; one more member in the archive")

    # B: the record's size and hash of the archive changed to fit
    b = bytearray(real); b[offsets[4] + BLOCK + 100] ^= 1
    r.restore("B1_changed_file", bytes(b), record_for(bytes(b), files, rec),
              "record fits the archive as a whole; one bit of the fifth file changed")
    arch = close(real[:end] + extra)
    r.restore("B2_member_outside_the_list", arch, record_for(arch, files, rec),
              "record fits the archive as a whole; one more member that the list does not name")
    arch = close(real[:end] + ustar_member("../../outside.npz", b"more"))
    r.restore("B3_member_outside_the_list_and_the_folder", arch, record_for(arch, files, rec),
              "as B2, the member's name leading out of the folder")
    arch = close(real[:offsets[140]])
    r.restore("B4_one_member_fewer", arch, record_for(arch, files, rec),
              "record fits the archive as a whole; the last member is not in the archive")

    # C: small archives and records written together
    one, two = b"first file", b"second file"

    def small(case, members, listed, note, before=None):
        arch = close(b"".join(members))
        return r.restore(case, arch, record_for(arch, listed), note, before)

    small("C0_good", [ustar_member("labels/a.npz", one), ustar_member("run_files/s5/preds.npz", two)],
          [entry("labels/a.npz", one), entry("run_files/s5/preds.npz", two)], "control: two good members")
    small("C1_order", [ustar_member("run_files/s5/preds.npz", two), ustar_member("labels/a.npz", one)],
          [entry("labels/a.npz", one), entry("run_files/s5/preds.npz", two)], "the two members in the other order")
    small("C2_up_from_labels", [ustar_member("labels/../../x.npz", one)], [entry("labels/../../x.npz", one)],
          "listed and packed: a name that climbs out of labels/ and of the folder")
    small("C3_absolute", [ustar_member("/labels/a.npz", one)], [entry("/labels/a.npz", one)],
          "listed and packed: an absolute name")
    small("C4_dotdot_as_run", [ustar_member("run_files/../preds_x.npz", one)],
          [entry("run_files/../preds_x.npz", one)], "listed and packed: '..' in the place of the run's folder")
    small("C5_dotdot_twice", [ustar_member("run_files/../../preds_x.npz", one)],
          [entry("run_files/../../preds_x.npz", one)], "listed and packed: '..' twice")
    small("C6_symbolic_link", [ustar_member("labels/a.npz", b"", b"2", b"../../outside")],
          [entry("labels/a.npz", b"")], "a symbolic link under a good name")
    small("C7_hard_link", [ustar_member("labels/a.npz", b"", b"1", b"../../outside")],
          [entry("labels/a.npz", b"")], "a hard link under a good name")
    small("C8_folder", [ustar_member("labels/a.npz", b"", b"5")], [entry("labels/a.npz", b"")],
          "a folder under a good name")
    small("C9_fifo", [ustar_member("labels/a.npz", b"", b"6")], [entry("labels/a.npz", b"")],
          "a named pipe under a good name")
    small("C10_backslashes", [ustar_member("labels/..\\..\\x.npz", one)], [entry("labels/..\\..\\x.npz", one)],
          "listed and packed: backslashes in the place of slashes")
    pax = b"20 path=../../x.npz\n"
    small("C11_extended_header", [ustar_member("PaxHeader/a", pax, b"x"), ustar_member("labels/a.npz", one)],
          [entry("labels/a.npz", one)], "an extended header that gives the member another name; the list has the plain name")
    small("C11b_extended_header_listed", [ustar_member("PaxHeader/a", pax, b"x"), ustar_member("labels/a.npz", one)],
          [entry("../../x.npz", one)], "the same, and the list has the other name")
    small("C11c_not_a_tar_file", [b"x" * 700], [entry("labels/a.npz", one)],
          "bytes that are no tar file, with a record that fits them")
    small("C12_prefix_field", [ustar_member("a.npz", one, prefix=b"../../labels")],
          [entry("../../labels/a.npz", one)], "listed and packed: a name through the prefix field that climbs out")
    small("C13_other_file_there", [ustar_member("labels/a.npz", one)], [entry("labels/a.npz", one)],
          "a different file stands where the member goes", before={"labels/a.npz": b"other"})
    d = r.work / "C13_other_file_there" / "top" / "ret" / "labels" / "a.npz"
    r.results["C13_other_file_there"]["file_there_unchanged"] = d.read_bytes() == b"other"
    small("C14_same_file_there", [ustar_member("labels/a.npz", one)], [entry("labels/a.npz", one)],
          "the same file stands where the member goes", before={"labels/a.npz": one})
    small("C15_good_then_bad", [ustar_member("labels/a.npz", one), ustar_member("labels/b.npz", two)],
          [entry("labels/a.npz", one), entry("labels/b.npz", one)],
          "the second member differs from its entry: is the first one written?")

    # what the name of case C10 would be on a system where the backslash separates folders
    # (computed with the standard library's rules for such paths; not run on such a system)
    import ntpath
    import re as _re
    pattern = _re.compile(r"(labels/[^/]+\.npz|run_files/[^/]+/preds[^/]*\.npz)")
    name = "labels/..\\..\\x.npz"
    target = ntpath.normpath(str(pathlib.PureWindowsPath("C:/w/ret") / name))
    r.results["C10_inferred_backslash_system"] = {
        "note": "computed, not run: where C10's name would point from the folder C:/w/ret",
        "name_passes_the_pattern_of_the_script": bool(pattern.fullmatch(name)),
        "target": target, "inside_the_folder": target.lower().startswith("c:\\w\\ret\\")}

    # D: the command check
    slim = pathlib.Path(a.return_slim)
    some = sorted(p.relative_to(slim).as_posix() for p in slim.rglob("*") if p.is_file())
    victim = next(p for p in some if p.endswith(".json") or p.endswith(".log"))

    def nothing(ret):
        pass

    def change_file(ret):
        q = ret / victim
        q.write_bytes(q.read_bytes() + b"\n")

    def add_file(ret):
        (ret / "labels").mkdir(exist_ok=True)
        (ret / "labels" / "new.npz").write_bytes(b"x")

    def drop_file(ret):
        (ret / victim).rename(ret.parent / "taken_out")

    def half(ret):
        # write the label files only, with content that fits the list
        for f, o in zip(files, offsets):
            if f["path"].startswith("labels/"):
                q = ret / f["path"]
                q.parent.mkdir(parents=True, exist_ok=True)
                q.write_bytes(real[o + BLOCK:o + BLOCK + f["bytes"]])

    r.check("D0_as_in_the_repository", rec, slim, a.kept_list, nothing, "control")
    r.check("D1_changed_file", rec, slim, a.kept_list, change_file, "one kept file one byte longer")
    r.check("D2_other_file", rec, slim, a.kept_list, add_file, "one file that the list does not name")
    r.check("D3_missing_file", rec, slim, a.kept_list, drop_file, "one kept file that is no array file taken out")
    r.check("D4_labels_only", rec, slim, a.kept_list, half, "the 132 label files written back, the nine others not")
    bad = json.loads(json.dumps(rec)); bad["files"][0]["sha256"] = "0" * 64
    r.check("D5_record_wrong_hash", bad, slim, a.kept_list, nothing, "record: the hash of one file wrong")
    bad = json.loads(json.dumps(rec)); bad["files"][0]["bytes"] += 1; bad["files"][1]["bytes"] -= 1
    r.check("D6_record_wrong_sizes", bad, slim, a.kept_list, nothing,
            "record: the sizes of two files wrong, their sum right")
    bad = json.loads(json.dumps(rec)); bad["archive"]["sha256"] = "0" * 64; bad["archive"]["bytes"] = 1
    r.check("D7_record_wrong_archive", bad, slim, a.kept_list, nothing, "record: size and hash of the archive wrong")
    bad = json.loads(json.dumps(rec)); bad["files"] = bad["files"][1:]; bad["n_files"] -= 1
    bad["bytes_of_the_files"] = sum(f["bytes"] for f in bad["files"])
    r.check("D8_record_one_entry_fewer", bad, slim, a.kept_list, nothing, "record: one entry fewer")
    bad = json.loads(json.dumps(rec)); bad["files"][0], bad["files"][1] = bad["files"][1], bad["files"][0]
    r.check("D9_record_order", bad, slim, a.kept_list, nothing, "record: two entries in the other order")

    print(json.dumps(r.results, indent=1))
    if a.out:
        pathlib.Path(a.out).write_text(json.dumps(r.results, indent=1) + "\n")


if __name__ == "__main__":
    main()
