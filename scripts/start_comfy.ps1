# Start ComfyUI for the Krea 2 pixel-art pipeline on Windows (foreground; Ctrl+C stops it). Untested on Windows.
# No memory cap here (start_comfy.sh uses a systemd cgroup on Linux). Extra arguments go to ComfyUI's main.py.
#   $env:COMFYUI_DIR   ComfyUI folder   default: <pipeline>\ComfyUI
#   $env:COMFY_LISTEN  default 127.0.0.1;  $env:COMFY_PORT  default 8188
$Comfy = if ($env:COMFYUI_DIR) { $env:COMFYUI_DIR } else { Join-Path (Split-Path $PSScriptRoot) "ComfyUI" }
$Listen = if ($env:COMFY_LISTEN) { $env:COMFY_LISTEN } else { "127.0.0.1" }
$Port = if ($env:COMFY_PORT) { $env:COMFY_PORT } else { "8188" }
$Py = Join-Path $Comfy "venv\Scripts\python.exe"
if (-not (Test-Path (Join-Path $Comfy "main.py"))) { Write-Error "no main.py in '$Comfy'; set `$env:COMFYUI_DIR"; exit 1 }
Set-Location $Comfy
& $Py main.py --listen $Listen --port $Port @args
