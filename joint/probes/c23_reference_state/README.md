# The reference code's element state and the order of the exact solves

20 November 2026, after the verdict of gate G-C2.3. **Nothing here is a gate, nothing was pre-specified, and no verdict and no judged number changes.** The probes isolate a defect of the measuring code that the author's recomputation of G-C2.3 found; `docs/G-C2.3_verdict.md` states what it means for the gates.

## What the probes show

The judged error of a pair, $\lvert F/F^*(e) - 1\rvert$, needs an exact solve of the reference model at the predicted end displacement $e$ (`c2/evaluate.py`, `metrics`; `c2/instance.py`, `solve_at_e`).

- Each set of elements keeps the bubble parameters of its last accepted evaluation and starts its next evaluation from them (`fejoint/nlhex.py`: the attribute `bub`, written by `warm()`; `fejoint/nlsolve.py` calls `warm()` after every accepted iterate).
- The two problems of an exported member, with and without the loading spring, share their element sets, and the evaluation of a gate builds one problem object for a member. So the exact solve of a pair starts from the element state that the exact solve of the pair before it left.
- The element iteration is capped at 60 steps, and the first evaluation of a solve is not inside the solver's line search, which would shorten a step that cannot be evaluated. If that first evaluation does not end within the cap, the solve raises `RuntimeError: bubble condensation did not converge`, and `metrics` writes an infinite error, as it does for any failure of that solve.
- This happened where the pair before was at 8 mm and the pair itself at 0.5 mm or 1 mm, in a few cases. With the element state set to zero before the solve, every such solve converges.

## Run

From the `joint` folder, with `FEJOINT_SOLVER=legacy` where PARDISO is installed:

    python -I -B probes/c23_reference_state/cause.py RECORDS INSTANCES OUT.json
    python -I -B probes/c23_reference_state/pairs.py RECORDS INSTANCES MEMBER RUN:READING:LEVEL,RUN:READING:LEVEL[,...]
    python -I -B probes/c23_reference_state/c21_pair.py C21RETURN C21INSTANCES
    python -I -B probes/c23_reference_state/effect_on_reported_numbers.py RECORDS
    python -I -B probes/c23_reference_state/c21_effect.py C21RETURN
    python -I -B probes/c23_reference_state/nearest_label.py RECORDS

`RECORDS` is the kept copy of G-C2.3's return package whole, with the label and prediction files of its deposit (`records/c23/deposit.json`); `INSTANCES` a folder of G-C2.3's instances as `audit/c23_recompute.py --regenerate` writes them. `C21RETURN` is `records/c2/return` and `C21INSTANCES` a folder of G-C2.1's instances (`audit/c2_recompute.py`). The scripts call the stamped metric function and change nothing in the stamped code; `cause.py` and `pairs.py` set the attribute `bub` of the element sets from outside.

## Results

The outputs of a run of 22 November 2026 (numpy 2.4.6, scipy 1.18.1, scipy's SuperLU, one thread a process) are filed in this folder: `cause.json` and `cause.txt` (what `cause.py` wrote and printed), `pairs_third_0034.txt` (three orders, each named in the file), `pairs_eval_0063.txt`, `c21_pair.txt`, `effect_on_reported_numbers.txt`, `c21_effect.txt` and `nearest_label.txt`. The tables below quote them. For `c21_pair.py`, G-C2.1's 580 instances were regenerated first; all 580 files have the SHA-256 of that gate's manifest.

**`cause.py`, member `third_0034` of G-C2.3's third sample** (numpy 2.4.6, scipy 1.18.1, scipy's SuperLU)

| What was done | Signed error of the label-free seed 7, condensed, 0.5 mm |
|---|---|
| after the pair "seed 6, condensed, 8 mm", element state kept | infinite: bubble condensation did not converge |
| a new problem object, given nothing but the element state that this pair left | infinite, the same note |
| the same order, the element state set to zero in between | 0.003727693919260533 |
| after the pair "seed 6, raw, 8 mm", which precedes it in the gate's order | 0.003727693919260977, the returned value bit for bit |

The last row is from `pairs.py` (the second order in `pairs_third_0034.txt`); the others are from `cause.py`.

- The failing evaluation is the first of the solve. Of the two element sets, the flange converges from the kept state in 15 element iterations (3 from zero). The web and root do not converge within the cap of 60; with the cap raised to 200 they converge in 62 iterations (2 from zero), to an energy of 125.87613177510924 against 125.87613177510926 from zero.
- The host's own infinite row of this member (seed 6, raw, 0.5 mm, after "seed 6, condensed, 8 mm") is reproduced with the element state kept, and gives -0.0027282879135048788 with the state set to zero.

**`pairs.py`, member `eval_0063`, supervised runs** (the two other infinite rows of G-C2.3's return)

| Pair, in the gate's order | Returned | Element state kept | Element state set to zero before the pair |
|---|---|---|---|
| seed 5, raw, 8 mm | 0.022238755425174617 | 0.02223875542517595 | 0.02223875542517595 |
| seed 6, condensed, 0.5 mm | infinite | infinite | 1.020935954139211 |
| seed 6, condensed, 1 mm | infinite | infinite | 1.0537772160075902 |
| seed 6, condensed, 2 mm | 0.6404322964574589 | 0.6404322964574589 | 0.6404322964574594 |

A failed solve leaves the element state as it was, so the failure at 0.5 mm carries on to 1 mm.

**`c21_pair.py`, member `eval_0046` of G-C2.1** (the one failed reference solve in G-C2.1's verdict: supervised_64, seed 1, 0.5 mm)

| What was done | Signed error |
|---|---|
| the pair alone, on a new problem object | -0.004491609982833267 |
| after "supervised_64, seed 0, 8 mm", the pair before it in G-C2.1's order | infinite: bubble condensation did not converge |
| the same order, the element state set to zero in between | -0.004491609982833267 |

**`effect_on_reported_numbers.py`**: what the reported numbers of G-C2.3 that contain the three infinite rows would be with the values above. No judged number contains such a row. The last lines of `effect_on_reported_numbers.txt` list every printed figure of `docs/G-C2.3_verdict.md` that contains one of the rows; the block of part 1 is computed there with the stamped function.

| Reported number | Returned | With the values from a zero element state |
|---|---|---|
| label-free arm, raw, third sample: median of seed 6, and median over the seeds | 1.358019% | 1.353574% |
| the same: 90th percentile of seed 6 (the median over the seeds is seed 7's) | 10.190997% | 10.012299% |
| the same: pairs above 10% in seed 6 | 46 | 45 |
| ratio of the medians, both arms raw, third sample | 1.2570 | 1.2611 |
| supervised arm, condensed, fresh members of G-C2.2: 90th percentile of seed 6, and median over the seeds | 120.457254% | 120.104349% |
| ratio of the 90th percentiles, both arms condensed, fresh members of G-C2.2 | 32.876 | 32.780 |
| part 1 applied to the raw reading, third sample: pairs not flagged above 10%; readings not flagged above 5% | 4; 31 of 708 | 3; 30 of 708 |
| the same block: ranking probability of seed 6 | 0.8592 | 0.8678 |
| label-free arm, raw, seed 6, third sample, at 0.5 mm: median; 90th percentile; median signed error | 0.95%; 3.70%; +0.06% | 0.91%; 3.06%; +0.03% |
| rows with an infinite error | 3 | 0 |

**`c21_effect.py`**: what the figures of G-C2.1's verdict document that contain its failed solve would be with the value above. They are figures of one run of the supervised arm, which is descriptive in that gate.

| Figure of supervised_64, seed 1, held-out members | Returned | With the value from a zero element state |
|---|---|---|
| pairs above 10%, and infinite distances | 128, 1 | 127, 0 |
| median and 90th percentile over the 448 pairs | 5.9823%, 20.6081% | 5.9697%, 20.4660% |
| at 0.5 mm: median, 90th percentile, pairs above 10% | 10.7909%, 28.6853%, 34 | 10.6241%, 27.7512%, 33 |
| the tail above the 90th percentile: pairs at 6 and 8 mm, at 0.5 and 1 mm, in members below 300 MPa | 18, 23, 22 | 19, 22, 22 |

The median signed distances, over the 448 pairs and at 0.5 mm, do not change.

**`nearest_label.py`**: from which label the exact solve of a pair starts. The stamped metric starts it from the label nearest to the pair's predicted end displacement, so the start depends on the pair. Counted over the returned predictions of the 132 evaluated members, 396 pairs at each level for an arm's reading:

| Arm and reading | Pairs whose nearest label is not that of their own level, at 0.5, 1, 2, 3, 4, 6 and 8 mm |
|---|---|
| label-free, condensed | 0, 0, 0, 0, 0, 0, 0 |
| label-free, raw | 0, 0, 0, 0, 1, 1, 13 |
| supervised, condensed | 0, 395, 391, 396, 396, 396, 396 |
| supervised, raw | 0, 0, 0, 0, 0, 0, 0 |

- At 0.5 mm all 1,584 pairs start from the label of 0.5 mm, each with its own end displacement put in. There a failure was set, in everything that was measured, by the element state left and not by the pair that follows.
- The supervised arm's condensed fields have about half the end displacement, so above 0.5 mm their solves nearly always start from the label of a level below. The pair of `eval_0063` at 1 mm (seed 6, condensed) starts from the label of 0.5 mm, as the pair at 0.5 mm before it did, and fails from the same kept state. In `third_0034` the pair at 1 mm starts from the label of 1 mm and converged.
- The independent audit of G-C2.3 found this in its second round (`docs/reviews/audit_report_G-C2.3_2026-11-22.md`); the script was written after it.

## What this does not show

- How often a solve fails for this reason in general. In G-C2.3's run 3 of 11,088 rows failed, in 2 chains; in G-C2.1's, 1 row; in G-C2.2's, none.
- That every converged solve is independent of the element state it started from. The problem is convex, and where two recomputations in different orders both converged they agree to within the figures that `docs/G-C2.3_verdict.md` gives; nothing more was tested.
