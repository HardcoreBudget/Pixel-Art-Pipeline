"""The arena map (20 x 12 tiles of 16 px; the 320x180 view shows rows 0..11 minus the last 12 px) and the tileset
it is built from. The map has three layers: ground (opaque), deco (behind the fighters) and front (in front of
them). Water tiles are chosen from each cell's neighbours (the autotile). Every unique tile is stored once in the
tileset, 4 frames each, so the map is a grid of tile indices."""
import json

import numpy as np

import tiles as TL
from px import canvas, blit, save, OUT

W, H = 20, 12
TS = 16

# 'w' water, '#' wall face, '^' wall top, 'A' arch (2x2), '.' floor
GROUND = [
    "^^^^^^^^^^^^^^^^^^^^",
    "##################H#",
    "#########AA#########",
    "#########AA#########",
    "....................",
    "....................",
    "...........wwwwww...",
    "..........wwwwwwww..",
    "..........wwwwwwww..",
    "...........wwwwww...",
    "ww..................",
    "www.................",
]


class Tileset:
    def __init__(self):
        self.keys, self.frames = [], []          # frames[i] = [4 x 16x16 RGBA]

    def add(self, key, make):
        if key in self.keys:
            return self.keys.index(key)
        self.keys.append(key)
        self.frames.append([make(f) for f in range(TL.FR)])
        return len(self.keys) - 1

    def sheet(self, f, cols=8):
        n = len(self.keys); rows = (n + cols - 1) // cols
        img = canvas(cols * TS, rows * TS)
        for i, fr in enumerate(self.frames):
            blit(img, fr[f], (i % cols) * TS, (i // cols) * TS)
        return img


def build():
    ts = Tileset()
    ground = np.full((H, W), -1, int)
    deco = np.full((H, W), -1, int)
    front = np.full((H, W), -1, int)
    r = np.random.default_rng(42)
    iswater = lambda x, y: 0 <= x < W and 0 <= y < H and GROUND[y][x] == "w" or (y >= H and 0 <= x < W and GROUND[H - 1][x] == "w")
    # floor variants: first place 2-tile slabs (6/7 across, 8/9 down), then fill the rest at random
    floor_plan = [[-1] * W for _ in range(H)]
    free = lambda x, y: 0 <= x < W and 0 <= y < H and GROUND[y][x] == "." and floor_plan[y][x] < 0
    for y in range(H):
        for x in range(W):
            if not free(x, y):
                continue
            k = r.random()
            if k < 0.22 and free(x + 1, y):
                floor_plan[y][x], floor_plan[y][x + 1] = 6, 7
            elif k < 0.36 and free(x, y + 1):
                floor_plan[y][x], floor_plan[y + 1][x] = 8, 9
            else:
                floor_plan[y][x] = int(r.choice([0, 1, 2, 3, 4, 5], p=[.24, .18, .18, .16, .12, .12]))
    for y in range(H):
        for x in range(W):
            ch = GROUND[y][x]
            if ch == "^":
                s = (x * 7) % 4
                ground[y, x] = ts.add(("top", s), lambda f, s=s: TL.wall_top(s))
            elif ch in "#H":
                v = 1 if (x in (3, 13, 16) or ch == "H") else 2 if x == 6 else 0
                s = (x * 3 + y) % 3
                ground[y, x] = ts.add(("face", v, s), lambda f, v=v, s=s: TL.wall_face(v, s))
            elif ch == "A":
                part = (0 if x == 9 else 1, 0 if y == 2 else 1)
                ground[y, x] = ts.add(("arch", part), lambda f, p=part: TL.arch(p))
            elif ch == "w":
                flags = frozenset(d for d, (dx, dy) in {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0),
                                                       "NE": (1, -1), "NW": (-1, -1), "SE": (1, 1), "SW": (-1, 1)}.items()
                                  if not iswater(x + dx, y + dy) and not (x + dx < 0 or x + dx >= W))
                ground[y, x] = ts.add(("water", tuple(sorted(flags))), lambda f, fl=flags: TL.water(fl, f))
            else:
                v = floor_plan[y][x]
                sh = y == 4
                ground[y, x] = ts.add(("floor", v, sh), lambda f, v=v, sh=sh: TL.floor(v, shadow=sh))
    # deco: moon emblem above the arch, pillars, braziers, mushrooms, tufts, lily pads, rubble
    deco[1, 9] = ts.add(("moon",), lambda f: TL.moon_emblem())
    for px_ in (1, 18):
        deco[1, px_] = ts.add(("pillar", 0), lambda f: TL.pillar(0))
        deco[2, px_] = ts.add(("pillar", 1), lambda f: TL.pillar(1))
        deco[3, px_] = ts.add(("pillar", 2), lambda f: TL.pillar(2))
    deco[3, 7] = ts.add(("pillar", 1, "broken"), lambda f: TL.pillar(1, broken=True))
    deco[4, 7] = ts.add(("pillar", 2), lambda f: TL.pillar(2))
    for bx in (5, 14):
        deco[3, bx] = ts.add(("brazier", 0), lambda f: TL.brazier(0, f))
        deco[4, bx] = ts.add(("brazier", 1), lambda f: TL.brazier(1, f))
    for (x, y, v) in ((10, 6, 0), (18, 8, 1), (2, 4, 0), (12, 4, 1), (16, 10, 0), (3, 9, 1)):
        deco[y, x] = ts.add(("mush", v), lambda f, v=v: TL.mushrooms(f, v))
    for (x, y, s) in ((0, 5, 0), (8, 5, 1), (17, 4, 2), (19, 9, 3), (9, 10, 4), (4, 11, 5), (11, 4, 6)):
        deco[y, x] = ts.add(("tuft", s), lambda f, s=s: TL.tuft(s))
    for (x, y) in ((12, 7), (16, 6), (14, 9)):
        deco[y, x] = ts.add(("lily",), lambda f: TL.lily(f))
    for (x, y, s) in ((6, 6, 0), (19, 5, 1), (8, 9, 2)):
        deco[y, x] = ts.add(("rubble", s), lambda f, s=s: TL.rubble(s))
    # moss carpets (2x2 blobs) in quiet corners of the floor; the blob's cells go on the deco layer where free
    for (x0, y0, s) in ((0, 6, 0), (17, 9, 1), (6, 10, 2), (9, 4, 3)):
        for py in range(2):
            for px_ in range(2):
                x, y = x0 + px_, y0 + py
                if x < W and y < H and deco[y, x] < 0 and GROUND[y][x] == ".":
                    deco[y, x] = ts.add(("mosspatch", s, px_, py), lambda f, s=s, p=(px_, py): TL.moss_patch(p, s))
    # vines hanging over the wall (front of the wall, behind the fighters): deco layer too, on wall rows
    for x in (4, 11, 15):
        if deco[1, x] < 0:
            deco[1, x] = ts.add(("vine",), lambda f: TL.vine(f))
    # front: fern fronds at the bottom corners
    for x0 in (4, 17):
        front[11, x0] = ts.add(("fern", 0), lambda f: TL.fern(0, f))
        front[11, x0 + 1] = ts.add(("fern", 1), lambda f: TL.fern(1, f))
    return ts, {"ground": ground, "deco": deco, "front": front}


def render(ts, layers, f, which=("ground", "deco")):
    img = canvas(W * TS, H * TS)
    for name in which:
        m = layers[name]
        for y in range(H):
            for x in range(W):
                if m[y, x] >= 0:
                    blit(img, ts.frames[m[y, x]][f], x * TS, y * TS)
    return img


if __name__ == "__main__":
    ts, layers = build()
    print(len(ts.keys), "unique tiles")
    for f in range(4):
        save(ts.sheet(f), OUT / f"tileset_f{f}.png")
    img = render(ts, layers, 0, ("ground", "deco", "front"))
    save(img[:180], OUT / "map_f0.png", s=3)
    from PIL import Image
    fr = [Image.fromarray(render(ts, layers, f, ("ground", "deco", "front"))[:180]).resize((960, 540), Image.NEAREST)
          for f in range(4)]
    fr[0].save(OUT / "map_anim.gif", save_all=True, append_images=fr[1:], duration=160, loop=0)
    json.dump({k: v.tolist() for k, v in layers.items()}, open(OUT / "map.json", "w"))
