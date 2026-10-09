"""A reusable fighter rig built from design pixels (the lessons of the Drowned Shrine, generalised).

A character supplies:
  layers  - pieces cut from its 64-grid design (design coordinates), each complete where others hide it
  joints  - measured joint positions (design coordinates)
  SPEC    - which pieces form which limb, what the torso/head/pelvis/cloth are, the draw order

and poses. A pose is a dict (see Rig.frame). Every frame is assembled from the design's own pieces:
  - legs and arms: two-bone IK with the design's bone lengths, bending to the design's own side;
  - each piece turned about its joint with RotSprite (exact at multiples of 90 degrees);
  - cloth only through twist() (inverse warp, cannot tear);
  - one ink line around the silhouette on its own layer."""
import math
import sys
import pathlib

import numpy as np
from scipy import ndimage

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "drowned_shrine"))
sys.path.insert(0, str(HERE.parent))
from agentdraw.core import rotsprite, scale2x
from px import C, ramp_step


def shift(img, dx, dy):
    dx, dy = int(round(dx)), int(round(dy))
    out = np.zeros_like(img)
    ys, xs = np.nonzero(img[..., 3] > 0)
    ny, nx = ys + dy, xs + dx
    ok = (ny >= 0) & (ny < img.shape[0]) & (nx >= 0) & (nx < img.shape[1])
    out[ny[ok], nx[ok]] = img[ys[ok], xs[ok]]
    return out


def move(img, deg, pivot, new):
    """Turn img about pivot (+ clockwise on screen) and carry the pivot to new."""
    dx, dy = new[0] - pivot[0], new[1] - pivot[1]
    if abs(deg) < 0.5:
        return shift(img, dx, dy)
    return rotsprite(img, deg, pivot, dx, dy)


def rot(p, deg, pivot):
    a = math.radians(deg)
    x, y = p[0] - pivot[0], p[1] - pivot[1]
    return (pivot[0] + x * math.cos(a) - y * math.sin(a), pivot[1] + x * math.sin(a) + y * math.cos(a))


def angle(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def ik(root, end, a, b, bend):
    rx, ry = root; ex, ey = end
    d = min(math.hypot(ex - rx, ey - ry), a + b - 1e-3)
    ang = math.atan2(ey - ry, ex - rx)
    k = math.acos(max(-1, min(1, (a * a + d * d - b * b) / (2 * a * d))))
    return (rx + a * math.cos(ang - bend * k), ry + a * math.sin(ang - bend * k))


def twist(img, anchor, reach, bend, wave=0.0, phase=0.0, k=0.35):
    """Tear-free cloth: every output pixel samples the source rotated back about the anchor by an angle growing with
    distance (bend at >= reach) plus a travelling ripple, from an 8x Scale2x copy."""
    if abs(bend) < 0.3 and abs(wave) < 0.3:
        return img.copy()
    H, W = img.shape[:2]
    big = scale2x(scale2x(scale2x(img)))
    yy, xx = np.mgrid[0:H, 0:W]
    px, py = xx + 0.5 - anchor[0], yy + 0.5 - anchor[1]
    r = np.sqrt(px * px + py * py)
    u = np.clip(r / reach, 0, 1)
    a = np.radians(bend * u ** 1.4 + wave * np.sin(phase - r * k) * u)
    sx = np.floor((np.cos(a) * px + np.sin(a) * py + anchor[0]) * 8).astype(int)
    sy = np.floor((-np.sin(a) * px + np.cos(a) * py + anchor[1]) * 8).astype(int)
    ok = (sx >= 0) & (sx < W * 8) & (sy >= 0) & (sy < H * 8)
    out = np.zeros_like(img)
    out[ok] = big[sy[ok], sx[ok]]
    return out


class Rig:
    def __init__(self, layers, joints, spec, W=128, H=96, OX=32, OY=28):
        self.W, self.H, self.OX, self.OY = W, H, OX, OY
        pad = lambda a: np.pad(a, ((OY, H - a.shape[0] - OY), (OX, W - a.shape[1] - OX), (0, 0)))
        self.L0 = {k: pad(v) for k, v in layers.items()}
        self.J = {k: (v[0] + OX, v[1] + OY) for k, v in joints.items()}
        self.S = spec
        self.dark = {}

    # -------------------------------------------------------------- pieces
    def piece(self, name, dark=False):
        if not dark:
            return self.L0[name]
        if name not in self.dark:
            self.dark[name] = ramp_step(self.L0[name], -1)
        return self.dark[name]

    def bone(self, name, a0, b0, a1, b1, dark=False):
        d = (angle(a1, b1) - angle(a0, b0) + 180) % 360 - 180
        return move(self.piece(name, dark), d, a0, a1)

    def chain(self, limb, root_n, target, end_deg, pieces, joints, dark=False):
        """A two-bone limb: pieces = (upper, lower, end or None), joints = (root, mid, end) names in the pieces'
        own rest pose. The end is pulled in along the limb if out of reach."""
        up, lo, en = pieces
        r0, m0, e0 = (self.J[j] for j in joints)
        a, b = math.dist(r0, m0), math.dist(m0, e0)
        dx, dy = target[0] - root_n[0], target[1] - root_n[1]
        d = math.hypot(dx, dy)
        if d > a + b - 0.05:
            s = (a + b - 0.05) / d
            target = (root_n[0] + dx * s, root_n[1] + dy * s)
        side = (e0[0] - r0[0]) * (m0[1] - r0[1]) - (e0[1] - r0[1]) * (m0[0] - r0[0])
        mid = None
        for bend in (1, -1):
            mid = ik(root_n, target, a, b, bend)
            sd = (target[0] - root_n[0]) * (mid[1] - root_n[1]) - (target[1] - root_n[1]) * (mid[0] - root_n[0])
            if sd * side >= 0:
                break
        out = {up: self.bone(up, r0, m0, root_n, mid, dark), lo: self.bone(lo, m0, e0, mid, target, dark)}
        if en:
            out[en] = move(self.piece(en, dark), end_deg, e0, target)
        return out, mid, target

    # -------------------------------------------------------------- a frame
    def frame(self, pose, named=False):
        """pose keys (all optional):
          root (dx, dy)          pelvis offset
          lean deg               torso turn about the waist (+ = clockwise: forward for a right-facing fighter)
          head (dx, dy, deg)     head offset and turn about the neck
          <limb> (x, y, deg, mode)  for each limb in SPEC['limbs']: end target and end-piece turn;
                                 mode 'rest' = offset from the rest end carried by its root, 'root' = relative to
                                 the limb's root joint, 'abs' = offset from the rest end in canvas space (planted)
          cloth {name: (bend, wave, phase)}
          front [layer, ...]     layers moved to the top for this frame; back [layer, ...] moved to the bottom
          tint {layer: steps}    ramp steps (e.g. a flash)"""
        S, J = self.S, self.J
        rx, ry = pose.get("root", (0, 0))
        lean = pose.get("lean", 0.0)
        waist0 = J[S["waist"]]
        waist = (waist0[0] + rx, waist0[1] + ry)
        body = lambda q: rot((q[0] + rx, q[1] + ry), lean, waist)      # a point on the torso
        hips = lambda q: (q[0] + rx, q[1] + ry)                          # a point on the pelvis
        L = {}
        L[S["pelvis"]] = shift(self.L0[S["pelvis"]], rx, ry)
        L[S["torso"]] = move(self.L0[S["torso"]], lean, waist0, waist)
        neck0 = J[S["neck"]]
        neck = body(neck0)
        hdx, hdy, hdeg = pose.get("head", (0, 0, 0))
        L[S["head"]] = move(self.L0[S["head"]], lean * 0.6 + hdeg, neck0, (neck[0] + hdx, neck[1] + hdy))
        for name, lim in S["limbs"].items():
            root_j = lim["joints"][0]
            carrier = hips if lim.get("on") == "pelvis" else body
            root_n = carrier(J[root_j])
            x, y, deg, mode = pose.get(name, (0, 0, 0, "rest"))
            e0 = J[lim["joints"][2]]
            if mode == "root":
                target = (root_n[0] + x, root_n[1] + y)
            elif mode == "abs":
                target = (e0[0] + x, e0[1] + y)
            else:                                                        # 'rest': carried with its root
                r0 = J[root_j]
                target = (root_n[0] + e0[0] - r0[0] + x, root_n[1] + e0[1] - r0[1] + y)
            parts, mid, end = self.chain(name, root_n, target, deg + (lean if lim.get("on") != "pelvis" else 0),
                                         lim["pieces"], lim["joints"], lim.get("dark", False))
            for k, v in parts.items():
                L[lim.get("slots", {}).get(k, k)] = v
        for name, cl in S.get("cloth", {}).items():
            bend, wave, phase = pose.get("cloth", {}).get(name, (0, 0, 0))
            a0 = J[cl["anchor"]]
            src = twist(self.L0[name], a0, cl["reach"], bend, wave, phase, cl.get("k", 0.35))
            if cl.get("on") == "head":
                L[name] = move(src, lean * 0.6 + hdeg, neck0, (neck[0] + hdx, neck[1] + hdy))
            elif cl.get("on") == "pelvis":
                L[name] = shift(src, rx, ry)
            else:
                L[name] = move(src, lean, waist0, waist)
        for k, steps in pose.get("tint", {}).items():
            if k in L:
                L[k] = ramp_step(L[k], steps)
        if pose.get("spin"):
            # the whole fighter turned as one body (knockdowns, lying on the floor): pivot = (x, y) or the waist.
            # Turned piece by piece BEFORE assembly, so the outline and its pocket clean-up see the turned body.
            deg, pv = pose["spin"] if isinstance(pose["spin"], tuple) else (pose["spin"], waist)
            L = {k: rotsprite(v, deg, pv) for k, v in L.items()}
        order = [n for n in S["order"] if n not in pose.get("front", []) and n not in pose.get("back", [])]
        order = list(pose.get("back", [])) + order + list(pose.get("front", []))
        img = np.zeros((self.H, self.W, 4), np.uint8)
        for n in order:
            if n in L:
                m = L[n][..., 3] > 0
                img[m] = L[n][m]
        a = img[..., 3] > 0
        ring = ndimage.binary_dilation(a, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])) & ~a
        # the ring can strand 1-4 px pockets in narrow notches and creases: close them with ink (they read as outline)
        filled = ndimage.binary_fill_holes(a | ring) & ~(a | ring)
        lab, n = ndimage.label(filled)
        if n:
            sizes = ndimage.sum(filled, lab, range(1, n + 1))
            for i, sz in enumerate(sizes, 1):
                if sz <= 4:
                    ring |= lab == i
        line = np.zeros_like(img); line[ring] = C["ink"]
        img[ring] = C["ink"]
        if pose.get("ground"):
            # lying or sitting on the floor: the body's weight-bearing pieces (SPEC['support']: head, torso, pelvis,
            # legs - not dangling cloth or hands) rest their lowest pixel on the ground line; anything that would
            # reach below the floor is pressed flat against it (cut at the line)
            G = int(pose["ground"])
            sup = np.zeros(img.shape[:2], bool)
            for n in S.get("support", []):
                if n in L:
                    sup |= L[n][..., 3] > 0
            sup = ndimage.binary_dilation(sup, np.ones((3, 3), bool)) & (img[..., 3] > 0) if sup.any() else img[..., 3] > 0
            dy = G - int(np.nonzero(sup)[0].max())
            img, line = shift(img, 0, dy), shift(line, 0, dy)
            L = {k: shift(v, 0, dy) for k, v in L.items()}
            if G + 1 < img.shape[0]:
                # where the body continued below the floor, the cut would leave an open edge: close it with ink
                cut = (img[G, :, 3] > 0) & (img[G + 1, :, 3] > 0)
                img[G + 1:] = 0; line[G + 1:] = 0
                for v in L.values():
                    v[G + 1:] = 0
                img[G, cut] = C["ink"]; line[G, cut] = C["ink"]
        if pose.get("flash"):
            img = ramp_step(img, pose["flash"])
        if named:
            blank = np.zeros_like(img)
            return img, {n: L.get(n, blank) for n in S["order"]} | {"line": line}
        return img


def holes(img, base=None):
    """QA. Tears show as pinholes: enclosed transparent pockets of 1-4 px (bigger enclosed gaps are shapes, like the
    space inside a bent arm). Returns (pinholes, islands): islands counts every separate piece beyond the body."""
    a = img[..., 3] > 0
    enclosed = ndimage.binary_fill_holes(a) & ~a
    lab, n = ndimage.label(enclosed)
    sizes = ndimage.sum(enclosed, lab, range(1, n + 1))
    pin = int(sum(s for s in sizes if s <= 4))
    lab2, n2 = ndimage.label(a, structure=np.ones((3, 3)))
    return pin, n2 - 1          # (pinhole pixels, extra islands: anything not joined to the body floats)


def adopt_fragments(L, max_px=16, order=None):
    """Every piece must be one connected shape: a small fragment detached from its piece's main body goes to the
    piece it touches most (within 2 px), so no pixel is left hanging when limbs move apart."""
    moved = []
    for n in list(L):
        m = L[n][..., 3] > 0
        lab, k = ndimage.label(m, structure=np.ones((3, 3)))
        if k < 2:
            continue
        sizes = ndimage.sum(m, lab, range(1, k + 1))
        main = int(np.argmax(sizes)) + 1
        for i, s in enumerate(sizes, 1):
            if i == main or s > max_px:
                continue
            frag = lab == i
            ring = ndimage.binary_dilation(frag, np.ones((3, 3)), iterations=2) & ~frag
            best, bc = None, 0
            for o, v in L.items():
                if o != n:
                    c = int((ring & (v[..., 3] > 0)).sum())
                    if c > bc:
                        best, bc = o, c
            # a fragment pixel covered by a layer above its piece is leftover hidden fill: delete it; a visible one
            # moves to the neighbour (into empty pixels only), and hidden fill above the neighbour there is cleared
            above_n = order[order.index(n) + 1:] if order and n in order else []
            covered = np.zeros_like(frag)
            for o in above_n:
                if o in L:
                    covered |= L[o][..., 3] > 0
            vis = frag & ~covered
            L[n][frag & covered] = 0
            if best and vis.any():
                put_ = vis & (L[best][..., 3] == 0)
                L[best][put_] = L[n][put_]
                if order and best in order:
                    for o in order[order.index(best) + 1:]:
                        if o in L and o != n:
                            L[o][put_] = 0
            L[n][vis] = 0
            moved.append((n, best, int(s), int(vis.sum())))
    return moved
