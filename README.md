# vmux examples

Small, fast examples you can read in a minute and run in a second.

## Setup

```bash
uv tool install vmux-cli
vmux login
```

## Quick start

```bash
# Hello world
vmux run python hello.py

# Web server with preview URL
vmux run -dp 8000 python web_server.py

# GPU compute (Modal)
vmux run --provider modal --gpu T4 python gpu_hello.py
```

## Examples

All web servers honor `PORT`, so `-p/-dp` works everywhere.

### Cloudflare (fast start)

| Example | What it is | Command |
|---------|------------|---------|
| `hello.py` | Sanity check | `vmux run python hello.py` |
| `web_server.py` | FastAPI hello + preview URL | `vmux run -dp 8000 python web_server.py` |
| `background_job.py` | Long-running logs | `vmux run -d python background_job.py` |
| `burrow.py` | WebSocket + SSE dashboard | `vmux run -dp 8000 python burrow.py` |
| `collab-terminal/` | Shared terminal over WS | `vmux run -dp 8000 python collab-terminal/server.py` |
| `gradio_chat.py` | Gradio UI | `vmux run -dp 7860 python gradio_chat.py` |
| `waves/` | Bun + Vite demo | `cd waves && vmux run -dp 5173 bun run dev` |

### Modal (GPU + heavy deps)

| Example | What it is | Command |
|---------|------------|---------|
| `gpu_hello.py` | CUDA sanity check | `vmux run --provider modal --gpu T4 python gpu_hello.py` |
| `vllm_server.py` | OpenAI-compatible API | `vmux run --provider modal --gpu A10G -dp 8080 python vllm_server.py` |
| `whisper_api.py` | Audio transcription | `vmux run --provider modal --gpu T4 -dp 8000 python whisper_api.py` |
| `embeddings_api.py` | RAG embeddings | `vmux run --provider modal --gpu T4 -dp 8000 python embeddings_api.py` |
| `image_gen.py` | SDXL Turbo | `vmux run --provider modal --gpu A10G -dp 8000 python image_gen.py` |
| `ollama_chat.py` | Local Llama (Ollama) | `vmux run --provider modal --gpu T4 python ollama_chat.py` |
| `jupyter.py` | JupyterLab | `vmux run --provider modal -dp 8888 python jupyter.py` |
| `llm-chat/` | Full-stack LLM chat | See `llm-chat/README.md` |

## Patterns

### Preview URLs

Expose a port to get a public URL:

```bash
vmux run -p 8000 python server.py          # attached
vmux run -dp 8000 python server.py         # detached
```

The preview URL shows a loading page with live logs until your server starts.

### Detached jobs

Run in background, check later:

```bash
vmux run -d python train.py     # start
vmux ps                         # list jobs
vmux logs -f <id>               # follow logs
vmux attach <id>                # interactive tmux
vmux stop <id>                  # stop
```

### Run vs attach

`vmux run` starts a job and creates a tmux session in the sandbox.  
`vmux attach <id>` connects to **that same session** for interactive work.

```bash
# Start a server
vmux run -dp 8000 python web_server.py

# Later, attach to the same tmux session
vmux attach <job_id>
```

### Session mode (LLM / automation)

Machine‑readable JSON events for Claude/Codex tool use:

```bash
vmux session run --json -dp 8000 python web_server.py
vmux session logs --json <job_id> --offset 0
vmux session exec --json "python -c \"print(1+1)\""
vmux session stop <job_id>
```

Note: `vmux session --json` is machine‑readable and does **not** attach to tmux.  
For interactive shells, use `vmux attach <job_id>`.

#### Claude Code / Codex CLI example

Use `vmux session --json` as the external executor from your LLM loop:

```bash
# 1) Start a job (JSON events)
vmux session run --json -dp 8000 python web_server.py

# 2) Stream logs with offsets (for the LLM to track progress)
vmux session logs --json <job_id> --offset 0

# 3) Execute a command inside the same job
vmux session exec --json "python -c \"print('hello from vmux')\""

# 4) Stop when done
vmux session stop <job_id>
```

Legacy: `vmux tool` is still available as a hidden alias.

### GPU selection

```bash
vmux run --provider modal --gpu T4 python script.py    # 16GB, budget
vmux run --provider modal --gpu L4 python script.py    # 24GB, balanced
vmux run --provider modal --gpu A10G python script.py  # 24GB, fast
vmux run --provider modal --gpu A100 python script.py  # 80GB, training
vmux run --provider modal --gpu H100 python script.py  # 80GB, fastest
```

### Snapshot cache (Modal)

```bash
# Cache deps after a successful run
vmux run --provider modal --cache python vllm_server.py
```

### Environment variables

```bash
# Pass env vars
vmux run -e API_KEY=xxx python script.py

# Use secrets (stored in keychain)
vmux secret set HF_TOKEN
vmux run --provider modal python script.py  # HF_TOKEN available
```

## Stage markers

Add markers to your scripts for cleaner vmux output:

```python
print("[vmux:stage] loading")      # start a stage
print("[vmux:stage:done] loading") # end a stage
print("[vmux:ready] http://...")   # signal ready
```

## API usage

After starting `vllm_server.py`:

```bash
curl https://<preview-url>/v1/chat/completions \
  -H "Authorization: Bearer vmux" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "NousResearch/Meta-Llama-3-8B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

After starting `whisper_api.py`:

```bash
curl -X POST https://<preview-url>/transcribe -F "file=@audio.mp3"
```

After starting `embeddings_api.py`:

```bash
curl -X POST https://<preview-url>/embed \
  -H "Content-Type: application/json" \
  -d '{"texts": ["hello", "world"]}'
```
