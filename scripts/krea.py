#!/usr/bin/env python3
"""Text-to-image with Krea 2 Turbo (Krea 2 Community License: commercial use allowed under $1M/yr company revenue;
you own the outputs) + e-n-v-y's Krea-2-Pixel-Art LoRA (MIT), through the running ComfyUI.

  krea.py "a young farmer with a straw hat ..." --name farmer [--pixel 64] [--seed N]

--pixel 32|64|128 picks the LoRA trained for that pixel grid (the card: generate at 1024; 64 works best without the
trigger word "pixel art"); the result is snapped to exactly that grid (1024/64 = 16 px cells). --pixel 0: no LoRA.
Turbo settings from the ComfyUI docs: 8 steps, CFG 1.0, er_sde + simple.
Writes out/krea/<name>_raw.png (background removed) and <name>_px.png (pixel-snapped, cropped).

ComfyUI must be running (scripts/start_comfy.sh) at COMFYUI_URL (default http://127.0.0.1:8188).
--dump-workflow FILE writes the API-format workflow this command would queue and exits without contacting ComfyUI.
"""
import argparse, io, json, pathlib, sys, time, urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
UNET = "krea2_turbo-Q4_K_M.gguf"
TE = "qwen3vl_4b_fp8_scaled.safetensors"
VAE = "qwen_image_vae.safetensors"
PIXEL_LORAS = {32: "k2-pixel32.safetensors", 64: "k2-pixel64.safetensors", 128: "k2-pixel128.safetensors"}
STYLE = ("16-bit retro game sprite for a cozy farming game, chunky pixels, a dark outline, two or three shades per "
         "colour. Single character, full body, facing the camera, on a plain white background.")


def workflow(a, prompt):
    wf = {
        "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": UNET}},
        "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": TE, "type": "krea2", "device": "default"}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": prompt}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": ""}},
        "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": a.size, "height": a.size, "batch_size": 1}},
        "8": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["5", 0], "negative": ["6", 0],
                                                   "latent_image": ["7", 0], "seed": a.seed, "steps": a.steps, "cfg": a.cfg,
                                                   "sampler_name": "er_sde", "scheduler": "simple", "denoise": 1.0}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["4", 0]}},
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "krea"}},
    }
    if a.pixel:
        wf["2"] = {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": PIXEL_LORAS[a.pixel],
                                                                  "strength_model": a.lora}}
        wf["8"]["inputs"]["model"] = ["2", 0]
    return wf


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("prompt", help="what to draw; the STYLE suffix is appended unless --no-style")
    p.add_argument("--name", required=True, help="output file stem: <name>_raw.png and <name>_px.png")
    p.add_argument("--pixel", type=int, choices=[0, 32, 64, 128], default=64,
                   help="pixel LoRA / grid (default 64: 1024 px / 64 = 16 px cells); 0 = no LoRA, detect the grid")
    p.add_argument("--lora", type=float, default=1.0, help="LoRA strength (default 1.0)")
    p.add_argument("--no-style", dest="style", action="store_false", help="don't append the STYLE suffix")
    p.add_argument("--seed", type=int, default=7101, help="sampler seed (default 7101)")
    p.add_argument("--size", type=int, default=1024, help="square canvas in px (default 1024)")
    p.add_argument("--steps", type=int, default=8, help="sampling steps (default 8, Turbo)")
    p.add_argument("--cfg", type=float, default=1.0, help="CFG (default 1.0, Turbo)")
    p.add_argument("--colors", type=int, default=32, help="palette size of <name>_px.png (default 32)")
    p.add_argument("--out", default=str(HERE.parent / "out" / "krea"), help="output folder (default <repo>/out/krea)")
    p.add_argument("--dump-workflow", metavar="FILE", default=None,
                   help="write the API-format workflow JSON to FILE and exit (ComfyUI is not contacted)")
    return p


def full_prompt(a):
    prompt = a.prompt + (" " + STYLE if a.style else "")
    if a.pixel in (32, 128):
        prompt = "pixel art, " + prompt  # the LoRA's trigger word (64 works best without it)
    return prompt


def main():
    a = build_parser().parse_args()
    prompt = full_prompt(a)
    if a.dump_workflow:
        pathlib.Path(a.dump_workflow).write_text(json.dumps(workflow(a, prompt), indent=2) + "\n")
        print(f"wrote {a.dump_workflow}")
        return
    from PIL import Image
    import comfy_client as gen
    import pixel_snap
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    pid = json.loads(gen.call("/prompt", {"prompt": workflow(a, prompt)}))["prompt_id"]
    print(f"queued {pid} pixel={a.pixel} seed={a.seed} {a.size}px {a.steps} steps", flush=True)
    while True:
        h = json.loads(gen.call(f"/history/{pid}"))
        if pid in h:
            st = h[pid].get("status", {})
            if st.get("status_str") == "error":
                raise SystemExit("ComfyUI error:\n" + json.dumps(st.get("messages"), indent=1)[-3000:])
            if st.get("completed"):
                break
        time.sleep(5)
    im = Image.open(io.BytesIO(gen.call("/view?" + urllib.parse.urlencode(h[pid]["outputs"]["10"]["images"][0]))))
    raw = pixel_snap.clean_alpha(im)
    raw.save(out / f"{a.name}_raw.png")
    # the LoRA draws on an exact grid: size/pixel px per cell; without the LoRA, detect as usual
    cell = a.size / a.pixel if a.pixel else None
    px, cell = pixel_snap.pixelate(raw, 0, a.colors, crop=True, cell_px=cell)
    px.save(out / f"{a.name}_px.png")
    warn = pixel_snap.failed_sprite(raw)
    print(f"done in {time.time() - t0:.0f}s: {px.width}x{px.height} (cell {cell:.1f}px) -> {out}/{a.name}_*"
          + (f"\n{warn}" if warn else ""))


if __name__ == "__main__":
    main()
