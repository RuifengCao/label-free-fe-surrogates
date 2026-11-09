# Why seed 0 of G-C2.1 did not train

Exploratory, after the verdict (`docs/G-C2.1_verdict.md`) and not pre-registered. Nothing here changes the verdict. 9 November 2026.

## Findings

1. **Seed 0 trained for seven epochs, then collapsed and stayed collapsed.** With the effect of each epoch's drawn displacements removed (section 3), seed 0's mean loss fell like those of seeds 1 and 2 through epoch 7, from 10.608 to 10.548, rose to 10.627 in epoch 8, and stayed at 10.625 for the rest of the run (standard deviation 0.005 over epochs 8 to 200). Seed 1 rose in epoch 14, stayed at the same level over epochs 15 to 18 (10.625), and came down again from epoch 19. Seed 2 never rose more than 0.034 above the median of the five epochs before. The level at which both stayed is the loss of the starting field, the field the networks give before their first step: on the same draws, the host's runs and the starting field differ by 0.0012 or less in the collapsed epochs checked (section 3).
2. **In a collapse, every node gets the same latent.** CPU replays of the first 3,072 steps of seeds 0 and 1 (six epochs, all inside the 5,120-step warm-up) collapsed once each: seed 1 between the probes at steps 1,856 and 1,920, seed 0 between those at steps 2,752 and 2,816. Between the two probes, the relative variance of the encoder's node latents fell from 0.84 to 0.0085 (seed 1) and from 0.90 to 0.0005 (seed 0), e/(D + δ) fell from 0.092 to 0.007 and from 0.106 to 0.005, and the spread of u_y over the free nodes at D = 8 mm fell by factors of 65 and 140. The decoder sees each node's latent beside the mean of all of them (`c2.model.field`), so equal latents give every node the same output. The verdict found seed 0's predictions uniform in space.
3. **Each collapse came with a burst in the encoder's gradient alone.** The global gradient norm exceeded the clipping limit of 1 at every step of both replays (median 36 and 33), and the decoder carried most of it (median 33 and 30, against 0.39 and 0.34 for the encoder), so the encoder's share of a clipped step was about 1%. Just before each collapse, the encoder's norm exceeded ten times its median over the previous 256 steps in 7 consecutive steps (seed 0, steps 2,776 to 2,782) and in 5 of 9 (seed 1, steps 1,900 to 1,908), by factors of 11 to 92, while the decoder's stayed at 0.5 to 1.7 times its own median. The encoder's share rose to between 8% and 65%. Four isolated bursts were not followed by a collapse; in each, the decoder's norm rose as well, to 2.7 to 5.2 times its median, and the encoder's share stayed between 2.5% and 5.7%.
4. **The replays show what this training can do, not when the host's runs did it.** A replay draws the same member and displacements at every step as the host's run, so a difference between their epoch means is a difference between their models. The replays agreed with the host to within 0.005 through epoch 5 (seed 0) and epoch 3 (seed 1), then parted: they collapsed in epochs 6 and 4, the host's runs in epochs 8 and 14. Both replays had begun to recover by step 3,072.
5. **The collapse accounts for seed 0, not for the FAIL.** As the verdict states, C1 turned on seed 0, while C2 fails even on the two seeds that trained (90th percentiles of 31.2% and 18.6%, against 10%).

## 1. What was run

- **Replays** (`diag_seed.py`). The stamped tree (`git archive prereg-c2`), the returned manifest (`records/c2/return/manifest.json`), and the instances regenerated with the stamped code, which equal the host's (580 of 580 by SHA-256, `records/c2/audit/regenerate.json`). The replay follows `c2.train.train` step by step: the same torch and numpy seeds, initialisation, member order, displacements, AdamW, clipping and schedule. Only the device differs: one CPU thread, float32 at matmul precision 'highest', torch 2.15.0 and numpy 2.5.3, where the host ran an RTX 5090 with torch 2.12.1.
  - Every step records the loss, the gradient norms of the encoder, decoder and head before clipping, the global norm and the learning rate.
  - Every 64 steps, a probe on the first training member (`train_0000`) at D = 0.5, 2 and 8 mm records: the relative variance of the encoder's node latents (the mean squared distance of a node's latent from the mean latent, over the mean squared latent; 0 when all nodes share one latent); e/(D + δ), the head output that `c2.model.field` multiplies by D + δ to give the end section's displacement e (0 at the start); the spread (standard deviation) of u_y over the free nodes; and the norms of the zero-initialised last layers.
  - Each replay ran 3,072 steps, at about 6.5 s a step with the two side by side. Each was resumed twice from its own checkpoint, at steps 1,088 and 2,112, with the networks, optimiser, schedule and both random generators restored.
- **Bursts and collapses** (`analyse_replays.py`). A burst is a step whose encoder gradient norm exceeds ten times its median over the previous 256 steps. A collapse is a probe at which the relative variance of the latents (mean over the three displacements) has fallen below a third of its value at the probe before.
- **The host's loss histories** (`analyse_host.py`). A step's loss is the mean of ln Π over its four fields, and Π grows with D, so an epoch's mean loss moves with the epoch's draws.
  - The draws depend on the seed alone (numpy's `default_rng`: a permutation of the 512 training members each epoch, then four D a step by `c2.train.sample_D`). Drawn again, they equal the replays' records at all 3,072 steps of both seeds: the members exactly, D to the four decimals recorded.
  - For each epoch, X is the mean of ln D over its 2,048 draws and Q the mean of (ln D)². Least squares over the 600 epoch means of the three seeds, with one level for each seed and block of five epochs, gives a loss of level + 1.664 X + 0.094 Q (standard errors 0.022 and 0.017): a slope of 1.78 in ln D at the mean draw. Fitted instead to the replays' 4,608 steps before their collapses, with one level for each member, the slope is 1.87 (1.698 X + 0.138 Q).
  - The adjusted epoch mean, L - 1.664 (X - X̄) - 0.094 (Q - Q̄) with the bars the means over all 600 epochs, is the epoch's mean at the average draw. It cuts the standard deviation of seed 0's epoch means over epochs 101 to 200 from 0.049 to 0.0055.
- **The starting field** (`start_field.py`). Built as `c2.train.train` builds them, the networks start with the last layers of the decoder and the head at zero, so their field is the starting field whatever the other weights are (checked). The mean of its loss by `c2.train.step_loss` over the host's draws of an epoch is what that epoch would have shown had the field stayed at the start.

## 2. The replays against the host

Mean loss over each epoch. Every step draws the same member and displacements in both.

| Epoch | Seed 0: replay | host | difference | Seed 1: replay | host | difference |
|---|---|---|---|---|---|---|
| 1 | 10.5417 | 10.5444 | -0.0027 | 10.6177 | 10.6145 | +0.0032 |
| 2 | 10.5981 | 10.5963 | +0.0018 | 10.5636 | 10.5686 | -0.0050 |
| 3 | 10.5309 | 10.5295 | +0.0014 | 10.6400 | 10.6399 | +0.0001 |
| 4 | 10.5965 | 10.6007 | -0.0041 | 10.5819 | 10.6027 | -0.0208 |
| 5 | 10.5759 | 10.5793 | -0.0034 | 10.5800 | 10.5660 | +0.0141 |
| 6 | 10.6582 | 10.6026 | +0.0555 | 10.4638 | 10.4627 | +0.0011 |

The replay of seed 0 collapsed in epoch 6 (steps 2,561 to 3,072), between steps 2,752 and 2,816, and its mean over that epoch lay 0.056 above the host's. The replay of seed 1 collapsed in epoch 4 (steps 1,537 to 2,048), between steps 1,856 and 1,920, and its mean over that epoch lay 0.021 below the host's. After epoch 5 of seed 0 and epoch 3 of seed 1, the replays cannot stand for the host's runs.

## 3. The host's loss histories, adjusted for the draws

Adjusted mean loss over each epoch (section 1).

| Epoch | Seed 0 | Seed 1 | Seed 2 |
|---|---|---|---|
| 1 | 10.608 | 10.612 | 10.602 |
| 2 | 10.580 | 10.579 | 10.580 |
| 3 | 10.560 | 10.566 | 10.569 |
| 4 | 10.560 | 10.603 | 10.557 |
| 5 | 10.560 | 10.560 | 10.595 |
| 6 | 10.556 | 10.554 | 10.593 |
| 7 | 10.548 | 10.558 | 10.576 |
| 8 | **10.627** | 10.564 | 10.561 |
| 9 | 10.623 | 10.556 | 10.597 |
| 10 | 10.625 | 10.554 | 10.570 |
| 11 | 10.633 | 10.555 | 10.548 |
| 12 | 10.626 | 10.539 | 10.549 |
| 13 | 10.625 | 10.548 | 10.547 |
| 14 | 10.633 | **10.726** | 10.545 |
| 15 | 10.629 | 10.629 | 10.554 |
| 16 | 10.632 | 10.626 | 10.542 |
| 17 | 10.624 | 10.624 | 10.531 |
| 18 | 10.629 | 10.621 | 10.537 |
| 19 | 10.619 | 10.614 | 10.519 |
| 20 | 10.625 | 10.587 | 10.530 |
| 21 | 10.631 | 10.574 | 10.522 |
| 22 | 10.618 | 10.580 | 10.508 |
| 23 | 10.624 | 10.574 | 10.513 |
| 24 | 10.617 | 10.578 | 10.525 |
| 21 to 50 | 10.624 | 10.555 | 10.492 |
| 51 to 100 | 10.626 | 10.461 | 10.438 |
| 101 to 150 | 10.624 | 10.406 | 10.395 |
| 151 to 200 | 10.625 | 10.375 | 10.367 |

- Seed 0 over epochs 8 to 200: mean 10.6248, standard deviation 0.0051, range 10.611 to 10.638. Seed 1 over epochs 15 to 18: mean 10.6251.
- Epochs more than 0.03 above the median of the five epochs before them (from epoch 4, of those there are): seed 0, epochs 8 to 10; seed 1, epochs 14 to 16; seed 2, epoch 47 (0.034). No others in 200 epochs.
- A collapse that recovers within an epoch raises that epoch's mean by less, so shorter events may not show here.

**The starting field.** Mean loss over an epoch of the host's run, and of the starting field on the same members and displacements (`start_field.py`, `compare_start.py`):

| Seed, epoch | Host | Starting field | Host minus starting field |
|---|---|---|---|
| 0, 1 | 10.5444 | 10.5650 | -0.0206 |
| 0, 8 | 10.6715 | 10.6727 | -0.0012 |
| 0, 200 | 10.7426 | 10.7435 | -0.0010 |
| 1, 16 | 10.6166 | 10.6164 | +0.0002 |

In epoch 1, seed 0 was already 0.021 below the starting field. In the collapsed epochs, seed 0's epochs 8 and 200 and seed 1's epoch 16, the host's runs and the starting field differ by 0.0012 or less. On the adjusted scale of the table above, the starting field lies at 10.623 to 10.629. The verdict found seed 0's predicted unknowns, in the median, 0.5% of the label's norm away from the starting field.

## 4. The collapses in the replays

| | Seed 0 | Seed 1 |
|---|---|---|
| Probes before and after | steps 2,752 and 2,816 | steps 1,856 and 1,920 |
| Bursts | steps 2,776 to 2,782 (7 of 7) | steps 1,900 to 1,908 (5 of 9) |
| Largest burst, against the median of the previous 256 steps | 21.3 against 0.340 (step 2,777) | 32.9 against 0.359 (step 1,904) |
| Learning rate | 5.4 × 10⁻⁴ | 3.7 × 10⁻⁴ |
| Relative variance of the latents | 0.9014 to 0.0005 | 0.8417 to 0.0085 |
| e/(D + δ) | 0.1061 to 0.0047 | 0.0917 to 0.0070 |
| Spread of u_y at D = 8 mm | 0.0274 to 0.00020 mm | 0.0168 to 0.00026 mm |
| At step 3,072: relative variance; e/(D + δ) | 0.122; 0.037 | 0.594; 0.086 |

Gradient norms before clipping at the burst steps:

| Step | Encoder | Decoder | Head | All | Encoder's share |
|---|---|---|---|---|---|
| Seed 0, 2,776 | 3.94 | 21.9 | 13.7 | 26.2 | 0.151 |
| 2,777 | 21.30 | 30.9 | 25.9 | 45.6 | 0.467 |
| 2,778 | 4.09 | 24.0 | 13.6 | 27.9 | 0.147 |
| 2,779 | 7.64 | 17.8 | 9.5 | 21.6 | 0.354 |
| 2,780 | 5.69 | 33.4 | 10.9 | 35.5 | 0.160 |
| 2,781 | 6.49 | 32.3 | 22.8 | 40.1 | 0.162 |
| 2,782 | 4.67 | 40.3 | 24.1 | 47.2 | 0.099 |
| Seed 1, 1,900 | 5.56 | 65.1 | 33.6 | 73.4 | 0.076 |
| 1,902 | 8.04 | 19.2 | 10.8 | 23.5 | 0.343 |
| 1,904 | 32.89 | 36.0 | 12.6 | 50.4 | 0.653 |
| 1,906 | 9.42 | 48.2 | 41.7 | 64.5 | 0.146 |
| 1,908 | 4.06 | 37.7 | 23.1 | 44.4 | 0.092 |
| Median over 3,072 steps, seed 0 | 0.393 | 33.1 | 11.4 | 36.4 | 0.011 |
| Median over 3,072 steps, seed 1 | 0.343 | 30.0 | 10.1 | 32.7 | 0.010 |

The isolated bursts were at steps 1,156, 2,211 and 3,012 of seed 1 and step 3,043 of seed 0, the last while seed 0 was recovering. The steps around each collapse are in `records/replays.log`, and every step in `records/seed0.jsonl` and `records/seed1.jsonl`.

## 5. Reading

**Shown.**
- Seed 0 did not fail to start. It trained for seven epochs, then fell back to the starting field's loss (to within 0.0012 in epochs 8 and 200) and stayed there for 193 epochs, with the uniform field that the verdict found. The verdict, reading means over 20 epochs, found its loss at its starting level throughout; that holds from epoch 8. The replays show one way into that state: every node gets nearly the same latent.
- Seed 0 is not alone. On the host, seed 1 rose in epoch 14, stayed at the same loss over epochs 15 to 18 and left it from epoch 19; it was back at its level before the collapse, about 10.55, by about epoch 40. Each replay collapsed once within six epochs, with the same signs (nearly one latent for all nodes, a uniform field), and had begun to recover by step 3,072.
- In the replays, each collapse fell between two probes that bracket a run of bursts in the encoder's gradient, during the warm-up. In those bursts the encoder's gradient rose and the decoder's did not.

**Not shown.**
- Why seed 0 stayed and seed 1 left. The host recorded nothing within an epoch.
- Whether the bursts cause the collapses or come with them, and what starts them. The probes are 64 steps apart.
- Whether the host's collapses began with bursts, or in which step of their epochs.

**An inference, not tested.** AdamW's step for a weight is its first moment over the root of its second, so the step answers to the gradient's size against that weight's own history, not to its absolute size. The encoder's share of a clipped step was about 1%, and its second moments were built on that. In the bursts before the collapses the share rose to between 8% and 65%. With AdamW's default β1 = 0.9 and β2 = 0.999, which `c2/train.py` keeps, a gradient far above a weight's history moves the weight by up to about three times the learning rate in one step, in the gradient's direction; several such steps in a row would move the whole encoder a long way in one direction. In the isolated bursts the decoder's gradient rose with the encoder's, the clipping scaled both down, and the encoder's share stayed below 6%.

## 6. For the next pre-specification

The verdict plans a surrogate gate on the CHS splices with the same training code. Points it could settle before the run:

- **Record what this note had to reconstruct.** The loss of every step, or each epoch's X and Q; the gradient norms of the three networks; and, every few hundred steps, the probe of section 1 on a fixed training member. With these, a verdict can tell a collapsed seed from a slow one, and when it collapsed. The probe costs one forward pass.
- **Test the training on development members before stamping.** Over several seeds, with the probe, whether a change removes the collapses without slowing the training. Candidates: clipping each network's gradient separately, at a limit near its usual size; a lower peak learning rate or a longer warm-up; β2 = 0.99, under which a burst moves a weight by at most about one learning rate a step; a normalisation of the encoder's output. By the inference in section 5, raising the global limit would remove the damping that the isolated bursts had, so it is not on the list. A replay step took about 6.5 s on this CPU and 0.17 s on the host, so these tests belong on the GPU.
- **Say how a collapsed seed counts.** G-C2.1 entered it in the medians with its errors, as a finished seed. With three seeds, one collapsed seed makes the median the worse of the other two; in G-C2.1 that decided C1. Whether a collapsed seed may be rerun, and how many seeds to run, have to be fixed before the run.
- **The collapse is one of G-C2.1's two failures.** The other, the tail at the largest levels in the members with low yield stress, failed C2 in the two seeds that trained.

## 7. Files

- `diag_seed.py`: the replay, run as `DIAG_THREADS=1 python -I diag_seed.py JOINT DATA records/seed0.jsonl 0 3072 64` and the same for seed 1. JOINT is the `joint/` folder of `git archive prereg-c2`; DATA holds `manifest.json` and `inst/`, the regenerated instances.
- `analyse_replays.py`, `analyse_host.py`, `start_field.py`, `compare_start.py`: sections 2 to 4, run in this folder as below, with RECORDS the folder `joint/records/c2/return`. Their printouts are the `.log` files in `records/`.
- `records/seed0.jsonl`, `records/seed1.jsonl`: one line per step, a probe every 64 steps, and a line where a replay was resumed. The checkpoints (82 MB each) were not kept.
- `records/replays.json`, `records/host_adjusted.json`, `records/start_field_s0.json`, `records/start_field_s1.json`, `records/start_field_compare.json`: the analyses' outputs.

```
python -I analyse_replays.py RECORDS records/replays.json records/seed0.jsonl records/seed1.jsonl
python -I analyse_host.py JOINT RECORDS records/host_adjusted.json records/seed0.jsonl records/seed1.jsonl
DIAG_THREADS=1 python -I start_field.py JOINT DATA records/start_field_s0.json 0 1,8,200
DIAG_THREADS=1 python -I start_field.py JOINT DATA records/start_field_s1.json 1 16
python -I compare_start.py RECORDS records/host_adjusted.json records/start_field_compare.json records/start_field_s0.json records/start_field_s1.json
```
