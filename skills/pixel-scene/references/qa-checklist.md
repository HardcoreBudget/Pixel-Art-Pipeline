# Frame review checklist

Review every frame zoomed 5–6×, beside the design and beside the previous frame. A frame passes only if all of
these hold.

## Integrity (no tears)

- [ ] No hole inside a part. Scan each frame for transparent pixels enclosed by one character's pixels, and for
      background showing through cloth or skin.
- [ ] No floating pixels: no 1–3 px islands apart from the body (except intentional sparks).
- [ ] Every joint is covered: knee, ankle, elbow, shoulder, hip. The piece above overlaps the piece below; no notch,
      no gap.
- [ ] Cloth is one continuous shape: no horizontal strips, no stringy rows.
- [ ] The outline is closed. One ink ring goes around the silhouette, and internal outlines come from the design
      pieces.

## Fidelity

- [ ] Idle frame 0 equals the design, apart from redrawn props.
- [ ] Every piece still reads as itself: boots keep their cuffs, gloves their knuckles, the face its eyes.
- [ ] No limb is longer or shorter than in the design (IK uses the design's bone lengths).
- [ ] The palette holds: only scene ramp colours, no blends.

## Motion

- [ ] Arcs: hands, feet and weapon tips travel on arcs across frames, not zigzags.
- [ ] Weight: the body is lowest just after a landing or contact and highest at push-off or apex.
- [ ] Planted feet stay planted (±0 px) on grounded frames.
- [ ] Anticipation before big moves, and follow-through with overshoot after.
- [ ] Silhouette: the move reads as a black shape. The weapon and striking limb are outside the body's outline.
- [ ] Nothing important sits under or on the face.

## Scene

- [ ] Contacts connect: the strike reaches the target on the contact frame.
- [ ] Effects sit on the contact point, and damage numbers don't overlap.
- [ ] UI states match the action (bars drain after hits, prompts time with the hit).
- [ ] The loop closes: frame N−1 leads into frame 0.
- [ ] The plugin renders equal your frames for every document.
