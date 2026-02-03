#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["fastapi", "uvicorn", "transformers", "torch", "accelerate"]
# ///
"""
Whisper Transcription API - audio to text.

Start the server:
    vmux run --provider modal --gpu T4 -dp 8000 python whisper_api.py

Transcribe audio:
    curl -X POST https://<preview-url>/transcribe -F "file=@audio.mp3"

Returns:
    {"text": "Hello world...", "chunks": [...]}

Environment:
    WHISPER_MODEL    Model to use (default: openai/whisper-large-v3-turbo)
"""

import os
import tempfile

MODEL = os.environ.get("WHISPER_MODEL", "openai/whisper-large-v3-turbo")


def create_app():
    from fastapi import FastAPI, File, UploadFile, Form
    from fastapi.responses import JSONResponse
    import torch
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

    app = FastAPI(title="Whisper API")

    print(f"[vmux:stage] loading")
    print(f"Loading {MODEL}...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        MODEL, torch_dtype=dtype, low_cpu_mem_usage=True
    )
    model.to(device)
    processor = AutoProcessor.from_pretrained(MODEL)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=dtype,
        device=device,
    )
    print(f"[vmux:stage:done] loading")

    @app.get("/")
    def index():
        return {"model": MODEL, "device": device}

    @app.post("/transcribe")
    async def transcribe(
        file: UploadFile = File(...),
        language: str | None = Form(None),
    ):
        suffix = os.path.splitext(file.filename or "")[1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            kwargs = {"language": language} if language else {}
            result = pipe(
                tmp_path,
                chunk_length_s=30,
                batch_size=16,
                return_timestamps=True,
                generate_kwargs=kwargs,
            )
            return JSONResponse({
                "text": result["text"],
                "chunks": result.get("chunks", []),
            })
        finally:
            os.unlink(tmp_path)

    return app


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(create_app(), host="0.0.0.0", port=port)
