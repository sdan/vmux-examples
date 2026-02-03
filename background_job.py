#!/usr/bin/env python3
"""
Background Job - long-running task with progress.

    vmux run -d python background_job.py

Runs detached. Check progress with:
    vmux logs -f <job_id>
"""

import time

TOTAL_STEPS = 100

print(f"Starting background job with {TOTAL_STEPS} steps")
print()

for i in range(TOTAL_STEPS):
    progress = (i + 1) / TOTAL_STEPS * 100
    bar = "=" * int(progress / 2) + ">" + " " * (50 - int(progress / 2))
    print(f"\r[{bar}] {progress:.0f}%", end="", flush=True)
    time.sleep(0.5)

print("\n\nJob complete!")
