#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["vllm", "fastapi", "uvicorn"]
# ///
"""
Full-stack LLM Chat - vLLM + Web UI in one command.

    vmux run --provider modal --gpu A10G -dp 8000 python main.py

Environment:
    MODEL   Model to load (default: openai/gpt-oss-20b)
    PORT    Port to serve on (default: 8000)
"""

import json
import os
import subprocess
import sys
import threading
import time

MODEL = os.environ.get("MODEL", "openai/gpt-oss-20b")
PORT = int(os.environ.get("PORT", "8000"))
VLLM_PORT = 8080

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>vmux Chat</title>
  <link rel="icon" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxNiAxNiIgc2hhcGUtcmVuZGVyaW5nPSJjcmlzcEVkZ2VzIj48cmVjdCB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIGZpbGw9IiMwZjExMTUiLz48cmVjdCB4PSI0IiB5PSIwIiB3aWR0aD0iMiIgaGVpZ2h0PSIxIiBmaWxsPSIjZjVmNWY0Ii8+PHJlY3QgeD0iNCIgeT0iMSIgd2lkdGg9IjIiIGhlaWdodD0iMSIgZmlsbD0iI2Y1ZjVmNCIvPjxyZWN0IHg9IjQiIHk9IjIiIHdpZHRoPSIyIiBoZWlnaHQ9IjEiIGZpbGw9IiNmNWY1ZjQiLz48cmVjdCB4PSI0IiB5PSIzIiB3aWR0aD0iMiIgaGVpZ2h0PSIxIiBmaWxsPSIjZjVmNWY0Ii8+PHJlY3QgeD0iNSIgeT0iMiIgd2lkdGg9IjEiIGhlaWdodD0iMiIgZmlsbD0iI2ZlY2FjYSIvPjxyZWN0IHg9IjEwIiB5PSIwIiB3aWR0aD0iMiIgaGVpZ2h0PSIxIiBmaWxsPSIjZjVmNWY0Ii8+PHJlY3QgeD0iMTAiIHk9IjEiIHdpZHRoPSIyIiBoZWlnaHQ9IjEiIGZpbGw9IiNmNWY1ZjQiLz48cmVjdCB4PSIxMCIgeT0iMiIgd2lkdGg9IjIiIGhlaWdodD0iMSIgZmlsbD0iI2Y1ZjVmNCIvPjxyZWN0IHg9IjEwIiB5PSIzIiB3aWR0aD0iMiIgaGVpZ2h0PSIxIiBmaWxsPSIjZjVmNWY0Ii8+PHJlY3QgeD0iMTAiIHk9IjIiIHdpZHRoPSIxIiBoZWlnaHQ9IjIiIGZpbGw9IiNmZWNhY2EiLz48cmVjdCB4PSI0IiB5PSI0IiB3aWR0aD0iOCIgaGVpZ2h0PSIyIiBmaWxsPSIjZjVmNWY0Ii8+PHJlY3QgeD0iMyIgeT0iNiIgd2lkdGg9IjEwIiBoZWlnaHQ9IjQiIGZpbGw9IiNmNWY1ZjQiLz48cmVjdCB4PSI0IiB5PSIxMCIgd2lkdGg9IjgiIGhlaWdodD0iMiIgZmlsbD0iI2Y1ZjVmNCIvPjxyZWN0IHg9IjUiIHk9IjEyIiB3aWR0aD0iNiIgaGVpZ2h0PSIxIiBmaWxsPSIjZjVmNWY0Ii8+PHJlY3QgeD0iNSIgeT0iNyIgd2lkdGg9IjIiIGhlaWdodD0iMiIgZmlsbD0iIzFmMjkzNyIvPjxyZWN0IHg9IjkiIHk9IjciIHdpZHRoPSIyIiBoZWlnaHQ9IjIiIGZpbGw9IiMxZjI5MzciLz48cmVjdCB4PSI1IiB5PSI3IiB3aWR0aD0iMSIgaGVpZ2h0PSIxIiBmaWxsPSIjZmZmIi8+PHJlY3QgeD0iOSIgeT0iNyIgd2lkdGg9IjEiIGhlaWdodD0iMSIgZmlsbD0iI2ZmZiIvPjxyZWN0IHg9IjciIHk9IjEwIiB3aWR0aD0iMiIgaGVpZ2h0PSIxIiBmaWxsPSIjZmNhNWE1Ii8+PC9zdmc+">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11/styles/github-dark.min.css">
  <script src="https://cdn.jsdelivr.net/npm/highlight.js@11/highlight.min.js"></script>
  <style>
    :root { --bg:#0a0a0a; --bg2:#1a1a1a; --bg3:#2a2a2a; --fg:#e5e5e5; --fg2:#888; --accent:#10b981; --border:#333; --code-bg:#161616; }
    @media(prefers-color-scheme:light) { :root { --bg:#fff; --bg2:#f5f5f5; --bg3:#e5e5e5; --fg:#1a1a1a; --fg2:#666; --accent:#059669; --border:#ddd; --code-bg:#f8f8f8; } }
    *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
    html, body { height:100%; overflow:hidden; }
    body { font-family:'Inter',-apple-system,BlinkMacSystemFont,system-ui,sans-serif; font-size:15px; line-height:1.6; background:var(--bg); color:var(--fg); -webkit-font-smoothing:antialiased; }
    main { height:100dvh; display:flex; flex-direction:column; max-width:900px; margin:0 auto; }

    .header { flex-shrink:0; padding:16px 20px; border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; }
    .header-left { display:flex; align-items:center; gap:10px; }
    .status { width:8px; height:8px; border-radius:50%; background:var(--accent); }
    .status.loading { background:#f59e0b; animation:pulse 1.5s ease-in-out infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
    .model-name { font-size:14px; font-weight:600; color:var(--fg); }
    .model-badge { font-size:11px; padding:3px 8px; background:var(--bg2); border-radius:4px; color:var(--fg2); }
    .clear-btn { padding:6px 12px; font-size:13px; background:transparent; border:1px solid var(--border); border-radius:6px; color:var(--fg2); cursor:pointer; transition:all 0.15s; }
    .clear-btn:hover { border-color:var(--fg2); color:var(--fg); }

    .messages { flex:1; overflow-y:auto; padding:24px 20px; }
    .empty { height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:12px; }
    .empty h1 { font-size:28px; font-weight:700; background:linear-gradient(135deg,var(--accent),#3b82f6); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
    .empty p { font-size:15px; color:var(--fg2); }

    .msg { margin-bottom:24px; animation:fadeIn 0.2s ease-out; }
    @keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
    .msg-header { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
    .msg-avatar { width:28px; height:28px; border-radius:6px; display:flex; align-items:center; justify-content:center; font-size:14px; font-weight:600; }
    .msg.user .msg-avatar { background:var(--accent); color:#fff; }
    .msg.assistant .msg-avatar { background:var(--bg3); color:var(--fg); }
    .msg-role { font-size:13px; font-weight:600; color:var(--fg2); }
    .msg-content { padding-left:36px; }
    .msg.user .msg-text { background:var(--bg2); padding:12px 16px; border-radius:12px; display:inline-block; max-width:85%; }
    .msg.assistant .msg-text { line-height:1.7; }
    .msg.assistant .msg-text p { margin-bottom:12px; }
    .msg.assistant .msg-text p:last-child { margin-bottom:0; }
    .msg.assistant .msg-text ul, .msg.assistant .msg-text ol { margin:12px 0; padding-left:24px; }
    .msg.assistant .msg-text li { margin-bottom:6px; }
    .msg.assistant .msg-text strong { font-weight:600; }
    .msg.assistant .msg-text em { font-style:italic; color:var(--fg2); }
    .msg.assistant .msg-text a { color:var(--accent); text-decoration:none; }
    .msg.assistant .msg-text a:hover { text-decoration:underline; }

    .code-block { position:relative; margin:16px 0; border-radius:8px; overflow:hidden; background:var(--code-bg); border:1px solid var(--border); }
    .code-header { display:flex; align-items:center; justify-content:space-between; padding:8px 12px; background:var(--bg3); border-bottom:1px solid var(--border); }
    .code-lang { font-size:12px; font-weight:500; color:var(--fg2); text-transform:uppercase; }
    .copy-btn { padding:4px 10px; font-size:12px; background:transparent; border:1px solid var(--border); border-radius:4px; color:var(--fg2); cursor:pointer; transition:all 0.15s; display:flex; align-items:center; gap:4px; }
    .copy-btn:hover { border-color:var(--accent); color:var(--accent); }
    .copy-btn.copied { border-color:var(--accent); color:var(--accent); }
    .code-block pre { margin:0; padding:16px; overflow-x:auto; font-family:'JetBrains Mono','Fira Code',monospace; font-size:13px; line-height:1.5; }
    .code-block code { background:transparent !important; padding:0 !important; }

    code:not(pre code) { background:var(--bg3); padding:2px 6px; border-radius:4px; font-family:'JetBrains Mono',monospace; font-size:0.9em; }

    .cursor { display:inline-block; width:2px; height:1em; background:var(--accent); margin-left:2px; animation:blink 1s step-end infinite; vertical-align:text-bottom; }
    @keyframes blink { 50%{opacity:0} }
    .msg-footer { padding-left:36px; margin-top:8px; display:flex; align-items:center; gap:12px; }
    .elapsed { font-size:12px; color:var(--fg2); }
    .msg-actions { display:flex; gap:4px; }
    .msg-action { padding:4px 8px; font-size:12px; background:transparent; border:none; color:var(--fg2); cursor:pointer; border-radius:4px; transition:all 0.15s; }
    .msg-action:hover { background:var(--bg2); color:var(--fg); }

    .suggestions { padding:12px 20px 20px; display:flex; gap:8px; flex-wrap:wrap; justify-content:center; }
    .suggestion { padding:10px 16px; font-size:14px; background:var(--bg2); border:1px solid var(--border); border-radius:20px; color:var(--fg); cursor:pointer; transition:all 0.15s; }
    .suggestion:hover { border-color:var(--accent); background:var(--bg3); }
    .suggestion:disabled { opacity:0.5; cursor:not-allowed; }

    .input-area { flex-shrink:0; padding:16px 20px; padding-bottom:max(16px,env(safe-area-inset-bottom)); border-top:1px solid var(--border); background:var(--bg); }
    .input-row { display:flex; gap:12px; align-items:flex-end; }
    .input-field { flex:1; padding:14px 18px; font-size:15px; font-family:inherit; background:var(--bg2); border:1px solid var(--border); border-radius:16px; color:var(--fg); outline:none; resize:none; min-height:52px; max-height:200px; transition:border-color 0.15s; }
    .input-field:focus { border-color:var(--accent); }
    .input-field::placeholder { color:var(--fg2); }
    .send { width:52px; height:52px; border-radius:14px; background:var(--accent); border:none; color:#fff; font-size:20px; cursor:pointer; display:flex; align-items:center; justify-content:center; flex-shrink:0; transition:all 0.15s; }
    .send:disabled { opacity:0.4; cursor:not-allowed; }
    .send:not(:disabled):hover { transform:scale(1.05); filter:brightness(1.1); }
    .send:not(:disabled):active { transform:scale(0.95); }

    @media(max-width:600px) {
      main { max-width:100%; }
      .messages { padding:16px; }
      .msg-content { padding-left:0; margin-top:8px; }
      .msg-footer { padding-left:0; }
      .msg.user .msg-text { max-width:100%; }
    }
  </style>
</head>
<body>
  <main>
    <div class="header">
      <div class="header-left">
        <span class="status loading" id="status"></span>
        <span class="model-name" id="model">Loading...</span>
        <span class="model-badge">GPU</span>
      </div>
      <button class="clear-btn" id="clear" style="display:none">Clear chat</button>
    </div>
    <div class="messages" id="messages">
      <div class="empty" id="empty">
        <h1>vmux Chat</h1>
        <p id="model-display">Loading model...</p>
      </div>
    </div>
    <div class="suggestions" id="suggestions">
      <button class="suggestion" disabled>Explain how transformers work</button>
      <button class="suggestion" disabled>Write a Python quicksort</button>
      <button class="suggestion" disabled>What makes a good API?</button>
    </div>
    <div class="input-area">
      <div class="input-row">
        <textarea class="input-field" id="input" placeholder="Ask anything..." rows="1" disabled></textarea>
        <button class="send" id="send" disabled>↑</button>
      </div>
    </div>
  </main>
  <script>
    const $ = s => document.querySelector(s);
    const $$ = s => document.querySelectorAll(s);
    let messages = [], generating = false;

    marked.setOptions({ breaks: true, gfm: true });

    $('#input').addEventListener('input', e => {
      e.target.style.height = 'auto';
      e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
    });

    $('#input').addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
    });
    $('#send').addEventListener('click', send);
    $('#clear').addEventListener('click', clearChat);

    $$('.suggestion').forEach(btn => {
      btn.addEventListener('click', () => send(btn.textContent));
    });

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
          const name = data.model.split('/').pop();
          const stages = {
            'downloading': 'Downloading ' + name + '...',
            'loading': 'Loading into GPU...',
          };
          $('#model-display').textContent = stages[data.stage] || 'Starting...';
          $('#model').textContent = data.stage || 'Loading...';
          setTimeout(checkHealth, 2000);
        }
      } catch {
        $('#model-display').textContent = 'Connecting...';
        setTimeout(checkHealth, 3000);
      }
    }
    checkHealth();

    function clearChat() {
      messages = [];
      $('#messages').innerHTML = '<div class="empty" id="empty"><h1>vmux Chat</h1><p id="model-display">' + $('#model').textContent + '</p></div>';
      $('#suggestions').style.display = 'flex';
      $('#clear').style.display = 'none';
    }

    function renderMarkdown(text) {
      let html = marked.parse(text);
      // Wrap code blocks with copy button
      html = html.replace(/<pre><code class="language-(\\w+)">([\s\S]*?)<\\/code><\\/pre>/g, (_, lang, code) => {
        const decoded = code.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&').replace(/&quot;/g,'"');
        return '<div class="code-block"><div class="code-header"><span class="code-lang">' + lang + '</span><button class="copy-btn" onclick="copyCode(this)"><span>Copy</span></button></div><pre><code class="language-' + lang + '">' + code + '</code></pre></div>';
      });
      html = html.replace(/<pre><code>([\s\S]*?)<\\/code><\\/pre>/g, (_, code) => {
        return '<div class="code-block"><div class="code-header"><span class="code-lang">code</span><button class="copy-btn" onclick="copyCode(this)"><span>Copy</span></button></div><pre><code>' + code + '</code></pre></div>';
      });
      return html;
    }

    function copyCode(btn) {
      const code = btn.closest('.code-block').querySelector('code').textContent;
      navigator.clipboard.writeText(code);
      btn.innerHTML = '<span>Copied!</span>';
      btn.classList.add('copied');
      setTimeout(() => { btn.innerHTML = '<span>Copy</span>'; btn.classList.remove('copied'); }, 2000);
    }
    window.copyCode = copyCode;

    function copyMessage(btn) {
      const text = btn.closest('.msg').querySelector('.msg-text').textContent;
      navigator.clipboard.writeText(text);
      btn.textContent = 'Copied!';
      setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
    }
    window.copyMessage = copyMessage;

    function addMsg(role, text = '') {
      const empty = $('#empty');
      if (empty) empty.remove();
      if (role === 'user') {
        $('#suggestions').style.display = 'none';
        $('#clear').style.display = 'block';
      }

      const id = Date.now();
      const div = document.createElement('div');
      div.className = 'msg ' + role;
      div.id = 'msg-' + id;

      const avatar = role === 'user' ? 'U' : 'AI';
      const roleLabel = role === 'user' ? 'You' : 'Assistant';

      if (role === 'user') {
        div.innerHTML = '<div class="msg-header"><div class="msg-avatar">' + avatar + '</div><span class="msg-role">' + roleLabel + '</span></div><div class="msg-content"><div class="msg-text">' + esc(text) + '</div></div>';
      } else {
        div.innerHTML = '<div class="msg-header"><div class="msg-avatar">' + avatar + '</div><span class="msg-role">' + roleLabel + '</span></div><div class="msg-content"><div class="msg-text"><span class="cursor"></span></div></div>';
      }

      $('#messages').appendChild(div);
      $('#messages').scrollTop = $('#messages').scrollHeight;
      return id;
    }

    function updateMsg(id, text, done = false, elapsed = null, tokenCount = null) {
      const msgText = document.querySelector('#msg-' + id + ' .msg-text');
      const msgEl = document.querySelector('#msg-' + id);
      if (msgText) {
        if (done) {
          msgText.innerHTML = renderMarkdown(text);
          msgText.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
          // Add footer with elapsed time, tokens/s, and actions
          let footer = msgEl.querySelector('.msg-footer');
          if (!footer) {
            footer = document.createElement('div');
            footer.className = 'msg-footer';
            msgEl.querySelector('.msg-content').appendChild(footer);
          }
          const secs = elapsed ? (elapsed/1000).toFixed(1) : 0;
          const tps = (elapsed && tokenCount) ? (tokenCount / (elapsed/1000)).toFixed(1) : null;
          const stats = elapsed ? '<span class="elapsed">' + secs + 's' + (tps ? ' · ' + tps + ' tok/s' : '') + '</span>' : '';
          footer.innerHTML = stats + '<div class="msg-actions"><button class="msg-action" onclick="copyMessage(this)">Copy</button></div>';
        } else {
          msgText.innerHTML = esc(text) + '<span class="cursor"></span>';
        }
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
      let tokenCount = 0;

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
              if (chunk) {
                fullText += chunk;
                tokenCount++;
                updateMsg(assistantId, fullText);
              }
            } catch {}
          }
        }

        messages.push({ role: 'assistant', content: fullText });
        updateMsg(assistantId, fullText, true, Date.now() - start, tokenCount);
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
        if vllm_ready.is_set():
            return {"ready": True, "model": MODEL, "stage": "ready"}
        elif vllm_started.is_set():
            return {"ready": False, "model": MODEL, "stage": "loading"}
        else:
            return {"ready": False, "model": MODEL, "stage": "downloading"}

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
