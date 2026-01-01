#!/usr/bin/env python3
# /// script
# dependencies = ["aiohttp"]
# ///
"""
NetProbe - Network Analytics Tool
Inspired by Tailscale DERP, measures network performance between endpoints.

Features:
- Latency measurement (ping-style RTT)
- Bandwidth estimation (download/upload speed)
- Jitter analysis
- Packet loss detection
- Connection quality scoring
- Multi-endpoint comparison
"""

import asyncio
import aiohttp
import time
import statistics
import socket
import struct
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum


class ConnectionQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class ProbeResult:
    """Result from a single probe."""
    endpoint: str
    timestamp: datetime
    latency_ms: float
    success: bool
    error: Optional[str] = None


@dataclass
class EndpointStats:
    """Aggregated statistics for an endpoint."""
    endpoint: str
    samples: int = 0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0
    avg_latency_ms: float = 0
    jitter_ms: float = 0
    packet_loss_pct: float = 0
    download_mbps: Optional[float] = None
    upload_mbps: Optional[float] = None
    quality: ConnectionQuality = ConnectionQuality.POOR
    latencies: list = field(default_factory=list)

    def update(self, result: ProbeResult):
        """Update stats with new probe result."""
        if result.success:
            self.latencies.append(result.latency_ms)
            self.min_latency_ms = min(self.min_latency_ms, result.latency_ms)
            self.max_latency_ms = max(self.max_latency_ms, result.latency_ms)
            self.avg_latency_ms = statistics.mean(self.latencies)
            if len(self.latencies) > 1:
                self.jitter_ms = statistics.stdev(self.latencies)

        self.samples += 1
        failed = self.samples - len(self.latencies)
        self.packet_loss_pct = (failed / self.samples) * 100
        self._calculate_quality()

    def _calculate_quality(self):
        """Calculate connection quality score."""
        if self.packet_loss_pct > 10:
            self.quality = ConnectionQuality.CRITICAL
        elif self.packet_loss_pct > 5 or self.avg_latency_ms > 200:
            self.quality = ConnectionQuality.POOR
        elif self.avg_latency_ms > 100 or self.jitter_ms > 30:
            self.quality = ConnectionQuality.FAIR
        elif self.avg_latency_ms > 50 or self.jitter_ms > 15:
            self.quality = ConnectionQuality.GOOD
        else:
            self.quality = ConnectionQuality.EXCELLENT


# DERP-like relay servers (using public endpoints for testing)
DERP_ENDPOINTS = {
    "cloudflare": "https://1.1.1.1/cdn-cgi/trace",
    "google": "https://www.google.com/generate_204",
    "aws-us-east": "https://dynamodb.us-east-1.amazonaws.com/ping",
    "aws-us-west": "https://dynamodb.us-west-2.amazonaws.com/ping",
    "azure": "https://azure.microsoft.com/favicon.ico",
    "fastly": "https://www.fastly.com/favicon.ico",
}

# Speed test endpoints
SPEED_TEST_ENDPOINTS = {
    "cloudflare-100mb": "https://speed.cloudflare.com/__down?bytes=104857600",
    "cloudflare-10mb": "https://speed.cloudflare.com/__down?bytes=10485760",
    "cloudflare-1mb": "https://speed.cloudflare.com/__down?bytes=1048576",
}


class NetProbe:
    """Network probe and analytics engine."""

    def __init__(self, duration_hours: float = 2.0, probe_interval: float = 1.0):
        self.duration_seconds = duration_hours * 3600
        self.probe_interval = probe_interval
        self.stats: dict[str, EndpointStats] = {}
        self.start_time: Optional[datetime] = None
        self.probes_sent = 0
        self.running = False

    async def probe_endpoint(self, session: aiohttp.ClientSession,
                            name: str, url: str) -> ProbeResult:
        """Send a single probe to an endpoint."""
        start = time.perf_counter()
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                await resp.read()
                latency_ms = (time.perf_counter() - start) * 1000
                return ProbeResult(
                    endpoint=name,
                    timestamp=datetime.now(),
                    latency_ms=latency_ms,
                    success=True
                )
        except Exception as e:
            return ProbeResult(
                endpoint=name,
                timestamp=datetime.now(),
                latency_ms=0,
                success=False,
                error=str(e)[:50]
            )

    async def measure_download_speed(self, session: aiohttp.ClientSession,
                                     size_bytes: int = 10_485_760) -> float:
        """Measure download speed in Mbps."""
        url = f"https://speed.cloudflare.com/__down?bytes={size_bytes}"
        start = time.perf_counter()
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                await resp.read()
                elapsed = time.perf_counter() - start
                mbps = (size_bytes * 8 / 1_000_000) / elapsed
                return mbps
        except Exception:
            return 0.0

    async def measure_upload_speed(self, session: aiohttp.ClientSession,
                                   size_bytes: int = 1_048_576) -> float:
        """Measure upload speed in Mbps (simulated with POST)."""
        url = "https://speed.cloudflare.com/__up"
        data = b'0' * size_bytes
        start = time.perf_counter()
        try:
            async with session.post(url, data=data,
                                   timeout=aiohttp.ClientTimeout(total=30)) as resp:
                await resp.read()
                elapsed = time.perf_counter() - start
                mbps = (size_bytes * 8 / 1_000_000) / elapsed
                return mbps
        except Exception:
            return 0.0

    def format_quality_indicator(self, quality: ConnectionQuality) -> str:
        """Format quality with color indicator."""
        indicators = {
            ConnectionQuality.EXCELLENT: "●",  # Green
            ConnectionQuality.GOOD: "●",       # Light green
            ConnectionQuality.FAIR: "●",       # Yellow
            ConnectionQuality.POOR: "●",       # Orange
            ConnectionQuality.CRITICAL: "●",   # Red
        }
        return f"{indicators[quality]} {quality.value}"

    def format_stats_table(self) -> str:
        """Format statistics as a table."""
        lines = []
        lines.append("=" * 90)
        lines.append(f"{'Endpoint':<15} {'RTT (ms)':<12} {'Min/Max':<15} "
                    f"{'Jitter':<10} {'Loss %':<8} {'Quality':<12}")
        lines.append("-" * 90)

        for name, stats in sorted(self.stats.items()):
            if stats.samples > 0:
                rtt = f"{stats.avg_latency_ms:.1f}" if stats.latencies else "N/A"
                minmax = f"{stats.min_latency_ms:.0f}/{stats.max_latency_ms:.0f}" if stats.latencies else "N/A"
                jitter = f"{stats.jitter_ms:.1f}" if len(stats.latencies) > 1 else "N/A"
                loss = f"{stats.packet_loss_pct:.1f}%"
                quality = self.format_quality_indicator(stats.quality)
                lines.append(f"{name:<15} {rtt:<12} {minmax:<15} "
                           f"{jitter:<10} {loss:<8} {quality:<12}")

        lines.append("=" * 90)
        return "\n".join(lines)

    def format_speed_results(self, download: float, upload: float) -> str:
        """Format speed test results."""
        lines = []
        lines.append("\n" + "=" * 50)
        lines.append("  SPEED TEST RESULTS")
        lines.append("=" * 50)
        lines.append(f"  ↓ Download: {download:.2f} Mbps")
        lines.append(f"  ↑ Upload:   {upload:.2f} Mbps")
        lines.append("=" * 50)
        return "\n".join(lines)

    async def run_speed_test(self, session: aiohttp.ClientSession):
        """Run a speed test."""
        print("\n[*] Running speed test (10MB download)...")
        download = await self.measure_download_speed(session, 10_485_760)

        print("[*] Running speed test (1MB upload)...")
        upload = await self.measure_upload_speed(session, 1_048_576)

        print(self.format_speed_results(download, upload))
        return download, upload

    async def probe_all_endpoints(self, session: aiohttp.ClientSession):
        """Probe all endpoints concurrently."""
        tasks = [
            self.probe_endpoint(session, name, url)
            for name, url in DERP_ENDPOINTS.items()
        ]
        results = await asyncio.gather(*tasks)

        for result in results:
            if result.endpoint not in self.stats:
                self.stats[result.endpoint] = EndpointStats(endpoint=result.endpoint)
            self.stats[result.endpoint].update(result)

        self.probes_sent += len(DERP_ENDPOINTS)

    async def run(self):
        """Main probe loop."""
        self.start_time = datetime.now()
        self.running = True
        end_time = self.start_time + timedelta(seconds=self.duration_seconds)

        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    NetProbe v1.0                             ║
║          Network Analytics & DERP-style Monitoring           ║
╠══════════════════════════════════════════════════════════════╣
║  Started:  {self.start_time.strftime('%Y-%m-%d %H:%M:%S'):<47} ║
║  Duration: {self.duration_seconds/3600:.1f} hours{' '*41}║
║  Targets:  {len(DERP_ENDPOINTS)} endpoints{' '*39}║
╚══════════════════════════════════════════════════════════════╝
""")

        connector = aiohttp.TCPConnector(limit=20, ttl_dns_cache=300)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Initial speed test
            await self.run_speed_test(session)

            print("\n[*] Starting continuous probe monitoring...")
            print("    Press Ctrl+C to stop and view final report\n")

            speed_test_interval = 300  # Every 5 minutes
            last_speed_test = time.time()

            try:
                while datetime.now() < end_time and self.running:
                    await self.probe_all_endpoints(session)

                    # Update display
                    elapsed = datetime.now() - self.start_time
                    remaining = end_time - datetime.now()

                    print(f"\033[2J\033[H")  # Clear screen
                    print(f"NetProbe | Elapsed: {str(elapsed).split('.')[0]} | "
                          f"Remaining: {str(remaining).split('.')[0]} | "
                          f"Probes: {self.probes_sent:,}")
                    print()
                    print(self.format_stats_table())

                    # Periodic speed test
                    if time.time() - last_speed_test > speed_test_interval:
                        await self.run_speed_test(session)
                        last_speed_test = time.time()

                    await asyncio.sleep(self.probe_interval)

            except KeyboardInterrupt:
                self.running = False

        # Final report
        self.print_final_report()

    def print_final_report(self):
        """Print comprehensive final report."""
        elapsed = datetime.now() - self.start_time

        print(f"""

╔══════════════════════════════════════════════════════════════╗
║                     FINAL REPORT                             ║
╠══════════════════════════════════════════════════════════════╣
║  Duration:     {str(elapsed).split('.')[0]:<44}║
║  Total Probes: {self.probes_sent:<44,}║
╚══════════════════════════════════════════════════════════════╝
""")
        print(self.format_stats_table())

        # Best endpoint recommendation
        best = min(
            [(n, s) for n, s in self.stats.items() if s.latencies],
            key=lambda x: x[1].avg_latency_ms,
            default=None
        )
        if best:
            print(f"\n[✓] Best endpoint: {best[0]} ({best[1].avg_latency_ms:.1f}ms avg)")

        # Quality summary
        quality_counts = {}
        for stats in self.stats.values():
            q = stats.quality.value
            quality_counts[q] = quality_counts.get(q, 0) + 1

        print("\nQuality Distribution:")
        for quality, count in sorted(quality_counts.items()):
            bar = "█" * count
            print(f"  {quality:<10}: {bar} ({count})")


async def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="NetProbe - Network Analytics Tool")
    parser.add_argument("-d", "--duration", type=float, default=2.0,
                       help="Duration in hours (default: 2)")
    parser.add_argument("-i", "--interval", type=float, default=1.0,
                       help="Probe interval in seconds (default: 1)")
    args = parser.parse_args()

    probe = NetProbe(duration_hours=args.duration, probe_interval=args.interval)
    await probe.run()


if __name__ == "__main__":
    asyncio.run(main())
