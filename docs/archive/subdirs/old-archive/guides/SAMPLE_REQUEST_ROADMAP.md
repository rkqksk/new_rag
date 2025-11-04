# 샘플 요청 시스템 로드맵

## 📋 현재 상태 (v1.0)

### 구현된 기능
- ✅ 제품 카드에서 바로 샘플 요청 (항상 보이는 버튼)
- ✅ 제품 상세 페이지에서 샘플 요청
- ✅ 샘플 요청 폼 (회사명, 담당자, 연락처, 이메일, 수량, 요청사항)
- ✅ JSON 파일 기반 저장 (`data/sample_requests.json`)
- ✅ 샘플 요청 목록 조회 API

### 현재 데이터 구조
```json
{
  "id": "uuid-string",
  "product_id": "idx_123",
  "product_name": "50ml 헤비브로우용기",
  "product_code": "HG050-R001",
  "company_name": "테스트 회사",
  "contact_name": "홍길동",
  "contact_phone": "010-1234-5678",
  "contact_email": "test@example.com",
  "request_qty": 100,
  "request_message": "샘플 요청 메시지",
  "status": "pending",
  "timestamp": "2025-10-25T08:54:10.603962",
  "created_at": "2025-10-25T08:54:10.603962"
}
```

### 현재 API 엔드포인트
- `POST /api/v1/sample-request` - 샘플 요청 생성
- `GET /api/v1/sample-requests` - 샘플 요청 목록 조회 (status 필터 가능)

---

## 🚀 향후 발전 방향

### Phase 2: 데이터베이스 마이그레이션

**목표**: JSON 파일 → PostgreSQL/MySQL 데이터베이스

**테이블 스키마 설계**:
```sql
CREATE TABLE sample_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 제품 정보
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    product_code VARCHAR(100) NOT NULL,

    -- 요청자 정보
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,

    -- 요청 내용
    request_qty INTEGER,
    request_message TEXT,

    -- 상태 관리
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, approved, shipped, completed, cancelled

    -- 샘플 배송 정보 (Phase 3에서 추가)
    shipping_address TEXT,
    shipping_zipcode VARCHAR(10),
    tracking_number VARCHAR(100),

    -- 결제 정보 (Phase 4에서 추가)
    payment_status VARCHAR(20), -- unpaid, paid, refunded
    payment_method VARCHAR(50),
    payment_amount DECIMAL(10, 2),
    payment_transaction_id VARCHAR(100),

    -- 관리자 메모
    admin_notes TEXT,

    -- 타임스탬프
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    shipped_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- 외래키
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 인덱스
CREATE INDEX idx_sample_requests_status ON sample_requests(status);
CREATE INDEX idx_sample_requests_created_at ON sample_requests(created_at DESC);
CREATE INDEX idx_sample_requests_company ON sample_requests(company_name);
CREATE INDEX idx_sample_requests_email ON sample_requests(contact_email);
```

**마이그레이션 스크립트**:
```python
# scripts/migrate_sample_requests_to_db.py
def migrate_json_to_database():
    """Migrate existing JSON data to PostgreSQL"""
    with open('data/sample_requests.json', 'r') as f:
        requests = json.load(f)

    for request in requests:
        db.execute(
            "INSERT INTO sample_requests (...) VALUES (...)",
            request
        )
```

---

### Phase 3: 샘플 배송 및 추적

**추가 기능**:
1. **배송 주소 입력**: 샘플 요청 시 배송지 정보 수집
2. **배송 상태 추적**:
   - pending → approved → shipped → delivered
   - 택배사 API 연동 (CJ대한통운, 우체국 등)
   - 송장번호 자동 업데이트
3. **고객 알림**:
   - 이메일 알림 (요청 접수, 승인, 배송 시작, 배송 완료)
   - SMS 알림 (선택사항)

**API 추가**:
```python
POST /api/v1/sample-request/{request_id}/shipping
GET  /api/v1/sample-request/{request_id}/tracking
PUT  /api/v1/sample-request/{request_id}/status
```

---

### Phase 4: 간편 결제 시스템 연동

**목표**: 샘플 비용 온라인 결제 지원

#### 4.1 결제 시스템 선정

**추천 PG사**:
1. **토스페이먼츠** (Toss Payments)
   - 국내 1위 간편결제
   - API 연동 간편
   - 수수료 경쟁력
   - 정산 빠름

2. **네이버페이** (Naver Pay)
   - 네이버 유저 기반
   - 신뢰도 높음

3. **카카오페이** (Kakao Pay)
   - 카카오톡 연동
   - 모바일 친화적

4. **나이스페이** (NICE Payments)
   - 전통적 PG사
   - 안정성 높음

#### 4.2 결제 프로세스

```
1. 샘플 요청 → 2. 견적 확인 → 3. 결제 → 4. 배송
```

**결제 플로우**:
```python
# 1. 샘플 요청 생성
POST /api/v1/sample-request
→ response: { request_id, status: "pending", estimated_price: 15000 }

# 2. 관리자 승인 + 견적 확정
PUT /api/v1/sample-request/{request_id}/approve
→ body: { final_price: 12000, shipping_fee: 3000 }
→ response: { status: "approved", payment_url: "https://..." }

# 3. 고객 결제
→ 고객이 payment_url로 이동
→ PG사 결제 페이지
→ 결제 완료 → Webhook 수신

# 4. 결제 확인 Webhook
POST /api/v1/webhooks/payment
→ body: { request_id, transaction_id, amount, status: "paid" }
→ DB 업데이트: payment_status = "paid"

# 5. 배송 시작
PUT /api/v1/sample-request/{request_id}/ship
→ body: { tracking_number: "123456789" }
→ 고객에게 배송 알림
```

#### 4.3 가격 정책

**샘플 가격 계산**:
```python
def calculate_sample_price(product, quantity):
    """
    샘플 가격 = (제품 단가 × 수량) + 배송비

    - 제품 단가: MOQ 기준 단가의 120% (소량이므로)
    - 배송비:
      - 5개 이하: 3,000원
      - 5-10개: 무료
      - 10개 이상: 무료
    """
    unit_price = product.pricing.regular_price * 1.2
    product_cost = unit_price * quantity

    if quantity <= 5:
        shipping_fee = 3000
    else:
        shipping_fee = 0

    return {
        'product_cost': product_cost,
        'shipping_fee': shipping_fee,
        'total': product_cost + shipping_fee
    }
```

#### 4.4 결제 데이터 모델 확장

```python
class SampleRequestPayment(BaseModel):
    request_id: str

    # 가격 정보
    product_cost: int
    shipping_fee: int
    total_amount: int

    # 결제 정보
    payment_method: str  # card, transfer, kakao, naver, toss
    payment_status: str  # pending, paid, failed, refunded
    pg_provider: str     # toss, nice, kakao

    # PG사 응답
    transaction_id: str
    approval_number: str
    paid_at: datetime

    # 환불 정보
    refund_amount: Optional[int]
    refund_reason: Optional[str]
    refunded_at: Optional[datetime]
```

#### 4.5 토스페이먼츠 연동 예시

```python
import requests

TOSS_SECRET_KEY = "test_sk_..."
TOSS_CLIENT_KEY = "test_ck_..."

def create_payment(request_id: str, amount: int):
    """토스페이먼츠 결제 생성"""

    payment_data = {
        "orderId": request_id,
        "orderName": f"샘플 요청 #{request_id}",
        "amount": amount,
        "successUrl": f"https://yoursite.com/payment/success?orderId={request_id}",
        "failUrl": f"https://yoursite.com/payment/fail?orderId={request_id}",
        "customerEmail": customer_email,
        "customerName": customer_name,
    }

    response = requests.post(
        "https://api.tosspayments.com/v1/payments",
        headers={
            "Authorization": f"Basic {TOSS_SECRET_KEY}",
            "Content-Type": "application/json"
        },
        json=payment_data
    )

    return response.json()  # { paymentUrl: "https://..." }

@app.post("/api/v1/webhooks/toss-payment")
async def toss_payment_webhook(webhook_data: dict):
    """토스페이먼츠 Webhook 처리"""

    order_id = webhook_data['orderId']
    status = webhook_data['status']  # DONE, CANCELED

    if status == "DONE":
        # DB 업데이트
        db.execute(
            """
            UPDATE sample_requests
            SET payment_status = 'paid',
                payment_transaction_id = %s,
                approved_at = NOW()
            WHERE id = %s
            """,
            (webhook_data['paymentKey'], order_id)
        )

        # 배송 준비 프로세스 시작
        prepare_shipping(order_id)

        # 고객 이메일 발송
        send_email(
            to=customer_email,
            subject="샘플 결제 완료",
            body="샘플 요청이 승인되었습니다. 배송 준비 중입니다."
        )

    return {"status": "ok"}
```

---

### Phase 5: 관리자 대시보드

**기능**:
1. **샘플 요청 목록**:
   - 상태별 필터링 (pending, approved, shipped, completed)
   - 날짜 범위 검색
   - 회사명/이메일 검색

2. **요청 상세 보기**:
   - 제품 정보
   - 요청자 정보
   - 결제 상태
   - 배송 상태

3. **액션**:
   - 승인/거부
   - 견적 입력
   - 송장번호 입력
   - 관리자 메모 추가

4. **통계**:
   - 일별/월별 샘플 요청 추이
   - 제품별 인기도
   - 회사별 요청 빈도
   - 결제 완료율

**API**:
```python
GET  /api/v1/admin/sample-requests              # 목록
GET  /api/v1/admin/sample-requests/{id}         # 상세
PUT  /api/v1/admin/sample-requests/{id}/approve # 승인
PUT  /api/v1/admin/sample-requests/{id}/reject  # 거부
POST /api/v1/admin/sample-requests/{id}/note    # 메모 추가
GET  /api/v1/admin/sample-requests/stats        # 통계
```

---

### Phase 6: 자동화 및 AI

1. **자동 견적 시스템**:
   - 제품 단가 기반 자동 견적
   - 수량별 할인 자동 적용

2. **이상 패턴 감지**:
   - 동일 이메일/전화번호 중복 요청
   - 비정상적으로 많은 수량 요청
   - 스팸 필터링

3. **챗봇 연동**:
   - 샘플 요청 관련 문의 자동 응답
   - 배송 상태 자동 안내

---

## 📊 데이터 활용 전략

### 수집할 데이터
1. **제품 데이터**:
   - 샘플 요청이 많은 제품
   - 시즌별 인기 제품
   - 용량/재질별 선호도

2. **고객 데이터**:
   - 산업별 고객 분포 (화장품, 식품, 제약 등)
   - 지역별 분포
   - 재요청 고객

3. **전환율 데이터**:
   - 샘플 요청 → 실제 주문 전환율
   - 평균 첫 주문 금액
   - 재구매율

### 분석 및 활용
```python
# 예시: 샘플 요청 분석
SELECT
    p.category_type,
    p.material,
    COUNT(*) as request_count,
    AVG(sr.request_qty) as avg_quantity,
    COUNT(DISTINCT sr.company_name) as unique_companies
FROM sample_requests sr
JOIN products p ON sr.product_id = p.id
WHERE sr.created_at >= NOW() - INTERVAL '30 days'
GROUP BY p.category_type, p.material
ORDER BY request_count DESC;
```

---

## 🔒 보안 및 개인정보 보호

### GDPR/개인정보보호법 준수
1. **데이터 수집 동의**:
   - 개인정보 수집 동의 체크박스 필수
   - 이용약관 명시

2. **데이터 암호화**:
   - 이메일, 전화번호 DB 암호화
   - SSL/TLS 통신

3. **데이터 보존 기간**:
   - 샘플 요청 데이터: 3년 보관 후 자동 삭제
   - 삭제 요청 처리 프로세스

4. **접근 제어**:
   - 관리자 권한 관리
   - 감사 로그 (Audit Log)

---

## 📅 구현 우선순위

### High Priority (3개월 이내)
1. ✅ ~~샘플 요청 UI/UX 개선~~ (완료)
2. 🔄 데이터베이스 마이그레이션
3. 🔄 관리자 대시보드 기본 기능

### Medium Priority (6개월 이내)
4. 배송 주소 수집 및 관리
5. 이메일 알림 시스템
6. 기본 통계 대시보드

### Low Priority (1년 이내)
7. 간편 결제 시스템 연동
8. 배송 추적 시스템
9. AI 기반 자동화

---

## 💡 참고사항

### 현재 파일 위치
- **Frontend**: `app/static/app.html`
- **Backend API**: `app/api_simple.py`
- **데이터 모델**: `SampleRequest` in `app/api_simple.py:82-93`
- **데이터 저장**: `data/sample_requests.json`

### 관련 문서
- [API Reference](API_REFERENCE.md)
- [Architecture](ARCHITECTURE.md)
- [Deployment](DEPLOYMENT.md)

---

**Last Updated**: 2025-10-25
**Version**: 1.0
**Status**: Phase 1 Complete, Planning Phase 2-6
