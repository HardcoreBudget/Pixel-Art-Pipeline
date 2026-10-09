# Code map of the reference implementation

The Python the rules in `lessons.md` came from, in `scenes/` of the Pixel-Art-Pipeline repository. Read it to see
where a rule came from, then do the same thing with the plugin's verbs.

## `scenes/drowned_shrine/` (The Drowned Shrine)

| File | What it holds |
|---|---|
| `px.py` | Palette `RAMPS` (16 ramps, darkest first), `C` colour names, `ramp_step`, `blit`, `art` (ASCII art to RGBA), `outline`. |
| `light.py` | `index()` (pixel to palette index), `apply(img, steps, emissive=True)` with a Bayer dither, and `lightmap(h, w, ambient, lights)`. |
| `repix.py` | Krea raw image to 64-grid cells (grid phase plus cell mode), `to_palette` in CIELAB. Usage: `python repix.py <name> ramp,ramp,...`. |
| `kestrel.py` | Ownership masks, limb pieces, `hidden()` fills, `JOINTS`, and `layers.npz` (stack equals the design). |
| `kestrel_anim.py` | `move`, `bone`, `knee_for` (IK with the design's own bend side), `leg`, `twist` (tear-free cloth), `sword`, `frame(pose, named)`, `anims()`, `PAS_ORDER`. |
| `gloomlure.py` | A non-humanoid: jaw hinge, a stalk redrawn as a curve, fins bent by whole-pixel shifts, hand-drawn eye states. |
| `tiles.py`, `tilemap.py` | Rule-drawn tiles, the water autotile chosen by neighbours, a `Tileset` of unique tiles, and a 3-layer map. |
| `font.py`, `ui.py` | Hand-drawn 5 px and 7 px fonts; panels, bars with a lost-HP ghost, icons, locks, menus. |
| `fx.py` | Slash, spark, sunburst, ring, splash, plume, bubble, stun stars, charge, motes, fireflies. |
| `scene.py` | `hero_state(t)`, `boss_state(t)`, `render(t)`: shadows, then reflection, y-sorted fighters, effects, lighting, UI, fade. |
| `export_pas.py` | Jobs for the sandbox builder, `build_many`, and a pixel check against the plugin's renders. |
| `PLAN.md` | View, palette, cast, beats with tick ranges, and the frame list. |

- **Sandbox builder:** `unity/PasBuilder/Editor/SandboxBuild.cs` (copied into a scratch Unity project's `Assets/`). It
  reads JSON jobs with layers, cels, tags, poses, layer properties and `tiles`, and renders every frame back.
- **Helpers in `scenes/agentdraw/`:** `core.py` (`rotsprite`, `scale2x`, `assign`, `settle`, `shade_fill`,
  `layer_sheet`) and `pas.py` (`export_job`, `build_many`).
- **Review tools** (in this skill's `scripts/`): `fsheet.py` (a fighter's animations as review rows with the ground line and pinholes/islands), `render_all.py` (the whole loop to GIF and
  npy), `contact.py` (contact sheets per tick range), `ksheet.py` (a character's animations zoomed).

## `scenes/ashen_peak/` (Ashen Peak)

| File | What it holds |
|---|---|
| `rig.py` | The reusable fighter rig: `Rig(layers, joints, SPEC).frame(pose, named)`; poses use root, lean, head, limb targets (modes `rest`, `root`, `abs`), cloth, spin, ground, front/back and tint. Also `twist`, `holes`, `adopt_fragments`. |
| `riku.py`, `grimhold.py` | Ownership masks, hidden fills, `JOINTS`, `ORDER`, and `build()` to `*_layers.npz` (stack equals the design). |
| `riku_anim.py`, `grimhold_anim.py` | `SPEC` and `anims()`: 16 and 12 moves; `build_frames()` reports pinholes and islands. |
| `stage.py` | The parallax stage (sky, peaks, temple, floor, foreground), swaying lanterns, `twist` banners, petals. |
| `hud.py` | Health bars with a ghost, the timer, medallions, the heavy call-out font, the combo counter. |
| `ffx.py` | Fireball, fire pop, block and hit sparks, dust, shockwave, speed lines, flame arc. |
| `fight.py` | The choreography as clips per fighter, `HITS`, `COMBOS`, `FREEZE`, `render(t)`, `make()`. |
| `fsheet.py` | The review sheet: each animation a row, zoomed, with the ground line and (pinholes, islands) per frame. |
| `export.py` | `Riku.pas`, `Grimhold.pas`, `AshenPeak.pas` through the sandbox, checked against the plugin's renders. |
