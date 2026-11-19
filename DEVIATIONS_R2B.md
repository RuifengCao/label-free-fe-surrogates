# R2B DEVIATIONS LEDGER

Companion to `PREREG_R2B.md` (r2, stamped 3 November 2026, tag
`prereg-r2b`, self-hash `4905049d...`). The stamped file is never edited.
Its Sec. 7 has the adjudication record deviations itself, among them:
restarts, resumed seeds, repeated attempts, steps not started or whose last
attempt did not exit 0, steps started on more than one host or GPU driver,
a solve ledger above 0, a different torch, GPU or TF32 setting between the
arms, and adjudicating code or a pre-registration other than the tag's. The
verdict file (`records/wp9/r2b/r2b_verdict.json`) lists three, all of one
event: the session's steps started on two hosts, the baseline's two
attempts, and the baseline's restart (seeds 3 and 4 reused, seed 5 resumed
from its checkpoint at epoch 161). This ledger records what the
adjudication cannot see: two departures from the runbook, the fine set's
labelled count (B1) and an instance rental that ran out during the session
(B2), and, under B2, the event behind the three deviations. No criterion,
threshold, configuration or verdict is changed by any entry below.
`tests/test_r2b_returns.py` checks each time, host, count and step quoted
here from the committed return against it; what comes from the PI rather
than from the return is marked as his. Times are box time (+0800) unless
marked UTC. The return's tarball is not committed; its SHA-256 is in
`records/wp9/README.md`.

## B1 -- the fine set's labelled count read 60, not the runbook's 320 (9 November 2026, UK time; 10 November, box time)

**Facts.** RUNBOOK_R2B Sec. 0d expected `runs/data3d_phase2_fine` with
manifest `0f859ad98a01...`, 320 instances and 320 labelled, and asked the
operator to stop and report anything else. That line was wrong (below), and
the session started without the stop it asked for. The box printed that
manifest, 320 instances and 60 labelled: the operator's screenshot, which
the PI forwarded at 17:04 UTC on 9 November (neither is in the repository).
By then the session's first step had started, at 01:02:06 on 10 November
(17:02:06 UTC on 9 November; `session/status.txt`). The same day the PI had
the line checked against the code and the records below, and let the run go
on.

**Why 60.** `fejepa.cli info` counts the instances that the manifest flags
as labelled, and this manifest flags 60. It is the manifest every run on
this set has recorded (`0f859ad98a01...`, as in Phase-2b's report and in
fine3d's R2a reports). The files of P3's 256 fine evaluation instances hold
their reference solutions: both arms labelled them without a solve (in both
reports `labels_present.fine_val` reads 256 and the solve ledger 0), as
fine3d's R2a did. RUNBOOK_FINE3D Sec. 0d carried the same line. Both
runbooks now read 60 labelled, each with a dated note at the line.

**Against the pre-registration.** PREREG_R2B Sec. 3 reads the first 256
instances of the fine set, labelled since Phase 2, and buys no label; both
hold. The departure is from the runbook's instruction to stop.

## B2 -- the instance's rental ran out during the baseline; the session resumed on another host (16-18 November 2026)

**Facts.** `session/status.txt` records S's arm and its amplitude pass from
01:02:06 on 10 November to 12:07:06 on 13 November, each started once and
ended with exit 0, then the gate's line (`r2b_b: r2b_s has a complete
report`) and the baseline's start at 12:07:08 on 13 November, all on host
`autodl-container-eb3344896e-709d725c` with GPU driver 595.71.05. Nothing
records the end of that attempt: no exit line, no `session interrupted`
(which Ctrl-C writes) and no STOP. Its log, kept as
`session/r2b_b.log.20261118-203710` (the session script renames a step's
log when the step starts again), ends without an error after seed 5's line
at 80% of its steps (163,840 of 204,800). Seeds 3 and 4 had finished: their
states were written at 14:54:40 on 14 November and 17:45:41 on 15 November
(the provenance file's listing). The session started again at 20:37:10 on
18 November, on host `autodl-container-1qjylxm03k-f5fe291f` with driver
595.71.05: it skipped S's two finished steps, found S's report complete and
restarted the baseline from its states (D9). Seeds 3 and 4 were read from
their states, and seed 5 resumed from its checkpoint at epoch 161 of 200
(step 164,864; `session/r2b_b.log`). The baseline ended with exit 0 at
03:01:59 on 19 November, and its amplitude pass ran from 03:02:00 to
03:38:19, exit 0.

**When and why the first attempt ended.** The records do not date it. In
its log seeds 3 and 4 took 26:50:49 each, 8.05 min per epoch. From seed 4's
state at 17:45:41 on 15 November, seed 5's epoch 161 falls near 15:22 on 16
November and its epoch 162 about 8 min later; the attempt ended between the
two checkpoints, since the restart found epoch 161's. This is an estimate
from the unit times: the checkpoints' own times are not in the return. The
status file records nothing from then until 20:37:10 on 18 November, about
53 h. The return does not record why the attempt ended; the PI stated on 19
November 2026 that the instance stopped because its weekly rental had run
out.

**What ran where.** On the first host: S's three seeds, its P3 evaluation
and its amplitude pass; the baseline's seeds 3 and 4, and its seed 5 to
epoch 161. On the second: seed 5's epochs 162 to 200; the evaluation of the
baseline's three states on the validation split (E8's cell, which supplies
K1's values: a restart evaluates reused states again) and on the fine set
(P3); and the baseline's amplitude pass. Every number of the baseline that
the verdict reads therefore comes from the second host, and every number of
S from the first. The second host held the first's outputs (S's report and
states, the baseline's states and seed 5's checkpoint), as the restart's
reading of them and the provenance file's listing show. On 19 November 2026
the PI's console lists the second host's instance and no longer the
first's; that the second was cloned from the first, with its disks, is an
inference. Both start lines read driver 595.71.05, and both reports record
torch 2.12.1+cu130, an RTX 5090 and TF32, the settings the adjudication
compares between the arms. The provenance file, written on the second host,
describes only it: 16 CPUs (Xeon Gold 6459C) and `oom_kill 0`. The return
holds nothing else about the first host. It holds one suite log, undated
and naming no host: whether Sec. 0c's suite ran again on the second host is
not recorded.

**Against the runbook.** RUNBOOK_R2B asks that the instance's balance cover
about 210 h (its paragraph on time, before Sec. 0). By the PI's account the
instance was rented by the week, and the rental ran out during the
baseline, an estimated 158 h after the session's first step; the session
was then restarted as the runbook's Sec. 1c provides. This is the cause of
the three deviations that the verdict file lists.

**Against the pre-registration.** Sec. 7 provides the restart (D9) and has
the adjudication record it, the second attempt and the second host; the
verdict file lists all three. PREREG_R2B does not claim that a resumed seed
equals an uninterrupted one. The session script checked the code before
every step of the second attempt (no STOP), and both reports record
`prereg-r2b`. Holding the other values as they are, condition (i) would
hold for any fine displacement error of the baseline's seed 5 from about
0.06 to 0.73 (it is 0.308), condition (ii) for any fine / in-band ratio from
about 1.4 to 25.5 (it is 7.72), and K1 for any in-band value of that seed
from 0 to three times its own: seed 5's last 39 epochs, trained on the
second host, could not have decided the verdict.
