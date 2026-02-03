#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["fastapi", "uvicorn", "diffusers", "torch", "accelerate", "transformers"]
# ///
"""
Image Generation API - SDXL Turbo text-to-image.

Start the server:
    vmux run --provider modal --gpu A10G -dp 8000 python image_gen.py

Generate an image:
    curl "https://<preview-url>/generate?prompt=a+cat+astronaut" -o cat.png

Environment:
    SD_MODEL    Model to use (default: stabilityai/sdxl-turbo)
"""

import io
import os

MODEL = os.environ.get("SD_MODEL", "stabilityai/sdxl-turbo")


def create_app():
    from fastapi import FastAPI, Query
    from fastapi.responses import Response
    import torch
    from diffusers import AutoPipelineForText2Image

    app = FastAPI(title="Image Generation API")

    print(f"[vmux:stage] loading")
    print(f"Loading {MODEL}...")
    pipe = AutoPipelineForText2Image.from_pretrained(
        MODEL, torch_dtype=torch.float16, variant="fp16"
    )
    pipe.to("cuda")
    print(f"[vmux:stage:done] loading")

    @app.get("/")
    def index():
        return {"model": MODEL, "usage": "GET /generate?prompt=your+prompt"}

    @app.get("/generate")
    def generate(
        prompt: str = Query(...),
        steps: int = Query(4),  # SDXL Turbo only needs 4 steps
        seed: int | None = Query(None),
    ):
        generator = None
        if seed is not None:
            generator = torch.Generator("cuda").manual_seed(seed)

        image = pipe(
            prompt=prompt,
            num_inference_steps=steps,
            guidance_scale=0.0,  # Turbo doesn't use guidance
            generator=generator,
        ).images[0]

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)
        return Response(content=buf.read(), media_type="image/png")

    return app


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(create_app(), host="0.0.0.0", port=port)
