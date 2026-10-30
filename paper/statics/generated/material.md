# Manuscript material (generated from the committed records; do not edit)

### Two-dimensional plates, every metric at the largest label budget. The supervised networks were trained on 1,024 labelled instances; the label-free transformer on the same 1,024 instances without their solutions.

| Model | Displacement error | Relative energy gap | von Mises error | Peak stress error | Critical-region recall | Worse than zero field |
|---|---|---|---|---|---|---|
| Label-free | 0.0634 ± 0.0031 | 0.0383 ± 0.0019 | 0.123 ± 0.002 | 0.128 ± 0.001 | 0.753 ± 0.001 | 0/768 |
| Supervised, displacement | 0.0505 ± 0.0023 | 0.133 ± 0.014 | 0.235 ± 0.015 | 0.141 ± 0.007 | 0.668 ± 0.015 | 0/768 |
| Supervised, energy norm | 0.0547 ± 0.0094 | 0.0290 ± 0.0125 | 0.106 ± 0.020 | 0.0947 ± 0.0356 | 0.804 ± 0.055 | 0/768 |
| Graph network, displacement | 0.0499 ± 0.0003 | 0.825 ± 0.020 | 0.578 ± 0.009 | 0.321 ± 0.011 | 0.517 ± 0.006 | 187/768 |
| Nearest-neighbour field | 0.404 | 0.959 | 0.735 | 0.643 | 0.515 | 94/256 |
| Scaled polynomial | 1.42 | 873 | 11.4 | 30.8 | 0.159 | 256/256 |
| Ritz projection, $p = 6$ | 0.0500 | 0.0404 | 0.122 | 0.272 | 0.828 | 0/256 |
| Ritz projection, $p = 8$ | 0.0424 | 0.0333 | 0.109 | 0.208 | 0.852 | 0/256 |
| Zero field | 1.00 | 1.00 | 1.00 | 1.00 | – | – |

- 256 validation instances, never trained on; four load cases each. Errors are relative to the reference finite-element solution, per load case, then averaged over the load cases; the relative energy gap of the zero field is 1. Trained networks: mean ± sample standard deviation over 3 seeds; the nearest-neighbour field and the scaled polynomial are deterministic.
- Worse than zero field: instance-seed pairs whose relative energy gap, the mean over the four load cases as the evaluation records it, exceeds 1, that is, predictions further from the solution in the energy norm than the zero field on average; the count uses the reference solutions. The test of \cref{cor:zero} needs none and applies to single load cases (\cref{sec:methods:metrics}).
- Critical-region recall: the share of the 10% most stressed elements of the reference solution that are also among the 10% most stressed of the prediction (higher is better; in every other column lower is better).
- The two-dimensional comparison (\cref{sec:methods:prereg}). The label-free row evaluates, without retraining them, the label-free networks of the latent-regularisation run (supplementary Section~\SuppSide), trained on the same 1,024 instances. Supervised, energy norm: the same transformer trained on $\mathcal{L}_K$ \eqref{eq:lk} instead of $\mathcal{L}_D$ \eqref{eq:ld}, with everything else unchanged.
- Ritz projection (\cref{sec:methods:ritz}), added after the pre-registered runs: computed per instance from its own stiffness matrix and loads, without labels or training, with 42 and 72 unknowns at $p = 6$ and 8; deterministic, so its count of predictions worse than the zero field is over the instances.

### Two-dimensional plates, the July run with the earlier code: every metric at the largest label budget, on the instances of \cref{tab:2d}.

| Model | Displacement error | Relative energy gap | von Mises error | Peak stress error | Critical-region recall | Worse than zero field |
|---|---|---|---|---|---|---|
| Label-free | 0.166 ± 0.002 | 0.0817 ± 0.0040 | 0.210 ± 0.003 | 0.228 ± 0.001 | 0.739 ± 0.003 | 3/768 |
| Supervised, displacement | 0.160 ± 0.003 | 0.418 ± 0.037 | 0.433 ± 0.031 | 0.334 ± 0.036 | 0.584 ± 0.027 | 52/768 |
| Supervised, displacement + energy term | 0.161 ± 0.005 | 0.166 ± 0.040 | 0.257 ± 0.007 | 0.246 ± 0.022 | 0.708 ± 0.012 | 14/768 |
| Label-free, then supervised | 0.166 ± 0.006 | 0.236 ± 0.032 | 0.336 ± 0.020 | 0.301 ± 0.019 | 0.645 ± 0.008 | 21/768 |
| Graph network, displacement | 0.167 ± 0.000 | 2.57 ± 0.25 | 1.10 ± 0.07 | 1.32 ± 0.13 | 0.322 ± 0.027 | 481/768 |
| Nearest-neighbour field | 0.404 | 0.959 | 0.735 | 0.643 | 0.515 | 94/256 |
| Scaled polynomial | 1.42 | 873 | 11.4 | 30.8 | 0.159 | 256/256 |
| Zero field | 1.00 | 1.00 | 1.00 | 1.00 | – | – |

- 256 validation instances, never trained on; four load cases each. Errors are relative to the reference finite-element solution, per load case, then averaged over the load cases; the relative energy gap of the zero field is 1. Trained networks: mean ± sample standard deviation over 3 seeds; the nearest-neighbour field and the scaled polynomial are deterministic.
- Worse than zero field: instance-seed pairs whose relative energy gap, the mean over the four load cases as the evaluation records it, exceeds 1, that is, predictions further from the solution in the energy norm than the zero field on average; the count uses the reference solutions. The test of \cref{cor:zero} needs none and applies to single load cases (\cref{sec:methods:metrics}).
- Critical-region recall: the share of the 10% most stressed elements of the reference solution that are also among the 10% most stressed of the prediction (higher is better; in every other column lower is better).
- The July run (16 July 2026). Its code did not multiply the load scale back onto the output (\cref{sec:methods:networks}); we attribute the narrow spread of the displacement errors to this; no experiment isolated it.

### Three-dimensional solids, every metric at the largest label budget. The supervised networks were trained on 1,024 labelled instances; the label-free transformer on the same 1,024 instances without their solutions.

| Model | Displacement error | Relative energy gap | von Mises error | Peak stress error | Critical-region recall | Worse than zero field |
|---|---|---|---|---|---|---|
| Label-free | 0.0300 ± 0.0028 | 0.00912 ± 0.00228 | 0.0554 ± 0.0045 | 0.0807 ± 0.0134 | 0.793 ± 0.022 | 0/768 |
| Supervised, displacement | 0.0470 ± 0.0038 | 31.2 ± 53.5 | 0.370 ± 0.140 | 0.784 ± 0.807 | 0.619 ± 0.005 | 18/768 |
| Supervised, displacement + energy term | 0.0470 ± 0.0122 | 0.116 ± 0.050 | 0.128 ± 0.008 | 0.115 ± 0.026 | 0.730 ± 0.006 | 2/768 |
| Supervised, energy norm | 0.0227 ± 0.0022 | 0.00504 ± 0.00022 | 0.0440 ± 0.0014 | 0.0386 ± 0.0011 | 0.858 ± 0.001 | 0/768 |
| Graph network, displacement | 0.0168 ± 0.0001 | 0.447 ± 0.084 | 0.296 ± 0.010 | 0.488 ± 0.011 | 0.679 ± 0.009 | 28/768 |
| Nearest-neighbour field | 0.382 | 1.22 | 0.717 | 1.23 | 0.509 | 88/256 |
| Scaled polynomial | 1.56 | 4,362 | 14.9 | 54.8 | 0.137 | 256/256 |
| Ritz projection, $p = 6$ | 0.0208 | 0.0183 | 0.0854 | 0.321 | 0.811 | 0/256 |
| Ritz projection, $p = 7$ | 0.0134 | 0.0114 | 0.0624 | 0.283 | 0.859 | 0/256 |
| Ritz projection, $p = 8$ | 0.0100 | 0.00838 | 0.0521 | 0.253 | 0.879 | 0/256 |
| Ritz projection, $p = 9$ | 0.00798 | 0.00654 | 0.0449 | 0.223 | 0.896 | 0/256 |
| Zero field | 1.00 | 1.00 | 1.00 | 1.00 | – | – |

- 256 validation instances, never trained on; four load cases each. Errors are relative to the reference finite-element solution, per load case, then averaged over the load cases; the relative energy gap of the zero field is 1. Trained networks: mean ± sample standard deviation over 3 seeds; the nearest-neighbour field and the scaled polynomial are deterministic.
- Worse than zero field: instance-seed pairs whose relative energy gap, the mean over the four load cases as the evaluation records it, exceeds 1, that is, predictions further from the solution in the energy norm than the zero field on average; the count uses the reference solutions. The test of \cref{cor:zero} needs none and applies to single load cases (\cref{sec:methods:metrics}).
- Critical-region recall: the share of the 10% most stressed elements of the reference solution that are also among the 10% most stressed of the prediction (higher is better; in every other column lower is better).
- The three-dimensional comparison (\cref{sec:methods:prereg}). Supervised, energy norm: the three-dimensional energy-norm run (\cref{sec:norm:three}), the same transformer trained on $\mathcal{L}_K$ \eqref{eq:lk} with the same labelled instances, settings and seeds, beside the stored label-free and displacement-supervised transformers, which it evaluated again, reproducing their values exactly.
- Ritz projection (\cref{sec:methods:ritz}), added after the pre-registered runs: computed per instance from its own stiffness matrix and loads, without labels or training, with 168, 252, 360 and 495 unknowns at $p = 6$, 7, 8 and 9; deterministic, so its count of predictions worse than the zero field is over the instances.

### Label efficiency: relative displacement error / relative energy gap against the number of labelled training instances (seed means).

| Run | Model | 16 | 64 | 256 | 1,024 |
|---|---|---|---|---|---|
| 3D | Supervised, displacement | 0.395 / 18.5 | 0.288 / 5.95 | 0.0726 / 0.799 | 0.0470 / 31.2 |
| 3D | Supervised, displacement + energy term | 0.369 / 0.621 | 0.256 / 0.854 | 0.0833 / 0.964 | 0.0470 / 0.116 |
| 3D | Graph network, displacement | – | 0.149 / 18.3 | – | 0.0168 / 0.447 |
| 3D | Nearest-neighbour field | 0.648 / 5.74 | 0.477 / 2.24 | 0.400 / 1.20 | 0.382 / 1.22 |
| 3D | Label-free (no labels) | 0.0300 / 0.00912 | 0.0300 / 0.00912 | 0.0300 / 0.00912 | 0.0300 / 0.00912 |
| 2D | Supervised, displacement | 0.459 / 20.8 | 0.165 / 3.06 | 0.0712 / 0.430 | 0.0505 / 0.133 |
| 2D | Supervised, energy norm | 0.362 / 0.254 | 0.0889 / 0.0505 | 0.0667 / 0.0383 | 0.0547 / 0.0290 |
| 2D | Graph network, displacement | – | 0.370 / 149 | – | 0.0499 / 0.825 |
| 2D | Nearest-neighbour field | 0.687 / 6.50 | 0.466 / 1.65 | 0.408 / 1.03 | 0.404 / 0.959 |
| 2D | Label-free (no labels) | 0.0634 / 0.0383 | 0.0634 / 0.0383 | 0.0634 / 0.0383 | 0.0634 / 0.0383 |

- Seed means over 3 seeds; the nearest-neighbour field is deterministic. A dash marks a budget at which the model was not trained (the graph network was trained at 64 and 1,024 labels only). 3D: the three-dimensional comparison (\cref{tab:3d}); 2D: the two-dimensional comparison (\cref{tab:2d}). The label-free row repeats its single value, which uses the same 1,024 instances without labels.

### The July run (two dimensions, earlier code): relative displacement error / relative energy gap against the number of labelled training instances (seed means).

| Model | 16 | 64 | 256 | 1,024 |
|---|---|---|---|---|
| Supervised, displacement | 0.272 / 6.26 | 0.193 / 2.72 | 0.176 / 1.26 | 0.160 / 0.418 |
| Supervised, displacement + energy term | 0.410 / 2.56 | 0.184 / 0.579 | 0.182 / 0.154 | 0.161 / 0.166 |
| Label-free, then supervised | 0.207 / 1.32 | 0.189 / 0.201 | 0.181 / 0.302 | 0.166 / 0.236 |
| Graph network, displacement | 0.684 / 92.6 | 0.425 / 80.6 | 0.181 / 7.55 | 0.167 / 2.57 |
| Nearest-neighbour field | 0.687 / 6.50 | 0.466 / 1.65 | 0.408 / 1.03 | 0.404 / 0.959 |
| Label-free (no labels) | 0.166 / 0.0817 | 0.166 / 0.0817 | 0.166 / 0.0817 | 0.166 / 0.0817 |

- Seed means over 3 seeds; the nearest-neighbour field is deterministic, and the same as in \cref{tab:labeleff}. The graph network was trained at every budget in this run. The label-free row repeats its single value, which uses the same 1,024 instances without labels.

### Three-dimensional solids on the finer mesh (lc = 0.0374), never trained on. Zero-shot rows use the networks trained in-band; few-shot rows train, with labels, on the first 16 or on all of the 64 fine-mesh instances reserved for few-shot training.

| Model | Displacement error | Relative energy gap | von Mises error | Peak stress error | Critical-region recall |
|---|---|---|---|---|---|
| Label-free, zero-shot | 0.258 ± 0.045 | 0.306 ± 0.220 | 0.305 ± 0.063 | 0.769 ± 0.667 | 0.721 ± 0.006 |
| Supervised (1,024 labels), zero-shot | 0.257 ± 0.048 | 0.985 ± 0.267 | 0.537 ± 0.040 | 2.56 ± 1.39 | 0.462 ± 0.028 |
| Graph network (1,024 labels), zero-shot | 0.459 ± 0.010 | 16.3 ± 9.6 | 2.40 ± 0.84 | 11.6 ± 7.8 | 0.0610 ± 0.0083 |
| Nearest-neighbour field | 0.401 | 4.98 | 1.55 | 3.61 | 0.232 |
| Scaled polynomial | 1.95 | 540 | 18.7 | 134 | 0.102 |
| Ritz projection, $p = 6$ | 0.0225 | 0.0199 | 0.0906 | 0.460 | 0.807 |
| Ritz projection, $p = 7$ | 0.0149 | 0.0126 | 0.0676 | 0.424 | 0.855 |
| Ritz projection, $p = 8$ | 0.0113 | 0.00943 | 0.0575 | 0.390 | 0.878 |
| Ritz projection, $p = 9$ | 0.00904 | 0.00729 | 0.0494 | 0.353 | 0.895 |
| Label-free, then 16 fine-mesh labels | 0.0531 ± 0.0030 | 0.0702 ± 0.0112 | 0.166 ± 0.016 | 0.389 ± 0.061 | 0.715 ± 0.004 |
| Supervised from scratch, 16 fine-mesh labels | 0.799 ± 0.037 | 2.34 ± 1.25 | 1.07 ± 0.19 | 2.58 ± 1.23 | 0.116 ± 0.014 |
| Label-free, then 64 fine-mesh labels | 0.0298 ± 0.0020 | 0.0520 ± 0.0088 | 0.126 ± 0.018 | 0.272 ± 0.068 | 0.731 ± 0.014 |
| Supervised from scratch, 64 fine-mesh labels | 0.193 ± 0.076 | 13.2 ± 5.3 | 2.57 ± 0.47 | 8.94 ± 4.65 | 0.128 ± 0.043 |

- 256 fine-mesh evaluation instances (median 36,216 nodes), disjoint from the 64 instances reserved for few-shot training. Mean ± sample standard deviation over 3 seeds; the naive baselines are deterministic and built from the 1,024 in-band labelled instances.
- In-band, the label-free network's displacement error is 0.0300; the zero-shot ratio is therefore 8.62.
- Few-shot training minimises the relative displacement error $\mathcal{L}_D$ \eqref{eq:ld}, without the energy term, for 50 epochs at learning rate 1.5 × 10⁻³, from the trained label-free network of the same seed or from random initialisation (scratch); the few-shot comparison was pre-registered as reported only. Ritz projection: \cref{sec:methods:ritz}, added after the pre-registered runs, deterministic, on the fine meshes themselves, with nothing trained.

### The pre-registered claims of the comparisons reported in this paper, with the outcomes that the code recorded at the time.

| Run | Criterion | Measured | Outcome |
|---|---|---|---|
| July run (2D), 16 July 2026 | K5: conjugate gradients from the prediction of a label-free network (64 validation instances) save < 20% of the iterations from zero | −0.9% | triggered |
| Three-dimensional comparison, 28 September 2026 | G2 (a), budgets ≥ 64 (amendment): displacement-supervised transformer with the energy term at least 3 times better than the zero field in displacement, and better than both naive baselines | 3.9 / 12.0 / 21.3 times; naive beaten | met |
|  | G2 (a), every budget (the registered form, reported for reference) | 2.71 times at 16 labels | not met |
|  | G2 (b): label-free displacement error within +10% of the displacement-supervised transformer's at 1,024 labels, and relative energy-gap advantage ≥ 40% at every budget | −36.3%; 99.95% / 99.85% / 98.86% / 99.97% | met |
|  | G2 (c): finer mesh, zero-shot displacement error ≤ 1.25 times in-band, and better than both naive baselines | 8.62 times; best naive 0.401 against 0.258 | not met |
|  | Gate G2 = (a) and ((b) or (c)), amended |  | GO |
|  | Gate G2, registered form (reference) |  | NO-GO |
|  | KP4: finer mesh, zero-shot displacement error > 1.5 times in-band, or a naive baseline better | 8.62 times | triggered |
| Two-dimensional comparison, 9 October 2026 | H1: label-free transformer lower than the displacement-supervised transformer ($\mathcal{L}_D$) in relative energy gap beyond the noise guard, 1,024 labels | −71.3% (guard 12.4%) | supported |
|  | H2a: energy-norm-supervised transformer ($\mathcal{L}_K$) lower than the displacement-supervised transformer ($\mathcal{L}_D$) in relative energy gap beyond the guard | −78.2% (guard 16.4%) | supported |
|  | H2b: energy-norm-supervised transformer lower than the displacement-supervised transformer in von Mises error beyond the guard | −54.9% (guard 12.3%) | supported |
|  | H3 (a reading, no criterion): energy-norm-supervised transformer against the label-free transformer in relative energy gap | −24.2% (guard 38.1%) | no difference shown |
| Three-dimensional energy-norm run, 25 October 2026 | H2a-3D: energy-norm-supervised transformer ($\mathcal{L}_K$) lower than the displacement-supervised transformer ($\mathcal{L}_D$) in relative energy gap beyond the noise guard, on the seeds' medians | −98.2% (guard 11.7%) | supported |
|  | H2b-3D: the same in von Mises error | −83.6% (guard 10.0%) | supported |
|  | H3-3D (a reading without a criterion): energy-norm-supervised transformer against the label-free transformer in relative energy gap, on the seeds' medians | −41.0% (guard 27.0%) | energy-norm-supervised transformer lower |

- The criteria are those of the pre-registration documents, which number their own; the runs are those of \cref{sec:methods:prereg}. Gates decide whether a study proceeds to its next stage, kill conditions withdraw a claim when triggered. G2 (a) is a sanity check of the supervised side, (b) the accuracy of the label-free network and (c) its transfer to the finer mesh; the amendment of the three-dimensional gate, written after the initial run, assessed (a) from 64 labels only; its naive baselines are the nearest-neighbour field and the scaled polynomial of \cref{sec:methods:networks}. The holdout evaluation's claims are in \cref{tab:holdout}. Supplementary Section~\SuppPrereg{} lists every criterion of every run with its notes, and the departures from the plans.
- Noise guard: a comparison of a network A with a reference B over three seeds each, with rel = mean(A)/mean(B) − 1 and SE_rel = $(s_A^2/3 + s_B^2/3)^{1/2}$ divided by mean(B), where $s_A$ and $s_B$ are the sample standard deviations over the seeds, finds A lower beyond the guard when rel is below minus the guard, max(10%, 2 SE_rel), and higher beyond it when rel exceeds the guard; within it no difference is shown, which is not equivalence. The three-dimensional energy-norm run applies it to each seed's median over the instances. $\mathcal{L}_D$ and $\mathcal{L}_K$ are the losses \eqref{eq:ld} and \eqref{eq:lk}.

### Every pre-registered criterion of the runs reported here, with its outcome.

| Run | Criterion | Measured | Outcome |
|---|---|---|---|
| July run (2D), 16 July 2026 | G1′ (a), energy-term sub-experiment (separately trained networks): supervised + energy term at least 3 times better than the zero field in displacement, and better than the two naive baselines and the plain polynomial, fitted on 1,024 labelled instances, at every budget | 4.5–6.1 times; baselines beaten at every budget | met |
|  | G1′ (b), \cref{tab:2djuly,tab:labeleffjuly}, 64 labels: the energy term lowers the relative energy gap by ≥ 50% and the von Mises error by ≥ 25% | 78.7%, 65.4% | met |
|  | G1′ (c), \cref{tab:2djuly,tab:labeleffjuly}, 64 labels: label-free, then supervised beats supervised by ≥ 10% in relative energy gap or ≥ 5% in displacement | 92.6%, 2.0% | met |
|  | Gate G1′ = (a) and (b) and (c) |  | GO |
|  | K1, energy-term sub-experiment: the better of the fixed and the gradient-scaled energy term lowers the relative energy gap by < 25% at every budget | 98.0% / 94.4% / 90.6% / 74.0% | not triggered |
|  | K2, \cref{tab:2djuly}: label-free displacement error > 30% above supervised, 1,024 labels | +3.6% | not triggered |
|  | C1-advantage, \cref{tab:labeleffjuly}: label-free relative energy-gap advantage over supervised < 40% at every budget | 98.7% / 97.0% / 93.5% / 80.4% | not triggered |
|  | K4: a latent-space regulariser raises the standardised effective rank of the latent vectors by ≤ 1.5 times | 1.70 times | not triggered |
|  | K5: conjugate gradients from the prediction of a label-free network (64 validation instances) save < 20% of the iterations from zero | −0.9% | triggered |
|  | K6: a cross-resolution invariance term shrinks the transfer gap by < 10% at coarsening 2.5 | −23.7% | triggered |
|  | E6 (alignment): within-geometry rank correlation of latent and solution distances < 0.3 | 0.730 | not triggered |
|  | C5: any pre-registered check of the conditioning bound, the modewise identity or the conjugate-gradient bound violated | none | not triggered |
| Joint-embedding run (2D), 31 July 2026 | K3: a self-supervised joint-embedding term added to label-free pretraining changes the displacement error and the relative energy gap of the transformer, fine-tuned with 16, 64 and 256 labels, by less than 3% at every budget (if triggered, the term is dropped) | change with the term, 16 / 64 / 256 labels: displacement −13.5% / −0.5% / +2.6%; relative energy gap −48.4% / +92.5% / −16.4% (positive: more accurate) | not triggered |
| Initial three-dimensional run, 21 September 2026 | Gate G2 and kill conditions as registered; the label-free objective was defective (deviation D14) | (a), (b), (c) not met; KP1, KP2, KP4 triggered | NO-GO |
| Pilot of the amendment (3D), 22 September 2026 | Label-free displacement error after 20 epochs < 0.90 | 0.309 | met |
| Three-dimensional comparison, 28 September 2026 | G2 (a), budgets ≥ 64 (amendment), \cref{tab:labeleff}: displacement-supervised transformer with the energy term at least 3 times better than the zero field in displacement, and better than both naive baselines | 3.9 / 12.0 / 21.3 times; naive beaten | met |
|  | G2 (a), every budget (the registered form, reported for reference) | 2.71 times at 16 labels | not met |
|  | G2 (b), \cref{tab:labeleff,tab:3d}: label-free displacement error within +10% of the displacement-supervised transformer's at 1,024 labels, and relative energy-gap advantage ≥ 40% at every budget | −36.3%; 99.95% / 99.85% / 98.86% / 99.97% | met |
|  | G2 (c), \cref{tab:transfer}: finer mesh, zero-shot displacement error ≤ 1.25 times in-band, and better than both naive baselines | 8.62 times; best naive 0.401 against 0.258 | not met |
|  | Gate G2 = (a) and ((b) or (c)), amended |  | GO |
|  | Gate G2, registered form (reference) |  | NO-GO |
|  | KP1: supervised (1,024 labels) better than label-free by > 10% in displacement | −36.3% | not triggered |
|  | KP2: relative energy-gap advantage < 40% at any budget | minimum 98.9% | not triggered |
|  | KP3: the energy term lowers the relative energy gap by < 25% at every budget | +96.6% / +85.7% / −20.7% / +99.6% | not triggered |
|  | KP4: finer mesh, zero-shot displacement error > 1.5 times in-band, or a naive baseline better | 8.62 times | triggered |
|  | KP5: any pre-registered check of the conditioning bound, the modewise identity or the conjugate-gradient bound violated | none | not triggered |
|  | KP6 (alignment): within-geometry rank correlation of latent and solution distances < 0.3 | 0.827 | not triggered |
| Latent-\hspace{0pt}regularisation run (2D), 29 September 2026 | Latent regularisation, K1: relative change of the displacement error or of the relative energy gap beyond the noise guard | within the guard | not triggered |
|  | Latent regularisation, K2: the separation does not rise in any seed | rose in every seed | not triggered |
|  | Latent regularisation, GO: separation raised by ≥ 0.02 in every seed | +0.009 / +0.014 / +0.002 | NO-GO |
| Bottleneck run (3D), 30 September 2026 | Token bottleneck, M = 512, K1: in-band relative energy gap or finer-mesh displacement error worse than the label-free transformer's beyond the noise guard | +280.9% (guard 287.2%), +79.1% (guard 41.9%) | triggered |
|  | Token bottleneck, M = 512, K2: finer-mesh training step longer than 2 s | 0.049 s | not triggered |
|  | Token bottleneck, M = 512: outcome |  | dropped |
|  | Token bottleneck, M = 1,024, K1: in-band relative energy gap or finer-mesh displacement error worse than the label-free transformer's beyond the noise guard | +183.3% (guard 70.5%), +122.0% (guard 33.3%) | triggered |
|  | Token bottleneck, M = 1,024, K2: finer-mesh training step longer than 2 s | 0.047 s | not triggered |
|  | Token bottleneck, M = 1,024: outcome |  | dropped |
| Two-dimensional comparison, 9 October 2026 | H1, \cref{tab:2d,tab:cm2d}: label-free transformer lower than the displacement-supervised transformer ($\mathcal{L}_D$) in relative energy gap beyond the noise guard, 1,024 labels | −71.3% (guard 12.4%) | supported |
|  | H2a: energy-norm-supervised transformer ($\mathcal{L}_K$) lower than the displacement-supervised transformer ($\mathcal{L}_D$) in relative energy gap beyond the guard | −78.2% (guard 16.4%) | supported |
|  | H2b: energy-norm-supervised transformer lower than the displacement-supervised transformer in von Mises error beyond the guard | −54.9% (guard 12.3%) | supported |
|  | H3 (a reading, no criterion): energy-norm-supervised transformer against the label-free transformer in relative energy gap | −24.2% (guard 38.1%) | no difference shown |
|  | Reuse: the label-free networks of the latent-regularisation run reproduce that run's per-instance relative energy gaps and displacement errors (largest relative deviation at most $10^{-4}$) | largest relative deviation 0 | passed |
| Holdout evaluation, 21 October 2026 | T1 (3D): label-free transformer better than the displacement-supervised transformer on all five metrics, in each seed and in the seed mean | 20 of 20 comparisons | replicated |
|  | T2 (3D): graph network's displacement error lower than the label-free transformer's on more than 50% of the instances in each seed, and its von Mises error higher on at least 95% of the instance-seed pairs | 86.3%–95.8%; 100% | replicated |
|  | T3 (3D): each displacement-supervised network has load cases worse than the zero field, each with a positive energy and no other | 340 and 237 of 8,232 load cases | replicated |
|  | H1 (2D): label-free transformer lower than the displacement-supervised transformer ($\mathcal{L}_D$) in relative energy gap beyond the noise guard | −71.3% (guard 11.5%) | replicated |
|  | H2a (2D): energy-norm-supervised transformer ($\mathcal{L}_K$) lower than the displacement-supervised transformer in relative energy gap beyond the guard | −42.9% (guard 47.4%) | not replicated |
|  | H2b (2D): energy-norm-supervised transformer lower than the displacement-supervised transformer in von Mises error beyond the guard | −52.8% (guard 12.9%) | replicated |
|  | H2c (2D): energy-norm-supervised transformer's von Mises error less than half the displacement-supervised transformer's, rel below −50% | −52.8% | replicated |
|  | D2 (2D): label-free transformer's displacement error higher than the displacement-supervised transformer's and its other four metrics better, in each seed and in the seed mean | 20 of 20 comparisons | replicated |
|  | H3 (2D, a reading without a criterion): energy-norm-supervised transformer against the label-free transformer in relative energy gap | +99.1% (guard 160.2%) | no difference shown |
|  | V: the per-instance values of every network and metric distributed alike on the holdout and the validation instances (two-sided Mann–Whitney tests, Holm's procedure at a family-wise level of 5%) | 35 quantities, zero rejected | \hspace{0pt}representative |
| Three-dimensional energy-norm run, 25 October 2026 | H2a-3D: energy-norm-supervised transformer ($\mathcal{L}_K$) lower than the displacement-supervised transformer ($\mathcal{L}_D$) in relative energy gap beyond the noise guard, on the seeds' medians | −98.2% (guard 11.7%) | supported |
|  | H2b-3D: the same in von Mises error | −83.6% (guard 10.0%) | supported |
|  | H3-3D (a reading without a criterion): energy-norm-supervised transformer against the label-free transformer in relative energy gap, on the seeds' medians | −41.0% (guard 27.0%) | energy-norm-supervised transformer lower |

- Runs are named as in \cref{tab:runs} and dated by their records; the pilot of the amendment is the short run that the amendment required before the three-dimensional comparison (Section~\ref{app:prereg}). Labels are those of the pre-registration documents, each of which numbers its own criteria. Gates (G1′, G2) decide whether the study proceeds to its next stage. Kill conditions withdraw a claim, or abandon a component, when triggered: in two dimensions K1–K6, C1-advantage (the claimed advantage in relative energy gap), C5 (the pre-registered checks of Section~\ref{app:repro:checks}) and E6 (latent alignment); in three dimensions KP1–KP6, with KP5 the counterpart of C5. The latent-regularisation and bottleneck runs number their criteria afresh, with the meanings given here. A criterion reads the trained networks of the tables it names; the energy-term sub-experiment of the July run trained its own supervised networks with and without the energy term, with the same configuration. K4, E6 and KP6 concern latent representations, which this paper does not use. Standardised effective rank: the participation ratio of the eigenvalues of the covariance of the latent vectors, each dimension standardised. The 3D amendment, the deviations and the joint-embedding term are described below, the latent regularisation and the token bottleneck in Section~\ref{app:e1}, the July run in Section~\ref{app:july}.
- Noise guard: a comparison of a network A with a reference B over three seeds each, with rel = mean(A)/mean(B) − 1 and SE_rel = $(s_A^2/3 + s_B^2/3)^{1/2}$ divided by mean(B), where $s_A$ and $s_B$ are the sample standard deviations over the seeds, finds A lower beyond the guard when rel is below minus the guard, max(10%, 2 SE_rel), and higher beyond it when rel exceeds the guard; within it no difference is shown, which is not equivalence. The hypotheses H1–H3 of the 2D comparison use it (\cref{tab:cm2d}), and so do the latent-regularisation and bottleneck runs, with the label-free network as B (their pre-registrations call it the resolution), the holdout evaluation, and the three-dimensional energy-norm run, which applies it to each seed's median over the instances (\cref{tab:k3d}). $\mathcal{L}_D$ and $\mathcal{L}_K$ are the losses \eqref{eq:ld} and \eqref{eq:lk}.

### The pre-registered hypotheses of the two-dimensional comparison, with 1,024 labelled instances, as its adjudicator recorded them, and the readings its pre-registration required beside each.

|  | H1 | H2a | H2b | H3 |
|---|---|---|---|---|
| Network A | Label-free | Supervised, energy norm | Supervised, energy norm | Supervised, energy norm |
| Reference B | Supervised, displacement | Supervised, displacement | Supervised, displacement | Label-free |
| Metric | Relative energy gap | Relative energy gap | von Mises error | Relative energy gap |
| A, seeds 0, 1, 2 | 0.0374, 0.0405, 0.0371 | 0.0370, 0.0146, 0.0355 | 0.119, 0.0829, 0.116 | 0.0370, 0.0146, 0.0355 |
| B, seeds 0, 1, 2 | 0.132, 0.148, 0.120 | 0.132, 0.148, 0.120 | 0.232, 0.251, 0.222 | 0.0374, 0.0405, 0.0371 |
| rel | −71.3% | −78.2% | −54.9% | −24.2% |
| SE_rel | 6.2% | 8.2% | 6.1% | 19.0% |
| Guard | 12.4% | 16.4% | 12.3% | 38.1% |
| Reading | supported | supported | supported | no difference shown |
| Medians: rel (guard) | −78.7% (10.0%) | −83.3% (11.6%) | −53.6% (11.8%) | −21.4% (33.7%) |
| Welch 95% interval | −97% to −45% | −101% to −55% | −73% to −37% | −103% to +54% |
| Instance resampling 95% | −74.3% to −68.3% | −80.3% to −76.3% | −57.2% to −52.8% | −28.0% to −21.9% |

- rel, SE_rel and the noise guard as defined in the note to \cref{tab:criteria}, over the three seeds' values, each the mean over the 256 validation instances and their four load cases.
- Medians: the same reading on each seed's median over the instances instead of its mean. Welch: rel ± t × SE_rel, with t the 97.5% quantile of Student's distribution at the Welch–Satterthwaite degrees of freedom, a symmetric interval that can extend below −100%. Instance resampling: the 2.5% and 97.5% percentiles of rel over 2,000 resamplings of the 256 validation instances, the same instances drawn for both networks and every seed, the seeds kept.
- H3 is a reading without a criterion. With the roles of A and B exchanged, rel was +31.9% against a guard of 50.2%.

### Time of the label-free transformer's inference against solves of the same systems, on the same instances, with the surrogate's accuracy there.

|  | 2D | 3D | 3D, fine mesh |
|---|---|---|---|
| Instances (load cases) | 32 (128) | 32 (128) | 8 (32) |
| Nodes, median | 562 | 4,960 | 38,156 |
| Surrogate, first call | 3.2 ms | 49 ms | 2.15 s |
| Surrogate, repeated call | 2.4 ms | 49 ms | 2.16 s |
| Sparse direct solve | 3.8 ms | 1.22 s | 133 s |
| CG from the zero field | 28 ms | 1.72 s | 26.1 s |
| CG from the prediction | 29 ms | 1.71 s | 27.4 s |
| CG to the prediction's accuracy | 8.8 ms | 292 ms | 4.50 s |
| the same, after rescaling by c* | 8.7 ms | 296 ms | 5.01 s |
| Assembly of $K$, the repository's assembler | 9.5 ms | 900 ms | 8.07 s |
| Ritz projection after assembly | 1.4–2.1 ms | 34–144 ms | 0.54–1.39 s |
| CG iterations per load case | 290 / 85 | 746 / 134 | 1,456 / 241 |
| Surrogate's relative energy gap | 0.029 | 0.0085 | 0.12 |
| Surrogate's displacement error | 0.050 | 0.031 | 0.27 |
| Energy gap after rescaling by c* | 0.028 | 0.0077 | 0.065 |
| Displacement error after rescaling by c* | 0.040 | 0.014 | 0.076 |
| CG's displacement error at that accuracy | 0.049 | 0.017 | 0.16 |

- Medians over the instances (CG iterations, from the zero field / to the prediction's accuracy, and CG's displacement error: over the load cases). 2D: the first 32 validation instances of the two-dimensional comparison; 3D: the first 32 validation and 8 fine-mesh instances of the three-dimensional comparison; the label-free transformers of seed 0. Wall times per instance, all load cases together, without the assembly, which the surrogate does not need.
- Surrogate: one NVIDIA GeForce RTX 5090 with TF32, preparing the inputs and copying the prediction back included; first call after an untimed warm-up on 4 validation instances, repeated call the median of 2 further passes. Solvers: the CPU of the same machine (Xeon Platinum 8470Q, 25 CPUs, the thread environment set to 25): SuperLU, which produced the labels, and unpreconditioned conjugate gradients (CG) to a relative residual of $10^{-10}$, from the zero field or from the prediction. CG to the prediction's accuracy stops, on each load case, at the first iterate whose relative energy error is at most the prediction's: it reads the reference solution, a lower bound. The fine-mesh direct solve used up its budget of 900 s after seven of the eight instances; its median, and the ratios that use it, are over those seven.
- Ritz projection (\cref{sec:methods:ritz}), from the lowest to the highest degree ($p = 6$ to 9 in 3D, 6 and 8 in 2D), with the machine's 25 BLAS threads: the time after the assembly of $K$, which is listed apart (in 2D the assembler also builds the four load vectors), for the free block, the basis, $\Phi^{\top}K\Phi$ and $\Phi^{\top}F$, the small solve and the reconstruction.
- On the fine mesh, three of the 32 load cases had a relative energy gap above 1 (4.76, 4.77 and 22.0) and three of the eight instances a mean above 1; CG matches such a load case with no iteration. Threads: \cref{sec:cost:inference} and the supplementary material.

### The pre-registered hypotheses of the three-dimensional energy-norm run, with 1,024 labelled instances, as its adjudicator recorded them, and the readings its pre-registration required beside each.

|  | H2a-3D | H2b-3D | H3-3D |
|---|---|---|---|
| Network A | Supervised, energy norm | Supervised, energy norm | Supervised, energy norm |
| Reference B | Supervised ($\mathcal{L}_D$) | Supervised ($\mathcal{L}_D$) | Label-free |
| Metric | Relative energy gap | von Mises error | Relative energy gap |
| A, seeds 0, 1, 2 | 0.00432, 0.00448, 0.00452 | 0.0412, 0.0425, 0.0437 | 0.00432, 0.00448, 0.00452 |
| B, seeds 0, 1, 2 | 0.224, 0.256, 0.275 | 0.247, 0.254, 0.276 | 0.00932, 0.00744, 0.00581 |
| rel | −98.2% | −83.6% | −41.0% |
| SE_rel | 5.9% | 3.4% | 13.5% |
| Guard | 11.7% | 10.0% | 27.0% |
| Reading | supported | supported | A lower |
| Welch 95% interval | −123.5% to −73.0% | −98.0% to −69.2% | −98.7% to +16.7% |
| Instance resampling 95% | −98.4% to −98.1% | −84.5% to −82.7% | −43.9% to −38.4% |
| Seed means: rel (guard) | −99.98% (guard 197.9%) | −88.1% (guard 43.7%) | −44.7% (guard 29.0%) |
| Seed means: Welch 95% | −526% to +326% | −182% to +6% | −106% to +16% |
| Holdout: rel (guard) | −98.0% (guard 12.6%) | −83.0% (guard 10.0%) | −38.0% (guard 25.6%) |
| Holdout, seed means: rel (guard) | −99.997% (guard 199.6%) | −89.0% (guard 60.2%) | −35.4% (guard 26.4%) |

- Every reading is of the seeds' values, each seed's median over the 256 validation instances (the pre-registered statistic) unless the row says seed means; rel, SE_rel and the noise guard as defined in the note to \cref{tab:criteria}. Welch: rel ± t × SE_rel at the Welch–Satterthwaite degrees of freedom, a symmetric interval that can extend below −100%. Instance resampling: the 2.5% and 97.5% percentiles of rel over 2,000 resamplings of the 256 instances, the same instances for both networks and every seed, the seeds kept, each seed's value the median of its resampled values. Holdout: the same readings on the 686 held-out instances of \cref{sec:holdout}, without a verdict.
- H3-3D is a reading without a criterion. With the roles of A and B exchanged, rel was +69.5% against a guard of 45.8%.

### The claims of the three- and two-dimensional comparisons read again on held-out instances, as the adjudicator of the holdout evaluation recorded them, beside their values on the validation instances.

| Claim | Statement | Validation | Holdout | Outcome |
|---|---|---|---|---|
| T1 (3D) | Label-free transformer better than the displacement-supervised transformer on all five metrics, each seed and the seed mean | 20 of 20 | 20 of 20 | replicated |
| T2 (3D) | Graph network: lower displacement error than the label-free transformer on most instances, each seed; higher von Mises error on at least 95% of the pairs | 84.4%–92.6%; 99.9% | 86.3%–95.8%; 100% | replicated |
| T3 (3D) | Load cases worse than the zero field, displacement-supervised transformer and graph network, each with a positive energy | 126 and 106 of 3,072 | 340 and 237 of 8,232 | replicated |
| H1 (2D) | Label-free below the displacement-supervised transformer in relative energy gap, beyond the guard | −71.3% (guard 12.4%) | −71.3% (guard 11.5%) | replicated |
| H2a (2D) | Energy-norm-supervised below the displacement-supervised transformer in relative energy gap, beyond the guard | −78.2% (guard 16.4%) | −42.9% (guard 47.4%) | \hspace{0pt}not replicated |
| H2b (2D) | The same in von Mises error | −54.9% (guard 12.3%) | −52.8% (guard 12.9%) | replicated |
| H2c (2D) | The same, by more than half | −54.9% | −52.8% | replicated |
| D2 (2D) | Label-free transformer: higher displacement error than the displacement-supervised one, lower errors on the other four metrics, each seed and the seed mean | 20 of 20 | 20 of 20 | replicated |
| H3 (2D) | A reading: energy-norm-supervised against label-free transformer, relative energy gap | −24.2% (guard 38.1%) | +99.1% (guard 160.2%) | no difference shown |
| V | Per-instance values alike on the holdout and validation instances, 35 quantities | – | none rejected | \hspace{0pt}representative |

- Validation: the values of \cref{sec:norm,sec:labelfree,sec:checks} on the validation instances (T3 per load case). Holdout: the same stored networks on 686 (3D) and 4,111 (2D) held-out instances. T1 and D2: the comparisons that hold, five metrics in three seeds and the seed mean; T2: the lowest and highest share over the seeds, and the share of the instance-seed pairs; H1 to H3: rel and the noise guard of the note to \cref{tab:claims}; H2c: the rel of H2b, against −50%. V: per network and metric, a two-sided Mann–Whitney test of the holdout against the validation instances, the 35 p-values taken together by Holm's procedure at a family-wise level of 5% (supplementary Section~\SuppPrereg).

### Holdout evaluation: the mean and the median of every network and metric on the validation and on the held-out instances.

| Network | Metric | Validation: mean / median | Holdout: mean / median | Ratio of the means (95%) |
|---|---|---|---|---|
| Three dimensions, 686 held-out instances |
| Label-free | Displacement | 0.0300 / 0.0280 | 0.0285 / 0.0269 | 0.95 (0.93–0.98) |
|  | Energy gap | 0.00912 / 0.00758 | 0.00805 / 0.00739 | 0.88 (0.86–0.91) |
|  | von Mises | 0.0554 / 0.0532 | 0.0541 / 0.0521 | 0.98 (0.96–0.99) |
|  | Peak stress | 0.0807 / 0.0788 | 0.0799 / 0.0775 | 0.99 (0.97–1.01) |
|  | Recall | 0.793 / 0.790 | 0.790 / 0.787 | 1.00 (0.99–1.00) |
| Supervised, displacement | Displacement | 0.0470 / 0.0408 | 0.0493 / 0.0419 | 1.05 (0.98–1.16) |
|  | Energy gap | 31.2 / 0.255 | 172 / 0.231 | 5.50 (0.01–16.49) |
|  | von Mises | 0.370 / 0.259 | 0.408 / 0.253 | 1.10 (0.75–1.80) |
|  | Peak stress | 0.784 / 0.235 | 0.646 / 0.209 | 0.82 (0.37–1.71) |
|  | Recall | 0.619 / 0.629 | 0.623 / 0.635 | 1.01 (1.00–1.01) |
| Graph network | Displacement | 0.0168 / 0.0137 | 0.0160 / 0.0142 | 0.95 (0.91–1.01) |
|  | Energy gap | 0.447 / 0.209 | 0.307 / 0.197 | 0.69 (0.59–0.84) |
|  | von Mises | 0.296 / 0.252 | 0.276 / 0.242 | 0.93 (0.90–0.97) |
|  | Peak stress | 0.488 / 0.186 | 0.353 / 0.172 | 0.72 (0.63–0.82) |
|  | Recall | 0.679 / 0.700 | 0.683 / 0.702 | 1.01 (1.00–1.01) |
| Two dimensions, 4,111 held-out instances |
| Label-free | Displacement | 0.0634 / 0.0472 | 0.0646 / 0.0477 | 1.02 (0.99–1.05) |
|  | Energy gap | 0.0383 / 0.0253 | 0.0393 / 0.0284 | 1.02 (0.99–1.06) |
|  | von Mises | 0.123 / 0.120 | 0.124 / 0.124 | 1.01 (0.99–1.03) |
|  | Peak stress | 0.128 / 0.138 | 0.129 / 0.140 | 1.01 (0.99–1.03) |
|  | Recall | 0.753 / 0.753 | 0.751 / 0.752 | 1.00 (0.99–1.00) |
| Supervised, displacement | Displacement | 0.0505 / 0.0406 | 0.0519 / 0.0410 | 1.03 (1.00–1.05) |
|  | Energy gap | 0.133 / 0.118 | 0.137 / 0.119 | 1.02 (0.99–1.07) |
|  | von Mises | 0.235 / 0.231 | 0.236 / 0.231 | 1.00 (0.99–1.01) |
|  | Peak stress | 0.141 / 0.147 | 0.145 / 0.147 | 1.03 (1.01–1.05) |
|  | Recall | 0.668 / 0.675 | 0.669 / 0.677 | 1.00 (1.00–1.00) |
| Supervised, energy norm | Displacement | 0.0547 / 0.0420 | 0.0567 / 0.0419 | 1.04 (1.01–1.07) |
|  | Energy gap | 0.0290 / 0.0210 | 0.0781 / 0.0223 | 2.69 (1.12–4.64) |
|  | von Mises | 0.106 / 0.108 | 0.111 / 0.109 | 1.05 (1.02–1.08) |
|  | Peak stress | 0.0947 / 0.100 | 0.105 / 0.101 | 1.11 (1.02–1.24) |
|  | Recall | 0.804 / 0.802 | 0.802 / 0.803 | 1.00 (1.00–1.00) |
| Graph network | Displacement | 0.0499 / 0.0392 | 0.0496 / 0.0383 | 1.00 (0.97–1.02) |
|  | Energy gap | 0.825 / 0.517 | 0.793 / 0.554 | 0.96 (0.92–1.00) |
|  | von Mises | 0.578 / 0.489 | 0.567 / 0.504 | 0.98 (0.96–1.00) |
|  | Peak stress | 0.321 / 0.153 | 0.320 / 0.159 | 1.00 (0.95–1.05) |
|  | Recall | 0.517 / 0.549 | 0.520 / 0.544 | 1.01 (1.00–1.01) |

- Per network and metric, the mean and the median over the instances of each instance's value averaged over the seeds; the validation values recomputed by the holdout evaluation, whose check of the reports' displacement errors and relative energy gaps they passed (the graph networks' to within $2 \times 10^{-4}$ in the median). Ratio: holdout mean over validation mean, with a 95% percentile interval from 2,000 resamplings of the holdout instances. V's two-sided Mann–Whitney tests compare the per-instance values; Holm's procedure rejected none of their p-values, which the evaluation's verdict records, at a family-wise level of 5%. The energy-norm-supervised transformer was evaluated in 2D only: its 3D counterpart was trained after this evaluation (\cref{sec:norm:three}).

### The Ritz projection paired with the networks and baselines: the share of the instances on which the projection was the more accurate, per set and degree $p$.

| Set | Model | $p$ | Displacement error | Relative energy gap | von Mises error | Peak stress error | Critical-region recall |
|---|---|---|---|---|---|---|---|
| 3D, validation | Label-free | 6 | 67%–79% | 0.4%–6% | 1%–8% | 0%–1% | 48%–71% |
|  |  | 7 | 91%–98% | 3%–25% | 14%–31% | 0%–1% | 81%–96% |
|  |  | 8 | 98%–99% | 11%–73% | 37%–67% | 0%–1% | 95%–99.6% |
|  |  | 9 | 99.6%–100% | 38%–100% | 69%–98% | 0%–2% | 99.6%–100% |
|  | Supervised, displacement | 6 | 93%–94% | 100% | 100% | 31%–37% | 100% |
|  |  | 7 | 99.6%–100% | 100% | 100% | 36%–42% | 100% |
|  |  | 8 | 100% | 100% | 100% | 41%–46% | 100% |
|  |  | 9 | 100% | 100% | 100% | 47%–51% | 100% |
|  | Supervised, displacement + energy term | 6 | 81%–100% | 100% | 95%–100% | 0.4% | 93%–95% |
|  |  | 7 | 97%–100% | 100% | 100% | 0.4% | 99%–99.6% |
|  |  | 8 | 100% | 100% | 100% | 1%–2% | 100% |
|  |  | 9 | 100% | 100% | 100% | 2% | 100% |
|  | Supervised, energy norm | 6 | 43%–57% | 0%–1% | 0%–2% | 0% | 23%–25% |
|  |  | 7 | 78%–85% | 0%–1% | 4%–7% | 0% | 51%–54% |
|  |  | 8 | 94%–96% | 1%–4% | 13%–19% | 0% | 61%–65% |
|  |  | 9 | 98%–99% | 6%–10% | 28%–43% | 0% | 74%–80% |
|  | Graph network, displacement | 6 | 16%–19% | 100% | 100% | 30%–35% | 99.6%–100% |
|  |  | 7 | 56%–62% | 100% | 100% | 32%–39% | 100% |
|  |  | 8 | 90%–93% | 100% | 100% | 35%–43% | 100% |
|  |  | 9 | 99% | 100% | 100% | 38%–48% | 100% |
|  | Token bottleneck, M = 512 | 6 | 98%–100% | 39%–99% | 52%–98% | 1%–12% | 85%–95% |
|  |  | 7 | 100% | 80%–100% | 88%–100% | 2%–19% | 99.6%–100% |
|  |  | 8 | 100% | 99.6%–100% | 99%–100% | 3%–25% | 100% |
|  |  | 9 | 100% | 100% | 100% | 4%–32% | 100% |
|  | Token bottleneck, M = 1,024 | 6 | 99%–100% | 49%–78% | 58%–77% | 1%–2% | 80%–89% |
|  |  | 7 | 100% | 86%–99.6% | 90%–98% | 1%–3% | 99%–100% |
|  |  | 8 | 100% | 99%–100% | 98%–100% | 1%–5% | 100% |
|  |  | 9 | 100% | 100% | 100% | 2%–8% | 100% |
|  | Nearest-neighbour field | 6 | 100% | 100% | 100% | 90% | 93% |
|  |  | 7 | 100% | 100% | 100% | 93% | 96% |
|  |  | 8 | 100% | 100% | 100% | 96% | 98% |
|  |  | 9 | 100% | 100% | 100% | 97% | 98% |
|  | Scaled polynomial | 6 | 100% | 100% | 100% | 100% | 100% |
|  |  | 7 | 100% | 100% | 100% | 100% | 100% |
|  |  | 8 | 100% | 100% | 100% | 100% | 100% |
|  |  | 9 | 100% | 100% | 100% | 100% | 100% |
|  | Zero field | 6 | 100% | 100% | 100% | 100% | 100% |
|  |  | 7 | 100% | 100% | 100% | 100% | 100% |
|  |  | 8 | 100% | 100% | 100% | 100% | 100% |
|  |  | 9 | 100% | 100% | 100% | 100% | 100% |
| 3D, finer mesh | Label-free, zero-shot | 6 | 100% | 99.6%–100% | 100% | 8%–19% | 92%–96% |
|  |  | 7 | 100% | 100% | 100% | 9%–20% | 99%–100% |
|  |  | 8 | 100% | 100% | 100% | 12%–20% | 100% |
|  |  | 9 | 100% | 100% | 100% | 14%–21% | 100% |
|  | Supervised, displacement, zero-shot | 6 | 100% | 100% | 100% | 82%–97% | 100% |
|  |  | 7 | 100% | 100% | 100% | 87%–98% | 100% |
|  |  | 8 | 100% | 100% | 100% | 91%–99% | 100% |
|  |  | 9 | 100% | 100% | 100% | 96%–99% | 100% |
|  | Graph network, displacement, zero-shot | 6 | 100% | 100% | 100% | 100% | 100% |
|  |  | 7 | 100% | 100% | 100% | 100% | 100% |
|  |  | 8 | 100% | 100% | 100% | 100% | 100% |
|  |  | 9 | 100% | 100% | 100% | 100% | 100% |
|  | Nearest-neighbour field | 6 | 100% | 100% | 100% | 100% | 100% |
|  |  | 7 | 100% | 100% | 100% | 100% | 100% |
|  |  | 8 | 100% | 100% | 100% | 100% | 100% |
|  |  | 9 | 100% | 100% | 100% | 100% | 100% |
|  | Scaled polynomial | 6 | 100% | 100% | 100% | 100% | 100% |
|  |  | 7 | 100% | 100% | 100% | 100% | 100% |
|  |  | 8 | 100% | 100% | 100% | 100% | 100% |
|  |  | 9 | 100% | 100% | 100% | 100% | 100% |
|  | Label-free, then fine-mesh labels, 16 labels | 6 | 95%–96% | 100% | 99.6%–100% | 16%–43% | 95%–96% |
|  |  | 7 | 99%–100% | 100% | 100% | 23%–53% | 99%–100% |
|  |  | 8 | 100% | 100% | 100% | 26%–63% | 100% |
|  |  | 9 | 100% | 100% | 100% | 34%–73% | 100% |
|  | Supervised from scratch, fine-mesh labels, 16 labels | 6 | 100% | 100% | 100% | 100% | 100% |
|  |  | 7 | 100% | 100% | 100% | 100% | 100% |
|  |  | 8 | 100% | 100% | 100% | 100% | 100% |
|  |  | 9 | 100% | 100% | 100% | 100% | 100% |
|  | Label-free, then fine-mesh labels, 64 labels | 6 | 66%–72% | 100% | 80%–99.6% | 2%–17% | 89%–96% |
|  |  | 7 | 90%–95% | 100% | 100% | 4%–23% | 98%–100% |
|  |  | 8 | 98%–99.6% | 100% | 100% | 5%–28% | 99%–100% |
|  |  | 9 | 100% | 100% | 100% | 9%–38% | 100% |
|  | Supervised from scratch, fine-mesh labels, 64 labels | 6 | 100% | 100% | 100% | 100% | 100% |
|  |  | 7 | 100% | 100% | 100% | 100% | 100% |
|  |  | 8 | 100% | 100% | 100% | 100% | 100% |
|  |  | 9 | 100% | 100% | 100% | 100% | 100% |
|  | Token bottleneck, M = 512, zero-shot | 6 | 100% | 100% | 100% | 38%–61% | 99%–99.6% |
|  |  | 7 | 100% | 100% | 100% | 46%–74% | 100% |
|  |  | 8 | 100% | 100% | 100% | 59%–80% | 100% |
|  |  | 9 | 100% | 100% | 100% | 70%–87% | 100% |
|  | Token bottleneck, M = 1,024, zero-shot | 6 | 100% | 100% | 100% | 40%–64% | 98%–99% |
|  |  | 7 | 100% | 100% | 100% | 59%–68% | 100% |
|  |  | 8 | 100% | 100% | 100% | 75%–83% | 100% |
|  |  | 9 | 100% | 100% | 100% | 80%–93% | 100% |
| 3D, holdout | Label-free | 6 | 67%–81% | 1%–3% | 1%–4% | 0%–0.1% | 56%–79% |
|  |  | 7 | 91%–97% | 2%–21% | 12%–28% | 0%–0.1% | 84%–95% |
|  |  | 8 | 98%–99.9% | 12%–71% | 32%–69% | 0%–0.3% | 96%–99% |
|  |  | 9 | 99.6%–100% | 34%–99.9% | 67%–96% | 0%–1% | 99.7%–100% |
|  | Supervised, displacement | 6 | 92%–95% | 100% | 100% | 26%–32% | 100% |
|  |  | 7 | 99%–99.6% | 100% | 100% | 32%–35% | 100% |
|  |  | 8 | 99.9%–100% | 100% | 100% | 36%–40% | 100% |
|  |  | 9 | 100% | 100% | 100% | 44%–46% | 100% |
|  | Graph network, displacement | 6 | 16%–20% | 100% | 100% | 26%–32% | 99%–99.9% |
|  |  | 7 | 62%–68% | 100% | 100% | 29%–36% | 100% |
|  |  | 8 | 92%–95% | 100% | 100% | 33%–39% | 100% |
|  |  | 9 | 99.6%–99.7% | 100% | 100% | 36%–45% | 100% |
|  | Supervised, energy norm | 6 | 45%–58% | 0.1%–1% | 1%–2% | 0%–0.1% | 27%–28% |
|  |  | 7 | 82%–88% | 1%–2% | 3%–7% | 0%–0.3% | 52%–55% |
|  |  | 8 | 94%–97% | 2%–4% | 11%–17% | 0%–0.3% | 63%–67% |
|  |  | 9 | 98%–99% | 6%–12% | 31%–44% | 0%–0.3% | 77%–84% |
| 2D, validation | Label-free | 6 | 80%–84% | 16%–20% | 47%–53% | 0%–0.4% | 95%–96% |
|  |  | 8 | 96%–97% | 61%–66% | 82%–86% | 2%–3% | 98%–99% |
|  | Supervised, displacement | 6 | 58%–67% | 100% | 100% | 0.4%–4% | 100% |
|  |  | 8 | 76%–78% | 100% | 100% | 2%–8% | 100% |
|  | Supervised, energy norm | 6 | 44%–73% | 0.4%–15% | 2%–45% | 0% | 24%–89% |
|  |  | 8 | 64%–96% | 2%–55% | 7%–74% | 0%–2% | 33%–98% |
|  | Graph network, displacement | 6 | 57%–61% | 100% | 100% | 29%–32% | 99.6%–100% |
|  |  | 8 | 74%–75% | 100% | 100% | 36%–41% | 100% |
|  | Nearest-neighbour field | 6 | 100% | 100% | 100% | 84% | 96% |
|  |  | 8 | 100% | 100% | 100% | 92% | 96% |
|  | Scaled polynomial | 6 | 100% | 100% | 100% | 100% | 100% |
|  |  | 8 | 100% | 100% | 100% | 100% | 100% |
|  | Zero field | 6 | 100% | 100% | 100% | 100% | 100% |
|  |  | 8 | 100% | 100% | 100% | 100% | 100% |
| 2D, holdout | Label-free | 6 | 79%–84% | 17%–19% | 49%–53% | 0.1%–0.2% | 94%–96% |
|  |  | 8 | 94%–95% | 62%–66% | 81%–85% | 4% | 99% |
|  | Supervised, displacement | 6 | 56%–63% | 100% | 100% | 1%–3% | 99.98%–100% |
|  |  | 8 | 73%–77% | 100% | 100% | 4%–8% | 99.98%–100% |
|  | Supervised, energy norm | 6 | 41%–72% | 0.4%–16% | 2%–46% | 0.1%–0.4% | 21%–87% |
|  |  | 8 | 63%–94% | 2%–59% | 8%–73% | 0.2%–4% | 33%–97% |
|  | Graph network, displacement | 6 | 55%–57% | 100% | 100% | 29%–33% | 99.9%–100% |
|  |  | 8 | 71%–72% | 100% | 100% | 37%–42% | 99.98%–100% |

- The share of the instances on which the Ritz projection was strictly the more accurate than the model, for each seed of a trained network (the lowest and the highest over the three seeds; one value when they agree), and for the deterministic baselines. Higher is better in critical-region recall, lower in every other metric; ties, which occur only in critical-region recall, are counted with neither. A share strictly between 0% and 100% is never shown as either. Networks at 1,024 labelled instances; on the finer mesh the networks trained in-band are applied zero-shot and the few-shot networks are those of the transfer comparison. The shares for every other network and budget of the summaries are in the records.

### Three-dimensional energy-norm run: every metric of the three transformers on the 256 validation instances, the seeds' medians and the seeds' means over the instances (mean ± sample standard deviation over the three seeds).

| Network | Statistic | Displacement error | Relative energy gap | von Mises error | Peak stress error | Critical-region recall |
|---|---|---|---|---|---|---|
| Label-free | seed medians | 0.0271 ± 0.0022 | 0.00752 ± 0.00176 | 0.0527 ± 0.0040 | 0.0785 ± 0.0149 | 0.790 ± 0.023 |
|  | seed means | 0.0300 ± 0.0028 | 0.00912 ± 0.00228 | 0.0554 ± 0.0045 | 0.0807 ± 0.0134 | 0.793 ± 0.022 |
| Supervised ($\mathcal{L}_D$) | seed medians | 0.0415 ± 0.0026 | 0.251 ± 0.026 | 0.259 ± 0.015 | 0.222 ± 0.014 | 0.628 ± 0.009 |
|  | seed means | 0.0470 ± 0.0038 | 31.2 ± 53.5 | 0.370 ± 0.140 | 0.784 ± 0.807 | 0.619 ± 0.005 |
| Supervised, energy norm | seed medians | 0.0203 ± 0.0019 | 0.00444 ± 0.00010 | 0.0425 ± 0.0013 | 0.0379 ± 0.0008 | 0.858 ± 0.001 |
|  | seed means | 0.0227 ± 0.0022 | 0.00504 ± 0.00022 | 0.0440 ± 0.0014 | 0.0386 ± 0.0011 | 0.858 ± 0.001 |


### Three-dimensional energy-norm run: the 30 secondary comparisons, exploratory, each with the noise guard, on the seeds' medians and on the seeds' means.

| Comparison (A against B) | Metric | Medians: rel (guard) | Reading | Seed means: rel (guard) | Reading |
|---|---|---|---|---|---|
| Energy norm against displacement ($\mathcal{L}_D$) | Displacement error | −51.1% (guard 10.0%) | A better | −51.8% (guard 10.8%) | A better |
|  | Relative energy gap | −98.2% (guard 11.7%) | A better | −99.98% (guard 197.9%) | within |
|  | von Mises error | −83.6% (guard 10.0%) | A better | −88.1% (guard 43.7%) | A better |
|  | Peak stress error | −82.9% (guard 10.0%) | A better | −95.1% (guard 118.9%) | within |
|  | Critical-region recall | +36.7% (guard 10.0%) | A better | +38.6% (guard 10.0%) | A better |
| Energy norm against label-free | Displacement error | −25.0% (guard 12.3%) | A better | −24.3% (guard 13.7%) | A better |
|  | Relative energy gap | −41.0% (guard 27.0%) | A better | −44.7% (guard 29.0%) | A better |
|  | von Mises error | −19.4% (guard 10.0%) | A better | −20.6% (guard 10.0%) | A better |
|  | Peak stress error | −51.7% (guard 22.0%) | A better | −52.1% (guard 19.2%) | A better |
|  | Critical-region recall | +8.7% (guard 10.0%) | within | +8.1% (guard 10.0%) | within |
| Label-free against supervised ($\mathcal{L}_D$) | Displacement error | −34.7% (guard 10.0%) | A better | −36.3% (guard 11.6%) | A better |
|  | Relative energy gap | −97.0% (guard 11.8%) | A better | −99.97% (guard 197.9%) | within |
|  | von Mises error | −79.6% (guard 10.0%) | A better | −85.0% (guard 43.7%) | A better |
|  | Peak stress error | −64.6% (guard 10.6%) | A better | −89.7% (guard 118.9%) | within |
|  | Critical-region recall | +25.8% (guard 10.0%) | A better | +28.2% (guard 10.0%) | A better |


## In-text numbers

- `numAmpFineCstar`: 1.23
- `numAmpFineDisp`: 0.258
- `numAmpFineDispC`: 0.0832
- `numAmpFineGapMedian`: 0.0911
- `numAmpFineGapMedianC`: 0.0418
- `numAmpFineRedMax`: 69%
- `numAmpFineRedMin`: 66%
- `numAmpIdentity`: $2 \times 10^{-12}$
- `numAmpInCstar`: 1.00
- `numAmpInDisp`: 0.0300
- `numAmpInDispC`: 0.0142
- `numAmpInGap`: 0.00912
- `numAmpInGapC`: 0.00740
- `numAmpRatioBoth`: 5.9
- `numAmpRatioFineOnly`: 2.8
- `numAmpRows`: 4,608
- `numAuditItems`: 22 of 22
- `numChebThree`: 0.055
- `numChebTwo`: 0.043
- `numCmAdvMax`: 99.8%
- `numCmAdvMin`: 71.3%
- `numCmDispSpread`: 1.27
- `numCmFreeDisp`: 0.0634
- `numCmFreeDispExcessAbs`: 25.6%
- `numCmFreeDispExcessMax`: 37%
- `numCmFreeDispExcessMin`: 15%
- `numCmFreeDispFour`: 0.0634
- `numCmFreeGap`: 0.0383
- `numCmFreeGapMedian`: 0.0251
- `numCmFreeGapSeeds`: 0.0374, 0.0405 and 0.0371
- `numCmFreePeak`: 0.128
- `numCmFreeRecall`: 0.753
- `numCmFreeVm`: 0.123
- `numCmFreeWorse`: 0
- `numCmKnormDisp`: 0.0547
- `numCmKnormGap`: 0.0290
- `numCmKnormGapMedian`: 0.0172
- `numCmKnormGapSeeds`: 0.0370, 0.0146 and 0.0355
- `numCmKnormPeak`: 0.0947
- `numCmKnormRecall`: 0.804
- `numCmKnormVm`: 0.106
- `numCmKnormWorse`: 0
- `numCmKnormWorseSixteen`: 11
- `numCmKnormWorseSixtyFour`: 1
- `numCmKnormWorseTwoFiveSix`: 0
- `numCmLabDisp`: 0.0505
- `numCmLabDispFour`: 0.0505
- `numCmLabGap`: 0.133
- `numCmLabGapMedian`: 0.117
- `numCmLabGapSixteen`: 20.8
- `numCmLabOverFreeGap`: 3.5
- `numCmLabOverFreeGapRoot`: 1.9
- `numCmLabOverFreeVm`: 1.9
- `numCmLabOverKnormGap`: 4.60
- `numCmLabPeak`: 0.141
- `numCmLabRecall`: 0.668
- `numCmLabVm`: 0.235
- `numCmLabWorse`: 0
- `numCmLabWorseSixteen`: 768
- `numCmLabWorseSixtyFour`: 532
- `numCmLabWorseTwoFiveSix`: 53
- `numCmMgnBelowLabDisp`: 1%
- `numCmMgnDisp`: 0.0499
- `numCmMgnGap`: 0.825
- `numCmMgnGapMedian`: 0.521
- `numCmMgnOverFreeVm`: 4.7
- `numCmMgnOverLabGap`: 6.2
- `numCmMgnPeak`: 0.321
- `numCmMgnRecall`: 0.517
- `numCmMgnVm`: 0.578
- `numCmMgnWorse`: 187
- `numCmMgnWorseSixtyFour`: 766
- `numCmPairs`: 768
- `numCmSecondary`: 80
- `numCmSolves`: 5,120
- `numCmSolvesTrain`: 4,096
- `numCmSolvesVal`: 1,024
- `numCmVal`: 256
- `numCoarsenHigh`: 2.5
- `numCoarsenHighCoarse`: 0.174
- `numCoarsenHighFine`: 0.198
- `numCoarsenHighReduction`: −23.7%
- `numCoarsenHighWiden`: 23.7%
- `numCoarsenLow`: 1.8
- `numCoarsenLowCoarse`: 0.182
- `numCoarsenLowFine`: 0.189
- `numCoarsenLowReduction`: −17.6%
- `numCoarsenLowWiden`: 17.6%
- `numCondThree`: 0.012
- `numCondTwo`: 0.022
- `numCostAsmFine`: 8.07 s
- `numCostAsmOverRitzMax`: 27
- `numCostAsmOverRitzMin`: 6
- `numCostAsmVal`: 900 ms
- `numCostBreakEvenDirect`: 84,000
- `numCostBreakEvenMatch`: 400,000
- `numCostCgTol`: $10^{-10}$
- `numCostFineDirectSolved`: seven
- `numCostFineDirectTotal`: eight
- `numCostLabelMin`: 21
- `numCostRitzFineMax`: 1.39 s
- `numCostRitzFineMin`: 0.54 s
- `numCostRitzValMax`: 144 ms
- `numCostRitzValMin`: 34 ms
- `numCostSurrFine`: 2.15 s
- `numCostSurrVal`: 49 ms
- `numCostThreads`: 25
- `numCostThreeFineDirectRatio`: 64
- `numCostThreeFineGap`: 0.12
- `numCostThreeFineMatchRatio`: 1.9
- `numCostThreeValDirectRatio`: 27
- `numCostThreeValGap`: 0.0085
- `numCostThreeValMatchRatio`: 5.2
- `numCostTwoDirectRatio`: 1.2
- `numCostTwoGap`: 0.029
- `numCostTwoMatchRatio`: 2.9
- `numCostWarmFewer`: 0.3%
- `numCostWarmMore`: 2.0%
- `numCrossThree`: $7.43 \times 10^{-3}$
- `numCrossTwo`: $8.39 \times 10^{-3}$
- `numDfourteenAlpha`: $3.6 \times 10^{-4}$
- `numDfourteenDisp`: 0.99964
- `numDfourteenGap`: 0.99928
- `numDiagFixedMax`: 0.22
- `numDiagFixedMin`: 0.20
- `numDiagFixedSeeds`: six
- `numDiagScaledMax`: 0.52
- `numDiagScaledMin`: 0.22
- `numDiagSeeds`: six
- `numEOneBaseDisp`: 0.0634
- `numEOneBaseGap`: 0.0383
- `numEOneDeltaMax`: 0.014
- `numEOneDeltaMin`: 0.002
- `numEOneFloor`: 0.02
- `numEtwoFineMax`: 2.2
- `numEtwoFineMin`: 1.8
- `numEtwoGapMax`: 3.8
- `numEtwoGapMin`: 2.8
- `numEtwoNodesFine`: 41,367
- `numEtwoNodesIn`: 12,318
- `numEtwoStepMax`: 51
- `numEtwoStepMin`: 38
- `numEtwoTransformerFineStep`: 14.8
- `numFewFactorMax`: 5.7
- `numFewFactorMin`: 2.3
- `numFewSixteenDisp`: 0.0531
- `numFewSixteenGap`: 0.0702
- `numFewSixteenPeak`: 0.389
- `numFewSixteenScratchDisp`: 0.799
- `numFewSixteenVm`: 0.166
- `numFewSixtyFourDisp`: 0.0298
- `numFewSixtyFourGap`: 0.0520
- `numFewSixtyFourPeak`: 0.272
- `numFewSixtyFourScratchDisp`: 0.193
- `numFewSixtyFourVm`: 0.126
- `numFieldBoundMax`: 0.85
- `numFieldLoadWorseFree`: 1
- `numFieldLoadWorseLab`: 126
- `numFieldLoadWorseMgn`: 106
- `numFieldLoads`: 3,072
- `numFieldRqAboveLab`: 89.0%
- `numFieldRqAboveMgn`: 99.9%
- `numFieldRqFree`: 11.9
- `numFieldRqLab`: 132
- `numFieldRqMgn`: 1,026
- `numFieldVmElemFree`: 0.0508
- `numFieldVmElemLab`: 0.257
- `numFieldVmElemMgn`: 0.226
- `numFieldVmVolFree`: 0.0474
- `numFieldVmVolLab`: 0.247
- `numFieldVmVolMgn`: 0.209
- `numFigFineLoad`: downward body force
- `numFigMedianLoad`: downward body force
- `numFigTwoDDispMax`: 0.033
- `numFigTwoDDispMin`: 0.026
- `numFigTwoDGapMax`: 0.66
- `numFigTwoDGapMin`: 0.031
- `numFigTwoDLoad`: shear traction on the top edge
- `numFigWorstFreeC`: 0.78
- `numFigWorstFreeDisp`: 0.22
- `numFigWorstFreeDispC`: 0.045
- `numFigWorstLoad`: downward body force
- `numFigWorstTwiceFree`: 12%
- `numFigWorstTwiceLab`: 67%
- `numFigWorstTwiceMgn`: 52%
- `numFineFreeDisp`: 0.258
- `numFineFreeGap`: 0.306
- `numFineFreeVm`: 0.305
- `numFineKill`: 1.5
- `numFineKnnDisp`: 0.401
- `numFineLabDisp`: 0.257
- `numFineLabGap`: 0.985
- `numFineLabVm`: 0.537
- `numFineMgnDisp`: 0.459
- `numFineMgnGap`: 16.3
- `numFineMgnVm`: 2.40
- `numFineRatio`: 8.6
- `numFineWin`: 1.25
- `numGOneFtDisp`: 2.0%
- `numGOneFtGap`: 92.6%
- `numGOneGapReduction`: 78.7%
- `numGOneRetired`: 5.8%
- `numGOneSanityMax`: 6.1
- `numGOneSanityMin`: 4.5
- `numGOneSanityTableSixteen`: 2.4
- `numGOneVmReduction`: 65.4%
- `numGTwoAdvMin`: 98.9%
- `numGTwoFloor`: 64
- `numGTwoParity`: −36.3%
- `numGTwoSanityMax`: 21.3
- `numGTwoSanitySixteen`: 2.71
- `numGTwoSanitySixtyFour`: 3.9
- `numGTwoSanityX`: 3.0
- `numHOneRel`: 71.3%
- `numHOneTau`: 12.4%
- `numHThreeExRel`: 31.9%
- `numHThreeExTau`: 50.2%
- `numHThreeRel`: 24.2%
- `numHThreeResHigh`: 28.0%
- `numHThreeResLow`: 21.9%
- `numHThreeSeedRel`: 1%, 64% and 4%
- `numHThreeSeedsZeroTwo`: 2.7%
- `numHThreeTau`: 38.1%
- `numHTwoARel`: 78.2%
- `numHTwoARootRel`: 53.4%
- `numHTwoATau`: 16.4%
- `numHTwoBRel`: 54.9%
- `numHTwoBTau`: 12.3%
- `numHoldContentDev`: $2 \times 10^{-4}$
- `numHoldHOneRel`: 71.3%
- `numHoldHOneTau`: 11.5%
- `numHoldHThreeRel`: +99.1%
- `numHoldHThreeTau`: 160.2%
- `numHoldHTwoABaseSeeds`: 0.142, 0.147 and 0.121
- `numHoldHTwoAMedHold`: 0.0223
- `numHoldHTwoAMedRel`: 81.4%
- `numHoldHTwoAMedTau`: 13.4%
- `numHoldHTwoAMedVal`: 0.0210
- `numHoldHTwoANewSeeds`: 0.130, 0.0213 and 0.0834
- `numHoldHTwoARatio`: 2.69
- `numHoldHTwoARatioHigh`: 4.64
- `numHoldHTwoARatioLow`: 1.12
- `numHoldHTwoARel`: 42.9%
- `numHoldHTwoASeedZero`: 9%
- `numHoldHTwoATau`: 47.4%
- `numHoldHTwoATop`: 254
- `numHoldHTwoATopSeeds`: 254.3, 21.6 and 190.4
- `numHoldHTwoBRel`: 52.8%
- `numHoldHTwoBTau`: 12.9%
- `numHoldStates`: 21
- `numHoldTThreeLab`: 340
- `numHoldTThreeLoads`: 8,232
- `numHoldTThreeMgn`: 237
- `numHoldTTwoMax`: 95.8%
- `numHoldTTwoMin`: 86.3%
- `numHoldThreeExcl`: 34
- `numHoldThreeN`: 686
- `numHoldThreeSolves`: 2,744
- `numHoldThreeTail`: 720
- `numHoldTwoExcl`: 33
- `numHoldTwoFreeGap`: 0.0393
- `numHoldTwoKnormGap`: 0.0781
- `numHoldTwoLoads`: 49,332
- `numHoldTwoN`: 4,111
- `numHoldTwoPairs`: 12,333
- `numHoldTwoSolves`: 16,444
- `numHoldTwoTail`: 4,144
- `numHoldTwoWorseInstFree`: none
- `numHoldTwoWorseInstKnorm`: 9
- `numHoldTwoWorseInstLab`: 16
- `numHoldTwoWorseInstMgn`: 2,904
- `numHoldTwoWorseLoadFree`: 11
- `numHoldTwoWorseLoadKnorm`: 21
- `numHoldTwoWorseLoadLab`: 57
- `numHoldTwoWorseLoadMgn`: 11,399
- `numHoldVAlpha`: 5%
- `numHoldVQuantities`: 35
- `numJulyOverCmDispMax`: 3.4
- `numJulyOverCmDispMin`: 2.6
- `numKappaTauTwo`: $1.5 \times 10^{-7}$
- `numKappaThreeHigh`: $5.2 \times 10^{5}$
- `numKappaThreeLow`: $2.9 \times 10^{4}$
- `numKappaTwoHigh`: $1.5 \times 10^{5}$
- `numKappaTwoLow`: $4.8 \times 10^{3}$
- `numKdClosureGap`: 101.3%
- `numKdClosureVm`: 105.0%
- `numKdFreeDispRel`: 25.0%
- `numKdFreeGapMedian`: 0.0075
- `numKdFreeMedMax`: 0.0093
- `numKdFreeMedMin`: 0.0058
- `numKdFreePairs`: 738
- `numKdFreePeakRel`: 51.7%
- `numKdFreeRel`: 41.0%
- `numKdFreeTau`: 27.0%
- `numKdFreeVmRel`: 19.4%
- `numKdFreeWelchHigh`: +16.7%
- `numKdFreeWelchLow`: −98.7%
- `numKdGapRel`: 98.2%
- `numKdGapTau`: 11.7%
- `numKdHoldFreeRel`: 38.0%
- `numKdHoldFreeTau`: 25.6%
- `numKdHoldGapRel`: 98.0%
- `numKdHoldGapTau`: 12.6%
- `numKdHoldVmRel`: 83.0%
- `numKdHoldVmTau`: 10.0%
- `numKdKnormGapMedian`: 0.0044
- `numKdLabGapMedian`: 0.25
- `numKdMeansGapRel`: 99.98%
- `numKdMeansGapTau`: 197.9%
- `numKdMeansVmRel`: 88.1%
- `numKdMeansVmTau`: 43.7%
- `numKdMeansVmWelchHigh`: +5.8%
- `numKdMeansVmWelchLow`: −182.0%
- `numKdSecondary`: 30
- `numKdVmRel`: 83.6%
- `numKdVmTau`: 10.0%
- `numKfiveEval`: 64
- `numKfiveFiveGap`: 0.0430
- `numKfiveFree`: 242.5
- `numKfiveNaive`: 261.3
- `numKfiveNaiveSaving`: −8.7%
- `numKfiveSaving`: −0.9%
- `numKfiveStartGap`: 0.0722
- `numKfiveTol`: $10^{-6}$
- `numKfiveTwentyGap`: 0.0260
- `numKfiveZero`: 240.4
- `numKthreeBand`: 3%
- `numKthreeBaseRef`: 0.201 ± 0.033
- `numKthreeBaseSeeds`: 0.811, 6.99 and 1.66
- `numKthreeGain`: 92.5%
- `numKthreeOutside`: four
- `numKthreeWorse`: three
- `numMgnDispLowerMax`: 92.6%
- `numMgnDispLowerMin`: 84.4%
- `numMgnGapHigherMin`: 99.2%
- `numMgnLowerDispHigherVm`: 685
- `numMgnPeakLowerMax`: 29%
- `numMgnPeakLowerMin`: 17%
- `numMgnVmHigher`: 767
- `numModesPhrase`: $2 \times 10^{-15}$ in both dimensions
- `numModesThree`: $2 \times 10^{-15}$
- `numModesTwo`: $2 \times 10^{-15}$
- `numNlCmEFree`: 0.158
- `numNlCmEKnorm`: 0.139
- `numNlCmELab`: 0.344
- `numNlCmLabelE`: 1.14
- `numNlCmLabelVm`: 1.12
- `numNlCmNormE`: 2.5
- `numNlCmNormEMean`: 2.5
- `numNlCmNormVm`: 2.2
- `numNlCmNormVmMean`: 2.2
- `numNlCmVmFree`: 0.120
- `numNlCmVmKnorm`: 0.107
- `numNlCmVmLab`: 0.230
- `numNlThreeEFree`: 0.0863
- `numNlThreeEKnorm`: 0.0666
- `numNlThreeELab`: 0.501
- `numNlThreeLabelE`: 1.30
- `numNlThreeLabelVm`: 1.24
- `numNlThreeLabelWithin`: 1.3
- `numNlThreeNormE`: 7.5
- `numNlThreeNormEMean`: 10.7
- `numNlThreeNormVm`: 6.1
- `numNlThreeNormVmMean`: 8.4
- `numNlThreeNormVmWord`: six
- `numNlThreeVmFree`: 0.0527
- `numNlThreeVmKnorm`: 0.0425
- `numNlThreeVmLab`: 0.259
- `numNodesFineMax`: 71,749
- `numNodesFineMedian`: 36,216
- `numNodesFineMin`: 15,175
- `numNodesInMax`: 17,692
- `numNodesInMedian`: 5,617
- `numNodesInMin`: 2,195
- `numPairCmFreeKnormGapTwoFiveSix`: 72.4%
- `numPairCmKnormFreeDisp`: 68.1%
- `numPairCmKnormFreeGap`: 87.6%
- `numPairCmKnormFreePeak`: 84.9%
- `numPairCmKnormFreeRecall`: 74.1%
- `numPairCmKnormFreeVm`: 83.3%
- `numPairCmKnormLabDisp`: 49.7%
- `numPairCmKnormLabGap`: 99.9%
- `numPairCmKnormLabPeak`: 84.6%
- `numPairCmKnormLabRecall`: 98.6%
- `numPairCmKnormLabVm`: 99.9%
- `numPairCmLabDisp`: 29.9%
- `numPairCmLabGap`: 99.9%
- `numPairCmLabPeak`: 62.6%
- `numPairCmLabRecall`: 96.7%
- `numPairCmLabVm`: 99.9%
- `numPairCmMgnLabDisp`: 55.7%
- `numPairCmMgnLabGap`: none
- `numPairCmMgnLabPeak`: 41.0%
- `numPairCmMgnLabRecall`: 9.8%
- `numPairCmMgnLabVm`: none
- `numPairCmOpposite`: 69.9%
- `numPairThreeAncDisp`: 81.2%
- `numPairThreeAncGap`: 99.7%
- `numPairThreeAncPeak`: 75.3%
- `numPairThreeAncRecall`: 95.7%
- `numPairThreeAncVm`: 99.7%
- `numPairThreeLabDisp`: 78.9%
- `numPairThreeLabGap`: 99.9%
- `numPairThreeLabPeak`: 87.4%
- `numPairThreeLabRecall`: all
- `numPairThreeLabVm`: 99.9%
- `numPairTwoAncDisp`: 36.2%
- `numPairTwoAncGap`: 91.8%
- `numPairTwoAncPeak`: 44.8%
- `numPairTwoAncRecall`: 76.4%
- `numPairTwoAncVm`: 75.1%
- `numPairTwoLabDisp`: 39.1%
- `numPairTwoLabGap`: all
- `numPairTwoLabPeak`: 63.2%
- `numPairTwoLabRecall`: 98.8%
- `numPairTwoLabVm`: 99.3%
- `numParamsAux`: 0.6
- `numParamsGraph`: 3.9
- `numParamsTransformer`: 6.7
- `numPilotDisp`: 0.309
- `numPilotLimit`: 0.90
- `numPremiseThree`: 0.462
- `numPremiseTwo`: 0.464
- `numRemeshFine`: 1.27
- `numRemeshGeometries`: 16
- `numRemeshInDev`: 2%
- `numRerunAccDev`: $4 \times 10^{-16}$
- `numRerunCpu`: Xeon Gold 6459C
- `numRerunIters`: two
- `numRerunThreads`: 16
- `numRhoThree`: 0.827
- `numRhoTwo`: 0.730
- `numRitzFineBnPeakMax`: 62%
- `numRitzFineBnPeakMin`: 7%
- `numRitzFineFreePeakMax`: 92%
- `numRitzFineFreePeakMin`: 79%
- `numRitzFineFtPeakMax`: 98%
- `numRitzFineFtPeakMin`: 62%
- `numRitzFineGapAll`: 99.6%
- `numRitzFineGapNine`: 0.0070
- `numRitzFineGapSix`: 0.019
- `numRitzFineLabPeakMax`: 17.6%
- `numRitzHoldFreeDispNineMax`: 100%
- `numRitzHoldFreeDispNineMin`: 99.6%
- `numRitzHoldFreeDispSixMax`: 81%
- `numRitzHoldFreeDispSixMin`: 67%
- `numRitzHoldFreePeakMin`: 99.4%
- `numRitzHoldKnormGapMin`: 88%
- `numRitzHoldKnormPeakMiss`: two
- `numRitzThreeK`: 168, 252, 360 and 495
- `numRitzThreeKMax`: 495
- `numRitzTwoFreeDispMax`: 97%
- `numRitzTwoFreeDispMin`: 80%
- `numRitzTwoFreeGapEightMax`: 66%
- `numRitzTwoFreeGapEightMin`: 61%
- `numRitzTwoFreeGapSixMax`: 20%
- `numRitzTwoFreeGapSixMin`: 16%
- `numRitzTwoFreePeakMin`: 96.8%
- `numRitzTwoK`: 42 and 72
- `numRitzTwoKEight`: 72
- `numRitzTwoKSix`: 42
- `numRitzValFreeDispNineMax`: 100%
- `numRitzValFreeDispNineMin`: 99.6%
- `numRitzValFreeDispSixMax`: 79%
- `numRitzValFreeDispSixMin`: 67%
- `numRitzValFreePeakMin`: 98.4%
- `numRitzValGapNine`: 0.0063
- `numRitzValGapSix`: 0.018
- `numRitzValKnormGapMin`: 89.8%
- `numRitzValNineDispAll`: 97.6%
- `numRitzValPeakNine`: 0.23
- `numRitzValPeakRatioMax`: 4.9
- `numRitzValPeakRatioMin`: 2.4
- `numRitzValPeakSix`: 0.32
- `numSpecBoundMax`: 0.90
- `numSpecFigIndex`: 221
- `numSpecFreeMax`: 3,622
- `numSpecFreeMin`: 348
- `numSpecIeeeLabKnormGap`: 11.9
- `numSpecIeeeLabKnormRq`: 9.30
- `numSpecIeeeRqFree`: 9.12
- `numSpecIeeeRqKnorm`: 9.42
- `numSpecIeeeRqLab`: 114
- `numSpecIeeeRqMgn`: 558
- `numSpecKnormFreeAbove`: 49.1%
- `numSpecKnormFreeDisp`: 0.64
- `numSpecKnormFreeDispSeeds`: 0.81, 0.39 and 0.81
- `numSpecKnormFreeGap`: 0.66
- `numSpecKnormFreeRq`: 1.04
- `numSpecLabKnormAbove`: 94.9%
- `numSpecLabKnormAboveSeedGm`: 98.8%
- `numSpecLabKnormDisp`: 1.26
- `numSpecLabKnormDispLower`: 50.0%
- `numSpecLabKnormDispSeeds`: 0.96, 1.65 and 1.26
- `numSpecLabKnormGap`: 9.85
- `numSpecLabKnormRq`: 7.80
- `numSpecLabKnormRqSeeds`: 8.26, 9.46 and 6.07
- `numSpecLoadCases`: 1,024
- `numSpecLoadWorseFree`: 1
- `numSpecLoadWorseKnorm`: 0
- `numSpecLoadWorseLab`: 1
- `numSpecLoadWorseMgn`: 724
- `numSpecLoads`: 3,072
- `numSpecMgnLabAbove`: 93.4%
- `numSpecMgnLabDisp`: 1.00
- `numSpecMgnLabGap`: 4.34
- `numSpecMgnLabRq`: 4.33
- `numSpecRqFree`: 10.3
- `numSpecRqKnorm`: 11.3
- `numSpecRqLab`: 115
- `numSpecRqMgn`: 553
- `numSpecRqStarOverMin`: 1.27
- `numSpecShareEucFree`: 7.2%
- `numSpecShareEucKnorm`: 6.6%
- `numSpecShareEucLab`: 24%
- `numSpecShareEucMgn`: 49%
- `numSpecShareEucStar`: 0.2%
- `numSpecShareKFree`: 69%
- `numSpecShareKKnorm`: 73%
- `numSpecShareKLab`: 95%
- `numSpecShareKMgn`: 99%
- `numSpecShareKStar`: 1.5%
- `numSpecSpectralShare`: 90%
- `numSpecSpectralShareMax`: 102%
- `numSpecSpectralShareMin`: 82%
- `numSpecTfFree`: 2.7%
- `numSpecTfKnorm`: 2.9%
- `numSpecTfLab`: 0.7%
- `numSpecTfMgn`: 0.05%
- `numSpecTfStiffFree`: 41%
- `numSpecTfStiffKnorm`: 36%
- `numSpecTfStiffLoads`: 670
- `numSpecTfStiffN`: 2,010
- `numSpecVmAreaFree`: 0.105
- `numSpecVmAreaKnorm`: 0.0896
- `numSpecVmAreaLab`: 0.227
- `numSpecVmAreaMgn`: 0.462
- `numSpecVmAreaRatio`: 2.26
- `numSpecVmElemFree`: 0.112
- `numSpecVmElemKnorm`: 0.0964
- `numSpecVmElemLab`: 0.231
- `numSpecVmElemMgn`: 0.474
- `numSpecVmElemRatio`: 2.22
- `numSqrtKappaMax`: 723
- `numSqrtKappaMin`: 69
- `numTauSqKappaTwo`: $6 \times 10^{-18}$
- `numTauSquared`: $10^{-12}$
- `numThreadsCgGainMax`: 29%
- `numThreadsCgGainMin`: 16%
- `numThreadsDirectDev`: 1.1%
- `numThreadsDrift`: 2.1%
- `numThreadsFineN`: 2
- `numThreadsHost`: 25
- `numThreadsTwoCg`: 4.3%
- `numThreadsTwoDirect`: 7.2%
- `numThreadsTwoN`: 8
- `numThreadsValN`: 8
- `numThreeAncDisp`: 0.0470
- `numThreeAncGap`: 0.116
- `numThreeAncGapMedian`: 0.108
- `numThreeAncOverFreeGap`: 12.7
- `numThreeAncOverFreeGapRoot`: 3.6
- `numThreeAncPeak`: 0.115
- `numThreeAncRecall`: 0.730
- `numThreeAncVm`: 0.128
- `numThreeAncWorse`: 2
- `numThreeAncWorseTwoFiveSix`: 4
- `numThreeEvalSolves`: 2,048
- `numThreeFewSolves`: 256
- `numThreeFreeDisp`: 0.0300
- `numThreeFreeDispAdvantage`: 36.3%
- `numThreeFreeDispFour`: 0.0300
- `numThreeFreeGap`: 0.00912
- `numThreeFreeGapMedian`: 0.00763
- `numThreeFreeLoadWorse`: 1
- `numThreeFreeLoads`: 3,072
- `numThreeFreeOverMgnDisp`: 1.8
- `numThreeFreePeak`: 0.0807
- `numThreeFreeRecall`: 0.793
- `numThreeFreeVm`: 0.0554
- `numThreeFreeWorse`: 0
- `numThreeGuardTotal`: ten
- `numThreeGuardWithin`: three
- `numThreeKnormDisp`: 0.0227
- `numThreeKnormGap`: 0.00504
- `numThreeKnormPeak`: 0.0386
- `numThreeKnormRecall`: 0.858
- `numThreeKnormVm`: 0.0440
- `numThreeKnormWorse`: 0
- `numThreeLabDisp`: 0.0470
- `numThreeLabDispFour`: 0.0470
- `numThreeLabGap`: 31.2
- `numThreeLabGapMedian`: 0.252
- `numThreeLabGapMs`: 31.2 ± 53.5
- `numThreeLabGapSeeds`: 0.297, 93.0, 0.365
- `numThreeLabPeak`: 0.784
- `numThreeLabRecall`: 0.619
- `numThreeLabVm`: 0.370
- `numThreeLabWorse`: 18
- `numThreeLabWorseTwoFiveSix`: 132
- `numThreeLabWorst`: 23,727
- `numThreeLabWorstSeed`: 1
- `numThreeMedianRatioMax`: 33
- `numThreeMedianRatioMin`: 14
- `numThreeMgnDisp`: 0.0168
- `numThreeMgnGap`: 0.447
- `numThreeMgnGapMedian`: 0.208
- `numThreeMgnOverFreePeak`: 6.0
- `numThreeMgnOverFreeVm`: 5.3
- `numThreeMgnPeak`: 0.488
- `numThreeMgnRecall`: 0.679
- `numThreeMgnVm`: 0.296
- `numThreeMgnWorse`: 28
- `numThreePairs`: 768
- `numThreeSolves`: 6,400
- `numThreeTrainSolves`: 4,096
- `numThreeVal`: 256
- `numTimeBottleneckSeedMax`: 2.5
- `numTimeBottleneckSeedMin`: 2.5
- `numTimeBottleneckSpeedup`: 11
- `numTimeThreeSeed`: 27.3
- `numTimeTwoParallel`: 2 h 58 min
- `numTwoAdvMax`: 98.7%
- `numTwoAdvMin`: 80.4%
- `numTwoAncDisp`: 0.161
- `numTwoAncGap`: 0.166
- `numTwoAncGapMedian`: 0.0709
- `numTwoAncPeak`: 0.246
- `numTwoAncRecall`: 0.708
- `numTwoAncSixteenSeeds`: 0.225, 0.458, 0.546
- `numTwoAncVm`: 0.257
- `numTwoAncWorse`: 14
- `numTwoDispSpread`: 1.05
- `numTwoFreeDisp`: 0.166
- `numTwoFreeDispExcess`: +3.6%
- `numTwoFreeDispExcessAbs`: 3.6%
- `numTwoFreeDispFour`: 0.1658
- `numTwoFreeGap`: 0.0817
- `numTwoFreeGapMedian`: 0.0493
- `numTwoFreePeak`: 0.228
- `numTwoFreeRecall`: 0.739
- `numTwoFreeVm`: 0.210
- `numTwoFreeWorse`: 3
- `numTwoFtDisp`: 0.166
- `numTwoFtGap`: 0.236
- `numTwoFtGapMedian`: 0.156
- `numTwoFtPeak`: 0.301
- `numTwoFtRecall`: 0.645
- `numTwoFtVm`: 0.336
- `numTwoFtWorse`: 21
- `numTwoGapSpread`: 31
- `numTwoLabDisp`: 0.160
- `numTwoLabDispFour`: 0.1600
- `numTwoLabGap`: 0.418
- `numTwoLabGapMedian`: 0.274
- `numTwoLabGapSixteen`: 6.26
- `numTwoLabOverFreeGap`: 5.1
- `numTwoLabPeak`: 0.334
- `numTwoLabRecall`: 0.584
- `numTwoLabVm`: 0.433
- `numTwoLabWorse`: 52
- `numTwoMgnDisp`: 0.167
- `numTwoMgnGap`: 2.57
- `numTwoMgnGapMedian`: 1.35
- `numTwoMgnPeak`: 1.32
- `numTwoMgnRecall`: 0.322
- `numTwoMgnVm`: 1.10
- `numTwoMgnWorse`: 481
- `numTwoPairs`: 768
- `numTwoRuns`: nine
- `numTwoRunsDisp`: 0.1658 ± 0.0023
- `numTwoRunsGap`: 0.0820 ± 0.0026
- `numTwoSolves`: 7,168
- `numTwoSolvesOffline`: 5,120
- `numTwoSolvesRun`: 2,048
- `numTwoVal`: 256
- `numWarmFractionSeven`: 15%
- `numWarmFractionSeventeen`: 6%
- `numWarmFractionTwelve`: 9%
- `numWithinThree`: $6.76 \times 10^{-2}$
- `numWithinTwo`: $7.56 \times 10^{-2}$
- `numWorstFreeDisp`: 0.071
- `numWorstFreeGap`: 0.0349
- `numWorstFreeVm`: 0.10
- `numWorstIndex`: 107
- `numWorstLabDisp`: 0.032
- `numWorstLabGap`: 2.90
- `numWorstLabVm`: 0.73
- `numWorstMgnDisp`: 0.033
- `numWorstMgnGap`: 27.0
- `numWorstMgnVm`: 2.4
- `numWorstSeedLabDisp`: 0.55
- `numWorstSeedLabPeak`: 361
- `numWorstSeedLabVm`: 65
