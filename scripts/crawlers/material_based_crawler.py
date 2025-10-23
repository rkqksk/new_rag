#!/usr/bin/env python3
"""
Material-Based Comprehensive Crawler
Crawls ALL products (idx 13-970) and organizes by MATERIAL (PE, PET, PETG, PP, Other)

Output Structure:
    data/crawled_products_final/
    ├── PE/products/
    ├── PET/products/
    ├── PETG/products/
    ├── PP/products/
    └── Other/products/

Usage:
    python scripts/crawlers/material_based_crawler.py
    python scripts/crawlers/material_based_crawler.py --resume
"""

import asyncio
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
import sys
import re

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from chungjin_crawler import ChungjinCrawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('material_based_crawl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MaterialBasedCrawler:
    """Material-based comprehensive crawler and organizer"""

    def __init__(self, base_dir: str, progress_file: str = "material_crawl_progress.json"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Material categories
        self.materials = ["PE", "PET", "PETG", "PP", "Other"]

        # Create material directories
        for material in self.materials:
            (self.base_dir / material / "products").mkdir(parents=True, exist_ok=True)
            (self.base_dir / material / "images").mkdir(parents=True, exist_ok=True)
            (self.base_dir / material / "print_area").mkdir(parents=True, exist_ok=True)

        self.progress_file = Path(progress_file)
        self.progress = self._load_progress()

        # Statistics by material
        self.stats = {
            "total_attempted": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "by_material": {material: 0 for material in self.materials},
            "errors": []
        }

    def _load_progress(self) -> dict:
        """Load crawl progress"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                logger.info(f"✓ Loaded progress: last_idx={progress.get('last_crawled_idx', 0)}")
                return progress
            except Exception as e:
                logger.warning(f"Failed to load progress: {e}")

        return {
            "last_crawled_idx": 0,
            "successful_idx": [],
            "failed_idx": [],
            "by_material": {material: [] for material in self.materials},
            "started_at": None,
            "updated_at": None
        }

    def _save_progress(self, idx: int, success: bool, material: str = None):
        """Save progress after each crawl"""
        if success:
            if idx not in self.progress["successful_idx"]:
                self.progress["successful_idx"].append(idx)
            if material and material in self.materials:
                if idx not in self.progress["by_material"][material]:
                    self.progress["by_material"][material].append(idx)
        else:
            if idx not in self.progress["failed_idx"]:
                self.progress["failed_idx"].append(idx)

        self.progress["last_crawled_idx"] = idx
        self.progress["updated_at"] = datetime.now().isoformat()

        if not self.progress["started_at"]:
            self.progress["started_at"] = datetime.now().isoformat()

        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save progress: {e}")

    def _extract_material(self, product_data: dict) -> str:
        """
        Extract material from product specifications

        Returns: 'PE', 'PET', 'PETG', 'PP', or 'Other'
        """
        specs = product_data.get("specifications", {})

        # Check for material field
        material_value = None
        for key, value in specs.items():
            if '재질' in key or 'Material' in key.lower() or '원료' in key:
                material_value = str(value).upper()
                break

        if not material_value:
            logger.debug(f"No material found in specs: {specs}")
            return "Other"

        # Extract material type
        if 'PETG' in material_value:
            return "PETG"
        elif 'PET' in material_value:
            return "PET"
        elif 'PE' in material_value:
            return "PE"
        elif 'PP' in material_value:
            return "PP"
        else:
            logger.debug(f"Unknown material: {material_value}")
            return "Other"

    def _get_material_path(self, material: str) -> Path:
        """Get path for specific material"""
        if material not in self.materials:
            material = "Other"
        return self.base_dir / material

    async def crawl_and_organize(
        self,
        start_idx: int,
        end_idx: int,
        delay: float = 2.0,
        resume: bool = False
    ):
        """Crawl all products and organize by material"""

        start_time = datetime.now()

        logger.info("="*80)
        logger.info("Material-Based Comprehensive Crawl")
        logger.info("="*80)
        logger.info(f"Range: idx {start_idx} → {end_idx}")
        logger.info(f"Total indices: {end_idx - start_idx + 1}")
        logger.info(f"Materials: {', '.join(self.materials)}")
        logger.info(f"Output: {self.base_dir}")
        logger.info(f"Delay: {delay}s per request")
        logger.info(f"Resume mode: {resume}")
        logger.info("="*80)

        # Determine starting point
        if resume and self.progress["last_crawled_idx"] > 0:
            start_idx = self.progress["last_crawled_idx"] + 1
            logger.info(f"📍 Resuming from idx {start_idx}")

        # Initialize crawler (temporary output dir)
        temp_output = self.base_dir / "temp_crawl"
        temp_output.mkdir(exist_ok=True)

        crawler = ChungjinCrawler(
            output_dir=str(temp_output),
            browser_type="webkit",
            use_playwright=False
        )

        # Crawl each index
        for idx in range(start_idx, end_idx + 1):
            self.stats["total_attempted"] += 1

            # Check if already crawled successfully
            if idx in self.progress["successful_idx"]:
                logger.info(f"⏭️  Skipping idx {idx} (already crawled)")
                self.stats["skipped"] += 1
                continue

            url = f"http://chungjinkorea.com/kr/product/view.php?idx={idx}"

            try:
                logger.info(f"\n[{self.stats['total_attempted']}/{end_idx - start_idx + 1}] Crawling idx {idx}...")

                # Crawl product
                product_data = await crawler.crawl_product(url)

                # Check if valid product
                if self._is_valid_product(product_data):
                    # Extract material
                    material = self._extract_material(product_data)

                    # Get material-specific directory
                    material_dir = self._get_material_path(material)

                    # Save product JSON to material folder
                    json_path = material_dir / "products" / f"idx_{idx}.json"
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(product_data, f, ensure_ascii=False, indent=2)

                    # Move images to material folder if downloaded
                    if product_data.get("downloaded_images"):
                        await self._move_images(product_data, idx, material_dir, temp_output)

                    # Move print area PDF if downloaded
                    if product_data.get("print_area_local_path"):
                        await self._move_print_area(product_data, idx, material_dir, temp_output)

                    logger.info(f"✅ idx {idx}: {product_data.get('product_name', 'Unknown')} → {material}")

                    self.stats["successful"] += 1
                    self.stats["by_material"][material] += 1
                    self._save_progress(idx, success=True, material=material)
                else:
                    logger.warning(f"⚠️  idx {idx}: Product not found or invalid")
                    self.stats["failed"] += 1
                    self._save_progress(idx, success=False)

                # Rate limiting
                if idx < end_idx:
                    await asyncio.sleep(delay)

                # Progress update every 50 products
                if self.stats["total_attempted"] % 50 == 0:
                    self._print_progress_summary()

            except Exception as e:
                logger.error(f"❌ idx {idx}: Error - {str(e)}")
                self.stats["failed"] += 1
                self.stats["errors"].append({
                    "idx": idx,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                self._save_progress(idx, success=False)
                await asyncio.sleep(delay)

        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time

        await self._print_final_summary(start_time, end_time, duration)

        # Close crawler
        await crawler.automation.close_browser()

        # Clean up temp directory
        import shutil
        if temp_output.exists():
            shutil.rmtree(temp_output)
            logger.info(f"🗑️  Cleaned up temp directory")

        return self.stats

    async def _move_images(self, product_data: dict, idx: int, material_dir: Path, temp_dir: Path):
        """Move downloaded images to material-specific folder"""
        for img_info in product_data.get("downloaded_images", []):
            if "local_path" in img_info:
                src_path = Path(img_info["local_path"])
                if src_path.exists():
                    # Create new filename: idx_13_main_1.jpg
                    filename = f"idx_{idx}_{img_info['type']}_{src_path.name}"
                    dst_path = material_dir / "images" / filename

                    try:
                        import shutil
                        shutil.copy2(src_path, dst_path)
                        img_info["local_path"] = str(dst_path)
                    except Exception as e:
                        logger.warning(f"Failed to move image: {e}")

    async def _move_print_area(self, product_data: dict, idx: int, material_dir: Path, temp_dir: Path):
        """Move print area PDF to material-specific folder"""
        src_path = Path(product_data["print_area_local_path"])
        if src_path.exists():
            filename = f"idx_{idx}_print_area.pdf"
            dst_path = material_dir / "print_area" / filename

            try:
                import shutil
                shutil.copy2(src_path, dst_path)
                product_data["print_area_local_path"] = str(dst_path)
            except Exception as e:
                logger.warning(f"Failed to move print area PDF: {e}")

    def _is_valid_product(self, product_data: dict) -> bool:
        """Check if product data is valid"""
        if not product_data:
            return False
        if not product_data.get('product_name') or product_data['product_name'] == 'Unknown Product':
            return False
        if not product_data.get('specifications') and not product_data.get('images'):
            return False
        return True

    def _print_progress_summary(self):
        """Print progress summary"""
        total = self.stats["total_attempted"]
        success = self.stats["successful"]
        failed = self.stats["failed"]
        skipped = self.stats["skipped"]

        logger.info("\n" + "="*60)
        logger.info("📊 Progress Update")
        logger.info("="*60)
        logger.info(f"Attempted: {total}")
        logger.info(f"Successful: {success} ({success/total*100:.1f}%)")
        logger.info(f"Failed: {failed} ({failed/total*100:.1f}%)")
        logger.info(f"Skipped: {skipped}")
        logger.info("\nBy Material:")
        for material in self.materials:
            count = self.stats["by_material"][material]
            if count > 0:
                logger.info(f"  {material}: {count} products")
        logger.info("="*60)

    async def _print_final_summary(self, start_time, end_time, duration):
        """Print final crawl summary"""
        total = self.stats["total_attempted"]
        success = self.stats["successful"]
        failed = self.stats["failed"]
        skipped = self.stats["skipped"]

        logger.info("\n" + "="*80)
        logger.info("✅ MATERIAL-BASED CRAWL COMPLETE!")
        logger.info("="*80)
        logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration}")
        logger.info("")
        logger.info(f"Total attempted: {total}")
        logger.info(f"Successful: {success} ({success/total*100:.1f}%)")
        logger.info(f"Failed (404/invalid): {failed} ({failed/total*100:.1f}%)")
        logger.info(f"Skipped: {skipped}")
        logger.info("")
        logger.info("Products by Material:")
        for material in self.materials:
            count = self.stats["by_material"][material]
            logger.info(f"  {material}: {count} products")
        logger.info("")
        logger.info(f"Output directory: {self.base_dir}")
        logger.info("="*80)

        # Save final report
        report = {
            "crawl_info": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration.total_seconds(),
                "duration_formatted": str(duration)
            },
            "statistics": self.stats,
            "progress": self.progress
        }

        report_path = self.base_dir / "material_crawl_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"\n📄 Report saved: {report_path}")


async def main():
    """Main execution function"""

    parser = argparse.ArgumentParser(description="Material-based product crawler")
    parser.add_argument("--start", type=int, default=13, help="Start index (default: 13)")
    parser.add_argument("--end", type=int, default=970, help="End index (default: 970)")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests (default: 2.0s)")
    parser.add_argument("--resume", action="store_true", help="Resume from last crawled index")
    parser.add_argument("--output", type=str, default="data/crawled_products_final", help="Output directory")

    args = parser.parse_args()

    print("\n" + "="*80)
    print("Chungjin Korea - Material-Based Comprehensive Crawler")
    print("="*80)
    print(f"Index range: {args.start} → {args.end} ({args.end - args.start + 1} indices)")
    print(f"Materials: PE, PET, PETG, PP, Other")
    print(f"Delay: {args.delay}s per request")
    print(f"Resume: {args.resume}")
    print(f"Output: {args.output}")
    print(f"Estimated time: {(args.end - args.start + 1) * args.delay / 60:.1f} minutes")
    print("="*80)

    # Confirmation
    if not args.resume:
        response = input("\n⚠️  This will crawl ALL products and organize by material. Continue? (y/n): ")
        if response.lower() != 'y':
            print("Crawl cancelled.")
            return

    # Execute crawl
    crawler = MaterialBasedCrawler(base_dir=args.output)

    try:
        stats = await crawler.crawl_and_organize(
            start_idx=args.start,
            end_idx=args.end,
            delay=args.delay,
            resume=args.resume
        )

        print("\n" + "="*80)
        print("✅ Material-Based Crawl Completed!")
        print("="*80)
        print(f"Successful products: {stats['successful']}")
        print(f"Failed indices: {stats['failed']}")
        print("\nProducts by Material:")
        for material, count in stats['by_material'].items():
            if count > 0:
                print(f"  {material}: {count} products")
        print(f"\nOutput: {args.output}")
        print("="*80)

    except KeyboardInterrupt:
        print("\n\n⏸️  Crawl interrupted by user.")
        print(f"   Progress saved. Use --resume to continue.")
    except Exception as e:
        logger.error(f"Crawl failed: {e}", exc_info=True)
        print(f"\n❌ Crawl failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
