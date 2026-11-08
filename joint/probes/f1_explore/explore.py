"""Exploratory runs after the verdict of gate G-F1 (probes/f1_explore/EXPLORE_PLAN.md): E1a, E1, E2 and E3.

The gate's code is imported unchanged and checked against docs/G-F1_code.sha256 before anything runs. The set-up
is changed on copies of the configuration in memory; for E3's elastic-plastic bolts, f1.run.model is replaced
inside this process by the same function with a bolt curve, and restored afterwards.

From joint/:
  python probes/f1_explore/explore.py run E1a E1 E2 E3 [--case TEXT] [--out DIR] [--smoke]
  python probes/f1_explore/explore.py tables [--out DIR] [--smoke]

run      solves the cases of the experiments named, in that order; a case with a record is skipped, so a run that
         was cut off is continued by the same command; --case keeps only the cases whose id contains TEXT.
tables   writes RESULTS.md from the records: the checks first, then the tables and the readings of the plan.
--smoke  every path on the tiny meshes (coarse -> tiny, medium -> tiny-flag), against tiny reference paths of the
         gate's own code; nothing is compared with the tests' conclusions and the numbers are not used.
Outside --smoke, the hashes of EXPLORE_PLAN.md and of this file must be in PLAN_HASH.txt.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse  # noqa: E402
import contextlib  # noqa: E402
import copy  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
JOINT = HERE.parents[1]
sys.path.insert(0, str(JOINT))

import numpy as np  # noqa: E402

import f1.run as R  # noqa: E402
from f1.config import DATA, PLATES, TUBE, canonical, config  # noqa: E402
from f1.materials import material  # noqa: E402
from f1.readings import bolt_at, bolt_increase_reading, measured_preload, moment_at, moment_reading  # noqa: E402
from f1.verdict import at_point, model_quantity  # noqa: E402
from fejoint import chs  # noqa: E402

GATE = JOINT / "records" / "G-F1" / "records"
DRY = JOINT / "records" / "f1_dry" / "records"
SPLICES = ("frictionless", "no-slip")
# The A325T bolts of the thesis, Table 2.2 (E, fy, eps_u) and the gate's stress area (f1/config.py).
BOLT = {"curve": "material_bolt_eng.csv", "E": 217100.0, "fy": 817.0, "eu": 0.0580, "As": 213.8}
N_YIELD_KN = BOLT["fy"] * BOLT["As"] / 1e3
REL = 1e-6
E1_EXTRA = 0.006
E3 = {"step": 0.001, "max": 0.05, "theta_stop": 0.0105}
E3_THETAS = (0.002, 0.003, 0.005, 0.0075, 0.01)
E3_RULE_THETAS = (0.005, 0.01)
E3_BOLT_MOMENTS = (100.0, 125.0, 150.0, 175.0)
FE3 = {"B-13": "B13_FE3_fig37.csv", "B-19": "B19_FE3_fig37.csv"}

_LOG = None


def log(msg: str):
    print(msg, flush=True)
    if _LOG is not None:
        with open(_LOG, "a") as f:
            f.write(msg + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def guard() -> int:
    """Every file of docs/G-F1_code.sha256 against its hash; the run stops on any difference."""
    bad, n = [], 0
    for line in (JOINT / "docs" / "G-F1_code.sha256").read_text().splitlines():
        if not line.strip():
            continue
        h, p = line.split(maxsplit=1)
        n += 1
        if sha256(JOINT / p.strip().lstrip("*")) != h:
            bad.append(p)
    if bad:
        raise SystemExit(f"the gate's code differs from docs/G-F1_code.sha256: {bad}")
    return n


def plan_hashes() -> dict:
    return {"EXPLORE_PLAN.md": sha256(HERE / "EXPLORE_PLAN.md"), "explore.py": sha256(Path(__file__))}


def require_plan_hash():
    p = HERE / "PLAN_HASH.txt"
    text = p.read_text() if p.exists() else ""
    missing = [f for f, h in plan_hashes().items() if f"{h}  {f}" not in text]
    if missing:
        raise SystemExit(f"not in PLAN_HASH.txt (hash before running; record changes in DEVIATIONS.md): {missing}")


def mesh_of(mesh: str, smoke: bool) -> str:
    return {"coarse": "tiny", "medium": "tiny-flag"}[mesh] if smoke else mesh


def write(path: Path, rec: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(rec, indent=1))
    os.replace(tmp, path)


def gate_record(spec: str, splice: str, smoke: bool, out: Path) -> dict:
    """The gate's coarse J2 nominal record (B-19: the dry run's); in smoke runs, a tiny path of the gate's code."""
    name = f"{spec}_{splice}_hencky_nominal_coarse.json"
    if not smoke:
        return json.loads(((GATE if spec == "B-13" else DRY) / name).read_text())
    p = out / "ref" / name.replace("_coarse", "_tiny")
    if p.exists():
        return json.loads(p.read_text())
    cfg = config(spec == "B-19")
    rec = R.run_path(spec, cfg, splice, "hencky", "nominal", "tiny", log=lambda m: log(f"ref {m}"))
    write(p, rec)
    return rec


def case(out: Path, cid: str, fn, cfg: dict, base: dict, extra: dict, relabel: dict | None = None) -> dict:
    path = out / "records" / f"{cid}.json"
    if path.exists():
        log(f"{path.name} exists, skipped")
        return json.loads(path.read_text())
    t0 = time.time()
    rec = fn(lambda m: log(f"{cid} {m}"))
    if relabel:
        rec["case"].update(relabel)
    rec["explore"] = {"id": cid, "plan": "probes/f1_explore/EXPLORE_PLAN.md", **extra}
    rec["config_sha256"] = hashlib.sha256(canonical(cfg).encode()).hexdigest()
    rec["base_config_sha256"] = hashlib.sha256(canonical(base).encode()).hexdigest()
    write(path, rec)
    log(json.dumps({"case_done": cid, "seconds": round(time.time() - t0, 1)}))
    return rec


def same_levels(a: dict, b: dict, skip_yield: bool = False):
    """Records a and b at their common control values (converged levels of both): M, Theta_D and the six bolt
    forces, relative to b. skip_yield leaves out levels where a bolt exceeds A_s f_yb in either record."""
    bl = {round(lv["control_value"], 10): lv for lv in b["levels"] if lv["converged"]}
    n, worst, fails = 0, 0.0, []
    for lv in a["levels"]:
        m = bl.get(round(lv["control_value"], 10))
        if m is None or not lv["converged"]:
            continue
        if skip_yield and max(max(lv["bolts_kN"]), max(m["bolts_kN"])) >= N_YIELD_KN:
            continue
        n += 1
        pairs = [("M_kNm", lv["M_kNm"], m["M_kNm"]), ("Theta_D", lv["Theta_D"], m["Theta_D"])]
        pairs += [(f"bolt{i + 1}", x, y) for i, (x, y) in enumerate(zip(lv["bolts_kN"], m["bolts_kN"]))]
        for key, x, y in pairs:
            d = abs(x - y) / max(abs(y), 1e-300)
            worst = max(worst, d)
            if d > REL:
                fails.append([lv["control_value"], key, x, y])
    return n, worst, fails


# ---------------------------------------------------------------- E1


def e1_values(gate: dict, cfg: dict) -> list:
    return sorted(set(R.bracket_values("B-13", cfg, gate)) | {E1_EXTRA})


def e1a_id(smoke):
    return f"E1a_B-13_frictionless_hencky_nominal_{mesh_of('coarse', smoke)}"


def e1a_check(out: Path, smoke: bool):
    rec = json.loads((out / "records" / f"{e1a_id(smoke)}.json").read_text())
    return same_levels(rec, gate_record("B-13", "frictionless", smoke, out))


def run_E1a(out: Path, smoke: bool, only: str | None):
    cfg = config(False)
    gate = gate_record("B-13", "frictionless", smoke, out)
    V = e1_values(gate, cfg)
    mesh = mesh_of("coarse", smoke)
    cid = e1a_id(smoke)
    if only and only not in cid:
        return
    case(out, cid, lambda lg: R.run_path("B-13", cfg, "frictionless", "hencky", "nominal", mesh, values=V, log=lg),
         cfg, cfg, {"values": V, "experiment": "E1a"})
    n, worst, fails = e1a_check(out, smoke)
    log(json.dumps({"check": "E1a", "compared_levels": n, "worst_relative": worst, "failures": fails[:12]}))
    if n == 0 or fails:
        raise SystemExit("E1a's check failed: E1 is not run (EXPLORE_PLAN.md, E1a)")


def run_E1(out: Path, smoke: bool, only: str | None):
    cfg = config(False)
    cid = f"E1_B-13_frictionless_hencky_nominal_{mesh_of('medium', smoke)}"
    if only and only not in cid:
        return
    n, _, fails = e1a_check(out, smoke)
    if n == 0 or fails:
        raise SystemExit("E1a's check has not passed: E1 is not run")
    V = e1_values(gate_record("B-13", "frictionless", smoke, out), cfg)
    mesh = mesh_of("medium", smoke)
    case(out, cid, lambda lg: R.run_path("B-13", cfg, "frictionless", "hencky", "nominal", mesh, values=V, log=lg),
         cfg, cfg, {"values": V, "experiment": "E1"})


# ---------------------------------------------------------------- E2


def e2_preloads() -> dict:
    cfg = config(False)
    mp = measured_preload(cfg["tests"]["B-13"]["bolt_forces"], cfg["points"]["B-13"]["bolt_moments_kNm"][0])
    return {"uniform-mean": float(np.mean(mp)), "uniform-100": 100.0}


def run_E2(out: Path, smoke: bool, only: str | None):
    base = config(False)
    mesh = mesh_of("coarse", smoke)
    for label, P in e2_preloads().items():
        for sp in SPLICES:
            cid = f"E2_B-13_{sp}_hencky_{label}_{mesh}"
            if only and only not in cid:
                continue
            cfg = copy.deepcopy(base)
            cfg["model"]["preload_kN"] = P

            def fn(lg, cfg=cfg, sp=sp):
                return R.run_path("B-13", cfg, sp, "hencky", "nominal", mesh, log=lg)

            case(out, cid, fn, cfg, base, {"experiment": "E2", "preload_kN": P}, relabel={"preload": label})


# ---------------------------------------------------------------- E3


def bolt_points() -> list:
    """(engineering strain, stress) of the elastic-plastic bolt from the coupon curve, by f1/materials.py's rule."""
    d = np.loadtxt(DATA / BOLT["curve"], delimiter=",", skiprows=3)
    e, s = d[:, 0], d[:, 1]
    sel = (e >= 0.004) & (e <= BOLT["eu"] + 1e-9)
    e, s = e[sel], np.maximum.accumulate(s[sel])
    pts = [(BOLT["fy"] / BOLT["E"], BOLT["fy"])]
    for ei, si in zip(e, s):
        if ei > pts[-1][0] + 1e-4 and si >= pts[-1][1]:
            pts.append((float(ei), float(si)))
    A = np.array(pts)
    idx = np.unique(np.r_[0, np.round(np.linspace(0, len(A) - 1, 14)).astype(int)])
    return [tuple(map(float, r)) for r in A[idx]]


def bolt_curve(g: chs.FlangeSplice):
    assert g.E_b == BOLT["E"] and g.As == BOLT["As"], "bolt E or area differs from the gate's"
    A = np.array(bolt_points())
    return (A[:, 0] * g.L_b / 2, A[:, 1] * g.As, 0.0)


@contextlib.contextmanager
def ep_bolts():
    """f1.run.model with the elastic-plastic bolt curve; otherwise line for line the gate's function."""
    orig = R.model

    def model(name, cfg, splice, theory, mesh):
        g = R.geometry(name, cfg)
        plate = PLATES[cfg["specimens"][name]["plate"]]
        mats = {0: material(plate, theory), 1: material(TUBE, theory), 2: material(TUBE, theory)}
        return chs.SpliceModel(g, mesh, mats=mats, splice=splice, bolt_curve=bolt_curve(g))

    R.model = model
    try:
        yield
    finally:
        R.model = orig


def e3_config(spec: str) -> dict:
    cfg = copy.deepcopy(config(spec == "B-19"))
    ld = cfg["loading"]["bending"]
    ld["step"], ld["max"] = E3["step"], E3["max"]
    cfg["points"][spec]["theta"] = E3["theta_stop"] / 1.2
    return cfg


def e3_id(spec, sp, smoke):
    return f"E3_{spec}_{sp}_hencky_nominal_{mesh_of('coarse', smoke)}_ep-bolts"


def run_E3(out: Path, smoke: bool, only: str | None):
    mesh = mesh_of("coarse", smoke)
    for spec in ("B-13", "B-19"):
        for sp in SPLICES:
            cid = e3_id(spec, sp, smoke)
            if only and only not in cid:
                continue
            base, cfg = config(spec == "B-19"), e3_config(spec)

            def fn(lg, spec=spec, cfg=cfg, sp=sp):
                with ep_bolts():
                    return R.run_path(spec, cfg, sp, "hencky", "nominal", mesh, log=lg)

            case(out, cid, fn, cfg, base, {"experiment": "E3", "bolt_points_eng": bolt_points(),
                                           "N_yield_kN": N_YIELD_KN, **E3})


# ---------------------------------------------------------------- tables


def f(x, d=2):
    return "not reached" if x is None else f"{x:.{d}f}"


def value_at(rec, key, target, vkey):
    """at_point's value, or None with the status shown ('missing': the path does not reach the point)."""
    if rec is None:
        return None, "no record"
    v, s = at_point(rec, key, target, vkey)
    return (v, "") if s == "ok" else (None, s)


def fmt_vs(vs, d=1):
    v, s = vs
    return f"{v:.{d}f}" if v is not None else (s if s != "missing" else "not reached")


def tables(out: Path, smoke: bool) -> str:
    recs = {p.stem: json.loads(p.read_text()) for p in sorted((out / "records").glob("*.json"))}
    c13, c19 = config(False), config(True)
    L = ["# G-F1 exploratory runs: results", "",
         "Exploratory, after the verdict and not pre-registered (`EXPLORE_PLAN.md`). Written by "
         "`python probes/f1_explore/explore.py tables`." + (" SMOKE RUN: numbers not used." if smoke else ""), ""]
    if (HERE / "DEVIATIONS.md").exists() and not smoke:
        L += ["Deviations from the plan: see `DEVIATIONS.md`.", ""]
    L += ["## Cases", "", "| Case | Levels | All converged, KKT ok | Last control | Last Theta_D (rad) | Last M (kNm) | s |",
          "|---|---|---|---|---|---|---|"]
    for k, r in recs.items():
        lv = r["levels"]
        ok = bool(r["preload"].get("converged")) and all(x["converged"] and x["kkt_ok"] for x in lv)
        L.append(f"| {k} | {len(lv)} | {ok} | {lv[-1]['control_value'] if lv else '-'} | "
                 f"{f(lv[-1]['Theta_D'], 5) if lv else '-'} | {f(lv[-1]['M_kNm'], 1) if lv else '-'} | {r['seconds']} |")
    test_c3 = bolt_increase_reading(c13["tests"]["B-13"]["bolt_forces"], *c13["points"]["B-13"]["bolt_moments_kNm"])
    edge = test_c3["value"] - test_c3["tolerance"]

    # E1
    L += ["", "## E1. The mesh and C3", ""]
    ia, im = e1a_id(smoke), f"E1_B-13_frictionless_hencky_nominal_{mesh_of('medium', smoke)}"
    if ia in recs:
        n, worst, fails = e1a_check(out, smoke)
        L.append(f"E1a check: {n} common levels, largest relative difference {worst:.2e}; "
                 f"{'passed' if n and not fails else 'FAILED'}.")
        if n and not fails and im in recs:
            gr = gate_record("B-13", "frictionless", smoke, out)
            c3c, _ = model_quantity(gr, "B-13", c13, "C3")
            c1c, _ = model_quantity(gr, "B-13", c13, "C1")
            c3m, s3 = model_quantity(recs[im], "B-13", c13, "C3")
            c1m, s1 = model_quantity(recs[im], "B-13", c13, "C1")
            b = {(k, M): at_point(r, "M_kNm", M, "bolt1_kN")[0] for k, r in (("coarse", gr), ("medium", recs[im]))
                 for M in (25.0, 100.0)}
            L += ["", "| | Coarse (gate) | Medium | Medium / coarse |", "|---|---|---|---|",
                  f"| C3 (kN) | {f(c3c)} | {f(c3m)} ({s3}) | {f(c3m / c3c if c3m else None, 4)} |",
                  f"| C1 (kNm) | {f(c1c)} | {f(c1m)} ({s1}) | {f(c1m / c1c if c1m else None, 4)} |",
                  f"| Bolt 1 at 25 kNm (kN) | {f(b['coarse', 25.0])} | {f(b['medium', 25.0])} | |",
                  f"| Bolt 1 at 100 kNm (kN) | {f(b['coarse', 100.0])} | {f(b['medium', 100.0])} | |", "",
                  "Plastic points (plate, tube, weld, bolts) at each medium level: "
                  + "; ".join(f"{x['control_value']}: {x['plastic_points']}" for x in recs[im]["levels"]) + ".", "",
                  "Elastic mesh flag of the gate for this quantity: 1.0177."]
            if c3m is not None:
                if c3m >= edge:
                    rd = f"the medium C3 is at least {edge:.2f} kN: the mesh alone can account for the miss."
                elif abs(c3m - c3c) < 1.5:
                    rd = "the medium C3 lies within 1.5 kN of the coarse value: the mesh is not the main cause."
                else:
                    rd = "neither condition holds; reported as found, without a reading."
                L += ["", f"**Reading by the plan's rule** (test less tolerance {edge:.2f} kN): {rd}"]
    # E2
    L += ["", "## E2. One preload value in every bolt", ""]
    P = e2_preloads()
    mesh = mesh_of("coarse", smoke)
    rows, vals = [], {}
    for sp in SPLICES:
        srcs = [("nominal 125 kN (gate)", gate_record("B-13", sp, smoke, out), 125.0)]
        if not smoke:
            srcs.append(("measured (gate)", json.loads((GATE / f"B-13_{sp}_hencky_measured_coarse.json").read_text()),
                         None))
        for label, p in P.items():
            k = f"E2_B-13_{sp}_hencky_{label}_{mesh}"
            if k in recs:
                srcs.append((f"{label} ({p:.2f} kN)", recs[k], p))
        for name, r, p in srcs:
            c1, _ = model_quantity(r, "B-13", c13, "C1")
            c3, _ = model_quantity(r, "B-13", c13, "C3")
            m5, _ = model_quantity(r, "B-13", c13, "C1", theta=0.0005)
            vals[sp, name.split(" ")[0]] = (c1, c3, p)
            rows.append(f"| {sp} | {name} | {f(c1)} | {f(c3)} | {f(m5)} |")
    L += ["| Bound | Preload | C1 (kNm) | C3 (kN) | M at 0.0005 rad (kNm) |", "|---|---|---|---|---|"] + rows
    if all((sp, "uniform-mean") in vals and (sp, "measured") in vals for sp in SPLICES):
        ok = all(vals[sp, "uniform-mean"][1] is not None and vals[sp, "measured"][1] is not None
                 and abs(vals[sp, "uniform-mean"][1] - vals[sp, "measured"][1]) <= 1.0
                 and abs(vals[sp, "uniform-mean"][0] - vals[sp, "measured"][0]) <= 1.0 for sp in SPLICES)
        L += ["", "**Reading (i)**: " + ("for both bounds C3 within 1 kN and C1 within 1 kNm of the measured-preload "
              "values: one preload value reproduces the uneven set for these quantities." if ok else
              "not both within 1 kN and 1 kNm: the unevenness matters (see the table for which quantity and bound).")]
    pts = sorted((v[2], v[1]) for (sp, nm), v in vals.items() if sp == "frictionless" and v[2] is not None
                 and v[1] is not None)
    if len(pts) == 3:
        Ps, Cs = np.array([p for p, _ in pts]), np.array([c for _, c in pts])
        star = None
        for i in range(2):
            if (Cs[i] - edge) * (Cs[i + 1] - edge) <= 0 and Cs[i] != Cs[i + 1]:
                star = Ps[i] + (edge - Cs[i]) * (Ps[i + 1] - Ps[i]) / (Cs[i + 1] - Cs[i])
        lower = all(vals["no-slip", nm][1] is not None and vals["frictionless", nm][1] is not None
                    and vals["no-slip", nm][1] < vals["frictionless", nm][1]
                    for nm in ("nominal", "uniform-mean", "uniform-100") if ("no-slip", nm) in vals)
        L += ["", "**Reading (ii)**: " + (f"P* = {round(star * 2) / 2:.1f} kN" if star is not None else
              "the frictionless C3 does not cross the edge between 100 and 125 kN")
              + f" (edge {edge:.2f} kN); the no-slip C3 {'stays' if lower else 'does not stay'} the lower value."]
    # E3
    L += ["", "## E3. Towards the resistance", ""]
    e3 = {(s, sp): recs.get(e3_id(s, sp, smoke)) for s in ("B-13", "B-19") for sp in SPLICES}
    checks, good = [], True
    for (s, sp), r in e3.items():
        if r is None:
            continue
        n, worst, fails = same_levels(r, gate_record(s, sp, smoke, out), skip_yield=True)
        good &= bool(n) and not fails
        checks.append(f"{s} {sp}: {n} common levels below bolt yield, largest relative difference {worst:.2e}"
                      + ("" if n and not fails else f"; FAILED {fails[:4]}"))
    L += ["Check against the gate's records (dry run for B-19): " + "; ".join(checks) + "."]
    if not good:
        L += ["", "**The check failed: nothing else of E3 is read (EXPLORE_PLAN.md, E3).**"]
        return "\n".join(L) + "\n"
    ratios = {}
    for s in ("B-13", "B-19"):
        cfg = c13 if s == "B-13" else c19
        files = cfg["tests"][s]["moment_rotation"]
        L += ["", f"### {s}", "", "| Theta_D (rad) | Test (kNm) | Author FE (3) | Frictionless | r | No-slip | r |",
              "|---|---|---|---|---|---|---|"]
        for th in E3_THETAS:
            t = moment_reading(files, th)["value"]
            a = moment_at(FE3[s], th)
            mv = {sp: value_at(e3[s, sp], "Theta_D", th, "M_kNm") for sp in SPLICES}
            for sp in SPLICES:
                ratios[s, sp, th] = None if mv[sp][0] is None else mv[sp][0] / t
            L.append(f"| {th} | {t:.1f} | {a:.1f} ({a / t:.2f}) | {fmt_vs(mv['frictionless'])} | "
                     f"{f(ratios[s, 'frictionless', th])} | {fmt_vs(mv['no-slip'])} | {f(ratios[s, 'no-slip', th])} |")
        L += ["", "| M (kNm) | Test bolt 1 (upper dotted, kN) | Frictionless | No-slip |", "|---|---|---|---|"]
        for M in E3_BOLT_MOMENTS:
            try:
                tb = bolt_at(cfg["tests"][s]["bolt_forces"], "1-2 upper", M)
            except ValueError:
                tb = None
            mb = {sp: value_at(e3[s, sp], "M_kNm", M, "bolt1_kN") for sp in SPLICES}
            if tb is None and all(v[0] is None for v in mb.values()):
                continue
            L.append(f"| {M:.0f} | {f(tb, 1)} | {fmt_vs(mb['frictionless'])} | {fmt_vs(mb['no-slip'])} |")
        for sp in SPLICES:
            r = e3[s, sp]
            if r is None:
                continue
            lv = r["levels"]
            y = next((x for x in lv if x["converged"] and max(x["bolts_kN"]) >= N_YIELD_KN), None)
            drops = []
            for i in range(6):
                fs = [x["bolts_kN"][i] for x in lv if x["converged"]]
                j = next((k for k, v in enumerate(fs) if v >= N_YIELD_KN), None)
                if j is not None and any(fs[k + 1] < fs[k] * (1 - 1e-9) for k in range(j, len(fs) - 1)):
                    drops.append(i + 1)
            L += ["", f"{sp}: first level with a bolt above {N_YIELD_KN:.1f} kN: "
                  + (f"control {y['control_value']}, M {y['M_kNm']:.1f} kNm, Theta_D {y['Theta_D']:.5f} rad"
                     if y else "none") + f"; plastic points at the last level {lv[-1]['plastic_points']}; "
                  + (f"yielded bolts whose force fell along the path: {drops}" if drops else
                     "no yielded bolt's force fell along the path") + "."]
    hold = {sp: all(ratios.get((s, sp, th)) is not None and 0.90 <= ratios[s, sp, th] <= 1.10
                    for s in ("B-13", "B-19") for th in E3_RULE_THETAS) for sp in SPLICES}
    pause = any(all(ratios.get((s, sp, 0.01)) is None or not 0.90 <= ratios[s, sp, 0.01] <= 1.10 for sp in SPLICES)
                for s in ("B-13", "B-19"))
    if hold["frictionless"] and not hold["no-slip"]:
        out_ = "frictionless holds and no-slip does not: train both bounds (envelope)."
    elif hold["frictionless"] and hold["no-slip"]:
        out_ = "both hold: train both bounds; friction governs the stiffness but not the resistance."
    elif hold["no-slip"]:
        out_ = "no-slip holds and frictionless does not: train the no-slip bound only."
    elif pause:
        out_ = "for B-13 or B-19 neither bound lies within [0.90, 1.10] at 0.01 rad: no surrogate yet."
    else:
        out_ = "another outcome: train both bounds, with the ratios reported."
    L += ["", f"**Rule for the reference energy** (ratios at {E3_RULE_THETAS} rad, both specimens; holds = all four "
          f"within [0.90, 1.10]): frictionless {'holds' if hold['frictionless'] else 'does not hold'}, no-slip "
          f"{'holds' if hold['no-slip'] else 'does not hold'}. Outcome: {out_} The rule informs the owner's choice; "
          "it does not make it."]
    return "\n".join(L) + "\n"


def main(argv=None):
    global _LOG
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=["run", "tables"])
    ap.add_argument("experiments", nargs="*")
    ap.add_argument("--case", default=None)
    ap.add_argument("--out", default=str(HERE))
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out).resolve()
    if a.smoke and out == HERE:
        raise SystemExit("--smoke needs an --out outside probes/f1_explore")
    out.mkdir(parents=True, exist_ok=True)
    n = guard()
    if not a.smoke:
        require_plan_hash()
    if a.command == "tables":
        text = tables(out, a.smoke)
        (out / "RESULTS.md").write_text(text)
        print(text)
        return
    _LOG = out / "run.log"
    log(f"# {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC: explore.py run {' '.join(a.experiments)}"
        + (f" --case {a.case}" if a.case else "") + (" --smoke" if a.smoke else "")
        + f"; gate code checked ({n} files); plan {plan_hashes()['EXPLORE_PLAN.md'][:12]}, "
        f"explore.py {plan_hashes()['explore.py'][:12]}")
    runners = {"E1a": run_E1a, "E1": run_E1, "E2": run_E2, "E3": run_E3}
    for e in a.experiments:
        runners[e](out, a.smoke, a.case)
    log(f"# {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC: done")


if __name__ == "__main__":
    main()
