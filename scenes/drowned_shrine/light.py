"""Palette-true lighting: every pixel moves along its own ramp by an integer number of steps, never blended.
A light map (float steps per pixel) is built from an ambient level plus radial lights, then quantised with a
4x4 Bayer matrix so the edges of a light pool dither instead of banding."""
import numpy as np

from px import RAMPS, hx

_keys, _ramp_start, _ramp_len, _pos, _cols = [], [], [], [], []
_i = 0
for name, r in RAMPS.items():
    for j, h in enumerate(r):
        c = hx(h)
        _keys.append((int(c[0]) << 16) | (int(c[1]) << 8) | int(c[2]))
        _ramp_start.append(_i); _ramp_len.append(len(r)); _pos.append(j); _cols.append(c[:3])
    _i += len(r)
_names = [name for name, r in RAMPS.items() for _ in r]
EMISSIVE = np.array([n in ("fire", "glow") for n in _names])     # light sources never darken
KEYS = np.array(_keys); ORDER = np.argsort(KEYS); SK = KEYS[ORDER]
START = np.array(_ramp_start); LEN = np.array(_ramp_len); POS = np.array(_pos); COLS = np.array(_cols, np.uint8)
BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16


def index(img):
    """Palette index of each pixel, -1 where the colour is not in the palette (left untouched by lighting)."""
    k = (img[..., 0].astype(np.int64) << 16) | (img[..., 1].astype(np.int64) << 8) | img[..., 2]
    i = np.searchsorted(SK, k).clip(0, len(SK) - 1)
    ok = SK[i] == k
    return np.where(ok, ORDER[i], -1)


def apply(img, steps, emissive=True):
    """Shift each pixel by steps (float array, same HxW), dithered to integers with the Bayer matrix."""
    h, w = img.shape[:2]
    b = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w]
    d = np.floor(steps + b).astype(int)
    idx = index(img)
    ok = (idx >= 0) & (img[..., 3] > 0) & (d != 0)
    out = img.copy()
    ii = idx[ok]
    dd = np.where(EMISSIVE[ii] & emissive, np.maximum(d[ok], 0), d[ok])
    new = START[ii] + np.clip(POS[ii] + dd, 0, LEN[ii] - 1)
    out[..., :3][ok] = COLS[new]
    return out


def lightmap(h, w, ambient, lights):
    """ambient: steps everywhere (e.g. -1.2 for night). lights: (x, y, radius, strength) - strength steps at the
    centre, falling off linearly to 0 at the radius. Lights add; the result is capped at the strongest light's
    level so two overlapping pools don't burn out."""
    yy, xx = np.mgrid[0:h, 0:w]
    L = np.full((h, w), float(ambient))
    add = np.zeros((h, w))
    for (x, y, r, s) in lights:
        d = np.sqrt((xx - x) ** 2 + ((yy - y) * 1.25) ** 2)       # squashed: pools lie on the floor
        add = np.maximum(add, np.clip(1 - d / r, 0, 1) * s)
    return L + add
