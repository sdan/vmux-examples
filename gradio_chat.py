#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["gradio", "openai"]
# ///
"""
Gradio Chat UI - beautiful chat interface for any OpenAI-compatible API.

Start vLLM first:
    vmux run --provider modal --gpu A10G -dp 8080 python vllm_server.py

Then run this UI pointing to it:
    vmux run -dp 7860 -e OPENAI_BASE_URL=https://<vllm-url>/v1 python gradio_chat.py

Or use any OpenAI-compatible API:
    vmux run -dp 7860 -e OPENAI_API_KEY=sk-xxx python gradio_chat.py
"""

import os

import gradio as gr
from openai import OpenAI

BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "vmux")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


def chat(message: str, history: list) -> str:
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    for h in history:
        messages.append({"role": "user", "content": h[0]})
        if h[1]:
            messages.append({"role": "assistant", "content": h[1]})
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content


demo = gr.ChatInterface(
    chat,
    title="vmux Chat",
    description=f"Model: {MODEL} | API: {BASE_URL}",
    examples=["Hello!", "Write a haiku about coding", "Explain quantum computing"],
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    print(f"[vmux:ready] http://0.0.0.0:{port}")
    demo.launch(server_name="0.0.0.0", server_port=port)
