#!/usr/bin/env python3
"""
Onehago Image Download Orchestrator
Maintains multiple concurrent image download workers
Automatically launches new workers as soon as old ones complete
"""
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Configuration
MAX_CONCURRENT_WORKERS = 10  # Maximum concurrent workers
TOTAL_CATEGORY2_PRODUCTS = 136062  # Total category 2 products to download
PRODUCTS_PER_WORKER = 5000  # Each worker handles 5000 products
WORKER_SCRIPT = Path('/Users/oypnus/Project/rag-enterprise/scripts/onehago_image_worker.py')

# Calculate total workers needed
TOTAL_WORKERS = (TOTAL_CATEGORY2_PRODUCTS + PRODUCTS_PER_WORKER - 1) // PRODUCTS_PER_WORKER  # Ceiling division

def launch_worker(worker_id, start_product, end_product):
    """Launch a single image download worker"""
    process = subprocess.Popen(
        ['python3', str(WORKER_SCRIPT), str(worker_id), str(start_product), str(end_product)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    return process

def main():
    print(f"{'='*80}")
    print(f"🖼️  ONEHAGO IMAGE DOWNLOAD ORCHESTRATOR")
    print(f"{'='*80}")
    print(f"📊 Configuration:")
    print(f"   Max concurrent workers: {MAX_CONCURRENT_WORKERS}")
    print(f"   Total category 2 products: {TOTAL_CATEGORY2_PRODUCTS:,}")
    print(f"   Products per worker: {PRODUCTS_PER_WORKER:,}")
    print(f"   Total workers needed: {TOTAL_WORKERS}")
    print(f"⏱️  Started at {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*80}")
    print("")

    workers_completed = 0
    workers_failed = 0
    start_time = datetime.now()

    # Active workers: {worker_id: (process, start_product, end_product)}
    active_workers = {}
    next_worker_id = 0
    last_status_time = time.time()

    # Launch initial batch of workers
    print(f"🚀 Launching initial batch of {MAX_CONCURRENT_WORKERS} workers...")
    for _ in range(min(MAX_CONCURRENT_WORKERS, TOTAL_WORKERS)):
        start_product = next_worker_id * PRODUCTS_PER_WORKER
        end_product = min((next_worker_id + 1) * PRODUCTS_PER_WORKER, TOTAL_CATEGORY2_PRODUCTS)

        process = launch_worker(next_worker_id, start_product, end_product)
        active_workers[next_worker_id] = (process, start_product, end_product)
        print(f"✅ Launched worker {next_worker_id} (products {start_product}-{end_product})", flush=True)
        next_worker_id += 1

    print(f"\n🔄 Monitoring workers and launching new ones as they complete...")
    print(f"{'='*80}\n")

    # Continuous monitoring loop
    while active_workers or next_worker_id < TOTAL_WORKERS:
        # Check each active worker
        for worker_id in list(active_workers.keys()):
            process, start_prod, end_prod = active_workers[worker_id]

            # Read output line by line (non-blocking)
            line = process.stdout.readline()
            if line:
                # Print progress lines
                if any(keyword in line for keyword in ["Worker", "Product", "Downloaded", "Images"]):
                    print(f"[W{worker_id}] {line.rstrip()}", flush=True)

            # Check if process finished
            if process.poll() is not None:
                # Process finished, read remaining output
                for remaining_line in process.stdout:
                    if any(keyword in remaining_line for keyword in ["Worker", "completed", "SUMMARY"]):
                        print(f"[W{worker_id}] {remaining_line.rstrip()}", flush=True)

                # Check exit code
                if process.returncode == 0:
                    print(f"✅ Worker {worker_id} completed successfully", flush=True)
                    workers_completed += 1
                else:
                    print(f"❌ Worker {worker_id} failed with exit code {process.returncode}", flush=True)
                    workers_failed += 1

                # Remove from active workers
                del active_workers[worker_id]

                # Launch next worker immediately
                if next_worker_id < TOTAL_WORKERS:
                    start_product = next_worker_id * PRODUCTS_PER_WORKER
                    end_product = min((next_worker_id + 1) * PRODUCTS_PER_WORKER, TOTAL_CATEGORY2_PRODUCTS)

                    new_process = launch_worker(next_worker_id, start_product, end_product)
                    active_workers[next_worker_id] = (new_process, start_product, end_product)
                    print(f"🚀 Launched worker {next_worker_id} (products {start_product}-{end_product})", flush=True)
                    next_worker_id += 1

        # Print periodic status update
        current_time = time.time()
        if current_time - last_status_time >= 900:  # Every 15 minutes
            print(f"\n{'='*80}")
            print(f"📊 STATUS UPDATE ({datetime.now().strftime('%H:%M:%S')})")
            print(f"{'='*80}")
            print(f"   Active workers: {len(active_workers)}")
            print(f"   Completed: {workers_completed} ({workers_completed/TOTAL_WORKERS*100:.1f}%)")
            print(f"   Failed: {workers_failed} ({workers_failed/TOTAL_WORKERS*100:.1f}%)")
            print(f"   Remaining: {TOTAL_WORKERS - workers_completed - workers_failed}")

            elapsed_hours = (datetime.now() - start_time).total_seconds() / 3600
            if workers_completed > 0:
                rate = workers_completed / elapsed_hours
                print(f"   Rate: {rate:.1f} workers/hour")
            print(f"{'='*80}\n")
            last_status_time = current_time

        # Small sleep to avoid busy waiting
        time.sleep(0.1)

    # Final summary
    elapsed_time = (datetime.now() - start_time).total_seconds()
    print(f"\n{'='*80}")
    print(f"🏁 IMAGE DOWNLOAD ORCHESTRATION COMPLETE")
    print(f"{'='*80}")
    print(f"Workers completed: {workers_completed}/{TOTAL_WORKERS}")
    print(f"Workers failed: {workers_failed}/{TOTAL_WORKERS}")
    print(f"Total time: {elapsed_time/3600:.1f} hours")
    if workers_completed > 0:
        print(f"Average time per worker: {elapsed_time/workers_completed/60:.1f} minutes")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
