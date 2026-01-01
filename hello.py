#!/usr/bin/env python3
"""Simple test script for vmux."""

import os
import time

print("🚀 Hello from vmux!")
print(f"   Working dir: {os.getcwd()}")
print(f"   Files here: {os.listdir('.')}")
print()

for i in range(5):
    print(f"   Count: {i+1}/5")
    time.sleep(1)

print()
print("✅ Done!")
