# vmux LLM Chat

A clean, minimal chat interface for open-source LLMs.

**Frontend**: Next.js (deploy to Vercel)
**Backend**: vLLM on GPU (deploy via vmux)

## Quick Start

### 1. Start the backend

```bash
# From this directory
vmux run --provider modal --gpu A10G -dp 8000 python backend.py

# Or with a different model
vmux run --provider modal --gpu A100 -dp 8000 -e MODEL=meta-llama/Llama-3.1-70B-Instruct python backend.py
```

Copy the preview URL (e.g., `https://8000-<job>-<token>.purr.ge`).

### 2. Run the frontend

```bash
npm install
npm run dev
```

Open http://localhost:3000 and paste your backend URL.

### 3. Deploy frontend to Vercel

```bash
npx vercel
```

## Architecture

```
┌─────────────────┐      ┌─────────────────┐
│  Next.js (Vercel) │ ──→ │  vLLM (vmux)    │
│  - Chat UI       │      │  - OpenAI API   │
│  - Streaming     │      │  - GPU compute  │
└─────────────────┘      └─────────────────┘
```

## Environment Variables

**Backend** (`backend.py`):
- `MODEL` - HuggingFace model ID (default: `NousResearch/Meta-Llama-3-8B-Instruct`)
- `PORT` - Server port (default: `8000`)

## Models

| Model | GPU | Command |
|-------|-----|---------|
| Llama 3 8B | A10G | `vmux run --gpu A10G -dp 8000 python backend.py` |
| Llama 3.1 70B | A100 | `vmux run --gpu A100 -dp 8000 -e MODEL=meta-llama/Llama-3.1-70B-Instruct python backend.py` |
| Mistral 7B | T4 | `vmux run --gpu T4 -dp 8000 -e MODEL=mistralai/Mistral-7B-Instruct-v0.3 python backend.py` |
