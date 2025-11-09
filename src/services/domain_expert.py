from typing import Any, Dict, List, Optional

from src.core.embedding_service import EmbeddingService
from src.core.model_integrator import ModelConfig, ModelIntegrator, ModelProvider
from src.core.rag_pipeline import RAGPipeline


class DomainExpert:
    """
    Specialized domain-specific RAG expert with advanced capabilities
    """

    def __init__(
        self,
        name: str,
        domain: str,
        rag_pipeline: RAGPipeline,
        embedding_service: EmbeddingService,
        model_integrator: ModelIntegrator,
    ):
        """
        Initialize a domain-specific expert

        Args:
            name: Expert identifier
            domain: Specific knowledge domain
            rag_pipeline: RAG pipeline for retrieval
            embedding_service: Embedding generation service
            model_integrator: Model management utility
        """
        self.name = name
        self.domain = domain
        self.rag_pipeline = rag_pipeline
        self.embedding_service = embedding_service
        self.model_integrator = model_integrator

    def ingest_domain_documents(
        self, document_paths: List[str], metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest domain-specific documents with optional metadata

        Args:
            document_paths: List of document file paths
            metadata: Additional metadata to attach to documents

        Returns:
            Ingestion statistics
        """
        # Attach domain-specific metadata
        domain_metadata = metadata or {}
        domain_metadata["domain"] = self.domain

        return self.rag_pipeline.ingest_documents(
            document_paths, additional_metadata=domain_metadata
        )

    def query_domain_knowledge(
        self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform domain-specific semantic search and query processing

        Args:
            query: User's query
            top_k: Number of top context chunks to retrieve
            filters: Optional metadata filters

        Returns:
            Query result with context and generated response
        """
        # Apply domain-specific filters
        domain_filters = filters or {}
        domain_filters["domain"] = self.domain

        # Retrieve context chunks
        context_chunks = self.rag_pipeline.retrieve(
            query, top_k=top_k, metadata_filters=domain_filters
        )

        # Generate response
        response = self.rag_pipeline.generate_response(context_chunks, query)

        # Extract citations
        citations = self.rag_pipeline.extract_citations(context_chunks, response)

        return {
            "response": response,
            "context_chunks": context_chunks,
            "citations": citations["citations"],
            "metadata": {"domain": self.domain, "citation_count": citations["citation_count"]},
        }

    @classmethod
    def create_manufacturing_expert(
        cls,
        rag_pipeline: RAGPipeline,
        embedding_service: EmbeddingService,
        model_integrator: Optional[ModelIntegrator] = None,
    ) -> "DomainExpert":
        """
        Factory method to create a manufacturing domain expert

        Args:
            rag_pipeline: Configured RAG pipeline
            embedding_service: Embedding service
            model_integrator: Optional model integrator

        Returns:
            Manufacturing domain expert instance
        """
        # Create model integrator if not provided
        if model_integrator is None:
            model_integrator = ModelIntegrator()
            model_integrator.register_model(
                "manufacturing_llm",
                ModelConfig(
                    provider=ModelProvider.OLLAMA, model_name="mistral:7b-instruct-v0.2-q4_K_M"
                ),
            )

        return cls(
            name="Manufacturing Expert",
            domain="manufacturing",
            rag_pipeline=rag_pipeline,
            embedding_service=embedding_service,
            model_integrator=model_integrator,
        )
