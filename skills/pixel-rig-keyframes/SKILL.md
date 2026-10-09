---
name: pixel-rig-keyframes
description: Use when turning a pixel-art character design into a rig and key poses in the Pixel Art Studio Unity plugin -- a Krea 2 design (scripts/krea.py) as the reference, then peeling it into complete layers (hidden parts drawn in), measuring the joints and posing the keyframes at pixel level with the plugin's verbs.
---

# Rig layers and keyframes in Pixel Art Studio

Krea 2 draws one still picture of the character. Everything after that happens in Pixel Art Studio, at pixel level,
with the plugin's verbs: the layers, the parts the body hides, the joints and every pose. The design stays the
reference the whole way: each piece is cut from its pixels, and the rest frame must equal it exactly.

You make two things, in this order:

1. **Complete rig layers.** The character split into the parts that move on their own (sword, shield, each arm, head,
   each leg, cape, tail, wings ...), each a WHOLE layer, including what the rest of the body hides: the grip inside
   the fist, the shoulder under the pauldron, the cape behind the torso. A turned part reveals whatever was behind it;
   an incomplete layer shows a hole there. This is the step that takes the most care.
2. **Keyframes.** The key poses of each action (wind-up / swing / follow-through / recover; contact / passing;
   take-off / apex / land ...), made by turning the design's pieces about their joints. The in-betweens come last.

The plugin's own reference is `Assets/PixelArtStudio/SKILL.md` in a project with the plugin installed. Read its
"Building a character (start here)" section and the sections it names before the first call. For whole scenes
(tiles, effects, lighting, UI) use the `pixel-scene` skill; the same rig built in Python is in `scenes/`
(`scenes/drowned_shrine/kestrel.py`, `scenes/ashen_peak/riku.py` and `grimhold.py` cut the layers and fill what they
hide; `scenes/ashen_peak/rig.py` poses them).

## The rule that matters most

**Peel before you animate.** Decide the rig (which parts move independently), peel it, check every layer is whole,
and only then pose keyframes. Poses without a rig force you to redraw every frame, which drifts; a rig with holes
breaks the moment a limb moves.

## Workflow

| Stage | How | Gate before moving on |
|---|---|---|
| 1. Design | `python scripts/krea.py "<detailed prompt>" --name hero --no-style --pixel 64` (2-4 seeds) | Whole body, the view you will animate, parts clearly separated, held items clear of the face |
| 2. Onto the grid | `pas.palette.fromImage`, `pas.palette.ramp`, then `pas.layer.importPng` with `cell: 16`, `match: "lab"`, `ramps` | The layer reads as the design; render it once (`pas.render.frame`) as the reference PNG |
| 3. Peel | `pas.layer.peel` (a polygon and colour entries per piece, front-most first); `pas.check.tears` with `pieces` | Every design pixel is in exactly one piece; `pas.read.diff` against the reference says `identical` |
| 4. Complete the pieces | `pas.pixels.shadeFill` toward each joint, `pas.pixels.extend` under the covers, hand drawing where a fill is not enough; then `pas.layer.settle` | Settle succeeds (the stack equals the design); every layer alone is whole (`pas.render.layers`) |
| 5. Rig | Groups are bones (`pas.layer.group`); measure each joint on the design in pixel-edge coordinates | A written joint list: hip, knee, ankle, shoulder, elbow, neck, item grip |
| 6. Keyframes | Duplicate the rest frame (`pas.frame.duplicate`), turn the pieces (`pas.pose.set` then `pas.pose.bake`, or `pas.transform.free`), two-bone limbs with `pas.pose.reach`, cloth with `pas.transform.bend`; try poses with `pas.check.pose` | Each key: the same character, items in the right hand, 0 pinholes and 0 extra islands (`pas.check.tears`) |
| 7. In-betweens and tags | Duplicate the keys, turn the pieces part of the way, `pas.frame.clean`, `pas.frame.duration`, `pas.tag.add` | Every frame passes stage 6's gate; look at each tag as a zoomed strip |

The verbs and their arguments per stage: references/commands.md. Part lists and peel order for a knight, a dragon,
a fox and a slime: references/rig-specs.md. Sessions, the layer tree, bringing in layers drawn elsewhere, and
in-betweening: references/plugin-import.md.

## Environment

- `krea.py` needs ComfyUI running (`scripts/start_comfy.sh`; `curl -s http://127.0.0.1:8188/system_stats` answers).
  A 1024 px design takes about 7 minutes on a 4 GB GPU. Run one GPU job at a time. Kill processes by PID, never by
  pattern (`pkill -f` matches your own shell).
- Ask before touching a Unity Editor someone else has open; another agent may be using it. Work on your own
  document, or on a headless copy of the project.
- Keep each `execute_code` call short (under about 90 seconds) and idempotent: a call that times out is sent again
  and the Editor runs both copies.

## Deciding the rig

- One layer per part that moves on its own in ANY planned action. A slash needs the sword arm separate from the body;
  a walk needs each leg; a flap needs each wing.
- Cut each limb into rigid pieces that turn about joints: thigh, shin, foot or boot; upper arm, forearm with the fist.
  A limb that only swings whole can stay one piece.
- Held items are their own layers, inside the group of the arm that holds them, so they follow the arm.
- Accessories that sway (cape, scarf, tail, ponytail) are their own layers and are bent, not turned; hats and beards
  stay on the head.
- Peel the outermost first: items in front, then limbs in front, then the head, then limbs behind, then things
  behind the body (cape, far wing). What remains is the torso.

## Peeling and completing a part

1. **Name sides by the picture**, not by the character: `arm_near` / `arm_far`, or "the arm on the right of the
   picture". The character's own left and right get mixed up as soon as it faces the other way.
2. **One part per piece.** "Both legs" makes one layer; the rig needs one per leg.
3. **Take the whole anatomy.** A head piece is the face, the ears and the hair, everything above the collar; a leg is
   the trouser leg from the hip down and the boot. After each body part, look at the piece and at what is left.
4. **Keep the holder.** A held item's piece is the item only; the hand stays on the arm. Draw the hidden grip on the
   item's layer, inside the fist, so the item can turn in the hand.
5. **Draw what the part hid.** When the arm comes off, the torso needs the side of the breastplate and the cape beside
   the body; when a leg comes off, the lower edge of the tabard. Paint it on the piece that owns it, in that piece's
   ramp (`pas.pixels.shadeFill`), toward the joints it turns about. Only the design's view: never draw the back of
   something the front view does not show.
6. **Fill toward the joints and overlap them.** The thigh up under the skirt to the hip, the shin up inside the knee,
   the torso down under the belt. Size `pas.pixels.extend`'s `by` to the largest turn the joint must survive.

## Quality gates (check them, don't assume)

- **The stack equals the design.** `pas.layer.settle` (the reference PNG, `frame: 0`, the peeled copy as
  `partitionFrame`) succeeds, and `pas.read.diff` with the reference answers `identical: true`. Read what settle
  adopted or dropped: a part of the design taken for a stray fragment shows up there.
- **Every layer alone is whole.** Render the layer sheet (`pas.render.layers`, scale 4-6) and look at every cell. A
  layer with a hole where a neighbour covered it needs more fill.
- **No piece holds a chunk of a neighbour** (chest pixels in the arm layer). `pas.check.tears` with `pieces` names the
  stray specks and the piece each belongs to; move them there.
- **A big turn shows flat fills.** Pass the fill colours as `hiddenEntries` to `pas.check.tears`, and look at a zoomed
  render of each candidate pose.
- **Keyframes.** The rest frame equals the design. Every frame has 0 pinholes and 0 extra islands. Limbs keep the
  design's length (they are turned, never redrawn); only what has no fixed shape (a blade at a new angle, a smear) is
  drawn new. Reject a pose that hides the hands under the head or loses the held item inside the body's silhouette.
- **Look at every frame**, zoomed 5-6x beside the design (`pixel-scene`'s `references/qa-checklist.md` is the list).
