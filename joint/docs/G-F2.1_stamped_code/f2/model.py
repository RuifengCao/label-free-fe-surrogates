"""The network of the CHS surrogate (development draft of 20 November 2026; nothing here is stamped): features of an
exported instance, the maps from the network's outputs to a field z of the instance, and the field itself. Follows
c2/model.py: the repository's transformer encoder over the nodes, a copy of its field decoder, and a head that gives
the unknowns that belong to no node from the pooled latent.

The loading device's rotation Theta enters as the fraction Theta / Theta_max of the member's own device range. Every
output is scaled by s = L_REF Theta + delta, a displacement in mm: L_REF turns the rotation into a displacement and
delta is the bolts' pre-shortening, so that the scale stays positive at the preload state.

The lift. The end rotation theta (a head output) times a fixed field of the instance is added to the nodal outputs,
so that the network gives the tube's displacements as a correction to a simple motion that follows the end section
(G-C2.1 moves its web with the end displacement in the same way). The kinds (lift_field):
    none      no lift;
    v         the export's virtual rotation field: the far tube's sections (beyond z_h) rotate by theta zeta / L,
              zeta the distance from z_h and L the far tube's length; the axis does not deflect (shear arises);
    beam      v, and the axis deflects by theta zeta^2 / (2 L): constant curvature without shear;
    bending   beam, and the sections distort as in pure bending (Poisson's ratio of the tube), faded in over FADE;
    rigid     every tube node above the plate rotates with the end section about the tube's base (no strain in the
              tube; the jump is at the base).
One kind has three multipliers instead of one (lift_fields), the head then giving one more number, the rotation phi
of the tube's base:
    frame     the tube above the plate moves as a beam: it translates along its axis with w0, rotates about its
              base with phi, and bends as in pure bending, from the base to the end section, with theta - phi.
    hinge     frame, and the plate follows the tube's base where the base rises: every plate node's u_z (the gaps on
              the splice plane included) gets max(0, w0 - phi y) g(r), g one under the tube and its fillet and
              falling linearly to zero at the inner edge of the bolts' bearing rings. No bolt is stretched by it.
"""
from __future__ import annotations

import numpy as np

from .family import RANGES, geometry
from .instance import FLAGS

L_REF = 300.0          # mm: about the tube's diameter (323.9 mm)
THETA_KINDS = ("sqrt", "uniform")      # how the training draws its device rotations (sample_Theta)
LAM_MIN = 0.0125       # the smallest sampled fraction of the device range (G-C2.1: 0.1 mm of 8 mm)
FADE = 100.0           # mm: the length over which the section distortion of the lift "bending" sets in
LIFTS = ("none", "v", "beam", "bending", "rigid")     # one multiplier: the end rotation
LIFT_KINDS = LIFTS + ("frame", "hinge")
BEAMS = ("frame", "hinge")
GATES = ("softplus", "softplus_open")                       # the map of the contact unknowns (see field)                            # the kinds with the base rotation phi as one more head output
UNDER_FLOOR = 0.1269280110429726    # softplus(-2): with a field underneath, the least a contact unknown starts from, over s T


def features(ex: dict, q) -> np.ndarray:
    """(N, 21): centred and RMS-normalised coordinates (3), Dirichlet flags (3), the node flags of the export (10),
    the family parameters over their range maxima (5). The fraction of the device range is appended per field (the
    22nd feature). No solve involved."""
    nodes = np.asarray(ex["nodes"], float)
    c = nodes - nodes.mean(axis=0, keepdims=True)
    c = c / (np.sqrt((c ** 2).sum(axis=1).mean()) + 1e-12)
    n = nodes.shape[0]
    dmask = np.asarray(ex["fixed"])[:3 * n].reshape(n, 3).astype(float)
    flags = np.asarray(ex["node_flags"]).astype(float)
    desc = np.array([getattr(q, k) / RANGES[k][1] for k in RANGES])
    return np.concatenate([c, dmask, flags, np.broadcast_to(desc, (n, desc.size))], axis=1)


def lift_field(ex: dict, q, kind: str) -> np.ndarray:
    """(n_z,): the field that the end rotation multiplies (zero on theta itself, on the fixed unknowns and on the
    contact unknowns). See the module's text for the kinds."""
    assert kind in LIFTS, f"lift must be one of {LIFTS}"
    nodes = np.asarray(ex["nodes"], float)
    n, n_z, ith = nodes.shape[0], int(np.asarray(ex["v"]).size), int(ex["ith"])
    fixed = np.asarray(ex["fixed"], bool)
    nonneg = np.zeros(n_z, bool); nonneg[np.asarray(ex["cidx"], int)] = True
    out = np.zeros(n_z)
    if kind == "none":
        return out
    if kind == "v":
        out = np.asarray(ex["v"], float).copy()
    else:
        x, y, zc = nodes.T
        tube = np.asarray(ex["node_flags"])[:, FLAGS.index("tube")].astype(bool)
        z_end = float(zc.max())
        z0 = float(geometry(q).tp) if kind == "rigid" else float(ex["z_h"])
        idx = np.nonzero(tube & (zc > z0 + 1e-9))[0]
        zeta, L = zc[idx] - z0, z_end - z0
        if kind == "rigid":
            out[3 * idx + 2] = -y[idx]
            out[3 * idx + 1] = zeta
        else:
            out[3 * idx + 2] = -y[idx] * zeta / L
            out[3 * idx + 1] = zeta ** 2 / (2.0 * L)
            if kind == "bending":
                nu, f = float(ex["nu_t"]), np.minimum(1.0, zeta / FADE)
                out[3 * idx + 1] += nu * (y[idx] ** 2 - x[idx] ** 2) / (2.0 * L) * f
                out[3 * idx + 0] = nu * x[idx] * y[idx] / L * f
    out[ith] = 0.0                                               # theta itself is the head's output
    # the end section's u_z slots and the hanging nodes' slots are unused (fixed); the symmetry plane's u_x is fixed
    out[fixed] = 0.0
    if kind == "rigid":
        out[nonneg] = 0.0                                        # the root's opening slots at the tube's base
    assert not (out != 0)[nonneg].any(), "the lift touches a contact unknown"
    return out


def lift_fields(ex: dict, q, kind: str) -> np.ndarray:
    """(3, n_z): the fields multiplied by w0, by the base rotation phi and by theta - phi. For the kinds of
    lift_field the first two are zero and the third is that field (phi is then not used and counts as zero)."""
    assert kind in LIFT_KINDS, f"lift must be one of {LIFT_KINDS}"
    nodes = np.asarray(ex["nodes"], float)
    n_z = int(np.asarray(ex["v"]).size)
    out = np.zeros((3, n_z))
    if kind not in BEAMS:
        out[2] = lift_field(ex, q, kind)
        return out
    fixed = np.asarray(ex["fixed"], bool)
    nonneg = np.zeros(n_z, bool); nonneg[np.asarray(ex["cidx"], int)] = True
    x, y, zc = nodes.T
    tube = np.asarray(ex["node_flags"])[:, FLAGS.index("tube")].astype(bool)
    z0, z_end = float(geometry(q).tp), float(zc.max())
    idx = np.nonzero(tube & (zc > z0 + 1e-9))[0]
    zeta, L = zc[idx] - z0, z_end - z0
    nu, f = float(ex["nu_t"]), np.minimum(1.0, (zc[idx] - z0) / FADE)
    out[0, 3 * idx + 2] = 1.0                                    # along the axis
    out[1, 3 * idx + 2] = -y[idx]                                # about the base
    out[1, 3 * idx + 1] = zeta
    out[2, 3 * idx + 2] = -y[idx] * zeta / L                     # pure bending between the base and the end
    out[2, 3 * idx + 1] = zeta ** 2 / (2.0 * L) + nu * (y[idx] ** 2 - x[idx] ** 2) / (2.0 * L) * f
    out[2, 3 * idx + 0] = nu * x[idx] * y[idx] / L * f
    out[:, fixed | nonneg] = 0.0
    out[:, [int(ex["ith"]), int(ex["iw0"])]] = 0.0               # w0 and theta themselves are the head's outputs
    return out


def plate_follow(ex: dict, q):
    """For the lift "hinge": the u_z slots of the nodes at or below the plate's top face that are not fixed, their
    y, and the factor g(r) (see the module's text)."""
    nodes = np.asarray(ex["nodes"], float)
    x, y, zc = nodes.T
    g = geometry(q)
    r, r_in, r_out = np.hypot(x, y), g.R + g.leg, g.r2 - g.r_bear
    assert r_out > r_in
    w = np.clip((r_out - r) / (r_out - r_in), 0.0, 1.0)
    sel = np.nonzero((zc <= g.tp + 1e-9) & (w > 0))[0]
    idx = 3 * sel + 2
    keep = ~np.asarray(ex["fixed"], bool)[idx]
    root = np.asarray(ex["node_flags"])[sel, FLAGS.index("root_tube")].astype(bool)   # these slots hold root openings
    keep &= ~root
    return idx[keep], y[sel][keep], w[sel][keep]


def maps(ex: dict, q, device, lift: str = "beam"):
    """The masks and constants that turn network outputs into a field z (n_z) of the instance, and those of the
    readings of a field (the end rotation, the tests' rotation Theta_D)."""
    import torch

    n = int(np.asarray(ex["nodes"]).shape[0])
    n_z = int(np.asarray(ex["v"]).size)
    nb = int(np.asarray(ex["head"]).size)
    ith, iw0 = int(ex["ith"]), int(ex["iw0"])
    assert n_z == 3 * n + 3 * nb + 2 and ith == n_z - 1 and iw0 == n_z - 2
    assert np.array_equal(np.asarray(ex["head"]).ravel(), 3 * n + 3 * np.arange(nb))
    cidx = np.asarray(ex["cidx"], int)
    assert cidx.max() < 3 * n, "a contact unknown outside the nodal slots"
    nonneg = np.zeros(n_z, bool); nonneg[cidx] = True
    fixed = np.asarray(ex["fixed"], bool)
    assert not (fixed & nonneg).any() and not fixed[3 * n:].any()
    r = float(geometry(q).r_bear)
    hs = np.tile([1.0, 1.0 / r, 1.0 / r], nb)
    delta = np.asarray(ex["delta"], float).ravel()
    assert delta.size == nb and np.ptp(delta) <= 1e-12 * max(abs(delta).max(), 1e-300), "one pre-shortening for all bolts"
    b = lambda a: torch.as_tensor(a, device=device)  # noqa: E731
    follow = {}
    if lift == "hinge":
        pi, py, pg = plate_follow(ex, q)
        follow = {"plate_idx": b(pi.astype(np.int64)), "plate_y": b(py.astype(np.float32)),
                  "plate_g": b(pg.astype(np.float32))}
    return {"nonneg": b(nonneg), "fixed": b(fixed), "head_scale": b(hs.astype(np.float32)),
            "lift": b(lift_fields(ex, q, lift).astype(np.float32)), "lift_kind": lift, **follow,
            "aux": 1 if lift in BEAMS else 0, "delta": float(delta[0]),
            "Theta_max": float(ex["Theta_max"]), "k_th": float(ex["k_th"]), "uD": 3 * int(ex["iD"]) + 2,
            "d": float(ex["d"]), "ThetaD_pre": float(ex["ThetaD_pre"]), "n": n, "n_z": n_z, "nb": nb}


def build(cfg: dict, in_dim: int, nb: int):
    """(encoder, decoder, head): the repository's build_encoder, a copy of its FieldDecoder and the head network
    (the bolt heads' three unknowns each, w0 and theta, and for the lifts "frame" and "hinge" the base rotation
    phi), last layers zeroed."""
    import torch
    from torch import nn
    from fejepa.models.fejepa import build_encoder

    m = cfg["model"]
    enc = build_encoder(in_dim, m["dim"], m["depth"], m["heads"])
    enc.use_checkpoint = bool(m["activation_checkpointing"])
    d = m["dim"]
    dec = nn.Sequential(nn.Linear(2 * d, 2 * d), nn.GELU(), nn.Linear(2 * d, d), nn.GELU(), nn.Linear(d, 3))
    aux = 1 if m.get("lift") in BEAMS else 0
    head = nn.Sequential(nn.Linear(d, d), nn.GELU(), nn.Linear(d, d), nn.GELU(), nn.Linear(d, 3 * nb + 2 + aux))
    with torch.no_grad():
        for net in (dec, head):
            net[-1].weight.zero_()
            net[-1].bias.zero_()
    return enc, dec, head


_GATE = {}


def open_gate():
    """The function (u, T) -> T softplus(u / T) whose backward pass lets an opening pull through unreduced.

    The forward value is the softplus map's. In the backward pass a gradient g of the loss with respect to the
    map's value is multiplied by the map's slope sigmoid(u / T) only where g >= 0 (the loss wants the unknown
    smaller: the contact closes, and the slope lets it settle); where g < 0 (the loss wants the unknown larger: the
    contact is pulled open) g passes as it is. With the plain map a closed contact, u / T well below zero, passes
    almost nothing either way, so a contact that has closed is slow to open again. The stationary points are the
    same as those of a projected gradient: an open contact has no gradient left, a closed contact keeps a push
    towards closing only."""
    if "f" not in _GATE:
        import torch

        class OpenGate(torch.autograd.Function):
            @staticmethod
            def forward(ctx, u, T):
                ctx.save_for_backward(u)
                ctx.T = T
                return T * torch.nn.functional.softplus(u / T)

            @staticmethod
            def backward(ctx, g):
                (u,) = ctx.saved_tensors
                return torch.where(g < 0, g, g * torch.sigmoid(u / ctx.T)), None

        _GATE["f"] = OpenGate
    return _GATE["f"].apply


def inputs(base, lam):
    """Features of a batch of fields: base (N, 21) of the instance and the fractions lam (B,) of the device range ->
    (B, N, 22)."""
    import torch

    B, N = lam.shape[0], base.shape[0]
    return torch.cat([base.unsqueeze(0).expand(B, N, base.shape[1]), lam[:, None, None].expand(B, N, 1)], dim=-1)


def field(enc, dec, head, base, mp: dict, Theta, T: float, lift: bool = True, gate: str = "softplus", under=None):
    """The predicted fields z (B, n_z) at loading-device rotations Theta (B,): decoder outputs (softplus at
    temperature T on the contact unknowns) and head outputs (each bolt head's a and two tilts, w0, theta), times the
    scale s = L_REF Theta + delta (the tilts also over the bearing radius, theta and phi over L_REF); with lift, plus
    the instance's lift fields times their multipliers; the fixed unknowns zero. gate "softplus_open" keeps the
    softplus values and changes the backward pass only (open_gate).

    under (B, n_z), a field given from outside (f2.train.under_field: a coarser mesh's network, carried to this
    mesh): the outputs are then a correction to it. The nodal displacements, the heads' unknowns, w0 and theta add
    to it, and the lift is multiplied by the correction's theta only. A contact unknown stays the map of an output:
    the map's argument is shifted so that a zero output gives the value underneath, or s T UNDER_FLOOR if that is
    larger (a contact closed underneath starts a hair open, where the map still passes a gradient). With zero
    outputs, as the networks start, the field is the one underneath."""
    import torch
    from torch import nn

    B, n, nb = Theta.shape[0], mp["n"], mp["nb"]
    h = enc(inputs(base, Theta / mp["Theta_max"]))             # (B, N, dim)
    pooled = h.mean(dim=-2, keepdim=True)
    un = dec(torch.cat([h, pooled.expand_as(h)], dim=-1)).reshape(B, -1)          # (B, 3n)
    assert gate in GATES, f"gate must be one of {GATES}"
    s = (L_REF * Theta + mp["delta"])[:, None]
    arg = un
    if under is not None:
        if mp["aux"]:
            raise NotImplementedError("a field underneath is written for the lifts with one multiplier")
        y = (under[:, :3 * n] / (s * T)).clamp_min(UNDER_FLOOR)
        start = T * torch.where(y > 20.0, y, torch.log(torch.expm1(y.clamp(max=20.0))))
        arg = un + torch.where(mp["nonneg"][:3 * n], start, torch.zeros_like(start))
    mapped = open_gate()(arg, T) if gate == "softplus_open" else T * nn.functional.softplus(arg / T)
    un = torch.where(mp["nonneg"][:3 * n], mapped, un)
    gh = head(pooled[:, 0])                                    # (B, 3 nb + 2), one more with a base rotation
    w0 = gh[:, 3 * nb:3 * nb + 1] * s
    th = gh[:, 3 * nb + 1:3 * nb + 2] * s / L_REF
    z = torch.cat([un * s, gh[:, :3 * nb] * mp["head_scale"] * s, w0, th], dim=1)
    if under is not None:
        z = z + torch.where(mp["nonneg"], torch.zeros_like(under), under)
    if lift:
        if mp["aux"]:
            phi = gh[:, 3 * nb + 2:3 * nb + 3] * s / L_REF
            z = z + w0 * mp["lift"][0] + phi * mp["lift"][1] + (th - phi) * mp["lift"][2]
            if "plate_idx" in mp:                               # the plate follows the base where the base rises
                up = torch.relu(w0 - phi * mp["plate_y"]) * mp["plate_g"]
                z = z.index_add(1, mp["plate_idx"], up)
        else:
            z = z + th * mp["lift"][2]
    return torch.where(mp["fixed"], torch.zeros_like(z), z)


def readings(energy, mp: dict, z, Theta) -> dict:
    """What a field says without any reference: its end rotation, the moment of its spring reading
    M = 2 k_th (Theta - theta), and the tests' rotation Theta_D (relative to the preload state). z (B, n_z)."""
    theta = z[:, mp["n_z"] - 1]
    uD = energy.physical(z)[:, mp["uD"]]
    return {"theta": theta, "M": 2.0 * mp["k_th"] * (Theta - theta), "ThetaD": uD / mp["d"] - mp["ThetaD_pre"]}


def sample_Theta(rng, Theta_max: float, B: int, lam_min: float = LAM_MIN, kind: str = "sqrt",
                 top: float = 1.0) -> np.ndarray:
    """B device rotations between lam_min Theta_max and top Theta_max. kind "sqrt": sqrt(Theta) uniform, as G-C2.1
    samples its displacements; with top 1 this is the sampling of every run before 24 November 2026, and the same
    numbers come from the generator. kind "uniform": Theta uniform. With top above 1 rotations beyond the member's
    device range are drawn, so that the last evaluation level is not the edge of what the training saw."""
    assert kind in THETA_KINDS, f"kind must be one of {THETA_KINDS}"
    assert top > lam_min
    if kind == "uniform":
        return rng.uniform(lam_min * Theta_max, top * Theta_max, size=B)
    lo, hi = np.sqrt(lam_min * Theta_max), np.sqrt(top * Theta_max)
    return rng.uniform(lo, hi, size=B) ** 2


__all__ = ["L_REF", "LAM_MIN", "LIFTS", "LIFT_KINDS", "BEAMS", "GATES", "UNDER_FLOOR", "open_gate", "features", "lift_field", "lift_fields",
           "plate_follow", "maps", "build",
           "inputs", "field", "readings", "sample_Theta", "THETA_KINDS"]
