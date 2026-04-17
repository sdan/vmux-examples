"""Qwen3-Reranker-0.6B — text reranking API via vmux.

Run:
  vmux run --provider modal --gpu T4 -dp 8000 python qwen_reranker.py

Query:
  curl -X POST https://<preview-url>/rerank \
    -H "Content-Type: application/json" \
    -d '{"query": "What is deep learning?", "documents": ["Deep learning is...", "Cats are cute"]}'
"""

# /// script
# dependencies = ["fastapi[standard]", "torch", "transformers>=4.51.0", "accelerate"]
# ///

import os
import torch
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "Qwen/Qwen3-Reranker-0.6B"
MAX_LENGTH = 8192

print("[vmux:stage] loading model")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, padding_side="left")
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=torch.float16)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device).eval()

# Token IDs for scoring
yes_token_id = tokenizer.convert_tokens_to_ids("yes")
no_token_id = tokenizer.convert_tokens_to_ids("no")

print("[vmux:stage:done] loading model")


def get_relevance_score(query: str, document: str, task: str = "Given a web search query, retrieve relevant passages that answer the query.") -> float:
    """Score how relevant a document is to a query (0-1)."""
    prefix = f"Instruct: {task}\n"
    prompt = f"{prefix}Query: {query}\nDocument: {document}\nRelevant:"

    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    # Append "yes" so the model scores it
    text += "yes"

    inputs = tokenizer(text, return_tensors="pt", max_length=MAX_LENGTH, truncation=True).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        # Position -2: logits predicting the "yes" token (last real decision point)
        logits = outputs.logits[:, -2, :]
        yes_no_logits = logits[:, [yes_token_id, no_token_id]]
        probs = torch.nn.functional.softmax(yes_no_logits, dim=-1)
        relevance = probs[:, 0].item()  # P("yes")

    return relevance


# --- FastAPI app ---

app = FastAPI(title="Qwen3-Reranker-0.6B")


class RerankRequest(BaseModel):
    query: str
    documents: list[str]
    task: str = "Given a web search query, retrieve relevant passages that answer the query."
    top_k: int | None = None


class ScoredDocument(BaseModel):
    index: int
    score: float
    document: str


class RerankResponse(BaseModel):
    results: list[ScoredDocument]


@app.post("/rerank", response_model=RerankResponse)
def rerank(req: RerankRequest):
    scored = []
    for i, doc in enumerate(req.documents):
        score = get_relevance_score(req.query, doc, req.task)
        scored.append(ScoredDocument(index=i, score=score, document=doc))

    scored.sort(key=lambda x: x.score, reverse=True)

    if req.top_k:
        scored = scored[: req.top_k]

    return RerankResponse(results=scored)


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME, "device": device}


port = int(os.environ.get("PORT", 8000))
print(f"[vmux:ready] http://0.0.0.0:{port}")
uvicorn.run(app, host="0.0.0.0", port=port)
