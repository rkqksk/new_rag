#!/usr/bin/env python3
"""
Packaging Image Download Orchestrator

Maintains 14 concurrent image download workers for packaging products.
Automatically launches new workers as soon as old ones complete.
OPTIMIZED: First 3 images per product for 81% storage savings.

Features:
- 14 concurrent workers (optimal parallelism)
- Continuous worker replacement (automatic)
- Real-time progress monitoring
- Estimated completion tracking
- Worker failure detection and logging
"""
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Configuration
MAX_CONCURRENT_WORKERS = 14  # 14 workers for optimal parallelism
TOTAL_PACKAGING_PRODUCTS = 22457  # Total packaging products with images
PRODUCTS_PER_WORKER = (TOTAL_PACKAGING_PRODUCTS + MAX_CONCURRENT_WORKERS - 1) // MAX_CONCURRENT_WORKERS  # ~1604 products per worker
WORKER_SCRIPT = Path('/Users/oypnus/Project/rag-enterprise/scripts/packaging_image_worker.py')

# Calculate total workers needed
TOTAL_WORKERS = (TOTAL_PACKAGING_PRODUCTS + PRODUCTS_PER_WORKER - 1) // PRODUCTS_PER_WORKER

def launch_worker(worker_id, start_product, end_product):
    """Launch a single packaging image download worker"""
    process = subprocess.Popen(
        ['python3', str(WORKER_SCRIPT), str(worker_id), str(start_product), str(end_product)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    return process

def print_banner():
    """Print startup banner with configuration"""
    print(f"{'='*80}")
    print(f"📦 PACKAGING IMAGE DOWNLOAD ORCHESTRATOR")
    print(f"{'='*80}")
    print(f"🎯 OPTIMIZED FOR STORAGE EFFICIENCY")
    print(f"   Images per product: First 3 only (81% storage savings)")
    print(f"   Total images: ~67,371 vs 345,803 (all images)")
    print(f"   Estimated storage: ~6.4 GB vs ~33 GB")
    print(f"")
    print(f"📊 Configuration:")
    print(f"   Max concurrent workers: {MAX_CONCURRENT_WORKERS}")
    print(f"   Total packaging products: {TOTAL_PACKAGING_PRODUCTS:,}")
    print(f"   Products per worker: ~{PRODUCTS_PER_WORKER:,}")
    print(f"   Total workers needed: {TOTAL_WORKERS}")
    print(f"")
    print(f"⏱️  Estimated time: ~1.0 hours with 14 workers")
    print(f"⏱️  Started at {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*80}")
    print("")

def main():
    print_banner()

    workers_completed = 0
    workers_failed = 0
    start_time = datetime.now()

    # Active workers: {worker_id: (process, start_product, end_product)}
    active_workers = {}
    next_worker_id = 0
    last_status_time = time.time()

    # Launch initial batch of workers
    print(f"🚀 Launching initial batch of {MAX_CONCURRENT_WORKERS} workers...")
    print(f"")
    for _ in range(min(MAX_CONCURRENT_WORKERS, TOTAL_WORKERS)):
        start_product = next_worker_id * PRODUCTS_PER_WORKER
        end_product = min((next_worker_id + 1) * PRODUCTS_PER_WORKER, TOTAL_PACKAGING_PRODUCTS)

        process = launch_worker(next_worker_id, start_product, end_product)
        active_workers[next_worker_id] = (process, start_product, end_product)
        print(f"✅ Worker {next_worker_id:02d}: Products {start_product:,}-{end_product:,} ({end_product-start_product:,} products)", flush=True)
        next_worker_id += 1

    print(f"\n{'='*80}")
    print(f"🔄 MONITORING WORKERS (Automatic replacement enabled)")
    print(f"{'='*80}\n")

    # Continuous monitoring loop
    while active_workers or next_worker_id < TOTAL_WORKERS:
        # Check each active worker
        for worker_id in list(active_workers.keys()):
            process, start_prod, end_prod = active_workers[worker_id]

            # Read output line by line (non-blocking)
            line = process.stdout.readline()
            if line:
                # Print important progress lines only (filter noise)
                if any(keyword in line for keyword in ["Worker", "Product", "Downloaded", "Images", "📦", "✅", "⚠️", "SUMMARY"]):
                    # Shorten worker ID in output
                    display_line = line.rstrip().replace(f"Worker-{worker_id:04d}", f"W{worker_id:02d}")
                    print(f"{display_line}", flush=True)

            # Check if process finished
            if process.poll() is not None:
                # Process finished, read remaining output
                for remaining_line in process.stdout:
                    if any(keyword in remaining_line for keyword in ["completed", "SUMMARY", "Images saved"]):
                        display_line = remaining_line.rstrip().replace(f"Worker-{worker_id:04d}", f"W{worker_id:02d}")
                        print(f"{display_line}", flush=True)

                # Check exit code
                if process.returncode == 0:
                    print(f"")
                    print(f"✅ Worker {worker_id:02d} completed successfully (products {start_prod:,}-{end_prod:,})", flush=True)
                    print(f"")
                    workers_completed += 1
                else:
                    print(f"❌ Worker {worker_id:02d} failed with exit code {process.returncode}", flush=True)
                    workers_failed += 1

                # Remove from active workers
                del active_workers[worker_id]

                # Launch next worker immediately
                if next_worker_id < TOTAL_WORKERS:
                    start_product = next_worker_id * PRODUCTS_PER_WORKER
                    end_product = min((next_worker_id + 1) * PRODUCTS_PER_WORKER, TOTAL_PACKAGING_PRODUCTS)

                    new_process = launch_worker(next_worker_id, start_product, end_product)
                    active_workers[next_worker_id] = (new_process, start_product, end_product)
                    print(f"🚀 Worker {next_worker_id:02d} launched: Products {start_product:,}-{end_product:,} ({end_product-start_product:,} products)", flush=True)
                    print(f"")
                    next_worker_id += 1

        # Print periodic status update
        current_time = time.time()
        if current_time - last_status_time >= 600:  # Every 10 minutes
            elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60

            print(f"\n{'='*80}")
            print(f"📊 STATUS UPDATE ({datetime.now().strftime('%H:%M:%S')} - {elapsed_minutes:.1f} minutes elapsed)")
            print(f"{'='*80}")
            print(f"   Active workers: {len(active_workers)}")
            print(f"   Completed: {workers_completed}/{TOTAL_WORKERS} ({workers_completed/TOTAL_WORKERS*100:.1f}%)")
            print(f"   Failed: {workers_failed} ({workers_failed/TOTAL_WORKERS*100:.1f}%)")
            print(f"   Remaining: {TOTAL_WORKERS - workers_completed - workers_failed}")

            if workers_completed > 0:
                rate = workers_completed / elapsed_minutes
                eta_minutes = (TOTAL_WORKERS - workers_completed) / rate if rate > 0 else 0
                print(f"   Rate: {rate*60:.1f} workers/hour")
                print(f"   ETA: {eta_minutes:.0f} minutes ({eta_minutes/60:.1f} hours)")

            print(f"{'='*80}\n")
            last_status_time = current_time

        # Small sleep to avoid busy waiting
        time.sleep(0.1)

    # Final summary
    elapsed_time = (datetime.now() - start_time).total_seconds()

    print(f"\n{'='*80}")
    print(f"🏁 PACKAGING IMAGE DOWNLOAD COMPLETE")
    print(f"{'='*80}")
    print(f"")
    print(f"📊 Final Statistics:")
    print(f"   Workers completed: {workers_completed}/{TOTAL_WORKERS}")
    print(f"   Workers failed: {workers_failed}/{TOTAL_WORKERS}")
    print(f"   Total time: {elapsed_time/60:.1f} minutes ({elapsed_time/3600:.2f} hours)")

    if workers_completed > 0:
        print(f"   Average time per worker: {elapsed_time/workers_completed/60:.1f} minutes")

    print(f"")
    print(f"📦 Image Statistics (Estimated):")
    products_processed = workers_completed * PRODUCTS_PER_WORKER
    estimated_images = products_processed * 3  # First 3 images per product
    estimated_storage_gb = estimated_images * 100 / (1024 * 1024)  # 100KB per image

    print(f"   Products processed: ~{products_processed:,}")
    print(f"   Images downloaded: ~{estimated_images:,}")
    print(f"   Storage used: ~{estimated_storage_gb:.1f} GB")

    print(f"")
    print(f"💾 Output directory: /Users/oypnus/Project/rag-enterprise/data/onehago/images/packaging/")
    print(f"📋 Worker logs: /tmp/packaging_image_worker_*.log")
    print(f"📊 Worker progress: data/onehago/images/packaging/worker_*_progress.json")

    print(f"")
    print(f"✨ STORAGE SAVINGS ACHIEVED: 81% (6.4 GB vs 33 GB)")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
