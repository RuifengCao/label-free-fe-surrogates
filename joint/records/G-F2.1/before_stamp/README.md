# What was checked before the stamp of gate G-F2.1

Made on 25 November 2026 on the author's machine (a processor, no GPU), except the timing, which is from the gate's host. Nothing of the gate was drawn or trained for any of it.

- `host_check_processor.json`: the record of the host check (`f21/smoke.py`) on the code as stamped: its checks, the seconds of its stages, the machine. Its sample of two was drawn with the day 20260102, and its verdict is that of stand-in networks.
- `session_simulation.json`: the outcome of the simulation of the host's task, for the trainings one after another and at the same time. Its sample of two was drawn with the day 20260103. The logs are not kept here: they hold the paths of the machine.
- `timing/`: the timing on the gate's host: `timing.json` (the session, the seconds of the second epochs and their ratio), the progress files of the four runs of two epochs, and the cost of a training step by its parts on the smaller mesh and on the family's mesh.
- `first_order/`: the judged first-order value against the exact one (`probes/f21_first_order/first_order.py`): the estimate from the development's records for all 31 members, the exact value on eight of them, solved again on the author's machine, and the record of those eight members' exports and labels there.
- `code_equivalence.json`: stand-in trainings under the development's `f2` files as the two runs of the recipe had them (`records/f2_dev/code_as_run/`) and under the stamped files (`probes/f21_code_equivalence/`).
- `tests.txt`: the result and the slowest tests of the whole suite on the stamped state, without the block of warnings, which holds the paths of the machine.
- `not_stamped.sha256`: the SHA-256 at the stamp of three files that the stamp does not cover: the script with which the verdict's statistics are computed again after the run, and the two test files of the gate and of the development.

The JSON files hold `Infinity` and `NaN` where a value is infinite or not a number.
