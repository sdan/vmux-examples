#!/usr/bin/env python3
"""Counts for 2 hours, printing the current epoch timestamp each second."""

import time

DURATION_SECONDS = 2 * 60 * 60  # 2 hours

def main():
    start = time.time()
    end = start + DURATION_SECONDS

    while time.time() < end:
        print(int(time.time()))
        time.sleep(1)

if __name__ == "__main__":
    main()
