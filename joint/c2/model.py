"""The network of gate G-C2.1: the repository's encoder with a copy of its field decoder and a head for the bolt
head's unknowns, node features from the export, the output scale, the non-negative map on the contact unknowns and
the prescribed values."""
from __future__ import annotations

import numpy as np

from .family import RANGES, D_MAX, BOLT


def features(ex: dict, q) -> np.ndarray:
    """(N, 20): centred and RMS-normalised coordinates (3), Dirichlet flags (3), the node flags of the export (7),
    the family parameters over their range maxima (7). The loading-device displacement over D_MAX is appended per
    field (the 21st feature). No solve involved."""
    nodes = np.asarray(ex["nodes"], float)
    c = nodes - nodes.mean(axis=0, keepdims=True)
    c = c / (np.sqrt((c ** 2).sum(axis=1).mean()) + 1e-12)
    n = nodes.shape[0]
    dmask = np.asarray(ex["fixed"])[:3 * n].reshape(n, 3).astype(float)
    flags = np.asarray(ex["node_flags"]).astype(float)
    desc = np.array([getattr(q, k) / RANGES[k][1] for k in RANGES])
    return np.concatenate([c, dmask, flags, np.broadcast_to(desc, (n, desc.size))], axis=1)


def maps(ex: dict, device):
    """The masks and constants that turn network outputs into a field z (n_z) of the instance."""
    import torch

    n = int(np.asarray(ex["nodes"]).shape[0])
    n_z = int(np.asarray(ex["v"]).size)
    nb = int(np.asarray(ex["head"]).size)
    assert nb == 1, "one bolt per quarter model in this family"
    assert n_z == 3 * n + 3 * nb + 1 and int(ex["e_idx"]) == n_z - 1
    assert np.array_equal(np.asarray(ex["head"]).ravel(), 3 * n + 3 * np.arange(nb))
    nonneg = np.zeros(3 * n, bool); nonneg[np.asarray(ex["cidx"])] = True
    fixed = np.asarray(ex["fixed"], bool)
    assert not (fixed[:3 * n] & nonneg).any() and not fixed[3 * n:].any()
    hs = np.tile([1.0, 1.0 / BOLT["bearing_r"], 1.0 / BOLT["bearing_r"]], nb)
    web = np.zeros(n_z, bool); web[3 * np.nonzero(np.asarray(ex["node_flags"])[:, 4])[0]] = True
    web &= ~fixed
    assert not (web[:3 * n] & nonneg).any(), "a non-negative unknown on the web"
    b = lambda a: torch.as_tensor(a, device=device)  # noqa: E731
    return {"nonneg": b(nonneg), "fixed": b(fixed), "head_scale": b(hs.astype(np.float32)),
            "web_x": b(web.astype(np.float32)), "delta": float(ex["delta"]), "n": n, "n_z": n_z, "nb": nb}


def build(cfg: dict, in_dim: int):
    """(encoder, decoder, head): the repository's build_encoder, a copy of its FieldDecoder and the head network
    (the end section's u_x e and the bolt head's three unknowns), last layers zeroed."""
    import torch
    from torch import nn
    from fejepa.models.fejepa import build_encoder

    m = cfg["model"]
    enc = build_encoder(in_dim, m["dim"], m["depth"], m["heads"])
    enc.use_checkpoint = bool(m["activation_checkpointing"])
    d = m["dim"]
    dec = nn.Sequential(nn.Linear(2 * d, 2 * d), nn.GELU(), nn.Linear(2 * d, d), nn.GELU(), nn.Linear(d, 3))
    head = nn.Sequential(nn.Linear(d, d), nn.GELU(), nn.Linear(d, d), nn.GELU(), nn.Linear(d, 4))
    with torch.no_grad():
        for net in (dec, head):
            net[-1].weight.zero_()
            net[-1].bias.zero_()
    return enc, dec, head


def inputs(base, D):
    """Features of a batch of fields: base (N, 20) of the instance and the loading-device displacements D (B,) ->
    (B, N, 21)."""
    import torch

    B, N = D.shape[0], base.shape[0]
    return torch.cat([base.unsqueeze(0).expand(B, N, base.shape[1]),
                      (D / D_MAX)[:, None, None].expand(B, N, 1)], dim=-1)


def field(enc, dec, head, base, mp: dict, D, T: float, lift: bool = False):
    """The predicted fields z (B, n_z) at loading-device displacements D (B,): decoder outputs (softplus at
    temperature T on the non-negative unknowns) and head outputs (e, then the bolt head's a, b, c), times the scale
    D + delta (the tilts also over the bearing radius); with lift, plus e on u_x of every node of the web (the web
    translating with its end section, so that the network gives the web's stretch as a correction); the fixed
    unknowns zero."""
    import torch
    from torch import nn

    B = D.shape[0]
    h = enc(inputs(base, D))                                   # (B, N, dim)
    pooled = h.mean(dim=-2, keepdim=True)
    un = dec(torch.cat([h, pooled.expand_as(h)], dim=-1)).reshape(B, -1)
    un = torch.where(mp["nonneg"], T * nn.functional.softplus(un / T), un)
    gh = head(pooled[:, 0])                                    # (B, 4)
    s = (D + mp["delta"])[:, None]
    e = gh[:, :1] * s
    z = torch.cat([un * s, gh[:, 1:] * mp["head_scale"] * s, e], dim=1)
    if lift:
        z = z + e * mp["web_x"]
    return torch.where(mp["fixed"], torch.zeros_like(z), z)
