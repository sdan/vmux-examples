#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["fastapi", "uvicorn", "sentence-transformers", "torch"]
# ///
"""
Embeddings API - text to vectors for RAG and semantic search.

Start the server:
    vmux run --provider modal --gpu T4 -dp 8000 python embeddings_api.py

Generate embeddings:
    curl -X POST https://<preview-url>/embed \
      -H "Content-Type: application/json" \
      -d '{"texts": ["Hello world", "How are you?"]}'

Returns:
    {"embeddings": [[0.1, ...], [0.3, ...]], "dim": 1024}

Environment:
    EMBED_MODEL    Model to use (default: Alibaba-NLP/gte-Qwen2-1.5B-instruct)
"""

import os

MODEL = os.environ.get("EMBED_MODEL", "Alibaba-NLP/gte-Qwen2-1.5B-instruct")


def create_app():
    from fastapi import FastAPI
    from pydantic import BaseModel
    import torch
    from sentence_transformers import SentenceTransformer

    app = FastAPI(title="Embeddings API")

    print(f"[vmux:stage] loading")
    print(f"Loading {MODEL}...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(MODEL, device=device, trust_remote_code=True)
    dim = model.get_sentence_embedding_dimension()
    print(f"[vmux:stage:done] loading")

    class EmbedRequest(BaseModel):
        texts: list[str]
        normalize: bool = True

    @app.get("/")
    def index():
        return {"model": MODEL, "device": device, "dim": dim}

    @app.post("/embed")
    def embed(req: EmbedRequest):
        embeddings = model.encode(
            req.texts,
            normalize_embeddings=req.normalize,
            convert_to_numpy=True,
        )
        return {"embeddings": embeddings.tolist(), "dim": dim}

    @app.post("/similarity")
    def similarity(req: EmbedRequest):
        """Compute pairwise cosine similarity."""
        import numpy as np

        if len(req.texts) < 2:
            return {"error": "need at least 2 texts"}

        embeddings = model.encode(req.texts, normalize_embeddings=True)
        sim = np.dot(embeddings, embeddings.T)
        return {"texts": req.texts, "similarity": sim.tolist()}

    return app


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(create_app(), host="0.0.0.0", port=port)
