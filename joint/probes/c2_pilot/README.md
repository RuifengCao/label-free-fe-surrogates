# CPU pilots of gate G-C2.1 (6 November 2026)

Exploratory, not a gate. They shaped the loading and the reading of the force in `c2/`, as `docs/PRESPEC_G-C2.1.md` states.

**Common settings.** Members drawn with seed 8 (32 training members) and seed 7 (6 held-out members), and Bursi and Jaspart's preloaded T1 as a tested member: all in SEEDS_SEEN, outside the gate's samples. The coarse mesh (10 mm, one layer through the flange). A small model: width 64, depth 2, 4 heads, no activation checkpointing. Otherwise the configuration's training settings: AdamW at $10^{-3}$, the repository's cosine schedule with 5% warm-up over each run's own steps, one member and four loading levels per step, the mean of $\log \Pi$ as the loss, float32. One seed (0). CPU, one thread.

**Scripts.** `pilot_cpu.py` exports a pilot family with the gate's code and labels its held-out and tested members; `pilot_trend.py` trains on it with evaluations along the way; `pilot_curve.py` evaluates a saved model with the full metrics of `c2/evaluate.py`. These are their final versions.
- `pilot_cpu.py` once also trained and evaluated (`pilot_coarse_summary.json`). That part went out of date when the evaluation changed to the curve metric and was removed: every later pilot trained through `pilot_trend.py`.
- The runs under displacement control and with the stiff spring used earlier versions of these scripts and of `c2/` (6 November 2026); what each reading meant there is stated below.
- Example: `python pilot_cpu.py JOINT soft_plastic --workers 1`, then `python pilot_trend.py JOINT soft_plastic/data trend_soft_plastic300 --epochs 300 --eval_at 60,150,300 --lift web`, with `JOINT` the path of `joint/`.
- The records in `records/` are the scripts' outputs, except that in their `args` the local path of `joint/` is left out and the data folder is named by the pilot family's folder alone, and that `curve_spring_plastic300.json` (the output `curve_eval.json` of `pilot_curve.py`) carries a note on how it was made.

## Under displacement control (the end section's displacement prescribed)

The force was read from the stresses, $F = 4\,\nabla\Pi \cdot v$ with $v$ a ramp in the web; `F_E` is the derivative of the predicted energy along the load, $4\,dE/dd$ by central differences. Levels 0.1 to 3 mm.

| Record | Material | Web lifted | Steps | Median abs force error | 90th percentile | Median energy gap | Contact overlap |
|---|---|---|---|---|---|---|---|
| `pilot_coarse_summary.json` | plastic | no | 1,920 | 34.8% | 86.8% | 39.0% | 0.00 |
| `trend_coarse_a.json`, epoch 60 of 300 (stopped at 80) | plastic | no | 1,920 | 102.8% | 192.8% | 71.3% | 0.00 |
| `trend_coarse_lift60.json` | plastic | yes | 1,920 | 35.1% | 80.0% | 34.9% | 0.00 |
| `trend_plastic_FE60.json` (the same run, with `F_E`: 40.8%) | plastic | yes | 1,920 | 35.1% | 80.0% | 34.9% | 0.00 |
| `trend_plastic_lift300.json`, epoch 300 (`F_E`: 12.5%) | plastic | yes | 9,600 | 12.6% | 38.5% | 8.2% | 0.67 |
| `trend_elastic60.json` (`trend_elastic_FE60.json`: `F_E` 70.4%) | elastic, see below | no | 1,920 | 34.0% | 185.6% | 1.1% | 0.79 |
| `trend_elastic_save.json` | elastic, see below | yes | 1,920 | 34.5% | 113.1% | 1.3% | 0.82 |

**The elastic controls under displacement control are flawed.** Their yield stresses of steel and bolt were multiplied by 100, and so, by mistake, was the bolt's yield force from which the preload is set: the preload was a hundred times too large. The preload's energy then dominated $\Pi$, so their energy gaps look small. The force errors stand, but the gaps do not compare with the plastic runs. Found in `trend_elastic_save`, whose saved model showed bolt forces of about 5.6 MN. The controls under spring loading set the preload from the nominal yield force.

## Under spring loading, $k_s = 100$ kN/mm per quarter, $D$ up to 4 mm

The force is the spring reading $F = 4 k_s (D - e)$, compared at the same $D$; `F_sigma` is the stress reading as above; `e` is the end displacement.

| Record | Material | Web lifted | Steps | Median abs force error | 90th percentile | Stress reading | End displacement | Median energy gap | Contact overlap |
|---|---|---|---|---|---|---|---|---|---|
| `trend_spring_elastic60.json` | elastic, nominal preload | yes | 1,920 | 5.6% | 31.7% | 11.5% | 6.8% | 6.8% | 0.58 |
| `trend_spring_plastic300.json`, epoch 120 | plastic | yes | 3,840 | 28.9% | 69.7% | 15.7% | 12.5% | 14.5% | 0.59 |
| `trend_spring_plastic300_nolift.json`, epoch 120 (stopped after it) | plastic | no | 3,840 | 26.2% | 103.3% | 23.5% | 16.1% | 18.0% | 0.50 |
| `trend_spring_plastic300.json`, epoch 300 | plastic | yes | 9,600 | 11.2% | 20.1% | 8.8% | 4.7% | 4.8% | 0.73 |

In the last run the force error was 4% to 8% at $D$ up to 1 mm and 15% to 16% at 2 to 4 mm. The distance of its predicted points from the reference curve (`curve_spring_plastic300.json`, `pilot_curve.py` on the saved model, with the load feature scaled by 4 mm as in its training) was 14.7% in the median and 32.4% at the 90th percentile: 22% at $D = 0.1$ mm, 8% to 10% at 0.25 to 1 mm, 15% to 16% at 2 to 4 mm. There $e/(D - e)$ is 2 to 13, and the reading at the same $D$ magnifies the error of $e$ by that factor: the reason for the softer spring and the curve metric below.

## Under spring loading, $k_s = 20$ kN/mm per quarter, $D$ up to 8 mm (the gate's loading)

Judged as the gate judges: the distance of the predicted point $(e, F)$ from the reference curve, $F/F^*(e) - 1$, $F^*(e)$ from an exact solve at the predicted $e$.

`trend_soft_plastic300.json`, evaluated at epochs 60, 150 and 300 with `c2/evaluate.py`'s metrics. The distance from the curve is the judged quantity; the other columns are reported only.

| Epoch | Steps | Median distance from the curve | 90th percentile | Force at the same $D$ | Stress reading | End displacement | Median energy gap | Contact overlap | Plastic overlap |
|---|---|---|---|---|---|---|---|---|---|
| 60 | 1,920 | 35.0% | 170.0% | 14.5% | 28.2% | 51.0% | 10.1% | 0.59 | 0.24 |
| 150 | 4,800 | 26.2% | 80.6% | 8.2% | 12.0% | 28.0% | 4.6% | 0.62 | 0.34 |
| 300 | 9,600 | 9.6% | 37.9% | 4.3% | 7.6% | 10.4% | 2.6% | 0.62 | 0.51 |

Median distance from the curve by level:

| $D$ (mm) | 0.5 | 1 | 2 | 3 | 4 | 6 | 8 |
|---|---|---|---|---|---|---|---|
| epoch 60 | 20.2% | 15.9% | 14.5% | 21.8% | 41.3% | 102.3% | 159.4% |
| epoch 150 | 15.8% | 18.9% | 5.1% | 10.4% | 28.1% | 55.9% | 71.8% |
| epoch 300 | 9.4% | 6.1% | 5.6% | 8.0% | 14.3% | 12.7% | 11.4% |

- At the same $D$ the force error was 2.1% to 2.7% up to $D = 2$ mm at epoch 60, while the distance from the curve there was 14% to 20%: in the elastic range the soft spring sets the force, and the reading at the same $D$ hides the T-stub's error.
- On the preloaded T1 the distance at epoch 300 was 27.3%, 24.7%, 6.3%, 4.6%, 7.3%, 5.7% and 13.0% at the seven levels.
- Against the stiff spring's run after the same 9,600 steps (14.7% and 32.4%, over $D$ up to 4 mm): a smaller median over a longer range of end displacement (to about 5 mm against about 3 mm), and a 90th percentile a little larger.

Row by row at epoch 300 (`curve_soft_plastic300.json`, `pilot_curve.py` on the saved model; it reproduces the median and the 90th percentile above):
- 19 of the 42 held-out pairs lie above 10%, 10 above 20% and 6 above 30%. The signed median is +8.5%: the predicted end displacements are mostly too small and the forces too large.
- The weakest held-out member (`eval_0005`: $t_f$ 10.4 mm, $w$ 103 mm, $f_y$ 295 MPa, $\rho$ 0.79; a plastic force of 105 to 121 kN, about half the others') lies 32% to 89% above the curve from $D = 3$ mm on, its end displacement 19% to 24% short.
- At $D$ of 0.5 and 1 mm, where the end displacement is under 0.2 mm, `eval_0000` lies 54% and 39% above the curve and `eval_0002` 22% and 26%; the other four held-out members lie within 13%.
