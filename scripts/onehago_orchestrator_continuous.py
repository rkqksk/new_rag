#!/usr/bin/env python3
"""
Onehago Phase 2 Continuous Orchestrator
Maintains 25 concurrent workers at all times
Automatically launches new workers as soon as old ones complete
"""
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Configuration
MAX_CONCURRENT_WORKERS = 12  # Maximum concurrent workers (reduced to avoid connection refused)
START_WORKER_ID = 90          # Resume from product 90,000 (worker 90)
END_WORKER_ID = 2011          # Process until 2,011,553 products (worker 2011)
WORKER_SCRIPT = Path('/Users/oypnus/Project/rag-enterprise/scripts/onehago_worker.py')

def launch_worker(worker_id):
    """Launch a single worker process"""
    process = subprocess.Popen(
        ['python3', str(WORKER_SCRIPT), str(worker_id)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    return process

def main():
    print(f"{'='*80}")
    print(f"🚀 ONEHAGO PHASE 2 CONTINUOUS ORCHESTRATOR")
    print(f"{'='*80}")
    print(f"📊 Configuration:")
    print(f"   Max concurrent workers: {MAX_CONCURRENT_WORKERS}")
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

    # Active workers: {worker_id: process}
    active_workers = {}
    next_worker_id = START_WORKER_ID
    last_status_time = time.time()

    # Launch initial batch of workers
    print(f"🚀 Launching initial batch of {MAX_CONCURRENT_WORKERS} workers...")
    for _ in range(min(MAX_CONCURRENT_WORKERS, total_workers)):
        if next_worker_id <= END_WORKER_ID:
            process = launch_worker(next_worker_id)
            active_workers[next_worker_id] = process
            print(f"✅ Launched worker {next_worker_id}", flush=True)
            next_worker_id += 1

    print(f"\n🔄 Monitoring workers and launching new ones as they complete...")
    print(f"{'='*80}\n")

    # Continuous monitoring loop
    while active_workers or next_worker_id <= END_WORKER_ID:
        # Check each active worker
        for worker_id in list(active_workers.keys()):
            process = active_workers[worker_id]

            # Read output line by line (non-blocking)
            line = process.stdout.readline()
            if line:
                # Only print progress lines, not startup messages
                if "Worker" in line and ("%" in line or "complete" in line.lower()):
                    print(f"[W{worker_id}] {line.rstrip()}", flush=True)

            # Check if process finished
            if process.poll() is not None:
                # Process finished, read remaining output
                for remaining_line in process.stdout:
                    if "Worker" in remaining_line and ("%" in remaining_line or "complete" in remaining_line.lower()):
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
                if next_worker_id <= END_WORKER_ID:
                    new_process = launch_worker(next_worker_id)
                    active_workers[next_worker_id] = new_process
                    print(f"🚀 Launched worker {next_worker_id} (replacing {worker_id})", flush=True)
                    next_worker_id += 1

        # Print status update every 5 minutes
        current_time = time.time()
        if current_time - last_status_time >= 300:  # 5 minutes
            elapsed = datetime.now() - start_time
            completed_total = workers_completed + workers_failed
            rate = completed_total / elapsed.total_seconds() * 3600 if elapsed.total_seconds() > 0 else 0
            remaining_workers = total_workers - completed_total

            print(f"\n{'='*80}")
            print(f"📊 STATUS UPDATE ({datetime.now().strftime('%H:%M:%S')})")
            print(f"{'='*80}")
            print(f"   Active workers: {len(active_workers)}")
            print(f"   Completed: {workers_completed} ({workers_completed/total_workers*100:.1f}%)")
            print(f"   Failed: {workers_failed} ({workers_failed/total_workers*100:.1f}%)")
            print(f"   Remaining: {remaining_workers}")
            print(f"   Rate: {rate:.1f} workers/hour")

            if rate > 0:
                eta_hours = remaining_workers / rate
                print(f"   ETA: {eta_hours:.1f} hours")

            print(f"{'='*80}\n")
            last_status_time = current_time

        time.sleep(0.1)  # Small delay to prevent CPU spinning

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
        import traceback
        traceback.print_exc()
        sys.exit(1)
