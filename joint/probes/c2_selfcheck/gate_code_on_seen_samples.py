#!/usr/bin/env python3
"""The self-check code of gate G-C2.3 on the two samples that were seen before its stamp.

c23.evaluate.self_check is given the predictions of G-C2.2's three runs on its fresh sample ("eval") and on G-C2.1's
held-out sample ("former"): the force of each prediction is read from the predicted field as c23.evaluate reads it,
F = 4 k_s (D - e), and the judged errors are taken from G-C2.2's verdict record, so no exact solve is made. The
output must agree with the exploratory reading of 18 November 2026 (records/selfcheck_indicators.txt and
records/spread_details.txt), which rebuilt the forces from the recorded relative errors. Nothing of G-C2.3 is
drawn: both samples have seeds used before, and the instances are exported under G-C2.2's configuration.

    python3 -I gate_code_on_seen_samples.py RETURN INST

RETURN  G-C2.2's return package with its label and prediction files (audit/c22_deposit.py restore)
INST    a folder for the exports of the 128 members, made here (a few minutes; kept if they exist)
"""
import json
import sys
from pathlib import Path

import numpy as np

JOINT = Path(__file__).resolve().parents[2]


def main(argv=None):
    here = Path(__file__).resolve().parent                      # the script's own folder must not shadow modules
    sys.path[:] = [p for p in sys.path if not p or Path(p).resolve() != here]
    sys.path.insert(0, str(JOINT))
    ret, inst = (Path(a) for a in (argv or sys.argv[1:])[:2])
    from c2.data import load_export
    from c2.instance import ExportedProblem
    from c22 import data as data22
    from c22.config import config as config22, sha256
    from c23.config import SPREAD_THRESHOLD
    from c23.evaluate import self_check

    cfg = config22()
    assert json.loads((ret / "manifest.json").read_text())["config_sha256"] == sha256(cfg)
    data22.generate(cfg, inst, splits=("eval", "former"))
    man = json.loads((inst / "manifest.json").read_text())
    v = json.loads((ret / "verdict.json").read_text())
    seeds = ("5", "6", "7")
    out = {"threshold": SPREAD_THRESHOLD}
    for split in ("former", "eval"):
        ids = sorted(r["id"] for r in man["instances"] if r["split"] == split)
        rows = {s: {} for s in seeds}
        worst = 0.0
        for s in seeds:
            rec = v["readings"]["condensed"][s][f"{split}_rows"]
            with np.load(ret / "run_files" / f"label_free_s{s}" / "preds_condensed.npz") as z:
                for m in ids:
                    ex, _ = load_export(inst / "inst" / f"{m}.npz")
                    P = ExportedProblem(ex)
                    with np.load(ret / "labels" / f"{m}.npz") as lab:
                        D, F_ref = lab["D"], lab["F"]
                    rows[s][m] = []
                    for lv in range(D.size):
                        e = float(np.asarray(z[m][lv], dtype=np.float64)[P.e_idx])
                        F = 4.0 * P.k_s * (float(D[lv]) - e)
                        worst = max(worst, abs(F / float(F_ref[lv]) - 1 - rec[m][lv]["F_err"]))
                        rows[s][m].append({"F": F, "abs_curve_err": rec[m][lv]["abs_curve_err"]})
        r = self_check({"threshold": SPREAD_THRESHOLD}, rows, ids)
        spread = np.array([r["by_member"][m]["spread"] for m in ids]).ravel()
        out[split] = {k: r[k] for k in r if k not in ("by_member", "threshold")}
        out[split]["upper_quartile_of_the_spread"] = float(np.quantile(spread, 0.75))
        out[split]["largest_difference_of_the_force_from_the_recorded_force_error"] = worst
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
