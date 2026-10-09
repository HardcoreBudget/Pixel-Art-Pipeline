"""Pixel clean-up for generated designs: hard transparency, background keying, grid snapping.

The helpers krea.py uses:
  clean_alpha    hard alpha; keys out a flat, border-connected background (the plain white Krea draws on)
  pixelate       snaps the image to a true pixel grid, one palette colour per cell
  detect_cell    estimates the model's own pixel size (used only when no grid is given, i.e. krea.py --pixel 0)
  failed_sprite  warns when a single-character sprite looks like a failed (noise) generation
"""
from PIL import Image


def clean_alpha(img, tol=40, key_border=True):
    """Hard transparency: alpha < 128 becomes fully clear (RGB zeroed so nothing fringes), the rest fully opaque.
    If the model returned an opaque background anyway, key out the flat colour (and, on light backgrounds, any bright
    near-grey glow) connected to the image border."""
    import numpy as np
    from scipy import ndimage
    a = np.array(img.convert("RGBA"))
    opaque = a[..., 3] >= 128
    if key_border and (~opaque).mean() < 0.05:  # no real transparency: fall back to removing the border-connected background
        rgb = a[..., :3].astype(int)
        border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
        bg = np.median(border, axis=0)
        near = np.abs(rgb - bg).sum(-1) <= tol
        if bg.mean() > 200:
            # a light background often carries a soft glow/gradient that drifts out of tol; bright, near-grey pixels are
            # background too as long as they reach the border (the sprite's dark outline keeps inner whites, like an
            # apron, from connecting to it)
            near |= (rgb.mean(-1) > 190) & (rgb.max(-1) - rgb.min(-1) < 45)
        lab, _ = ndimage.label(near)
        edge_labels = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
        opaque &= ~np.isin(lab, edge_labels[edge_labels > 0])
    if key_border and (~opaque).any():
        # partly transparent output can still carry opaque white/grey cloud patches around the figure: remove bright,
        # near-grey opaque regions that touch the transparent area or the border (the dark outline keeps light areas
        # inside the character, like a white apron, from touching either)
        rgb = a[..., :3].astype(int)
        pale = opaque & (rgb.mean(-1) > 190) & (rgb.max(-1) - rgb.min(-1) < 45)
        if pale.any():
            lab, n = ndimage.label(pale)
            clear = ~opaque
            drop = []
            for i, sl in enumerate(ndimage.find_objects(lab), 1):
                # look one pixel around the patch: a background cloud is mostly surrounded by transparency (or the
                # image edge); a beard, a white apron or a grey watering can is mostly surrounded by the character
                y0, y1 = max(sl[0].start - 1, 0), min(sl[0].stop + 1, lab.shape[0])
                x0, x1 = max(sl[1].start - 1, 0), min(sl[1].stop + 1, lab.shape[1])
                m = lab[y0:y1, x0:x1] == i
                ring = ndimage.binary_dilation(m) & ~m
                at_edge = y0 == 0 or x0 == 0 or y1 == lab.shape[0] or x1 == lab.shape[1]
                if ring.any() and (clear[y0:y1, x0:x1][ring].mean() >= 0.35 or (at_edge and m.sum() > 400)):
                    drop.append(i)
            if drop:
                opaque &= ~np.isin(lab, drop)
    if key_border and opaque.any():
        # drop dust: isolated opaque specks (keying leftovers, stray model pixels) that would stretch the crop box.
        # Real detached parts (a separate sword, a sparkle) are far larger than 0.5% of the figure or 200 px.
        lab, n = ndimage.label(opaque)
        if n > 1:
            sizes = np.bincount(lab.ravel())
            sizes[0] = 0
            dust = (sizes < 0.005 * sizes.max()) & (sizes < 200)
            dust[0] = False
            opaque &= ~dust[lab]
    a[..., 3] = np.where(opaque, 255, 0)
    a[~opaque, :3] = 0
    return Image.fromarray(a, "RGBA")


def failed_sprite(raw):
    """A warning string if a cleaned single-character sprite looks like a failed generation, else None.
    A good sprite is one opaque island with no enclosed holes; the silent noise glitch (no error from ComfyUI) comes
    out as scattered islands riddled with holes. Only meaningful for kind "sprite"."""
    import numpy as np
    from scipy import ndimage
    op = np.array(raw.convert("RGBA"))[..., 3] >= 128
    lab, n = ndimage.label(op)
    islands = int((np.bincount(lab.ravel())[1:] >= 100).sum())
    tl, tn = ndimage.label(~op)
    edge = set(np.unique(np.concatenate([tl[0], tl[-1], tl[:, 0], tl[:, -1]])).tolist())
    sizes = np.bincount(tl.ravel())
    holes = sum(1 for i in range(1, tn + 1) if i not in edge and sizes[i] >= 50)
    if islands > 2 or holes > 3:
        return (f"WARNING: this looks like a failed generation ({islands} separate pieces, {holes} holes; a good sprite is "
                f"1 piece with no holes). It is usually a one-off glitch: rerun with the same seed.")
    return None


def detect_cell(rgb, opaque, with_strength=False):
    """Estimate the pixel size the model drew at: the strongest period of the colour-edge profile (3-16 px)."""
    import numpy as np
    a = rgb.astype(int)
    power, freqs = 0, None
    for axis in (1, 0):
        e = (np.abs(np.diff(a, axis=axis)).sum(-1) > 40) & (opaque[:, 1:] if axis == 1 else opaque[1:, :])
        prof = e.sum(axis=0 if axis == 1 else 1).astype(float)
        if prof.sum() == 0:
            continue
        prof -= prof.mean()
        n = 16384  # zero-pad for sub-pixel period resolution
        power = power + np.abs(np.fft.rfft(prof * np.hanning(len(prof)), n)) ** 2 / (prof ** 2).sum()
        freqs = np.fft.rfftfreq(n)
    if freqs is None:
        return None
    band = (freqs >= 1 / 16) & (freqs <= 1 / 3)
    pb = power[band]
    i = pb.argmax()
    cell, strength = 1 / freqs[band][i], pb[i] / np.median(pb)
    return (cell, strength) if with_strength else cell


def pixelate(img, grid, colors, crop=True, key_border=True, fallback_grid=64, cell_px=None, palette_img=None):
    """Snap the model's output to a true pixel grid: hard alpha, one palette colour per cell (the cell's most common)."""
    import numpy as np
    a = np.array(clean_alpha(img, key_border=key_border))
    opaque = a[..., 3] >= 128
    if crop and opaque.any():
        ys, xs = np.where(opaque)
        pad = 2
        y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, a.shape[0])
        x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, a.shape[1])
        a, opaque = a[y0:y1, x0:x1], opaque[y0:y1, x0:x1]
    rgb = a[..., :3]
    # one shared palette from the opaque pixels, no dithering
    pal_src = Image.fromarray(rgb[opaque].reshape(1, -1, 3) if opaque.any() else rgb)
    pal_img = palette_img or pal_src.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    idx = np.array(Image.fromarray(rgb).quantize(palette=pal_img, dither=Image.Dither.NONE))
    palette = np.array(pal_img.getpalette()[:colors * 3], dtype=np.uint8).reshape(-1, 3)

    def edges(cell):
        gw, gh = max(1, round(a.shape[1] / cell)), max(1, round(a.shape[0] / cell))
        return gw, gh, np.linspace(0, a.shape[0], gh + 1).astype(int), np.linspace(0, a.shape[1], gw + 1).astype(int)

    def purity(cell):
        """Share of each cell's interior that is its most common palette colour (real pixel art: high)."""
        gw, gh, ye, xe = edges(cell)
        hit = tot = 0
        for j in range(gh):
            for i in range(gw):
                sl = (slice(ye[j] + 1, ye[j + 1] - 1), slice(xe[i] + 1, xe[i + 1] - 1))
                v = idx[sl][opaque[sl]]
                if v.size:
                    hit += np.bincount(v).max(); tot += v.size
        return hit / tot if tot else 0

    longest = max(a.shape[0], a.shape[1])
    if cell_px:
        cell = cell_px
    elif grid:
        cell = longest / grid
    else:
        found = detect_cell(rgb, opaque, with_strength=True)
        # trust the model's own grid only when it is clearly periodic AND its cells are near-flat;
        # a detailed illustration (no real grid) falls back to a fixed size instead of a noise period
        if found and found[1] >= 15 and purity(found[0]) >= 0.6:
            cell = found[0]
        else:
            cell = longest / fallback_grid
    gw, gh, ys_edges, xs_edges = edges(cell)
    out = np.zeros((gh, gw, 4), dtype=np.uint8)
    for j in range(gh):
        for i in range(gw):
            sl = (slice(ys_edges[j], ys_edges[j + 1]), slice(xs_edges[i], xs_edges[i + 1]))
            op = opaque[sl]
            if op.size == 0 or op.mean() < 0.5:
                continue
            counts = np.bincount(idx[sl][op], minlength=len(palette))
            out[j, i, :3] = palette[counts.argmax()]
            out[j, i, 3] = 255
    return Image.fromarray(out, "RGBA"), cell
