"""Guard job of a gate's command queue. It reads how the stage before it ended and, unless that stage ended with
exit code 0, cancels every later job of the same family, so that nothing runs after an error: the runbook's
"stop and report".

    python -I tools/guard.py STAGE FAMILY SELF

STAGE   the name of the stage's job (queue/STAGE.job.json). A stage that was paused and continued (tools/pause.py,
        tools/resume.py) also has the jobs STAGE_b_hold (the wait) and STAGE_c (the continuation), and so on; the
        last continuation decides.
FAMILY  a text that every job of the runbook carries in its name, for example "c22".
SELF    this guard's own job name; the later jobs are those whose names sort after it.

A cancelled job gets a queue/NAME.done.json that says so, which the runner then skips. The guard changes nothing else.
"""
import json
import pathlib
import sys
import time

QUEUE = pathlib.Path(__file__).resolve().parents[1] / "queue"


def names() -> list:
    return sorted(p.name[:-len(".job.json")] for p in QUEUE.glob("*.job.json"))


def done(name: str):
    p = QUEUE / f"{name}.done.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main() -> int:
    stage, family, me = sys.argv[1], sys.argv[2], sys.argv[3]
    chain = [n for n in names() if n == stage or n.startswith(stage + "_")]
    runs = [n for n in chain if not n.endswith("_hold")]
    if not runs:
        why = f"no job named {stage}"
    else:
        last = max(runs)
        d = done(last)
        waiting = [n for n in chain if done(n) is None]
        if waiting:
            why = f"jobs of the stage have not ended: {waiting}"
        elif d.get("returncode") != 0 or d.get("killed"):
            why = f"{last} ended with {json.dumps({k: d.get(k) for k in ('returncode', 'killed', 'error')})}"
        else:
            print(f"guard: {last} ended with exit code 0; the queue goes on", flush=True)
            return 0
    later = [n for n in names() if n > me and family in n and done(n) is None]
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    for n in later:
        tmp = QUEUE / f"{n}.done.json.tmp"
        tmp.write_text(json.dumps({"name": n, "cancelled": True, "by": me, "because": why, "ended": stamp}, indent=1),
                       encoding="utf-8")
        tmp.replace(QUEUE / f"{n}.done.json")
    print(f"guard: {why}. Cancelled {len(later)} later jobs: {later}. Stop and report.", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
