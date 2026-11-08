# Independent pre-stamp reviews of gate G-C2.1: reports as delivered

Verbatim reports of the independent reviewer (a separate agent that did not write the code) to the author, 6 November 2026. Paths under /tmp are the reviewer's scratch copies in the development sandbox.

---

# Round 1 (6 November 2026, about 03:48 GMT)

## G-C2.1 review: not ready to stamp

**Overall:** The package is not fit to stamp yet.

The mechanics, the torch energy, the network map, training and resume, data and the CLI all check out. Two code defects need fixing first:
- the label check would almost certainly fail on the GPU box (where the run is executed);
- the verdict can come out as FAIL when the pre-specified rule says PASS.

The prespec must also be brought into line with the configuration. Its judged metric currently differs from the code's. After the blocking and should-fix items below, I see no further obstacle.

**Files changed while I was reviewing:** `fejoint/nlsolve.py` and `c2/evaluate.py` (03:32), `docs/PRESPEC_G-C2.1.md` (03:38) and the new `probes/c2_pilot/` folder (03:19 to 03:38). I re-read all of them, and the findings apply to these versions:
- nlsolve.py: 981b06be…
- evaluate.py: c8b7aae4…
- PRESPEC: d0a8a7d7…
- config.py: aee1ebfb…
- RUNBOOK_C2.md: 4c167894…

On the current tree the runbook's three test files give `23 passed, 1 warning` (test_c2.py alone: 14).

**Disclosure for "What was seen before the stamp":** during this review I solved `tested_BJ_T1_preloaded` at the gate's mesh (5 mm, two layers) at the seven configured evaluation levels.
- F = 34.2, 67.3, 131.0, 179.1, 195.9, 215.4 and 228.1 kN at D = 0.5 to 8 mm.
- I also solved seed-7 members 0 to 2 and seed-8 members 0 to 2 at the gate's mesh. These are seen seeds.
- The prespec currently says the T1 was solved only on a coarse mesh. Please add this.

### Blocking

**B1. The label check will fail at runbook section 4, so training never starts.**
- **Where:** `fejoint/nlsolve.py:98,113`; `c2/config.py:37-38`.
- **What happens:** near the optimum, the predicted energy decrease (slope about 1e-13 N mm) falls below the round-off of E (about 3e5 N mm). The Armijo test then becomes a coin flip and cuts t (0.5, 0.125, then 4.9e-4). Line 113 (`t * step_norm <= tol * zscale`) then declares convergence while the residual is still about 1e-8.
- **Evidence:** I ran 48 label solves on seven seen members, with the config's tol 1e-12 and max_it 80. All reported `converged`, but three exceeded the 1e-8 limit:

  | Member | Level | Residual on unconstrained unknowns | Multiplier on separated unknowns |
  |---|---|---|---|
  | tested T1 | D = 8 mm | 1.01e-8 | — |
  | seed 7, member 2 | D = 6 mm | 1.2e-8 | 4.5e-9 |
  | seed 8, member 1 | D = 3.5 mm (training level) | 2.9e-8 | — |

  With 3 of 7 members failing, a clean pass over 132 members is essentially impossible. The project's own records already show kkt_max up to 6.5e-7 (fine mesh) and 1.0e-8 (flow theory).
- **The labels themselves are accurate:** continuing the T1 solve moves F by only 3e-12.
- **Fix:**
  - In `nlsolve.solve`, take the full step without the Armijo test when -slope ≤ about 1e-13·|E|, and declare convergence only on a full step.
  - I validated this as a scratch subclass (`/tmp/review_c2/sqp_fix.py`). All seven T1 levels end with residuals ≤ 9e-13, with the same iteration counts. The BJ records stay valid.
  - Also, or instead, relax `max_residual_unconstrained` and `max_lambda_inactive` to 1e-6, the G-C1.3 values, and update prespec line 241.

**B2. A NaN in the 90th percentile can turn a PASS into a FAIL.**
- **Where:** `c2/evaluate.py:101`, `:166-173`.
- **What happens:** `np.quantile` (linear method) interpolates inf against inf and returns NaN. With 448 rows this happens once 46 or more rows are infinite.
  - That seed's 90th percentile becomes NaN, `np.median` over the seeds becomes NaN, and `C2 = NaN <= 0.10` is False.
  - The current code produces infinite rows whenever the reference force at the predicted e is ≤ 0 or the solve there fails, so this is now more likely, not less.
- **Demonstrated on the current evaluate.py** (small config, seeds 7 and 8): seeds 0 and 1 predict the labels exactly, seed 2 has every row infinite. The code gives FAIL with C2 = NaN; the pre-specified rule (seed 2 counted as inf) gives C2 = 4.8e-8 and PASS.
- **Fix:**
  - Return inf whenever the order statistic above the 90th-percentile position is infinite (sort and interpolate explicitly, or clip to the float maximum and map back to inf).
  - Assert that C1_value and C2_value are not NaN.
  - Add a test like `test_non_finite_and_missing_label_free_seeds` in test_c13.

**B3. The prespec contradicts the configuration and code.**
- **Criteria (lines 181-185):** C1 and C2 judge |F_pred/F_ref - 1| at the same D. The config and `evaluate.py` judge |F_pred/F*(e_pred) - 1|. The prespec's own line 92 argues for the curve metric.
- **Numbers that differ from the config:**

  | Item | Prespec | Config / code |
  |---|---|---|
  | k_s (lines 56, 127) | 100 kN/mm | 20 kN/mm |
  | D maximum (line 56) | 4 mm | 8 mm |
  | Training sqrt(D) range (line 159) | sqrt(0.05) to sqrt(4) | sqrt(0.1) to sqrt(8) |
  | Load feature (line 150) | D over 4 mm | D over 8 mm |
  | Evaluation levels (line 137) | 0.1, 0.25, 0.5, 1, 2, 3, 4 mm | 0.5, 1, 2, 3, 4, 6, 8 mm |
  | Supervised levels (line 137) | 0.15 to 3.5 mm | 0.75, 1.5, 2.5, 3.5, 5, 7 mm |
  | Arms (lines 171-172) | 51,200 steps each (100 and 800 epochs) | 200 epochs each: 102,400 and 12,800 steps |
  | Budget (lines 175-177) | 307,200 steps, 26 h | 345,600 steps, 28.8 h (the runbook matches the config) |
  | End displacement (Question, line 9) | about 3 mm | e at D = 8 is 4.0 to 5.2 mm on the members I solved |

- **Rationale text:** "Chosen here" (line 56) still argues for the stiff spring.
- **Unevaluable predictions:** the Verdict bullet (line 188), the config `non_finite_seed` text and the evaluate.py module docstring (lines 7-8) all say such a prediction makes the whole seed infinite. The current `metrics` makes the curve error infinite per row instead.

### Should fix

**S1. Some solver errors still make a whole seed infinite.**
- **Where:** `c2/evaluate.py:52,58`.
- **What happens:** `metrics` catches only RuntimeError. Other errors escape to `_member` (line 88): the whole member becomes an error, no eval summary is formed (line 155), and the seed counts as infinite. That way one solver failure decides a seed.
- **Which errors escape:** numpy's `LinAlgError` is a ValueError. pypardiso raises `PyPardisoError(Exception)` and `ValueError`. On the box, PARDISO handles these systems (about 4,000 unknowns, above PARDISO_MIN = 3000).
- **Fix:** catch Exception per row and record the message.
- **Risk:** in my tests `solve_at_e` converged for e from -0.18 to 15.4 mm, so the risk is low.

**S2. The runbook's loss figures are wrong for the current setup.**
- **Where:** RUNBOOK line 128 says the loss "falls from about 14" and the exact solutions give "about 10".
- **Where 14 comes from:** the displacement-control pilot (`pilot_coarse_summary.json`: 13.99 → 10.23).
- **Current values:** under spring loading, the zero-output start is about 10.5 to 10.9. The exact solutions give 10.29 to 10.64 (T1 10.50) over the sampled D.
- **Why it matters:** the runbook tells the operator to stop when output differs from a comment.
- **Design note:** the spring dominates the energy. In the elastic range a 5% error in e changes Π by only about (k_s/k_T)·ε², roughly 4e-4 relative. The soft-spring pilot (still "[to be filled]") should show whether that is resolved.

**S3. Other runbook gaps.**
- Line 94 says labels take "about 1 h"; line 13 says about 15 min with 16 workers. I measured 100 to 320 s per member on a shared 2-core machine.
- Line 53 "NN passed" should now read 23.
- Line 57 says the expected warning is a torch sparse notice. The actual warning is `tests/test_c2.py:218`, `float(Et[b])` on a tensor that requires grad: add `.detach()` and fix the note.
- The `nvidia-smi` queries (lines 48, 86, 116) omit `memory.total`, which the memory stop rule needs.
- The provenance line from the C1.3 addendum (lscpu, cgroup cpu.max and memory.max) is missing. W = nproc - 1 can oversubscribe under a container CPU quota.

**S4. Test coverage is thinner than G-C1.3's.**
- test_c2 lacks c13's tests for:
  - resume to the same end state;
  - a non-finite stop being final;
  - the verdict with non-finite and infinite seeds;
  - refusal of files from another configuration or with changed labels;
  - the repository-file check.
- I ran resume and the non-finite stop by hand. Resume is bitwise identical for both arms on CPU, and the non-finite stop is final with no predictions written. The verdict path fails (B2).

**S5. The pilot scripts are missing.**
- `probes/c2_pilot/README.md` names `pilot_cpu.py`, `pilot_trend.py` and `pilot_curve.py` as "final versions". Only the README and the records are present.
- The modified `README.md:54` also describes the folder as complete.

**S6. The "preloaded" tested members carry less than 60.7 kN.**
- ρ = 60.7 kN / N_y is a pre-shortening ratio. Because the flange gives, the T1 member carries 55.96 kN at D = 0.5 mm, about 8% below the test's 60.7 kN.
- The probe reached 60.7 kN with δ = 0.0665 mm; the family uses δ = 0.0609 mm.
- These members are reported only, but the prespec should say this, or set ρ from the probe's δ.

### Minor

- **Config claim:** `c2/config.py:4` says "everything that changes a number of the run is here". It is not, though all of the following are pinned by the code hashes:
  - the bubble line search's 8 halvings and the Armijo constants;
  - the stress-reading ramp start x0 = t_f + r + 10;
  - the mesh settings n_tw and growth (c13's config listed them);
  - reg and k_rot_factor;
  - the validity rule t_w ≤ t_f + 2;
  - the evaluation's TOL and the `solve_at_e` tolerance and iteration limit;
  - D_MAX and K_SPRING, read from family.py rather than from cfg.
- **Steel law wording:** `family.py:53-54` adds REG·α at every breakpoint, so the hardening segment ends at 1.35 fy + about 3 MPa. The config (line 52), the family docstring and prespec line 128 say "added on the plateau".
- **Unused export field:** `v_norm` (`instance.py:67-68,80,109,141`) is never used. It is the only exported value that goes through LAPACK, so instance-file bytes, and with them SHA-256, can differ across BLAS builds or zlib versions. "Regenerated" (runbook section 7) means equal arrays, not equal hashes.
- **torch_energy.py:130-138:**
  - A step zeroed after 8 halvings stays zeroed for later iterations. I saw this in a few elements, with no effect on the energy beyond 1.3e-7.
  - When t = 0 and da is non-finite, line 138 gives NaN; use `torch.where(t > 0, t*da, 0)`.
- **plasticity.py:**
  - Line 125: when Newton lands exactly on the root, the safeguard bisects away from it. It recovers, but non-convergence after 60 iterations would be silent.
  - Line 154: `hencky`'s docstring lists 4 returns; it returns 5.
- **nlhex.py:97-114:** after 40 failed halvings the tiny step is accepted and can pass the step test at line 111. Convergence is judged on the step only, never on the residual.
- **tstub_pl.set_preload (lines 152-171):** no convergence flag. It is not used by the gate.
- **evaluate.py housekeeping:** NpzFile handles are never closed. `eval_rows` order depends on worker completion; sort by id. The JSON contains Infinity and NaN.
- **"sandbox":** prespec line 39 quotes the owner using this word. It is not a path; flag it only if the hygiene rule covers the word.
- **Evaluation time:** `solve_at_e` takes 10 to 184 s here when e_pred is far from the reference. Warm-starting from the member's label with the closest e would help.

### Checked and fine

- **Pins:** SHA-256 of the six `src/fejepa` files match the config. The import trace loads exactly the 20 files in CODE plus those six.
- **Material law:**
  - Radial return, consistent tangent and incremental potential pass finite-difference checks. They stay finite at breakpoints, at zero strain and at strains up to 5.
  - The yield residual is ≤ 2.2e-13, and the tangent is positive definite (minimum eigenvalue 7 MPa).
- **Bolt law:** continuous and monotone; torch and numpy agree.
- **Torch Hencky energy:**
  - The closed form equals the return mapping: within 1e-12 in float64, and within 6e-7 in float32 for strains ≥ 1e-6.
  - Gradients are finite at zero strain, and there is no NaN branch in `torch.where`.
  - Bubble Newton in float32 against the float64 reference (exact, noisy, scaled and wrong-level fields at D = 6 mm): energy within 1.3e-7, gradient ≤ 1.7e-4 of max|g|.
- **Instance:** the T change for the rigid end, the fixed mask, the contact indices, v and e_idx are all correct. F agrees with F_sigma to 7e-11 on gate-mesh labels.
- **Network map:** fixed unknowns are exactly zero and contact unknowns ≥ 0 by construction, so the evaluation's assertions cannot fail for finite float32 output.
- **Device placement:** every tensor is created with the device, and sparse-mm inputs are contiguous. Not run on a GPU here.
- **Data:** sampling and seed checks are deterministic; manifest, ledger and SHA checks work; levels are sorted with warm starts; the fork pools have no torch in the parent.
- **Sizes:** 1,342 to 1,617 nodes and 6.4 MiB of energy tensors per member, so about 3.2 GiB for 512 (the runbook says about 4 GB). Return package about 60 MB.
- **Records:** `probes/c2_bj1997_compare.py` reproduces every T1 statement in the prespec.
- **Runbook counts match the config:** 580 members, 132 labelled, 860 solves, 2,856 predicted fields, 102,400 and 12,800 steps, 45 bench losses, 20 code hashes plus 6 repository lines.
- **Hygiene:** no tool names, temporary or home paths, or em and en dashes, and British spelling throughout, in all new files including the pilot README.

**Scratch material:** everything is in `/tmp/review_c2/`. The key scripts are `sqp_seq.py` (reproduces B1), `sqp_fix.py` (the validated fix), `paths.py` and `verdict_rerun.py` (B2), `labels.py` and `label_*.json` (the seven members), `bubbles.py`, `solve_at_e.py` and `lossnum.py`. The demo data is in `/tmp/review_c2/demo`. Nothing in the repository was modified.

No new memory items.

---

# Round 2 (6 November 2026, about 17:25 GMT)

## G-C2.1 second-round audit: fit to stamp once the disclosure is corrected

**Bottom line.** I found no blocking defect. The B1 solver fix is correct and robust in every case I ran. The three runbook paths I could exercise without a GPU work end to end:
- write-config, generate, labels and check-labels;
- training with resume and the loop's stops;
- evaluation and the return package.

One item must be fixed before stamping: the prespec's account of what was seen before the stamp is no longer true (S1). That is a text change, plus optionally two seeds added to SEEDS_SEEN. Everything else is minor.

**What I executed.** All runs were in my own copies under `/tmp/claude-0/-home-claude/8ff2db7c-f7cd-5897-8207-48e2e1d8242b/scratchpad/c2/review2/`. Nothing in the repository was touched, and no seed 20261106 or 20261107 member was drawn.
- **The gate's tests:** 30 passed, no warnings, 187 s.
- **Instrumented label solves on the gate's mesh:**
  - T1 preloaded, seed 7 member 0 and seed 7 member 2 at the evaluation levels;
  - seed 8 member 1 at the training levels;
  - 27 levels in all.
- **65 calls to `solve_at_e`,** warm-started exactly as `metrics` does:
  - seed 7 member 0: all seven levels at 0.5, 0.8, 0.95, 1.05, 1.2 and 1.5 times the label's e, plus e = -0.05, 0.001, 6 and 12 mm;
  - T1: the same factors up to D = 2 mm only (stopped early to free CPU).
- **T1 at D = 0 and 0.5 mm.**
- **The stamp helper,** run in a separate copy.
- **The runbook end to end:** sections 1, 2, 3, 4, 5, 6 and 7, run verbatim from the extracted blocks with only paths, the SHA placeholder and the CPU device changed. The configuration was tiny: seen seeds 8 and 7, coarse mesh, T1 preloaded only.
- **Shell checks:** `bash -n` on all 12 blocks, a simulation of the `pipefail` / `break 2` loop, and the W one-liner.
- **Import trace and hygiene grep.**

Everything else I only read.

### Blocking

None.

### Should fix

**S1. The "What was seen before the stamp" section is now inaccurate.** Where: `docs/PRESPEC_G-C2.1.md` lines 86 to 90 and line 118.
- **What it says:**
  - Line 86: members were drawn before the stamp "all with seeds in SEEDS_SEEN (7 and 8)".
  - Line 118: only the preloaded T1 was solved in family form.
- **What happened instead:** while I worked, a separate dry run ran on this machine. It is not mine; I only read its files, under `scratchpad/c2/runbook_dry/boxA/`. Its `c2_config.json` has `train_seed 101`, `eval_seed 102`, 4 training and 2 held-out members, on the coarse mesh. Its `labels/` folder holds labels for:
  - `train_0000` to `train_0003` and `eval_0000` to `eval_0001` (seeds 101 and 102);
  - all four tested members: T1 and T2, preloaded and snug.
  - boxB and boxC hold no C2 data.
- **My own solves** (the same members the prespec already names) should be disclosed as a second review:
  - T1, seed 7 members 0 and 2 and seed 8 member 1 on the gate's mesh;
  - `solve_at_e` at perturbed e on seed 7 member 0 and T1;
  - T1 at D = 0;
  - a tiny train-and-evaluate run on seed 8 members 0 to 2 and seed 7 members 0 and 1 (coarse mesh).
- **Fix:**
  - Add 101 and 102 to `SEEDS_SEEN` (`c2/config.py:19`). This changes the config hash, which is fine before the stamp. Otherwise, reword line 86.
  - Extend lines 86 to 90 with the dry run and both reviews.
  - Amend line 118 to say that T2 and the snug members were solved on the coarse mesh by the dry run.
- **Effect on the verdict:** none. The tested members are reported only, and no gate seed was touched.

### Minor

**M1. The round-off branch also accepts uphill steps.** Where: `fejoint/nlsolve.py:93`.
- The branch that skips Armijo is the else-case of `-slope > 1e-13|E|`, so it also admits slope ≥ 0 with a step of any size.
- With an exact QP step and a positive definite tangent this cannot happen: slope ≤ -dzᵀH dz.
- Every slope in my 27 levels and 65 `solve_at_e` runs was negative.
- A guard would make it robust: treat slope > 1e-13|E| as a failure.

**M2. The post-step convergence test is dead code.** Where: `nlsolve.py:120`.
- If `step_norm <= tol*zscale` held, line 88 would already have exited the loop. Convergence is declared only at line 88: the full Newton step is negligible and is not taken.
- The prespec's "declares convergence only on a full step" is right in substance.

**M3. The relaxed limit on separated multipliers is one-sided.**
- `min_lambda >= -1e-8` (`nlsolve.py:139`) covers every contact unknown, separated ones included. A negative multiplier on a separated unknown is therefore still held to 1e-8.
- Prespec lines 93 and 275 say those multipliers are allowed 1e-6.
- No practical effect: the worst measured value was 5.3e-13.

**M4. One percentile comes out huge but finite instead of infinite.** Where: `c2/evaluate.py:107-109`.
- With exactly 45 of 448 rows infinite, `_quantile(v, 0.9)` returns 1.348e307, not inf (demonstrated). The interpolation fraction is 0.3, which falls below the big/2 cut.
- Any value ≥ 0.10 fails C2, so the verdict cannot change. A reported p90 or C2_value of 1.35e307 would puzzle a reader.
- Fix: return inf whenever the upper order statistic used is infinite and the fraction is above 0.

**M5. A docstring contradicts the code.** Where: `evaluate.py:39`.
- It says the warm start is "the label at the same D".
- The code (line 54) and prespec line 211 use the label nearest in e.

**M6. Summary means are not byte-identical across re-runs.** Where: `evaluate.py:176`.
- `rows` follows the order in which workers finish. With W > 1 the summary "mean" fields can differ in the last bit between re-runs: 102 of 200 random permutations of 448 values gave a different `np.mean`.
- Medians, percentiles and the verdict are unaffected. Sorting by id fixes it.
- With one worker, two evaluations gave byte-identical `verdict.json`.

**M7. The comment on W names the wrong command.** Where: RUNBOOK line 52.
- The comment says "nproc: the CPU count W below uses", but W uses `os.cpu_count()` and cgroup-v2 `cpu.max`.
- On the C1.3 box (`cpu.max 2500000 100000`, from `records/c13/return/provenance.log`) W = 24. That is correct.
- Under cgroup v1, or a limit set only by cpuset, W becomes the host CPU count minus 1. That means oversubscription, though not a crash.
- `len(os.sched_getaffinity(0))` would be safer.

**M8. One pilot row omits a run.** Where: prespec line 101.
- The row gives "34.8% to 35.1%" at 1,920 steps under displacement control.
- It omits `trend_coarse_a` (102.8%, no lift), which the pilot README lists.

**M9. The evaluation has no time bound for far-off predictions.**
- `solve_at_e` overwrites only e in the label it starts from.
- At D = 4 to 8 mm, even 5% off takes 7 to 14 iterations and 30 to 65 s here; e = 12 mm took 23 iterations and 115 s.
- A badly trained seed predicting extreme e could run far past "1 to 3 h". This only affects broken runs.

**M10. The worktree step hides its own error.** Where: RUNBOOK 0b.
- `2>/dev/null` hides why `git worktree add` failed (for example, a missing tag); the operator sees only the fallback's `cd` error.
- Consider `git bundle verify` before the bundle fetch.

### Verified correct

- **B1, the solver fix.**
  - All 27 levels converged in 2 to 12 iterations (limit 80).
  - Worst residual 5.9e-11, multipliers at most 5.3e-13, complementarity 3.6e-13, F against F_sigma at most 8.9e-14.
  - Each level ended with one step taken without the Armijo test, of 1e-11 to 1e-7 mm, with an energy change of at most +4.8e-16 relative (round-off). The energy noise is about 100 times below the 1e-13 threshold, so Armijo above it is reliable and there is no stall.
  - Labels equal the first round's to 2.3e-11 mm in e.
  - The prespec's line 92 claims hold (residuals at most 6e-11; forces unchanged to 0.1 N).
  - The 1e-6 limits leave four or more orders of margin.
- **`solve_at_e`:** all 65 cases converged.
  - e = -0.05 gives F* < 0, which counts as infinite by rule.
  - e = 0.001 gives F* = 860 N.
- **First-round items:** B2 is fixed (apart from M4) and B3 is fixed; S1 to S6 and the earlier minor items are fixed as stated. The three items left deliberately are harmless.
- **Numbers that match the code and configuration:**
  - The 5% and 10% thresholds, the arms, 200 epochs, 102,400, 12,800 and 345,600 steps, 0.30 s a step and 28.8 h.
  - The levels, the seeds, k_s, D_max, the KKT limits and the stop rules.
  - 580 members, 132 labelled, 860 solves and 2,856 predicted fields.
  - The bench's 45 losses and the memory rule.
  - The analytic zero-output loss of 10.47, which matches the runbook's "about 10.5 to 11".
- **Prespec figures:** the figures quoted from the seven pre-stamp solves agree with them:
  - e of 0.036 to 0.077 mm at D = 0.5 and 4.02 to 5.76 mm at 8 mm;
  - e/(D−e) of 1.01 to 2.58;
  - secant stiffness of 109 to 256 kN/mm;
  - yielding starting at D of 1 to 3 mm.
- **T1 preload:** the tested T1 carries 55.61 kN at D = 0.
- **The pilot table** matches the README, apart from M8.
- **Import trace and pins:**
  - The import trace loads exactly the 20 CODE files and the 6 pinned repository files, and the pins match.
  - They equal the hashes stamped for G-C1.3 (which were pinned at wp9-pool 92dfc93). This clone is shallow, so the commit itself could not be checked.
- **The stamp helper:**
  - It prints the config hash `f1c16e52eb6aaaf0ab05d1c62d1f10dbdc000c6c154efbe1bca9bb32407dea72` for the current config, the same as write-config.
  - It writes a 26-line hash file that passes `sha256sum -c` from joint/ with 0 failures, and copies the 20 files.
  - .gitignore hides none of its outputs.
- **The runbook run:**
  - Outputs matched the comments, including the `{"status": "finished", "steps": N}` lines and "ok": true from check-labels.
  - The section 3 one-liner fails only on CPU, where peak memory is None; on CUDA it is a number.
  - The `pipefail` / `break 2` loop behaves as described.
  - The W one-liner gives 24 on the C1.3 box's cgroup.
- **Hygiene** is clean: no tool names, temporary paths or dashes, and British spelling.

### Fitness

The package is fit to stamp after S1, the disclosure fix (text, and optionally `SEEDS_SEEN`). No code change is needed for the run to complete and for the verdict to be computed as pre-specified. M1 to M10 can be fixed now, at the cost of new hashes before the stamp, or left; none can change the verdict.

**Possible memory item.** The GPU box used for C1.3 was an RTX 5090 (32 GB) with a Xeon 8470Q, a cgroup-v2 limit of 25 CPUs and 98.8 GB of memory. Source: `joint/records/c13/return/provenance.log`. I did not use stored memory.

---

# Round 2, check of the fixes (6 November 2026, about 17:50 GMT)

## Check of the second-round fixes: fit to stamp

**Verdict.** The diff is correct and breaks nothing I could find, so the package is fit to stamp now. The only point left is an optional one-word change to the prespec.

**What I checked.** Everything ran in fresh copies under `/tmp/claude-0/-home-claude/8ff2db7c-f7cd-5897-8207-48e2e1d8242b/scratchpad/c2/review2/`. I did not touch the repository, did not use the gate's seeds, and solved nothing on the gate's mesh.

- **Scope of the change:** the repository differs from the tree I audited in exactly the five files. `round2_fixes.diff` applied to my audited copy reproduces all five byte for byte, and `src/` is unchanged.
- **Tests:** the three test files give `31 passed`, with no warnings, in 210 s. This matches the runbook's new count.
- **Stamp helper:** run on a copy, it gives config hash `795515630ff6f37a819c7503931c7d7cf6e70a9f272e25ac96730394dd361fb4`, the same as `write-config`. The hash file has 26 lines and `sha256sum -c` reports 0 failures.

### Each fix

- **S1 (seeds and disclosure)**
  - `SEEDS_SEEN = [7, 8, 101, 102]`. The tests still hold, because `small_cfg` drops only 7 and 8. The pilot scripts set their own `seeds_seen`, so they are unaffected.
  - I read the dry runs' configurations without changing anything:
    - boxA: seeds 101 and 102, 4 training and 2 held-out members, coarse mesh, width 32, depth 1, 6 epochs, levels [1, 4, 8], all four tested members labelled.
    - `dry2` uses the same seeds and lists all four tested members.
    - The new prespec text describes both runs correctly.
  - The account of the second review is accurate, including "at most 6e-11", which I measured as 5.9e-11.
  - The 22 corners are right: 22 of the 32 combinations pass `violations`.
- **M3 (multiplier limits):** the new wording matches the code. `min_lambda >= -1e-8` covers every contact unknown.
- **M4 (`_quantile`)**
  - I compared it with a brute-force quantile that keeps infinities: n from 1 to 79 and 447 to 1001, q of 0.1, 0.5 and 0.9, and every count of infinite rows. That is 23,814 cases, with 0 mismatches and no huge finite values.
  - It equals `np.quantile` whenever nothing is infinite.
  - Its index, (n-1)q, is the one numpy's linear method uses. For example, n = 21 and q = 0.9 give exactly 18, so a stand-in with zero weight is ignored.
  - An empty input is never passed (guarded by `v.size`). A NaN still reaches the existing assertion.
  - The new test's cases are right.
- **M5 (docstring):** fixed.
- **M6 (worker order)**
  - Results are now sorted by member id inside the `with` block, which matches the single-worker order.
  - Through the CLI, on a tiny seen-seed configuration (seeds 8 and 7, coarse mesh):
    - `label --workers 2` worked on all three splits (all converged) and check-labels passed;
    - six tiny trainings ran;
    - `evaluate` with 1 and with 2 workers gave byte-identical `verdict.json`.
  - This runs both Pool branches independently of your second dry run.
- **M7 (W one-liner)**
  - `len(os.sched_getaffinity(0))` is used in both one-liners, and the comments now match the code.
  - On the C1.3 box's cgroup (`cpu.max` 25 CPUs) W is still 24.
- **M8 (pilot row):** the row now reads 34.8% to 102.8%, 80.0% to 192.8% and 34.9% to 71.3%. These match the pilot README, and the added sentence is accurate.
- **M9 (evaluation time note):** reasonable.
- **M10 and your 0b change**
  - All three new blocks pass `bash -n`.
  - I ran them verbatim on a toy origin with an annotated tag and HOME pointed at a sandbox:
    - **Fetch path:** "fresh", the new tag, the commit printed, the worktree at the tag (`git describe` gives `prereg-c2`), and `records` created.
    - **Re-running the worktree block:** it takes the "exists" branch and lands on the same commit.
    - **Bundle path, with the origin unreachable:** the fetch fails visibly, then FETCH-OK, then the worktree.
  - `make_song_c2.py` now asserts 13 blocks, which matches the runbook.
- **M1 and M2 (solver guard, dead test):** left as they were, which I accept. Neither can affect a run: every slope in 92 solves was negative, and the dead test is harmless.

### Nits, optional

- **Prespec, "Members built but not solved":** "about 4,600 unknowns" is the number of *free* unknowns of the largest corner. That member has 5,053 unknowns in all, 428 of them fixed. The manifest's `unknowns` field would show 5,053, so "about 4,600 free unknowns" avoids confusion. The conclusion is unaffected: these sizes are far below the direct solver's limit of 45,000.
- **`c2/config.py:17-18`:** the comment says "a dry run"; there were two.

**For your disclosure.** In this round I also built six of the 22 corner members, without solving them, and repeated the tiny train-and-evaluate run on members of seeds 7 and 8 on the coarse mesh. Both are already covered by the prespec's wording.

Fit to stamp now.
