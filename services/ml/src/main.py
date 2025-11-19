from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="ML Service", version="1.0.0")

class EmbeddingRequest(BaseModel):
    texts: List[str]

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model: str

@app.get("/health")
def health():
    return {"status": "healthy", "service": "ml"}

@app.post("/embeddings", response_model=EmbeddingResponse)
def generate_embeddings(request: EmbeddingRequest):
    # TODO: Implement embedding generation
    return EmbeddingResponse(
        embeddings=[[0.0] * 384 for _ in request.texts],
        model="all-MiniLM-L6-v2"
    )

@app.get("/models")
def list_models():
    return {
        "models": [
            {"name": "all-MiniLM-L6-v2", "type": "embedding", "status": "ready"},
            {"name": "gpt-4", "type": "llm", "status": "ready"}
        ]
    }
