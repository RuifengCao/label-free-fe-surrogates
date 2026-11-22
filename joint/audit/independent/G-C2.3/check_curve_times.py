# Independent audit of gate G-C2.3, round 2: was a member of the author's first recomputation resumed part-way?
#
# What it checks. The step --curves of the author's recomputation writes one file a pair, in the order of its list,
# on one problem object for a member; if a member is taken up again, the pairs that are left start on a new object,
# from a zero element state. Each file records the seconds of its own computation. This script reads the per-pair
# files with their file times and, for every member and list (label-free arm read condensed; supervised arm read
# raw), puts the files in the order of the list (seed, then level) and compares the time between two files with
# the seconds that the later file records. Within a member that was computed in one piece, a file is written right
# after its computation, so the difference "time since the file before, less its own seconds" is small; a resumed
# member shows at least the time of building a new object and of evaluating its labels, a second process on the
# same member shows files out of order or written twice. It prints the distribution of that difference, the
# members with a difference above a limit, the files that are not in the order of the list, and how the members
# were spread over time (how many were in work at once). It also compares the files with the packed curves.json.
#
# Usage: python -I check_curve_times.py <folder of the per-pair files> <curves.json of the records> [<limit in s>]
import json
import os
import re
import sys


def main():
    folder, packed = sys.argv[1], sys.argv[2]
    limit = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    rows = {}
    for f in sorted(os.listdir(folder)):
        m = re.fullmatch(r"(.+)__(.+)_(condensed|raw)_l(\d)\.json", f)
        if not m:
            print("a file of another name:", f)
            continue
        p = os.path.join(folder, f)
        d = json.load(open(p, encoding="utf-8"))
        st = os.stat(p)
        rows[(m.group(1), m.group(2), m.group(3), int(m.group(4)))] = (st.st_mtime, float(d["seconds"]), d)
    print("per-pair files:", len(rows))
    packed_rows = json.load(open(packed, encoding="utf-8"))
    keyp = {(r["id"], r["run"], r["reading"], r["level"]): r for r in packed_rows}
    same = sum(1 for k, v in rows.items() if k in keyp and keyp[k] == v[2])
    print("packed rows:", len(packed_rows), "| per-pair files equal to their packed row:", same, "| files without a packed row:", len(set(rows) - set(keyp)))
    groups = {}
    for (iid, run, reading, l), v in rows.items():
        groups.setdefault((iid, run.rsplit("_s", 1)[0], reading), []).append((int(run.rsplit("_s", 1)[1]), l, v[0], v[1]))
    slack_all, over, disorder, spans = [], [], [], []
    first_gap = []
    for key in sorted(groups):
        g = sorted(groups[key])                               # the order of the list: seed, then level
        times = [x[2] for x in g]
        if times != sorted(times):
            disorder.append(key)
        for a, b in zip(g, g[1:]):
            slack = (b[2] - a[2]) - b[3]                      # time since the file before, less its own seconds
            slack_all.append(slack)
            if abs(slack) > limit:
                over.append((key, a[:2], b[:2], round(slack, 3)))
        spans.append((g[0][2] - g[0][3], g[-1][2], key, len(g)))
    s = sorted(slack_all)
    print("groups (member, arm, reading):", len(groups), "| sizes:", sorted({len(v) for v in groups.values()}))
    if s:
        print(f"time since the file before, less the file's own seconds, over {len(s)} pairs of neighbours: least {s[0]:.4f} s, median {s[len(s) // 2]:.4f} s, "
              f"most {s[-1]:.4f} s")
    print(f"neighbours with a difference above {limit} s in size:", len(over), over[:8])
    print("groups whose files are not in the order of the list:", len(disorder), disorder[:5])
    # how the groups lie in time: overlaps show how many were in work at once
    spans.sort()
    events = sorted([(a, 1) for a, _, _, _ in spans] + [(b, -1) for _, b, _, _ in spans])
    live = most = 0
    for _, e in events:
        live += e
        most = max(most, live)
    import time
    t0, t1 = min(a for a, _, _, _ in spans), max(b for _, b, _, _ in spans)
    print("first start (by the first file less its seconds):", time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t0)), "| last file:",
          time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t1)), "UTC | most groups in work at once:", most)
    # the gaps between the end of one group and the start of the next one on the same worker cannot be told
    # from the files alone; the largest pause in which no group was in work:
    idle, end = 0.0, spans[0][1]
    for a, b, _, _ in spans[1:]:
        if a > end:
            idle = max(idle, a - end)
        end = max(end, b)
    print(f"longest time in which no group was in work: {idle:.1f} s")
    short = [(k, n) for _, _, k, n in spans if n != 21]
    print("groups that do not hold 21 files:", short)


if __name__ == "__main__":
    main()
