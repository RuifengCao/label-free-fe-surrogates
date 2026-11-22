# Independent audit of gate G-C2.3: the kept copy of the return package and the deposit of its arrays.
#
# What it checks, with the auditor's own code:
#   1. the archive of the return package: its size and SHA-256 against the file that came with it;
#   2. return_files.sha256 of the proposed commit against the files as the auditor unpacked them (400 files);
#   3. the kept files in the proposed tree against the received ones: which are byte for byte equal, which differ
#      only by CR LF to LF, which differ otherwise and in how many places, and which are absent; the lists
#      return_kept.sha256 and keep_report.json against that;
#   4. the files that are in the kept list and not in the tree (the deposit), by kind;
#   5. the archive of the deposit: its size and SHA-256, each member's size and SHA-256 against deposit.json and
#      against the package as received;
#   6. the archive's listing kept in the tree against a listing that the auditor made (owner and group as numbers).
#
# Usage: python -I check_kept.py <archive c23_return.tar.gz> <its .sha256 file> <unpacked package (gate3_records)>
#            <records/c23 of the proposed tree> <deposit archive> <auditor's numeric listing> <summary.json>
import hashlib
import json
import os
import re
import sys
import tarfile


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    archive, shafile, rec, c23, deposit, listing, outp = sys.argv[1:8]
    out = {}
    out["archive"] = {"bytes": os.path.getsize(archive), "sha256": sha(archive),
                      "equals_file_beside_it": open(shafile).read().split()[0] == sha(archive)}
    print("1. archive:", out["archive"])
    files = {}
    for root, _, fs in os.walk(rec):
        for f in fs:
            p = os.path.join(root, f)
            files[os.path.relpath(p, rec).replace(os.sep, "/")] = p
    listed = dict((l.split("  ", 1)[1], l.split("  ", 1)[0]) for l in open(os.path.join(c23, "return_files.sha256")).read().splitlines())
    mine = {k: sha(p) for k, p in files.items()}
    out["received"] = {"files_unpacked": len(files), "listed": len(listed), "same_names": set(listed) == set(mine),
                       "different_hash": [k for k in listed if mine.get(k) != listed[k]]}
    print("2. return_files.sha256:", out["received"])
    kept_list = dict((l.split("  ", 1)[1], l.split("  ", 1)[0]) for l in open(os.path.join(c23, "return_kept.sha256")).read().splitlines())
    rep = json.load(open(os.path.join(c23, "keep_report.json")))
    in_tree = {}
    for root, _, fs in os.walk(os.path.join(c23, "return")):
        for f in fs:
            p = os.path.join(root, f)
            in_tree[os.path.relpath(p, os.path.join(c23, "return")).replace(os.sep, "/")] = p
    kinds = {"equal": [], "crlf_only": [], "crlf_and_other": [], "other_only": []}
    replaced = {}
    not_listed, wrong_hash = [], []
    for k, p in in_tree.items():
        if k not in kept_list:
            not_listed.append(k)
            continue
        if sha(p) != kept_list[k]:
            wrong_hash.append(k)
        a, b = open(files[k], "rb").read(), open(p, "rb").read()
        if a == b:
            kinds["equal"].append(k)
            continue
        a2 = a.replace(b"\r\n", b"\n")
        if a2 == b:
            kinds["crlf_only"].append(k)
            continue
        # what else differs: split both at the kept copy's mark W and compare the fixed parts
        parts = b.split(b"W")
        pattern = b"(.{1,200}?)".join(re.escape(x) for x in parts)
        ok = False
        for cand in ((a2, "crlf_and_other"), (a, "other_only")):
            m = None
            if len(parts) <= 400:
                try:
                    m = re.fullmatch(pattern, cand[0], re.S)
                except re.error:
                    m = None
            if m:
                kinds[cand[1] if cand[0] is a2 and a2 != a else "other_only"].append(k)
                # count the places where a longer text stands in the received file for a W of the kept one
                replaced[k] = sum(1 for g in m.groups() if g != b"W")
                ok = True
                break
        if not ok:
            kinds.setdefault("unexplained", []).append(k)
    absent = sorted(set(kept_list) - set(in_tree))
    left_out = sorted(set(listed) - set(kept_list))
    by_kind = {}
    for k in absent:
        key = "labels" if k.startswith("labels/") else ("predictions of the six runs" if re.fullmatch(r"run_files/[^/]+/preds(_condensed|_base)?\.npz", k) else "other")
        by_kind[key] = by_kind.get(key, 0) + 1
    out["kept"] = {"in_tree": len(in_tree), "kept_list": len(kept_list), "in_tree_not_in_list": not_listed,
                   "in_tree_with_other_hash_than_list": wrong_hash,
                   "equal_to_received": len(kinds["equal"]), "crlf_only": len(kinds["crlf_only"]),
                   "crlf_and_replacement": len(kinds["crlf_and_other"]), "replacement_only": len(kinds["other_only"]),
                   "unexplained": kinds.get("unexplained", []),
                   "files_with_replacements": {k: v for k, v in sorted(replaced.items())},
                   "in_list_not_in_tree": len(absent), "of_them": by_kind,
                   "received_not_kept": left_out,
                   "received_not_kept_hashes_in_report": all(any(x["file"] == k and x["sha256"] == mine[k] for x in rep["left_out"]) for k in left_out),
                   "report": {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in rep.items()},
                   "report_crlf_equals_mine": sorted(rep["line_ends_converted"]) == sorted(
                       [k for k in kept_list if k in files and b"\r\n" in open(files[k], "rb").read()
                        and os.path.splitext(k)[1] in (".log", ".json", ".py", ".txt")]),
                   "report_replaced_equals_mine": {k: v for k, v in rep["folder_replaced"].items()} == replaced,
                   "kept_list_unchanged_count": sum(1 for k in kept_list if kept_list[k] == listed[k])}
    print("3. kept copy:", out["kept"])
    # deposit
    dj = json.load(open(os.path.join(c23, "deposit.json")))
    out["deposit_json_keys"] = sorted(dj)
    members = {}
    with tarfile.open(deposit) as t:
        for m in t:
            if m.isfile():
                data = t.extractfile(m).read()
                members[m.name] = (len(data), hashlib.sha256(data).hexdigest(), m.uname, m.gname, m.uid, m.gid, m.mtime, oct(m.mode))
    out["deposit"] = {"bytes": os.path.getsize(deposit), "sha256": sha(deposit), "members": len(members),
                      "member_bytes": sum(v[0] for v in members.values()),
                      "owner_names": sorted({(v[2], v[3]) for v in members.values()}),
                      "owner_ids": sorted({(v[4], v[5]) for v in members.values()}),
                      "mtimes": sorted({v[6] for v in members.values()})[:3], "modes": sorted({v[7] for v in members.values()}),
                      "names_head": sorted(members)[:2]}
    print("5. deposit archive:", out["deposit"])
    print("   deposit.json keys:", out["deposit_json_keys"], {k: v for k, v in dj.items() if not isinstance(v, (list, dict))})
    json.dump(out, open(outp, "w", encoding="utf-8"), indent=1, default=str)
    # members against deposit.json and against the package
    flist = dj.get("files") or dj.get("members") or []
    if isinstance(flist, dict):
        flist = [dict(v, file=k) if isinstance(v, dict) else {"file": k, "sha256": v} for k, v in flist.items()]
    by_name = {}
    for f in flist:
        nm = f.get("file") or f.get("name") or f.get("path")
        by_name[nm] = f
    def strip(n):
        for pre in ("gate3_records/", "return/", "c23_arrays/", "./"):
            if n.startswith(pre):
                n = n[len(pre):]
        return n
    mem2 = {strip(k): v for k, v in members.items()}
    dj2 = {strip(k): v for k, v in by_name.items()}
    bad_json = [k for k in mem2 if k not in dj2 or dj2[k].get("sha256") != mem2[k][1] or (dj2[k].get("bytes", mem2[k][0]) != mem2[k][0])]
    bad_pkg = [k for k in mem2 if listed.get(k) != mem2[k][1]]
    out["deposit_members"] = {"in_json": len(dj2), "not_as_in_json": bad_json[:5], "n_not_as_in_json": len(bad_json),
                              "not_as_in_package": bad_pkg[:5], "n_not_as_in_package": len(bad_pkg),
                              "equal_to_absent_set": sorted(mem2) == absent}
    print("   members:", out["deposit_members"])
    # listing
    kept_listing = open(os.path.join(c23, "return_listing.txt")).read()
    my_listing = open(listing).read()
    out["listing"] = {"equal_to_auditors": kept_listing == my_listing, "lines": len(kept_listing.splitlines()),
                      "owner_fields": sorted({l.split()[1] for l in kept_listing.splitlines()})}
    print("6. listing:", out["listing"])
    json.dump(out, open(outp, "w", encoding="utf-8"), indent=1, default=str)


if __name__ == "__main__":
    main()
