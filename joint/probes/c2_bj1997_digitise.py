"""Digitise Fig. 10 of Bursi and Jaspart (1997) (preloaded T1) from a 300 dpi greyscale image of the printed page
(page 18 of the PDF; the image is not kept in the repository). Usage, from joint/:
    python probes/c2_bj1997_digitise.py PAGE18.png
Prints the lower envelope (the experimental curve) and the upper envelope (the authors' two simulations) of the
dark pixels at the displacements of probes/c2_bj1997_fig10.json. Calibration, in pixels of the crop: x = 0 mm at
column 28, x = 16 mm at column 587; F = 0 at row 598.5, F = 250 kN at row 33.5. The legend box and the 15 rows above
the axis (tick marks) are masked; at 0.5 mm the simulations rise steeply, so only the lower envelope is read there."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

CROP = (690, 1800, 1310, 2420)
X0, X16, Y0, Y250 = 28.0, 587.0, 598.5, 33.5
LEGEND = (228, 435, 620, 620)          # columns and rows of the crop covered by the legend box (masked)
THR = 110

a = np.asarray(Image.open(sys.argv[1]).convert("L").crop(CROP), dtype=float)
dark = a < THR
fig = json.loads((Path(__file__).parent / "c2_bj1997_fig10.json").read_text())
print("Delta_mm  lower_kN  upper_kN")
for D in fig["Delta_mm"]:
    c = int(round(X0 + D / 16.0 * (X16 - X0)))
    lo, hi = [], []
    for cc in (c - 1, c, c + 1):
        rows = np.nonzero(dark[int(Y250) + 4:int(Y0) - 15, cc])[0] + int(Y250) + 4
        if LEGEND[0] <= cc <= LEGEND[2]:
            rows = rows[rows < LEGEND[1]]
        if rows.size:
            lo.append(rows.max()); hi.append(rows.min())
    f = lambda r: (Y0 - r) / (Y0 - Y250) * 250.0  # noqa: E731
    print(f"{D:8.1f}  {f(np.mean(lo)):8.1f}  {f(np.mean(hi)):8.1f}")
