"""The Gloomlure: layers from the Krea design's own pixels, then every animation frame drawn from a pose.

Layers (bottom first): tail (the fin on the right), fin_low, dorsal (the spiky crest), body (head, upper lip and
teeth), mouth (the dark inside and tongue - only what the design shows, plus hand-filled depth), jaw (the lavender
lower jaw/belly with its teeth), eye, stalk (redrawn per frame as a curve), bulb (the lure, the design's pixels).

Canvas 80 x 80: the design's 64 x 64 at offset (8, 8); body centre ~ (40, 40)."""
import json
import math
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
from agentdraw.core import poly_mask, rect_mask, ellipse_mask, assign, shade_fill, settle, composite, diff, \
    reassign_islands, layer_sheet, rotsprite
from px import C, OUT, RAMPS, hx, DESIGNS

W = H = 80
O = 8
ORDER = ["tail", "fin_low", "dorsal", "body", "mouth", "jaw", "eye", "stalk", "bulb"]
PAS_ORDER = ORDER + ["line"]
SPR = OUT / "sprites" / "gloomlure"
HINGE = (33 + O, 35 + O)            # the jaw's hinge at the back of the mouth
BULB = (6.5 + O, 19 + O)            # the lure's centre in the design
ANCHOR = (24 + O, 13 + O)           # where the stalk leaves the forehead


def cm(img, *names):
    m = np.zeros(img.shape[:2], bool)
    for n in names:
        m |= (img[..., :3] == C[n][:3]).all(-1) & (img[..., 3] > 0)
    return m


def ownership(ref):
    sky = cm(ref, "sky0", "sky1", "sky2", "sky3", "sky4")
    warm = cm(ref, "fire0", "fire1", "fire2", "fire5", "fire6", "gold1", "gold2", "gold3", "cream0", "cream1", "cream2")
    bulb = rect_mask(2, 14, 11, 24) & (warm | cm(ref, "ink"))
    stalk = poly_mask([(4, 2), (27, 2), (27, 13), (21, 14), (20, 7), (12, 7), (9, 14), (4, 14)])
    eye = ellipse_mask(29.5, 26.5, 4.6, 4.2)
    mouth = poly_mask([(12, 32), (20, 33), (28, 30), (33, 31), (33, 36), (30, 41), (20, 40), (13, 37)]) & \
        (cm(ref, "ink", "fire0", "fire1", "fire2", "fire5", "fire6", "cream0", "cream1", "cream2", "night3", "sky1"))
    # the upper teeth stay with the head: the top row of cream inside the mouth
    upper_teeth = rect_mask(12, 30, 33, 34) & cm(ref, "cream0", "cream1", "cream2")
    jaw = poly_mask([(11, 36), (22, 35), (31, 33), (35, 34), (40, 40), (45, 44), (46, 51), (36, 53), (22, 53), (14, 47), (11, 41)])
    jaw &= ~poly_mask([(13, 34), (30, 34), (30, 38), (13, 38)]) | cm(ref, "violet4", "violet5", "sky1", "cream0", "cream1", "cream2")
    tail = rect_mask(48, 24, 63, 46) & (sky | cm(ref, "ink", "violet0", "violet1", "violet2", "night0", "night1"))
    tail &= ~poly_mask([(44, 24), (50, 24), (50, 46), (44, 46)])
    fin_low = rect_mask(38, 52, 56, 62)
    dorsal = sky & poly_mask([(30, 4), (52, 4), (52, 36), (30, 20)])
    parts = [("bulb", bulb), ("eye", eye), ("upper_teeth", upper_teeth), ("mouth", mouth), ("jaw", jaw),
             ("stalk", stalk), ("fin_low", fin_low), ("tail", tail), ("dorsal", dorsal),
             ("body", np.ones(ref.shape[:2], bool))]
    L, rest = assign(ref, parts)
    ut = L.pop("upper_teeth"); m = ut[..., 3] > 0; L["body"][m] = ut[m]
    return L


def rmp(name, lo=0, hi=None):
    return [hx(h) for h in RAMPS[name][lo:hi]]


def hidden(L):
    ink = hx(RAMPS["ink"][0])
    # the head continues behind the jaw, eye, stalk root and fins
    shade_fill(L["body"], ellipse_mask(33, 32, 17, 17), [hx(RAMPS["violet"][0]), hx(RAMPS["violet"][1]),
                                                         hx(RAMPS["night"][1]), hx(RAMPS["violet"][1])], ink)
    # the mouth's depth: dark, with the tongue continuing, so an opened jaw shows a throat, not a hole
    m = poly_mask([(12, 33), (32, 31), (36, 36), (33, 44), (20, 44), (12, 39)])
    L["mouth"][m & (L["mouth"][..., 3] == 0)] = ink
    tongue = ellipse_mask(26, 41, 6, 3)
    L["mouth"][tongue & m] = C["fire0"]
    L["mouth"][ellipse_mask(25, 40.5, 3.5, 1.5) & m] = C["fire1"]
    # the eye socket under the eye (for blinks/squints), the dorsal's root under the body
    shade_fill(L["dorsal"], poly_mask([(34, 12), (47, 16), (48, 30), (36, 22)]), rmp("sky", 0, 3), ink)
    shade_fill(L["tail"], poly_mask([(45, 28), (52, 26), (52, 44), (45, 42)]), rmp("sky", 0, 3), ink)
    return L


def build_layers():
    g = np.asarray(Image.open(DESIGNS / "gloomlure_design.png").convert("RGBA")).copy()
    L = ownership(g)
    for n in list(L):
        reassign_islands(L, n, max_px=6)
    print("partition diff", diff(composite(L, ORDER), g))
    part = {k: v.copy() for k, v in L.items()}
    L = hidden(L)
    print("dropped", settle(L, ORDER, part))
    print("stack diff", diff(composite(L, ORDER), g))
    layer_sheet(L, ORDER, OUT / "gloomlure_layers.png", g, s=6, cols=5,
                title=f"Gloomlure - {len(ORDER)} layers; stack == design: {diff(composite(L, ORDER), g) == 0}")
    np.savez_compressed(OUT / "gloomlure_layers.npz", **L)
    return L


# ---------------------------------------------------------------- animation

def pad(a):
    return np.pad(a, ((O, H - 64 - O), (O, W - 64 - O), (0, 0)))


def over(dst, src):
    m = src[..., 3] > 0
    dst[m] = src[m]
    return dst


def shift(img, dx, dy):
    dx, dy = int(round(dx)), int(round(dy))
    out = np.zeros_like(img)
    ys, xs = np.nonzero(img[..., 3] > 0)
    ny, nx = ys + dy, xs + dx
    ok = (ny >= 0) & (ny < img.shape[0]) & (nx >= 0) & (nx < img.shape[1])
    out[ny[ok], nx[ok]] = img[ys[ok], xs[ok]]
    return out


def turn(img, deg, pivot):
    return img.copy() if abs(deg) < 0.5 else rotsprite(img, deg, pivot)


def rot(p, deg, pivot):
    a = math.radians(deg)
    x, y = p[0] - pivot[0], p[1] - pivot[1]
    return (pivot[0] + x * math.cos(a) - y * math.sin(a), pivot[1] + x * math.sin(a) + y * math.cos(a))


def wave_cols(img, amp, phase, x0, grow=1):
    """Shift each column vertically by a travelling wave; the shift grows with distance from x0 (grow=+1 to the
    right, -1 to the left). Fins ripple this way without redrawing their shading."""
    out = np.zeros_like(img)
    for x in range(img.shape[1]):
        col = img[:, x]
        if not col[..., 3].any():
            continue
        d = max(0, (x - x0) * grow)
        s = int(round(amp * math.sin(phase - d * 0.45) * min(1, d / 8)))
        c = np.roll(col, s, 0)
        m = c[..., 3] > 0
        out[m, x] = c[m]
    return out


def wave_rows(img, amp, phase, y0, grow=1):
    out = np.zeros_like(img)
    for y in range(img.shape[0]):
        row = img[y]
        if not row[..., 3].any():
            continue
        d = max(0, (y - y0) * grow)
        s = int(round(amp * math.sin(phase - d * 0.5) * min(1, d / 6)))
        r = np.roll(row, s, 0)
        m = r[..., 3] > 0
        out[y][m] = r[m]
    return out


def stalk(anchor, bulb_top, bend, droop=0.0):
    """The lure's stalk: a cubic curve from the forehead up and over to the bulb, 3 px thick (violet0 core with a
    violet2 lit upper edge); bend lifts the arc, droop lets it sag."""
    img = np.zeros((H, W, 4), np.uint8)
    ax, ay = anchor; bx, by = bulb_top
    c1 = (ax - 2, ay - 12 * bend + 6 * droop)
    c2 = (bx + 2, by - 13 * bend + 8 * droop)
    pts = []
    for i in range(80):
        t = i / 79
        x = (1 - t) ** 3 * ax + 3 * (1 - t) ** 2 * t * c1[0] + 3 * (1 - t) * t * t * c2[0] + t ** 3 * bx
        y = (1 - t) ** 3 * ay + 3 * (1 - t) ** 2 * t * c1[1] + 3 * (1 - t) * t * t * c2[1] + t ** 3 * by
        pts.append((x, y))
    yy, xx = np.mgrid[0:H, 0:W]
    m = np.zeros((H, W), bool)
    for (x, y) in pts:
        m |= (xx + 0.5 - x) ** 2 + (yy + 0.5 - y) ** 2 <= 1.25 ** 2
    img[m] = C["violet0"]
    top = m & ~np.roll(m, 1, 0)                                  # the upper edge catches the lure's light
    img[top] = C["violet2"]
    return img


EYES = {
    # hand-drawn eye states over the socket (11 x 9), '.' leaves the socket's own pixels
    "squint": ["...........",
               "..lllllll..",
               ".lwwwwwwwl.",
               "llllllllll.",
               ".lfffffl...",
               "..lllll....",
               "...........",
               "...........",
               "..........."],
    "swirl": ["...lllll...",
              "..lcccccl..",
              ".lcclllccl.",
              ".lclcccl.cl",
              ".lclclccl.l",
              ".lcclll.cl.",
              "..lcccccl..",
              "...lllll...",
              "..........."],
    "blaze": ["...fffff...",
              "..fgggggf..",
              ".fgghhhggf.",
              ".fghhhhhgf.",
              ".fghhlhhgf.",
              ".fgghhhggf.",
              "..fgggggf..",
              "...fffff...",
              "..........."],
}
EK = {"l": "ink", "w": "violet2", "c": "cream2", "f": "fire2", "g": "fire5", "h": "fire6"}


def eye_layer(L0, state):
    if state == "open":
        return L0["eye"].copy()
    img = np.zeros((H, W, 4), np.uint8)
    # the socket: fill the eye area with the head's dark violet, then draw the state on top
    m = ellipse_mask(29.5 + O, 26.5 + O, 4.6, 4.2, shape=(H, W))
    img[m] = C["violet0"]
    rows = EYES[state]
    for dy, r in enumerate(rows):
        for dx, ch in enumerate(r):
            if ch != ".":
                img[22 + O + dy, 24 + O + dx] = C[EK[ch]]
    return img


def bulb_layer(L0, pos, bright=0):
    """The lure's design pixels at pos (its centre); bright > 0 steps it up its ramps and adds a halo ring."""
    b = shift(L0["bulb"], pos[0] - BULB[0], pos[1] - BULB[1])
    if bright:
        from px import ramp_step
        b = ramp_step(b, bright)
        yy, xx = np.mgrid[0:H, 0:W]
        d = np.sqrt((xx + 0.5 - pos[0]) ** 2 + (yy + 0.5 - pos[1]) ** 2)
        halo = (d > 5.2) & (d <= 5.2 + bright) & (b[..., 3] == 0) & ((xx + yy) % 2 == 0)
        b[halo] = C["fire4"]
    return b


REST = dict(tilt=0.0, jaw=0.0, eye="open", bulb=(0, 0), bend=1.0, droop=0.0, bright=0, fin=(1.0, 0.0),
            dy=0, flash=0, dorsal_up=0)


def P(**kw):
    p = dict(REST); p.update(kw); return p


def frame(L0, p, named=False):
    """tilt: the whole fish turns about its centre (+ = clockwise, head up for a left-facing fish);
    jaw: degrees the jaw opens (+) or clamps (-) about the hinge."""
    c = (40, 40)
    L = {}
    fa, fph = p["fin"]
    L["tail"] = wave_rows(L0["tail"], fa * 1.5, fph, 30 + O, 1)
    L["fin_low"] = wave_cols(L0["fin_low"], fa, fph + 1, 40 + O, 1)
    dors = wave_cols(L0["dorsal"], fa * 0.8, fph + 2, 32 + O, 1)
    L["dorsal"] = shift(dors, 0, -p["dorsal_up"])
    L["body"] = L0["body"].copy()
    L["mouth"] = L0["mouth"].copy()
    # the jaw opens counter-clockwise about the hinge (its front drops) - rotsprite's negative angle
    L["jaw"] = turn(L0["jaw"], -p["jaw"], HINGE)
    L["eye"] = eye_layer(L0, p["eye"])
    bpos = (BULB[0] + p["bulb"][0], BULB[1] + p["bulb"][1])
    L["stalk"] = stalk(ANCHOR, (bpos[0] + 0.5, bpos[1] - 4.5), p["bend"], p["droop"])
    L["bulb"] = bulb_layer(L0, bpos, p["bright"])
    tilt = p["tilt"]
    for k in L:
        L[k] = shift(turn(L[k], tilt, c), 0, p["dy"])
    bulb_scene = rot(bpos, tilt, c)
    img = np.zeros((H, W, 4), np.uint8)
    for n in ORDER:
        over(img, L[n])
    a = img[..., 3] > 0
    ring = ndimage.binary_dilation(a, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])) & ~a
    line = np.zeros_like(img); line[ring] = C["ink"]
    img[ring] = C["ink"]
    L["line"] = line
    if p["flash"]:
        from px import ramp_step
        img = ramp_step(img, p["flash"])
        L = {k: ramp_step(v, p["flash"]) for k, v in L.items()}
    lure = (bulb_scene[0], bulb_scene[1] + p["dy"])
    return (img, L, lure) if named else (img, lure)


def anims():
    A = {}
    A["idle"] = [P(jaw=[0, 2, 4, 4, 2, 0][i], bulb=(round(1.5 * math.sin(i * math.pi / 3)), round(math.cos(i * math.pi / 3))),
                   fin=(1.0, i * math.pi / 3), bend=1.0 + 0.05 * math.sin(i * math.pi / 3)) for i in range(6)]
    A["windup"] = [P(tilt=5, jaw=-3, bulb=(3, -1), bend=1.1, fin=(1.4, 0.5), dorsal_up=1),
                   P(tilt=9, jaw=-4, bulb=(5, -2), bend=1.15, fin=(1.6, 1.5), dorsal_up=1)]
    A["lunge"] = [P(tilt=-8, jaw=18, bulb=(6, 2), bend=0.9, fin=(1.8, 2.5), eye="blaze"),
                  P(tilt=-10, jaw=24, bulb=(7, 3), bend=0.85, fin=(1.8, 3.5), eye="blaze"),
                  P(tilt=-6, jaw=-4, bulb=(4, 1), bend=0.95, fin=(1.4, 4.5))]
    A["hurt"] = [P(tilt=10, jaw=8, eye="squint", bulb=(4, 3), bend=0.9, fin=(2.0, 1.0), flash=2),
                 P(tilt=7, jaw=5, eye="squint", bulb=(3, 2), bend=0.95, fin=(1.6, 2.0))]
    A["charge"] = [P(tilt=-3, jaw=-3, eye="blaze", bulb=(-2, -3 - (i % 2)), bend=1.2, bright=1 + (i % 2),
                     fin=(1.3, i * math.pi / 2), dorsal_up=1 + (i % 2)) for i in range(4)]
    A["stunned"] = [P(tilt=-14, jaw=10, eye="swirl", bulb=(3, 9 + (i % 2)), bend=0.5, droop=1.0,
                      fin=(0.6, i * math.pi / 2), dy=1 + (i % 2)) for i in range(4)]
    return A


def main():
    L0 = {k: pad(v) for k, v in build_layers().items()}
    SPR.mkdir(parents=True, exist_ok=True)
    for f in SPR.glob("*_*.png"):
        if f.stem.split("_")[-1].isdigit():
            f.unlink()
    A = anims()
    lures, rows = {}, []
    for name, poses in A.items():
        imgs = []
        for i, p in enumerate(poses):
            img, lure = frame(L0, p)
            Image.fromarray(img).save(SPR / f"{name}_{i}.png")
            lures[f"{name}_{i}"] = lure
            imgs.append(img)
        rows.append(imgs)
    (SPR / "lures.json").write_text(json.dumps(lures))
    n = max(len(r) for r in rows)
    sheet = Image.new("RGBA", (n * W * 3, len(rows) * H * 3), (60, 64, 88, 255))
    for j, imgs in enumerate(rows):
        for i, img in enumerate(imgs):
            sheet.alpha_composite(Image.fromarray(img).resize((W * 3, H * 3), Image.NEAREST), (i * W * 3, j * H * 3))
    sheet.save(OUT / "gloomlure_sheet.png")
    print({k: len(v) for k, v in A.items()})


if __name__ == "__main__":
    main()
