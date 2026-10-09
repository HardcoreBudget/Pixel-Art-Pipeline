# Third-party notices

## This repository

The maintainer's own work is under two licences (both "Copyright (c) 2026 Hazim Emad Ismail (HardcoreBudget)"): the code -- the scripts,
the installers, the workflow file, the two skills (`skills/pixel-scene`, `skills/pixel-rig-keyframes`), the scene source
code, `unity/` and the site's HTML -- under the MIT License (`LICENSE`); the media -- the images, GIFs and videos, the
example designs in `examples/`, the scenes' art and `.pas` files, and the trailer and behind-the-scenes videos in `docs/` (the YouTube uploads are the same videos) -- under CC BY 4.0
(`LICENSE-MEDIA`).

The repository **does not contain** any of the software or model weights below. `install.sh` / `install.ps1` download
them from their own sources, and `scripts/krea.py` talks to ComfyUI over HTTP. Each one stays under its own licence,
and **you must read and accept each licence yourself** before you download or use it. The summaries here are not legal
advice and do not replace the licence texts.

Every licence below was checked at the source named in its row on **2026-10-09**. Hugging Face files were matched to the
installer by their SHA-256 (Hugging Face's LFS metadata for each file equals the value in `install.sh`).

## Software

| Component | Version the installer uses | Used for | Licence (SPDX) | Checked at (2026-10-09) |
|---|---|---|---|---|
| ComfyUI | commit `79be670` (its version file says 0.37.0; the commit is 39 commits after the `v0.37.0` tag) | runs the model | GPL-3.0 | https://github.com/Comfy-Org/ComfyUI/blob/79be670/LICENSE (the old `comfyanonymous/ComfyUI` URL redirects there) |
| ComfyUI-GGUF | commit `6ea2651` | the `UnetLoaderGGUF` node that loads the Krea 2 Turbo GGUF file | Apache-2.0 | https://github.com/city96/ComfyUI-GGUF/blob/6ea2651/LICENSE |
| PyTorch (`torch`) | 2.14.0 (`cu126` wheels on Linux) | ComfyUI's runtime | `Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT` (the package's licence expression) | https://pypi.org/project/torch/2.14.0/ ; https://github.com/pytorch/pytorch/blob/main/LICENSE |
| `torchvision` | as resolved by pip (0.29.0 tested) | ComfyUI | BSD-3-Clause | https://github.com/pytorch/vision/blob/main/LICENSE |
| `torchaudio` | as resolved by pip (2.11.0 tested) | ComfyUI | BSD-2-Clause | https://github.com/pytorch/audio/blob/main/LICENSE |
| ComfyUI's Python requirements | as resolved by pip from ComfyUI's `requirements.txt` | ComfyUI | each package's own licence (not listed one by one here) | ComfyUI's `requirements.txt` at the commit above |
| ComfyUI-GGUF's Python requirements: `gguf`, `sentencepiece`, `protobuf` | as resolved by pip | the GGUF loader | `gguf`: MIT; `sentencepiece`: Apache-2.0; `protobuf`: BSD-3-Clause | https://pypi.org/project/gguf/ ; https://pypi.org/project/sentencepiece/ ; https://pypi.org/project/protobuf/ |
| Pillow | any recent (12.2 and 12.3 tested) | images in `scripts/` | MIT-CMU | https://pypi.org/project/pillow/12.3.0/ ; https://github.com/python-pillow/Pillow/blob/main/LICENSE |
| NumPy | any recent (1.26 and 2.5 tested) | `scripts/pixel_snap.py` | BSD-3-Clause (NumPy 2.5's wheel declares `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` for its bundled parts) | https://pypi.org/project/numpy/2.5.0/ ; https://github.com/numpy/numpy/blob/main/LICENSE.txt |
| SciPy | any recent (1.13 and 1.18 tested) | `scripts/pixel_snap.py` (`scipy.ndimage`) | BSD-3-Clause | https://github.com/scipy/scipy/blob/main/LICENSE.txt |

No background-removal model, library or custom node is used: `scripts/pixel_snap.py` keys out the plain white
background itself with NumPy and SciPy.

## Models

| File (as the installer downloads it) | Published by | Licence | Checked at (2026-10-09) |
|---|---|---|---|
| `krea2_turbo-Q4_K_M.gguf`: a GGUF Q4_K_M quantisation of Krea 2 Turbo | Hugging Face user `vantagewithai` (a third party, not Krea), repo `vantagewithai/Krea-2-Turbo-GGUF` | Krea 2 Community License Agreement v.1 (22 June 2026). The repo's card declares `krea-2-community-license`, names `krea/Krea-2-Turbo` as the base model ("quantized"), and says it is a "GGUF quantized version" of Krea 2 Turbo. | https://huggingface.co/vantagewithai/Krea-2-Turbo-GGUF ; licence text below |
| `qwen3vl_4b_fp8_scaled.safetensors`: the text encoder (Qwen3-VL 4B in fp8) | Comfy-Org (ComfyUI's maintainers), repo `Comfy-Org/Krea-2`, folder `text_encoders` | The repo's card declares the Krea 2 Community License for the whole repo, which also ships Krea's `LICENSE.pdf`. The underlying model is Qwen3-VL-4B-Instruct, which is Apache-2.0 (Krea's own inference code loads `Qwen/Qwen3-VL-4B-Instruct`). Treat this copy as under the Krea 2 Community License. | https://huggingface.co/Comfy-Org/Krea-2 ; https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct ; https://github.com/krea-ai/krea-2/blob/main/inference.py |
| `qwen_image_vae.safetensors`: the Qwen-Image VAE | Comfy-Org, repo `Comfy-Org/Qwen-Image_ComfyUI`, folder `split_files/vae` | Apache-2.0 (the repo's card; the original `Qwen/Qwen-Image` repo has an Apache-2.0 `LICENSE` file). The same file (same SHA-256) is also in `Comfy-Org/Krea-2`; Krea's code loads the VAE from `Qwen/Qwen-Image`. | https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI ; https://huggingface.co/Qwen/Qwen-Image/blob/main/LICENSE |
| `k2-pixel32.safetensors`, `k2-pixel64.safetensors`, `k2-pixel128.safetensors`: Krea-2-Pixel-Art LoRAs | Hugging Face user `e-n-v-y`, repo `e-n-v-y/Krea-2-Pixel-Art` | MIT, as declared in the model card's metadata (`license: mit`; the repo has no separate licence file). The card names `krea/Krea-2-Raw` as the base model, so the LoRAs are trained on Krea 2 Raw; the Krea 2 Community License applies when you use them with Krea 2 in any case. | https://huggingface.co/e-n-v-y/Krea-2-Pixel-Art |

None of these Hugging Face repos was gated on 2026-10-09 (Hugging Face API: `gated: false`), so the installer needs no
token for them. Krea's own repos (`krea/Krea-2-Turbo`, `krea/Krea-2-Raw`) **are** gated: you log in and accept the
licence before you can download from them.

## Krea 2 Community License: what it says

Read the licence itself: https://www.krea.ai/krea-2-licensing (Krea's page), and the same text as a PDF at
https://cdn.jsdelivr.net/gh/krea-ai/krea-2@db3984fbc6e13b34c0064990fc2d95ac64d00058/assets/hf_samples/LICENSE.pdf
(from Krea's GitHub repo `krea-ai/krea-2`, the link Krea's Hugging Face cards give; byte-identical to the
`LICENSE.pdf` in `Comfy-Org/Krea-2`). It incorporates Krea's Acceptable Use Policy:
https://www.krea.ai/krea-2-use-policy. All three were read on 2026-10-09. The points that matter for this pipeline:

- **Use.** A limited, non-exclusive, worldwide, non-transferable, non-sublicensable, revocable, royalty-free licence to
  use, copy, distribute, make Derivatives of, and generate Outputs from Krea 2 (section 2.1).
- **Commercial use** of the model, Derivatives or Outputs is allowed only if you (with all affiliated entities) have
  total company-wide annual revenue **under US$1,000,000**, on a trailing twelve months, from all sources. At or above
  it you need an enterprise licence from Krea first (section 2.3).
- **Outputs.** You own the Outputs you generate, subject to complying with the licence; Krea claims no ownership
  (section 5.3). You are responsible for them, including any third-party rights they touch.
- **Content filtering.** You must use "reasonable and appropriate" content-filter measures against prohibited,
  harmful or unlawful content in your deployment. The licence's examples include open-source classifiers, moderation
  APIs and **manual human review** (section 4.2). **This pipeline has no automatic content filter**: choosing and
  applying a measure is up to you.
- **AI disclosure** where a law, regulation or platform requires it (section 4.3), and the **Acceptable Use Policy**
  (section 4.4; for example no CSAM, no non-consensual intimate imagery, no deceptive deepfakes, no infringement of
  third-party rights, no military or mass-surveillance use).
- **Distributing the model or a Derivative** (section 3): include a copy of the licence and bind recipients to it; start
  the model's name with "Krea"; keep this notice in a "Notice" text file: "Krea 2 is licensed under the Krea 2
  Community License Agreement. For more information, visit https://krea.ai/krea-2-licensing." For a Derivative you
  made, also say that you modified the model, and do not present it as an official Krea product.
- **Termination.** Automatic on breach (9.1); **Krea may end it for any reason with 30 days' notice** (9.2); it ends if
  you sue over the model (9.3). Then you must stop using and delete the model and your Derivatives (9.4).
- Delaware law (10.1).

### The GGUF file: a third-party Derivative

`krea2_turbo-Q4_K_M.gguf` is a quantisation of Krea 2 Turbo, so it is a Derivative under the licence ("any modified
version of the Krea Model"). Its publisher's repo declares the Krea 2 Community License, starts the model name with
"Krea" and calls itself a quantized version. On 2026-10-09 the repo's file list held only the 13 `.gguf` files,
`Vantage_Krea-2-Turbo.json`, `README.md` and `.gitattributes`: **no copy of the licence and no "Notice" file** (section 3.1(a) and
(c) ask a distributor for both). Its licence link points to Krea's gated Hugging Face page.

This repository does not redistribute the file: the installer downloads it from that publisher, and you accept the
Krea 2 Community License yourself when you download it. If you prefer a source that ships the licence file, these
alternatives exist (neither was tested with this pipeline):

- **Comfy-Org's repackaged Krea 2 Turbo** in `Comfy-Org/Krea-2` (which includes Krea's `LICENSE.pdf`), for example
  `diffusion_models/krea2_turbo_fp8_scaled.safetensors` (13.1 GB) or `krea2_turbo_nvfp4.safetensors` (7.7 GB). These
  are not GGUF files: they load with ComfyUI's own `UNETLoader`, not `UnetLoaderGGUF`, and need more memory than the
  Q4_K_M file. Krea's README lists ComfyUI among the platforms that run Krea 2.
- **Make your own GGUF** from Krea's official weights (`krea/Krea-2-Turbo`, gated: log in and accept the licence) with
  ComfyUI-GGUF's `tools/` (`convert.py`, then a patched `llama.cpp` to quantise). A file you make for your own use is
  not distributed, so section 3 does not apply to it. Whether `convert.py` handles Krea 2's architecture was not
  checked.

## Example images

`examples/*.png` are three designs (Sir Stacks, Bonk, Mira) that the maintainer generated with this pipeline
(Krea 2 Turbo with the Krea-2-Pixel-Art LoRA) for the Pixel Art Studio trailer, then brought onto their 64-pixel grid
in Pixel Art Studio. They are Krea 2 Outputs: under the Krea 2 Community License the person who generated them owns
them and Krea claims no ownership (section 5.3). The maintainer releases them under **CC BY 4.0** (`LICENSE-MEDIA`).

## Scenes and showcase site

`scenes/` (Ashen Peak and The Drowned Shrine) and `docs/` (the showcase site) are the maintainer's work: the code under the
**MIT License** (`LICENSE`); the hand-drawn pixel art and bitmap fonts in the scenes, the built `.pas` files, and the
trailer pages' art and videos under **CC BY 4.0** (`LICENSE-MEDIA`). The four Krea 2 designs in `scenes/designs/` (`*_raw.png`) are Krea 2
Outputs the maintainer generated and owns (section 5.3), released under CC BY 4.0 like `examples/`. The scenes' code needs only
Pillow, NumPy and SciPy (listed above). `unity/PasBuilder` compiles against Pixel Art Studio, which is not part of this
repository and has its own licence (the Unity Asset Store EULA).

Fonts: the pages in `docs/` load Atkinson Hyperlegible, IBM Plex Mono, Silkscreen, Jersey 10, Bungee and JetBrains Mono
from Google Fonts at view time. They are under the SIL Open Font License 1.1 and are not included in this repository.
The behind-the-scenes video shows the Unity Editor's own interface, which belongs to Unity Technologies.
