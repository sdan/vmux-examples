#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["vllm"]
# ///
"""
OpenAI-compatible LLM server using vLLM.

Start the server:
    vmux run --provider modal --gpu A10G -dp 8080 python vllm_server.py

Query it:
    curl https://<preview-url>/v1/chat/completions \
      -H "Authorization: Bearer vmux" \
      -H "Content-Type: application/json" \
      -d '{"model": "NousResearch/Meta-Llama-3-8B-Instruct",
           "messages": [{"role": "user", "content": "Hello!"}]}'

Environment:
    VMUX_MODEL    Model to serve (default: NousResearch/Meta-Llama-3-8B-Instruct)
    PORT          Port to listen on (default: 8080)
"""

import os
import subprocess
import sys

MODEL = os.environ.get("VMUX_MODEL", "NousResearch/Meta-Llama-3-8B-Instruct")
PORT = os.environ.get("PORT", "8080")


def main():
    print(f"[vmux:stage] loading")
    print(f"Model: {MODEL}")
    print(f"Port:  {PORT}")

    cmd = [
        sys.executable,
        "-m", "vllm.entrypoints.openai.api_server",
        "--model", MODEL,
        "--host", "0.0.0.0",
        "--port", PORT,
        "--api-key", "vmux",
    ]

    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
