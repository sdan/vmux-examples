---
name: vmux
description: Deploy to vmux cloud compute. Use when user says "deploy", "vmux", "run in cloud", "preview URL", "GPU", or wants to run commands on remote compute with optional GPU access.
---

# vmux — Cloud Compute for Agents

Run any command in the cloud. GPU in one flag.

**IMPORTANT: Always use `vmux session` commands (not `vmux run` or `vmux logs`).** The session API returns machine-readable JSON that you can parse. Never use `vmux run`, `vmux logs -f`, or `vmux attach` — those are interactive commands for humans.

## Commands (Always Use These)

```bash
vmux session run --json -d [flags] <command>    # Start job → returns JSON
vmux session logs --json <job_id> --offset <n>  # Poll logs → returns JSON
vmux session exec --json <job_id> "<cmd>"       # Run command → returns JSON
vmux session stop <job_id>                      # Stop job
vmux ps                                         # List jobs
```

## Start a Job

```bash
vmux session run --json -d [flags] <command>
```

**Always include `-d` (detach) with session commands.**

**Flags:**
| Flag | Description |
|------|-------------|
| `-d` | Detach (required for session API) |
| `-p <port>` | Expose port for preview URL |
| `-e KEY=VAL` | Set environment variable |
| `--provider modal` | Use Modal for GPU |
| `--gpu <type>` | GPU: T4, L4, A10G, A100, H100 |

**Example:**
```bash
vmux session run --json -d -p 8000 --provider modal --gpu A10G python server.py
```

**Response:**
```json
{"event":"job_started","job_id":"abc123","preview_urls":{"8000":"https://8000-abc123-token.purr.ge"}}
```

## Poll Logs

```bash
vmux session logs --json <job_id> --offset <n>
```

Track `offset` between calls to get only new logs. Start with `--offset 0`.

**Response:**
```json
{"logs":"Installing dependencies...\n","offset":142,"truncated":false}
```

## Execute Command in Sandbox

```bash
vmux session exec --json <job_id> "<command>"
```

**Response:**
```json
{"stdout":"hello\n","stderr":"","exit_code":0}
```

## Stop Job

```bash
vmux session stop <job_id>
```

## GPU Tiers

```bash
--gpu T4      # 16GB, budget inference
--gpu A10G    # 24GB, production (use for LLMs like gpt-oss, llama-70b)
--gpu A100    # 80GB, training
--gpu H100    # 80GB, fastest
```

## Lifecycle Pattern

```python
import json, subprocess

def shell(cmd):
    return subprocess.check_output(cmd, shell=True, text=True)

# 1. Start job
result = json.loads(shell("vmux session run --json -d -p 8000 python server.py"))
job_id = result["job_id"]
preview_url = result.get("preview_urls", {}).get("8000")

# 2. Poll logs until ready
offset = 0
ready = False
while not ready:
    time.sleep(2)
    logs = json.loads(shell(f"vmux session logs --json {job_id} --offset {offset}"))
    offset = logs["offset"]
    print(logs["logs"], end="")
    if "running on" in logs["logs"].lower() or "uvicorn" in logs["logs"].lower():
        ready = True

# 3. Use preview URL or exec commands
shell(f'vmux session exec --json {job_id} "nvidia-smi"')

# 4. Stop when done
shell(f"vmux session stop {job_id}")
```

## Example: Train nanoGPT on H100

```bash
# Start training job
vmux session run --json -d --provider modal --gpu H100 "bash -c 'pip install torch numpy transformers datasets tiktoken wandb tqdm && git clone https://github.com/karpathy/nanoGPT && cd nanoGPT && python data/shakespeare_char/prepare.py && python train.py config/train_shakespeare_char.py'"

# Poll logs (repeat with updated offset)
vmux session logs --json <job_id> --offset 0

# Stop when done
vmux session stop <job_id>
```

## DO NOT USE

These commands are for humans only, not agents:
- ❌ `vmux run` (use `vmux session run --json -d`)
- ❌ `vmux logs -f` (use `vmux session logs --json`)
- ❌ `vmux attach` (interactive terminal, not for agents)
