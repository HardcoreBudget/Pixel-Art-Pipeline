"""agentdraw: pixel-level layer and animation authoring for Pixel Art Studio (the agent draws; no diffusion).

A character is a set of complete layers on one W x H canvas (default 64 x 64), each an RGBA uint8 array. The Krea
reference supplies the design and palette; the agent decides every pixel: which part it belongs to, and what is drawn
where another part hides it.

  from agentdraw.core import *
  ref = load_ref("knight")                 # 64 x 64 RGBA, feet on the bottom row minus a margin
  zoom(ref, "knight_zoom.png")             # 12x with a pixel grid and coordinates, for reading pixels
"""
import os
import pathlib

import numpy as np
from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
PIX = HERE.parent
# load_ref() reads <name>_px.png designs from $AGENTDRAW_REF (default: scenes/designs); the scenes do not use it.
REF = pathlib.Path(os.environ.get("AGENTDRAW_REF", PIX / "designs"))
OUT = pathlib.Path(os.environ.get("SCENES_OUT", PIX.parent / "out" / "scenes")) / "agentdraw"
W = H = 64


def load_ref(name, size=(W, H), floor=1):
    """The Krea sprite on a size canvas: centred, feet `floor` pixels above the bottom edge."""
    s = np.asarray(Image.open(REF / f"{name}_px.png").convert("RGBA")).copy()
    s[s[..., 3] < 128] = 0; s[s[..., 3] >= 128, 3] = 255
    ys, xs = np.nonzero(s[..., 3])
    s = s[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    c = np.zeros((size[1], size[0], 4), np.uint8)
    h, w = s.shape[:2]
    x0 = (size[0] - w) // 2; y0 = size[1] - floor - h
    c[y0:y0 + h, x0:x0 + w] = s
    return c


def blank(size=(W, H)):
    return np.zeros((size[1], size[0], 4), np.uint8)


def palette(*arrs):
    """Unique opaque colours of the arrays, darkest first."""
    cols = np.unique(np.concatenate([a[a[..., 3] > 0][:, :3] for a in arrs]), axis=0)
    return cols[np.argsort(cols.astype(int).sum(1))]


def rgba(hexstr):
    h = hexstr.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)] + [255], np.uint8)


def hexs(c):
    return "#%02X%02X%02X" % tuple(int(v) for v in c[:3])


# ---------------------------------------------------------------- viewing

def checker(w, h, s, a=(222, 226, 222), b=(246, 246, 246)):
    im = Image.new("RGBA", (w * s, h * s))
    d = ImageDraw.Draw(im)
    for y in range(h):
        for x in range(w):
            d.rectangle([x * s, y * s, x * s + s - 1, y * s + s - 1], fill=a if (x + y) % 2 else b)
    return im


def zoom(arr, path, s=12, crop=None, marks=None):
    """arr at s x with a pixel grid, a stronger line every 8 px and coordinates on the edges (for reading pixels).
    crop = (x0, y0, x1, y1) in pixels; marks = {(x, y): (r, g, b)} outlined cells."""
    x0, y0, x1, y1 = crop or (0, 0, arr.shape[1], arr.shape[0])
    a = arr[y0:y1, x0:x1]; h, w = a.shape[:2]
    pad = 22
    im = Image.new("RGBA", (w * s + pad, h * s + pad), (255, 255, 255, 255))
    base = checker(w, h, s); base.alpha_composite(Image.fromarray(a).resize((w * s, h * s), Image.NEAREST))
    im.paste(base, (pad, pad))
    d = ImageDraw.Draw(im)
    for x in range(w + 1):
        X = x0 + x
        d.line([pad + x * s, pad, pad + x * s, pad + h * s], fill=(90, 90, 90, 255) if X % 8 == 0 else (190, 190, 190, 255))
        if X % 4 == 0 and x < w:
            d.text((pad + x * s + 1, 2 + (10 if X % 8 else 0)), str(X), fill=(0, 0, 0, 255))
    for y in range(h + 1):
        Y = y0 + y
        d.line([pad, pad + y * s, pad + w * s, pad + y * s], fill=(90, 90, 90, 255) if Y % 8 == 0 else (190, 190, 190, 255))
        if Y % 2 == 0 and y < h:
            d.text((1, pad + y * s + 1), str(Y), fill=(0, 0, 0, 255))
    for (mx, my), col in (marks or {}).items():
        X, Y = pad + (mx - x0) * s, pad + (my - y0) * s
        d.rectangle([X, Y, X + s - 1, Y + s - 1], outline=tuple(col) + (255,), width=2)
    im.save(path)
    return path


def show_layers(layers, order, path, ref=None, s=5, title=""):
    """Every layer alone on a checkerboard (hidden pixels = what another layer covers in the stack, tinted in the
    'hidden' row), the stack, and the reference: the proof that each part is isolated and complete."""
    names = list(order)
    comp = composite(layers, names)
    covered = {}
    for i, n in enumerate(names):
        above = np.zeros(comp.shape[:2], bool)
        for m in names[i + 1:]:
            above |= layers[m][..., 3] > 0
        covered[n] = (layers[n][..., 3] > 0) & above
    tiles = [("stack", comp)] + ([("reference", ref)] if ref is not None else []) + [(n, layers[n]) for n in names]
    h, w = comp.shape[:2]
    cols = len(tiles); lab = 14
    im = Image.new("RGBA", (cols * (w * s + 6), 2 * (h * s + lab) + lab), (255, 255, 255, 255))
    d = ImageDraw.Draw(im)
    if title:
        d.text((4, 1), title, fill=(0, 0, 0, 255))
    for j, (n, a) in enumerate(tiles):
        X = j * (w * s + 6)
        t = checker(w, h, s); t.alpha_composite(Image.fromarray(a).resize((w * s, h * s), Image.NEAREST))
        im.paste(t, (X, lab + lab)); d.text((X + 2, lab + 1), n, fill=(0, 0, 0, 255))
        if n in covered:  # second row: the layer with its hidden pixels outlined in magenta
            hid = covered[n]
            t2 = checker(w, h, s); t2.alpha_composite(Image.fromarray(a).resize((w * s, h * s), Image.NEAREST))
            dd = ImageDraw.Draw(t2)
            for y, x in zip(*np.nonzero(hid)):
                dd.rectangle([x * s, y * s, x * s + s - 1, y * s + s - 1], outline=(255, 0, 200, 255))
            im.paste(t2, (X, 2 * lab + h * s + lab))
            d.text((X + 2, lab + h * s + lab + 1), f"{int(hid.sum())} hidden px", fill=(160, 0, 130, 255))
    im.save(path)
    return path


# ---------------------------------------------------------------- stacking

def composite(layers, order):
    out = blank((next(iter(layers.values())).shape[1], next(iter(layers.values())).shape[0]))
    for n in order:
        m = layers[n][..., 3] > 0
        out[m] = layers[n][m]
    return out


def diff(a, b):
    return int((np.abs(a.astype(int) - b.astype(int)).sum(-1) > 0).sum())


# ---------------------------------------------------------------- drawing primitives (all in place, pixel exact)

def poly_mask(points, shape=(H, W)):
    """Filled polygon (pixel centres inside or on the edge), points in pixel coordinates."""
    im = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(im).polygon([tuple(p) for p in points], fill=1, outline=1)
    return np.asarray(im).astype(bool)


def rect_mask(x0, y0, x1, y1, shape=(H, W)):
    m = np.zeros(shape, bool); m[y0:y1 + 1, x0:x1 + 1] = True
    return m


def take(src, mask):
    """A new layer holding src's pixels inside mask."""
    out = np.zeros_like(src); m = mask & (src[..., 3] > 0); out[m] = src[m]
    return out


def put(layer, x, y, colour):
    if 0 <= y < layer.shape[0] and 0 <= x < layer.shape[1]:
        layer[y, x] = colour if len(colour) == 4 else list(colour) + [255]


def rows(layer, x0, y0, art, key):
    """Paint a small ASCII drawing: art = list of strings, key = {char: colour}; ' ' and '.' leave pixels alone,
    '_' clears a pixel. The main way to draw hidden parts by hand."""
    for dy, line in enumerate(art):
        for dx, ch in enumerate(line):
            if ch in " .":
                continue
            if ch == "_":
                layer[y0 + dy, x0 + dx] = 0
            else:
                put(layer, x0 + dx, y0 + dy, key[ch])


def ascii_map(arr, crop=None, key=None):
    """Print pixels as characters (one per palette colour) with coordinates: reading the sprite as text."""
    x0, y0, x1, y1 = crop or (0, 0, arr.shape[1], arr.shape[0])
    cols = palette(arr) if key is None else None
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@$%&*+=?"
    lut = {tuple(c): chars[i] for i, c in enumerate(cols)} if key is None else key
    lines = ["    " + "".join(str((x // 10) % 10) for x in range(x0, x1)), "    " + "".join(str(x % 10) for x in range(x0, x1))]
    for y in range(y0, y1):
        lines.append(f"{y:3d} " + "".join(lut.get(tuple(arr[y, x, :3]), "?") if arr[y, x, 3] else "." for x in range(x0, x1)))
    return "\n".join(lines), lut


def ellipse_mask(cx, cy, rx, ry, shape=(H, W)):
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    return ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0


def assign(ref, parts):
    """Visible-pixel ownership: parts = [(name, mask), ...] in priority order (front-most first); the first mask
    containing a pixel owns it. Returns {name: layer} holding exactly the reference's pixels (a partition)."""
    owned = np.zeros(ref.shape[:2], bool); out = {}
    for name, m in parts:
        mm = m & ~owned & (ref[..., 3] > 0)
        out[name] = take(ref, mm); owned |= mm
    rest = (ref[..., 3] > 0) & ~owned
    return out, rest


def fill(layer, mask, colour, only_empty=True):
    """Paint colour into mask (by default only where the layer is empty: visible pixels stay exact)."""
    m = mask & ((layer[..., 3] == 0) if only_empty else True)
    layer[m] = colour if len(colour) == 4 else list(colour) + [255]


def outline(layer, colour, where=None):
    """Darken the outer edge of a layer's shape with colour (pixels of the layer that touch transparency)."""
    from scipy import ndimage
    a = layer[..., 3] > 0
    edge = a & ~ndimage.binary_erosion(a, structure=np.ones((3, 3)))
    if where is not None:
        edge &= where
    layer[edge] = colour if len(colour) == 4 else list(colour) + [255]


def overlay(ref, layers, order, path, s=10):
    """Ownership check: the reference tinted per layer (one colour per part) at s x, with the grid."""
    tints = [(230, 60, 60), (60, 160, 230), (240, 200, 40), (90, 200, 90), (200, 90, 220), (240, 140, 40),
             (40, 200, 200), (150, 110, 70), (120, 120, 250), (250, 120, 170), (160, 200, 80), (100, 100, 100)]
    a = ref.copy().astype(float)
    for i, n in enumerate(order):
        m = (layers[n][..., 3] > 0) & (ref[..., 3] > 0) & (np.abs(layers[n].astype(int) - ref.astype(int)).sum(-1) == 0)
        a[m, :3] = a[m, :3] * 0.45 + np.array(tints[i % len(tints)]) * 0.55
    zoom(a.astype(np.uint8), path, s=s)
    return {n: tints[i % len(tints)] for i, n in enumerate(order)}


def settle(layers, order, partition):
    """Keep every hand-drawn hidden pixel only where the stack really hides it: the pixel's visible owner (from the
    partition assign() made BEFORE any drawing) must be drawn ABOVE the layer; anything else would show and change the
    character. Visible pixels are never touched. Returns {layer: dropped px}; after it the stack equals the reference."""
    rank = {n: i for i, n in enumerate(order)}
    H_, W_ = next(iter(layers.values())).shape[:2]
    owner = np.full((H_, W_), -1)
    for n in order:
        owner[partition[n][..., 3] > 0] = rank[n]
    dropped = {}
    for n in order:
        a = layers[n]
        vis = partition[n][..., 3] > 0
        a[vis] = partition[n][vis]  # visible pixels stay exactly the reference's
        bad = (a[..., 3] > 0) & ~vis & ~(owner > rank[n])
        if bad.any():
            a[bad] = 0; dropped[n] = int(bad.sum())
    return dropped


def layer_sheet(layers, order, path, ref, s=6, cols=3, title=""):
    """Review sheet: the reference and the stack, then for every layer (bottom first) the layer alone and the same
    layer with the pixels the stack hides outlined in magenta (what was drawn by hand), with counts."""
    from PIL import ImageFont
    h, w = ref.shape[:2]
    comp = composite(layers, order)
    tile_w, tile_h, lab = w * s, h * s, 16
    cell_w = 2 * tile_w + 18
    items = [("reference", ref, None), ("stack (all layers)", comp, None)]
    for i, n in enumerate(order):
        above = np.zeros((h, w), bool)
        for m in order[i + 1:]:
            above |= layers[m][..., 3] > 0
        items.append((n, layers[n], (layers[n][..., 3] > 0) & above))
    nrows = 1 + (len(items) - 2 + cols - 1) // cols
    im = Image.new("RGBA", (cols * (cell_w + 10) + 10, 24 + nrows * (tile_h + lab + 12)), (255, 255, 255, 255))
    d = ImageDraw.Draw(im)
    d.text((10, 4), title, fill=(0, 0, 0, 255))

    def tile(a, hid=None):
        t = checker(w, h, s); t.alpha_composite(Image.fromarray(a).resize((tile_w, tile_h), Image.NEAREST))
        if hid is not None:
            dd = ImageDraw.Draw(t)
            for y, x in zip(*np.nonzero(hid)):
                dd.rectangle([x * s, y * s, x * s + s - 1, y * s + s - 1], outline=(255, 0, 200, 255), width=1)
        return t

    for j, (n, a, hid) in enumerate(items):
        if j < 2:
            X, Y = 10 + j * (tile_w + 16), 24
            im.paste(tile(a), (X, Y + lab)); d.text((X, Y), n, fill=(0, 0, 0, 255))
            continue
        k = j - 2; r, c = 1 + k // cols, k % cols
        X, Y = 10 + c * (cell_w + 10), 24 + r * (tile_h + lab + 12)
        im.paste(tile(a), (X, Y + lab)); im.paste(tile(a, hid), (X + tile_w + 18, Y + lab))
        vis = int((a[..., 3] > 0).sum()) - int(hid.sum())
        d.text((X, Y), f"{n}: {vis} visible px + {int(hid.sum())} drawn behind other parts (magenta)", fill=(0, 0, 0, 255))
    im.save(path)
    return path


def reassign_islands(layers, name, max_px=12):
    """Pixels of `name` in small pieces cut off from its main shape (stray specks between legs, a cape fleck by the
    hand) move to whichever other layer has the nearest pixel. Returns the number moved. Run before hidden fills."""
    from scipy import ndimage
    a = layers[name]; m = a[..., 3] > 0
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    if n < 2:
        return 0
    sizes = ndimage.sum(m, lab, range(1, n + 1)); main = int(np.argmax(sizes)) + 1
    others = [k for k in layers if k != name and "shadow" not in k]  # a shadow never takes body pixels
    dist = {k: ndimage.distance_transform_edt(~(layers[k][..., 3] > 0)) for k in others}
    moved = 0
    for i in range(1, n + 1):
        if i == main or sizes[i - 1] > max_px:
            continue
        piece = lab == i
        best = min(others, key=lambda k: dist[k][piece].min())
        layers[best][piece] = a[piece]; a[piece] = 0; moved += int(piece.sum())
    return moved


def shade_fill(layer, mask, ramp, outline_col=None, light=(-1, -1), only_empty=True):
    """Fill mask as a rounded, shaded form: ramp = colours dark -> light (the reference's own shades); the edge ring
    gets outline_col (or ramp[0]), the inside steps lighter with distance from the edge, and pixels toward the light
    direction (dx, dy) get one step lighter. Only empty pixels by default, so visible pixels stay exact."""
    from scipy import ndimage
    if not mask.any():
        return
    d = ndimage.distance_transform_cdt(np.pad(mask, 1), metric="chessboard")[1:-1, 1:-1]
    ys, xs = np.nonzero(mask)
    cy, cx = ys.mean(), xs.mean()
    for y, x in zip(ys, xs):
        if only_empty and layer[y, x, 3]:
            continue
        if d[y, x] <= 1:
            col = outline_col if outline_col is not None else ramp[0]
        else:
            k = min(len(ramp) - 1, 1 + (d[y, x] - 2) // 2)
            if (x - cx) * light[0] + (y - cy) * light[1] > 0 and k < len(ramp) - 1:
                k += 1
            col = ramp[k]
        layer[y, x] = col


def scale2x(img):
    """EPX/Scale2x on an RGBA array: doubles the size keeping hard pixel-art edges (the RotSprite first step)."""
    H_, W_ = img.shape[:2]
    P = np.pad(img, ((1, 1), (1, 1), (0, 0)), mode="edge")
    c = P[1:-1, 1:-1]; A = P[:-2, 1:-1]; B = P[1:-1, 2:]; C = P[1:-1, :-2]; D = P[2:, 1:-1]
    eq = lambda u, v: (u == v).all(-1)
    out = np.zeros((H_ * 2, W_ * 2, 4), img.dtype)
    e0 = np.where((eq(C, A) & ~eq(C, D) & ~eq(A, B))[..., None], A, c)
    e1 = np.where((eq(A, B) & ~eq(A, C) & ~eq(B, D))[..., None], B, c)
    e2 = np.where((eq(D, C) & ~eq(D, B) & ~eq(C, A))[..., None], C, c)
    e3 = np.where((eq(B, D) & ~eq(B, A) & ~eq(D, C))[..., None], D, c)
    out[0::2, 0::2] = e0; out[0::2, 1::2] = e1; out[1::2, 0::2] = e2; out[1::2, 1::2] = e3
    return out


def rotsprite(img, angle, pivot, dx=0.0, dy=0.0):
    """RotSprite: Scale2x three times (8x), rotate with nearest neighbour at 8x about the pivot (degrees, + clockwise
    on screen), then sample back to 1x at pixel centres, and translate by (dx, dy). Much cleaner than a 1x nearest
    rotation: outlines stay 1 px, no torn diagonals. A draft for hand clean-up, not a final frame."""
    big = scale2x(scale2x(scale2x(img)))
    k = 8
    H_, W_ = img.shape[:2]
    yy, xx = np.mgrid[0:H_, 0:W_]
    a = np.radians(angle)
    px, py = xx + 0.5 - pivot[0] - dx, yy + 0.5 - pivot[1] - dy
    sx = (np.cos(a) * px + np.sin(a) * py + pivot[0]) * k
    sy = (-np.sin(a) * px + np.cos(a) * py + pivot[1]) * k
    sx = np.floor(sx).astype(int); sy = np.floor(sy).astype(int)
    ok = (sx >= 0) & (sx < W_ * k) & (sy >= 0) & (sy < H_ * k)
    out = np.zeros_like(img); out[ok] = big[sy[ok], sx[ok]]
    return out
