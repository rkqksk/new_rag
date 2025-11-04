#!/usr/bin/env python3
"""
Onehago Phase 2 Orchestrator - Manages multiple workers
Launches workers in batches, monitors progress, handles failures
"""
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Configuration
WORKERS_PER_BATCH = 8  # Number of concurrent workers
START_WORKER_ID = 90   # Resume from product 90,000 (worker 90)
END_WORKER_ID = 2011   # Process until 2,011,553 products (worker 2011)
WORKER_SCRIPT = Path('/Users/oypnus/Project/rag-enterprise/scripts/onehago_worker.py')

def main():
    print(f"{'='*80}")
    print(f"🚀 ONEHAGO PHASE 2 ORCHESTRATOR")
    print(f"{'='*80}")
    print(f"📊 Configuration:")
    print(f"   Workers per batch: {WORKERS_PER_BATCH}")
    print(f"   Start worker ID: {START_WORKER_ID} (product {START_WORKER_ID * 1000:,})")
    print(f"   End worker ID: {END_WORKER_ID} (product {END_WORKER_ID * 1000:,})")
    print(f"   Total workers: {END_WORKER_ID - START_WORKER_ID + 1}")
    print(f"   Total products: {(END_WORKER_ID - START_WORKER_ID + 1) * 1000:,}")
    print(f"⏱️  Started at {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*80}")
    print("")

    total_workers = END_WORKER_ID - START_WORKER_ID + 1
    workers_completed = 0
    workers_failed = 0
    start_time = datetime.now()

    # Process workers in batches
    current_worker_id = START_WORKER_ID

    while current_worker_id <= END_WORKER_ID:
        # Determine batch size
        batch_end = min(current_worker_id + WORKERS_PER_BATCH - 1, END_WORKER_ID)
        batch_size = batch_end - current_worker_id + 1

        print(f"\n{'='*80}")
        print(f"📦 BATCH: Workers {current_worker_id} to {batch_end} ({batch_size} workers)")
        print(f"{'='*80}")

        # Launch workers in this batch
        processes = {}
        for worker_id in range(current_worker_id, batch_end + 1):
            print(f"🚀 Launching worker {worker_id}...", flush=True)
            process = subprocess.Popen(
                ['python3', str(WORKER_SCRIPT), str(worker_id)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            processes[worker_id] = process

        print(f"\n✅ Launched {len(processes)} workers")
        print(f"🔄 Monitoring batch completion...")
        print("")

        # Monitor workers in this batch
        while processes:
            for worker_id in list(processes.keys()):
                process = processes[worker_id]

                # Read output line by line
                line = process.stdout.readline()
                if line:
                    print(f"[W{worker_id}] {line.rstrip()}", flush=True)

                # Check if process finished
                if process.poll() is not None:
                    # Process finished, read remaining output
                    for remaining_line in process.stdout:
                        print(f"[W{worker_id}] {remaining_line.rstrip()}", flush=True)

                    # Check exit code
                    if process.returncode == 0:
                        print(f"✅ Worker {worker_id} completed successfully")
                        workers_completed += 1
                    else:
                        print(f"❌ Worker {worker_id} failed with exit code {process.returncode}")
                        workers_failed += 1

                    del processes[worker_id]

            time.sleep(0.1)  # Small delay to prevent CPU spinning

        # Batch completed
        print(f"\n{'='*80}")
        print(f"✅ BATCH COMPLETE")
        print(f"{'='*80}")
        print(f"📊 Batch workers: {batch_size}")
        print(f"📈 Total progress: {workers_completed + workers_failed}/{total_workers} workers")
        print(f"✅ Success: {workers_completed}")
        print(f"❌ Failed: {workers_failed}")

        elapsed = datetime.now() - start_time
        rate = (workers_completed + workers_failed) / elapsed.total_seconds() * 3600 if elapsed.total_seconds() > 0 else 0
        print(f"⏱️  Elapsed: {elapsed}")
        print(f"📈 Rate: {rate:.1f} workers/hour")

        # Estimate time remaining
        remaining_workers = total_workers - (workers_completed + workers_failed)
        if rate > 0:
            eta_seconds = remaining_workers / rate * 3600
            eta_hours = eta_seconds / 3600
            print(f"⏳ ETA: {eta_hours:.1f} hours for remaining {remaining_workers} workers")

        print(f"{'='*80}")
        print("")

        # Move to next batch
        current_worker_id = batch_end + 1

    # Final summary
    elapsed = datetime.now() - start_time
    print(f"\n{'='*80}")
    print(f"✅ ORCHESTRATOR COMPLETE")
    print(f"{'='*80}")
    print(f"📊 Statistics:")
    print(f"   Total workers: {total_workers}")
    print(f"   Completed: {workers_completed} ({workers_completed/total_workers*100:.1f}%)")
    print(f"   Failed: {workers_failed} ({workers_failed/total_workers*100:.1f}%)")
    print(f"   Products extracted: ~{workers_completed * 1000:,}")
    print(f"⏱️  Time: {elapsed}")
    print(f"📈 Rate: {workers_completed / elapsed.total_seconds() * 3600:.1f} workers/hour")
    print(f"{'='*80}")

    # Exit with success if >95% workers succeeded
    success_rate = workers_completed / total_workers if total_workers > 0 else 0
    sys.exit(0 if success_rate > 0.95 else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Workers may still be running in background.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
