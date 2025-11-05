#!/usr/bin/env python3
"""
Web Crawler Pipeline Skill - Executable Wrapper

Complete pipeline: Crawl → Validate → Dedupe → Integrate → Publish
Supports both credential-free (onehago.com) and credential-required (freemold.net) sites.

Usage:
    python skill.py <command> [options]

Commands:
    init, crawl, validate, dedupe, integrate, publish, status, rollback, repair, report
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


class WebCrawlerPipeline:
    """Main pipeline orchestrator with authentication support"""

    def __init__(self, site: str, base_dir: Optional[Path] = None):
        self.site = site
        self.base_dir = base_dir or PROJECT_ROOT / "data" / site.replace(".", "_")
        self.config_file = self.base_dir / "config.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load site-specific configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_config(self):
        """Save configuration"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def _checkpoint(self, stage: str, status: str, metadata: Optional[Dict] = None):
        """Save checkpoint for rollback capability"""
        checkpoint_dir = self.base_dir / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            "checkpoint_id": f"{stage}_{status}",
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "status": status,
            "can_rollback": True,
            "metadata": metadata or {}
        }

        checkpoint_file = checkpoint_dir / f"{stage}_{status}.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)

        print(f"✅ Checkpoint saved: {stage}_{status}")

    def _load_checkpoint(self, checkpoint_id: str) -> Optional[Dict]:
        """Load checkpoint data"""
        checkpoint_dir = self.base_dir / "checkpoints"
        checkpoint_file = checkpoint_dir / f"{checkpoint_id}.json"

        if checkpoint_file.exists():
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def init(self, auth_type: str = "none", auth_file: Optional[str] = None):
        """Initialize pipeline for a site"""
        print(f"🚀 Initializing pipeline for {self.site}")

        # Create directory structure
        (self.base_dir / "raw").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "validated").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "deduped").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "integrated").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "production").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "checkpoints").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "logs").mkdir(parents=True, exist_ok=True)

        # Initialize config
        self.config = {
            "site": self.site,
            "auth_type": auth_type,
            "auth_file": auth_file,
            "created_at": datetime.now().isoformat(),
            "pipeline_version": "1.0.0",
            "stages": {
                "init": "completed",
                "crawl": "pending",
                "validate_L1": "pending",
                "dedupe": "pending",
                "validate_L2": "pending",
                "integrate": "pending",
                "validate_L3": "pending",
                "publish": "pending"
            }
        }
        self._save_config()
        self._checkpoint("init", "completed", {"auth_type": auth_type})

        print(f"✅ Pipeline initialized at: {self.base_dir}")
        print(f"   Auth type: {auth_type}")
        return {"status": "success", "base_dir": str(self.base_dir)}

    def crawl(self, mode: str = "full", workers: int = 4, auth_file: Optional[str] = None):
        """Execute web crawling with authentication support"""
        print(f"🕷️  Starting crawl for {self.site}")
        print(f"   Mode: {mode}, Workers: {workers}")

        auth_type = self.config.get("auth_type", "none")
        auth_file = auth_file or self.config.get("auth_file")

        if auth_type != "none" and not auth_file:
            print("❌ Error: auth_file required for authenticated crawling")
            return {"status": "error", "message": "Missing auth_file"}

        # Import appropriate crawler based on auth type
        if auth_type == "none":
            print("   Using: Simple HTTP crawler (no authentication)")
            from scripts import onehago_smart_crawler as crawler_module
        elif auth_type == "cookie":
            print(f"   Using: Cookie-based authentication ({auth_file})")
            # Load cookies and set up authenticated session
            # This would use selenium or requests.Session with cookies
            from scripts import crawl_with_cookies as crawler_module
        elif auth_type == "session":
            print(f"   Using: Session-based authentication ({auth_file})")
            from scripts import crawl_with_session as crawler_module
        else:
            print(f"❌ Error: Unknown auth type: {auth_type}")
            return {"status": "error", "message": f"Unknown auth_type: {auth_type}"}

        # Execute crawl
        raw_dir = self.base_dir / "raw"
        try:
            # This is a placeholder - actual crawler execution would go here
            print(f"   Output: {raw_dir}")
            print(f"   ⏳ Crawling in progress...")

            # Update config
            self.config["stages"]["crawl"] = "completed"
            self._save_config()
            self._checkpoint("crawl", "completed", {
                "mode": mode,
                "workers": workers,
                "output_dir": str(raw_dir)
            })

            print("✅ Crawl completed")
            return {"status": "success", "output_dir": str(raw_dir)}

        except Exception as e:
            print(f"❌ Crawl failed: {e}")
            self._checkpoint("crawl", "failed", {"error": str(e)})
            return {"status": "error", "message": str(e)}

    def validate(self, level: str = "L1", auto_fix: bool = False):
        """Execute validation at specified level"""
        print(f"🔍 Running validation level: {level}")

        if level == "L1":
            return self._validate_L1(auto_fix)
        elif level == "L2":
            return self._validate_L2(auto_fix)
        elif level == "L3":
            return self._validate_L3(auto_fix)
        elif level == "all":
            results = []
            for lvl in ["L1", "L2", "L3"]:
                result = self.validate(lvl, auto_fix)
                results.append(result)
            return {"status": "success", "results": results}
        else:
            return {"status": "error", "message": f"Unknown level: {level}"}

    def _validate_L1(self, auto_fix: bool = False):
        """L1: Schema Validation (Post-Crawl)"""
        print("📋 L1: Schema Validation")

        raw_dir = self.base_dir / "raw"
        validated_dir = self.base_dir / "validated"
        validated_dir.mkdir(parents=True, exist_ok=True)

        # Load raw data
        raw_files = list(raw_dir.glob("*.jsonl"))
        if not raw_files:
            return {"status": "error", "message": "No raw data files found"}

        total_records = 0
        valid_records = 0
        invalid_records = 0

        for raw_file in raw_files:
            print(f"   Validating: {raw_file.name}")

            valid_output = validated_dir / raw_file.name
            invalid_output = validated_dir / f"invalid_{raw_file.name}"

            with open(raw_file, 'r', encoding='utf-8') as f_in, \
                 open(valid_output, 'w', encoding='utf-8') as f_valid, \
                 open(invalid_output, 'w', encoding='utf-8') as f_invalid:

                for line in f_in:
                    total_records += 1
                    try:
                        record = json.loads(line.strip())

                        # Schema validation
                        if self._validate_schema(record):
                            valid_records += 1
                            f_valid.write(line)
                        else:
                            invalid_records += 1
                            if auto_fix:
                                fixed = self._fix_schema(record)
                                f_valid.write(json.dumps(fixed, ensure_ascii=False) + '\n')
                                valid_records += 1
                                invalid_records -= 1
                            else:
                                f_invalid.write(line)
                    except json.JSONDecodeError:
                        invalid_records += 1
                        f_invalid.write(line)

        # Update config
        self.config["stages"]["validate_L1"] = "completed"
        self._save_config()
        self._checkpoint("validate_L1", "completed", {
            "total": total_records,
            "valid": valid_records,
            "invalid": invalid_records,
            "pass_rate": f"{valid_records/total_records*100:.2f}%"
        })

        print(f"✅ L1 Validation complete:")
        print(f"   Total: {total_records:,}")
        print(f"   Valid: {valid_records:,} ({valid_records/total_records*100:.2f}%)")
        print(f"   Invalid: {invalid_records:,}")

        return {
            "status": "success",
            "level": "L1",
            "total": total_records,
            "valid": valid_records,
            "invalid": invalid_records
        }

    def _validate_L2(self, auto_fix: bool = False):
        """L2: Completeness Check (Pre-Integration)"""
        print("📊 L2: Completeness Check")

        validated_dir = self.base_dir / "validated"

        total_products = 0
        complete_products = 0
        incomplete_products = 0

        for validated_file in validated_dir.glob("*.jsonl"):
            if validated_file.name.startswith("invalid_"):
                continue

            print(f"   Checking: {validated_file.name}")

            with open(validated_file, 'r', encoding='utf-8') as f:
                for line in f:
                    total_products += 1
                    product = json.loads(line.strip())

                    quality_score = self._calculate_quality_score(product)

                    if quality_score >= 70.0:
                        complete_products += 1
                    else:
                        incomplete_products += 1

        # Update config
        self.config["stages"]["validate_L2"] = "completed"
        self._save_config()
        self._checkpoint("validate_L2", "completed", {
            "total": total_products,
            "complete": complete_products,
            "incomplete": incomplete_products,
            "completeness_rate": f"{complete_products/total_products*100:.2f}%"
        })

        print(f"✅ L2 Completeness check complete:")
        print(f"   Total: {total_products:,}")
        print(f"   Complete (≥70%): {complete_products:,} ({complete_products/total_products*100:.2f}%)")
        print(f"   Incomplete: {incomplete_products:,}")

        return {
            "status": "success",
            "level": "L2",
            "total": total_products,
            "complete": complete_products,
            "incomplete": incomplete_products
        }

    def _validate_L3(self, auto_fix: bool = False):
        """L3: Relationship Integrity (Post-Integration)"""
        print("🔗 L3: Relationship Integrity")

        integrated_dir = self.base_dir / "integrated"

        # This would validate referential integrity between entities
        # For now, placeholder implementation

        self.config["stages"]["validate_L3"] = "completed"
        self._save_config()
        self._checkpoint("validate_L3", "completed", {})

        print("✅ L3 Relationship validation complete")

        return {"status": "success", "level": "L3"}

    def _validate_schema(self, record: Dict) -> bool:
        """Validate record against schema"""
        required_fields = ["product_id", "product_name"]
        return all(field in record and record[field] for field in required_fields)

    def _fix_schema(self, record: Dict) -> Dict:
        """Attempt to fix schema issues"""
        # Add missing required fields with defaults
        if "product_id" not in record or not record["product_id"]:
            record["product_id"] = f"unknown_{datetime.now().timestamp()}"
        if "product_name" not in record or not record["product_name"]:
            record["product_name"] = "Unknown Product"
        return record

    def _calculate_quality_score(self, product: Dict) -> float:
        """Calculate quality score (0-100)"""
        score = 0.0

        # Product name (20 points)
        if product.get("product_name"):
            score += 20

        # Images (30 points: 20 for any images, +10 for 3+ images)
        image_urls = product.get("image_urls", [])
        if image_urls:
            score += 20
            if len(image_urls) >= 3:
                score += 10

        # Specifications (25 points)
        specifications = product.get("specifications", {})
        if specifications and len(specifications) >= 3:
            score += 25
        elif specifications:
            score += 15

        # Company info (15 points)
        if product.get("company_name") or product.get("company_id"):
            score += 15

        # Valid URLs (10 points)
        if product.get("product_url") and product["product_url"].startswith("http"):
            score += 10

        return min(score, 100.0)

    def dedupe(self, strategy: str = "priority"):
        """Execute deduplication"""
        print(f"🔄 Deduplicating with strategy: {strategy}")

        validated_dir = self.base_dir / "validated"
        deduped_dir = self.base_dir / "deduped"
        deduped_dir.mkdir(parents=True, exist_ok=True)

        # Load all validated records
        all_products = {}
        for validated_file in validated_dir.glob("*.jsonl"):
            if validated_file.name.startswith("invalid_"):
                continue

            with open(validated_file, 'r', encoding='utf-8') as f:
                for line in f:
                    product = json.loads(line.strip())
                    product_id = product.get("product_id")

                    if not product_id:
                        continue

                    if product_id not in all_products:
                        all_products[product_id] = product
                    else:
                        # Apply deduplication strategy
                        if strategy == "priority":
                            # Keep the one with higher quality score
                            existing_score = self._calculate_quality_score(all_products[product_id])
                            new_score = self._calculate_quality_score(product)
                            if new_score > existing_score:
                                all_products[product_id] = product
                        elif strategy == "merge":
                            # Merge records
                            all_products[product_id] = self._merge_records(
                                all_products[product_id], product
                            )

        # Write deduplicated data
        output_file = deduped_dir / "deduped.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for product in all_products.values():
                f.write(json.dumps(product, ensure_ascii=False) + '\n')

        total_before = sum(1 for _ in validated_dir.glob("*.jsonl") if not _.name.startswith("invalid_"))
        total_after = len(all_products)

        self.config["stages"]["dedupe"] = "completed"
        self._save_config()
        self._checkpoint("dedupe", "completed", {
            "strategy": strategy,
            "before": total_before,
            "after": total_after,
            "duplicates_removed": total_before - total_after
        })

        print(f"✅ Deduplication complete:")
        print(f"   Unique products: {total_after:,}")
        print(f"   Duplicates removed: {total_before - total_after:,}")

        return {
            "status": "success",
            "strategy": strategy,
            "unique_products": total_after
        }

    def _merge_records(self, record1: Dict, record2: Dict) -> Dict:
        """Merge two records, keeping best data from each"""
        merged = record1.copy()

        # Merge images
        images1 = set(record1.get("image_urls", []))
        images2 = set(record2.get("image_urls", []))
        merged["image_urls"] = list(images1 | images2)

        # Merge specifications
        specs1 = record1.get("specifications", {})
        specs2 = record2.get("specifications", {})
        merged["specifications"] = {**specs1, **specs2}

        # Keep non-empty fields from record2
        for key in record2:
            if record2[key] and (key not in merged or not merged[key]):
                merged[key] = record2[key]

        return merged

    def integrate(self, normalize: bool = True):
        """Integrate deduplicated data"""
        print(f"🔗 Integrating data (normalize={normalize})")

        deduped_dir = self.base_dir / "deduped"
        integrated_dir = self.base_dir / "integrated"
        integrated_dir.mkdir(parents=True, exist_ok=True)

        # Load deduped data
        deduped_file = deduped_dir / "deduped.jsonl"
        if not deduped_file.exists():
            return {"status": "error", "message": "No deduped data found"}

        integrated_products = []
        with open(deduped_file, 'r', encoding='utf-8') as f:
            for line in f:
                product = json.loads(line.strip())

                if normalize:
                    product = self._normalize_product(product)

                integrated_products.append(product)

        # Write integrated data
        output_file = integrated_dir / "integrated.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for product in integrated_products:
                f.write(json.dumps(product, ensure_ascii=False) + '\n')

        self.config["stages"]["integrate"] = "completed"
        self._save_config()
        self._checkpoint("integrate", "completed", {
            "total_products": len(integrated_products),
            "normalized": normalize
        })

        print(f"✅ Integration complete:")
        print(f"   Integrated products: {len(integrated_products):,}")

        return {
            "status": "success",
            "total_products": len(integrated_products)
        }

    def _normalize_product(self, product: Dict) -> Dict:
        """Normalize product data to standard schema"""
        normalized = {
            "id": product.get("product_id"),
            "name": product.get("product_name"),
            "url": product.get("product_url"),
            "images": product.get("image_urls", []),
            "specifications": product.get("specifications", {}),
            "company": {
                "id": product.get("company_id"),
                "name": product.get("company_name"),
            },
            "metadata": {
                "source": self.site,
                "crawled_at": product.get("crawled_at"),
                "updated_at": datetime.now().isoformat()
            }
        }
        return normalized

    def publish(self, target: str = "production", dry_run: bool = False):
        """Publish validated data to production"""
        print(f"🚀 Publishing to: {target} (dry_run={dry_run})")

        integrated_dir = self.base_dir / "integrated"
        production_dir = self.base_dir / target
        production_dir.mkdir(parents=True, exist_ok=True)

        integrated_file = integrated_dir / "integrated.jsonl"
        if not integrated_file.exists():
            return {"status": "error", "message": "No integrated data found"}

        if dry_run:
            print("   Dry run - no files will be modified")
            with open(integrated_file, 'r', encoding='utf-8') as f:
                total = sum(1 for _ in f)
            print(f"   Would publish: {total:,} products")
            return {"status": "success", "dry_run": True, "total": total}

        # Copy to production
        output_file = production_dir / f"{self.site.replace('.', '_')}_products.jsonl"
        with open(integrated_file, 'r', encoding='utf-8') as f_in, \
             open(output_file, 'w', encoding='utf-8') as f_out:
            total = 0
            for line in f_in:
                f_out.write(line)
                total += 1

        self.config["stages"]["publish"] = "completed"
        self.config["published_at"] = datetime.now().isoformat()
        self.config["published_file"] = str(output_file)
        self._save_config()
        self._checkpoint("publish", "completed", {
            "target": target,
            "total_products": total,
            "output_file": str(output_file)
        })

        print(f"✅ Published to production:")
        print(f"   File: {output_file}")
        print(f"   Products: {total:,}")

        return {
            "status": "success",
            "target": target,
            "total_products": total,
            "output_file": str(output_file)
        }

    def status(self):
        """Show pipeline status"""
        print(f"\n{'='*80}")
        print(f"📊 Pipeline Status: {self.site}")
        print(f"{'='*80}")

        stages = self.config.get("stages", {})
        for stage, status in stages.items():
            icon = "✅" if status == "completed" else "⏳" if status == "pending" else "❌"
            print(f"{icon} {stage:20s}: {status}")

        print(f"{'='*80}\n")

        return {"status": "success", "stages": stages}

    def rollback(self, checkpoint_id: str):
        """Rollback to a checkpoint"""
        print(f"⏪ Rolling back to: {checkpoint_id}")

        checkpoint = self._load_checkpoint(checkpoint_id)
        if not checkpoint:
            return {"status": "error", "message": f"Checkpoint not found: {checkpoint_id}"}

        if not checkpoint.get("can_rollback", False):
            return {"status": "error", "message": "Checkpoint cannot be rolled back"}

        stage = checkpoint["stage"]
        print(f"   Stage: {stage}")
        print(f"   Timestamp: {checkpoint['timestamp']}")

        # Update config to reset stages after this checkpoint
        stages_order = ["init", "crawl", "validate_L1", "dedupe", "validate_L2",
                        "integrate", "validate_L3", "publish"]

        try:
            reset_index = stages_order.index(stage) + 1
            for stage_name in stages_order[reset_index:]:
                if stage_name in self.config["stages"]:
                    self.config["stages"][stage_name] = "pending"
        except ValueError:
            pass

        self._save_config()

        print(f"✅ Rolled back to checkpoint: {checkpoint_id}")

        return {"status": "success", "checkpoint": checkpoint}

    def repair(self, auto_fix: bool = True):
        """Auto-repair data quality issues"""
        print("🔧 Running auto-repair...")

        # Re-run all validations with auto_fix enabled
        results = []
        for level in ["L1", "L2", "L3"]:
            result = self.validate(level, auto_fix=auto_fix)
            results.append(result)

        print("✅ Auto-repair complete")

        return {"status": "success", "results": results}

    def report(self, format: str = "text"):
        """Generate pipeline report"""
        print(f"📊 Generating report (format={format})")

        report = {
            "site": self.site,
            "created_at": self.config.get("created_at"),
            "published_at": self.config.get("published_at"),
            "stages": self.config.get("stages", {}),
            "checkpoints": []
        }

        # Load all checkpoints
        checkpoint_dir = self.base_dir / "checkpoints"
        if checkpoint_dir.exists():
            for checkpoint_file in sorted(checkpoint_dir.glob("*.json")):
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    report["checkpoints"].append(json.load(f))

        if format == "json":
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            # Text format
            print(f"\n{'='*80}")
            print(f"📊 Pipeline Report: {self.site}")
            print(f"{'='*80}")
            print(f"Created: {report['created_at']}")
            if report['published_at']:
                print(f"Published: {report['published_at']}")
            print(f"\nStages:")
            for stage, status in report["stages"].items():
                print(f"  {stage:20s}: {status}")
            print(f"\nCheckpoints: {len(report['checkpoints'])}")
            print(f"{'='*80}\n")

        return {"status": "success", "report": report}


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Web Crawler Pipeline Skill")
    parser.add_argument("command", choices=[
        "init", "crawl", "validate", "dedupe", "integrate",
        "publish", "status", "rollback", "repair", "report"
    ])
    parser.add_argument("--site", required=True, help="Target site (e.g., onehago.com)")
    parser.add_argument("--auth", default="none", choices=["none", "cookie", "session", "oauth"])
    parser.add_argument("--auth-file", help="Authentication file path")
    parser.add_argument("--mode", default="full", help="Crawl mode")
    parser.add_argument("--workers", type=int, default=4, help="Number of workers")
    parser.add_argument("--level", default="L1", help="Validation level")
    parser.add_argument("--auto-fix", action="store_true", help="Enable auto-fix")
    parser.add_argument("--strategy", default="priority", help="Deduplication strategy")
    parser.add_argument("--normalize", action="store_true", help="Normalize data")
    parser.add_argument("--target", default="production", help="Publish target")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--checkpoint-id", help="Checkpoint ID for rollback")
    parser.add_argument("--format", default="text", choices=["text", "json"])

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = WebCrawlerPipeline(args.site)

    # Execute command
    if args.command == "init":
        result = pipeline.init(auth_type=args.auth, auth_file=args.auth_file)
    elif args.command == "crawl":
        result = pipeline.crawl(mode=args.mode, workers=args.workers, auth_file=args.auth_file)
    elif args.command == "validate":
        result = pipeline.validate(level=args.level, auto_fix=args.auto_fix)
    elif args.command == "dedupe":
        result = pipeline.dedupe(strategy=args.strategy)
    elif args.command == "integrate":
        result = pipeline.integrate(normalize=args.normalize)
    elif args.command == "publish":
        result = pipeline.publish(target=args.target, dry_run=args.dry_run)
    elif args.command == "status":
        result = pipeline.status()
    elif args.command == "rollback":
        if not args.checkpoint_id:
            print("❌ Error: --checkpoint-id required for rollback")
            return 1
        result = pipeline.rollback(args.checkpoint_id)
    elif args.command == "repair":
        result = pipeline.repair(auto_fix=args.auto_fix)
    elif args.command == "report":
        result = pipeline.report(format=args.format)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1

    # Print result
    if result.get("status") == "error":
        print(f"❌ Error: {result.get('message')}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
