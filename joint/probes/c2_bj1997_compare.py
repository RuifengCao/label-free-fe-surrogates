"""Force of the reference model of stage C2 against Bursi and Jaspart's T1 test and their simulations (Fig. 10),
at the digitised displacements. Usage, from joint/: python probes/c2_bj1997_compare.py RUN.json [RUN.json ...]
(the outputs of probes/c2_bj1997.py). The model's force is interpolated linearly in its web deformation; a reading
beyond the model's last point is left out."""
import json
import sys
from pathlib import Path

import numpy as np

fig = json.loads((Path(__file__).parent / "c2_bj1997_fig10.json").read_text())
for path in sys.argv[1:]:
    r = json.loads(Path(path).read_text())
    for mode, c in r["curves"].items():
        x = np.array([row["Delta_web_mm"] for row in c["rows"]])
        F = np.array([row["F_kN"] for row in c["rows"]])
        print(f"{Path(path).name} {mode} mesh h {r['mesh']['h']} n_tf {r['mesh']['n_tf']}")
        print("Delta_mm  model_kN  test_kN  model/test  authors_kN  model/authors")
        for D, t, a in zip(fig["Delta_mm"], fig["test_kN"], fig["authors_fe_kN"]):
            if D > x.max():
                continue
            m = float(np.interp(D, x, F))
            ra = f"{m / a:10.3f}" if a else "         -"
            print(f"{D:8.1f}  {m:8.1f}  {t:7.0f}  {m / t:10.3f}  {a if a else '-':>10}  {ra}")
