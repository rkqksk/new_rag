from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient

from src.api.routes.rag_routes import RAGRouter
from src.core.document_loader import FlexibleDocumentLoader
from src.core.embedding_service import EmbeddingService
from src.core.error_handler import ErrorHandler
from src.core.model_integrator import ModelConfig, ModelIntegrator, ModelProvider
from src.core.rag_pipeline import RAGPipeline


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application

    Returns:
        Configured FastAPI application
    """
    # Initialize core components
    error_handler = ErrorHandler()
    embedding_service = EmbeddingService()
    model_integrator = ModelIntegrator()

    # Register local Ollama model
    model_integrator.register_model(
        "local_llm",
        ModelConfig(provider=ModelProvider.OLLAMA, model_name="mistral:7b-instruct-v0.2-q4_K_M"),
    )

    # Initialize vector database
    qdrant_client = QdrantClient(":memory:")

    # Configure text splitter
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    # Create RAG pipeline
    rag_pipeline = RAGPipeline(
        loader=FlexibleDocumentLoader(),
        text_splitter=text_splitter,
        embedding_model=embedding_service,
        vector_db=qdrant_client,
    )

    # Create FastAPI application
    app = FastAPI(
        title="RAG Enterprise",
        description="Open-source Retrieval-Augmented Generation System",
        version="0.1.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create and include RAG router
    rag_router = RAGRouter(rag_pipeline=rag_pipeline, error_handler=error_handler)
    app.include_router(rag_router.router, prefix="/rag", tags=["Retrieval-Augmented Generation"])

    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


# Application entry point
app = create_app()
