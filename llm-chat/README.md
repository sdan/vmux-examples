# vmux LLM Chat

Full-stack LLM chat with vLLM backend and web UI — one command.

## Quick Start

```bash
vmux run --provider modal --gpu A10G -dp 8000 python main.py
```

Opens a chat UI at the preview URL. Default model: `openai/gpt-oss-20b`.

> **Note**: GPT-OSS uses MXFP4 quantization which requires compute capability 8.0+. Use A10G or A100, not T4.

## Other Models

```bash
# GPT-OSS 20B (default) - requires A10G/A100
vmux run --provider modal --gpu A10G -dp 8000 python main.py

# Qwen 2.5 3B (works on T4, fast load)
vmux run --provider modal --gpu T4 -dp 8000 -e MODEL=Qwen/Qwen2.5-3B-Instruct python main.py

# Llama 3.1 70B (large, needs A100)
vmux run --provider modal --gpu A100 -dp 8000 -e MODEL=meta-llama/Llama-3.1-70B-Instruct python main.py
```

## Environment Variables

- `MODEL` - HuggingFace model ID (default: `openai/gpt-oss-20b`)
- `PORT` - Server port (default: `8000`)

## Architecture

```
┌─────────────────────────────────────┐
│  main.py                            │
│  ├─ FastAPI (port 8000)             │
│  │   └─ Chat UI (HTML/JS)           │
│  └─ vLLM (port 8080, internal)      │
│       └─ OpenAI-compatible API      │
└─────────────────────────────────────┘
```

Everything runs in one process — no separate frontend/backend deploy.
