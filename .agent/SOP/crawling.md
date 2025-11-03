# SOP: Web Crawling for Product Data

## Purpose
웹사이트에서 화장품 용기 제품 데이터를 크롤링하고 RAG 시스템에 자동 연동

## Scope
- **Target**: 청진코리아 제품 카탈로그 (Bottle, Jar, Cap, Pump 등)
- **Output**: JSON 제품 데이터 (specifications, images, pricing)
- **Frequency**: On-demand 또는 scheduled (주 1회)

## Prerequisites
- [ ] Python환경 설정 완료 (`requirements.txt`)
- [ ] `agents/crawling_agent.py` 실행 가능
- [ ] 크롤링 대상 사이트 URL 확인
- [ ] Output 디렉토리 생성 (`data/products/crawled/`)

## Standard Operating Procedure

### 1. 크롤링 설정 확인
```python
# agents/crawling_agent.py 사용
from agents.crawling_agent import CrawlingAgent, CrawlCategory

config = {
    "site_name": "청진코리아",
    "site_url": "http://chungjinkorea.com",
    "output_dir": "data/products/crawled/"
}
```

### 2. 크롤링 카테고리 정의
```python
categories = [
    CrawlCategory(name="Bottle", url="http://chungjinkorea.com/bottle", pages=68),
    CrawlCategory(name="Jar", url="http://chungjinkorea.com/jar", pages=4),
    CrawlCategory(name="Cap", url="http://chungjinkorea.com/cap", pages=15),
    CrawlCategory(name="Pump", url="http://chungjinkorea.com/pump", pages=8)
]
```

### 3. 크롤링 실행
```bash
# Direct Python execution
python3 agents/crawling_agent.py

# Or via API
curl -X POST http://localhost:8000/api/agents/crawling/start \
  -H "Content-Type: application/json" \
  -d '{
    "site": "청진코리아",
    "categories": ["Bottle", "Jar"]
  }'
```

### 4. 결과 검증
```bash
# Check output files
ls -lh data/products/crawled/

# Verify JSON structure
cat data/products/crawled/Bottle/products/idx_0.json | python3 -m json.tool

# Expected fields:
# - product_code, product_name
# - specifications (capacity, material, neck_size)
# - pricing (moq, coating_option, printing_option)
# - images[]
```

### 5. 에러 처리

#### Case 1: 네트워크 오류
```
Error: Connection timeout
Action:
  1. 네트워크 연결 확인
  2. 사이트 접근 가능 여부 확인 (방화벽, VPN)
  3. Retry with exponential backoff
```

#### Case 2: 페이지 구조 변경
```
Error: Cannot find product elements
Action:
  1. 사이트 HTML 구조 확인 (개발자 도구)
  2. CSS selector 업데이트 (agents/crawling_agent.py)
  3. Test on single page before bulk crawling
```

#### Case 3: Rate limiting
```
Error: 429 Too Many Requests
Action:
  1. Reduce crawl speed (add delay between requests)
  2. Implement polite crawling (robots.txt 준수)
  3. Use session management
```

## Quality Checks

### Data Completeness
- [ ] 모든 제품에 `product_code` 존재
- [ ] `specifications.capacity` 파싱 성공
- [ ] `images` 배열에 최소 1개 이미지
- [ ] `pricing` 정보 존재

### Data Accuracy
- [ ] 용량 단위 정규화 (ml, L 통일)
- [ ] 재질명 표준화 (PET, PETG, PP, PE 등)
- [ ] Neck size 형식 검증 (예: 24/410, 28/400)

## Next Steps
크롤링 완료 후 자동 연계:
1. **Embedding Generation** (SOP/embedding.md)
2. **Vector Indexing** (agents/vector_db_loader_agent.py)
3. **Quality Validation** (data validation scripts)

## Monitoring

### Metrics to Track
- **Success rate**: 크롤링 성공 제품 수 / 전체 제품 수
- **Data quality**: 필수 필드 완성도 (%)
- **Performance**: 제품당 평균 크롤링 시간

### Alerts
- Success rate < 90% → 사이트 구조 변경 의심
- Crawl time > 5초/제품 → 네트워크 이슈 확인

## Maintenance

### Weekly
- [ ] 크롤링 성공률 확인
- [ ] 에러 로그 검토

### Monthly
- [ ] 사이트 구조 변경 체크
- [ ] 새 카테고리 추가 확인
- [ ] Data schema 검증

---

**Owner**: Data Engineering Team
**Last Updated**: 2025-10-26
**Version**: 1.0
