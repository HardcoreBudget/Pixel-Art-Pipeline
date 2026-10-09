"""A character's animations zoomed, one row per animation (96x80 sprite cells).

  python ksheet.py ANIM1,ANIM2,... [SCALE] [OUT.png]

Frames are read from $SPRITES/<anim>_<n>.png (default: the current folder). Default output: ./ksheet.png.
"""
import glob, os, sys
import numpy as np
from PIL import Image, ImageDraw
S = os.path.join(os.environ.get("SPRITES", "."), "")
anims = sys.argv[1].split(",")
s = int(sys.argv[2]) if len(sys.argv) > 2 else 4
rows = []
for a in anims:
    fs = sorted(glob.glob(S + f"{a}_*.png"), key=lambda f: int(f.rsplit("_", 1)[1][:-4]))
    rows.append((a, [np.asarray(Image.open(f).convert("RGBA")) for f in fs]))
n = max(len(r[1]) for r in rows)
W, H = 96 * s, 80 * s
sheet = Image.new("RGBA", (n * W, len(rows) * (H + 12)), (58, 62, 90, 255))
d = ImageDraw.Draw(sheet)
for j, (a, fr) in enumerate(rows):
    for i, f in enumerate(fr):
        sheet.alpha_composite(Image.fromarray(f).resize((W, H), Image.NEAREST), (i * W, j * (H + 12) + 12))
        d.text((i * W + 3, j * (H + 12)), f"{a} {i}", fill=(255, 255, 0, 255))
sheet.save(sys.argv[3] if len(sys.argv) > 3 else "ksheet.png")
