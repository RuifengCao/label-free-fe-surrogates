# FINE3D DEVIATIONS LEDGER

Companion to `PREREG_FINE3D.md` (r5, stamped 18 October 2026, tag
`prereg-fine3d`, self-hash `534f5dba...`). The stamped file is never edited.
Its Sec. 8 has the adjudication record deviations itself, among them:
restarts, resumed seeds, seeds taken from disk, repeated attempts, steps not
started or whose last attempt did not exit 0, a solve ledger above 0, a
different torch, GPU or TF32 setting between the arms, R3 seeds on more than
one host or GPU driver, and adjudicating code or a pre-registration other
than the tag's. The verdict file (`records/wp9/fine3d/fine3d_verdict.json`)
lists none. This ledger records the departures the adjudication cannot see,
from the return. No criterion, threshold, configuration or verdict is
changed by any entry below. `tests/test_fine3d_returns.py` checks each time,
commit, tree and count quoted here from the committed return against it. The
tarball's member times (the tarball is not committed; its SHA-256 is in
`records/wp9/README.md`) and R1's records (R1's return, to be committed on
branch cmame-paper) are quoted as read there.

## F1 -- the session ran before R1, not after it (20-21 October 2026)

**Facts.** RUNBOOK_FINE3D Sec. 0 has R1 (branch cmame-paper, PREREG_HOLDOUT)
run first when one visit runs both, its return packed and sent before this
branch is checked out, because the two branches share the checkout and
`runs/`; the operator instruction of 18 October 2026 (not in the repository)
said the same. This visit ran the fine3d session first: its status file runs
from 01:29 on 20 October to 16:35 on 21 October, box time (+0800)
(`records/wp9/fine3d/return/session/status.txt`). R1 ran after it on the
same host: R1's earliest dated record, its precheck at 18:02:11 box time on
21 October, is 1 h 27 min after the session's last step ended (16:35:09),
and R1's first attempt started at 10:02 UTC, 18:02 box time. R1's first
suite run is undated (RUNBOOK_CMAME Sec. E0c, on branch cmame-paper, runs it
just before that precheck).

**Against the pre-registration.** PREREG_FINE3D does not order the two, and
R1's result does not gate this session (RUNBOOK_FINE3D Sec. 0). The
adjudication checks the session's inputs by their records (the corpora's
manifests and the Phase-2b states by SHA-256). The departure is from the
runbook's instruction only.

## F2 -- the return's provenance file names a cmame-paper commit (21 October 2026)

**Facts.** RUNBOOK_FINE3D Sec. 2 writes `provenance.txt` from the checkout
after the session; its first lines are the checkout's HEAD, tree,
`git describe`, tags and `git status`. In this return they name commit
`8b5d4436ee4a91836b627ef852cd2f5e98d88b0f` (tree
`e288619b0338a6fa497dfabba6c953e8b3a4e553`, describe
`prereg-cm2d-2-g8b5d443`, no tag), two commits after branch cmame-paper's
tag `prereg-cm2d`, and not `prereg-fine3d` (commit
`5a312232796e417bedac582aa77872922f84c07c`, tree
`371b2913f93137fb63bd633f365eff810f8f2fe3`); `git status` lists one
untracked file outside `runs/`. The checkout had therefore been switched to
cmame-paper before the return was packed. The records place the switch after
06:25:10 on 21 October, box time (the session script's last check of the
commit, before R3's labelled arm), and before 18:02:23 (R1's first attempt);
the operator instruction of 18 October asked for no git command in the
checkout while the session ran. The return was packed at 18:03 (the
tarball's member times: its files copied at 18:03:29, the provenance file
written by 18:03:33), a minute after R1's first attempt, which was made on
the same commit and stopped at once (each step exit 2: R1's script is not on
that commit); R1 then ran from 18:16:04 on `prereg-holdout` (R1's return,
`status.txt` and `machine.txt`).

**What the records show about the session's code.** The session ran on the
stamped commit: every report and every R3 seed records `prereg-fine3d`, and
the adjudication, which refuses a report of another commit, refused none;
the session script checks the commit before every step, and the status file
has no STOP line; the session's suite read `704 passed, 1 skipped`
(`session/pytest.log`; RUNBOOK_FINE3D Sec. 0c, before the session; the log
itself is undated), the stamped commit's count. The rest of the file
describes the box and `runs/`, which the switch does not change: torch
2.12.1+cu130 with CUDA and gmsh 4.15.2; the SHA-256 of the four reports and
the two amplitude records, which equal the committed files'; the states'
SHA-256, which equal those the reports record; the GPU (RTX 5090, driver
595.71.05), the host, 25 CPUs (Xeon Platinum 8470Q), the memory limit and
events (`oom_kill 0`) and the disks.

**Why it is recorded here.** The adjudication reads the commit each report
records, not the provenance file, so the verdict file cannot show this. The
file's git lines record the checkout when the return was packed, not the
session's.
