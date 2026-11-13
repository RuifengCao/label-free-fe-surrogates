"""Amplitude condensation of a batch of fields of one instance: the reading judged by gate G-C2.2.

For each field b of the batch: the amplitude a_b that minimises the total potential of

    z_c = keep(z0_b + a (z_b - z0_b))        (keep: the contact unknowns clamped at zero from below)

at the field's loading-device displacement D_b, over a_min <= a <= a_max. z0 is the network's own field at the
smallest loading level, so z - z0 is the part of the field that the loading causes. No reference solution enters.

The slope g = dPi/da is driven to zero by a safeguarded secant iteration: from a = 1 the search first steps downhill
until the slope changes sign (the steps grow, or follow the secant with an overshoot), then refines the bracket by
regula falsi kept away from the bracket's ends. Every evaluation is one energy and its derivative in a. The point of
lowest energy among those evaluated is returned, so the result never has a higher energy than a = 1."""
import torch


def condense(energy, z0, z, D, nonneg, nb: int, a_min: float = 0.5, a_max: float = 3.0, evals: int = 8,
             rtol: float = 1e-4):
    """energy: c2.torch_energy.InstanceEnergy; z0, z (B, n_z); D (B,); nonneg (n_z,) bool; nb: bubble Newton steps.
    Returns a (B,) without gradient and a dict: 'rel_slope' |dPi/da| / Pi at a (B,), 'evals' (int),
    'at_bound' (B,) bool (the minimiser lies on a_min or a_max), 'converged' (B,) bool."""
    d = z - z0
    B, dev = z.shape[0], z.device

    def vg(a):
        a = a.clone().requires_grad_(True)
        zc = z0 + a[:, None] * d
        Pi = energy.energy(torch.where(nonneg, zc.clamp_min(0.0), zc), D, iters=nb)
        g, = torch.autograd.grad(Pi.sum(), a)
        return Pi.detach(), g.detach()

    nan = float("nan")
    lo = torch.full((B,), a_min, device=dev)                 # bracket: slope < 0 at lo, slope > 0 at hi
    hi = torch.full((B,), a_max, device=dev)
    g_lo = torch.full((B,), nan, device=dev)                 # nan: that end is the bound, not evaluated
    g_hi = torch.full((B,), nan, device=dev)
    a = torch.ones(B, device=dev).clamp(a_min, a_max)
    P, g = vg(a)
    best_a, best_P, best_g = a.clone(), P.clone(), g.clone()
    a_prev, g_prev = a.clone(), g.clone()
    n, first = 1, True
    done = torch.zeros(B, dtype=torch.bool, device=dev)
    at_bound = torch.zeros(B, dtype=torch.bool, device=dev)
    while True:
        neg = g < 0
        take_lo, take_hi = neg & (a >= lo), (~neg) & (a <= hi)
        lo, g_lo = torch.where(take_lo, a, lo), torch.where(take_lo, g, g_lo)
        hi, g_hi = torch.where(take_hi, a, hi), torch.where(take_hi, g, g_hi)
        better = P < best_P
        if not first:
            best_a, best_P, best_g = torch.where(better, a, best_a), torch.where(better, P, best_P), torch.where(better, g, best_g)
        at_bound = ((a >= a_max) & neg) | ((a <= a_min) & ~neg & (g > 0)) | at_bound
        done = done | (best_g.abs() <= rtol * best_P.abs()) | at_bound
        if n >= evals or bool(done.all()):
            break
        have = torch.isfinite(g_lo) & torch.isfinite(g_hi)
        w = hi - lo
        sec = (lo * g_hi - hi * g_lo) / (g_hi - g_lo)                           # regula falsi inside the bracket
        sec = torch.minimum(torch.maximum(sec, lo + 0.1 * w), hi - 0.1 * w)
        direction = torch.where(neg, torch.ones_like(a), -torch.ones_like(a))   # downhill
        last = (a - a_prev).abs()
        grow = torch.where(last > 0, 2.0 * last, torch.full_like(a, 0.04))
        slope = (g - g_prev) / (a - a_prev)
        ext = torch.where((last > 0) & (slope > 0), 1.25 * (g.abs() / slope.clamp_min(1e-30)), grow)
        ext = torch.minimum(torch.maximum(ext, torch.full_like(a, 0.02)), torch.maximum(4.0 * last, torch.full_like(a, 0.04)))
        out = (a + direction * ext).clamp(a_min, a_max)                          # expansion while not bracketed
        new = torch.where(have, sec, out)
        new = torch.where(done, best_a, new)
        a_prev, g_prev = a, g
        a = new
        P, g = vg(a)
        n += 1
        first = False
    return best_a, {"rel_slope": best_g.abs() / best_P.abs(), "evals": n, "at_bound": at_bound, "converged": done}
