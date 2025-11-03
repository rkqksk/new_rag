from typing import List, Dict, Any
from langchain.document_loaders import BaseLoader
from langchain.text_splitter import TextSplitter
from langchain.embeddings import BaseEmbedding
from qdrant_client import QdrantClient

class RAGPipeline:
    def __init__(
        self,
        loader: BaseLoader,
        text_splitter: TextSplitter,
        embedding_model: BaseEmbedding,
        vector_db: QdrantClient,
        collection_name: str = "documents"
    ):
        """
        Initialize RAG Pipeline with core components

        Args:
            loader: Document loading mechanism
            text_splitter: Text chunking strategy
            embedding_model: Embedding generation model
            vector_db: Vector database client
            collection_name: Qdrant collection name
        """
        self.loader = loader
        self.text_splitter = text_splitter
        self.embedding_model = embedding_model
        self.vector_db = vector_db
        self.collection_name = collection_name

    def ingest_documents(self, source_paths: List[str]) -> Dict[str, Any]:
        """
        Load, split, and index documents into vector database

        Args:
            source_paths: List of document file paths

        Returns:
            Ingestion statistics
        """
        # Load documents
        documents = self.loader.load_documents(source_paths)

        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)

        # Generate embeddings
        embeddings = [
            self.embedding_model.embed_query(chunk.page_content)
            for chunk in chunks
        ]

        # Index in Qdrant
        points = [
            {
                'id': hash(chunk.page_content),
                'vector': embedding,
                'payload': {
                    'text': chunk.page_content,
                    'metadata': chunk.metadata
                }
            }
            for chunk, embedding in zip(chunks, embeddings)
        ]

        self.vector_db.upsert(
            collection_name=self.collection_name,
            points=points
        )

        return {
            'total_documents': len(source_paths),
            'total_chunks': len(chunks)
        }

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search on indexed documents

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            Top matching document chunks
        """
        query_embedding = self.embedding_model.embed_query(query)

        search_results = self.vector_db.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k
        )

        return [
            {
                'text': result.payload['text'],
                'metadata': result.payload['metadata'],
                'score': result.score
            }
            for result in search_results
        ]