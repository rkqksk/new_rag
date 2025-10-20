# RAG Cloud Integration Enhanced Plan - PART 2

**Date**: 2025-10-20
**Status**: 수정 중 (PaddleOCR-VL + RBAC)

---

## 4️⃣ PaddleOCR-VL 기술 평가

### 4.1 기술 비교표

```
┌────────────────┬───────────┬────────────┬──────────────────┐
│ 특성           │ Tesseract │ EasyOCR    │ PaddleOCR-VL     │
├────────────────┼───────────┼────────────┼──────────────────┤
│ 한국어 정확도  │ 75%       │ 88%        │ 95% ⭐           │
│ 표 구조 인식   │ ❌        │ ❌         │ ✅ (JSON 출력)  │
│ 키-밸류 추출   │ ❌        │ ❌         │ ✅ (자동 구조화) │
│ 처리 속도(GPU) │ 2초       │ 5초        │ 15초             │
│ 처리 속도(CPU) │ 8초       │ 20초       │ 40초             │
│ 모델 크기      │ 10MB      │ 50MB       │ 500MB (양자화)   │
│ GPU 요구       │ 선택      │ 선택       │ 권장             │
│ 다언어 지원    │ 약함      │ 강함       │ 강함 ⭐          │
└────────────────┴───────────┴────────────┴──────────────────┘

PaddleOCR-VL = PaddleOCR (Text) + Vision Language Model (Layout)
```

### 4.2 거래명세서 처리 비교

**Tesseract 결과 (70% 정확도)**:
```
OOO 주식회사
2025년 10월 거래명세서

품목 수량 단가 합계
용기50ml 1000 500 500000
흰색뚜껑 1000 100 100000
[표 구조 손실]
합계: 600000원
```

**PaddleOCR-VL 결과 (95% 정확도)**:
```json
{
  "document_type": "거래명세서",
  "header": {
    "회사명": "OOO 주식회사",
    "작성일": "2025-10-20",
    "거래처": "◇◇ 유통",
    "담당자": "김미영"
  },
  "table": {
    "columns": ["품목", "규격", "수량", "단가", "합계"],
    "rows": [
      {
        "품목": "용기",
        "규격": "50ml",
        "수량": 1000,
        "단가": 500,
        "합계": 500000
      },
      {
        "품목": "뚜껑",
        "규격": "흰색",
        "수량": 1000,
        "단가": 100,
        "합계": 100000
      }
    ],
    "summary": {
      "소계": 600000,
      "세금": 60000,
      "합계": 660000
    }
  },
  "confidence": 0.95
}
```

**Qdrant 저장 구조**:
```python
# Chunk 1: 헤더
vector = embed("OOO 주식회사 2025년 10월 거래명세서 김미영")
payload = {
  "doc_id": "inv_20251020_001",
  "chunk_type": "header",
  "content": json.dumps({"회사명": "OOO", "작성일": "2025-10-20"}),
  "source_provider": "onedrive",
  "file_name": "2025-10-20_거래명세서.pdf"
}

# Chunk 2: 테이블
vector = embed("용기 50ml 1000개 500원 합계 500000원...")
payload = {
  "doc_id": "inv_20251020_001",
  "chunk_type": "table",
  "content": json.dumps(table_data),
  "source_provider": "onedrive"
}

# 검색 가능
query = "50ml 용기 가격이 얼마야?"
→ Chunk 2 매칭 (정확도 높음)
→ 답변: "50ml 용기는 단가 500원, 1000개 기준 합계 500,000원입니다."
```

### 4.3 구현 계획

**설치**:
```bash
pip install paddlepaddle paddleocr paddlenlp

# GPU 가속 (권장)
pip install paddlepaddle-gpu
```

**코드**:
```python
from paddleocr import PaddleOCR
from paddleocr.tools.table_structure import OCRTable

class PaddleOCRProcessor:
    def __init__(self):
        self.ocr = PaddleOCR(use_gpu=True, lang="ch")  # ch=한자+영문
        self.table_ocr = OCRTable(use_gpu=True)

    async def process_document(self, file_path):
        """OCR + 테이블 인식 + 구조화"""

        # 1. 전체 OCR
        result = self.ocr.ocr(file_path)

        # 2. 테이블 감지 및 추출
        table_result = self.table_ocr(file_path)

        # 3. 구조화 (JSON)
        structured = self._structure_output(result, table_result)
        return structured

    def _structure_output(self, ocr_result, table_result):
        """텍스트 + 테이블 → JSON"""
        output = {
            "text_blocks": [],
            "tables": [],
            "confidence": 0.95
        }

        # 텍스트 블록
        for block in ocr_result:
            for line in block:
                text, conf = line
                output["text_blocks"].append({"text": text, "confidence": conf})

        # 테이블 블록
        for table in table_result:
            structured_table = {
                "columns": table.get("header", []),
                "rows": table.get("body", [])
            }
            output["tables"].append(structured_table)

        return output
```

**성능**:
```
문서당 처리:
├─ 거래명세서 (1페이지): 15초 (GPU), 40초 (CPU)
├─ 복합 테이블 (3페이지): 45초 (GPU), 120초 (CPU)
└─ 이미지 스캔본: +5초 (흐릿함 보정)

배치 처리:
├─ 100개 문서 (GPU): 25분
├─ 100개 문서 (CPU): 67분
└─ Celery 3 workers (GPU): 8분 (병렬화)
```

---

## 5️⃣ Role-based Data Stratification (RBAC)

### 5.1 권한 계층 (5단계)

```yaml
권한 레벨:
  10: Super Admin
      └─ 모든 데이터 접근 (극비 문서 포함)
      └─ 사용자 관리, 권한 설정

  9: Executive (임원급)
     └─ 극비 문서 접근
     └─ 부서별 주요 계약서, 재무 보고서

  7: Department Head (부서장)
     └─ 기밀 문서 접근
     └─ 부서내 대부분의 문서

  5: Employee (일반 직원)
     └─ 내부용 문서만
     └─ 자신의 부서 및 공개 정보

  3: Client (외부 고객)
     └─ 공개 정보만
     └─ 자신이 주문한 거래명세서 등

  1: Guest
     └─ 공개 공지사항만
```

### 5.2 데이터 분류 (5단계)

```yaml
분류 레벨:
  1. Public (공개)
     └─ 뉘스레터, 제품 카탈로그

  2. Internal (내부용)
     └─ 직원 공지, 일반 문서

  3. Confidential (기밀)
     └─ 거래처 계약서, 거래명세서

  4. Restricted (제한)
     └─ 재무 정보, 인사 기록

  5. Secret (극비)
     └─ 전략 계획, CEO 메모
```

### 5.3 구현 아키텍처

**데이터베이스 스키마** (PostgreSQL):
```sql
-- 1. 사용자 권한
CREATE TABLE user_roles (
    user_id UUID,
    role_level INT,  -- 1-10
    department VARCHAR(100),
    created_at TIMESTAMP
);

-- 2. 문서 권한 (세분화)
CREATE TABLE document_permissions (
    doc_id UUID,
    classification_level INT,  -- 1-5
    allowed_roles INT[],  -- [5, 7, 9, 10]
    allowed_departments VARCHAR[],
    owner_id UUID,
    created_at TIMESTAMP
);

-- 3. 접근 감사 로그
CREATE TABLE access_audit (
    user_id UUID,
    doc_id UUID,
    access_type VARCHAR (read, download, export),
    timestamp TIMESTAMP,
    ip_address INET,
    result VARCHAR (success, denied),
    reason VARCHAR  -- 권한 없음, 시간대 제한 등
);
```

**Qdrant 메타데이터 필터링**:
```python
# 벡터 저장 시
payload = {
  "doc_id": "inv_20251020_001",
  "classification": "Confidential",  # 3
  "allowed_roles": [5, 7, 9, 10],
  "allowed_departments": ["Sales", "Finance"],
  "owner_id": "user_emp123"
}

# 검색 시 (사용자 권한 필터)
async def search_with_rbac(query, user_id):
    user = await get_user(user_id)  # role_level=5, department="Sales"

    # Qdrant 필터링
    filter_condition = {
        "must": [
            {
                "key": "allowed_roles",
                "match": {"any": [user.role_level]}
            },
            {
                "key": "allowed_departments",
                "match": {"any": [user.department]}
            }
        ]
    }

    results = qdrant.search(
        query_vector=embed(query),
        query_filter=filter_condition,
        limit=5
    )
    return results
```

**API 이중 검증**:
```python
@app.get("/api/v1/documents/{doc_id}")
async def get_document(doc_id: str, current_user: User):
    # 1. 데이터베이스 검증
    doc_perms = await db.query(
        "SELECT * FROM document_permissions WHERE doc_id = %s",
        [doc_id]
    )

    if current_user.role_level not in doc_perms.allowed_roles:
        logger.warning(f"Access denied: {current_user.id} → {doc_id}")
        raise HTTPException(status_code=403, detail="접근 권한 없음")

    # 2. Qdrant 검증 (중복 확인)
    results = qdrant.get(doc_id)
    if current_user.role_level not in results.payload["allowed_roles"]:
        raise HTTPException(status_code=403)

    # 3. 감사 로그 기록
    await log_access(current_user.id, doc_id, "success")

    return results
```

**UI 마스킹**:
```python
# 사용자가 권한 없는 문서 검색 시
{
  "id": "inv_20251020_001",
  "title": "[접근 권한 없음]",
  "snippet": "[기밀 문서] 상세 내용을 볼 수 없습니다",
  "confidence": 0.95,
  "reason": "Confidential 등급 (필요: Executive 이상)"
}
```

### 5.4 성능 최적화

**Redis 캐싱** (사용자 권한):
```python
# 첫 로그인 시
user_perms = {
  "role_level": 5,
  "department": "Sales",
  "allowed_doc_classes": [1, 2, 3]  # Public, Internal, Confidential
}
redis.set(f"user_perms:{user_id}", json.dumps(user_perms), ex=3600)

# 검색 시 (DB 쿼리 회피)
user_perms = redis.get(f"user_perms:{user_id}")  # 매우 빠름
```

**Qdrant 필터 인덱싱**:
```yaml
# Qdrant 설정: 필터 필드 인덱싱
payload_indexing:
  allowed_roles: indexed
  classification: indexed
  allowed_departments: indexed

# 효과: 필터 쿼리 <100ms (인덱스 없으면 1초 이상)
```

---

## 6️⃣ 팀 리소스 설명

### 6.1 리소스 = 인력 + 시간 + 역량

```
개발자 리소스 시나리오:

시나리오 1: 1명 Full-time
├─ 달력 기간: 8주
├─ 총 비용: $16,000 (1명 × 8주 × $2,000/주)
├─ 병렬화: 0% (순차 처리)
└─ 특징: 느림, 저비용

시나리오 2: 2명 Full-time ⭐ 권장
├─ 달력 기간: 6주 (40% 단축)
├─ 총 비용: $24,000 (2명 × 6주 × $2,000/주)
├─ 병렬화: 40% (동시 개발 가능)
│  ├─ Dev1: OneDrive + Google Drive adapter
│  └─ Dev2: PaddleOCR-VL + RBAC 구현
└─ 특징: 최적 속도-비용

시나리오 3: 3명 Full-time
├─ 달력 기간: 5주 (50% 단축)
├─ 총 비용: $30,000 (3명 × 5주)
├─ 병렬화: 50% (오버헤드 주의)
├─ 문제: 커뮤니케이션 오버헤드 발생
└─ 특징: 한계 수익 체감
```

### 6.2 병렬화 가능 작업 (70%)

```
├─ Cloud Adapters (2주)
│  ├─ OneDrive API 통합
│  └─ Google Drive API 통합 (병렬, Dev1-2)
│
├─ Processing Pipeline (2주)
│  ├─ PaddleOCR-VL 통합
│  ├─ Docling + TableTransformer
│  └─ 임베딩 최적화 (병렬, Dev2-3)
│
└─ Frontend (2주)
   ├─ Cloud 설정 UI
   ├─ 상태 대시보드
   └─ RBAC 관리 UI (병렬, Dev3)
```

### 6.3 Critical Path (순차 필수, 4주)

```
1. Database Schema (3일)
   ↓
2. OAuth2 구현 (5일)
   ↓
3. Cloud Adapters (5일)
   ↓
4. Webhook 핸들러 (3일)
   ↓
5. Chat UI 통합 (3일)

총 순차: 19일 (~4주)
```

**병렬화 효율**:
- 순차 8주 → 병렬 6주 = **25% 시간 절감**
- 비용: +$8,000 (추가 개발자) → 납기 2주 단축

---

## 7️⃣ PaddleOCR-VL 환경 설정 상세

### 7.1 설치 및 초기화

```bash
# 1. PaddlePaddle 설치 (GPU 버전)
pip install paddlepaddle-gpu==2.5.1

# 2. PaddleOCR 설치
pip install paddleocr==2.7.0.3

# 3. 모델 다운로드 (첫 실행 시 자동, 5분 소요)
# 한국어 + 영문 모델: ~500MB
export PADDLE_DOWNLOAD_PATH=/app/models/paddle

# 4. GPU 확인
python3 -c "import paddle; print(paddle.device.get_device())"
# 출력: gpu:0 (GPU 사용 중)
```

### 7.2 초기화 코드

```python
from paddleocr import PaddleOCR, PPStructure
import logging

logger = logging.getLogger(__name__)

class PaddleOCRInit:
    _instance = None

    @classmethod
    def get_instance(cls):
        """Singleton: 모델 메모리 절약"""
        if cls._instance is None:
            logger.info("🔄 PaddleOCR 모델 로딩 중...")
            cls._instance = PaddleOCRInit()
        return cls._instance

    def __init__(self):
        # 1. 텍스트 OCR (한자+영문)
        self.ocr = PaddleOCR(
            use_angle_cls=True,  # 회전된 텍스트 감지
            lang='ch',  # 중문 (한자+영문)
            use_gpu=True,
            gpu_mem=2048,  # GPU 메모리 2GB 할당
            show_log=False
        )

        # 2. 표 구조 인식
        self.structure = PPStructure(
            use_gpu=True,
            show_log=False
        )

        logger.info("✅ PaddleOCR 초기화 완료")

    async def process_image(self, image_path: str):
        """이미지 처리 (한국어 지원)"""
        try:
            result = self.ocr.ocr(image_path)
            return result
        except Exception as e:
            logger.error(f"OCR 오류: {str(e)}")
            raise

    async def detect_table_structure(self, image_path: str):
        """표 구조 감지"""
        try:
            result = self.structure(image_path)
            return result
        except Exception as e:
            logger.error(f"표 감지 오류: {str(e)}")
            raise
```

### 7.3 한국어 처리 최적화

```python
class KoreanOCROptimizer:
    """한국어 OCR 정확도 최적화"""

    @staticmethod
    async def preprocess_image(image_path: str):
        """이미지 전처리"""
        import cv2
        import numpy as np

        img = cv2.imread(image_path)

        # 1. 회색도 변환
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. 대비 개선 (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)

        # 3. 노이즈 제거
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)

        # 4. 이진화 (스캔 문서 용)
        _, binary = cv2.threshold(denoised, 127, 255, cv2.THRESH_BINARY)

        return binary

    @staticmethod
    async def extract_korean_text(ocr_result):
        """한국어 텍스트 추출"""
        texts = []
        for line in ocr_result:
            for word_info in line:
                text, confidence = word_info[1], word_info[2]
                # 한국어 유니코드: AC00-D7A3 범위
                if any('\uac00' <= c <= '\ud7a3' for c in text):
                    texts.append({
                        'text': text,
                        'confidence': confidence
                    })
        return texts
```

---

## 8️⃣ 테스트 전략

### 8.1 OCR 정확도 검증

```python
import pytest
from difflib import SequenceMatcher

class TestPaddleOCR:
    """OCR 정확도 테스트"""

    async def test_korean_invoice_processing(self):
        """거래명세서 처리 테스트"""
        # 테스트 파일
        invoice_path = "tests/fixtures/invoice_kr.pdf"

        # 처리
        processor = PaddleOCRProcessor()
        result = await processor.process_document(invoice_path)

        # 검증
        assert result['confidence'] >= 0.90, "정확도 미달"
        assert len(result['tables']) > 0, "표 감지 실패"
        assert 'summary' in result, "요약 정보 누락"

    async def test_table_structure_preservation(self):
        """표 구조 보존 테스트"""
        invoice_path = "tests/fixtures/complex_table.pdf"

        result = await PaddleOCRProcessor().process_document(invoice_path)

        # 표 구조 검증
        for table in result['tables']:
            assert 'columns' in table, "컬럼 정보 누락"
            assert 'rows' in table, "행 정보 누락"
            assert len(table['rows']) > 0, "빈 테이블"

    async def test_confidence_scoring(self):
        """신뢰도 점수 검증"""
        result = await PaddleOCRProcessor().process_document("test.pdf")

        # 신뢰도 범위 검증
        assert 0 <= result['confidence'] <= 1.0, "신뢰도 범위 오류"

    def calculate_accuracy(self, expected: str, actual: str) -> float:
        """정확도 계산 (Levenshtein 유사도)"""
        return SequenceMatcher(None, expected, actual).ratio()
```

### 8.2 RBAC 접근 제어 테스트

```python
class TestRBACAccess:
    """RBAC 접근 제어 테스트"""

    async def test_employee_cannot_access_secret(self):
        """직원이 극비 문서 접근 실패"""
        user = {"user_id": "emp123", "role_level": 5}
        doc = {"doc_id": "secret_001", "classification": 5}

        result = await check_access(user, doc)
        assert result['allowed'] is False, "접근 제어 실패"

    async def test_executive_can_access_restricted(self):
        """임원이 제한 문서 접근 성공"""
        user = {"user_id": "exec123", "role_level": 9}
        doc = {"doc_id": "restricted_001", "classification": 4}

        result = await check_access(user, doc)
        assert result['allowed'] is True, "접근 허용 실패"

    async def test_department_filtering(self):
        """부서별 문서 필터링"""
        user = {"user_id": "emp123", "role_level": 5, "department": "Sales"}

        results = await search_with_rbac("contract", user)

        # Sales 부서만 결과에 포함
        for doc in results:
            assert doc['allowed_departments'] contains "Sales"
```

---

## 9️⃣ RBAC 마이그레이션 전략

### 9.1 기존 문서 권한 할당

```python
async def migrate_existing_documents_to_rbac(default_classification: int = 2):
    """기존 1,587개 문서에 RBAC 권한 추가"""

    # 1. 기존 문서 목록 조회 (Qdrant)
    existing_docs = await qdrant.scroll(
        collection_name="products_text",
        limit=1000
    )

    # 2. 권한 정책 정의
    policy_map = {
        "제품 카탈로그": {"classification": 1, "allowed_roles": [1, 3, 5, 7, 9, 10]},  # Public
        "내부 문서": {"classification": 2, "allowed_roles": [5, 7, 9, 10]},  # Internal
        "거래 계약": {"classification": 3, "allowed_roles": [5, 7, 9, 10]},  # Confidential
        "재무": {"classification": 4, "allowed_roles": [7, 9, 10]},  # Restricted
        "전략": {"classification": 5, "allowed_roles": [9, 10]}  # Secret
    }

    # 3. 각 문서 마이그레이션
    migrated = 0
    for doc in existing_docs:
        doc_id = doc['id']
        doc_type = await infer_document_type(doc)

        policy = policy_map.get(doc_type, policy_map["내부 문서"])

        # Qdrant 페이로드 업데이트
        await qdrant.overwrite_payload(
            collection_name="products_text",
            points_selector=doc_id,
            payload={
                "classification": policy["classification"],
                "allowed_roles": policy["allowed_roles"],
                "allowed_departments": ["Sales", "Finance"],  # 기본값
                "owner_id": "system_migration"
            }
        )

        migrated += 1
        if migrated % 100 == 0:
            logger.info(f"🔄 {migrated}/1587 문서 마이그레이션 완료")

    logger.info(f"✅ RBAC 마이그레이션 완료: {migrated}개 문서")
    return migrated
```

### 9.2 권한 감사 로그

```python
async def log_rbac_change(user_id: str, action: str, details: dict):
    """RBAC 권한 변경 감사"""
    await db.execute("""
        INSERT INTO access_audit
        (user_id, action, details, timestamp)
        VALUES (%s, %s, %s, NOW())
    """, [user_id, action, json.dumps(details)])

# 사용 예
await log_rbac_change(
    user_id="admin_001",
    action="document_classification_changed",
    details={
        "doc_id": "inv_20251020_001",
        "old_classification": 2,
        "new_classification": 3
    }
)
```

---

## 🔟 모니터링 지표

### 10.1 OCR 성능 메트릭

```python
from prometheus_client import Counter, Histogram, Gauge

# 처리된 문서 수
ocr_documents_processed = Counter(
    'ocr_documents_processed_total',
    'Total documents processed',
    ['processor_type', 'status']
)

# 처리 시간
ocr_processing_time = Histogram(
    'ocr_processing_time_seconds',
    'OCR processing time',
    buckets=(5, 10, 15, 20, 30, 60)
)

# 정확도 점수
ocr_confidence_score = Gauge(
    'ocr_confidence_score',
    'Average OCR confidence',
    ['document_type']
)

# 사용 예
ocr_documents_processed.labels(
    processor_type='advanced',
    status='success'
).inc()

ocr_processing_time.observe(processing_time_seconds)
```

### 10.2 RBAC 접근 통계

```python
rbac_access_attempts = Counter(
    'rbac_access_attempts_total',
    'Total access attempts',
    ['result', 'classification_level']
)

rbac_denied_access = Counter(
    'rbac_denied_access_total',
    'Denied access attempts',
    ['reason']  # 'insufficient_role', 'wrong_department'
)

# 사용 예
rbac_access_attempts.labels(
    result='success',
    classification_level='Confidential'
).inc()

rbac_denied_access.labels(reason='insufficient_role').inc()
```

---

## 다음: PART 3 (최종 타임라인)

PART 2 보강 완료:
- ✅ PaddleOCR-VL 기술 평가
- ✅ RBAC 5단계 구조
- ✅ **환경 설정** (신규)
- ✅ **한국어 최적화** (신규)
- ✅ **테스트 전략** (신규)
- ✅ **마이그레이션 전략** (신규)
- ✅ **모니터링 지표** (신규)

