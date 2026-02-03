#!/usr/bin/env python3
"""
Ollama Chat - run Llama locally on Modal GPU.

    vmux run --provider modal --gpu T4 python ollama_chat.py
    vmux run --provider modal --gpu A10G python ollama_chat.py  # faster

No API keys required - Ollama runs models locally.
"""

import json
import subprocess
import sys
import time
import urllib.request

MODEL = "llama3.2:3b"  # ~2GB download


def install_ollama():
    """Install Ollama binary."""
    if subprocess.run(["which", "ollama"], capture_output=True).returncode == 0:
        return

    print("Installing Ollama...")
    try:
        # Official install script (best effort in container)
        subprocess.run(
            ["bash", "-lc", "curl -fsSL https://ollama.com/install.sh | sh"],
            check=True,
        )
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "Failed to install Ollama. If this keeps happening, try a newer base image "
            "or pre-bake Ollama into a custom image."
        )


def start_server():
    """Start Ollama server and wait for it."""
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        try:
            urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def pull_model():
    """Download the model."""
    print(f"Pulling {MODEL}...")
    subprocess.run(["ollama", "pull", MODEL], check=True)


def chat(prompt: str) -> str:
    """Send a prompt and get response."""
    data = json.dumps({"model": MODEL, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read()).get("response", "").strip()


def main():
    # Check GPU
    result = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True)
    if result.returncode != 0:
        print("No GPU detected. Use: vmux run --provider modal --gpu T4 python ollama_chat.py")
        return
    print(f"GPU: {result.stdout.strip()}")

    install_ollama()
    if not start_server():
        print("Failed to start Ollama server")
        sys.exit(1)
    pull_model()

    # Interactive chat
    print(f"\nChat with {MODEL} (type 'quit' to exit)\n")
    while True:
        try:
            user = input("You: ").strip()
            if user.lower() in ("quit", "exit", "q") or not user:
                break
            print(f"AI: {chat(user)}\n")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    main()
