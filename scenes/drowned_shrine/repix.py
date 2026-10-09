"""Krea raw design -> a clean 64-grid sprite in the scene palette.

The LoRA draws on a 16-px grid (1024 / 64). Find the grid's phase (the offset whose cells are most uniform),
take each cell's dominant colour (the mode of its inner pixels, so anti-aliased cell edges don't vote), then map
every colour to the nearest palette entry in a perceptual space, restricted to the ramps the character may use."""
import sys

import numpy as np
from PIL import Image

from px import RAMPS, hx, OUT, DESIGNS


def lab(rgb):
    rgb = np.asarray(rgb, float) / 255
    lin = np.where(rgb > 0.04045, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = lin @ M.T / np.array([0.9505, 1.0, 1.089])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def grid_phase(a, cell=16):
    best = None
    rgb = a[..., :3].astype(float)
    for o in range(cell):
        # variance across each cell's inner 8x8, summed
        sub = rgb[o:, o:]
        h, w = (sub.shape[0] // cell) * cell, (sub.shape[1] // cell) * cell
        s = sub[:h, :w].reshape(h // cell, cell, w // cell, cell, 3)[:, 4:12, :, 4:12]
        v = s.var(axis=(1, 3)).sum()
        if best is None or v < best[0]:
            best = (v, o)
    return best[1]


def cells(raw, cell=16):
    a = np.asarray(raw.convert("RGBA"))
    o = grid_phase(a, cell)
    H, W = (a.shape[0] - o) // cell, (a.shape[1] - o) // cell
    out = np.zeros((H, W, 4), np.uint8)
    for y in range(H):
        for x in range(W):
            c = a[o + y * cell + 3:o + (y + 1) * cell - 3, o + x * cell + 3:o + (x + 1) * cell - 3].reshape(-1, 4)
            if (c[:, 3] > 127).mean() < 0.5:
                continue
            c = c[c[:, 3] > 127][:, :3] // 4
            keys, counts = np.unique(c[:, 0].astype(int) << 12 | c[:, 1].astype(int) << 6 | c[:, 2], return_counts=True)
            k = keys[counts.argmax()]
            m = c[(c[:, 0].astype(int) << 12 | c[:, 1].astype(int) << 6 | c[:, 2]) == k]
            out[y, x, :3] = (m.mean(0) * 4 + 2).clip(0, 255)
            out[y, x, 3] = 255
    return out, o


def to_palette(img, ramps, weights=None):
    """Map each opaque pixel to the nearest colour among the given ramps (CIELAB distance)."""
    pal = [(k, i, hx(h)) for k in ramps for i, h in enumerate(RAMPS[k])]
    P = np.array([p[2][:3] for p in pal]); PL = lab(P)
    out = img.copy()
    m = img[..., 3] > 0
    L = lab(img[..., :3][m])
    d = ((L[:, None, :] - PL[None]) ** 2).sum(-1)
    j = d.argmin(1)
    out[..., :3][m] = P[j]
    return out


def crop_to(img, size=64, foot_pad=2):
    """Centre the sprite horizontally on a size x size canvas, feet foot_pad px above the bottom."""
    ys, xs = np.nonzero(img[..., 3] > 0)
    h, w = ys.max() - ys.min() + 1, xs.max() - xs.min() + 1
    c = np.zeros((size, size, 4), np.uint8)
    ox = (size - w) // 2
    oy = size - foot_pad - h
    c[oy:oy + h, ox:ox + w] = img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return c


if __name__ == "__main__":
    name, ramps = sys.argv[1], sys.argv[2].split(",")
    raw = Image.open(DESIGNS / f"{name}_raw.png")
    g, o = cells(raw)
    p = to_palette(g, ramps)
    Image.fromarray(p).save(OUT / f"{name}_grid.png")
    Image.fromarray(p).resize((p.shape[1] * 6, p.shape[0] * 6), Image.NEAREST).save(OUT / f"{name}_grid_x6.png")
    print(name, "phase", o, "grid", g.shape[:2], "colours", len(np.unique(p[p[..., 3] > 0][:, :3], axis=0)))
