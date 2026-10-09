---
name: pixel-scene
description: Build an animated pixel-art game scene (tiles, characters with full movesets, effects, lighting, UI) from AI character designs, with every frame drawn at pixel level by the agent and exported as Pixel Art Studio .pas files. Use when asked to make pixel-art characters, animations, tilesets, battle or fighting scenes, or sprite sheets for the plugin.
---

# Pixel scene from a design

Krea 2 draws **the design only**: one still picture of each character. You draw everything else pixel by pixel in
code: layers, every animation frame, tiles, effects, lighting and UI. Then you prove the plugin renders it the same.
Review happens **only on GIFs on an index.html page**, so every step ends in something the reviewer can watch.

Paths in this skill: `$PIPELINE` is the Pixel-Art-Pipeline folder (its `scripts/krea.py` makes the designs), and
`$SCENE` is your own working folder for one scene.

The skill was distilled from two finished scenes, whose full source is in `$PIPELINE/scenes/` (rebuild them with
`$PIPELINE/scenes/README.md`; their pages are in `$PIPELINE/docs/`):
- **"The Drowned Shrine"**, a turn-based battle.
- **"Ashen Peak"**, a one-on-one 2D fighting scene with two full movesets.

The character's pixels are made with the plugin's verbs; steps 3 to 6 name the plugin's SKILL.md section for each
(`Assets/PixelArtStudio/SKILL.md` in a project with the plugin installed, the "Model Conventions" part), and that file
is the manual. `references/code-map.md` maps the reference implementation the rules below came from (`rig.py`,
`kestrel.py`, `kestrel_anim.py`, in `$PIPELINE/scenes/`), so the names in the lessons make sense. To work in code
instead of verbs, start a fighter from `scenes/ashen_peak/rig.py` and copy a scene's layout (one module per
character, one `*_anim.py`, a `scene.py` with `N`, `OUT` and `render(t)`).

## The workflow

1. **Pick the reference game and pin the scene.** Choose the view size (320 × 180 or smaller), the tile size (16), the
   character canvas (64-grid design, canvas padded so swings don't clip), the palette (ramps, darkest first), the cast
   and a beat list with tick ranges (80 ms ticks). Write it down (`PLAN.md`) before drawing anything.
2. **Designs (Krea 2).** Use `python $PIPELINE/scripts/krea.py "<prompt>" --name <char> --pixel 64 --no-style
   --colors 12..14 --seed N`, two seeds each.
   - Ask for **flat colours, a limited palette with named accents** (unnamed accents get quantised away), side
     view, **limbs clearly separated from the body** and a plain white background.
   - Generate every fighter **facing the same way** and mirror at render time.
   - If RAM is tight, stop ComfyUI before a Unity run and start it again afterwards with
     `$PIPELINE/scripts/start_comfy.sh`.
3. **Design onto the grid (the plugin: "Building a character (start here)", "Bringing pixels in", "Palette ramps").**
   Set the scene palette and tag its ramps with `pas.palette.ramp`, then bring Krea's `_raw` design onto the
   character's 64-grid with `pas.layer.importPng` (`cell`, `match: "lab"`, the character's `ramps`, `x`/`y` so the feet
   stand a few pixels above the canvas bottom). Add a ramp when a colour lands between two. Then clean the design by
   hand with the drawing verbs: ground shadow, white background islands, hollow blades.
4. **Layers, back to front (the plugin: "Building a character (start here)", "Masks", "Hidden fills", "Settling a
   rig", "Layer conventions").**
   - Peel each part off the design, front-most first, with `pas.layer.peel` (or one at a time with
     `pas.selection.shape` and `pas.selection.move_to_layer`); a pixel belongs to exactly one part.
   - **Cut every limb into rigid pieces:** thigh, shin, boot (split at the cuff), upper arm, forearm with the fist or
     glove.
   - Clean the partition with `pas.check.tears` (`pieces`), and move each stray speck to its piece.
   - Fill what each piece hides (the thigh top under the tunic, the shin inside the boot cuff) with
     `pas.pixels.shadeFill` in that part's ramp.
   - `pas.layer.settle` against the design drops what would show and proves the stack equals the design, 0 px
     different. Measure the joints (hip, knee, ankle, shoulder, elbow) on the design as pixel-edge points.
5. **Frames from poses (the plugin: "Animating", "Poses", "Reaching", "Turning pieces", "Bending cloth", "Motion
   recipes", "A worked rig").** Each frame is the rest frame duplicated (`pas.frame.duplicate`) and its pieces turned:
   - Pieces **turn about their measured joints** (`pas.pose.set`, baked clean with `pas.pose.bake`, or
     `pas.transform.free`); knees and elbows come from two-bone `pas.pose.reach`, bending to the same side as in the
     design.
   - Head and torso keep the design's pixels (moved, or leaned a few degrees).
   - **Cloth (capes, scarves, headband tails, banners) is bent with `pas.transform.bend`**, never by shifting rows.
   - **Redraw only what has no fixed shape:** a sword blade at any angle, a lure stalk. Everything else is design
     pixels.
   - Finish with one ink line around the silhouette, on its own layer (`pas.draw.outline`).
6. **Review every frame (the plugin: "Frame review checklist", "Seeing your work")**, zoomed 5-6x beside the design,
   with `references/qa-checklist.md` as the extra list. Fix, re-render, and look again. Never ship a frame you haven't
   looked at.
7. **The world.**
   - Tiles are drawn by rule (patterns periodic in the tile size; an autotile chosen by neighbours; 2-tile slabs to
     break the grid).
   - The UI kit and fonts are hand-drawn glyphs.
   - Effects return `(sprite, anchor)`.
   - Lighting moves every pixel along its ramp (`light.py`, Bayer dither; fire and glow ramps are emissive; the
     fighters get a darkness floor so they stay readable).
8. **Choreography (`scene.py`).** The image is a pure function of the tick, so every state is `state(t)`; the loop is
   exact and any frame re-renders alone. Render the whole loop, then read it as **contact sheets per beat**
   (consecutive ticks, cropped to the action) before anyone sees the GIF.
9. **Into the plugin (the scene's own exporter).** The character's layers, poses, frames and tags are already
   plugin documents, made with the verbs above. Use a headless **sandbox** copy of the Unity project only (for
   example `$PAS_SANDBOX`), never an editor someone else has open:
   - One layer per piece, with fixed-order slots (a part that changes depth gets two slots, filled one at a time).
   - One tag per animation; tiles through `pas.tiles.set`.
   - The plugin renders every frame back; the renders must equal what you expect, pixel for pixel.
10. **Show it.** Build an index.html page: the loop as a native-resolution GIF scaled with
    `image-rendering: pixelated`, beat stills, each animation as its own GIF, the design next to its 64-grid version,
    the layer sheets, the tileset, the UI kit, and a table of the plugin documents.

## Rules that came from mistakes

The full list, with the evidence, is in `references/lessons.md`. Never break these. (The reference code's names map to
the plugin's: `twist()` is `pas.transform.bend`, `settle` is `pas.layer.settle`, `rig.holes` is `pas.check.tears`.)

- **Never resynthesise a limb.** Shaded capsules "crumble and look awful" next to design pixels. Cut pieces from the
  design and turn them.
- **Never bend cloth by moving rows or columns forward.** Rows separate and the cape "tears apart". Use `twist()`,
  which maps from the output back to the source.
- **Runs and walks are keyed cycles** (contact, down, passing, up, and so on) with a real stride of about ±9 px. A small
  loop under the hips reads as a shuffle. A foreshortened far leg can't stride: draw it from the near leg's pieces,
  one ramp step darker.
- **Nothing important goes under the head.** Overhead weapons go to the right of the face; arms tucked behind the head
  hide the hands.
- **Keep props out of the body's silhouette**, or they vanish (a sword trailing behind a running body).
- **Every layer must stack to the design at rest** before any frame is drawn. Idle frame 0 equals the design, apart
  from redrawn props.
- **Blade remnants hide in other parts' masks.** After you drop a part, check its colours are gone everywhere.
- **`settle` drops hidden fills on the top layer**, because nothing covers them. Put a root that must hide under
  another part on a layer below that part.
- **Every frame: 0 pinholes and 0 extra islands** (`rig.holes`), a clean contact sheet, and the plugin renders
  equal to yours.
- **Big heads and short limbs:** sell kicks by tipping the whole body about the planted foot, and keep fists clear of
  the face.
