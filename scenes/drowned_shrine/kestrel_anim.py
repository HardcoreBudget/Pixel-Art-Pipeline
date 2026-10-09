"""Kestrel, animated frame by frame. Every frame is drawn fresh from a pose:

- head, scarf wrap and tunic are the Krea design's own pixels, moved (and turned with RotSprite when she leans);
- the cloak and the scarf's tail are the design's pixels too, bent per frame by whole-pixel row/column shifts
  (a shear that grows with distance from the shoulder), so they flutter without losing their shading;
- legs, arms and the sword are redrawn every frame from joints (two-bone IK for knees and elbows), shaded in the
  design's own ramps, then one ink line goes round the whole silhouette.

The canvas is 96 x 80 (the design's 64 x 64 at offset (16, 16)) so a raised sword never clips. Feet at (48, 76)."""
import math
import sys
import json

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
from agentdraw.core import rotsprite
from px import C, OUT

W, H = 96, 80
OX, OY = 16, 16
SPR = OUT / "sprites" / "kestrel"
L0 = {k: np.pad(v, ((OY, H - 64 - OY), (OX, W - 64 - OX), (0, 0))) for k, v in np.load(OUT / "kestrel_layers.npz").items()}

HIP = (48.0, 59.0)                 # pelvis centre at rest
NECK = (53.0, 39.0)
SHO_F, SHO_B = (55.0, 44.0), (50.0, 43.0)
FOOT_F, FOOT_B = (57.0, 72.0), (37.0, 72.0)      # ankles at rest
GRIP = (61.0, 51.0)
SWORD = -63.0

R = lambda *names: [C[n] for n in names]
PANTS = R("ink", "wood1", "wood2", "wood3")
BOOTS = R("ink", "wood0", "wood1", "wood2")
GLOVE = R("ink", "wood1", "wood2", "wood3")


# ---------------------------------------------------------------- drawing primitives (96 x 80)

def capsule(p0, p1, r0, r1):
    yy, xx = np.mgrid[0:H, 0:W]
    px, py = xx + 0.5, yy + 0.5
    (ax, ay), (bx, by) = p0, p1
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0, 1) if L2 > 0 else np.zeros_like(px)
    r = r0 + (r1 - r0) * t
    return (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2 <= r * r


def shade(mask, rmp, light=(-0.6, -0.8)):
    out = np.zeros((H, W, 4), np.uint8)
    if not mask.any():
        return out
    inner = ndimage.binary_erosion(mask, structure=np.ones((3, 3)))
    d = ndimage.distance_transform_edt(mask)
    gy, gx = np.gradient(d)
    n = np.sqrt(gx * gx + gy * gy) + 1e-6
    facing = (-gx * light[0] - gy * light[1]) / n
    k = len(rmp) - 1
    level = 0.5 + 0.45 * facing
    idx = np.clip(1 + np.floor(level * (k - 0.001)).astype(int), 1, k)
    cols = np.stack(rmp)
    out[inner] = cols[idx[inner]]
    out[mask & ~inner] = rmp[1]
    return out


def over(dst, src):
    m = src[..., 3] > 0
    dst[m] = src[m]
    return dst


def shift(img, dx, dy):
    dx, dy = int(round(dx)), int(round(dy))
    out = np.zeros_like(img)
    ys, xs = np.nonzero(img[..., 3] > 0)
    ny, nx = ys + dy, xs + dx
    ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
    out[ny[ok], nx[ok]] = img[ys[ok], xs[ok]]
    return out


def turn(img, deg, pivot):
    if abs(deg) < 0.5:
        return img.copy()
    return rotsprite(img, deg, pivot)


def rot(p, deg, pivot):
    a = math.radians(deg)
    x, y = p[0] - pivot[0], p[1] - pivot[1]
    return (pivot[0] + x * math.cos(a) - y * math.sin(a), pivot[1] + x * math.sin(a) + y * math.cos(a))


def ik(root, end, a, b, bend=1):
    rx, ry = root; ex, ey = end
    dx, dy = ex - rx, ey - ry
    d = min(math.hypot(dx, dy), a + b - 1e-3)
    ang = math.atan2(dy, dx)
    k = math.acos(max(-1, min(1, (a * a + d * d - b * b) / (2 * a * d))))
    return (rx + a * math.cos(ang - bend * k), ry + a * math.sin(ang - bend * k))


# ---------------------------------------------------------------- parts

import kestrel as KL
J = {k: (v[0] + OX, v[1] + OY) for k, v in KL.JOINTS.items()}


def move(img, deg, pivot, new):
    """Turn img about pivot (+ clockwise) and carry the pivot to new."""
    dx, dy = new[0] - pivot[0], new[1] - pivot[1]
    if abs(deg) < 0.5:
        return shift(img, dx, dy)
    return rotsprite(img, deg, pivot, dx, dy)


def bone(name, a0, b0, a1, b1):
    """Place a design segment whose rest bone runs a0 -> b0 so that it runs a1 -> b1."""
    ang = math.degrees(math.atan2(b1[1] - a1[1], b1[0] - a1[0]) - math.atan2(b0[1] - a0[1], b0[0] - a0[0]))
    ang = (ang + 180) % 360 - 180
    return move(L0[name], ang, a0, a1)


def knee_for(hip, ankle, side):
    """Two-bone IK with the design's own bone lengths; the knee bends to the same side as in the design.
    An ankle out of reach is pulled in along the leg (the leg straightens)."""
    hr, kr, ar = J[side + "_hip"], J[side + "_knee"], J[side + "_ankle"]
    a = math.dist(hr, kr); b = math.dist(kr, ar)
    dx, dy = ankle[0] - hip[0], ankle[1] - hip[1]
    d = math.hypot(dx, dy)
    if d > a + b - 0.05:
        k = (a + b - 0.05) / d
        ankle = (hip[0] + dx * k, hip[1] + dy * k)
    rest_side = (ar[0] - hr[0]) * (kr[1] - hr[1]) - (ar[1] - hr[1]) * (kr[0] - hr[0])
    for bend in (1, -1):
        kn = ik(hip, ankle, a, b, bend)
        sd = (ankle[0] - hip[0]) * (kn[1] - hip[1]) - (ankle[1] - hip[1]) * (kn[0] - hip[0])
        if sd * rest_side >= 0:
            return kn, ankle
    return kn, ankle


def leg(side, hip_n, foot, root, plant, pieces=None, rel=False, dark=False):
    """foot = (dx, dy, boot_deg): planted feet move from the rest ankle on the ground; unplanted feet move with the
    hip; rel=True gives the ankle directly relative to the hip. pieces: whose design segments to draw (the run
    uses the near leg's for both, the far one a ramp step darker)."""
    pc = pieces or side
    hr, kr, ar = J[pc + "_hip"], J[pc + "_knee"], J[pc + "_ankle"]
    fx, fy, bdeg = foot
    if rel:
        target = (hip_n[0] + fx, hip_n[1] + fy)
    elif plant:
        target = (ar[0] + fx, ar[1] + fy)
    else:
        target = (hip_n[0] + ar[0] - hr[0] + fx, hip_n[1] + ar[1] - hr[1] + fy)
    kn, an = knee_for(hip_n, target, pc)
    out = {side + "_thigh": bone(pc + "_thigh", hr, kr, hip_n, kn),
           side + "_shin": bone(pc + "_shin", kr, ar, kn, an),
           side + "_boot": move(L0[pc + "_boot"], bdeg, ar, an)}
    if dark:
        from px import ramp_step
        out = {k: ramp_step(v, -1) for k, v in out.items()}
    return out


def capsule_part(p0, p1, r0, r1, rmp):
    m = capsule(p0, p1, r0, r1)
    img = shade(m, rmp)
    ring = m & ~ndimage.binary_erosion(m, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
    img[ring] = C["ink"]
    return img


def sword(grip, deg, glow=0, length=22):
    """The sword drawn at any angle: grip, cross-guard, a 3-px blade (lit edge / flat / shaded edge), point.
    glow > 0 turns the blade to sunlight (Dawn Cleave)."""
    img = np.zeros((H, W, 4), np.uint8)
    a = math.radians(deg)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux                                      # the blade's side normal
    gx, gy = grip
    guard = (gx + ux * 3, gy + uy * 3)
    tip = (guard[0] + ux * length, guard[1] + uy * length)
    yy, xx = np.mgrid[0:H, 0:W]
    px, py = xx + 0.5, yy + 0.5
    t = (px - guard[0]) * ux + (py - guard[1]) * uy
    s = (px - guard[0]) * nx + (py - guard[1]) * ny
    half = np.where(t < length - 5, 2.1, 2.1 * np.clip((length - t) / 5, 0, 1))
    blade = (t >= 0.5) & (t <= length) & (np.abs(s) <= half + 0.01)
    ring = blade & ~ndimage.binary_erosion(blade, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
    lit = (nx * -0.6 + ny * -0.8) > 0                     # which side faces the light
    if glow:
        cols = ("fire6", "fire5", "fire4", "fire3")
    else:
        cols = ("silver3", "silver2", "silver1", "ink")
    side = s > 0 if lit else s < 0
    img[blade] = C[cols[1]]
    img[blade & side & (np.abs(s) > 0.5)] = C[cols[0]]
    img[blade & ~side & (np.abs(s) > 0.7)] = C[cols[2]]
    img[ring] = C[cols[3]]
    # grip (behind the guard) and pommel
    g = capsule((gx - ux * 2.5, gy - uy * 2.5), guard, 1.3, 1.3)
    img[g & (img[..., 3] == 0)] = C["wood1"]
    img[capsule((gx - ux * 3.5, gy - uy * 3.5), (gx - ux * 3.5, gy - uy * 3.5), 1.2, 1.2) & (img[..., 3] == 0)] = C["gold2"]
    # cross-guard: a bar across the blade
    gb = capsule((guard[0] - nx * 3.5, guard[1] - ny * 3.5), (guard[0] + nx * 3.5, guard[1] + ny * 3.5), 1.1, 1.1)
    img[gb] = C["stone2"]
    img[gb & ~ndimage.binary_erosion(gb)] = C["ink"]
    if glow:
        rng = np.random.default_rng(int(glow * 7))
        for k in range(6):
            u = rng.uniform(0.2, 1.0) * length
            x, y = guard[0] + ux * u + nx * rng.uniform(-4, 4), guard[1] + uy * u + ny * rng.uniform(-4, 4)
            if 0 <= int(x) < W and 0 <= int(y) < H and img[int(y), int(x), 3] == 0:
                img[int(y), int(x)] = C["fire5" if k % 2 else "fire6"]
    return img, tip


def twist(img, anchor, reach, bend, wave=0.0, phase=0.0, k=0.35):
    """Bend a hanging cloth about its anchor: every output pixel samples the source rotated back by an angle that
    grows with its distance r from the anchor (bend degrees at r >= reach, eased), plus a travelling ripple
    (wave degrees). Sampled from a 3x Scale2x (8x) copy, like RotSprite, and mapped output -> source, so the cloth
    can never tear: every output pixel takes some source pixel."""
    from agentdraw.core import scale2x
    big = scale2x(scale2x(scale2x(img)))
    yy, xx = np.mgrid[0:H, 0:W]
    px, py = xx + 0.5 - anchor[0], yy + 0.5 - anchor[1]
    r = np.sqrt(px * px + py * py)
    u = np.clip(r / reach, 0, 1)
    ang = np.radians(bend * u ** 1.4 + wave * np.sin(phase - r * k) * u)
    ca, sa = np.cos(ang), np.sin(ang)
    sx = (ca * px + sa * py + anchor[0]) * 8
    sy = (-sa * px + ca * py + anchor[1]) * 8
    sx = np.floor(sx).astype(int); sy = np.floor(sy).astype(int)
    ok = (sx >= 0) & (sx < W * 8) & (sy >= 0) & (sy < H * 8)
    out = np.zeros_like(img)
    out[ok] = big[sy[ok], sx[ok]]
    return out


CLOAK_ANCHOR = (50.0, 42.0)     # where the cloak hangs from the shoulders
SCARF_ANCHOR = (44.0, 41.0)     # where the scarf's tail leaves the neck


def cloak(dx, dy, blow, phase, flap=1.0, lift=0.0):
    """The design's cloak swung back (blow: + streams it back and up, as when running) and rippling (flap)."""
    bend = 7.0 * blow + 5.0 * lift
    return shift(twist(L0["cloak"], CLOAK_ANCHOR, 30, bend, 4.0 * flap, phase), dx, dy)


def scarf(dx, dy, amp, phase, lift=0.0, stretch=0.0):
    """The design's scarf tail, waving (amp) and lifting (lift: + raises the tail)."""
    bend = 6.0 * lift + 3.0 * stretch
    return shift(twist(L0["scarf_tail"], SCARF_ANCHOR, 34, bend, 3.0 * amp, phase, 0.3), dx, dy)


# ---------------------------------------------------------------- a frame

HIP = (48.0, 59.0)            # the lean pivot (pelvis centre)
REST = dict(root=(0, 0), lean=0.0, head=(0, 0, 0.0), ff=(0, 0, 0), bf=(0, 0, 0), plant=True,
            arm=(0, 0, 0), sword=SWORD, glow=0, cloak=(1.0, 0.0, 1.0, 0.0), scarf=(1.5, 0.0, 0.0, 0.0),
            sword_behind=False, arms_under_head=False)


def P(**kw):
    p = dict(REST); p.update(kw); return p


PAS_ORDER = ["cloak", "scarf_tail", "sword_back", "b_shin", "b_boot", "b_thigh", "f_shin", "f_boot", "f_thigh",
             "upper_arm", "torso", "sword_under", "arms_under", "wrap", "head", "sword", "arms", "line"]


def frame(p, named=False):
    """Draw one frame from pose p. Returns (image, sword tip), or with named=True the layers by PAS_ORDER name."""
    rx, ry = p["root"]
    lean = p["lean"]
    pivot = (HIP[0] + rx, HIP[1] + ry)
    body = lambda q: rot((q[0] + rx, q[1] + ry), lean, pivot)
    L = {}
    blow, ph, flap, lift = p["cloak"]
    L["cloak"] = turn(cloak(rx, ry, blow, ph, flap, lift), lean * 0.6, pivot)
    amp, sph, slift, sst = p["scarf"]
    L["scarf_tail"] = turn(scarf(rx, ry, amp, sph, slift, sst), lean * 0.6, pivot)
    if p.get("stride"):
        near, far = p["stride"]
        fh = J["f_hip"]
        L.update(leg("b", body((fh[0] - 3, fh[1] + 0.5)), far, (rx, ry), False, pieces="f", rel=True, dark=True))
        L.update(leg("f", body(fh), near, (rx, ry), False, pieces="f", rel=True))
    else:
        L.update(leg("b", body(J["b_hip"]), p["bf"], (rx, ry), p["plant"]))
        L.update(leg("f", body(J["f_hip"]), p["ff"], (rx, ry), p["plant"]))
    L["torso"] = turn(shift(L0["torso"], rx, ry), lean, pivot)
    neck = body(NECK)
    hdx, hdy, hrot = p["head"]
    L["wrap"] = turn(shift(L0["wrap"], rx, ry), lean, pivot)
    head = shift(L0["head"], neck[0] - NECK[0] + hdx, neck[1] - NECK[1] + hdy)
    L["head"] = turn(head, lean * 0.5 + hrot, (neck[0] + hdx, neck[1] + hdy))
    # the arms: the design's forearms and gloves, turned about their root; the root may slide toward the shoulder
    # (a raised swing), and then an outlined upper arm joins them under the tunic
    adeg, rdx, rdy = p["arm"]
    root_r, hands_r = J["arm_root"], J["hands"]
    root_n = body((root_r[0] + rdx, root_r[1] + rdy))
    arms = move(L0["arms"], adeg + lean, root_r, root_n)
    t = math.radians(adeg + lean)
    hx_, hy_ = hands_r[0] - root_r[0], hands_r[1] - root_r[1]
    grip = (root_n[0] + hx_ * math.cos(t) - hy_ * math.sin(t), root_n[1] + hx_ * math.sin(t) + hy_ * math.cos(t))
    if rdx or rdy:
        L["upper_arm"] = capsule_part(body(J["shoulder"]), root_n, 2.6, 2.4, GLOVE)
    sw, tip = sword(grip, p["sword"], p["glow"])
    if p["sword_behind"]:
        L["sword_back"] = sw
    elif p["arms_under_head"]:
        L["sword_under"] = sw
    else:
        L["sword"] = sw
    L["arms_under" if p["arms_under_head"] else "arms"] = arms
    img = np.zeros((H, W, 4), np.uint8)
    for n in PAS_ORDER:
        if n in L:
            over(img, L[n])
    a = img[..., 3] > 0
    ring = ndimage.binary_dilation(a, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])) & ~a
    line = np.zeros((H, W, 4), np.uint8); line[ring] = C["ink"]
    L["line"] = line
    img[ring] = C["ink"]
    if named:
        blank = np.zeros((H, W, 4), np.uint8)
        return img, {n: L.get(n, blank) for n in PAS_ORDER}
    return img, tip


# ---------------------------------------------------------------- animations

def anims():
    A = {}
    b = [0, 0, 1, 1, 1, 0]
    A["idle"] = [P(root=(0, b[i]), arm=(b[i] * 2, 0, 0), sword=SWORD + b[i] * 2, head=(0, [0, 0, 0, 1, 1, 0][i], 0),
                   cloak=(1.0, i * math.pi / 3, 1.0, 0), scarf=(1.8, i * math.pi / 3, 0, 0)) for i in range(6)]
    # run: a classic 8-frame stride. Near leg, ankle relative to the hip (x forward, y down) and boot tilt:
    # contact (heel reaching, toe up), down (weight lands), passing, push-off (toe down), heel kick behind,
    # tuck, knee up, reach. The far leg is the same four frames later. The body is lowest just after contact.
    STRIDE = [(9.0, 8.8, -15), (4.5, 10.5, -5), (-1.5, 11.5, 0), (-8.0, 9.2, 28),
              (-9.0, 3.5, 70), (-3.5, 2.5, 50), (4.0, 4.0, 15), (8.5, 6.5, -8)]
    BOB = [2, 3, 1, 0, 2, 3, 1, 0]
    run = []
    for i in range(8):
        ph = i / 8 * 2 * math.pi
        run.append(P(root=(2, BOB[i]), lean=14, stride=(STRIDE[i], STRIDE[(i + 4) % 8]),
                     arm=(28 + 3 * math.sin(2 * ph), 0, 0), sword=22 + 4 * math.sin(2 * ph),
                     cloak=(6.0 + 0.6 * math.sin(2 * ph), ph * 2, 1.2, 1.5), scarf=(2.5, ph * 2, 3.0, 1.0),
                     head=(1, 0, 0)))
    A["run"] = run
    # slash 1: wind up high behind, cut down through, follow through low, recover
    A["slash1"] = [
        P(root=(-1, 1), lean=-6, arm=(-55, 0, -6), sword=-130, ff=(1, 0, 0), bf=(-1, 0, 0), cloak=(1.5, 0.5, 1, 0), scarf=(2, 0.5, 0, 0), arms_under_head=True),
        P(root=(1, 1), lean=2, arm=(-30, 0, -4), sword=-55, ff=(3, 0, 0), bf=(0, 0, 0), cloak=(2.5, 1.0, 1, 1), scarf=(2.5, 1, 1, 0)),
        P(root=(3, 2), lean=10, arm=(20, 0, 0), sword=15, ff=(5, 0, 0), bf=(1, 0, 0), cloak=(3.5, 1.5, 1, 1), scarf=(3, 1.5, 1, 1)),
        P(root=(3, 2), lean=10, arm=(35, 0, 0), sword=55, ff=(5, 0, 0), bf=(1, 0, 0), cloak=(3.0, 2.0, 1, 0.5), scarf=(2.5, 2, 0, 1)),
        P(root=(2, 1), lean=6, arm=(20, 0, 0), sword=30, ff=(4, 0, 0), bf=(1, 0, 0), cloak=(2.0, 2.5, 1, 0), scarf=(2, 2.5, 0, 0)),
    ]
    # slash 2: from low behind, a rising cut to straight overhead (the timed hit)
    A["slash2"] = [
        P(root=(1, 2), lean=10, arm=(45, 0, 0), sword=150, ff=(4, 0, 0), bf=(0, 0, 0), cloak=(2, 3.0, 1, 0), scarf=(2, 3, 0, 0), sword_behind=True),
        P(root=(1, 3), lean=14, arm=(55, 0, 0), sword=175, ff=(4, 0, 0), bf=(0, 0, 0), cloak=(2, 3.4, 1, 0), scarf=(2, 3.4, 0, 0), sword_behind=True),
        P(root=(3, 0), lean=0, arm=(-25, 0, -3), sword=-40, ff=(5, 0, 0), bf=(2, 0, 0), cloak=(4, 3.8, 1.2, 2), scarf=(3, 3.8, 2, 1)),
        P(root=(3, -1), lean=-6, arm=(-32, 2, -6), sword=-68, ff=(5, 0, 0), bf=(2, -1, -10), cloak=(4, 4.2, 1.2, 3), scarf=(3, 4.2, 3, 1)),
        P(root=(2, 0), lean=-3, arm=(-28, 2, -6), sword=-62, ff=(4, 0, 0), bf=(1, 0, 0), cloak=(3, 4.6, 1, 1), scarf=(2.5, 4.6, 1, 0)),
    ]
    # hop back: crouch, tucked in the air, land
    A["hop"] = [
        P(root=(0, 3), lean=-6, arm=(-10, 0, 0), sword=-40, cloak=(1, 5, 1, 0), scarf=(1.5, 5, 0, 0)),
        P(root=(0, -2), lean=-12, plant=False, ff=(2, -3, 15), bf=(3, -2, 10), arm=(-15, 0, 0), sword=-50, cloak=(-3, 5.5, 1, -2), scarf=(2, 5.5, -3, 0)),
        P(root=(0, -2), lean=-10, plant=False, ff=(1, -1, 8), bf=(2, -1, 5), arm=(-15, 0, 0), sword=-55, cloak=(-2, 6, 1, -1), scarf=(2, 6, -2, 0)),
        P(root=(0, 2), lean=-4, arm=(-5, 0, 0), sword=-60, cloak=(1, 6.5, 1, 0), scarf=(1.5, 6.5, 0, 0)),
    ]
    # block: blade upright in front, the jolt of the bite, holding
    A["block"] = [
        P(root=(-1, 1), lean=-4, arm=(-30, 1, -3), sword=-96, cloak=(1, 0, 1, 0), scarf=(1.5, 0, 0, 0)),
        P(root=(-2, 2), lean=-9, arm=(-26, 1, -3), sword=-104, ff=(-1, 0, 0), bf=(-2, 0, 0), cloak=(-2, 0.5, 1.5, 1), scarf=(3, 0.5, 2, 0)),
        P(root=(-1, 1), lean=-6, arm=(-28, 1, -3), sword=-99, cloak=(0, 1, 1, 0), scarf=(2, 1, 1, 0)),
    ]
    # leap: crouch with the sword drawn back, spring, rising with the sword lifting, apex with the blade overhead
    A["leap"] = [
        P(root=(0, 4), lean=10, arm=(45, 0, 0), sword=160, cloak=(2, 0, 1, 0), scarf=(2, 0, 0, 0), sword_behind=True),
        P(root=(1, -3), lean=-6, plant=False, ff=(-1, 3, 25), bf=(2, 2, 25), arm=(20, 0, 0), sword=-150, glow=1, cloak=(1, 0.6, 1, -4), scarf=(2, 0.6, -4, 1), sword_behind=True),
        P(root=(1, -4), lean=-10, plant=False, ff=(2, -2, 10), bf=(3, -2, 10), arm=(-40, 1, -6), sword=-120, glow=2, cloak=(0, 1.2, 1, -3), scarf=(3, 1.2, -3, 1), arms_under_head=True),
        P(root=(1, -4), lean=-12, plant=False, ff=(3, -3, 5), bf=(4, -3, 5), arm=(-30, 3, -6), sword=-50, glow=3, cloak=(0, 1.8, 1.2, -1), scarf=(3, 1.8, -1, 1)),
    ]
    # plunge: the downward cleave; impact crouch with the blade driven down in front
    A["plunge"] = [
        P(root=(2, -3), lean=8, plant=False, ff=(3, -3, 10), bf=(4, -3, 10), arm=(-20, 0, -3), sword=-30, glow=4, cloak=(0, 2.4, 1.4, 4), scarf=(3, 2.4, 4, 1)),
        P(root=(3, 1), lean=18, arm=(55, 0, 0), sword=80, glow=5, ff=(4, 0, 0), bf=(0, 0, 0), cloak=(2, 3.0, 1.4, 5), scarf=(3, 3.0, 5, 1)),
        P(root=(3, 4), lean=16, arm=(60, 0, 0), sword=85, glow=6, ff=(4, 0, 0), bf=(0, 0, 0), cloak=(3, 3.6, 1, 2), scarf=(2.5, 3.6, 2, 0)),
    ]
    # victory: flick the sword out, twirl it through three angles, raise it high and hold
    vic = [P(root=(0, 1), arm=(10, 0, 0), sword=-20, cloak=(1, 0, 1, 0), scarf=(2, 0, 0, 0))]
    for k, ang in enumerate((60, 150, 240)):
        vic.append(P(root=(0, 0), arm=(15, 0, 0), sword=ang, cloak=(1.5, k, 1, 0), scarf=(2.5, k, 0, 0), sword_behind=90 < ang < 270))
    for k in range(2):
        vic.append(P(root=(0, -1), lean=-4, arm=(-34, 2, -6), sword=-72, head=(0, -1, -4), cloak=(2, 4 + 0.6 * k, 1.2, 1),
                     scarf=(3, 4 + 0.6 * k, 1, 1)))
    A["victory"] = vic
    return A


def main():
    SPR.mkdir(parents=True, exist_ok=True)
    for f in SPR.glob("*_*.png"):
        if f.stem.split("_")[-1].isdigit():
            f.unlink()
    A = anims()
    tips = {}
    rows = []
    for name, poses in A.items():
        imgs = []
        for i, p in enumerate(poses):
            img, tip = frame(p)
            Image.fromarray(img).save(SPR / f"{name}_{i}.png")
            tips[f"{name}_{i}"] = tip
            imgs.append(img)
        rows.append((name, imgs))
    (SPR / "tips.json").write_text(json.dumps(tips))
    # a review sheet: one row per animation at 3x
    n = max(len(r[1]) for r in rows)
    sheet = Image.new("RGBA", (n * W * 3, len(rows) * H * 3), (60, 64, 88, 255))
    for j, (_, imgs) in enumerate(rows):
        for i, img in enumerate(imgs):
            sheet.alpha_composite(Image.fromarray(img).resize((W * 3, H * 3), Image.NEAREST), (i * W * 3, j * H * 3))
    sheet.save(OUT / "kestrel_sheet.png")
    print({k: len(v) for k, v in A.items()})


if __name__ == "__main__":
    main()
