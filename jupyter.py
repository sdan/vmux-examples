#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["jupyterlab", "pip", "numpy"]
# ///
"""
JupyterLab - run notebooks in the cloud.

    vmux run --provider modal -dp 8888 python jupyter.py
    vmux run --provider modal --gpu T4 -dp 8888 python jupyter.py  # with GPU

Opens JupyterLab with no password, accessible via preview URL.
"""

import os
import subprocess
import sys


def _write_startup_script(gpu: bool) -> None:
    startup_dir = os.path.expanduser("~/.ipython/profile_default/startup")
    os.makedirs(startup_dir, exist_ok=True)
    script_path = os.path.join(startup_dir, "00-vmux-deps.py")
    gpu_flag = "1" if gpu else "0"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(
            f"""\
import os
import subprocess
import importlib.util

GPU = os.environ.get("VMUX_GPU", "none").lower() not in ("", "none")
PIP_ENV = {{**os.environ, "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PIP_NO_INPUT": "1"}}

def _has(pkg: str) -> bool:
    return importlib.util.find_spec(pkg) is not None

def _pip(args):
    subprocess.check_call(["python", "-m", "pip", *args], env=PIP_ENV)

def _ensure_torch():
    if _has("torch"):
        return
    if GPU:
        print("[vmux] Installing PyTorch (CUDA)...", flush=True)
        _pip(["install", "torch", "torchvision", "torchaudio", "--index-url",
              "https://download.pytorch.org/whl/cu121"])
    else:
        print("[vmux] Installing PyTorch (CPU)...", flush=True)
        _pip(["install", "torch", "torchvision", "torchaudio"])

def _ensure_jax():
    if _has("jax"):
        return
    if GPU:
        print("[vmux] Installing JAX (CUDA)...", flush=True)
        _pip(["install", "jax[cuda12]", "-f",
              "https://storage.googleapis.com/jax-releases/jax_cuda_releases.html"])
    else:
        print("[vmux] Installing JAX (CPU)...", flush=True)
        _pip(["install", "jax"])

_ensure_torch()
_ensure_jax()
"""
        )
    print(f"[vmux] IPython startup deps configured ({script_path})", flush=True)

if __name__ == "__main__":
    print("[vmux:stage] starting", flush=True)
    port = os.environ.get("PORT", "8888")
    gpu = os.environ.get("VMUX_GPU", "none").lower() not in ("", "none")
    _write_startup_script(gpu)

    cmd = [
        "jupyter", "lab",
        "--ip=0.0.0.0",
        f"--port={port}",
        "--no-browser",
        "--allow-root",
        "--ServerApp.token=",
        "--ServerApp.password=",
        "--ServerApp.allow_origin=*",
        "--ServerApp.allow_remote_access=True",
        "--ServerApp.disable_check_xsrf=True",
        "--ServerApp.log_level=INFO",
    ]
    subprocess.call(cmd)
