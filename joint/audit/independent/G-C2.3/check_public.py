# Independent audit of gate G-C2.3: what the proposed commit would publish.
#
# What it checks, on every path that the proposed commit adds or changes (the list proposed_changes.txt):
#   1. the strings of a private JSON file (given as an argument; the values are loaded in code and never printed
#      or written): in plain text, without regard to case, with doubled backslashes or forward slashes, reversed,
#      in ROT13, in hexadecimal, percent-encoded, in base64 at its three alignments, in UTF-16, and as JSON \u
#      escapes; in .npz files also inside every member after decompression;
#   2. the names of accounts that the received package shows in the paths of its logs (taken from the received
#      files by this script, never printed), searched in the same forms;
#   3. paths of a home or temporary folder, e-mail addresses, and, when a list of names is given, names of
#      assistants or tool vendors (the list is not filed: a name of it may be one of the private strings);
#   4. carriage returns, bytes outside ASCII, em and en dashes, and a list of American spellings in the new
#      English documents;
#   5. paths that a .gitignore of the proposed tree would drop.
# Only counts, file names and neutral excerpts are printed.
#
# Usage: python -I check_public.py <proposed tree> <proposed_changes.txt> <private strings json>
#            <unpacked received package> <summary.json> [<names.txt>]
import base64
import codecs
import fnmatch
import io
import json
import os
import re
import sys
import zipfile


def forms(v: str):
    """Byte patterns under which a string could hide; (label, compiled pattern)."""
    out = []
    plain = {v, v.replace("\\", "\\\\"), v.replace("\\", "/"), v.replace(" ", "_"), v.replace(" ", "-"), v.replace(" ", "")}
    for p in plain:
        out.append(("plain", re.compile(re.escape(p.encode("utf-8")), re.I)))
        out.append(("utf-16", re.compile(re.escape(p.encode("utf-16-le")), re.I)))
    out.append(("reversed", re.compile(re.escape(v[::-1].encode("utf-8")), re.I)))
    out.append(("rot13", re.compile(re.escape(codecs.encode(v, "rot13").encode("utf-8")), re.I)))
    raw = v.encode("utf-8")
    out.append(("hex", re.compile(re.escape(raw.hex().encode()), re.I)))
    out.append(("percent", re.compile(re.escape("".join("%%%02X" % b for b in raw).encode()), re.I)))
    for variant in {v, v.lower(), v.upper(), v.capitalize()}:
        r = variant.encode("utf-8")
        for off in range(3):
            b = base64.b64encode(b"\0" * off + r).decode()
            core = b[(off * 4 + 2) // 3 + (1 if off else 0): len(b) - (4 if (off + len(r)) % 3 else 0)]
            if len(core) >= 6:
                out.append(("base64", re.compile(re.escape(core.encode()))))
    if any(ord(c) > 127 for c in v):
        out.append(("json escape", re.compile(re.escape(json.dumps(v)[1:-1].encode()), re.I)))
    return out


AMERICAN = r"\b(colou?r(?<!colour)\w*|behavior\w*|center(ed|s|ing)?|analyz\w+|model(ed|ing)\b|label(ed|ing)\b|" \
           r"cancel(ed|ing)\b|travel(ed|ing)\b|gray|defense|favor\w*|neighbor\w*|fiber\w*|artifact\w*|" \
           r"judgment|catalog\b|fulfill\b|skeptic\w*|program\b|license\b|practice[ds]?\b|" \
           r"\w+(?<![s])iz(e|ed|es|ing|ation|ations|er|ers)\b|\w+yz(e|ed|es|ing)\b)"
IZE_OK = {"size", "sized", "sizes", "resize", "resized", "prize", "seize", "seized", "capsize", "sizing"}


def main():
    tree, changes, private, received, outp = sys.argv[1:6]
    paths = [l.split("\t", 1)[1].strip() for l in open(changes, encoding="utf-8").read().splitlines() if l.strip()]
    secret = [v for v in json.load(open(private, encoding="utf-8")).values() if isinstance(v, str) and v]
    # The words of the folder patterns are put together from parts, so that this file does not itself hold the
    # literals that it, and the repository's own scans, search for.
    def word(*parts):
        return "".join(parts).encode()
    sep, slash = rb"(?:\\\\|\\|/)", b"/"            # a backslash, a doubled backslash or a slash; a slash
    accounts = word("Us", "ers")
    account = re.compile(rb"[A-Za-z]:" + sep + accounts + sep + rb"([^\\/\r\n\"]+)")
    users = set()
    for root, _, files in os.walk(received):
        for f in files:
            if f.endswith((".log", ".json", ".txt", ".py")):
                data = open(os.path.join(root, f), "rb").read()
                for m in account.finditer(data):
                    users.add(m.group(1).decode("utf-8", "replace"))
    pats = [(f"private string {i + 1}", lab, p) for i, v in enumerate(secret) for lab, p in forms(v)]
    pats += [(f"user name {i + 1} of a received path", lab, p) for i, v in enumerate(sorted(users)) for lab, p in forms(v)
             if len(v) >= 4]
    folders = [slash + word("ho", "me") + slash, slash + accounts + slash, slash + word("ro", "ot") + slash,
               slash + word("t", "mp") + slash, slash + word("v", "ar") + slash + word("fol", "ders") + slash,
               slash + word("m", "nt") + rb"/[a-z]/", word("App", "Data"), rb"\\" + word("Te", "mp") + rb"\\",
               b"%" + word("USER", "PROFILE") + b"%", b"~" + slash]
    home = re.compile(rb"([A-Za-z]:" + sep + rb"(?:" + accounts + rb"|" + word("Documents and ", "Settings") + rb")|"
                      + b"|".join(folders) + rb")", re.I)
    email = re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
    names = []
    if len(sys.argv) > 6:                   # optional: a file of names to look for, one a line; it is not filed
        names = [l.strip() for l in open(sys.argv[6], encoding="utf-8").read().splitlines() if l.strip()]
    vendor = re.compile(rb"\b(" + b"|".join(re.escape(n.encode("utf-8")) for n in names) + rb")\b", re.I) if names else None
    found = {"private": {}, "home": {}, "email": {}, "vendor": {}, "cr": [], "non_ascii": {}, "dash": {}, "american": {},
             "missing": [], "ignored": []}
    n_files = n_bytes = n_members = 0
    for rel in paths:
        p = os.path.join(tree, rel)
        if not os.path.isfile(p):
            found["missing"].append(rel)
            continue
        data = open(p, "rb").read()
        n_files += 1
        n_bytes += len(data)
        blobs = [("", data)]
        if rel.endswith((".npz", ".zip")):
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    for nm in z.namelist():
                        blobs.append((nm, z.read(nm)))
                        blobs.append((nm + " (name)", nm.encode()))
                        n_members += 1
            except zipfile.BadZipFile:
                pass
        blobs.append(("(path)", rel.encode()))
        for where, blob in blobs:
            for what, lab, pat in pats:
                n = len(pat.findall(blob))
                if n:
                    found["private"].setdefault(rel, []).append([what, lab, where, n])
        is_text = not rel.endswith((".npz", ".pt", ".tar", ".gz", ".png", ".pdf"))
        if is_text:
            for m in home.finditer(data):
                found["home"].setdefault(rel, {}).setdefault(m.group(1).decode("ascii", "replace"), 0)
                found["home"][rel][m.group(1).decode("ascii", "replace")] += 1
            for m in email.finditer(data):
                dom = m.group(0).split(b"@")[1].decode()
                found["email"].setdefault(rel, {}).setdefault("<...>@" + dom, 0)
                found["email"][rel]["<...>@" + dom] += 1
            for m in (vendor.finditer(data) if vendor else ()):
                w = m.group(1).decode().lower()
                found["vendor"].setdefault(w, {}).setdefault(rel, 0)
                found["vendor"][w][rel] += 1
            if b"\r" in data:
                found["cr"].append(rel)
            na = sum(1 for b in data if b > 127)
            if na:
                found["non_ascii"][rel] = na
            text = data.decode("utf-8", "replace")
            for ch, nm in ((chr(0x2014), "em dash"), (chr(0x2013), "en dash")):
                if ch in text:
                    found["dash"].setdefault(rel, {})[nm] = text.count(ch)
            if rel.endswith(".md"):
                for m in re.finditer(AMERICAN, text, re.I):
                    w = m.group(0).lower()
                    if w in IZE_OK:
                        continue
                    found["american"].setdefault(rel, {}).setdefault(w, 0)
                    found["american"][rel][w] += 1
    # 5. the .gitignore files of the proposed tree against the changed paths
    rules = []
    for root, _, files in os.walk(tree):
        if ".gitignore" in files:
            base = os.path.relpath(root, tree).replace(os.sep, "/")
            for line in open(os.path.join(root, ".gitignore"), encoding="utf-8").read().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    rules.append(("" if base == "." else base + "/", line))

    def ignored(rel):
        state = False
        for base, rule in rules:
            if not rel.startswith(base):
                continue
            sub = rel[len(base):]
            neg = rule.startswith("!")
            r = rule[1:] if neg else rule
            anchored = r.startswith("/") or ("/" in r.rstrip("/"))
            r2 = r.strip("/")
            parts = sub.split("/")
            hit = False
            if anchored:
                hit = fnmatch.fnmatch(sub, r2) or fnmatch.fnmatch(sub, r2 + "/*") or sub.startswith(r2 + "/")
            else:
                cands = parts[:-1] if r.endswith("/") else parts
                hit = any(fnmatch.fnmatch(c, r2) for c in cands)
            if hit:
                state = not neg
        return state

    found["ignored"] = [rel for rel in paths if ignored(rel)]
    found["gitignore_rules"] = [b + r for b, r in rules]
    found["counts"] = {"paths": len(paths), "files_read": n_files, "bytes": n_bytes, "npz_members": n_members,
                       "private_strings": len(secret), "user_names_from_received_paths": len(users), "patterns": len(pats)}
    json.dump(found, open(outp, "w", encoding="utf-8"), indent=1)
    print("searched:", found["counts"])
    print("private strings or user names found in:", {k: [[w, l, wh, n] for w, l, wh, n in v] for k, v in found["private"].items()} or "no file")
    print("home or temporary folder patterns:", found["home"] or "none")
    print("e-mail addresses:", found["email"] or "none")
    print("names of the list:", ("%d names searched; found %d of them" % (len(names), len(found["vendor"]))) if names else "no list given")
    for k, v in enumerate(found["vendor"].values()):       # the names themselves are not printed
        print("    name", k + 1, "of those found, in", sorted(v.items(), key=lambda kv: -kv[1])[:6])
    print("files with a carriage return:", len(found["cr"]), found["cr"][:5])
    print("text files with bytes outside ASCII:", found["non_ascii"] or "none")
    print("em or en dashes:", found["dash"] or "none")
    print("American spellings in .md files:", found["american"] or "none")
    print("changed paths missing from the tree:", found["missing"] or "none")
    print("changed paths that a .gitignore rule would drop:", found["ignored"] or "none")
    print(".gitignore rules:", found["gitignore_rules"])


if __name__ == "__main__":
    main()
