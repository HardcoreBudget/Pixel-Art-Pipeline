# Ashen Peak: a one-round 2D arcade fight

Genre reference: Mortal Kombat (1992 onward) and the 2D arcade fighter in general:
- a side-view one-on-one fight on a single stage that scrolls with the fighters, with parallax layers behind;
- health bars and a round timer at the top, round-win medallions, and "ROUND 1" / "FIGHT!" / "K.O." / "WINS"
  call-outs;
- combo counters, hit sparks, block sparks and knockdowns.

The cast, stage, moves and UI are original.

- **View:** 256 × 144, shown at 4×. The stage is 400 px wide; the camera follows the midpoint between the fighters.
- **Fighters:** 64-grid designs on a 128 × 96 canvas, the design at offset (32, 28), feet at (64, 88). P2 is mirrored.
- **Ticks:** 80 ms, giving a loop of about 45 s.

## Stage: Ashen Peak Temple at dusk (parallax, back to front)

| Layer | Scroll | Contents |
|---|---|---|
| sky | 0 | A dithered dusk gradient and a low red sun. |
| far peaks | 0.15 | Silhouettes. |
| near peaks | 0.3 | Silhouettes with snow caps catching the sun. |
| temple | 0.6 | A pagoda with curved jade roofs, glowing lanterns that sway, cloth banners bent by `twist()`, and a stone gate. |
| courtyard floor | 1.0 | 16 px stone flags, receding bands. |
| foreground | 1.25 | Plum branches with petals at the top corners. |

Particles: sakura petals drifting in the wind, and embers from the braziers.

## Cast

- **Riku** (fast, kick-based monk). Moves: stance, walk, jab, roundhouse, sweep, jump, flying kick, uppercut,
  **Sun Palm** (a fireball projectile), block, hit, knockdown, get-up, launch, victory.
- **Grimhold** (heavy, armoured brute). Moves: stance, walk, hook, **shoulder charge**, **ground slam** (a travelling
  shockwave), uppercut, roar, block, hit, knockdown, get-up, defeat.

## Beats

1. **Intro:** the camera pans, then ROUND 1, FIGHT!
2. **Opening:** both fighters walk in.
3. **Riku's combo:** jab, jab, roundhouse, "3 HITS".
4. **Grimhold answers:** a hook that Riku blocks, then a shoulder charge that knocks him down; he gets up.
5. **Ground slam:** Grimhold slams, Riku jumps the shockwave and lands a flying kick.
6. **Sun Palm:** Riku's fireball hits Grimhold.
7. **Grimhold's uppercut** launches Riku, who falls and gets up.
8. **Sweep:** Riku sweeps, Grimhold goes down and gets up.
9. **Finale:** Grimhold charges again, Riku leaps over and lands the Thousand Suns barrage (4 palm hits, then a flaming
   uppercut). K.O., a hit-freeze, Grimhold falls, RIKU WINS, fade, loop.

## The rules from the skill

- Limbs are design pieces turned about their joints.
- Cloth bends only by `twist()`.
- Walks and runs are keyed cycles.
- Weapons and striking limbs stay outside the body's silhouette.
- Every frame is reviewed zoomed against the checklist.
