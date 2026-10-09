#!/usr/bin/env bash
# The Drowned Shrine: the Krea 2 designs (design only; the agent drew everything after them).
# Run from the repository root with ComfyUI running (scripts/start_comfy.sh). PY = a Python with Pillow, numpy, SciPy.
# Outputs go to out/krea/<name>_raw.png and _px.png. The picked designs are already in scenes/designs/
# (kestrel_9101, gloomlure_9402); a seed reproduces a picture only on the same hardware, drivers and ComfyUI version.
set -euo pipefail
cd "$(dirname "$0")/../.."
PY=${PY:-ComfyUI/venv/bin/python}
HERO="An original hero for a pixel art RPG battle: Kestrel, a young swordswoman, full body, side view facing right, battle-ready stance with feet apart and knees bent, a short curved silver sword held low and forward in her front hand, both arms held clear of the body, a long crimson red scarf trailing behind her, short teal cloak over a cream tunic, brown belt, brown gloves and boots, short dark brown hair. Simple bold shapes, flat colours, a limited palette of about 12 colours with crimson red, teal, cream and silver as accents, clean dark outline, readable silhouette, plain white background."
BOSS="An original boss monster for a pixel art RPG battle: the Gloomlure, a large floating deep-sea anglerfish spirit, side view facing left, huge round head with wide open jaws and jagged white teeth, a glowing yellow lantern lure dangling from a curved stalk on its forehead, one small glowing cyan eye, deep indigo body with a pale lavender belly, ragged translucent blue fins and a wispy tail, floating in the air. Simple bold shapes, flat colours, a limited palette of about 12 colours with glowing yellow and cyan as accents, clean dark outline, readable silhouette, plain white background."
ENV="Pixel art RPG battle arena seen from a top-down three-quarter view, a flooded stone shrine courtyard at night: cracked grey-blue stone floor tiles, shallow teal water pools with ripples, broken moss-covered stone pillars, hanging vines, clusters of glowing cyan mushrooms, two stone braziers with orange fire, moonlight, cohesive limited palette, empty arena, no characters, no text, no user interface."
for s in 9101 9202; do $PY scripts/krea.py "$HERO" --name kestrel_$s --seed $s --pixel 64 --no-style --colors 14; done
for s in 9301 9402; do $PY scripts/krea.py "$BOSS" --name gloomlure_$s --seed $s --pixel 64 --no-style --colors 14; done
# a mood reference for the arena (not used as pixels) and a 128-grid trial of the boss (not picked)
$PY scripts/krea.py "$ENV" --name shrine_env_9501 --seed 9501 --pixel 128 --no-style --colors 32
$PY scripts/krea.py "$BOSS" --name gloomlure128_9601 --seed 9601 --pixel 128 --no-style --colors 16
