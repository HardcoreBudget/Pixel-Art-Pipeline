"""Contact sheet of a rendered scene loop: every `step`-th tick from t0 to t1, cropped, 2x, five per row.

  python contact.py T0 T1 STEP [X0,Y0,X1,Y1] [OUT.png]

Reads $SCENE/out/scene_frames.npy (written by render_all.py; override with SCENE_FRAMES, for example
SCENE_FRAMES=out/scenes/drowned_shrine/scene_frames.npy for the repository's Drowned Shrine). Default crop: the whole
320x180 view; default output: ./contact.png.
"""
import os, pathlib, sys
import numpy as np
from PIL import Image, ImageDraw
frames = os.environ.get("SCENE_FRAMES") or str(pathlib.Path(os.environ.get("SCENE", ".")) / "out" / "scene_frames.npy")
F = np.load(frames)
t0, t1, step = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
x0, y0, x1, y1 = [int(v) for v in sys.argv[4].split(",")] if len(sys.argv) > 4 else (0, 0, 320, 180)
s = 2; cols = 5
ticks = list(range(t0, t1, step))
w, h = (x1 - x0) * s, (y1 - y0) * s
sheet = Image.new("RGB", (cols * w, ((len(ticks) + cols - 1) // cols) * (h + 12)), (20, 20, 30))
d = ImageDraw.Draw(sheet)
for i, t in enumerate(ticks):
    im = Image.fromarray(F[t][y0:y1, x0:x1, :3]).resize((w, h), Image.NEAREST)
    x, y = (i % cols) * w, (i // cols) * (h + 12)
    sheet.paste(im, (x, y + 12)); d.text((x + 3, y), f"t={t}", fill=(255, 255, 0))
sheet.save(sys.argv[5] if len(sys.argv) > 5 else "contact.png")
