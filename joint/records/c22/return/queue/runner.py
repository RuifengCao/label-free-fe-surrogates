"""Job runner for the development trials on this laptop (exploratory work, not a gate).

It runs, one after another, the jobs found in the folder `queue` next to this file. A job is a file
NAME.job.json holding {"script": "<Python script inside this folder>", "args": [...], "note": "..."}.
Each job runs with this environment's own Python. Its output goes to logs/NAME.log and its result to
queue/NAME.done.json. Jobs run in the order of their names; a job that already has a .done.json is skipped.

- Only scripts inside this folder are run.
- While it runs, the runner asks Windows not to go to sleep. It changes no setting: the request ends with the window.
- It stops when this window is closed, or when a file queue/STOP appears (after the running job).
- A file queue/NAME.kill stops the job NAME while it is running.
"""
import datetime
import json
import os
import pathlib
import subprocess
import sys
import time

BASE = pathlib.Path(__file__).resolve().parent
QUEUE, LOGS = BASE / "queue", BASE / "logs"
POLL_IDLE, POLL_JOB = 20.0, 5.0


def now() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def keep_awake(on: bool) -> None:
    """Ask Windows to stay awake while this process lives (ES_CONTINUOUS | ES_SYSTEM_REQUIRED). No setting changes."""
    if os.name != "nt":
        return
    import ctypes
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000001 if on else 0x80000000)


def write_json(path: pathlib.Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def status(state: str, job=None, **more) -> None:
    write_json(LOGS / "runner_status.json", {"time": now(), "state": state, "job": job, "pid": os.getpid(), **more})


def pending() -> list:
    jobs = sorted(p for p in QUEUE.glob("*.job.json"))
    return [p for p in jobs if not (QUEUE / (p.name[:-len(".job.json")] + ".done.json")).exists()]


def run_job(path: pathlib.Path) -> None:
    name = path.name[:-len(".job.json")]
    done = QUEUE / f"{name}.done.json"
    try:
        job = json.loads(path.read_text(encoding="utf-8-sig"))
        script = (BASE / job["script"]).resolve()
        if BASE not in script.parents or not script.is_file():
            raise ValueError(f"the script must be a file inside {BASE}: {job['script']}")
        args = [str(a) for a in job.get("args", [])]
    except Exception as err:                                   # a malformed job is recorded and skipped
        write_json(done, {"name": name, "error": f"{type(err).__name__}: {err}", "ended": now()})
        print(f"[{now()}] {name}: not run ({err})", flush=True)
        return
    log = LOGS / f"{name}.log"
    env = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    started, t0 = now(), time.time()
    print(f"[{started}] {name}: started ({job.get('note', '')})", flush=True)
    with open(log, "ab") as fh:
        fh.write(f"=== {name} started {started}: {script.name} {' '.join(args)}\n".encode())
        fh.flush()
        proc = subprocess.Popen([sys.executable, "-I", "-u", str(script), *args], cwd=str(BASE), env=env,
                                stdout=fh, stderr=subprocess.STDOUT)
        killed = False
        while True:
            try:
                rc = proc.wait(timeout=POLL_JOB)
                break
            except subprocess.TimeoutExpired:
                status("running", name, started=started, minutes=round((time.time() - t0) / 60, 1))
                if (QUEUE / f"{name}.kill").exists():
                    proc.terminate()
                    killed = True
        fh.write(f"=== {name} ended {now()} with code {rc}\n".encode())
    write_json(done, {"name": name, "returncode": rc, "killed": killed, "started": started, "ended": now(),
                      "seconds": round(time.time() - t0, 1)})
    print(f"[{now()}] {name}: ended with code {rc} after {round((time.time() - t0) / 60, 1)} min", flush=True)


def main() -> int:
    QUEUE.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    keep_awake(True)
    print(f"[{now()}] runner started in {BASE}", flush=True)
    print("Closing this window stops the runs. Keep the laptop plugged in and do not close the lid.", flush=True)
    idle_since = None
    try:
        while True:
            if (QUEUE / "STOP").exists():
                print(f"[{now()}] queue/STOP found: stopping", flush=True)
                status("stopped")
                return 0
            todo = pending()
            if todo:
                idle_since = None
                run_job(todo[0])
                continue
            if idle_since is None:
                idle_since = time.time()
                print(f"[{now()}] no job waiting; checking the queue every {int(POLL_IDLE)} s", flush=True)
            status("idle", idle_minutes=round((time.time() - idle_since) / 60, 1))
            time.sleep(POLL_IDLE)
    except KeyboardInterrupt:
        status("interrupted")
        return 1
    finally:
        keep_awake(False)


if __name__ == "__main__":
    sys.exit(main())
