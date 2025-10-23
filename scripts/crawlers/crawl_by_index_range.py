#!/usr/bin/env python3
"""
Index-Based Comprehensive Crawler
Crawls ALL products by idx (13-970) to ensure complete dataset

Usage:
    python scripts/crawlers/crawl_by_index_range.py
    python scripts/crawlers/crawl_by_index_range.py --start 13 --end 970
    python scripts/crawlers/crawl_by_index_range.py --resume
"""

import asyncio
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from chungjin_crawler import ChungjinCrawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawl_by_index.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class IndexRangeCrawler:
    """Index-based comprehensive crawler"""

    def __init__(self, output_dir: str, progress_file: str = "crawl_progress.json"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.progress_file = Path(progress_file)
        self.progress = self._load_progress()

        # Statistics
        self.stats = {
            "total_attempted": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }

    def _load_progress(self) -> dict:
        """Load crawl progress from file"""
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
            "started_at": None,
            "updated_at": None
        }

    def _save_progress(self, idx: int, success: bool):
        """Save progress after each crawl"""
        if success:
            if idx not in self.progress["successful_idx"]:
                self.progress["successful_idx"].append(idx)
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

    async def crawl_index_range(
        self,
        start_idx: int,
        end_idx: int,
        delay: float = 2.0,
        resume: bool = False
    ):
        """Crawl all products in index range"""

        start_time = datetime.now()

        logger.info("="*80)
        logger.info("Index-Based Comprehensive Crawl")
        logger.info("="*80)
        logger.info(f"Range: idx {start_idx} → {end_idx}")
        logger.info(f"Total indices: {end_idx - start_idx + 1}")
        logger.info(f"Delay: {delay}s per request")
        logger.info(f"Resume mode: {resume}")
        logger.info(f"Output: {self.output_dir}")
        logger.info("="*80)

        # Determine starting point
        if resume and self.progress["last_crawled_idx"] > 0:
            start_idx = self.progress["last_crawled_idx"] + 1
            logger.info(f"📍 Resuming from idx {start_idx}")

        # Initialize crawler
        crawler = ChungjinCrawler(
            output_dir=str(self.output_dir),
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

                # Check if product exists (not 404 or empty)
                if self._is_valid_product(product_data):
                    # Save product JSON
                    json_path = self.output_dir / f"idx_{idx}.json"
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(product_data, f, ensure_ascii=False, indent=2)

                    logger.info(f"✅ idx {idx}: {product_data.get('product_name', 'Unknown')}")
                    self.stats["successful"] += 1
                    self._save_progress(idx, success=True)
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

                # Continue with next idx
                await asyncio.sleep(delay)

        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time

        await self._print_final_summary(start_time, end_time, duration)

        # Close crawler
        await crawler.automation.close_browser()

        return self.stats

    def _is_valid_product(self, product_data: dict) -> bool:
        """Check if product data is valid (not 404 or empty)"""
        if not product_data:
            return False

        # Must have product name
        if not product_data.get('product_name') or product_data['product_name'] == 'Unknown Product':
            return False

        # Should have some specifications or images
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
        logger.info("="*60)

    async def _print_final_summary(self, start_time, end_time, duration):
        """Print final crawl summary"""
        total = self.stats["total_attempted"]
        success = self.stats["successful"]
        failed = self.stats["failed"]
        skipped = self.stats["skipped"]

        logger.info("\n" + "="*80)
        logger.info("✅ CRAWL COMPLETE!")
        logger.info("="*80)
        logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration}")
        logger.info("")
        logger.info(f"Total attempted: {total}")
        logger.info(f"Successful: {success} ({success/total*100:.1f}%)")
        logger.info(f"Failed (404/invalid): {failed} ({failed/total*100:.1f}%)")
        logger.info(f"Skipped (already crawled): {skipped}")
        logger.info("")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"JSON files created: {success}")
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

        report_path = self.output_dir / "crawl_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"\n📄 Report saved: {report_path}")

        # Print sample errors if any
        if self.stats["errors"]:
            logger.info("\n⚠️  Sample Errors (first 5):")
            for error in self.stats["errors"][:5]:
                logger.info(f"  idx {error['idx']}: {error['error']}")


async def main():
    """Main execution function"""

    parser = argparse.ArgumentParser(description="Index-based product crawler")
    parser.add_argument("--start", type=int, default=13, help="Start index (default: 13)")
    parser.add_argument("--end", type=int, default=970, help="End index (default: 970)")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests in seconds (default: 2.0)")
    parser.add_argument("--resume", action="store_true", help="Resume from last crawled index")
    parser.add_argument("--output", type=str, default="data/crawled_products_complete", help="Output directory")

    args = parser.parse_args()

    print("\n" + "="*80)
    print("Chungjin Korea - Comprehensive Index Crawler")
    print("="*80)
    print(f"Index range: {args.start} → {args.end} ({args.end - args.start + 1} indices)")
    print(f"Delay: {args.delay}s per request")
    print(f"Resume: {args.resume}")
    print(f"Output: {args.output}")
    print(f"Estimated time: {(args.end - args.start + 1) * args.delay / 60:.1f} minutes")
    print("="*80)

    # Confirmation
    if not args.resume:
        response = input("\nStart crawling? (y/n): ")
        if response.lower() != 'y':
            print("Crawl cancelled.")
            return

    # Execute crawl
    crawler = IndexRangeCrawler(output_dir=args.output)

    try:
        stats = await crawler.crawl_index_range(
            start_idx=args.start,
            end_idx=args.end,
            delay=args.delay,
            resume=args.resume
        )

        print("\n✅ Crawl completed successfully!")
        print(f"   Successful products: {stats['successful']}")
        print(f"   Failed indices: {stats['failed']}")
        print(f"   Output: {args.output}")

    except KeyboardInterrupt:
        print("\n\n⏸️  Crawl interrupted by user.")
        print(f"   Progress saved. Use --resume to continue.")
    except Exception as e:
        logger.error(f"Crawl failed: {e}", exc_info=True)
        print(f"\n❌ Crawl failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
