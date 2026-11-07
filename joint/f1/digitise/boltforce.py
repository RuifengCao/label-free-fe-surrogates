import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from digi import *
from skimage.measure import label, regionprops
import json
from PIL import ImageDraw

def inside(m, box, pad=3):
    m = m.copy()
    m[:int(box['top']) + pad] = False; m[int(box['bottom']) - pad + 1:] = False
    m[:, :int(box['left']) + pad] = False; m[:, int(box['right']) - pad + 1:] = False
    return m

def points(a, kind, cal, excl):
    fx, fy, box, _ = cal
    m = inside(colour_mask(a, kind), box)
    if kind == 'black':
        for g in box['gx']: m[:, int(round(g)) - 1:int(round(g)) + 2] = False
        for g in box['gy']: m[int(round(g)) - 1:int(round(g)) + 2, :] = False
    pts = []
    if kind == 'cyan':
        # solid lines: centre of each vertical run in each column
        H, W = m.shape
        for c in range(W):
            rows = np.nonzero(m[:, c])[0]
            if len(rows) == 0: continue
            runs = np.split(rows, np.where(np.diff(rows) > 1)[0] + 1)
            for r in runs:
                if len(r) >= 2: pts.append((c, r.mean(), len(r)))
    else:
        L = label(m, connectivity=2)
        for p in regionprops(L):
            r0, c0, r1, c1 = p.bbox
            h, w = r1 - r0, c1 - c0
            lo, hi = (8, 60) if kind == 'black' else (20, 70)
            if lo <= p.area <= hi and h <= 10 and w <= 11:
                pts.append((p.centroid[1], p.centroid[0], p.area))
            elif kind == 'black' and 2 * lo <= p.area <= 2 * hi and h <= 10 and w <= 20:
                # two touching dots side by side: split at the column midpoint
                rr, cc = np.nonzero(L[r0:r1, c0:c1] == p.label)
                mid = np.median(cc)
                for sel in (cc < mid, cc >= mid):
                    pts.append((c0 + cc[sel].mean(), r0 + rr[sel].mean(), sel.sum()))
    P = np.array([(fx(c), fy(r), s) for c, r, s in pts])
    for (x0, x1, y0, y1) in excl:
        P = P[~((P[:, 0] >= x0) & (P[:, 0] <= x1) & (P[:, 1] >= y0) & (P[:, 1] <= y1))]
    return P

def split_pair(P, dM=2.5, sep=3.0, Mmax=None):
    """Upper and lower envelopes of a two-series point cloud, binned in M."""
    M, B = P[:, 0], P[:, 1]
    edges = np.arange(0, (Mmax or M.max()) + dM, dM)
    out = []
    for lo in edges:
        s = (M >= lo) & (M < lo + dM)
        if s.sum() == 0: continue
        b = np.sort(B[s]); mc = M[s].mean()
        if b[-1] - b[0] > sep:
            g = np.argmax(np.diff(b))
            out.append((mc, b[g + 1:].mean(), b[:g + 1].mean()))
        else:
            out.append((mc, b.mean(), b.mean()))
    return np.array(out)

def draw(a, cal, series, path):
    fx, fy, box, _ = cal
    im = Image.fromarray(a.astype(np.uint8)).copy(); dr = ImageDraw.Draw(im)
    c = np.arange(a.shape[1]); r = np.arange(a.shape[0])
    ax = np.polyfit(fx(c), c, 1); ay = np.polyfit(fy(r), r, 1)
    cols = [(255, 0, 255), (0, 160, 0)]
    for arr in series:
        for j, col in ((1, cols[0]), (2, cols[1])):
            for M, Bv in zip(arr[:, 0], arr[:, j]):
                u, v = np.polyval(ax, M), np.polyval(ay, Bv)
                dr.rectangle([u - 1, v - 1, u + 1, v + 1], fill=col)
    im.save(path)

if __name__ == '__main__':
    res = {}
    # exclusion boxes in data coords (M0, M1, B0, B1): legend, labels with arrows, failure cross
    EX = {
      'B13': ('emb/im-001.png', 145, [(215, 330, -5, 70), (225, 250, 198, 222), (108, 128, 195, 222), (150, 170, 168, 186), (150, 170, 147, 168), (152, 170, 112, 132), (150, 180, 84, 100), (146, 152, 160, 200)]),
      'B19': ('emb/im-002.png', 201, [(215, 330, -5, 70), (288, 305, 200, 222), (176, 192, 198, 216), (200, 226, 170, 186), (200, 226, 108, 128), (100, 124, 98, 114), (204, 230, 140, 160)]),
    }
    for sp, (f, Mend, ex) in EX.items():
        a = load(f); cal = calibrate(a, list(range(0, 326, 25)), list(range(0, 226, 25)), verbose=False)
        S = []
        for kind, name in (('black', '1-2'), ('cyan', '3-4'), ('red', '5-6')):
            P = points(a, kind, cal, ex)
            P = P[P[:, 0] <= Mend + 1.5]
            env = split_pair(P, Mmax=Mend)
            res[f'{sp}_{name}'] = env.round(2).tolist()
            S.append(env)
            first, last = env[0], env[-1]
            print(f'{sp} bolts {name}: {len(P)} pts; first M {first[0]:.1f}: {first[1]:.1f}/{first[2]:.1f}; last M {last[0]:.1f}: {last[1]:.1f}/{last[2]:.1f}')
        draw(a, cal, S, f'out/ov_bolts_{sp}.png')
    json.dump(res, open('out/raw_bolts.json', 'w'))


def split_dotted(P, win=12.0):
    """Split two dotted series by a moving median of all dots."""
    M, B = P[:, 0], P[:, 1]
    o = np.argsort(M); M, B = M[o], B[o]
    mid = np.array([np.median(B[np.abs(M - m) <= win / 2]) for m in M])
    up = B >= mid
    return np.column_stack([M[up], B[up]]), np.column_stack([M[~up], B[~up]])


def split_track(P, dM=2.5, sep=3.0, Mmax=None):
    """Like split_pair, but a bin with a single value is given to the nearer track
    and the other track is interpolated."""
    M, B = P[:, 0], P[:, 1]
    edges = np.arange(0, (Mmax or M.max()) + dM, dM)
    rows = []
    pu = pl = None
    for lo in edges:
        s = (M >= lo) & (M < lo + dM)
        if s.sum() == 0: continue
        b = np.sort(B[s]); mc = M[s].mean()
        if b[-1] - b[0] > sep:
            g = np.argmax(np.diff(b)); u, l = b[g + 1:].mean(), b[:g + 1].mean()
        else:
            v = b.mean()
            if pu is None or abs(pu - pl) <= sep:
                u = l = v
            elif abs(v - pu) <= abs(v - pl):
                u, l = v, np.nan
            else:
                u, l = np.nan, v
        rows.append([mc, u, l])
        if not np.isnan(u): pu = u
        if not np.isnan(l): pl = l
        if pl is None: pl = pu
        if pu is None: pu = pl
    A = np.array(rows, dtype=float)
    for j in (1, 2):
        ok = ~np.isnan(A[:, j])
        A[~ok, j] = np.interp(A[~ok, 0], A[ok, 0], A[ok, j])
    return A
