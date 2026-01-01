# vmux examples

Run anything in the cloud. These are example scripts for [vmux](https://vmux.sdan.io).

## setup

```bash
uv tool install vmux-cli
vmux login
```

## examples

### hello world

```bash
vmux run python hello.py
```

5 seconds. prints cwd, lists files, counts to 5. good sanity check.

### long-running

```bash
vmux run -d python epoch_counter.py
```

detached. close your laptop. job keeps running.

```bash
vmux ps
vmux logs -f <job_id>
vmux attach <job_id>
```

### web servers

```bash
vmux run -p 8000 python burrow.py
```

expose a port, get a preview URL. websockets just work.

burrow is a fastapi demo with:
- websocket broadcasting
- server-sent events
- real-time metrics
- graceful shutdown

### collaborative terminal

```bash
vmux run -p 8000 python collab-terminal/server.py
```

shared bash session. multiple users connect to same PTY via websocket.

### network probe

```bash
vmux run python netprobe.py
```

measures latency, jitter, packet loss to cloudflare, google, aws. periodic speed tests.

### ml training

```bash
vmux run python train_arithmetic.py
```

teaches a 1B LLM to add numbers via RL. watch reward go from ~0.66 → 1.0.

```bash
vmux run -d python train_llama.py
```

fine-tunes llama-3.1-8B. longer job, run detached.

requires tinker api key:
```bash
vmux secret set TINKER_API_KEY
```

## cli

```
vmux run python train.py          # run in the cloud
vmux run -d python train.py       # detached
vmux run -p 8000 python server.py # expose port, get preview URL

vmux ps                           # list jobs
vmux logs -f <id>                 # follow logs
vmux attach <id>                  # back in your tmux session
vmux stop <id>                    # kill it
```

## more

[vmux.sdan.io](https://vmux.sdan.io)
