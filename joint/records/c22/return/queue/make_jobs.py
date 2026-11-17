"""Write the job files of gate G-C2.2 into the laptop's queue, in the order of their names (run in the laptop's
Linux shell that mounts W). Outside the stamp; the job files go into the return package (RUNBOOK_C22.md, section 6).

    python3 make_jobs.py A        # 0d host check and section 1 (configuration), each with its guard
    python3 make_jobs.py B        # sections 2 to 5 with their guards; only after the operator has checked A's output

A guard's name must sort after every continuation of its stage and must not begin with the stage's name and "_".
"""
import json
import pathlib
import sys
import time

Q = pathlib.Path.home() / "W/queue"
H = "ef5376a4d6c3cc98d7888121439c8d959ee817d332958dd6b1141b25e78734bb"
M = "gate/joint/c22/__main__.py"


def job(name, args, note, script=M):
    return name, {"script": script, "args": args, "note": note}


def guard(stage, me):
    assert not me.startswith(stage + "_") and me > stage + "_zzzz", (stage, me)
    return me, {"script": "tools/guard.py", "args": [stage, "c22", me], "note": f"G-C2.2: guard after {stage}"}


def train(n, seed):
    return job(f"{n}_c22_train_s{seed}", ["train", "--data", "gate_data", "--runs", "gate_runs", "--seed", str(seed),
                                          "--repo", "gate", "--config-sha", H],
               f"G-C2.2 runbook 4: training, seed {seed}")


def label(n, split):
    return job(f"{n}_c22_label_{split}", ["label", "--data", "gate_data", "--split", split, "--workers", "16"],
               f"G-C2.2 runbook 3: labels of the set {split}")


SETS = {
    "A": [
        job("70_c22_smoke", ["--repo", "gate", "--device", "cuda", "--workers", "4", "--out", "gate_records/smoke"],
            "G-C2.2 runbook 0d: the host check from the stamped tree", script="gate/joint/c22/smoke.py"),
        guard("70_c22_smoke", "70z_c22_guard"),
        job("71_c22_config", ["write-config", "--out", "gate_records/c22_config.json", "--repo", "gate"],
            "G-C2.2 runbook 1: configuration"),
        guard("71_c22_config", "71z_c22_guard"),
    ],
    "B": [
        job("72_c22_generate", ["generate", "--data", "gate_data"], "G-C2.2 runbook 2: generation"),
        guard("72_c22_generate", "72z_c22_guard"),
        label("73a", "eval"), label("73b", "former"), label("73c", "tested"),
        job("73d_c22_check_labels", ["check-labels", "--data", "gate_data"], "G-C2.2 runbook 3: the check of the labels"),
        guard("73d_c22_check_labels", "73z_c22_guard"),
        train(74, 5), guard("74_c22_train_s5", "74z_c22_guard"),
        train(75, 6), guard("75_c22_train_s6", "75z_c22_guard"),
        train(76, 7), guard("76_c22_train_s7", "76z_c22_guard"),
        job("77_c22_evaluate", ["evaluate", "--data", "gate_data", "--runs", "gate_runs", "--config-sha", H,
                                "--workers", "16"], "G-C2.2 runbook 5: evaluation"),
        guard("77_c22_evaluate", "77z_c22_guard"),
    ],
}


def main() -> int:
    which = sys.argv[1]
    jobs = SETS[which]
    names = [n for n, _ in jobs]
    assert names == sorted(names) and len(set(names)) == len(names), names
    assert all("c22" in n for n in names)
    for n in names:
        for suffix in (".job.json", ".done.json"):
            if (Q / (n + suffix)).exists():
                print(f"refused: {n}{suffix} exists already")
                return 1
    if "--dry" in sys.argv:
        for n, j in jobs:
            print(n, json.dumps(j))
        return 0
    for n, j in jobs:
        tmp = Q / f"{n}.job.json.tmp"
        tmp.write_text(json.dumps(j, indent=1), encoding="utf-8")
        tmp.rename(Q / f"{n}.job.json")
        print("queued", n, flush=True)
        time.sleep(0.2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
