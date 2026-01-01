# vmux examples

<img src="og.png" width="100%" />

Example scripts for [vmux](https://vmux.sdan.io). Run Python in the cloud.

## Setup

```bash
uv tool install vmux-cli
vmux login
```

## Examples

### Hello World

```bash
vmux run python hello.py
```

A 5-second sanity check that prints the working directory, lists files, and counts to 5. Good for verifying your setup works.

### Long-running Jobs

```bash
vmux run -d python epoch_counter.py
```

The `-d` flag works like Docker - it detaches from the container and lets the job run in the background. You can close your laptop and the job keeps running.

```bash
vmux ps                    # like docker ps
vmux logs -f <job_id>      # like docker logs -f
vmux attach <job_id>       # like docker attach, but it's tmux (may take a few seconds to load)
vmux stop <job_id>         # like docker stop
```

### Web Servers

```bash
vmux run -p 8000 python burrow.py
vmux run -dp 8000 python burrow.py  # detached + port
```

The `-p` flag exposes a port and gives you a preview URL like `https://<job_id>.purr.ge`. WebSockets are proxied automatically.

Burrow is a production-style FastAPI demo that shows WebSocket broadcasting, Server-Sent Events, a real-time metrics dashboard, and graceful shutdown handling.

### Collaborative Terminal

```bash
vmux run -p 8000 python collab-terminal/server.py
```

A shared bash session where multiple users connect to the same PTY via WebSocket. Anyone with the preview URL can join and type commands.

### Network Probe

```bash
vmux run python netprobe.py
```

A network analytics tool that measures latency, jitter, and packet loss to Cloudflare, Google, and AWS endpoints. It runs periodic speed tests and displays results in a live dashboard.

### ML Training

```bash
vmux run python train_arithmetic.py
```

Teaches a 1B-parameter LLM to add numbers using reinforcement learning. You can watch the reward climb from ~0.66 to 1.0 as the model learns.

```bash
vmux run -d python train_llama.py
```

Fine-tunes Llama-3.1-8B on instruction-following. This is a longer job so you'll want to run it detached.

Both examples require a Tinker API key:
```bash
vmux secret set TINKER_API_KEY
```

## CLI Reference

```
vmux run python train.py          # like uv run, but in the cloud
vmux run -d python train.py       # detached, like docker -d
vmux run -p 8000 python server.py # expose port, get preview URL
vmux run -dp 8000 python server.py # detached + port

vmux ps                           # list running containers
vmux logs -f <id>                 # follow logs
vmux attach <id>                  # back in your tmux session
vmux stop <id>                    # stop container
```

## More

See [vmux.sdan.io](https://vmux.sdan.io) for documentation.
