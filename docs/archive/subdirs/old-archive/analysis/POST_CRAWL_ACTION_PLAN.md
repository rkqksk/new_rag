# Onehago 크롤링 후 실행 계획

## 📊 현재 상황 분석

### 크롤링 데이터 현황
- **총 제품 수**: 2,011,553개
- **Packaging 제품**: 492,091개 (24.46%)
- **서비스 리스팅**: 1,519,462개 (75.54%)

### Category 구조
```
onehago.com
├─ Packaging (492,091개, category_id: 2-113)
│  ├─ makeup_containers    : 153,059개 (31.10%)
│  ├─ food_containers      : 110,183개 (22.39%)
│  ├─ bottles_jars         : 108,641개 (22.08%)
│  ├─ pharmaceutical       :  88,187개 (17.92%)
│  ├─ applicators          :  22,392개 ( 4.55%)
│  ├─ post_processing      :   2,420개 ( 0.49%)
│  ├─ tubes                :   2,400개 ( 0.49%)
│  ├─ caps                 :   2,315개 ( 0.47%)
│  ├─ pumps                :   2,137개 ( 0.43%)
│  └─ pouches              :     357개 ( 0.07%)
│
├─ OEM/ODM (1,678개, category_id: 3)
├─ Design (1,122개, category_id: 5)
├─ Marketing (76개, category_id: 6)
└─ Other (1,516,586개)
```

---

## 🎯 Phase 3: 이미지 다운로드 전략

### ✅ 가능한 것들
1. **Category별 구분**: `category_id` 필드로 완벽하게 구분 가능
2. **Subcategory별 구분**: packaging 내 10개 세부 카테고리로 분류 가능
3. **선택적 다운로드**: 특정 category/subcategory만 선택하여 다운로드 가능

### ⚠️ 저장 용량 문제
```
전체 Packaging 이미지 다운로드 시:
- 제품 수: 492,091개
- 제품당 이미지: 최대 3개
- 이미지당 크기: ~100 KB
- 총 예상 용량: ~147.6 GB ❌ (100GB 제한 초과!)
```

### 💡 해결 방안 (3가지 옵션)

#### **옵션 1: 이미지 개수 제한** (추천 ⭐)
```
제품당 1개 이미지만 다운로드:
- 제품 수: 492,091개
- 제품당 이미지: 1개
- 총 예상 용량: ~49.2 GB ✅
```

**장점**:
- 모든 packaging 제품 커버
- 대표 이미지만 저장하여 용량 절약
- 가장 공정한 분배

**단점**:
- 제품당 상세 이미지 부족

#### **옵션 2: 상위 Subcategory만 선택**
```
makeup_containers + food_containers + bottles_jars만 다운로드:
- 제품 수: 371,883개 (전체의 75.6%)
- 제품당 이미지: 3개
- 총 예상 용량: ~111.6 GB ❌ (여전히 초과)

→ 이미지 1개로 제한하면: ~37.2 GB ✅
```

**장점**:
- 주요 카테고리에 집중
- 비즈니스 임팩트 큰 제품군 우선

**단점**:
- pharmaceutical, applicators 등 누락
- 불완전한 커버리지

#### **옵션 3: 단계별 다운로드** (최고 유연성 ⭐⭐⭐)
```
Phase 3-1: makeup_containers (153,059개)
- 이미지: 제품당 1개
- 용량: ~15.3 GB
- 목적: 화장품 용기 우선 확보

Phase 3-2: bottles_jars (108,641개)
- 이미지: 제품당 1개
- 용량: ~10.9 GB
- 목적: 범용 병/용기 확보

Phase 3-3: pharmaceutical (88,187개)
- 이미지: 제품당 1개
- 용량: ~8.8 GB
- 목적: 의약품 용기 확보

Phase 3-4: food_containers (110,183개)
- 이미지: 제품당 1개
- 용량: ~11.0 GB
- 목적: 식품 용기 확보

Phase 3-5: 나머지 subcategory (31,621개)
- 이미지: 제품당 1개
- 용량: ~3.2 GB

총 누적 용량: ~49.2 GB ✅
```

**장점**:
- 중간에 멈출 수 있는 유연성
- 비즈니스 우선순위에 따라 조정 가능
- 점진적 검증 가능

**단점**:
- 여러 번 실행 필요

---

## 🚀 실행 계획 (옵션 3 기준)

### Step 1: Category 필터링 스크립트 작성 ✅
```python
# scripts/filter_packaging_products.py
import json

# Load category classification
with open('data/onehago/crawled/production/category_classification.json') as f:
    classification = json.load(f)

# Extract products by subcategory
def filter_by_subcategory(subcategory_name):
    target_ids = classification['packaging_subcategories'][subcategory_name]

    filtered = []
    with open('data/onehago/crawled/production/all_product_urls.jsonl') as f:
        for line in f:
            product = json.loads(line)
            if product['category_id'] in target_ids:
                filtered.append(product)

    return filtered

# Phase 3-1: makeup_containers
makeup_products = filter_by_subcategory('makeup_containers')
with open('data/onehago/images/phase3_makeup_input.jsonl', 'w') as f:
    for p in makeup_products:
        f.write(json.dumps(p, ensure_ascii=False) + '\n')
```

### Step 2: 이미지 다운로드 Orchestrator 실행

#### Phase 3-1: Makeup Containers (우선순위 1)
```bash
# 입력 파일 생성
python3 scripts/filter_packaging_products.py makeup_containers

# Orchestrator 실행
python3 scripts/onehago_image_orchestrator.py \
  --input data/onehago/images/phase3_makeup_input.jsonl \
  --output data/onehago/images/category_makeup/ \
  --workers 10 \
  --max-images 1
```

**예상 시간**:
- 153,059개 제품 × 2초/제품 = 84.9시간
- 10 workers → 약 8.5시간

#### Phase 3-2: Bottles & Jars (우선순위 2)
```bash
python3 scripts/filter_packaging_products.py bottles_jars

python3 scripts/onehago_image_orchestrator.py \
  --input data/onehago/images/phase3_bottles_input.jsonl \
  --output data/onehago/images/category_bottles/ \
  --workers 10 \
  --max-images 1
```

**예상 시간**: ~6 hours

#### Phase 3-3: Pharmaceutical (우선순위 3)
```bash
python3 scripts/filter_packaging_products.py pharmaceutical

python3 scripts/onehago_image_orchestrator.py \
  --input data/onehago/images/phase3_pharma_input.jsonl \
  --output data/onehago/images/category_pharma/ \
  --workers 10 \
  --max-images 1
```

**예상 시간**: ~5 hours

#### Phase 3-4: Food Containers (우선순위 4)
```bash
python3 scripts/filter_packaging_products.py food_containers

python3 scripts/onehago_image_orchestrator.py \
  --input data/onehago/images/phase3_food_input.jsonl \
  --output data/onehago/images/category_food/ \
  --workers 10 \
  --max-images 1
```

**예상 시간**: ~6 hours

#### Phase 3-5: 나머지 (우선순위 5)
```bash
for subcat in applicators tubes caps pumps pouches post_processing; do
  python3 scripts/filter_packaging_products.py $subcat

  python3 scripts/onehago_image_orchestrator.py \
    --input data/onehago/images/phase3_${subcat}_input.jsonl \
    --output data/onehago/images/category_${subcat}/ \
    --workers 10 \
    --max-images 1
done
```

**예상 시간**: ~1.8 hours (combined)

---

## 📊 Phase 4: 데이터 품질 검증

### Step 1: 이미지 다운로드 성공률 체크
```bash
python3 scripts/validate_image_downloads.py

# Output:
# - 성공률 (%)
# - 실패한 product_id 리스트
# - 이미지 해상도/크기 통계
```

### Step 2: 누락 이미지 재다운로드
```bash
python3 scripts/retry_failed_images.py \
  --failed-list data/onehago/images/failed_products.json \
  --max-retries 3
```

### Step 3: 중복 이미지 제거
```bash
python3 scripts/deduplicate_images.py \
  --input-dir data/onehago/images/ \
  --method md5  # MD5 hash로 중복 검출
```

---

## 🎯 Phase 5: RAG 시스템 통합

### Step 1: 이미지 메타데이터 생성
```python
# scripts/generate_image_metadata.py
import json
from PIL import Image
import hashlib

for product_file in glob('data/onehago/images/**/*.jpg'):
    img = Image.open(product_file)

    metadata = {
        'product_id': extract_product_id(product_file),
        'image_path': product_file,
        'width': img.width,
        'height': img.height,
        'format': img.format,
        'size_bytes': os.path.getsize(product_file),
        'md5': hashlib.md5(open(product_file, 'rb').read()).hexdigest()
    }

    # Save to metadata DB
    save_to_db(metadata)
```

### Step 2: 텍스트 + 이미지 통합 인덱싱
```python
# RAG pipeline에 이미지 포함
from rag_pipeline import process_document

for product in packaging_products:
    document = {
        'text': product['product_name'] + ' ' + product['specifications'],
        'images': load_product_images(product['product_id']),
        'metadata': {
            'category': get_subcategory(product['category_id']),
            'product_url': product['product_url']
        }
    }

    # Vector DB에 저장 (text embedding + image path)
    vector_db.upsert(document)
```

### Step 3: Multi-modal RAG 쿼리
```python
# 사용자 쿼리 예시:
query = "50ml 화장품 용기 추천해줘"

# 1. Text-based retrieval
text_results = vector_db.search(query, top_k=10)

# 2. 이미지 포함 응답 생성
for result in text_results:
    product_info = result['metadata']
    images = get_product_images(product_info['product_id'])

    # LLM에 이미지 경로도 전달
    response = llm.generate(
        text=product_info['text'],
        images=images  # 이미지도 context로 제공
    )
```

---

## ⏰ 전체 타임라인

```
┌─────────────────────────────────────────────────────────┐
│ Phase 2: Text Extraction (현재 진행 중)                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 50% (1M/2M)  │
│ 예상 완료: 24-36시간                                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Phase 3-1: Makeup Containers 이미지 다운로드             │
│ ━━━━━━━━━━━░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  0%         │
│ 제품 수: 153,059개                                       │
│ 예상 시간: 8.5시간 (10 workers)                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Phase 3-2: Bottles & Jars 이미지 다운로드               │
│ ━━━━━━━━━░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  0%         │
│ 제품 수: 108,641개                                       │
│ 예상 시간: 6시간                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Phase 3-3: Pharmaceutical 이미지 다운로드                │
│ ━━━━━━━░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  0%         │
│ 제품 수: 88,187개                                        │
│ 예상 시간: 5시간                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Phase 3-4: Food Containers 이미지 다운로드               │
│ ━━━━━━━━━░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  0%         │
│ 제품 수: 110,183개                                       │
│ 예상 시간: 6시간                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Phase 3-5: 나머지 Subcategories 이미지 다운로드          │
│ ━░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  0%         │
│ 제품 수: 31,621개                                        │
│ 예상 시간: 1.8시간                                       │
└─────────────────────────────────────────────────────────┘

📅 총 예상 완료 시간: 27.3시간 (약 1.1일)
💾 총 저장 용량: ~49.2 GB
```

---

## 🛠️ 필요한 스크립트 목록

### 1. `scripts/filter_packaging_products.py` ✅ (생성 필요)
- Category/subcategory별 제품 필터링
- Phase별 입력 파일 생성

### 2. `scripts/onehago_image_orchestrator.py` ✅ (이미 존재)
- 현재 경로: `/Users/oypnus/Project/rag-enterprise/scripts/onehago_image_orchestrator.py`
- 10-worker 이미지 다운로드 orchestration

### 3. `scripts/onehago_image_worker.py` ✅ (생성 필요)
- 개별 worker 스크립트
- 제품별 이미지 다운로드 로직

### 4. `scripts/validate_image_downloads.py` (생성 필요)
- 다운로드 성공률 체크
- 실패 제품 리스트 생성

### 5. `scripts/retry_failed_images.py` (생성 필요)
- 실패한 이미지 재다운로드

### 6. `scripts/deduplicate_images.py` (생성 필요)
- MD5 기반 중복 이미지 제거

### 7. `scripts/generate_image_metadata.py` (생성 필요)
- 이미지 메타데이터 생성

---

## 📝 체크리스트

### Phase 2 완료 후 즉시 실행
- [ ] Category 분석 결과 확인
- [ ] 최종 제품 수 검증 (예상: 2,011,553개)
- [ ] Packaging 제품 수 확인 (예상: 492,091개)

### Phase 3 준비
- [ ] `filter_packaging_products.py` 스크립트 작성
- [ ] `onehago_image_worker.py` 스크립트 작성
- [ ] 이미지 저장 디렉토리 구조 생성
- [ ] Orchestrator 설정 검증

### Phase 3 실행
- [ ] Phase 3-1: makeup_containers (8.5시간)
- [ ] Phase 3-2: bottles_jars (6시간)
- [ ] Phase 3-3: pharmaceutical (5시간)
- [ ] Phase 3-4: food_containers (6시간)
- [ ] Phase 3-5: 나머지 (1.8시간)

### Phase 4 검증
- [ ] 이미지 다운로드 성공률 체크
- [ ] 실패 이미지 재다운로드
- [ ] 중복 이미지 제거
- [ ] 최종 저장 용량 확인

### Phase 5 RAG 통합
- [ ] 이미지 메타데이터 생성
- [ ] Vector DB에 이미지 경로 추가
- [ ] Multi-modal RAG 쿼리 테스트

---

## 💡 추천 실행 방식

### 옵션 A: 보수적 접근 (추천)
1. Phase 2 완료 대기 (24-36시간)
2. 결과 분석 및 검증
3. Phase 3-1 (makeup) 먼저 실행
4. 성공 확인 후 나머지 단계 진행

### 옵션 B: 적극적 접근
1. Phase 2와 Phase 3-1 동시 실행
2. 서버 리소스 모니터링 필수
3. Phase 2 완료 후 Phase 3-2~3-5 순차 실행

---

## 🚨 주의사항

### 서버 부하 관리
- **Phase 2 (text extraction)**: 12 workers 사용 중
- **Phase 3 (image download)**: 10 workers 계획
- **총 동시 실행**: 22 concurrent processes
- ⚠️ 서버 메모리/CPU 모니터링 필수

### 네트워크 제한
- Onehago 서버의 rate limit 주의
- 필요시 worker 수 조정 (10 → 5)
- 타임아웃 설정: 30초

### 저장 용량
- **현재 사용량 확인 필요**
- Phase 3 시작 전 최소 60GB 여유 공간 필요
- 중간 체크포인트마다 용량 확인

---

## 📞 Contact & Support

문제 발생 시:
1. 로그 파일 확인: `/tmp/onehago_image_*.log`
2. 진행상황 모니터링: `http://localhost:5555` (Dual Orchestrator Dashboard)
3. 스크립트 중단: `pkill -f onehago_image_orchestrator`

---

**최종 업데이트**: 2025-11-02
**다음 실행 단계**: Phase 2 완료 대기 → Phase 3-1 실행
