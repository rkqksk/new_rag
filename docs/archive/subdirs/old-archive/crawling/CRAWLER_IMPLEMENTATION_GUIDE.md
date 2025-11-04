# Web Crawler Agent System - Implementation Quick Reference

**Version**: 1.0  
**Date**: 2025-01-28  
**Audience**: Development Team

---

## Quick Index

- [Core Patterns](#core-patterns)
- [Code Templates](#code-templates)
- [Testing Checklist](#testing-checklist)
- [Deployment Checklist](#deployment-checklist)
- [Troubleshooting Guide](#troubleshooting-guide)

---

## Core Patterns

### Pattern 1: Exponential Backoff with Jitter

**When to use**: Any retry logic for transient failures

```python
import random
import asyncio

async def exponential_backoff(attempt, base_delay=1, max_delay=60):
    """Calculate backoff with jitter"""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter

async def retry_with_backoff(func, max_attempts=3):
    """Retry function with exponential backoff"""
    for attempt in range(max_attempts):
        try:
            return await func()
        except TransientError as e:
            if attempt < max_attempts - 1:
                delay = await exponential_backoff(attempt)
                print(f"Attempt {attempt + 1} failed, retrying in {delay:.1f}s")
                await asyncio.sleep(delay)
            else:
                raise
```

### Pattern 2: Circuit Breaker for Failing Endpoints

**When to use**: Prevent cascading failures when a site is unreachable

```python
from datetime import datetime, timedelta
import enum

class CircuitState(enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker open (recovery in {self._time_until_reset()}s)")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self):
        if self.last_failure_time is None:
            return False
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def _time_until_reset(self):
        if self.last_failure_time is None:
            return 0
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return max(0, self.recovery_timeout - elapsed)
```

### Pattern 3: Structured Logging

**When to use**: Every significant event in the crawler

```python
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_event(
        self,
        level: str,
        event: str,
        job_id: str,
        **metadata
    ):
        """Log structured event"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "event": event,
            "job_id": job_id,
            **metadata
        }
        
        log_method = getattr(self.logger, level.lower())
        log_method(json.dumps(log_entry))
    
    def log_item_processed(
        self,
        job_id: str,
        item_id: str,
        status: str,
        duration_ms: int,
        attempts: int = 1,
        error: Optional[str] = None,
        **metadata
    ):
        """Log item processing event"""
        self.log_event(
            "info" if status == "success" else "error",
            "item_processed",
            job_id=job_id,
            item_id=item_id,
            status=status,
            duration_ms=duration_ms,
            attempts=attempts,
            error=error,
            **metadata
        )
```

### Pattern 4: State Checkpoint for Resume

**When to use**: Enable resuming interrupted crawls

```python
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

class StateCheckpoint:
    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(self, job_id: str, state: Dict[str, Any]):
        """Save job state for resuming"""
        checkpoint_file = self.checkpoint_dir / f"{job_id}.json"
        state["checkpoint_time"] = datetime.utcnow().isoformat()
        
        with open(checkpoint_file, "w") as f:
            json.dump(state, f, indent=2)
        
        return checkpoint_file
    
    def load_checkpoint(self, job_id: str) -> Dict[str, Any]:
        """Load saved job state"""
        checkpoint_file = self.checkpoint_dir / f"{job_id}.json"
        
        if not checkpoint_file.exists():
            return None
        
        with open(checkpoint_file, "r") as f:
            return json.load(f)
    
    def delete_checkpoint(self, job_id: str):
        """Delete checkpoint after successful completion"""
        checkpoint_file = self.checkpoint_dir / f"{job_id}.json"
        if checkpoint_file.exists():
            checkpoint_file.unlink()

# Example usage
checkpoint = StateCheckpoint(Path("./checkpoints"))

# Save progress
checkpoint.save_checkpoint("job_123", {
    "page_number": 5,
    "items_processed": 45,
    "last_item_id": "idx_960"
})

# Resume from checkpoint
state = checkpoint.load_checkpoint("job_123")
if state:
    print(f"Resume from page {state['page_number']}")
```

### Pattern 5: Error Classification

**When to use**: Decide whether to retry, skip, or alert

```python
import enum
from typing import Optional

class ErrorType(enum.Enum):
    TRANSIENT = "transient"        # Retry
    RATE_LIMIT = "rate_limit"      # Retry with longer backoff
    AUTH_FAILURE = "auth_failure"   # Skip, alert
    NOT_FOUND = "not_found"        # Skip, mark as deleted
    PARSING_ERROR = "parsing_error" # Log, fallback
    BROWSER_ERROR = "browser_error" # Restart, retry
    UNKNOWN = "unknown"             # Log, alert

class ErrorClassifier:
    @staticmethod
    def classify(error: Exception, response_status: Optional[int] = None) -> ErrorType:
        """Classify error type"""
        
        # HTTP status-based classification
        if response_status:
            if response_status in [429, 503, 504]:
                return ErrorType.TRANSIENT
            if response_status == 429:
                return ErrorType.RATE_LIMIT
            if response_status in [401, 403]:
                return ErrorType.AUTH_FAILURE
            if response_status == 404:
                return ErrorType.NOT_FOUND
        
        # Exception type classification
        error_str = str(error).lower()
        
        if "timeout" in error_str or "connection" in error_str:
            return ErrorType.TRANSIENT
        
        if "429" in error_str:
            return ErrorType.RATE_LIMIT
        
        if "playwright" in error_str or "browser" in error_str:
            return ErrorType.BROWSER_ERROR
        
        if "parse" in error_str or "selector" in error_str:
            return ErrorType.PARSING_ERROR
        
        return ErrorType.UNKNOWN
    
    @staticmethod
    def should_retry(error_type: ErrorType, attempt_count: int, max_retries: int) -> bool:
        """Determine if error is retryable"""
        if attempt_count >= max_retries:
            return False
        
        retryable = {
            ErrorType.TRANSIENT,
            ErrorType.RATE_LIMIT,
            ErrorType.BROWSER_ERROR,
            ErrorType.UNKNOWN  # Retry once
        }
        
        return error_type in retryable
    
    @staticmethod
    def get_recovery_action(error_type: ErrorType) -> str:
        """Get recovery action"""
        actions = {
            ErrorType.TRANSIENT: "retry",
            ErrorType.RATE_LIMIT: "wait_and_retry",
            ErrorType.AUTH_FAILURE: "skip_and_alert",
            ErrorType.NOT_FOUND: "skip_and_mark",
            ErrorType.PARSING_ERROR: "log_and_fallback",
            ErrorType.BROWSER_ERROR: "restart_and_retry",
            ErrorType.UNKNOWN: "log_and_alert"
        }
        return actions[error_type]
```

---

## Code Templates

### Template 1: Site-Specific Crawler

```python
# crawlers/mysite_crawler.py
import asyncio
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime

from core.base_crawler import BaseSiteCrawler
from core.http_client import RetryableHTTPClient
from core.parsing_engine import ParsingEngine
from core.error_manager import ErrorRecoveryManager

logger = logging.getLogger(__name__)

class MySiteCrawler(BaseSiteCrawler):
    """Crawler for mysite.com"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.site_id = "mysite"
        self.domain = "mysite.com"
        self.base_url = config.get("base_url", "https://mysite.com")
        
        self.http_client = RetryableHTTPClient(
            max_retries=config.get("max_retries", 3),
            base_delay=config.get("base_delay", 1)
        )
        self.parser = ParsingEngine()
        self.error_manager = ErrorRecoveryManager()
    
    async def get_category_urls(self) -> List[str]:
        """Discover category pages"""
        categories = self.config.get("categories", [])
        return [cat["url"] for cat in categories]
    
    async def get_page_urls(self, category_url: str, page: int) -> List[str]:
        """Get product URLs for a page"""
        url = f"{category_url}?page={page}"
        
        try:
            response = await self.http_client.get_with_retry(url)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract product URLs based on site selectors
            selector = self.config["selectors"]["product_list"]
            links = soup.select(selector)
            
            urls = []
            for link in links:
                href = link.get("href")
                if href:
                    full_url = f"{self.base_url}{href}" if href.startswith("/") else href
                    urls.append(full_url)
            
            return urls
        
        except Exception as e:
            logger.error(f"Failed to get page URLs from {url}: {e}")
            return []
    
    async def parse_product_page(self, html: str) -> Optional[Dict[str, Any]]:
        """Extract product data from HTML"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Use flexible parsing engine
            data = self.parser.parse_page(
                html,
                self.config.get("selectors", {})
            )
            
            # Validate data
            validators = self.config.get("validators", {})
            if not self.parser.validate_data(data, validators):
                logger.warning(f"Data validation failed: {data}")
                return None
            
            # Add metadata
            data["crawled_at"] = datetime.utcnow().isoformat()
            data["site_id"] = self.site_id
            
            return data
        
        except Exception as e:
            logger.error(f"Failed to parse product page: {e}")
            return None
    
    async def get_next_page_link(self, html: str) -> Optional[str]:
        """Find next page URL"""
        soup = BeautifulSoup(html, "html.parser")
        
        # Site-specific pagination logic
        next_button = soup.select_one(self.config["selectors"].get("pagination_next"))
        if next_button and next_button.get("href"):
            return f"{self.base_url}{next_button['href']}"
        
        return None
    
    async def crawl_category(
        self,
        category_url: str,
        max_pages: Optional[int] = None
    ) -> Dict[str, Any]:
        """Crawl entire category"""
        logger.info(f"Starting crawl: {category_url}")
        
        all_urls = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
            
            urls = await self.get_page_urls(category_url, page)
            if not urls:
                break
            
            all_urls.extend(urls)
            logger.info(f"Page {page}: Found {len(urls)} products")
            
            page += 1
            await asyncio.sleep(self.config.get("delay_between_pages", 2))
        
        # Process all URLs
        results = {
            "total": len(all_urls),
            "success": 0,
            "failed": 0,
            "items": []
        }
        
        for i, url in enumerate(all_urls, 1):
            try:
                response = await self.http_client.get_with_retry(url)
                data = await self.parse_product_page(response.text)
                
                if data:
                    results["items"].append(data)
                    results["success"] += 1
                else:
                    results["failed"] += 1
                
                logger.info(f"[{i}/{len(all_urls)}] Processed: {url}")
            
            except Exception as e:
                logger.error(f"Failed to crawl {url}: {e}")
                results["failed"] += 1
            
            await asyncio.sleep(self.config.get("delay_between_items", 1))
        
        return results
```

### Template 2: Metrics and Monitoring

```python
# monitoring/metrics.py
import time
from functools import wraps
from datetime import datetime
from typing import Any, Callable

class CrawlerMetrics:
    """Simple metrics collection"""
    
    def __init__(self):
        self.metrics = {
            "requests": [],
            "items_processed": [],
            "errors": [],
            "retries": []
        }
    
    def record_request(
        self,
        site_id: str,
        url: str,
        status_code: int,
        duration_ms: float
    ):
        """Record HTTP request"""
        self.metrics["requests"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "site_id": site_id,
            "url": url,
            "status_code": status_code,
            "duration_ms": duration_ms
        })
    
    def record_item_processed(
        self,
        job_id: str,
        item_id: str,
        site_id: str,
        status: str,
        duration_ms: float,
        attempts: int = 1
    ):
        """Record item processing"""
        self.metrics["items_processed"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "job_id": job_id,
            "item_id": item_id,
            "site_id": site_id,
            "status": status,
            "duration_ms": duration_ms,
            "attempts": attempts
        })
    
    def record_error(
        self,
        site_id: str,
        error_type: str,
        error_message: str
    ):
        """Record error"""
        self.metrics["errors"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "site_id": site_id,
            "error_type": error_type,
            "error_message": error_message
        })
    
    def get_summary(self) -> dict:
        """Get metrics summary"""
        success = sum(1 for m in self.metrics["items_processed"] if m["status"] == "success")
        total = len(self.metrics["items_processed"])
        success_rate = (success / total * 100) if total > 0 else 0
        
        avg_duration = 0
        if self.metrics["items_processed"]:
            avg_duration = sum(m["duration_ms"] for m in self.metrics["items_processed"]) / total
        
        return {
            "total_requests": len(self.metrics["requests"]),
            "total_items": total,
            "successful_items": success,
            "success_rate": success_rate,
            "avg_duration_ms": avg_duration,
            "total_errors": len(self.metrics["errors"]),
            "error_types": list(set(e["error_type"] for e in self.metrics["errors"]))
        }

def measure_time(func: Callable) -> Callable:
    """Decorator to measure function execution time"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration_ms = (time.time() - start) * 1000
        return result, duration_ms
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration_ms = (time.time() - start) * 1000
        return result, duration_ms
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
```

---

## Testing Checklist

### Unit Tests

- [ ] RetryableHTTPClient
  - [ ] Successful request returns response
  - [ ] Transient error triggers retry
  - [ ] Permanent error fails immediately
  - [ ] Exponential backoff is calculated correctly
  - [ ] Max retries limit is enforced
  - [ ] Circuit breaker opens after threshold

- [ ] ErrorRecoveryManager
  - [ ] Network errors classified as TRANSIENT
  - [ ] 404 errors classified as NOT_FOUND
  - [ ] 429 errors classified as RATE_LIMIT
  - [ ] Recovery action for each error type

- [ ] ParsingEngine
  - [ ] CSS selector extraction works
  - [ ] Fallback selectors used when primary fails
  - [ ] Data validation enforces required fields
  - [ ] Invalid data rejected

- [ ] StateTracker
  - [ ] Checkpoint saved correctly
  - [ ] Checkpoint loaded correctly
  - [ ] State persisted to database

### Integration Tests

- [ ] Complete crawler flow
  - [ ] Category page crawled
  - [ ] Product URLs extracted
  - [ ] Product pages parsed
  - [ ] Data saved to database
  - [ ] Progress tracked

- [ ] Error recovery
  - [ ] Transient error retried and succeeded
  - [ ] Permanent error skipped with alert
  - [ ] Rate limit handled with backoff
  - [ ] Failed items added to DLQ

- [ ] Resume capability
  - [ ] Interrupted job paused
  - [ ] State checkpoint saved
  - [ ] Job resumed from checkpoint
  - [ ] No duplicate processing

### Performance Tests

- [ ] Concurrent crawling
  - [ ] 5 concurrent jobs execute
  - [ ] No race conditions
  - [ ] Memory usage stays within limits

- [ ] Load testing
  - [ ] Rate limiting enforced
  - [ ] Circuit breaker prevents overload
  - [ ] System degrades gracefully

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing (unit, integration, e2e)
- [ ] Code reviewed
- [ ] Configuration reviewed
- [ ] Database migrations tested
- [ ] Monitoring dashboards created
- [ ] Alert rules configured
- [ ] Runbooks written

### Deployment

- [ ] Database migrations applied
- [ ] Configuration deployed
- [ ] Health checks passing
- [ ] Smoke tests running
- [ ] Monitoring alerts verified

### Post-Deployment

- [ ] Monitor error rate (target: < 5%)
- [ ] Monitor success rate (target: > 95%)
- [ ] Monitor response latency (target: < 3s p95)
- [ ] Monitor queue depth (target: < 50)
- [ ] Alert if thresholds breached

---

## Troubleshooting Guide

### Issue: High Error Rate (> 20%)

**Symptoms**: Alert triggered, many items failing

**Diagnosis**:
1. Check logs for error types
2. Verify site connectivity: `curl -I https://mysite.com`
3. Check circuit breaker status
4. Review recent site changes

**Resolution**:
- If rate limit: Increase delay between requests
- If timeout: Increase timeout threshold
- If parsing: Update selectors for site changes
- If auth: Check credentials, IP allowlist

### Issue: Crawler Slow (> 5s per item)

**Symptoms**: Progress slow, ETA increasing

**Diagnosis**:
1. Check average response time
2. Check network latency: `ping mysite.com`
3. Monitor CPU/memory usage
4. Check for browser bottlenecks

**Resolution**:
- Increase concurrent requests (if site allows)
- Reduce delay between requests
- Optimize parsing logic
- Scale up hardware resources

### Issue: OOM (Out of Memory)

**Symptoms**: Process killed, memory exceeds limit

**Diagnosis**:
1. Check memory per item
2. Monitor collection size growth
3. Look for memory leaks in parsing

**Resolution**:
- Process items in batches
- Save intermediate results to database
- Limit in-memory cache size
- Use streaming instead of loading full page

### Issue: Stuck Job (No Progress for 24h)

**Symptoms**: Job in IN_PROGRESS state, no activity

**Diagnosis**:
1. Check logs for last activity
2. Verify database connectivity
3. Check job queue status
4. Look for deadlock conditions

**Resolution**:
- Manually pause job: `curl -X POST /api/jobs/{id}/pause`
- Check database locks
- Restart crawler service
- Resume job: `curl -X POST /api/jobs/{id}/resume`

---

## Quick Commands

```bash
# Check crawler health
curl http://localhost:8000/api/crawler/health

# List active jobs
curl http://localhost:8000/api/jobs?status=in_progress

# Get job details
curl http://localhost:8000/api/jobs/{job_id}

# Pause job
curl -X POST http://localhost:8000/api/jobs/{job_id}/pause

# Resume job
curl -X POST http://localhost:8000/api/jobs/{job_id}/resume

# View metrics
curl http://localhost:8000/api/metrics

# View logs
docker logs crawler_service | jq '.event'

# View DLQ items
curl http://localhost:8000/api/dlq?job_id={job_id}
```

