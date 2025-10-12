"""
RAG Enterprise Workflow Orchestrator
Central coordination for the entire RAG pipeline
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import traceback

from agents.chunking_agent import chunk_text, chunk_table, chunk_paragraphs
from agents.embedding_agent import try_embedding_with_fallback
from agents.vector_db_loader_agent import save_faiss_index, save_metadata
from agents.search_agent import search_faiss
from agents.monitoring_agent import MonitoringAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessingStage(Enum):
    PENDING = "pending"
    CRAWLING = "crawling"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentType(Enum):
    PDF = "pdf"
    EXCEL = "excel"
    WORD = "word"
    IMAGE = "image"
    TEXT = "text"
    HTML = "html"

@dataclass
class ProcessingMetadata:
    source_url: Optional[str] = None
    upload_time: datetime = field(default_factory=datetime.now)
    customer_id: Optional[str] = None
    department: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    error_messages: List[str] = field(default_factory=list)

@dataclass
class Document:
    id: str
    path: Path
    type: DocumentType
    content: Optional[Any] = None
    chunks: List[Dict] = field(default_factory=list)
    embeddings: List[List[float]] = field(default_factory=list)
    metadata: ProcessingMetadata = field(default_factory=ProcessingMetadata)
    stage: ProcessingStage = ProcessingStage.PENDING

class PipelineError(Exception):
    pass

class WorkflowOrchestrator:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.monitor = MonitoringAgent()
        self.processing_queue = asyncio.Queue()
        self.error_queue = asyncio.Queue()
        self.max_workers = self.config.get('max_workers', 4)
        self.retry_attempts = self.config.get('retry_attempts', 3)
        self.primary_model = self.config.get('primary_embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
        self.fallback_model = self.config.get('fallback_embedding_model', 'jhgan/ko-sbert-nli')
        logger.info(f"Orchestrator initialized with {self.max_workers} workers")

    async def process_document(self, document: Document) -> Document:
        start_time = datetime.now()
        try:
            if document.stage == ProcessingStage.PENDING:
                document = await self._parse_document(document)
            if document.stage == ProcessingStage.PARSING:
                document = await self._chunk_document(document)
            if document.stage == ProcessingStage.CHUNKING:
                document = await self._embed_chunks(document)
            if document.stage == ProcessingStage.EMBEDDING:
                document = await self._index_document(document)
            document.metadata.processing_time = (datetime.now() - start_time).total_seconds()
            document.stage = ProcessingStage.COMPLETED
            logger.info(f"Document {document.id} processed in {document.metadata.processing_time:.2f}s")
            await self.monitor.record_success(document)
            return document
        except Exception as e:
            document.stage = ProcessingStage.FAILED
            document.metadata.error_messages.append(str(e))
            logger.error(f"Failed to process document {document.id}: {e}")
            logger.error(traceback.format_exc())
            await self.monitor.record_error(document, e)
            await self.error_queue.put(document)
            raise PipelineError(f"Document processing failed: {e}")

    async def _parse_document(self, document: Document) -> Document:
        document.stage = ProcessingStage.PARSING
        logger.info(f"Parsing {document.type.value} document: {document.id}")
        if document.type == DocumentType.PDF:
            from agents.file_parser_agent import parse_pdf
            document.content = await asyncio.to_thread(parse_pdf, document.path)
        elif document.type == DocumentType.EXCEL:
            import pandas as pd
            document.content = await asyncio.to_thread(pd.read_excel, document.path)
        elif document.type == DocumentType.IMAGE:
            from agents.file_parser_agent import parse_image
            document.content = await asyncio.to_thread(parse_image, document.path)
        else:
            with open(document.path, 'r', encoding='utf-8') as f:
                document.content = f.read()
        return document

    async def _chunk_document(self, document: Document) -> Document:
        document.stage = ProcessingStage.CHUNKING
        logger.info(f"Chunking document: {document.id}")
        chunk_size = self.config.get('chunk_size', 500)
        overlap = self.config.get('chunk_overlap', 50)
        if document.type in [DocumentType.PDF, DocumentType.TEXT, DocumentType.HTML]:
            chunks = chunk_text(document.content, chunk_size=chunk_size, overlap=overlap)
        elif document.type == DocumentType.EXCEL:
            chunks = []
            for sheet_name, df in document.content.items():
                table_chunks = chunk_table(df.to_dict('records'), chunk_by='row')
                chunks.extend(table_chunks)
        else:
            chunks = chunk_paragraphs(str(document.content), chunk_size=chunk_size)
        document.chunks = [{
            'id': f"{document.id}_chunk_{i}",
            'text': chunk,
            'metadata': {'document_id': document.id, 'chunk_index': i, 'source': str(document.path)}
        } for i, chunk in enumerate(chunks)]
        logger.info(f"Created {len(document.chunks)} chunks for document {document.id}")
        return document

    async def _embed_chunks(self, document: Document) -> Document:
        document.stage = ProcessingStage.EMBEDDING
        logger.info(f"Generating embeddings for {len(document.chunks)} chunks")
        tasks = []
        for chunk in document.chunks:
            task = asyncio.create_task(self._generate_embedding(chunk['text'], chunk['id']))
            tasks.append(task)
        embeddings = await asyncio.gather(*tasks, return_exceptions=True)
        valid_embeddings = []
        for i, emb in enumerate(embeddings):
            if isinstance(emb, Exception):
                logger.error(f"Failed to generate embedding for chunk {i}: {emb}")
                document.metadata.error_messages.append(f"Embedding failed for chunk {i}")
            else:
                valid_embeddings.append(emb)
                document.chunks[i]['embedding'] = emb
        document.embeddings = valid_embeddings
        logger.info(f"Generated {len(valid_embeddings)} embeddings successfully")
        return document

    async def _generate_embedding(self, text: str, chunk_id: str) -> List[float]:
        return await asyncio.to_thread(
            try_embedding_with_fallback,
            self.primary_model,
            self.fallback_model,
            text,
            chunk_id
        )

    async def _index_document(self, document: Document) -> Document:
        document.stage = ProcessingStage.INDEXING
        logger.info(f"Indexing document {document.id} with {len(document.embeddings)} embeddings")
        if not document.embeddings:
            raise PipelineError("No embeddings to index")
        import numpy as np
        embeddings_array = np.array(document.embeddings, dtype='float32')
        metadata_list = [
            {'document_id': document.id, 'chunk_id': chunk['id'], 'text': chunk['text'], **chunk['metadata']}
            for chunk in document.chunks if 'embedding' in chunk
        ]
        index_path = self.config.get('faiss_index_path', './data/faiss.index')
        metadata_path = self.config.get('metadata_path', './data/metadata.json')
        await asyncio.to_thread(save_faiss_index, embeddings_array, index_path)
        await asyncio.to_thread(save_metadata, metadata_list, metadata_path)
        logger.info(f"Document {document.id} indexed successfully")
        return document

    async def batch_process(self, documents: List[Document]) -> List[Document]:
        logger.info(f"Starting batch processing of {len(documents)} documents")
        workers = [asyncio.create_task(self._worker()) for _ in range(self.max_workers)]
        for doc in documents:
            await self.processing_queue.put(doc)
        await self.processing_queue.join()
        for worker in workers:
            worker.cancel()
        await self._process_error_queue()
        logger.info("Batch processing completed")
        return documents

    async def _worker(self):
        while True:
            try:
                document = await self.processing_queue.get()
                await self.process_document(document)
                self.processing_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                self.processing_queue.task_done()

    async def _process_error_queue(self):
        retry_count = {}
        while not self.error_queue.empty():
            document = await self.error_queue.get()
            doc_id = document.id
            retry_count[doc_id] = retry_count.get(doc_id, 0) + 1
            if retry_count[doc_id] <= self.retry_attempts:
                logger.info(f"Retrying document {doc_id} (attempt {retry_count[doc_id]})")
                try:
                    await self.process_document(document)
                except Exception as e:
                    logger.error(f"Retry failed for {doc_id}: {e}")
                    if retry_count[doc_id] == self.retry_attempts:
                        logger.error(f"Max retries reached for {doc_id}")
                        await self.monitor.record_failure(document)
            else:
                logger.error(f"Abandoning document {doc_id} after {self.retry_attempts} attempts")

    async def run(self):
        logger.info("Starting workflow orchestrator")
        try:
            while True:
                new_documents = await self._check_for_new_documents()
                if new_documents:
                    await self.batch_process(new_documents)
                await asyncio.sleep(self.config.get('poll_interval', 60))
        except KeyboardInterrupt:
            logger.info("Shutting down orchestrator")
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            raise

    async def _check_for_new_documents(self) -> List[Document]:
        return []

if __name__ == "__main__":
    import sys
    config_path = sys.argv[1] if len(sys.argv) > 1 else "agents/workflow_config.json"
    orchestrator = WorkflowOrchestrator(config_path)
    asyncio.run(orchestrator.run())
