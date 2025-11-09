#!/usr/bin/env python3
"""
Embedding Fine-tuning Training Script (v6.0.0)
==============================================

Train domain-specific embeddings on product data

Usage:
    python scripts/train_embeddings.py --products data/products.json --output models/finetuned

Options:
    --products PATH     Path to products JSON file
    --output PATH       Output directory for fine-tuned model
    --base-model NAME   Base sentence transformer model (default: all-MiniLM-L6-v2)
    --epochs INT        Training epochs (default: 3)
    --batch-size INT    Batch size (default: 16)
    --eval              Enable evaluation on test set
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.embedding_finetuning import (
    EmbeddingDatasetBuilder,
    EmbeddingFineTuner,
    EmbeddingEvaluator,
    finetune_embeddings,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_products_from_qdrant():
    """Load products from Qdrant"""
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(url="http://localhost:6333")

        # Get all points from collection
        points = client.scroll(collection_name="products", limit=10000)[0]

        products = []
        for point in points:
            products.append({"metadata": point.payload, "id": point.id, "score": 1.0})

        logger.info(f"Loaded {len(products)} products from Qdrant")
        return products

    except Exception as e:
        logger.error(f"Failed to load from Qdrant: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description="Fine-tune embeddings on product data")
    parser.add_argument("--products", type=str, help="Path to products JSON file (optional)")
    parser.add_argument(
        "--output",
        type=str,
        default="models/finetuned-embeddings",
        help="Output directory for model",
    )
    parser.add_argument(
        "--base-model",
        type=str,
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Base model",
    )
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--eval", action="store_true", help="Enable evaluation")
    parser.add_argument("--from-qdrant", action="store_true", help="Load products from Qdrant")

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Embedding Fine-tuning Training Script")
    logger.info("=" * 60)

    # Step 1: Load products
    if args.from_qdrant:
        logger.info("Loading products from Qdrant...")
        products = load_products_from_qdrant()
    elif args.products:
        logger.info(f"Loading products from {args.products}...")
        with open(args.products, "r", encoding="utf-8") as f:
            data = json.load(f)
            products = data if isinstance(data, list) else data.get("products", [])
    else:
        logger.error("No product source specified. Use --products or --from-qdrant")
        sys.exit(1)

    if not products:
        logger.error("No products loaded. Exiting.")
        sys.exit(1)

    logger.info(f"Loaded {len(products)} products")

    # Step 2: Build dataset
    logger.info("Building training dataset...")
    builder = EmbeddingDatasetBuilder(products)
    positive_pairs = builder.create_positive_pairs()
    triplets = builder.create_hard_negatives(positive_pairs, neg_ratio=1.0)

    logger.info(f"Dataset: {len(positive_pairs)} positive pairs, {len(triplets)} triplets")

    if len(triplets) < 100:
        logger.warning(
            f"Only {len(triplets)} triplets. Recommend at least 1000 for good results."
        )

    # Step 3: Fine-tune
    logger.info(f"Fine-tuning {args.base_model}...")
    fine_tuner = EmbeddingFineTuner(base_model=args.base_model, output_path=args.output)
    fine_tuner.train(triplets=triplets, epochs=args.epochs, batch_size=args.batch_size)

    logger.info(f"✅ Fine-tuning complete! Model saved to: {args.output}")

    # Step 4: Evaluation (optional)
    if args.eval:
        logger.info("Evaluating model...")
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(args.output)
        evaluator = EmbeddingEvaluator(model)

        # Create test queries
        test_queries = [p[0] for p in positive_pairs[:100]]
        test_corpus = [p[1] for p in positive_pairs[:100]]
        test_relevant = {i: [i] for i in range(len(test_queries))}

        # Compute metrics
        mrr = evaluator.compute_mrr(test_queries, test_corpus, test_relevant)
        recall_10 = evaluator.compute_recall_at_k(test_queries, test_corpus, test_relevant, k=10)

        logger.info(f"📊 Evaluation Results:")
        logger.info(f"   MRR: {mrr:.4f}")
        logger.info(f"   Recall@10: {recall_10:.4f}")

    logger.info("=" * 60)
    logger.info("Training complete!")
    logger.info(f"Model: {args.output}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
