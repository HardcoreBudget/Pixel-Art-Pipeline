#!/usr/bin/env bash
# Pixel-Art-Pipeline installer (Linux, macOS). Safe to run again: every step checks what is already there first.
#
#   curl -fsSL https://raw.githubusercontent.com/HardcoreBudget/Pixel-Art-Pipeline/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/HardcoreBudget/Pixel-Art-Pipeline/main/install.sh | bash -s -- --yes
#   git clone https://github.com/HardcoreBudget/Pixel-Art-Pipeline.git && cd Pixel-Art-Pipeline && ./install.sh
#
# Steps:
#   1. the pipeline itself: this folder, or (when piped from curl) a clone into $PIPELINE_DIR
#   2. ComfyUI in $COMFYUI_DIR (default: ComfyUI/ inside the pipeline folder), cloned at the tested commit;
#      an existing checkout is used as it is and never changed
#   3. the custom node ComfyUI-GGUF, at the tested commit
#   4. a Python venv in $COMFYUI_DIR/venv: PyTorch, ComfyUI's and ComfyUI-GGUF's requirements, this pipeline's
#   5. the six model files (about 13 GB) into $COMFYUI_DIR/models/..., each checked against its SHA-256
#   6. the two Claude Code skills into ~/.claude/skills (asks first; --yes answers yes)
#   7. prints the next commands
#
# Options:
#   --dry-run       print every step, change nothing, download nothing
#   --yes, -y       answer yes to the skills question
#   --no-skills     skip step 6       --no-models   skip step 5
#   -h, --help      this text
# Environment (optional):
#   COMFYUI_DIR      ComfyUI folder                 default: <pipeline>/ComfyUI
#   PIPELINE_DIR     where a piped install clones   default: ./Pixel-Art-Pipeline
#   PYTHON           Python used to make the venv   default: python3.12, else python3 (3.10 or newer)
#   TORCH_INDEX_URL  PyTorch wheel index            default: https://download.pytorch.org/whl/cu126 on Linux,
#                                                    PyPI on macOS
#   HF_TOKEN         Hugging Face token, sent only to huggingface.co, if a model page needs you to log in
#   SKILLS_DIR       where the skills go            default: ~/.claude/skills
#
# Every model has its own licence; read and accept each one on its model page before you use it
# (see the README's licence table and THIRD_PARTY_NOTICES.md).
set -u

REPO_URL="https://github.com/HardcoreBudget/Pixel-Art-Pipeline.git"
COMFYUI_URL_GIT="https://github.com/comfyanonymous/ComfyUI.git"
COMFYUI_COMMIT="79be670"          # ComfyUI v0.37.0, the version the pipeline was tested with
GGUF_URL_GIT="https://github.com/city96/ComfyUI-GGUF.git"
GGUF_COMMIT="6ea2651"

# subfolder of models/ | file name | source URL (recorded) | SHA-256
MODELS=(
  "diffusion_models|krea2_turbo-Q4_K_M.gguf|https://huggingface.co/vantagewithai/Krea-2-Turbo-GGUF/resolve/main/krea2_turbo-Q4_K_M.gguf|bc12f539de7a7a6ddf9bac17ec6e5bfecd42c3517190f491131d8464a1034b40"
  "text_encoders|qwen3vl_4b_fp8_scaled.safetensors|https://huggingface.co/Comfy-Org/Krea-2/resolve/main/text_encoders/qwen3vl_4b_fp8_scaled.safetensors|54bd5144df0bbc25dd6ccadfcb826b521445a1b06ae5a42570bdd2974ca87094"
  "vae|qwen_image_vae.safetensors|https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors|a70580f0213e67967ee9c95f05bb400e8fb08307e017a924bf3441223e023d1f"
  "loras|k2-pixel32.safetensors|https://huggingface.co/e-n-v-y/Krea-2-Pixel-Art/resolve/main/k2-pixel32.safetensors|35a79daf8c9499554c5cd299dc3940f78c2d5f0b4ef30b3ad42ea232cdf14af0"
  "loras|k2-pixel64.safetensors|https://huggingface.co/e-n-v-y/Krea-2-Pixel-Art/resolve/main/k2-pixel64.safetensors|53f1033700a866eaf6f56026cc352e26cd7d0563d4b32957dbbd3765b60d47bf"
  "loras|k2-pixel128.safetensors|https://huggingface.co/e-n-v-y/Krea-2-Pixel-Art/resolve/main/k2-pixel128.safetensors|005cfe8e6ba05cbee90cf68ac9feb6f1f769d29a62a78c2eebcaa81955fb2a08"
)
SKILLS=(pixel-scene pixel-rig-keyframes)

DRY=0 YES=0 DO_SKILLS=1 DO_MODELS=1
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --yes|-y) YES=1 ;;
    --no-skills) DO_SKILLS=0 ;;
    --no-models) DO_MODELS=0 ;;
    -h|--help) sed -n '2,33p' "${BASH_SOURCE[0]:-/dev/null}" 2>/dev/null | sed 's/^# \{0,1\}//'
               [ -f "${BASH_SOURCE[0]:-}" ] || echo "See https://github.com/HardcoreBudget/Pixel-Art-Pipeline"; exit 0 ;;
    *) echo "unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

FAILS=() TODOS=()
say()  { printf '\n==> %s\n' "$*"; }
info() { printf '    %s\n' "$*"; }
warn() { printf '    WARNING: %s\n' "$*" >&2; }
fail() { printf '    FAILED: %s\n' "$*" >&2; FAILS+=("$*"); }
todo() { printf '    TODO: %s\n' "$*"; TODOS+=("$*"); }
run()  { # run a command, or print it under --dry-run
  if [ "$DRY" = 1 ]; then printf '    [dry-run] %s\n' "$*"; return 0; fi
  printf '    + %s\n' "$*"; "$@"
}
have() { command -v "$1" >/dev/null 2>&1; }
ask() { # ask "question" -> 0 for yes
  [ "$YES" = 1 ] && { info "$1 yes (--yes)"; return 0; }
  if [ -r /dev/tty ] && { : < /dev/tty; } 2>/dev/null; then
    local reply; printf '    %s [y/N] ' "$1"; read -r reply < /dev/tty || reply=""
    case "$reply" in y|Y|yes|YES) return 0 ;; *) return 1 ;; esac
  fi
  info "$1 no (no terminal to ask; rerun with --yes)"; return 1
}
sha256() { if have sha256sum; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi; }

OS=$(uname -s)
[ "$DRY" = 1 ] && say "DRY RUN: nothing is changed or downloaded"

# ---- 0. tools -------------------------------------------------------------------------------------------------
say "Checking tools"
for t in git curl; do have "$t" && info "$t: $(command -v "$t")" || fail "$t is not installed"; done
have sha256sum || have shasum || fail "neither sha256sum nor shasum is installed"
if [ -z "${PYTHON:-}" ]; then
  if have python3.12; then PYTHON=python3.12; else PYTHON=python3; fi
fi
if have "$PYTHON" && "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  info "python: $PYTHON ($("$PYTHON" -c 'import sys; print(sys.version.split()[0])')); tested with 3.12"
else
  fail "Python 3.10 or newer is needed (set PYTHON=...); tested with 3.12"
fi
if [ "${#FAILS[@]}" -gt 0 ] && [ "$DRY" = 0 ]; then echo "Install the missing tools and run again." >&2; exit 1; fi

# ---- 1. the pipeline ------------------------------------------------------------------------------------------
say "Pipeline"
SRC="${BASH_SOURCE[0]:-}"
if [ -n "$SRC" ] && [ -f "$SRC" ] && [ -f "$(dirname "$SRC")/scripts/krea.py" ]; then
  REPO=$(cd "$(dirname "$SRC")" && pwd)
  info "using $REPO"
else
  REPO=${PIPELINE_DIR:-$PWD/Pixel-Art-Pipeline}
  if [ -f "$REPO/scripts/krea.py" ]; then
    info "using the existing clone $REPO"
  else
    run git clone "$REPO_URL" "$REPO" || { fail "git clone $REPO_URL"; exit 1; }
  fi
  [ "$DRY" = 0 ] && REPO=$(cd "$REPO" && pwd)
fi
COMFYUI_DIR=${COMFYUI_DIR:-$REPO/ComfyUI}

# ---- 2. ComfyUI -----------------------------------------------------------------------------------------------
say "ComfyUI in $COMFYUI_DIR"
if [ -f "$COMFYUI_DIR/main.py" ]; then
  cur=$(git -C "$COMFYUI_DIR" rev-parse --short=7 HEAD 2>/dev/null || echo "not a git checkout")
  info "found an existing ComfyUI ($cur); left as it is (tested commit: $COMFYUI_COMMIT)"
else
  run git clone "$COMFYUI_URL_GIT" "$COMFYUI_DIR" && run git -C "$COMFYUI_DIR" checkout --quiet "$COMFYUI_COMMIT" \
    || fail "ComfyUI clone/checkout"
fi

# ---- 3. custom nodes ------------------------------------------------------------------------------------------
say "Custom node ComfyUI-GGUF (loads the Krea 2 Turbo GGUF)"
GGUF_DIR="$COMFYUI_DIR/custom_nodes/ComfyUI-GGUF"
if [ -d "$GGUF_DIR/.git" ] || [ -f "$GGUF_DIR/__init__.py" ]; then
  info "found $GGUF_DIR; left as it is (tested commit: $GGUF_COMMIT)"
else
  run git clone "$GGUF_URL_GIT" "$GGUF_DIR" && run git -C "$GGUF_DIR" checkout --quiet "$GGUF_COMMIT" \
    || fail "ComfyUI-GGUF clone/checkout"
fi
info "No background-removal node is needed: scripts/pixel_snap.py removes the plain white background in Python."

# ---- 4. Python environment ------------------------------------------------------------------------------------
say "Python venv in $COMFYUI_DIR/venv"
VPY="$COMFYUI_DIR/venv/bin/python"
MARK="$COMFYUI_DIR/venv/.pixel-art-pipeline-installed"
if [ -f "$MARK" ]; then
  info "already installed ($MARK); delete that file to reinstall the packages"
else
  [ -x "$VPY" ] || run "$PYTHON" -m venv "$COMFYUI_DIR/venv" || fail "python -m venv"
  if [ -z "${TORCH_INDEX_URL:-}" ] && [ "$OS" = Linux ]; then TORCH_INDEX_URL="https://download.pytorch.org/whl/cu126"; fi
  if [ -n "${TORCH_INDEX_URL:-}" ]; then
    run "$VPY" -m pip install torch torchvision torchaudio --index-url "$TORCH_INDEX_URL" || fail "PyTorch install"
  else
    run "$VPY" -m pip install torch torchvision torchaudio || fail "PyTorch install"
  fi
  run "$VPY" -m pip install -r "$COMFYUI_DIR/requirements.txt" -r "$GGUF_DIR/requirements.txt" \
    -r "$REPO/requirements.txt" || fail "requirements install"
  if [ "${#FAILS[@]}" -eq 0 ]; then run touch "$MARK"; fi
fi
[ "$OS" = Darwin ] && warn "macOS: the pipeline was tested on Linux with an NVIDIA GPU only; PyTorch uses MPS or the CPU here."

# ---- 5. models ------------------------------------------------------------------------------------------------
say "Models (about 13 GB) into $COMFYUI_DIR/models"
if [ "$DO_MODELS" = 0 ]; then
  info "skipped (--no-models)"
else
  for m in "${MODELS[@]}"; do
    IFS='|' read -r sub file url want <<< "$m"
    dest="$COMFYUI_DIR/models/$sub/$file"
    if [ -z "$url" ]; then todo "$file: no download URL recorded; put it in models/$sub/ by hand"; continue; fi
    if [ -f "$dest" ]; then
      if [ "$DRY" = 1 ]; then info "$sub/$file exists; its SHA-256 would be checked"; continue; fi
      got=$(sha256 "$dest")
      if [ "$got" = "$want" ]; then info "$sub/$file: present, SHA-256 OK"; continue; fi
      fail "$sub/$file exists but its SHA-256 is $got, not $want; move it away and run again"; continue
    fi
    auth=()
    [ -n "${HF_TOKEN:-}" ] && auth=(-H "Authorization: Bearer $HF_TOKEN")
    run mkdir -p "$COMFYUI_DIR/models/$sub"
    if [ "$DRY" = 1 ]; then
      info "[dry-run] curl -fL -C - -o $dest.part $url ; check SHA-256 $want ; rename to $file"; continue
    fi
    info "+ curl $url"
    if ! curl -fL -C - --retry 10 --retry-delay 5 ${auth[@]+"${auth[@]}"} -o "$dest.part" "$url"; then
      fail "download $url (if the page asks you to log in or accept a licence: do that, set HF_TOKEN and rerun)"; continue
    fi
    got=$(sha256 "$dest.part")
    if [ "$got" = "$want" ]; then mv "$dest.part" "$dest"; info "$sub/$file: SHA-256 OK"
    else fail "$sub/$file: SHA-256 $got, expected $want (kept as $dest.part)"; fi
  done
fi

# ---- 6. Claude Code skills ------------------------------------------------------------------------------------
SKILLS_DIR=${SKILLS_DIR:-$HOME/.claude/skills}
say "Claude Code skills (${SKILLS[*]}) into $SKILLS_DIR"
if [ "$DO_SKILLS" = 0 ]; then
  info "skipped (--no-skills)"
elif ask "Install the two skills into $SKILLS_DIR?"; then
  for s in "${SKILLS[@]}"; do
    if [ -d "$SKILLS_DIR/$s" ] && [ "$DRY" = 0 ] && diff -rq "$REPO/skills/$s" "$SKILLS_DIR/$s" >/dev/null 2>&1; then
      info "$s: already installed and up to date"; continue
    fi
    if [ -d "$SKILLS_DIR/$s" ]; then run mv "$SKILLS_DIR/$s" "$SKILLS_DIR/$s.bak-$(date +%Y%m%d%H%M%S)"; fi
    run mkdir -p "$SKILLS_DIR" && run cp -R "$REPO/skills/$s" "$SKILLS_DIR/$s" || fail "copy skill $s"
  done
else
  info "skills not installed; to do it later: cp -R \"$REPO/skills/\"* \"$SKILLS_DIR/\""
fi

# ---- 7. summary -----------------------------------------------------------------------------------------------
say "Summary"
for t in "${TODOS[@]+"${TODOS[@]}"}"; do echo "    TODO: $t"; done
for f in "${FAILS[@]+"${FAILS[@]}"}"; do echo "    FAILED: $f"; done
[ "$DRY" = 1 ] && echo "    (dry run: nothing was changed)"
cat <<EOF

Next:
  export COMFYUI_DIR="$COMFYUI_DIR"
  "$REPO/scripts/start_comfy.sh"                  # ComfyUI on http://127.0.0.1:8188 (log: \$COMFYUI_DIR/comfy.log)
  curl -s http://127.0.0.1:8188/system_stats      # ready when this answers
  "$COMFYUI_DIR/venv/bin/python" "$REPO/scripts/krea.py" "a chibi knight in steel armour, side view, plain white background" \\
      --name knight --pixel 64 --no-style --colors 14 --seed 4102
  # -> $REPO/out/krea/knight_raw.png and knight_px.png
EOF
[ "${#FAILS[@]}" -eq 0 ] || exit 1
