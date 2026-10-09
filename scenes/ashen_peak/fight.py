"""Ashen Peak: the fight, composed tick by tick (80 ms). Every state is a function of the tick; the loop is exact.

Each fighter follows a list of clips: (start tick, animation, ticks per frame, x from, x to, lift peak, ...).
Riku (P1) faces right; Grimhold (P2) is his own sprites mirrored and faces left. Draw order: stage back, shadows,
the defender, the attacker, effects, the foreground branches, petals, the HUD, call-outs, the fade."""
import math
import sys
import pathlib

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "drowned_shrine"))
from px import C, canvas, blit, ramp_step
from font import text, BIG
import light as LI
import stage as ST
import hud as H
import ffx

N = 360
VW, VH = ST.VW, ST.VH
GROUND = 132                       # the stage y of the fighters' feet
ANCHOR = (64, 89)                  # the feet on the 128 x 96 sprite canvas
SPR = ST.OUT / "sprites"


class Sprites:
    def __init__(self, name, mirror=False):
        self.name, self.mirror, self.cache = name, mirror, {}

    def get(self, anim, i):
        k = (anim, i)
        if k not in self.cache:
            a = np.asarray(Image.open(SPR / self.name / f"{anim}_{i}.png").convert("RGBA")).copy()
            self.cache[k] = a[:, ::-1].copy() if self.mirror else a
        return self.cache[k]

    def count(self, anim):
        return len(list((SPR / self.name).glob(f"{anim}_*.png")))


RIKU, GRIM = Sprites("riku"), Sprites("grimhold", mirror=True)


def ease(u, k="io"):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u) if k == "io" else 1 - (1 - u) ** 2 if k == "o" else u * u if k == "i" else u


# ---------------------------------------------------------------- the choreography
# clip = (t0, anim, ticks_per_frame, x0, x1, lift, opts); a clip lasts until the next one starts.
# opts: loop (cycle the frames), frames (explicit frame list), ease

R_CLIPS = [
    (0, "stance", 2, 150, 150, 0, {"loop": True}),
    (30, "walk", 1, 150, 180, 0, {"loop": True}),
    (46, "jab", 1, 180, 180, 0, {}),
    (50, "cross", 1, 180, 182, 0, {}),
    (54, "roundhouse", 1, 182, 180, 0, {"frames": [0, 1, 2, 3, 3, 3, 4, 5]}),
    (62, "stance", 2, 180, 180, 0, {"loop": True}),
    (63, "block", 1, 180, 177, 0, {"frames": [0, 1, 1, 1, 0, 0]}),
    (69, "stance", 2, 177, 177, 0, {"loop": True}),
    (80, "knockdown", 2, 177, 138, 22, {"air": (80, 87)}),
    (92, "knockdown", 1, 138, 138, 0, {"frames": [5]}),
    (98, "getup", 2, 138, 138, 0, {}),
    (106, "stance", 2, 138, 140, 0, {"loop": True}),
    (118, "jump", 1, 140, 146, 0, {"frames": [0, 0]}),
    (120, "jump", 2, 146, 156, 34, {"frames": [1, 2, 2, 3], "air": (120, 133)}),
    (127, "flykick", 2, 156, 162, 0, {"frames": [0, 1, 2]}),
    (133, "jump", 2, 162, 150, 0, {"frames": [4]}),
    (136, "stance", 2, 150, 150, 0, {"loop": True}),
    (148, "sunpalm", 2, 150, 150, 0, {}),
    (160, "stance", 2, 150, 146, 0, {"loop": True}),
    (180, "launch", 2, 146, 128, 40, {"air": (180, 193), "frames": [0, 1, 2, 2, 2, 2, 2]}),
    (187, "knockdown", 2, 128, 118, 0, {"frames": [2, 3, 4, 5]}),
    (195, "knockdown", 1, 118, 118, 0, {"frames": [5]}),
    (202, "getup", 2, 118, 118, 0, {}),
    (210, "walk", 1, 118, 150, 0, {"loop": True}),
    (222, "sweep", 2, 150, 150, 0, {}),
    (232, "stance", 2, 150, 150, 0, {"loop": True}),
    (262, "jump", 1, 150, 146, 0, {"frames": [0, 0]}),
    (264, "jump", 2, 146, 126, 30, {"frames": [1, 2, 2, 3, 3, 3], "air": (264, 276)}),
    (276, "jump", 1, 126, 126, 0, {"frames": [4, 4]}),
    (278, "walk", 1, 126, 140, 0, {"loop": True}),
    (282, "jab", 1, 140, 141, 0, {}),
    (286, "cross", 1, 141, 142, 0, {}),
    (290, "jab", 1, 142, 143, 0, {}),
    (294, "cross", 1, 143, 144, 0, {}),
    (298, "uppercut", 1, 144, 146, 0, {"frames": [0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4]}),
    (311, "stance", 2, 146, 146, 0, {"loop": True}),
    (318, "victory", 2, 146, 146, 0, {}),
    (330, "victory", 2, 146, 146, 0, {"frames": [3, 4, 5, 4], "loop": True}),
]
G_CLIPS = [
    (0, "stance", 2, 250, 250, 0, {"loop": True}),
    (30, "walk", 2, 250, 226, 0, {"loop": True}),
    (46, "stance", 2, 226, 226, 0, {"loop": True}),
    (47, "hit", 1, 226, 228, 0, {}),
    (51, "hit", 1, 228, 230, 0, {}),
    (57, "hit", 1, 230, 236, 0, {"frames": [0, 0, 1, 1, 2]}),
    (62, "hook", 1, 236, 226, 0, {}),
    (68, "stance", 2, 226, 228, 0, {"loop": True}),
    (70, "charge", 2, 228, 228, 0, {"frames": [0]}),
    (72, "charge", 1, 228, 206, 0, {"frames": [1, 2, 3, 4, 1, 2, 3, 4], "ease": "i"}),
    (80, "charge", 1, 206, 202, 0, {"frames": [5, 5, 5, 5]}),
    (84, "stance", 2, 202, 194, 0, {"loop": True}),
    (112, "slam", 2, 194, 194, 0, {}),
    (126, "stance", 2, 194, 194, 0, {"loop": True}),
    (129, "hit", 1, 194, 204, 0, {"frames": [0, 0, 1, 1, 2]}),
    (134, "walk", 2, 204, 228, 0, {"loop": True}),
    (146, "roar", 2, 228, 228, 0, {"loop": True}),
    (156, "stance", 2, 228, 228, 0, {"loop": True}),
    (158, "hit", 1, 228, 236, 0, {"frames": [0, 0, 1, 1, 2, 2]}),
    (164, "walk", 1, 236, 194, 0, {"loop": True}),
    (176, "uppercut", 2, 194, 196, 0, {}),
    (188, "stance", 2, 196, 196, 0, {"loop": True}),
    (225, "knockdown", 2, 196, 210, 12, {"air": (225, 230)}),
    (237, "knockdown", 1, 210, 210, 0, {"frames": [5]}),
    (243, "getup", 2, 210, 210, 0, {}),
    (251, "roar", 2, 210, 210, 0, {"loop": True}),
    (262, "charge", 2, 210, 210, 0, {"frames": [0]}),
    (264, "charge", 1, 210, 184, 0, {"frames": [1, 2, 3, 4, 1, 2, 3, 4, 1, 2], "ease": "i"}),
    (274, "charge", 1, 184, 184, 0, {"frames": [5, 5, 5, 5]}),
    (278, "stance", 2, 184, 184, 0, {"loop": True}),
    (283, "hit", 1, 184, 186, 0, {}),
    (287, "hit", 1, 186, 188, 0, {}),
    (291, "hit", 1, 188, 190, 0, {}),
    (295, "hit", 1, 190, 192, 0, {}),
    (300, "launch", 2, 192, 214, 44, {"air": (300, 312), "frames": [0, 1, 2, 2, 2, 2]}),
    (312, "knockdown", 2, 214, 222, 0, {"frames": [2, 3, 4, 5]}),
    (320, "knockdown", 1, 222, 222, 0, {"frames": [5]}),
]
FREEZE = (300, 306)                # the K.O. hit-freeze: the world holds the frame of tick 300


def clip_at(clips, t):
    k = max(i for i, c in enumerate(clips) if c[0] <= t)
    c = clips[k]
    t1 = clips[k + 1][0] if k + 1 < len(clips) else N
    return c, t1


def fighter(clips, spr, t):
    (t0, anim, rate, x0, x1, lift, opts), t1 = clip_at(clips, t)
    frames = opts.get("frames") or list(range(spr.count(anim)))
    i = (t - t0) // rate
    i = i % len(frames) if opts.get("loop") else min(i, len(frames) - 1)
    u = (t - t0) / max(1, t1 - t0)
    x = x0 + (x1 - x0) * ease(u, opts.get("ease", "io"))
    y = 0.0
    if "air" in opts:
        a0, a1 = opts["air"]
        if a0 <= t < a1:
            v = (t - a0) / (a1 - a0)
            y = lift * 4 * v * (1 - v)
    return anim, frames[i], x, y


# hits: (tick, target 'R' or 'G', damage %, kind) ; kind: hit / block / fire / big
HITS = [(47, "G", 5, "hit"), (51, "G", 6, "hit"), (57, "G", 9, "big"), (64, "R", 3, "block"),
        (80, "R", 15, "big"), (129, "G", 8, "big"), (158, "G", 12, "fire"), (180, "R", 20, "big"),
        (225, "G", 12, "big"), (283, "G", 8, "fire"), (287, "G", 8, "fire"), (291, "G", 8, "fire"),
        (295, "G", 8, "fire"), (300, "G", 16, "big")]
COMBOS = [(57, 3), (300, 5)]         # (tick the counter appears, hits)


def health(who, t):
    h = 100 - sum(d for (tk, w, d, _) in HITS if w == who and tk <= t)
    return max(0, h)


def cam_at(t):
    _, _, rx, _ = fighter(R_CLIPS, RIKU, t)
    _, _, gx, _ = fighter(G_CLIPS, GRIM, t)
    return max(0.0, min(ST.SCROLL, (rx + gx) / 2 - VW / 2))


def shake(t):
    for (tk, w, d, kind) in HITS:
        if kind == "big" and 0 <= t - tk < 4:
            return [(3, 1), (-3, -1), (2, 0), (-1, 0)][t - tk]
    if 118 <= t < 122:                                     # the ground slam
        return [(0, 3), (0, -2), (0, 2), (0, -1)][t - 118]
    return (0, 0)


# ---------------------------------------------------------------- rendering

STAGE = ST.Stage()


def shadow(img, x, w=18):
    yy, xx = np.mgrid[0:VH, 0:VW]
    m = ((xx - x) / w) ** 2 + ((yy - GROUND - 1) / 2.5) ** 2 <= 1
    return LI.apply(img, np.where(m, -1.0, 0.0))


def place(img, spr, x, y, cam):
    blit(img, spr, int(round(x - cam)) - ANCHOR[0], int(round(GROUND - y)) - ANCHOR[1])


def render(t):
    t %= N
    tw = FREEZE[0] if FREEZE[0] <= t < FREEZE[1] else t          # the world time (held during the freeze)
    cam = cam_at(tw)
    img = STAGE.back(t, cam)
    ra, rf, rx, ry = fighter(R_CLIPS, RIKU, tw)
    ga, gf, gx, gy = fighter(G_CLIPS, GRIM, tw)
    img = shadow(img, rx - cam, 16 - min(8, ry / 5))
    img = shadow(img, gx - cam, 22 - min(10, gy / 5))
    rs, gs = RIKU.get(ra, rf), GRIM.get(ga, gf)
    # a struck fighter flashes white for a tick
    for (tk, w, d, kind) in HITS:
        if tk == tw and kind != "block":
            if w == "G":
                gs = ramp_step(gs, 3)
            else:
                rs = ramp_step(rs, 3)
    attacker_r = ra in ("jab", "cross", "roundhouse", "sweep", "flykick", "uppercut", "sunpalm")
    order = [("G", gs, gx, gy), ("R", rs, rx, ry)] if attacker_r else [("R", rs, rx, ry), ("G", gs, gx, gy)]
    for _, s, x, y in order:
        place(img, s, x, y, cam)
    for (sp, x, y) in effects(t, tw, cam, rx, gx, ry, gy):
        img_s, (ox, oy) = sp
        blit(img, img_s, int(round(x - ox)), int(round(y - oy)))
    STAGE.front(img, t, cam)
    for (x, y, c) in ST.petals(t, cam):
        if 0 <= x < VW and 0 <= y < VH and img[y, x, 3]:
            img[y, x] = C[c]
    sx, sy = shake(tw)
    if sx or sy:
        img = np.roll(np.roll(img, sx, 1), sy, 0)
    if FREEZE[0] <= t < FREEZE[1] and t % 2 == 0:
        img = ramp_step(img, 1)
    hud_layer(img, t, tw)
    fd = -5 + 5 * t / 8 if t < 8 else -5 * min(1, (t - 346) / 12) if t >= 346 else 0
    if fd:
        img = LI.apply(img, np.full(img.shape[:2], fd), emissive=False)
        if fd <= -5:
            img[..., :3] = C["dusk0"][:3]
    return img


def effects(t, tw, cam, rx, gx, ry, gy):
    out = []
    head_y = GROUND - 44
    for (tk, w, d, kind) in HITS:
        age = tw - tk
        if 0 <= age < 4:
            tx = (gx - 16 if w == "G" else rx + 14) - cam
            ty = GROUND - (gy if w == "G" else ry) - (30 if kind != "big" else 34)
            if kind == "block":
                out.append((ffx.block_spark(age), tx, ty))
            elif kind == "fire":
                out.append((ffx.fire_pop(age), tx, ty))
            else:
                out.append((ffx.hit_spark(age, kind == "big"), tx, ty))
    # the Sun Palm fireball: leaves Riku's hands at 152, reaches Grimhold at 158
    if 152 <= tw < 158:
        u = (tw - 152) / 6
        x = (rx + 28) + ((gx - 20) - (rx + 28)) * u
        out.append((ffx.fireball(tw), x - cam, GROUND - 36))
    # the ground slam's shockwave: from Grimhold's fists toward Riku, passing under his jump
    if 118 <= tw < 128:
        x = (gx - 30) - (tw - 118) * 6
        out.append((ffx.shockwave(tw), x - cam, GROUND + 1))
    if 118 <= tw < 124:
        out.append((ffx.dust(tw - 118, 30), gx - 30 - cam, GROUND + 1))
    # dust where a fighter lands or is thrown down
    for (tk, x_of) in ((87, lambda: rx), (133, lambda: rx), (190, lambda: rx), (230, lambda: gx), (276, lambda: rx), (312, lambda: gx)):
        if 0 <= tw - tk < 6:
            out.append((ffx.dust(tw - tk), x_of() - cam, GROUND + 1))
    # speed lines behind the charges
    for (a, b) in ((72, 80), (264, 274)):
        if a <= tw < b:
            out.append((ffx.speed_lines(tw), gx + 58 - cam, GROUND - 26))
    # the flaming uppercut of Thousand Suns
    if 299 <= tw < 302:
        out.append((ffx.flame_arc(tw - 299), rx + 20 - cam, GROUND - 40))
    # the swoosh of the roundhouse
    if 56 <= tw < 59:
        from fx import slash
        out.append((slash(tw - 56, a0=-150, a1=-20, r=16, ramp=("cream0", "cream1", "cream2", "cream2")), rx + 16 - cam, GROUND - 34))
    return out


def hud_layer(img, t, tw):
    if t < 8 or t >= 346:
        return
    lag = 8
    hr, hg = health("R", tw), health("G", tw)
    gr, gg = health("R", max(0, tw - lag)), health("G", max(0, tw - lag))
    sec = max(0, 99 - t // 12)
    H.hud(img, (hr / 100, gr / 100 if gr != hr else None), (hg / 100, gg / 100 if gg != hg else None), sec,
          wins=(1 if t >= 318 else 0, 0))
    def centre(im, y, dy=0):
        blit(img, im, (VW - im.shape[1]) // 2, y + dy)
    if 8 <= t < 24:
        drop = [-14, -6, -2, 0][t - 8] if t - 8 < 4 else 0
        centre(H.callout("ROUND 1", fill=("cream2", "cream1", "cream0")), 52, drop)
    if 24 <= t < 36:
        k = t - 24
        if k >= 9 and k % 2:
            pass
        else:
            centre(H.callout("FIGHT!"), 50, [-8, -3, 0][k] if k < 3 else 0)
    for (tk, n) in COMBOS:
        if 0 <= t - tk < 16:
            c = H.combo(n)
            x = 12 if tk < 200 else 12
            blit(img, c, x - max(0, 6 - 2 * (t - tk)) * 4, 40)
    if 302 <= t < 330:
        ko = H.callout("K.O.", fill=("crimson4", "crimson3", "crimson2", "crimson1"))
        centre(ko, 44, [-10, -4, 0][t - 302] if t - 302 < 3 else 0)
    if 326 <= t < 346:
        w = H.callout("RIKU WINS")
        centre(w, 66, [-8, -3, 0][t - 326] if t - 326 < 3 else 0)


def make(path=ST.OUT / "ashen_peak.gif"):
    frames = [render(t) for t in range(N)]
    np.save(ST.OUT / "fight_frames.npy", np.stack(frames))
    ims = [Image.fromarray(f[..., :3]) for f in frames]
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=80, loop=0)
    return path


if __name__ == "__main__":
    import time
    t0 = time.time()
    make()
    print("rendered", N, "ticks in", round(time.time() - t0), "s")
