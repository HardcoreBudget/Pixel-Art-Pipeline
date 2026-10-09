"""Grimhold's moveset, every frame assembled from his design's pieces by the rig (see rig.py)."""
import math
import sys
import pathlib

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rig as R
import grimhold as K

SPEC = {
    "waist": "waist", "neck": "neck", "pelvis": "pelvis", "torso": "torso", "head": "head",
    "limbs": {
        "rl": {"pieces": ("r_thigh", "r_shin", "r_foot"), "joints": ("r_hip", "r_knee", "r_ankle"), "on": "pelvis"},
        "ll": {"pieces": ("l_thigh", "l_shin", "l_foot"), "joints": ("l_hip", "l_knee", "l_ankle"), "on": "pelvis"},
        "ra": {"pieces": ("ra_upper", "ra_fore", None), "joints": ("ra_sh", "ra_el", "ra_wr")},
        "la": {"pieces": ("la_upper", "la_fore", None), "joints": ("la_sh", "la_el", "la_wr")},
    },
    "cloth": {"tabard": {"anchor": "belt", "reach": 14, "on": "pelvis", "k": 0.4}},
    "order": K.ORDER,
    "support": ["head", "torso", "pelvis", "tabard", "r_thigh", "r_shin", "r_foot", "l_thigh", "l_shin", "l_foot"],
}
RIG = R.Rig(dict(np.load(K.OUT / "grimhold_layers.npz")), K.JOINTS, SPEC)
G = 89


def P(**kw):
    p = {"rl": (0, 0, 0, "abs"), "ll": (0, 0, 0, "abs")}
    p.update(kw)
    return p


def cloth(ph, tab=(0, 4)):
    return {"tabard": (tab[0], tab[1], ph)}


def anims():
    A = {}
    b = [0, 0, 1, 1, 1, 0]
    A["stance"] = [P(root=(0, b[i]), lean=b[i] * 0.6, la=(0, b[i], 0, "rest"), ra=(0, b[i], 0, "rest"),
                     head=(0, [0, 0, 0, 1, 1, 0][i], 0), cloth=cloth(i * math.pi / 3)) for i in range(6)]
    # a heavy stomping walk: each foot lifts and plants with a lurch of the shoulders
    LX = [2, 1, 0, -1, -2, -0.5, 1, 2]
    LY = [0, 0, 0, 0, 0, -3, -4, -1]
    A["walk"] = [P(root=(0, [2, 1, 0, 1, 2, 1, 0, 1][i]), lean=[3, 2, 1, 2, 3, 2, 1, 2][i], ll=(LX[i], LY[i], 0, "abs"),
                   rl=(LX[(i + 4) % 8], LY[(i + 4) % 8], 0, "abs"), la=(0, [2, 1, 0, 1, 2, 1, 0, 1][i], 0, "rest"),
                   cloth=cloth(i * math.pi / 4, tab=(4, 4))) for i in range(8)]
    # hook: the lead gauntlet cocks back, swings round in an arc, follows through, recovers
    A["hook"] = [
        P(root=(-2, 1), lean=-8, la=(-7, 3, 0, "rest"), cloth=cloth(0)),
        P(root=(-1, 1), lean=-4, la=(-4, 1, 0, "rest"), cloth=cloth(0.5)),
        P(root=(3, 1), lean=10, la=(18, 0, 0, "root"), ll=(2, 0, 0, "abs"), cloth=cloth(1.0, tab=(-6, 4))),
        P(root=(4, 2), lean=14, la=(15, 6, 0, "root"), ll=(2, 0, 0, "abs"), cloth=cloth(1.5, tab=(-6, 4))),
        P(root=(3, 2), lean=12, la=(12, 8, 0, "root"), ll=(2, 0, 0, "abs"), cloth=cloth(2.0, tab=(-3, 4))),
        P(root=(1, 1), lean=4, ll=(1, 0, 0, "abs"), cloth=cloth(2.5)),
    ]
    # shoulder charge: drop the shoulder, then drive in with a pounding run (unplanted feet), impact
    STR = [(6, 10, -10), (1, 11, 0), (-5, 9, 20), (-3, 4, 40)]
    run = []
    for i in range(4):
        near, far = STR[i], STR[(i + 2) % 4]
        run.append(P(root=(3, 3 + [0, 1, 0, 1][i]), lean=26, ll=(near[0], near[1], near[2], "root"),
                     rl=(far[0] - 2, far[1], far[2], "root"), la=(-3, 6, 0, "rest"), ra=(5, 3, 0, "rest"),
                     cloth=cloth(i * 1.5, tab=(-14, 4))))
    A["charge"] = [P(root=(0, 4), lean=18, la=(-3, 6, 0, "rest"), ra=(4, 3, 0, "rest"), cloth=cloth(0))] + run + \
        [P(root=(5, 3), lean=30, ll=(4, 0, 0, "abs"), la=(-2, 5, 0, "rest"), ra=(6, 2, 0, "rest"), cloth=cloth(6, tab=(-16, 3)))]
    # ground slam: both fists raised overhead, then down onto the stones, the impact held, recover
    up = dict(la=(3, -18, 0, "root"), ra=(12, -15, 0, "root"))
    A["slam"] = [
        P(root=(0, 1), lean=-2, cloth=cloth(0)),
        P(root=(-1, -2), lean=-12, head=(0, 0, -6), **up, cloth=cloth(0.6, tab=(4, 4))),
        P(root=(-1, -3), lean=-15, head=(0, 0, -8), la=(2, -19, 0, "root"), ra=(11, -16, 0, "root"), cloth=cloth(1.2, tab=(6, 4))),
        P(root=(2, 7), lean=30, la=(14, 16, 0, "root"), ra=(16, 14, 0, "root"), ll=(2, 0, 0, "abs"), cloth=cloth(1.8, tab=(-10, 3))),
        P(root=(2, 8), lean=32, la=(14, 17, 0, "root"), ra=(16, 15, 0, "root"), ll=(2, 0, 0, "abs"), cloth=cloth(2.4, tab=(-8, 3))),
        P(root=(2, 7), lean=30, la=(14, 16, 0, "root"), ra=(16, 14, 0, "root"), ll=(2, 0, 0, "abs"), cloth=cloth(3.0, tab=(-6, 3))),
        P(root=(1, 2), lean=6, ll=(1, 0, 0, "abs"), cloth=cloth(3.6)),
    ]
    # uppercut: dip with the gauntlet low, drive it up past the helmet, hold, recover
    A["uppercut"] = [
        P(root=(0, 5), lean=12, la=(0, 8, 0, "rest"), cloth=cloth(0)),
        P(root=(2, 2), lean=4, la=(14, 2, 0, "root"), cloth=cloth(0.6)),
        P(root=(3, -3), lean=-10, la=(12, -14, 0, "root"), rl=(0, -1, 15, "abs"), cloth=cloth(1.2, tab=(4, 4))),
        P(root=(3, -4), lean=-11, la=(11, -15, 0, "root"), rl=(0, -1, 15, "abs"), cloth=cloth(1.8, tab=(4, 4))),
        P(root=(1, 1), lean=2, la=(2, 2, 0, "rest"), cloth=cloth(2.4)),
        P(root=(0, 0), cloth=cloth(3.0)),
    ]
    # roar: chest out, helmet up, arms spread low, the whole body shaking
    A["roar"] = [P(root=(k % 2, -1), lean=-12, head=(0, -1, -12), la=(7, 7, 0, "rest"), ra=(-6, 6, 0, "rest"),
                   cloth=cloth(k, tab=(0, 5))) for k in range(4)]
    # block: gauntlets up before the helmet; the second frame is the push of a blocked blow
    A["block"] = [P(root=(-1 - 2 * k, 1), lean=-6, la=(-8, -6, 0, "rest"), ra=(8, -8, 0, "rest"), cloth=cloth(k))
                  for k in range(2)]
    A["hit"] = [
        P(root=(-3, 0), lean=-16, head=(-1, 0, -10), la=(-4, -3, 0, "rest"), ra=(-3, -4, 0, "rest"), cloth=cloth(0, tab=(8, 3))),
        P(root=(-3, 0), lean=-10, head=(-1, 0, -6), la=(-3, -2, 0, "rest"), cloth=cloth(0.8, tab=(5, 3))),
        P(root=(-1, 0), lean=-4, head=(0, 0, -2), cloth=cloth(1.6)),
    ]
    air = dict(ll=(5, 10, 10, "root"), rl=(0, 11, 10, "root"))
    flat = dict(ll=(-15, 6, 0, "root"), rl=(-8, 12, 0, "root"), la=(-1, 15, 0, "root"), ra=(-2, 15, 0, "root"))
    A["knockdown"] = [
        P(lean=-10, spin=-30, **air, la=(-5, -4, 0, "rest"), ra=(-6, -5, 0, "rest"), cloth=cloth(0, tab=(10, 3))),
        P(root=(0, 4), lean=-6, spin=-60, **air, la=(-5, -6, 0, "rest"), ra=(-6, -6, 0, "rest"), cloth=cloth(0.7, tab=(14, 3))),
        P(spin=-85, ll=(1, 13, 0, "root"), rl=(-2, 13, 0, "root"), la=(-4, -6, 0, "rest"), ra=(-5, -6, 0, "rest"), ground=G - 1, cloth=cloth(1.4, tab=(16, 3))),
        P(spin=-90, **flat, ground=G, cloth=cloth(2.1, tab=(8, 2))),
        P(spin=-84, **flat, ground=G - 3, cloth=cloth(2.8, tab=(10, 2))),
        P(spin=-90, **flat, ground=G, cloth=cloth(3.5, tab=(6, 1))),
    ]
    A["getup"] = [
        A["knockdown"][-1],
        P(spin=-45, ll=(8, 6, 0, "root"), rl=(4, 8, 0, "root"), la=(2, 5, 0, "rest"), ra=(-4, 6, 0, "rest"), ground=G, cloth=cloth(0.7, tab=(6, 3))),
        P(root=(0, 4), spin=-10, lean=8, la=(0, 3, 0, "rest"), cloth=cloth(1.4, tab=(4, 4))),
        P(root=(0, 1), lean=2, cloth=cloth(2.1)),
    ]
    A["launch"] = [P(root=(0, -2), lean=-12, spin=-20 * (k + 1), ll=(4 + k, 10, 10, "root"), rl=(-1, 11, 10, "root"),
                     la=(-5, -5 - k, 0, "rest"), ra=(-6, -6 - k, 0, "rest"), head=(0, 0, -8), cloth=cloth(k * 0.7, tab=(12, 3)))
                   for k in range(3)]
    return A


def build_frames(out_dir=None):
    out_dir = out_dir or (K.OUT / "sprites" / "grimhold")
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in out_dir.glob("*.png"):
        f.unlink()
    report = {}
    for name, poses in anims().items():
        for i, p in enumerate(poses):
            img = RIG.frame(p)
            Image.fromarray(img).save(out_dir / f"{name}_{i}.png")
            report[f"{name}_{i}"] = R.holes(img)
    return report


if __name__ == "__main__":
    rep = build_frames()
    bad = {k: v for k, v in rep.items() if v != (0, 0)}
    print(len(rep), "frames; pinholes/specks:", bad or "none")
