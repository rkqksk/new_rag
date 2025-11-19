#!/usr/bin/env python3
"""
Migration Script: Flat → Hierarchical Chunking

Migrates existing flat chunks to hierarchical parent-child structure.

**Phase**: Phase 1, Week 1
**Expected Results**:
- Search precision: 0.88 → 0.92 (+4.5%)
- Context completeness: +30%
- Missing information: -40%

**Usage**:
```bash
# Dry run (preview only)
python scripts/migrate_to_hierarchical_chunks.py --dry-run

# Full migration
python scripts/migrate_to_hierarchical_chunks.py

# Custom settings
python scripts/migrate_to_hierarchical_chunks.py \
  --parent-size 512 \
  --child-size 128 \
  --input data/products.json \
  --output data/hierarchical_chunks.json
```

**Version**: v10.5.0
**Created**: 2025-11-17
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.api.services.hierarchical_chunking_service import (
    HierarchicalChunkingService,
    ParentChunk,
    ChildChunk
)


class HierarchicalChunkMigrator:
    """
    Migrate existing flat chunks to hierarchical structure
    """

    def __init__(
        self,
        parent_chunk_size: int = 512,
        child_chunk_size: int = 128,
        dry_run: bool = False
    ):
        """
        Initialize migrator

        Args:
            parent_chunk_size: Target parent chunk size
            child_chunk_size: Target child chunk size
            dry_run: If True, only preview changes
        """
        self.service = HierarchicalChunkingService(
            parent_chunk_size=parent_chunk_size,
            child_chunk_size=child_chunk_size
        )
        self.dry_run = dry_run

        logger.info(
            f"HierarchicalChunkMigrator initialized: "
            f"parent={parent_chunk_size}, child={child_chunk_size}, dry_run={dry_run}"
        )

    async def load_products(self, input_path: str) -> List[Dict]:
        """
        Load products from JSON file

        Args:
            input_path: Path to products.json

        Returns:
            List of product dictionaries
        """
        logger.info(f"Loading products from: {input_path}")

        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                products = json.load(f)

            logger.info(f"Loaded {len(products)} products")
            return products

        except FileNotFoundError:
            logger.error(f"File not found: {input_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            return []

    def product_to_document(self, product: Dict) -> str:
        """
        Convert product dictionary to document text

        Args:
            product: Product dictionary

        Returns:
            Formatted document string
        """
        # Extract fields
        name = product.get('name', 'Unknown')
        capacity = product.get('capacity', '')
        material = product.get('material', '')
        color = product.get('color', '')
        usage = product.get('usage', '')
        price = product.get('price', '')
        moq = product.get('moq', '')
        description = product.get('description', '')

        # Format document
        doc = f"제품명: {name}\n\n"

        if capacity:
            doc += f"용량: {capacity}\n"
        if material:
            doc += f"재질: {material}\n"
        if color:
            doc += f"색상: {color}\n"
        if usage:
            doc += f"용도: {usage}\n\n"

        if price:
            doc += f"가격: {price}\n"
        if moq:
            doc += f"MOQ: {moq}\n\n"

        if description:
            doc += f"상세 설명:\n{description}\n"

        return doc.strip()

    async def migrate_product(
        self,
        product: Dict
    ) -> Dict:
        """
        Migrate a single product to hierarchical chunks

        Args:
            product: Product dictionary

        Returns:
            Migration result dictionary
        """
        product_id = product.get('id', product.get('name', 'unknown'))
        logger.info(f"Migrating product: {product_id}")

        # Convert to document
        document = self.product_to_document(product)

        # Create metadata
        metadata = {
            'product_id': product_id,
            'name': product.get('name', ''),
            'category': product.get('category', ''),
            'material': product.get('material', ''),
            'capacity': product.get('capacity', '')
        }

        # Create hierarchical chunks
        parents, children = await self.service.create_hierarchical_chunks(
            document,
            metadata=metadata
        )

        # Get statistics
        stats = self.service.get_statistics(parents, children)

        result = {
            'product_id': product_id,
            'original_length': len(document),
            'num_parents': len(parents),
            'num_children': len(children),
            'stats': stats,
            'parents': [
                {
                    'id': p.id,
                    'content': p.content,
                    'token_count': p.token_count,
                    'child_ids': p.child_ids,
                    'metadata': p.metadata
                }
                for p in parents
            ],
            'children': [
                {
                    'id': c.id,
                    'content': c.content,
                    'token_count': c.token_count,
                    'parent_id': c.parent_id,
                    'metadata': c.metadata
                }
                for c in children
            ]
        }

        return result

    async def migrate_all(
        self,
        input_path: str,
        output_path: str
    ) -> Dict:
        """
        Migrate all products

        Args:
            input_path: Path to input products.json
            output_path: Path to output hierarchical_chunks.json

        Returns:
            Migration summary statistics
        """
        # Load products
        products = await self.load_products(input_path)

        if not products:
            logger.error("No products to migrate")
            return {}

        # Migrate each product
        logger.info(f"Migrating {len(products)} products...")

        results = []
        total_parents = 0
        total_children = 0

        for i, product in enumerate(products, 1):
            logger.info(f"Progress: {i}/{len(products)}")

            result = await self.migrate_product(product)
            results.append(result)

            total_parents += result['num_parents']
            total_children += result['num_children']

        # Summary statistics
        summary = {
            'total_products': len(products),
            'total_parents': total_parents,
            'total_children': total_children,
            'avg_parents_per_product': round(total_parents / len(products), 2),
            'avg_children_per_product': round(total_children / len(products), 2),
            'avg_children_per_parent': round(total_children / total_parents, 2) if total_parents else 0,
            'products': results
        }

        # Save results
        if not self.dry_run:
            logger.info(f"Saving results to: {output_path}")

            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

            logger.info(f"Migration complete: {output_path}")
        else:
            logger.info("DRY RUN: No files written")

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total products: {summary['total_products']}")
        logger.info(f"Total parent chunks: {summary['total_parents']}")
        logger.info(f"Total child chunks: {summary['total_children']}")
        logger.info(f"Avg parents/product: {summary['avg_parents_per_product']}")
        logger.info(f"Avg children/product: {summary['avg_children_per_product']}")
        logger.info(f"Avg children/parent: {summary['avg_children_per_parent']}")
        logger.info("="*60)

        return summary


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Migrate flat chunks to hierarchical parent-child structure"
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/products.json',
        help='Input products JSON file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/hierarchical_chunks.json',
        help='Output hierarchical chunks JSON file'
    )
    parser.add_argument(
        '--parent-size',
        type=int,
        default=512,
        help='Parent chunk size in tokens (default: 512)'
    )
    parser.add_argument(
        '--child-size',
        type=int,
        default=128,
        help='Child chunk size in tokens (default: 128)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview migration without writing files'
    )

    args = parser.parse_args()

    logger.info("Starting hierarchical chunk migration...")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Parent size: {args.parent_size} tokens")
    logger.info(f"Child size: {args.child_size} tokens")
    logger.info(f"Dry run: {args.dry_run}")

    # Initialize migrator
    migrator = HierarchicalChunkMigrator(
        parent_chunk_size=args.parent_size,
        child_chunk_size=args.child_size,
        dry_run=args.dry_run
    )

    # Run migration
    summary = await migrator.migrate_all(args.input, args.output)

    if summary:
        logger.success("Migration completed successfully!")

        # Expected improvement metrics
        logger.info("\nEXPECTED IMPROVEMENTS (from RAG_ADVANCEMENT_PLAN.md):")
        logger.info("- Search precision: 0.88 → 0.92 (+4.5%)")
        logger.info("- Context completeness: +30%")
        logger.info("- Missing information: -40%")

        logger.info("\nNEXT STEPS:")
        logger.info("1. Create Qdrant collections: hierarchical_parents, hierarchical_children")
        logger.info("2. Generate embeddings for child chunks")
        logger.info("3. Store chunks in Qdrant with parent-child links")
        logger.info("4. Update search API to use hierarchical retrieval")
        logger.info("5. Run benchmarks to verify +4.5% precision improvement")
    else:
        logger.error("Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
