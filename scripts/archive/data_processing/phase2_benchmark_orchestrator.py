#!/usr/bin/env python3
"""
Phase 2 Benchmark Orchestrator - 15 Workers

Launches and manages 15 concurrent workers for benchmark validation crawling.
Monitors progress and handles worker lifecycle.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import time

# Configuration
TOTAL_WORKERS = 14
TOTAL_PRODUCTS = 22901  # From cleaned/all_products_clean.jsonl
PRODUCTS_PER_WORKER = (TOTAL_PRODUCTS + TOTAL_WORKERS - 1) // TOTAL_WORKERS  # ~1636 products per worker
WORKER_SCRIPT = Path(__file__).parent / 'phase2_benchmark_crawler_15workers.py'

def launch_worker(worker_id: int, start_index: int, end_index: int):
    """Launch a single worker process"""
    process = subprocess.Popen(
        ['python3', str(WORKER_SCRIPT), str(worker_id), str(start_index), str(end_index)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    return process

def print_banner():
    """Print startup banner"""
    print("="*80)
    print("🔍 PHASE 2 BENCHMARK ORCHESTRATOR - 14 WORKERS (TEXT-ONLY)")
    print("="*80)
    print()
    print("📊 Configuration:")
    print(f"   Total products: {TOTAL_PRODUCTS:,}")
    print(f"   Workers: {TOTAL_WORKERS}")
    print(f"   Products per worker: ~{PRODUCTS_PER_WORKER:,}")
    print(f"   Mode: Text-only extraction (no images)")
    print()
    print("🎯 Purpose: Validate existing packaging extraction quality")
    print("📈 Monitor: http://localhost:5555")
    print()
    print("⏱️  Estimated time: ~35-45 minutes with 14 workers")
    print("   (Based on ~1.5 seconds per product average)")
    print()
    print("="*80)
    print()

def main():
    print_banner()

    # Launch all workers
    workers = {}
    print(f"🚀 Launching {TOTAL_WORKERS} workers...")
    print()

    for worker_id in range(TOTAL_WORKERS):
        start_index = worker_id * PRODUCTS_PER_WORKER
        end_index = min((worker_id + 1) * PRODUCTS_PER_WORKER, TOTAL_PRODUCTS)
        products_count = end_index - start_index

        process = launch_worker(worker_id, start_index, end_index)
        workers[worker_id] = (process, start_index, end_index)

        print(f"✅ Worker {worker_id:02d}: Products {start_index:,}-{end_index:,} ({products_count:,} products)")

    print()
    print("="*80)
    print("🔄 ALL WORKERS LAUNCHED")
    print("="*80)
    print()
    print("📊 Monitor progress at: http://localhost:5555")
    print("📝 Worker logs: /tmp/benchmark_worker_*.log")
    print()
    print("⏳ Waiting for workers to complete...")
    print()

    # Monitor workers
    start_time = datetime.now()
    completed = 0
    failed = 0

    while workers:
        for worker_id in list(workers.keys()):
            process, start_idx, end_idx = workers[worker_id]

            # Check if process finished
            if process.poll() is not None:
                if process.returncode == 0:
                    print(f"✅ Worker {worker_id:02d} completed (products {start_idx:,}-{end_idx:,})")
                    completed += 1
                else:
                    print(f"❌ Worker {worker_id:02d} failed with exit code {process.returncode}")
                    failed += 1

                del workers[worker_id]

        time.sleep(1)  # Check every second

    # Final summary
    elapsed = (datetime.now() - start_time).total_seconds()

    print()
    print("="*80)
    print("✅ BENCHMARK CRAWLING COMPLETE")
    print("="*80)
    print()
    print("📊 Final Statistics:")
    print(f"   Workers completed: {completed}/{TOTAL_WORKERS}")
    print(f"   Workers failed: {failed}/{TOTAL_WORKERS}")
    print(f"   Total time: {elapsed/60:.1f} minutes ({elapsed/3600:.2f} hours)")
    if completed > 0:
        print(f"   Average time per worker: {elapsed/completed/60:.1f} minutes")
        print(f"   Overall rate: {TOTAL_PRODUCTS/elapsed*60:.0f} products/min")
    print()
    print("📁 Output directory: data/onehago/crawled/production/benchmark/")
    print("📊 View results at: http://localhost:5555")
    print()
    print("="*80)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Orchestrator interrupted. Workers may still be running in background.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Orchestrator error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
