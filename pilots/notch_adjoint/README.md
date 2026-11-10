# Pilot: label-free primal and adjoint networks on notched plates

An exploratory pilot, run on 28 October 2026 for the proposal of an FWO junior postdoctoral fellowship (submitted on 10 November 2026). It is not one of this repository's gates and was not run under a stamp, but its plan was fixed, and its SHA-256 recorded, before any network was trained.

The question: on plate geometries the networks have not seen, does the adjoint correction J(u) + z^T (F - K u), with the primal network u and the adjoint network z both trained on energies alone (no solved examples), estimate the stress at a notch root much better than the plug-in value J(u)? And how tight is the bound 2 sqrt(dPi dPi*)?

## Files

- `PLAN.md`: the plan, hashed at 01:07:42 UTC before any training.
- `DEVIATIONS.md`: one deviation, D1 (training in single precision, each step on one of four fixed groups of six training geometries), recorded and hashed at 01:13:47 UTC, before the run reported here.
- `HASHES_before_run.txt`: the SHA-256 of the plan and the code before the run, and again after D1.
- `gen.py`: the plate family, the Triangle mesh, the quadratic-triangle stiffness (scikit-fem), the loads, the quantity of interest and the reference solutions.
- `model.py`, `run.py`: the networks, training and evaluation as run, after D1. `archive_model_preD1.py` and `archive_run_preD1.py` are the versions hashed before D1.
- `run.log`, `results.json`: the run of 01:13:57 to 01:58:37 UTC; three seeds, each evaluated on 16 held-out geometries with 4 load cases.
- `RESULTS.md`: the results, version 2, revised after an independent review the same day. The reading fixed in advance was not met: it required the corrected median error to be at most one fifth of the plug-in median in every seed, and in seed 0 it was about one third (a ratio of 3.1).
- `identities_check.py`: numerical checks, on random symmetric positive definite matrices, of the identities and bounds the proposal uses: the adjoint correction and its bound, the Rayleigh quotient of linear buckling, the bound from an equilibrated split of the residual, and an inertia check for the critical load factor (27 and 28 October 2026).

## Running

With Python, numpy, scipy, JAX (CPU), scikit-fem and triangle installed, from this folder:

```
python identities_check.py
python run.py
```

`run.py` trains and evaluates seeds 0, 1 and 2 (other seeds can be given as arguments), prints its log and writes `results.json` in the current folder, so run it in a copy of this folder to keep the records. The run took about 45 minutes on two CPU cores.

## Licence

The code (`*.py`) is licensed under the PolyForm Noncommercial License 1.0.0, as the rest of this repository. The plan, deviations, results, hashes and run records (`*.md`, `HASHES_before_run.txt`, `run.log` and `results.json`) are licensed under the Creative Commons Attribution 4.0 International licence; see the repository's README.
