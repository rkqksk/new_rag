# 전체 제품 재크롤링 실행 계획

## 개요
업그레이드된 크롤러를 사용하여 청진코리아 전체 제품 (398개)을 재크롤링하고 데이터를 최신화합니다.

## 크롤러 업그레이드 내역

### 주요 개선사항
1. **innerText 기반 스펙 파싱**: 재질, 제품코드, 사양 정보 추출
2. **이미지 추출 강화**: img 태그 + CSS background-image 모두 수집
3. **Definition Lists 지원**: dl/dt/dd 구조 완벽 파싱
4. **인쇄영역 PDF**: 자동 다운로드 및 저장
5. **제품명 100% 추출**: img alt 속성 활용

### 파싱 전략 (3단계 폴백)
```python
방법 1: DL 요소 기반 추출 (product-view-bottom-item 컨테이너)
  → dt/dd 쌍으로 스펙 추출

방법 2: innerText 기반 파싱 (DL이 없는 경우)
  → 키워드 매칭 (제품명, 코드, 재질, 사양, Product, Material, Specification)

방법 3: 페이지 전체 DL 요소 (최후의 폴백)
  → 모든 dl 요소 검색 후 필터링
```

## 크롤링 범위

### 카테고리별 상세
| 카테고리 | 페이지 수 | 예상 제품 수 | URL |
|---------|---------|------------|-----|
| Bottle | 68 | ~340 | http://chungjinkorea.com/kr/product/list.php?part_idx=1 |
| Jar | 4 | ~20 | http://chungjinkorea.com/kr/product/list.php?part_idx=2 |
| Cap&Pump | 14 | ~38 | http://chungjinkorea.com/kr/product/list.php?part_idx=3 |
| **합계** | **86** | **~398** | - |

### 예상 소요 시간
- **Delay 설정**: 2초 (서버 부하 방지)
- **제품당 평균 시간**: 약 5-8초 (네비게이션 + 데이터 추출 + 이미지 다운로드)
- **총 예상 시간**: 30-60분

## 디렉토리 구조

```
data/
├── crawled_products_organized/   # 기존 데이터 (400개 JSON)
├── crawled_products_updated/     # 새 크롤링 결과 (자동 생성)
│   ├── idx_*.json               # 제품 데이터 (398개)
│   ├── images/                  # 제품 이미지
│   │   └── idx_*_*.jpg
│   ├── print_area/              # 인쇄영역 PDF
│   │   └── idx_*_print_area.pdf
│   ├── validation_report.json   # 품질 검증 리포트
│   └── full_site_crawl_*.json   # 크롤링 요약
└── crawled_products_backup/      # 기존 데이터 백업 (마이그레이션 시)
```

## 실행 단계

### 1단계: 준비 (5분)
```bash
cd /Users/oypnus/Project/rag-enterprise

# venv 활성화
source .direnv/python-3.11/bin/activate

# 의존성 확인
python3 -c "import asyncio, aiohttp, playwright; print('Dependencies OK')"

# 크롤러 확인
ls -la scripts/crawlers/chungjin_crawler.py
ls -la scripts/crawlers/recrawl_all_products.py
```

### 2단계: 재크롤링 실행 (30-60분)
```bash
# 대화형 실행
python3 scripts/crawlers/recrawl_all_products.py

# 프롬프트:
# - "재크롤링을 시작하시겠습니까? (y/n):" → y 입력
# - 크롤링 진행 (자동)
# - "기존 데이터를 백업하고 새 데이터로 교체하시겠습니까? (y/n):" → n 입력 (일단 검증 먼저)
```

### 3단계: 검증 (10분)
```bash
# 결과 확인
ls -la data/crawled_products_updated/

# JSON 파일 개수 확인
find data/crawled_products_updated -name "idx_*.json" | wc -l

# 검증 리포트 확인
cat data/crawled_products_updated/validation_report.json | jq

# 샘플 데이터 확인
cat data/crawled_products_updated/idx_912.json | jq '.specifications'
```

### 4단계: 비교 분석 (5분)
- 기존 vs 새 데이터 비교 (자동 생성됨)
- 재질 추출률, 제품코드 추출률, 사양 정보 추출률 확인
- 이미지 수집률 확인

### 5단계: 마이그레이션 (선택적)
```bash
# 만족스러운 경우에만 실행
python3 scripts/crawlers/recrawl_all_products.py
# → 마이그레이션 프롬프트에서 y 입력

# 또는 수동 마이그레이션:
mv data/crawled_products_organized data/crawled_products_backup
mv data/crawled_products_updated data/crawled_products_organized
```

## 데이터 품질 기준

### 필수 항목
- ✅ 제품명: 100% (img alt에서 추출)
- ✅ 이미지: 최소 1개 이상
- ✅ 스펙 정보: 최소 1개 이상 항목

### 선택 항목
- 재질 정보: 목표 70%+
- 제품코드: 목표 80%+
- 사양 정보: 목표 90%+
- 인쇄영역 PDF: 가능한 모든 제품

## 모니터링

### 진행 상황 로깅
```
실시간 로그: 콘솔 출력 + recrawl_all_products.log 파일
- [페이지 X/Y] URL 수집 중...
- [제품 N/M] 크롤링 중...
- ✓ 제품명: ...
- ✓ 이미지: N개
- ✓ 스펙: N개 항목
```

### 에러 처리
- 네트워크 에러: 재시도 (최대 3회)
- JavaScript 실행 실패: 로그 기록 후 계속 진행
- 이미지 다운로드 실패: 경고 로그 후 계속 진행

## 성공 기준

### 정량적 기준
- 전체 성공률: 95% 이상 (약 378개 이상 성공)
- 재질 정보 추출률: 70% 이상
- 제품코드 추출률: 80% 이상
- 사양 정보 추출률: 90% 이상
- 이미지 수집률: 98% 이상

### 정성적 기준
- 제품명 정확도: 100% (기계적 추출)
- 스펙 정보 완성도: 기존 대비 개선
- 이미지 품질: 원본 해상도 유지
- PDF 다운로드: 링크가 있는 모든 제품

## 백업 및 롤백 계획

### 백업
- 기존 데이터: `data/crawled_products_organized/` → `data/crawled_products_backup/`
- 자동 백업: 마이그레이션 실행 시 자동 수행

### 롤백 (문제 발생 시)
```bash
# 새 데이터 삭제
rm -rf data/crawled_products_organized

# 백업에서 복구
mv data/crawled_products_backup data/crawled_products_organized
```

## 실행 체크리스트

- [ ] Python 3.11 venv 활성화
- [ ] Playwright 및 의존성 설치 확인
- [ ] 크롤러 스크립트 실행 권한 확인
- [ ] 디스크 공간 확인 (최소 2GB 여유)
- [ ] 네트워크 연결 안정성 확인
- [ ] 실행 전 기존 데이터 확인
- [ ] 재크롤링 실행
- [ ] 검증 리포트 확인
- [ ] 샘플 데이터 검증
- [ ] 비교 분석 검토
- [ ] 마이그레이션 결정
- [ ] 백업 확인

## 예상 결과물

### 파일
1. `data/crawled_products_updated/idx_*.json` (398개)
2. `data/crawled_products_updated/images/idx_*_*.jpg` (~1000+ 이미지)
3. `data/crawled_products_updated/print_area/idx_*_print_area.pdf` (~300개)
4. `data/crawled_products_updated/validation_report.json`
5. `data/crawled_products_updated/full_site_crawl_*.json`
6. `recrawl_all_products.log`

### 리포트 내용
```json
{
  "crawl_info": {
    "timestamp": "2025-10-18T20:30:00",
    "duration_seconds": 2400,
    "duration_formatted": "0:40:00"
  },
  "categories": {
    "Bottle": {"total_products": 340, "success": 337, "error": 3, "success_rate": 99.1},
    "Jar": {"total_products": 20, "success": 20, "error": 0, "success_rate": 100.0},
    "Cap&Pump": {"total_products": 38, "success": 38, "error": 0, "success_rate": 100.0}
  },
  "overall_stats": {
    "total_products": 398,
    "total_success": 395,
    "total_error": 3,
    "success_rate": 99.2
  },
  "data_quality": {
    "total_files": 395,
    "material_extraction_rate": 75.4,
    "product_code_extraction_rate": 89.1,
    "specification_extraction_rate": 94.2,
    "image_extraction_rate": 98.7
  }
}
```

## 문제 해결

### 일반적인 문제
1. **Playwright 에러**
   ```bash
   playwright install webkit
   ```

2. **네트워크 타임아웃**
   - Delay 증가: `delay=3` 또는 `delay=5`

3. **메모리 부족**
   - 카테고리별 개별 실행
   - `chungjin_crawler.py`의 `crawl_category()` 메서드 사용

4. **디스크 공간 부족**
   - 임시 파일 정리
   - 기존 백업 삭제

## 참고 자료
- 크롤러 소스: `scripts/crawlers/chungjin_crawler.py`
- 실행 스크립트: `scripts/crawlers/recrawl_all_products.py`
- 브라우저 자동화: `scripts/crawlers/browser_automation.py`
- MCP 서버: `mcp_servers/google_devtools/server.py`

---
**작성일**: 2025-10-18
**작성자**: RAG Enterprise Team
**버전**: 1.0
