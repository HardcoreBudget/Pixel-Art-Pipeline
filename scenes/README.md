# The two reference scenes

The full source of two pixel-art scenes, and the worked examples behind the `pixel-scene` skill. Krea 2 drew the four
character designs and nothing else; every animation frame, tile, effect, font, the lighting and the UI are drawn in
this code, pixel by pixel. Pages with every animation:
[Ashen Peak](https://hardcorebudget.github.io/Pixel-Art-Pipeline/ashen-peak/) and
[The Drowned Shrine](https://hardcorebudget.github.io/Pixel-Art-Pipeline/drowned-shrine/).

| | The Drowned Shrine | Ashen Peak |
|---|---|---|
| Genre | turn-based battle (after *Sea of Stars*) | one-round arcade fight (after *Mortal Kombat*) |
| View | 320 x 180, 16 px tiles | 256 x 144, a 400 px parallax stage |
| Loop | 336 ticks of 80 ms (26.9 s) | 360 ticks of 80 ms (28.8 s) |
| Cast | Kestrel (44 frames, 18 layers), Gloomlure (21 frames) | Riku (76 frames, 16 moves), Grimhold (61 frames, 12 moves) |
| Plan | [`drowned_shrine/PLAN.md`](drowned_shrine/PLAN.md) | [`ashen_peak/PLAN.md`](ashen_peak/PLAN.md) |

## Rebuild them

No GPU and no ComfyUI: Python 3.10 or later with Pillow, NumPy and SciPy (`pip install -r requirements.txt`). Run from
the repository root. Everything is written under `out/scenes/` (set `SCENES_OUT` to put it elsewhere).

```bash
# The Drowned Shrine (about 1 minute)
python scenes/drowned_shrine/kestrel.py          # layers; prints "stack diff 0" (the stack equals the design)
python scenes/drowned_shrine/kestrel_anim.py     # 44 frames in 9 animations -> sprites/kestrel/
python scenes/drowned_shrine/gloomlure.py        # layers and 21 frames -> sprites/gloomlure/
SCENE=scenes/drowned_shrine python skills/pixel-scene/scripts/render_all.py   # scene.gif, scene_x3.gif, scene_frames.npy

# Ashen Peak (about 3 minutes)
python scenes/ashen_peak/riku.py                 # 15 pieces, "stack diff 0"
python scenes/ashen_peak/grimhold.py             # 14 pieces
python scenes/ashen_peak/riku_anim.py            # "76 frames; pinholes/specks: none"
python scenes/ashen_peak/grimhold_anim.py        # "61 frames; pinholes/specks: none"
python scenes/ashen_peak/fight.py                # ashen_peak.gif, fight_frames.npy
```

With Python 3.12, NumPy 2.5, Pillow 12.3 and SciPy 1.18 on Linux, every layer file, all 66 + 137 sprite frames and all
336 + 360 scene frames come out identical to the ones on the pages, and the Drowned Shrine GIF byte for byte. Other
library versions may differ in a pixel here and there (RotSprite and the dithers are exact integer code, but image
resampling is not guaranteed across Pillow versions).

Other entry points:

| Command | Writes |
|---|---|
| `python scenes/drowned_shrine/tilemap.py` | `tileset_f0..3.png`, `map_f0.png`, `map_anim.gif`, `map.json` |
| `python scenes/drowned_shrine/ui.py`, `font.py` | `ui_sheet.png`, `font_sheet.png` |
| `python scenes/drowned_shrine/scene.py [TICK ...]` | `scene_keys.png`, chosen ticks side by side |
| `python scenes/drowned_shrine/repix.py kestrel_9101 ink,crimson,teal,skin,wood,cream,silver,stone,night` | the raw design snapped to its 64 grid in the scene palette (reproduces `designs/kestrel_9101_grid.png` exactly) |
| `python scenes/ashen_peak/stage.py`, `hud.py` | `stage_check.png`, `hud_check.png` |
| `python scenes/ashen_peak/fsheet.py riku stance,walk,jab 3` | a review sheet: each animation a row, the ground line, (pinholes, islands) per frame |

## The designs

`designs.sh` in each folder is the exact Krea 2 call (prompts, seeds, `--pixel 64 --no-style --colors 14`); it needs
ComfyUI running (see the [main README](../README.md#usage)). The picked designs are already here, in `designs/`:

| File | What it is |
|---|---|
| `kestrel_9101_raw.png`, `gloomlure_9402_raw.png`, `riku_7101_raw.png`, `grimhold_7301_raw.png` | Krea 2's 1024 px designs (background removed) |
| `kestrel_9101_grid.png`, `riku_7101_grid.png` | `repix.py`'s 64-grid version in the scene palette: what `kestrel.py` / `riku.py` build from |
| `gloomlure_design.png`, `grimhold_design_raw.png` | the same, padded to 64 x 64 by a one-off step: what `gloomlure.py` / `grimhold.py` build from |
| `kestrel_portrait.png` | the 22 x 22 head on the HP plate, cut from her design and tidied by hand |

## Into Pixel Art Studio

`pas/` holds the seven documents the scenes export to. In each, the plugin's own renderer draws every frame identical
to the scene's frames:

| Document | Canvas | Layers | Frames | Tags |
|---|---|---|---|---|
| `ShrineTiles.pas` | 128 x 192 | 1 | 4 | Animate; tile size 16, the Tiles tab's scratchpad = the 20 x 12 map |
| `ShrineArena.pas` | 320 x 192 | 3 | 4 | Animate |
| `Kestrel.pas` | 96 x 80 | 18 | 44 | Idle, Run, Slash1, Slash2, Hop, Block, Leap, Plunge, Victory |
| `Gloomlure.pas` | 80 x 80 | 10 | 21 | Idle, Windup, Lunge, Hurt, Charge, Stunned |
| `Riku.pas` | 128 x 96 | 16 | 76 | 16 moves |
| `Grimhold.pas` | 128 x 96 | 15 | 61 | 12 moves |
| `AshenPeak.pas` | 400 x 144 | 6 | 8 | Ambient |

To rebuild them, `drowned_shrine/export_pas.py` and `ashen_peak/export.py` write JSON jobs and run a headless Unity on a
**scratch** project (never your real one) that has Pixel Art Studio and [`unity/PasBuilder`](../unity/PasBuilder)
installed, then compare the plugin's renders with the scene's frames pixel for pixel. Set the scratch project up once:

1. Create an empty Unity 2022.3 project (for example `Unity -batchmode -createProject /path/to/scratch -quit`).
2. Add Pixel Art Studio's package dependencies to its `Packages/manifest.json`: `"com.unity.2d.pixel-perfect": "5.1.0"`
   and `"com.unity.2d.tilemap": "1.0.0"`.
3. Import Pixel Art Studio (`Unity -batchmode -projectPath /path/to/scratch -importPackage PixelArtStudio-1.0.unitypackage -quit`,
   or Assets > Import Package in the Editor).
4. Copy the `unity/PasBuilder` folder into the project's `Assets/` folder (it becomes `Assets/PasBuilder/Editor/...`).
5. Open the project once (`Unity -batchmode -projectPath /path/to/scratch -quit`) so it compiles. Close any Editor that has
   it open before an export: the scripts run their own headless Unity on it.

Then, after the rebuild steps above (the export scripts read their layers and frames from `out/scenes/`):

```bash
export UNITY_EDITOR=/path/to/Unity/Editor/Unity  PAS_SANDBOX=/path/to/scratch
python scenes/drowned_shrine/export_pas.py       # tiles arena kestrel gloomlure; prints "plugin mismatches: none" (about 1 minute)
python scenes/ashen_peak/export.py               # Riku, Grimhold, AshenPeak; likewise (about 2 minutes)
```

The documents land in the scratch project's `Assets/Built/`, the plugin's renders of every frame in
`out/scenes/agentdraw/pas_render/`, and the Unity log in `out/scenes/agentdraw/pas_jobs/batch.log`.

Tested exactly as above on Linux with Unity 2022.3.62f3 and Pixel Art Studio 1.0, no GPU: `SandboxBuild.cs` compiles
with no errors or warnings, both scripts print "plugin mismatches: none" for all seven documents, and every rebuilt
`.pas` is byte-identical to the one in `pas/`. Windows, macOS and other Unity versions are untested.

## Layout

| Path | What it holds |
|---|---|
| `agentdraw/core.py` | the drawing helpers: masks, `assign`, `settle`, `shade_fill`, `layer_sheet`, `rotsprite`, `scale2x` |
| `agentdraw/pas.py` | `export_job` (layers and frames to a builder job) and `build` / `build_many` (headless Unity) |
| `drowned_shrine/` | `px.py` palette and output paths, `light.py`, `tiles.py`, `tilemap.py`, `font.py`, `ui.py`, `fx.py`, `repix.py`, `kestrel.py`, `kestrel_anim.py`, `gloomlure.py`, `scene.py`, `export_pas.py` |
| `ashen_peak/` | `rig.py` (the reusable rig), `riku.py`, `riku_anim.py`, `grimhold.py`, `grimhold_anim.py`, `stage.py`, `hud.py`, `ffx.py`, `fight.py`, `fsheet.py`, `export.py` |
| `designs/` | the inputs above |
| `pas/` | the plugin documents |

[`skills/pixel-scene/references/code-map.md`](../skills/pixel-scene/references/code-map.md) describes each file.
Ashen Peak imports the palette, fonts and lighting from `drowned_shrine/`.

Licence: the code is MIT (`LICENSE`); the art, designs and `.pas` files are CC BY 4.0 (`LICENSE-MEDIA`).
