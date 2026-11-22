"""Write the job files of gate G-C2.3 into the queue of its host, in the order of their names. Outside the stamp;
the job files and this script go into the return package (RUNBOOK_C23.md, section 9).

    python3 make_jobs_c23.py QUEUE P HASH    # before the stamp, from the draft tree pre3/: the host check, the
                                             # check of the state files' predictions, a pilot of the training
                                             # labels on members of a seen seed, and three timing probes
    python3 make_jobs_c23.py QUEUE A HASH    # 0e host check from the stamped tree and section 1, each with its guard
    python3 make_jobs_c23.py QUEUE B HASH    # sections 2 to 5 (part 1); only after the operator has checked A's output
    python3 make_jobs_c23.py QUEUE C HASH    # sections 6 to 8 (part 2); refused unless part 1's verdict ended with 0
    python3 make_jobs_c23.py QUEUE BC HASH   # B and C in one go, for a run that nobody watches: every stage has a
                                             # guard, and the verdict of part 1 ends with a code other than 0 unless
                                             # the identity check is in order
    python3 make_jobs_c23.py QUEUE R HASH    # after predictions of a label-free state that are not finite, which
                                             # is a final stop (runbook, section 4): the three predictions again,
                                             # the evaluation and the verdict, without guards, so that the INVALID
                                             # verdict is written

QUEUE is the queue's folder on the host. HASH is the configuration hash of the stamp (the first line of
write-config). Add --dry to print the jobs only. Add --from NAME to write only the jobs of the set from NAME on: for
a set that a guard stopped for a reason of the host, after the owner has agreed and the operator has moved the job
and done files of those jobs out of the queue (RUNBOOK_C23.md, "After a stop"). A guard's name must sort after every
continuation of its stage and must not begin with the stage's name and "_".
"""
import json
import pathlib
import sys
import time

M = "gate3/joint/c23/__main__.py"
FAMILY = "c23"


def job(name, args, note, script=M):
    return name, {"script": script, "args": args, "note": note}


def guard(stage, me):
    assert not me.startswith(stage + "_") and me > stage + "_zzzz", (stage, me)
    return me, {"script": "tools/guard.py", "args": [stage, FAMILY, me], "note": f"G-C2.3: guard after {stage}"}


def label(n, split, section):
    return job(f"{n}_c23_label_{split}", ["label", "--data", "gate3_data", "--split", split, "--workers", "16"],
               f"G-C2.3 runbook {section}: labels of the set {split}")


def sets(H):
    run = ["--data", "gate3_data", "--runs", "gate3_runs"]

    def predict(n, seed):
        return job(f"{n}_c23_predict_s{seed}",
                   ["predict-label-free", *run, "--seed", str(seed), "--state",
                    f"gate_runs/label_free_s{seed}/state.pt", "--repo", "gate3", "--config-sha", H],
                   f"G-C2.3 runbook 4: predictions of the label-free state, seed {seed}")

    def train(n, seed):
        return job(f"{n}_c23_train_s{seed}", ["train", *run, "--seed", str(seed), "--repo", "gate3",
                                              "--config-sha", H],
                   f"G-C2.3 runbook 7: supervised training, seed {seed}")

    def evaluate(n, arm, section):
        return job(f"{n}_c23_evaluate_{arm}", ["evaluate", *run, "--config-sha", H, "--arm", arm, "--workers", "16"],
                   f"G-C2.3 runbook {section}: evaluation of the arm {arm}")

    pre = "pre3/joint/probes"
    out = {
        # no guard in this set: the jobs after the host check do not depend on it, and nothing follows them
        "P": [
            job("79_c23pre_smoke", ["--repo", "pre3", "--device", "cuda", "--workers", "4", "--out",
                                    "pre3_records/smoke"],
                "G-C2.3 before the stamp: the host check from the draft tree", script="pre3/joint/c23/smoke.py"),
            job("80_c23pre_repredict", ["--repo", "pre3", "--data", "gate_data", "--runs", "gate_runs", "--out",
                                        "pre3_records/repredict"],
                "G-C2.3 before the stamp: predictions from G-C2.2's state files against G-C2.2's prediction files "
                "(reads G-C2.2's folders, writes into the new folder only)",
                script=f"{pre}/c23_precheck/repredict.py"),
            job("81_c23pre_pilot_labels", ["--out", "pre3_records/pilot_labels", "--members", "32", "--workers",
                                           "16", "--seed", "101"],
                "G-C2.3 before the stamp: the eight label levels on 32 members of a family seed used before "
                "G-C2.1's stamp, on the gate's mesh (draws nothing of the gate)",
                script=f"{pre}/c23_precheck/pilot_labels.py"),
            job("82_c23pre_step_cost", ["--repo", "pre3", "--data", "gate_data", "--out",
                                        "pre3_records/step_cost.json"],
                "probe: seconds per training step, energy and supervised loss (reads G-C2.2's exports)",
                script=f"{pre}/c2_timing/step_cost.py"),
            job("83_c23pre_time_curve", ["--repo", "pre3", "--data", "gate_data", "--state",
                                         "gate_runs/label_free_s5/state.pt", "--out", "pre3_records/time_curve.json"],
                "probe: the surrogate's curve against the reference solve (reads G-C2.2's exports and state)",
                script=f"{pre}/c2_timing/time_curve.py"),
            job("84_c23pre_f2_cost", ["--out", "pre3_records/f2_energy_cost.json", "--device", "cuda"],
                "probe: the training energy of one CHS splice instance", script=f"{pre}/f2_cost/energy_cost.py"),
        ],
        "A": [
            job("85_c23_smoke", ["--repo", "gate3", "--device", "cuda", "--workers", "4", "--out",
                                 "gate3_records/smoke"],
                "G-C2.3 runbook 0e: the host check from the stamped tree", script="gate3/joint/c23/smoke.py"),
            guard("85_c23_smoke", "85z_c23_guard"),
            job("86_c23_config", ["write-config", "--out", "gate3_records/c23_config.json", "--repo", "gate3",
                                  "--config-sha", H],
                "G-C2.3 runbook 1: configuration"),
            guard("86_c23_config", "86z_c23_guard"),
        ],
        "B": [
            job("87_c23_generate", ["generate", "--data", "gate3_data", "--config-sha", H],
                "G-C2.3 runbook 2: generation"),
            guard("87_c23_generate", "87z_c23_guard"),
            label("88a", "third", 3), label("88b", "eval", 3), label("88c", "tested", 3),
            job("88d_c23_check_held_out", ["check-labels", "--data", "gate3_data", "--splits", "third", "eval",
                                           "tested"], "G-C2.3 runbook 3: the check of the held-out labels"),
            guard("88d_c23_check_held_out", "88z_c23_guard"),
            predict(89, 5), guard("89_c23_predict_s5", "89z_c23_guard"),
            predict(90, 6), guard("90_c23_predict_s6", "90z_c23_guard"),
            predict(91, 7), guard("91_c23_predict_s7", "91z_c23_guard"),
            evaluate(92, "label_free", 5), guard("92_c23_evaluate_label_free", "92z_c23_guard"),
            job("93_c23_verdict_part1", ["verdict", *run, "--config-sha", H], "G-C2.3 runbook 5: verdict of part 1"),
            guard("93_c23_verdict_part1", "93z_c23_guard"),
        ],
        "C": [
            label("94a", "train", 6),
            job("94b_c23_check_all", ["check-labels", "--data", "gate3_data"],
                "G-C2.3 runbook 6: the check of all labels"),
            guard("94b_c23_check_all", "94z_c23_guard"),
            train(95, 5), guard("95_c23_train_s5", "95z_c23_guard"),
            train(96, 6), guard("96_c23_train_s6", "96z_c23_guard"),
            train(97, 7), guard("97_c23_train_s7", "97z_c23_guard"),
            evaluate(98, "supervised_512", 8), guard("98_c23_evaluate_supervised_512", "98z_c23_guard"),
            job("99_c23_verdict_final", ["verdict", *run, "--config-sha", H, "--final"],
                "G-C2.3 runbook 8: the final verdict"),
            guard("99_c23_verdict_final", "99z_c23_guard"),
        ],
    }
    out["BC"] = out["B"] + out["C"]
    # the record of an INVALID end: no guard, new names that sort after part 1's jobs and before part 2's
    out["R"] = [job(f"93r{k}_c23_record_predict_s{seed}", predict(0, seed)[1]["args"],
                    f"G-C2.3 runbook 4: the record of an INVALID end, predictions of seed {seed}")
                for k, seed in enumerate((5, 6, 7), start=1)]
    out["R"] += [job("93r4_c23_record_evaluate", evaluate(0, "label_free", 5)[1]["args"],
                     "G-C2.3 runbook 4: the record of an INVALID end, evaluation of the label-free arm"),
                 job("93r5_c23_record_verdict", ["verdict", *run, "--config-sha", H],
                     "G-C2.3 runbook 4: the record of an INVALID end, the verdict")]
    return out


def main() -> int:
    Q, which, H = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    assert len(H) == 64 and all(c in "0123456789abcdef" for c in H), "HASH is not a SHA-256"
    jobs = sets(H)[which]
    names = [n for n, _ in jobs]
    assert names == sorted(names) and len(set(names)) == len(names), names
    if "--from" in sys.argv:                         # a set that was stopped: the jobs from the named one on
        k = sys.argv.index("--from") + 1
        start = sys.argv[k] if k < len(sys.argv) else ""
        if start not in names or jobs[names.index(start)][1]["script"] == "tools/guard.py":
            print(f"refused: --from needs the name of a job of set {which} that is not a guard")
            return 1
        jobs = [(n, j) for n, j in jobs if n >= start]
        names = [n for n, _ in jobs]
    assert all(FAMILY in n for n in names)
    for a in names:                                  # no job may be taken for a continuation of another stage
        assert not any(b != a and b.startswith(a + "_") for b in names), a
    if "--dry" in sys.argv:
        for n, j in jobs:
            print(n, json.dumps(j))
        return 0
    if not Q.is_dir():
        print(f"refused: {Q} is not a folder")
        return 1
    if which != "R" and names[0] > "93z_c23_guard":   # part 2 is queued without part 1 only after part 1's verdict
        d = Q / "93z_c23_guard.done.json"
        ended = json.loads(d.read_text(encoding="utf-8")) if d.exists() else {}
        if ended.get("returncode") != 0 or ended.get("cancelled") or ended.get("killed"):
            print("refused: the guard after the verdict of part 1 has not ended with exit code 0")
            return 1
    for n in names:
        for suffix in (".job.json", ".done.json"):
            if (Q / (n + suffix)).exists():
                print(f"refused: {n}{suffix} exists already")
                return 1
    for n, j in jobs:
        tmp = Q / f"{n}.job.json.tmp"
        tmp.write_text(json.dumps(j, indent=1), encoding="utf-8")
        tmp.rename(Q / f"{n}.job.json")
        print("queued", n, flush=True)
        time.sleep(0.2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
