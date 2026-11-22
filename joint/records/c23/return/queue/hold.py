"""A job that only waits: it keeps the queue from starting anything while a job is paused (tools/pause.py), and ends
when tools/resume.py writes queue/NAME.go."""
import pathlib
import sys
import time

QUEUE = pathlib.Path(__file__).resolve().parents[1] / "queue"
name = sys.argv[1]
print(f"paused: waiting for queue/{name}.go", flush=True)
while not (QUEUE / f"{name}.go").exists():
    time.sleep(2)
print("continuing", flush=True)
