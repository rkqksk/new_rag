#!/usr/bin/env python3
"""
Test script for quality improvement comparison
Before (current RAG) vs After (two-stage RAG with dictionary)
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from app.services.rag_qa_service import RAGQAService, QARequest
from app.services.two_stage_rag_service import TwoStageRAGService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_current_system(qa_service: RAGQAService, query: str):
    """Test current RAG system"""
    request = QARequest(question=query, top_k=3)
    response = await qa_service.answer_question(request)

    return {
        "query": query,
        "answer": response.answer,
        "products": response.related_products,
        "confidence": response.confidence
    }


async def test_improved_system(qa_service: TwoStageRAGService, query: str):
    """Test improved two-stage RAG system"""
    response = await qa_service.answer_question(query)

    return {
        "query": query,
        "answer": response["answer"],
        "products": response["related_products"],
        "confidence": response["confidence"],
        "plan": response.get("plan")
    }


def analyze_quality(result: dict, system: str) -> dict:
    """Analyze response quality"""
    answer = result["answer"]
    products = result["products"]

    metrics = {
        "system": system,
        "query": result["query"],
        "answer_length": len(answer),
        "num_products": len(products),
        "has_product_code": "제품 코드" in answer or "제품코드" in answer,
        "has_material_info": any(mat in answer for mat in ["PE", "PET", "재질"]),
        "has_use_case": any(kw in answer for kw in ["용도", "사용", "적합"]),
        "has_capacity_info": "ml" in answer,
        "has_recommendation_reason": any(kw in answer for kw in ["추천", "이유", "장점"]),
        "confidence": result["confidence"],
        "products_enriched": sum(1 for p in products if "enriched" in p)
    }

    # Quality score (0-10)
    score = 0
    if metrics["has_product_code"]: score += 2
    if metrics["has_material_info"]: score += 2
    if metrics["has_use_case"]: score += 2
    if metrics["has_recommendation_reason"]: score += 2
    if metrics["answer_length"] > 200: score += 1
    if metrics["products_enriched"] > 0: score += 1

    metrics["quality_score"] = min(score, 10)

    return metrics


async def run_comparison():
    """Run comparison between current and improved systems"""

    # Initialize services
    qdrant = QdrantClient(host="localhost", port=6333)
    embedder = SentenceTransformer("Alibaba-NLP/gte-Qwen2-7B-instruct")

    # Current system
    current_qa = RAGQAService(
        qdrant_client=qdrant,
        embedding_model=embedder,
        ollama_url="http://localhost:11434",
        model_name="qwen2.5:3b"
    )

    # Improved system
    improved_qa = TwoStageRAGService(
        qdrant_client=qdrant,
        embedding_model=embedder,
        dictionary_path="/Users/oypnus/Project/rag-enterprise/data/product_dictionary.json",
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        ollama_url="http://localhost:11434",
        ollama_model="qwen2.5:3b"
    )

    # Test queries
    test_queries = [
        "50ml 용기 추천해줘",
        "40ml 브로우용기 어때?",
        "에센스용 소형 용기 필요해",
        "크림 담을 수 있는 큰 용기",
        "65ml 브로우용기 정보 알려줘"
    ]

    results = []

    for query in test_queries:
        logger.info(f"\n{'='*60}")
        logger.info(f"Query: {query}")
        logger.info(f"{'='*60}")

        # Test current system
        logger.info("Testing current system...")
        current_result = await test_current_system(current_qa, query)
        current_metrics = analyze_quality(current_result, "current")

        # Test improved system
        logger.info("Testing improved system...")
        improved_result = await test_improved_system(improved_qa, query)
        improved_metrics = analyze_quality(improved_result, "improved")

        # Store results
        results.append({
            "query": query,
            "current": {
                "answer": current_result["answer"],
                "metrics": current_metrics
            },
            "improved": {
                "answer": improved_result["answer"],
                "plan": improved_result.get("plan"),
                "metrics": improved_metrics
            }
        })

        # Print comparison
        logger.info(f"\n--- Current System ---")
        logger.info(f"Answer: {current_result['answer'][:200]}...")
        logger.info(f"Quality Score: {current_metrics['quality_score']}/10")
        logger.info(f"Products: {current_metrics['num_products']} (enriched: {current_metrics['products_enriched']})")

        logger.info(f"\n--- Improved System ---")
        logger.info(f"Answer: {improved_result['answer'][:200]}...")
        logger.info(f"Quality Score: {improved_metrics['quality_score']}/10")
        logger.info(f"Products: {improved_metrics['num_products']} (enriched: {improved_metrics['products_enriched']})")
        logger.info(f"Plan: {improved_result.get('plan')}")

    # Summary statistics
    current_avg_score = sum(r["current"]["metrics"]["quality_score"] for r in results) / len(results)
    improved_avg_score = sum(r["improved"]["metrics"]["quality_score"] for r in results) / len(results)
    improvement = ((improved_avg_score - current_avg_score) / current_avg_score) * 100

    summary = {
        "total_queries": len(test_queries),
        "current_avg_quality": current_avg_score,
        "improved_avg_quality": improved_avg_score,
        "improvement_percentage": improvement,
        "results": results
    }

    # Save results
    output_path = project_root / "qa_quality_comparison.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(f"\n{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total queries tested: {len(test_queries)}")
    logger.info(f"Current system avg quality: {current_avg_score:.2f}/10")
    logger.info(f"Improved system avg quality: {improved_avg_score:.2f}/10")
    logger.info(f"Improvement: {improvement:+.1f}%")
    logger.info(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(run_comparison())
