"""Riku's moveset, every frame assembled from his design's pieces by the rig (see rig.py)."""
import math
import sys
import pathlib

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rig as R
import riku as K

SPEC = {
    "waist": "waist", "neck": "neck", "pelvis": "pelvis", "torso": "torso", "head": "head",
    "limbs": {
        "rl": {"pieces": ("r_thigh", "r_shin", "r_foot"), "joints": ("r_hip", "r_knee", "r_ankle"), "on": "pelvis"},
        "ll": {"pieces": ("l_thigh", "l_shin", "l_foot"), "joints": ("l_hip", "l_knee", "l_ankle"), "on": "pelvis"},
        "ra": {"pieces": ("ra_upper", "ra_fore", None), "joints": ("ra_sh", "ra_el", "ra_wr")},
        "la": {"pieces": ("la_upper", "la_fore", None), "joints": ("la_sh", "la_el", "la_wr")},
    },
    "cloth": {"band": {"anchor": "knot", "reach": 22, "on": "head", "k": 0.3},
              "skirt": {"anchor": "belt", "reach": 10, "on": "pelvis", "k": 0.5}},
    "order": K.ORDER,
    "support": ["head", "torso", "pelvis", "skirt", "r_thigh", "r_shin", "r_foot", "l_thigh", "l_shin", "l_foot"],
}
RIG = R.Rig(dict(np.load(K.OUT / "riku_layers.npz")), K.JOINTS, SPEC)
FEET = (64, 89)          # the ground contact point on the 128 x 96 canvas


def P(**kw):
    """A pose with planted feet by default ('abs' offsets from the rest ankles)."""
    p = {"rl": (0, 0, 0, "abs"), "ll": (0, 0, 0, "abs")}
    p.update(kw)
    return p


def cloth(ph, band=(4, 6), skirt=(0, 3)):
    return {"band": (band[0], band[1], ph), "skirt": (skirt[0], skirt[1], ph * 1.3)}


def anims():
    A = {}
    guard = dict(la=(0, 0, 0, "rest"), ra=(0, 0, 0, "rest"))
    # stance: a fighting bounce, fists riding the torso, the headband tails and skirt moving on the air
    b = [0, 1, 2, 2, 1, 0]
    A["stance"] = [P(root=(0, b[i]), lean=b[i] * 0.8, la=(0, [0, 0, 1, 1, 0, 0][i], 0, "rest"),
                     cloth=cloth(i * math.pi / 3, band=(5 + b[i], 5), skirt=(0, 2))) for i in range(6)]
    # walk forward: each foot planted 5 frames sliding back under the body, lifted 3 frames stepping forward
    LX = [2, 1, 0, -1, -2, -0.5, 1, 2]
    LY = [0, 0, 0, 0, 0, -2, -3, -1]
    walk = []
    for i in range(8):
        j = (i + 4) % 8
        walk.append(P(root=(0, [1, 0, 0, 0, 1, 0, 0, 0][i]), lean=3, ll=(LX[i], LY[i], 0, "abs"),
                      rl=(LX[j], LY[j], 0, "abs"), cloth=cloth(i * math.pi / 4, band=(7, 5), skirt=(3, 3))))
    A["walk"] = walk
    # jab: a snap with the lead hand, a small step in
    A["jab"] = [
        P(root=(0, 0), lean=-2, la=(-2, 0, 0, "rest"), cloth=cloth(0)),
        P(root=(2, 0), lean=6, la=(17, -1, 0, "root"), ll=(1, 0, 0, "abs"), cloth=cloth(0.6, band=(8, 4))),
        P(root=(3, 0), lean=7, la=(17, -1, 0, "root"), ll=(1, 0, 0, "abs"), cloth=cloth(1.2, band=(9, 4))),
        P(root=(1, 0), lean=2, la=(2, -1, 0, "rest"), ll=(1, 0, 0, "abs"), cloth=cloth(1.8)),
    ]
    # cross: the rear fist drives straight through past the lead hand, hips turning in, the lead fist back to the chin
    A["cross"] = [
        P(root=(-1, 0), lean=-3, ra=(-2, 1, 0, "rest"), cloth=cloth(0)),
        P(root=(6, 1), lean=20, ra=(19, 5, 0, "root"), la=(-7, -3, 0, "rest"), rl=(3, 0, 0, "abs"), spin=(7, (74, 88)), cloth=cloth(0.7, band=(10, 4))),
        P(root=(7, 1), lean=21, ra=(19, 5, 0, "root"), la=(-7, -3, 0, "rest"), rl=(3, 0, 0, "abs"), spin=(8, (74, 88)), cloth=cloth(1.4, band=(11, 4))),
        P(root=(2, 0), lean=5, ra=(1, 0, 0, "rest"), rl=(1, 0, 0, "abs"), cloth=cloth(2.1)),
    ]
    # roundhouse (lead leg, head height): weight back, chamber, then the whole body tips back about the planted rear
    # foot so the straight kicking leg rises to head height; hold; re-chamber; land
    arms_up = dict(la=(-3, -2, 0, "rest"), ra=(-1, -2, 0, "rest"))
    PIV = (50, 88)                                        # the planted rear foot on the canvas
    A["roundhouse"] = [
        P(root=(-2, 0), lean=-6, **arms_up, cloth=cloth(0)),
        P(root=(-2, -1), lean=-12, ll=(7, 3, -20, "root"), **arms_up, spin=(-8, PIV), cloth=cloth(0.6, band=(8, 5))),
        P(root=(-3, -1), lean=-14, ll=(12, -3, -75, "root"), la=(-3, -2, 0, "rest"), ra=(-7, 0, 0, "rest"), spin=(-24, PIV), cloth=cloth(1.2, band=(12, 5), skirt=(-8, 3))),
        P(root=(-3, -1), lean=-15, ll=(12, -3, -75, "root"), la=(-3, -2, 0, "rest"), ra=(-7, 0, 0, "rest"), spin=(-26, PIV), cloth=cloth(1.8, band=(12, 5), skirt=(-8, 3))),
        P(root=(-2, -1), lean=-12, ll=(7, 3, -20, "root"), **arms_up, spin=(-8, PIV), cloth=cloth(2.4, band=(9, 5))),
        P(root=(-1, 0), lean=-4, ll=(2, 0, 0, "abs"), cloth=cloth(3.0)),
    ]
    # sweep: drop right down, a hand to the floor, the lead leg scything flat along the ground
    A["sweep"] = [
        P(root=(0, 5), lean=12, la=(0, 3, 0, "rest"), cloth=cloth(0)),
        P(root=(-3, 11), lean=26, ll=(16, 0, 10, "root"), la=(4, 11, 0, "rest"), ra=(-5, 3, 0, "rest"), cloth=cloth(0.8, band=(12, 4), skirt=(8, 2))),
        P(root=(-3, 11), lean=27, ll=(16, 0, 15, "root"), la=(4, 11, 0, "rest"), ra=(-6, 3, 0, "rest"), cloth=cloth(1.6, band=(14, 4), skirt=(8, 2))),
        P(root=(-3, 11), lean=26, ll=(16, 0, 10, "root"), la=(4, 11, 0, "rest"), ra=(-5, 3, 0, "rest"), cloth=cloth(2.4, band=(12, 4), skirt=(8, 2))),
        P(root=(0, 5), lean=10, ll=(2, 0, 0, "abs"), cloth=cloth(3.2)),
    ]
    # jump: crouch, take off (legs long, toes down), tuck, open for the descent, land
    A["jump"] = [
        P(root=(0, 5), lean=6, la=(0, 2, 0, "rest"), ra=(0, 2, 0, "rest"), cloth=cloth(0)),
        P(root=(0, -2), lean=-4, ll=(2, 12, 25, "root"), rl=(-4, 12, 25, "root"), la=(0, -2, 0, "rest"), cloth=cloth(0.7, band=(-6, 4), skirt=(0, 3))),
        P(root=(0, -3), ll=(6, 5, 10, "root"), rl=(-2, 6, 10, "root"), la=(0, -2, 0, "rest"), cloth=cloth(1.4, band=(2, 5), skirt=(0, 4))),
        P(root=(0, -2), ll=(3, 9, 15, "root"), rl=(-4, 9, 15, "root"), cloth=cloth(2.1, band=(10, 5), skirt=(0, 4))),
        P(root=(0, 4), lean=5, la=(0, 1, 0, "rest"), cloth=cloth(2.8)),
    ]
    # flying kick: airborne, lead leg driven diagonally down-forward, rear leg tucked, arms back for balance
    A["flykick"] = [P(root=(0, -2), lean=-10 - k, ll=(13 + k * 0.5, 6, -30, "root"), rl=(-4, 5, 10, "root"),
                      la=(-4, -2, 0, "rest"), ra=(-6, -1, 0, "rest"), cloth=cloth(k * 0.7, band=(14, 4), skirt=(-10, 3)))
                    for k in range(3)]
    # uppercut (lead hand): sink with the fist low, then drive it up in front of the face onto the toes, hold, settle
    A["uppercut"] = [
        P(root=(0, 7), lean=14, la=(0, 6, 0, "rest"), ra=(-1, -1, 0, "rest"), cloth=cloth(0)),
        P(root=(2, 2), lean=4, la=(12, 2, 0, "root"), ra=(-2, -2, 0, "rest"), cloth=cloth(0.6, band=(-4, 4))),
        P(root=(3, -4), lean=-6, la=(12, -12, 0, "root"), ra=(-3, 0, 0, "rest"), rl=(0, -1, 20, "abs"), cloth=cloth(1.2, band=(-10, 5), skirt=(0, 4))),
        P(root=(3, -5), lean=-8, la=(11, -13, 0, "root"), ra=(-3, 0, 0, "rest"), rl=(0, -1, 20, "abs"), cloth=cloth(1.8, band=(-12, 5), skirt=(0, 4))),
        P(root=(0, 1), lean=0, cloth=cloth(2.4)),
    ]
    # Sun Palm: gather both hands at the rear hip, thrust both palms forward, hold while the fire leaves, recover
    A["sunpalm"] = [
        P(root=(-2, 1), lean=-10, la=(-7, 10, 0, "root"), ra=(-5, 9, 0, "root"), cloth=cloth(0, band=(3, 5))),
        P(root=(-3, 2), lean=-12, la=(-7, 10, 0, "root"), ra=(-5, 9, 0, "root"), cloth=cloth(0.6, band=(3, 5))),
        P(root=(3, 1), lean=10, la=(17, 3, 0, "root"), ra=(17, 5, 0, "root"), ll=(2, 0, 0, "abs"), cloth=cloth(1.2, band=(12, 4))),
        P(root=(4, 1), lean=11, la=(17, 3, 0, "root"), ra=(17, 5, 0, "root"), ll=(2, 0, 0, "abs"), cloth=cloth(1.8, band=(13, 4))),
        P(root=(3, 1), lean=9, la=(16, 3, 0, "root"), ra=(16, 5, 0, "root"), ll=(2, 0, 0, "abs"), cloth=cloth(2.4, band=(11, 4))),
        P(root=(1, 0), lean=2, ll=(1, 0, 0, "abs"), cloth=cloth(3.0)),
    ]
    # block: forearms up in front of the face; the second frame is the push of a blocked hit
    A["block"] = [P(root=(-1 - 2 * k, 1), lean=-6, la=(-2, -8, 0, "rest"), ra=(8, -8, 0, "rest"), cloth=cloth(k, band=(6, 4)))
                  for k in range(2)]
    # hit: the head snaps back, the body folds away from the blow, then recovers
    A["hit"] = [
        P(root=(-3, 0), lean=-18, head=(-1, 0, -10), la=(-4, -3, 0, "rest"), ra=(-4, -4, 0, "rest"), cloth=cloth(0, band=(14, 3))),
        P(root=(-3, 0), lean=-12, head=(-1, 0, -6), la=(-3, -2, 0, "rest"), ra=(-3, -2, 0, "rest"), cloth=cloth(0.8, band=(10, 3))),
        P(root=(-1, 0), lean=-5, head=(0, 0, -2), cloth=cloth(1.6)),
    ]
    # knockdown: launched back, turning in the air, slammed flat on the floor, a bounce, lying still.
    # Lying frames rest their lowest pixel on the ground line; arms lie along the body.
    G = 89
    air_legs = dict(ll=(5, 10, 10, "root"), rl=(0, 11, 10, "root"))
    flat = dict(ll=(-9, 10, 0, "root"), rl=(-2, 12, 0, "root"), la=(2, 12, 0, "root"), ra=(1, 12, 0, "root"))
    A["knockdown"] = [
        P(root=(0, 0), lean=-10, spin=-30, **air_legs, la=(-5, -4, 0, "rest"), ra=(-6, -5, 0, "rest"), cloth=cloth(0, band=(16, 3))),
        P(root=(0, 4), lean=-6, spin=-60, **air_legs, la=(-5, -6, 0, "rest"), ra=(-6, -6, 0, "rest"), cloth=cloth(0.7, band=(20, 3))),
        P(spin=-85, ll=(1, 12, 0, "root"), rl=(-2, 12, 0, "root"), la=(-4, -6, 0, "rest"), ra=(-5, -6, 0, "rest"), ground=G - 1, cloth=cloth(1.4, band=(22, 3))),
        P(spin=-90, **flat, ground=G, cloth=cloth(2.1, band=(10, 2))),
        P(spin=-84, **flat, ground=G - 3, cloth=cloth(2.8, band=(12, 2))),
        P(spin=-90, **flat, ground=G, cloth=cloth(3.5, band=(8, 1))),
    ]
    # get up: from flat, sit up (the seat on the floor), rise through a crouch into the stance
    A["getup"] = [
        A["knockdown"][-1],
        P(spin=-45, ll=(8, 6, 0, "root"), rl=(4, 8, 0, "root"), la=(2, 5, 0, "rest"), ra=(-4, 6, 0, "rest"), ground=G, cloth=cloth(0.7, band=(8, 3))),
        P(root=(0, 6), spin=-10, lean=8, la=(0, 3, 0, "rest"), cloth=cloth(1.4, band=(6, 4))),
        P(root=(0, 1), lean=2, cloth=cloth(2.1)),
    ]
    # launched by an uppercut: turning back in the air, limbs thrown loose
    A["launch"] = [P(root=(0, -2), lean=-12, spin=-20 * (k + 1), ll=(4 + k, 10, 10, "root"), rl=(-1, 11, 10, "root"),
                     la=(-5, -5 - k, 0, "rest"), ra=(-6, -6 - k, 0, "rest"), head=(0, 0, -8), cloth=cloth(k * 0.7, band=(16, 3)))
                   for k in range(3)]
    # victory: settle, then the lead fist raised high at his front side, the other hand on the hip, chin up
    A["victory"] = [P(root=(0, 1), cloth=cloth(0))] + \
        [P(root=(0, -1), lean=-5, la=(12, -11, 0, "root"), ra=(-3, 5, 0, "rest"), head=(0, -1, -6),
           cloth=cloth(0.7 * k, band=(8, 6))) for k in range(1, 6)]
    return A


def build_frames(out_dir=None):
    out_dir = out_dir or (K.OUT / "sprites" / "riku")
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
