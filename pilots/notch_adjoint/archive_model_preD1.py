"""Label-free primal and adjoint networks for the notched-plate family (JAX, CPU).

The training code reads only K, the load vectors F_t and F_b, and q. It never reads the reference solutions.
"""
import numpy as np
import jax
import jax.numpy as jnp

jax.config.update("jax_enable_x64", True)


R_Q = 0.03


def features(pts, params):
    """Point features (11): x, y; scaled d, rho, y_c; bounded notch-scaled coordinates and exp(-r / s) for s = rho, R_Q."""
    d, rho, yc = params
    x, y = pts[:, 0], pts[:, 1]
    n = len(x)
    cols = [x, y, np.full(n, (d - 0.25) / 0.1), np.full(n, (rho - 0.065) / 0.035), np.full(n, yc / 0.3)]
    for s in (rho, R_Q):
        xi, eta = (x - d) / s, (y - yc) / s
        r = np.sqrt(xi ** 2 + eta ** 2)
        cols += [xi / (1 + r), eta / (1 + r), np.exp(-r)]
    return np.stack(cols, axis=1)


def pack(insts):
    """Concatenate instances into one block-diagonal system with static shapes."""
    feats, bc, ix, iy, rows, cols, vals, Ft, Fb, q, inst_of_dof = [], [], [], [], [], [], [], [], [], [], []
    off = 0
    for k, I in enumerate(insts):
        feats.append(features(I["pts"], I["params"]))
        bc.append((I["pts"][:, 1] + 1.0) / 2.0)
        ix.append(I["ix"] + off); iy.append(I["iy"] + off)
        Kc = I["K"].tocoo()
        rows.append(Kc.row + off); cols.append(Kc.col + off); vals.append(Kc.data)
        Ft.append(I["F_t"]); Fb.append(I["F_b"]); q.append(I["q"])
        inst_of_dof.append(np.full(I["n_dof"], k))
        off += I["n_dof"]
    cat = np.concatenate
    return dict(feats=jnp.asarray(cat(feats)), bc=jnp.asarray(cat(bc)), ix=jnp.asarray(cat(ix)), iy=jnp.asarray(cat(iy)),
                rows=jnp.asarray(cat(rows)), cols=jnp.asarray(cat(cols)), vals=jnp.asarray(cat(vals)),
                Ft=jnp.asarray(cat(Ft)), Fb=jnp.asarray(cat(Fb)), q=jnp.asarray(cat(q)),
                inst=jnp.asarray(cat(inst_of_dof))), dict(n_dof=off, n_inst=len(insts))


def init_mlp(key, sizes):
    params = []
    for a, b in zip(sizes[:-1], sizes[1:]):
        key, k1 = jax.random.split(key)
        params.append((jax.random.normal(k1, (a, b)) * np.sqrt(1.0 / a), jnp.zeros(b)))
    return params


def mlp(params, x):
    for W, b in params[:-1]:
        x = jnp.tanh(x @ W + b)
    W, b = params[-1]
    return x @ W + b


def fields(params, P, S, n_fields):
    """Network output at the node locations, scattered to global dof vectors, one per field."""
    out = mlp(params, P["feats"]) * P["bc"][:, None]
    vecs = []
    for f in range(n_fields):
        v = jnp.zeros(S["n_dof"])
        v = v.at[P["ix"]].set(out[:, 2 * f]).at[P["iy"]].set(out[:, 2 * f + 1])
        vecs.append(v)
    return vecs


def per_inst(P, S, x):
    return jax.ops.segment_sum(x, P["inst"], num_segments=S["n_inst"])


def quad(P, S, u, v):
    """Per-instance u^T K v for the block-diagonal system."""
    prod = P["vals"] * u[P["rows"]] * v[P["cols"]]
    return jax.ops.segment_sum(prod, P["inst"][P["rows"]], num_segments=S["n_inst"])


def rescale(P, S, v, f):
    """Closed-form, label-free energy-optimal scale per instance: c* = f^T v / v^T K v; returns c* v."""
    c = per_inst(P, S, f * v) / quad(P, S, v, v)
    return v * c[P["inst"]]


def energy(P, S, v, f):
    """Per-instance Pi(v) = 1/2 v^T K v - f^T v."""
    return 0.5 * quad(P, S, v, v) - per_inst(P, S, f * v)


def primal_loss(params, P, S):
    ut, ub = fields(params, P, S, 2)
    ut, ub = rescale(P, S, ut, P["Ft"]), rescale(P, S, ub, P["Fb"])
    return jnp.mean(energy(P, S, ut, P["Ft"]) + energy(P, S, ub, P["Fb"]))


def adjoint_loss(params, P, S):
    (z,) = fields(params, P, S, 1)
    z = rescale(P, S, z, P["q"])
    return jnp.mean(energy(P, S, z, P["q"]))


def adam_train(loss_fn, params, P, S, steps, lr0=1e-3, lr1=1e-5, log_every=500, log=print):
    grad_fn = jax.jit(jax.value_and_grad(lambda p, A: loss_fn(p, A, S)))
    m = jax.tree_util.tree_map(jnp.zeros_like, params)
    v = jax.tree_util.tree_map(jnp.zeros_like, params)
    b1, b2, eps = 0.9, 0.999, 1e-8

    @jax.jit
    def update(params, m, v, g, t, lr):
        m = jax.tree_util.tree_map(lambda a, b: b1 * a + (1 - b1) * b, m, g)
        v = jax.tree_util.tree_map(lambda a, b: b2 * a + (1 - b2) * b * b, v, g)
        mh = jax.tree_util.tree_map(lambda a: a / (1 - b1 ** t), m)
        vh = jax.tree_util.tree_map(lambda a: a / (1 - b2 ** t), v)
        params = jax.tree_util.tree_map(lambda p, a, b: p - lr * a / (jnp.sqrt(b) + eps), params, mh, vh)
        return params, m, v

    hist = []
    for t in range(1, steps + 1):
        lr = lr1 + 0.5 * (lr0 - lr1) * (1 + np.cos(np.pi * (t - 1) / steps))
        val, g = grad_fn(params, P)
        params, m, v = update(params, m, v, g, t, lr)
        if t % log_every == 0 or t == 1:
            hist.append((t, float(val)))
            log("step %d loss %.6f" % (t, float(val)))
    return params, hist
