# Web Crawler Agent System - Design Blueprint

**Version**: 1.0  
**Date**: 2025-01-28  
**Status**: Design Phase  
**Target Websites**: chunjinkorea.com, freemold.net, onehago.com

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Core Components](#core-components)
4. [Error Handling Strategy](#error-handling-strategy)
5. [Monitoring & Observability](#monitoring--observability)
6. [Scalability Design](#scalability-design)
7. [State Management](#state-management)
8. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

This document provides a comprehensive design blueprint for a **production-grade web crawler agent system** that handles multiple e-commerce websites with robust error recovery, detailed monitoring, and horizontal scalability.

### Key Design Goals

- **Reliability**: Automatic recovery from transient failures with exponential backoff
- **Observability**: Real-time progress tracking, detailed logging, and performance metrics
- **Maintainability**: Modular architecture supporting independent crawler updates
- **Scalability**: Multi-site, multi-page, concurrent crawling with resource pooling
- **Extensibility**: Easy addition of new websites with minimal boilerplate

### Design Principles

```
┌─────────────────────────────────────────────────────┐
│         Web Crawler Agent System Principles         │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 1. MODULAR DESIGN                                   │
│    • One crawler per website                        │
│    • Pluggable parsing strategies                   │
│    • Reusable error recovery mechanisms             │
│                                                     │
│ 2. FAULT TOLERANCE                                  │
│    • Exponential backoff for retries               │
│    • Circuit breaker pattern for failing endpoints │
│    • Dead letter queues for failed crawls          │
│    • Automatic state persistence                    │
│                                                     │
│ 3. OBSERVABILITY                                    │
│    • Structured logging at key checkpoints         │
│    • Metrics collection (success rate, latency)    │
│    • Real-time progress dashboard                  │
│    • Health check endpoints                        │
│                                                     │
│ 4. EFFICIENT RESOURCE USAGE                        │
│    • Connection pooling                            │
│    • Rate limiting per domain                      │
│    • Browser instance caching/reuse                │
│    • Bandwidth-aware scheduling                    │
│                                                     │
│ 5. AUTOMATION-READY                                │
│    • Resume interrupted crawls                     │
│    • Incremental updates                           │
│    • Scheduled execution with state validation     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Architecture Overview

### High-Level System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Crawler Orchestration Layer                   │
│                   (CrawlerOrchestrator)                          │
│  • Job scheduling & distribution                                │
│  • Multi-site coordination                                      │
│  • State management & persistence                               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌───────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  ChungjinCrawler  │ │  FreemoldCrawler │ │  OneHagoCrawler  │
│  (Site-specific)  │ │  (Site-specific) │ │  (Site-specific) │
└────────┬──────────┘ └──────────┬───────┘ └────────┬─────────┘
         ↓                       ↓                   ↓
     ┌───────────────────────────────────────────────────┐
     │    Core Crawler Components (Shared)              │
     ├───────────────────────────────────────────────────┤
     │ • RetryableHTTPClient (with exponential backoff) │
     │ • ParsingEngine (flexible selector-based)        │
     │ • ErrorRecoveryManager (circuit breaker)         │
     │ • StateTracker (resume capability)               │
     └───────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
    ┌─────────┐          ┌──────────┐        ┌──────────┐
    │ Database│          │Redis     │        │File      │
    │(State)  │          │(Cache)   │        │Storage   │
    └─────────┘          └──────────┘        └──────────┘
         ↓                    ↓                    ↓
    ┌────────────────────────────────────────────────────┐
    │         Monitoring & Observability Layer           │
    ├────────────────────────────────────────────────────┤
    │ • PrometheusMetrics (HTTP library)                │
    │ • StructuredLogger (JSON output)                  │
    │ • HealthCheckService                             │
    │ • DashboardAPI (real-time progress)              │
    └────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Request
    ↓
CrawlerOrchestrator
    ├─ Load state from database
    ├─ Create job record
    ├─ Route to appropriate crawler
    ↓
Site-Specific Crawler (ChungjinCrawler)
    ├─ Validate configuration
    ├─ Fetch URL list
    ├─ Save progress checkpoint
    ↓
RetryableHTTPClient
    ├─ Execute request (with retry logic)
    ├─ Handle transient failures (3xx, 4xx, 5xx)
    ├─ Apply exponential backoff
    ├─ Use circuit breaker if needed
    ↓
ParsingEngine
    ├─ Extract data using CSS selectors
    ├─ Validate extracted data
    ├─ Handle parsing errors gracefully
    ↓
StateTracker
    ├─ Save crawled item to database
    ├─ Update progress metrics
    ├─ Persist checkpoint
    ↓
Monitoring System
    ├─ Record metrics (latency, success rate)
    ├─ Log structured events
    ├─ Update dashboard
    ↓
Job Completion
    ├─ Generate summary report
    ├─ Send notifications
    ├─ Archive state
```

---

## Core Components

### 1. RetryableHTTPClient

**Purpose**: Handle HTTP requests with sophisticated retry logic

```python
class RetryableHTTPClient:
    """
    HTTP client with exponential backoff and circuit breaker
    
    Features:
    - Exponential backoff (base=1s, max=60s)
    - Jitter to prevent thundering herd
    - Circuit breaker pattern for failing endpoints
    - Connection pooling
    - Configurable timeout per site
    """
    
    def __init__(self, max_retries=3, base_delay=1, max_delay=60):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.circuit_breakers = {}  # Per-domain circuit breaker
        self.connection_pool = aiohttp.TCPConnector(limit=10)
    
    async def get_with_retry(self, url, headers=None, timeout=30):
        """
        Retry logic:
        1. First attempt (immediate)
        2. Retry on: 429, 503, 504, timeout, connection errors
        3. Skip retry on: 400, 401, 403, 404 (permanent errors)
        4. Backoff: 1s, 2s, 4s (exponential) + random jitter
        """
        
    def _calculate_backoff(self, attempt):
        """
        Exponential backoff with jitter:
        delay = min(base * (2 ^ attempt) + random(0, 1), max)
        """
```

**Retry Strategy**:

```
Attempt 1: Immediate
  ↓ (failure)
Attempt 2: 1s + jitter (0-1s) = 1-2s wait
  ↓ (failure)
Attempt 3: 2s + jitter (0-2s) = 2-4s wait
  ↓ (failure)
Attempt 4: 4s + jitter (0-4s) = 4-8s wait
  ↓ (failure)
→ Permanent failure (circuit breaker triggered)
```

### 2. ErrorRecoveryManager

**Purpose**: Detect and classify errors, implement recovery strategies

```python
class ErrorRecoveryManager:
    """
    Error classification and recovery:
    
    Error Types:
    - TRANSIENT: Network timeout, 503 (Service Unavailable)
    - RATE_LIMIT: 429 (Too Many Requests)
    - AUTH_FAILURE: 401, 403 (Permanent)
    - NOT_FOUND: 404 (Permanent for this URL)
    - PARSING_ERROR: Invalid HTML structure
    - BROWSER_ERROR: Playwright/Selenium failure
    - UNKNOWN: Unexpected error
    
    Recovery Strategies:
    - TRANSIENT: Retry with exponential backoff
    - RATE_LIMIT: Wait + Retry (longer backoff)
    - AUTH_FAILURE: Alert operator, skip item
    - NOT_FOUND: Mark as deleted, skip item
    - PARSING_ERROR: Log issue, continue with fallback
    - BROWSER_ERROR: Restart browser, retry
    - UNKNOWN: Log details, mark for manual review
    """
    
    def classify_error(self, error, response=None):
        """Classify error type"""
        
    def get_recovery_action(self, error_type, attempt_count):
        """Return recovery action (retry, skip, alert, etc.)"""
```

**Error Recovery Matrix**:

```
┌──────────────────┬──────────────────┬─────────────────────┐
│ Error Type       │ Recovery Action  │ Backoff Strategy    │
├──────────────────┼──────────────────┼─────────────────────┤
│ TRANSIENT        │ Retry            │ Exponential (1-4s)  │
│ RATE_LIMIT       │ Retry + Wait     │ Exponential (5-30s) │
│ AUTH_FAILURE     │ Skip + Alert     │ N/A (no retry)      │
│ NOT_FOUND        │ Skip + Mark      │ N/A (no retry)      │
│ PARSING_ERROR    │ Log + Fallback   │ N/A (no retry)      │
│ BROWSER_ERROR    │ Restart + Retry  │ Exponential (1-2s)  │
│ UNKNOWN          │ Log + Manual      │ Retry 1x           │
└──────────────────┴──────────────────┴─────────────────────┘
```

### 3. StateTracker

**Purpose**: Track crawling progress, enable resume capability

```python
class StateTracker:
    """
    Persistent state management:
    
    State Types:
    - JOB: Overall crawling job status
    - PAGE: Page-level crawling status
    - ITEM: Individual item crawling status
    - CHECKPOINT: Savepoint for resuming
    
    State Transitions:
    JOB: PENDING → IN_PROGRESS → PAUSED → COMPLETED/FAILED
    PAGE: PENDING → IN_PROGRESS → COMPLETED/FAILED
    ITEM: PENDING → IN_PROGRESS → COMPLETED/FAILED/SKIPPED
    
    Persistence:
    - Database: Job/page metadata
    - Redis: Real-time counters
    - File: Checkpoint snapshots
    """
    
    def create_job(self, site_id, start_url, config):
        """Initialize job state"""
        
    def update_item_status(self, job_id, item_id, status, metadata=None):
        """Update individual item status"""
        
    def save_checkpoint(self, job_id, page_num, items_processed):
        """Save state for resuming"""
        
    def load_checkpoint(self, job_id):
        """Restore state from checkpoint"""
```

**State Persistence Design**:

```
Database (PostgreSQL):
├─ CrawlJob
│  ├─ id (UUID)
│  ├─ site_id (chunjin|freemold|onehago)
│  ├─ status (pending, in_progress, paused, completed, failed)
│  ├─ config (JSON: selectors, retry_policy, etc.)
│  ├─ created_at, updated_at, completed_at
│  └─ metadata (JSON: error_summary, stats)
│
├─ CrawlPage
│  ├─ job_id (FK)
│  ├─ page_number
│  ├─ status (pending, in_progress, completed, failed)
│  ├─ items_found, items_processed
│  └─ error_details (JSON)
│
└─ CrawlItem
   ├─ job_id (FK)
   ├─ item_id (product_id)
   ├─ url
   ├─ status (pending, success, failed, skipped)
   ├─ retries_count
   ├─ last_error (JSON)
   └─ crawled_data (JSONB)

Redis (Real-time metrics):
├─ job:{job_id}:counters
│  ├─ total_items
│  ├─ processed_items
│  ├─ successful_items
│  ├─ failed_items
│  └─ start_time
│
└─ site:{site_id}:health
   ├─ last_error_at
   ├─ consecutive_errors
   └─ circuit_breaker_state
```

### 4. ParsingEngine

**Purpose**: Extract data using flexible, site-specific selectors

```python
class ParsingEngine:
    """
    Flexible HTML parsing with fallback strategies:
    
    Features:
    - CSS selector-based extraction
    - Multiple selector alternatives
    - Data validation and type coercion
    - Error recovery with fallback selectors
    - Image/file extraction
    """
    
    def parse_page(self, html, site_config):
        """
        Parse HTML using site-specific configuration:
        {
            "selectors": {
                "product_name": ".product-title",
                "price": [".price", ".product-price"],  # alternatives
                "description": ".description"
            },
            "validators": {
                "product_name": "string, required",
                "price": "float, optional"
            }
        }
        """
        
    def extract_with_fallback(self, soup, selectors):
        """
        Try primary selector, fallback to alternatives:
        selectors = [".primary-selector", ".fallback1", ".fallback2"]
        """
        
    def validate_data(self, data, validators):
        """
        Validate extracted data against schema:
        - Type checking
        - Required field validation
        - Format validation (email, URL, etc.)
        """
```

### 5. Site-Specific Crawlers

**Purpose**: Implement site-specific logic for each website

```python
class BaseSiteCrawler:
    """
    Abstract base class for site-specific crawlers
    
    Methods to implement:
    - get_category_urls(): Discover category pages
    - get_page_urls(category_url): Get product URLs per page
    - parse_product_page(html): Extract product data
    - get_next_page_link(html): Find pagination
    """
    
    async def crawl_category(self, category_url, max_pages=None):
        """Crawl entire category with pagination"""
        
    async def crawl_product(self, product_url):
        """Crawl single product page"""
        
    async def handle_javascript(self, url):
        """Handle JS-heavy pages using browser automation"""

# Site implementations
class ChungjinCrawler(BaseSiteCrawler):
    """chunjinkorea.com specific implementation"""
    # URL patterns, selectors, custom logic
    
class FreemoldCrawler(BaseSiteCrawler):
    """freemold.net specific implementation"""
    # URL patterns, selectors, custom logic
    
class OneHagoCrawler(BaseSiteCrawler):
    """onehago.com specific implementation"""
    # URL patterns, selectors, custom logic
```

### 6. CrawlerOrchestrator

**Purpose**: Coordinate multiple crawlers, manage job lifecycle

```python
class CrawlerOrchestrator:
    """
    Master orchestrator for all crawling operations:
    
    Responsibilities:
    - Job creation and lifecycle management
    - Route crawling requests to appropriate crawler
    - Coordinate multi-site crawling
    - Monitor resource utilization
    - Trigger alerts on failures
    """
    
    async def submit_crawl_job(self, site_id, config):
        """
        Submit new crawling job:
        {
            "site_id": "chunjin|freemold|onehago",
            "config": {
                "start_url": "https://...",
                "max_pages": 10,
                "retry_policy": {...},
                "selectors": {...}
            }
        }
        Returns: job_id (UUID)
        """
        
    async def pause_job(self, job_id):
        """Pause running job (save state for resume)"""
        
    async def resume_job(self, job_id):
        """Resume paused job from last checkpoint"""
        
    async def cancel_job(self, job_id):
        """Cancel running job"""
        
    def get_job_status(self, job_id):
        """Get real-time job status"""
```

---

## Error Handling Strategy

### Error Classification Hierarchy

```
Errors
├─ RECOVERABLE (Transient)
│  ├─ Network Errors
│  │  ├─ Timeout
│  │  ├─ Connection refused
│  │  └─ DNS resolution failure
│  ├─ HTTP Errors
│  │  ├─ 429 (Too Many Requests)
│  │  ├─ 503 (Service Unavailable)
│  │  └─ 504 (Gateway Timeout)
│  └─ Temporary Parsing Issues
│     ├─ Partial content
│     └─ Missing expected elements
│
├─ PERMANENT (Non-recoverable)
│  ├─ HTTP Errors
│  │  ├─ 401 (Unauthorized)
│  │  ├─ 403 (Forbidden)
│  │  └─ 404 (Not Found)
│  ├─ Data Validation Errors
│  │  ├─ Invalid URL format
│  │  └─ Corrupted response
│  └─ Configuration Errors
│     ├─ Invalid selectors
│     └─ Wrong site config
│
└─ UNKNOWN (Requires Investigation)
   ├─ Unexpected HTTP status
   ├─ Malformed HTML
   └─ Browser crashes
```

### Retry Logic Decision Tree

```
Request fails
    ↓
Classify error type
    ├─ TRANSIENT?
    │  ├─ Attempt < max_retries?
    │  │  ├─ Yes → Wait (exponential backoff) → Retry
    │  │  └─ No → Move to dead letter queue
    │  └─ Rate limit? 
    │     ├─ Yes → Wait (longer) → Retry
    │     └─ No → Exponential backoff
    │
    ├─ PERMANENT?
    │  ├─ 404? → Mark item as deleted → Continue
    │  ├─ Auth? → Alert operator → Skip
    │  └─ Invalid? → Log error → Skip
    │
    └─ UNKNOWN?
       ├─ Log details
       ├─ Alert operator
       └─ Attempt 1 retry, then manual review
```

### Circuit Breaker Pattern

```
States: CLOSED → OPEN → HALF_OPEN → CLOSED

CLOSED (Normal):
- All requests pass through
- Failure count = 0
- Track recent failures

OPEN (Failing):
- Triggered when:
  - Consecutive failures >= threshold (e.g., 5)
  - OR recent error rate > threshold (e.g., 50% in last 100)
- All requests fail immediately (fast fail)
- Wait for backoff period (e.g., 60s)

HALF_OPEN (Testing):
- After backoff period expires
- Allow limited requests (e.g., 1 per second)
- If success: → CLOSED (reset failure count)
- If failure: → OPEN (extend backoff period)
```

**Implementation**:

```python
class CircuitBreaker:
    """Circuit breaker per domain/endpoint"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
    
    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpen(f"Circuit open for {self.recovery_timeout}s")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = now()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def _should_attempt_reset(self):
        elapsed = now() - self.last_failure_time
        return elapsed.total_seconds() >= self.recovery_timeout
```

### Dead Letter Queue (DLQ)

**Purpose**: Track items that failed permanently for manual review

```python
class DeadLetterQueue:
    """
    Store permanently failed items:
    
    Triggers:
    - Exceeded max retries
    - Permanent error (404, 403, etc.)
    - Validation error after extraction
    
    Storage:
    {
        "job_id": "...",
        "item_id": "...",
        "url": "...",
        "error_type": "PARSING_ERROR",
        "error_details": {...},
        "last_attempt_at": "2025-01-28T...",
        "created_at": "..."
    }
    """
    
    async def add_failed_item(self, job_id, item_id, error, metadata=None):
        """Add item to DLQ"""
        
    async def get_dlq_items(self, job_id):
        """Get all DLQ items for a job"""
        
    async def retry_dlq_item(self, dlq_item_id):
        """Manually retry a DLQ item"""
```

---

## Monitoring & Observability

### Metrics Collection

**Key Metrics**:

```python
class CrawlerMetrics:
    """
    Prometheus metrics for crawler monitoring
    
    Counters:
    - crawler_requests_total (site, status)
    - crawler_items_processed_total (site, status)
    - crawler_errors_total (site, error_type)
    - crawler_retries_total (site, reason)
    
    Histograms:
    - crawler_request_duration_seconds (site, status)
    - crawler_item_processing_duration_seconds (site)
    - crawler_page_processing_duration_seconds (site)
    
    Gauges:
    - crawler_active_jobs
    - crawler_queue_length
    - crawler_items_in_dlq
    - crawler_circuit_breaker_state (site, state)
    
    Custom:
    - success_rate (current: success / (success + failed))
    - error_rate_by_type
    - average_retries_per_item
    """
    
    def __init__(self):
        self.request_counter = Counter(...)
        self.request_duration = Histogram(...)
        self.active_jobs = Gauge(...)
        # ... more metrics
    
    def record_request(self, site_id, status, duration):
        """Record HTTP request"""
        
    def record_item_processed(self, site_id, status, duration):
        """Record item processing"""
        
    def record_error(self, site_id, error_type):
        """Record error occurrence"""
```

**Metric Dashboard** (for visualization):

```
┌──────────────────────────────────────────────────────────────┐
│ Web Crawler Monitoring Dashboard                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Active Jobs: 3                Success Rate: 94.2%            │
│ Total Items: 1,245           Avg Latency: 2.3s             │
│ Errors: 72                   Circuit Breaker: CLOSED        │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Site Performance:                                            │
│                                                              │
│ chunjinkorea.com:                                           │
│   Success: 450/480 (93.8%)   Avg time: 2.1s               │
│   Errors: 15 (timeout:8, 429:4, parsing:3)                │
│                                                              │
│ freemold.net:                                              │
│   Success: 380/395 (96.2%)   Avg time: 1.8s               │
│   Errors: 9 (404:5, timeout:4)                            │
│                                                              │
│ onehago.com:                                               │
│   Success: 315/370 (85.1%)   Avg time: 3.2s               │
│   Errors: 48 (429:20, timeout:15, parsing:13)             │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Error Breakdown:                Error Recovery:             │
│                                                              │
│ Timeout: 27 (37.5%)          Retries Attempted: 156        │
│ Rate Limit (429): 24 (33.3%) Retries Successful: 84 (54%)  │
│ Parsing: 16 (22.2%)          DLQ Items: 12                 │
│ 404: 5 (6.9%)                                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Structured Logging

**Log Format** (JSON):

```json
{
  "timestamp": "2025-01-28T10:45:32.123Z",
  "level": "INFO",
  "logger": "ChungjinCrawler",
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "event": "item_processed",
  "site_id": "chunjin",
  "page_num": 5,
  "item_id": "idx_960",
  "status": "success",
  "duration_ms": 2340,
  "attempts": 1,
  "metadata": {
    "product_name": "50ml Bottle",
    "images_count": 5,
    "specs_count": 8
  }
}
```

**Log Levels**:

- **ERROR**: Unrecoverable errors, circuit breaker trips, DLQ additions
- **WARN**: Transient errors (will retry), slow responses, missing data
- **INFO**: Job progress, milestones, completion, page transitions
- **DEBUG**: Request details, parsing steps, selector attempts
- **TRACE**: Raw HTML chunks, full responses (for development)

### Health Check Service

**Endpoint**: `GET /api/crawler/health`

```json
{
  "status": "healthy",
  "timestamp": "2025-01-28T10:45:32Z",
  "uptime_seconds": 86400,
  "sites": {
    "chunjin": {
      "status": "healthy",
      "last_crawl": "2025-01-28T10:30:00Z",
      "circuit_breaker": "CLOSED",
      "error_rate_1h": 0.06,
      "response_time_p95_ms": 3200
    },
    "freemold": {
      "status": "degraded",
      "last_crawl": "2025-01-28T09:45:00Z",
      "circuit_breaker": "HALF_OPEN",
      "error_rate_1h": 0.15,
      "response_time_p95_ms": 5100
    },
    "onehago": {
      "status": "healthy",
      "last_crawl": "2025-01-28T10:40:00Z",
      "circuit_breaker": "CLOSED",
      "error_rate_1h": 0.08,
      "response_time_p95_ms": 3800
    }
  },
  "active_jobs": 2,
  "queue_depth": 15,
  "dlq_items": 8
}
```

### Alert Rules

```yaml
alert_rules:
  high_error_rate:
    condition: error_rate > 20% in 10 minutes
    severity: CRITICAL
    action: notify_ops, page_oncall
  
  circuit_breaker_open:
    condition: circuit_breaker.state == "OPEN"
    severity: CRITICAL
    action: notify_ops, automatic_investigation
  
  slow_responses:
    condition: p95_latency > 10s for 15 minutes
    severity: WARNING
    action: notify_ops, increase_timeouts
  
  dlq_accumulation:
    condition: dlq_items > 100 in 1 hour
    severity: WARNING
    action: notify_ops, trigger_review
  
  job_stuck:
    condition: job.in_progress_duration > 24 hours
    severity: WARNING
    action: notify_ops, suggest_manual_intervention
```

---

## Scalability Design

### Horizontal Scaling Strategy

```
┌─────────────────────────────────────────────────────┐
│ Crawler Instance Pool (3+ instances)               │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Instance 1              Instance 2                 │
│ ┌──────────────┐        ┌──────────────┐          │
│ │ ChungjinCr.  │        │ FreemoldCr.  │          │
│ │ (chunjin)    │        │ (freemold)   │          │
│ └──────────────┘        └──────────────┘          │
│                                                     │
│                Instance 3                          │
│                ┌──────────────┐                    │
│                │ OneHagoCr.   │                    │
│                │ (onehago)    │                    │
│                └──────────────┘                    │
│                                                     │
└─────────────────────────────────────────────────────┘
         ↓              ↓              ↓
┌─────────────────────────────────────────────────────┐
│ Shared Resources                                    │
├─────────────────────────────────────────────────────┤
│ • PostgreSQL (job state)                           │
│ • Redis (rate limiter, cache)                      │
│ • S3/Blob (downloaded data)                        │
└─────────────────────────────────────────────────────┘
```

### Concurrency Model

```python
class CrawlerPool:
    """
    Concurrent crawler execution with resource management:
    
    Configuration:
    - max_concurrent_jobs: 5 (global limit)
    - max_concurrent_per_site: 1 (rate limiting)
    - max_concurrent_requests: 10 (connection pool)
    - queue_strategy: FIFO with priority
    """
    
    def __init__(self, max_jobs=5, max_per_site=1):
        self.job_queue = asyncio.Queue()
        self.active_jobs = {}  # job_id → task
        self.site_semaphores = {}  # site_id → Semaphore
        self.max_concurrent_jobs = max_jobs
        self.max_concurrent_per_site = max_per_site
    
    async def submit_job(self, job_config):
        """Queue job for execution"""
        
    async def _process_queue(self):
        """Worker: dequeue and execute jobs"""
        
    async def _execute_job(self, job_config):
        """Execute single job with concurrency limits"""
```

**Queue Configuration**:

```python
# Priority-based queue
queue_rules = {
    "priority": {
        "incremental": 3,    # Resume jobs have higher priority
        "full": 2,           # Full crawls
        "validation": 1      # Data validation crawls
    },
    "fair_allocation": {
        "per_site_max_concurrent": 1,  # One job per site at a time
        "allow_different_sites": True   # But allow parallel across sites
    }
}
```

### Rate Limiting Strategy

```python
class RateLimiter:
    """
    Per-domain rate limiting to prevent blocking
    
    Configuration:
    {
        "chunjinkorea.com": {
            "requests_per_second": 0.5,  # Max 1 request per 2 seconds
            "burst_size": 2,             # Allow small bursts
            "backoff_multiplier": 2.0    # Double wait on 429
        },
        "freemold.net": {
            "requests_per_second": 1.0,
            "burst_size": 3,
            "backoff_multiplier": 1.5
        }
    }
    """
    
    async def acquire(self, domain):
        """Wait until request is allowed for domain"""
        # Uses token bucket algorithm
```

### Resource Pooling

```python
class ResourcePool:
    """Reusable resource management"""
    
    - HTTP session pool (aiohttp.ClientSession)
    - Browser instance pool (Playwright)
    - Connection pool (max 10 concurrent)
    - Memory limits per crawler (500MB)
    
    Benefits:
    - Reduced startup overhead
    - Efficient resource utilization
    - Graceful degradation under load
```

---

## State Management

### Job Lifecycle

```
┌─────────────┐
│  CREATED    │ (Initial state, configuration validated)
│  (0 items)  │
└──────┬──────┘
       ↓
┌─────────────────────┐
│  PENDING            │ (Queued, waiting for execution)
│  (0/N items)        │
└──────┬──────────────┘
       ↓
┌─────────────────────┐
│  IN_PROGRESS        │ (Running)
│  (M/N items)        │
└──────┬──────────────┘
       ├─ PAUSED ──────┐ (Explicit pause, state saved)
       │               │
       └─→ RESUMED ────┘
       │
       ├─ CANCELLED ──┐ (Cancelled by user, cleanup)
       │              │
       └─→ ABORTED ───┘
       │
       └─ COMPLETED ────┐ (Success, all items processed)
                        │
                   ┌────┘
       ┌──────────────────────┐
       │  COMPLETED_WITH_ERRORS│ (Partial success, some in DLQ)
       │  (M/N items success)  │
       └──────────────────────┘
       
       OR
       
       ├─ FAILED ──────────────┐ (Failed, unable to complete)
       │ (permanent error)      │
       └───────────────────────┘
```

### Data Validation During Crawling

```python
class DataValidator:
    """
    Multi-level validation strategy:
    
    Level 1: Extraction Validation
    - Required fields present
    - Type correctness
    - Format validation (URL, email, etc.)
    
    Level 2: Business Logic Validation
    - Price > 0
    - Product name not generic
    - Images accessible
    
    Level 3: Consistency Validation
    - No duplicate entries
    - Referential integrity
    - Data freshness check
    
    Level 4: Comparison Validation (Incremental updates)
    - Compare with previous crawl
    - Flag significant changes
    - Track historical versions
    """
    
    def validate_item(self, item, schema):
        """Validate single item"""
        
    def get_validation_errors(self):
        """Get detailed validation report"""
        
    def flag_warnings(self, item):
        """Flag non-fatal issues (missing optional fields, etc.)"""
```

---

## Implementation Roadmap

### Phase 1: Core Foundation (Weeks 1-2)

**Goals**: Build essential components with error handling

- [ ] RetryableHTTPClient with exponential backoff
- [ ] ErrorRecoveryManager with classification logic
- [ ] StateTracker with database persistence
- [ ] Basic structured logging setup
- [ ] Unit tests (80%+ coverage)

**Output**: Core libraries ready for integration

### Phase 2: Site-Specific Crawlers (Weeks 3-4)

**Goals**: Implement crawlers for each website

- [ ] ChungjinCrawler (build on existing code)
- [ ] FreemoldCrawler
- [ ] OneHagoCrawler
- [ ] ParsingEngine with selector framework
- [ ] Integration tests per site

**Output**: Three functional site crawlers

### Phase 3: Orchestration & Scaling (Weeks 5-6)

**Goals**: Multi-job coordination and scalability

- [ ] CrawlerOrchestrator
- [ ] Job queue and task scheduling
- [ ] Rate limiting per domain
- [ ] Connection pooling
- [ ] Concurrency tests

**Output**: Production-ready orchestration layer

### Phase 4: Monitoring & Operations (Weeks 7-8)

**Goals**: Observability and operational tools

- [ ] Prometheus metrics collection
- [ ] Dashboard API
- [ ] Health check endpoints
- [ ] Alert configuration
- [ ] Runbook documentation

**Output**: Full observability stack

### Phase 5: Advanced Features (Weeks 9+)

**Goals**: Reliability improvements and automation

- [ ] Circuit breaker pattern
- [ ] Dead letter queue processing
- [ ] Automatic recovery strategies
- [ ] Performance optimization
- [ ] Load testing and capacity planning

**Output**: Production-hardened system

---

## Directory Structure

```
/crawler_system/
├── core/
│   ├── __init__.py
│   ├── base_crawler.py           # Abstract crawler class
│   ├── http_client.py            # RetryableHTTPClient
│   ├── error_manager.py          # ErrorRecoveryManager
│   ├── state_tracker.py          # State persistence
│   ├── parsing_engine.py         # ParsingEngine
│   └── circuit_breaker.py        # CircuitBreaker
│
├── crawlers/
│   ├── __init__.py
│   ├── chungjin_crawler.py       # ChungjinCrawler
│   ├── freemold_crawler.py       # FreemoldCrawler
│   ├── onehago_crawler.py        # OneHagoCrawler
│   └── configs/
│       ├── chungjin_config.yaml
│       ├── freemold_config.yaml
│       └── onehago_config.yaml
│
├── orchestration/
│   ├── __init__.py
│   ├── orchestrator.py           # CrawlerOrchestrator
│   ├── job_queue.py              # Job scheduling
│   ├── rate_limiter.py           # Rate limiting
│   └── resource_pool.py          # Resource management
│
├── monitoring/
│   ├── __init__.py
│   ├── metrics.py                # Prometheus metrics
│   ├── logger.py                 # Structured logging
│   ├── health_check.py           # Health checks
│   └── alerts.py                 # Alert management
│
├── models/
│   ├── __init__.py
│   ├── job.py                    # Job state model
│   ├── item.py                   # Item model
│   ├── error.py                  # Error models
│   └── metrics.py                # Metric models
│
├── api/
│   ├── __init__.py
│   ├── routes.py                 # API endpoints
│   ├── schemas.py                # Request/response schemas
│   └── middleware.py             # Auth, logging middleware
│
├── database/
│   ├── __init__.py
│   ├── models.py                 # SQLAlchemy models
│   ├── migrations/
│   └── seed.sql                  # Initial data
│
├── tests/
│   ├── unit/
│   │   ├── test_http_client.py
│   │   ├── test_error_manager.py
│   │   ├── test_state_tracker.py
│   │   └── test_parsing_engine.py
│   ├── integration/
│   │   ├── test_chungjin_crawler.py
│   │   ├── test_freemold_crawler.py
│   │   └── test_onehago_crawler.py
│   ├── e2e/
│   │   └── test_full_workflow.py
│   └── fixtures/
│       └── sample_html/
│
├── scripts/
│   ├── run_crawler.py            # CLI entry point
│   ├── scheduler.py              # Scheduled execution
│   └── migrate.py                # Database migration
│
├── config/
│   ├── __init__.py
│   ├── settings.py               # Global settings
│   ├── logging.yaml              # Logging config
│   └── alerts.yaml               # Alert rules
│
├── requirements.txt
├── setup.py
├── README.md
└── docs/
    ├── ARCHITECTURE.md
    ├── API_REFERENCE.md
    ├── OPERATIONAL_GUIDE.md
    └── TROUBLESHOOTING.md
```

---

## Key Implementation Considerations

### 1. Database Schema

**Critical tables for state management**:

```sql
CREATE TABLE crawl_jobs (
    id UUID PRIMARY KEY,
    site_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    config JSONB NOT NULL,
    stats JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP NULL,
    INDEX (site_id, status),
    INDEX (created_at DESC)
);

CREATE TABLE crawl_items (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    item_id VARCHAR(100),
    url TEXT,
    status VARCHAR(20),
    retries_count INT DEFAULT 0,
    last_error JSONB,
    crawled_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX (job_id, status),
    INDEX (job_id, created_at DESC)
);

CREATE TABLE dead_letter_queue (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES crawl_jobs(id),
    item_id VARCHAR(100),
    error_type VARCHAR(50),
    error_details JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX (job_id),
    INDEX (error_type),
    INDEX (created_at DESC)
);
```

### 2. Configuration Management

**Site-specific configuration example**:

```yaml
# crawlers/configs/chungjin_config.yaml
site:
  id: chunjin
  domain: chungjinkorea.com
  base_url: http://chungjinkorea.com/kr

categories:
  - name: Bottle
    url: http://chungjinkorea.com/kr/product/list.php?part_idx=1
    pages: 68
  - name: Jar
    url: http://chungjinkorea.com/kr/product/list.php?part_idx=2
    pages: 4

selectors:
  product_list: "a[href*='view.php']"
  product_name: "img[src*='goodsImages']"
  price: [".price", ".product-price"]
  description: ".description"
  pagination_next: ".paging-next"

validators:
  product_name:
    required: true
    type: string
  price:
    required: false
    type: float

retry_policy:
  max_retries: 3
  base_delay: 1
  max_delay: 60
  backoff_multiplier: 2

rate_limiting:
  requests_per_second: 0.5
  burst_size: 2

timeouts:
  request: 30
  page_load: 10
  overall_job: 3600
```

### 3. Error Notifications

**Alert channels**:

```python
class NotificationManager:
    """Send alerts on critical failures"""
    
    channels = {
        "CRITICAL": ["pagerduty", "slack", "email"],
        "WARNING": ["slack", "email"],
        "INFO": ["slack"]
    }
    
    def notify(self, severity, message, metadata=None):
        """Route notification to appropriate channels"""
```

---

## Testing Strategy

### Unit Tests

```python
# test_retry_logic.py
def test_exponential_backoff_calculation():
    """Verify backoff formula: base * (2^attempt) + jitter"""
    
def test_circuit_breaker_state_transitions():
    """Verify CLOSED → OPEN → HALF_OPEN → CLOSED"""
    
def test_error_classification():
    """Verify error type detection"""
```

### Integration Tests

```python
# test_chungjin_integration.py
async def test_crawl_single_product():
    """Test end-to-end product crawling"""
    
async def test_pagination_handling():
    """Test page navigation with grouping"""
    
async def test_retry_on_transient_error():
    """Test recovery from temporary failure"""
```

### Load Tests

```python
# test_load.py
async def test_concurrent_crawling():
    """Test with 5+ concurrent jobs"""
    
async def test_rate_limiting():
    """Verify rate limits are enforced"""
    
async def test_resource_cleanup():
    """Verify no resource leaks under load"""
```

---

## Conclusion

This design blueprint provides a **production-grade foundation** for a robust, observable, and scalable web crawler agent system. Key strengths:

✅ **Reliability**: Exponential backoff, circuit breaker, DLQ  
✅ **Observability**: Structured logging, metrics, dashboards  
✅ **Maintainability**: Modular design, clear separation of concerns  
✅ **Scalability**: Concurrent execution, rate limiting, resource pooling  
✅ **Extensibility**: Easy to add new sites with configuration-driven approach

Implementation should follow the phased roadmap, starting with core components and progressively adding orchestration, monitoring, and advanced features.

