#!/usr/bin/env python3
"""Holiday tree - run me in the cloud! 🎄"""

import time
import random

def main():
    # Build the tree
    tree_height = 12

    print("\n" + " " * tree_height + "⭐")
    time.sleep(0.3)

    for i in range(tree_height):
        spaces = " " * (tree_height - i - 1)
        width = 2 * i + 1

        # Add some ornaments randomly
        row = ""
        for j in range(width):
            if random.random() < 0.15:
                row += random.choice(["🔴", "🔵", "🟡", "⚪"])
            else:
                row += "🌲"

        print(spaces + row)
        time.sleep(0.2)

    # Tree trunk
    trunk_width = 3
    trunk_spaces = " " * (tree_height - trunk_width // 2 - 1)
    print(trunk_spaces + "🪵" * trunk_width)
    print(trunk_spaces + "🪵" * trunk_width)

    # Presents
    time.sleep(0.5)
    print()
    present_spaces = " " * (tree_height - 5)
    print(present_spaces + "🎁 🎀 🎁 🎀 🎁 🎀 🎁")

    print()
    print(" " * (tree_height - 8) + "✨ Happy Holidays from vmux! ✨")
    print(" " * (tree_height - 10) + "Running in Cloudflare Containers 🚀")
    print()

if __name__ == "__main__":
    main()
