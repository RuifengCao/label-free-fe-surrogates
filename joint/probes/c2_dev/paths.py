"""Folders the scripts of this note read and write (exploratory; under no stamp).

Each is taken from an environment variable; three have defaults inside this repository.

    C2DEV_JOINT    the joint/ folder of `git archive prereg-c2`, the tree stamped for G-C2.1
    C2DEV_SRC      the src/ folder of the same tree
    C2DEV_DATA     a folder holding manifest.json and inst/: the 580 instances exported with the stamped code
                   (`python -m c2 generate`), which equal the host's
    C2DEV_STATES   a folder holding label_free_s0/state.pt to label_free_s2/state.pt, the host's final states of
                   G-C2.1 (hashes in ../c2_diag/HOST_STATES.md; not in the repository)
    C2DEV_RETURN   G-C2.1's return package; default ../../records/c2/return
    C2DEV_WORK     what the scripts write and read back; default records/ in this folder
    C2DEV_RUNS     the runs/ folder of the GPU scripts; default records/gpu in this folder, which holds the small
                   records of those runs
"""
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _folder(name, default=None):
    value = os.environ.get(name)
    if value:
        return Path(value)
    if default is None:
        raise SystemExit(f"set the environment variable {name} (see paths.py)")
    return default


def joint():
    return _folder("C2DEV_JOINT")


def src():
    return _folder("C2DEV_SRC")


def data():
    return _folder("C2DEV_DATA")


def states():
    return _folder("C2DEV_STATES")


def ret():
    return _folder("C2DEV_RETURN", HERE.parents[1] / "records" / "c2" / "return")


def work():
    return _folder("C2DEV_WORK", HERE / "records")


def runs():
    return _folder("C2DEV_RUNS", HERE / "records" / "gpu")
