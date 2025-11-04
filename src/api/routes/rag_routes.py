from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import tempfile
import os

from src.core.rag_pipeline import RAGPipeline
from src.core.document_loader import FlexibleDocumentLoader
from src.core.metadata_filter import MetadataFilter
from src.core.error_handler import ErrorHandler

class DocumentUploadRequest(BaseModel):
    """Request model for document upload"""
    file_paths: List[str] = Field(..., min_items=1)
    metadata: Optional[Dict[str, Any]] = None

class QueryRequest(BaseModel):
    """Request model for RAG query"""
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    """Response model for RAG query"""
    response: str
    context_chunks: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class RAGRouter:
    """RAG API Router with comprehensive functionality"""

    def __init__(
        self,
        rag_pipeline: RAGPipeline,
        error_handler: ErrorHandler
    ):
        """
        Initialize RAG Router with dependencies

        Args:
            rag_pipeline: Configured RAG pipeline
            error_handler: Error handling utility
        """
        self.router = APIRouter()
        self.rag_pipeline = rag_pipeline
        self.error_handler = error_handler
        self._setup_routes()

    def _setup_routes(self):
        """Configure API routes"""

        @self.router.post("/upload-file")
        async def upload_file(file: UploadFile = File(...)):
            """
            Upload a file and index it in the RAG system

            Args:
                file: Uploaded file

            Returns:
                Ingestion statistics
            """
            try:
                # Save uploaded file to temporary location
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_path = temp_file.name

                # Ingest the document
                result = self.rag_pipeline.ingest_documents([temp_path])

                # Clean up temp file
                os.unlink(temp_path)

                return {
                    "filename": file.filename,
                    "total_documents": result["total_documents"],
                    "total_chunks": result["total_chunks"]
                }

            except Exception as e:
                error_info = self.error_handler.log_error(e, {
                    'filename': file.filename
                })
                raise HTTPException(
                    status_code=500,
                    detail=f"File upload failed: {error_info['error_message']}"
                )

        @self.router.post("/upload", response_model=Dict[str, int])
        async def upload_documents(request: DocumentUploadRequest):
            """
            Upload and index documents in the RAG system

            Args:
                request: Document upload request

            Returns:
                Ingestion statistics
            """
            try:
                # Apply optional metadata transformations
                if request.metadata:
                    documents = FlexibleDocumentLoader.load_documents(request.file_paths)
                    documents = [
                        {**doc, 'metadata': {**doc.get('metadata', {}), **request.metadata}}
                        for doc in documents
                    ]
                else:
                    documents = request.file_paths

                result = self.rag_pipeline.ingest_documents(documents)
                return result

            except Exception as e:
                error_info = self.error_handler.log_error(e, {
                    'file_paths': request.file_paths,
                    'metadata': request.metadata
                })
                raise HTTPException(
                    status_code=500,
                    detail=f"Document upload failed: {error_info['error_message']}"
                )

        @self.router.post("/query", response_model=QueryResponse)
        async def process_query(request: QueryRequest):
            """
            Process query with RAG pipeline

            Args:
                request: Query request with optional filters

            Returns:
                Augmented query response
            """
            try:
                # Retrieve context chunks
                context_chunks = self.rag_pipeline.retrieve(
                    request.query,
                    top_k=request.top_k
                )

                # Apply optional metadata filters
                if request.filters:
                    context_chunks = MetadataFilter.filter_by_tags(
                        context_chunks,
                        include_tags=request.filters.get('include_tags'),
                        exclude_tags=request.filters.get('exclude_tags')
                    )

                # Generate response
                response = self.rag_pipeline.generate_response(
                    context_chunks,
                    request.query
                )

                # Extract citations
                citations_result = self.rag_pipeline.extract_citations(
                    context_chunks,
                    response
                )

                return QueryResponse(
                    response=response,
                    context_chunks=context_chunks,
                    citations=citations_result['citations'],
                    metadata={
                        'citation_count': citations_result['citation_count'],
                        'total_context_chunks': len(context_chunks)
                    }
                )

            except Exception as e:
                error_info = self.error_handler.log_error(e, {
                    'query': request.query,
                    'filters': request.filters
                })
                raise HTTPException(
                    status_code=500,
                    detail=f"Query processing failed: {error_info['error_message']}"
                )