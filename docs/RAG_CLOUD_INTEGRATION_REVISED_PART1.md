# RAG Cloud Integration Enhanced Plan - PART 1

**Date**: 2025-10-20
**Status**: 수정 중 (사용자 피드백 반영)
**Target**: OneDrive + Google Drive 공유폴더 싱크

---

## 1️⃣ OneDrive/Google Drive 공유폴더 싱크 메커니즘

### 기술 개요: Virtual File System (VFS) 패턴

```
┌─────────────────────────────┐
│  사용자: 공유폴더 선택      │
│  ("Sales/Invoices" 폴더)   │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  OAuth2 인증 플로우        │
│  • Microsoft Graph API      │
│  • Google Drive API v3      │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  Virtual File System        │
│  • 클라우드 파일 = 로컬 파일│
│  • 캐싱 + 중복방지          │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  Delta API 동기화           │
│  • 변경사항만 추적          │
│  • 웹훅 + 주기적 확인      │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  로컬 임시 저장소           │
│  /local_sync/invoices/      │
│  ├─ 2025-10-20_invoice.pdf  │
│  ├─ 2025-10-21_receipt.xlsx │
│  └─ 중복 감지 (SHA256)      │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  문서 처리 파이프라인       │
│  → PaddleOCR-VL 또는        │
│  → Docling 파서             │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│  Qdrant 임베딩              │
│  1,587개 벡터 추가/갱신    │
└─────────────────────────────┘
```

### 1.1 OneDrive 구현 (Microsoft Graph API)

**인증 흐름**:
```python
# 1. 사용자가 "Sales 폴더 싱크" 버튼 클릭
# 2. OAuth2 redirect → Microsoft 로그인
# 3. 권한 승인 (Files.Read)
# 4. Access Token + Refresh Token 저장 (encrypted)

class OneDriveVFS:
    def __init__(self, access_token):
        self.graph = GraphClient(access_token)

    async def select_folder(self, folder_path: str):
        """사용자가 선택한 폴더 ID 가져오기"""
        # OneDrive: /drive/root/children?$search="Sales"
        # 결과: {"id": "folder_123", "name": "Sales"}

    async def list_files_delta(self, folder_id: str, delta_token=None):
        """변경사항 추적 (Delta Query)"""
        # 첫 호출: /me/drive/items/folder_123/delta
        # 응답: files[], delta_token="abc123"
        # 다음 호출: delta_token 사용 → 변경분만 반환

        # 효과: 1000개 파일 중 5개 추가 → 5개만 다운로드
        # 첫 sync: 5분 | 다음 sync: 10초

    async def download_file(self, file_id, local_path):
        """파일 다운로드 (캐시 확인)"""
        # SHA256 계산 후 DB 확인
        # 이미 있으면: 스킵
        # 새 파일: 다운로드 → 처리 파이프라인
```

**특징**:
- Delta API: 변경사항만 동기화 (효율적)
- Webhook: 파일 변경 시 즉시 알림 (실시간)
- 웹훅 유효기간: 3일 → Celery Beat로 자동 갱신

### 1.2 Google Drive 구현

**차이점**:
- Delta Query 없음 → `files().list()` + `modifiedTime` 비교
- Push Notification: 최대 7일 유효
- Changes API: 상세 변경사항 조회

```python
class GoogleDriveVFS:
    async def list_files_incremental(self, folder_id, last_sync_time):
        """마지막 동기화 이후 변경파일만"""
        # query: f"parents='{folder_id}' and modifiedTime > '{last_sync_time}'"
        # 결과: 변경된 파일만 반환
```

### 1.3 로컬 캐시 구조

```
/app/data/local_sync/
├─ cloud_sources.db (SQLite, 메타데이터)
│  ├─ source_id: "onedrive_sales"
│  ├─ folder_path: "/drive/root/Sales"
│  ├─ last_sync: "2025-10-20 10:30:00"
│  └─ delta_token: "abc123xyz"
│
├─ onedrive_sales/
│  ├─ 2025-10-20_invoice_001.pdf (50KB)
│  ├─ 2025-10-20_receipt_002.xlsx (120KB)
│  └─ .cache/
│      └─ file_hashes.json
│         {
│           "50kb_hash_abc123": "2025-10-20_invoice_001.pdf",
│           "120kb_hash_xyz": "2025-10-20_receipt_002.xlsx"
│         }
│
└─ gdrive_invoices/
   ├─ [similar structure]
```

**캐시 동작**:
1. 파일 다운로드 후 SHA256 계산
2. DB에 저장: `{file_hash: file_path}`
3. 다음 동기화: 해시 비교 → 중복 감지
4. 새 파일만 처리 파이프라인으로 진행

---

## 2️⃣ 고급 처리 vs 기본 처리 상세 정의

### 2.1 파일 타입별 처리 전략

**거래명세서 예시**:
```
기본 처리 (Tesseract):
├─ 텍스트만 추출: "OOO 주식회사 2025년 10월 거래명세서"
├─ 표 구조 손실: 행과 열이 섞임
├─ 정확도: 70%
└─ 시간: 2초

고급 처리 (PaddleOCR-VL):
├─ JSON 구조화 출력:
│  {
│    "header": {"거래처": "OOO", "날짜": "2025-10-20"},
│    "table": {
│      "columns": ["품목", "수량", "단가", "합계"],
│      "rows": [
│        {"품목": "용기 50ml", "수량": 1000, "단가": 500, "합계": 500000}
│      ]
│    },
│    "summary": {"합계": "500,000원", "세금": "50,000원"}
│  }
├─ 정확도: 95%
└─ 시간: 15초 (GPU) / 40초 (CPU)
```

### 2.2 자동 선택 로직

```python
class ProcessingStrategy:
    async def select_processor(self, file_info):
        """파일명/내용 분석 후 처리 방식 결정"""

        # 규칙 1: 파일명 키워드 감지
        if "거래명세서" in file_info.name or "송장" in file_info.name:
            return "advanced"  # PaddleOCR-VL

        # 규칙 2: MIME 타입 분석
        if file_info.mime == "application/pdf":
            # PDF 첫 페이지 미리보기
            preview = await extract_preview(file_info)

            # 규칙 3: 표/이미지 비율
            if has_complex_tables(preview):
                return "advanced"  # Docling
            elif has_dense_text(preview):
                return "basic"  # PyMuPDF

        # 기타: Excel/이미지
        if file_info.mime == "application/vnd.ms-excel":
            return "advanced"  # openpyxl (자동)

        return "basic"  # 기본값
```

### 2.3 비용-효율 분석

```yaml
월별 처리 가정: 1000개 파일/월

시나리오 1: 모두 기본 처리
├─ 처리 시간: 1000 × 2초 = 2000초 (33분)
├─ 정확도: 70%
├─ 수동 보정: 300 × 5분 = 1500분 (25시간 = $1,250)
└─ 총 비용: $250 (인프라) + $1,250 (인력) = $1,500

시나리오 2: 선별 고급 (30% 고급, 70% 기본) ⭐ 권장
├─ 처리 시간: 700×2초 + 300×15초 = 5400초 (90분)
├─ 정확도: 85%
├─ 수동 보정: 150 × 5분 = 750분 (12.5시간 = $625)
└─ 총 비용: $250 (인프라) + $625 (인력) = $875 (-$625 절감)

시나리오 3: 모두 고급 처리
├─ 처리 시간: 1000 × 15초 = 15000초 (250분)
├─ 정확도: 95%
├─ 수동 보정: 50 × 5분 = 250분 = $125
└─ 총 비용: $500 (GPU) + $125 (인력) = $625 (-$875 절감, +$250 인프라)
```

**권장**: **시나리오 2 (선별 고급)**
- 정확도 85% (충분함)
- 비용 $875/월 (가장 효율적)
- ROI: $1,500 → $875 (42% 절감)

---

## 3️⃣ Webhook 동기화 검증

### 3.1 기술적 가능성: ✅ 100% 가능

**OneDrive Webhook**:
```
1. Cloud Source 생성 시 Subscription API 호출
   POST /subscriptions
   {
     "changeType": "created,updated,deleted",
     "notificationUrl": "https://yourapp.com/webhooks/onedrive",
     "resource": "/drive/root/children",
     "expirationDateTime": "2025-10-23T10:30:00Z"  // 3일 유효
   }

2. 파일 변경 감지
   → Webhook 수신 (1-5초 이내)
   → Celery 작업 생성 (우선도: high)
   → 파일 다운로드 + 처리

3. Webhook 유효기간 관리
   → Celery Beat: 매일 오전 10시 renewal
   → 자동 갱신 (사용자 개입 없음)
```

**Google Drive Push Notification**:
```
1. Watch Request
   POST /files/{folderId}/watch
   {
     "id": "channel_unique_id",
     "type": "web_hook",
     "address": "https://yourapp.com/webhooks/gdrive",
     "expiration": 604800000  // 7일 (ms)
   }

2. 이벤트 수신
   → notification 헤더: 파일 변경
   → Changes API 호출하여 상세 조회
   → 처리 파이프라인 실행
```

### 3.2 Fallback 메커니즘 (안정성)

```python
class SyncManager:
    async def sync_with_fallback(self, source_id):
        """Webhook 우선, 실패시 주기적 동기화로 fallback"""

        # Primary: Webhook (이미 수신)
        if webhook_received:
            return await process_webhook_changes()

        # Secondary: Periodic Sync (1시간마다)
        if last_sync_time < now - 1hour:
            return await perform_delta_sync()

        # Tertiary: Full Resync (하루에 1회, 3am)
        if is_3am_and_not_synced_today():
            return await full_resync()  # 검증용
```

**상태별 동기화**:
- Webhook 정상: 실시간 (1-5초)
- Webhook 실패 1회: 주기적 (1시간)
- Webhook 실패 3회: Full Resync (1일)
- Webhook 실패 7회: 사용자 알림 + 수동 개입

---

## 4️⃣ PostgreSQL 스키마 (데이터 레이어)

### 4.1 클라우드 소스 관리

```sql
-- 1. Cloud Sources (연결된 클라우드 폴더)
CREATE TABLE cloud_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    provider VARCHAR(50),  -- 'onedrive', 'gdrive', 'dropbox'
    provider_folder_id VARCHAR(500),  -- OneDrive: folder_id, GDrive: folder_id
    provider_folder_path VARCHAR(500),  -- "/drive/root/Sales"
    local_sync_path VARCHAR(500),  -- "/app/data/local_sync/onedrive_sales"
    display_name VARCHAR(255),  -- "Sales Invoices"

    -- OAuth 토큰 (암호화됨)
    access_token_encrypted BYTEA,
    refresh_token_encrypted BYTEA,
    token_expiry TIMESTAMP,

    -- 동기화 상태
    last_sync TIMESTAMP,
    last_sync_status VARCHAR(50),  -- 'success', 'failed', 'partial'
    delta_token VARCHAR(1000),  -- OneDrive Delta Token

    -- Webhook 관리
    webhook_id VARCHAR(500),  -- Subscription/Watch ID
    webhook_expiry TIMESTAMP,
    webhook_status VARCHAR(50),  -- 'active', 'expired', 'failed'

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, provider, provider_folder_id)
);

-- 2. 처리 작업 추적
CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cloud_source_id UUID REFERENCES cloud_sources(id),
    file_id VARCHAR(500),  -- 클라우드 제공자의 파일 ID
    file_name VARCHAR(500),
    file_size BIGINT,
    file_hash VARCHAR(64),  -- SHA256

    processor_type VARCHAR(50),  -- 'basic', 'advanced', 'auto'
    status VARCHAR(50),  -- 'pending', 'processing', 'completed', 'failed'
    error_message TEXT,

    -- 처리 결과
    qdrant_doc_id VARCHAR(255),  -- Qdrant document ID
    qdrant_vector_count INT,
    processing_time_ms INT,
    confidence_score FLOAT,

    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- 3. 동기화 이벤트 (감사 로그)
CREATE TABLE sync_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cloud_source_id UUID REFERENCES cloud_sources(id),
    event_type VARCHAR(50),  -- 'webhook_received', 'sync_started', 'file_added', 'error'
    event_data JSONB,  -- 추가 정보 저장
    status VARCHAR(50),

    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4.2 API 엔드포인트 상세

```python
# 1. 클라우드 소스 추가
POST /api/v1/cloud-sources/authorize
Body: {
    "provider": "onedrive",  # or "gdrive"
    "display_name": "Sales Invoices"
}
Response: {
    "authorization_url": "https://login.microsoftonline.com/...",
    "state": "random_state_token"
}

# 2. OAuth 콜백
GET /api/v1/cloud-sources/authorize/callback?code=...&state=...
→ 토큰 저장 (암호화)
→ 폴더 선택 UI로 리다이렉트

# 3. 폴더 선택
POST /api/v1/cloud-sources/{source_id}/folders
Body: { "folder_id": "folder_123" }
→ 로컬 캐시 디렉토리 생성
→ 첫 동기화 시작

# 4. 동기화 상태
GET /api/v1/cloud-sources/{source_id}/status
Response: {
    "source_id": "...",
    "last_sync": "2025-10-20T10:30:00Z",
    "file_count": 1234,
    "sync_status": "success",
    "webhook_status": "active",
    "next_renewal": "2025-10-23T10:30:00Z"
}

# 5. 수동 동기화
POST /api/v1/cloud-sources/{source_id}/sync
Response: { "task_id": "...", "status": "started" }

# 6. Webhook 핸들러
POST /webhooks/onedrive
Headers: {
    "client-state": "...encrypted_state...",
    "x-ms-webhook-authentic": "..."
}
→ Celery 작업 생성 (high priority)

POST /webhooks/gdrive
Headers: { "x-goog-channel-id": "...", "x-goog-channel-token": "..." }
→ Changes API 호출 후 처리
```

---

## 5️⃣ 보안 & 암호화 전략

### 5.1 토큰 저장 (PostgreSQL pgcrypto)

```python
from cryptography.fernet import Fernet
import os

class TokenEncryption:
    def __init__(self):
        self.cipher = Fernet(os.getenv("TOKEN_ENCRYPTION_KEY"))

    async def encrypt_token(self, token: str) -> bytes:
        """OAuth 토큰 암호화"""
        return self.cipher.encrypt(token.encode())

    async def decrypt_token(self, encrypted: bytes) -> str:
        """암호화된 토큰 복호화"""
        return self.cipher.decrypt(encrypted).decode()

# 저장 시
encrypted_token = await encryption.encrypt_token(access_token)
await db.execute(
    "UPDATE cloud_sources SET access_token_encrypted = %s WHERE id = %s",
    [encrypted_token, source_id]
)

# 사용 시
encrypted = await db.fetchval(
    "SELECT access_token_encrypted FROM cloud_sources WHERE id = %s",
    [source_id]
)
access_token = await encryption.decrypt_token(encrypted)
```

### 5.2 Webhook 검증

```python
# OneDrive Subscription 검증
import hashlib
import hmac

async def validate_onedrive_webhook(request):
    """Microsoft Graph Webhook 서명 검증"""
    client_state = request.headers.get("client-state")
    signature = request.headers.get("x-ms-webhook-authentic")

    # 저장된 상태와 비교
    expected_signature = hmac.new(
        os.getenv("WEBHOOK_SECRET").encode(),
        msg=client_state.encode(),
        digestmod=hashlib.sha256
    ).digest()

    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Invalid webhook signature")

# Google Drive Push Notification 검증
async def validate_gdrive_webhook(request):
    """Google Drive Push Notification 검증"""
    channel_id = request.headers.get("x-goog-channel-id")
    channel_token = request.headers.get("x-goog-channel-token")

    # 저장된 channel 정보와 비교
    stored = await db.fetchrow(
        "SELECT * FROM cloud_sources WHERE webhook_id = %s",
        [channel_id]
    )

    if not stored or stored['webhook_status'] != 'active':
        raise ValueError("Invalid channel")
```

---

## 6️⃣ 에러 처리 & 재시도 전략

### 6.1 OAuth 토큰 갱신

```python
async def get_valid_token(source_id: str) -> str:
    """토큰 만료 확인 후 필요시 갱신"""
    source = await db.fetchrow(
        "SELECT * FROM cloud_sources WHERE id = %s",
        [source_id]
    )

    if source['token_expiry'] < datetime.utcnow() + timedelta(minutes=5):
        # 토큰 갱신 필요
        new_token = await refresh_oauth_token(
            provider=source['provider'],
            refresh_token=decrypt(source['refresh_token_encrypted'])
        )

        await db.execute(
            "UPDATE cloud_sources SET access_token_encrypted = %s, token_expiry = %s WHERE id = %s",
            [encrypt(new_token), datetime.utcnow() + timedelta(hours=1), source_id]
        )

        return new_token

    return decrypt(source['access_token_encrypted'])

async def refresh_oauth_token(provider: str, refresh_token: str):
    """Provider별 토큰 갱신"""
    if provider == "onedrive":
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data={
                    "client_id": os.getenv("ONEDRIVE_CLIENT_ID"),
                    "client_secret": os.getenv("ONEDRIVE_CLIENT_SECRET"),
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                }
            ) as resp:
                data = await resp.json()
                return data['access_token']
```

### 6.2 Webhook 재시도 로직

```python
@celery_app.task(bind=True, max_retries=5)
async def process_webhook_changes(self, source_id: str, changes: dict):
    """Webhook 변경사항 처리 (자동 재시도)"""
    try:
        for file_change in changes['value']:
            await download_and_process_file(source_id, file_change)

        await db.execute(
            "UPDATE sync_events SET status = %s WHERE cloud_source_id = %s",
            ['completed', source_id]
        )

    except Exception as exc:
        # Exponential backoff: 1s → 2s → 4s → 8s → 16s
        retry_delay = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=retry_delay)
```

---

## 다음: PART 2 (PaddleOCR-VL + RBAC)

PART 1 보강 완료:
- ✅ 기술 개요
- ✅ OneDrive/Google Drive 구현
- ✅ 캐시 구조
- ✅ 처리 전략 + 비용 분석
- ✅ Webhook 검증
- ✅ **PostgreSQL 스키마** (신규)
- ✅ **API 엔드포인트** (신규)
- ✅ **보안 & 암호화** (신규)
- ✅ **에러 처리** (신규)

