"""R0-a: is the surrogate as poor on the training members as on the held-out ones?
For the chosen training members with exact solutions so far: energy gap, end-displacement error and force error at
the same loading displacement of the host's final model (seed given), by stratum (fy < 300 MPa or not) and by
level, next to the same quantities of the 64 held-out members (from the gate's verdict.json)."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths  # noqa: E401,E702
sys.path.insert(0, str(paths.joint()))
import json, numpy as np
from pathlib import Path
from c2.data import load_export
from c2.instance import ExportedProblem
seed = int(sys.argv[1])
LEVELS = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]
man = json.load(open(paths.data() / "manifest.json")); par = {r["id"]: r["params"] for r in man["instances"]}
sel = json.load(open(paths.work() / "selection.json"))
pr = np.load(paths.work() / f"out/preds_s{seed}_train.npz")
rows = []
cache = Path(paths.work() / f"out/train_rows_s{seed}.json")
done = json.loads(cache.read_text()) if cache.exists() else {}
for iid in sel["order"]:
    lp = Path(paths.work() / "labels") / f"{iid}.npz"
    if not lp.exists() or iid not in pr.files: continue
    if iid not in done:
        lab = np.load(lp); ex, q = load_export(Path(paths.data() / "inst") / f"{iid}.npz"); P = ExportedProblem(ex)
        out = []
        for l, D in enumerate(LEVELS):
            r = P.evaluate(pr[iid][l].astype(np.float64), D)
            out.append({"D": D, "gap": r["Pi"] / float(lab["Pi"][l]) - 1, "e_err": r["e"] / float(lab["e"][l]) - 1, "F_err": r["F"] / float(lab["F"][l]) - 1,
                        "m": float(lab["e"][l]) / (D - float(lab["e"][l])), "bolt_err": r["bolt_N"] / float(lab["bolt_N"][l]) - 1})
        done[iid] = out; cache.write_text(json.dumps(done))
    for r in done[iid]: rows.append({"iid": iid, "weak": par[iid]["fy"] < 300, **r})
v = json.load(open(paths.ret() / "verdict.json"))
ev = v["arms"]["label_free"][str(seed)]["eval_rows"]
held = []
for iid, rr in ev.items():
    lab = np.load(paths.ret() / f"labels/{iid}.npz")
    for l, r in enumerate(rr):
        held.append({"iid": iid, "weak": par[iid]["fy"] < 300, "D": r["D"], "gap": r["gap"], "e_err": r["e_err"], "F_err": r["F_err"], "m": float(lab["e"][l]) / (r["D"] - float(lab["e"][l]))})
q = lambda x, p: float(np.quantile(np.asarray(x, float), p)) if len(x) else float("nan")
def line(S):
    return f"n {len(S):3d} ({len({r['iid'] for r in S}):2d} members)  gap median {100*q([r['gap'] for r in S],.5):6.2f}%  p90 {100*q([r['gap'] for r in S],.9):6.2f}% | |e err| median {100*q([abs(r['e_err']) for r in S],.5):5.2f}%  p90 {100*q([abs(r['e_err']) for r in S],.9):6.2f}% | |F err, same D| median {100*q([abs(r['F_err']) for r in S],.5):5.2f}%  p90 {100*q([abs(r['F_err']) for r in S],.9):6.2f}% | e too small in {sum(r['e_err'] < 0 for r in S)}"
print(f"seed {seed}: training members solved so far: {len({r['iid'] for r in rows})}")
for name, cond in (("weak (fy < 300), D >= 6", lambda r: r["weak"] and r["D"] >= 6), ("weak, D = 3 or 4", lambda r: r["weak"] and r["D"] in (3.0, 4.0)), ("weak, D <= 2", lambda r: r["weak"] and r["D"] <= 2),
                   ("others (fy >= 300), D >= 6", lambda r: (not r["weak"]) and r["D"] >= 6), ("others, D = 3 or 4", lambda r: (not r["weak"]) and r["D"] in (3.0, 4.0)), ("others, D <= 2", lambda r: (not r["weak"]) and r["D"] <= 2), ("all", lambda r: True)):
    print(f"  {name}\n     training: {line([r for r in rows if cond(r)])}\n     held-out: {line([r for r in held if cond(r)])}")
