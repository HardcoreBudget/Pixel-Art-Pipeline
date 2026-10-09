"""The Drowned Shrine tileset: 16x16 tiles drawn by rule, pixel by pixel, in the scene palette.

Ground tiles are opaque (floor slabs, wall, water autotile); deco and object tiles are transparent and sit on
layers above. Animated tiles (water, flames, glowing mushrooms) have 4 frames; the rest repeat one image.
Patterns that must continue across tiles (water ripples, the floor's texture) are functions of the tile's
position modulo a period, so any neighbour lines up."""
import numpy as np

from px import C, canvas, rect, put, art, rng

T = 16
FR = 4


def tile():
    return canvas(T, T)


# ---------------------------------------------------------------- floor

def slab(img, x, y, w, h, seed, crack=False, moss=0, open_=""):
    """One paving slab: base stone1, lit top/left edge (stone2), shadowed bottom/right (stone0), a few specks.
    open_ names the sides ('l','r','t','b') where the slab continues into the next tile: no edge drawn there."""
    r = rng(seed)
    rect(img, x, y, w, h, "stone1")
    if "t" not in open_:
        rect(img, x, y, w, 1, "stone2")
    if "l" not in open_:
        rect(img, x, y, 1, h, "stone2")
    if "t" not in open_ and "l" not in open_:
        put(img, x, y, "stone3")
    if "b" not in open_:
        rect(img, x, y + h - 1, w, 1, "stone0")
    if "r" not in open_:
        rect(img, x + w - 1, y, 1, h, "stone0")
    for _ in range(max(1, w * h // 28)):
        sx, sy = x + 1 + r.integers(0, max(1, w - 2)), y + 1 + r.integers(0, max(1, h - 2))
        put(img, sx, sy, "stone0" if r.random() < 0.6 else "stone2")
    if crack:
        cx, cy = x + 2 + r.integers(0, max(1, w - 6)), y + 1
        while cy < y + h - 1 and x < cx < x + w - 1:
            put(img, cx, cy, "night1"); put(img, cx + 1, cy, "stone2")
            cy += 1; cx += r.integers(-1, 2)
    for _ in range(moss):
        mx, my = x + r.integers(0, w), y + h - 1 - r.integers(0, 2)
        put(img, mx, my, "moss2"); put(img, mx, my - 1, "moss1")


def floor(variant, seed=0, shadow=False):
    img = _floor(variant, seed)
    if shadow:                                # the wall's shadow on the first floor row: a ramp step darker
        from px import ramp_step
        m = np.zeros((T, T), bool); m[:6] = True
        m[6] = (np.arange(T) % 2 == 0); m[7] = (np.arange(T) % 4 == 1)
        img = ramp_step(img, -1, m)
    return img


def _floor(variant, seed=0):
    img = tile()
    rect(img, 0, 0, T, T, "night1")          # mortar shows wherever slabs leave a gap
    s = 100 * variant + seed
    if variant == 0:
        slab(img, 0, 0, 15, 15, s)
    elif variant == 1:
        slab(img, 0, 0, 15, 7, s); slab(img, 0, 8, 15, 7, s + 1)
    elif variant == 2:
        slab(img, 0, 0, 7, 15, s); slab(img, 8, 0, 7, 15, s + 1)
    elif variant == 3:
        for i, (x, y) in enumerate(((0, 0), (8, 0), (0, 8), (8, 8))):
            slab(img, x, y, 7, 7, s + i)
    elif variant == 4:
        slab(img, 0, 0, 15, 15, s, crack=True)
    elif variant == 6:                       # a long slab spanning two tiles: left half
        slab(img, 0, 0, 16, 15, s, open_="r")
    elif variant == 7:                       # ... and its right half
        slab(img, 0, 0, 15, 15, s + 7, open_="l")
    elif variant == 8:                       # a tall slab spanning two tiles: top half
        slab(img, 0, 0, 15, 16, s, open_="b")
    elif variant == 9:                       # ... and its bottom half
        slab(img, 0, 0, 15, 15, s + 9, open_="t")
    elif variant == 5:                       # mossy mortar: moss grows in the joints
        slab(img, 0, 0, 7, 15, s); slab(img, 8, 0, 7, 15, s + 1)
        r = rng(s)
        for y in range(T):
            if r.random() < 0.6:
                put(img, 7, y, "moss2" if r.random() < 0.7 else "moss3")
        for x in range(T):
            if r.random() < 0.6:
                put(img, x, 15, "moss2" if r.random() < 0.7 else "moss3")
        for _ in range(4):
            put(img, 6 + r.integers(0, 3), r.integers(0, 16), "moss1")
    return img


# ---------------------------------------------------------------- wall

def wall_face(variant=0, seed=0):
    """Brick courses 5 px tall, staggered; the face is darker than the floor (it faces away from the moon)."""
    img = tile()
    rect(img, 0, 0, T, T, "night0")
    r = rng(500 + seed + 10 * variant)
    for row, y in enumerate(range(0, T, 4)):
        off = 0 if row % 2 == 0 else 4
        for x in range(-8 + off, T, 8):
            x0, x1 = max(0, x), min(T, x + 7)
            if x1 <= x0:
                continue
            rect(img, x0, y, x1 - x0, 3, "stone0")
            rect(img, x0, y, x1 - x0, 1, "stone1")
            if r.random() < 0.25:
                put(img, x0 + r.integers(0, max(1, x1 - x0)), y + 1 + r.integers(0, 2), "night1")
            if r.random() < 0.12:
                put(img, x0 + r.integers(0, max(1, x1 - x0)), y, "stone2")
    if variant == 1:                         # vines hanging down the face
        for vx in (3, 11):
            length = 8 + r.integers(0, 8)
            for y in range(length):
                xx = vx + (1 if (y // 3) % 2 else 0)
                put(img, xx, y, "moss2")
                if y % 3 == 1:
                    put(img, xx + 1, y, "moss3"); put(img, xx - 1, y + 1, "moss1")
            put(img, vx, length, "moss3")
    if variant == 2:                         # a missing brick
        rect(img, 5, 4, 7, 3, "ink"); rect(img, 5, 6, 7, 1, "night1")
    return img


def wall_top(seed=0):
    """Overgrowth along the coping: leaf clumps over a stone lip; the lip casts a line of shadow on the face."""
    img = tile()
    r = rng(700 + seed)
    rect(img, 0, 0, T, 11, "moss0")
    for _ in range(9):
        cx, cy = r.integers(-2, 18), r.integers(0, 9)
        for dy in range(-2, 3):
            for dx in range(-3, 4):
                if dx * dx / 9 + dy * dy / 4 <= 1:
                    put(img, cx + dx, cy + dy, "moss1" if dy >= 0 else "moss2")
        put(img, cx - 1, cy - 2, "moss3"); put(img, cx, cy - 2, "moss3")
    rect(img, 0, 11, T, 1, "stone3"); rect(img, 0, 12, T, 2, "stone2"); rect(img, 0, 14, T, 1, "stone1")
    rect(img, 0, 15, T, 1, "ink")
    for x in range(T):                        # leaves spilling over the lip
        if r.random() < 0.3:
            put(img, x, 11, "moss2"); put(img, x, 12, "moss1")
    return img


def arch(part):
    """The shrine archway, 2x2 tiles: part = (col, row). A dark passage with a faint glow deep inside."""
    img = tile()
    big = canvas(32, 32)
    # the face around it
    for ty in range(2):
        for tx in range(2):
            big[ty * 16:(ty + 1) * 16, tx * 16:(tx + 1) * 16] = wall_face(0, 20 + tx + 2 * ty)
    yy, xx = np.mgrid[0:32, 0:32]
    opening = ((xx - 15.5) ** 2 / 11.5 ** 2 + (yy - 14) ** 2 / 12 ** 2 <= 1) | ((abs(xx - 15.5) <= 11.5) & (yy >= 14))
    keystones = ((xx - 15.5) ** 2 / 13.5 ** 2 + (yy - 14) ** 2 / 14 ** 2 <= 1) | ((abs(xx - 15.5) <= 13.5) & (yy >= 14))
    ring = keystones & ~opening
    big[ring] = C["stone2"]
    big[ring & (yy < 14) & ((xx + yy) % 4 == 0)] = C["stone0"]         # voussoir joints
    big[ring & (xx < 16) & (yy < 12)] = C["stone3"]
    big[opening] = C["ink"]
    inner = opening & ((xx - 15.5) ** 2 / 7 ** 2 + (yy - 22) ** 2 / 8 ** 2 <= 1)
    big[inner] = C["night0"]
    for (gx, gy) in ((12, 27), (13, 26), (19, 28), (18, 27), (16, 29)):   # far mushrooms glowing in the dark
        big[gy, gx] = C["glow0"]
    big[25, 13] = C["glow1"]; big[26, 18] = C["glow1"]
    return big[part[1] * 16:(part[1] + 1) * 16, part[0] * 16:(part[0] + 1) * 16].copy()


def moon_emblem():
    """A carved crescent above the arch (deco tile, transparent)."""
    rows = ["......oooo......",
            "....ooMMMMoo....",
            "...oMMmmmmMMo...",
            "..oMmmo..oomMo..",
            "..oMmo.....oMo..",
            ".oMmo.......oo..",
            ".oMmo...........",
            ".oMmo.......oo..",
            "..oMmo.....oMo..",
            "..oMmmo..oomMo..",
            "...oMMmmmmMMo...",
            "....ooMMMMoo....",
            "......oooo......"]
    img = tile()
    return art(rows, {"o": "ink", "M": "stone3", "m": "stone2"}, 0, 1, img)


# ---------------------------------------------------------------- water

WATER_MASK = {}


def water_px(gx, gy, f):
    """The water's colour at global pixel (gx, gy), frame f: deep base, drifting ripple dashes, sparse glints.
    Periodic in 16 px both ways so tiles line up."""
    x, y = gx % 16, gy % 16
    col = "water1" if (y // 4) % 2 == 0 else "water1"
    # ripple dashes: short horizontal highlights on staggered rows, drifting right 1 px per frame
    for (ry, rx, ln) in ((2, 1, 4), (6, 9, 5), (10, 4, 3), (13, 12, 4)):
        if y == ry and (x - rx - f) % 16 < ln:
            col = "water2"
        if y == ry - 1 and (x - rx - f - 1) % 16 < ln - 2:
            col = "water3"
    if (x, y) in (((5 + 4 * f) % 16, 8), ((13 + 4 * f) % 16, 3)) and f % 2 == 0:
        col = "water4"
    return col


def water(flags, f):
    """A pool tile. flags: the set of directions (N,S,E,W,NE,NW,SE,SW) where the neighbour is LAND.
    Land edges: N shows the pool's inner stone face (4 px) with a foam line; S a 2-px lit rim; E/W 2-px rims."""
    img = floor(0, 3)                         # land under everything; water drawn over it
    yy, xx = np.mgrid[0:T, 0:T]
    wet = np.ones((T, T), bool)
    top = 5 if "N" in flags else 0
    bot = 2 if "S" in flags else 0
    lef = 2 if "W" in flags else 0
    rig = 2 if "E" in flags else 0
    wet &= (yy >= top) & (yy < T - bot) & (xx >= lef) & (xx < T - rig)
    # rounded outer corners
    for d, (cx, cy) in {"NW": (lef, top), "NE": (T - 1 - rig, top), "SW": (lef, T - 1 - bot), "SE": (T - 1 - rig, T - 1 - bot)}.items():
        a, b = d[0], d[1]
        if a in flags and b in flags:
            sx = 1 if b == "W" else -1; sy = 1 if a == "N" else -1
            for (dx, dy) in ((0, 0), (1, 0), (0, 1)):
                wet[cy + sy * dy, cx + sx * dx] = False
    # inner corners (diagonal land, both sides water): a small stone notch
    for d in ("NW", "NE", "SW", "SE"):
        if d in flags and d[0] not in flags and d[1] not in flags:
            h = 5 if d[0] == "N" else 2
            x0 = 0 if d[1] == "W" else T - 2
            y0 = 0 if d[0] == "N" else T - h
            wet[y0:y0 + h, x0:x0 + 2] = False
            if d[0] == "N":
                wet[y0:y0 + 2, (0 if d[1] == "W" else T - 3):(0 if d[1] == "W" else T - 3) + 3] = False
    for y in range(T):
        for x in range(T):
            if wet[y, x]:
                img[y, x] = C[water_px(x, y, f)]
    dry = ~wet
    # the N face: land rows just above water (in 3/4 view the pool's back wall faces us)
    face = dry & np.roll(wet, -1, 0) | dry & np.roll(wet, -2, 0) | dry & np.roll(wet, -3, 0) | dry & np.roll(wet, -4, 0)
    face &= (yy < T - 1)
    faceN = face & ~(np.roll(wet, 1, 0) & (yy > 0))
    for y in range(T):
        for x in range(T):
            if faceN[y, x] and ("N" in flags or ("NW" in flags or "NE" in flags) and y < 5):
                below = [wet[min(T - 1, y + k), x] for k in (1, 2, 3, 4)]
                if below[0]:
                    img[y, x] = C["stone0"]
                elif below[1] or below[2]:
                    img[y, x] = C["stone1"]
                elif below[3]:
                    img[y, x] = C["stone3"]
    # side and bottom rims: the pixel of land touching water is lit
    touch = dry & (np.roll(wet, 1, 0) | np.roll(wet, 1, 1) | np.roll(wet, -1, 1))
    touch &= ~faceN | ~(np.roll(wet, -1, 0))
    for y in range(T):
        for x in range(T):
            if touch[y, x] and not (y + 1 < T and wet[y + 1, x]):
                img[y, x] = C["stone3"] if (y > 0 and wet[y - 1, x]) else C["stone2"]
    # foam where the N face meets water
    for x in range(T):
        for y in range(1, T):
            if wet[y, x] and not wet[y - 1, x] and (x + f) % 3 != 0:
                img[y, x] = C["water4"]
    # the shadow the face casts on the water's first rows
    for x in range(T):
        for y in range(2, T):
            if wet[y, x] and not wet[y - 2, x] and wet[y - 1, x]:
                img[y, x] = C["water0"]
    return img


# ---------------------------------------------------------------- objects and deco (transparent)

def pillar(part, broken=False):
    """A round column, 1 tile wide: part 0 = capital (top), 1 = shaft, 2 = base. Moonlit from the left."""
    img = tile()
    bands = ["ink", "stone1", "stone3", "stone4", "stone3", "stone2", "stone2", "stone1", "stone1", "stone0", "ink"]
    x0 = 3
    if part == 1:
        for i, b in enumerate(bands):
            rect(img, x0 + i - 1 + 1, 0, 1, T, b)
        for y in (5, 11):                      # drums
            rect(img, x0 + 1, y, 9, 1, "stone0"); put(img, x0 + 2, y, "stone2")
        for (x, y) in ((6, 2), (7, 3), (7, 8), (8, 9)):
            put(img, x, y, "stone1")
        if broken:
            img[:6] = 0
            for x, h in zip(range(x0 + 1, x0 + 10), (7, 6, 4, 5, 3, 4, 6, 5, 7)):
                img[:h, x] = 0
                put(img, x, h, "stone4")
    elif part == 0:
        rect(img, 1, 8, 14, 4, "ink"); rect(img, 2, 8, 12, 3, "stone2"); rect(img, 2, 8, 12, 1, "stone4")
        rect(img, 0, 5, 16, 3, "ink"); rect(img, 1, 5, 14, 2, "stone3"); rect(img, 1, 5, 14, 1, "stone4")
        for i, b in enumerate(bands):
            rect(img, x0 + i, 12, 1, 4, b)
        for (x, y, c) in ((3, 4, "moss2"), (4, 4, "moss2"), (5, 3, "moss3"), (11, 4, "moss1"), (12, 4, "moss2"),
                          (2, 5, "moss2"), (3, 5, "moss3"), (12, 5, "moss2"), (4, 12, "moss2"), (4, 13, "moss1")):
            put(img, x, y, c)
    else:
        for i, b in enumerate(bands):
            rect(img, x0 + i, 0, 1, 9, b)
        rect(img, 1, 9, 14, 4, "ink"); rect(img, 2, 9, 12, 3, "stone2"); rect(img, 2, 9, 12, 1, "stone3")
        rect(img, 0, 13, 16, 3, "ink"); rect(img, 1, 13, 14, 2, "stone1"); rect(img, 1, 13, 14, 1, "stone3")
        for x in range(2, 14, 3):
            put(img, x, 12, "moss2")
    return img


def brazier(part, f):
    """A stone brazier, 1x2 tiles: part 0 = the flame (animated, 4 frames), part 1 = bowl and pedestal."""
    img = tile()
    if part == 1:
        rows = ["oooooooooooooooo",
                "oMMMMMMMMMMMMMMo",
                ".ommmmmmmmmmmmo.",
                "..osssssssssso..",
                "...ooosssssooo..",
                ".....osssso.....",
                ".....omsmso.....",
                ".....omssso.....",
                ".....omssso.....",
                ".....omssso.....",
                "....osmssss o...",
                "...oMMMMMMMMo...",
                "...ommmmmmmmo...",
                "..oooooooooooo..",
                "................",
                "................"]
        art(rows, {"o": "ink", "M": "stone3", "m": "stone2", "s": "stone1"}, 0, 0, img)
        rect(img, 2, 0, 12, 1, "fire2"); rect(img, 4, 0, 8, 1, "fire3")
        return img
    # flame: a teardrop that leans and flickers; layered ramps from the rim up
    lean = [0, 1, 0, -1][f]
    hgt = [12, 14, 13, 11][f]
    for y in range(hgt):
        t = y / hgt                                   # 0 at the rim, 1 at the tip
        half = (5.5 * (1 - t) ** 0.8) * (0.9 if f % 2 else 1.0)
        cx = 7.5 + lean * t * 2
        for x in range(T):
            d = abs(x - cx)
            if d <= half:
                yy = T - 1 - y
                inner = d / max(half, 0.5)
                col = "fire2" if inner > 0.75 else "fire3" if inner > 0.45 else "fire4" if t > 0.25 or inner > 0.25 else "fire5"
                if t < 0.35 and inner < 0.3:
                    col = "fire6"
                put(img, x, yy, col)
    for (x, y) in (((4 + 3 * f) % 13 + 1, 2), ((9 + 5 * f) % 13 + 1, 0)):
        put(img, x, y, "fire4")                       # rising embers
    return img


def mushrooms(f, variant=0):
    """A cluster of glowing cyan mushrooms; the caps pulse glow0 -> glow1 -> glow2."""
    img = tile()
    pulse = [0, 1, 2, 1][f]
    caps = [(4, 9, 3), (10, 11, 2), (7, 12, 2)] if variant == 0 else [(5, 11, 2), (10, 9, 3)]
    for (cx, cy, r) in caps:
        for y in range(cy, 16):
            if y > cy + r - 1:
                put(img, cx, y, "cream0"); put(img, cx + 1, y, "cream1")
        for dy in range(-r, 1):
            for dx in range(-r - 1, r + 2):
                if dx * dx / (r + 1.2) ** 2 + dy * dy / r ** 2 <= 1:
                    put(img, cx + dx, cy + dy, "glow0")
        for dx in range(-r, r + 1):
            put(img, cx + dx, cy - r + 1 if r > 2 else cy - 1, ["glow0", "glow1", "glow2"][pulse])
        put(img, cx - r + 1, cy - r + (1 if r > 2 else 0), "glow2")
        for dx in range(-r - 1, r + 2):
            put(img, cx + dx, cy + 1, "teal0")
    return img


def tuft(seed=0):
    img = tile()
    r = rng(900 + seed)
    for i in range(6):
        x = 3 + r.integers(0, 10); h = 3 + r.integers(0, 4)
        for y in range(h):
            put(img, x + (1 if y > h // 2 and i % 2 else 0), 15 - y, "moss3" if y < h - 1 else "moss4")
        put(img, x, 15, "moss1")
    return img


def lily(f):
    img = tile()
    rows = ["..oooo..",
            ".oMMmMo.",
            "oMmmmMmo",
            "omm.mmmo",
            ".ommmmo.",
            "..oooo.."]
    art(rows, {"o": "moss0", "M": "moss4", "m": "moss3"}, 4, 6 + (1 if f in (1, 2) else 0), img)
    if f == 2:
        put(img, 9, 5, "crimson3")
    put(img, 8, 7 + (1 if f in (1, 2) else 0), "crimson3")
    put(img, 9, 7 + (1 if f in (1, 2) else 0), "crimson4")
    return img


def rubble(seed=0):
    img = tile()
    r = rng(950 + seed)
    for _ in range(3):
        x, y = 2 + r.integers(0, 10), 8 + r.integers(0, 6)
        w = 2 + r.integers(0, 3)
        rect(img, x, y, w, 2, "stone2"); rect(img, x, y, w, 1, "stone3"); rect(img, x, y + 2, w, 1, "ink")
    return img


def fern(part, f):
    """Foreground fern fronds (drawn in front of the fighters), 2 tiles wide: part = 0 (left) or 1 (right)."""
    big = canvas(32, 16)
    sway = [0, 1, 1, 0][f]
    for (bx, ang, ln) in ((6, -0.9, 16), (12, -0.35, 15), (18, 0.2, 14), (24, 0.7, 13)):
        for k in range(ln):
            t = k / ln
            x = int(round(bx + np.sin(ang) * k + sway * t))
            y = int(round(15 - np.cos(ang) * k * 0.9))
            put(big, x, y, "moss1")
            if k % 2 == 0 and k > 2:
                put(big, x - 1, y, "moss2"); put(big, x + 1, y + 1, "moss2")
                if k % 4 == 0:
                    put(big, x - 2, y + 1, "moss3"); put(big, x + 2, y + 1, "moss0")
    return big[:, part * 16:(part + 1) * 16].copy()


def vine(f, length=14):
    img = tile()
    sway = [0, 0, 1, 1][f]
    for y in range(length):
        x = 8 + (sway if y > length // 2 else 0)
        put(img, x, y, "moss2")
        if y % 3 == 0:
            put(img, x - 1, y, "moss3"); put(img, x + 1, y + 1, "moss1")
    return img


def moss_patch(part, seed=0, size=(2, 2)):
    """An organic moss carpet over the floor (deco, transparent), size tiles wide/high; part = (col, row).
    Soft edge: the blob's rim is dithered moss1 over the stone, the body moss2 with moss3 tufts."""
    W_, H_ = size[0] * T, size[1] * T
    big = canvas(W_, H_)
    r = rng(1200 + seed)
    yy, xx = np.mgrid[0:H_, 0:W_]
    d = np.full((H_, W_), 9.0)
    for _ in range(5):
        cx, cy = r.uniform(W_ * .35, W_ * .65), r.uniform(H_ * .35, H_ * .65)
        rx, ry = r.uniform(W_ * .16, W_ * .26), r.uniform(H_ * .14, H_ * .22)
        d = np.minimum(d, ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    body = d <= 1.0
    rim = (d > 1.0) & (d <= 1.45) & ((xx + yy) % 2 == 0)
    big[body] = C["moss1"]; big[rim] = C["moss1"]
    inner = d <= 0.55
    big[inner & ((xx * 3 + yy * 5) % 7 < 4)] = C["moss2"]
    for _ in range(int(body.sum() // 22)):
        ys, xs = np.nonzero(inner)
        if len(xs):
            i = r.integers(0, len(xs)); put(big, xs[i], ys[i], "moss3"); put(big, xs[i], ys[i] - 1, "moss4")
    return big[part[1] * T:(part[1] + 1) * T, part[0] * T:(part[0] + 1) * T].copy()
