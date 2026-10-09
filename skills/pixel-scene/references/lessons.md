# Lessons: what went wrong, and what fixed it

Each entry gives the symptom the reviewer saw, the cause, and the fix now in the code.

## Characters

1. **The limbs "crumble and look awful".** Legs and arms were redrawn every frame as shaded capsules in the
   design's ramps. The design's knees, cuffs, highlights and internal outlines were lost, and the limbs merged into
   one brown mass.
   **Fix:** cut the limbs from the design into pieces (thigh, shin, boot; forearm with the glove), paint what each piece
   hides, and turn each piece about its measured joint with RotSprite and IK.
2. **The run "isn't how legs should run in games".** The feet traced a ±5 px ellipse under the hips, which reads as a
   shuffle.
   **Fix:** an 8-frame keyed stride: contact (heel forward, toe up), down (lowest), passing, push-off (toe down),
   heel kick behind, tuck, knee up, reach. Feet go about ±9 px from the hip; the far leg is the same four frames later.
3. **The far leg can't stride.** The design drew it foreshortened for a lunge stance: thigh plus shin was 10.8 px
   against the near leg's 12.7.
   **Fix:** in the run, draw both legs from the near leg's pieces, the far one a ramp step darker. It is a common
   sprite convention.
4. **The cape "tears apart".** Each row was shifted forward on its own; lifting or stretching separated the rows.
   **Fix:** `twist(img, anchor, reach, bend, wave, phase)`. For each OUTPUT pixel, rotate back about the anchor by an
   angle that grows with distance, then sample an 8× Scale2x copy. Every output pixel gets a source pixel, so nothing
   can tear.
5. **Hands hidden in overhead poses.** The arms were drawn under the head to keep them off the face, and the pose
   read as a sword with no hands.
   **Fix:** raise the weapon to the right of the face and keep the arms on top.
6. **The sword vanishes in the run.** A blade trailing behind a leaning body stays inside the silhouette.
   **Fix:** carry it low and forward, so the silhouette tells the story.
7. **Stray pixels near the head.** Blade pixels sat inside the head's mask, and the blade part was later dropped.
   **Fix:** own props by colour AND region, and scan the other parts for the prop's colours.
8. **Blinks that don't close.** The eyeball's black belonged to other layers, so recolouring the eye layer left the
   eye half open (the crab).
   **Fix:** draw a lid over the whole eyeball.

## Designs

9. **Krea's `_px` output is garbled** (noisy faces, merged colours).
   **Fix:** `repix.py`. The raw image already sits on the LoRA's 16 px grid: find the phase, take each cell's mode,
   and map it to the scene palette.
10. **A 12-colour Krea design loses unnamed accents** (the crab's lava).
    **Fix:** name the accent colours in the prompt.
11. **Colours between two ramps come out speckled** (the fins between stone and water).
    **Fix:** add a ramp for that hue and restrict the mapping to the ramps that character uses.

## Scene

12. **Damage numbers overlap** when two hits land within the pop's lifetime.
    **Fix:** offset the second hit and shorten the lifetime.
13. **The fighter doesn't reach the target.** Check the distance to the target on the contact sheet, not by
    arithmetic.
14. **Night lighting muddies the fighters.** Give fighter pixels a darkness floor (−0.4 steps). Emissive ramps
    (fire, glow) never darken, except in a fade to black.
15. **Stale assumptions about the canvas.** When a sprite canvas changes size, grep the scene for the old offsets
    (`- 32`).

## Tools

16. **Stopping ComfyUI removes its transient unit** (`DETACH=1 start_comfy.sh` uses `--collect`), so
    `systemctl --user start` then fails.
    **Fix:** start it again with `start_comfy.sh`.
17. **`settle` drops hidden fills on the top layer**, because nothing covers them.
18. **`partition diff` can be circular** if the reference is rebuilt from the layers themselves. Keep the real
    design and compare against it.

## From the fighting scene (Ashen Peak)

19. **Fragments appear after `settle`.** A hidden fill can join a stray pixel to its piece; `settle` then removes
    the joining pixels and strands it, so it hangs in the air when the limb moves.
    **Fix:** `rig.adopt_fragments(L, order=ORDER)` AFTER `settle`. A covered fragment pixel is leftover fill and is
    deleted; a visible one moves to the piece it touches (empty pixels only). The stack must still equal the design.
20. **Check that each character is one shape, not just free of specks.** A floating fragment picks up its own
    outline and grows past any "speck" size. `rig.holes()` now returns (pinholes, extra islands). Both must be 0 on
    every frame.
21. **Pinholes versus intended gaps.** The design itself has enclosed gaps (the space inside a bent arm). Only
    1–4 px enclosed pockets are tears. The outline ring can strand such pockets in narrow notches, so the rig closes
    them with ink.
22. **The waist wedge.** A torso that leans about the waist opens a wedge against a pelvis that doesn't lean.
    **Fix:** layer the belt and skirt OVER the torso and extend the torso's hidden fill down under them.
23. **Spin before assembly.** Turning the finished frame (knockdowns) strands new pinholes after the clean-up.
    Turn the pieces, then assemble and outline.
24. **Lying on the floor.** A spun body sinks through the ground. The `ground` pose flag puts its lowest pixel on
    the ground line.
25. **Chibi proportions (a big head, short limbs).**
    - A kick reaches only knee height. Tip the WHOLE body back about the planted foot (`spin` with that foot as the
      pivot), so the straight leg rises to head height. Add a swoosh effect.
    - The far arm can't reach past a big head: keep punches at chest height, and use the LEAD arm for uppercuts and
      victory fists, clear in front of the face.
    - A sweep needs a real drop (hips down about 11 px, a hand on the floor).
26. **Dark trousers merge the legs** into one black mass in crouches. Pose so the striking leg's silhouette clears
    the body.
27. **Spacing in choreography.** Place fighters by their body fronts, not their centres: bodies overlapping on a
    contact frame read as a smudge. Check every contact on a contact sheet.
28. **Fallen fighters "still floating above the ground".** The ground snap rested the lowest pixel of ANYTHING on
    the floor: the headband tails or a hanging gauntlet. The body floated 8–10 px above the stones.
    **Fix:** the `ground` flag rests only the weight-bearing pieces (`SPEC["support"]`: head, torso, pelvis, legs),
    and cuts anything that would pass below the floor, with an ink line where the cut crosses the body.
    In lying poses:
    - **Stack the legs**, since a wide stance puts one hip high above the other on the back (the near leg reaches
      down across to the floor).
    - **Angle the legs down to the floor from the hips**, since a thick torso lifts the hips.
    - **Lay the hands along the body**, not raised.
    Check against a standing fighter's feet line in the scene, not only the sprite's own ground line.
