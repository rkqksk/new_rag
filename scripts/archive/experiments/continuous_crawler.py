#!/usr/bin/env python3
"""
Continuous Crawler with Auto-restart
Runs crawler continuously and restarts every 30 minutes
"""
import subprocess
import time
import os
from datetime import datetime
from pathlib import Path

LOG_FILE = "/tmp/continuous_crawler.log"
CHECK_INTERVAL = 1800  # 30 minutes in seconds
CRAWLER_SCRIPT = "scripts/crawl_onehago_complete.py"

def log(message):
    """Write log message to file and console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")

def count_products():
    """Count crawled products"""
    try:
        data_dir = Path("data/chungjinkorea/crawled_products_final")
        if data_dir.exists():
            json_files = list(data_dir.rglob("*.json"))
            return len(json_files)
    except Exception as e:
        log(f"⚠️ Error counting products: {e}")
    return 0

def run_crawler_with_timeout():
    """Run crawler with timeout"""
    log(f"🔄 Starting new crawl cycle...")
    
    start_time = time.time()
    
    try:
        # Run crawler with timeout
        process = subprocess.Popen(
            ["python3", CRAWLER_SCRIPT, "--details"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Monitor process with timeout
        while True:
            elapsed = time.time() - start_time
            
            if elapsed >= CHECK_INTERVAL:
                log(f"⏰ Crawler reached 30-minute timeout - terminating...")
                process.terminate()
                time.sleep(5)
                if process.poll() is None:
                    process.kill()
                return "TIMEOUT"
            
            # Check if process finished
            if process.poll() is not None:
                return_code = process.returncode
                if return_code == 0:
                    log(f"✅ Crawler completed successfully")
                    return "SUCCESS"
                else:
                    log(f"⚠️ Crawler exited with code {return_code}")
                    return "ERROR"
            
            # Wait a bit before checking again
            time.sleep(5)
            
    except Exception as e:
        log(f"❌ Error running crawler: {e}")
        return "ERROR"

def main():
    log("=" * 50)
    log("🚀 Continuous Crawler Started")
    log(f"Check interval: {CHECK_INTERVAL} seconds (30 minutes)")
    log("=" * 50)
    
    cycle_count = 0
    
    while True:
        cycle_count += 1
        log("")
        log(f"📊 Cycle #{cycle_count}")
        
        # Run crawler
        result = run_crawler_with_timeout()
        
        # Show progress
        product_count = count_products()
        log(f"📈 Current progress: {product_count} products crawled")
        
        # Brief pause before restart
        log("⏸️ Waiting 10 seconds before next cycle...")
        time.sleep(10)

if __name__ == "__main__":
    main()
