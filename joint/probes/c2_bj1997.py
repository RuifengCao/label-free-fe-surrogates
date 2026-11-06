"""T-stubs T1 and T2 of Bursi and Jaspart (1997) with the plastic reference model of stage C2 (fejoint.tstub_pl):
deformation theory and flow theory, preloaded or not, under a prescribed displacement of the web's end.

Usage, from joint/:  python probes/c2_bj1997.py . --spec T1 --modes hencky,flow --h 5 --ntf 2 --out RUN.json
The laws are the authors' nominal ones, read by eye from their Fig. 8(a) (T1) and Fig. 15(a) (T2). Each row of
the output gives the end displacement beyond the preloaded state, the force, the web deformation at x_meas (the
reading of their Fig. 10), the bolt force, and the solver's convergence and optimality residuals. Compare with the
tests by probes/c2_bj1997_compare.py."""
import sys, time, json, argparse
sys.path.insert(0, sys.argv[1])
import numpy as np
from fejoint.tstub import TStubPair
from fejoint.tstub_pl import PlasticTStubModel
from fejoint.plasticity import Material, Hardening
ap = argparse.ArgumentParser()
ap.add_argument("repo"); ap.add_argument("--spec", default="T1"); ap.add_argument("--preload", type=float, default=60.7e3)
ap.add_argument("--modes", default="hencky,flow"); ap.add_argument("--h", type=float, default=5.0); ap.add_argument("--ntf", type=int, default=2)
ap.add_argument("--out", required=True); ap.add_argument("--levels", default="0.05,0.1,0.2,0.3,0.4,0.5,0.6,0.75,1.0,1.25,1.5,2.0,2.5,3.0,4.0,5.0")
ap.add_argument("--elastic_bolts", action="store_true")
a = ap.parse_args()
E = 210000.0
REG = 1e-4 * E                                   # slope added to plateaus (regulariser), MPa
def hard(points):
    al = np.array([max(e - s / E, 0.0) for e, s in points]); al[0] = 0.0
    sg = np.array([s for _, s in points], float) + REG * al
    return Hardening(al, sg, h_end=REG)
# Fig. 8(a) (T1) and Fig. 15(a) (T2), nominal laws, read by eye (+-10 MPa, +-0.005)
MAT = {"T1": {"flange": [(431 / E, 431), (0.020, 431), (0.100, 520), (0.170, 568), (0.335, 595)],
              "web": [(469 / E, 469), (0.020, 469), (0.100, 535), (0.170, 568), (0.335, 590)],
              "bolt": [(893 / E, 893), (0.020, 893), (0.040, 950), (0.060, 975)]},
       "T2": {"flange": [(282 / E, 282), (0.015, 282), (0.090, 385), (0.170, 433), (0.330, 480)],
              "web": [(290 / E, 290), (0.015, 290), (0.090, 400), (0.170, 447), (0.330, 497)],
              "bolt": [(795 / E, 795), (0.018, 795), (0.040, 880), (0.060, 905)]}}
GEO = {"T1": TStubPair(t_f=10.7, t_w=7.1, b=150.0, L=80.0, w=90.0, bolt_y=(20.0,), H=220.0, corner="root", r=15.0,
                       d=12.0, As=84.3, head=7.5, nut=10.8, bearing_r=12.0, n_washers=2, washer_t=2.5, x_meas=150.0),
       "T2": TStubPair(t_f=16.0, t_w=9.5, b=150.0, L=80.0, w=90.0, bolt_y=(20.0,), H=220.0, corner="root", r=18.0,
                       d=12.0, As=84.3, head=7.5, nut=10.8, bearing_r=8.3, n_washers=1, washer_t=2.5, x_meas=35.0)}
g = GEO[a.spec]; mp = MAT[a.spec]
mf, mw = Material(E, 0.3, hard(mp["flange"])), Material(E, 0.3, hard(mp["web"]))
levels = [float(v) for v in a.levels.split(",")]
res = {"spec": a.spec, "preload_N": a.preload, "mesh": {"h": a.h, "n_tf": a.ntf}, "material_points": mp,
       "plateau_regulariser_MPa": REG, "curves": {}}
for mode in a.modes.split(","):
    m0 = PlasticTStubModel(g, mf, mw, h=a.h, n_tf=a.ntf, control="displacement")
    Lh = g.L_b / 2
    bc = None
    if not a.elastic_bolts:
        pts = [(s / E * Lh, s * g.As) for e, s in mp["bolt"][:1]] + [(e * Lh, s * g.As + REG * g.As * (e - mp["bolt"][0][0]))
                                                                    for e, s in mp["bolt"][1:]]
        e_pts, N_pts = np.array([p[0] for p in pts]), np.array([p[1] for p in pts])
        e_pts[0] = N_pts[0] / m0.k_ax                  # yield extension from the spring's own stiffness
        bc = (e_pts, N_pts, REG * g.As / Lh)
    m = PlasticTStubModel(g, mf, mw, h=a.h, n_tf=a.ntf, control="displacement", bolt_curve=bc)
    t0 = time.time()
    pre = m.set_preload(a.preload, mode=mode)
    if mode == "flow":
        m.commit()
    u = (m.T_phys @ m.z).reshape(-1, 3)
    d0 = float(u[m.endn, 0] @ m.end_w)
    rows = []
    for d in levels:
        t1 = time.time()
        z, rep = m.solve(d0 + d, mode=mode)
        r = m.readings(z, rep)
        if mode == "flow":
            m.commit()
        row = {"d_mm": d, "F_kN": r["F_N"] / 1e3, "Delta_web_mm": r["Delta_web_mm"], "bolt_kN": r["bolt_force_N"][0] / 1e3,
               "iterations": r["iterations"], "converged": r["converged"], "plastic_points": r["plastic_points"],
               "kkt_max": max(abs(v) for v in r["kkt"].values()), "seconds": round(time.time() - t1, 1)}
        rows.append(row)
        print(mode, json.dumps(row), flush=True)
    res["curves"][mode] = {"preload": {"delta": pre["delta"]}, "d0_mm": d0, "rows": rows, "bolt_curve": None if bc is None else
                           {"e": list(map(float, bc[0])), "N": list(map(float, bc[1])), "slope_end": float(bc[2])},
                           "seconds": round(time.time() - t0, 1)}
    json.dump(res, open(a.out, "w"), indent=1)
print("done", flush=True)
