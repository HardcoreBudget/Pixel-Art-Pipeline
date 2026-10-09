"""Drowned Shrine scene: pixel helpers and the scene's master palette.

Every sprite, tile and UI element in the scene is drawn in this palette, in ramps (darkest first), so light and
shadow are a step along a ramp, never a blend."""
import os
import pathlib

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
DESIGNS = HERE.parent / "designs"   # the Krea designs and the 64-grid inputs the characters are built from
# Everything a run writes goes under $SCENES_OUT (default: <repo>/out/scenes): drowned_shrine/, ashen_peak/, agentdraw/.
OUT_ROOT = pathlib.Path(os.environ.get("SCENES_OUT", HERE.parent.parent / "out" / "scenes"))
OUT = OUT_ROOT / "drowned_shrine"
OUT.mkdir(parents=True, exist_ok=True)


def hx(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)] + [255], np.uint8)


# ramps, darkest first
RAMPS = {
    "ink":    ["#0B0A16"],
    "night":  ["#141326", "#1E1D38", "#2A2B4C", "#383D63"],
    "stone":  ["#2F3552", "#414A6B", "#566388", "#7482A6", "#9AA6C4", "#C3CCE0"],
    "moss":   ["#16302F", "#224A40", "#336B4F", "#4E8D57", "#79B061", "#B2D67A"],
    "water":  ["#10243C", "#163A55", "#1D5870", "#277A88", "#3AA0A2", "#68C7BD", "#B4ECDF"],
    "glow":   ["#2FB9D0", "#6FE6EC", "#D2FFF9"],
    "fire":   ["#4A1A28", "#8A2E2C", "#C9502E", "#EE8A36", "#FFC34E", "#FFEC96", "#FFFBE2"],
    "crimson": ["#4A1426", "#7C1E34", "#B3303E", "#E0564E", "#F58A70"],
    "teal":   ["#123A44", "#1B5A60", "#2A7D7A", "#44A394"],
    "skin":   ["#5C2E2E", "#9A5645", "#CF8A64", "#F0BE92"],
    "wood":   ["#2C1A1E", "#4B2C28", "#6E4432", "#96633F", "#BE8C57"],
    "cream":  ["#A89C84", "#D8CDB0", "#F4EEDC"],
    "silver": ["#4E5670", "#8C95AE", "#C9D0E0", "#F4F7FF"],
    "violet": ["#1F1638", "#2F2156", "#453479", "#62509E", "#8A7AC4", "#B9ADE4"],
    "gold":   ["#6B4A1E", "#A8782C", "#D8AA46", "#F5D878"],
    "sky":    ["#24406E", "#35609A", "#5089C2", "#7FB6E0", "#BFE2F5"],
    # Ashen Peak (the fight scene): a dusk sky, warm stone, jade roofs, plum petals
    "dusk":   ["#1A1330", "#2E1A45", "#52234F", "#822F55", "#B8434F", "#E06A4E", "#F59A5A", "#FFCB7A"],
    "warm":   ["#1F161E", "#35242C", "#503640", "#6E4B52", "#936A68", "#BB9184", "#DDBBA6"],
    "jade":   ["#0F2525", "#173934", "#22524A", "#357161", "#55957C"],
    "petal":  ["#A24A72", "#D5719A", "#F4A6C2", "#FFD8E6"],
}
C = {f"{k}{i}": hx(h) for k, r in RAMPS.items() for i, h in enumerate(r)}
C["ink"] = C["ink0"]
PALETTE = np.array([v for v in C.values()])


def ramp_step(img, steps, mask=None):
    """Move every pixel `steps` along its ramp (negative = darker), clamped at the ends. Palette-true lighting."""
    out = img.copy()
    look = {}
    for k, r in RAMPS.items():
        for i, h in enumerate(r):
            j = max(0, min(len(r) - 1, i + steps))
            look[tuple(hx(h)[:3])] = hx(r[j])
    a = img[..., 3] > 0
    if mask is not None:
        a &= mask
    ys, xs = np.nonzero(a)
    for y, x in zip(ys, xs):
        v = look.get(tuple(img[y, x, :3]))
        if v is not None:
            out[y, x, :3] = v[:3]
    return out


def canvas(w, h):
    return np.zeros((h, w, 4), np.uint8)


def blit(dst, src, x, y, flip=False):
    """Draw src onto dst with its top-left at (x, y); binary alpha (pixel art)."""
    if flip:
        src = src[:, ::-1]
    h, w = src.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x0 >= x1 or y0 >= y1:
        return dst
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    m = s[..., 3] > 0
    dst[y0:y1, x0:x1][m] = s[m]
    return dst


def fill(img, mask, col):
    img[mask] = C[col] if isinstance(col, str) else col


def rect(img, x, y, w, h, col):
    img[max(0, y):y + h, max(0, x):x + w] = C[col] if isinstance(col, str) else col


def put(img, x, y, col):
    if 0 <= x < img.shape[1] and 0 <= y < img.shape[0]:
        img[y, x] = C[col] if isinstance(col, str) else col


def art(rows, key, x0=0, y0=0, img=None):
    """ASCII art -> RGBA. key maps a character to a colour name; '.' and ' ' are empty."""
    h, w = len(rows), max(len(r) for r in rows)
    if img is None:
        img = canvas(w + x0, h + y0)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch not in ". ":
                put(img, x0 + x, y0 + y, key[ch])
    return img


def outline(img, col="ink", diag=False):
    """A 1-px outline around the opaque shape, outside it."""
    from scipy import ndimage
    m = img[..., 3] > 0
    st = np.ones((3, 3), bool) if diag else np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
    ring = ndimage.binary_dilation(m, st) & ~m
    out = img.copy()
    out[ring] = C[col]
    return out


def pad(img, n):
    return np.pad(img, ((n, n), (n, n), (0, 0)))


def save(img, path, s=1):
    im = Image.fromarray(img)
    if s != 1:
        im = im.resize((im.width * s, im.height * s), Image.NEAREST)
    im.save(path)
    return path


def rng(seed):
    return np.random.default_rng(seed)
