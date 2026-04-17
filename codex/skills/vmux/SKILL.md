---
name: vmux
description: Deploy to vmux cloud compute. Use when user says "deploy", "vmux", "run in cloud", "preview URL", or wants to run commands on remote compute.
---

# vmux - Cloud Compute in 5 Seconds

Run any command in the cloud. Close your laptop, keep running.

## Setup

```bash
vmux whoami  # Check login status
vmux login   # If needed
```

## vmux run

```bash
vmux run [flags] <command>
```

### Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--json` | | Emit JSON events (for LLM/agent use) |
| `--detach` | `-d` | Run in background, return job ID immediately |
| `--port <port>` | `-p` | Expose port for preview URL (can use multiple times) |
| `--preview` | | Auto-detect port from framework and expose it |
| `--env KEY=VAL` | `-e` | Set environment variable |
| `--no-bundle` | | Skip bundling local packages (faster for scripts) |

### Flag Combinations

Flags can be combined: `-dp 8000` = detached + port 8000

```bash
vmux run python script.py           # Streams logs, blocks
vmux run -d python script.py        # Detached, returns job ID
vmux run -p 8000 python server.py   # Expose port 8000, get preview URL
vmux run -dp 8000 python server.py  # Detached + port (most common for web)
vmux run -d --preview bun run dev   # Auto-detect port from framework
vmux run -p 3000 -p 8000 npm run dev  # Multiple ports
vmux run -e API_KEY=xxx python app.py # With env var
```

### JSON Mode (for LLMs/agents)

```bash
vmux run --json -d python server.py
# Returns: {"job_id": "...", "preview_urls": {...}}
```

## After Deploy

Always give the user:
1. The **preview URL** (if port exposed) - format: `https://<port>-<job-id>-<token>.purr.ge`
2. The **job ID**
3. How to monitor: `vmux logs -f <job-id>`
4. How to stop: `vmux stop <job-id>`

## Other Commands

```bash
vmux ps                 # List running jobs
vmux logs <job-id>              # All logs
vmux logs -f <job-id>           # Follow logs in real-time
vmux logs --tail 50 <job-id>    # Last 50 lines
vmux logs -f --tail 50 <job-id> # Last 50, then follow
vmux logs --json <job-id>       # JSON output for agents
vmux logs --json --tail 20 <job-id>  # Last 20 lines as JSON
vmux exec <job-id> <cmd>                        # Run command in running job (stateful shell)
vmux exec <job-id> --file SRC[:DST] <cmd>       # Upload local file(s) into the job, then exec
vmux exec --json <job-id> <cmd>                 # JSON output
vmux exec --create <cmd>                        # Auto-create Modal sandbox, run command
vmux exec --create --provider cloudflare <cmd>  # Auto-create Cloudflare sandbox
vmux exec --create --gpu H100 <cmd>             # Modal with GPU
vmux attach <job-id>    # Interactive tmux session (Ctrl+B,D to detach)
vmux stop <job-id>      # Kill job
vmux stop -a            # Stop all running jobs
vmux debug <job-id>     # Show tmux status and processes
vmux secret set KEY     # Store secret in keychain
```

## Agent Workflow

For LLM/agent automation, use `--json` flags:

```bash
# Option A: Start job explicitly, then exec
vmux run --json -d -p 8000 python server.py
# Returns: {"job_id": "abc123", "preview_urls": {"8000": "https://..."}}

# Option B: Auto-create sandbox with exec --create
vmux exec --json --create --gpu H100 "pip install torch"
# Returns: {"job_id": "abc123", "stdout": "...", "exit_code": 0}

# Check logs (last 20 lines)
vmux logs --json --tail 20 abc123
# Returns: {"logs": "...", "lines": 20}

# Execute more commands (reuse job_id, stateful shell)
vmux exec --json abc123 "python train.py"
# Returns: {"job_id": "abc123", "stdout": "...", "exit_code": 0}

# Stop when done
vmux stop abc123
```

### Empty Sandbox (for interactive use)

```bash
# Provision empty sandbox (persistent until stopped)
vmux run -d sleep infinity                    # Cloudflare
vmux run -d --provider modal --gpu H100 sleep infinity  # Modal + GPU

# Or use exec --create (provisions + runs command in one step)
vmux exec --create "pip install torch"                    # Modal (default)
vmux exec --create --provider cloudflare "apt install -y curl"  # Cloudflare
vmux exec --create --gpu H100 "pip install torch"         # Modal + GPU
```

### Upload Local Files Into a Job

Use `vmux exec --file` to upload local scripts/configs into a running job (works on both Cloudflare and Modal providers):

```bash
vmux exec <job-id> --file ./prepare.py python /workspace/prepare.py
vmux exec <job-id> --file ./cfg.json:/workspace/cfg.json python train.py --config /workspace/cfg.json
```

## Monitoring Long-Running Commands

**Important:** `vmux exec` is non-streaming. For tailing logs:

### Option 1: Pipe to stdout + vmux logs (Recommended)

Run training with output to stdout:
```bash
vmux exec <job-id> "python -u train.py 2>&1 | tee -a train.log"
```

Then stream via:
```bash
vmux logs -f <job-id>
```

### Option 2: Poll log files

For file-based logs, poll periodically:
```bash
vmux exec <job-id> "tail -n 50 train.log"
```

### Option 3: Inspect Files via exec

```bash
vmux exec <job-id> "tail -n 50 /workspace/train.log"
```

### Option 4: Attach for interactive tailing

```bash
vmux attach <job-id>
# Inside tmux:
tail -f train.log
# Ctrl+B,D to detach
```
