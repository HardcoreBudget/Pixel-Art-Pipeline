<#
Pixel-Art-Pipeline installer (Windows PowerShell 5.1 or PowerShell 7). Safe to run again: every step checks what is
already there first. The same steps as install.sh; see its header for details.

  irm https://raw.githubusercontent.com/HardcoreBudget/Pixel-Art-Pipeline/main/install.ps1 | iex
  & ([scriptblock]::Create((irm https://raw.githubusercontent.com/HardcoreBudget/Pixel-Art-Pipeline/main/install.ps1))) -Yes
  git clone https://github.com/HardcoreBudget/Pixel-Art-Pipeline.git; cd Pixel-Art-Pipeline; .\install.ps1

Options: -DryRun (print every step, change nothing, download nothing), -Yes (install the skills without asking),
-NoSkills, -NoModels. With "irm | iex" no options can be passed: set $env:PAS_DRY_RUN = "1" or $env:PAS_YES = "1".
Environment (optional): COMFYUI_DIR, PIPELINE_DIR, PYTHON, TORCH_INDEX_URL (default the cu126 index), HF_TOKEN,
SKILLS_DIR (default ~\.claude\skills).

Every model has its own licence; read and accept each one on its model page before you use it.
#>
param([switch]$DryRun, [switch]$Yes, [switch]$NoSkills, [switch]$NoModels)
$ErrorActionPreference = "Continue"
if ($env:PAS_DRY_RUN -eq "1") { $DryRun = $true }
if ($env:PAS_YES -eq "1") { $Yes = $true }
$FromFile = [bool]$PSCommandPath

$RepoUrl = "https://github.com/HardcoreBudget/Pixel-Art-Pipeline.git"
$ComfyGit = "https://github.com/comfyanonymous/ComfyUI.git"; $ComfyCommit = "79be670"   # ComfyUI v0.37.0
$GgufGit = "https://github.com/city96/ComfyUI-GGUF.git"; $GgufCommit = "6ea2651"
$Models = @(
  @("diffusion_models", "krea2_turbo-Q4_K_M.gguf", "https://huggingface.co/vantagewithai/Krea-2-Turbo-GGUF/resolve/main/krea2_turbo-Q4_K_M.gguf", "bc12f539de7a7a6ddf9bac17ec6e5bfecd42c3517190f491131d8464a1034b40"),
  @("text_encoders", "qwen3vl_4b_fp8_scaled.safetensors", "https://huggingface.co/Comfy-Org/Krea-2/resolve/main/text_encoders/qwen3vl_4b_fp8_scaled.safetensors", "54bd5144df0bbc25dd6ccadfcb826b521445a1b06ae5a42570bdd2974ca87094"),
  @("vae", "qwen_image_vae.safetensors", "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors", "a70580f0213e67967ee9c95f05bb400e8fb08307e017a924bf3441223e023d1f"),
  @("loras", "k2-pixel32.safetensors", "https://huggingface.co/e-n-v-y/Krea-2-Pixel-Art/resolve/main/k2-pixel32.safetensors", "35a79daf8c9499554c5cd299dc3940f78c2d5f0b4ef30b3ad42ea232cdf14af0"),
  @("loras", "k2-pixel64.safetensors", "https://huggingface.co/e-n-v-y/Krea-2-Pixel-Art/resolve/main/k2-pixel64.safetensors", "53f1033700a866eaf6f56026cc352e26cd7d0563d4b32957dbbd3765b60d47bf"),
  @("loras", "k2-pixel128.safetensors", "https://huggingface.co/e-n-v-y/Krea-2-Pixel-Art/resolve/main/k2-pixel128.safetensors", "005cfe8e6ba05cbee90cf68ac9feb6f1f769d29a62a78c2eebcaa81955fb2a08")
)
$Skills = @("pixel-scene", "pixel-rig-keyframes")
$Fails = New-Object System.Collections.Generic.List[string]
$Todos = New-Object System.Collections.Generic.List[string]

function Say($m) { Write-Host ""; Write-Host "==> $m" }
function Info($m) { Write-Host "    $m" }
function Fail($m) { Write-Host "    FAILED: $m" -ForegroundColor Red; $script:Fails.Add($m) }
function Todo($m) { Write-Host "    TODO: $m" -ForegroundColor Yellow; $script:Todos.Add($m) }
function Run([string]$exe, [string[]]$a) {
  $line = "$exe " + ($a -join " ")
  if ($DryRun) { Write-Host "    [dry-run] $line"; return $true }
  Write-Host "    + $line"
  & $exe @a | Out-Host
  return ($LASTEXITCODE -eq 0)
}
function Stop-Install([int]$code) {
  # "exit" would close the user's PowerShell window under "irm | iex"; only a script file exits
  if ($script:FromFile) { exit $code } elseif ($code -ne 0) { throw "install stopped (see the messages above)" }
}
function Have($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }

if ($DryRun) { Say "DRY RUN: nothing is changed or downloaded" }

Say "Checking tools"
foreach ($t in @("git")) { if (Have $t) { Info "${t}: $((Get-Command $t).Source)" } else { Fail "$t is not installed" } }
$Py = $env:PYTHON
if (-not $Py) { if (Have "py") { $Py = "py" } else { $Py = "python" } }
$PyArgs = @(); if ($Py -eq "py") { $PyArgs = @("-3.12") }
$ver = & $Py @PyArgs -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
if (-not $ver -and $PyArgs.Count -gt 0) { $PyArgs = @(); $ver = & $Py -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null }
if ($ver -and ([version]$ver -ge [version]"3.10")) { Info "python: $Py $($PyArgs -join ' ') ($ver); tested with 3.12" }
else { Fail "Python 3.10 or newer is needed (set `$env:PYTHON); tested with 3.12" }
if ($Fails.Count -gt 0 -and -not $DryRun) { Write-Host "Install the missing tools and run again."; Stop-Install 1 }

Say "Pipeline"
$Src = $PSCommandPath
if ($Src -and (Test-Path (Join-Path (Split-Path $Src) "scripts\krea.py"))) { $Repo = Split-Path $Src; Info "using $Repo" }
else {
  $Repo = if ($env:PIPELINE_DIR) { $env:PIPELINE_DIR } else { Join-Path (Get-Location) "Pixel-Art-Pipeline" }
  if (Test-Path (Join-Path $Repo "scripts\krea.py")) { Info "using the existing clone $Repo" }
  elseif (-not (Run "git" @("clone", $RepoUrl, $Repo))) { Fail "git clone $RepoUrl"; Stop-Install 1 }
}
$Comfy = if ($env:COMFYUI_DIR) { $env:COMFYUI_DIR } else { Join-Path $Repo "ComfyUI" }

Say "ComfyUI in $Comfy"
if (Test-Path (Join-Path $Comfy "main.py")) {
  $cur = git -C $Comfy rev-parse --short=7 HEAD 2>$null
  Info "found an existing ComfyUI ($cur); left as it is (tested commit: $ComfyCommit)"
} elseif (-not ((Run "git" @("clone", $ComfyGit, $Comfy)) -and (Run "git" @("-C", $Comfy, "checkout", "--quiet", $ComfyCommit)))) {
  Fail "ComfyUI clone/checkout"
}

Say "Custom node ComfyUI-GGUF (loads the Krea 2 Turbo GGUF)"
$Gguf = Join-Path $Comfy "custom_nodes\ComfyUI-GGUF"
if (Test-Path (Join-Path $Gguf "__init__.py")) { Info "found $Gguf; left as it is (tested commit: $GgufCommit)" }
elseif (-not ((Run "git" @("clone", $GgufGit, $Gguf)) -and (Run "git" @("-C", $Gguf, "checkout", "--quiet", $GgufCommit)))) {
  Fail "ComfyUI-GGUF clone/checkout"
}
Info "No background-removal node is needed: scripts\pixel_snap.py removes the plain white background in Python."

Say "Python venv in $Comfy\venv"
$Vpy = Join-Path $Comfy "venv\Scripts\python.exe"
$Mark = Join-Path $Comfy "venv\.pixel-art-pipeline-installed"
if (Test-Path $Mark) { Info "already installed ($Mark); delete that file to reinstall the packages" }
else {
  if (-not (Test-Path $Vpy)) { if (-not (Run $Py ($PyArgs + @("-m", "venv", (Join-Path $Comfy "venv"))))) { Fail "python -m venv" } }
  $TorchIndex = if ($env:TORCH_INDEX_URL) { $env:TORCH_INDEX_URL } else { "https://download.pytorch.org/whl/cu126" }
  if (-not (Run $Vpy @("-m", "pip", "install", "torch", "torchvision", "torchaudio", "--index-url", $TorchIndex))) { Fail "PyTorch install" }
  if (-not (Run $Vpy @("-m", "pip", "install", "-r", (Join-Path $Comfy "requirements.txt"), "-r", (Join-Path $Gguf "requirements.txt"), "-r", (Join-Path $Repo "requirements.txt")))) { Fail "requirements install" }
  if ($Fails.Count -eq 0 -and -not $DryRun) { New-Item -ItemType File -Force $Mark | Out-Null }
}
Write-Host "    WARNING: Windows is untested; the pipeline was built and tested on Linux with an NVIDIA GPU." -ForegroundColor Yellow

Say "Models (about 13 GB) into $Comfy\models"
if ($NoModels) { Info "skipped (-NoModels)" }
else {
  foreach ($m in $Models) {
    $sub, $file, $url, $want = $m
    $dir = Join-Path $Comfy "models\$sub"; $dest = Join-Path $dir $file
    if (-not $url) { Todo "${file}: no download URL recorded; put it in models\$sub\ by hand"; continue }
    if (Test-Path $dest) {
      if ($DryRun) { Info "$sub\$file exists; its SHA-256 would be checked"; continue }
      $got = (Get-FileHash -Algorithm SHA256 $dest).Hash.ToLower()
      if ($got -eq $want) { Info "$sub\${file}: present, SHA-256 OK" } else { Fail "$sub\$file exists but its SHA-256 is $got, not $want; move it away and run again" }
      continue
    }
    if ($DryRun) { Info "[dry-run] download $url -> $dest.part ; check SHA-256 $want ; rename to $file"; continue }
    New-Item -ItemType Directory -Force $dir | Out-Null
    $a = @("-fL", "-C", "-", "--retry", "10", "--retry-delay", "5", "-o", "$dest.part", $url)
    if ($env:HF_TOKEN) { $a = @("-H", "Authorization: Bearer $($env:HF_TOKEN)") + $a }
    Write-Host "    + curl.exe $url"
    & curl.exe @a
    if ($LASTEXITCODE -ne 0) { Fail "download $url (if the page asks you to log in or accept a licence: do that, set HF_TOKEN and rerun)"; continue }
    $got = (Get-FileHash -Algorithm SHA256 "$dest.part").Hash.ToLower()
    if ($got -eq $want) { Move-Item "$dest.part" $dest; Info "$sub\${file}: SHA-256 OK" }
    else { Fail "$sub\${file}: SHA-256 $got, expected $want (kept as $dest.part)" }
  }
}

$SkillsDir = if ($env:SKILLS_DIR) { $env:SKILLS_DIR } else { Join-Path $HOME ".claude\skills" }
Say "Claude Code skills ($($Skills -join ', ')) into $SkillsDir"
if ($NoSkills) { Info "skipped (-NoSkills)" }
else {
  $ok = $Yes
  if ($Yes) { Info "yes (-Yes)" }
  else { try { $ok = ((Read-Host "    Install the two skills into $SkillsDir? [y/N]") -match '^(y|yes)$') } catch { $ok = $false } }
  if ($ok) {
    foreach ($s in $Skills) {
      $to = Join-Path $SkillsDir $s
      if ($DryRun) { Info "[dry-run] copy $Repo\skills\$s -> $to"; continue }
      New-Item -ItemType Directory -Force $SkillsDir | Out-Null
      if (Test-Path $to) { Move-Item $to "$to.bak-$(Get-Date -Format yyyyMMddHHmmss)" }
      Copy-Item -Recurse (Join-Path $Repo "skills\$s") $to
      Info "$s installed"
    }
  } else { Info "skills not installed; to do it later copy $Repo\skills\* into $SkillsDir" }
}

Say "Summary"
foreach ($t in $Todos) { Write-Host "    TODO: $t" }
foreach ($f in $Fails) { Write-Host "    FAILED: $f" }
if ($DryRun) { Write-Host "    (dry run: nothing was changed)" }
Write-Host @"

Next:
  `$env:COMFYUI_DIR = "$Comfy"
  & "$Repo\scripts\start_comfy.ps1"               # ComfyUI on http://127.0.0.1:8188
  & "$Vpy" "$Repo\scripts\krea.py" "a chibi knight in steel armour, side view, plain white background" ``
      --name knight --pixel 64 --no-style --colors 14 --seed 4102
  # -> $Repo\out\krea\knight_raw.png and knight_px.png
"@
if ($Fails.Count -gt 0) { Stop-Install 1 }
