"""Render a whole scene loop to frames (npy) and GIFs (native and 3x).

  SCENE=/path/to/scene python render_all.py

Imports the scene's own `scene.py` from $SCENE (it must define N, OUT and render(t) -> HxWx(3|4) uint8 array, as the
reference implementation does). Writes to the scene's OUT. The Drowned Shrine, from the repository root:

  SCENE=scenes/drowned_shrine python skills/pixel-scene/scripts/render_all.py
"""
import os, sys, time
sys.path.insert(0, os.environ.get("SCENE", "."))
import numpy as np
from PIL import Image
import scene as S
t0 = time.time()
frames = [S.render(t) for t in range(S.N)]
np.save(S.OUT / "scene_frames.npy", np.stack(frames))
ims = [Image.fromarray(f[..., :3]) for f in frames]
ims[0].save(S.OUT / "scene.gif", save_all=True, append_images=ims[1:], duration=80, loop=0)
big = [im.resize((ims[0].width * 3, ims[0].height * 3), Image.NEAREST) for im in ims]
big[0].save(S.OUT / "scene_x3.gif", save_all=True, append_images=big[1:], duration=80, loop=0)
print("rendered", len(frames), "in", round(time.time() - t0), "s")
