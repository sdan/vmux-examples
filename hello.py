#!/usr/bin/env python3
"""
Hello World - verify vmux is working.

    vmux run python hello.py
    vmux run --provider modal python hello.py
"""

import os
import time

print("vmux hello world")
print(f"  cwd: {os.getcwd()}")
print(f"  provider: {os.environ.get('VMUX_PROVIDER', 'cloudflare')}")
print()

for i in range(3):
    print(f"  tick {i+1}/3")
    time.sleep(1)

print("\ndone")
