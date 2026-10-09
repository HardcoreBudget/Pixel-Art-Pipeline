"""Plugin documents for the scene, built headlessly in the SANDBOX Unity project (never the main one):

- ShrineTiles.pas: the tileset (8 tiles per row, 16 px), 4 frames (animated water, flames, mushrooms, ferns),
  tile size 16 and the Tiles tab's scratchpad = the arena's ground layer (20 x 12 cells).
- ShrineArena.pas: the arena itself, 320 x 192, layers ground / deco / front, 4 frames.
- Kestrel.pas: every animation, one tag each, layers by kestrel_anim.PAS_ORDER, canvas 96 x 80.
- Gloomlure.pas: likewise (when its frames exist).

Each build renders every frame back through the plugin's own compositor; the check is pixel equality."""
import json
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
from agentdraw.pas import export_job, build_many
from px import OUT

import tilemap as TM

JOBS = OUT / "pas_jobs"
JOBS.mkdir(parents=True, exist_ok=True)


def tiles_job():
    ts, layers = TM.build()
    frames = [ts.sheet(f) for f in range(4)]
    path = export_job("ShrineTiles", {"tiles": frames}, ["tiles"], tags=[("Animate", 0, 3)], durations=[160] * 4)
    job = json.loads(path.read_text())
    cols = 8
    g = layers["ground"]
    cells = []
    for y in range(TM.H):
        for x in range(TM.W):
            i = int(g[y, x])
            cells += [-1, -1] if i < 0 else [i % cols, i // cols]
    job["tiles"] = {"tileWidth": 16, "tileHeight": 16, "mapWidth": TM.W, "mapHeight": TM.H, "cells": cells}
    path.write_text(json.dumps(job))
    return path, frames


def arena_job():
    ts, layers = TM.build()
    per = {n: [TM.render(ts, layers, f, (n,)) for f in range(4)] for n in ("ground", "deco", "front")}
    path = export_job("ShrineArena", per, ["ground", "deco", "front"], tags=[("Animate", 0, 3)], durations=[160] * 4)
    flat = [TM.render(ts, layers, f, ("ground", "deco", "front")) for f in range(4)]
    return path, flat


def kestrel_job():
    import kestrel_anim as K
    A = K.anims()
    per = {n: [] for n in K.PAS_ORDER}
    flat, tags, durs = [], [], []
    ms = {"idle": 160, "run": 80, "slash1": 90, "slash2": 90, "hop": 100, "block": 110, "leap": 100, "plunge": 90, "victory": 140}
    for name, poses in A.items():
        a = len(flat)
        for p in poses:
            img, L = K.frame(p, named=True)
            for n in K.PAS_ORDER:
                per[n].append(L[n])
            flat.append(img); durs.append(ms[name])
        tags.append((name.capitalize(), a, len(flat) - 1))
    return export_job("Kestrel", per, K.PAS_ORDER, tags=tags, durations=durs), flat


def gloomlure_job():
    import gloomlure as G
    L0 = {k: G.pad(v) for k, v in np.load(OUT / "gloomlure_layers.npz").items()}
    A = G.anims()
    per = {n: [] for n in G.PAS_ORDER}
    flat, tags, durs = [], [], []
    ms = {"idle": 160, "windup": 160, "lunge": 90, "hurt": 100, "charge": 140, "stunned": 180}
    for name, poses in A.items():
        a = len(flat)
        for p in poses:
            img, L, _ = G.frame(L0, p, named=True)
            for n in G.PAS_ORDER:
                per[n].append(L[n])
            flat.append(img); durs.append(ms[name])
        tags.append((name.capitalize(), a, len(flat) - 1))
    return export_job("Gloomlure", per, G.PAS_ORDER, tags=tags, durations=durs), flat


def check(name, flat):
    bad = {}
    for f, img in enumerate(flat):
        p = OUT.parent / "agentdraw" / "pas_render" / name / f"pas_frame_{f:02d}.png"
        r = np.asarray(Image.open(p).convert("RGBA"))
        d = int((np.abs(r.astype(int) - img.astype(int)).sum(-1) > 0)[img[..., 3] > 0].sum()) + \
            int(((r[..., 3] > 0) != (img[..., 3] > 0)).sum())
        if d:
            bad[f] = d
    return bad


if __name__ == "__main__":
    which = sys.argv[1:] or ["tiles", "arena", "kestrel", "gloomlure"]
    made = {}
    for w in which:
        path, flat = {"tiles": tiles_job, "arena": arena_job, "kestrel": kestrel_job, "gloomlure": gloomlure_job}[w]()
        name = json.loads(path.read_text())["name"]
        made[name] = (path, flat)
    rc, log = build_many([(p, n) for n, (p, _) in made.items()])
    print("unity rc", rc, "log", log)
    for n, (_, flat) in made.items():
        print(n, "frames", len(flat), "plugin mismatches:", check(n, flat) or "none")
