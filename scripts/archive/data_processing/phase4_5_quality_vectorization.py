#!/usr/bin/env python3
"""
Phase 4 & 5: Quality Validation & Vectorization Preparation
- Phase 4: Schema validation, quality dashboard, ingestion readiness
- Phase 5: Chunking strategy, embedding config, index metadata
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime
from jsonschema import validate, ValidationError
import hashlib
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = Path("/Users/oypnus/Project/rag-enterprise/data")
FINAL_DIR = DATA_DIR / "crawled_products_final"
QUALITY_DIR = DATA_DIR / "quality"

QUALITY_DIR.mkdir(exist_ok=True)


class QualityValidationFramework:
    """Phase 4: Quality Validation"""

    def __init__(self):
        self.validation_results = []
        self.quality_dashboard = {}
        self.ingestion_readiness = []

    def load_all_products(self) -> Dict[str, Dict]:
        """Load all products from final structure"""
        logger.info("📂 Loading all products...")
        products = {}

        for json_file in FINAL_DIR.glob("*/products/idx_*.json"):
            product_id = json_file.stem
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    products[product_id] = json.load(f)
            except Exception as e:
                logger.error(f"Error loading {product_id}: {e}")

        logger.info(f"✅ Loaded {len(products)} products")
        return products

    def validate_schema(self, products: Dict[str, Dict]) -> Dict:
        """Validate product schema"""
        logger.info("🔍 Validating product schema...")

        # Define product schema
        schema = {
            "type": "object",
            "required": ["product_name", "idx"],
            "properties": {
                "product_name": {"type": "string"},
                "idx": {"type": "string"},
                "images": {"type": "array"},
                "specifications": {"type": "object"},
                "downloaded_images": {"type": "array"},
                "url": {"type": "string"},
                "crawled_at": {"type": "string"}
            }
        }

        passed = 0
        failed = 0

        for product_id, product in products.items():
            try:
                validate(instance=product, schema=schema)
                passed += 1
            except ValidationError as e:
                failed += 1
                self.validation_results.append({
                    "product_id": product_id,
                    "error": str(e)
                })

        logger.info(f"✅ Schema validation: {passed}/{len(products)} passed")
        return {"passed": passed, "failed": failed, "total": len(products)}

    def calculate_completeness_by_product(self, products: Dict[str, Dict]) -> List[Dict]:
        """Calculate completeness for each product"""
        logger.info("📊 Calculating completeness scores...")

        scores = []
        for product_id, product in products.items():
            # Field completeness
            fields_present = 0
            total_fields = 7

            if product.get("product_name"):
                fields_present += 1
            if product.get("idx"):
                fields_present += 1
            if product.get("images"):
                fields_present += 1
            if product.get("specifications"):
                fields_present += 1
            if product.get("downloaded_images"):
                fields_present += 1
            if product.get("url"):
                fields_present += 1
            if product.get("crawled_at"):
                fields_present += 1

            completeness = (fields_present / total_fields) * 100

            # Asset count
            image_count = len(product.get("downloaded_images", []))
            spec_count = len(product.get("specifications", {})) if isinstance(product.get("specifications"), dict) else 0

            scores.append({
                "product_id": product_id,
                "completeness": completeness,
                "image_count": image_count,
                "spec_count": spec_count,
                "status": "ready" if completeness >= 70 else "review"
            })

        return scores

    def generate_quality_dashboard(self, products: Dict[str, Dict], completeness_scores: List[Dict]) -> Dict:
        """Generate quality dashboard"""
        logger.info("📈 Generating quality dashboard...")

        # Category distribution
        category_dist = defaultdict(int)
        for product_id in products.keys():
            # Infer category from product_id range
            idx = int(product_id.split("_")[1])
            if idx < 400:
                category_dist["Bottle"] += 1
            elif idx < 800:
                category_dist["CapPump"] += 1
            else:
                category_dist["Jar"] += 1

        # Completeness distribution
        completeness_scores_list = [s["completeness"] for s in completeness_scores]
        avg_completeness = sum(completeness_scores_list) / len(completeness_scores_list)

        ready_count = len([s for s in completeness_scores if s["status"] == "ready"])

        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "total_products": len(products),
            "average_completeness": avg_completeness,
            "products_ready": ready_count,
            "products_for_review": len(completeness_scores) - ready_count,
            "category_distribution": dict(category_dist),
            "asset_statistics": {
                "total_images": sum(len(p.get("downloaded_images", [])) for p in products.values()),
                "average_images_per_product": sum(len(p.get("downloaded_images", [])) for p in products.values()) / len(products)
            },
            "specification_statistics": {
                "products_with_specs": len([p for p in products.values() if p.get("specifications")])
            }
        }

        return dashboard

    def create_ingestion_readiness_report(self, completeness_scores: List[Dict]) -> Dict:
        """Create ingestion readiness report"""
        logger.info("✅ Creating ingestion readiness report...")

        ready_products = [s for s in completeness_scores if s["status"] == "ready"]
        review_products = [s for s in completeness_scores if s["status"] == "review"]

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_products": len(completeness_scores),
            "ready_for_vectorization": len(ready_products),
            "requires_attention": len(review_products),
            "readiness_percentage": (len(ready_products) / len(completeness_scores)) * 100,
            "products_ready": [p["product_id"] for p in ready_products[:10]],
            "products_for_review": [p["product_id"] for p in review_products[:10]],
            "next_steps": [
                "1. Verify all products have valid JSON and images",
                "2. Check specification completeness",
                "3. Validate asset paths",
                "4. Proceed to Phase 5: Vectorization Preparation"
            ]
        }

        return report

    def run_phase4(self):
        """Run Phase 4: Quality Validation"""
        logger.info("\n" + "="*60)
        logger.info("PHASE 4: DATA QUALITY VALIDATION FRAMEWORK")
        logger.info("="*60 + "\n")

        products = self.load_all_products()

        # Validation
        schema_result = self.validate_schema(products)

        # Completeness
        completeness_scores = self.calculate_completeness_by_product(products)

        # Dashboard
        dashboard = self.generate_quality_dashboard(products, completeness_scores)

        # Readiness report
        readiness = self.create_ingestion_readiness_report(completeness_scores)

        # Save reports
        self._save_reports(dashboard, readiness, completeness_scores)

        logger.info("\n✅ Phase 4 Complete!")
        return dashboard, readiness, completeness_scores

    def _save_reports(self, dashboard, readiness, completeness):
        """Save all reports"""
        validation_dir = QUALITY_DIR / "validation"
        validation_dir.mkdir(exist_ok=True)

        with open(validation_dir / "quality_dashboard.json", 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2, ensure_ascii=False)

        with open(validation_dir / "ingestion_readiness.json", 'w', encoding='utf-8') as f:
            json.dump(readiness, f, indent=2, ensure_ascii=False)

        with open(validation_dir / "completeness_scores_updated.json", 'w', encoding='utf-8') as f:
            json.dump(completeness, f, indent=2, ensure_ascii=False)

        logger.info("💾 Reports saved to quality/validation/")


class VectorizationPreparation:
    """Phase 5: Vectorization Pipeline Preparation"""

    def __init__(self):
        self.chunking_config = {}
        self.embedding_config = {}
        self.index_metadata = {}

    def design_chunking_strategy(self) -> Dict:
        """Design chunking strategy"""
        logger.info("🔄 Designing chunking strategy...")

        strategy = {
            "text_chunking": {
                "method": "field_level",
                "approaches": {
                    "field_level": {
                        "units": ["product_name", "description", "specifications"],
                        "rationale": "Preserve semantic completeness per field"
                    },
                    "hierarchical_context": {
                        "format": "{category}/{product_name} → {field}",
                        "rationale": "Enable category-aware queries"
                    }
                },
                "max_tokens": 512,
                "overlap": 50
            },
            "image_chunking": {
                "method": "per_image_with_metadata",
                "metadata_injection": ["product_name", "category", "image_type"],
                "embedding_model": "OpenCLIP-ViT-H-14",
                "dimension": 1024
            },
            "document_chunking": {
                "method": "recursive_character_split",
                "chunk_size": 1000,
                "overlap": 200,
                "document_types": ["print_area", "spec_sheet"]
            }
        }

        return strategy

    def configure_embedding_models(self) -> Dict:
        """Configure embedding models"""
        logger.info("🎯 Configuring embedding models...")

        config = {
            "text_model": {
                "name": "gte-Qwen2-7B-instruct",
                "dimension": 3584,
                "max_tokens": 512,
                "batch_size": 32,
                "model_type": "dense",
                "purpose": "semantic search on product specs and descriptions"
            },
            "image_model": {
                "name": "OpenCLIP-ViT-H-14",
                "dimension": 1024,
                "input_size": [224, 224],
                "batch_size": 16,
                "model_type": "dense",
                "purpose": "visual search on product images"
            },
            "sparse_model": {
                "name": "BM25",
                "type": "keyword",
                "purpose": "traditional keyword-based search (hybrid fusion)"
            },
            "reranker": {
                "name": "cross-encoder",
                "dimension": "query-doc pairs",
                "purpose": "final ranking of retrieved results"
            }
        }

        return config

    def generate_index_metadata(self) -> Dict:
        """Generate index metadata structure"""
        logger.info("📑 Generating index metadata...")

        # Load all products
        products = {}
        for json_file in FINAL_DIR.glob("*/products/idx_*.json"):
            product_id = json_file.stem
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    product_data = json.load(f)
                    products[product_id] = product_data
            except:
                pass

        metadata = {
            "timestamp": datetime.now().isoformat(),
            "total_products": len(products),
            "collection_names": {
                "text": "products_text",
                "images": "products_images",
                "hybrid": "products_hybrid"
            },
            "chunk_mapping": self._create_chunk_mapping(products),
            "category_index": self._create_category_index(products),
            "vectorization_parameters": {
                "text_embedding_model": "gte-Qwen2-7B-instruct",
                "image_embedding_model": "OpenCLIP-ViT-H-14",
                "batch_processing": True,
                "batch_size": 32,
                "parallel_workers": 4
            }
        }

        return metadata

    def _create_chunk_mapping(self, products: Dict) -> Dict:
        """Create mapping of chunks to products"""
        mapping = {
            "text_chunks": {},
            "image_chunks": {},
            "document_chunks": {}
        }

        for product_id, product in products.items():
            # Text chunks
            mapping["text_chunks"][f"{product_id}_name"] = {
                "product_id": product_id,
                "type": "product_name",
                "weight": 1.5
            }
            mapping["text_chunks"][f"{product_id}_specs"] = {
                "product_id": product_id,
                "type": "specifications",
                "weight": 1.2
            }

            # Image chunks
            for idx, image in enumerate(product.get("downloaded_images", [])):
                mapping["image_chunks"][f"{product_id}_img_{idx}"] = {
                    "product_id": product_id,
                    "image_path": image.get("local_path"),
                    "image_type": image.get("type")
                }

        return mapping

    def _create_category_index(self, products: Dict) -> Dict:
        """Create category-based index for optimized filtering"""
        category_index = {
            "Bottle": [],
            "CapPump": [],
            "Jar": []
        }

        for product_id in products.keys():
            idx = int(product_id.split("_")[1])
            if idx < 400:
                category_index["Bottle"].append(product_id)
            elif idx < 800:
                category_index["CapPump"].append(product_id)
            else:
                category_index["Jar"].append(product_id)

        return category_index

    def design_search_fusion_strategy(self) -> Dict:
        """Design multi-modal search fusion strategy"""
        logger.info("🔀 Designing search fusion strategy...")

        strategy = {
            "fusion_algorithm": "Reciprocal Rank Fusion (RRF)",
            "retrieval_pipeline": {
                "step_1_parallel": {
                    "text_search": {
                        "model": "gte-Qwen2-7B-instruct",
                        "top_k": 20,
                        "weight": 1.0
                    },
                    "sparse_search": {
                        "model": "BM25",
                        "top_k": 20,
                        "weight": 0.8
                    },
                    "image_search": {
                        "model": "OpenCLIP-ViT-H-14",
                        "top_k": 10,
                        "weight": 0.5
                    }
                },
                "step_2_fusion": {
                    "method": "RRF with k=60",
                    "output": "top_k*2 candidates"
                },
                "step_3_reranking": {
                    "model": "cross-encoder",
                    "top_k": 10,
                    "final_output": "top-10 results"
                }
            },
            "query_intent_detection": {
                "visual_query": "detected when image provided",
                "specification_query": "detected from keywords like 재질, 사양, 직경",
                "hybrid_query": "combining text and spec search"
            }
        }

        return strategy

    def run_phase5(self):
        """Run Phase 5: Vectorization Preparation"""
        logger.info("\n" + "="*60)
        logger.info("PHASE 5: VECTORIZATION PIPELINE PREPARATION")
        logger.info("="*60 + "\n")

        # Design strategies
        chunking_strategy = self.design_chunking_strategy()
        embedding_config = self.configure_embedding_models()
        index_metadata = self.generate_index_metadata()
        fusion_strategy = self.design_search_fusion_strategy()

        # Save configurations
        self._save_configurations(chunking_strategy, embedding_config, index_metadata, fusion_strategy)

        logger.info("\n✅ Phase 5 Complete!")
        return {
            "chunking": chunking_strategy,
            "embeddings": embedding_config,
            "index_metadata": index_metadata,
            "fusion": fusion_strategy
        }

    def _save_configurations(self, chunking, embedding, metadata, fusion):
        """Save all configurations"""
        config_dir = QUALITY_DIR / "vectorization_config"
        config_dir.mkdir(exist_ok=True)

        with open(config_dir / "chunking_strategy.json", 'w', encoding='utf-8') as f:
            json.dump(chunking, f, indent=2, ensure_ascii=False)

        with open(config_dir / "embedding_models.json", 'w', encoding='utf-8') as f:
            json.dump(embedding, f, indent=2, ensure_ascii=False)

        with open(config_dir / "index_metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        with open(config_dir / "fusion_strategy.json", 'w', encoding='utf-8') as f:
            json.dump(fusion, f, indent=2, ensure_ascii=False)

        logger.info("💾 Configurations saved to quality/vectorization_config/")


def main():
    logger.info("\n" + "="*60)
    logger.info("RUNNING PHASE 4 & 5: QUALITY & VECTORIZATION")
    logger.info("="*60)

    # Phase 4: Quality Validation
    quality_framework = QualityValidationFramework()
    dashboard, readiness, completeness = quality_framework.run_phase4()

    logger.info(f"\n📊 Quality Dashboard Summary:")
    logger.info(f"   Total Products: {dashboard['total_products']}")
    logger.info(f"   Average Completeness: {dashboard['average_completeness']:.1f}%")
    logger.info(f"   Ready for Vectorization: {dashboard['products_ready']}")
    logger.info(f"   Readiness: {readiness['readiness_percentage']:.1f}%")

    # Phase 5: Vectorization Preparation
    vectorization = VectorizationPreparation()
    phase5_results = vectorization.run_phase5()

    logger.info(f"\n🎯 Vectorization Configuration:")
    logger.info(f"   Text Model: gte-Qwen2-7B-instruct (3584 dims)")
    logger.info(f"   Image Model: OpenCLIP-ViT-H-14 (1024 dims)")
    logger.info(f"   Fusion: Reciprocal Rank Fusion + Cross-Encoder Reranking")
    logger.info(f"   Collections: 3 (text, images, hybrid)")

    logger.info("\n" + "="*60)
    logger.info("✅ PHASE 4 & 5 COMPLETE!")
    logger.info("="*60)
    logger.info("\nReady for:")
    logger.info("  1. Qdrant database initialization")
    logger.info("  2. Vector ingestion pipeline")
    logger.info("  3. Hybrid search deployment")


if __name__ == "__main__":
    main()
