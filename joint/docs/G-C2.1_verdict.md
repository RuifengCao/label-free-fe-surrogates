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


<!-- generated by audit/c2_write_verdict.py from records/c2/return and records/c2/audit; config 795515630ff6f37a819c7503931c7d7cf6e70a9f272e25ac96730394dd361fb4 -->

### Criteria (label-free arm; 64 held-out members at seven levels, 448 pairs a seed)

The distance of a pair from the curve is abs(F / F\*(e) - 1): F = 4 k_s (D - e) is the spring reading of the predicted field and F\*(e) the reference force at its end displacement e.

| Seed | Median distance | 90th percentile | Infinite distances |
|---|---|---|---|
| 0 | 17,012% | 507,506% | 44 |
| 1 | 6.611% | 31.160% | 0 |
| 2 | 2.412% | 18.561% | 0 |
| **Median over seeds** | **6.611%** (C1: at most 5%) | **31.160%** (C2: at most 10%) | |

C1 = False; C2 = False; verdict = **FAIL**. Status of the six runs: label_free_s0 finished, label_free_s1 finished, label_free_s2 finished, supervised_64_s0 finished, supervised_64_s1 finished, supervised_64_s2 finished. Missing runs: 0; non-finite runs: 0. Recomputed by `audit/c2_recompute.py` from the returned predictions and labels: C1 6.611%, C2 31.160%, FAIL.

### Every arm and seed, held-out pairs (reported)

Medians over the 448 pairs unless marked. Signed errors are prediction over reference, less 1. The force at the same D is the spring reading against the reference's at that D; the stress reading is the force the predicted field's stresses carry, against the same reference; the bound is 4 sqrt(2 k_s (Pi - Pi\*)) over the reference force; the energy gap is (Pi - Pi\*) / abs(Pi\*).

| Run | Distance | Distance, p90 | Signed distance | Above 10% | Infinite | Force at the same D, abs error | Force at the same D, signed error | End displacement e error | Stress reading error | Energy gap | Bound | Within bound | Contact overlap | Plastic overlap | Bolt force error | Displacement error | Not evaluated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| label_free s0 | 17,012% | 507,506% | +17,012% | 448 | 44 | 32.0% | +32.0% | -99.7% | -100.6% | 22.49% | 57.7% | 100% | 0.149 | 0.000 | -46.08% | 99.5% | 0 |
| label_free s1 | 6.6% | 31.2% | +4.7% | 153 | 0 | 2.3% | +1.5% | -4.6% | +2.8% | 1.13% | 13.4% | 100% | 0.845 | 0.710 | +0.01% | 12.8% | 0 |
| label_free s2 | 2.4% | 18.6% | +2.0% | 74 | 0 | 0.8% | +0.5% | -2.1% | +1.5% | 0.42% | 8.4% | 100% | 0.962 | 0.790 | +0.08% | 3.8% | 0 |
| supervised_64 s0 | 7.4% | 29.0% | -0.9% | 163 | 0 | 3.1% | -0.5% | +0.9% | +52.3% | 210.90% | 185.0% | 100% | 0.476 | 0.198 | +0.00% | 11.7% | 0 |
| supervised_64 s1 | 6.0% | 20.6% | -0.9% | 128 | 1 | 2.4% | -0.4% | +0.9% | +62.8% | 160.00% | 155.8% | 100% | 0.000 | 0.241 | -0.00% | 10.8% | 0 |
| supervised_64 s2 | 5.3% | 16.1% | -0.8% | 112 | 0 | 2.1% | -0.3% | +0.8% | +26.6% | 118.79% | 134.7% | 100% | 0.511 | 0.248 | -0.00% | 11.1% | 0 |

The infinite distances, with the note the evaluation wrote (levels in mm):

- label_free s0, held-out: "the reference force at the predicted end displacement is not positive", 44 pairs: 28 at 0.5, 15 at 1, 1 at 2; predicted end displacement 0.0004 to 0.0016 mm, preload ratio 0.23 to 0.88.
- label_free s0, tested: "the reference force at the predicted end displacement is not positive", 3 pairs: 2 at 0.5, 1 at 1; predicted end displacement 0.0004 to 0.0008 mm, preload ratio 0.82.
- supervised_64 s1, held-out: "RuntimeError: bubble condensation did not converge", 1 pair: 1 at 0.5; predicted end displacement 0.1040 mm, preload ratio 0.84.

### The distance by level, held-out members (64 a level)

**Median distance**

| Run | 0.5 mm | 1 mm | 2 mm | 3 mm | 4 mm | 6 mm | 8 mm |
|---|---|---|---|---|---|---|---|
| label_free s0 | 158,678% | 23,101% | 16,646% | 16,024% | 15,854% | 14,988% | 14,388% |
| label_free s1 | 7.8% | 6.4% | 5.2% | 6.0% | 5.4% | 5.2% | 17.0% |
| label_free s2 | 1.7% | 1.4% | 1.7% | 1.6% | 2.6% | 3.4% | 9.5% |
| supervised_64 s0 | 19.4% | 13.1% | 8.4% | 5.9% | 3.1% | 5.3% | 8.3% |
| supervised_64 s1 | 10.8% | 9.3% | 6.8% | 6.2% | 3.7% | 4.2% | 6.4% |
| supervised_64 s2 | 8.4% | 7.5% | 6.5% | 3.9% | 2.7% | 4.3% | 7.7% |

**90th percentile of the distance**

| Run | 0.5 mm | 1 mm | 2 mm | 3 mm | 4 mm | 6 mm | 8 mm |
|---|---|---|---|---|---|---|---|
| label_free s0 | infinite | infinite | 67,055% | 34,562% | 29,077% | 25,334% | 23,953% |
| label_free s1 | 23.2% | 19.7% | 15.2% | 18.4% | 19.8% | 37.1% | 73.4% |
| label_free s2 | 4.5% | 3.3% | 4.6% | 15.1% | 21.1% | 33.3% | 46.6% |
| supervised_64 s0 | 47.3% | 36.0% | 23.3% | 12.5% | 8.2% | 20.4% | 42.4% |
| supervised_64 s1 | 28.7% | 21.3% | 14.6% | 11.8% | 9.2% | 11.6% | 25.9% |
| supervised_64 s2 | 23.8% | 16.8% | 13.6% | 9.7% | 6.6% | 10.9% | 19.0% |

**Pairs above 10%**

| Run | 0.5 mm | 1 mm | 2 mm | 3 mm | 4 mm | 6 mm | 8 mm |
|---|---|---|---|---|---|---|---|
| label_free s0 | 64 | 64 | 64 | 64 | 64 | 64 | 64 |
| label_free s1 | 26 | 19 | 12 | 13 | 15 | 24 | 44 |
| label_free s2 | 0 | 0 | 3 | 11 | 11 | 18 | 31 |
| supervised_64 s0 | 44 | 39 | 27 | 11 | 6 | 10 | 26 |
| supervised_64 s1 | 34 | 31 | 19 | 10 | 4 | 7 | 23 |
| supervised_64 s2 | 26 | 26 | 18 | 7 | 2 | 9 | 24 |

**Median signed distance**

| Run | 0.5 mm | 1 mm | 2 mm | 3 mm | 4 mm | 6 mm | 8 mm |
|---|---|---|---|---|---|---|---|
| label_free s0 | +158,678% | +23,101% | +16,646% | +16,024% | +15,854% | +14,988% | +14,388% |
| label_free s1 | +6.0% | +2.9% | +2.1% | -2.2% | +4.1% | +5.2% | +17.0% |
| label_free s2 | +1.1% | +0.8% | +1.4% | +1.0% | +2.2% | +3.1% | +9.5% |
| supervised_64 s0 | -10.8% | -6.2% | -2.0% | -2.8% | -0.3% | -1.2% | +6.8% |
| supervised_64 s1 | -1.9% | +3.2% | -2.2% | -5.3% | -1.2% | -1.5% | +3.6% |
| supervised_64 s2 | -5.1% | +0.6% | +1.9% | -2.6% | -0.7% | -0.5% | +5.3% |

**The other readings by level** (medians over the 64 held-out members at each level, over the pairs the reference code evaluated; the counts are of pairs)

| Run | D (mm) | Force at the same D, signed error | Abs error | Bound | Within bound | End displacement e error | Stress reading error | Energy gap | Contact overlap | Plastic overlap | Bolt force error | Displacement error | Infinite distances | Not evaluated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| label_free s0 | 0.5 | +14.0% | 14.0% | 44.8% | 64 of 64 | -99.3% | -100.5% | 12.51% | 0.278 | 1.000 | +5.51% | 98.9% | 28 | 0 |
| label_free s0 | 1 | +15.7% | 15.7% | 43.3% | 64 of 64 | -99.4% | -100.5% | 14.56% | 0.248 | 1.000 | -11.60% | 99.1% | 15 | 0 |
| label_free s0 | 2 | +18.4% | 18.4% | 46.0% | 64 of 64 | -99.5% | -100.5% | 17.24% | 0.190 | 0.000 | -45.72% | 99.2% | 1 | 0 |
| label_free s0 | 3 | +26.0% | 26.0% | 52.4% | 64 of 64 | -99.6% | -100.5% | 20.51% | 0.119 | 0.000 | -55.41% | 99.5% | 0 | 0 |
| label_free s0 | 4 | +56.8% | 56.8% | 74.3% | 64 of 64 | -99.8% | -100.6% | 28.72% | 0.049 | 0.000 | -56.74% | 99.7% | 0 | 0 |
| label_free s0 | 6 | +122.9% | 122.9% | 132.8% | 64 of 64 | -99.9% | -100.9% | 57.01% | 0.048 | 0.000 | -59.16% | 99.8% | 0 | 0 |
| label_free s0 | 8 | +179.9% | 179.9% | 193.1% | 64 of 64 | -99.9% | -101.1% | 87.16% | 0.048 | 0.000 | -61.02% | 99.8% | 0 | 0 |
| label_free s1 | 0.5 | +0.8% | 0.9% | 9.6% | 64 of 64 | -5.8% | +0.0% | 0.52% | 0.859 | 1.000 | -2.43% | 9.9% | 0 | 0 |
| label_free s1 | 1 | +0.4% | 0.8% | 7.3% | 64 of 64 | -3.0% | +0.3% | 0.43% | 0.890 | 1.000 | +0.87% | 11.1% | 0 | 0 |
| label_free s1 | 2 | +0.4% | 1.0% | 8.7% | 64 of 64 | -2.0% | +2.4% | 0.60% | 0.883 | 0.621 | +2.52% | 8.5% | 0 | 0 |
| label_free s1 | 3 | -1.0% | 2.4% | 10.4% | 64 of 64 | +4.8% | +3.4% | 0.86% | 0.657 | 0.609 | +0.01% | 15.0% | 0 | 0 |
| label_free s1 | 4 | +3.3% | 4.5% | 18.4% | 64 of 64 | -6.2% | +6.7% | 1.74% | 0.863 | 0.629 | +0.00% | 13.5% | 0 | 0 |
| label_free s1 | 6 | +4.6% | 4.6% | 26.0% | 64 of 64 | -4.1% | +3.5% | 2.61% | 0.703 | 0.665 | +0.01% | 13.4% | 0 | 0 |
| label_free s1 | 8 | +16.1% | 16.1% | 41.0% | 64 of 64 | -8.3% | +9.4% | 4.15% | 0.655 | 0.693 | +1.03% | 19.8% | 0 | 0 |
| label_free s2 | 0.5 | +0.2% | 0.3% | 5.1% | 64 of 64 | -1.2% | +0.6% | 0.15% | 0.965 | 1.000 | +0.33% | 2.2% | 0 | 0 |
| label_free s2 | 1 | +0.1% | 0.2% | 4.1% | 64 of 64 | -0.8% | +0.8% | 0.14% | 0.969 | 1.000 | +0.13% | 2.0% | 0 | 0 |
| label_free s2 | 2 | +0.2% | 0.3% | 4.3% | 64 of 64 | -1.5% | -0.0% | 0.15% | 0.973 | 0.711 | +0.01% | 2.5% | 0 | 0 |
| label_free s2 | 3 | +0.4% | 0.8% | 6.4% | 64 of 64 | -1.6% | +1.0% | 0.29% | 0.932 | 0.707 | +0.00% | 4.7% | 0 | 0 |
| label_free s2 | 4 | +1.9% | 2.0% | 12.6% | 64 of 64 | -3.3% | +3.7% | 0.68% | 1.000 | 0.705 | +0.00% | 6.6% | 0 | 0 |
| label_free s2 | 6 | +2.7% | 3.0% | 24.0% | 64 of 64 | -2.6% | +3.6% | 1.91% | 0.861 | 0.738 | +0.21% | 7.9% | 0 | 0 |
| label_free s2 | 8 | +9.0% | 9.0% | 38.3% | 64 of 64 | -5.2% | +7.1% | 3.25% | 0.710 | 0.724 | +1.44% | 17.3% | 0 | 0 |
| supervised_64 s0 | 0.5 | -1.9% | 3.2% | 138.7% | 64 of 64 | +12.5% | +67.5% | 110.91% | 0.702 | 0.000 | +12.73% | 14.7% | 0 | 0 |
| supervised_64 s0 | 1 | -1.0% | 2.4% | 119.5% | 64 of 64 | +6.7% | +48.8% | 112.07% | 0.803 | 0.000 | +8.92% | 11.4% | 0 | 0 |
| supervised_64 s0 | 2 | -0.5% | 1.8% | 115.1% | 64 of 64 | +2.4% | +37.0% | 103.83% | 0.732 | 0.027 | -4.86% | 10.7% | 0 | 0 |
| supervised_64 s0 | 3 | -1.8% | 3.1% | 130.9% | 64 of 64 | +5.8% | +27.9% | 125.62% | 0.489 | 0.198 | +0.00% | 12.2% | 0 | 0 |
| supervised_64 s0 | 4 | -0.3% | 2.6% | 242.0% | 64 of 64 | +0.5% | +41.5% | 309.49% | 0.000 | 0.319 | -0.01% | 9.6% | 0 | 0 |
| supervised_64 s0 | 6 | -1.1% | 4.8% | 426.6% | 64 of 64 | +1.0% | +116.7% | 589.33% | 0.000 | 0.437 | -0.03% | 9.9% | 0 | 0 |
| supervised_64 s0 | 8 | +6.4% | 7.9% | 694.4% | 64 of 64 | -3.2% | +256.4% | 1,087% | 0.000 | 0.519 | -0.02% | 12.3% | 0 | 0 |
| supervised_64 s1 | 0.5 | -0.3% | 1.6% | 88.6% | 64 of 64 | +1.9% | +58.5% | 49.98% | 0.364 | 0.000 | +5.76% | 15.4% | 1 | 0 |
| supervised_64 s1 | 1 | +0.5% | 1.5% | 81.6% | 64 of 64 | -3.2% | +47.0% | 53.25% | 0.267 | 0.000 | -0.00% | 10.1% | 0 | 0 |
| supervised_64 s1 | 2 | -0.4% | 1.4% | 89.5% | 64 of 64 | +2.2% | +46.6% | 65.24% | 0.000 | 0.014 | -9.09% | 10.0% | 0 | 0 |
| supervised_64 s1 | 3 | -2.9% | 3.6% | 133.9% | 64 of 64 | +10.0% | +54.5% | 130.48% | 0.195 | 0.179 | +0.00% | 11.0% | 0 | 0 |
| supervised_64 s1 | 4 | -1.1% | 3.0% | 228.4% | 64 of 64 | +1.6% | +76.0% | 278.66% | 0.000 | 0.289 | -0.00% | 9.5% | 0 | 0 |
| supervised_64 s1 | 6 | -1.4% | 3.8% | 452.9% | 64 of 64 | +0.8% | +166.3% | 681.26% | 0.000 | 0.427 | -0.01% | 9.0% | 0 | 0 |
| supervised_64 s1 | 8 | +3.4% | 6.1% | 737.7% | 64 of 64 | -2.1% | +242.2% | 1,221% | 0.000 | 0.526 | -0.11% | 12.9% | 0 | 0 |
| supervised_64 s2 | 0.5 | -0.9% | 1.3% | 81.3% | 64 of 64 | +5.4% | +30.0% | 42.65% | 0.622 | 0.000 | +6.51% | 14.4% | 0 | 0 |
| supervised_64 s2 | 1 | +0.1% | 1.1% | 77.1% | 64 of 64 | -0.7% | +20.9% | 46.97% | 0.652 | 0.000 | -0.01% | 10.2% | 0 | 0 |
| supervised_64 s2 | 2 | +0.3% | 1.4% | 83.8% | 64 of 64 | -2.4% | +13.3% | 56.93% | 0.659 | 0.015 | -9.27% | 10.2% | 0 | 0 |
| supervised_64 s2 | 3 | -1.1% | 2.1% | 106.3% | 64 of 64 | +4.4% | +14.1% | 89.70% | 0.489 | 0.191 | +0.00% | 11.5% | 0 | 0 |
| supervised_64 s2 | 4 | -0.6% | 2.3% | 200.8% | 64 of 64 | +1.3% | +27.2% | 201.33% | 0.395 | 0.321 | -0.00% | 9.0% | 0 | 0 |
| supervised_64 s2 | 6 | -0.5% | 4.2% | 422.9% | 64 of 64 | +0.4% | +33.5% | 594.81% | 0.140 | 0.446 | -0.00% | 9.8% | 0 | 0 |
| supervised_64 s2 | 8 | +5.1% | 7.3% | 694.4% | 64 of 64 | -3.0% | +120.6% | 1,072% | 0.000 | 0.507 | -0.03% | 13.2% | 0 | 0 |

### The distance at 8 mm and the yield stress (held-out members: 20 below 300 MPa, 44 at or above)

| Run | Pearson correlation with the yield stress | Median, below 300 MPa | Median, at or above 300 MPa |
|---|---|---|---|
| label_free s0 | -0.295 | 17,055% | 13,705% |
| label_free s1 | -0.619 | 51.1% | 11.2% |
| label_free s2 | -0.618 | 32.4% | 6.6% |
| supervised_64 s0 | -0.556 | 22.6% | 4.2% |
| supervised_64 s1 | -0.354 | 16.3% | 5.1% |
| supervised_64 s2 | -0.444 | 14.2% | 6.1% |

**The tail: the pairs above each run's 90th percentile of the distance, and the pairs above 10% at 8 mm**

| Run | 90th percentile | Pairs above it | At 6 and 8 mm | At 0.5 and 1 mm | In members below 300 MPa | Above 10% at 8 mm | Of them at or above 300 MPa |
|---|---|---|---|---|---|---|---|
| label_free s0 | 507,506% | 45 | 0 | 44 | 20 | 64 | 44 |
| label_free s1 | 31.2% | 45 | 33 | 5 | 32 | 44 | 25 |
| label_free s2 | 18.6% | 45 | 31 | 0 | 38 | 31 | 13 |
| supervised_64 s0 | 29.0% | 45 | 14 | 29 | 17 | 26 | 9 |
| supervised_64 s1 | 20.6% | 45 | 18 | 23 | 22 | 23 | 10 |
| supervised_64 s2 | 16.1% | 45 | 16 | 24 | 20 | 24 | 10 |

**The five largest distances at 8 mm in label-free seeds 1 and 2: the members, by yield stress, and their distances at every level**

| Member | Yield stress (MPa) | Flange (mm) | Seed | 0.5 mm | 1 mm | 2 mm | 3 mm | 4 mm | 6 mm | 8 mm |
|---|---|---|---|---|---|---|---|---|---|---|
| eval_0049 | 239.8 | 8.51 | 1 | 8.3% | 0.6% | 34.2% | 27.9% | 40.9% | 89.4% | 141.4% |
| eval_0049 | 239.8 | 8.51 | 2 | 2.6% | 1.0% | 18.8% | 21.6% | 30.0% | 55.9% | 81.7% |
| eval_0026 | 241.2 | 8.84 | 1 | 0.7% | 0.9% | 23.8% | 31.0% | 51.7% | 104.7% | 159.3% |
| eval_0026 | 241.2 | 8.84 | 2 | 0.0% | 1.1% | 19.3% | 26.2% | 36.2% | 63.2% | 89.5% |
| eval_0043 | 248.6 | 15.27 | 1 | 3.5% | 6.4% | 5.8% | 42.2% | 47.3% | 58.4% | 84.8% |
| eval_0043 | 248.6 | 15.27 | 2 | 3.8% | 5.2% | 2.2% | 40.8% | 54.7% | 70.9% | 85.3% |
| eval_0046 | 265.5 | 9.80 | 1 | 12.4% | 2.4% | 22.2% | 22.3% | 36.4% | 85.6% | 136.8% |
| eval_0046 | 265.5 | 9.80 | 2 | 4.7% | 2.4% | 10.1% | 15.8% | 24.1% | 49.3% | 73.0% |
| eval_0034 | 268.5 | 8.78 | 1 | 12.3% | 0.5% | 20.3% | 23.3% | 34.9% | 78.0% | 124.5% |
| eval_0034 | 268.5 | 8.78 | 2 | 5.6% | 0.3% | 9.9% | 15.4% | 21.8% | 43.8% | 67.5% |
| eval_0052 | 306.6 | 8.30 | 1 | 17.5% | 9.8% | 6.8% | 5.4% | 15.5% | 50.6% | 89.5% |
| eval_0052 | 306.6 | 8.30 | 2 | 1.4% | 0.1% | 7.5% | 9.0% | 10.5% | 24.9% | 44.0% |

Yield stresses of the 64 held-out members: 239.0 to 455.1 MPa.

### Training, and the size of the predicted fields (held-out pairs)

| Run | Mean loss, epochs 1 to 20 | Mean loss, epochs 181 to 200 | Loss, epoch 200 | Smallest loss (epoch) | e / e_ref, median | Norm of the unknowns / label's, median (largest) | Largest predicted unknown in size | Distinct values predicted |
|---|---|---|---|---|---|---|---|---|
| label_free s0 | 10.6130 | 10.6353 | 10.7426 | 10.5188 (170) | 0.0033 | 0.57% (3.9%) | 0.007787 | 4,940 of 1,939,420 |
| label_free s1 | 10.5901 | 10.3564 | 10.3987 | 10.2655 (177) | 0.9542 | 96.96% (237.2%) | 5.074 | 1,760,228 of 1,939,420 |
| label_free s2 | 10.5548 | 10.3683 | 10.4209 | 10.2862 (190) | 0.9794 | 98.70% (240.5%) | 5.785 | 1,760,320 of 1,939,420 |
| supervised_64 s0 | 5.243e-03 | 7.947e-05 | 7.556e-05 | 7.312e-05 (189) | 1.0093 | 99.63% (167.8%) | 6.662 | 1,756,385 of 1,939,420 |
| supervised_64 s1 | 5.560e-03 | 6.117e-05 | 6.182e-05 | 5.356e-05 (192) | 1.0086 | 99.62% (172.5%) | 6.7 | 1,757,753 of 1,939,420 |
| supervised_64 s2 | 5.126e-03 | 4.186e-05 | 3.989e-05 | 3.707e-05 (199) | 1.0081 | 99.48% (180.4%) | 7.434 | 1,758,679 of 1,939,420 |

The losses are the mean training loss of each epoch (history.json): the energy loss for the label-free arm, the supervised loss for the supervised arm, so the two arms' losses are not comparable. RUNBOOK_C2.md, section 5, expects the label-free loss to end at about 10.3 to 10.6 (numbers, not criteria). The norms are those of the unknown vectors z, prediction against label, at every held-out pair; the largest unknown and the distinct values are over the predictions for the 64 held-out members.

### The four tested members, every arm and seed (reported, not judged): signed distance from the curve

| Run | Member | 0.5 mm | 1 mm | 2 mm | 3 mm | 4 mm | 6 mm | 8 mm |
|---|---|---|---|---|---|---|---|---|
| label_free s0 | BJ_T1_preloaded | infinite | infinite | +117,270% | +39,310% | +29,485% | +23,854% | +21,883% |
| label_free s0 | BJ_T1_snug | +35,224% | +35,224% | +35,224% | +35,224% | +35,224% | +35,224% | +35,224% |
| label_free s0 | BJ_T2_preloaded | infinite | +33,674% | +15,103% | +12,880% | +12,019% | +11,269% | +10,966% |
| label_free s0 | BJ_T2_snug | +21,745% | +21,745% | +21,745% | +21,745% | +21,745% | +21,745% | +21,745% |
| label_free s1 | BJ_T1_preloaded | +25.4% | +9.1% | +3.0% | +6.0% | +3.8% | -2.8% | +6.9% |
| label_free s1 | BJ_T1_snug | +49.1% | +36.0% | +12.0% | -6.9% | -3.5% | +0.2% | +12.2% |
| label_free s1 | BJ_T2_preloaded | -2.9% | -6.2% | -11.9% | +0.2% | +10.8% | +9.9% | +18.1% |
| label_free s1 | BJ_T2_snug | +39.5% | +27.1% | +7.9% | -7.7% | -0.1% | +11.1% | +22.2% |
| label_free s2 | BJ_T1_preloaded | +8.6% | +5.0% | +3.1% | +3.0% | +0.4% | +1.5% | +4.5% |
| label_free s2 | BJ_T1_snug | +3.7% | +3.5% | +2.0% | +0.9% | +1.3% | +2.4% | +5.0% |
| label_free s2 | BJ_T2_preloaded | -0.1% | -0.7% | -0.7% | -0.5% | +2.2% | +9.2% | +16.2% |
| label_free s2 | BJ_T2_snug | -1.4% | -3.1% | -2.6% | -2.5% | +2.1% | +10.3% | +17.9% |
| supervised_64 s0 | BJ_T1_preloaded | -4.6% | +5.9% | +8.5% | -3.8% | -6.0% | -3.7% | +1.6% |
| supervised_64 s0 | BJ_T1_snug | +51.8% | +42.8% | +19.2% | -3.0% | -2.3% | -7.5% | -3.7% |
| supervised_64 s0 | BJ_T2_preloaded | -43.0% | -31.3% | -18.5% | -0.2% | -5.7% | -0.5% | +14.9% |
| supervised_64 s0 | BJ_T2_snug | +15.6% | +10.1% | -2.8% | -5.6% | -8.5% | -1.2% | +14.9% |
| supervised_64 s1 | BJ_T1_preloaded | +13.2% | +19.9% | +11.5% | -0.8% | -2.7% | +3.8% | -1.7% |
| supervised_64 s1 | BJ_T1_snug | +49.5% | +41.5% | +20.7% | -0.1% | +2.3% | +2.0% | -0.5% |
| supervised_64 s1 | BJ_T2_preloaded | -20.7% | -7.8% | -9.5% | -3.4% | -2.0% | +8.1% | +28.7% |
| supervised_64 s1 | BJ_T2_snug | +25.7% | +16.7% | +1.2% | -6.9% | +8.8% | +14.7% | +24.5% |
| supervised_64 s2 | BJ_T1_preloaded | +8.4% | +18.1% | +11.4% | -1.4% | -3.0% | -0.1% | +0.0% |
| supervised_64 s2 | BJ_T1_snug | +39.6% | +31.4% | +17.7% | -1.8% | -1.5% | -2.1% | -2.5% |
| supervised_64 s2 | BJ_T2_preloaded | -18.0% | -8.4% | -7.7% | -1.0% | -5.6% | -6.7% | +7.4% |
| supervised_64 s2 | BJ_T2_snug | +17.3% | +8.4% | -3.3% | -6.3% | +1.2% | -4.2% | +8.3% |

**The tested members overall** (medians over each member's seven levels, and over all 28 tested pairs of the run)

| Run | Member | Distance | Signed distance | Force at the same D, signed error | Bound | Within bound | End displacement e error | Stress reading error | Energy gap | Contact overlap | Plastic overlap | Bolt force error | Displacement error | Infinite distances |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| label_free s0 | BJ_T1_preloaded | 39,310% | +39,310% | +33.9% | 59.7% | 7 of 7 | -99.7% | -100.4% | 24.05% | 0.157 | 0.000 | -18.59% | 99.6% | 2 |
| label_free s0 | BJ_T1_snug | 35,224% | +35,224% | +33.9% | 64.0% | 7 of 7 | -99.7% | -100.4% | 29.44% | 0.157 | 0.000 | -100.40% | 99.6% | 0 |
| label_free s0 | BJ_T2_preloaded | 12,880% | +12,880% | +18.1% | 43.6% | 7 of 7 | -99.5% | -100.6% | 12.33% | 0.083 | 0.000 | -18.50% | 99.2% | 1 |
| label_free s0 | BJ_T2_snug | 21,745% | +21,745% | +19.1% | 46.4% | 7 of 7 | -99.5% | -100.5% | 17.79% | 0.042 | 0.000 | -100.32% | 99.3% | 0 |
| label_free s0 | all four | 26,670% | +26,670% | +30.8% | 59.9% | 28 of 28 | -99.7% | -100.5% | 26.12% | 0.045 | 0.000 | -63.19% | 99.5% | 3 |
| label_free s1 | BJ_T1_preloaded | 6.0% | +6.0% | +3.1% | 15.5% | 7 of 7 | -5.1% | -0.8% | 1.15% | 0.947 | 0.600 | -0.39% | 8.9% | 0 |
| label_free s1 | BJ_T1_snug | 12.0% | +12.0% | +2.5% | 17.7% | 7 of 7 | -6.3% | -1.8% | 2.30% | 0.897 | 0.681 | +0.00% | 12.4% | 0 |
| label_free s1 | BJ_T2_preloaded | 9.9% | +0.2% | +0.2% | 11.2% | 7 of 7 | -0.9% | +3.1% | 0.78% | 1.000 | 0.807 | +1.71% | 23.4% | 0 |
| label_free s1 | BJ_T2_snug | 11.1% | +11.1% | +3.2% | 16.0% | 7 of 7 | -8.7% | -0.6% | 2.17% | 0.733 | 0.819 | +0.00% | 34.0% | 0 |
| label_free s1 | all four | 8.5% | +7.4% | +2.8% | 15.7% | 28 of 28 | -6.4% | -0.7% | 1.44% | 0.931 | 0.792 | +0.00% | 12.7% | 0 |
| label_free s2 | BJ_T1_preloaded | 3.1% | +3.1% | +1.3% | 8.7% | 7 of 7 | -3.0% | -4.7% | 0.51% | 1.000 | 0.755 | +0.05% | 4.8% | 0 |
| label_free s2 | BJ_T1_snug | 2.4% | +2.4% | +0.8% | 8.4% | 7 of 7 | -1.9% | -1.3% | 0.50% | 0.949 | 0.738 | +0.61% | 3.0% | 0 |
| label_free s2 | BJ_T2_preloaded | 0.7% | -0.1% | -0.0% | 5.6% | 7 of 7 | +0.1% | +1.6% | 0.19% | 1.000 | 0.849 | +0.43% | 1.7% | 0 |
| label_free s2 | BJ_T2_snug | 2.6% | -1.4% | -0.2% | 5.6% | 7 of 7 | +1.2% | +2.4% | 0.26% | 1.000 | 0.853 | +1.74% | 2.8% | 0 |
| label_free s2 | all four | 2.6% | +2.2% | +0.8% | 7.7% | 28 of 28 | -2.1% | +0.8% | 0.38% | 1.000 | 0.835 | +0.45% | 3.1% | 0 |
| supervised_64 s0 | BJ_T1_preloaded | 4.6% | -3.7% | -0.8% | 136.9% | 7 of 7 | +2.8% | +23.3% | 126.41% | 0.340 | 0.193 | +0.11% | 8.3% | 0 |
| supervised_64 s0 | BJ_T1_snug | 7.5% | -2.3% | -1.9% | 179.9% | 7 of 7 | +1.9% | -35.5% | 252.80% | 0.000 | 0.158 | -5.82% | 7.0% | 0 |
| supervised_64 s0 | BJ_T2_preloaded | 14.9% | -5.7% | -3.0% | 131.5% | 7 of 7 | +11.5% | +237.5% | 81.56% | 0.407 | 0.220 | -0.23% | 23.4% | 0 |
| supervised_64 s0 | BJ_T2_snug | 8.5% | -1.2% | -0.4% | 97.3% | 7 of 7 | +0.9% | +37.8% | 79.75% | 0.000 | 0.222 | -66.28% | 21.6% | 0 |
| supervised_64 s0 | all four | 6.0% | -2.6% | -0.9% | 175.6% | 28 of 28 | +2.2% | +30.5% | 217.68% | 0.186 | 0.207 | -1.08% | 11.7% | 0 |
| supervised_64 s1 | BJ_T1_preloaded | 3.8% | +3.8% | +1.9% | 145.7% | 7 of 7 | -2.8% | +15.3% | 143.25% | 0.000 | 0.247 | +0.20% | 8.4% | 0 |
| supervised_64 s1 | BJ_T1_snug | 2.3% | +2.3% | +2.1% | 127.4% | 7 of 7 | -3.3% | -18.7% | 116.53% | 0.000 | 0.253 | -4.43% | 7.4% | 0 |
| supervised_64 s1 | BJ_T2_preloaded | 8.1% | -3.4% | -1.4% | 97.7% | 7 of 7 | +9.1% | +88.6% | 74.65% | 0.318 | 0.530 | -0.23% | 17.3% | 0 |
| supervised_64 s1 | BJ_T2_snug | 14.7% | +14.7% | +3.1% | 101.0% | 7 of 7 | -12.4% | +70.3% | 84.41% | 0.244 | 0.219 | -12.78% | 13.7% | 0 |
| supervised_64 s1 | all four | 8.5% | +3.1% | +2.0% | 114.2% | 28 of 28 | -3.1% | +42.5% | 100.47% | 0.012 | 0.256 | -0.58% | 13.0% | 0 |
| supervised_64 s2 | BJ_T1_preloaded | 3.0% | +0.0% | +0.0% | 111.6% | 7 of 7 | -0.0% | -11.5% | 83.98% | 0.493 | 0.269 | +0.04% | 8.1% | 0 |
| supervised_64 s2 | BJ_T1_snug | 2.5% | -1.5% | -1.1% | 181.3% | 7 of 7 | +1.3% | -25.5% | 236.27% | 0.000 | 0.159 | -4.81% | 9.3% | 0 |
| supervised_64 s2 | BJ_T2_preloaded | 7.4% | -6.7% | -1.1% | 69.5% | 7 of 7 | +9.5% | +74.1% | 38.11% | 0.000 | 0.513 | +0.00% | 17.0% | 0 |
| supervised_64 s2 | BJ_T2_snug | 6.3% | +1.2% | +1.1% | 87.1% | 7 of 7 | -2.3% | +8.4% | 62.76% | 0.000 | 0.174 | -6.40% | 19.8% | 0 |
| supervised_64 s2 | all four | 6.5% | -1.2% | -0.6% | 140.9% | 28 of 28 | +1.4% | -1.9% | 155.35% | 0.000 | 0.239 | -0.59% | 12.8% | 0 |

**Every reading of the tested members, by level**

| Run | Member | D (mm) | Signed distance | Force at the same D, signed error | Bound | Within bound | End displacement e error | Stress reading error | Energy gap | Contact overlap | Plastic overlap | Bolt force error | Displacement error | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| label_free s0 | BJ_T1_preloaded | 0.5 | infinite | +16.9% | 53.2% | yes | -99.4% | -100.4% | 13.43% | 0.285 | 1.000 | +8.38% | 99.0% | the reference force at the predicted end displacement is not positive |
| label_free s0 | BJ_T1_preloaded | 1 | infinite | +18.8% | 48.9% | yes | -99.5% | -100.4% | 16.58% | 0.306 | 1.000 | +3.47% | 99.2% | the reference force at the predicted end displacement is not positive |
| label_free s0 | BJ_T1_preloaded | 2 | +117,270% | +22.1% | 50.9% | yes | -99.6% | -100.4% | 19.86% | 0.277 | 0.000 | -18.20% | 99.3% |  |
| label_free s0 | BJ_T1_preloaded | 3 | +39,310% | +33.9% | 59.7% | yes | -99.7% | -100.4% | 24.05% | 0.157 | 0.000 | -18.59% | 99.6% |  |
| label_free s0 | BJ_T1_preloaded | 4 | +29,485% | +63.2% | 82.5% | yes | -99.8% | -100.5% | 33.54% | 0.045 | 0.000 | -19.06% | 99.8% |  |
| label_free s0 | BJ_T1_preloaded | 6 | +23,854% | +122.6% | 138.1% | yes | -99.9% | -100.7% | 61.45% | 0.045 | 0.000 | -23.94% | 99.8% |  |
| label_free s0 | BJ_T1_preloaded | 8 | +21,883% | +180.4% | 194.7% | yes | -99.9% | -100.9% | 91.72% | 0.045 | 0.000 | -26.08% | 99.9% |  |
| label_free s0 | BJ_T1_snug | 0.5 | +35,224% | +27.5% | 59.8% | yes | -99.6% | -100.4% | 28.04% | 0.161 | 1.000 | -100.39% | 99.5% |  |
| label_free s0 | BJ_T1_snug | 1 | +35,224% | +27.5% | 59.8% | yes | -99.6% | -100.4% | 28.04% | 0.161 | 1.000 | -100.39% | 99.5% |  |
| label_free s0 | BJ_T1_snug | 2 | +35,224% | +27.7% | 60.0% | yes | -99.6% | -100.4% | 28.08% | 0.161 | 0.000 | -100.39% | 99.5% |  |
| label_free s0 | BJ_T1_snug | 3 | +35,224% | +33.9% | 64.0% | yes | -99.7% | -100.4% | 29.44% | 0.157 | 0.000 | -100.40% | 99.6% |  |
| label_free s0 | BJ_T1_snug | 4 | +35,224% | +63.7% | 85.4% | yes | -99.8% | -100.5% | 37.13% | 0.045 | 0.000 | -100.53% | 99.8% |  |
| label_free s0 | BJ_T1_snug | 6 | +35,224% | +123.0% | 139.7% | yes | -99.9% | -100.7% | 64.13% | 0.045 | 0.000 | -100.75% | 99.8% |  |
| label_free s0 | BJ_T1_snug | 8 | +35,224% | +180.4% | 195.7% | yes | -99.9% | -100.9% | 94.02% | 0.045 | 0.000 | -100.97% | 99.9% |  |
| label_free s0 | BJ_T2_preloaded | 0.5 | infinite | +8.9% | 43.6% | yes | -98.9% | -100.6% | 8.89% | 0.352 | 1.000 | +8.52% | 97.7% | the reference force at the predicted end displacement is not positive |
| label_free s0 | BJ_T2_preloaded | 1 | +33,674% | +9.8% | 35.9% | yes | -99.1% | -100.5% | 9.39% | 0.352 | 1.000 | +6.20% | 98.2% |  |
| label_free s0 | BJ_T2_preloaded | 2 | +15,103% | +11.7% | 35.8% | yes | -99.2% | -100.5% | 10.66% | 0.250 | 0.000 | -7.62% | 98.6% |  |
| label_free s0 | BJ_T2_preloaded | 3 | +12,880% | +18.1% | 39.7% | yes | -99.5% | -100.5% | 12.33% | 0.083 | 0.000 | -18.50% | 99.2% |  |
| label_free s0 | BJ_T2_preloaded | 4 | +12,019% | +49.2% | 62.2% | yes | -99.8% | -100.7% | 20.56% | 0.042 | 0.000 | -18.79% | 99.7% |  |
| label_free s0 | BJ_T2_preloaded | 6 | +11,269% | +121.6% | 128.4% | yes | -99.9% | -101.0% | 49.83% | 0.042 | 0.000 | -19.50% | 99.7% |  |
| label_free s0 | BJ_T2_preloaded | 8 | +10,966% | +185.5% | 192.8% | yes | -99.9% | -101.3% | 82.65% | 0.042 | 0.000 | -21.43% | 99.7% |  |
| label_free s0 | BJ_T2_snug | 0.5 | +21,745% | +17.0% | 45.0% | yes | -99.5% | -100.5% | 17.31% | 0.042 | 1.000 | -100.32% | 99.2% |  |
| label_free s0 | BJ_T2_snug | 1 | +21,745% | +17.0% | 45.0% | yes | -99.5% | -100.5% | 17.31% | 0.042 | 1.000 | -100.32% | 99.2% |  |
| label_free s0 | BJ_T2_snug | 2 | +21,745% | +17.1% | 45.1% | yes | -99.5% | -100.5% | 17.33% | 0.042 | 0.000 | -100.32% | 99.2% |  |
| label_free s0 | BJ_T2_snug | 3 | +21,745% | +19.1% | 46.4% | yes | -99.5% | -100.5% | 17.79% | 0.057 | 0.000 | -100.31% | 99.3% |  |
| label_free s0 | BJ_T2_snug | 4 | +21,745% | +49.2% | 66.0% | yes | -99.8% | -100.7% | 24.19% | 0.042 | 0.000 | -100.41% | 99.7% |  |
| label_free s0 | BJ_T2_snug | 6 | +21,745% | +121.8% | 130.4% | yes | -99.9% | -101.0% | 52.56% | 0.042 | 0.000 | -100.61% | 99.7% |  |
| label_free s0 | BJ_T2_snug | 8 | +21,745% | +185.8% | 194.2% | yes | -99.9% | -101.3% | 85.14% | 0.042 | 0.000 | -100.79% | 99.7% |  |
| label_free s1 | BJ_T1_preloaded | 0.5 | +25.4% | +3.3% | 15.5% | yes | -19.3% | -13.4% | 1.15% | 0.812 | 1.000 | -3.55% | 22.0% |  |
| label_free s1 | BJ_T1_preloaded | 1 | +9.1% | +1.6% | 8.3% | yes | -8.3% | -5.6% | 0.48% | 0.880 | 1.000 | +0.92% | 8.9% |  |
| label_free s1 | BJ_T1_preloaded | 2 | +3.0% | +0.7% | 9.7% | yes | -3.0% | -4.6% | 0.73% | 0.821 | 0.230 | +0.30% | 3.0% |  |
| label_free s1 | BJ_T1_preloaded | 3 | +6.0% | +3.1% | 11.0% | yes | -9.2% | +0.9% | 0.82% | 0.947 | 0.665 | -0.00% | 11.1% |  |
| label_free s1 | BJ_T1_preloaded | 4 | +3.8% | +3.2% | 17.0% | yes | -5.1% | +12.1% | 1.43% | 1.000 | 0.600 | -0.39% | 7.6% |  |
| label_free s1 | BJ_T1_preloaded | 6 | -2.8% | -2.6% | 28.6% | yes | +2.1% | +15.1% | 2.63% | 1.000 | 0.486 | -1.39% | 3.2% |  |
| label_free s1 | BJ_T1_preloaded | 8 | +6.9% | +6.4% | 38.1% | yes | -3.6% | -0.8% | 3.50% | 1.000 | 0.565 | -1.33% | 13.0% |  |
| label_free s1 | BJ_T1_snug | 0.5 | +49.1% | +7.7% | 22.9% | yes | -27.8% | -4.4% | 4.10% | 0.629 | 1.000 | -72.48% | 34.7% |  |
| label_free s1 | BJ_T1_snug | 1 | +36.0% | +6.1% | 17.7% | yes | -22.0% | -4.0% | 2.47% | 0.765 | 1.000 | -51.92% | 27.1% |  |
| label_free s1 | BJ_T1_snug | 2 | +12.0% | +2.5% | 10.9% | yes | -9.0% | -1.8% | 0.93% | 0.897 | 0.493 | -3.40% | 10.3% |  |
| label_free s1 | BJ_T1_snug | 3 | -6.9% | -4.6% | 14.9% | yes | +13.5% | -5.7% | 1.60% | 0.289 | 0.681 | +0.01% | 19.6% |  |
| label_free s1 | BJ_T1_snug | 4 | -3.5% | -3.1% | 16.9% | yes | +4.8% | +4.1% | 1.46% | 1.000 | 0.828 | +0.60% | 6.1% |  |
| label_free s1 | BJ_T1_snug | 6 | +0.2% | +0.2% | 26.5% | yes | -0.1% | +16.6% | 2.30% | 1.000 | 0.496 | +0.93% | 3.4% |  |
| label_free s1 | BJ_T1_snug | 8 | +12.2% | +11.4% | 40.5% | yes | -6.3% | +0.7% | 4.03% | 1.000 | 0.574 | +0.00% | 12.4% |  |
| label_free s1 | BJ_T2_preloaded | 0.5 | -2.9% | -0.3% | 11.2% | yes | +3.1% | +7.8% | 0.58% | 0.830 | 1.000 | -2.19% | 3.6% |  |
| label_free s1 | BJ_T2_preloaded | 1 | -6.2% | -0.7% | 6.4% | yes | +7.1% | +4.0% | 0.30% | 0.914 | 1.000 | +1.71% | 10.1% |  |
| label_free s1 | BJ_T2_preloaded | 2 | -11.9% | -1.8% | 9.7% | yes | +15.4% | +4.0% | 0.78% | 0.636 | 0.326 | +13.19% | 23.4% |  |
| label_free s1 | BJ_T2_preloaded | 3 | +0.2% | +0.2% | 7.1% | yes | -0.9% | +3.1% | 0.39% | 1.000 | 0.471 | -0.00% | 5.0% |  |
| label_free s1 | BJ_T2_preloaded | 4 | +10.8% | +9.9% | 15.0% | yes | -20.1% | -1.2% | 1.19% | 1.000 | 0.877 | -0.22% | 23.5% |  |
| label_free s1 | BJ_T2_preloaded | 6 | +9.9% | +9.4% | 27.9% | yes | -7.8% | -10.3% | 2.35% | 1.000 | 0.807 | +3.74% | 52.2% |  |
| label_free s1 | BJ_T2_preloaded | 8 | +18.1% | +17.1% | 44.0% | yes | -9.2% | -5.6% | 4.31% | 1.000 | 0.803 | +5.38% | 50.0% |  |
| label_free s1 | BJ_T2_snug | 0.5 | +39.5% | +4.3% | 20.4% | yes | -25.2% | +6.1% | 3.56% | 0.200 | 1.000 | -80.12% | 39.0% |  |
| label_free s1 | BJ_T2_snug | 1 | +27.1% | +3.2% | 16.0% | yes | -18.8% | +5.2% | 2.17% | 0.289 | 1.000 | -62.07% | 29.7% |  |
| label_free s1 | BJ_T2_snug | 2 | +7.9% | +1.1% | 8.4% | yes | -6.4% | +1.3% | 0.61% | 0.500 | 0.442 | -23.23% | 10.2% |  |
| label_free s1 | BJ_T2_snug | 3 | -7.7% | -5.0% | 10.7% | yes | +26.3% | -0.6% | 0.94% | 0.733 | 0.492 | +1.75% | 34.0% |  |
| label_free s1 | BJ_T2_snug | 4 | -0.1% | -0.1% | 12.0% | yes | +0.1% | -4.9% | 0.80% | 1.000 | 0.890 | +0.00% | 3.3% |  |
| label_free s1 | BJ_T2_snug | 6 | +11.1% | +10.6% | 30.4% | yes | -8.7% | -15.4% | 2.85% | 1.000 | 0.819 | +4.92% | 63.8% |  |
| label_free s1 | BJ_T2_snug | 8 | +22.2% | +20.9% | 48.7% | yes | -11.2% | -4.9% | 5.35% | 1.000 | 0.781 | +6.43% | 57.8% |  |
| label_free s2 | BJ_T1_preloaded | 0.5 | +8.6% | +1.3% | 6.5% | yes | -7.4% | -7.2% | 0.20% | 0.920 | 1.000 | -0.19% | 7.4% |  |
| label_free s2 | BJ_T1_preloaded | 1 | +5.0% | +0.9% | 5.4% | yes | -4.7% | -4.9% | 0.20% | 0.857 | 1.000 | -0.13% | 4.4% |  |
| label_free s2 | BJ_T1_preloaded | 2 | +3.1% | +0.7% | 5.8% | yes | -3.0% | -5.1% | 0.25% | 0.942 | 0.755 | +0.30% | 2.3% |  |
| label_free s2 | BJ_T1_preloaded | 3 | +3.0% | +1.6% | 8.7% | yes | -4.8% | -4.7% | 0.51% | 1.000 | 0.728 | -0.00% | 4.8% |  |
| label_free s2 | BJ_T1_preloaded | 4 | +0.4% | +0.3% | 11.8% | yes | -0.5% | -1.0% | 0.69% | 1.000 | 0.874 | +0.80% | 2.9% |  |
| label_free s2 | BJ_T1_preloaded | 6 | +1.5% | +1.3% | 19.4% | yes | -1.1% | +9.1% | 1.22% | 1.000 | 0.594 | +2.54% | 4.8% |  |
| label_free s2 | BJ_T1_preloaded | 8 | +4.5% | +4.2% | 28.3% | yes | -2.3% | +9.4% | 1.94% | 1.000 | 0.600 | +0.05% | 6.1% |  |
| label_free s2 | BJ_T1_snug | 0.5 | +3.7% | +0.8% | 7.1% | yes | -2.8% | -1.3% | 0.39% | 0.949 | 1.000 | +2.07% | 3.0% |  |
| label_free s2 | BJ_T1_snug | 1 | +3.5% | +0.7% | 6.7% | yes | -2.7% | -1.7% | 0.35% | 0.949 | 1.000 | +0.61% | 2.7% |  |
| label_free s2 | BJ_T1_snug | 2 | +2.0% | +0.4% | 6.7% | yes | -1.6% | -3.6% | 0.35% | 0.949 | 0.675 | +5.01% | 1.2% |  |
| label_free s2 | BJ_T1_snug | 3 | +0.9% | +0.5% | 8.4% | yes | -1.5% | -5.8% | 0.50% | 0.868 | 0.738 | +0.00% | 1.5% |  |
| label_free s2 | BJ_T1_snug | 4 | +1.3% | +1.2% | 11.5% | yes | -1.9% | -0.2% | 0.67% | 1.000 | 0.859 | +0.46% | 3.1% |  |
| label_free s2 | BJ_T1_snug | 6 | +2.4% | +2.2% | 18.9% | yes | -1.8% | +9.7% | 1.17% | 1.000 | 0.553 | +2.76% | 4.7% |  |
| label_free s2 | BJ_T1_snug | 8 | +5.0% | +4.7% | 28.5% | yes | -2.6% | +10.5% | 1.99% | 1.000 | 0.593 | +0.05% | 6.2% |  |
| label_free s2 | BJ_T2_preloaded | 0.5 | -0.1% | -0.0% | 5.6% | yes | +0.1% | +1.4% | 0.14% | 0.939 | 1.000 | +0.79% | 1.7% |  |
| label_free s2 | BJ_T2_preloaded | 1 | -0.7% | -0.1% | 3.9% | yes | +0.7% | +2.0% | 0.11% | 1.000 | 1.000 | +0.43% | 1.1% |  |
| label_free s2 | BJ_T2_preloaded | 2 | -0.7% | -0.1% | 3.7% | yes | +0.8% | +2.5% | 0.11% | 0.985 | 0.818 | +0.07% | 1.4% |  |
| label_free s2 | BJ_T2_preloaded | 3 | -0.5% | -0.4% | 4.9% | yes | +2.1% | +3.3% | 0.19% | 1.000 | 0.524 | +0.00% | 1.1% |  |
| label_free s2 | BJ_T2_preloaded | 4 | +2.2% | +2.2% | 8.3% | yes | -4.5% | +1.6% | 0.36% | 1.000 | 0.926 | +0.18% | 3.4% |  |
| label_free s2 | BJ_T2_preloaded | 6 | +9.2% | +8.8% | 27.4% | yes | -7.2% | -7.2% | 2.27% | 1.000 | 0.849 | +4.99% | 67.7% |  |
| label_free s2 | BJ_T2_preloaded | 8 | +16.2% | +15.3% | 43.8% | yes | -8.2% | -2.2% | 4.28% | 1.000 | 0.820 | +5.97% | 70.1% |  |
| label_free s2 | BJ_T2_snug | 0.5 | -1.4% | -0.2% | 4.8% | yes | +1.2% | +3.8% | 0.19% | 0.688 | 1.000 | -1.75% | 0.6% |  |
| label_free s2 | BJ_T2_snug | 1 | -3.1% | -0.5% | 4.5% | yes | +2.7% | +3.8% | 0.17% | 1.000 | 1.000 | +1.91% | 2.3% |  |
| label_free s2 | BJ_T2_snug | 2 | -2.6% | -0.4% | 4.4% | yes | +2.4% | +4.7% | 0.17% | 0.786 | 0.752 | -0.50% | 1.5% |  |
| label_free s2 | BJ_T2_snug | 3 | -2.5% | -1.0% | 5.6% | yes | +5.1% | +2.4% | 0.26% | 0.733 | 0.515 | +1.74% | 5.2% |  |
| label_free s2 | BJ_T2_snug | 4 | +2.1% | +2.0% | 8.4% | yes | -4.1% | +0.3% | 0.39% | 1.000 | 0.915 | +0.00% | 2.8% |  |
| label_free s2 | BJ_T2_snug | 6 | +10.3% | +9.9% | 27.0% | yes | -8.1% | -1.1% | 2.25% | 1.000 | 0.853 | +4.81% | 62.8% |  |
| label_free s2 | BJ_T2_snug | 8 | +17.9% | +16.9% | 44.3% | yes | -9.1% | +1.5% | 4.44% | 1.000 | 0.822 | +6.53% | 67.2% |  |
| supervised_64 s0 | BJ_T1_preloaded | 0.5 | -4.6% | -0.8% | 135.3% | yes | +4.5% | +46.6% | 87.04% | 0.340 | 0.000 | +15.49% | 10.6% |  |
| supervised_64 s0 | BJ_T1_preloaded | 1 | +5.9% | +1.1% | 81.6% | yes | -5.6% | +23.3% | 46.25% | 0.647 | 0.000 | +18.54% | 8.3% |  |
| supervised_64 s0 | BJ_T1_preloaded | 2 | +8.5% | +1.8% | 98.6% | yes | -7.9% | +38.2% | 74.35% | 0.821 | 0.016 | +0.30% | 10.8% |  |
| supervised_64 s0 | BJ_T1_preloaded | 3 | -3.8% | -2.4% | 136.9% | yes | +7.0% | +12.5% | 126.41% | 0.579 | 0.193 | +0.00% | 10.5% |  |
| supervised_64 s0 | BJ_T1_preloaded | 4 | -6.0% | -5.2% | 198.6% | yes | +8.2% | +19.9% | 194.32% | 0.091 | 0.257 | +0.11% | 8.3% |  |
| supervised_64 s0 | BJ_T1_preloaded | 6 | -3.7% | -3.4% | 335.9% | yes | +2.8% | +41.1% | 363.74% | 0.000 | 0.361 | -1.33% | 4.5% |  |
| supervised_64 s0 | BJ_T1_preloaded | 8 | +1.6% | +1.5% | 610.8% | yes | -0.8% | +14.8% | 902.60% | 0.000 | 0.464 | -3.00% | 4.9% |  |
| supervised_64 s0 | BJ_T1_snug | 0.5 | +51.8% | +8.0% | 166.7% | yes | -28.9% | -89.1% | 217.76% | 0.846 | 0.000 | -39.04% | 15.2% |  |
| supervised_64 s0 | BJ_T1_snug | 1 | +42.8% | +6.9% | 177.3% | yes | -25.1% | -71.2% | 246.31% | 0.410 | 0.000 | -45.39% | 12.7% |  |
| supervised_64 s0 | BJ_T1_snug | 2 | +19.2% | +3.8% | 179.9% | yes | -13.6% | -35.5% | 252.80% | 0.000 | 0.034 | -31.98% | 7.0% |  |
| supervised_64 s0 | BJ_T1_snug | 3 | -3.0% | -1.9% | 174.0% | yes | +5.5% | +8.4% | 217.60% | 0.000 | 0.158 | -0.00% | 13.9% |  |
| supervised_64 s0 | BJ_T1_snug | 4 | -2.3% | -2.1% | 289.1% | yes | +3.3% | +10.3% | 425.60% | 0.000 | 0.262 | -0.02% | 5.4% |  |
| supervised_64 s0 | BJ_T1_snug | 6 | -7.5% | -6.9% | 586.3% | yes | +5.6% | +18.0% | 1,129% | 0.000 | 0.339 | -4.64% | 6.4% |  |
| supervised_64 s0 | BJ_T1_snug | 8 | -3.7% | -3.5% | 741.2% | yes | +1.9% | -49.9% | 1,349% | 0.000 | 0.440 | -5.82% | 4.6% |  |
| supervised_64 s0 | BJ_T2_preloaded | 0.5 | -43.0% | -6.7% | 131.5% | yes | +74.9% | +237.5% | 80.84% | 0.800 | 0.000 | +13.41% | 30.4% |  |
| supervised_64 s0 | BJ_T2_preloaded | 1 | -31.3% | -4.8% | 105.8% | yes | +48.8% | +170.0% | 81.56% | 0.939 | 0.000 | +12.06% | 23.4% |  |
| supervised_64 s0 | BJ_T2_preloaded | 2 | -18.5% | -3.0% | 78.0% | yes | +25.8% | +95.7% | 50.78% | 0.857 | 0.022 | -0.31% | 13.9% |  |
| supervised_64 s0 | BJ_T2_preloaded | 3 | -0.2% | -0.1% | 73.9% | yes | +0.7% | +62.0% | 42.66% | 0.407 | 0.220 | -0.00% | 21.4% |  |
| supervised_64 s0 | BJ_T2_preloaded | 4 | -5.7% | -5.7% | 269.8% | yes | +11.5% | +253.1% | 386.95% | 0.282 | 0.480 | -0.23% | 55.7% |  |
| supervised_64 s0 | BJ_T2_preloaded | 6 | -0.5% | -0.4% | 501.6% | yes | +0.4% | +780.5% | 760.01% | 0.000 | 0.571 | -0.83% | 29.4% |  |
| supervised_64 s0 | BJ_T2_preloaded | 8 | +14.9% | +14.1% | 650.1% | yes | -7.6% | +893.2% | 940.19% | 0.000 | 0.635 | -2.97% | 22.4% |  |
| supervised_64 s0 | BJ_T2_snug | 0.5 | +15.6% | +2.0% | 94.5% | yes | -11.7% | +22.8% | 76.28% | 0.500 | 0.000 | -68.52% | 21.6% |  |
| supervised_64 s0 | BJ_T2_snug | 1 | +10.1% | +1.4% | 95.1% | yes | -8.0% | -21.3% | 77.26% | 1.000 | 0.000 | -66.28% | 9.3% |  |
| supervised_64 s0 | BJ_T2_snug | 2 | -2.8% | -0.4% | 96.7% | yes | +2.5% | -11.2% | 79.75% | 0.000 | 0.011 | -66.56% | 9.7% |  |
| supervised_64 s0 | BJ_T2_snug | 3 | -5.6% | -3.3% | 97.3% | yes | +17.5% | +37.8% | 78.30% | 0.000 | 0.222 | -44.86% | 9.7% |  |
| supervised_64 s0 | BJ_T2_snug | 4 | -8.5% | -8.4% | 287.6% | yes | +17.1% | +315.6% | 459.72% | 1.000 | 0.551 | -71.20% | 54.6% |  |
| supervised_64 s0 | BJ_T2_snug | 6 | -1.2% | -1.1% | 488.5% | yes | +0.9% | +684.9% | 737.34% | 0.000 | 0.568 | -0.33% | 33.1% |  |
| supervised_64 s0 | BJ_T2_snug | 8 | +14.9% | +14.1% | 686.0% | yes | -7.6% | +744.1% | 1,063% | 0.000 | 0.627 | -2.47% | 24.3% |  |
| supervised_64 s1 | BJ_T1_preloaded | 0.5 | +13.2% | +1.9% | 81.4% | yes | -11.0% | +15.3% | 31.53% | 0.210 | 1.000 | +13.15% | 10.5% |  |
| supervised_64 s1 | BJ_T1_preloaded | 1 | +19.9% | +3.1% | 73.6% | yes | -16.4% | +8.0% | 37.62% | 0.024 | 0.000 | +18.62% | 12.6% |  |
| supervised_64 s1 | BJ_T1_preloaded | 2 | +11.5% | +2.3% | 84.3% | yes | -10.4% | +31.4% | 54.40% | 0.000 | 0.018 | +0.30% | 10.4% |  |
| supervised_64 s1 | BJ_T1_preloaded | 3 | -0.8% | -0.5% | 145.7% | yes | +1.3% | +7.4% | 143.25% | 0.237 | 0.171 | +0.00% | 8.4% |  |
| supervised_64 s1 | BJ_T1_preloaded | 4 | -2.7% | -2.3% | 222.9% | yes | +3.6% | +66.6% | 244.93% | 0.000 | 0.247 | +0.20% | 4.8% |  |
| supervised_64 s1 | BJ_T1_preloaded | 6 | +3.8% | +3.4% | 319.4% | yes | -2.8% | -61.1% | 328.82% | 0.000 | 0.368 | -0.16% | 4.4% |  |
| supervised_64 s1 | BJ_T1_preloaded | 8 | -1.7% | -1.6% | 519.8% | yes | +0.9% | +173.9% | 653.68% | 0.000 | 0.464 | -4.71% | 5.1% |  |
| supervised_64 s1 | BJ_T1_snug | 0.5 | +49.5% | +7.7% | 98.6% | yes | -27.9% | -2.1% | 76.25% | 0.581 | 1.000 | -37.33% | 19.4% |  |
| supervised_64 s1 | BJ_T1_snug | 1 | +41.5% | +6.8% | 94.3% | yes | -24.6% | -27.4% | 69.70% | 0.000 | 0.000 | -32.78% | 14.6% |  |
| supervised_64 s1 | BJ_T1_snug | 2 | +20.7% | +4.0% | 98.9% | yes | -14.4% | -18.7% | 76.39% | 0.000 | 0.029 | -10.68% | 7.4% |  |
| supervised_64 s1 | BJ_T1_snug | 3 | -0.1% | -0.0% | 127.4% | yes | +0.1% | -26.6% | 116.53% | 0.000 | 0.209 | +0.00% | 10.8% |  |
| supervised_64 s1 | BJ_T1_snug | 4 | +2.3% | +2.1% | 183.3% | yes | -3.3% | -42.5% | 171.16% | 0.000 | 0.253 | -0.01% | 3.8% |  |
| supervised_64 s1 | BJ_T1_snug | 6 | +2.0% | +1.9% | 394.6% | yes | -1.5% | +35.7% | 511.41% | 0.000 | 0.345 | -2.87% | 3.8% |  |
| supervised_64 s1 | BJ_T1_snug | 8 | -0.5% | -0.5% | 688.2% | yes | +0.2% | +175.2% | 1,163% | 0.000 | 0.413 | -4.43% | 4.3% |  |
| supervised_64 s1 | BJ_T2_preloaded | 0.5 | -20.7% | -2.3% | 77.6% | yes | +26.2% | +88.6% | 28.11% | 0.245 | 1.000 | +3.02% | 17.1% |  |
| supervised_64 s1 | BJ_T2_preloaded | 1 | -7.8% | -0.9% | 71.6% | yes | +9.1% | +73.5% | 37.38% | 0.237 | 0.000 | -1.54% | 17.3% |  |
| supervised_64 s1 | BJ_T2_preloaded | 2 | -9.5% | -1.4% | 78.8% | yes | +12.0% | +54.3% | 51.83% | 0.318 | 0.001 | +3.71% | 12.1% |  |
| supervised_64 s1 | BJ_T2_preloaded | 3 | -3.4% | -2.5% | 97.7% | yes | +13.6% | +33.7% | 74.65% | 1.000 | 0.260 | -0.00% | 25.7% |  |
| supervised_64 s1 | BJ_T2_preloaded | 4 | -2.0% | -2.0% | 300.3% | yes | +4.0% | +242.6% | 479.68% | 0.524 | 0.530 | -0.23% | 49.5% |  |
| supervised_64 s1 | BJ_T2_preloaded | 6 | +8.1% | +7.7% | 535.4% | yes | -6.4% | +579.8% | 865.75% | 1.000 | 0.558 | -0.85% | 28.2% |  |
| supervised_64 s1 | BJ_T2_preloaded | 8 | +28.7% | +26.9% | 844.6% | yes | -14.5% | +485.5% | 1,587% | 0.000 | 0.634 | -1.37% | 13.8% |  |
| supervised_64 s1 | BJ_T2_snug | 0.5 | +25.7% | +3.1% | 79.2% | yes | -18.0% | +49.3% | 53.53% | 0.244 | 0.000 | -71.93% | 22.8% |  |
| supervised_64 s1 | BJ_T2_snug | 1 | +16.7% | +2.1% | 77.0% | yes | -12.5% | +34.1% | 50.71% | 0.256 | 0.000 | -62.32% | 13.7% |  |
| supervised_64 s1 | BJ_T2_snug | 2 | +1.2% | +0.2% | 81.9% | yes | -1.1% | +22.7% | 57.27% | 0.000 | 0.015 | -44.67% | 8.7% |  |
| supervised_64 s1 | BJ_T2_snug | 3 | -6.9% | -4.3% | 101.0% | yes | +22.7% | +77.4% | 84.41% | 0.737 | 0.219 | -12.78% | 13.3% |  |
| supervised_64 s1 | BJ_T2_snug | 4 | +8.8% | +8.1% | 271.3% | yes | -16.5% | +70.3% | 409.31% | 0.364 | 0.516 | -0.03% | 36.9% |  |
| supervised_64 s1 | BJ_T2_snug | 6 | +14.7% | +14.1% | 781.9% | yes | -11.5% | +263.4% | 1,889% | 0.000 | 0.562 | -0.31% | 13.3% |  |
| supervised_64 s1 | BJ_T2_snug | 8 | +24.5% | +23.1% | 1,071% | yes | -12.4% | +473.3% | 2,590% | 0.000 | 0.634 | -1.28% | 23.0% |  |
| supervised_64 s2 | BJ_T1_preloaded | 0.5 | +8.4% | +1.2% | 91.2% | yes | -7.3% | -8.2% | 39.55% | 0.240 | 1.000 | +11.57% | 9.3% |  |
| supervised_64 s2 | BJ_T1_preloaded | 1 | +18.1% | +2.9% | 72.9% | yes | -15.2% | -10.5% | 36.88% | 0.518 | 0.000 | +12.31% | 13.7% |  |
| supervised_64 s2 | BJ_T1_preloaded | 2 | +11.4% | +2.3% | 79.8% | yes | -10.4% | -11.5% | 48.77% | 0.493 | 0.005 | +0.30% | 6.2% |  |
| supervised_64 s2 | BJ_T1_preloaded | 3 | -1.4% | -0.8% | 111.6% | yes | +2.4% | -23.8% | 83.98% | 0.632 | 0.200 | +0.00% | 11.2% |  |
| supervised_64 s2 | BJ_T1_preloaded | 4 | -3.0% | -2.6% | 139.8% | yes | +4.1% | -11.0% | 96.29% | 0.550 | 0.269 | +0.04% | 8.1% |  |
| supervised_64 s2 | BJ_T1_preloaded | 6 | -0.1% | -0.1% | 243.0% | yes | +0.1% | -16.8% | 190.32% | 0.000 | 0.354 | -0.86% | 3.3% |  |
| supervised_64 s2 | BJ_T1_preloaded | 8 | +0.0% | +0.0% | 464.6% | yes | -0.0% | -18.3% | 522.32% | 0.379 | 0.488 | -5.25% | 5.5% |  |
| supervised_64 s2 | BJ_T1_snug | 0.5 | +39.6% | +6.5% | 141.3% | yes | -23.7% | -25.5% | 156.55% | 0.000 | 0.000 | -34.26% | 20.0% |  |
| supervised_64 s2 | BJ_T1_snug | 1 | +31.4% | +5.4% | 142.9% | yes | -19.7% | -28.2% | 160.03% | 0.000 | 0.000 | -29.88% | 15.4% |  |
| supervised_64 s2 | BJ_T1_snug | 2 | +17.7% | +3.5% | 140.5% | yes | -12.6% | -38.2% | 154.14% | 0.000 | 0.023 | -15.87% | 9.3% |  |
| supervised_64 s2 | BJ_T1_snug | 3 | -1.8% | -1.1% | 181.3% | yes | +3.1% | -36.5% | 236.27% | 0.000 | 0.159 | +0.00% | 14.9% |  |
| supervised_64 s2 | BJ_T1_snug | 4 | -1.5% | -1.3% | 253.0% | yes | +2.1% | +12.4% | 326.09% | 0.000 | 0.260 | -0.01% | 7.9% |  |
| supervised_64 s2 | BJ_T1_snug | 6 | -2.1% | -1.9% | 439.0% | yes | +1.6% | +23.2% | 632.84% | 0.000 | 0.369 | -1.72% | 5.8% |  |
| supervised_64 s2 | BJ_T1_snug | 8 | -2.5% | -2.3% | 780.7% | yes | +1.3% | +43.9% | 1,496% | 0.364 | 0.449 | -4.81% | 5.0% |  |
| supervised_64 s2 | BJ_T2_preloaded | 0.5 | -18.0% | -2.0% | 59.8% | yes | +22.0% | +74.1% | 16.71% | 0.645 | 1.000 | +5.75% | 17.0% |  |
| supervised_64 s2 | BJ_T2_preloaded | 1 | -8.4% | -1.0% | 62.1% | yes | +9.8% | +39.6% | 28.10% | 0.828 | 0.000 | +5.56% | 12.0% |  |
| supervised_64 s2 | BJ_T2_preloaded | 2 | -7.7% | -1.1% | 67.6% | yes | +9.5% | +0.5% | 38.11% | 0.424 | 0.001 | +8.68% | 15.8% |  |
| supervised_64 s2 | BJ_T2_preloaded | 3 | -1.0% | -0.7% | 69.5% | yes | +3.8% | +28.6% | 37.77% | 0.000 | 0.217 | +0.00% | 8.9% |  |
| supervised_64 s2 | BJ_T2_preloaded | 4 | -5.6% | -5.6% | 220.5% | yes | +11.4% | +286.2% | 258.59% | 0.000 | 0.513 | -0.23% | 55.2% |  |
| supervised_64 s2 | BJ_T2_preloaded | 6 | -6.7% | -6.5% | 479.7% | yes | +5.3% | +523.4% | 694.97% | 0.000 | 0.548 | -0.85% | 30.4% |  |
| supervised_64 s2 | BJ_T2_preloaded | 8 | +7.4% | +7.0% | 687.0% | yes | -3.8% | +803.0% | 1,050% | 0.000 | 0.571 | -2.98% | 28.2% |  |
| supervised_64 s2 | BJ_T2_snug | 0.5 | +17.3% | +2.2% | 67.8% | yes | -12.9% | +8.4% | 39.31% | 0.917 | 0.000 | -69.13% | 19.8% |  |
| supervised_64 s2 | BJ_T2_snug | 1 | +8.4% | +1.1% | 76.6% | yes | -6.7% | -4.4% | 50.19% | 0.000 | 0.000 | -63.20% | 11.8% |  |
| supervised_64 s2 | BJ_T2_snug | 2 | -3.3% | -0.5% | 74.4% | yes | +3.0% | -22.3% | 47.27% | 0.000 | 0.000 | -42.19% | 8.0% |  |
| supervised_64 s2 | BJ_T2_snug | 3 | -6.3% | -3.8% | 87.1% | yes | +20.0% | -10.5% | 62.76% | 0.000 | 0.174 | -6.40% | 18.3% |  |
| supervised_64 s2 | BJ_T2_snug | 4 | +1.2% | +1.2% | 228.6% | yes | -2.3% | +129.9% | 290.53% | 0.000 | 0.514 | -0.03% | 40.1% |  |
| supervised_64 s2 | BJ_T2_snug | 6 | -4.2% | -4.0% | 430.4% | yes | +3.3% | +630.5% | 572.45% | 0.000 | 0.546 | -0.33% | 31.4% |  |
| supervised_64 s2 | BJ_T2_snug | 8 | +8.3% | +7.8% | 685.5% | yes | -4.2% | +801.4% | 1,061% | 0.000 | 0.628 | -2.46% | 25.5% |  |

### Run record

- Bench: 0.1669 s a step on average (median 0.1677, largest 0.1774) on 8 training members; 45 losses, all finite: True; peak memory 0.36 GiB and energies of the training set 3.27 GiB; predicted training time at most 16.0 h (345,600 steps).
- Labels: 132 of 132 needed, missing 0, levels as configured: True, every level converged: True, check ok: True. 132 members labelled by 24 worker processes, 32.9 s to 144.2 s a member; one ledger entry a member: True; solver: scipy.
- Worst optimality residuals over the labels, against their limits: max_complementarity 5.5e-12 (<= 1e-08); max_lambda_inactive 2.9e-11 (<= 1e-06); max_residual_unconstrained 3.9e-10 (<= 1e-06); min_gap 0 (>= -1e-12); min_lambda -8.3e-12 (>= -1e-08); the two force readings (spring and stresses) of every reference agree to 2.9e-13 (at most 1e-06).
- Training (`train_times.log`, host autodl-container-eb3344896e-709d725c): from 07 November 2026 16:16:03 to 08 November 2026 07:22:43 CST (UTC+8), 15.11 h.

| Run | Attempts | Started (CST) | Ended (CST) | Hours | Status | Steps | Seconds per epoch, median (range) | Seconds per step, median epoch | Peak memory (GiB) | Losses finite |
|---|---|---|---|---|---|---|---|---|---|---|
| label_free_s0 | 1 | 07 Nov 16:16:04 | 07 Nov 20:59:06 | 4.72 | finished | 102,400 | 83.86 (81.77 to 90.22) | 0.1638 | 3.56 | True |
| label_free_s1 | 1 | 07 Nov 20:59:07 | 08 Nov 01:51:05 | 4.87 | finished | 102,400 | 87.22 (78.18 to 88.92) | 0.1704 | 3.56 | True |
| label_free_s2 | 1 | 08 Nov 01:51:06 | 08 Nov 06:47:05 | 4.93 | finished | 102,400 | 88.34 (87.33 to 89.51) | 0.1725 | 3.57 | True |
| supervised_64_s0 | 1 | 08 Nov 06:47:07 | 08 Nov 06:58:59 | 0.20 | finished | 12,800 | 3.59 (2.44 to 3.77) | 0.0561 | 0.35 | True |
| supervised_64_s1 | 1 | 08 Nov 06:59:00 | 08 Nov 07:10:54 | 0.20 | finished | 12,800 | 3.58 (2.95 to 3.84) | 0.0559 | 0.35 | True |
| supervised_64_s2 | 1 | 08 Nov 07:10:55 | 08 Nov 07:22:42 | 0.20 | finished | 12,800 | 3.57 (2.38 to 3.75) | 0.0558 | 0.35 | True |

- Predictions: 68, 68, 68, 68, 68, 68 members in the six runs' preds.npz, all finite: True.
- Evaluation: `evaluate.log` written at 08 November 2026 16:27:45 CST (the archive's listing), 9.08 h after the end of training; its line: `{"verdict": "FAIL", "C1_value": 0.06611381238606373, "C2_value": 0.31159970927825037, "missing": [], "non_finite": []}`.
- The archive's `records/` folder last changed at 2026-11-08 16:29:14 CST (its listing).

### The author's recomputation (`audit/c2_recompute.py`, records in `records/c2/audit/`)

- Regeneration (`regenerate.json`; Python 3.13.17, numpy 2.4.6, scipy 1.18.1, zlib 1.3, BLAS threads 1): the manifest's configuration is the stamped one: True; every returned member is the configured draw: True; members shared by the training and held-out sets: 0. All 580 instances regenerated: file SHA-256 equal to the manifest's for 512 of 512 train, 64 of 64 eval, 4 of 4 tested; node and unknown counts equal for 512 of 512, 64 of 64, 4 of 4.
- Members (`members/`, environment in `environment.json`; Python 3.13.17, numpy 2.4.6, scipy 1.18.1, solver scipy, BLAS threads 1): 68 of 68, missing 0. The returned labels on the regenerated instances, at 476 levels: largest relative difference in energy 3.3e-16 and in force 0, in end displacement 0 mm; largest unconstrained residual 1.3e-10, smallest gap 0, smallest multiplier -8.3e-12.
- Every metric of the three label-free seeds on the 64 held-out and 4 tested members, recomputed with the stamped metric function against the returned values (largest absolute difference):

| Run | curve_err | F_err | e_err | F_sigma_err | gap | bound | iou_contact | iou_plastic | bolt_err | u_rel_l2 |
|---|---|---|---|---|---|---|---|---|---|---|
| label_free_s0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| label_free_s1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| label_free_s2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Pairs whose containment in the bound differs from the returned one: label_free_s0 0, label_free_s1 0, label_free_s2 0.

| Run | Median distance, recomputed | Returned | 90th percentile, recomputed | Returned | Infinite, recomputed | Returned |
|---|---|---|---|---|---|---|
| label_free_s0 | 170.1221844384233 | 170.1221844384233 | 5075.0578803668795 | 5075.0578803668795 | 44 | 44 |
| label_free_s1 | 0.06611381238606373 | 0.06611381238606373 | 0.31159970927825037 | 0.31159970927825037 | 0 | 0 |
| label_free_s2 | 0.02411537875011993 | 0.02411537875011993 | 0.18561450521959055 | 0.18561450521959055 | 0 | 0 |

Recomputed C1 0.06611381238606373 and C2 0.31159970927825037, FAIL; returned 0.06611381238606373 and 0.31159970927825037, FAIL.

- Re-solved 4 members from the regenerated instances (`resolve.json`; numpy 2.4.6, scipy 1.18.1, solver scipy, BLAS threads 1): eval_0000: bit for bit True, largest difference 0 of the largest unknown, 0 in energy, 0 in force, iterations equal to the ledger's True, converged True; eval_0026: bit for bit True, largest difference 0 of the largest unknown, 0 in energy, 0 in force, iterations equal to the ledger's True, converged True; eval_0063: bit for bit True, largest difference 0 of the largest unknown, 0 in energy, 0 in force, iterations equal to the ledger's True, converged True; tested_BJ_T1_preloaded: bit for bit True, largest difference 0 of the largest unknown, 0 in energy, 0 in force, iterations equal to the ledger's True, converged True.
