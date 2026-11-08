# Gate G-C2.1: verdict

**What was pre-specified**
- `docs/PRESPEC_G-C2.1.md`, configuration SHA-256 `795515630ff6f37a819c7503931c7d7cf6e70a9f272e25ac96730394dd361fb4`, stamped at 20:38 GMT on 6 November 2026.
- The tag `prereg-c2`, made at 22:10 GMT the same evening, points to commit `896e040` (21:18 GMT). The repository code the run imports is pinned file by file in `docs/G-C2.1_code.sha256`.
- The operator worked from a Chinese version of `RUNBOOK_C2.md`, with its commands copied verbatim and the same checkpoints. That version is not in the repository.

**Where the numbers come from**
- **The return package**: `c2_return.tar.gz`, SHA-256 `7b6f19e6c316b0a3bf39c6821206f9e061dc2d8b1fc09724acdad125946b3ae0`, 51,271,219 bytes. The SHA-256 reported with it matches the file.
  - Its 110 files are kept as received in `records/c2/return/`.
  - `records/c2/return_files.sha256` lists their hashes.
  - `records/c2/return_listing.txt` is the archive's own listing, with the time of each file in CST (UTC+8). By it, the folder the package was assembled in last changed at 16:29 CST on 8 November 2026.
- **The verdict and every metric** come from `records/c2/return/verdict.json`, which the stamped `c2/evaluate.py` wrote on the GPU host.
- **The author's recomputation**: `audit/c2_recompute.py` (not under the stamp; written after the run) reproduces them. It regenerates all 580 instances from the stamped code, recomputes every metric of the label-free arm on the 64 held-out and 4 tested members from the returned predictions and labels, and re-solves four members. Its outputs are in `records/c2/audit/`.
- **The tables** at the end are generated from those records by `audit/c2_write_verdict.py`, also written after the run.

**Independent audit** (8 November 2026), with its own code:
- The return package has the SHA-256 and size reported. Its 110 files are those kept in `records/c2/return/`, byte for byte, and `return_listing.txt` is the archive's listing.
- The run used the stamped commit `896e040`. Its configuration hash, its 20 code hashes and its 6 repository hashes are those of the stamp, and the returned configuration is the stamped one. The 26 file hashes checked, and the 31 tests passed.
- The 132 members were labelled once each, at the configured levels; every level converged, within the residual limits. Each of the six runs ran once, with no resume, to its configured number of steps.
- The predictions of every run cover exactly the 64 held-out and 4 tested members. They are finite, every fixed unknown is zero and every contact unknown is non-negative.
- From the per-pair rows of `verdict.json`, the audit recomputed each seed's median and 90th percentile, C1 (6.61%), C2 (31.2%) and the verdict, FAIL: all identical. The end displacement errors and the force errors at the same $D$ of all 2,856 predicted fields, recomputed from the predictions and labels, equal those of `verdict.json` exactly.
- It regenerated all 580 instances. Written through zlib 1.3, all 580 files have the manifest's SHA-256 and sizes. Written through zlib-ng, the five it tried have other SHA-256 values, with the same arrays.
- With the stamped library it solved 12 pairs of eval_0026 and eval_0030 at their predicted end displacements. The 11 finite distances agree with `verdict.json` to within 7e-13 in relative terms. The infinite one is reproduced: a reference force of -140.6 N at an end displacement of 0.0004 mm. The other readings of all six runs on these two members agree to within 6e-14.
- It found eight errors in the draft of this verdict, its tables, its scripts and the README. Among them were a sentence on C1 that the next one contradicted, and a README line that claimed more than the pre-specification allows. It found two omissions: the overall readings of the tested members, which the pre-specification requires, and a departure from the runbook (deviation 4 below). It raised fifteen smaller points of sources, wording and rounding. This text takes up all of them.
- Its second reading of the final text found one more error, a sentence that credited the audit with recomputing every metric, and seven smaller points. This text takes them up too. It reran `audit/c2_write_verdict.py` and got the same tables byte for byte, before the one change to them that it asked for.

## Run record

**Host** (`provenance.log`, 15:49 CST on 7 November 2026)
- `autodl-container-eb3344896e-709d725c`: an RTX 5090 with NVIDIA driver 595.71.05; a Xeon Platinum 8470Q with a quota of 25 CPUs; a memory limit of 98,784,247,808 bytes.
- torch 2.12.1+cu130, numpy 2.4.6, scipy 1.18.1, Python 3.12.3.
- pypardiso did not load, so the labels were solved with scipy's SuperLU, as the ledger records. The evaluation does not log its solver; it ran in the same environment, so it used SuperLU too (inferred).

**Preconditions** (sections 0 and 1 of the runbook)
- The worktree was at the tag and clean, with 16 GB free. pgrep found no other run of the gate's or the repository's code.
- All 26 hashes of `docs/G-C2.1_code.sha256` checked, and the 31 tests passed.
- The configuration hash was the stamped one, the twenty code hashes those of the stamp, and the six repository files checked.

**Generation and bench**
- 580 instances were generated: 512 training, 64 held-out and 4 tested members.
- The bench took 0.167 s a step on average. All 45 of its losses were finite.
- It bounded the training at 16.0 h, inside the stop rule of 0.30 s a step. Its peak memory and the training set's energies took 3.6 GiB of the GPU's 31.8 GiB.

**Labels**
- 132 members were labelled once each, by 24 worker processes, in 33 s to 144 s a member: the 64 held-out and 4 tested members at seven levels, and the first 64 training members at six.
- Every level converged and the label check passed. Every worst optimality residual was within its limit (the tables give them). The two force readings of every reference, the spring's and the stresses', agreed to 2.9e-13.

**Training**
- From 16:16:03 CST on 7 November to 07:22:43 CST on 8 November 2026 (08:16:03 to 23:22:43 GMT on 7 November): 15.1 h, inside the bench's bound.
- Each of the six runs ran once, from start to end, with no resume. Each began within 2 s of the previous one's end and finished with its configured number of steps. No loss and no prediction was non-finite.
- A label-free epoch (512 steps) took 78 s to 90 s: 0.164 s to 0.173 s a step in the median epoch of each run. A supervised epoch (64 steps) took about 3.6 s.

**Evaluation**
- Every run had its predictions, for all 64 held-out and 4 tested members. No run was missing and none was non-finite.
- `evaluate.log` was written at 16:27 CST on 8 November, 9 h 5 min after the end of training. When the evaluation started was not logged.

## Deviations

None of them changes a number of the run.

1. **The GPU reading before the run.**
   - In section 0c and before the bench, `nvidia-smi` reported a utilisation of 100% with 2 MiB of memory in use. The runbook's comment expected about 0%, and its rule is to stop and report on any output that differs from a comment.
   - The operator went on.
   - With 2 MiB in use, no process held memory on the GPU (inferred). The bench, at 0.167 s a step, lay within the range of the label-free training that followed a reading of 0%: 0.164 s to 0.173 s a step in the median epochs. So the records show no sign of a competing load. As in G-C1.3, the 100% reading was most likely a reporting artefact (inferred).
2. **The CPUs seen by the shell.** The third provenance entry, at 16:15 CST before the training, reports 208 CPUs from `nproc`, where the first two report 25.
   - The host name, the driver and the container's quota of 25 CPUs are unchanged. So this was most likely a shell with a wider CPU affinity, outside the run's tmux session for one, or a changed CPU set (inferred).
   - The runbook's worker count takes the smaller of the two, less one: 24, as `label.log` records for the labels. The evaluation computes it the same way but does not log it.
3. **The time of the evaluation.** The runbook asks for a report if the evaluation has not ended after 6 h. Its start was not logged, so the records cannot tell whether it ran that long.
4. **Seed 0's loss.** The runbook's comment on the training (section 5) expects the label-free loss to end at about 10.3 to 10.6, as "numbers, not criteria".
   - Seed 0's ended at 10.74 in its last epoch, at 20:59 CST on 7 November, and averaged 10.64 over its last 20 epochs. Seeds 1 and 2 ended at 10.40 and 10.42.
   - By the runbook's general rule an output that differs from a comment is reported. No report is recorded.
   - No pre-specified stop applies to a loss that does not fall, so a report would not have changed the run (inferred).

The records show no other departure. Some outputs that the runbook checks by eye were not logged: the `fresh` line and the fetch of section 0b, and the summary lines of sections 2 and 3. The files those lines read, the manifest and `bench.json`, hold the expected values.

## Verdict

**FAIL on both criteria, judged as pre-specified.**
- **C1**: the median over the three seeds of the per-seed median distance from the reference curve is 6.61%, against a threshold of 5%. The seeds give 17,012%, 6.61% and 2.41%.
- **C2**: the median over the three seeds of the per-seed 90th percentile of that distance is 31.2%, against a threshold of 10%. The seeds give 507,506%, 31.2% and 18.6%.
- No label-free seed stopped, and none was missing.

**The recomputation**
- The author recomputed every metric of the three label-free runs from the returned predictions and labels, on the 64 held-out and 4 tested members. The recomputation used the stamped metric function and the host's numpy 2.4.6 and scipy 1.18.1, on one BLAS thread a process with scipy's SuperLU.
  - All 1,428 pairs give the returned values to the last bit, in every metric and in the bound's containment. So the medians, the 90th percentiles, C1, C2 and the verdict are the returned ones exactly.
  - The audit, with its own code, recomputed the criteria from the returned per-pair values, the end displacement errors and the force errors at the same $D$ of every pair, and every reading of two members (above).
- The returned labels, evaluated by the author on the regenerated instances, give the label's force and end displacement exactly and its energy to within 3.3e-16 in relative terms. Their largest unconstrained residual there is 1.3e-10 (`aggregate.json`).
- The author regenerated all 580 instances from the stamped code. The bytes of an instance file depend on the zlib that numpy's `savez_compressed` writes through. Written through zlib 1.3, all 580 files have the manifest's SHA-256 (`regenerate.json`), so the host's numpy wrote through zlib 1.3 too (inferred; the host did not log its zlib). Written through zlib-ng, which the author's development machine has, the five files the audit tried have other SHA-256 values, with the same arrays.
- Four members (three held-out, one tested), re-solved by the author from the regenerated instances with the host's solver and numpy version, reproduce the returned labels bit for bit, in the ledger's numbers of iterations (`resolve.json`).
- A first pass of the author's recomputation, with numpy 2.5.3, was stopped after six members, when the author switched to the host's version (`records/c2/audit/numpy253/`). Its metrics differ from the returned ones by at most 3e-12 in the distance from the curve (2.6e-14 in seeds 1 and 2), and its four re-solves differ from the labels by at most 2e-14 of the largest unknown.

## What this means

**As fixed in advance (FAIL on both)**
- At this budget the label-free surrogate does not reproduce the plastic force-deformation curve within these limits.
- The thresholds stay. The supervised arm and the reported readings below are described, not substituted for the criteria. Any next stage is pre-specified anew.

**How it failed**
- **Seed 0 did not train.**
  - Its loss stayed at its starting level for all 200 epochs: 10.61 in the mean of the first 20 epochs and 10.64 in the last 20. The losses of seeds 1 and 2 fell from 10.59 and 10.55 to 10.36 and 10.37.
  - Its predicted fields stayed near the field the network starts from. With the last layers of the decoder and the head zeroed at the start, that field is zero except for the non-negative unknowns, which start at $T \ln 2\,(D + \delta)$, the softplus of a zero output.
  - In the median, the predicted unknowns were 0.6% of the label's in norm, and 0.5% of it from the starting field (audit). The predicted end displacements were 0.3% of the reference's.
  - The predicted fields are uniform in space. In every pair, all free nodes share one $u_y$, and those off the web and off the contact plane, where the $x$ unknown is the separation, share one $u_x$ (audit). On the held-out members its 1,939,420 predicted unknowns take only 4,940 distinct values, against 1.76 million in each of the other five runs.
  - With the end displacement near zero, the spring reading $4 k_s (D - e)$ is close to $4 k_s D$, far above the reference force at so small an end displacement: hence a median distance of 17,012%. In 44 of its 448 pairs, at the three smallest levels, the reference force at the predicted end displacement is not positive, an infinite distance. These pairs have predicted end displacements of 0.0004 to 0.0016 mm, in members with preload ratios of 0.23 to 0.88.
  - The run ended normally, with finite losses and predictions, so none of the pre-specified stops applies: the seed enters the medians with its errors, as a finished seed does. (The pre-specification calls a FAIL decided by a stopped seed a failure of training at these settings; seed 0 did not stop.)
  - Why it did not leave its starting point was not examined.
- **Seeds 1 and 2 trained.**
  - C2 fails on them alone: their 90th percentiles are 31.2% and 18.6%.
  - C1 turns on seed 0. Its median distance and seed 1's (6.61%) are above 5%, and seed 2's (2.41%) is within it. Had seed 0's median been at most 5%, the median over the seeds would have been too.
- **The tail of each trained seed**, the 45 pairs above its 90th percentile, lies mostly at the largest levels and in the members with the lowest yield stress. In seeds 1 and 2, 33 and 31 of these pairs are at 6 and 8 mm, and 32 and 38 are in the 20 held-out members with a yield stress below 300 MPa.
  - At $D$ = 8 mm the median distance is 17.0% and 9.5% in seeds 1 and 2, and the 90th percentile 73% and 47%. Up to 2 mm seed 2's median is 1.4% to 1.7%.
  - The distance at 8 mm falls as the yield stress rises (Pearson's correlation -0.62 in both seeds). Its median is 51% and 32% in the 20 members below 300 MPa, against 11% and 6.6% in the other 44.
  - It exceeds 10% in many stronger members too: 25 of seed 1's 44 pairs above 10% at 8 mm, and 13 of seed 2's 31, are in members at or above 300 MPa.
  - Of the five largest distances at 8 mm in each seed, nine of the ten are in members with yield stresses of 240 to 268 MPa: 68% to 159% at 8 mm, against 0% to 12% at 0.5 mm. The tenth, 89% in seed 1, is in a member with 307 MPa.
- **The errors lean one way**: the signed median distance is +4.7% and +2.0%. The predicted end displacements are too small, by 4.6% and 2.1% in the median, and the forces at the same $D$ too large, by 1.5% and 0.5%.

**Against the expectation stated before the run**
- The pre-specification expected the gate to fail, on C2 at least, and held C1 uncertain. Every seed's 90th percentile exceeded 10%. C1 failed by 1.6 points in the median seed, seed 1; seed 2's median, 2.41%, was within 5%.
- The pilot's tail came from two places: its weakest member from $D$ = 3 mm on, and the two smallest levels of two members. Here the tail came mainly from the first: the members with low yield stress at the larger levels. The two smallest levels hold 5 of seed 1's 45 tail pairs and none of seed 2's.
- The errors leant one way, as expected: +4.7% and +2.0% in the signed median, against +8.5% in the pilot.
- A seed that does not train was not foreseen.

**The supervised arm** (descriptive, as pre-specified): the first 64 training members with six solved levels each, 384 labelled fields, and an eighth of the label-free arm's steps.
- Its median distance from the curve was 7.4%, 6.0% and 5.3%, against 6.6% and 2.4% for the label-free seeds that trained. Its 90th percentile was 29.0%, 20.6% and 16.1%, against 31.2% and 18.6%. No seed of either arm had a 90th percentile within 10%.
- Its distances are largest at the smallest level (medians of 8.4% to 19.4% at 0.5 mm) and smallest at 4 mm (2.7% to 3.7%). Those of label-free seeds 1 and 2 are largest at 8 mm.
- Its fields are far from the solution in energy: an energy gap of 119% to 211% in the median, against 1.1% and 0.42% for label-free seeds 1 and 2, and a contact overlap of 0 to 0.51, against 0.85 and 0.96.
- In one pair of its seed 1, at 0.5 mm, the reference solve at the predicted end displacement failed: an infinite distance.

**Other readings** (reported, not judged; label-free seeds 1 and 2, medians over the 448 held-out pairs)
- The force at the same $D$ was within 2.3% and 0.8% of the reference in the median, much closer than the distance from the curve. As the pre-specification explains, in the elastic range the spring sets the force at the same $D$ and hides the T-stub's error.
- The certified bound $4\sqrt{2 k_s (\Pi - \Pi^*)}$ contained the force error in every pair of every run, as the theorem says.
- The energy gap was 1.1% and 0.42%. The displacements were within 12.8% and 3.8% of the reference in relative norm. The contact overlap was 0.85 and 0.96, and the overlap of the plastic Gauss points 0.71 and 0.79.
- **The four tested members** (Bursi and Jaspart's T1 and T2, preloaded and snug, as members of the family):
  - In seed 2 the distance from the curve was at most 8.6% at every level of T1, and at most 3.1% up to 4 mm for T2, rising to 16% and 18% at 8 mm.
  - In seed 1 it reached 49% and 39% at the smallest level of the snug T1 and T2.
  - In seed 0 it was 10,966% or more, or infinite. The tables give every reading of every arm and seed, overall and by level.

**What it does not show**
- Anything about the T-stub tests, that is, the experiments.
- Unloading, cyclic loading or other load paths that are not monotonic; large displacements, friction, fracture or bolts that bend; other meshes, or T-stubs outside this family.
- Why seed 0 did not train, or whether more steps, another schedule or other seeds would have changed the outcome: no such run was made.

## Consequences

- **The thresholds stay**, and any next stage of the plastic surrogate is pre-specified anew, as fixed in advance.
- **Any summary of this gate** reports the FAIL on both criteria and names seed 0, which did not train.
- **A surrogate gate on the CHS splices of G-F1** is planned, with the same training code. Its pre-specification will have to deal with both ways this gate failed: a seed that does not leave its starting field, and the tail at the largest levels in the members with low yield stress.

## Numbers

The tables follow in `docs/G-C2.1_verdict_numbers.md`; they are appended below in the assembled verdict.
