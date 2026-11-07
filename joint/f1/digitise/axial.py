"""Axial test curves (Fidalgo 2023, Fig. 2.5: T-13 black, T-19 red; LVDT-C dashed, LVDT-T solid; and Fig. 2.22,
red, North dashed and South solid): the mean of the two LVDT readings at each load level. At each load, the pixel
rows within +-2 rows are scanned for runs of the series colour; run centres are clustered (a gap of more than 3 px
separates two lines) and the mean of the (at most two) cluster centres is the mean displacement."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from digi import load, calibrate, colour_mask


def mean_curve(path, kind, loads, x_range=(0.0, 30.0), excl=(), band=2):
    a = load(path)
    fx, fy, box, sc = calibrate(a, list(range(0, 31, 5)) if 'im-000' in os.path.basename(path) and 'emb31' in path
                                else list(range(0, 31, 2)), list(range(0, 2001, 200)), verbose=False)
    m = colour_mask(a, kind)
    m[:int(box['top']) + 3] = False; m[int(box['bottom']) - 2:] = False
    m[:, :int(box['left']) + 3] = False; m[:, int(box['right']) - 2:] = False
    if kind == 'black':
        for g in box['gx']: m[:, int(round(g)) - 2:int(round(g)) + 3] = False
        for g in box['gy']: m[int(round(g)) - 2:int(round(g)) + 3, :] = False
    c = np.arange(a.shape[1]); r = np.arange(a.shape[0])
    ay = np.polyfit(fy(r), r, 1)
    out = []
    for T in loads:
        row = int(round(np.polyval(ay, T)))
        cents = []
        for rr in range(row - band, row + band + 1):
            cols = np.nonzero(m[rr])[0]
            xs = fx(cols)
            keep = (xs >= x_range[0]) & (xs <= x_range[1])
            for (x0, x1, y0, y1) in excl:
                keep &= ~((xs >= x0) & (xs <= x1) & (T >= y0) & (T <= y1))
            cols = cols[keep]
            if cols.size == 0:
                continue
            runs = np.split(cols, np.where(np.diff(cols) > 1)[0] + 1)
            cents += [float(run.mean()) for run in runs]
        if not cents:
            out.append((T, np.nan, np.nan, np.nan, 0)); continue
        cents = np.sort(np.array(cents))
        groups = np.split(cents, np.where(np.diff(cents) > 3)[0] + 1)
        centres = [float(np.median(gg)) for gg in groups]
        if len(centres) > 2:            # keep the two largest groups
            sizes = [len(gg) for gg in groups]
            idx = sorted(np.argsort(sizes)[-2:])
            centres = [centres[i] for i in idx]
        xs = [float(fx(cc)) for cc in centres]
        if len(xs) == 1:
            xs = xs * 2
        out.append((T, float(np.mean(xs)), xs[0], xs[1], len(groups)))
    return out, sc


if __name__ == '__main__':
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    loads = [200, 400, 600, 700, 800, 900, 1000, 1100, 1200, 1400]
    for name, path, kind, xr, ex in [
            ('T-13 Fig 2.5', 'emb31/im-000.png', 'black', (0.0, 30.0), [(23.5, 30.5, 1300, 2000), (21, 30.5, 0, 700)]),
            ('T-19 Fig 2.5', 'emb31/im-000.png', 'red', (0.0, 30.0), [(21, 30.5, 0, 700)]),
            ('T-13 Fig 2.22a', 'emb50/im-000.png', 'red', (0.0, 30.0), [(18.5, 30.5, 0, 760)]),
            ('T-19 Fig 2.22b', 'emb50/im-001.png', 'red', (0.0, 30.0), [(18.5, 30.5, 0, 760)])]:
        res, sc = mean_curve(os.path.join(base, path), kind, loads, xr, ex)
        print(name, 'scale mm/px', round(sc[0], 4))
        for T, xm, x1, x2, ng in res:
            print(f'   {T:5d} kN: mean {xm:.3f} mm  (lines {x1:.3f}, {x2:.3f}; groups {ng})')


def two_lines(path, kind, T_lo, T_hi, excl=(), deg=2):
    """Rows between T_lo and T_hi where exactly two lines of the colour are found; each line (left, right) fitted
    by a polynomial in T. Returns the fits and the rows used."""
    a = load(path)
    xv = list(range(0, 31, 5)) if 'emb31' in path else list(range(0, 31, 2))
    fx, fy, box, sc = calibrate(a, xv, list(range(0, 2001, 200)), verbose=False)
    m = colour_mask(a, kind)
    m[:int(box['top']) + 3] = False; m[int(box['bottom']) - 2:] = False
    m[:, :int(box['left']) + 3] = False; m[:, int(box['right']) - 2:] = False
    if kind == 'black':
        for g in box['gx']: m[:, int(round(g)) - 2:int(round(g)) + 3] = False
        for g in box['gy']: m[int(round(g)) - 2:int(round(g)) + 3, :] = False
    rows = []
    for rr in range(m.shape[0]):
        T = float(fy(rr))
        if not (T_lo <= T <= T_hi):
            continue
        cols = np.nonzero(m[rr])[0]
        xs = fx(cols)
        keep = np.ones(cols.size, bool)
        for (x0, x1, y0, y1) in excl:
            keep &= ~((xs >= x0) & (xs <= x1) & (T >= y0) & (T <= y1))
        cols = cols[keep]
        if cols.size == 0:
            continue
        runs = np.split(cols, np.where(np.diff(cols) > 1)[0] + 1)
        cents = np.array([run.mean() for run in runs])
        groups = np.split(np.sort(cents), np.where(np.diff(np.sort(cents)) > 3)[0] + 1)
        if len(groups) == 2:
            rows.append((T, float(fx(np.median(groups[0]))), float(fx(np.median(groups[1])))))
    R = np.array(rows)
    pl = np.polyfit(R[:, 0], R[:, 1], deg); pr = np.polyfit(R[:, 0], R[:, 2], deg)
    res_l = R[:, 1] - np.polyval(pl, R[:, 0]); res_r = R[:, 2] - np.polyval(pr, R[:, 0])
    return pl, pr, R, (float(np.abs(res_l).max()), float(np.abs(res_r).max())), sc
