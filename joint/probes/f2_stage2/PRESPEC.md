# Trial of two changes to the second training cycle of the CHS surrogate: plan fixed before the runs

Written on 24 November 2026, before either run of the trial was started. Exploratory, not a gate: the trial chooses
the recipe that a later gate will test on members not seen so far. Nothing here supports a claim about accuracy on
unseen connections.

## Question

After the second cycle of 22 November 2026 (formal mesh, seed 0) the error of the moment at the same joint rotation
is concentrated in thin plates and at the last evaluation level. Two changes of the second cycle are tried, each
once, to see whether they lower that error without raising the others:

1. the device rotations of the training steps drawn uniformly, and up to 1.15 times the member's device range
   (so far: sqrt(Theta) uniform, up to the device range, which is the last evaluation level);
2. the same, with 32 more training members with thin plates.

## What is run

All three runs are second cycles on the family's mesh from the same starting weights: the final weights of the
first cycle, preset fam128_bending_e400, seed 0, step 51,200 (state.pt, SHA-256
a53454d474a964f9a015ffbc68c51031d35cc8e693a0dae3a3c50d9eaf444904). Each has 25,600 steps, a peak learning rate of
3e-4 with the same warm-up, cosine schedule, optimiser, gradient cap and clipping, seed 0, four device rotations a
step, and no label.

| run | preset | rotations of a step | training members | epochs |
|---|---|---|---|---|
| control (run on 22 November 2026) | fam128_bending_more | sqrt(Theta) uniform between 0.0125 Theta_max and Theta_max | 128 | 200 |
| arm 1 | fam128_bending_more_u | Theta uniform between 0.0125 Theta_max and 1.15 Theta_max | 128 | 200 |
| arm 2 | fam128_bending_more_ux | as arm 1 | 128 and 32 more | 160 |

The 32 extra members of arm 2 are drawn with seed 20261124 over the family's ranges with the plate thickness
between 10 and 12.5 mm, exported with their preload solve and never solved further (f2.data.extra_config). The
control kept two averages of its weights; they took no part in its training and are not used here; the arms keep
none. The control is not run again: its final weights and its evaluation of 22 November 2026 are used
(configuration f2eced7a4990b1934783dd6d2ce05cbd4eafc6dcf757b23e3f856bf8ebd64c2a).

The arms are evaluated as the control was: the 31 evaluated members of the development (16 drawn at random, 11
picked by hand, 4 tested splices) at the seven levels 0.0625, 0.125, 0.25, 0.375, 0.5, 0.75 and 1 of the device
range, against the reference solutions already computed, in the condensed reading (f2/evaluate.py).

## Measures

e is abs_curveD_err of f2/evaluate.py: the absolute relative difference between the surrogate's moment and the
reference moment at the surrogate's joint rotation. Percentiles are numpy's default (linear interpolation).

| | measure | control |
|---|---|---|
| P | median of e at the last level over the 8 evaluated members with a plate thinner than 12.5 mm | 7.0742 % |
| G1 | median of e at the last level over the 31 members | 3.4209 % |
| G2 | median of e over the 217 points | 0.9878 % |
| G3 | 90th percentile of e over the 217 points | 3.6862 % |
| G4 | 90th percentile of e over the 112 points of the 16 members drawn at random | 2.8869 % |
| G5 | median of e over the 62 points of the two lowest levels | 0.7891 % |

The 8 members of P: dev_T10hi, dev_W1, dev_W2, eval_0001, eval_0003, eval_0005, eval_0006, eval_0013.

## Rule

An arm passes if its run finished its 25,600 steps and

    P <= 5.30 %  and  G1 <= 3.76 %  and  G2 <= 1.09 %  and  G3 <= 4.06 %  and  G4 <= 3.18 %  and  G5 <= 0.87 %

(P at least a quarter below the control; no other measure more than a tenth above it), the values compared without
rounding.

- Both arms pass: arm 2 is taken if its P is at least 0.5 percentage points below arm 1's; otherwise arm 1, which
  needs no extra data.
- One arm passes: it is taken.
- No arm passes: the second cycle stays as it was run on 22 November 2026.

A run stopped by a non-finite loss does not pass. A run interrupted from outside (session, compute units) is resumed
from its checkpoint and judged when finished. Whatever the outcome, no further change is tried before the gate.

## Reported outside the rule

The last-level errors of dev_W1 and dev_W2 (control 56.9 % and 14.7 %), the largest error, the raw reading, the
errors by level and by thickness band, the statistics without the last level, and the snapshots during training.

## What limits the conclusion

One run an arm: how much two second cycles from the same weights differ by chance has not been measured, which is
why P must fall by a quarter. The 31 members have been watched throughout the development. The arms may run on
another of the allowed GPU models than the control (RTX PRO 6000); this is recorded in each run's history.
