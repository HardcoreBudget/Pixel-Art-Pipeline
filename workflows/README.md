# Workflows

`krea2_pixel_api.json` is the API-format ComfyUI workflow that `scripts/krea.py` queues, made with its default
settings (`--pixel 64`, seed 7101, 1024 x 1024, 8 steps, CFG 1.0, `er_sde` + `simple`, the k2-pixel64 LoRA at 1.0) and
the placeholder prompt `<your prompt>` followed by krea.py's default style suffix. Regenerate it, or write one for
other settings, without ComfyUI running:

```bash
python3 scripts/krea.py "<your prompt>" --name example --dump-workflow workflows/krea2_pixel_api.json
```

**Using it in ComfyUI.**

- In the web UI (http://127.0.0.1:8188), open the file with the workflow menu's Open command or drag it onto the
  canvas. An API-format file holds no node positions, so the nodes arrive stacked: arrange them, then edit the prompt
  in node 5 (the positive `CLIPTextEncode`) and the seed in node 8 (`KSampler`).
- Or queue it as it is over HTTP:
  `python3 -c "import json,urllib.request; urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8188/prompt', json.dumps({'prompt': json.load(open('workflows/krea2_pixel_api.json'))}).encode(), {'Content-Type': 'application/json'}))"`
  The picture lands in ComfyUI's `output/` folder as `krea_*.png`, before krea.py's background removal and grid snap.

It needs the custom node ComfyUI-GGUF (`UnetLoaderGGUF`) and a ComfyUI with Krea 2 support (`CLIPLoader` type
`krea2`; tested with v0.37.0), plus the model files listed in the main README.
