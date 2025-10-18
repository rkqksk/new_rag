# 크롤링 데이터 구조 설계

## 디렉토리 구조

```
data/crawled_products/
├── Bottle/
│   ├── products/              # JSON 제품 데이터
│   │   ├── idx_417.json
│   │   ├── idx_418.json
│   │   └── ...
│   ├── images/                # 제품 이미지
│   │   ├── idx_417_main_1.jpg
│   │   ├── idx_417_additional_1_2.jpg
│   │   └── ...
│   ├── print_area/            # 인쇄영역 PDF
│   │   ├── idx_417_print_area.pdf
│   │   └── ...
│   └── Bottle_report.csv      # 카테고리별 상세 리포트
│
├── Jar/
│   ├── products/
│   ├── images/
│   ├── print_area/
│   └── Jar_report.csv
│
├── Cap_Pump/                  # &는 파일시스템에서 문제될 수 있어 _로 대체
│   ├── products/
│   ├── images/
│   ├── print_area/
│   └── Cap_Pump_report.csv
│
└── master_report.csv          # 전체 카테고리 통합 리포트
```

## CSV 리포트 컬럼

### 개별 카테고리 리포트 (예: Bottle_report.csv)
| 컬럼명 | 설명 | 예시 값 |
|--------|------|---------|
| idx | 제품 ID | 417 |
| product_name | 제품명 | PET병 50ml |
| url | 제품 URL | http://chungjinkorea.com/kr/product/view.php?idx=417 |
| crawl_status | 크롤링 상태 | 성공/실패 |
| image_count | 이미지 개수 | 3 |
| image_status | 이미지 추출 상태 | 성공/부분성공/실패 |
| image_types | 이미지 유형 | main,additional_1,additional_2 |
| print_area_status | 인쇄영역 상태 | 없음/성공/실패 |
| spec_count | 사양 항목 개수 | 5 |
| spec_status | 사양 정리 상태 | 완료/실패 |
| spec_keys | 사양 항목 목록 | 용량,재질,색상,크기,무게 |
| crawled_at | 크롤링 시간 | 2025-10-18T11:15:00 |
| json_path | JSON 파일 경로 | products/idx_417.json |

### 통합 리포트 (master_report.csv)
추가 컬럼:
- category: 카테고리명 (Bottle/Jar/Cap_Pump)
- category_url: 카테고리 페이지 URL

## 정리 전략

### 우선순위 1: 즉시 삭제 가능
- `dev/` 디렉토리의 실험 스크립트 (check_*, test_*)
- 테스트 데이터 디렉토리 (data/test_*)
- 백업 로그 파일 (*.log.old, *.bak)
- 임시 파일 (temp_*, *.tmp)

### 우선순위 2: 아카이브 후 삭제
- 성공한 크롤링 로그 (crawl_*.log)
- 구버전 스크립트 (chungjin_crawler_v1.py 등)
- 테스트 결과 요약 (category_*_test.json)

### 우선순위 3: 보관
- 최종 크롤링 결과 (data/crawled_products/)
- 프로덕션 크롤러 (chungjin_crawler.py)
- 실행 스크립트 (crawl_bottle_only.py, crawl_all_categories.py)
- 최종 크롤링 로그 (최신 1개만)

### 우선순위 4: 구조 변경
- 기존 data/crawled_products/ 파일들을 카테고리별로 재구성
- JSON, 이미지, PDF를 적절한 서브디렉토리로 이동
