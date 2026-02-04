# vmux Skills for OpenAI Codex

Teach Codex CLI to deploy to vmux cloud compute with GPU access.

## Install

Copy the skill to your user skills directory:

```bash
# macOS/Linux
cp -r skills/vmux ~/.agents/skills/vmux

# Or symlink for auto-updates
ln -s "$(pwd)/skills/vmux" ~/.agents/skills/vmux
```

Restart Codex to load the skill.

## Usage

Once installed, Codex automatically uses vmux when you say:

- "deploy this to the cloud"
- "run this with a GPU"
- "give me a preview URL"
- "vmux run ..."

Or invoke directly:

```
$vmux python server.py
```

## What Codex Learns

The skill teaches Codex the full vmux session API:

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

Codex knows how to request GPUs via Modal:

```bash
vmux session run --json -dp 8000 --provider modal --gpu A10G python llm.py
```

GPU tiers: T4 (16GB, budget) → L4/A10G (24GB, production) → A100/H100 (80GB, training)

## Example Conversation

**You:** Deploy my FastAPI server with a preview URL

**Codex:**
```bash
vmux session run --json -dp 8000 python main.py
```
Started job `abc123`. Preview URL: https://8000-abc123-xyz.purr.ge

**You:** Now run it with a GPU for inference

**Codex:**
```bash
vmux session run --json -dp 8000 --provider modal --gpu A10G python main.py
```
Started Modal job with A10G GPU. Preview URL: https://8000-def456-xyz.purr.ge

## Skill Configuration

To disable the skill without deleting it, add to `~/.codex/config.toml`:

```toml
[[skills.config]]
path = "~/.agents/skills/vmux"
enabled = false
```
