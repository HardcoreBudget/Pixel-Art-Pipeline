"""Review sheet: each animation a row, frames zoomed, a ground line at the feet, the pinhole count under each.

  python scenes/ashen_peak/fsheet.py riku stance,walk,jab [SCALE] [X0,Y0,X1,Y1] [OUT.png]

Reads $SCENES_OUT/ashen_peak/sprites/<char>/ (built by riku_anim.py / grimhold_anim.py). Default output: ./fsheet.png.
"""
import sys, glob, pathlib
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rig as R
char, anims = sys.argv[1], sys.argv[2].split(",")
s = int(sys.argv[3]) if len(sys.argv) > 3 else 3
crop = [int(v) for v in sys.argv[4].split(",")] if len(sys.argv) > 4 else (0, 0, 128, 96)
from stage import OUT
D = OUT / "sprites" / char
rows = []
for a in anims:
    fs = sorted(D.glob(f"{a}_*.png"), key=lambda f: int(f.stem.rsplit("_", 1)[1]))
    rows.append((a, [np.asarray(Image.open(f).convert("RGBA")) for f in fs]))
x0, y0, x1, y1 = crop
w, h = (x1 - x0) * s, (y1 - y0) * s
n = max(len(r[1]) for r in rows)
sheet = Image.new("RGBA", (n * w, len(rows) * (h + 14)), (70, 44, 80, 255))
d = ImageDraw.Draw(sheet)
for j, (a, fr) in enumerate(rows):
    for i, f in enumerate(fr):
        X, Y = i * w, j * (h + 14) + 14
        sheet.alpha_composite(Image.fromarray(f[y0:y1, x0:x1]).resize((w, h), Image.NEAREST), (X, Y))
        gy = Y + (89 - y0) * s
        d.line([(X, gy), (X + w - 1, gy)], fill=(120, 200, 120, 255))
        d.text((X + 3, Y - 13), f"{a} {i} {R.holes(f)}", fill=(255, 255, 0, 255))
sheet.save(sys.argv[5] if len(sys.argv) > 5 else "fsheet.png")
