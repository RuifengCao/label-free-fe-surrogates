# Branching the collapses of G-C2.1's replays

Exploratory, after the verdict (`docs/G-C2.1_verdict.md`) and not pre-registered, like `RESULTS.md` in this folder. Nothing here changes the verdict. 9 November 2026.

## Findings

1. **Cutting the encoder's bursts prevents the collapse.** The states just before the two replays' collapses (seed 1 at step 1,856, seed 0 at step 2,752) were reproduced bit for bit and branched for 256 steps. Left unchanged, both collapsed exactly as in the replays. With the encoder's gradient scaled down, before clipping, to at most five times its median over the previous 256 steps, neither collapsed. The scaling acted at two steps in each seed: steps 1,900 and 1,905 of seed 1, and steps 2,776 and 2,778 of seed 0. In these two events, the updates of the burst steps cause the collapse.
2. **AdamW's β2 at 0.99, or half the learning rate, prevents it too, and then no burst occurs.** Each of the three changes kept both seeds' latents diverse for the 256 steps; the lowest relative variance of the latents was 0.81 to 0.89, against 0.0005 and 0.0059 unchanged.
3. **The collapse happens in the encoder's first block.** In seed 0, between steps 2,768 and 2,800, the mean square of the residual stream after the first of the eight blocks rose from 644 to 32,891, while its node variance fell from 393 to 110; the part shared by all nodes grew about 130-fold. Most of it came from that block's MLP, whose output went from a mean square of 464 to 25,094 with a node variance of 319 falling to 54. From there on the shared part dominates every node's vector, and the relative variance of the latents fell to 0.0006. Seed 1's collapse has the same signs on a smaller scale: a mean square of 224 rising to 771 within eight steps, and the MLP's node variance falling from 55 to 20. In both, the relative variance after the input layer and the gain of the encoder's final LayerNorm hardly changed.
4. **The branches that did not collapse had lower losses** than the unchanged ones on the same draws: by 0.060 to 0.135 on average over the 256 steps, and by 0.041 to 0.109 over the last 128.
5. **What this does not show.** Two events, 256 steps each. Whether a change prevents collapses over whole runs, in other seeds and later in training, and what it costs at the end of training, needs full runs with the probes, on a GPU. The host's own collapses (seed 0 in epoch 8, seed 1 in epoch 14) were not branched: the host kept no state from before them.

## 1. What was run

- **The states.** `diag_seed.py` replayed seed 1 to step 1,856 and seed 0 to step 2,752 again, the last probes before the collapses, each in segments under the sandbox's two-hour limit and resumed from its own checkpoints. Every step's loss, gradient norms and probe equal those of `records/seed0.jsonl` and `records/seed1.jsonl`, bit for bit.
- **The branches** (`branch.py`). From each state, 256 steps on the same members and displacements as the replay, in four variants:
  - `control`: nothing changed;
  - `enc_cap`: before clipping, the encoder's gradient is scaled down to at most five times the median of its norm over the previous 256 steps (0.67% and 0.92% of the replays' steps exceed five times, the bursts included; the bursts were 11 to 92 times);
  - `beta2`: AdamW's β2 is 0.99 from the branch on, instead of 0.999;
  - `lr_half`: the learning rate is halved from the branch on.
- **The probes**, every 16 steps on the first training member at D = 0.5, 2 and 8 mm, as in `RESULTS.md`, and in addition the relative variance after the input layer, after each block and after the final LayerNorm, and that LayerNorm's gain. Seed 0's branches also record the mean square and node variance of the residual stream at each stage, and of the first block's attention and MLP outputs; seed 1's control was run again over its first 96 steps with these, every 8 steps. A probe draws no random numbers: both of seed 1's control runs, probed at different intervals, are identical to the replay at every step.
- **Reading** (`analyse_branches.py`). A branch collapsed if a probe fell below a third of its first. A burst is a step whose encoder gradient norm exceeds ten times its median over the previous 256 steps, as in `RESULTS.md`.

## 2. The branches

| Seed, branch | Collapsed | Lowest relative variance of the latents (step) | Bursts | Steps capped (scale) | Loss minus control: all 256 steps; last 128 |
|---|---|---|---|---|---|
| 1, control | yes | 0.0059 (1,936) | 1,900, 1,902, 1,904, 1,906, 1,908 | | 0; 0 |
| 1, enc_cap | no | 0.8227 (1,904) | 1,900, 1,905 | 1,900 (0.321), 1,905 (0.106) | -0.0602; -0.0456 |
| 1, beta2 | no | 0.8389 (1,888) | none | | -0.0628; -0.0409 |
| 1, lr_half | no | 0.8119 (2,064) | none | | -0.0926; -0.0748 |
| 0, control | yes | 0.0005 (2,816) | 2,776 to 2,782 | | 0; 0 |
| 0, enc_cap | no | 0.8565 (2,784) | 2,776, 2,778 | 2,776 (0.429), 2,778 (0.053) | -0.0957; -0.0840 |
| 0, beta2 | no | 0.8876 (2,880) | none | | -0.0995; -0.0647 |
| 0, lr_half | no | 0.8667 (3,008) | none | | -0.1354; -0.1086 |

- Both controls equal the replays at every step and collapse where the replays did.
- In each `enc_cap` branch the first burst is the control's; capping it changes the trajectory, and the second burst, larger than any of the control's in seed 0 (95 times its median), is capped as well.
- Every step draws the same member and displacements in all four branches of a seed, so the loss differences compare models, not draws.

## 3. Inside the encoder

Seed 0, `control`, then `enc_cap`. "After block 1" is the residual stream after the first block; its mean square splits into the part shared by all nodes and the node variance. Probes at D = 0.5, 2 and 8 mm, averaged.

| Step | Input layer, relative variance | After block 1: mean square | node variance | MLP output of block 1: mean square | node variance | Latents, relative variance |
|---|---|---|---|---|---|---|
| 2,752 | 0.358 | 660 | 427 | 485 | 347 | 0.9014 |
| 2,768 | 0.357 | 644 | 393 | 464 | 319 | 0.8989 |
| 2,784 | 0.354 | 5,833 | 298 | 4,835 | 222 | 0.0224 |
| 2,800 | 0.344 | 32,891 | 110 | 25,094 | 54 | 0.0006 |
| 2,816 | 0.342 | 40,941 | 117 | 30,687 | 55 | 0.0005 |
| 3,008 | 0.361 | 26,381 | 5,203 | 20,721 | 3,835 | 0.1068 |
| 2,816, `enc_cap` | 0.351 | 760 | 420 | 575 | 349 | 0.8895 |
| 3,008, `enc_cap` | 0.350 | 1,019 | 548 | 789 | 467 | 0.8707 |

- The first block's attention output grew too, from a mean square of 26 to 1,706 by step 2,816, almost all of it shared by the nodes.
- In `beta2` and `lr_half` the mean square after the first block stayed between 638 and 866.
- The median |gain| of the final LayerNorm was 0.982 at step 2,752 and 0.978 at step 2,816.
- Seed 1, `control`, every 8 steps: after the first block, mean square 224 at step 1,904, 771 at 1,912 and 1,378 at 1,936; node variance 90, 40 and 51; MLP output mean square 114, 417 and 691 with node variance 55, 20 and 27; latents 0.77, 0.045 and 0.0059.
- Recovery, as far as the replay of seed 0 went, rebuilt variation between the nodes on top of the shared part: by step 3,008 the node variance after the first block was 5,203, but the mean square was still 26,381.

## 4. Reading

**Shown.**
- In both events, the encoder's updates at the burst steps cause the collapse: the same state and the same draws, with the encoder's gradient scaled down at two steps, do not collapse.
- Each of three changes, a cap on the encoder's gradient, β2 = 0.99 and half the learning rate, prevents both collapses for 256 steps. Under the last two the bursts do not occur, so the bursts depend on where the training is, not on particular members or displacements.
- The collapse is a blow-up of a part of the first block's output that every node shares, mostly from its MLP, which swamps what distinguishes the nodes.

**Not shown.**
- What makes the encoder's gradient burst while the latents are still diverse.
- Whether any of the changes prevents collapses over whole runs and in other seeds, and what each costs in the trained model.
- Whether the host's collapses were the same. The final model states of the host's runs, if Song sends them, can show whether seed 0's first block carries such a shared part after 200 epochs.

**Context, not tested here.** Loss spikes in transformer training under Adam are known in large language models, where they have been traced to Adam's update (Molybog et al., 2023, arXiv:2304.09871), and have been reproduced in small models at high learning rates (Wortsman et al., 2023, arXiv:2309.14322). Whether the collapses here are the same phenomenon was not examined.

## 5. For the next pre-specification

- **The probe of `RESULTS.md`, with the mean square after the first block, would show a collapse when it happens.** The mean square after the first block rose 9-fold within 16 steps in seed 0 and 3.4-fold within 8 steps in seed 1.
- **Each of the three changes is a candidate, and the branches cannot rank them.**
  - The cap acted at two steps in 256 and left the others unchanged; it adds two settings (five times, 256 steps).
  - β2 = 0.99 changes every step slightly.
  - Half the learning rate had the lowest loss over these 256 steps, inside the warm-up; its effect over 200 epochs is not known.
- **Ranking them needs whole runs**: on the T-stub family, several seeds each, with the probes, comparing how often each collapses and its loss and errors at the end. That is GPU work.

## 6. Files

- `branch.py`, `analyse_branches.py`.
- `records/branches/branch_s{0,1}_{control,enc_cap,beta2,lr_half}.jsonl`: the branches, one line a step, a probe every 16 steps. Seed 1's four branches ran before the probe recorded mean squares and the first block's outputs; the training steps are the same code (both controls equal the replay).
- `records/branches/branch_s1_control_fine.jsonl`: seed 1's control again, 96 steps, the full probe every 8 steps.
- `records/branches/seed{0,1}_branches.{json,log}`, `records/branches/seed1_control_fine.{json,log}`: the readings.
- The replays to the branch points and their checkpoints (82 MB each) were not kept; their records equal `records/seed{0,1}.jsonl` up to those steps.

Run in this folder, with JOINT and DATA as in `RESULTS.md`:

```
DIAG_THREADS=1 python -I diag_seed.py JOINT DATA s1.jsonl 1 1856 64
DIAG_THREADS=1 python -I branch.py JOINT DATA s1.ckpt.pt s1.jsonl records/branches/branch_s1_control.jsonl control 256 16
DIAG_THREADS=1 python -I branch.py JOINT DATA s1.ckpt.pt s1.jsonl records/branches/branch_s1_control_fine.jsonl control 96 8
python -I analyse_branches.py records/branches/seed1_branches.json records/seed1.jsonl records/branches/branch_s1_control.jsonl records/branches/branch_s1_enc_cap.jsonl records/branches/branch_s1_beta2.jsonl records/branches/branch_s1_lr_half.jsonl
```

and the same with `enc_cap`, `beta2` and `lr_half` in place of `control`, and for seed 0 with `0 2752` and `s0`.
