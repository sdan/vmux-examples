---
name: vmux
description: Deploy to vmux cloud compute. Use when user says "deploy", "vmux", "run in cloud", "preview URL", "GPU", or wants to run commands on remote compute with optional GPU access.
---

# vmux — Cloud Compute for Agents

Run any command in the cloud. Close your laptop, keep running. GPU in one flag.

## Quick Reference

```bash
vmux session run --json -dp 8000 python server.py   # Start job, get JSON
vmux session logs --json <job_id> --offset 0        # Poll logs
vmux session exec --json <job_id> "ls -la"          # Run command in job
vmux session stop <job_id>                          # Stop job
```

## Session API (Machine-Readable)

Use `vmux session --json` for structured output. Every command returns JSON.

### Start a Job

```bash
vmux session run --json [flags] <command>
```

**Flags:**
| Flag | Short | Description |
|------|-------|-------------|
| `--detach` | `-d` | Run in background (always use for sessions) |
| `--port <port>` | `-p` | Expose port for preview URL |
| `--env KEY=VAL` | `-e` | Set environment variable |
| `--provider modal` | | Use Modal for GPU access |
| `--gpu <type>` | | GPU type: T4, L4, A10G, A100, H100 |

**Response:**
```json
{"event":"job_started","job_id":"abc123","preview_urls":{"8000":"https://8000-abc123-token.purr.ge"}}
```

### Poll Logs

```bash
vmux session logs --json <job_id> --offset <n>
```

Returns logs since byte offset. Track `offset` to avoid duplicates.

**Response:**
```json
{"logs":"Starting server...\n","offset":42,"truncated":false}
```

### Execute Command

```bash
vmux session exec --json <job_id> "<command>"
```

Run a command inside the running job's sandbox.

**Response:**
```json
{"stdout":"hello\n","stderr":"","exit_code":0}
```

### Stop Job

```bash
vmux session stop <job_id>
```

### List Jobs

```bash
vmux ps --json
```

## GPU Access (Modal)

```bash
# T4: 16GB, budget inference
vmux session run --json -dp 8000 --provider modal --gpu T4 python inference.py

# A10G: 24GB, production inference (required for gpt-oss, llama-70b)
vmux session run --json -dp 8000 --provider modal --gpu A10G python llm_server.py

# A100: 80GB, training
vmux session run --json -dp 8000 --provider modal --gpu A100 python train.py
```

## Lifecycle Pattern

```python
# 1. Start job
result = shell("vmux session run --json -dp 8000 python server.py")
job_id = json.loads(result)["job_id"]
preview_url = json.loads(result)["preview_urls"]["8000"]

# 2. Poll until ready (check for "Uvicorn running" or similar)
offset = 0
while not ready:
    logs = shell(f"vmux session logs --json {job_id} --offset {offset}")
    data = json.loads(logs)
    offset = data["offset"]
    if "running on" in data["logs"].lower():
        ready = True

# 3. Use the preview URL
response = requests.get(preview_url)

# 4. Execute commands in sandbox if needed
shell(f'vmux session exec --json {job_id} "pip install newpackage"')

# 5. Stop when done
shell(f"vmux session stop {job_id}")
```

## Human Commands (Interactive)

For interactive use (not in agent loops):

```bash
vmux run -dp 8000 python server.py   # Deploy, stream logs
vmux logs -f <job_id>                # Follow logs
vmux attach <job_id>                 # Interactive tmux (Ctrl+B,D to detach)
vmux stop <job_id>                   # Stop job
vmux ps                              # List jobs
```

## After Deploy

Always report:
1. **Preview URL**: `https://8000-<job_id>-<token>.purr.ge`
2. **Job ID**: For logs/stop/attach
3. **Monitor**: `vmux logs -f <job_id>`
4. **Stop**: `vmux stop <job_id>`
