#!/usr/bin/env bash
# Start ComfyUI for the Krea 2 pixel-art pipeline (Linux, systemd user session).
# Runs in its own cgroup capped at MEMMAX (default 16G) so an out-of-memory kill lands on ComfyUI, not on the other
# programs you have open (a Unity Editor, for example). Listens on COMFY_LISTEN:COMFY_PORT (default 127.0.0.1:8188)
# only. Output is appended to COMFY_LOG.
# LD_LIBRARY_PATH is cleared for ComfyUI only: a CUDA/cuDNN from another Python install on LD_LIBRARY_PATH can shadow
# the libraries the venv's torch ships with and abort it ("undefined symbol: cudnnGetLibConfig"). torch finds its own.
#
#   start_comfy.sh                         foreground; Ctrl+C stops it
#   MEMMAX=20G start_comfy.sh              a higher memory cap
#   DETACH=1 MEMMAX=16G start_comfy.sh     run as a background systemd user service (COMFY_UNIT, default
#                                          "comfyui-pixel") that outlives the terminal; stop it with:
#                                          systemctl --user stop comfyui-pixel
#   start_comfy.sh --reserve-vram 0.7      extra arguments go to ComfyUI's main.py
#
# Environment (all optional):
#   COMFYUI_DIR     ComfyUI checkout                      default: <pipeline>/ComfyUI (where install.sh puts
#                                                         it) if that exists, else $HOME/ComfyUI
#   COMFYUI_PYTHON  Python with ComfyUI's requirements    default: $COMFYUI_DIR/venv/bin/python
#   COMFY_LOG       log file                              default: $COMFYUI_DIR/comfy.log
#   COMFY_LISTEN    address to listen on                  default: 127.0.0.1
#   COMFY_PORT      port                                  default: 8188
#   COMFY_UNIT      systemd unit name for DETACH=1        default: comfyui-pixel
#   MEMMAX          memory cap (systemd MemoryMax)        default: 16G
PIPELINE=$(cd "$(dirname "$0")/.." && pwd)
if [ -z "${COMFYUI_DIR:-}" ]; then
  if [ -f "$PIPELINE/ComfyUI/main.py" ]; then COMFYUI_DIR=$PIPELINE/ComfyUI; else COMFYUI_DIR=$HOME/ComfyUI; fi
fi
COMFYUI_PYTHON=${COMFYUI_PYTHON:-$COMFYUI_DIR/venv/bin/python}
COMFY_LOG=${COMFY_LOG:-$COMFYUI_DIR/comfy.log}
COMFY_LISTEN=${COMFY_LISTEN:-127.0.0.1}
COMFY_PORT=${COMFY_PORT:-8188}
COMFY_UNIT=${COMFY_UNIT:-comfyui-pixel}
MEMMAX=${MEMMAX:-16G}

cd "$COMFYUI_DIR" || { echo "COMFYUI_DIR '$COMFYUI_DIR' not found; set COMFYUI_DIR to your ComfyUI checkout" >&2; exit 1; }
[ -f main.py ] || { echo "no main.py in '$COMFYUI_DIR'; is COMFYUI_DIR a ComfyUI checkout?" >&2; exit 1; }
[ -x "$COMFYUI_PYTHON" ] || { echo "COMFYUI_PYTHON '$COMFYUI_PYTHON' is not executable; set COMFYUI_PYTHON" >&2; exit 1; }
COMFY_LOG=$(realpath -m "$COMFY_LOG")

if ! command -v systemd-run >/dev/null 2>&1; then
  [ "${DETACH:-0}" = 1 ] && { echo "DETACH=1 needs systemd-run" >&2; exit 1; }
  echo "systemd-run not found: starting WITHOUT the $MEMMAX memory cap; log: $COMFY_LOG" >&2
  exec env -u LD_LIBRARY_PATH "$COMFYUI_PYTHON" main.py --listen "$COMFY_LISTEN" --port "$COMFY_PORT" "$@" \
    >> "$COMFY_LOG" 2>&1
fi
if [ "${DETACH:-0}" = 1 ]; then
  exec systemd-run --user --unit="$COMFY_UNIT" --collect --quiet -p MemoryMax="$MEMMAX" -p MemorySwapMax=1G \
    -p WorkingDirectory="$PWD" -p StandardOutput="append:$COMFY_LOG" -p StandardError="append:$COMFY_LOG" \
    env -u LD_LIBRARY_PATH "$COMFYUI_PYTHON" main.py --listen "$COMFY_LISTEN" --port "$COMFY_PORT" "$@"
fi
exec env -u LD_LIBRARY_PATH systemd-run --user --scope --quiet -p MemoryMax="$MEMMAX" -p MemorySwapMax=1G \
  "$COMFYUI_PYTHON" main.py --listen "$COMFY_LISTEN" --port "$COMFY_PORT" "$@" >> "$COMFY_LOG" 2>&1
