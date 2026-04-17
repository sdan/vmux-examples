#!/usr/bin/env python3
"""
JupyterLab - run notebooks in the cloud.

    vmux run --provider modal -dp 8888 python jupyter.py
    vmux run --provider modal --gpu T4 -dp 8888 python jupyter.py  # with GPU

Opens JupyterLab with no password, accessible via preview URL.
Modal images bake in Jupyter + Torch + JAX + matplotlib + Hugging Face by default.
"""

import os
import subprocess

if __name__ == "__main__":
    # Install jupyter + matplotlib
    subprocess.call(["pip", "install", "-q", "jupyterlab", "matplotlib"])
    print("[vmux:stage] starting", flush=True)
    port = os.environ.get("PORT", "8888")
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
