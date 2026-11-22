# Independent audit of gate G-C2.3: exact solves of chosen pairs with the stamped reference library and a
# driver of the auditor's own.
#
# What it checks. For a pair (run, reading, member, level) the judged error is F / F*(e) - 1: e is the end
# displacement of the predicted field, F = 4 k_s (D - e) its spring force, F*(e) the force of the reference model
# at the prescribed end displacement e. This script reads e from the returned prediction file, calls the stamped
# ExportedProblem.solve_at_e (warm start: the label nearest in e, as the stamped metric does) and forms the error
# itself. It does not import c2.evaluate, c23.evaluate, or any script of the author's.
#
# The reference code keeps the bubble parameters of its last solve in each element set (attribute "bub"). A unit
# of work is therefore a list of steps on ONE problem object, so that the state in which a solve starts is under
# the auditor's control:
#   {"op": "zero"}                      set the element state to zero (as a new problem object has it)
#   {"op": "fresh"}                     build a new problem object
#   {"op": "pair", "run": R, "reading": "raw"|"condensed", "level": l, "evaluate": bool}
#                                       the exact solve of the pair from the present element state; with
#                                       "evaluate" the predicted field is evaluated afterwards, as the stamped
#                                       metric does, and it is recorded whether that call changed the state
#   {"op": "probe", "run": R, "reading": ..., "level": l, "cap": n}
#                                       no solve: the number of bubble iterations that the first evaluation of
#                                       that pair's solve needs from the present element state, per element set,
#                                       counted up to cap (the stamped cap is 60), with the energy of each set
#                                       there; the state is left as it was
#   {"op": "label", "level": l}         evaluate the label at a level (as the stamped evaluation does first)
#   {"op": "label_state", "level": l}   evaluate the label at a level and adopt the bubble parameters of that
#                                       evaluation as the element state (the state of an exact solution at that
#                                       level, without a solve)
# One JSON result file is written for each unit; a unit whose file exists is skipped, so the job can be resumed.
#
# Usage: python -I solve_pairs.py --repo <stamped joint folder> --inst <instances> --labels <labels>
#            --runs <run folders> --units <units.json> --out <results folder> [--part i/n] [--reverse]
# Set FEJOINT_SOLVER=legacy and one BLAS thread a process before the call, as on the host.
import argparse
import hashlib
import json
import os
import sys

sys.dont_write_bytecode = True      # the stamped tree is read, never written: no bytecode folders in it
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--inst", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--units", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--part", default="0/1")
    ap.add_argument("--reverse", action="store_true", help="take the units from the end of the list")
    a = ap.parse_args()
    if os.environ.get("FEJOINT_SOLVER") != "legacy":
        sys.exit("set FEJOINT_SOLVER=legacy (the host had scipy's solver only)")
    sys.path.insert(0, os.path.abspath(a.repo))
    import numpy as np
    from c2.instance import ExportedProblem          # the stamped reference problem; nothing else of the gate

    files = {"raw": "preds.npz", "condensed": "preds_condensed.npz"}
    part, nparts = (int(v) for v in a.part.split("/"))
    units = json.load(open(a.units, encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)
    pred_cache = {}

    def pred(run, reading, member):
        key = (run, reading)
        if key not in pred_cache:
            pred_cache[key] = np.load(os.path.join(a.runs, run, files[reading]))
        return np.asarray(pred_cache[key][member], dtype=np.float64)

    def state_hash(P):
        h = hashlib.sha256()
        for s in P.solids:
            h.update(np.ascontiguousarray(s.bub).tobytes())
        return h.hexdigest()[:16]

    def state_size(P):
        return [float(np.abs(s.bub).max()) for s in P.solids]

    todo = [u for k, u in enumerate(units) if k % nparts == part]
    for unit in (reversed(todo) if a.reverse else todo):
        outp = os.path.join(a.out, unit["id"] + ".json")
        if os.path.exists(outp):
            continue
        member = unit["member"]
        with np.load(os.path.join(a.inst, member + ".npz"), allow_pickle=False) as z:
            ex = {key: z[key] for key in z.files if key not in ("params_json", "config_sha256")}
        with np.load(os.path.join(a.labels, member + ".npz")) as z:
            ref = {key: z[key] for key in z.files}
        P = ExportedProblem(ex)
        res = []
        for step in unit["steps"]:
            op = step["op"]
            t0 = time.perf_counter()
            r = dict(step)
            if op == "zero":
                for s in P.solids:
                    s.bub = np.zeros_like(s.bub)
            elif op == "fresh":
                P = ExportedProblem(ex)
            elif op == "label":
                lv = step["level"]
                before = state_hash(P)
                try:
                    ev = P.evaluate(ref["z"][lv], float(ref["D"][lv]))
                    r.update(Pi=ev["Pi"], F=ev["F"], F_label=float(ref["F"][lv]), Pi_label=float(ref["Pi"][lv]))
                except Exception as err:
                    r["note"] = f"{type(err).__name__}: {err}"
                r["state_changed"] = state_hash(P) != before
            elif op == "label_state":
                lv = step["level"]
                try:
                    P.evaluate(ref["z"][lv], float(ref["D"][lv]))
                    for s in P.solids:
                        s.warm()                   # adopt the bubble parameters of the label's field as the state
                except Exception as err:
                    r["note"] = f"{type(err).__name__}: {err}"
                r["state_size_after"] = state_size(P)
            elif op in ("pair", "probe"):
                lv = step["level"]
                zp = pred(step["run"], step["reading"], member)[lv]
                D = float(ref["D"][lv])
                e = float(zp[P.e_idx])
                F = 4.0 * P.k_s * (D - e)
                near = int(np.argmin(np.abs(np.asarray(ref["e"]) - e)))
                r.update(D=D, e=e, F=F, near=near, state_before=state_hash(P), state_size_before=state_size(P))
                if op == "probe":
                    z0 = np.where(P.prob_e.fixed, 0.0, ref["z"][near])
                    z0[P.e_idx] = e
                    u = P.prob_e.T @ z0
                    its, energies = [], []
                    for s in P.solids:
                        try:
                            ev = s.evaluate(u, mode="hencky", tangent=False, max_it=int(step.get("cap", 400)))
                            its.append(int(ev[3]["bubble_iterations"]))
                            energies.append(float(ev[0]))
                        except RuntimeError as err:
                            its.append(f"{err}")
                            energies.append(None)
                    r["bubble_iterations"], r["set_energies"] = its, energies
                    r["state_changed"] = state_hash(P) != r["state_before"]
                else:
                    note, err_signed, conv, Fstar = "", float("nan"), None, None
                    try:
                        c = P.solve_at_e(e, z0=ref["z"][near])
                        conv, Fstar = bool(c["converged"]), float(c["F"])
                        if conv and Fstar > 0:
                            err_signed = F / Fstar - 1.0
                        else:
                            err_signed = float("inf")
                            note = "not converged" if not conv else "reference force not positive"
                    except Exception as err:
                        err_signed, note = float("inf"), f"{type(err).__name__}: {err}"
                    r.update(curve_err=err_signed, note=note, converged=conv, F_star=Fstar,
                             state_after=state_hash(P), state_size_after=state_size(P))
                    if step.get("evaluate"):
                        before = state_hash(P)
                        try:
                            ev = P.evaluate(zp, D)
                            r["Pi_field"] = ev["Pi"]
                            r["gap"] = (ev["Pi"] - float(ref["Pi"][lv])) / abs(float(ref["Pi"][lv]))
                        except Exception as err:
                            r["evaluate_note"] = f"{type(err).__name__}: {err}"
                        r["evaluate_changed_state"] = state_hash(P) != before
            else:
                raise SystemExit(f"unknown step {op}")
            r["seconds"] = round(time.perf_counter() - t0, 2)
            res.append(r)
        tmp = outp + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"id": unit["id"], "member": member, "steps": res}, fh, indent=1)
        os.replace(tmp, outp)
        print(unit["id"], "done", flush=True)


if __name__ == "__main__":
    main()
