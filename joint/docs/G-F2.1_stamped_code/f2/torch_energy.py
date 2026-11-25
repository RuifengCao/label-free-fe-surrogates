"""The energy of an exported CHS splice instance in torch, for training (f2.instance holds the reference in numpy).

The closed-form Hencky law, the element sets with their bubble parameters and the sparse helpers are gate
G-C2.1's (c2/torch_energy.py), imported unchanged. Here: three element sets (plate, tube, fillet weld, each with
its own law and Young's modulus), the twelve half bolts' axial springs with a pre-shortening per bolt, the linear
part (the heads' tilt springs, weak springs on the head separations), and the loading spring
1/2 k_th (theta - Theta)^2 of each field's loading-device rotation Theta.

All functions take a batch of fields of one instance: z (B, n_z) -> energies (B,).
"""
from __future__ import annotations

import numpy as np

from c2.torch_energy import HenckyLaw, ElementSet, BoltSprings as _BoltSprings, sparse, _t

PARTS = ("p", "t", "w")


class BoltSprings(_BoltSprings):
    """c2.torch_energy.BoltSprings with a pre-shortening per bolt (nb,) instead of one value."""

    def __init__(self, k, e_pts, N_pts, h_end, delta, device, dtype):
        super().__init__(k, e_pts, N_pts, h_end, 0.0, device, dtype)
        self.delta = _t().as_tensor(np.asarray(delta, float), dtype=dtype, device=device)


class InstanceEnergy:
    """Pi(z) of one exported instance (the dict of f2.instance.export) for a batch of fields z (B, n_z)."""

    def __init__(self, ex: dict, device="cpu", dtype=None):
        torch = _t()
        dtype = torch.float32 if dtype is None else dtype
        self.device, self.dtype = device, dtype
        self.sets = []
        for p in PARTS:
            law = HenckyLaw(ex[f"hard_{p}_alpha"], ex[f"hard_{p}_sigma"], float(ex[f"hard_{p}_hend"]),
                            float(ex[f"E_{p}"]), float(ex[f"nu_{p}"]), device, dtype)
            self.sets.append(ElementSet(ex["nodes"], ex[f"hexes_{p}"], law, device, dtype))
        self.T = sparse(ex["T_row"], ex["T_col"], ex["T_val"], ex["T_shape"], device, dtype)
        self.K = sparse(ex["K_row"], ex["K_col"], ex["K_val"], ex["K_shape"], device, dtype)
        self.head = torch.as_tensor(np.asarray(ex["head"]).ravel(), dtype=torch.long, device=device)
        self.bolts = BoltSprings(float(ex["k_ax"]), ex["bolt_e"], ex["bolt_N"], float(ex["bolt_hend"]), ex["delta"],
                                 device, dtype)
        self.ith, self.k_th = int(ex["ith"]), float(ex["k_th"])

    def physical(self, z):                             # (B, n_z) -> (B, 3n)
        torch = _t()
        return torch.sparse.mm(self.T, z.T.contiguous()).T

    def energy(self, z, Theta, iters: int = 10):       # (B, n_z), (B,) -> (B,)
        torch = _t()
        u = self.physical(z)
        E = 0.5 * (z * torch.sparse.mm(self.K, z.T.contiguous()).T).sum(-1)
        for s in self.sets:
            E = E + s.energy(u, iters=iters)
        return E + self.bolts.energy(z[:, self.head]) + 0.5 * self.k_th * (z[:, self.ith] - Theta) ** 2


__all__ = ["BoltSprings", "InstanceEnergy", "PARTS"]
