import torch
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Centralized embedding service with multiple model support
    """

    AVAILABLE_MODELS = {
        "all-MiniLM-L6-v2": {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "dim": 384,
            "description": "Lightweight, fast model for general-purpose embeddings",
        },
        "all-mpnet-base-v2": {
            "model_name": "sentence-transformers/all-mpnet-base-v2",
            "dim": 768,
            "description": "High-performance model with good semantic understanding",
        },
    }

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding model

        Args:
            model_name: Name of the embedding model to use
        """
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(f"Unsupported model: {model_name}")

        model_info = self.AVAILABLE_MODELS[model_name]
        self.model = SentenceTransformer(model_info["model_name"])
        self.model_name = model_name
        self.embedding_dim = model_info["dim"]

        # Move to GPU if available
        if torch.cuda.is_available():
            self.model = self.model.to("cuda")

    def embed_documents(self, documents: list) -> torch.Tensor:
        """
        Generate embeddings for a list of documents

        Args:
            documents: List of text documents to embed

        Returns:
            Tensor of document embeddings
        """
        return self.model.encode(documents, convert_to_tensor=True)

    def embed_query(self, query: str) -> torch.Tensor:
        """
        Generate embedding for a single query

        Args:
            query: Text query to embed

        Returns:
            Embedding tensor
        """
        return self.model.encode(query, convert_to_tensor=True)

    @classmethod
    def list_available_models(cls):
        """
        List all available embedding models

        Returns:
            Dictionary of available models with their details
        """
        return cls.AVAILABLE_MODELS
