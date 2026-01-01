#!/usr/bin/env python3
# /// script
# dependencies = ["fastapi", "uvicorn", "websockets"]
# ///
"""
🐰 Burrow - Real-time Data Processing Demo for vmux
====================================================

A production-style Python webserver showcasing vmux's preview URL feature.
Watch rabbits hop across your data pipeline in real-time!

Demonstrates:
• WebSocket connection pooling & broadcasting
• Server-Sent Events (SSE) streaming
• Async background tasks with graceful shutdown
• Health checks & metrics endpoints
• Ring buffers for historical data

Run with vmux:
    vmux run --preview python burrow.py

Then open your preview URL (e.g., https://abc123xyz.purr.ge) to see:
• Real-time carrot stock ticker (rabbit commodities market)
• Live server metrics dashboard
• WebSocket message broadcasting
• Animated pixel rabbits!
"""

import asyncio
import json
import random
import time
import os
import signal
import sys
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Set, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import uvicorn


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class CarrotStock:
    """Rabbit commodities market ticker."""
    symbol: str
    name: str
    price: float
    emoji: str
    change: float = 0.0
    volume: int = 0

    def hop(self) -> "CarrotStock":
        """Simulate a price hop (rabbits don't just move, they hop!)."""
        # Rabbits are unpredictable - sometimes big hops!
        if random.random() < 0.1:  # 10% chance of big hop
            movement = random.gauss(0, self.price * 0.01)  # 1% volatility
        else:
            movement = random.gauss(0, self.price * 0.002)  # 0.2% normal

        self.change = movement
        self.price = max(0.01, self.price + movement)
        self.volume += random.randint(100, 1000)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "emoji": self.emoji,
            "price": round(self.price, 2),
            "change": round(self.change, 4),
            "change_pct": round((self.change / (self.price - self.change)) * 100, 2) if self.price != self.change else 0,
            "volume": self.volume,
        }


@dataclass
class BurrowMetrics:
    """Warren (server) metrics collector."""
    start_time: float = field(default_factory=time.time)
    requests: int = 0
    rabbits_connected: int = 0  # ws connections
    hops_broadcast: int = 0     # messages sent
    carrots_processed: int = 0  # data points

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uptime_seconds": round(self.uptime_seconds, 2),
            "uptime_human": self._format_uptime(),
            "requests": self.requests,
            "rabbits_connected": self.rabbits_connected,
            "hops_broadcast": self.hops_broadcast,
            "carrots_processed": self.carrots_processed,
            "memory_mb": self._get_memory_mb(),
        }

    def _format_uptime(self) -> str:
        secs = int(self.uptime_seconds)
        hours, remainder = divmod(secs, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"

    def _get_memory_mb(self) -> float:
        try:
            import resource
            return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024, 2)
        except:
            return 0.0


# ============================================================================
# Global State (The Warren)
# ============================================================================

# WebSocket connection pool (rabbits in the warren)
warren: Set[WebSocket] = set()

# Rabbit commodities market
MARKET = {
    "CRRT": CarrotStock("CRRT", "Organic Carrots", 142.50, "🥕"),
    "LTUC": CarrotStock("LTUC", "Luxury Lettuce", 88.25, "🥬"),
    "HAYX": CarrotStock("HAYX", "Premium Hay", 56.00, "🌾"),
    "KLVR": CarrotStock("KLVR", "Wild Clover", 73.80, "🍀"),
    "THYM": CarrotStock("THYM", "Garden Thyme", 195.40, "🌿"),
}

# Metrics
metrics = BurrowMetrics()

# Recent data buffer (rabbit memory - they remember the last 100 hops)
hop_history: deque = deque(maxlen=100)

# Shutdown event
burrow_closing = asyncio.Event()


# ============================================================================
# Background Tasks (Night Watch Rabbits)
# ============================================================================

async def market_hopper():
    """Simulate the rabbit commodities market and broadcast to warren."""
    while not burrow_closing.is_set():
        # All stocks take a hop
        updates = []
        for stock in MARKET.values():
            stock.hop()
            updates.append(stock.to_dict())
            metrics.carrots_processed += 1

        # Store in history
        hop_history.append({
            "timestamp": datetime.now().isoformat(),
            "stocks": updates,
        })

        # Broadcast to all rabbits in the warren
        if warren:
            message = json.dumps({
                "type": "market_hop",
                "data": updates,
                "timestamp": datetime.now().isoformat(),
            })

            disconnected = set()
            for rabbit in warren:
                try:
                    await rabbit.send_text(message)
                    metrics.hops_broadcast += 1
                except:
                    disconnected.add(rabbit)

            warren.difference_update(disconnected)

        await asyncio.sleep(0.5)  # 2 hops per second


async def warren_watcher():
    """Periodically log warren status to console."""
    rabbit_states = ["🐰", "🐇", "🐾"]
    idx = 0
    while not burrow_closing.is_set():
        m = metrics.to_dict()
        state = rabbit_states[idx % len(rabbit_states)]
        print(f"{state} Warren | uptime={m['uptime_human']} rabbits={m['rabbits_connected']} "
              f"hops={m['hops_broadcast']} carrots={m['carrots_processed']}")
        idx += 1
        await asyncio.sleep(10)


# ============================================================================
# Lifespan Management (Opening/Closing the Burrow)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the burrow lifecycle with graceful shutdown."""
    print("🐰 Burrow opening...")
    print(f"   Port: 8000")
    print(f"   Preview URL: Your vmux preview URL will proxy here!")

    # Start the night watch
    tasks = [
        asyncio.create_task(market_hopper()),
        asyncio.create_task(warren_watcher()),
    ]

    yield

    # Time to close the burrow
    print("\n🌙 Burrow closing for the night...")
    burrow_closing.set()

    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    # Send all rabbits home
    for rabbit in list(warren):
        try:
            await rabbit.close()
        except:
            pass

    print("💤 All rabbits tucked in. Goodnight!")


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Burrow",
    description="🐰 Real-time rabbit data processing for vmux",
    lifespan=lifespan,
)


# ============================================================================
# The Burrow Dashboard (HTML)
# ============================================================================

BURROW_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🐰 Burrow | vmux demo</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f1115;
            --bg-secondary: #1a1d23;
            --border: #2a2f3a;
            --text: #c9ccd1;
            --text-muted: #6b7280;
            --text-bright: #e5e7eb;
            --accent: #f59e0b;
            --green: #10b981;
            --red: #ef4444;
            --bunny-white: #f5f5f4;
            --bunny-pink: #fecaca;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'JetBrains Mono', monospace;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.6;
        }

        .container { max-width: 900px; margin: 0 auto; padding: 24px; }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 32px;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 18px;
            color: var(--text-bright);
        }

        .logo svg { width: 28px; height: 28px; }

        .status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: var(--text-muted);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--green);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }

        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            padding: 20px;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            font-size: 12px;
            color: var(--text-muted);
        }

        .stock-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--border);
        }

        .stock-row:last-child { border-bottom: none; }

        .stock-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .stock-emoji { font-size: 18px; }

        .stock-symbol {
            font-weight: 600;
            font-size: 14px;
            color: var(--text-bright);
        }

        .stock-name {
            font-size: 11px;
            color: var(--text-muted);
        }

        .stock-price {
            text-align: right;
        }

        .stock-value {
            font-size: 16px;
            font-weight: 500;
            color: var(--text-bright);
        }

        .stock-change {
            font-size: 11px;
            padding: 2px 6px;
            margin-top: 4px;
            display: inline-block;
        }

        .stock-change.up {
            background: rgba(16, 185, 129, 0.15);
            color: var(--green);
        }

        .stock-change.down {
            background: rgba(239, 68, 68, 0.15);
            color: var(--red);
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }

        .metric {
            text-align: center;
            padding: 12px;
            background: var(--bg);
            border: 1px solid var(--border);
        }

        .metric-value {
            font-size: 24px;
            font-weight: 600;
            color: var(--accent);
        }

        .metric-label {
            font-size: 10px;
            color: var(--text-muted);
            margin-top: 4px;
        }

        .chart-container {
            height: 120px;
            display: flex;
            align-items: flex-end;
            gap: 2px;
            padding: 0 4px;
        }

        .chart-bar {
            flex: 1;
            background: var(--accent);
            min-height: 4px;
            transition: height 0.3s ease;
            opacity: 0.7;
        }

        .chart-bar:hover { opacity: 1; }

        .log-container {
            height: 150px;
            overflow-y: auto;
            font-size: 11px;
            background: var(--bg);
            border: 1px solid var(--border);
            padding: 12px;
        }

        .log-entry {
            margin-bottom: 4px;
            opacity: 0.8;
        }

        .log-time { color: var(--text-muted); }
        .log-msg { color: var(--accent); }

        /* Hopping rabbit animation */
        .rabbit-parade {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 40px;
            pointer-events: none;
            overflow: hidden;
        }

        .hopping-rabbit {
            position: absolute;
            bottom: 8px;
            font-size: 24px;
            animation: hop 0.4s ease-in-out infinite, moveRight 15s linear infinite;
        }

        @keyframes hop {
            0%, 100% { transform: translateY(0) scaleX(1); }
            50% { transform: translateY(-12px) scaleX(1.1); }
        }

        @keyframes moveRight {
            from { left: -40px; }
            to { left: 100%; }
        }

        footer {
            text-align: center;
            padding: 32px;
            color: var(--text-muted);
            font-size: 11px;
            border-top: 1px solid var(--border);
            margin-top: 32px;
        }

        footer a { color: var(--accent); text-decoration: none; }
        footer a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">
                <svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect width="16" height="16" fill="#0f1115"/>
                    <rect x="4" y="0" width="2" height="4" fill="#f5f5f4"/>
                    <rect x="5" y="2" width="1" height="2" fill="#fecaca"/>
                    <rect x="10" y="0" width="2" height="4" fill="#f5f5f4"/>
                    <rect x="10" y="2" width="1" height="2" fill="#fecaca"/>
                    <rect x="4" y="4" width="8" height="2" fill="#f5f5f4"/>
                    <rect x="3" y="6" width="10" height="4" fill="#f5f5f4"/>
                    <rect x="4" y="10" width="8" height="2" fill="#f5f5f4"/>
                    <rect x="5" y="12" width="6" height="1" fill="#f5f5f4"/>
                    <rect x="5" y="7" width="2" height="2" fill="#1f2937"/>
                    <rect x="9" y="7" width="2" height="2" fill="#1f2937"/>
                    <rect x="5" y="7" width="1" height="1" fill="#fff"/>
                    <rect x="9" y="7" width="1" height="1" fill="#fff"/>
                    <rect x="7" y="10" width="2" height="1" fill="#fca5a5"/>
                </svg>
                Burrow
            </div>
            <div class="status">
                <div class="status-dot"></div>
                <span id="connection-status">connected</span>
            </div>
        </header>

        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <span>🥕 rabbit commodities</span>
                    <span id="last-update">—</span>
                </div>
                <div id="stocks"></div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span>📊 warren metrics</span>
                    <span id="uptime">—</span>
                </div>
                <div class="metrics-grid">
                    <div class="metric">
                        <div class="metric-value" id="rabbits-connected">0</div>
                        <div class="metric-label">rabbits connected</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="hops-broadcast">0</div>
                        <div class="metric-label">hops broadcast</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="carrots-processed">0</div>
                        <div class="metric-label">carrots processed</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="memory-mb">0</div>
                        <div class="metric-label">memory (mb)</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <span>📈 CRRT price history</span>
                    <span>last 50 hops</span>
                </div>
                <div class="chart-container" id="price-chart"></div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span>🐾 hop log</span>
                    <span>websocket events</span>
                </div>
                <div class="log-container" id="hop-log"></div>
            </div>
        </div>

        <footer>
            powered by <a href="https://vmux.sdan.io">vmux</a> •
            preview url proxying to port 8000 •
            <a href="/api/health">health</a> •
            <a href="/api/metrics">metrics</a>
        </footer>
    </div>

    <div class="rabbit-parade">
        <div class="hopping-rabbit" style="animation-delay: 0s;">🐰</div>
        <div class="hopping-rabbit" style="animation-delay: 3s;">🐇</div>
        <div class="hopping-rabbit" style="animation-delay: 7s;">🐰</div>
        <div class="hopping-rabbit" style="animation-delay: 11s;">🐇</div>
    </div>

    <script>
        const priceHistory = [];
        const maxHistory = 50;
        let reconnectAttempts = 0;

        const stocksEl = document.getElementById('stocks');
        const lastUpdateEl = document.getElementById('last-update');
        const uptimeEl = document.getElementById('uptime');
        const rabbitsEl = document.getElementById('rabbits-connected');
        const hopsEl = document.getElementById('hops-broadcast');
        const carrotsEl = document.getElementById('carrots-processed');
        const memoryEl = document.getElementById('memory-mb');
        const chartEl = document.getElementById('price-chart');
        const logEl = document.getElementById('hop-log');
        const statusEl = document.getElementById('connection-status');
        const statusDot = document.querySelector('.status-dot');

        const fmt = (n) => n.toLocaleString();

        function connect() {
            const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
            const ws = new WebSocket(`${protocol}//${location.host}/ws`);

            ws.onopen = () => {
                statusEl.textContent = 'connected';
                statusDot.style.background = '#10b981';
                reconnectAttempts = 0;
                addLog('🐰 joined the warren');
            };

            ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);

                if (msg.type === 'market_hop') {
                    updateStocks(msg.data);
                    lastUpdateEl.textContent = new Date(msg.timestamp).toLocaleTimeString();
                } else if (msg.type === 'metrics') {
                    updateMetrics(msg.data);
                }
            };

            ws.onclose = () => {
                statusEl.textContent = 'reconnecting...';
                statusDot.style.background = '#f59e0b';
                addLog('🐾 hopped away, coming back...');

                reconnectAttempts++;
                const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
                setTimeout(connect, delay);
            };

            ws.onerror = () => addLog('⚠️ tunnel collapse');
        }

        function updateStocks(stocks) {
            stocksEl.innerHTML = stocks.map(s => `
                <div class="stock-row">
                    <div class="stock-info">
                        <span class="stock-emoji">${s.emoji}</span>
                        <div>
                            <div class="stock-symbol">${s.symbol}</div>
                            <div class="stock-name">${s.name}</div>
                        </div>
                    </div>
                    <div class="stock-price">
                        <div class="stock-value">$${s.price.toFixed(2)}</div>
                        <span class="stock-change ${s.change >= 0 ? 'up' : 'down'}">
                            ${s.change >= 0 ? '+' : ''}${s.change_pct.toFixed(2)}%
                        </span>
                    </div>
                </div>
            `).join('');

            // Track CRRT price for chart
            const crrt = stocks.find(s => s.symbol === 'CRRT');
            if (crrt) {
                priceHistory.push(crrt.price);
                if (priceHistory.length > maxHistory) priceHistory.shift();
                renderChart();
            }
        }

        function updateMetrics(m) {
            uptimeEl.textContent = m.uptime_human;
            rabbitsEl.textContent = fmt(m.rabbits_connected);
            hopsEl.textContent = fmt(m.hops_broadcast);
            carrotsEl.textContent = fmt(m.carrots_processed);
            memoryEl.textContent = m.memory_mb.toFixed(1);
        }

        function renderChart() {
            if (priceHistory.length < 2) return;

            const min = Math.min(...priceHistory);
            const max = Math.max(...priceHistory);
            const range = max - min || 1;

            chartEl.innerHTML = priceHistory.map((p, i) => {
                const height = ((p - min) / range) * 100 + 20;
                const opacity = 0.3 + (i / priceHistory.length) * 0.7;
                return `<div class="chart-bar" style="height: ${height}px; opacity: ${opacity}"></div>`;
            }).join('');
        }

        function addLog(msg) {
            const time = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerHTML = `<span class="log-time">[${time}]</span> <span class="log-msg">${msg}</span>`;
            logEl.appendChild(entry);
            logEl.scrollTop = logEl.scrollHeight;

            while (logEl.children.length > 50) {
                logEl.removeChild(logEl.firstChild);
            }
        }

        async function fetchMetrics() {
            try {
                const res = await fetch('/api/metrics');
                const data = await res.json();
                updateMetrics(data);
            } catch (e) {}
        }

        connect();
        setInterval(fetchMetrics, 2000);
    </script>
</body>
</html>
"""


# ============================================================================
# Routes
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the burrow dashboard."""
    metrics.requests += 1
    return BURROW_HTML


@app.get("/api/health")
async def health():
    """Health check for monitoring."""
    metrics.requests += 1
    return {
        "status": "🐰 hopping",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": metrics.uptime_seconds,
    }


@app.get("/api/metrics")
async def get_metrics():
    """Warren metrics endpoint."""
    metrics.requests += 1
    return metrics.to_dict()


@app.get("/api/market")
async def get_market():
    """Current market data."""
    metrics.requests += 1
    return {
        "stocks": [s.to_dict() for s in MARKET.values()],
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/stream")
async def stream_events(request: Request):
    """SSE stream of market hops."""
    metrics.requests += 1

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break

            data = {
                "stocks": [s.to_dict() for s in MARKET.values()],
                "metrics": metrics.to_dict(),
                "timestamp": datetime.now().isoformat(),
            }

            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time warren updates."""
    await websocket.accept()
    warren.add(websocket)
    metrics.rabbits_connected = len(warren)

    print(f"🐰 New rabbit joined the warren (total: {len(warren)})")

    try:
        # Send welcome metrics
        await websocket.send_text(json.dumps({
            "type": "metrics",
            "data": metrics.to_dict(),
        }))

        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({
                    "type": "metrics",
                    "data": metrics.to_dict(),
                }))

    except WebSocketDisconnect:
        pass
    finally:
        warren.discard(websocket)
        metrics.rabbits_connected = len(warren)
        print(f"🐾 Rabbit left the warren (total: {len(warren)})")


# ============================================================================
# Entry Point
# ============================================================================

def handle_signal(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n🌙 Received signal {signum}, closing burrow...")
    burrow_closing.set()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    print(r"""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   🐰 Burrow - Real-time Data Processing Demo                 ║
    ║                                                               ║
    ║   Production patterns demonstrated:                          ║
    ║   • WebSocket connection pooling (the warren)                ║
    ║   • Server-Sent Events streaming                             ║
    ║   • Async background tasks with graceful shutdown            ║
    ║   • Health checks & metrics endpoints                        ║
    ║   • Ring buffer for historical data (rabbit memory)          ║
    ║                                                               ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║                                                               ║
    ║   🌐 HTTP:  http://0.0.0.0:8000                              ║
    ║   📡 WS:    ws://0.0.0.0:8000/ws                             ║
    ║   📊 API:   /api/health, /api/metrics, /api/market           ║
    ║   📺 SSE:   /api/stream                                      ║
    ║                                                               ║
    ║   Run with: vmux run --preview python burrow.py              ║
    ║   Your *.purr.ge URL will proxy to port 8000!                ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
    )
