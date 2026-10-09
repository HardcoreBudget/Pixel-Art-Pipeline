"""Ashen Peak Temple: the fight stage, drawn by rule pixel by pixel in parallax layers.

Each layer is drawn once at its own width (view width + scroll range * factor); the camera offsets it by
-cam * factor. Animated parts (lanterns, banners, braziers) are drawn per tick on top of the static layers."""
import math
import sys
import pathlib

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "drowned_shrine"))
sys.path.insert(0, str(HERE.parent))
from px import C, canvas, rect, put, blit, rng, art, OUT as SCENE_OUT
from light import BAYER

VW, VH = 256, 144
STAGE_W = 400
SCROLL = STAGE_W - VW                  # the camera's range
FLOOR_Y = 112                          # where the courtyard meets the back wall
OUT = SCENE_OUT.parent / "ashen_peak"
OUT.mkdir(parents=True, exist_ok=True)
FACTORS = {"sky": 0.0, "far": 0.15, "near": 0.3, "temple": 0.6, "floor": 1.0, "fg": 1.25}


def width(layer):
    return int(VW + SCROLL * FACTORS[layer]) + 2


def dither_band(img, y0, y1, c0, c1, x0=0, x1=None):
    """Rows y0..y1 blend from colour c0 to c1 by an ordered dither (no new colours)."""
    x1 = x1 or img.shape[1]
    for y in range(y0, y1):
        u = (y - y0 + 0.5) / max(1, y1 - y0)
        for x in range(x0, x1):
            img[y, x] = C[c1] if u > BAYER[y % 4, x % 4] else C[c0]


# ---------------------------------------------------------------- sky

def sky():
    img = canvas(width("sky"), VH)
    bands = [(0, 18, "dusk0", "dusk1"), (18, 38, "dusk1", "dusk2"), (38, 56, "dusk2", "dusk3"),
             (56, 72, "dusk3", "dusk4"), (72, 86, "dusk4", "dusk5"), (86, 100, "dusk5", "dusk6"), (100, VH, "dusk6", "dusk6")]
    for y0, y1, a, b in bands:
        dither_band(img, y0, y1, a, b)
    # a low red sun behind the peaks, ringed, with two thin cloud streaks across it
    cx, cy, r = 212, 84, 15
    yy, xx = np.mgrid[0:VH, 0:img.shape[1]]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    img[d <= r + 2] = C["dusk6"]
    img[d <= r] = C["dusk7"]
    img[(d <= r - 4)] = C["fire6"]
    for (y, x0, x1, col) in ((79, 180, 248, "dusk5"), (80, 186, 238, "dusk4"), (88, 194, 256, "dusk5"),
                             (89, 202, 252, "dusk4"), (30, 20, 90, "dusk2"), (31, 30, 70, "dusk3"),
                             (46, 180, 250, "dusk3"), (47, 196, 236, "dusk4"), (62, 40, 110, "dusk4")):
        img[y, x0:x1] = C[col]
    # a few early stars in the top band
    r_ = rng(3)
    for _ in range(18):
        x, y = r_.integers(0, img.shape[1]), r_.integers(1, 26)
        put(img, x, y, "dusk5" if r_.random() < 0.5 else "petal3")
    return img


# ---------------------------------------------------------------- peaks

def ridge(w, base, amp, seed, peaks):
    """A ridgeline: a sum of sharp peaks plus fine jag; returns the top y of the mountain at each x."""
    r = rng(seed)
    top = np.full(w, float(base))
    for _ in range(peaks):
        px_, h, sw = r.uniform(0, w), r.uniform(amp * 0.5, amp), r.uniform(18, 46)
        top = np.minimum(top, base - h * np.clip(1 - np.abs(np.arange(w) - px_) / sw, 0, 1) ** 1.2)
    jag = np.cumsum(r.integers(-1, 2, w)) * 0.4
    jag -= np.convolve(jag, np.ones(15) / 15, mode="same")
    return (top + jag).astype(int)


def peaks(layer):
    w = width(layer)
    img = canvas(w, VH)
    if layer == "far":
        top = ridge(w, 100, 46, 11, 7)
        body, lit, haze = "dusk2", "dusk3", "dusk3"
    else:
        top = ridge(w, 108, 40, 23, 6)
        body, lit, haze = "dusk1", "dusk2", "dusk2"
    for x in range(w):
        t = max(0, top[x])
        img[t:, x] = C[body]
        # the slope facing the sun (to the left of each crest: rising ridge) catches light
        if x > 0 and top[x] < top[x - 1] and layer == "near":
            img[t:t + 3, x] = C[lit]
        if layer == "near" and t < 80:                      # snow on the high peaks, lit pink by the sun
            img[t:t + max(1, (80 - t) // 6), x] = C["petal2" if x % 7 else "petal3"]
    # haze at the base: dither toward the sky colour
    for y in range(92 if layer == "far" else 100, VH):
        for x in range(w):
            if img[y, x, 3] and (y - 92) / 30 > BAYER[y % 4, x % 4]:
                img[y, x] = C[haze]
    return img


# ---------------------------------------------------------------- temple (mid layer)

def roof(img, cx, y, half, depth, col_top="jade3", col="jade2", col_dark="jade1"):
    """A curved pagoda roof: eaves sweep up at both ends; the underside is shadowed."""
    for dx in range(-half, half + 1):
        u = abs(dx) / half
        lift = int(round(5 * u ** 3))                       # the upturned eave
        top = y - lift
        bot = y + depth - int(round(2 * u ** 2)) - lift
        x = cx + dx
        if 0 <= x < img.shape[1]:
            img[top:bot, x] = C[col]
            img[top, x] = C[col_top]
            if bot - 1 > top:
                img[bot - 1, x] = C[col_dark]
            if u > 0.93:
                img[top - 1, x] = C["gold2"]                # gilded eave tips
    for dx in range(-half + 3, half - 2, 3):                # tile ribs
        x = cx + dx
        img[y + 1:y + depth - 2, x] = C[col_dark]
    img[y + depth - 1:y + depth + 1, cx - half + 4:cx + half - 3] = C["ink"]


def temple():
    w = width("temple")
    img = canvas(w, VH)
    cx = w // 2 - 6
    # the back wall of the courtyard with a railing
    rect(img, 0, 96, w, 18, "warm2")
    rect(img, 0, 96, w, 2, "warm4"); rect(img, 0, 98, w, 1, "warm3")
    for x in range(4, w, 12):
        rect(img, x, 99, 3, 13, "warm3"); rect(img, x, 99, 1, 13, "warm4")
    rect(img, 0, 112, w, 2, "warm1")
    # the pagoda: three tiers, pillars, a lit doorway
    for tier, (half, top, h) in enumerate(((46, 58, 38), (36, 36, 22), (26, 18, 18))):
        body_top = top + 7
        rect(img, cx - half + 8, body_top, 2 * (half - 8), h - 7, "wood1")
        for px_ in range(cx - half + 10, cx + half - 9, 9):
            rect(img, px_, body_top, 2, h - 7, "crimson1")
            put(img, px_, body_top, "crimson2")
        roof(img, cx, top, half, 7)
    rect(img, cx - 9, 76, 18, 20, "fire3")                  # the doorway glows
    rect(img, cx - 7, 78, 14, 18, "fire4")
    rect(img, cx - 1, 78, 2, 18, "wood1")
    rect(img, cx - 13, 94, 26, 2, "warm4")                  # steps
    rect(img, cx - 17, 96, 34, 2, "warm3")
    # the finial
    rect(img, cx, 4, 1, 14, "gold1")
    for yy in (6, 9, 12):
        rect(img, cx - 2, yy, 5, 1, "gold2")
    put(img, cx, 3, "gold3")
    # two gate posts with a lintel on each side
    for gx in (cx - 110, cx + 104):
        rect(img, gx, 54, 5, 42, "crimson1"); rect(img, gx, 54, 1, 42, "crimson2")
        rect(img, gx + 26, 54, 5, 42, "crimson1"); rect(img, gx + 26, 54, 1, 42, "crimson2")
        rect(img, gx - 6, 48, 43, 4, "crimson2"); rect(img, gx - 6, 48, 43, 1, "crimson3"); rect(img, gx - 8, 46, 47, 2, "ink")
        rect(img, gx - 2, 56, 35, 2, "crimson1")
    return img, cx


LANTERNS = [(-60, 72), (-30, 70), (30, 70), (60, 72), (-18, 49), (18, 49)]     # relative to the pagoda centre


def lantern(t, k):
    """A paper lantern (crimson with a warm core) swaying on its cord; 11 x 16."""
    img = canvas(11, 16)
    sway = int(round(1.2 * math.sin(t * 0.18 + k * 1.7)))
    for y in range(0, 5):
        put(img, 5 + (sway if y > 2 else 0), y, "ink")
    rows = [".ooooo.", "orRRRro", "oRYYYRo", "oRYFYRo", "oRYYYRo", "orRRRro", ".ooooo.", "...g..."]
    key = {"o": "ink", "r": "crimson1", "R": "crimson2", "Y": "fire4", "F": "fire5", "g": "gold2"}
    art(rows, key, 2 + sway, 5, img)
    return img


def banner(t, k, h=30):
    """A hanging cloth banner on a pole, bent with the tear-free twist warp so it ripples in the wind."""
    sys.path.insert(0, str(HERE.parent / "drowned_shrine"))
    from agentdraw.core import scale2x
    w = 9
    src = canvas(w + 12, h + 4)
    rect(src, 6, 2, w, h, "crimson2")
    rect(src, 6, 2, 1, h, "crimson3")
    rect(src, 6 + w - 1, 2, 1, h, "crimson1")
    for y in range(8, h - 4, 7):                            # a gold sigil strip
        rect(src, 8, y, w - 4, 2, "gold2")
    for x in range(6, 6 + w):                               # a notched hem
        if (x - 6) % 3 != 1:
            put(src, x, h + 2, "crimson1")
    src[1, 4:6 + w + 2] = C["wood2"]                        # the crossbar
    big = scale2x(scale2x(scale2x(src)))
    H_, W_ = src.shape[:2]
    yy, xx = np.mgrid[0:H_, 0:W_]
    ax, ay = 6 + w / 2, 2.0
    px_, py_ = xx + 0.5 - ax, yy + 0.5 - ay
    r = np.sqrt(px_ ** 2 + py_ ** 2)
    u = np.clip(r / h, 0, 1)
    ang = np.radians(8 * u ** 1.3 + 9 * np.sin(t * 0.35 + k - r * 0.25) * u)
    sx = (np.cos(ang) * px_ + np.sin(ang) * py_ + ax) * 8
    sy = (-np.sin(ang) * px_ + np.cos(ang) * py_ + ay) * 8
    sx, sy = np.floor(sx).astype(int), np.floor(sy).astype(int)
    ok = (sx >= 0) & (sx < W_ * 8) & (sy >= 0) & (sy < H_ * 8)
    out = canvas(W_, H_)
    out[ok] = big[sy[ok], sx[ok]]
    # the pole
    rect(out, 5, 0, 1, H_, "wood1")
    return out


# ---------------------------------------------------------------- floor and foreground

def floor():
    w = width("floor")
    img = canvas(w, VH)
    y = FLOOR_Y
    rows = [(y, 7), (y + 7, 8), (y + 15, 9), (y + 24, 9)]
    r = rng(5)
    for k, (y0, h) in enumerate(rows):
        slab = 26 + 6 * k
        off = (k % 2) * slab // 2
        rect(img, 0, y0, w, h, "warm3")
        for x0 in range(-off, w, slab):
            # perspective: vertical joints lean away from the stage centre
            lean = (x0 + slab / 2 - w / 2) / (w / 2)
            for yy in range(y0, y0 + h):
                jx = int(round(x0 + lean * (yy - y) * 0.5))
                put(img, jx, yy, "warm1")
                put(img, jx + 1, yy, "warm4" if yy == y0 else "warm2")
            rect(img, x0 + 2, y0, slab - 3, 1, "warm5" if k == 0 else "warm4")      # the lit front edge
            for _ in range(2):
                put(img, x0 + r.integers(3, slab - 2), y0 + r.integers(2, max(3, h - 1)), "warm2")
        rect(img, 0, y0 + h - 1, w, 1, "warm1")
    rect(img, 0, y - 1, w, 1, "warm1")
    return img


def branch(flip=False):
    """A plum branch hanging into the frame, with blossoms; 90 x 40."""
    img = canvas(90, 40)
    r = rng(8)
    pts = [(0, 4), (20, 8), (38, 14), (54, 17), (70, 24), (86, 27)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n):
            x = x0 + (x1 - x0) * i / n; y = y0 + (y1 - y0) * i / n
            th = max(1, int(3 - x / 35))
            for dy in range(th):
                put(img, int(x), int(y) + dy, "warm0" if dy else "warm1")
    for (bx, by) in ((30, 11), (56, 17), (44, 14)):          # twigs
        for i in range(9):
            put(img, bx + i // 2, by + i, "warm0")
    blossoms = [(10, 7), (18, 11), (27, 9), (33, 19), (41, 12), (48, 22), (57, 14), (63, 21), (72, 27), (80, 25), (24, 16), (66, 30)]
    for (bx, by) in blossoms:
        for dx, dy, c in ((0, -1, "petal2"), (-1, 0, "petal2"), (1, 0, "petal1"), (0, 1, "petal1"), (0, 0, "petal3")):
            put(img, bx + dx, by + dy, c)
    return img[:, ::-1].copy() if flip else img


def fg():
    w = width("fg")
    img = canvas(w, VH)
    blit(img, branch(), 0, 0)
    blit(img, branch(flip=True), w - 90, 0)
    return img


# ---------------------------------------------------------------- the stage per tick

class Stage:
    def __init__(self):
        self.sky, self.far, self.near = sky(), peaks("far"), peaks("near")
        self.temple, self.pag_x = temple()
        self.floor, self.fg = floor(), fg()

    def back(self, t, cam):
        """Everything behind the fighters, for camera x cam (0..SCROLL)."""
        img = canvas(VW, VH)
        blit(img, self.sky, 0, 0)
        blit(img, self.far, -int(round(cam * FACTORS["far"])), 0)
        blit(img, self.near, -int(round(cam * FACTORS["near"])), 0)
        tx = -int(round(cam * FACTORS["temple"]))
        blit(img, self.temple, tx, 0)
        for k, (dx, y) in enumerate(LANTERNS):
            blit(img, lantern(t, k), tx + self.pag_x + dx - 5, y - 5)
        for k, bx in enumerate((self.pag_x - 150, self.pag_x - 84, self.pag_x + 78, self.pag_x + 144)):
            blit(img, banner(t, k), tx + bx, 58)
        blit(img, self.floor, -int(round(cam * FACTORS["floor"])), 0)
        return img

    def front(self, img, t, cam):
        blit(img, self.fg, -int(round(cam * FACTORS["fg"])), 0)
        return img


def petals(t, cam, n=16):
    """Plum petals drifting across the stage on the wind (screen space, with a little parallax)."""
    r = rng(99)
    out = []
    for k in range(n):
        x0, y0 = r.uniform(0, VW + 80), r.uniform(-20, VH)
        vx, vy = r.uniform(0.9, 1.8), r.uniform(0.25, 0.6)
        ph = r.uniform(0, 6.28)
        x = (x0 - vx * t - cam * 0.8) % (VW + 80) - 40
        y = (y0 + vy * t + 3 * math.sin(t * 0.2 + ph)) % (VH + 20) - 10
        col = "petal2" if k % 3 else "petal3"
        out.append((int(x), int(y), col))
        if (t // 3 + k) % 2 == 0:
            out.append((int(x) + 1, int(y), "petal1"))
    return out


if __name__ == "__main__":
    from PIL import Image
    S = Stage()
    frames = []
    for cam in (0, 72, 144):
        img = S.back(0, cam)
        S.front(img, 0, cam)
        for (x, y, c) in petals(0, cam):
            if 0 <= x < VW and 0 <= y < VH:
                img[y, x] = C[c]
        frames.append(img)
    sheet = np.concatenate(frames, 0)
    Image.fromarray(sheet).resize((VW * 3, VH * 3 * 3), Image.NEAREST).save(OUT / "stage_check.png")
