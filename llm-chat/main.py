#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["vllm", "fastapi", "uvicorn", "httpx"]
# ///
"""
vmux Chat - Full-stack LLM Chat with Next.js frontend + vLLM backend.

Run locally (auto-builds frontend if npm available):
    uv run main.py

Deploy with vmux (uses pre-built frontend from out/):
    vmux run --provider modal --gpu A10G -dp 8000 uv run main.py

Environment variables:
    MODEL    Model to load (default: openai/gpt-oss-20b)
    PORT     Port to serve on (default: 8000)
"""

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

MODEL = os.environ.get("MODEL", "openai/gpt-oss-20b")
PORT = int(os.environ.get("PORT", "8000"))
VLLM_PORT = 8080

# Directory where Next.js static export lives
STATIC_DIR = Path(__file__).parent / "frontend"


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
    from fastapi.responses import JSONResponse, StreamingResponse, FileResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    import httpx

    app = FastAPI(title="vmux LLM Chat")
    vllm_ready = threading.Event()
    vllm_stage = {"current": "downloading"}

    # Enable CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Start vLLM in background
    def init_vllm():
        print(f"[vmux:stage] downloading")
        print(f"Starting vLLM with model: {MODEL}")
        proc = start_vllm()
        vllm_stage["current"] = "loading"
        print(f"[vmux:stage] loading")

        def stream_logs():
            for line in proc.stdout:
                print(line.decode(), end="")
        threading.Thread(target=stream_logs, daemon=True).start()

        if wait_for_vllm():
            vllm_stage["current"] = "ready"
            print(f"[vmux:stage:done] loading")
            print(f"[vmux:ready] http://0.0.0.0:{PORT}")
            vllm_ready.set()
        else:
            print("ERROR: vLLM failed to start")

    threading.Thread(target=init_vllm, daemon=True).start()

    @app.get("/health")
    def health():
        return {
            "ready": vllm_ready.is_set(),
            "model": MODEL,
            "stage": vllm_stage["current"],
        }

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

    # Serve static frontend if it exists
    if STATIC_DIR.exists():
        # Serve static assets (JS, CSS, images)
        app.mount("/_next", StaticFiles(directory=STATIC_DIR / "_next"), name="next-static")

        # Serve index.html for root
        @app.get("/")
        async def serve_index():
            index_file = STATIC_DIR / "index.html"
            if index_file.exists():
                return FileResponse(index_file, media_type="text/html")
            return HTMLResponse("<h1>Frontend not built. Run: npm run build</h1>")

        # Catch-all for other static files
        @app.get("/{path:path}")
        async def serve_static(path: str):
            # Skip API routes
            if path.startswith("v1/") or path == "health":
                return JSONResponse({"error": "Not found"}, status_code=404)

            file_path = STATIC_DIR / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)

            # Try with .html extension
            html_path = STATIC_DIR / f"{path}.html"
            if html_path.exists():
                return FileResponse(html_path, media_type="text/html")

            # Try index.html in directory
            index_path = STATIC_DIR / path / "index.html"
            if index_path.exists():
                return FileResponse(index_path, media_type="text/html")

            # Fallback to main index for SPA routing
            return FileResponse(STATIC_DIR / "index.html", media_type="text/html")
    else:
        @app.get("/")
        async def no_frontend():
            return HTMLResponse("""
            <html>
            <head><title>vmux Chat</title></head>
            <body style="font-family: system-ui; padding: 40px; text-align: center;">
                <h1>Frontend not built</h1>
                <p>Run <code>npm run build</code> to build the Next.js frontend.</p>
                <p>The API is available at <code>/v1/chat/completions</code></p>
            </body>
            </html>
            """)

    return app


def build_frontend():
    """Build Next.js frontend if not already built."""
    import shutil

    # Check if npm/node available
    if not shutil.which("npm"):
        print("npm not found - skipping frontend build")
        return False

    print("[vmux] Building frontend...")
    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("[vmux] Frontend built successfully")
            return True
        else:
            print(f"[vmux] Frontend build failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"[vmux] Frontend build error: {e}")
        return False


if __name__ == "__main__":
    import uvicorn

    # Auto-build frontend if missing
    if not STATIC_DIR.exists():
        print(f"Frontend not found at {STATIC_DIR}")
        build_frontend()

    if STATIC_DIR.exists():
        print(f"[vmux] Serving frontend from {STATIC_DIR}")
    else:
        print(f"[vmux] Running API-only mode (no frontend)")

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=PORT)
