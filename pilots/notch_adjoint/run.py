"""Run the pilot exactly as fixed in PLAN.md: train both networks for seeds 0, 1, 2; evaluate on held-out geometries."""
import json, sys, time
import numpy as np
import jax
import jax.numpy as jnp
from gen import sample_params, build
from model import pack, init_mlp, primal_loss, adjoint_loss, adam_train, fields

STEPS = 6000
SIZES_P = [11, 64, 64, 64, 64, 4]
SIZES_A = [11, 64, 64, 64, 64, 2]


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def main(seeds):
    train = [build(p, solve_reference=False) for p in sample_params(np.random.default_rng(2026), 24)]
    test = [build(p, solve_reference=True) for p in sample_params(np.random.default_rng(2027), 16)]
    loads = np.random.default_rng(2028).uniform([0.5, -0.5], [1.5, 0.5], size=(16, 4, 2))
    groups = [pack(train[i:i + 6]) for i in range(0, 24, 6)]          # four fixed groups (DEVIATIONS.md, D1)
    Pte, Ste = pack(test)
    results = {}
    for seed in seeds:
        log("seed %d: primal" % seed)
        kp, ka = jax.random.split(jax.random.PRNGKey(seed))
        pp, hp = adam_train(primal_loss, init_mlp(kp, SIZES_P), groups, STEPS, log=log)
        log("seed %d: adjoint" % seed)
        pa, ha = adam_train(adjoint_loss, init_mlp(ka, SIZES_A), groups, STEPS, log=log)
        # predictions on the held-out geometries; label-free rescaling and all evaluation in double precision
        ut, ub = fields(pp, Pte, Ste, 2)
        (z,) = fields(pa, Pte, Ste, 1)
        ut, ub, z = (np.asarray(a, dtype=np.float64) for a in (ut, ub, z))
        rows = []
        off = 0
        for g, I in enumerate(test):
            n = I["n_dof"]
            sl = slice(off, off + n)
            off += n
            K, q = I["K"], I["q"]
            Z = I["Z"]
            c = lambda v, f: v * (f @ v) / (v @ (K @ v))                   # closed-form label-free rescaling
            ut_g, ub_g, zg = c(ut[sl], I["F_t"]), c(ub[sl], I["F_b"]), c(z[sl], q)
            ez = zg - Z
            dPis = 0.5 * ez @ (K @ ez)
            for a_t, a_b in loads[g]:
                F = a_t * I["F_t"] + a_b * I["F_b"]
                U = a_t * I["U_t"] + a_b * I["U_b"]
                u = a_t * ut_g + a_b * ub_g
                eu = u - U
                dPi = 0.5 * eu @ (K @ eu)
                Js = q @ U
                Jp = q @ u
                Jc = Jp + zg @ (F - K @ u)
                B = 2.0 * np.sqrt(dPi * dPis)
                rows.append(dict(geom=g, a_t=a_t, a_b=a_b, J_ref=Js, J_plug=Jp, J_corr=Jc, bound=B,
                                 err_plug=abs(Jp - Js) / abs(Js), err_corr=abs(Jc - Js) / abs(Js),
                                 rel_energy_u=np.sqrt(eu @ (K @ eu) / (U @ (K @ U))),
                                 rel_energy_z=np.sqrt(ez @ (K @ ez) / (Z @ (K @ Z))),
                                 bound_holds=bool(abs(Jc - Js) <= B * (1 + 1e-9)), effectivity=B / abs(Jc - Js)))
        ep = np.array([r["err_plug"] for r in rows]); ec = np.array([r["err_corr"] for r in rows])
        summ = dict(median_err_plug=float(np.median(ep)), p90_err_plug=float(np.percentile(ep, 90)),
                    median_err_corr=float(np.median(ec)), p90_err_corr=float(np.percentile(ec, 90)),
                    median_ratio_plug_over_corr=float(np.median(ep / ec)),
                    ratio_of_medians=float(np.median(ep) / np.median(ec)),
                    bound_holds_share=float(np.mean([r["bound_holds"] for r in rows])),
                    median_effectivity=float(np.median([r["effectivity"] for r in rows])),
                    median_rel_bound=float(np.median([r["bound"] / abs(r["J_ref"]) for r in rows])),
                    median_rel_energy_u=float(np.median([r["rel_energy_u"] for r in rows])),
                    median_rel_energy_z=float(np.median([r["rel_energy_z"] for r in rows])),
                    positive=bool(np.median(ec) <= np.median(ep) / 5 and all(r["bound_holds"] for r in rows)),
                    loss_primal=hp, loss_adjoint=ha)
        log("seed %d summary: %s" % (seed, json.dumps({k: v for k, v in summ.items() if not k.startswith("loss")})))
        results[seed] = dict(summary=summ, rows=rows)
        json.dump(results, open("results.json", "w"), indent=1, default=float)
    log("done")


if __name__ == "__main__":
    main([int(s) for s in sys.argv[1:]] or [0, 1, 2])
