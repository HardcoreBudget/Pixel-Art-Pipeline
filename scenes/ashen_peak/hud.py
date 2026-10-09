"""The fighting-game HUD: mirrored health bars with a lost-health ghost, name plates, round medallions, a round timer,
a combo counter, and a heavy 11 px call-out font (ROUND 1 / FIGHT! / K.O. / WINS). All hand-drawn in the palette."""
import sys
import pathlib

import numpy as np
from scipy import ndimage

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "drowned_shrine"))
from px import C, canvas, rect, put, blit, art
from font import text, BIG, SMALL

HUGE = {
    "R": ["#######.", "########", "###..###", "###..###", "########", "#######.", "###.###.", "###..###", "###..###", "###..###", "###..###"],
    "O": [".######.", "########", "###..###", "###..###", "###..###", "###..###", "###..###", "###..###", "###..###", "########", ".######."],
    "U": ["###..###", "###..###", "###..###", "###..###", "###..###", "###..###", "###..###", "###..###", "###..###", "########", ".######."],
    "N": ["###..###", "####.###", "########", "########", "###.####", "###..###", "###..###", "###..###", "###..###", "###..###", "###..###"],
    "D": ["######..", "#######.", "###.####", "###..###", "###..###", "###..###", "###..###", "###..###", "###.####", "#######.", "######.."],
    "1": ["..###...", ".####...", "#####...", "..###...", "..###...", "..###...", "..###...", "..###...", "..###...", "########", "########"],
    "F": ["########", "########", "###.....", "###.....", "######..", "######..", "###.....", "###.....", "###.....", "###.....", "###....."],
    "I": ["#####", "#####", ".###.", ".###.", ".###.", ".###.", ".###.", ".###.", ".###.", "#####", "#####"],
    "G": [".######.", "########", "###.....", "###.....", "###.####", "###.####", "###..###", "###..###", "###..###", "########", ".######."],
    "H": ["###..###", "###..###", "###..###", "###..###", "########", "########", "###..###", "###..###", "###..###", "###..###", "###..###"],
    "T": ["#########", "#########", "...###...", "...###...", "...###...", "...###...", "...###...", "...###...", "...###...", "...###...", "...###..."],
    "!": ["###", "###", "###", "###", "###", "###", "###", "###", "...", "###", "###"],
    "K": ["###..###", "###.###.", "######..", "#####...", "####....", "####....", "#####...", "######..", "###.###.", "###..###", "###..###"],
    ".": ["...", "...", "...", "...", "...", "...", "...", "...", "...", "###", "###"],
    "W": ["###...###", "###...###", "###...###", "###...###", "###.#.###", "#########", "#########", "####.####", "###...###", "###...###", "##.....##"],
    "S": [".######.", "########", "###.....", "###.....", "#######.", ".#######", ".....###", ".....###", "###..###", "########", ".######."],
    " ": ["....", "....", "....", "....", "....", "....", "....", "....", "....", "....", "...."],
}


def callout(s, fill=("gold3", "gold2", "fire4", "fire3", "crimson2"), spacing=1):
    """Heavy call-out text: a vertical gradient fill (one colour per band of rows), a highlight line on each
    stroke's top, a 1 px ink outline and a 2 px drop shadow."""
    glyphs = [HUGE[ch] for ch in s]
    h = 11
    w = sum(len(g[0]) for g in glyphs) + spacing * (len(glyphs) - 1)
    m = np.zeros((h, w), bool)
    x = 0
    for g in glyphs:
        for y, row in enumerate(g):
            for dx, ch in enumerate(row):
                if ch == "#":
                    m[y, x + dx] = True
        x += len(g[0]) + spacing
    pad = 3
    img = canvas(w + 2 * pad, h + 2 * pad)
    mm = np.zeros(img.shape[:2], bool); mm[pad:pad + h, pad:pad + w] = m
    ring = ndimage.binary_dilation(mm, np.ones((3, 3), bool)) & ~mm
    shadow = (np.roll(np.roll(ring | mm, 2, 0), 1, 1)) & ~mm & ~ring
    img[shadow] = C["dusk0"]
    img[ring] = C["ink"]
    for y in range(h):
        col = fill[min(len(fill) - 1, y * len(fill) // h)]
        img[pad + y][mm[pad + y]] = C[col]
    top = mm & ~np.roll(mm, 1, 0)
    img[top] = C["fire6"]
    return img


def health_bar(frac, ghost=None, w=100, mirror=False):
    """A long bar: ink frame with a gold trim, dark trough, green fill with a lit top row; the ghost (health just
    lost) shows in red and drains a few ticks later. mirror=True drains toward the screen edge from the centre."""
    img = canvas(w, 9)
    rect(img, 1, 0, w - 2, 9, "ink"); rect(img, 0, 1, w, 7, "ink")
    rect(img, 1, 1, w - 2, 7, "gold1"); rect(img, 2, 2, w - 4, 5, "dusk0")
    inner = w - 4
    n = int(round(inner * max(0.0, min(1.0, frac))))
    g = int(round(inner * max(0.0, min(1.0, ghost)))) if ghost is not None else n
    def span(a, b, col, y=2, h=5):
        if b > a:
            rect(img, 2 + a, y, b - a, h, col)
    if g > n:
        span(n, g, "crimson2"); span(n, g, "crimson3", 2, 1)
    col, hi, lo = ("moss3", "moss5", "moss2") if frac > 0.3 else ("fire3", "fire5", "fire2")
    span(0, n, col); span(0, n, hi, 2, 1); span(0, n, lo, 6, 1)
    for x in range(12, inner, 12):                          # tick marks
        if x < n:
            put(img, 2 + x, 3, lo)
    return img[:, ::-1].copy() if mirror else img


def medallion(won):
    rows = [".ooo.", "oYGYo", "oGgGo", "oYGYo", ".ooo."] if won else [".ooo.", "odddo", "oddd o".replace(" ", ""), "odddo", ".ooo."]
    return art(rows, {"o": "ink", "Y": "gold3", "G": "gold2", "g": "gold1", "d": "dusk1"})


def timer(sec):
    t = text(f"{sec:02d}", BIG, fill=["cream2", "cream1"], shade="cream0")
    img = canvas(26, 17)
    rect(img, 1, 0, 24, 17, "ink"); rect(img, 0, 1, 26, 15, "ink")
    rect(img, 1, 1, 24, 15, "gold1"); rect(img, 2, 2, 22, 13, "dusk0")
    blit(img, t, (26 - t.shape[1]) // 2, 3)
    return img


def hud(img, p1, p2, sec, wins=(0, 0), names=("RIKU", "GRIMHOLD")):
    """p1/p2 = (health 0..1, ghost 0..1 or None)."""
    VW = img.shape[1]
    blit(img, health_bar(*p1, w=106), 6, 6)
    blit(img, health_bar(*p2, w=106, mirror=True), VW - 112, 6)
    blit(img, timer(sec), (VW - 26) // 2, 3)
    n1 = text(names[0], fill="cream2"); n2 = text(names[1], fill="cream2")
    blit(img, n1, 7, 16)
    blit(img, n2, VW - 7 - n2.shape[1], 16)
    for k in range(2):
        blit(img, medallion(k < wins[0]), 7 + n1.shape[1] + 3 + k * 7, 16)
        blit(img, medallion(k < wins[1]), VW - 7 - n2.shape[1] - 9 - k * 7, 16)
    return img


def combo(n):
    num = text(str(n), BIG, fill=["gold3", "gold2"], shade="fire3", shadow=True)
    lab = text("HITS", BIG, fill=["cream2", "cream1"], shade="cream0", shadow=True)
    img = canvas(num.shape[1] + lab.shape[1] + 2, max(num.shape[0], lab.shape[0]))
    blit(img, num, 0, 0); blit(img, lab, num.shape[1] + 2, 0)
    return img


if __name__ == "__main__":
    from PIL import Image
    from stage import Stage, OUT, VW, VH
    S = Stage()
    img = S.back(0, 72)
    S.front(img, 0, 72)
    hud(img, (0.62, 0.8), (0.35, 0.5), 57, wins=(1, 0))
    c = callout("FIGHT!")
    blit(img, c, (VW - c.shape[1]) // 2, 50)
    c2 = callout("ROUND 1", fill=("cream2", "cream1", "cream0"))
    blit(img, c2, (VW - c2.shape[1]) // 2, 30)
    c3 = callout("K.O.", fill=("crimson4", "crimson3", "crimson2", "crimson1"))
    blit(img, c3, 20, 70)
    blit(img, combo(3), 150, 76)
    Image.fromarray(img).resize((VW * 4, VH * 4), Image.NEAREST).save(OUT / "hud_check.png")
