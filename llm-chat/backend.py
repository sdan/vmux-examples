#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["vllm", "fastapi", "uvicorn", "httpx"]
# ///
"""
LLM Chat Backend - vLLM server with OpenAI-compatible API.

Deploy with vmux:

    vmux run --provider modal --gpu A10G -dp 8000 python backend.py

Environment variables:
    MODEL    Model to load (default: NousResearch/Meta-Llama-3-8B-Instruct)
    PORT     Port to serve on (default: 8000)

The server exposes:
    GET  /health              Health check (ready status + model info)
    POST /v1/chat/completions OpenAI-compatible chat completions API
    GET  /v1/models           List available models
"""

import json
import os
import subprocess
import sys
import threading
import time

MODEL = os.environ.get("MODEL", "NousResearch/Meta-Llama-3-8B-Instruct")
PORT = int(os.environ.get("PORT", "8000"))
VLLM_PORT = 8080


def start_vllm():
    """Start vLLM OpenAI-compatible server."""
    cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", MODEL,
        "--host", "127.0.0.1",
        "--port", str(VLLM_PORT),
        "--served-model-name", "default",
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def wait_for_vllm(timeout=600):
    """Wait for vLLM to be ready."""
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{VLLM_PORT}/health")
            urllib.request.urlopen(req, timeout=5)
            return True
        except Exception:
            time.sleep(2)
    return False


def create_app():
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse, StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    import httpx

    app = FastAPI(title="vmux LLM Backend")
    vllm_ready = threading.Event()

    # Enable CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Start vLLM in background
    def init_vllm():
        print(f"[vmux:stage] loading")
        print(f"Starting vLLM with model: {MODEL}")
        proc = start_vllm()

        def stream_logs():
            for line in proc.stdout:
                print(line.decode(), end="")
        threading.Thread(target=stream_logs, daemon=True).start()

        if wait_for_vllm():
            print(f"[vmux:stage:done] loading")
            print(f"[vmux:ready] http://0.0.0.0:{PORT}")
            vllm_ready.set()
        else:
            print("ERROR: vLLM failed to start")

    threading.Thread(target=init_vllm, daemon=True).start()

    @app.get("/health")
    def health():
        return {"ready": vllm_ready.is_set(), "model": MODEL}

    @app.get("/v1/models")
    def models():
        return {
            "object": "list",
            "data": [{"id": "default", "object": "model", "owned_by": "vmux"}]
        }

    @app.api_route("/v1/{path:path}", methods=["GET", "POST", "OPTIONS"])
    async def proxy(path: str, request: Request):
        """Proxy requests to vLLM."""
        if request.method == "OPTIONS":
            return JSONResponse({})

        if not vllm_ready.is_set():
            return JSONResponse({"error": "Model still loading"}, status_code=503)

        url = f"http://127.0.0.1:{VLLM_PORT}/v1/{path}"

        if request.method == "GET":
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(url)
                return JSONResponse(resp.json())

        body = await request.json()

        if body.get("stream"):
            async def stream():
                try:
                    async with httpx.AsyncClient(timeout=httpx.Timeout(300, connect=30)) as client:
                        async with client.stream("POST", url, json=body) as resp:
                            async for chunk in resp.aiter_bytes():
                                yield chunk
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

            return StreamingResponse(
                stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                },
            )
        else:
            async with httpx.AsyncClient(timeout=300) as client:
                resp = await client.post(url, json=body)
                return JSONResponse(resp.json())

    return app


if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=PORT)
