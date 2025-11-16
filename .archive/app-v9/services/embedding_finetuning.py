"""
Embedding Fine-tuning for Domain-Specific Optimization (v6.0.0)
================================================================

Fine-tune sentence transformer models on domain-specific data for improved search quality.

Features:
- Dataset preparation from existing product data
- Contrastive learning with positive/negative pairs
- Triplet loss training
- Evaluation metrics (MRR, NDCG, Recall@K)
- Model export and deployment

Training Data:
- Positive pairs: (query, relevant_product)
- Hard negatives: (query, similar_but_irrelevant_product)
- Triplet: (anchor, positive, negative)

Version: v6.0.0
"""

import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from sentence_transformers import (
    InputExample,
    SentenceTransformer,
    evaluation,
    losses,
)
from sentence_transformers.evaluation import InformationRetrievalEvaluator
from torch.utils.data import DataLoader

logger = logging.getLogger(__name__)


# ============================================================================
# Dataset Preparation
# ============================================================================


class EmbeddingDatasetBuilder:
    """
    Build training dataset from product data for embedding fine-tuning
    """

    def __init__(self, products: List[Dict]):
        """
        Initialize dataset builder

        Args:
            products: List of product dictionaries with metadata
        """
        self.products = products
        logger.info(f"EmbeddingDatasetBuilder initialized with {len(products)} products")

    def create_positive_pairs(self) -> List[Tuple[str, str]]:
        """
        Create positive pairs (query, product_text)

        Positive pairs are queries that should match specific products

        Returns:
            List of (query, product_text) tuples
        """
        positive_pairs = []

        for product in self.products:
            meta = product.get("metadata", {})

            # Extract product info
            product_name = meta.get("product_name", "")
            product_code = meta.get("product_code", "")
            material = meta.get("material", "")
            capacity = meta.get("capacity", "")

            if not product_name:
                continue

            # Create product text
            product_text = f"{product_name} {material} {capacity}"

            # Generate queries
            queries = []

            # Query 1: Product name
            queries.append(product_name)

            # Query 2: Material + capacity
            if material and capacity:
                queries.append(f"{capacity} {material} 용기")

            # Query 3: Capacity only
            if capacity:
                queries.append(f"{capacity} 용기")

            # Query 4: Product code
            if product_code:
                queries.append(product_code)

            # Add pairs
            for query in queries:
                if query and len(query) > 2:
                    positive_pairs.append((query, product_text))

        logger.info(f"Created {len(positive_pairs)} positive pairs")
        return positive_pairs

    def create_hard_negatives(
        self, positive_pairs: List[Tuple[str, str]], neg_ratio: float = 1.0
    ) -> List[Tuple[str, str, str]]:
        """
        Create triplets with hard negatives (anchor, positive, negative)

        Hard negatives are products that are similar but not relevant

        Args:
            positive_pairs: Positive (query, product) pairs
            neg_ratio: Ratio of negatives to positives

        Returns:
            List of (query, positive_product, negative_product) triplets
        """
        triplets = []

        # Group products by material for hard negative sampling
        products_by_material = {}
        for product in self.products:
            material = product.get("metadata", {}).get("material", "")
            if material:
                products_by_material.setdefault(material, []).append(product)

        for query, positive_text in positive_pairs:
            # Find positive product
            positive_product = None
            for product in self.products:
                product_text = f"{product.get('metadata', {}).get('product_name', '')} {product.get('metadata', {}).get('material', '')} {product.get('metadata', {}).get('capacity', '')}"
                if product_text.strip() == positive_text.strip():
                    positive_product = product
                    break

            if not positive_product:
                continue

            # Sample hard negatives (same material, different capacity/name)
            material = positive_product.get("metadata", {}).get("material", "")
            candidates = products_by_material.get(material, [])

            # Filter out positive product
            negatives = [p for p in candidates if p != positive_product]

            # Sample negatives
            num_negatives = max(1, int(neg_ratio))
            sampled_negatives = random.sample(negatives, min(num_negatives, len(negatives)))

            for neg_product in sampled_negatives:
                neg_text = f"{neg_product.get('metadata', {}).get('product_name', '')} {neg_product.get('metadata', {}).get('material', '')} {neg_product.get('metadata', {}).get('capacity', '')}"
                triplets.append((query, positive_text, neg_text))

        logger.info(f"Created {len(triplets)} triplets with hard negatives")
        return triplets

    def save_dataset(self, output_path: str):
        """
        Save dataset to JSON file

        Args:
            output_path: Path to save dataset
        """
        positive_pairs = self.create_positive_pairs()
        triplets = self.create_hard_negatives(positive_pairs)

        dataset = {
            "positive_pairs": positive_pairs,
            "triplets": triplets,
            "num_products": len(self.products),
            "num_positive_pairs": len(positive_pairs),
            "num_triplets": len(triplets),
        }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        logger.info(f"Dataset saved to {output_path}")


# ============================================================================
# Fine-tuning
# ============================================================================


class EmbeddingFineTuner:
    """
    Fine-tune sentence transformer models for domain-specific embeddings
    """

    def __init__(
        self,
        base_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        output_path: str = "models/finetuned-embeddings",
    ):
        """
        Initialize fine-tuner

        Args:
            base_model: HuggingFace base model
            output_path: Path to save fine-tuned model
        """
        self.base_model = base_model
        self.output_path = output_path
        self.model = None

        logger.info(f"EmbeddingFineTuner initialized (base_model={base_model})")

    def load_model(self):
        """Load base model"""
        if self.model is None:
            logger.info(f"Loading base model: {self.base_model}")
            self.model = SentenceTransformer(self.base_model)
            logger.info("Base model loaded successfully")

    def prepare_training_data(
        self, triplets: List[Tuple[str, str, str]]
    ) -> List[InputExample]:
        """
        Prepare training data from triplets

        Args:
            triplets: List of (anchor, positive, negative) triplets

        Returns:
            List of InputExample for training
        """
        train_examples = []

        for anchor, positive, negative in triplets:
            # Create InputExample for triplet loss
            example = InputExample(texts=[anchor, positive, negative])
            train_examples.append(example)

        logger.info(f"Prepared {len(train_examples)} training examples")
        return train_examples

    def train(
        self,
        triplets: List[Tuple[str, str, str]],
        epochs: int = 3,
        batch_size: int = 16,
        warmup_steps: int = 100,
        evaluation_steps: int = 500,
    ):
        """
        Train model on triplets

        Args:
            triplets: Training triplets (anchor, positive, negative)
            epochs: Number of training epochs
            batch_size: Training batch size
            warmup_steps: Warmup steps for learning rate
            evaluation_steps: Steps between evaluations
        """
        self.load_model()

        # Prepare training data
        train_examples = self.prepare_training_data(triplets)

        # Create data loader
        train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)

        # Define loss function (Triplet Loss)
        train_loss = losses.TripletLoss(model=self.model)

        # Train model
        logger.info(f"Starting training: {epochs} epochs, {len(train_examples)} examples")

        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=epochs,
            warmup_steps=warmup_steps,
            output_path=self.output_path,
            show_progress_bar=True,
        )

        logger.info(f"Training complete. Model saved to {self.output_path}")

    def evaluate(self, queries: List[str], corpus: List[str], relevant_docs: Dict[str, List[str]]):
        """
        Evaluate model on test set

        Args:
            queries: Test queries
            corpus: Document corpus
            relevant_docs: Dict mapping query to relevant document IDs

        Returns:
            Evaluation metrics
        """
        if self.model is None:
            self.load_model()

        # Create evaluator
        evaluator = InformationRetrievalEvaluator(
            queries=queries, corpus=corpus, relevant_docs=relevant_docs
        )

        # Evaluate
        score = evaluator(self.model)

        logger.info(f"Evaluation score: {score}")
        return score


# ============================================================================
# Evaluation Metrics
# ============================================================================


class EmbeddingEvaluator:
    """
    Evaluate embedding quality with standard metrics
    """

    def __init__(self, model: SentenceTransformer):
        self.model = model

    def compute_mrr(
        self, queries: List[str], corpus: List[str], relevant_docs: Dict[str, List[int]]
    ) -> float:
        """
        Compute Mean Reciprocal Rank (MRR)

        Args:
            queries: List of queries
            corpus: List of documents
            relevant_docs: Dict mapping query index to relevant doc indices

        Returns:
            MRR score
        """
        # Encode queries and corpus
        query_embeddings = self.model.encode(queries, convert_to_tensor=True)
        corpus_embeddings = self.model.encode(corpus, convert_to_tensor=True)

        # Compute similarity
        from sentence_transformers import util

        scores = util.cos_sim(query_embeddings, corpus_embeddings)

        # Compute MRR
        reciprocal_ranks = []
        for i, query_scores in enumerate(scores):
            # Get ranking
            ranking = torch.argsort(query_scores, descending=True).cpu().numpy()

            # Find rank of first relevant document
            relevant = relevant_docs.get(i, [])
            for rank, doc_idx in enumerate(ranking, start=1):
                if doc_idx in relevant:
                    reciprocal_ranks.append(1.0 / rank)
                    break
            else:
                reciprocal_ranks.append(0.0)

        mrr = np.mean(reciprocal_ranks)
        logger.info(f"MRR: {mrr:.4f}")
        return mrr

    def compute_recall_at_k(
        self, queries: List[str], corpus: List[str], relevant_docs: Dict[str, List[int]], k: int = 10
    ) -> float:
        """
        Compute Recall@K

        Args:
            queries: List of queries
            corpus: List of documents
            relevant_docs: Dict mapping query index to relevant doc indices
            k: Top-K threshold

        Returns:
            Recall@K score
        """
        import torch
        from sentence_transformers import util

        # Encode
        query_embeddings = self.model.encode(queries, convert_to_tensor=True)
        corpus_embeddings = self.model.encode(corpus, convert_to_tensor=True)

        # Similarity
        scores = util.cos_sim(query_embeddings, corpus_embeddings)

        # Compute recall@k
        recalls = []
        for i, query_scores in enumerate(scores):
            # Get top-k
            top_k = torch.topk(query_scores, k).indices.cpu().numpy()

            # Check recall
            relevant = set(relevant_docs.get(i, []))
            retrieved = set(top_k)

            if len(relevant) > 0:
                recall = len(relevant & retrieved) / len(relevant)
                recalls.append(recall)

        avg_recall = np.mean(recalls) if recalls else 0.0
        logger.info(f"Recall@{k}: {avg_recall:.4f}")
        return avg_recall


# ============================================================================
# Convenience Functions
# ============================================================================


def build_dataset_from_products(products: List[Dict], output_path: str):
    """
    Build training dataset from product data

    Args:
        products: List of product dictionaries
        output_path: Path to save dataset
    """
    builder = EmbeddingDatasetBuilder(products)
    builder.save_dataset(output_path)


def finetune_embeddings(
    dataset_path: str,
    base_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    output_path: str = "models/finetuned-embeddings",
    epochs: int = 3,
    batch_size: int = 16,
):
    """
    Fine-tune embeddings on domain-specific dataset

    Args:
        dataset_path: Path to training dataset (JSON)
        base_model: Base sentence transformer model
        output_path: Path to save fine-tuned model
        epochs: Training epochs
        batch_size: Batch size
    """
    # Load dataset
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    triplets = dataset.get("triplets", [])

    if not triplets:
        raise ValueError("No triplets found in dataset")

    # Create fine-tuner
    fine_tuner = EmbeddingFineTuner(base_model=base_model, output_path=output_path)

    # Train
    fine_tuner.train(triplets=triplets, epochs=epochs, batch_size=batch_size)

    logger.info(f"Fine-tuning complete! Model saved to: {output_path}")


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Build dataset
    products = [
        {
            "metadata": {
                "product_id": "001",
                "product_name": "50ml PET 용기",
                "product_code": "PET-50-001",
                "material": "PET",
                "capacity": "50ml",
            }
        },
        {
            "metadata": {
                "product_id": "002",
                "product_name": "100ml PP 용기",
                "product_code": "PP-100-001",
                "material": "PP",
                "capacity": "100ml",
            }
        },
    ]

    # Build dataset
    build_dataset_from_products(products, "data/embedding_dataset.json")

    # Fine-tune
    finetune_embeddings(
        dataset_path="data/embedding_dataset.json",
        output_path="models/finetuned-embeddings",
        epochs=1,  # Reduced for example
        batch_size=8,
    )
