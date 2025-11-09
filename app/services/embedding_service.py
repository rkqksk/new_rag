"""
Embedding Service
Generates embeddings using Ollama
"""

from typing import List, Optional

import httpx


async def generate_embedding(
    text: str, ollama_url: str = "http://localhost:11434"
) -> Optional[List[float]]:
    """Generate embedding vector for text using Ollama

    Args:
        text: Text to embed
        ollama_url: Ollama API URL

    Returns:
        Embedding vector or None if failed
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ollama_url}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("embedding")
    except Exception as e:
        print(f"Embedding generation error: {e}")

    return None
