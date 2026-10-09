"""The one HTTP helper krea.py needs to talk to a running ComfyUI.

The server address comes from the COMFYUI_URL environment variable (default http://127.0.0.1:8188, which is where
start_comfy.sh listens). Only the standard library is used.
"""
import json
import os
import urllib.request

HOST = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")


def call(path, data=None):
    """GET HOST+path, or POST `data` as JSON when it is given. Returns the response body as bytes."""
    req = urllib.request.Request(HOST + path, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return r.read()
