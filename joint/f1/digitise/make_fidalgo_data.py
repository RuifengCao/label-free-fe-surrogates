"""Reproduce the digitised Fidalgo (2023) data from the thesis PDF.

Usage: python -I make_fidalgo_data.py THESIS_PDF OUT_DIR
Needs pdfimages (poppler), numpy, scipy, scikit-image, Pillow, and digi.py, boltforce.py
next to this file. Writes the CSV files and summary JSON files into OUT_DIR.
"""
import sys, os, json, subprocess, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from digi import load, calibrate, extract, resample, smooth
from boltforce import points, split_dotted, split_track
from axial import two_lines  # noqa: F401

pdf, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
tmp = tempfile.mkdtemp()

def page_images(page):
    d = os.path.join(tmp, f'p{page}')
    os.makedirs(d, exist_ok=True)
    subprocess.run(['pdfimages', '-png', '-f', str(page), '-l', str(page), pdf, os.path.join(d, 'im')], check=True)
    return sorted(os.path.join(d, f) for f in os.listdir(d))

# PDF page numbers (thesis page + 16)
fig33 = page_images(64)[0]
fig34a, fig34b = page_images(65)[:2]
fig37a, fig37b = page_images(67)[:2]
fig218 = page_images(45)[:4]

def clean(x, y, n=110):
    x, y = np.array(x), np.array(y)
    xs, ys = resample(x, y, 400)
    xs, ys = smooth(xs, 7), smooth(ys, 7)
    xs[-1], ys[-1] = x[-1], y[-1]
    xs, ys = resample(xs, ys, n)
    return np.concatenate([[0.0], xs]), np.concatenate([[0.0], ys])

# moment-rotation
MT = {}
a = load(fig33); cal = calibrate(a, [0, .01, .02, .03, .04, .05], [0, 50, 100, 150, 200, 250, 300, 350], verbose=False)
leg = (0.0395, 0.051, -5, 120)
MT['B19_test_fig33'] = extract(a, 'red', cal, excl=[leg])[:2]
MT['B13_test_fig33'] = extract(a, 'black', cal, excl=[leg, (0.0350, 0.0425, 222, 256), (0.0183, 0.0250, 280, 312)])[:2]
for sp, f in (('B13', fig37a), ('B19', fig37b)):
    a = load(f); cal = calibrate(a, [0, .015, .03, .045], [0, 50, 100, 150, 200, 250, 300, 350], verbose=False)
    leg = (0.0255, 0.046, -5, 130)
    MT[f'{sp}_test_fig37'] = extract(a, 'red', cal, excl=[leg])[:2]
    MT[f'{sp}_FE3_fig37'] = extract(a, 'cyan', cal, excl=[leg])[:2]
summ = {}
for k, (x, y) in sorted(MT.items()):
    xs, ys = clean(x, y)
    src = 'Fig. 3.3' if 'fig33' in k else 'Fig. 3.7'
    with open(os.path.join(out, f'{k}.csv'), 'w') as fh:
        fh.write(f'# Fidalgo (2023) PhD thesis, University of Toronto, {src}; digitised 6 November 2026 from the embedded chart image\n')
        fh.write('# theta in rad, M in kNm; first row is the origin added by hand; resolution about 8e-5 rad and 0.7 kNm per pixel\n')
        fh.write('theta_rad,M_kNm\n')
        for p, q in zip(xs, ys):
            fh.write(f'{p:.6f},{q:.2f}\n')
    j = int(np.argmax(ys)); rx, ry = xs[:j + 1], np.maximum.accumulate(ys[:j + 1])
    lv = [50, 100, 150, 200, 225] if k.startswith('B13') else [50, 100, 150, 200, 250, 275, 290]
    th = [0.001, 0.002, 0.005, 0.01, 0.015, 0.02, 0.03] if k.startswith('B13') else [0.001, 0.002, 0.005, 0.01, 0.015]
    summ[k] = dict(peak=(round(float(xs[j]), 5), round(float(ys[j]), 1)), end=(round(float(xs[-1]), 5), round(float(ys[-1]), 1)),
                   theta_at_M={str(M): round(float(np.interp(M, ry, rx)), 5) for M in lv},
                   M_at_theta={str(t): round(float(np.interp(t, xs[:j + 1], ys[:j + 1])), 1) for t in th if t <= xs[j]})
json.dump(summ, open(os.path.join(out, 'summary_mtheta.json'), 'w'), indent=1)

# materials
T22 = {'plate19': dict(E=204500, Fy=373, Fu=475, eu=0.1764, w=0.0, fig='2.18(a)'),
       'plate13': dict(E=201000, Fy=397, Fu=484, eu=0.1335, w=0.4, fig='2.18(b)'),
       'chs': dict(E=191700, Fy=380, Fu=446, eu=0.1545, w=0.5, fig='2.18(c)'),
       'bolt': dict(E=217100, Fy=817, Fu=947, eu=0.0580, w=0.0, fig='2.18(d)')}
axes = {'plate19': ([0, .1, .2, .3, .4, .5], [0, 150, 300, 450, 600], (0.29, 0.51, -10, 165)),
        'plate13': ([0, .1, .2, .3, .4, .5], [0, 150, 300, 450, 600], (0.29, 0.51, -10, 165)),
        'chs': ([0, .1, .2, .3, .4, .5], [0, 150, 300, 450, 600], (0.29, 0.51, -10, 165)),
        'bolt': ([0, .05, .1, .15, .2, .25, .3], [0, 200, 400, 600, 800, 1000], (0.15, 0.31, -10, 330))}
msum = {}
for (k, f) in zip(['plate19', 'plate13', 'chs', 'bolt'], fig218):
    xv, yv, leg = axes[k]
    a = load(f); cal = calibrate(a, xv, yv, verbose=False)
    x, y, _ = extract(a, 'cyan', cal, excl=[leg], margin=2)
    xs, ys = resample(x, y, 500); xs, ys = smooth(xs, 7), smooth(ys, 7); xs, ys = resample(xs, ys, 160)
    keep = np.concatenate([[True], np.diff(xs) > 0]); xs, ys = xs[keep], ys[keep]
    p = T22[k]
    with open(os.path.join(out, f'material_{k}_eng.csv'), 'w') as fh:
        fh.write(f"# Fidalgo (2023), Fig. {p['fig']}, FE coupon curve (cyan, w = {p['w']}); digitised 6 November 2026\n")
        fh.write('# engineering strain, engineering stress in MPa; the elastic branch is below the resolution (about 0.0009 strain per pixel); use E from Table 2.2\n')
        fh.write('eng_strain,eng_stress_MPa\n')
        for q, r in zip(xs, ys):
            fh.write(f'{q:.5f},{r:.1f}\n')
    pts = [e for e in [0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.125, 0.15] if e < p['eu']] + [p['eu']]
    msum[k] = dict(max_eng=(round(float(xs[np.argmax(ys)]), 4), round(float(ys.max()), 1)),
                   eng_at=[(e, round(float(np.interp(e, xs, ys)), 1)) for e in pts],
                   true_at=[(round(float(np.log1p(e)), 4), round(float(np.interp(e, xs, ys) * (1 + e)), 1)) for e in pts])
json.dump(msum, open(os.path.join(out, 'summary_materials.json'), 'w'), indent=1)

# bolt forces
EX = {'B13': (fig34a, 144, [(215, 330, -5, 70), (225, 250, 198, 222), (108, 128, 195, 222), (150, 170, 168, 186), (150, 170, 147, 168), (152, 170, 112, 132), (150, 180, 84, 100), (146, 152, 160, 200), (128, 139.5, 194, 210)]),
      'B19': (fig34b, 201, [(215, 330, -5, 70), (288, 305, 200, 222), (176, 192, 198, 216), (200, 226, 170, 186), (200, 226, 108, 128), (100, 124, 98, 114), (204, 230, 140, 160), (189, 196, 193.5, 205)])}
bsum = {}
for sp, (f, Mend, ex) in EX.items():
    a = load(f); cal = calibrate(a, list(range(0, 326, 25)), list(range(0, 226, 25)), verbose=False)
    P = points(a, 'black', cal, ex); P = P[P[:, 0] <= Mend]
    up, lo = split_dotted(P)
    cy = split_track(points(a, 'cyan', cal, ex), Mmax=Mend)
    rd = split_track(points(a, 'red', cal, ex), Mmax=Mend)
    rows = [('1-2 upper', m, b) for m, b in up] + [('1-2 lower', m, b) for m, b in lo]
    rows += [('3', m, u) for m, u, l in cy] + [('4', m, l) for m, u, l in cy]
    rows += [('5-6 upper', m, u) for m, u, l in rd] + [('5-6 lower', m, l) for m, u, l in rd]
    with open(os.path.join(out, f'boltforce_{sp}.csv'), 'w') as fh:
        fh.write(f"# Fidalgo (2023), Fig. 3.4({'a' if sp == 'B13' else 'b'}), bolt force B (kN) against applied moment Mf (kNm), bolts 1 to 6; digitised 6 November 2026\n")
        fh.write('# 1-2 upper/lower: the two dotted series split by a moving median; above about 75 kNm the upper one is bolt 1 (figure labels); below that they overlap\n')
        fh.write('# 3 and 4: cyan solid lines, 3 above 4 (figure labels); 5-6 upper/lower: not labelled separately in the figure\n')
        fh.write('# resolution about 0.58 kNm and 0.56 kN per pixel; bolt forces were measured only up to 180 kN for safety (thesis p. 48)\n')
        fh.write('series,M_kNm,B_kN\n')
        for s, m, b in rows:
            fh.write(f'{s},{m:.1f},{b:.1f}\n')
    at = lambda arr, col, M: round(float(np.interp(M, arr[:, 0], arr[:, col])), 1)
    Ms = [0, 25, 50, 75, 100, 125, 140] if sp == 'B13' else [0, 25, 50, 75, 100, 150, 195]
    bsum[sp] = {str(M): dict(upper12=at(up, 1, M), lower12=at(lo, 1, M), b3=at(cy, 1, M), b4=at(cy, 2, M), up56=at(rd, 1, M), lo56=at(rd, 2, M)) for M in Ms}
    bsum[sp]['last'] = dict(upper12=up[-1].round(1).tolist(), lower12=lo[-1].round(1).tolist(), b3=cy[-1, [0, 1]].round(1).tolist(), b4=cy[-1, [0, 2]].round(1).tolist())
json.dump(bsum, open(os.path.join(out, 'summary_boltforce.json'), 'w'), indent=1)
# axial tests: rows where both LVDT lines are found (Fig. 2.5: T-13 black, T-19 red; Fig. 2.22: red)
from axial import two_lines
fig25 = page_images(31)[0]
fig222a, fig222b = page_images(50)[:2]
for name, f, kind, ex, lo, hi, src in [
        ('T13_test_fig25', fig25, 'black', [(23.5, 30.5, 1300, 2000), (21, 30.5, 0, 700)], 700, 950, 'Fig. 2.5 (black: LVDT-C dashed, LVDT-T solid)'),
        ('T13_test_fig222', fig222a, 'red', [(18.5, 30.5, 0, 760)], 700, 950, 'Fig. 2.22(a) (red: North dashed, South solid)'),
        ('T19_test_fig25', fig25, 'red', [(21, 30.5, 0, 700)], 1050, 1550, 'Fig. 2.5 (red: LVDT-C dashed, LVDT-T solid)'),
        ('T19_test_fig222', fig222b, 'red', [(18.5, 30.5, 0, 760)], 1050, 1550, 'Fig. 2.22(b) (red: North dashed, South solid)')]:
    pl, pr, R, res, sc = two_lines(f, kind, lo, hi, ex)
    with open(os.path.join(out, f'{name}.csv'), 'w') as fh:
        fh.write(f'# Fidalgo (2023), {src}; digitised 7 November 2026: pixel rows between {lo} and {hi} kN where both LVDT lines are found\n')
        fh.write('# load in kN, displacement of the left and the right line in mm (which LVDT is which is not needed: the gate uses their mean); about 0.044 mm per pixel\n')
        fh.write('T_kN,delta_left_mm,delta_right_mm\n')
        for T, xl, xr in R:
            fh.write(f'{T:.2f},{xl:.4f},{xr:.4f}\n')
shutil.rmtree(tmp)
print('wrote', len(os.listdir(out)), 'files to', out)
