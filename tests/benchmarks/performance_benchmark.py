import pytest
from typing import List
import time

from src.core.rag_pipeline import RAGPipeline
from src.core.document_loader import FlexibleDocumentLoader
from src.core.embedding_service import EmbeddingService

class PerformanceBenchmarks:
    """
    Comprehensive performance benchmarking for RAG pipeline
    """

    @pytest.fixture
    def sample_documents(self, tmp_path):
        """Generate sample documents for benchmarking"""
        documents = [
            tmp_path / f"doc_{i}.txt" for i in range(100)
        ]

        for doc in documents:
            doc.write_text(f"Sample document content for benchmark {doc.stem}")

        return [str(doc) for doc in documents]

    def test_document_ingestion_performance(
        self,
        benchmark,
        sample_documents
    ):
        """
        Benchmark document ingestion performance

        Measures:
        - Total ingestion time
        - Documents per second
        - Memory usage
        """
        loader = FlexibleDocumentLoader()
        embedding_service = EmbeddingService()

        def ingestion_func():
            pipeline = RAGPipeline(
                loader=loader,
                text_splitter=None,  # Use default
                embedding_model=embedding_service.embed_query,
                vector_db=None  # In-memory for benchmark
            )
            return pipeline.ingest_documents(sample_documents)

        result = benchmark(ingestion_func)

        assert result['total_documents'] == len(sample_documents)

    def test_query_retrieval_performance(
        self,
        benchmark,
        sample_documents
    ):
        """
        Benchmark semantic search performance

        Measures:
        - Query response time
        - Number of retrieved chunks
        """
        loader = FlexibleDocumentLoader()
        embedding_service = EmbeddingService()

        # Prepare pipeline with documents
        pipeline = RAGPipeline(
            loader=loader,
            text_splitter=None,
            embedding_model=embedding_service.embed_query,
            vector_db=None
        )
        pipeline.ingest_documents(sample_documents)

        def query_func():
            return pipeline.retrieve(
                "performance benchmark query",
                top_k=10
            )

        results = benchmark(query_func)
        assert len(results) > 0

    @pytest.mark.parametrize("document_count", [10, 100, 1000])
    def test_scalability(
        self,
        benchmark,
        tmp_path,
        document_count
    ):
        """
        Test RAG pipeline scalability with increasing document volumes
        """
        documents = [
            tmp_path / f"scalability_doc_{i}.txt"
            for i in range(document_count)
        ]

        for doc in documents:
            doc.write_text(f"Scalability test document {doc.stem}")

        loader = FlexibleDocumentLoader()
        embedding_service = EmbeddingService()

        def scalability_test():
            pipeline = RAGPipeline(
                loader=loader,
                text_splitter=None,
                embedding_model=embedding_service.embed_query,
                vector_db=None
            )
            pipeline.ingest_documents([str(doc) for doc in documents])

        result = benchmark(scalability_test)

        # Optional: Add performance assertions
        # assert result < expected_time_threshold