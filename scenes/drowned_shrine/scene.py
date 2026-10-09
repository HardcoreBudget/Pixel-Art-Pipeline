"""The Drowned Shrine battle, composed tick by tick. Every visual state is a pure function of the tick t (80 ms),
so any frame can be rendered alone and the loop is exact: t = N wraps to t = 0.

Draw order: ground+deco tiles -> ground shadows -> boss reflection (on water only) -> fighters (y-sorted) ->
effects -> front tiles -> lighting (palette ramp steps) -> UI (never lit) -> fade."""
import json
import math
import pathlib

import numpy as np
from PIL import Image

import fx
import light as LI
import tilemap as TM
import ui as U
from font import text, BIG
from px import C, canvas, blit, OUT, ramp_step, RAMPS, DESIGNS

N = 336
VW, VH = 320, 180
HERO_HOME = (70, 136)          # feet
HERO_ATK = (158, 134)
BOSS_HOME = (208, 96)          # body centre
POOL_Y = 124                   # the waterline the boss's reflection mirrors about
SPR = OUT / "sprites"


def lerp(a, b, u):
    return a + (b - a) * u


def ease(u, k="io"):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u) if k == "io" else 1 - (1 - u) ** 2 if k == "o" else u * u if k == "i" else u


def seg(t, t0, t1):
    return (t - t0) / max(1, t1 - t0)


# ---------------------------------------------------------------- sprites

class Sheet:
    """Animations of one character: SPR/<name>/<anim>_<i>.png, 64x64, anchor given per character."""

    def __init__(self, name, anchor, placeholder):
        self.name, self.anchor, self.ph = name, anchor, placeholder
        self.cache = {}

    def get(self, anim, i):
        key = (anim, i)
        if key not in self.cache:
            d = SPR / self.name
            files = sorted(d.glob(f"{anim}_*.png")) if d.exists() else []
            if files:
                self.cache[key] = np.asarray(Image.open(files[i % len(files)]).convert("RGBA")).copy()
            else:
                self.cache[key] = self.ph(anim, i)
        return self.cache[key]

    def count(self, anim):
        d = SPR / self.name
        return len(list(d.glob(f"{anim}_*.png"))) if d.exists() else 1


def _ph_hero(anim, i):
    img = canvas(64, 64)
    yy, xx = np.mgrid[0:64, 0:64]
    img[((xx - 32) / 8) ** 2 + ((yy - 40) / 20) ** 2 <= 1] = C["teal2"]
    img[((xx - 32) / 5) ** 2 + ((yy - 22) / 5) ** 2 <= 1] = C["skin2"]
    img[(abs(xx - 44) <= 10) & (abs(yy - 40) <= 0)] = C["silver3"]
    return img


def _ph_boss(anim, i):
    img = canvas(64, 64)
    yy, xx = np.mgrid[0:64, 0:64]
    img[((xx - 34) / 26) ** 2 + ((yy - 32) / 20) ** 2 <= 1] = C["violet2"]
    img[((xx - 20) / 4) ** 2 + ((yy - 26) / 4) ** 2 <= 1] = C["glow1"]
    img[((xx - 8) / 3) ** 2 + ((yy - 8) / 3) ** 2 <= 1] = C["fire5"]
    return img


HERO = Sheet("kestrel", (48, 76), _ph_hero)
BOSS = Sheet("gloomlure", (40, 40), _ph_boss)
_LURES = None


def lure_pos(t):
    """The lure bulb's centre in scene space for tick t (from the frame it is drawn in)."""
    global _LURES
    if _LURES is None:
        f = SPR / "gloomlure" / "lures.json"
        _LURES = json.loads(f.read_text()) if f.exists() else {}
    ba, bf, bx, by, _, _ = boss_state(t)
    lx, ly = _LURES.get(f"{ba}_{bf % max(1, BOSS.count(ba))}", (14, 18))
    return bx + lx - 40, by + ly - 40


def loop_frame(t, n, every=2):
    return (t // every) % n


# ---------------------------------------------------------------- choreography

def hero_state(t):
    """(anim, frame, feet_x, feet_y, lift) - lift raises the sprite above its shadow."""
    hx_, hy = HERO_HOME
    nid = HERO.count("idle")
    idle = ("idle", loop_frame(t, nid, 2), hx_, hy, 0)
    if 62 <= t < 70:                                   # run in
        u = ease(seg(t, 62, 70), "i")
        return ("run", loop_frame(t, HERO.count("run"), 1), lerp(hx_, HERO_ATK[0], u), lerp(hy, HERO_ATK[1], u), 0)
    if 70 <= t < 78:
        return ("slash1", min(HERO.count("slash1") - 1, (t - 70) * HERO.count("slash1") // 8), *HERO_ATK, 0)
    if 78 <= t < 90:
        return ("slash2", min(HERO.count("slash2") - 1, (t - 78) * HERO.count("slash2") // 10), *HERO_ATK, 0)
    if 90 <= t < 100:                                  # hop back home in an arc
        u = ease(seg(t, 90, 100), "o")
        return ("hop", min(HERO.count("hop") - 1, (t - 90) * HERO.count("hop") // 10),
                lerp(HERO_ATK[0], hx_, u), lerp(HERO_ATK[1], hy, u), 16 * math.sin(math.pi * u))
    if 112 <= t < 122:                                 # block the bite
        k = 0 if t < 114 else 1 if t < 118 else 2
        push = 0 if t < 116 else -2 if t < 118 else -1
        return ("block", k, hx_ + push, hy, 0)
    if 194 <= t < 202:
        u = ease(seg(t, 194, 202), "i")
        return ("run", loop_frame(t, HERO.count("run"), 1), lerp(hx_, HERO_ATK[0], u), lerp(hy, HERO_ATK[1], u), 0)
    if 202 <= t < 210:
        return ("slash1", min(HERO.count("slash1") - 1, (t - 202) * HERO.count("slash1") // 8), *HERO_ATK, 0)
    if 210 <= t < 222:                                 # leap up over the boss
        u = seg(t, 210, 222)
        x = lerp(HERO_ATK[0], BOSS_HOME[0] - 8, ease(u, "o"))
        return ("leap", min(HERO.count("leap") - 1, int(u * HERO.count("leap"))), x, HERO_ATK[1], 70 * math.sin(math.pi * 0.5 * ease(u, "o")))
    if 222 <= t < 230:                                 # plunge
        u = ease(seg(t, 222, 225), "i")
        k = min(HERO.count("plunge") - 1, (t - 222) * HERO.count("plunge") // 8)
        return ("plunge", k, BOSS_HOME[0] - 8, HERO_ATK[1], lerp(70, 34, u))
    if 230 <= t < 246:                                 # long hop home
        u = ease(seg(t, 230, 246), "io")
        return ("hop", min(HERO.count("hop") - 1, (t - 230) * HERO.count("hop") // 16),
                lerp(BOSS_HOME[0] - 8, hx_, u), lerp(HERO_ATK[1], hy, u), lerp(34, 0, u) + 26 * math.sin(math.pi * u))
    if 286 <= t < 320:
        return ("victory", min(HERO.count("victory") - 1, (t - 286) // 3), hx_, hy, 0)
    return idle


def boss_state(t):
    """(anim, frame, cx, cy, waterline_clip or None, visible)."""
    bx, by = BOSS_HOME
    nid = BOSS.count("idle")
    bob = round(2 * math.sin(t * 2 * math.pi / 24))
    idle = ("idle", loop_frame(t, nid, 2), bx, by + bob, None, True)
    if t < 20:
        return ("idle", 0, bx, by + 60, POOL_Y, False)
    if t < 32:                                         # rising out of the pool
        u = ease(seg(t, 20, 32), "o")
        return ("idle", loop_frame(t, nid, 2), bx, lerp(by + 50, by, u), POOL_Y + 4, True)
    if 74 <= t < 78 or 84 <= t < 88:
        return ("hurt", 0 if t in (74, 75, 84, 85) else 1, bx + (3 if t in (74, 84) else 2), by + bob, None, True)
    if 100 <= t < 108:                                 # wind-up: drift back
        u = ease(seg(t, 100, 108))
        return ("windup", 0 if t < 104 else 1, bx + 10 * u, by - 4 * u, None, True)
    if 108 <= t < 118:                                 # lunge
        u = ease(seg(t, 108, 114), "i")
        k = 0 if t < 111 else 1 if t < 116 else 2
        return ("lunge", k, lerp(bx + 10, 124, u), lerp(by - 4, 116, u), None, True)
    if 118 <= t < 132:                                 # swim back
        u = ease(seg(t, 118, 132))
        return ("idle", loop_frame(t, nid, 2), lerp(124, bx, u), lerp(116, by, u), None, True)
    if 132 <= t < 206:
        return ("charge", loop_frame(t, BOSS.count("charge"), 2), bx, by + bob, None, True)
    if 206 <= t < 210:
        return ("hurt", 0 if t < 208 else 1, bx + 2, by + bob, None, True)
    if 210 <= t < 224:
        return ("charge", loop_frame(t, BOSS.count("charge"), 2), bx, by + bob, None, True)
    if 224 <= t < 250:
        return ("stunned", loop_frame(t, BOSS.count("stunned"), 3), bx + (4 if t < 228 else 3), by + 6, None, True)
    if 250 <= t < 262:
        return ("stunned", loop_frame(t, BOSS.count("stunned"), 3), bx + 3, by + 6, None, True)
    if t >= 262:
        return ("stunned", 0, bx + 3, by + 6, None, False)
    return idle


# damage pops: (tick, x, y, text, big font colours)
DAMAGE = [(75, BOSS_HOME[0], BOSS_HOME[1] - 24, "14", False), (85, BOSS_HOME[0] + 14, BOSS_HOME[1] - 34, "21", True),
          (116, HERO_HOME[0], HERO_HOME[1] - 58, "8", False), (207, BOSS_HOME[0], BOSS_HOME[1] - 24, "12", False),
          (225, BOSS_HOME[0] + 4, BOSS_HOME[1] - 34, "73", True)]
PROMPTS = [(84, "PERFECT!", ("fire5", "fire4", "fire3"), "fire2"), (115, "BLOCK!", ("silver3", "silver2"), "silver1"),
           (227, "BREAK!", ("glow2", "glow1"), "glow0")]


def boss_hp(t):
    steps = [(0, 120), (75, 106), (85, 85), (207, 73), (225, 0)]
    return [v for (k, v) in steps if t >= k][-1]


def hero_hp(t):
    return 142 if t >= 116 else 150


def hero_mp(t):
    return 18 if t >= 192 else 30


def ghost(fn, t, lag=10):
    """The lost-HP ghost: the value lag ticks ago, draining over the last 6 of them."""
    a, b = fn(max(0, t - lag)), fn(t)
    if a == b:
        return None
    u = max(0.0, min(1.0, (t - lag - max(k for k in range(t + 1) if fn(k) != fn(max(0, k - 1)) or k == 0) + 6) / 6))
    return a


# ---------------------------------------------------------------- the frame

TS, LAYERS = TM.build()
_ground_cache = {}


def world_tiles(f):
    if f not in _ground_cache:
        _ground_cache[f] = (TM.render(TS, LAYERS, f, ("ground", "deco")), TM.render(TS, LAYERS, f, ("front",)))
    return _ground_cache[f]


def water_mask():
    g = TM.render(TS, LAYERS, 0, ("ground",))
    idx = LI.index(g)
    names = [k for k, r in RAMPS.items() for _ in r]
    wr = np.array([n == "water" for n in names])
    return (idx >= 0) & wr[np.clip(idx, 0, None)]


WATER = water_mask()


def shadow(img, x, y, rx, ry):
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    m = ((xx - x) / rx) ** 2 + ((yy - y) / ry) ** 2 <= 1
    return LI.apply(img, np.where(m, -1.0, 0.0))


def render(t):
    t %= N
    ftile = (t // 2) % 4
    g, front = world_tiles(ftile)
    img = g.copy()
    # ---- fighters' states
    ha, hf, hx_, hy, lift = hero_state(t)
    ba, bf, bx, by, clip, bvis = boss_state(t)
    # shadows on the ground
    img = shadow(img, int(hx_), int(hy), 11 - min(6, lift / 8), 3)
    if bvis and clip is None:
        img = shadow(img, int(bx), POOL_Y + 14, 16, 3)
    # boss reflection: flipped about the waterline, drawn only on water, darker, rows wobbling
    bs = BOSS.get(ba, bf)
    if bvis:
        ref = ramp_step(bs[::-1], -2)
        top = int(2 * POOL_Y + 12 - by - 40)
        layer = canvas(VW, 192)
        blit(layer, ref, int(bx) - 40, top)
        for yy in range(192):
            sh = int(round(math.sin(yy * 0.9 + t * 0.7)))
            if sh:
                layer[yy] = np.roll(layer[yy], sh, 0)
        m = (layer[..., 3] > 0) & WATER & ((np.arange(192)[:, None] + t) % 3 != 0)
        img[m] = layer[m]
    # the fighters, y-sorted by their ground line
    hs = HERO.get(ha, hf)
    before = img.copy()
    items = [(hy, "hero"), (by + 26 if clip is None else 0, "boss")]
    for _, who in sorted(items):
        if who == "hero":
            blit(img, hs, int(hx_) - HERO.anchor[0], int(hy - lift) - HERO.anchor[1])
        elif bvis:
            spr = bs
            if 250 <= t < 262 and t % 2:
                spr = ramp_step(bs, 2)
            if clip is not None:
                spr = spr.copy()
                cut = clip - (int(by) - 40)
                if 0 <= cut < 80:
                    spr[cut:] = 0
            blit(img, spr, int(bx) - 40, int(by) - 40)
    fighters = (img != before).any(-1)
    # ---- effects (world space)
    fxs = world_fx(t, hx_, hy, lift, bx, by)
    for (spr, x, y) in fxs:
        blit(img, spr, int(x), int(y))
    for (x, y, col) in fx.fireflies(t):
        if 0 <= x < VW and 0 <= y < 192 and not WATER[y, x]:
            img[y, x] = C[col]
    for (x, y, col) in dissolve(t, bx, by):
        if 0 <= x < VW and 0 <= y < 192:
            img[y, x] = C[col]
    blit(img, front, 0, 0)
    img = img[:VH]
    # ---- lighting
    Lm = lightmap(t, bx, by, bvis)
    fm = fighters[:VH]
    Lm[fm] = np.maximum(Lm[fm], -0.4)          # fighters stay readable in the dark
    img = LI.apply(img, Lm)
    # ---- camera shake (world only)
    sx, sy = shake(t)
    if sx or sy:
        img = np.roll(np.roll(img, sx, 1), sy, 0)
    if flash(t):
        img = ramp_step(img, flash(t))
    # ---- UI
    draw_ui(img, t, bx, by, bvis)
    # ---- fades
    fd = fade(t)
    if fd:
        img = LI.apply(img, np.full(img.shape[:2], fd), emissive=False)
        if fd <= -5:
            img[..., :3] = C["ink"][:3]
    return img


def shake(t):
    if 84 <= t < 87:
        return [(2, 0), (-2, 1), (1, 0)][t - 84]
    if 225 <= t < 231:
        return [(3, 1), (-3, -1), (2, 1), (-2, 0), (1, 0), (-1, 0)][t - 225]
    if 116 <= t < 118:
        return [(-1, 0), (1, 0)][t - 116]
    return (0, 0)


def flash(t):
    return 2 if t in (224, 225) else 1 if t in (84, 226) else 0


def fade(t):
    if t < 8:
        return -5 + 5 * t / 8
    if t >= 322:
        return -5 * min(1, (t - 322) / 12)
    return 0


def lightmap(t, bx, by, bvis):
    f = (t // 2) % 4
    fl = [0, 1, -1, 1][f]
    amb = -1.8
    if 132 <= t < 224:                                 # the charge swallows the light
        amb = -1.5 - 1.0 * ease(seg(t, 132, 146))
    if 224 <= t < 240:
        amb = lerp(-2.5, -1.5, ease(seg(t, 224, 240)))
    lights = [(88, 60, 46 + fl, 2.1), (232, 60, 46 - fl, 2.1), (168, 42, 20, 1.2)]
    for (x, y) in ((10, 6), (18, 8), (2, 4), (12, 4), (16, 10), (3, 9)):
        lights.append((x * 16 + 8, y * 16 + 11, 18, 1.4))
    if bvis:
        lx, ly = lure_pos(t)
        s = 1.6
        r = 34
        if 132 <= t < 224:
            s, r = 3.4, 34 + 16 * ease(seg(t, 132, 150)) + 3 * math.sin(t * 0.8)
        lights.append((lx, ly, r, s))
    if 222 <= t < 232:                                 # the sunburst lights everything near it
        lights.append((bx, by, 120 * (1 - seg(t, 222, 232)) + 20, 3.0))
    return LI.lightmap(VH, VW, amb, lights)


def world_fx(t, hx_, hy, lift, bx, by):
    out = []

    def place(sp, x, y):
        img, (ox, oy) = sp
        out.append((img, x - ox, y - oy))

    # bubbles and the rising plume
    for k, t0 in enumerate((2, 6, 9, 12, 14, 16, 17, 18, 19)):
        age = t - t0
        if 0 <= age < 10:
            place(fx.bubble(age, k), 180 + (k * 17) % 60, POOL_Y + 10 - age * 1.2)
    if 18 <= t < 26:
        place(fx.plume(t - 18, 30, 56), BOSS_HOME[0], POOL_Y + 10)
    if 22 <= t < 30:
        place(fx.splash(t - 22, 1, 48), BOSS_HOME[0], POOL_Y + 8)
    for k, t0 in enumerate((10, 16, 22, 28)):
        if 0 <= t - t0 < 6:
            place(fx.ring(t - t0, rx=30, ry=8), BOSS_HOME[0], POOL_Y + 8)
    # slashes and sparks
    for (t0, x, y, a0, a1) in ((72, HERO_ATK[0] + 18, HERO_ATK[1] - 26, -60, 80), (81, HERO_ATK[0] + 16, HERO_ATK[1] - 30, 190, 330),
                               (204, HERO_ATK[0] + 18, HERO_ATK[1] - 26, -60, 80)):
        if 0 <= t - t0 < 3:
            place(fx.slash(t - t0, a0, a1, r=18), x, y)
    for (t0, x, y, big) in ((74, BOSS_HOME[0] - 22, BOSS_HOME[1] - 4, False), (84, BOSS_HOME[0] - 20, BOSS_HOME[1] - 12, True),
                            (116, HERO_HOME[0] + 18, HERO_HOME[1] - 30, False), (206, BOSS_HOME[0] - 22, BOSS_HOME[1] - 4, False)):
        if 0 <= t - t0 < 4:
            place(fx.spark(t - t0, big, ("silver3", "silver2", "silver1") if t0 == 116 else ("fire6", "fire5", "fire4")), x, y)
    if 222 <= t < 232:
        place(fx.sunburst(t - 222), bx, by)
    if 224 <= t < 230:
        place(fx.ring(t - 224, rx=40, ry=10, col=("fire5", "fire4", "fire3")), bx, POOL_Y + 12)
    # the charge: motes spiralling into the lure
    if 136 <= t < 222:
        place(fx.charge(t % 8), *lure_pos(t))
    # stunned stars
    if 228 <= t < 262:
        place(fx.stun_stars(t), bx, by - 30)
    # the lure falling into the pool as the boss dissolves
    if 280 <= t < 290:
        place(fx.splash(t - 280, 3, 24), bx - 20, POOL_Y + 10)
        place(fx.ring(min(5, t - 280), rx=20, ry=6), bx - 20, POOL_Y + 10)
    return out


_boss_pixels = None


def dissolve(t, bx, by):
    global _boss_pixels
    if not (262 <= t < 300):
        return []
    if _boss_pixels is None:
        s = BOSS.get("stunned", 0)
        names = {tuple(v[:3]): k for k, v in C.items()}
        ys, xs = np.nonzero(s[..., 3] > 0)
        _boss_pixels = [(int(x) - 40, int(y) - 40, names.get(tuple(s[y, x, :3]), "violet3")) for y, x in zip(ys, xs)]
    pix = [(int(bx) + x, int(by) + y, c) for (x, y, c) in _boss_pixels]
    return fx.motes(pix, t - 262)


# ---------------------------------------------------------------- UI

def slide(t, t0, dist, dur=5):
    return int(round(dist * (1 - ease(seg(t, t0, t0 + dur), "o")))) if t < t0 + dur else 0


def draw_ui(img, t, bx, by, bvis):
    if t < 8 or t >= 322:
        return
    # the hero's plate slides up; the boss's plate drops in when it appears
    active = 46 <= t < 100 or 172 <= t < 250
    hp_g = hero_hp(t - 8) if hero_hp(t - 8) != hero_hp(t) else None
    mp_g = hero_mp(t - 8) if hero_mp(t - 8) != hero_mp(t) else None
    blit(img, U.hero_plate(portrait(), "KESTREL", hero_hp(t), 150, hero_mp(t), 30, hp_g, mp_g,
                           active and (t // 4) % 2 == 0), 4, 142 + slide(t, 30, 40))
    if 28 <= t < 262:
        g = boss_hp(t - 8) if boss_hp(t - 8) != boss_hp(t) else None
        blit(img, U.name_plate("GLOOMLURE", boss_hp(t) / 120, None if g is None else g / 120), 230, 4 - slide(t, 28, 24))
    # banners
    for (t0, t1, msg) in ((22, 44, "A GLOOMLURE RISES FROM THE DEEP!"), (100, 112, "ABYSSAL BITE"),
                          (134, 168, "THE GLOOMLURE IS GATHERING LIGHT..."), (186, 196, "DAWN CLEAVE"),
                          (252, 272, "THE GLOOMLURE WAS VANQUISHED!")):
        if t0 <= t < t1:
            b = U.banner(msg)
            blit(img, b, (VW - b.shape[1]) // 2, 22 - slide(t, t0, 12, 3))
    # the menus
    if 46 <= t < 62:
        sel = 0 if t < 52 else 1 if t < 58 else 0
        m = U.menu(sel=sel)
        if t in (60, 61):
            m = ramp_step(m, 1)
        blit(img, m, 100, 44)
        blit(img, U.cursor(t // 3), 93, 44 + 4 + sel * 11)
    if 172 <= t < 194:
        sel = 0 if t < 178 else 1
        blit(img, U.menu(sel=sel), 100, 44)
        if t < 182:
            blit(img, U.cursor(t // 3), 93, 48 + sel * 11)
        else:
            sm = U.menu([("sun", "DAWN CLEAVE 12"), ("moon", "MOONSTEP 6")], sel=0, w=90, title="SKILL")
            if t in (192, 193):
                sm = ramp_step(sm, 1)
            blit(img, sm, 118, 60)
            blit(img, U.cursor(t // 3), 111, 60 + 12)
    # locks over the charging boss: sword, sun, sun
    if 134 <= t < 232:
        kinds = ("sword", "sun", "sun")
        broken = (208, 226, 228)
        x0 = int(bx) - 22
        y0 = int(by) - 52
        for i, k in enumerate(kinds):
            if t < 134 + 3 * i:
                continue
            st, age = "whole", 0
            if t >= broken[i] - 2 and t < broken[i]:
                st = "crack"
            elif t >= broken[i]:
                st, age = "gone", t - broken[i]
                if age > 4:
                    continue
            pop = -2 if t - (134 + 3 * i) < 2 else 0
            blit(img, U.lock_plate(k, st, age), x0 + i * 15, y0 + pop)
        if t < 226:
            blit(img, text("1", fill="gold3"), x0 + 46, y0 + 3)
    # damage numbers: pop up, hang, fall and blink out
    for (t0, x, y, s, big) in DAMAGE:
        age = t - t0
        if 0 <= age < 18:
            dy = [0, -4, -7, -8, -8, -7, -6, -6, -6, -6, -6, -6, -6, -6, -5, -4, -3, -2][age]
            if age >= 14 and age % 2:
                continue
            fill = ["fire5", "fire4", "fire3"] if big else ["cream2", "cream1"]
            im = text(s, BIG, fill=fill, shade="fire2" if big else "cream0")
            blit(img, im, int(x) - im.shape[1] // 2, int(y) + dy)
    for (t0, s, fill, shade) in PROMPTS:
        age = t - t0
        if 0 <= age < 14:
            im = text(s, BIG, fill=list(fill), shade=shade, shadow=True)
            dy = [6, 2, -1, 0][age] if age < 4 else 0
            if age >= 11 and age % 2:
                continue
            x = (VW - im.shape[1]) // 2 if s == "BREAK!" else (int(bx) - 60 if s == "PERFECT!" else HERO_HOME[0] - im.shape[1] // 2)
            y = 60 if s == "BREAK!" else (int(by) - 58 if s == "PERFECT!" else HERO_HOME[1] - 76)
            blit(img, im, x, y + dy)
    # victory
    if 290 <= t < 322:
        v = text("VICTORY", BIG, fill=["gold3", "gold2"], shade="gold1", shadow=True)
        dy = [-20, -10, -4, 0, 1, 0][t - 290] if t - 290 < 6 else 0
        blit(img, v, (VW - v.shape[1]) // 2, 50 + dy)
    if 298 <= t < 322:
        p = U.panel(120, 22)
        blit(p, text("EXP +120   GOLD +45", fill="cream2"), 8, 4)
        blit(p, text("MOONPEARL X1", fill="glow1"), 8, 12)
        blit(img, p, (VW - 120) // 2, 64 + slide(t, 298, 8, 4))


_portrait = None


def portrait():
    global _portrait
    if _portrait is None:
        p = DESIGNS / "kestrel_portrait.png"   # a 22 x 22 crop of her head, hand-tidied for the HP plate
        _portrait = np.asarray(Image.open(p).convert("RGBA")).copy() if p.exists() else None
    return _portrait


def make_gif(path, frames_ms=80, scale=1, t0=0, t1=N):
    ims = []
    for t in range(t0, t1):
        a = render(t)
        im = Image.fromarray(a[..., :3])
        if scale != 1:
            im = im.resize((VW * scale, VH * scale), Image.NEAREST)
        ims.append(im)
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=frames_ms, loop=0, optimize=False)
    return path


if __name__ == "__main__":
    import sys
    ticks = [int(a) for a in sys.argv[1:]] or [40, 60, 84, 116, 150, 190, 226, 300]
    sheet = canvas(VW * 2, VH * ((len(ticks) + 1) // 2))
    for i, t in enumerate(ticks):
        blit(sheet, render(t), (i % 2) * VW, (i // 2) * VH)
    Image.fromarray(sheet).resize((sheet.shape[1] * 2, sheet.shape[0] * 2), Image.NEAREST).save(OUT / "scene_keys.png")
