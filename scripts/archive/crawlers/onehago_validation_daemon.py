#!/usr/bin/env python3
"""
Onehago Phase 2 Background Validation Daemon

Continuously monitors Phase 2 output folder and automatically validates/repairs
products as they are extracted. Runs independently in background.

Features:
- File system monitoring with watchdog
- Real-time validation of new products
- Automatic repair triggering for failures
- Independent background operation
- Graceful shutdown handling
"""
import json
import time
import signal
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
import requests
from bs4 import BeautifulSoup
from collections import defaultdict

# Configuration
WATCH_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only')
REPAIR_OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/repaired')
DAEMON_LOG = Path('/tmp/onehago_validation_daemon.log')
DAEMON_STATE = Path('/tmp/onehago_validation_daemon_state.json')

# Validation criteria
REQUIRED_FIELDS = ['product_id', 'product_name', 'specifications', 'company_info', 'image_urls', 'image_count']
MIN_IMAGE_COUNT = 1
MIN_SPEC_FIELDS = 2
MIN_COMPANY_FIELDS = 1

# Crawler settings
TIMEOUT = 30
RETRY_ATTEMPTS = 3
DELAY_BETWEEN_REQUESTS = 0.5

# Daemon control
RUNNING = True

class ValidationDaemon:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        # State tracking
        self.validated_products = self.load_state()
        self.files_in_progress = set()

        # Statistics
        self.stats = {
            'total_validated': 0,
            'passed': 0,
            'failed': 0,
            'repaired': 0,
            'repair_failed': 0,
            'files_processed': 0,
            'daemon_started': datetime.now().isoformat()
        }

        # Create output directory
        REPAIR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> Set[str]:
        """Load daemon state (already validated product IDs)"""
        if DAEMON_STATE.exists():
            try:
                with open(DAEMON_STATE, 'r') as f:
                    data = json.load(f)
                    return set(data.get('validated_products', []))
            except:
                return set()
        return set()

    def save_state(self):
        """Save daemon state"""
        with open(DAEMON_STATE, 'w') as f:
            json.dump({
                'validated_products': list(self.validated_products),
                'stats': self.stats,
                'last_update': datetime.now().isoformat()
            }, f, indent=2)

    def log(self, message: str, level: str = 'INFO'):
        """Log message to file and console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)

        with open(DAEMON_LOG, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')

    def validate_product(self, product: Dict) -> tuple[bool, List[str]]:
        """Validate product data quality"""
        issues = []
        product_id = product.get('product_id', 'UNKNOWN')

        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in product:
                issues.append(f"Missing field: {field}")

        # Validate product name
        product_name = product.get('product_name', '')
        if not product_name or len(product_name) < 5:
            issues.append("Invalid or too short product name")

        # Validate specifications
        specs = product.get('specifications', {})
        if not isinstance(specs, dict):
            issues.append("specifications is not a dict")
        elif len(specs) < MIN_SPEC_FIELDS:
            issues.append(f"Only {len(specs)} specification fields (minimum {MIN_SPEC_FIELDS})")

        # Validate company info
        company = product.get('company_info', {})
        if not isinstance(company, dict):
            issues.append("company_info is not a dict")
        elif len(company) < MIN_COMPANY_FIELDS:
            issues.append(f"Only {len(company)} company fields (minimum {MIN_COMPANY_FIELDS})")

        # Validate images
        image_urls = product.get('image_urls', [])
        image_count = product.get('image_count', 0)

        if not isinstance(image_urls, list):
            issues.append("image_urls is not a list")
        elif len(image_urls) < MIN_IMAGE_COUNT:
            issues.append(f"Only {len(image_urls)} images (minimum {MIN_IMAGE_COUNT})")

        if len(image_urls) != image_count:
            issues.append(f"image_count mismatch: {image_count} vs {len(image_urls)}")

        # Validate image URLs
        for url in image_urls:
            if not url.startswith('http'):
                issues.append(f"Invalid image URL: {url}")
                break

        is_valid = len(issues) == 0
        return is_valid, issues

    def extract_product_details(self, product_url: str, product_id: str) -> Dict:
        """Re-crawl product page and extract complete data"""
        for attempt in range(RETRY_ATTEMPTS):
            try:
                response = self.session.get(product_url, timeout=TIMEOUT)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract product name
                pack_tit = soup.find('div', class_='pack_tit')
                product_name = pack_tit.get_text(strip=True) if pack_tit else ""

                # Extract specifications and company info
                pack_info = soup.find('div', class_='pack_info')

                specifications = {}
                company_info = {}
                phone = ""
                fax = ""
                email = ""

                if pack_info:
                    dt_elements = pack_info.find_all('dt')
                    for dt in dt_elements:
                        label = dt.get_text(strip=True)
                        dd = dt.find_next_sibling('dd')
                        value = dd.get_text(strip=True) if dd else ""

                        # Map Korean labels to nested structures
                        if '코드' in label:
                            specifications['코드'] = value
                        elif '용량' in label:
                            specifications['용량'] = value
                        elif '사이즈' in label:
                            specifications['사이즈'] = value
                        elif 'MOQ' in label or '수량' in label:
                            specifications['MOQ'] = value
                        elif '재질' in label:
                            specifications['재질'] = value
                        elif '원산지' in label:
                            specifications['원산지'] = value
                        elif '제조사' in label:
                            company_info['제조사'] = value
                        elif '담당' in label:
                            company_info['담당'] = value
                        elif 'PHONE' in label or '전화' in label:
                            phone = value
                        elif 'FAX' in label:
                            fax = value
                        elif 'E MAIL' in label or 'EMAIL' in label or '이메일' in label:
                            email = value

                # Extract all image URLs
                image_urls = []
                img_tags = soup.find_all('img')
                for img in img_tags:
                    src = img.get('src', '')
                    if src and 'productImages' in src:
                        if src.startswith('http'):
                            image_urls.append(src)
                        else:
                            image_urls.append(f"https://www.onehago.com{src}")

                # Remove duplicates while preserving order
                seen = set()
                unique_images = []
                for url in image_urls:
                    if url not in seen:
                        seen.add(url)
                        unique_images.append(url)

                # Build result
                result = {
                    'detail_crawled': True,
                    'detail_crawled_at': datetime.now().isoformat(),
                    'specifications': specifications,
                    'company_info': company_info,
                    'image_urls': unique_images,
                    'product_name': product_name,
                    'phone': phone,
                    'fax': fax,
                    'email': email,
                    'image_count': len(unique_images),
                    'repaired': True,
                    'repaired_at': datetime.now().isoformat(),
                    'repaired_by': 'validation_daemon'
                }

                return result

            except Exception as e:
                if attempt < RETRY_ATTEMPTS - 1:
                    self.log(f"Retry {attempt + 1}/{RETRY_ATTEMPTS} for product {product_id}: {e}", 'WARNING')
                    time.sleep(2 * (attempt + 1))
                else:
                    self.log(f"Failed to re-crawl product {product_id} after {RETRY_ATTEMPTS} attempts: {e}", 'ERROR')
                    return None

        return None

    def repair_product(self, product: Dict, issues: List[str]) -> Dict:
        """Repair a failed product by re-crawling"""
        product_id = product.get('product_id', 'UNKNOWN')
        product_url = product.get('product_url', '')

        if not product_url:
            self.log(f"No URL for product {product_id}", 'ERROR')
            return None

        self.log(f"🔧 Repairing product {product_id} - Issues: {', '.join(issues)}", 'INFO')

        # Re-crawl product
        repaired_data = self.extract_product_details(product_url, product_id)

        if repaired_data:
            # Merge with original data
            repaired_product = {
                **product,
                **repaired_data
            }

            # Validate repaired data
            is_valid, new_issues = self.validate_product(repaired_product)

            if is_valid:
                self.log(f"✅ Successfully repaired product {product_id}", 'INFO')
                self.stats['repaired'] += 1
                return repaired_product
            else:
                self.log(f"⚠️ Repair incomplete for product {product_id}: {', '.join(new_issues)}", 'WARNING')
                self.stats['repair_failed'] += 1
                return repaired_product  # Return even if not perfect
        else:
            self.log(f"❌ Failed to repair product {product_id}", 'ERROR')
            self.stats['repair_failed'] += 1
            return None

    def process_file(self, file_path: Path):
        """Process a single output file"""
        # Avoid processing files currently being written
        if file_path in self.files_in_progress:
            return

        # Only process worker output and batch files
        if not (file_path.name.startswith('worker_') or file_path.name.startswith('batch_')):
            return

        if not file_path.name.endswith('.jsonl'):
            return

        self.files_in_progress.add(file_path)

        try:
            self.log(f"📂 Processing file: {file_path.name}", 'INFO')

            # Output file for repaired products
            output_file = REPAIR_OUTPUT_DIR / f"repaired_{file_path.name}"

            new_products_validated = 0
            new_products_repaired = 0

            with open(file_path, 'r', encoding='utf-8') as infile:
                with open(output_file, 'a', encoding='utf-8') as outfile:
                    for line in infile:
                        if not line.strip():
                            continue

                        try:
                            product = json.loads(line)
                            product_id = product.get('product_id', 'UNKNOWN')

                            # Skip if already validated
                            if product_id in self.validated_products:
                                continue

                            # Validate product
                            is_valid, issues = self.validate_product(product)

                            if is_valid:
                                self.stats['passed'] += 1
                                # Write valid product as-is
                                outfile.write(json.dumps(product, ensure_ascii=False) + '\n')
                                self.validated_products.add(product_id)
                                new_products_validated += 1
                            else:
                                self.stats['failed'] += 1

                                # Attempt repair
                                repaired_product = self.repair_product(product, issues)

                                if repaired_product:
                                    outfile.write(json.dumps(repaired_product, ensure_ascii=False) + '\n')
                                    self.validated_products.add(product_id)
                                    new_products_repaired += 1

                                # Rate limiting
                                time.sleep(DELAY_BETWEEN_REQUESTS)

                            self.stats['total_validated'] += 1

                        except json.JSONDecodeError:
                            continue

            self.stats['files_processed'] += 1

            if new_products_validated > 0 or new_products_repaired > 0:
                self.log(f"✅ File {file_path.name}: Validated {new_products_validated}, Repaired {new_products_repaired}", 'INFO')

            # Save state periodically
            self.save_state()

        except Exception as e:
            self.log(f"Error processing {file_path.name}: {e}", 'ERROR')

        finally:
            self.files_in_progress.discard(file_path)


class FileEventHandler(FileSystemEventHandler):
    """Handle file system events"""
    def __init__(self, daemon: ValidationDaemon):
        self.daemon = daemon
        self.last_processed = {}

    def on_modified(self, event):
        if isinstance(event, FileModifiedEvent) and not event.is_directory:
            self._handle_file_event(event.src_path)

    def on_created(self, event):
        if isinstance(event, FileCreatedEvent) and not event.is_directory:
            self._handle_file_event(event.src_path)

    def _handle_file_event(self, file_path: str):
        """Handle file creation/modification"""
        file_path = Path(file_path)

        # Only process jsonl files
        if not file_path.name.endswith('.jsonl'):
            return

        # Debounce: wait for file to be fully written
        current_time = time.time()
        last_time = self.last_processed.get(file_path, 0)

        # Process if not processed in last 5 seconds
        if current_time - last_time > 5:
            self.last_processed[file_path] = current_time

            # Small delay to ensure file is fully written
            time.sleep(2)

            # Process the file
            self.daemon.process_file(file_path)


def signal_handler(signum, frame):
    """Handle graceful shutdown"""
    global RUNNING
    print("\n🛑 Received shutdown signal, stopping daemon...")
    RUNNING = False


def main():
    global RUNNING

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create daemon
    daemon = ValidationDaemon()

    daemon.log("=" * 80, 'INFO')
    daemon.log("🚀 ONEHAGO VALIDATION DAEMON STARTED", 'INFO')
    daemon.log("=" * 80, 'INFO')
    daemon.log(f"Watch directory: {WATCH_DIR}", 'INFO')
    daemon.log(f"Repair output: {REPAIR_OUTPUT_DIR}", 'INFO')
    daemon.log(f"Log file: {DAEMON_LOG}", 'INFO')
    daemon.log(f"State file: {DAEMON_STATE}", 'INFO')
    daemon.log("", 'INFO')

    # Process existing files first
    daemon.log("📋 Processing existing files...", 'INFO')
    existing_files = list(WATCH_DIR.glob('worker_*.jsonl')) + list(WATCH_DIR.glob('batch_*.jsonl'))

    for file_path in sorted(existing_files):
        if not RUNNING:
            break
        daemon.process_file(file_path)

    daemon.log(f"✅ Processed {daemon.stats['files_processed']} existing files", 'INFO')
    daemon.log("", 'INFO')

    # Setup file system monitoring
    daemon.log("👀 Starting file system monitor...", 'INFO')
    event_handler = FileEventHandler(daemon)
    observer = Observer()
    observer.schedule(event_handler, str(WATCH_DIR), recursive=False)
    observer.start()

    daemon.log("✅ Daemon running in background", 'INFO')
    daemon.log("Press Ctrl+C to stop", 'INFO')
    daemon.log("", 'INFO')

    # Main loop
    try:
        while RUNNING:
            time.sleep(10)

            # Periodic status report
            if daemon.stats['total_validated'] > 0 and daemon.stats['total_validated'] % 100 == 0:
                daemon.save_state()
                daemon.log(f"📊 Status: Validated {daemon.stats['total_validated']}, "
                          f"Passed {daemon.stats['passed']}, Failed {daemon.stats['failed']}, "
                          f"Repaired {daemon.stats['repaired']}", 'INFO')

    except KeyboardInterrupt:
        pass

    finally:
        # Cleanup
        daemon.log("", 'INFO')
        daemon.log("🛑 Stopping file system monitor...", 'INFO')
        observer.stop()
        observer.join()

        # Final state save
        daemon.save_state()

        # Final statistics
        daemon.log("=" * 80, 'INFO')
        daemon.log("📊 DAEMON SHUTDOWN SUMMARY", 'INFO')
        daemon.log("=" * 80, 'INFO')
        daemon.log(f"Total products validated: {daemon.stats['total_validated']}", 'INFO')
        daemon.log(f"Passed validation: {daemon.stats['passed']}", 'INFO')
        daemon.log(f"Failed validation: {daemon.stats['failed']}", 'INFO')
        daemon.log(f"Successfully repaired: {daemon.stats['repaired']}", 'INFO')
        daemon.log(f"Repair failed: {daemon.stats['repair_failed']}", 'INFO')
        daemon.log(f"Files processed: {daemon.stats['files_processed']}", 'INFO')
        daemon.log("", 'INFO')
        daemon.log(f"💾 State saved to: {DAEMON_STATE}", 'INFO')
        daemon.log("=" * 80, 'INFO')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
Onehago Phase 2 Background Validation Daemon

Continuously monitors Phase 2 output folder and automatically validates/repairs
products as they are extracted. Runs independently in background.

Usage:
    python3 onehago_validation_daemon.py

The daemon will:
1. Process existing files in the watch directory
2. Monitor for new/modified files (worker_*.jsonl, batch_*.jsonl)
3. Validate each product against quality criteria
4. Automatically re-crawl and repair failed products
5. Save repaired data to: data/onehago/crawled/production/repaired/
6. Track state for resume capability

Features:
- Real-time file system monitoring with watchdog
- Automatic validation and repair
- Graceful shutdown (Ctrl+C)
- State persistence across restarts
- Rate limiting and retry logic
- Comprehensive logging

Output:
- Repaired files: repaired_worker_*.jsonl, repaired_batch_*.jsonl
- State file: /tmp/onehago_validation_daemon_state.json
- Log file: /tmp/onehago_validation_daemon.log

To run in background:
    nohup python3 onehago_validation_daemon.py > /dev/null 2>&1 &

To stop:
    Press Ctrl+C (foreground) or kill <pid> (background)
""")
        sys.exit(0)

    # Check for watchdog dependency
    try:
        import watchdog
    except ImportError:
        print("❌ Error: 'watchdog' library required")
        print("Install with: pip3 install watchdog")
        sys.exit(1)

    main()
