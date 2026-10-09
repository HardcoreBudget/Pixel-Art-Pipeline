"""Plugin documents for Ashen Peak, built headlessly in the SANDBOX Unity project (never the main one), each frame
rendered back by the plugin and compared pixel for pixel:

- Riku.pas / Grimhold.pas: 128 x 96, one layer per design piece + the outline, one tag per animation.
- AshenPeak.pas: the stage, 400 x 144, its parallax layers (sky, far, near, temple, floor, fg), 8 frames with the
  lanterns swaying and the banners rippling on the temple layer."""
import json
import sys
import pathlib

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "drowned_shrine"))
sys.path.insert(0, str(HERE.parent))
from agentdraw.pas import export_job, build_many
from agentdraw.core import OUT as ADOUT
from px import canvas, blit
import stage as ST


def fighter_job(name, mod):
    A = mod.anims()
    order = list(mod.SPEC["order"]) + ["line"]
    per = {n: [] for n in order}
    flat, tags, durs = [], [], []
    for anim, poses in A.items():
        a = len(flat)
        for p in poses:
            img, L = mod.RIG.frame(p, named=True)
            for n in order:
                per[n].append(L[n])
            flat.append(img)
            durs.append(160 if anim in ("stance", "victory", "roar") else 80 if anim in ("walk", "charge") else 100)
        tags.append((anim.capitalize(), a, len(flat) - 1))
    return export_job(name, per, order, tags=tags, durations=durs), flat


def stage_job():
    S = ST.Stage()
    W = ST.STAGE_W
    names = ["sky", "far", "near", "temple", "floor", "fg"]
    per = {n: [] for n in names}
    flat = []
    for f in range(8):
        t = f * 3
        layers = {}
        for n in names:
            img = canvas(W, ST.VH)
            src = {"sky": S.sky, "far": S.far, "near": S.near, "temple": S.temple, "floor": S.floor, "fg": S.fg}[n]
            if n == "sky":                                      # the sky is fixed: repeat it across the stage
                blit(img, src, 0, 0); blit(img, src, src.shape[1], 0)
            else:
                blit(img, src, 0, 0)
            if n == "temple":
                for k, (dx, y) in enumerate(ST.LANTERNS):
                    blit(img, ST.lantern(t, k), S.pag_x + dx - 5, y - 5)
                for k, bx in enumerate((S.pag_x - 150, S.pag_x - 84, S.pag_x + 78, S.pag_x + 144)):
                    blit(img, ST.banner(t, k), bx, 58)
            layers[n] = img
            per[n].append(img)
        comp = canvas(W, ST.VH)
        for n in names:
            m = layers[n][..., 3] > 0
            comp[m] = layers[n][m]
        flat.append(comp)
    return export_job("AshenPeak", per, names, tags=[("Ambient", 0, 7)], durations=[240] * 8), flat


def check(name, flat):
    bad = {}
    for f, img in enumerate(flat):
        p = ADOUT / "pas_render" / name / f"pas_frame_{f:02d}.png"
        r = np.asarray(Image.open(p).convert("RGBA"))
        d = int((np.abs(r.astype(int) - img.astype(int)).sum(-1) > 0)[img[..., 3] > 0].sum()) + \
            int(((r[..., 3] > 0) != (img[..., 3] > 0)).sum())
        if d:
            bad[f] = d
    return bad


if __name__ == "__main__":
    import riku_anim, grimhold_anim
    made = {}
    for name, fn in (("Riku", lambda: fighter_job("Riku", riku_anim)), ("Grimhold", lambda: fighter_job("Grimhold", grimhold_anim)),
                     ("AshenPeak", stage_job)):
        path, flat = fn()
        made[name] = (path, flat)
    rc, log = build_many([(p, n) for n, (p, _) in made.items()])
    print("unity rc", rc)
    for n, (_, flat) in made.items():
        print(n, "frames", len(flat), "plugin mismatches:", check(n, flat) or "none")
