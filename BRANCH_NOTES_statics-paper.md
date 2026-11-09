# BRANCH NOTES -- statics-paper

Called `cmame-paper` until 29 October 2026, when it was renamed `statics-paper` on GitHub
(Stage 16). This file, the runbook, the manuscript's directory, its generator and its tests
were renamed after it in Stage 18; the entries before Stage 18 use their old names.
Branched 3 Oct 2026 from `wp9-pool` at `414a372` (Stage 0e). Purpose: the
manuscript (`paper/statics/`) and the box sessions it needs. `wp9-pool`
stays at its pre-stamp head for PREREG_W9; nothing here touches PREREG_W9,
its configurations or any other stamped configuration.

## Governance

- The manuscript's numbers are generated from committed records only
  (`scripts/make_statics_material.py`, checked by `tests/test_statics_material.py`).
- Box sessions follow `RUNBOOK_STATICS.md`. A session's return is committed
  under `records/cmame/` before the manuscript reads it.
- Code changes leave every default training and evaluation path unchanged;
  new behaviour is opt-in, with tests.

## Stage 0 (3 Oct 2026) -- the manuscript draft

`5d089b7`: `paper/cmame/` (sections, generated tables, figures and numbers,
references), the generator, its tests, and the three two-dimensional reports
of July 2026 under `records/phase1/` with their hashes. Two independent
reviews addressed. Suite 453.

## Stage 1 (6 Oct 2026) -- diagnostics in the field export; standalone timing

- `scripts/export_fields.py` records, per model, seed, validation instance and
  load case: the squared Euclidean and stiffness norms of the error (their
  ratio, the error's Rayleigh quotient, is its error-weighted mean eigenvalue
  of K, a single number for its weight in stiff modes; normalised by the
  solution's own quotient it equals g over the squared relative displacement
  error); the relative von Mises error over the element values (the
  evaluation's) and weighted by element volume (the L^2 norm of Proposition
  1); the stress-energy integral of the error, equal to its squared stiffness
  norm by Proposition 1; and the largest absolute prediction on a constrained
  dof (0, since K is stored unconstrained). Per instance and load case of U*:
  its two norms and gamma*. `fields.json` summarises them per model (medians,
  the largest ratio to Proposition 1's bound, the two identities' deviations,
  and how often a supervised model's error has the larger Rayleigh quotient
  than the label-free model's on the same instance, load case and seed). The
  figure files carry the element volumes. The manuscript's two statements
  that these quantities were not measured (the errors' weight in stiff modes;
  the bound against measured errors) can then be replaced by measurements.
- `RUNBOOK_CMAME.md` Sec. A: the timing and field export of `RUNBOOK_W9.md`
  Sec. 4, run on their own before PREREG_W9's stamp (the 2D timing on E1's
  validation instances only, since F5 is made by wp9's session 1); outputs
  under `runs/cmame/timing/`.
- Tests: `tests/test_w9_fields.py` checks the new arrays against direct
  computations (Lemma 1 and Proposition 1's identity to 1e-8, gamma* from
  the stress tensors, the stiffness norm against the free block, the bound on
  every prediction, the Rayleigh quotients inside the stiffness matrix's
  spectrum, the element-count error against the evaluation's, the
  volume-weighted error against the figure's stresses) and the summaries
  against the arrays. Timing on a mesh of 17,425 nodes and 76,800 elements:
  1.5 s per instance for the nine models (the largest validation mesh has
  17,692 nodes), a few minutes over the validation split.
  `tests/test_cmame_runbook.py` checks that the runbook names only existing
  scripts and options, writes only under `runs/cmame/`, and states the
  suite's current count (the two LaTeX builds deselected on the box), and that
  its commands are RUNBOOK_W9 Sec. 4's apart from the F5 timing. Suite 457.

## Stage 2 (6 Oct 2026) -- CM2D: the 2D supervised networks retrained, with a stiffness-norm control

The manuscript's 2D comparison reads the run of 16 July 2026 (the July code);
the label-free transformer was trained again with the current code (E1), the
supervised networks were not. And its explanation of the label-free
network's lower stress errors -- the norm of the objective -- was never
tested with labels. CM2D (PREREG_CM2D.md, r1 draft, not stamped) retrains the
supervised rows on E1's corpus, split and seeds with the current code, beside
E1's states (evaluated, not trained), and adds the same transformer trained
on the relative stiffness-norm error: H1 (label-free against labels-only,
energy gap), H2a and H2b (stiffness norm against labels-only: energy gap, and
the von Mises error that neither loss contains), H3 (a two-sided reading,
stiffness norm against label-free).

- Code (opt-in; every default path unchanged):
  `EnergyAnchor.quad` (v^T K v with the constrained dofs masked, analytic
  gradient); `SupervisedConfig.loss = "knorm"`, the mean over load cases of
  ||u - U*||_K / ||U*||_K (the displacement loss with the norm replaced;
  recorded in the protocol only when not the default); E8's
  `include_anchor` (default true) and `include_knorm` (default false) rows,
  the stiffness-norm row's largest-budget states kept; `e8.reuse_from` with
  `supervised_grid: true` evaluates the reused label-free states beside a
  trained supervised grid (refused with a fine-tuning row; the configuration
  may differ from the source run only in the keys that shape the supervised
  grid); the step count exact for configurations that name `include_knorm`;
  the results page and figure show the new row.
- `records/cmame/`: the default path against `wp8-lejepa` again on both
  miniatures, identical (the final Stage 2 `src`); `tests/test_w9_records.py`
  now requires the committed `src` to be the tree named by the newest
  regression record. `cm2d_sims.json`: the decision rule's operating
  characteristics (equal and unequal seed spreads, July's spread, per-instance
  blow-ups) and the run's wall time by a simulation of its unit schedule.
- `scripts/make_cm2d_config.py` -> `configs/cm2d_v1.json` (from E1's stamped
  base); PREREG_CM2D.md; `scripts/stamp_prereg_cm2d.py`;
  `scripts/cm2d_precheck.py` (GO/STOP before the run: the GPU idle, the
  checkout on the tag with the describe string the report records, the
  configuration, the dry run, E1's corpus and labels, E1's states
  reproducing E1's validation values when evaluated as the run evaluates
  them, a short stiffness-norm training on the GPU, no earlier attempt;
  `--restart` before a restart, refused once a report exists; `--pre-stamp`
  for a readiness check before the stamp); `scripts/adjudicate_cm2d.py`;
  RUNBOOK_CMAME Sec. B (the box: readiness, checks, the run started only on
  GO, health check, restart, return) and C (the adjudication).
- Three independent reviews (code, pre-registration, operations) before the
  draft went to the PI. Addressed: H2 split into H2a (energy gap; close to a
  check that the loss took effect) and H2b (von Mises error; the test of the
  manuscript's explanation); L_K uses each reference solution only through
  one number per load case and its gradient is the label-free one weighted
  per load case, so H3 compares two weightings of the same residual; the
  label-free and supervised transformers of a seed share their initial
  weights and instance order (tested); the operating characteristics extended
  to July's spread, a noisy new arm and per-instance blow-ups; the
  reproduction of E1's values moved before the run; a finished report can no
  longer be overwritten by a restart, and the run starts only on the
  precheck's GO; the adjudicator checks E1's report as a stamped run, the
  recorded commit and tree against the tag, every seed value's presence,
  attempts by start and exit lines and by run logs, and writes strict JSON;
  secondary readings never block a verdict; mutation checks of the new tests.
  Second round: the background states what July's labels+energy row did
  and did not test; the constrained dofs and the relation of the von Mises
  error to Proposition 1 stated; the graph-network reading corrected
  against the earlier runs; H3's reading with the roles exchanged reported
  beside it; the precheck leaves the GPU alone when it is busy, turns a
  failed reproduction into a FAIL line, sees any script of the repository
  as another run, checks that the run imports this checkout's code, and
  treats any trace of an earlier attempt as one; the run and the restart
  use up their GO, so a re-pasted block starts nothing; B0 fetches its own
  commit; the restart rules no longer contradict the health check.
- Tests: `tests/test_cm2d_training.py` (the loss and its gradient against
  direct computations, what the trainer minimises, the reuse run on a
  miniature with its refusals and exact step count, the units' payloads, the
  supervised-grid keys against the label-free units, every other key
  compared, shared initial weights and order), `tests/test_cm2d_prereg.py`
  (configuration, stamp, simulation record, the quoted numbers),
  `tests/test_cm2d_adjudicate.py` (verdicts, refusals, reuse checks,
  deviations, the command line on a made-up return around E1's report, the
  pre-run checks on a miniature laid out like the box, the git and stack
  checks), `tests/test_cmame_runbook.py` per section. Suite 501.

## Stage 3 (7 Oct 2026) -- a full check of Stages 1-2; RUNBOOK_CMAME Sec. B rehearsed end to end; PREREG_CM2D r2

- Checked: the code of Stages 1-2 read against PREREG_CM2D and RUNBOOK_CMAME;
  every number PREREG_CM2D quotes from E1's, July's and Phase-2b's records
  recomputed (all as quoted). No defect in `src`, which is unchanged.
- A functional check of the stiffness-norm loss (`scripts/cm2d_funccheck.py`,
  `records/cmame/cm2d_funccheck.json`: another corpus drawn by the 2D
  generator, a transformer of width 32 and depth 2 trained for 25 epochs on
  48 instances with each loss and the label-free objective, two seeds): L_K's
  validation energy gap and von Mises error far below L_D's, the L_K value
  the trainer computes equal to the mean square root of the per-load relative
  energy gap up to float32 round-off (relative deviation 7e-6 in the median,
  1.1e-4 at most: the stiffness spread of these meshes amplifies it, as the
  same formula in float32 shows), gradient clipping at 1 acting about as
  often for both losses. Its result bears on H2a and H2b (and on H1's and
  H3's comparisons), so PREREG_CM2D r2 discloses it, with the rehearsal's
  adjudication of its miniature (Sec. 1, 4, 7 and 9; r1 said that no
  supervised network had been trained with the stiffness norm and that the
  effects of L_K had never been measured); no question, arm, measurement or
  criterion changed, and the stamp script accepts only the r2 draft.
- Rehearsed (sandbox, CPU): Sec. B0-B4 and C, their blocks run verbatim on a
  miniature laid out like the box -- a local origin, an E1-like run on a tag
  `prereg-e1`, the generated configuration, the stamp and the tag
  `prereg-cm2d`; B0's and B2's checks gave GO; the run started on its GO and
  was killed with its workers as by a box restart; the re-pasted block
  started nothing; B3's checks gave GO and the restart took the finished
  units from the unit cache and resumed the interrupted one from its epoch
  checkpoint; B2' ran during it; B4's return was adjudicated by Sec. C with
  the reuse checks passed and the restart, the cached and resumed units, the
  two attempts and the two run logs recorded as deviations (on that
  miniature -- three supervised epochs beside label-free states of one --
  H1 NOT SUPPORTED, H2a and H2b SUPPORTED, H3 the stiffness-norm
  transformer lower: mechanics, not evidence). What a CPU
  sandbox cannot provide was stood in for in the sandbox copy only (an idle
  `nvidia-smi`, the CPU accepted on the precheck's torch line, E1's hash
  constants following the miniature).
- Fixed: one of the precheck's tests compared the precheck's reproduction of
  E1-like values with reference values computed on the CPU and required an
  exact match, while the precheck evaluates on the GPU whenever there is one:
  it passes on a machine without a GPU and would fail on the box. The
  precheck's tests now run it on the CPU; on the box the precheck itself
  still uses the GPU, as the run does. The zero-field count of the
  adjudication covers every row, the naive rows included (PREREG_CM2D
  Sec. 5: "per row and budget"). The test of the loss the trainer computes
  allows a relative deviation of 1e-4 (3e-5 observed), not 2e-3. And the
  suite could end without its summary line: `gmsh.initialize()` restores
  SIGPIPE's default action in the process that meshes, gmsh stays
  initialised in the test process after the first test that meshes in it,
  and a failed worker pool that still writes to its stopped workers' queue
  (tests/test_w9_parallel_kill.py, after tests/test_w9_ood2d.py) then ends
  the whole process (once in five full runs in the sandbox; reproduced in
  isolation). `tests/conftest.py` starts every test with SIGPIPE ignored
  again, as Python has it. The runs themselves are not affected: neither
  CM2D's run nor Sec. A's scripts mesh in their main process. (A run that
  generates a gmsh corpus in its main process and then loses a worker would
  end by SIGPIPE instead of its RuntimeError: for wp9, not changed here.)
- New tests: a restart beside the reused states, after an attempt that ended
  before its report and before one unit's result, evaluates the states
  again, takes the other units from the cache, ends with the first attempt's
  values everywhere and is adjudicated to the same verdicts with the restart
  recorded; a stiffness-norm training resumed from its epoch checkpoint ends
  bit for bit as the uninterrupted one; the functional check's record is the
  script's output on the Stage 2 code, PREREG_CM2D quotes its numbers, and
  the script runs; every test starts with SIGPIPE ignored, also after a test
  that meshed in the test process. An independent review of this stage
  addressed. Suite 507.

## Stage 4 (8 Oct 2026) -- the three roles of the energy, named in the manuscript

- Introduction: before the list of contributions, two sentences name the
  three roles of the energy (training objective, evaluation metric, failure
  detector) and point to the theory section, which derives each from the
  exactness lemma, and to the first three subsections of the
  three-dimensional results, which take them in turn.
- Discussion: a paragraph "The energy as an energy-based model" after "The
  energy in deployment". An energy-based model in machine learning is used,
  among other things, to find the output most compatible with an input, to
  rank two candidates and to detect whether one is compatible at all; its
  energy is learned and in arbitrary units, and the detection threshold is
  generally unknown when the model is built. The discrete potential energy
  is assembled and, with compatibility measured in the energy norm, answers
  the three exactly: its minimiser is the solution, and the ranking and the
  sign test of the preceding paragraph answer the other two, a compatible
  prediction being one no further from the solution than the zero field and
  the threshold, zero, needing no tuning. The picture of a training loss as
  an energy landscape is literal here as well; the loss is in general not
  convex in the parameters. The paragraph does not mention joint-embedding
  architectures. "The energy in deployment" now scopes its exact ranking to
  one load case, as the corollary "Zero-field test and ranking" states (it
  said one instance).
- References: LeCun, Chopra, Hadsell, Ranzato and Huang, "A tutorial on
  energy-based learning", cited in the authors' version (v1.0, 19 August
  2006, with the URL of the PDF read). The book (Predicting Structured Data,
  MIT Press, 2007) contains the chapter "Energy-Based Models" by LeCun and
  others; its author list and pages are to be confirmed before the entry is
  switched to it (comment in `references.bib`, whose header now says how an
  entry checked against another source is marked).
- Data and code availability (pending boxes): the repository is to be moved
  and renamed. The boxes ask for its address, its licence and the tag of the
  version described; note that the reviewers need the present address if
  the move comes after submission; and ask that the move be a transfer and
  rename on the hosting service, because git records the dates given to
  commits and annotated tags but not when they were pushed, which only the
  service records. A dated archive taken before the move, with an export of
  the service's record, is a further safeguard.
- No code, configuration, record or generated file changed. Suite 507.

## Stage 4b (8 Oct 2026) -- the return of RUNBOOK_CMAME Sec. A and B0, recorded

- `records/cmame/timing/`: Sec. A as it ran on the box on 8 October 2026 on
  commit `61f018f` (Stage 3): inference timing against exact solves (2D:
  E1's label-free state of seed 0 on 32 validation instances; 3D: Phase-2b's
  on 32 validation and the first 8 fine-set instances) and the field export
  of Phase-2b's nine states of the 1,024-instance budget, with the box's
  suite (505 passed, the two LaTeX builds deselected), the machine and the
  check before the timing. Fourteen files, copied byte for byte from the
  operator's tarball, whose SHA-256 matched on receipt;
  `records/cmame/README.md` lists their hashes and what each holds.
- `records/cmame/cm2d_ready.log`: B0 on the same commit (after Sec. A, by
  the operator's account): GO, with PREREG_CM2D unstamped, as it must be
  until the stamp.
- `tests/test_cmame_timing_records.py` (8 tests): the files and their
  hashes; every step exited 0 on the named commit and tree, with the GPU
  idle before the timing; the reports read are the committed records and the
  states the runs' own; every solver solved every instance, no CG fell back
  to the direct solve, the solutions agree with the labels, every matching
  CG met its target, and the timed model reproduces its report on every
  timed instance; the field export is complete and within the runbook's
  ranges; its counts agree with the manuscript's numbers; on every load case
  of `energies_val.npz`, the exactness lemma, the zero-field test and
  ranking, and the stress bound hold between quantities computed
  independently (the energies against the error's stiffness norm, the von
  Mises error against that norm), and the energy-optimal amplitude holds on
  the stored gaps; the per-instance means reproduce the report's energy
  gaps, displacement errors and von Mises errors; the figure rules,
  applied to the report's arrays, select the exported instances; B0 said GO
  on the same commit with PREREG_CM2D unstamped. Corruptions of a scratch
  copy of the records, with the README's hashes updated so that the hash
  test could not mask them, each made the test reading that record fail
  (an energy's sign, a timed row, the stamp line, the suite's summary line,
  and fourteen more in the review).
- `RUNBOOK_CMAME.md`: the suite count the box should now see is 513 passed,
  2 deselected (A0c, B1c); Sec. A says that it has returned, and where; B0's
  note on its commit now reads that the commit must contain the precheck
  script (Stage 1's, on which Sec. A was first planned, does not; both ran on
  Stage 3's).
- What the records show, for the next stage. The manuscript does not read
  these records yet; what it already states from other records (the
  label-free per-load count, the 2D warm-start finding) agrees with them.
  - Cost, medians over instances. Surrogate: first call on the GPU,
    preparation and copy back included. Solvers on the CPU, in a 16-CPU
    allotment with OMP and MKL set to 16 threads (the threads the direct
    solve and the mat-vec actually used are not recorded; to be settled
    before the manuscript states any): SuperLU on
    the free block, CG unpreconditioned to a relative residual of 1e-10, and
    the matching CG, stopped by the labels and so a lower bound. 2D
    validation (about 1,100 free dofs): surrogate 2.6 ms, direct 3.1 ms, CG
    24 ms, matching CG 7.2 ms. 3D validation (about 14,000): 49 ms, 0.91 s,
    1.2 s, 0.22 s. 3D fine set (about 112,000): 2.2 s, 105 s, 26 s, 4.3 s;
    there the surrogate's displacement error is 0.27 (median over the 8
    timed instances; 0.20 over all 256 of the fine set; seed 0) against
    0.031 on the 32 validation ones, and on 3 of the 32 fine load cases it
    is worse than the zero field, so that the matching CG took no step
    there. Started from the prediction, CG to 1e-10 took about as many
    iterations as from zero (per-instance ratios 0.98 to 1.04; on the fine
    set 1.6% to 3.5% more).
  - Per load case on the 3D validation split (3,072 per network): labels
    only 126 and graph network 106 worse than the zero field, label-free 1;
    none after the rescaling by c*.
  - The errors' Rayleigh quotient over the solution's, median: label-free
    12, labels only 132, graph network 1,026; a supervised error has the
    larger quotient on 89% (labels only) and 99.9% (graph network) of the
    instance, load case and seed triples. The volume-weighted von Mises
    error is close to the unweighted element-wise one (medians 0.047 and
    0.051 label-free, 0.25 and 0.26 labels only, 0.21 and 0.23 graph
    network), and Proposition 1's bound held on every prediction (largest
    ratio 0.85).
- The manuscript is unchanged. The next stage is to write the cost table,
  the field figures, the supervised networks' per-load counts and the
  spectral readings from these records, and to revise what they bear on: the
  discussion's "We have not measured the spectral content of the errors",
  the limitations' list of what is pending, and the introduction's "sparse
  direct and iterative solvers are fast at the sizes studied here" (in 3D,
  per instance, the direct solve took a median 20 times the surrogate's
  time on the validation set and 51 times on the fine set, and the matching
  CG, a lower bound, 3.9 times on the validation set).
- No source, script, configuration or generated file changed; one test file
  added. Suite 515.

## Stage 5 (8 Oct 2026) -- a last check of the code; PREREG_CM2D r3, stamped

- A last check before the stamp, by three independent reviews (the training
  and evaluation path the run executes; the adjudicator against the
  pre-registration and against the report the runner writes; the stamp, the
  tag, the precheck and the runbook, simulated on a single-branch clone),
  found no defect in the code. `src` is unchanged since Stage 2.
- PREREG_CM2D r3, approved by the principal investigator on 8 October 2026,
  four corrections of text; no question, arm, measurement or criterion
  changed:
  - Sec. 4 quoted the guard's operating characteristics "at July's L_D
    spread (8.9% in the relative energy gap; 7.1% in the von Mises error)"
    from a simulation at 9% only. It now quotes the 9% simulation for the
    energy gap (H1's and H2a's reference) and a new one at 7.1% for the von
    Mises error (H2b's): false support 1.3 / 3.4 / 8.8 / 11.8 / 16.5% and
    detection of a ratio of 0.8 in 97 / 89 / 57 / 45 / 38% at new-arm
    spreads of 5 / 9 / 20 / 30 / 50%; the summary "8-16% at new-arm spreads
    of 20-50%" holds for both.
  - Sec. 7 says the cost profile (52 ms per step) ran on the host the
    instance had then (Xeon Platinum 8470Q, 25 CPUs), and that on 8 October
    the instance ran on another (Xeon Gold 6459C, 16 CPUs; same GPU model,
    driver and torch) on which no training step has been timed; that the
    graph network takes the four load cases one after another through its
    checkpointed layers, where the transformer encodes them as one batch, so
    its step may take twice the transformer's or longer; the schedule is
    simulated at two and a half and three times (19.8 and 22.0 h); and the
    balance is raised from about 20 h to about 30 h.
  - Sec. 4 discloses the runs on the box before the stamp: the readiness
    check B0 (E1's states reproduced; the run's transformer trained with L_K
    for one epoch of two steps on two pool instances, relative energy gap
    0.995, nothing kept) and Sec. A's 2D timing of E1's label-free state of
    seed 0 on 32 validation instances (E1's values recomputed there, plus the
    rescaling by c* and conjugate gradients' iterations and times, none of
    which the hypotheses read).
  - Sec. 6 names the r3 draft as the one the stamp script accepts (it named
    r2).
- Stamped on 8 October 2026 with `scripts/stamp_prereg_cm2d.py` (which now
  accepts the r3 draft only): CONFIG_SHA256[cm2d_v1] =
  `bf1f1143b397331b95954229010bdce7bd9340d1b6e2abeb139337b117784a03`
  (configuration unchanged), footer
  `6eaf835fc9cab109d51160e50aec9da8e19ee4c2211c11977ac4b21d76846b7c`; the
  run's own guard (`verify_prereg`, label `cm2d_v1`) accepts it.
- `scripts/cm2d_sims.py`: the 7.1% cells, drawn after all the others so that
  every earlier value of `records/cmame/cm2d_sims.json` is unchanged, and
  graph-network step factors of 2.5 and 3; the record regenerated.
- `RUNBOOK_CMAME.md`: the box fetches directly (A0b, B0, B1b): on 8 October,
  by the operator's report, AutoDL's network route answered HTTP 503 and the
  direct fetch worked; the tag's refspec is forced, so that a stale local tag is
  replaced. The run's time is 11-22 h and the balance at least 30 h; the
  graph network's units at 1,024 labels may take 6-9 h. Before the operator
  instruction is sent, the repo side checks on the remote that only
  `prereg-cm2d` points at the stamped commit. B3: after a worker's
  death the run's own message suggests `--reuse-states`; the runbook's
  no-restart rule takes precedence. Sec. C fetches the tag by a forced
  refspec, in a clone of its own, checks that only `prereg-cm2d` points at
  the stamped commit, and checks out that commit before adjudicating. The
  box's suite count is now 514 passed, 2 deselected.
- Tests: the r3 quotes are pinned to their records (the 7.1% cells and the
  8-16% summary, the schedule's hours and the 30 h balance, B0's log and the
  precheck's smoke code, Sec. A's 2D timing, the two hosts); the stamp
  script's r3 markers. Suite 516.
- Review findings left as they are, for the record: the run records its
  `git describe` only when it writes the report (5 s timeout; a timeout would
  make the adjudication refuse; the operator runs no git command during the
  run, and `src` is not changed before the stamp for it); "no other tag on
  that commit" (PREREG Sec. 6) is checked on the remote before the run and
  at the adjudication (Sec. C), not by the precheck; the runbook fetches
  directly only, as the principal investigator decided on 8 October, with no
  fall-back to AutoDL's network route; a unit that hangs has
  no watchdog (the health check B2' shows it); each worker sets its torch
  threads from the host's CPU count (42 on this host's 128 CPUs, 16 of them
  allotted), as in E1; E8's built-in summaries use population standard
  deviations, the verdicts sample ones; the adjudicator flags a medians'
  disagreement by comparing the guard's outcome on medians with that on
  means, inside its `robustness` block.
- An incident in the sandbox, nothing pushed: one review made its scratch
  copy of this worktree with `cp -r`, which shares the worktree's git
  directory, and its simulated stamp commit and tag landed in the local
  repository. On the principal investigator's approval the branch was set
  back to `16973d3` and the tag deleted; the remote was never touched.
  Scratch copies are made with `git clone`.

## Stage 6 (9 Oct 2026) -- CM2D's return and verdict, recorded

- `records/cmame/cm2d/return/`: RUNBOOK_CMAME Sec. B as it ran on the box on
  the stamped commit `094c804` (tag `prereg-cm2d`): started
  2026-10-08T15:24:06Z, one attempt, exit 0, the supervised grid 12.8 h;
  nine files copied byte for byte from the operator's tarball, whose SHA-256
  matched on receipt (`records/cmame/README.md` lists them).
- `records/cmame/cm2d/verdict.json`: `scripts/adjudicate_cm2d.py` at the
  stamped commit, in a clone of its own with the tag fetched by a forced
  refspec (RUNBOOK_CMAME Sec. C), on 9 October; run again on the same inputs
  it writes the same file byte for byte. The label-free row passed its reuse
  checks (largest relative deviation from E1's values 0), and the adjudicator
  recorded no deviation. At 1,024 labels, seed means:
  - H1 SUPPORTED: relative energy gap 0.0383 (label-free) against 0.1334
    (labels only, L_D): rel -71.3%, threshold 12.4%.
  - H2a SUPPORTED: 0.0290 (stiffness norm, L_K) against 0.1334: rel -78.2%,
    threshold 16.4%.
  - H2b SUPPORTED: relative L2 von Mises error 0.106 (L_K) against 0.235
    (L_D): rel -54.9%, threshold 12.3%.
  - H3, no difference shown: 0.0290 (L_K) against 0.0383 (label-free): rel
    -24.2%, threshold 38.1%; L_K's seed values 0.0370, 0.0146 and 0.0355.
- Secondary readings (exploratory, PREREG_CM2D Sec. 5): the graph network
  has the lowest seed-mean displacement error at 1,024 labels (0.0499,
  against 0.0505 for L_D) and a relative energy gap of 0.825, above both
  L_D's and the label-free row's. The label-free row has the lower energy gap
  and the lower von Mises error than L_D on 767 of 768 instance-seed pairs,
  and so has L_K. L_K is worse than the label-free row beyond the guard at
  16 labels in every metric and at 64 in four of five (critical-region recall
  within), and within the guard at 256 and 1,024 in every metric. Values
  worse than the zero field: L_D 768, 532, 53 and 0 of 768 at 16, 64, 256 and
  1,024 labels; L_K 11, 1, 0 and 0; the graph network 766 and 187 at 64 and
  1,024; the label-free row none.
- Cost on this host (16 CPUs allotted, three workers), from the completion
  times in `run.log` (each unit's time includes its setup and evaluation):
  36-41 ms per transformer step (L_K about 5% slower than L_D overall) and
  73-78 ms per graph-network step, about twice; the grid took 12.8 h (PREREG_CM2D Sec. 7: 11.4 h at 52 ms with the graph network as fast
  as the transformer, 17.9 h at twice).
- Departures from the runbook's operations (`records/cmame/README.md`), none
  touching a file the adjudicator reads or a criterion: the direct fetch
  timed out and the operator fetched by one of the two routes of the
  supplement to his instruction of 8 October (which one is not recorded);
  after the run, B2's line that sets an earlier precheck log aside ran again
  at the box's terminal and renamed the precheck log (arrow keys pressed
  during the run may have recalled it from the shell history; how it came to
  run is not recorded).
- `tests/test_cm2d_records.py` (9 tests): the files and their hashes; one
  attempt on the stamped commit and tree; the report is the stamped
  configuration's on E1's corpus and seeds, with no restart and a solve
  ledger of 0; the verdict was made from these files; the verdicts, the 80
  comparisons, the label efficiency and the secondary counts follow from the
  report's per-instance arrays by the rule of PREREG_CM2D Sec. 4, recomputed
  in the test; and everything in the verdict that does not depend on git is
  what the adjudicator computes in process from the committed files. An
  independent review forged the hashes and confirmed that 21 corruptions of
  the return or the verdict each made a test fail.
- `RUNBOOK_CMAME.md`: Sec. B says that it has returned, and where; the box's
  suite count is now 523 passed, 2 deselected. The branch is no longer
  frozen.
- The manuscript is unchanged. The next stage is to bring this run into it:
  the two-dimensional comparison with the current code beside July's, and
  the statements the verdict bears on (the discussion's "we did not train
  one" and its reading of the stiffness norm, the limitation on the
  supervised baselines).
- No source, script, configuration or generated file changed. Suite 525.

## Stage 7 (9 Oct 2026) -- the error spectra of CM2D's models: script and runbook (post hoc)

The manuscript explains the label-free network's accurate stresses by the
norm of its objective (Corollary "Modewise contraction": the energy norm
weights the error in each eigenmode of K by its eigenvalue, the Euclidean
displacement norm weights all modes equally), and its discussion says that
the spectral content of the errors has not been measured. CM2D's H2b changed
only the norm of the supervised loss and the von Mises error halved; this
stage measures what the change did to the error itself. Specified after
CM2D's verdict: post hoc, reported only; nothing in PREREG_CM2D reads it.

- `scripts/cm2d_spectra.py` (new): for CM2D's kept states at 1,024 labels
  (L_D, L_K and the graph network, seeds 0-2) and E1's three label-free
  states, on the run's 256 validation instances, per load case:
  - the error's squared Euclidean and stiffness norms; normalised by the
    solution's, their ratio is the error's Rayleigh quotient over the
    solution's, as in Stage 1's 3D export;
  - the error's spectrum over the eigenmodes of the free stiffness block,
    diagonalised once per instance (at most about 3,600 free dofs), in both
    norms and in two binnings: by each mode's eigenvalue over the solution's
    own Rayleigh quotient RQ*, on fixed 1/8-decade edges from 10^-2 to
    10^6.5 with a bin below and one above (the axis on which the two losses
    differ: the Euclidean-weighted mean of lambda / RQ* is the normalised
    Rayleigh quotient; CM2D's meshes span about 10^-1.62 to 10^5.44 RQ*),
    and by mode rank in 40 bins of nearly equal count (for completeness:
    nearly all of a smooth field's Euclidean norm falls in the first rank
    bin, so the rank spectra cannot separate the rows); the solution's own
    spectra;
  - the von Mises errors over the element values (the evaluation's) and
    area-weighted; the energies and c*;
  - the rounding: every model also predicts every instance with TF32 off
    (`fejepa.runtime.setup_torch(tf32=False)`, the attention by the math
    backend), the run's policy restored after each instance; the error of
    that prediction (norms, log spectra) and the difference u - u_ieee
    (norms, stiffness log spectrum) are recorded beside the run's own
    predictions, so that the stiff end of a spectrum can be told from TF32's
    rounding, which is rough and falls there (the content check reads the
    run's own predictions only);
  - the checks: the spectra of each binning sum to the two norms; Lemma 1
    (||e||_K^2 = 2 (Pi_h(u) - Pi_h(U*))); the plane-stress form of
    Proposition "Energy gap and stress error" (the stress-energy identity
    with the three-dimensional bulk modulus, the bound
    vm^2 <= (1 + gamma*) g on every prediction, and gamma* itself through
    (1 + gamma*) ||s_vm(U*)||^2 / (3G) = ||U*||_K^2).
  Per row the summary gives the quotient (overall, per seed and per load
  case: the solution's own quotient varies between load cases by up to a
  decade relative to the smallest eigenvalue), the shares above 10^k RQ*,
  the IEEE predictions' readings and the rounding's share of the error's
  stiffness norm, overall and above 10^2, 10^3 and 10^4 RQ*. Per pair of
  rows it gives the ratios (first / second) of the means of the energy gap
  and of the von Mises error (the verdict's kind of comparison: for L_D
  against L_K they are H2a's and H2b's) and, since per load case the
  relative gap is the normalised Rayleigh quotient times the squared
  relative displacement error, the geometric-mean ratio of the gaps factored
  exactly into the ratios of the two (how much of a difference in energy is
  a difference in the error's spectral content and how much one in its
  size; the factorisation holds for the geometric means, not for the ratios
  of means), overall and per seed, with the shares of opposite rankings
  (Remark "Opposite rankings"). At a given seed the three transformer rows
  share their initial weights and instance order (PREREG_CM2D Sec. 2), so
  their pairing is a control; for the graph network's pairs only the ratios
  of means, the pooled geometric means and the share on the seed geometric
  means do not depend on the pairing. One figure instance by a rule fixed in
  the script: the median of L_D's relative energy gap, seed 0 (validation
  index 221, `instance_27356.npz`), with the mesh, the fields (also the IEEE
  predictions), the stresses, RQ*, gamma* and every mode's squared
  coefficient of the reference and of each row's seed-0 error. Before any
  model runs, the report's SHA-256 and every state's are checked against
  CM2D's committed provenance file (the label-free ones also against the
  report's d9_restart record), and a mismatch refuses; every model is also
  checked against the report's per-instance arrays (all five metrics
  recorded, the displacement error and the relative energy gap gated at a
  median relative deviation of 1e-3), and a mismatch ends with exit status
  5 after everything is written.
- `tests/test_cm2d_spectra.py` (10 tests): end to end on a CM2D-shaped CPU
  miniature on coarse gmsh plates (unequal element areas, holes; states,
  report, provenance file), with every identity on every array, the
  per-load arrays averaging to the report's per-instance values, the
  eigenvalues recomputed, every summary (whole tail curves included)
  recomputed from the arrays, the stored log spectra rebinned from the
  figure file's per-mode data, what the script prints, and strict JSON; the
  binning (the rank edges; an eigenmode's spectra one in its own bin of each
  binning; a mode exactly at 10^k RQ* counted at and above 10^k; the bins
  below and above); gamma*, the area-weighted von Mises error, the identity
  and the bound against independent computations on a structured mesh and
  on a gmsh mesh; a prediction that is not zero on a constrained dof;
  constructed smooth and rough errors and a rough rounding, which the
  summary orders the right way round (a wrong gamma* or a wrong spectrum
  moves the summary's checks of them); the refusals (a supervised state, the
  report, a label-free state against the d9_restart record and against the
  provenance file); exit status 5, with one outlying instance not failing a
  model and the figure instance beyond `--n-val`; the second pass's switch
  (TF32 off and the math attention backend inside, the run's policy and the
  default backends after, also when the pass fails); and, in process, with
  every prediction perturbed only inside that switch, the perturbation
  recorded as u - u_ieee (the figure's too), the content check reading the
  run's own predictions. Every one of 15 mutants of the second pass's code
  is killed by these tests.
- `RUNBOOK_CMAME.md` Sec. D (new): fetch (directly, as A0b ran on 8
  October, or from a git bundle of the branch the operator instruction
  sends, made with `git bundle create cmame-paper.bundle 094c804..cmame-paper`;
  a fetch that prints nothing for 10 min is abandoned for the bundle),
  checkout, CUDA and the suite, the export (`--device cuda`; about 10 min;
  nothing else on the GPU), what to expect, the return after any exit, and
  in the repo an end-to-end check against the verdict (H2a's and H2b's
  ratios of means). The header no longer calls the sections independent
  (Sec. D reads Sec. B's states and Sec. C's records); Sec. C says when it
  ran. The box's suite count, in A0c, B1c and D0c, is now 535 passed, 2
  deselected: so the suite reads under the box's Python 3.12.3, numpy 2.4.6,
  scipy 1.18.0 and torch 2.12.1+cu130, in a fresh clone (CPU); there, a
  rehearsal of the export at CM2D's model sizes on gmsh plates ended with
  exit 0, every model reproducing its arrays exactly and the TF32 policy
  restored. `tests/test_cmame_runbook.py` (two new tests): Sec. D names the
  script with options it accepts, writes only under `runs/cmame/spectra/`
  and its own return (every `tee`, redirection, `mkdir` and `OUT`), uses
  Sec. A's `run` helper, A0b's fetch and B1c's process check, pins its
  bundle route, checkout, rotations and the return line by line, exports
  from CM2D's committed return, and names the figure instance that the
  script's rule selects from the committed report and the summary line's
  keys; the suite count and both `--deselect` options are checked in each
  of the three sections.
- Three independent reviews, each reviewer in a clone of its own:
  - Code and science (three rounds, the third re-running every mutant on
    the candidate): no blocking defect; the identities, the log binning,
    the pair statistics and the gamma* check verified on the real
    validation meshes, rebuilt from the generator; the binning by mode rank
    alone could not have separated the rows and was supplemented, before
    any box run, by the binning by lambda / RQ*, whose edges were then
    widened to 10^-2 (seven instances put one mode of the axial load case
    just below 10^-1.5 RQ*). Of the reviewer's mutants of the script, all
    are killed by the tests above except two that are equivalent in
    practice (`>=` for `>` in a share; a padded bin count).
  - Operations (three rounds): no blocking defect; the runbook's blocks
    were run as pasted in a simulated box (both fetch routes, exit 0, exit
    5, a refusal, a crash, second pastes); the bundle block made pasteable,
    the return named once per paste, a CUDA check added; all of the
    reviewer's 31 mutants of Sec. D are killed by the tests above.
  - A fresh review before the push, of the run on the box itself: no
    blocking defect; one important point, answered by the second pass with
    TF32 off: TF32's rounding is rough and the stiffness norm weights it
    heavily, so on the most accurate rows it could account for part of the
    stiff end of a spectrum, and the states exist only on the box. Also from
    it: a guard against a non-positive eigenvalue, the pairing-free share,
    the per-load quotients, the runbook's rules for a fetch that hangs and
    for going on to the return after any exit, and a test assertion on
    element areas made robust to the gmsh version.
- Stage 6's record completed (`records/cmame/README.md`): the operator
  fetched the branch and the tag from the git bundle, one of the two routes
  of the supplement to his instruction of 8 October (his report, relayed on
  9 October).
- No source, configuration, pre-registration or manuscript change. Suite 537.

## Stage 8 (9 Oct 2026) -- the error spectra of CM2D's models, returned and recorded

- `records/cmame/spectra/`: RUNBOOK_CMAME Sec. D as it ran on the box on
  Stage 7's commit `8b5d443` on 9 October (16:23 UTC at the return): the
  suite 535 passed, 2 deselected; the export exited 0, its timed part 70 s
  (the eigendecompositions 31 s, the second pass with TF32 off 14 s); seven
  files copied byte for byte from the operator's tarball, whose SHA-256
  matched on receipt (`records/cmame/README.md` lists them). Every state
  matched CM2D's provenance file; every transformer reproduced the report's
  per-instance arrays exactly, the graph network within 1.4e-4 in median on
  the displacement error and the energy gap, the two the export gates
  (5.2e-4 on the peak von Mises error; its CUDA scatter reductions are not
  bitwise reproducible); the TF32 policy was in force after the second pass
  as before it.
- End to end (RUNBOOK_CMAME D3): the export's seed means of the relative
  energy gap and of the von Mises error are the verdict's, seed by seed, for
  H1, H2a, H2b and H3 (largest relative deviation 2.2e-13); L_D's over L_K's
  ratios of means are 4.596 (energy gap) and 2.215 (von Mises error), H2a's
  and H2b's.
- Readings (post hoc, reported only; medians over a row's 3,072
  seed-instance-load-case triples, pair readings on the same seed, instance
  and load case; the solution's own Rayleigh quotient is a median 1.27 times
  the smallest eigenvalue):
  - the error's normalised Rayleigh quotient (its Rayleigh quotient over the
    solution's): label-free 10.3, L_K 11.3, L_D 115, graph network 553;
  - L_D against L_K: L_D's quotient the larger on 94.9% of the triples
    (98.8% on the seed geometric means, which do not depend on the pairing),
    geometric-mean ratio 7.80 (per seed 8.26, 9.46 and 6.07); the squared
    relative displacement error's geometric-mean ratio 1.26 (per seed 0.96,
    1.65 and 1.26; L_D's the smaller on 50.0% of the triples); so the
    relative energy gap's ratio is 9.85 (= 7.800 x 1.262). The change of
    norm changed the error's spectral content, and its Euclidean size much
    less: on the log scale about 90% of the gap ratio is spectral (per seed
    102%, 82% and 88%);
  - L_K against the label-free row: quotient ratio 1.04 (L_K's the larger on
    49.1%), squared displacement ratio 0.64 (per seed 0.81, 0.39 and 0.81):
    in the geometric mean the same spectral content and a smaller error;
    H3, on the seed means of the gap, showed no difference (L_K's seeds
    vary widely);
  - the graph network against L_D: quotient ratio 4.33, squared displacement
    ratio 1.00;
  - the share of the error's squared stiffness norm in the modes at or above
    100 RQ*: label-free 69%, L_K 73%, L_D 95%, graph network 99% (the
    solution's own 1.5%); of its squared Euclidean norm at or above 10 RQ*:
    7.2%, 6.6%, 24% and 49% (the solution's 0.2%);
  - the bound of Proposition "Energy gap and stress error" holds on every
    load case (largest ratio 0.90);
  - TF32's rounding (u - u_ieee): a median 2.7% (label-free), 2.9% (L_K),
    0.7% (L_D) and 0.05% (graph network) of the error's squared stiffness
    norm, and, in the modes at or above 10^4 RQ*, 41% (label-free) and 36%
    (L_K) of the error's squared stiffness norm there (on the 2,010 of 3,072
    load cases whose modes reach that far); with TF32 off the quotients are
    9.1, 9.4, 114 and 558, and L_D's over L_K's geometric-mean quotient
    ratio 9.30 and gap ratio 11.9. The rounding makes the two smooth rows
    look rougher, so the readings as run understate the difference.
- `tests/test_cm2d_spectra_records.py` (11 tests): the files and their
  hashes; one export on Stage 7's commit and tree, exit 0 after a green
  suite, the TF32 policy kept, the machine, texts and timings quoted, and
  the log's summary line that of the JSON; the inputs (CM2D's committed
  report and provenance file, the stamped configuration, the twelve states,
  the run's validation split); every model's agreement with the report, also
  recomputed from the per-load arrays (the graph network's recorded
  deviations too); Lemma "Exactness", the zero-field test and ranking, the
  energy-optimal amplitude (the gap of c* u from the stored energies), the
  plane-stress stress identity and bound (gamma* from the stored integrals),
  the spectra's sums and the Rayleigh quotients' range on every array; bin
  by bin, every spectrum's stiffness-weighted over Euclidean mass within the
  bin's eigenvalue range and the outer bins empty, and the rounding of
  TF32's size on every prediction (so the second pass was not the first
  again); the summaries, counts and eigenvalue ranges recomputed with the
  script's functions, and the readings the manuscript may quote written out
  again from their definitions (overall, per seed and with TF32 off); the
  verdict's seed means for every hypothesis and H2a's and H2b's ratios; and
  the figure file, the rule's instance, with its stiffness matrix
  reassembled from its mesh by the generator's assembly (the eigenvalues, U*
  solving the stored loads, every row's seed-0 coefficients, norms,
  energies, gaps, c*, spectra and stresses).
- An independent review, in a clone of its own: no blocking defect; one
  statement corrected (the graph network's median deviation, which is within
  1.4e-4 on the gated metrics only), two readings worded more cautiously (L_D
  against L_K's displacement errors; L_K against the label-free row, beside
  H3), and the checks above added where its mutation run found gaps. Of its
  113 corruptions of the records (each with the README's hash forged), 105
  now fail a test; the other 8 touch nothing the records claim or quote (a
  shift of the rounding's mass between two low bins, the largest eigenvalue
  or the dof count of an instance that is not an extreme, two graph-network
  deviations that the records cannot recompute, one model's inference time,
  the suite's warning count and its time).
- `RUNBOOK_CMAME.md`: Sec. D says that it has returned, and where; the box's
  suite count, in A0c, B1c and D0c, is now 546 passed, 2 deselected.
- The manuscript is unchanged: its discussion still says that the spectral
  content of the errors has not been measured. The next stage brings CM2D
  and these readings into it.
- No source, script, configuration, pre-registration or manuscript change.
  Suite 548.

## Stage 9 (9 Oct 2026) -- CM2D, the error spectra and the field export in the manuscript

The manuscript reads the records of Stages 4b, 6 and 8. Every new number is
generated from them by `scripts/make_cmame_material.py`, which checks each
statement the text makes about them and stops otherwise; the cost table
waits for the thread measurement of RUNBOOK_W9 Sec. 4.

- Section 5 (two dimensions) now reports CM2D, the run of 9 October 2026, as
  the comparison. Its opening says what was retrained (L_D at every budget,
  the graph network at 64 and 1,024) and what was reused (E1's label-free
  states). Table 1 (`table_2d.tex`) is CM2D at 1,024 labels (label-free,
  supervised L_D, supervised in the stiffness norm L_K, graph network, the
  naive rows). 5.1: accuracy, H1, the guard defined in the text ("no
  difference shown" is not equivalence), the readings beside the verdicts
  (Table A.2), the graph network against L_D (lowest displacement error, 1%
  below L_D and within the guard; lower gap or von Mises error on no pair).
  5.2: H2a and H2b (the area-weighted ratio of von Mises errors, 2.26 against
  2.22 element-wise); H3 on its own (within the guard; seed 1 makes most of
  the difference, seeds 0 and 2 alone 2.7%; L_K lower on 87.6% of the pairs;
  instance resampling 21.9% to 28.0% lower, the seed-level guard does not
  separate). 5.3: the spectra (post hoc; Figure 2 `fig_spectra.pdf`; Figure 3
  `fig_field2d.pdf`, the rule's instance, 221, seed 0); the 90% is the
  log-share of the geometric-mean ratio 9.85, not of H2a's 4.60; TF32's
  rounding (2,010 triples = 670 load cases x 3 seeds) understates the
  differences between the networks trained in the two norms. 5.4: label
  efficiency; the budget comparisons named as 80 exploratory secondary readings
  without multiplicity correction; at 256 labels L_K's seed means are within
  the guard of the label-free ones although the label-free network has the
  lower gap on 72.4% of the pairs. 5.5: the run of 16 July 2026 (its table
  `table_2djuly.tex`, the former Table 1; decisions; observations).
- Theory: Remark "Size and spectral position of an error" (g = rho delta^2,
  eq:factor); the conjugate-gradient factor renamed q (rho is the quotient);
  Sec. 3.3 gains the area- against element-weighted von Mises medians in 2D
  and the volume-weighted ones in 3D (three significant digits); the counts
  of single load cases and the exported networks named in Sec. 3.4 and 3.7.
- Methods: L_D and L_K as numbered equations, L_K's dependence on each
  solution through ||U*_j||_K^2 only and its gradient (eq:lkgrad); TF32
  defined; the code versions by run; CM2D's reuse of E1's states, shared
  initial weights and the same sequence of per-epoch permutations; the
  field-plot rules, with the 2D rule disclosed as written after CM2D's verdict.
- Section 6: Figures 6 and 7 (`fig_field_worst.pdf`, `fig_field_median.pdf`)
  and Section 7's Figure 9 (`fig_field_fine.pdf`): the three visible faces of
  the box in a right-handed oblique view (front face z = max; the candidate's
  view was a mirror image); on the worst instance's load case the label-free
  displacement has the reference's shape and too large an amplitude (delta
  0.22, 0.045 after c* = 0.78); the 3D quotients and per-load counts; the
  stale F_max attribution of the 2D/3D displacement difference replaced.
- Abstract (250 words, no digits), introduction and conclusion: the 2D
  label-free against supervised result restored in the abstract; "with the
  labels fixed, the norm of the loss decided the stress accuracy"; the
  spectral reading flagged as post hoc; the 3D failure sentences scoped.
  Discussion: H3 as "no difference shown, which is not equivalence", the
  spectral share stated as a log-share of the geometric-mean ratio,
  Limitations (what was known at registration; exploratory budget readings).
- Appendix A: CM2D's criteria rows with network names; the guard note without
  tau (tau is the CG tolerance); Table A.2 (`table_cm2d.tex`): per-seed
  values, rel, SE_rel, guard, the guard on medians, Welch's and the
  instance-resampling 95% intervals for H1-H3 and H3 with the roles exchanged;
  "Three things were known" (the functional check also showed H1's direction
  and H3's split between its two seeds); the operational departures named; the
  run dated 8-9 October. The provenance sentences of Sec. 4.5 and the body of
  Appendix A's July paragraph, whose correction awaits the principal
  investigator, are unchanged apart from the paragraph title. Appendix B:
  Proposition B.1's bound renamed beta (delta is the displacement error).
- Generator: CM2D (report and verdict), the spectra and the field export are
  read and hashed into `sources.json`, with `scripts/adjudicate_cm2d.py`
  (checked against the hash the verdict records; the reuse bound 10^-4 is read
  from it). Every spectral reading the text quotes is recomputed from the
  per-load arrays and checked against the export's summary (TF32 off, the
  stiff-mode rounding and its count, per seed, seed geometric means, the
  2,010/670 count, the log bins). New checks: opposite rankings in either
  order; one count for label-free and L_D per load case; the gap and von
  Mises shares on the same pairs; the label-free gap below the graph
  network's at 64; L_K's errors the smaller in every seed, by far in seed 1;
  the medians and intervals beside the verdicts; the fig5 and fig6 load-case
  statements; Pi_h(u) > 0 against the error norms (not against g > 1, which is
  computed from the same energies). The field plots' load case "max" is
  np.argmax; each panel's sign is the stored energy's. Legends use the tables'
  names. Five new figures; colours follow the entity (L_K green, marker X; the
  five series validate all-pairs in light mode); single-hue ramps for fields.
- Tests (`tests/test_cmame_material.py`, 13 new): CM2D's numbers against the
  verdict and the report's arrays; every quoted spectral and CM2D reading
  recomputed independently; the criteria table against the verdict and the
  adjudicator's bound; every cell of Table A.2 recomputed from the report alone
  (seeds, rel, SE_rel, guard, reading, the guard on medians, Welch's interval,
  an independent resampling of the instances, the exchanged roles); the
  spectral and 3D readings from the per-load arrays; each field plot's
  instance and load case by its rule; the figure files tied to the energies
  and to Phase-2b's P3 arrays; the faces of the oblique view (right-handed,
  owner tetrahedra, exact tiling); each panel's annotation and colour scale;
  Appendix A's description of the functional check against its record.
  RUNBOOK_CMAME's suite count (A0c, B1c, D0c): 562 passed, 2 deselected.
- Review: three independent reviews of the candidate (science, code,
  editorial). No number was wrong. Two blocking findings, both fixed: "could
  not be told apart" (now: seed means within the noise guard, which is not
  equivalence) and Figure 4's caption (the 2D panels are CM2D's; July trained
  the energy-term transformer in 2D and the graph network at every budget).
  The important and minor findings were applied as listed above; the
  reviewers' proposed tests were adapted and added. A second, fresh review of
  the fixed candidate (with the mesh fix) found nothing blocking; its findings
  were applied: Table A.2 pinned cell by cell, Appendix C's description of the
  tests scoped ("the main numbers"), "the later code" in Sec. 6.1, the mesh
  wording; the proof of Proposition 1's display is numbered. Correction to
  Stage 8's note: seed 2's spectral log-share is 88.5% (written there as 88%).
- The structured tetrahedral mesh (`src/fejepa/fe/tet3d.py`; the patch
  `tet3d_kuhn_fix.patch` from another session, with two corrections from the
  second review: the code comment, and the coverage test asserting exactly
  once): `structured_tet_mesh` split each hexahedral cell into five tetrahedra
  that all share one corner, a table that tiles a cell under no corner
  ordering; with the ordering used, they covered 5/6 of the cell (no overlaps,
  one void per cell), and neighbouring cells did not conform. It now uses the
  six-tetrahedron Kuhn split along each cell's c0-c6 diagonal, the same in
  every cell, which is conforming. `tests/test_tet3d_mesh.py` (3 tests): exact
  and conforming tiling, every point covered exactly once, the P1 energy of a
  linear field exact. No record and no run reported in the manuscript used
  this mesh: every configuration of the reported runs and of wp9 uses gmsh
  (2D) or gmsh3d (3D); only the WP7-S1 smoke configurations,
  `scripts/bench3d_scale.py`, `scripts/amp_compile_check.py` and tests did.
  The tests' three-dimensional instances, on which the manuscript's theory
  checks also run, are now proper meshes of their boxes; every check passes,
  as it did on the defective meshes (the identities and bounds hold for any
  assembled system). No experiment is re-run. Because `src` changed, the
  cross-branch regression against wp8-lejepa ran again in the sandbox (both
  miniatures identical: 162 and 2,590 numbers, every state file
  byte-identical; 43 s and 100 s), and `records/cmame/`'s two summaries and its
  README name the new `src` tree, `7cc8ac1b...`, as `tests/test_w9_records.py`
  requires. wp9-pool, which noted the split as an observation in its own Stage
  notes, is frozen until session 2 returns; the fix goes there afterwards, with
  its regression record and its runbook's suite count.
- One source file changed (the mesh fix above), and the two regression
  summaries with it; no configuration, pre-registration or run record. Suite
  564.

## Stage 10a (10 Oct 2026) -- the provenance of the July 2026 documents, corrected

The manuscript said that the pre-registration documents of the two-dimensional
runs of July 2026 were committed on 3 August 2026, after the runs. For the run
of 16 July 2026 that was inaccurate, and to the paper's disadvantage; and it
did not mention that the repository's history had been replaced. Checked on
10 October 2026 against the hosting service and the commits themselves:

- The repository was created on 14 July 2026. Its first commit, `b365af5`
  ("Add files via upload", 03:25 UTC), was made through GitHub's web
  interface, which created it (committer GitHub) and signed it (verified; the
  packet names GitHub's web-flow key B5690EEEBB952194 and 03:25:10 UTC). It
  held the code of v2.1.4, which differs from v2.1.5 only in the four files
  that FIX_NOTES_v2_1_5.md lists; `PREREG.md` as shipped with that release, a
  template whose hash line was blank and which otherwise equals the stamped
  document that the run of 16 July checked (SHA-256 `b9470e68...`, as
  PROVENANCE_NOTE.md records); and `configs/phase1_rec8_v2.json` byte for byte
  as now (canonical SHA-256 `62b26ad8...`, the stamped hash, recomputed). It
  did not hold `PREREG_WP2.md`. The service still serves `b365af5` by its hash.
- The activity record logs nothing on the repository between that commit and
  a force push on 2 August 2026 at 17:29 UTC, which replaced the history (that
  commit alone) with the one that begins at the root commit `a548825`
  ("v2.1.5", dated 2026-08-03 01:26 +0800, 17:26 UTC on 2 August). That commit
  holds both stamped documents and PROVENANCE_NOTE.md as compiled on 1 August,
  which records their hashes. The record logs no tag creations and does not
  show visibility.
- The owner account's security log (exported by the account holder on
  10 October 2026; 643 entries from 13 April) records that the present
  repository (id 1299960094) was created, public, on 14 July 2026 at
  03:23:30 UTC, and that a public repository of the same name (id
  1268189576), created on 13 June 2026, had been deleted 13 seconds before
  (03:23:17 UTC). No entry of the export has the action `repo.access` (a
  change of visibility).
- FIX_NOTES_v2_1_5.md records a first attempt of the run of 16 July, on
  14 July, which stopped before any training (the corpus it had generated
  carried no labels); PROVENANCE_NOTE.md records the offline labelling of
  15 July. The manuscript did not mention the attempt.

Changes:
- Methods (pre-registration): the run of 16 July (document and configuration
  uploaded on 14 July in a commit that the service created and signed; the
  document there the template, differing from the checked copy only in the
  hash line, which held the hash of the configuration uploaded then; a first
  attempt stopped before any training) is separated from the run of 31 July
  (document committed on 2 August, after the run, its content resting on the
  archives and the provenance note); the replaced history is stated, with a
  pointer to Appendix A.
- Discussion (limitations): the same correction in one sentence.
- Appendix A, "Provenance of the two-dimensional runs of July 2026": the facts
  above, times in UTC (the committer's time zone, UTC+8, named for the date of
  3 August), the first attempt and the offline labelling, the tag
  `provenance-2026-07-14` (created in October 2026) that keeps `b365af5`, the
  exported activity record, and the security log's record that the
  repository was public from its creation. The deleted namesake of 13 June,
  which held nothing that the paper relies on (the author), is stated in the
  records and in the provenance note's addendum, not in the text, at the
  author's decision.
- Methods: the repository named public since its creation on 14 July.
- Appendix C: the activity record, exported on 10 October 2026, is committed
  in `records/provenance/` with a README on how it was obtained
  (`gh api ... /activity --paginate`; pages joined and sorted, events as
  returned; 103 events) and on the two commits; beside it, the security
  log's 15 entries that name FE-JEPA, with user agents, request identifiers
  and request headers removed (no other entry of the export committed).
- PROVENANCE_NOTE.md: a dated addendum (10 October 2026) on the first history,
  the force push and the tag; its header names the addendum.
- `tests/test_provenance_records.py` (5 tests): the export is the committed one;
  its counts, its two events before 6 August and the absence of logged tag
  creations, and the times, commits and tag quoted by Appendix A and the
  addendum; `a548825` a root commit with that date, holding the two stamped
  documents and the note as compiled on 1 August, which records their hashes,
  unchanged since (skipped without the history); `b365af5`, where present (the
  tag fetched), a root commit made and signed by the service at that time,
  whose `PREREG.md` differs from the stamped one only in the blank hash line,
  whose configuration is the registered one by blob and canonical hash, without
  `PREREG_WP2.md`, and whose code differs from v2.1.5 only in the four files,
  with the tag on it if the tag is present (without the commit, the README's
  statements are checked); the security log's entries: the committed ones,
  the three creation and deletion times, public throughout, no visibility
  change, nothing private kept, and the text and the note agreeing.
- Review: an independent review verified every statement against the API and
  the commit objects; its findings were applied: the stale limitation
  sentence; "the hash entered later" (the box's copy was stamped by
  14 July, as the fix notes record; the uploaded document was the release's
  template); "pushed" for a web upload, with the service's signature; the
  public status on 14 July stated only from the owner account's security
  log; the tag's creation date; the first
  attempt disclosed; tests for the first commit and for the note as
  committed; "today" removed; the replaced history named as one commit.
  RUNBOOK_CMAME's suite count (A0c, B1c, D0c): 567 passed, 2 deselected.
- The tag `provenance-2026-07-14` on `b365af5` is created and pushed by the
  author from a terminal (an annotated tag on a commit that no branch holds),
  before this commit, which names it.
- No source file, configuration, pre-registration or run record changed.
  Suite 569.

## Stage 10b (10 Oct 2026) -- authors, affiliations, declarations and licences

The authors' decisions of 10 October 2026, entered in the manuscript:

- Both authors are corresponding authors, Cao submitting the manuscript and
  handling the correspondence with the journal (`main.tex`: one footnote,
  "Corresponding authors.", and Song's address). Elsevier's submission system
  holds one corresponding author, the one who submits; its journals may show
  further corresponding authors in the published article at the authors'
  request, and this journal has published articles that show two.
- Affiliations as in the authors' joint preprint arXiv:2608.14695: School of
  Engineering, The University of Manchester, Oxford Road, Manchester M13 9PL;
  School of Computer Science, Wuhan University, 299 Bayi Road, Wuchang
  District, Wuhan 430072.
- `sections/declarations.tex`: the CRediT statement (Cao: Conceptualization,
  Data curation, Formal analysis, Methodology, Project administration,
  Software, Validation, Visualization, Writing -- original draft, Writing --
  review & editing; Song: Data curation, Investigation, Resources, Validation,
  Writing -- review & editing); no competing interests; no specific funding;
  the generative-AI declaration under the heading of Elsevier's policy of
  June 2026 ("... in the manuscript preparation process"), naming Claude
  Fable 5, Claude Fable 5.1 and Claude Opus 5.5 (Anthropic).
- Licences (the author's decision of 10 October 2026): `LICENSE` holds the
  PolyForm Noncommercial License 1.0.0, verbatim from the PolyForm Project's
  repository, after the line "Required Notice: Copyright 2026 Ruifeng Cao";
  `LICENSE-CC-BY-4.0` holds the legal code of CC BY 4.0 (SPDX's text) for the
  records, the console record `wp2_e2_console.txt`, the pre-registration
  documents, the deviations ledger, the provenance note and `paper/`. The
  README's new section "Licence" states what each covers and that the terms
  apply to every version in the repository. The Data availability statement
  names both licences; its first sentence (the address, the tag and the
  Zenodo DOI) stays pending until the repository's move, and Appendix C's
  pending box no longer lists the licence.
- Appendix C: the code was written with the assistance of the same models.
- Section 3.3 (the author's decision of 10 October 2026 to keep the term
  "label-free"): the training is defined as label-free; in the terms of
  machine learning it is unsupervised, though by Corollary 1 it is exactly
  stiffness-norm regression; it is not self-supervised learning, and the
  terms from self-supervised learning in Appendices A and B belong to
  separate experiments.
- `highlights.txt` (the author's choice of 10 October 2026): the 3D result
  carries "pre-registered"; the graph network's line says 3D; a 2D line, "In
  2D, with the same labels, a stiffness-norm loss halved the stress error",
  replaces the line on unmet criteria, which the text and Table A.1 still
  report. Five lines of at most 84 characters.
- `tests/test_cmame_material.py`: the highlights test follows the new lines
  and checks that the 2D stiffness-norm transformer's von Mises error is
  between 0.4 and 0.55 times the supervised transformer's ("halved"; the
  record gives 0.106 against 0.235); the test for hand-typed numbers skips the
  two model names and the two licence names that contain version numbers.
- `tests/test_licences.py` (4 new): both licence texts are verbatim (SHA-256 of
  the official texts), the README names each path it licenses and each
  exists, and the Data availability statement names both licences.
- RUNBOOK_CMAME: the suite count in A0c, B1c and D0c reads 571 passed, 2 deselected.
- The manuscript compiles without undefined references.
- No source file, configuration, pre-registration or run record changed.
  Suite 573.

## Stage 10c (10 Oct 2026) -- one narrative: the three roles, three dimensions first

The full-text check of 10 October 2026 (two independent readers, a reading of the
full texts of the three closest works and a bibliography check) and the authors'
decisions of that day (three dimensions before two; "stiffness norm" throughout),
entered in the manuscript, then read again by two independent readers, whose
findings are addressed. No result changed: every number still comes from the
generator, and no record, configuration, pre-registration or source file changed.

- Structure:
  - Section 5 is the three-dimensional comparison, by role (training objective,
    evaluation metric, failure detector), then label efficiency and the
    pre-registered decisions; Section 6 is the two-dimensional comparison, "the
    norm or the labels?", which tests the explanation of Section 3.
  - Introduction: one statement of the three roles, with the metric role made
    precise (energy differences rank the predictions of one load case without a
    solution; the relative energy gap of the tables needs the solution's energy);
    the thesis moved there from the discussion, softened to "controls them less
    well"; the label-free definition at the end of its second paragraph;
    contribution 1 separates the classical identities from the statements added.
  - Section 3 by role; a new Corollary 3 (ranking by energy) holds the ranking
    statement, the zero-field test is Corollary 4 and the warm-start bound
    Corollary 5. Section 3.7's checks, Section 3.3's medians, the TF32 paragraph
    and the field-plot rules moved to Appendix C (C.1 to C.3).
  - Section 4.5: one paragraph and the run register (Table 1); the text names the
    runs. The noise guard is defined once (note to Table A.1) and scoped to the
    runs that registered it; the three-dimensional pre-registration fixed none.
    "Each run was carried out once" now says that restarts reused trained
    networks and that the one repetition is the amendment of deviation D14.
  - The July run (old Section 5.5, Table 3 and the July rows of the
    label-efficiency table) moved to a new Appendix D (Tables D.1 and D.2), with
    a summary in Section 6.5; its warm-start test (K5) and Corollary 5's values
    form a new Section 8.3.
  - The token bottleneck moved from Section 8.2 to Appendix B, now "Two
    pre-registered side experiments"; Section 4.2 defines it.
  - Discussion: opens with "One energy, three roles"; a paragraph on the
    counterexample of FEVessel (a single run, best test error over the last third
    of training, reduced-integration references, unstated quadrature); sections
    cited instead of re-quoted numbers; limitations added (Proposition 1's
    assumptions, the displacement reversal between the dimensions, untested
    label-free fine-tuning, point-cloud thinning against mesh refinement).
- Accuracy:
  - Related work corrected against the full texts: Monteiro Fernandes et al.
    train a 3D convolutional network on the stress divergence; Monteiro
    Fernandes et al. and FEVessel each compare the same network with and without
    labels in a single run, with opposite outcomes; PFEM's warm start is "up to
    about nine times fewer iterations" at a tolerance of 10^-3; the nearest uses
    of the energy or residual to screen predictions are named; the shrinking of
    the saving with the tolerance is credited to PFEM and FEVessel.
  - Abstract, introduction and conclusion: no "decided the stress accuracy";
    H2b "supporting a pre-registered hypothesis"; the graph network's reversal
    labelled a reading of the run; ranking "of one load case".
  - Section 5.5 states the gate under both readings (GO amended, NO-GO
    registered) and that KP1 and KP2 were not triggered; the introduction's
    "pre-registered criteria ... met" is now the accuracy condition only.
  - Squared ratios: macros numThreeAncOverFreeGapRoot, numCmLabOverFreeGapRoot
    and numHTwoARootRel give the root-mean-square relative stiffness-norm errors
    beside the headline ratios of g.
  - The noise guard of the two-dimensional comparison, applied after the run to
    the three-dimensional comparison, puts three of its ten differences of seed
    means within the guard (numThreeGuardWithin, numThreeGuardTotal; the
    generator stops if the set changes).
  - Section 6 says what was known when the comparison was registered beside the
    hypotheses; the area-weighted reading cites Appendix C.1.
  - Drafting traces removed (DRAFT comments, "to be confirmed", "to be
    completed", Appendix C's pending box). Two pending boxes remain: the cost
    table (Section 8.4) and the Data availability's first sentence.
- Decisions of 10 October 2026 (Guide for Authors): the footnote "Corresponding
  authors. Ruifeng Cao handles correspondence."; Fig. 1's caption and Appendix C
  on AI-assisted drawing, and the generative-AI declaration names the TikZ code
  of Fig. 1 and the graphical abstract; the abstract has 240 words (248 with
  hyphenated words split) and no digits; `graphical_abstract.tex` (13 x 5.2 cm,
  numbers from generated/numbers.tex); line numbers after the front matter
  (`\linenumbersfalse` removes them); the highlights say "von Mises error".
- Generator: run names in Table A.1 and in the hashes list; "Label-free
  transformer" and "Token bottleneck" in Tables 6, 7 and B.2 and Fig. B.1;
  "stiffness norm" and "noise guard" in the notes, which define the guard once;
  the July rows of the label-efficiency table in
  `table_label_efficiency_july.tex`; three dimensions first in Table 3 and
  Figs. 5 and 6; the few-shot loss in Table 5's note; G1' (a) names the two naive
  baselines and the plain polynomial.
- Bibliography: issue numbers, OpenReview and proceedings addresses, DOIs and
  ISBNs added; arXiv DOIs for the three preprints; DeRyck2024 cited as its ICLR
  version. Still to check in a browser: OrtizStainier1999 (DOI, issue),
  Taylor2023DFR (DOI), Saad2003 (SIAM DOI), LeCun2006EBM (chapter authors and
  pages), and the published versions of PFEM and Monteiro Fernandes et al.
- Tests: the new table in TEXT; checks of the root ratios and of the guard
  reading; the hand-typed-number check skips table column widths; the theory
  tests renamed for the new corollary numbers; the highlights test follows the
  new wording; `test_manuscript_compiles` also builds the graphical abstract and
  checks its 2.5:1 page. No test added; the runbook's count stands.
  Suite 573.

## Stage 10d (11 Oct 2026) -- the cost table; the abstract names the three roles

- Abstract: the sentence on the metric and the detector becomes two. "The
  identity gives the energy three roles: training objective, metric and
  failure detector. Without reference solutions, the energy ranks predictions
  of one load case by their stiffness-norm error, and its sign flags
  predictions worse than the zero field." The list is three bare noun
  phrases, as in the title, with "and" before the last and no serial comma;
  the comma before "and" in the second sentence joins two independent
  clauses; "without reference solutions" governs both roles that need none;
  the error is named, since "this error" stood a sentence away from its noun.
  244 words, no digits.
- Section 8.4: the pending box is replaced by Table 8 (`table_cost.tex`) and
  a paragraph. The table: on the first 32 validation instances of each
  comparison and the first 8 fine-mesh instances of the 3D one, with the
  label-free transformer of seed 0, the medians of the surrogate's first and
  repeated call against the sparse direct solve (SuperLU) and conjugate
  gradients from the zero field, from the prediction, and stopped at the
  prediction's accuracy (an oracle stop, so a lower bound) with and without
  c*; the iterations per load case; the surrogate's accuracy with and without
  c*, and the matched CG's displacement error. Its notes give the instances,
  the hardware and settings, the fine mesh's failures (three load cases with
  a relative energy gap above 1, matched with no iteration) and the threads.
  The paragraph quotes the ratios as medians of per-instance ratios, the
  warm start's change of iterations in both directions with the caveat of
  Section 8.3, the threads in three dimensions (so the CG times may be
  overstated), and why the times are not read as a speed advantage (GPU
  against CPU, neither solver the one of choice for these symmetric positive
  definite systems, the matched ratio falling on the finer mesh).
- The introduction's "at the sizes studied here, sparse direct and iterative
  solvers are fast" now reads "conjugate gradients reached the surrogate's
  accuracy within a few times its inference time (Section 8.4)"; the
  discussion and the conclusion add that the predictions of Table 8 did not
  shorten conjugate gradients to $10^{-10}$ in two dimensions or three.
- `records/cmame/threads/`: RUNBOOK_W9 Sec. 4's return of 11 October 2026,
  byte for byte (the files wp9-pool commits as `records/wp9/threads/`), with
  a README section. It ran on another host (a Xeon Platinum 8470Q, 25
  threads) than the cost table (a Xeon Gold 6459C, 16).
- Generator: `cost_material` computes every cell from the per-instance records
  (refusing a record with an unsolved, fallen-back or unmatched solve, or a
  timed model that does not reproduce its report), the fine mesh's failures,
  and the thread readings in 3D and 2D; macros numCost... and numThreads....
  Appendix C no longer excepts a pending cost table and names the timings
  among the generator's inputs.
- An independent review: one blocking finding (the thread sentence had no
  scope; the 2D thread readings, unread, showed one thread faster), five
  important (per-instance ratios not said; "exact solves"; what the first
  call includes; the timing host's BLAS threads never read; the fine mesh's
  failures hidden by medians; no reason given for claiming no speed
  advantage) and minor ones (the warm-start wording, rounding of node
  medians, the table's scaling, an untested row, the 3D warm-start null
  result missing from the discussion); all addressed. The table now sets
  unscaled, and its float fits the page.
- Tests: `test_the_cost_table_follows_from_the_timing_records` recomputes
  every cell, ratio, failure count and thread reading with numpy from the
  per-instance records and checks the timing script's own summary medians
  against them; the new table in TEXT. RUNBOOK_CMAME: the suite count in
  A0c, B1c and D0c reads 572 passed, 2 deselected.
  Suite 574.

## Stage 10e (11 Oct 2026) -- the repository's new address in the manuscript and the records

- The repository was transferred on 11 October 2026 from HymnOfLight, the
  account that created it, to RuifengCao (about 12:28 UTC), and renamed
  label-free-fe-surrogates (before 12:52 UTC); the old addresses redirect and
  the repository keeps its id. `git ls-remote` gave the same 6 branches and
  11 tags from the old address before the transfer and from all three
  addresses after it, until 13:34 UTC, when wp10-joint moved on. The activity
  record exported after the transfer begins with the 103 events of the export
  of 10 October, unchanged; an export taken before the transfer gave the same
  output byte for byte. Software Heritage archived the repository from the
  old address before the transfer and from the new one after it, and both
  visits gave the snapshot swh:1:snp:79f91af6d07e45a45933743bda38253b49c82bb6.
- Data availability: the last pending box is replaced. The code,
  configurations and records are at
  https://github.com/RuifengCao/label-free-fe-surrogates; the version described
  is tagged `cmame-submission` and archived at Zenodo,
  https://doi.org/10.5281/zenodo.23298799; the repository as it stood on
  11 October 2026, when it moved to its present address, is archived with its
  full history by Software Heritage as that snapshot (linked). The DOI is
  reserved: on submission day the tag is made on the submitted commit, the
  tag's source archive is uploaded to the Zenodo draft and published, the DOI
  is checked to resolve, and the new address is saved to Software Heritage
  again; the PDF does not circulate before. The paragraph sets with
  `\emergencystretch=3em`, which keeps the addresses and the identifier inside
  the measure.
- Appendix A: the visibility sentence no longer outruns its evidence: the
  security log of the account that created the repository, exported on
  10 October 2026, records no change of its visibility up to that day.
  Appendix C: the entries of that log, and two sentences on the transfer, the
  second export and the snapshot.
- `records/provenance/`: `github_activity_2026-10-11.json` (the record
  exported after the transfer, 110 events, written as the first export; its
  compact form is the export as returned), `refs_2026-10-11.txt` (`git
  ls-remote --symref` of the new address at 13:33 UTC) and
  `repository_2026-10-11.json` (the repository's id, name, creation time,
  visibility and owner after the transfer). The README gains a section on the
  transfer and names the account of the security log by what it now is.
- `PROVENANCE_NOTE.md`: an addendum of 11 October 2026, CRLF kept; the
  opening lists it. The addendum of 10 October is left as written.
- README: titled with the new name; it says that the repository was called
  FE-JEPA until 11 October 2026, that the old address leads here and that the
  package keeps the name `fejepa`, and points to `CITATION.cff`.
- `CITATION.cff` (CFF 1.2.0, valid by `cffconvert --validate`): the code's
  author alone, the repository, the licence PolyForm-Noncommercial-1.0.0, the
  DOI and the snapshot. main gets the same README and a `CITATION.cff`
  without the DOI, which goes in once the Zenodo record is published.
- Tests: `tests/test_repository_transfer.py` (5 tests): the second export
  begins with the first, is written the same way, and in compact form hashes
  to the export as returned; the repository record keeps the id that the
  security log records as created, at the same second; the snapshot
  identifier recomputed from the listed refs (the manifest of swh.model, whose
  8.4.1 gives the same identifier), the kinds of the listed objects and the
  peeled commits of the tags where the clone holds them (git checks only in a
  work tree of its own); the records README's counts, times and hashes; the
  manuscript's statements, with no pending box left and no "owner account",
  HymnOfLight or FE-JEPA in its files; the note, the README and
  CITATION.cff. `test_cmame_material.py` names the DOI among the names that
  carry version numbers. Twenty-two deliberate mutations were all caught.
- An independent review: two blocking findings (the DOI read as a typed
  number; the suite count), four important (the snapshot is the repository at
  its move, not its history up to that day, since wp10-joint moved at 13:34
  UTC; the visibility claim beyond its evidence; quoted facts the tests did
  not check; the reserved DOI before submission) and minor ones (wording of
  the records README, the repository record, git checks in a tree unpacked
  inside another clone, a stale docstring, the scope of the name checks,
  peeled commits, the DOI on main, the DOI and the snapshot shown as links);
  all addressed. RUNBOOK_CMAME: the suite count in A0c, B1c and D0c reads
  577 passed, 2 deselected.
  Suite 579.

## Stage 10f (11 Oct 2026) -- references checked against their published versions; a data reference

- Six references were checked against PDFs of their published versions from
  the publishers' sites: the articles of OrtizStainier1999, Taylor2023DFR,
  MonteiroFernandes2025 and Wang2026PretrainFEM, the front matter of
  Saad2003 and the chapter of LeCun et al.; and Sun2026FEVessel against the
  PDF of its preprint (arXiv:2607.17318v1), read in full again. The articles'
  entries were right, and the DOIs of OrtizStainier1999 and Saad2003, which
  the PDFs do not print, were confirmed to lead to the article and the book.
  The chapter is now cited as published, "Energy-based models", chapter 10 of
  Predicting Structured Data (MIT Press, Cambridge, MA, 2007), pp. 191--246,
  with its six editors and its own DOI (10.7551/mitpress/7443.003.0014, from
  the publisher's site; key LeCun2007EBM), instead of the authors' version of
  2006. Saad2003 gains the DOI of its electronic edition, and its ISBN-10 is
  replaced by the ISBN of the paperback that the front matter prints,
  hyphenated in the standard way. The five standard references not checked
  until then (Samaniego2020, Geuzaine2009, Gustafsson2020, MarsdenWest2001,
  EppsPulley1983) were checked against the online records their comments
  name. Each entry's comment says what was checked; the header no longer
  lists entries to be checked.
- The three closest works, read in their published or preprint versions:
  - Wang et al. (the pretrain finite element method) derive, in their
    Appendix C, an asymptotic iteration bound for fixed-point iterations in
    which the logarithm of the norm of the initial error enters additively,
    and conclude that the benefit of a warm start shrinks as the tolerance
    tightens. Sun et al. (FEVessel), in their Appendix B, extend it to the
    symmetric positive definite system: for stationary iterations and, by the
    Chebyshev bound, for conjugate gradients, their estimate of the
    iterations a warm start saves is set by its initial relative residual and
    independent of the tolerance, up to a bounded offset from the constant of
    the bound and the conversion between residual and error, so that its
    share falls as the tolerance tightens; they add a model of the solver's
    set-up cost. Section 9 no longer says that a warm start saves a fixed
    number of iterations: both studies derive this for a bound or an
    estimate, and the conjugate-gradient counts of Sun et al. saved 580
    iterations at 10^-3 but 69 at 10^-4, which the section now states. The arXiv version
    3 of Wang et al., read at arxiv.org on 11 October 2026, has the same
    appendix; the readings of 10 October missed both appendices. Corollary 5
    is the energy-norm form of the estimate of Sun et al., without the
    offset; the opening of Section 3 no longer counts it among the
    statements added here, and Section 3 (after the corollary), Sections 2
    and 9 and the introduction's list of contributions credit both studies.
    Remark 4 credits the observation of Wang et al. that Newton's method
    could start from a larger residual from their predictions than from the
    zero initial guess, although the predictions were much closer to the
    solution; the remark bounds the conversion that Sun et al. treat as an
    offset.
  - For their linear problems Wang et al. report iteration counts to a
    relative residual of 10^-3, with unpreconditioned conjugate gradients in
    two dimensions and with unpreconditioned and preconditioned conjugate
    gradients in three (Section 9, which said "a preconditioned method in
    three"); Sun et al. report iteration counts and wall-clock speed-ups at
    three relative-residual tolerances (Section 9).
  - Both tested discretisation invariance on the point cloud of a test
    instance at varying density: "on the training mesh" is dropped
    (Section 7), and Section 9 uses the same term.
  - The supervised network of Sun et al. was more accurate in the H^1
    seminorm, which they report, not the H^1 norm (Sections 2 and 9).
  - In Monteiro Fernandes et al., the label-free network was more accurate in
    stress than the same network trained on the reference stresses (mean
    relative errors of 2.16% against 2.86% for sigma_xx and 3.99% against
    4.82% for the von Mises stress); "slightly" is dropped (Section 2).
  The other statements about them stand as written, among them that the
  comparison of Sun et al. is a single run whose errors are the lowest over
  the last third of training, with reference solutions on reduced-integration
  hexahedra with hourglass control and a quadrature of the energy loss that
  is not stated.
- Dalton et al. (2023), read on 11 October 2026 in the accepted manuscript,
  train the same graph network on the same 200 inputs with and without
  simulator outputs, in single runs: comparable displacement errors, smaller
  errors in energy and deformation gradient without labels, and a supervised
  loss that adds the deformation gradient narrowing that gap without closing
  it (their Appendix B). Section 2 said that two studies made such a
  comparison; it now names three, and the introduction cites Dalton et al.
  among the single runs.
- Section 4.2 said "normalised extents"; the geometry descriptor divides each
  extent by the upper end of its sampling range, so that the absolute size is
  kept, and the text now says so. It also states that every network ran 200
  epochs, so that a supervised network with n labelled instances took 200n
  steps and the comparisons at the smaller budgets differ in steps as well as
  in labels. Both points came from an outside review of an earlier version.
- The other checked works:
  - Ortiz and Stainier note that the strain-energy density of a finitely
    deforming solid, and with it their incremental potential, is in general
    not convex. The Outlook, which extends the construction to steps that are
    convex minimisations, now says so, and describes variational integrators
    as deriving each step from a discrete variational principle, not as
    minimisations.
  - Saad is cited at Section 6.11.3 for the bound of conjugate gradients.
- The Zenodo archive of the version described is cited in the Data
  availability statement as the data reference Cao2026Zenodo. The journal's
  guide asks for "[dataset]" immediately before a data reference; a brace
  group in the author field puts it before the author's initial in
  elsarticle-num's output. Its title, author and DOI are those of
  CITATION.cff, and its version is the tag that CITATION.cff's identifier
  names; the Zenodo record is published with them before submission.
- Tests: `tests/test_cmame_references.py` (4 tests): the data reference's
  fields, their agreement with CITATION.cff and the citation; the references
  as BibTeX renders them with elsarticle-num, without warnings; the comments
  of the checked entries, the header, the chapter's and Saad's fields, and
  that the entries without a comment are those of 10 October; the corrected
  sentences, and the corrected statements gone from their files.
  `test_repository_transfer.py` quotes the Data availability statement with
  the citation. Forty-nine deliberate mutations were all caught.
- An independent review, three rounds. First round: one blocking finding
  (the suite count), four important (the counts of Wang et al. are
  relative-residual counts only for their linear problems; Remark 4 did not
  credit their observation on Newton residuals; the opening of Section 3
  counted Corollary 5 among the statements added here without
  qualification; the Outlook set Ortiz and Stainier under convex
  minimisation) and minor ones (the description of the bound, citations as
  sentence subjects, "unpreconditioned" and "discretisation invariance"
  throughout, the chapter's place and sections, Saad's section and DOI, the
  header's account of the entries of 10 October, the supervised baseline of
  Monteiro Fernandes et al. trained on stresses, the tests' handling of
  BibTeX warnings, their scope and comments). Second round: two ambiguous
  clauses, "et al.~" before citations, and this entry. Third round: the
  statements resting on the preprint of Sun et al., checked against it; one
  blocking finding (Section 9 said that a warm start saves a fixed number of
  iterations, which both studies derive only for a bound or an estimate and
  which the conjugate-gradient counts of Sun et al. contradict) and minor ones
  (the offset in their estimate is bounded and comes also from the constant
  of the bound; wall-clock speed-ups rather than times; a page break inside
  "et al.", now "et~al."; the preprint's version in its entry; "the same
  data" rather than "the same instances"). All these were addressed. Not adopted: two optional additions from Wang et al.
  (the input-point distribution, and their claim that training on the
  equations avoids discretisation errors) and quotation marks for the
  sentence paraphrasing LeCun et al. Left for the submission checklist:
  publishing the Zenodo record with this title, author and version, its
  resource type, and the proof's handling of "[dataset]"; a check of
  Samaniego2020, MarsdenWest2001 and EppsPulley1983 against Crossref.
  RUNBOOK_CMAME: the suite count in A0c, B1c and D0c reads 581 passed, 2
  deselected.
  Suite 583.

## Stage 10g (11 Oct 2026) -- the break-even of label-free training

- Section 8.4 ends with a paragraph on what label-free training saves. At the
  median times of Table 8, the 4,096 solves that label the 1,024 training
  instances in three dimensions take about 15 min of the direct solver,
  against 27.3 h of training per seed, which the supervised transformer needs
  as well: for these problems label-free training saves those minutes, not
  the cost of training. Against the direct solve, one seed's training is
  recovered after about 110,000 predicted instances, and after about 590,000
  against conjugate gradients stopped at the surrogate's accuracy (an upper
  bound, since that stop reads the reference solution), on the hardware of
  Table 8. The abstract's first sentence now says that the cost of a solve per
  training example dominates where solves are expensive, instead of calling it
  the cost the surrogate should remove. The paragraph points to the
  Outlook, where solves are expensive enough for label-free training to pay
  for itself.
- The numbers are generated (`numCostLabelMin`, `numCostBreakEvenDirect`,
  `numCostBreakEvenMatch`, rounded to two significant figures) by
  `cost_material` from the 3D validation medians of the timing record, the
  training solves and the per-seed training time; the generator stops if the
  surrogate is not faster than either solve.
- Tests: `tests/test_cmame_references.py` recomputes the three numbers from
  the timing record and the deviation ledger, independently of the
  generator, and quotes the paragraph. RUNBOOK_CMAME: the suite count in A0c,
  B1c and D0c reads 582 passed, 2 deselected.
  Suite 584.

## Stage 11 (14 Oct 2026) -- PREREG_HOLDOUT r5 draft: the manuscript's claims on never-used instances

- Purpose: after submission, re-read eight of the manuscript's claims on the
  instances of its two corpora on which no recorded run or tool trained a
  network, computed a label or evaluated a network, with the stored states
  unchanged (evaluation only; nothing trains). The manuscript is not
  changed; the results are for a revision. Draft only: not stamped, not
  tagged. r1, r2 and r3 were each reviewed by three independent reviewers
  (code, the pre-registration, the box procedure), and r4's changes by a
  fourth; r2, r3 and r4 take up every finding (the third and fourth rounds
  found nothing blocking, and r4 changes no set, count, threshold or
  claim's rule). r5, after a review of the rules' margins (most of the
  eight rules turn only if the holdout numbers differ from the validation
  numbers by 20% or more; D2 and H2c by about 4% and 11%), adds V, whether
  the per-instance values are distributed alike on the holdout set and on
  the validation instances, beside the eight claims, with the comparisons
  that failed reported for a claim that does not replicate, the
  pairing-free reading of T1 and D2, intervals for the holdout-over-
  validation ratios of the means, the dependence among the claims stated,
  and the states' SHA-256 checked before the labels; no set, count, or
  claim's threshold or rule changes (one threshold added, V's level). Two
  independent reviewers (statistics and code; the pre-registration and the
  box procedure) read r5 and found three blocking points, all taken up:
  the seed matching was called arbitrary (at a seed the two transformers
  start from the same weights: it is a control); V was described and
  licensed as a test of the means (it compares the share of holdout values
  above validation values, so a mean carried by a few instances can move
  without a rejection); and its quoted power was that of eight quantities
  moved together (one error metric alone is detected far less often, a
  critical-region recall alone in most draws already at 2%; now recorded
  per quantity). A sixth round, one reviewer on the fixes, found nothing
  blocking; its points (two intervals for the ratios of the means, the
  wording of the dependence and of what V can see, tests of the new
  readings with sets of different sizes) are taken up. A last reading of
  the pushed text (no change to the code, a record or a test) added V's
  verdict to what any revision reports (the Publication line), said that
  the joint calibration rests mostly on, not entirely on, the
  three-dimensional label-free transformer, named the reports' arrays as
  the source of the quoted pairing-free margins, and set V's bullet in
  three paragraphs.
- Sets (`fejepa.analysis.holdout`): the tail of each corpus's pool after the
  deepest prefix any recorded run or tool used, by the seeded split, without
  the instances that another recorded set drew again, that a recorded tool
  rebuilt, or whose own file is held outside the box (backups of a whole
  corpus do not count) (`excluded`): `runs/data3d_phase2` pool[1024:]
  without 34 (686 instances) and `runs/data2d` pool[25600:] without 33
  (4,111). `scripts/holdout_pool_depths.py` reads every report at the head
  of the six branches from git objects, every JSON file reachable from the
  remote branches and tags it records (the same fifteen reports), and the
  depths of the tools outside the runs from their records
  (`records/cmame/holdout/pool_depths.json`). `scripts/holdout_overlap.py`
  replays the three-dimensional generator's sequential stream for every
  recorded set (checked against the field export's figure instances). Sets
  of seed 0 that draw a mesh size per instance hold the same instances index
  by index: the cross-branch regression's miniature of
  `configs/phase2b_v1.json` (`scripts/regress_against_branch.py`, run in the
  sandbox) is in-band instances 0 to 79 meshed coarsely (it labelled 67 and
  trained on 64), and the sandbox's rehearsal sets and reviewers'
  reproductions are shorter prefixes (two at the corpus's own band of mesh
  sizes, copies of in-band instances 0 to 5 and 0 to 9); the fine-mesh set,
  without the draw, repeats in-band instances 28, 106 and 294 of the tail
  and 198, 210 and 218 of the training pool (fine evaluation instances 212,
  224 and 232). Excluded from h3d: the 32 tail instances among 0 to 79 and
  106 and 294. In two dimensions: the 32 tail instances among the 256 that
  wp9's load-scale measurement rebuilt (the regression's 2D miniature, 0 to
  79, and the sandbox's rehearsals, 0 to 39 at most, among them) and
  instance 29992, whose own file the authors' July 2026 archive holds.
  Bounds: a set of the corpora's generators and seed of at most 80 instances
  with a band, 320 at one size or 256 in two dimensions shares with the
  tails only excluded instances (the script checks this); the sandbox,
  scanned on 14 October 2026 at 05:37 UTC by `scripts/holdout_scan_sets.py`
  (over /home/claude, /tmp and /mnt/user-data), holds no longer set
  (`records/cmame/holdout/overlap.json`), and is scanned again before the
  stamp, which is not made unless the scan exits 0; its time and result are
  recorded with the stamp. Labels: one direct solve per instance (four load
  cases) into `runs/holdout/<set>/labels/`, a manifest with the SHA-256 of
  each corpus file and labels file and the residual (at most 1e-8); the
  corpus files are read only; a resumed labelling keeps its labels, solves a
  truncated labels file or one recording other bytes of its corpus file
  again, and leaves the manifest as it was when it keeps every label; every
  file is written to a temporary name, flushed and moved into place.
- For the revision of the manuscript (not changed here): its Sec. 4.1 says
  "the other 720 were never used" and Sec. 7 that no network had seen the
  fine evaluation instances; three of each are instances of the other set
  (above), and 34 of the 720 were drawn again by other sets. Without fine
  evaluation instances 212, 224 and 232 the zero-shot seed means of the
  three networks' five metrics in the transfer comparison change by less
  than 1% (largest: the graph network's critical-region recall, -0.9%); no
  reading of Sec. 7 changes.
- `configs/holdout_v1.json`: the two sets with their exclusions, the
  reports (Phase-2b's, CM2D's), the 21 states with their SHA-256 copied
  from the records (the Phase-2b d9 record, the box's listing of 22
  September 2026 in `records/wp9/phase2_supervised_states.json`, E1's
  report as CM2D's records it, CM2D's provenance file), the content
  tolerance (1e-3, as the exports, with every value required finite), the
  claims' thresholds and V's family-wise level (5%); `load_spec` refuses
  criteria other than these six.
- `scripts/holdout_run.py` (box): `--stage label|eval|all`; refuses to run
  unless PREREG_HOLDOUT is stamped for the configuration; the evaluation
  refuses a report or a state with another SHA-256 (exit 3) before any model
  is built and before anything is written, checks every state by content on
  its run's validation split (exit 5 on a mismatch, after writing
  everything), then evaluates every state on every holdout instance with
  the frozen metric suite, with the per-load gaps and energies, on the
  validation instances too (`eval.json`, `eval_arrays.npz`), each corpus
  and labels file checked against the labels manifest first.
- `scripts/adjudicate_holdout.py` and `fejepa.analysis.adjudicate_holdout`:
  the claims T1-T3 (3D), H1, H2a, H2b (CM2D's, with its guard), H2c (the
  abstract's "more than halved", rel < -50% of the seed means) and D2 (the
  2D abstract sentence, in each seed and the seed mean), the reading H3, and
  the secondary readings beside their validation values with the
  holdout-over-validation ratios (per row and seed, each flagged with its
  state's content check; the counts and ratios over the seeds that passed;
  a comparison of two rows only when every seed of both passed);
  non-finite values as PREREG_CM2D in H1, H2a, H2b and H2c, NOT EVALUATED
  elsewhere (also of the row a claim says is better; disclosed). It
  verifies every returned file against the provenance file and refuses an
  unlisted one; a set without a complete evaluation is a deviation (its
  claims NOT EVALUATED), not a refusal; a set whose evaluation records
  another labels manifest than the one returned is one too after a
  labelling that `status.txt` records after the start of the evaluation that
  wrote the returned file (its last attempt that exited 0 or 5), and is
  refused otherwise, every other check of the set applying first;
  `status.txt` is read by attempt (a start line with its time and host, and
  the exit line that follows it), giving the attempts, a last attempt cut
  off or failed, and the hosts. A claim that does not replicate lists the
  comparisons that failed (`failing`: per metric and seed or the seed mean
  in T1 and D2, the part in T2, the network in T3). T1 and D2 carry the
  pairing-free reading: per metric, whether every one of the nine pairs of
  seeds holds, and the least favourable pair's relative difference (on the
  validation instances all hold; closest 3.0% in D2, the peak von Mises
  error), for the holdout set and, in `validation_reference`, for the
  validation instances; at a seed the two transformers start from the same
  initial weights, so the seed matching is a control and the nine pairs
  read whether a comparison also holds across seeds. V
  (`representativeness`): per set that returned and is adjudicable, row
  and metric (35 quantities), the per-instance values (mean over the seeds
  that passed) on the holdout set against the validation instances
  recomputed in the same run, a two-sided Mann-Whitney test (asymptotic,
  tie and continuity corrections; one vectorised call per set, equal to
  the per-quantity calls), Holm's step-down procedure at 5% family-wise;
  REPRESENTATIVE or NOT REPRESENTATIVE with the rejected quantities and
  those in which the holdout set ranks worse (by the share of holdout
  values above validation values, not by the means); rows with no passing
  seed and quantities with non-finite values (counted per side) left out
  and listed; NOT EVALUATED with nothing to read. Named V because R names
  wp9's remeshed set in Sec. 2. Beside it, per set, row and metric, the
  holdout-over-validation ratio of the means with two 95% intervals from
  2,000 instance resamples (`ratio_intervals`, seeded): the holdout set
  alone resampled over the validation mean as it is, and both sides
  resampled on their own. The
  verdict file records the versions of Python, NumPy and SciPy.
- `scripts/holdout_resample.py`: the rules on 1,000 resamples of the
  validation instances of the holdout sizes (`records/cmame/holdout/resample.json`):
  every claim REPLICATED in every resample drawn directly; with the
  validation set's own sampling added, every claim in all 1,000 except D2,
  in 969 (each of the 31 failures through the peak von Mises error in seed
  0; the record counts the failures per comparison; H2c came closest among
  the others, its largest rel -50.7%). PREREG_HOLDOUT Sec. 5 discloses
  this, and that T3's sign part is an identity of the computation. The
  record also calibrates V on the validation instances alone: random
  halves of 128 (1,000 splits) read NOT REPRESENTATIVE in 2.1%, and with
  the label-free transformer's four error metrics multiplied on one half by
  1.05, 1.10, 1.15 and 1.20, in 15%, 65.5%, 98% and 100% (200 each); at the
  holdout sizes (drawn with replacement) 2.6% without a change and 54%,
  100%, 100% and 100% with the factors, eight quantities moved at once. With
  one quantity alone made worse at the holdout sizes (an error metric
  multiplied, the recall divided; 200 draws per factor), V rejected it in
  1.5% to 99.5% of the draws at 1.10 (median about 30%) and 15% to 100% at
  1.20 among the error metrics (the 2D label-free transformer's energy gap,
  which H1 reads, 3.5% and 20.5%), and the recalls in 2.5% to 100% at 1.02:
  a test of the per-instance values rarely sees a 10% change of a widely
  spread quantity from 256 validation instances.
- `scripts/stamp_prereg_holdout.py`: the CM2D stamp, for this file (r5).
  `scripts/holdout_scan_sets.py`: the sets of the corpora's generators and
  seed under given directories, per kind, against the bounds (exit 0 iff
  within them), copies of the corpus manifests and stray instance files.
- RUNBOOK_CMAME Sec. E: the box session (remote set to the repository's new
  address, branch and tag with a bundle route, 21 states counted and
  checked by SHA-256 before anything is labelled, the holdout files
  counted, 5 GB free, suite, the four stages logged with start lines
  naming the host to a status file that is never rotated, E1' for
  interruptions, read per attempt: a stage whose last line is a start line
  or an exit of 128 or more is cut off and run again, a labelling run again
  is followed by its evaluation, a stage cut off twice is not run again;
  no progress for 30 min is reported, not stopped; the return with a
  provenance file of every returned file's SHA-256 and the host) and the
  repo-side adjudication. The suite on the box leaves out the tests that
  need TeX: the two LaTeX builds and the bibliography rendering
  (`tests/test_cmame_references.py`, which the box has never run); the
  count in A0c, D0c and E0c reads 683 passed, 3 deselected. B1c, which
  runs only on the tagged commit, reads that commit's 514 passed, 2
  deselected, as CM2D's return records it.
- Tests: `tests/test_holdout_rules.py` (with the configuration's thresholds,
  the rules read REPLICATED on the manuscript's own validation arrays with
  its quoted values, and the zero-field counts are its own; each rule at its
  boundary, ties, a gap and a mean gap of exactly 1, exactly half and the
  content tolerance (both medians, not the largest deviation) included; the
  non-finite rule; a failed seed's own readings kept outside the counts and
  ratios; the secondary readings, new row against reference, beside
  validation arrays of their own, and the claims' rules on the validation
  arrays for reference; the resampling record, its failure counts and the
  quoted margins re-derived, with V's calibration and the numbers the text
  quotes; the failing comparisons named per claim; the pairing-free reading
  on constructed seeds where the matched comparison holds and a cross pair
  does not, and its quoted margins; V on the manuscript's arrays against
  themselves, a constructed shift rejected in its direction and nothing
  else, recall lower read as worse, rows and non-finite quantities left
  out, a failed seed not read, nothing to read; Holm at its boundaries,
  with a NaN and in any order; V's level from the configuration, in the
  adjudication and in the calibration; the calibration with one quantity
  changed against V with that quantity alone changed; the ratio intervals
  re-drawn by hand with sets of different sizes and a remainder chunk,
  seeded, as the adjudication calls them, with failed seeds, non-finite
  values and a zero validation mean; the validation side's pairing-free
  readings against the holdout side's; a zero value in the
  pairing-free reading; the heavy tail the text quotes),
  `tests/test_holdout_config.py` (every
  configured value against its record, the thresholds against the
  pre-registration's text; the pool depths and the history scan re-derived
  from the listed commits and tags, or checked for consistency without them;
  the overlap record and its bounds re-derived, and the 34 and 33 exclusions
  derived from it; the regression tool's miniatures the sets it replays,
  within the bounds; the names; the draft or a verified stamp, stamped as a
  copy only; the scan script on sets of its own),
  `tests/test_holdout_run.py` (miniature 2D and 3D runs end to end: exact
  labels, untouched corpus files, resume with its summary line, a manifest
  record written again, a truncated labels file and one recording other
  bytes, the manifest kept, content checks to 1e-6, arrays against summaries
  and Lemma 1 on both sets, refusals before anything is written, a corpus or
  labels file that is not the manifest's, a state that does not reproduce
  its report, a set that did not return, a labels manifest other than the
  evaluation's with and without a labelling after it (an E1' recovery before
  the evaluation kept among the latter), labelled and resumed instances,
  attempts read by attempt and hosts, a report changed in the adjudicating
  checkout, non-finite values with a strict verdict, adjudicating code that
  differs from the commit compared, a pre-registration stamped for another
  configuration, and 32 altered returns each refused for its own reason,
  another commit or tree among them; V and the failing lists end to end,
  the seed of a state that failed left out of V and a set that did not
  return left out of it; E0c's state check run as the runbook writes it,
  on the miniature, with one state changed), and
  `tests/test_cmame_runbook.py` for Sec. E.
  Suite 686.

## Stage 11, r6 (16 Oct 2026) -- PREREG_HOLDOUT r6 wording: no rule, set or code changed

- An independent check before the stamp: the rules implemented again from
  the pre-registration's text alone (frozen before any code was read), then
  compared with `scripts/adjudicate_holdout.py` on 20,000 generated cases
  under the sandbox's versions and under the box's (numpy 2.4.6, scipy
  1.18.0), on 56 edge cases and on the manuscript's own arrays (every quoted
  number and `records/cmame/holdout/resample.json` reproduced); and the
  run's GPU paths, each one that export_fields.py or cm2d_spectra.py already
  ran on the box. No blocking finding: every verdict as the text states it.
  The text changed in three places:
  - Sec. 7: when no attempt of a set's evaluation exited 0 or 5, the
    evaluation whose start a labelling must follow is its first attempt, as
    `labelled_after_evaluation` reads it (tested since r4); the text had no
    such case.
  - Sec. 7: the stamp script refuses any file but this r6 draft (the text
    still named r5; found by an independent review of these changes); a
    test now ties the draft named there to the stamp script's.
  - Sec. 9: a critical-region recall changed alone is detected at 2% in 54%
    to 100% of the draws for six of the seven recalls and in 2.5% for the
    two-dimensional graph network's; the text said "in most draws" for any
    one recall. The test reads both figures from the record.
- Noted, not changed (none reachable with these arrays): scipy 1.18 gives
  p = NaN for a quantity whose per-instance values are all tied (1.17 gave
  1; Holm never rejects NaN, so the verdict is the same, but the verdict
  file would record "nan"); the guard's denominators are regularised at a
  reference mean of 0; the content check counts a non-finite value of the
  report as an infinite deviation (every pinned array is finite).
- The suite under the box's versions (Python 3.12.3, torch 2.12.1+cu130,
  numpy 2.4.6, scipy 1.18.0) before this change: 684 passed, 2 skipped (no
  LaTeX). RUNBOOK_CMAME's suite lines now read `684 passed, 3 deselected`.
  Suite 687 (686 + 1).

## Stage 11, stamp (18 Oct 2026) -- PREREG_HOLDOUT stamped before the run

- The sandbox scanned again before the stamp (PREREG_HOLDOUT Sec. 7), over
  the same directories: `python scripts/holdout_scan_sets.py /home/claude
  /tmp /mnt/user-data`, 18 October 2026 at 07:45 UTC, exit 0, within the
  bounds of Sec. 2. Three dimensions with a band of mesh sizes: 86 sets,
  the longest 80 (the cross-branch regression's miniature); three
  dimensions at one size: 85 sets, the longest 20; two dimensions: 49
  sets, the longest 80 (the regression's two-dimensional miniature). Two
  copies of the two-dimensional corpus's manifest, with no instance file
  beside them. Instance files without a manifest in 32 directories: corpus
  files 0 to 10 in two (copies from the authors' July 2026 archive, Sec. 2)
  and the suite's miniature labels in 30.
- `scripts/stamp_prereg_holdout.py --date "18 October 2026"`:
  CONFIG_SHA256[holdout_v1] = 0266f0d015bc7004512eb8f22de22b8dacc8afbe0b32c157c79c63710564af5a,
  the status line, and the file's SHA-256 in its last line,
  3d6680970c3298009f87549a8be1e35f75bec8a6d0cce69ecc30ffb079ee9a1c; read
  back and verified, and checked again apart from the script (the
  configuration's canonical hash, the self-hash).
- Tag `prereg-holdout`, annotated, on this commit, and no other tag on it.
  The branch is frozen until the run has returned. Suite 687.

## Stage 12 (20 Oct 2026) -- PREREG_K3D r1 draft: the 3D supervised transformer retrained with the stiffness-norm loss

- Purpose: CM2D's stiffness-norm control in three dimensions (decided 18
  October 2026). PREREG_CM2D showed in two dimensions that training the
  supervised transformer with the stiffness norm of the error (L_K) in place
  of the relative Euclidean displacement error (L_D), changing nothing else,
  lowers its relative energy gap and its von Mises error at 1,024 labels;
  the manuscript's explanation of the label-free network's lower stress
  errors by the norm of its objective had not been tested in three
  dimensions. K3D trains the L_K transformer on Phase-2's corpus, split,
  1,024 labelled instances, settings and seeds, beside Phase-2's L_D states
  and Phase-2b's label-free states, which are evaluated again (each must
  reproduce Phase-2b's per-instance values in the median) and not trained.
  Draft only: not stamped, not tagged.
- The decisions read the E-series guard on per-seed medians over the 256
  validation instances (H2a-3D: relative energy gap; H2b-3D: von Mises
  error; H3-3D, L_K against the label-free transformer, a reading). One
  validation instance (`instance_00485.npz`) carries the L_D reference's seed
  means (seed 1: relative energy gap 23,727): with seed means the reference's
  own SE_rel is 0.989, tau >= 1.98 and no reduction could be shown. The
  per-seed median is PREREG_CM2D's pre-registered robustness reading, whose
  two-dimensional values were known; other robust statistics spread alike.
  The statistic was chosen knowing the reference's values, before any L_K
  training in three dimensions; the seed-mean reading is reported beside
  every verdict. Operating characteristics by simulation
  (`scripts/k3d_sims.py`, `records/cmame/k3d_sims.json`): at the references'
  spreads, at L_K's two-dimensional ones, at wide new-arm spreads, and the
  two hypotheses together with correlated seed effects.
- `scripts/k3d_train.py` (configs/k3d_v1.json): one process on the box. Before
  the GPU is touched, the dry run included: the guard (the CONFIG_SHA256 line
  and the last line), the tag (a guarded run must be on `prereg-k3d` exactly)
  and the commit, the source report (Phase-2b's, by SHA-256, its embedded
  configuration by its own hash), the stored states (SHA-256 against the
  records they are copied from), the corpus manifest and the training
  instances' labels, the holdout set's labels manifest and every corpus and
  labels file it lists (SHA-256). Then a GPU that works and is free (no
  fallback to the CPU, exit status 2); a lock (one run at a time); the six
  stored states evaluated and content-checked (exit status 5 before any
  training); the three seeds trained in order exactly as E8's `labels_knorm`
  unit would train them (the model built right after seeding, the trainer's
  order, loss "knorm", E8's epochs and learning rate, activation
  checkpointing off as in the code that trained the L_D states); every state
  on PREREG_HOLDOUT's h3d set with the labels its run computed (the labels
  manifest recorded by SHA-256; `--skip-holdout` after its evaluation has
  failed in two consecutive attempts); the report. A restart is the same
  command: finished seeds and the stored states' evaluations are kept, an
  interrupted seed resumes from its epoch checkpoint if this code (`git
  describe` and commit), configuration and seed wrote it, anything else is
  moved aside. Every JSON file is flushed to the disk before it is moved
  into place; each seed records the machine (container, CPU model, GPU driver
  and UUID) and the torch build.
- `scripts/adjudicate_k3d.py`: the verdicts, the reading, the secondary
  readings (every metric, 30 comparisons on medians and means, instance
  pairs, zero-field counts, the share of the L_D-to-label-free gap that L_K
  closes, the labels+energy row's arrays, the holdout readings if the labels
  manifest the run used is PREREG_HOLDOUT's returned one, the training), the
  refusals (the content check recomputed from the arrays; the return's
  states, seed files and commits against the report) and the deviations of
  PREREG_K3D Sec. 6. `scripts/stamp_prereg_k3d.py`: the stamp, refusing a
  configuration that fails the run's own checks.
- The code that trained the L_D states against this code:
  `scripts/regress_supervised_rows.py` ran the regression's miniature of
  Phase-2's configuration on this code and on wp7-3d `e672110` and `99d3674`
  (the attempts that trained L_D at 1,024 labels): the supervised and naive
  rows' cells identical and the supervised states byte-identical; the
  label-free row differs, as D14 requires (`records/cmame/k3d/`). On CPU
  miniatures the script's L_K states are E8's `labels_knorm` states byte for
  byte, with activation checkpointing off or on.
- `src`: three changes, two from wp9-pool Stage 2 (PREREG_FINE3D r5): the
  supervised trainer keeps the loss of the last step of every epoch across a
  resume; an epoch checkpoint that cannot be read is moved aside while one
  that can be read but not restored stops the training (both were deleted);
  and `atomic_torch_save` flushes the file and its directory entry to the
  disk around the rename (the bytes written are the same).
  `scripts/regress_against_branch.py` against `wp8-lejepa` again: identical
  (`records/cmame/README.md`).
- Four independent reviews of the draft, each on its own clone: the code
  (one blocking finding: the end-to-end test expected a torch deviation that
  the box's own torch does not produce, so the suite would have failed in
  F0c; fixed, and the suite run under the box's torch version string), the
  pre-registration and its statistics (the disclosure of what was known when
  the median was chosen, the content check stated as it is, the joint and
  wide-spread rates, the share of the gap closed), the box procedure (the
  same blocking test; the rule for leaving the holdout set out, the exit
  statuses after a Ctrl-C, the health check, a full disk, the balance), and
  the decision rules implemented again from the text alone (227,417 cases;
  no disagreement a real run could produce; the rule's edges and the seed
  means' direction now defined in the text and the code). Every finding was
  taken up or answered.
- RUNBOOK_CMAME Sec. F: the box procedure (balance; fetch or bundle; the
  status check first; checkout on the tag; the holdout labels manifest and
  the memory limit; suite; dry run; the run in tmux with its status file;
  health check; interruptions; return) and the adjudication. The suite lines
  of A, D and F read the current count; E's stays at its tag's (684), which
  E0c runs.
- Sec. F rehearsed on the CPU with this package, its blocks as written but
  for the paths, the device and the suite collected only: a local remote
  with a rehearsal stamp and tag, a box clone at the previous commit with
  miniature inputs (Phase-2's stored states, the h3d labels); F0b by fetch
  and by bundle, F0c, F0d; F1 killed (no exit line) and pasted again, the
  stored states' evaluations and the finished seed kept; F2's return; F3's
  adjudication, verdicts written, the deviations those of the rehearsal (two
  attempts, results from the earlier one, the CPU and its torch). One change:
  the dry run's first line counts the holdout instances (it named them files).
- Three more independent reviews after the rehearsal, each on its own clone: the
  run's CUDA and box-scale paths (the 1,024 training instances meshed again
  exactly: GPU peak about 14-15 GiB of 31.4 at the largest, host memory about
  25 GiB, about 22-25 h per seed; L_K's path is the one the label-free and
  CM2D runs used on the box; the L_D regression records reproduced), the
  adjudication and the stamp (about 55 run-shaped returns, no crash, no false
  refusal, the guard's numbers by hand to 1e-12) and the operator procedure
  under failures (kills at every stage, a corrupted checkpoint, two copies, a
  stale lock, the holdout failing). No finding against the training or the
  verdicts. Changes: the values worse than the zero field listed and every
  epoch's loss in the verdict file (PREREG Sec. 5); deviations for TF32 in
  training, a return without reused.json, holdout readings not evaluated and a
  holdout skip that two holdout failures in the run logs did not precede;
  the stored states' SHA-256 hashed again as evaluated, and reused.json records
  the TF32 setting; the dry run writes a probe through the checkpoint writer on
  the box's disk and removes it. RUNBOOK F1' decides by the last line of
  status.txt, the run helper refuses to start a second copy (its process
  pattern anchored at the interpreter, so no other command line matches) or a
  run whose report exists (a block pasted twice), exit 3 or 5 looks for a
  running copy first, and the --skip-holdout block checks its own condition
  (three seed files, the last two logs ending in a holdout traceback; else NOT
  ALLOWED); F0a works in a tmux session Sec. E left open, and F1' stops on a
  full disk seen on the screen or by df. PREREG Sec. 6 states the return's
  required files and that the runbook names the failures run again once.
- Tests: `tests/test_k3d_train.py` (21), `tests/test_k3d_adjudicate.py` (42),
  `tests/test_k3d_prereg.py` (12), `tests/test_cmame_runbook.py` (+1). Suite
  763 (687 + 76).

## Stage 13 (25 Oct 2026) -- the returns of PREREG_HOLDOUT and PREREG_K3D committed as received, with their verdicts

- PREREG_K3D was stamped on 21 October 2026 before the run, on the commit
  that carries the tag `prereg-k3d` (`7614ae2`): CONFIG_SHA256[k3d_v1] =
  070bf83772b44e76cb249bb5f2e5f42507cd374551d2272233161d796f623433, and the
  file's SHA-256 in its last line,
  9e33f048e2093a65ef281bd061d84ea04dc0b8d567b411278ad410572fa913f2; that
  commit changed nothing else and added no entry here.
- The branch was frozen from PREREG_HOLDOUT's stamp until that run's return
  on 21 October 2026 (PREREG_HOLDOUT Sec. 7), took Stage 12's two commits
  after it (12:55 and 12:57 UTC), and was frozen again from PREREG_K3D's
  stamp until this return (PREREG_K3D Sec. 6). Both runs have now returned:
  the branch takes changes again.
- PREREG_HOLDOUT's run (RUNBOOK_CMAME Sec. E, 21 October 2026):
  `records/cmame/holdout/return/`, the return as received, and
  `records/cmame/holdout/verdict.json` (`scripts/adjudicate_holdout.py` with
  the tag checked out). Seven claims REPLICATED (T1, T2, T3, H1, H2b, H2c,
  D2); H2a NOT REPLICATED: L_K's relative energy gap against L_D's in two
  dimensions, on the 4,111 holdout instances, rel -42.9% with tau 47.4%
  (L_K's seeds 0.1298, 0.0213 and 0.0834). On per-seed medians L_K reads
  rel -81.4% against L_D (tau 13.4%): a few holdout instances carry its
  seed means (`records/cmame/README.md`). H3: no difference shown. V:
  REPRESENTATIVE. The adjudication records each of the four stages started
  twice, exits 2 and 0. `records/cmame/README.md` records two departures
  under PREREG_HOLDOUT Sec. 7: the first attempts ran on commit `8b5d443`,
  the box's checkout of RUNBOOK_CMAME Sec. D, which does not hold the
  script; and on 20 October 2026 a review of Stage 12 meshed the 1,024
  training instances of the three-dimensional corpus again in the sandbox
  (Stage 12 above reports it), a set beyond the bounds of Sec. 2, none of
  whose instances is in the tail from which h3d is drawn.
- The sandbox scanned again (`python scripts/holdout_scan_sets.py
  /home/claude /tmp /mnt/user-data`), 25 October 2026 at 12:22 UTC, exit 0,
  within the bounds of PREREG_HOLDOUT Sec. 2. Three dimensions with a band
  of mesh sizes: 73 sets, the longest 80; at one size: 72 sets, the longest
  20; two dimensions: 39 sets, the longest 80. Two copies of the
  two-dimensional corpus's manifest, with no instance file beside them;
  instance files without a manifest in 4 directories: corpus files 0 to 10
  of `runs/data2d` in two (Sec. 2's copies) and the miniature holdout
  labels of the Sec. F rehearsals (12 each) in two.
- PREREG_K3D's run (RUNBOOK_CMAME Sec. F, 22-25 October 2026):
  `records/cmame/k3d/return/` and `records/cmame/k3d/verdict.json`
  (`scripts/adjudicate_k3d.py` at the stamped commit, with PREREG_HOLDOUT's
  return and verdict committed on it locally: RUNBOOK_CMAME Sec. F3).
  H2a-3D SUPPORTED (relative energy gap, per-seed medians: rel -98.2%, tau
  11.7%); H2b-3D SUPPORTED (von Mises error: -83.6%, tau 10.0%); H3-3D: the
  stiffness-norm transformer lower beyond the guard than the label-free
  transformer (-41.0%, tau 27.0%). H3-3D's Welch 95% interval on the
  per-seed medians runs from -98.7% to +16.7%. No deviation. The
  container's memory limit, 90 GiB, is not the 92 GiB that PREREG_K3D Sec. 7
  and F0c give, and is above the 64 GB both require. Three of the verdict's
  input paths name the adjudicating clone: the script writes them from its
  own location. Both in `records/cmame/README.md`.
- The manuscript (`paper/cmame/`) is not changed here. Any revision reports
  both runs' verdicts and readings, and qualifies its statement of H2a
  (PREREG_HOLDOUT, Publication and Sec. 5; PREREG_K3D, Publication).
- RUNBOOK_CMAME: the suite lines of A0c and D0c read the current count;
  E0c's and F0c's keep their tags' (684 and 760), which
  `tests/test_cmame_runbook.py` now reads from the committed returns.
  Sec. E and F, and their adjudications E3 and F3, now say that they ran,
  as Sec. A to D do.
- One independent review of the package (the returns against their
  tarballs, both adjudications run again, every quoted number, the
  departures, the tests): nothing blocking. Its points were taken up: the
  window of PREREG_HOLDOUT Sec. 7 and what is known in it, the order of
  the stages, the times marked by their clock, the memory limit, the Welch
  intervals that PREREG_K3D Sec. 4 puts beside the verdicts, the reading
  beside H2a, and the wording of these notes and of the tests' summaries.
- Tests: `tests/test_holdout_records.py` (8) and `tests/test_k3d_records.py`
  (8): the returns whole and hashed, the attempts, the verdicts recomputed
  from the per-instance arrays without the adjudicators' code, the
  adjudications run again in process, and the numbers that
  `records/cmame/README.md` and this entry quote from the returns and the
  verdicts; `tests/test_cmame_runbook.py` changed. Suite 779 (763 + 16).

## Stage 14 (27 Oct 2026) -- the polynomial Ritz baseline and the enriched c*: box scripts, post hoc

- Why. CMAME declined the manuscript on 18 October 2026; it goes to the
  Journal of Computational Physics, whose guide asks that a problem other
  approaches have treated be compared with them. The manuscript compares
  its networks with exact solvers (the cost table) and with fitted
  baselines, but not with a classical approximation of the same order of
  size: a per-instance polynomial Ritz-Galerkin projection, which needs the
  instance's K and F and no label or training. This stage adds that
  baseline, post hoc, and the exploratory enriched c* reading that asks
  whether the networks carry information beyond such a polynomial space.
  Nothing here is pre-registered and no verdict reads either reading.
- The specification, fixed on 20 October 2026 (the project's note of that
  day, its Appendices 1 and 2), before any paired computation on the
  manuscript's instances, and after exploratory readings of the same
  construction on freshly drawn instances and on wp9's sets, which do not
  enter the manuscript. Appendix 1 (the baseline):
  - per instance, the Ritz-Galerkin projection on a vector polynomial
    subspace with the instance's own K and F: per displacement component
    the functions (x/W) L_a(2x/W - 1) L_b(2y/H - 1) [L_c(2z/D - 1)], L the
    Legendre polynomials, W, H, D the bounding box's edge lengths,
    a + b (+ c) <= p - 1; they vanish on the clamped face x = 0;
  - A = P^T K P pseudo-inverted by its eigendecomposition, the directions
    with eigenvalue at most 1e-13 times the largest dropped, no scaling; no
    label, no training, nothing tuned on the manuscript's instances;
  - the whole ladder reported: 3D p = 6, 7, 8, 9 (168, 252, 360, 495
    unknowns), 2D p = 6, 8 (42, 72);
  - the sets: the manuscript's 3D validation instances (256) and fine set
    (its first 256), its 2D validation instances (256), and PREREG_HOLDOUT's
    h3d (686) and h2d (4,111);
  - the manuscript's five metrics and the load cases worse than the zero
    field, with the repository's functions, against the same labels;
  - each instance checked against the records (its size and ||U*||_K per
    load case, relative difference at most 1e-6); one that differs is
    listed apart and left out of the pairing;
  - paired with every recorded model's per-instance values on the set: the
    share of instances on which the Ritz solution is better;
  - the timing of the Ritz work (P^T K P, the small solve, the
    reconstruction) apart from the assembly of K, the manuscript's cost-table
    row measured on the same kind of machine as the rest of the table;
  - the manuscript states that this is a classical baseline added after
    the CMAME decision, that its specification was fixed before any paired
    computation on the manuscript's instances, and that it was written after
    the exploratory readings; no pre-registered verdict changes.
  Appendix 2 (the enriched c*; exploratory, not in the manuscript):
  - models: wp9 session 2's 2D baseline (`b_n1024`) and S (`s_n1024`), and
    Phase-2b's 3D label-free transformer, three seeds each; sets: wp9's IB,
    F2 and F5 in 2D, the 3D validation instances and fine set;
  - the coarse space of Appendix 1 at 2D p = 6 (42 unknowns), 3D p = 8
    (360); per instance and load case the relative energy gap and the peak
    stress error of the network scaled by c*, of the Ritz solution and of
    the enriched c* (the Ritz projection on span{u} + range(P));
  - complementary when either holds: in band, for each of the three seeds
    the median enriched gap is at most 0.8 times the smaller of the medians
    of c* u and of Ritz; out of distribution, the enriched peak-stress
    error's median is at most half Ritz's.
- What the appendices leave open, decided in the code before any run on the
  box (and stated in the outputs: each summary's `solves`, each reading's
  `solves` and `choices`): the enriched system is solved with Jacobi
  scaling and the eigenvalues at most 1e-12 times the largest dropped (the
  reference script's solve), while its Ritz solution is Appendix 1's;
  per-instance values are the means over the load battery (as the records
  hold them), the per-load-case medians beside them; the out-of-distribution
  condition must hold for every seed and set; arms are read separately; the
  reading is "complementary" when a computed condition holds, "not" when
  both are computed and neither holds, null otherwise; it is given over
  every instance and, when an instance fails the identity check, over those
  that pass; a set whose network does not reproduce its records is left out
  of it; the enriched gap's excess over the smaller of c* u's and Ritz's,
  round-off by construction, is flagged above 1e-8 (`bound_ok`). Beyond
  Appendix 2, as the hand-over of 20 October 2026 allowed: Phase-2's
  labels-only transformer (L_D) and graph network and PREREG_K3D's L_K, on
  the 3D sets, read the same way and marked `"appendix": false`.
- Code. `src/fejepa/analysis/ritz.py`, the construction and the projections
  (checked against the sandbox reference that two reviews checked on 20
  October 2026: bitwise equal on a 2D and a 3D instance; that reference is
  not in the repository);
  `scripts/ritz_baseline.py`, `scripts/enriched_cstar.py` and
  `scripts/ritz_timing.py`; `configs/ritz_v1.json`, every input with its
  SHA-256. They read the box's own files and labels (nothing is solved
  again): the corpora by their manifests as the reports record them, the
  holdout sets as PREREG_HOLDOUT's run checks them (with the labels
  manifests its return carries), wp9's sets by the per-file SHA-256 of their
  manifests and wp9's two reports by the SHA-256 of wp9-pool's records
  (Stage 1, `2f35f2d`; the model and feature code that session 2 ran,
  `92dfc93`, is this branch's apart from the stiffness-norm loss and the
  structured-mesh fix, neither of which these models use). Every input is
  checked before any computation (`--check` does only that); the identity
  check runs on every instance; the instance order of the pairing sources
  is checked where two sources share values (Phase-2b's arrays against the
  identity record's own per-seed values; the label-free states' rows where
  two reports evaluated the same states, R4's against Phase-2b's and E1's
  against CM2D's; the deterministic rows across reports, which align every
  row of the July runs; the holdout arrays' file lists), and rests on the
  recorded split and fine set otherwise (E2's two reports on both 3D sets,
  E1's other two runs); the enriched reading first checks every model on 8
  instances against its report's per-instance arrays (tolerance 1e-3, as
  PREREG_HOLDOUT's content check) and again on the whole set; worker
  processes compute the instances and the rows are written in order, so
  that a run cut off resumes. Exit statuses are documented in each script.
- `src` gained that one module, which nothing else in `src` imports.
  `scripts/regress_against_branch.py` against `wp8-lejepa` ran again on 27
  October 2026 (both miniatures, as at Stages 9, 11 and 12): identical,
  apart from this side's tree; `records/cmame/README.md` and the two
  summaries name the new tree, which `tests/test_w9_records.py` checks
  against the committed `src`. PREREG_K3D's two regression records
  (`records/cmame/k3d/`, its Sec. 7 evidence) name the code that run used
  and stay as committed: `tests/test_k3d_prereg.py` now reads their tree
  from the README's K3D section, and checks it against the return's commit,
  where it read the table, which names the current code.
- The cost table. It was measured on 8 October 2026 on an Intel Xeon Gold
  6459C (16 CPUs); the box has since been an Intel Xeon Platinum 8470Q (25
  CPUs). RUNBOOK_CMAME Sec. G therefore runs the table's own measurements
  (`scripts/time_inference_vs_solve.py`, Sec. A's two commands) again on
  the box, beside the baseline's timing on the same instances (the first 32
  validation instances and 8 of the fine set, 4 instances of warm-up, one
  process, the machine's thread settings).
- RUNBOOK_CMAME Sec. G: the checks, the fifteen steps (the baseline's five
  sets, Appendix 2's three arms, the four timing steps, then the three
  models beyond Appendix 2), interruptions, the return and the repository
  side (each summary rebuilt from its rows, each reading from its
  summaries). The suite lines of A0c, D0c and G0c read the current count.
- Disclosed: on 21 October 2026, 12:59 to 14:59 UTC, a sandbox run of
  Appendix 1 on the fine set, regenerated from its generator's stream and
  labelled by AMG-preconditioned CG, reached 78 of its 256 instances before
  it was stopped, when it was decided that every computation runs on the
  box; 14 of the 78 failed the identity check against the records (the
  sandbox's meshes are not the box's to round-off, up to 8.5e-6). Its
  per-instance gaps were printed in its log; no model was paired with them,
  and none of its rows is used.
- One independent review of the package (the specification, the box's
  safety, the pairing against the records, the runbook pasted as written,
  the tests, the costs on instances of the fine set's size): nothing
  blocking. Taken up: the timing's repetitions decided by the first run, as
  the cost table's; one physical line per step in G1, so that G1' can paste
  steps again; the instance order checked where sources share values; the
  thread pools recorded with the timing; the bound flagged; the solves and
  the reading's choices written into the outputs; E1's states in G0c; the
  time estimates.
- Tests: `tests/test_ritz.py` (11; the construction and the projections on
  a 2D and a 3D instance), `tests/test_ritz_config.py` (6; the configuration
  against the records, the pairing sources and their instance order),
  `tests/test_ritz_scripts.py` (12; the three scripts end to end on a
  miniature box, with refusals, resumption, worker processes and the
  repository side; the timing's repetition rule),
  `tests/test_cmame_runbook.py` (Sec. G) and `tests/test_k3d_prereg.py` (the
  K3D records' tree, above). Suite 809 (779 + 30).

## Stage 15 (29 Oct 2026) -- the return of RUNBOOK_CMAME Sec. G committed as received: the Ritz baseline and the enriched c*

- What. The return of Sec. G's run of 28 October 2026 on the box, under
  `records/cmame/ritz/`: the tarball as the operator sent it
  (`ritz_return_20261029-1150.tgz`, 23,818,923 bytes, SHA-256
  `c0f5621fac38e8a946c34c7870a6c284305e2c2f0ccec29b24946a0f984c96af`) and its
  50 files other than the per-instance rows, unpacked beside it byte for byte
  (`ritz/return/`). The 19 rows files (81 MB unpacked, the largest 19.6 MB)
  stay in the tarball: earlier returns were committed unpacked, with their
  tarballs left out and their SHA-256 recorded; here the tarball itself is the
  record (decided on 29 October 2026). `records/cmame/README.md` gives the
  return, the checks and the readings.
- The run. The branch at `0c1d59a` (tree
  `d36f70537aadbf7a98e1a265aebea6daaa111b0b`, `git describe`
  `prereg-k3d-2-g0c1d59a`), on the host of PREREG_HOLDOUT's and PREREG_K3D's
  runs; G0c's suite 806 passed, 3 deselected; G0d's eleven lines; the fifteen
  steps of G1 in order, each with one start line and `exit=0`, from
  2026-10-28T17:26:48Z to about 20:29; no memory event.
- Checked on receipt, on 29 October 2026: every file against the return's
  `provenance.txt`; every summary rebuilt from its rows and the records and
  every reading from its summaries, all 25 files identical byte for byte
  (wp9's two arms with wp9-pool's records copies of their reports, at the
  SHA-256 that `configs/ritz_v1.json` pins); every set's rows numbered 0 to
  n-1, no file twice; the enriched reading's Ritz rows against the baseline's
  p = 8 within 1.3e-10. The 5,565 instances of the baseline passed the
  identity check (largest relative difference 2.5e-12); no direction was
  dropped; no Ritz solution was worse than the zero field on any load case;
  every network reproduced its report.
- The readings (the README's tables give them). The baseline: on val3d the
  Ritz solution's displacement error is the lower, against the label-free
  transformer, on 67% to 79% of the instances at p = 6 and on 99.6% to 100%
  at p = 9; its relative energy gap on 0.4% to 6% at p = 6 and on 38% to
  100% at p = 9, by seed; its peak von Mises error on at most 2% at every p.
  Against L_K, on at most 10.2% in the relative energy gap (at p = 9) and on
  none in the peak von Mises error. Against the supervised transformers
  trained on the displacement error, with or without the energy term, the
  graph networks and the deterministic baselines, its relative energy gap is
  the lower on every instance at every p, on every set. The enriched c*:
  Appendix 2's three arms are not complementary; beyond Appendix 2, L_K is
  (out of distribution, the fine set's ratios 0.418, 0.250 and 0.408), and
  Phase-2's labels-only transformer and graph network are not.
- Fixed before the run, in the project's note of 27 October 2026 (the check
  of the pushed code before the operator instruction was sent), and done as
  written:
  - a sensitivity reading of Appendix 2 on the per-load-case medians beside
    the reading (the summaries carry them): for every arm it reads as the
    reading does;
  - the check that every set's rows are numbered 0 to n-1 without repeats;
  - the code's choices that Stage 14's list leaves out, stated here: (1)
    val2d's identity check reads its free-dof count, Sec. D's spectral export
    carrying no node count, and h3d's and h2d's ||U*||_K is
    sqrt(-2 Pi_h(U*)) from PREREG_HOLDOUT's arrays (the labels' relative
    residuals at most 5.3e-11, so that the two agree to about 1e-10); (2) an
    instance that fails the identity check is left out of its set's medians,
    means and worse-than-zero counts (`n_used`), not only of the pairing
    (none failed); (3) "better" is strict, ties counted apart; (4) val2d's
    pairing leaves out wp9-pool session 2's five reports on the same
    instances (the rule of 2 October 2026; the summary's `not_paired`); (5)
    P^T K P is formed once at the largest p and each smaller p takes its
    principal sub-block, the solution of a separate solve at that p; (6) W, H
    and D are the instance's metadata, checked against its nodes (the mesh
    spans [0, W] x [0, H] (x [0, D]) and every Dirichlet dof sits on x = 0,
    within 1e-8, the step stopping otherwise), which every generator's
    placement rule guarantees, holes and cavities being kept off the
    boundary; (7) the timing's `ritz_s` includes the extraction of the free
    block and the basis, and the 2D assembly builds the load battery too.
- Decided on 29 October 2026 by the PI:
  - the manuscript's cost table takes every row from the measurements of 28
    October 2026 on this host, the Ritz row among them with its assembly
    apart; those of 8 October 2026, on the earlier host, agree in every
    accuracy value and are mentioned in the supplementary material;
  - the manuscript reports the baseline as Appendix 1's last item asks,
    with one change: it states that this is a classical baseline added post
    hoc, after the original analyses, that its specification was fixed on 20
    October 2026 before any paired computation on the manuscript's
    instances, that it was written after exploratory readings on freshly
    drawn instances and on wp9's sets, and that no pre-registered verdict
    changes; the occasion of the addition that the item names (Stage 14) is
    not stated.
- `src`, the configurations and the scripts are unchanged. RUNBOOK_CMAME
  G3 gains the date of the run; the suite lines of A0c, D0c and G0c read the
  current count.
- Tests: `tests/test_ritz_return.py` (11): the tarball and its members, the
  unpacked files against them, `provenance.txt`, the fifteen steps and the
  checks of G0c and G0d, the rows, the identity and the Ritz solutions, the
  summaries and readings rebuilt in process and compared byte for byte (the
  baseline's, the three-dimensional arms', every reading), the README's
  statement on the models whose energy gap the Ritz solution beats on every
  instance, the sensitivity reading, and the README's and these notes'
  quotes. Suite 820 (809 + 11).

## Stage 16 (29 Oct 2026) -- the manuscript revised: the held-out instances, the three-dimensional stiffness-norm run and the Ritz baseline; the branch renamed

- The branch. Renamed from `cmame-paper` to `statics-paper` on GitHub on 29
  October 2026, after Stage 15 was pushed (decided by the PI that day). Its
  commits and tags are unchanged, and GitHub redirects the web addresses of
  the old name. The stamped pre-registrations, `configs/ritz_v1.json` and
  Sections A to G of RUNBOOK_CMAME name the old branch, as they ran;
  RUNBOOK_CMAME's opening now says so. `paper/cmame/`, `records/cmame/` and
  the files named after them keep their names: stamped documents and pinned
  configurations name them.
- The manuscript (`paper/cmame/`), as decided by the PI on 29 October 2026:
  - The holdout evaluation (PREREG_HOLDOUT) in a new Section 7: its claims, H3
    and V with their values on both sets (`table_holdout.tex`), and in
    Appendix A the means and medians of both sets (`table_holdout_values.tex`),
    the run and its two departures. H2a, which did not replicate, is qualified
    in Section 6.2 with its held-out values and the readings beside it, as its
    Sec. 6 requires of any version of the paper written after the evaluation.
  - The three-dimensional stiffness-norm run (PREREG_K3D) in a new Section 5.6
    with its table (`table_k3d.tex`) and in Table 2; the seeds' medians and
    means and the 30 secondary comparisons in the supplementary material.
    Section 5.6, Appendix A and the limitations state that the statistic was
    fixed after the reference's per-instance values were known, and why.
  - The Ritz baseline (Stage 14's Appendix 1; the return of Stage 15): the
    method in a new Section 4.5, its rows at every degree in Tables 2, 5 and
    7, the paired shares in Sections 5.7, 6.1, 7 and 8.1 and, for every set,
    model and degree, in the supplementary material (`table_ritz_pairs.tex`).
    As decided at Stage 15, the text states that it was added after the
    original analyses and not pre-registered, its specification written on 20
    October 2026, after exploratory readings, and committed on 27 October
    2026, public before any paired computation on the manuscript's instances
    (28 October 2026), and that it changes no pre-registered verdict.
  - The cost table (Table 10) takes every row from the measurements of 28
    October 2026 on the host of the Ritz run, the assembly and the Ritz
    projection in rows of their own, and states the fine-mesh direct solve's
    budget (seven of eight instances solved); the threads' readings and the
    measurement of 8 October 2026 move to the supplementary material.
  - The abstract (247 words), the highlights (five, at most 85 characters),
    the introduction, the related work (Larson et al., arXiv:2412.04596v3,
    whose SIAM version's journal, volume and pages are to be checked; Barucq
    et al. 2026), the discussion, the conclusion and the graphical abstract
    follow.
  - `\journal` names the Journal of Computational Physics. The Data
    availability statement names the version described by the tag
    `statics-paper-1.0` and its archive at Zenodo, whose DOI is pending (a
    box in the statement; `references.bib` and `CITATION.cff` gain it when
    it is reserved). Appendix C prints the records' paths relative to
    `records/` and refers to the README, which gains a section naming the
    generation script, its outputs and its tests.
  - New: `supplementary.tex`, the supplementary material (Tables S1 to S3,
    the threads and the earlier timing).
- An independent review of the revision (29 October 2026, read only; the
  numbers recomputed from the records with its own scripts) found every
  number right. Its points on wording, scope and disclosure are addressed:
  the abstract, introduction and conclusion qualify the K3D verdicts by
  their statistic and add the share of the gap closed (PREREG_K3D Sec. 5,
  105.0% in von Mises error and 101.3% in relative energy gap on the
  medians); "every supervised network" reads "every network supervised on
  the displacement error", and the held-out replication names the networks
  without stored weights; the Ritz baseline is labelled post hoc wherever
  it is reported, its specification dated by its commit (27 October 2026),
  public before the run; the Ritz statements are restricted to three dimensions where they
  are, read network by network, and qualified for peak stress on the finer
  mesh; Section 7 reports PREREG_HOLDOUT Sec. 6's two-dimensional counts of
  predictions worse than the zero field and states that the verdicts are not
  independent, and the seeds' largest gaps are labelled as read after the
  evaluation; Table 2's note, Appendix A's content check and its account of
  the review of 20 October 2026 are corrected; the tag drops "v2"; the
  metric is called the peak stress error throughout; the notation of the
  Ritz basis follows the paper's.
- `src`, the configurations and the records are unchanged.
- Tests: `tests/test_cmame_material.py` gains four (the K3D numbers and table
  recomputed from the report and its holdout arrays, the share of the gap
  closed included; the holdout numbers and every cell of Table A.3 from the
  evaluation's arrays and manifests; the Ritz numbers and rows from its
  summaries; that the sources name no journal but the one of `\journal` and,
  in their journal fields, the references', print `records/cmame/` once and
  speak of no earlier submission or version); its cost-table test reads the
  timings of 28 October 2026 and the Ritz timings, its highlights test ties
  the lines to the records, its test of hand-typed numbers reads the
  supplementary material too, and its build test builds the supplementary
  material and checks that the graphical abstract's text ends on its page
  (text pushed off the page is clipped without a warning).
  `tests/test_cmame_references.py` and `tests/test_repository_transfer.py`
  read the new tag and the pending DOI. RUNBOOK_CMAME's suite lines read the
  current count. Suite 824 (820 + 4).

## Stage 17 (29 Oct 2026) -- the manuscript restructured around the norm of the loss against the labels; supplementary material S1 to S10

- As decided by the PI on 29 October 2026 (the assessment of the paper's narrative for the
  Journal of Computational Physics, option A), the manuscript's main line is which norm to
  train and evaluate finite-element surrogates in. Title: "The norm, not the labels:
  training and evaluating finite-element surrogates in the energy norm". The stiffness norm
  is called the energy norm throughout, and the networks are named by their loss: the
  displacement-supervised, the energy-norm-supervised and the label-free transformers, and
  the graph network. No run, number or verdict changed; the records are unchanged.
- Structure: 1 Introduction; 2 Related work (paragraphs on the norm of the loss and on error
  estimation without the solution; 17 references added, checked on 29 October 2026 against
  the bibliographic records their comments name); 3 Energy, norm and stress; 4 Problems,
  networks and comparisons; 5 The norm of the loss (the 3D energy-norm run, H2a and H2b,
  the spectra); 6 Training without the solutions (the 3D comparison, H1 and H3, fewer
  labels); 7 Evaluation in the energy norm (the reversal of the rankings, predictions worse
  than the zero field); 8 Held-out instances; 9 A classical baseline and the cost; 10
  Discussion; 11 Conclusion; Appendix A the pre-registered claims (`table_claims.tex`, new).
- New Fig. 1 (`fig_norm_labels.pdf`): the same transformer in the two-by-two of norm and
  labels, one cell empty, in both dimensions, with the medians over the validation instances
  of the relative energy-norm and von Mises errors averaged over the seeds (`numNl*`); the
  generator checks every statement the text makes about them, and a new test recomputes
  them from the reports.
- Moved to the supplementary material, nothing deleted: the pre-registration record with the
  list of runs (S1), further 3D and 2D results (S2, S3), the transfer (S4), the warm starts
  with their corollary and remark (S5), the side experiments (S6), the July run (S7),
  reproducibility with the conditioning lemma and the modewise corollary (S8), the Ritz pairs
  (S9) and the timing (S10). The paper cites these sections by the numbers in
  `suppsections.tex`, which the supplementary material checks as it is built; the
  supplementary material reads the paper's labels from `main.aux` and numbers its own
  references [S1], [S2] and so on. `sections/results3d.tex` and `sections/results2d.tex` are
  removed (their content is in Sections 5 to 8 and the supplementary material);
  `sections/holdout.tex` is Section 8; the schematic figure is dropped.
- Front matter: one corresponding author (Ruifeng Cao); keywords, highlights and the
  graphical abstract redrawn around the norm and the labels.
- Dates: the three-dimensional comparison ran from 22 to 28 September 2026 and reused the
  supervised networks that its initial run (31 August to 21 September 2026) had trained in
  the first half of September; the text and Table S1 now say so.
- An independent review of the restructured text (29 October 2026, read only; the numbers
  resolved and checked against the records) found the energy-norm statement of the abstract
  off by a factor of two, two statements stronger than the numbers (the factor 1.3 holds for
  the median energy-norm and von Mises errors only; the Ritz projection beats the label-free
  transformer in the seed means, not in every seed), a 2D-only spectral reading stated
  generally, and a sentence on the 3D label budgets that the energy-norm-supervised
  transformer contradicts; all are corrected, and the generator now checks that the Ritz
  projection's median peak stress error at the top of its ladder is more than twice the
  label-free transformer's in each seed, and quotes the Welch interval of the 3D seed-mean
  von Mises reduction (it includes zero). Its other points on caveats, terms, dates and
  length are addressed: each caveat is stated with its result, the held-out instances are
  a section of their own after the evaluation, and the main text is shorter by the moves
  above.
- Tests: `tests/test_cmame_material.py` gains one (Fig. 1's numbers recomputed from the
  reports) and checks the claims table, the new names, the highlights, the Ritz projection
  against the networks at the top of its ladder and the Welch interval; the quotes of
  `tests/test_cmame_references.py` follow the text to the supplementary material.
  RUNBOOK_CMAME's suite lines read the current count. Suite 825 (824 + 1).

## Stage 18 (29 Oct 2026) -- the manuscript's directory, its generator and tests, the runbook and these notes renamed after the branch

- At the PI's request of 29 October 2026, the files named after the branch's old name are
  renamed after its new one, with `statics` in place of `cmame`: `paper/cmame/` is
  `paper/statics/`, `RUNBOOK_CMAME.md` is
  `RUNBOOK_STATICS.md`, `BRANCH_NOTES_cmame-paper.md` is `BRANCH_NOTES_statics-paper.md`,
  `scripts/make_cmame_material.py` is `scripts/make_statics_material.py`, and
  `tests/test_cmame_material.py`, `tests/test_cmame_references.py`,
  `tests/test_cmame_runbook.py` and `tests/test_cmame_timing_records.py` are
  `tests/test_statics_material.py`, `tests/test_statics_references.py`,
  `tests/test_statics_runbook.py` and `tests/test_statics_timing_records.py`.
- Not renamed: `records/cmame/`, whose paths the stamped pre-registrations (PREREG_CM2D,
  PREREG_HOLDOUT, PREREG_K3D), the configurations `configs/holdout_v1.json` and
  `configs/ritz_v1.json` and the adjudicators, whose SHA-256 the verdicts record, name, and
  by which the records list their inputs; and the tag `cmame-submission`, which
  PREREG_HOLDOUT and `records/cmame/holdout/pool_depths.json` name. The stamped documents,
  the configurations, the scripts and `src`, the records, the entries of these notes before
  this stage, Sections A to G of the runbook and the docstrings of the tests not renamed keep
  the old names as they were written; the runbook's opening says how to read its commands
  on a later commit, and `records/cmame/README.md` opens with the new names of the files it
  names.
- Updated to the new names: the README's section on the paper, which now also names the
  runbook and these notes and says that documents written before 29 October 2026 use the
  old names; the openings of the runbook and of these notes; `records/phase1/README.md`;
  the generator (its output directory, its docstrings and the name that `sources.json`
  records); and the tests that read the renamed files.
- The list of hashes in Section S8 of the supplementary material says that the records of
  the runs of October 2026 are kept in one subdirectory of `records/`, without printing its
  name. No other text or number of the manuscript changed, and no figure was regenerated.
- Stage 17 as pushed (`6640672`) lacked two of its changes: `sections/results2d.tex` and
  `sections/results3d.tex`, no longer read, were still there, and the runbook was Stage
  16's, whose suite lines read 821, so that `test_the_runbook_states_the_suite_count`
  failed there (824 passed and 1 failed on a fresh clone). This stage removes the two files
  and states the current count.
- Tests: `tests/test_statics_material.py` gains one (no file or directory at the top of the
  repository or in `paper/`, `scripts/` and `tests/` carries the old name, and in `records/`
  only `records/cmame/` does), and its test of the manuscript's sources allows no exception
  now; `tests/test_statics_runbook.py` finds the tests that Sections A to G deselect under
  their new names and checks that the runbook's opening says how to read them. The
  runbook's suite lines read the current count. Suite 826 (825 + 1).

## Stage 19 (30 Oct 2026) -- figure captions and table notes shortened; the paper checked against the Guide for Authors

- At the PI's request of 30 October 2026. The journal's Guide for Authors asks for a caption
  of "a brief title" and "a description of the image", with "the amount of text" kept "to a
  minimum", and places table notes below the table body. In seven papers that the journal
  published between 2019 and 2025 (their versions on arXiv), the figure captions have a
  median of about 25 to 60 words and no table has more than a caption above it; here the
  main text's six figure captions had 64 to 152 words (median 101, words counted as the
  test below counts them), and its five tables 113 to 315 words of notes below them. They
  now have 24 to 80 words (median 57), and the tables 0 to 60.
- Figures: each caption gives a title, what is plotted and the symbols. What the captions
  said beyond that is in the text: that removing the solutions also changes the weighting
  of the load cases and the learning rate, and the factors on the means over the instances
  (Section 1); which networks Fig. 3 shows at which budgets (Section 6.3); where the
  networks lie in Fig. 4 and which instance is at its top right, and the rule that chose the
  instance of Fig. 5 (Section 7.1); the selection rules of Figs. S2 and S3 (Sections S3 and
  S4). The field plots' captions state that values above the reference's maximum saturate.
- Tables: each caption says what the table holds and which statistic; the notes keep only
  what concerns a row or a column. The definitions of the metrics are those of Section 4.4;
  the noise guard, now Eq. (A.1), and the gates and kill conditions are in Appendix A; the
  protocol of the cost table is a paragraph of Section S10 (`cost_protocol.tex`); the
  conventions of the criteria and the definitions of the Welch and resampling intervals are
  in the text of Section S1; the readings beside Tables S10, S11 and S13 are paragraphs of
  Sections S4 and S6 (`amplitude_readings.tex`, `remesh_readings.tex`, `e2_readings.tex`);
  the pairing rules of Table S16 are in Section S9, and the few-shot settings in Section S4.
  No number changed, and no figure was regenerated.
- The Guide checked sentence by sentence: Section 3's inline fraction uses the solidus, the
  display of Appendix A is numbered, captions refer to sections rather than to "the text",
  Table 3 is first cited after Tables 1 and 2 (Section 4.6 now cites Section 8), and Prager
  and Synge (1947) carry their DOI, read from the MaRDI record of the article. Larson et al.
  are cited in their version of record, SIAM Journal on Scientific Computing 48(5), pages
  C1192 to C1219, checked against the article that the PI supplied; what the text states of
  it holds for that version.
- An independent reading of the change against the Stage 18 text found what the shortening
  had lost or blurred; each is restored from the same records. Section S6.1 and Table S2
  give the accuracy criterion of the latent-regularisation run again, its two relative
  changes and their guard; Section S6.1, the caption of Table S12 and Section S8 say that
  its untrained networks were measured after the runs, and how they were built. The caption
  of Table 3 and Section 4.6 say that Table 3 holds the claims that the holdout evaluation,
  itself pre-registered, read again, not the comparisons' pre-registered claims. The caption
  of Table 4 defines CG and says which rows are medians over the load cases; its note and
  Section 9.2 say that the fine-mesh direct solve had one budget for all its instances. The
  raw-token variant of Table S12, the holdout rows of Table S6 and the deterministic rows of
  Tables 1 and 2 are named; three paragraphs of Sections S4 and S6 are reworded; Tables S4
  and S14, Fig. S3 and the statements of Tables A.1 and S2 point again to what they use.
- Tests: `tests/test_statics_material.py` gains two: figure captions at most 90 words,
  table captions at most 80, notes at most 60 words below a table of the paper and 40 in
  the supplementary material; and the accuracy criterion of the latent-regularisation run
  recomputed from the per-seed values of its two reports, with the noise guard of Eq.
  (A.1). It regenerates the four paragraphs byte for byte with the tables, and checks the
  cost table's two notes and its protocol's statements. The runbook's suite lines read the
  current count. Suite 828 (826 + 2).

## Stage 20 (30 Oct 2026) -- the paper checked again against every sentence of the Guide for Authors

- At the PI's request of 30 October 2026 the paper was checked again against the journal's
  Guide for Authors, split into its 497 sentences and list items, in two passes made
  independently of each other; what follows is what the manuscript could change.
- Formulae: the eleven inline formulae of Section 3 that still set a small fraction with a
  horizontal line use the solidus; the displays keep theirs.
- Headings: the paragraph headings of Sections 2, 4.1, 4.2 and 10 become numbered
  subsections (2.1 to 2.5, 4.1.1 to 4.1.3, 4.2.1 to 4.2.3, 10.1 to 10.6); those of the
  supplementary material stand on a line of their own.
- Captions explain every symbol they show: delta, g and Pi_h(u) in Fig. 5, lambda_m and
  R(U*) in Fig. 2, delta and c* in Fig. S3, M in Fig. S4; c* in Table 4, p in Tables 1 and
  2, M in Table S13.
- Cross-references: four pointers "above" or "below" without a number are replaced by
  numbers or by what they pointed to (Sections 2, S1, S5 and S8); Table S1's caption no
  longer says "the text"; Section S1 no longer cites Fig. S2 before Fig. S1.
- Generative AI: Section 4.6 names the models with which the generation script and the
  code of the experiments were written, as Elsevier's policy asks of data visualisations
  made with AI tools; the declaration says that the tools also reviewed the code and that
  no image was generated or altered by them; Section S1 says that the review of 20 October
  2026 was made with them.
- Section 4.3 names PyTorch and says that each run's report records the versions of
  Python, PyTorch, NumPy and SciPy it ran with; Section 4.6 cites Eq. (A.1) where it
  introduces the noise guard; "sanity" in the paper's own words becomes "plausibility"
  (the pre-registrations keep their term); the abstract says "averaged over the seeds".
- The main figures are set at the width they are drawn at, 17.8 cm, centred into the
  margins, so that their lettering prints at its drawn size rather than at 77 per cent of
  it (`\figfull` in `main.tex`).
- References: the five conference papers given with an OpenReview or proceedings address
  carry the date on which it was added, 10 October 2026, as the date it was last
  accessed; Ainsworth and Oden (2000) carry the DOI of the book's online edition, read from
  the Technical University of Munich's library catalogue.
- Tests: `tests/test_statics_material.py` gains three (inline formulae use the solidus;
  the manuscript's headings are numbered and those of the supplementary material stand on
  a line of their own; Section 4.6 names the models of the generative-AI declaration), and
  its filter of the prose skips `\figfull`. The runbook's suite lines read the current
  count. Suite 831 (828 + 3).

## Stage 21 (30 Oct 2026) -- the declaration of competing interest, the archive of the trained networks, the volume of PINO

- At the PI's decisions of 30 October 2026 the declaration of competing interest declares
  the first author's commercial licences, in the wording of the journal's declarations
  tool: he holds the copyright in the code and offers licences for commercial use of the
  code and of the trained networks, both licensed for non-commercial use only. It declared
  none before, while the Data availability statement offered commercial licences.
- The trained networks whose states the records name with their SHA-256 hashes, 34 files,
  were collected from the training machine on 30 October 2026 after a check there against
  those hashes, and are to be archived at Zenodo under CC BY-NC 4.0 (`Cao2026Networks`, a
  data reference like the archive of the code, with the same author and version; its DOI is
  reserved before submission, and until then a pending box in the Data availability
  statement says so). The statement says that the other networks, the meshes and the
  reference solutions are not archived, and how they are regenerated; supplementary
  Section S8 points to it.
- Li et al. (2024) carry their volume, issue and article number (1, 3 and 9), checked
  against the published article.
- Tests: `tests/test_statics_references.py` gains two (the networks' archive is a data
  reference cited with its licence and its pending DOI; the volume, issue and article
  number of Li et al.), and its rendering test renders both entries;
  `tests/test_statics_material.py` gains one (the declaration of competing interest
  declares the commercial licences that the Data availability statement offers), and the
  licence's name joins the names with versions; `tests/test_repository_transfer.py`
  expects the second pending box. The runbook's suite lines read the current count.
  Suite 834 (831 + 3).

## Stage 22 (30 Oct 2026) -- the DOIs of the two archives

- The DOIs of the archive of the version described and of the archive of its trained
  networks were reserved at Zenodo on 30 October 2026: 10.5281/zenodo.23815187 for the code
  (`Cao2026Zenodo`) and 10.5281/zenodo.23815225 for the networks (`Cao2026Networks`). Both
  are new records, independent of the repository's first archive (10.5281/zenodo.23298799),
  filled by hand and published before the paper is submitted. The Data availability
  statement gives each DOI after the citation of its archive, in place of the two pending
  boxes, and the references carry them; no pending box is left in the manuscript.
- The archive of the networks also holds the three label-free networks of the July run,
  whose SHA-256 hashes the provenance note gives (Run 1), 37 networks in all; they were
  checked against those hashes on the PI's computer on 30 October 2026.
- An independent check of the archive's README against the repository found that the
  records name the states of 40 networks with their hashes, not 34: the Ritz baseline's
  records also name six label-free networks of a separate study (`configs/ritz_v1.json`,
  the arms `b_n1024` and `s_n1024`, read in its appendix readings), which the paper does not
  report and the archive does not hold. The statement of Stage 21 said that the networks
  whose states the records name are archived; it now says that, of the networks trained in
  the runs reported here, those whose states the records and the repository's provenance
  note name are archived. It said that the other networks can be retrained with the code of
  the versions that the records name, while the reports of the July runs record no version
  (the provenance note names them) and the initial three-dimensional run has no committed
  report (the list of deviations names its code); it now says the configurations, seeds and
  versions of the code that the repository records. It also said that the meshes are
  regenerated up to rounding differences between machines, while a fine mesh regenerated on
  another machine in August 2026 differed in 6 of its 97,790 tetrahedra and gmsh's sizing is
  version-dependent (`BRANCH_NOTES_wp7-3d.md`, G1.1 and G1.2); it now says that they are
  regenerated not necessarily bit for bit, since a mesh can differ slightly between machines
  and between versions of the mesh generator. A corpus manifest's hash would not show such a
  difference: the manifest lists each instance's numbers of nodes and holes, not its mesh.
- CITATION.cff gives the version described, the DOI of its archive and the archive of its
  networks; it no longer names the first archive, whose description named the tag of that
  earlier version.
- Tests: `tests/test_statics_references.py` and `tests/test_repository_transfer.py` check
  the two DOIs in the references, the statement and CITATION.cff, that no pending box is
  left, and that the provenance note gives the three hashes; the networks' test also walks
  the records for the hashes they give under a state's name (40, six of them those of the
  separate study) and checks the evidence of the two other corrections; the rendering test
  renders both DOIs; the two DOIs join the names with versions in
  `tests/test_statics_material.py`. Suite 834 (831 + 3), unchanged.

## Stage 23 (31 Oct 2026) -- a reading before submission: the prior comparison of loss norms, the finer mesh's energy-norm network, the largest errors, and five statements

- Why. A reading of the Stage 22 manuscript before submission raised points that the
  committed records answer without a new run. Every new number is generated from the
  records and recomputed by the tests; nothing here changes a pre-registered verdict, and
  the readings added are marked as taken after the runs.
- The related work. Section 2.2 said that no comparison changing the norm of a supervised
  loss while keeping its labels was known for finite-element surrogates. A preprint of 14
  July 2026 (Haltmayer et al., arXiv:2607.12570) trains a surrogate of multiscale Darcy flow
  on the energy norm of the error of its coefficients and compares, with the same labels,
  L2, relative L2 and L1 losses (its Section 5.2.2); a literature search of 31 October 2026
  found more such comparisons, among them the soft-tissue experiment of Dalton et al. that
  Section 2.2 itself described (the deformation gradient added to the displacement loss).
  Section 2.2 now says that adding the deformation gradient is one way of changing the norm
  of a supervised loss while keeping its labels, and that no comparison is known that trains
  an elasticity surrogate on its labels in the energy norm of the assembled stiffness
  matrix. Section 2.3, labelled `sec:related:norm`, reviews four of the comparisons found:
  H1 losses for three neural operators (Liu et al., JCP 2024), a stress term evaluated
  through the material model (Storm et al., CMAME 2024), the energy-norm loss of Haltmayer
  et al., and an energy-norm loss for a neural preconditioner (Rudikov et al., ICML 2024).
  Each reference was checked against the sources that its comment names.
- Fig. 1's caption and the graphical abstract now say that removing the solutions also
  changes the weighting of the load cases and the learning rate, as the introduction and
  Section 6 said; the graphical abstract's lower row moved up 1.2 mm and its foot down
  0.8 mm to make room for the line, and its build test reads the line in the PDF.
- The finer mesh. The three-dimensional energy-norm-supervised transformer, trained after
  the transfer comparison, was not in the transfer table (`tab:transfer`). The reading
  beside the Ritz baseline (Stage 14, `scripts/enriched_cstar.py`, arm `k3d_labels_knorm`,
  marked `"appendix": false`) evaluated its three stored states on the 256 fine-mesh
  instances on 28 October 2026, with the code that reproduced the other three networks'
  recorded fine-mesh values and this network's recorded in-band values (the content checks
  of those arms). Its row now stands in the table, as zero-shot and evaluated after the runs
  (the caption says so), from the per-instance rows of the return as received, checked
  against that arm's summary and the run's states. The generator pairs it with the Ritz
  ladder of the baseline's rows of the same instances, as the baseline pairs the other
  networks, and adds the pairs to the table of the shares (`tab:ritzpairs`) and to the
  text's readings: the projection's relative energy gap was lower than each network's on at
  least 98.4% of the fine-mesh instances (99.6% without it), and in the peak stress error
  the energy-norm-supervised transformer was the more accurate on 42% to 95% of them. The
  text says that it did not transfer either (displacement error 0.0227 in-band, 0.260 on the
  finer mesh) and that its relative energy gap and von Mises error there, like the
  label-free transformer's, were lower than those of the two networks trained on the
  displacement error; "the lowest" of the label-free transformer became "lower than these
  two". The rows of the displacement-supervised transformer and the graph network name their
  loss, as in the other tables.
- The largest errors. Two supplementary tables (`tab:tails3d`, `tab:tails2d`, each with a
  paragraph "The largest errors" in Sections S2 and S3) give, for every network trained on
  1,024 instances, the median, the 90th and
  99th percentiles and the largest value of the relative energy gap over the instance-seed
  pairs of the validation and held-out instances, the pairs worse than the zero field and
  the instances with such a pair, with those that have one in two or three seeds. The
  held-out arrays of the holdout evaluation and of the three-dimensional energy-norm run
  hold the same instances and, for the two networks that both evaluated, identical values.
  Read after the runs: the networks trained in the energy norm had no pair worse than the
  zero field but the energy-norm-supervised transformer's nine on the two-dimensional
  held-out instances, each one seed's on an instance of its own, which its other two seeds
  predicted with relative energy gaps of at most 0.304 and the label-free transformer of at
  most 0.363; for the displacement-supervised transformer and the graph network, more than
  half of the instances concerned had such a pair in two or three seeds. The checks section
  and the holdout section say so in a sentence each; every held-out pair counted has a load
  case of positive energy, as the arrays' per-load energies show (the generator checks it).
- Five statements. Section 4.3 states how the code computes L_K (from the difference, a
  negative value set to zero, 1e-30 under the square root; the methods test reads the two
  lines of `src/fejepa/train/supervised.py`). Section 4.6 says that the noise guard is a
  rule of decision, not a test at a stated level of significance. Section 4.4 says that
  every error is relative to the finite-element solution on the same mesh and that, where
  the peak stress lies where the clamped boundary meets the rest of the boundary, at which
  the continuous stresses are in general singular, the peak stress error measures agreement
  with the discrete peak, not a converged value. Section 7.2 says that the cost of the check
  and of the rescaling by c*, where a surrogate is used without K and F, is their assembly,
  which here took longer than the surrogate's inference (the generator checks it in every
  column of the cost table).
  Section 10.2 says that the gain is in the accuracy of the stresses, not in speed.
- An independent check of the stage recomputed every new cell and number from the records
  and found none wrong; it found six things in the text and the guards, all corrected. (1)
  "Worse than the zero field" meant an instance-seed pair's mean over the load cases in the
  new sentences but single load cases in the checks section, where one of the label-free
  transformer's three-dimensional load cases is above one; the new sentences now say "a
  mean relative energy gap above one", and S2 states the load case. (2) "Which the networks
  trained in the energy norm predicted well" overstated: the instances on which a network
  trained on the displacement error failed were harder for every network (its median on
  them above its median over all instances, checked for each network and set); S2 now says
  so and gives the bounds as far from one. (3) The finer-mesh row had no stated provenance
  and its two cross-references pointed at each other; S4 now says that the run of the Ritz
  baseline evaluated it with code that reproduced its in-band and the other networks'
  fine-mesh records (the generator checks the four content checks and the configuration's
  hash), and the list of runs names the evaluation. (4) The discussion and the introduction
  now say that the stop of conjugate gradients reads the solution. (5) S2 names the variant
  with the energy term (two pairs, each one seed's, on instances that the graph network
  failed in every seed; no holdout row, its networks not being stored); the tails' captions
  say "read after the runs" and their sets "holdout", as the Ritz table. (6) The cost of
  the check is compared with the larger of the surrogate's two calls; the graph network's
  failures are guarded in every set; S3's statement on the mean and median is now numbers
  (0.0781 to 0.0305 without the nine pairs; median 0.0188 either way) and guarded; Section
  4.3 and the discussion say "depends only through" beside the code's use of the
  difference. The related work was checked against the sources as well, and the discussion
  now notes that the energy-norm loss of Haltmayer et al. agrees with the paper's account.
- Tests: `tests/test_statics_material.py` recomputes the finer-mesh row, its numbers and
  its pairs from the rows of the Ritz return (`_fine_knorm`), the two tables of the tails
  and their readings from the reports and the holdout arrays, names the new inputs among
  the sources and the two tables among the outputs; `tests/test_statics_references.py`
  checks the four references, their comments, Section 2.2's new sentence and the absence of
  the old one. The runbook's suite lines read the new count. Suite 837 (834 + 3).

## Stage 24 (31 Oct 2026) -- the graphical abstract redrawn

- Why. The co-author's reading: in the cell "not possible: a displacement loss needs the
  solutions" the text ran out of its hatched frame, and the drawing was hard to read. At
  the journal's sizes it was: the Guide for Authors asks for at least 1328 x 531 pixels,
  ScienceDirect shows a graphical abstract in a window of 500 x 200 pixels and the table
  of contents 200 pixels high, where the drawing's 7 pt text was about 9 pixels high; and
  it held about 150 words and numbers in three blocks, where the guide asks for a clear
  start and end and little clutter.
- The new drawing (13 x 5.2 cm, as before; no text below 8 pt, about 90 words and
  numbers) reads from left to right. Left, top: "Minimising the energy is regression in
  the energy norm" (the first highlight), the identity of Lemma 1 written with /2, and
  beside it that the energy needs only K and F, not the solution. Left, below: the median
  relative von Mises errors of the same three-dimensional transformer trained with the
  displacement loss, with the energy-norm loss and on the energy alone (Fig. 1's medians
  over the 256 validation solids averaged over the three seeds, its colours and markers),
  as bars to scale; an arrow from each bar to the next carries the step: changing the
  norm (6.1-fold) and removing the solutions (1.24-fold, with the caveat of Stage 23 as a
  footnote marked by a dagger). Right: the von Mises stress of a typical validation solid
  (as the caption of the median field plot calls it), for the reference, the label-free
  transformer and the displacement-supervised one, on one colour scale. The hatched
  cell, the side notes and the foot are gone: the ranking by displacement error and the
  sign of the energy are in the highlights, the pre-registered verdicts and the held-out
  replication in the paper.
- The stress fields are those of the median field plot (`fig_field_median.pdf`: the
  validation instance at the median of the label-free transformer's relative energy gaps,
  seed 0, and its load case at the median), drawn from the records by the generator's new
  `fig_ga_fields`: `generated/ga_field_reference.pdf`, `ga_field_labelfree.pdf` and
  `ga_field_displacement.pdf`, each box alone at the height at which the graphical
  abstract places it (1.12 cm), on that plot's colour scale, rasterised at 600 dpi
  (`_save` takes the resolution, 300 dpi by default). They regenerate byte for byte, also
  through the generator's full run. On that instance the displacement-supervised
  transformer's von Mises error in seed 0 is below its median over the 256 instances (103
  of them have a lower one), so the choice does not favour the label-free one. No other
  figure was regenerated: the three files were written by calling the new function alone.
- The bars' lengths, the values and the two factors are Fig. 1's macros in
  `generated/numbers.tex`, which the generator already checks against the records.
- An independent check of a first draft of the drawing against the paper found no wrong
  number and seven points, all taken: its headline ("the energy is an energy-norm loss
  that needs no solutions") read as if the identity, which holds U* on both sides, needed
  none; the metric did not say relative, over which solids or seeds; the asterisk of the
  footnote was about 3 pixels high at 500 x 200 and echoed U*; "a validation solid" did
  not say that it was a typical one; each factor stood beside one row rather than between
  the two that it compares; the label-free network had two names; and the 1/2 of the
  identity was about 6 pixels high.
- The declaration of generative AI and S8 now say that the graphical abstract's stress
  fields are drawn from the records by the generation script, and the rest of it by the
  TikZ code.
- Tests: `test_manuscript_compiles` reads the graphical abstract's text in content order
  (`pdftotext -raw`): the statements, each training's value, the two steps and the
  caveat, with the numbers those of `numbers.tex`, which the source names only by their
  macros; and its words' boxes (`pdftotext -bbox`): each on the page at least 1 mm from
  its edges, no two overlapping, none across the boundary of the two panels (`\gasplit`),
  and none on a bar or a field, whose rectangles the build writes to its log (`\gamark`).
  Each of these checks failed when the drawing was deliberately broken in its way. The
  three field files join the figures whose presence the regeneration test checks. Suite
  837 (834 + 3), unchanged.

## Stage 25 (1 Nov 2026) -- corrections from the final reading before submission

- Why. Before the tag, two independent readings, one of the manuscript and one of the
  supplementary material, looked for errors of language, reference and consistency (the
  numbers being checked by the tests). They found no wrong number; the points below were
  checked against the sources and corrected. No number, table value or figure changed.
- The manuscript:
  - Section 1 counted four studies as "one ... two others ... a third"; the last is now "a
    fourth". Its last sentence said that the identity, the conditioning bounds of Section 3
    and their checks were "first stated" in the companion note, against Section 3, which
    says that Lemma 1, Remark 1 and two statements of S8 are restated from it and that the
    identity is classical; it now says what Section 3 says. The claim that did not replicate
    is "the mean relative energy gap", as Section 8 has it.
  - Sections 2.4 and 7 cited Section 3.6 for the two checks, of which the ranking
    (Corollary 2) is in Section 3.5; both cite Sections 3.5 and 3.6. A comma splice in
    Section 2.3 is mended.
  - Section 4.1 names the in-band range, which the text and the supplementary material use;
    Section 4.3 says that the three-dimensional energy-norm-supervised transformer, like the
    graph network, was trained at one budget only (1,024), and writes N, not n, for the
    number of labelled instances, n being the number of unknowns.
  - Section 3.4 writes the mean stress sigma_m instead of p, which names the Ritz degree.
  - Section 9.2 says that its ratios of times are medians of the per-instance ratios, not
    ratios of the medians in Table 4 (27 against 25, for example); Table 4's row is
    "Relative energy gap after rescaling by c*".
  - Section 10.5 glosses the joint-embedding term, which the manuscript did not define.
  - The first paragraph of Data availability is set ragged right: justified, its URLs were
    stretched into gaps that a copy from the PDF kept (its four underfull lines are gone).
- The supplementary material:
  - S8 cited "Corollaries S1 to 3 and Remarks S1 and 3", cleveref having merged a
    supplementary and two main-text labels into a range; it now lists them one by one.
  - S1 said that the two-dimensional holdout instances lie beyond the deepest prefix "of its
    training pool", which Section 4.1 defines as the first 1,024 of the non-validation
    instances; it now says "of its non-validation instances", as Section 4.1 does, and its
    first "in-band" points to Section 4.1.
  - S3's "This geometric mean" referred, as written, to that of the ratio of the squared
    displacement errors; it now names the geometric-mean ratio of the relative energy gaps,
    9.85 (Section 5.3).
  - S2's "its median" named the instance; it now names the transformer's median over the
    instance-seed pairs (Table S5). S7.1's "the supervised transformer" is the
    displacement-supervised one, the table having three. S4 glosses the token bottlenecks at
    their first mention.
  - Generated text: the remesh readings say "every network" (the table has three) and the
    timing protocol "relative energy gap" for the stop of conjugate gradients, as the
    timing script computes it.
  - Floats: placeins puts each section's floats before the next section, and a barrier
    before S6.2 keeps Table S14 in S6.1; the supplementary material has 37 pages (35).
  - The bullets of the list of runs in S8 were drawn from a bitmap (Type 3) font wherever
    the cm-super fonts are not installed; they are now the bullet of the maths fonts.
- Not changed: E and B, which name Young's and the bulk modulus in Section 3.4 and, as
  defined where they appear, the energy-norm error in Fig. 1 and the reference network of
  the noise guard; the version suffixes of two arXiv references, which name the versions
  checked; the subdirectory of the records of October 2026, which S8 does not name.
- Tests: the sentences that `tests/test_statics_references.py` quotes and the row of Table 4
  that `tests/test_statics_material.py` reads follow the text. Suite 837 (834 + 3),
  unchanged.

## Stage 26 (1 Nov 2026) -- one meaning per symbol

- Why. Stage 25 left E and B with two meanings each. Now each symbol has one meaning in the
  manuscript, the supplementary material and the figures: a letter, in its typeface, names
  one quantity, function, space or index, and an index runs over one kind of object.
  Subscripts that are labels (sigma_vm, F_max) belong to the symbol they label and are set
  upright where a letter could be read as a symbol. The names of the pre-registered
  criteria (C5, D2, E6, G2, H1, K1, KP5, T1) are names that the pre-registration documents
  fixed, not symbols, and are kept. An independent reading of the notation, given only the
  PDFs, the sources and this rule, found no letter or index with two meanings after the
  first round, and the points of the second round below. No number changed.
- E is Young's modulus only: Fig. 1 names its two errors in words, "energy norm" and "von
  Mises", instead of E and vM, and its caption says so. Only this figure is redrawn.
- B is the bulk modulus only and s the deviatoric stress only: the noise guard (Appendix A)
  compares a network with a comparator network through mean and sd of each, and the tables
  of the pre-registered hypotheses in two and three dimensions and of the 30 secondary
  comparisons name the network and the comparator instead of A and B (rows "Network",
  "Comparator"; readings "better", "worse", "network lower"; notes "with the network and the
  comparator exchanged"). "Reference" stays the name of the finite-element solution.
- m is the index of the eigenmodes only: Section 3.4 no longer names the mean stress
  (sigma_m, Stage 25) and writes the trace of the stress instead; gamma* =
  G ||tr sigma||^2 / (3B ||sigma_vm||^2), the same number. I is named the identity tensor.
- L names the Lebesgue spaces only: the number of load cases is J, in Corollary 1, the
  losses and the gradient of Section 4.3, and the separation statement of S6. Section 2.3
  says that the relative L^2 errors of mesh surrogates are computed as Euclidean norms of
  the nodal or point values, and Section 2.4 names the stiffness matrix and the load
  vectors in words before Section 3 defines K and F.
- k is the iteration of conjugate gradients only, a and b label two predictions and c is a
  scale factor: the Ritz basis (eq:ritzbasis) has degrees p_x, p_y and p_z with
  p_x + p_y + p_z <= p - 1, instead of P_k and a, b, c; the Ritz projection is u_Ritz, not
  u_p, a subscript of u being a load case or a label.
- The iteration of S5 is a superscript of u only: the energy gap, the relative energy gap,
  the residual and the error of an iterate are written as functions of it, gap(u^k),
  g(u^0), r(u^0), instead of gap_k, g_0, r_0, e_0 and r_k, a subscript being a load case
  and g(0) = 1 the zero field's. Remark S1 bounds the initial residual by the relative
  energy gap, as its bound says.
- The superscript + is the pseudo-inverse only: Corollary S2 writes the gradient step as a
  map, instead of u^+ and e_m^+.
- n is the number of unknowns only: the critical-region recall and the rule of the field
  plots (S8) are stated without a further count.
- i indexes instances and j load cases: the separation statement of S6 compares load cases
  j and j', its latent representation is xi_j (z is a coordinate), with the Euclidean norm
  written ||.||_2, and its decoder is a calligraphic D (D labels the displacement loss).
- w_m are the eigenvectors: the proof of Proposition 2 writes g(v) for every v. Corollary 2
  names two predictions u_a and u_b, as Remarks 2 and 3 do, since u_j is the prediction of
  load case j.
- c is the scale factor: the energy-optimal amplitude of an instance's four load cases
  together is c*_inst (S4.2, Table S13), not c_b, and the characteristic length is
  l_c with an upright c.
- Tables: the table of the latent-regularisation run names the silhouette and the
  coefficient of determination of the linear probe in words (S numbers the supplementary
  material and R is the Rayleigh quotient); the holdout values (Table S4) name the relative
  energy gap, which they give, instead of "Energy gap".
- Generation: Fig. 1 is drawn with the system Python, whose matplotlibrc selects Inter, as
  the paper's other figures were; they are not regenerated. Its caption stays within 90
  words.
- Tests: the rows, the note and the reading that `tests/test_statics_material.py` reads in
  the tables of the hypotheses, and the sentence of S5 that
  `tests/test_statics_references.py` quotes, follow the text. Suite 837 (834 + 3),
  unchanged.

## Stage 27 (7 Nov 2026) -- the manuscript prepared for Engineering Applications of Artificial Intelligence: the title names stress analysis, the engineering application and its limits stated, six references added

- Why. The manuscript is prepared for Engineering Applications of Artificial Intelligence,
  whose conditions for sending a paper to review are that the abstract says which is the
  contribution to artificial intelligence and which the application in engineering, that
  the title and the abstract use no undefined acronym, and that the paper is set in one
  column (the journal's page, read on 6 November 2026). The text now states the engineering
  application that its problems already were, what the results mean for the use of such
  surrogates, and where they do not pay. An independent reading of a first draft, given only
  the PDFs, the sources and the journal's conditions, found three statements that went
  beyond the results (on the break-even, the screen and the transfer to real parts), an
  abstract sentence that could be read of the two-dimensional transformer, and a dozen
  smaller points; the text below is the corrected one. No number, table, figure or
  pre-registered verdict changed.
- The title adds the application: "The norm, not the labels: training and evaluating
  finite-element surrogates for stress analysis in the energy norm" (the manuscript, its
  PDF metadata and the supplementary material's title page).
- The journal. `\journal` names Engineering Applications of Artificial Intelligence, and so
  does the first page's footer. Section 2.2 said that surrogates trained on a physical
  objective "have a history in this journal", which no longer names the journals it cites;
  it says "in computational physics". The test that the manuscript names no earlier journal
  covers the journal of those citations as well, outside the bibliography's journal fields.
- The abstract (248 words; at most 250) has the two parts the journal asks for, each named:
  "Application in engineering:" (the stress analysis of perforated plates and solids with
  cavities, stylised families in which holes concentrate stress) and "Contribution to
  artificial intelligence:" (training and evaluating such surrogates in the energy norm, with
  or without solutions, and screening their predictions without solutions), followed by the
  identity, the comparisons of the norm, the three-dimensional label-free result, now
  introduced by "In three dimensions", the ranking and the sign of the energy, and the Ritz
  baseline in the seed means without the number of unknowns. The graph network's ratio,
  which the introduction and Section 7 give, left the abstract.
- The introduction opens with the engineering setting (holes and internal cavities
  concentrate stress; components that contain them are analysed many times, in design
  studies, in uncertainty quantification and in the assessment of parts whose voids differ)
  and names the families of Section 4.1. Its first list of surrogates adds one from the
  journal, and a second, which predicts the stresses directly, is cited as such. The
  companion note is set apart from this paper: it checks its statements on synthetic
  problems and probe instances (its abstract), and the trained networks, their comparisons
  and the baselines are new here. The introduction ends with three rules for engineering use
  and the limit of the screen (gross failures only).
- Section 10.2, "In practice", is now "Engineering use" (`sec:discussion:engineering`):
  - the rules: train in the energy norm, which by Corollary 1 and Proposition 1 is the
    compliance-weighted error of the stresses, with the solutions or without them; compare
    surrogates by their energy-norm and stress errors, not by displacement errors alone;
    screen with the energy, whose sign flags gross failures (each of the nine held-out
    predictions of the energy-norm-supervised transformer with a mean relative energy gap
    above one had a load case that it flags), whose differences pick, among several
    predictions of a load case, the most accurate in the energy norm (Corollary 2), and send
    a failed prediction back to the solver, since the rescaling by c* only makes it no worse
    than the zero field;
  - the costs, as Sections 7.2 and 9 give them: no speed gain; one network's training
    recovered against the direct solve after about 84,000 predictions, with the caveats of
    Section 9.2; in two dimensions the direct solve took 1.2 times the inference and is
    exact; the screen's assembly (900 ms against 49 ms in three dimensions) is most of the
    cost of a Ritz projection, which was the more accurate but in peak stress; passing the
    screen does not make a prediction accurate, and a surrogate's accuracy on a family has to
    be established on solved instances of it;
  - the prospects, as limits: parts whose voids differ are instances of a family, of which
    the solids here are a stylised version; real voids are more numerous, smaller and
    irregular, need finer meshes than any on which the networks were accurate, and other
    geometries, numbers of voids and loads were not tested; label-free training would pay
    most where solves are expensive (Section 10.6).
  Every sentence that the subsection had is kept, but "the compliance" of F^T U*, which is
  now "the product" (compliance names C^{-1} elsewhere).
- Section 10.5 adds that no metric isolates the stresses at the holes or cavities, and that
  where the discrete peak lies at the clamped edge the peak stress error does not measure a
  concentration at a hole. Section 4.1 adds that the problems are linear, so that the fields
  scale with the loads and inversely with Young's modulus. Sections 2.2, 4 and 9.3 point to
  the subsections of Section 10 that they mean (`sec:discussion:earlier`, labelled now,
  `sec:discussion:transfer`, `sec:discussion:engineering`, `sec:discussion:outlook`). The
  conclusion states the rules as the introduction does; the keywords add "stress analysis"
  (seven, the most the journal allows).
- References. A literature search of 6 November 2026 found close work published or read
  since the references were last checked. Six entries were added, each checked against the
  sources that its comment names, and the text states of each only what that check read:
  - Do et al. (Engineering with Computers 42, 199, 2026): a coordinate-based network gives
    the nodal displacement vector of a finite-element mesh and is trained on the total
    potential energy of the discretised system, for linear and nonlinear plane elasticity
    (Section 2.2, beside Larson et al.);
  - Kaewnuratchadasorn et al. (Computer-Aided Civil and Infrastructure Engineering, 2024):
    a physics-informed neural operator trained, for static problems, on a weak form based on
    the principle of least work (Section 2.2);
  - Song et al. (the same journal, 2023): a graph network for braced steel frames trained
    without labels on the residual of the equilibrium of internal and external forces
    (Section 2.2);
  - Bai et al. (Computational Mechanics, 2023): a least-squares weighted residual loss
    compared with the collocation and the energy losses in two- and three-dimensional solid
    mechanics (Section 2.1);
  - Deshpande et al. (2024) and Jiang and Chen (2023), surrogates of finite-element models in
    Engineering Applications of Artificial Intelligence, cited in the introduction only, the
    second as one that predicts the stresses directly.
- Tests: `tests/test_statics_references.py` checks the six entries, their comments and the
  sentences that cite them, and that "this journal" is gone; `tests/test_statics_material.py`
  checks the journal's conditions on the front matter (the two named parts of the abstract;
  no acronym in the title or the abstract; elsarticle's one-column preprint option; at most
  seven keywords, the last "stress analysis") and names the new journal. The runbook's suite
  lines read the new count. Suite 839 (836 + 3).

## Stage 28 (7 Nov 2026) -- the prose of the paper and of the supplementary material edited for clause-stacked sentences; no claim, number or reference changed

- Why. Before submission, every section of the manuscript and of the supplementary material
  was read again for sentences that stack clauses with semicolons, colons and chains of
  "which" and "with", and for sentences that argue with a reader instead of stating a
  result. In the manuscript 115 of its 454 sentences were split or reordered, and the
  sentences of more than 45 words fell from 115 to 34, most of those left being definitions
  with formulae or sentences that the tests pin; in the supplementary material 106 of 329
  were, and its long sentences fell from 71 to 19. The abstract, the declarations, the
  highlights, the graphical abstract and the cover letter are unchanged. No number, unit,
  citation, cross-reference, equation, link, table, figure or pre-registered verdict
  changed: a script that compares them in the sources before and after found them the same,
  but for four references that now begin a sentence (`\Cref`).
- Two sentences that answered an imagined objection now state the result: "We do not claim
  that the networks beat classical methods on these problems" (Section 1) reads "The
  networks did not beat classical methods on these problems", and "We do not read these
  times as a speed advantage of the surrogate" (Section 9.2) reads "These times do not show
  a speed advantage of the surrogate", followed by its three reasons, one sentence each.
- Wording made exact where a split exposed it:
  - Section 4.3 and supplementary Section S2: "a regression of the two versions of the code
    on small problems" is "a regression test", so that it is not read as the regression of
    Section 3 (the check of PREREG_K3D, on CPU miniatures);
  - Section 4.3: the energy term in three dimensions has its gradient scaled to at most the
    norm of the gradient of L_D, "except with 16 labelled instances, where the term has a
    fixed weight", as supplementary Section S1 states the policy;
  - Section 10.5: the scope sentence first says that a pre-registered comparison kept the
    joint-embedding term, then that the scope without it was chosen after that comparison;
  - supplementary Section S1: the second departure of the holdout evaluation, one sentence
    of about 130 words, is five; Appendix A: the naive baselines are those of condition (a);
  - supplementary Section S4: the fine-mesh peak-stress shares say what they compare, the
    network against the projection (`_net_better`).
- The generated paragraphs of the cost protocol, the amplitude readings and the bottleneck
  readings, and the caption of the table of the three-dimensional energy-norm run, are split
  in the same way (`scripts/make_statics_material.py`); the figures are unchanged.
- Tests: four pinned sentences follow the new sentence boundaries, in
  `tests/test_statics_references.py` ("In polycrystals the label-free network was more
  accurate in", "At finite strains", "The discretisation invariance") and in
  `tests/test_statics_material.py` (the cost protocol's sentence on the fine-mesh direct
  solve). Suite 839 (836 + 3), unchanged.

## Stage 29 (7 Nov 2026) -- the abstract ends on the screen, and a keyword names physics-informed machine learning

- Why. The journal's scope asks for novel aspects of artificial intelligence used for an
  engineering application (its page, read again on 6 November 2026), and an editor reads
  the abstract first. Two small changes make the abstract's claims easier to place, with
  nothing added or removed:
  - "stylised families" is "parametric families": the geometries are drawn from
    parametric distributions (Section 4.1); Section 10.2 still calls the solids a stylised
    version of real parts with voids;
  - the sentence on the Ritz projection and the finer mesh comes before the one on the
    energy's ranking and sign, so that the abstract ends on the check that needs no
    solution. The words, 248, are the same.
- The keywords replace "potential energy" with "physics-informed machine learning", the
  field in which Section 2 places the energy-trained networks, so that the manuscript is
  indexed with that work; seven keywords, the last "stress analysis", as before.
- No number, table, figure, test or supplementary page changed. Suite 839 (836 + 3),
  unchanged.

## Stage 30 (9 Nov 2026) -- the data sets are archived at Zenodo, and the Data availability statement cites them

- Why. The journal's scope asks that the results be "validated using public data sets for
  easy replicability of the research results" (its page, read on 6 November 2026). Until
  now the statement said that the meshes and reference solutions were not archived and
  that the code regenerates them, though not necessarily bit for bit.
- The archive (Zenodo, 10.5281/zenodo.24091113, CC BY 4.0, version statics-paper-1.0)
  holds the 7,677 instances on which the networks were trained, validated and evaluated
  on held-out data, with their reference solutions: in three dimensions the validation
  set (256), the training pool (1,024), the holdout set (686) and the finer set (320: 256
  for evaluation, 64 for few-shot training); in two dimensions the validation set (256),
  the training pool (1,024) and the holdout set (4,111). Each instance keeps its mesh,
  loads, constraints, reference solutions, material and geometry; the stiffness matrix is
  omitted, and each file records its number of nonzeros, its Frobenius norm and its
  SHA-256, which a matrix rebuilt by the archived code reproduces with the library
  versions of the runs.
- The instances were exported on 9 November 2026 on the training machine, from the files
  that the runs read, by a script that uses only the standard library and numpy and
  writes nothing until its checks pass: the split, recomputed from its seed, against the
  validation lists that the records hold (the training pools follow from the same
  split), the held-out files and their labels against the hashes in
  `records/cmame/holdout`, and the corpus manifests against the hashes that the
  pre-registrations and reports record (`dc75628290bb...`, `0f859ad98a01...`,
  `3553396d1831...`). The archive's manifest gives each instance's source SHA-256.
  Checked again on the returned manifest, summary and hash list: every role holds the
  instances that the split gives; all 4,797 held-out instances have the recorded source
  hashes; every instance has its reference solutions; the node counts of the 3D
  validation set and of the fine evaluation set are those of Section 4.1 (2,195 to
  17,692, median 5,617; 15,175 to 71,749, median 36,216.5, which `numbers.tex` gives
  truncated, as 36,216); the three archives downloaded on another computer match the
  hash list.
- The statement: the paragraph on the networks ends where it did, and a new paragraph
  cites the archive (entry `Cao2026Data`, with "[dataset]" before it as for the archives
  of the code and of the networks), names the sets that it holds in the terms of
  Section 4.1, says that the archived code rebuilds the stiffness matrices, and keeps, for
  the instances that it does not hold, the sentence on regeneration not necessarily bit
  for bit. It gives no count: 7,677 would be a number typed by hand that sums two
  generated ones (the holdout sizes), and Sections 4.1 and 8 already give each set's size.
  The paragraph is set ragged right, as the statement's first paragraph is, so that the
  address of the archive is not broken across lines; it keeps its indent.
- Tests: the networks' test no longer pins the sentence that moved; a new test pins the
  paragraph, the entry and its DOI, and checks that the sizes of the sets that it names,
  as Sections 4.1 and 8 give them, sum to the archive's 7,677; the bibliography test
  renders the new entry; the check for numbers typed by hand knows the new DOI as a
  name. The runbook's suite lines read the new count. No number, table, figure or
  supplementary page changed. Suite 840 (837 + 3).

## Stage 31 (9 Nov 2026) -- the prose edited again for wording that slows the reader; no number or reference changed, and a few statements made exact

- Why. Before submission, the manuscript and the supplementary material were read again
  against a revised editing checklist. Stage 28 split clause-stacked sentences; this pass
  looked for wording that costs the reader more effort than the content needs: inanimate
  subjects given the verbs of a person ("the code refused to start a run", "the run asked
  whether", "no network could know", a test that "reads" the solution), vivid verbs where
  the field's plain verb fits ("pays for itself", "repairs", "beat", "carries"), "so that"
  where a result is meant (it marks purpose), long gaps between a subject and its verb,
  pronouns whose antecedent was unclear, and actions hidden in nouns. In the manuscript 66
  of its 592 sentences changed, and in the supplementary material 67 of its 440. The
  abstract keeps its 248 words; the highlights, the figures and the graphical abstract are
  unchanged. No number, unit, citation, cross-reference, equation, link, table value or
  pre-registered verdict changed: a script that compares them in the sources before and
  after found them the same, but for one reference that no longer begins a sentence
  (`\cref{tab:ritzpairs}`) and the criterion of supplementary Section S1, which reads "a
  displacement error at most a third of the zero field's" instead of "three times more
  accurate in displacement than the zero field".
- Wording made exact where the edit exposed it:
  - supplementary Section S9: the networks paired with the Ritz projection are "those
    trained on 1,024 instances", not "with 1,024 labelled instances", since the table
    includes the label-free transformer, which used no labels;
  - Section 2: the multiscale Darcy surrogate reached lower errors than "when trained with
    L2, relative L2 or L1 losses" (was "and": each loss was a separate comparison);
  - Sections 1, 9 and 10 and the cost table: the conjugate-gradient stop "uses the
    reference solution" (was "reads the solution"); label-free training "recovers its
    cost" or "is most useful" where solves are expensive (was "pays for itself");
  - Section 3: K and F are what "a finite-element code assembles before solving" (was
    "every": a matrix-free code does not assemble K);
  - Section 7: the rescaling "makes every prediction that the check flags no worse than
    the zero field", which is what Proposition 2 gives (was "repairs what it flags");
  - Section 10, outlook: at finite strains the choice of norm "may again decide what a
    surrogate learns" (was "will"), since that setting was not tested;
  - supplementary Section S1: the independent review of 20 October 2026 is described in
    the passive, as what was meshed, solved and read in that review, not as an agent that
    meshed them.
- A second reading, by an AI tool that had not seen the edit, compared every changed
  sentence with the original. Its findings were taken: the novelty sentence of Section 2 keeps "a
  comparison" ("a study" would have widened it), the runs still "decide" the claims,
  Section 9 keeps the GPU and the CPU side by side as the first reason, Section 10 keeps
  "regarded as valid within the range of mesh sizes", Section S4 keeps "diagnoses the
  error", and several pronouns and attachments that the edit had made unclear were fixed.
- The generated paragraphs and notes follow (`scripts/make_statics_material.py`): the cost
  protocol, the remeshing and bottleneck readings, and the notes of the result tables, the
  cost table, the transfer table and the July table; the figures are unchanged.
- Tests: six pinned sentences follow the new wording, four in
  `tests/test_statics_references.py` (the multiscale Darcy comparison of Section 2, the
  conjugate-gradient stop and the cost of label-free training in Section 9, and the
  outlook at finite strains), one in `tests/test_statics_material.py` (the cost protocol's
  first sentence) and one in `tests/test_repository_transfer.py` (the Software Heritage
  sentence of supplementary Section S8). Suite 840 (837 + 3), unchanged.
- The manuscript has 60 pages, one more than before: the last row of Table A.1 moves to
  the next page. The supplementary material keeps its 37 pages.

## Stage 32 (9 Nov 2026) -- the journal's layout and its double-anonymized review: the paper in 43 pages, review copies without the authors, six keywords

- Why. The journal's Guide for Authors, read in full on 9 November 2026 (a copy the PI
  saved that day), sets three conditions that the manuscript of Stage 31 did not meet:
  "all submissions must not exceed 50 pages, and the manuscript file size should be under
  100 MB. Submissions that do not meet these requirements will be subject to desk
  rejection" (the manuscript had 60); "This journal follows a double anonymized review
  process", with the title page and the anonymized manuscript as separate files and
  neither the manuscript nor any supplementary material carrying the authors' names or
  affiliations; and "1 to 6 keywords" (there were seven). Its other conditions were met:
  one column, an abstract of at most 250 words that names the contribution to artificial
  intelligence and the application in engineering, no undefined acronym in the title or the
  abstract, highlights of three to five lines of at most 85 characters, a graphical
  abstract at least 1328 pixels wide, a declaration of the use of generative AI, a funding
  statement, a CRediT statement and the data in a public repository.
- Layout: `\documentclass[3p,12pt]{elsarticle}`, the single-column journal layout of
  Elsevier's template, at the same 12 points, sets the manuscript in 43 pages (the template's
  default, preprint at 12 points, took 60; at 11 points it took 58). One line that could not
  break within the tolerance ran 11 points into the margin; `\emergencystretch` of 1 em lets
  it stretch instead. Nothing else changed in the text, the tables or the figures.
- Keywords: six, without "linear elasticity", which the abstract's "linear elastostatics"
  and the keywords "finite element method" and "stress analysis" cover.
- Review copies. `main.tex` and `supplementary.tex` define `\ifanonymous`, set when the build
  defines `\anonymousbuild`
  (`latexmk -pdf -usepretex='\def\anonymousbuild{}' -jobname=main_anonymous main.tex`, and
  the same for the supplementary material, after the paper). The review copy of the paper
  names no author and has no author metadata; leaves out the CRediT statement and the
  declaration of competing interest, which the separate title page and the journal's
  declarations tool give; gives the Data availability statement without the addresses of
  the repository, of its Zenodo archive and of its Software Heritage snapshot, and without
  the DOIs of the archives of the networks and of the data sets, saying that the title page
  gives them; and cites the authors' note and their three archives as "Anonymous, Details
  omitted for double-anonymized reviewing (2026)", in the form of Elsevier's guidance, from
  `references_anonymous.bib`. That file is written by `scripts/make_anonymous_bib.py` from
  `references.bib`: the four entries are anonymous under the same keys, so that the text,
  the citations and their numbering are the paper's, and every other entry is unchanged.
  The review copy of the supplementary material names no author and cites in the same way.
  The review copy of the paper has 42 pages, that of the supplementary material 37.
- The paper and its supplementary material as the repository builds them, and the arXiv
  version, keep the authors, the statements and the addresses.
- Tests: the front-matter test reads the new layout and at most six keywords; the test of
  the declaration of competing interest reads it up to the switch that the review copy
  leaves it out by; the compile test also requires no box running into the margin of the
  paper, at most 50 pages for the paper and its review copy, and builds both review copies,
  requiring of each no undefined reference, no box in the margin, no author metadata, and
  none of the authors' names, affiliations, e-mail address, repository name or archive
  addresses in its text; a new test requires that `references_anonymous.bib` is the
  script's output and that its four entries name no author and no address. The runbook's
  suite lines read the new count. Suite 841 (838 + 3).
