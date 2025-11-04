from typing import Any, Dict, List, Protocol, runtime_checkable, Optional
import httpx
import asyncio

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


@runtime_checkable
class DocumentLoader(Protocol):
    """Protocol for document loaders"""

    def load_documents(self, source_paths: List[str]) -> List[Any]: ...


@runtime_checkable
class TextSplitter(Protocol):
    """Protocol for text splitters"""

    def split_documents(self, documents: List[Any]) -> List[Any]: ...


@runtime_checkable
class EmbeddingModel(Protocol):
    """Protocol for embedding models"""

    def embed_query(self, text: str) -> List[float]: ...


class RAGPipeline:
    def __init__(
        self,
        loader: DocumentLoader,
        text_splitter: TextSplitter,
        embedding_model: EmbeddingModel,
        vector_db: QdrantClient,
        collection_name: str = "documents",
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "qwen2.5:7b-instruct",
    ):
        """
        Initialize RAG Pipeline with core components

        Args:
            loader: Document loading mechanism
            text_splitter: Text chunking strategy
            embedding_model: Embedding generation model
            vector_db: Vector database client
            collection_name: Qdrant collection name
            ollama_url: Ollama API endpoint
            ollama_model: Ollama model name
        """
        self.loader = loader
        self.text_splitter = text_splitter
        self.embedding_model = embedding_model
        self.vector_db = vector_db
        self.collection_name = collection_name
        self.ollama_url = ollama_url.rstrip("/")
        self.ollama_model = ollama_model
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Ensure the collection exists in Qdrant, create if not"""
        try:
            self.vector_db.get_collection(self.collection_name)
        except:
            # Collection doesn't exist, create it
            # Get embedding dimension from model
            embedding_dim = getattr(self.embedding_model, "embedding_dim", 384)
            self.vector_db.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
            )

    def ingest_documents(
        self, source_paths: List[str], additional_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Load, split, and index documents into vector database

        Args:
            source_paths: List of document file paths
            additional_metadata: Optional additional metadata to attach to all chunks

        Returns:
            Ingestion statistics
        """
        # Load documents
        documents = self.loader.load_documents(source_paths)

        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)

        # Generate embeddings
        embeddings = [self.embedding_model.embed_query(chunk.page_content) for chunk in chunks]

        # Prepare additional metadata
        extra_metadata = additional_metadata or {}

        # Index in Qdrant
        points = [
            PointStruct(
                id=abs(hash(chunk.page_content)),
                vector=embedding.tolist() if hasattr(embedding, "tolist") else embedding,
                payload={"text": chunk.page_content, "metadata": {**chunk.metadata, **extra_metadata}},
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

        self.vector_db.upsert(collection_name=self.collection_name, points=points)

        return {"total_documents": len(source_paths), "total_chunks": len(chunks)}

    def retrieve(
        self, query: str, top_k: int = 5, metadata_filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search on indexed documents

        Args:
            query: Search query
            top_k: Number of results to return
            metadata_filters: Optional metadata filters for search

        Returns:
            Top matching document chunks
        """
        query_embedding = self.embedding_model.embed_query(query)

        # Convert tensor to list if needed
        if hasattr(query_embedding, "tolist"):
            query_embedding = query_embedding.tolist()

        # Prepare search parameters
        search_params = {
            "collection_name": self.collection_name,
            "query_vector": query_embedding,
            "limit": top_k,
        }

        # Add metadata filters if provided
        if metadata_filters:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            conditions = [
                FieldCondition(key=f"metadata.{key}", match=MatchValue(value=value))
                for key, value in metadata_filters.items()
            ]
            search_params["query_filter"] = Filter(must=conditions)

        search_results = self.vector_db.search(**search_params)

        return [
            {
                "text": result.payload["text"],
                "metadata": result.payload["metadata"],
                "score": result.score,
            }
            for result in search_results
        ]

    def _call_ollama_sync(self, prompt: str) -> str:
        """Call Ollama API synchronously"""
        try:
            import requests
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2000,
                    },
                },
                timeout=120.0
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except Exception as e:
            # Fallback to simple summary if Ollama fails
            return f"[Ollama error: {str(e)}]"

    def generate_response(self, context_chunks: List[Dict[str, Any]], query: str) -> str:
        """
        Generate response based on retrieved context chunks using Ollama LLM

        Args:
            context_chunks: Retrieved context chunks
            query: User query

        Returns:
            Generated response text
        """
        # Build prompt based on context availability
        if not context_chunks:
            prompt = f"""You are a helpful assistant. Answer the following question based on your knowledge:

Question: {query}

Provide a clear, concise answer. If you don't know, say so honestly."""
        else:
            # Build context from chunks
            context_text = "\n\n".join([
                f"[Source {i+1}]: {chunk['text']}"
                for i, chunk in enumerate(context_chunks)
            ])

            prompt = f"""You are an expert assistant. Answer the question based ONLY on the provided context.

Context:
{context_text}

Question: {query}

Instructions:
- Answer based on the context provided
- Be specific and cite relevant information
- If the context doesn't contain enough information, say so
- Keep your answer clear and concise

Answer:"""

        # Call Ollama synchronously
        response = self._call_ollama_sync(prompt)
        return response

    def extract_citations(
        self, context_chunks: List[Dict[str, Any]], response: str
    ) -> Dict[str, Any]:
        """
        Extract citations from context chunks

        Args:
            context_chunks: Retrieved context chunks
            response: Generated response

        Returns:
            Citation information
        """
        citations = [
            {
                "source": chunk.get("metadata", {}).get("source", "Unknown"),
                "score": chunk.get("score", 0.0),
                "text_preview": chunk.get("text", "")[:100] + "..."
            }
            for chunk in context_chunks
        ]

        return {
            "citations": citations,
            "citation_count": len(citations)
        }
