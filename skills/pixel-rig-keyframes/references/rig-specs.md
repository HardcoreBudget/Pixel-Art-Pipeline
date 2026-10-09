# Rig specs

A rig spec is three lists, written down before the first peel: the pieces in peel order (front-most first), the joint
each piece turns about, and what each piece must have drawn in because another piece hides it. Name pieces by the
picture's sides (`arm_near` / `arm_far`, or left and right of the picture).

## Order: outermost first

Each peel row takes a part from what is left, so a part must be fully visible (or covered only by parts already
taken) when its turn comes: front items, front limbs, the head, back limbs, then things behind the body (cape, far
wing, a tail behind). What remains is the torso.

## Groups and joints

Each bone is a group. A limb is a group holding its pieces (upper arm, then a forearm group holding the forearm and
the held item), so a pose on the shoulder carries everything below it. Measure each joint on the design: the middle
of the pixels where the two pieces overlap, in pixel-edge coordinates.

## Example rigs

### Knight (front view, sword and round shield)

| Piece | In the group of | Turns about | Draw in where it was hidden |
|---|---|---|---|
| `sword` | the sword arm's forearm | the grip | the grip inside the fist |
| `shield` | the shield arm's forearm | the grip | nothing; draw the gauntlet, forearm, armour and tabard it covered on those pieces |
| `arm_right`: pauldron and upper arm, forearm with gauntlet | torso | shoulder, elbow | the shoulder under the pauldron; on the torso, the side of the breastplate and tabard and the crimson cape beside the body |
| `arm_left`: as `arm_right` | torso | shoulder, elbow | as `arm_right` |
| `head`: face, hair, ponytail | torso | neck | the top of the armour collar, on the torso |
| `leg_right`: thigh, shin, boot | torso | hip, knee, ankle | the thigh top under the tabard; on the torso, the lower edge of the tabard and armour, and the cape behind |
| `leg_left`: as `leg_right` | torso | hip, knee, ankle | as `leg_right` |
| `cape` | torso | the neck clasp (bent, not turned) | the whole cape behind the torso |
| `torso` | (root) | the hips | what every piece above it hid |

### Dragon (round body, small arms, wings)

| Piece | Turns about | Draw in where it was hidden |
|---|---|---|
| `smoke` (an effect, its own layer) | (moves, does not turn) | the wing behind it |
| `wing_left`, `wing_right` | the wing root | the green shoulder on the torso; the wing root under the body |
| `tail` | the tail root (bent) | the body and leg where the tail crossed them |
| `arm_left`, `arm_right`: small arms and claws | shoulder | the cream belly and green side of the body |
| `head`: with the horns | neck | the top of the round body |
| `leg_left`, `leg_right`: leg and clawed foot | hip | the bottom of the round body |
| `torso` | (root) | |

### Fox (side view, four legs, scarf)

| Piece | Turns about | Draw in where it was hidden |
|---|---|---|
| `tail` | the tail root (bent) | the hind quarters and back legs |
| `scarf` | the knot (bent) | the cream-white fur of the neck and chest |
| `leg_front_near` | shoulder | the far front leg and the chest fur behind it |
| `leg_hind_near` | hip | the far back leg and the belly fur behind it |
| `leg_front_far` | shoulder | the underside of the chest where it joins |
| `leg_hind_far` | hip | the underside of the belly where it joins |
| `head`: ears and snout | neck | the neck fur |
| `body` | (root) | |

The far legs can be drawn from the near legs' pieces, one ramp step darker, when the design foreshortens them.

### Slime (no limbs)

| Piece | Moves how | Draw in where it was hidden |
|---|---|---|
| `skull`, `coins`: things inside the jelly | ride the body, a pixel or two of lag | clear translucent jelly where they were |
| `eyes`, `mouth` | ride the body; blinks and mouth shapes are drawn | smooth jelly where they were |
| `puddle`: the flat jelly at the base | stays on the floor | the round body ends at the floor |
| `body` | squash and stretch: `pas.transform.free` with `scaleX` / `scaleY` about the point where it touches the floor | |
