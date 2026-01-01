# Collaborative Terminal

A real-time collaborative terminal that multiple users can share. Built with FastAPI, WebSockets, and vmux preview URLs.

## What This Does

- Spawns a shared bash terminal in the cloud
- Multiple users connect via WebSocket to the same PTY
- Everyone sees the same output and can type commands
- Uses xterm.js for a real terminal experience in the browser

## Quick Start

```bash
# Install vmux
uv tool install vmux-cli

# Login with GitHub
vmux login

# Run the collaborative terminal with a preview URL
vmux run --preview python server.py
```

You'll get a public URL like `https://abc123xyz.purr.ge` that anyone can open to join the terminal session.

## How It Works

### Architecture

```
┌─────────────────┐     ┌──────────────────────────────────────┐
│   Browser 1     │     │         Cloudflare Edge              │
│   (xterm.js)    │────▶│                                      │
└─────────────────┘     │  ┌────────────────────────────────┐  │
                        │  │     Worker (vmux-api)          │  │
┌─────────────────┐     │  │                                │  │
│   Browser 2     │────▶│  │  *.purr.ge → wsConnect()      │  │
│   (xterm.js)    │     │  │           → containerFetch()  │  │
└─────────────────┘     │  └────────────────────────────────┘  │
                        │              │                        │
┌─────────────────┐     │              ▼                        │
│   Browser N     │────▶│  ┌────────────────────────────────┐  │
│   (xterm.js)    │     │  │   Durable Object (Sandbox)     │  │
└─────────────────┘     │  │                                │  │
                        │  │  ┌──────────────────────────┐  │  │
                        │  │  │   Container              │  │  │
                        │  │  │                          │  │  │
                        │  │  │  FastAPI + uvicorn       │  │  │
                        │  │  │       ↓                  │  │  │
                        │  │  │  WebSocket endpoint      │  │  │
                        │  │  │       ↓                  │  │  │
                        │  │  │  Shared PTY (bash)       │  │  │
                        │  │  │                          │  │  │
                        │  │  └──────────────────────────┘  │  │
                        │  └────────────────────────────────┘  │
                        └──────────────────────────────────────┘
```

### Key Components

1. **Preview URL Routing** (`*.purr.ge`)
   - Wildcard DNS points all subdomains to Cloudflare
   - Worker extracts job ID from hostname
   - Routes to the correct Durable Object/container

2. **WebSocket Proxying**
   - Worker detects `Upgrade: websocket` header
   - Uses `sandbox.wsConnect(request, 8000)` to proxy to container
   - Full bidirectional WebSocket communication

3. **Shared PTY**
   - Python `pty` module creates a pseudo-terminal
   - Multiple WebSocket clients read/write to same PTY
   - Terminal resize events are forwarded

## Code Walkthrough

### server.py

```python
# Create PTY when first user joins a room
master_fd, slave_fd = pty.openpty()
pid = os.fork()

if pid == 0:
    # Child: become the bash process
    os.setsid()
    os.dup2(slave_fd, 0)  # stdin
    os.dup2(slave_fd, 1)  # stdout
    os.dup2(slave_fd, 2)  # stderr
    os.execvp("/bin/bash", ["/bin/bash"])
else:
    # Parent: read from PTY and broadcast to all clients
    asyncio.create_task(read_pty(room_id, master_fd))
```

### Worker Preview Proxy

```typescript
// In worker/src/index.ts
if (url.hostname.endsWith(".purr.ge")) {
  const jobId = url.hostname.split(".")[0];

  // WebSocket upgrade
  if (request.headers.get("Upgrade") === "websocket") {
    return await sandbox.wsConnect(request, 8000);
  }

  // Regular HTTP
  return await sandbox.containerFetch(proxyRequest, 8000);
}
```

## Features

- **Real-time collaboration** - See others typing instantly
- **User count** - Shows how many people are connected
- **Terminal resize** - Automatically adapts to window size
- **Full terminal emulation** - Colors, cursor movement, vim, etc.
- **No authentication** - Anyone with the URL can join

## Use Cases

- **Pair programming** - Share a terminal for debugging together
- **Live demos** - Show terminal commands to an audience
- **Teaching** - Students follow along in real-time
- **Support** - Debug customer issues collaboratively

## Try the Fun Stuff

Once connected, try the `purr` command:

```bash
purr         # Purring cat
purr walk    # Cat walks across screen (like sl)
purr nyan    # Nyan cat with rainbow trail
```

## Technical Notes

### Dependencies

The container needs `websockets` for uvicorn WebSocket support:
```
fastapi
uvicorn
websockets  # Required for WebSocket!
```

### Port Binding

The server must bind to `0.0.0.0:8000` (not `127.0.0.1`):
```python
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Preview URL Format

Preview URLs use the full 12-character job ID:
```
https://{job_id}.purr.ge
```

## Extending This

Ideas for modifications:
- Add authentication (check a password before allowing connection)
- Add read-only mode for viewers
- Record and replay terminal sessions
- Add chat alongside the terminal
- Support multiple terminal tabs

## License

MIT
