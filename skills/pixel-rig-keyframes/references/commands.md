# Commands

Stage 1 runs from the repository root with ComfyUI up. Every later stage is a plugin verb, called from C# on a
session (`session.Do("verb", ("arg", value), ...)` for commands, `session.Query(...)` for `pas.read.*`,
`pas.render.*` and `pas.check.*`). The argument lists below are the ones a rig needs; the plugin's `SKILL.md` has
every argument, the refusals and the return values.

## 1. Design: `scripts/krea.py`

```bash
PY=ComfyUI/venv/bin/python   # any Python with Pillow, numpy and SciPy
$PY scripts/krea.py "<prompt>" --name hero --no-style --pixel 64 [--seed N] [--colors 14]
```

- Writes `out/krea/hero_raw.png` (1024 px, background removed) and `hero_px.png` (snapped to its grid, cropped,
  reduced to `--colors`). Import `_raw.png` into the plugin: the reduction in `_px.png` drops small accents.
- Prompt for a rig: full body, the view you will animate (side view for fighters, front or three-quarter otherwise),
  arms slightly away from the body, held items clear of the face and torso, feet apart, a plain white background.
  Name every clothing layer, colour and item, and say which hand holds what ("a sword in the hand on the right side
  of the picture"). Name accent colours, or they are quantised away.
- Try 2-4 seeds; pick the one whose parts are easiest to separate, not the prettiest.

## 2. Onto the grid

Create an indexed document with room for the poses (the trailer cast used 128 x 96 for a 64-grid design).

| Verb | Arguments that matter |
|---|---|
| `pas.palette.fromImage` | `png` (the `_raw.png`), `cell: 16`, `count`: proposes colours darkest first; add the ones you keep with `pas.palette.addEntry` |
| `pas.palette.ramp` | `name`, `entries` darkest first; `emissive: true` for eyes, fire, lamps |
| `pas.layer.importPng` | `path`, `cell: 16`, `match: "lab"`, `ramps` (the character's), `x`, `y` (feet a few pixels above the canvas bottom); leave `phase` out |
| `pas.render.frame` | `frame: 0`, `out`: the reference PNG every later check compares with |

Add a ramp when a colour lands between two (speckled fins between stone and water).

## 3. Peel

| Verb | Arguments that matter |
|---|---|
| `pas.layer.add` | one empty layer per piece, `name`, `index` (build the whole tree first, then read `pas.read.document` for the indices) |
| `pas.frame.duplicate` | copy frame 0 before filling: the copy is settle's `partitionFrame` |
| `pas.layer.peel` | `layer` (the design), `frame`, and per row `targets[i]`, `polygons[i]` (flat x, y list; empty = the whole canvas), `entries[i]` (palette entries; empty = any). Rows are taken front-most first, each minus what earlier rows took. Indexed documents only. |
| `pas.selection.shape` + `pas.selection.move_to_layer` | the same, one piece at a time: `polygon`, `and` (the piece's colours), `minus` (pieces already taken); then `createNewLayer: true` |
| `pas.check.tears` | `frame`, `pieces`: each piece's stray specks and the piece each belongs to |
| `pas.read.diff` | `frame: 0`, `png` (the reference): must answer `identical: true` |

Polygon points are integers: round a measured half-pixel vertex yourself.

## 4. Complete the pieces

| Verb | Arguments that matter |
|---|---|
| `pas.pixels.shadeFill` | `layer`, `frame`, `selection` (the region the piece hides, from `pas.selection.shape`), `ramp`, `stepFrom` / `stepTo`, `lightFrom`; fills only empty pixels |
| `pas.pixels.extend` | `layer`, `frame`, `by` (1-16: the pivot-to-edge reach times the sine of the largest turn, plus one), `states`, `skipEntries` (the outline ink) |
| drawing verbs | `pas.pixels.set`, `pas.draw.*` for what a fill cannot make: a grip inside a fist, the cape's hidden middle |
| `pas.layer.settle` | `reference`, `x`, `y`, `frame: 0`, `partitionFrame`, `pieces`; `adoptFragments: false` for a piece made of several parts (a pair of wings) |
| `pas.render.layers` | `frame: 0`, `scale: 4`, `out`: one cell per layer, to look at each piece alone |
| `pas.frame.remove` | the partition frame, once settle has succeeded |

A piece that must stay hidden under another goes on a layer below it, or settle drops its fill. A hidden fill lies
under the piece that rides the same bone (a forearm's skin under its glove, not under the torso).

## 5. Rig

| Verb | Arguments that matter |
|---|---|
| `pas.layer.group` | `layer`, `name`: wraps a piece in a group; the group is the bone, its children follow it |
| `pas.layer.add` | `name`, `parent` (a group), `index` among its children |
| `pas.layer.move` | `layer`, `to`, `parent` |

Joints are pixel-edge points measured on the design: the middle of the pixels where two pieces overlap (rows 51 and
52 meet at y 52; the middle of column 19 is x 19.5).

## 6. Keyframes

| Verb | Arguments that matter |
|---|---|
| `pas.frame.duplicate` | `frame` (the rest frame), `poses: true` to keep poses |
| `pas.pose.set` | `layer` (a piece or a group), `frame`, `angle` (clockwise on screen), `pivotX` / `pivotY` (the joint), `x` / `y` |
| `pas.pose.reach` | `upper`, `lower`, optional `hand`, `frame`, the rest joints `rootX/Y`, `midX/Y`, `endX/Y`, the `targetX/Y` for the end, `rootToX/Y` when the root moved |
| `pas.pose.bake` | `layers`, `frames`: turns the posed pixels cleanly (RotSprite) into the cels and clears the poses |
| `pas.transform.free` | `layer`, `frame`, `angle`, `pivotX/Y`, `toX/Y`: one exact turn, baked at once |
| `pas.transform.bend` | `layer`, `frame`, `anchorX/Y` (where the cloth is tied), `reach`, `bend`, `wave`, `phase`: cloth without tearing rows apart |
| `pas.check.pose` | `frame`, `turns` (7 numbers each, as `pas.transform.free` takes them), `bends`: tries a pose without changing the document |
| `pas.draw.outline` | `layer` (an outline layer), `frame`: one ink ring round the silhouette, last |
| `pas.check.tears` | `frame` or `tag`: pinholes and extra islands; `hiddenEntries` for fill colours that must not show |

A pose is a nearest-neighbour preview; bake it once the frame reads right. Bake a group, not a layer inside a posed
group.

## 7. In-betweens and tags

| Verb | Arguments that matter |
|---|---|
| `pas.frame.duplicate` | a key, then turn its pieces part of the way to the next key (ease in and out) |
| `pas.frame.clean` | `frame`, `states`, `maxFill`, `skipEntries`, `hiddenEntries`: fills pinholes and drops stray specks |
| `pas.frame.duration` | `frame`, `durationMs`: hold the extremes a frame longer |
| `pas.tag.add` | `name`, `from`, `to`, `direction` (`Forward`, `Reverse`, `PingPong`), `loops` |
| `pas.render.tag` | look at a whole tag as a strip |
