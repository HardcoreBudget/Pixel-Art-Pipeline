#!/usr/bin/env bash
# The six Pixel Art Studio trailer cast designs: Krea 2 Turbo + the 64-grid pixel LoRA (krea.py --pixel 64), the
# prompts and seeds the final designs were made with. Each design was made with two seeds and one was picked; the
# picked seed is the one run here (the other is in the comment). Skips designs that already exist.
#
#   scripts/trailer_cast.sh                 writes out/trailer_cast/<name>_s<seed>_{raw,px}.png
#   OUT=/some/folder scripts/trailer_cast.sh
#
# ComfyUI must be running (scripts/start_comfy.sh). About 7 min per design on a 4 GB laptop GPU.
# The same seed on different hardware, drivers or ComfyUI versions may not give the same picture.
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PYTHON:-python3}
OUT=${OUT:-$HERE/../out/trailer_cast}
mkdir -p "$OUT"
COMMON="Full body, side view facing right, standing, limbs clearly separated from the body, flat colours, a limited palette, a dark 1-pixel outline, chunky 16-bit game sprite, plain white background."
# Round 2 (brash2, glob2) dropped "standing" from the common suffix:
COMMON2="Full body, side view facing right, limbs clearly separated from the body, flat colours, a limited palette, a dark 1-pixel outline, chunky 16-bit game sprite, plain white background."
run() { # name seed prompt suffix
  if [ -f "$OUT/$1_s$2_raw.png" ]; then echo "skip $1 $2"; return; fi
  echo "=== $1 seed $2 $(date +%T)"
  "$PY" "$HERE/krea.py" "$3 $4" --name "$1_s$2" --pixel 64 --no-style --colors 14 --seed "$2" --out "$OUT" \
    || echo "FAILED $1 $2"
}
# picked 4102 (other seed 4101)
run sir_stacks 4102 "A chibi knight. Steel plate armour with a royal blue tabard, a tall red plume on the helmet, a short royal blue cape, brown leather gauntlets and boots. Proud stance, chest out." "$COMMON"
# picked 4102 (other seed 4101)
run pip 4102 "A small young courier. A teal hoodie with a square chest pocket, round black glasses, a long red scarf trailing behind, a brown messenger bag on a strap, white sneakers, messy brown hair." "$COMMON"
# picked 4102 (other seed 4101)
run bonk 4102 "A mossy stone golem, much taller and wider than a person, glowing amber eyes, huge boulder fists, green moss on its shoulders and head, heavy stone legs. Slow and smug." "$COMMON"
# picked 4101 (other seed 4102)
run mira 4101 "A small painter girl. A plum beret, a cream smock with colourful paint dots, ginger hair, holding a giant yellow pencil with a pink eraser end like a staff." "$COMMON"
# picked 4201 (other seed 4202)
run brash2 4201 "A cocky young brawler in a fighting stance, fists up. A tall spiky orange mohawk, a purple bandana tied round the forehead with two long trailing tails, a sleeveless lime green tank top, baggy brown cargo shorts, white tape wrapped on the fists, chunky purple high-top sneakers, a big grin. Standing, not crouching." "$COMMON2"
# picked 4201 (other seed 4202)
run glob2 4201 "A round green jelly slime blob with NO legs and NO feet, sitting flat on the ground like a drop of jelly, a wide round base, big shiny cartoon eyes, a small smile, one drip running down its side, a white shine highlight on top. Cute." "$COMMON2"
echo "ALL DONE $(date +%T)"
