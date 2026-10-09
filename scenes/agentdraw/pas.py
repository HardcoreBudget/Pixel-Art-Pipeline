"""Export agentdraw layers/frames to the sandbox builder's JSON and build a real .pas headlessly.

  from agentdraw.pas import export_job, build
  job = export_job("Knight", layers_by_frame, order, tags=[("Idle", 0, 3)], durations=[120]*4)
  build(job, "Knight")      # Unity -batchmode on $PAS_SANDBOX (a scratch project, never your main one)

layers_by_frame: {layer name: [RGBA array per frame]} (a layer with fewer frames repeats its last one);
groups: {group name: parent or None} for bone groups (no pixels); parents: {layer: group}.
"""
import json, os, pathlib, subprocess

import numpy as np

from agentdraw.core import OUT, hexs

# A Unity Editor binary and a SCRATCH Unity project (never your real one) that holds Pixel Art Studio and
# unity/PasBuilder/Editor/SandboxBuild.cs from this repository.
UNITY = os.environ.get("UNITY_EDITOR", "Unity")
SANDBOX = pathlib.Path(os.environ.get("PAS_SANDBOX", "PAS-Sandbox"))


def export_job(name, layers_by_frame, order, tags=(), durations=None, groups=None, parents=None, poses=(), props=None):
    """props: {layer: {"hidden": bool, "opacity": 0-255, "locked": bool}} (e.g. an onion-skin reference layer)."""
    props = props or {}
    nframes = max(len(v) for v in layers_by_frame.values())
    first = next(iter(layers_by_frame.values()))[0]
    H, W = first.shape[:2]
    cols = {}
    for frames in layers_by_frame.values():
        for a in frames:
            for c in np.unique(a[a[..., 3] > 0][:, :3], axis=0):
                cols.setdefault(tuple(int(v) for v in c), len(cols) + 1)
    if len(cols) > 255:
        raise ValueError(f"{len(cols)} colours: an indexed .pas holds 255 (+ transparent)")
    palette = [hexs(c) for c, _ in sorted(cols.items(), key=lambda kv: kv[1])]
    lut = {c: i for c, i in cols.items()}
    layers = []
    groups = groups or {}; parents = parents or {}
    for g, gp in groups.items():  # bone groups first (bottom), they own no pixels
        layers.append({"name": g, "parent": gp or "", "group": True, "cels": []})
    for n in order:
        frames = layers_by_frame[n]; cels = []
        for f in range(nframes):
            a = frames[min(f, len(frames) - 1)]
            idx = np.zeros(H * W, int)
            m = a[..., 3].reshape(-1) > 0
            rgb = a[..., :3].reshape(-1, 3)
            idx[m] = [lut[tuple(int(v) for v in c)] for c in rgb[m]]
            cels.append({"frame": f, "indices": idx.tolist()})
        layers.append({"name": n, "parent": parents.get(n, ""), "group": False, "cels": cels,
                       "hidden": bool(props.get(n, {}).get("hidden", False)), "opacity": int(props.get(n, {}).get("opacity", 0)),
                       "locked": bool(props.get(n, {}).get("locked", False))})
    durations = durations or [100] * nframes
    job = {"name": name, "width": W, "height": H, "palette": palette, "layers": layers,
           "frames": [{"duration": int(d)} for d in durations],
           "tags": [{"name": t, "from": a, "to": b, "loops": True} for t, a, b in tags],
           "poses": [dict(layer=l, frame=f, angle=float(a), x=float(x), y=float(y), pivotX=float(px), pivotY=float(py))
                     for l, f, a, x, y, px, py in poses]}
    path = OUT / "pas_jobs" / f"{name}.json"; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(job))
    return path


def build(job_path, name, timeout=1800):
    """Headless Unity on the sandbox: .pas at Assets/Built/<name>.pas, every frame rendered back by the plugin's own
    compositor into out/agentdraw/pas_render/<name>/pas_frame_NN.png. Returns (ok, render dir, log path)."""
    render = OUT / "pas_render" / name; render.mkdir(parents=True, exist_ok=True)
    log = OUT / "pas_jobs" / f"{name}.log"
    cmd = [UNITY, "-batchmode", "-nographics", "-projectPath", str(SANDBOX), "-logFile", str(log),
           "-executeMethod", "PipelineSandbox.SandboxBuild.Run", "-job", str(pathlib.Path(job_path).resolve()),
           "-pas", f"Assets/Built/{name}.pas", "-render", str(render)]
    rc = subprocess.call(cmd, timeout=timeout)
    text = log.read_text(errors="replace") if log.exists() else ""
    ok = rc == 0 and "[SandboxBuild] OK" in text
    return ok, render, log


def build_many(items, timeout=3600):
    """items = [(job_path, name), ...]: one headless Unity run builds them all. Returns (rc, log path)."""
    lst = OUT / "pas_jobs" / "batch.txt"
    lines = []
    for job, name in items:
        render = OUT / "pas_render" / name; render.mkdir(parents=True, exist_ok=True)
        lines.append(f"{pathlib.Path(job).resolve()}|Assets/Built/{name}.pas|{render}")
    lst.write_text("\n".join(lines) + "\n")
    log = OUT / "pas_jobs" / "batch.log"
    rc = subprocess.call([UNITY, "-batchmode", "-nographics", "-projectPath", str(SANDBOX), "-logFile", str(log),
                          "-executeMethod", "PipelineSandbox.SandboxBuild.Run", "-jobs", str(lst)], timeout=timeout)
    return rc, log
