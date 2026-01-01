# vmux examples

Example scripts for [vmux](https://vmux.sdan.io) - run any command in the cloud.

## Quick Start

```bash
# Install vmux
uv tool install vmux-cli

# Login with GitHub
vmux login

# Run an example
vmux run python hello.py
```

## Examples

### Basic Scripts

| Example | Description | Command |
|---------|-------------|---------|
| `hello.py` | Simple test script | `vmux run python hello.py` |
| `ticker.py` | 2-min counter | `vmux run python ticker.py` |
| `epoch_counter.py` | 2-hour epoch timer | `vmux run -d python epoch_counter.py` |
| `holiday.py` | Festive tree animation | `vmux run python holiday.py` |

### Network & Monitoring

| Example | Description | Command |
|---------|-------------|---------|
| `netprobe.py` | Network analytics (latency, jitter, speed) | `vmux run python netprobe.py` |

### ML Training (requires Tinker API)

| Example | Description | Command |
|---------|-------------|---------|
| `train_arithmetic.py` | RL: teach LLM to add | `vmux run -e TINKER_API_KEY=xxx python train_arithmetic.py` |
| `train_llama.py` | SL: fine-tune Llama-3.1-8B | `vmux run -d python train_llama.py` |

### Web Servers (with preview URLs)

| Example | Description | Command |
|---------|-------------|---------|
| `burrow.py` | Real-time data dashboard | `vmux run -p 8000 python burrow.py` |
| `collab-terminal/` | Shared terminal via WebSocket | `vmux run --preview python collab-terminal/server.py` |

## CLI Flags Reference

```bash
vmux run [OPTIONS] COMMAND

Options:
  -d, --detach     Run in background, return job ID
  -p, --port INT   Expose port for preview URL (repeatable)
  --preview        Shorthand for -p 8000
  -e, --env K=V    Set environment variable
```

## Common Patterns

```bash
# Run and watch output
vmux run python hello.py

# Run in background
vmux run -d python long_job.py

# Web server with preview URL
vmux run -p 8000 python server.py

# Multiple ports
vmux run -p 3000 -p 8000 npm run dev

# With environment variables
vmux run -e API_KEY=xxx python script.py

# Check running jobs
vmux ps

# Follow logs
vmux logs -f <job_id>

# Attach to tmux session
vmux attach <job_id>

# Stop a job
vmux stop <job_id>
```

## What Each Example Demonstrates

### `hello.py`
Basic vmux test - prints info and counts to 5. Good for verifying setup.

### `ticker.py` / `epoch_counter.py`
Long-running scripts for testing `-d` (detach) mode and log streaming.

### `holiday.py`
Fun ASCII art animation. Shows terminal output rendering in the cloud.

### `netprobe.py`
Async network monitoring with aiohttp. Measures latency to Cloudflare, Google, AWS endpoints. Runs periodic speed tests.

### `train_arithmetic.py`
Teaches a 1B-parameter LLM to add numbers using RL. Watch reward go from ~0.66 to 1.0 as it learns.

### `train_llama.py`
Fine-tunes Llama-3.1-8B on instruction-following. Demonstrates longer training jobs with `-d`.

### `burrow.py`
Production-style FastAPI server with:
- WebSocket connection pooling
- Server-Sent Events streaming
- Real-time metrics dashboard
- Graceful shutdown handling

Access via your preview URL: `https://<job_id>.purr.ge`

### `collab-terminal/`
Collaborative terminal - multiple users share the same bash session via WebSocket. See [collab-terminal/README.md](collab-terminal/README.md) for architecture details.

## License

MIT
