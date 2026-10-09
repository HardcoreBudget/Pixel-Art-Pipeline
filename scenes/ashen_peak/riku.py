"""Riku: pieces cut from the Krea design (seed 7101, re-pixelated into the palette), back to front.

Pieces: band (headband tails, cloth), r_thigh r_shin r_foot (rear leg), l_thigh l_shin l_foot (lead leg),
skirt (the gi's lower flaps, cloth), pelvis (belt), torso, head, ra_upper ra_fore (rear arm, the fist is part of the
forearm), la_upper la_fore (lead arm)."""
import sys
import pathlib

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "drowned_shrine"))
sys.path.insert(0, str(HERE.parent))
from agentdraw.core import poly_mask, rect_mask, ellipse_mask, assign, shade_fill, settle, composite, diff, \
    reassign_islands, layer_sheet, overlay
from px import C, RAMPS, hx, OUT as SOUT, DESIGNS
OUT = SOUT.parent / "ashen_peak"

JOINTS = {
    "r_hip": (27.0, 46.0), "r_knee": (19.5, 52.0), "r_ankle": (17.5, 57.0),
    "l_hip": (38.0, 46.0), "l_knee": (41.0, 51.5), "l_ankle": (41.0, 57.0),
    "la_sh": (38.0, 28.0), "la_el": (40.5, 37.0), "la_wr": (47.0, 35.0),
    "ra_sh": (24.0, 28.0), "ra_el": (20.0, 36.5), "ra_wr": (28.0, 35.0),
    "neck": (33.0, 24.0), "waist": (31.0, 40.0), "knot": (23.0, 14.0), "belt": (31.0, 40.0),
}
ORDER = ["band", "r_thigh", "r_shin", "r_foot", "l_thigh", "l_shin", "l_foot", "la_upper", "torso", "skirt", "pelvis",
         "head", "ra_upper", "ra_fore", "la_fore"]


def cm(img, *names):
    m = np.zeros(img.shape[:2], bool)
    for n in names:
        m |= (img[..., :3] == C[n][:3]).all(-1) & (img[..., 3] > 0)
    return m


def rmp(name, lo=0, hi=None):
    return [hx(h) for h in RAMPS[name][lo:hi]]


def ownership(ref):
    skin = cm(ref, "skin0", "skin1", "skin2", "skin3", "wood1", "wood0", "crimson4")
    band_col = cm(ref, "crimson1", "crimson2", "fire1", "fire2", "fire6", "skin0", "ink", "wood0")
    band = poly_mask([(4, 20), (14, 13), (23, 12), (24, 16), (20, 20), (19, 26), (16, 32), (10, 32), (4, 24)]) & band_col
    head = poly_mask([(21, 1), (50, 1), (50, 16), (45, 24), (37, 25), (28, 25), (22, 20), (21, 8)])
    # the lead fist and forearm: right of the elbow; the upper arm: from the shoulder down to the elbow
    la_fore = poly_mask([(40, 32), (46, 26), (55, 25), (56, 38), (48, 39), (41, 39)]) & ~head
    la_upper = poly_mask([(35, 29), (41, 26), (44, 31), (43, 39), (38, 39), (35, 34)]) & skin
    # the rear arm: the bicep on the left, the forearm and fist crossing the chest
    ra_upper = poly_mask([(16, 29), (22, 25), (27, 27), (26, 31), (22.5, 32), (22.5, 39), (17, 39)]) & (skin | cm(ref, "ink"))
    ra_fore = poly_mask([(19, 31), (28, 30), (36, 31), (36, 38), (26, 39), (19, 38)]) & (skin | cm(ref, "warm0", "warm1", "crimson4"))
    pelvis = rect_mask(22, 38, 40, 40)
    skirt = poly_mask([(20, 40), (41, 40), (42, 45), (38, 47), (24, 47), (20, 44)]) & cm(ref, "fire1", "fire2", "fire3", "ink", "crimson1", "crimson2", "wood0")
    l_foot = rect_mask(34, 55, 50, 62)
    r_foot = rect_mask(11, 55, 23, 62)
    l_shin = poly_mask([(35, 50), (46, 49), (47, 56), (35, 56)])
    r_shin = poly_mask([(14, 50), (25, 49), (24, 56), (13, 56)])
    l_thigh = poly_mask([(32, 43), (46, 43), (46, 51), (35, 52), (32, 48)])
    r_thigh = poly_mask([(17, 43), (32, 43), (32, 49), (24, 53), (16, 52)])
    torso = np.ones(ref.shape[:2], bool)
    parts = [("band", band), ("head", head), ("la_fore", la_fore), ("la_upper", la_upper), ("ra_upper", ra_upper),
             ("ra_fore", ra_fore), ("pelvis", pelvis), ("skirt", skirt), ("l_foot", l_foot), ("r_foot", r_foot),
             ("l_shin", l_shin), ("r_shin", r_shin), ("l_thigh", l_thigh), ("r_thigh", r_thigh), ("torso", torso)]
    L, rest = assign(ref, parts)
    return L


def hidden(L):
    ink = hx(RAMPS["ink"][0])
    pants = rmp("warm", 0, 3)
    gi = rmp("fire", 1, 4)
    skin = rmp("skin", 1, 4)
    # the torso behind both arms: the gi and chest continue (gi colours; the chest's skin shows in the design)
    shade_fill(L["torso"], poly_mask([(22, 25), (42, 25), (42, 39), (21, 39)]), gi, ink)
    # ... and down under the belt and skirt, so a leaning torso never opens a wedge at the waist
    shade_fill(L["torso"], poly_mask([(21, 36), (41, 36), (41, 45), (21, 45)]), gi, ink)
    # the upper arms continue under the forearms to the elbow; the forearms reach back into the elbow
    # the lead upper arm sits behind the chest at rest: paint it whole (shoulder cap to elbow) so a punch shows it
    from rig import rot
    shade_fill(L["la_upper"], poly_mask([(35, 26), (41, 25), (44, 30), (44, 38), (38, 39), (36, 33)]), skin, ink)
    shade_fill(L["ra_upper"], poly_mask([(19, 27), (26, 27), (24, 38), (18, 38)]), skin, ink)
    shade_fill(L["la_fore"], ellipse_mask(41, 36.5, 2.6, 2.4), skin, ink)
    shade_fill(L["ra_fore"], ellipse_mask(20.5, 35.5, 2.6, 2.4), skin, ink)
    # thighs up under the skirt to the hip; shins up inside the knee; feet reach up into the shin
    shade_fill(L["l_thigh"], poly_mask([(33, 40), (43, 40), (44, 47), (34, 47)]), pants, ink)
    shade_fill(L["r_thigh"], poly_mask([(22, 40), (32, 40), (31, 48), (22, 48)]), pants, ink)
    shade_fill(L["l_shin"], poly_mask([(37, 47), (45, 47), (45, 52), (37, 52)]), pants, ink)
    shade_fill(L["r_shin"], poly_mask([(16, 48), (23, 48), (23, 53), (16, 53)]), pants, ink)
    shade_fill(L["l_shin"], poly_mask([(37, 54), (44, 54), (44, 58), (37, 58)]), pants, ink)
    shade_fill(L["r_shin"], poly_mask([(14, 54), (21, 54), (21, 58), (14, 58)]), pants, ink)
    # the skirt behind the pelvis; the head's neck under the collar
    shade_fill(L["skirt"], poly_mask([(22, 38), (40, 38), (40, 42), (22, 42)]), gi, ink)
    shade_fill(L["head"], poly_mask([(29, 21), (38, 21), (38, 27), (29, 27)]), skin, ink)
    # the headband's knot under the hair
    shade_fill(L["band"], poly_mask([(19, 11), (26, 11), (26, 16), (19, 16)]), rmp("crimson", 1, 4), ink)
    return L


def build():
    ref = np.asarray(Image.open(DESIGNS / "riku_7101_grid.png").convert("RGBA")).copy()
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(ref).save(OUT / "riku_design.png")
    L = ownership(ref)
    for n in list(L):
        reassign_islands(L, n, max_px=12)

    overlay(ref, L, ORDER[::-1], OUT / "riku_ownership.png", s=10)
    print("partition diff", diff(composite(L, ORDER), ref))
    part = {k: v.copy() for k, v in L.items()}
    L = hidden(L)
    print("dropped", settle(L, ORDER, part))
    from rig import adopt_fragments
    print("fragments adopted:", adopt_fragments(L, order=ORDER))
    print("stack diff", diff(composite(L, ORDER), ref))
    layer_sheet(L, ORDER, OUT / "riku_layers.png", ref, s=5, cols=5,
                title=f"Riku - {len(ORDER)} pieces; stack == design: {diff(composite(L, ORDER), ref) == 0}")
    np.savez_compressed(OUT / "riku_layers.npz", **L)
    return L


if __name__ == "__main__":
    build()
