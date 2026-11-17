"""Audit of gate G-C2.2, item 5: the kept copy of the return package against the package as received.

  archive     SHA-256 and size of the archive, and the hash file that came with it;
  listing     return_listing.txt against the archive's own member list (names, sizes, times);
  received    return_files.sha256 against the SHA-256 of every file unpacked from the archive;
  kept        return_kept.sha256 against the files of records/c22/return in the proposed tree;
  differences every kept file compared with the received one: identical, or differing only by line ends (CR LF to
              LF), or by line ends and declared replacements; any other difference is listed with the differing
              lines counted. The replacements are detected, not assumed: a differing line is accepted only if the
              received line becomes the kept line when the path of the working folder (given with --path, in each
              spelling given) is replaced by W, or the name (given with --name) by "the operator";
  left out    the received files that are not kept, and keep_report.json's list of them with their hashes;
  privacy     a search of the kept copy and of the other new files for a path of a personal folder, for the name
              given, for e-mail addresses, for characters outside ASCII, and for the names given with --word.

The private strings are passed on the command line and are not written to the output; the output names them
PATH and NAME.

Round 2 added three things: other declared replacements (--replace OLD=NEW, a differing line is also accepted if
OLD becomes NEW in it); the search of every path that the commit adds or changes (--changes, the list of
`git diff --name-status`), not only of the kept copy and the author's new files; and a search for the private
strings in encoded form (hexadecimal and base64), which a search for the plain strings cannot see.

Usage:  python -I a6_kept_copy.py ARCHIVE RECEIVED_UNPACKED PROPOSED --path P [--path P2 ...] --name N [--word X ...]
        [--replace OLD=NEW ...] [--changes CHANGES.txt] [--out OUT.json]
        RECEIVED_UNPACKED is the folder that holds gate_records after unpacking; PROPOSED the export of the commit.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import tarfile


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def files_under(root):
    out = {}
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            out[os.path.relpath(p, root).replace(os.sep, "/")] = p
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive"); ap.add_argument("received"); ap.add_argument("proposed")
    ap.add_argument("--path", action="append", default=[]); ap.add_argument("--name", action="append", default=[])
    ap.add_argument("--word", action="append", default=[]); ap.add_argument("--out")
    ap.add_argument("--replace", action="append", default=[]); ap.add_argument("--changes")
    a = ap.parse_args()
    repl = [tuple(x.encode("utf-8") for x in r.split("=", 1)) for r in a.replace]
    res = {}
    raw = open(a.archive, "rb").read()
    side = a.archive[:-len(".tar.gz")] + ".sha256"
    res["archive"] = {"sha256": sha_bytes(raw), "bytes": len(raw),
                      "hash_file_matches": open(side).read().split()[0] == sha_bytes(raw) if os.path.exists(side) else None}
    with tarfile.open(a.archive) as tf:
        mem = tf.getmembers()
    tfiles = [m for m in mem if m.isfile()]
    res["archive"].update(members=len(mem), files=len(tfiles), other_kinds=sorted({m.type.decode() for m in mem if not m.isfile()}),
                          mtime_min=min(m.mtime for m in tfiles), mtime_max=max(m.mtime for m in tfiles),
                          dir_mtime_max=max((m.mtime for m in mem if m.isdir()), default=None),
                          total_bytes=sum(m.size for m in tfiles), owners=sorted({(m.uname, m.gname) for m in mem}).__len__())
    rc = os.path.join(a.proposed, "joint", "records", "c22")
    rec = files_under(os.path.join(a.received, "gate_records"))
    kept = files_under(os.path.join(rc, "return"))
    # the list of hashes as received
    lines = [l.rstrip("\n").split(None, 1) for l in open(os.path.join(rc, "return_files.sha256"), encoding="utf-8") if l.strip()]
    listed = {f.lstrip("*").strip(): h for h, f in lines}
    def strip(k):
        return k[len("gate_records/"):] if k.startswith("gate_records/") else k
    listed = {strip(k): h for k, h in listed.items()}
    bad = [k for k, p in rec.items() if listed.get(k) != sha_bytes(open(p, "rb").read())]
    res["return_files.sha256"] = {"lines": len(lines), "received_files": len(rec), "names_equal": sorted(listed) == sorted(rec), "hashes_differing": len(bad)}
    lines = [l.rstrip("\n").split(None, 1) for l in open(os.path.join(rc, "return_kept.sha256"), encoding="utf-8") if l.strip()]
    klisted = {strip(f.lstrip("*").strip()): h for h, f in lines}
    klisted = {(k[len("return/"):] if k.startswith("return/") else k): h for k, h in klisted.items()}
    badk = [k for k, p in kept.items() if klisted.get(k) != sha_bytes(open(p, "rb").read())]
    res["return_kept.sha256"] = {"lines": len(lines), "kept_files": len(kept), "names_equal": sorted(klisted) == sorted(kept), "hashes_differing": len(badk)}
    # the listing
    lst = open(os.path.join(rc, "return_listing.txt"), encoding="utf-8").read().splitlines()
    names_in_listing = sum(1 for m in mem if any(l.endswith(m.name) or l.endswith(m.name + "/") for l in lst))
    res["return_listing.txt"] = {"lines": len(lst), "archive_members": len(mem), "members_found_in_listing": names_in_listing}
    # differences
    kinds = {"identical": [], "line_ends_only": [], "line_ends_and_replacements": [], "replacements_only": [], "other": []}
    detail = {}
    for k in sorted(kept):
        if k not in rec:
            kinds["other"].append(k); detail[k] = "not in the received package"; continue
        rb, kb = open(rec[k], "rb").read(), open(kept[k], "rb").read()
        if rb == kb:
            kinds["identical"].append(k); continue
        crlf = rb.count(b"\r\n")
        r2 = rb.replace(b"\r\n", b"\n")
        if r2 == kb:
            kinds["line_ends_only"].append(k); detail[k] = {"crlf": crlf}; continue
        rl, kl = r2.split(b"\n"), kb.split(b"\n")
        info = {"crlf": crlf, "lines_differing": 0, "path_lines": 0, "name_lines": 0, "other_declared_lines": 0, "unexplained_lines": 0,
                "kept_has_cr": kb.count(b"\r")}
        if len(rl) != len(kl):
            info["line_count_differs"] = [len(rl), len(kl)]; kinds["other"].append(k); detail[k] = info; continue
        for x, y in zip(rl, kl):
            if x == y:
                continue
            info["lines_differing"] += 1
            t, used_p, used_n = x, False, False
            for p in sorted(a.path, key=len, reverse=True):
                pb = p.encode("utf-8")
                if pb in t:
                    t = t.replace(pb, b"W"); used_p = True
            for nme in a.name:
                nb = nme.encode("utf-8")
                if nb in t:
                    t = t.replace(nb, b"the operator"); used_n = True
            used_r = False
            for old, new in repl:
                if old in t:
                    t = t.replace(old, new); used_r = True
            if t == y:
                info["path_lines"] += used_p; info["name_lines"] += used_n; info["other_declared_lines"] += used_r
            else:
                info["unexplained_lines"] += 1
        key = "other" if info["unexplained_lines"] else ("line_ends_and_replacements" if crlf else "replacements_only")
        kinds[key].append(k); detail[k] = info
    res["differences"] = {k: len(v) for k, v in kinds.items()}
    res["files_with_replacements"] = {k: detail[k] for k in kinds["line_ends_and_replacements"] + kinds["replacements_only"]}
    res["files_other"] = {k: detail[k] for k in kinds["other"]}
    res["kept_files_with_cr"] = [k for k, p in kept.items() if not k.endswith(".npz") and not k.endswith(".pt") and b"\r" in open(p, "rb").read()]
    left = sorted(set(rec) - set(kept))
    res["left_out"] = {k: sha_bytes(open(rec[k], "rb").read()) for k in left}
    kr = json.load(open(os.path.join(rc, "keep_report.json"), encoding="utf-8"))
    res["keep_report_keys"] = {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in kr.items()}
    res["keep_report_raw_left_out"] = None
    for key, v in kr.items():
        if isinstance(v, (list, dict)) and len(v) == len(left):
            items = v if isinstance(v, list) else [dict(name=n, **(x if isinstance(x, dict) else {"sha256": x})) for n, x in v.items()]
            got = {}
            for it in items:
                if isinstance(it, dict):
                    nm = next((str(it[c]) for c in ("file", "name", "path") if c in it), None)
                    hh = next((str(it[c]) for c in it if "sha" in c.lower()), None)
                    got[strip(nm) if nm else None] = hh
            res["keep_report_raw_left_out"] = {"key": key, "names_equal": sorted(map(str, got)) == left,
                                               "hashes_equal": all(got.get(k) == h for k, h in res["left_out"].items())}
    # privacy
    targets = dict(("joint/records/c22/return/" + k, p) for k, p in kept.items())
    for extra in ("joint/docs/G-C2.2_verdict.md", "joint/audit/c22_keep.py", "joint/audit/c22_recompute.py", "joint/audit/c22_write_verdict.py", "joint/README.md"):
        targets[extra] = os.path.join(a.proposed, extra)
    for k, p in files_under(rc).items():
        if not k.startswith("return/"):
            targets["joint/records/c22/" + k] = p
    if a.changes:
        for line in open(a.changes, encoding="utf-8"):
            if line.strip():
                rel = line.rstrip("\n").split("\t")[-1]
                targets.setdefault(rel, os.path.join(a.proposed, rel))
    pats = {"windows_user_path": re.compile(rb"[A-Za-z]:\\\\?Users\\", re.I), "posix_home_path": re.compile(rb"/(home|Users|mnt/c/Users|root)/[A-Za-z0-9_.-]+"),
            "email": re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]+"), "non_ascii": re.compile(rb"[\x80-\xff]")}
    hits = {}
    for k, p in sorted(targets.items()):
        if p.endswith((".npz", ".pt")):
            continue
        b = open(p, "rb").read()
        for nm, pat in pats.items():
            n = len(pat.findall(b))
            if n:
                hits.setdefault(nm, {})[k] = n
        for i, w in enumerate(a.path):
            if w.encode() in b or w.replace("\\", "\\\\").encode() in b or w.lower().encode() in b.lower():
                hits.setdefault("PATH", {})[k] = hits.get("PATH", {}).get(k, 0) + 1
        for w in a.name:
            n = len(re.findall(re.escape(w.encode()), b, flags=re.I))
            if n:
                hits.setdefault("NAME", {})[k] = n
        for w in a.word:
            n = len(re.findall(re.escape(w.encode()), b, flags=re.I))
            if n:
                hits.setdefault("word:" + w, {})[k] = n
        # the private strings in encoded form: hexadecimal (either case) and base64 at the three alignments
        private = [("PATH", s) for s in a.path] + [("NAME", s) for s in a.name] + [("REPLACED", o.decode("utf-8")) for o, _ in repl]
        for kind, s in private:
            raw = s.encode("utf-8")
            forms = {raw.hex().encode(), raw.hex().upper().encode()}
            for shift in range(3):
                enc = base64.b64encode(b"x" * shift + raw)
                core = enc[(4 if shift else 0):len(enc) - 4]
                if len(core) >= 8:
                    forms.add(core)
            for part in re.split(rb"[\\/ ]", raw):
                if len(part) >= 5:
                    forms.add(part.hex().encode())
            n = sum(b.count(f) for f in forms)
            if n:
                hits.setdefault(kind + " in encoded form", {})[k] = hits.get(kind + " in encoded form", {}).get(k, 0) + n
    res["privacy_hits"] = hits
    res["files_searched"] = len([p for p in targets.values() if not p.endswith((".npz", ".pt"))])
    out = json.dumps(res, indent=1, ensure_ascii=True)
    if a.out:
        open(a.out, "w").write(out)
    print(out)


if __name__ == "__main__":
    main()
