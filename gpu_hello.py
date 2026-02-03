#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["torch"]
# ///
"""
GPU Hello World - verify CUDA is working on Modal.

    vmux run --provider modal --gpu T4 python gpu_hello.py
    vmux run --provider modal --gpu A10G python gpu_hello.py
"""

import subprocess
import sys


def main():
    # Check nvidia-smi
    result = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True)
    if result.returncode != 0:
        print("no GPU detected")
        print("use: vmux run --provider modal --gpu T4 python gpu_hello.py")
        return

    print(result.stdout.strip())
    print()

    # PyTorch check
    import torch

    if not torch.cuda.is_available():
        print("CUDA not available in PyTorch")
        return

    device = torch.device("cuda")
    name = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9

    print(f"PyTorch: {torch.__version__}")
    print(f"Device:  {name}")
    print(f"VRAM:    {vram:.1f} GB")
    print()

    # Quick benchmark
    import time

    size = 4096
    a = torch.randn(size, size, device=device)
    b = torch.randn(size, size, device=device)

    # Warmup
    torch.cuda.synchronize()
    _ = torch.mm(a, b)
    torch.cuda.synchronize()

    # Benchmark
    start = time.perf_counter()
    for _ in range(10):
        torch.mm(a, b)
    torch.cuda.synchronize()
    elapsed = (time.perf_counter() - start) / 10

    tflops = 2 * size**3 / elapsed / 1e12
    print(f"Benchmark: {size}x{size} matmul = {tflops:.1f} TFLOPS")


if __name__ == "__main__":
    main()
