#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["vllm", "fastapi", "uvicorn"]
# ///
"""
Full-stack LLM Chat - vLLM + Web UI in one command.

    vmux run --provider modal --gpu A10G -dp 8000 python main.py

Environment:
    MODEL   Model to load (default: NousResearch/Meta-Llama-3-8B-Instruct)
    PORT    Port to serve on (default: 8000)
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

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>vmux Chat</title>
  <link rel="icon" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxNiAxNiIgc2hhcGUtcmVuZGVyaW5nPSJjcmlzcEVkZ2VzIj48cmVjdCB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIGZpbGw9IiMwZjExMTUiLz48cmVjdCB4PSI0IiB5PSIwIiB3aWR0aD0iMiIgaGVpZ2h0PSIxIiBmaWxsPSIjZjVmNWY0Ii8+PHJlY3QgeD0iNCIgeT0iMSIgd2lkdGg9IjIiIGhlaWdodD0iMSIgZmlsbD0iI2Y1ZjVmNCIvPjxyZWN0IHg9IjQiIHk9IjIiIHdpZHRoPSIyIiBoZWlnaHQ9IjEiIGZpbGw9IiNmNWY1ZjQiLz48cmVjdCB4PSI0IiB5PSIzIiB3aWR0aD0iMiIgaGVpZ2h0PSIxIiBmaWxsPSIjZjVmNWY0Ii8+PHJlY3QgeD0iNSIgeT0iMiIgd2lkdGg9IjEiIGhlaWdodD0iMiIgZmlsbD0iI2ZlY2FjYSIvPjxyZWN0IHg9IjEwIiB5PSIwIiB3aWR0aD0iMiIgaGVpZ2h0PSIxIiBmaWxsPSIjZjVmNWY0Ii8+PHJlY3QgeD0iMTAiIHk9IjEiIHdpZHRoPSIyIiBoZWlnaHQ9IjEiIGZpbGw9IiNmNWY1ZjQiLz48cmVjdCB4PSIxMCIgeT0iMiIgd2lkdGg9IjIiIGhlaWdodD0iMSIgZmlsbD0iI2Y1ZjVmNCIvPjxyZWN0IHg9IjEwIiB5PSIzIiB3aWR0aD0iMiIgaGVpZ2h0PSIxIiBmaWxsPSIjZjVmNWY0Ii8+PHJlY3QgeD0iMTAiIHk9IjIiIHdpZHRoPSIxIiBoZWlnaHQ9IjIiIGZpbGw9IiNmZWNhY2EiLz48cmVjdCB4PSI0IiB5PSI0IiB3aWR0aD0iOCIgaGVpZ2h0PSIyIiBmaWxsPSIjZjVmNWY0Ii8+PHJlY3QgeD0iMyIgeT0iNiIgd2lkdGg9IjEwIiBoZWlnaHQ9IjQiIGZpbGw9IiNmNWY1ZjQiLz48cmVjdCB4PSI0IiB5PSIxMCIgd2lkdGg9IjgiIGhlaWdodD0iMiIgZmlsbD0iI2Y1ZjVmNCIvPjxyZWN0IHg9IjUiIHk9IjEyIiB3aWR0aD0iNiIgaGVpZ2h0PSIxIiBmaWxsPSIjZjVmNWY0Ii8+PHJlY3QgeD0iNSIgeT0iNyIgd2lkdGg9IjIiIGhlaWdodD0iMiIgZmlsbD0iIzFmMjkzNyIvPjxyZWN0IHg9IjkiIHk9IjciIHdpZHRoPSIyIiBoZWlnaHQ9IjIiIGZpbGw9IiMxZjI5MzciLz48cmVjdCB4PSI1IiB5PSI3IiB3aWR0aD0iMSIgaGVpZ2h0PSIxIiBmaWxsPSIjZmZmIi8+PHJlY3QgeD0iOSIgeT0iNyIgd2lkdGg9IjEiIGhlaWdodD0iMSIgZmlsbD0iI2ZmZiIvPjxyZWN0IHg9IjciIHk9IjEwIiB3aWR0aD0iMiIgaGVpZ2h0PSIxIiBmaWxsPSIjZmNhNWE1Ii8+PC9zdmc+">
  <style>
    :root { --bg:#fff; --bg2:rgba(0,0,0,0.04); --fg:#000; --fg2:rgba(0,0,0,0.5); --blue:#007AFF; --border:rgba(0,0,0,0.08); }
    @media(prefers-color-scheme:dark) { :root { --bg:#000; --bg2:rgba(255,255,255,0.08); --fg:#fff; --fg2:rgba(255,255,255,0.5); --blue:#0A84FF; --border:rgba(255,255,255,0.1); } }
    *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
    html, body { height:100%; overflow:hidden; }
    body { font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text',system-ui,sans-serif; font-size:16px; line-height:1.5; background:var(--bg); color:var(--fg); -webkit-font-smoothing:antialiased; }
    main { height:100dvh; display:flex; flex-direction:column; }

    .header { flex-shrink:0; padding:14px 16px; border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:center; gap:8px; }
    .status { width:8px; height:8px; border-radius:50%; background:#34C759; }
    .status.loading { background:#FF9500; animation:pulse 1.5s ease-in-out infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
    .model-name { font-size:14px; font-weight:500; color:var(--fg2); }

    .messages { flex:1; overflow-y:auto; padding:20px 16px; }
    .empty { height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px; }
    .empty h1 { font-size:24px; font-weight:600; }
    .empty p { font-size:15px; color:var(--fg2); }

    .msg { margin-bottom:12px; }
    .msg.user { text-align:right; }
    .msg.assistant { text-align:left; }
    .bubble { display:inline-block; max-width:85%; padding:10px 14px; border-radius:18px; font-size:15px; line-height:1.45; word-wrap:break-word; white-space:pre-wrap; }
    .bubble.user { background:var(--blue); color:#fff; border-bottom-right-radius:4px; }
    .bubble.assistant { background:var(--bg2); border-bottom-left-radius:4px; }
    .bubble { animation:fadeIn 0.2s ease-out; }
    @keyframes fadeIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }

    .cursor { display:inline-block; width:2px; height:1em; background:var(--fg2); margin-left:2px; animation:blink 1s step-end infinite; vertical-align:text-bottom; }
    @keyframes blink { 50%{opacity:0} }
    .elapsed { font-size:11px; color:var(--fg2); margin-top:4px; opacity:0.6; }

    .suggestions { padding:8px 16px 16px; display:flex; gap:8px; flex-wrap:wrap; justify-content:center; }
    .suggestion { padding:8px 14px; font-size:14px; background:none; border:1px solid var(--border); border-radius:18px; color:var(--fg2); cursor:pointer; transition:all 0.15s; }
    .suggestion:hover { border-color:var(--blue); color:var(--blue); }
    .suggestion:disabled { opacity:0.5; cursor:not-allowed; }

    .input-area { flex-shrink:0; padding:12px 16px; padding-bottom:max(12px,env(safe-area-inset-bottom)); border-top:1px solid var(--border); }
    .input-row { display:flex; gap:10px; align-items:flex-end; }
    .input-field { flex:1; padding:12px 16px; font-size:16px; font-family:inherit; background:var(--bg2); border:none; border-radius:24px; color:var(--fg); outline:none; resize:none; min-height:48px; max-height:160px; }
    .input-field::placeholder { color:var(--fg2); }
    .send { width:44px; height:44px; border-radius:50%; background:var(--blue); border:none; color:#fff; font-size:18px; cursor:pointer; display:flex; align-items:center; justify-content:center; flex-shrink:0; transition:all 0.15s; }
    .send:disabled { opacity:0.3; cursor:not-allowed; }
    .send:not(:disabled):hover { transform:scale(1.05); }
    .send:not(:disabled):active { transform:scale(0.95); }

    @media(min-width:768px) { .messages{padding:24px} .bubble{max-width:70%;font-size:16px} .empty h1{font-size:28px} }
  </style>
</head>
<body>
  <main>
    <div class="header">
      <span class="status loading" id="status"></span>
      <span class="model-name" id="model">Loading...</span>
    </div>
    <div class="messages" id="messages">
      <div class="empty" id="empty">
        <h1>vmux Chat</h1>
        <p id="model-display">Loading model...</p>
      </div>
    </div>
    <div class="suggestions" id="suggestions">
      <button class="suggestion" disabled>Explain quantum computing</button>
      <button class="suggestion" disabled>Write a haiku about code</button>
      <button class="suggestion" disabled>What is the meaning of life?</button>
    </div>
    <div class="input-area">
      <div class="input-row">
        <textarea class="input-field" id="input" placeholder="Message" rows="1" disabled></textarea>
        <button class="send" id="send" disabled>↑</button>
      </div>
    </div>
  </main>
  <script>
    const $ = s => document.querySelector(s);
    const $$ = s => document.querySelectorAll(s);
    let messages = [], generating = false;

    // Auto-resize textarea
    $('#input').addEventListener('input', e => {
      e.target.style.height = 'auto';
      e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px';
    });

    // Enter to send
    $('#input').addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
    });
    $('#send').addEventListener('click', send);

    // Suggestions
    $$('.suggestion').forEach(btn => {
      btn.addEventListener('click', () => send(btn.textContent));
    });

    // Health check
    async function checkHealth() {
      try {
        const res = await fetch('/health');
        const data = await res.json();
        if (data.ready) {
          $('#status').className = 'status';
          const name = data.model.split('/').pop();
          $('#model').textContent = name;
          $('#model-display').textContent = name;
          $('#input').disabled = false;
          $('#send').disabled = false;
          $$('.suggestion').forEach(b => b.disabled = false);
          $('#input').focus();
        } else {
          setTimeout(checkHealth, 2000);
        }
      } catch {
        setTimeout(checkHealth, 3000);
      }
    }
    checkHealth();

    function addMsg(role, text = '') {
      const empty = $('#empty');
      if (empty) empty.remove();
      if (role === 'user') $('#suggestions').style.display = 'none';

      const id = Date.now();
      const div = document.createElement('div');
      div.className = 'msg ' + role;
      div.id = 'msg-' + id;
      div.innerHTML = '<div class="bubble ' + role + '">' + (text ? esc(text) : '<span class="cursor"></span>') + '</div>';
      $('#messages').appendChild(div);
      $('#messages').scrollTop = $('#messages').scrollHeight;
      return id;
    }

    function updateMsg(id, text, done = false, elapsed = null) {
      const div = document.querySelector('#msg-' + id + ' .bubble');
      if (div) {
        div.innerHTML = esc(text) + (done ? '' : '<span class="cursor"></span>');
        if (done && elapsed) div.innerHTML += '<div class="elapsed">' + (elapsed/1000).toFixed(1) + 's</div>';
      }
      $('#messages').scrollTop = $('#messages').scrollHeight;
    }

    function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

    async function send(text) {
      const msg = text || $('#input').value.trim();
      if (!msg || generating) return;

      generating = true;
      $('#input').value = '';
      $('#input').style.height = 'auto';
      $('#send').disabled = true;

      addMsg('user', msg);
      messages.push({ role: 'user', content: msg });
      const assistantId = addMsg('assistant');

      const start = Date.now();
      let fullText = '';

      try {
        const res = await fetch('/v1/chat/completions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model: 'default', messages, stream: true })
        });

        const reader = res.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          for (const line of decoder.decode(value).split('\\n')) {
            if (!line.startsWith('data: ')) continue;
            const data = line.slice(6);
            if (data === '[DONE]') continue;
            try {
              const chunk = JSON.parse(data).choices?.[0]?.delta?.content || '';
              fullText += chunk;
              updateMsg(assistantId, fullText);
            } catch {}
          }
        }

        messages.push({ role: 'assistant', content: fullText });
        updateMsg(assistantId, fullText, true, Date.now() - start);
      } catch (e) {
        updateMsg(assistantId, 'Error: ' + e.message, true);
      }

      generating = false;
      $('#send').disabled = false;
      $('#input').focus();
    }
  </script>
</body>
</html>'''


def start_vllm():
    cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", MODEL,
        "--host", "127.0.0.1",
        "--port", str(VLLM_PORT),
        "--served-model-name", "default",
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def wait_for_vllm(timeout=600):
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{VLLM_PORT}/health", timeout=5)
            return True
        except:
            time.sleep(2)
    return False


def create_app():
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
    import httpx

    app = FastAPI()
    vllm_ready = threading.Event()
    vllm_started = threading.Event()

    def init_vllm():
        print(f"Loading {MODEL}...")
        proc = start_vllm()
        vllm_started.set()  # Signal that process has started
        threading.Thread(target=lambda: [print(l.decode(), end="") for l in proc.stdout], daemon=True).start()
        if wait_for_vllm():
            vllm_ready.set()
        else:
            print("ERROR: vLLM failed to start")

    # Start vLLM immediately in background
    threading.Thread(target=init_vllm, daemon=True).start()

    @app.get("/", response_class=HTMLResponse)
    def index():
        return HTML

    @app.get("/health")
    def health():
        return {"ready": vllm_ready.is_set(), "model": MODEL}

    @app.api_route("/v1/{path:path}", methods=["GET", "POST"])
    async def proxy(path: str, request: Request):
        if not vllm_ready.is_set():
            return JSONResponse({"error": "Model loading"}, status_code=503)

        url = f"http://127.0.0.1:{VLLM_PORT}/v1/{path}"

        if request.method == "GET":
            async with httpx.AsyncClient(timeout=60) as client:
                return JSONResponse((await client.get(url)).json())

        body = await request.json()
        if body.get("stream"):
            async def stream():
                async with httpx.AsyncClient(timeout=httpx.Timeout(300, connect=30)) as client:
                    async with client.stream("POST", url, json=body) as resp:
                        async for chunk in resp.aiter_bytes():
                            yield chunk
            return StreamingResponse(stream(), media_type="text/event-stream")
        else:
            async with httpx.AsyncClient(timeout=300) as client:
                return JSONResponse((await client.post(url, json=body)).json())

    return app


if __name__ == "__main__":
    import uvicorn
    # Signal ready immediately so Modal tunnel works
    print(f"[vmux:ready] http://0.0.0.0:{PORT}")
    uvicorn.run(create_app(), host="0.0.0.0", port=PORT)
