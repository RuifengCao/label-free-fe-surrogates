"""Probe, 22 Nov 2026 (after the second round of the independent audit of G-C2.3): from which label does the exact
solve of a pair start? c2/evaluate.py (metrics) starts it from the label nearest to the pair's predicted end
displacement. This script reads the returned labels and predictions and counts, for each arm and reading and at each
level, the pairs whose nearest label is not that of their own level. It solves nothing.
  python -I -B probes/c23_reference_state/nearest_label.py RECORDS
RECORDS is the kept copy of G-C2.3's return package whole, with the label and prediction files of its deposit."""
import json
import pathlib
import sys

import numpy as np

LEVELS = (0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0)
FILES = {"condensed": "preds_condensed.npz", "raw": "preds.npz"}
rec = pathlib.Path(sys.argv[1])
man = json.loads((rec / "manifest.json").read_text())
ids = [r["id"] for r in man["instances"] if r["split"] in ("third", "eval", "tested")]
e_ref = {}
for i in ids:
    with np.load(rec / "labels" / f"{i}.npz") as z:
        e_ref[i] = z["e"].astype(float)


def nearest(run, reading, members):
    out = {}
    with np.load(rec / "run_files" / run / FILES[reading]) as z:
        for i in members:
            e = z[i][:, -1].astype(float)                    # the end displacement is the last unknown
            out[i] = [int(k) for k in np.argmin(np.abs(e_ref[i][None, :] - e[:, None]), axis=1)]
    return out


print(f"{len(ids)} evaluated members, three runs an arm: {3 * len(ids)} pairs at each level")
print("pairs whose nearest label is not that of their own level, at 0.5, 1, 2, 3, 4, 6 and 8 mm:")
at_first = 0
for arm in ("label_free", "supervised_512"):
    for reading in FILES:
        other = [0] * len(LEVELS)
        for seed in "567":
            for i, near in nearest(f"{arm}_s{seed}", reading, ids).items():
                for l, k in enumerate(near):
                    other[l] += int(k != l)
                at_first += int(near[0] == 0)
        print(f"  {arm}, {reading}: " + ", ".join(str(n) for n in other))
print(f"pairs at 0.5 mm whose nearest label is that of 0.5 mm, both arms and both readings: {at_first} of {4 * 3 * len(ids)}")
for i, run, reading in (("eval_0063", "supervised_512_s6", "condensed"), ("eval_0063", "supervised_512_s6", "raw"),
                        ("third_0034", "label_free_s6", "raw"), ("third_0034", "label_free_s7", "condensed")):
    near = nearest(run, reading, [i])[i]
    print(f"{i}, {run}, {reading}: the level of the nearest label for the pairs at the seven levels: "
          + ", ".join(f"{LEVELS[k]:g}" for k in near))
