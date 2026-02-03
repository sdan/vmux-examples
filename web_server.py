#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["fastapi", "uvicorn"]
# ///
"""
Simple Web Server - FastAPI hello world with preview URL.

    vmux run -dp 8000 python web_server.py

Opens a preview URL that proxies to your server.
"""

import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>vmux</title>
        <style>
            body {
                font-family: system-ui, sans-serif;
                background: #0f1115;
                color: #e5e7eb;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }
            .container {
                text-align: center;
                padding: 2rem;
            }
            h1 { font-size: 3rem; margin-bottom: 0.5rem; }
            p { color: #9ca3af; }
            a { color: #f59e0b; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>vmux</h1>
            <p>Your server is running.</p>
            <p><a href="/api/health">/api/health</a></p>
        </div>
    </body>
    </html>
    """


@app.get("/api/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    print(f"[vmux:ready] http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
