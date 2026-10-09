"""Fight effects, drawn per frame in the palette; each returns (sprite, (anchor_x, anchor_y))."""
import math
import sys
import pathlib

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "drowned_shrine"))
from px import C, canvas, put, rect, rng
import fx as FX


def fireball(f):
    """The Sun Palm: a flame orb with a hot core and a flickering tail streaming back (to the left), 6-frame loop."""
    img = canvas(34, 17)
    cx, cy = 25, 8
    yy, xx = np.mgrid[0:17, 0:34]
    wob = [0, 1, 0, -1, 0, 1][f % 6]
    d = np.sqrt((xx - cx) ** 2 + ((yy - cy) * 1.15) ** 2)
    # the tail: a teardrop narrowing to the left, its edge rippling
    tail = np.zeros((17, 34), bool)
    for x in range(0, cx):
        u = (cx - x) / cx
        half = 6.5 * (1 - u) ** 0.8 + 0.6 * math.sin(x * 0.9 + f * 1.3)
        tail[:, x] = np.abs(yy[:, x] - cy - wob * u) <= half
    ball = d <= 7
    img[tail | ball] = C["fire2"]
    img[(tail & (np.abs(yy - cy) <= 3.5 * (xx / cx) ** 0.7)) | (d <= 5.5)] = C["fire3"]
    img[(d <= 4.2) | (tail & (np.abs(yy - cy) <= 1.5) & (xx > 12))] = C["fire4"]
    img[d <= 3] = C["fire5"]
    img[d <= 1.6] = C["fire6"]
    r = rng(40 + f)
    for _ in range(5):                                      # sparks shed from the tail
        x, y = r.integers(0, 14), cy + r.integers(-6, 7)
        put(img, x, y, "fire4" if r.random() < 0.5 else "fire5")
    return img, (cx, cy)


def fire_pop(f):
    """The fireball bursting on contact: 5 frames."""
    if f < 4:
        img, a = FX.spark(f, big=True, cols=("fire6", "fire5", "fire3"))
        if f < 2:
            yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
            d = np.sqrt((xx - a[0]) ** 2 + (yy - a[1]) ** 2)
            img[(d >= 4 + 3 * f) & (d < 6 + 3 * f)] = C["fire4"]
        return img, a
    return canvas(3, 3), (1, 1)


def block_spark(f):
    return FX.spark(min(f, 3), big=False, cols=("silver3", "glow2", "glow1"))


def hit_spark(f, big=False):
    return FX.spark(min(f, 3), big=big, cols=("fire6", "gold3", "crimson3"))


def dust(f, w=22):
    """A dust puff at the feet (landing / knockdown), 6 frames: billows out and thins."""
    img = canvas(w + 8, 12)
    r = rng(7)
    base = 11
    for k in range(9):
        side = -1 if k % 2 else 1
        x0 = (w + 8) / 2 + side * (2 + k * 1.2 + f * (1.5 + k * 0.25))
        y0 = base - 2 - (k % 3) - f * 0.6
        rad = max(0.0, 2.6 - f * 0.35 + (k % 3) * 0.4)
        yy, xx = np.mgrid[0:12, 0:w + 8]
        m = (xx - x0) ** 2 + (yy - y0) ** 2 <= rad * rad
        if f >= 3:
            m &= (xx + yy + f) % 2 == 0
        img[m] = C["warm5" if k % 3 else "warm4"]
    return img, ((w + 8) // 2, base)


def shockwave(f):
    """The ground slam's wave: a ridge of broken stone and a light crest travelling right, with chips thrown up.
    The caller moves it; f animates the crest, 4-frame loop."""
    img = canvas(30, 22)
    base = 20
    r = rng(12 + f % 4)
    for x in range(30):
        u = x / 29
        h = int(round(10 * math.sin(math.pi * u) ** 1.5 * (0.8 + 0.2 * math.sin(f * 1.7 + x * 0.6))))
        for y in range(base - h, base + 1):
            put(img, x, y, "warm4" if y < base - h + 2 else "warm3" if y < base - 2 else "warm2")
        if h > 3:
            put(img, x, base - h - 1, "fire5" if x % 3 == 0 else "fire4")
    for _ in range(7):                                      # stone chips
        x, y = r.integers(4, 26), r.integers(0, 9)
        rect(img, x, y, 2, 2, "warm4"); put(img, x, y + 1, "warm2")
    return img, (15, base)


def speed_lines(f, w=40, h=26):
    """Motion lines streaming behind a charge (to the left of the anchor)."""
    img = canvas(w, h)
    r = rng(60 + f)
    for k in range(7):
        y = int(2 + k * (h - 4) / 6 + r.integers(-1, 2))
        ln = int(r.integers(10, w - 6))
        x0 = w - ln - int(r.integers(0, 6))
        img[y, x0:x0 + ln] = C["cream1" if k % 2 else "warm5"]
    return img, (w, h // 2)


def flame_arc(f):
    """The finishing uppercut's rising flame crescent, 4 frames."""
    img, a = FX.slash(min(f, 2), a0=-100, a1=60, r=20, ramp=("fire3", "fire4", "fire5", "fire6"))
    return img, a
