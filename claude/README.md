# vmux Skills for Claude Code

Teach Claude Code to deploy to vmux cloud compute with GPU access.

## Install

Copy the skill to your personal skills directory:

```bash
cp -r skills/vmux ~/.claude/skills/vmux
```

Or symlink for auto-updates:

```bash
ln -s "$(pwd)/skills/vmux" ~/.claude/skills/vmux
```

## Usage

Once installed, Claude Code automatically uses vmux when you say:

- "deploy this to the cloud"
- "run this with a GPU"
- "give me a preview URL"
- "vmux run ..."

Or invoke directly:

```
/vmux python server.py
```

## What Claude Learns

The skill teaches Claude the full vmux session API:

```bash
# Start a job (JSON output for parsing)
vmux session run --json -dp 8000 python server.py

# Poll logs with offset tracking
vmux session logs --json <job_id> --offset 0

# Execute commands in the sandbox
vmux session exec --json <job_id> "pip install torch"

# Stop when done
vmux session stop <job_id>
```

## GPU Access

Claude knows how to request GPUs via Modal:

```bash
vmux session run --json -dp 8000 --provider modal --gpu A10G python llm.py
```

GPU tiers: T4 (16GB, budget) → L4/A10G (24GB, production) → A100/H100 (80GB, training)

## Example Conversation

**You:** Deploy my FastAPI server with a preview URL

**Claude:**
```bash
vmux session run --json -dp 8000 python main.py
```
Started job `abc123`. Preview URL: https://8000-abc123-xyz.purr.ge

**You:** Now run it with a GPU for inference

**Claude:**
```bash
vmux session run --json -dp 8000 --provider modal --gpu A10G python main.py
```
Started Modal job with A10G GPU. Preview URL: https://8000-def456-xyz.purr.ge
