# Independent audit of gate G-C2.3: the condensed fields from their parts.
#
# What it checks. The condensed reading of a field is keep(z_0 + a (z - z_0)): z the raw field, z_0 the base
# field, a the amplitude kept in condense.json, keep the contact unknowns set to at least zero. For every run and
# every evaluated member this script forms that field in float32 from the returned raw fields, base fields and
# amplitudes, with numpy alone, and compares it with the returned condensed field. It also counts the amplitudes
# at the two limits. The contact unknowns are read from the instance files.
#
# Usage: python -I check_condensed.py <unpacked return package (gate3_records)> <instances folder> <summary.json>
import json
import os
import sys

import numpy as np


def main():
    R, inst, outp = sys.argv[1:4]
    out = {}
    total = equal = 0
    worst = 0.0
    for arm in ("label_free", "supervised_512"):
        for seed in (5, 6, 7):
            run = f"{arm}_s{seed}"
            d = os.path.join(R, "run_files", run)
            raw, cond, base = (np.load(os.path.join(d, f)) for f in ("preds.npz", "preds_condensed.npz", "preds_base.npz"))
            c = json.load(open(os.path.join(d, "condense.json"), encoding="utf-8"))
            n_eq = n = at_lo = at_hi = 0
            for m in raw.files:
                with np.load(os.path.join(inst, m + ".npz"), allow_pickle=False) as z:
                    cidx = np.asarray(z["cidx"], int)
                a = np.asarray(c["members"][m]["a"], dtype=np.float32)
                z0, zr = base[m].astype(np.float32), raw[m].astype(np.float32)
                zc = z0[None, :] + a[:, None] * (zr - z0[None, :])
                zc[:, cidx] = np.maximum(zc[:, cidx], np.float32(0.0))
                n += 1
                same = np.array_equal(zc, cond[m])
                n_eq += same
                if not same:
                    worst = max(worst, float(np.abs(zc - cond[m]).max()))
                at_lo += int((a <= np.float32(c["reading"]["a_min"])).sum())
                at_hi += int((a >= np.float32(c["reading"]["a_max"])).sum())
            out[run] = {"members": n, "bit_identical": int(n_eq), "amplitudes_at_lower_limit": at_lo, "amplitudes_at_upper_limit": at_hi}
            total += n
            equal += n_eq
            print(run, out[run])
    out["total"] = {"arrays": total, "bit_identical": int(equal), "largest_difference_otherwise": worst}
    print(out["total"])
    json.dump(out, open(outp, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
