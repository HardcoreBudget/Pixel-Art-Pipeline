# Working in Pixel Art Studio

> Ask the user before touching a Unity Editor they or another agent have open. Check every step by reading the
> document back (`session.Inspect()`, `pas.read.document`) and by looking at renders, never by assuming a call worked.

## Sessions

The plugin's reference is `Assets/PixelArtStudio/SKILL.md` (also `StudioScript.Describe()`); read "Getting a
session" first.

- `StudioScript.Create("Assets/Art/Hero.pas", width, height, ColorMode.Indexed)` makes a new document;
  `StudioScript.Open(path)` opens one (if a Studio window already has it open, you get that document, not a copy).
- In `execute_code`, fully qualify the names (`PixelArtStudio.Editor.Scripting.StudioScript.Open(path)`) and write
  the `("name", value)` arguments inline. `Create` throws when the file exists, so check first and `Open` instead.
- Wrap each logical step in `session.Batch("...", s => { ... })`: all or nothing, one undo entry. Then `Save()`.

## The layer tree

- A group is a bone: a pose on the group turns everything inside it about the group's pivot, and a child's own pose
  turns on top of that. Give a group's pose a pivot (a group holds no pixels, so without one it turns about the
  canvas origin).
- `pas.layer.group` wraps a layer in a new group; `pas.layer.add` with `parent` adds a layer inside a group;
  `pas.layer.move` with `parent` moves one in.
- Build the whole tree first, then draw: every add or group shifts the indices above it. Read `pas.read.document` for
  the indices once the tree is built.

## Layers drawn elsewhere

A piece drawn outside the plugin (in Python, as `scenes/` does, or in another editor) comes in as a PNG:

- `pas.layer.importPng` with `path`, `x`, `y` and either `name` (a new layer, with `parent` and `index` to place it in
  the tree) or `layer` (paste into an existing one). On an indexed document give `match: "lab"` and the piece's
  `ramps`, so every pixel lands on a palette entry.
- `pas.pixels.paste` writes a block from code: `x`, `y`, `width`, `height`, `coverage` (bool per pixel, row-major) and
  `indices` (indexed) or `colors` (RGBA).
- Every piece at the same canvas position it had in the design, so the stack still equals the design:
  `pas.read.diff` with the reference PNG answers `identical: true`.

## Poses, frames and tags

- `pas.pose.set` (`layer`, `frame`, `angle`, `pivotX`, `pivotY`, `x`, `y`): positive angle turns clockwise on screen;
  pivots are pixel-edge coordinates. Poses are per frame and not interpolated: pose every frame you make.
- Poses preview at nearest neighbour; `pas.pose.bake` turns the pixels cleanly and clears the poses.
- `pas.frame.duplicate` with `poses: true` copies a frame with its poses; `pas.frame.duration` sets its time;
  `pas.tag.add` (`name`, `from`, `to`, `direction`, `loops`) names a move. A move played backwards is a `Reverse` tag,
  not copied frames.
- A reference picture (the design, or a sketch of a key pose) can sit on a layer at the bottom: lock it and lower its
  opacity with `pas.layer.properties` (`locked: true`, `opacity`), and hide it (`visible: false`) before checks,
  settles and exports.

## From keyframes to the finished move

1. Put the keys on frames 0, k, 2k ... (k = in-betweens + 1), each a duplicate of the rest frame with its pieces
   turned.
2. On each key, pose the root first (body bob or lean), then parents before children (the upper arm before the item
   it holds). Match the silhouette first, then the item angles.
3. Fill the in-betweens by turning the pieces part of the way (ease in and out). Look at every frame at 1x and zoomed,
   and fix: turned pixels that break the outline, a hidden part that now shows, the item's hand.
4. Where a pose cannot come from turning (a turned head, a foreshortened arm, a smear frame), redraw that piece on
   that frame only. The rest pieces stay the design.
5. `pas.check.tears` and `pas.frame.clean` on every frame; then play each tag (`pas.render.tag`) beside the keys.

The plugin's layer conventions apply throughout: one anatomical part per layer, no pixels bleeding across layers,
every independently moving layer drawn complete, and each layer alone plus the composite checked on every frame.
