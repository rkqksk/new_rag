# Onehago.com 전체 크롤링 상태

## 실행 정보
- **시작 시간**: 2025-10-27 02:47 KST
- **프로세스 ID**: 24882
- **스크립트**: `scripts/crawl_onehago_full.py`
- **로그 파일**: `/tmp/onehago_full_crawl.log`

## 현재 진행 상황 (2025-10-27 03:00 KST 기준)

### 통계
- **완료 카테고리**: 13/217 (약 6%)
- **처리된 이미지**: 1,516개
- **실패율**: 0% (모든 카테고리 성공)

### 예상 완료 시간
- **카테고리당 평균 시간**: 약 22분
- **총 예상 소요 시간**: 약 79.6시간 (약 3.3일)
- **예상 완료 시각**: 2025-10-30 10:00 KST 경

### 데이터 저장 위치
- **카테고리별 제품 리스트**: `data/onehago/full_crawl/category_*.json`
- **다운로드된 이미지**: `data/onehago/full_crawl/images/`
- **최종 통합 데이터**: `data/onehago/full_crawl/all_products_full.json` (완료 후 생성)
- **진행 상황 추적**: `data/onehago/full_crawl/progress.json`

## 모니터링 방법

### 진행 상황 확인
```bash
/tmp/monitor_crawl.sh
```

### 실시간 로그 확인
```bash
tail -f /tmp/onehago_full_crawl.log
```

### 프로세스 상태 확인
```bash
ps aux | grep crawl_onehago_full
```

### 이미지 다운로드 현황
```bash
ls data/onehago/full_crawl/images/ | wc -l
```

### 진행률 확인
```bash
cat data/onehago/full_crawl/progress.json
```

## 완료된 카테고리 (13개)
1. Category ID: 2 (PACKAGING)
2. Category ID: 193
3. Category ID: 210
4. Category ID: 209
5. Category ID: 208
6. Category ID: 7 (BOTTLE)
7. Category ID: 207
8. Category ID: 124
9. Category ID: 34
10. Category ID: 35
11. Category ID: 182
12. Category ID: 36
13. Category ID: 33

## 데이터 구조

### 제품 정보 필드
각 제품은 다음 정보를 포함합니다:

- `product_id`: 제품 고유 ID
- `company_no`: 회사 번호
- `category_id`: 카테고리 ID
- `category_name`: 카테고리 이름
- `product_name`: 제품명
- `moq`: 최소 주문 수량
- `image_url`: 이미지 URL
- `detail_url`: 상세 페이지 URL
- `detailed_name`: 상세 제품명
- `full_image_url`: 고화질 이미지 URL
- `image_path`: 다운로드된 이미지 경로
- `specifications`: 제품 사양
  - 코드 (Code)
  - 용량 (Capacity)
  - 사이즈 (Size)
  - Neck
  - MOQ
  - 재질 (Material)
  - 원산지 (Origin)
  - 제조사 (Manufacturer)
  - PHONE
  - FAX
  - 담당 (Contact)
  - E MAIL
- `manufacturer`: 제조사
- `phone`: 전화번호
- `email`: 이메일
- `crawled_at`: 크롤링 시간

## 주의사항

1. **중단하지 마세요**: 프로세스를 중단하면 진행 상황이 저장되지만, `all_products_full.json`은 생성되지 않습니다.
2. **재시작 가능**: 중단된 경우 같은 명령으로 재시작하면 `progress.json`에서 이어서 크롤링합니다.
3. **디스크 공간**: 약 2-3GB 정도 필요할 것으로 예상됩니다.

## 문제 해결

### 프로세스가 멈춘 경우
```bash
# 프로세스 확인
ps aux | grep crawl_onehago_full

# 없으면 재시작
python3 scripts/crawl_onehago_full.py 2>&1 | tee /tmp/onehago_full_crawl.log &
```

### 진행 상황 초기화 (처음부터 다시 시작)
```bash
rm data/onehago/full_crawl/progress.json
```

---

**마지막 업데이트**: 2025-10-27 03:00 KST
**상태**: 🟢 정상 실행 중
