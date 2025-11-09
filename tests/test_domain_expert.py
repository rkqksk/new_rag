import tempfile
from pathlib import Path

import pytest
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient

from src.core.document_loader import FlexibleDocumentLoader
from src.core.embedding_service import EmbeddingService
from src.core.model_integrator import ModelIntegrator
from src.core.rag_pipeline import RAGPipeline
from src.services.domain_expert import DomainExpert


class TestDomainExpert:
    @pytest.fixture
    def temp_manufacturing_documents(self):
        """Create temporary manufacturing documents for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            documents = [
                (
                    Path(tmpdir) / "sop_1.txt",
                    "Manufacturing Standard Operating Procedure for Quality Control",
                ),
                (
                    Path(tmpdir) / "process_1.txt",
                    "Process Flow for Precision Manufacturing with Cpk Metrics",
                ),
                (
                    Path(tmpdir) / "quality_1.txt",
                    "ISO 9001 Quality Management Principles in Manufacturing",
                ),
            ]

            for path, content in documents:
                path.write_text(content)

            yield [str(path) for path, _ in documents]

    @pytest.fixture
    def manufacturing_expert(self):
        """Create a manufacturing domain expert for testing"""
        # Initialize core components
        qdrant_client = QdrantClient(":memory:")
        loader = FlexibleDocumentLoader()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        embedding_service = EmbeddingService()
        model_integrator = ModelIntegrator()

        # Create RAG pipeline
        rag_pipeline = RAGPipeline(
            loader=loader,
            text_splitter=text_splitter,
            embedding_model=embedding_service,
            vector_db=qdrant_client,
        )

        # Create manufacturing expert
        return DomainExpert.create_manufacturing_expert(
            rag_pipeline=rag_pipeline,
            embedding_service=embedding_service,
            model_integrator=model_integrator,
        )

    def test_domain_expert_document_ingestion(
        self, manufacturing_expert, temp_manufacturing_documents
    ):
        """Test domain-specific document ingestion"""
        result = manufacturing_expert.ingest_domain_documents(temp_manufacturing_documents)

        assert result["total_documents"] == 3
        assert result["total_chunks"] > 0

    def test_domain_knowledge_query(self, manufacturing_expert, temp_manufacturing_documents):
        """Test domain-specific knowledge retrieval"""
        # First ingest documents
        manufacturing_expert.ingest_domain_documents(temp_manufacturing_documents)

        # Perform query
        query_result = manufacturing_expert.query_domain_knowledge(
            "What are manufacturing quality control principles?"
        )

        assert "response" in query_result
        assert "context_chunks" in query_result
        assert "citations" in query_result
        assert query_result["metadata"]["domain"] == "manufacturing"
        assert len(query_result["context_chunks"]) > 0

    def test_domain_expert_metadata_filtering(
        self, manufacturing_expert, temp_manufacturing_documents
    ):
        """Test metadata-based filtering in domain expert"""
        # Ingest documents
        manufacturing_expert.ingest_domain_documents(
            temp_manufacturing_documents, metadata={"source": "test_docs"}
        )

        # Query with additional filters
        query_result = manufacturing_expert.query_domain_knowledge(
            "Manufacturing quality principles", filters={"source": "test_docs"}
        )

        assert query_result["metadata"]["domain"] == "manufacturing"
        assert len(query_result["context_chunks"]) > 0

    def test_citation_extraction(self, manufacturing_expert, temp_manufacturing_documents):
        """Verify citation extraction mechanism"""
        # Ingest documents
        manufacturing_expert.ingest_domain_documents(temp_manufacturing_documents)

        # Perform query
        query_result = manufacturing_expert.query_domain_knowledge(
            "ISO 9001 principles in manufacturing"
        )

        assert "citations" in query_result
        assert isinstance(query_result["citations"], list)
        assert query_result["metadata"]["citation_count"] >= 0
