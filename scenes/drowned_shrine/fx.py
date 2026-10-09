"""Battle effects, drawn per frame in the scene palette. Each function returns (sprite, (ox, oy)): the sprite and
the offset of its anchor point, so an effect is placed by where it happens, not by its bounding box."""
import math

import numpy as np

from px import C, canvas, put, rect, rng


def _ring_sector(img, cx, cy, r0, r1, a0, a1, col, squash=1.0):
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dx, dy = xx - cx, (yy - cy) / squash
    d = np.sqrt(dx ** 2 + dy ** 2)
    a = np.degrees(np.arctan2(dy, dx)) % 360
    lo, hi = a0 % 360, a1 % 360
    ang = (a >= lo) & (a <= hi) if lo <= hi else (a >= lo) | (a <= hi)
    m = (d >= r0) & (d < r1) & ang
    img[m] = C[col]
    return m


def slash(f, a0=-70, a1=80, r=20, flip=False, ramp=("silver1", "silver2", "silver3", "silver3")):
    """A crescent sword trail, 3 frames: full bright arc -> thinner, trailing -> broken wisps."""
    S = 2 * r + 6
    img = canvas(S, S)
    c = S // 2
    if f == 0:
        _ring_sector(img, c, c, r - 5, r + 1, a0, a1, ramp[0])
        _ring_sector(img, c, c, r - 3, r + 1, a0 + 10, a1, ramp[1])
        _ring_sector(img, c, c, r - 1, r + 1, a0 + 25, a1 - 5, ramp[2])
    elif f == 1:
        _ring_sector(img, c, c, r - 2, r + 2, a0 + 40, a1 + 10, ramp[0])
        _ring_sector(img, c, c, r, r + 2, a0 + 60, a1 + 5, ramp[2])
    elif f == 2:
        m = _ring_sector(canvas(S, S), c, c, r, r + 2, a0 + 80, a1 + 15, ramp[0])
        ys, xs = np.nonzero(m)
        for y, x in zip(ys, xs):
            if (x * 3 + y) % 5 < 2:
                img[y, x] = C[ramp[0]]
    if flip:
        img = img[:, ::-1].copy()
    return img, (c, c)


def spark(f, big=False, cols=("fire6", "fire5", "fire4")):
    """An 8-ray impact star, 4 frames: burst, longer thinner rays, ray tips only, a last glint."""
    n = 15 if big else 11
    img = canvas(n * 2 + 1, n * 2 + 1)
    c = n
    lens = [(5, 3), (9, 5), (n, 8), (n, n - 2)][f] if big else [(4, 2), (7, 4), (n - 1, 7), (n, n - 1)][f]
    for k in range(8):
        a = math.radians(45 * k + (22 if f % 2 else 0) * 0)
        L, start = (lens[0], 0) if k % 2 == 0 else (lens[1], 0)
        start = [0, 2, 5, L - 2][f]
        for t in range(start, L):
            x, y = int(round(c + math.cos(a) * t)), int(round(c + math.sin(a) * t))
            put(img, x, y, cols[0] if t < L * 0.5 else cols[1] if t < L * 0.8 else cols[2])
    if f == 0:
        rect(img, c - 2, c - 1, 5, 3, cols[0]); rect(img, c - 1, c - 2, 3, 5, cols[0])
    return img, (c, c)


def sunburst(f, n=10):
    """Dawn Cleave's burst: a white core, a gold ring expanding and 12 rays, 10 frames."""
    R = 40
    img = canvas(2 * R + 1, 2 * R + 1)
    c = R
    t = f / (n - 1)
    ring_r = 6 + 30 * t
    if f < n - 1:
        _ring_sector(img, c, c, ring_r - (3 if f < 4 else 2), ring_r, 0, 359.9, "fire4" if f < 5 else "fire3", 0.8)
    for k in range(12):
        a = math.radians(30 * k + 15 * (f % 2))
        L0, L1 = 4 + 18 * t, 12 + 28 * min(1, t * 1.6)
        for s in np.arange(L0, L1, 0.7):
            x, y = int(round(c + math.cos(a) * s)), int(round(c + math.sin(a) * s * 0.8))
            put(img, x, y, "fire6" if s < L0 + 4 else "fire5" if s < L0 + 10 else "fire4")
    core = max(0, 9 - f * 2)
    if core:
        yy, xx = np.mgrid[0:2 * R + 1, 0:2 * R + 1]
        d = np.sqrt((xx - c) ** 2 + ((yy - c) / 0.8) ** 2)
        img[d < core] = C["fire5"]; img[d < core * 0.6] = C["fire6"]
    return img, (c, c)


def ring(f, n=6, rx=26, ry=7, col=("water6", "water5", "water4")):
    """An expanding ellipse on the floor or water surface (shockwave / ripple)."""
    t = (f + 1) / n
    W_, H_ = 2 * rx + 3, 2 * ry + 3
    img = canvas(W_, H_)
    cx, cy = rx + 1, ry + 1
    a, b = rx * t, ry * t
    for k in range(int(8 * a) + 8):
        th = 2 * math.pi * k / (int(8 * a) + 8)
        put(img, int(round(cx + a * math.cos(th))), int(round(cy + b * math.sin(th))),
            col[0] if t < 0.4 else col[1] if t < 0.75 else col[2])
    return img, (cx, cy)


def splash(f, seed=0, w=40):
    """Water thrown up and falling back: droplets on parabolas, 8 frames."""
    r = rng(300 + seed)
    img = canvas(w + 8, 48)
    base = 44
    drops = [(r.uniform(-w / 2, w / 2), r.uniform(-1.6, 1.6), r.uniform(4.5, 7.5)) for _ in range(26)]
    for (x0, vx, vy) in drops:
        t = f * 1.1
        x, y = x0 + vx * t * 3, base - (vy * t - 0.55 * t * t) * 3
        if y <= base:
            col = "water6" if vy > 6.5 else "water5" if vy > 5.5 else "water4"
            put(img, int(x + w / 2 + 4), int(y), col)
            if f < 4:
                put(img, int(x + w / 2 + 4), int(y) + 1, "water3")
    return img, (w // 2 + 4, base)


def bubble(age, seed=0):
    """One bubble rising from the pool: grows, wobbles, pops at age 9."""
    img = canvas(7, 7)
    if age >= 10:
        return img, (3, 3)
    if age == 9:
        for (x, y) in ((0, 3), (6, 3), (3, 0), (1, 1), (5, 1)):
            put(img, x, y, "water6")
        return img, (3, 3)
    rr = 1 if age < 3 else 2
    for y in range(7):
        for x in range(7):
            d = (x - 3) ** 2 + (y - 3) ** 2
            if rr * rr - rr <= d <= rr * rr + rr:
                put(img, x, y, "water5")
    put(img, 3 - rr + 1, 3 - rr + 1, "water6")
    return img, (3, 3)


def stun_stars(f, rx=11, ry=3):
    """Three little stars orbiting over a stunned head."""
    img = canvas(2 * rx + 5, 2 * ry + 7)
    cx, cy = rx + 2, ry + 3
    for k in range(3):
        th = 2 * math.pi * (k / 3 + f / 8)
        x, y = int(round(cx + rx * math.cos(th))), int(round(cy + ry * math.sin(th)))
        col = "gold3" if math.sin(th) > 0 else "gold2"
        put(img, x, y, col); put(img, x - 1, y, col); put(img, x + 1, y, col); put(img, x, y - 1, col); put(img, x, y + 1, col)
        if math.sin(th) > 0:
            put(img, x, y, "fire6")
    return img, (cx, cy)


def charge(f, R=26):
    """Light being drawn into the lure: motes spiralling inward and a contracting ring, 8-frame cycle."""
    img = canvas(2 * R + 1, 2 * R + 1)
    c = R
    for k in range(10):
        ph = (f / 8 + k / 10) % 1
        rad = R * (1 - ph)
        th = 2 * math.pi * (k * 0.37 + ph * 0.5)
        x, y = int(round(c + rad * math.cos(th))), int(round(c + rad * math.sin(th)))
        put(img, x, y, "fire6" if ph > 0.6 else "fire5")
        if ph < 0.6:
            put(img, x + (1 if math.cos(th) < 0 else -1), y, "fire4")
    rr = R * (1 - (f % 8) / 8)
    if rr > 3:
        _ring_sector(img, c, c, rr - 1, rr, 0, 359.9, "fire4")
    return img, (c, c)


def motes(pixels, f, seed=0):
    """The boss dissolving: each (x, y, col) pixel drifts upward with its own speed and wobble, turning to glow
    colours, and winks out; f = 0.. ~24. Returns a list of (x, y, colour name) to draw in scene space."""
    r = rng(400 + seed)
    out = []
    for i, (x, y, col) in enumerate(pixels):
        delay = r.uniform(0, 10) + (1 - y / 200) * 0            # not all at once
        spd = r.uniform(0.6, 1.6)
        t = f - delay
        if t < 0:
            out.append((x, y, col)); continue
        life = r.uniform(6, 14)
        if t > life:
            continue
        nx = x + math.sin(t * 0.5 + i) * 1.5
        ny = y - spd * t * 1.4
        c2 = "glow2" if t < life * 0.3 else "glow1" if t < life * 0.7 else "glow0"
        if (i % 3 == 0) or t < 2:
            out.append((int(round(nx)), int(round(ny)), c2))
    return out


def plume(f, w=22, h=40):
    """A column of water bursting up (the boss surfacing), 8 frames: rises to full height by f=2, then
    breaks into falling sheets and drops. Anchored at its base centre."""
    img = canvas(w + 24, h + 10)
    cx, base = (w + 24) // 2, h + 6
    r = rng(77)
    top = [h * 0.55, h * 0.9, h, h * 0.95, h * 0.8, h * 0.55, h * 0.3, h * 0.1][f]
    width = [w * 0.5, w * 0.7, w * 0.8, w, w * 1.1, w * 1.2, w * 1.3, w * 1.3][f]
    for y in range(int(base - top), base):
        u = (base - y) / max(1, top)                       # 0 at the base, 1 at the crest
        half = width / 2 * (1 - 0.5 * u) if f < 4 else width / 2 * (0.6 + 0.4 * u)
        if u > 0.78 and f < 4:
            half *= max(0.15, math.sqrt(max(0.0, 1 - ((u - 0.78) / 0.22) ** 2)))
        for x in range(int(cx - half), int(cx + half) + 1):
            edge = abs(x - cx) > half - 1.5
            if f >= 4 and not edge and (x * 7 + y * 3 + f) % 5 < 3:
                continue                                    # the column hollows out as it collapses
            col = "water6" if u > 0.8 or edge and x < cx else "water5" if edge else "water4" if (x + y) % 3 else "water5"
            put(img, x, y, col)
    for k in range(18):                                     # thrown droplets
        a = r.uniform(-2.4, -0.7)
        v = r.uniform(3, 6)
        t = f * 0.9
        x = cx + math.cos(a) * v * t * 1.6
        y = base - top * 0.7 + (math.sin(a) * v * t + 0.8 * t * t) * 1.3
        if 0 <= x < w + 24 and 0 <= y < h + 10:
            put(img, int(x), int(y), "water6" if k % 3 else "water5")
            put(img, int(2 * cx - x), int(y), "water5")
    return img, (cx, base)


def fireflies(t, n=14, w=320, h=180, seed=5):
    """Drifting glow motes: each wanders on its own Lissajous path and pulses; returns (x, y, colour)."""
    r = rng(900 + seed)
    out = []
    for k in range(n):
        x0, y0 = r.uniform(0, w), r.uniform(20, h - 40)
        ax, ay = r.uniform(8, 22), r.uniform(4, 10)
        fx_, fy_ = r.uniform(0.02, 0.05), r.uniform(0.03, 0.07)
        ph = r.uniform(0, 6.28)
        x = x0 + ax * math.sin(fx_ * t + ph)
        y = y0 + ay * math.sin(fy_ * t + ph * 1.3)
        pulse = (math.sin(0.25 * t + ph * 3) + 1) / 2
        if pulse < 0.15:
            continue
        col = "glow2" if pulse > 0.75 else "glow1" if pulse > 0.4 else "glow0"
        out.append((int(round(x)), int(round(y)), col))
    return out
