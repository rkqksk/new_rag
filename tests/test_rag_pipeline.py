import tempfile
from pathlib import Path

import pytest
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient

from src.core.document_loader import FlexibleDocumentLoader
from src.core.embedding_service import EmbeddingService
from src.core.rag_pipeline import RAGPipeline


class TestRAGPipeline:
    @pytest.fixture
    def temp_documents(self):
        """Create temporary test documents"""
        with tempfile.TemporaryDirectory() as tmpdir:
            documents = [
                (Path(tmpdir) / "doc1.txt", "This is a test document about machine learning."),
                (
                    Path(tmpdir) / "doc2.txt",
                    "RAG is an advanced technique in natural language processing.",
                ),
            ]

            for path, content in documents:
                path.write_text(content)

            yield [str(path) for path, _ in documents]

    @pytest.fixture
    def rag_pipeline(self):
        """Create RAG pipeline with test configurations"""
        loader = FlexibleDocumentLoader()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        embedding_model = EmbeddingService()

        # Use in-memory Qdrant for testing
        qdrant_client = QdrantClient(":memory:")

        return RAGPipeline(
            loader=loader,
            text_splitter=text_splitter,
            embedding_model=embedding_model,
            vector_db=qdrant_client,
        )

    def test_document_ingestion(self, rag_pipeline, temp_documents):
        """Test document ingestion process"""
        result = rag_pipeline.ingest_documents(temp_documents)

        assert result["total_documents"] == 2
        assert result["total_chunks"] > 0

    def test_semantic_retrieval(self, rag_pipeline, temp_documents):
        """Test semantic retrieval from ingested documents"""
        # First ingest documents
        rag_pipeline.ingest_documents(temp_documents)

        # Perform retrieval
        query = "machine learning techniques"
        results = rag_pipeline.retrieve(query, top_k=2)

        assert len(results) > 0
        assert all("text" in result for result in results)
        assert all("score" in result for result in results)

    def test_loader_supported_extensions(self):
        """Verify supported document extensions"""
        extensions = FlexibleDocumentLoader.get_supported_extensions()
        expected_extensions = [".pdf", ".txt", ".csv", ".md"]

        assert set(extensions) == set(expected_extensions)

    def test_embedding_model_availability(self):
        """Test embedding model availability and initialization"""
        models = EmbeddingService.list_available_models()

        assert len(models) > 0
        assert "all-MiniLM-L6-v2" in models
        assert "all-mpnet-base-v2" in models
