#!/usr/bin/env bash
# Ashen Peak: the Krea 2 designs (design only; the agent drew everything after them).
# Run from the repository root with ComfyUI running (scripts/start_comfy.sh). PY = a Python with Pillow, numpy, SciPy.
# Outputs go to out/krea/<name>_raw.png and _px.png. The picked designs are already in scenes/designs/
# (riku_7101, grimhold_7301); a seed reproduces a picture only on the same hardware, drivers and ComfyUI version.
set -euo pipefail
cd "$(dirname "$0")/../.."
PY=${PY:-ComfyUI/venv/bin/python}
RIKU="An original fighter for a pixel art 2D fighting game: Riku, a young martial arts monk, full body, side view facing right, fighting stance with both fists raised in front of the chest, legs apart and knees bent, both arms clearly separated from the body, bare muscular forearms, a sleeveless saffron orange gi top with a dark brown belt, loose black trousers tucked into cloth shin wraps, bare feet, a red headband with two long trailing tails, short spiky black hair. Simple bold shapes, flat colours, a limited palette of about 12 colours with saffron orange, red and black as accents, clean dark outline, readable silhouette, plain white background."
GRIM="An original fighter for a pixel art 2D fighting game: Grimhold, a huge armored warlord, full body, side view facing right, heavy fighting stance with big iron gauntlet fists raised, legs wide apart, both arms clearly separated from the body, a horned iron helmet covering the face with two glowing amber eye slits, massive round shoulder pauldrons, dark iron armor plates over a crimson tunic, a short fur waist cloth, heavy iron boots. Simple bold shapes, flat colours, a limited palette of about 12 colours with iron grey, crimson and glowing amber as accents, clean dark outline, readable silhouette, plain white background."
for s in 7101 7202; do $PY scripts/krea.py "$RIKU" --name riku_$s --seed $s --pixel 64 --no-style --colors 14; done
for s in 7301 7402; do $PY scripts/krea.py "$GRIM" --name grimhold_$s --seed $s --pixel 64 --no-style --colors 14; done
