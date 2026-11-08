"""CPU seconds of one training-energy evaluation with its gradient (float32, four fields, ten bubble Newton steps),
for a G-C2.1 T-stub (a development member, seed 7) and the CHS family's B-13 on the coarse mesh, at a plastic
reference state of each. Only a relative indication of the GPU cost: the network's own cost is not included.

    python -I probes/f2_dev/energy_cost.py
"""
import os
import sys

for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_k] = "1"

import json  # noqa: E402
import pathlib  # noqa: E402
import time  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if not p or pathlib.Path(p).resolve() != HERE]
sys.path.insert(0, str(HERE.parents[1]))

import numpy as np  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(1)


def timed(E, Z, load, reps=5):
    zt = torch.tensor(Z, dtype=torch.float32, requires_grad=True)
    lt = torch.tensor(load, dtype=torch.float32)
    E.energy(zt, lt).sum().backward()                    # warm-up
    ts = []
    for _ in range(reps):
        zt.grad = None
        t0 = time.perf_counter()
        E.energy(zt, lt).sum().backward()
        ts.append(time.perf_counter() - t0)
    return float(np.median(ts))


def main():
    from c2.family import sample, MESH
    from c2.instance import build as c2_build, export as c2_export, ExportedProblem as C2P
    from c2.torch_energy import InstanceEnergy as C2E
    from f2.family import Params, TESTED
    from f2 import instance as I
    from f2.torch_energy import InstanceEnergy as F2E

    q = sample(1, 7)[0][0]
    m = c2_build(q, mesh=MESH)
    ex = c2_export(m, q)
    r = C2P(ex).solve(4.0)
    rng = np.random.default_rng(0)
    Z = np.stack([r["z"] * (1 + 0.01 * rng.normal(size=r["z"].size)) for _ in range(4)])
    Z[:, ex["fixed"]] = 0.0
    Z[:, ex["cidx"]] = np.maximum(Z[:, ex["cidx"]], 0.0)
    t_c2 = timed(C2E(ex), Z, [4.0] * 4)
    q2 = Params(**TESTED["B-13_nominal"])
    ex2, pre = I.make(q2, mesh="coarse", k_th=4e9)
    P = I.ExportedProblem(ex2)
    r2 = P.solve(0.02, z0=pre["z"])
    Z2 = np.stack([r2["z"] * (1 + 0.01 * rng.normal(size=r2["z"].size)) for _ in range(4)])
    Z2[:, ex2["fixed"]] = 0.0
    Z2[:, ex2["cidx"]] = np.maximum(Z2[:, ex2["cidx"]], 0.0)
    t_f2 = timed(F2E(ex2), Z2, [0.02] * 4)
    n1, n2 = int(ex["nodes"].shape[0]), int(ex2["nodes"].shape[0])
    c1 = int(ex["hexes_f"].shape[0] + ex["hexes_w"].shape[0])
    c2_ = int(sum(ex2[f"hexes_{p}"].shape[0] for p in I.PARTS))
    print(json.dumps({"c2": {"nodes": n1, "cells": c1, "unknowns": int(ex["v"].size), "seconds": t_c2},
                      "f2_B-13": {"nodes": n2, "cells": c2_, "unknowns": int(ex2["v"].size), "seconds": t_f2,
                                  "theta_at_Theta_0.02": r2["theta"], "ThetaD": r2["ThetaD"]},
                      "ratio_seconds": t_f2 / t_c2, "ratio_nodes": n2 / n1, "ratio_cells": c2_ / c1}, indent=1))


if __name__ == "__main__":
    main()
