"""T-stub pair of fejoint.tstub with plasticity in the flange and the web, bolt preload and displacement control.

Same mesh, bolt-head model, contact and readings as fejoint.tstub.analyse (rigid head planes in unilateral
contact with the flange's outer face, free to tilt against bending springs; the plane between the flanges a
rigid frictionless support; quarter model, or half model along the length with full_length). What changes:
  material  the flange and the web (with its root radius or weld) are PlasticHexSets (fejoint.nlhex) with their
            own Material each; the head's bending springs stay linear; the half bolt's axial spring is elastic or
            elastic-plastic (fejoint.nlsolve.AxialSprings, deformation-theory form);
  preload   each half bolt is shorter than its grip by delta (a pre-shortening): its extension is a + delta, a the
            head's axial displacement, so its force is N(a + delta) (k_ax (a + delta) while elastic). delta is set
            by a fixed-point iteration so that every bolt carries the target force with no external load;
  load      either a total force F on the pair, uniform on the web's end section (as before), or a prescribed
            uniform displacement u_x = d of that section (displacement control), whose reaction is the force.
Solved with fejoint.nlsolve (deformation theory: one convex problem per load level; flow theory: load steps).
Units: N, mm, MPa.
"""
from __future__ import annotations

from dataclasses import asdict
import numpy as np
import scipy.sparse as sp

from .tstub import TStubPair, build
from .joint import _face_weights
from .nlhex import PlasticHexSet
from .nlsolve import ContactProblem, AxialSprings
from .plasticity import Material


class PlasticTStubModel:
    def __init__(self, g: TStubPair, mat_f: Material, mat_w: Material, h: float = 2.5, n_tf: int = 4,
                 k_rot_factor: float = 1.0, reg: float = 1e-6, hx_max: float = 20.0, control: str = "displacement",
                 bolt_curve=None):
        """bolt_curve: None (elastic bolts) or the half bolt's force-extension law beyond yield,
        (extensions, forces, final slope) with extensions[0] = forces[0] / k_ax (see nlsolve.AxialSprings)."""
        assert control in ("displacement", "force")
        self.g, self.control = g, control
        nodes, hexes, part = build(g, h, n_tf, hx_max=hx_max, with_part=True)
        self.nodes, self.hexes, self.part = nodes, hexes, part
        n = nodes.shape[0]; ndof = 3 * n
        self.n, self.ndof = n, ndof
        x, y, z = nodes.T
        face = np.nonzero(np.isclose(x, g.t_f))[0]
        patches = [face[np.hypot(y[face] - yb, z[face] - g.w / 2) <= g.bearing_r + 1e-9] for yb in g.bolt_y]
        assert all(p.size >= 3 for p in patches)
        self.patches = patches
        nb = len(patches); self.nb = nb
        Lh = g.L_b / 2
        self.k_ax = g.Eb * g.As / Lh
        d_s = np.sqrt(4 * g.As / np.pi); I_s = np.pi * d_s ** 4 / 64
        k_rot = k_rot_factor * g.Eb * I_s / Lh
        k_sh = 16.0 * g.d ** 2 * 800.0 / 16.0
        diag = np.zeros(ndof)
        for p in patches:
            wts = _face_weights(nodes, p, (1, 2)); wts = wts / wts.sum()
            diag[3 * p + 1] += k_sh * wts; diag[3 * p + 2] += k_sh * wts
        nfull = ndof + 3 * nb
        is_pux = np.zeros(ndof, bool)
        for p in patches:
            is_pux[3 * p] = True
        ident = np.r_[np.nonzero(~is_pux)[0], ndof + np.arange(3 * nb)]
        rT, cT, vT = [ident], [ident], [np.ones(ident.size)]
        for k, (p, yb) in enumerate(zip(patches, g.bolt_y)):
            base = ndof + 3 * k
            rT += [3 * p] * 4
            cT += [np.full(p.size, base), np.full(p.size, base + 1), np.full(p.size, base + 2), 3 * p]
            vT += [np.ones(p.size), y[p] - yb, z[p] - g.w / 2, -np.ones(p.size)]
        T = sp.csr_matrix((np.concatenate(vT), (np.concatenate(rT), np.concatenate(cT))), shape=(nfull, nfull))
        head_k = np.tile([0.0, k_rot, k_rot], nb)          # the axial bolt springs are an AxialSprings set
        K_lin = (T.T @ sp.block_diag([sp.diags(diag), sp.diags(head_k)]) @ T).tocsr()
        kreg = np.zeros(nfull)
        for p in patches:
            kreg[3 * p] = reg * self.k_ax / p.size
        K_lin = (K_lin + sp.diags(kreg)).tocsr()
        self.T_phys = T[:ndof]                                   # z -> physical u (3n)
        self.head_a = ndof + 3 * np.arange(nb)                   # axial head unknowns
        self.share = 0.5 if g.full_length else 0.25
        xe = x.max()
        self.endn = np.nonzero(np.isclose(x, xe))[0]
        wts = _face_weights(nodes, self.endn, (1, 2)); self.end_w = wts / wts.sum()
        fixed = np.zeros(nfull, bool)
        fixed[3 * np.nonzero(np.isclose(z, 0))[0] + 2] = True
        if not g.full_length:
            fixed[3 * np.nonzero(np.isclose(y, g.L / 2))[0] + 1] = True
        fixed_d = fixed.copy(); fixed_d[3 * self.endn] = True
        contact = np.nonzero(np.isclose(x, 0))[0]
        self.contact = contact
        cidx = np.r_[3 * contact, np.concatenate([3 * p for p in patches])]
        self.n_contact = contact.size
        self.bolts = AxialSprings(ndof + 3 * np.arange(nb), nfull, self.k_ax, N_curve=bolt_curve)
        self.sets = [PlasticHexSet(nodes, hexes[part == 0], mat_f), PlasticHexSet(nodes, hexes[part == 1], mat_w),
                     self.bolts]
        self.probs = {"force": ContactProblem(self.T_phys, K_lin, np.zeros(nfull), self.sets, fixed, cidx),
                      "displacement": ContactProblem(self.T_phys, K_lin, np.zeros(nfull), self.sets, fixed_d, cidx)}
        self.prob = self.probs[control]
        self.nfull = nfull
        self.delta = 0.0
        self.z = np.zeros(nfull)
        self.meta = {"geometry": asdict(g), "mesh": {"h": h, "n_tf": n_tf, "nodes": int(n), "unknowns": int(nfull)},
                     "k_ax": self.k_ax, "k_rot": k_rot, "control": control}

    # ---- loads ------------------------------------------------------------------------------------------------
    def solve(self, value, mode="hencky", z0=None, control=None, **kw):
        """Solve at a load level: a total force F (force control) or the end displacement d (displacement
        control; the default is the model's own control)."""
        control = self.control if control is None else control
        self.prob = self.probs[control]
        f = np.zeros(self.nfull)
        self.bolts.delta[:] = self.delta                          # preload: the bolt's extension is a + delta
        if control == "force":
            np.add.at(f, 3 * self.endn, self.share * value * self.end_w)
        self.prob.f = f
        z = (self.z if z0 is None else z0).copy()
        if control == "displacement":
            z[3 * self.endn] = value
        z, rep = self.prob.solve(z, mode=mode, **kw)
        self.z = z
        self.last_control = control
        return z, rep

    def readings(self, z, rep):
        g = self.g
        u = (self.T_phys @ z).reshape(-1, 3)
        bolt = self.bolts._law(z[self.head_a] + self.delta)[0]
        grad = rep["grad"]
        if getattr(self, "last_control", self.control) == "displacement":
            F = float(grad[3 * self.endn].sum()) / self.share
        else:
            F = float(self.prob.f[3 * self.endn].sum()) / self.share
        x, y, zc = self.nodes.T
        out = {"F_N": F, "bolt_force_N": [float(b) for b in bolt],
               "contact_fraction": float((z[3 * self.contact] <= 1e-12 * max(np.abs(z).max(), 1e-300)).mean()),
               "plastic_points": rep.get("plastic_points"), "kkt": {k: rep[k] for k in
                                                                      ("min_gap", "min_lambda", "max_complementarity",
                                                                       "max_lambda_inactive",
                                                                       "max_residual_unconstrained")},
               "iterations": rep["iterations"], "converged": rep["converged"]}
        sec = np.nonzero(np.isclose(x, g.x_meas))[0]
        if sec.size:
            w = _face_weights(self.nodes, sec, (1, 2)); w = w / w.sum()
            out["Delta_web_mm"] = 2.0 * float((u[sec, 0] * w).sum())
        ends = [0.0, g.L] if g.full_length else [0.0]
        gaps = []
        for ye in ends:
            m = np.nonzero(np.isclose(x, 0) & np.isclose(y, ye) & np.isclose(zc, 0))[0]
            if m.size == 1:
                gaps.append(2.0 * float(u[m[0], 0]))
        out["Delta_gap_mm"] = float(np.mean(gaps)) if gaps else None
        out["d_end_mm"] = float((u[self.endn, 0] * self.end_w).sum())
        return out

    def set_preload(self, N_target, mode="hencky", tol=1e-6, max_it=20):
        """Pre-shortening delta so that every bolt carries N_target at zero external load (fixed point on delta),
        solved under force control with no load; the displacement-controlled loading then starts from there."""
        if N_target <= 0:
            self.delta = 0.0
            return {"delta": 0.0}
        self.delta = N_target / self.k_ax
        hist = []
        for _ in range(max_it):
            snap = [s.snapshot() for s in self.sets]
            z, rep = self.solve(0.0, mode=mode, control="force")
            r = self.readings(z, rep)
            Nm = float(np.mean(r["bolt_force_N"]))
            hist.append((self.delta, Nm))
            if abs(Nm / N_target - 1) < tol:
                break
            for s, sn in zip(self.sets, snap):
                s.restore(sn)
            self.delta *= N_target / Nm
        return {"delta": self.delta, "history": hist}

    def commit(self):
        for s in self.sets:
            s.commit()


__all__ = ["PlasticTStubModel"]
