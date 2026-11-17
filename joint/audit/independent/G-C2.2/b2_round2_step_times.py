"""Audit of gate G-C2.2, round 2: the slow stretches of the three training runs (deviation 3 of the corrected
verdict document), and how well the records fix their clock times.

From the three history.json and attempts.log of the return package:
  - the epochs that took at least --slow seconds a step (default 0.6), as stretches of consecutive epochs, with
    their number and their hours; the number of epochs between --idle (default 0.38) and --slow;
  - for each run, the time between its start line and its end line that the epoch times do not cover (the set-up
    before the first epoch, the checkpoints, the predictions after the last epoch);
  - for the end of chosen epochs, two clock times: counted forward from the run's start line with no time for the
    set-up (the earliest possible), and counted back from the run's end line with no time for the predictions (the
    latest possible). The true time lies between the two; they differ by the uncovered time of the run.
    With --setup and --predict (seconds, defaults 100 and 249: the values that the two parts of seed 5 show) the
    two counts are also given with these allowances.

Usage:  python -I b2_round2_step_times.py RECORDS [--slow 0.6] [--idle 0.38] [--setup 100] [--predict 249] [--out OUT.json]
"""
import argparse
import datetime as dt
import json
import os


def stamp(line):
    return dt.datetime.fromisoformat(line.split()[0]).replace(tzinfo=None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records"); ap.add_argument("--slow", type=float, default=0.6); ap.add_argument("--idle", type=float, default=0.38)
    ap.add_argument("--setup", type=float, default=100.0); ap.add_argument("--predict", type=float, default=249.0); ap.add_argument("--out")
    a = ap.parse_args()
    res = {"runs": {}}
    n_slow = n_mid = n_fast = 0
    for seed in (5, 6, 7):
        run = os.path.join(a.records, "run_files", f"label_free_s{seed}")
        h = json.load(open(os.path.join(run, "history.json")))
        ep = h["epoch_seconds"]
        steps = h["total_steps"] // len(ep)
        per = [x / steps for x in ep]
        att = [l for l in open(os.path.join(run, "attempts.log")).read().replace("\r", "").split("\n") if l.strip()]
        slow = [p >= a.slow for p in per]
        stretches, k = [], 0
        while k < len(per):
            if slow[k]:
                j = k
                while j + 1 < len(per) and slow[j + 1]:
                    j += 1
                stretches.append({"epochs": [k + 1, j + 1], "number": j - k + 1, "hours": sum(ep[k:j + 1]) / 3600,
                                  "seconds_a_step_min_max": [min(per[k:j + 1]), max(per[k:j + 1])]})
                k = j + 1
            else:
                k += 1
        n_slow += sum(slow); n_mid += sum(a.idle <= p < a.slow for p in per); n_fast += sum(p < a.idle for p in per)
        r = {"stretches": stretches, "slow_epochs": sum(slow), "slow_hours": sum(x for x, s in zip(ep, slow) if s) / 3600, "attempts": att}
        # the parts of the run between a start (or resume) line and the next end of work
        if seed == 5:
            parts = [("first part: start line to the stop by the pause (the queue's record)", stamp(att[0]), None, 0, 75),
                     ("second part: resume line to end line", stamp(att[2]), stamp(att[3]), 75, 200)]
        else:
            parts = [("start line to end line", stamp(att[0]), stamp(att[-1]), 0, 200)]
        r["parts"] = []
        for name, t0, t1, e0, e1 in parts:
            covered = sum(ep[e0:e1])
            p = {"part": name, "epochs": [e0 + 1, e1], "seconds_of_the_epochs": covered}
            if t1 is not None:
                p["seconds_from_line_to_line"] = (t1 - t0).total_seconds()
                p["seconds_not_covered_by_epochs"] = (t1 - t0).total_seconds() - covered
            r["parts"].append(p)
            marks = sorted({s["epochs"][0] - 1 for s in stretches if e0 < s["epochs"][0] - 1 <= e1} | {s["epochs"][1] for s in stretches if e0 < s["epochs"][1] <= e1})
            for m in marks:
                fwd = t0 + dt.timedelta(seconds=sum(ep[e0:m]))
                row = {"end_of_epoch": m, "counted_from_the_start_line": fwd.strftime("%d %H:%M:%S"),
                       "with_setup": (fwd + dt.timedelta(seconds=a.setup)).strftime("%d %H:%M:%S")}
                if t1 is not None:
                    back = t1 - dt.timedelta(seconds=sum(ep[m:e1]))
                    row.update(counted_back_from_the_end_line=back.strftime("%d %H:%M:%S"),
                               with_predictions=(back - dt.timedelta(seconds=a.predict)).strftime("%d %H:%M:%S"))
                p.setdefault("clock", []).append(row)
        res["runs"][seed] = r
    res["epochs_at_or_above_slow"] = n_slow; res["epochs_between_idle_and_slow"] = n_mid; res["epochs_below_idle"] = n_fast
    if a.out:
        open(a.out, "w").write(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
