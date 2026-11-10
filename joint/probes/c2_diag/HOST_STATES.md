# The host's final models of G-C2.1's label-free runs

Exploratory, after the verdict (`docs/G-C2.1_verdict.md`) and not pre-registered, like `RESULTS.md` and `BRANCHES.md` in this folder. Nothing here changes the verdict. 10 November 2026.

The final states of the three label-free runs were sent from the host on 10 November 2026 as `c2_label_free_states.tgz` (SHA-256 `9942b9a637efee47c7307f7c41e18c43e8f73cc706fccc6d9c4d6bdb9751e983`), holding `label_free_s0/state.pt`, `label_free_s1/state.pt` and `label_free_s2/state.pt` (SHA-256 `9cb8c29e2dab8ca6fb9e994faaac2c9c0c163a4915cd90fee0c3171b12ecd79b`, `938ffb8c6be95100f2a61726f3bc3d87f353b6e7a96b1559e65b487e5a251f1a` and `b5efe01450b9a48f9f959499e724176ec9cdb63ce15292463d7fb03766cc31be`). Each records epoch 200 and step 102,400, the stamped configuration's hash, and a loss history equal to the run's `history.json` in `records/c2/return`. They were loaded with `torch.load(weights_only=True)`, allowing only torch's version class besides the defaults. The files (82 MB each) are not in the repository.

## Findings

1. **The host's seed 0 ended in the collapse the replays showed.** On nine training members, the relative variance of its latents is 0.0002 or less, against 0.64 to 0.73 for seed 2. The variation between nodes is already gone after the encoder's first block: there the residual stream of the first member has a mean square of 913,734, of which the node variance is 8,519 (0.9%; seed 2: 67%).
2. **It could not recover, because no gradient reaches its encoder.** At the final state the encoder's gradient norm is 1.3 × 10⁻¹¹ (median over 16 draws), against 0.195 and 0.100 for seeds 1 and 2. The cut is in the decoder and the head: in the first hidden layer of each, every unit's GELU input is below -5 at every node, displacement and member checked (the largest is -5.26 in the decoder and -5.60 in the head), where GELU's slope is below 7.2 × 10⁻⁶ in size. Only the last layers' biases still receive a gradient (norms 0.338 and 0.992); every other layer's is 7 × 10⁻⁵ or less. The outputs then depend on neither the member nor the node, which gives the uniform field the verdict found; its loss on the 16 draws is 0.0010 below the starting field's on average. The square roots of AdamW's second-moment estimates for the encoder are 2 × 10⁻¹⁷ to 4 × 10⁻¹³ (medians over its input layer, each block and its final LayerNorm): the encoder has had next to no gradient for a long time.
3. **In the replay of seed 0 the same death had begun.** Before the replays' collapses (steps 1,856 and 2,752), no unit in the first hidden layer of the decoder or the head was below -3 everywhere. At step 3,072, about 300 steps after seed 0's collapse, 14.5% of the decoder's first-layer units and 3.9% of the head's were; seed 1's replay, further into its recovery at the same step, had none.
4. **Seeds 1 and 2 kept a working decoder, seed 1 only just.** Every unit in seed 1's first decoder layer has a negative GELU input everywhere (the largest is -0.63), and 93.6% are below -3 everywhere; seed 2 also has 84.4% below -3, but its largest input is 9.62. Seed 1's latents vary far less between nodes than seed 2's (relative variance 0.03 to 0.07 against 0.64 to 0.73). Seed 1 is the seed that collapsed in epoch 14 and came back, and the one with the larger error in the verdict (median 6.61% against 2.41%). Whether these are connected was not examined.

## 1. What was run

- **`host_states.py`**, on each final state:
  - probes on nine training members (`train_0000`, `train_0064`, ..., `train_0448` and `train_0511`) at D = 0.5, 2 and 8 mm: the relative variance after the input layer, after each block and of the latents; the mean square and node variance of the residual stream after the first block and of that block's attention and MLP outputs; e/(D + δ);
  - the GELU inputs of the first and second hidden layers of the decoder and of the head over those members, nodes and displacements: each unit's largest input, and the share of units whose largest input is below -3 (slope below 0.012 in size) and below -5 (below 7.2 × 10⁻⁶);
  - gradient norms of the encoder (whole and by block), of each layer's weights and biases in the decoder and head, and the loss, on 16 draws (members from numpy's `default_rng(12345)`, displacements by `c2.train.step_loss`); the same loss for the starting field, the networks as `c2.train.train` builds them;
  - medians of the square root of AdamW's second moments, by block and network; the final LayerNorm's median |gain|.
- **`units.py`**, the same unit counts and the latents' relative variance for four replay checkpoints: the states the branches of `BRANCHES.md` started from (seed 1 at step 1,856, seed 0 at step 2,752), and the replays' last checkpoints (step 3,072), after their collapses.

## 2. The three final states

| | Seed 0 | Seed 1 | Seed 2 |
|---|---|---|---|
| Latents, relative variance, nine members | 0.0000 to 0.0002 | 0.0312 to 0.0708 | 0.6408 to 0.7325 |
| After block 1, first member: mean square; node variance | 913,734; 8,519 | 3,390,214; 639,230 | 4,732,130; 3,147,113 |
| Encoder gradient norm, median over 16 draws | 1.3 × 10⁻¹¹ | 0.195 | 0.100 |
| Decoder, first layer: largest GELU input; units below -3 and below -5 everywhere | -5.26; 100%, 100% | -0.634; 93.6%, 32.8% | 9.62; 84.4%, 0% |
| Head, first layer: largest GELU input; units below -3 and below -5 everywhere | -5.60; 100%, 100% | -0.587; 91.4%, 34.4% | 3.63; 69.9%, 0% |
| Gradient norm of the decoder's last bias; of the head's | 0.338; 0.992 | 1.75; 0.744 | 0.888; 0.550 |
| e/(D + δ), median over the nine members | 0.0008 | 0.262 | 0.265 |
| Loss minus the starting field's, mean over 16 draws | -0.0010 | -0.2598 | -0.2694 |
| Final LayerNorm, median of the gains' sizes | 0.924 | 0.502 | 0.322 |

- Seed 0's other gradients: the decoder's first-layer weights 7.9 × 10⁻¹², its second-layer bias 1.5 × 10⁻⁶ and last-layer weights 2.6 × 10⁻⁷; the head's second-layer bias 6.9 × 10⁻⁵ and last-layer weights 5.0 × 10⁻⁶.
- The second hidden layers of seed 0's decoder and head get inputs of about zero (largest 3.2 × 10⁻⁷ and 3.8 × 10⁻⁶), as the dead first layers pass on almost nothing.
- The mean square after the first block grew large in all three seeds over 200 epochs; what sets seed 0 apart is that 99% of it is shared by the nodes.

## 3. Before and after the replays' collapses

| Replay state | Latents, relative variance (median, nine members) | Decoder, first layer: largest GELU input; below -3 everywhere | Head, first layer: largest GELU input; below -3 everywhere |
|---|---|---|---|
| Seed 1, step 1,856, before | 0.8499 | 3.58; 0% | 1.46; 0% |
| Seed 1, step 3,072, after | 0.5661 | 4.93; 0% | 1.38; 0% |
| Seed 0, step 2,752, before | 0.8874 | 4.37; 0% | 1.63; 0% |
| Seed 0, step 3,072, after | 0.1156 | 5.23; 14.5% | 0.494; 3.9% |

No state in this table has a unit below -5 everywhere in the head; in seed 0's decoder after the collapse, 0.6% are.

## 4. Reading

**Shown.**
- The host's seed 0 ended where the replays' collapses lead: the first block's output shared by all nodes, latents that do not vary between nodes, and a uniform field.
- Its first hidden layers in the decoder and the head are dead for every input checked, so no gradient reaches anything before them. That is why it never came back.
- In the replay of seed 0, a collapse began to kill those units within 300 steps.

**Inferred, not tested.** Once every node and member gives the decoder nearly the same input, each unit is either active for all inputs or inactive for all of them, so units can die together; when the last one has died, no gradient reaches the encoder and the state is final. Seed 1's replay, which had recovered further, had lost no unit.

**Not shown.**
- When the host's seed 0 lost its last unit, and whether its collapse in epoch 8 was the cause. The host kept no state from before epoch 200.
- Whether seed 1's weaker decoder and less varied latents explain its larger error.

## 5. For the next pre-specification

- **Add two things to the probe of `RESULTS.md`**: the share of dead units in the first hidden layers of the decoder and the head (largest GELU input below -3 and below -5 over a fixed set of inputs), and the encoder's gradient norm. A seed whose units are all dead and whose encoder gradient is near 10⁻¹¹ cannot recover, and can be recorded as such when it happens.
- **Preventing the collapse** (`BRANCHES.md`) shuts the route into this state, as far as the replays show.
- **Guarding against the units' death itself** is a separate candidate, not tested: for example, normalising the decoder's and the head's inputs, or an activation without a flat region.

## 6. Files

- `host_states.py`, `units.py`.
- `records/host_states/host_states.json` and `.log`, `records/host_states/units.json` and `.log`: their outputs.
- Not kept: the three host states (SHA-256 above; on the host and with the author) and the four replay checkpoints (82 MB each; `RESULTS.md` and `BRANCHES.md` say how to make them again).

Run in this folder, with JOINT and DATA as in `RESULTS.md`, STATES a folder holding `label_free_s0/state.pt` to `label_free_s2/state.pt`, and copies of the checkpoint that `diag_seed.py` keeps (every 64 steps), taken at steps 1,856 and 3,072 of seed 1's replay and 2,752 and 3,072 of seed 0's:

```
python -I host_states.py JOINT DATA STATES records/host_states/host_states.json
python -I units.py JOINT DATA records/host_states/units.json "seed 1 before its collapse=s1_1856.ckpt.pt" "seed 1 after (replay end)=s1_3072.ckpt.pt" "seed 0 before its collapse=s0_2752.ckpt.pt" "seed 0 after (replay end)=s0_3072.ckpt.pt"
```
