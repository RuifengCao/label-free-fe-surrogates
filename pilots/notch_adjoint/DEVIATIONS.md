# Deviations from PLAN.md (recorded before any evaluation result was seen)

## D1, 28 October 2026, 01:14 UTC: training precision and batching
- What the plan said: 6,000 full-batch steps on all 24 training geometries, double precision.
- Why it changes: on this machine (2 CPU cores) a full-batch double-precision step was measured at about 1 s, so the plan would take about 10 hours for three seeds. The first run (seed 0, primal network) was stopped before its step 500 log line; no network was evaluated and no held-out quantity was computed.
- What is done instead: each of the 6,000 steps uses one of four fixed groups of six training geometries, taken in turn (the same 24 geometries); training in single precision. Everything else is unchanged: networks, losses, learning-rate schedule, seeds, held-out geometries, load cases, metrics and the reading fixed in advance. Network outputs are converted to double precision before the label-free rescaling and all evaluation quantities (energy gaps, errors and the bound).
