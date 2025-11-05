---
name: web-crawler-pipeline
description: Unified web crawling pipeline - complete automation from authentication to data publishing with checkpoint and rollback support
license: MIT
metadata:
  version: "1.0.0"
  domain: "data-engineering"
  triggers:
    - "web crawling"
    - "data pipeline"
    - "crawler automation"
    - "data validation"
    - "data integration"
---

# Web Crawler Pipeline Skill

**Version**: 1.0.0
**Purpose**: 통합 웹 크롤링 파이프라인 - 인증 처리부터 데이터 발행까지 완전 자동화
**Architecture**: Progressive Disclosure with Checkpoint & Rollback

---

## 🎯 Skill Overview

### What This Skill Does

이 Skill은 웹 크롤링부터 데이터 검증, 통합, 발행까지의 전체 파이프라인을 자동화합니다.

**Key Features**:
- ✅ **Authentication Handling**: Credential 있는/없는 사이트 모두 지원
- ✅ **Multi-Stage Validation**: 3단계 검증 (L1, L2, L3)
- ✅ **Auto Deduplication**: 중복 제거 자동화
- ✅ **Relationship Mapping**: 데이터 관계 자동 매핑
- ✅ **Checkpoint & Rollback**: 각 단계별 저장점과 복구 기능
- ✅ **Quality Scoring**: 데이터 품질 자동 점수화

### When to Use This Skill

- 새로운 웹사이트 크롤링 프로젝트 시작 시
- 기존 크롤링 데이터 품질 개선 필요 시
- 인증이 필요한 사이트 크롤링 시
- 대규모 데이터 통합 작업 시

---

## 📋 Commands

### Primary Commands

#### `init` - 크롤링 프로젝트 초기화
```bash
Skill: web-crawler-pipeline init --site onehago.com --auth none
Skill: web-crawler-pipeline init --site freemold.net --auth cookie
```

**Parameters**:
- `--site`: 크롤링 대상 사이트 도메인
- `--auth`: 인증 방식 (`none`, `cookie`, `session`, `oauth`)
- `--output-dir`: 출력 디렉토리 (optional, default: `data/{site}/`)

**Output**: 프로젝트 구조 생성, 설정 파일 초기화

---

#### `crawl` - 웹 크롤링 실행
```bash
Skill: web-crawler-pipeline crawl --site onehago.com --mode full
Skill: web-crawler-pipeline crawl --site freemold.net --mode incremental --auth-file cookies.json
```

**Parameters**:
- `--site`: 크롤링 대상 사이트
- `--mode`: 크롤링 모드 (`full`, `incremental`, `sample`)
- `--workers`: Worker 수 (default: 8)
- `--auth-file`: 인증 파일 경로 (credential 있는 사이트용)
- `--resume`: 이전 크롤링 이어하기 (default: false)

**Output**:
- Raw JSONL 파일: `data/{site}/crawled/raw/`
- Progress 파일: `data/{site}/crawled/progress.json`
- Log: `data/{site}/crawled/logs/crawl_{timestamp}.log`

**Authentication Handling**:
```python
# None authentication
if auth_type == "none":
    crawler = SimpleCrawler(site)

# Cookie-based authentication
elif auth_type == "cookie":
    cookies = load_cookies(auth_file)
    crawler = AuthenticatedCrawler(site, cookies=cookies)

# Session-based authentication
elif auth_type == "session":
    session = create_authenticated_session(auth_file)
    crawler = SessionCrawler(site, session=session)

# OAuth authentication
elif auth_type == "oauth":
    token = get_oauth_token(auth_file)
    crawler = OAuthCrawler(site, token=token)
```

---

#### `validate` - 데이터 검증 실행
```bash
Skill: web-crawler-pipeline validate --site onehago.com --level L1
Skill: web-crawler-pipeline validate --site onehago.com --level all
```

**Parameters**:
- `--site`: 검증 대상 사이트
- `--level`: 검증 레벨 (`L1`, `L2`, `L3`, `all`)
- `--auto-fix`: 자동 수정 활성화 (default: false)
- `--report`: 보고서 생성 (default: true)

**Validation Levels**:

**L1 - Schema Validation** (Post-Crawl):
- JSON 스키마 준수 확인
- 필수 필드 존재 확인
- 데이터 타입 검증
- **Checkpoint**: `data/{site}/crawled/validated_L1/`

**L2 - Completeness Check** (Pre-Integration):
- 필드 완전성 검증 (image_urls, specifications 등)
- 데이터 품질 점수 계산
- 중복 제거 확인
- **Checkpoint**: `data/{site}/crawled/validated_L2/`

**L3 - Relationship Integrity** (Post-Integration):
- 참조 무결성 검증
- Orphan 레코드 확인
- 관계 일관성 체크
- **Checkpoint**: `data/{site}/integrated/validated_L3/`

**Output**:
- Validation Report: `data/{site}/validation_reports/validation_{level}_{timestamp}.json`
- Issues List: `data/{site}/validation_reports/issues_{level}.json`

---

#### `dedupe` - 중복 제거
```bash
Skill: web-crawler-pipeline dedupe --site onehago.com --strategy priority
```

**Parameters**:
- `--site`: 대상 사이트
- `--strategy`: 중복 제거 전략 (`priority`, `merge`, `latest`)
- `--key`: 중복 판단 키 (default: `product_id`)

**Deduplication Strategies**:

**Priority Strategy** (Default):
```python
PRIORITY_RULES = [
    'has_images',          # 1순위: 이미지 있음
    'field_completeness',  # 2순위: 필드 완전성
    'crawled_at DESC'      # 3순위: 최신 데이터
]
```

**Merge Strategy**:
```python
MERGE_RULES = {
    'product_name': 'longest',
    'image_urls': 'union',
    'specifications': 'merge',
    'company_info': 'most_complete'
}
```

**Output**:
- Deduplicated JSONL: `data/{site}/crawled/cleaned/all_products_clean.jsonl`
- Deduplication Report: `data/{site}/integration_reports/dedupe_{timestamp}.json`

---

#### `integrate` - 데이터 통합
```bash
Skill: web-crawler-pipeline integrate --site onehago.com --normalize
```

**Parameters**:
- `--site`: 통합 대상 사이트
- `--normalize`: 스키마 정규화 활성화 (default: true)
- `--map-relationships`: 관계 매핑 활성화 (default: true)

**Integration Pipeline**:

**Stage 1: Schema Normalization**
```python
# 필드명 표준화
FIELD_MAPPING = {
    'prod_id': 'product_id',
    'prod_name': 'product_name',
    'imgs': 'image_urls',
    'img_cnt': 'image_count'
}

# 데이터 타입 통일
TYPE_CONVERSION = {
    'product_id': 'string',
    'image_count': 'integer',
    'crawled_at': 'datetime'
}

# 중첩 구조 정규화
NESTED_FIELDS = {
    'specifications': ['code', 'capacity', 'size', 'moq', 'material', 'origin'],
    'company_info': ['name', 'phone', 'fax', 'email', 'contact_person']
}
```

**Stage 2: Relationship Mapping**
```python
# Product → Images (1:N)
map_product_images(products, images)

# Product → Category (N:1)
map_product_categories(products, categories)

# Product → Company (N:1)
map_product_companies(products, companies)
```

**Output**:
- Integrated JSONL: `data/{site}/integrated/all_products_integrated.jsonl`
- Relationship Maps:
  - `data/{site}/integrated/relationships/product_images_map.json`
  - `data/{site}/integrated/relationships/product_category_map.json`
  - `data/{site}/integrated/relationships/product_company_map.json`

---

#### `publish` - 데이터 발행
```bash
Skill: web-crawler-pipeline publish --site onehago.com --target production
```

**Parameters**:
- `--site`: 발행 대상 사이트
- `--target`: 발행 타겟 (`staging`, `production`)
- `--version`: 버전 태그 (optional)

**Publish Checks**:
1. ✅ L3 Validation 통과 확인
2. ✅ Quality Score ≥ 95 확인
3. ✅ Relationship Integrity 100% 확인
4. ✅ Critical Issues = 0 확인

**Output**:
- Published Data: `data/{site}/published/{target}/all_products_v{version}.jsonl`
- Publish Report: `data/{site}/published/publish_report_{timestamp}.json`
- Metadata: `data/{site}/published/metadata.json`

---

### Secondary Commands

#### `status` - 파이프라인 상태 확인
```bash
Skill: web-crawler-pipeline status --site onehago.com
```

**Output**: 전체 파이프라인 진행 상황, 각 단계 완료 여부, 이슈 요약

---

#### `rollback` - 특정 단계로 롤백
```bash
Skill: web-crawler-pipeline rollback --site onehago.com --stage dedupe
```

**Parameters**:
- `--site`: 롤백 대상 사이트
- `--stage`: 롤백할 단계 (`crawl`, `validate-L1`, `dedupe`, `validate-L2`, `integrate`, `validate-L3`)

---

#### `repair` - 자동 수정
```bash
Skill: web-crawler-pipeline repair --site onehago.com --issue missing_images
```

**Parameters**:
- `--site`: 수정 대상 사이트
- `--issue`: 수정할 이슈 타입
- `--dry-run`: 미리보기 모드 (default: false)

**Repairable Issues**:
- `missing_images`: 이미지 없는 제품 재크롤링
- `invalid_urls`: 유효하지 않은 URL 수정
- `schema_errors`: 스키마 오류 자동 수정
- `orphaned_records`: Orphan 레코드 처리

---

#### `report` - 종합 보고서 생성
```bash
Skill: web-crawler-pipeline report --site onehago.com --format html
```

**Parameters**:
- `--site`: 보고서 대상 사이트
- `--format`: 보고서 형식 (`json`, `html`, `pdf`)

**Report Sections**:
1. Executive Summary
2. Pipeline Stages Status
3. Data Quality Metrics
4. Validation Results
5. Integration Statistics
6. Issues and Recommendations

---

## 🔄 Complete Pipeline Flow

### Detailed Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1: INITIALIZATION                                    │
└─────────────────────────────────────────────────────────────┘
    ↓
    • Create project structure
    • Initialize configuration
    • Detect authentication requirements
    • Setup logging and monitoring
    ↓
    CHECKPOINT: init_complete.json
    ↓

┌─────────────────────────────────────────────────────────────┐
│  STAGE 2: AUTHENTICATION (if required)                      │
└─────────────────────────────────────────────────────────────┘
    ↓
    IF auth_type != "none":
        • Load authentication credentials
        • Create authenticated session
        • Validate authentication
        • Store session tokens
    ↓
    CHECKPOINT: auth_session.pkl
    ↓

┌─────────────────────────────────────────────────────────────┐
│  STAGE 3: WEB CRAWLING                                      │
└─────────────────────────────────────────────────────────────┘
    ↓
    • Launch worker pool (N workers)
    • Distribute URLs across workers
    • Extract HTML content
    • Parse product data
    • Extract image URLs
    • Handle pagination
    • Retry failed requests (3x with exponential backoff)
    • Save progress every 50 products
    ↓
    OUTPUT: data/{site}/crawled/raw/
    CHECKPOINT: crawl_progress.json
    ↓

┌─────────────────────────────────────────────────────────────┐
│  STAGE 4: VALIDATION L1 (Schema Validation)                 │
└─────────────────────────────────────────────────────────────┘
    ↓
    For each record:
        • Check JSON schema compliance
        • Verify mandatory fields exist
        • Validate data types
        • Check URL format
    ↓
    IF validation_failed:
        → Generate issue report
        → Auto-fix if possible
        → Re-validate
    ↓
    OUTPUT: data/{site}/crawled/validated_L1/
    REPORT: validation_L1_report.json
    CHECKPOINT: validate_L1_complete.json
    ↓

┌─────────────────────────────────────────────────────────────┐
│  STAGE 5: DEDUPLICATION                                     │
└─────────────────────────────────────────────────────────────┘
    ↓
    • Group records by product_id
    • Apply deduplication strategy (priority/merge)
    • Resolve field conflicts
    • Calculate quality scores
    • Keep best record for each product
    ↓
    STATS:
        - Input records: X
        - Unique products: Y
        - Duplicates removed: X - Y
        - Merge conflicts: Z
    ↓
    OUTPUT: data/{site}/crawled/cleaned/all_products_clean.jsonl
    REPORT: dedupe_report.json
    CHECKPOINT: dedupe_complete.json
    ↓

┌─────────────────────────────────────────────────────────────┐
│  STAGE 6: VALIDATION L2 (Completeness Check)                │
└─────────────────────────────────────────────────────────────┘
    ↓
    For each unique product:
        • Check field completeness
        • Calculate quality score
        • Verify image URLs accessibility
        • Check specifications completeness
    ↓
    QUALITY SCORE FORMULA:
        score = (
            has_product_name * 20 +
            has_images * 30 +
            has_specifications * 25 +
            has_company_info * 15 +
            has_valid_urls * 10
        ) / 100
    ↓
    IF quality_score < 70:
        → Flag as low quality
        → Add to repair queue
    ↓
    OUTPUT: data/{site}/crawled/validated_L2/
    REPORT: validation_L2_report.json
    CHECKPOINT: validate_L2_complete.json
    ↓

┌─────────────────────────────────────────────────────────────┐
│  STAGE 7: INTEGRATION                                       │
└─────────────────────────────────────────────────────────────┘
    ↓
    STEP 7.1: Schema Normalization
        • Standardize field names
        • Unify data types
        • Normalize nested structures
        • Apply field mappings
    ↓
    STEP 7.2: Relationship Mapping
        • Extract images → Create image entities
        • Map product_id ↔ image_id (1:N)
        • Map product_id ↔ category_id (N:1)
        • Map product_id ↔ company_id (N:1)
        • Generate relationship maps
    ↓
    STEP 7.3: Enhancement
        • Add metadata (crawled_at, version, source)
        • Calculate derived fields
        • Enrich with external data (if available)
    ↓
    OUTPUT:
        - data/{site}/integrated/all_products_integrated.jsonl
        - data/{site}/integrated/relationships/*.json
    REPORT: integration_report.json
    CHECKPOINT: integrate_complete.json
    ↓

┌─────────────────────────────────────────────────────────────┐
│  STAGE 8: VALIDATION L3 (Relationship Integrity)            │
└─────────────────────────────────────────────────────────────┘
    ↓
    • Check referential integrity
    • Detect orphaned records
    • Validate relationship cardinality
    • Check circular references
    • Verify foreign key constraints
    ↓
    QUERIES:
        - Orphaned images: SELECT * FROM images
          WHERE product_id NOT IN (SELECT product_id FROM products)

        - Invalid categories: SELECT * FROM products
          WHERE category_id NOT IN (SELECT category_id FROM categories)

        - Image count mismatch: SELECT * FROM products
          WHERE image_count != (SELECT COUNT(*) FROM images
                                WHERE images.product_id = products.product_id)
    ↓
    IF relationship_errors > 0:
        → Generate error report
        → Block publish
        → Trigger repair workflow
    ↓
    OUTPUT: data/{site}/integrated/validated_L3/
    REPORT: validation_L3_report.json
    CHECKPOINT: validate_L3_complete.json
    ↓

┌─────────────────────────────────────────────────────────────┐
│  STAGE 9: PRE-PUBLISH CHECKS                                │
└─────────────────────────────────────────────────────────────┘
    ↓
    • Verify L3 validation passed
    • Check quality score ≥ 95
    • Verify relationship integrity = 100%
    • Confirm critical issues = 0
    • Review completeness rate ≥ 98%
    ↓
    IF any_check_failed:
        → Block publish
        → Generate blocker report
        → Exit with error
    ↓
    ALL CHECKS PASSED ✅
    ↓

┌─────────────────────────────────────────────────────────────┐
│  STAGE 10: PUBLISH                                          │
└─────────────────────────────────────────────────────────────┘
    ↓
    • Create version tag (v{YYYYMMDD}_{sequence})
    • Copy integrated data to publish directory
    • Generate metadata file
    • Create publish manifest
    • Archive previous version
    • Update production symlink
    ↓
    OUTPUT:
        - data/{site}/published/{target}/all_products_v{version}.jsonl
        - data/{site}/published/metadata.json
        - data/{site}/published/manifest.json
    REPORT: publish_report.json
    ↓

┌─────────────────────────────────────────────────────────────┐
│  STAGE 11: POST-PUBLISH VERIFICATION                        │
└─────────────────────────────────────────────────────────────┘
    ↓
    • Verify file integrity (checksum)
    • Confirm record count matches
    • Test data accessibility
    • Generate final report
    ↓
    ✅ PIPELINE COMPLETE
```

---

## 🔧 Configuration

### Site Configuration File

Location: `data/{site}/config.json`

```json
{
  "site": {
    "domain": "onehago.com",
    "name": "Onehago Packaging",
    "base_url": "https://www.onehago.com"
  },
  "authentication": {
    "type": "none",
    "credentials_file": null,
    "session_duration": null
  },
  "crawling": {
    "workers": 8,
    "timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 5,
    "rate_limit": 100,
    "user_agent": "Mozilla/5.0 (compatible; DataPipeline/1.0)"
  },
  "validation": {
    "L1": {
      "enabled": true,
      "auto_fix": true,
      "mandatory_fields": ["product_id", "product_name", "product_url"]
    },
    "L2": {
      "enabled": true,
      "min_quality_score": 70,
      "completeness_threshold": 0.8
    },
    "L3": {
      "enabled": true,
      "referential_integrity": true,
      "orphan_check": true
    }
  },
  "deduplication": {
    "strategy": "priority",
    "key": "product_id",
    "priority_rules": [
      "has_images",
      "field_completeness",
      "crawled_at DESC"
    ]
  },
  "integration": {
    "normalize_schema": true,
    "map_relationships": true,
    "field_mapping": {
      "prod_id": "product_id",
      "prod_name": "product_name"
    }
  },
  "publish": {
    "target": "production",
    "version_format": "v{YYYYMMDD}_{seq}",
    "min_quality_score": 95,
    "min_completeness": 0.98
  }
}
```

---

## 📊 Quality Metrics

### Automated Quality Scoring

```python
def calculate_quality_score(product: dict) -> float:
    """Calculate comprehensive quality score (0-100)"""

    score = 0.0

    # Product Name (20 points)
    if product.get('product_name'):
        score += 20
        if len(product['product_name']) > 10:
            score += 5  # Bonus for detailed name

    # Images (30 points)
    image_urls = product.get('image_urls', [])
    if image_urls:
        score += 20
        if len(image_urls) >= 3:
            score += 10  # Bonus for multiple images

    # Specifications (25 points)
    specs = product.get('specifications', {})
    if specs:
        filled_specs = sum(1 for v in specs.values() if v)
        spec_ratio = filled_specs / max(len(specs), 1)
        score += 25 * spec_ratio

    # Company Info (15 points)
    company = product.get('company_info', {})
    if company:
        filled_company = sum(1 for v in company.values() if v)
        company_ratio = filled_company / max(len(company), 1)
        score += 15 * company_ratio

    # Valid URLs (10 points)
    if product.get('product_url') and is_valid_url(product['product_url']):
        score += 10

    return min(score, 100.0)
```

---

## 🚨 Error Handling & Recovery

### Checkpoint System

각 단계 완료 시 checkpoint 파일 생성:

```json
{
  "checkpoint_id": "validate_L1_complete",
  "timestamp": "2025-01-25T10:30:00Z",
  "stage": "validate-L1",
  "status": "completed",
  "input_records": 245804,
  "output_records": 245804,
  "errors": 0,
  "warnings": 125,
  "duration_seconds": 320,
  "can_rollback": true,
  "next_stage": "dedupe"
}
```

### Rollback Mechanism

```python
def rollback(site: str, target_stage: str):
    """Rollback pipeline to specific stage"""

    # 1. Load checkpoint
    checkpoint = load_checkpoint(site, target_stage)

    # 2. Remove all data after checkpoint
    cleanup_stages_after(checkpoint)

    # 3. Restore checkpoint state
    restore_checkpoint_data(checkpoint)

    # 4. Reset progress tracking
    reset_progress(site, target_stage)

    # 5. Log rollback operation
    log_rollback(site, target_stage, reason="manual_rollback")
```

### Auto-Repair

```python
AUTO_REPAIR_RULES = {
    'missing_images': {
        'action': 'recrawl_product',
        'retry_count': 3,
        'fallback': 'flag_for_manual_review'
    },
    'invalid_url': {
        'action': 'normalize_url',
        'retry_count': 1,
        'fallback': 'remove_record'
    },
    'schema_error': {
        'action': 'apply_schema_mapping',
        'retry_count': 1,
        'fallback': 'quarantine_record'
    },
    'orphaned_image': {
        'action': 'find_parent_product',
        'retry_count': 2,
        'fallback': 'remove_orphan'
    }
}
```

---

## 📈 Performance Optimization

### Parallel Processing

```python
# Multi-worker crawling
with ProcessPoolExecutor(max_workers=8) as executor:
    futures = [
        executor.submit(crawl_worker, worker_id, product_range)
        for worker_id, product_range in enumerate(distribute_work(products, 8))
    ]
    results = [f.result() for f in as_completed(futures)]

# Batch validation
def batch_validate(records: List[dict], batch_size: int = 1000):
    """Validate records in batches for better performance"""
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        validate_batch(batch)
```

### Caching

```python
# URL deduplication cache
url_cache = set()

# Schema validation cache
schema_cache = {}

# Relationship lookup cache
relationship_cache = {
    'product_images': {},
    'product_category': {},
    'product_company': {}
}
```

---

## 🔐 Security & Authentication

### Supported Authentication Types

#### 1. None (Public Sites)
```python
crawler = SimpleCrawler(site_url)
```

#### 2. Cookie-based (Freemold.net style)
```python
# Load cookies from file
cookies = load_cookies('data/freemold/cookies.json')

# Create authenticated session
session = requests.Session()
for cookie in cookies:
    session.cookies.set(cookie['name'], cookie['value'])

crawler = AuthenticatedCrawler(site_url, session=session)
```

#### 3. Session-based (Login flow)
```python
# Perform login
session = requests.Session()
login_data = {
    'username': credentials['username'],
    'password': credentials['password']
}
response = session.post(f"{site_url}/login", data=login_data)

# Verify authentication
if response.status_code == 200:
    crawler = SessionCrawler(site_url, session=session)
```

#### 4. OAuth (API-based)
```python
# Get OAuth token
token = get_oauth_token(
    client_id=credentials['client_id'],
    client_secret=credentials['client_secret']
)

# Create authenticated client
headers = {'Authorization': f'Bearer {token}'}
crawler = OAuthCrawler(site_url, headers=headers)
```

### Credential Storage

**Location**: `data/{site}/credentials/`

**Supported Formats**:
- `cookies.json`: Cookie-based authentication
- `session.pkl`: Session persistence
- `token.json`: OAuth tokens
- `.env`: Environment variables

**Security**:
- Credentials 디렉토리는 `.gitignore`에 포함
- 암호화 옵션 제공 (AES-256)
- 자동 만료 체크 및 갱신

---

## 📖 Usage Examples

### Example 1: Simple Crawl (No Auth)

```bash
# Initialize project
Skill: web-crawler-pipeline init --site onehago.com --auth none

# Run full pipeline
Skill: web-crawler-pipeline crawl --site onehago.com --mode full --workers 8
Skill: web-crawler-pipeline validate --site onehago.com --level all --auto-fix
Skill: web-crawler-pipeline dedupe --site onehago.com --strategy priority
Skill: web-crawler-pipeline integrate --site onehago.com
Skill: web-crawler-pipeline publish --site onehago.com --target production

# Check final status
Skill: web-crawler-pipeline status --site onehago.com
Skill: web-crawler-pipeline report --site onehago.com --format html
```

### Example 2: Authenticated Crawl (Cookie-based)

```bash
# Initialize with authentication
Skill: web-crawler-pipeline init --site freemold.net --auth cookie

# Provide credentials (manual step - copy cookies.json to data/freemold/credentials/)

# Run crawl with authentication
Skill: web-crawler-pipeline crawl --site freemold.net --mode full \
  --auth-file data/freemold/credentials/cookies.json \
  --workers 4

# Continue with pipeline
Skill: web-crawler-pipeline validate --site freemold.net --level all
Skill: web-crawler-pipeline dedupe --site freemold.net
Skill: web-crawler-pipeline integrate --site freemold.net
Skill: web-crawler-pipeline publish --site freemold.net
```

### Example 3: Incremental Update

```bash
# Run incremental crawl (only new products)
Skill: web-crawler-pipeline crawl --site onehago.com --mode incremental --resume

# Validate only new data
Skill: web-crawler-pipeline validate --site onehago.com --level L1

# Merge with existing data
Skill: web-crawler-pipeline dedupe --site onehago.com --strategy merge

# Publish update
Skill: web-crawler-pipeline publish --site onehago.com --target staging
```

### Example 4: Repair and Republish

```bash
# Identify issues
Skill: web-crawler-pipeline validate --site onehago.com --level all

# Auto-repair specific issue
Skill: web-crawler-pipeline repair --site onehago.com --issue missing_images

# Re-validate
Skill: web-crawler-pipeline validate --site onehago.com --level L2

# Republish
Skill: web-crawler-pipeline publish --site onehago.com --target production
```

---

## 🎓 Best Practices

### 1. Always Initialize First
```bash
# ✅ Good
Skill: web-crawler-pipeline init --site example.com --auth none
Skill: web-crawler-pipeline crawl --site example.com

# ❌ Bad
Skill: web-crawler-pipeline crawl --site example.com  # No init!
```

### 2. Validate at Each Stage
```bash
# ✅ Good - Validate after each major step
Skill: web-crawler-pipeline crawl ...
Skill: web-crawler-pipeline validate --level L1
Skill: web-crawler-pipeline dedupe ...
Skill: web-crawler-pipeline validate --level L2

# ❌ Bad - Skip validation
Skill: web-crawler-pipeline crawl ...
Skill: web-crawler-pipeline dedupe ...
Skill: web-crawler-pipeline publish ...  # No validation!
```

### 3. Use Checkpoints for Long Operations
```bash
# Enable resume for long crawls
Skill: web-crawler-pipeline crawl --site example.com --resume

# If interrupted, resume from checkpoint
Skill: web-crawler-pipeline crawl --site example.com --resume
```

### 4. Test on Staging First
```bash
# ✅ Good - Test on staging
Skill: web-crawler-pipeline publish --site example.com --target staging
# Verify staging data...
Skill: web-crawler-pipeline publish --site example.com --target production

# ❌ Bad - Direct to production
Skill: web-crawler-pipeline publish --site example.com --target production
```

### 5. Monitor Quality Scores
```bash
# Generate reports regularly
Skill: web-crawler-pipeline report --site example.com --format html

# Check quality before publish
Skill: web-crawler-pipeline validate --site example.com --level all
```

---

## 🔍 Troubleshooting

### Common Issues

#### Issue 1: Authentication Failures
```
Error: Authentication failed for site freemold.net
```

**Solution**:
1. Verify credentials file exists: `data/freemold/credentials/cookies.json`
2. Check cookie expiration
3. Re-export fresh cookies from browser
4. Retry with `--auth-file` parameter

#### Issue 2: Validation Failures
```
Error: L2 validation failed - 1250 products with quality score < 70
```

**Solution**:
1. Review validation report: `data/{site}/validation_reports/validation_L2_report.json`
2. Run repair: `Skill: web-crawler-pipeline repair --site {site} --issue low_quality`
3. Re-validate: `Skill: web-crawler-pipeline validate --site {site} --level L2`

#### Issue 3: Duplicate Records After Dedupe
```
Warning: Still 500 duplicate records after deduplication
```

**Solution**:
1. Check dedupe strategy: Try `--strategy merge` instead of `priority`
2. Verify unique key: Confirm `product_id` is truly unique
3. Manual inspection: Review duplicates in dedupe report

#### Issue 4: Publish Blocked
```
Error: Publish blocked - Quality score 92.5 < required 95.0
```

**Solution**:
1. Lower quality threshold (temporary): Edit `data/{site}/config.json`
2. Fix quality issues: Run `repair` for specific issues
3. Re-integrate: `Skill: web-crawler-pipeline integrate --site {site}`
4. Retry publish

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-25 | Initial release with full pipeline |
| - | - | - Authentication support (none, cookie, session, OAuth) |
| - | - | - 3-level validation (L1, L2, L3) |
| - | - | - Checkpoint & rollback system |
| - | - | - Auto-repair capabilities |

---

**Author**: Data Pipeline Team
**Maintainer**: RAG Enterprise
**License**: MIT
**Last Updated**: 2025-01-25
