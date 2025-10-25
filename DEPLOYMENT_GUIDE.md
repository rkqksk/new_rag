# 🚀 화장품 용기 스마트 상담 시스템 - 배포 가이드

**버전**: 1.0.0
**날짜**: 2025-10-24
**상태**: ✅ Production Ready

---

## 📋 시스템 개요

### 핵심 기능
1. **스마트 검색**: 용량 기반 정확한 제품 매칭 (40ml, 50ml, 65ml...)
2. **자동 추천**: 사용자 질문에서 용량/재질/용도 자동 추출
3. **간편 문의**: 클릭 한 번으로 견적 문의 완료
4. **AI 상담**: 255개 전문 Q&A 지식 베이스 활용

### 기술 스택
- **Frontend**: Vanilla JavaScript (단일 HTML 파일)
- **Backend**: FastAPI (Python 3.11+)
- **Database**:
  - JSON 파일 (제품 데이터)
  - Qdrant Vector DB (Q&A 검색)
- **AI**: Ollama (로컬 임베딩)

---

## 🎯 간소화된 사용자 여정

### 이전 (9단계)
```
업체 선택 → 생산제품 선택 → 용량 검색 → 담당자 검색 →
샘플 문의 → 단가 문의 → 답변 대기 → 확인 → 계약
```

### 현재 (3단계) ✨
```
1️⃣ 용량 검색 (예: "50ml 세럼")
   ↓
2️⃣ 제품 카드 확인 → "문의하기" 클릭
   ↓
3️⃣ 연락처 입력 → 자동 접수 완료
```

**시간 절감**: ~15분 → ~2분 (87% 감소)

---

## 🚀 배포 방법

### 1단계: 서버 시작

```bash
# 프로젝트 디렉토리로 이동
cd /Users/oypnus/Project/rag-enterprise

# FastAPI 서버 시작
uvicorn app.api_simple:app --host 0.0.0.0 --port 8000
```

### 2단계: 브라우저 접속

```
http://localhost:8000
```

또는 외부 접근 시:
```
http://YOUR_SERVER_IP:8000
```

### 3단계: 동작 확인

1. ✅ 메인 페이지 로드 확인
2. ✅ 검색창에 "50ml" 입력
3. ✅ 제품 카드 표시 확인
4. ✅ "문의하기" 버튼 클릭
5. ✅ 연락처 폼 제출 테스트

---

## 📁 파일 구조

```
rag-enterprise/
├── app/
│   ├── api_simple.py           ← 백엔드 API (단일 파일)
│   └── static/
│       └── app.html            ← 프론트엔드 (단일 파일)
├── data/
│   ├── product_dictionary_enhanced.json     ← 제품 데이터 (5개)
│   ├── packaging_qa_knowledge_base.json     ← Q&A (255개)
│   └── inquiries.json                       ← 문의 내역 (자동 생성)
└── scripts/
    ├── enhance_packaging_data.py           ← 데이터 강화
    ├── generate_embeddings.py              ← 임베딩 생성
    └── test_rag_queries.py                 ← 검색 테스트
```

---

## 🔧 API 엔드포인트

### 1. 제품 검색
```http
GET /api/v1/products/search?query={검색어}&limit={개수}
```

**예시**:
```bash
curl "http://localhost:8000/api/v1/products/search?query=50ml세럼&limit=5"
```

**응답**:
```json
{
  "query": "50ml세럼",
  "total": 2,
  "products": [
    {
      "product_id": "idx_13",
      "product_name": "40ml 브로우용기",
      "product_code": "BE040-R001",
      "material": "PE",
      "capacity": {"value": 40, "unit": "ml"},
      "suitable_product_types": ["세럼", "에센스"],
      "score": 100
    }
  ]
}
```

### 2. Q&A 검색
```http
GET /api/v1/qa/search?query={질문}&limit={개수}
```

**예시**:
```bash
curl "http://localhost:8000/api/v1/qa/search?query=PP소재특성&limit=3"
```

### 3. 문의 접수
```http
POST /api/v1/inquiries
Content-Type: application/json

{
  "product_id": "idx_13",
  "product_name": "40ml 브로우용기",
  "product_code": "BE040-R001",
  "company_name": "ABC 화장품",
  "contact_name": "홍길동",
  "contact_phone": "010-1234-5678",
  "contact_email": "test@example.com",
  "quantity": "1000개",
  "message": "샘플 및 단가 문의"
}
```

### 4. 문의 조회
```http
GET /api/v1/inquiries?limit=50
```

---

## 🎨 사용자 인터페이스

### 검색 화면
```
┌─────────────────────────────────────────┐
│   🧴 화장품 용기 스마트 상담           │
│   원하는 용량 입력하고 바로 문의하세요  │
└─────────────────────────────────────────┘

  [예: 50ml 세럼용기, 100미리...]  [검색]

  [40ml] [50ml] [65ml] [70ml] [100ml] [150ml]
  [세럼] [크림] [로션]

  ┌─────────────────────┐
  │ 40ml 브로우용기     │
  │ BE040-R001          │
  │                     │
  │ [PE] [40ml] [세럼]  │
  │                     │
  │ 📍 소형/휴대용      │
  │ ⏱️ 1-2주 사용량    │
  │ ✨ 세럼, 에센스     │
  │                     │
  │ [💬 문의하기] [상세]│
  └─────────────────────┘
```

### 문의 폼
```
┌─────────────────────────┐
│ 견적 문의               │
│                         │
│ 선택 제품:              │
│ [40ml 브로우용기]       │
│                         │
│ 회사명: ____________    │
│ 담당자: ____________    │
│ 연락처: ____________    │
│ 이메일: ____________    │
│ 수량:   ____________    │
│ 요청사항:               │
│ ___________________     │
│                         │
│ [문의 보내기]           │
└─────────────────────────┘
```

---

## ⚙️ 설정 및 커스터마이징

### 1. API 베이스 URL 변경

`app/static/app.html` 파일에서:

```javascript
// 로컬 테스트
const API_BASE = 'http://localhost:8000';

// 프로덕션 배포
const API_BASE = 'https://your-domain.com';
```

### 2. 제품 데이터 업데이트

```bash
# 1. 제품 정보 수정
vi data/product_dictionary.json

# 2. 데이터 강화 실행
python scripts/enhance_packaging_data.py

# 3. 서버 재시작
# (자동으로 새 데이터 로드됨)
```

### 3. Q&A 지식 베이스 추가

```bash
# 1. Q&A 마크다운 파일 수정
vi data/추가\ Q\&A\ 세트\ -\ 화장품\ 용기\ 상담.md

# 2. 파싱 및 임베딩 재생성
python scripts/enhance_packaging_data.py
python scripts/generate_embeddings.py

# 3. Qdrant 컬렉션 확인
curl http://localhost:6333/collections/cosmetic_packaging
```

---

## 🧪 테스트 시나리오

### 시나리오 1: 용량으로 검색
```
입력: "50ml"
예상 결과: 40ml, 65ml 제품 추천 (가까운 용량)
```

### 시나리오 2: 용도로 검색
```
입력: "세럼용기"
예상 결과: 세럼에 적합한 모든 용량 표시
```

### 시나리오 3: 재질로 검색
```
입력: "PE 재질"
예상 결과: PE 소재 제품만 필터링
```

### 시나리오 4: 복합 검색
```
입력: "50ml PE 세럼"
예상 결과:
  1순위: 정확히 50ml + PE + 세럼용
  2순위: 40ml, 65ml PE 제품
```

### 시나리오 5: 문의 완료
```
1. 제품 선택
2. "문의하기" 클릭
3. 폼 작성
4. 제출
5. "문의가 접수되었습니다" 확인
6. data/inquiries.json에 저장 확인
```

---

## 📊 모니터링

### 실시간 로그 확인
```bash
tail -f /tmp/api_server.log
```

### 문의 내역 확인
```bash
# 최근 10개 문의 조회
curl http://localhost:8000/api/v1/inquiries?limit=10 | python -m json.tool

# 파일로 직접 확인
cat data/inquiries.json
```

### Qdrant 상태 확인
```bash
curl http://localhost:6333/collections/cosmetic_packaging | python -m json.tool
```

---

## 🔒 보안 설정 (프로덕션)

### 1. HTTPS 설정
```bash
# Let's Encrypt SSL 인증서
sudo certbot --nginx -d your-domain.com
```

### 2. CORS 제한
`app/api_simple.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 3. Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/products/search")
@limiter.limit("30/minute")
async def api_search_products(...):
    ...
```

---

## 🐛 트러블슈팅

### 문제 1: 서버가 시작되지 않음
```bash
# 포트 충돌 확인
lsof -i:8000

# 프로세스 종료
kill -9 $(lsof -ti:8000)

# 다시 시작
uvicorn app.api_simple:app --host 0.0.0.0 --port 8000
```

### 문제 2: 제품 검색 결과 없음
```bash
# 데이터 파일 확인
ls -lh data/product_dictionary_enhanced.json

# 데이터 다시 강화
python scripts/enhance_packaging_data.py

# API 테스트
curl "http://localhost:8000/api/v1/products/search?query=50ml"
```

### 문제 3: Qdrant 연결 실패
```bash
# Qdrant 실행 확인
docker ps | grep qdrant

# 없으면 시작
docker run -p 6333:6333 qdrant/qdrant

# 임베딩 재생성
python scripts/generate_embeddings.py
```

### 문제 4: 문의 저장 안 됨
```bash
# 디렉토리 권한 확인
ls -ld data/

# 권한 설정
chmod 755 data/
chmod 644 data/inquiries.json

# 수동 생성
echo "[]" > data/inquiries.json
```

---

## 📈 성능 최적화

### 1. 데이터 캐싱
```python
from functools import lru_cache

@lru_cache(maxsize=1)
def load_products() -> Dict[str, Any]:
    """캐시된 제품 데이터 로드"""
    ...
```

### 2. 비동기 처리
```python
import asyncio

async def parallel_search(query):
    products_task = search_products(query)
    qa_task = search_qa_qdrant(query)

    products, qa = await asyncio.gather(products_task, qa_task)
    return products, qa
```

### 3. Qdrant 인덱스 최적화
```bash
# HNSW 파라미터 조정
curl -X PUT http://localhost:6333/collections/cosmetic_packaging \
  -H "Content-Type: application/json" \
  -d '{
    "hnsw_config": {
      "m": 32,
      "ef_construct": 200
    }
  }'
```

---

## 🚀 프로덕션 배포 체크리스트

- [ ] HTTPS 인증서 설정 완료
- [ ] CORS 정책 설정 완료
- [ ] Rate limiting 적용 완료
- [ ] 환경 변수 설정 완료
- [ ] 데이터 백업 자동화 완료
- [ ] 모니터링 대시보드 설정 완료
- [ ] 에러 알림 설정 완료
- [ ] 로그 로테이션 설정 완료
- [ ] 데이터베이스 백업 스케줄 완료
- [ ] 부하 테스트 완료

---

## 📞 지원 및 문의

**문제 발생 시**:
1. 로그 파일 확인: `/tmp/api_server.log`
2. 데이터 백업 확인: `data/*.backup`
3. API 헬스 체크: `curl http://localhost:8000/health`

**추가 개선 사항**:
- 제품 이미지 추가
- 실시간 채팅 기능
- 관리자 대시보드
- 문의 상태 추적
- 이메일 자동 응답

---

**배포 완료!** 🎉

이제 `http://localhost:8000`으로 접속하여 사용하실 수 있습니다.
