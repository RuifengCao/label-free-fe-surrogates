"""Digitise raster charts from the Fidalgo (2023) thesis.

Calibration uses the plot frame and the grey gridlines, whose data values are known
from the axis labels. Curves are extracted by colour, skeletonised, and ordered along
the longest path of a minimum spanning tree over the skeleton pixels.
"""
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import minimum_spanning_tree, shortest_path
from skimage.morphology import skeletonize
from scipy.sparse.csgraph import connected_components


def load(path):
    return np.asarray(Image.open(path).convert('RGB')).astype(int)


def _clusters(idx):
    """Group consecutive integer indices; return the mean of each group."""
    if len(idx) == 0:
        return []
    groups, cur = [], [idx[0]]
    for i in idx[1:]:
        if i - cur[-1] <= 1:
            cur.append(i)
        else:
            groups.append(cur)
            cur = [i]
    groups.append(cur)
    return [float(np.mean(g)) for g in groups]


def calibrate(a, xvals, yvals, frac_frame=0.55, frac_grid=0.35, verbose=True):
    """Return functions px->data. xvals/yvals list the data values of the left frame,
    the vertical gridlines and the right frame (and bottom frame, horizontal gridlines,
    top frame for y)."""
    H, W, _ = a.shape
    s = a.sum(2)
    dark = s < 200
    grey = (np.abs(a[..., 0] - a[..., 1]) < 10) & (np.abs(a[..., 1] - a[..., 2]) < 10) & (a[..., 0] > 95) & (a[..., 0] < 215)
    # frame: longest dark runs
    colc, rowc = dark.sum(0), dark.sum(1)
    fcols = _clusters(np.where(colc > frac_frame * colc.max())[0])
    frows = _clusters(np.where(rowc > frac_frame * rowc.max())[0])
    left, right = fcols[0], fcols[-1]
    top, bottom = frows[0], frows[-1]
    # gridlines inside the frame
    sub = grey[int(top) + 3:int(bottom) - 2, int(left) + 3:int(right) - 2]
    gc = _clusters(np.where(sub.sum(0) > frac_grid * sub.shape[0])[0] + int(left) + 3)
    gr = _clusters(np.where(sub.sum(1) > frac_grid * sub.shape[1])[0] + int(top) + 3)
    def match(lo, hi, lines, vals):
        # vals are uniformly spaced from lo to hi; assign each detected line to its slot
        n = len(vals)
        sp = (hi - lo) / (n - 1)
        pos, val = [lo, hi], [vals[0], vals[-1]]
        for g in lines:
            k = int(round((g - lo) / sp))
            if 0 < k < n - 1 and abs(g - (lo + k * sp)) < 0.25 * abs(sp):
                pos.append(g)
                val.append(vals[k])
        return pos, val
    xs, xv = match(left, right, gc, list(xvals))
    ys, yv = match(bottom, top, gr, list(yvals))
    if len(xs) < 3 or len(ys) < 3:
        raise ValueError(f'too few lines: x {xs}; y {ys}')
    px = np.polyfit(xs, xv, 1)
    py = np.polyfit(ys, yv, 1)
    rx = np.array(xv) - np.polyval(px, xs)
    ry = np.array(yv) - np.polyval(py, ys)
    if verbose:
        print(f'  lines used x {len(xs)}/{len(xvals)}, y {len(ys)}/{len(yvals)}; frame L{left:.1f} R{right:.1f} T{top:.1f} B{bottom:.1f}; grid x {[round(g,1) for g in gc]} y {[round(g,1) for g in gr]}')
        print(f'  residual x max {np.abs(rx).max()/abs(px[0]):.2f} px, y max {np.abs(ry).max()/abs(py[0]):.2f} px; '
              f'scale x {abs(px[0]):.3g}/px, y {abs(py[0]):.3g}/px')
    box = dict(left=left, right=right, top=top, bottom=bottom, gx=gc, gy=gr)
    return (lambda c: np.polyval(px, c)), (lambda r: np.polyval(py, r)), box, (abs(px[0]), abs(py[0]))


def colour_mask(a, kind):
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    if kind == 'red':
        return (R > 170) & (G < 110) & (B < 110)
    if kind == 'cyan':
        return (R < 140) & (G > 120) & (B > 190) & (B - R > 90)
    if kind == 'black':
        mx = np.maximum(np.maximum(R, G), B); mn = np.minimum(np.minimum(R, G), B)
        return ((R + G + B) < 240) & ((mx - mn) < 40)
    raise ValueError(kind)


def order_curve(mask, gap=18.0):
    """Skeletonise and return pixel coordinates (col,row) ordered along the longest
    MST path."""
    sk = skeletonize(mask)
    r, c = np.nonzero(sk)
    P = np.column_stack([c, r]).astype(float)
    if len(P) < 3:
        raise ValueError('too few pixels')
    tree = cKDTree(P)
    n = len(P)
    g = gap
    while True:
        pairs = np.array(sorted(tree.query_pairs(g)))
        d = np.linalg.norm(P[pairs[:, 0]] - P[pairs[:, 1]], axis=1)
        G = coo_matrix((d, (pairs[:, 0], pairs[:, 1])), shape=(n, n))
        ncomp, lab = connected_components(G, directed=False)
        if ncomp == 1 or g > 4 * gap:
            break
        g *= 1.25
    if ncomp > 1:
        # keep the largest component only
        big = np.bincount(lab).argmax()
        keep = np.where(lab == big)[0]
        P = P[keep]
        return order_curve_points(P, g)
    T = minimum_spanning_tree(G)
    T = T + T.T
    d0 = shortest_path(T, indices=0, directed=False)
    d0[np.isinf(d0)] = -1
    A = int(np.argmax(d0))
    dA, pred = shortest_path(T, indices=A, directed=False, return_predecessors=True)
    dA[np.isinf(dA)] = -1
    B = int(np.argmax(dA))
    path = [B]
    while path[-1] != A:
        path.append(int(pred[path[-1]]))
    return P[path], n, len(path)


def order_curve_points(P, gap):
    tree = cKDTree(P)
    n = len(P)
    pairs = np.array(sorted(tree.query_pairs(gap)))
    d = np.linalg.norm(P[pairs[:, 0]] - P[pairs[:, 1]], axis=1)
    G = coo_matrix((d, (pairs[:, 0], pairs[:, 1])), shape=(n, n))
    T = minimum_spanning_tree(G); T = T + T.T
    d0 = shortest_path(T, indices=0, directed=False); d0[np.isinf(d0)] = -1
    A = int(np.argmax(d0))
    dA, pred = shortest_path(T, indices=A, directed=False, return_predecessors=True); dA[np.isinf(dA)] = -1
    B = int(np.argmax(dA))
    path = [B]
    while path[-1] != A:
        path.append(int(pred[path[-1]]))
    return P[path], n, len(path)


def resample(x, y, n=300):
    xn = (x - x.min()) / max(np.ptp(x), 1e-12)
    yn = (y - y.min()) / max(np.ptp(y), 1e-12)
    s = np.concatenate([[0], np.cumsum(np.hypot(np.diff(xn), np.diff(yn)))])
    t = np.linspace(0, s[-1], n)
    return np.interp(t, s, x), np.interp(t, s, y)


def smooth(v, k=5):
    if k <= 1:
        return v
    ker = np.ones(k) / k
    pad = np.concatenate([np.full(k // 2, v[0]), v, np.full(k // 2, v[-1])])
    return np.convolve(pad, ker, mode='valid')


from scipy.sparse.csgraph import connected_components


def extract(a, kind, cal, excl=(), margin=4, gap=18.0, origin=(0.0, 0.0), extra_mask=None):
    """Return data-space (x, y) arrays for one coloured curve.
    excl: boxes in data coords (x0, x1, y0, y1) to blank out.
    origin: the data-space point the curve starts nearest to."""
    fx, fy, box, _ = cal
    m = colour_mask(a, kind)
    if extra_mask is not None:
        m &= extra_mask
    H, W = m.shape
    keep = np.zeros_like(m)
    keep[int(box['top']) + margin:int(box['bottom']) - margin + 1, int(box['left']) + margin:int(box['right']) - margin + 1] = True
    m &= keep
    cols = np.arange(W)
    rows = np.arange(H)
    X = fx(cols)[None, :].repeat(H, 0)
    Y = fy(rows)[:, None].repeat(W, 1)
    if kind == 'black':
        for g in box['gx']:
            m[:, max(int(round(g)) - 2, 0):int(round(g)) + 3] = False
        for g in box['gy']:
            m[max(int(round(g)) - 2, 0):int(round(g)) + 3, :] = False
    for (x0, x1, y0, y1) in excl:
        m &= ~((X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1))
    P, nsk, npath = order_curve(m, gap=gap)
    x, y = fx(P[:, 0]), fy(P[:, 1])
    # orient from the origin end
    xr = max(np.ptp(x), 1e-12); yr = max(np.ptp(y), 1e-12)
    d0 = np.hypot((x[0] - origin[0]) / xr, (y[0] - origin[1]) / yr)
    d1 = np.hypot((x[-1] - origin[0]) / xr, (y[-1] - origin[1]) / yr)
    if d1 < d0:
        x, y = x[::-1], y[::-1]
    return x, y, dict(mask_px=int(m.sum()), skeleton_px=nsk, path_px=npath)


def overlay(a, cal, curves, path):
    """Draw extracted curves (data coords) back onto the image as magenta dots."""
    fx, fy, box, _ = cal
    from PIL import ImageDraw
    im = Image.fromarray(a.astype(np.uint8)).copy()
    dr = ImageDraw.Draw(im)
    # invert the linear maps
    c = np.arange(a.shape[1]); r = np.arange(a.shape[0])
    ax = np.polyfit(fx(c), c, 1); ay = np.polyfit(fy(r), r, 1)
    for (x, y) in curves:
        for xi, yi in zip(x[::3], y[::3]):
            u, v = np.polyval(ax, xi), np.polyval(ay, yi)
            dr.ellipse([u - 1.5, v - 1.5, u + 1.5, v + 1.5], fill=(255, 0, 255))
    im.save(path)
