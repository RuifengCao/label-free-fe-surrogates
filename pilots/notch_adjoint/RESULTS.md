# Pilot results: label-free primal and adjoint networks on notched plates (28 October 2026)

Version 2 of this write-up, revised after an independent review (same day). Version 1 gave a wrong cause for the size of the effectivity, presented the verdict as partly met, and listed the oracle bound as evidence; all three are corrected below.

Plan: PLAN.md, hashed at 01:07:42 UTC before any training. One deviation (D1, at the end), hashed at 01:13:47 UTC before the run reported here. Run: 01:13:57 to 01:58:37 UTC (run.log); raw numbers in results.json. An independent rerun of seed 0 with the same code reproduced run.log and all 64 rows of results.json exactly.

## Per seed (16 held-out geometries x 4 load cases = 64 cases per seed)

| Seed | Plug-in J(u): median / 90th pct / max | Corrected: median / 90th pct / max | Ratio of medians (verdict metric) | Median of per-case ratios | Oracle bound / J* (median) | Effectivity (median) | Energy error u / z (median) |
|---|---|---|---|---|---|---|---|
| 0 | 1.41% / 11.3% / 25.2% | 0.46% / 1.29% / 2.2% | 3.1 | 5.3 | 21% | 35 | 7.3% / 34.7% |
| 1 | 3.43% / 11.5% / 20.6% | 0.48% / 2.50% / 5.7% | 7.1 | 6.5 | 22% | 37 | 8.0% / 35.4% |
| 2 | 2.51% / 11.8% / 22.8% | 0.39% / 2.18% / 4.9% | 6.5 | 8.4 | 18% | 46 | 7.2% / 33.2% |

- Errors are relative to J* = q^T U* of the same FE model: the mean of sigma_yy over the elements whose centroids lie within 0.03 of the notch root point.
- The corrected estimate was worse than the plug-in value in 9, 4 and 4 of the 64 cases.

## Reading fixed in advance: not met
- PLAN.md required, in each of the three seeds, a corrected median error at most one fifth of the plug-in median. Seeds 1 and 2 meet it (7.1 and 6.5); seed 0 does not (3.1). **The pre-fixed reading is negative.**
- The verdict stays on the ratio of medians, as planned; the median of per-case ratios (5.3, 6.5, 8.4) is reported alongside, as PLAN.md also lists it, and is not used to change the verdict.

## What the pilot shows
- Without any solved example, the adjoint correction made the estimate of the notch stress both more accurate and steadier on unseen geometries of the family: the corrected median error was 0.39% to 0.48% in every seed, against 1.4% to 3.4% before, and the 90th percentile fell from about 11% to 1.3% to 2.5%.
- Post hoc comparison (made by the reviewer, not planned): a least-squares fit of J on the three geometric parameters, using the 24 training geometries' solved values, gives a median error of 1.3% to 1.9% and a 90th percentile of 3.5% to 5.7% on the same cases, depending on the basis. The plug-in network alone is no better than this fit; the corrected estimate is about three times more accurate at the median. On a parametric family such a fit is a strong baseline; scanned geometry has no such parameters.

## The bound
- The bound 2 sqrt(dPi dPi*) was evaluated with the reference solutions, an oracle check. It holds by the Cauchy-Schwarz inequality, so its holding in all 192 cases checks the code, not the method.
- Its size, 18% to 22% of the stress at the median, comes from the adjoint network's energy error (about 34% held out, and about 23% on the training geometries, estimated from the final training loss, so the adjoint network underfits). The oracle bound exceeded the plug-in's own actual error in every case, so it certifies nothing yet.
- The effectivity, bound over actual corrected error, equals 1 / |cos| of the angle between the two networks' errors in the energy inner product; it does not depend on how large the errors are. Medians of 35 to 46 mean the two errors are nearly orthogonal in that inner product, which is why the corrected error is far below the bound.
- Certifying the stress therefore needs a better adjoint network (task T2.2) and a computable bound (task T1.1).

## What it does not show
- Two dimensions, linear elasticity, one family of notches with three parameters, 24 training geometries and one draw of 16 held-out geometries; the seeds vary only the network initialisation. The geometry is the effective unit: geometry-level ratios of medians are 3.3, 7.6 and 6.5. Geometry 4 (d = 0.329, rho = 0.032, y_c = 0.277), the sharpest notch at the edge of the training range, accounts for 10 of the 17 cases made worse by the correction and for the largest corrected errors in seeds 1 and 2.
- The inputs are tuned to the quantity: six features are centred on the root point and three are scaled by the region's radius, so both networks are specific to this quantity of interest. Not tested: other regions, unknown hot spots, peak stresses (the regional mean is 0.71 to 0.81 of sigma_yy averaged within 0.006 of the root).
- No speed advantage at this size: a direct solve takes about 0.05 s, against 0.06 to 0.10 s for the meshing and assembly that the method needs anyway.
- No computable bound; no three-dimensional, nonlinear or scanned geometry; no comparison with supervised networks or reduced bases beyond the post hoc fit above.

## Deviations (as promised in PLAN.md)
- D1 (DEVIATIONS.md): training in single precision, with each step on one of four fixed groups of six training geometries in turn, because a full-batch double-precision step took about 1 s on the two-core machine. The code before D1 was reconstructed from the recorded edits; archive_model_preD1.py and archive_run_preD1.py match the SHA-256 recorded at 01:07:42 UTC, so the difference between the two versions is exactly D1.

## Errata to DEVIATIONS.md (left unchanged because it is hashed)
- Its header time, 01:14 UTC, should read 01:13 UTC: the file was written at 01:13:01 and hashed at 01:13:47.
- "No held-out quantity was computed" is inaccurate: run.py solves the held-out references before training. Two smoke tests of the whole pipeline (01:08 and 01:13 UTC), each with three training steps, also printed held-out metrics of these essentially untrained networks; they tested the code path and carry no information about trained networks. No metric of a trained network was seen before the run reported here.
- The stopped run's log, deleted before the new run, had two lines: "01:08:15 seed 0: primal" and "01:08:17 step 1 loss -0.130782".
- The hash times are recorded on this machine; an external timestamp (a public commit) would make them checkable.
