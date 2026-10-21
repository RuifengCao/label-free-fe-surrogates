# FE-JEPA v2.0 -- RESULTS

Run `01ab66dcb818` | 2026-10-20T02:17:51+00:00 | git `prereg-fine3d` | device=cuda tf32=True | workers=1
Pre-registration: verified `01ab66dcb818` against `PREREG_FINE3D.md`

## Gate G2 (PREREG_PHASE2)
**NO-GO** -- logic a AND (b OR c); (a)=False (b)=False (c)=False; transfer zone: retired

| kill | triggered |
|---|---|
| KP1 | no |
| KP2 | no |
| KP3 | no |
| KP4 | **YES** |
| KP5 | no |
| KP6 | no |

Reasons:
- `a_sanity`: no budget at or above sanity_min_budget 64: (a) unassessed
- `b_label_efficiency`: ar / labels cell missing
- `KP3`: sourced from P1 shared cells; anchored egap improvements [] (kill if ALL < 0.25)
- `c_transfer`: fine/in-band ratio 4.794 (win <= 1.25, kill > 1.5); naive beaten at fine: True
- `KP5`: P4/WP6 not run -- theory transcription unverified
- `KP6`: P5/E6 not run -- alignment claim unevaluated

Sanity condition (a) assessed at budgets >= 64 (PREREG_PHASE2B); the stamped Phase-2 form (every budget) is reported as reference:
- reference G2 (all budgets): **NO-GO** -- (a)=False (b)=False (c)=False; a_sanity: no budget at or above sanity_min_budget 0: (a) unassessed

## Gate G1' (legacy; not the Phase-2 gate)
not run

## Kill conditions
| exp | condition | triggered | note |
|---|---|---|---|
| e8 | K2: not evaluated (ar_only run: no labels-only cells) | no | AR 0.1071 |
| e8 | C1-advantage: not evaluated (ar_only run) | no |  |

## E1' -- anchor as supervised auxiliary (P-A)
not run

## E5' -- repaired sanity
not run

## E8 -- regime grid (headline table)
**Displacement rel-L2**
| regime |  |
|---|

**Relative energy gap**
| regime |  |
|---|

AR (unlabeled pool 1024, 0 labels): disp 0.1071±0.0205, egap 0.0317±0.0104, vM 0.1245±0.0227
Label-efficiency AUC (disp): 

## E2 -- JEPA vs AR (P-B, one-shot verdict)
not run

## E3' -- collapse (standardized rank)
not run

## E4' -- cross-resolution invariance
not run

## E6 -- latent-physics alignment
not run

## E7 -- learned init + CG polish
not run

## WP2 -- region-mask ratio sweep (pre-E2)
not run

## WP6 -- theory numeric falsification pass
not run

## Data economy (WP5)
- labelled instances: 256 (val 256 + pool prefix 0), 4 solves each
- reference solves total: 0
- unlabeled pool depth used: 1024 (x1024.0 the labelled prefix)

## Solve ledger
- total: 0 (wall 0.0 s)

## Provenance
- runs/data3d_phase2: n=2000, backend=gmsh3d, manifest `dc75628290bb`
- runs/data3d_phase2_fine: n=320, backend=gmsh3d, manifest `0f859ad98a01`
