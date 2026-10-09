"""Grimhold: pieces cut from the Krea design (seed 7301, re-pixelated into the palette), back to front.

Pieces: r_thigh r_shin r_foot (rear leg), l_thigh l_shin l_foot (lead leg), tabard (the hanging front cloth),
ra_upper ra_fore (rear arm: crimson sleeve, iron gauntlet with the fist), torso (chest plate and pauldrons),
pelvis (belt), head (helmet and horns), la_upper la_fore (lead arm)."""
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
    "r_hip": (22.0, 41.0), "r_knee": (18.0, 49.0), "r_ankle": (15.0, 55.0),
    "l_hip": (38.0, 41.0), "l_knee": (41.0, 49.0), "l_ankle": (40.0, 55.0),
    "ra_sh": (17.0, 23.0), "ra_el": (7.0, 28.0), "ra_wr": (10.0, 39.0),
    "la_sh": (42.0, 27.0), "la_el": (46.0, 37.0), "la_wr": (51.0, 30.0),
    "neck": (35.0, 14.0), "waist": (31.0, 37.0), "belt": (30.0, 39.0),
}
ORDER = ["ra_upper", "ra_fore", "r_thigh", "r_shin", "r_foot", "l_thigh", "l_shin", "l_foot", "la_upper", "torso",
         "tabard", "pelvis", "head", "la_fore"]


def cm(img, *names):
    m = np.zeros(img.shape[:2], bool)
    for n in names:
        m |= (img[..., :3] == C[n][:3]).all(-1) & (img[..., 3] > 0)
    return m


def rmp(name, lo=0, hi=None):
    return [hx(h) for h in RAMPS[name][lo:hi]]


def clean(g):
    g = g.copy()
    # the white background caught between the rear gauntlet and the body
    white = rect_mask(12, 30, 21, 38) & cm(g, "silver3")
    g[white] = 0
    return g


def ownership(ref):
    crimson = cm(ref, "crimson0", "crimson1", "crimson2", "fire0", "fire1")
    iron = cm(ref, "ink", "night0", "night1", "silver0", "silver1", "silver2", "stone0", "stone4")
    head = poly_mask([(24, 0), (47, 0), (47, 11), (42, 14), (29, 14), (24, 9)]) | \
        (poly_mask([(28, 10), (43, 10), (43, 15), (28, 15)]) & ~rect_mask(16, 13, 27, 20))
    la_fore = poly_mask([(47, 18), (60, 18), (60, 31), (54, 36), (47, 38), (46, 30)]) & (iron | cm(ref, "wood0"))
    la_upper = poly_mask([(39, 25), (48, 25), (49, 40), (43, 41), (39, 33)]) & crimson
    ra_fore = poly_mask([(3, 28), (14, 28), (18, 36), (17, 45), (8, 45), (3, 38)]) & ~crimson
    ra_upper = poly_mask([(3, 21), (18, 21), (18, 30), (4, 31)]) & (crimson | cm(ref, "ink", "wood0"))
    pelvis = poly_mask([(19, 35), (40, 35), (40, 40), (19, 40)]) & cm(ref, "wood0", "wood1", "ink", "silver0", "silver1", "night0")
    tabard = poly_mask([(26, 39), (35, 39), (35, 53), (26, 53)]) & ~rect_mask(0, 0, 25, 64) & \
        cm(ref, "crimson0", "crimson1", "crimson2", "night0", "night1", "ink", "fire0", "wood0")
    l_foot = rect_mask(33, 55, 50, 61)
    r_foot = rect_mask(8, 55, 22, 62)
    l_shin = poly_mask([(33, 47), (46, 47), (46, 55), (33, 55)])
    r_shin = poly_mask([(9, 47), (24, 47), (22, 55), (9, 55)])
    l_thigh = poly_mask([(33, 38), (47, 38), (47, 50), (34, 50)])
    r_thigh = poly_mask([(13, 38), (27, 38), (26, 50), (12, 50)])
    torso = np.ones(ref.shape[:2], bool)
    parts = [("head", head), ("la_fore", la_fore), ("la_upper", la_upper), ("ra_fore", ra_fore), ("ra_upper", ra_upper),
             ("tabard", tabard), ("pelvis", pelvis), ("l_foot", l_foot), ("r_foot", r_foot), ("l_shin", l_shin),
             ("r_shin", r_shin), ("l_thigh", l_thigh), ("r_thigh", r_thigh), ("torso", torso)]
    L, rest = assign(ref, parts)
    return L


def hidden(L):
    ink = hx(RAMPS["ink"][0])
    iron = [hx(h) for h in ("#141326", "#1E1D38", "#4E5670", "#8C95AE")]
    cloth = rmp("crimson", 0, 3)
    boots = rmp("wood", 0, 3)
    # the chest plate continues behind both arms and down behind the belt and tabard
    shade_fill(L["torso"], poly_mask([(18, 16), (44, 16), (44, 41), (19, 41)]), iron, ink)
    # the upper arms run under their pauldrons to the shoulder and down inside the gauntlet cuffs
    shade_fill(L["ra_upper"], poly_mask([(10, 18), (20, 18), (19, 29), (9, 30)]), cloth, ink)
    shade_fill(L["la_upper"], poly_mask([(39, 22), (46, 22), (48, 39), (41, 39)]), cloth, ink)
    shade_fill(L["ra_fore"], ellipse_mask(7.5, 29.5, 3.5, 3.0), iron, ink)
    shade_fill(L["la_fore"], ellipse_mask(46, 36, 3.2, 3.0), iron, ink)
    # thighs up under the belt; shins up into the knee; shins down inside the boots
    shade_fill(L["l_thigh"], poly_mask([(33, 36), (44, 36), (45, 44), (34, 44)]), cloth, ink)
    shade_fill(L["r_thigh"], poly_mask([(16, 36), (27, 36), (26, 44), (16, 44)]), cloth, ink)
    shade_fill(L["l_shin"], poly_mask([(35, 45), (45, 45), (45, 58), (35, 58)]), boots, ink)
    shade_fill(L["r_shin"], poly_mask([(11, 45), (23, 45), (21, 58), (10, 58)]), boots, ink)
    # the tabard hangs from under the belt; the helmet's neck under the collar
    shade_fill(L["tabard"], poly_mask([(26, 37), (35, 37), (35, 41), (26, 41)]), cloth, ink)
    shade_fill(L["head"], poly_mask([(30, 12), (41, 12), (41, 18), (30, 18)]), iron, ink)
    return L


def build():
    g = np.asarray(Image.open(DESIGNS / "grimhold_design_raw.png").convert("RGBA")).copy()
    ref = clean(g)
    Image.fromarray(ref).save(OUT / "grimhold_design.png")
    L = ownership(ref)
    for n in list(L):
        reassign_islands(L, n, max_px=12)

    overlay(ref, L, ORDER[::-1], OUT / "grimhold_ownership.png", s=10)
    print("partition diff", diff(composite(L, ORDER), ref))
    part = {k: v.copy() for k, v in L.items()}
    L = hidden(L)
    print("dropped", settle(L, ORDER, part))
    from rig import adopt_fragments
    print("fragments adopted:", adopt_fragments(L, order=ORDER))
    print("stack diff", diff(composite(L, ORDER), ref))
    layer_sheet(L, ORDER, OUT / "grimhold_layers.png", ref, s=5, cols=5,
                title=f"Grimhold - {len(ORDER)} pieces; stack == design: {diff(composite(L, ORDER), ref) == 0}")
    np.savez_compressed(OUT / "grimhold_layers.npz", **L)
    return L


if __name__ == "__main__":
    build()
