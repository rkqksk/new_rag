"""
Async RAG Q&A Service
Asynchronous version of RAG Q&A service for better performance
"""

import asyncio
import logging
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue
from sentence_transformers import SentenceTransformer

from app.utils.product_utils import (
    batch_validate_products,
    enrich_product_with_metadata,
    generate_image_urls,
    validate_product_integrity,
)

logger = logging.getLogger(__name__)


class AsyncRAGQAService:
    """Asynchronous RAG Q&A service with optimizations"""

    def __init__(
        self,
        qdrant_client: QdrantClient,
        embedding_model: SentenceTransformer,
        ollama_url: str = "http://localhost:11434",
        model_name: str = "qwen2.5:3b",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize async RAG Q&A service

        Args:
            qdrant_client: Qdrant vector DB client
            embedding_model: Sentence transformer model
            ollama_url: Ollama API URL
            model_name: LLM model name
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.qdrant = qdrant_client
        self.embedder = embedding_model
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries

        # Compile regex patterns once for performance
        self._capacity_ml_pattern = re.compile(r"(\d+)\s*(ml|미리)")
        self._capacity_g_pattern = re.compile(r"(\d+)\s*g\b")
        self._product_ml_pattern = re.compile(r"(\d+)\s*ml")
        self._product_g_pattern = re.compile(r"(\d+)\s*g\b")

        # Connection pool for HTTP client
        self._http_client: Optional[httpx.AsyncClient] = None

        logger.info(f"✅ AsyncRAGQAService initialized with model: {model_name}")

    @asynccontextmanager
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        try:
            yield self._http_client
        except Exception as e:
            logger.error(f"HTTP client error: {e}")
            raise

    async def _generate_embedding_async(self, text: str) -> List[float]:
        """
        Generate embedding asynchronously

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        loop = asyncio.get_event_loop()
        # Run CPU-intensive embedding generation in thread pool
        embedding = await loop.run_in_executor(None, self.embedder.encode, text)
        return embedding.tolist()

    async def _search_similar_async(
        self,
        query_embedding: List[float],
        collection_name: str,
        limit: int = 3,
        capacity_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search similar products asynchronously

        Args:
            query_embedding: Query embedding vector
            collection_name: Qdrant collection name
            limit: Number of results
            capacity_filter: Optional capacity filter

        Returns:
            List of similar products
        """
        loop = asyncio.get_event_loop()

        # Prepare filter if capacity is specified
        filter_obj = None
        if capacity_filter:
            filter_obj = Filter(
                must=[FieldCondition(key="capacity", match=MatchValue(value=capacity_filter))]
            )

        # Run search in thread pool to avoid blocking
        # Use a lambda to pass keyword arguments properly to qdrant.search
        def _search_with_kwargs():
            return self.qdrant.search(
                collection_name=collection_name,
                query_vector=("text", query_embedding),  # Use named "text" vector
                query_filter=filter_obj,
                limit=limit,
                score_threshold=0.3,
            )

        results = await loop.run_in_executor(None, _search_with_kwargs)

        return [{"id": hit.id, "score": hit.score, "payload": hit.payload} for hit in results]

    async def _generate_llm_response_async(
        self, question: str, context: str, retry_count: int = 0
    ) -> str:
        """
        Generate LLM response with retry logic

        Args:
            question: User question
            context: Context from similar products
            retry_count: Current retry attempt

        Returns:
            Generated answer
        """
        prompt = f"""You are a helpful product recommendation assistant.

Based on the following product information, answer the user's question.

Products:
{context}

Question: {question}

Please provide a helpful and concise answer in Korean."""

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 500,
        }

        try:
            async with self._get_http_client() as client:
                response = await client.post(f"{self.ollama_url}/api/generate", json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("response", "죄송합니다. 답변을 생성할 수 없습니다.")

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            if retry_count < self.max_retries:
                logger.warning(
                    f"LLM generation failed, retrying... ({retry_count + 1}/{self.max_retries})"
                )
                await asyncio.sleep(2**retry_count)  # Exponential backoff
                return await self._generate_llm_response_async(question, context, retry_count + 1)
            logger.error(f"LLM generation failed after {self.max_retries} retries: {e}")
            return "죄송합니다. 시스템 오류로 답변을 생성할 수 없습니다."

    async def answer_question_async(
        self,
        question: str,
        collection_name: str = "products_all",
        top_k: int = 3,
        return_all: bool = False,
        min_integrity_score: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Answer question using RAG approach asynchronously

        Args:
            question: User question
            collection_name: Qdrant collection name
            top_k: Number of similar products to retrieve (ignored if return_all=True)
            return_all: If True, return all filtered results
            min_integrity_score: Minimum integrity score for filtering (0.0~1.0)

        Returns:
            Response with answer and related products (with image URLs and integrity validation)
        """
        try:
            # Extract capacity from query if present
            capacity_filter = self._extract_capacity_from_query(question)

            # Generate embedding and search concurrently
            embedding_task = self._generate_embedding_async(question)

            # Wait for embedding
            query_embedding = await embedding_task

            # Search for similar products (use large limit if return_all=True)
            search_limit = 200 if return_all else top_k
            similar_products = await self._search_similar_async(
                query_embedding, collection_name, search_limit, capacity_filter
            )

            # Convert to standard format and apply integrity validation
            formatted_products = []
            for product in similar_products:
                payload = product.get("payload", {})
                formatted = {
                    "product_id": payload.get("product_id", "unknown"),
                    "product_name": payload.get("product_name", "Unknown"),
                    "category": payload.get("category", "Unknown"),
                    "similarity_score": product.get("score", 0.0),
                    "specifications": payload.get("specifications", {}),
                    "print_area_url": payload.get("print_area_url"),
                }
                formatted_products.append(formatted)

            # Apply integrity validation and enrichment
            validated_products = batch_validate_products(
                formatted_products,
                require_images=False,
                require_specs=False,
                min_integrity_score=min_integrity_score,
            )

            enriched_products = [
                enrich_product_with_metadata(p, include_image_count=True, include_spec_count=True)
                for p in validated_products
            ]

            # Apply top_k limit if return_all=False
            if not return_all:
                enriched_products = enriched_products[:top_k]

            # Prepare context from similar products
            context_parts = []
            for product in enriched_products:
                name = product.get("product_name", "Unknown")
                category = product.get("category", "Unknown")
                specs = product.get("specifications", {})
                material = specs.get("재질", "Unknown")
                capacity = specs.get("용량", "Unknown")
                context_parts.append(
                    f"- {name} (카테고리: {category}, 재질: {material}, 용량: {capacity})"
                )

            context = "\n".join(context_parts)

            # Generate LLM response
            answer = await self._generate_llm_response_async(question, context)

            return {
                "question": question,
                "answer": answer,
                "related_products": enriched_products,
                "confidence": self._calculate_confidence(enriched_products),
                "total_count": len(enriched_products),
                "return_all": return_all,
                "min_integrity_score": min_integrity_score,
                "qa_id": f"qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error in answer_question_async: {e}")
            raise

    def _extract_capacity_from_query(self, query: str) -> Optional[str]:
        """Extract capacity from query (ml/g)"""
        # ml first (50ml, 50미리)
        match = self._capacity_ml_pattern.search(query.lower())
        if match:
            return match.group(1) + "ml"

        # g search (50g)
        match = self._capacity_g_pattern.search(query.lower())
        if match:
            return match.group(1) + "g"

        return None

    def _calculate_confidence(self, products: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on search results"""
        if not products:
            return 0.0

        # Average of top scores
        scores = [p.get("score", 0.0) for p in products]
        return sum(scores) / len(scores) if scores else 0.0

    async def batch_answer_questions(
        self,
        questions: List[str],
        collection_name: str = "products_all",
        top_k: int = 3,
        return_all: bool = False,
        min_integrity_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Answer multiple questions in batch for efficiency

        Args:
            questions: List of questions
            collection_name: Qdrant collection name
            top_k: Number of similar products per question
            return_all: If True, return all filtered results
            min_integrity_score: Minimum integrity score for filtering

        Returns:
            List of responses
        """
        tasks = [
            self.answer_question_async(q, collection_name, top_k, return_all, min_integrity_score)
            for q in questions
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing question {i}: {result}")
                processed_results.append(
                    {
                        "question": questions[i],
                        "answer": "처리 중 오류가 발생했습니다.",
                        "error": str(result),
                    }
                )
            else:
                processed_results.append(result)

        return processed_results

    async def close(self):
        """Clean up resources"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
