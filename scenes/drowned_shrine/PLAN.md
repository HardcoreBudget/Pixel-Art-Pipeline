# The Drowned Shrine: a looping battle scene

Genre reference: Sea of Stars (2023) turn-based battles: a hand-built arena, readable fighters, locks over a
charging enemy, timed hits and blocks, pixel UI. Characters, setting and UI are original.

- View 320 x 180, tiles 16 px (map 20 x 12, the last 12 px cropped), fighters on 64 x 64 canvases.
- One tick = 80 ms (12.5 fps); tiles animate every 2 ticks.
- Palette: `px.RAMPS` (15 ramps). Lighting = integer steps along ramps with Bayer dither (`light.py`).
- Layers, back to front: ground tiles, deco tiles, shadows, boss reflection (in water only), fighters (y-sorted),
  effects, front tiles (ferns), lighting pass, UI (unlit), fade.

## Cast

- **Kestrel** (humanoid): a swordswoman with a crimson scarf and a teal cloak. Home: feet at (70, 136), facing right.
- **Gloomlure** (non-humanoid): a floating anglerfish spirit with a glowing lure. It hovers over the pool at
  about (228, 112), facing left. HP 120.

## Beats (ticks)

| ticks | beat |
|---|---|
| 0-45 | Fade in. Bubbles in the pool, rings, a plume. The Gloomlure rises out of the water. Banner "A GLOOMLURE RISES FROM THE DEEP!" The plates slide in. |
| 46-100 | Kestrel's turn. The menu opens and the cursor goes ATTACK, SKILL, ATTACK, then selects. She runs in. Slash 1 hits for 14. Slash 2 is a timed hit: PERFECT!, 21. She hops back. Boss 120 -> 85. |
| 100-170 | The boss's turn: "ABYSSAL BITE". It winds up and lunges with its jaws open; Kestrel makes a timed BLOCK! and takes 8 (150 -> 142). The boss returns and starts charging: the scene darkens, the lure blazes, and the locks [SWORD][SUN][SUN] appear one by one. |
| 172-250 | Kestrel's turn. Menu: SKILL, then DAWN CLEAVE (12 MP, 30 -> 18). She runs in. The slash breaks the sword lock (12). She leaps and plunges, with a sunburst. Both SUN locks shatter: BREAK!, a flash and a shake, 73. The charge is cancelled and the boss is stunned. She hops home. Boss 85 -> 0. |
| 250-320 | The boss flickers and dissolves into light motes; its lure falls into the pool. Kestrel's victory pose. Banner VICTORY; panel EXP +120, GOLD +45. |
| 320-336 | Fade to black; loop. |

## Frames to draw

- **Kestrel:** idle 6, run 6, slash1 5, slash2 5, hop back 4, block 3, leap 4, plunge 3, victory 6.
- **Gloomlure:** idle 6, wind-up 2, lunge 3, hurt 2, charge 4, stunned 4. Its death is an effect (motes).
