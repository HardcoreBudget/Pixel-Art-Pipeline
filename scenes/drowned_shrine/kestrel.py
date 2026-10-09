"""Kestrel: layers from the Krea design's own pixels (re-pixelated into the scene palette), back to front.

ORDER (bottom first): cloak, scarf_tail, back_leg, torso, front_leg, wrap, head, arms (both arms, the hands and
the sword: one unit that swings about the shoulder)."""
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
from agentdraw.core import poly_mask, rect_mask, assign, take, shade_fill, settle, reassign_islands, composite, diff, layer_sheet, overlay
from px import C, OUT, RAMPS, hx, DESIGNS

ORDER = ["cloak", "scarf_tail", "b_shin", "b_boot", "b_thigh", "f_shin", "f_boot", "f_thigh", "torso", "wrap", "head", "arms"]
# joints in design coordinates (64 x 64): measured on the design (x right, y down)
JOINTS = {"f_hip": (40.5, 41.0), "f_knee": (41.0, 48.5), "f_ankle": (39.5, 53.5),
          "b_hip": (25.5, 46.5), "b_knee": (21.5, 52.0), "b_ankle": (19.5, 55.5),
          "shoulder": (39.0, 29.0), "arm_root": (37.5, 37.0), "hands": (46.0, 35.0)}
SPR = OUT / "sprites" / "kestrel"
SPR.mkdir(parents=True, exist_ok=True)


def cm(img, *names):
    m = np.zeros(img.shape[:2], bool)
    for n in names:
        m |= (img[..., :3] == C[n][:3]).all(-1) & (img[..., 3] > 0)
    return m


def clean(g):
    g = g.copy()
    # the ground shadow Krea drew under the feet, and the white background left between the legs
    g[59:][cm(g[59:], "silver1")] = 0
    gap = np.zeros(g.shape[:2], bool); gap[50:59, 21:37] = True
    g[gap & cm(g, "silver3")] = 0
    # the blade: Krea drew its outline and ridge; its flat (left of the ridge) is background. Fill enclosed gaps.
    blade = np.zeros(g.shape[:2], bool); blade[9:34, 44:62] = True
    solid = g[..., 3] > 0
    holes = ndimage.binary_fill_holes(solid & blade) & ~solid & blade
    g[holes] = C["silver2"]
    # the blade's lit edge: the flat pixel next to the left outline
    for y in range(9, 34):
        xs = [x for x in range(44, 62) if holes[y, x]]
        if xs:
            g[y, xs[0]] = C["silver3"]
    return g


def ownership(ref):
    wood = cm(ref, "ink", "wood0", "wood1", "wood2", "wood3", "skin0", "skin1", "night0")
    arms = poly_mask([(31, 32), (44, 30), (50, 31), (51, 38), (47, 41), (38, 41), (33, 40)]) & wood
    head = poly_mask([(19, 1), (52, 1), (52, 21), (46, 24), (34, 23.5), (32, 21), (27, 21), (22, 22), (19, 18)])
    wrap = poly_mask([(26, 20), (34, 20), (35, 24), (43, 24), (43, 31), (36, 31), (30, 30), (26, 28)])
    tail = poly_mask([(1, 26), (10, 24), (18, 20), (26.5, 20), (26.5, 30), (20, 30), (13, 33), (10, 38), (1, 38)])
    f_thigh = poly_mask([(36, 40), (47, 40), (47, 47), (44, 50.5), (38, 50.5), (36, 46)]) & wood
    f_shin = poly_mask([(35, 49.5), (45, 48.5), (45, 55), (48, 57), (48, 62), (33, 62), (35, 56)]) & wood
    b_thigh = poly_mask([(18, 45), (30, 44), (30, 48), (26, 53.5), (19, 53)]) & wood
    b_shin = poly_mask([(14, 51.5), (26, 51.5), (25, 57), (26, 62), (14, 62)]) & wood
    torso = poly_mask([(21, 28), (26, 25), (36, 24), (45, 27), (45, 36), (40, 38), (40, 46), (36, 48), (21, 48), (21, 38)])
    teal = cm(ref, "teal0", "teal1", "teal2", "teal3")
    cloak = np.ones(ref.shape[:2], bool)
    blade = poly_mask([(43, 8), (62, 8), (62, 22), (53, 34), (43, 36), (41, 30), (49, 22)]) & \
        cm(ref, "ink", "silver0", "silver1", "silver2", "silver3", "stone0", "stone3", "stone5", "night0")
    blade_col = cm(ref, "silver0", "silver1", "silver2", "silver3", "stone0", "stone3", "stone5")
    blade |= poly_mask([(46, 8), (62, 8), (62, 24), (46, 24)]) & (blade_col | cm(ref, "ink")) & (np.arange(64)[None, :] > 48)
    parts = [("cloak_t", teal & ~arms), ("arms", arms), ("blade", blade & ~arms), ("head", head), ("wrap", wrap), ("f_thigh", f_thigh),
             ("f_shin", f_shin), ("b_thigh", b_thigh), ("b_shin", b_shin), ("torso", torso),
             ("scarf_tail", tail), ("cloak", cloak)]
    L, rest = assign(ref, parts)
    m = L.pop("cloak_t")[..., 3] > 0
    L["cloak"][m] = ref[m]
    L.pop("blade")                      # the sword is redrawn every frame at the hands
    for side, cut in (("f", 53), ("b", 55)):   # the boot starts at its cuff row
        sh = L[side + "_shin"]
        boot = np.zeros_like(sh); boot[cut:] = sh[cut:]; sh[cut:] = 0
        L[side + "_boot"] = boot
    # the arms piece is the forearms and gloves only (rows 33-41, x 36-48): the guard and grip lines around the
    # hands belong to the sword (redrawn), the belt pixels to its left belong to the torso
    keep = rect_mask(36, 33, 48, 41) & ~rect_mask(42, 30, 48, 33)
    a = L["arms"]
    belt = (a[..., 3] > 0) & ~keep & (np.arange(64)[None, :] < 36)
    L["torso"][belt] = a[belt]
    a[~keep] = 0
    return L


def ramp(name, lo=0, hi=None):
    r = RAMPS[name][lo:hi]
    return [hx(h) for h in r]


def hidden(L):
    """What the parts hide, drawn in their own colours so a moved part never uncovers a hole."""
    ink = hx(RAMPS["ink"][0])
    pants = ramp("wood", 1, 4)
    # the torso under the arms and the scarf wrap: tunic continues
    shade_fill(L["torso"], poly_mask([(24, 27), (40, 25), (44, 30), (42, 38), (26, 38)]), ramp("cream"), ink)
    # the head's neck under the wrap
    shade_fill(L["head"], poly_mask([(33, 18), (43, 18), (43, 27), (33, 27)]), ramp("skin", 1), ink)
    # each thigh continues up under the tunic to a rounded hip; each shin continues up under the thigh to the knee
    shade_fill(L["f_thigh"], poly_mask([(36, 37), (45, 37), (46, 45), (38, 46), (35, 42)]), pants, ink)
    shade_fill(L["f_shin"], poly_mask([(37, 45), (45, 45), (44, 51), (37, 51)]), pants, ink)
    # each shin reaches down inside its boot's cuff, so a turned boot never shows a gap at the ankle
    shade_fill(L["f_shin"], poly_mask([(37, 51), (42, 51), (42, 55), (37, 55)]), pants, ink)
    shade_fill(L["b_shin"], poly_mask([(17, 53), (22, 53), (22, 57), (17, 57)]), pants, ink)
    shade_fill(L["b_thigh"], poly_mask([(21, 41), (30, 41), (31, 47), (24, 50), (20, 47)]), pants, ink)
    shade_fill(L["b_shin"], poly_mask([(17, 48), (25, 48), (25, 54), (17, 54)]), pants, ink)
    # the arms continue left under the tunic (their root turns there when she swings)
    shade_fill(L["arms"], poly_mask([(31, 33), (39, 33), (39, 40), (31, 40)]), ramp("wood", 1, 4), ink)
    # the cloak behind the torso and the legs
    shade_fill(L["cloak"], poly_mask([(12, 28), (40, 25), (42, 34), (36, 52), (14, 52)]), ramp("teal"), ink)
    # the scarf tail's root behind the wrap
    shade_fill(L["scarf_tail"], poly_mask([(20, 21), (31, 21), (31, 28), (20, 29)]), ramp("crimson", 1, 4), ink)
    return L


def main():
    g = np.asarray(Image.open(DESIGNS / "kestrel_9101_grid.png").convert("RGBA")).copy()
    ref = clean(g)
    Image.fromarray(ref).save(SPR / "design.png")
    L = ownership(ref)
    for n in list(L):
        reassign_islands(L, n)
    overlay(ref, L, ORDER[::-1], OUT / "kestrel_ownership.png", s=10)
    noblade = ref.copy(); noblade[composite(L, ORDER)[..., 3] == 0] = 0
    ref = noblade
    print("partition diff (without the blade)", diff(composite(L, ORDER), ref))
    part = {k: v.copy() for k, v in L.items()}
    L = hidden(L)
    print("dropped:", settle(L, ORDER, part))
    print("stack diff", diff(composite(L, ORDER), ref))
    layer_sheet(L, ORDER, OUT / "kestrel_layers.png", ref, s=6, cols=4,
                title=f"Kestrel - {len(ORDER)} layers; stack == design: {diff(composite(L, ORDER), ref) == 0}")
    np.savez_compressed(OUT / "kestrel_layers.npz", **L)


if __name__ == "__main__":
    main()
