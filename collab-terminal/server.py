#!/usr/bin/env python3
"""
Collaborative Terminal Server - runs on vmux with preview URL

A simple FastAPI + WebSocket server that provides a shared terminal experience.
Multiple users can connect and see/send commands to the same PTY.
"""

import asyncio
import os
import pty
import select
import struct
import fcntl
import termios
from typing import Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(title="Collaborative Terminal")

# Connected clients per room
rooms: Dict[str, Set[WebSocket]] = {}

# PTY processes per room
pty_processes: Dict[str, dict] = {}


HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Collaborative Terminal</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css">
    <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #1a1a2e;
            color: #eee;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            padding: 12px 20px;
            background: #16213e;
            border-bottom: 1px solid #0f3460;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 { font-size: 18px; color: #e94560; }
        .info { color: #888; font-size: 13px; }
        .users {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .user-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #4ecdc4;
        }
        #terminal-container {
            flex: 1;
            padding: 10px;
        }
        #terminal {
            height: 100%;
        }
    </style>
</head>
<body>
    <header>
        <div>
            <h1>🐱 Collaborative Terminal</h1>
            <div class="info">Powered by vmux + purr.ge</div>
        </div>
        <div class="users">
            <span id="user-count">1 user</span>
            <div class="user-dot"></div>
        </div>
    </header>
    <div id="terminal-container">
        <div id="terminal"></div>
    </div>
    <script>
        const term = new Terminal({
            cursorBlink: true,
            fontSize: 14,
            fontFamily: 'Menlo, Monaco, monospace',
            theme: {
                background: '#1a1a2e',
                foreground: '#eee',
                cursor: '#e94560',
            }
        });
        const fitAddon = new FitAddon.FitAddon();
        term.loadAddon(fitAddon);
        term.open(document.getElementById('terminal'));
        fitAddon.fit();

        // WebSocket connection
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${protocol}//${location.host}/ws/main`);

        ws.onopen = () => {
            term.write('\\r\\n\\x1b[32mConnected to collaborative terminal!\\x1b[0m\\r\\n');
            // Send initial size
            ws.send(JSON.stringify({
                type: 'resize',
                cols: term.cols,
                rows: term.rows
            }));
        };

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === 'output') {
                term.write(msg.data);
            } else if (msg.type === 'users') {
                document.getElementById('user-count').textContent =
                    msg.count === 1 ? '1 user' : `${msg.count} users`;
            }
        };

        ws.onclose = () => {
            term.write('\\r\\n\\x1b[31mDisconnected\\x1b[0m\\r\\n');
        };

        // Send input to server
        term.onData((data) => {
            ws.send(JSON.stringify({ type: 'input', data }));
        });

        // Handle resize
        window.addEventListener('resize', () => {
            fitAddon.fit();
            ws.send(JSON.stringify({
                type: 'resize',
                cols: term.cols,
                rows: term.rows
            }));
        });
    </script>
</body>
</html>
"""


@app.get("/")
async def get_index():
    return HTMLResponse(HTML_PAGE)


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()

    # Add to room
    if room_id not in rooms:
        rooms[room_id] = set()
    rooms[room_id].add(websocket)

    # Start PTY if not exists for this room
    if room_id not in pty_processes:
        master_fd, slave_fd = pty.openpty()
        pid = os.fork()

        if pid == 0:
            # Child process
            os.setsid()
            os.dup2(slave_fd, 0)
            os.dup2(slave_fd, 1)
            os.dup2(slave_fd, 2)
            os.close(master_fd)
            os.close(slave_fd)
            os.execvp("/bin/bash", ["/bin/bash"])
        else:
            # Parent process
            os.close(slave_fd)
            pty_processes[room_id] = {
                'master_fd': master_fd,
                'pid': pid
            }
            # Start reading from PTY in background
            asyncio.create_task(read_pty(room_id, master_fd))

    # Broadcast user count
    await broadcast_users(room_id)

    try:
        while True:
            data = await websocket.receive_text()
            msg = __import__('json').loads(data)

            if msg['type'] == 'input' and room_id in pty_processes:
                # Write to PTY
                os.write(pty_processes[room_id]['master_fd'], msg['data'].encode())

            elif msg['type'] == 'resize' and room_id in pty_processes:
                # Resize PTY
                winsize = struct.pack('HHHH', msg['rows'], msg['cols'], 0, 0)
                fcntl.ioctl(pty_processes[room_id]['master_fd'], termios.TIOCSWINSZ, winsize)

    except WebSocketDisconnect:
        pass
    finally:
        rooms[room_id].discard(websocket)
        await broadcast_users(room_id)

        # Clean up if no users left
        if not rooms[room_id]:
            del rooms[room_id]
            if room_id in pty_processes:
                try:
                    os.kill(pty_processes[room_id]['pid'], 9)
                    os.close(pty_processes[room_id]['master_fd'])
                except:
                    pass
                del pty_processes[room_id]


async def read_pty(room_id: str, master_fd: int):
    """Read from PTY and broadcast to all clients"""
    loop = asyncio.get_event_loop()

    while room_id in pty_processes:
        try:
            # Check if there's data to read
            r, _, _ = select.select([master_fd], [], [], 0.1)
            if r:
                data = os.read(master_fd, 4096)
                if data:
                    await broadcast_output(room_id, data.decode('utf-8', errors='replace'))
                else:
                    break
        except Exception as e:
            print(f"PTY read error: {e}")
            break

        await asyncio.sleep(0.01)


async def broadcast_output(room_id: str, data: str):
    """Broadcast PTY output to all clients in room"""
    if room_id not in rooms:
        return

    message = __import__('json').dumps({'type': 'output', 'data': data})
    disconnected = set()

    for ws in rooms[room_id]:
        try:
            await ws.send_text(message)
        except:
            disconnected.add(ws)

    rooms[room_id] -= disconnected


async def broadcast_users(room_id: str):
    """Broadcast user count to all clients"""
    if room_id not in rooms:
        return

    count = len(rooms[room_id])
    message = __import__('json').dumps({'type': 'users', 'count': count})

    for ws in rooms[room_id]:
        try:
            await ws.send_text(message)
        except:
            pass


if __name__ == "__main__":
    print("Starting Collaborative Terminal on port 8000...")
    print("Share this terminal with others using your preview URL!")
    uvicorn.run(app, host="0.0.0.0", port=8000)
